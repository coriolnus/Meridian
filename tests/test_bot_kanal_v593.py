"""v593 — konuşan filo kanal çekirdeği bota_sor (spec 2026-09-29 §3.4-§3.7): doğrulama, kota, hatırla/unut, defter, taşıyıcı."""
import datetime as dt
import io
import json
import urllib.error

import pytest

from meridian import bot_kanal as bk, kadro, obs, store

SIMDI = dt.datetime(2026, 9, 29, 12, 0, tzinfo=dt.timezone.utc)


class SahteTasiyici:
    def __init__(self, metin="cevap", hata=None):
        self.cagrilar, self.metin, self.hata = [], metin, hata

    def sor(self, bot, mesaj, oturum):
        self.cagrilar.append((bot, mesaj, oturum))
        if self.hata:
            raise self.hata
        return bk.TasiyiciSonuc(self.metin, arac_cagrilari=2, model_cagrilari=3)


class SahteHafiza:
    def __init__(self, sonuc=True):
        self.yazilanlar, self.sonuc = [], sonuc

    def yaz(self, bot, metin, etiketler):
        self.yazilanlar.append((bot, metin, etiketler))
        return self.sonuc


def _defter():
    return store.read_jsonl(bk.DEFTER)


def test_normal_soru_tasiyiciya_gider_ve_deftere_yazilir(sandbox_state):
    t = SahteTasiyici("rejim risk-on")
    assert bk.bota_sor("bekci", "durum?", "telegram", "tg-bekci-1", tasiyici=t, simdi=SIMDI) == "rejim risk-on"
    assert t.cagrilar == [("bekci", "durum?", "tg-bekci-1")]
    s = _defter()[-1]
    assert (s["bot"], s["kanal"], s["oturum"], s["tur"]) == ("bekci", "telegram", "tg-bekci-1", "sohbet")
    assert s["arac_cagrilari"] == 2 and s["model_cagrilari"] == 3 and s["kota_bugun"] == 1


@pytest.mark.parametrize("bot,kanal", [("kod", "telegram"), ("yok", "pano"), ("bekci", "faks")])
def test_gecersiz_bot_ya_da_kanal_reddedilir(sandbox_state, bot, kanal):
    with pytest.raises(ValueError):
        bk.bota_sor(bot, "x", kanal, "o", tasiyici=SahteTasiyici(), simdi=SIMDI)


def test_kota_doluysa_tasiyici_cagrilmaz(sandbox_state):
    k = tuple(kadro.Bot(**{**b.__dict__, "gunluk_tavan": 1, "gunluk_tavan_neden": None})
              if b.ad == "karne" else b for b in kadro.kadro_yukle())
    t = SahteTasiyici()
    bk.bota_sor("karne", "1", "pano", "o", tasiyici=t, simdi=SIMDI, kadro=k)
    cevap = bk.bota_sor("karne", "2", "pano", "o", tasiyici=t, simdi=SIMDI, kadro=k)
    assert "kotam doldu" in cevap and "(1/1)" in cevap and len(t.cagrilar) == 1
    assert _defter()[-1]["tur"] == "kota_doldu"


def test_kota_gun_donumunde_sifirlanir(sandbox_state):
    k = tuple(kadro.Bot(**{**b.__dict__, "gunluk_tavan": 1, "gunluk_tavan_neden": None})
              if b.ad == "karne" else b for b in kadro.kadro_yukle())
    t = SahteTasiyici()
    bk.bota_sor("karne", "1", "pano", "o", tasiyici=t, simdi=SIMDI, kadro=k)
    ertesi = SIMDI + dt.timedelta(days=1)
    assert bk.bota_sor("karne", "2", "pano", "o", tasiyici=t, simdi=ertesi, kadro=k) == "cevap"


def test_tavan_none_sayilir_ama_sinirlamaz(sandbox_state):
    t = SahteTasiyici()
    for i in range(5):
        bk.bota_sor("sef", str(i), "pano", "o", tasiyici=t, simdi=SIMDI)
    assert len(t.cagrilar) == 5 and bk.gunluk_sayim("sef", "2026-09-29") == 5


