"""test_gelen_kutusu_mandal_v234.py — GELEN KUTUSU HİJYENİ: tekrar-eden bilinen-durum → DURUM (2026-08-12).

Operatör şikâyeti "çok fazla alarm var" ÖLÇÜLDÜ (canlı defter):
  * `finviz_unavailable` ~5 dakikada bir (~200+/gün) — token yok, durum DEĞİŞMİYOR (EDG-2026-022:
    FINVIZ alınmayacak), ama her keşif turu aynı yokluğu yeniden anlatıyordu.
  * MIRROR_DRIFT adet-sapması her gün ×4 AYNI içerikle (NUE/EMR/BKNG/AMGN `olculemedi` — kök
    bilinen: makbuzsuz boyut, ROADMAP Ö-7).
  * DATA_QUALITY bar-kaynak uyuşmazlığı (MNST %50) aynı (ticker, tarih, kaynak, sapma) ile günlük.

FELSEFE: gürültü SAKLANMAZ — bilinen-durum bir kez alarmlanır, tekrarı SAYILIR ve görünür kalır
(v192 bastırma-sayacı emsali), DEĞİŞİM her zaman ANINDA alarmlanır. Üç çivi:
  1. `obs.alarm` imza-mandalı (`MANDAL_IMZALAR`): MIRROR_DRIFT adet/durum imzası + DATA_QUALITY
     yalnız `bar_kaynak_uyusmazligi`. Sermaye-sınıfı jetonlar sözlükte YOK ve olamaz.
  2. `finviz.discover_universe`: uyarı kadansı durum değişmedikçe günde 1; keşif denemesi sürüyor.
  3. Bastırılanın DIŞ okuyucuları: `watchdog.parity_report` `alarm_mandal` satırı ve
     `finviz.status()["last"]` sayaç alanları (YASA-6 — okuyucusuz defter yok).

SINIR ÇİVİLERİ: alarm SEVİYESİ/eşiği değişmedi; teslim katmanı (`_maybe_notify` 6 sa penceresi)
dokunulmadı; `icra`/`koruma_dolumu` (dolum-başına olay) mandallanmaz; mandal makinesi düşerse
alarm SUSMAZ (fail-open).
"""
from __future__ import annotations

import time as _time

import pytest

from meridian import obs, store, watchdog as wd
from meridian.adapters import finviz


def _olaylar(token: str = "") -> list[dict]:
    return [e for e in store.read_jsonl("events.jsonl") if token in str(e)]


def _adet_sapmasi(ticker="NUE", local_qty=12.0, alpaca_qty=9.0, sinif="olculemedi"):
    return obs.alarm(obs.ALARM_MIRROR_DRIFT,
                     f"ayna adet sapması: {ticker} — içeride {local_qty:g}, Alpaca'da {alpaca_qty:g}",
                     ticker=ticker, local_qty=local_qty, alpaca_qty=alpaca_qty,
                     drift_sinifi=sinif, drift_neden="boyut makbuzu yok")


# =================================================================================================
# A. İMZA-MANDALI — MIRROR_DRIFT adet sapması
# =================================================================================================
def test_ayni_adet_sapmasi_imzasi_ikinci_kez_satir_uretmez_ama_sayilir(sandbox_state):
    """CANLI OLAY: aynı (ticker, local_qty, alpaca_qty, sınıf) her gün yeniden alarmlanıyordu.
    İlk görüş alarm; tekrar SATIRSIZ ama SAYAÇLI (v192 — bastırılan görünür kalır)."""
    r1 = _adet_sapmasi()
    r2 = _adet_sapmasi()
    assert len(_olaylar("MIRROR_DRIFT")) == 1, "tekrar yeniden satır bastı — mandal tutmadı"
    assert not r1.get("mandal_bastirildi") and r2.get("mandal_bastirildi") is True
    defter = store.read_json(obs.MANDAL_FILE, {})
    (imza, kayit), = defter.items()
    assert "NUE" in imza and "olculemedi" in imza
    assert kayit["n"] == 2 and kayit["bastirilan"] == 1


