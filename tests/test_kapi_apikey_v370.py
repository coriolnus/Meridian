"""v370 — F4-B İSTEMCİ TARAFI: Nous çağrılarına KOŞULLU `apikey` başlığı (APISIX kapı hazırlığı).

NE ÖLÇER. Sabah penceresinde `NOUS_ENDPOINT` APISIX kapısının `/llm/v1` rotasına çevrilecek ve
rota key-auth ile kilitlenecek. Kapı, tüketiciyi `apikey` BAŞLIĞINDAN tanır. Bu dosya İSTEMCİNİN
o kilide hazır olduğunu çiviler — kilidin kendisini DEĞİL (o operatör penceresi):

  (1) `KAPI_APIKEY` DOLU  → `POST {base}/chat/completions` başlıklarında `apikey` VAR ve değeri
      sırrın kendisidir; `Authorization: Bearer …` AYNEN durur (kapı arkasındaki upstream hâlâ
      Bearer ister — kapı Bearer'ı DEĞİŞTİRMEZ, üstüne bir katman koyar).
  (2) `KAPI_APIKEY` DOLU  → `GET {base}/models` sondasında da `apikey` VAR. İKİ yüzey ayrı ayrı
      çivilenir VE başlığı kuran yardımcının TEK olduğu ölçülür (tek-kaynak yasası; v345'in
      "iki tarama kolu ayrı ayrı yazıldı, biri güncellenmedi" dersi aynı sınıftır).
  (3) `KAPI_APIKEY` YOK/BOŞ → başlıklarda `apikey` ANAHTARI HİÇ YOKTUR. Flip'ten ÖNCEKİ davranış
      bit-eş korunur: boş değerle bile başlık gönderilmez (APISIX boş `apikey`i geçerli bir
      tüketici sanmaz ama 401 döndürür — "yokken de gönder" hatası kapıyı bugünden kırardı).
  (4) `"KAPI_APIKEY"` `secrets.ALLOWED` içindedir. EMSAL (secrets.py satır 50-54 vakası,
      çivisi test_fallback_chain_v70.py::test_fallback_name_is_settable): kodun OKUDUĞU ama izin
      listesinde OLMAYAN ad operatörce HİÇ ayarlanamaz — `secrets.set` onu reddeder ve özellik
      ömrü boyunca ölü kalır, üstelik SESSİZCE.

SIR DEĞERİ: testte sahte ("test-kapi-anahtari"). Gerçek ağ çağrısı YOKTUR — `httpx.post`/`httpx.get`
her testte yamalıdır ve sap URL'yi hiç açmadan başlıkları toplar.
"""
from __future__ import annotations

import inspect

import httpx
import pytest

from meridian import hermes, secrets

SAHTE = "test-kapi-anahtari"           # sahte değer — gerçek sır hiçbir yere yazılmaz


def _sirlar(monkeypatch, **kv):
    """`secrets.get`i YALNIZ bu testin sözlüğüyle besle — gerçek `.env`/`state/secrets.json`
    OKUNMAZ. hermes.py'nin içe aktardığı `secrets` modülü ile `secrets` aynı nesnedir; ikisini de yamalamak gerekmez
    ama `ping_brain` da o içe aktarılan `secrets` üzerinden okur, yama oradan uygulanır (v239 deseni)."""
    monkeypatch.setattr(hermes.secrets, "get", lambda k, *a, **kw: kv.get(k), raising=False)


class _Yanit:
    """httpx.Response'un bu iki yolun DOKUNDUĞU yüzeyi kadarı — ağ yok, gövde saptır."""

    def __init__(self, body: dict, status: int = 200):
        self.status_code, self._body = status, body

    def json(self):
        return self._body

    def raise_for_status(self):
        if self.status_code >= 400:
            raise AssertionError("bu testte 4xx/5xx yolu ölçülmüyor")


_IYI_CEVAP = {"choices": [{"message": {"content": "tamam"}, "finish_reason": "stop"}],
              "usage": {"prompt_tokens": 3, "completion_tokens": 2}}


