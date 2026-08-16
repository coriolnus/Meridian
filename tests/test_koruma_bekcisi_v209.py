"""test_koruma_bekcisi_v209.py — #8 KORUMA dedektörü (watchdog.koruma_report).

VAKA (canlı A1, 2026-08-07): broker'da 5 açık pozisyon, açık emir SIFIR, beşi de KORUMASIZ.
`portfolio.json` dört pozisyon için stop BEYAN EDİYORDU; broker'da karşılığı yoktu. Kök neden
olay defterinde saniyesiyle ölçüldü: bracket TIF'i emrin TAMAMINA uygulanır, E1 (`ENTRY_TIF="day"`)
TIF'i DAY'e çekince koruma bacakları da DAY oldu ve giriş dolduktan ~6,5 saat sonra, seans
kapanışında (20:00Z) `expired` + OCO kardeşi `canceled` oldu. Hiçbir dedektör bunu görmedi:
`reconcile_broker_state` o gece 4 MIRROR_DRIFT alarmı bastı — hepsi ADET sapması, hiçbiri koruma.

YÖNTEM: hiçbir test ağa çıkmaz — adaptörün OKUMA uçları saplanır (`positions`/`orders`/`transport`).
Gerçek istemciye DOKUNULMAZ, emir gönderen/iptal eden hiçbir yol çağrılmaz. Her iddianın yanında
POZİTİF KONTROL vardır: sınır bilerek delinir ve iddianın gerçekten düştüğü gösterilir.
"""
from __future__ import annotations

import pytest

from meridian import config, obs, store, watchdog
from meridian.adapters import alpaca

FAKE_KEY = "PKKORUMAFAKEKEY7788990011"
FAKE_SECRET = "SKKORUMAFAKESECRET2233445566778899"


@pytest.fixture
def ayna(sandbox_state, monkeypatch):
    """Sahte kimlik + `alpaca_paper` arka ucu; taşıma SAĞLIKLI. Mandal her testte temiz başlar."""
    from meridian import secrets as secrets_mod
    monkeypatch.setenv("ALPACA_PAPER_KEY", FAKE_KEY)
    monkeypatch.setenv("ALPACA_PAPER_SECRET", FAKE_SECRET)
    monkeypatch.delenv("MERIDIAN_GCP_PROJECT", raising=False)
    secrets_mod.clear_cache()
    monkeypatch.setattr(config, "BROKER", "alpaca_paper")
    monkeypatch.setattr(alpaca, "paper_available", lambda: True)
    monkeypatch.setattr(alpaca, "transport", lambda: {"ok": True, "error": ""})
    watchdog._KORUMA_ALARMED.clear()
    yield sandbox_state
    watchdog._KORUMA_ALARMED.clear()
    secrets_mod.clear_cache()


def _sap(monkeypatch, positions, orders):
    monkeypatch.setattr(alpaca, "positions", lambda: list(positions))
    monkeypatch.setattr(alpaca, "orders", lambda **kw: list(orders))


def _poz(sym, qty, side="long"):
    return {"symbol": sym, "qty": str(qty), "side": side}


def _parent(sym, coid, qty, legs=(), status="filled"):
    """Motor bracket parent'ı — sahiplik KANITI (P- öneki + DOLMUŞ)."""
    return {"id": f"id-{coid}", "client_order_id": coid, "symbol": sym, "side": "buy",
            "type": "limit", "time_in_force": "day", "status": status,
            "qty": str(qty), "filled_qty": str(qty if status == "filled" else 0),
            "legs": list(legs)}


def _bacak(sym, qty, tip, status, side="sell", coid="8796e3f6-a515-41ef-b470-8d3bceba5c3d"):
    """Koruma bacağı — `client_order_id`si ALPACA üretimidir (UUID), motor öneki TAŞIMAZ."""
    return {"id": f"leg-{coid}-{tip}-{status}", "client_order_id": coid, "symbol": sym,
            "side": side, "type": tip, "time_in_force": "day", "status": status,
            "qty": str(qty), "filled_qty": "0"}


