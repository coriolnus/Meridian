"""adapters/fmp.py — Financial Modeling Prep (STABLE API) istemcisi: kotalı, çift-anahtarlı,
sızdırmaz tek GET kapısı üzerinden fiyat/kazanç/üyelik verisi.

(a) Ne yapar: FMP_API_KEY varken canlı adayları zenginleştirir — kote fiyat, şirket profili, kazanç
rapor tarihleri (PEAD çapası + kazanç-karartma guard'ının girdisi), tam EOD geçmişi (bar zincirinin
derin-backfill kolu) ve güncel S&P 500 üyeliği. Anahtar yoksa uydurma veri ÜRETİLMEZ: available()
False döner, çağıranlar boş/None ile dürüstçe bozunur. Stable sözleşme: taban
https://financialmodelingprep.com/stable; her istek ?apikey=<KEY> sorgu parametresi taşır; biçim
/quote?symbol=AAPL, /profile?symbol=AAPL gibi sorgu-parametreli uçlardır.
(b) Kilit girişler: quote(), profile(), earnings_dates(strict=...), historical_eod(),
sp500_constituents(), ping(which=...), available()/health()/usage()/quota_blocked(); iç kapılar
_get() (rotasyonlu) ve _get_with_key() (tek anahtar, muhasebeli).
(c) Değişmezler: available() = ANAHTAR VAR demektir, ÇALIŞIYOR demek değil (kotalı anahtar 429
yerken de True; üretim sorusunun cevabı health()). Ücretsiz katman ~250 istek/gün: birincil anahtar
429 kotasına girince YEDEK anahtara (FMP_API_KEY_2) otomatik rotasyon yapılır; kota bloğu
ANAHTAR-BAŞINA izlenir, tüm anahtarlar bloklu iken hiç istek atılmaz (boş istek ne veri getirir ne
kota geri verir). 401/403/5xx ve ağ hataları rotasyonla ÇÖZÜLMEZ, aynen fırlatılır. Anahtar sorgu
parametresinde gittiği için httpx hata metni tam URL taşır — her hata metni KAYNAĞINDA maskelenir
(_redact), anahtar asla loga/diske düşmez; istisna TÜRÜ korunur ki ping() 401'i ayırt edebilsin.
earnings_dates'te boş liste "kazanç yok" ile "istek düştü"yü ayıramaz — strict=True hatayı yutmaz.
(d) Okur/yazar: state/fmp_usage.json günlük kota muhasebesi (gün/anahtar/durum-kodu kırılımı, 429
anlarının damgalı listesi; oku-değiştir-yaz file_lock ile kilitli); başka önbellek tutmaz — bar
önbelleği adapters/data.py'nin, üyelik önbelleği adapters/constituents.py'nindir."""
from __future__ import annotations
import os
import httpx
from .. import secrets

# TABAN ADRESİ ENV'DEN (TSK-089 Faz 2, kapı yönlendirmesi): FMP trafiğini APISIX kapısına
# çevirebilmek için taban dağıtımda değiştirilebilir olmalı — kod değişikliği gerektirmeden.
# Yönlendirme OPT-IN'dir: env yokken VARSAYILAN DAVRANIŞ DEĞİŞMEZ (aynı sağlayıcı ucu).
# Sondaki `/` kırpılır çünkü tek tüketim noktası (_get_with_key) tabanı bölü + yol ile
# bitiştirir — kırpılmazsa "…/fmp//quote" gibi çift-bölü üretir (bazı kapılar ayrı yol sayar).
BASE = os.environ.get("MERIDIAN_FMP_BASE", "https://financialmodelingprep.com/stable").rstrip("/")


def available() -> bool:
    """ANAHTAR VAR demektir (birincil YA DA yedek) — ÇALIŞIYOR demek DEĞİL. Kotalı bir anahtar 429
    döndürürken de True'dur; üretim sorusunun cevabı health()."""
    return bool(_active_keys())


# Sağlık kaydı: her çağrı bunu günceller. available()=True ama sürekli 429 ise BU söyler; eskiden
# tüm hatalar `except: return []` ile yutuluyordu ve FMP'nin ölü olduğunu hiçbir yer bilmiyordu.
# `blocked_until` KALDIRILDI: yazılıyordu ama üretimde HİÇBİR yerde okunmuyordu —
# gerçek kota bloğu anahtar-başına `_KEY_BLOCKED` ile tutuluyor. Okunmayan bir alan, "kota bloğu
# izleniyor" izlenimi verip hiçbir şey yapmıyordu. `last_key`/`last_body` ise ÖLÇÜM: 418 başarısız
# çağrının sebebini (kota mı, auth mı, ağ mı) tahminle değil kayıtla cevaplamak için.
_HEALTH = {"ok": None, "calls": 0, "fails": 0, "last_status": None, "last_error": "", "at": None,
           "last_key": None, "last_body": ""}

