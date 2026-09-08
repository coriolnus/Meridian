"""SOUL DENETÇİSİ — KAPI ROTASI VE CEVAPLAYAN MODEL (v455, TSK-138 dilim-2, 2026-09-08).

NE ÖLÇÜLDÜ, NE DEĞİŞTİ. Canlı arıza (A1 `events.jsonl`, olay `brifing_kural_denetimi`,
2026-09-07T22:05:31Z): `hukum=denetlenemedi · kaynak=llm_dustu · cagri_n=3` — YENİDEN-ÜRETİM
çağrısı 150 sn'lik dış duvara çarptı. Kapı ölçümü aynı gün: `/llm/hizli/v1/chat/completions`
200 + `choices` ~1 sn; `/llm/v1/chat/completions` 89 sn + "overloaded" 502 gövdesi. Kapı istek
gövdesindeki `model` alanını YOK SAYAR (routes.yaml `ai-proxy-multi` → `options.model` sabittir),
yani "hızlı model" bir model ADI değil bir ROTA URL'sidir. Operatör kararı (2026-09-08 16:0xZ):
denetçinin İKİ çağrısı da hızlı rotaya alınır, iç bütçe 120 sn KALIR, ve CEVABI HANGİ MODELİN
verdiği ölçülür — iki gece ölçülecek.

NEDEN YENİ BİR ÇAĞRI YOLU, ROTA AYARI DEĞİL — ÖLÇÜLDÜ, VARSAYILMADI (yerel hermes v0.18.2
kaynağı; canlı v0.19.0, sürüm farkı BEYAN EDİLİR):
  * `@sef` profili `model.provider: custom:kapi` diyor; `runtime_provider._get_named_custom_provider`
    ADLANDIRILMIŞ custom girdisini bulduğu an `base_url`u O GİRDİDEN alır.
  * `_resolve_named_custom_runtime` içinde `explicit_base_url` YALNIZ ÇIPLAK `custom` dalında
    okunur — adlandırılmış girdi onu HİÇ görmez. `CUSTOM_BASE_URL` ortam değişkeni de o çıplak
    dala aittir.
  * `resolve_requested_provider` config'in `model.provider`ını `HERMES_INFERENCE_PROVIDER`
    ortam değişkeninden ÖNCE okur — yani ortamdan sağlayıcı da çevrilemez.
  Sonuç: hermes CLI yolunda çağrı BAŞINA rota tutamağı YOKTUR; rota ancak profilin
  `config.yaml`ı değiştirilerek (ve dağıtılarak) döner. Dahası hermes yalnız METNİ basar —
  yanıt gövdesindeki `model` alanı (cevaplayan modelin TEK dürüst kaynağı) o yoldan OKUNAMAZ.
  İki şart birlikte tek bir uygulamayı bırakır: denetçi çağrısı kapıya DOĞRUDAN gider.

BEDEL AÇIKÇA ÇİVİLENİR (bedel yasası — kazanç ölçülüp bedel ölçülmezse körlük sessizdir):
  * Tüketici kimliği `bot_sef` yerine `motor_meridian` olur (`KAPI_APIKEY`); ikisi de
    `deploy/apisix/routes.yaml`ın HER İKİ LLM rotasında da whitelist'tedir.
  * Sistem promptu artık hermes'in derlediği tam metin değil, profilin KENDİ `SOUL.md`sidir —
    koşum anında, hermes'in okuduğu AYNI dosyadan okunur (tek-kaynak). Kaybedilen: hermes'in
    kendi taban promptu ve araç listesi. Araç takımlarının HEPSİ zaten kapalı ve doğrudan çağrı
    hiç `tools` göndermez, yani araç yüzeyi GENİŞLEMEZ — DARALIR.
  * Kapı kökü ya da `KAPI_APIKEY` ölçülemezse yol BUGÜNKÜ davranışa (hermes profili) düşer ve
    düşüş ADIYLA deftere yazılır — sessiz bir kapanma değil.

GERÇEK KAPIYA İSTEK YOK: her HTTP `httpx.post` saplamasıyla ölçülür, gerçek sır hiçbir yere
girmez (sahte değer kullanılır ve çiviler onun HİÇBİR çıktıda geçmediğini ayrıca ölçer).

YARDIMCILAR v385'TEN İTHAL EDİLİR, KOPYALANMAZ (tek-kaynak yasası).
"""
from __future__ import annotations

