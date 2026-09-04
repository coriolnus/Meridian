"""BAYAT BYTECODE — ÖLÇÜM ARACININ KENDİ BÜTÜNLÜĞÜ (v334, 2026-08-30).

ÖLÇÜLEN KUSUR (Faz 3 Görev 1 ajanı buldu, bu tur ölçüp genelledi). `ops/` ve
`research/olcumler/` betikleri paket olmadıkları için testlerde dosya yolundan yükleniyordu:

    spec = importlib.util.spec_from_file_location(ad, yol)
    mod  = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)          # <-- KUSUR BURADA

`spec.loader` bir `SourceFileLoader`dır ve `SourceLoader.get_code()` kaynağı derlemeden ÖNCE
`__pycache__/<ad>.cpython-3XX.pyc` dosyasına bakar. Zaman-damgalı pyc'nin geçerlilik kontrolü
YALNIZ İKİ ALANDIR: kaynağın TAM SANİYEye kırpılmış mtime'ı ve kaynağın BAYT BOYUTU. Yani
boyutu değiştirmeyen bir düzenleme (`5` → `2`, `==` → `!=`, `<` → `>`) pyc'nin kaydettiği
saniyenin içinde kalırsa BAYAT bytecode "geçerli" sayılır ve KAYNAK YERİNE O KOŞAR.

Bulgunun doğuş biçimi tam da budur: bir mutasyon dosya BOYUTUNU değiştirmediği için geri
yükleme sonrası `diff` "özdeş" dedi, ama çivi MUTASYONLU modülü ölçmeye devam etti. Test
yeşil derken kaynağı değil ÖNBELLEĞİ ölçüyordu — bu bir ÖLÇÜM ARACI arızasıdır, ürün arızası
değil, ve bu dosyadaki hiçbir çivi üretim davranışına dokunmaz.

TEK YARDIMCI, ON YEDİ ÇAĞRI YERİ DEĞİL: düzeltme `ops/sasi_yukleyici.py::kaynaktan_yukle`
içinde tek yerde yaşar (`tests/conftest.py`ye `betikten_modul_yukle` adıyla İÇE AKTARILIR). On yedi kopya on yedi sürüklenme yüzeyidir; §B çivisi kalıbın geri
sızmasını yasaklar.
"""
from __future__ import annotations

import ast
import importlib.util
import os
import pathlib
import sys

import pytest

from tests.conftest import betikten_modul_yukle

TESTLER = pathlib.Path(__file__).resolve().parent

#: Ham `exec_module` çağırmasına İZİNLİ tek dosya BU dosyadır — tuzağı KURMAK için kalıbın
#: kendisine ihtiyacı var (`_tuzagi_kur`). `conftest.py` listede DEĞİL: yardımcı ham çağrıyı
#: hiç kullanmaz, `compile()` + `exec()` ile kaynaktan derler.
HAM_YUKLEYICI_MUAFI = frozenset({"test_bayat_bytecode_v334.py"})


def _tuzagi_kur(tmp_path: pathlib.Path) -> tuple[pathlib.Path, int]:
    """Bayat-ama-"geçerli" bir pyc kurar ve HAM kalıbın ne gördüğünü döndürür.

    Kurulum, saniye-çözünürlüğünün doğal olarak ürettiği durumun DETERMİNİSTİK hâlidir:
      1. `DEGER = 5` yazılır ve HAM kalıpla yüklenir  → pyc başlığı (mtime0, boyut0) olur.
      2. Kaynak `DEGER = 2` yapılır — BOYUT AYNI (tek karakter, tek karakterle değişti).
      3. mtime0 geri verilir → pyc'nin iki alanlı kontrolü hâlâ "geçerli" der.
    Adım 3 hile değildir: aynı saniye içinde yapılan boyut-koruyan bir düzenleme bunu
    kendiliğinden üretir; elle geri vermek yalnız 1 saniyelik çakışma penceresini
    yarış-koşulu olmaktan çıkarır.
    """
    betik = tmp_path / "bayat_birim.py"
    betik.write_text("DEGER = 5\n", encoding="utf-8")

    st0 = betik.stat()
    spec = importlib.util.spec_from_file_location("bayat_birim_v334", betik)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)                      # pyc BURADA yazılır
    assert mod.DEGER == 5, "kurulum bozuk: taban değer okunamadı"

    betik.write_text("DEGER = 2\n", encoding="utf-8")
    assert betik.stat().st_size == st0.st_size, "mutasyon BOYUTU değiştirdi — tuzak kurulamaz"
    os.utime(betik, (st0.st_atime, st0.st_mtime))

    ham = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ham)
    return betik, ham.DEGER


