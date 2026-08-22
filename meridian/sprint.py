"""sprint.py — öğrenme sprintinin KONTROL YÜZEYİ: kum havuzu kurulumu, otomatik kadans ve koşum yolu.

NE YAPAR. Canlı döngü işlem-kıtıdır: gemiye alınmış bir v2'nin min_sample işlem biriktirmesi canlı
kâğıt defterde yıllar alır, yani yansıt→sonuç döngüsü hiç kapanmaz. Sprint o döngüyü tarihi İLERİ
veri üzerinde DAKİKALARDA ve dürüstçe kapatır: `start()` canlı state'i `state/sprint/<sid>` altına
kopyalar (`_kur_kum_havuzu`; SKIP_COPY barları/sırları/HALT'ı/SQLite artefaktını dışarıda tutar,
bars + skills symlink'lenir), defterleri düz kitaba sıfırlar ve `sprint_run` çocuğunu KENDİ
MERIDIAN_ROOT'uyla ayrı süreçte doğurur — canlı defter, karne ve koşan zamanlayıcıya dokunulmaz.
Koşum yolu önce ayrı systemd birimidir (`meridian-sprint@.service`; worker restart'ı sprinti
öldürmesin diye), kullanılamazsa ADLI sebeple `Popen`a düşülür (`kosum_yolu` damgası).

TETİK: otomatik kadans (`maybe_start`/`should_run`: gece penceresi SPRINT_HOURS, haftalık taban
SPRINT_STALE_DAYS, taze-hipotez tetiği SPRINT_MIN_NEW_HYP, yetim yeniden-başlatma freni
YETIM_YENIDEN_SAAT, meşguliyet kapıları) + hiçbir kapıya uğramayan pano/CLI override'ı `start()`.
Bütçe makineden türetilir (`auto_config`); `status()` yetim/koşu göstergelerini de taşır.

DEĞİŞMEZLER. Seçim ve ölçüm AYRIK takvim pencerelerindedir (aday CUTOFF'a kadar veride, DEĞİŞMEMİŞ
OOS kapısıyla seçilir; realized_delta yalnız EVAL_START sonrası işlemlerde ölçülür — sızıntı yok)
ve pencereler operatör-ayarlı DEĞİLDİR (oynar cutoff = p-hacking). v1 ve v2 AYNI pencereyi AYNI düz
kitaptan yürür: rejim ortak-mod olur, delta parametre değişimini ölçer. Sonuç açıkça "antrenman"
etiketli bir kalibrasyon noktasıdır — canlı calibration()'a, otonomi merdivenine ve canlı önericiye
ASLA karışmaz; üretim kapısı bypass edilmez. `kum_havuzunda()` süreç-dışı paylaşımlı kaynaklara
(ör. ajanın skills dizini) yazmadan önce sorulan izolasyon kapısıdır.

OKUR: canlı `state/` (kopya kaynağı), `hermes.SEARCH_PROGRESS` (meşguliyet), `hypotheses.jsonl`
(taze-aday tabanı), kum havuzlarındaki `sprint_runs.jsonl`. YAZAR: canlı `sprint_status.json`
(etiketli okuma-modeli, öğrenme defteri DEĞİL) ve kum havuzu ağacı (kurulum/budama)."""
from __future__ import annotations
import datetime as dt
import json
import os
import shlex
import shutil
import subprocess
import sys
import time
from pathlib import Path

import yaml

from . import config, store

SANDBOX_KEEP = 3   # retain the newest N sprint sandboxes; older ones are pruned on the next start

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
# makes every sandbox session suppress entries → n_v1=0 and a uselessly "inconclusive" sprint.
# SEANS-İÇİ ARŞİVLER DE ATLANIR (A1 ölçümü). state/bars_intraday 43M + state/intraday_bars 40M
# = 83M, yani bir kum havuzunun ~110M'inin dörtte üçü (state/sprint 438M = 4 × ~110M). Bu iki dizin bu
# küme yazıldıktan SONRA doğdu — SKIP_COPY yalnız "bars"ı atlıyordu, yeni gelenler sessizce kopyalanır
# oldu. YAZAR TEKLİĞİ arşivci tarafında: bars_intraday'i barsarchive.py, intraday_bars'ı bararchive.py
# yazar (meridian-barsarchive birimi); SPRINT ÇOCUĞUNUN YOLUNDA OKUYUCULARI YOK, kopya yalnız disk
# yakıyordu. Dizin yokluğu taze-kurulum hâline eşdeğerdir: okuyucular yokluğu sahte bir "yolunda" ile
# değil BEYANLA karşılıyor (`barsarchive.render_summary` — "arşivi YOK ... henüz hiç tur koşmadı").
# DEPOLAMA ARTEFAKTI DA ATLANIR — SINIFI BOYUT DEĞİL İZOLASYON (ölçüldü). Altı defter, `state/meridian.db` VARSA SQLite'tan okunur (`store.db_backed` →
# `storage.active`; yol her çağrıda `config.STATE`ten türer). DB kum havuzuna kopyalanınca
# `_reset_sandbox_state`in HAM DOSYA yazımları çocuğun store okumalarına GÖRÜNMEZ olur: çocuk
# canlının `portfolio.json`unu DB kopyasından okur, `last_date="2026-07-31"` görür ve
# `loop.daily_cycle` monotonluk bekçisi eval penceresindeki HER tarihsel seansı
# `regressive_session_refused` ile reddeder. ÖLÇÜM (A1, salt-okuma): son kum havuzunda 522/522 seans
# reddedildi, DB'deki 95 işlemin hepsi strategy_version=4 olduğu için `_count(1)=0`, ve 07-31'den
# beri 154 kadans koşusunun TAMAMI ~60 sn'de `phase=done, n_v1=0` ile bitti — yani mekanizma
# migrasyondan bu yana hiç kalibrasyon noktası üretemedi. Kum havuzu DB'SİZ DOĞUNCA çocukta
# `storage.active()` False döner ve dosya-tabanlı davranışa, yani migrasyon ÖNCESİ ÖLÇÜLMÜŞ-İYİ yola
# (07-22 sprinti: n_v1=100) dönülür. İKİNCİ KAZANÇ AYNI SATIRDA: canlı worker yazarken SICAK bir WAL
# veritabanını `shutil` ile kopyalamak tutarlı bir anlık görüntü DEĞİLDİR (ana dosya ile -wal/-shm
# ayrı anlarda okunur) — o risk de kapanır. Sınıf: (kopyalanan HALT tüm sandbox
# girişlerini bastırır) ikinci kuşağı, artı "SKIP_COPY denylist'i state'e yeni gelen artefaktları
# sessizce kaçırır" (hemen üstteki bars_intraday vakasıyla aynı sınıf).
SKIP_COPY = {"bars", "bars_intraday", "intraday_bars", "sprint", "secrets.json", "HALT",
             "meridian.db", "meridian.db-wal", "meridian.db-shm"}


def _now() -> str:
    """Şu anki UTC zamanını saniye çözünürlüklü ISO-8601 metni olarak verir."""
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


# Bir sprint FAZININ terminal (bitmiş/durmuş) mi yoksa hâlâ "koşuyor" gibi mi okunacağını TEK
# yerde tanımlar. `sprint_run` bu fazları yazar (baseline/search/candidate → koşuyor; done/stopped/
# error → terminal); `start()` 'starting' (koşuyor), `stop()` 'stopping' (terminal) yazar. Orphan
# göstergesi (aşağıda, status()) bu kümeyi kullanır: ölü pid + TERMİNAL faz NORMALDİR (iş bitti),
# ölü pid + terminal-OLMAYAN faz ise YARIDA KALMIŞ (orphan) bir sprinttir.
_TERMINAL_PHASES = frozenset({"done", "stopped", "stopping", "error"})


