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

GÖREV 2 (2026-09-30): Görev 1'in "iki planlı araç henüz kayıtsız" sabitlemesi bilinçli olarak yeni
sözleşmeye çevrildi — `kadro.PLANLI_ARACLAR` kayıtta, aktif botların listelediği HER ad kayıtta, ikisi
pano sohbetinin kaydına GİRMEZ (`test_planli_araclar_kayitli_ve_pano_sohbetine_girmez`). Bölüm 8:
  * `is_iste` MCP'den kanal BİLİNMEDEN çağrılır → defterde `kanal: null` + `cagiran: "mcp:<bot>"`; kanal
    ve kimlik MODELDEN gelemez (şema dışı); tavan kanallar arasında ortaktır; ret (tavan / bilinmeyen iş)
    `isError` taşır — model "tetiklendi" diye okuyamasın.
  * `bot_hafizasi_ara` hedef botun `bot-<ad>` bankasında SALT-OKUR recall (sahte `_cagir`, ağ yok): tek
    POST, çitli + scrub'lı; hedef kadroda aktif değilse HTTP'siz ret; diske yazmaz.
  * Rol-1 kararı: `hafiza_ara` alt süreci MCP'nin stdin borusunu (JSON-RPC girdisi) miras almaz.

DAL SONU TURU (2026-09-30, inceleme I-1 · M-1 · M-5) — Bölüm 9:
  * I-1: `--bot` kipinde getter çıktısı da sohbet araçlarıyla AYNI zarftan geçer (çit + scrub + tavan +
    şema); `--bot`SUZ kip BAYT-ÖZDEŞ ham kalır. Her aktif bot × her izinli araç: metin çitle başlar.
  * M-1: nesne olmayan mesaj / `params` → -32600 (id varsa id, yoksa null), iç hata → -32603; döngü ÖLMEZ.
  * M-5: GERÇEK alt süreç (`python -m meridian.mcp_server --bot …`, `MERIDIAN_ROOT` = sandbox kökü): stdout
    yalnız JSON-RPC, obs satırı stderr'de, getter çitli; gerçek `state/`e yazım yok.
"""
from __future__ import annotations

import dataclasses
import hashlib
import io
import json
import os
import pathlib
import shutil
import subprocess
import sys

import pytest

from meridian import bot_hafiza, config, is_istek, kadro, secrets, sohbet, store
from meridian import mcp_server as ms

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
    yazanlar = set(sohbet.YAZAN_ARACLAR) | set(ms.MCP_YAZAN_ARACLAR)
    assert {"oneri_yaz", "is_iste"} <= yazanlar
    assert not set(ms.izinli_araclar(None)) & yazanlar


def test_bekci_yalniz_kadro_araclari(sandbox_state):
    beklenen = sorted(kadro.bot_bul("bekci").araclar)
    assert "is_iste" in beklenen, "bekçi kadroda is_iste taşıyor — Görev 2 onu kayda aldı, beklenen düşürmez"
    assert _liste("bekci") == beklenen


@pytest.mark.parametrize("ad", [b.ad for b in kadro.aktif_botlar()])
def test_her_aktif_bot_kendi_kadro_kumesini_gorur(sandbox_state, ad):
    """Getter (`karne` → `meridian_selfreview`), sohbet aracı ve MCP'ye özgü araç aynı kayıttan, kadro sırasıyla."""
    b = kadro.bot_bul(ad)
    # Gerçek kadroda `bot_hafizasi_ara` yalnız `hafiza: hepsi` botta listeli; öyle olmasa beklenen kadronun TAMAMI olmazdı.
    assert "bot_hafizasi_ara" not in b.araclar or b.hafiza == "hepsi"
    assert ms.izinli_araclar(ad) == list(b.araclar)
    assert _liste(ad) == sorted(b.araclar)


def test_planli_araclar_kayitli_ve_pano_sohbetine_girmez(sandbox_state):
    """Görev 1'in "henüz kayıtsız" pin'inin YERİNE: kadronun planladığı iki araç kayıtta; aktif botların
    listelediği HER ad kayıtta (atlanan yok); ikisi pano sohbetinin kaydına GİRMEZ (sohbetin beyaz listesi
    donuk — bu araçlar MCP sunucusuna özgüdür)."""
    kayit = ms.arac_kaydi()
    assert set(ms._mcp_araclari()) == set(kadro.PLANLI_ARACLAR)
    assert set(kadro.PLANLI_ARACLAR) <= set(kayit)
    assert not set(kadro.PLANLI_ARACLAR) & (set(sohbet.ARACLAR) | set(sohbet.BEYAZ_LISTE))
    for b in kadro.aktif_botlar():
        assert set(b.araclar) <= set(kayit), (b.ad, set(b.araclar) - set(kayit))
    assert set(kadro.PLANLI_ARACLAR) <= set(ms.izinli_araclar("sef"))


