"""test_mcp_bot_alt_kume_v597.py — Parça 1b G1 Görev 1: araç sunucusunda BOT BAŞI araç alt kümesi.

NE ÇİVİLENİR (spec `docs/superpowers/specs/2026-09-29-konusan-bot-filosu-design.md` §3.2, plan
`docs/superpowers/plans/2026-09-30-konusan-filo-parca1b-g1-arac-alt-kumesi.md` Görev 1):
  * `--bot` verilmezse sunucu BUGÜNKÜ 6 getter'ı sunar (geri uyum) ve yazan araç SUNMAZ.
  * `--bot <ad>`: yalnız kadroda AKTİF bot açılır (yazım hatası / sırada / kilitli → süreç açılmaz,
    sessiz 6-getter YOK); `tools/list` yalnız o botun `araclar`ı ∩ kayıt; izinli olmayan araç
    `tools/call`da reddedilir ve KOŞMAZ (iki kat).
  * `bot_hafizasi_ara` yalnız `hafiza: hepsi` bota — kadro `araclar`ında olsa bile (iki kat).
  * Sohbet araçları `sohbet._arac_kos` üzerinden koşar: çit + scrub + tavan + şema (kopya YOK).
  * `oneri_yaz` MCP'den AYNI onay defterine yazar; panonun MEVCUT gelen kutusu ve MEVCUT onay ucu
    satırı tanır, onay MEVCUT icra fonksiyonunu çağırır (ikinci onay yolu YOK).

GÖREV 2 SINIRI (brief): `is_iste` ve `bot_hafizasi_ara` bu görevde KAYITSIZDIR; kadro onları listelerse
sunucu ATLAR. `_GOREV2_KAYITSIZ` Görev 2'de boşalır — o gün
`test_gorev2_araclari_henuz_kayitsiz_ve_atlanir` öter ve beklenen kümeler güncellenir.
"""
from __future__ import annotations

import dataclasses
import io
import json

import pytest

from meridian import kadro, sohbet, store
from meridian import mcp_server as ms

#: Görev 2'nin kaydedeceği iki araç — bu görevde kayıtta YOKLAR (brief'in beyanı; çivi aşağıda).
_GOREV2_KAYITSIZ = frozenset({"is_iste", "bot_hafizasi_ara"})

_ALTI_GETTER = sorted(["meridian_regime", "meridian_calibrations", "meridian_near_miss",
                       "meridian_cf_summary", "meridian_selfreview", "meridian_candidate_context"])

# Biçimi `notify.scrub`un `bearer` desenine uyan UYDURMA bir jeton (gerçek bir sır değildir).
_SAHTE_JETON = "abcdefghijklmnop0123456789XYZ"


def _rpc(bot, *mesajlar):
    giris = io.StringIO("".join(json.dumps(m) + "\n" for m in mesajlar))
    cikis = io.StringIO()
    ms.serve(giris, cikis, bot=bot)
    return [json.loads(s) for s in cikis.getvalue().splitlines() if s.strip()]


def _liste(bot):
    yanit = _rpc(bot, {"jsonrpc": "2.0", "id": 1, "method": "tools/list"})[0]
    return sorted(t["name"] for t in yanit["result"]["tools"])


def _cagri(bot, ad, args=None, mid=2):
    return _rpc(bot, {"jsonrpc": "2.0", "id": mid, "method": "tools/call",
                      "params": {"name": ad, "arguments": {} if args is None else args}})[0]


def _sohbet_onerileri() -> list[dict]:
    return [r for r in store.read_jsonl(sohbet.ONAY_DEFTERI)
            if isinstance(r, dict) and r.get("kaynak") == sohbet.CAGRI_KIND]


# =================================================================================================
# 1) ALT KÜME — tools/list
# =================================================================================================
def test_bot_yokken_bugunku_alti_getter(sandbox_state):
    assert _liste(None) == _ALTI_GETTER


