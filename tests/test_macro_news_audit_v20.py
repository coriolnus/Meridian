"""test_macro_news_audit_v20.py — adapters.macro + adapters.news EMEKLİLİK ÇİVİSİ.

TARİHÇE. Bu dosya 2026-07-21'de (tur 5) iki adaptörün DENETİMİYDİ ve dört kusur çivilemişti:
  M1    donmuş son tarih ("2026-07-10") — `dataset.py`de bir kez ölümcül olmuş hatanın ikizi
  M2/N2 ikisinin de ÜRETİM tüketicisi yok (skill yüzeyi) — teşhis o gün YAZILI hâle getirildi
  N1    "boş haber listesi = haber yok" — kaynak ölü de olabilir; `status()` gerçeği söylemeliydi
  N3    20'den fazla sembol SESSİZCE kırpılıyordu

BUGÜN (2026-07-30, temizlik turu). M2/N2 teşhisi kapatıldı: iki modül de EMEKLİ edildi, çünkü
denetimin kendi bulgusu ("üretim tüketicisi yok") dokuz gün sonra hâlâ geçerliydi ve bir
mekanizmanın tek savunması "bir gün lazım olabilir" olamaz (hedef sözleşmesi md.1).

TESTLER NE YAPIYOR ARTIK. Silinen bir fonksiyonun davranışı sınanamaz; sınanabilecek olan
EMEKLİLİĞİN KENDİSİDİR. Bu dosya üç şeyi çiviler:
  1. Adlar GERÇEKTEN yok (yarım emeklilik = en kötü hâl: kod ölü, testler yeşil).
  2. Modüller hâlâ İÇE AKTARILABİLİR (mezar taşı dosyaları duruyor → geri-al notu adresinde).
  3. Geri-al notu ve ÖĞRENİLEN DERSLER mezar taşında yazılı. Bu çivi olmadan biri dosyayı
     tamamen silebilir ve o dört kusurun hafızası kaybolurdu — o zaman haber katmanı geri
     istendiğinde aynı sessiz-kırpma ve aynı "anahtar var = çalışıyor" tuzağı yeniden kurulurdu.
"""
from __future__ import annotations

import inspect

from meridian.adapters import macro, news


EMEKLI_ADLAR = {
    macro: ("snapshot", "status", "WINDOW_START"),
    news: ("stock_news", "status", "available", "MAX_SYMBOLS"),
}


# ---------- 1) GERÇEKTEN YOK ----------
def test_emekli_adlar_gercekten_yok():
    """Yarım emeklilik yasağı: ad kalırsa çağıran da kalabilir ve ölü kod canlı görünür."""
    for mod, adlar in EMEKLI_ADLAR.items():
        for ad in adlar:
            assert not hasattr(mod, ad), f"{mod.__name__}.{ad} hâlâ var — emeklilik yarım kalmış"


def test_uretim_kodunda_caginan_kalmadi():
    """Çağıran taraması KODLA doğrulanır, hatırlamayla değil: `meridian` paketinde bu iki modülü
    içe aktaran TEK satır olmamalı (mezar taşlarının kendisi hariç)."""
    import ast
    import pathlib
    kok = pathlib.Path(macro.__file__).resolve().parent.parent          # …/meridian
    suclu = []
    for p in sorted(kok.rglob("*.py")):
        if p.name in ("macro.py", "news.py"):
            continue
        for n in ast.walk(ast.parse(p.read_text())):
            adlar = ([a.name for a in n.names] if isinstance(n, (ast.Import, ast.ImportFrom))
                     else [])
            mod = getattr(n, "module", "") or ""
            for a in adlar:
                if a.split(".")[-1] in ("macro", "news") or mod.endswith((".macro", ".news")):
                    suclu.append(f"{p.name}:{mod}.{a}")
    assert not suclu, f"emekli adaptörün üretim çağıranı var: {suclu}"


# ---------- 2) MEZAR TAŞI DURUYOR ----------
def test_mezar_taslari_ice_aktarilabilir():
    """Dosyalar SİLİNMEDİ: geri-al notu bir adreste durmalı ve `import` patlamamalı."""
    assert macro.__doc__ and news.__doc__


# ---------- 3) GERİ-AL NOTU + DÖRT DERSİN HAFIZASI ----------
def test_geri_al_notu_yazili():
    for mod in (macro, news):
        d = inspect.getdoc(mod) or ""
        assert "ÇIKARILDI 2026-07-30" in d, f"{mod.__name__}: emeklilik damgası yok"
        assert "GERİ-AL" in d, f"{mod.__name__}: geri-al notu yok"
        assert "ÇAĞIRAN TARAMASI" in d, f"{mod.__name__}: emekliliğin KANITI yazılmamış"


def test_news_dersleri_kaybolmadi():
    """N1 ve N3 ölçülmüş kusurlardı; haber katmanı geri kurulursa aynı tuzaklara düşülmemeli."""
    d = inspect.getdoc(news) or ""
    assert "SESSİZ KIRPMA" in d, "N3 dersi (20 sembol sessiz kırpma) mezar taşından silinmiş"
    assert "HABER ALINAMADI" in d, "N1 dersi ('haber yok' ≠ 'alınamadı') mezar taşından silinmiş"
    assert "news_symbols_truncated" in d and "news_fetch_failed" in d, \
        "derslerin kaydedileceği olay adları yazılmamış — ders soyut kalır"


def test_macro_dersi_kaybolmadi():
    """M1 (donmuş son tarih) bu depoda BİR KEZ ölümcül olmuş bir hata sınıfıdır."""
    d = inspect.getdoc(macro) or ""
    assert "regime.classify" in d, "canlı rejim yolunun NEREDE olduğu yazılmamış"
    assert "fetch_end()" in d, "M1 dersi (pencere HER ÇAĞRIDA bugüne kadar) mezar taşından silinmiş"
