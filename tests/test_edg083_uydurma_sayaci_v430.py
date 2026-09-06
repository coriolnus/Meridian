"""tests/test_edg083_uydurma_sayaci_v430.py — EDG-2026-083 UYDURMA SAYACININ çivisi.

NE ÖLÇER. `research/olcumler/edg083_zihin_modeli_ek_sayfalar/uydurma_say.py` — kartın
(`EDG-2026-083-zihin-modeli-talep-uzerine-ek-sayfalar.yaml`, `olcum_plani` 3. madde) "uydurma
sayımı" adımını üreten betiği doğrular: Hindsight zihin modeli sayfalarındaki (markdown metin)
depo atıflarını BEŞ sınıfa (`yol`/`kart`/`kalem`/`civi`/`sha`) ayırıp GERÇEK depoda doğrular, sayfa
başına ve toplamda `dogrulanan/toplam` oranını üretir. Betik HÜKÜM VERMEZ — eşik (%80/%60) burada
GEÇMEZ, bu dosya yalnız SAYIMIN doğruluğunu ölçer.

ROL: AJAN (worktree). AĞSIZ, `meridian`SIZ: bu dosya `meridian` paketinden hiçbir şey içe
aktarmaz (betiğin kendisi de aktarmaz — obs'a ulaşma riski yok). Betik `betikten_modul_yukle`
(`ops.sasi_yukleyici.kaynaktan_yukle`nin `tests/conftest.py` takma adı) ile KAYNAKTAN yüklenir —
paket olmayan `research/olcumler/*` betikleri için depo genelinde TEK yükleme yolu budur (bayat
`__pycache__` kusuru, `ops/sasi_yukleyici.py` modül başlığı); sys.path hack'i YOK.

GERÇEK DEPO KÖKÜ, SENTETİK SAYFA İÇERİĞİ. Testler GERÇEK `--repo` (bu dosyanın bulunduğu ağacın
kökü, `KOK`) ile çalışır — `git ls-files`/kart dizini/ROADMAP.md/`tests/` GERÇEK depo durumunu
yansıtır — ama sayfa dosyaları (JSON/`.md`) `tmp_path`te ÜRETİLİR (sahte depo İCAT EDİLMEDİ, brief
şartı). Sabit sınama seti (hepsi bu turda TEK TEK doğrulandı, ölçüm tarihi 2026-09-06):
  · gerçek yol   `meridian/pitlaw.py`            (git ls-files'ta VAR)
  · uydurma yol  `meridian/olmayan_modul.py`     (git ls-files'ta YOK)
  · gerçek kart  `EDG-2026-067`                  (`research/cards/EDG-2026-067-*.yaml` VAR)
  · uydurma kart `EDG-2026-999`                  (öyle bir dosya YOK)
  · gerçek kalem `TSK-142`                       (ROADMAP.md'de `[TSK-142]` geçiyor)
  · uydurma kalem `TSK-999`                      (ROADMAP.md'de YOK)
  · gerçek çivi  `v341`                          (`tests/test_pit_yasasi_v341.py` VAR)
  · uydurma çivi `v999`                          (`tests/*_v999.py` YOK)
  · gerçek sha   `ce6f013`                       (bu depoda GERÇEK, ESKİ bir commit — git geçmişi
                                                   değişmez, bu kısa sha KALICI olarak çözülür)
  · sahte sha    `deadbeef1`                     (`git cat-file -e` ile ÇÖZÜLEMEZ — 128 döner)

MUTASYON KANITLARI (CLAUDE.md §6 — "çivi yeşili kanıt değildir"): bu dosyanın docstring'i turun
SONUNDA, gerçek mutasyon koşumlarından SONRA güncellenir (rapor dosyasında ayrıca yazılı) —
`atiflari_cikar`ın sınıf ayrımını kaldıran ve `oran` hesabını `toplam==0`da `0.0`a çeviren iki
BAĞIMSIZ mutasyon, ilgili testleri KIRMIZI yapmalı.

ÇAPA YASAĞI: bu dosyada `dosya.py` + iki-nokta + rakam biçiminde (satır çapası) HİÇBİR atıf YOK
— `test_capa_yasagi_bu_dosyalarda_satir_capasi_yok` bunu bu dosyanın VE ölçülen betiğin kendi
metnini TARAYARAK ayrıca kanıtlar. Sembolik atıflar (`atiflari_cikar`, `ls_files_getir` gibi) NOKTA
İÇERMEZ — `codelaw`ın `tests/` içindeki backtick `modül.sembol` taraması (yalnız `DECLARED_*`
beyanlarını hedefleyen bir sözleşme) bu araştırma betiğini hiç göremeyeceğinden, ona nokta'lı bir
biçimde atıf yazmak ölçülemeyen bir hedefe (`hedef_yok`) işaret ederdi — bilinçli olarak
KULLANILMADI."""
from __future__ import annotations

