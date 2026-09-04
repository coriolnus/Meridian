"""test_capa_uyusmasi_v373.py — SEMBOL ÇAPASI YASASI: `dosya.py::sembol` AST İLE DOĞRULANIR.

BOŞLUK (ölçüldü 2026-09-02, TSK-030 adım-2): satır çapası (`dosya.py:NNN`) sessizce çürür —
api.py'ye eklenen 38 satır 36 çapayı birden kaydırdı ve iki çivi (v214/v314) kırmızıya döndü.
Çırçır (`TSX_CAPA_TABANI`) borcun BÜYÜMESİNİ engelliyordu ama çapanın BAYATLIĞINI otomatik
DOĞRULAYAMIYORDU: bir satır numarası her zaman "bir satırı" gösterir, doğru satırı gösterip
göstermediği ölçülemez. SEMBOL çapası da çürür — ama çürümesi SESLİDİR: sembol silinince ya da
adı değişince AST'de BULUNAMAZ ve yasa o an öter.

ÇEKİRDEK TEK, BESLEME İKİ (tek-kaynak yasası): `codelaw.capa_uyusmasi` metinden çapa çıkarıp
hedef modülü AST ile ayrıştırır; onu İKİ kaynak besler — (a) `DECLARED_*` beyan metinleri,
(b) `ui/src` tsx/ts kaynağı. İki besleme iki tarayıcıya bölünseydi çürüme sınıfının tanımı
zamanla ayrışırdı (`_capalari_olc`in satır dünyasında paylaşılma gerekçesinin aynısı).

ÜÇ KOVA, HEPSİ ADLI (v214'ün "unresolved adıyla sayılır" deseni): çözülen · çürüyen ·
çözülemeyen. "0 çürük" cümlesi, kaçının hakkında hüküm KURULAMADIĞI bilinmeden okunamaz.
"""
from __future__ import annotations

import pathlib

from meridian import codelaw

#: Canlı ağaçta bugün ölçülen sembol çapası sayısının ALT SINIRI — pozitif kontrolün eşiği.
#: Tarayıcı yanlış köke ya da yanlış uzantıya bakarsa sıfır dosya döner ve "0 çürüyen" hükmü
#: bekçinin kendi körlüğünü yeşil sanmasına dönerdi (v314 `test_TARAMA_SESSIZCE_BOS_DEGIL`).
#: ÖLÇÜLDÜ 2026-09-02: 299 çözülen (260 tsx + 39 beyan), 0 çürüyen, 0 çözülemeyen. Eşik ÖLÇÜMÜN
#: KENDİSİ DEĞİL: bu bir çırçır değil KÖRLÜK ALARMIdır — sayıya yapıştırmak, çapa silen her meşru
#: temizliği kırmızıya çevirirdi. 150, "tarayıcı yüzlerce dosyayı gerçekten görüyor" demeye yeter
#: ve yanlış-kök/yanlış-uzantı arızasının ürettiği sıfırı kaçırmaz.
CANLI_ASGARI_COZULEN = 150


def _agac(kok: pathlib.Path, govde: str, ad: str = "hedef.py") -> None:
    (kok / ad).write_text(govde, encoding="utf-8")


_HEDEF = (
    "SABIT = 1\n"
    "\n"
    "def var_olan():\n"
    "    return SABIT\n"
    "\n"
    "class Sinif:\n"
    "    ALAN = 2\n"
    "    def metot(self):\n"
    "        return self.ALAN\n"
)


def _coz(tmp_path, metin, kaynak="Kart.tsx"):
    return codelaw.capa_uyusmasi([(kaynak, metin)], py_kokler=(str(tmp_path),))


# ---------------------------------------------------------------------------
# (a) ÜÇ KOVA — hepsi ADLI
# ---------------------------------------------------------------------------

def test_VAR_OLAN_sembol_COZULENE_adiyla_duser(tmp_path):
    """Temel hüküm: hedef modül AST ile ayrıştırılır ve sembol BULUNUR."""
    _agac(tmp_path, _HEDEF)
    r = _coz(tmp_path, "// kaynak: hedef.py::var_olan\n")
    assert [(c["kaynak"], c["capa"], c["sembol"]) for c in r["cozulen"]] == [
        ("Kart.tsx", "hedef.py::var_olan", "var_olan")], r
    assert r["curuyen"] == [] and r["cozulemeyen"] == [], r


