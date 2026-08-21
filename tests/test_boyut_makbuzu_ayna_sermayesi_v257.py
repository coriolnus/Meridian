"""Boyut makbuzu AYNANIN kullandığı sermayeyi de yazmalı — çiviler (ROADMAP Ö-53).

ÖLÇÜLEN KUSUR (2026-08-22): açık pozisyonların yedisinde de kitap ile broker adet tutmuyordu
(kitap 15.661,22 fazla maliyet taşıyor) ve sebebi KAYITTAN ÇIKMIYORDU. Kök neden `loop.py`de:

    eq_now = float(_hb["equity"])              # KİTABIN sermayesi (nabız)
    eq     = float(acct["equity"]) ...         # BROKER'ın sermayesi (Alpaca hesabı)
    meta["size_law"][plan] = {"eq_now": eq_now, ...}   # makbuz KİTABINKİNİ yazıyor
    alpaca.submit_plan(pl, eq, ...)                    # ayna BROKER'ınkiyle boyutlanıyor

İki tabanın farklı olması KUSUR DEĞİL (her defter kendi parasına göre boyutlanır). Kusur,
makbuzun aynanın FİİLEN kullandığı sayıyı hiç yazmamasıdır: bu yüzden makbuzu OLAN planlarda
bile (CRM · BDX · MRK · MRNA) sapma açıklanamıyor ve `MIRROR_DRIFT` "gönderim↔dolum kıyası
kurulamaz" diyor. Çivi o boşluğu kapatır.

AST İLE, METİNLE DEĞİL: bu gece üç metin-eşleşmeli çivi totoloji çıktı (biri yardımcı fonksiyonun
ADINI eşleştiriyordu). Yapıyı sormak, kelimeyi aramaktan farklıdır.
"""
import ast
import pathlib

LOOP = pathlib.Path(__file__).resolve().parents[1] / "meridian" / "loop.py"
AGAC = ast.parse(LOOP.read_text(encoding="utf-8"))


def _submit_plan_cagrisi() -> ast.Call:
    for d in ast.walk(AGAC):
        if (isinstance(d, ast.Call) and isinstance(d.func, ast.Attribute)
                and d.func.attr == "submit_plan"):
            return d
    raise AssertionError("alpaca.submit_plan çağrısı BULUNAMADI — çapa çürüdü, çivi kör kalırdı")


def _makbuz_sozlugu() -> ast.Dict:
    """`meta.setdefault("size_law", {})[...] = {...}` atamasının SAĞ tarafı."""
    for d in ast.walk(AGAC):
        if not isinstance(d, ast.Assign) or not isinstance(d.value, ast.Dict):
            continue
        for h in d.targets:
            if (isinstance(h, ast.Subscript) and isinstance(h.value, ast.Call)
                    and isinstance(h.value.func, ast.Attribute)
                    and h.value.func.attr == "setdefault"
                    and any(isinstance(a, ast.Constant) and a.value == "size_law"
                            for a in h.value.args)):
                return d.value
    raise AssertionError("size_law makbuz sözlüğü BULUNAMADI — çapa çürüdü")


def test_capalar_yasiyor():
    assert _submit_plan_cagrisi() is not None and _makbuz_sozlugu() is not None


def test_aynaya_giden_sermaye_makbuzda_KAYITLI():
    """`submit_plan`e ikinci konumsal argüman olarak giden DEĞİŞKEN, makbuzda da geçmeli.
    Geçmezse aynanın hangi sermayeyle boyutlandığı kayıttan ASLA çıkarılamaz."""
    cagri = _submit_plan_cagrisi()
    assert len(cagri.args) >= 2, "submit_plan'e equity konumsal geçmiyor — çivi varsayımı bozuldu"
    ayna_eq = cagri.args[1]
    assert isinstance(ayna_eq, ast.Name), f"beklenen bir DEĞİŞKEN, gelen {type(ayna_eq).__name__}"
    adlar = {n.id for n in ast.walk(_makbuz_sozlugu()) if isinstance(n, ast.Name)}
    assert ayna_eq.id in adlar, (
        f"aynaya `{ayna_eq.id}` sermayesiyle gönderiliyor ama makbuz onu YAZMIYOR "
        f"(makbuzdaki adlar: {sorted(adlar)}) — sapma kayıttan açıklanamaz kalır (Ö-53)")


def test_kitap_sermayesi_de_KALIYOR():
    """Ayna sermayesini eklemek kitabınkini KOVMAMALI: kıyas iki sayıyı da ister."""
    anahtarlar = {k.value for k in _makbuz_sozlugu().keys
                  if isinstance(k, ast.Constant)}
    assert "eq_now" in anahtarlar, "kitabın sermayesi makbuzdan düşmüş — kıyasın bir tarafı yok"
    assert "size_mult" in anahtarlar and "peak" in anahtarlar, \
        "de-risk girdileri makbuzdan düşmüş"