def test_kayit_tek_kaynaktan_turer():
    """Kayıt = 6 getter ∪ `sohbet.ARACLAR` ∪ MCP'ye özgü iki araç — şema/açıklama KOPYALANMAZ, aynı nesnedir."""
    kayit = ms.arac_kaydi()
    mcp = ms._mcp_araclari()
    assert set(kayit) == {t["name"] for t in ms.TOOLS} | set(sohbet.ARACLAR) | set(mcp)
    for kaynak in (sohbet.ARACLAR, mcp):
        for ad, a in kaynak.items():
            assert kayit[ad]["inputSchema"] is a.sema and kayit[ad]["description"] == a.aciklama
    for t in ms.TOOLS:
        assert kayit[t["name"]]["inputSchema"] is t["inputSchema"]
    # MCP'ye özgü şemalar modül sabitidir: her türetim AYNI nesneyi görür (kayıt ↔ çağrı anı doğrulaması ayrışamaz)
    assert all(ms._mcp_araclari()[ad].sema is mcp[ad].sema for ad in mcp)


def test_kayitta_ad_cakismasi_sessizce_ezilmez(monkeypatch):
    monkeypatch.setitem(sohbet.ARACLAR, "meridian_regime", sohbet.ARACLAR["pano_ozeti"])
    with pytest.raises(ValueError, match="meridian_regime"):
        ms.arac_kaydi()


def test_mcp_araci_sohbet_araciyla_cakisirsa_sessizce_ezilmez(monkeypatch):
    monkeypatch.setitem(sohbet.ARACLAR, "is_iste", sohbet.ARACLAR["pano_ozeti"])
    with pytest.raises(ValueError, match="is_iste"):
        ms.arac_kaydi()


# =================================================================================================
# 2) bot_hafizasi_ara — yalnız `hafiza: hepsi` (iki kat)
# =================================================================================================
class _HafizaCasusu:
    """Sahte `_cagir(yontem, url, govde, basliklar, zaman_asimi)` — AĞ YOK. Her çağrıyı kaydeder; recall'a
    verilen cevabı döner, `hata` verilmişse onu fırlatır. Salt-okur araçtan recall DIŞI çağrı beklenmez."""

    def __init__(self, recall=None, hata: Exception | None = None):
        self.cagrilar: list = []
        self.recall = {"results": []} if recall is None else recall
        self.hata = hata

    def __call__(self, yontem, url, govde, basliklar, zaman_asimi):
        self.cagrilar.append((yontem, url, govde))
        if self.hata is not None:
            raise self.hata
        if yontem == "POST" and url.endswith("/memories/recall"):
            return self.recall
        raise AssertionError(f"salt-okur araçtan beklenmeyen çağrı: {yontem} {url}")


def _hafiza_bagla(monkeypatch, casus: _HafizaCasusu) -> None:
    """Araç gövdesinin kurduğu `bot_hafiza.HindsightHafiza`yı sahte `_cagir` + uydurma anahtarla kurdurur
    (gerçek credential OKUNMAZ, istek atılmaz)."""
    gercek = bot_hafiza.HindsightHafiza
    monkeypatch.setattr(bot_hafiza, "HindsightHafiza",
                        lambda *a, **kw: gercek(_cagir=casus, _anahtar=lambda: "K" * 32))


def _hafiza_duzenegi(monkeypatch, casus: _HafizaCasusu):
    """Kadroya `araclar`ında `bot_hafizasi_ara` taşıyan ama `hafiza: kendi` olan bir karne koyar — `hafiza`
    koşulu ancak böyle ısırılabilir (gerçek karne o aracı listelemez)."""
    _hafiza_bagla(monkeypatch, casus)
    gercek = kadro.kadro_yukle()
    karne = kadro.bot_bul("karne", gercek)
    assert karne.hafiza != "hepsi"
    sahte = tuple(dataclasses.replace(b, araclar=b.araclar + ("bot_hafizasi_ara",))
                  if b.ad == "karne" else b for b in gercek)
    monkeypatch.setattr(kadro, "kadro_yukle", lambda yol=None: sahte)
    return sahte


def test_bot_hafizasi_ara_yalniz_hepsi_hafizali_bota(sandbox_state, monkeypatch):
    casus = _HafizaCasusu()
    sahte = _hafiza_duzenegi(monkeypatch, casus)
    assert kadro.bot_bul("sef", sahte).hafiza == "hepsi"
    assert "bot_hafizasi_ara" in ms.izinli_araclar("sef", kadro=sahte)
    assert "bot_hafizasi_ara" not in ms.izinli_araclar("karne", kadro=sahte)
    assert "bot_hafizasi_ara" in _liste("sef") and "bot_hafizasi_ara" not in _liste("karne")
    args = {"bot": "bekci", "soru": "x"}
    r = _cagri("karne", "bot_hafizasi_ara", args)["result"]
    assert r["isError"] is True and "izinli değil" in r["content"][0]["text"] and casus.cagrilar == []
    # pozitif kontrol: aynı çağrı `hafiza: hepsi` bottan GERÇEKTEN koşar
    r2 = _cagri("sef", "bot_hafizasi_ara", args)["result"]
    assert r2["isError"] is False and len(casus.cagrilar) == 1


@pytest.mark.parametrize("bot", ["karne", "bekci"])
def test_bot_hafizasi_ara_gercek_kadroda_hepsi_olmayan_sunucudan_izinli_degil(sandbox_state, monkeypatch, bot):
    casus = _HafizaCasusu()
    _hafiza_bagla(monkeypatch, casus)
    assert "bot_hafizasi_ara" not in _liste(bot)
    r = _cagri(bot, "bot_hafizasi_ara", {"bot": "sef", "soru": "x"})["result"]
    assert r["isError"] is True and "izinli değil" in r["content"][0]["text"] and casus.cagrilar == []


