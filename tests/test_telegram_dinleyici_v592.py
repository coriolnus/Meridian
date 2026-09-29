"""v592 — Telegram dinleyicisi çekirdeği (spec 2026-09-29 §3.5, K3): yetki, yönlendirme, yanıt, yoklama."""
import hashlib

import pytest

from meridian import kadro, notify, obs, telegram_dinleyici as td

YETKILI = "4242"


def _m(metin, sohbet=YETKILI, yanit=None, mid=7):
    m = {"message_id": mid, "chat": {"id": int(sohbet)}, "text": metin}
    if yanit is not None:
        m["reply_to_message"] = {"message_id": 99, "text": yanit}
    return m


@pytest.mark.parametrize("metin,bot,neden,govde", [
    ("@bekci şu an takılı ne var?", "bekci", "onek", "şu an takılı ne var?"),
    ("@Bekci: durum?", "bekci", "onek", "durum?"),
    ("@KARNE, bu hafta?", "karne", "onek", "bu hafta?"),
    ("merhaba", "sef", "varsayilan", "merhaba"),
])
def test_yonlendir_onek_ve_varsayilan(metin, bot, neden, govde):
    y = td.yonlendir(_m(metin), YETKILI)
    assert (y.bot, y.neden, y.metin) == (bot, neden, govde)


def test_yonlendir_rapor_imzasina_yanit():
    y = td.yonlendir(_m("bu kalem ne?", yanit="🔭 Meridian bekçi\n1. TAKILI x"), YETKILI)
    assert (y.bot, y.neden) == ("bekci", "imza")


def test_yonlendir_bot_cevabina_yanit_ayni_bota():
    y = td.yonlendir(_m("devam et", yanit="💬 @karne\nGEÇTİ"), YETKILI)
    assert (y.bot, y.neden) == ("karne", "sohbet_imza")


def test_yonlendir_onek_yanittan_once_gelir():
    y = td.yonlendir(_m("@karne bak", yanit="🔭 Meridian bekçi\n…"), YETKILI)
    assert y.bot == "karne"


def test_yonlendir_yabanci_sohbet():
    assert td.yonlendir(_m("@bekci selam", sohbet="5550123987"), YETKILI).neden == "yabanci"


def test_yonlendir_pasif_ve_bilinmeyen_bot():
    assert td.yonlendir(_m("@kod neden?"), YETKILI).neden == "pasif_bot"
    assert td.yonlendir(_m("@yokboyle selam"), YETKILI).neden == "bilinmeyen_bot"
    assert td.yonlendir(_m("   "), YETKILI).neden == "bos"


def test_oturum_kimligi():
    assert td.oturum_kimligi("bekci", _m("x", yanit="🔭 Meridian bekçi"), "20260929") == "tg-bekci-r99"
    assert td.oturum_kimligi("sef", _m("x"), "20260929") == "tg-sef-20260929"


def _isle(metin, sohbet=YETKILI, yanit=None, cevap="tamam", hata=None):
    cagrilar, gidenler = [], []

    def bota_sor(bot, m, kanal, oturum):
        cagrilar.append((bot, m, kanal, oturum))
        if hata:
            raise hata
        return cevap

    neden = td.isle({"update_id": 1, "message": _m(metin, sohbet, yanit)}, yetkili_sohbet=YETKILI,
                    bota_sor=bota_sor, gonder=lambda t, r: gidenler.append((t, r)) or True, bugun="20260929")
    return neden, cagrilar, gidenler


def test_isle_normal_cevap_imzali_ve_yanitli(sandbox_state):
    neden, cagrilar, gidenler = _isle("@bekci durum?")
    assert neden == "onek"
    assert cagrilar == [("bekci", "durum?", "telegram", "tg-bekci-20260929")]
    assert gidenler[0][0].startswith("💬 @bekci\n") and gidenler[0][1] == 7


def test_isle_yabanci_cevapsiz_ve_sayilir(sandbox_state):
    neden, cagrilar, gidenler = _isle("@bekci selam", sohbet="5550123987")
    assert (neden, cagrilar, gidenler) == ("yabanci", [], [])
    olay = [e for e in obs.recent(20) if e.get("event") == "bot_yabanci_mesaj"]
    assert olay and olay[-1].get("sohbet_sha") == hashlib.sha256(b"5550123987").hexdigest()[:12]
    assert "5550123987" not in str(olay[-1])


