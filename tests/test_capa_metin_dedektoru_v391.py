"""test_capa_metin_dedektoru_v391.py — SATIR ÇAPASI YASASININ ÜÇÜNCÜ VE DÖRDÜNCÜ DÜNYASI
(TSK-080, Ö-49 KALANI — B-18 ikinci bakım dilimi, 2026-09-03).

WP6-E'nin "GERÇEKTEN AÇIK KALANLAR" listesindeki iki alt-kalemi kapatır:

  B1 · `docs/` YASA KAPSAMI DIŞINDA — `_EK_CAPA_KOKLERI` hiçbir zaman `docs`u içermedi (2324
       çapanın 704'ü çürüktü, çoğu tarihli teşhis belgesindeydi). TSK-080'in TAZE ölçümü
       (2026-09-03, `_capalari_olc` ile GERÇEK çözümleme): 139 `.md`, 2997 çapa, 1020 çürük →
       951 tarihli teşhis · 64 `RUNBOOK.md` (üretilmiş) · 5 YAŞAYAN (bu turda sembole çevrildi).
       `codelaw.stale_docs_line_anchors` bu üçüncü dünyayı `.py` gibi SIFIR TOLERANSLA kapatır —
       ama `codelaw._docs_capa_disi` ile İKİ SINIFI (tarihli teşhis belgesi + üretilmiş RUNBOOK)
       baştan dışlar; dışlanan dosya SESSİZCE değil ADIYLA (`disla_out`) düşer.

       ÖLÇÜLEN SÜRPRİZ: RUNBOOK'un 64 çürüğünün TAMAMI `ops/*.sh` başlık yorumundan DEĞİL,
       ONAYLI KAYNAK SÖZLEŞMESİ madde-2'den (`MERIDIAN_ENGINEERING_LOG.md` "KALICI RİSKLER /
       DERSLER" excerpt'i) geliyor — o günlük kendisi vaka-künyeli tarihsel kayıt ve depo
       kökünde, `docs/` dışında; TSK-080'in dosya sahipliği onu KAPSAMAZ (rapora açık madde).

  B2 · DÜZ-METİN / ÇAPRAZ-BİÇİM ÇAPASI — üç satır-çapası dünyası da (`.py`, `.tsx`, `docs`) TEK
       sözdizimini tanır: dosya adı BİTİŞİK `:NNN`, hedef DAİMA `.py`. `codelaw.stale_text_anchors`
       iki YENİ kör noktayı kapatır: (a) çapraz-biçim (`goal.yaml:27`, opsiyonel `NNN-MMM` aralık),
       (b) düz-metin Türkçe "satır NNN" (dosya adı bitişik DEĞİL, aynı satırdaki ÖNCEKİ belirteçten
       çözülür). Hüküm YAPISAL OLARAK DAR (içerik uyumu ölçülemez — yalnız hedef VARLIĞI/MENZİLİ),
       bu yüzden `report()["ok"]`i ETKİLEMEZ (v214 emsali: `line_anchor_unresolved` ile aynı
       disiplin — adıyla raporlanır, bekçiyi kırmızıya çekmez).

Her sıfır/dışlama iddiasının yanında POZİTİF KONTROL var (test_codelaw_v59 disiplini): sentetik
bir çürük/dışlanan/çözülemeyen çapa verilir, tarayıcının onu YAKALAMASI beklenir.
"""
from __future__ import annotations

import pathlib

from meridian import codelaw

REPO = pathlib.Path(__file__).resolve().parents[1]


# ---------------------------------------------------------------------------
# B1 (a) — `_docs_capa_disi`: TEK KAPI, ÜÇ SINIF
# ---------------------------------------------------------------------------

def test_docs_capa_disi_TARIHLI_TESHIS_BELGESINI_DISLAR():
    assert codelaw._docs_capa_disi("DENETIM-BAYAT-BEYAN-SUPURME-2026-08-23.md") is True
    assert codelaw._docs_capa_disi("ENVANTER-O49-KALAN-2026-08-22.md") is True


def test_docs_capa_disi_RUNBOOK_DISLAR():
    assert codelaw._docs_capa_disi("RUNBOOK.md") is True