import json
import pathlib
import re

import pytest

from tests.conftest import betikten_modul_yukle

KOK = pathlib.Path(__file__).resolve().parents[1]
BETIK_YOLU = KOK / "research" / "olcumler" / "edg083_zihin_modeli_ek_sayfalar" / "uydurma_say.py"

GERCEK_YOL = "meridian/pitlaw.py"
UYDURMA_YOL = "meridian/olmayan_modul.py"
GERCEK_KART = "EDG-2026-067"
UYDURMA_KART = "EDG-2026-999"
GERCEK_KALEM = "TSK-142"
UYDURMA_KALEM = "TSK-999"
GERCEK_CIVI = "v341"
UYDURMA_CIVI = "v999"
GERCEK_SHA = "ce6f013"
SAHTE_SHA = "deadbeef1"


def _yukle():
    return betikten_modul_yukle(BETIK_YOLU, "edg083_uydurma_say")


# =================================================================================================
# ÖN-KOŞUL — sınama setinin İDDİALARI depoda GERÇEKTEN doğru mu (test-taban sapması olmasın)
# =================================================================================================

def test_on_kosul_sinama_seti_depoda_iddia_ettigi_gibi():
    assert (KOK / GERCEK_YOL).is_file()
    assert not (KOK / UYDURMA_YOL).exists()
    assert list((KOK / "research" / "cards").glob(f"{GERCEK_KART}-*.yaml"))
    assert not list((KOK / "research" / "cards").glob(f"{UYDURMA_KART}-*.yaml"))
    assert f"[{GERCEK_KALEM}]" in (KOK / "ROADMAP.md").read_text(encoding="utf-8")
    assert f"[{UYDURMA_KALEM}]" not in (KOK / "ROADMAP.md").read_text(encoding="utf-8")
    assert list((KOK / "tests").glob(f"*_{GERCEK_CIVI}.py"))
    assert not list((KOK / "tests").glob(f"*_{UYDURMA_CIVI}.py"))


# =================================================================================================
# ÇAPA YASAĞI — `dosya.py:NNN` biçimi hiçbir yerde (docstring dahil) yok
# =================================================================================================

_YASAKLI_SATIR_CAPASI_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\.py:\d+\b")


def test_capa_yasagi_bu_dosyalarda_satir_capasi_yok():
    for yol in (BETIK_YOLU, pathlib.Path(__file__)):
        metin = yol.read_text(encoding="utf-8")
        bulunan = _YASAKLI_SATIR_CAPASI_RE.findall(metin)
        assert not bulunan, f"{yol} içinde yasaklı satır-çapası deseni bulundu: {bulunan}"


# =================================================================================================
# SINIF REGEXLERİ + TEKİLLEŞTİRME — `atiflari_cikar`
# =================================================================================================

