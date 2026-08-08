"""test_dalga_w1_v216.py — DALGA W1: jeton ayrımı · damgasız yazım · taban kayması · eğri dönemi.

NE ÖLÇER (her iş kendi çivisiyle, kaynakları satır satır yazılı):

  N1   `obs.ALARM_NAKED_POSITION` — korumasız-pozisyon alarmı `MIRROR_DRIFT` jetonunu ÖDÜNÇ
       almıyor; 6 saatlik susturma penceresi ADET SAPMASI alarmlarıyla PAYLAŞILMIYOR.
       (kaynak: `meridian/watchdog.py` #8 bölümünün v209'da yazdığı ölçülmüş bedel)

  SB-4 `watchdog.kitap_damga_report` — kitap `store` kapısı DIŞINDAN değiştiğinde alarm.
       2026-08-04 vakası fikstür olarak BİREBİR yeniden üretilir: içerik değişir, `entity_meta`
       damgası ilerlemez. (kaynak: docs/BAYAT-SERMAYE-KOK-2026-08-07.md §7)

  SB-3 `recompute.report` `taban_kaymasi` satırı + `watchdog.monotonicity_report` `sermaye_taban`
       sayacı. Satırın 08-04'ü YAKALAYAMADIĞI (yapısal sınır) ve sayacın YAKALADIĞI birlikte
       çivilenir — biri diğerinin gerekçesi.

  Ç1   `analytics._realized_drawdown` serinin KAPSADIĞI DÖNEMİ ölçer; canlı döneme ait m2m yoksa
       bacak ÖLÇÜLEMEDİ olur ve `max_dd` bir ALT SINIRA döner. EŞİKLERE DOKUNULMADI.
       (kaynak: docs/CIFT-KAYNAK-TARAMASI-2026-08-09.md §4.1)

  Ç5   `broker.DERISK_FLOOR_DD` ve `shadowlaw.DD_VETO_MARGIN` goal'a TEST-kaynaklı bağlanır.
       (emsal: tests/test_hafta3a_v119.py:78 — `broker.py`/`shadowlaw.py`ye DOKUNULMADI)

  #10  `watchdog.mutabakat_tazelik_report` — ayna mutabakat kaydının SEANS tazeliği.
       (kaynak: docs/CIFT-KAYNAK-TARAMASI-2026-08-09.md §4.2/§4.5 — 24,3 sa bayat ölçümü)

  #7   `tests/conftest` modül-durumu tabanı `alpaca._TRANSPORT` + `obs._SUPPRESS_LOGGED`i de
       sıfırlıyor (v215 sızıntısının SINIF kapaması).
"""
from __future__ import annotations

import json

import pytest

from meridian import (analytics, broker, config, obs, recompute, shadowlaw, storage, store,
                      watchdog)
from meridian.adapters import alpaca


# =================================================================================================
# ORTAK FİKSTÜRLER
# =================================================================================================
def _islem(i: int, pnl: float, kapanis: str = "2026-07-20") -> dict:
    return {"id": f"T{i:05d}", "ts_open": "2026-07-01", "ts_close": kapanis, "ticker": "AAA",
            "side": "long", "entry": 100.0, "exit": 100.0 + pnl / 10.0, "qty": 10,
            "r_multiple": pnl / 300.0, "pnl_dollars": pnl, "costs": 5.0,
            "exit_reason": "target" if pnl > 0 else "stop", "strategy_version": 3,
            "regime": "trend_up", "setup": "breakout_vcp", "score": 80}


@pytest.fixture
def db_kitap(sandbox_state):
    """CANLI ARKA UÇLA AYNI ZEMİN: kitap DB'de. Bu bir kolaylık değil bir KAPIDIR — damgasızlık
    ancak `entity_meta.rev` bir yazım SAYACI olduğunda ayırt edilebilir; dosya arka ucunda her
    yazım mtime'ı oynatır ve sınıf TANIMSIZDIR (`kitap_damga_report` bunu kendi raporunda söyler).
    Canlı `state/portfolio.json` DOSYA OLARAK YOKTUR — kitap DB'dedir (BAYAT-SERMAYE-KOK §7)."""
    storage.ensure_schema()
    yield sandbox_state
    storage.close_connections()


def _db_disi_yazim(doc: dict) -> None:
    """`store` KAPISINI ATLAYAN yazım — 2026-08-04'ün ölçülmüş imzası.

    `store.write_json` → `storage.write_doc` → `do_write_doc` + `_touch` (storage.py:480) yolu
    `entity_meta.rev`i HER yazımda artırır. Buradaki yazım o son adımı ATLAR: içerik değişir,
    damga yerinde kalır. Canlı kanıt tam buydu — 08-04'te rev yalnız İKİ kez ilerledi (3→4→5) ve
    ikisi de kanıtlı `_save_broker`dı, oysa kitabın içeriği ÜÇÜNCÜ kez değişmişti."""
    c = storage.connect(storage.db_path())
    c.execute("UPDATE portfolio SET doc_json=? WHERE id=1", (json.dumps(doc),))
    c.commit()


# =================================================================================================
# N1 — JETON AYRIMI
# =================================================================================================
def test_N1_naked_position_kendi_jetonudur_ve_bildirim_kapsamindadir():
    """Jeton `obs.py`de tanımlı olmalı VE `NOTIFY_TOKENS` onu TÜRETMELİ.

    İkinci şart birincisinden ayrıdır ve unutulması ölçülmüş bir kusurdur: v209 bu dedektörü
    yazarken jetonu ekleyemediği için (`obs.py` o turun yazım kapsamı dışındaydı) `MIRROR_DRIFT`i
    ödünç aldı — listede olmayan bir jeton YAZILIR ama operatörün telefonuna HİÇ ULAŞMAZ."""
    assert obs.ALARM_NAKED_POSITION == "NAKED_POSITION"
    assert obs.ALARM_NAKED_POSITION in obs.NOTIFY_TOKENS, \
        "jeton bildirim kapsamı DIŞINDA — alarm yazılır ama teslim edilmez"
    assert obs.ALARM_NAKED_POSITION != obs.ALARM_MIRROR_DRIFT