# --------------------------------------------------------------------------------------------------
# KOTA BLOĞU SÜRESİ — SAAT SABİTİ DEĞİL, SAĞLAYICININ GÜNLÜK SIFIRLAMASI (2026-08-25, v291)
# --------------------------------------------------------------------------------------------------
# ESKİ HÂL: `QUOTA_COOLDOWN_S = 3600`. Blok BİR SAAT sürüyordu ama FMP kotası GÜNLÜKTÜR — yani blok
# her saat kendiliğinden açılıyor ve her açılışta iki anahtara birer GARANTİLİ-429 atılıyordu.
# KANIT (state/fmp_usage.json `quota_hits`, ÖLÇÜM — tahmin değil): 07-28 21:37→22:37 · 07-29
# 20:33→21:36→22:56 — hepsi tam bir saat arayla ve hepsi ÇİFT (birincil + yedek). Ölçülen kazanç
# 10-20 çağrı/gün.
#
# YENİ HÂL: blok, BİR SONRAKİ UTC GÜN DÖNÜMÜNE kadar sürer.
#
# "UTC gün dönümü" VARSAYIMI DOĞRULANMADI, GÖZLEMDEN TÜRETİLDİ — ve karşı kanıt da yazılıdır:
#   * SAĞLAYICI SÖYLEMİYOR: 429 gövdesi yalnız "Limit Reach . Please upgrade your plan..." diyor,
#     reset saati YOK (gövdenin tamamı `quota_hits[].body`de kayıtlı — okunabilir, uydurulmadı).
#   * KARŞI KANIT: defterde 2026-07-30T00:53 UTC'de HÂLÂ 429 var (o gün yalnız ~10 çağrı yapılmış,
#     yani yeniden tükenme değil). Demek ki gerçek sıfırlama UTC gün dönümünden SONRA olabilir
#     (ör. ABD-doğu gece yarısı ≈ 04:00-05:00 UTC ya da 24 saatlik kayan pencere).
#   * SONUÇ: UTC gün sonu bir ALT SINIRDIR. Saatlik sabitten kesinlikle daha doğrudur (kota günlük,
#     saatlik değil) ama "kesin sıfırlama anı" DİYE OKUNMAMALIDIR.
#   * ARTIK RİSK, AÇIKÇA: gerçek sıfırlama daha geçse ve bir tüketici gün dönümünün HEMEN ardından
#     çağrı yapsa, gelen 429 anahtarı o günün SONUNA kadar bloklar — yani bir günlük kota
#     kullanılmadan kalabilir. Bugünkü kadans bunu ISKALIYOR (gece işleri 20:00-20:20 UTC arasında,
#     blok o saatte çoktan açılmış olur), ama sıfırlama saati ÖLÇÜLENE kadar bu bir açık kalemdir.
def _blok_bitisi(now: float | None = None) -> float:
    """429 bloğunun bitiş damgası: `now`dan sonraki İLK UTC gün dönümü (epoch saniye).

    Gün dönümüne 30 saniye kala bloklanan anahtar yalnız 30 saniye bloklu kalır — sağlayıcının
    takvimi neyse odur; süreyi yapay bir tabanla uzatmak tam da kaçınılan şeyi (uydurma saat
    sabiti) geri getirirdi."""
    import datetime as _d
    import time as _t
    ts = _d.datetime.fromtimestamp(float(now if now is not None else _t.time()), _d.timezone.utc)
    ertesi = (ts.date() + _d.timedelta(days=1))
    return _d.datetime(ertesi.year, ertesi.month, ertesi.day, tzinfo=_d.timezone.utc).timestamp()

# --- YEDEK ANAHTAR ROTASYONU (operatör isteği) -----------------------------------
# Birincil FMP anahtarı günlük kotayı (ücretsiz katman ~250/gün) doldurup 429 yeyince İKİNCİ bir
# anahtara OTOMATİK geçilir. İkinci anahtar ayrı bir ücretsiz hesaptan alınır ve günlük kotayı fiilen
# İKİYE katlar — "çalışmıyor"un baskın sebebi tam da bu kota tükenmesiydi. Kota-bloğu ANAHTAR-BAŞINA
# izlenir; ikisi de bloklu olmadıkça sistem 'kota doldu' saymaz. Anahtarlar asla loglanmaz/sızmaz.
BACKUP_KEY = "FMP_API_KEY_2"
_KEY_BLOCKED: dict[str, float] = {}   # anahtar-adı -> blocked_until (epoch)


def _active_keys() -> list[tuple[str, str]]:
    """Sıralı (ad, değer): birincil önce, sonra yedek. Boş/None atlanır; AYNI değer iki kez sayılmaz
    (operatör yanlışlıkla aynısını girerse boş yere ikinci 429 çağrısı yapılmaz). Anahtar OKUMANIN
    TEK KAYNAĞI — dağılırsa sızma/sürüklenme riski ('anahtar tek yerde')."""
    out: list[tuple[str, str]] = []
    seen: set[str] = set()
    for name in ("FMP_API_KEY", BACKUP_KEY):
        v = secrets.get(name)
        if v and v not in seen:
            seen.add(v)
            out.append((name, v))
    return out


