"""EDG-2026-056 — SPLIT ORAN-İMZASI RETRO TARAMASI (K=1, hücre: oran_imza_retro).

SALT-OKUMA: state/bars/*.csv doğrudan okunur; meridian motoru IMPORT EDİLMEZ, state'e YAZILMAZ.
Kural donuk `donuk_tanim.json`dan OKUNUR (kodda ikinci bir eşik kopyası tutulmaz — eşik sonradan
değişmesin diye tek kaynak). Yer gerçeği donuk `bilinen_split_donuk.json`dan OKUNUR.
"""
from __future__ import annotations
import csv, hashlib, json, math, pathlib

BURA = pathlib.Path(__file__).resolve().parent
KOK = BURA.parents[2]
BARS = KOK / "state" / "bars"

TANIM = json.loads((BURA / "donuk_tanim.json").read_text())
_ORANLAR: list[tuple[str, float]] = [
    (ad, float(x))
    for yon in ("ileri", "ters")
    for ad, x in TANIM["bilinen_split_oranlari"][yon].items()
]
SAYAC = {"bar": 0, "fiyat_adayi": 0, "hacim_olculemedi": 0, "aday": 0, "fiyat_hesaplanamadi": 0}
# İKİNCİL merdiven ancak BİRİNCİL kapıdan ÖNCEKİ havuz üzerinde anlamlıdır (ilk sürüm merdiveni
# F=1.5 sonrası havuzda saydı ve 2.0 için tautolojik 55 üretti — düzeltildi, HÜKÜM DEĞİŞMEDİ).
FIYAT_ADAYLARI: list[dict] = []