# =================================================================================================
# CANLI VAKA — 2026-08-07 ölçümünün BİREBİR şekli (regresyon çıpası)
# =================================================================================================
CANLI_POZISYONLAR = [_poz("AMGN", 22), _poz("BKNG", 22), _poz("EMR", 37),
                     _poz("NUE", 25), _poz("NVDA", 1)]
CANLI_EMIRLER = [
    # dört motor bracket'ı: giriş DOLDU, iki koruma bacağı kapanışta ÖLDÜ (expired + OCO canceled)
    _parent("EMR", "P-2026-08-05-EMR", 37, legs=[
        _bacak("EMR", 37, "limit", "expired", coid="fbab98c1-f012-47ce-8724-17457611985a"),
        _bacak("EMR", 37, "stop", "canceled", coid="a1be9baf-3ef3-4e78-8ff0-20cb30728045")]),
    _parent("BKNG", "P-2026-08-05-BKNG", 22, legs=[
        _bacak("BKNG", 22, "limit", "expired", coid="e3b2e2d3-50d0-462e-98ea-8f9ec9370810"),
        _bacak("BKNG", 22, "stop", "canceled", coid="95d4dc02-0c87-4fcd-9614-32c3383c6d14")]),
    _parent("NUE", "P-2026-08-05-NUE", 25, legs=[
        _bacak("NUE", 25, "limit", "expired", coid="8796e3f6-a515-41ef-b470-8d3bceba5c3d"),
        _bacak("NUE", 25, "stop", "canceled", coid="2af95ccb-8851-4d01-ab0f-e661c072925c")]),
    _parent("AMGN", "P-2026-08-05-AMGN-momentum_burst", 22, legs=[
        _bacak("AMGN", 22, "limit", "expired", coid="42080cc1-86f5-48e2-bac1-74333cbecafd"),
        _bacak("AMGN", 22, "stop", "canceled", coid="6396a952-bed7-460b-9ae0-8de6e2fbe9e3")]),
    # operatörün kendi NVDA'sı: motor öneki YOK (A3) — motorun sorumluluğu değil
    {"id": "nvda-1", "client_order_id": "44a307ae-a466-46d2-9a1b-0cb2527dbaa1", "symbol": "NVDA",
     "side": "buy", "type": "market", "time_in_force": "day", "status": "filled",
     "qty": "1", "filled_qty": "1", "legs": []},
]


def test_canli_vaka_dort_motor_pozisyonu_KORUMASIZ_sayilir(ayna, monkeypatch):
    """Canlı şekil: 4 motor pozisyonunun 4'ü korumasız; NVDA AYRI sayılır ve `ok`u düşürmez."""
    _sap(monkeypatch, CANLI_POZISYONLAR, CANLI_EMIRLER)
    r = watchdog.koruma_report()
    assert r["ok"] is False, "dört korumasız pozisyon varken dedektör GEÇTİ — hüküm yanlış"
    assert r["korumasiz"] == 4 and r["toplam"] == 4
    assert r["korumasiz_semboller"] == ["AMGN", "BKNG", "EMR", "NUE"]
    # MOTOR-DIŞI AYRI: sayılır, görünür, ama motorun paydasına GİRMEZ
    assert r["motor_disi"] == 1 and r["motor_disi_semboller"] == ["NVDA"]
    assert r["motor_disi_korumasiz"] == 1
    assert r["olculemedi"] is False and r["sev"] == "sev-1"


def test_ok_alani_DONER_hukum_veren_dedektor(ayna, monkeypatch):
    """`ok` alanı SÖZLEŞMEDİR (`watchdog.conservation_report` dersi): hüküm vermeyen dedektör bakanı boş geçirir."""
    _sap(monkeypatch, CANLI_POZISYONLAR, CANLI_EMIRLER)
    assert "ok" in watchdog.koruma_report()
    # POZİTİF KONTROL: temiz durumda da alan DÖNER ve True olur (None kalmaz)
    _sap(monkeypatch, [_poz("EMR", 37)],
         [_parent("EMR", "P-1-EMR", 37, legs=[_bacak("EMR", 37, "stop", "new")])])
    temiz = watchdog.koruma_report()
    assert temiz["ok"] is True and temiz["korumasiz"] == 0 and temiz["toplam"] == 1