def _key_blocked(name: str) -> bool:
    """Bu FMP anahtarı şu an 429-kota bloğunda mı? `_KEY_BLOCKED`teki blocked_until damgasını
    şimdiyle karşılaştırır; kayıt yoksa False. Süreç-içi bellekte tutulur, diske yazılmaz."""
    import time as _t
    return _t.time() < float(_KEY_BLOCKED.get(name) or 0)


def _block_key(name: str) -> None:
    """Adı verilen anahtarı SAĞLAYICININ günlük sıfırlamasına kadar bloklu işaretler (429 sonrası;
    süre gerekçesi `_blok_bitisi` başlığında). Kota dolmuşken istek atmak ne veri getirir ne kotayı
    geri verir; bu işaret diğer FMP tüketicilerini korur."""
    _KEY_BLOCKED[name] = _blok_bitisi()


# --------------------------------------------------------------------------------------------------
# 402 = PLAN SINIRI (KOTA DEĞİL) → UÇ BAŞINA GÜNLÜK KAPATMA (2026-08-25, v291)
# --------------------------------------------------------------------------------------------------
# ÖLÇÜLEN VAKA: 2026-08-23'te 43 çağrının 43'ü 402 ile düştü, hepsi BİRİNCİ anahtarda
# (`by_key: {FMP_API_KEY: 43}`) — rotasyon hiç ateşlenmedi ve ateşlenmemeliydi de:
# 402 "bu uç ÜCRETSİZ PLANDA kapalı" demektir, ikinci anahtar AYNI ücretsiz plandadır, yani
# rotasyon 43 kaybı 86 yapardı. Bu hesapta gerçek KOTA sinyali 429'dur ve tam 251./502. çağrıda
# gelir (`quota_hits` defteri) — iki sinyal AYRI politikaya bağlıdır ve bu ayrım kasıtlıdır.
#
# DOĞRU DAVRANIŞ: 402 alan UCU (path) o gün için kapat. Kapatma ANAHTAR başına DEĞİL uç başına;
# aksi hâlde ücretsiz planda ÇALIŞAN uçlar (ör. `insider-trading/latest` — Y3, günde 1 çağrı,
# vazgeçilmez) kapalı bir kardeş uç yüzünden susturulurdu. Desen `adapters/insider.py`nin 402
# dalından alındı ("sembol sembol denemek 250 boş istek atmak olurdu"); oradaki dal tek TURU
# kesiyordu, buradaki kapatma GÜN boyunca yaşar ve TÜM tüketicileri korur.
#
# BİLİNÇLİ KABA-TANE: kapatma UCUN TAMAMINI kapsar, istek BİÇİMİNİ değil. `quote` ucu tekil
# sembolle 200, virgüllü çoklu listeyle 402 döner (bkz. `quote` docstring'i); çoklu bir çağrı
# 402 yerse tekil yol da o gün kapanır. Üretimde çoklu yol tüketilmiyor, o yüzden bugün maliyeti
# yok — ama açılırsa burası ince-taneleştirilmeli.
_PATH_BLOCKED: dict[str, float] = {}   # uç (path) -> blocked_until (epoch)


def _norm_path(path: str) -> str:
    """Uç adının kanonik hâli — blok anahtarı bununla tutulur ki '/quote' ile 'quote' AYNI uç sayılsın."""
    return str(path or "").lstrip("/")


def _path_blocked(path: str) -> bool:
    """Bu uç 402 yüzünden şu an kapalı mı? Kayıt yoksa False; damga geçmişse blok kendiliğinden düşer."""
    import time as _t
    return _t.time() < float(_PATH_BLOCKED.get(_norm_path(path)) or 0)


def _block_path(path: str) -> None:
    """Ucu sağlayıcının günlük sıfırlamasına kadar kapatır (402 sonrası). Süre gerekçesi
    `_blok_bitisi` başlığında: plan sınırı da kota gibi GÜNLÜK bir olgudur ve saatlik yeniden
    deneme her açılışta garantili-402 üretirdi."""
    _PATH_BLOCKED[_norm_path(path)] = _blok_bitisi()


def blocked_paths() -> list[str]:
    """ŞU AN 402 ile kapalı uçların adları (sıralı). Muhasebenin görünen yüzü: 'istek neden
    atılmadı' sorusu tahminle değil kayıtla cevaplanır. Süresi dolmuş kayıtlar listelenmez."""
    return sorted(p for p in _PATH_BLOCKED if _path_blocked(p))


def health() -> dict:
    """FMP HTTP yolunun son durumunun kopyası (ok, çağrı/hata sayaçları, son HTTP kodu, son hata,
    son kullanılan anahtar adı ve damga). Anahtarın VARLIĞINI değil, çağrının sonucunu bildirir.

    KAPALI UÇLAR BURADA DEĞİL, `blocked_paths()`tedir: bu sözlük "son ÇAĞRININ sonucu"nu anlatır ve
    şeması dışarıda çivili (tests/test_review_backlog_v98). Atılmamış bir isteğin durumu bir çağrı
    sonucu değildir; ikisini aynı sözlüğe koymak her iki okuyucuyu da yanıltırdı."""
    return dict(_HEALTH)