def test_hepsi_kosulu_bilinen_ada_bagli():
    """Koşulun taşıdığı ad bir yazım hatasıyla ayrışırsa iki kat SESSİZCE tek kata düşerdi — ad KAYITTA olmalı."""
    assert set(ms.YALNIZ_HEPSI_HAFIZALI) <= set(ms.arac_kaydi())


# =================================================================================================
# 3) tools/call — izin kontrolü ÖNCE, araç KOŞMAZ
# =================================================================================================
def test_izinli_olmayan_arac_cagrisi_reddedilir_ve_kosmaz(sandbox_state, monkeypatch):
    # Vekil getter'ın `TOOLS` kaydına konur: iki kip de (bot yok = yalnız getter kaydı, bot = tam kayıt)
    # getter'ı çağrı anında oradan okur, yani aynı vekil iki kipte de görünür.
    kosuldu: list = []
    monkeypatch.setitem(ms._BY_NAME["meridian_regime"], "fn", lambda a: kosuldu.append(1) or {})
    r = _cagri("bekci", "meridian_regime")["result"]
    assert r["isError"] is True and "izinli değil" in r["content"][0]["text"] and kosuldu == []
    # pozitif kontrol: aynı vekil izinli olduğu kipte (bot yok) GERÇEKTEN koşar
    r2 = _cagri(None, "meridian_regime")["result"]
    assert r2["isError"] is False and kosuldu == [1]


def test_bot_yokken_yazan_arac_kayitta_yok_ve_cagrilamaz(sandbox_state):
    """`--bot`suz kip sohbet araçlarını KAYDA BİLE almaz (Tur 2: `sohbet` ithal edilmez) — yazan araç
    bugün G1 öncesindeki gibi "bilinmeyen araç" alır ve deftere satır düşmez."""
    store.append_jsonl("trade_plans.jsonl", {"id": "P-2026-09-30-MU", "ticker": "MU",
                                             "date": "2026-09-30", "gate_verdict": "REVIEW"})
    yanit = _cagri(None, "oneri_yaz", {"tur": "not", "gerekce": "deneme"})
    assert "result" not in yanit and yanit["error"]["code"] == -32602
    assert _sohbet_onerileri() == []


def test_handle_tam_kayitla_izin_kumesi_verilmezse_yine_alti_getter(sandbox_state):
    """Savunma derinliği: `_handle`e TAM kayıt verilip izin kümesi verilmezse bot yok sayılır ve
    yalnız altı getter izinlidir — yazan araç listelenmez, koşmaz."""
    kayit = ms.arac_kaydi()
    liste = ms._handle({"jsonrpc": "2.0", "id": 1, "method": "tools/list"}, kayit)
    assert sorted(t["name"] for t in liste["result"]["tools"]) == _ALTI_GETTER
    r = ms._handle({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                    "params": {"name": "oneri_yaz", "arguments": {"tur": "not", "gerekce": "g"}}},
                   kayit)["result"]
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


# =================================================================================================
# 7) TUR 2 — stdio protokol akışı yalnız JSON-RPC (I-1) · `--bot`suz yol sohbet/kadro ithal etmez (M-1)
# =================================================================================================
def _protokol_satirlari(out: str) -> list[dict]:
    """Gerçek stdout'taki HER boş olmayan satır geçerli bir JSON-RPC 2.0 mesajı olmalı."""
    satirlar = [s for s in out.splitlines() if s.strip()]
    ayrik = [json.loads(s) for s in satirlar]
    assert all(isinstance(m, dict) and m.get("jsonrpc") == "2.0" for m in ayrik), satirlar
    return ayrik


def test_oneri_yaz_obs_satiri_stdio_protokol_akisina_karismaz(sandbox_state, capsys):
    """`obs._emit` olayı stdout'a basar; `serve` gerçek stdout'u protokol akışı olarak kullanırken
    başarılı `oneri_yaz`ın `sohbet_oneri_yazildi` satırı o akışa KARIŞMAMALI (stderr'e gider)."""
    giris = io.StringIO("".join(json.dumps(m) + "\n" for m in (
        {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
         "params": {"name": "oneri_yaz", "arguments": {"tur": "not", "gerekce": "deneme"}}},
        {"jsonrpc": "2.0", "id": 2, "method": "ping"})))
    ms.serve(giris, None, bot="sef")
    out, err = capsys.readouterr()
    yanitlar = _protokol_satirlari(out)
    assert [y["id"] for y in yanitlar] == [1, 2] and yanitlar[0]["result"]["isError"] is False
    # pozitif kontrol: olay GERÇEKTEN basıldı — yalnız doğru akışa
    assert len(_sohbet_onerileri()) == 1
    assert "sohbet_oneri_yazildi" in err and "sohbet_oneri_yazildi" not in out