# =================================================================================================
# §A — MEKANİZMA
# =================================================================================================
def test_a1_TUZAK_KURULABILIYOR_pozitif_kontrol(tmp_path):
    """POZİTİF KONTROL: bu yorumlayıcıda bayat bytecode GERÇEKTEN koşabiliyor mu?

    Bu çivi KIRMIZIYA DÖNERSE §A2'nin yeşili BOŞ demektir — yardımcı bir şeyi değil, HİÇBİR
    ŞEYİ savuşturuyor olur. Ölü bir pozitif kontrol sessiz kalmamalıdır (bu deponun p95
    dersi: "aletin ÇÖZÜNÜRLÜĞÜNÜ raporla"). Kırmızıysa CPython zaman-damgalı pyc yerine
    hash-tabanlı pyc'ye geçmiş olabilir — o zaman §A2/§B'nin hâlâ gerekli olup olmadığı
    yeniden tartılır, sessizce yeşile bırakılmaz."""
    _betik, ham_deger = _tuzagi_kur(tmp_path)
    assert ham_deger == 5, (
        f"TUZAK KURULAMADI: ham `exec_module` kaynağın yeni değerini ({ham_deger}) gördü, "
        f"yani bu yorumlayıcıda bayat pyc artık koşmuyor. §A2 bundan sonra hiçbir şey "
        f"ölçmez — koruma hâlâ gerekli mi, yeniden tartılmalı.")


def test_a2_PAYLASILAN_YARDIMCI_kaynaktan_derliyor(tmp_path):
    """ÇEKİRDEK ÇİVİ: aynı tuzak kurulu iken yardımcı KAYNAĞI görmeli.

    "Bayat bytecode koşarsa bu test kırmızı olur" — kırmızılığın anlamı budur."""
    betik, ham_deger = _tuzagi_kur(tmp_path)
    if ham_deger != 5:
        pytest.skip("ÖLÇÜLEMEDİ: tuzak kurulamadı (bkz. §A1) — yeşil sahte olurdu")

    mod = betikten_modul_yukle(betik, "bayat_birim_v334_yardimci")
    assert mod.DEGER == 2, (
        f"YARDIMCI BAYAT BYTECODE KOŞTURDU: kaynak `DEGER = 2` derken modül {mod.DEGER} "
        f"raporladı — `__pycache__` kaynağın önüne geçti. Yardımcı `compile()` ile "
        f"KAYNAKTAN derlemeli.")


def test_a3_yardimci_PYCACHE_YAZMIYOR(tmp_path):
    """Yardımcı önbelleği okumadığı gibi YAZMAMALI da.

    Yazsaydı, aynı betiği HAM kalıpla okuyan bir başkası için tuzağı yardımcı kurardı —
    düzeltme, düzelttiği kusurun tohumunu ekerdi."""
    betik = tmp_path / "iz_birakmaz.py"
    betik.write_text("DEGER = 7\n", encoding="utf-8")
    mod = betikten_modul_yukle(betik, "iz_birakmaz_v334")
    assert mod.DEGER == 7
    pyc = pathlib.Path(importlib.util.cache_from_source(str(betik)))
    assert not pyc.exists(), f"yardımcı pyc yazdı: {pyc}"