def test_N1_korumasiz_pozisyon_alarmi_MIRROR_DRIFT_odunc_ALMAZ(sandbox_state, monkeypatch):
    """Alarm satırının jetonu NAKED_POSITION; `kind`/`sev` sözleşmesi DEĞİŞMEDEN taşınır."""
    monkeypatch.setattr(watchdog, "koruma_report", lambda: {
        "ok": False, "olculemedi": False, "kapsam_disi": False, "neden": "",
        "korumasiz": 1, "toplam": 1, "payda_beyani": watchdog.KORUMA_PAYDA_BEYANI,
        "korumasiz_semboller": ["NUE"], "motor_disi": 0, "motor_disi_korumasiz": 0,
        "motor_disi_semboller": [], "emir_tavani_dolu": False, "sev": watchdog.KORUMA_SEV,
        "rows": [{"ticker": "NUE", "adet": 54.0, "yon": "long", "motor": True, "korumali": False,
                  "kapsanan": 0.0, "kismi": False, "stop_emirleri": [],
                  "neden": "broker'da CANLI koruyucu stop YOK"}]})
    watchdog._KORUMA_ALARMED.clear()
    kayit = []
    monkeypatch.setattr(obs, "alarm", lambda tok, msg, **kw: kayit.append((tok, msg, kw)))
    watchdog.check_koruma_and_alarm()
    assert len(kayit) == 1
    tok, msg, kw = kayit[0]
    assert tok == "NAKED_POSITION", f"jeton hâlâ ödünç: {tok}"
    assert "KORUMASIZ POZİSYON" in msg and "NUE" in msg
    assert kw["kind"] == "korumasiz_pozisyon" and kw["sev"] == watchdog.KORUMA_SEV


def test_N1_koruma_OLCULEMEDI_dali_da_ayri_jetondadir(sandbox_state, monkeypatch):
    """"Ölçülemedi" de bu sorunun bir hâlidir; adet sapmasının penceresinde kalması, N1'in
    kapattığı kusuru yarım bırakmak olurdu."""
    monkeypatch.setattr(watchdog, "koruma_report", lambda: {
        "ok": None, "olculemedi": True, "kapsam_disi": False, "rows": [],
        "neden": "Alpaca kimliği/erişimi yok", "sev": watchdog.KORUMA_SEV})
    watchdog._KORUMA_ALARMED.clear()
    kayit = []
    monkeypatch.setattr(obs, "alarm", lambda tok, msg, **kw: kayit.append((tok, msg, kw)))
    watchdog.check_koruma_and_alarm()
    assert [t for t, _, _ in kayit] == ["NAKED_POSITION"]


def test_N1_iki_alarm_ARTIK_AYNI_susturma_penceresini_paylasmaz(sandbox_state, monkeypatch):
    """ASIL ÖLÇÜM — kusur jetonun adında değil, `obs._maybe_notify`in JETON BAŞINA tuttuğu 6
    saatlik pencerededir. Gürültülü bir mutabakat gecesi `MIRROR_DRIFT` penceresini doldurur;
    eskiden korumasız-pozisyon alarmının TESLİMATI da onunla birlikte bastırılırdı.

    Kanal BAĞLI taklit edilir (`notify.configured` True, `notify.send` True): önce MIRROR_DRIFT
    penceresi kurulur, sonra NAKED_POSITION denenir. İkincisi teslim edilmelidir."""
    from meridian import notify
    monkeypatch.setattr(notify, "configured", lambda: True)
    gonderilen = []
    monkeypatch.setattr(notify, "send", lambda m: (gonderilen.append(m), True)[1])
    obs._SUPPRESS_LOGGED.clear()
    obs.alarm(obs.ALARM_MIRROR_DRIFT, "adet sapması 1")
    obs.alarm(obs.ALARM_MIRROR_DRIFT, "adet sapması 2")          # aynı pencere → bastırılır
    obs.alarm(obs.ALARM_NAKED_POSITION, "NUE korumasız")
    assert sum(1 for m in gonderilen if "MIRROR_DRIFT" in m) == 1, "pencere kurulmadı"
    assert sum(1 for m in gonderilen if "NAKED_POSITION" in m) == 1, \
        "korumasız-pozisyon alarmı adet sapmasının penceresi tarafından SUSTURULDU"


# =================================================================================================
# SB-4 — DAMGASIZ YAZIM BEKÇİSİ
# =================================================================================================
def test_SB4_2026_08_04_vakasi_store_disi_yazim_ALARM_uretir(db_kitap, monkeypatch):
    """08-04 BİREBİR: kitap 100000/0,0 iken defterin ESKİ tabanına (94457,91/−5542,09) çekilir ve
    yazım `store` kapısından GEÇMEZ. Bekçi bunu ADIYLA bağırmalı."""
    beyanli = {"cash": 100000.0, "realized_pnl": 0.0, "peak_equity": 100000.0,
               "last_date": "2026-08-03", "positions": {}}
    store.write_json("portfolio.json", beyanli)
    assert store.db_backed("portfolio.json") is True, "fikstür DB arka ucunda değil"
    watchdog.check_kitap_damga_and_alarm()                        # taban kaydedilir
    damga_once = store.stamp("portfolio.json")

    _db_disi_yazim({"cash": 94457.91, "realized_pnl": -5542.09, "peak_equity": 100000.0,
                    "last_date": "2026-08-03", "positions": {}})
    assert store.stamp("portfolio.json") == damga_once, \
        "fikstür geçersiz: damga ilerledi, yani yazım store kapısından GEÇMİŞ"

    kayit = []
    monkeypatch.setattr(obs, "alarm", lambda tok, msg, **kw: kayit.append((tok, msg, kw)))
    watchdog._DAMGA_ALARMED.clear()
    rep = watchdog.check_kitap_damga_and_alarm()
    assert rep["ok"] is False and rep["damgasiz"] == ["portfolio.json"]
    assert [t for t, _, _ in kayit] == [obs.ALARM_DATA_QUALITY]
    assert "DAMGASIZ YAZIM" in kayit[0][1] and "store" in kayit[0][1]
    assert kayit[0][2]["kind"] == "damgasiz_yazim"


