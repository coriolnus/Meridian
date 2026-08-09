"""test_codelaw_kor_nokta_v214.py — BEKÇİNİN KENDİ KÖRLÜĞÜ (2026-08-08).

Denetim (docs/ARTEFAKT-TARAMASI-2026-08-07) iki kusur bildirdi. Bu dosya ikisini de ÖLÇÜYLE
çiviler ve birinin gerekçesini DÜZELTİR:

  B-2 · İDDİA: `_store().read_json(...)` deseni grafikte "HİÇ görünmüyor" (9 çağrı yeri).
        ÖLÇÜM: bu YANLIŞ. O çağrıların AST şekli `Attribute(value=Call(...))`tir ve eski filtre
        yalnız `isinstance(n.func, ast.Attribute)` diye sorup TABANA hiç bakmıyordu — dokuzu da
        çözülüyordu. `test_dokuz_store_cagrisi_grafikte_gorunuyor` bunu dosya+satır düzeyinde
        kanıtlar; bulgunun kaydı böylece dürüstleşir.
        ASIL KUSUR (ve bulgunun doğru çekirdeği): tarayıcı ÇÖZEMEDİĞİNİ SAYMIYORDU. Ölçülen iki
        sınıf hiçbir sayaca girmiyordu — çıplak-ad çağrısı ve konumsal-argümansız çağrı.

  B-4 · `sieve.json` muafiyeti BAYATTI ve `stale_sinks` bunu YAPISAL olarak göremez (tetikleyicisi
        `unread`, okuma ise yazarla aynı modülde). Kapama: `declared_claims()`.

Her sıfır iddiasının yanında bir POZİTİF KONTROL var (test_codelaw_v59'un disiplini): sentetik
bir çözülmez desen ve sentetik bir bayat beyan verilir, tarayıcının yakalaması beklenir.
"""
from __future__ import annotations

import ast
import pathlib

from meridian import codelaw

REPO = pathlib.Path(__file__).resolve().parents[1]

#: Denetimin B-2'de saydığı dokuz çağrı yeri — dosya, satır, rol.
DOKUZ_CAGRI = [
    ("insider.py", 281, "reader"), ("insider.py", 637, "writer"),
    ("shortinterest.py", 210, "reader"), ("shortinterest.py", 353, "reader"),
    ("shortinterest.py", 392, "reader"),
    ("massive.py", 555, "reader"), ("massive.py", 564, "writer"),
    ("massive.py", 632, "reader"), ("massive.py", 856, "writer"),
]


# ---------------------------------------------------------------------------
# B-2 (1) — DOKUZ ÇAĞRININ ÖLÇÜLEN AST BİÇİMİ
# ---------------------------------------------------------------------------

def test_dokuz_cagrinin_ast_bicimi_olculdu_taban_bir_CAGRIDIR():
    """Biçim varsayılmaz, ÖLÇÜLÜR: `Call(func=Attribute(value=Call(Name('_store')), attr=...))`.
    Bu test bir gün kırılırsa çağrı yeri değişmiştir ve B-2'nin kaydı yeniden ölçülmelidir."""
    hedef: dict[str, set[int]] = {}
    for dosya, satir, _rol in DOKUZ_CAGRI:
        hedef.setdefault(dosya, set()).add(satir)

    gorulen = 0
    for dosya, satirlar in hedef.items():
        p = REPO / "meridian" / "adapters" / dosya
        tree = ast.parse(p.read_text())
        for n in ast.walk(tree):
            if not (isinstance(n, ast.Call) and n.lineno in satirlar
                    and isinstance(n.func, ast.Attribute)
                    and n.func.attr in (codelaw.READ_CALLS | codelaw.WRITE_CALLS)):
                continue
            gorulen += 1
            assert isinstance(n.func.value, ast.Call), \
                f"{dosya}:{n.lineno} taban artık bir çağrı değil: {type(n.func.value).__name__}"
            assert isinstance(n.func.value.func, ast.Name) and n.func.value.func.id == "_store"
            assert isinstance(n.args[0], ast.Name), "ad modül sabiti olarak geçmiyor"
    assert gorulen == len(DOKUZ_CAGRI), f"9 çağrının {gorulen}'i bulundu"


def test_dokuz_store_cagrisi_grafikte_gorunuyor_dosya_ve_satir_duzeyinde():
    """B-2'nin ÖLÇÜLMÜŞ HÜKMÜ: bu dokuz çağrı grafikte GÖRÜNÜYOR (bulgu 'hiç görünmüyor' diyordu).
    `massive_verify.json` bir EMNİYET ANAHTARIDIR; yazarı ve okuyucusu haritada olmak zorundadır."""
    g = codelaw.artifact_graph()
    yerler: set[str] = set()
    for info in g["artifacts"].values():
        yerler |= set(info["writer_sites"]) | set(info["reader_sites"])

    eksik = [f"{d}:{s}" for d, s, _ in DOKUZ_CAGRI if f"{d}:{s}" not in yerler]
    assert not eksik, f"grafikte görünmeyen `_store()` çağrısı: {eksik}"

    for d, s, rol in DOKUZ_CAGRI:
        anahtar = "writer_sites" if rol == "writer" else "reader_sites"
        assert any(f"{d}:{s}" in info[anahtar] for info in g["artifacts"].values()), \
            f"{d}:{s} yanlış rolde görünüyor"

    ev = g["artifacts"]["massive_verify.json"]
    assert ev["writer_sites"] == ["massive.py:856"] and ev["reader_sites"] == ["massive.py:632"]


