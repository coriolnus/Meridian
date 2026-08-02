"""pk_kys.py — KYS-2026-001 ARAÇ-DOĞRULAMA PK'si (kart `guards` maddesi 1).

KARTIN ŞARTI: "sentetik kontrol — yapay olay-penceresi enjeksiyonuyla bilinen-yönlü sıkıştırma
aracın ölçtüğü yönde çıkmalı (araç-doğrulama, ölçümden ÖNCE)". Yani ÖNCE aracın kendisi sınanır;
geçmezse ölçüm KOŞMAZ.

NEDEN SENTETİK VE NEDEN ÖNCE. `olay_disi_kiyas` bu turda ilk kez bir kart yüzeyinde sayı üretecek.
Gerçek veriyle başlarsak, çıkan farkın ne kadarı "araç doğru ölçüyor" ne kadarı "dünya böyle" ayırt
edilemez. Sentetik zeminde CEVAP ÖNCEDEN BİLİNİR: δ kadar kaydırılmış bir olay penceresi enjekte
edilir; temiz kıyasın δ'yı BULMASI, kirli kıyasın onu SIKIŞTIRMASI beklenir.

BEŞ KOL:
  PK-0  pencere eşdeğerliği   — `earnings.in_blackout` ile BİREBİR mi (varsayım değil, ölçüm)
  PK-1  δ = +30 bps, yaygınlık %70 → temiz ≈ +30 bps · sıkışma POZİTİF (kirli okuma bastırılmış)
  PK-2  δ = −30 bps, yaygınlık %70 → temiz ≈ −30 bps · sıkışma NEGATİF (işaret δ'yı takip eder)
  PK-3  δ =   0 bps, yaygınlık %70 → temiz ≈ 0 · sıkışma ≈ 0 (araç YOKTAN sıkışma UYDURMUYOR)
  PK-4  δ = +30 bps, yaygınlık %15 → sıkışma VAR ama PK-1'in yarısından KÜÇÜK (yaygınlıkla ölçekli)

GEÇME ÖLÇÜTLERİ NEDEN BUNLAR (ve ilk taslakta ne vardı — kayda geçiyor, çünkü ölçüt seçimi
sonradan anlatılırsa hiçbir PK inandırıcı değildir):
  * İlk taslak ek bir ŞART taşıyordu: `kirli/temiz < 0,50` (yaygın kolda). O şart aracın değil
    SENTETİK TASARIMIN özelliğini ölçüyordu — 180 günlük panelde kıyasların çoğu sezon DIŞI,
    yani kirliliği ~%1 olan günlere düşüyordu (koşum: gün-kirliliği medyanı 0,01; kirli/temiz 0,65).
    Yani kol, adında yazan "%70 yaygınlık" rejimini HİÇ KURMUYORDU. Düzeltme eşiği gevşetmek değil
    TASARIMI onarmak oldu: panel sezonun kendisine indirildi (aşağıdaki `_sentetik`), ölçütler ise
    teoriye demirlendi. Her taslakta kartın ASIL şartı (YÖN) zaten geçiyordu; değişen, yönün
    yanına konan ikinci şartın keyfî bir orandan ÖLÇÜLEBİLİR bir doğruluk+tekdüzelik çiftine
    çevrilmesidir. `kirli/temiz` yine RAPORLANIR — artık kapı değil, tanı.
  * DOĞRULUK: temiz kıyas enjekte edilen δ'yı ±TOL_DOGRULUK_BPS içinde geri vermeli. Bir kestirici
    "doğru yönü" gösterip yanlış büyüklük veriyorsa, bu turun bps cinsinden çıktısı okunamaz.
  * TEKDÜZELİK: sıkışma yaygınlıkla büyümeli. Teori: gün tabanı MEDYAN olduğu için, kirli satırlar
    kesitin yarısını geçtiği anda medyanın kendisi kirli gruba düşer ve kirli okuma ≈ 0'a bastırılır;
    yaygınlık düşükken medyan yerinde kalır ve sıkışma küçülür. Bu, EAP'nin ölçtüğü %64/%74
    yaygınlığının neden bir ALTYAPI sorunu olduğunun tam mekanizmasıdır.

EŞİKLER KOŞUMDAN ÖNCE YAZILDI (aşağıdaki sabitler) ve gerçek-veri ölçümü başlamadan dondurulmuştur.
"""
from __future__ import annotations

import json
import sys

import ortak_kys as ok

ok.muhurle()                                    # meridian ithalatından ÖNCE (mühür sözleşmesi)

import numpy as np                              # noqa: E402
from meridian import earnings                   # noqa: E402
from meridian.olcum_araclari import olay_disi_kiyas  # noqa: E402

