"""v239 KALEM 2 — YETİM-RESTART MEŞGULİYET KAPISINA TAKILIP KALICI BLOKLUYDU.

ÖLÇÜLEN ARIZA (canlı olay defteri, her poll'de aynı satır):
    sprint_cadence_skip{sebep:"mesgul:canli_arama", yetim:true, gecen_gun:5,
                        arama_bayrak_yasi_sa:0.17, arama_bayat:false}
v235 yetimi bir TETİK yapmıştı ama tetiği meşguliyet kapılarının ARDINA koymuştu. Beyin zinciri
~5 dakikada bir yansıma turu açtığı için `SEARCH_PROGRESS` parmak izi sürekli değişiyor →
bayatlık saati her turda sıfırlanıyor → `arama["mesgul"]` ASLA False olmuyor → tetik hiç yanmıyor.
Yani v235'in yetim-restart'ı ÖLÜ bir mekanizmaydı: 5 gündür ölü bir çocuk, 5 gündür doğmuyor.

DÜZELTMENİN SÖZLEŞMESİ — İKİ YÖN, İKİSİ DE ÇİVİLİ:
  (→) yetim ∧ YÜK meşguliyeti (canlı arama / bar kovalaması) → **RESTART** (yetim zaten ÖLÜ bir
      süreçtir; canlı aramayla çakışmaz — ayrı süreçler).
  (←) SAĞLIKLI ∧ meşgul → **skip** (mevcut doğru davranış BİREBİR korunur; bu, düzeltmenin
      "her kapıyı aç" değil "yanlış kapıyı aç" olmadığının kanıtı).
Ek olarak korunan üç kural ayrı ayrı çivilenir: gece penceresi, 12 saatlik yetim freni ve
YETKİ kapısı (`elle_tik` — 2026-07-30'da ölçülmüş kaza: elle tik 4 işçilik alt süreç başlatıyordu).

CANLI STATE'E YAZILMAZ: her test `sandbox_state` içinde koşar.
"""
from __future__ import annotations

import datetime as dt
import json

from meridian import sprint, store

UTC = dt.timezone.utc


# GECE PENCERESİ İÇİ bir karar ânı (SPRINT_HOURS = (22, 6)).
# MESAFE ÇİVİLENİR, TAKVİM DEĞİL (v159/v224 deseni): `started_at` ENJEKTE EDİLEN karar ânına göre
# kurulur, gerçek duvar saatine göre DEĞİL — `should_run` tz-aware `now` verildiğinde gün/saat
# bacaklarının ikisini de ondan türetir, dolayısıyla gerçek saate demirlemek testi saat-bağımlı
# (yani hiçbir şey kanıtlamayan) hâle getirirdi.
GECE = dt.datetime(2026, 8, 13, 23, 0, tzinfo=UTC)
GUNDUZ = dt.datetime(2026, 8, 13, 14, 0, tzinfo=UTC)


def _arama_bayragi(monkeypatch, kosuyor: bool):
    """`kosuyor=True` CANLI ARIZAYI birebir kurar: bayrak `running=True` ve parmak izi TAZE
    (bayat DEĞİL) — yani `_arama_durumu` dürüstçe "meşgul" der. Testler tam bu hâlde ölçer;
    bayrağı bayatlatarak kolaya kaçılmaz."""
    from meridian import hermes
    monkeypatch.setattr(hermes, "SEARCH_PROGRESS",
                        ({"running": True, "phase": "walk", "i": 3, "total": 12}
                         if kosuyor else {}), raising=False)
    sprint._ARAMA_GOZLEM.update(iz=None, beri=None, olayli=False)


def _yetim_kur(sandbox_state, monkeypatch, *, saat_once: float, arama_kosuyor: bool,
               an: dt.datetime = GECE):
    """Yetim bir sprint (ölü pid + terminal-olmayan faz) + canlı arama bayrağı kurar."""
    _arama_bayragi(monkeypatch, arama_kosuyor)
    (sandbox_state / "hypotheses.jsonl").write_text(json.dumps({"id": "H00001"}) + "\n")
    basla = (an - dt.timedelta(hours=saat_once)).isoformat(timespec="seconds")
    store.write_json(sprint.STATUS_FILE,
                     {"pid": 999999, "sid": "sid-yetim", "phase": "baseline",
                      "progress": 281, "total": 527, "started_at": basla, "n_hyp_at_start": 1})
    return basla