import importlib
import json

import httpx
import pytest

from tests.test_soul_denetimi_v385 import (  # tek-kaynak: sahte profil/kuyruk/kurulum TEK yerde
    _Kuyruk, _ihlalli_cevap, _olaylar, _profil_evi, _sef_kur, _temiz_cevap)

# SAHTE KAPI ANAHTARI — gerçek değil. Değeri hiçbir çıktıda geçmemeli (aşağıda ayrıca ölçülür).
SAHTE_KAPI_ANAHTARI = "SAHTE-KAPI-ANAHTARI-9876543210"
# Sahte profilin kapı tabanı. GERÇEK profilin biçimiyle AYNI şekildedir; gerçek değeri
# `deploy/hermes/profiles/sef/config.yaml` taşır ve üretim onu O DOSYADAN okur.
SAHTE_KAPI_TABANI = "http://127.0.0.1:9080/llm/v1"


@pytest.fixture
def sd():
    return importlib.import_module("ops.soul_denetimi")


def _config_yaz(ev, base_url=SAHTE_KAPI_TABANI, model="saglayici/sahte-model:free",
                max_tokens=8000):
    """Sahte profile bir `config.yaml` koyar — kapı kökü ORADAN ölçülür.

    v385'in `_profil_evi`si YALNIZ `SOUL.md` yazar ve bu bir eksik DEĞİL: config'siz bir profilde
    kapı kökü ÖLÇÜLEMEZ ve yol hermes'e düşer. Yani v385'in bütün akış çivileri, bu turdan sonra
    da profil yolunu ölçmeye DEVAM eder — o dosyalara tek satır dokunulmadan."""
    govde = {"model": {"provider": "custom:kapi", "default": model, "max_tokens": max_tokens},
             "providers": {"kapi": {"base_url": base_url, "key_env": "BOT_KEY_SEF"}}}
    import yaml
    (ev / "config.yaml").write_text(yaml.safe_dump(govde, allow_unicode=True), encoding="utf-8")
    return ev


class _Yanit:
    """`httpx.post` dönüşü — OpenAI-uyumlu gövdenin sınanan asgarisi."""

    def __init__(self, govde, durum=200):
        self._govde = govde
        self.status_code = durum

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    def json(self):
        return self._govde


def _kapi_govdesi(metin, model="nvidia/nemotron-3-super-120b-a12b:free"):
    govde = {"choices": [{"message": {"content": metin}, "finish_reason": "stop"}]}
    if model is not None:
        govde["model"] = model
    return govde


class _Kapi:
    """`httpx.post` saplaması — çağrıları SIRAYLA cevaplar ve HEPSİNİ saklar.

    Kuyruk tükenirse çivi AÇIK bir `AssertionError` ile patlar: beklenenden fazla çağrı, kotasız
    bir yüzeyde doğrudan operatörün bütçesidir (v385'in `_Kuyruk` sözleşmesiyle aynı gerekçe)."""

    def __init__(self, *govdeler):
        self.govdeler = list(govdeler)
        self.cagrilar: list[dict] = []

    def __call__(self, url, **kw):
        self.cagrilar.append({"url": url, **kw})
        assert self.govdeler, (
            f"BEKLENENDEN FAZLA kapı çağrısı: {len(self.cagrilar)}. çağrı için gövde yok")
        g = self.govdeler.pop(0)
        if isinstance(g, Exception):
            raise g
        return _Yanit(g)

    @property
    def urller(self) -> list[str]:
        return [c["url"] for c in self.cagrilar]


@pytest.fixture
def kurulum(tmp_path, monkeypatch, sandbox_state, request):
    """`@sef` sahte profil evine bağlı, kapı anahtarı SAHTE, ilk (sıralama) çağrısı saplı.

    `_profili_cagir` yine saplıdır ve BU BİR ÇİVİDİR: sıralama çağrısı hermes profilinde KALIR —
    yalnız DENETÇİ çağrıları rotaya taşınır. Sapa dokunulmadığı için, o çağrının kapıya
    kaymadığını her test kendiliğinden ölçer (kapı kuyruğu fazladan çağrıda patlar)."""
    m, ev = _sef_kur(tmp_path, monkeypatch, request)
    _config_yaz(ev)
    from meridian import secrets as _secrets
    monkeypatch.setattr(_secrets, "get",
                        lambda ad: SAHTE_KAPI_ANAHTARI if ad == "KAPI_APIKEY" else None)
    return m, ev


