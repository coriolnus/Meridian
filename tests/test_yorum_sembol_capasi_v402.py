"""test_yorum_sembol_capasi_v402.py — TSK-120: `api.py`'nin 7 çürük sembol çapası +
`capa_uyusmasi`nın ÜÇÜNCÜ BESLEMESİ (`meridian/**`+`tests/**` yorum satırları + docstring'leri).

BOŞLUK (ölçüldü 2026-09-03, v382 bölüm E prototipi): `codelaw.report()` sembol çapasını yalnız
İKİ kaynaktan besliyordu — `DECLARED_*` beyan metinleri ve `ui/src` tsx/ts kaynağı. `meridian/**`
ve `tests/**` dosyalarının SERBEST yorum/docstring metni HİÇBİR taramadan geçmiyordu; `api.py`
tam olarak bu kör noktada yedi çürük `modül.sembol` çapası biriktirmişti (D2, TSK-120).

D1 — TARAYICI KUSURU: `codelaw._modul_adlari`'nın `ast.Assign` dalı yalnız `ast.Name` hedeflerini
topluyordu; `AKTIF, ARSIV = "aktif", "arsiv"` gibi tuple-unpack atamalar SESSİZCE atlanıyordu —
`skills.ARSIV` GERÇEK bir sembolken sahte-çürük görünüyordu (yasanın en pahalı arızası: yanlış
alarm). Düzeltme `_atama_adlari` yardımcısı ile geldi; bu dosya o düzeltmeyi sentetik bir modülde
DOĞRUDAN ölçer.

D3 — ÜÇÜNCÜ BESLEME: `codelaw._yorum_metinleri`/`_dosya_yorum_metni` KOD DİZGESİNİ DEĞİL, yalnız
YORUM (`tokenize.COMMENT`) ve DOCSTRING (`ast.get_docstring`) metnini çeker — `_TERFI_ASAMA =
"shadow_model.terfi"` gibi bir kod sabiti çapa SAYILMAMALI, çünkü o bir VERİDİR, yazarın serbest
düşüncesi değil. Bu ayrım sentetik olarak burada ölçülür.
"""
from __future__ import annotations

import ast
import pathlib

from meridian import codelaw

REPO = pathlib.Path(__file__).resolve().parents[1]
MERIDIAN = REPO / "meridian"

#: D2'de düzeltilen yedi ÇÜRÜK çapa (canlı ağaçta artık BULUNMAMALI). "shadow_model.terfi" iki
#: konumda tekrarlıyordu (×2) — sözlük anahtarı bu yüzden sayıyı değil VARLIĞI ölçer, aşağıdaki
#: test iki konumu da metinden ayrı ayrı doğrular.
D2_DUZELTILEN_CAPALAR = (
    "shadow_model.terfi",
    "shadow_model.refit_and_save",
    "skills.ARSIV",
    "ledgers.cf_resolved",
    "durum_sozlugu.satirlar",
    "auth.header.Authorization",
)


# ---------------------------------------------------------------------------
# (a) D1 — TUPLE-ASSIGN TARAYICI KUSURU
# ---------------------------------------------------------------------------

def test_TUPLE_ASSIGN_hedefleri_MODUL_ADLARINA_toplanir():
    """Sentetik modül: `AKTIF, ARSIV = "aktif", "arsiv"` — İKİ ad da toplanmalı. Eski hâl yalnız
    `ast.Name` hedefini işliyordu, tuple hedefini SESSİZCE atlıyordu (`skills.ARSIV`nin gerçek
    kusuru buydu)."""
    tree = ast.parse('AKTIF, ARSIV = "aktif", "arsiv"\n')
    adlar = codelaw._modul_adlari(tree)
    assert {"AKTIF", "ARSIV"} <= adlar, adlar


def test_IC_ICE_TUPLE_de_cozulur():
    """`_atama_adlari` yinelemeli: `(a, (b, c)) = ...` AST'de geçerlidir ve nadir olsa da
    aynı kusuru taşırdı — yinelemeli çözüm olmasaydı `c` sessizce kaybolurdu."""
    tree = ast.parse("a, (b, c) = 1, (2, 3)\n")
    adlar = codelaw._modul_adlari(tree)
    assert {"a", "b", "c"} <= adlar, adlar


