"""Sermaye tabanı birleştirme — B (ayna kitabın tabanıyla boyutlanır) + D (kitap aynanın
adedini benimser). ROADMAP Ö-53, operatör kararı 2026-08-22.

ÖLÇÜLEN GEREKÇE. Yedi açık pozisyonun yedisinde de adet ayrıştı. İki mekanizma ölçüldü:

  1. per_share (BASKIN, dördünde de): ayna emri DOLUMDAN ÖNCE vermek zorunda →
     `tetik − stop`; kitap dolumdan SONRA yazar → `dolum − stop`. CRM'de birebir doğrulandı
     (ayna 0,315·%1·99.997,14/16,1203 = 19 · kitap .../17,6517 = 17). Bu fark YAPISAL:
     iki taraf da kendi bağlamında DOĞRU ve fark ortadan KALDIRILAMAZ, ancak UZLAŞTIRILABİLİR.
  2. equity tabanı (ikincil, −%2,1…+%6,5): kitap `_hb["equity"]`, ayna `acct["equity"]`.

B mekanizma-2'yi kaynağında kurutur; D mekanizma-1'in kaçınılmaz artığını dolumdan SONRA
uzlaştırır. İkisi birlikte gerekli — B tek başına ayrışmanın küçük kısmını çözerdi.
"""
import ast
import pathlib

import pytest

LOOP_YOL = pathlib.Path(__file__).resolve().parents[1] / "meridian" / "loop.py"
AGAC = ast.parse(LOOP_YOL.read_text(encoding="utf-8"))


# ═══════════════════════════ B — AYNA KİTABIN TABANIYLA ═══════════════════════════

def _submit_cagrisi() -> ast.Call:
    for d in ast.walk(AGAC):
        if (isinstance(d, ast.Call) and isinstance(d.func, ast.Attribute)
                and d.func.attr == "submit_plan"):
            return d
    raise AssertionError("alpaca.submit_plan çağrısı YOK — çapa çürüdü, çiviler kör kalırdı")


def _boyut_ifadesi() -> ast.AST:
    """`submit_plan`e giden equity İFADESİ — argüman bir DEĞİŞKENSE tanımına kadar çözülür.

    Çivi sözdizimini değil ANLAMI sormalı: `submit_plan(pl, min(eq_now, eq))` ile
    `_x = min(eq_now, eq); submit_plan(pl, _x)` aynı şeydir ve ikincisi daha okunur. İlk hâl
    satır-içi ifade dayatıyordu, yani kodu çirkinleştirmeye zorluyordu — çivinin işi bu değil."""
    arg = _submit_cagrisi().args[1]
    if not isinstance(arg, ast.Name):
        return arg
    for d in ast.walk(AGAC):
        if (isinstance(d, ast.Assign) and len(d.targets) == 1
                and isinstance(d.targets[0], ast.Name) and d.targets[0].id == arg.id):
            return d.value
    raise AssertionError(f"`{arg.id}` submit_plan'e geçiyor ama TANIMI bulunamadı — çapa çürüdü")


def _boyut_adlari() -> set:
    return {n.id for n in ast.walk(_boyut_ifadesi()) if isinstance(n, ast.Name)}


def test_B_ayna_KITABIN_tabaniyla_boyutlanir():
    """`submit_plan`e giden equity artık broker'ın ham `eq`si DEĞİL — kitabın tabanını içermeli."""
    adlar = _boyut_adlari()
    assert "eq_now" in adlar, (
        f"ayna hâlâ kitabın tabanını görmüyor (ifadedeki adlar: {sorted(adlar)}) — B uygulanmamış")


def test_B_broker_tavani_KORUNUR():
    """GUARD: kitap equity'si broker'ınkini AŞABİLİR (ölçüldü: +%6,5). O hâlde emir broker'ın
    parasını aşar ve reddedilir. İfade `min` ile iki tabanı da görmeli — kitap tabanını
    KAYITSIZ ŞARTSIZ kullanmak yeni bir arıza sınıfı açardı."""
    adlar = _boyut_adlari()
    assert "min" in adlar, "broker tavanı YOK — kitap equity'si yüksekken emir reddedilir"
    assert "eq" in adlar, "broker tabanı ifadede yok — tavan neyle kıyaslanıyor?"


def _makbuz_sozlugu() -> ast.Dict:
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
    raise AssertionError("size_law makbuzu YOK — çapa çürüdü")


def test_B_makbuz_UC_tabani_da_yazar():
    """Kıyas üç sayı ister: kitabınki · broker'ınki · FİİLEN KULLANILAN. İkisi eksikse
    guard'ın bağlayıp bağlamadığı kayıttan çıkarılamaz."""
    anahtarlar = {k.value for k in _makbuz_sozlugu().keys if isinstance(k, ast.Constant)}
    for ad in ("eq_now", "eq_broker", "eq_ayna"):
        assert ad in anahtarlar, f"makbuzda `{ad}` yok (mevcut: {sorted(anahtarlar)})"


# ═══════════════════════════ D — KİTAP AYNANIN ADEDİNİ BENİMSER ═══════════════════

def _yardimci() -> ast.FunctionDef:
    for d in ast.walk(AGAC):
        if isinstance(d, ast.FunctionDef) and d.name == "_adet_benimse":
            return d
    raise AssertionError("_adet_benimse YOK — D uygulanmamış")


def test_D_yardimci_var_ve_cagriliyor():
    assert _yardimci() is not None
    cagri = [d for d in ast.walk(AGAC) if isinstance(d, ast.Call)
             and isinstance(d.func, ast.Name) and d.func.id == "_adet_benimse"]
    assert cagri, "_adet_benimse tanımlı ama HİÇ ÇAĞRILMIYOR — ölü kod"


