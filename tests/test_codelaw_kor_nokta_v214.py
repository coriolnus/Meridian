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
                                         "konumsal_arg_yok": 1}
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
    assert len(hepsi) == len(codelaw.DECLARED_SINKS)
    iddialilar = [c["artifact"] for c in hepsi if c["claims_no_prod_reader"]]
    assert iddialilar == ["insider_signals.json"], iddialilar
    # ve iddiası doğru: bu dosyayı gerçekten HİÇBİR yer okumuyor (yazar bile)
    assert codelaw.artifact_graph()["artifacts"]["insider_signals.json"]["readers"] == []


# ---------------------------------------------------------------------------
# GERİLEME YOK — YASA-6 GEVŞEMEDİ
# ---------------------------------------------------------------------------

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
    assert len(codelaw.DECLARED_SINKS) == 36, "muafiyet listesi büyümüş/küçülmüş — gerekçesini yaz"
    assert r["ok"] is True, r


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