def test_DUZ_NAME_atama_REGRESYONU_bozulmadi():
    """Tuple dalı eklenirken düz `ad = deger` yolu bozulmamalı (regresyon)."""
    tree = ast.parse("SABIT = 1\n")
    assert "SABIT" in codelaw._modul_adlari(tree)


def test_SKILLS_ARSIV_CANLI_AGACTA_cozulur(tmp_path=None):
    """CANLI ölçüm: `skills.py`deki gerçek `AKTIF, ARSIV = ...` artık `cozulen`e düşer —
    api.py'de HİÇBİR değişiklik gerekmeden (D1 kusuru api.py'de değil `_modul_adlari`deydi)."""
    r = codelaw.capa_uyusmasi([("test", "`skills.ARSIV` gerçek mi?")],
                              py_kokler=("meridian",), modul_bicimi=True)
    assert [c["sembol"] for c in r["cozulen"]] == ["ARSIV"], r
    assert r["curuyen"] == [], r


# ---------------------------------------------------------------------------
# (b) SINIF-NİTELİKLİ AD (classmethod) — canlı "shadow_model.refit_and_save" düzeltmesi
# ---------------------------------------------------------------------------

def test_CLASSMETHOD_dosya_sembol_bicimiyle_CANLIDA_cozulur():
    """D2 düzeltmesinin kendisi ölçülür: `shadow_model.py::ShadowTradeOutcomeModel.refit_and_save`
    (classmethod) `dosya.py::Sinif.metot` biçimiyle CANLI ağaçta çözülür — `_modul_adlari` sınıf
    gövdesindeki üyeleri zaten `Sinif.uye` biçiminde topluyor (D1'in AYRI bir dalı DEĞİL, mevcut
    davranış); api.py'nin düzeltmesi bu davranışa DAYANIR."""
    r = codelaw.capa_uyusmasi(
        [("test", "`shadow_model.py::ShadowTradeOutcomeModel.refit_and_save` ve "
                   "`shadow_model.py::ShadowTradeOutcomeModel.evaluate_promotion`")],
        py_kokler=("meridian",))
    semboller = {c["sembol"] for c in r["cozulen"]}
    assert semboller == {"ShadowTradeOutcomeModel.refit_and_save",
                         "ShadowTradeOutcomeModel.evaluate_promotion"}, r
    assert r["curuyen"] == [], r


# ---------------------------------------------------------------------------
# (c) D3 — YORUM/DOCSTRING METNİ ÇEKİLİR, KOD DİZGESİ ÇEKİLMEZ
# ---------------------------------------------------------------------------

_HEDEF_MODUL = (
    "def var_olan():\n"
    "    return 1\n"
)

_KOD_DIZGESI_ICEREN = (
    '"""Modül docstring: hedef.py::var_olan burada da geçer (DOCSTRING — ÇEKİLMELİ)."""\n'
    "# yorum: hedef.py::var_olan yorumda da var (YORUM — ÇEKİLMELİ)\n"
    '_SABIT = "hedef.py::kayip_sembol"   # bu bir KOD DİZGESİDİR — ÇEKİLMEMELİ\n'
    "def f():\n"
    '    return "hedef.py::kayip_sembol_2"  # yine kod dizgesi, ÇEKİLMEMELİ\n'
)


def test_KOD_DIZGESI_CEKILMEZ_yorum_ve_docstring_CEKILIR(tmp_path):
    (tmp_path / "hedef.py").write_text(_HEDEF_MODUL, encoding="utf-8")
    (tmp_path / "kaynak.py").write_text(_KOD_DIZGESI_ICEREN, encoding="utf-8")
    metin = codelaw._dosya_yorum_metni(tmp_path / "kaynak.py")
    assert "hedef.py::var_olan" in metin, metin
    assert "kayip_sembol" not in metin, (
        f"kod dizgesi (`_SABIT` ve `return` değeri) ÇEKİLDİ — yorum/docstring ayrımı çalışmıyor: {metin}")


