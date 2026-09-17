"""v518 — TSK-206: codelaw taraması `ops/`u kapsar (2026-09-17).

ÖLÇÜLEN DURUM (Rol-1 ölçümü + bu turun yeniden ölçümü, 2026-09-17): Yasa 4 ve Yasa 6 tarayıcılarının
HEPSİ yalnız `meridian` kökünü tarıyordu. `ops/` (44 dosya) için "mekanik" etiketi doğru değildi:
  * Yasa 4 — 19 işaretsiz yakalayıcı (13 dosya); ≥7'si gerekçeyi `# sessiz-yutma DEĞİL:` biçiminde
    yazmıştı ve `MARKER_RE` o biçimi TANIMAZ.
  * Yasa 6 — `DECLARED_SINKS`in 44 girdisinin 6'sının yazarı taramada görünmüyordu (4 ops brifing
    damgası + `auth.json` + `litestream.env`) ve bu altı beyan NE doğrulanıyor NE borç defterinde
    (`unverifiable_claims`) NE çürük sayılıyordu: SESSİZ BEYAN. Desen beyanı ise aynı durumu
    `orphan_patterns`/`desen_kodda_yok` ile KIRIYORDU — asimetri EDG-101 desenini beyansız bıraktı.

Numara v518: Rol-1 rezervi (ana checkout + worktree'lerde çakışma yok, ölçüldü 2026-09-17).

ÇİVİLER
  K0. Ölçülen modül BU ağacın modülüdür (worktree PYTHONPATH tuzağı).
  1.  Varsayılan tarama `ops/`u içerir — Yasa 4 (`silent_handlers`) ve Yasa 6 (`artifact_graph`) ayrı.
  2.  `silent_handlers()` boş (19 kalem kapandı) + sentetik iki köklü ağaçta ops tarafındaki işaretsiz
      yakalayıcı YAKALANIR (pozitif kontrol).
  3.  Sinyalsiz yakalayıcının penceresinde `sessiz-yutma DEĞİL` biçimi 0 (tarama çivisi) + pozitif kontrol.
  4.  `meridian` kökü DEĞİŞMEZLİĞİ: demet sonucunun meridian dosyalı kesiti `artifact_graph("meridian")`
      ile birebir; sabit tablosunda önceki kökün kararı korunur.
  5.  Sessiz beyan 0 (canlı) + sentetik ağaçta yazarı görünmeyen, borç defterinde olmayan beyan ÇÜRÜK
      sayılır; borç defterine (`UNVERIFIABLE_SINKS`) nedeniyle girince sayılmaz; yazarı görünür olunca
      borç kaydı çürür.
  6.  `*/edg101_*.jsonl` desen beyanı kodda karşılanır (yalnız `soul_denetimi.py`), `orphan_patterns` boş.
  7.  Taban adı çakışması 0; sentetik iki kökte aynı ad → yakalanır ve `report()` ok'u düşer.
  8.  `str` kök imzası geriye uyumlu: tek dizge kök, tek elemanlı demetle AYNI sonucu verir.
  9.  Çapa taramasında kök TEKİLLEŞİR: `ops` hem üretim hem ek çapa kökünde — adres defterinde çift yol yok.
"""
from __future__ import annotations

import pathlib
import textwrap

from meridian import codelaw

KOK = pathlib.Path(__file__).resolve().parent.parent


def _meridian_adlari() -> set[str]:
    return {f.name for f in codelaw._py_files("meridian")}


# ================================================================================================
# K0 — ölçülen modül bu ağacın modülü
# ================================================================================================

def test_K0_olculen_codelaw_BU_agacin_modulu():
    assert pathlib.Path(codelaw.__file__).resolve().parent.parent == KOK, codelaw.__file__


# ================================================================================================
# 1 — varsayılan tarama `ops/`u içerir
# ================================================================================================

def test_1_uretim_kokleri_TEK_kaynak_ve_varsayilan():
    assert codelaw.URETIM_KOKLERI == ("meridian", "ops")
    dosyalar = [str(f) for f in codelaw._py_files(codelaw.URETIM_KOKLERI)]
    assert any(d.startswith("meridian/") for d in dosyalar)
    assert any(d.startswith("ops/") for d in dosyalar), "üretim demeti ops dosyası üretmiyor"


def test_1a_YASA4_varsayilan_taramasi_ops_dosyalarini_gorur():
    isaretli = codelaw.silent_handlers(include_annotated=True)
    assert any(h["file"].startswith("ops/") for h in isaretli), \
        "varsayılan Yasa 4 taraması ops/ yakalayıcılarını görmüyor"
    assert any(h["file"].startswith("ops/") for h in codelaw.annotated_handlers())


