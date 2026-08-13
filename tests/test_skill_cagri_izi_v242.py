"""test_skill_cagri_izi_v242.py — SKILL ÇAĞRI İZİ: GERİLEME ONARIMI + AJAN SAYACI + İZOLASYON (2026-08-13).

Kaynak: `docs/DENETIM-SKILL-CAGRI-IZI-2026-08-13.md` (salt-okuma canlı denetim; her iddia
`dosya:satır` ya da canlı komut çıktısıyla bağlı). Bu dosya o denetimin DÖRT bulgusunu kilitler.

ÖLÇÜLMÜŞ DURUM (denetim §0, canlı A1):
    30/30 skill LLM'e SUNULUYOR · 13'ü `-s` ile isteme giriyor (6.839 enjeksiyon) ·
    4'ünü LLM KENDİ açmış (11 `skill_view`) · bunların Meridian defterlerindeki izi: **0**.

DÖRT SÖZLEŞME:

  1. GERİLEME ONARIMI (§2.4/§B1). `nous_call_skills` olayı çağrı başına `names: [...]` tam listesini
     yazıyordu; son basıldığı an 2026-07-20T10:06:49. `_agent_call` yeniden yazılırken liste
     `preloaded: <sayı>`ya ÇÖKTÜ. Adlar geri geldi — hem olay defterine hem telemetri defterine,
     TAVANLI ve tavan ADIYLA sayılarak (sessiz kırpma yasak).

  2. AJANIN KENDİ SAYACI (§B3/Ö2). `~/.hermes/skills/.usage.json` sorunun cevabını taşıyor ve repoda
     onu okuyan tek satır kod YOKTU. Bağlandı — ve İKİ SAYAÇ AYRI TAŞINIR: `use_count` "BİZ isteme
     bastık" (`-s`), `view_count` "MODEL kendi açtı" (`skill_view`). Toplanmaları teşhisi çökertir.

  3. İZOLASYON SIZINTISI (§1.4/§B4). Sprint kum havuzu, canlının PAYLAŞIMLI ajan skill dizinini
     buduyordu (canlı kanıt: `15:20:13 agent_skills_synced pruned=[… dört fmp=req skill]`, 59 sn
     sonra canlı onarım). Kum havuzu artık o dizini DEĞİŞTİRMEZ — ve atlama SESSİZ DEĞİLDİR.

  4. YANILTICI ALAN (§B6). `agent_skills_synced.linked` = "YENİ kurulan symlink"ti, ama
     `agent_skill_coverage()` aynı sözcüğü "bağlı TOPLAM" anlamında kullanıyor. Denetimin kendi
     ön-ölçümü bu yüzden yanlış okundu. Olay tarafı `yeni_baglanan`a çevrildi + kapsam yazılıyor.

Alt süreç ve ağ SAPLIDIR; fikstürlerde gerçek anahtar/token YOKTUR. Canlı `~/.hermes` OKUNMAZ:
`AGENT_SKILLS_DIR` her testte tmp'ye yamalanır (aksi halde test operatörün makinesine bağlanırdı ve
geçtiğinde hiçbir şey kanıtlamazdı — `sandbox_state`in `AGENT_CONFIG` dersi).
"""
import json
import os
import subprocess
from pathlib import Path

import pytest

from meridian import agent_telemetry as at, analytics, config, hermes, skills, sprint, store

REPO_SKILLS = Path(hermes.__file__).resolve().parent.parent / "skills"
# Canlı vakanın gerçek aktörleri: `canslim-screener` kum havuzunda kapanan dört `fmp=req` skill'den
# biri, `vcp-screener` hem canlıda hem kum havuzunda açık. İkisinin de klasörü depoda DURUYOR —
# `sync_agent_skills` yalnız var olan klasörü symlink'ler, yani uydurma ad testi sessizce boşa
# çıkarırdı.
KAPALI_SANDBOX = "canslim-screener"
ACIK = "vcp-screener"


class _Kosum:
    """subprocess.run sonucu taklidi — süreç YOK, ağ YOK (v197 fikstürünün ikizi)."""

    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode, self.stdout, self.stderr = returncode, stdout, stderr