def test_docs_capa_disi_YASAYAN_BELGEYI_DISLAMAZ():
    """Dışlama ÜÇ sınıfla SINIRLI — dördüncü bir sınıf icat edilmemeli. Sıradan bir yaşayan belge
    (`docs/ARAYUZ-SOZLUGU.md`, kökte, `superpowers/plans|specs` DIŞINDA) hiçbir sınıfa girmez."""
    assert codelaw._docs_capa_disi("ARAYUZ-SOZLUGU.md") is False
    assert codelaw._docs_capa_disi("docs/ARAYUZ-SOZLUGU.md") is False


# ---------------------------------------------------------------------------
# B1 (a)-RULING — TARİH-ÖNEKLİ SUPERPOWERS PLAN/SPEC (düzeltme turu 1, 2026-09-03)
# ---------------------------------------------------------------------------
# İnceleme sorusu-1'in Rol-1 ruling'i: `docs/superpowers/plans/` ve `docs/superpowers/specs/`
# İÇİNDE, `YYYY-AA-GG-` ÖNEKLİ dosya adı da tarihli-teşhis belgesiyle AYNI aile sayılır — ama
# YALNIZ bu iki dizinde (dizin sınırı KASTEN DAR, bkz. `_DOCS_SUPERPOWERS_TARIHLI_DIZINLER`
# docstring'i).

def test_docs_capa_disi_SUPERPOWERS_PLAN_ONEK_TARIHLI_DISLAR():
    assert codelaw._docs_capa_disi(
        "docs/superpowers/plans/2026-08-17-23c-dinlenen-limit-plan.md") is True


def test_docs_capa_disi_SUPERPOWERS_SPEC_ONEK_TARIHLI_DISLAR():
    assert codelaw._docs_capa_disi(
        "docs/superpowers/specs/2026-08-27-bot-roster-design.md") is True


def test_docs_capa_disi_ONEK_TARIH_DIZIN_DISINDA_DISLAMAZ():
    """DİZİN SINIRI KASTEN DAR: AYNI dosya adı (`YYYY-AA-GG-` önekli) `superpowers/plans|specs`
    DIŞINDA bir yerde ise (ör. `docs/mutasyon/`, kendi ayrı günlük türü) dışlanmaz — geniş bir
    "önekte tarih varsa dışla" kuralı ilgisiz dosyaları da yutardı."""
    assert codelaw._docs_capa_disi("docs/mutasyon/2026-08-01.md") is False
    assert codelaw._docs_capa_disi("2026-08-17-23c-dinlenen-limit-plan.md") is False, (
        "dizin bilgisi olmayan çıplak dosya adı (c) sınıfına giremez — dizin ŞART")


def test_docs_capa_disi_SUPERPOWERS_DIZININDE_ONEKSIZ_AD_DISLANMAZ():
    """DİZİN doğru ama AD tarih-ÖNEKLİ değilse (varsayımsal) yine dışlanmaz — iki koşul BİRLİKTE
    gerekir, dizin TEK BAŞINA yeterli değil."""
    assert codelaw._docs_capa_disi("docs/superpowers/plans/oneksiz-plan.md") is False


# ---------------------------------------------------------------------------
# B1 (b) — `stale_docs_line_anchors`: POZİTİF KONTROL + DIŞLAMA + MUTASYON
# ---------------------------------------------------------------------------

def _sentetik_docs_agac(kok: pathlib.Path) -> None:
    """`meridian`e benzeyen bir hedef ağacı + `docs`u kurar: bir YAŞAYAN belge (menzil-dışı
    çapa taşır → ÇÜRÜK), bir TARİHLİ TEŞHİS belgesi (AYNI türde çürük çapa taşır → DIŞLANIR — (a)),
    bir RUNBOOK.md (AYNI türde çürük çapa taşır → DIŞLANIR — (b)), bir SUPERPOWERS PLAN dosyası
    (AYNI türde çürük çapa taşır → DIŞLANIR — (c), RULING düzeltme turu 1)."""
    (kok / "meridian").mkdir()
    (kok / "meridian" / "hedef.py").write_text("x = 1\n", encoding="utf-8")
    (kok / "docs").mkdir()
    (kok / "docs" / "yasayan.md").write_text(
        "kaynak: hedef.py:999 (menzil dışı)\n", encoding="utf-8")
    (kok / "docs" / "TESHIS-2026-08-13.md").write_text(
        "kaynak: hedef.py:999 (menzil dışı, tarihli)\n", encoding="utf-8")
    (kok / "docs" / "RUNBOOK.md").write_text(
        "kaynak: hedef.py:999 (menzil dışı, üretilmiş)\n", encoding="utf-8")
    (kok / "docs" / "superpowers").mkdir()
    (kok / "docs" / "superpowers" / "plans").mkdir()
    (kok / "docs" / "superpowers" / "plans" / "2026-08-17-sentetik-plan.md").write_text(
        "kaynak: hedef.py:999 (menzil dışı, plan)\n", encoding="utf-8")