def test_SB4_MESRU_store_yazimi_alarm_URETMEZ(db_kitap, monkeypatch):
    """DIŞ YAZIM YASAK DEĞİL, SESSİZ YAZIM YASAK. `ops/sermaye_beyani_iade.py` gibi motor DIŞI ama
    `store`dan geçen bir onarım damgayı ilerletir ve bu bekçi ona DOKUNMAZ — yoksa bekçi meşru
    operatör onarımını suçlar ve ilk haftada susturulurdu."""
    store.write_json("portfolio.json", {"cash": 100000.0, "realized_pnl": 0.0})
    watchdog.check_kitap_damga_and_alarm()
    store.write_json("portfolio.json", {"cash": 100000.0, "realized_pnl": 0.0,
                                        "sermaye_resetleri": [{"id": "R1", "ofset": 5542.09}]})
    kayit = []
    monkeypatch.setattr(obs, "alarm", lambda tok, msg, **kw: kayit.append(tok))
    watchdog._DAMGA_ALARMED.clear()
    rep = watchdog.check_kitap_damga_and_alarm()
    assert rep["ok"] is True and not kayit
    assert [r["sinif"] for r in rep["rows"]] == ["damgali_degisim"]


def test_SB4_icerik_ayni_yeniden_yazim_alarm_URETMEZ(db_kitap, monkeypatch):
    """`dagit [1b]`in goal/bounds dersi: damga ilerler, içerik BİREBİR aynıdır. Ham damga farkına
    bakan bir bekçi burada KUSUR bağırırdı (2026-08-02 bounds.yaml yanlış-alarmı)."""
    kitap = {"cash": 100000.0, "realized_pnl": 0.0}
    store.write_json("portfolio.json", kitap)
    watchdog.check_kitap_damga_and_alarm()
    store.write_json("portfolio.json", dict(kitap))               # aynı içerik, yeni rev
    kayit = []
    monkeypatch.setattr(obs, "alarm", lambda tok, msg, **kw: kayit.append(tok))
    rep = watchdog.check_kitap_damga_and_alarm()
    assert not kayit and rep["ok"] is True
    assert [r["sinif"] for r in rep["rows"]] == ["damga_ilerledi_icerik_ayni"]


def test_SB4_mandal_ayni_olguyu_iki_kez_anlatmaz(db_kitap, monkeypatch):
    """EEMUA bütçesi: aynı damgasız yazım her 300 sn'lik poll'da yeniden bağırmaz."""
    store.write_json("portfolio.json", {"cash": 100000.0, "realized_pnl": 0.0})
    watchdog.check_kitap_damga_and_alarm()
    _db_disi_yazim({"cash": 94457.91, "realized_pnl": -5542.09})
    kayit = []
    monkeypatch.setattr(obs, "alarm", lambda tok, msg, **kw: kayit.append(tok))
    watchdog._DAMGA_ALARMED.clear()
    watchdog.check_kitap_damga_and_alarm()
    watchdog.check_kitap_damga_and_alarm()
    watchdog.check_kitap_damga_and_alarm()
    assert len(kayit) == 1, f"mandal tutmadı: {len(kayit)} alarm"


def test_SB4_dosya_arka_ucunda_HUKUM_VERMEZ_temiz_de_DEMEZ(sandbox_state):
    """AYIRT EDİCİ GÜCÜN SINIRI BEYANLI: dosya arka ucunda mtime her yazımda oynar, yani
    "damgasız yazım" TANIMSIZDIR. Rapor `ayirt_edici=False` der ve `ok`u None bırakır — "temiz"
    demek, ölçemediği bir şeyi ölçülmüş göstermek olurdu (UYDURMA YASAĞI)."""
    store.write_json("portfolio.json", {"cash": 100000.0})
    assert store.db_backed("portfolio.json") is False
    rep = watchdog.kitap_damga_report(persist=True)
    assert rep["rows"][0]["ayirt_edici"] is False
    (config.STATE / "portfolio.json").write_text(json.dumps({"cash": 1.0}))
    rep2 = watchdog.kitap_damga_report()
    # dosyada damga da içerik de değişir → sınıf `damgali_degisim`, yani SUÇLAMA YOK
    assert rep2["rows"][0]["sinif"] in ("damgali_degisim", "olculemedi")
    assert not rep2["damgasiz"]


def test_SB4_ilk_gozlem_taban_kurar_hukum_VERMEZ(db_kitap):
    """Taban yokken "değişmedi" demek de "değişti" demek de uydurma olurdu."""
    store.write_json("portfolio.json", {"cash": 100000.0})
    rep = watchdog.kitap_damga_report(persist=True)
    assert rep["rows"][0]["sinif"] == "taban_yok" and rep["ok"] is True


def test_SB4_okuma_yolu_TABANI_ILERLETMEZ(db_kitap):
    """Akranlarıyla (monotonicity/ownership) AYNI sözleşme: `/api/diagnostics`i açık tutmak
    dedektörü körleştiremez. `persist=False` çağrısı damgasız yazımı SOĞURMAMALI."""
    store.write_json("portfolio.json", {"cash": 100000.0})
    watchdog.kitap_damga_report(persist=True)
    _db_disi_yazim({"cash": 94457.91})
    watchdog.kitap_damga_report()                                  # salt okuma × 3
    watchdog.kitap_damga_report()
    rep = watchdog.kitap_damga_report()
    assert rep["damgasiz"] == ["portfolio.json"], "okuma yolu tabanı ilerletip kanıtı yuttu"


def test_SB4_yerlesim_poll_kadansindadir(sandbox_state, monkeypatch):
    """YERLEŞİM ÖLÇÜMÜNÜN ÇİVİSİ: dedektör 300 sn'lik `check_and_alarm` poll'unda koşar, günde bir
    koşan `check_integrity_and_alarm`da DEĞİL. 08-04'te fark 13,9 saatti (bir sonraki döngü turu
    21:47:54'te kitabı zaten çimentolamıştı) ve o gecikme aynanın yarım boyutlu emirlerinin
    ÖNÜNDEKİ tek fırsat penceresiydi."""
    cagrildi = {"damga": 0, "mutabakat": 0}
    monkeypatch.setattr(watchdog, "check_kitap_damga_and_alarm",
                        lambda: cagrildi.__setitem__("damga", cagrildi["damga"] + 1))
    monkeypatch.setattr(watchdog, "check_mutabakat_and_alarm",
                        lambda: cagrildi.__setitem__("mutabakat", cagrildi["mutabakat"] + 1))
    monkeypatch.setattr(watchdog, "check_koruma_and_alarm", lambda: None)
    watchdog.check_and_alarm()
    assert cagrildi == {"damga": 1, "mutabakat": 1}