def _post_basliklari(monkeypatch) -> dict:
    """`_nous_text`in GERÇEKTEN gönderdiği başlıkları yakala (çağrıdan sonra doldurulur)."""
    yakalanan: dict = {}

    def sahte_post(url, **kw):
        yakalanan["url"] = url
        yakalanan["headers"] = kw.get("headers") or {}
        return _Yanit(_IYI_CEVAP)

    monkeypatch.setattr(httpx, "post", sahte_post)
    return yakalanan


def _get_basliklari(monkeypatch) -> dict:
    """`ping_brain('nous')` sondasının GERÇEKTEN gönderdiği başlıkları yakala."""
    yakalanan: dict = {}

    def sahte_get(url, **kw):
        yakalanan["url"] = url
        yakalanan["headers"] = kw.get("headers") or {}
        return _Yanit({"data": [{"id": "Hermes-4-405B"}]})

    monkeypatch.setattr(httpx, "get", sahte_get)
    return yakalanan


@pytest.fixture(autouse=True)
def _sonda_uzak_kalsin(monkeypatch):
    """`ping_brain('nous')` önce YEREL kuruluma bakar; yerel ikili varsa HTTP yoluna hiç girmez.
    Bu dosya UZAK (portal/kapı) yolunu ölçüyor — yereli kapat, yoksa çivi sessizce hiçbir şey
    ölçmez ve "yeşil" yalnız erken dönüşün yeşilidir."""
    monkeypatch.setattr(hermes, "_nous_local", lambda: False, raising=False)


# ------------------------------- (4) İZİN LİSTESİ (ÖNCE) -------------------------------

def test_4_kapi_anahtari_ayarlanabilir():
    """Kod bu adı OKUYACAK; ALLOWED'da yoksa `secrets.set` reddeder → operatör HİÇ ayarlayamaz."""
    assert "KAPI_APIKEY" in secrets.ALLOWED, \
        "kod bu adı okuyor ama secrets.set onu reddeder — kapı anahtarı hiç ayarlanamaz"


# ------------------------------- (1) POST YÜZEYİ -------------------------------

def test_1a_sir_varsa_post_apikey_basligini_tasir(sandbox_state, monkeypatch):
    _sirlar(monkeypatch, NOUS_API_KEY="nous-sahte", KAPI_APIKEY=SAHTE)
    yakalanan = _post_basliklari(monkeypatch)

    hermes._nous_text("merhaba", note="v370 civi")

    h = yakalanan["headers"]
    assert h.get("apikey") == SAHTE, f"apikey başlığı yok/yanlış: {sorted(h)}"


def test_1b_authorization_bearer_AYNEN_kalir(sandbox_state, monkeypatch):
    """Kapı Bearer'ı DEĞİŞTİRMEZ: upstream (Nous portal) hâlâ Bearer ister. `apikey` EK katmandır —
    Authorization'ı ezen bir değişiklik kapıyı geçer, upstream'de 401 alır."""
    _sirlar(monkeypatch, NOUS_API_KEY="nous-sahte", KAPI_APIKEY=SAHTE)
    yakalanan = _post_basliklari(monkeypatch)

    hermes._nous_text("merhaba", note="v370 civi")

    h = yakalanan["headers"]
    assert h.get("Authorization") == "Bearer nous-sahte"
    assert h.get("Content-Type") == "application/json"   # POST'un kendi başlığı da kaybolmadı


# ------------------------------- (2) SONDA YÜZEYİ + TEK KAYNAK -------------------------------