def test_D_esikten_BAGIMSIZ_calisir():
    """%25 eşiği ALARM eşiğidir, ayrışma eşiği değil. Ölçüldü: BDX %7 · CRM %12 · MRK %14 —
    üçü de eşiğin ALTINDA ve sessizce ayrışıyordu. Benimseme eşiğe bağlanırsa bu üçü ayrışık
    kalır ve D amacını kaybeder."""
    src = LOOP_YOL.read_text(encoding="utf-8")
    i = src.index("_adet_benimse(")
    # çağrıdan geriye en yakın `> 0.25` eşik testi, ÇAĞRIYI KAPSAYAN blokta olmamalı:
    cagri_satir = src[:i].count("\n") + 1
    for d in ast.walk(AGAC):
        if not (isinstance(d, ast.If) and d.lineno < cagri_satir <= (d.end_lineno or 0)):
            continue
        kaynak = ast.unparse(d.test)
        assert "0.25" not in kaynak, (
            f"benimseme %25 eşiğinin İÇİNDE (satır {d.lineno}: `{kaynak}`) — "
            f"eşik altındaki BDX/CRM/MRK ayrışık kalır")


@pytest.mark.parametrize("ad,gerekce", [
    ("broker", "broker geçilmediyse (pano force-sync gibi eski çağıranlar) kitap DEĞİŞTİRİLEMEZ"),
    ("scaled", "ölçek-çıkış BİLİNÇLİ bir boşluktur, sapma değil — benimsenirse iş kaybolur"),
])
def test_D_kapsam_disi_dallar_KAYNAKTA(ad, gerekce):
    """D'nin kapsamı DAR ve bu darlık kodda GÖRÜNÜR olmalı."""
    govde = ast.unparse(_yardimci())
    kaynak = LOOP_YOL.read_text(encoding="utf-8")
    assert ad in govde or ad in kaynak, f"{ad} kapsam kısıtı yok — {gerekce}"


def test_D_tek_tarafli_pozisyonlara_DOKUNMAZ():
    """Yalnız kitapta olan (split_brain / karşılıksız Ö-52) ve yalnız broker'da olan
    (motor-dışı, operatörün kendi NVDA'sı) pozisyonlar AYRI sınıftır. Benimseme onlara
    uygulanırsa biri kitaptan pozisyon SİLER, diğeri sahiplik sınırını çiğner."""
    govde = ast.unparse(_yardimci())
    assert "positions" in govde, "yardımcı kitabın pozisyon defterine bakmıyor"
    # aynanın adedi 0/negatifse benimseme YAPILMAZ — yoksa "aynada yok" kitabı sıfırlardı
    assert ("<= 0" in govde or "< 1" in govde or "> 0" in govde), \
        "aynanın adedi sıfır/negatifken benimseme engellenmiyor — kitap sıfırlanabilir"


def test_D_degisiklik_KAYITLI():
    """UYDURMA YASAĞI'nın kardeşi: sessiz düzeltme, düzeltme değil KAYIPTIR. Benimseme
    öncesi/sonrası adetle birlikte deftere ve olay akışına düşmeli."""
    govde = ast.unparse(_yardimci())
    assert "obs." in govde, "benimseme olay akışına yazmıyor — operatör düzeltmeyi göremez"
    assert "out" in govde, "benimseme broker_reconcile çıktısına yazmıyor (YASA 6 okuyucusu)"


def test_D_sinif_semboller_arasi_TASMAZ():
    """DÖNGÜ TAŞMASI. `_sinif` yalnız %25 eşiğini aşan dalda atanır; benimseme eşiğin DIŞINDA
    koşar. Sıfırlanmazsa bir ÖNCEKİ sembolün sınıfı bu sembole yapışır — sessiz ve teşhisi
    zehirleyen bir hata (ilk uygulamada `locals().get` ile tam bunu yapmıştım, öz inceleme yakaladı).

    Çivi: döngü gövdesinde, eşik testinden ÖNCE bir `_sinif = ... None` sıfırlaması olmalı."""
    src = LOOP_YOL.read_text(encoding="utf-8")
    esik = src.index("abs(aq - qty) / qty > 0.25")
    onceki = src.rindex("_sinif", 0, esik)
    blok = src[onceki:esik]
    assert "None" in blok, (
        "eşik testinden önce `_sinif` sıfırlaması YOK — bir önceki sembolün sınıfı taşar")
    # `locals()` YASAĞI ÇAĞRI YERİNE DARALTILDI: dosyanın başka yerinde meşru kullanımı var,
    # dosya geneli bir yasak o yüzden yanlış-pozitifti (ilk hâli tam bunu yaptı).
    cagri = next((d for d in ast.walk(ast.parse(src)) if isinstance(d, ast.Call)
                  and isinstance(d.func, ast.Name) and d.func.id == "_adet_benimse"), None)
    assert cagri is not None, "_adet_benimse çağrısı bulunamadı — çapa çürüdü"
    kw = next((k for k in cagri.keywords if k.arg == "sinif"), None)
    assert kw is not None, "`sinif` adlandırılmış argüman olarak geçmiyor"
    assert isinstance(kw.value, ast.Name), (
        f"sınıf AÇIKÇA bir değişken olarak geçmeli, gelen {type(kw.value).__name__} "
        f"(`locals()` gibi dolaylı okuma teşhisi sessizce zehirler)")
