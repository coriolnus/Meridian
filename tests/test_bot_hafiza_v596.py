"""v596 — konuşan filo Hindsight hafıza yazıcısı `bot_hafiza.HindsightHafiza` (plan 2026-09-29 Parça 1b-ön Görev 2;
spec 2026-09-29 §3.4). `hatırla:` → retain, `unut:` → recall + en fazla `UNUT_TAVANI` bellek için GERİ ALINABİLİR
`state: invalidated`, `geri_al` → `state: valid`. Kalıcı silme yolu YOK.

AĞ YOK: her çivi ya sahte `_cagir` taşır ya da `urlopen`u yamar — gerçek 8888'e hiçbir istek gitmez. `bota_sor`
üzerinden koşan (olay yazabilen) her çivi `sandbox_state` alır.
"""
import ast
import datetime as dt
import inspect
import io
import json
import re
import urllib.error

import pytest

from meridian import bot_hafiza as bh, bot_kanal as bk, obs, secrets, store

ANAHTAR = "K" * 32
TABAN = "http://127.0.0.1:8888"
SIMDI = dt.datetime(2026, 9, 29, 12, 0, tzinfo=dt.timezone.utc)
RETAIN_TAMAM = {"success": True, "bank_id": "bot-bekci", "items_count": 1, "async": False}


_VARSAYILAN = object()   # `None` bir CEVAP sınıfıdır (boş gövde) — varsayılanı ondan ayırır


class Casus:
    """Sahte `_cagir(yontem, url, govde, basliklar, zaman_asimi)`: her çağrıyı kaydeder, yola göre cevap verir."""

    def __init__(self, recall=_VARSAYILAN, retain=_VARSAYILAN, patch_hatasi_sirasi=None):
        self.cagrilar = []
        self.recall = {"results": []} if recall is _VARSAYILAN else recall
        self.retain = RETAIN_TAMAM if retain is _VARSAYILAN else retain
        self.patch_hatasi_sirasi = patch_hatasi_sirasi

    def __call__(self, yontem, url, govde, basliklar, zaman_asimi):
        self.cagrilar.append({"yontem": yontem, "url": url, "govde": govde, "basliklar": basliklar,
                              "zaman_asimi": zaman_asimi})
        if yontem == "POST" and url.endswith("/memories/recall"):
            return self.recall
        if yontem == "POST" and url.endswith("/memories"):
            return self.retain
        if yontem == "PATCH":
            if len(self.patchler()) - 1 == self.patch_hatasi_sirasi:
                raise RuntimeError("hindsight HTTP 500")
            return None
        raise AssertionError(f"beklenmeyen çağrı {yontem} {url}")

    def patchler(self):
        return [c for c in self.cagrilar if c["yontem"] == "PATCH"]


def _h(casus, **kw):
    return bh.HindsightHafiza(_cagir=casus, _anahtar=lambda: ANAHTAR, **kw)


def _recall(*kayitlar):
    return {"results": [{"id": i, "text": t, "type": "world"} for i, t in kayitlar]}


def _utc_mu(iso: str) -> bool:
    return dt.datetime.fromisoformat(iso).utcoffset() == dt.timedelta(0)


# ---- yaz (retain) -----------------------------------------------------------------------------------------

def test_yaz_istek_bicimi_ve_yalniz_authorization_basligi():
    c = Casus()
    assert _h(c).yaz("bekci", "cuma toplantısı iptal", ("sabit_not", "bot:bekci", "kanal:telegram")) is True
    (cagri,) = c.cagrilar
    assert (cagri["yontem"], cagri["url"]) == ("POST", f"{TABAN}/v1/default/banks/bot-bekci/memories")
    assert cagri["basliklar"] == {"Authorization": f"Bearer {ANAHTAR}"}
    assert cagri["zaman_asimi"] == 10.0
    (oge,) = cagri["govde"]["items"]
    assert _utc_mu(oge.pop("timestamp"))
    assert cagri["govde"] == {"items": [{"content": "cuma toplantısı iptal", "context": "operatör notu",
                                         "tags": ["sabit_not", "bot:bekci", "kanal:telegram"],
                                         "metadata": {"kaynak": "operator"}}], "async": False}


def test_yaz_success_false_ise_false_doner():
    assert _h(Casus(retain={**RETAIN_TAMAM, "success": False})).yaz("bekci", "x", ("sabit_not",)) is False


