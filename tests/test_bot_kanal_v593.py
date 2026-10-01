"""v593 — konuşan filo kanal çekirdeği bota_sor (spec 2026-09-29 §3.4-§3.7): doğrulama, kota, hatırla/unut, defter, taşıyıcı."""
import datetime as dt
import io
import json
import urllib.error

import pytest

from meridian import bot_hafiza as bh, bot_kanal as bk, kadro, obs, store

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
    # G4 Görev 2: tek adımlı `unut` EMEKLİ — iki adım (`unut_adaylari` salt-okur, `unut_uygula`) + `geri_al`.
    def __init__(self, sonuc=True, adaylar=(), donus_sonuc=True, donus_kimlik="op-1", uygula_hatasi=None,
                 geri_al_hatasi_sirasi=None):
        self.yazilanlar, self.sonuc = [], sonuc
        self.aday_sorgulari, self.adaylar = [], list(adaylar)
        self.uygulananlar, self.uygula_hatasi = [], uygula_hatasi
        self.geri_al_denemeleri, self.geri_al_hatasi_sirasi = [], geri_al_hatasi_sirasi
        self.donusler, self.donus_sonuc, self.donus_kimlik = [], donus_sonuc, donus_kimlik

    def yaz(self, bot, metin, etiketler):
        self.yazilanlar.append((bot, metin, etiketler))
        return self.sonuc

    def unut_adaylari(self, bot, ifade):
        self.aday_sorgulari.append((bot, ifade))
        return list(self.adaylar)

    def unut_uygula(self, bot, idler, ifade):
        self.uygulananlar.append((bot, list(idler), ifade))
        if self.uygula_hatasi is not None:
            raise self.uygula_hatasi
        return list(idler)

    def geri_al(self, bot, memory_id):
        self.geri_al_denemeleri.append((bot, memory_id))
        if len(self.geri_al_denemeleri) - 1 == self.geri_al_hatasi_sirasi:
            raise _nedenli("http_502")
        return True

    def donus_yaz(self, bot, mesaj, cevap, etiketler):
        self.donusler.append((bot, mesaj, cevap, etiketler))
        return bh.DonusSonucu(self.donus_sonuc, self.donus_kimlik)


def _defter():
    return store.read_jsonl(bk.DEFTER)


#: Görev 1'den (Parça 1b-ön) beri `HermesTasiyici` sohbet POST'undan SONRA oturum dökümünü GET eder. Yalnız
#: sohbet isteğini ölçen çiviler GET'e bu araçsız, verisiz turu döner (ölçüm dışı; sayım çivileri aşağıda).
_ARACSIZ_TUR = {"data": [{"role": "user", "content": "soru"}, {"role": "assistant", "content": "tamam"}]}


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


def test_hatirla_hafiza_verilmezse_gercek_sinif_anahtarsiz_yazilamadi_ve_olay(sandbox_state):
    # Parça 1b G4 Görev 1 (Rol-1 kararı 2026-09-30): `hafiza` verilmeyen çağrı ÜRETİM varsayılanına
    # (`bot_hafiza.HindsightHafiza`) gider. `sandbox_state` credential kanalını kapatır → anahtar yok →
    # HTTP'den ÖNCE hata; sessiz kalınmaz: "YAZILAMADI" + sınıf ve kapalı-küme nedenli olay.
    cevap = bk.bota_sor("sef", "hatırla: x", "pano", "o", tasiyici=SahteTasiyici(), simdi=SIMDI)
    assert "YAZILAMADI" in cevap and _defter()[-1]["hafiza_durumu"] == "yazilamadi"
    assert any(e.get("event") == "bot_hafiza_yazim_hatasi" and e.get("sinif") == "RuntimeError"
               and e.get("neden") == "anahtar_yok" for e in obs.recent(20))


def test_unut_hafiza_verilmezse_gercek_sinif_anahtarsiz_aranamadi(sandbox_state):
    # Eski "bağlı değil" dalı emekli (G4 Görev 1): hafıza VERİLMEDİYSE gerçek sınıf; anahtar yoksa aday listesi
    # ARANAMADI (G4 Görev 2: ilk adım salt-okur — "hiçbir şey unutulmadı" burada DOĞRUDUR).
    t = SahteTasiyici()
    cevap = bk.bota_sor("bekci", "unut: eski not", "telegram", "o", tasiyici=t, simdi=SIMDI)
    assert t.cagrilar == [] and "ARANAMADI" in cevap and "hiçbir şey unutulmadı" in cevap
    s = _defter()[-1]
    assert (s["tur"], s["hafiza_durumu"]) == ("unut", "aranamadi")


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


def test_hermes_tasiyici_istek_bicimi_ve_jetonsuz_hata(sandbox_state):
    # Görev 1 (uygulayıcı, 2026-09-30): `HermesTasiyici.sor` artık sayım düşerse `obs.warn` yazar. Taşıyıcıyı
    # koşan her çivi `sandbox_state` alır — gerileme anında olay CANLI yerel `events.jsonl`e düşmesin (ölçüldü:
    # mutasyon koşumlarında fikstürsüz çiviler bekçiye takıldı ve satırlar ağacın state/'inde kaldı).
    gorulen = {}

    def cagir(url, govde, basliklar, zaman_asimi):
        if not url.endswith("/chat/completions"):
            return _ARACSIZ_TUR
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
    assert any(e.get("event") == "bot_hafiza_unut_hatasi" and e.get("bot") == "bekci" for e in obs.recent(20))


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


def test_hermes_varsayilan_cagri_zaman_asimli_post(sandbox_state, monkeypatch):
    # Review Focus 1: taşıyıcı asılırsa Telegram döngüsü de asılır — zaman aşımı urlopen'a GİDER.
    gorulen = {}

    def urlopen(istek, timeout=None):
        if istek.get_method() == "GET":
            return _Cevap(json.dumps(_ARACSIZ_TUR).encode())
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
    # G4 Görev 2 (Rol-1 kararı 3): `onayla` ve İKİ KELİMELİ `geri al` (`kadro.ad_katla` + `_` ile `geri_al`).
    ("onayla: unut a1b2c3", ("onayla", "unut a1b2c3")),
    ("Onayla : Unut A1B2C3", ("onayla", "Unut A1B2C3")),
    ("onayla:", ("onayla", "")),
    ("geri al: a1b2c3", ("geri_al", "a1b2c3")),
    ("Geri Al : a1b2c3", ("geri_al", "a1b2c3")),
    ("GERİ AL: a1b2c3", ("geri_al", "a1b2c3")),
    ("geri  al:\ta1b2c3", ("geri_al", "a1b2c3")),
    ("geri al:", ("geri_al", "")),
    ("geri\nal: a1b2c3", None),                # kelimeler arası satır sonu komut değil
    ("geri al a1b2c3", None),
    ("geri alma: a1b2c3", None),
    ("geri: a1b2c3", None),
    ("al: a1b2c3", None),
    ("onaylama: unut a1b2c3", None),
    ("geri al bunu: a1b2c3", None),             # en çok İKİ kelime
    ("hatırla bunu: not", None),                # iki kelime ama tabloda değil
    ("unut şunu: not", None),
]

#: Komut adı → defter `tur`u. `onayla` satırı Rol-1 kararı 4 (2026-09-30) ile `unut_onay` adını taşır (onayladığı iş
#: unutmadır); diğerlerinde tur = komut adı.
_KOMUT_TURU = {"onayla": "unut_onay"}


@pytest.mark.parametrize("metin,beklenen", KOMUT_TABLOSU)
def test_komut_oneki_tablosu_ve_bota_sor_dagitimi_AYNI_hukmu_verir(sandbox_state, metin, beklenen):
    # AYRIŞMA ÇİVİSİ: tespit fonksiyonu ile bota_sor'un dağıtımı iki ayrı regex'e bölünürse bir girdi
    # bir yerde komut, öbüründe soru sayılır (I-1 sınıfı). Hüküm DAVRANIŞTAN ölçülür: taşıyıcı çağrıldı
    # mı, çağrılmadıysa defter satırının `tur`u ne.
    assert bk.komut_oneki(metin) == beklenen
    t = SahteTasiyici()
    bk.bota_sor("sef", metin, "pano", "o", tasiyici=t, hafiza=SahteHafiza(), simdi=SIMDI)
    dagitim = "model" if t.cagrilar else _defter()[-1]["tur"]
    assert dagitim == (_KOMUT_TURU.get(beklenen[0], beklenen[0]) if beklenen else "model")


def test_komutlar_tablosu_donuk():
    assert bk.KOMUTLAR == ("hatirla", "unut", "onayla", "geri_al")


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


# ---- Tur 3 (son inceleme I-1): taşıyıcı zaman aşımı ZORUNLU ve ÜRETİM yolu çivili ------------------------
# `urlopen(timeout=None)` soketi SONSUZ bloklar → tek asılı api_server çağrısı Telegram döngüsünü süresiz
# kilitler (plan Review Focus 1). Varsayılan bir değer tek başına güvence değildir: `None`a çeviren tek
# satır bütün açık-değerli çivileri yeşil bırakırdı. İki çivi: (1) kurucu geçersiz değeri REDDEDER;
# (2) üretimin TEK yolu (`bota_sor`, taşıyıcı VERİLMEDEN → `HermesTasiyici()` → varsayılan HTTP yolu)
# urlopen'a sonlu, sabitlenmiş (300 sn) zaman aşımı geçirir. `_cagir` ENJEKTE EDİLMEZ — ölçülen o yol.

@pytest.mark.parametrize("deger", [None, 0, 0.0, -1, -0.5, float("inf"), float("-inf"), float("nan"), "300", True])
def test_hermes_zaman_asimi_sonlu_ve_pozitif_olmali(deger):
    with pytest.raises(ValueError):
        bk.HermesTasiyici(zaman_asimi_s=deger)


def test_uretim_yolu_varsayilan_tasiyici_sonlu_sabit_zaman_asimi_gecirir(sandbox_state, monkeypatch):
    import inspect
    import math
    gorulen = {}
    monkeypatch.setattr(bk.secrets, "credential_oku", lambda ad: "K" * 32 if ad == "API_SERVER_KEY" else None)

    def urlopen(istek, timeout=None):
        if istek.get_method() == "GET":
            return _Cevap(json.dumps(_ARACSIZ_TUR).encode())
        gorulen.update(timeout=timeout, url=istek.full_url)
        return _Cevap(json.dumps({"choices": [{"message": {"content": "tamam"}}]}).encode())

    monkeypatch.setattr(bk.urllib.request, "urlopen", urlopen)
    assert bk.bota_sor("bekci", "x", "pano", "o", simdi=SIMDI) == "tamam"
    z = gorulen["timeout"]
    assert isinstance(z, (int, float)) and not isinstance(z, bool) and math.isfinite(z) and z > 0
    # G4 Görev 1: varsayılan ADLI sabitten okunur (çapraz bütçe çivisi aşağıda aynı sabiti okur); değer 300 DONUK.
    assert z == 300 == bk.HERMES_ZAMAN_ASIMI_S == inspect.signature(bk.HermesTasiyici).parameters["zaman_asimi_s"].default
    assert gorulen["url"] == "http://127.0.0.1:8642/p/bekci/v1/chat/completions"


# ---- Parça 1b-ön Görev 1: araçsız-veri uyarısı (Parça 0 EN AĞIR BULGU) -----------------------------------
# Araç katmanı bağlı olmayan bot bir araç çağrısı ve SONUCU uydurup operatöre gerçek veri gibi sundu
# (oturumda `tool_calls` yoktu). Savunma modele güvenmez: taşıyıcı GERÇEK araç sayısını ölçer, sayı 0 iken
# veri taşıyan cevap uyarı öneki alır; sayı ölçülemezse AYRI uyarı (uydurma yasağı: None ≠ 0).

@pytest.mark.parametrize("cevap,beklenen", [
    ("Rejim neutral, bütçe %100", True), ("kaynak: risk/state.json", True), ("Bugün 3 kalem var", True),
    ("Merhaba, nasıl yardımcı olabilirim?", False), ("", False)])
def test_veri_iceriyor(cevap, beklenen):
    assert bk.veri_iceriyor(cevap) is beklenen


class SayacliTasiyici(SahteTasiyici):
    def __init__(self, metin, arac):
        super().__init__(metin); self.arac = arac
    def sor(self, bot, mesaj, oturum):
        self.cagrilar.append((bot, mesaj, oturum))
        return bk.TasiyiciSonuc(self.metin, arac_cagrilari=self.arac, model_cagrilari=1)


