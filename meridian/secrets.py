"""secrets.py — sır erişiminin tek kapısı: systemd credential → env → yerel 0600 deposu, ya da hiçbiri (Hard Rule 5).

NE YAPAR. `get(name)` bir sırrı `KAYNAKLAR` SIRASIYLA çözer: (1) systemd credential dizini
(`$CREDENTIALS_DIRECTORY/<ad>` — sır süreç ORTAMINA hiç girmez; TSK-064 Faz-1B, `credential_oku`),
(2) süreç env'i, (3) yerel operatör deposu
(`state/secrets.json`, chmod 0600, gitignore'lu — pano üzerinden girilen anahtarlar buraya düşer).
Credential kanalı env'i YENER (geçişin yönü ortamdan credential'a doğrudur; gerekçe `_fetch`te),
env de dosyayı: dosya, bir env değerini sessizce ezemez. Yerel depo tek operatörün yerel L0
kutusunda panodan anahtar yapıştırabilmesi içindir; A1'de anahtarların yeri systemd credential
kanalıdır ve dosya oraya asla kopyalanmaz. 300 sn TTL'li süreç-içi önbellek; `clear_cache()`
rotasyon sonrası anında tazeler.

DÖRDÜNCÜ BASAMAK KAPANDI (IaC-K5, operatör kararı 2026-09-07). Zincirin sonunda bir BULUT sır
deposu basamağı vardı; sistem 2026-08'de o buluttan Oracle A1'e taşındığı gün o basamak
ULAŞILAMAZ oldu ama koddan düşmedi. Bıraktığı şey ölü kod değil ölü BEYAN'dı: `status()` var
olmayan bir kanalı adıyla raporlayabiliyordu, pano onun için Türkçe karşılık taşıyordu ve
`pyproject.toml` kurulmamış bir istemciyi beyan ediyordu — yani "sır nereden geliyor" sorusunun
cevabı bir ihtimalle YANLIŞ olabiliyordu ve bu tam da TSK-064'ün farksal ölçümünün dayandığı
yüzeydi. Çivi: `tests/test_gcp_yolu_kaldirildi_v448.py`.

DEĞİŞMEZLER. DEĞER ASLA LOGLANMAZ: hata yollarında yalnız hatanın TÜRÜ kaydedilir, içerik/anahtar
asla; `status()`/`mask()` en fazla maskeli ipucu (son 4 karakter) gösterir. Yazım BEYAZ
LİSTELİDİR: `set`/`delete` yalnız ALLOWED'daki BİLİNEN adları kabul eder — pano POST'u PATH,
MERIDIAN_MODE, otonomi bayrağı gibi keyfi bir env-değişkeni ekemez. Buradaki veri/paper
anahtarları icraya karşı ETKİSİZDİR: girilmeleri ekranları/bildirimleri açar ama canlı alım-satımı
ASLA açamaz (canlı broker yolu ayrıca iki elle-kurulan env bayrağı + otonomi seviyesiyle
kapılıdır). Dosya izni OKURKEN de denetlenir: sahibi dışına açık `secrets.json` süreç başına bir
kez uyarılır (`secrets_file_permissions`); okunamayan dosya "hiç sır yapılandırılmamış" gibi
görünmez, türüyle uyarılır (YASA 4).

OKUR/YAZAR. `state/secrets.json` (atomik yazım, 0600); credential dizini ve env salt-okunur."""
from __future__ import annotations
import json
import os
import tempfile
import time

from . import config

TTL_SECONDS = 300
_cache: dict[str, tuple[float, str | None]] = {}

# ---- systemd CREDENTIAL KANALI (TSK-064 YOL-1 Faz-1B) ------------------------------------------
#: `_fetch`in ÇÖZÜM SIRASI ve `status()["source"]`ın DONUK sözlüğü — TEK kaynak. Panonun Türkçe
#: karşılık sözlüğü (`app.js`teki `SRC_TR`) bunun KOPYASIDIR; kopya sessizce ayrışmasın diye
#: ayrışma çivisi `tests/test_sir_credential_v439.py`dedir (tek-kaynak yasası).
KAYNAKLAR: tuple[str, ...] = ("credential", "env", "file")