@pytest.fixture
def ajan(sandbox_state, monkeypatch):
    """Yerel ajan düzeneği: saplı alt süreç + tek modelli zincir + skill senkronu devre dışı."""
    monkeypatch.setattr(hermes, "_hermes_bin", lambda: "/sahte/hermes")
    monkeypatch.setattr(hermes, "sync_agent_skills", lambda: None)
    monkeypatch.setattr(hermes.secrets, "get", lambda k: {"NOUS_MODEL": "model-x"}.get(k))
    monkeypatch.setattr(subprocess, "run", lambda cmd, **kw: _Kosum(0, '{"reviews": []}\n', ""))
    return sandbox_state


@pytest.fixture
def ajan_dizini(sandbox_state, tmp_path, monkeypatch):
    """PAYLAŞIMLI ajan skill dizininin tmp ikizi — canlı `~/.hermes/skills`e ASLA dokunulmaz.

    `sandbox_state` BAĞIMLILIĞI KOLAYLIK DEĞİL KAPIDIR (`vaka` fikstürünün emsali): bu yolun
    okuyucusu YASA 4 gereği `obs.warn` basıyor ve sandbox olmadan o satır CANLI `events.jsonl`e
    düşerdi — testin kendi artefaktı operatöre üretim arızası gibi görünürdü."""
    d = tmp_path / "hermes_skills"
    d.mkdir()
    monkeypatch.setattr(hermes, "AGENT_SKILLS_DIR", str(d))
    return d


@pytest.fixture(autouse=True)
def _uyari_hafizasi_sifirla(monkeypatch):
    """"Süreç başına bir uyarı" hafızası SÜREÇ-İÇİDİR — testler arası taşınırsa ikinci testin
    ölçtüğü şey dedektör değil SIRA olur (conftest'teki `_MODUL_DURUMLARI` dersinin aynısı)."""
    monkeypatch.setattr(skills, "_AJAN_KULLANIM_UYARILDI", set())


def _olaylar(ad: str) -> list:
    return [e for e in store.read_jsonl("events.jsonl") if e.get("event") == ad]


def _katalog_sap(monkeypatch, enabled: set, hepsi=(ACIK, KAPALI_SANDBOX)):
    """`skills.catalog()` sapı — kayıt defteri/atıf analitiği bu testlerin konusu değil."""
    monkeypatch.setattr(skills, "catalog",
                        lambda: [{"name": n, "enabled": n in enabled} for n in hepsi])


def _kum_havuzuna_gir(monkeypatch, tmp_path) -> Path:
    """`config.STATE`i GERÇEK kum havuzu yoluna taşı: `<canlı state>/sprint/<sid>/state`.

    Bayrak yamalamak YETMEZ ve bu bilinçli: `MERIDIAN_SPRINT_SBROOT` yalnız systemd yolunda yazılır,
    `Popen` düşüş yolunda yoktur — bayrağa-tek dayanan bir test, sızıntının açık kaldığı yolu hiç
    ölçmezdi. Burada YAPI kurulur, bayrak kurulmaz."""
    sb = tmp_path / "state" / "sprint" / "20260813-151752" / "state"
    sb.mkdir(parents=True)
    monkeypatch.setattr(config, "STATE", sb)
    monkeypatch.delenv("MERIDIAN_SPRINT_SBROOT", raising=False)
    return sb


# ================================================================= 1) KAYBEDİLEN İZ GERİ GELDİ

def test_agent_call_olayi_skill_ADLARINI_yaziyor(ajan):
    """§2.4'ün onarımı: olay defteri artık "kaç tane" DEĞİL "hangileri" de söylüyor."""
    hermes._agent_call("istem", preload=(ACIK, "position-sizer"), kind="review")
    ev = _olaylar("agent_call")[-1]
    assert ev["skills"] == [ACIK, "position-sizer"], "ön-yüklenen adlar olaya yazılmadı (gerileme geri döndü)"
    assert ev["preloaded"] == 2, "eski sayı alanı SİLİNMEDİ — mevcut okuyucular kırılmamalı"
    assert ev["skills_kirpildi_n"] == 0, "kırpma sayacı her satırda yazılmalı (yokluk 'sıfır sanılır')"


def test_telemetri_defteri_de_adlari_tasiyor_sayinin_YANINDA(ajan):
    """İki defter `iz_id` ile birleşse de her biri TEK BAŞINA okunabilir kalmalı (§Ö1 simetrik satır)."""
    hermes._agent_call("istem", preload=(ACIK,), kind="review")
    r = store.read_jsonl(at.CAGRI_DEFTERI)[-1]
    assert r["on_yukleme"] == [ACIK]
    assert r["on_yukleme_n"] == 1, "sayı alanı yerinde duruyor (liste onun YERİNE değil YANINA geldi)"


