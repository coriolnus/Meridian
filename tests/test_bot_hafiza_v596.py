"""v596 — konuşan filo Hindsight hafıza yazıcısı `bot_hafiza.HindsightHafiza` (plan 2026-09-29 Parça 1b-ön Görev 2;
spec 2026-09-29 §3.4). `hatırla:` → retain, `unut:` → recall + en fazla `UNUT_TAVANI` bellek için GERİ ALINABİLİR
`state: invalidated`, `geri_al` → `state: valid`. Kalıcı silme yolu YOK.

AĞ YOK: her çivi ya sahte `_cagir` taşır ya da `urlopen`u yamar — gerçek 8888'e hiçbir istek gitmez. `bota_sor`
üzerinden koşan (olay yazabilen) her çivi `sandbox_state` alır.

Parça 1b G1 Görev 2 (2026-09-30): `ara(bot, soru, k)` — MCP `bot_hafizasi_ara` aracının gövdesi. SALT-OKUR: tek
recall POST'u, PATCH/DELETE YOK; dönüş `[(tarih, metin), …]` (tarih ölçülmüş okuyucunun alan sırasıyla,
yoksa "(tarih yok)"); metin ÖNCE scrub SONRA `ARA_KESIT_TAVANI`; zarf tanınmazsa hata ("sonuç yok" uydurulmaz).

Parça 1b G4 Görev 2 (2026-09-30): tek adımlı `unut` EMEKLİ — `unut_adaylari` (SALT-OKUR recall, PATCH YOK) +
`unut_uygula` (en fazla `UNUT_TAVANI` PATCH `invalidated`; hata istisnası `denenen`/`kalan`/`unutulanlar` taşır);
tanınmayan bellek kimliğinin `neden`i `kimlik` (eskiden `bicim`).
"""
import ast
import datetime as dt
import http.client
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
                raise bh._hata("hindsight HTTP 500", "http_500")      # varsayılan yolun işaretlediği biçim
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


# ---- unut iki adım: unut_adaylari (salt-okur recall) + unut_uygula (invalidated) — G4 Görev 2 -------------------

def test_unut_adaylari_salt_okur_tek_recall_patch_yok_en_fazla_uc():
    # İlk adım HİÇBİR ŞEYİ değiştirmez (plan Review Focus 2): tek recall POST'u, PATCH/DELETE/retain YOK.
    c = Casus(recall=_recall(("m1", "eski not bir"), ("m2", "eski not iki"), ("m3", "eski not üç"),
                             ("m4", "dördüncü"), ("m5", "beşinci")))
    donen = _h(c).unut_adaylari("bekci", "  eski not ")
    assert donen == [("m1", "eski not bir"), ("m2", "eski not iki"), ("m3", "eski not üç")]
    (recall,) = c.cagrilar
    assert (recall["yontem"], recall["url"]) == ("POST", f"{TABAN}/v1/default/banks/bot-bekci/memories/recall")
    assert recall["govde"] == {"query": "eski not", "budget": "low", "max_tokens": bh.UNUT_RECALL_MAX_TOKENS}
    assert bh.UNUT_TAVANI == 3


def test_unut_adaylari_recall_bossa_bos_liste():
    c = Casus(recall={"results": []})
    assert _h(c).unut_adaylari("bekci", "hiç yazılmamış bir şey") == [] and len(c.cagrilar) == 1


@pytest.mark.parametrize("zarf", ["liste", "items", "results", "memories", "data"])
def test_unut_adaylari_recall_zarfi_olculmus_okuyucu_kadar_toleransli(zarf):
    # Ölçülen okuyucu `deploy/hindsight/hafiza_sor.sh`: liste ise kendisi, değilse items|results|memories|data.
    dizi = [{"id": "m1", "text": "eski not"}]
    c = Casus(recall=dizi if zarf == "liste" else {zarf: dizi, "trace": {}})
    assert _h(c).unut_adaylari("bekci", "eski") == [("m1", "eski not")]
    assert c.patchler() == []


@pytest.mark.parametrize("cevap", [{"sonuclar": []}, {"results": "x"}, "x", None, 3])
def test_unut_adaylari_recall_zarfi_taninmazsa_hata_neden_bicim(cevap):
    # Tanınmayan zarf "eşleşme yok" SAYILMAZ: operatöre "hiçbir şey bulunamadı" demek ölçülmemiş bir iddia olurdu.
    c = Casus(recall=cevap)
    with pytest.raises(RuntimeError) as e:
        _h(c).unut_adaylari("bekci", "eski")
    assert bh.hata_nedeni(e.value) == "bicim" and c.patchler() == []


@pytest.mark.parametrize("kayit", [{"text": "kimliksiz"}, {"id": "../m1", "text": "x"}, {"id": "a/b", "text": "x"},
                                   {"id": 7, "text": "x"}, {"id": "", "text": "x"}, "düz-metin"])
def test_unut_adaylari_ilk_uc_sonucta_kimlik_taninmazsa_neden_kimlik(kayit):
    # Kimlik URL YOLUNA girer; biri bile tanınmazsa aday listesi VERİLMEZ (yarım liste operatöre sessiz kalırdı).
    # Task 1 kaygısı K-5 (Rol-1 2026-09-30): bu hata `bicim` değil, kendi kapalı-küme nedeni `kimlik`.
    c = Casus(recall={"results": [{"id": "m1", "text": "iyi"}, kayit]})
    with pytest.raises(RuntimeError) as e:
        _h(c).unut_adaylari("bekci", "eski")
    assert e.value.neden == "kimlik" and bh.hata_nedeni(e.value) == "kimlik"
    assert c.patchler() == []