def test_1b_YASA6_varsayilan_grafi_ops_yazimlarini_gorur():
    g = codelaw.artifact_graph()
    assert "bekci_brifingi.py" in g["artifacts"]["bekci_brifingi_damga.json"]["writers"], \
        "varsayılan Yasa 6 grafı ops/ yazımını görmüyor"
    assert any(u["file"].startswith("ops/") for u in g["unresolved"]), \
        "ops/ çözülemeyen çağrıları sayılmıyor"


# ================================================================================================
# 2 — Yasa 4: ops/ temiz + pozitif kontrol
# ================================================================================================

def test_2_uretim_koklerinde_isaretsiz_sessiz_yakalayici_YOK():
    kalan = codelaw.silent_handlers()
    assert kalan == [], "işaretsiz sessiz yakalayıcı: " + "; ".join(
        f"{h['file']}:{h['line']} ({h['function']})" for h in kalan)


def test_2a_iki_koklu_sentetik_agacta_ops_tarafi_YAKALANIR(tmp_path):
    (tmp_path / "meridian").mkdir()
    (tmp_path / "ops").mkdir()
    (tmp_path / "meridian" / "temiz.py").write_text("x = 1\n", encoding="utf-8")
    (tmp_path / "ops" / "betik.py").write_text(textwrap.dedent("""
        def f(p):
            try:
                return int(p)
            except ValueError:
                return None
    """), encoding="utf-8")
    kokler = (str(tmp_path / "meridian"), str(tmp_path / "ops"))
    hits = codelaw.silent_handlers(kokler)
    assert [pathlib.Path(h["file"]).name for h in hits] == ["betik.py"], hits
    assert codelaw.silent_handlers(str(tmp_path / "meridian")) == [], "tek kök ops'u görmemeli"


# ================================================================================================
# 3 — `sessiz-yutma DEĞİL` biçimi sinyalsiz yakalayıcıda 0
# ================================================================================================

_DEGIL = "sessiz-yutma DEĞİL"


def _degil_bicimli(hits: list[dict]) -> list[str]:
    """Sinyalsiz yakalayıcıların (işaretli dâhil) üst satırı + gövdesinde `sessiz-yutma DEĞİL` arar.
    Pencere `codelaw.marker_of` ile AYNI: yakalayıcının üstündeki satırdan gövdenin sonuna."""
    bulunan: list[str] = []
    satir_memo: dict[str, list[str]] = {}
    for h in hits:
        satirlar = satir_memo.setdefault(
            h["file"], pathlib.Path(h["file"]).read_text(encoding="utf-8").splitlines())
        bas = max(1, h["line"] - 1)
        # gövde sonu: bir sonraki daha az girintili, boş olmayan satıra kadar (yaklaşık ama kapsayıcı)
        girinti = len(satirlar[h["line"] - 1]) - len(satirlar[h["line"] - 1].lstrip())
        son = h["line"]
        while son < len(satirlar):
            s = satirlar[son]
            if s.strip() and (len(s) - len(s.lstrip())) <= girinti:
                break
            son += 1
        if any(_DEGIL in satirlar[i - 1] for i in range(bas, son + 1)):
            bulunan.append(f"{h['file']}:{h['line']}")
    return bulunan


def test_3_sinyalsiz_yakalayicida_DEGIL_bicimi_YOK():
    hits = codelaw.silent_handlers(include_annotated=True)
    assert hits, "tarama boş — çivi kör"
    assert _degil_bicimli(hits) == [], (
        "`# sessiz-yutma DEĞİL:` MARKER_RE'ye uymaz; sinyalsiz yakalayıcıda bu biçim işaret SAYILMAZ")


def test_3a_DEGIL_bicimi_pozitif_kontrol(tmp_path):
    (tmp_path / "s.py").write_text(textwrap.dedent("""
        def f(p):
            try:
                return int(p)
            except ValueError:  # sessiz-yutma DEĞİL: çağıran None'ı ölçülemedi okur
                return None
    """), encoding="utf-8")
    hits = codelaw.silent_handlers(str(tmp_path), include_annotated=True)
    assert len(hits) == 1 and hits[0]["marker"] is None and hits[0]["bare_marker"] is True, hits
    assert len(_degil_bicimli(hits)) == 1


# ================================================================================================
# 4 — meridian kökü DEĞİŞMEZLİĞİ
# ================================================================================================