USAGE_FILE = "fmp_usage.json"       # {date, calls, fails, blocked_at, atlanan} — günlük kota muhasebesi


def _gun_defteri(u: dict, today: str) -> dict:
    """Günlük defterin o güne ait hâli: gün DÖNDÜYSE sayaçlar sıfırlanır ama `quota_hits` TAŞINIR.

    O defterin tek amacı sağlayıcının kota RESET SAATİNİ ölçmek; ölçüm ancak gün SINIRINI aşan bir
    pencerede yapılabilir — her gece silmek, tam da ölçülmek istenen olguyu siliyordu. Yardımcı
    olarak ayrıldı çünkü artık İKİ yazar var (çağrı muhasebesi + atlanan-istek muhasebesi) ve gün
    dönümü kuralının iki kopyası sessizce ayrışırdı."""
    if u.get("date") == today:
        return u
    return {"date": today, "calls": 0, "fails": 0, "blocked_at": None,
            "quota_hits": list(u.get("quota_hits") or [])[-20:]}


def _usage_atlandi(path: str) -> None:
    """ATILMAYAN istek de bir olgudur: 402 ile kapalı bir uç yüzünden atlanan çağrı `atlanan` ve
    `atlanan_by_path` altında AYRI sayılır.

    `calls`a EKLENMEZ: atılmamış istek bir çağrı değildir ve onu çağrı saymak, defterin tek işini
    ('kota neden bitti' sorusunu kayıtla cevaplamak) bozardı. Sessizce hiç saymamak ise bu deponun
    yasağı — 'istek atılmadı' kararının kaç kez verildiği görünmeden kalırdı."""
    try:
        from .. import store
        import datetime as _d
        today = _d.date.today().isoformat()
        with store.file_lock(USAGE_FILE):
            u = _gun_defteri(store.read_json(USAGE_FILE, {}) or {}, today)
            u["atlanan"] = int(u.get("atlanan", 0)) + 1
            _p = _norm_path(path) or "?"
            u.setdefault("atlanan_by_path", {})[_p] = int((u.get("atlanan_by_path") or {}).get(_p, 0)) + 1
            store.write_json(USAGE_FILE, u)
    except Exception:  # sessiz-yutma: geç bağlanan yardımcı modül/çağrı; asıl karar bu değere bağlı değil ve çağıran yokluğu yedek değerle karşılıyor
        pass


def _usage(ok: bool, *, status: int | None, key_name: str, error: str = "", body: str = "") -> None:
    """Günlük çağrı sayacı: ücretsiz katman ~250/gün ve 250 ticker'lık BİR bar
    tazelemesi bunun tamamını yakıyor. Sayaç olmadan 'kota neden bitti' sorusu tahminle cevaplanıyordu.

    HER OLGU PARAMETRE OLARAK GELİR, `_HEALTH`TEN OKUNMAZ. Eskiden durum/anahtar adı
    modül-globalinden geri okunuyordu ve bu iki yoldan birden yanlış atıf üretiyordu:
      * BAYAT ATIF — `ping()` `_HEALTH["last_key"]`i hiç yazmıyordu; yedek anahtarın testi, bir
        ÖNCEKİ çağrının anahtar adıyla `by_key`e işleniyordu.
      * THREAD YARIŞI — `_HEALTH` tek ve paylaşılan; iki iş parçacığı (zamanlayıcı + ajan) aynı anda
        çağırdığında biri diğerinin durumunu okuyup kendi satırını onun adına yazıyordu.
    İkisi de sessizdi: sayılar tutuyordu, KİME ait olduğu yanlıştı — ve teşhis o dağılımdan çıkıyor.

    GÖVDE KİLİTLİDİR: oku-değiştir-yaz idi ama `read_json` ile `write_json` AYRI kilit
    bölümleriydi — aradaki pencerede ikinci bir iş parçacığı (zamanlayıcı vs. API `ping`) aynı belgeyi
    okuyup kendi artırımını yazınca birinci çağrı SAYILMAMIŞ oluyordu. Kota muhasebesinin eksik
    sayması, tam da 'kota neden bitti' sorusunu cevaplayamamak demektir. `store.file_lock` bir RLock
    döndürür: AYNI SÜREÇTEKİ iplikler için yeterlidir; süreçler-arası koruma İDDİA EDİLMEZ (ayrı bir
    süreç bu defteri yazsaydı kayıp yine mümkündü — bugün yazan tek süreç var)."""
    try:
        from .. import store
        import datetime as _d
        today = _d.date.today().isoformat()
        with store.file_lock(USAGE_FILE):
            # GÜN DÖNÜMÜ KURALI TEK YERDE: `_gun_defteri` (sayaçlar sıfırlanır, `quota_hits` taşınır).
            u = _gun_defteri(store.read_json(USAGE_FILE, {}) or {}, today)
            u["calls"] = int(u.get("calls", 0)) + 1
            # SEBEP DAĞILIMI: "510 çağrı / 418 başarısız" tek başına kota mı, auth mı,
            # ağ mı olduğunu söylemiyordu — ve yanlış teşhis yanlış politikayı doğurur (bir
            # çağrı-sayısı bütçesi, sorun ConnectError ise TAMAMEN yanlış araçtır). Yanıt
            # ALINMADIYSA anahtar istisna SINIF ADIdır, "None" değil: "yanıt gelmedi" ile "yanıt
            # 200 değildi" ayrı şeyler.
            _lbl = str(status) if status is not None else (error or "?").split(":")[0]
            u.setdefault("by_status", {})[_lbl] = int((u.get("by_status") or {}).get(_lbl, 0)) + 1
            _k = key_name or "?"
            u.setdefault("by_key", {})[_k] = int((u.get("by_key") or {}).get(_k, 0)) + 1
            if not ok:
                u["fails"] = int(u.get("fails", 0)) + 1
                if status == 429:
                    if not u.get("blocked_at"):
                        u["blocked_at"] = u["calls"]
                    # 429'un GERÇEK saati ve GERÇEK gövdesi — sağlayıcının reset saatini ÖLÇMEK
                    # için. Son 20 ile sınırlı: defter büyümesin, ama desen görünsün.
                    import datetime as _dt2
                    u.setdefault("quota_hits", []).append(
                        {"at": _dt2.datetime.now(_dt2.timezone.utc).isoformat(timespec="seconds"),
                         "key": _k, "calls_today": u["calls"], "body": (body or "")[:200]})
                    u["quota_hits"] = u["quota_hits"][-20:]
            store.write_json(USAGE_FILE, u)
    except Exception:  # sessiz-yutma: geç bağlanan yardımcı modül/çağrı; asıl karar bu değere bağlı değil ve çağıran yokluğu yedek değerle karşılıyor
        pass