def test_a4_yardimci_DUNDERLARI_koruyor(tmp_path):
    """`__file__` korunmalı: `ops/` betikleri yollarını ondan türetir (`Path(__file__).parent`).
    `sys.modules` kaydı VARSAYILAN OLARAK KAPALI — açık isteyen çağrı yeri açar (v121/v126)."""
    betik = tmp_path / "dunder_birim.py"
    betik.write_text("import pathlib\nBURASI = pathlib.Path(__file__).resolve().parent\n",
                     encoding="utf-8")
    mod = betikten_modul_yukle(betik, "dunder_birim_v334")
    assert mod.BURASI == tmp_path.resolve()
    assert mod.__file__ == str(betik)
    assert mod.__name__ == "dunder_birim_v334"
    assert "dunder_birim_v334" not in sys.modules, "varsayılan `sys.modules` kaydı sızdırdı"

    mod2 = betikten_modul_yukle(betik, "dunder_kayitli_v334", sys_modules_kaydet=True)
    try:
        assert sys.modules["dunder_kayitli_v334"] is mod2
    finally:
        sys.modules.pop("dunder_kayitli_v334", None)


def test_a5_yardimci_DONT_INHERIT_ile_derliyor():
    """Yardımcının `compile()` çağrısı `dont_inherit=True` taşımalı — CPython'ın kendi
    yükleyicisi gibi (`SourceLoader.source_to_code`: `dont_inherit=True, optimize=-1`).

    NEDEN DAVRANIŞ DEĞİL SÖZLEŞME ÇİVİSİ. Varsayılan (`False`) ile derlenen betik, ÇAĞIRANIN
    (`conftest.py`) yürürlükteki `__future__` ifadelerini miras alır. Bugün conftest'te öyle
    bir ifade YOK, yani davranışsal bir çivi bugün İKİ HÂLDE DE yeşil olurdu — hiçbir şey
    ölçmezdi. Kırılma, biri conftest'e `from __future__ import annotations` eklediği gün
    doğar ve on altı betiği birden sessizce vurur; üstelik hedeflerden biri (`ops/olcum.py`)
    ertelenmiş tiplerin kendisini ÖLÇÜP karşı karar vermiştir. Sürüklenmeyi doğduğu yerde
    yasaklamanın tek yolu bayrağı çivilemektir.

    ÇAPA GÖVDEYİ TAKİP EDER: uygulama 2026-08-30'da `conftest.py`den `ops/sasi_yukleyici.py`ye
    taşındı (üretim tarafı da aynı gövdeyi çağırsın diye). Çivi de onunla taşındı — bu deponun
    "çapa satır değil SEMBOL" kuralının aynısı, bir dosya ölçeğinde."""
    kaynak = (TESTLER.parent / "ops" / "sasi_yukleyici.py").read_text(encoding="utf-8")
    for dugum in ast.walk(ast.parse(kaynak)):
        if isinstance(dugum, ast.FunctionDef) and dugum.name == "_derle":
            cagrilar = [n for n in ast.walk(dugum)
                        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                        and n.func.id == "compile"]
            assert len(cagrilar) == 1, f"beklenmeyen `compile` çağrı sayısı: {len(cagrilar)}"
            bayrak = {k.arg: k.value for k in cagrilar[0].keywords}
            assert "dont_inherit" in bayrak, (
                "`compile(..., dont_inherit=True)` YOK — betikler conftest'in `__future__` "
                "ifadelerini miras alır (bkz. bu çivinin gerekçesi)")
            assert isinstance(bayrak["dont_inherit"], ast.Constant) and \
                bayrak["dont_inherit"].value is True, "`dont_inherit` True DEĞİL"
            return
    pytest.fail("`ops/sasi_yukleyici.py::_derle` bulunamadı — çivi hedefini kaybetti")