@pytest.mark.parametrize("onek", ["hatırla:", "HATIRLA:", "hatirla :", "Hatırla:"])
def test_hatirla_modele_gitmez_hafizaya_yazilir(sandbox_state, onek):
    t, h = SahteTasiyici(), SahteHafiza()
    cevap = bk.bota_sor("sef", f"{onek} cuma toplantısı iptal", "telegram", "o", tasiyici=t, hafiza=h, simdi=SIMDI)
    assert t.cagrilar == [] and h.yazilanlar[0][:2] == ("sef", "cuma toplantısı iptal")
    assert "sabit_not" in h.yazilanlar[0][2] and "kanal:telegram" in h.yazilanlar[0][2]
    assert "Not aldım" in cevap and _defter()[-1]["tur"] == "hatirla"


def test_hatirla_bos_govde_sorar(sandbox_state):
    # RULING (uygulayıcı, 2026-09-29): brief mesajı "Neyi hatırlayayım? …" (büyük N) ile brief
    # çivisinin `"neyi" in cevap` iddiası çelişiyordu — mesaj brief'teki gibi korundu, iddia harf
    # duyarsız yapıldı (niyet: "gövdesiz not → ne hatırlanacağı SORULUR").
    h = SahteHafiza()
    assert "neyi" in bk.bota_sor("sef", "hatırla:   ", "pano", "o", tasiyici=SahteTasiyici(), hafiza=h,
                                 simdi=SIMDI).lower()
    assert h.yazilanlar == []


def test_hatirla_hafiza_bagli_degilse_acik_soyler(sandbox_state):
    cevap = bk.bota_sor("sef", "hatırla: x", "pano", "o", tasiyici=SahteTasiyici(), simdi=SIMDI)
    assert "henüz bağlı değil" in cevap
    assert any(e.get("event") == "bot_hafiza_bagli_degil" for e in obs.recent(20))


def test_unut_henuz_hazir_degil_ve_sinyalli(sandbox_state):
    t = SahteTasiyici()
    cevap = bk.bota_sor("bekci", "unut: eski not", "telegram", "o", tasiyici=t, simdi=SIMDI)
    assert t.cagrilar == [] and "henüz hazır değil" in cevap
    assert _defter()[-1]["tur"] == "unut"


def test_tasiyici_hatasi_defterde_ve_yukari_firlar(sandbox_state):
    with pytest.raises(TimeoutError):
        bk.bota_sor("bekci", "x", "telegram", "o", tasiyici=SahteTasiyici(hata=TimeoutError("zaman")), simdi=SIMDI)
    s = _defter()[-1]
    assert s["tur"] == "hata" and s["hata"] == "TimeoutError"


def test_defter_scrub_ve_cevap_tavani(sandbox_state):
    anahtar = "sk-or-v1-" + "a" * 64
    bk.bota_sor("sef", f"anahtarım {anahtar}", "pano", "o", tasiyici=SahteTasiyici("y" * 5000), simdi=SIMDI)
    s = _defter()[-1]
    assert anahtar not in json.dumps(s) and len(s["cevap"]) == bk.CEVAP_TAVANI and s["kesildi"] is True


def test_defter_yazim_hatasi_cevabi_dusurmez(sandbox_state, monkeypatch):
    # RULING (uygulayıcı, 2026-09-29, ölçüldü): brief'in `patla`sı `store.append_jsonl`i KOŞULSUZ
    # düşürüyordu; `obs._emit` olayı da AYNI fonksiyonla `events.jsonl`e aynalar, yani olay hiçbir
    # zaman deftere düşemez ve `obs.recent` onu göremezdi (çivi uygulamadan bağımsız kırmızı).
    # Arıza yalnız konuşma defterine uygulanır — ölçülen şey "defter düşer, olay yazılır, cevap döner".
    asil = store.append_jsonl

    def patla(ad, satir):
        if ad == bk.DEFTER:
            raise OSError("disk dolu")
        return asil(ad, satir)
    monkeypatch.setattr(bk.store, "append_jsonl", patla)
    assert bk.bota_sor("sef", "x", "pano", "o", tasiyici=SahteTasiyici("tamam"), simdi=SIMDI) == "tamam"
    assert any(e.get("event") == "bot_defter_yazim_hatasi" for e in obs.recent(20))


