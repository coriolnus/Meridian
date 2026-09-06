"""test_as_of_pit_okuyucu_v429.py — TSK-156 dilim-2 (b): pitlaw ('constituents','as_of') sınıf
kararı + `as_of_pit_durumu`nun OKUYUCUSU (`universe_drift()`/`api`).

BAĞLAM: `constituents.as_of_pit_durumu(date)` (TSK-154, D2) doğduğundan beri OKUYUCUSUZDU — ajan
ölçümü 2026-09-05: `api.py` yalnız `health()`/`universe_drift()`/`current()` çağırıyordu, hiçbiri
`as_of_pit_durumu`yu çağırmıyordu (Yasa 6 ihlali: üretilip tüketilmeyen beyan). Aynı anda `pitlaw`
kaydı `('constituents','as_of')`i besleyeni HTTP 403 aldığı gerekçesiyle `PIT_SOZLESMELI_BESLEYENI_
KAPALI` (üçüncü kova) sınıfında bekletiyordu — o gerekçe BAYATTI: TSK-156 dilim-1 (#19, EDG-076)
besleyeni AÇIK ölçtü (`_fetch_hist_changes()` Wikipedia 'Historical components' tablosunu oldid/sha
damgasıyla okur, K1 28/28, K2 as_of fark 0, rename EQR→VMRK elle eşlemeli) ve gerçek üretim
tüketicisi doğdu (`backtest.replay(..., uyelik=...)`, TSK-159 S2, main dalında — bu worktree
dalının forklandığı noktadan SONRA merge oldu, bkz. devir notu).

BU KARTIN İŞİ: (1) kaydı `PIT_KAYNAKLAR`a taşı (pitlaw.py'de yapıldı, burada MEKANİK çivilenir);
(2) `universe_drift()`e `as_of_pit` okuyucusu ekle (Yasa 6); (3) o alanın `/api/diagnostics`
ucundan (universe_drift.json'ı servis eden uç) da geçtiğini çivile.

İKİ MUTASYON (devir notunda elle doğrulanır, TDD gereği — koda GEÇİCİ uygulanıp geri alınır):
  MUTASYON 1 — `('constituents','as_of')` `PIT_KAYNAKLAR`dan çıkarılıp geri
  `PIT_SOZLESMELI_BESLEYENI_KAPALI`ya taşınırsa `test_kayit_PIT_KAYNAKLARDA_ve_KAPALI_KOVADA_DEGIL`
  KIRMIZI olur.
  MUTASYON 2 — `universe_drift()`ün `as_of_pit` alanı (ok dalından) kaldırılırsa
  `test_universe_drift_as_of_pit_sozlesmesi_ok_dalinda` KIRMIZI olur.
"""
from __future__ import annotations

import datetime as dt

from fastapi.testclient import TestClient

from meridian import api, pitlaw, store
from meridian.adapters import constituents


# =================================================================================================
# A) pitlaw KAYDI — sınıf taşındı, gerekçe ölçümlü
# =================================================================================================
def test_kayit_PIT_KAYNAKLARDA_ve_KAPALI_KOVADA_DEGIL():
    """MUTASYON 1 HEDEFİ. Besleyen artık AÇIK ölçüldü (TSK-156 dilim-1 #19, EDG-076) — kayıt
    beyaz listede olmalı, 'besleyeni kapalı' üçüncü kovada KALMAMALI (iki defter ayrık olmalı,
    aynı anahtar ikisinde birden duramaz — emsal `test_IKI_DEFTER_AYRIK`, v341)."""
    assert ("constituents", "as_of") in pitlaw.PIT_KAYNAKLAR, (
        "('constituents','as_of') PIT_KAYNAKLAR'da değil — besleyen açık ölçüldü (EDG-076), "
        "kayıt beyaz listeye taşınmalıydı")
    assert ("constituents", "as_of") not in pitlaw.PIT_SOZLESMELI_BESLEYENI_KAPALI, (
        "('constituents','as_of') hâlâ 'besleyeni kapalı' kovasında — bayat gerekçe (Wikipedia "
        "403) düzeltilmeden taşıma yarım kalmış")