def status() -> dict:
    """Sprint durumunu okur ve canlılığı ÖLÇEREK zenginleştirir: zombi süreç toplanır, pid sinyalle
    yoklanır (`active`), ölü pid + terminal-olmayan faz `orphan` işaretlenir, son koşu satırları kum
    havuzu defterlerinden eklenir. SALT OKUMA — hiçbir sprinti diriltmez/öldürmez."""
    st = store.read_json(STATUS_FILE, {})
    pid, alive = st.get("pid"), False
    if pid:
        try:
            # Reap first: os.kill(pid, 0) SUCCEEDS on a zombie, so a finished child read as 'active'
            # forever and start() refused with 'already_running' for the life of the server.
            # WNOHANG waitpid clears the zombie (harmless ChildProcessError if it wasn't our child).
            try:
                os.waitpid(int(pid), os.WNOHANG)
            except (ChildProcessError, OSError, ValueError):  # sessiz-yutma: yardımcı/telemetri yolu; başarısızlığı karara girmez ve çağıran yedek değerle aynen devam eder
                pass
            os.kill(int(pid), 0)
            alive = True
        except (OSError, ValueError):  # sessiz-yutma: yardımcı/telemetri yolu; başarısızlığı karara girmez ve çağıran yedek değerle aynen devam eder
            alive = False
    # ORPHAN GÖSTERGESİ: pid KAYITLI ama ÖLÜ ve faz TERMİNAL DEĞİL → sprint YARIDA KALDI.
    # Ölçülen kusur: pid 96924 ölü, phase='baseline', progress
    # 281/527, dosya yaşı 42,6 sa. `active` (=alive) ZATEN False idi; ama okuyucu (pano) `phase`+
    # `progress`ten "%53 koşuyor" çiziyordu — yani `active` tek başına "koşuyor mu?"yu yanıtlamıyor,
    # çünkü DONMUŞ bir faz/ilerleme canlıymış gibi taşınıyor. Bu bayrak o ayrımı SPRINT.PY
    # KATMANINDA dürüstleştirir (Ajan B panoda bunu okuyup yansıtır — çakışma yok). Ölü pid +
    # TERMİNAL faz NORMALDİR (done/stopped/…: iş bitti) → orphan DEĞİL. Faz YOKSA "koşuyor" gibi de
    # okunmaz → orphan DEĞİL (zombie-reap testi v45 o hâli yalnız `active False` diye çiviler).
    # BURADA DİRİLTİLMEZ: status() salt okur. YENİDEN BAŞLATMA KADANSIN işidir —
    # `should_run` yetimi tetik sayar (sebep=yetim_sprint_yeniden, ≥YETIM_YENIDEN_SAAT fren).
    faz = st.get("phase")
    orphan = bool(pid) and not alive and faz is not None and faz not in _TERMINAL_PHASES
    # YASA 6: sprint_run.py her aramadan sonra `sprint_runs.jsonl`'a satır yazıyordu ve
    # KOD İÇİNDE HİÇBİR OKUYUCUSU YOKTU — üretildi, kimse tüketmedi; yedi desenli bütünlük raporunun
    # panoya hiç bağlanmamasıyla aynı kusur. Son koşular buradan durumun içine girer (pano zaten
    # sprint.status()'u render ediyor), böylece defterin bir tüketicisi olur.
    # TERS ORPHAN GÖRÜNÜR OLUR: yukarıdaki YASA-6 düzeltmesi okuyucuyu kurdu ama
    # defter DİSKTE HİÇ YOK — `read_jsonl` her zaman [] döndürüyor ve pano "son koşu yok" çiziyor.
    # 2026-07-22 sprinti aramayı TAMAMLADI (sprint_status.json: search.evaluated=8, phase=done) ve
    # satır yine yok: defter ya hiç doğmadı ya 07-23 depo taşımasında kayboldu. Hiçbir dedektör bu
    # yönü sormuyor — orphan taraması yalnız VAR OLAN dosyaları sorgular, "okuyucusu var ama dosyası
    # yok"u değil. `runs_ledger` o ayrımı taşır: "henüz satır yok" ile "defter hiç yok" AYRI hükümler.
    # TERS ORPHAN'IN KÖK NEDENİ BULUNDU. Yukarıdaki not "defter ya hiç doğmadı ya
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
    return {**st, "active": alive, "orphan": orphan,
            "orphan_note": (None if not orphan else
                            f"pid {pid} ÖLÜ ama faz '{faz}' terminal değil — sprint YARIDA KALDI "
                            f"(orphan): süreç yok, ilerleme donmuş, 'koşuyor' DEĞİL. Kadans yetim "
                            f"tetiğiyle (yetim_sprint_yeniden, ≥{YETIM_YENIDEN_SAAT:.0f} sa fren) "
                            f"uygun ilk gece penceresinde YENİDEN başlatır; bu gösterge yalnız okur."),
            "runs": _runs,
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

    KISIT: buradaki HAM YOL yazımları yalnız kum havuzu DEPOLAMA ARTEFAKTISIZ (yani
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
    # SNAPSHOT the v1 seed into the sandbox history. run.bootstrap_v01 does this in production; the
    # sandbox reset skipped it, so after Phase B shipped v2 (parent=1) a forward-LOSING v2 routed into
    # rollback.revert_to(1) → FileNotFoundError (swallowed by daily_cycle): the negative calibration point
    # was never written and the sprint could only ever close on WINNERS (a systematic training bias). Write
    # v0001.yaml directly (config.HISTORY here points at LIVE, not the sandbox, so we can't use snapshot()).
    config.dump_yaml(config.default_strategy(), hist / "v0001.yaml")


def _prune_old_sandboxes(keep: int = SANDBOX_KEEP) -> None:
    """Retain only the newest `keep` sprint sandboxes. Each start() copies the live state tree into a
    new dated dir (bars are symlinked) and nothing ever deleted them — an operator-paced disk leak.
    Never deletes the currently-active sandbox.

    BOYUT İDDİASI TAZELENDİ. Bu docstring "~1.5 MB" diyordu: YAZILDIĞI GÜN DOĞRUYDU,
    sonra canlı state büyüdü ve iddia bayatladı. A1'de ölçüm: state/ 617M, state/sprint 438M =
    4 kum havuzu × ~110M. SKIP_COPY'ye bars_intraday+intraday_bars (43M+40M = 83M) eklendikten sonra
    kum havuzu başına ARİTMETİK BEKLENTİ ~27M'dir (110−83). BU BİR TÜRETİM, ÖLÇÜM DEĞİL — yeni bir
    sandbox doğduğunda `du -sh state/sprint/*` ile doğrulanmadan "ölçüldü" diye anılmaz.
    Birikme sınırsız DEĞİL: SANDBOX_KEEP=3 + her start()'ta budama çalışıyor (A1'de
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

    `start()`TEN AYRI BİR FONKSİYON OLMASININ SEBEBİ ÖLÇÜLEBİLİRLİKTİR: izolasyon
    sözleşmesini sınayan test YASANIN KENDİSİNİ çağırabilmelidir. Sırayı (kopya, bağlar, sıfırlama)
    teste yeniden yazmak bu depoda tekrar tekrar yaşanan "aynı yasanın iki uygulaması" hatasıdır —
    testteki kopya yeşil kalırken üretim yolu sessizce ayrışır ve dedektör hiçbir şey ölçmez.
    Fonksiyon SAFtır: yalnız diski kurar, süreç doğurmaz, durum dosyası yazmaz."""
    # SBROOT KANONİK YOLA DAMGALANIR. `state/sprint_status.json` hâlâ
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


# ==================================================================================================
# "BU SÜREÇ KUM HAVUZUNDA MI?" — İZOLASYON SÖZLEŞMESİNİN SORULABİLİR HÂLİ
# --------------------------------------------------------------------------------------------------
# NEDEN VAR — ÖLÇÜLMÜŞ SIZINTI (docs/DENETIM-SKILL-CAGRI-IZI-2026-08-13.md).
# Bu dosyanın başlığı "canlı defterler, karne ve koşan Hermes ASLA dokunulmaz" diyor ve bu DEFTERLER
# için doğru. Ama kum havuzu, süreç DIŞINDAKİ paylaşımlı kaynakları da değiştirebiliyordu. Kanıt iki
# ayrı defterde, 59 saniye arayla:
#     sprint  2026-08-13T15:20:13  agent_skills_synced  enabled=26  linked=0
#             pruned=[parabolic-short-trade-planner, ibd-distribution-day-monitor,
#                     canslim-screener, economic-calendar-fetcher]
#     canlı   2026-08-13T15:21:12  agent_skills_synced  enabled=30  linked=4  pruned=[]   ← onarım
# ZİNCİR: kum havuzunda FMP anahtarı YOK → `skills.reconcile_enablement` o dört `fmp=req` skill'ini
# kapatıyor → `hermes.sync_agent_skills` kum havuzunun (26'lık) enabled setine bakıp onları
# CANLININ paylaşımlı `~/.hermes/skills` dizininden SÖKÜYOR. Söküm ile bir sonraki canlı senkron
# arasındaki pencerede o dört skill canlı ajanın kataloğunda da YOK — sunulmuyor, `skill_view` ile
# açılamıyor. Yani "kum havuzu canlıdan izoledir" vaadi AJAN KATMANINDA tutmuyordu.
#
# ÖLÇÜT YAPISALDIR, BAYRAK DEĞİL — ve bu bilinçli: `MERIDIAN_SPRINT_SBROOT` YALNIZ systemd yolunda
# yazılıyor (`start()`), `Popen` düşüş yolunda hiç yok. Bayrağa-tek dayanan bir ölçüt, sızıntıyı tam
# da düşüş yolunda (yerel geliştirme + systemd birimi kurulu olmayan sunucu) AÇIK bırakırdı. Yapı
# her iki yolu kapsar: kum havuzu TANIMI GEREĞİ `<canlı state>/sprint/<sid>/state` altında doğar
# (`_kur_kum_havuzu` yukarıda) ve çocuk `MERIDIAN_ROOT=<sbroot>` ile koştuğu için `config.STATE` bu
# yola çözülür. Bayrak varsa yine OKUNUR (varlığı kesin bilgidir), yapı ise yedek değil TABANDIR.
# ==================================================================================================
def kum_havuzunda() -> bool:
    """Bu SÜREÇ bir sprint kum havuzunda mı koşuyor? PAYLAŞIMLI bir kaynağa yazmadan önce sorulur.

    Kum havuzunun KENDİ dosyalarına yazmak serbesttir (zaten tüm amacı budur); bu kapı yalnız
    süreç dışındaki, canlıyla ORTAK kaynaklar içindir — bugünkü tek örneği ajanın
    `~/.hermes/skills` dizini (`hermes.sync_agent_skills`)."""
    try:
        st = Path(config.STATE).resolve()
    except OSError:  # sessiz-yutma: yol çözümü düştü (kopmuş symlink/izin) — kapı KAPALI tarafa değil AÇIK tarafa düşer; bu bir teşhis yolu değil, canlı senkronun kendisidir ve yanlış "kum havuzundayım" cevabı canlı onarımı durdururdu
        return False
    sb = os.environ.get("MERIDIAN_SPRINT_SBROOT")
    if sb:
        try:
            if Path(sb).resolve() in (st, *st.parents):
                return True
        except OSError:  # sessiz-yutma: bayrak yolu çözülemedi — aşağıdaki YAPISAL ölçüt zaten aynı soruyu bayraksız cevaplıyor, yani dedektör kapanmıyor sadece ikinci kanıtını kaybediyor
            pass
    # `<canlı state>/sprint/<sid>/state` → parent = <sid>, parent.parent = "sprint"
    return st.name == "state" and st.parent.parent.name == "sprint"


# ==================================================================================================
# KOŞUM YOLU — SPRINT KENDİ SYSTEMD BİRİMİNDE DOĞAR
# --------------------------------------------------------------------------------------------------
# ÖLÇÜLMÜŞ KÖK NEDEN (kanıt: ölüm-anı yakalayıcısı; üç ölümde de aynı desen):
#     14:50:02 sprint ilerliyor (113/531) → 14:54:14 worker YENİ pid ile ayağa kalkıyor (dağıtım
#     `systemctl restart meridian`) → 14:54:16 SPRINT ORPHAN → 14:54:22 pid yok. OOM YOK, traceback YOK.
# Aşağıdaki `Popen(..., start_new_session=True)` yeni bir OTURUM açar ama systemd'nin CGROUP'undan
# ÇIKARMAZ; systemd varsayılanı `KillMode=control-group` cgroup'taki HER süreci öldürür. Yani sprint
# her dağıtımda sessizce öldürülüyordu — kum havuzu, ilerleme ve gecelik kalibrasyon noktası birlikte.
# Bunu hiçbir `Popen` bayrağı çözemez (setsid oturumu değiştirir, cgroup'u değiştirmez); tek yapısal
# yol AYRI BİR SYSTEMD BİRİMİDİR: `deploy/oracle-a1/meridian-sprint@.service` (şablon; örnek adı = sid).
#
# FAIL-OPEN DEĞİL, FAIL-VISIBLE. Yol kullanılamıyorsa (birim kurulu değil, sudo geçmiyor, systemd yok
# — ör. yerel macOS geliştirmesi) eski `Popen` yoluna DÜŞÜLÜR, ama ASLA sessizce: `sprint_systemd_yok`
# olayı ADLI bir sebeple düşer ve `sprint_status.json`a `kosum_yolu:"systemd"|"popen"` damgalanır.
# Yani "sprint neden yine öldü?" sorusu bir sonraki turda ÖLÇÜMLE cevaplanır, tahminle değil.
# (Damganın çocuk yazımlarında hayatta kalması `sprint_run.STAMP_KEYS`e bağlıdır.)
#
# ÇİFT-SPRINT YASAĞI, DÜŞÜŞ YOLUNUN TEK GERÇEK RİSKİ: aynı kum havuzuna iki yazar, ölçümün kendisini
# çöpe atardı. Bu yüzden `Popen`a düşmeden ÖNCE birimin GERÇEKTEN koşmadığı `MainPID` ile SORULUR;
# koşuyorsa systemd yolu kabul edilir (tetik komutu hata dönmüş olsa bile).
# ==================================================================================================
BIRIM_DOSYA_ADI = "meridian-sprint@.service"
# Şablonun kurulu olabileceği yollar — systemd'nin birim arama sırasıyla aynı (yerel yönetici
# dizini önce). SALT DOSYA yoklaması yapılır, `systemctl cat` DEĞİL: bkz. `_birim_kurulu`.
BIRIM_ARANAN_DIZINLER = ("/etc/systemd/system", "/run/systemd/system",
                         "/usr/local/lib/systemd/system", "/usr/lib/systemd/system",
                         "/lib/systemd/system")
ORTAM_DOSYASI = "sprint.env"          # kum havuzunun KÖKÜNDE; birimin `EnvironmentFile=`i bunu okur
# Birim dosyasındaki mutlak yolun (WorkingDirectory + EnvironmentFile) KOD TARAFINDAKİ KARŞILIĞI.
# Bu bir İKİNCİ TANIM DEĞİL, bir KAPIDIR: kum havuzu bu kökün altında değilse (taşınmış kurulum,
# farklı MERIDIAN_ROOT, symlink'li yol) birim BAŞKA bir dosyadan ortam okurdu ve sprint yanlış kökle
# koşardı. Uyuşmazlık `yol_uyusmazligi` sebebiyle systemd yolunu REDDEDER — sessizce ayrışmaz.
BIRIM_KOK = "/opt/meridian"
# ZAMAN AŞIMLARI TAVANDIR, BEKLENEN SÜRE DEĞİL. `Type=simple` birimde `systemctl start` exec'ten
# hemen sonra döner (ölçülen mertebe: yüz milisaniye). Tavanın DAR tutulmasının sebebi ölçülmüş bir
# kısıttır: `/api/sprint/start` bir `async def` uçtur, yani bu çağrı olay döngüsünü BLOKLAR — uzun
# bir tavan panoyu ve /healthz'i asılı-tick bekçisinin eşiğine kadar dondururdu. 15 sn beklenenin
# ~50 katıdır ve zaman aşımı yolu GÜVENLİDİR (kuyruktaki iş iptal edilir, sonra düşülür).
BASLAT_ZAMAN_ASIMI = 15.0
# 20 sn > birimdeki `TimeoutStopSec=15`: systemd'nin SIGKILL'i HER ZAMAN bu tavandan ÖNCE gelir,
# yani buradaki zaman aşımı "systemd durduramadı" demektir — "beklemeyi bıraktık" değil.
# (`/api/sprint/stop` `def`tir, yani thread havuzunda koşar ve olay döngüsünü bloklamaz.)
DURDUR_ZAMAN_ASIMI = 20.0
MAINPID_DENEME, MAINPID_BEKLE_SN = 4, 0.25   # ≤1 sn: `Type=simple`de MainPID fork anında yazılır
# WORKER ORTAMINDAN ÇOCUĞA DEVREDİLENLER — ALLOWLIST, PREFİX KURALI DEĞİL.
# Bugünkü `Popen` yolu worker'ın TÜM ortamını (`{**os.environ, …}`) çocuğa akıtıyor; systemd birimi
# ise TEMİZ ortamla koşar. Fark bilinçli bir DARALTMADIR ve iki yönü de ölçüldü:
#   TAŞINIR (davranışı değiştirdiği ÖLÇÜLDÜ):
#     · MERIDIAN_PARALLEL_PROBES — `reflect._parallel_prefill_probes` + `reflect.prefill_incumbents`
#       okur; taşınmazsa arama SERİLEŞİR (canlı
#       birimde `=1`), yani sprint gece penceresine sığmayabilir.
#     · MERIDIAN_SEARCH_MAX_MIN  — `reflect.coordinate_descent_search` okur; varsayılanı 35, canlı
#       birimde 60. Taşınmazsa
#       aramanın duvar-saati tavanı SESSİZCE değişirdi (ölçüm koşulları ayrışır).
#     · PATH/HOME/LANG/LC_ALL/TZ/PYTHONPATH — süreç zeminidir; TZ ve LANG tarih/dize davranışına girer.
#   TAŞINMAZ (bilinçli): `MERIDIAN_DASH_TOKEN` (SIR — bugün her sprint çocuğunun /proc/<pid>/environ'ında
#     duruyor; bu birim o yüzeyi kapatır), `MERIDIAN_BIND_HOST`/`MERIDIAN_AUTOSTART_*`/`CYCLE_POLL_*`
#     (yalnız sunucu-giriş noktaları okur), `HERMES_*` (sprint LLM ÇAĞIRMAZ). Prefiks kuralı
#     (`MERIDIAN_*` hepsi) YAZILMADI: ilk isabeti `MERIDIAN_DASH_TOKEN` olurdu.
DEVREDILEN_ORTAM = ("PATH", "HOME", "LANG", "LC_ALL", "TZ", "PYTHONPATH",
                    "MERIDIAN_PARALLEL_PROBES", "MERIDIAN_SEARCH_MAX_MIN")


def _birim_adi(sid: str) -> str:
    """Örnek adı = sid = kum havuzu dizin adı. Tek eşleme, üç yerde aynı ad (birim, dizin, durum)."""
    return f"meridian-sprint@{sid}.service"


def _birim_kurulu() -> str | None:
    """Şablon birim kurulu mu? → kurulu dosyanın yolu ya da None.

    SALT DOSYA YOKLAMASI, BİLİNÇLİ OLARAK ALT SÜREÇ YOK. `systemctl cat` daha "doğru" bir yoklama
    olurdu ama (a) henüz systemd yolunu seçmiş değiliz — yoklamanın kendisi bedelli olmamalı, (b) bu
    depoda `subprocess.Popen`ı saplayan MEVCUT sprint testleri var ve `subprocess.run` onların
    saplamasına girerdi: yoklama, ölçtüğü şeyi bozardı."""
    for d in BIRIM_ARANAN_DIZINLER:
        try:
            p = Path(d) / BIRIM_DOSYA_ADI
            if p.exists():
                return str(p)
        except OSError:  # sessiz-yutma: yol yoklanamıyorsa "kurulu değil" hükmü DOĞRUDUR ve çağıran zaten adlı sebeple popen'a düşer
            continue
    return None


def _systemctl_komutu() -> tuple[list[str] | None, str | None]:
    """Birimi TETİKLEYEN komutun öneki → (komut, None) | (None, sebep).

    SEAM `MERIDIAN_SPRINT_SYSTEMCTL`: tetik komutunu baştan sona değiştirir. Var olma sebebi ölçülmüş
    bir belirsizliktir — `meridian.service`te `NoNewPrivileges=true` yürürlüktedir ve bu bayrak SETUID
    ikililerini (sudo TAM OLARAK öyle bir ikilidir) yetki kazanmaktan alıkoyar; operatör kabuğunda
    ölçülen `sudo -n` başarısı worker İÇİNDEN geçerli olduğunu KANITLAMAZ. Sudo geçmezse operatörün
    ikinci yolu (polkit + `busctl call … StartUnit`, setuid'siz) KOD DEĞİŞİKLİĞİ İSTEMEZ: bu değişken
    onu yerine koyar. Ölçüm komutu ve iki seçeneğin gerekçesi birim dosyasının kurulum adımı [3]'te."""
    ham = (os.environ.get("MERIDIAN_SPRINT_SYSTEMCTL") or "").strip()
    if ham:
        parcalar = shlex.split(ham)
        return (parcalar, None) if parcalar else (None, "tetik_komutu_bos")
    sc = shutil.which("systemctl")
    if not sc:
        return None, "systemctl_yok"
    if getattr(os, "geteuid", lambda: 1)() == 0:
        return [sc], None          # root'sak sudo'ya hiç gerek yok (konteyner/kurtarma yolu)
    sudo = shutil.which("sudo")
    if not sudo:
        return None, "sudo_yok"
    # `-n`: parola İSTEMEZ, ister istemez BAŞARISIZ olur. Bekleyen bir tetik zamanlayıcı thread'ini
    # kilitlerdi; "hızlı ve adlı başarısızlık" burada doğru taraftır.
    return [sudo, "-n", sc], None


def _ortam_metni(ortam: dict) -> str:
    """systemd `EnvironmentFile` içeriği — HER değer TEK TIRNAK içinde.

    SESSİZ BOZULMA SINIFI: systemd'nin env ayrıştırıcısı KABUK BENZERİDİR. `KEY={"a": 1}` yazılsaydı
    içteki `"` işaretleri TIRNAK sayılıp sökülür, çocuğa `{a: 1}` ulaşır ve `json.loads` patlardı —
    üstelik bunu ancak canlıda, gece yarısı öğrenirdik. Tek tırnak içinde systemd hiçbir şeyi
    yorumlamaz. Değerde tek tırnak/satır sonu varsa ValueError: taşınamayan bir ortamla systemd yolu
    seçilmez (çağıran `Popen`a düşer ve sebebi yazar) — kırpmak ya da kaçırmak, ölçülmemiş bir
    dönüşüm uydurmak olurdu."""
    satirlar = []
    for k in sorted(ortam):
        v = str(ortam[k])
        if "'" in v or "\n" in v or "\r" in v:
            raise ValueError(f"{k}: systemd ortam dosyasında taşınamayan karakter (tek tırnak/satır sonu)")
        satirlar.append(f"{k}='{v}'")
    return "\n".join(satirlar) + "\n"


def _mainpid(birim: str) -> int | None:
    """Birimin ana süreç pid'i (`systemctl show -p MainPID`) — 0/okunamaz ise None.

    SALT OKUMA, YETKİ GEREKTİRMEZ: `show` bir D-Bus property okumasıdır, `sudo` KULLANILMAZ. Bu yüzden
    tetik komutu değiştirilmiş olsa (polkit/busctl) bile bu yoklama çalışır — okuma ile tetik AYRI
    kanallardır ve ayrı kalmaları teşhis için önemlidir."""
    sc = shutil.which("systemctl")
    if not sc:
        return None
    try:
        r = subprocess.run([sc, "show", "-p", "MainPID", "--value", birim],
                           capture_output=True, text=True, timeout=10, stdin=subprocess.DEVNULL)
        if r.returncode != 0:
            return None
        return int((r.stdout or "").strip() or 0) or None      # systemd koşmayan birime 0 der
    except (OSError, ValueError, subprocess.SubprocessError):  # sessiz-yutma: sonuç KAYDA GEÇİYOR — çağıran None'ı "birim koşmuyor" diye ADLI sebebe (mainpid_yok) çevirir ve popen'a düşer
        return None


def _systemd_durdur(birim: str, komut: list[str] | None = None, *,
                    bloklamadan: bool = False) -> tuple[bool, str | None]:
    """`systemctl stop <birim>` → (durduruldu?, sebep). `bloklamadan`: yalnız işi kuyruğa koyar."""
    if komut is None:
        komut, sebep = _systemctl_komutu()
        if komut is None:
            return False, sebep
    args = [*komut, "stop", *(["--no-block"] if bloklamadan else []), birim]
    try:
        r = subprocess.run(args, capture_output=True, text=True,
                           timeout=DURDUR_ZAMAN_ASIMI, stdin=subprocess.DEVNULL)
    except subprocess.TimeoutExpired:  # sessiz-yutma: sonuç KAYDA GEÇİYOR — sebep çağırana döner ve `stop()` onu `sprint_systemd_durdurulamadi` olayına yazar; istisna nesnesinin kendisi bilgi taşımaz (tavan zaten bizim)
        return False, "zaman_asimi"
    except (OSError, subprocess.SubprocessError) as e:
        return False, f"{type(e).__name__}: {e}"
    if r.returncode == 0:
        return True, None
    return False, (((r.stderr or r.stdout or "").strip().splitlines() or [""])[0][:200]
                   or f"rc={r.returncode}")


def _systemd_baslat(sid: str, sbroot: Path, ortam: dict) -> tuple[int | None, str | None, str | None]:
    """Sprint'i KENDİ systemd biriminde başlat → (pid, None, ayrinti) | (None, sebep, ayrinti).

    `sebep` HER ZAMAN adlı bir dizedir (UYDURMA YASAĞI'nın karşılığı: "olmadı" değil, "şu adımda,
    şu yüzden olmadı"). Sıra ucuzdan pahalıya: komut → birim → yol kapısı → ortam dosyası → tetik."""
    komut, sebep = _systemctl_komutu()
    if komut is None:
        return None, sebep, None
    if not _birim_kurulu():
        return None, "birim_kurulu_degil", f"aranan: {BIRIM_DOSYA_ADI} @ {', '.join(BIRIM_ARANAN_DIZINLER)}"
    ortam_dosyasi = Path(sbroot) / ORTAM_DOSYASI
    beklenen = f"{BIRIM_KOK}/state/sprint/{sid}/{ORTAM_DOSYASI}"
    if str(ortam_dosyasi) != beklenen:
        return None, "yol_uyusmazligi", f"birim '{beklenen}' okur, kum havuzu '{ortam_dosyasi}'"
    try:
        # sır penceresi yok: dosya 0600 İZNİYLE DOĞAR — write_text+chmod çifti kısa bir
        # herkes-okur penceresi bırakıyordu (WP6/H9 süpürmesi 2026-08-23; secrets._write emsali)
        fd = os.open(ortam_dosyasi, os.O_CREAT | os.O_WRONLY | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w") as f:
            f.write(_ortam_metni(ortam))
        os.chmod(ortam_dosyasi, 0o600)
    except (OSError, ValueError) as e:
        return None, "ortam_yazilamadi", f"{type(e).__name__}: {e}"
    birim = _birim_adi(sid)
    try:
        r = subprocess.run([*komut, "start", birim], capture_output=True, text=True,
                           timeout=BASLAT_ZAMAN_ASIMI, stdin=subprocess.DEVNULL)
        rc = r.returncode
        ayrinti = (((r.stderr or r.stdout or "").strip().splitlines() or [""])[0][:200]) or None
    except subprocess.TimeoutExpired:  # sessiz-yutma: sonuç KAYDA GEÇİYOR — `rc=None` aşağıda `zaman_asimi` sebebine çevrilir, iş iptal edilir ve `sprint_systemd_yok` olayı ayrıntısıyla düşer
        rc, ayrinti = None, f"tetik {BASLAT_ZAMAN_ASIMI:.0f} sn'de dönmedi"
    except (OSError, subprocess.SubprocessError) as e:
        return None, "tetik_calistirilamadi", f"{type(e).__name__}: {e}"
    # ÇİFT-SPRINT KAPISI: `Popen`a düşmeden önce birimin koşup koşmadığı SORULUR. Tetik hata dönse
    # bile birim ayakta olabilir (ör. sudo stderr'e uyarı yazıp rc≠0 verirken job başarılı olabilir);
    # o hâlde ikinci bir süreç doğurmak aynı kum havuzuna iki yazar demektir ve ölçüm çöpe gider.
    pid = None
    for _ in range(MAINPID_DENEME):
        pid = _mainpid(birim)
        if pid:
            break
        time.sleep(MAINPID_BEKLE_SN)
    if pid:
        return pid, None, (ayrinti if rc not in (0, None) else None)
    if rc is None:
        # ZAMAN AŞIMI + MainPID yok: iş HÂLÂ KUYRUKTA olabilir ve biz `Popen` ettikten sonra
        # ateşleyebilir. En iyi çaba iptal, sonra düşüş — çift sprint riski kapatılır.
        _systemd_durdur(birim, komut, bloklamadan=True)
        return None, "zaman_asimi", ayrinti
    # rc==0 ama MainPID yok: `Type=simple`de MainPID fork anında yazılır, yani süreç DOĞDU ve HEMEN
    # öldü (ya da systemd okunamıyor). Koşan bir şey OLMADIĞI ölçüldüğü için düşüş güvenlidir.
    return None, ("mainpid_yok" if rc == 0 else "baslatma_hatasi"), (ayrinti or f"rc={rc}")


def start(cfg: dict | None = None) -> dict:
    """Yeni bir sprint başlatır: eski kum havuzlarını budar, sid'li havuzu kurar ve çocuğu ÖNCE systemd
    biriminde, olmazsa `Popen` yedeğiyle doğurur. Zaten koşan sprint varsa `already_running` döner.
    Durum dosyasına pid/faz/koşum yolu + taze-aday tetiğinin hipotez sayacı tabanı damgalanır."""
    cfg = cfg or {}
    if status().get("active"):
        return {"status": "already_running", **status()}
    _prune_old_sandboxes()
    sid = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    sbroot = _kur_kum_havuzu(sid)
    live = config.STATE
    conf = {"k_max": int(cfg.get("k_max", 3)), "budget": int(cfg.get("budget", 12))}
    # TEK KODLAMA, İKİ YOL: aynı dize hem `Popen` argümanına hem systemd ortam dosyasına gider —
    # iki ayrı `json.dumps` çağrısı, iki yolun sessizce ayrışabileceği bir yüzey olurdu. BOŞLUKSUZ
    # (`separators`): `${VAR}` zaten tek argüman verir, ama biri bir gün birimde süslü parantezi
    # düşürürse (`$VAR`) systemd değeri boşluklardan böler — boşluksuz dize o hatayı da yutar.
    conf_json = json.dumps(conf, separators=(",", ":"))
    sprint_ortami = {"MERIDIAN_ROOT": str(sbroot), "MERIDIAN_BROKER": "internal",
                     "MERIDIAN_SPRINT_STATUS": str((live / STATUS_FILE).resolve())}
    pid, sebep, ayrinti = _systemd_baslat(sid, sbroot, {
        **{k: os.environ[k] for k in DEVREDILEN_ORTAM if os.environ.get(k)},
        **sprint_ortami, "MERIDIAN_SPRINT_SBROOT": str(sbroot), "MERIDIAN_SPRINT_CONF": conf_json})
    from . import obs
    if pid is not None:
        kosum_yolu, birim = "systemd", _birim_adi(sid)
        obs.log("sprint_systemd_baslatildi", sid=sid, birim=birim, pid=pid, uyari=ayrinti,
                detail=("sprint KENDİ systemd biriminde koşuyor — worker restart'ı artık onu "
                        f"öldürmez (v241 kök nedeni). Günlüğü: journalctl -u {birim}"))
    else:
        kosum_yolu, birim = "popen", None
        obs.warn("sprint_systemd_yok", sebep=sebep, ayrinti=ayrinti, sid=sid,
                 birim=_birim_adi(sid), kosum_yolu="popen",
                 detail=("systemd koşum yolu KULLANILAMADI — sprint eski `Popen` yoluyla, yani "
                         "WORKER'IN CGROUP'UNDA doğuyor: `systemctl restart meridian` onu yine "
                         "öldürür (v241 kök nedeni GERİ, ama görünür). Kurulum adımları: "
                         "deploy/oracle-a1/meridian-sprint@.service başlığı."))
        proc = subprocess.Popen(
            [sys.executable, "-m", "meridian.sprint_run", str(sbroot), conf_json],
            env={**os.environ, **sprint_ortami}, stdout=subprocess.DEVNULL,
            stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, start_new_session=True)
        pid = proc.pid
    # HİPOTEZ SAYACI BAŞLANGIÇTA DAMGALANIR: otomatik kadansın ikinci tetiği ("son sprintten beri
    # taze aday birikti mi") ancak bir TABAN varsa ölçülebilir. Damga olmadan `taze = len(hyps) − 0`
    # olurdu ve tetik her gece yanardı — haftalık disiplin sessizce kaybolurdu.
    # DAMGAYI ÇOCUK SÜREÇ SİLİYORDU. Yukarıdaki `Popen` çocuğa
    # `MERIDIAN_SPRINT_STATUS` ile BU dosyayı verir ve `sprint_run._write_live_status` onu
    # birleştirmeden eziyordu: aşağıdaki damga İLK ilerleme yazımında yok oluyor, `should_run`
    # tabanı 0 sayıp her gece tetikliyordu. Koruma çocuk tarafında (`sprint_run._damgayi_koru`) —
    # yazımın kendi katmanında, çünkü `stop()` ve çocuğun hata yolu da aynı dosyaya yazar.
    try:
        from . import memory
        n_hyp = len(memory.all_hypotheses())
    except Exception as e:
        obs.warn("sprint_hyp_baseline_failed", error=f"{type(e).__name__}: {e}",
                 detail="taze-aday tetiği tabanı yazılamadı — kadans haftalık tabana düşer")
        n_hyp = None
    # ŞEMA KORUNUR, İKİ ALAN EKLENİR. Mevcut okuyucuların (pano, kadans `should_run`, watchdog
    # `_sprint_liveness`, yetim göstergesi) beklediği alan kümesi AYNEN durur — `pid` hâlâ pid'dir,
    # yalnız KAYNAĞI değişti (systemd yolunda `MainPID`). Eklenen ikisi TEŞHİS içindir:
    #   · `kosum_yolu` — "bu sprint hangi yoldan koştu?" sorusu SONRADAN sorulabilir olsun diye.
    #   · `birim` — systemd yolunda `journalctl -u <birim>` adresini taşır; popen yolunda None
    #     (uydurma yok: birim yoksa alan da bir birim ADI taşımaz).
    # İkisi de `sprint_run.STAMP_KEYS`e eklendi, yoksa çocuğun İLK ilerleme yazımında silinirlerdi
    # (C15'in birebir aynı sınıfı — damga ebeveynde doğar, çocuk dosyayı yeniden yazar).
    st = {"pid": pid, "sid": sid, "phase": "starting", "started_at": _now(),
          "cfg": conf, "sbroot": str(sbroot), "eval_start": EVAL_START, "cutoff": CUTOFF,
          "n_hyp_at_start": n_hyp, "kosum_yolu": kosum_yolu, "birim": birim}
    store.write_json(STATUS_FILE, st)
    return {"started": True, **st}


# ==================================================================================================
# OTOMATİK KADANS — TETİK, EŞZAMANLILIK BEKÇİSİ, BÜTÇE ÖZ-AYARI
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
#       (`reflect._parallel_prefill_probes` → `_havuz_tavani`, workers = max(2, min(4, çekirdek−2))).
#       İkisi birlikte makineyi doyurur ve
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


# ------------------------------------------------------------------------------------------------
# CANLI-ARAMA BAYRAĞI: BAYATLIK YASASI (canlı vaka).
# ÖLÇÜLEN ARIZA: `sprint_cadence_skip sebep=mesgul:canli_arama` 4+ gün boyunca HER döngüde tekrar
# etti; aynı pencerede sprint yetim (pid ölü, faz 'baseline') ve 9,6 gündür yeni hipotez yok.
# `hermes.SEARCH_PROGRESS` süreç-içi bir sözlüktür ve `reflect_once` onu normal/istisna çıkışta
# temizler (`hermes.py` → `reflect_once` + `_reflect_once_govde`) — yani bayrağın GÜNLERCE
# `running=True` kalabilmesinin tek yolu,
# aramanın kendisinin ASILI kalmasıdır (canlı arama `ProcessPoolExecutor` açar,
# `reflect._parallel_prefill_probes`;
# ölen bir işçi süreci ebeveyni sonsuza dek bekletebilir). Bayrak o hâlde DÜRÜSTÇE "koşuyor" der
# ama iş ölüdür — ve kadansın tek meşguliyet kanıtı bu bayrak olduğundan ÖĞRENMENİN TAMAMI
# (sprint → hipotez → kalibrasyon) sessizce kilitlenir. Bu, YASA-4'ün kovaladığı sınıfın ta
# kendisidir: temizlenmeyen bir bayrak = beyansız sonsuz kilit.
#
# YASA: bayrak `running=True` VE parmak izi (faz/i/total/değişken/değer) ARAMA_BAYAT_SAAT boyunca
# HİÇ değişmemişse arama BAYAT sayılır — kadans onu meşguliyet kanıtı olarak KULLANMAZ, tespit
# OLAYLIDIR (`sprint_arama_bayragi_bayat`, episode başına bir kez) ve bayrak panoya da dürüst
# görünsün diye `running=False, phase="bayat_temizlendi"` ile işaretlenir (hermes_runtime:522 aynı
# sözlüğü render eder). Asılı iş parçacığı bir gün UYANIRSA kendi `update`i bayrağı yeniden yazar
# ve parmak izi DEĞİŞTİĞİ için gözlem sıfırlanır — canlı bir arama asla bayat okunmaz.
#
# EŞİK TÜRETİMDİR, ÖLÇÜM DEĞİL: incumbent walk ~90 sn ÖLÇÜLÜDÜR (`hermes._reflect_once_govde`
# `phase="incumbent"` adımı) ve her sonda
# `_on_probe` ile parmak izini değiştirir; 6 saat = o adımın >200 katı. İkincil özellik: gece
# penceresi 8 saat (22→06) olduğundan, pencere başında bayatlaşan bir bayrak AYNI gece içinde
# aşılır ve sprint o gece kendine gelir.
ARAMA_BAYAT_SAAT = 6.0
# Süreç-içi gözlem defteri — izlediği bayrakla AYNI ömürde (restart ikisini birden sıfırlar).
_ARAMA_GOZLEM: dict = {"iz": None, "beri": None, "olayli": False}
# YETİM YENİDEN-BAŞLATMA FRENİ: yetim tetiği ancak yetim başlangıç bu kadar eskiyse yanar.
# 12 saat = gece penceresinin (8 sa) üstü — aynı gece içinde ölen bir çocuk AYNI pencerede ikinci
# kez doğamaz, en erken ertesi gece denenir (çökme döngüsü ≤1 deneme/gece'ye sınırlanır).
YETIM_YENIDEN_SAAT = 12.0
# Yetim tespiti episode başına BİR olay üretir (sid ile anahtarlanır) — 300 sn'lik poll'de her
# turda warn basmak, alarmın kendisini gürültüye çevirirdi.
_YETIM_OLAYLI: set = set()

# ==================================================================================================
# MEŞGULİYET KAPILARI YETİM-RESTART'I KALICI BLOKLUYORDU (canlı ölçüm)
# --------------------------------------------------------------------------------------------------
# ÖLÇÜLEN ARIZA — canlı olay defteri, aynı satır her poll'de:
#     sprint_cadence_skip{sebep:"mesgul:canli_arama", yetim:true, gecen_gun:5,
#                         arama_bayrak_yasi_sa:0.17, arama_bayat:false}
# Yetim bir TETİK yapılmıştı (`yetim_sprint_yeniden`) ama tetik, gövdede meşguliyet
# kapılarının ARDINA konmuştu. Beyin zinciri ~5 dakikada bir yansıma turu açtığı için
# `SEARCH_PROGRESS` parmak izi sürekli DEĞİŞİYOR → bayatlık saati her turda sıfırlanıyor →
# `arama["mesgul"]` ASLA False olmuyor. Yani bayatlık yasası (ARAMA_BAYAT_SAAT) doğru
# çalışıyor ve tam da bu yüzden tetik hiç yanmıyor: bayrak asılı değil, gerçekten meşgul. Sonuç
# yetim-restart'ın ÖLÜ bir mekanizma olması — 5 gündür ölü bir çocuk, 5 gündür yeniden doğmuyor.
#
# AYRIM: "MEŞGUL" İKİ AYRI SORUYU CEVAPLIYOR ve ikisi tek argümanla taşınıyordu.
#   (a) YÜK KAPISI  — `canli_arama`, `bar_kovalamasi`: "makine şu an dolu mu?" Bu soru YETİM için
#       sorulmaz: yetim ZATEN ÖLÜ bir süreçtir, canlı aramayla ÇAKIŞMAZ (ayrı süreçler) ve onu
#       yeniden doğurmak gece penceresinde, 12 saatlik frenin ardında, poll başına en çok bir kez
#       olur. Yük kapısının kalıcı olması, öğrenmenin tamamını (sprint → hipotez → kalibrasyon)
#       süresiz kilitliyordu — yani kapının önlediği zarardan büyük bir zarar üretiyordu.
#   (b) YETKİ KAPISI — `elle_tik`: "bu çağıranın sprint başlatmaya HAKKI var mı?" Bu bir yük
#       sorusu DEĞİLDİR ve yetim onu deleMEZ. `scheduler.advance_once`ın iki çağıranı var (daemon
#       döngüsü + panonun ELLE TİK düğmesi) ve ÖLÇÜLMÜŞ bir kaza var: elle tik,
#       saat 22:00'yi geçince gerçekten 4 işçilik bir alt süreç başlatıyordu. Operatör "bir tur
#       ilerlet" derken dakikalarca sürecek bir antrenman İSTEMEMİŞTİR — sprintin elle tetiği ayrı
#       bir düğmedir (`/api/sprint/start`) ve o hiçbir kapıya uğramaz.
# Bu yüzden bypass YÜK kapılarına özgüdür; yetki kapıları burada adıyla listelenir.
#
# KORUNAN KURALLAR: (1) `st.active` (GERÇEKTEN koşan sprint) bypass edilmez — iki sprint 8 çekirdeği
# ikiye böler. (2) Gece penceresi (SPRINT_HOURS) yerinde kalır ve yetim tetiğinden ÖNCE gelir:
# yarıda kalmış bir antrenmanı gündüz yeniden başlatmak, 4 işçiyi canlı kararların makinesine
# sokmaktır. (3) 12 saatlik yetim freni (YETIM_YENIDEN_SAAT) yerinde kalır — bypass yalnız
# `yetim_tetik` (yetim ∧ fren aşıldı) için açılır, çıplak `yetim` için değil; aksi hâlde hemen ölen
# bir çocuk 5 dakikada bir yeniden doğardı (çökme döngüsü).
# ==================================================================================================
MESGUL_YETKI_KAPILARI = frozenset({"elle_tik"})


def _arama_durumu(simdi: dt.datetime | None = None) -> dict:
    """Canlı koordinat-inişi araması ŞU AN meşguliyet kanıtı mı? `hermes.search_progress_oku()`dan
    okunur. Okunamıyorsa MEŞGUL SAYILIR: muhafazakâr taraf, "emin değilsen 8 çekirdeği ikiye
    bölme"dir. Dönüş her zaman yaş taşır: `yas_sa` bayrağın SON İLERLEMEDEN beri kaç saattir
    değişmediğidir (skip olayına aynen çıkar — bkz. maybe_start).
    `simdi` yalnız tz-AWARE ise saat kabul edilir (should_run'ın `gun_ref` seam'iyle aynı kural).

    KAYNAK DEĞİŞTİ (2026-08-17, Ö-50): eskiden `hermes.SEARCH_PROGRESS` sözlüğü DOĞRUDAN okunurdu
    ve docstring gerekçesi "zamanlayıcı ve api AYNI süreçtedir — daemon thread" idi. Öğrenme
    döngüsü kendi systemd birimine taşınınca bu varsayım ÇÖKER ve çöküş SESSİZDİR: sözlük okunamaz
    hâle gelmez, BOŞ kalır → `running` falsy → "meşgul değil" → sprint KOŞAN BİR ARAMANIN ÜSTÜNE
    8 çekirdeklik antrenman başlatırdı. Aşağıdaki `except` yedeği bunu YAKALAYAMAZDI çünkü ortada
    istisna yoktu. Üç değerli okuyucu tam bu yüzden var: "ölçülemedi" ile "arama yok" ayrı
    cevaplardır ve yalnız ikincisi sprint'i serbest bırakır."""
    try:
        from . import hermes
        okuma = hermes.search_progress_oku()
    except Exception as e:
        from . import obs
        obs.warn("sprint_search_busy_unreadable", error=f"{type(e).__name__}: {e}",
                 detail="arama durumu okunamadı — sprint MEŞGUL sayıp başlamadı (muhafazakâr taraf)")
        return {"mesgul": True, "bayat": False, "yas_sa": None, "faz": None, "kaynak": "okunamadi"}
    if okuma["durum"] == "olculemedi":
        from . import obs
        obs.warn("sprint_search_busy_unreadable", error=okuma.get("neden"),
                 detail="arama durumu ÖLÇÜLEMEDİ — sprint MEŞGUL sayıp başlamadı (muhafazakâr taraf)")
        return {"mesgul": True, "bayat": False, "yas_sa": None, "faz": None, "kaynak": "olculemedi"}
    sp = okuma["kayit"]
    if not sp.get("running"):
        _ARAMA_GOZLEM.update(iz=None, beri=None, olayli=False)
        return {"mesgul": False, "bayat": False, "yas_sa": None, "faz": sp.get("phase"),
                "kaynak": "bayrak"}
    if simdi is None or simdi.tzinfo is None:
        simdi = dt.datetime.now(dt.timezone.utc)
    iz = (sp.get("phase"), sp.get("i"), sp.get("total"), sp.get("variable"), sp.get("new"))
    if _ARAMA_GOZLEM.get("iz") != iz or _ARAMA_GOZLEM.get("beri") is None:
        _ARAMA_GOZLEM.update(iz=iz, beri=simdi, olayli=False)      # ilerleme var → saat sıfırlanır
    yas_sa = max(0.0, (simdi - _ARAMA_GOZLEM["beri"]).total_seconds() / 3600.0)
    bayat = yas_sa >= ARAMA_BAYAT_SAAT
    if bayat and not _ARAMA_GOZLEM.get("olayli"):
        from . import obs
        obs.warn("sprint_arama_bayragi_bayat", yas_sa=round(yas_sa, 1),
                 esik_saat=ARAMA_BAYAT_SAAT, faz=sp.get("phase"), i=sp.get("i"),
                 total=sp.get("total"),
                 detail=("canlı arama bayrağı `running=True` ama parmak izi bu süredir HİÇ "
                         "değişmedi — arama asılı/ölü sayıldı; kadans bu bayrağı artık meşguliyet "
                         "kanıtı olarak KULLANMAYACAK (öğrenme kilidi açılıyor). Bayrak panoda da "
                         "dürüst görünsün diye 'bayat_temizlendi' ile işaretlendi; asılı iş "
                         "parçacığı uyanırsa kendi yazımı gözlemi sıfırlar"))
        try:
            # KAPIDAN GEÇER (Ö-50): eskiden `SEARCH_PROGRESS.update(...)` doğrudan çağrılıyordu.
            # Süreç ayrımından sonra o yazım HİÇBİR İŞE YARAMAZDI — sprint kendi belleğindeki
            # sözlüğü yazar, panonun okuduğu süreç onu asla görmezdi. `_progress` hem belleği hem
            # disk aynasını yazar, yani "bayat temizlendi" beyanı gerçekten okuyucuya ulaşır.
            hermes._progress(
                running=False, phase="bayat_temizlendi", bayat_yas_sa=round(yas_sa, 1),
                bayat_temizleyen="sprint_kadansi",
                bayat_ts=simdi.isoformat(timespec="seconds"))
        except Exception:  # sessiz-yutma: yardımcı/telemetri yolu; başarısızlığı karara girmez ve çağıran yedek değerle aynen devam eder
            pass
        _ARAMA_GOZLEM["olayli"] = True
    return {"mesgul": not bayat, "bayat": bayat, "yas_sa": round(yas_sa, 2),
            "faz": sp.get("phase"), "kaynak": "bayrak"}


def _search_busy() -> bool:
    """GERİYE UYUM SARICI: karar `_arama_durumu`dadır — bayatlık yasası oradadır."""
    return bool(_arama_durumu()["mesgul"])


def should_run(*, mesgul: str | None = None, now: dt.datetime | None = None) -> dict:
    """Kadans bu an sprint başlatmalı mı? DÖNÜŞ her zaman bir SEBEP taşır — `False` tek başına
    "arıza mı, disiplin mi" sorusunu cevaplamaz ve tam olarak o belirsizlik kapatılıyor."""
    from . import memory
    st = status()
    now = now or dt.datetime.now()
    hyps = memory.all_hypotheses()
    son = st.get("started_at")
    # GÜN BACAĞI ARTIK ENJEKTE `now`DAN TÜRER ("kararın ânı" seam'i kapatıldı). `son`
    # (started_at) her zaman tz-AWARE UTC'dir (`_now()`); gün farkı ancak KARŞILAŞTIRILABİLİR bir
    # MUTLAK anla hesaplanabilir. Çağıran tz-aware bir `now` verdiyse karar ânı ODUR ve gün bacağı
    # onu kullanır → karar test-edilebilir olur, saat ve gün bacakları TEK ana dayanır.
    # NAIVE ya da VERİLMEMİŞ `now` mutlak bir ana denk düşmez (aware `son`dan çıkarılırsa TypeError
    # olurdu) → gerçek UTC saatine düşülür. Bu geri-düşüş DAVRANIŞ-NÖTRDÜR: üretimde `now=None →
    # dt.datetime.now()` (naive yerel) olduğundan `gun_ref` BİREBİR eski ifadeye
    # (`dt.datetime.now(utc)`) eşittir — hiçbir üretim çağıranı değişmez. v159 mesafe-çivisi de
    # naive SABİT bir tarih enjekte ettiğinden AYNI geri-düşüşe girer ve yeşil kalır. Naive `now`u
    # UTC sanıp çevirmek (`.replace`/`.astimezone`) HEM üretim nötrlüğünü HEM v159'u bozardı — o
    # yüzden bilinçle YAPILMIYOR (ayrım "aware mı" sorusudur, bir dönüştürme değil).
    gun_ref = now if now.tzinfo is not None else dt.datetime.now(dt.timezone.utc)
    try:
        gecen = gun_ref - dt.datetime.fromisoformat(str(son))
        gun, gecen_saat = gecen.days, round(gecen.total_seconds() / 3600.0, 1)
    except (TypeError, ValueError):  # sessiz-yutma: sonuç KAYDA GEÇİYOR (gun=None → "hiç koşmadı" tetiği) — bilgi kaybolmaz
        gun, gecen_saat = None, None
    taze = len(hyps) - int(st.get("n_hyp_at_start") or 0)
    # ARAMA BAYRAĞI GÖZLEMİ AYNI KARAR ÂNIYLA (gun_ref) OKUNUR — yaş, skip olayına aynen çıkar.
    arama = _arama_durumu(gun_ref)
    # YETİM SPRINT: pid ÖLÜ + faz terminal DEĞİL (status():orphan). Yetim bir koşu "koştu"
    # SAYILMAZ — sayılırsa haftalık taban, YARIDA KALMIŞ bir başlangıçtan ölçülür ve kadans 7 gün
    # boşa susar (canlı vaka: 4,4 gündür ölü çocuk, faz='baseline', kadans
    # `tetik_yok/mesgul` arasında salınıyordu). YENİDEN BAŞLATMA KADANSIN İŞİDİR (operatör
    # mandası "elle tetik beklemeden tam fonksiyonlu") — o yüzden yetim bir TETİKTİR,
    # yalnız gösterge değil. ÇÖKME DÖNGÜSÜ FRENİ: tetik ancak yetim başlangıç YETIM_YENIDEN_SAAT'ten
    # eskiyse yanar; hemen ölen bir çocuk aynı gece 5 dakikada bir yeniden doğamaz (≤1 deneme/12sa).
    yetim = bool(st.get("orphan"))
    yetim_tetik = yetim and gecen_saat is not None and gecen_saat >= YETIM_YENIDEN_SAAT
    ctx = {"gecen_gun": gun, "taze_hipotez": taze, "n_hipotez": len(hyps),
           "saat": now.hour, "pencere": list(SPRINT_HOURS), "cfg": auto_config(),
           "arama_bayragi": arama, "yetim": yetim, "yetim_saat": gecen_saat if yetim else None,
           # TETİK AYRI ALAN OLARAK TAŞINIR: `yetim` "yarıda kalmış bir sprint var"
           # der, `yetim_tetik` "ve 12 saatlik fren aşıldı, yeniden başlatılabilir" der. İkisi tek
           # bayrakla anlatılırsa skip olayından "neden hâlâ başlamadı?" sorusu cevaplanamaz.
           "yetim_tetik": yetim_tetik,
           "sid": st.get("sid")}
    if st.get("active"):
        return {**ctx, "kos": False, "sebep": "zaten_kosuyor"}
    # YÜK KAPILARI YETİM-RESTART'I BLOKLAYAMAZ, YETKİ KAPILARI BLOKLAR (bkz. MESGUL_YETKI_KAPILARI
    # üstündeki ölçüm/gerekçe). Sağlıklı sprintte davranış BİREBİR eskisi gibidir: meşgulse skip.
    if mesgul and (not yetim_tetik or mesgul in MESGUL_YETKI_KAPILARI):
        return {**ctx, "kos": False, "sebep": f"mesgul:{mesgul}"}
    if arama["mesgul"] and not yetim_tetik:
        return {**ctx, "kos": False, "sebep": "mesgul:canli_arama"}
    lo, hi = SPRINT_HOURS
    # Pencere gece yarısını AŞAR (22→06): tek bir `lo <= h < hi` karşılaştırması burada HER ZAMAN
    # False verirdi ve kadans hiç koşmazdı — sessizce.
    if not (now.hour >= lo or now.hour < hi):
        return {**ctx, "kos": False, "sebep": "saat_dilimi_disinda"}
    # TETİK: yetim yeniden-başlatma VEYA haftalık taban VEYA taze aday birikimi.
    # "Hiç koşmadı" (gun=None) da tetiktir. Yetim, saat penceresinden SONRA gelir: yarıda kalmış
    # antrenmanı gündüz yeniden başlatmak, 4 işçiyi canlı kararların makinesine sokmaktır.
    if yetim_tetik:
        return {**ctx, "kos": True, "sebep": "yetim_sprint_yeniden"}
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
    # YETİM TESPİTİ OLAYLIDIR — skip'ten ÖNCE, çünkü yetim bir sprint kapılara takılıp
    # (arama/pencere) günlerce başlatılamayabilir ve o hâl SESSİZ kalamaz (YASA 4). Episode başına
    # bir satır: sid anahtarı, aynı yetim için 300 sn'de bir tekrarını keser.
    if karar.get("yetim") and karar.get("sid") and karar["sid"] not in _YETIM_OLAYLI:
        obs.warn("sprint_yetim_tespit", sid=karar["sid"], yetim_saat=karar.get("yetim_saat"),
                 yeniden_esik_saat=YETIM_YENIDEN_SAAT,
                 detail=("sprint çocuğu ÖLÜ + faz terminal değil (yetim) — kadans, yetim başlangıç "
                         f"{YETIM_YENIDEN_SAAT:.0f} saati aştığında uygun ilk gece penceresinde "
                         "YENİDEN başlatır (sebep=yetim_sprint_yeniden); canlı arama/bar kovalaması "
                         "gibi YÜK kapıları bu tetiği artık bloklamaz (2026-08-13), yalnız yetki "
                         f"kapıları ({', '.join(sorted(MESGUL_YETKI_KAPILARI))}) bloklar; "
                         "operatör onarımı gerekmez"))
        _YETIM_OLAYLI.add(karar["sid"])
    if not karar["kos"]:
        _ab = karar.get("arama_bayragi") or {}
        obs.log("sprint_cadence_skip", sebep=karar["sebep"], gecen_gun=karar["gecen_gun"],
                taze_hipotez=karar["taze_hipotez"],
                arama_bayrak_yasi_sa=_ab.get("yas_sa"), arama_bayat=_ab.get("bayat"),
                # `yetim` ile `yetim_tetik` AYRI alanlar: birincisi "yarıda kalmış sprint var",
                # ikincisi "ve 12 sa fren aşıldı". Skip satırında ikisi de olmazsa "yetim=true ama
                # neden hâlâ başlamadı?" sorusu defterden cevaplanamaz (canlı teşhis 2026-08-13).
                yetim=karar.get("yetim") or False,
                yetim_tetik=karar.get("yetim_tetik") or False)
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
    """Antrenmanı durdur. ÜÇ KATMAN, sırayla: (1) işbirlikçi STOP dosyası, (2) koşum yoluna UYGUN
    sert durdurma, (3) durum damgası.

    (2) NEDEN YOLA BAĞLI: systemd yolunda süreç ARTIK BİZİM ÇOCUĞUMUZ DEĞİLDİR. `os.kill(pid, 15)`
    yalnız ana süreci vurur — `ProcessPoolExecutor` işçileri birimin cgroup'unda YAŞAMAYA DEVAM eder
    (Restart=no olduğu için systemd de onları toplamaz). `systemctl stop` cgroup'un tamamını indirir
    (KillMode=control-group) ve 20 sn sonra SIGKILL'i garanti eder. AYRICA pid-YENİDEN-KULLANIM
    riskini kapatır: yabancı bir süreç haline gelmiş bir pid'e sinyal göndermek, bu depoda zaten
    ölçülmüş bir sınıftır (watchdog `_sprint_liveness` pid yeniden-kullanımını ayrıca çapraz sorar).
    Birim durdurulamazsa pid yolu YEDEK olarak yine denenir — hiç durdurmamaktan iyidir, ve
    başarısızlık `sprint_systemd_durdurulamadi` ile KAYDA GEÇER."""
    st = store.read_json(STATUS_FILE, {})
    sbroot = st.get("sbroot")
    if sbroot:
        try:
            (Path(sbroot) / "state" / "STOP").write_text("1")   # cooperative flag; child checks each session
        except OSError:  # sessiz-yutma: yardımcı G/Ç yolu; çağıran yokluğu zaten yedek değerle karşılıyor ve asıl okuma hatası store katmanında bir kez uyarılıyor
            pass
    pid, yol = st.get("pid"), st.get("kosum_yolu")
    # `birim` damgası yoksa sid'den türetilir: DAMGA ÖNCESİ başlamış (damgasız) ama systemd altında
    # koşan bir sprint kalmasın diye DEĞİL — öyle bir sprint yok; damga bir gün bir yazımda düşerse
    # `stop()` yine de doğru birimi adresleyebilsin diye.
    birim = st.get("birim") or (_birim_adi(st["sid"]) if yol == "systemd" and st.get("sid") else None)
    durduruldu = False
    if yol == "systemd" and birim:
        durduruldu, sebep = _systemd_durdur(birim)
        if not durduruldu:
            from . import obs
            obs.warn("sprint_systemd_durdurulamadi", birim=birim, sebep=sebep, pid=pid,
                     detail=("systemd birimi durdurulamadı — pid'e SIGTERM ile yedek durdurmaya "
                             "düşülüyor; havuz işçileri birimin cgroup'unda kalabilir, "
                             f"operatör doğrulaması: systemctl status {birim}"))
    if pid and not durduruldu:
        try:
            os.kill(int(pid), 15)
        except (OSError, ValueError):  # sessiz-yutma: yardımcı/telemetri yolu; başarısızlığı karara girmez ve çağıran yedek değerle aynen devam eder
            pass
    store.write_json(STATUS_FILE, {**st, "phase": "stopping", "stopped_at": _now()})
    return {"stopping": True, "kosum_yolu": yol, "birim": birim}
