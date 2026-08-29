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


# ================================================================================================
# BEŞİNCİ KÖRLÜK — KAPININ KENDİSİ ÇALIŞMIYORDU (2026-08-29, tam suite koşumunda bulundu)
# ------------------------------------------------------------------------------------------------
# VAKA: yukarıdaki iki çivi (`ESLESME_YOKSA…`, `KURESEL_dosyalar…`) kırmızıydı ve sebebi
# betikteki bir SÖZDİZİMİ kusuruydu: üç yerde `${#DIZI[@]-0}` yazılıydı. Bash'te `${#parametre}`
# biçimi varsayılan-değer soneki (`-0`) KABUL ETMEZ → `bad substitution`. Betik `set -e`
# KULLANMADIĞI için hata ÖLÜMCÜL DEĞİLDİR: satır stderr'e düşer, `[[ ]]` testi başarısız sayılır
# ve kapı SESSİZCE "false" olur. Yani üç `if` hiç değerlendirilmedi.
#
# ÜÇ FARKLI BEDEL ÖLÇÜLDÜ, biri diğerlerinden tehlikeli:
#   · satır 101 (KÜRESEL kapısı) → `tests/conftest.py` değişince "TAM SUITE GEREKLİ" DEMEZ,
#     dar bir küme önerir. Bu EKSİK-KAPSAMAdır — betiğin kendi başlığındaki "aşırı-kapsama
#     güvenli, eksik-kapsama değil" sözleşmesinin TAM TERSİ. Tehlikeli olan budur.
#   · satır 163 (eşleşme kapısı) → "EŞLEŞME YOK" yerine BOŞ liste basar (sessiz-yeşil).
#   · satır 66  (boş-diff kapısı) → "DEĞİŞİKLİK YOK" yerine düşer ve jeton listesi boş kaldığı
#     için `grep -rlE ""` HER dosyayı tutar: boş bir diff **394 test dosyası** "etkilenen"
#     sayılır. Bu kapının HİÇ çivisi yoktu; aşağıdaki ilk çivi onu kapatır.
#
# AŞAĞIDAKİ İKİNCİ ÇİVİ SINIFI KAPATIR, ÖRNEĞİ DEĞİL: üç satırı tek tek düzeltmek yalnız
# bugünkü üç örneği kapatır — yarın eklenen DÖRDÜNCÜ bir kapı aynı biçimi kullanırsa aynı
# sessiz körlük geri gelir (bu deponun tekrar eden dersi: "kapanan sınıf değil, o günkü
# örneklerdi"). O yüzden çivi tek tek satırlara değil, betiğin KABUK GENİŞLETME HATASI
# ÜRETMEMESİ olgusuna bakar.
# ================================================================================================

def _kos_ayrik(*yollar: str) -> tuple[int, str, str]:
    """`_kos` gibi ama stdout/stderr AYRI — kabuk genişletme hataları stderr'e düşer ve
    birleşik okumada betiğin kendi metnine karışırlar."""
    r = subprocess.run([str(BETIK), "--yollar", *yollar],
                       capture_output=True, text=True, cwd=KOK)
    return r.returncode, r.stdout, r.stderr


def test_BOS_diff_DEGISIKLIK_YOK_diyor_ve_her_dosyayi_secmiyor():
    """SATIR 66'NIN ÇİVİSİ — bu kapının hiç çivisi yoktu.

    Boş yol listesi "koşulacak bir şey yok" demektir. Kapı düşerse betik devam eder ve jeton
    listesi boş olduğu için `grep -rlE ""` TÜM test dosyalarını tutar — yani "hiçbir şey
    değişmedi" girdisi "her şey etkilendi" hükmüne dönüşür (ölçüldü: 394 dosya)."""
    rc, out, err = _kos_ayrik()
    birlesik = out + err
    assert "DEĞİŞİKLİK YOK" in birlesik.upper() or "DEGISIKLIK YOK" in birlesik.upper(), (
        f"boş diff adıyla bildirilmiyor:\n{birlesik}")
    assert rc == 0, "boş diff bir arıza değildir — çıkış kodu 0 olmalı"
    assert "etkilenen test dosyaları" not in out, (
        f"boş diff'te etkilenen küme hesaplanmış — kapı düşmüş:\n{out}")


def test_betik_KABUK_GENISLETME_HATASI_uretmiyor():
    """SINIF ÇİVİSİ (örnek çivisi değil): betik hiçbir yolda `bad substitution` /
    `unbound variable` üretmemeli.

    Neden ayrı bir çivi: yukarıdaki davranış çivileri yalnız ÜÇ bilinen kapıyı dolaylı olarak
    korur. Yarın eklenen dördüncü bir kapı aynı geçersiz biçimi kullanırsa davranış çivileri
    onu göremez (o kapının davranışını kimse sınamıyordur) ama BU çivi görür — çünkü olguya
    bakar: betik sessizce yutulan bir genişletme hatası ÜRETEMEZ.

    `set -e` yokluğu bu sınıfı görünmez yapar: hata ölümcül değildir, yalnız stderr'e düşer ve
    kapı sessizce 'false' olur. Sessizliği kıran tek şey stderr'i OKUYAN bir çividir."""
    senaryolar: list[tuple[str, tuple[str, ...]]] = [
        ("boş diff", ()),
        ("motor .py", ("meridian/sprint.py",)),
        ("küresel dosya", ("tests/conftest.py",)),
        ("varlık", ("meridian/web/pano.html",)),
        ("eşleşmeyen yol", ("bir/" + "olma" + "yan/" + "diz" + "in/" + "dos" + "ya" + ".md",)),
        ("çoklu yol", ("meridian/spend.py", "docs/RUNBOOK.md")),
    ]
    for ad, yollar in senaryolar:
        _rc, _out, err = _kos_ayrik(*yollar)
        dusuk = err.lower()
        for hata in ("bad substitution", "unbound variable", "syntax error"):
            assert hata not in dusuk, (
                f"[{ad}] betik kabuk hatası üretiyor ({hata!r}) — `set -e` olmadığı için bu "
                f"hata ölümcül değil, kapıyı SESSİZCE devre dışı bırakır:\n{err}")