def test_aracsiz_veri_uyarisi_ve_defter(sandbox_state):
    c = bk.bota_sor("bekci", "rejim?", "telegram", "o", tasiyici=SayacliTasiyici("Rejim neutral, bütçe %100", 0), simdi=SIMDI)
    assert c.startswith(bk.UYARI_ARACSIZ) and "Rejim neutral" in c
    s = _defter()[-1]
    assert s["arac_siz_veri"] is True and s["cevap"].startswith(bk.UYARI_ARACSIZ)


def test_aracli_veri_uyarisiz(sandbox_state):
    c = bk.bota_sor("bekci", "rejim?", "telegram", "o", tasiyici=SayacliTasiyici("Rejim neutral", 2), simdi=SIMDI)
    assert not c.startswith("⚠️") and _defter()[-1]["arac_siz_veri"] is False


def test_verisiz_aracsiz_cevap_uyarisiz(sandbox_state):
    c = bk.bota_sor("sef", "selam", "pano", "o", tasiyici=SayacliTasiyici("Merhaba!", 0), simdi=SIMDI)
    assert c == "Merhaba!"


def test_arac_sayisi_olculemediyse_ayri_uyari(sandbox_state):
    c = bk.bota_sor("karne", "getiri?", "pano", "o", tasiyici=SayacliTasiyici("Getiri %2", None), simdi=SIMDI)
    assert c.startswith(bk.UYARI_OLCULEMEDI) and _defter()[-1]["arac_olculemedi"] is True


def test_uyari_cift_eklenmez(sandbox_state):
    c = bk.bota_sor("bekci", "x", "pano", "o", tasiyici=SayacliTasiyici(bk.UYARI_ARACSIZ + "\n3 kalem", 0), simdi=SIMDI)
    assert c.count(bk.UYARI_ARACSIZ) == 1


def test_hermes_tasiyici_bu_turun_arac_cagrilarini_sayar(sandbox_state):
    oturum_mesajlari = {"data": [
        {"role": "user", "content": "eski"}, {"role": "assistant", "tool_calls": [{"function": {"name": "a"}}]},
        {"role": "tool", "content": "x"}, {"role": "assistant", "content": "eski cevap"},
        {"role": "user", "content": "yeni"}, {"role": "assistant", "content": "yeni cevap"}]}
    def cagir(url, govde, basliklar, zaman_asimi):
        if url.endswith("/chat/completions"):
            return {"choices": [{"message": {"content": "yeni cevap"}}]}
        assert url.endswith("/p/bekci/api/sessions/o-1/messages") and govde is None
        return oturum_mesajlari
    s = bk.HermesTasiyici(_cagir=cagir, _anahtar=lambda: "K" * 32).sor("bekci", "yeni", "o-1")
    assert s.arac_cagrilari == 0


def test_hermes_tasiyici_oturum_okunamazsa_none(sandbox_state):
    # RULING (uygulayıcı, 2026-09-30, ölçüldü): brief çivisi `sandbox_state` almıyordu; brief Step 3'ün
    # istediği `obs.warn` olayı canlı `state/events.jsonl`e düşüyor ve conftest canlı-yazım bekçisi testi
    # düşürüyordu. Fikstür eklendi — iddia brief'teki gibi.
    def cagir(url, govde, basliklar, zaman_asimi):
        if url.endswith("/chat/completions"):
            return {"choices": [{"message": {"content": "c"}}]}
        raise OSError("okunamadı")
    assert bk.HermesTasiyici(_cagir=cagir, _anahtar=lambda: "K" * 32).sor("bekci", "m", "o").arac_cagrilari is None


# ---- Görev 1 brief dışı ek çiviler (uygulayıcı) -----------------------------------------------------------

def test_uyari_metinleri_donuk():
    # Plan "Global Constraints": iki metin DONUK — ölçüm kartı ve operatör bu metinleri tanır.
    assert bk.UYARI_ARACSIZ == "⚠️ Bu cevap hiçbir araç çağrısına dayanmıyor — içindeki veri doğrulanmadı."
    assert bk.UYARI_OLCULEMEDI == "⚠️ Bu cevabın araç kullanımı doğrulanamadı."


def test_hermes_tasiyici_bu_turdaki_arac_cagrilarini_gercekten_sayar(sandbox_state):
    # POZİTİF KONTROL: her zaman 0 dönen bir sayım brief çivilerini yeşil bırakırdı. Önceki turun 1 aracı
    # SAYILMAZ; bu turun iki asistan mesajındaki 2 + 1 araç sayılır; `tool_calls: None` 0 sayılır → 3.
    d = {"data": [
        {"role": "user", "content": "eski"}, {"role": "assistant", "tool_calls": [{"function": {"name": "a"}}]},
        {"role": "tool", "content": "x"}, {"role": "assistant", "content": "eski cevap"},
        {"role": "user", "content": "yeni"},
        {"role": "assistant", "tool_calls": [{"function": {"name": "b"}}, {"function": {"name": "c"}}]},
        {"role": "tool", "content": "y"}, {"role": "tool", "content": "z"},
        {"role": "assistant", "tool_calls": [{"function": {"name": "d"}}]}, {"role": "tool", "content": "w"},
        {"role": "assistant", "content": "yeni cevap", "tool_calls": None}]}

    def cagir(url, govde, basliklar, zaman_asimi):
        if url.endswith("/chat/completions"):
            return {"choices": [{"message": {"content": "yeni cevap"}}]}
        return d
    assert bk.HermesTasiyici(_cagir=cagir, _anahtar=lambda: "K" * 32).sor("bekci", "yeni", "o-1").arac_cagrilari == 3


@pytest.mark.parametrize("govde", [
    {}, [], {"data": "x"}, {"data": None}, {"data": []},
    {"data": [{"role": "assistant", "content": "c"}]},                      # hizalı ama kullanıcı mesajı yok → tur bulunamaz
    {"data": [{"role": "user"}, "bozuk"]},
    # Tur 2: `tool_calls` biçim parametreleri düştü — sayım artık `tool_calls`a değil `role: tool` sonuçlarına bakar (I-2)
])
def test_hermes_oturum_bicimi_beklenmedikse_arac_sayisi_none_ve_olay(sandbox_state, govde):
    # Biçimi tanınmayan oturum dökümü 0 SAYILMAZ (uydurma yasağı) — None + sınıf adlı olay.
    def cagir(url, govde_, basliklar, zaman_asimi):
        if url.endswith("/chat/completions"):
            return {"choices": [{"message": {"content": "c"}}]}
        return govde
    s = bk.HermesTasiyici(_cagir=cagir, _anahtar=lambda: "K" * 32).sor("bekci", "m", "o")
    assert s.metin == "c" and s.arac_cagrilari is None
    assert any(e.get("event") == "bot_arac_sayimi_olculemedi" and e.get("bot") == "bekci" and e.get("sinif")
               and e.get("neden") == "bicim" for e in obs.recent(20))


@pytest.mark.parametrize("oturum", ["../x", "a/b", "..", "o?k=1", "o#f", "o o", ""])
def test_hermes_oturum_kimligi_url_yoluna_uygun_degilse_get_atilmaz_none(sandbox_state, oturum):
    # Oturum kimliği artık URL YOLUNA girer (bot adıyla aynı sınıf, Tur 2): yol dışına taşan kimlik
    # başka bir uca istek attırırdı. İstek atılmaz, sayım ölçülemedi (None) — sohbet cevabı düşmez.
    urller = []

    def cagir(url, govde, basliklar, zaman_asimi):
        urller.append(url)
        return {"choices": [{"message": {"content": "c"}}]}
    s = bk.HermesTasiyici(_cagir=cagir, _anahtar=lambda: "K" * 32).sor("bekci", "m", oturum)
    assert s.metin == "c" and s.arac_cagrilari is None
    assert [u for u in urller if not u.endswith("/chat/completions")] == []
    assert _olcum_nedeni() == "oturum_kimligi"


def test_hermes_oturum_okunamazsa_olay_sinif_adiyla_yazilir(sandbox_state):
    def cagir(url, govde, basliklar, zaman_asimi):
        if url.endswith("/chat/completions"):
            return {"choices": [{"message": {"content": "c"}}]}
        raise OSError("okunamadı")
    assert bk.HermesTasiyici(_cagir=cagir, _anahtar=lambda: "K" * 32).sor("bekci", "m", "o").arac_cagrilari is None
    assert any(e.get("event") == "bot_arac_sayimi_olculemedi" and e.get("bot") == "bekci"
               and e.get("sinif") == "OSError" and e.get("neden") == "ag" for e in obs.recent(20))


def test_hermes_varsayilan_cagri_oturum_mesajlarini_zaman_asimli_get_ile_okur(sandbox_state, monkeypatch):
    # Varsayılan HTTP yolu: sohbet POST'undan SONRA oturum dökümü GET ile, AYNI zaman aşımıyla, anahtar
    # yalnız `Authorization` başlığında, gövdesiz.
    istekler = []

    def urlopen(istek, timeout=None):
        istekler.append((istek, timeout))
        if istek.get_method() == "POST":
            return _Cevap(json.dumps({"choices": [{"message": {"content": "tamam"}}]}).encode())
        return _Cevap(json.dumps({"data": [
            {"role": "user", "content": "soru"},
            {"role": "assistant", "tool_calls": [{"function": {"name": "meridian_rejim"}}]},
            {"role": "tool", "content": "{}"}, {"role": "assistant", "content": "tamam"}]}).encode())

    monkeypatch.setattr(bk.urllib.request, "urlopen", urlopen)
    s = bk.HermesTasiyici(_anahtar=lambda: "K" * 32, zaman_asimi_s=9).sor("bekci", "soru", "tg-bekci-7")
    assert s.metin == "tamam" and s.arac_cagrilari == 1
    assert [i.get_method() for i, _ in istekler] == ["POST", "GET"]
    get, z = istekler[1]
    assert get.full_url == "http://127.0.0.1:8642/p/bekci/api/sessions/tg-bekci-7/messages"
    assert get.data is None and z == 9 and get.get_header("Authorization") == "Bearer " + "K" * 32


def test_hermes_oturum_okuma_http_hatasi_yalniz_kod_tasir_anahtar_sizmaz(sandbox_state, monkeypatch):
    anahtar = "GIZLIANAHTAR" + "Y" * 20

    def urlopen(istek, timeout=None):
        if istek.get_method() == "POST":
            return _Cevap(json.dumps({"choices": [{"message": {"content": "tamam"}}]}).encode())
        raise urllib.error.HTTPError(f"{istek.full_url}?key={anahtar}", 404, f"Not Found {anahtar}", {}, None)

    monkeypatch.setattr(bk.urllib.request, "urlopen", urlopen)
    assert bk.HermesTasiyici(_anahtar=lambda: anahtar).sor("bekci", "x", "o").arac_cagrilari is None
    olaylar = [e for e in obs.recent(20) if e.get("event") == "bot_arac_sayimi_olculemedi"]
    assert olaylar and olaylar[-1]["sinif"] == "RuntimeError" and anahtar not in json.dumps(obs.recent(50))
    assert olaylar[-1]["neden"] == "http_404"
    assert set(olaylar[-1]) == {"ts", "level", "event", "bot", "sinif", "neden"}
    # GET dalında da hata çevirisi: yalnız KOD, URL/mesaj/anahtar yok, zincir bastırılmış.
    with pytest.raises(RuntimeError) as e:
        bk.HermesTasiyici._cagir_varsayilan("http://127.0.0.1:8642/p/bekci/api/sessions/o/messages", None,
                                            {"Authorization": f"Bearer {anahtar}"}, 5)
    assert str(e.value) == "api_server HTTP 404"
    assert e.value.__cause__ is None and e.value.__suppress_context__ is True


def test_olculemeyen_arac_sayisi_arac_siz_veri_alanini_uydurmaz(sandbox_state):
    # Sayı ölçülemediyse "araçsız veri mi" sorusunun cevabı da BİLİNMİYOR: False yazmak "temiz" demek olurdu.
    bk.bota_sor("karne", "getiri?", "pano", "o", tasiyici=SayacliTasiyici("Getiri %2", None), simdi=SIMDI)
    s = _defter()[-1]
    assert s["arac_siz_veri"] is None and s["arac_olculemedi"] is True and s["arac_cagrilari"] is None
    assert s["cevap"] == bk.UYARI_OLCULEMEDI + "\nGetiri %2"


