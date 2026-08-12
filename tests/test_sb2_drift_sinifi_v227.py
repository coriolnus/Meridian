"""test_sb2_drift_sinifi_v227.py — MIRROR_DRIFT SAPMA SINIFI (`drift_sinifi`), SB-2 / B2.

ÖLÇÜLEN GEREKÇE (docs/BAYAT-SERMAYE-KOK-2026-08-07.md §8/B2): 08-05 gecesi DÖRT MIRROR_DRIFT
alarmı bastı ve HİÇBİRİ sebebi ADLANDIRMADI — belirti (adet %49 sapma) görüldü, SEBEP sınıfı
söylenmedi (gerçek kök: gönderim anında kitabın boyut tabanı 94.457,91$, dolum anında 100.000$).
Bu tur `reconcile_broker_state`in ADET sapması alarmına, SB-1 boyut makbuzunu (`size_law`, v222)
DOLUM anının girdilerine kıyaslayan bir `drift_sinifi` alanı ekler.

YÖNTEM: türetme çekirdeği (`loop._drift_sinifi_adet`) SAF fonksiyon olarak TEK TEK sınanır (her
sınıf + `olculemedi`'nin ADI OLAN hâlleri); sonra `reconcile_broker_state` üzerinden uçtan uca
alarmın alanı taşıdığı ve EŞİĞİN (>%25) DEĞİŞMEDİĞİ gösterilir. Türetilemeyen sınıf UYDURULMAZ:
`olculemedi` + neden (0/boş DEĞİL). Beyan_kaydi bilerek `olculemedi`'dir — makbuz beyan_n/ofset
taşımaz (SB-1 makbuz genişletme AYRI kalem).

GÜNCELLEME (WP-E dolum boşlukları turu, teşhis docs/TESHIS-WPE-AYNA-DOLUM-2026-08-10.md):
  * B6 — `fill_eq_now` yalnız pozisyon BU SEANSTA dolduysa dolum tabanıdır; saf çağrılar artık
    `dolum_taze=True` geçirir, e2e pozisyon anlık görüntüsü `ts_open` taşır. Yaşlı pozisyonda
    kıyas YAPILMAZ (yeni testler test_wpe_dolum_boslugu_v234.py'de).
  * B5/ROADMAP §2-7 — makbuzsuz sapmanın adı `olculemedi` değil `makbuzsuz_boyut`.
  * B8 — `motor_yetimi` üçe ayrıldı; buradaki yetim testi `giris_yetimi` alt-adını doğrular.
  * B2 — 1.3 kuyruk-güdümlü oldu: `icra` sapma testi artık yamalanacak trades SATIRINI da yazar
    (satırsız kapanış yamalanamaz ve `exit_fill_patch_satirsiz` uyarısıyla düşer).
"""
from __future__ import annotations

import pytest

from meridian import config, health, loop, store
from meridian.adapters import alpaca


# ---- SB-1 boyut makbuzu iskeleti (v222 gerçek şeması: 5 alan) -----------------------------------
def _makbuz(eq_kaynak="eq_now", eq_now=94457.91, peak=100000.0, size_mult=0.4916, kitap_rev=5):
    return {"eq_kaynak": eq_kaynak, "eq_now": eq_now, "peak": peak,
            "size_mult": size_mult, "kitap_rev": kitap_rev}


def _wire(monkeypatch, orders, positions):
    """`reconcile_broker_state`in gerektirdiği ayna kapıları: alpaca_paper + SAĞLIKLI taşıma."""
    monkeypatch.setattr(config, "BROKER", "alpaca_paper")
    monkeypatch.setattr(alpaca, "paper_available", lambda: True)
    monkeypatch.setattr(alpaca, "orders", lambda **k: orders)
    monkeypatch.setattr(alpaca, "positions", lambda: positions)
    monkeypatch.setattr(alpaca, "transport", lambda: {"ok": True})


def _events(token: str) -> list:
    return [e for e in store.read_jsonl("events.jsonl") if token in str(e)]