def test_on_ucus_onariminda_GERCEKTEN_GONDERILEN_liste_yazilir(ajan, monkeypatch):
    """`Unknown skill(s)` onarımı listeyi KÜÇÜLTÜR. Defter, istenen listeyi değil GÖNDERİLENİ yazmalı:
    aksi halde "bu çağrıda hangi skill vardı" sorusu yanlış cevaplanır (v190 onarım yolu)."""
    sonuclar = [_Kosum(1, "Error: Unknown skill(s): olmayan-skill\n", ""),
                _Kosum(0, '{"reviews": []}\n', "")]
    it = iter(sonuclar)
    monkeypatch.setattr(subprocess, "run", lambda cmd, **kw: next(it))
    hermes._agent_call("istem", preload=(ACIK, "olmayan-skill"), kind="review")
    satirlar = store.read_jsonl(at.CAGRI_DEFTERI)
    assert satirlar[0]["on_yukleme"] == [ACIK, "olmayan-skill"], "düşen koşum TAM listeyi taşımalı"
    assert satirlar[-1]["on_yukleme"] == [ACIK], "onarımdan sonraki koşum KÜÇÜLMÜŞ listeyi taşımalı"
    ev = _olaylar("agent_call")[-1]
    assert ev["skills"] == [ACIK] and ev["preloaded"] == 1


def test_tavan_ADIYLA_sayilir_sessiz_kirpma_yok():
    """Hacim ölçüldü (proposal-8 → 208 bayt), tavan 12 bugünün yolunda hiç tetiklenmez. Tetiklendiği
    gün SUSMAZ: kırpılan sayı yazılır. Sessiz kırpma, defteri yalancı yapardı."""
    adlar, kirpilan = at.skill_adlari([f"skill-{i}" for i in range(at.SKILL_AD_TAVANI + 3)])
    assert len(adlar) == at.SKILL_AD_TAVANI and kirpilan == 3
    assert at.skill_adlari([ACIK]) == ([ACIK], 0)
    assert at.skill_adlari(None) == ([], 0)
    # TAVAN GERÇEK ÖN-YÜKLEMENİN ÜSTÜNDE: `_skill_preload` 8'de kapanıyor, tavan 12 → bugün asla
    # kırpma olmaz. Tavan bir gün 8'in ALTINA düşerse bu satır uyarır (sessiz veri kaybı olurdu).
    assert at.SKILL_AD_TAVANI > 8


def test_kaydet_kirpma_sayacini_deftere_yaziyor(sandbox_state):
    """Kırpma telemetri defterinde de ADIYLA görünür (iki defter aynı kuraldan geçer)."""
    at.kaydet(kind="review", model="m", deneme=1, alt=0, sure_ms=1.0, sonuc_sinifi=at.SINIF_DOLU,
              on_yukleme_n=20, on_yukleme=[f"s{i}" for i in range(20)], stdout="x")
    r = store.read_jsonl(at.CAGRI_DEFTERI)[-1]
    assert len(r["on_yukleme"]) == at.SKILL_AD_TAVANI
    assert r["on_yukleme_kirpildi_n"] == 20 - at.SKILL_AD_TAVANI


def test_on_yukleme_kavrami_OLMAYAN_yolda_alan_hic_yazilmaz(sandbox_state):
    """HTTP taşıyıcısının ön-yükleme kavramı YOKTUR. Boş liste yazmak "ölçüldü, hiç skill yoktu"
    diye okunurdu — bu depoda tekrar eden "eksik alan = sıfır sanılır" sınıfının aynası."""
    at.kaydet(kind="system_eval", model="m", deneme=1, alt=0, sure_ms=1.0,
              sonuc_sinifi=at.SINIF_DOLU, tasiyici=at.TASIYICI_HTTP, stdout="x")
    assert "on_yukleme" not in store.read_jsonl(at.CAGRI_DEFTERI)[-1]


# ============================================== 2) AJANIN KENDİ SAYACI — İKİ OLGU, İKİ AYRI ALAN

def _usage_yaz(dizin: Path, veri: dict) -> None:
    (dizin / skills.AJAN_KULLANIM_DOSYASI).write_text(json.dumps(veri), encoding="utf-8")


