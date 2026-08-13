"""test_ogrenme_katmani_durmasi_v235.py — ÖĞRENME KATMANI DURMASI zinciri (2026-08-12 canlı vakası).

CANLI SEMPTOM ZİNCİRİ (üç alarm ailesi TEK zincir):
    hermes canlı-araması asılı → `SEARCH_PROGRESS.running=True` günlerce değişmeden kaldı →
    `sprint_cadence_skip sebep=mesgul:canli_arama` her döngüde (4+ gün) → sprint çocuğu çoktan ölü
    (pid yok, faz='baseline' terminal değil = YETİM) ama kadans onu yeniden başlat(a)mıyordu →
    9,6 gündür yeni hipotez yok (MECHANISM_STALE "ÖĞRENME DURDU").

İKİ DÜZELTME (sprint.py, v235):
    (1) ARAMA BAYRAĞI BAYATLIK YASASI: bayrak `running=True` VE parmak izi ARAMA_BAYAT_SAAT (6 sa)
        boyunca değişmemişse arama asılı/ölü sayılır — olay (`sprint_arama_bayragi_bayat`) düşer,
        bayrak 'bayat_temizlendi' ile işaretlenir, kadans kilidi açılır. İlerleyen (parmak izi
        değişen) bir arama ASLA bayat okunmaz. Skip olayı artık bayrak yaşını taşır.
    (2) YETİM TETİĞİ: pid ölü + faz terminal değil → yetim koşu "koştu" SAYILMAZ; kadans, yetim
        başlangıç YETIM_YENIDEN_SAAT'i (12 sa — çökme döngüsü freni) aştığında uygun ilk gece
        penceresinde YENİDEN başlatır (sebep=yetim_sprint_yeniden). Tespit olaylıdır, episode
        başına bir kez (`sprint_yetim_tespit`).

S5 (sermaye_taban 0,01 GERİLEME): `sermaye.sermaye_taban` — zımni tabanın SENT-TAM kanonik
türetimi. Aynı defter iki yoldan yazılınca sonuç bit-bit aynıdır (yanlış alarm yok); GERÇEK
1-sentlik gerileme yine alarmlar. Karşılaştırma epsilon'u BİLEREK yok.

CANLI STATE'E YAZILMAZ: her test `sandbox_state` içinde koşar; hiçbir test alt süreç başlatmaz
(meşguliyet/monkeypatch kapıları bunu garanti eder — v136'daki 22:00 kazası dersi).
"""
from __future__ import annotations

import datetime as dt
import random

import pytest

from meridian import sermaye, sprint, store

UTC = dt.timezone.utc
GECE = dt.datetime(2026, 8, 12, 23, 0, tzinfo=UTC)          # pencere içi (22→06), tz-AWARE
OLU_PID = 999999


def _iso(t: dt.datetime) -> str:
    return t.isoformat(timespec="seconds")


def _temiz(monkeypatch, progress: dict | None = None) -> None:
    """Süreç-içi gözlem defterlerini test başına sıfırla (monkeypatch geri alır) ve arama
    bayrağını kur. Sıfırlamadan önceki testin gözlemi sonrakine sızardı (sıra bağımlılığı)."""
    from meridian import hermes
    monkeypatch.setattr(sprint, "_ARAMA_GOZLEM", {"iz": None, "beri": None, "olayli": False})
    monkeypatch.setattr(sprint, "_YETIM_OLAYLI", set())
    monkeypatch.setattr(hermes, "SEARCH_PROGRESS", dict(progress or {}), raising=False)


def _olaylar(ad: str) -> list[dict]:
    return [e for e in store.read_jsonl("events.jsonl") if e.get("event") == ad]


# ==================================================================================================
# (1) ARAMA BAYRAĞI — bayatlık yasası
# ==================================================================================================
def test_taze_bayrak_mesgul_ve_yas_tasir(sandbox_state, monkeypatch):
    """TAZE bayrak (ilk gözlem) MEŞGULDÜR — mevcut davranış korunur; karar artık bayrak yaşını da
    taşır (skip olayına çıkan alanın kaynağı)."""
    _temiz(monkeypatch, {"running": True, "phase": "probing", "i": 2, "total": 10})
    karar = sprint.should_run(now=GECE)
    assert karar["kos"] is False and karar["sebep"] == "mesgul:canli_arama", karar
    ab = karar["arama_bayragi"]
    assert ab["mesgul"] is True and ab["bayat"] is False
    assert ab["yas_sa"] is not None and ab["yas_sa"] < 0.01, ab