def test_hermes_tasiyici_istek_bicimi_ve_jetonsuz_hata():
    gorulen = {}

    def cagir(url, govde, basliklar, zaman_asimi):
        gorulen.update(url=url, govde=govde, basliklar=basliklar, zaman_asimi=zaman_asimi)
        return {"choices": [{"message": {"content": "tamam"}}]}

    t = bk.HermesTasiyici(_cagir=cagir, _anahtar=lambda: "K" * 32, zaman_asimi_s=7)
    assert t.sor("karne", "soru", "tg-karne-1").metin == "tamam"
    assert gorulen["url"] == "http://127.0.0.1:8642/p/karne/v1/chat/completions"
    assert gorulen["basliklar"]["X-Hermes-Session-Id"] == "tg-karne-1" and gorulen["zaman_asimi"] == 7
    assert gorulen["govde"]["messages"] == [{"role": "user", "content": "soru"}]
    with pytest.raises(RuntimeError) as e:
        bk.HermesTasiyici(_cagir=cagir, _anahtar=lambda: None).sor("karne", "x", "o")
    assert "K" * 8 not in str(e.value)


# ---- brief dışı ek çiviler (uygulayıcı): spec §3.4 scrub, hafıza-yazamadı dalı, varsayılan HTTP yolu ----

def test_unut_olayi_yazilir(sandbox_state):
    bk.bota_sor("bekci", "Unut: eski not", "telegram", "o", tasiyici=SahteTasiyici(), simdi=SIMDI)
    assert any(e.get("event") == "bot_unut_hazir_degil" and e.get("bot") == "bekci" for e in obs.recent(20))


def test_hatirla_govdesi_hafizaya_scrub_ile_gider(sandbox_state):
    # spec §3.4: "kayıt öncesi notify.scrub" — sabit not da bir hafıza kaydıdır.
    anahtar = "sk-or-v1-" + "b" * 64
    h = SahteHafiza()
    bk.bota_sor("sef", f"hatırla: yeni anahtar {anahtar}", "pano", "o", hafiza=h, simdi=SIMDI)
    assert h.yazilanlar and anahtar not in h.yazilanlar[0][1] and "yeni anahtar" in h.yazilanlar[0][1]


def test_defter_cevaptaki_sirri_da_keserken_de_maskeler(sandbox_state):
    # Model cevabı bir sırrı yankılayabilir. Sıra: ÖNCE scrub, SONRA tavan — ters sırada tavan anahtarı
    # ortadan böler, yarım anahtar desene uymaz ve deftere sızar.
    anahtar = "sk-or-v1-" + "c" * 64
    bk.bota_sor("sef", "x", "pano", "o", tasiyici=SahteTasiyici("y" * (bk.CEVAP_TAVANI - 10) + anahtar), simdi=SIMDI)
    s = _defter()[-1]
    assert "sk-or-v1-" not in json.dumps(s) and s["cevap"].endswith("***")


def test_hatirla_hafiza_yazamazsa_acik_soyler_ve_olay(sandbox_state):
    cevap = bk.bota_sor("sef", "hatırla: x", "pano", "o", hafiza=SahteHafiza(sonuc=False), simdi=SIMDI)
    assert "YAZILAMADI" in cevap and _defter()[-1]["tur"] == "hatirla"
    assert any(e.get("event") == "bot_hafiza_yazilamadi" for e in obs.recent(20))


def test_gunluk_sayim_yalniz_o_botun_sohbet_satirlarini_sayar(sandbox_state):
    t = SahteTasiyici()
    bk.bota_sor("sef", "a", "pano", "o", tasiyici=t, simdi=SIMDI)
    bk.bota_sor("bekci", "b", "pano", "o", tasiyici=t, simdi=SIMDI)
    bk.bota_sor("sef", "hatırla: c", "pano", "o", tasiyici=t, simdi=SIMDI)
    bk.bota_sor("sef", "d", "pano", "o", tasiyici=t, simdi=SIMDI - dt.timedelta(days=1))
    assert bk.gunluk_sayim("sef", "2026-09-29") == 1 and bk.gunluk_sayim("bekci", "2026-09-29") == 1


