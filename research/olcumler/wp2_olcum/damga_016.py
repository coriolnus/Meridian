"""EDG-2026-016 turunun KOD DAMGASI — kod/girdi/çıktı sha256 + kart dokunulmazlık kanıtı.

Kart dokunulmazlığı GIT'SİZ kanıtlanır (ajanlar git komutu koşmaz): kart dosyasının mtime'ı
ölçüm başlangıcından ÖNCE ise dosya bu tur boyunca yazılmamıştır. sha256 ayrıca kayda geçer.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import platform

import ortak as O

SB = O.SANDBOX
REPO = O.REPO
KART = REPO / "research" / "cards" / "EDG-2026-016-turnover-ana-etkisi.yaml"


def sha(p: pathlib.Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


sonuc = json.load(open(SB / "sonuc_016.json"))
olcum_basi = sonuc["olcum_tarihi"]
kart_mtime = __import__("datetime").datetime.fromtimestamp(
    KART.stat().st_mtime, __import__("datetime").timezone.utc).isoformat()

def repo_head() -> str:
    """HEAD sha'sı DOSYADAN okunur — ajanlar git komutu KOŞMAZ (CLAUDE.md #8)."""
    h = (REPO / ".git" / "HEAD").read_text().strip()
    if h.startswith("ref:"):
        ref = REPO / ".git" / h.split(" ", 1)[1].strip()
        if ref.exists():
            return ref.read_text().strip()
        for line in (REPO / ".git" / "packed-refs").read_text().splitlines():
            if line.endswith(h.split(" ", 1)[1].strip()):
                return line.split(" ", 1)[0]
        return "çözülemedi"
    return h


out = {
    "kart": "EDG-2026-016",
    "repo": str(REPO),
    "repo_HEAD": repo_head(),
    "sandbox": str(SB),
    "olcum_tarihi": olcum_basi,
    "olcum_kodu_sha256": {f: sha(SB / f) for f in
                          ("ortak.py", "pk.py", "k016.py", "rapor_016.py", "damga_016.py")},
    "onceki_turdan_devralinan": {
        "not": "ortak.py ve pk.py bu turda DEĞİŞTİRİLMEDİ; sha'lar önceki tur damgasıyla "
               "karşılaştırılır — eşitse pk.json'daki PK4/PK5 bu tur için de geçerlidir.",
        "eslesme": {},
    },
    "girdi_sha256": {
        p: sha(REPO / p) for p in (
            "research/edgar_facts/shares_outstanding.csv.gz",
            "state/bars_integrity.json",
            "state/counterfactuals.jsonl",
            "state/cf_open.json",
        )},
    "kart_sha256": {KART.name: sha(KART)},
    "kart_mtime_utc": kart_mtime,
    "kart_dokunulmadi": bool(kart_mtime < olcum_basi),
    "kart_dokunulmadi_kaniti": "kart dosyasının mtime'ı ölçüm başlangıcından ÖNCE — dosya bu tur "
                               "boyunca YAZILMADI (ajan yalnız okudu).",
    "cikti_sha256": {f: sha(SB / f) for f in ("sonuc_016.json",) if (SB / f).exists()},
    "python": f"Python {platform.python_version()}",
    "not": "Önceki turun kol_/sonuc_ dosyaları EZİLMEDİ; bu turun çıktıları sonuc_016.json + "
           "RAPOR_016.md.",
}

eski = json.load(open(SB / "kod_damgasi.json"))
for f in ("ortak.py", "pk.py"):
    out["onceki_turdan_devralinan"]["eslesme"][f] = {
        "onceki": eski["olcum_kodu_sha256"][f], "simdi": out["olcum_kodu_sha256"][f],
        "ayni": bool(eski["olcum_kodu_sha256"][f] == out["olcum_kodu_sha256"][f])}
out["girdi_onceki_turla_ayni"] = {
    k: bool(eski["girdi_sha256"].get(k) == v) for k, v in out["girdi_sha256"].items()}

O.json_yaz(SB / "kod_damgasi_016.json", out)
print(json.dumps({k: out[k] for k in ("kart_dokunulmadi", "kart_mtime_utc", "olcum_tarihi",
                                      "girdi_onceki_turla_ayni")}, ensure_ascii=False, indent=2))
print("yazıldı: kod_damgasi_016.json")