def test_gerekce_uzunluk_ve_olcum_kelimeleri():
    """Gerekçe Yasa 4 eşiğini (≥20 anlamlı karakter) geçmeli VE ölçümün iki çapasını taşımalı:
    besleyenin damgası (`oldid`) ve tek-kaynak sınırının konusu (`rename`) — kısa/soyut bir
    gerekçe ('artık açık' gibi) ölçümü DEĞİL bir hissi kaydederdi (uydurma yasağı)."""
    gerekce = pitlaw.PIT_KAYNAKLAR[("constituents", "as_of")]
    assert len(gerekce.strip()) >= 20, f"gerekçe çok kısa: {gerekce!r}"
    assert "oldid" in gerekce, f"gerekçe besleyenin damgasını (oldid) anmıyor: {gerekce!r}"
    assert "rename" in gerekce, f"gerekçe tek-kaynak sınırını (rename) anmıyor: {gerekce!r}"


def test_kapali_kova_BOS_ama_SILINMEDI():
    """Kova tarihsel bir sınıftır (pitlaw.py şerhi, § PIT_SOZLESMELI_BESLEYENI_KAPALI) — tek
    sakini taşındığı için BOŞ, ama sözlüğün kendisi bir sonraki 'sözleşme var, besleyen kapalı'
    kaynak için açık durur (emsal: BILINEN_IHLALLER'in boş kalışı, EDG-2026-062)."""
    assert pitlaw.PIT_SOZLESMELI_BESLEYENI_KAPALI == {}
    assert isinstance(pitlaw.PIT_SOZLESMELI_BESLEYENI_KAPALI, dict)


def test_as_of_hala_constituents_modulunde_tanimli():
    """İKİ YÖNLÜ TAMLIĞIN İLK YÖNÜ (emsal `test_kayittaki_her_sembol_modulunde_GERCEKTEN_tanimli`,
    v341) — taşınan kaydın sembolü kaynakta GERÇEKTEN var, taşıma bir yazım hatasıyla kopmadı."""
    assert hasattr(constituents, "as_of") and callable(constituents.as_of)


# =================================================================================================
# B) universe_drift() — as_of_pit OKUYUCUSU (Yasa 6)
# =================================================================================================
def _dolgu(gercek: list[str] | None = None, n: int = 460) -> list[str]:
    """MAKULLUK KAPISINI (MIN_MEMBERS=400) geçecek kadar sentetik dolgu — biçim `_real_list`
    (test_sp500_tarihsel_kaynak_v422.py) ile AYNI: kısa alfasayısal ad, gerçek ticker şekli."""
    gercek = gercek or []
    dolgu = [f"PAD{i:03d}" for i in range(max(0, n - len(gercek)))]
    return gercek + dolgu


def test_universe_drift_as_of_pit_sozlesmesi_ok_dalinda(sandbox_state, monkeypatch):
    """MUTASYON 2 HEDEFİ (ok dalı). `as_of_pit` alanı `as_of_pit_durumu(bugün)`ün AYNEN dönüşüdür
    — iki ayrı çağrı aynı anlık görüntüden okunduğu sürece birebir eşleşmeli (tek-kaynak yasası)."""
    today = dt.date.today().isoformat()
    store.write_json(constituents.CACHE, {
        "as_of": today, "current": _dolgu(),
        "changes": [{"date": "2099-01-01", "added": "NEW", "removed": "OLD", "reason": "x"}],
        "changes_kaynak": "wikipedia_historical_components",
        "changes_meta": {"oldid": 1, "sha256": "x", "n_satir": 1, "n_tarih_yok": 0,
                         "cekim_ts": today}})
    monkeypatch.setattr(constituents, "current", lambda *a, **k: _dolgu())

    d = constituents.universe_drift()
    assert d["status"] == "ok"
    assert "as_of_pit" in d, "universe_drift() as_of_pit alanını taşımıyor (Yasa 6 okuyucusu yok)"
    beklenen = constituents.as_of_pit_durumu(today)
    assert d["as_of_pit"] == beklenen, (
        f"as_of_pit universe_drift() içinde farklı hesaplanıyor: {d['as_of_pit']} != {beklenen}")
    for k in ("pit", "neden", "changes_kaynak", "kaynak_sinifi"):
        assert k in d["as_of_pit"], f"as_of_pit sözleşmesinde eksik alan: {k}"
    assert d["as_of_pit"]["pit"] is True, "gelecek tarihli değişiklik satırı pit=True üretmeli"
    assert d["as_of_pit"]["changes_kaynak"] == "wikipedia_historical_components"
    assert d["as_of_pit"]["kaynak_sinifi"] == "tarihsel_tablo"