def _sirala(m, monkeypatch, kapi, ilk_metin="- MECHANISM_STALE 5 kez: bugün bak"):
    """Sıralama profilden, denetim kapıdan — koşumun tamamını sürer ve `(metin, kaynak)` döner."""
    monkeypatch.setattr(m, "_profili_cagir", _Kuyruk(ilk_metin))
    monkeypatch.setattr(httpx, "post", kapi)
    return m.sirala(m.topla())


# ================================================================================================
# 1) ROTA — VARSAYILAN HIZLI, ORTAMLA GERİ ALINABİLİR
# ================================================================================================

def test_A1_VARSAYILAN_ROTA_HIZLI(kurulum, monkeypatch):
    """Ortamda hiçbir şey yokken denetçi HIZLI rotaya gider.

    Bu bir tercih değil ÖLÇÜLMÜŞ bir karardır: 2026-09-07 gecesi yeniden-üretim danışma rotasında
    150 sn'lik duvara çarptı ve denetim HİÇ yapılamadı. Varsayılan yanlış tarafta olsaydı,
    değişiklik canlıda ancak biri ortam değişkenini hatırlarsa etkili olurdu."""
    m, _ = kurulum
    monkeypatch.delenv(m.DENETIM_ROTA_ENV, raising=False)
    kapi = _Kapi(_kapi_govdesi(_temiz_cevap()))
    _sirala(m, monkeypatch, kapi)
    assert kapi.urller == ["http://127.0.0.1:9080/llm/hizli/v1/chat/completions"], kapi.urller


def test_A2_ORTAMLA_DANISMA_ROTASINA_DONULUR(kurulum, monkeypatch):
    """Geri alma DAĞITIMSIZ olmalı: rota bir ortam değişkeniyle eski uca döner.

    Ölçüm turu iki gecedir ve kötü giderse geri dönüş yolu bir dağıtım penceresi beklememelidir."""
    m, _ = kurulum
    monkeypatch.setenv(m.DENETIM_ROTA_ENV, "danisma")
    kapi = _Kapi(_kapi_govdesi(_temiz_cevap()))
    _sirala(m, monkeypatch, kapi)
    assert kapi.urller == ["http://127.0.0.1:9080/llm/v1/chat/completions"], kapi.urller


def test_A3_PROFIL_ROTASI_HERMESE_DONER_VE_HIC_HTTP_YOK(kurulum, monkeypatch):
    """TAM geri alma: `profil` değeri bu turdan ÖNCEKİ davranışı (hermes CLI) geri getirir.

    İki değerli bir bayrak (`hizli`/`danisma`) yalnız ROTAYI geri alırdı — doğrudan HTTP yolunu
    değil. Ölçüm turunun tek dürüst geri dönüşü, değiştirdiğimiz her şeyin geri alınabilmesidir."""
    m, _ = kurulum
    monkeypatch.setenv(m.DENETIM_ROTA_ENV, "profil")
    kuyruk = _Kuyruk("- MECHANISM_STALE 5 kez: bugün bak", _temiz_cevap())
    monkeypatch.setattr(m, "_profili_cagir", kuyruk)
    monkeypatch.setattr(httpx, "post", _Kapi())      # tek çağrıda bile patlar
    metin, kaynak = m.sirala(m.topla())
    assert kaynak == "llm", (kaynak, metin)
    assert kuyruk.n == 2, f"denetçi profil yolundan geçmedi: {kuyruk.n} çağrı"


def test_A4_TANINMAYAN_ROTA_ADIYLA_KAYDA_GECER_VE_VARSAYILANA_DUSER(kurulum, monkeypatch):
    """Yazım hatası SESSİZ bir davranış değişikliği olamaz (Yasa 4).

    `SOUL_DENETIM_ROTA=hızlı` (Türkçe ı) yazan bir operatör bugün hiçbir uyarı almadan
    danışma rotasında kalırdı; kayıt olmadan bu ayrım iki gecelik ölçümü sessizce bozardı."""
    m, _ = kurulum
    monkeypatch.setenv(m.DENETIM_ROTA_ENV, "hızlı")
    kapi = _Kapi(_kapi_govdesi(_temiz_cevap()))
    _sirala(m, monkeypatch, kapi)
    assert kapi.urller == ["http://127.0.0.1:9080/llm/hizli/v1/chat/completions"], kapi.urller
    adlar = [e.get("event") for e in _olaylar("sef_brifingi_denetci_rotasi_taninmadi")]
    assert adlar, "tanınmayan rota ADIYLA deftere yazılmadı"


