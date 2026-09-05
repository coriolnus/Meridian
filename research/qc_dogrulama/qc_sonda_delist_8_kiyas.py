#!/usr/bin/env python3
"""EDG-2026-021 ⑤ — QC delist sondasının YEREL KIYASI (8 emekli sembol).

Ayrım burada tutulur: `qc_sonda_delist_8.py` QC'de koşar ve YALNIZ QC'nin cevabını basar;
kıyas YEREL yapılır, çünkü QC Research repo dosyalarını GÖREMEZ. Yerel tarihler buraya ELLE
KOPYALANMAZ — iki kaynaktan OKUNUR (tek-kaynak yasası; kopya sessizce ayrışır):

  Kaynak-1 (beyan)       `meridian/adapters/data.py` içindeki `RETIRED_SYMBOLS` — ast ile,
                         METİN olarak okunur. `meridian` İTHAL EDİLMEZ: ithal edilse betik
                         pytest dışında koşarken `meridian.obs` canlı yerel deftere yazardı
                         (CLAUDE.md §2, üç vaka 2026-08-30).
  Kaynak-2/3 (vekil+otorite)
                         `wp-qc-5-retired-caprazdogrulama-2026-08-09.md` mutabakat tablosu —
                         yerel üyelik son görülme + Massive `delisted_utc`.

İki kaynak delist tarihinde ÇELİŞİRSE betik bunu bulgu olarak basar (sessizce birini seçmez).

KOMUT SATIRI (sözleşme burasıdır, `main()` değil — CLAUDE.md §1):
    python research/qc_dogrulama/qc_sonda_delist_8_kiyas.py --yerel-tablo
    python research/qc_dogrulama/qc_sonda_delist_8_kiyas.py \\
        --qc research/olcumler/qc_dogrulama/sonda_delist_8.json
    python .../qc_sonda_delist_8_kiyas.py --qc <json> --json   # makine okuması
Çıkış kodu: 0 = kıyas koştu (AYRIK satır olsa da — hüküm Rol-1'de) · 1 = okuma/kaynak hatası.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from datetime import date
from pathlib import Path

KOK = Path(__file__).resolve().parents[2]
DATA_PY = KOK / "meridian" / "adapters" / "data.py"
WP5_MD = KOK / "research" / "qc_dogrulama" / "wp-qc-5-retired-caprazdogrulama-2026-08-09.md"
# wp-qc-5 ölçümünün KAPSAM TARİHİ dosya adından türer (tek kaynak): o tarihten SONRA emekli edilen
# semboller (TSK-143, 2026-09-05: EA/AVB/EQR — kanıtları `data.py::RETIRED_SYMBOLS` şerhinde, Massive
# doğrulaması aynı gün) bu çapraz-doğrulamanın KAPSAMINDA DEĞİLDİR; kart EDG-2026-021 o günün 8'ini
# ölçtü. Kapsam dışı olanlar sessizce düşmez: `yerel_tablo()` onları `KAPSAM_DISI`na yazar.
WP5_OLCUM_TARIHI = re.search(r"(\d{4}-\d{2}-\d{2})", WP5_MD.name).group(1)
KAPSAM_DISI: dict[str, str] = {}

_TARIH = re.compile(r"\b(\d{4}-\d{2}-\d{2})\b")


# ------------------------------------------------------------------- yerel tablo (iki kaynak)

def retired_symbols() -> dict[str, str]:
    """`RETIRED_SYMBOLS` — ast ile OKUNUR, ithal EDİLMEZ (obs'a yazma riski)."""
    agac = ast.parse(DATA_PY.read_text(encoding="utf-8"))
    for d in ast.walk(agac):
        hedef = d.targets[0] if isinstance(d, ast.Assign) else getattr(d, "target", None)
        if isinstance(d, (ast.Assign, ast.AnnAssign)) and getattr(hedef, "id", "") == \
                "RETIRED_SYMBOLS":
            return {k.value: ast.literal_eval(v) for k, v in zip(d.value.keys, d.value.values)}
    raise SystemExit(f"{DATA_PY} içinde RETIRED_SYMBOLS bulunamadı")


def wp5_mutabakat() -> dict[str, dict]:
    """wp-qc-5 mutabakat tablosu: ticker → {beyan, uyelik_son_gorulme, massive}."""
    out: dict[str, dict] = {}
    for hat in WP5_MD.read_text(encoding="utf-8").splitlines():
        if not hat.startswith("|"):
            continue
        h = [c.strip() for c in hat.strip().strip("|").split("|")]
        if len(h) < 4 or not re.fullmatch(r"[A-Z][A-Z.]{0,5}", h[0]):
            continue
        d1, d2, d3 = (_TARIH.search(h[1]), _TARIH.search(h[2]), _TARIH.search(h[3]))
        if not (d1 and d2):
            continue
        out[h[0]] = {"beyan": d1.group(1), "uyelik_son_gorulme": d2.group(1),
                     "massive": d3.group(1) if d3 else None,
                     "massive_ham": h[3]}
    return out


def yerel_tablo() -> dict[str, dict]:
    """wp-qc-5 KAPSAMINDAKİ sembollerin yerel gerçeği — İKİ kaynaktan, çelişki BEYANLI.

    ARTIK (TSK-143, 2026-09-05): `RETIRED_SYMBOLS` ölçüm gününden (WP5_OLCUM_TARIHI) SONRA emekli
    edilen sembolleri de taşır; onlar bu tabloya GİRMEZ, `KAPSAM_DISI[tic] = neden` olarak beyan
    edilir (o günkü ölçüm onları ölçmedi — 'satır okunamadı' diye düşmek ölçümü yanlış anlatırdı)."""
    reg = retired_symbols()
    wp5 = wp5_mutabakat()
    tablo: dict[str, dict] = {}
    KAPSAM_DISI.clear()
    for tic, aciklama in reg.items():
        m = _TARIH.search(aciklama)
        if not m:
            raise SystemExit(f"RETIRED_SYMBOLS[{tic}] tarih taşımıyor: {aciklama!r}")
        if tic not in wp5:
            # wp-qc-5 tablosu o ölçümün DONMUŞ kadrosudur: tabloda olmayan sembol (ölçümden sonra
            # emekli edilen — EA 08-05 emekli oldu ama 08-09 ölçümü onu ölçmedi) kapsam dışıdır.
            KAPSAM_DISI[tic] = (f"emeklilik {m.group(1)}; wp-qc-5 ({WP5_OLCUM_TARIHI}) kadrosunda "
                                f"yok — o ölçümün kapsamında değil (kanıt: data.py RETIRED şerhi)")
            continue
        w = wp5.get(tic, {})
        celiski = (w.get("beyan") is not None and w["beyan"] != m.group(1))
        tablo[tic] = {
            "retired_delist": m.group(1),
            "retired_neden": aciklama,
            "uyelik_son_gorulme": w.get("uyelik_son_gorulme"),
            "massive_delisted_utc": w.get("massive"),
            "kaynak_celiskisi": (f"RETIRED={m.group(1)} · wp-qc-5={w.get('beyan')}"
                                 if celiski else None),
        }
        if tablo[tic]["uyelik_son_gorulme"] is None:
            raise SystemExit(f"wp-qc-5 tablosunda {tic} satırı okunamadı")
    return tablo


# ------------------------------------------------------------------------------- kıyas

def _gun(s):
    return date.fromisoformat(s) if s else None


def kiyasla(qc: dict) -> dict:
    """QC sondası JSON'u ile yerel tabloyu GÜN GÜNE kıyaslar. Hüküm YOK — sayı ve etiket."""
    tablo = yerel_tablo()
    qc_kayit = {k.get("ticker"): k for k in (qc or {}).get("semboller", []) if k.get("ticker")}
    satirlar = []
    for tic in sorted(tablo):
        y = tablo[tic]
        k = qc_kayit.get(tic)
        qc_t = (k or {}).get("qc_delist_tarihi")
        qc_u = (k or {}).get("qc_uyari_tarihi")
        if k is None:
            mut, fark = "QC_SONDASINDA_YOK", None
        elif not qc_t:
            # WARNING geldi ama DELISTED gelmedi → "ölçülemedi"nin ALT SINIFI, ayrı etiket:
            # aynı kutuya konsaydı operatör "hiç veri yok" ile "uyarı var" arasını göremezdi.
            mut, fark = ("QC_UYARI_TIPI" if qc_u else "QC_OLCULEMEDI"), None
        else:
            fark = (_gun(qc_t) - _gun(y["retired_delist"])).days
            mut = "AYNI" if fark == 0 else "AYRIK"
        satirlar.append({
            "ticker": tic,
            "retired_delist": y["retired_delist"],
            "uyelik_son_gorulme": y["uyelik_son_gorulme"],
            "massive_delisted_utc": y["massive_delisted_utc"],
            "qc_delist_tarihi": qc_t,
            "qc_uyari_tarihi": qc_u,
            "uyari_fark_gun": (None if not (qc_u and y["retired_delist"]) else
                               (_gun(qc_u) - _gun(y["retired_delist"])).days),
            "qc_son_bar_VEKIL": (k or {}).get("son_bar_tarihi_VEKIL"),
            "qc_neden": (k or {}).get("neden"),
            "fark_gun": fark,
            "mutabakat": mut,
            "kaynak_celiskisi": y["kaynak_celiskisi"],
        })
    ozet = {m: sum(1 for s in satirlar if s["mutabakat"] == m)
            for m in ("AYNI", "AYRIK", "QC_UYARI_TIPI", "QC_OLCULEMEDI", "QC_SONDASINDA_YOK")}
    return {
        "kaynaklar": {"beyan": "meridian/adapters/data.py::RETIRED_SYMBOLS (ast, ithalsiz)",
                      "vekil_ve_otorite": WP5_MD.relative_to(KOK).as_posix(),
                      "qc": "qc_sonda_delist_8.py çıktısı"},
        "beyan": "Hüküm YOKTUR. 'AYRIK' bir kill değil, bir ÇELİŞKİdir — wp-qc-5'in çakışma "
                 "istisnası (Security Master tarih/neden çelişkisi) buradan tetiklenir ve "
                 "kararı Rol-1+operatör verir. 'QC_OLCULEMEDI' ölçülemedidir, 'aynı değil' "
                 "DEĞİLDİR. 'QC_UYARI_TIPI' = yalnız DelistingType.WARNING geldi; WARNING "
                 "delist gününden bir gün ÖNCE gelir, kıyasa GİRMEZ (uyari_fark_gun yalnız "
                 "TANIDIR). qc_son_bar_VEKIL de kıyasa GİRMEZ (delist tarihi değildir).",
        "ozet": ozet, "satirlar": satirlar,
    }


# ------------------------------------------------------------------------- komut satırı

def _yaz_tablo(satirlar, sutunlar):
    gen = [max(len(str(s.get(c, ""))) for s in satirlar + [{c: c}]) for c in sutunlar]
    print("  ".join(c.ljust(g) for c, g in zip(sutunlar, gen)))
    for s in satirlar:
        print("  ".join(str(s.get(c) if s.get(c) is not None else "-").ljust(g)
                        for c, g in zip(sutunlar, gen)))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="⑤ QC delist sondası ↔ yerel kaynaklar kıyası")
    ap.add_argument("--yerel-tablo", action="store_true", help="yalnız yerel tabloyu bas")
    ap.add_argument("--qc", type=Path, help="qc_sonda_delist_8.py çıktısı (JSON dosyası)")
    ap.add_argument("--json", action="store_true", help="kıyası JSON olarak bas")
    a = ap.parse_args(argv)

    if a.yerel_tablo or not a.qc:
        tablo = yerel_tablo()
        satirlar = [dict(ticker=t, **v) for t, v in sorted(tablo.items())]
        if a.json:
            print(json.dumps(tablo, ensure_ascii=False, indent=2))
        else:
            _yaz_tablo(satirlar, ["ticker", "retired_delist", "uyelik_son_gorulme",
                                  "massive_delisted_utc", "kaynak_celiskisi"])
            eksik = [t for t, v in tablo.items() if v["massive_delisted_utc"] is None]
            print(f"\nMassive üçüncü otoritesi EKSİK: {eksik or 'yok'} "
                  "(ÖLÇÜLEMEDİ — 'çelişki' DEĞİL)")
        if not a.qc:
            if not a.yerel_tablo:
                print("\n(--qc verilmedi: yalnız yerel tablo basıldı)")
            return 0

    try:
        qc = json.loads(a.qc.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"QC JSON okunamadı ({a.qc}): {type(e).__name__}: {e}")
        return 1
    r = kiyasla(qc)
    if a.json:
        print(json.dumps(r, ensure_ascii=False, indent=2))
    else:
        _yaz_tablo(r["satirlar"], ["ticker", "retired_delist", "qc_delist_tarihi", "fark_gun",
                                   "mutabakat", "qc_uyari_tarihi", "qc_son_bar_VEKIL",
                                   "massive_delisted_utc"])
        for _s in r["satirlar"]:
            if _s["qc_neden"]:
                print(f'  {_s["ticker"]}: {_s["qc_neden"]}')
        print("\nözet:", json.dumps(r["ozet"], ensure_ascii=False))
        print(r["beyan"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