def test_enjeksiyon_ile_MODELIN_KENDI_ACMASI_ayri_alanlarda(ajan_dizini):
    """Denetimin çekirdek ayrımı: `use_count` = BİZ isteme bastık (`-s`), `view_count` = MODEL kendi
    açtı (`skill_view`). Canlı ölçüm 6.839'a karşı 11 — toplansaydı asıl bulgu (model skill
    araçlarını fiilen kullanmıyor) görünmez olurdu."""
    _usage_yaz(ajan_dizini, {ACIK: {"use_count": 1097, "view_count": 3,
                                    "last_used_at": "2026-08-13T17:13:00+00:00",
                                    "last_viewed_at": "2026-08-13T14:18:05+00:00"}})
    k = skills.ajan_kullanim()
    assert k["ok"] is True and k["neden"] is None
    r = k["kayitlar"][ACIK]
    assert r["ajan_yukleme_n"] == 1097 and r["ajan_acilma_n"] == 3
    assert r["ajan_yukleme_n"] + r["ajan_acilma_n"] != r["ajan_yukleme_n"], "iki sayaç ayrı olgudur"
    assert r["son_acilma"] == "2026-08-13T14:18:05+00:00"


def test_katalog_ajan_katmanini_tasiyor(ajan_dizini, monkeypatch):
    """§B5: `last_run` deterministik boru hattını damgalar, LLM katmanının karşılığı YOKTU."""
    _usage_yaz(ajan_dizini, {ACIK: {"use_count": 5, "view_count": 2}})
    monkeypatch.setattr(skills, "_skill_descriptions", lambda: {ACIK: "x", KAPALI_SANDBOX: "y"})
    monkeypatch.setattr(skills, "registry", lambda: {"skills": {}})
    monkeypatch.setattr(analytics, "skill_attribution", lambda: {"skills": []})
    cat = {c["name"]: c for c in skills.catalog()}
    assert cat[ACIK]["ajan_yukleme_n"] == 5 and cat[ACIK]["ajan_acilma_n"] == 2
    assert cat[ACIK]["ajan_kullanim_neden"] is None
    # KAYIT YOKLUĞU 'SIFIR' DEĞİLDİR: sayaç okundu ama bu ad orada yok → None + NEDEN.
    assert cat[KAPALI_SANDBOX]["ajan_yukleme_n"] is None
    assert "kayıtlı değil" in cat[KAPALI_SANDBOX]["ajan_kullanim_neden"]


def test_dosya_yoksa_None_ve_NEDEN_uydurma_yok(ajan_dizini):
    """UYDURMA YASAĞI: ölçülemeyen değer 0 değil None, ve nedeni yazılı."""
    k = skills.ajan_kullanim()
    assert k["ok"] is False and k["kayitlar"] == {}
    assert k["neden"] and "yok" in k["neden"]


def test_ucuncu_taraf_SEMASI_degisirse_uydurulmaz(ajan_dizini):
    """Dosyanın sahibi Hermes CLI'dir; şema bizim sözleşmemiz DEĞİL. Beklenmedik şekil sessizce
    'sıfır kullanım'a çevrilmez."""
    (ajan_dizini / skills.AJAN_KULLANIM_DOSYASI).write_text("[1, 2, 3]", encoding="utf-8")
    k = skills.ajan_kullanim()
    assert k["ok"] is False and "şema" in k["neden"]

    (ajan_dizini / skills.AJAN_KULLANIM_DOSYASI).write_text("{bozuk json", encoding="utf-8")
    k2 = skills.ajan_kullanim()
    assert k2["ok"] is False and k2["kayitlar"] == {}

    # ALAN TİPİ de doğrulanır: sayı olmayan bir sayaç None'dır, 0 DEĞİL.
    _usage_yaz(ajan_dizini, {ACIK: {"use_count": "cok", "view_count": None}})
    r = skills.ajan_kullanim()["kayitlar"][ACIK]
    assert r["ajan_yukleme_n"] is None and r["ajan_acilma_n"] is None

    # `bool` DIŞLANIR: Python'da `isinstance(True, int)` DOĞRUDUR. Sayaç bir gün bayrağa çevrilirse
    # (`"use_count": true`) tip kontrolünden geçer ve panoya "1 kullanım" diye yazılırdı — üçüncü
    # taraf şemasının değişmesinin uydurma ÜRETMESİ tam olarak bu testin yasakladığı şey.
    _usage_yaz(ajan_dizini, {ACIK: {"use_count": True, "view_count": False}})
    r2 = skills.ajan_kullanim()["kayitlar"][ACIK]
    assert r2["ajan_yukleme_n"] is None and r2["ajan_acilma_n"] is None