def test_olculemeyen_arac_sayisinda_verisiz_cevap_da_uyari_alir(sandbox_state):
    # Brief: `n is None` → önek KOŞULSUZ (veri içeriğine bakılmaz).
    c = bk.bota_sor("sef", "selam", "pano", "o", tasiyici=SayacliTasiyici("Merhaba!", None), simdi=SIMDI)
    assert c == bk.UYARI_OLCULEMEDI + "\nMerhaba!"


def test_aracsiz_veri_onek_bicimi_ve_olculmus_alanlar(sandbox_state):
    c = bk.bota_sor("bekci", "kaç?", "pano", "o", tasiyici=SayacliTasiyici("3 kalem", 0), simdi=SIMDI)
    assert c == bk.UYARI_ARACSIZ + "\n3 kalem"
    s = _defter()[-1]
    assert s["arac_siz_veri"] is True and s["arac_olculemedi"] is False and s["cevap"] == c
    bk.bota_sor("sef", "selam", "pano", "o", tasiyici=SayacliTasiyici("Merhaba!", 0), simdi=SIMDI)
    s = _defter()[-1]
    assert s["arac_siz_veri"] is False and s["arac_olculemedi"] is False and s["cevap"] == "Merhaba!"


def test_hermes_uretilen_telegram_oturum_kimlikleri_desene_uyar_get_atilir(sandbox_state):
    # memory `kimlik-uzayi-olculmeden-duvar-yok`: ret deseni meşru kimlik uzayını kırmamalı. Uzayın bugünkü TEK
    # üreticisi `telegram_dinleyici.oturum_kimligi` (pano/claude kanal kimlikleri henüz yok) — kimlikler oradan
    # TÜRETİLİR, elle yazılmaz; üretici biçim değiştirirse bu çivi öter.
    from meridian import telegram_dinleyici as td
    kimlikler = [td.oturum_kimligi("bekci", {}, "20260929"),
                 td.oturum_kimligi("karne", {"reply_to_message": {"message_id": 4711, "text": "x"}}, "20260929"),
                 td.oturum_kimligi("sef", {"reply_to_message": {"message_id": 5, "text": "💬 @sef · tg-sef-r3"}},
                                   "20260929")]
    assert kimlikler == ["tg-bekci-20260929", "tg-karne-r4711", "tg-sef-r3"]
    for oturum in kimlikler:
        urller = []

        def cagir(url, govde, basliklar, zaman_asimi):
            urller.append(url)
            if url.endswith("/chat/completions"):
                return {"choices": [{"message": {"content": "tamam"}}]}
            return _ARACSIZ_TUR
        s = bk.HermesTasiyici(_cagir=cagir, _anahtar=lambda: "K" * 32).sor("bekci", "m", oturum)
        assert s.arac_cagrilari == 0 and urller[-1].endswith(f"/api/sessions/{oturum}/messages")


# ---- Tur 2 (inceleme I-1, I-2, I-3, M-2 — Rol-1 kararları 2026-09-30) -------------------------------------

def _tasiyici_dokumle(dokum, cevap):
    """Sohbet çağrısı `cevap` döner, oturum dökümü GET'i `dokum`."""
    def cagir(url, govde, basliklar, zaman_asimi):
        if url.endswith("/chat/completions"):
            return {"choices": [{"message": {"content": cevap}}]}
        return dokum
    return bk.HermesTasiyici(_cagir=cagir, _anahtar=lambda: "K" * 32)


def _olcum_nedeni():
    olay = [e for e in obs.recent(20) if e.get("event") == "bot_arac_sayimi_olculemedi"]
    return olay[-1].get("neden") if olay else None


#: Önceki tur ARAÇLI: hizasız bir sayım bu turun araçsız cevabını bu 1 sonuçla susturur (sessiz, tehlikeli yön).
_ESKI_TUR_ARACLI = [
    {"role": "user", "content": "eski"},
    {"role": "assistant", "tool_calls": [{"id": "1", "function": {"name": "meridian_rejim"}}]},
    {"role": "tool", "content": "{\"rejim\": \"neutral\"}"}, {"role": "assistant", "content": "eski cevap"}]


@pytest.mark.parametrize("dokum", [
    {"data": _ESKI_TUR_ARACLI},                                                        # bayat: bu tur yazılmamış
    {"data": _ESKI_TUR_ARACLI + [{"role": "user", "content": "yeni"}]},               # cevap henüz yazılmamış
    {"data": _ESKI_TUR_ARACLI + [{"role": "user", "content": "yeni"},
                                 {"role": "tool", "content": "yeni cevap"}]},         # son mesaj asistan değil
    {"data": _ESKI_TUR_ARACLI + [{"role": "user", "content": "yeni"},
                                 {"role": "assistant", "content": None}]},            # içerik yok
    {"data": _ESKI_TUR_ARACLI + [{"role": "user", "content": "yeni"},
                                 {"role": "assistant", "content": [{"type": "text", "text": "yeni cevap"}]}]},
])
def test_hermes_dokum_bu_tura_hizali_degilse_sayim_none_tur_hizasiz(sandbox_state, dokum):
    # I-1: döküm ancak SON mesajı `assistant` ve içeriği az önce alınan cevaba (strip sonrası) EŞİTSE bu turundur.
    s = _tasiyici_dokumle(dokum, "yeni cevap").sor("bekci", "yeni", "o-1")
    assert s.metin == "yeni cevap" and s.arac_cagrilari is None and _olcum_nedeni() == "tur_hizasiz"


def test_hermes_eski_tur_aracli_bu_tur_aracsiz_yalniz_hizaliysa_sifir(sandbox_state):
    dokum = {"data": _ESKI_TUR_ARACLI + [{"role": "user", "content": "yeni"},
                                         {"role": "assistant", "content": "yeni cevap"}]}
    assert _tasiyici_dokumle(dokum, "yeni cevap").sor("bekci", "yeni", "o-1").arac_cagrilari == 0
    assert _tasiyici_dokumle(dokum, "başka cevap").sor("bekci", "yeni", "o-1").arac_cagrilari is None
    assert _olcum_nedeni() == "tur_hizasiz"


def test_hermes_hiza_bas_son_bosluk_farkini_tolere_eder(sandbox_state):
    dokum = {"data": [{"role": "user", "content": "yeni"}, {"role": "assistant", "tool_calls": [{"id": "1"}]},
                      {"role": "tool", "content": "x"}, {"role": "assistant", "content": "  yeni cevap"}]}
    assert _tasiyici_dokumle(dokum, "yeni cevap\n").sor("bekci", "yeni", "o-1").arac_cagrilari == 1


def test_hermes_sonucsuz_arac_cagrisi_sayilmaz(sandbox_state):
    # I-2: sayılan SONUÇTUR (`role: tool`), deneme (`tool_calls` öğesi) değil — yanıtsız yapılandırılmış çağrı 0.
    dokum = {"data": [{"role": "user", "content": "yeni"},
                      {"role": "assistant", "tool_calls": [{"id": "1", "function": {"name": "meridian_uydurma"}}]},
                      {"role": "assistant", "content": "yeni cevap"}]}
    assert _tasiyici_dokumle(dokum, "yeni cevap").sor("bekci", "yeni", "o-1").arac_cagrilari == 0


def test_hermes_iki_arac_sonucu_iki_sayilir(sandbox_state):
    dokum = {"data": [{"role": "user", "content": "yeni"},
                      {"role": "assistant", "tool_calls": [{"id": "1"}, {"id": "2"}, {"id": "3"}]},
                      {"role": "tool", "content": "a"}, {"role": "tool", "content": "b"},
                      {"role": "assistant", "content": "yeni cevap"}]}
    assert _tasiyici_dokumle(dokum, "yeni cevap").sor("bekci", "yeni", "o-1").arac_cagrilari == 2


def test_hermes_hata_donen_arac_sonucu_da_sayilir_bilinen_sinir(sandbox_state):
    # BİLİNEN SINIR (docstring + kart kill-list): hata dönen araç da bir sonuçtur — sayım içeriğe bakmaz.
    dokum = {"data": [{"role": "user", "content": "yeni"}, {"role": "assistant", "tool_calls": [{"id": "1"}]},
                      {"role": "tool", "content": "{\"error\": \"unknown tool\"}"},
                      {"role": "assistant", "content": "yeni cevap"}]}
    assert _tasiyici_dokumle(dokum, "yeni cevap").sor("bekci", "yeni", "o-1").arac_cagrilari == 1


@pytest.mark.parametrize("hata,neden", [
    (OSError("x"), "ag"), (TimeoutError("x"), "ag"), (urllib.error.URLError("x"), "ag"),
    (json.JSONDecodeError("x", "d", 0), "bicim"), (TypeError("x"), "beklenmeyen"),
])
def test_hermes_olculemedi_nedeni_sinifa_gore(sandbox_state, hata, neden):
    # M-2: neden kapalı bir kümeden; `str(e)`, URL ya da anahtar olaya GİRMEZ.
    def cagir(url, govde, basliklar, zaman_asimi):
        if url.endswith("/chat/completions"):
            return {"choices": [{"message": {"content": "c"}}]}
        raise hata
    assert bk.HermesTasiyici(_cagir=cagir, _anahtar=lambda: "K" * 32).sor("bekci", "m", "o").arac_cagrilari is None
    assert _olcum_nedeni() == neden


#: Rol-1 I-3 kararı (2026-09-30), Tur 3 kararıyla güncel — alan sözlüğü DONUK; katlanmış küçük harfle KELİME
#: BAŞINDA KÖK ÖNEKİ eşleşir. `kar` Tur 3'te DÜŞTÜ (3 harf; karar/karne/kardeş çakışması); `getiri` Tur 4'te
#: DÜŞTÜ ("getirmek" fiili; getiri iddiaları rakam/`%` taşır).
SOZLUK_DONUK = ["rejim", "maruziyet", "pozisyon", "stop", "alarm", "emir", "zarar", "butce",
                "sinyal", "plan", "fiyat", "hisse", "portfoy", "dolum", "tetik"]


def test_veri_sozlugu_rol1_kararina_esit():
    assert list(bk.VERI_SOZLUGU) == SOZLUK_DONUK


@pytest.mark.parametrize("yazim,kelime", [
    ("Rejim", "rejim"), ("maruziyet", "maruziyet"), ("POZİSYON", "pozisyon"), ("stop", "stop"), ("Alarm", "alarm"),
    ("emir", "emir"), ("Zarar", "zarar"), ("Bütçe", "butce"),
    ("sinyal", "sinyal"), ("plan", "plan"), ("Fiyat", "fiyat"), ("hisse", "hisse"), ("Portföy", "portfoy"),
    ("dolum", "dolum"), ("tetik", "tetik"),
])
def test_veri_isareti_sozluk_her_kelime_katlanarak(yazim, kelime):
    assert bk.veri_isareti(f"şu an {yazim} konusu") == f"sozluk:{kelime}"


@pytest.mark.parametrize("cevap,isaret", [
    ("Bugün 3 kalem var", "rakam"),
    ("Tam %yüz", "yuzde"),                                   # yalnız `%` (rakamsız)
    ("KAYNAK belirtilmedi", "kaynak"), ("SOURCE: meridian", "kaynak"), ("bkz. risk/state.JSONL", "kaynak"),
    ("Rejim risk-on, maruziyet yüksek", "sozluk:rejim"),     # inceleme I-3 örneği
    ("AAPL için stop tetiklendi", "sozluk:stop"),            # inceleme I-3 örneği
    ("Bütçe yüzde yüz", "sozluk:butce"),                     # inceleme I-3 örneği
    ("NVDA yükseliyor", "sembol:NVDA"), ("AAPL'in durumu iyi", "sembol:AAPL"),
    ("Merhaba, nasıl yardımcı olabilirim?", None), ("OK, anlaşıldı", None),
    ("Karar senin, karne hazır", None),                      # tam kelime: `kar` karar/karne İÇİNDE sayılmaz
    ("", None),
])
def test_veri_isareti_hangi_isaret(cevap, isaret):
    assert bk.veri_isareti(cevap) == isaret
    assert bk.veri_iceriyor(cevap) is (isaret is not None)


@pytest.mark.parametrize("jeton", ["OK", "UTC", "API", "JSON", "PDF", "AI", "TL", "USD"])
def test_veri_isareti_rol1_sembol_disi_listesi(jeton):
    assert bk.veri_isareti(f"{jeton} tamam") is None


