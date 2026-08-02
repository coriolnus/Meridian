"""sprint.py — the 'öğrenme antrenmanı' (learning sprint) CONTROL SURFACE.

TETİK: OTOMATİK KADANS + operatör override (2026-07-30, operatör mandası "elle tetik beklemeden tam
fonksiyonlu"). Başlığı 2026-07-30 öncesinde "Operator-triggered" diyordu ve bu ÖLÇÜLEBİLİR bir kusur
üretiyordu: son sprint 2026-07-22'de koştu, sekiz gün önce, çünkü kimse düğmeye basmadı — döngüyü
DAKİKALARDA kapatabilen tek mekanizma, operatörün hafızasına asılıydı. Kadans `maybe_start()`tedir;
pano/CLI düğmesi (`start()`) OVERRIDE olarak aynen durur ve hiçbir kapıya uğramaz.

Why it exists: the live loop is trade-starved — a shipped v2 would take ~1.5 years of live paper to accrue
min_sample trades, so the reflect→outcome loop never closes. The sprint closes it in MINUTES on historical
FORWARD data, honestly:

  * It runs in a SEPARATE OS SUBPROCESS with its own MERIDIAN_ROOT (a sandbox under state/sprint/<id>).
    The live paper book, ledgers, scoreboard, and the running scheduler/Hermes are NEVER touched — there is
    no rewind and nothing to restore.
  * Selection and measurement use DISJOINT calendar windows: the coordinate-descent search selects a v2
    through the UNCHANGED OOS gate on data ≤ CUTOFF; the realized_delta is then measured ONLY on trades from
    the strictly-later eval window. No look-ahead leakage.
  * v1 and v2 are each walked forward over the SAME eval window from an identically-reset FLAT book, so the
    market regime is common-mode and cancels — the delta reflects the parameter change, not a regime gap.
  * The result is a clearly-labeled TRAINING calibration point. It is NEVER merged into live calibration(),
    the real-money autonomy ladder, or the live proposer. To close the LIVE loop for real, the discovered
    candidate must still clear the PRODUCTION gate and accrue production trades — the sprint de-risks
    discovery, it never bypasses the law.
"""
from __future__ import annotations
import datetime as dt
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

from . import config, store

SANDBOX_KEEP = 3   # retain the newest N sprint sandboxes; older ones are pruned on the next start (L5)

# FIXED windows — deliberately NOT operator-tunable (a movable cutoff would be p-hacking). Disjoint by
# construction: select on data ≤ CUTOFF, measure on trades ≥ EVAL_START. Eval spans ~2y so v1 and v2 each
# clear min_sample (~30) trades and the same-window baseline is real, not a scoreboard fallback.
CUTOFF = "2024-06-30"
SELECT_WINDOWS = ("2022-01-01", "2023-01-01", "2024-06-30", "2024-06-30",
                  ["2023-01-01", "2023-07-01", "2024-01-01", "2024-06-30"], 10)