# =================================================================================================
# A. TÜRETME ÇEKİRDEĞİ — `loop._drift_sinifi_adet` (saf fonksiyon, sınıf başına bir hüküm)
# =================================================================================================
def test_boyutlama_tabani_canli_08_05_vakasini_yakalar(sandbox_state):
    """08-05 KANITI: gönderim eq_now 94457,91$ (bayat taban) ≠ dolum eq_now 100000$ → çarpan
    0,4916→1,0. Sınıf `boyutlama_tabani` ve neden İKİ tabanı da adıyla taşır."""
    sinif, neden = loop._drift_sinifi_adet(_makbuz(), fill_eq_now=100000.0, fill_peak=100000.0,
                                           dolum_taze=True)   # B6: ayni-seans dolumu
    assert sinif == "boyutlama_tabani", f"08-05 vakası yanlış sınıfa düştü: {sinif} — {neden}"
    assert "94457" in neden and "100000" in neden, "neden iki boyut tabanını da adlandırmıyor"


def test_sermaye_kaynagi_bayat_nabiz_kanaldan_gelir(sandbox_state, monkeypatch):
    """AMGN bacağı: makbuz eq_kaynak=nabiz VE nabız yaşı > 1 seans → `sermaye_kaynagi`. KANAL-özgü
    kök, generic taban kıyasından ÖNCE (eq_now da farklı olsa bile nabız kanalı kazanır)."""
    monkeypatch.setattr(health, "heartbeat_age_seconds", lambda: 90000.0)   # ~25 sa > 1 seans
    sinif, neden = loop._drift_sinifi_adet(_makbuz(eq_kaynak="nabiz", kitap_rev=None),
                                           fill_eq_now=100000.0, fill_peak=100000.0,
                                           dolum_taze=True)
    assert sinif == "sermaye_kaynagi", f"{sinif} — {neden}"
    assert "nabız" in neden or "nabiz" in neden


def test_taze_nabiz_sermaye_kaynagi_DEGIL_tabana_duser(sandbox_state, monkeypatch):
    """POZİTİF KONTROL: nabız TAZE (yaş ≤ 1 seans) ise `sermaye_kaynagi` verilmez — taban farkı
    hâlâ varsa `boyutlama_tabani`'na düşer. Sınıf, nabzın YAŞINI gerçekten okuyor."""
    monkeypatch.setattr(health, "heartbeat_age_seconds", lambda: 120.0)
    sinif, _ = loop._drift_sinifi_adet(_makbuz(eq_kaynak="nabiz", kitap_rev=None),
                                       fill_eq_now=100000.0, fill_peak=100000.0, dolum_taze=True)
    assert sinif == "boyutlama_tabani"


def test_derisk_carpani_esik_degisiminde(sandbox_state):
    """eq_now İKİ bacakta AYNI (100000) ama makbuz çarpanı (0,5) dolum çarpanından (derisk_mult=1,0)
    farklı → de-risk eşiği/kartı arada değişti = `derisk_carpani`."""
    sinif, neden = loop._drift_sinifi_adet(
        _makbuz(eq_now=100000.0, size_mult=0.5, kitap_rev=None),
        fill_eq_now=100000.0, fill_peak=100000.0, dolum_taze=True)
    assert sinif == "derisk_carpani", f"{sinif} — {neden}"


def test_kitap_kaydi_rev_gonderim_dolum_arasinda_degisti(sandbox_state, monkeypatch):
    """Çarpan AYNI ama makbuz kitap_rev (5) ≠ dolum-anı rev (7) → kitap arada DEĞİŞTİ = `kitap_kaydi`."""
    monkeypatch.setattr(store, "stamp", lambda name: ("sha", 7))
    sinif, neden = loop._drift_sinifi_adet(
        _makbuz(eq_now=100000.0, size_mult=1.0, kitap_rev=5),
        fill_eq_now=100000.0, fill_peak=100000.0, dolum_taze=True)
    assert sinif == "kitap_kaydi", f"{sinif} — {neden}"
    assert "5" in neden and "7" in neden