def test_KORUMALI_pozisyon_yakalanmaz_bacak_coidi_UUID_olsa_bile(ayna, monkeypatch):
    """TUZAK: koruma bacağının coid'i Alpaca üretimidir → `is_engine_order` HER ZAMAN False.

    Dedektör "canlı stop var mı" sorusunu motor önekiyle süzseydi, KORUNAN her pozisyon çıplak
    görünürdü (`alpaca` OCO süpürme bloğunun dersi). Bu test o süzgecin girmediğini kanıtlar."""
    poz = [_poz("EMR", 37)]
    emir = [_parent("EMR", "P-1-EMR", 37,
                    legs=[_bacak("EMR", 37, "limit", "new", coid="tp-uuid"),
                          _bacak("EMR", 37, "stop", "held", coid="sl-uuid")])]
    _sap(monkeypatch, poz, emir)
    r = watchdog.koruma_report()
    assert r["ok"] is True and r["korumasiz"] == 0
    assert not alpaca.is_engine_order(emir[0]["legs"][1]), \
        "test kurgusu bozuk: bacak motor öneki taşımamalıydı"
    assert r["rows"][0]["korumali"] is True and r["rows"][0]["kapsanan"] == 37
    # POZİTİF KONTROL: AYNI kurgu, stop bacağı ÖLÜ → aynı pozisyon korumasız sayılır
    emir[0]["legs"][1]["status"] = "canceled"
    assert watchdog.koruma_report()["korumasiz"] == 1


def test_broker_erisilemezse_ok_None_ve_NEDEN_sifir_DEGIL(ayna, monkeypatch):
    """ÖLÇÜLEMEDİ ≠ 0. `positions()`/`orders()` arızada da [] döner (A1) — boş listeyi 'temiz'
    okumak, tam da arızayı temizlik diye raporlamak olurdu."""
    _sap(monkeypatch, [], [])
    monkeypatch.setattr(alpaca, "transport", lambda: {"ok": False, "error": "ReadTimeout: positions"})
    r = watchdog.koruma_report()
    assert r["ok"] is None, "broker okunamazken hüküm verildi"
    assert r["korumasiz"] is None and r["toplam"] is None, "ölçülemeyen sayı 0 yazıldı (UYDURMA)"
    assert r["olculemedi"] is True and "okunamadı" in r["neden"] and "ReadTimeout" in r["neden"]
    # POZİTİF KONTROL: taşıma sağlığı geri gelince AYNI boş liste 'temiz' olarak ölçülür
    monkeypatch.setattr(alpaca, "transport", lambda: {"ok": True, "error": ""})
    temiz = watchdog.koruma_report()
    assert temiz["ok"] is True and temiz["korumasiz"] == 0 and temiz["toplam"] == 0


def test_emir_ucu_duserse_de_None_pozisyon_okunmus_olsa_bile(ayna, monkeypatch):
    """İKİNCİ ARIZA KAPISI: pozisyonlar okundu ama EMİR listesi düştü → 'hepsi korumasız' DEĞİL.

    Bu dal olmasaydı geçici bir 5xx, dört sağlam pozisyonu sev-1 çıplaklık diye alarmlardı."""
    cagri = {"n": 0}

    def _transport():
        cagri["n"] += 1
        return {"ok": cagri["n"] < 2, "error": "" if cagri["n"] < 2 else "HTTP 502: orders"}

    _sap(monkeypatch, [_poz("EMR", 37)], [])
    monkeypatch.setattr(alpaca, "transport", _transport)
    r = watchdog.koruma_report()
    assert r["ok"] is None and r["korumasiz"] is None
    assert "emir listesi okunamadı" in r["neden"] and "502" in r["neden"]