def _saglikli_kur(sandbox_state, monkeypatch, *, gun_once: int, arama_kosuyor: bool,
                  an: dt.datetime = GECE):
    """Yetim OLMAYAN taban: pid yok (active False, orphan False), haftalık tetik dolu."""
    _arama_bayragi(monkeypatch, arama_kosuyor)
    (sandbox_state / "hypotheses.jsonl").write_text(json.dumps({"id": "H00001"}) + "\n")
    basla = (an - dt.timedelta(days=gun_once, hours=12)).isoformat(timespec="seconds")
    store.write_json(sprint.STATUS_FILE, {"started_at": basla, "n_hyp_at_start": 1})


# ============================ (→) YETİM ∧ YÜK-MEŞGULİYETİ → RESTART ============================

def test_yetim_canli_arama_kosarken_YENIDEN_BASLAR(sandbox_state, monkeypatch):
    """ASIL İDDİA. Canlı arama GERÇEKTEN meşgul (bayrak taze, bayat DEĞİL) ve sprint yetim →
    kadans artık `yetim_sprint_yeniden` der. Eski kod burada `mesgul:canli_arama` diyordu."""
    _yetim_kur(sandbox_state, monkeypatch, saat_once=30, arama_kosuyor=True)
    assert sprint.status()["orphan"] is True
    karar = sprint.should_run(now=GECE)
    ab = karar["arama_bayragi"]
    assert ab["mesgul"] is True and ab["bayat"] is False, (
        f"kurulum yanlış — arama meşgul/bayat-değil olmalıydı: {ab}")
    assert karar["kos"] is True and karar["sebep"] == "yetim_sprint_yeniden", karar


def test_yetim_cagiran_yuk_sinyali_verse_de_yeniden_baslar(sandbox_state, monkeypatch):
    """`bar_kovalamasi` bir YÜK sinyalidir (veri hattı ağa çıkıyor) — yetkiyi ilgilendirmez."""
    _yetim_kur(sandbox_state, monkeypatch, saat_once=30, arama_kosuyor=False)
    karar = sprint.should_run(mesgul="bar_kovalamasi", now=GECE)
    assert karar["kos"] is True and karar["sebep"] == "yetim_sprint_yeniden", karar


# ============================ (←) SAĞLIKLI ∧ MEŞGUL → SKIP (korunur) ============================

def test_saglikli_sprint_canli_arama_kosarken_ATLAR(sandbox_state, monkeypatch):
    """POZİTİF KONTROL / REGRESYON KARŞITI: düzeltme 'her kapıyı açmak' değildir. Yetim YOKKEN
    canlı arama hâlâ kadansı durdurur — aksi hâlde iki ProcessPoolExecutor 8 çekirdeği böler."""
    _saglikli_kur(sandbox_state, monkeypatch, gun_once=9, arama_kosuyor=True)
    karar = sprint.should_run(now=GECE)
    assert karar["yetim"] is False
    assert karar["kos"] is False and karar["sebep"] == "mesgul:canli_arama", karar


def test_saglikli_sprint_cagiran_mesguliyetiyle_ATLAR(sandbox_state, monkeypatch):
    _saglikli_kur(sandbox_state, monkeypatch, gun_once=9, arama_kosuyor=False)
    karar = sprint.should_run(mesgul="bar_kovalamasi", now=GECE)
    assert karar["kos"] is False and karar["sebep"] == "mesgul:bar_kovalamasi", karar


# ============================ KORUNAN ÜÇ KURAL ============================

