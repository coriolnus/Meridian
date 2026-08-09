"""test_dalga2_sprint_v224.py — DALGA-2 AJAN C: sprint.py'nin İKİ kusuru.

BULGU 9 — `should_run(now=)` SEAM'İ (gün bacağı enjekte now'u taşımıyordu).
    v159 bunu ölçtü ("mesafeyi çivile, takvimi değil") ama ÜRETİM seam'ini AÇIK bıraktı: `now=`
    yalnız saat/pencere bacağını taşıyor, GÜN bacağı `dt.datetime.now(utc)`'tan geliyordu. Bu tur
    seam KAPATILIR — gün bacağı, çağıran tz-AWARE bir `now` verdiyse ONDAN türer ("kararın ânı"
    vaadi). DÜZELTME DAVRANIŞ-NÖTRDÜR: naive/verilmemiş `now` (üretim varsayılanı VE v159'un enjekte
    ettiği tür) mutlak bir ana denk düşmez → gerçek UTC saatine düşülür, yani `gun_ref` BİREBİR eski
    ifadeye eşittir. Aşağıda hem nötrlük hem de kapalı-seam (enjeksiyonun gün bacağını taşıması)
    çivilenir. v159 mesafe-çivisi bu dosyanın kapsamında ayrıca koşturulur ve YEŞİL kalmalıdır.

BULGU 2 (kod bacağı) — ORPHAN-PID GÖSTERGESİ.
    Ölçülen kusur (2026-08-09 triyajı): sprint pid'i ölü ama durum `phase='baseline'`, progress
    281/527 taşıyor; `active` zaten False'tı ama okuyucu (pano) fazdan "%53 koşuyor" çiziyordu.
    status() artık ölü pid + terminal-OLMAYAN faz'ı ORPHAN diye dürüstçe işaretler. Sprint
    DİRİLTİLMEZ (kadans/kota ayrı operatör kalemi) — yalnız durum dürüstleşir.

CANLI STATE'E YAZILMAZ: her test `sandbox_state` (tmp + config.STATE monkeypatch) içinde koşar.
"""
from __future__ import annotations

import datetime as dt
import json
import os

import pytest

from meridian import sprint, store

UTC = dt.timezone.utc
# tz-AWARE, SABİT started_at: enjekte now ile mesafe kurulur (gün bacağı artık now'dan türediği
# için gerçek duvar saatinden BAĞIMSIZ olmalı — testin çivilediği şey tam da budur).
FIXED_SON = "2026-08-02T00:00:00+00:00"


def _kur(sandbox_state, monkeypatch, *, started_at, n_hyp, n_hyp_at_start):
    """should_run için sandbox kurulumu: canlı arama SUSTURULUR (aksi hâlde `_search_busy`
    muhafazakâr tarafa düşer), hipotez defteri ve ebeveyn damgası yazılır. pid YOK → `active` False
    → should_run saat/gün bacaklarına ilerler."""
    from meridian import hermes
    monkeypatch.setattr(hermes, "SEARCH_PROGRESS", {}, raising=False)
    (sandbox_state / "hypotheses.jsonl").write_text(
        "".join(json.dumps({"id": f"H{i:05d}"}) + "\n" for i in range(n_hyp)))
    store.write_json(sprint.STATUS_FILE, {"started_at": started_at, "n_hyp_at_start": n_hyp_at_start})


def _taban_gercek(gecen_gun: int) -> str:
    """v159 `_taban` ile AYNI mesafe-çivisi: started_at = GERÇEK şimdi (UTC) − (gecen_gun gün + 12
    saat). 12 saatlik yastık, `.days` tabana-yuvarlamasını testin ε koşum süresinden bağımsız
    kılar (6g12s → .days == 6)."""
    return (dt.datetime.now(UTC) - dt.timedelta(days=gecen_gun, hours=12)).isoformat(timespec="seconds")