def test_bot_yokken_yazan_arac_sunulmaz():
    """Geri-uyum kipi (varsayılan profil) YAZAN bir aracı ne listeler ne koşturur."""
    assert not set(ms.izinli_araclar(None)) & set(sohbet.YAZAN_ARACLAR)


def test_bekci_yalniz_kadro_araclari(sandbox_state):
    beklenen = sorted(set(kadro.bot_bul("bekci").araclar) - _GOREV2_KAYITSIZ)
    assert beklenen, "bekçinin kayıtlı aracı yok — çivi boş kümeyi eşitlerdi"
    assert _liste("bekci") == beklenen


@pytest.mark.parametrize("ad", [b.ad for b in kadro.aktif_botlar()])
def test_her_aktif_bot_kendi_kadro_kumesini_gorur(sandbox_state, ad):
    """Getter (`karne` → `meridian_selfreview`) ve sohbet aracı aynı kayıttan, kadro sırasıyla."""
    b = kadro.bot_bul(ad)
    beklenen = [a for a in b.araclar if a not in _GOREV2_KAYITSIZ]
    assert ms.izinli_araclar(ad) == beklenen
    assert _liste(ad) == sorted(beklenen)


def test_gorev2_araclari_henuz_kayitsiz_ve_atlanir(sandbox_state):
    kayit = ms.arac_kaydi()
    assert _GOREV2_KAYITSIZ <= set(kadro.PLANLI_ARACLAR)
    assert not _GOREV2_KAYITSIZ & set(kayit), (
        "Görev 2 bu araçları kaydetti — `_GOREV2_KAYITSIZ` kümesini ve beklenenleri güncelle")
    # kadro listeler (sef: ikisi de), sunucu kırılmadan atlar
    assert _GOREV2_KAYITSIZ <= set(kadro.bot_bul("sef").araclar)
    assert not _GOREV2_KAYITSIZ & set(ms.izinli_araclar("sef"))


def test_kayit_tek_kaynaktan_turer():
    """Kayıt = mevcut 6 getter ∪ `sohbet.ARACLAR` — sunucu kendi aracını İCAT ETMEZ, şemayı kopyalamaz."""
    kayit = ms.arac_kaydi()
    assert set(kayit) == {t["name"] for t in ms.TOOLS} | set(sohbet.ARACLAR)
    for ad, a in sohbet.ARACLAR.items():
        assert kayit[ad]["inputSchema"] is a.sema and kayit[ad]["description"] == a.aciklama
    for t in ms.TOOLS:
        assert kayit[t["name"]]["inputSchema"] is t["inputSchema"]


def test_kayitta_ad_cakismasi_sessizce_ezilmez(monkeypatch):
    monkeypatch.setitem(sohbet.ARACLAR, "meridian_regime", sohbet.ARACLAR["pano_ozeti"])
    with pytest.raises(ValueError, match="meridian_regime"):
        ms.arac_kaydi()


# =================================================================================================
# 2) bot_hafizasi_ara — yalnız `hafiza: hepsi` (iki kat)
# =================================================================================================
def _hafiza_duzenegi(monkeypatch, kosuldu: list):
    """Görev 2 öncesi: kayda bir `bot_hafizasi_ara` VEKİLİ, kadroya `araclar`ında onu taşıyan ama
    `hafiza: kendi` olan bir karne koyar — koşul ancak böyle ısırılabilir (gerçek karne onu listelemez)."""
    gercek_kayit = ms.arac_kaydi

    def kayit():
        k = gercek_kayit()
        k["bot_hafizasi_ara"] = {"name": "bot_hafizasi_ara", "description": "vekil",
                                 "inputSchema": {"type": "object", "properties": {}},
                                 "cagir": lambda a, b=None: kosuldu.append(1) or "vekil"}
        return k

    monkeypatch.setattr(ms, "arac_kaydi", kayit)
    gercek = kadro.kadro_yukle()
    karne = kadro.bot_bul("karne", gercek)
    assert karne.hafiza != "hepsi"
    sahte = tuple(dataclasses.replace(b, araclar=b.araclar + ("bot_hafizasi_ara",))
                  if b.ad == "karne" else b for b in gercek)
    monkeypatch.setattr(kadro, "kadro_yukle", lambda yol=None: sahte)
    return sahte