def test_unut_adaylari_kesit_once_scrub_sonra_80_tavan():
    anahtar = "sk-or-v1-" + "a" * 64
    metin = "x" * 60 + " " + anahtar + "\n" + "y" * 100
    ((_, kesit),) = _h(Casus(recall=_recall(("m1", metin)))).unut_adaylari("bekci", "x")
    assert len(kesit) <= 80 and "sk-or-v1-" not in kesit and "\n" not in kesit


def test_unut_adaylari_metinsiz_sonuc_kesiti_uydurulmaz():
    ((_, kesit),) = _h(Casus(recall={"results": [{"id": "m1"}]})).unut_adaylari("bekci", "x")
    assert kesit == "(metin yok)"


@pytest.mark.parametrize("ifade", ["", "   ", "\n", None])
def test_unut_adaylari_bos_ifade_http_oncesi_reddedilir(ifade):
    # Boş sorgu recall'da rastgele en yakın bellekleri döndürür — aday listesi operatörün seçimi olmazdı.
    c = Casus(recall=_recall(("m1", "x")))
    with pytest.raises(ValueError):
        _h(c).unut_adaylari("bekci", ifade)
    assert c.cagrilar == []


def test_unut_uygula_en_fazla_uc_patch_invalidated_ve_geri_alinabilir_neden():
    c = Casus()
    assert _h(c).unut_uygula("bekci", ["m1", "m2", "m3"], "eski not") == ["m1", "m2", "m3"]
    patchler = c.cagrilar
    assert [p["url"] for p in patchler] == [f"{TABAN}/v1/default/banks/bot-bekci/memories/m{i}" for i in (1, 2, 3)]
    assert all(p["yontem"] == "PATCH" and p["basliklar"] == {"Authorization": f"Bearer {ANAHTAR}"}
               and p["zaman_asimi"] == bh.HAFIZA_ZAMAN_ASIMI_S for p in patchler)
    for p in patchler:
        assert set(p["govde"]) == {"state", "reason"} and p["govde"]["state"] == "invalidated"
        m = re.fullmatch(r"operatör unut: eski not \((.+)\)", p["govde"]["reason"])
        assert m and _utc_mu(m.group(1))


@pytest.mark.parametrize("idler", [[], ["m1", "m2", "m3", "m4"], "m1", None, ("m1",) * 0])
def test_unut_uygula_bos_ya_da_tavan_ustu_liste_http_oncesi_reddedilir(idler):
    c = Casus()
    with pytest.raises(ValueError) as e:
        _h(c).unut_uygula("bekci", idler, "x")
    assert c.cagrilar == [] and e.value.denenen == [] and e.value.unutulanlar == []


@pytest.mark.parametrize("idler", [["m1", "../x"], ["m1", "a/b"], ["m1", 7], ["", "m1"]])
def test_unut_uygula_gecersiz_kimlikte_hic_patch_atilmaz_neden_kimlik(idler):
    # Kimlikler bekleyen kayıttan (`state/`) gelir; dış hasar URL yoluna girmesin — biri bile tanınmazsa HİÇBİRİ.
    c = Casus()
    with pytest.raises(ValueError) as e:
        _h(c).unut_uygula("bekci", idler, "x")
    assert c.cagrilar == [] and bh.hata_nedeni(e.value) == "kimlik"
    assert (e.value.denenen, e.value.kalan, e.value.unutulanlar) == ([], list(idler), [])


def test_unut_uygula_kismi_hata_denenen_kalan_unutulanlar_tasir():
    # 2. PATCH düşerse 1. zaten emekliye ayrılmıştır; 2. de SUNUCUDA uygulanmış olabilir (zaman aşımı) — `denenen`
    # hata vereni de taşır ki geri alma onu da kapsasın; `kalan` hiç denenmeyendir (Rol-1 kararı 4, 2026-09-30).
    c = Casus(patch_hatasi_sirasi=1)
    with pytest.raises(RuntimeError) as e:
        _h(c).unut_uygula("bekci", ["m1", "m2", "m3"], "x")
    assert (e.value.unutulanlar, e.value.denenen, e.value.kalan) == (["m1"], ["m1", "m2"], ["m3"])
    assert len(c.patchler()) == 2 and bh.hata_nedeni(e.value) == "http_500"


def test_unut_uygula_anahtar_yoksa_istek_atilmaz_denenen_bos():
    c = Casus()
    with pytest.raises(RuntimeError) as e:
        bh.HindsightHafiza(_cagir=c, _anahtar=lambda: None).unut_uygula("bekci", ["m1", "m2"], "x")
    assert c.cagrilar == [] and bh.hata_nedeni(e.value) == "anahtar_yok"
    assert (e.value.denenen, e.value.kalan, e.value.unutulanlar) == ([], ["m1", "m2"], [])