def _kesit(info: dict, adlar: set[str]) -> dict:
    def _yer(liste):
        return [s for s in liste if s.rsplit(":", 1)[0] in adlar]
    return {"writers": [m for m in info["writers"] if m in adlar],
            "readers": [m for m in info["readers"] if m in adlar],
            "writer_sites": _yer(info["writer_sites"]),
            "reader_sites": _yer(info["reader_sites"])}


def test_4_demetin_meridian_kesiti_meridian_koku_ile_BIREBIR():
    g_m = codelaw.artifact_graph("meridian")
    g_d = codelaw.artifact_graph()
    adlar = _meridian_adlari()
    for ad, info in g_m["artifacts"].items():
        assert ad in g_d["artifacts"], f"{ad} demet grafında kayboldu"
        assert _kesit(g_d["artifacts"][ad], adlar) == _kesit(info, adlar), ad
    for ad in set(g_d["artifacts"]) - set(g_m["artifacts"]):
        bos = {"writers": [], "readers": [], "writer_sites": [], "reader_sites": []}
        assert _kesit(g_d["artifacts"][ad], adlar) == bos, \
            f"{ad}: demette meridian dosyası YENİ bir ad çözdü — sabit tablosu sızdı"
    assert [u for u in g_d["unresolved"] if u["file"].startswith("meridian/")] == g_m["unresolved"]
    for desen, yerler in g_m["declared_patterns"].items():
        assert [y for y in g_d["declared_patterns"].get(desen, [])
                if y.rsplit(":", 1)[0] in adlar] == yerler, desen
    # HÜKÜM DEMETTEDİR: `meridian` tek başına KISMİ görünümdür. Orada doğan her ihlal, dış okuyucusu
    # YALNIZ ops/'ta olan bir artefakt olmalı (ölçülen: `monotonic_amnesty.json`, TSK-206'da beyanı
    # kalktı) — başka sebepli bir meridian-kök ihlali değişmezliğin bozulduğunu gösterir.
    assert g_d["violations"] == [] and g_d["stale_sinks"] == []
    for ad in g_m["violations"]:
        dis = set(g_d["artifacts"][ad]["external_readers"])
        assert dis and not (dis & adlar), f"{ad}: meridian-kök ihlali ops okuyucusuyla açıklanmıyor"


def test_4a_sabit_tablosu_ONCEKI_kokun_kararini_korur():
    gm = codelaw._global_consts("meridian")
    gd = codelaw._global_consts(codelaw.URETIM_KOKLERI)
    ezilen = {k: (v, gd.get(k)) for k, v in gm.items() if gd.get(k) != v}
    assert ezilen == {}, f"ops sabiti meridian çözümünü ezdi/düşürdü: {ezilen}"
    # meridian içinde çakışıp DÜŞÜRÜLMÜŞ ad (ölçülen: `DEFTER`) ops'tan yeniden CANLANMAZ
    assert "DEFTER" not in gm and "DEFTER" not in gd