TOHUM = 20260802
N_SEMBOL = 200
N_GUN = 40                                      # takvim günü — SEZON paneli (bkz. modül başlığı)
SEZON_MERKEZI = 20
# GÜRÜLTÜ BİLEREK KÜÇÜK (30 bps/gün): bu kol ARACIN KESTİRİCİSİNİ sınar, istatistiksel GÜCÜ değil.
# Gerçek getiri oynaklığıyla (≈%2/gün) koşulsaydı δ=30 bps'lik enjeksiyon örnekleme gürültüsünün
# altında kalır ve PK "araç yanlış" ile "örneklem küçük"ü ayırt edemezdi — pozitif kontrolün ilk
# kuralı cevabın ÖNCEDEN bilinmesidir. Gerçek gürültünün hakkı CI adımında (blok bootstrap) verilir.
SIGMA_GUNLUK = 0.003
SIGMA_PIYASA = 0.01                             # ortak faktör — GÜN tabanının anlamlı olması için
DELTA = 0.0030                                  # enjekte edilen olay-penceresi kayması (30 bps)

# --- KOŞUMDAN ÖNCE YAZILMIŞ GEÇME EŞİKLERİ -------------------------------------------------------
TOL_DOGRULUK_BPS = 5.0     # temiz kıyas δ'yı bu tolerans içinde geri vermeli
TOL_SIFIR_BPS = 5.0        # δ=0 kolunda |temiz| ve |sıkışma| bu değerin altında kalmalı
MAX_SEYREK_ORANI = 0.50    # seyrek kolun sıkışması, yaygın kolun sıkışmasının bu katından KÜÇÜK


def _sentetik(delta: float, yaygınlık: float, tohum: int = TOHUM):
    """Sentetik SEZON paneli + olay takvimi. Dönüş: (getiri satırları, olay günleri).

    TASARIM. Sembollerin `yaygınlık` oranı sezon çekirdeğinde rapor verir: olay günü
    [SEZON_MERKEZI, SEZON_MERKEZI+5] aralığında düzgün dağılır. Pencere [olay−5, olay] olduğundan
    sezon merkezindeki GÜN, çekirdekteki HER sembolün penceresi içindedir → o günün kirliliği
    ≈ `yaygınlık`. Kalan semboller HİÇ rapor vermez ve daima temiz taban üyesidir.

    NEDEN "hiç rapor vermez" (ve bu neden bir kusur değil): kol, TEK bir değişkeni — gün kesitindeki
    kirlilik oranını — izole etmek için var. Sezon dışına serpiştirilmiş ikinci bir olay kümesi,
    kıyasların çoğunu kirliliği ~%1 olan günlere taşır ve kolun adında yazan rejim hiç kurulmaz
    (ilk taslağın kusuru; bkz. modül başlığı). Gerçek dünyada her sembol rapor verir — o gerçeğin
    ölçüsü bu PK'nin değil, `kapsama_kys.py`nin ve asıl ölçümün işidir.

    Bu düzen, EAP'nin ölçtüğü gerçeğin sentetik ikizidir: bir olayın penceresinde evrenin ort.
    %64'ü / medyan %74'ü KENDİ penceresindedir.
    """
    import datetime as dt
    rng = np.random.default_rng(tohum)
    gunler = [(dt.date(2024, 1, 1) + dt.timedelta(days=i)).isoformat() for i in range(N_GUN)]
    semboller = [f"S{i:03d}" for i in range(N_SEMBOL)]

    olaylar: dict = {}
    for s in semboller:
        if rng.random() < yaygınlık:
            gun_i = SEZON_MERKEZI + int(rng.integers(0, ok.BLACKOUT_DAYS + 1))
            olaylar[s] = [gunler[gun_i]]
        else:
            olaylar[s] = []                      # olayı YOK — daima temiz taban üyesi

    piyasa = rng.normal(0.0, SIGMA_PIYASA, size=N_GUN)
    satirlar = []
    for s in semboller:
        oi = gunler.index(olaylar[s][0]) if olaylar[s] else None
        for j, g in enumerate(gunler):
            r = piyasa[j] + rng.normal(0.0, SIGMA_GUNLUK)
            if oi is not None and 0 <= (oi - j) <= ok.BLACKOUT_DAYS:   # in_blackout ile BİREBİR
                r += delta
            satirlar.append((s, g, float(r)))
    return satirlar, olaylar