def test_tek_adimli_unut_emekli():
    # Tek adımlı `unut` (recall + PATCH aynı çağrıda) G4 Görev 2 ile EMEKLİ: ilk adım PATCH atamaz olsun diye yöntem
    # ikiye bölündü. Eski yöntem ne sınıfta ne protokolde kalır — geri dönüşü sessiz olmasın.
    assert not hasattr(bh.HindsightHafiza, "unut") and not hasattr(bk.Hafiza, "unut")
    assert "def unut(" not in inspect.getsource(bh)


# ---- ara (salt-okur recall — MCP `bot_hafizasi_ara`) -------------------------------------------------------

def test_ara_tek_recall_post_patch_yok_ve_k_sonuc():
    c = Casus(recall={"results": [
        {"id": "m1", "text": "cuma toplantısı iptal", "occurred_start": "2026-09-26T09:00:00Z",
         "mentioned_at": "2026-09-27T10:00:00Z"},
        {"id": "m2", "text": "cuma yemeği", "mentioned_at": "2026-09-28T11:00:00Z"},
        {"id": "m3", "text": "üçüncü"}]})
    donen = _h(c).ara("bekci", "  cuma  ", k=2)
    assert donen == [("2026-09-26T09:00:00Z", "cuma toplantısı iptal"), ("2026-09-28T11:00:00Z", "cuma yemeği")]
    (cagri,) = c.cagrilar                                    # TEK çağrı: PATCH / DELETE / retain YOK
    assert (cagri["yontem"], cagri["url"]) == ("POST", f"{TABAN}/v1/default/banks/bot-bekci/memories/recall")
    assert cagri["govde"] == {"query": "cuma", "budget": bh.UNUT_RECALL_BUTCESI,
                              "max_tokens": bh.UNUT_RECALL_MAX_TOKENS}
    assert cagri["basliklar"] == {"Authorization": f"Bearer {ANAHTAR}"} and cagri["zaman_asimi"] == 10.0


def test_ara_varsayilan_k_bes():
    c = Casus(recall={"results": [{"id": f"m{i}", "text": f"not {i}"} for i in range(9)]})
    assert [m for _, m in _h(c).ara("bekci", "not")] == [f"not {i}" for i in range(5)]


def test_ara_tarih_yoksa_uydurulmaz_metin_yoksa_soylenir():
    c = Casus(recall={"results": [{"id": "m1", "text": "tarihsiz"}, {"id": "m2", "occurred_start": 7},
                                  {"id": "m3", "text": "  "}]})
    assert _h(c).ara("bekci", "x") == [("(tarih yok)", "tarihsiz"), ("(tarih yok)", "(metin yok)"),
                                        ("(tarih yok)", "(metin yok)")]


def test_ara_metin_once_scrub_sonra_tavan():
    anahtar = "sk-or-v1-" + "a" * 64
    uzun = "x" * (bh.ARA_KESIT_TAVANI - 20) + " " + anahtar + "\n" + "y" * 900
    ((_, metin),) = _h(Casus(recall=_recall(("m1", uzun)))).ara("bekci", "x")
    assert "sk-or-v1-" not in metin and "\n" not in metin
    # tam tavanda kesilir: daha kısa bir tavan (ör. `unut`un 80'i) modele eksik bellek metni verirdi
    assert len(metin) == bh.ARA_KESIT_TAVANI and metin.endswith("…")


def test_ara_recall_bossa_bos_liste():
    c = Casus(recall={"results": []})
    assert _h(c).ara("bekci", "hiç yazılmamış") == [] and len(c.cagrilar) == 1


@pytest.mark.parametrize("cevap", [{"sonuclar": []}, {"results": "x"}, "x", None, 3,
                                   {"results": [{"id": "m1", "text": "iyi"}, "düz-metin"]}])
def test_ara_taninmayan_cevap_bos_sayilmaz(cevap):
    # Tanınmayan zarf ya da sonuç öğesi "hafızada yok" demek olmaz — ölçülmemiş bir iddia olurdu.
    with pytest.raises(RuntimeError):
        _h(Casus(recall=cevap)).ara("bekci", "x")


@pytest.mark.parametrize("soru", ["", "   ", "\n", None])
def test_ara_bos_soru_http_oncesi_reddedilir(soru):
    c = Casus()
    with pytest.raises(ValueError):
        _h(c).ara("bekci", soru)
    assert c.cagrilar == []


@pytest.mark.parametrize("k", [0, -1, True, "5", 2.0, None])
def test_ara_k_gecersizse_http_oncesi_reddedilir(k):
    c = Casus()
    with pytest.raises(ValueError):
        _h(c).ara("bekci", "x", k=k)
    assert c.cagrilar == []


def test_ara_varsayilan_http_yolu_post_recall(monkeypatch):
    gorulen = {}

    def urlopen(istek, timeout=None):
        gorulen.update(istek=istek, timeout=timeout)
        return _Cevap(json.dumps({"results": [{"id": "m1", "text": "not"}]}).encode())

    monkeypatch.setattr(bh.urllib.request, "urlopen", urlopen)
    assert bh.HindsightHafiza(_anahtar=lambda: ANAHTAR).ara("sef", "not") == [("(tarih yok)", "not")]
    istek = gorulen["istek"]
    assert istek.get_method() == "POST" and gorulen["timeout"] == 10.0
    assert istek.full_url == f"{TABAN}/v1/default/banks/bot-sef/memories/recall"


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
    with pytest.raises(ValueError) as e:
        _h(c).geri_al("bekci", kimlik)
    assert c.cagrilar == [] and bh.hata_nedeni(e.value) == "kimlik"


