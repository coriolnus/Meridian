#!/usr/bin/env python3
"""research/olcumler/edg019_skill_gorus_etki/olcum.py — EDG-2026-019 RESMÎ ÖLÇÜM (TSK-073, 2026-09-03).

NE ÖLÇER. `research/cards/EDG-2026-019-skill-gorus-defteri.yaml`nin `success_metric` maddesi:
yüzey-başına (aday-sıralayıcı, çıkış), skill-başına tarih-kümeli bootstrap CI + Benjamini-Hochberg
FDR süzgeci; TERFİ ADAYI = FDR-sağkalan VE etki eşiği geçildi VE n_min görüş var. Bu betik o
hükmü DONMUŞ bir girdiden üretir — kartın kendi cümlesi: "HİÇBİR TERFİ OTOMATİK DEĞİL" (bu betik
de öyle: yalnız ÖLÇER, hükmü Rol-1 karta + K defterine işler, CLAUDE.md §3/§5).

NEDEN motor CANLI STATE OKUMAZ (ajan sınırı). `meridian.skill_gorus.rapor()` AYNI hükmü zaten
üretir ama LİVE `state/skill_gorusleri.jsonl` + cf/trades defterlerini okur (`defter()`,
`_gozlemler()`). Bu turun ajanı canlıya dokunamaz (CLAUDE.md §3 ajan sınırı) — bu yüzden girdi
`--girdi` ile verilen DONMUŞ bir dosyadır (Rol-1 A1'den çeker); betik `research/olcumler/`
altında yaşar ve `meridian/` HİÇ DEĞİŞTİRİLMEZ.

GİRDİ ŞEMASI — NEDEN TEK DOSYA. Motorun kendi "t-anı girdi kesiti" biçimi
(`meridian.skill_gorus.SNAPSHOT_ALANLARI`: skill, tarih, hedef, skor, karar, r, mfe_r, kaynak)
GÖRÜŞ tarafını (skor → aday-sıralayıcı, karar → çıkış) ve SONUÇ tarafını (r, mfe_r) TEK satırda
taşır — iki ayrı dondurulmuş dosyayı `hedef` anahtarıyla elle eşleştirme riski (bir taraf eksik/
sıralaması farklı donarsa sessizce yanlış eşleşir) böylece YOK. Aynı şema burada TEKRAR
TANIMLANIR (`TUM_ALANLAR`) — motor modülünün `SNAPSHOT_ALANLARI`sını buradan İTHAL ETMİYORUZ
çünkü o alan motorun t-çiti sözleşmesidir (kadans/kuyruk davranışına bağlı); burada yaşayan kopya
YALNIZ şema-adları içindir ve iki liste ayrışırsa `tests/test_edg019_olcum_v389.py` bunu ölçer.

EŞİKLER KARTTAN OKUNUR, KODDAN DEĞİL (CLAUDE.md §2). Kart `success_metric` alanında SERBEST
METİN taşır (yapılandırılmış eşik alanı yok) — `esikleri_karttan_oku()` dört sayıyı (FDR q,
|rank-IC| eşiği, n_min, CI seviyesi) o cümleden REGEX'le çeker; biri bulunamazsa ValueError
(UYDURMA YASAĞI — eksik bir eşikle "ölçüldü" demek uydurmaktır). `meridian.skill_gorus.KART_*`
sabitleri BİLEREK kullanılmaz (o modülün kendi donmuş kopyası — bugün karttakiyle özdeş ama bu
betiğin doğruluğu o özdeşliğe BAĞIMLI OLMAMALI; `esikleri_karttan_oku()`nün testleri bu iki
kaynağın bugün örtüştüğünü AYRICA doğrular, ayrışma çivisi).

YENİDEN KULLANILAN SAF PRİMİTİFLER (motor DEĞİŞTİRİLMEDİ, yalnız İTHAL EDİLDİ — istatistiği
İKİNCİ KEZ YAZMAMAK için): `meridian.faz5_cikis.tarih_kumeli_bootstrap` (kartın dondurduğu
YÖNTEM — "YENİDEN YAZILMAZ, ÇAĞRILIR" kendi docstring'inin sözü) ve
`meridian.skill_gorus._rank_ic_ayristir` (rank-IC'nin gözlem-başına ayrıştırması, `analytics.
spearman_ic` ile çapraz doğrulamalı). Motorun `bootstrap_p`si CI seviyesini PARAMETRE ALMIYOR
(içeride `KART_CI` sabitine bağlı) — bu yüzden `_bootstrap_p_karttan()` AYNI ikili-arama
algoritmasını karttan okunan CI seviyesiyle burada tekrar eder (~15 satır, gerekçeli kopya);
altındaki bootstrap PRİMİTİFİ yine motordan ÇAĞRILIR, yeniden YAZILMAZ.

KULLANIM:
    python olcum.py --girdi <donmuş.jsonl> --kuru        # yalnız şema kontrolü, istatistik YOK
    python olcum.py --girdi <donmuş.jsonl> [--cikti /yol.json]   # tam ölçüm

POZİTİF KONTROL: `tests/test_edg019_olcum_v389.py` sentetik, BİLİNEN rank-IC'li bir seri besler
ve betiğin onu GERÇEKTEN bulduğunu (FDR-sağkalan + terfi adayı) kanıtlar; aynı testin negatif
kontrolü aynı seriyi KARIŞTIRIP (IC'yi sıfırlayıp) betiğin artık BULMADIĞINI gösterir — dedektör
her zaman "terfi buldum" demiyor mu, yoksa gerçekten mi ölçüyor sorusunun cevabı.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

import yaml

KOK = pathlib.Path(__file__).resolve().parents[3]
KART_YOLU = KOK / "research" / "cards" / "EDG-2026-019-skill-gorus-defteri.yaml"

# --- girdi şeması: motorun "t-anı girdi kesiti" biçiminin BURADAKİ AYNI KOPYASI (yukarı bkz) ---
ZORUNLU_ALANLAR = ("skill", "tarih", "hedef")
TUM_ALANLAR = ("skill", "tarih", "hedef", "skor", "karar", "r", "mfe_r", "kaynak")

# P_ARAMA_ADIM BURADA TANIMLANMAZ (düzeltme turu 2026-09-03, inceleme bulgusu): bu bir KART EŞİĞİ
# DEĞİL — bootstrap p'nin ikili-arama ÇÖZÜNÜRLÜĞÜdür (kaç basamak ince arandığı), success_metric'te
# hiç geçmez. `esikleri_karttan_oku()`nün dört eşiği gibi karttan OKUNMAZ; motor karşılığı VAR
# (`meridian.skill_gorus.P_ARAMA_ADIM = 7`) ve bu tamamen ALGORİTMİK bir seçimdir (yön: kilidi
# AÇMA yönünde yanılmaz, yalnız p'nin kaç ondalık hassasiyetle raporlandığını belirler) — kart
# provenance'ı olmayan bir sayıyı burada İKİNCİ KEZ yazıp iki kopyanın SESSİZCE ayrışmasına izin
# vermek yerine, doğrudan motordan TÜRETİLİR (tek-kaynak). `_bootstrap_p_karttan()` bunu çağrı
# anında `meridian.skill_gorus.P_ARAMA_ADIM`den okur; motorun çözünürlüğü değişirse bu betik
# OTOMATİK izler — `tests/test_edg019_olcum_v389.py::test_p_arama_adim_motordan_turetiliyor` bu
# türetimi ölçer.


# ======================================================================================
# EŞİKLER — KARTTAN OKUNUR
# ======================================================================================

def esikleri_karttan_oku(kart_yolu: pathlib.Path = KART_YOLU) -> dict:
    """Kartın `success_metric` serbest-metninden dört eşiği REGEX'le çeker (yukarı bkz — UYDURMA
    YASAĞI: eksik eşik ValueError, sessizce varsayılan atanmaz)."""
    kart = yaml.safe_load(kart_yolu.read_text(encoding="utf-8"))
    if not isinstance(kart, dict):
        raise ValueError(f"kart sözlük değil: {kart_yolu}")
    metin = " ".join(str(kart.get("success_metric", "")).split())

    def _bul(desen: str, ad: str) -> str:
        m = re.search(desen, metin)
        if not m:
            raise ValueError(
                f"kart eşiği '{ad}' success_metric metninde bulunamadı ({kart_yolu}) — "
                "betik eşiği UYDURAMAZ, kart cümlesi değişmiş olabilir"
            )
        return m.group(1)

    fdr_q = float(_bul(r"FDR\s+q\s*=\s*([\d.]+)", "fdr_q"))
    rank_ic_esigi = float(_bul(r"\|rank-IC\|\s*>=\s*([\d.]+)", "rank_ic_esigi"))
    n_min = int(_bul(r"n_min\s*=\s*(\d+)", "n_min"))
    ci_yuzde = float(_bul(r"bootstrap\s+%(\d+)\s*CI", "ci_seviye"))
    return {
        "fdr_q": fdr_q, "rank_ic_esigi": rank_ic_esigi, "n_min": n_min,
        "ci_seviye": ci_yuzde / 100.0,
        "kart_id": kart.get("card_id"), "kart_yolu": str(kart_yolu),
    }


def esikleri_motorla_karsilastir(esikler: dict) -> list[str]:
    """AYRIŞMA ÇİVİSİ (tek-kaynak yasası): karttan okunan eşikler `meridian.skill_gorus.KART_*`
    sabitleriyle bugün örtüşüyor mu? Örtüşmezse betik YİNE karttan okunanı kullanır (kart SSoT'tur)
    ama fark ADIYLA raporlanır — sessiz sürüklenme YOK."""
    from meridian import skill_gorus as _sg
    farklar = []
    if esikler["fdr_q"] != _sg.KART_FDR_Q:
        farklar.append(f"fdr_q: kart={esikler['fdr_q']} motor={_sg.KART_FDR_Q}")
    if esikler["rank_ic_esigi"] != _sg.KART_ETKI_RANK_IC:
        farklar.append(f"rank_ic_esigi: kart={esikler['rank_ic_esigi']} motor={_sg.KART_ETKI_RANK_IC}")
    if esikler["n_min"] != _sg.KART_N_MIN:
        farklar.append(f"n_min: kart={esikler['n_min']} motor={_sg.KART_N_MIN}")
    if esikler["ci_seviye"] != _sg.KART_CI:
        farklar.append(f"ci_seviye: kart={esikler['ci_seviye']} motor={_sg.KART_CI}")
    return farklar


# ======================================================================================
# GİRDİ OKUMA + ŞEMA DOĞRULAMA (--kuru bunu koşar, istatistiği KOŞMAZ)
# ======================================================================================

def gozlem_satirlarini_oku(girdi_yolu: pathlib.Path) -> list[dict]:
    satirlar: list[dict] = []
    for i, ham in enumerate(girdi_yolu.read_text(encoding="utf-8").splitlines(), start=1):
        ham = ham.strip()
        if not ham:
            continue
        try:
            satirlar.append(json.loads(ham))
        except json.JSONDecodeError as exc:
            raise ValueError(f"{girdi_yolu}:{i} JSON ayrıştırılamadı: {exc}") from exc
    return satirlar


def sema_ihlallerini_bul(satirlar: list[dict]) -> list[str]:
    """Zorunlu alan eksikliği · görüşsüz satır (skor VE karar ikisi de boş) · tanınmayan alan
    (YASA 4: sessiz yutma yok — adıyla raporlanır, satır atılmaz/düzeltilmez)."""
    ihlaller: list[str] = []
    for i, s in enumerate(satirlar):
        if not isinstance(s, dict):
            ihlaller.append(f"satır {i}: dict değil ({type(s).__name__})")
            continue
        konum = f"satır {i} [{s.get('skill', '?')}/{s.get('hedef', '?')}]"
        eksik = [a for a in ZORUNLU_ALANLAR if not s.get(a)]
        if eksik:
            ihlaller.append(f"{konum}: zorunlu alan eksik: {eksik}")
        if s.get("skor") is None and s.get("karar") is None:
            ihlaller.append(f"{konum}: skor VE karar ikisi de boş — görüşsüz satır")
        yabanci = [a for a in s if a not in TUM_ALANLAR]
        if yabanci:
            ihlaller.append(f"{konum}: tanınmayan alan: {yabanci}")
    return ihlaller


# ======================================================================================
# GÖRÜŞ + SONUÇ AYRIMI — motorun `_gorusleri_tureti()` eşleme kuralının AYNISI
# ======================================================================================

def gorusleri_ve_sonuclari_ayir(satirlar: list[dict]) -> tuple[list[dict], dict[str, dict]]:
    """Skor doluysa aday-sıralayıcı görüşü, HER satır çıkış görüşü (motorun kuralı — `karar`
    boşsa "?" ile doldurulur, cikis çözücüsü karar DEĞERİNİ değil r/mfe_r'yi okur). `sonuclar`
    hedef→satır sözlüğüdür (aynı satır hem görüş hem sonuç kaynağıdır — girdi şeması gereği)."""
    gorusler: list[dict] = []
    sonuclar: dict[str, dict] = {}
    for g in satirlar:
        sk, hedef, tarih = str(g["skill"]), str(g["hedef"]), str(g["tarih"])
        if g.get("skor") is not None:
            gorusler.append({"skill": sk, "yuzey": "aday-siralayici", "hedef": hedef,
                              "skor": float(g["skor"]), "tarih": tarih})
        gorusler.append({"skill": sk, "yuzey": "cikis", "hedef": hedef,
                          "karar": str(g.get("karar") or "?"), "tarih": tarih})
        sonuclar[hedef] = g
    return gorusler, sonuclar


# ======================================================================================
# BOOTSTRAP p — motorun `bootstrap_p` ikili-aramasının CI-parametreli kopyası (yukarı bkz)
# ======================================================================================

def _bootstrap_p_karttan(degerler, tarihler, ci_seviye: float) -> dict:
    from meridian import faz5_cikis as _f5
    from meridian import skill_gorus as _sg

    adim = _sg.P_ARAMA_ADIM   # motordan TÜRETİLİR — bu betikte İKİNCİ bir kopya YOK (yukarı bkz)
    taban = _f5.tarih_kumeli_bootstrap(degerler, tarihler, seviye=ci_seviye)
    if taban.get("lo") is None:
        return {"p": None, "neden": taban.get("neden") or "aralık kurulamadı — p ÖLÇÜLEMEDİ"}
    en_sert = 1.0 - 2.0 ** -adim
    if _f5.tarih_kumeli_bootstrap(degerler, tarihler, seviye=en_sert).get("sifiri_disliyor"):
        return {"p": round(1.0 - en_sert, 4), "neden": None}
    lo, hi = 0.0, en_sert
    if not _f5.tarih_kumeli_bootstrap(degerler, tarihler, seviye=lo).get("sifiri_disliyor"):
        return {"p": 1.0, "neden": None}
    for _ in range(adim):
        orta = (lo + hi) / 2.0
        if _f5.tarih_kumeli_bootstrap(degerler, tarihler, seviye=orta).get("sifiri_disliyor"):
            lo = orta
        else:
            hi = orta
    return {"p": round(1.0 - lo, 4), "neden": None}


# ======================================================================================
# ÇÖZÜCÜLER — kartın iki ölçülen yüzeyi (aday-sıralayıcı, çıkış); eşikler PARAMETRE
# ======================================================================================

def cozucu_siralayici(gorusler: list[dict], sonuclar: dict, esikler: dict) -> dict:
    """Skill başına rank-IC (skor → gerçekleşen R) + kümeli CI/p. Kartın `n_min`/etki eşiği
    PARAMETRE olarak gelir (koddan değil karttan) — bkz. modül docstring'i."""
    from meridian import faz5_cikis as _f5
    from meridian import skill_gorus as _sg

    per: dict[str, list] = {}
    eslesmeyen = 0
    for g in gorusler:
        if g.get("yuzey") != "aday-siralayici":
            continue
        s = sonuclar.get(g["hedef"])
        if s is None or s.get("r") is None:
            eslesmeyen += 1
            continue
        per.setdefault(g["skill"], []).append((float(g["skor"]), float(s["r"]), str(g["tarih"])))
    out: dict[str, dict] = {}
    for sk, rows in sorted(per.items()):
        n = len(rows)
        if n < esikler["n_min"]:
            out[sk] = {"n": n, "kova": f"ÖLÇÜLDÜ — ÖRNEKLEM YETERSİZ {n}/{esikler['n_min']}",
                       "olcum": None, "p": None}
            continue
        z, ic = _sg._rank_ic_ayristir([(a, b) for a, b, _ in rows])
        if ic is None:
            out[sk] = {"n": n, "kova": "ÖLÇÜLEMEDİ", "olcum": None, "p": None,
                       "neden": "rank-IC tanımsız (skor ya da R rütbelerinde değişim yok)"}
            continue
        tarihler = [t for *_, t in rows]
        ci = _f5.tarih_kumeli_bootstrap(z, tarihler, seviye=esikler["ci_seviye"])
        pp = _bootstrap_p_karttan(z, tarihler, esikler["ci_seviye"])
        out[sk] = {
            "n": n, "kova": "OLCULDU",
            "olcum": {"rank_ic": round(ic, 4), "lo": ci.get("lo"), "hi": ci.get("hi"),
                      "n_kume": ci.get("n_kume")},
            "p": pp.get("p"), "p_neden": pp.get("neden"),
            "etki_esigi_gecti": bool(abs(ic) >= esikler["rank_ic_esigi"]),
            "yon": (1 if ic > 0 else (-1 if ic < 0 else 0)),
        }
    return {"skiller": out, "eslesmeyen_gorus": eslesmeyen,
            "metrik": "rank-IC (skor → gerçekleşen R)"}


def cozucu_cikis(gorusler: list[dict], sonuclar: dict, esikler: dict) -> dict:
    """Skill başına havuza-göre çıkış katkısı (kartın "çıkış-katkısı > 0 CI-altı" tanımı)."""
    per: dict[str, list] = {}
    eslesmeyen, havuz = 0, []
    for g in gorusler:
        if g.get("yuzey") != "cikis":
            continue
        s = sonuclar.get(g["hedef"])
        if s is None or s.get("r") is None or s.get("mfe_r") is None:
            eslesmeyen += 1
            continue
        left = float(s["mfe_r"]) - float(s["r"])
        per.setdefault(g["skill"], []).append((left, str(g["tarih"])))
        havuz.append(left)
    if not havuz:
        return {"skiller": {}, "eslesmeyen_gorus": eslesmeyen,
                "metrik": "çıkış katkısı = havuz ort. left_r − skill left_r", "havuz_ort_left_r": None}
    havuz_ort = sum(havuz) / len(havuz)
    from meridian import faz5_cikis as _f5
    out: dict[str, dict] = {}
    for sk, rows in sorted(per.items()):
        n = len(rows)
        if n < esikler["n_min"]:
            out[sk] = {"n": n, "kova": f"ÖLÇÜLDÜ — ÖRNEKLEM YETERSİZ {n}/{esikler['n_min']}",
                       "olcum": None, "p": None}
            continue
        katkilar = [havuz_ort - left for left, _ in rows]
        tarihler = [t for _, t in rows]
        ci = _f5.tarih_kumeli_bootstrap(katkilar, tarihler, seviye=esikler["ci_seviye"])
        pp = _bootstrap_p_karttan(katkilar, tarihler, esikler["ci_seviye"])
        out[sk] = {
            "n": n, "kova": "OLCULDU",
            "olcum": {"katki": round(sum(katkilar) / n, 4), "lo": ci.get("lo"), "hi": ci.get("hi"),
                      "n_kume": ci.get("n_kume")},
            "p": pp.get("p"), "p_neden": pp.get("neden"),
            "etki_esigi_gecti": bool(ci.get("lo") is not None and ci["lo"] > 0),
            "yon": (1 if (ci.get("lo") is not None and ci["lo"] > 0) else
                    (-1 if (ci.get("hi") is not None and ci["hi"] < 0) else 0)),
        }
    return {"skiller": out, "eslesmeyen_gorus": eslesmeyen, "havuz_ort_left_r": round(havuz_ort, 4),
            "metrik": "çıkış katkısı = havuz ort. left_r − skill left_r (POZİTİF = daha az ödül bıraktı)"}


# ======================================================================================
# ÖLÇÜM — iki yüzey + FDR + terfi adayları (kartın TERFİ ADAYI tanımı, §success_metric)
# ======================================================================================

def olc(satirlar: list[dict], esikler: dict) -> dict:
    from meridian import skill_gorus as _sg

    gorusler, sonuclar = gorusleri_ve_sonuclari_ayir(satirlar)
    yuzeyler: dict[str, dict] = {}
    terfi: list[dict] = []
    for yuzey, cozucu in (("aday-siralayici", cozucu_siralayici), ("cikis", cozucu_cikis)):
        c = cozucu(gorusler, sonuclar, esikler)
        pler = {sk: v.get("p") for sk, v in c["skiller"].items()}
        fdr = _sg.bh_fdr(pler, q=esikler["fdr_q"])
        for sk, v in c["skiller"].items():
            v["fdr"] = fdr["aile"].get(sk)
            sagkalan = bool((v.get("fdr") or {}).get("sagkalan"))
            yeterli = sagkalan and (v.get("n") or 0) >= esikler["n_min"]
            v["terfi_adayi"] = bool(yeterli and v.get("etki_esigi_gecti") and (v.get("yon") or 0) > 0)
            if v["terfi_adayi"]:
                terfi.append({"skill": sk, "yuzey": yuzey, "n": v["n"], "p": v.get("p"),
                              "olcum": v.get("olcum")})
        yuzeyler[yuzey] = {
            "skiller": c["skiller"],
            "fdr": {k: fdr[k] for k in ("m", "q", "kritik_p")},
            "eslesmeyen_gorus": c["eslesmeyen_gorus"], "metrik": c["metrik"],
        }
    return {
        "kart": esikler.get("kart_id"), "esikler": esikler,
        "esik_ayrisma_kontrolu": esikleri_motorla_karsilastir(esikler),
        "yuzeyler": yuzeyler, "terfi_adaylari": terfi,
        "girdi_n": len(satirlar),
        "beyan": ("HİÇBİR TERFİ OTOMATİK DEĞİL — bu betik yalnız ÖLÇER; hükmü Rol-1 karta + "
                  "K defterine AYNI turda işler (CLAUDE.md §3/§5)."),
    }


# ======================================================================================
# CLI
# ======================================================================================

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="EDG-2026-019 skill görüş defteri ETKİ ölçümü (donmuş girdiden, motor DEĞİŞMEZ)")
    ap.add_argument("--girdi", required=True,
                     help="donmuş gözlem JSONL (şema: skill,tarih,hedef,skor,karar,r,mfe_r,kaynak)")
    ap.add_argument("--kart", default=str(KART_YOLU), help="kart yolu (varsayılan EDG-2026-019)")
    ap.add_argument("--kuru", action="store_true", help="yalnız şema kontrolü — istatistik KOŞMAZ")
    ap.add_argument("--cikti", default=None, help="JSON çıktısını dosyaya yaz (varsayılan: stdout)")
    a = ap.parse_args(argv)

    girdi_yolu = pathlib.Path(a.girdi)
    satirlar = gozlem_satirlarini_oku(girdi_yolu)
    ihlaller = sema_ihlallerini_bul(satirlar)

    if a.kuru:
        if ihlaller:
            print(f"BOZUK-ŞEMA · {girdi_yolu} — {len(ihlaller)} ihlal:", file=sys.stderr)
            for i in ihlaller[:50]:
                print(f"  - {i}", file=sys.stderr)
            return 1
        print(f"GÜNCEL-ŞEMA · {girdi_yolu} — {len(satirlar)} satır, ihlal yok")
        return 0

    if ihlaller:
        print(f"ŞEMA BOZUK, ölçüm KOŞULMADI — önce --kuru ile düzelt: {ihlaller[:5]}", file=sys.stderr)
        return 1

    esikler = esikleri_karttan_oku(pathlib.Path(a.kart))
    sonuc = olc(satirlar, esikler)
    cikti = json.dumps(sonuc, ensure_ascii=False, indent=2, sort_keys=True)
    if a.cikti:
        pathlib.Path(a.cikti).write_text(cikti + "\n", encoding="utf-8")
        print(f"yazıldı: {a.cikti}")
    else:
        print(cikti)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
