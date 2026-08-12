"""test_gemini_olu_model_gocu_v235.py — Gemini HTTP 404 kökünün kapanışı (2026-08-12).

CANLI KÖK (Rol-1 canlıdan ölçtü): anahtar SAĞLAM (models-list HTTP 200) ama üretim çağrısı 404 —
canlı `~/.hermes/config.yaml` `model.default: gemini-3.5-flash` taşıyordu ve o ad Google
listesinden KALKMIŞTI. Repo varsayılanı da (çıplak `gemini-3.1-pro`) o listede HİÇ olmayan bir
addı (yalnız `-preview` türevi var) — aynı 404 sınıfının bekleyen ikinci kopyası.

İKİ ONARIM TEK STRATEJİ (yeniden-adlandırmaya dayanıklılık):
  (1) `GEMINI_DEFAULT_MODEL` SABİT ALIAS'a geçti (`gemini-pro-latest`) — operatörün 3.1-pro
      tercihi (2026-07-19) alias üzerinden korunur; alias şu an 3.1-pro-preview'ı gösteriyor.
  (2) `config_ensure_integrations` ajan config'inde DURAN bilinen-ölü adı alias'a GÖÇÜRÜR ve
      OLAYLAR (`gemini_dead_model_migrated` eski→yeni) — sessiz değiştirme YASAK.

TANINMAYAN ADLAR SERBEST GEÇER: elimizdeki model listesi KESİTTİ (head-12) ve Google adlandırma
döngüsü dönüyor (resmî örnekler 3.6-flash'a geçti). Göç haritası yalnız bilinen-ölü adlar içindir;
"listede yok → ölü" çıkarımı gelecekteki geçerli bir modeli kırardı. Bu dosyada GERÇEK API çağrısı
YOKTUR — canlı doğrulama Rol-1'in dağıtım-sonrası işidir.
"""
import yaml

from meridian import store, hermes


def _olaylar(ad):
    return [r for r in store.read_jsonl("events.jsonl") if r.get("event") == ad]


def _hazirla(monkeypatch, model_default, provider="gemini"):
    """Sahte ajan config'ini sandbox'ın AGENT_CONFIG yoluna yazar; ikiliyi 'kurulu' yapar.
    (`sandbox_state` AGENT_CONFIG'i tmp'ye yönlendirir — gerçek ~/.hermes'e dokunulmaz.)"""
    monkeypatch.setattr(hermes, "_hermes_bin", lambda: "/fake/hermes")
    cfg = {"model": {"provider": provider}}
    if model_default is not None:
        cfg["model"]["default"] = model_default
    with open(hermes.AGENT_CONFIG, "w") as fh:
        yaml.safe_dump(cfg, fh)


def _yazilan():
    with open(hermes.AGENT_CONFIG) as fh:
        return yaml.safe_load(fh)


def test_olu_ad_yazimda_aliasa_gocer_ve_olaylanir(sandbox_state, monkeypatch):
    """Canlı vakanın birebir kapanışı: config'te duran gemini-3.5-flash yazımda flash alias'ına
    çevrilir (hızlı-görev ROLÜ korunur), değişiklik listede görünür ve olay eski→yeni taşır."""
    _hazirla(monkeypatch, "gemini-3.5-flash")
    r = hermes.config_ensure_integrations()
    assert r["ok"]
    assert "model.default(gemini-3.5-flash→gemini-flash-latest)" in r["changed"]
    assert _yazilan()["model"]["default"] == "gemini-flash-latest"
    ev = _olaylar("gemini_dead_model_migrated")
    assert len(ev) == 1, "göç OLAYSIZ olamaz — sessiz değiştirme yasak"
    assert ev[0]["eski"] == "gemini-3.5-flash" and ev[0]["yeni"] == "gemini-flash-latest"
    # göç TEK ATIMLIK: ikinci koşum ne yeniden yazar ne yeniden olaylar (churn/olay seli yok)
    r2 = hermes.config_ensure_integrations()
    assert r2["ok"] and r2["changed"] == []
    assert len(_olaylar("gemini_dead_model_migrated")) == 1


def test_eski_repo_varsayilani_ciplak_31pro_da_gocer(sandbox_state, monkeypatch):
    """Aynı 404 sınıfının ikinci kopyası: config'e bir yolla yazılmış çıplak gemini-3.1-pro da
    pro alias'ına taşınır — operatör tercihi (pro sınıfı) alias üzerinden korunur."""
    _hazirla(monkeypatch, "gemini-3.1-pro")
    r = hermes.config_ensure_integrations()
    assert r["ok"]
    assert _yazilan()["model"]["default"] == "gemini-pro-latest"
    ev = _olaylar("gemini_dead_model_migrated")
    assert ev and ev[0]["eski"] == "gemini-3.1-pro" and ev[0]["yeni"] == "gemini-pro-latest"


def test_taninmayan_ad_serbest_gecer(sandbox_state, monkeypatch):
    """Gelecek modeli kırma yasağı: haritada olmayan bir ad (ör. resmî örneklere yeni giren
    gemini-3.6-flash) ÖLÜ DAMGALANMAZ — değer aynen korunur, olay basılmaz. Elimizdeki liste
    kesitti; 'listede görmedim → ölü' çıkarımı yanlış onarım olurdu (uydurma yasağı)."""
    _hazirla(monkeypatch, "gemini-3.6-flash")
    r = hermes.config_ensure_integrations()
    assert r["ok"]
    assert _yazilan()["model"]["default"] == "gemini-3.6-flash"
    assert not any(c.startswith("model.default(") for c in r["changed"])
    assert _olaylar("gemini_dead_model_migrated") == []