def test_2a_sir_varsa_models_sondasi_da_apikey_tasir(sandbox_state, monkeypatch):
    """İKİNCİ YÜZEY: sonda unutulursa kilit sonrası pano 'anahtar reddedildi' der ve arıza
    beyinde sanılır — gerçek sebep sondanın kapıdan geçememesidir."""
    _sirlar(monkeypatch, NOUS_API_KEY="nous-sahte", KAPI_APIKEY=SAHTE)
    yakalanan = _get_basliklari(monkeypatch)

    sonuc = hermes.ping_brain("nous")

    assert sonuc["ok"] is True, sonuc
    assert yakalanan["headers"].get("apikey") == SAHTE, \
        f"sonda başlıksız gidiyor: {sorted(yakalanan['headers'])}"
    assert yakalanan["headers"].get("Authorization") == "Bearer nous-sahte"


def test_2b_iki_yuzey_ayni_yardimciyi_cagirir(sandbox_state, monkeypatch):
    """TEK-KAYNAK YASASI ÖLÇÜMÜ: başlık sözlüğü iki yerde AYRI AYRI kurulursa biri güncellenmeden
    kalır (v345'in iki-tarama-kolu vakası). Yardımcıyı sap ile değiştirip İKİ yüzeyin de o sapın
    ürününü gönderdiğini ölç — kaynak GERÇEKTEN tekse iki çağrı da damgayı taşır."""
    _sirlar(monkeypatch, NOUS_API_KEY="nous-sahte", KAPI_APIKEY=SAHTE)
    monkeypatch.setattr(hermes, "_nous_headers",
                        lambda: {"Authorization": "Bearer nous-sahte", "x-v370-damga": "tek"})
    post = _post_basliklari(monkeypatch)
    get = _get_basliklari(monkeypatch)

    hermes._nous_text("merhaba", note="v370 civi")
    hermes.ping_brain("nous")

    assert post["headers"].get("x-v370-damga") == "tek", "POST kendi başlığını ayrıca kuruyor"
    assert get["headers"].get("x-v370-damga") == "tek", "sonda kendi başlığını ayrıca kuruyor"


def test_2c_yardimci_sirri_kendi_okur_argumansiz():
    """Yardımcı sırrı ÇAĞIRANDAN almaz: iki çağrı yeri iki farklı değer geçemesin (aynı sınıf)."""
    assert list(inspect.signature(hermes._nous_headers).parameters) == []


# ------------------------------- (3) SIR YOKKEN BİT-EŞ -------------------------------

def test_3a_sir_yokken_post_apikey_TASIMAZ(sandbox_state, monkeypatch):
    """Flip'ten ÖNCE değişiklik tamamen hareketsizdir: başlık HİÇ eklenmez (boş değerle bile)."""
    _sirlar(monkeypatch, NOUS_API_KEY="nous-sahte")          # KAPI_APIKEY yok → None
    yakalanan = _post_basliklari(monkeypatch)

    hermes._nous_text("merhaba", note="v370 civi")

    assert "apikey" not in yakalanan["headers"], \
        f"sır yokken başlık eklendi: {sorted(yakalanan['headers'])}"


def test_3b_bos_sir_de_baslik_URETMEZ(sandbox_state, monkeypatch):
    """Boş string sır ("silindi ama anahtar duruyor") başlık üretmez — APISIX'in boş `apikey`i
    tüketici SAYMAMASI beklenir (tasarım varsayımı, flip'te ölçülür); o hâlde arıza sırrın
    YOKLUĞU gibi değil BAŞARISIZLIĞI gibi okunurdu."""
    _sirlar(monkeypatch, NOUS_API_KEY="nous-sahte", KAPI_APIKEY="")
    yakalanan = _post_basliklari(monkeypatch)

    hermes._nous_text("merhaba", note="v370 civi")

    assert "apikey" not in yakalanan["headers"]


def test_3c_sir_yokken_sonda_da_apikey_TASIMAZ(sandbox_state, monkeypatch):
    _sirlar(monkeypatch, NOUS_API_KEY="nous-sahte")
    yakalanan = _get_basliklari(monkeypatch)

    hermes.ping_brain("nous")

    assert "apikey" not in yakalanan["headers"], \
        f"sonda sır yokken başlık ekledi: {sorted(yakalanan['headers'])}"