def test_okunamayan_sayac_SESSIZ_kalmaz(ajan_dizini):
    """YASA 4: alanların None kalması "hiç kullanılmadı" diye okunurdu — neden ADIYLA olaylanır."""
    skills.ajan_kullanim()                               # hafıza `_uyari_hafizasi_sifirla` ile temiz
    ev = _olaylar("ajan_skill_kullanim_okunamadi")
    assert ev and ev[-1]["neden"] == "dosya_yok"
    skills.ajan_kullanim()
    assert len(_olaylar("ajan_skill_kullanim_okunamadi")) == 1, "süreç başına BİR uyarı (defter gürültüsü yok)"


# ================================================ 3) İZOLASYON: KUM HAVUZU CANLI DİZİNE DOKUNAMAZ

def test_kum_havuzu_canlinin_symlinkini_SOKEMEZ(ajan_dizini, monkeypatch, tmp_path):
    """CANLI VAKANIN KALICI TESTİ (§B4). Kum havuzunda FMP anahtarı yok → `canslim-screener` kapalı
    → eski kod onu canlının PAYLAŞIMLI dizininden söküyordu ve canlı ajan onu bir sonraki senkrona
    kadar GÖRMÜYORDU."""
    os.symlink(REPO_SKILLS / KAPALI_SANDBOX, ajan_dizini / KAPALI_SANDBOX)
    _katalog_sap(monkeypatch, enabled={ACIK})            # kum havuzunun (anahtarsız) enabled seti
    _kum_havuzuna_gir(monkeypatch, tmp_path)

    out = hermes.sync_agent_skills()

    assert (ajan_dizini / KAPALI_SANDBOX).is_symlink(), "kum havuzu canlının symlink'ini SÖKTÜ (sızıntı geri döndü)"
    assert not (ajan_dizini / ACIK).exists(), "kum havuzu paylaşımlı dizine YENİ link de kuramaz"
    assert out["atlandi"] == "kum_havuzu"
    assert out["olurdu_sokulecek"] == [KAPALI_SANDBOX] and out["olurdu_baglanacak"] == [ACIK]
    assert out["pruned"] == [] and out["yeni_baglanan"] == []


def test_atlama_SESSIZ_degil_ne_olurdu_defterde(ajan_dizini, monkeypatch, tmp_path):
    """Fail-visible: engellenen değişiklik ADIYLA yazılır, yoksa sızıntı kapandı mı bilinemezdi."""
    os.symlink(REPO_SKILLS / KAPALI_SANDBOX, ajan_dizini / KAPALI_SANDBOX)
    _katalog_sap(monkeypatch, enabled={ACIK})
    _kum_havuzuna_gir(monkeypatch, tmp_path)
    hermes.sync_agent_skills()
    ev = _olaylar("agent_skills_sync_atlandi_kum_havuzu")
    assert ev, "atlama olayı yazılmadı — sessiz bir kapı, açık bir kapıdan ayırt edilemez"
    assert ev[-1]["olurdu_sokulecek"] == [KAPALI_SANDBOX] and ev[-1]["n_sokulecek"] == 1


def test_degisiklik_YOKSA_olay_da_yok(ajan_dizini, monkeypatch, tmp_path):
    """Kum havuzu saatlerce koşar ve senkron döngüsel çağrılır: engellenecek bir şey yokken her
    turda olay basmak, kum havuzunun kendi defterini gürültüyle doldururdu."""
    os.symlink(REPO_SKILLS / ACIK, ajan_dizini / ACIK)
    _katalog_sap(monkeypatch, enabled={ACIK})            # zaten bağlı, sökülecek de yok
    _kum_havuzuna_gir(monkeypatch, tmp_path)
    hermes.sync_agent_skills()
    assert _olaylar("agent_skills_sync_atlandi_kum_havuzu") == []


def test_kum_havuzu_dizini_YARATMAZ_bile(sandbox_state, monkeypatch, tmp_path):
    """`makedirs` de bir mutasyondur: olmayan bir `~/.hermes/skills`i kum havuzunun yaratması,
    canlının hiç kurulmamış ajan yüzeyini sessizce var etmek olurdu."""
    yok = tmp_path / "hic-olmayan" / "skills"
    monkeypatch.setattr(hermes, "AGENT_SKILLS_DIR", str(yok))
    _katalog_sap(monkeypatch, enabled={ACIK})
    _kum_havuzuna_gir(monkeypatch, tmp_path)
    hermes.sync_agent_skills()
    assert not yok.exists()