# ---- ortak kapılar ------------------------------------------------------------------------------------------

ISLEMLER = ("yaz", "unut_adaylari", "unut_uygula", "geri_al", "ara", "donus_yaz")


def _islem(h, islem, bot="bekci"):
    return {"yaz": lambda: h.yaz(bot, "x", ("sabit_not",)), "unut_adaylari": lambda: h.unut_adaylari(bot, "x"),
            "unut_uygula": lambda: h.unut_uygula(bot, ["m1"], "x"),
            "geri_al": lambda: h.geri_al(bot, "m1"), "ara": lambda: h.ara(bot, "x"),
            "donus_yaz": lambda: h.donus_yaz(bot, "x", "y", ("sohbet_donusu",))}[islem]


@pytest.mark.parametrize("bot", ["../x", "a/b", "Bekci", "", "bekci?k=1", "bekci-1"])
@pytest.mark.parametrize("islem", ISLEMLER)
def test_bot_adi_http_oncesi_reddedilir(bot, islem):
    c = Casus()
    with pytest.raises(ValueError):
        _islem(_h(c), islem, bot)()
    assert c.cagrilar == []


@pytest.mark.parametrize("islem", ISLEMLER)
def test_anahtar_yoksa_istek_atilmaz_ve_hata_metni_sabit(islem):
    c = Casus()
    with pytest.raises(RuntimeError) as e:
        _islem(bh.HindsightHafiza(_cagir=c, _anahtar=lambda: None), islem)()
    assert str(e.value) == "hindsight kiracı anahtarı credential yok" and c.cagrilar == []
    assert e.value.neden == "anahtar_yok" and bh.hata_nedeni(e.value) == "anahtar_yok"


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
        bh.HindsightHafiza(_anahtar=lambda: "GIZLIANAHTAR" + "Z" * 20).unut_adaylari("bekci", "x")
    assert str(e.value) == f"hindsight {type(hata).__name__}" and "GIZLI" not in str(e.value)
    assert e.value.__cause__ is None and e.value.__suppress_context__ is True


def test_varsayilan_yol_json_olmayan_govde_sinyalli(monkeypatch):
    monkeypatch.setattr(bh.urllib.request, "urlopen", lambda istek, timeout=None: _Cevap(b"<html>gizli</html>"))
    with pytest.raises(RuntimeError) as e:
        bh.HindsightHafiza(_anahtar=lambda: ANAHTAR).unut_adaylari("bekci", "x")
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
    # G4 Görev 2: tek adımlı `unut` yerine iki adım + geri alma protokolde (emeklilik çivisi `test_tek_adimli_unut_emekli`).
    for ad in ("yaz", "unut_adaylari", "unut_uygula", "geri_al", "donus_yaz"):
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


def _kod():
    """Son `unut:` ilk adımının verdiği kısa kod — defter satırından (operatörün gördüğü cevapla aynı kod)."""
    return next(s for s in reversed(_defter()) if s["tur"] == "unut")["unut_kodu"]


def test_bota_sor_gercek_sinifla_hatirla_ve_iki_adimli_unut_ve_geri_al(sandbox_state):
    c = Casus(recall=_recall(("m1", "cuma toplantısı iptal"), ("m2", "cuma yemeği")))
    h = _h(c)
    assert bk.bota_sor("sef", "hatırla: cuma toplantısı iptal", "pano", "o", hafiza=h, simdi=SIMDI) \
        == "Not aldım: cuma toplantısı iptal"
    cevap = bk.bota_sor("sef", "unut: cuma", "pano", "o", hafiza=h, simdi=SIMDI)
    kod = _kod()
    assert "1) cuma toplantısı iptal 2) cuma yemeği" in cevap and f"onayla: unut {kod}" in cevap
    assert c.patchler() == []                                   # İLK ADIM HİÇBİR ŞEYİ DEĞİŞTİRMEZ (casus)
    cevap = bk.bota_sor("sef", f"onayla: unut {kod}", "pano", "o", hafiza=h, simdi=SIMDI + dt.timedelta(minutes=5))
    assert cevap.startswith("Unuttum") and f"geri al: {kod}" in cevap
    assert [p["url"].rsplit("/", 1)[1] for p in c.patchler()] == ["m1", "m2"]
    assert all(p["govde"]["state"] == "invalidated" and p["govde"]["reason"].startswith("operatör unut: cuma (")
               for p in c.patchler())
    s = _defter()[-1]
    assert (s["tur"], s["hafiza_durumu"], s["unutulan_idler"], s["denenen"], s["kalan"]) == (
        "unut_onay", "unutuldu", ["m1", "m2"], ["m1", "m2"], [])
    bk.bota_sor("sef", f"geri al: {kod}", "pano", "o", hafiza=h, simdi=SIMDI + dt.timedelta(hours=2))
    assert [(p["url"].rsplit("/", 1)[1], p["govde"]) for p in c.patchler()[2:]] == [
        ("m1", {"state": "valid"}), ("m2", {"state": "valid"})]
    assert (_defter()[-1]["tur"], _defter()[-1]["hafiza_durumu"]) == ("geri_al", "geri_alindi")