def test_bot_hafizasi_ara_yalniz_hepsi_hafizali_bota(sandbox_state, monkeypatch):
    kosuldu: list = []
    sahte = _hafiza_duzenegi(monkeypatch, kosuldu)
    assert kadro.bot_bul("sef", sahte).hafiza == "hepsi"
    assert "bot_hafizasi_ara" in ms.izinli_araclar("sef", kadro=sahte)
    assert "bot_hafizasi_ara" not in ms.izinli_araclar("karne", kadro=sahte)
    assert "bot_hafizasi_ara" in _liste("sef") and "bot_hafizasi_ara" not in _liste("karne")
    r = _cagri("karne", "bot_hafizasi_ara")["result"]
    assert r["isError"] is True and "izinli değil" in r["content"][0]["text"] and kosuldu == []


def test_hepsi_kosulu_bilinen_ada_bagli():
    """Koşulun taşıdığı ad bir yazım hatasıyla ayrışırsa iki kat SESSİZCE tek kata düşerdi."""
    assert set(ms.YALNIZ_HEPSI_HAFIZALI) <= set(kadro.PLANLI_ARACLAR) | set(ms.arac_kaydi())


# =================================================================================================
# 3) tools/call — izin kontrolü ÖNCE, araç KOŞMAZ
# =================================================================================================
def test_izinli_olmayan_arac_cagrisi_reddedilir_ve_kosmaz(sandbox_state, monkeypatch):
    kosuldu: list = []
    gercek_kayit = ms.arac_kaydi

    def kayit():
        k = gercek_kayit()
        k["meridian_regime"] = {**k["meridian_regime"],
                                "cagir": lambda a, b=None: kosuldu.append(1) or "x"}
        return k

    monkeypatch.setattr(ms, "arac_kaydi", kayit)
    r = _cagri("bekci", "meridian_regime")["result"]
    assert r["isError"] is True and "izinli değil" in r["content"][0]["text"] and kosuldu == []
    # pozitif kontrol: aynı vekil izinli olduğu kipte (bot yok) GERÇEKTEN koşar
    r2 = _cagri(None, "meridian_regime")["result"]
    assert r2["isError"] is False and kosuldu == [1]


def test_bot_yokken_kayitli_yazan_arac_cagrilamaz(sandbox_state):
    store.append_jsonl("trade_plans.jsonl", {"id": "P-2026-09-30-MU", "ticker": "MU",
                                             "date": "2026-09-30", "gate_verdict": "REVIEW"})
    r = _cagri(None, "oneri_yaz", {"tur": "not", "gerekce": "deneme"})["result"]
    assert r["isError"] is True and "izinli değil" in r["content"][0]["text"]
    assert _sohbet_onerileri() == []


def test_kayitsiz_arac_hala_bilinmeyen_arac_hatasi(sandbox_state):
    assert _cagri("bekci", "meridian_send_order")["error"]["code"] == -32602


def test_arac_adi_dizge_degilse_dongu_olmez(sandbox_state):
    yanitlar = _rpc("bekci",
                    {"jsonrpc": "2.0", "id": 5, "method": "tools/call",
                     "params": {"name": ["alarm_oku"], "arguments": {}}},
                    {"jsonrpc": "2.0", "id": 6, "method": "ping"})
    assert yanitlar[0]["error"]["code"] == -32602
    assert yanitlar[1]["id"] == 6 and yanitlar[1]["result"] == {}


# =================================================================================================
# 4) SOHBET ARAÇLARI — `_arac_kos` üzerinden: çit + scrub + tavan + şema
# =================================================================================================
def test_sohbet_araci_cit_ve_scrub_ile_doner(sandbox_state):
    r = _cagri("bekci", "alarm_oku", mid=3)["result"]
    assert r["content"][0]["text"].startswith("<<<VERI:alarm_oku>>>")
    assert r["isError"] is False


