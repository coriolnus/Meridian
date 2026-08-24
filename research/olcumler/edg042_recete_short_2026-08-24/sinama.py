"""EDG-2026-042 · R2 SENTETİK İŞARET SINAMASI — short bacağı (long emsali AYNEN korunur).

NEDEN SENTETİK: kartın R2 bloğu bir SÖZLEŞMEdir, bir ölçüm iddiası değil. Gerçek defterde
BUGÜN short satır YOKTUR (2026-08-22 snapshot'ında 893/893 `side="long"`; motor `broker.py`
içinde `side="long"` SABİTİ yazar, alan "gelecekteki SHORT desteğine ayrılmıştır"). Sözleşmeyi
gerçek veriyle sınamak İMKÂNSIZ; sentetik satır sınamanın TEK dürüst yoludur ve buradaki
sayılar ÖLÇÜM DEĞİLDİR — hiçbiri karta friksiyon rakamı olarak geçmez.

EMSAL: 2026-08-22 long sınaması (KOMUT.txt [0b]) — düşük dolum → +100,0 · yüksek dolum → −100,0.
Bu dosya o emsali AYNEN tekrarlar ve short için simetriğini ekler.

BEKLENTİ (kartın R2 birleşik formülü: aleyhte_bps = yon_isareti × bps_delta(afp, exit)):
  long  + DÜŞÜK  dolum (afp 99 / exit 100) → +100,0  ALEYHTE
  long  + YÜKSEK dolum (afp 101 / exit 100) → −100,0 LEHTE
  short + YÜKSEK dolum (afp 101 / exit 100) → +100,0 ALEYHTE   ← R2'nin eklediği bacak
  short + DÜŞÜK  dolum (afp 99 / exit 100) → −100,0  LEHTE     ← R2'nin eklediği bacak
  side boş/bilinmeyen                        → bps HESAPLANMAZ, olculemedi (uydurma yasağı)

AYRICA: aynı sentetik girdi ESKİ (2026-08-22) reçeteyle de koşturulur. Amaç, düzeltmenin
MADDİ olduğunu göstermek: eski reçete short satırların işaretini TERS yazar, yani hükmü ters
yöne çevirirdi (2026-08-22'de long için yaşanan T00103 vakasının short karşılığı).

YAZMA SINIRI: canlıya bağlanılmaz, state/'e ve donmuş dizine tek bayt yazılmaz; her koşum
geçici dizinde yapılır. ÇIKTI: sinama.json (bu dizine).
"""
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

DIZIN = Path(__file__).resolve().parent
ESKI_BETIK = DIZIN.parent / "edg042_kosum_2026-08-22" / "olcum.py"   # SALT-OKUNUR
YENI_BETIK = DIZIN / "olcum.py"

EXIT = 100.0
AFP_DUSUK, AFP_YUKSEK = 99.0, 101.0    # ±100 bps tam: (99/100−1)·1e4 = −100 · (101/100−1)·1e4 = +100

#: (ticker, side, alpaca_fill_price, exit_reason, kova, beklenen_yeni_bps, aciklama)
VAKALAR = [
    ("SYNLA", "long", AFP_DUSUK, "target", "cikis_hedef", 100.0,
     "long + DÜŞÜK dolum: satışta kötü fiyat → ALEYHTE (+). 2026-08-22 emsali, DEĞİŞMEMELİ."),
    ("SYNLL", "long", AFP_YUKSEK, "target", "cikis_hedef", -100.0,
     "long + YÜKSEK dolum: satışta iyi fiyat → LEHTE (−). 2026-08-22 emsali, DEĞİŞMEMELİ."),
    ("SYNSA", "short", AFP_YUKSEK, "stop", "cikis_stop", 100.0,
     "short + YÜKSEK dolum: buy-to-cover'da kötü fiyat → ALEYHTE (+). R2'nin YENİ bacağı."),
    ("SYNSL", "short", AFP_DUSUK, "stop", "cikis_stop", -100.0,
     "short + DÜŞÜK dolum: buy-to-cover'da iyi fiyat → LEHTE (−). R2'nin YENİ bacağı."),
    ("SYNSU", "  SHORT ", AFP_YUKSEK, "stop", "cikis_stop", 100.0,
     "yön normalizasyonu: boşluk/BÜYÜK harf 'short' olarak okunur, sessizce düşmez."),
    ("SYNXX", None, AFP_DUSUK, "target", "cikis_hedef", None,
     "side BOŞ: yön bilinmeden işaret seçilemez → bps HESAPLANMAZ, olculemedi (uydurma yasağı)."),
]