def test_soul_ve_uyari_metinlerindeki_buyuk_harf_jetonlari_sembol_sayilmaz():
    # Rol-1 I-3: kendi SOUL/uyarı metinlerimizde ÖLÇÜLEN büyük harfli jetonlar (vurgu kelimeleri: NE, TEK, YOK…)
    # sembol değildir. SOUL'a yeni bir vurgu kelimesi girerse bu çivi öter ve `SEMBOL_DISI` bilinçli güncellenir;
    # SOUL'a gerçek bir sembol örneği girerse DIŞLANMAZ — bu çivi o gün değiştirilir.
    import pathlib
    kok = pathlib.Path(__file__).resolve().parent.parent / "deploy" / "hermes"
    soullar = sorted(kok.rglob("SOUL*.md"))
    assert soullar
    metinler = [p.read_text() for p in soullar] + [bk.UYARI_ARACSIZ, bk.UYARI_OLCULEMEDI]
    jetonlar = {t for m in metinler for t in bk._SEMBOL_DESENI.findall(m)}
    assert jetonlar
    sembol_sanilan = sorted(t for t in jetonlar if str(bk.veri_isareti(f"{t} tamam")).startswith("sembol:"))
    assert sembol_sanilan == []


def test_defter_veri_isareti_alani(sandbox_state):
    bk.bota_sor("bekci", "rejim?", "pano", "o", tasiyici=SayacliTasiyici("Rejim risk-on, maruziyet yüksek", 0),
                simdi=SIMDI)
    s = _defter()[-1]
    assert s["veri_isareti"] == "sozluk:rejim" and s["arac_siz_veri"] is True
    assert s["cevap"] == bk.UYARI_ARACSIZ + "\nRejim risk-on, maruziyet yüksek"
    bk.bota_sor("sef", "selam", "pano", "o", tasiyici=SayacliTasiyici("Merhaba!", 0), simdi=SIMDI)
    assert _defter()[-1]["veri_isareti"] is None
    bk.bota_sor("karne", "x", "pano", "o", tasiyici=SayacliTasiyici("AAPL güçlü", None), simdi=SIMDI)
    s = _defter()[-1]
    assert s["veri_isareti"] == "sembol:AAPL" and s["arac_siz_veri"] is None


# ---- Tur 3 (Rol-1 kararı 2026-09-30: sözlük KÖK ÖNEKİ; `kar` düştü; ölçülmüş çakışma dışlaması) ------------
# Ölçüm (Tur 2, bağımsız eşlem): tam-kelime kuralı 10 çekimli alan cümlesinin 1'ini yakaladı — Türkçe eklemeli.

@pytest.mark.parametrize("cevap,isaret", [
    ("Fiyatı yükseldi.", "sozluk:fiyat"), ("Açık pozisyonlar temiz.", "sozluk:pozisyon"),
    ("Stop tetiklendi.", "sozluk:stop"), ("Hisseleri sattık.", "sozluk:hisse"),
    ("Portföyde değişiklik yok.", "sozluk:portfoy"), ("Rejimi risk-on.", "sozluk:rejim"),
    ("Bütçemiz dolu.", "sozluk:butce"),
    ("Sinyaller karışık.", "sozluk:sinyal"), ("Emirler iletildi.", "sozluk:emir"),
    ("Dün gece tetiklendi.", "sozluk:tetik"), ("Zararı büyük.", "sozluk:zarar"),
])
def test_veri_isareti_cekimli_alan_kelimeleri_kok_onekiyle_yakalanir(cevap, isaret):
    assert bk.veri_isareti(cevap) == isaret


@pytest.mark.parametrize("cevap", ["karar verdim", "karne geldi", "kardeşim", "Merhaba, nasıl yardımcı olabilirim?"])
def test_veri_isareti_kar_cakismalari_veri_sayilmaz(cevap):
    assert bk.veri_isareti(cevap) is None


@pytest.mark.parametrize("cevap", ["Emirhan geldi", "Nedeni zararsız görünüyor"])
def test_veri_isareti_olculmus_sozluk_dislamalari_veri_sayilmaz(cevap):
    assert bk.veri_isareti(cevap) is None


def test_sozluk_dislama_kumesi_donuk():
    # Dışlama kümesi BİLİNÇLİ ve DONUK: bir alan kelimesini ("emirler") buraya sessizce eklemek sözlüğü kör eder.
    assert bk.SOZLUK_DISI == {"emirhan", "zararsiz"}


#: Tur 3 ölçümü (2026-09-30): önek kuralının kendi SOUL/uyarı metinlerimizdeki TÜM isabetleri, sınıflandırılmış.
#: KABUL = alan verisi, sayılır ("dikkat bütçesi", "alarm yığını", "emir gönderme"); DIŞLANAN = açıkça veri
#: değil ("nedeni zararsız görünüyor" — zararsız = "zararı yok" değil "masum").
SOUL_SOZLUK_KABUL = {"alarm", "butcesi", "butcesini", "emir"}
SOUL_SOZLUK_DISLANAN = {"zararsiz"}


def test_soul_ve_uyari_metinlerindeki_sozluk_isabetleri_olculmus_kumede():
    # Sembol dışlama çivisinin (Tur 2) eşi: SOUL'da YENİ bir kelime önek kuralına takılırsa bu çivi öter ve
    # kelime bilinçli sınıflanır (KABUL ya da `SOZLUK_DISI`).
    import pathlib
    kok = pathlib.Path(__file__).resolve().parent.parent / "deploy" / "hermes"
    soullar = sorted(kok.rglob("SOUL*.md"))
    assert soullar
    metinler = [p.read_text() for p in soullar] + [bk.UYARI_ARACSIZ, bk.UYARI_OLCULEMEDI]
    isabetler = {m.group(0) for t in metinler for m in bk._SOZLUK_DESENI.finditer(kadro.ad_katla(t))}
    assert isabetler and isabetler <= SOUL_SOZLUK_KABUL | SOUL_SOZLUK_DISLANAN, sorted(
        isabetler - SOUL_SOZLUK_KABUL - SOUL_SOZLUK_DISLANAN)
    assert SOUL_SOZLUK_DISLANAN <= bk.SOZLUK_DISI
    assert all(str(bk.veri_isareti(k)).startswith("sozluk:") for k in SOUL_SOZLUK_KABUL)
    assert all(bk.veri_isareti(k) is None for k in SOUL_SOZLUK_DISLANAN)


def test_veri_isareti_kok_kelime_ortasinda_sayilmaz():
    # Rol-1 Tur 3: önek KELİME BAŞINDA — "saplantı" içindeki `plan` veri değildir.
    assert bk.veri_isareti("Saplantı yapma") is None


@pytest.mark.parametrize("cevap,isaret", [
    ("Emirhan fiyatı sordu", "sozluk:fiyat"), ("Nedeni zararsız ama pozisyon açık", "sozluk:pozisyon")])
def test_veri_isareti_dislanan_kelimeden_sonra_taramaya_devam_eder(cevap, isaret):
    # Mutasyon M3-7 (Tur 3) hayatta kaldı: dışlanan kelimede tarama DURURSA arkasındaki gerçek veri kelimesi
    # sessizce kaçardı. Dışlama yalnız O kelimeyi atlar.
    assert bk.veri_isareti(cevap) == isaret


# ---- Tur 4 (Rol-1 kararı 2026-09-30: `getiri` düştü; `hisset` ÖNEK dışlaması) ------------------------------
# Ölçüm (Tur 3, depo Türkçe belgeleri): `getiri*` isabetlerinin 41/137'si "getirmek" fiiliydi.

def test_veri_isareti_getirmek_fiili_veri_sayilmaz_getiri_iddiasi_rakamla_yakalanir():
    assert bk.veri_isareti("bunu getirir misin") is None
    assert bk.veri_isareti("getiri %3") == "rakam" and bk.veri_iceriyor("getiri %3") is True


@pytest.mark.parametrize("cevap", ["Bu durum risk hissettirdi", "hissetmek zor", "Hissettim"])
def test_veri_isareti_hissetmek_fiili_veri_sayilmaz(cevap):
    # BİLİNEN GÜRÜLTÜ (Rol-1 kapsamı `hisset`): "hissediyorum"/"hissederim" `hissed` ile başlar ve `hisse`ye takılır;
    # `hissedi`/`hissede` dışlaması "hissedir" (hisse+dir) ve "hissede" (hisse+de) isimlerini de yutardı.
    assert bk.veri_isareti(cevap) is None


@pytest.mark.parametrize("cevap", ["Hissedarlar toplandı", "Hisseler düştü"])
def test_veri_isareti_hisse_isimleri_hisset_dislamasina_ragmen_yakalanir(cevap):
    assert bk.veri_isareti(cevap) == "sozluk:hisse"


def test_sozluk_onek_dislama_listesi_donuk():
    assert bk.SOZLUK_DISI_ONEK == ("hisset",)


# ---- Parça 1b G4 Görev 2: `unut:` İKİ ADIM (aday listesi → `onayla: unut <kod>`) + `geri al: <kod>` ---------------
# Plan Review Focus 2: ilk adım HİÇBİR şeyi değiştirmez (yalnız aday listesi + kısa kod); süresi geçen/yabancı/bilinmeyen
# kod reddedilir; başka botun adayını onaylamak mümkün değildir. Bekleyen kayıt `state/bot_unut_bekleyen.json` (Rol-1
# kararı 1): `{kod: {bot, idler, kesitler, ifade, ts, son, durum}}`, kod 6 hex, ömür 15 dk, kayıt SİLİNMEZ (durum değişir).

import re as _re  # noqa: E402  (G4 Görev 2 bölümü)

IKI_ADAY = [("m1", "eski not bir"), ("m2", "eski not iki")]


def _bekleyen():
    return store.read_json(bk.UNUT_BEKLEYEN, {})


def _unut_adimi(bot="bekci", ifade="eski not", h=None, simdi=SIMDI, kanal="telegram"):
    """İlk adımı koşar; `(cevap, kod, hafıza)` döner. Kod defter satırından okunur (cevapla aynı olduğu da ölçülür)."""
    h = h if h is not None else SahteHafiza(adaylar=IKI_ADAY)
    cevap = bk.bota_sor(bot, f"unut: {ifade}", kanal, "o", tasiyici=SahteTasiyici(), hafiza=h, simdi=simdi)
    kod = _defter()[-1].get("unut_kodu")
    return cevap, kod, h


def _onayla(kod, bot="bekci", h=None, simdi=SIMDI, kanal="telegram"):
    return bk.bota_sor(bot, f"onayla: unut {kod}", kanal, "o", tasiyici=SahteTasiyici(), hafiza=h, simdi=simdi)


def _geri_al(kod, bot="bekci", h=None, simdi=SIMDI):
    return bk.bota_sor(bot, f"geri al: {kod}", "pano", "o", tasiyici=SahteTasiyici(), hafiza=h, simdi=simdi)


def _olaylar(ad):
    return [e for e in obs.recent(50) if e.get("event") == ad]


def test_unut_ilk_adim_aday_listeler_hicbir_seyi_degistirmez_kod_verir(sandbox_state):
    t = SahteTasiyici()
    h = SahteHafiza(adaylar=IKI_ADAY)
    cevap = bk.bota_sor("bekci", "unut: eski not", "telegram", "o", tasiyici=t, hafiza=h, simdi=SIMDI)
    s = _defter()[-1]
    kod = s["unut_kodu"]
    assert _re.fullmatch(r"[0-9a-f]{6}", kod)
    assert "1) eski not bir 2) eski not iki" in cevap and f"onayla: unut {kod}" in cevap
    assert "unutulmadı" in cevap and "15 dk" in cevap
    # İLK ADIM PATCH ATMAZ: yalnız salt-okur aday sorgusu; uygula / geri al / model YOK.
    assert h.aday_sorgulari == [("bekci", "eski not")] and h.uygulananlar == [] and h.geri_al_denemeleri == []
    assert t.cagrilar == []
    assert (s["tur"], s["hafiza_durumu"], s["aday_idler"]) == ("unut", "onay_bekliyor", ["m1", "m2"])
    kayit = _bekleyen()[kod]
    assert kayit == {"bot": "bekci", "idler": ["m1", "m2"], "kesitler": ["eski not bir", "eski not iki"],
                     "ifade": "eski not", "ts": "2026-09-29T12:00:00+00:00", "son": "2026-09-29T12:15:00+00:00",
                     "durum": "bekliyor"}
    assert bk.UNUT_ONAY_OMRU == dt.timedelta(minutes=15)


def test_unut_eslesme_yoksa_acik_soyler_kod_yok(sandbox_state):
    cevap = bk.bota_sor("bekci", "unut: yok böyle bir şey", "pano", "o", hafiza=SahteHafiza(), simdi=SIMDI)
    assert cevap == "Eşleşen bir not bulamadım; hiçbir şey unutulmadı."
    s = _defter()[-1]
    assert (s["hafiza_durumu"], s["aday_idler"], s["unut_kodu"]) == ("eslesme_yok", [], None)
    assert _bekleyen() == {}


