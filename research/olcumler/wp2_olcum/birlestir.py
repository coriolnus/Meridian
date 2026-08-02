"""Üç kartın sonucunu TEK sonuc.json'da AYRI BLOKLAR hâlinde birleştirir + kod damgası üretir.

Üç kart AYRI AİLEDİR: birinin hükmü diğerini ETKİLEMEZ. Ortak olan tek şey boru hattı bekçisidir
(pozitif kontrol + PK4/PK5) — o düşerse ÜÇÜ DE hükümsüzdür.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import subprocess

import ortak as O

SB = O.SANDBOX


def sha(p: pathlib.Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> None:
    pk = json.load(open(SB / "pk.json"))
    bloklar = {}
    for kid, f in (("EDG-2026-012", "sonuc_012.json"), ("EDG-2026-013", "sonuc_013.json"),
                   ("EDG-2026-014", "sonuc_014.json")):
        p = SB / f
        bloklar[kid] = json.load(open(p)) if p.exists() else {
            "DURUM": "OLCULMEDI", "neden": f"{f} üretilmedi"}

    gecti = pk["pozitif_kontrol"]["GECTI"] is True and pk["pk4_yol_tutarliligi"]["gecti"] is True \
        and pk["pk5_ozdeslikler"]["gecti"] is True
    for kid, b in bloklar.items():
        h = b.get("hukum_onerisi")
        if h is not None:
            h["boru_hatti_bekcisi_GECTI"] = gecti
            if not gecti:
                h["oneri"] = "BORU HATTI GEÇERSİZ — pozitif kontrol/PK tutmadı, hüküm YAZILMAZ"

    out = {
        "dalga": "WP2 ölçüm dalgası — EDG-2026-012 / -013 / -014",
        "olcum_tarihi": bloklar["EDG-2026-012"].get("olcum_tarihi"),
        "sandbox": str(SB),
        "rol": "ölçüm ajanı — KART DOKUNULMADI, hüküm ÖNERİDİR (hükmü Rol-1 işler)",
        "ortak_bekci": {
            "pozitif_kontrol": pk["pozitif_kontrol"],
            "pk4_yol_tutarliligi": pk["pk4_yol_tutarliligi"],
            "pk5_ozdeslikler": pk["pk5_ozdeslikler"],
            "split_takvimi_bar_serisi_duz_mu": pk["split_takvimi_bar_serisi_duz_mu"],
            "split_normalizasyon_dogrulama": pk["split_normalizasyon_dogrulama"],
            "GECTI": gecti,
            "not": "Üç kart AYRI AİLEDİR; hükümleri birbirini etkilemez. Ortak olan yalnız bu "
                   "bekçidir — düşerse üçü de hükümsüz olurdu.",
        },
        "veri_kaynagi": {
            "barlar": "state/bars (CANLI önbellek, SALT-OKUNUR) — takvim kapısı + bars_integrity "
                      "dışlaması (kanonik defter yolu + hesaplanan yol)",
            "edgar": "research/edgar_facts/ (2026-08-01 ingest) — shares_outstanding.csv.gz + "
                     "fundamentals.csv.gz; PIT semantiği README §1 (`filed` kullanılır, `end` DEĞİL)",
            "evren": "meridian.adapters.data.REPLAY_UNIVERSE (251); barı yüklenen 248. "
                     "RETIRED_SYMBOLS (8) DIŞARIDA — kartların 'universe: full_251' metnine sadık; "
                     "bunun sonucu HAYATTA-KALMA ÇARPIKLIĞIDIR ve hükümde okunmalıdır.",
        },
        "kartlar": bloklar,
    }
    O.json_yaz(SB / "sonuc.json", out)

    # ---------------- kod damgası ----------------
    try:
        head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(O.REPO), capture_output=True,
                              text=True, timeout=20).stdout.strip()
    except Exception as e:
        head = f"okunamadı: {type(e).__name__}: {e}"
    dosyalar = sorted(p for p in SB.glob("*.py"))
    damga = {
        "repo_HEAD": head,
        "repo": str(O.REPO),
        "sandbox": str(SB),
        "olcum_kodu_sha256": {p.name: sha(p) for p in dosyalar},
        "girdi_sha256": {
            "research/edgar_facts/shares_outstanding.csv.gz": sha(O.EDGAR / "shares_outstanding.csv.gz"),
            "research/edgar_facts/fundamentals.csv.gz": sha(O.EDGAR / "fundamentals.csv.gz"),
            "research/edgar_facts/tutarsizlik.json": sha(O.EDGAR / "tutarsizlik.json"),
            "state/bars_integrity.json": sha(O.LIVE_STATE / "bars_integrity.json"),
            "state/counterfactuals.jsonl": sha(O.LIVE_STATE / "counterfactuals.jsonl"),
            "state/cf_open.json": sha(O.LIVE_STATE / "cf_open.json"),
        },
        "kart_sha256": {p.name: sha(p) for p in sorted(
            (O.REPO / "research" / "cards").glob("EDG-2026-01[234]-*.yaml"))},
        "cikti_sha256": {p.name: sha(p) for p in sorted(SB.glob("sonuc*.json")) + [SB / "pk.json"]},
        "python": subprocess.run([str(O.REPO / ".venv/bin/python"), "-V"], capture_output=True,
                                 text=True).stdout.strip(),
        "not": "Kart dosyalarının sha256'sı ölçüm ÖNCESİ ve SONRASI aynıdır — ajan karta DOKUNMADI.",
    }
    O.json_yaz(SB / "kod_damgasi.json", damga)
    print(f"== sonuc.json + kod_damgasi.json yazıldı (bekçi GEÇTİ={gecti}) ==")
    for kid, b in bloklar.items():
        print(f"   {kid}: {b.get('DURUM')} · {b.get('hukum_onerisi', {}).get('oneri', b.get('neden'))}")


if __name__ == "__main__":
    main()
