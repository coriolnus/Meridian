"""threshold_curve.py — MIN_SCORE EŞİK EĞRİSİ: kapıyı yükseltmek kâr getirir mi?
(Kârlılık Programı Aşama 1.3, 2026-07-29)

CEVAPLADIĞI SORU. `entry.min_score` canlıda 60. Bu sayı bir ÖLÇÜMDEN değil, ilk günkü bir
varsayımdan geliyor. "Yükseltsek daha az ama daha iyi işlem mi alırız?" sorusunun bugüne kadarki
tek kanıtı, 95 işlemin skor dilimlerine bakılarak yapılmış bir çıkarımdı (skor 70-80 dilimi
-0.285R, >=80 dilimi +0.066R) — ve o çıkarım TAM REPLAY'de TUTMADI: 2026-07-28 Aşama 0 turunda
H2 (min_score 60→80) OOS'u Δ-0.095 KÖTÜLEŞTİRDİ (P=0.089, ÇÜRÜDÜ). Bu modül o çelişkinin
kalıcı ölçüm yüzeyidir: dilim istatistiği ile eşik taraması aynı panoda yan yana durur.

DİLİM İSTATİSTİĞİ NEDEN REPLAY'İ YANLIŞLAMAZ (ve tersi). İkisi FARKLI SORULAR sorar:
  * eşik eğrisi (bu modül): "eşiği yükseltseydik, GEÇEN adayların ortalama ileri getirisi ne olurdu?"
    — yalnız SEÇİM etkisini ölçer, sabit ufukta, çıkış kuralından bağımsız.
  * tam replay (backtest.walk_forward): "eşiği yükseltseydik SİSTEM ne yapardı?" — daha az aday,
    farklı pozisyon sırası, farklı sermaye kullanımı, farklı eşzamanlılık, farklı çıkışlar.
Bir eşik, seçim kalitesini artırıp sistem sonucunu kötüleştirebilir (ör. en iyi adayları alırken
portföyü boş bırakmak, ya da kalan adayların hepsini aynı rejimde toplamak). Bu yüzden buradaki
eğri BİR KARAR DEĞİL, bir hipotez kaynağıdır; kapı hâlâ tek hakemdir (replay + olasılıksal kapı).
Çıktının `capraz_not` alanı bu uyarıyı sayının YANINDA taşır.

ÖLÇÜM TANIMI. x ekseni: aday skoru (`score`, hem `trades.jsonl` hem cf defterinde ALAN olarak var —
canlı dosyadan doğrulandı). y ekseni İKİ TANE ve ikisi de ayrı raporlanır:
  * `ileri_getiri` — sinyal barından 5/10/20 bar sonraki yüzde getiri, BARLARDAN
    (`component_ic.forward_returns`, tek tanım). Çıkış kuralından ve cf sadakat kusurundan
    BAĞIMSIZDIR: cf satırından yalnız giriş anı alınır (bkz. component_ic modül başlığı, karar 4).
  * `gerceklesen_r` — defterdeki `r_multiple`. Gerçek katmanda bu CANLI çıkışın sonucudur; cf
    katmanında SİMÜLE edilmiş çıkışın (sadakat kusuru burayı KİRLETİR — etiketi alanın yanında).
Roadmap 1.3 "kâr/işlem eğrisi" der; kâr/işlem tam olarak `gerceklesen_r`dir, ama tek başına
bırakılırsa cf tarafında sadakat kusurunu taşır — bu yüzden ikisi birlikte verilir.

KATMANLAR AYRI SATIR. gerçek (n≈95) ile cf (n≈2100) asla havuzlanmaz: 22:1 oranıyla cf, gerçeği
boğar ve raporlanan eğri fiilen cf'in eğrisi olur (`score_calibration`ın yıllarca yaptığı hata).
"""
from __future__ import annotations

import math

import pandas as pd

from . import store, obs, sieve
from . import component_ic as cic

THRESHOLD_FILE = "threshold_curve.json"