# ==================================================================================================
# SEAM — DAVRANIŞ NÖTRLÜĞÜ (naive/None now gün bacağına SIZMAZ)
# ==================================================================================================
def test_naive_now_gun_bacagina_SIZMAZ_davranis_notr(sandbox_state, monkeypatch):
    """DAVRANIŞ-NÖTRLÜK KANITI. Naive `now` (üretim varsayılanı ve v159'un enjekte ettiği tür) gün
    bacağına GİRMEZ: gün her zaman GERÇEK saatten hesaplanır, tıpkı düzeltmeden önceki gibi.

    started_at gerçek şimdiden 6,5 gün geride. Naive now'un tarihi 2020 (ESKİ): gün bacağına
    sızsaydı gecen_gun ~2400 olurdu. 6 çıkması, naive değerin gün bacağına HİÇ girmediğinin
    doğrudan kanıtıdır — ve `now=None` (üretim yolu) BİREBİR aynı sonucu verir."""
    _kur(sandbox_state, monkeypatch, started_at=_taban_gercek(6), n_hyp=3, n_hyp_at_start=3)

    karar_naive = sprint.should_run(now=dt.datetime(2020, 1, 1, 23, 0))   # naive, saat pencere içi
    assert karar_naive["gecen_gun"] == 6, (
        f"naive now GÜN bacağına sızdı — davranış nötr DEĞİL (beklenen 6, "
        f"sızsaydı ~2400): {karar_naive['gecen_gun']}")

    karar_default = sprint.should_run()                                   # now=None → üretim yolu
    assert karar_default["gecen_gun"] == 6, karar_default["gecen_gun"]
    assert karar_naive["gecen_gun"] == karar_default["gecen_gun"], "naive ve varsayılan yol ayrıştı"

    # Naive yolun TAM kararı da düzeltme öncesiyle aynıdır: saat 23 pencere içinde, gun 6, taze 0.
    assert karar_naive["kos"] is False and karar_naive["sebep"].startswith("tetik_yok"), karar_naive


def test_default_now_gun_bacagi_gercek_saatten(sandbox_state, monkeypatch):
    """now=None yolu (tüm üretim çağıranları: maybe_start, analytics, scheduler) gün bacağını gerçek
    UTC saatinden hesaplar. 7 gün geri → gecen_gun 7 (eski ifadeyle birebir aynı)."""
    _kur(sandbox_state, monkeypatch, started_at=_taban_gercek(7), n_hyp=3, n_hyp_at_start=3)
    assert sprint.should_run()["gecen_gun"] == 7


# ==================================================================================================
# SEAM — KAPALI (enjekte tz-AWARE now GÜN bacağını taşır); davranış v159 ile AYNI
# ==================================================================================================
def test_aware_now_6_gun_TASINIR_susar(sandbox_state, monkeypatch):
    """SEAM KAPALI: enjekte tz-aware now gün bacağını taşır. 6 gün < 7 eşik → kadans SUSAR
    (tetik_yok) — v159'un 6-gün hükmüyle AYNI davranış, ama gün artık now'dan gelir."""
    _kur(sandbox_state, monkeypatch, started_at=FIXED_SON, n_hyp=3, n_hyp_at_start=3)
    # 2026-08-08T23:00Z − 2026-08-02T00:00Z = 6g 23s → .days == 6; saat 23 pencere içinde (22→06).
    karar = sprint.should_run(now=dt.datetime(2026, 8, 8, 23, 0, tzinfo=UTC))
    assert karar["gecen_gun"] == 6, karar["gecen_gun"]
    assert karar["taze_hipotez"] == 0, karar["taze_hipotez"]
    assert karar["kos"] is False, karar
    assert karar["sebep"].startswith("tetik_yok"), karar["sebep"]


def test_aware_now_7_gun_TASINIR_yanar_haftalik(sandbox_state, monkeypatch):
    """SEAM'İN İKİNCİ YÖNÜ: 7 gün >= eşik → kadans YANAR, sebep 'haftalik_taban' (taze DEĞİL) —
    v159 ile AYNI ayrım. Enjekte now gün bacağını çivi gibi taşır, gerçek saate bağlı değil."""
    _kur(sandbox_state, monkeypatch, started_at=FIXED_SON, n_hyp=3, n_hyp_at_start=3)
    # 2026-08-09T23:00Z − 2026-08-02T00:00Z = 7g 23s → .days == 7.
    karar = sprint.should_run(now=dt.datetime(2026, 8, 9, 23, 0, tzinfo=UTC))
    assert karar["gecen_gun"] == 7, karar["gecen_gun"]
    assert karar["taze_hipotez"] == 0, karar["taze_hipotez"]
    assert karar["kos"] is True, karar
    assert karar["sebep"] == "haftalik_taban", karar["sebep"]


@pytest.mark.parametrize("gun_offset", [0, 5, 6, 7, 10])
def test_aware_now_gun_bacagini_DOGRUDAN_belirler(sandbox_state, monkeypatch, gun_offset):
    """KAPALI-SEAM'İN ÇEKİRDEK KANITI: enjekte aware now gün bacağını DOĞRUDAN belirler. SABİT bir
    started_at (2026-08-02) verilip now süpürülür; gecen_gun tam olarak gun_offset'i izler.

    Seam AÇIK olsaydı (eski kod) gecen_gun, gerçek saatten (bugün − 2026-08-02) gelen SABİT bir
    değer olur ve enjeksiyona kör kalırdı — 0/5/6/7/10 dizisi bunu doğrudan çürütür."""
    _kur(sandbox_state, monkeypatch, started_at=FIXED_SON, n_hyp=3, n_hyp_at_start=3)
    son_dt = dt.datetime.fromisoformat(FIXED_SON)                 # tz-aware
    now = son_dt + dt.timedelta(days=gun_offset, hours=2)         # +2s: .days yastığı, saat pencerede
    assert sprint.should_run(now=now)["gecen_gun"] == gun_offset