def sentetik_ham() -> dict:
    return {
        "kart": "EDG-2026-042", "kosum": "SENTETIK_SINAMA (ölçüm değildir)",
        "cekim_zamani": "SENTETIK", "makine": "SENTETIK (canlıya bağlanılmadı)",
        "goal_slippage_bps": 5,
        "entry_execution": {"n": 0, "satirlar": []},
        "trades": {"n": len(VAKALAR), "satirlar": [
            {"id": f"SYN{i:03d}", "plan_id": f"PSYN{i:03d}", "ticker": tkr,
             "ts_close": "2026-08-24", "side": side, "exit": EXIT, "exit_reason": er,
             "kaynak": "live_paper", "broker_teyit": "teyitli", "broker_teyit_neden": "sentetik",
             "alpaca_fill_price": afp, "alpaca_fill_beyan": None}
            for i, (tkr, side, afp, er, _kova, _bek, _acik) in enumerate(VAKALAR)]},
    }


def kostur(betik: Path, ham: dict) -> dict:
    with tempfile.TemporaryDirectory(prefix="edg042_sinama_") as td:
        kok = Path(td)
        shutil.copy2(betik, kok / "olcum.py")
        (kok / "canli_ham.json").write_text(json.dumps(ham, ensure_ascii=False), encoding="utf-8")
        ck = subprocess.run([sys.executable, "-B", str(kok / "olcum.py")],
                            capture_output=True, text=True)
        if ck.returncode != 0:
            raise SystemExit(f"{betik} çöktü:\n{ck.stdout}\n{ck.stderr}")
        return json.loads((kok / "sonuc.json").read_text(encoding="utf-8"))


def bps_bul(sonuc: dict, kova: str, ticker: str):
    """(bps, olculemedi_nedeni) — satır hangi kovada nasıl işlenmiş?"""
    for r in sonuc.get(kova, {}).get("satir_dokumu", []):
        if r["ticker"] == ticker:
            return r["bps"], None
    for r in (sonuc.get(kova, {}).get("olculemedi") or {}).get("satirlar", []):
        if r.get("ticker") == ticker:
            return None, r.get("neden")
    return None, "SATIR HİÇBİR KOVADA BULUNAMADI"


def main() -> None:
    ham = sentetik_ham()
    yeni, eski = kostur(YENI_BETIK, ham), kostur(ESKI_BETIK, ham)

    satirlar, gecti = [], True
    for tkr, side, afp, _er, kova, beklenen, aciklama in VAKALAR:
        y_bps, y_neden = bps_bul(yeni, kova, tkr)
        e_bps, e_neden = bps_bul(eski, kova, tkr)
        ok = (y_bps == beklenen) if beklenen is not None else (y_bps is None and y_neden is not None)
        gecti = gecti and ok
        satirlar.append({
            "ticker": tkr, "side": side, "exit": EXIT, "alpaca_fill_price": afp, "kova": kova,
            "beklenen_bps": beklenen, "yeni_recete_bps": y_bps, "yeni_recete_neden": y_neden,
            "eski_recete_bps": e_bps, "eski_recete_neden": e_neden,
            "eski_recete_TERS_MI": (e_bps is not None and beklenen is not None
                                    and e_bps == -beklenen and beklenen != 0),
            "gecti": ok, "aciklama": aciklama})

    out = {
        "kart": "EDG-2026-042",
        "ne": "R2 sentetik işaret sınaması — short bacağı + long emsalinin korunması",
        "bu_sayilar_OLCUM_DEGILDIR": ("sentetik satırlar; gerçek defterde short satır YOK "
                                      "(893/893 side=long). Hiçbir rakam karta friksiyon "
                                      "tahmini olarak geçmez."),
        "kart_formulu": ("aleyhte_bps = yon_isareti × bps_delta(alpaca_fill_price, exit); "
                         "yon_isareti = −1 (long) · +1 (short); side ∉ {long,short} → olculemedi"),
        "recete_yeni": str(YENI_BETIK.relative_to(DIZIN.parents[2])),
        "recete_eski": str(ESKI_BETIK.relative_to(DIZIN.parents[2])),
        "vakalar": satirlar,
        "long_emsali_korundu": all(s["gecti"] for s in satirlar if s["side"] == "long"),
        "eski_recetenin_short_hatasi": [s["ticker"] for s in satirlar if s["eski_recete_TERS_MI"]],
        "hukum": "GEÇTİ" if gecti else "KALDI",
    }
    (DIZIN / "sinama.json").write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n",
                                       encoding="utf-8")
    print(json.dumps({"hukum": out["hukum"],
                      "vakalar": {s["ticker"]: s["yeni_recete_bps"] for s in satirlar},
                      "eski_recete_ters_yazdiklari": out["eski_recetenin_short_hatasi"]},
                     ensure_ascii=False))
    if not gecti:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