def usage() -> dict:
    """Diskteki günlük kota muhasebesini (state/fmp_usage.json: {date, calls, fails, blocked_at})
    okur. Dosya yoksa/okunamazsa boş sözlük — pano bunu "muhasebe yok" olarak gösterir."""
    try:
        from .. import store
        return store.read_json(USAGE_FILE, {}) or {}
    except Exception:  # sessiz-yutma: geç bağlanan yardımcı modül/çağrı; asıl karar bu değere bağlı değil ve çağıran yokluğu yedek değerle karşılıyor
        return {}


def quota_blocked() -> bool:
    """TÜM FMP anahtarları 429 kotasında mı? Yedek anahtar açıksa False — toplu tüketici (250 ticker'lık
    bar tazelemesi) onunla ilerler; yedek günlük kotayı ikiye katlar. Tek anahtar varsa eski davranış:
    o bloklu ise True. Kota dolmuşken istek atmak ne veri getirir ne kotayı geri verir; yalnız diğer
    FMP tüketicilerini (kazanç, temel veri) aç bırakır."""
    keys = _active_keys()
    return bool(keys) and all(_key_blocked(name) for name, _ in keys)


def _redact(msg: str) -> str:
    """apikey sorgu parametresi olarak gider; httpx'in hata metni TAM URL'i taşır. Bu metin bir gün
    loglanırsa anahtar diske düşer — TÜM aktif anahtarları (birincil + yedek) kaynağında maskele."""
    out = str(msg)
    for _, key in _active_keys():
        if key:
            out = out.replace(key, "***")
    return out