def test_atiflari_cikar_bes_sinifi_ayri_ayri_bulur_ve_TEKILLESTIRIR():
    o = _yukle()
    icerik = (
        f"gerçek yol {GERCEK_YOL} ve tekrar {GERCEK_YOL}; "
        f"uydurma yol {UYDURMA_YOL}; "
        f"gerçek kart {GERCEK_KART} tekrar {GERCEK_KART}; uydurma kart {UYDURMA_KART}; "
        f"gerçek kalem {GERCEK_KALEM}; uydurma kalem {UYDURMA_KALEM}; "
        f"gerçek çivi {GERCEK_CIVI}; uydurma çivi {UYDURMA_CIVI}; "
        f"gerçek sha {GERCEK_SHA}; sahte sha {SAHTE_SHA}; salt rakam 1234567 (sha SAYILMAMALI)"
    )
    atiflar = o.atiflari_cikar(icerik)
    assert atiflar["yol"] == {GERCEK_YOL, UYDURMA_YOL}, atiflar["yol"]
    assert atiflar["kart"] == {GERCEK_KART, UYDURMA_KART}, atiflar["kart"]
    assert atiflar["kalem"] == {GERCEK_KALEM, UYDURMA_KALEM}, atiflar["kalem"]
    assert atiflar["civi"] == {GERCEK_CIVI, UYDURMA_CIVI}, atiflar["civi"]
    assert atiflar["sha"] == {GERCEK_SHA, SAHTE_SHA}, atiflar["sha"]
    assert "1234567" not in atiflar["sha"], "tamamı rakam olan bir dizge sha SAYILMAMALI"


def test_atiflari_cikar_bos_icerikte_bes_sinif_de_bos_kume():
    o = _yukle()
    atiflar = o.atiflari_cikar("bu sayfada hiçbir depo atıfı yok, düz Türkçe düzyazı.")
    assert atiflar == {"yol": set(), "kart": set(), "kalem": set(), "civi": set(), "sha": set()}


def test_atiflari_cikar_yol_bastaki_nokta_egik_cizgiyi_soyar():
    o = _yukle()
    atiflar = o.atiflari_cikar(f"bkz. ./{GERCEK_YOL}")
    assert atiflar["yol"] == {GERCEK_YOL}


# =================================================================================================
# SINIF DOĞRULAYICILARI — GERÇEK depo kökü ile
# =================================================================================================

def test_ls_files_getir_gercek_yol_var_uydurma_yol_yok():
    o = _yukle()
    kume, hata = o.ls_files_getir(KOK)
    assert hata is None
    assert GERCEK_YOL in kume
    assert UYDURMA_YOL not in kume


def test_kart_dogrula_gercek_ve_uydurma():
    o = _yukle()
    assert o.kart_dogrula(KOK, GERCEK_KART) is True
    assert o.kart_dogrula(KOK, UYDURMA_KART) is False


def test_kalem_dogrula_gercek_ve_uydurma():
    o = _yukle()
    assert o.kalem_dogrula(KOK, GERCEK_KALEM) is True
    assert o.kalem_dogrula(KOK, UYDURMA_KALEM) is False


def test_civi_dogrula_gercek_ve_uydurma():
    o = _yukle()
    assert o.civi_dogrula(KOK, GERCEK_CIVI) is True
    assert o.civi_dogrula(KOK, UYDURMA_CIVI) is False


def test_sha_dogrula_gercek_ve_sahte():
    o = _yukle()
    ok, hata = o.sha_dogrula(KOK, GERCEK_SHA)
    assert ok is True and hata is None
    ok, hata = o.sha_dogrula(KOK, SAHTE_SHA)
    assert ok is False and hata is None, "sahte sha bir HATA değil, doğrulanamayan bir SONUÇ"


# =================================================================================================
# YASA 4 — git çağrısı gerçekten çökerse (OSError) sessizce yutulmaz, `hata` alanına yazılır
# =================================================================================================

