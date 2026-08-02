"""test_sprint_audit_v45.py — sprint (tur 32) + sprint_run (tur 33) denetimi, 2026-07-21.

Sprint, canlı defterin YANINDA koşan tek şey: ayrı süreç, ayrı MERIDIAN_ROOT, ayrı state. 7. soru:
  SR1 "canlı defter ASLA dokunulmaz" → izolasyon üç şeye dayanıyor (kopyalama, MERIDIAN_ROOT,
     SKIP_COPY) ve üçü de tek tek kontrol edilmiyordu. Bir gün biri env'i unutursa sprint CANLI
     trades.jsonl'ı sıfırlar — geri dönüşü olmayan bir hata.
  SR2 "pencereler sabittir (p-hacking yok)" → CUTOFF/EVAL_START env'den okunabilir hale gelirse
     operatör pencere alışverişi yapabilir; sabitlik yazılıydı, test edilmiyordu
  SR3 "sonuç EĞİTİM kalibrasyonudur, canlıya karışmaz" → canlı kalibrasyon/otonomi merdiveni
     sprint dosyalarını okumamalı
  SR4 "HALT kum havuzuna girmez" → kopyalanan bir kill-switch sprint'i sessizce faydasız kılar (audit #23)
"""
from __future__ import annotations

import inspect
import json
import os
import pathlib

import pytest
import yaml

from meridian import config, sprint, storage, store


SRC = inspect.getsource(sprint)


# ---------- SR1: izolasyon ----------
def test_sr1_child_runs_with_its_own_meridian_root():
    assert '"MERIDIAN_ROOT": str(sbroot)' in SRC, "çocuk süreç CANLI state'e yazabilir"
    assert '"MERIDIAN_BROKER": "internal"' in SRC, "sprint aynaya emir göndermemeli"


def test_sr1b_reset_only_touches_the_sandbox(sandbox_state, tmp_path):
    """_reset_sandbox_state VERİLEN dizini sıfırlar; canlı state'e tek bir yazma bile olmamalı."""
    live_trades = config.STATE / "trades.jsonl"
    store.write_jsonl("trades.jsonl", [{"id": "T1"}])
    before = live_trades.read_text()
    sb = tmp_path / "sbstate"
    sb.mkdir()
    sprint._reset_sandbox_state(sb)
    assert (sb / "trades.jsonl").read_text() == ""            # kum havuzu sıfırlandı
    assert live_trades.read_text() == before                  # canlı defter DOKUNULMADI
    assert (sb / "history" / "v0001.yaml").exists()           # geri alma için ebeveyn anlık görüntüsü


def test_sr1c_sandbox_gets_a_flat_book_and_v1_parent_none(tmp_path):
    sb = tmp_path / "sbstate"; sb.mkdir()
    sprint._reset_sandbox_state(sb)
    pf = json.loads((sb / "portfolio.json").read_text())
    assert pf["positions"] == {} and pf["armed"] == [] and pf["realized_pnl"] == 0.0
    strat = yaml.safe_load((sb / "strategy.yaml").read_text())
    assert strat["version"] == 1 and strat["parent"] is None


# ---------- SR4: HALT ve sırlar kopyalanmaz ----------
def test_sr4_halt_and_secrets_never_enter_the_sandbox():
    for name in ("HALT", "secrets.json", "bars", "sprint"):
        assert name in sprint.SKIP_COPY, f"{name} kum havuzuna kopyalanıyor"


def test_sr4b_seans_ici_arsivler_kum_havuzuna_kopyalanmaz():
    """SR4'ün BOYUT kardeşi — AYRI test, çünkü sınıfı ayrı. HALT/secrets bir İZOLASYON iddiasıdır
    (kopyalanırsa sprint yanlış ölçer); bars_intraday/intraday_bars ise izolasyonu bozmaz, yalnız
    kum havuzunu şişirir — sınıf BOYUT. 2026-08-02 A1 ölçümü: bu iki seans-içi önbellek 83M/sandbox
    (43M + 40M), yani ~110M'lik kum havuzunun dörtte üçü; sprint çocuğunun yolunda OKUYUCULARI YOK.
    SKIP_COPY bu kararın TEK ÇİVİLEME NOKTASI: kümeden düşerlerse kopyalama sessizce geri gelir —
    hiçbir şey patlamaz, yalnız state/sprint yeniden şişer, yani testsiz fark edilmez."""
    for name in ("bars_intraday", "intraday_bars"):
        assert name in sprint.SKIP_COPY, \
            f"{name} kum havuzuna kopyalanıyor (2026-08-02 ölçümü: ikisi birlikte 83M/sandbox)"