def test_SB4_dedektor_dususu_mekanizma_bekcisini_GOTURMEZ(sandbox_state, monkeypatch):
    """Yalıtım disiplini (#8 korumanın aynısı): üç dedektörden birinin arızası poll'u düşüremez."""
    def _patlat():
        raise RuntimeError("sonda düştü")
    monkeypatch.setattr(watchdog, "check_kitap_damga_and_alarm", _patlat)
    monkeypatch.setattr(watchdog, "check_koruma_and_alarm", lambda: None)
    uyari = []
    monkeypatch.setattr(obs, "warn", lambda ev, **kw: uyari.append(ev))
    watchdog.check_and_alarm()                                     # istisna DIŞARI ÇIKMAMALI
    assert "damga_dedektoru_dustu" in uyari


# =================================================================================================
# SB-3 — TABAN KAYMASI
# =================================================================================================
def test_SB3_taban_kaymasi_satiri_tabani_ADIYLA_yayimlar(sandbox_state):
    """Satırın EKLEDİĞİ şey: kitabın zımni tabanı ve beyanlı tabanı MAKİNE-OKUNUR olarak yan yana.
    2026-08-04 soruşturmasının ilk yarısı tam olarak bu sayıyı elle yeniden kurmakla geçti."""
    store.write_jsonl("trades.jsonl", [_islem(0, -5542.09)])
    store.write_json("portfolio.json", {
        "cash": 100000.0, "realized_pnl": 0.0, "positions": {},
        "sermaye_resetleri": [{"id": "R1", "ts": "2026-08-01", "ofset": 5542.09,
                               "neden": "canlı taban 100.000$'a taşındı"}]})
    satir = next(r for r in recompute.report()["rows"] if r["check"] == "taban_kaymasi")
    assert satir["ok"] is True
    assert satir["a"] == pytest.approx(5542.09, abs=0.01)          # zımni taban
    assert satir["b"] == pytest.approx(5542.09, abs=0.01)          # beyanlı taban
    assert "monotonicity_report" in satir["detail"], "okuyucu asıl dedektöre yönlendirilmiyor"


def test_SB3_beyansiz_taban_satiri_KIRAR(sandbox_state):
    """Beyan yokken kitabın defterden sapan kısmını açıklayan bir kayıt yoktur → satır kırmızı."""
    store.write_jsonl("trades.jsonl", [_islem(0, -5542.09)])
    store.write_json("portfolio.json", {"cash": 100000.0, "realized_pnl": 0.0, "positions": {}})
    satir = next(r for r in recompute.report()["rows"] if r["check"] == "taban_kaymasi")
    assert satir["ok"] is False and "BEYANSIZ taban" in satir["detail"]


def test_SB3_TERS_ONARIM_satiri_YESIL_birakir_ve_bu_YAZILI(sandbox_state):
    """B3 ÖNERİSİNİN ÖLÇÜLEN KUSURU — susturulmuyor, ADLANDIRILIYOR.

    08-04'ün ikinci ayağı: beyan ZATEN silinmişken kitap defterin eski tabanına çekildi. Onarım
    DENKLEMİN İKİ TARAFINI birlikte taşıdığı için A = B = 0 ve satır YEŞİL kalır. Bu bir uygulama
    hatası değil, tek bir ANIN kimliğinin yapısal sınırıdır; bu test o sınırı ÇİVİLER ki yarın
    biri "taban dedektörümüz var" diye okumasın."""
    store.write_jsonl("trades.jsonl", [_islem(0, -5542.09)])
    store.write_json("portfolio.json", {"cash": 94457.91, "realized_pnl": -5542.09,
                                        "positions": {}})          # beyan YOK, taban geri çekilmiş
    rows = {r["check"]: r for r in recompute.report()["rows"]}
    assert rows["taban_kaymasi"]["ok"] is True, "satır beklenmedik biçimde ötüyor"
    assert rows["realized_pnl"]["ok"] is True                       # üç kimlik de yeşil (v213)
    assert rows["cash_identity"]["ok"] is True


def test_SB3_monotonluk_sayaci_TERS_ONARIMI_ayni_dongude_yakalar(sandbox_state):
    """SATIR O GÜN ÖTMELİYDİ — ve öten satır BUDUR. Zımni taban normal işletimde SABİTTİR (kapanan
    her işlem iki tarafı eşit artırır) ve yalnız bir BEYANLA yükselir; düşmesi tanım gereği
    beyansız bir taban kaymasıdır. 08-04: 5.542,09 → 0,0."""
    store.write_jsonl("trades.jsonl", [_islem(0, -5542.09)])
    store.write_json("portfolio.json", {
        "cash": 100000.0, "realized_pnl": 0.0, "positions": {}, "last_date": "2026-08-03",
        "peak_equity": 100000.0,
        "sermaye_resetleri": [{"id": "R1", "ts": "2026-08-01", "ofset": 5542.09, "neden": "reset"}]})
    ilk = watchdog.monotonicity_report(persist=True)
    assert ilk["tracked"] and store.read_json(watchdog.MONOTONIC_FILE, {})["sermaye_taban"] \
        == pytest.approx(5542.09, abs=0.01)

    # TERS ONARIM (beyan zaten silinmiş + kitap eski tabana çekilmiş — 08-04 21:47:54 hâli)
    store.write_json("portfolio.json", {"cash": 94457.91, "realized_pnl": -5542.09,
                                        "positions": {}, "last_date": "2026-08-04",
                                        "peak_equity": 100000.0})
    rep = watchdog.monotonicity_report()
    alanlar = {r["field"]: r for r in rep["regressions"]}
    assert "sermaye_taban" in alanlar, f"taban kayması görülmedi: {rep['regressions']}"
    assert alanlar["sermaye_taban"]["was"] == pytest.approx(5542.09, abs=0.01)
    assert alanlar["sermaye_taban"]["now"] == pytest.approx(0.0, abs=0.01)