def test_yetki_kapisi_elle_tik_YETIMDE_DE_bloklar(sandbox_state, monkeypatch):
    """`elle_tik` bir YÜK sinyali değil YETKİ kapısıdır (2026-07-30 ölçülmüş kazası: pano 'bir tur
    ilerlet' düğmesi 22:00'den sonra gerçekten 4 işçilik alt süreç başlatıyordu). Yetim onu delemez
    — sprintin elle tetiği AYRI bir düğmedir (`/api/sprint/start`)."""
    _yetim_kur(sandbox_state, monkeypatch, saat_once=30, arama_kosuyor=False)
    karar = sprint.should_run(mesgul="elle_tik", now=GECE)
    assert karar["kos"] is False and karar["sebep"] == "mesgul:elle_tik", karar
    assert "elle_tik" in sprint.MESGUL_YETKI_KAPILARI


def test_gece_penceresi_yerinde_kalir(sandbox_state, monkeypatch):
    """Yarıda kalmış antrenmanı GÜNDÜZ yeniden başlatmak, 4 işçiyi canlı kararların makinesine
    sokmaktır — yetim tetiği saat penceresinden SONRA gelir ve bu sıra korunur."""
    _yetim_kur(sandbox_state, monkeypatch, saat_once=30, arama_kosuyor=True)
    karar = sprint.should_run(now=GUNDUZ)
    assert karar["kos"] is False and karar["sebep"] == "saat_dilimi_disinda", karar


def test_12_saatlik_yetim_freni_yerinde_kalir(sandbox_state, monkeypatch):
    """Bypass `yetim_tetik`e bağlıdır, çıplak `yetim`e değil: hemen ölen bir çocuk 5 dakikada bir
    yeniden doğamaz (çökme döngüsü ≤1 deneme/12 sa)."""
    _yetim_kur(sandbox_state, monkeypatch, saat_once=2, arama_kosuyor=True)
    karar = sprint.should_run(now=GECE)
    assert karar["yetim"] is True and karar["yetim_tetik"] is False
    assert karar["kos"] is False and karar["sebep"] == "mesgul:canli_arama", karar


def test_gercekten_kosan_sprint_bypass_edilmez(sandbox_state, monkeypatch):
    """`active` (canlı pid) bypass EDİLMEZ: iki sprint 8 çekirdeği ikiye böler ve ikisi de yavaşlar."""
    from meridian import hermes
    monkeypatch.setattr(hermes, "SEARCH_PROGRESS", {}, raising=False)
    (sandbox_state / "hypotheses.jsonl").write_text(json.dumps({"id": "H00001"}) + "\n")
    basla = (dt.datetime.now(UTC) - dt.timedelta(hours=30)).isoformat(timespec="seconds")
    store.write_json(sprint.STATUS_FILE,
                     {"pid": __import__("os").getpid(), "sid": "sid-canli", "phase": "baseline",
                      "started_at": basla, "n_hyp_at_start": 1})
    st = sprint.status()
    assert st["active"] is True and st["orphan"] is False
    karar = sprint.should_run(now=GECE)
    assert karar["kos"] is False and karar["sebep"] == "zaten_kosuyor", karar


# ============================ DEFTER: SKIP SATIRI TEŞHİS EDİLEBİLİR OLMALI ============================

def test_skip_olayi_yetim_ve_tetigi_AYRI_tasir(sandbox_state, monkeypatch):
    """Canlı teşhis bu iki alanın ayrılığına dayanıyordu: `yetim=true` görünüyordu ama "neden hâlâ
    başlamadı?" sorusu defterden cevaplanamıyordu (fren mi, kapı mı?)."""
    # `maybe_start` `should_run()`u ENJEKSİYONSUZ çağırır (üretim yolu) → gün/saat bacakları GERÇEK
    # saatten türer; bu tek testte çıpa da o yüzden gerçek şimdidir.
    _yetim_kur(sandbox_state, monkeypatch, saat_once=2, arama_kosuyor=False,
               an=dt.datetime.now(UTC))
    sprint._YETIM_OLAYLI.clear()
    sprint.maybe_start(mesgul="elle_tik")
    satirlar = [json.loads(l) for l in
                (sandbox_state / "events.jsonl").read_text().splitlines() if l.strip()]
    skip = [e for e in satirlar if e.get("event") == "sprint_cadence_skip"]
    assert skip, f"skip olayı yazılmadı: {[e.get('event') for e in satirlar]}"
    assert skip[-1]["yetim"] is True and skip[-1]["yetim_tetik"] is False, skip[-1]
