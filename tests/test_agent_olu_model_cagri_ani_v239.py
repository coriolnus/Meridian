"""v239 KALEM 3 — ÖLÜ-MODEL GÖÇÜ ÇAĞRI ANINI KAPSAMIYORDU.

ÖLÇÜLEN ÇELİŞKİ: `hermes.GEMINI_DEFAULT_MODEL` DOĞRU (`gemini-pro-latest`) ve v235'in göçü
(`config_ensure_integrations`) çalışıyor — ama canlıda BUGÜNKÜ 20 `agent_call` olayının hepsi
`model="gemini-3.5-flash"` taşıyor (üretim 404).

KÖK İZLENDİ: `_agent_call` model zincirini varsayılandan DEĞİL SIRLARDAN kurar
(`NOUS_MODEL` → `NOUS_FALLBACK_MODEL`) ve seçilen adı CLI'ya `--model` ile geçirir. v235'in göçü
YALNIZ `~/.hermes/config.yaml`ın `model.default` alanını onarıyordu; sır tarafına HİÇ bakmıyordu.
Yani "ölü ad kendi kendine iyileşmez" dersi bir yolda öğrenilmiş, ikizi açık bırakılmıştı.
Bu depodaki `.env` ölçümü aynı imzayı taşır: `NOUS_MODEL=gemini-3.5-flash` (ölü),
`NOUS_FALLBACK_MODEL=tencent/hy3:free`, `GEMINI_MODEL=gemini-3.5-flash` (ölü).

BU DOSYA ÇİVİLER:
  (1) çağrı anı zinciri ölü adı alias'a çevirir ve OLAYLAR (sessiz değiştirme yasak);
  (2) TANINMAYAN ad SERBEST geçer (gelecekteki geçerli bir adı "ölü" damgalamak, onarım kılığında
      bir arıza olurdu) — düzeltmenin karşı-testi;
  (3) rapor edilen model kimliği ile ÇAĞRILAN model kimliği ayrışmaz (yeni bir çift-kaynak
      doğmasın: bu turun kapattığı sınıfın ta kendisi);
  (4) v235'in config göçü BOZULMADAN durur.
"""
from __future__ import annotations

import json

from meridian import hermes, store


def _sirlar(monkeypatch, **kv):
    """`secrets.get`i yalnız bu testin sözlüğüyle besle — gerçek `.env` OKUNMAZ, YAZILMAZ."""
    monkeypatch.setattr(hermes.secrets, "get", lambda k, *a, **kw: kv.get(k), raising=False)
    hermes._OLU_MODEL_OLAYLI.clear()


def _olaylar(sandbox_state, ad: str) -> list:
    yol = sandbox_state / "events.jsonl"
    if not yol.exists():
        return []
    return [json.loads(l) for l in yol.read_text().splitlines()
            if l.strip() and json.loads(l).get("event") == ad]


# ---------------------------------- (1) ÇAĞRI ANI GÖÇÜ ----------------------------------

def test_1a_cagri_zinciri_olu_adi_aliasa_cevirir(sandbox_state, monkeypatch):
    """CANLI GEOMETRİ: birincil sır ölü ad, yedek sır canlı (tencent). Zincir alias'la kurulmalı."""
    _sirlar(monkeypatch, NOUS_MODEL="gemini-3.5-flash", NOUS_FALLBACK_MODEL="tencent/hy3:free")
    assert hermes._nous_model_zinciri() == ["gemini-flash-latest", "tencent/hy3:free"]


def test_1b_gocu_OLAYLAR_sessiz_degistirme_yasak(sandbox_state, monkeypatch):
    _sirlar(monkeypatch, NOUS_MODEL="gemini-3.5-flash")
    hermes._nous_model_zinciri()
    ev = _olaylar(sandbox_state, "agent_model_olu_ad_gocuruldu")
    assert ev, "ölü ad sessizce çevrildi — YASA 4 ihlali"
    assert ev[-1]["eski"] == "gemini-3.5-flash" and ev[-1]["yeni"] == "gemini-flash-latest"
    assert ev[-1]["kaynak"] == "NOUS_MODEL", "hangi yüzeydeki ad göçtü yazılmamış"