def test_SB3_kapanan_islem_tabani_OYNATMAZ(sandbox_state):
    """YANLIŞ-ALARM KAPISI: normal işletim (bir işlem daha kapandı) sayacı kıpırdatmamalı, yoksa
    dedektör her seans öter ve susturulur."""
    store.write_jsonl("trades.jsonl", [_islem(0, -300.0)])
    store.write_json("portfolio.json", {"cash": 99700.0, "realized_pnl": -300.0, "positions": {}})
    watchdog.monotonicity_report(persist=True)
    store.write_jsonl("trades.jsonl", [_islem(0, -300.0), _islem(1, -400.0)])
    store.write_json("portfolio.json", {"cash": 99300.0, "realized_pnl": -700.0, "positions": {}})
    rep = watchdog.monotonicity_report()
    assert not [r for r in rep["regressions"] if r["field"] == "sermaye_taban"]


# =================================================================================================
# Ç1 — EQUITY_CURVE DÜRÜSTLÜĞÜ
# =================================================================================================
def _canli_defter(n: int = 45, dd_pnl: float = -300.0) -> list:
    out = []
    for i in range(n):
        kazanan = i % 3 != 2
        out.append(_islem(i, 900.0 if kazanan else dd_pnl, kapanis="2026-07-20"))
    return out


def test_C1_seri_donemi_KAPSIYORSA_davranis_BIREBIR_eskisi_gibi(sandbox_state):
    """REGRESYON ÇİVİSİ: eğri kitabın seansını kapsıyorsa iki bacak da ölçülür ve KÖTÜ olan
    seçilir — yani mevcut yasa bir hane bile oynamadı."""
    store.write_jsonl("trades.jsonl", _canli_defter())
    store.write_json("equity_curve.json", {"version": 4, "points": [
        ["2026-07-01", 100000.0], ["2026-07-20", 85000.0]]})       # %15 m2m düşüşü
    store.write_json("portfolio.json", {"cash": 100000.0, "last_date": "2026-07-20"})
    dd = analytics._realized_drawdown()
    assert dd["donem_kapsami"] == "kapsiyor" and dd["m2m_durum"] == "olculdu"
    assert dd["gunluk_m2m_dd"] > dd["kapali_islem_dd"]
    assert dd["max_dd"] == dd["gunluk_m2m_dd"] and dd["max_dd_alt_sinir"] is False


def test_C1_BAYAT_seri_m2m_bacagini_OLCULEMEDI_yapar_sayiyi_GIZLEMEZ(sandbox_state):
    """CANLI VAKANIN FİKSTÜRÜ (2026-08-08 21:52Z): seri 2026-07-20'de donmuş, kitap ilerlemiş.
    Bayat seriyle "kötüsü" HESAPLANMAZ; ama görülen sayı `bayat_seri_dd`de ADIYLA durur."""
    store.write_jsonl("trades.jsonl", _canli_defter())
    store.write_json("equity_curve.json", {"version": 4, "points": [
        ["2023-01-12", 100000.0], ["2026-07-20", 94457.91]]})
    store.write_json("portfolio.json", {"cash": 99549.62, "last_date": "2026-08-07"})
    dd = analytics._realized_drawdown()
    assert dd["donem_kapsami"] == "kapsamiyor" and dd["m2m_durum"] == "donem_disi"
    assert dd["gunluk_m2m_dd"] is None, "bayat seri m2m bacağı gibi raporlanıyor"
    assert dd["bayat_seri_dd"] is not None, "görülen sayı GİZLENMİŞ — hüküm denetlenemez olur"
    assert dd["seri_donem"] == ["2023-01-12", "2026-07-20"] and dd["defter_seansi"] == "2026-08-07"
    assert dd["max_dd"] == dd["kapali_islem_dd"] and dd["max_dd_alt_sinir"] is True


def test_C1_alt_sinir_esigi_gecse_bile_GECTI_DENMEZ(sandbox_state):
    """ÖLÇÜLEMEYEN BACAK 0 SAYILMAZ. Kapanmış bacak eşiğin altında ama m2m bacağı yoksa gerçek
    düşüş bundan yalnız KÖTÜ olabilir → hüküm `olculemedi`, `gecti` DEĞİL."""
    store.write_jsonl("trades.jsonl", _canli_defter(dd_pnl=-100.0))     # sığ kapanmış düşüş
    store.write_json("equity_curve.json", {"version": 4, "points": [
        ["2026-06-01", 100000.0], ["2026-06-30", 99000.0]]})
    store.write_json("portfolio.json", {"cash": 100000.0, "last_date": "2026-07-20"})
    dd = analytics._realized_drawdown()
    assert dd["max_dd"] <= analytics.EDGE_MAXDD_MAX and dd["max_dd_alt_sinir"] is True
    k = analytics.edge_verdict()["criteria"]["kuyruk"]
    assert k["status"] == "olculemedi" and k["dd_bacagi"] is None
    r = analytics.result_verdict()["criteria"]["maks_dusus"]
    assert r["status"] == "olculemedi" and r["value"] == dd["max_dd"]


def test_C1_alt_sinir_esigi_ASIYORSA_hukum_KESINDIR(sandbox_state):
    """Eksik bacak hükmü İYİLEŞTİREMEZ: alt sınır zaten tavanı aşıyorsa "kaldı" kesindir ve
    ölçülemedi'ye kaçmak, bilinen bir başarısızlığı belirsizliğe gömmek olurdu."""
    store.write_jsonl("trades.jsonl", [_islem(i, -300.0) for i in range(45)])
    store.write_json("equity_curve.json", {"version": 4, "points": [
        ["2026-06-01", 100000.0], ["2026-06-30", 99000.0]]})
    store.write_json("portfolio.json", {"cash": 90000.0, "last_date": "2026-07-20"})
    dd = analytics._realized_drawdown()
    assert dd["max_dd_alt_sinir"] is True and dd["max_dd"] > analytics.EDGE_MAXDD_MAX
    assert analytics.edge_verdict()["criteria"]["kuyruk"]["status"] == "kaldi"
    assert analytics.result_verdict()["criteria"]["maks_dusus"]["status"] == "kaldi"