def test_erisim_deseni_sayimi_store_cagri_bicimini_ADIYLA_raporlar():
    """"Hepsini görüyorum" ölçülmeden iddia edilemez: hangi TABAN biçiminden kaç tane görüldüğü
    rapora çıkar. `cagri:_store()` kovası B-2'nin desenidir ve dokuz çağrıyı taşır."""
    g = codelaw.artifact_graph()
    desenler = g["access_patterns"]
    assert desenler.get("cagri:_store()") == len(DOKUZ_CAGRI), desenler
    assert desenler.get("ad:store", 0) > 100, "kanonik `store.` deseni kaybolmuş"
    assert codelaw.report()["store_access_patterns"] == desenler


# ---------------------------------------------------------------------------
# B-2 (3) — META-DÜZELTME: TARAYICI GÖREMEDİĞİNİ SAYAR
# ---------------------------------------------------------------------------

def test_ciplak_ad_cagrisi_ARTIK_sayiliyor(tmp_path):
    """ÖLÇÜLEN GERÇEK KÖR SINIF: `from .store import read_json` sonrası `read_json(ad)`.
    Eski filtre `isinstance(n.func, ast.Attribute)` dediği için bu çağrı ne artefakta, ne
    `unresolved`a, ne `UNSCANNED`e düşüyordu — HİÇBİR SAYAÇTA yoktu."""
    (tmp_path / "ciplak.py").write_text(
        "from .store import read_json, write_json\n"
        "def f(ad):\n"
        "    write_json(ad, {})\n"
        "    return read_json('gercek.json', {})\n")
    g = codelaw.artifact_graph(str(tmp_path))

    assert g["access_patterns"].get("ciplak_ad") == 2, g["access_patterns"]
    # literal adlı çıplak çağrı ARTEFAKT olarak görülür
    assert "gercek.json" in g["artifacts"]
    # değişken adlı olan SESSİZCE ATLANMAZ: adlandırılmış kovaya düşer
    coz = [u for u in g["unresolved"] if u["base"] == "ciplak_ad"]
    assert len(coz) == 1 and coz[0]["reason"] == "ad_cozulemedi", coz


def test_konumsal_argumansiz_cagri_sessizce_atlanmaz(tmp_path):
    """`store.write_json(name=...)` — `n.args` boş olduğu için eski filtreden SESSİZCE düşerdi.
    Bugün canlıda 0 örnek var; sıfır örnek 'kapı kapalı' demek DEĞİLDİR, bu yüzden sentetik."""
    (tmp_path / "kwonly.py").write_text(
        "from . import store\n"
        "def f():\n"
        "    store.write_json(name='x.json', data={})\n"
        "    store.read_json()\n")
    g = codelaw.artifact_graph(str(tmp_path))
    kova = [u for u in g["unresolved"] if u["reason"] == "konumsal_arg_yok"]
    assert len(kova) == 2, g["unresolved"]
    assert {u["role"] for u in kova} == {"reader", "writer"}
    assert g["unresolved_by_reason"]["konumsal_arg_yok"] == 2


def test_her_unresolved_kaydinin_ADI_VAR_ve_kovalar_sayiliyor(tmp_path):
    """META-KURAL: çözülemeyen HER desen adlandırılmış bir kovaya düşer ve sayılır. "Sessizce
    görünmez" sınıfı yapısal olarak kapalıdır."""
    (tmp_path / "karisik.py").write_text(
        "from . import store\n"
        "AD = 'iyi.json'\n"
        "SAYI = 'bu_bir_artefakt_degil.txt'\n"
        "def f(x, i):\n"
        "    store.write_json(AD, {})\n"
        "    store.write_json(x, {})\n"                     # ad_cozulemedi (Name)
        "    store.read_json(f'p_{i}.json', {})\n"          # ad_cozulemedi (JoinedStr)
        "    store.read_json(SAYI, {})\n"                   # artefakt_adi_degil
        "    store.write_json()\n")                         # konumsal_arg_yok
    g = codelaw.artifact_graph(str(tmp_path))

    assert set(g["unresolved_by_reason"]) == set(codelaw.UNRESOLVED_REASONS)
    assert g["unresolved_by_reason"] == {"ad_cozulemedi": 2, "artefakt_adi_degil": 1,
                                         "konumsal_arg_yok": 1, "desen_beyanli": 0}
    assert sum(g["unresolved_by_reason"].values()) == len(g["unresolved"])
    for u in g["unresolved"]:
        assert u["reason"] in codelaw.UNRESOLVED_REASONS
        assert u["base"] and u["arg_kind"] and u["line"] > 0
    assert list(g["artifacts"]) == ["iyi.json"]