# TARAMA IZGARASI: 40..90 adım 5. Alt uç canlı eşiğin (60) belirgin altından başlar ki eşiği
# DÜŞÜRMEK de bir seçenek olarak görünsün — yalnız yukarı bakan bir tarama, cevabı soruya gömer.
# Üst uç 90: 95 işlemlik defterde 90 üstünde kalan aday sayısı tek haneye düşer ve her hücre
# ölçülemedi olurdu.
THRESHOLDS = tuple(range(40, 95, 5))
MIN_N = 10          # bir eşik hücresinin ortalamasının raporlanması için en az gözlem. Altında
                    # ortalama YAZILMAZ (None) — 3 gözlemden ortalama R çıkarmak, eğriyi en sağ
                    # ucunda gürültüyle yukarı büken tam olarak o hatadır.
CI_Z = 1.96


def _ort_ci(vals: list) -> dict:
    """Ortalama + %95 güven aralığı (normal yaklaşım, SE = s/sqrt(n)).

    ARALIK ZORUNLU: eşik yükseldikçe n düşer, yani eğrinin sağ ucu DOĞASI GEREĞİ daha gürültülüdür.
    Aralıksız bir eğri, tam da en az veriye dayanan ucunda en ikna edici görünür — 07-28'de
    "80 üstü +0.066R" çıkarımı bu yanılsamanın ta kendisiydi (o dilimde n azdı ve replay yanlışladı).

    n<MIN_N → hepsi None (UYDURMA YASAĞI). Standart sapma sıfırsa (tek değerin tekrarı) aralık
    ortalamanın kendisine çöker; bu bir kesinlik iddiası değil, örneklemin gerçekten sabit
    olmasıdır ve `sd` alanından okunur."""
    n = len(vals)
    if n < MIN_N:
        return {"ort": None, "n": n, "ci": None, "sd": None, "neden": f"n<{MIN_N}"}
    ort = sum(vals) / n
    var = sum((v - ort) ** 2 for v in vals) / (n - 1) if n > 1 else 0.0
    sd = math.sqrt(var)
    se = sd / math.sqrt(n)
    return {"ort": round(ort, 4), "n": n, "sd": round(sd, 4), "neden": None,
            "ci": {"lo": round(ort - CI_Z * se, 4), "hi": round(ort + CI_Z * se, 4), "seviye": 0.95}}


def _gozlemler() -> tuple[list, dict]:
    """(katman, ticker, tarih, skor, gerçekleşen_r) satırları — eleme muhasebesiyle.

    POPÜLASYON `component_ic._rows()` İLE AYNI OLMALI (gerçek: trades.jsonl'in P- biçimli plan_id
    taşıyan satırları; cf: `resolved_rows(entered_only=True)`). Farklı iki popülasyondan hesaplanan
    iki tablo panoda yan yana durunca okur onları karşılaştırır — ve karşılaştırma sessizce
    geçersizdir. Buradaki fark yalnız EK ALANLARdır (skor + gerçekleşen R), satır kümesi değil."""
    from . import counterfactual as cf
    rows, sayim = [], {"gercek": 0, "cf": 0}
    with sieve.Sieve("threshold_curve.gercek") as sv:
        for t in store.read_jsonl("trades.jsonl"):
            pid = str(t.get("plan_id") or "")
            parts = pid.split("-")
            if not pid.startswith("P-") or len(parts) < 5:
                sv.drop("sema:plan_id_biçimi:eski_şema"); continue
            if t.get("score") is None:
                sv.drop("sema:eksik_alan:score"); continue
            sv.keep()
            rows.append(("gercek", parts[4], "-".join(parts[1:4]), float(t["score"]),
                         None if t.get("r_multiple") is None else float(t["r_multiple"])))
            sayim["gercek"] += 1
    with sieve.Sieve("threshold_curve.cf") as sv:
        for r in cf.resolved_rows(entered_only=True):
            if not r.get("ticker") or not r.get("date"):
                sv.drop("sema:eksik_alan:ticker_veya_date"); continue
            if r.get("score") is None:
                sv.drop("sema:eksik_alan:score"); continue
            sv.keep()
            rows.append(("cf", str(r["ticker"]), str(r["date"])[:10], float(r["score"]),
                         None if r.get("r_multiple") is None else float(r["r_multiple"])))
            sayim["cf"] += 1
    return rows, sayim