def test_SILINEN_sembol_CURUYENE_adiyla_duser(tmp_path):
    """ÇÜRÜMENİN SESLİ OLMASI: modül VAR, sembol YOK. Satır çapasında bu sınıf ölçülemezdi —
    silinen bir fonksiyonun satır numarası hâlâ "bir satırı" gösterirdi."""
    _agac(tmp_path, _HEDEF)
    r = _coz(tmp_path, "// kaynak: hedef.py::silinmis_olan\n")
    assert [(c["capa"], c["sembol"], c["neden"]) for c in r["curuyen"]] == [
        ("hedef.py::silinmis_olan", "silinmis_olan", "sembol_yok")], r
    assert r["cozulen"] == [], r


def test_HEDEF_YOKSA_COZULEMEYENE_adiyla_duser(tmp_path):
    """Hükmü KURULAMAYAN çapa sessizce atılmaz (v214 disiplini) — ihlal DEĞİL ama SAYILIR."""
    _agac(tmp_path, _HEDEF)
    r = _coz(tmp_path, "// yok_boyle_bir_dosya.py::sembol ve hedef.py::var_olan\n")
    assert [(c["capa"], c["neden"]) for c in r["cozulemeyen"]] == [
        ("yok_boyle_bir_dosya.py::sembol", "hedef_yok")], r
    assert len(r["cozulen"]) == 1, r


def test_IKIRCIKLI_HEDEF_hukum_KURULMAZ(tmp_path):
    """Aynı adlı iki dosya → ölçülemeyen şey ihlal SAYILMAZ (UYDURMA YASAĞI), ama sayılır."""
    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()
    _agac(tmp_path / "a", _HEDEF)
    _agac(tmp_path / "b", "x = 1\n")
    r = _coz(tmp_path, "// hedef.py::var_olan\n")
    assert [(c["neden"], c["aday_n"]) for c in r["cozulemeyen"]] == [("ikircikli", 2)], r
    assert r["curuyen"] == [], r


def test_AYRISTIRILAMAYAN_HEDEF_hukum_KURULMAZ(tmp_path):
    """Sözdizimi bozuk hedef → `ayristirilamaz`. Çürüme İDDİA EDİLMEZ: AST kurulamadıysa
    sembolün yokluğu kanıtlanmış değildir."""
    _agac(tmp_path, "def yarim(\n")
    r = _coz(tmp_path, "// hedef.py::yarim\n")
    assert [(c["capa"], c["neden"]) for c in r["cozulemeyen"]] == [
        ("hedef.py::yarim", "ayristirilamaz")], r
    assert r["curuyen"] == [], r


# ---------------------------------------------------------------------------
# (b) ÇAPA BİÇİMLERİ
# ---------------------------------------------------------------------------

def test_SINIF_METODU_noktali_adla_cozulur(tmp_path):
    """`Sinif.metot` — sınıf gövdesindeki adlar da çözülür. Yalnız modül-seviyesi adları
    tanısaydık `broker.py::PaperBroker.size_position` gibi ÖLÇÜLEBİLİR bir çapa sessizce
    çürük sayılırdı (yanlış alarm, yasanın en pahalı arızası)."""
    _agac(tmp_path, _HEDEF)
    r = _coz(tmp_path, "// hedef.py::Sinif.metot · hedef.py::Sinif.ALAN · hedef.py::SABIT\n")
    assert [c["sembol"] for c in r["cozulen"]] == ["Sinif.metot", "Sinif.ALAN", "SABIT"], r


def test_SINIFTA_OLMAYAN_METOT_CURUR(tmp_path):
    """Noktalı ad GEVŞETME DEĞİL: sınıfta bulunmayan üye yine çürür."""
    _agac(tmp_path, _HEDEF)
    r = _coz(tmp_path, "// hedef.py::Sinif.yok_boyle\n")
    assert [c["sembol"] for c in r["curuyen"]] == ["Sinif.yok_boyle"], r