@pytest.mark.parametrize("cevap", [None, {}, {"items_count": 1}, [], "tamam"])
def test_yaz_cevabi_taninmazsa_yazildi_uydurulmaz(cevap):
    # Uydurma yasağı: `success` alanı okunamayan bir 2xx "Not aldım" demeye yetmez.
    with pytest.raises(RuntimeError) as e:
        _h(Casus(retain=cevap)).yaz("bekci", "x", ("sabit_not",))
    assert ANAHTAR[:8] not in str(e.value)


# ---- unut (recall + invalidated) --------------------------------------------------------------------------

def test_unut_recall_sonra_en_fazla_uc_patch_ve_geri_alinabilir_neden():
    c = Casus(recall=_recall(("m1", "eski not bir"), ("m2", "eski not iki"), ("m3", "eski not üç"),
                             ("m4", "dördüncü"), ("m5", "beşinci")))
    donen = _h(c).unut("bekci", "eski not")
    assert donen == [("m1", "eski not bir"), ("m2", "eski not iki"), ("m3", "eski not üç")]
    recall, *patchler = c.cagrilar
    assert (recall["yontem"], recall["url"]) == ("POST", f"{TABAN}/v1/default/banks/bot-bekci/memories/recall")
    assert recall["govde"] == {"query": "eski not", "budget": "low", "max_tokens": bh.UNUT_RECALL_MAX_TOKENS}
    assert [p["url"] for p in patchler] == [f"{TABAN}/v1/default/banks/bot-bekci/memories/m{i}" for i in (1, 2, 3)]
    assert all(p["yontem"] == "PATCH" and p["basliklar"] == {"Authorization": f"Bearer {ANAHTAR}"}
               for p in patchler)
    for p in patchler:
        assert set(p["govde"]) == {"state", "reason"} and p["govde"]["state"] == "invalidated"
        m = re.fullmatch(r"operatör unut: eski not \((.+)\)", p["govde"]["reason"])
        assert m and _utc_mu(m.group(1))
    assert bh.UNUT_TAVANI == 3


def test_unut_recall_bossa_bos_liste_ve_patch_yok():
    c = Casus(recall={"results": []})
    assert _h(c).unut("bekci", "hiç yazılmamış bir şey") == []
    assert c.patchler() == [] and len(c.cagrilar) == 1


@pytest.mark.parametrize("zarf", ["liste", "items", "results", "memories", "data"])
def test_unut_recall_zarfi_olculmus_okuyucu_kadar_toleransli(zarf):
    # Ölçülen okuyucu `deploy/hindsight/hafiza_sor.sh`: liste ise kendisi, değilse items|results|memories|data.
    dizi = [{"id": "m1", "text": "eski not"}]
    c = Casus(recall=dizi if zarf == "liste" else {zarf: dizi, "trace": {}})
    assert _h(c).unut("bekci", "eski") == [("m1", "eski not")]
    assert len(c.patchler()) == 1


@pytest.mark.parametrize("cevap", [{"sonuclar": []}, {"results": "x"}, "x", None, 3])
def test_unut_recall_zarfi_taninmazsa_hata_ve_patch_yok(cevap):
    # Tanınmayan zarf "eşleşme yok" SAYILMAZ: operatöre "hiçbir şey unutulmadı" demek ölçülmemiş bir iddia olurdu.
    c = Casus(recall=cevap)
    with pytest.raises(RuntimeError):
        _h(c).unut("bekci", "eski")
    assert c.patchler() == []


@pytest.mark.parametrize("kayit", [{"text": "kimliksiz"}, {"id": "../m1", "text": "x"}, {"id": "a/b", "text": "x"},
                                   {"id": 7, "text": "x"}, {"id": "", "text": "x"}, "düz-metin"])
def test_unut_ilk_uc_sonucta_kimlik_taninmazsa_hic_patch_atilmaz(kayit):
    # Kimlik URL YOLUNA girer; biri bile tanınmazsa HİÇBİRİ emekliye ayrılmaz (yarım iş operatöre sessiz kalırdı).
    c = Casus(recall={"results": [{"id": "m1", "text": "iyi"}, kayit]})
    with pytest.raises(RuntimeError):
        _h(c).unut("bekci", "eski")
    assert c.patchler() == []


def test_unut_kesit_once_scrub_sonra_80_tavan():
    anahtar = "sk-or-v1-" + "a" * 64
    metin = "x" * 60 + " " + anahtar + "\n" + "y" * 100
    ((_, kesit),) = _h(Casus(recall=_recall(("m1", metin)))).unut("bekci", "x")
    assert len(kesit) <= 80 and "sk-or-v1-" not in kesit and "\n" not in kesit