def test_sohbet_araci_ciktisi_suzulur_ve_kesilir(sandbox_state, monkeypatch):
    ham = f"Authorization: Bearer {_SAHTE_JETON}\n" + "satır\n" * (sohbet.ARAC_CIKTI_TAVANI // 3)
    monkeypatch.setitem(sohbet.ARACLAR, "alarm_oku",
                        sohbet.ARACLAR["alarm_oku"]._replace(cagir=lambda a, b=None: ham))
    metin = _cagri("bekci", "alarm_oku")["result"]["content"][0]["text"]
    assert metin.startswith("<<<VERI:alarm_oku>>>") and metin.rstrip().endswith(
        "<<<VERI-SON:alarm_oku>>>")
    assert _SAHTE_JETON not in metin and "Bearer ***" in metin
    assert "satır daha kesildi" in metin and len(metin) < len(ham)


def test_sohbet_sema_disi_cagri_hata_doner_ve_arac_kosmaz(sandbox_state, monkeypatch):
    kosuldu: list = []
    monkeypatch.setitem(sohbet.ARACLAR, "kart_oku", sohbet.ARACLAR["kart_oku"]._replace(
        cagir=lambda a, b=None: kosuldu.append(1) or "x"))
    r = _cagri("karne", "kart_oku", {})["result"]
    assert r["isError"] is True and "ŞEMA DIŞI" in r["content"][0]["text"] and kosuldu == []


def test_sohbet_araci_istisnasi_donguyu_oldurmez(sandbox_state, monkeypatch):
    def patla(a, b=None):
        raise RuntimeError("patla")
    monkeypatch.setitem(sohbet.ARACLAR, "alarm_oku",
                        sohbet.ARACLAR["alarm_oku"]._replace(cagir=patla))
    yanitlar = _rpc("bekci",
                    {"jsonrpc": "2.0", "id": 7, "method": "tools/call",
                     "params": {"name": "alarm_oku", "arguments": {}}},
                    {"jsonrpc": "2.0", "id": 8, "method": "ping"})
    r = yanitlar[0]["result"]
    assert r["isError"] is True
    assert r["content"][0]["text"].startswith("<<<VERI:alarm_oku>>>") and "patla" in r["content"][0]["text"]
    assert yanitlar[1]["id"] == 8 and yanitlar[1]["result"] == {}


# =================================================================================================
# 5) oneri_yaz — AYNI onay defteri, MEVCUT onay akışı (ikinci onay yolu YOK)
# =================================================================================================
@pytest.fixture
def istemci(sandbox_state, monkeypatch):
    from fastapi.testclient import TestClient
    from meridian import api, config
    monkeypatch.setattr(api, "DASH_TOKEN", None)
    gercek = dict(config.limits())
    monkeypatch.setattr(config, "limits", lambda: {**gercek, "autonomy_level": 0})
    return TestClient(api.app)


def test_oneri_yaz_sohbet_kaydindaki_govdeden_gecer(sandbox_state, monkeypatch):
    """MCP `oneri_yaz` ikinci bir yazıcı DEĞİLDİR: `sohbet.ARACLAR`daki gövdeyi, `mcp:<bot>` bağlamıyla çağırır."""
    goruldu: list = []
    monkeypatch.setitem(sohbet.ARACLAR, "oneri_yaz", sohbet.ARACLAR["oneri_yaz"]._replace(
        cagir=lambda a, b=None: goruldu.append((a, dict(b or {}))) or "vekil"))
    r = _cagri("SEF", "oneri_yaz", {"tur": "not", "gerekce": "g"})["result"]
    assert r["isError"] is False
    assert goruldu == [({"tur": "not", "gerekce": "g"}, {"oturum": "mcp:sef"})]


def test_oneri_yaz_mcpden_ayni_onay_defterine_ve_mevcut_onay_yoluna(istemci, monkeypatch):
    from meridian import api
    from meridian import loop as _loop
    plan = "P-2026-09-30-MU"
    store.append_jsonl("trade_plans.jsonl", {"id": plan, "ticker": "MU", "date": "2026-09-30",
                                             "gate_verdict": "REVIEW"})
    r = _cagri("sef", "oneri_yaz", {"tur": "plan_onayi", "hedef": plan,
                                    "gerekce": "operatör baksın"})["result"]
    assert r["isError"] is False and r["content"][0]["text"].startswith("<<<VERI:oneri_yaz>>>")

    satirlar = _sohbet_onerileri()
    assert len(satirlar) == 1
    oid = satirlar[0]["id"]
    # api'nin öneri satırını tanıdığı ÜÇ koşul: `decision` yok · kaynak == CAGRI_KIND · kimlik biçimi
    assert "decision" not in satirlar[0] and satirlar[0]["kaynak"] == sohbet.CAGRI_KIND
    assert sohbet.oneri_kimligi_mi(oid) and sohbet.oneri_satiri(oid) == satirlar[0]
    assert satirlar[0]["oturum"] == "mcp:sef" and satirlar[0]["durum"] == "bekliyor"
    assert oid in r["content"][0]["text"]

    t = api._defter_tarama()
    assert oid not in (t["kararlar"] or {}) and t["atfedilemeyen"] == 0

    kutu = istemci.get("/api/approvals").json()["inbox"]
    oge = next((o for o in kutu if o.get("id") == oid), None)
    assert oge is not None and oge["type"] == "sohbet_onerisi", kutu
    assert oge["oturum"] == "mcp:sef" and oge["hedef"] == plan

    cagrilar: list = []
    monkeypatch.setattr(_loop, "operator_onay_ver",
                        lambda plan_id, **kw: cagrilar.append(plan_id) or {"ok": True})
    y = istemci.post(f"/api/approvals/{oid}", json={"decision": "approve", "reason": "uygun"})
    assert y.status_code == 200, y.text
    assert cagrilar == [plan] and y.json()["icra"]["ok"] is True
    kutu2 = istemci.get("/api/approvals").json()["inbox"]
    assert not [o for o in kutu2 if o.get("id") == oid], "karar verilmiş öneri hâlâ bekliyor"


def test_oneri_yaz_hedef_kapisi_mcpden_de_isler(sandbox_state):
    """Enjeksiyon savunmasının davranışsal yarısı MCP'de de: var olmayan plana öneri YAZILMAZ."""
    r = _cagri("sef", "oneri_yaz", {"tur": "plan_onayi", "hedef": "P-YOK",
                                    "gerekce": "g"})["result"]
    assert r["isError"] is True and "YAZILMADI" in r["content"][0]["text"]
    assert _sohbet_onerileri() == []


# =================================================================================================
# 6) AÇILIŞ — kadro dışı / pasif bot açılmaz
# =================================================================================================
def test_kadro_disi_ya_da_pasif_botla_acilmaz(capsys):
    assert ms.main(["--bot", "kod"]) != 0 and "kod" in capsys.readouterr().err
    assert ms.main(["--bot", "yokboyle"]) != 0 and "yokboyle" in capsys.readouterr().err
    assert ms.main(["--bot", "hipotez"]) != 0 and "hipotez" in capsys.readouterr().err


@pytest.mark.parametrize("ad", ["kod", "yokboyle", "hipotez", ""])
def test_serve_de_pasif_botla_satir_okumadan_reddeder(sandbox_state, ad):
    giris = io.StringIO('{"jsonrpc": "2.0", "id": 1, "method": "ping"}\n')
    cikis = io.StringIO()
    with pytest.raises(ms.BotAcilamaz):
        ms.serve(giris, cikis, bot=ad)
    assert cikis.getvalue() == "" and giris.tell() == 0


def test_main_gecerli_botu_ve_bot_yoklugunu_serve_e_iletir(monkeypatch):
    goruldu: list = []
    monkeypatch.setattr(ms, "serve", lambda stdin=None, stdout=None, bot=None: goruldu.append(bot))
    assert ms.main(["--bot", "bekci"]) == 0 and ms.main([]) == 0
    assert goruldu == ["bekci", None]
