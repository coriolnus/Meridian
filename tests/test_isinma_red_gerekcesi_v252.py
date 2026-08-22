"""Isınma sprinti `cleared=0` derken NEDENİNİ de söylemeli (2026-08-21).

ÖLÇÜLEN KUSUR (canlı, 2026-08-21): `meridian-learn` günlerdir saatte bir
`warmup_sprint evaluated=40 cleared=0 best=null` basıyor. Operatör "öğrenme çalışmıyor" diye
bildirdi; ölçüm döngünün SAĞLAM olduğunu, kapının 40 sondanın hepsini reddettiğini gösterdi
(`_gate_eval` tam kapı + `k_probes=40` kazanan-laneti cezası).

KUSUR SAYIDA DEĞİL GÖRÜNÜRLÜKTE: `_gate_eval` reddin insan-okunur gerekçesini ZATEN üretiyor
(`_gate_why` → metin) ama `coordinate_descent_search` onu `_why` değişkenine alıp ATIYOR; ize
girmiyor, log'a girmiyor. Sonuç: operatör "0 geçti" görüyor ve neden geçmediğini
BİLEMİYOR — kuraklık teşhis EDİLEMEZ. Bu YASA 6'nın (üretilen alanın tüketicisi olmalı) tam
tersi: gerekçe üretiliyor ve hiçbir yere ulaşmıyor.

Bu dosya iki şeyi çiviler: (1) iz satırı reddin gerekçesini TAŞIR, (2) ısınma log'u gerekçe
DAĞILIMINI taşır. İkisi de olmadan `cleared=0` teşhis edilemez bir sayıdır.
"""
import inspect

from meridian import reflect, hermes_runtime


def test_iz_satiri_RED_GEREKCESINI_tasir():
    """`coordinate_descent_search`in iz satırı, geçmeyen sonda için `why` taşımalı.

    `_gate_eval` gerekçeyi zaten üretiyor; ize koymamak onu ÜRETİP ÇÖPE ATMAKTIR."""
    src = inspect.getsource(reflect.coordinate_descent_search)
    assert 'trace.append(' in src, "iz kaydı bulunamadı — çivi güncellenmeli"
    # iz sözlüğünde `why` anahtarı OLMALI
    i = src.index("trace.append(")
    blok = src[i:i + 500]
    assert '"why"' in blok or "'why'" in blok, (
        "iz satırı red gerekçesini TAŞIMIYOR — `_gate_eval`in ürettiği `_why` atılıyor ve "
        "`cleared=0` teşhis edilemez bir sayı olarak kalıyor (YASA 6)")


def test_isinma_logu_GEREKCE_DAGILIMI_tasir():
    """`_warmup_sprint` log'u yalnız sayı değil, red gerekçelerinin DAĞILIMINI da basmalı."""
    src = inspect.getsource(hermes_runtime._warmup_sprint)
    # ÇAĞRIYI AST İLE OKU, DİZGİ ARAMA (2026-08-21 kasıtlı-kırmızı bulgusu): ilk hâl
    # `"neden_dagilim" in src` diyordu ve YARDIMCININ ADI (`_red_neden_dagilimi`) o dizgiyi
    # içerdiği için, log alanını SİLSEM BİLE çivi yeşil kalıyordu — totoloji.
    import ast
    agac = ast.parse(inspect.getsource(hermes_runtime).replace("\n    ", "\n"), mode="exec") \
        if False else ast.parse(src.lstrip())
    cagri = [d for d in ast.walk(agac)
             if isinstance(d, ast.Call) and getattr(d.func, "attr", None) == "log"
             and d.args and getattr(d.args[0], "value", None) == "warmup_sprint"]
    assert cagri, "obs.log(\"warmup_sprint\", …) çağrısı bulunamadı — çivi güncellenmeli"
    anahtarlar = {k.arg for c in cagri for k in c.keywords}
    assert "neden_dagilim" in anahtarlar, (
        f"ısınma log ÇAĞRISI gerekçe dağılımı taşımıyor (alanlar: {sorted(anahtarlar)}) — "
        f"operatör `cleared=0` görüp NEDEN'i bilemez")


def test_gerekce_dagilimi_TUKETILEBILIR_bicimde(monkeypatch):
    """Dağılım bir SÖZLÜK olmalı (gerekçe → sayı), serbest metin değil — okunabilir olması yetmez,
    SAYILABİLİR olmalı ki bir kova baskınsa görünsün."""
    fn = getattr(hermes_runtime, "_red_neden_dagilimi", None)
    assert callable(fn), "_red_neden_dagilimi yardımcısı yok"
    iz = [{"passes": False, "why": "skor marjı: -0.004 < 0.010"},
          {"passes": False, "why": "skor marjı: -0.011 < 0.010"},
          {"passes": False, "why": "fold çoğunluğu: 2/5"},
          {"passes": True, "why": None}]
    d = fn(iz)
    assert isinstance(d, dict) and d, f"dağılım sözlük olmalı: {d!r}"
    assert sum(d.values()) == 3, f"yalnız GEÇMEYENLER sayılmalı (3 bekleniyor): {d}"
    # aynı KOVA'ya düşen iki farklı sayısal gerekçe TEK kovada toplanmalı — yoksa dağılım
    # her sonda için ayrı satır olur ve "hangi dal baskın" sorusu cevapsız kalır
    assert len(d) == 2, f"sayısal ayrıntı kovayı bölmemeli, 2 kova bekleniyor: {d}"