def test_unut_metinsiz_sonuc_kesiti_uydurulmaz():
    ((_, kesit),) = _h(Casus(recall={"results": [{"id": "m1"}]})).unut("bekci", "x")
    assert kesit == "(metin yok)"


def test_unut_kismi_hata_emekliye_ayrilanlari_istisnada_tasir():
    # 2. PATCH düşerse 1. zaten emekliye ayrılmıştır: operatör hangisini geri alacağını bilmeli (Review Focus 2/3).
    c = Casus(recall=_recall(("m1", "bir"), ("m2", "iki"), ("m3", "üç")), patch_hatasi_sirasi=1)
    with pytest.raises(RuntimeError) as e:
        _h(c).unut("bekci", "x")
    assert e.value.unutulanlar == [("m1", "bir")] and len(c.patchler()) == 2


@pytest.mark.parametrize("ifade", ["", "   ", "\n"])
def test_unut_bos_ifade_http_oncesi_reddedilir(ifade):
    # Boş sorgu recall'da rastgele en yakın bellekleri döndürür — emekliye ayrılan şey operatörün seçimi olmazdı.
    c = Casus(recall=_recall(("m1", "x")))
    with pytest.raises(ValueError):
        _h(c).unut("bekci", ifade)
    assert c.cagrilar == []


# ---- geri_al ------------------------------------------------------------------------------------------------

def test_geri_al_state_valid():
    c = Casus()
    assert _h(c).geri_al("bekci", "123e4567-e89b-12d3-a456-426614174000") is True
    (p,) = c.cagrilar
    assert (p["yontem"], p["url"]) == (
        "PATCH", f"{TABAN}/v1/default/banks/bot-bekci/memories/123e4567-e89b-12d3-a456-426614174000")
    assert p["govde"] == {"state": "valid"} and p["basliklar"] == {"Authorization": f"Bearer {ANAHTAR}"}


@pytest.mark.parametrize("kimlik", ["../m1", "a/b", "", "m1?x=1", "m1#f", "..", None, 5])
def test_geri_al_gecersiz_kimlik_http_oncesi_reddedilir(kimlik):
    c = Casus()
    with pytest.raises(ValueError):
        _h(c).geri_al("bekci", kimlik)
    assert c.cagrilar == []


# ---- ortak kapılar ------------------------------------------------------------------------------------------

@pytest.mark.parametrize("bot", ["../x", "a/b", "Bekci", "", "bekci?k=1", "bekci-1"])
@pytest.mark.parametrize("islem", ["yaz", "unut", "geri_al"])
def test_bot_adi_http_oncesi_reddedilir(bot, islem):
    c = Casus()
    h = _h(c)
    with pytest.raises(ValueError):
        {"yaz": lambda: h.yaz(bot, "x", ("sabit_not",)), "unut": lambda: h.unut(bot, "x"),
         "geri_al": lambda: h.geri_al(bot, "m1")}[islem]()
    assert c.cagrilar == []


@pytest.mark.parametrize("islem", ["yaz", "unut", "geri_al"])
def test_anahtar_yoksa_istek_atilmaz_ve_hata_metni_sabit(islem):
    c = Casus()
    h = bh.HindsightHafiza(_cagir=c, _anahtar=lambda: None)
    with pytest.raises(RuntimeError) as e:
        {"yaz": lambda: h.yaz("bekci", "x", ("sabit_not",)), "unut": lambda: h.unut("bekci", "x"),
         "geri_al": lambda: h.geri_al("bekci", "m1")}[islem]()
    assert str(e.value) == "hindsight kiracı anahtarı credential yok" and c.cagrilar == []


@pytest.mark.parametrize("deger", [None, 0, 0.0, -1, float("inf"), float("-inf"), float("nan"), "10", True])
def test_zaman_asimi_sonlu_ve_pozitif_olmali(deger):
    with pytest.raises(ValueError):
        bh.HindsightHafiza(zaman_asimi_s=deger)


# ---- varsayılan HTTP yolu (urlopen yamalı — üretimin TEK yolu, `_cagir` enjekte EDİLMEZ) ----------------------