def test_ls_files_getir_git_calisamazsa_HATA_ALANINA_yazar_cokme(monkeypatch):
    o = _yukle()

    def _patlar(*a, **k):
        raise FileNotFoundError("git ikili dosyası PATH'te yok (test simülasyonu)")

    monkeypatch.setattr(o.subprocess, "run", _patlar)
    kume, hata = o.ls_files_getir(KOK)
    assert kume is None
    assert hata and "çalıştırılamadı" in hata


def test_sha_dogrula_git_calisamazsa_dogrulanamadi_VE_hata_doner(monkeypatch):
    o = _yukle()

    def _patlar(*a, **k):
        raise FileNotFoundError("git ikili dosyası PATH'te yok (test simülasyonu)")

    monkeypatch.setattr(o.subprocess, "run", _patlar)
    ok, hata = o.sha_dogrula(KOK, GERCEK_SHA)
    assert ok is False
    assert hata and "çalıştırılamadı" in hata


# =================================================================================================
# SAYFA-DÜZEYİ ÖLÇÜM — `sayfa_olc` (tam beklenen sayım, UYDURMA YASAĞI dahil)
# =================================================================================================

def _karisik_sayfa_icerigi() -> str:
    return (
        f"S1: {GERCEK_YOL} · {UYDURMA_YOL} · {GERCEK_KART} · {UYDURMA_KART} · "
        f"{GERCEK_KALEM} · {UYDURMA_KALEM} · {GERCEK_CIVI} · {UYDURMA_CIVI} · "
        f"{GERCEK_SHA} · {SAHTE_SHA}"
    )


def test_sayfa_olc_karisik_sayfada_5_sinif_1_2_dogrulanir_toplam_5_10():
    o = _yukle()
    ls_kume, hata = o.ls_files_getir(KOK)
    assert hata is None
    roadmap_metni = (KOK / "ROADMAP.md").read_text(encoding="utf-8")
    hata_biriktirici: list = []
    sayfa = {"id": "s1", "kaynak_dosya": "s1.md", "content": _karisik_sayfa_icerigi()}
    sonuc = o.sayfa_olc(sayfa, KOK, ls_kume, roadmap_metni, hata_biriktirici)

    assert sonuc["toplam"] == 10
    assert sonuc["dogrulanan"] == 5
    assert sonuc["oran"] == pytest.approx(0.5)
    assert sonuc["oran_neden"] is None
    for sinif in ("yol", "kart", "kalem", "civi", "sha"):
        assert sonuc["sinif_bazinda"][sinif]["toplam"] == 2, sinif
        assert sonuc["sinif_bazinda"][sinif]["dogrulanan"] == 1, sinif
    dogrulanamayan_atiflar = {d["atif"] for d in sonuc["dogrulanamayan"]}
    assert dogrulanamayan_atiflar == {UYDURMA_YOL, UYDURMA_KART, UYDURMA_KALEM, UYDURMA_CIVI, SAHTE_SHA}
    assert not hata_biriktirici


def test_sayfa_olc_toplam_SIFIRSA_oran_NONE_ve_neden_var_SIFIR_DEGIL():
    """Uydurma yasağı: ölçülemeyen (atıf yok → oran tanımsız) `None` olur, `0.0` DEĞİL."""
    o = _yukle()
    ls_kume, _ = o.ls_files_getir(KOK)
    roadmap_metni = (KOK / "ROADMAP.md").read_text(encoding="utf-8")
    sayfa = {"id": "bos", "kaynak_dosya": "bos.md", "content": "düz Türkçe düzyazı, atıf yok."}
    sonuc = o.sayfa_olc(sayfa, KOK, ls_kume, roadmap_metni, [])
    assert sonuc["toplam"] == 0
    assert sonuc["oran"] is None
    assert isinstance(sonuc["oran_neden"], str) and len(sonuc["oran_neden"]) >= 20