def test_cozulemeyen_cagri_sekli_de_adlandirilir():
    """Ad bile çözülemeyen bir çağrı şekli (Subscript/lambda) `_callee` tarafından ADLANDIRILIR —
    `None` dönmek yetmez, biçimin adı raporlanabilir olmalı."""
    n = ast.parse("tools['fn'](1)").body[0].value
    ad, desen = codelaw._callee(n)
    assert ad is None and desen == "cozulemeyen_sekil:Subscript"


def test_canli_taramada_kor_sinif_kalmadi():
    """Canlı ağaçta her `store` erişimi ya artefakta ya adlandırılmış kovaya gider; toplamlar tutar."""
    g = codelaw.artifact_graph()
    assert sum(g["unresolved_by_reason"].values()) == len(g["unresolved"])
    assert g["access_patterns"], "erişim deseni sayacı boş — census çalışmıyor"
    # v214 öncesi HİÇ sayılmayan çıplak-ad sınıfı artık sayıda
    assert g["access_patterns"].get("ciplak_ad", 0) > 0


# ---------------------------------------------------------------------------
# B-4 — SIEVE MUAFİYETİNİN YENİ HÂLİ + YAPISAL DELİĞİN KAPANMASI
# ---------------------------------------------------------------------------

def test_sieve_beyani_artik_GERCEK_zinciri_anlatiyor():
    """Muafiyet duruyor (statik graf hâlâ dış okuyucu göremiyor: tek `store` okuması aynı modülde)
    ama METNİ artık gerçeği söylüyor: `sieve.report()` bir KARAR girdisidir."""
    g = codelaw.DECLARED_SINKS["sieve.json"]
    assert "tek okuyucusu kendi testidir" not in g, "bayat cümle geri gelmiş"
    for kanit in ("sieve.stages", "sieve.report", "api.api_diagnostics", "_terfi_hukmu",
                  "mutation.detector_red", "watchdog.parity_report"):
        assert kanit in g, f"beyan ölçülen zinciri anmıyor: {kanit}"
    assert not any(r.search(g) for r in codelaw.CLAIM_NO_PROD_READER), \
        "yeni metin hâlâ 'üretimde okuyucusu yok' iddiası taşıyor"


def test_sieve_zinciri_KODDA_hala_duruyor():
    """Beyanın dayandığı zincir bir iddia değil, ölçülebilir bir olgu olmalı (YASA 6'nın kendisi).

    SATIR NUMARASINA ÇİVİLENMEZ — bilinçli. Bu tur `api.py`nin oturum ortasında ~189 satır
    kaydığı ÖLÇÜLDÜ (paralel iş kolu); satır numarası çivilemek, kapatmaya çalıştığımız bayat-iddia
    hastalığını teste bulaştırmak olurdu. Sözleşme MODÜL+FONKSİYON düzeyindedir."""
    c = codelaw.declared_claims(declared={"sieve.json": "tek okuyucusu kendi testidir (tests/x.py)"})
    assert c[0]["stale_claim"] is True
    cagiranlar = c[0]["external_accessors"]["sieve.report"]
    moduller = {y.split(":")[0] for y in cagiranlar}
    assert {"api.py", "mutation.py", "watchdog.py"} <= moduller, cagiranlar


def test_YANLIS_MUAFIYET_BEYANI_yakalanir_sentetik(tmp_path):
    """POZİTİF KONTROL — yapısal deliğin kapandığının kanıtı. Sentetik kurulum `sieve.json`un
    BİREBİR deseni: yazan da okuyan da AYNI modül (`unread` True kalır, `stale_sinks` SESSİZ),
    ama okumayı saran fonksiyon DIŞARIDAN çağrılıyor ve beyan "okuyucusu yok" diyor."""
    (tmp_path / "defter.py").write_text(
        "from . import store\n"
        "DOSYA = 'muhasebe.json'\n"
        "def _oku():\n"
        "    return store.read_json(DOSYA, {})\n"
        "def rapor():\n"                       # BİR sıçrama: rapor() -> _oku()
        "    return {'n': len(_oku())}\n"
        "def yaz(d):\n"
        "    store.write_json(DOSYA, d)\n")
    (tmp_path / "karar.py").write_text(
        "from . import defter\n"
        "def hukum():\n"
        "    return 'EVET' if defter.rapor()['n'] else 'HAYIR'\n")

    beyan = {"muhasebe.json": "ŞU AN tek okuyucusu kendi testidir (tests/test_x.py)"}
    g = codelaw.artifact_graph(str(tmp_path))
    # ESKİ dedektör kör: dosya `unread`, muafiyet "geçerli", `stale_sinks` boş.
    assert g["artifacts"]["muhasebe.json"]["unread"] is True
    assert g["artifacts"]["muhasebe.json"]["external_readers"] == []
    assert [k for k in beyan if k in g["artifacts"] and not g["artifacts"][k]["unread"]] == []

    # YENİ dedektör görüyor.
    curuk = codelaw.stale_claims(str(tmp_path), declared=beyan)
    assert len(curuk) == 1, codelaw.declared_claims(str(tmp_path), declared=beyan)
    assert curuk[0]["external_accessors"] == {"defter.rapor": ["karar.py:3"]}


