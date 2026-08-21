"""Ret KİMLİĞİ: `entry_rejects` sayar ama KİMİ reddettiğini söylemez (Ö-51b, 2026-08-21).

ÖLÇÜLEN KUSUR (EXE-2026-006 hükmü, 2026-08-17): kartın Ö1 ürünü — *"kaçtı denilenlerin yüzde
kaçı dinlenen limitle doluyor"* — HESAPLANAMADI ve sebebi BİRİM UYUŞMAZLIĞIYDI:

    payda: `entry_rejects["entry_missed_limit"]`  → bir RED OLAYI sayacı
                                                    (aynı plan günlerce reddedilebilir)
    pay  : iki kolun defter FARKI                 → DİSTİNKT İŞLEM sayısı

Ham bölme %132 ve %141 verdi. Bir oran %100'ü aşamaz; o sayılar sonuç değil, tanımın
belirtisiydi. İkinci kusur: yerinden-etme HİÇ KAÇMAMIŞ işlemleri de içeri alıyor, yani pay saf
değil (ölçüldü: cap=0,005'te 251 yeni işleme karşı 154 YERİNDEN OLAN).

Ö1 ancak reddedilen PLANLARIN kimliği kaydedilirse hesaplanır. Bu dosya o kaydı çiviler.

TASARIM SINIRI — BU ÇİVİNİN ÖLÇMEDİĞİ: kimlik kaydı Ö1'i HESAPLANABİLİR yapar, DOĞRU yapmaz.
Doğruluk hâlâ yan-kanal ayrıştırmasına bağlı ve o ayrı bir hesaptır (`yan_kanal_ayristirma.json`).
"""
import ast
import inspect
import pathlib

from meridian import backtest as BT


def test_ret_kimligi_TOPLANIYOR():
    """`replay` ret olaylarını yalnız SAYMAMALI — reddedilen planın kimliğini de toplamalı."""
    assert "entry_reject_ids" in BT.BacktestResult.__dataclass_fields__, (
        "BacktestResult ret kimliğini taşımıyor — Ö1'in paydası DİSTİNKT PLAN olarak sayılamaz "
        "ve oran %100'ü aşmaya devam eder (2026-08-17'de %132/%141 ölçüldü)")


def test_kimlik_TICKER_ve_TARIH_tasir():
    """Kimlik (ticker, tarih) çiftidir. Yalnız ticker YETMEZ: aynı sembol farklı günlerde
    reddedilir ve distinkt PLAN sayısı yine şişer."""
    # AST İLE, DİZGİ İLE DEĞİL (2026-08-21): ilk hâl `"ticker" in blok` diyordu ve DÜŞTÜ —
    # kod değişken adı olarak `t` kullanıyor, literal "ticker" hiç geçmiyor. Dizgi araması
    # kodun ADLANDIRMASINA bağımlıdır; AST YAPIYA bakar.
    src = inspect.getsource(BT.replay)
    agac = ast.parse(src.lstrip())
    ekler = [d for d in ast.walk(agac)
             if isinstance(d, ast.Call) and getattr(d.func, "attr", None) == "append"
             and "entry_reject_ids" in ast.dump(d.func)]
    assert ekler, "replay ret kimliğini DOLDURMUYOR (entry_reject_ids…append bulunamadı)"
    arg = ekler[0].args[0]
    assert isinstance(arg, ast.Tuple) and len(arg.elts) == 2, (
        f"kimlik 2'li demet olmalı (ticker, tarih): {ast.dump(arg)[:140]}")
    ikinci = ast.dump(arg.elts[1])
    assert "date" in ikinci, (
        f"kimliğin ikinci öğesi TARİH değil — aynı sembolün farklı günleri tek plan sayılır: {ikinci[:140]}")


def test_sayac_ile_kimlik_AYNI_OLAYDAN_beslenir():
    """Sayaç ve kimlik AYNI ret olayından yazılmalı. Ayrı yerlerden beslenirlerse ayrışırlar ve
    'aynı gerçek iki yerde' kusurunun (WP6-26) yeni bir vakası doğar."""
    src = inspect.getsource(BT.replay)
    agac = ast.parse(src.lstrip())
    # `_rej.get("reason")` koşulunun İÇİNDE hem sayaç hem kimlik yazımı olmalı
    bulundu = False
    for d in ast.walk(agac):
        if not isinstance(d, ast.If):
            continue
        govde = ast.dump(d)
        if "entry_rejects" in govde and "entry_reject_ids" in govde:
            bulundu = True
    assert bulundu, (
        "sayaç ve kimlik AYNI koşul bloğunda yazılmıyor — ayrışabilirler (aynı gerçek iki yerde)")