EVAL_START = "2024-07-01"
STATUS_FILE = "sprint_status.json"    # written LIVE — a labeled read-model, NOT a learning ledger
# bars symlinked; sprint subtree excluded; keys not needed; HALT must NEVER enter the sandbox — the
# operator halting LIVE trading is the natural moment to run an offline sprint, but a copied kill-switch
# makes every sandbox session suppress entries → n_v1=0 and a uselessly "inconclusive" sprint (audit #23).
# SEANS-İÇİ ARŞİVLER DE ATLANIR (2026-08-02 A1 ölçümü). state/bars_intraday 43M + state/intraday_bars 40M
# = 83M, yani bir kum havuzunun ~110M'inin dörtte üçü (state/sprint 438M = 4 × ~110M). Bu iki dizin bu
# küme yazıldıktan SONRA doğdu — SKIP_COPY yalnız "bars"ı atlıyordu, yeni gelenler sessizce kopyalanır
# oldu. YAZAR TEKLİĞİ arşivci tarafında: bars_intraday'i barsarchive.py, intraday_bars'ı bararchive.py
# yazar (meridian-barsarchive birimi); SPRINT ÇOCUĞUNUN YOLUNDA OKUYUCULARI YOK, kopya yalnız disk
# yakıyordu. Dizin yokluğu taze-kurulum hâline eşdeğerdir: okuyucular yokluğu sahte bir "yolunda" ile
# değil BEYANLA karşılıyor (barsarchive.py:748 — "arşivi YOK ... henüz hiç tur koşmadı").
# DEPOLAMA ARTEFAKTI DA ATLANIR — SINIFI BOYUT DEĞİL İZOLASYON (2026-08-02 ölçümü). WP-H/H9'dan
# (07-31) beri altı defter, `state/meridian.db` VARSA SQLite'tan okunur (`store.db_backed` →
# `storage.active`; yol her çağrıda `config.STATE`ten türer). DB kum havuzuna kopyalanınca
# `_reset_sandbox_state`in HAM DOSYA yazımları çocuğun store okumalarına GÖRÜNMEZ olur: çocuk
# canlının `portfolio.json`unu DB kopyasından okur, `last_date="2026-07-31"` görür ve
# `loop.daily_cycle` monotonluk bekçisi (loop.py:719) eval penceresindeki HER tarihsel seansı
# `regressive_session_refused` ile reddeder. ÖLÇÜM (A1, salt-okuma): son kum havuzunda 522/522 seans
# reddedildi, DB'deki 95 işlemin hepsi strategy_version=4 olduğu için `_count(1)=0`, ve 07-31'den
# beri 154 kadans koşusunun TAMAMI ~60 sn'de `phase=done, n_v1=0` ile bitti — yani mekanizma
# migrasyondan bu yana hiç kalibrasyon noktası üretemedi. Kum havuzu DB'SİZ DOĞUNCA çocukta
# `storage.active()` False döner ve dosya-tabanlı davranışa, yani migrasyon ÖNCESİ ÖLÇÜLMÜŞ-İYİ yola
# (07-22 sprinti: n_v1=100) dönülür. İKİNCİ KAZANÇ AYNI SATIRDA: canlı worker yazarken SICAK bir WAL
# veritabanını `shutil` ile kopyalamak tutarlı bir anlık görüntü DEĞİLDİR (ana dosya ile -wal/-shm
# ayrı anlarda okunur) — o risk de kapanır. Sınıf: audit #23'ün (kopyalanan HALT tüm sandbox
# girişlerini bastırır) ikinci kuşağı, artı "SKIP_COPY denylist'i state'e yeni gelen artefaktları
# sessizce kaçırır" (hemen üstteki bars_intraday vakasıyla aynı tur).
SKIP_COPY = {"bars", "bars_intraday", "intraday_bars", "sprint", "secrets.json", "HALT",
             "meridian.db", "meridian.db-wal", "meridian.db-shm"}


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def status() -> dict:
    st = store.read_json(STATUS_FILE, {})
    pid, alive = st.get("pid"), False
    if pid:
        try:
            # Reap first: os.kill(pid, 0) SUCCEEDS on a zombie, so a finished child read as 'active'
            # forever and start() refused with 'already_running' for the life of the server (audit #22).
            # WNOHANG waitpid clears the zombie (harmless ChildProcessError if it wasn't our child).
            try:
                os.waitpid(int(pid), os.WNOHANG)
            except (ChildProcessError, OSError, ValueError):  # sessiz-yutma: yardımcı/telemetri yolu; başarısızlığı karara girmez ve çağıran yedek değerle aynen devam eder
                pass
            os.kill(int(pid), 0)
            alive = True
        except (OSError, ValueError):  # sessiz-yutma: yardımcı/telemetri yolu; başarısızlığı karara girmez ve çağıran yedek değerle aynen devam eder
            alive = False
    # YASA 6 (2026-07-21): sprint_run.py her aramadan sonra `sprint_runs.jsonl`'a satır yazıyordu ve
    # KOD İÇİNDE HİÇBİR OKUYUCUSU YOKTU — üretildi, kimse tüketmedi; yedi desenli bütünlük raporunun
    # panoya hiç bağlanmamasıyla aynı kusur. Son koşular buradan durumun içine girer (pano zaten
    # sprint.status()'u render ediyor), böylece defterin bir tüketicisi olur.
    # TERS ORPHAN GÖRÜNÜR OLUR (K1, 2026-07-30): yukarıdaki YASA-6 düzeltmesi okuyucuyu kurdu ama
    # defter DİSKTE HİÇ YOK — `read_jsonl` her zaman [] döndürüyor ve pano "son koşu yok" çiziyor.
    # 2026-07-22 sprinti aramayı TAMAMLADI (sprint_status.json: search.evaluated=8, phase=done) ve
    # satır yine yok: defter ya hiç doğmadı ya 07-23 depo taşımasında kayboldu. Hiçbir dedektör bu
    # yönü sormuyor — orphan taraması yalnız VAR OLAN dosyaları sorgular, "okuyucusu var ama dosyası
    # yok"u değil. `runs_ledger` o ayrımı taşır: "henüz satır yok" ile "defter hiç yok" AYRI hükümler.
    # TERS ORPHAN'IN KÖK NEDENİ BULUNDU (2026-07-30). Yukarıdaki not "defter ya hiç doğmadı ya
    # taşımada kayboldu" diyordu — İKİSİ DE DEĞİL. Defter HER SPRINTTE doğuyor, yalnız BAŞKA BİR
    # YERE: `sprint_run` çocuk süreçtir ve `MERIDIAN_ROOT=<sbroot>` ile koşar, yani onun
    # `store.append_jsonl("sprint_runs.jsonl", …)` çağrısı KUM HAVUZUNUN state'ine yazar. Ölçüm:
    #     state/sprint/20260714-210605/state/sprint_runs.jsonl   921 B
    #     state/sprint/20260719-164050/state/sprint_runs.jsonl   921 B
    #     state/sprint/20260722-093305/state/sprint_runs.jsonl   443 B
    # Üçü de yerinde. Canlı yol boştu çünkü oraya YAZAN yok — okuyucu yanlış rafa bakıyordu.
    # ÇÖZÜM BURADA, YAZARDA DEĞİL: çocuğun canlı state'e yazması izolasyonu delerdi (kum havuzunun
    # bütün varlık sebebi "canlıya dokunmaması"). Okuyucu kum havuzlarını gezer; `sbroot` damgası
    # zaten durumun içinde ve saklanan sandbox sayısı sınırlı (SANDBOX_KEEP), yani tarama ucuz.
    _runs, _kaynak = _sandbox_runs(limit=5)
    if not _runs:
        _canli = store.read_jsonl("sprint_runs.jsonl", limit=5)
        if _canli:
            _runs, _kaynak = _canli, "canli"
    return {**st, "active": alive, "runs": _runs,
            "runs_ledger": ("var" if _runs else "YOK"), "runs_kaynak": _kaynak,
            "runs_note": (None if _runs else
                          "hiçbir kum havuzunda sprint_runs.jsonl yok — sprint arama fazına hiç "
                          "ulaşmamış olabilir (Faz A min_sample'a takılıyorsa satır yazılmaz)")}