def test_dogru_beyan_yanlis_pozitif_uretmez(tmp_path):
    """Dedektör ihbarcı değil: 'aynı modül → statik graf göremez' bir SINIR TARİFİDİR, iddia
    değil. Dış erişimcisi olsa bile böyle bir beyan çürütülmüş sayılmaz."""
    (tmp_path / "defter.py").write_text(
        "from . import store\n"
        "def rapor():\n"
        "    return store.read_json('muhasebe.json', {})\n"
        "def yaz(d):\n"
        "    store.write_json('muhasebe.json', d)\n")
    (tmp_path / "karar.py").write_text(
        "from . import defter\n"
        "def h():\n"
        "    return defter.rapor()\n")
    beyan = {"muhasebe.json": "okuma aynı modülde (defter.rapor) → statik graf göremez; DIŞ "
                              "tüketici gerçek: karar.h() hükmü buradan besler"}
    c = codelaw.declared_claims(str(tmp_path), declared=beyan)
    assert c[0]["claims_no_prod_reader"] is False
    assert c[0]["stale_claim"] is False
    assert c[0]["external_accessors"] == {"defter.rapor": ["karar.py:3"]}


def test_iddia_dogruysa_curuk_sayilmaz(tmp_path):
    """"Okuyucusu yok" diyen bir beyan, GERÇEKTEN dış çağıranı yoksa ayakta kalır."""
    (tmp_path / "defter.py").write_text(
        "from . import store\n"
        "def _oku():\n"
        "    return store.read_json('yalniz.json', {})\n"
        "def yaz(d):\n"
        "    store.write_json('yalniz.json', d)\n")
    beyan = {"yalniz.json": "ŞU AN tek okuyucusu kendi testidir (tests/test_y.py)"}
    c = codelaw.declared_claims(str(tmp_path), declared=beyan)
    assert c[0]["claims_no_prod_reader"] is True and c[0]["stale_claim"] is False


def test_canli_agacta_curutulmus_muafiyet_beyani_YOK():
    """ASIL YASA (B-4): bir muafiyet, gerçeği örtmek için kullanılamaz. Bu test kırılırsa
    beyanın metni ÇÜRÜMÜŞTÜR — metni gerçeğe göre tazele, testi gevşetme."""
    curuk = codelaw.stale_claims()
    assert curuk == [], "beyanı çürütülmüş muafiyet: " + "; ".join(
        f"{c['artifact']} ← {sorted(c['external_accessors'])}" for c in curuk)


def test_iddia_eden_her_beyan_kayit_altinda():
    """"Üretimde okuyucusu yok" diyen beyanlar SAYILABİLİR olmalı — sessiz bir iddia denetlenemez."""
    hepsi = codelaw.declared_claims()
    assert len([c for c in hepsi if c["kind"] == "sink"]) == len(codelaw.DECLARED_SINKS)
    assert len(hepsi) == (len(codelaw.DECLARED_SINKS) + len(codelaw.DECLARED_SINK_PATTERNS)
                          + len(codelaw.HUMAN_INVOKED_SINKS))
    iddialilar = [c["artifact"] for c in hepsi if c["claims_no_prod_reader"]]
    assert iddialilar == ["insider_signals.json"], iddialilar
    # ve iddiası doğru: bu dosyayı gerçekten HİÇBİR yer okumuyor (yazar bile)
    assert codelaw.artifact_graph()["artifacts"]["insider_signals.json"]["readers"] == []


# ---------------------------------------------------------------------------
# B-5 — DESEN BEYANI: TARİHLİ AD ARTIK SAHİPLENİLEBİLİR (v215)
# ---------------------------------------------------------------------------

def test_desen_koddan_TURETILIR_elle_yazilmaz():
    """Tasarım kararının çivisi: desen anahtarı `ast.JoinedStr`den ÖLÇÜLÜR. Sabit parçalar durur,
    çözülebilen değişken değerine, çözülemeyen `*`a döner."""
    tree = ast.parse("ARCHIVE_DIR = 'intraday_bars'\n"
                     "def f(day):\n"
                     "    store.append_jsonl(f'{ARCHIVE_DIR}/{day}.jsonl', {})\n")
    arg = [n.args[0] for n in ast.walk(tree)
           if isinstance(n, ast.Call) and getattr(n.func, "attr", None) == "append_jsonl"][0]
    consts = codelaw._module_consts(tree)
    assert codelaw._joined_glob(arg, consts, {}) == "intraday_bars/*.jsonl"
    # artefakt uzantısı taşımayan bir f-string desen ÜRETMEZ (gürültü olurdu)
    yok = ast.parse("f'{a}/{b}.txt'").body[0].value
    assert codelaw._joined_glob(yok, {}, {}) is None