# =================================================================================================
# §B — SÜRÜKLENME KAPISI
# =================================================================================================
def _exec_module_cagrilari(kaynak: str) -> list[int]:
    """`<bir şey>.exec_module(...)` ÇAĞRILARININ satır numaraları.

    METİN TARAMASI DEĞİL AST — ve bu bir üslup tercihi değil, ölçülmüş bir gerekçe: bu çivinin
    ilk hâli düz `grep` yapıyordu ve `conftest.py`de kusuru ANLATAN iki düzyazı satırını
    (bir docstring, bir yorum bloğu) suçlu saydı. Yasağı anlatan cümle yasağın kendi kurbanı
    olur — bu deponun tekrar eden tuzağı (`codelaw`ın "çapa satır değil SEMBOL" notu, ve
    düzyazının hayalet çapa doğurduğu 2026-08-29 vakası). Çağrı ile çağrıdan SÖZ ETMEK ayrı
    şeylerdir; ayrımı yalnız ayrıştırıcı yapabilir."""
    bulgular = []
    for dugum in ast.walk(ast.parse(kaynak)):
        if (isinstance(dugum, ast.Call) and isinstance(dugum.func, ast.Attribute)
                and dugum.func.attr == "exec_module"):
            bulgular.append(dugum.lineno)
    return bulgular


def test_b_test_dosyalari_HAM_EXEC_MODULE_kullanmiyor():
    """Kalıp geri sızmasın. On yedi çağrı yeri tek yardımcıya toplandı; on sekizincisi
    eklenirse bu çivi onu ADIYLA düşürür.

    Yasak olan `exec_module` ÇAĞRISIDIR — `spec_from_file_location` DEĞİL: spec kurmak
    önbelleğe dokunmaz (yardımcı da dunder'ları doğru kurmak için onu kullanır), önbelleği
    okuyan `loader.exec_module`dur."""
    suclu = []
    for yol in sorted(TESTLER.rglob("*.py")):
        if yol.name in HAM_YUKLEYICI_MUAFI:
            continue
        for no in _exec_module_cagrilari(yol.read_text(encoding="utf-8")):
            suclu.append(f"{yol.relative_to(TESTLER.parent)}:{no}")
    assert not suclu, (
        f"ham `exec_module` çağrısı geri sızdı: {suclu} — `__pycache__` kaynağın önüne "
        f"geçebilir (bkz. bu dosyanın başlığı). `tests.conftest.betikten_modul_yukle` kullan.")


# =================================================================================================
# §C — ÜRETİM TARAFI: edg032b REFERANS ŞASİSİ (2026-08-30, ikinci kalem)
# =================================================================================================
# On üç çağrı yeri (`ops/replay_sweep.py` + on iki `research/olcumler/*/olcum.py`) AYNI dosyayı
# yükler: donmuş referans şasi `edg032b_tamsatir_2026-08-13/olcum.py`. O tek dosya için bir kez
# bayat pyc doğarsa ON ÜÇ ölçüm betiği birden yanlış referansla koşar — ve `sonuc.json` doğru
# görünür. Test tarafındaki kusur "yeşil test yalan söyler"di; buradaki karşılığı "ölçüm sayısı
# SESSİZCE yanlış olur"dur ve onu yakalayacak bir çivi YOKTU.
#
# ŞASİNİN KENDİSİ DÜZENLENEMEZ (ölçüldü): sha256'sı provenans çapasıdır —
# `edg057_leading_sector_2026-08-24/RAPOR.md` "Kasa" satırında anılır ve
# `edg032c_kunye_tazeleme_2026-08-24/RAPOR.md` onu künyedeki `sasi.sha256` alanına karşı
# DOĞRULAR. Bir bayt değişirse iki rapor birden yalan söyler. Bu yüzden düzeltme YÜKLEYİCİ
# tarafındadır ve §C4 şasiyi ADIYLA korur.
CHASSIS = ("research/olcumler/edg032b_tamsatir_2026-08-13/olcum.py")

