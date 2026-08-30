"""v274 — 2026-08-23 canlı pano ihlal triyajının yedi düzeltmesine çiviler.

[1] Kaynak-farkındalı mutabakat: recompute `realized_pnl`/`cash_identity`/`taban_kaymasi` ve
    `sermaye.sermaye_taban` artık Σ'yı CANLI-SINIF (kaynak != replay_seed) satırlarla alır; bir
    re-seed'in eklediği tohum satırı SAHTE alarm üretmez (yön 1) ama gerçek canlı kayıp yine
    KIRMIZI yakar (yön 2). Ofsetin canlı payı kayıttan ölçülür (`sermaye.canli_ofset`);
    ölçülemiyorsa satır adıyla "ölçülemedi" der, uydurmaz.
[2] session_refresh sel kesimi: aynı (ip, yol) çifti ~5 dk'da bir olaya örneklenir; aradakiler
    `atlanan_n` sayacında taşınır — bilgi kaybı yok, sel yok.
[3] /api/diagnostics `dagitim` bloğu: dagit.sh beyanının YASA-6 okuyucusu — dosya yokken adlı
    boşluk, varken alanlar.
[4] trade_plans retention KURALI: işleme dönüşen plan kırpılmaz (store.merge_dated_jsonl);
    ops/plan_geri_doldur.py süpürülmüş gövdeleri kaynaklı ve idempotent iade eder.
[5] ops/alarm_backlog_digest.py: birikmiş teslim-edilmemişler TEK özet mesaja katlanır; sayaçlar
    sıfırlanmaz, damga idempotens sağlar, tek tek yeniden gönderim YOK.
[6] Litestream sır çifti: ALLOWED'da; ikisi de mevcutken state/litestream.env 0600 doğar, biri
    silinince dosya kalkar; değer hiçbir olaya düşmez.
[7] Pano bayat metin: intraday kartı "Faz 4b henüz uygulanmadı" demez — 4b kapısı + pencere
    yoluyla tutarlı metin (pozitif kontroller).
"""
from __future__ import annotations

import json
import pathlib
import stat
import time

import pytest
from fastapi.testclient import TestClient

from meridian import api, auth, recompute, secrets, sermaye, store, watchdog
from tests.conftest import betikten_modul_yukle

REPO = pathlib.Path(__file__).resolve().parent.parent
APP_JS = (REPO / "meridian" / "web" / "app.js").read_text()


def _ops_modul(ad: str):
    return betikten_modul_yukle(REPO / "ops" / f"{ad}.py", f"_v274_{ad}")


# ---- [1] sentetik defter: canlı çağ + tohum dilimi + beyanlı reset ------------------------------
RESET = {"id": "SR-TEST", "tarih": "2026-07-26T00:00:00+00:00", "ofset": 5542.09,
         "onceki_cash": 94457.91, "yeni_cash": 100000.0,
         "onceki_realized_pnl": -5542.09, "yeni_realized_pnl": 0.0,
         "tohum_etkisi_usd": -5542.09, "tohum_islem_n": 3, "canli_islem_n": 0,
         "belirsiz_islem_n": 0, "gerekce": "test tohum ayrıştırması", "arac": "test"}

SEED = [{"id": "T00001", "plan_id": "P-2022-01-06-CF", "pnl_dollars": -5000.0, "kaynak": "replay_seed"},
        {"id": "T00002", "plan_id": "P-2022-02-01-GE", "pnl_dollars": -542.09, "kaynak": "replay_seed"},
        {"id": "T00003", "plan_id": "P-2022-03-01-CF", "pnl_dollars": 0.0, "kaynak": "replay_seed"}]
CANLI = [{"id": "T00100", "plan_id": "P-2026-08-01-AAPL", "pnl_dollars": 100.0, "kaynak": "live_paper"},
         {"id": "T00101", "plan_id": "P-2026-08-02-MSFT", "pnl_dollars": 50.0}]   # damgasız → belirsiz → canlı-sınıf


def _defter_kur(trades):
    store.write_json("portfolio.json", {"cash": 100150.0, "realized_pnl": 150.0,
                                        "positions": {}, "sermaye_resetleri": [RESET]})
    store.write_jsonl("trades.jsonl", trades)