def test_unut_aday_hatasi_aranamadi_der_ve_nedenli_olay(sandbox_state):
    class Patlayan(SahteHafiza):
        def unut_adaylari(self, bot, ifade):
            raise _nedenli("zaman_asimi", "hindsight gizli-metin-XYZ")

    cevap = bk.bota_sor("bekci", "unut: x", "pano", "o", hafiza=Patlayan(), simdi=SIMDI)
    assert "ARANAMADI" in cevap and "gizli-metin" not in cevap
    s = _defter()[-1]
    assert (s["tur"], s["hafiza_durumu"], s["aday_idler"]) == ("unut", "aranamadi", [])
    (olay,) = _olaylar("bot_hafiza_unut_hatasi")
    assert (olay["bot"], olay["kanal"], olay["sinif"], olay["neden"], olay["adim"]) == (
        "bekci", "pano", "RuntimeError", "zaman_asimi", "aday")


@pytest.mark.parametrize("mesaj", ["unut:", "unut:   ", "Unut :\n"])
def test_unut_bos_govde_sorar_hafiza_cagrilmaz(sandbox_state, mesaj):
    # Boş sorgu recall'da en yakın rastgele bellekleri döndürür — hafızaya HİÇ gidilmez.
    h = SahteHafiza(adaylar=IKI_ADAY)
    cevap = bk.bota_sor("bekci", mesaj, "pano", "o", hafiza=h, simdi=SIMDI)
    assert "neyi unutayım" in cevap.lower() and h.aday_sorgulari == []
    assert _defter()[-1]["hafiza_durumu"] == "bos_govde"


def test_unut_ifadesi_hafizaya_ve_kayda_scrub_ile_gider(sandbox_state):
    # İfade Hindsight'a sorgu VE `reason` olarak gider (bellek geçmişinde kalır) — hatırla ile aynı süzgeç.
    anahtar = "sk-or-v1-" + "e" * 64
    _, kod, h = _unut_adimi(ifade=f"eski anahtar {anahtar}")
    assert anahtar not in h.aday_sorgulari[0][1] and "eski anahtar" in h.aday_sorgulari[0][1]
    assert anahtar not in json.dumps(_bekleyen()) and _bekleyen()[kod]["ifade"] == "eski anahtar ***"


def test_unut_kesitleri_cevapta_scrub_edilir(sandbox_state):
    anahtar = "sk-or-v1-" + "f" * 64
    cevap, kod, _ = _unut_adimi(h=SahteHafiza(adaylar=[("m1", f"anahtar {anahtar}")]))
    assert anahtar not in cevap and "1) anahtar ***" in cevap and anahtar not in json.dumps(_bekleyen())


def test_unut_adaylari_tavandan_fazlaysa_kayit_ve_onay_tavanda_kalir(sandbox_state):
    # Gerçek sınıf zaten `UNUT_TAVANI` döndürür; kanal katmanı sahte/değişen bir hafızaya da güvenmez (PATCH ≤ 3).
    h = SahteHafiza(adaylar=[(f"m{i}", f"not {i}") for i in range(1, 6)])
    _, kod, _ = _unut_adimi(h=h)
    assert _bekleyen()[kod]["idler"] == ["m1", "m2", "m3"]
    _onayla(kod, h=h)
    assert h.uygulananlar == [("bekci", ["m1", "m2", "m3"], "eski not")]


def test_onayla_ayni_bot_sure_icinde_uygular_ve_geri_alinabilir_der(sandbox_state):
    _, kod, h = _unut_adimi()
    cevap = _onayla(kod, h=h, simdi=SIMDI + dt.timedelta(minutes=14, seconds=59))
    assert h.uygulananlar == [("bekci", ["m1", "m2"], "eski not")]
    assert cevap == f"Unuttum (geri alınabilir — `geri al: {kod}`): 1) eski not bir 2) eski not iki"
    s = _defter()[-1]
    assert (s["tur"], s["hafiza_durumu"], s["unut_kodu"]) == ("unut_onay", "unutuldu", kod)
    assert (s["unutulan_idler"], s["denenen"], s["kalan"]) == (["m1", "m2"], ["m1", "m2"], [])
    assert _bekleyen()[kod]["durum"] == "uygulandi"


def test_onayla_baska_botun_kodunu_reddeder_patch_yok_kod_bekler(sandbox_state):
    _, kod, h = _unut_adimi(bot="bekci")
    cevap = _onayla(kod, bot="karne", h=h)
    assert h.uygulananlar == [] and "@bekci" in cevap and "unutulmadı" in cevap
    s = _defter()[-1]
    assert (s["bot"], s["tur"], s["hafiza_durumu"], s["ret_nedeni"]) == ("karne", "unut_onay", "reddedildi",
                                                                         "baska_bot")
    (olay,) = _olaylar("bot_unut_onay_reddi")
    assert (olay["bot"], olay["neden"]) == ("karne", "baska_bot")
    assert _bekleyen()[kod]["durum"] == "bekliyor"            # yabancının denemesi kodu TÜKETMEZ
    _onayla(kod, bot="bekci", h=h)
    assert h.uygulananlar == [("bekci", ["m1", "m2"], "eski not")]


@pytest.mark.parametrize("gecen", [dt.timedelta(minutes=15), dt.timedelta(minutes=16), dt.timedelta(days=2)])
def test_onayla_suresi_dolmus_kodu_reddeder(sandbox_state, gecen):
    _, kod, h = _unut_adimi()
    cevap = _onayla(kod, h=h, simdi=SIMDI + gecen)
    assert h.uygulananlar == [] and "süresi doldu" in cevap.lower()
    assert _defter()[-1]["ret_nedeni"] == "suresi_doldu"
    assert _olaylar("bot_unut_onay_reddi")[-1]["neden"] == "suresi_doldu"
    assert _bekleyen()[kod]["durum"] == "suresi_doldu"
    _onayla(kod, h=h, simdi=SIMDI + gecen)                     # ikinci deneme de aynı ret — kayıt silinmedi
    assert h.uygulananlar == [] and _defter()[-1]["ret_nedeni"] == "suresi_doldu"


@pytest.mark.parametrize("govde", ["unut ffffff", "unut xyz", "unut a1b2c", "evet", "unut", "unut a1b2c3 fazla",
                                   "sil a1b2c3"])
def test_onayla_bilinmeyen_ya_da_bicimsiz_kod_reddedilir(sandbox_state, govde):
    h = SahteHafiza(adaylar=IKI_ADAY)
    cevap = bk.bota_sor("bekci", f"onayla: {govde}", "pano", "o", hafiza=h, simdi=SIMDI)
    assert h.uygulananlar == [] and "unutulmadı" in cevap
    s = _defter()[-1]
    assert (s["tur"], s["hafiza_durumu"], s["ret_nedeni"]) == ("unut_onay", "reddedildi", "bilinmeyen_kod")
    assert _olaylar("bot_unut_onay_reddi")[-1]["neden"] == "bilinmeyen_kod"


def test_onayla_kod_harf_buyuklugune_duyarsiz(sandbox_state):
    _, kod, h = _unut_adimi()
    _onayla(kod.upper(), h=h)
    assert len(h.uygulananlar) == 1


def test_onayla_bos_govde_sorar_olay_yok(sandbox_state):
    h = SahteHafiza()
    cevap = bk.bota_sor("bekci", "onayla:", "pano", "o", hafiza=h, simdi=SIMDI)
    assert "onayla: unut" in cevap and h.uygulananlar == []
    assert _defter()[-1]["hafiza_durumu"] == "bos_govde" and _olaylar("bot_unut_onay_reddi") == []


def test_onayla_ikinci_kez_zaten_uygulandi(sandbox_state):
    _, kod, h = _unut_adimi()
    _onayla(kod, h=h)
    cevap = _onayla(kod, h=h)
    assert len(h.uygulananlar) == 1 and f"geri al: {kod}" in cevap
    assert _defter()[-1]["ret_nedeni"] == "zaten_uygulandi"


def test_onay_kismi_hatada_denenen_kalan_ve_unutulanlar_deftere(sandbox_state):
    hata = _nedenli("http_500")
    hata.unutulanlar, hata.denenen, hata.kalan = ["m1"], ["m1", "m2"], ["m3"]
    h = SahteHafiza(adaylar=[("m1", "bir"), ("m2", "iki"), ("m3", "üç")], uygula_hatasi=hata)
    _, kod, _ = _unut_adimi(h=h)
    cevap = _onayla(kod, h=h)
    assert cevap.startswith("UNUTULAMADI") and "1) bir" in cevap and "iki" not in cevap
    assert f"geri al: {kod}" in cevap
    s = _defter()[-1]
    assert (s["hafiza_durumu"], s["unutulan_idler"], s["denenen"], s["kalan"]) == (
        "unutulamadi", ["m1"], ["m1", "m2"], ["m3"])
    (olay,) = _olaylar("bot_hafiza_unut_hatasi")
    assert (olay["neden"], olay["adim"], olay["sinif"]) == ("http_500", "onay", "RuntimeError")
    kayit = _bekleyen()[kod]
    assert (kayit["durum"], kayit["denenen"]) == ("uygulandi", ["m1", "m2"])


def test_onay_hicbir_istek_atilmadiysa_kod_bekliyor_kalir_yeniden_denenebilir(sandbox_state):
    hata = _nedenli("anahtar_yok")
    hata.unutulanlar, hata.denenen, hata.kalan = [], [], ["m1", "m2"]
    h = SahteHafiza(adaylar=IKI_ADAY, uygula_hatasi=hata)
    _, kod, _ = _unut_adimi(h=h)
    cevap = _onayla(kod, h=h)
    assert cevap.startswith("UNUTULAMADI") and f"onayla: unut {kod}" in cevap
    assert _bekleyen()[kod]["durum"] == "bekliyor"
    assert _olaylar("bot_hafiza_unut_hatasi")[-1]["neden"] == "anahtar_yok"
    h.uygula_hatasi = None
    _onayla(kod, h=h)
    assert len(h.uygulananlar) == 2 and _bekleyen()[kod]["durum"] == "uygulandi"


def test_onay_istisnasi_denenen_tasimazsa_bilinmiyor_der_uydurmaz(sandbox_state):
    # Uydurma yasağı: istisna hangi PATCH'lerin denendiğini söylemiyorsa defter `None` yazar ("hiçbiri" değil); kod
    # `uygulandi` sayılır ki `geri al` TÜM adayları geri alabilsin (valid PATCH'i zaten geçerli bellekte zararsız).
    h = SahteHafiza(adaylar=IKI_ADAY, uygula_hatasi=ConnectionError("hindsight gizli-metin-XYZ"))
    _, kod, _ = _unut_adimi(h=h)
    cevap = _onayla(kod, h=h)
    assert cevap.startswith("UNUTULAMADI") and "gizli-metin" not in cevap
    s = _defter()[-1]
    assert (s["unutulan_idler"], s["denenen"], s["kalan"]) == (None, None, None)
    assert _olaylar("bot_hafiza_unut_hatasi")[-1]["neden"] == "beklenmeyen"
    assert _bekleyen()[kod]["durum"] == "uygulandi"
    _geri_al(kod, h=h)
    assert h.geri_al_denemeleri == [("bekci", "m1"), ("bekci", "m2")]


def test_geri_al_uygulanan_kodu_valid_yapar(sandbox_state):
    _, kod, h = _unut_adimi()
    _onayla(kod, h=h)
    cevap = _geri_al(kod, h=h, simdi=SIMDI + dt.timedelta(days=3))       # 15 dk sınırı geri almaya UYGULANMAZ
    assert h.geri_al_denemeleri == [("bekci", "m1"), ("bekci", "m2")]
    assert cevap == "Geri aldım (yeniden hatırlanır): 1) eski not bir 2) eski not iki"
    s = _defter()[-1]
    assert (s["tur"], s["hafiza_durumu"], s["unut_kodu"], s["geri_alinan_idler"], s["denenen"], s["kalan"]) == (
        "geri_al", "geri_alindi", kod, ["m1", "m2"], ["m1", "m2"], [])
    assert _bekleyen()[kod]["durum"] == "geri_alindi"