def test_A5_YENIDEN_URETIM_DE_AYNI_ROTADAN_GIDER(kurulum, monkeypatch):
    """Operatör kararı İKİ çağrıyı da kapsar — ve 2026-09-07'de duvara çarpan zaten YENİDEN-ÜRETİMdi.

    Yalnız denetim taşınsaydı ölçülen arıza AYNEN yerinde kalırdı: kazanç ölçülür, arıza sürerdi."""
    m, _ = kurulum
    kapi = _Kapi(_kapi_govdesi(_ihlalli_cevap()),                     # 1) denetim → ihlal
                 _kapi_govdesi("- düzeltilmiş MECHANISM_STALE metni"),  # 2) yeniden-üretim
                 _kapi_govdesi(_temiz_cevap()))                        # 3) yeniden-denetim
    _sirala(m, monkeypatch, kapi)
    hizli = "http://127.0.0.1:9080/llm/hizli/v1/chat/completions"
    assert kapi.urller == [hizli, hizli, hizli], kapi.urller


# ================================================================================================
# 2) CEVAPLAYAN MODEL — YANIT GÖVDESİNDEN, UYDURULMADAN
# ================================================================================================

def test_B1_CEVAPLAYAN_MODEL_YANITTAN_OKUNUR(kurulum, monkeypatch, sd):
    """Kapı istemcinin `model` alanını EZER; cevaplayan modelin tek dürüst kaynağı YANIT gövdesidir.

    İstenen künye (`model`) de kalır: ikisi ayrıştığı gün — ki 2026-09-08'de ultra istenip super
    cevaplıyor — teşhis tam o farktan okunur."""
    m, _ = kurulum
    kapi = _Kapi(_kapi_govdesi(_temiz_cevap(), model="nvidia/nemotron-3-super-120b-a12b:free"))
    _sirala(m, monkeypatch, kapi)
    olay = _olaylar(sd.OLAY)[-1]
    assert olay.get("cevaplayan_model") == "nvidia/nemotron-3-super-120b-a12b:free", olay
    assert olay.get("model") == "custom:kapi/saglayici/sahte-model:free", olay


def test_B2_MODEL_ALANI_YOKSA_NONE_VE_NEDEN(kurulum, monkeypatch, sd):
    """Ölçülemeyen değer UYDURULMAZ: `None` + ADIYLA neden (uydurma yasağı + Yasa 4).

    İstenen künyeyi buraya kopyalamak en ucuz yanlıştı: defter "super cevapladı" der, gerçekte
    ölçüm HİÇ YAPILMAMIŞ olurdu — ve iki gecelik ölçüm tam bu alandan okunacak."""
    m, _ = kurulum
    kapi = _Kapi(_kapi_govdesi(_temiz_cevap(), model=None))
    _sirala(m, monkeypatch, kapi)
    olay = _olaylar(sd.OLAY)[-1]
    assert olay.get("cevaplayan_model") is None, olay
    assert _olaylar("sef_brifingi_cevaplayan_model_olculemedi"), "neden ADIYLA deftere yazılmadı"


def test_B3_HUKUM_CEVAPLAYAN_MODELI_TASIR_AMA_DAMGAYA_YAZMAZ(kurulum, monkeypatch, sd):
    """Alan `Hukum`da durur ve YALNIZ olaya gider — damganın şeması DONUK (Yasa 6 / O4).

    `Gecis.kayit()` hem olaya hem damgaya akar; yeni alan oraya girseydi damganın okuyucusu
    (`_kural_denetimi_satiri`) onu HİÇ basmaz ve yazım okunmayan bir artefakt olurdu."""
    m, ev = kurulum
    kapi = _Kapi(_kapi_govdesi(_temiz_cevap(), model="sahte/cevaplayan:free"))
    monkeypatch.setattr(m, "_profili_cagir", _Kuyruk("- metin"))
    monkeypatch.setattr(httpx, "post", kapi)
    g = sd.gecir(profil_evi=str(ev), ilk_metin="- MECHANISM_STALE 5 kez: bak",
                 ilk_istem="İLK İSTEM", veri_terimleri=[], cagir=m._denetci_cagir,
                 bot="sef", cevaplayan_oku=m._cevaplayan_model_oku)
    assert g.hukum.cevaplayan_model == "sahte/cevaplayan:free", g.hukum
    assert "cevaplayan_model" not in g.kayit("sef"), g.kayit("sef")