def _satir(rows, ad):
    return next(r for r in rows if r["check"] == ad)


def test_reseed_tohum_satiri_SAHTE_alarm_uretmez(sandbox_state):
    """YÖN 1: tohum dilimi (re-seed'in eklediği dahil) kimlikleri KIPIRDATMAZ — eski kaynak-körü
    formülün 2026-08-22/23 yanlış-alarmı yapısal olarak kapalı."""
    _defter_kur(SEED + CANLI)
    rows = recompute.report()["rows"]
    for ad in ("realized_pnl", "cash_identity", "taban_kaymasi"):
        s = _satir(rows, ad)
        assert s["ok"] is True, f"{ad} tohumla KIRMIZI: {s}"
    # re-seed simülasyonu: YENİ tohum satırları eklenir, realized kıpırdamaz
    yeni_tohum = [{"id": "T00004", "plan_id": "P-2024-01-01-NVDA", "pnl_dollars": -1000.0,
                   "kaynak": "replay_seed"}]
    _defter_kur(SEED + yeni_tohum + CANLI)
    rows = recompute.report()["rows"]
    for ad in ("realized_pnl", "cash_identity", "taban_kaymasi"):
        s = _satir(rows, ad)
        assert s["ok"] is True, f"{ad} re-seed sonrası SAHTE alarm: {s}"


def test_gercek_canli_kayip_HALA_kirmizi(sandbox_state):
    """YÖN 2: canlı-sınıf bir satırın kaybolması dedektörü yakar — kaynak süzgeci gerçek
    ayrışmayı yutan bir susturucu DEĞİLDİR."""
    _defter_kur(SEED + CANLI[:1])                 # +50$'lık damgasız canlı satır KAYIP
    rows = recompute.report()["rows"]
    s = _satir(rows, "realized_pnl")
    assert s["ok"] is False and "AYRIŞMA" in s["detail"], s
    assert _satir(rows, "taban_kaymasi")["ok"] is False


def test_sermaye_taban_tohumdan_bagimsiz_canliya_duyarli(sandbox_state):
    _defter_kur(SEED + CANLI)
    pf = store.read_json("portfolio.json", {})
    t0 = sermaye.sermaye_taban(pf, store.read_jsonl("trades.jsonl"))
    assert t0 == 0.0, t0                          # realized 150 − Σ canlı 150
    # tohum eklemek tabanı KIPIRDATMAZ (eski formülde 1000$ düşerdi → sahte GERİLEME)
    _defter_kur(SEED + [{"id": "T9", "pnl_dollars": -1000.0, "kaynak": "replay_seed"}] + CANLI)
    assert sermaye.sermaye_taban(pf, store.read_jsonl("trades.jsonl")) == t0
    # canlı satır silmek tabanı OYNATIR (gerileme dedektörünün gördüğü büyüklük)
    _defter_kur(SEED + CANLI[:1])
    assert sermaye.sermaye_taban(pf, store.read_jsonl("trades.jsonl")) == 50.0


def test_canli_ofset_kayittan_olculur_ve_olculemeyen_UYDURULMAZ(sandbox_state):
    _defter_kur(SEED + CANLI)
    co = sermaye.canli_ofset(store.read_json("portfolio.json", {}))
    assert co == {"deger": 0.0, "neden": None, "n_reset": 1}
    assert sermaye.canli_ofset({}) == {"deger": 0.0, "neden": None, "n_reset": 0}
    # damga basılmadan yazılmış reset: tohum etkisi None + tohum_islem_n>0 → pay AYRIŞTIRILAMAZ
    bozuk = dict(RESET, tohum_etkisi_usd=None)
    co2 = sermaye.canli_ofset({"sermaye_resetleri": [bozuk]})
    assert co2["deger"] is None and "ayrıştırılamıyor" in co2["neden"]
    # ve recompute satırları bu hâlde "ölçülemedi" der, sayı uydurmaz, kırmızı da yakmaz
    pf = store.read_json("portfolio.json", {})
    pf["sermaye_resetleri"] = [bozuk]
    store.write_json("portfolio.json", pf)
    rows = recompute.report()["rows"]
    for ad in ("realized_pnl", "taban_kaymasi"):
        s = _satir(rows, ad)
        assert s["ok"] is True and s["b"] is None and "YAPILAMADI" in s["detail"], s