def test_geri_al_yalniz_denenen_idleri_geri_alir(sandbox_state):
    hata = _nedenli("http_500")
    hata.unutulanlar, hata.denenen, hata.kalan = ["m1"], ["m1", "m2"], ["m3"]
    h = SahteHafiza(adaylar=[("m1", "bir"), ("m2", "iki"), ("m3", "üç")], uygula_hatasi=hata)
    _, kod, _ = _unut_adimi(h=h)
    _onayla(kod, h=h)
    _geri_al(kod, h=h)
    # `m3` hiç denenmedi (`kalan`) — ona valid PATCH'i atılmaz; `m2` hata verdi ama sunucuda uygulanmış olabilir.
    assert h.geri_al_denemeleri == [("bekci", "m1"), ("bekci", "m2")]


@pytest.mark.parametrize("senaryo,neden", [
    ("bilinmeyen", "bilinmeyen_kod"), ("bicimsiz", "bilinmeyen_kod"), ("baska_bot", "baska_bot"),
    ("bekliyor", "uygulanmadi"), ("suresi_doldu", "uygulanmadi"), ("ikinci", "zaten_geri_alindi"),
])
def test_geri_al_ret_nedenleri(sandbox_state, senaryo, neden):
    _, kod, h = _unut_adimi()
    if senaryo in ("baska_bot", "ikinci"):
        _onayla(kod, h=h)
    if senaryo == "ikinci":
        _geri_al(kod, h=h)
    if senaryo == "suresi_doldu":
        _onayla(kod, h=h, simdi=SIMDI + dt.timedelta(hours=1))
    onceki = len(h.geri_al_denemeleri)
    hedef = {"bilinmeyen": "abcdef" if kod != "abcdef" else "fedcba", "bicimsiz": "xyz"}.get(senaryo, kod)
    cevap = _geri_al(hedef, bot="karne" if senaryo == "baska_bot" else "bekci", h=h)
    assert len(h.geri_al_denemeleri) == onceki and cevap
    s = _defter()[-1]
    assert (s["tur"], s["hafiza_durumu"], s["ret_nedeni"]) == ("geri_al", "reddedildi", neden)
    assert _olaylar("bot_unut_geri_al_reddi")[-1]["neden"] == neden


def test_geri_al_kismi_hatada_kod_uygulandi_kalir_yeniden_denenebilir(sandbox_state):
    h = SahteHafiza(adaylar=IKI_ADAY, geri_al_hatasi_sirasi=1)
    _, kod, _ = _unut_adimi(h=h)
    _onayla(kod, h=h)
    cevap = _geri_al(kod, h=h)
    assert "GERİ ALINAMADI" in cevap and "1) eski not bir" in cevap
    s = _defter()[-1]
    assert (s["hafiza_durumu"], s["geri_alinan_idler"], s["denenen"], s["kalan"]) == (
        "geri_alinamadi", ["m1"], ["m1", "m2"], [])
    olay = _olaylar("bot_hafiza_geri_al_hatasi")[-1]
    assert (olay["neden"], olay["sinif"]) == ("http_502", "RuntimeError")
    assert _bekleyen()[kod]["durum"] == "uygulandi"
    h.geri_al_hatasi_sirasi = None
    _geri_al(kod, h=h)
    assert _bekleyen()[kod]["durum"] == "geri_alindi"


def test_geri_al_bos_govde_sorar(sandbox_state):
    h = SahteHafiza()
    cevap = bk.bota_sor("bekci", "geri al:", "pano", "o", hafiza=h, simdi=SIMDI)
    assert "geri al: <kod>" in cevap and h.geri_al_denemeleri == []
    assert _defter()[-1]["hafiza_durumu"] == "bos_govde"


def test_bekleyen_kayitlar_yedi_gunden_eski_sonuclanmislari_budanir(sandbox_state):
    # Durum dosyası (defter DEĞİL) sınırsız büyümesin: 7 günden eski SONUÇLANMIŞ kayıt yazımda budanır; tam iz
    # `bot_sohbet.jsonl` defterinde kalır. Bedeli: 7 günden eski bir kod `geri al` ile artık bulunamaz.
    eski = SIMDI - dt.timedelta(days=8)
    _, uygulanan, h = _unut_adimi(simdi=eski)
    _onayla(uygulanan, h=h, simdi=eski)
    _, bekleyen, _ = _unut_adimi(simdi=eski, h=h)
    _, yakin, _ = _unut_adimi(simdi=SIMDI - dt.timedelta(days=6), h=h)
    _onayla(yakin, h=h, simdi=SIMDI - dt.timedelta(days=6))
    _, yeni, _ = _unut_adimi(simdi=SIMDI, h=h)
    doc = _bekleyen()
    assert uygulanan not in doc and bekleyen not in doc               # süresi dolmuş sayıldı ve budandı
    assert doc[yakin]["durum"] == "uygulandi" and doc[yeni]["durum"] == "bekliyor"
    assert bk.UNUT_BEKLEYEN_SAKLAMA == dt.timedelta(days=7)


def test_kod_cakisirsa_yeniden_uretilir(sandbox_state, monkeypatch):
    kodlar = iter(["aaaaaa", "aaaaaa", "bbbbbb"])
    monkeypatch.setattr(bk, "_kod_uret", lambda: next(kodlar))
    _, k1, h = _unut_adimi()
    _, k2, _ = _unut_adimi(h=h)
    assert (k1, k2) == ("aaaaaa", "bbbbbb") and set(_bekleyen()) == {"aaaaaa", "bbbbbb"}


def test_bekleyen_durum_sozlugu_donuk():
    assert bk.UNUT_DURUMLARI == ("bekliyor", "uygulandi", "geri_alindi", "suresi_doldu")


def test_kod_uretici_alti_hex(sandbox_state):
    assert all(_re.fullmatch(r"[0-9a-f]{6}", bk._kod_uret()) for _ in range(50))


def test_bekleyen_kayit_yazilamazsa_kod_verilmez_ve_olay(sandbox_state, monkeypatch):
    asil = store.update_json

    def patla(ad, fn, default=None):
        if ad == bk.UNUT_BEKLEYEN:
            raise OSError("disk dolu")
        return asil(ad, fn, default)
    monkeypatch.setattr(bk.store, "update_json", patla)
    cevap, kod, h = _unut_adimi()
    assert "onayla" not in cevap and "unutulmadı" in cevap and kod is None
    assert _defter()[-1]["hafiza_durumu"] == "kayit_yazilamadi"
    olay = _olaylar("bot_unut_bekleyen_hatasi")[-1]
    assert (olay["adim"], olay["sinif"]) == ("aday", "OSError")
    cevap = _onayla("abcdef", h=h)
    assert h.uygulananlar == [] and _defter()[-1]["hafiza_durumu"] == "kayit_hatasi"
    assert _olaylar("bot_unut_bekleyen_hatasi")[-1]["adim"] == "onay"


def test_hazir_degil_dali_emekli():
    # "hazır değil" metni/olayı artık YALAN olurdu (yöntem uygulandı); iz kalmasın.
    import inspect
    kaynak = inspect.getsource(bk)
    assert "bot_unut_hazir_degil" not in kaynak and not hasattr(bk, "_UNUT_HAZIR_DEGIL")


def test_tek_adimli_unut_dali_emekli():
    # Eski tek adımlı yol (`hafiza.unut` → hemen PATCH) kanal katmanında da iz bırakmaz.
    import inspect
    kaynak = inspect.getsource(bk)
    assert "hafiza.unut(" not in kaynak and ".unut(bot" not in kaynak


# ---- G4 Görev 2 Tur 2 (görev incelemesi M-1..M-4; Rol-1 2026-09-30) ------------------------------------------------

def _kaydi_boz(kod, sil=(), **alanlar):
    """Bekleyen kaydı DIŞARIDAN bozar (dış hasar benzetimi — üretim yolu değil, doğrudan `store`)."""
    doc = {k: dict(v) for k, v in store.read_json(bk.UNUT_BEKLEYEN, {}).items()}
    for alan in sil:
        doc[kod].pop(alan)
    doc[kod].update(alanlar)
    store.write_json(bk.UNUT_BEKLEYEN, doc)


@pytest.mark.parametrize("sil,bozuk", [
    ((), {"son": "bozuk-tarih"}), ((), {"son": None}), ((), {"son": "2026-09-29T12:15:00"}),   # dilimsiz an
    (("son",), {}), ((), {"ts": "x"}),
])
def test_suresi_olculemeyen_bekleyen_kod_onaylanamaz_fail_closed(sandbox_state, sil, bozuk):
    # M-1 (Rol-1 yükseltti): `ts`/`son` okunamayan kayıt süre denetimini ATLAMAZ — güvenlik kapısı hata durumunda
    # KAPALI kalır: `suresi_doldu` sayılır, onay reddedilir, PATCH atılmaz, bozuk kayıt olayla bildirilir.
    _, kod, h = _unut_adimi()
    _kaydi_boz(kod, sil=sil, **bozuk)
    cevap = _onayla(kod, h=h)
    assert h.uygulananlar == [] and "unutulmadı" in cevap
    assert _defter()[-1]["ret_nedeni"] == "suresi_doldu"
    assert _olaylar("bot_unut_onay_reddi")[-1]["neden"] == "suresi_doldu"
    assert _olaylar("bot_unut_bekleyen_bozuk_kayit")
    assert _bekleyen()[kod]["durum"] == "suresi_doldu"


def test_sahibi_okunamayan_kod_baska_bot_reddinde_none_yazmaz(sandbox_state):
    # M-1 "benzeri": `bot` alanı olmayan kayıt reddedilir (fail-closed) ve cevap "@None" demez.
    _, kod, h = _unut_adimi()
    _kaydi_boz(kod, sil=("bot",))
    cevap = _onayla(kod, h=h)
    assert h.uygulananlar == [] and "@None" not in cevap and "unutulmadı" in cevap
    assert _defter()[-1]["ret_nedeni"] == "baska_bot"


def test_yeni_aday_listesi_ayni_botun_eski_bekleyen_kodunu_dusurur(sandbox_state):
    # M-2 (Rol-1): bot başına TEK canlı kod — yeni liste verilirken aynı botun `bekliyor` kaydı `suresi_doldu` olur
    # (aynı kilitli yazımda; kayıt SİLİNMEZ). Eski listeyi yanlışlıkla onaylamak mümkün değildir.
    _, eski, h = _unut_adimi(ifade="eski not")
    _, yeni, _ = _unut_adimi(ifade="başka not", h=h)
    doc = _bekleyen()
    assert (doc[eski]["durum"], doc[yeni]["durum"]) == ("suresi_doldu", "bekliyor")
    cevap = _onayla(eski, h=h)
    assert h.uygulananlar == [] and "daha yeni" in cevap and "unutulmadı" in cevap
    assert _defter()[-1]["ret_nedeni"] == "suresi_doldu"
    assert _olaylar("bot_unut_onay_reddi")[-1]["neden"] == "suresi_doldu"
    _onayla(yeni, h=h)
    assert h.uygulananlar == [("bekci", ["m1", "m2"], "başka not")]


def test_yeni_aday_listesi_baska_botun_ve_sonuclanmis_kodlara_dokunmaz(sandbox_state):
    _, karne_kodu, h = _unut_adimi(bot="karne")
    _, uygulanan, _ = _unut_adimi(h=h)
    _onayla(uygulanan, h=h)
    _, yeni, _ = _unut_adimi(h=h)
    doc = _bekleyen()
    assert (doc[karne_kodu]["durum"], doc[uygulanan]["durum"], doc[yeni]["durum"]) == (
        "bekliyor", "uygulandi", "bekliyor")


def test_eslesmesiz_unut_eski_bekleyen_kodu_dusurmez(sandbox_state):
    # Liste VERİLMEDİYSE (eşleşme yok) yeni kod da yoktur — eski kod canlı kalır.
    _, kod, h = _unut_adimi()
    bk.bota_sor("bekci", "unut: yok böyle bir şey", "pano", "o", hafiza=SahteHafiza(), simdi=SIMDI)
    assert _bekleyen()[kod]["durum"] == "bekliyor"


def test_geri_alinmis_kodu_onaylamak_dogru_durumu_soyler(sandbox_state):
    # M-3: geri alınmış kod "zaten onaylandı (geri almak için …)" DEMEZ — ret nedeni ve metin gerçek durumu söyler.
    _, kod, h = _unut_adimi()
    _onayla(kod, h=h)
    _geri_al(kod, h=h)
    cevap = _onayla(kod, h=h)
    assert len(h.uygulananlar) == 1
    assert _defter()[-1]["ret_nedeni"] == "zaten_geri_alindi"
    assert _olaylar("bot_unut_onay_reddi")[-1]["neden"] == "zaten_geri_alindi"
    assert "geri alındı" in cevap and "zaten onaylandı" not in cevap