def test_intraday_bars_DECLARED_gorunuyor_desen_katmaninda():
    """B-5'in ölçülen hükmü: yazım SÖKÜLMEDİ, beyan katmanı açıldı. Tarihli ad hâlâ ÇÖZÜLEMİYOR
    (artefakt sözlüğüne girmiyor) ama artık SAHİPSİZ değil."""
    g = codelaw.artifact_graph()
    assert g["declared_patterns"] == {"intraday_bars/*.jsonl": ["bararchive.py:111"]}
    assert g["orphan_patterns"] == [], "kodda karşılığı olmayan desen beyanı: ölü muafiyet"

    kayit = [u for u in g["unresolved"] if u["file"].endswith("bararchive.py")]
    assert len(kayit) == 1 and kayit[0]["reason"] == "desen_beyanli"
    assert kayit[0]["pattern"] == "intraday_bars/*.jsonl"
    # AF DEĞİL: ad hâlâ çözülemedi, hâlâ `unresolved`da sayılıyor, artefakt olmadı
    assert not [a for a in g["artifacts"] if a.startswith("intraday_bars")]
    assert sum(g["unresolved_by_reason"].values()) == len(g["unresolved"])


def test_desensiz_tarihli_ad_HALA_yakalaniyor(tmp_path):
    """DESTEĞİN GENEL AF OLMADIĞININ ÇİVİSİ: beyanı olmayan bir tarihli ad `desen_beyanli`ye
    DÜŞMEZ; `ad_cozulemedi` olarak sayılmaya devam eder."""
    (tmp_path / "yeni.py").write_text(
        "from . import store\n"
        "KLASOR = 'yeni_arsiv'\n"
        "def f(gun):\n"
        "    store.append_jsonl(f'{KLASOR}/{gun}.jsonl', {})\n")
    g = codelaw.artifact_graph(str(tmp_path))
    u = g["unresolved"][0]
    assert u["reason"] == "ad_cozulemedi", g["unresolved"]
    assert u["pattern"] == "yeni_arsiv/*.jsonl", "şekil türetildi ama beyan yok — doğru davranış"
    assert g["declared_patterns"] == {}
    assert g["unresolved_by_reason"]["desen_beyanli"] == 0


def test_GELECEK_tuketici_iddiasi_yanlis_pozitif_uretmez():
    """B-5 (3): "Faz-5/6 okuyacak" bugünkü çağrı analiziyle SINANAMAZ. Mekanizma bunu bilir:
    iddiayı test etmeye çalışıp yanlış-pozitif üretmez, ama SESSİZ de kalmaz — adıyla raporlar."""
    kayit = [c for c in codelaw.declared_claims()
             if c["artifact"] == "intraday_bars/*.jsonl"][0]
    assert kayit["kind"] == "pattern"
    assert kayit["stale_claim"] is False, kayit.get("stale_reasons")
    assert kayit["unverifiable"], "sınanamazlık gerekçesi yazılmamış"
    assert "intraday_bars/*.jsonl" in codelaw.report()["unverifiable_claims"]

    spec = codelaw.DECLARED_SINK_PATTERNS["intraday_bars/*.jsonl"]
    for kanit in ("bararchive.py:111", "_retention", "EXE-2026-002"):
        assert kanit in spec["gerekce"], f"beyan ölçülen olguyu anmıyor: {kanit}"
    assert "KALDIRILMALI" in spec["sinanamaz"], "devir şartı yazılmamış"


def test_sinanabilirligini_SOYLEMEYEN_desen_beyani_curuktur():
    """Sessizlik yapısal olarak imkânsız: bir desen beyanı ya sınanabilir bir tüketici (`cli`)
    gösterir ya da NEDEN sınanamadığını yazar. İkisi de yoksa beyan çürüktür."""
    curuk = codelaw.stale_claims(declared={}, human={},
                                 patterns={"intraday_bars/*.jsonl": {"gerekce": "sadece laf"}})
    assert [c["stale_reasons"] for c in curuk] == [["sinanabilirlik_beyan_edilmemis"]]


def test_kodda_karsiligi_kalmayan_desen_beyani_curuktur():
    """`stale_sinks` emsali, desen katmanında: muafiyet işi bitince kalmaz."""
    curuk = codelaw.stale_claims(declared={}, human={},
                                 patterns={"hayalet/*.jsonl": {"gerekce": "x", "sinanamaz": "y"}})
    assert [c["stale_reasons"] for c in curuk] == [["desen_kodda_yok"]]