def test_makbuzsuz_boyut_makbuz_yok_restart_oncesi(sandbox_state):
    """Makbuz YOK (restart-öncesi / makbuzsuz gönderim) → `makbuzsuz_boyut` + neden (ROADMAP §2-7,
    2026-08-12 forensiği: jenerik `olculemedi` bu alt-hâli gizliyordu; ad artık teşhisin kendisi).
    dolum_taze geçirilmese bile ad değişmez — makbuzsuzluk yaş sorusundan ÖNCE gelir."""
    sinif, neden = loop._drift_sinifi_adet(None, fill_eq_now=100000.0, fill_peak=100000.0)
    assert sinif == "makbuzsuz_boyut"
    assert "makbuz" in neden and len(neden) >= 20


def test_olculemedi_dolum_eq_now_yok_eski_cagiran(sandbox_state):
    """Dolum-anı eq_now geçilmedi (reconcile eq_now'suz çağrıldı) → `olculemedi`, uydurma yok."""
    sinif, neden = loop._drift_sinifi_adet(_makbuz(), fill_eq_now=None, fill_peak=100000.0)
    assert sinif == "olculemedi"
    assert "eq_now" in neden


def test_beyan_kaydi_olculemedi_makbuz_beyani_tasimadigindan(sandbox_state, monkeypatch):
    """TÜM ölçülebilir girdiler eşit (eq_now/size_mult/kitap_rev): kalan fark icra VEYA beyan_kaydi.
    Makbuz beyan_n/ofset TAŞIMADIĞINDAN ayrım YAPILAMAZ → `olculemedi` + neden İKİSİNİ de adlandırır.
    (beyan_kaydi'nin B2 tablosundaki ayırt edici alanı v222 makbuzunda YOK — bu turda genişletilmez.)"""
    monkeypatch.setattr(store, "stamp", lambda name: ("sha", 5))   # rev AYNI → kitap_kaydi elenir
    sinif, neden = loop._drift_sinifi_adet(
        _makbuz(eq_now=100000.0, size_mult=1.0, kitap_rev=5),
        fill_eq_now=100000.0, fill_peak=100000.0, dolum_taze=True)
    assert sinif == "olculemedi", f"{sinif} — {neden}"
    assert "beyan" in neden and "icra" in neden


# =================================================================================================
# B. UÇTAN UCA — `reconcile_broker_state`: alarm alanı taşır + EŞİK DEĞİŞMEZ
# =================================================================================================
def test_adet_sapmasi_alarmi_boyutlama_tabani_tasir(sandbox_state, monkeypatch):
    """08-05 uçtan uca: içeride 54, Alpaca'da 25 (>%25). Alarm VE `qty_drift` kaydı
    `drift_sinifi=boyutlama_tabani` taşır; mesaj sonuna sınıf cümlesi eklenir."""
    _wire(monkeypatch, orders=[], positions=[{"symbol": "NUE", "qty": "25"}])
    meta = {"armed": [], "size_law": {"P-NUE": _makbuz()}, "peak_equity": 100000.0}
    out = loop.reconcile_broker_state(
        meta, "2026-08-06", [],
        open_positions={"NUE": {"qty": 54.0, "scaled_out": False, "plan_id": "P-NUE",
                                "ts_open": "2026-08-06"}},   # B6: bu seansta doldu — kıyas meşru
        fill_eq_now=100000.0)
    qd = out["positions"]["qty_drift"]
    assert len(qd) == 1 and qd[0]["drift_sinifi"] == "boyutlama_tabani"
    ev = _events("MIRROR_DRIFT")
    assert any(e.get("drift_sinifi") == "boyutlama_tabani" for e in ev), "alarm alanı taşımıyor"
    assert any("sapma sınıfı: boyutlama_tabani" in str(e.get("message", "")) for e in ev)