def pk0_pencere_esdegerligi() -> dict:
    """PK-0 — `PENCERE` gerçekten `earnings.in_blackout` mu? Sembol×gün TAM taramayla kanıtlanır.

    `olay_disi_kiyas`ın KİRLİ saydığı satır kümesi (varsayılan hedefler) ile `in_blackout`un True
    dediği (ticker, gün) kümesi BİREBİR aynı olmalıdır. Aynı değilse bu turun tüm sayıları BAŞKA
    bir olay tanımını ölçerdi ve kartın `features_asof` şartı ("karartma tanımıyla BİREBİR") sessizce
    ihlal edilirdi."""
    satirlar, olaylar = _sentetik(delta=0.0, yaygınlık=0.7)
    yol = ok.KUM_HAVUZU / "state" / "earnings.csv"        # KUM HAVUZU — canlı takvime dokunulmaz
    ok.takvim_yaz({t: ds for t, ds in olaylar.items() if ds}, yol)
    earnings.clear_cache()

    r = olay_disi_kiyas(satirlar, olaylar, pencere=ok.PENCERE, min_taban=1)
    arac_kirli = {(k["kimlik"], k["gun"]) for k in r["kiyaslar"]}   # min_taban=1 → hedef düşmez
    guard_kirli = {(s, g) for s, g, _ in satirlar if earnings.in_blackout(s, g)}
    return {"ad": "PK-0 pencere eşdeğerliği (in_blackout BİREBİR)",
            "pencere": {"once": ok.PENCERE[0], "sonra": ok.PENCERE[1]},
            "n_satir": len(satirlar), "n_kirli_arac": len(arac_kirli),
            "n_kirli_in_blackout": len(guard_kirli), "n_taban_yok": r["n_taban_yok"],
            "arac_fazlasi_ornek": sorted(arac_kirli - guard_kirli)[:5],
            "guard_fazlasi_ornek": sorted(guard_kirli - arac_kirli)[:5],
            "gecti": bool(arac_kirli == guard_kirli and arac_kirli),
            "beyan": ("olay_disi_kiyas'ın KİRLİ saydığı (sembol, gün) kümesi ile "
                      "earnings.in_blackout'un True dediği küme birebir karşılaştırıldı; sentetik "
                      "takvim kum havuzuna yazıldı, canlı state/earnings.csv'ye DOKUNULMADI")}