def test_universe_drift_as_of_pit_bos_gunluk_pit_false_nedenli(sandbox_state, monkeypatch):
    """Değişiklik günlüğü boşken (survivorship) `as_of_pit.pit` False VE `neden` BOŞ değil —
    uydurma yasağı: 'ölçemedik' ile 'öyle değil' ayrı beyan taşır."""
    today = dt.date.today().isoformat()
    store.write_json(constituents.CACHE, {
        "as_of": today, "current": _dolgu(),
        "changes": [], "changes_kaynak": None, "changes_meta": None})
    monkeypatch.setattr(constituents, "current", lambda *a, **k: _dolgu())

    d = constituents.universe_drift()
    assert d["status"] == "ok"
    assert d["as_of_pit"]["pit"] is False
    assert d["as_of_pit"]["neden"], "pit=False iken neden BOŞ olamaz (uydurma yasağı)"
    assert d["as_of_pit"]["changes_kaynak"] is None
    assert d["as_of_pit"]["kaynak_sinifi"] is None


def test_universe_drift_as_of_pit_unknown_dalinda_da_tasinir(sandbox_state, monkeypatch):
    """Üyelik kaynağı çökse bile (`current()` makullük kapısından geçmeyen bir liste döndürüyor)
    `as_of_pit` beyanı KAYBOLMAZ — `hic_uye_canlida`nın (TSK-143) taşıdığı AYNI disiplin."""
    today = dt.date.today().isoformat()
    store.write_json(constituents.CACHE, {
        "as_of": today, "current": [],
        "changes": [{"date": "2099-01-01", "added": "NEW", "removed": "OLD"}],
        "changes_kaynak": "wikipedia_historical_components", "changes_meta": None})
    monkeypatch.setattr(constituents, "current", lambda *a, **k: [])

    d = constituents.universe_drift()
    assert d["status"] == "unknown"
    assert "as_of_pit" in d, "unknown dalında as_of_pit alanı YOK — beyan üyelik kaynağıyla düşüyor"
    assert d["as_of_pit"]["pit"] is True


# =================================================================================================
# C) /api/diagnostics — universe_drift.json'ı servis eden uç as_of_pit'i geçiriyor
# =================================================================================================
def test_api_diagnostics_universe_drift_as_of_pit_gecer(sandbox_state):
    """API katmanı: `loop._universe_drift_check`in `universe_drift()`in TAMAMINI (`{**rep, ...}`)
    diske yazdığı ve `/api/diagnostics`in o dosyayı BÜTÜN OLARAK okuduğu sözleşme (modül başlığı
    (h), constituents.py) — yeni alan ikinci bir kablo döşenmeden pano yüzeyine ulaşır."""
    beklenen_as_of_pit = {"pit": True, "neden": None,
                          "changes_kaynak": "wikipedia_historical_components",
                          "kaynak_sinifi": "tarihsel_tablo", "changes_meta": None}
    store.write_json("universe_drift.json", {
        "status": "ok", "n_stale": 0, "stale": [],
        "as_of_pit": beklenen_as_of_pit,
        "date": dt.date.today().isoformat()})

    c = TestClient(api.app)
    d = c.get("/api/diagnostics").json()
    assert "universe_drift" in d, "/api/diagnostics universe_drift anahtarını hiç taşımıyor"
    assert d["universe_drift"]["as_of_pit"] == beklenen_as_of_pit, (
        f"/api/diagnostics universe_drift.json'daki as_of_pit'i AYNEN geçirmiyor: "
        f"{d['universe_drift'].get('as_of_pit')}")