def test_bota_sor_gercek_sinifla_onay_en_fazla_uc_patch(sandbox_state):
    c = Casus(recall=_recall(*[(f"m{i}", f"not {i}") for i in range(1, 6)]))
    h = _h(c)
    bk.bota_sor("bekci", "unut: not", "pano", "o", hafiza=h, simdi=SIMDI)
    bk.bota_sor("bekci", f"onayla: unut {_kod()}", "pano", "o", hafiza=h, simdi=SIMDI)
    assert len(c.patchler()) == bh.UNUT_TAVANI == 3


def test_bota_sor_gercek_sinifla_kismi_patch_hatasi_denenen_kalan_deftere(sandbox_state):
    c = Casus(recall=_recall(("m1", "bir"), ("m2", "iki"), ("m3", "üç")), patch_hatasi_sirasi=1)
    h = _h(c)
    bk.bota_sor("bekci", "unut: x", "pano", "o", hafiza=h, simdi=SIMDI)
    kod = _kod()
    cevap = bk.bota_sor("bekci", f"onayla: unut {kod}", "pano", "o", hafiza=h, simdi=SIMDI)
    assert cevap.startswith("UNUTULAMADI") and "1) bir" in cevap and f"geri al: {kod}" in cevap
    s = _defter()[-1]
    assert (s["tur"], s["hafiza_durumu"], s["unutulan_idler"], s["denenen"], s["kalan"]) == (
        "unut_onay", "unutulamadi", ["m1"], ["m1", "m2"], ["m3"])
    olay = [e for e in obs.recent(20) if e.get("event") == "bot_hafiza_unut_hatasi"][-1]
    assert (olay["neden"], olay["adim"], olay["sinif"]) == ("http_500", "onay", "RuntimeError")


def test_bota_sor_gercek_sinif_hindsight_erisilemezse_yazilamadi_aranamadi_ve_olay(sandbox_state, monkeypatch):
    def urlopen(istek, timeout=None):
        raise urllib.error.URLError("[Errno 61] Connection refused")

    monkeypatch.setattr(bh.urllib.request, "urlopen", urlopen)
    h = bh.HindsightHafiza(_anahtar=lambda: ANAHTAR)
    assert "YAZILAMADI" in bk.bota_sor("sef", "hatırla: x", "pano", "o", hafiza=h, simdi=SIMDI)
    assert "ARANAMADI" in bk.bota_sor("sef", "unut: x", "pano", "o", hafiza=h, simdi=SIMDI)
    olaylar = obs.recent(20)
    assert any(e.get("event") == "bot_hafiza_yazim_hatasi" and e.get("sinif") == "RuntimeError" for e in olaylar)
    assert any(e.get("event") == "bot_hafiza_unut_hatasi" and e.get("sinif") == "RuntimeError"
               and e.get("neden") == "ag" and e.get("adim") == "aday" for e in olaylar)
    assert _defter()[-1]["hafiza_durumu"] == "aranamadi"


def test_bota_sor_gercek_sinif_anahtarsiz_sessiz_kalmaz(sandbox_state):
    c = Casus()
    h = bh.HindsightHafiza(_cagir=c, _anahtar=lambda: None)
    assert "YAZILAMADI" in bk.bota_sor("sef", "hatırla: x", "pano", "o", hafiza=h, simdi=SIMDI)
    assert "ARANAMADI" in bk.bota_sor("sef", "unut: x", "pano", "o", hafiza=h, simdi=SIMDI)
    assert c.cagrilar == []
    assert any(e.get("event") == "bot_hafiza_unut_hatasi" and e.get("neden") == "anahtar_yok" for e in obs.recent(20))


# ---- Parça 1b G4 Görev 1: `donus_yaz` (sohbet dönüşü kaydı) + yapısal `neden` -------------------------------------
# Spec §3.4 (2026-09-30 düzeltmesi): Hermes `auto_retain` KAPALI; dönüşü YALNIZ `bota_sor` bu yöntemle yazar. Retain
# `async: true` — Hindsight arka planda işler, hemen `success` + `operation_id` döner (A1 OpenAPI, 2026-09-30).

DONUS_ETIKETLERI = ("bot:bekci", "kanal:telegram", "sohbet_donusu")
RETAIN_ASYNC = {"success": True, "bank_id": "bot-bekci", "items_count": 1, "async": True,
                "operation_id": "op-1", "operation_ids": ["op-1"]}


def test_donus_yaz_istek_bicimi_async_baglam_kaynak_icerik():
    c = Casus(retain=RETAIN_ASYNC)
    assert _h(c).donus_yaz("bekci", "durum?", "rejim risk-on", DONUS_ETIKETLERI) == bh.DonusSonucu(True, "op-1")
    (cagri,) = c.cagrilar
    assert (cagri["yontem"], cagri["url"]) == ("POST", f"{TABAN}/v1/default/banks/bot-bekci/memories")
    assert cagri["basliklar"] == {"Authorization": f"Bearer {ANAHTAR}"}
    assert cagri["zaman_asimi"] == bh.DONUS_ZAMAN_ASIMI_S == 3.0     # Tur 2 (Rol-1 K-1): AYRI ve KISA
    (oge,) = cagri["govde"]["items"]
    assert _utc_mu(oge.pop("timestamp"))
    assert cagri["govde"] == {"items": [{"content": "Operatör: durum?\n@bekci: rejim risk-on",
                                         "context": "sohbet dönüşü", "tags": list(DONUS_ETIKETLERI),
                                         "metadata": {"kaynak": "bot_kanal"}}], "async": True}


