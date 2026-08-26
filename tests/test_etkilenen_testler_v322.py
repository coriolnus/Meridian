"""ETKİLENEN-TEST SEÇİCİSİ — TAM SUITE HER COMMIT'İN ARACI DEĞİL · v322

VAKA (2026-08-26, operatör): "size'ı 5'e çektin diye tekrardan full suite koştun, ekstra
30 dk kaybettirdi." Haklıydı. ÖLÇÜLDÜ:

    tam suite                 7183 test   28:13
    gerçekten etkilenen küme   149 test    0:18.7      ← 90 kat

Değişiklik dört dosyaydı: bir `.tsx` sınıf adı + yeniden derlenmiş paket + manifest + ÜRETİLEN
html. O yolları okuyan test dosyası SEKİZ taneydi. 28 dakikanın 27'si boşa gitti.

KÖK NEDEN BİR OKUMA HATASIYDI: CLAUDE.md madde 6 "tam suite yalnız Rol-1'de TEK-OTORİTER" der —
"HER COMMIT'te" DEMEZ. Kuralı sıkılaştırmak disiplin değil israftır.

BU BETİĞİN YASASI VE SINIRI (ikisi de betikte yazılı, burada ÇİVİLİ):
  · diff `meridian/**/*.py`ye DOKUNUYORSA → seçici YETMEZ, tam suite gerekir. Orada etki
    IMPORT GRAFİĞİNDEN gelir; bir testin o dosyanın ADINI içermesi gerekmez. Seçicinin
    "hangi test dosyası bu yolu anıyor" mantığı orada YAPISAL OLARAK KÖRDÜR.
  · dokunmuyorsa (varlık/UI/doküman) → değişen yolları anan test dosyaları yeterlidir,
    çünkü bu depoda o testler yolları AÇIKÇA okur (kaynak-tarayıcı çiviler).

AŞIRI-KAPSAMA GÜVENLİDİR, EKSİK-KAPSAMA DEĞİL: seçici şüphede kaldığında GENİŞ davranır
(taban ad + uzantısız ad + üst dizin). Fazladan koşan bir test saniye yakar; kaçan bir test
sessiz bir gerileme dağıtır.
"""
from __future__ import annotations

import pathlib
import re
import subprocess

KOK = pathlib.Path(__file__).resolve().parents[1]
BETIK = KOK / "ops/etkilenen_testler.sh"


def _kos(*yollar: str) -> tuple[int, str]:
    assert BETIK.exists(), f"betik YOK: {BETIK.relative_to(KOK)}"
    r = subprocess.run([str(BETIK), "--yollar", *yollar],
                       capture_output=True, text=True, cwd=KOK)
    return r.returncode, r.stdout + r.stderr


def test_PY_degisikligi_TAM_SUITE_diyor():
    """ASIL SINIR ÇİVİSİ: motor değiştiyse seçici kendi körlüğünü BEYAN etmeli."""
    rc, cikti = _kos("meridian/sprint.py")
    assert "TAM SUITE" in cikti.upper(), (
        f"`.py` değişikliğinde tam suite talep edilmiyor — seçici import grafiğini göremez "
        f"ve sessizce eksik küme önerir:\n{cikti}")
    assert rc != 0, "tam suite gerektiren durum çıkış koduyla da ayrışmalı (betik dilsiz kalamaz)"


def test_TEST_dosyasindaki_py_degisikligi_TAM_SUITE_TETIKLEMEZ():
    """Aşırıya kaçma çivisi: `tests/` altındaki bir `.py` motor değişikliği DEĞİLDİR.
    Aksi halde her çivi eklemesi 28 dakika isterdi ve kural kendi amacını yerdi."""
    rc, cikti = _kos("tests/test_favicon_v320.py")
    assert "TAM SUITE" not in cikti.upper(), (
        f"test dosyası değişikliği tam suite tetikledi — kural kendini yiyor:\n{cikti}")


def test_VARLIK_degisikligi_ETKILENEN_KUMEYI_veriyor():
    """Operatörün vakası: `2a604f5`in dört yolu → o yolları okuyan test dosyaları."""
    rc, cikti = _kos("meridian/web/pano-assets/manifest.json",
                     "meridian/web/pano.html",
                     "ui/src/pano/kabuk/app-sidebar.tsx")
    assert "TAM SUITE" not in cikti.upper(), f"varlık değişikliği tam suite istedi:\n{cikti}"
    for beklenen in ("test_favicon_v320.py", "test_marka_isareti_v321.py"):
        assert beklenen in cikti, f"{beklenen} etkilenen kümede YOK:\n{cikti}"
    assert "pytest" in cikti, "koşulacak komut basılmıyor — çıktı elle çevrilmek zorunda kalır"