def test_PAYDA_beyanli(ayna, monkeypatch):
    """Paydasız bir sayı ('3 korumasız') risk oranını söylemez: payda + BEYAN metni zorunlu."""
    _sap(monkeypatch, CANLI_POZISYONLAR, CANLI_EMIRLER)
    r = watchdog.koruma_report()
    assert r["toplam"] == 4 and r["korumasiz"] == 4
    beyan = r["payda_beyani"]
    assert "korumasız" in beyan and "toplam" in beyan.lower() and "motor" in beyan.lower(), beyan
    assert watchdog.KORUMA_PAYDA_BEYANI == beyan
    # Payda MOTOR pozisyonlarıdır: NVDA paydayı ŞİŞİRMEZ (5 değil 4)
    assert r["toplam"] == len([x for x in r["rows"] if x["motor"]]) == 4


def test_motor_disi_pozisyon_ok_hukmunu_DUSURMEZ_ama_gorunur(ayna, monkeypatch):
    """A3: motor sahibi olmadığı pozisyonu koruyamaz — sorumluluk değil, GÖRÜNÜRLÜK."""
    _sap(monkeypatch, [_poz("NVDA", 1)], [CANLI_EMIRLER[-1]])
    r = watchdog.koruma_report()
    assert r["ok"] is True, "motor-dışı çıplak pozisyon motorun hükmünü düşürdü (A3 ihlali)"
    assert r["toplam"] == 0 and r["korumasiz"] == 0
    assert r["motor_disi"] == 1 and r["motor_disi_korumasiz"] == 1
    assert r["motor_disi_semboller"] == ["NVDA"]


def test_kismi_kapsama_KORUMASIZ_sayilir(ayna, monkeypatch):
    """'Yarısı korunuyor' bir güvenlik hâli değil ölçülmüş bir açıktır — yukarı yuvarlanmaz."""
    _sap(monkeypatch, [_poz("EMR", 37)],
         [_parent("EMR", "P-1-EMR", 37, legs=[_bacak("EMR", 20, "stop", "new")])])
    r = watchdog.koruma_report()
    assert r["ok"] is False and r["korumasiz"] == 1
    row = r["rows"][0]
    assert row["kismi"] is True and row["kapsanan"] == 20 and "20/37" in row["neden"]


def test_kisa_pozisyonu_ALIS_stopu_korur_satis_stopu_korumaz(ayna, monkeypatch):
    """Yön sabit yazılsaydı, YANLIŞ yöndeki bir stop 'koruma' sanılırdı — çıplaklıktan beter."""
    poz = [_poz("EMR", 37, side="short")]
    yanlis = [_parent("EMR", "P-1-EMR", 37, legs=[_bacak("EMR", 37, "stop", "new", side="sell")])]
    _sap(monkeypatch, poz, yanlis)
    assert watchdog.koruma_report()["korumasiz"] == 1
    dogru = [_parent("EMR", "P-1-EMR", 37, legs=[_bacak("EMR", 37, "stop", "new", side="buy")])]
    _sap(monkeypatch, poz, dogru)
    assert watchdog.koruma_report()["korumasiz"] == 0


def test_limit_bacagi_koruma_SAYILMAZ(ayna, monkeypatch):
    """Kâr-al (limit) bacağı bir KORUMA değildir: yukarı çıkışta dolar, düşüşte hiçbir şey yapmaz."""
    _sap(monkeypatch, [_poz("EMR", 37)],
         [_parent("EMR", "P-1-EMR", 37, legs=[_bacak("EMR", 37, "limit", "new")])])
    assert watchdog.koruma_report()["korumasiz"] == 1