def test_4b_sabit_onceligi_sentetik(tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    a.mkdir()
    b.mkdir()
    (a / "m1.py").write_text('ORTAK = "a.json"\nCIFT = "x.json"\n', encoding="utf-8")
    (a / "m2.py").write_text('CIFT = "y.json"\n', encoding="utf-8")
    (b / "b1.py").write_text('ORTAK = "b.json"\nCIFT = "z.json"\nYALNIZ_B = "c.json"\n',
                             encoding="utf-8")
    g = codelaw._global_consts((str(a), str(b)))
    assert g == {"ORTAK": "a.json", "YALNIZ_B": "c.json"}, g
    # düz birleşme (öncelik YOK) `ORTAK`ı düşürürdü — kuralın ısırdığı dal budur
    assert codelaw._global_consts(str(b)) == {"ORTAK": "b.json", "CIFT": "z.json", "YALNIZ_B": "c.json"}


# ================================================================================================
# 5 — sessiz beyan
# ================================================================================================

def _sessiz(kayitlar: list[dict]) -> list[str]:
    return [c["artifact"] for c in kayitlar
            if any(str(r).startswith("sessiz_beyan") for r in c.get("stale_reasons") or [])]


def test_5_canli_agacta_SESSIZ_BEYAN_YOK():
    assert _sessiz(codelaw.declared_claims()) == []
    r = codelaw.report()
    assert r["sessiz_beyanlar"] == [], r["sessiz_beyanlar"]


def test_5a_dort_ops_damgasi_DOGRULANIR_iki_sink_BORC_DEFTERINDE():
    g = codelaw.artifact_graph()
    for dosya in ("bekci_brifingi_damga.json", "karne_brifingi_damga.json",
                  "oneri_brifingi_damga.json", "sef_brifingi_damga.json"):
        assert g["artifacts"][dosya]["writers"], f"{dosya} yazarı hâlâ görünmüyor"
        assert dosya in g["declared_sinks"], dosya
    borc = {u["artifact"]: u for u in codelaw.unverifiable_claims()}
    for dosya in ("auth.json", "litestream.env"):
        assert dosya in borc and borc[dosya]["kind"] == "sink" and borc[dosya]["neden"], borc.get(dosya)
    assert set(codelaw.UNVERIFIABLE_SINKS) <= set(codelaw.DECLARED_SINKS), \
        "borç kaydı beyansız bir ada işaret ediyor"
    for ad, neden in codelaw.UNVERIFIABLE_SINKS.items():
        assert len(neden) >= 30, f"{ad}: sınanamazlık nedeni bir cümle bile değil"


def test_5b_sentetik_SESSIZ_BEYAN_yakalanir_borc_defteri_onu_ADLANDIRIR(tmp_path):
    (tmp_path / "yazar.py").write_text(
        "from . import store\n"
        "def f():\n"
        "    store.write_json('gorunen.json', {})\n", encoding="utf-8")
    beyan = {"gorunen.json": "yazarı görünür, okuyucusu aynı modül — doğrulanır",
             "hayalet.json": "yazarı store dışından yazar — statik graf göremez"}
    curuk = codelaw.stale_claims(str(tmp_path), declared=beyan)
    assert _sessiz(curuk) == ["hayalet.json"], curuk
    # borç defterine NEDENİYLE girince sessiz değildir, borçtur
    borclu = codelaw.declared_claims(str(tmp_path), declared=beyan,
                                     sinanamaz={"hayalet.json": "yazım store dışı dosya erişimi"})
    kayit = {c["artifact"]: c for c in borclu}
    assert kayit["hayalet.json"]["stale_claim"] is False, kayit["hayalet.json"]
    assert kayit["hayalet.json"]["unverifiable"] == "yazım store dışı dosya erişimi"
    # yazarı GÖRÜNÜR bir ada borç kaydı: kayıt BAYATTIR (beyan işi bitince kalmaz)
    bayat = codelaw.stale_claims(str(tmp_path), declared=beyan,
                                 sinanamaz={"gorunen.json": "artık doğru değil",
                                            "hayalet.json": "yazım store dışı"})
    assert [c["artifact"] for c in bayat] == ["gorunen.json"], bayat
    assert any("yazar_gorunur" in r for r in bayat[0]["stale_reasons"]), bayat[0]


def test_5c_human_kaydinda_da_sessiz_beyan_yakalanir(tmp_path):
    (tmp_path / "okur.py").write_text("x = 1\n", encoding="utf-8")
    curuk = codelaw.stale_claims(str(tmp_path), declared={}, patterns={},
                                 human={"hayalet.jsonl": {"cli": "meridian.okur --karne"}})
    assert "hayalet.jsonl" in _sessiz(curuk), curuk


# ================================================================================================
# 6 — EDG-101 desen beyanı
# ================================================================================================

def test_6_edg101_deseni_kodda_KARSILANIR_ve_dar():
    g = codelaw.artifact_graph()
    yerler = g["declared_patterns"].get("*/edg101_*.jsonl", [])
    assert yerler and {y.rsplit(":", 1)[0] for y in yerler} == {"soul_denetimi.py"}, (
        f"desen çağrı yerleri yalnız soul_denetimi olmalı (ikinci yazar beyanın altına sessizce "
        f"girer): {yerler}")
    assert g["orphan_patterns"] == [], g["orphan_patterns"]
    spec = codelaw.DECLARED_SINK_PATTERNS["*/edg101_*.jsonl"]
    assert {"sinif", "gerekce", "sinanamaz"} <= set(spec)
    for kanit in ("MERIDIAN_EDG101_YAKALAMA_DIZIN", "EDG-2026-101", "KALDIRILMALI"):
        assert kanit in spec["gerekce"] + spec["sinanamaz"], kanit
    assert "*/edg101_*.jsonl" in codelaw.report()["unverifiable_claims"]


# ================================================================================================
# 7 — taban adı çakışması
# ================================================================================================

def test_7_uretim_koklerinde_TABAN_ADI_CAKISMASI_YOK():
    cakisma = codelaw.modul_adi_cakismalari()
    assert cakisma == {}, f"iki modül tek modül sayılır (modül kimliği taban adıdır): {cakisma}"
    assert codelaw.report()["modul_adi_cakismasi"] == {}


def test_7a_sentetik_iki_kokte_ayni_ad_YAKALANIR(tmp_path, monkeypatch):
    a, b = tmp_path / "a", tmp_path / "b"
    a.mkdir()
    b.mkdir()
    for d in (a, b):
        (d / "ayni.py").write_text("x = 1\n", encoding="utf-8")
        (d / "__init__.py").write_text("", encoding="utf-8")
    kokler = (str(a), str(b))
    cakisma = codelaw.modul_adi_cakismalari(kokler)
    assert list(cakisma) == ["ayni.py"] and len(cakisma["ayni.py"]) == 2, cakisma
    codelaw.UNSCANNED.clear()
    monkeypatch.setattr(codelaw, "stale_claims", lambda *a_, **k_: [])
    r = codelaw.report(kokler)
    assert r["modul_adi_cakismasi"] == cakisma and r["ok"] is False, r
    (b / "ayni.py").rename(b / "farkli.py")
    r = codelaw.report(kokler)
    assert r["modul_adi_cakismasi"] == {} and r["ok"] is True, r


# ================================================================================================
# 8 — str kök imzası geriye uyumlu
# ================================================================================================

def test_8_str_kok_tek_elemanli_demetle_AYNI(tmp_path):
    (tmp_path / "yazar.py").write_text(
        "from . import store\n"
        "AD = 'rapor.json'\n"
        "def f(p):\n"
        "    store.write_json(AD, {})\n"
        "    try:\n"
        "        return int(p)\n"
        "    except ValueError:\n"
        "        return None\n", encoding="utf-8")
    k = str(tmp_path)
    assert codelaw.artifact_graph(k) == codelaw.artifact_graph((k,))
    assert codelaw.silent_handlers(k) == codelaw.silent_handlers((k,))
    assert [str(f) for f in codelaw._py_files(k)] == [str(f) for f in codelaw._py_files((k,))]
    damga = codelaw._src_stamp(k)
    assert isinstance(damga, tuple) and len(damga) == 2 and damga[0] == 1, damga
    assert codelaw.report(k)["tsx_line_anchors"] is None, "sentetik kök üretim sayıldı"


# ================================================================================================
# 9 — çapa kökleri tekilleşir
# ================================================================================================

def test_9_kok_demeti_TEKILLESIR_ve_capa_adres_defterinde_cift_yol_yok():
    assert codelaw._kokler(("meridian", "ops", "tests", "ops")) == ("meridian", "ops", "tests")
    adres = codelaw._capa_adres_defteri(("meridian", "ops", "tests", "ops"))
    ciftler = {ad: yollar for ad, yollar in adres.items() if len(set(yollar)) != len(yollar)}
    assert ciftler == {}, f"aynı dosya adres defterinde iki kez — çapa `ikircikli` sayılır: {ciftler}"


def test_9b_ayni_kok_iki_kez_verilse_de_capa_TEK_sayilir(tmp_path):
    (tmp_path / "hedef.py").write_text("x = 1\n", encoding="utf-8")
    (tmp_path / "beyan.py").write_text('S = "hedef.py:999"\n', encoding="utf-8")  # çapa-sentetik: tmp_path'e yazılan sentetik fikstür, gerçek dosya değil (TSK-206)
    k = str(tmp_path)
    tek = codelaw.stale_line_anchors(k)
    assert [c["neden"] for c in tek] == ["menzil_disi"], tek
    assert codelaw.stale_line_anchors((k, k)) == tek, "aynı kök demette iki kez: çapa iki kez sayıldı"
    assert codelaw.stale_line_anchors(k, ek_kokler=(k,)) == tek, "ek kök üretim köküyle çakıştı: çift sayım"


def test_9a_capa_sayimi_TARIHI_kok_kumesiyle_AYNI():
    """ÖNCE/SONRA: çapa dünyası tarihsel olarak `meridian` + `_EK_CAPA_KOKLERI` (= tests, ops) idi.
    Üretim demeti `ops`u zaten taşıdığı için `report()` onu İKİ kez gezmemeli — sayım aynı kalır."""
    tarihi: list[dict] = []
    codelaw.stale_line_anchors(("meridian", "tests", "ops"), cozulemeyen_out=tarihi)
    ciftli: list[dict] = []
    codelaw.stale_line_anchors(codelaw.URETIM_KOKLERI, cozulemeyen_out=ciftli,
                               ek_kokler=codelaw._EK_CAPA_KOKLERI)
    r = codelaw.report()
    assert len(r["line_anchor_unresolved"]) == len(tarihi) == len(ciftli), (
        len(r["line_anchor_unresolved"]), len(tarihi), len(ciftli))
    assert sorted(map(str, r["line_anchor_unresolved"])) == sorted(map(str, tarihi))