def test_B4_DUSEN_YENIDEN_DENETIMDE_ONCEKI_CAGRININ_MODELI_SIZMAZ(kurulum, monkeypatch, sd):
    """Çağrı düşerse ölçüm YOKTUR — ve ARADAKİ çağrıların modeli oraya SIZAMAZ.

    ÜÇ ÇAĞRILIK YOL BİLEREK SÜRÜLÜR (yalnız düşen bir çağrı bu dalı SÜRMEZ: `_yeniden`in kendi
    `except`i alanı zaten hiç doldurmaz). Sıra: denetim → ihlal (`sahte/ilk`) · YENİDEN-ÜRETİM →
    metin (`sahte/ikinci`) · yeniden-DENETİM → düşer. Tutucu her çağrıda sıfırlanmasaydı, teslim
    edilen `llm_dustu` hükmü defterde ÜRETİM çağrısının modeliyle görünürdü: hiç yapılmamış bir
    ölçüm, yapılmış gibi okunurdu (uydurma yasağı) ve ölçüm aleti kendi arızasını gizlerdi."""
    m, _ = kurulum
    kapi = _Kapi(_kapi_govdesi(_ihlalli_cevap(), model="sahte/ilk:free"),
                 _kapi_govdesi("- düzeltilmiş MECHANISM_STALE metni", model="sahte/ikinci:free"),
                 RuntimeError("kapı düştü"))
    _sirala(m, monkeypatch, kapi)
    olay = _olaylar(sd.OLAY)[-1]
    assert olay.get("kaynak") == "llm_dustu", olay
    assert olay.get("cevaplayan_model") is None, olay


def test_B5_OKUYUCU_CEVAPLAYAN_MODELI_BASAR(kurulum, monkeypatch):
    """YASA 6: okunmayan alan üretilmemiştir. Operatörün her koşumda gördüğü durum satırı basar."""
    m, _ = kurulum
    kapi = _Kapi(_kapi_govdesi(_temiz_cevap(), model="sahte/cevaplayan:free"))
    _sirala(m, monkeypatch, kapi)
    satir = m._denetci_teshis_satiri()
    assert "sahte/cevaplayan:free" in satir, satir


def test_B6_OKUYUCU_OLCULEMEDIYI_AYIRIR(kurulum, monkeypatch):
    """`None` "ölçemedim"dir ve öyle basılır — boş bir dizge onu "ölçtüm, boştu" gibi gösterirdi."""
    m, _ = kurulum
    kapi = _Kapi(_kapi_govdesi(_temiz_cevap(), model=None))
    _sirala(m, monkeypatch, kapi)
    satir = m._denetci_teshis_satiri()
    assert "cevaplayan=ÖLÇÜLEMEDİ" in satir, satir


# ================================================================================================
# 3) DÜŞÜŞ YOLU — ÖLÇÜLEMEYEN KAPI SESSİZCE KAPANMAZ
# ================================================================================================

def test_C1_KAPI_KOKU_OLCULEMEZSE_PROFIL_YOLUNA_DUSER(tmp_path, monkeypatch, sandbox_state,
                                                      request):
    """Config'i okunamayan bir profilde rota UYDURULMAZ — bugünkü (ölçülmüş, çalışan) yola düşülür.

    Alternatif "kapıya sabit bir kök yaz" olurdu: profil bir gün portu değiştirdiğinde denetim
    sessizce ölürdü (tek-kaynak yasası — kök profilin KENDİ `config.yaml`ından ölçülür)."""
    m, _ = _sef_kur(tmp_path, monkeypatch, request)     # config.yaml YOK
    from meridian import secrets as _secrets
    monkeypatch.setattr(_secrets, "get",
                        lambda ad: SAHTE_KAPI_ANAHTARI if ad == "KAPI_APIKEY" else None)
    kuyruk = _Kuyruk("- MECHANISM_STALE 5 kez: bak", _temiz_cevap())
    monkeypatch.setattr(m, "_profili_cagir", kuyruk)
    monkeypatch.setattr(httpx, "post", _Kapi())          # tek çağrıda patlar
    metin, kaynak = m.sirala(m.topla())
    assert kaynak == "llm", (kaynak, metin)
    assert kuyruk.n == 2, f"düşüş yolu profil çağrısına inmedi: {kuyruk.n}"
    assert _olaylar("sef_brifingi_denetci_rota_dustu"), "düşüş ADIYLA deftere yazılmadı"


