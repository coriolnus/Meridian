"""secrets.py — Secret Manager, a local 0600 store, or nothing (Hard Rule 5). Reads a secret from,
in order:
  1) process env,
  2) a local operator store  (state/secrets.json, chmod 0600, gitignored)  ← app-entered keys land here,
  3) GCP Secret Manager      (if google-cloud-secret-manager + MERIDIAN_GCP_PROJECT set).
Env still wins, so nothing an env var sets can be silently overridden by the file. The local store
exists so the single operator can paste keys through the dashboard on a local L0 box; on the VM the
keys belong in Secret Manager (source 3) and the file is never copied there.

Never logs a value. Only the operator (source 1/2) or Secret Manager (source 3) ever holds it, and
status()/mask() only ever expose a masked hint (last 4 chars). Writes are whitelisted (ALLOWED) so a
dashboard POST can only ever set a KNOWN key name — never an arbitrary env-like variable."""
from __future__ import annotations
import json
import os
import tempfile
import time

from . import config

TTL_SECONDS = 300
_cache: dict[str, tuple[float, str | None]] = {}

# The ONLY names a write may target. A POST for anything outside this set is refused — so the
# dashboard can never be used to plant PATH, MERIDIAN_MODE, autonomy flags, etc. Data/paper keys
# here are inert to execution: storing them enables screeners/notifications but NEVER live trading
# (the live broker path is gated separately behind two hand-set env flags + autonomy_level>=1).
ALLOWED: frozenset[str] = frozenset({
    "FMP_API_KEY",              # data: FMP screeners + news (opt-in, data-only)
    "FMP_API_KEY_2",            # YEDEK FMP anahtarı: birincil 429 (kota) yeyince otomatik rotasyon — günlük kotayı ikiye katlar (adapters/fmp.py _active_keys)
    "ALPACA_PAPER_KEY",         # paper broker adapter (inert until the live flags are hand-set)
    "ALPACA_PAPER_SECRET",      # optional — some setups only expose an endpoint + key
    "ALPACA_PAPER_ENDPOINT",    # optional base URL override (default paper-api.alpaca.markets)
    "TELEGRAM_BOT_TOKEN",       # alerts
    "TELEGRAM_CHAT_ID",
    "MERIDIAN_WEBHOOK_URL",     # alerts (alternative to Telegram)
    "HERMES_API_KEY",           # the LLM brain (Anthropic)
    "NOUS_API_KEY",             # Nous Hermes brain (Nous Portal / hermes-agent OpenAI-compat endpoint)
    "NOUS_ENDPOINT",            # optional base URL override (default https://inference.nousresearch.com/v1)
    "NOUS_MODEL",               # optional model id override
    # 2026-07-22: kod bu adı OKUYORDU (hermes._agent_call düşüş zinciri + ajan fallback_providers)
    # ama izin listesinde YOKTU — yani `secrets.set` onu reddediyor, operatör hiçbir zaman
    # ayarlayamıyordu. Sonuç: "düşüş zinciri" ömrü boyunca tek elemanlı kaldı ve olay kaydı
    # "tüm model zinciri cevapsız (tried=1)" diyordu; yedeğin YOKLUĞU, BAŞARISIZLIĞI gibi okunuyordu.
    "NOUS_FALLBACK_MODEL",      # 429'da düşülecek BAĞIMSIZ kotalı model (ör. tencent/hy3:free)
    "GEMINI_API_KEY",           # Gemini brain (AI Studio key)
    "GEMINI_OAUTH_TOKEN",       # Gemini brain via OAuth Bearer (operatörün kendi OAuth akışından)
    "GEMINI_MODEL",             # optional model id override
    "HERMES_BRAIN_ORDER",       # brain chain priority, e.g. "gemini,nous,claude"
    "ANTHROPIC_API_KEY",
    # 2026-07-23: Finviz otonom aday kaynağı. Elite CSV export için (1 haftalık trial). YOKKEN veya
    # süresi dolunca adapter public HTML'e düşer, o da olmazsa evren REPLAY_UNIVERSE'e döner — hepsi
    # dürüst bozunma (adapters/finviz.py). Yalnız evreni genişletir; karar/kapı asla Finviz'e bakmaz.
    "FINVIZ_API_KEY",
    # 2026-07-29: Massive EOD bar sağlayıcısı. TEK grouped çağrısı TÜM ABD piyasasının o günkü
    # barlarını verir — bugünkü "sembol başına 1 FMP isteği" yağmurunu (250 istek = FMP günlük
    # kotasının tamamı, canlı kanıt state/fmp_usage.json) 1 isteğe indirir. YOKKEN adaptör dürüstçe
    # devre dışı ve zincir FMP→Cboe→Nasdaq ile aynen sürer (adapters/massive.py). Anahtar girilse
    # bile barları YAZMAYA ancak `--dogrula` ölçümü ayarlama ölçeği uyumunu kanıtlarsa başlar.
    "MASSIVE_API_KEY",
})

def _path():
    """Resolved at call time so a relocated state dir (tests, MERIDIAN_ROOT) is always honored."""
    return config.STATE / "secrets.json"


# ---------------- local operator store (source 2) ----------------
_PERM_WARNED = False