def test_docs_capasi_ARTIK_GORULUYOR(tmp_path, monkeypatch):
    """Kör noktanın kendisi: `docs/` içindeki bir menzil-dışı çapa yakalanır — aynı metin bir
    `.py` dosyasında olsaydı yasa onu bugün de görüyordu (`_EK_CAPA_KOKLERI` `docs` içermiyordu)."""
    _sentetik_docs_agac(tmp_path)
    monkeypatch.chdir(tmp_path)
    kor: list = []
    disla: list = []
    curuk = codelaw.stale_docs_line_anchors("docs", py_kokler=("meridian",),
                                            cozulemeyen_out=kor, disla_out=disla)
    assert [(c["kaynak"], c["neden"]) for c in curuk] == [("yasayan.md:1", "menzil_disi")], curuk


def test_docs_dislama_UC_SINIF_da_ADIYLA_DUSER(tmp_path, monkeypatch):
    """Dışlanan üç belge SESSİZCE atılmaz — `disla_out`a adıyla yazılır (Yasa 6 disiplini:
    dışlanan kapsam da görünür kalır). (c) sınıfı (RULING, düzeltme turu 1) da dahil."""
    _sentetik_docs_agac(tmp_path)
    monkeypatch.chdir(tmp_path)
    disla: list = []
    codelaw.stale_docs_line_anchors("docs", py_kokler=("meridian",), disla_out=disla)
    assert sorted(disla) == [
        "2026-08-17-sentetik-plan.md", "RUNBOOK.md", "TESHIS-2026-08-13.md"], disla


def test_docs_dislama_KALDIRILINCA_TARIHLI_BELGE_de_OTER(tmp_path, monkeypatch):
    """MUTASYON KANITI (CLAUDE.md §6: çivi yeşili kanıt değildir): `_docs_capa_disi` filtresi
    olmadan AYNI ağaç taranırsa tarihli belge/RUNBOOK/plan da ÇÜRÜK sayılır — yani dışlama
    sessizce hiçbir şey yapmıyor DEĞİL, gerçekten üç sınıfı hükümden çıkarıyor. Bu test
    `_docs_capa_disi`yi BAYPAS ederek (tarayıcının kendi filtresiz çekirdeğini, `_capalari_olc`u,
    doğrudan çağırarak) o mutasyonu KALICI bir regresyon testine çevirir."""
    _sentetik_docs_agac(tmp_path)
    monkeypatch.chdir(tmp_path)
    adres = codelaw._capa_adres_defteri(("meridian",))
    tum_dosyalar = list(codelaw._md_files("docs"))
    assert {f.name for f in tum_dosyalar} == {
        "yasayan.md", "TESHIS-2026-08-13.md", "RUNBOOK.md", "2026-08-17-sentetik-plan.md"}
    curuk_FILTRESIZ = codelaw._capalari_olc(tum_dosyalar, adres, None, "mutasyon_kaniti")
    assert {c["kaynak"].split(":")[0] for c in curuk_FILTRESIZ} == {
        "yasayan.md", "TESHIS-2026-08-13.md", "RUNBOOK.md", "2026-08-17-sentetik-plan.md"}, (
        "filtresiz çekirdek dördünü de çürük görmüyor — dışlamanın gerçekten bir şey filtrelediği "
        f"kanıtlanamadı: {curuk_FILTRESIZ}")