def test_C2_KAPI_ANAHTARI_YOKSA_PROFIL_YOLUNA_DUSER(kurulum, monkeypatch):
    """Sır yoksa çağrı 401 alacaktı; düşüş ÖNCE olur ve kayda geçer (dürüst bozunma)."""
    m, _ = kurulum
    from meridian import secrets as _secrets
    monkeypatch.setattr(_secrets, "get", lambda ad: None)
    kuyruk = _Kuyruk("- MECHANISM_STALE 5 kez: bak", _temiz_cevap())
    monkeypatch.setattr(m, "_profili_cagir", kuyruk)
    monkeypatch.setattr(httpx, "post", _Kapi())
    metin, kaynak = m.sirala(m.topla())
    assert (kaynak, kuyruk.n) == ("llm", 2), (kaynak, kuyruk.n)
    assert _olaylar("sef_brifingi_denetci_rota_dustu"), "düşüş ADIYLA deftere yazılmadı"


def test_C3_BOS_CEVAP_TESLIMATI_DUSURMEZ(kurulum, monkeypatch, sd):
    """Kapı 200 döndürüp içerik vermezse hüküm `llm_dustu`dur, teslimat GİDER (fail-open)."""
    m, _ = kurulum
    kapi = _Kapi(_kapi_govdesi("", model="sahte/cevaplayan:free"))
    metin, kaynak = _sirala(m, monkeypatch, kapi)
    assert kaynak == "llm" and "MECHANISM_STALE" in metin, (kaynak, metin)
    assert _olaylar(sd.OLAY)[-1].get("kaynak") == "llm_dustu", _olaylar(sd.OLAY)[-1]


def test_C4_KESILEN_CEVAP_GECERLI_SAYILMAZ(kurulum, monkeypatch, sd):
    """"CEVAP BOŞ DEĞİL ⇒ CEVAP GEÇERLİDİR" varsayımı burada da YASAK
    (`meridian/hermes.py::_nous_text`teki sıranın aynısı, `ops/sef_brifingi.py::_denetci_cagir`
    docstring'inin gerekçesi). Gövde `finish_reason: "length"` ile döner — içerik BOŞ DEĞİL,
    hatta ŞEMAYA UYAN geçerli bir JSON: kesilme kontrolü olmasaydı bu cevap "temiz" sayılıp
    kabul edilirdi. Kesilme kontrolü BOŞ-metin kontrolünden ÖNCE çalıştığı için hüküm HER
    hâlükârda `llm_dustu` olmalı ve gerekçe KESİLME sınıfını taşımalı — teslimat yine gider
    (fail-open), ama denetim "geçti" SAYILMAZ."""
    m, _ = kurulum
    govde = {"choices": [{"message": {"content": _temiz_cevap()}, "finish_reason": "length"}],
            "model": "sahte/cevaplayan:free"}
    kapi = _Kapi(govde)
    metin, kaynak = _sirala(m, monkeypatch, kapi)
    assert kaynak == "llm" and "MECHANISM_STALE" in metin, (kaynak, metin)
    olay = _olaylar(sd.OLAY)[-1]
    assert olay.get("kaynak") == "llm_dustu", olay
    assert "KESİLDİ" in olay.get("gerekce", ""), olay


# ================================================================================================
# 4) SÖZLEŞMELER — BÜTÇE, SIR, SİSTEM PROMPTU
# ================================================================================================

def test_D1_IC_BUTCE_120_SN_KALIR(kurulum, monkeypatch):
    """Operatör kararı: rota değişir, BÜTÇE DEĞİŞMEZ. Sayı TEKRARLANMAZ, üretimden okunur —
    tekrarlayan bir çivi tam da "iki kopya sessizce ayrışır" sınıfını çiviye taşırdı."""
    m, _ = kurulum
    kapi = _Kapi(_kapi_govdesi(_temiz_cevap()))
    _sirala(m, monkeypatch, kapi)
    assert kapi.cagrilar[0]["timeout"] == m.MODEL_TIMEOUT_S, kapi.cagrilar[0]["timeout"]