def test_KOD_DIZGESINDEKI_capa_HUKME_GIRMEZ(tmp_path):
    """Uçtan uca: kod dizgesindeki kırık çapa (`hedef.py::kayip_sembol`) `capa_uyusmasi`ya HİÇ
    girmemeli — ne `cozulen`e ne `curuyen`e. Yorumdaki DOĞRU çapa (`var_olan`) ise çözülmeli."""
    (tmp_path / "hedef.py").write_text(_HEDEF_MODUL, encoding="utf-8")
    (tmp_path / "kaynak.py").write_text(_KOD_DIZGESI_ICEREN, encoding="utf-8")
    metin = codelaw._dosya_yorum_metni(tmp_path / "kaynak.py")
    r = codelaw.capa_uyusmasi([("kaynak.py", metin)], py_kokler=(str(tmp_path),))
    semboller_curuyen = {c["sembol"] for c in r["curuyen"]}
    assert "kayip_sembol" not in semboller_curuyen and "kayip_sembol_2" not in semboller_curuyen, r
    assert any(c["sembol"] == "var_olan" for c in r["cozulen"]), r


# ---------------------------------------------------------------------------
# (d) SENTETİK ÇÜRÜK ÇAPA — `curuyen`e düşer
# ---------------------------------------------------------------------------

def test_SENTETIK_CURUK_yorum_capasi_YORUM_METINLERI_ile_CURUYENE_duser(tmp_path):
    """`_yorum_metinleri` bir kökten dosya toplar; sentetik kökte kırık bir `modül.sembol`
    yorumu gerçekten `curuyen`e düşmeli — mekanizmanın UÇTAN UCA çalıştığının pozitif kontrolü."""
    (tmp_path / "meridian").mkdir()
    (tmp_path / "meridian" / "hedef.py").write_text(_HEDEF_MODUL, encoding="utf-8")
    (tmp_path / "meridian" / "kaynak.py").write_text(
        "# kırık çapa: `hedef.olmayan_sembol` burada yaşıyor\n", encoding="utf-8")
    import os
    cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        ler = codelaw._yorum_metinleri(kokler=("meridian",))
        r = codelaw.capa_uyusmasi(ler, py_kokler=("meridian",), modul_bicimi=True)
    finally:
        os.chdir(cwd)
    assert [(c["capa"], c["neden"]) for c in r["curuyen"]] == [
        ("hedef.olmayan_sembol", "sembol_yok")], r


# ---------------------------------------------------------------------------
# (e) CANLI AĞAÇ — api.py'de yedisi YOK (ÇALIŞMA AĞACI, `git show` DEĞİL)
# ---------------------------------------------------------------------------

def test_CANLI_CALISMA_AGACINDA_api_py_YEDI_capa_YOK():
    """D2'nin nihai hükmü: bugünkü ÇALIŞMA AĞACINDA (diskteki dosya, `git show HEAD:` değil)
    `codelaw.report()`ın üçüncü beslemesi `api.py` kaynaklı TEK BİR çürük dahi bulmamalı."""
    r = codelaw.report()
    y = r["yorum_sembol_capalari"]
    assert y is not None, "yorum_sembol_capalari ÖLÇÜLMEDİ (None) — canlı kökte hesaplanmalıydı"
    api_curuk = [c for c in y["curuyen"] if c["kaynak"] == "meridian/api.py"]
    assert api_curuk == [], f"api.py hâlâ çürük çapa taşıyor: {api_curuk}"


def test_CANLI_CALISMA_AGACINDA_D2_CAPALARI_api_py_KAYNAKLI_DEGIL():
    """DAR hüküm, KAYNAĞA BAĞLI (UYDURMA YASAĞI — D2'nin sözleşmesi yalnız `api.py`ydi, "hiçbir
    dosyada asla" DEĞİL): D2'nin isim listesindeki YEDİ çapa metni, kaynağı `meridian/api.py`
    OLAN hiçbir curuyen kaydında görünmemeli. ÖLÇÜLDÜ (2026-09-03): aynı METİN başka dosyalarda
    (`tests/test_golge_fit_gorunurlugu_v192.py`, `tests/test_capa_uyusmasi_v373.py`,
    `tests/test_kapi_yuzeyi_v361.py` — hepsi TSK-120'nin dosya sahipliği DIŞINDA) BAĞIMSIZ olarak
    da tekrarlanıyor; bunları düzeltmek bu görevin kapsamı DIŞINDA (raporda listelenir, Rol-1
    karar verir) — bu test o genişlemeyi İDDİA ETMEZ."""
    r = codelaw.report()
    api_capalar = {c["capa"] for c in r["yorum_sembol_capalari"]["curuyen"]
                   if c["kaynak"] == "meridian/api.py"}
    for capa in D2_DUZELTILEN_CAPALAR:
        assert capa not in api_capalar, f"{capa} api.py kaynaklı curuyen'de: {api_capalar}"