#: systemd'nin credential dizinini bildirdiği ortam değişkeni (systemd ≥247).
CREDENTIAL_DIZIN_ENV = "CREDENTIALS_DIRECTORY"


def credential_oku(ad: str) -> str | None:
    """`$CREDENTIALS_DIRECTORY/<ad>` dosyasındaki sırrı döner; kanal ya da değer yoksa `None`.

    NEDEN BU KANAL. Bu depoda ortam ÇOCUKLARA AKAR (`serve.sh` uvicorn'u `env=os.environ` ile,
    `hermes_composite` ajan alt süreçlerini devralınan ortamla doğurur), yani `EnvironmentFile`
    ile verilen bir sır motor sürecinin VE onun doğurduğu her LLM ajan sürecinin
    `/proc/<pid>/environ`ında okunur hâlde durur — 0600'lük bir dosyada saklanan sırrı, aynı
    kullanıcı olarak koşan her alt sürecin ortamına dağıtmak kilidi takıp anahtarı kapının üstüne
    bırakmaktır. `LoadCredential=` bunu YAPISAL olarak kapatır: systemd sırrı PID 1 olarak
    (sandbox'tan ÖNCE) okur, `$CREDENTIALS_DIRECTORY` altına 0400 bir tmpfs dosyası bırakır, süreç
    bitince siler. Gerekçenin tamamı:
    `deploy/oracle-a1/meridian.service.d/53-nous-kapi-credential.conf`.

    NEDEN BURADA (ve `api._read_dash_token`ta değil). TSK-049 aynı okumayı TEK sır için pano
    tarafında yaptı; bu tur onu sır erişiminin TEK KAPISINA taşır, böylece `get` üzerinden okuyan
    HER tüketici (`hermes._nous_headers` dahil) tek satır değişmeden kazanır. Kopyalanan şey
    davranıştır, kod değil — pano okuyucusu kendi biçim toleransıyla yerinde kalır.

    KİMLİK = AD. `LoadCredential=NOUS_API_KEY:/etc/meridian/nous_api_key` yazılır; credential
    KİMLİĞİ sır ADIYLA aynıdır, kaynak DOSYA adı serbesttir. Kimlik ile ad ayrışsaydı okuyucu
    dosyayı bulamaz ve kanal sessizce ölürdü (çivi: `test_sir_credential_v439.py`).

    BİÇİM TOLERANSI, DAR. Sözleşme ÇIPLAK değerdir (`LoadCredential` dosyanın TAMAMINI taşır,
    sondaki yeni satır serbest). Operatörün `.env` alışkanlığı `AD=deger`dir ve o satırın kaynağa
    kopyalanması ÖNGÖRÜLEBİLİR bir kazadır, o yüzden YALNIZ İSTENEN adın öneki tanınır — başka bir
    adın öneki yutulmaz, çünkü o "kaynak dosyalar karışmış" demektir ve sessizce düzeltmek arızayı
    gizlerdi.

    BOŞ DEĞER `None`'DIR: boş string dönmek "ayarlı ama değersiz" demek olurdu ve `_fetch` alt
    kanallara HİÇ düşmezdi — sıfır ile "bilmiyorum" aynı şey değildir (uydurma yasağı)."""
    kdir = os.environ.get(CREDENTIAL_DIZIN_ENV)
    if not kdir:
        return None
    # AD BİR DOSYA ADIDIR, YOL DEĞİL: `../x` ya da mutlak bir yol, bu okuyucuyu credential
    # dizininin dışından keyfi dosya okuyan bir ilkele çevirirdi ve adı ÇAĞIRAN verir.
    if not ad or ad != os.path.basename(ad) or ad in (".", ".."):
        return None
    try:
        with open(os.path.join(kdir, ad), encoding="utf-8") as fh:
            ham = fh.read()
    # Kanal GERÇEKTEN zorunluyken sessiz kalmayan yer systemd'nin KENDİSİDİR: `LoadCredential=`
    # kaynak dosyası yoksa birim HİÇ başlamaz. Buradaki sessizliğin gizleyebileceği tek durum
    # "bu kurulumda credential kanalı yok"tur ve onun doğru yanıtı alt kanallara düşmektir.
    # sessiz-yutma: credential kanalı isteğe bağlı — dosya-yok/izin/kodlama hatası "bu kurulumda o kanal yok" demektir, alt kanala düşmek bugünkü davranışı birebir korur
    except (OSError, ValueError):
        return None
    # ÖNCE `strip()` SONRA ilk satır: kaynağı `printf '%s\n'` yazar; kırpılmazsa değere görünmez
    # bir `\n` yapışır ve `Authorization: Bearer <deger>\n` başlığı upstream'de 401 alır — en
    # sinsi hâl budur ("ayarlı ama çalışmıyor", arıza ağda aranır).
    satirlar = ham.strip().splitlines()
    deger = satirlar[0].strip() if satirlar else ""
    onek = f"{ad}="
    if deger.startswith(onek):
        deger = deger[len(onek):].strip()
    return deger or None


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
    # APISIX KAPI TÜKETİCİ ANAHTARI (F4-B istemci tarafı). Kapının key-auth eklentisi tüketiciyi
    # `apikey` BAŞLIĞINDAN tanır; `hermes._nous_headers` bu sır DOLUYSA o başlığı Nous'a giden
    # HTTP çağrılarına ekler (POST /chat/completions + GET /models sondası, tek kaynak).
    # YALNIZ `NOUS_ENDPOINT` kapıya çevrildiğinde anlamlıdır: sır yokken HİÇBİR başlık eklenmez ve
    # bugünkü davranış bit-eş kalır (dürüst bozunma — flip'ten önce değişiklik hareketsizdir).
    # Adı ÖNCE buraya koymak, satır 50-54'teki vakanın dersidir: kodun okuduğu ama ALLOWED'da
    # olmayan ad operatörce HİÇ ayarlanamaz. Çivi: tests/test_kapi_apikey_v370.py.
    "KAPI_APIKEY",
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
    # LİTESTREAM S3 KİMLİĞİ (2026-08-23): canlıdaki litestream birimi `state/litestream.env`i
    # drop-in ile ZATEN okuyordu (deploy/oracle-a1/meridian-litestream.service.d/10-s3-env.conf)
    # ama dosyayı üreten yol yoktu — sır zincirinin pano ucu bu iki addır. İKİSİ DE mevcutken
    # `litestream_env_sync` env dosyasını 0600 doğumla üretir; biri silinirse dosya kalkar
    # (yarım kimlik sessiz arıza olurdu). İcraya karşı ETKİSİZ: yalnız DB yedeğinin kimliği.
    "LITESTREAM_ACCESS_KEY_ID",
    "LITESTREAM_SECRET_ACCESS_KEY",
})