def build() -> dict | None:
    """Eşik × katman tablosu. Hiç gözlem yoksa ya da bar evreni okunamadıysa None (boş tablo
    yazıp "ölçtük" izlenimi vermek, ölçmemekten kötüdür)."""
    rows, sayim = _gozlemler()
    if not rows:
        return None
    per = cic._load_universe()
    if not per:
        obs.warn("threshold_curve_no_bars", detail="önbellekte bar yok — eşik eğrisi ölçülemedi")
        return None

    # İleri getiri serileri sembol başına BİR KEZ (satır başına değil) — 2200 satırın çoğu aynı
    # sembolün farklı günleri.
    gerekli = {t for _, t, _, _, _ in rows}
    fwd: dict = {}
    for t in sorted(gerekli & set(per)):
        try:
            fwd[t] = pd.DataFrame(cic.forward_returns(per[t]))
        except Exception as e:
            obs.warn("threshold_curve_frame_failed", ticker=t, error=f"{type(e).__name__}: {e}")

    # (katman, skor, {ufuk: getiri}, gerçekleşen_r)
    gozlem: list = []
    with sieve.Sieve("threshold_curve.eslesme") as sv:
        for katman, ticker, dstr, skor, rmul in rows:
            frame = fwd.get(ticker)
            if frame is None:
                sv.drop("sema:bar_yok:sembol"); continue
            d = pd.Timestamp(dstr)
            if d not in frame.index:
                # AYNI KÖK, AYNI YASA (2026-08-07): bu aşama `component_ic` ile BİREBİR aynı
                # çerçeveyi (cic._load_universe) ve aynı satırları görüyor, bu yüzden aynı 7 satırı
                # (hepsi DD, bütünlük defterinin dışladığı 2025-11-04 öncesi) düşürüyordu. Sınıflama
                # tek yerde: `cic.eslesme_nedeni` — gerekçe orada yazılı.
                sv.drop(cic.eslesme_nedeni(ticker, dstr)); continue
            sv.keep()
            satir = frame.loc[d]
            gozlem.append((katman, skor,
                           {h: (None if pd.isna(satir[h]) else float(satir[h])) for h in cic.HORIZONS},
                           rmul))

    egri: dict = {}
    for lay in ("gercek", "cf"):
        alt = [g for g in gozlem if g[0] == lay]
        noktalar = []
        for esik in THRESHOLDS:
            gecen = [g for g in alt if g[1] >= esik]
            nokta = {"esik": esik, "n_aday": len(gecen),
                     # ADAY ORANI: "eşiği 80 yapsak defterin %12'si kalır" cümlesi, ham sayıdan
                     # daha okunabilir bir maliyet ölçüsüdür (kanıt hızının doğrudan çarpanı).
                     "aday_orani": round(len(gecen) / len(alt), 4) if alt else None,
                     "ileri_getiri": {str(h): _ort_ci([g[2][h] for g in gecen if g[2][h] is not None])
                                      for h in cic.HORIZONS},
                     "gerceklesen_r": _ort_ci([g[3] for g in gecen if g[3] is not None])}
            noktalar.append(nokta)
        egri[lay] = noktalar

    out = {
        "esikler": list(THRESHOLDS), "horizons": list(cic.HORIZONS), "katmanlar": ["gercek", "cf"],
        "canli_min_score": _canli_min_score(),
        "getiri_tanimi": "close[t+h]/close[t]-1 (sinyal barı kapanışından, yüzde; R'ye bölünmez)",
        "r_tanimi": "defterdeki r_multiple — gerçek katmanda canlı çıkış, cf katmanında SİMÜLE çıkış",
        "cf_sadakat": ("cf `ileri_getiri`si barlardan gelir ve sadakat kusurundan BAĞIMSIZDIR; cf "
                       "`gerceklesen_r`si ise simüle çıkıştan gelir ve KUSURU TAŞIR"),
        "capraz_not": ("SEÇİM ETKİSİ ≠ SİSTEM ETKİSİ: 2026-07-28 H2 replay'i min_score 60→80'i "
                       "Δ-0.095 ile ÇÜRÜTTÜ (P=0.089) — dilim istatistiği yükselirken tam replay "
                       "kötüleşebilir (daha az aday, farklı eşzamanlılık ve sermaye kullanımı). "
                       "Bu eğri hipotez üretir; kapı hâlâ tek hakemdir."),
        "min_n": MIN_N, "egri": egri,
        "n_gozlem": {"gercek": sayim["gercek"], "cf": sayim["cf"], "eslesen": len(gozlem)},
        sieve.PROV_KEY: sieve.provenance(sayim["gercek"] + sayim["cf"], sayim["gercek"], sayim["cf"],
                                         stages_=("threshold_curve.gercek", "threshold_curve.cf",
                                                  "threshold_curve.eslesme")),
    }
    out["verdict"] = _verdict(out)
    store.write_json(THRESHOLD_FILE, out)
    obs.log("threshold_curve", n_gercek=sayim["gercek"], n_cf=sayim["cf"], n_eslesen=len(gozlem))
    return out