def _sandbox_runs(limit: int = 5) -> tuple[list, str | None]:
    """Kum havuzlarındaki `sprint_runs.jsonl` satırları, en yeniden eskiye. Dizin adları zaman
    damgasıdır (bkz. `_prune_old_sandboxes`), o yüzden sıralama kronolojiktir."""
    root = config.STATE / "sprint"
    if not root.exists():
        return [], None
    out: list = []
    try:
        dirs = sorted((d for d in root.iterdir() if d.is_dir()), key=lambda d: d.name, reverse=True)
    except OSError as e:
        from . import obs
        obs.warn("sprint_sandbox_scan_failed", error=f"{type(e).__name__}: {e}",
                 detail="kum havuzu defterleri taranamadı — 'son koşu yok' YANLIŞ olabilir")
        return [], None
    for d in dirs:
        f = d / "state" / "sprint_runs.jsonl"
        try:
            satirlar = [json.loads(x) for x in f.read_text().splitlines() if x.strip()]
        except (OSError, ValueError):  # sessiz-yutma: sonuç KAYDA GEÇİYOR (o sandbox atlanır, kalanlar taranır) — eksik/bozuk bir defter diğerlerini gizlemez
            continue
        for r in reversed(satirlar):
            out.append({**r, "sandbox": d.name})
            if len(out) >= limit:
                return out, "kum_havuzu"
    return out, ("kum_havuzu" if out else None)