def test_docs_dislama_SUPERPOWERS_ONEK_KALDIRILINCA_PLAN_da_OTER(tmp_path, monkeypatch):
    """MUTASYON KANITI (RULING, düzeltme turu 1, inceleme sorusu-1): yalnız (c) sınıfı
    (superpowers plan/spec dizin filtresi) devre dışı bırakılırsa — (a)/(b) DOKUNULMADAN —
    sentetik plan dosyası da ÇÜRÜK sayılır. Ruling'in istediği tam olarak bu: "ön-ek desenini
    kaldır → çivi ötmeli"."""
    _sentetik_docs_agac(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(codelaw, "_DOCS_SUPERPOWERS_TARIHLI_DIZINLER", ())
    kor: list = []
    disla: list = []
    curuk = codelaw.stale_docs_line_anchors("docs", py_kokler=("meridian",),
                                            cozulemeyen_out=kor, disla_out=disla)
    kaynaklar = {c["kaynak"].split(":")[0] for c in curuk}
    assert "2026-08-17-sentetik-plan.md" in kaynaklar, curuk
    # (a)/(b) HÂLÂ dışlı — yalnız (c) mutasyona uğradı:
    assert "TESHIS-2026-08-13.md" not in kaynaklar and "RUNBOOK.md" not in kaynaklar
    assert sorted(disla) == ["RUNBOOK.md", "TESHIS-2026-08-13.md"], disla


def test_docs_koku_YOKSA_UNSCANNED(tmp_path, monkeypatch):
    """`stale_tsx_line_anchors` emsali: kök bulunamazsa körlük SESSİZ değil, `UNSCANNED`e yazılır."""
    monkeypatch.chdir(tmp_path)
    codelaw.UNSCANNED.clear()
    curuk = codelaw.stale_docs_line_anchors("olmayan_docs_koku")
    assert curuk == []
    assert any(u["phase"] == "stale_docs_line_anchors" for u in codelaw.UNSCANNED), codelaw.UNSCANNED
    codelaw.UNSCANNED.clear()


def test_docs_capasi_COZULEMEYENI_SESSIZCE_ATMAZ(tmp_path, monkeypatch):
    """`.py`/`.tsx` dünyasıyla AYNI disiplin: hükmü kurulamayan çapa (hedef ağaçta yok) SAYILIR,
    sessizce düşmez."""
    (tmp_path / "meridian").mkdir()
    (tmp_path / "meridian" / "hedef.py").write_text("x = 1\n", encoding="utf-8")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "yasayan.md").write_text(
        "yok_boyle_bir_dosya.py:12 ve hedef.py:1\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    kor: list = []
    curuk = codelaw.stale_docs_line_anchors("docs", py_kokler=("meridian",), cozulemeyen_out=kor)
    assert curuk == []
    assert [k["neden"] for k in kor] == ["hedef_yok"], kor
    assert kor[0]["capa"] == "yok_boyle_bir_dosya.py:12"


# ---------------------------------------------------------------------------
# B1 (c) — `report()` KABLOLAMASI: `ok`u ETKİLER, tri-state DAVRANIR
# ---------------------------------------------------------------------------

def test_report_docs_alanlari_canli_agacta_TEMIZ():
    """Bu turun kendi kanıtı: 5 yaşayan-belge çürüğü sembole çevrildi, canlı ağaçta `docs`
    kapsamı bugün TEMİZ ve tam `report()["ok"]`e katılıyor."""
    r = codelaw.report()
    assert r["docs_line_anchors"] == [], r["docs_line_anchors"]
    assert r["docs_line_anchor_var"] is False
    assert isinstance(r["docs_line_anchor_excluded"], list) and len(r["docs_line_anchor_excluded"]) > 50, (
        "dışlanan dosya sayısı beklenenden düşük — tarayıcı gerçekten `docs/`yi mi tarıyor?")
    assert "RUNBOOK.md" in r["docs_line_anchor_excluded"]
    assert r["ok"] is True, r


def test_docs_line_anchor_var_ok_HUKMUNU_DUSURUR_sentetik(tmp_path, monkeypatch):
    """POZİTİF KONTROL: `docs_line_anchor_var` gerçekten `ok`u False'a çekiyor mu? Sentetik bir
    ağaçta (sentetik `root="meridian"` — `report()`in `docs` kapısını AÇAN köke ihtiyacı var,
    bkz. `tsx_hedef` mantığı) YAŞAYAN belgede çürük çapa varken `report()["ok"]` False olmalı."""
    (tmp_path / "meridian").mkdir()
    (tmp_path / "meridian" / "hedef.py").write_text("x = 1\n", encoding="utf-8")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "yasayan.md").write_text("hedef.py:999\n", encoding="utf-8")
    (tmp_path / "tests").mkdir()
    (tmp_path / "ops").mkdir()
    (tmp_path / "ui").mkdir()
    (tmp_path / "ui" / "src").mkdir(parents=True, exist_ok=True)
    monkeypatch.chdir(tmp_path)
    # DİĞER YASALARIN KENDİ İHLALLERİYLE KARIŞMAMASI İÇİN İZOLE EDİLİR: bu minik sentetik ağaçta
    # `DECLARED_SINK_PATTERNS`/`HUMAN_INVOKED_SINKS` üretim artefaktlarını (`intraday_bars/*.jsonl`
    # vb.) anıyor ve bunlar burada DOĞAL olarak `stale_claims` üretiyor — docs GATİNGİNDEN
    # BAĞIMSIZ, ayrı bir kırmızı. İzolasyon olmadan bu test YANLIŞ SEBEPLE geçerdi (ölçüldü:
    # mutasyonla `docs_curuk_var is not True` kaldırılınca test hâlâ YEŞİLDİ — CLAUDE.md §6).
    monkeypatch.setattr(codelaw, "stale_claims", lambda *a, **k: [])
    r = codelaw.report(root="meridian")
    assert r["docs_line_anchor_var"] is True
    assert r["stale_claims"] == [], "izolasyon başarısız — hâlâ başka bir yasa kırmızı üretiyor"
    assert r["ok"] is False, r