#: Provenans çapası. Değeri raporlardan gelir, buradan UYDURULMAZ.
CHASSIS_SHA256 = "75cef79215a7404f386517678df3d264d65d671ad23734a0b6559427177c85da"


def test_c1_URETIM_yardimcisi_kaynaktan_derliyor(tmp_path):
    """`ops.sasi_yukleyici` de aynı tuzağa karşı bağışık olmalı (§A2'nin üretim tarafı eşi)."""
    from ops.sasi_yukleyici import kaynaktan_yukle
    betik, ham_deger = _tuzagi_kur(tmp_path)
    if ham_deger != 5:
        pytest.skip("ÖLÇÜLEMEDİ: tuzak kurulamadı (bkz. §A1)")
    mod = kaynaktan_yukle(betik, "uretim_birim_v334")
    assert mod.DEGER == 2, (
        f"ÜRETİM YARDIMCISI BAYAT BYTECODE KOŞTURDU: kaynak 2 derken modül {mod.DEGER} raporladı")


def test_c2_sasi_yukleyici_ARGV_ve_SYSTEMEXIT_sozlesmesini_koruyor(tmp_path):
    """`referans_sasi_yukle` on üç çağrı yerindeki DANSI birebir korumalı.

    O dans süs değil: şasinin `__main__` bloğu `sys.argv`e bakar, o yüzden yükleme sırasında
    argv şasinin kendi yoluna çevrilir ve `SystemExit` yutulur (`raise SystemExit(main())`
    deseni içe aktarmada beklenir). argv SONRA geri verilir — verilmezse çağıranın kendi
    argümanları yok olur."""
    from ops.sasi_yukleyici import referans_sasi_yukle
    sahte = tmp_path / "sahte_sasi.py"
    sahte.write_text(
        "import sys\n"
        "GORULEN_ARGV = list(sys.argv)\n"
        "raise SystemExit(0)\n"          # `raise SystemExit(main())` deseni
        "ULASILMAZ = 1\n", encoding="utf-8")

    onceki = list(sys.argv)
    mod = referans_sasi_yukle(sahte, "sahte_ref_v334")
    assert sys.argv == onceki, "argv GERİ VERİLMEDİ — çağıranın argümanları yok oldu"
    assert mod.GORULEN_ARGV == [str(sahte)], (
        f"şasi argv'yi kendi yolu olarak görmedi: {mod.GORULEN_ARGV}")
    assert not hasattr(mod, "ULASILMAZ"), "SystemExit'ten sonrası koştu — desen bozuldu"
    assert "sahte_ref_v334" not in sys.modules, "`sys.modules`e sızdı"


#: ÜRETİM TARAFINDA HÂLÂ ham `exec_module` çağıran, BİLEREK kapsam dışı bırakılmış çağrı yerleri.
#: Sayılar da tutulur: aynı dosyaya İKİNCİ bir çağrı eklenmesi de düşürür.
#:
#: BU LİSTE YALNIZ KÜÇÜLEBİLİR (cırcır). Bir kalem düzeltilince buradan DÜŞÜLÜR; düşülmezse çivi
#: "artık yok" diye ADIYLA öter. Yeni bir kalem EKLEMEK için gerekçesi buraya yazılır — sessizce
#: büyüyen bir muafiyet listesi, muafiyetin kendisinden daha tehlikelidir.
BEYANLI_KALAN: dict[str, int] = {
    # BOŞ — üretim tarafındaki on dokuz çağrı yerinin HEPSİ kaynaktan derlemeye çevrildi
    # (2026-08-30). Kapı bundan sonra saf cırcırdır: ham `exec_module` geri gelirse ADIYLA
    # öter. Yeni bir muafiyet EKLEMEK gerekirse gerekçesi buraya yazılır.
}