def test_donus_ve_not_sabitleri_donuk():
    assert (bh.DONUS_TAVANI, bh.DONUS_BAGLAMI, bh.DONUS_KAYNAGI) == (2000, "sohbet dönüşü", "bot_kanal")
    assert bh.DONUS_ZAMAN_ASIMI_S == 3.0
    assert (bh.NOT_BAGLAMI, bh.NOT_KAYNAGI) == ("operatör notu", "operator")


def test_donus_yaz_her_parca_once_scrub_sonra_tavan():
    # Ters sırada tavan anahtarı ortadan böler, yarım anahtar desene uymaz ve kalıcı bankaya sızar.
    anahtar = "sk-or-v1-" + "a" * 64
    mesaj = "x" * (bh.DONUS_TAVANI - 10) + anahtar
    cevap = "y" * (bh.DONUS_TAVANI - 5) + anahtar + "z" * 50
    c = Casus(retain=RETAIN_ASYNC)
    _h(c).donus_yaz("bekci", mesaj, cevap, DONUS_ETIKETLERI)
    icerik = c.cagrilar[0]["govde"]["items"][0]["content"]
    assert "sk-or-v1-" not in icerik
    operator, bot = icerik.split("\n@bekci: ")
    assert operator == "Operatör: " + "x" * (bh.DONUS_TAVANI - 10) + "***"
    assert bot == ("y" * (bh.DONUS_TAVANI - 5) + "***" + "z" * 50)[:bh.DONUS_TAVANI]


def test_donus_yaz_success_false_ise_false():
    assert _h(Casus(retain={**RETAIN_ASYNC, "success": False})).donus_yaz("bekci", "x", "y", DONUS_ETIKETLERI) \
        == bh.DonusSonucu(False, "op-1")


@pytest.mark.parametrize("cevap", [None, {}, {"operation_id": "op-1"}, [], "tamam"])
def test_donus_yaz_cevabi_taninmazsa_yazildi_uydurulmaz_neden_bicim(cevap):
    with pytest.raises(RuntimeError) as e:
        _h(Casus(retain=cevap)).donus_yaz("bekci", "x", "y", DONUS_ETIKETLERI)
    assert e.value.neden == "bicim" and bh.hata_nedeni(e.value) == "bicim"


def test_yaz_govdesi_donus_kaydindan_etkilenmez():
    # `hatırla:` retain'i SENKRON kalır (bağlam "operatör notu", kaynak "operator") — dönüş kaydının `async: true`su
    # ona sızmaz; iki gövde yan yana ölçülür.
    c = Casus()
    h = _h(c)
    h.yaz("bekci", "not", ("sabit_not",))
    h.donus_yaz("bekci", "soru", "cevap", DONUS_ETIKETLERI)
    yaz, donus = (cg["govde"] for cg in c.cagrilar)
    assert (yaz["async"], yaz["items"][0]["context"], yaz["items"][0]["metadata"]) == (
        False, "operatör notu", {"kaynak": "operator"})
    assert (donus["async"], donus["items"][0]["context"], donus["items"][0]["metadata"]) == (
        True, "sohbet dönüşü", {"kaynak": "bot_kanal"})


# ---- yapısal `neden` (kapalı küme; mesaj metninden TÜRETİLMEZ) -----------------------------------------------------

@pytest.mark.parametrize("hata,neden", [
    (urllib.error.HTTPError(f"{TABAN}/x", 503, "Service Unavailable", {}, None), "http_503"),
    (urllib.error.HTTPError(f"{TABAN}/x", 401, "Unauthorized", {}, None), "http_401"),
    (urllib.error.URLError(ConnectionRefusedError(61, "Connection refused")), "ag"),
    (ConnectionResetError(54, "reset"), "ag"),
    (TimeoutError("timed out"), "zaman_asimi"),                                 # okuma sırasında soket zaman aşımı
    (urllib.error.URLError(TimeoutError("timed out")), "zaman_asimi"),          # bağlanırken (urllib sarar)
    (http.client.IncompleteRead(b"yarim"), "ag"),
    (ValueError("Invalid header value b'Bearer GIZLI\\n'"), "beklenmeyen"),     # istemci tarafı, ağ değil
])
def test_varsayilan_yol_istisnasi_yapisal_neden_tasir(monkeypatch, hata, neden):
    def urlopen(istek, timeout=None):
        raise hata

    monkeypatch.setattr(bh.urllib.request, "urlopen", urlopen)
    with pytest.raises(RuntimeError) as e:
        bh.HindsightHafiza(_anahtar=lambda: ANAHTAR).donus_yaz("bekci", "x", "y", DONUS_ETIKETLERI)
    assert e.value.neden == neden and bh.hata_nedeni(e.value) == neden
    assert "GIZLI" not in str(e.value)


def test_varsayilan_yol_json_olmayan_govde_neden_bicim(monkeypatch):
    monkeypatch.setattr(bh.urllib.request, "urlopen", lambda istek, timeout=None: _Cevap(b"<html>gizli</html>"))
    with pytest.raises(RuntimeError) as e:
        bh.HindsightHafiza(_anahtar=lambda: ANAHTAR).donus_yaz("bekci", "x", "y", DONUS_ETIKETLERI)
    assert bh.hata_nedeni(e.value) == "bicim"