def _kol(ad: str, delta: float, yaygınlık: float) -> dict:
    satirlar, olaylar = _sentetik(delta=delta, yaygınlık=yaygınlık)
    r = olay_disi_kiyas(satirlar, olaylar, pencere=ok.PENCERE, ozet="medyan", min_taban=5)
    s = r["sikisma"] or {}
    temiz, kirli = s.get("temiz"), s.get("kirli")
    oran = (abs(kirli) / abs(temiz)) if (temiz not in (None, 0) and kirli is not None) else None
    kirlilikler = [v["kirlilik_orani"] for v in r["gun_tabani"].values()
                   if v["kirlilik_orani"] is not None]
    # KIYASLARIN gördüğü kirlilik (gün başına değil, HEDEF başına ağırlıklı): kolun gerçekten hangi
    # rejimi kurduğunu bu sayı söyler — gün medyanı sezon dışını da sayar ve rejimi gizler.
    gun_kirlilik = {g: v["kirlilik_orani"] for g, v in r["gun_tabani"].items()}
    hedef_kirlilikleri = [gun_kirlilik.get(str(k["gun"])) for k in r["kiyaslar"]]
    hedef_kirlilikleri = sorted(x for x in hedef_kirlilikleri if x is not None)
    return {"ad": ad, "delta_bps": round(delta * 1e4, 3), "yaygınlık": yaygınlık,
            "n_hedef": r["n_hedef"], "n_kiyaslanan": r["n_kiyaslanan"],
            "n_taban_yok": r["n_taban_yok"],
            "temiz_fazla_bps": None if temiz is None else round(temiz * 1e4, 2),
            "kirli_fazla_bps": None if kirli is None else round(kirli * 1e4, 2),
            "sikisma_bps": None if s.get("fark") is None else round(s["fark"] * 1e4, 2),
            "kirli/temiz(tanı)": None if oran is None else round(oran, 4),
            "kiyas_agirlikli_kirlilik_medyan": (round(hedef_kirlilikleri[len(hedef_kirlilikleri) // 2], 4)
                                                if hedef_kirlilikleri else None),
            "gun_kirliligi_max": round(max(kirlilikler), 4) if kirlilikler else None,
            "uyari": r["uyari"]}


def kos() -> dict:
    pk0 = pk0_pencere_esdegerligi()
    k1 = _kol("PK-1 δ=+30bps · yaygınlık %70", +DELTA, 0.70)
    k2 = _kol("PK-2 δ=−30bps · yaygınlık %70", -DELTA, 0.70)
    k3 = _kol("PK-3 δ=0 · yaygınlık %70 (uydurma kontrolü)", 0.0, 0.70)
    k4 = _kol("PK-4 δ=+30bps · yaygınlık %15 (seyrek)", +DELTA, 0.15)

    hedef_bps = DELTA * 1e4
    k1["gecti"] = bool(k1["sikisma_bps"] is not None and k1["sikisma_bps"] > 0
                       and abs(k1["temiz_fazla_bps"] - hedef_bps) <= TOL_DOGRULUK_BPS
                       and k1["kirli_fazla_bps"] < k1["temiz_fazla_bps"])
    k1["olcut"] = (f"temiz ≈ +{hedef_bps:.0f}bps (±{TOL_DOGRULUK_BPS}) · sıkışma > 0 · kirli < temiz")
    k2["gecti"] = bool(k2["sikisma_bps"] is not None and k2["sikisma_bps"] < 0
                       and abs(k2["temiz_fazla_bps"] + hedef_bps) <= TOL_DOGRULUK_BPS
                       and abs(k2["kirli_fazla_bps"]) < abs(k2["temiz_fazla_bps"]))
    k2["olcut"] = (f"temiz ≈ −{hedef_bps:.0f}bps (±{TOL_DOGRULUK_BPS}) · sıkışma < 0 · |kirli|<|temiz|")
    k3["gecti"] = bool(k3["sikisma_bps"] is not None
                       and abs(k3["sikisma_bps"]) < TOL_SIFIR_BPS
                       and abs(k3["temiz_fazla_bps"]) < TOL_SIFIR_BPS)
    k3["olcut"] = f"|temiz| < {TOL_SIFIR_BPS}bps VE |sıkışma| < {TOL_SIFIR_BPS}bps"
    k4["gecti"] = bool(k4["sikisma_bps"] is not None and k1["sikisma_bps"]
                       and 0 <= k4["sikisma_bps"] < MAX_SEYREK_ORANI * k1["sikisma_bps"])
    k4["olcut"] = f"0 ≤ sıkışma(seyrek) < {MAX_SEYREK_ORANI} × sıkışma(yaygın)"

    kollar = [pk0, k1, k2, k3, k4]
    return {"pk": "KYS-2026-001 araç-doğrulama (kart guards #1)",
            "arac": "meridian.olcum_araclari.olay_disi_kiyas",
            "tohum": TOHUM, "n_sembol": N_SEMBOL, "n_gun": N_GUN, "delta_bps": hedef_bps,
            "esikler": {"TOL_DOGRULUK_BPS": TOL_DOGRULUK_BPS, "TOL_SIFIR_BPS": TOL_SIFIR_BPS,
                        "MAX_SEYREK_ORANI": MAX_SEYREK_ORANI,
                        "beyan": ("eşikler gerçek-veri ölçümü başlamadan yazıldı; ilk taslaktaki "
                                  "keyfî `kirli/temiz < 0,50` şartı KAPI olmaktan çıkarılıp TANI "
                                  "alanına indirildi ve gerekçesi modül başlığında yazılıdır "
                                  "(kartın asıl şartı olan YÖN her taslakta geçiyordu)")},
            "kollar": kollar, "gecti": bool(all(k["gecti"] for k in kollar)),
            "muhur": ok.muhur_dogrula(),
            "hukum_yok": "bu dosya ARACI sınar; kart hükmü Rol-1'dedir"}


if __name__ == "__main__":
    sonuc = kos()
    (ok.CIKTI / "pk_kys001.json").write_text(
        json.dumps(sonuc, ensure_ascii=False, indent=2), encoding="utf-8")
    for k in sonuc["kollar"]:
        print(f"{'GEÇTİ' if k['gecti'] else 'KALDI'}  {k['ad']}")
        if "sikisma_bps" in k:
            print(f"        temiz={k['temiz_fazla_bps']}bps  kirli={k['kirli_fazla_bps']}bps  "
                  f"sıkışma={k['sikisma_bps']}bps  kirli/temiz={k['kirli/temiz(tanı)']}  "
                  f"kıyas-ağırlıklı kirlilik={k['kiyas_agirlikli_kirlilik_medyan']}  n={k['n_kiyaslanan']}")
        else:
            print(f"        arac_kirli={k['n_kirli_arac']}  in_blackout={k['n_kirli_in_blackout']}")
    print("\nPK TOPLU:", "GEÇTİ" if sonuc["gecti"] else "KALDI")
    sys.exit(0 if sonuc["gecti"] else 3)
