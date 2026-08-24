"""EDG-2026-042 · R2 REGRESYON KANITI — eski (2026-08-22) ↔ yeni (R2) reçete BAYT-ÖZDEŞ mi?

NEDEN: R2 yalnız KAPSAM genişletmesidir (short bacağın işaret sözleşmesi). Gerçek örneklemde
short satır YOKTUR (893/893 `side="long"`), dolayısıyla yeni reçetenin çıktısı eski reçetenin
çıktısıyla BAYT-BAYT AYNI olmak ZORUNDADIR. Değilse bu bir REGRESYONdur ve koşum durur.

NASIL: iki reçete de `sonuc.json`u KENDİ dizinine yazar; donmuş dizin (edg042_kosum_2026-08-22/)
EZİLMEMELİDİR. Bu yüzden her iki betik de geçici bir dizine, kendi `canli_ham.json` kopyasıyla
birlikte taşınıp ORADA koşturulur. Donmuş dizine ve state/'e TEK BAYT yazılmaz; canlıya
BAĞLANILMAZ (yeni çekim YOK — 2026-08-22 snapshot'ı aynen kullanılır).

ÇIKTI: ozdeslik.json (bu dizine).
"""
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

YENI_DIZIN = Path(__file__).resolve().parent
ESKI_DIZIN = YENI_DIZIN.parent / "edg042_kosum_2026-08-22"
HAM = ESKI_DIZIN / "canli_ham.json"          # SALT-OKUNUR kaynak — 2026-08-22 snapshot'ı


def _sha(yol: Path) -> str:
    return hashlib.sha256(yol.read_bytes()).hexdigest()


def kostur(betik: Path, etiket: str) -> tuple[bytes, str]:
    """Betiği geçici dizinde, ham snapshot kopyasıyla koşturur; sonuc.json BAYTLARINI döner."""
    with tempfile.TemporaryDirectory(prefix=f"edg042_{etiket}_") as td:
        kok = Path(td)
        shutil.copy2(betik, kok / "olcum.py")
        shutil.copy2(HAM, kok / "canli_ham.json")
        ck = subprocess.run([sys.executable, "-B", str(kok / "olcum.py")],
                            capture_output=True, text=True)
        if ck.returncode != 0:
            raise SystemExit(f"{etiket} reçetesi çöktü:\n{ck.stdout}\n{ck.stderr}")
        return (kok / "sonuc.json").read_bytes(), ck.stdout.strip()


def main() -> None:
    eski_betik, yeni_betik = ESKI_DIZIN / "olcum.py", YENI_DIZIN / "olcum.py"
    eski_bayt, eski_stdout = kostur(eski_betik, "eski")
    yeni_bayt, yeni_stdout = kostur(yeni_betik, "yeni")
    ozdes = eski_bayt == yeni_bayt

    out = {
        "kart": "EDG-2026-042",
        "ne": ("R2 regresyon kanıtı — eski (2026-08-22 donuk) reçete ile yeni (R2, yöne koşullu) "
               "reçete AYNI snapshot'ta bayt-özdeş sonuç üretiyor mu?"),
        "bu_bir_olcum_kosumu_DEGILDIR": ("hüküm taşımaz, karta sayı yazmaz; yalnız reçete "
                                         "değişikliğinin davranış-nötr olduğunu kanıtlar"),
        "snapshot": {"dosya": str(HAM.relative_to(YENI_DIZIN.parents[2])),
                     "sha256": _sha(HAM), "yeni_cekim_yapildi_mi": False},
        "recete_eski": {"yol": str(eski_betik.relative_to(YENI_DIZIN.parents[2])),
                        "sha256": _sha(eski_betik), "dokunuldu_mu": False},
        "recete_yeni": {"yol": str(yeni_betik.relative_to(YENI_DIZIN.parents[2])),
                        "sha256": _sha(yeni_betik)},
        "sonuc_sha256_eski": hashlib.sha256(eski_bayt).hexdigest(),
        "sonuc_sha256_yeni": hashlib.sha256(yeni_bayt).hexdigest(),
        "bayt_ozdes": ozdes,
        "bayt_uzunluk": {"eski": len(eski_bayt), "yeni": len(yeni_bayt)},
        "stdout_eski": eski_stdout,
        "stdout_yeni": yeni_stdout,
        "hukum": ("GEÇTİ — long örnekleminde davranış DEĞİŞMEDİ (short satır yok, yeni dal hiç "
                  "ateşlenmedi)" if ozdes else
                  "KALDI — ÇIKTI DEĞİŞTİ: bu bir REGRESYONdur, koşum DURDURULUR"),
    }
    (YENI_DIZIN / "ozdeslik.json").write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n",
                                              encoding="utf-8")
    print(json.dumps({"bayt_ozdes": ozdes, "hukum": out["hukum"]}, ensure_ascii=False))
    if not ozdes:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