def test_isle_bota_sor_hatasi_sessiz_degil(sandbox_state):
    neden, _, gidenler = _isle("@karne?", hata=TimeoutError("zaman aşımı"))
    assert "cevap veremiyor" in gidenler[0][0] and "TimeoutError" in gidenler[0][0]
    assert any(e.get("event") == "bot_sohbet_hatasi" for e in obs.recent(20))


def test_isle_pasif_bot_bilgilendirir(sandbox_state):
    neden, cagrilar, gidenler = _isle("@kod neden?")
    assert neden == "pasif_bot" and cagrilar == [] and "henüz aktif değil" in gidenler[0][0]


def test_guncellemeleri_al_basari_ve_hata(sandbox_state):
    def iyi(url, govde, zaman_asimi):
        assert url.endswith("/getUpdates") and govde["offset"] == 5 and govde["timeout"] == 50
        return {"ok": True, "result": [{"update_id": 5}]}

    def kotu(url, govde, zaman_asimi):
        raise OSError("ağ yok")

    assert td.guncellemeleri_al("JETONDEGERI123", 5, _cagir=iyi) == [{"update_id": 5}]
    # TUR 2 (I-1): HATA ile "güncelleme yok" AYRI — hata `None`, boş liste yalnız "yok" demek.
    assert td.guncellemeleri_al("JETONDEGERI123", 5, _cagir=kotu) is None
    olay = [e for e in obs.recent(20) if e.get("event") == "telegram_yoklama_hatasi"]
    assert olay and "JETONDEGERI123" not in str(olay[-1])
    assert td.guncellemeleri_al("JETONDEGERI123", 5,
                                _cagir=lambda u, g, z: {"ok": True, "result": []}) == []


def test_guncellemeleri_al_ok_false_hata_sayilir_ve_sessiz_degil(sandbox_state):
    # HTTP 200 gövdesinde `ok: false` (ör. 409 başka tüketici, 401 jeton iptali): sessiz boş tur
    # DEĞİL — `None` + olay (hata kodu taşınır, açıklama metni taşınmaz).
    d = td.guncellemeleri_al("JETONDEGERI123", 5, _cagir=lambda u, g, z: {
        "ok": False, "error_code": 409, "description": "Conflict: terminated by other getUpdates"})
    assert d is None
    olay = [e for e in obs.recent(20) if e.get("event") == "telegram_yoklama_hatasi"]
    assert olay and olay[-1].get("error_code") == 409


def test_guncellemeleri_al_jeton_hata_metninde_olsa_da_olaya_dusmez(sandbox_state):
    # Minor-1 (Tur 2'de Önemli'ye yükseltildi): istisna METNİ jetonu taşıyabilir (URL yolu). Olay
    # yalnız sınıf adını taşımalı — `str(e)` basan bir değişiklik bu çiviyi kırmızıya çevirir.
    def kotu(url, govde, zaman_asimi):
        raise OSError("https://api.telegram.org/botJETONDEGERI123/getUpdates: 409")

    assert td.guncellemeleri_al("JETONDEGERI123", 5, _cagir=kotu) is None
    olaylar = obs.recent(50)
    assert any(e.get("event") == "telegram_yoklama_hatasi" for e in olaylar)
    assert all("JETONDEGERI123" not in str(e) for e in olaylar)


def _sirlar(monkeypatch):
    monkeypatch.setattr(td.secrets, "get", lambda ad: {"TELEGRAM_BOT_TOKEN": "J" * 20,
                                                        "TELEGRAM_CHAT_ID": YETKILI}.get(ad))


def _sirali_cagir(sonuclar, ofsetler=None):
    """Her yoklamada sıradaki sonucu verir: istisna örneği → fırlatılır, liste → `ok: True` gövdesi."""
    it = iter(sonuclar)

    def cagir(url, govde, zaman_asimi):
        if ofsetler is not None:
            ofsetler.append(govde["offset"])
        s = next(it)
        if isinstance(s, BaseException):
            raise s
        return {"ok": True, "result": s}
    return cagir