def _get(path: str, params: dict | None = None, timeout: float = 20.0):
    """Sıradaki AÇIK anahtarla GET; birincil 429 (kota) yeyince YEDEK anahtara ROTASYON. Anahtar çağırana
    asla sızmaz (yalnız _get_with_key ekler; hata metni maskelenir). 401/403/5xx rotasyonla çözülmez.

    402 (plan sınırı) ROTASYONLA DA ÇÖZÜLMEZ ve tekrar denemeyle de: uç o gün için kapatılır
    (gerekçe `_PATH_BLOCKED` başlığında) ve sonraki çağrılar ağa ÇIKMADAN dürüst bir gerekçeyle
    düşer. `ping()` bu kapıdan geçmez — teşhis aracı kapalı uçta bile gerçek isteği atmalıdır."""
    keys = _active_keys()
    if not keys:
        raise RuntimeError("FMP_API_KEY absent — FMP calls disabled")
    if _path_blocked(path):
        # KAPALI UÇ: istek ATILMAZ. Atılsaydı garantili bir 402 daha yerdik — ne veri gelir ne
        # plan açılır; yalnız `fails` şişer (canlı defterde 43/43 tam olarak böyle yandı).
        _usage_atlandi(path)
        raise RuntimeError(f"FMP: '{_norm_path(path)}' ucu ücretsiz planda KAPALI (HTTP 402) — "
                           f"bugünlük istek atılmadı")
    last_exc: Exception | None = None
    for name, key in keys:
        if _key_blocked(name):
            continue                       # bu anahtar kota-bloklu — yedeğe geç, boş istek atma
        try:
            # Anahtar ADI çağrının KENDİSİYLE taşınır (değer asla loglanmaz). Modül-globaline
            # yazıp orada geri okumak, iki iş parçacığı arasında atfı sessizce takas ediyordu.
            return _get_with_key(path, params, timeout, key, key_name=name)
        except httpx.HTTPStatusError as e:
            last_exc = e
            # 429'u _HEALTH["last_status"]'tan oku (yanıt gövdesinden değil): _get_with_key onu GERÇEK
            # yanıt kodundan set eder; bazı çağrılar/mock'lar HTTPStatusError'ı response=None ile atar.
            if _HEALTH.get("last_status") == 429:
                _block_key(name)           # bu anahtarı kota-bloğuna al...
                if any(n != name and not _key_blocked(n) for n, _ in keys):
                    try:
                        from .. import obs
                        obs.log("fmp_key_rotated", key_slot=name, reason="429_quota",
                                detail="birincil FMP kotası doldu — yedek anahtara geçildi")
                    except Exception:  # sessiz-yutma: kayıt kanalı düştü; rotasyonun kendisi kararı düşürmez
                        pass
                continue                   # ...ve YEDEK anahtara rotasyon
            if _HEALTH.get("last_status") == 402:
                # PLAN SINIRI: ne rotasyon (yedek AYNI planda) ne tekrar deneme (plan gün içinde
                # açılmaz) çözer. Ucu kapat, sebebi kayda geç, hatayı AYNEN fırlat — çağıranın
                # bugünkü davranışı (yutup boş dönmek) değişmesin.
                _block_path(path)
                try:
                    from .. import obs
                    obs.warn("fmp_path_closed", path=_norm_path(path), status=402,
                             key_slot=name, blocked_paths=",".join(blocked_paths()),
                             detail="uç ücretsiz planda kapalı (HTTP 402) — bugünlük istek "
                                    "atılmayacak; rotasyon UYGULANMADI çünkü yedek anahtar da "
                                    "aynı ücretsiz plandadır (43 kayıp 86 olurdu)")
                except Exception:  # sessiz-yutma: kayıt kanalı düştü; kapatmanın kendisi kararı düşürmez
                    pass
            raise                          # 401/403/5xx: rotasyon çözmez
        except Exception as e:
            last_exc = e
            raise                          # ağ hatası: kota değil; yedek de aynı ağda, rotasyon anlamsız
    # buraya gelindi: ya tüm anahtarlar önceden bloklu ya da hepsi 429 verdi
    if last_exc is not None:
        raise last_exc
    # HEPSİ ÖN-BLOKLU: eskiden birincil anahtarla YİNE DE bir istek atılıyordu. Kota dolmuşken atılan
    # istek ne veri getirir ne kotayı geri verir — yalnız `fails` sayacını şişirir ve bloğun kendi
    # amacını (boş istek atmamak) çiğner. Canlı defterde 510 çağrının 418'i başarısızdı; bu yol o
    # sayının bir kısmını kendi eliyle üretiyordu. Artık istek ATILMAZ ve sebep açıkça söylenir.
    raise RuntimeError("FMP: tüm anahtarlar kota-bloklu — istek atılmadı")


def _get_with_key(path: str, params: dict | None, timeout: float, key: str, key_name: str = "?"):
    """TEK anahtarla ham GET + sağlık/kota muhasebesi + maskeleme. Rotasyon _get()'te; burada tek deneme.

    `key_name` MUHASEBENİN ÖZNESİDİR: hangi anahtar konuştu. Çağrı boyunca YEREL taşınır ve
    `_usage`a parametre geçer — modül-globali üzerinden dolaşsaydı eşzamanlı iki çağrı birbirinin
    adına yazardı ve `ping()` gibi rotasyonsuz yollar hiç ad yazmadığı için bayat atıf üretirdi."""
    import datetime as _dt
    q = dict(params or {})
    q["apikey"] = key
    _HEALTH["calls"] += 1
    _HEALTH["at"] = _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")
    _HEALTH["last_key"] = key_name     # pano/health() için; muhasebe artık BUNU okumaz
    _HEALTH["last_status"] = None      # ÖNCEKİ çağrının durumu bu çağrıya sızmasın: bağlantı hatası
                                       # (yanıt yok) eski bir 429'u miras alıp sahte kota-bloğu kurardı
    status, body = None, ""
    try:
        r = httpx.get(f"{BASE}/{path.lstrip('/')}", params=q, timeout=timeout)
        status = r.status_code
        _HEALTH["last_status"] = status
        # GÖVDEYİ YALNIZCA KAYDET, ÜZERİNDE DAL AÇMA. Sağlayıcının 429 gövdesi kotanın
        # ne zaman sıfırlandığını çoğu zaman yazar; onu okumadan "bütçe" kurmak varsayım eklemek
        # olurdu. `getattr` zorunlu: testlerdeki sahte yanıt nesnelerinde `.text` yok.
        body = _redact(getattr(r, "text", "") or "")[:200]
        _HEALTH["last_body"] = body
        r.raise_for_status()
        _HEALTH.update({"ok": True, "last_error": ""})
        _usage(True, status=status, key_name=key_name, body=body)
        return r.json()
    except Exception as e:
        _HEALTH["fails"] += 1
        _err = _redact(f"{type(e).__name__}: {e}")[:200]
        _HEALTH.update({"ok": False, "last_error": _err})
        _usage(False, status=status, key_name=key_name, error=_err, body=body)
        # MASKELİ yeniden fırlat: bir çağıran str(e) loglarsa ham URL (dolayısıyla anahtar) diske
        # düşmesin. TÜR KORUNUR — ping() HTTPStatusError.response.status_code'a bakıp 401'i "anahtar
        # geçersiz" diye çeviriyor; türü RuntimeError'a çevirmek o teşhisi bozuyordu.
        try:
            e.args = tuple(_redact(str(a)) for a in e.args)
        except Exception:  # sessiz-yutma: yardımcı/telemetri yolu; başarısızlığı karara girmez ve çağıran yedek değerle aynen devam eder
            pass
        raise


