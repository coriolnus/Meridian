"""BETİK/ŞASİ YÜKLEYİCİ — KAYNAKTAN DERLER, `__pycache__`E BAKMAZ (2026-08-30).

ÖLÇÜLEN KUSUR. `ops/` ve `research/olcumler/` betikleri paket değildir, o yüzden dosya yolundan
yükleniyorlardı:

    sp = importlib.util.spec_from_file_location("edg032b_ref", REFERANS)
    m  = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)                       # <-- KUSUR BURADA

`sp.loader` bir `SourceFileLoader`dır ve `SourceLoader.get_code()` kaynağı derlemeden ÖNCE
`__pycache__/<ad>.cpython-3XX.pyc`e bakar. Zaman damgalı pyc'nin geçerlilik kontrolü YALNIZ İKİ
ALANDIR: kaynağın TAM SANİYEye kırpılmış mtime'ı ve kaynağın BAYT BOYUTU. Boyutu değiştirmeyen
bir düzenleme (`5`→`2`, `==`→`!=`, `<`→`>`) pyc'nin kaydettiği saniyenin içinde kalırsa BAYAT
bytecode "geçerli" sayılır ve KAYNAK YERİNE O KOŞAR.

NEDEN BU ÜRETİM TARAFINDA DAHA CİDDİ. Test tarafında kusur "yeşil test yalan söyler"di ve en
azından bir çivi vardı. Burada karşılığı ŞUDUR: on üç ölçüm betiği (`ops/replay_sweep.py` +
on iki `research/olcumler/*/olcum.py`) AYNI donmuş referans şasisini yükler. O tek dosya için bir
kez bayat pyc doğarsa on üç ölçüm birden yanlış referansla koşar, `sonuc.json` doğru görünür ve
bunu yakalayacak hiçbir çivi yoktur.

ÖLÇÜM (2026-08-30). `get_code()` probe'u ile — üretim kodu ÇALIŞTIRILMADAN — on dokuz üretim
çağrı yerinin on yedisinde kusur GERÇEK ölçüldü; negatif kontrol her hedefte koşuldu (pyc
silinince probe mutasyonlu kodu döndürdü, yani kör değil). Önkoşulun bu depoda gerçekleştiği de
ölçüldü: 1116 `.py` değişikliğinin 18'i (%1,6) BOYUT-KORUYANDIR ve toplu metin dönüşümlerinde
patlarlar (`a81a3dd7` tek commit'te dokuz dosya).

ŞASİNİN KENDİSİNE DOKUNULMADI ve dokunulmamalı: `edg032b_tamsatir_2026-08-13/olcum.py`nin
sha256'sı bir PROVENANS ÇAPASIDIR — `edg057_leading_sector_2026-08-24/RAPOR.md` "Kasa" satırında
anılır, `edg032c_kunye_tazeleme_2026-08-24/RAPOR.md` onu künyedeki `sasi.sha256` alanına karşı
doğrular. Düzeltme bu yüzden YÜKLEYİCİ tarafındadır. Kapı:
`tests/test_bayat_bytecode_v334.py` §C.

TEK UYGULAMA: `tests/conftest.py::betikten_modul_yukle` de buraya devreder. İki kopya iki
sürüklenme yüzeyi olurdu — bu deponun tekrar eden "iki kopya sessizce ayrışır" sınıfı.
"""

import importlib.util
import pathlib
import sys


def _derle(yol, ad):
    """(kod nesnesi, boş modül) — kaynaktan derlenmiş, `__pycache__`e HİÇ dokunulmamış.

    `compile()` ne pyc OKUR ne de YAZAR. Yazmamak da şart: yazsaydı bu yardımcı, aynı dosyayı
    ham kalıpla okuyan bir başkası için tuzağı kendisi kurardı.

    Spec yine kurulur — `__file__`/`__name__`/`__spec__` doğru olmalı (şasi ve ölçüm betikleri
    yollarını `Path(__file__)`den türetir). Spec KURMAK önbelleğe dokunmaz; dokunan
    `loader.exec_module`dur ve o hiç çağrılmaz.

    `dont_inherit=True` ZORUNLU: CPython'ın kendi yükleyicisi de böyle derler
    (`_bootstrap_external.SourceLoader.source_to_code`). Varsayılan `False` olsaydı derlenen
    betik BU dosyanın `__future__` ifadelerini miras alırdı — sessiz sürüklenmenin ta kendisi.
    """
    yol = pathlib.Path(yol)
    assert yol.exists(), f"betik YOK: {yol}"
    ad = ad or f"_betik_{yol.stem}"
    assert ad != "__main__", f"betik `__main__` adıyla yüklenemez ({yol}) — ana koruması ateşler"
    spec = importlib.util.spec_from_file_location(ad, yol)
    assert spec is not None, f"spec kurulamadı: {yol}"
    return compile(yol.read_text(encoding="utf-8"), str(yol), "exec",
                   dont_inherit=True), importlib.util.module_from_spec(spec)


def kaynaktan_yukle(yol, ad=None, *, sys_modules_kaydet=False):
    """Paket olmayan bir betiği KAYNAKTAN derleyip modül olarak döndürür.

    sys_modules_kaydet : VARSAYILAN KAPALI. Yalnız kendi adını çözmesi gereken betikler açar
                         (ertelenmiş tip çözümü, pickle). Açan çağrı yeri temizliğinden de
                         sorumludur.
    """
    kod, mod = _derle(yol, ad)
    if sys_modules_kaydet:
        sys.modules[mod.__name__] = mod
    try:
        exec(kod, mod.__dict__)
    except BaseException:
        if sys_modules_kaydet:
            sys.modules.pop(mod.__name__, None)   # yarım modül kayıtta BIRAKILMAZ
        raise
    return mod


def referans_sasi_yukle(yol, ad="edg032b_ref"):
    """edg032b referans şasisini yükler — on üç çağrı yerindeki DANSI birebir koruyarak.

    Dans süs değildir ve üç parçası da gereklidir:
      · `sys.argv` şasinin KENDİ yoluna çevrilir — şasinin `__main__` bloğu argv'ye bakıp iş
        yapar; çağıranın argümanlarıyla yüklenirse içe aktarma bir KOŞUM tetikleyebilir.
      · `SystemExit` YUTULUR — şasi `raise SystemExit(main())` desenindedir ve bu, modül olarak
        yüklenirken beklenen çıkıştır.
      · argv `finally` ile GERİ VERİLİR — verilmezse çağıranın kendi argümanları yok olur.

    Tek fark, kusurun kendisidir: kod artık `exec_module` yerine KAYNAKTAN derlenir.
    """
    yol = pathlib.Path(yol)
    kod, mod = _derle(yol, ad)
    eski_argv = sys.argv
    sys.argv = [str(yol)]
    try:
        exec(kod, mod.__dict__)
    except SystemExit:            # `raise SystemExit(main())` — içe aktarmada BEKLENİR
        pass
    finally:
        sys.argv = eski_argv
    return mod