def _read_file() -> dict:
    global _PERM_WARNED
    try:
        p = _path()
        # İZİN DENETİMİ (denetim turu 28, 2026-07-21): yazarken 0600 uyguluyoruz ama OKURKEN hiç
        # bakmıyorduk. Dosya bir kopyalama/geri yükleme/eski sürüm yüzünden gruba ya da dünyaya
        # açıksa anahtarlar sessizce okunabilir durumda kalır ve bunu kimse söylemez. Süreç başına
        # BİR kez uyar (spam yok) — düzeltmeyi operatöre bırak, çalışmayı engelleme.
        if not _PERM_WARNED:
            mode = p.stat().st_mode & 0o777
            if mode & 0o077:
                _PERM_WARNED = True
                try:
                    from . import obs
                    obs.warn("secrets_file_permissions", mode=oct(mode),
                             detail="sır dosyası sahibi dışına açık — chmod 600 önerilir")
                except Exception:  # sessiz-yutma: kayıt kanalının kendisi düştü — ikinci bir kanal yok; kayıt denemesi çağıranı düşüremez
                    pass
        with p.open() as fh:
            data = json.load(fh)
        return data if isinstance(data, dict) else {}
    except FileNotFoundError:
        # sessiz-yutma: dosyanın HİÇ olmaması normal işletim hâlidir (operatör yerel sır deposu
        # kurmamış olabilir) — hata değil yapılandırma; burada uyarmak her çağrıda gürültü üretirdi.
        return {}
    except Exception as e:
        # YASA 4 (2026-07-21): dosya VARDIR ama okunamıyorsa boş sözlük dönmek "hiç sır
        # yapılandırılmamış" ile AYNI görünür — ajan sessizce deterministik moda düşer, hiçbir
        # sağlayıcı çağrılmaz ve kimse bunu bir hata sanmaz. Yalnız hatanın TÜRÜ kaydedilir;
        # dosya içeriği/anahtar ASLA loglanmaz.
        try:
            from . import obs
            obs.warn("secrets_file_unreadable", error=f"{type(e).__name__}")
        except Exception:
            # sessiz-yutma: kayıt kanalının kendisi düştü — ikinci kanal yok; uyarı denemesi
            # sır okumasını düşüremez.
            pass
        return {}


def _write_file(data: dict) -> None:
    """Atomic write with owner-only (0600) permissions. The value never touches a log."""
    path = _path()
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=".secrets_", suffix=".tmp")
    try:
        os.write(fd, json.dumps(data, indent=0).encode("utf-8"))
        os.close(fd)
        os.chmod(tmp, 0o600)
        os.replace(tmp, path)
        os.chmod(path, 0o600)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:  # sessiz-yutma: en iyi çaba temizlik/kilit bırakma; hedef zaten yoksa yapacak bir şey yok ve asıl iş yolu bundan ötürü durduramaz
            pass
        raise


# ---------------- read ----------------
def _fetch(name: str) -> str | None:
    v = os.environ.get(name)
    if v:
        return v
    fv = _read_file().get(name)
    if fv:
        return str(fv)
    project = os.environ.get("MERIDIAN_GCP_PROJECT")
    if project:
        try:
            from google.cloud import secretmanager  # optional dep, present only on the VM
            client = secretmanager.SecretManagerServiceClient()
            path = f"projects/{project}/secrets/{name}/versions/latest"
            resp = client.access_secret_version(request={"name": path})
            return resp.payload.data.decode("utf-8").strip()
        except Exception:  # sessiz-yutma: geç bağlanan yardımcı modül/çağrı; asıl karar bu değere bağlı değil ve çağıran yokluğu yedek değerle karşılıyor
            return None
    return None


def get(name: str) -> str | None:
    now = time.monotonic()
    hit = _cache.get(name)
    if hit and (now - hit[0]) < TTL_SECONDS:
        return hit[1]
    val = _fetch(name)
    _cache[name] = (now, val)
    return val


def present(name: str) -> bool:
    return bool(get(name))


def clear_cache() -> None:
    """Force the next get() to re-read (use right after rotating a secret)."""
    _cache.clear()


# ---------------- write (whitelisted, dashboard-facing) ----------------
def set(name: str, value: str) -> None:
    """Store a KNOWN secret in the local operator store. Refuses any name outside ALLOWED. An empty
    value clears it. Never logs the value; clears the read cache so the change is picked up at once."""
    if name not in ALLOWED:
        raise ValueError(f"'{name}' is not a settable secret")
    value = (value or "").strip()
    data = _read_file()
    if value:
        data[name] = value
    else:
        data.pop(name, None)
    _write_file(data)
    clear_cache()


def delete(name: str) -> None:
    if name not in ALLOWED:
        raise ValueError(f"'{name}' is not a settable secret")
    data = _read_file()
    if data.pop(name, None) is not None:
        _write_file(data)
    clear_cache()


# ---------------- status (masked only — never a full value) ----------------
def mask(value: str | None) -> str | None:
    if not value:
        return None
    v = str(value)
    return "••••" + v[-4:] if len(v) > 8 else "••••"


def _source_of(name: str) -> str | None:
    if os.environ.get(name):
        return "env"
    if _read_file().get(name):
        return "file"
    if os.environ.get("MERIDIAN_GCP_PROJECT") and get(name):
        return "gcp"
    return None


def status() -> dict:
    """Per-known-key: whether it is set, from which source, and a masked hint. No full values."""
    out = {}
    for name in sorted(ALLOWED):
        src = _source_of(name)
        val = _fetch(name) if src else None
        out[name] = {"set": bool(src), "source": src, "hint": mask(val)}
    return out