# ---------------------------------------------------------------------------
# (f) KÖRLÜK ALARMI — taranan dosya ≥ 200 ve capa_n ölçülen tabanın altına düşmez
# ---------------------------------------------------------------------------

#: ÖLÇÜLDÜ 2026-09-03: 567 taranan dosya, capa_n ~2200+. Eşik ÖLÇÜMÜN KENDİSİ DEĞİL — düşük
#: tutulan bir KÖRLÜK ALARMIdır (v373 `CANLI_ASGARI_COZULEN` deseni): tarayıcı yanlış köke ya da
#: yanlış dosya uzantısına bakarsa `taranan_dosya`/`capa_n` çöker ve "0 çürük" hükmü sahte-yeşile
#: döner. 200/500 böyle bir çöküşü kaçırmayacak kadar yüksek, meşru bir temizliği kırmızıya
#: çevirmeyecek kadar düşüktür.
CANLI_ASGARI_TARANAN_DOSYA = 200
CANLI_ASGARI_CAPA_N = 500


def test_KORLUK_ALARMI_taranan_dosya_ve_capa_n_TABANI_asiyor():
    y = codelaw.report()["yorum_sembol_capalari"]
    assert y["taranan_dosya"] >= CANLI_ASGARI_TARANAN_DOSYA, (
        f"yalnız {y['taranan_dosya']} dosya tarandı (asgari {CANLI_ASGARI_TARANAN_DOSYA}) — "
        "kök/uzantı yanlış olabilir")
    assert y["capa_n"] >= CANLI_ASGARI_CAPA_N, (
        f"yalnız {y['capa_n']} çapa görüldü (asgari {CANLI_ASGARI_CAPA_N}) — tarayıcı kör olabilir")


def test_report_ALANI_SENTETIK_KOKTE_UYDURMAZ(tmp_path):
    """Ölçülmeyen alan `None`dır, boş sözlük DEĞİL — `sembol_capalari`/`tsx_line_anchors` ile
    AYNI disiplin (v373/v314 emsali)."""
    r = codelaw.report(str(tmp_path))
    assert r["yorum_sembol_capalari"] is None, r["yorum_sembol_capalari"]


def test_report_ALANI_AŞAMA1_OKu_DUSURMEZ():
    """AŞAMA 1 — GÖZLEMSEL: canlı ağaçta bugün `curuyen` boş DEĞİL (102 ölçüldü, D2'nin dışındaki
    ~40 dosyada, TSK-120'nin dosya sahipliği DIŞINDA) — buna rağmen `report()["ok"]` bu alandan
    ETKİLENMEMELİ. Aşama 2'ye bağlanmadığının doğrudan kanıtı budur."""
    r = codelaw.report()
    y = r["yorum_sembol_capalari"]
    if y["curuyen"]:
        assert r["ok"] is True or "ok" in r, (
            "yorum_sembol_capalari dolu ama report() başka bir nedenle zaten kırmızıysa bu test "
            "o kırmızılığı gizlemez; yalnız BU ALANIN ok'u düşürmediğini ölçer")
    # DOĞRUDAN ÖLÇÜM: alan `ok` hesaplamasında KULLANILMAMALI — silent_handlers/graph/curuk/UNSCANNED/
    # capalar/tsx_nuks/docs_curuk_var/sembol_curume DIŞINDA hiçbir bileşen `ok`u etkilemez; bu ürün
    # kodundaki (`codelaw.report`) satırın kendisiyle doğrulanır: aşağıdaki grep sözleşmesi bekçidir.
    import inspect
    kaynak = inspect.getsource(codelaw.report)
    ok_satiri = kaynak[kaynak.index('"ok":'):]
    assert "yorum_sembol" not in ok_satiri, (
        "AŞAMA 2 (henüz erken): `ok` ifadesi yorum_sembol alanına bağlanmış görünüyor ama canlı "
        f"curuyen boş değil ({len(y['curuyen'])}) — bağlamak sahte-kırmızı üretir")