# ---------------------------------------------------------------------------
# B-7 — "ÇAĞIRANI YOK" ile "ÇAĞIRANI İNSAN" AYRI ŞEYLERDİR (v215)
# ---------------------------------------------------------------------------

def test_shadow_trades_CLI_tuketicisi_olculdu():
    """Zincir ÖLÇÜLDÜ: yazan `shadow_lifecycle`, okuyan `shadow_variants._load_books`, ve o
    okuyucunun TEK çağıranı `main()`in `--karne` kolu — yani bir İNSAN."""
    g = codelaw.artifact_graph()
    info = g["artifacts"]["shadow_trades.jsonl"]
    assert info["writers"] == ["shadow_lifecycle.py"]
    assert info["external_readers"] == ["shadow_variants.py"]
    assert info["unread"] is False, "dış okuyucusu var — DECLARED_SINKS'e ait DEĞİL"

    kayit = [c for c in codelaw.declared_claims()
             if c["artifact"] == "shadow_trades.jsonl"][0]
    assert kayit["kind"] == "human" and kayit["stale_claim"] is False, kayit.get("stale_reasons")
    assert kayit["cli"] == "meridian.shadow_variants --karne"
    # ÜRETİM YOLU YOK: okuyucuyu da CLI girişini de hiçbir `meridian/` modülü çağırmıyor
    assert kayit["external_accessors"] == {"shadow_variants._load_books": [],
                                           "shadow_variants.main": []}
    spec = codelaw.HUMAN_INVOKED_SINKS["shadow_trades.jsonl"]
    assert spec["sinif"] == "cagirani_insan"
    for kanit in ("shadow_lifecycle.py:574", "_load_books", "--karne", "SIFIR YETKİ"):
        assert kanit in spec["gerekce"], f"beyan ölçülen olguyu anmıyor: {kanit}"


def test_CLI_kaldirilirsa_beyan_CURUR_sentetik():
    """POZİTİF KONTROL: "tüketici şu CLI" iddiası fonksiyon/betik düzeyinde sınanır. Bayrak,
    modül ya da `main` bağı düşerse beyan ÇÜRÜR — sessiz kalmaz."""
    for spec, beklenen in (
        ({"cli": "meridian.shadow_variants --yokbayrak"}, "cli_bayragi_yok:--yokbayrak"),
        ({"cli": "meridian.olmayan_modul --karne"}, "cli_modulu_yok:meridian.olmayan_modul"),
        ({"gerekce": "cli alanı hiç yok"}, "cli_beyan_edilmemis"),
    ):
        curuk = codelaw.stale_claims(declared={}, patterns={},
                                     human={"shadow_trades.jsonl": spec})
        assert len(curuk) == 1 and beklenen in curuk[0]["stale_reasons"], (spec, curuk)


def test_okuyucu_main_kolundan_erisilemezse_beyan_curur(tmp_path):
    """"Çağıranı insan" iddiasının çekirdeği: okuyucu CLI girişinden ERİŞİLEBİLİR olmalı.
    Okuma varsa ama `main` ona ulaşmıyorsa iddia yanlıştır."""
    (tmp_path / "yazar.py").write_text(
        "from . import store\n"
        "def yaz(r):\n"
        "    store.append_jsonl('defter.jsonl', r)\n")
    (tmp_path / "okur.py").write_text(
        "from . import store\n"
        "def _yukle():\n"
        "    return store.read_jsonl('defter.jsonl')\n"
        "def main(argv=None):\n"
        "    import argparse\n"
        "    p = argparse.ArgumentParser()\n"
        "    p.add_argument('--karne', action='store_true')\n"
        "    return 0\n")          # <-- main `_yukle`yi ÇAĞIRMIYOR
    curuk = codelaw.stale_claims(str(tmp_path), declared={}, patterns={},
                                 human={"defter.jsonl": {"cli": "meridian.okur --karne"}})
    assert [c["stale_reasons"] for c in curuk] == [["okuyucu_main_kolundan_erisilemiyor"]]


def test_dis_okuyucusu_olmayan_defter_bu_kayda_ait_degil(tmp_path):
    """Kayıtların ayrık olmasının sebebi: `unread` bir defter `DECLARED_SINKS`e aittir. Yanlış
    dosyalanmış beyan sessizce 'geçerli' görünemez."""
    (tmp_path / "tek.py").write_text(
        "from . import store\n"
        "def _yukle():\n"
        "    return store.read_jsonl('defter.jsonl')\n"
        "def yaz(r):\n"
        "    store.append_jsonl('defter.jsonl', r)\n"
        "def main(argv=None):\n"
        "    import argparse\n"
        "    p = argparse.ArgumentParser()\n"
        "    p.add_argument('--karne', action='store_true')\n"
        "    return _yukle()\n")
    curuk = codelaw.stale_claims(str(tmp_path), declared={}, patterns={},
                                 human={"defter.jsonl": {"cli": "meridian.tek --karne"}})
    assert [c["stale_reasons"] for c in curuk] == [["dis_okuyucu_yok_DECLARED_SINKS_e_ait"]]