def test_adet_ya_da_sinif_degisimi_yeni_imzadir_ve_aninda_alarmlanir(sandbox_state):
    """DEĞİŞİM HER ZAMAN SESLİDİR: adet değişti → alarm; sınıf değişti → alarm."""
    _adet_sapmasi(local_qty=12.0)
    _adet_sapmasi(local_qty=12.0)                       # tekrar → sessiz
    _adet_sapmasi(local_qty=15.0)                       # ADET değişti
    _adet_sapmasi(local_qty=15.0, sinif="risk_buyudu")  # SINIF değişti
    assert len(_olaylar("MIRROR_DRIFT")) == 3
    assert len(store.read_json(obs.MANDAL_FILE, {})) == 3


def test_ilk_gorus_satiri_tekrar_mandalini_beyan_eder(sandbox_state):
    """YASA-4 ruhu: bastırma İŞARETLİDİR. İlk satır 'tekrarlar şurada sayılır' der."""
    _adet_sapmasi()
    (ev,) = _olaylar("MIRROR_DRIFT")
    assert ev.get("tekrar_mandali") == "state/" + obs.MANDAL_FILE


def test_serbest_penceresi_sonrasi_ayni_imza_YENIDEN_alarmlanir(sandbox_state, monkeypatch):
    """96 sa görünmeyen imza 'çözülmüş durum'dur; geri gelirse bu YENİ bir olgudur ve satırla
    (`mandal_yeniden=True`) anlatılır — mandal kalıcı bir kara delik değildir."""
    t0 = _time.time()
    monkeypatch.setattr(_time, "time", lambda: t0)
    _adet_sapmasi()
    _adet_sapmasi()
    monkeypatch.setattr(_time, "time", lambda: t0 + obs.MANDAL_SERBEST_S + 60)
    _adet_sapmasi()
    ev = _olaylar("MIRROR_DRIFT")
    assert len(ev) == 2, "serbest kalan imza yeniden alarmlanmadı — durum sonsuza dek sustu"
    assert ev[-1].get("mandal_yeniden") is True
    kayit = next(iter(store.read_json(obs.MANDAL_FILE, {}).values()))
    assert kayit["yeniden"] is True and kayit["n"] == 3 and kayit["bastirilan"] == 1


def test_icra_ve_koruma_dolumu_siniflari_mandallanmaz(sandbox_state):
    """Dolum-BAŞINA olaylar: imza tuple'ı fiyat/bacak taşımaz, 'aynı görünen' iki vaka ayrı
    gerçeklerdir. Mandallamak yeni olayı yutardı → bilinçli HARİÇ, davranış bugünkü gibi."""
    for _ in range(2):
        obs.alarm(obs.ALARM_MIRROR_DRIFT, "ayna sapması: AAPL", ticker="AAPL",
                  sim=10.0, alpaca_fill=11.0, divergence=0.1, drift_sinifi="icra")
    for _ in range(2):
        obs.alarm(obs.ALARM_MIRROR_DRIFT, "koruma dolumu: AAPL", ticker="AAPL",
                  drift_sinifi="koruma_dolumu", bacak="stop", fiyat=141.0)
    assert len(_olaylar("MIRROR_DRIFT")) == 4
    assert store.read_json(obs.MANDAL_FILE, {}) == {}


def test_ayracsiz_mirror_drift_satiri_oldugu_gibi_akar(sandbox_state):
    """`drift_sinifi` taşımayan yayıcı (ör. loop.py::_mirror_exit_sync çıkış-kapatılamadı) mandala HİÇ girmez —
    tanımadığımız satırı 'bilinen durum' saymak uydurma olurdu (fail-open)."""
    for i in range(2):
        obs.alarm(obs.ALARM_MIRROR_DRIFT, "ayna çıkışı kapatılamadı: NVDA",
                  ticker="NVDA", tries=i + 1, naked=True)
    assert len(_olaylar("MIRROR_DRIFT")) == 2