def test_ilerleyen_arama_ASLA_bayat_okunmaz(sandbox_state, monkeypatch):
    """PARMAK İZİ DEĞİŞİYORSA arama CANLIDIR: 7 saat sonra bile (eşik 6 sa) i ilerlemişse gözlem
    sıfırlanır ve bayrak MEŞGUL kalır — canlı bir aramayı 'asılı' diye ezmek, tam da bu yasanın
    yasakladığı ikinci hatadır (8 çekirdeği ikiye bölerdik)."""
    from meridian import hermes
    _temiz(monkeypatch, {"running": True, "phase": "probing", "i": 2, "total": 10})
    assert sprint.should_run(now=GECE)["sebep"] == "mesgul:canli_arama"
    hermes.SEARCH_PROGRESS["i"] = 3                            # arama gerçekten ilerledi
    karar = sprint.should_run(now=GECE + dt.timedelta(hours=7))
    assert karar["sebep"] == "mesgul:canli_arama", karar
    assert karar["arama_bayragi"]["bayat"] is False
    assert not _olaylar("sprint_arama_bayragi_bayat"), "ilerleyen arama bayat olayı üretti"


def test_bayat_bayrak_kilidi_ACAR_olayli_temizlenir_tek_olay(sandbox_state, monkeypatch):
    """CANLI VAKANIN ÇEKİRDEĞİ: parmak izi 6+ saat değişmeyen `running=True` bayrağı ARTIK kadansı
    kilitleyemez. Bayatlık (a) olaylıdır, (b) bayrağı panoya da dürüst işaretler
    ('bayat_temizlendi'), (c) episode başına TEK olay üretir — ve kilit açılınca haftalık taban
    tetiği GERÇEKTEN yanar (öğrenme kendine gelir)."""
    from meridian import hermes
    # Son (ölü DEĞİL, normal bitmiş) sprint 8 gün önce → kilit açılınca haftalık taban tetiklenmeli.
    store.write_json(sprint.STATUS_FILE,
                     {"started_at": _iso(GECE - dt.timedelta(days=8)),
                      "n_hyp_at_start": 0, "phase": "done"})
    _temiz(monkeypatch, {"running": True, "phase": "incumbent", "i": 0})
    assert sprint.should_run(now=GECE)["sebep"] == "mesgul:canli_arama"     # gözlem başlar
    karar = sprint.should_run(now=GECE + dt.timedelta(hours=6, minutes=30))  # 05:30 — pencere içi
    ab = karar["arama_bayragi"]
    assert ab["bayat"] is True and ab["mesgul"] is False, ab
    assert karar["kos"] is True and karar["sebep"] == "haftalik_taban", karar
    # bayrak panoda da dürüst: hermes_runtime aynı sözlüğü render eder
    assert hermes.SEARCH_PROGRESS.get("running") is False
    assert hermes.SEARCH_PROGRESS.get("phase") == "bayat_temizlendi"
    olay = _olaylar("sprint_arama_bayragi_bayat")
    assert len(olay) == 1 and olay[0]["yas_sa"] >= sprint.ARAMA_BAYAT_SAAT, olay
    # üçüncü çağrı: bayrak artık running=False → yeni olay YOK (episode kapandı)
    sprint.should_run(now=GECE + dt.timedelta(hours=6, minutes=40))
    assert len(_olaylar("sprint_arama_bayragi_bayat")) == 1, "bayat olayı episode başına 1 olmalı"


def test_skip_olayi_bayrak_yasini_tasir(sandbox_state, monkeypatch):
    """`sprint_cadence_skip` olayı artık bayrak yaşını taşır — canlıdaki 4 günlük
    'mesgul:canli_arama' döngüsünde İLK bakışta 'bayrak kaç saattir asılı?' okunabilsin."""
    _temiz(monkeypatch, {"running": True, "phase": "probing", "i": 1})
    baslatilan = []
    monkeypatch.setattr(sprint, "start", lambda cfg=None: baslatilan.append(cfg) or {"started": True})
    r = sprint.maybe_start()
    assert r["started"] is False and baslatilan == []
    skip = _olaylar("sprint_cadence_skip")
    assert skip and skip[-1]["sebep"] == "mesgul:canli_arama", skip
    assert skip[-1].get("arama_bayrak_yasi_sa") is not None, "skip olayı bayrak yaşını taşımıyor"
    assert skip[-1].get("arama_bayat") is False