# ==================================================================================================
# ORPHAN-PID GÖSTERGESİ — durum ölü sprinti dürüstçe "koşmuyor" der
# ==================================================================================================
def test_orphan_olu_pid_nonterminal_faz_isaretlenir(sandbox_state):
    """Ölçülen kusur (triyaj kalem 2): ölü pid + phase='baseline' + progress 281/527. `active` zaten
    False'tı ama okuyucu fazdan 'koşuyor' çiziyordu. status() artık ORPHAN diye işaretler."""
    store.write_json(sprint.STATUS_FILE,
                     {"pid": 999999, "sid": "x", "phase": "baseline", "progress": 281, "total": 527})
    st = sprint.status()
    assert st["active"] is False, "ölü pid canlı okunuyor"
    assert st["orphan"] is True, "ölü pid + terminal-olmayan faz orphan işaretlenmedi — pano yanılır"
    assert st["orphan_note"] and "orphan" in st["orphan_note"].lower()


def test_orphan_canli_pid_orphan_DEGIL(sandbox_state):
    """DİRİMİN KONTRASTI: gerçekten koşan bir sprint (canlı pid) orphan OLMAMALI — yoksa gösterge
    her koşan sprinti yanlış-alarmlar. Test sürecinin KENDİ pid'i canlıdır."""
    store.write_json(sprint.STATUS_FILE,
                     {"pid": os.getpid(), "sid": "x", "phase": "baseline", "progress": 10, "total": 527})
    st = sprint.status()
    assert st["active"] is True
    assert st["orphan"] is False
    assert st["orphan_note"] is None


def test_orphan_terminal_faz_olu_pid_orphan_DEGIL(sandbox_state):
    """Ölü pid + TERMİNAL faz NORMALDİR (iş bitti/durduruldu/çöktü) — orphan DEĞİL. Aksi hâlde
    her tamamlanmış sprint sonsuza dek 'orphan' damgası taşırdı."""
    for faz in ("done", "stopped", "error", "stopping"):
        store.write_json(sprint.STATUS_FILE, {"pid": 999999, "sid": "x", "phase": faz})
        st = sprint.status()
        assert st["active"] is False, faz
        assert st["orphan"] is False, f"terminal faz '{faz}' orphan sayıldı"
        assert st["orphan_note"] is None, faz


def test_orphan_fazsiz_olu_pid_orphan_DEGIL(sandbox_state):
    """v45 zombie-reap invariantı KORUNUR: fazsız ölü pid yalnız `active False`tır, orphan DEĞİL
    (faz yoksa 'koşuyor' gibi de okunmaz). Bu ayrım orphan göstergesiyle bozulmamalı."""
    store.write_json(sprint.STATUS_FILE, {"pid": 999999, "sid": "x"})
    st = sprint.status()
    assert st["active"] is False and st["orphan"] is False


def test_orphan_bos_durum_orphan_DEGIL(sandbox_state):
    """Hiç sprint koşmamışken (durum dosyası yok/boş) orphan False olmalı — pid yok, faz yok."""
    st = sprint.status()
    assert st.get("orphan") is False and st.get("active") is False


def test_orphan_should_run_ZATEN_KOSUYOR_demez_dirilTMEZ(sandbox_state, monkeypatch):
    """'orphan pid → durum koşmadı': orphaned bir sprint should_run'da 'zaten_kosuyor' OKUNMAMALI
    (ölü pid canlı sayılsaydı kadans sonsuza dek susardı). Gösterge sprint'i DİRİLTMEZ — bu test
    yalnız 'zaten_kosuyor' YANLIŞINI dışlar, kadansı tetiklemeyi değil."""
    from meridian import hermes
    monkeypatch.setattr(hermes, "SEARCH_PROGRESS", {}, raising=False)
    store.write_json(sprint.STATUS_FILE,
                     {"pid": 999999, "sid": "x", "phase": "baseline", "progress": 281, "total": 527,
                      "started_at": "2026-08-07T14:15:30+00:00", "n_hyp_at_start": 0})
    assert sprint.status()["orphan"] is True
    karar = sprint.should_run(now=dt.datetime(2026, 8, 9, 23, 0, tzinfo=UTC))
    assert karar["sebep"] != "zaten_kosuyor", f"orphaned (ölü) sprint 'koşuyor' okundu: {karar['sebep']}"