def test_dongu_ofseti_ilerletir_ve_kalici(sandbox_state, monkeypatch):
    monkeypatch.setattr(td.secrets, "get", lambda ad: {"TELEGRAM_BOT_TOKEN": "J" * 20,
                                                        "TELEGRAM_CHAT_ID": YETKILI}.get(ad))
    turlar = iter([[{"update_id": 10, "message": _m("merhaba")}], []])
    td.dongu(bota_sor=lambda *a: "ok", tur_sayisi=2, _cagir=lambda u, g, z: {"ok": True, "result": next(turlar)},
             gonder=lambda t, r: True)
    from meridian import store
    assert store.read_json("telegram_ofset.json", {}).get("ofset") == 11


def test_dongu_hata_turlarinda_ussel_geri_cekilir_ve_60ta_tavanlanir(sandbox_state, monkeypatch):
    # I-1: art arda hata → 1, 2, 4, … sn, tavan 60. Uyku enjekte; gerçek bekleme YOK.
    _sirlar(monkeypatch)
    uykular = []
    td.dongu(bota_sor=lambda *a: "ok", tur_sayisi=8, _cagir=_sirali_cagir([OSError("x")] * 8),
             gonder=lambda t, r: True, _uyku=uykular.append)
    assert uykular == [1, 2, 4, 8, 16, 32, 60, 60]


def test_dongu_basarili_tur_geri_cekilme_sayacini_sifirlar(sandbox_state, monkeypatch):
    _sirlar(monkeypatch)
    uykular = []
    td.dongu(bota_sor=lambda *a: "ok", tur_sayisi=4,
             _cagir=_sirali_cagir([OSError("x"), OSError("x"), [], OSError("x")]),
             gonder=lambda t, r: True, _uyku=uykular.append)
    assert uykular == [1, 2, 1]


def test_dongu_zehirli_guncelleme_donguyu_oldurmez_ofset_ikisini_de_gecer(sandbox_state, monkeypatch):
    # I-2: ilk güncellemede kadro okunamıyor (ValueError) → olay, ofset YİNE ilerler (en-çok-bir-kez);
    # ikinci güncelleme normal işlenir.
    _sirlar(monkeypatch)
    gercek, sayac = kadro.kadro_yukle, {"n": 0}

    def bozuk_sonra_saglam(yol=None):
        sayac["n"] += 1
        if sayac["n"] == 1:
            raise ValueError("kadro: bozuk")
        return gercek(yol)

    monkeypatch.setattr(td._kadro, "kadro_yukle", bozuk_sonra_saglam)
    cagrilar = []
    td.dongu(bota_sor=lambda bot, m, k, o: cagrilar.append((bot, m)) or "ok", tur_sayisi=1,
             _cagir=_sirali_cagir([[{"update_id": 10, "message": _m("merhaba")},
                                    {"update_id": 11, "message": _m("@bekci durum?")}]]),
             gonder=lambda t, r: True, _uyku=lambda s: None)
    assert cagrilar == [("bekci", "durum?")]
    from meridian import store
    assert store.read_json("telegram_ofset.json", {}).get("ofset") == 12
    olay = [e for e in obs.recent(50) if e.get("event") == "telegram_isle_hatasi"]
    assert olay and olay[-1].get("sinif") == "ValueError" and "bozuk" not in str(olay[-1])


def test_dongu_update_id_siz_guncelleme_atlanir(sandbox_state, monkeypatch):
    _sirlar(monkeypatch)
    cagrilar = []
    td.dongu(bota_sor=lambda bot, m, k, o: cagrilar.append(bot) or "ok", tur_sayisi=1,
             _cagir=_sirali_cagir([[{"message": _m("merhaba")},
                                    {"update_id": 20, "message": _m("merhaba")}]]),
             gonder=lambda t, r: True, _uyku=lambda s: None)
    assert cagrilar == ["sef"]
    from meridian import store
    assert store.read_json("telegram_ofset.json", {}).get("ofset") == 21
    assert any(e.get("event") == "telegram_isle_hatasi" for e in obs.recent(50))