def test_canli_agacta_hicbir_kayit_curuk_degil():
    """ASIL YASA, üç kayıt için birden: sink · pattern · human."""
    curuk = codelaw.stale_claims()
    assert curuk == [], "çürük beyan: " + "; ".join(
        f"{c['kind']}:{c['artifact']} ← {c.get('stale_reasons') or sorted(c['external_accessors'])}"
        for c in curuk)
    kinds = {c["kind"] for c in codelaw.declared_claims()}
    assert kinds == {"sink", "pattern", "human"}, kinds


# ---------------------------------------------------------------------------
# GERİLEME YOK — YASA-6 GEVŞEMEDİ
# ---------------------------------------------------------------------------

# MUAFİYET TABANI — SAYI-PIN'İN HALEFİ (v219'da BEYANLI kuruldu, 2026-08-09).
#
# ÖNCESİ `len(DECLARED_SINKS) == 36` idi ve o pin YANLIŞ ŞEYİ ölçüyordu. Bir sayı iki zıt olayı
# aynı kırmızıya katlar: (a) yeni bir muafiyet AÇILDI — tartışılması gereken şey, (b) bir muafiyet
# KAPANDI (artefakta gerçek dış okuyucu geldi) — kutlanması gereken şey. W1 turu (a)'yı yaptı ve
# pin, meşru bir beyan yüzünden kırmızıya döndü: bakım maliyeti tam da doğru davranışa biniyordu.
# Daha kötüsü, sayı EŞLENİK bir değişimi (bir muafiyet kapanırken başka biri açılırsa) HİÇ
# görmezdi — 36 = 36 kalır, liste sessizce başkalaşırdı.
#
# HALEF: adlandırılmış TABAN + tek yönlü kıyas. `SINK_TABANI - DECLARED_SINKS` boş olmalıdır, yani
# TABANDAN EKSİLEN her ad bir GERİLEMEDİR ve adıyla rapor edilir. EKLEME ihlal DEĞİLDİR (yeni
# mekanizma yeni lağım getirebilir) ama sessiz de değildir: eklenen ad bu listede DURMADIĞI sürece
# taban ile kod arasındaki fark testin hata mesajında değil, bu satırın DÜZENLENMEMİŞ olmasında
# görünür. v198 `KART_TABANI` deseninin ta kendisi: "değiştirmek serbest, ama bu satırı düzenleyerek".
#
# EKLEMENİN İKİNCİ KAPISI BAŞKA BİR TESTTEDİR ve gevşemedi: `test_codelaw_v59.
# test_her_beyanin_turkce_bir_gerekcesi_var` her muafiyetten >=30 karakterlik Türkçe bir gerekçe
# ister; `test_beyan_edilen_lagimlarin_hepsi_hala_lagim` de bayat muafiyeti (`stale_sinks`) düşürür.
# Yani "bedava muafiyet" yolu bu değişiklikle AÇILMIYOR — kapı yerinde, ölçüsü düzeldi.
#
# v219'DA BEYANLI GÜNCELLENDİ (2026-08-09) — TEK yeni muafiyet, ölçülen 36 → 37:
#   +1 `entity_damga.json` (W1/SB-4, 5df1657) — bayat-sermaye bekçisinin "kitap `store` kapısı
#      DIŞINDAN değişti" damgası. Okuyucusu yazarla AYNI modüldedir (dedektör kendi önceki
#      ölçümünü okur), o yüzden `unread` tetiklenir ve muafiyet beyanı ŞART.
# W3'ün `skill_gorusleri.jsonl` defteri BU LİSTEYE GİRMEDİ ve girmemeliydi: ÖLÇÜLDÜ, dış okuyucusu
# VAR (`api.py:2548`; artifact_graph `unread: False` diyor). Muafiyet listesi bir kaçış yoludur ve
# kapatılabilen yerde kullanılmaz (test_ajan_telemetri_v197'nin aynı hükmü).
SINK_TABANI = frozenset({
    "agent_tooluse.json", "agent_traces.jsonl", "approvals.jsonl", "auth.json",
    "bar_source_seams.json", "bars_fingerprint.json", "bars_source.json", "brain_cooldown.json",
    "composite_budget.json", "entity_damga.json", "fmp_usage.json", "hypothesis_id_hwm.json",
    "inc_cache.json", "insider_signals.json", "insider_trades.json", "integrity_alarmed.json",
    "integrity_audit_log.json", "massive_crosscheck.json", "massive_grouped_last.json",
    "massive_verify.json", "monotonic_amnesty.json", "notify_sent.json", "oos_erosion.json",
    "ownership_state.json", "pool_exhausted_seen.json", "probe_cache.json", "regime_trigger.json",
    "scan_debt.json", "short_interest.json", "short_interest_float.json", "sieve.json",
    "skill_recommendations.jsonl", "skill_revisions.json", "sp500_constituents.json",
    "sprint_status.json", "warmup_scale.json", "watchdog_alarmed.json",
})