class _Cevap(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.close()


def test_varsayilan_yol_retain_zaman_asimli_post(monkeypatch):
    gorulen = {}

    def urlopen(istek, timeout=None):
        gorulen.update(istek=istek, timeout=timeout)
        return _Cevap(json.dumps(RETAIN_TAMAM).encode())

    monkeypatch.setattr(bh.urllib.request, "urlopen", urlopen)
    assert bh.HindsightHafiza(_anahtar=lambda: ANAHTAR).yaz("bekci", "not", ("sabit_not",)) is True
    istek = gorulen["istek"]
    assert gorulen["timeout"] == bh.HAFIZA_ZAMAN_ASIMI_S == 10.0 and istek.get_method() == "POST"
    assert istek.full_url == f"{TABAN}/v1/default/banks/bot-bekci/memories"
    assert istek.get_header("Authorization") == f"Bearer {ANAHTAR}"
    assert istek.get_header("Content-type") == "application/json"
    assert json.loads(istek.data)["items"][0]["content"] == "not"


def test_varsayilan_yol_geri_al_patch(monkeypatch):
    gorulen = {}

    def urlopen(istek, timeout=None):
        gorulen.update(istek=istek, timeout=timeout)
        return _Cevap(b"")

    monkeypatch.setattr(bh.urllib.request, "urlopen", urlopen)
    assert bh.HindsightHafiza(_anahtar=lambda: ANAHTAR).geri_al("bekci", "m1") is True
    istek = gorulen["istek"]
    assert istek.get_method() == "PATCH" and json.loads(istek.data) == {"state": "valid"}
    assert istek.full_url == f"{TABAN}/v1/default/banks/bot-bekci/memories/m1" and gorulen["timeout"] == 10.0


def test_varsayilan_yol_http_hatasi_yalniz_kod_tasir_anahtar_url_sizmaz(monkeypatch):
    anahtar = "GIZLIANAHTAR" + "Z" * 20

    def urlopen(istek, timeout=None):
        raise urllib.error.HTTPError(f"{TABAN}/v1/default/banks/bot-bekci/memories?key={anahtar}", 401,
                                     f"Unauthorized {anahtar}", {}, None)

    monkeypatch.setattr(bh.urllib.request, "urlopen", urlopen)
    with pytest.raises(RuntimeError) as e:
        bh.HindsightHafiza(_anahtar=lambda: anahtar).yaz("bekci", "x", ("sabit_not",))
    assert str(e.value) == "hindsight HTTP 401" and e.value.http_kod == 401
    assert e.value.__cause__ is None and e.value.__suppress_context__ is True


@pytest.mark.parametrize("hata", [
    urllib.error.URLError("[Errno 61] Connection refused"), TimeoutError("timed out"),
    ValueError("Invalid header value b'Bearer GIZLIANAHTARZZZZZZZZZZZZZZZZZZZZ\\n'"),
])
def test_varsayilan_yol_ag_hatasi_sinif_adi_tasir_mesaj_sizmaz(monkeypatch, hata):
    # `http.client` geçersiz başlık hatası başlık DEĞERİNİ (anahtarı) mesajına yazar — mesaj yukarı TAŞINMAZ.
    def urlopen(istek, timeout=None):
        raise hata

    monkeypatch.setattr(bh.urllib.request, "urlopen", urlopen)
    with pytest.raises(RuntimeError) as e:
        bh.HindsightHafiza(_anahtar=lambda: "GIZLIANAHTAR" + "Z" * 20).unut("bekci", "x")
    assert str(e.value) == f"hindsight {type(hata).__name__}" and "GIZLI" not in str(e.value)
    assert e.value.__cause__ is None and e.value.__suppress_context__ is True


def test_varsayilan_yol_json_olmayan_govde_sinyalli(monkeypatch):
    monkeypatch.setattr(bh.urllib.request, "urlopen", lambda istek, timeout=None: _Cevap(b"<html>gizli</html>"))
    with pytest.raises(RuntimeError) as e:
        bh.HindsightHafiza(_anahtar=lambda: ANAHTAR).unut("bekci", "x")
    assert "gizli" not in str(e.value)


# ---- tek kaynak + protokol + kalıcı silme yok -----------------------------------------------------------------

def test_taban_ve_kiraci_anahtari_tek_kaynaktan(monkeypatch):
    istenen = []

    def tuzak(ad):
        istenen.append(ad)
        return ANAHTAR

    monkeypatch.setattr(secrets, "credential_oku", tuzak)
    c = Casus()
    h = bh.HindsightHafiza(_cagir=c)
    assert h.taban_url == secrets.HAFIZA_TABAN_URL
    h.yaz("bekci", "x", ("sabit_not",))
    assert istenen == [secrets.HAFIZA_KRED_ADI] and c.cagrilar[0]["url"].startswith(secrets.HAFIZA_TABAN_URL + "/")


def test_api_kopyalariyla_ayrismaz():
    # `bot_hafiza` `api`yi İTHAL ETMEZ (FastAPI uygulamasını kurmak); iki ÖLÇÜLMÜŞ upstream sabiti bu yüzden KOPYADIR
    # ve bu çivi onların ayrışmasını yakalar (tek-kaynak yasasının kopya reçetesi).
    from meridian import api
    assert bh.UNUT_RECALL_MAX_TOKENS == api.HAFIZA_RECALL_TOKEN_TAVANI
    assert bh.BANKA_KOKU == api._HAFIZA_BANK_KOKU
    kaynak = inspect.getsource(bh)
    assert not re.search(r"^\s*(from \. import[^\n]*\bapi\b|from \.api |import meridian\.api)", kaynak, re.M)


def test_bot_kanal_hafiza_protokolunu_uygular():
    for ad in ("yaz", "unut"):
        beklenen = list(inspect.signature(getattr(bk.Hafiza, ad)).parameters)
        assert list(inspect.signature(getattr(bh.HindsightHafiza, ad)).parameters) == beklenen, ad


def test_kalici_silme_yontemi_kaynakta_yok():
    # Spec §3.4: kalıcı silme YOK. Yöntem sabitleri AST'ten okunur (şerh metni sayılmaz).
    sabitler = {n.value for n in ast.walk(ast.parse(inspect.getsource(bh)))
                if isinstance(n, ast.Constant) and isinstance(n.value, str)}
    assert "DELETE" not in sabitler and {"POST", "PATCH"} <= sabitler


# ---- gerçek sınıf `bota_sor` içinde (Review Focus 3: Hindsight erişilemezse operatöre sessiz kalınmaz) ---------

def _defter():
    return store.read_jsonl(bk.DEFTER)


def test_bota_sor_gercek_sinifla_hatirla_ve_unut(sandbox_state):
    c = Casus(recall=_recall(("m1", "cuma toplantısı iptal"), ("m2", "cuma yemeği")))
    h = _h(c)
    assert bk.bota_sor("sef", "hatırla: cuma toplantısı iptal", "pano", "o", hafiza=h, simdi=SIMDI) \
        == "Not aldım: cuma toplantısı iptal"
    cevap = bk.bota_sor("sef", "unut: cuma", "pano", "o", hafiza=h, simdi=SIMDI)
    assert cevap == "Unuttum (geri alınabilir): 1) cuma toplantısı iptal 2) cuma yemeği"
    assert [p["url"].rsplit("/", 1)[1] for p in c.patchler()] == ["m1", "m2"]
    s = _defter()[-1]
    assert (s["tur"], s["hafiza_durumu"], s["unutulan_idler"]) == ("unut", "unutuldu", ["m1", "m2"])


def test_bota_sor_gercek_sinif_hindsight_erisilemezse_yazilamadi_unutulamadi_ve_olay(sandbox_state, monkeypatch):
    def urlopen(istek, timeout=None):
        raise urllib.error.URLError("[Errno 61] Connection refused")

    monkeypatch.setattr(bh.urllib.request, "urlopen", urlopen)
    h = bh.HindsightHafiza(_anahtar=lambda: ANAHTAR)
    assert "YAZILAMADI" in bk.bota_sor("sef", "hatırla: x", "pano", "o", hafiza=h, simdi=SIMDI)
    assert "UNUTULAMADI" in bk.bota_sor("sef", "unut: x", "pano", "o", hafiza=h, simdi=SIMDI)
    olaylar = obs.recent(20)
    assert any(e.get("event") == "bot_hafiza_yazim_hatasi" and e.get("sinif") == "RuntimeError" for e in olaylar)
    assert any(e.get("event") == "bot_hafiza_unut_hatasi" and e.get("sinif") == "RuntimeError" for e in olaylar)
    assert _defter()[-1]["hafiza_durumu"] == "unutulamadi"


def test_bota_sor_gercek_sinif_anahtarsiz_sessiz_kalmaz(sandbox_state):
    c = Casus()
    h = bh.HindsightHafiza(_cagir=c, _anahtar=lambda: None)
    assert "YAZILAMADI" in bk.bota_sor("sef", "hatırla: x", "pano", "o", hafiza=h, simdi=SIMDI)
    assert "UNUTULAMADI" in bk.bota_sor("sef", "unut: x", "pano", "o", hafiza=h, simdi=SIMDI)
    assert c.cagrilar == []