def test_watchdog_sermaye_taban_kanonikten_ve_reseed_gerilemesi_yok(sandbox_state):
    _defter_kur(SEED + CANLI)
    watchdog.monotonicity_report(persist=True)
    taban = store.read_json(watchdog.MONOTONIC_FILE, {}).get("sermaye_taban")
    assert taban == sermaye.sermaye_taban()
    # re-seed tohum ekler; trades sayacı ARTAR (gerileme değil), sermaye_taban SABİT kalır
    _defter_kur(SEED + [{"id": "T9", "pnl_dollars": -777.0, "kaynak": "replay_seed"}] + CANLI)
    rep = watchdog.monotonicity_report(persist=False)
    assert not [r for r in rep.get("regressions", []) if r["field"] == "sermaye_taban"], rep


# ---- [2] session_refresh örneklemesi ------------------------------------------------------------
def test_ornekleme_penceresi_ve_atlanan_n(sandbox_state):
    f = api._session_refresh_ornekle
    t0 = 1000.0
    assert f("127.0.0.1", "/api/summary", now=t0) == 0            # ilk olay: yaz, atlanan 0
    assert f("127.0.0.1", "/api/summary", now=t0 + 10) is None    # pencere içi: biriktir
    assert f("127.0.0.1", "/api/summary", now=t0 + 20) is None
    assert f("127.0.0.1", "/api/summary", now=t0 + 30) is None
    # farklı yol AYRI pencere: selin anahtarı (ip, yol) çiftidir
    assert f("127.0.0.1", "/api/today", now=t0 + 31) == 0
    # pencere dolunca: yaz ve ATLANANLARI taşı (bilgi kaybı yok)
    n = f("127.0.0.1", "/api/summary", now=t0 + api.REFRESH_ORNEKLEM_S + 1)
    assert n == 3, n
    assert f("127.0.0.1", "/api/summary", now=t0 + api.REFRESH_ORNEKLEM_S + 2) is None


def test_middleware_ayni_pencerede_TEK_session_refresh_olayi(sandbox_state, monkeypatch):
    auth.set_password("cok-uzun-ve-guclu-parola-123")
    iat = int(time.time()) - 7 * 3600
    tok = auth._sign(iat + 12 * 3600, iat)
    monkeypatch.setattr(api, "DASH_TOKEN", None)
    c = TestClient(api.app)
    hdr = {"cookie": f"{auth.COOKIE_NAME}={tok}"}
    r1 = c.get("/api/summary", headers=hdr)
    assert r1.status_code == 200
    # ikinci tazeleme AYNI (ip, yol) penceresinde → olay YAZILMAZ, sayaç birikir
    yeni = [v for v in r1.headers.get_list("set-cookie") if v.startswith(auth.COOKIE_NAME)][0]
    c.get("/api/summary", headers={"cookie": yeni.split(";")[0]})
    evs = [json.loads(s) for s in (sandbox_state / "events.jsonl").read_text().splitlines() if s.strip()]
    ref = [e for e in evs if e.get("event") == "session_refresh"]
    assert len(ref) == 1, [e.get("event") for e in evs]
    assert ref[0].get("atlanan_n") == 0 and ref[0].get("orneklem_s") == 300, ref[0]


# ---- [3] dagitim bloğu --------------------------------------------------------------------------
def test_diagnostics_dagitim_iki_dal(sandbox_state, monkeypatch):
    monkeypatch.setattr(api, "DASH_TOKEN", None)
    c = TestClient(api.app)
    d = c.get("/api/diagnostics").json()
    assert "olculemedi" in d.get("dagitim", {}), d.get("dagitim")
    assert "beyanlı dağıtım yok" in d["dagitim"]["olculemedi"]
    beyan = {"deployed_sha": "abc1234def", "dagitildi_utc": "2026-08-23T10:00:00Z",
             "dagitan_host": "l0", "kirli_gec_kullanildi": False}
    store.write_json("dagitim.json", beyan)
    d2 = c.get("/api/diagnostics", params={"taze": 1}).json()
    assert d2["dagitim"] == beyan, d2["dagitim"]