def test_saat_dilimsiz_simdi_reddedilir(sandbox_state):
    # Kota günü UTC'dir; saat dilimsiz bir an yerel saat sanılıp günü sessizce kaydırırdı.
    with pytest.raises(ValueError):
        bk.bota_sor("sef", "x", "pano", "o", tasiyici=SahteTasiyici(), simdi=dt.datetime(2026, 9, 29, 12))


class _Cevap(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.close()


def test_hermes_varsayilan_cagri_zaman_asimli_post(monkeypatch):
    # Review Focus 1: taşıyıcı asılırsa Telegram döngüsü de asılır — zaman aşımı urlopen'a GİDER.
    gorulen = {}

    def urlopen(istek, timeout=None):
        gorulen.update(istek=istek, timeout=timeout)
        return _Cevap(json.dumps({"choices": [{"message": {"content": "tamam"}}]}).encode())

    monkeypatch.setattr(bk.urllib.request, "urlopen", urlopen)
    sonuc = bk.HermesTasiyici(_anahtar=lambda: "K" * 32, zaman_asimi_s=9).sor("bekci", "soru", "tg-bekci-7")
    istek = gorulen["istek"]
    assert sonuc.metin == "tamam" and gorulen["timeout"] == 9 and istek.get_method() == "POST"
    assert istek.full_url == "http://127.0.0.1:8642/p/bekci/v1/chat/completions"
    assert istek.get_header("Authorization") == "Bearer " + "K" * 32
    assert istek.get_header("X-hermes-session-id") == "tg-bekci-7"
    assert json.loads(istek.data) == {"model": "hermes-agent", "messages": [{"role": "user", "content": "soru"}]}


def test_hermes_http_hatasi_yalniz_kod_tasir_anahtar_sizmaz(monkeypatch):
    anahtar = "GIZLIANAHTAR" + "Z" * 20

    def urlopen(istek, timeout=None):
        raise urllib.error.HTTPError(f"http://127.0.0.1:8642/p/bekci?key={anahtar}", 401,
                                     f"Unauthorized {anahtar}", {}, None)

    monkeypatch.setattr(bk.urllib.request, "urlopen", urlopen)
    with pytest.raises(RuntimeError) as e:
        bk.HermesTasiyici(_anahtar=lambda: anahtar).sor("bekci", "x", "o")
    assert "401" in str(e.value) and anahtar not in str(e.value)
    # zincir de taşımaz: HTTPError bağlamı bastırılır (traceback'e düşmesin)
    assert e.value.__cause__ is None and e.value.__suppress_context__ is True


def test_hermes_anahtarsiz_istek_atilmaz():
    def cagir(*a):
        raise AssertionError("anahtarsız istek atıldı")

    with pytest.raises(RuntimeError) as e:
        bk.HermesTasiyici(_cagir=cagir, _anahtar=lambda: None).sor("karne", "x", "o")
    assert "API_SERVER_KEY" in str(e.value)


# ---- Tur 2 (inceleme I-1 + yeniden derecelenen M-2) -------------------------------------------------

#: komut_oneki'nin DONUK hüküm tablosu — Telegram katmanı ile bota_sor aynı tespiti kullanır (tek kaynak).
KOMUT_TABLOSU = [
    ("hatırla: not", ("hatirla", "not")),
    ("HATIRLA : not", ("hatirla", "not")),
    ("hatirla: not", ("hatirla", "not")),
    ("Hatırla:çok satırlı\nnot", ("hatirla", "çok satırlı\nnot")),
    ("unut: not", ("unut", "not")),
    ("Unut : not", ("unut", "not")),
    ("hatırla:", ("hatirla", "")),
    ("hatırlatma: not", None),
    ("unutma: not", None),
    ("unutma", None),
    ("hatırla bunu", None),
    ("<<<VERI:yanitlanan_mesaj>>>\nx\n<<<VERI-SON:yanitlanan_mesaj>>>\nhatırla: not", None),
]


@pytest.mark.parametrize("metin,beklenen", KOMUT_TABLOSU)
def test_komut_oneki_tablosu_ve_bota_sor_dagitimi_AYNI_hukmu_verir(sandbox_state, metin, beklenen):
    # AYRIŞMA ÇİVİSİ: tespit fonksiyonu ile bota_sor'un dağıtımı iki ayrı regex'e bölünürse bir girdi
    # bir yerde komut, öbüründe soru sayılır (I-1 sınıfı). Hüküm DAVRANIŞTAN ölçülür: taşıyıcı çağrıldı
    # mı, çağrılmadıysa defter satırının `tur`u ne.
    assert bk.komut_oneki(metin) == beklenen
    t = SahteTasiyici()
    bk.bota_sor("sef", metin, "pano", "o", tasiyici=t, hafiza=SahteHafiza(), simdi=SIMDI)
    dagitim = "model" if t.cagrilar else _defter()[-1]["tur"]
    assert dagitim == (beklenen[0] if beklenen else "model")


def test_bota_sor_komut_tespitini_YALNIZ_komut_oneki_ile_yapar():
    # Tek kaynak YAPISAL: davranışı birebir aynı özel bir kopya bugün tabloyu geçer ama yarın ayrışır.
    # `_komut` komut_oneki'yi çağırır ve kendi regex/`re` çağrısı taşımaz; `_KOMUT` yalnız komut_oneki'de.
    import ast
    import inspect
    agac = ast.parse(inspect.getsource(bk))
    fonk = {n.name: n for n in agac.body if isinstance(n, ast.FunctionDef)}
    cagrilar = {c.func.id for c in ast.walk(fonk["_komut"]) if isinstance(c, ast.Call)
                and isinstance(c.func, ast.Name)}
    assert "komut_oneki" in cagrilar
    assert not any(isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name) and n.value.id == "re"
                   for n in ast.walk(fonk["_komut"]))
    kullananlar = {f for f, n in fonk.items() for d in ast.walk(n)
                   if isinstance(d, ast.Name) and d.id == "_KOMUT"}
    assert kullananlar == {"komut_oneki"}