def test_c3_URETIM_ham_exec_module_CIRCIRI():
    """Üretim tarafında ham `exec_module` yalnız BEYANLI kalemlerde olabilir.

    Dar bir "şasi çağrı yerleri temiz mi" kapısı yetmez: yarın BAŞKA bir dosyaya eklenen kalıbı
    görmezdi. Bu kapı envanteri tutar ve İKİ YÖNDE de öter —
      · beyan edilmemiş YENİ bir çağrı yeri  → kalıp geri sızıyor,
      · düzeltilmiş ama listede KALMIŞ kalem → liste bayatlıyor (muafiyet listesi eskirse, bir
        gün gerçekten gereken bir kırmızıyı da yutar).
    Kalıcı kırmızı üretmemesi bilinçlidir: kalıcı kırmızı okunmaz hâle gelir ve okunmayan bir
    çivi yoktur."""
    kok = TESTLER.parent
    bulunan = {}
    for alt in ("ops", "research", "skills"):
        for yol in sorted((kok / alt).rglob("*.py")):
            if "__pycache__" in str(yol):
                continue
            n = len(_exec_module_cagrilari(yol.read_text(encoding="utf-8")))
            if n:
                bulunan[str(yol.relative_to(kok))] = n

    yeni = {k: v for k, v in bulunan.items() if k not in BEYANLI_KALAN}
    assert not yeni, (
        f"BEYAN EDİLMEMİŞ ham `exec_module` çağrısı: {yeni} — `__pycache__` kaynağın önüne "
        f"geçebilir. `ops.sasi_yukleyici` kullan, ya da gerekçesiyle `BEYANLI_KALAN`a ekle.")
    bayat = {k: v for k, v in BEYANLI_KALAN.items() if bulunan.get(k) != v}
    assert not bayat, (
        f"`BEYANLI_KALAN` bayatladı: {bayat} (gerçek: "
        f"{ {k: bulunan.get(k, 0) for k in bayat} }) — düzeltilen kalem listeden DÜŞÜLMELİ.")


def test_c4_SASI_DOKUNULMAZ_ve_pycsi_bayat_degil():
    """KORUMA KAPISI — iki yönlü.

    (1) Şasi dosyası BAYT OLARAK korunur. sha256'sı iki raporda provenans olarak anılır; bir
        bayt değişirse o raporlar yalan söyler. Bu çivinin kırmızısı "testi düzelt" demez,
        "şasiyi geri al, ya da raporları ve künyeyi birlikte yenile" der.
    (2) Şasinin `__pycache__` girdisi varsa KAYNAKLA AYNI olmalı. Bayat bir pyc diskte
        dururken hiçbir ölçüm koşmamalıdır — düzeltmeden sonra yükleyici onu okumaz, ama
        kalıbı geri getiren biri olursa bu kapı önce öter."""
    import hashlib
    import importlib.util as _iu
    import marshal
    import struct

    sasi = TESTLER.parent / CHASSIS
    assert sasi.exists(), f"referans şasi YOK: {CHASSIS}"
    ham = sasi.read_bytes()
    assert hashlib.sha256(ham).hexdigest() == CHASSIS_SHA256, (
        f"REFERANS ŞASİ DEĞİŞMİŞ. sha256'sı provenans çapasıdır: "
        f"`edg057_leading_sector_2026-08-24/RAPOR.md` 'Kasa' satırında ve "
        f"`edg032c_kunye_tazeleme_2026-08-24/RAPOR.md` künye doğrulamasında anılır. "
        f"Değişiklik kasıtlıysa o iki raporu ve künyedeki `sasi.sha256` alanını da yenile.")

    pyc = pathlib.Path(_iu.cache_from_source(str(sasi)))
    if not pyc.exists():
        return                                   # önbellek yok → bayatlık da yok
    with pyc.open("rb") as f:
        bas = f.read(16)
        if len(bas) < 16:
            pytest.fail(f"şasi pyc'si okunamadı: {pyc}")
        _magic, flags, alan1, alan2 = struct.unpack("<4sIII", bas)
        diskteki = marshal.load(f)
    if flags & 0b1:
        return                                   # hash-tabanlı pyc: zaman damgası tuzağı yok
    st = sasi.stat()
    if not ((alan1 == int(st.st_mtime) & 0xFFFFFFFF) and (alan2 == st.st_size & 0xFFFFFFFF)):
        return                                   # geçersiz → yükleyici zaten yeniden derler
    taze = compile(ham.decode("utf-8"), diskteki.co_filename, "exec", dont_inherit=True)
    assert marshal.dumps(taze) == marshal.dumps(diskteki), (
        f"ŞASİNİN pyc'Sİ BAYAT VE 'GEÇERLİ' GÖRÜNÜYOR: {pyc}. Bu dosyayı SİL — diskte durduğu "
        f"sürece ham kalıba dönen her yükleyici kaynağı değil onu ölçer.")