def test_recall_zarfi_taninmazsa_neden_bicim():
    with pytest.raises(RuntimeError) as e:
        _h(Casus(recall={"sonuclar": []})).ara("bekci", "x")
    assert bh.hata_nedeni(e.value) == "bicim"


@pytest.mark.parametrize("hata", [
    RuntimeError("hindsight HTTP 500"),                  # MESAJ http der ama öznitelik yok → mesajdan türetilmez
    RuntimeError("hindsight TimeoutError"),
    ConnectionError("x"), TimeoutError("x"), ValueError("x"),
])
def test_hata_nedeni_isaretsiz_istisnada_beklenmeyen(hata):
    assert bh.hata_nedeni(hata) == "beklenmeyen"


@pytest.mark.parametrize("neden,beklenen", [
    ("anahtar_yok", "anahtar_yok"), ("ag", "ag"), ("zaman_asimi", "zaman_asimi"), ("bicim", "bicim"),
    ("kimlik", "kimlik"),                                   # G4 Görev 2 (Task 1 kaygısı K-5): bellek kimliği tanınmadı
    ("beklenmeyen", "beklenmeyen"), ("http_404", "http_404"),
    ("http_", "beklenmeyen"), ("http_abc", "beklenmeyen"), ("http_4040", "beklenmeyen"), ("gizli metin", "beklenmeyen"),
    (None, "beklenmeyen"), (7, "beklenmeyen"),
])
def test_hata_nedeni_kapali_kume(neden, beklenen):
    hata = RuntimeError("x")
    hata.neden = neden
    assert bh.hata_nedeni(hata) == beklenen


def test_hata_nedenleri_kumesi_donuk():
    # Olay sözlüğü kapalıdır: yeni neden bu satırı DÜZENLEYEREK gelir (brief arayüzü, G4 Görev 2).
    assert bh.HATA_NEDENLERI == ("anahtar_yok", "ag", "zaman_asimi", "bicim", "kimlik", "beklenmeyen")


# ---- gerçek sınıf `bota_sor` sohbet turunda (dönüş kaydı; Review Focus 1: hafıza hatası cevabı düşürmez) -------------

class _Tasiyici:
    def sor(self, bot, mesaj, oturum):
        return bk.TasiyiciSonuc("rejim risk-on", arac_cagrilari=1)


def test_bota_sor_gercek_sinifla_donus_kaydi_async_ve_scrubli(sandbox_state):
    anahtar = "sk-or-v1-" + "b" * 64
    c = Casus(retain=RETAIN_ASYNC)
    cevap = bk.bota_sor("bekci", f"durum? {anahtar}", "telegram", "o", tasiyici=_Tasiyici(), hafiza=_h(c),
                        simdi=SIMDI)
    assert cevap == "rejim risk-on"
    (cagri,) = c.cagrilar
    (oge,) = cagri["govde"]["items"]
    assert cagri["govde"]["async"] is True and anahtar not in json.dumps(cagri["govde"])
    assert oge["content"] == "Operatör: durum? ***\n@bekci: rejim risk-on"
    assert oge["tags"] == ["bot:bekci", "kanal:telegram", "sohbet_donusu"]
    s = _defter()[-1]
    assert (s["tur"], s["hafiza_durumu"], s["hafiza_islem_kimligi"]) == ("sohbet", "kabul_edildi", "op-1")


@pytest.mark.parametrize("hata,neden", [
    (urllib.error.URLError(ConnectionRefusedError(61, "Connection refused")), "ag"),
    (TimeoutError("timed out"), "zaman_asimi"),
    (urllib.error.HTTPError(f"{TABAN}/x", 500, "Internal", {}, None), "http_500"),
])
def test_bota_sor_gercek_sinif_hindsight_hatasinda_cevap_doner_yazilamadi_ve_nedenli_olay(sandbox_state, monkeypatch,
                                                                                         hata, neden):
    def urlopen(istek, timeout=None):
        raise hata

    monkeypatch.setattr(bh.urllib.request, "urlopen", urlopen)
    h = bh.HindsightHafiza(_anahtar=lambda: ANAHTAR)
    assert bk.bota_sor("bekci", "durum?", "pano", "o", tasiyici=_Tasiyici(), hafiza=h, simdi=SIMDI) == "rejim risk-on"
    assert _defter()[-1]["hafiza_durumu"] == "yazilamadi"
    olay = [e for e in obs.recent(20) if e.get("event") == "bot_hafiza_donus_hatasi"]
    assert olay and (olay[-1]["sinif"], olay[-1]["neden"], olay[-1]["kanal"]) == ("RuntimeError", neden, "pano")


def test_bota_sor_gercek_sinif_hatirla_hatasi_nedenli_olay(sandbox_state, monkeypatch):
    def urlopen(istek, timeout=None):
        raise urllib.error.URLError(ConnectionRefusedError(61, "Connection refused"))

    monkeypatch.setattr(bh.urllib.request, "urlopen", urlopen)
    h = bh.HindsightHafiza(_anahtar=lambda: ANAHTAR)
    assert "YAZILAMADI" in bk.bota_sor("sef", "hatırla: x", "pano", "o", hafiza=h, simdi=SIMDI)
    assert any(e.get("event") == "bot_hafiza_yazim_hatasi" and e.get("neden") == "ag" for e in obs.recent(20))


