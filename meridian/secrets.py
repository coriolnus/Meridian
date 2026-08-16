"""secrets.py — sır erişiminin tek kapısı: env → yerel 0600 deposu → Secret Manager, ya da hiçbiri (Hard Rule 5).

NE YAPAR. `get(name)` bir sırrı SIRAYLA çözer: (1) süreç env'i, (2) yerel operatör deposu
(`state/secrets.json`, chmod 0600, gitignore'lu — pano üzerinden girilen anahtarlar buraya düşer),
(3) GCP Secret Manager (google-cloud-secret-manager + MERIDIAN_GCP_PROJECT kuruluysa). Env HER
ZAMAN kazanır: dosya, bir env değerini sessizce ezemez. Yerel depo tek operatörün yerel L0
kutusunda panodan anahtar yapıştırabilmesi içindir; VM'de anahtarların yeri Secret Manager'dır ve
dosya oraya asla kopyalanmaz. 300 sn TTL'li süreç-içi önbellek; `clear_cache()` rotasyon sonrası
anında tazeler.

DEĞİŞMEZLER. DEĞER ASLA LOGLANMAZ: hata yollarında yalnız hatanın TÜRÜ kaydedilir, içerik/anahtar
asla; `status()`/`mask()` en fazla maskeli ipucu (son 4 karakter) gösterir. Yazım BEYAZ
LİSTELİDİR: `set`/`delete` yalnız ALLOWED'daki BİLİNEN adları kabul eder — pano POST'u PATH,
MERIDIAN_MODE, otonomi bayrağı gibi keyfi bir env-değişkeni ekemez. Buradaki veri/paper
anahtarları icraya karşı ETKİSİZDİR: girilmeleri ekranları/bildirimleri açar ama canlı alım-satımı
ASLA açamaz (canlı broker yolu ayrıca iki elle-kurulan env bayrağı + otonomi seviyesiyle
kapılıdır). Dosya izni OKURKEN de denetlenir: sahibi dışına açık `secrets.json` süreç başına bir
kez uyarılır (`secrets_file_permissions`); okunamayan dosya "hiç sır yapılandırılmamış" gibi
görünmez, türüyle uyarılır (YASA 4).

OKUR/YAZAR. `state/secrets.json` (atomik yazım, 0600); env ve Secret Manager salt-okunur."""
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
    # Kod bu adı OKUYORDU (hermes._agent_call düşüş zinciri + ajan fallback_providers)
    # ama izin listesinde YOKTU — yani `secrets.set` onu reddediyor, operatör hiçbir zaman
    # ayarlayamıyordu. Sonuç: "düşüş zinciri" ömrü boyunca tek elemanlı kaldı ve olay kaydı
    # "tüm model zinciri cevapsız (tried=1)" diyordu; yedeğin YOKLUĞU, BAŞARISIZLIĞI gibi okunuyordu.
    "NOUS_FALLBACK_MODEL",      # 429'da düşülecek BAĞIMSIZ kotalı model (ör. tencent/hy3:free)
    "GEMINI_API_KEY",           # Gemini brain (AI Studio key)
    "GEMINI_OAUTH_TOKEN",       # Gemini brain via OAuth Bearer (operatörün kendi OAuth akışından)
    "GEMINI_MODEL",             # optional model id override
    "HERMES_BRAIN_ORDER",       # brain chain priority, e.g. "gemini,nous,claude"
    "ANTHROPIC_API_KEY",
    # Finviz otonom aday kaynağı. Elite CSV export için (1 haftalık trial). YOKKEN veya
    # süresi dolunca adapter public HTML'e düşer, o da olmazsa evren REPLAY_UNIVERSE'e döner — hepsi
    # dürüst bozunma (adapters/finviz.py). Yalnız evreni genişletir; karar/kapı asla Finviz'e bakmaz.
    "FINVIZ_API_KEY",
    # Massive EOD bar sağlayıcısı. TEK grouped çağrısı TÜM ABD piyasasının o günkü
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
    """Yerel operatör deposunu (`state/secrets.json`) sözlük olarak okur; dosya yoksa `{}`.
    Okurken İZNİ de denetler: sahibi dışına açıksa süreç başına BİR kez uyarır. Okunamayan dosya
    "hiç sır yok" gibi görünmez — hatanın yalnız TÜRÜ kaydedilir, içerik/anahtar ASLA loglanmaz."""
    global _PERM_WARNED
    try:
        p = _path()
        # İZİN DENETİMİ: yazarken 0600 uyguluyoruz ama OKURKEN hiç
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
        # YASA 4: dosya VARDIR ama okunamıyorsa boş sözlük dönmek "hiç sır
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
    """Atomic write with owner-only (0600) permissions. The value never touches a log.

    DAYANIKLILIK `store._atomic_write` SÖZLEŞMESİNE HİZALANDI (2026-08-16): tmp → write → fsync →
    os.replace → DİZİN fsync. `os.replace` YALNIZ yer değiştirmenin atomik olduğunu söyler,
    verinin diske indiğini SÖYLEMEZ — store'da fsync'siz hâl güç kesintisi sonrası sıfır-baytlık
    dosya bırakıyordu (o modülün başlık notu) ve burada aynı kesinti SIRLARI siler: ajan sessizce
    deterministik moda düşer ve bu, yukarıdaki `secrets_file_unreadable` notunun anlattığı tam
    sınıftır. Bu modül `store`u BİLEREK kullanmaz (0600 + telemetriye/loga hiç dokunmama), o
    yüzden dayanıklılık burada ELDE tekrarlanır — kopyalanan şey davranış, kod değil."""
    path = _path()
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=".secrets_", suffix=".tmp")
    try:
        os.write(fd, json.dumps(data, indent=0).encode("utf-8"))
        os.fsync(fd)                      # veri diske insin; replace tek başına bunu GARANTİ ETMEZ
        os.close(fd)
        os.chmod(tmp, 0o600)
        os.replace(tmp, path)
        os.chmod(path, 0o600)
        # DİZİN fsync: yeni adın (dizin girdisinin) kendisi de kalıcı olsun. Dizin açılamıyorsa
        # (ör. izin) yazım BAŞARILIDIR — bu yalnız ek bir dayanıklılık adımıdır ve onun düşmesi
        # sırrı kaydetmiş bir çağrıyı hataya çeviremez.
        try:
            dfd = os.open(str(path.parent), os.O_RDONLY)
            try:
                os.fsync(dfd)
            finally:
                os.close(dfd)
        except OSError:  # sessiz-yutma: dizin fsync'i EN İYİ ÇABA; dosya zaten yerine konmuş ve içeriği fsync'lenmiştir, bu adımın düşmesi yazımı geçersiz kılmaz (store._atomic_write ile aynı hüküm)
            pass
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:  # sessiz-yutma: en iyi çaba temizlik/kilit bırakma; hedef zaten yoksa yapacak bir şey yok ve asıl iş yolu bundan ötürü durduramaz
            pass
        raise