def test_ESLESME_YOKSA_SESSIZ_KALMIYOR():
    """UYDURMA YASAĞI komşusu: hiçbir test eşleşmediyse betik BOŞ komut basıp 'temiz'
    izlenimi VERMEZ — eşleşme olmadığını söyler ve kararı okuyucuya bırakır."""
    # YOL ÇALIŞMA ANINDA KURULUR, LİTERAL YAZILMAZ. İlk sürüm literal yazdı ve seçici onu
    # BU DOSYADA buldu — yani çivi kendi metnini eşleştirip "eşleşme var" dedi. Kaynak tarayan
    # bir araca literal örnek vermek, aracı kendi test dosyasına yönlendirmektir.
    # DİZİN de eşleşmemeli: `dizin/` jetonu eklendikten sonra `docs/…` artık 51 dosya
    # yakalıyor (o jetonun bilinçli bedeli). Gerçek "eşleşme yok" hâlini ölçmek için hiçbir
    # testin anmadığı bir dizin gerekir.
    yok = "bir/" + "olma" + "yan/" + "diz" + "in/" + "dos" + "ya" + ".md"
    rc, cikti = _kos(yok)
    assert cikti.strip(), "eşleşme yokken betik tamamen sessiz — 'koşacak test yok' ile 'ölçemedim' aynı görünür"
    assert "EŞLEŞME YOK" in cikti.upper() or "ESLESME YOK" in cikti.upper(), (
        f"eşleşmeme hâli adıyla bildirilmiyor:\n{cikti}")


def test_betik_KENDI_SINIRINI_yaziyor():
    """YASA 6 komşusu: bir aracın sınırı, aracın İÇİNDE yazılı olmalı — kullanan kişi
    testi okumak zorunda kalmamalı."""
    s = BETIK.read_text(encoding="utf-8")
    assert "import" in s.lower() and "graf" in s.lower(), (
        "betik, `.py` değişikliğinde neden yetersiz kaldığını (import grafiği) açıklamıyor")


def test_SUITE_SURESI_OLCULUYOR():
    """İkinci kalem: 28 dakikanın nereye gittiği ÖLÇÜLMÜYORDU. `--durations` her koşumda en
    yavaş testleri basar ve maliyeti sıfırdır (pytest süreyi zaten tutuyor). Bu çivi ölçümün
    sessizce kapatılmasını engeller — kapatılırsa 'suite yavaş' tartışması yine sayısız kalır."""
    cfg = (KOK / "pyproject.toml").read_text(encoding="utf-8")
    m = re.search(r'^addopts\s*=\s*"([^"]*)"', cfg, re.M)
    assert m, "addopts okunamadı"
    ao = m.group(1)
    assert "--durations" in ao, f"suite süresi ölçülmüyor — addopts: {ao!r}"
    assert ao.count("-q") == 1, (
        f"ikinci `-q` özet satırını siler ('temiz' ile 'çıktı yok' aynı görünür): {ao!r}")


def test_KURESEL_dosyalar_TAM_SUITE_istiyor():
    """ÜÇÜNCÜ KAPI — dogfood sırasında bulundu. Bazı dosyalar `meridian/**/*.py` DEĞİLDİR ama
    erişimleri KÜRESELDİR:
      · `tests/conftest.py` — 7 autouse fikstür, yani HER testte koşar. `.py` kapısına
        takılmaz (meridian/ altında değil) ve adı çoğu testte GEÇMEZ → seçici onu tamamen
        ıskalar. Bir autouse fikstürü değiştirmek 7183 testin davranışını değiştirebilir.
      · `pyproject.toml` — `addopts` her koşumun bayraklarıdır.
    Bu çivi o körlüğü kapatır: küresel dosya değişti mi, seçici kendi yetersizliğini BEYAN eder."""
    for yol in ("tests/conftest.py", "pyproject.toml"):
        rc, cikti = _kos(yol)
        assert "TAM SUITE" in cikti.upper(), (
            f"{yol} küresel erişimli ama seçici dar bir küme önerdi:\n{cikti}")
        assert rc != 0, f"{yol} için çıkış kodu ayrışmıyor"


def test_DIZIN_SAYAN_testler_de_kumeye_giriyor():
    """DÖRDÜNCÜ KÖRLÜK — CANLI VAKAYLA BULUNDU (2026-08-26). Bu betiği `ops/` altına eklemek
    `test_uiux_s1b_v154`i kırdı: o test RUNBOOK'u üretip "N ops betiği" sayısını doğruluyor,
    yani `ops/` dizinini SAYIYOR. Yeni bir dosya sayıyı 18'den 19'a çıkardı ve üretilen belge
    bayatladı.

    Seçici bunu ISKALADI çünkü test yeni dosyanın ADINI hiç anmıyor — dizini anıyor (`ops/`).
    Sınıf genel: bir dizini SAYAN/tarayan test, o dizine eklenen HER dosyadan etkilenir ama
    hiçbirinin adını içermez. Jeton bu yüzden `dizin/` (eğik çizgili) — çıplak `ops` değil,
    çünkü o kelime olarak her yerde geçer."""
    rc, cikti = _kos("ops/etkilenen_testler.sh")
    assert "test_uiux_s1b_v154.py" in cikti, (
        f"`ops/` dizinini sayan test kümede YOK — bu tam olarak canlıda kaçan vakaydı:\n{cikti}")