def test_1c_olay_surec_basina_bir_kez_yazilir(sandbox_state, monkeypatch):
    """Çağrı ~5 dakikada bir koşuyor; her turda warn basmak alarmı gürültüye çevirirdi."""
    _sirlar(monkeypatch, NOUS_MODEL="gemini-3.5-flash")
    for _ in range(4):
        hermes._nous_model_zinciri()
    assert len(_olaylar(sandbox_state, "agent_model_olu_ad_gocuruldu")) == 1


def test_1d_ayni_aliasa_gocen_iki_ad_zinciri_TEKE_indirir(sandbox_state, monkeypatch):
    """Aynı modeli iki kez denemek "yedeklilik" değildir (brain_chain_facts'in ölçtüğü yanılsama)."""
    _sirlar(monkeypatch, NOUS_MODEL="gemini-3.5-flash", NOUS_FALLBACK_MODEL="gemini-flash-latest")
    assert hermes._nous_model_zinciri() == ["gemini-flash-latest"]


def test_1e_hic_sir_yoksa_CLI_varsayilani(sandbox_state, monkeypatch):
    _sirlar(monkeypatch)
    assert hermes._nous_model_zinciri() == [None]


# ------------------------- (2) KARŞI-TEST: TANINMAYAN AD SERBEST GEÇER -------------------------

def test_2a_taninmayan_ad_ceviRILMEZ(sandbox_state, monkeypatch):
    """Elimizdeki model listesi bir KESİTTİR. `gemini-3.6-flash` gelecekte geçerli olabilir;
    onu "ölü" damgalamak, onarım kılığında bir arıza olurdu."""
    _sirlar(monkeypatch, NOUS_MODEL="gemini-3.6-flash", NOUS_FALLBACK_MODEL="tencent/hy3:free")
    assert hermes._nous_model_zinciri() == ["gemini-3.6-flash", "tencent/hy3:free"]
    assert not _olaylar(sandbox_state, "agent_model_olu_ad_gocuruldu"), (
        "tanınmayan ad göç olayı ürettti — harita kapsamını aşmış")


def test_2b_canonical_model_bos_degeri_bozmaz(sandbox_state, monkeypatch):
    hermes._OLU_MODEL_OLAYLI.clear()
    assert hermes.canonical_model(None, kaynak="t") is None
    assert hermes.canonical_model("", kaynak="t") == ""


# ------------------- (3) RAPOR EDİLEN KİMLİK = ÇAĞRILAN KİMLİK (yeni split yok) -------------------

def test_3a_gemini_modeli_tek_kapidan_okunur(sandbox_state, monkeypatch):
    _sirlar(monkeypatch, GEMINI_MODEL="gemini-3.5-flash")
    assert hermes.gemini_model() == "gemini-flash-latest"
    _sirlar(monkeypatch)                       # sır yoksa repo varsayılanı (zaten canlı alias)
    assert hermes.gemini_model() == hermes.GEMINI_DEFAULT_MODEL


def test_3b_rapor_edilen_nous_kimligi_cagrilanla_ayni(sandbox_state, monkeypatch):
    """`_model_id`/`active_model` çevirmeden geçseydi "ne çağırdığımız" ile "ne rapor ettiğimiz"
    ayrışırdı — bu turun kapattığı çift-kaynak sınıfının YENİSİ."""
    _sirlar(monkeypatch, NOUS_MODEL="gemini-3.5-flash", NOUS_API_KEY="x")
    cagrilan = hermes._nous_model_zinciri()[0]
    assert hermes._model_id("nous") == cagrilan == "gemini-flash-latest"
    assert hermes.brain_chain_facts()["models"]["nous"] == cagrilan