def test_docs_alanlari_OLCULMEDIYSE_None(tmp_path, monkeypatch):
    """UYDURMA YASAĞI: sentetik `root` DIŞARIDAN `tsx_kok=None` ile çağrılırsa (yani `docs`
    kapısı kapalı kalırsa) alan `None`dir, boş liste DEĞİL — "baktım, temiz" ile "bakmadım" aynı
    alandan okunamaz (tsx_capalar ile AYNI disiplin)."""
    (tmp_path / "meridian").mkdir()
    monkeypatch.chdir(tmp_path)
    r = codelaw.report(root=str(tmp_path / "meridian"))
    assert r["docs_line_anchors"] is None
    assert r["docs_line_anchor_var"] is None
    assert r["docs_line_anchor_excluded"] is None


# ---------------------------------------------------------------------------
# B2 (a) — ÇAPRAZ-BİÇİM: `.yaml`/`.md`/`.json`/`.sh` hedefli `:NNN` (+ ARALIK)
# ---------------------------------------------------------------------------

def test_capraz_bicim_capa_menzil_disi_yakalanir(tmp_path, monkeypatch):
    (tmp_path / "state").mkdir()
    (tmp_path / "state" / "goal.yaml").write_text("a: 1\nb: 2\n", encoding="utf-8")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "notlar.md").write_text(
        "eşik `goal.yaml:27`de tanımlı\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    curuk = codelaw.stale_text_anchors("docs", hedef_kokler=("state",))
    assert [(c["capa"], c["neden"]) for c in curuk] == [("goal.yaml:27", "menzil_disi")], curuk


def test_capraz_bicim_capa_ARALIK_menzil_disi_yakalanir(tmp_path, monkeypatch):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "hedef.sh").write_text("#!/bin/sh\necho hi\n", encoding="utf-8")
    (tmp_path / "docs" / "notlar.md").write_text(
        "gövde `hedef.sh:10-20` arası\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    curuk = codelaw.stale_text_anchors("docs", hedef_kokler=("docs",))
    assert [(c["capa"], c["neden"]) for c in curuk] == [("hedef.sh:10-20", "menzil_disi")], curuk


def test_capraz_bicim_AYAKTA_capa_curuk_SAYILMAZ(tmp_path, monkeypatch):
    """NEGATİF KONTROL: menzil içindeki, boş/yorum olmayan bir satırı gösteren çapraz-biçim çapa
    çürük SAYILMAZ."""
    (tmp_path / "state").mkdir()
    (tmp_path / "state" / "goal.yaml").write_text("a: 1\nb: 2\nc: 3\n", encoding="utf-8")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "notlar.md").write_text("eşik `goal.yaml:2`de\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    curuk = codelaw.stale_text_anchors("docs", hedef_kokler=("state",))
    assert curuk == [], curuk


# ---------------------------------------------------------------------------
# B2 (b) — DÜZ-METİN: Türkçe "satır NNN" (dosya adı ÖNCEKİ belirteçten çözülür)
# ---------------------------------------------------------------------------

def test_duz_metin_satir_NNN_ONCEKI_dosya_adindan_cozulur(tmp_path, monkeypatch):
    (tmp_path / "meridian").mkdir()
    (tmp_path / "meridian" / "bararchive.py").write_text("a = 1\nb = 2\n", encoding="utf-8")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "notlar.md").write_text(
        "`bararchive.py`'nin dosya başlığı (satır 99) sorunu biliyor\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    curuk = codelaw.stale_text_anchors("docs", hedef_kokler=("meridian",))
    assert [(c["capa"], c["neden"]) for c in curuk] == [("satır 99", "menzil_disi")], curuk


def test_duz_metin_satir_NNN_ARALIK_ONCEKI_dosya_adindan_cozulur(tmp_path, monkeypatch):
    (tmp_path / "meridian").mkdir()
    (tmp_path / "meridian" / "bararchive.py").write_text("a = 1\nb = 2\n", encoding="utf-8")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "notlar.md").write_text(
        "`bararchive.py`'nin dosya başlığı (satır 13-18) sorunu biliyor\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    curuk = codelaw.stale_text_anchors("docs", hedef_kokler=("meridian",))
    assert [(c["capa"], c["neden"]) for c in curuk] == [("satır 13-18", "menzil_disi")], curuk


def test_duz_metin_satir_NNN_dosya_adi_YOKSA_cozulemez(tmp_path, monkeypatch):
    """UYDURMA YASAĞI: aynı satırda dosya-adı belirteci yoksa hedef UYDURULMAZ — hüküm
    KURULMAZ ama `dosya_belirtilmemis` nedeniyle KAYDEDİLİR (sessizce düşmez)."""
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "notlar.md").write_text(
        "kalan iş satır 42'de özetlendi (dosya adı yok)\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    kor: list = []
    curuk = codelaw.stale_text_anchors("docs", hedef_kokler=(), cozulemeyen_out=kor)
    assert curuk == []
    assert [k["neden"] for k in kor] == ["dosya_belirtilmemis"], kor


def test_duz_metin_satir_NNN_AYAKTA_curuk_SAYILMAZ(tmp_path, monkeypatch):
    (tmp_path / "meridian").mkdir()
    (tmp_path / "meridian" / "bararchive.py").write_text("a = 1\nb = 2\nc = 3\n", encoding="utf-8")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "notlar.md").write_text(
        "`bararchive.py` başlığı (satır 2) sorunu biliyor\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    curuk = codelaw.stale_text_anchors("docs", hedef_kokler=("meridian",))
    assert curuk == [], curuk


def test_duz_metin_dislama_docs_ile_AYNI_KAPI(tmp_path, monkeypatch):
    """B1 ile TEK dışlama kapısı paylaşılır: tarihli teşhis belgesindeki bir "satır NNN" metin
    çapası da dışlanır."""
    (tmp_path / "meridian").mkdir()
    (tmp_path / "meridian" / "hedef.py").write_text("x = 1\n", encoding="utf-8")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "TESHIS-2026-08-13.md").write_text(
        "`hedef.py`'nin başlığı (satır 999) sorunu biliyor\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    curuk = codelaw.stale_text_anchors("docs", hedef_kokler=("meridian",))
    assert curuk == [], curuk


# ---------------------------------------------------------------------------
# B2 (c) — MENZİL KONTROLÜ MUTASYONU + `report()`te `ok`U ETKİLEMEZ
# ---------------------------------------------------------------------------

def test_metin_capasi_menzil_kontrolu_KALDIRILINCA_OTER(tmp_path, monkeypatch):
    """MUTASYON KANITI: `n1 < 1 or ust > len(satirlar)` sınırı olmadan (elle taklit edilerek)
    AYNI veri üzerinde hüküm YOK olurdu — yani ölçüm gerçekten bu sınıra dayanıyor."""
    (tmp_path / "state").mkdir()
    (tmp_path / "state" / "goal.yaml").write_text("a: 1\n", encoding="utf-8")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "notlar.md").write_text("eşik `goal.yaml:27`de\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    curuk = codelaw.stale_text_anchors("docs", hedef_kokler=("state",))
    assert len(curuk) == 1, curuk
    # Menzil kontrolü OLMASAYDI (satır sayısı ne olursa olsun her zaman "içeride" sayılsaydı)
    # bu vaka görünmezdi — burada elle doğrulanıyor: dosyanın gerçek satır sayısı 1, çapa 27.
    satirlar = (tmp_path / "state" / "goal.yaml").read_text(encoding="utf-8").splitlines()
    assert len(satirlar) < 27, "sentetik veri artık menzil-dışı değil — test kendi tabanını yitirdi"


def test_report_text_anchor_stale_ALANI_GORUNUR_ve_OK_HUKMUNU_ETKILEMEZ(monkeypatch):
    """ASIL SÖZLEŞME: `report()["ok"]` `text_anchor_stale`ten TAMAMEN BAĞIMSIZDIR. Canlı ağacın
    bugünkü hâline bakılmaksızın (o sıfır da olabilir, dolu da) monkeypatch ile alanı ZORLA
    doldurup `ok`un DEĞİŞMEDİĞİ doğrudan kanıtlanır."""
    taban = codelaw.report()
    monkeypatch.setattr(codelaw, "stale_text_anchors",
                        lambda *a, **k: [{"kaynak": "x.md:1", "capa": "y.yaml:1", "neden": "menzil_disi"}])
    sonra = codelaw.report()
    assert sonra["text_anchor_stale"], "monkeypatch etkisiz kaldı — alan hâlâ boş"
    assert sonra["ok"] == taban["ok"], (
        f"text_anchor_stale dolu olunca ok değişti ({taban['ok']} → {sonra['ok']}) — "
        "bu alan `ok`u ETKİLEMEMELİYDİ (docstring sözleşmesi)")


def test_text_anchor_alanlari_canli_agacta_KAPSAM_OLCULDU():
    """KÖRLÜK ALARMI (v214 emsali): "0 bulgu" tek başına anlamsızdır — kapsamın GERÇEKTEN
    tarandığı ayrıca ölçülür. Bugün (2026-09-03) canlı `docs/`de yaşayan belgelerde ne çapraz-
    biçim ne düz-metin "satır NNN" deseni VAR (elle doğrulandı — `grep` sonucu boş); alan bu
    yüzden [] dönebilir, ama tarama gerçekten `docs/`yi görmüş olmalı — bu iki köşe taşıyla
    sınanır."""
    r = codelaw.report()
    assert isinstance(r["text_anchor_stale"], list)
    assert isinstance(r["text_anchor_unresolved"], list)
    # tarayıcı gerçekten dosya görüyor mu: en az yaşayan-belge sayısı kadar `.md` taranmış olmalı
    yasayan = [f for f in codelaw._md_files("docs") if not codelaw._docs_capa_disi(f.name)]
    assert len(yasayan) >= 20, "canlı `docs/` beklenenden küçük görünüyor — kök doğru mu?"


# ---------------------------------------------------------------------------
# GERİLEME YOK — `.py`/`.tsx` DÜNYALARI DEĞİŞMEDİ
# ---------------------------------------------------------------------------

def test_py_ve_tsx_dunyalari_docs_EKLENMESIYLE_BOZULMADI():
    """B1/B2 YENİ alanlar EKLER, VAR OLAN sözleşmeyi DEĞİŞTİRMEZ: `.py` dünyası hâlâ sıfır
    çürük, tsx dünyası hâlâ 0 borç (TSK-094 sonrası taban)."""
    r = codelaw.report()
    assert r["stale_line_anchors"] == []
    assert r["tsx_line_anchor_nuks"] is False
    assert r["sembol_capa_curume"] is False