# ==================================================================================================
# (2) YETİM SPRINT — kadans kendini toparlar
# ==================================================================================================
def _yetim_kur(monkeypatch, *, started_hours_ago: float, faz: str = "baseline", sid: str = "yt1"):
    _temiz(monkeypatch, {})
    store.write_json(sprint.STATUS_FILE,
                     {"pid": OLU_PID, "sid": sid, "phase": faz, "progress": 281, "total": 527,
                      "started_at": _iso(GECE - dt.timedelta(hours=started_hours_ago)),
                      "n_hyp_at_start": 0})


def test_yetim_gece_penceresinde_YENIDEN_baslatilir(sandbox_state, monkeypatch):
    """CANLI VAKA (S1): pid ölü, faz='baseline', 4+ gündür duruyor — haftalık taban 7 günü
    beklemeden (gun=2 < 7, taze=0) yetim tetiği yanar: kadans antrenmanı YENİDEN başlatabilir."""
    _yetim_kur(monkeypatch, started_hours_ago=48)
    karar = sprint.should_run(now=GECE)
    assert karar["yetim"] is True and karar["gecen_gun"] == 2, karar
    assert karar["kos"] is True and karar["sebep"] == "yetim_sprint_yeniden", karar


def test_yetim_freni_cokme_dongusunu_keser(sandbox_state, monkeypatch):
    """FREN: aynı gece başlayıp hemen ölen çocuk 5 dakikada bir yeniden doğamaz — yetim tetiği
    ancak başlangıç YETIM_YENIDEN_SAAT'ten (12 sa) eskiyse yanar. Taze yetim: tetik YOK."""
    _yetim_kur(monkeypatch, started_hours_ago=1)
    karar = sprint.should_run(now=GECE)
    assert karar["yetim"] is True and karar["yetim_saat"] == 1.0, karar
    assert karar["kos"] is False and karar["sebep"].startswith("tetik_yok"), karar


def test_yetim_gunduz_pencereye_saygili(sandbox_state, monkeypatch):
    """Yetim tetiği SAAT PENCERESİNİ delmez: 4 işçilik antrenmanı gündüz başlatmak, canlı
    kararların makinesini doyurmaktır (kadansın kendi gerekçesi)."""
    _yetim_kur(monkeypatch, started_hours_ago=48)
    karar = sprint.should_run(now=dt.datetime(2026, 8, 12, 14, 0, tzinfo=UTC))
    assert karar["yetim"] is True
    assert karar["kos"] is False and karar["sebep"] == "saat_dilimi_disinda", karar


def test_terminal_faz_yetim_tetigi_uretmez(sandbox_state, monkeypatch):
    """Ölü pid + TERMİNAL faz NORMALDİR (iş bitti) — yetim tetiği yanmamalı, yoksa her biten
    sprint 12 saat sonra sebepsiz yeniden koşardı."""
    _yetim_kur(monkeypatch, started_hours_ago=48, faz="done")
    karar = sprint.should_run(now=GECE)
    assert karar["yetim"] is False
    assert karar["kos"] is False and karar["sebep"].startswith("tetik_yok"), karar


def test_yetim_tespiti_olayli_ve_episode_basina_tek(sandbox_state, monkeypatch):
    """Yetim tespiti SESSİZ DEĞİL (YASA 4): `sprint_yetim_tespit` düşer — ama episode (sid) başına
    BİR kez; 300 sn'lik poll'de her turda warn basmak alarmı gürültüye çevirirdi. Bir kapı yetimi
    başlatmayı engellese bile tespit görünür kalır.

    BEYANLI GÜNCELLEME (v239, 2026-08-13). Bu testin "başlatma yolu kapalı" kurulumu ESKİDEN canlı
    arama bayrağıydı (`SEARCH_PROGRESS.running=True`). v239 tam O KAPIYI kaldırdı ve gerekçesi
    ölçüldü: canlı arama bir YÜK sinyalidir ve yetim ZATEN ÖLÜ bir süreçtir; beyin zinciri ~5
    dakikada bir tur açtığı için bayrak asla bayatlamıyordu ve v235'in yetim-restart'ı ÖLÜ bir
    mekanizmaya dönüşmüştü (canlı: `sebep=mesgul:canli_arama, yetim=true, gecen_gun=5`). Testin
    ASIL iddiası (tespit olaylı + episode başına bir kez) DEĞİŞMEDİ; kapalı tutulan kapı, v239'un
    bilerek KORUDUĞU kapıyla değiştirildi: `elle_tik` bir YETKİ kapısıdır (2026-07-30'un ölçülmüş
    kazası) ve yetim onu delmez. Yani test zayıflatılmadı — hâlâ ayakta olan bir kapıya baktırıldı.
    Yeni kolun iki yönü `tests/test_sprint_yetim_yuk_kapisi_v239.py`de ayrıca çivilidir."""
    _yetim_kur(monkeypatch, started_hours_ago=48)
    from meridian import hermes
    hermes.SEARCH_PROGRESS.update(running=True, phase="probing", i=1)   # YÜK kapısı: artık delinir
    baslatilan = []
    monkeypatch.setattr(sprint, "start", lambda cfg=None: baslatilan.append(cfg) or {"started": True})
    sprint.maybe_start(mesgul="elle_tik")                      # YETKİ kapısı: yetimde de bloklar
    sprint.maybe_start(mesgul="elle_tik")
    assert baslatilan == [], "yetki kapısı (elle_tik) delindi — 2026-07-30 kazası geri gelmiş"
    olay = _olaylar("sprint_yetim_tespit")
    assert len(olay) == 1 and olay[0]["sid"] == "yt1", olay
    skip = _olaylar("sprint_cadence_skip")
    assert skip and skip[-1].get("yetim") is True, "skip olayı yetim bilgisini taşımıyor"
    assert skip[-1].get("sebep") == "mesgul:elle_tik", skip[-1]