# ---- data endpoints (stable) ----
def quote(symbols: list[str]) -> list[dict]:
    """Real-time quote(s). Stable: /quote?symbol=AAPL (comma-join for a batch).

    ÇOKLU-SEMBOL — CANLI DOĞRULANDI (2026-07-23, taze yedek anahtarla): ücretsiz katmanda TEKİL
    /quote?symbol=AAPL çalışır (200) ama çoklu virgül-liste /quote?symbol=A,B,C ve /batch-quote?symbols=
    İKİSİ DE **HTTP 402 "Payment Required"** döndürür (ücretli özellik). Kritik olan: 402 GÜRÜLTÜLÜ bir
    hata — FMP sessizce ilk sembolü döndürüp gerisini DÜŞÜRMÜYOR, yani Finviz'deki sessiz-sürüklenme
    sınıfı BURADA YOK ve aşağıdaki `except` bunu yakalayıp [] döndürüyor (graceful). batch-quote'a
    geçmek de fayda etmez (o da 402). Üretimde çoklu yol zaten tüketilmiyor. Sonuç: kod değişikliği
    GEREKMEZ; ücretli plana geçilirse çoklu yol açılır."""
    if not available() or not symbols:
        return []
    try:
        return _get("quote", {"symbol": ",".join(symbols[:50])})
    except Exception:  # sessiz-yutma: ağ/sağlayıcı hatası bu yolun NORMAL hâli; çağıran boş sonuç üzerinden yedek kaynağa düşer ve kaynak seçimi ayrıca kaydedilir
        return []


def profile(symbol: str) -> dict | None:
    """Sembolün FMP şirket profili (stable: profile?symbol=X) — tek kayıtlık sözlük.
    Anahtar yoksa, sembol boşsa veya çağrı başarısızsa None (hata yutulur, sağlık kaydına yazılır)."""
    if not available() or not symbol:
        return None
    try:
        rows = _get("profile", {"symbol": symbol})
        return rows[0] if isinstance(rows, list) and rows else (rows or None)
    except Exception:  # sessiz-yutma: ağ/sağlayıcı hatası bu yolun NORMAL hâli; çağıran boş sonuç üzerinden yedek kaynağa düşer ve kaynak seçimi ayrıca kaydedilir
        return None


def earnings_dates(symbol: str, strict: bool = False) -> list[str]:
    """Sembolün kazanç RAPOR tarihleri (ISO, geçmiş+yakın gelecek). Stable: earnings?symbol=X.
    PEAD çapası + kazanç-karartma guard'ı bunu tüketir. Hata/anahtarsızlıkta boş liste.

    strict=True → HATA YUTULMAZ. Sebep: boş liste "bu şirket kazanç
    açıklamıyor" ile "istek başarısız" arasında ayrım yapmıyordu; kotanın pas ortasında bitmesi
    (bugün olduğu gibi) YARIM bir kazanç takvimi üretiyor, karartma guard'ı da veri yokken
    FAIL-OPEN olduğundan o isimlerde kazanç günü işlem açılıyordu."""
    if not available():
        return []
    try:
        data = _get("earnings", {"symbol": symbol})
        out = []
        for row in (data if isinstance(data, list) else []):
            d = str(row.get("date") or row.get("epsDate") or "")[:10]
            try:
                import datetime as _dt
                _dt.date.fromisoformat(d)
                out.append(d)
            except ValueError:  # sessiz-yutma: sağlayıcının biçimsiz TEK tarih alanı; yalnız o tarih düşer, satır başına uyarı 250 ticker'lık turda log seli olurdu
                continue
        return sorted(set(out))
    except Exception:
        if strict:
            raise
        return []