def test_sayfa_olc_tamamen_uydurmaysa_oran_TAM_SIFIR_NONE_DEGIL():
    """Karşıt uç: atıf VAR (toplam>0) ama hiçbiri doğrulanmıyor → oran 0.0 (ÖLÇÜLDÜ), None DEĞİL —
    'sıfır ile bilmiyorum aynı şey değildir' (CLAUDE.md §4) ayrımının İKİ YÖNÜ de test edilir."""
    o = _yukle()
    ls_kume, _ = o.ls_files_getir(KOK)
    roadmap_metni = (KOK / "ROADMAP.md").read_text(encoding="utf-8")
    sayfa = {"id": "hepsi-uydurma", "kaynak_dosya": "x.md",
             "content": f"{UYDURMA_YOL} · {UYDURMA_KART}"}
    sonuc = o.sayfa_olc(sayfa, KOK, ls_kume, roadmap_metni, [])
    assert sonuc["toplam"] == 2
    assert sonuc["dogrulanan"] == 0
    assert sonuc["oran"] == 0.0


# =================================================================================================
# SAYFA YÜKLEME — `.json` (şema) ve `.md` (ham) ikisi de desteklenir
# =================================================================================================

def test_sayfalari_yukle_json_ve_md_ikisini_de_okur(tmp_path):
    o = _yukle()
    (tmp_path / "a.json").write_text(
        json.dumps({"id": "a", "name": "Bağımlılık haritası", "version": 3,
                   "content": f"{GERCEK_YOL}"}), encoding="utf-8")
    (tmp_path / "b.md").write_text(f"# B\n{GERCEK_KART}\n", encoding="utf-8")

    sayfalar = o.sayfalari_yukle(tmp_path)
    by_id = {s["id"]: s for s in sayfalar}
    assert by_id["a"]["content"] == GERCEK_YOL
    assert by_id["a"]["name"] == "Bağımlılık haritası"
    assert by_id["a"]["version"] == 3
    assert GERCEK_KART in by_id["b"]["content"]
    assert by_id["b"]["name"] is None


# =================================================================================================
# UÇTAN UCA — `calistir` / CLI `ana`
# =================================================================================================

def test_calistir_uctan_uca_iki_sayfa_toplam_dogru_agirliklanir(tmp_path):
    o = _yukle()
    (tmp_path / "s1.md").write_text(_karisik_sayfa_icerigi(), encoding="utf-8")
    (tmp_path / "s2.md").write_text("hiç atıf yok, düz metin.", encoding="utf-8")

    sonuc = o.calistir(sayfa_dizin=tmp_path, repo=KOK)

    assert sonuc["girdi"]["n_sayfa"] == 2
    assert sonuc["sayfalar"]["s1"]["toplam"] == 10
    assert sonuc["sayfalar"]["s1"]["dogrulanan"] == 5
    assert sonuc["sayfalar"]["s2"]["oran"] is None
    assert sonuc["toplam"]["toplam"] == 10
    assert sonuc["toplam"]["dogrulanan"] == 5
    assert sonuc["toplam"]["oran"] == pytest.approx(0.5)
    assert sonuc["hata"] == []
    # betik hüküm VERMEZ — eşiğe dair hiçbir alan (gecti/kaldi/pass/fail) YOK
    assert not ({"gecti", "kaldi", "pass", "fail"} & set(sonuc))


def test_cli_ana_ciktiyi_yazar_ve_markdown_uretir(tmp_path):
    o = _yukle()
    sayfa_dizin = tmp_path / "sayfalar"
    sayfa_dizin.mkdir()
    (sayfa_dizin / "s1.md").write_text(_karisik_sayfa_icerigi(), encoding="utf-8")
    cikti = tmp_path / "sonuc.json"
    md = tmp_path / "rapor.md"

    rc = o.ana(["--sayfa-dizin", str(sayfa_dizin), "--repo", str(KOK),
               "--cikti", str(cikti), "--markdown", str(md)])

    assert rc == 0
    veri = json.loads(cikti.read_text(encoding="utf-8"))
    assert veri["sayfalar"]["s1"]["toplam"] == 10
    md_metin = md.read_text(encoding="utf-8")
    assert "s1" in md_metin
    assert "TOPLAM" in md_metin