def test_yetim_yeniden_baslatma_ucu_uca_status_temizlenir(sandbox_state, monkeypatch):
    """UÇTAN UCA: yetim tetiği → maybe_start GERÇEKTEN start()'a iner (monkeypatch'li) ve yeni
    sprint durumu yetimliği söker — kadans kendini TOPARLAR, operatör onarımı gerekmez."""
    _yetim_kur(monkeypatch, started_hours_ago=48, sid="yt-eski")
    monkeypatch.setattr(sprint, "SPRINT_HOURS", (0, 24))       # saatten bağımsız test (v136 dersi)
    baslatilan = []

    def _sahte_start(cfg=None):
        baslatilan.append(cfg)
        store.write_json(sprint.STATUS_FILE, {"pid": None, "sid": "yt-yeni", "phase": "starting",
                                              "started_at": _iso(GECE), "n_hyp_at_start": 0})
        return {"started": True, "sid": "yt-yeni"}

    monkeypatch.setattr(sprint, "start", _sahte_start)
    r = sprint.maybe_start()
    assert r.get("started") is True and baslatilan, r
    assert r["sebep"] == "yetim_sprint_yeniden"
    assert sprint.status()["orphan"] is False, "yeni başlangıç yetimliği sökmedi"


# ==================================================================================================
# S5 — sermaye_taban: kanonik sent-tam türetim
# ==================================================================================================
PNLS = [3.33, -1.11, 0.07, 2.50, -0.05, 10.10, -7.77, 0.01] * 12     # 96 sent-tam satır
TABAN = 5542.09                                                      # canlı vakanın beyan tabanı


def _kitap_yaz(pnls: list[float], *, taban: float = TABAN, ters: bool = False,
               karistir: int | None = None) -> None:
    """Aynı DEFTERİ farklı YOLDAN yaz: birikim sırası ve satır sırası değişir, ondalık içerik
    değişmez — 'aynı değer iki yoldan yazılınca' fikstürü."""
    sira = list(pnls)
    if ters:
        sira = sira[::-1]
    if karistir is not None:
        random.Random(karistir).shuffle(sira)
    realized = taban
    for p in sira:                                             # kayan-nokta birikimi, farklı sırayla
        realized += p
    store.write_json("portfolio.json", {"cash": 100000.0, "realized_pnl": realized})
    import json as _json
    from meridian import config as _cfg
    (_cfg.STATE / "trades.jsonl").write_text(
        "".join(_json.dumps({"id": i, "pnl_dollars": p}) + "\n" for i, p in enumerate(sira)))


def test_ayni_defter_iki_yoldan_bit_bit_ayni_ve_alarm_URETMEZ(sandbox_state):
    """ÇEKİRDEK: aynı ondalık defter iki farklı yazım yolundan (birikim + satır sırası) geçince
    kanonik taban BİT-BİT aynıdır → monotonluk kıyası (v < p) yanlış alarm ÜRETEMEZ. Temiz
    (sent-tam) defterde eski watchdog ifadesiyle de birebir aynıdır — tek satırlık yama planı
    (watchdog:1976) davranış değiştirmeden takılabilir."""
    _kitap_yaz(PNLS)
    v_once = sermaye.sermaye_taban()
    eski_ifade = round(
        float(store.read_json("portfolio.json", {})["realized_pnl"])
        - sum(float(t["pnl_dollars"]) for t in store.read_jsonl("trades.jsonl")), 2)
    assert v_once == TABAN == eski_ifade, (v_once, eski_ifade)
    _kitap_yaz(PNLS, ters=True)                                # yol 2: ters birikim
    v_sonra = sermaye.sermaye_taban()
    _kitap_yaz(PNLS, karistir=7)                               # yol 3: karışık sıra
    v_ucuncu = sermaye.sermaye_taban()
    assert v_once == v_sonra == v_ucuncu, "aynı defter, farklı yol → farklı taban (yuvarlama kırığı)"
    assert not (v_sonra < v_once), "yanlış GERİLEME alarmı üretirdi"