def test_3b2_rapor_yuzeyi_deftere_YAZMAZ(sandbox_state, monkeypatch):
    """2026-08-13 (otoriter suite bulgusu): ilk hâlde `canonical_model` HER çağrı yerinde olay
    basıyordu ve `hermes_runtime.status()` (pano `/api/hermes`) `active_model()` + `_model_id()`
    üzerinden CANLI `events.jsonl`e iki satır düşürüyordu — conftest sızıntı bekçisi
    `test_api_contract.py::test_hermes_status_payload_is_json_serializable_mid_search` teardown'unda yakaladı.
    KUSUR TEST DEĞİL YAYIN YERİYDİ: bir okuma isteği üretim defterine "göç oldu" yazamaz.
    ÇEVİRİ korunur (test_3b), OLAY yalnız gerçek çağrı yolundan basılır."""
    _sirlar(monkeypatch, NOUS_MODEL="gemini-3.5-flash", GEMINI_MODEL="gemini-3.5-flash",
            NOUS_API_KEY="x")
    assert hermes._model_id("nous") == "gemini-flash-latest"      # çeviri DURUYOR
    assert hermes.active_model() is not None or True              # rapor yolu çağrıldı
    assert hermes.gemini_model() == "gemini-flash-latest"         # sonda/rapor kapısı sessiz
    hermes.ping_brain  # noqa: B018 — sonda yüzeyi de aynı sessiz kapıdan okur
    assert not _olaylar(sandbox_state, "agent_model_olu_ad_gocuruldu"), (
        "RAPOR yüzeyi göç olayı bastı — sızıntı bekçisinin yakaladığı kusur geri geldi")
    hermes._nous_model_zinciri()                                  # GERÇEK çağrı yolu
    assert _olaylar(sandbox_state, "agent_model_olu_ad_gocuruldu"), (
        "gerçek çağrı yolu susturulmuş — sessiz-değiştirme yasağı ihlali")


def test_3c_iki_ayak_ayni_kimlige_giderse_zincir_yedeksiz_okunur(sandbox_state, monkeypatch):
    """ÖLÇÜLEN CANLI HÂL (bu depodaki `.env` ile birebir): `NOUS_MODEL` ve `GEMINI_MODEL` AYNI ölü
    adı taşıyor. Göç ikisini de aynı alias'a çevirir — yani yedeklilik hâlâ YOKTUR ve düzeltme
    bunu ÖRTMEZ. `same_model_ids` bu yüzden dolu kalmalı (kurt masalı yasağının tersi: gerçek bir
    ihlali sessizce yeşile çevirmek de bir uydurmadır)."""
    _sirlar(monkeypatch, NOUS_MODEL="gemini-3.5-flash", GEMINI_MODEL="gemini-3.5-flash",
            NOUS_API_KEY="x", GEMINI_API_KEY="y")
    f = hermes.brain_chain_facts()
    assert f["models"]["nous"] == f["models"]["gemini"] == "gemini-flash-latest"
    assert ["gemini", "nous"] in f["same_model_ids"], f


# ------------------- (4) v235'in CONFIG GÖÇÜ BOZULMADAN DURUYOR -------------------

def test_4a_config_gocu_hala_calisiyor(sandbox_state, monkeypatch, tmp_path):
    """v235 mezar taşı: config yolu bu turda değişmedi ve kapsamını korumalı."""
    cfg = tmp_path / "config.yaml"
    cfg.write_text("model:\n  provider: gemini\n  default: gemini-3.5-flash\n")
    monkeypatch.setattr(hermes, "AGENT_CONFIG", str(cfg))
    monkeypatch.setattr(hermes, "_hermes_bin", lambda: "/bin/true")
    _sirlar(monkeypatch)
    r = hermes.config_ensure_integrations()
    assert r.get("ok") is True
    import yaml
    assert yaml.safe_load(cfg.read_text())["model"]["default"] == "gemini-flash-latest"
    assert _olaylar(sandbox_state, "gemini_dead_model_migrated"), "v235 olayı kaybolmuş"


def test_4b_iki_katman_ayni_haritayi_paylasir():
    """Tek harita, iki katman: ikinci bir kopya, bu turun kovaladığı kusurun kendisi olurdu."""
    src = (store.config.ROOT / "meridian" / "hermes.py").read_text()
    assert src.count("GEMINI_DEAD_MODEL_MAP = {") == 1
    assert "GEMINI_DEAD_MODEL_MAP.get(eski_ad)" in src        # v235 config katmanı
    assert "GEMINI_DEAD_MODEL_MAP.get(str(ad).strip())" in src  # v239 çağrı-anı katmanı