def test_sr4c_depolama_artefakti_kum_havuzuna_kopyalanmaz():
    """SR4 AİLESİ (İZOLASYON), SR4b'nin BOYUT ailesi DEĞİL — ayrım bu testin varlık sebebidir.

    `meridian.db` kopyalanınca kum havuzu şişmez (defter dosyalarının kendisi zaten kopyalanıyor);
    BOZULAN ŞEY ÖLÇÜMÜN KENDİSİDİR. WP-H/H9'dan (2026-07-31) beri altı defter DB varsa SQLite'tan
    okunur, oysa `_reset_sandbox_state` defterleri HAM DOSYA yazımıyla sıfırlar — DB kopyası
    dururken o sıfırlama çocuğun store okumalarına GÖRÜNMEZ. Ölçülen sonuç (A1, salt-okuma):
    çocuk canlının `portfolio.json`unu DB kopyasından okuyup `last_date="2026-07-31"` görüyor,
    `loop.daily_cycle` monotonluk bekçisi eval penceresindeki 522/522 seansı
    `regressive_session_refused` ile reddediyor ve 154 kadans koşusunun tamamı ~60 sn'de
    `phase=done, n_v1=0` ile bitiyordu. Yani HALT ile aynı sınıf (audit #23): kopyalanan tek bir
    artefakt tüm kum havuzu girişlerini bastırıyor, hiçbir şey patlamıyor, sprint yalnız
    "inconclusive" diyor. `-wal`/`-shm` de çivilenir: ana dosya atlanıp yan dosyalar kopyalanırsa
    sandbox'ta yarım bir veritabanı doğar (ve sıcak bir WAL'i `shutil` ile kopyalamak zaten
    tutarlı bir anlık görüntü değildir)."""
    for name in (storage.DB_NAME, storage.DB_NAME + "-wal", storage.DB_NAME + "-shm"):
        assert name in sprint.SKIP_COPY, \
            (f"{name} kum havuzuna kopyalanıyor — çocukta `storage.active()` True döner ve "
             f"`_reset_sandbox_state`in ham dosya sıfırlaması store katmanına görünmez olur")


@pytest.fixture
def db_kum_havuzu(sandbox_state):
    """sandbox_state + bağlantı temizliği. `storage._CONNS` YOL-anahtarlıdır ve süreç ömrü boyunca
    açık kalır; tanıtıcıyı bırakmak uzun suite'te fd sızdırır (test_storage_v142 deseni)."""
    yield sandbox_state
    storage.close_connections()