def test_D2_ANAHTAR_APIKEY_BASLIGINDA_VE_HICBIR_CIKTIDA_YOK(kurulum, monkeypatch, sd):
    """Kapının `key-auth` eklentisi tüketiciyi `apikey` BAŞLIĞINDAN tanır (routes.yaml).

    Ve sır DEĞERİ hiçbir deftere/olaya girmez: `notify.scrub` yalnız izinli ADLARI tarar, yani
    bir sızıntı burada yakalanmazsa hiçbir yerde yakalanmaz."""
    m, _ = kurulum
    kapi = _Kapi(_kapi_govdesi(_temiz_cevap()))
    _sirala(m, monkeypatch, kapi)
    assert kapi.cagrilar[0]["headers"]["apikey"] == SAHTE_KAPI_ANAHTARI, kapi.cagrilar[0]
    from meridian import store
    ham = json.dumps(list(store.read_jsonl("events.jsonl")), ensure_ascii=False)
    assert SAHTE_KAPI_ANAHTARI not in ham, "kapı anahtarı olay defterine SIZDI"
    assert SAHTE_KAPI_ANAHTARI not in m._denetci_teshis_satiri()


def test_D3_SISTEM_PROMPTU_PROFILIN_SOUL_DOSYASINDAN(kurulum, monkeypatch):
    """Sistem promptu koşum anında profilin KENDİ `SOUL.md`sinden okunur — kopya YOK.

    Doğrudan çağrı hermes'in derlediği promptu kaybeder; KİMLİK yarısı kaybedilemez, çünkü
    yeniden-üretim çağrısı bir BRİFİNG üretir ve o metin `@sef` sesiyle yazılmak zorundadır."""
    m, ev = kurulum
    kapi = _Kapi(_kapi_govdesi(_temiz_cevap()))
    _sirala(m, monkeypatch, kapi)
    mesajlar = kapi.cagrilar[0]["json"]["messages"]
    assert mesajlar[0]["role"] == "system", mesajlar[0]
    assert mesajlar[0]["content"] == (ev / "SOUL.md").read_text(encoding="utf-8").strip()
    assert mesajlar[-1]["role"] == "user"


def test_D4_ISTEM_SIR_SUZGECINDEN_GECER(kurulum, monkeypatch):
    """Model çağrısı bir VERİ ÇIKIŞIDIR — hermes yolunda `notify.scrub` uygulanıyordu, burada da
    uygulanmalı. Süzgeç düşseydi aynı baytlar bir kanalda temiz, ötekinde ham giderdi."""
    m, _ = kurulum
    gorulen = []
    from meridian import notify
    monkeypatch.setattr(notify, "scrub", lambda s: gorulen.append(s) or "SUZULMUS-ISTEM")
    kapi = _Kapi(_kapi_govdesi(_temiz_cevap()))
    _sirala(m, monkeypatch, kapi)
    assert kapi.cagrilar[0]["json"]["messages"][-1]["content"] == "SUZULMUS-ISTEM", gorulen


def test_D5_MAX_TOKENS_PROFILDEN_AYNEN_TASINIR(kurulum, monkeypatch):
    """`max_tokens` ELLE YAZILMAZ, profilin KENDİ `config.yaml`ından AYNEN taşınır (B-2, tek-kaynak
    yasası). Değer testin İÇİNDE tekrarlanmaz — sahte profil dosyasından OKUNUR: sabit bir sayı
    (ör. 8000) burada yazılsaydı `_config_yaz`ın varsayılanıyla TESADÜFEN eşleşen bir çivi
    olurdu ve profil değeri bir gün değiştiğinde kırmızı olmayan bir çivi kalırdı."""
    m, ev = kurulum
    import yaml
    cfg = yaml.safe_load((ev / "config.yaml").read_text(encoding="utf-8"))
    beklenen = cfg["model"]["max_tokens"]
    kapi = _Kapi(_kapi_govdesi(_temiz_cevap()))
    _sirala(m, monkeypatch, kapi)
    assert kapi.cagrilar[0]["json"]["max_tokens"] == beklenen, kapi.cagrilar[0]