def test_esik_degismedi_yuzde25_altinda_alarm_yok(sandbox_state, monkeypatch):
    """REGRESYON: içeride 54, Alpaca'da 46 (|46-54|/54=%14,8 < %25) → NE alarm NE `qty_drift`.
    drift_sinifi eklemek eşiği kıpırdatmadı."""
    _wire(monkeypatch, orders=[], positions=[{"symbol": "NUE", "qty": "46"}])
    meta = {"armed": [], "size_law": {"P-NUE": _makbuz()}, "peak_equity": 100000.0}
    out = loop.reconcile_broker_state(
        meta, "2026-08-06", [],
        open_positions={"NUE": {"qty": 54.0, "scaled_out": False, "plan_id": "P-NUE"}},
        fill_eq_now=100000.0)
    assert out["positions"]["qty_drift"] == []
    assert not [e for e in _events("MIRROR_DRIFT") if "adet sapması" in str(e)]


def test_eski_cagiran_fill_eq_now_suz_olculemedi_ama_alarm_yine_oter(sandbox_state, monkeypatch):
    """REGRESYON: reconcile ESKİ imzayla (fill_eq_now GEÇİLMEDEN) çağrılırsa alarm YİNE öter
    (eşik/davranış değişmedi) ve sınıf dürüstçe `olculemedi` olur — imza değişikliği bozmadı."""
    _wire(monkeypatch, orders=[], positions=[{"symbol": "NUE", "qty": "25"}])
    meta = {"armed": [], "size_law": {"P-NUE": _makbuz()}, "peak_equity": 100000.0}
    out = loop.reconcile_broker_state(
        meta, "2026-08-06", [],
        open_positions={"NUE": {"qty": 54.0, "scaled_out": False, "plan_id": "P-NUE"}})
    qd = out["positions"]["qty_drift"]
    assert len(qd) == 1 and qd[0]["drift_sinifi"] == "olculemedi"
    assert _events("MIRROR_DRIFT"), "eşik/alarm davranışı değişti — alarm ötmedi"


def test_makbuzsuz_plan_reconcile_uzerinden_makbuzsuz_boyut(sandbox_state, monkeypatch):
    """restart-öncesi plan: `size_law` YOK → sapma yine yakalanır, sınıf ADIYLA `makbuzsuz_boyut`
    (eski jenerik `olculemedi` — ROADMAP §2-7 forensiğinin kapattığı okunmazlık)."""
    _wire(monkeypatch, orders=[], positions=[{"symbol": "NUE", "qty": "25"}])
    meta = {"armed": [], "peak_equity": 100000.0}          # size_law YOK
    out = loop.reconcile_broker_state(
        meta, "2026-08-06", [],
        open_positions={"NUE": {"qty": 54.0, "scaled_out": False, "plan_id": "P-NUE"}},
        fill_eq_now=100000.0)
    assert out["positions"]["qty_drift"][0]["drift_sinifi"] == "makbuzsuz_boyut"


# =================================================================================================
# C. DİĞER BEŞ MIRROR_DRIFT NOKTASI — SABİT ETİKETLER (olgusuna uygun, yeni ölçüm değil)
# =================================================================================================
def test_kayip_pozisyon_split_brain_etiketi(sandbox_state, monkeypatch):
    """1.2b: içeride açık, Alpaca'da NE pozisyon NE emir → `split_brain` (durum ayrışması)."""
    _wire(monkeypatch, orders=[], positions=[])
    meta = {"armed": [], "peak_equity": 100000.0}
    out = loop.reconcile_broker_state(
        meta, "2026-08-06", [],
        open_positions={"NUE": {"qty": 54.0, "scaled_out": False, "plan_id": "P-NUE"}},
        fill_eq_now=100000.0)
    assert out["positions"]["missing_on_alpaca"] == ["NUE"]
    assert any(e.get("drift_sinifi") == "split_brain" for e in _events("MIRROR_DRIFT"))