# ---- Tur 2 (Rol-1 K-1 kararı 2026-09-30): dönüş kaydının AYRI ve KISA zaman aşımı --------------------------------
# Dönüş kaydı operatörün cevabıyla AYNI turda senkron koşar (`hafiza_durumu` aynı defter satırında). `async: true` kabulü
# sağlıklı Hindsight'ta anında döner; ASILI Hindsight'ta cevap soket işlemi başına en fazla `DONUS_ZAMAN_ASIMI_S`
# gecikir. `HAFIZA_ZAMAN_ASIMI_S` (10 s) DEĞİŞMEZ — v599 onu Hermes profil yapılandırmasına bağlar; `yaz`/`unut`/`ara`
# onu kullanmaya devam eder.

def test_donus_zaman_asimi_hafiza_zaman_asimindan_kisa_ve_yalniz_donus_yazda():
    assert bh.DONUS_ZAMAN_ASIMI_S < bh.HAFIZA_ZAMAN_ASIMI_S == 10.0
    c = Casus(recall=_recall(("m1", "x")))
    h = _h(c)
    h.donus_yaz("bekci", "soru", "cevap", DONUS_ETIKETLERI)
    h.yaz("bekci", "not", ("sabit_not",))
    h.ara("bekci", "x")
    h.unut_adaylari("bekci", "x")
    h.unut_uygula("bekci", ["m1"], "x")
    h.geri_al("bekci", "m1")
    assert [cg["zaman_asimi"] for cg in c.cagrilar] == [bh.DONUS_ZAMAN_ASIMI_S] + [bh.HAFIZA_ZAMAN_ASIMI_S] * 5


def test_varsayilan_yol_donus_yaz_kisa_zaman_asimli_async_post(monkeypatch):
    # Üretimin TEK yolu (`_cagir` enjekte EDİLMEZ): kısa zaman aşımı urlopen'a GERÇEKTEN gider.
    gorulen = {}

    def urlopen(istek, timeout=None):
        gorulen.update(istek=istek, timeout=timeout)
        return _Cevap(json.dumps(RETAIN_ASYNC).encode())

    monkeypatch.setattr(bh.urllib.request, "urlopen", urlopen)
    assert bh.HindsightHafiza(_anahtar=lambda: ANAHTAR).donus_yaz("bekci", "soru", "cevap", DONUS_ETIKETLERI) \
        == bh.DonusSonucu(True, "op-1")
    istek = gorulen["istek"]
    assert gorulen["timeout"] == bh.DONUS_ZAMAN_ASIMI_S and istek.get_method() == "POST"
    assert istek.full_url == f"{TABAN}/v1/default/banks/bot-bekci/memories"
    assert json.loads(istek.data)["async"] is True


# ---- Tur 3 (görev incelemesi M-1, I-1) ----------------------------------------------------------------------------
# M-1: `async: true` retain'in `success`i KABULDÜR (çıkarım arka planda) — "işlendi" uydurulmaz; işlem kimliği
# (`operation_id`, yoksa `operation_ids[0]` — `ops/defter_ozeti_retain.py` emsali) deftere taşınsın diye döner.

@pytest.mark.parametrize("cevap,kimlik", [
    ({"success": True, "operation_id": "op-9", "operation_ids": ["op-8"]}, "op-9"),
    ({"success": True, "operation_ids": ["op-8", "op-7"]}, "op-8"),
    ({"success": True, "operation_id": None, "operation_ids": []}, None),
    ({"success": True}, None),
    ({"success": True, "operation_id": "../x"}, None),                         # URL/defter güvenli değil → yok
    ({"success": True, "operation_id": 7}, None),
    ({"success": True, "operation_id": "", "operation_ids": "op-1"}, None),
    ({"success": True, "operation_id": "123e4567-e89b-12d3-a456-426614174000"}, "123e4567-e89b-12d3-a456-426614174000"),
])
def test_donus_yaz_islem_kimligi_olculur_uydurulmaz(cevap, kimlik):
    assert _h(Casus(retain=cevap)).donus_yaz("bekci", "x", "y", DONUS_ETIKETLERI) == bh.DonusSonucu(True, kimlik)


def test_bota_sor_gercek_sinifla_uzun_telegram_alintisinda_operator_sorusu_kayitta(sandbox_state):
    # İnceleme I-1 (b), GERÇEK sınıf + gerçek üretici: 3000 karakterlik alıntıda bile kayıt operatörün sorusunu taşır,
    # alıntı gövdesini ve çit jetonlarını TAŞIMAZ.
    from meridian import telegram_dinleyici as td
    mesaj = td._bota_giden({"reply_to_message": {"text": "Rapor başlığı\n" + "z" * 3000}}, "bu kalem ne?")
    c = Casus(retain=RETAIN_ASYNC)
    bk.bota_sor("bekci", mesaj, "telegram", "o", tasiyici=_Tasiyici(), hafiza=_h(c), simdi=SIMDI)
    icerik = c.cagrilar[0]["govde"]["items"][0]["content"]
    assert icerik == "Operatör: (yanıt: Rapor başlığı)\nbu kalem ne?\n@bekci: rejim risk-on"
    assert "zzz" not in icerik and "VERI" not in icerik