def test_dongu_ofset_yazilamazsa_bellekte_ilerler_ve_dongu_surer(sandbox_state, monkeypatch):
    _sirlar(monkeypatch)

    def yazamaz(ad, obj):
        raise OSError("salt-okur dosya sistemi")

    monkeypatch.setattr(td.store, "write_json", yazamaz)
    cagrilar, ofsetler = [], []
    td.dongu(bota_sor=lambda bot, m, k, o: cagrilar.append(bot) or "ok", tur_sayisi=2,
             _cagir=_sirali_cagir([[{"update_id": 30, "message": _m("merhaba")}], []], ofsetler),
             gonder=lambda t, r: True, _uyku=lambda s: None)
    assert cagrilar == ["sef"] and ofsetler == [0, 31]
    olay = [e for e in obs.recent(50) if e.get("event") == "telegram_ofset_yazim_hatasi"]
    assert olay and olay[-1].get("sinif") == "OSError"


def test_dongu_ofset_islemeden_once_kalici(sandbox_state, monkeypatch):
    # En-çok-bir-kez: ofset güncelleme İŞLENMEDEN önce diske iner — bot çağrısı sürerken süreç
    # ölürse (dağıtım restart'ı, OOM) aynı mesaj yeniden oynatılıp ikinci kez cevaplanmaz.
    _sirlar(monkeypatch)
    from meridian import store
    gorulen = []
    td.dongu(bota_sor=lambda *a: gorulen.append(store.read_json("telegram_ofset.json", {}).get("ofset"))
             or "ok", tur_sayisi=1, _cagir=_sirali_cagir([[{"update_id": 40, "message": _m("merhaba")}]]),
             gonder=lambda t, r: True, _uyku=lambda s: None)
    assert gorulen == [41]


def test_yanitla_reply_ve_scrub(monkeypatch):
    # ANAHTAR 64 ONALTILIK: `notify._SIR_DESENLERI`in "openrouter" deseni `sk-or-v1-[0-9a-f]{64}`
    # ister; brief'in 40 karakterlik örneği o desene UYMAZ ve maskelenmezdi (ölçüldü 2026-09-29).
    # Test scrub'a uydurulur, scrub genişletilmez (bedeli v467'de ölçülen ayrı karar).
    giden = {}
    monkeypatch.setattr(notify.secrets, "get", lambda ad: {"TELEGRAM_BOT_TOKEN": "T" * 20,
                                                            "TELEGRAM_CHAT_ID": YETKILI}.get(ad))
    monkeypatch.setattr(notify, "_post", lambda url, payload, timeout=8.0: giden.update(payload) or True)
    assert notify.yanitla("sk-or-v1-" + "a" * 64 + " selam", reply_to=7) is True
    assert giden["reply_to_message_id"] == 7 and "a" * 40 not in giden["text"]


def test_yanitla_teslim_edilemezse_kayda_gecer(sandbox_state, monkeypatch):
    # Arayüz sözleşmesi: başarısızlık `notify_delivery_failed` olayıdır ("bildirim gelmedi" ile
    # "zaten cevap yoktu" ayırt edilebilmeli). Kanal yapılandırılmamışsa gönderim denenmedi →
    # olay YOK, dönüş False.
    monkeypatch.setattr(notify.secrets, "get", lambda ad: {"TELEGRAM_BOT_TOKEN": "T" * 20,
                                                            "TELEGRAM_CHAT_ID": YETKILI}.get(ad))
    monkeypatch.setattr(notify, "_post", lambda url, payload, timeout=8.0: False)
    assert notify.yanitla("selam", reply_to=7) is False
    olay = [e for e in obs.recent(20) if e.get("event") == "notify_delivery_failed"]
    assert olay and olay[-1].get("channels") == "telegram" and olay[-1].get("yanit") is True
    monkeypatch.setattr(notify.secrets, "get", lambda ad: None)
    assert notify.yanitla("selam", reply_to=7) is False
    assert len([e for e in obs.recent(20) if e.get("event") == "notify_delivery_failed"]) == len(olay)


def test_send_davranisi_degismedi(monkeypatch):
    giden = {}
    monkeypatch.setattr(notify.secrets, "get", lambda ad: {"TELEGRAM_BOT_TOKEN": "T" * 20,
                                                            "TELEGRAM_CHAT_ID": YETKILI}.get(ad))
    monkeypatch.setattr(notify, "_post", lambda url, payload, timeout=8.0: giden.update(payload) or True)
    assert notify.send("x") is True and "reply_to_message_id" not in giden