@pytest.mark.parametrize("islem", ["onayla", "geri_al"])
def test_budanmis_kod_bulunamadi_ve_saklama_suresi_soylenir(sandbox_state, islem):
    # M-4: 7 günden eski sonuçlanmış kayıt budanır; bilinmeyen kodda operatör NEDEN bulunamadığını öğrenir.
    eski = SIMDI - dt.timedelta(days=8)
    _, kod, h = _unut_adimi(simdi=eski)
    _onayla(kod, h=h, simdi=eski)
    _unut_adimi(bot="karne", h=h)                               # herhangi bir yazım budamayı tetikler
    assert kod not in _bekleyen()
    cevap = _onayla(kod, h=h) if islem == "onayla" else _geri_al(kod, h=h)
    assert _defter()[-1]["ret_nedeni"] == "bilinmeyen_kod"
    assert "bulunamadı" in cevap and "yanlış yazılmış" in cevap
    assert f"{bk.UNUT_BEKLEYEN_SAKLAMA.days} günden eski" in cevap and "budanmış" in cevap
    assert h.geri_al_denemeleri == [] and len(h.uygulananlar) == 1


# ---- Parça 1b G4 Görev 1: üretim kablolaması + dönüş kaydı + modele giden scrub + bütçe çapraz çivisi ----------
# Spec §3.4 (2026-09-30 düzeltmesi): Hermes `auto_retain` KAPALI — sohbet dönüşünü hafızaya YALNIZ `bota_sor` yazar,
# scrub'lı ve etiketli. Hafıza yazımı CEVABI DÜŞÜRMEZ; defter `hafiza_durumu` doğruyu söyler.

def _olay(ad):
    return [e for e in obs.recent(50) if e.get("event") == ad]


def test_sohbet_donusu_hafizaya_etiketli_yazilir_defter_kabul_edildi(sandbox_state):
    t, h = SahteTasiyici("rejim risk-on"), SahteHafiza()
    assert bk.bota_sor("bekci", "durum?", "telegram", "tg-bekci-1", tasiyici=t, hafiza=h, simdi=SIMDI) \
        == "rejim risk-on"
    assert h.donusler == [("bekci", "durum?", "rejim risk-on", ("bot:bekci", "kanal:telegram", "sohbet_donusu"))]
    assert h.yazilanlar == [] and h.aday_sorgulari == []
    s = _defter()[-1]
    # Tur 3 (inceleme M-1): `async: true` kabulü "işlendi" DEĞİLDİR — durum adı bunu söyler, kimlik deftere düşer.
    assert (s["tur"], s["hafiza_durumu"], s["hafiza_islem_kimligi"]) == ("sohbet", "kabul_edildi", "op-1")


@pytest.mark.parametrize("metin,arac,ek_etiketler,onek", [
    ("3 kalem", 0, ("arac_siz_veri",), bk.UYARI_ARACSIZ),       # araçsız VERİ → etiket + önekli cevap hafızada
    ("Getiri %2", None, ("arac_olculemedi",), bk.UYARI_OLCULEMEDI),  # sayı ölçülemedi → yalnız `arac_olculemedi`
    ("Merhaba!", 0, (), None),                                  # araçsız ama verisiz → etiket yok
    ("3 kalem", 2, (), None),                                   # araçlı veri → etiket yok
])
def test_donus_etiketleri_arac_isaretlerini_tasir_ve_onekli_cevap_yazilir(sandbox_state, metin, arac, ek_etiketler,
                                                                           onek):
    h = SahteHafiza()
    cevap = bk.bota_sor("karne", "soru", "pano", "o", tasiyici=SayacliTasiyici(metin, arac), hafiza=h, simdi=SIMDI)
    ((bot, mesaj, yazilan, etiketler),) = h.donusler
    assert (bot, mesaj) == ("karne", "soru")
    assert etiketler == ("bot:karne", "kanal:pano", "sohbet_donusu") + ek_etiketler
    # Hafızaya giden cevap operatörün GÖRDÜĞÜ (önekli) metindir: uyarı hafızada da kalır.
    assert yazilan == cevap == (metin if onek is None else f"{onek}\n{metin}")


class _PatlayanDonus(SahteHafiza):
    def __init__(self, hata):
        super().__init__()
        self.hata = hata

    def donus_yaz(self, bot, mesaj, cevap, etiketler):
        self.donusler.append((bot, mesaj, cevap, etiketler))
        raise self.hata


def _nedenli(neden, mesaj="hindsight gizli-metin-XYZ"):
    hata = RuntimeError(mesaj)
    hata.neden = neden
    return hata


@pytest.mark.parametrize("hata,sinif,neden", [
    (_nedenli("http_503"), "RuntimeError", "http_503"),
    (_nedenli("zaman_asimi"), "RuntimeError", "zaman_asimi"),
    (_nedenli("anahtar_yok"), "RuntimeError", "anahtar_yok"),
    (_nedenli("uydurma_neden"), "RuntimeError", "beklenmeyen"),    # kapalı küme DIŞI öznitelik geçmez
    (ConnectionError("hindsight gizli-metin-XYZ"), "ConnectionError", "beklenmeyen"),  # işaretsiz istisna
])
def test_donus_hafiza_istisnasi_cevabi_dusurmez_yazilamadi_ve_olay(sandbox_state, hata, sinif, neden):
    h = _PatlayanDonus(hata)
    cevap = bk.bota_sor("bekci", "durum?", "telegram", "o", tasiyici=SahteTasiyici("rejim risk-on"), hafiza=h,
                        simdi=SIMDI)
    assert cevap == "rejim risk-on" and len(h.donusler) == 1
    s = _defter()[-1]
    assert (s["tur"], s["hafiza_durumu"], s["cevap"]) == ("sohbet", "yazilamadi", "rejim risk-on")
    assert s["hafiza_islem_kimligi"] is None
    (olay,) = _olay("bot_hafiza_donus_hatasi")
    assert set(olay) == {"ts", "level", "event", "bot", "kanal", "sinif", "neden"}
    assert (olay["bot"], olay["kanal"], olay["sinif"], olay["neden"]) == ("bekci", "telegram", sinif, neden)
    assert "gizli-metin" not in json.dumps(obs.recent(50))


def test_donus_success_false_yazilamadi_ve_olay(sandbox_state):
    cevap = bk.bota_sor("bekci", "durum?", "pano", "o", tasiyici=SahteTasiyici("tamam"),
                        hafiza=SahteHafiza(donus_sonuc=False), simdi=SIMDI)
    assert cevap == "tamam" and _defter()[-1]["hafiza_durumu"] == "yazilamadi"
    (olay,) = _olay("bot_hafiza_donus_yazilamadi")
    assert (olay["bot"], olay["kanal"]) == ("bekci", "pano")


def test_kota_dolu_turda_donus_yazilmaz_atlandi(sandbox_state):
    k = tuple(kadro.Bot(**{**b.__dict__, "gunluk_tavan": 1, "gunluk_tavan_neden": None})
              if b.ad == "karne" else b for b in kadro.kadro_yukle())
    h = SahteHafiza()
    bk.bota_sor("karne", "1", "pano", "o", tasiyici=SahteTasiyici(), hafiza=h, simdi=SIMDI, kadro=k)
    assert "kotam doldu" in bk.bota_sor("karne", "2", "pano", "o", tasiyici=SahteTasiyici(), hafiza=h, simdi=SIMDI,
                                        kadro=k)
    assert [d[1] for d in h.donusler] == ["1"]
    s = _defter()[-1]
    assert (s["tur"], s["hafiza_durumu"]) == ("kota_doldu", "atlandi")


def test_hata_turunda_donus_yazilmaz_atlandi(sandbox_state):
    h = SahteHafiza()
    with pytest.raises(TimeoutError):
        bk.bota_sor("bekci", "x", "telegram", "o", tasiyici=SahteTasiyici(hata=TimeoutError("zaman")), hafiza=h,
                    simdi=SIMDI)
    assert h.donusler == []
    s = _defter()[-1]
    assert (s["tur"], s["hafiza_durumu"]) == ("hata", "atlandi")


@pytest.mark.parametrize("mesaj", ["hatırla: cuma toplantısı iptal", "unut: eski not"])
def test_komut_turunda_donus_yazilmaz(sandbox_state, mesaj):
    h = SahteHafiza()
    bk.bota_sor("sef", mesaj, "pano", "o", tasiyici=SahteTasiyici(), hafiza=h, simdi=SIMDI)
    assert h.donusler == [] and len(h.yazilanlar) + len(h.aday_sorgulari) == 1


def test_modele_giden_mesaj_scrub_edilir(sandbox_state):
    # Rol-1 hükmü (plan Global Constraints): operatörün yapıştırdığı sır DIŞ MODELE gitmez.
    anahtar = "sk-or-v1-" + "d" * 64
    t, h = SahteTasiyici("tamam"), SahteHafiza()
    bk.bota_sor("sef", f"anahtarım {anahtar} bunu sakla", "pano", "o", tasiyici=t, hafiza=h, simdi=SIMDI)
    ((_, giden, _),) = t.cagrilar
    assert anahtar not in giden and giden == "anahtarım *** bunu sakla"
    ((_, hafizaya, _, _),) = h.donusler
    assert anahtar not in hafizaya and hafizaya == "anahtarım *** bunu sakla"


def test_hafizaya_giden_cevap_da_scrub_edilir(sandbox_state):
    # Model cevabı bir sırrı yankılayabilir; operatöre dönen metin değişmez ama HAFIZAYA giden maskelidir.
    anahtar = "sk-or-v1-" + "9" * 64
    h = SahteHafiza()
    cevap = bk.bota_sor("sef", "x", "pano", "o", tasiyici=SahteTasiyici(f"anahtar {anahtar}"), hafiza=h, simdi=SIMDI)
    assert anahtar in cevap
    ((_, _, hafizaya, _),) = h.donusler
    assert anahtar not in hafizaya and hafizaya == "anahtar ***"


def test_hafiza_verilmezse_uretim_varsayilani_gercek_sinif_anahtarsiz_yazilamadi(sandbox_state, monkeypatch):
    # Üretim yolu: `hafiza` VERİLMEZ → `bot_hafiza.HindsightHafiza()`. Testte credential kanalı kapalı (sandbox) →
    # HTTP'den ÖNCE `anahtar_yok`; cevap düşmez, sessiz de kalınmaz. Ağa çıkılmadığı tuzakla ölçülür.
    from meridian import bot_hafiza as bh
    istekler = []

    def urlopen(istek, timeout=None):
        istekler.append(istek.full_url)
        raise AssertionError("anahtarsız hafıza isteği atıldı")
    monkeypatch.setattr(bh.urllib.request, "urlopen", urlopen)
    assert bk.bota_sor("bekci", "durum?", "telegram", "o", tasiyici=SahteTasiyici("tamam"), simdi=SIMDI) == "tamam"
    assert istekler == []
    s = _defter()[-1]
    assert (s["tur"], s["hafiza_durumu"]) == ("sohbet", "yazilamadi")
    (olay,) = _olay("bot_hafiza_donus_hatasi")
    assert (olay["sinif"], olay["neden"]) == ("RuntimeError", "anahtar_yok")


def test_bagli_degil_dali_emekli():
    # "bağlı değil" dalı artık ULAŞILAMAZ (hafıza verilmezse gerçek sınıf) — metni, olayı ve sabitleri iz bırakmaz.
    import inspect
    kaynak = inspect.getsource(bk)
    assert "bot_hafiza_bagli_degil" not in kaynak and "bagli_degil" not in kaynak
    assert not hasattr(bk, "_HAFIZA_BAGLI_DEGIL") and not hasattr(bk, "_UNUT_BAGLI_DEGIL")


def test_hafiza_protokolu_donus_yazi_tasir():
    import inspect
    assert list(inspect.signature(bk.Hafiza.donus_yaz).parameters) == ["self", "bot", "mesaj", "cevap", "etiketler"]