def test_ayna_kapaliyken_KAPSAM_DISI_ok_None_ve_alarm_YOK(ayna, monkeypatch):
    """`broker=internal`: sorunun REFERANSI yok. Ne 'temiz' denir ne her poll'da alarmlanır."""
    monkeypatch.setattr(config, "BROKER", "internal")
    _sap(monkeypatch, CANLI_POZISYONLAR, CANLI_EMIRLER)
    r = watchdog.check_koruma_and_alarm()
    assert r["ok"] is None and r["kapsam_disi"] is True and r["neden"]
    assert not [e for e in store.read_jsonl("events.jsonl") if e.get("level") == "alarm"], \
        "ayna kapalıyken alarm basıldı — yapılandırma hâli alarm bütçesini yiyor"


# =================================================================================================
# ALARM GEÇİŞİ
# =================================================================================================
def _alarmlar():
    return [e for e in store.read_jsonl("events.jsonl") if e.get("level") == "alarm"]


def test_korumasiz_pozisyon_sev1_alarmi_uretir_ve_MANDALLANIR(ayna, monkeypatch):
    _sap(monkeypatch, CANLI_POZISYONLAR, CANLI_EMIRLER)
    watchdog.check_koruma_and_alarm()
    al = _alarmlar()
    assert len(al) == 4, f"dört korumasız pozisyon, {len(al)} alarm"
    a = next(x for x in al if x.get("ticker") == "NUE")
    assert a["sev"] == "sev-1" and a["kind"] == "korumasiz_pozisyon"
    # JETON AYRIMI (N1, 2026-08-09): v209 burada `MIRROR_DRIFT`i ÖDÜNÇ alıyordu ve bedelini kendi
    # docstring'ine yazmıştı — `obs._maybe_notify`in 6 saatlik susturma penceresi JETON BAŞINADIR,
    # yani gürültülü bir mutabakat gecesinde ADET SAPMASI alarmları bu sev-1 alarmın TESLİMATINI
    # bastırabiliyordu. Ödünç bitti; `obs.ALARM_NAKED_POSITION` `NOTIFY_TOKENS` türetmesine
    # kendiliğinden girer (obs.py:98). Pencerenin ARTIK paylaşılmadığının davranışsal çivisi:
    # tests/test_dalga_w1_v216.py::test_N1_iki_alarm_ARTIK_AYNI_susturma_penceresini_paylasmaz
    assert a["alarm"] == obs.ALARM_NAKED_POSITION    # teslim edilen jeton sınıfı (NOTIFY_TOKENS)
    assert a["korumasiz"] == 4 and a["toplam"] == 4 and a["payda_beyani"]
    assert "KORUMASIZ POZİSYON" in str(a.get("message", "")) + str(a.get("event", ""))
    # MANDAL: aynı olgu ikinci poll'da TEKRAR anlatılmaz
    watchdog.check_koruma_and_alarm()
    assert len(_alarmlar()) == 4, "aynı korumasızlık ikinci kez alarmlandı (mandal tutmadı)"
    # DÜZELİNCE MANDAL DÜŞER, YENİDEN BOZULUNCA YENİDEN ALARMLANIR
    _sap(monkeypatch, [_poz("NUE", 25)],
         [_parent("NUE", "P-1-NUE", 25, legs=[_bacak("NUE", 25, "stop", "new")])])
    watchdog.check_koruma_and_alarm()
    assert len(_alarmlar()) == 4
    _sap(monkeypatch, CANLI_POZISYONLAR, CANLI_EMIRLER)
    watchdog.check_koruma_and_alarm()
    assert len(_alarmlar()) > 4, "düzelip yeniden bozulan koruma ikinci kez alarmlanmadı"


def test_olculemedi_kendi_jetonuyla_alarmlanir(ayna, monkeypatch):
    """'Ölçemedim' de bir hükümdür (YASA 4) ve 'temiz' değildir — kendi jetonu vardır."""
    _sap(monkeypatch, [], [])
    monkeypatch.setattr(alpaca, "transport", lambda: {"ok": False, "error": "ConnectError"})
    watchdog.check_koruma_and_alarm()
    al = _alarmlar()
    assert len(al) == 1 and al[0]["kind"] == "koruma_olculemedi"
    assert al[0]["sev"] == "sev-1" and al[0]["olculemedi"] is True
    assert "korumasız 0" in str(al[0].get("message", "")) + str(al[0].get("event", ""))