def _reset_sandbox_state(sbstate: Path) -> None:
    """Blank the sandbox ledgers so the sprint measures ITS OWN forward trades, starting from a fresh v1
    with parent=None (exactly the live starting condition, minus the accumulated history).

    KISIT (2026-08-02): buradaki HAM YOL yazımları yalnız kum havuzu DEPOLAMA ARTEFAKTISIZ (yani
    `meridian.db`siz) doğduğu için store-görünür bir gerçektir — `state/`e yeni bir depolama
    artefaktı gelirse SKIP_COPY'ye girmek ZORUNDADIR, aksi halde bu sıfırlama sessizce hiçbir şeyi
    sıfırlamaz (gerekçe ve ölçüm SKIP_COPY'nin üstünde)."""
    from .score import START_EQUITY
    (sbstate / "trades.jsonl").write_text("")
    (sbstate / "hypotheses.jsonl").write_text("")
    (sbstate / "scoreboard.json").write_text(json.dumps({"versions": {}}))
    (sbstate / "portfolio.json").write_text(json.dumps({
        "cash": START_EQUITY, "realized_pnl": 0.0, "last_id": 0, "positions": {},
        "armed": [], "pending_exits": {}, "last_date": None, "day_start_equity": START_EQUITY}))
    (sbstate / "strategy.yaml").write_text(yaml.safe_dump(config.default_strategy(), sort_keys=False))
    hist = sbstate / "history"
    if hist.exists():
        shutil.rmtree(hist)
    hist.mkdir(exist_ok=True)
    # SNAPSHOT the v1 seed into the sandbox history (M4). run.bootstrap_v01 does this in production; the
    # sandbox reset skipped it, so after Phase B shipped v2 (parent=1) a forward-LOSING v2 routed into
    # rollback.revert_to(1) → FileNotFoundError (swallowed by daily_cycle): the negative calibration point
    # was never written and the sprint could only ever close on WINNERS (a systematic training bias). Write
    # v0001.yaml directly (config.HISTORY here points at LIVE, not the sandbox, so we can't use snapshot()).
    config.dump_yaml(config.default_strategy(), hist / "v0001.yaml")


def _prune_old_sandboxes(keep: int = SANDBOX_KEEP) -> None:
    """Retain only the newest `keep` sprint sandboxes (L5). Each start() copies the live state tree into a
    new dated dir (bars are symlinked) and nothing ever deleted them — an operator-paced disk leak.
    Never deletes the currently-active sandbox.

    BOYUT İDDİASI TAZELENDİ (2026-08-02). Bu docstring "~1.5 MB" diyordu: YAZILDIĞI GÜN DOĞRUYDU,
    sonra canlı state büyüdü ve iddia bayatladı. A1'de ölçüm: state/ 617M, state/sprint 438M =
    4 kum havuzu × ~110M. SKIP_COPY'ye bars_intraday+intraday_bars (43M+40M = 83M) eklendikten sonra
    kum havuzu başına ARİTMETİK BEKLENTİ ~27M'dir (110−83). BU BİR TÜRETİM, ÖLÇÜM DEĞİL — yeni bir
    sandbox doğduğunda `du -sh state/sprint/*` ile doğrulanmadan "ölçüldü" diye anılmaz.
    Birikme sınırsız DEĞİL: SANDBOX_KEEP=3 + her start()'ta budama çalışıyor (2026-08-02 A1'de
    doğrulandı), kararlı durum 4 dizin = 3 saklanan + 1 yeni."""
    root = config.STATE / "sprint"
    if not root.exists():
        return
    active = status()
    active_sb = str(Path(active["sbroot"]).resolve()) if active.get("active") and active.get("sbroot") else None
    dirs = sorted([d for d in root.iterdir() if d.is_dir()], key=lambda d: d.name)   # names are timestamps
    for d in dirs[:-keep] if len(dirs) > keep else []:
        if active_sb and str(d.resolve()) == active_sb:
            continue
        try:
            shutil.rmtree(d)
        except OSError:  # sessiz-yutma: en iyi çaba temizlik/kilit bırakma; hedef zaten yoksa yapacak bir şey yok ve asıl iş yolu bundan ötürü durduramaz
            pass