# =================================================================================================
# B. İMZA-MANDALI — DATA_QUALITY yalnız bar-kaynak uyuşmazlığı
# =================================================================================================
def test_bar_kaynak_uyusmazligi_ayni_imza_bastirilir_yeni_tarih_alarmlanir(sandbox_state):
    """MNST vakası: aynı (ticker, tarih, kaynak, sapma) günlük tekrar → tek satır; tarih/sapma
    değişimi YENİ ölçümdür → alarm."""
    def _dq(date="2026-08-10", dev=50.0):
        return obs.alarm(obs.ALARM_DATA_QUALITY, f"BAR KAYNAK UYUŞMAZLIĞI: MNST {date}",
                         kind="bar_kaynak_uyusmazligi", ticker="MNST", date=date,
                         source="cboe", dev_pct=dev, tol_pct=0.25)
    _dq(); _dq(); _dq()
    assert len(_olaylar("BAR KAYNAK")) == 1
    _dq(date="2026-08-11")
    assert len(_olaylar("BAR KAYNAK")) == 2
    kayitlar = store.read_json(obs.MANDAL_FILE, {})
    assert len(kayitlar) == 2 and sum(v["bastirilan"] for v in kayitlar.values()) == 2


def test_gercek_yayici_uzerinden_ayni_gun_tekrari_tek_satir(sandbox_state, monkeypatch):
    """UÇTAN UCA: `data._massive_crosscheck` (gerçek alan adlarıyla) iki kez aynı uyuşmazlığı
    görür → tek alarm satırı. Alan adları değişirse imza da değişir — bu test onu çiviler."""
    import pandas as pd
    from meridian.adapters import data, massive
    monkeypatch.setattr(massive, "available", lambda: True)
    monkeypatch.setattr(massive, "bar_for",
                        lambda t, d: {"date": d, "close": 150.0, "open": 1, "high": 1,
                                      "low": 1, "volume": 1})
    monkeypatch.setattr(data, "_record_xcheck", lambda *a, **k: None)   # birikim defteri ayrı test konusu
    df = pd.DataFrame({"date": [pd.Timestamp("2026-08-10")], "close": [100.0]})
    data._massive_crosscheck("MNST", df, "cboe")
    data._massive_crosscheck("MNST", df, "cboe")
    ev = _olaylar("BAR KAYNAK UYUŞMAZLIĞI")
    assert len(ev) == 1 and ev[0]["ticker"] == "MNST"


def test_diger_data_quality_yayicilari_mandala_girmez(sandbox_state):
    """`kind` süzgeci: determinism/monotonicity/… ve kind'siz DATA_QUALITY bugünkü gibi akar —
    imza alanları olmayan iki AYRI bulguyu tek imzada eritmek gerçek alarmı yutardı."""
    obs.alarm(obs.ALARM_DATA_QUALITY, "GERİLEME: trades 129 → 95", kind="monotonicity",
              field="trades", ticker="X")
    obs.alarm(obs.ALARM_DATA_QUALITY, "GERİLEME: trades 129 → 95", kind="monotonicity",
              field="trades", ticker="X")
    obs.alarm(obs.ALARM_DATA_QUALITY, "veri kalitesi kapısı: index_ok=False")
    obs.alarm(obs.ALARM_DATA_QUALITY, "veri kalitesi kapısı: index_ok=False")
    assert len(_olaylar("DATA_QUALITY")) == 4
    assert store.read_json(obs.MANDAL_FILE, {}) == {}


# =================================================================================================
# C. SINIRLAR — sermaye jetonları, teslim katmanı, fail-open
# =================================================================================================
def test_sermaye_sinifi_jetonlar_mandal_sozlugune_giremez(sandbox_state):
    """N1/İŞ-3b dersi: sermaye-riski alarmı muhasebe gürültüsünün ARKASINDA bekleyemez. Mandal
    sözlüğü İKİ jetonla sınırlı; genişletmek bir KARARDIR ve bu çivi bilinçli kırılmalıdır."""
    assert set(obs.MANDAL_IMZALAR) == {"MIRROR_DRIFT", "DATA_QUALITY"}
    for tok in (obs.ALARM_NAKED_POSITION, obs.ALARM_ONAYLI_PLAN_GONDERILMEDI,
                obs.ALARM_CIRCUIT_BREAKER, obs.ALARM_HALT, obs.ALARM_GOAL_FAILURE):
        assert tok not in obs.MANDAL_IMZALAR
    # davranış kanıtı: NAKED_POSITION birebir tekrar bile HER SEFERİNDE satır basar
    for _ in range(2):
        obs.alarm(obs.ALARM_NAKED_POSITION, "KORUMASIZ POZİSYON: VLO", ticker="VLO",
                  adet=37.0, drift_sinifi="korumasiz")   # ayraç alanı taşısa bile jeton listede yok
    assert len(_olaylar("NAKED_POSITION")) == 2