def sha256(p: pathlib.Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _en_yakin_oran(r: float) -> tuple[str, float, float] | None:
    """(ad, rho, bagil_sapma) — en yakın donuk orana göre. Tolerans KONTROLÜ yapmaz."""
    en = min(_ORANLAR, key=lambda kv: abs(r / kv[1] - 1.0))
    return en[0], en[1], abs(r / en[1] - 1.0)


def adaylar(ticker: str, tarih: list[str], close: list[float], volume: list[float],
            tanim: dict) -> list[dict]:
    """Donuk kural: aday(t) := |r/rho - 1| <= tol  VE  (1/F) <= vr/r <= F."""
    tol = float(tanim["fiyat_tolerans_rel"])
    F = float(tanim["hacim_teyidi"]["F_birincil"])
    merdiven = [float(x) for x in tanim["hacim_teyidi"]["F_merdiveni_ikincil"]]
    out: list[dict] = []
    for i in range(1, len(close)):
        SAYAC["bar"] += 1
        c0, c1 = close[i - 1], close[i]
        if not (c0 > 0 and c1 > 0) or math.isnan(c0) or math.isnan(c1):
            SAYAC["fiyat_hesaplanamadi"] += 1
            continue
        r = c0 / c1
        ad, rho, sap = _en_yakin_oran(r)
        if sap > tol:
            continue
        SAYAC["fiyat_adayi"] += 1
        v0, v1 = volume[i - 1], volume[i]
        if not (v0 > 0 and v1 > 0) or math.isnan(v0) or math.isnan(v1):
            # UYDURMA YASAĞI: "teyit edilmedi" değil "ÖLÇÜLEMEDİ" — ayrı sayılır, aday sayılmaz.
            SAYAC["hacim_olculemedi"] += 1
            continue
        vr = v1 / v0
        kat = vr / r
        FIYAT_ADAYLARI.append({"ticker": ticker, "tarih": tarih[i], "kat": kat})
        if not ((1.0 / F) <= kat <= F):
            continue
        SAYAC["aday"] += 1
        out.append({
            "ticker": ticker, "tarih": tarih[i], "r": r, "eslesen_oran": ad, "rho": rho,
            "bagil_sapma": sap, "vr": vr, "vr_bolu_r": kat,
            "merdiven_teyit": {str(f): bool((1.0 / f) <= kat <= f) for f in merdiven},
            "yon": "ileri" if rho > 1 else "ters",
        })
    return out


def _csv_oku(p: pathlib.Path) -> tuple[list[str], list[float], list[float]]:
    t: list[str] = []
    c: list[float] = []
    v: list[float] = []
    with p.open() as f:
        for satir in csv.DictReader(f):
            t.append(str(satir["date"])[:10])
            try:
                c.append(float(satir["close"]))
            except (TypeError, ValueError):
                c.append(float("nan"))
            try:
                v.append(float(satir["volume"]))
            except (TypeError, ValueError):
                v.append(float("nan"))
    return t, c, v


def _kacirma_nedeni(yakalanmayan: list[dict]) -> dict:
    """Kaçırılan bilinen olay FİYAT kapısında mı HACİM kapısında mı düştü — sebep sayımı."""
    fiyat, hacim = [], []
    for e in yakalanmayan:
        r = float(e["r_kart_c_t1_bolu_c_t"])
        ad, rho, sap = _en_yakin_oran(r)
        (fiyat if sap > float(TANIM["fiyat_tolerans_rel"]) else hacim).append(
            {"ticker": e["ticker"], "tarih": e["tarih"], "r_kart": round(r, 5),
             "en_yakin_oran": ad, "bagil_sapma": round(sap, 4)})
    return {"fiyat_kapisinda_dustu": len(fiyat), "hacim_kapisinda_dustu": len(hacim),
            "fiyat_ADIYLA": fiyat, "hacim_ADIYLA": hacim}


def _merdiven(havuz: list[dict], birincil: dict) -> dict:
    out = {}
    for f in TANIM["hacim_teyidi"]["F_merdiveni_ikincil"]:
        f = float(f)
        gec = [a for a in havuz if (1.0 / f) <= a["kat"] <= f]
        anahtar = {(a["ticker"], a["tarih"]) for a in gec}
        es = sum(1 for k in anahtar if k in birincil)
        out[str(f)] = {
            "aday": len(gec), "eslesen": es, "eslesmeyen": len(gec) - es,
            "yanlis_pozitif": round((len(gec) - es) / len(gec), 4) if gec else None,
            "yakalama": round(es / len(birincil), 4) if birincil else None,
            "esikleri_gecer": bool(gec and (len(gec) - es) / len(gec) <= 0.20
                                   and es / len(birincil) >= 0.80),
        }
    return out


def main() -> None:
    liste_p = BURA / "bilinen_split_donuk.json"
    liste = json.loads(liste_p.read_text())
    birincil = {(e["ticker"], e["tarih"]): e for e in liste["birincil"]["olaylar"]}
    ikincil = {(e["ticker"], e["tarih"]): e for e in liste["ikincil_hukum_disi"]["olaylar"]}

    dosyalar = sorted(BARS.glob("*.csv"))
    tum: list[dict] = []
    for p in dosyalar:
        tic = p.stem.upper()
        t, c, v = _csv_oku(p)
        tum.extend(adaylar(tic, t, c, v, TANIM))

    bulunan = {(a["ticker"], a["tarih"]) for a in tum}
    eslesen = [a for a in tum if (a["ticker"], a["tarih"]) in birincil]
    eslesmeyen = [a for a in tum if (a["ticker"], a["tarih"]) not in birincil]
    yakalanmayan = [e for k, e in birincil.items() if k not in bulunan]
    ikincil_yakalanan = [k for k in ikincil if k in bulunan]

    n_aday = len(tum)
    yp = (len(eslesmeyen) / n_aday) if n_aday else None
    yakalama = len(eslesen) / len(birincil) if birincil else None
    gecti = (yp is not None and yp <= 0.20) and (yakalama is not None and yakalama >= 0.80)

    sonuc = {
        "kart": "EDG-2026-056", "hucre": "oran_imza_retro", "K": 1, "kosuldu": "2026-08-24",
        "donuk_tanim_sha256": sha256(BURA / "donuk_tanim.json"),
        "bilinen_split_listesi_sha256": sha256(liste_p),
        "bilinen_split_kaynak_sha256": liste["birincil"]["kaynak_sha256"],
        "kapsam": {"dosya": len(dosyalar), "bar_cifti": SAYAC["bar"],
                   "fiyat_hesaplanamadi": SAYAC["fiyat_hesaplanamadi"]},
        "sayimlar": {
            "aday": n_aday,
            "fiyat_adayi_hacim_oncesi": SAYAC["fiyat_adayi"],
            "hacim_olculemedi": SAYAC["hacim_olculemedi"],
            "bilinen_split_eslesen": len(eslesen),
            "eslesmeyen_aday": len(eslesmeyen),
            "yakalanmayan_bilinen_split": len(yakalanmayan),
            "birincil_bilinen_toplam": len(birincil),
        },
        "oranlar": {"yanlis_pozitif": yp, "yakalama": yakalama},
        "karar": {
            "esik": "YP <= 0.20 VE yakalama >= 0.80",
            "gecti": bool(gecti),
            "hukum": ("oran-imza dedektörü UYGULANABİLİR" if gecti
                      else "imza tek başına yetersiz — körlük BEYANLI kalır"),
        },
        "eslesmeyen_adaylar_ADIYLA": sorted(
            ({"ticker": a["ticker"], "tarih": a["tarih"], "r": round(a["r"], 5),
              "oran": a["eslesen_oran"], "vr_bolu_r": round(a["vr_bolu_r"], 3), "yon": a["yon"]}
             for a in eslesmeyen), key=lambda x: (x["ticker"], x["tarih"])),
        "eslesen_adaylar_ADIYLA": sorted(
            ({"ticker": a["ticker"], "tarih": a["tarih"], "r": round(a["r"], 5),
              "oran": a["eslesen_oran"], "vr_bolu_r": round(a["vr_bolu_r"], 3), "yon": a["yon"]}
             for a in eslesen), key=lambda x: (x["ticker"], x["tarih"])),
        "yakalanmayan_bilinen_ADIYLA": sorted(
            ({"ticker": e["ticker"], "tarih": e["tarih"],
              "r_kart": e["r_kart_c_t1_bolu_c_t"]} for e in yakalanmayan),
            key=lambda x: (x["ticker"], x["tarih"])),
        "ikincil_hukum_disi": {
            "toplam": len(ikincil), "yakalanan": len(ikincil_yakalanan),
            "yakalanan_ADIYLA": sorted(f"{a}/{b}" for a, b in ikincil_yakalanan),
        },
        "yon_kirilimi_aday": {
            "ileri": sum(1 for a in tum if a["yon"] == "ileri"),
            "ters": sum(1 for a in tum if a["yon"] == "ters"),
        },
        "yakalanmayan_neden_dagilimi": _kacirma_nedeni(yakalanmayan),
        "ikincil_merdiven_HUKUM_DISI": {
            "beyan": ("Hüküm YALNIZ F=1.5 (birincil) satırından okunur. Bu merdiven donuk tanımda "
                      "ölçümden ÖNCE ilan edildi ve yalnız DAYANIKLILIK gösterir — eşik seçmez."),
            "taban": "hacmi ÖLÇÜLEBİLEN fiyat adayları (F kapısından ÖNCE)",
            "taban_n": len(FIYAT_ADAYLARI),
            "basamaklar": _merdiven(FIYAT_ADAYLARI, birincil),
        },
    }
    (BURA / "sonuc.json").write_text(json.dumps(sonuc, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({k: sonuc[k] for k in
                      ("kapsam", "sayimlar", "oranlar", "karar", "yon_kirilimi_aday",
                       "ikincil_hukum_disi", "ikincil_merdiven_HUKUM_DISI")},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