def test_YOL_ONEKLI_capa_yalniz_O_YOLU_olcer(tmp_path):
    """`adapters/hedef.py::var_olan` — yol belirtilmişse yalnız o yol ölçülür (satır dünyasındaki
    `kapsam_disi` disiplininin aynısı)."""
    (tmp_path / "adapters").mkdir()
    _agac(tmp_path / "adapters", _HEDEF)
    assert [c["sembol"] for c in _coz(tmp_path, "// adapters/hedef.py::var_olan\n")["cozulen"]] \
        == ["var_olan"]
    assert [c["neden"] for c in _coz(tmp_path, "// baska/hedef.py::var_olan\n")["cozulemeyen"]] \
        == ["kapsam_disi"]


def test_MODUL_SEMBOL_bicimi_BACKTICK_icinde_cozulur(tmp_path):
    """PYTHON TARAFININ BİÇİMİ: `DECLARED_*` beyanları çapayı `modül.sembol` diye yazar
    (`hermes.search_progress_oku`), `dosya.py::sembol` diye değil. Aynı çekirdek ikisini de
    ölçer — iki biçim iki tarayıcıya bölünseydi beyan metinleri yine kör kalırdı."""
    _agac(tmp_path, _HEDEF)
    r = codelaw.capa_uyusmasi([("codelaw.py", "okuyan `hedef.var_olan`, yazan `hedef.SABIT`")],
                              py_kokler=(str(tmp_path),), modul_bicimi=True)
    assert [c["sembol"] for c in r["cozulen"]] == ["var_olan", "SABIT"], r


def test_MODUL_SEMBOL_bicimi_CURUMEYI_de_gorur(tmp_path):
    """Beyan metnindeki ölü ad da öter — yoksa biçim tanınır ama hüküm verilmezdi."""
    _agac(tmp_path, _HEDEF)
    r = codelaw.capa_uyusmasi([("codelaw.py", "okuyan `hedef.olmayan_ad`")],
                              py_kokler=(str(tmp_path),), modul_bicimi=True)
    assert [(c["sembol"], c["neden"]) for c in r["curuyen"]] == [("olmayan_ad", "sembol_yok")], r


def test_MODUL_BICIMI_PANO_TARAFINDA_KAPALI(tmp_path):
    """KAPSAM SINIRI (1) — VE NEDEN: pano düzyazısında `modül.alan` bir SEMBOL değil bir JSON
    ALAN adıdır. İlk canlı ölçümde (2026-09-02) "scheduler.last_tick" · "sprint.sebep" ·
    "component_ic.verdict" · "auth.header.Authorization" bu yüzden YANLIŞ ÇÜRÜME üretti; yanlış
    alarm bu yasanın en pahalı arızasıdır (susturulan bekçi, olmayan bekçiden beterdir).
    Pano tarafının biçimi bu yüzden TEKTİR: `dosya.py::sembol`."""
    _agac(tmp_path, _HEDEF)
    metin = "ucun `hedef.olmayan_alan` alanı"
    assert codelaw.capa_uyusmasi([("K.tsx", metin)], py_kokler=(str(tmp_path),))["curuyen"] == []
    # Aynı metin PYTHON beslemesinde ÇAPADIR — sınır biçimde değil BESLEMEDE.
    assert codelaw.capa_uyusmasi([("codelaw.py", metin)], py_kokler=(str(tmp_path),),
                                 modul_bicimi=True)["curuyen"] != []


def test_DOSYA_ADI_SEMBOL_SAYILMAZ(tmp_path):
    """KAPSAM SINIRI (3): backtick içindeki `hedef.py` · `x.json` deseni birebir tutturur ama
    dosya adıdır. İlk ölçümde 11 yanlış çürüme tam olarak buradan geldi."""
    _agac(tmp_path, _HEDEF)
    r = codelaw.capa_uyusmasi([("codelaw.py", "artefakt `hedef.json` ve kaynak `hedef.py`")],
                              py_kokler=(str(tmp_path),), modul_bicimi=True)
    assert r["curuyen"] == [] and r["cozulen"] == [], r