def test_getter_obs_satiri_stdio_protokol_akisina_karismaz(sandbox_state, capsys, monkeypatch):
    """Aynı sınıf getter'larda da var (`analytics` yolları `obs.warn` çağırabilir)."""
    from meridian import obs
    monkeypatch.setitem(ms._BY_NAME["meridian_regime"], "fn",
                        lambda a: obs.warn("mcp_getter_civi_olayi", detail="v597") and {"ok": 1})
    giris = io.StringIO(json.dumps({"jsonrpc": "2.0", "id": 4, "method": "tools/call",
                                    "params": {"name": "meridian_regime", "arguments": {}}}) + "\n")
    ms.serve(giris, None)
    out, err = capsys.readouterr()
    yanitlar = _protokol_satirlari(out)
    assert len(yanitlar) == 1 and yanitlar[0]["result"]["isError"] is False
    assert "mcp_getter_civi_olayi" in err and "mcp_getter_civi_olayi" not in out


def _taze_sunucu_ithal_kilitli(monkeypatch):
    """`meridian.sohbet`, `meridian.kadro`, `meridian.is_istek` ve `meridian.bot_hafiza` İTHALİ PATLARKEN
    `mcp_server`ı TAZE içe aktarır (son ikisi Görev 2: MCP'ye özgü araçların gövdeleri de yalnız `--bot` yolunda).

    Paket özniteliği silinir (yoksa `from . import sohbet` modüle hiç sormadan özniteliği döndürür) ve
    `sys.modules` girdisi `None` yapılır (ithal `ImportError` verir). Asıl modül nesnesine dokunulmaz:
    `meridian.mcp_server` girdisi ve özniteliği test sonunda monkeypatch ile geri gelir."""
    import importlib
    import sys

    import meridian
    for ad in ("sohbet", "kadro", "is_istek", "bot_hafiza"):
        monkeypatch.delattr(meridian, ad, raising=False)
        monkeypatch.setitem(sys.modules, f"meridian.{ad}", None)
    monkeypatch.delitem(sys.modules, "meridian.mcp_server", raising=False)
    monkeypatch.delattr(meridian, "mcp_server", raising=False)
    return importlib.import_module("meridian.mcp_server")


def test_botsuz_yol_sohbet_ve_kadro_ithal_etmeden_calisir(sandbox_state, monkeypatch):
    """Varsayılan (`--bot`suz, altı getter) yol `sohbet`/`kadro` arızasıyla (bozuk `SOHBET_*` ortamı,
    ithal hatası) ÖLMEMELİ — G1 öncesinde bu modüllere hiç bağlı değildi."""
    taze = _taze_sunucu_ithal_kilitli(monkeypatch)
    assert taze is not ms
    giris = io.StringIO("".join(json.dumps(m) + "\n" for m in (
        {"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/call",
         "params": {"name": "meridian_regime", "arguments": {}}},
        {"jsonrpc": "2.0", "id": 3, "method": "tools/call",
         "params": {"name": "oneri_yaz", "arguments": {"tur": "not", "gerekce": "g"}}})))
    cikis = io.StringIO()
    taze.serve(giris, cikis)
    yanitlar = [json.loads(s) for s in cikis.getvalue().splitlines() if s.strip()]
    assert sorted(t["name"] for t in yanitlar[0]["result"]["tools"]) == _ALTI_GETTER
    assert yanitlar[1]["result"]["isError"] is False
    assert yanitlar[2]["error"]["code"] == -32602
    assert taze.izinli_araclar(None) == [t["name"] for t in taze.TOOLS]
    legacy = taze._handle({"jsonrpc": "2.0", "id": 9, "method": "tools/list"})
    assert sorted(t["name"] for t in legacy["result"]["tools"]) == _ALTI_GETTER
    # pozitif kontrol: kilit GERÇEKTEN kilitli — bot kipi ve tam kayıt ithali patlatır (fail-closed)
    with pytest.raises(ImportError):
        taze.arac_kaydi()
    with pytest.raises(ImportError):
        taze.serve(io.StringIO(""), io.StringIO(), bot="sef")


# =================================================================================================
# 8) GÖREV 2 — `is_iste` (kanal null + cagiran) · `bot_hafizasi_ara` (salt-okur recall) · alt süreç stdin
# =================================================================================================
def _cit_ici(metin: str, ad: str) -> str:
    """VERİ çitinin İÇİ — çit yoksa (çıktı çitsiz modele gidiyorsa) iddia düşer."""
    bas, son = f"<<<VERI:{ad}>>>\n", f"\n<<<VERI-SON:{ad}>>>"
    assert metin.startswith(bas) and metin.endswith(son), metin[:120]
    return metin[len(bas):-len(son)]


def _is_defteri() -> list[dict]:
    return store.read_jsonl(is_istek.DEFTER)