@pytest.mark.parametrize("ad", ["../x", "a/b", "bekci/../karne", "Bekci", "", "bekci?k=1"])
def test_hermes_bot_adi_http_oncesi_reddedilir(ad):
    cagrilar = []

    def cagir(*a):
        cagrilar.append(a)
        return {"choices": [{"message": {"content": "x"}}]}

    with pytest.raises(ValueError):
        bk.HermesTasiyici(_cagir=cagir, _anahtar=lambda: "K" * 32).sor(ad, "x", "o")
    assert cagrilar == []


@pytest.mark.parametrize("govde", [
    {}, {"choices": []}, {"choices": [{"message": {}}]}, {"choices": [{"message": {"content": None}}]},
    {"choices": "gizli-govde-XYZ"},
])
def test_hermes_beklenmeyen_cevap_bicimi_sinif_adli_hata_ve_defter_hata(sandbox_state, govde):
    t = bk.HermesTasiyici(_cagir=lambda *a: govde, _anahtar=lambda: "K" * 32)
    with pytest.raises(RuntimeError) as e:
        bk.bota_sor("bekci", "x", "telegram", "o", tasiyici=t, simdi=SIMDI)
    assert str(e.value).startswith("api_server cevab") and "gizli" not in str(e.value)
    s = _defter()[-1]
    assert s["tur"] == "hata" and s["hata"] == "RuntimeError"


def test_hatirla_hafiza_istisnasi_yazilamadi_der_ve_olay_yazar(sandbox_state):
    class Patlayan:
        def yaz(self, bot, metin, etiketler):
            raise ConnectionError("hindsight kapalı")

    cevap = bk.bota_sor("sef", "hatırla: x", "pano", "o", hafiza=Patlayan(), simdi=SIMDI)
    assert "YAZILAMADI" in cevap and _defter()[-1]["hafiza_durumu"] == "yazilamadi"
    assert any(e.get("event") == "bot_hafiza_yazim_hatasi" and e.get("sinif") == "ConnectionError"
               for e in obs.recent(20))