def test_teslim_katmani_ilk_goruste_calisir_tekrarda_hic_cagrilmaz(sandbox_state, monkeypatch):
    """Bastırılan tekrar `_maybe_notify`ye HİÇ inmez (6 sa penceresine dokunulmadı; kadans
    yukarıda kesildi). İlk görüş teslim zincirine bugünkü gibi girer."""
    cagri: list[str] = []
    monkeypatch.setattr(obs, "_maybe_notify", lambda tok, msg: cagri.append(tok))
    _adet_sapmasi()
    _adet_sapmasi()
    assert cagri == ["MIRROR_DRIFT"]


def test_mandal_makinesi_duserse_alarm_susmaz(sandbox_state, monkeypatch):
    """FAIL-OPEN: defter yazılamıyorsa gürültü riskini alırız, sessizlik riskini ASLA."""
    monkeypatch.setattr(store, "update_json",
                        lambda *a, **k: (_ for _ in ()).throw(OSError("disk dolu")))
    _adet_sapmasi()
    _adet_sapmasi()
    assert len(_olaylar("MIRROR_DRIFT")) == 2, "mandal arızası alarmı yuttu — fail-open kırıldı"


# =================================================================================================
# D. GÖRÜNÜRLÜK — bastırılan SAYILIR ve panoya çıkar (YASA-6 dış okuyucu)
# =================================================================================================
def test_parity_alarm_mandal_satiri_bastirilani_gorunur_kilar(sandbox_state):
    """Defterin dış okuyucusu `watchdog.parity_report` → pano. Satır HEP ok=True: envanterdir,
    alarm değil — kırmızıya dönseydi gürültü-kısma mekanizması kendinden alarm üretirdi."""
    _adet_sapmasi()
    _adet_sapmasi()
    _adet_sapmasi()
    r = next((r for r in wd.parity_report()["rows"] if r["check"] == "alarm_mandal"), None)
    assert r is not None and r["ok"] is True
    assert "1 bilinen-aktif durum" in r["detail"] and "2 tekrar" in r["detail"]
    assert "NUE" in r["detail"] and "state/" + obs.MANDAL_FILE in r["detail"]


def test_defter_bosken_parity_satiri_hic_cikmaz(sandbox_state):
    """KURT MASALI YASAĞI: mandallanan hiçbir şey yokken satır da yok."""
    assert next((r for r in wd.parity_report()["rows"] if r["check"] == "alarm_mandal"), None) is None


def test_supruntu_eski_imzalari_dusurur_defter_okunur_kalir(sandbox_state, monkeypatch):
    """2× serbest penceresini aşmış imza düşer — defter sonsuz büyüyen bir çöplüğe dönmez;
    düşen imzanın dönüşü zaten İLK GÖRÜŞ muamelesi görür."""
    t0 = _time.time()
    monkeypatch.setattr(_time, "time", lambda: t0)
    _adet_sapmasi(ticker="ESKI")
    monkeypatch.setattr(_time, "time", lambda: t0 + 2 * obs.MANDAL_SERBEST_S + 60)
    _adet_sapmasi(ticker="YENI")
    defter = store.read_json(obs.MANDAL_FILE, {})
    assert len(defter) == 1 and "YENI" in next(iter(defter))


# =================================================================================================
# E. FİNVİZ UYARI KADANSI — durum değişmedikçe günde 1 (EDG-2026-022)
# =================================================================================================
def _finviz_yok(monkeypatch):
    from meridian import secrets
    monkeypatch.setattr(secrets, "get", lambda n: None)
    monkeypatch.delenv("MERIDIAN_FINVIZ_PUBLIC", raising=False)


def test_ayni_gun_ikinci_kesif_uyarisi_bastirilir_ama_sayilir(sandbox_state, monkeypatch):
    """CANLI OLAY: token yokken her keşif turu (~5 dk) uyarıyordu → ~200+/gün. Artık aynı durum
    aynı gün TEK uyarı; sonraki turlar sayaçta. Keşif denemesi DURMAZ (aşağıda ayrı çivi)."""
    _finviz_yok(monkeypatch)
    for _ in range(3):
        assert finviz.discover_universe(use_cache=False) == []
    assert len(_olaylar("finviz_unavailable")) == 1
    c = store.read_json("finviz_universe.json", {})
    assert c["source"] == "none" and c["bastirilan"] == 2 and c["uyarildi_gun"] == c["date"]
    assert finviz.status()["last"]["bastirilan"] == 2, "sayaç panoya çıkmıyor — YASA-6"