def _kur_kum_havuzu(sid: str) -> Path:
    """Kum havuzunu kur ve KÖKÜNÜ döndür: kopya → bars bağı → skills bağı → defter sıfırlama.

    `start()`TEN AYRI BİR FONKSİYON OLMASININ SEBEBİ ÖLÇÜLEBİLİRLİKTİR (2026-08-02): izolasyon
    sözleşmesini sınayan test YASANIN KENDİSİNİ çağırabilmelidir. Sırayı (kopya, bağlar, sıfırlama)
    teste yeniden yazmak bu depoda tekrar tekrar yaşanan "aynı yasanın iki uygulaması" hatasıdır —
    testteki kopya yeşil kalırken üretim yolu sessizce ayrışır ve dedektör hiçbir şey ölçmez.
    Fonksiyon SAFtır: yalnız diski kurar, süreç doğurmaz, durum dosyası yazmaz."""
    # SBROOT KANONİK YOLA DAMGALANIR (K1, 2026-07-30). `state/sprint_status.json` hâlâ
    # `/Users/erdemozturk/Documents/Claude/AI-Trading/...` yolunu taşıyor — 2026-07-22 sprintinden
    # kalma bir damga, ve o yol 07-23 taşımasından beri gerçek depoya SYMLINK. Sembolik yolu
    # damgalamak iki sorun doğurur: (1) damga, aynı dizini gösteren iki farklı dizgeyle kaydedilir
    # ve karşılaştıran her kod ("bu sandbox aktif mi?" — status():107 `Path(...).resolve()` ile
    # kıyaslıyor) ayrışma riski taşır, (2) symlink bir gün kaldırılırsa kayıt ARTIK var olmayan bir
    # yolu gösterir ve sprint'in nerede koştuğu geriye dönük olarak bilinemez.
    # `.resolve()` damgayı gerçek yola sabitler; okuyucu tarafı zaten resolve ediyordu.
    sbroot = (config.STATE / "sprint" / sid).resolve()
    sbstate = sbroot / "state"
    sbstate.mkdir(parents=True, exist_ok=True)
    live = config.STATE
    # copy live state into the sandbox EXCEPT the big/irrelevant/secret items
    for item in live.iterdir():
        if item.name in SKIP_COPY:
            continue
        dest = sbstate / item.name
        if item.is_dir():
            shutil.copytree(item, dest, dirs_exist_ok=True)
        else:
            shutil.copy2(item, dest)
    # symlink bars -> live cache (reuse; never refetch)
    barlink = sbstate / "bars"
    try:
        if not barlink.exists():
            barlink.symlink_to((live / "bars").resolve(), target_is_directory=True)
    except (OSError, NotImplementedError):  # sessiz-yutma: yardımcı G/Ç yolu; çağıran yokluğu zaten yedek değerle karşılıyor ve asıl okuma hatası store katmanında bir kez uyarılıyor
        shutil.copytree(live / "bars", barlink, dirs_exist_ok=True)
    # symlink skills -> live registry (config.SKILLS = ROOT/skills, a sibling of state/) so the child's
    # skills.reconcile_enablement reads the real catalog
    sklink = sbroot / "skills"
    try:
        if config.SKILLS.exists() and not sklink.exists():
            sklink.symlink_to(config.SKILLS.resolve(), target_is_directory=True)
    except (OSError, NotImplementedError):  # sessiz-yutma: yardımcı G/Ç yolu; çağıran yokluğu zaten yedek değerle karşılıyor ve asıl okuma hatası store katmanında bir kez uyarılıyor
        pass
    _reset_sandbox_state(sbstate)
    return sbroot


def start(cfg: dict | None = None) -> dict:
    cfg = cfg or {}
    if status().get("active"):
        return {"status": "already_running", **status()}
    _prune_old_sandboxes()
    sid = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    sbroot = _kur_kum_havuzu(sid)
    live = config.STATE
    conf = {"k_max": int(cfg.get("k_max", 3)), "budget": int(cfg.get("budget", 12))}
    env = {**os.environ, "MERIDIAN_ROOT": str(sbroot), "MERIDIAN_BROKER": "internal",
           "MERIDIAN_SPRINT_STATUS": str((live / STATUS_FILE).resolve())}
    proc = subprocess.Popen(
        [sys.executable, "-m", "meridian.sprint_run", str(sbroot), json.dumps(conf)],
        env=env, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
        start_new_session=True)
    # HİPOTEZ SAYACI BAŞLANGIÇTA DAMGALANIR: otomatik kadansın ikinci tetiği ("son sprintten beri
    # taze aday birikti mi") ancak bir TABAN varsa ölçülebilir. Damga olmadan `taze = len(hyps) − 0`
    # olurdu ve tetik her gece yanardı — haftalık disiplin sessizce kaybolurdu.
    # DAMGAYI ÇOCUK SÜREÇ SİLİYORDU (C15, 2026-08-02). Yukarıdaki `Popen` çocuğa
    # `MERIDIAN_SPRINT_STATUS` ile BU dosyayı verir ve `sprint_run._write_live_status` onu
    # birleştirmeden eziyordu: aşağıdaki damga İLK ilerleme yazımında yok oluyor, `should_run`
    # tabanı 0 sayıp her gece tetikliyordu. Koruma çocuk tarafında (`sprint_run._damgayi_koru`) —
    # yazımın kendi katmanında, çünkü `stop()` ve çocuğun hata yolu da aynı dosyaya yazar.
    try:
        from . import memory
        n_hyp = len(memory.all_hypotheses())
    except Exception as e:
        from . import obs
        obs.warn("sprint_hyp_baseline_failed", error=f"{type(e).__name__}: {e}",
                 detail="taze-aday tetiği tabanı yazılamadı — kadans haftalık tabana düşer")
        n_hyp = None
    st = {"pid": proc.pid, "sid": sid, "phase": "starting", "started_at": _now(),
          "cfg": conf, "sbroot": str(sbroot), "eval_start": EVAL_START, "cutoff": CUTOFF,
          "n_hyp_at_start": n_hyp}
    store.write_json(STATUS_FILE, st)
    return {"started": True, **st}