def test_iki_sermaye_AYRI_adlarla_durur():
    """Aynı sayı iki kez yazılırsa makbuz yalan söyler: alanlar AYRI olmalı."""
    m = _makbuz_sozlugu()
    esler = {k.value: v for k, v in zip(m.keys, m.values) if isinstance(k, ast.Constant)}
    ayna_ad = _submit_plan_cagrisi().args[1].id
    ayna_alan = [k for k, v in esler.items()
                 if any(isinstance(n, ast.Name) and n.id == ayna_ad for n in ast.walk(v))]
    assert ayna_alan, "ayna sermayesi hiçbir alanda yok"
    assert "eq_now" not in ayna_alan, \
        "ayna sermayesi `eq_now` alanına yazılmış — kitabınkinin ÜSTÜNE bindi, iki taban ayırt edilemez"


# ─────────────────────────────────────────────────────────────────────────────
# TÜKETİCİ (YASA 6): `eq_ayna` yalnız yazılırsa okuyucusuz alan olur. Tüketici
# `_drift_sinifi_adet` — sapma sınıfı tablosu. YENİ SINIF `ayna_taban` YALNIZ sınıflandırıcının
# PES ETTİĞİ son dalda çalışır: oradaki cümle "tüm ölçülebilir girdiler eşit" der ve `eq_ayna`
# ayrıysa o cümle ZATEN YANLIŞTIR. Önceki hiçbir sınıf bu yüzden yerinden oynamaz.
import pytest

from meridian import loop, store


@pytest.fixture
def son_dal(monkeypatch):
    """Sınıflandırıcıyı SON dala getirir: `kitap_kaydi` yerel kitap rev'ine bakıyor ve testi
    ortama bağımlı kılıyordu (yerelde rev=911, fikstürde 22 → yeni sınıfa hiç sıra gelmiyordu).
    Damgayı sabitlemek testi HERMETİK yapar; ölçtüğü şeyi değiştirmez."""
    monkeypatch.setattr(store, "stamp", lambda *a, **k: (None, 22))


def _mk(**k):
    """Sınıflandırıcının SON dalına düşen makbuz: her şey eşit, kıyas yapılabilir."""
    return {"eq_kaynak": "eq_now", "eq_now": 107288.55, "peak": 107288.55,
            "size_mult": 1.0, "kitap_rev": 22, "dolum_eq": 107288.55,
            "dolum_peak": 107288.55, **k}


def test_ayna_taban_ayrisinca_ADIYLA_siniflanir(son_dal):
    """Canlı vaka: kitap 107.288,55 ile, ayna ~99.800 ile boyutlandı → sapmanın SEBEBİ budur."""
    s, neden = loop._drift_sinifi_adet(_mk(eq_ayna=99800.0),
                                       fill_eq_now=107288.55, fill_peak=107288.55, dolum_taze=True)
    assert s == "ayna_taban", f"{s} — {neden}"
    assert "107288" in neden.replace(".", "").replace(",", "") or "107288.55" in neden
    assert "99800" in neden.replace(".", "").replace(",", "")
    assert len(neden) >= 20


def test_ayna_taban_ESITSE_eski_hukum_korunur(son_dal):
    """İki taban aynıysa yeni sınıf SUSAR — aksi halde her sapmayı kendine çekerdi."""
    s, _ = loop._drift_sinifi_adet(_mk(eq_ayna=107288.55),
                                   fill_eq_now=107288.55, fill_peak=107288.55, dolum_taze=True)
    assert s == "olculemedi"


def test_ESKI_makbuz_yanlis_siniflanmaz(son_dal):
    """GERİYE UYUM — canlıdaki dört makbuz (CRM·BDX·MRK·MRNA) `eq_ayna` TAŞIMIYOR.
    Alan yokluğu 'taban ayrıştı' diye okunursa dört pozisyon birden YANLIŞ sınıflanır."""
    s, neden = loop._drift_sinifi_adet(_mk(), fill_eq_now=107288.55,
                                       fill_peak=107288.55, dolum_taze=True)
    assert s == "olculemedi", f"eski makbuz {s} diye sınıflandı — uydurma"
    assert "makbuz" in neden or "beyan" in neden


@pytest.mark.parametrize("bozuk", ["yok", None, ""])
def test_bozuk_eq_ayna_uydurmaz(bozuk, son_dal):
    """Sayıya çevrilemeyen `eq_ayna` 'ayrışma var' DEMEK DEĞİLDİR — sessizce eski hükme düşer."""
    s, _ = loop._drift_sinifi_adet(_mk(eq_ayna=bozuk), fill_eq_now=107288.55,
                                   fill_peak=107288.55, dolum_taze=True)
    assert s == "olculemedi"