def test_pano_dagitim_satiri_pozitif_kontrol():
    assert "dagitimSatiri" in APP_JS and "Canlıdaki dağıtım" in APP_JS
    # Gözetim render'ına gerçekten bağlı (yalnız tanımlı değil)
    assert APP_JS.count("dagitimSatiri(") >= 2


# ---- [4] retention kuralı + geri-doldurma -------------------------------------------------------
def test_merge_dated_islem_donusen_plan_KIRPILMAZ(sandbox_state):
    planlar = [{"id": f"P{i:03d}", "date": f"2022-{(i % 12) + 1:02d}-01"} for i in range(60)]
    store.write_jsonl("trade_plans.jsonl", planlar)
    # en ESKİ iki plan işleme dönüşmüş — eski kural onları süpürürdü
    store.write_jsonl("trades.jsonl", [{"id": "T1", "plan_id": "P000"}, {"id": "T2", "plan_id": "P001"}])
    store.merge_dated_jsonl("trade_plans.jsonl", "2026-08-23",
                            [{"id": "PYENI", "date": "2026-08-23"}], cap=10)
    kalan = {p["id"] for p in store.read_jsonl("trade_plans.jsonl")}
    assert {"P000", "P001", "PYENI"} <= kalan, kalan
    assert len(kalan) == 12, kalan                # tavan 10 + korunan 2 (kural, sabit değil)
    # işleme dönüşmemiş defterlerde davranış DEĞİŞMEZ (candidates düz tavan)
    store.write_jsonl("candidates.jsonl", [{"id": f"C{i}", "date": "2022-01-01"} for i in range(30)])
    store.merge_dated_jsonl("candidates.jsonl", "2026-08-23", [{"id": "CY", "date": "2026-08-23"}], cap=5)
    assert len(store.read_jsonl("candidates.jsonl")) == 5


def test_plan_geri_doldur_kaynakli_ve_idempotent(sandbox_state, tmp_path, capsys):
    m = _ops_modul("plan_geri_doldur")
    store.write_jsonl("trades.jsonl", [{"id": f"T{i}", "plan_id": f"P{i}"} for i in range(1, 5)])
    store.write_jsonl("trade_plans.jsonl", [{"id": "P3", "date": "d"}, {"id": "P4", "date": "d"}])
    kaynak = tmp_path / "kaynak_plans.jsonl"
    kaynak.write_text(json.dumps({"id": "P1", "date": "2022-01-01", "entry_trigger": 10.0}) + "\n"
                      + json.dumps({"id": "P3", "date": "d", "entry_trigger": 99.0}) + "\n")
    # KURU KOŞU: hiçbir bayt yazılmaz; P2 kaynakta yok → çıkış 1 ve adıyla raporlanır
    assert m.main(["--kaynak", str(kaynak)]) == 1
    assert len(store.read_jsonl("trade_plans.jsonl")) == 2
    cikti = capsys.readouterr().out
    assert "P2" in cikti and "UYDURULMAZ" in cikti and "KURU KOŞU" in cikti
    # UYGULA: P1 iade edilir (BAŞA), mevcut P3 EZİLMEZ, P2 hâlâ eksik → çıkış 1
    assert m.main(["--kaynak", str(kaynak), "--uygula"]) == 1
    rows = store.read_jsonl("trade_plans.jsonl")
    assert [r["id"] for r in rows] == ["P1", "P3", "P4"]
    assert next(r for r in rows if r["id"] == "P3").get("entry_trigger") is None, \
        "mevcut satır kaynaktan EZİLDİ — idempotenz ihlali"
    # İKİNCİ koşum yeni satır yazmaz (idempotent); P2 için kaynak eklenince 0'a düşer
    assert m.main(["--kaynak", str(kaynak), "--uygula"]) == 1
    assert [r["id"] for r in store.read_jsonl("trade_plans.jsonl")] == ["P1", "P3", "P4"]
    kaynak2 = tmp_path / "k2.json"
    kaynak2.write_text(json.dumps([{"id": "P2", "date": "2022-02-01"}]))
    assert m.main(["--kaynak", str(kaynak), "--kaynak", str(kaynak2), "--uygula"]) == 0
    assert {r["id"] for r in store.read_jsonl("trade_plans.jsonl")} == {"P1", "P2", "P3", "P4"}