def test_gercek_gerileme_YINE_alarmlar(sandbox_state):
    """EŞİK GEVŞETİLMEDİ KANITI: gerçek 1-sentlik beyan silinmesi (realized_pnl −0,01) ve satır
    kaybı (negatif satır silinir) kanonik tabanı DÜŞÜRÜR → dedektörün v < p kuralı aynen yanar."""
    _kitap_yaz(PNLS)
    v_once = sermaye.sermaye_taban()
    pf = store.read_json("portfolio.json", {})
    store.write_json("portfolio.json", {**pf, "realized_pnl": float(pf["realized_pnl"]) - 0.01})
    v_sonra = sermaye.sermaye_taban()
    assert v_sonra < v_once and round(v_once - v_sonra, 2) == 0.01, (v_once, v_sonra)
    # satır kaybı: −7.77'lik satır silinirse Σ defter 7.77 artar → taban 7.77 düşer → alarm
    _kitap_yaz(PNLS)
    import json as _json
    from meridian import config as _cfg
    rows = [t for t in store.read_jsonl("trades.jsonl")]
    kayip = next(i for i, t in enumerate(rows) if t["pnl_dollars"] == -7.77)
    rows.pop(kayip)
    (_cfg.STATE / "trades.jsonl").write_text(
        "".join(_json.dumps(t) + "\n" for t in rows))
    assert sermaye.sermaye_taban() < v_once, "satır kaybı gerilemesi yutuldu"


def test_yarim_sent_tasiyan_kaynak_deterministik(sandbox_state):
    """(b) BACAĞININ BELGESİ: bugünkü broker dünyasında realized_pnl yarım-sent taşıyabilir
    (ham birikim, broker.py:569/595 — WP-E yama planı). Kanonik türetim o dünyada bile TEK ve
    satır-sırasından bağımsız bir değer verir (Σ sent-tam olduğu için tek oynak terim realized'ın
    kendisidir; onun sent değeri IEEE gereği o double için sabittir)."""
    store.write_json("portfolio.json", {"cash": 0.0, "realized_pnl": 5542.085})
    from meridian import config as _cfg
    (_cfg.STATE / "trades.jsonl").write_text("")
    v1 = sermaye.sermaye_taban()
    v2 = sermaye.sermaye_taban()
    beklenen = round(5542.085 * 100) / 100.0                   # IEEE-sabit tek değer
    assert v1 == v2 == beklenen, (v1, v2, beklenen)


def test_bozuk_satir_semantigi_watchdog_ile_birebir(sandbox_state):
    """Drop-in sözleşmesi: `pnl_dollars` None/eksik → 0 sayılır (watchdog `or 0.0` ile aynı);
    sayıya çevrilemeyen değer İSTİSNA fırlatır — watchdog kendi try'ında sayacı dürüstçe
    'okunamadı' diye kapatır, sahte bir 0 UYDURULMAZ."""
    import json as _json
    from meridian import config as _cfg
    store.write_json("portfolio.json", {"realized_pnl": 10.0})
    (_cfg.STATE / "trades.jsonl").write_text(
        _json.dumps({"id": 0, "pnl_dollars": None}) + "\n" + _json.dumps({"id": 1}) + "\n")
    assert sermaye.sermaye_taban() == 10.0
    (_cfg.STATE / "trades.jsonl").write_text(_json.dumps({"id": 0, "pnl_dollars": "abc"}) + "\n")
    with pytest.raises((TypeError, ValueError)):
        sermaye.sermaye_taban()


def test_durum_kanonik_tabani_yuzeyler(sandbox_state):
    """YASA 6: helper'ın kod-içi tüketicisi var — `durum()` (CLI/pano yüzeyi) kanonik tabanı taşır."""
    _kitap_yaz(PNLS)
    d = sermaye.durum()
    assert d["sermaye_taban_kanonik"] == TABAN, d["sermaye_taban_kanonik"]