# =================================================================================================
# MUTASYON KANITLARI — çivi yeşili tek başına kanıt değildir (CLAUDE.md §6)
# =================================================================================================

def test_MUTASYON_sinif_ayrimi_kaldirilirsa_sinif_bazinda_testi_KIRMIZI_olur():
    """`atiflari_cikar`ın sınıf ayrımını simüle-BOZAN bir mutasyon: beş kümeyi TEK kümede
    birleştirsek `test_sayfa_olc_karisik_sayfada_5_sinif_1_2_dogrulanir_toplam_5_10`ın
    `sinif_bazinda` iddiaları (her sınıf toplam==2) çürür. Testi TEKRAR YAZMADAN, doğrudan
    mutasyonlu bir sözlükle sayfa_olc'un TAM BU İDDİAYA duyarlı olduğunu gösterir."""
    o = _yukle()
    ls_kume, _ = o.ls_files_getir(KOK)
    roadmap_metni = (KOK / "ROADMAP.md").read_text(encoding="utf-8")

    orijinal = o.atiflari_cikar

    def mutasyonlu_atiflari_cikar(icerik):
        birlesik = set()
        for kume in orijinal(icerik).values():
            birlesik |= kume
        # sınıf ayrımı MAHVEDİLDİ: hepsi 'yol' sınıfına yığılıyor, diğer dört sınıf hep BOŞ
        return {"yol": birlesik, "kart": set(), "kalem": set(), "civi": set(), "sha": set()}

    o.atiflari_cikar = mutasyonlu_atiflari_cikar
    try:
        sayfa = {"id": "s1", "kaynak_dosya": "s1.md", "content": _karisik_sayfa_icerigi()}
        sonuc = o.sayfa_olc(sayfa, KOK, ls_kume, roadmap_metni, [])
        with pytest.raises(AssertionError):
            for sinif in ("yol", "kart", "kalem", "civi", "sha"):
                assert sonuc["sinif_bazinda"][sinif]["toplam"] == 2, sinif
    finally:
        o.atiflari_cikar = orijinal


def test_MUTASYON_toplam_sifirda_oran_sifira_cekilirse_uydurma_yasagi_testi_KIRMIZI_olur():
    """İkinci BAĞIMSIZ mutasyon: `toplam==0` durumunda `oran`ı `None` yerine `0.0` döndüren bir
    sayfa_olc ile `test_sayfa_olc_toplam_SIFIRSA_oran_NONE_ve_neden_var_SIFIR_DEGIL` iddiası
    (`oran is None`) çürür — uydurma yasağının (sıfır ≠ bilmiyorum) GERÇEKTEN zorlandığının
    kanıtı, sayfa_olc'un KENDİSİNİ mutasyonlu ÇAĞIRARAK (fonksiyonun içini KOPYALAMADAN)."""
    o = _yukle()
    ls_kume, _ = o.ls_files_getir(KOK)
    roadmap_metni = (KOK / "ROADMAP.md").read_text(encoding="utf-8")
    orijinal = o.sayfa_olc

    def mutasyonlu_sayfa_olc(*a, **k):
        r = orijinal(*a, **k)
        if r["toplam"] == 0:
            r["oran"] = 0.0        # UYDURMA YASAĞI İHLALİ: ölçülemeyen'i sıfırla KARIŞTIRIR
        return r

    o.sayfa_olc = mutasyonlu_sayfa_olc
    try:
        sayfa = {"id": "bos", "kaynak_dosya": "bos.md", "content": "atıf yok."}
        sonuc = o.sayfa_olc(sayfa, KOK, ls_kume, roadmap_metni, [])
        with pytest.raises(AssertionError):
            assert sonuc["oran"] is None
    finally:
        o.sayfa_olc = orijinal