def test_sr1d_kum_havuzu_dbsiz_dogar_ve_sifirlama_store_katmanina_gorunur(db_kum_havuzu, monkeypatch):
    """DAYANIKLI ÇİVİ: sıfırlama STORE KATMANINDAN doğrulanır, dosyadan değil — arka-uçtan bağımsız.

    SR1b bu vakayı YAKALAYAMADI ve sebebi tam olarak buydu: `(sb/"trades.jsonl").read_text() == ""`
    diye DOSYAYA bakıyor, yani üretimin okuduğu yüzeye değil. Depolama arka-ucu değişince (WP-H/H9)
    iddia doğru kaldı ama ANLAMINI kaybetti: dosya boş, defter dolu. Buradaki iddialar `store` ile
    ölçülür, dolayısıyla yarın üçüncü bir arka-uç gelse bile "kum havuzu SIFIR bir defterle doğar"
    cümlesi ölçülmeye devam eder.

    Kurgu üretimin ölçülmüş hâlidir: canlıda migre bir DB var, portföyün `last_date`i eval
    penceresinin İLERİSİNDE (canlıda 2026-07-31 idi; burada 2099 — monotonluk bekçisi için aynı
    şey) ve defterdeki tek işlem strategy_version≠1 (canlıda 95 işlemin hepsi v4 → `_count(1)=0`)."""
    storage.ensure_schema()                    # DB'yi yaratma yetkisi olan TEK yol
    store.write_json("portfolio.json", {
        "cash": 94457.91, "realized_pnl": -5542.09, "last_id": 95, "positions": {}, "armed": [],
        "pending_exits": {}, "last_date": "2099-01-01", "day_start_equity": 94457.91})
    store.append_jsonl("trades.jsonl", {"id": "T00001", "ticker": "AAPL", "side": "long",
                                        "strategy_version": 4, "r_multiple": 1.5})
    # KURULUM ÇİPASI: bu satır düşerse test ölçmek İSTEDİĞİ yolu ölçmüyordur (DB devrede değil) ve
    # aşağıdaki yeşil, izolasyondan değil kurulum hatasından gelirdi.
    assert store.db_backed("portfolio.json") and store.read_json("portfolio.json")["last_date"] == "2099-01-01"
    # WAL kontrol noktası: son bağlantı kapanınca veri ANA dosyaya iner. Kopyalanan şeyin gerçekten
    # canlı defter olması gerekir — yoksa "kopya zararsızdı" sonucu ölçümden değil zamanlamadan gelir.
    storage.close_connections()

    sbstate = sprint._kur_kum_havuzu("20990101-000000") / "state"
    monkeypatch.setattr(config, "STATE", sbstate)      # artık ÇOCUĞUN gördüğü state buradır
    assert store.read_json("portfolio.json", {})["last_date"] is None, \
        ("çocuk canlının portföyünü okuyor — `loop.daily_cycle` monotonluk bekçisi eval "
         "penceresindeki HER seansı `regressive_session_refused` ile reddeder (n_v1=0)")
    assert store.read_jsonl("trades.jsonl") == [], \
        "kum havuzu canlının işlemleriyle doğdu — v1 sayımı ve taban ölçümü kirlenir"
    assert not (sbstate / "meridian.db").exists(), \
        "kum havuzu DEPOLAMA ARTEFAKTIYLA doğdu — mekanizma budur, iki iddianın da kökü"


# ---------- SR2: pencereler sabit ----------
def test_sr2_windows_are_hardcoded_not_tunable():
    assert sprint.CUTOFF < sprint.EVAL_START, "seçim ve ölçüm pencereleri AYRIK olmalı"
    for token in ("CUTOFF", "EVAL_START"):
        line = next(l for l in SRC.splitlines() if l.startswith(f"{token} ="))
        assert "environ" not in line and "cfg" not in line, f"{token} dışarıdan ayarlanabilir → p-hacking"


def test_sr2b_select_windows_end_at_the_cutoff():
    assert sprint.SELECT_WINDOWS[2] == sprint.CUTOFF and sprint.SELECT_WINDOWS[3] == sprint.CUTOFF


# ---------- SR3: eğitim sonucu canlıya karışmaz ----------
def test_sr3_live_calibration_never_reads_sprint_artifacts():
    from meridian import analytics, probgate, selfreview
    for mod in (analytics, probgate, selfreview):
        src = inspect.getsource(mod)
        assert "sprint_status" not in src and "state/sprint" not in src, \
            f"{mod.__name__} sprint çıktısını canlı kalibrasyona karıştırıyor"


def test_sr3b_status_is_labeled_a_read_model():
    assert "read-model" in SRC and "NOT a learning ledger" in SRC


# ---------- süreç yaşam döngüsü ----------
def test_zombie_child_is_reaped_not_reported_active(sandbox_state, monkeypatch):
    """audit #22: biten çocuk 'active' okunuyordu ve start() sonsuza dek 'already_running' diyordu."""
    store.write_json(sprint.STATUS_FILE, {"pid": 999999, "sid": "x"})
    assert sprint.status()["active"] is False


def test_prune_keeps_the_newest_sandboxes(sandbox_state):
    root = config.STATE / "sprint"
    root.mkdir(parents=True, exist_ok=True)
    for name in ("2026-07-01", "2026-07-02", "2026-07-03", "2026-07-04", "2026-07-05"):
        (root / name).mkdir()
    sprint._prune_old_sandboxes(keep=3)
    left = sorted(d.name for d in root.iterdir())
    assert left == ["2026-07-03", "2026-07-04", "2026-07-05"]


def test_sprint_run_measures_on_the_eval_window_only():
    from meridian import sprint_run
    src = inspect.getsource(sprint_run)
    assert "EVAL_START" in src or "eval_start" in src
    assert "CUTOFF" in src or "cutoff" in src