def _canli_min_score() -> float | None:
    """Canlı eşik — `config.load_strategy()` üzerinden (strategy.yaml YAML'dir, store.read_json onu
    okuyamaz; ilk deneme None dönerse buraya düşülür)."""
    try:
        from . import config
        return float(config.load_strategy()["params"].get("entry.min_score"))
    except Exception as e:
        obs.warn("threshold_curve_min_score_unreadable", error=f"{type(e).__name__}: {e}")
        return None


def _verdict(doc: dict) -> str:
    """Tek cümlelik okuma. HÜKÜM YALNIZ GERÇEK KATMANDAN + yalnız ÖLÇÜLEBİLEN noktalardan kurulur;
    cf katmanı cümlede BAĞLAM olarak anılır (kuzey yıldızının 1. ölçütüyle aynı yasa)."""
    g = [p for p in doc["egri"]["gercek"] if p["gerceklesen_r"]["ort"] is not None]
    if not g:
        return (f"gerçek katmanda ölçülebilen eşik noktası yok (her nokta n<{MIN_N}) — eşik "
                f"hakkında bir şey söylenemez")
    en_iyi = max(g, key=lambda p: p["gerceklesen_r"]["ort"])
    canli = next((p for p in g if p["esik"] == doc.get("canli_min_score")), None)
    kuyruk = ""
    if canli and en_iyi["esik"] != canli["esik"]:
        ci_c, ci_e = canli["gerceklesen_r"]["ci"], en_iyi["gerceklesen_r"]["ci"]
        # ARALIKLAR ÖRTÜŞÜYORSA FARK GÖSTERİLEMEDİ: iki ortalamanın sırası tek başına bir kanıt
        # değildir; örtüşen aralıklarda "daha iyi" demek gürültüyü bulgu ilan etmektir.
        ortusuyor = bool(ci_c and ci_e and ci_c["lo"] <= ci_e["hi"] and ci_e["lo"] <= ci_c["hi"])
        kuyruk = (f" · canlı eşik {canli['esik']} (ort R {canli['gerceklesen_r']['ort']}, "
                  f"n={canli['gerceklesen_r']['n']}) — aralıklar "
                  f"{'ÖRTÜŞÜYOR: fark gösterilemedi' if ortusuyor else 'AYRIK'}")
    return (f"gerçek katmanda en yüksek ortalama R eşiği: {en_iyi['esik']} "
            f"(ort R {en_iyi['gerceklesen_r']['ort']}, n={en_iyi['gerceklesen_r']['n']})" + kuyruk)