def test_gun_donunce_ayni_durum_gunde_bir_kez_yeniden_uyarilir(sandbox_state, monkeypatch):
    """Kadans 'sonsuza dek sus' değil 'günde 1'dir: gün dönümünde durum hâlâ sürüyorsa bir kez
    daha söylenir ve o güne kadar bastırılan toplam satırın ÜSTÜNDE taşınır."""
    _finviz_yok(monkeypatch)
    finviz.discover_universe(use_cache=False)
    finviz.discover_universe(use_cache=False)
    c = store.read_json("finviz_universe.json", {})
    ilk = c["ilk_gorulme"]
    c["uyarildi_gun"] = "2020-01-01"                    # gün dönümü simülasyonu
    store.write_json("finviz_universe.json", c)
    finviz.discover_universe(use_cache=False)
    ev = _olaylar("finviz_unavailable")
    assert len(ev) == 2
    assert ev[-1]["bastirilan_toplam"] == 1 and ev[-1]["ilk_gorulme"] == ilk


def test_neden_degisirse_ayni_gun_aninda_uyarilir(sandbox_state, monkeypatch):
    """DEĞİŞİM = YENİ DURUM: arıza sınıfı değişti (token-yok → public parse düşük) → aynı gün
    ikinci uyarı ANINDA basılır, sayaç yeni durum için sıfırdan başlar."""
    import httpx
    _finviz_yok(monkeypatch)
    finviz.discover_universe(use_cache=False)
    monkeypatch.setattr(finviz, "_fetch_public",
                        lambda *a, **k: (_ for _ in ()).throw(httpx.ConnectError("no net")))
    finviz.discover_universe(use_cache=False, allow_public=True)
    ev = _olaylar("finviz_unavailable")
    assert len(ev) == 2 and ev[-1]["reason"] != ev[0]["reason"]
    assert store.read_json("finviz_universe.json", {})["bastirilan"] == 0


def test_toparlanma_sonrasi_yeni_ariza_aninda_uyarilir(sandbox_state, monkeypatch):
    """Token gelir → sağlıklı keşif durumu SIFIRLAR (davranış kendiliğinden canlanır, ek kod yok);
    sonra yeniden düşerse İLK tur uyarır — mandal 'bir kere sustuysa hep susar'a dönüşmez."""
    _finviz_yok(monkeypatch)
    finviz.discover_universe(use_cache=False)
    monkeypatch.setattr(finviz, "_fetch_public", lambda *a, **k: ["AAA", "BBB"])
    assert finviz.discover_universe(use_cache=False, allow_public=True) == ["AAA", "BBB"]
    monkeypatch.setattr(finviz, "_fetch_public",
                        lambda *a, **k: (_ for _ in ()).throw(RuntimeError("çöktü")))
    finviz.discover_universe(use_cache=False, allow_public=True)
    assert len(_olaylar("finviz_unavailable")) == 2
    assert len(_olaylar("finviz_universe")) >= 1          # sağlıklı tur olay yazmayı sürdürüyor


def test_kesif_denemesi_bastirilan_gunlerde_de_surer(sandbox_state, monkeypatch):
    """UYARI kadansı düştü, KEŞİF kadansı DEĞİL: bastırılan turda da `discover` gerçekten çağrılır
    — yarın token gelirse ilk tur yakalar (EDG-2026-022 hükmü davranışı dondurmaz)."""
    _finviz_yok(monkeypatch)
    sayac = {"n": 0}
    gercek = finviz.discover

    def _sayan(*a, **k):
        sayac["n"] += 1
        return gercek(*a, **k)

    monkeypatch.setattr(finviz, "discover", _sayan)
    for _ in range(3):
        finviz.discover_universe(use_cache=False)
    assert sayac["n"] == 3, "keşif fonksiyonu durduruldu — istenmeyen davranış değişikliği"