def test_KAPSAM_SINIRI_bilinmeyen_modul_CAPA_SAYILMAZ_ve_BEYANLI(tmp_path):
    """BEDEL YASASI — bu tarayıcının NE KAYBETTİĞİ ölçülür ve yazılır.

    KAPSAM SINIRI (2): `modül.sembol` yalnız BACKTICK içinde ve yalnız modülü ADRES DEFTERİNDE
    ÇÖZÜLEN belirteçlerde çapa sayılır. Türkçe düzyazı `r.json()` · `self.ALAN` gibi yüzlerce
    `x.y` belirteci taşır; hepsini çapa saymak `cozulemeyen` kovasını anlamsız gürültüye çevirir
    ve "kaç çapayı ölçemedim" sorusunu okunamaz yapardı.

    KAYIP AÇIK: modül adı YANLIŞ YAZILMIŞ bir `modül.sembol` çapası bu tarayıcıda görünmez —
    prozadan ayırt edilemez. Kaybın kapatıldığı yer `dosya.py::sembol` biçimidir: orada `.py::`
    sözdizimi belirteci çapa OLARAK işaretler ve çözülemeyen hedef ADIYLA sayılır
    (`test_HEDEF_YOKSA_COZULEMEYENE_adiyla_duser`)."""
    _agac(tmp_path, _HEDEF)
    r = codelaw.capa_uyusmasi([("codelaw.py", "ham `r.json()` ve `yok_modul.sembol` düzyazısı")],
                              py_kokler=(str(tmp_path),), modul_bicimi=True)
    assert r["cozulen"] == [] and r["curuyen"] == [] and r["cozulemeyen"] == [], r
    # Sınırın KENDİSİ beyanlı: gerekçe kaynakta yazılı olmalı, yalnız burada değil.
    assert "backtick" in codelaw.capa_uyusmasi.__doc__.lower(), \
        "kapsam sınırı çekirdeğin kendi belgesinde YAZILI DEĞİL — beyansız kapsam sessiz körlüktür"


def test_MEZAR_TASI_isareti_SEMBOL_capasinda_da_muaf(tmp_path):
    """Beyanlı muafiyet ÜÇ dünyada da AYNI işaretle çalışır (`çapa-mezar-taşı`): çürümüş bir
    çapayı KANIT olarak alıntılayan satır bulgu değildir. İkinci bir işaret icat etmek,
    satır dünyasından taşınan dersi sessizce ihlale çevirirdi."""
    _agac(tmp_path, _HEDEF)
    r = _coz(tmp_path, "// hedef.py::silinmis_olan bayatladı  // çapa-mezar-taşı\n")
    assert r["curuyen"] == [] and r["cozulen"] == [] and r["cozulemeyen"] == [], r


# ---------------------------------------------------------------------------
# (c) İKİ BESLEME — TEK ÇEKİRDEK
# ---------------------------------------------------------------------------

def test_IKI_BESLEME_de_AYNI_CEKIRDEKTEN_gecer():
    """TEK-KAYNAK ÇİVİSİ: beyan metinleri ve tsx kaynağı AYNI `capa_uyusmasi` gövdesinden
    geçmeli. Biri çekirdeği atlasaydı kovası boş kalırdı — ve "0 çürüyen" o besleme hakkında
    hiçbir şey söylemezdi."""
    r = codelaw.report()["sembol_capalari"]
    kaynaklar = {c["kaynak"] for c in r["cozulen"]}
    assert any(k.endswith((".ts", ".tsx")) for k in kaynaklar), f"tsx beslemesi BOŞ: {r['besleme']}"
    assert any(k.startswith("DECLARED_") for k in kaynaklar), \
        f"beyan beslemesi BOŞ: {r['besleme']}"
    assert r["besleme"]["beyan"] > 0 and r["besleme"]["tsx"] > 0, r["besleme"]


def test_CANLI_TARAMA_SESSIZCE_BOS_DEGIL():
    """POZİTİF KONTROL: canlı ağaçta tarayıcı gerçekten sembol çapası BULUYOR. Yanlış kök ya da
    yanlış uzantı süzgeci sıfır dosya döner ve "0 çürüyen" ebediyen yeşil kalırdı."""
    r = codelaw.report()["sembol_capalari"]
    assert len(r["cozulen"]) >= CANLI_ASGARI_COZULEN, \
        f"yalnız {len(r['cozulen'])} sembol çapası çözüldü (asgari {CANLI_ASGARI_COZULEN})"