def test_KUM_HAVUZU_DISINDA_sokme_AYNEN_calisiyor(ajan_dizini, monkeypatch):
    """KAPININ KARŞI YÜZÜ. Canlı öz-onarımı kapatmak, sızıntıyı düzeltmek değil yerini değiştirmek
    olurdu: 8 kapalı skill'in ajanda aktif kalması (2026-07 vakası) tam da bu senkronun varlık
    sebebidir."""
    os.symlink(REPO_SKILLS / KAPALI_SANDBOX, ajan_dizini / KAPALI_SANDBOX)
    _katalog_sap(monkeypatch, enabled={ACIK})
    assert sprint.kum_havuzunda() is False              # `sandbox_state` bir SPRINT kum havuzu DEĞİL

    out = hermes.sync_agent_skills()

    assert out["pruned"] == [KAPALI_SANDBOX] and out["yeni_baglanan"] == [ACIK]
    assert not (ajan_dizini / KAPALI_SANDBOX).exists() and (ajan_dizini / ACIK).is_symlink()


def test_kum_havuzu_olcutu_YAPISAL_bayrak_degil(monkeypatch, tmp_path):
    """`MERIDIAN_SPRINT_SBROOT` yalnız systemd yolunda yazılır; `Popen` düşüş yolunda YOK. Ölçüt
    bayrağa dayansaydı sızıntı tam da düşüş yolunda açık kalırdı."""
    monkeypatch.delenv("MERIDIAN_SPRINT_SBROOT", raising=False)
    sb = tmp_path / "state" / "sprint" / "20260813-151752" / "state"
    sb.mkdir(parents=True)
    monkeypatch.setattr(config, "STATE", sb)
    assert sprint.kum_havuzunda() is True, "yapısal ölçüt kum havuzunu tanımadı (Popen yolu açık kalır)"

    canli = tmp_path / "state"
    monkeypatch.setattr(config, "STATE", canli)
    assert sprint.kum_havuzunda() is False, "canlı state kum havuzu sanıldı — öz-onarım dururdu"

    # Bayrak VARSA ikinci kanıttır (systemd yolu): yapı tanımasa bile kapı kapanır.
    sbroot = tmp_path / "baska" / "yer"
    (sbroot / "state").mkdir(parents=True)
    monkeypatch.setenv("MERIDIAN_SPRINT_SBROOT", str(sbroot))
    monkeypatch.setattr(config, "STATE", sbroot / "state")
    assert sprint.kum_havuzunda() is True


# ================================================================ 4) `linked` ARTIK YANILTMIYOR

def test_olay_yeni_baglanan_ve_KAPSAM_yaziyor(ajan_dizini, monkeypatch):
    """§B6: `linked: 4` "yalnız 4 skill bağlı" diye okunuyordu (denetimin kendi ön-ölçümü dâhil).
    Olayı TEK BAŞINA okuyan biri artık toplam kapsamı da görüyor."""
    os.symlink(REPO_SKILLS / ACIK, ajan_dizini / ACIK)   # biri zaten bağlı → yeni bağlanan yalnız 1
    _katalog_sap(monkeypatch, enabled={ACIK, KAPALI_SANDBOX})

    hermes.sync_agent_skills()

    ev = _olaylar("agent_skills_synced")[-1]
    assert ev["yeni_baglanan"] == 1 and ev["yeni_baglanan_adlar"] == [KAPALI_SANDBOX]
    assert ev["kapsam"] == "2/2" and ev["bagli_toplam"] == 2 and ev["enabled"] == 2
    assert "linked" not in ev, ("`linked` olayda geri döndü — aynı ad `agent_skill_coverage()`te "
                               "TOPLAM anlamına geliyor ve iki anlam yine karışır")


def test_kapsam_alanlari_coverage_ile_TUTARLI(ajan_dizini, monkeypatch):
    """İki yüzey aynı sayıyı söylemeli: olaydaki `bagli_toplam` ile panonun okuduğu
    `agent_skill_coverage()["linked"]` ayrışırsa hangisinin doğru olduğu yine bilinemez."""
    _katalog_sap(monkeypatch, enabled={ACIK, KAPALI_SANDBOX})
    out = hermes.sync_agent_skills()
    cov = hermes.agent_skill_coverage()
    assert out["bagli_toplam"] == cov["linked"] == cov["enabled"] == 2
    assert cov["stale_linked"] == 0 and cov["missing"] == []