# ---- [5] alarm backlog digest -------------------------------------------------------------------
def test_digest_tek_mesaja_katlar_damgalar_ve_sayac_sifirlanmaz(sandbox_state, monkeypatch):
    m = _ops_modul("alarm_backlog_digest")
    store.write_json("notify_undelivered.json",
                     {"MECHANISM_STALE": 3, "BROKER_REJECT": 1, "_toplam": 4, "_teslim_hatasi": 1})
    store.write_jsonl("events.jsonl", [
        {"ts": "2026-08-20T01:00:00+00:00", "level": "alarm", "alarm": "MECHANISM_STALE", "message": "a"},
        {"ts": "2026-08-22T09:30:00+00:00", "level": "alarm", "alarm": "MECHANISM_STALE", "message": "b"}])
    gonderilen = []
    monkeypatch.setattr(m.notify, "configured", lambda: True)
    monkeypatch.setattr(m.notify, "send", lambda t: gonderilen.append(t) or True)
    assert m.main(["--uygula"]) == 0
    assert len(gonderilen) == 1, "TEK özet mesaj sözü ihlal edildi"
    msg = gonderilen[0]
    assert "MECHANISM_STALE ×3" in msg and "BROKER_REJECT ×1" in msg
    assert "2026-08-20" in msg and "2026-08-22" in msg          # ilk/son ÖLÇÜLDÜ
    assert "ölçülemedi" in msg                                   # BROKER_REJECT'in defterde satırı yok
    d = store.read_json("notify_undelivered.json", {})
    assert d["MECHANISM_STALE"] == 3 and d["_toplam"] == 4, "sayaç SIFIRLANDI — kümülatif sözleşme ihlali"
    assert d["_digest"]["toplam_kapsanan"] == 4
    # idempotens: yeni birikme yokken İKİNCİ koşum göndermez
    assert m.main(["--uygula"]) == 0
    assert len(gonderilen) == 1


def test_digest_gonderim_duserse_damga_BASILMAZ(sandbox_state, monkeypatch):
    m = _ops_modul("alarm_backlog_digest")
    store.write_json("notify_undelivered.json", {"DATA_QUALITY": 2, "_toplam": 2})
    monkeypatch.setattr(m.notify, "configured", lambda: True)
    monkeypatch.setattr(m.notify, "send", lambda t: False)
    assert m.main(["--uygula"]) == 1
    assert "_digest" not in store.read_json("notify_undelivered.json", {})
    # kanal yokken teslim İDDİA EDİLMEZ
    monkeypatch.setattr(m.notify, "configured", lambda: False)
    assert m.main(["--uygula"]) == 2