def test_c5_yeni_yukleyici_CPYTHONLA_BIREBIR_ayni_kodu_uretiyor():
    """DAVRANIŞ ÖZDEŞLİĞİ — düzeltmenin ölçümleri değiştirmediğinin kanıtı.

    Bu çivi olmadan iddia edilemezdi: ölçüm betikleri (depo yasası gereği) pytest dışında
    KOŞTURULAMAZ, yani "eskisi gibi davranıyor" ancak DOLAYLI kanıtlanabilir. Kanıt şudur:
    yükleyicinin ürettiği KOD NESNESİ, CPython'ın kendi yükleyicisinin aynı kaynaktan
    üreteceğiyle BAYT OLARAK aynı mı?

    `SourceFileLoader.source_to_code` CPython'ın derleme adımıdır ve `__pycache__`e HİÇ
    dokunmaz (okumaz da yazmaz da) — yani bu karşılaştırma şasiyi ÇALIŞTIRMADAN ve diske iz
    bırakmadan yapılır. Eşitlik, `exec_module`un bayat-olmayan hâlde ürettiği kodun aynısını
    ürettiğimiz demektir: düzeltme, ölçüm sonuçlarını değiştiremez."""
    import marshal
    from importlib.machinery import SourceFileLoader

    from ops.sasi_yukleyici import _derle

    sasi = TESTLER.parent / CHASSIS
    ham = sasi.read_bytes()
    bizim, _mod = _derle(sasi, "edg032b_ref")
    cpython = SourceFileLoader("edg032b_ref", str(sasi)).source_to_code(ham, str(sasi))
    assert marshal.dumps(bizim) == marshal.dumps(cpython), (
        "yükleyici CPython'ın ürettiğinden FARKLI kod üretiyor — düzeltme davranışı "
        "değiştirmiş olabilir; `compile()` bayrakları `source_to_code` ile hizalanmalı")


def test_b2_SURUKLENME_KAPISI_calisiyor_pozitif_kontrol():
    """POZİTİF KONTROL: §B'nin tarayıcısı gerçek bir çağrıyı GÖRÜYOR, düzyazıyı GÖRMÜYOR.

    §B yeşil olduğunda iki şey aynı görünür: "kalıp yok" ve "tarayıcı bozuk". Bu çivi ikisini
    ayırır — muafiyet listesindeki tek dosya (bu dosya) gerçek bir çağrı İÇERİR ve tarayıcı
    onu bulmalıdır; kusuru ANLATAN düzyazıyı ise bulmamalıdır."""
    kendi = (TESTLER / "test_bayat_bytecode_v334.py").read_text(encoding="utf-8")
    assert _exec_module_cagrilari(kendi), (
        "tarayıcı KENDİ dosyasındaki gerçek `exec_module` çağrılarını göremedi — §B'nin yeşili "
        "boş demektir")
    duzyazi = '"""`spec.loader.exec_module` KULLANMAZ."""\n# spec.loader.exec_module(mod)\n'
    assert _exec_module_cagrilari(duzyazi) == [], (
        "tarayıcı düzyazıyı çağrı sandı — yasağı anlatan cümle yasağın kurbanı olur")