def _anlik(kok) -> dict:
    return {str(p.relative_to(kok)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(kok.rglob("*")) if p.is_file()}


@pytest.mark.parametrize("bot,cagiran,is_adi,hedef", [("SEF", "mcp:sef", "brifing", "sef"),
                                                      ("bekci", "mcp:bekci", "karne", "karne"),
                                                      ("karne", "mcp:karne", "BEKÇİ", "bekci")])
def test_is_iste_mcpden_kanal_null_ve_cagiran_sunucunun_botu(sandbox_state, bot, cagiran, is_adi, hedef):
    r = _cagri(bot, "is_iste", {"ad": is_adi})["result"]
    ic = json.loads(_cit_ici(r["content"][0]["text"], "is_iste"))
    assert r["isError"] is False and ic["kabul"] is True and ic["bot"] == hedef and ic["neden"] == "kabul"
    (satir,) = _is_defteri()
    assert "kanal" in satir and satir["kanal"] is None, "kanal UYDURULMAZ — MCP'de bilinmiyor"
    assert satir["cagiran"] == cagiran and (satir["bot"], satir["neden"]) == (hedef, "kabul")
    govde = json.loads((config.STATE / is_istek.ISTEK_DIZINI / f"{hedef}.istek").read_text())
    assert govde["kanal"] is None and govde["bot"] == hedef


def test_is_iste_tavan_mcpden_de_isler_ve_kanallar_arasinda_ortak(sandbox_state):
    yanitlar = _rpc("sef", *({"jsonrpc": "2.0", "id": i, "method": "tools/call",
                              "params": {"name": "is_iste", "arguments": {"ad": "karne"}}} for i in (1, 2)))
    assert yanitlar[0]["result"]["isError"] is False
    r = yanitlar[1]["result"]
    ic = json.loads(_cit_ici(r["content"][0]["text"], "is_iste"))
    assert r["isError"] is True and (ic["kabul"], ic["neden"]) == (False, "tavan") and ic["sonraki_uygun"]
    assert len(_is_defteri()) == 1
    # Telegram'dan gelen kabul MCP isteğini de tavana sokar (tavanın hafızası bot başınadır, kanal başına değil)
    assert is_istek.is_iste("bekci", "telegram").kabul
    r2 = _cagri("sef", "is_iste", {"ad": "bekci"})["result"]
    assert r2["isError"] is True and json.loads(_cit_ici(r2["content"][0]["text"], "is_iste"))["neden"] == "tavan"
    assert [s["bot"] for s in _is_defteri()] == ["karne", "bekci"]


@pytest.mark.parametrize("ad", ["kod", "yokboyle", "../sef"])
def test_is_iste_bilinmeyen_is_reddedilir_ve_hicbir_sey_yazmaz(sandbox_state, ad):
    r = _cagri("sef", "is_iste", {"ad": ad})["result"]
    ic = json.loads(_cit_ici(r["content"][0]["text"], "is_iste"))
    assert r["isError"] is True and (ic["kabul"], ic["neden"]) == (False, "bilinmeyen_is")
    assert _is_defteri() == [] and not (config.STATE / is_istek.ISTEK_DIZINI).exists()


@pytest.mark.parametrize("args", [{"ad": "karne", "kanal": "telegram"}, {"ad": "karne", "cagiran": "mcp:karne"},
                                  {}, {"ad": 5}, {"ad": ""}])
def test_is_iste_kanal_ve_kimlik_modelden_gelemez(sandbox_state, args):
    """Kanal ve çağıran kimliği SUNUCUNUN bilgisidir: model şemaya alan ekleyip kendini Telegram ya da başka
    bir bot gibi gösteremez — şema dışı çağrı reddedilir, istek YAZILMAZ."""
    r = _cagri("sef", "is_iste", args)["result"]
    assert r["isError"] is True and "ŞEMA DIŞI" in r["content"][0]["text"]
    assert _is_defteri() == []


def test_bot_hafizasi_ara_hedef_bankaya_salt_okur_recall_citli_ve_scrubli(sandbox_state, monkeypatch):
    casus = _HafizaCasusu(recall={"results": [
        {"id": "m1", "text": f"bekçi notu: Authorization: Bearer {_SAHTE_JETON}",
         "mentioned_at": "2026-09-28T10:00:00Z"},
        {"id": "m2", "text": "ikinci not"}]})
    _hafiza_bagla(monkeypatch, casus)
    r = _cagri("sef", "bot_hafizasi_ara", {"bot": "BEKÇİ", "soru": "not"})["result"]
    assert r["isError"] is False
    ic = _cit_ici(r["content"][0]["text"], "bot_hafizasi_ara")
    assert [(y, u) for y, u, _ in casus.cagrilar] == [
        ("POST", f"{secrets.HAFIZA_TABAN_URL}/v1/default/banks/bot-bekci/memories/recall")]
    assert casus.cagrilar[0][2]["query"] == "not"
    assert _SAHTE_JETON not in ic and "Bearer ***" in ic
    assert "2026-09-28T10:00:00Z" in ic and "ikinci not" in ic and "(tarih yok)" in ic and "bot-bekci" in ic


def test_bot_hafizasi_ara_sonuc_yoksa_olculmus_sifir_der(sandbox_state, monkeypatch):
    casus = _HafizaCasusu(recall={"results": []})
    _hafiza_bagla(monkeypatch, casus)
    r = _cagri("sef", "bot_hafizasi_ara", {"bot": "karne", "soru": "hiç"})["result"]
    ic = _cit_ici(r["content"][0]["text"], "bot_hafizasi_ara")
    assert r["isError"] is False and "0 sonuç" in ic and "bot-karne" in ic and len(casus.cagrilar) == 1


@pytest.mark.parametrize("hedef", ["kod", "yokboyle", "../sef", "hipotez"])
def test_bot_hafizasi_ara_aktif_olmayan_hedef_http_oncesi_reddedilir(sandbox_state, monkeypatch, hedef):
    casus = _HafizaCasusu()
    _hafiza_bagla(monkeypatch, casus)
    r = _cagri("sef", "bot_hafizasi_ara", {"bot": hedef, "soru": "x"})["result"]
    assert r["isError"] is True and "aktif" in r["content"][0]["text"].lower() and casus.cagrilar == []


@pytest.mark.parametrize("args", [{"bot": "bekci"}, {"soru": "x"}, {"bot": "bekci", "soru": ""},
                                  {"bot": "bekci", "soru": "x", "k": 50}])
def test_bot_hafizasi_ara_sema_disi_http_yok(sandbox_state, monkeypatch, args):
    casus = _HafizaCasusu()
    _hafiza_bagla(monkeypatch, casus)
    r = _cagri("sef", "bot_hafizasi_ara", args)["result"]
    assert r["isError"] is True and "ŞEMA DIŞI" in r["content"][0]["text"] and casus.cagrilar == []


def test_bot_hafizasi_ara_hindsight_erisilemezse_hata_doner_ve_dongu_olmez(sandbox_state, monkeypatch):
    casus = _HafizaCasusu(hata=RuntimeError("hindsight URLError"))
    _hafiza_bagla(monkeypatch, casus)
    yanitlar = _rpc("sef",
                    {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                     "params": {"name": "bot_hafizasi_ara", "arguments": {"bot": "bekci", "soru": "x"}}},
                    {"jsonrpc": "2.0", "id": 2, "method": "ping"})
    r = yanitlar[0]["result"]
    ic = _cit_ici(r["content"][0]["text"], "bot_hafizasi_ara")
    assert r["isError"] is True and "RuntimeError" in ic
    assert yanitlar[1]["id"] == 2 and yanitlar[1]["result"] == {}


#: MCP'ye özgü YAZMAYAN her aracın örnek çağrısı. Yeni bir MCP aracı eklenip burada yoksa aşağıdaki çivi KeyError
#: ile öter — "yazmıyor" iddiası beyansız kalamaz.
_OKUYAN_ORNEK_ARGS = {"bot_hafizasi_ara": {"bot": "bekci", "soru": "x"}}


def test_mcp_ozgu_yazmayan_araclar_diske_yazmaz(sandbox_state, monkeypatch):
    casus = _HafizaCasusu(recall={"results": [{"id": "m1", "text": "not"}]})
    _hafiza_bagla(monkeypatch, casus)
    okuyanlar = sorted(set(ms._mcp_araclari()) - set(ms.MCP_YAZAN_ARACLAR))
    assert okuyanlar == ["bot_hafizasi_ara"]
    once = _anlik(sandbox_state)
    for ad in okuyanlar:
        assert _cagri("sef", ad, _OKUYAN_ORNEK_ARGS[ad])["result"]["isError"] is False
    assert _anlik(sandbox_state) == once, "yazmadığı beyan edilen araç diske yazdı"
    # pozitif kontrol: aynı ölçüm yazan aracı GERÇEKTEN görür
    assert _cagri("sef", "is_iste", {"ad": "karne"})["result"]["isError"] is False
    assert _anlik(sandbox_state) != once


def test_hafiza_ara_alt_sureci_mcp_stdin_borusunu_miras_almaz(sandbox_state, monkeypatch, tmp_path):
    """MCP stdio taşımasında sürecin stdin'i JSON-RPC GİRDİSİDİR; alt süreç onu miras alıp okursa protokol
    satırlarını TÜKETİR. `hafiza_ara` alt süreci `stdin=subprocess.DEVNULL` ile koşar (Rol-1 kararı)."""
    betik = tmp_path / "hafiza_ara.sh"
    betik.write_text("#!/bin/sh\n", encoding="utf-8")
    monkeypatch.setattr(sohbet, "_hafiza_betigi", lambda: str(betik))
    goruldu: list = []

    def sahte_run(argv, **kw):
        goruldu.append(kw)
        return subprocess.CompletedProcess(argv, 0, stdout="[1] not", stderr="")

    monkeypatch.setattr(sohbet.subprocess, "run", sahte_run)
    r = _cagri("sef", "hafiza_ara", {"soru": "x"})["result"]
    assert r["isError"] is False and len(goruldu) == 1
    assert "stdin" in goruldu[0] and goruldu[0]["stdin"] == subprocess.DEVNULL


# =================================================================================================
# 9) DAL SONU TURU — I-1 (getter zarfı `--bot` kipinde) · M-1 (nesne olmayan mesaj/params) · M-5 (gerçek alt süreç)
# =================================================================================================
def _selfreview_sahte_sirli() -> None:
    """`self_review.json`a biçimi `bearer` desenine uyan UYDURMA bir jeton koyar (gerçek sır değildir) — `attention`
    satırları dış hata metni taşıyabilir (inceleme I-1 senaryosu)."""
    store.write_json("self_review.json", {"generated": "2026-09-30",
                                          "attention": [f"watchdog: Authorization: Bearer {_SAHTE_JETON}"],
                                          "contradictions": [], "progress": {}})


def test_bot_kipinde_getter_citli_scrubli_botsuz_kip_bayt_ozdes(sandbox_state):
    _selfreview_sahte_sirli()
    r = _cagri("karne", "meridian_selfreview")["result"]
    ic = _cit_ici(r["content"][0]["text"], "meridian_selfreview")
    assert r["isError"] is False and _SAHTE_JETON not in ic and "Bearer ***" in ic
    assert json.loads(ic)["generated"] == "2026-09-30"
    # `--bot`suz kip (varsayılan Hermes profili, geri uyum): aynı getter BAYT-ÖZDEŞ ham JSON
    r0 = _cagri(None, "meridian_selfreview")["result"]
    assert r0["isError"] is False
    assert r0["content"][0]["text"] == json.dumps(ms._selfreview({}), ensure_ascii=False, default=str)


def test_bot_kipinde_getter_sema_disi_cagri_kosmaz(sandbox_state, monkeypatch):
    """Getter'lar da bot kipinde şema doğrulamasından geçer: zorunlu `ticker` yoksa getter KOŞMAZ."""
    kosuldu: list = []
    monkeypatch.setitem(ms._BY_NAME["meridian_candidate_context"], "fn", lambda a: kosuldu.append(1) or {})
    kadrolu = tuple(dataclasses.replace(b, araclar=b.araclar + ("meridian_candidate_context",))
                    if b.ad == "karne" else b for b in kadro.kadro_yukle())
    monkeypatch.setattr(kadro, "kadro_yukle", lambda yol=None: kadrolu)
    r = _cagri("karne", "meridian_candidate_context", {})["result"]
    assert r["isError"] is True and "ŞEMA DIŞI" in r["content"][0]["text"] and kosuldu == []
    # pozitif kontrol: şemaya uyan çağrı getter'ı gerçekten koşar
    assert _cagri("karne", "meridian_candidate_context", {"ticker": "MU"})["result"]["isError"] is False
    assert kosuldu == [1]


#: Her aracın şemaya uyan örnek çağrısı (bot × araç çivisi için). Burada olmayan araç `{}` ile çağrılır — şema
#: dışıysa bile metin YİNE çitli olmalı (ret ve arıza da aynı zarftan geçer).
_ORNEK_ARGS = {"plan_oku": {"tarih": "2026-09-30"}, "olay_sorgu": {"sql": "SELECT 1"},
               "bar_sorgu": {"sorgu": "kapsam"}, "hafiza_ara": {"soru": "x"}, "kart_oku": {"card_id": "EDG-2026-086"},
               "gunluk_ara": {"kelime": "x"}, "oneri_yaz": {"tur": "not", "gerekce": "g"}, "is_iste": {"ad": "karne"},
               "bot_hafizasi_ara": {"bot": "bekci", "soru": "x"}, "meridian_candidate_context": {"ticker": "MU"}}


@pytest.mark.parametrize("bot,arac", [(b.ad, a) for b in kadro.aktif_botlar() for a in ms.izinli_araclar(b.ad)])
def test_her_aktif_bot_her_izinli_arac_citli_doner(sandbox_state, monkeypatch, tmp_path, bot, arac):
    """Kadrodan parametreli: bir kadro satırı yarın yeni bir getter listelerse o da çitsiz akamaz."""
    monkeypatch.setattr(sohbet, "_hafiza_betigi", lambda: str(tmp_path / "yok.sh"))   # alt süreç yok
    _hafiza_bagla(monkeypatch, _HafizaCasusu())                                       # ağ yok
    r = _cagri(bot, arac, _ORNEK_ARGS.get(arac, {}))["result"]
    _cit_ici(r["content"][0]["text"], arac)


@pytest.mark.parametrize("bot", [None, "bekci"])
def test_nesne_olmayan_mesaj_ve_params_donguyu_oldurmez(sandbox_state, bot):
    """M-1: geçerli JSON ama nesne olmayan mesaj ya da `params` sunucuyu öldürüyordu (Hermes'teki bot o an
    ARAÇSIZ kalır). Artık -32600 (id varsa id ile, yoksa null) ve sonraki istek cevaplanır."""
    satirlar = ["[1, 2]", '"x"', "5", "null",
                json.dumps({"jsonrpc": "2.0", "id": 5, "method": "tools/call", "params": [1]}),
                json.dumps({"jsonrpc": "2.0", "id": 6, "method": "initialize", "params": [1]}),
                json.dumps({"jsonrpc": "2.0", "id": 7, "method": "tools/list", "params": "x"}),
                json.dumps({"jsonrpc": "2.0", "method": "tools/list", "params": 3}),
                "bu json değil",
                json.dumps({"jsonrpc": "2.0", "id": 8, "method": "tools/list"})]
    cikis = io.StringIO()
    ms.serve(io.StringIO("\n".join(satirlar) + "\n"), cikis, bot=bot)
    yanitlar = [json.loads(s) for s in cikis.getvalue().splitlines() if s.strip()]
    kodlar = [(y["id"], y["error"]["code"]) for y in yanitlar if "error" in y]
    assert kodlar == [(None, -32600)] * 4 + [(5, -32600), (6, -32600), (7, -32600), (None, -32600),
                                               (None, -32700)]
    assert yanitlar[-1]["id"] == 8 and yanitlar[-1]["result"]["tools"], "döngü bozuk satırlardan sonra ÖLDÜ"


def test_istek_islemede_beklenmeyen_istisna_donguyu_oldurmez(sandbox_state, monkeypatch, capsys):
    """Son savunma: `_handle` beklenmedik bir istisna atarsa -32603 döner, olay stderr'e düşer, döngü sürer."""
    gercek = ms._handle

    def patlayan(msg, *a, **kw):
        if isinstance(msg, dict) and msg.get("method") == "tools/list":
            raise RuntimeError("beklenmeyen")
        return gercek(msg, *a, **kw)

    monkeypatch.setattr(ms, "_handle", patlayan)
    giris = io.StringIO("".join(json.dumps(m) + "\n" for m in (
        {"jsonrpc": "2.0", "id": 1, "method": "tools/list"}, {"jsonrpc": "2.0", "id": 2, "method": "ping"})))
    ms.serve(giris, None, bot="bekci")
    out, err = capsys.readouterr()
    yanitlar = _protokol_satirlari(out)
    assert yanitlar[0]["id"] == 1 and yanitlar[0]["error"]["code"] == -32603
    assert yanitlar[1]["id"] == 2 and yanitlar[1]["result"] == {}
    assert "mcp_istek_isleme_hatasi" in err and "mcp_istek_isleme_hatasi" not in out


# ---- M-5: GERÇEK alt süreç ------------------------------------------------------------------------------
_AGAC = pathlib.Path(__file__).resolve().parents[1]


def _alt_surec(sandbox_state, bot: str, mesajlar, ham_satirlar=()) -> subprocess.CompletedProcess:
    """`python -m meridian.mcp_server --bot <bot>` — `MERIDIAN_ROOT` = sandbox kökü (state/ onun altında, goal/bounds
    fikstürden kopyalı; kadro buraya kopyalanır), `HOME` geçici. Test süreci ortamına YAZILMAZ: ortam yalnız
    çocuğa verilen sözlükte değişir (MERIDIAN_ROOT sızıntı bekçisi)."""
    kok = sandbox_state.parent
    (kok / "deploy/hermes").mkdir(parents=True, exist_ok=True)
    shutil.copyfile(kadro.KADRO_YOLU, kok / "deploy/hermes/kadro.yaml")
    ev = kok / "ev"
    ev.mkdir(exist_ok=True)
    ortam = {**os.environ, "MERIDIAN_ROOT": str(kok), "PYTHONPATH": str(_AGAC), "HOME": str(ev)}
    giris = "".join(json.dumps(m) + "\n" for m in mesajlar) + "".join(s + "\n" for s in ham_satirlar)
    giris += json.dumps({"jsonrpc": "2.0", "id": 999, "method": "ping"}) + "\n"   # stdin tüketilirse kaybolur
    return subprocess.run([sys.executable, "-m", "meridian.mcp_server", "--bot", bot], input=giris,
                          env=ortam, cwd=str(kok), capture_output=True, text=True, timeout=60)


def _gercek_state_izi() -> dict:
    """Ağacın GERÇEK `state/` defterlerinin (varsa) damgası — alt süreç oraya yazmamalı."""
    kok = _AGAC / "state"
    return {ad: ((kok / ad).stat().st_mtime_ns, (kok / ad).stat().st_size) if (kok / ad).exists() else None
            for ad in ("approvals.jsonl", "events.jsonl", "is_istek_defteri.jsonl")}


def test_gercek_alt_surec_stdout_yalniz_jsonrpc_obs_stderrde(sandbox_state):
    once = _gercek_state_izi()
    p = _alt_surec(sandbox_state, "sef", [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05"}},
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
        {"jsonrpc": "2.0", "id": 3, "method": "tools/call",
         "params": {"name": "oneri_yaz", "arguments": {"tur": "not", "gerekce": "alt süreç"}}}],
        ham_satirlar=["bu json değil", "[1, 2]"])
    assert p.returncode == 0, p.stderr[-2000:]
    yanitlar = _protokol_satirlari(p.stdout)                    # stdout'taki HER satır JSON-RPC 2.0
    byid = {y["id"]: y for y in yanitlar if y["id"] is not None}
    assert sorted(t["name"] for t in byid[2]["result"]["tools"]) == sorted(kadro.bot_bul("sef").araclar)
    assert byid[3]["result"]["isError"] is False and 999 in byid
    assert sorted(y["error"]["code"] for y in yanitlar if y["id"] is None) == [-32700, -32600]
    assert "sohbet_oneri_yazildi" in p.stderr and "sohbet_oneri_yazildi" not in p.stdout
    (satir,) = _sohbet_onerileri()                               # sandbox defterine yazıldı …
    assert satir["oturum"] == "mcp:sef"
    assert _gercek_state_izi() == once                          # … gerçek state/'e DEĞİL


def test_gercek_alt_surec_getter_citli_ve_scrubli(sandbox_state):
    _selfreview_sahte_sirli()
    p = _alt_surec(sandbox_state, "karne", [
        {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "meridian_selfreview", "arguments": {}}}])
    assert p.returncode == 0, p.stderr[-2000:]
    byid = {y["id"]: y for y in _protokol_satirlari(p.stdout)}
    ic = _cit_ici(byid[1]["result"]["content"][0]["text"], "meridian_selfreview")
    assert byid[1]["result"]["isError"] is False and _SAHTE_JETON not in p.stdout and "Bearer ***" in ic
    assert 999 in byid