def test_motor_disi_ciplakligi_ALARM_degil_UYARI(ayna, monkeypatch):
    """Operatörün kendi pozisyonu motorun sev-1 bütçesini yemez — ama sessiz de kalmaz."""
    _sap(monkeypatch, [_poz("NVDA", 1)], [CANLI_EMIRLER[-1]])
    watchdog.check_koruma_and_alarm()
    assert not _alarmlar(), "motor-dışı pozisyon sev-1 alarmı ürettı (A3 sınırı aşıldı)"
    uyari = [e for e in store.read_jsonl("events.jsonl")
             if e.get("event") == "korumasiz_motor_disi_pozisyon"]
    assert len(uyari) == 1 and uyari[0]["ticker"] == "NVDA"


# =================================================================================================
# KABLOLAMA — ÖLÜ MEKANİZMA SIFIR (hedef sözleşmesi #1)
# =================================================================================================
def test_check_and_alarm_koruma_gecisini_CAGIRIR(ayna, monkeypatch):
    """Dedektör bir ÜRETİM kadansına bağlı: `scheduler` → `check_and_alarm` (300 sn) → koruma."""
    cagrildi = []
    monkeypatch.setattr(watchdog, "check_koruma_and_alarm",
                        lambda: cagrildi.append(1) or {"ok": True})
    watchdog.check_and_alarm()
    assert cagrildi == [1], "koruma geçişi poll kadansında çağrılmıyor — dedektör ÖLÜ"


def test_koruma_arizasi_mekanizma_bekcisini_GOTURMEZ(ayna, monkeypatch):
    """Yalıtım: koruma dedektörü fırlatırsa `check_and_alarm` yine tamamlanır ve SESSİZ kalmaz."""
    def _patlat():
        raise RuntimeError("kasıtlı arıza")

    monkeypatch.setattr(watchdog, "check_koruma_and_alarm", _patlat)
    watchdog.check_and_alarm()                      # fırlatmamalı
    assert [e for e in store.read_jsonl("events.jsonl")
            if e.get("event") == "koruma_dedektoru_dustu"], "dedektör arızası SESSİZ yutuldu"


def test_dedektor_broker_a_YALNIZ_okuma_cagrisi_yapar():
    """SALT OKUMA SINIRI (AST): bekçi haber verir, düzeltmez — emir gönderen/iptal eden hiçbir
    adaptör çağrısı bu iki fonksiyonda ÇAĞRILMAZ.

    Metin taraması DEĞİL AST: gerekçe yorumlarında yasak fonksiyonun ADI geçebilir (ve geçiyor —
    sahiplik yasası `close_engine_position`la ortak). Yorumda ADI ANMAK ile onu ÇAĞIRMAK aynı şey
    değildir; metin taraması bu ayrımı yapamadığı için ya yanlış alarm verir ya gerekçeyi sildirir."""
    import ast
    import inspect
    import textwrap
    YASAK = {"submit_plan", "submit_bracket", "cancel_order", "cancel_open_entries",
             "close_engine_position", "close_all", "replace_order_stop",
             "post", "delete", "patch", "put"}
    cagrilar = set()
    for fn in (watchdog.koruma_report, watchdog.check_koruma_and_alarm):
        for node in ast.walk(ast.parse(textwrap.dedent(inspect.getsource(fn)))):
            if not isinstance(node, ast.Call):
                continue
            f = node.func
            cagrilar.add(f.attr if isinstance(f, ast.Attribute) else
                         (f.id if isinstance(f, ast.Name) else ""))
    kesisim = cagrilar & YASAK
    assert not kesisim, f"koruma bekçisi emir yüzeyini ÇAĞIRIYOR: {sorted(kesisim)}"
    assert {"positions", "orders", "transport"} <= cagrilar, \
        f"adaptörün okuma uçları kullanılmıyor: {sorted(cagrilar)}"