def test_C1_kitabin_seansi_OKUNAMAZSA_seri_bayat_SAYILMAZ(sandbox_state):
    """Kuramadığımız bir dönemin dışında olmakla suçlamak, dedektörün KENDİ körlüğünü bulguya
    çevirmek olurdu (dördüncü kovanın "tarama kendi körlüğünü üretti" dersi)."""
    store.write_jsonl("trades.jsonl", _canli_defter())
    store.write_json("equity_curve.json", {"version": 4, "points": [
        ["2026-01-01", 100000.0], ["2026-01-02", 85000.0]]})
    dd = analytics._realized_drawdown()                             # portfolio.json YOK
    assert dd["donem_kapsami"] == "olculemedi" and dd["m2m_durum"] == "olculdu"
    assert dd["max_dd_alt_sinir"] is False


def test_C1_ESIKLER_OYNAMADI(sandbox_state):
    """Bu iş bir EŞİK OYNATMA DEĞİLDİR. Üç kaynak hâlâ birebir aynı sayıda (v119'un çivisi)."""
    assert analytics.EDGE_MAXDD_MAX == analytics.RESULT_MAXDD_MAX == \
        float(config.goal()["max_drawdown"]) == 0.08


def test_C1_equity_curve_bayatlik_bekcisine_KAYITLI(sandbox_state):
    """İKİNCİL KAPAMA: `DERIVED_SOURCES` bu depodaki tek genel bayatlık dedektörüdür ve eğri onun
    listesinde YOKTU. Kaynak `trades.jsonl`dir (portfolio.json DEĞİL — kitabın beş yazarı var ve
    çoğu eğriyle ilgisiz)."""
    assert watchdog.DERIVED_SOURCES.get("equity_curve.json") == ["trades.jsonl"]
    store.write_jsonl("trades.jsonl", _canli_defter())
    store.write_json("equity_curve.json", {"version": 4, "points": [["2026-01-01", 1.0]]})
    import os
    import time
    yol = config.STATE / "trades.jsonl"
    t = time.time()
    os.utime(yol, (t, t))                                            # kaynak ilerledi
    os.utime(config.STATE / "equity_curve.json",
             (t - 10 * 3600, t - 10 * 3600))                         # türev durdu
    bayat = {s["artifact"] for s in watchdog.coherence_report()["stale"]}
    assert "equity_curve.json" in bayat


# =================================================================================================
# Ç5 — DERISK_FLOOR_DD ve DD_VETO_MARGIN TEST-KAYNAKLI BAĞ
# =================================================================================================
def test_C5_derisk_floor_dd_goal_max_drawdown_ile_AYNI_SAYIDIR():
    """AİLE #8'İN EN TEHLİKELİ UCU (CIFT-KAYNAK §4.9): `goal.max_drawdown`ın kodda üç kopyası var;
    ikisi (`EDGE_MAXDD_MAX`, `RESULT_MAXDD_MAX`) goal'a test-kaynaklı BAĞLI, üçüncüsü değildi. Ve
    üçüncüsü diğer ikisinden farklı bir şey yapıyor: onlar bir HÜKÜM eşiği, bu bir EMİR BOYUTU —
    `derisk_mult` canlı pozisyon adedini bu sayıdan üretir (broker.py:213-224). Operatör
    `goal.max_drawdown`ı değiştirirse iki hüküm eşiği testle takip ederdi, boyutlama rampası
    YERİNDE KALIRDI. Emsal: tests/test_hafta3a_v119.py:78 (aynı desen, aynı gerekçe).
    `broker.py` DEĞİŞTİRİLMEDİ — bağ TESTTEN kurulur, çünkü sabitin kod tarafındaki gerekçesi
    (rampanın üst ucu) yerinde ve doğru; eksik olan yalnız kapıydı."""
    assert broker.DERISK_FLOOR_DD == float(config.goal()["max_drawdown"]), \
        "boyutlama rampasının tabanı goal.max_drawdown'dan AYRIŞTI — emir boyutu sessizce kaydı"
    assert broker.DERISK_FLOOR_DD == analytics.EDGE_MAXDD_MAX == analytics.RESULT_MAXDD_MAX


def test_C5_derisk_rampasi_tabanda_SIFIR_boyut_verir():
    """Bağın DAVRANIŞSAL yarısı: sayı eşitliği tek başına bir iddiadır; rampanın o sayıda
    gerçekten kapandığı ölçülür (yoksa sabit doğru, tüketici yanlış olabilirdi)."""
    tepe = 100_000.0
    tabanda = tepe * (1.0 - broker.DERISK_FLOOR_DD)
    assert broker.derisk_mult(tabanda, tepe) == 0.0
    assert broker.derisk_mult(tabanda * 0.99, tepe) == 0.0
    assert broker.derisk_mult(tepe, tepe) == 1.0


def test_C5_dd_veto_margin_goalun_TAM_YARISIDIR():
    """`shadowlaw.DD_VETO_MARGIN` kendi yorumunda "goal.max_drawdown'un YARISI" diye YAZILI ama
    hiçbir test onu bağlamıyordu — CIFT-KAYNAK §1.2'nin "kalıntı kusur" başlığı tam bu sınıfı
    anlatıyor: yorumsuz (ya da yalnız yorumlu) bir yarı-türev taramadan sessizce geçer."""
    assert shadowlaw.DD_VETO_MARGIN == pytest.approx(
        float(config.goal()["max_drawdown"]) / 2.0), \
        "düşüş vetosu marjı goal bütçesinin yarısı olmaktan çıktı (kaynak yorumu bunu İDDİA EDİYOR)"


# =================================================================================================
# #10 — MUTABAKAT TAZELİĞİ
# =================================================================================================
@pytest.fixture
def ayna_acik(monkeypatch):
    monkeypatch.setattr(config, "BROKER", "alpaca_paper")
    watchdog._MUTABAKAT_ALARMED.clear()
    yield


def _reconcile(date: str, updated: str, **ek) -> None:
    store.write_json("broker_reconcile.json",
                     {"date": date, "updated": updated, "checked": True, "api_ok": True, **ek})