def test_model_blogu_yoksa_goc_sessizce_atlanir(sandbox_state, monkeypatch):
    """model bloğu/default alanı olmayan config göçü tetiklemez — mevcut idempotans sözleşmesi
    (v13) aynen ayakta kalır: senkron yalnız kendi entegrasyon anahtarlarını yazar."""
    monkeypatch.setattr(hermes, "_hermes_bin", lambda: "/fake/hermes")
    with open(hermes.AGENT_CONFIG, "w") as fh:
        fh.write("prompt_caching:\n  cache_ttl: 5m\n")
    r = hermes.config_ensure_integrations()
    assert r["ok"] and not any(c.startswith("model.default(") for c in r["changed"])
    assert _olaylar("gemini_dead_model_migrated") == []


def test_varsayilan_ve_harita_ad_deseni_civisi():
    """Varsayılan bir ALIAS olmalı — çıplak sürüm adı, Google'ın yeniden-adlandırma döngüsünde
    (3.5→3.6 dönmüş durumda) aynı 404 sınıfını yeniden doğurur. Çivi SABİT LİSTEYLE DEĞİL
    AD-DESENİYLE: '-latest' alias'ları yeniden-adlandırmaya dayanıklı tek ad sınıfı. Harita da
    aynı deseni taşır: anahtarlar çıplak ölü adlar, hedefler alias; rol (flash/pro) eşleşir."""
    assert hermes.GEMINI_DEFAULT_MODEL.endswith("-latest"), \
        "varsayılan çıplak sürüm adına dönmüş — 404 sınıfı geri gelir (2026-08-12 vakası)"
    assert hermes.GEMINI_DEFAULT_MODEL not in hermes.GEMINI_DEAD_MODEL_MAP, \
        "varsayılan bilinen-ölü listede olamaz"
    for eski, yeni in hermes.GEMINI_DEAD_MODEL_MAP.items():
        assert yeni.endswith("-latest"), f"göç hedefi alias değil: {eski}→{yeni}"
        assert not eski.endswith("-latest"), f"alias ölü-ad listesine giremez: {eski}"
        assert eski != yeni
        # rol korunumu: flash sınıfı flash alias'ına, pro sınıfı pro alias'ına gider
        if "flash" in eski:
            assert "flash" in yeni, f"hızlı-görev rolü kayboldu: {eski}→{yeni}"
        if "pro" in eski:
            assert "pro" in yeni, f"pro rolü kayboldu: {eski}→{yeni}"


def test_nous_override_ve_fallback_zinciri_degismez(sandbox_state, monkeypatch):
    """Operatör seti ÖNCELİKLİ: göç YALNIZ ajan config'indeki model.default'a dokunur —
    NOUS_MODEL/GEMINI_MODEL override çözümlemesi ve ücretsiz fallback zinciri
    (tencent/hy3:free) mevcut sözleşmeyle aynen kalır."""
    from meridian import secrets
    vals = {"NOUS_MODEL": "operator/ozel-model", "GEMINI_MODEL": "gemini-2.5-flash",
            "NOUS_ENDPOINT": "https://ornek.uc/v1"}
    monkeypatch.setattr(secrets, "get", lambda k: vals.get(k))
    _hazirla(monkeypatch, "gemini-3.5-flash")
    r = hermes.config_ensure_integrations()
    assert r["ok"] and _yazilan()["model"]["default"] == "gemini-flash-latest"   # göç koştu
    # override çözümlemesi operatör değerlerini döndürmeye devam eder (öncelik mantığı bozulmadı)
    assert hermes._model_id("nous") == "operator/ozel-model"
    assert hermes._model_id("gemini") == "gemini-2.5-flash"
    # fallback zinciri DEĞİŞMEDİ: birincil nous değilken ücretsiz Nous modeli (mevcut #1 sözleşmesi)
    assert _yazilan()["fallback_providers"] == [{"provider": "nous", "model": "tencent/hy3:free"}]


def test_bos_override_varsayilan_aliasa_duser(sandbox_state, monkeypatch):
    """Öncelik zincirinin öbür ucu: override BOŞKEN çözümleme artık alias'a düşer — yani ilk
    inceleme/yansıma çağrısının gideceği ad listede VAR olan bir addır, çıplak 404 adayı değil."""
    from meridian import secrets
    monkeypatch.setattr(secrets, "get", lambda k: None)
    monkeypatch.setattr(hermes, "_hermes_bin", lambda: None)      # nous yerel modda sayılmasın
    assert hermes._model_id("gemini") == "gemini-pro-latest"
    assert hermes._model_id("gemini") == hermes.GEMINI_DEFAULT_MODEL


def test_k1_pano_turetme_tutarliligi():
    """K1 (2026-07-30): pano varsayılan model adını SABİTİN KENDİSİNDEN türetir
    (api_secrets → model_defaults) — sabit alias'a geçince pano kendiliğinden doğruyu söyler.
    Ek çivi: kullanıcıya akan pano yüzeyinin KOD kısmında ölü çıplak adlar kalmadı
    (yorumlar davranış değildir — v122 dersi)."""
    import inspect
    import pathlib
    from meridian import api
    src = inspect.getsource(api.api_secrets)
    assert "GEMINI_DEFAULT_MODEL" in src, "pano varsayılanı sabitten türetilmiyor (K1 kırık)"
    js = (pathlib.Path(__file__).resolve().parent.parent / "meridian" / "web" / "app.js").read_text()
    js_kod = "\n".join(ln.split("//", 1)[0] for ln in js.splitlines())
    for olu in ("gemini-3.5-flash", "gemini-3.1-pro"):
        assert olu not in js_kod, f"panoda ölü model adı koda çakılı: {olu}"