# ---- [6] litestream sır çifti -------------------------------------------------------------------
def test_litestream_env_uret_sil_0600_ve_deger_loglanmaz(sandbox_state, monkeypatch):
    assert {"LITESTREAM_ACCESS_KEY_ID", "LITESTREAM_SECRET_ACCESS_KEY"} <= set(secrets.ALLOWED)
    monkeypatch.delenv("LITESTREAM_ACCESS_KEY_ID", raising=False)
    monkeypatch.delenv("LITESTREAM_SECRET_ACCESS_KEY", raising=False)
    GIZ1, GIZ2 = "AKIAtestKIMLIK9999", "cokGizliSecretDeger8888"
    secrets.set("LITESTREAM_ACCESS_KEY_ID", GIZ1)
    assert secrets.litestream_env_sync()["durum"] == "yok"       # tek anahtar: yarım kimlik ÜRETİLMEZ
    p = sandbox_state / "litestream.env"
    assert not p.exists()
    secrets.set("LITESTREAM_SECRET_ACCESS_KEY", GIZ2)
    assert secrets.litestream_env_sync()["durum"] == "yazildi"
    assert p.exists() and stat.S_IMODE(p.stat().st_mode) == 0o600
    icerik = p.read_text()
    assert f"LITESTREAM_ACCESS_KEY_ID={GIZ1}\n" in icerik
    assert f"LITESTREAM_SECRET_ACCESS_KEY={GIZ2}\n" in icerik
    # değer HİÇBİR olaya düşmez (obs → events.jsonl)
    ev = (sandbox_state / "events.jsonl")
    ham = ev.read_text() if ev.exists() else ""
    assert GIZ1 not in ham and GIZ2 not in ham, "sır değeri olay defterine sızdı"
    # biri silinirse dosya KALKAR
    secrets.delete("LITESTREAM_SECRET_ACCESS_KEY")
    assert secrets.litestream_env_sync()["durum"] == "kaldirildi"
    assert not p.exists()


def test_api_secrets_yolu_litestream_kancasini_cagirir(sandbox_state, monkeypatch):
    monkeypatch.setattr(api, "DASH_TOKEN", None)
    monkeypatch.delenv("LITESTREAM_ACCESS_KEY_ID", raising=False)
    monkeypatch.delenv("LITESTREAM_SECRET_ACCESS_KEY", raising=False)
    c = TestClient(api.app)
    r1 = c.post("/api/secrets/LITESTREAM_ACCESS_KEY_ID", json={"value": "idDEGERI12345"}).json()
    assert r1["ok"] and r1["litestream_env"]["durum"] == "yok"
    r2 = c.post("/api/secrets/LITESTREAM_SECRET_ACCESS_KEY", json={"value": "secretDEGERI6789"}).json()
    assert r2["litestream_env"]["durum"] == "yazildi"
    assert (sandbox_state / "litestream.env").exists()
    # litestream-dışı bir sır kancayı TETİKLEMEZ (yanıt alanı None)
    r3 = c.post("/api/secrets/TELEGRAM_CHAT_ID", json={"value": "12345"}).json()
    assert r3["litestream_env"] is None
    r4 = c.request("DELETE", "/api/secrets/LITESTREAM_ACCESS_KEY_ID").json()
    assert r4["litestream_env"]["durum"] == "kaldirildi"
    assert not (sandbox_state / "litestream.env").exists()
    # panoda alan çifti de var (pozitif kontrol)
    assert "LITESTREAM_ACCESS_KEY_ID" in APP_JS and "LITESTREAM_SECRET_ACCESS_KEY" in APP_JS


# ---- [7] bayat pano kartı -----------------------------------------------------------------------
def test_intraday_karti_bayat_cumleyi_tasimiyor():
    assert "henüz uygulanmadı" not in APP_JS, "bayat 'Faz 4b henüz uygulanmadı' cümlesi hâlâ panoda"
    assert "Faz 4b yok" not in APP_JS
    assert "Faz 4b UYGULANDI" in APP_JS
    # kart bugünkü mekanizmayla TUTARLI: 4b tek-kapı gönderimi + ayrı yetkili sabah penceresi
    assert "gerçek 4b emri" in APP_JS
    assert "EXE-009" in APP_JS and "bu bayrağa bağlı DEĞİLDİR" in APP_JS


def test_intraday_karti_koddaki_gercekle_tutarli():
    """Kart metninin dayandığı iki olgu KODDAN doğrulanır (metin koddan koparsa bu çivi söyler):
    _faz4b gerçek gönderim yapar (mirror_submit tek kapısı) ve pencere yolu INTRADAY_ARM'dan
    bağımsızdır."""
    src = (REPO / "meridian" / "intraday_cycle.py").read_text()
    assert "def _faz4b" in src and "mirror_submit_ve_kalicilastir" in src
    assert "intraday_4b_submitted" in src
    assert "INTRADAY_ARM'a bağlı\ndeğildir" in src or "INTRADAY_ARM'a bağlı değildir" in src