# ---- litestream env dosyası (birimin okuduğu tek yüzey) ----------------------------------------
LITESTREAM_ENV = "litestream.env"
LITESTREAM_PAIR = ("LITESTREAM_ACCESS_KEY_ID", "LITESTREAM_SECRET_ACCESS_KEY")


def litestream_env_sync() -> dict:
    """İki litestream anahtarı da mevcutsa `state/litestream.env`i üretir; biri eksikse kaldırır.

    Dosya 0600 İZNİYLE DOĞAR (sprint v270 deseni — `sprint._systemd_baslat`: write_text+chmod
    çifti kısa bir herkes-okur penceresi bırakır, `os.open(..., 0o600)` bırakmaz). İçerik systemd
    `EnvironmentFile` sözdizimidir; DEĞER hiçbir logda/olayda geçmez — dönen sözlük ve obs olayı
    yalnız DURUM taşır. Çağıran: api `/api/secrets/{name}` set/delete yolları (çift üyesi için)."""
    path = config.STATE / LITESTREAM_ENV
    kid, sec = get(LITESTREAM_PAIR[0]), get(LITESTREAM_PAIR[1])
    if kid and sec:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(path, os.O_CREAT | os.O_WRONLY | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w") as f:
            f.write(f"LITESTREAM_ACCESS_KEY_ID={kid}\nLITESTREAM_SECRET_ACCESS_KEY={sec}\n")
        os.chmod(path, 0o600)             # önceden var olan dosyanın izni de 0600'e çekilir
        durum = "yazildi"
    elif path.exists():
        os.unlink(path)                   # yarım kimlik dosyası BIRAKILMAZ — birim eski/eksik kimlikle koşmasın
        durum = "kaldirildi"
    else:
        durum = "yok"
    try:
        from . import obs
        obs.log("litestream_env_sync", durum=durum,
                detail="state/litestream.env " + ("üretildi (0600; iki anahtar da mevcut)"
                       if durum == "yazildi" else
                       ("kaldırıldı (çiftin bir üyesi eksik)" if durum == "kaldirildi"
                        else "yok ve üretilmedi (çift eksik)")))
    except Exception:  # sessiz-yutma: kayıt kanalının kendisi düştü — ikinci bir kanal yok; kayıt denemesi sır yazımını düşüremez
        pass
    return {"durum": durum, "path": str(path)}

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
    """Sırrı ÖNBELLEKSİZ çözer, `KAYNAKLAR` sırasıyla: (1) systemd credential dizini,
    (2) süreç env'i, (3) yerel 0600 deposu. Hiçbiri veremezse None; değer hiçbir yolda loglanmaz.

    CREDENTIAL NEDEN ÖNCE (TSK-064 Faz-1B). Geçiş İKİ FAZLIDIR ve faz-1'de iki kanal AYNI ANDA
    canlıdır (`EnvironmentFile` kalır, `LoadCredential` eklenir). Öncelik credential'da olmazsa
    faz-2'de ortam kanalı kapandığında davranış SESSİZCE değişirdi; üstelik geçişin farksal
    ölçümü (ortama SAHTE değer, credential'a gerçek değer → servis hâlâ iş yapıyor mu?) hangi
    kanalın okunduğunu ancak bu sıra sayesinde ölçebilir. Aynı hüküm pano token'ında da yürürlükte
    (`api._read_dash_token`) — orada BİR sır için verilmişti, burada tek kapıya taşındı.

    ENV ARTIK İKİNCİ, AMA DOSYAYI HÂLÂ YENER: alttaki basamakların kendi arasındaki sıra
    DEĞİŞMEDİ, yalnız önlerine bir basamak eklendi.

    ZİNCİR ÜÇ BASAMAKTA BİTER (IaC-K5, 2026-09-07). Sonda bir BULUT sır deposu basamağı vardı ve
    o basamak `except Exception` ile sarılıydı — yani istemci kurulu değilken, kimlik yokken ya
    da çağrı düşerken hepsi AYNI cevabı veriyordu: None. Üç ayrı dünya tek bir sessizliğe
    çöküyordu ve "sır ayarlı ama okunamıyor" ile "sır yok" ayırt edilemiyordu. Bulut zaten
    2026-08'de terk edilmişti; basamağı düşürmek o sessizliği de düşürür."""
    kv = credential_oku(name)
    if kv:
        return kv
    v = os.environ.get(name)
    if v:
        return v
    fv = _read_file().get(name)
    if fv:
        return str(fv)
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
    """Bu sır HANGİ kaynaktan geliyor — `KAYNAKLAR`daki adlardan biri; hiçbiri veremiyorsa None.

    SIRA `_fetch` İLE AYNIDIR ve bu bir süs değil, ölçümün kendisidir: TSK-064'ün geçiş betiği
    "uygulama hangi kanalı okuyor?" sorusunu bu yüzeyden sorar. İki sıra ayrışırsa durum raporu
    GERÇEK çözümü değil eski sırayı anlatır ve farksal ölçüm yanlış kanalı onaylar — sırrın
    ortamdan gerçekten çıktığı sanılırken çıkmamış olur (tek-kaynak yasası; çivi v439)."""
    if credential_oku(name):
        return "credential"
    if os.environ.get(name):
        return "env"
    if _read_file().get(name):
        return "file"
    return None


def status() -> dict:
    """Per-known-key: whether it is set, from which source, and a masked hint. No full values."""
    out = {}
    for name in sorted(ALLOWED):
        src = _source_of(name)
        val = _fetch(name) if src else None
        out[name] = {"set": bool(src), "source": src, "hint": mask(val)}
    return out