def historical_eod(symbol: str) -> list[dict]:
    """Full EOD OHLCV history. Stable: /historical-price-eod/full?symbol=AAPL."""
    if not available() or not symbol:
        return []
    try:
        data = _get("historical-price-eod/full", {"symbol": symbol})
        return data if isinstance(data, list) else data.get("historical", []) if isinstance(data, dict) else []
    except Exception:  # sessiz-yutma: ağ/sağlayıcı hatası bu yolun NORMAL hâli; çağıran boş sonuç üzerinden yedek kaynağa düşer ve kaynak seçimi ayrıca kaydedilir
        return []


# ÇIKARILDI 2026-07-30 (temizlik turu): `income_statement`, `search_name`, `stock_list` — üçü de
# `_get` üzerine ince sarmalayıcıydı ve ÜÇÜNÜN DE ÜRETİM ÇAĞIRANI YOKTU.
# ÇAĞIRAN TARAMASI (meridian/ + tests/ + ops/ + deploy/): tek eşleşme tanımların kendisiydi;
# `skills/` altındaki isim benzeri eşleşmeler AYRI betiklerin kendi FMP istemcileridir
# (skills/_emekli/.../screen_dividend_stocks.py gibi), bu modülü içe aktarmazlar.
# NEDEN SİLİNDİ, "belki lazım olur" DEĞİL: her biri FMP kotasından ücret yakabilecek bir ağ yolu
# açıyordu ve hiçbiri bir karara bağlı değildi — kotanın tamamı bugün bar zinciri + kazanç takvimi
# + insider akışı tarafından bütçelenmiş durumda (bkz. fmp.usage / adapters/insider.py başlığı).
# GERİ-AL: üçü de `_get(path, params)` çağıran üç satırlık gövdelerdi —
#   income_statement → _get("income-statement", {"symbol": symbol})
#   search_name      → _get("search-name", {"query": query})
#   stock_list       → _get("stock-list")
# aynı `if not available(): return []` + `except: return []` kalıbıyla (yukarıdaki
# `historical_eod` birebir aynı desendedir, şablon olarak o kullanılabilir).


def sp500_constituents() -> list[str]:
    """Current S&P 500 membership (survivorship-biased; use only for a live universe, not backtests)."""
    if not available():
        return []
    try:
        data = _get("sp500-constituent")
        return [row["symbol"] for row in data if isinstance(row, dict) and "symbol" in row]
    except Exception:  # sessiz-yutma: ağ/sağlayıcı hatası bu yolun NORMAL hâli; çağıran boş sonuç üzerinden yedek kaynağa düşer ve kaynak seçimi ayrıca kaydedilir
        return []


# ---- connectivity self-test (for the dashboard "Test" button) — never returns the key ----
def ping(which: str = "FMP_API_KEY") -> dict:
    """Live reachability + auth check for a SPECIFIC key. which=FMP_API_KEY (varsayılan) birincilyi,
    which=FMP_API_KEY_2 YEDEK anahtarı test eder — Ayarlar'daki iki ayrı 'Test et' düğmesi. Rotasyon YOK:
    hangi anahtarı doğruladığımızı bilelim. Returns NO secret — only {ok, detail}. HTTP 401/403 => wrong key."""
    key = secrets.get(which)
    label = "Yedek FMP" if which == BACKUP_KEY else "FMP"
    if not key:
        return {"ok": False, "detail": f"{label} anahtarı girilmemiş"}
    try:
        # `which` ZATEN anahtarın adıdır — muhasebeye o geçer. Eskiden hiç ad geçilmediği için
        # yedek anahtarın testi, bir ÖNCEKİ çağrının adıyla `by_key`e işleniyordu (bayat atıf).
        rows = _get_with_key("quote", {"symbol": "AAPL"}, 12.0, key, key_name=which)
        if isinstance(rows, list) and rows and "price" in rows[0]:
            return {"ok": True, "detail": f"bağlandı · AAPL ${rows[0].get('price')}"}
        if isinstance(rows, dict) and rows.get("Error Message"):
            return {"ok": False, "detail": "anahtar reddedildi (Error Message)"}
        return {"ok": False, "detail": "beklenmedik yanıt (anahtar geçersiz olabilir)"}
    except httpx.HTTPStatusError as e:
        code = e.response.status_code
        why = "anahtar geçersiz/yetkisiz" if code in (401, 403) else f"HTTP {code}"
        return {"ok": False, "detail": why}
    except Exception as e:
        return {"ok": False, "detail": f"bağlanılamadı ({type(e).__name__})"}


def status() -> dict:
    """Panoya tek satırlık sağlayıcı durumu: FMP anahtarı yapılandırılmış mı ve değilse kullanıcıya
    gösterilecek neden. Ağa GİTMEZ — canlı erişim testi için ping() kullanılır."""
    return {"provider": "FMP", "available": available(),
            "reason": "" if available() else "FMP_API_KEY yok — Ayarlar'dan ekleyin"}