def test_ihlal_seti_GERILEMEDI():
    """Sözleşme: değişiklik sonrası bekçinin bulduğu ihlal sayısı DÜŞMEYECEK. Tur öncesi ÖLÇÜLEN
    taban (2026-08-08): 104 artefakt · 0 `violations` · 0 `stale_sinks` · 0 işaretsiz sessiz
    yakalayıcı · 393 işaretli. Görünürlük ARTABİLİR (unresolved 15 → 21), azalamaz."""
    r = codelaw.report()
    g = codelaw.artifact_graph()
    assert r["silent_handlers"] == 0
    assert r["annotated_handlers"] >= 393, "işaretli yakalayıcı kaybolmuş — tarayıcı körelmiş olabilir"
    assert len(g["artifacts"]) >= 104, "artefakt sayısı düştü: grafik daraldı"
    assert g["violations"] == [] and g["stale_sinks"] == []
    assert r["unresolved_artifact_calls"] >= 21, "görünürlük geriledi (kör sınıf geri gelmiş olabilir)"
    # GERİLEME KIYASI (sayı-pin'in halefi, yukarıdaki beyan): tabandan EKSİLEN muafiyet ihlaldir.
    eksilen = SINK_TABANI - set(codelaw.DECLARED_SINKS)
    assert not eksilen, (
        f"muafiyet tabanından ad(lar) düşmüş: {sorted(eksilen)}. Bir muafiyet KAPANDIYSA "
        "(artefakta gerçek dış okuyucu geldi ya da artefakt öldü) bu dosyadaki `SINK_TABANI` "
        "BEYANLA güncellenir — sessiz düşüş, muafiyetin neden kalktığını kayıtsız bırakır.")
    # v215: iki yeni kayıt AÇIK ve SAYILI. Beyan eklemek serbest değil, gerekçelidir.
    assert len(codelaw.DECLARED_SINK_PATTERNS) == 1 and len(codelaw.HUMAN_INVOKED_SINKS) == 1
    assert r["stale_claims"] == [] and r["orphan_patterns"] == []
    assert r["ok"] is True, r


def test_muafiyet_tabani_KODLA_AYNI_KUMEDIR():
    """Tabanın ikinci yarısı: EKLEME ihlal değildir ama BEYANSIZ kalamaz. Bu test kırmızıya
    döndüğünde yapılacak şey kodu geri almak DEĞİL, yukarıdaki `SINK_TABANI` blokunu yeni adla ve
    GEREKÇESİYLE düzenlemektir (v198 `KART_TABANI` ratchet'i ile birebir aynı sözleşme).

    NEDEN İKİ AYRI TEST: yön ayrımı bir teşhis kararıdır. Yukarıdaki `test_ihlal_seti_GERILEMEDI`
    bir GÜVENLİK gerilemesidir (kapanmış bir muafiyet kayıtsız yeniden açılabilir); bu ise bir
    KAYIT borcudur. İkisi tek assert'te toplansaydı, meşru bir eklemenin kırmızısı "bekçi geriledi"
    diye okunurdu — v214'ün sayı-pin'inde tam olarak bu oldu."""
    olculen = set(codelaw.DECLARED_SINKS)
    assert olculen == SINK_TABANI, (
        f"muafiyet listesi tabandan ayrıştı — beyansız eklenen: {sorted(olculen - SINK_TABANI)}; "
        f"beyansız düşen: {sorted(SINK_TABANI - olculen)}. Ekleme MEŞRU olabilir; `SINK_TABANI` "
        "blokunu gerekçesiyle düzenle.")


def test_her_yeni_beyanin_gerekcesi_bir_cumleden_uzun():
    """`test_her_beyanin_turkce_bir_gerekcesi_var` disiplini iki yeni kayda da uygulanır."""
    for kayit in (codelaw.DECLARED_SINK_PATTERNS, codelaw.HUMAN_INVOKED_SINKS):
        for ad, spec in kayit.items():
            assert spec.get("sinif"), f"{ad}: sınıf yazılmamış"
            assert len(spec.get("gerekce", "")) >= 30, f"{ad}: gerekçe bir cümle bile değil"


def test_pozitif_kontrol_iki_yasa_da_hala_yakaliyor():
    """Yeşilin anlamı olması için tarayıcının çalıştığı KANITLANMALI (test_codelaw_v59 disiplini)."""
    assert len(codelaw.scan_source("try:\n    x = 1\nexcept Exception:\n    pass\n")) == 1
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        (pathlib.Path(d) / "y.py").write_text(
            "from . import store\n"
            "def f():\n"
            "    store.write_json('oksuz.json', {})\n")
        g = codelaw.artifact_graph(d)
        assert g["violations"] == ["oksuz.json"]