def test_CANLI_AGACTA_CURUYEN_SIFIR():
    """YASANIN CANLI HÜKMÜ: sembol çapası çürüdüyse ADI vardır ve düzeltmesi mekaniktir —
    burada taban YOKTUR (satır dünyasının çırçırı oraya aittir, buraya değil)."""
    r = codelaw.report()["sembol_capalari"]
    assert r["curuyen"] == [], (
        f"{len(r['curuyen'])} sembol çapası ÇÜRÜDÜ — sembol silindi ya da adı değişti. Doğru tepki "
        f"çapayı silmek değil bugünkü adı yazmaktır: {[c['capa'] for c in r['curuyen'][:5]]}")


# ---------------------------------------------------------------------------
# (d) RAPOR YÜZEYİ — YASA 6 + UYDURMA YASAĞI
# ---------------------------------------------------------------------------

def test_report_SENTETIK_KOKTE_ALANI_UYDURMAZ(tmp_path):
    """Ölçülmeyen alan `None`dır, boş sözlük DEĞİL: "baktım, temiz" ile "bakmadım" aynı alandan
    okunamaz (v314'ün tsx alanlarındaki disiplinin aynısı)."""
    r = codelaw.report(str(tmp_path))
    assert r["sembol_capalari"] is None and r["sembol_capa_curume"] is None, r


def test_CURUME_report_OKUNU_DUSURUR(tmp_path, monkeypatch):
    """ÇİVİNİN ASIL ÖLÇÜMÜ — TEK DEĞİŞKENLİ DENEY: aynı ağaç, tek değişen çapa. Sayıyı rapora
    yazıp `ok`a bağlamamak, yasayı çivi değil süs yapardı.

    `stale_claims` YALITILIR: o terim sentetik ağaçta HER ZAMAN doludur (depo sabitlerindeki
    beyanlar boş ağaçta doğrulanamaz), yalıtılmasaydı `ok` ikisinde de False çıkar ve deney
    sembol çapası hakkında hiçbir şey ölçmezdi (v314'ün aynı gerekçesi).

    `yorum_sembol_capalari` (üçüncü besleme, AŞAMA 2 — TSK-129, 2026-09-04) AYNI GEREKÇEYLE
    YALITILIR: `_yorum_sembol_capalari` metin köklerini HER ZAMAN gerçek `("meridian","tests")`e
    sabitler (`report()`'a bu sentetik `root` geçirilmez — yapısal sınır, fonksiyonun kendi
    docstring'inde yazılı); yalıtılmasaydı gerçek repo metni sentetik `hedef.py` adres defterine
    karşı çözülür, spurious curuyen üretir ve deney yine sembol çapası DIŞINDA bir şey ölçerdi."""
    codelaw.UNSCANNED.clear()
    monkeypatch.setattr(codelaw, "stale_claims", lambda *a, **k: [])
    monkeypatch.setattr(codelaw, "_yorum_sembol_capalari",
                        lambda **kw: {"taranan_dosya": 0, "capa_n": 0, "curuyen": []})
    _agac(tmp_path, _HEDEF)
    (tmp_path / "Saglam.tsx").write_text("// hedef.py::var_olan\n", encoding="utf-8")
    r = codelaw.report(str(tmp_path), tsx_kok=str(tmp_path))
    assert [c["sembol"] for c in r["sembol_capalari"]["cozulen"]] == ["var_olan"], r["sembol_capalari"]
    assert r["sembol_capa_curume"] is False and r["ok"] is True, r
    (tmp_path / "Curuk.tsx").write_text("// hedef.py::silinmis_olan\n", encoding="utf-8")
    r = codelaw.report(str(tmp_path), tsx_kok=str(tmp_path))
    assert r["sembol_capa_curume"] is True and r["ok"] is False, r


def test_report_ALANLARININ_OKUYUCUSU_VAR():
    """YASA 6: rapora yazılan her alanın okuyucusu bu dosyadır — ve üç kova da adıyla okunur."""
    r = codelaw.report()
    s = r["sembol_capalari"]
    assert set(s) == {"cozulen", "curuyen", "cozulemeyen", "besleme"}, sorted(s)
    assert r["sembol_capa_curume"] is False
    assert set(s["besleme"]) == {"beyan", "tsx"}, s["besleme"]