def test_10_kayit_kitabin_SEANSININ_gerisindeyse_BAYAT(sandbox_state, ayna_acik, monkeypatch):
    """ASIL ÖLÇÜ SEANS KIYASIDIR: kitap yeni bir seansı işlediyse ayna görünümü de o seansa ait
    olmalı. `EXPECTED["mirror_reconcile"]` penceresi 4 GÜN olduğu için 24,3 saatlik boşluk orada
    GÖRÜNMEZ (ölçüldü: CIFT-KAYNAK §4.5)."""
    import datetime as dt
    simdi = dt.datetime.now(dt.timezone.utc)
    _reconcile("2026-08-06", (simdi - dt.timedelta(hours=24.3)).isoformat(timespec="seconds"))
    store.write_json("portfolio.json", {"last_date": "2026-08-07"})
    rep = watchdog.mutabakat_tazelik_report()
    assert rep["ok"] is False and rep["seans_gerisinde"] is True and rep["yas_asildi"] is False
    assert rep["yas_h"] == pytest.approx(24.3, abs=0.2)
    kayit = []
    monkeypatch.setattr(obs, "alarm", lambda tok, msg, **kw: kayit.append((tok, msg)))
    watchdog.check_mutabakat_and_alarm()
    watchdog.check_mutabakat_and_alarm()                            # mandal: ikinci kez susar
    assert len(kayit) == 1 and kayit[0][0] == "MECHANISM_STALE"
    assert "BAYAT MUTABAKAT" in kayit[0][1]


def test_10_ayni_seans_TAZEDIR(sandbox_state, ayna_acik):
    import datetime as dt
    _reconcile("2026-08-07", dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"))
    store.write_json("portfolio.json", {"last_date": "2026-08-07"})
    assert watchdog.mutabakat_tazelik_report()["ok"] is True


def test_10_mutlak_tavan_arka_duvardir(sandbox_state, ayna_acik):
    """Seans kıyası tek başına yetmez: kitap da durmuşsa (ikisi birden) göreli her ölçü yeşil
    kalırdı. Mutlak tavan `EXPECTED["mirror_reconcile"]` ile AYNI sayıdır — bilerek."""
    import datetime as dt
    eski = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=5)
    _reconcile("2026-08-07", eski.isoformat(timespec="seconds"))
    store.write_json("portfolio.json", {"last_date": "2026-08-07"})
    rep = watchdog.mutabakat_tazelik_report()
    assert rep["ok"] is False and rep["yas_asildi"] is True and rep["seans_gerisinde"] is False
    assert watchdog.MUTABAKAT_MAX_YAS_S == watchdog.EXPECTED["mirror_reconcile"]


def test_10_kayit_YOKSA_olculemedi_TAZE_degil(sandbox_state, ayna_acik):
    rep = watchdog.mutabakat_tazelik_report()
    assert rep["ok"] is None and rep["olculemedi"] is True and "ÖLÇÜLEMEDİ" in rep["neden"]


def test_10_ayna_kapaliysa_KAPSAM_DISI_alarm_YOK(sandbox_state, monkeypatch):
    """Referansı olmayan bir soruyu her poll'da alarmlamak, EEMUA bütçesini bir YAPILANDIRMA
    hâliyle doldurmak olurdu (#8 korumanın aynı gerekçesi)."""
    monkeypatch.setattr(config, "BROKER", "internal")
    kayit = []
    monkeypatch.setattr(obs, "alarm", lambda tok, msg, **kw: kayit.append(tok))
    rep = watchdog.check_mutabakat_and_alarm()
    assert rep["kapsam_disi"] is True and not kayit