# ---------------- read ----------------
def _fetch(name: str) -> str | None:
    """Sırrı ÖNBELLEKSİZ çözer, sırayla: (1) süreç env'i, (2) yerel 0600 deposu,
    (3) `MERIDIAN_GCP_PROJECT` kuruluysa GCP Secret Manager. Hiçbiri veremezse None —
    env HER ZAMAN kazanır ve değer hiçbir yolda loglanmaz."""
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
    """Sır erişiminin TEK kapısı: `_fetch` sonucunu süreç-içi önbellekten (TTL 300 sn) verir.
    Yokluk da önbelleğe alınır; rotasyondan sonra `clear_cache()` anında tazeler."""
    now = time.monotonic()
    hit = _cache.get(name)
    if hit and (now - hit[0]) < TTL_SECONDS:
        return hit[1]
    val = _fetch(name)
    _cache[name] = (now, val)
    return val


def present(name: str) -> bool:
    """Bu sır AYARLI MI? (yalnız varlık/yokluk — değer çağırana hiç verilmez)."""
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
    """Sırrı yerel operatör deposundan siler; ALLOWED dışındaki her adı REDDEDER. Dosya yalnız
    gerçekten bir kayıt düştüyse yeniden yazılır (atomik, 0600) ve okuma önbelleği temizlenir."""
    if name not in ALLOWED:
        raise ValueError(f"'{name}' is not a settable secret")
    data = _read_file()
    if data.pop(name, None) is not None:
        _write_file(data)
    clear_cache()


# ---------------- status (masked only — never a full value) ----------------
def mask(value: str | None) -> str | None:
    """Değeri gösterilebilir ipucuna indirger: 8 karakterden uzunsa `••••` + SON 4 karakter,
    değilse yalnız `••••`; boş/None ise None. Tam değer hiçbir koşulda dönmez."""
    if not value:
        return None
    v = str(value)
    return "••••" + v[-4:] if len(v) > 8 else "••••"


def _source_of(name: str) -> str | None:
    """Bu sır HANGİ kaynaktan geliyor: "env" | "file" | "gcp"; hiçbiri veremiyorsa None.
    Sıra `_fetch` ile aynıdır — durum raporu gerçek çözüm sırasını yansıtsın diye."""
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