def test_motor_ve_cikis_yetimi_sabit_etiketleri(sandbox_state, monkeypatch):
    """AMD gerçek giriş yetimi → `giris_yetimi` (B8 alt-adı); NVDA çıkış yetimi (kuyrukta) → `cikis_yetimi`."""
    _wire(monkeypatch,
          orders=[{"id": "p1", "symbol": "NVDA", "client_order_id": "P-1-NVDA",
                   "status": "filled", "filled_qty": "10", "legs": []},
                  {"id": "p2", "symbol": "AMD", "client_order_id": "P-1-AMD",
                   "status": "filled", "filled_qty": "10", "legs": []}],
          positions=[{"symbol": "NVDA", "qty": "10"}, {"symbol": "AMD", "qty": "10"}])
    meta = {"armed": [], "mirror_exit_pending": {"NVDA": {"plan_id": "P-1-NVDA",
                                                          "reason": "time_stop", "tries": 3}}}
    out = loop.reconcile_broker_state(meta, "2026-08-06", [], open_positions={}, fill_eq_now=100000.0)
    assert out["positions"]["engine_orphans"] == ["AMD"], "liste üyeliği değişmemeli (_mirror_busy okuyucusu)"
    assert out["positions"]["exit_orphans"] == ["NVDA"]
    ev = _events("MIRROR_DRIFT")
    # B8: tek ad ("motor_yetimi") üç olguyu gizliyordu — silahlı/yakın-kapanış izi olmayan AMD
    # GERÇEK giriş yetimidir ve alt-adıyla alarmlanır (ayrıntılı sınıf testleri v234 dosyasında).
    assert any(e.get("drift_sinifi") == "giris_yetimi" for e in ev)
    assert not any(e.get("drift_sinifi") == "motor_yetimi" for e in ev), "eski jenerik ad hâlâ basılıyor"
    assert any(e.get("drift_sinifi") == "cikis_yetimi" for e in ev)


def test_exec_sapmasi_icra_etiketi(sandbox_state, monkeypatch):
    """1.3: sim ÇIKIŞ fiyatı (100) vs Alpaca dolum fiyatı (110) sapması → tanım gereği `icra`."""
    _wire(monkeypatch,
          orders=[{"id": "o1", "symbol": "NUE", "client_order_id": "P-NUE", "status": "filled", "legs": []}],
          positions=[])
    monkeypatch.setattr(alpaca, "exit_fill_price", lambda o: 110.0)
    # B2 sonrası 1.3 kuyruk-güdümlü: yama trades.jsonl'daki SATIRA yazılır — satır önce var olmalı
    # (canlı yolda `_persist_trade` kapanış anında yazar; eski test satırsız kapanış geçiriyordu).
    store.append_jsonl("trades.jsonl", {"plan_id": "P-NUE", "ticker": "NUE", "exit": 100.0,
                                        "exit_reason": "stop", "ts_close": "2026-08-06"})
    out = loop.reconcile_broker_state(
        {"armed": []}, "2026-08-06",
        [{"plan_id": "P-NUE", "ticker": "NUE", "exit": 100.0, "exit_reason": "stop"}],
        open_positions={}, fill_eq_now=100000.0)
    assert out["drift"] and out["drift"][0]["drift_sinifi"] == "icra"
    assert any(e.get("drift_sinifi") == "icra" for e in _events("MIRROR_DRIFT"))
    satir = [r for r in store.read_jsonl("trades.jsonl") if r.get("plan_id") == "P-NUE"][-1]
    assert satir.get("alpaca_fill_price") == 110.0, "kuyruk yaması satıra yazmadı"


def test_184_ayna_cikisi_kapatilamadi_cikis_yetimi_etiketi(sandbox_state, monkeypatch):
    """`_mirror_exit_sync` (kaynak :184): iç defter KAPALI, ayna kapatılamadı → `cikis_yetimi`."""
    monkeypatch.setattr(config, "BROKER", "alpaca_paper")
    monkeypatch.setattr(alpaca, "paper_available", lambda: True)
    monkeypatch.setattr(alpaca, "close_engine_position",
                        lambda t, plan_id=None: {"ok": False, "detail": "422", "naked": False, "owned": True})
    meta = {"mirror_exit_pending": {"NVDA": {"plan_id": "P-1-NVDA", "reason": "time_stop",
                                             "since": "2026-08-01", "tries": 0, "naked": False}}}
    out = loop._mirror_exit_sync(meta, "2026-08-02")
    assert out["failed"], "başarısız kapatma kuyruğa/rapora düşmedi"
    assert any(e.get("drift_sinifi") == "cikis_yetimi" for e in _events("MIRROR_DRIFT"))