# ==================================================================================================
# OTOMATİK KADANS (2026-07-30) — TETİK, EŞZAMANLILIK BEKÇİSİ, BÜTÇE ÖZ-AYARI
# ==================================================================================================
# NEDEN OTOMATİK. Canlı ölçüm: `sprint_status.json` son koşuyu 2026-07-22'de gösteriyor (phase=done,
# n_v1=100, shipped=false) ve `sprint_runs.jsonl` diskte HİÇ YOK. Yani sekiz gündür koşmadı ve
# koşmamasının hiçbir sebebi yoktu — "operator-triggered" bir mekanizmanın kadansı, operatörün
# hatırlamasıdır. `learning_scorecard.outcomes_measured=1` tam da bunun sonucu: kalibrasyon noktası
# üreten TEK hızlı yol atıl duruyordu.
#
# EŞZAMANLILIK — ÜÇ KAPI, ÜÇÜ DE AYRI BİR ARIZAYI ÖNLER:
#   (1) `sprint.status().active`  — iki sprint aynı anda 8 çekirdeği ikiye böler ve ikisi de yavaşlar.
#   (2) ARAMA KOŞUYOR MU (`hermes.SEARCH_PROGRESS`) — canlı arama da `ProcessPoolExecutor` açar
#       (reflect.py:1049, workers = max(2, min(4, çekirdek−2))). İkisi birlikte makineyi doyurur ve
#       ASIL bedeli zamanlayıcının 300 sn'lik poll'üdür: nabız bayatlar, /healthz 503'ler.
#   (3) ÇAĞIRANIN MEŞGULİYET SİNYALİ (`mesgul` argümanı) — zamanlayıcı EOD döngüsünü koşturmak
#       üzereyse sprint başlamaz. Bu kapı ÇAĞIRANDAN gelir çünkü "daily_cycle birazdan koşacak"
#       bilgisi yalnız orada vardır; bir dosyadan okunamaz.
#
# SAAT DİLİMİ. Sprint 4 işçiyle walk-forward koşturur — seans içinde başlatmak, canlı kararların
# koştuğu makineyi doyurmaktır. Pencere YEREL saattir (makinenin bulunduğu yer = operatörün gecesi).
SPRINT_HOURS = (22, 6)          # [22:00, 06:00) yerel — gece dilimi
SPRINT_STALE_DAYS = 7           # haftalık taban tetik
SPRINT_MIN_NEW_HYP = 5          # VEYA: son sprintten beri bu kadar taze hipotez birikti
# BÜTÇE ÖZ-AYARI — ÇEKİRDEK SAYISINDAN TÜRER, KOTADAN DEĞİL. Sprint LLM ÇAĞIRMAZ: `sprint_run`
# yalnız `reflect.search_and_submit` koşturur (deterministik koordinat inişi). Ajan kotasını bu
# yüzden bütçeye BAĞLAMADIM — bağlasaydım ölçülmeyen bir ilişki uydurmuş olurdum. Kota yine de
# ROL oynar ama TERS yönde ve yalnız değer olarak: beyin zinciri soğumadayken hipotez üreten tek
# mekanizma deterministik aramadır, yani sprint o gece DAHA değerlidir — bu bir kapı değil, bir not.
#
# İŞÇİ FORMÜLÜ REFLECT'İN KENDİSİNDEN ALINIR, YENİDEN YAZILMAZ: ikinci bir tanım, reflect'in formülü
# değiştiği gün sprint'in yanlış bir çekirdek varsayımıyla bütçe kurması demekti (bu depoda tekrar
# tekrar yaşanan "aynı yasanın iki uygulaması" hatası).
BUDGET_PER_WORKER = 3           # işçi başına sonda; 4 işçili makinede 12 = BUGÜNKÜ varsayılan
BUDGET_MIN, BUDGET_MAX = 6, 24
KMAX_MIN, KMAX_MAX = 2, 4