def test_hermes_zaman_asimi_sohbet_cagri_butcesini_kapsar():
    # M-5 çapraz çivisi: taşıyıcı api_server'ı, Hermes'in bir model çağrısını en kötü `deneme × istek zaman aşımı`
    # boyunca beklediğinden DAHA KISA bekleseydi, model hâlâ çalışırken taşıyıcı düşer ve operatör "cevap veremiyor"
    # alırdı. Bütçe sabitleri üretecin TEK kaynağından okunur (paket değil — KAYNAKTAN yüklenir).
    import inspect
    import pathlib

    from tests.conftest import betikten_modul_yukle
    u = betikten_modul_yukle(pathlib.Path(__file__).resolve().parent.parent / "ops/sohbet_profili_uret.py",
                             "sohbet_profili_uret_v593")
    varsayilan = inspect.signature(bk.HermesTasiyici).parameters["zaman_asimi_s"].default
    assert varsayilan == bk.HERMES_ZAMAN_ASIMI_S
    assert varsayilan >= u.SOHBET_API_DENEME * u.SOHBET_ISTEK_ZAMAN_ASIMI_SN


# ---- Tur 3 (görev incelemesi I-1, M-1, M-2 — Rol-1 kararları 2026-09-30) ---------------------------------------------
# I-1: Telegram YANIT turunda `mesaj` = yanıtlanan metnin VERİ çiti + operatörün sözleri. Hafızaya "Operatör:" diye
# giden metin çiti TAŞIMAZ (alıntı yanlış atıfla bankaya girmesin; uzun alıntıda operatörün sorusu tavanın dışına
# düşmesin); yerine `(yanıt: <ilk satır>)` kaynak etiketi. MODELE giden mesaj DEĞİŞMEZ (bağlam için alıntı gerekir).

from meridian import skill_gorus_llm as sgl, telegram_dinleyici as td  # noqa: E402  (Tur 3 bölümü)

RAPOR = "🔭 Meridian bekçi — 29 Eyl\n1. TAKILI AAPL planı 3 gündür bekliyor"


def _yanit_mesaji(alinti, sozler):
    """Telegram yanıt kipindeki `bota_sor` girdisi — GERÇEK üreticiyle (`telegram_dinleyici._bota_giden`) kurulur."""
    return td._bota_giden({"reply_to_message": {"text": alinti}}, sozler)


def test_telegram_yanit_turunda_hafizaya_cit_degil_kaynak_etiketi_ve_sozler_gider(sandbox_state):
    mesaj = _yanit_mesaji(RAPOR, "bu kalem ne?")
    assert sgl.VERI_ACILIS.format(ad=bk.ALINTI_CIT_ADI) in mesaj          # girdi gerçekten çitli
    t, h = SahteTasiyici("AAPL planı onay bekliyor"), SahteHafiza()
    bk.bota_sor("bekci", mesaj, "telegram", "tg-bekci-r99", tasiyici=t, hafiza=h, simdi=SIMDI)
    ((_, modele, _),) = t.cagrilar
    assert modele == mesaj                                                 # model alıntıyı GÖRÜR (bağlam)
    ((_, hafizaya, _, _),) = h.donusler
    assert hafizaya == "(yanıt: 🔭 Meridian bekçi — 29 Eyl)\nbu kalem ne?"
    assert "<<<" not in hafizaya and "TAKILI AAPL" not in hafizaya
    assert _defter()[-1]["mesaj"] == mesaj                                 # yerel defter tam metni tutar


def test_telegram_yanit_uzun_alintida_operator_sorusu_hafizada_kalir(sandbox_state):
    # İnceleme I-1 (b): tavan sondan keser; 1940+ karakterlik alıntıda operatörün sorusu kayıttan düşüyordu.
    alinti = "Rapor başlığı\n" + "x" * 3000
    h = SahteHafiza()
    bk.bota_sor("bekci", _yanit_mesaji(alinti, "bu kalem ne?"), "telegram", "o", tasiyici=SahteTasiyici(), hafiza=h,
                simdi=SIMDI)
    ((_, hafizaya, _, _),) = h.donusler
    assert hafizaya == "(yanıt: Rapor başlığı)\nbu kalem ne?" and len(hafizaya) < bh.DONUS_TAVANI


def test_telegram_yanit_kaynak_etiketi_once_scrub_sonra_tavan(sandbox_state):
    anahtar = "sk-or-v1-" + "7" * 64
    h = SahteHafiza()
    bk.bota_sor("bekci", _yanit_mesaji("y" * 60 + " " + anahtar + "\nikinci", "ne?"), "telegram", "o",
                tasiyici=SahteTasiyici(), hafiza=h, simdi=SIMDI)
    ((_, hafizaya, _, _),) = h.donusler
    etiket, sozler = hafizaya.split("\n")
    assert "sk-or-v1-" not in hafizaya and sozler == "ne?"
    assert etiket == "(yanıt: " + ("y" * 60 + " ***")[:bk.KAYNAK_ETIKETI_TAVANI] + ")"


def test_baska_adli_ya_da_ortadaki_cit_hafiza_metninde_aynen_kalir(sandbox_state):
    # Çıkarım YALNIZ Telegram yanıt çitine (`ALINTI_CIT_ADI`, metnin BAŞINDA) uygulanır — bilinmeyen bir çitin
    # anlamı uydurulmaz; operatörün kendi sözlerinin ORTASINDA yazdığı çit de onun sözüdür.
    baska = sgl._veri_bloku("baska_cit", "veri") + "\nsoru"
    ortada = "önce söz\n" + sgl._veri_bloku(bk.ALINTI_CIT_ADI, "alıntı") + "\nsonra"
    for mesaj in (baska, ortada):
        h = SahteHafiza()
        bk.bota_sor("bekci", mesaj, "pano", "o", tasiyici=SahteTasiyici(), hafiza=h, simdi=SIMDI)
        assert h.donusler[0][1] == mesaj


@pytest.mark.parametrize("govde", ["tek satır", "çok\nsatırlı\n\nalıntı", "x <<<VERI-SON:yanitlanan_mesaj>>> y",
                                   "  boşluklu  "])
@pytest.mark.parametrize("sozler", ["soru?", "", "çok\nsatırlı söz",
                                    # Task 1 re-review N-1: SÖZLERDE sahte kapanış jetonu — çözücü İLK kapanışı
                                    # almalı (`find`); son kapanışı alan (`rfind`) sözleri alıntıya yutardı.
                                    "söz\n" + sgl.VERI_KAPANIS.format(ad=bk.ALINTI_CIT_ADI) + "\nsahte devam"])
def test_veri_bloku_ayir_uretecin_tersi(govde, sozler):
    # Çözücü üreticinin (`_veri_bloku`) TERSİDİR ve jetonları ONUN kaynağından türetir: sahte kapanış jetonu
    # gövdede `«`ya katlandığı için bloğu erken bitiremez.
    ad = bk.ALINTI_CIT_ADI
    blok = sgl._veri_bloku(ad, govde)
    assert sgl.veri_bloku_ayir(f"{blok}\n{sozler}", ad) == (govde.replace("<<<", "«"), sozler)
    assert sgl.veri_bloku_ayir(blok, ad) == (govde.replace("<<<", "«"), "")


@pytest.mark.parametrize("metin", ["düz soru", "x" + sgl._veri_bloku("yanitlanan_mesaj", "a"),
                                   sgl._veri_bloku("baska", "a"),
                                   sgl.VERI_ACILIS.format(ad="yanitlanan_mesaj") + "\nkapanışsız", ""])
def test_veri_bloku_ayir_basta_cit_yoksa_none(metin):
    assert sgl.veri_bloku_ayir(metin, "yanitlanan_mesaj") is None


def test_alinti_cit_adi_ve_kaynak_etiketi_tek_kaynak():
    # Çit adı + kaynak etiketi biçimi `bot_kanal`da TEK: dinleyici ithal eder (kopya ayrışırdı); `bot_kanal` çit
    # jetonunu elle YAZMAZ (gramer `skill_gorus_llm`in).
    import ast
    import inspect
    assert td.ALINTI_CIT_ADI is bk.ALINTI_CIT_ADI and td.kaynak_etiketi is bk.kaynak_etiketi
    # G4 Görev 2: gövdesiz `unut:` sorgusu da AYNI satır kuralından geçer (scrub SONRA tavan). G4 kalıntıları M-2
    # (2026-10-01): kural ilk İÇERİK satırıdır (imza/uyarı atlanır) ve adı `alinti_icerik_satiri` — v608.
    assert td.alinti_icerik_satiri is bk.alinti_icerik_satiri
    atananlar = {h.id for n in ast.parse(inspect.getsource(td)).body if isinstance(n, ast.Assign)
                 for h in n.targets if isinstance(h, ast.Name)}
    assert not atananlar & {"ALINTI_CIT_ADI", "KAYNAK_ETIKETI_TAVANI"}
    assert "<<<" not in inspect.getsource(bk)
    assert bk.kaynak_etiketi("  ilk satır \n ikinci") == "(yanıt: ilk satır)"


# ---- M-1: işlem kimliği · M-2: hafıza süresi ----------------------------------------------------------------------

@pytest.mark.parametrize("kimlik", ["op-42", None])
def test_donus_islem_kimligi_deftere_yazilir(sandbox_state, kimlik):
    bk.bota_sor("bekci", "x", "pano", "o", tasiyici=SahteTasiyici(), hafiza=SahteHafiza(donus_kimlik=kimlik),
                simdi=SIMDI)
    s = _defter()[-1]
    assert "hafiza_islem_kimligi" in s and s["hafiza_islem_kimligi"] == kimlik


def test_donus_hafiza_suresi_sahte_saatle_olculur_model_suresine_karismaz(sandbox_state, monkeypatch):
    anlar = iter([100.0, 101.5, 101.5, 101.7504])       # taşıyıcı başı · taşıyıcı sonu · hafıza başı · hafıza sonu
    monkeypatch.setattr(bk, "_saat", lambda: next(anlar))
    bk.bota_sor("bekci", "x", "pano", "o", tasiyici=SahteTasiyici(), hafiza=SahteHafiza(), simdi=SIMDI)
    s = _defter()[-1]
    assert (s["sure_s"], s["hafiza_sure_s"]) == (1.5, 0.25)
    assert isinstance(s["hafiza_sure_s"], float) and not isinstance(s["hafiza_sure_s"], bool)


def test_hafiza_hatasinda_da_sure_olculur(sandbox_state, monkeypatch):
    anlar = iter([0.0, 1.0, 1.0, 4.0])
    monkeypatch.setattr(bk, "_saat", lambda: next(anlar))
    bk.bota_sor("bekci", "x", "pano", "o", tasiyici=SahteTasiyici(), hafiza=_PatlayanDonus(TimeoutError("t")),
                simdi=SIMDI)
    s = _defter()[-1]
    assert (s["hafiza_durumu"], s["hafiza_sure_s"]) == ("yazilamadi", 3.0)


def test_kota_ve_hata_satirinda_hafiza_suresi_ve_kimligi_yok(sandbox_state):
    k = tuple(kadro.Bot(**{**b.__dict__, "gunluk_tavan": 1, "gunluk_tavan_neden": None})
              if b.ad == "karne" else b for b in kadro.kadro_yukle())
    bk.bota_sor("karne", "1", "pano", "o", tasiyici=SahteTasiyici(), hafiza=SahteHafiza(), simdi=SIMDI, kadro=k)
    bk.bota_sor("karne", "2", "pano", "o", tasiyici=SahteTasiyici(), hafiza=SahteHafiza(), simdi=SIMDI, kadro=k)
    with pytest.raises(TimeoutError):
        bk.bota_sor("bekci", "x", "pano", "o", tasiyici=SahteTasiyici(hata=TimeoutError("z")), hafiza=SahteHafiza(),
                    simdi=SIMDI)
    kota, hata = _defter()[-2:]
    assert (kota["tur"], hata["tur"]) == ("kota_doldu", "hata")
    for satir in (kota, hata):
        assert "hafiza_sure_s" not in satir and "hafiza_islem_kimligi" not in satir
        assert satir["hafiza_durumu"] == "atlandi"


def test_donus_sonucu_nesne_degilse_yazilamadi_cevap_dusmez(sandbox_state):
    class Eski(SahteHafiza):
        def donus_yaz(self, bot, mesaj, cevap, etiketler):
            return True                                    # eski bool sözleşmesi — sessizce "kabul" SAYILMAZ

    assert bk.bota_sor("bekci", "x", "pano", "o", tasiyici=SahteTasiyici("tamam"), hafiza=Eski(), simdi=SIMDI) == "tamam"
    assert _defter()[-1]["hafiza_durumu"] == "yazilamadi"
    # Task 1 re-review N-3: istisna yolu SESSİZ değil — olay sınıf + kapalı-küme nedenle yazılır.
    (olay,) = _olay("bot_hafiza_donus_hatasi")
    assert (olay["bot"], olay["kanal"], olay["sinif"], olay["neden"]) == ("bekci", "pano", "AttributeError",
                                                                          "beklenmeyen")