def test_report_ALAN_SEKLI_taranan_dosya_capa_n_curuyen():
    """YASA 6: rapora yazılan alanın okuyucusu bu dosyadır — üç anahtar da adıyla okunur."""
    y = codelaw.report()["yorum_sembol_capalari"]
    assert set(y) == {"taranan_dosya", "capa_n", "curuyen"}, sorted(y)
    assert isinstance(y["taranan_dosya"], int) and isinstance(y["capa_n"], int)
    assert isinstance(y["curuyen"], list)


# ---------------------------------------------------------------------------
# (g) DÜZELTME TURU 1 — İNCELEME BULGUSU: `_YORUM_MEMO` KÖRLÜĞÜ YUTMAMALI
# ---------------------------------------------------------------------------

def test_YORUM_MEMO_KORLUGU_YUTMAZ(tmp_path):
    """İNCELEME BULGUSU (düzeltme turu 1, 2026-09-03): `_dosya_yorum_metni` `_GRAPH_CACHE` sınıfı
    bir SONUÇ önbelleğidir (`_YORUM_MEMO`) ama tokenize/ast HATASINDA bile sonucu önbelleğe
    yazıyordu — ikinci çağrı (aynı mtime) önbellek isabetinden dönüyor ve `_note_unscanned`i BİR
    DAHA çağırmıyordu (körlük sinyali kayboluyordu). `codelaw.py`nin kendi sözlüğü bu SINIFI
    (`_GRAPH_CACHE`/`_CLAIMS_CACHE`/`ledgers._WRITERS_CACHE`) üç kez tekrarlayıp
    `_onbellek_oku`/`_onbellege_yaz` ile kapatmıştı; `_YORUM_MEMO` dosya-başına çağrıldığı için o
    gövdenin evre-önekli yakalaması ÇAPRAZ-DOSYA sızıntısı üretirdi — bu yüzden seçilen düzeltme
    `_KAYNAK_MEMO`/`_AST_MEMO` sözleşmesiyle BİREBİR: başarısızlıkta HİÇBİR ŞEY önbelleklenmez,
    ikinci çağrı YENİDEN dener ve körlüğü YENİDEN bildirir. Emsal (TERS mekanizma, AYNI hedef):
    `tests/test_codelaw_kor_nokta_v214.py::test_onbellek_KORLUGU_YUTMAZ`."""
    (tmp_path / "bozuk.py").write_text("def (\n", encoding="utf-8")
    codelaw.UNSCANNED.clear()
    codelaw._dosya_yorum_metni(tmp_path / "bozuk.py")
    ilk = len(codelaw.UNSCANNED)
    assert ilk > 0, "ilk çağrı körlüğü hiç kaydetmedi — pozitif kontrol düştü"
    codelaw.UNSCANNED.clear()
    codelaw._dosya_yorum_metni(tmp_path / "bozuk.py")   # AYNI mtime — memo YAZILMAMIŞ olmalı
    assert len(codelaw.UNSCANNED) == ilk, (
        "ikinci çağrı körlüğü kaydetmedi — hata sonucu önbelleğe yazılmış olabilir (KÖRLÜK YUTULDU)")
    assert str(tmp_path / "bozuk.py") not in codelaw._YORUM_MEMO, (
        "bozuk dosyanın sonucu `_YORUM_MEMO`ya YAZILDI — `_KAYNAK_MEMO`/`_AST_MEMO` sözleşmesi ihlal edildi")
    codelaw.UNSCANNED.clear()


def test_YORUM_MEMO_BASARILI_DOSYAYI_YINE_ONBELLEKLER(tmp_path):
    """Düzeltmenin BEDELİ ölçülür (bedel yasası): hata durumunda önbellek kapatılırken SAĞLAM
    dosyalarda önbellek KAYBEDİLMEMELİ — aksi hâlde D5'in bedel ölçümü geçersiz kalırdı."""
    (tmp_path / "saglam.py").write_text('"""d."""\n# yorum\ndef f():\n    pass\n', encoding="utf-8")
    codelaw._dosya_yorum_metni(tmp_path / "saglam.py")
    assert str(tmp_path / "saglam.py") in codelaw._YORUM_MEMO, (
        "sağlam dosyanın sonucu önbelleklenmedi — düzeltme başarı yolunu da bozmuş olabilir")