def _workers() -> int:
    """`reflect`in kendi paralellik formülü — burada YENİDEN TANIMLANMAZ, kopyalanır ve nedeni
    yazılır. (İçe aktarıp okumak mümkün değil: formül bir fonksiyonun gövdesinde yerel bir ifade.)"""
    return max(2, min(4, (os.cpu_count() or 4) - 2))


def auto_config() -> dict:
    """`start(cfg)`in budget/k_max'ini MAKİNEDEN türet. Env override edilmişse ona DOKUNMA.

    ÇİPA DÜRÜSTLÜĞÜ: bu makinede (8 çekirdek → 4 işçi) formül budget=12, k_max=3 üretir — yani
    BUGÜNKÜ elle yazılmış varsayılanların TA KENDİSİ. Türetim davranışı bu makinede değiştirmez;
    yalnız BAŞKA bir makinede ölçeklenir. Ölçülmüş bir değeri yeniden üretmeyen bir formül,
    türetim değil yeni bir sabit olurdu."""
    w = _workers()
    out = {"cekirdek": os.cpu_count(), "isci": w}

    def _al(var: str, turetilen: int) -> tuple[int, str]:
        """Env override VARSA kazanır; BOZUKSA sessizce yutulmaz (YASA 4) — uyarı düşer ve
        türetime dönülür. Yanlış bir sayıyla koşmak, ölçülmüş bir sayıyla koşmaktan kötüdür."""
        raw = os.environ.get(var)
        if raw is None or raw.strip() == "":
            return turetilen, "turetim"
        try:
            return int(raw), f"env:{var}"
        except ValueError:
            from . import obs
            obs.warn("sprint_env_override_invalid", var=var, value=raw, turetilen=turetilen,
                     detail="env override sayı değil — türetilmiş değer kullanılıyor")
            return turetilen, "turetim(env_bozuk)"

    out["budget"], out["budget_kaynagi"] = _al(
        "MERIDIAN_SPRINT_BUDGET", max(BUDGET_MIN, min(BUDGET_MAX, BUDGET_PER_WORKER * w)))
    out["k_max"], out["k_max_kaynagi"] = _al(
        "MERIDIAN_SPRINT_KMAX", max(KMAX_MIN, min(KMAX_MAX, 1 + w // 2)))
    out["formul"] = (f"isci = max(2, min(4, cekirdek−2)) = {w}; "
                     f"budget = clamp({BUDGET_PER_WORKER}×{w}, {BUDGET_MIN}, {BUDGET_MAX}); "
                     f"k_max = clamp(1 + {w}//2, {KMAX_MIN}, {KMAX_MAX})")
    return out


def _search_busy() -> bool:
    """Canlı koordinat-inişi araması şu an koşuyor mu? Aynı süreçteki `hermes.SEARCH_PROGRESS`ten
    okunur (zamanlayıcı ve api AYNI süreçtedir — daemon thread). Okunamıyorsa MEŞGUL SAYILIR:
    muhafazakâr taraf, "emin değilsen 8 çekirdeği ikiye bölme"dir."""
    try:
        from . import hermes
        return bool((hermes.SEARCH_PROGRESS or {}).get("running"))
    except Exception as e:
        from . import obs
        obs.warn("sprint_search_busy_unreadable", error=f"{type(e).__name__}: {e}",
                 detail="arama durumu okunamadı — sprint MEŞGUL sayıp başlamadı (muhafazakâr taraf)")
        return True


def should_run(*, mesgul: str | None = None, now: dt.datetime | None = None) -> dict:
    """Kadans bu an sprint başlatmalı mı? DÖNÜŞ her zaman bir SEBEP taşır — `False` tek başına
    "arıza mı, disiplin mi" sorusunu cevaplamaz ve tam olarak o belirsizlik bu turda kapatılıyor."""
    from . import memory
    st = status()
    now = now or dt.datetime.now()
    hyps = memory.all_hypotheses()
    son = st.get("started_at")
    try:
        gun = (dt.datetime.now(dt.timezone.utc) - dt.datetime.fromisoformat(str(son))).days
    except (TypeError, ValueError):  # sessiz-yutma: sonuç KAYDA GEÇİYOR (gun=None → "hiç koşmadı" tetiği) — bilgi kaybolmaz
        gun = None
    taze = len(hyps) - int(st.get("n_hyp_at_start") or 0)
    ctx = {"gecen_gun": gun, "taze_hipotez": taze, "n_hipotez": len(hyps),
           "saat": now.hour, "pencere": list(SPRINT_HOURS), "cfg": auto_config()}
    if st.get("active"):
        return {**ctx, "kos": False, "sebep": "zaten_kosuyor"}
    if mesgul:
        return {**ctx, "kos": False, "sebep": f"mesgul:{mesgul}"}
    if _search_busy():
        return {**ctx, "kos": False, "sebep": "mesgul:canli_arama"}
    lo, hi = SPRINT_HOURS
    # Pencere gece yarısını AŞAR (22→06): tek bir `lo <= h < hi` karşılaştırması burada HER ZAMAN
    # False verirdi ve kadans hiç koşmazdı — sessizce.
    if not (now.hour >= lo or now.hour < hi):
        return {**ctx, "kos": False, "sebep": "saat_dilimi_disinda"}
    # TETİK: haftalık taban VEYA taze aday birikimi. "Hiç koşmadı" (gun=None) da tetiktir.
    if gun is not None and gun < SPRINT_STALE_DAYS and taze < SPRINT_MIN_NEW_HYP:
        return {**ctx, "kos": False,
                "sebep": f"tetik_yok(gun={gun}<{SPRINT_STALE_DAYS}, taze={taze}<{SPRINT_MIN_NEW_HYP})"}
    return {**ctx, "kos": True,
            "sebep": ("hic_kosmadi" if gun is None
                      else "haftalik_taban" if gun >= SPRINT_STALE_DAYS else "taze_aday_birikimi")}


def maybe_start(*, mesgul: str | None = None) -> dict:
    """OTOMATİK TETİK. Koşullar oluşmuşsa `start(auto_config())`; oluşmamışsa NEDENİ döner.

    Kapılardan geçemeyen bir tur SESSİZ DEĞİLDİR ama ALARM da değildir: karar defterine `info`
    düşer, çünkü "gece değil" ile "sprint çöktü" aynı seviyede raporlanırsa ikincisi kaybolur."""
    from . import obs
    karar = should_run(mesgul=mesgul)
    if not karar["kos"]:
        obs.log("sprint_cadence_skip", sebep=karar["sebep"], gecen_gun=karar["gecen_gun"],
                taze_hipotez=karar["taze_hipotez"])
        return {"started": False, **karar}
    cfg = karar["cfg"]
    res = start({"budget": cfg["budget"], "k_max": cfg["k_max"]})
    obs.log("sprint_cadence_start", sebep=karar["sebep"], budget=cfg["budget"], k_max=cfg["k_max"],
            formul=cfg["formul"], sid=res.get("sid"),
            detail="öğrenme antrenmanı OTOMATİK başladı — kum havuzu, canlı defter dokunulmaz")
    try:
        from . import watchdog
        watchdog.beat("sprint_cadence")
    except Exception as e:
        obs.warn("sprint_beat_failed", error=f"{type(e).__name__}: {e}")
    return {**res, **{k: karar[k] for k in ("sebep", "gecen_gun", "taze_hipotez")}}


def stop() -> dict:
    st = store.read_json(STATUS_FILE, {})
    sbroot = st.get("sbroot")
    if sbroot:
        try:
            (Path(sbroot) / "state" / "STOP").write_text("1")   # cooperative flag; child checks each session
        except OSError:  # sessiz-yutma: yardımcı G/Ç yolu; çağıran yokluğu zaten yedek değerle karşılıyor ve asıl okuma hatası store katmanında bir kez uyarılıyor
            pass
    pid = st.get("pid")
    if pid:
        try:
            os.kill(int(pid), 15)
        except (OSError, ValueError):  # sessiz-yutma: yardımcı/telemetri yolu; başarısızlığı karara girmez ve çağıran yedek değerle aynen devam eder
            pass
    store.write_json(STATUS_FILE, {**st, "phase": "stopping", "stopped_at": _now()})
    return {"stopping": True}