def test_10_TAZE_ama_checked_False_bir_ayna_gorunumu_DEGILDIR(sandbox_state, ayna_acik):
    """`loop._skip` dalı kaydı TAZE yazar ama içinde mutabakat YOKTUR. Rapor `checked`/`api_ok`/
    `skip_reason`ı her hâlde taşır ki okuyucu ikisini karıştırmasın."""
    import datetime as dt
    store.write_json("broker_reconcile.json", {
        "date": "2026-08-07", "checked": False, "skip_reason": "paper_available()=False",
        "updated": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")})
    store.write_json("portfolio.json", {"last_date": "2026-08-07"})
    rep = watchdog.mutabakat_tazelik_report()
    assert rep["ok"] is True                                        # TAZELİK hükmü: taze
    assert rep["checked"] is False and rep["skip_reason"] == "paper_available()=False"


# =================================================================================================
# #7 — CONFTEST BEKÇİSİ (v215 sızıntısının SINIF kapaması)
# =================================================================================================
def test_7_conftest_tabani_alpaca_TRANSPORT_ve_obs_SUPPRESS_LOGGED_icerir():
    """Kayıt (modül, öznitelik) çiftleriyle tutulur ve taban modülün KENDİ literalinden okunur —
    elle yazılmış bir kopya değil (2026-08-02 dersi: kopya, üretim tarafına eklenen alanla
    sessizce eskir)."""
    from tests import conftest as ct
    izlenen = {f"{m.__name__}.{a}" for m, a in ct._MODUL_DURUMLARI}
    assert "meridian.adapters.alpaca._TRANSPORT" in izlenen
    assert "meridian.obs._SUPPRESS_LOGGED" in izlenen
    assert ct._MODUL_DURUMU0["meridian.adapters.alpaca._TRANSPORT"]["ok"] is True
    assert ct._MODUL_DURUMU0["meridian.obs._SUPPRESS_LOGGED"] == {}


def test_7_kirletilen_tasima_kaydi_YERINDE_geri_alinir():
    """YERİNDE (clear+update), YENİ DICT ATAYARAK DEĞİL: `alpaca._note` globali kapatma yoluyla
    tutar, yeni bir nesne bağlamak sıfırlamayı hiçbir şeye dokunmamış hâle getirirdi
    (`_fmp._HEALTH` dersi, 2026-07-26)."""
    from tests import conftest as ct
    kimlik = id(alpaca._TRANSPORT)
    alpaca._TRANSPORT.update({"ok": False, "error": "sahte kesinti", "consecutive_fails": 3})
    obs._SUPPRESS_LOGGED["MIRROR_DRIFT"] = 1.0
    ct._clear_module_caches()
    assert alpaca._TRANSPORT["ok"] is True and alpaca._TRANSPORT["error"] == ""
    assert alpaca._TRANSPORT["consecutive_fails"] == 0
    assert obs._SUPPRESS_LOGGED == {}
    assert id(alpaca._TRANSPORT) == kimlik, "yeni dict atanmış — dış referanslar koptu"


def test_7_sizinti_reconcile_yolunu_ARTIK_kirletemez(sandbox_state, monkeypatch):
    """SIZINTININ ÖLÇÜLEN SONUCU (2026-08-08, otoriter suite): `loop.reconcile_broker_state`
    `alpaca.orders`/`positions` yamalanmış OLSA BİLE `alpaca.transport()["ok"]`i AYRICA sınar ve
    False görünce mutabakatı ERKEN döndürür. Kirli bir taşıma kaydı devralan bir test, kendi
    kurmadığı bir arızayla karşılaşırdı."""
    from tests import conftest as ct
    alpaca._TRANSPORT.update({"ok": False, "error": "önceki dosyadan devredildi"})
    assert alpaca.transport()["ok"] is False
    ct._clear_module_caches()
    assert alpaca.transport()["ok"] is True


# =================================================================================================
# W2 DEVRİ — LOOK-AHEAD DAMGA DENETİMİNİN KAPSAMI (Rol-1 ek kalemi, 2026-08-09)
# =================================================================================================
def test_W2_intraday_damga_kapsami_IKI_GOLGE_DEFTERINI_de_icerir():
    """Planlı kol AYRI bir deftere yazıyor (kill#3: silahli kolun defteri bayt-değişmez kalmalı).
    Kapsam listesi güncellenmeseydi look-ahead denetimi yeni kolu HİÇ taramazdı — ve kolun var olma
    sebebi tam da NÜFUS olduğu için denetlenmeyen satır sayısı büyüyecek olan taraftı.

    TUPLE İKİ MODÜL SABİTİYLE KIYASLANIR: `watchdog` adları literal tutar (import maliyeti), yani
    "aynı gerçek iki yerde" sınıfı buraya sızabilir. Kapı bu satırdır — sabit değişirse burası
    kırmızı yanar."""
    from meridian import intraday_shadow
    assert intraday_shadow.ORDERS_FILE in watchdog.INTRADAY_STAMP_LEDGERS
    assert intraday_shadow.PLANLI_ORDERS_FILE in watchdog.INTRADAY_STAMP_LEDGERS
    assert set(watchdog.INTRADAY_STAMP_LEDGERS) == {
        "intraday_decisions.jsonl", intraday_shadow.ORDERS_FILE,
        intraday_shadow.PLANLI_ORDERS_FILE}


def test_W2_planli_defterdeki_LOOK_AHEAD_satiri_yakalanir(sandbox_state):
    """Kapsam bir İDDİA değil: planlı deftere `decision_as_of < close_ts` taşıyan bir satır
    konulduğunda denetim onu ADIYLA düşürmeli (üç damganın şeması iki kolda birebir aynı —
    `intraday_shadow._satir` tek gövde)."""
    from meridian import intraday_shadow
    store.write_jsonl(intraday_shadow.PLANLI_ORDERS_FILE, [{
        "plan_id": "P-2026-08-08-AAA", "ticker": "AAA", "date": "2026-08-08", "kol": "planli",
        "status": "would_submit", "bar_t": "2026-08-08T14:30:00+00:00",
        "decision_as_of": "2026-08-08T14:29:00+00:00",       # KAPANIŞTAN ÖNCE → look-ahead
        "close_ts": "2026-08-08T14:31:00+00:00"}])
    rep = watchdog.intraday_stamp_report()
    satir = next(r for r in rep["rows"] if r["ledger"] == intraday_shadow.PLANLI_ORDERS_FILE)
    assert satir["ok"] is False and satir["violations"] == 1
    assert "LOOK-AHEAD" in satir["detail"] and "AAA" in satir["detail"]
    assert rep["ok"] is False


def test_W2_planli_defter_BOS_ihlal_DEGILDIR(sandbox_state):
    """"Damga tutmuyor" ile "denetlenecek satır yok" AYRI hükümlerdir — yeni kol daha ilk gününde
    sahte kırmızı yakmamalı (mevcut iki defterin sözleşmesiyle birebir aynı)."""
    from meridian import intraday_shadow
    rep = watchdog.intraday_stamp_report()
    satir = next(r for r in rep["rows"] if r["ledger"] == intraday_shadow.PLANLI_ORDERS_FILE)
    assert satir["ok"] is True and satir["rows"] == 0 and "defter boş" in satir["detail"]


# =================================================================================================
# ALARM BÜTÇESİ (EEMUA) — YENİ DEDEKTÖRLER BÜTÇEYİ YEMİYOR
# =================================================================================================
def test_alarm_butcesi_yeni_dedektorler_mandalli(db_kitap, monkeypatch, ayna_acik):
    """ROADMAP WP-P: ≤10 alarm/gün. İki yeni dedektör de MANDALLI — bir olgu, bir satır. 300 sn'lik
    poll günde 288 kez koşar; mandalsız bir dedektör tek başına bütçeyi 28 katına çıkarırdı."""
    import datetime as dt
    store.write_json("portfolio.json", {"cash": 100000.0, "last_date": "2026-08-07"})
    watchdog.check_kitap_damga_and_alarm()
    _db_disi_yazim({"cash": 94457.91, "last_date": "2026-08-07"})
    _reconcile("2026-08-06", (dt.datetime.now(dt.timezone.utc)
                              - dt.timedelta(hours=30)).isoformat(timespec="seconds"))
    kayit = []
    monkeypatch.setattr(obs, "alarm", lambda tok, msg, **kw: kayit.append(tok))
    watchdog._DAMGA_ALARMED.clear()
    for _ in range(12):                                              # bir saatlik poll dizisi
        watchdog.check_kitap_damga_and_alarm()
        watchdog.check_mutabakat_and_alarm()
    assert len(kayit) == 2, f"mandal tutmadı, {len(kayit)} alarm üretildi"
    assert sorted(kayit) == ["DATA_QUALITY", "MECHANISM_STALE"]
