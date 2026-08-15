"""auth.py — operatör kimliği: scrypt parola doğrulama + HMAC-imzalı, kayan-pencereli oturum çerezi.

NEDEN VAR. Pano bir dönem YALNIZ `--host 127.0.0.1` bağlanmasıyla korunuyordu; token hiçbir yerde
ayarlı olmadığı için `api._auth` onlarca uçta çağrılıyor ama hepsinde anında dönüyordu — fiilen
kimlik doğrulaması yoktu. Genel bir IP'ye çıkıldığı an bu, HALT/DEVAM/Flatten/mutasyon tetikleyen
bir yüzeyin yetkisiz açılması demekti.

TASARIM KARARLARI. (1) Parola diskte asla düz durmaz: `hashlib.scrypt` (stdlib; RFC 7914
etkileşimli-giriş profili n=2^15, r=8, p=1) ile tuzlanmış türetme; doğrulama `hmac.compare_digest`
ile sabit zamanlı — `!=` ilk uyumsuz baytta kısa devre yapar ve hash'i bayt bayt kurtarmaya izin
verir (CWE-208). (2) Oturum ÇEREZDE, localStorage'da DEĞİL: localStorage JS'e açıktır, tek XSS
kalıcı erişim demekti; HttpOnly + SameSite=Strict (CSRF, tek-POST'luk HALT/Flatten uçları için
teorik kaygı değildir). (3) Oturum durumsuz ve İMZALI: v2 jetonu `<exp>.<iat>.<nonce>.<imza>` —
sunucuda oturum tablosu yok, yeniden başlatma oturum düşürmez; imza anahtarı diskte (0600),
`rotate_key()` hepsini düşürür. Eski v1 jetonu yalnız DOĞRULANIR, yenilenmez: `iat` taşımaz ve
tavanı geriye hesaplamak UYDURMA olurdu. (4) URL'de token YOK: URL'ler sunucu loglarına, tarayıcı
geçmişine ve Referer'a düşer. (5) Kaba kuvvet IP başına kayan pencereyle sınırlanır; sayaç
süreç-içidir (tek süreçli dağıtımda yeterli — başka iddia yok).

KAYAN OTURUM. Sabit pencere, kesintisiz kullanılan panoyu saat dolunca kapıya çarpıyordu ("arayüz
kayboluyor" arızası oturumun kendisiydi); sınırsız kayma ise çalınmış çerezi ölümsüz yapardı.
`refresh_session` yarı-ömürden sonra uzatır ama `iat + SESSION_ABSOLUTE_MAX_S` MUTLAK TAVANINI
asla aşamaz — tavana varan oturum kullanılıyor olsa bile düşer.

GİRİŞLER: `set_password`/`verify_password`/`password_set`, `issue_session`/`verify_session`/
`refresh_session`, `rotate_key`, `locked_out`/`note_failure`/`note_success`/`retry_after_s`,
`note_session_drop` (düşüş olayı sel kapısı). Okur/yazar: yalnız `state/auth.json` — yazım
store tek kapısından geçer ve 0600 izni AÇIKÇA doğrulanır; hiçbir sır/parola loglanmaz.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets as _secrets
import time
from pathlib import Path

from . import config

# scrypt — RFC 7914 etkileşimli profil. n'i büyütmek güvenliği artırır ama giriş gecikmesini de
# artırır; 2^15 tipik bir dizüstünde ~100 ms sürer ve tek operatörlü bir panoda kabul edilebilir.
_SCRYPT = {"n": 2 ** 15, "r": 8, "p": 1, "dklen": 32}
_MAXMEM = 64 * 1024 * 1024          # n*r*128*2 üstü; varsayılan 32 MB sınırı 2^15'te YETMEZ

SESSION_TTL_S = 12 * 3600           # bir çalışma günü; sonrasında yeniden giriş
COOKIE_NAME = "meridian_session"

# ---- KAYAN OTURUMUN MUTLAK TAVANI (2026-08-14, operatör arızası: "arayüz bir süre sonra kayboluyor")
# ARIZA NEYDİ: `SESSION_TTL_S` SABİT bir pencereydi ve çerezi tazeleyen HİÇBİR yol yoktu — çerez
# yalnız girişte ve ilk-parola-kurulumunda yazılıyordu. Pano 12 saat KESİNTİSİZ kullanılsa bile
# saat dolduğu an `_auth` 401 verir, pano kapağı açar; çerez ORTAK olduğu için bütün sekmeler AYNI
# ANDA düşer. Yani "arayüz kayboluyor" bir çizim hatası değil, oturumun kendisiydi.
#
# DÜZELTME KAYAN PENCEREDİR ama kayma SINIRSIZ OLAMAZ: çalınmış bir çerez, kullanıldıkça kendini
# yenileyerek sonsuza kadar yaşardı — parolayı değiştirmek de onu düşürmez (`set_password` imza
# anahtarını bilerek korur). Bu yüzden jeton VERİLİŞ ZAMANINI (`iat`) taşır ve yenileme
# `iat + SESSION_ABSOLUTE_MAX_S`i AŞAMAZ. Tavana varan oturum, kullanılıyor olsa bile düşer ve
# operatör yeniden girer.
#
# 7 GÜN NEDEN: tavan iki maliyetin arasında seçilir — kısa tavan operatörü sık sık kapıya çarpar
# (düzeltmeye çalıştığımız arızanın seyreltilmiş hâli), uzun tavan çalınmış çerezin ömrüdür. Bir
# hafta, "operatör pazartesi bıraktığı panoyu cuma açtığında hâlâ içeride" ile "sızan bir çerez en
# fazla bir hafta yaşar" arasındaki dengedir. SAYI BURADA, TEK YERDE ve gerekçesiyle durur.
SESSION_ABSOLUTE_MAX_S = 7 * 86400

# ---- OTURUM DÜŞÜŞÜ RAPOR ARALIĞI ------------------------------------------------------------
# Düşüş olayı `api._auth`ta, çerez GELMİŞ ama doğrulanamamışken basılır. Pano 15 saniyede bir
# yokluyor ve `rotate_key()` sonrası tarayıcı ölü çerezi max-age dolana kadar GÖNDERMEYE devam
# eder — kısıtsız bir olay o durumda defteri saatlerce satır seliyle doldururdu. Süreç-içi bir
# defterdir ve öyle kalmalı (`_FAILS` ile aynı sınıf): diske yazsaydı susturmanın kaydı ikinci bir
# defter yüzeyi doğururdu. Süreç yeniden başlarsa pencere başına bir fazla satır düşer — seldan iyi.
DROP_REPORT_GAP_S = 300
_DROP_REPORTED: dict[str, float] = {}

# Kaba kuvvet: pencere içinde bu kadar başarısızlıktan sonra kilit
FAIL_WINDOW_S = 900                 # 15 dk
FAIL_MAX = 8
_FAILS: dict[str, list[float]] = {}


# ---- disk ----------------------------------------------------------------------------------
def _auth_file() -> Path:
    """Kimlik dosyasının yolu — HER ÇAĞRIDA yeniden çözülür, modül düzeyinde DONDURULMAZ.

    NEDEN FONKSİYON (2026-07-29): burası `AUTH_FILE = config.STATE / "auth.json"` idi, yani yol
    `import meridian.auth` ANINDA bağlanıyordu. `config.STATE`i SONRADAN yönlendiren her çağıran —
    test sandbox'ı, `MERIDIAN_ROOT` ile ikinci bir kök, bir kurtarma kopyası — auth'un hâlâ ESKİ
    dizini okuduğunu HİÇBİR YERDE göremiyordu. Somut bedeli: sandbox'lı testler kendi state
    dizinlerini kurup "parola kurulmamış" varsayıyordu, ama auth operatörün GERÇEK
    `state/auth.json`ını okumaya devam ettiği için `_auth` 51 uçta 401 veriyordu; üstelik hangi
    testin hangi sırada koştuğuna bağlı olarak. Bir yol sabiti, o yolu değiştirebilen bir
    yapılandırmanın yanında sessiz bir yalandır.

    `store._state()` aynı felsefeyi taşır: state yolu bir SABİT değil, o anki yapılandırmanın bir
    FONKSİYONUDUR. Güvenlik duruşu değişmez — canlıda `config.STATE` hiç yönlendirilmez, dolayısıyla
    dönen yol `state/auth.json`ın ta kendisidir.
    """
    return config.STATE / "auth.json"


def _read() -> dict:
    try:
        return json.loads(_auth_file().read_text())
    except (OSError, ValueError):  # sessiz-yutma: dosya yok (ilk kurulum) ya da bozuk — {} "kimlik yapılandırılmamış" demektir; parola ve oturum doğrulaması KAPALI tarafa düşer, kimse içeri alınmaz
        return {}


def _write(d: dict) -> None:
    """Kimlik defterini TEK YAZIM KAPISINDAN (`store.write_text`) geçir: atomik tmp→fsync→os.replace
    + süreçler-arası `flock` + BENZERSİZ tmp adı. Yazımın MANTIĞI (biçim, okuyucu sözleşmesi)
    değişmez — yalnız atomiklik/kilit/tmp-benzersizliği düzelir.

    ÖNCESİ (H9 kapı-dışı envanterinde EN TEHLİKELİ tekil): tmp adı SABİTTİ
    (`path.with_suffix(".json.tmp")`). İki süreç aynı anda yazarsa AYNI geçici dosyaya yazar, biri
    diğerinin baytlarını ezer ve `os.replace` yarı-yazılmış bir dosyayı yerine koyar — atomiklik
    iddiası tam orada biter. Ayrıca `fsync` YOKTU (güç kesintisinde sıfır-baytlık `auth.json` → `_read`
    `{}` okur → 'kimlik yapılandırılmamış' → parola ve tüm oturumlar KAPALI tarafa düşer, kimse içeri
    giremez) ve `flock` YOKTU (`set_password`/`rotate_key`/`_key` üçü de oku-değiştir-yaz'dır; kilitsiz
    araya giren ikinci bir yazar birinin `key`ini ya da hash'ini bayat bir kopyayla geri alabilirdi).
    `store.write_text` üçünü de kapıda verir; benzersiz tmp adını `mkstemp` sağlar.

    0600 İZNİ HÂLÂ BURADA ve BİLEREK: store'un `mkstemp`'i tmp'yi zaten 0600 açar (parola hash'i +
    imza anahtarı 0644 olarak diskte hiç durmaz) ve `os.replace` bunu son dosyaya taşır — ama bu
    store'un İÇSEL bir seçimidir, YAZILI bir sözleşmesi değil. auth kendi güvenlik iznini store'un
    tmp-modu tercihine devretmez: son dosyada 0600'ü AÇIKÇA doğrular (eski `_write`ın son satırındaki
    `os.chmod` güvencesinin KORUNMASI)."""
    from . import store
    store.write_text("auth.json", json.dumps(d, indent=2))
    os.chmod(_auth_file(), 0o600)


# ---- parola --------------------------------------------------------------------------------
def _derive(password: str, salt: bytes) -> bytes:
    return hashlib.scrypt(password.encode("utf-8"), salt=salt, maxmem=_MAXMEM, **_SCRYPT)


def set_password(password: str) -> None:
    """Parolayı ayarla/değiştir. Mevcut imza anahtarı KORUNUR: parola değiştirmek açık
    oturumları düşürmemeli — düşürmek isteniyorsa `rotate_key()` ayrı çağrılır."""
    if len(password) < 12:
        raise ValueError("parola en az 12 karakter olmalı — bu yüzey bir broker hesabına bakıyor")
    d = _read()
    salt = _secrets.token_bytes(16)
    d["salt"] = base64.b64encode(salt).decode()
    d["hash"] = base64.b64encode(_derive(password, salt)).decode()
    d["algo"] = "scrypt-n15-r8-p1"
    d.setdefault("key", base64.b64encode(_secrets.token_bytes(32)).decode())
    _write(d)


def password_set() -> bool:
    d = _read()
    return bool(d.get("hash") and d.get("salt"))


def verify_password(password: str) -> bool:
    d = _read()
    if not (d.get("hash") and d.get("salt")):
        return False
    try:
        salt = base64.b64decode(d["salt"])
        want = base64.b64decode(d["hash"])
    except (ValueError, TypeError):  # sessiz-yutma: kayıttaki salt/hash base64 çözülemiyorsa kayıt bozuktur — False girişi REDDEDER; bozuk kayıtla içeri almak yerine operatör parolayı sıfırlamak zorunda kalır
        return False
    return hmac.compare_digest(_derive(password, salt), want)


# ---- imza anahtarı -------------------------------------------------------------------------
def _key() -> bytes:
    d = _read()
    k = d.get("key")
    if not k:
        k = base64.b64encode(_secrets.token_bytes(32)).decode()
        d["key"] = k
        _write(d)
    return base64.b64decode(k)


def rotate_key() -> None:
    """İmza anahtarını değiştir → AÇIK TÜM OTURUMLAR DÜŞER. Parola sızdığından şüpheleniliyorsa
    parolayı değiştirmek TEK BAŞINA yetmez; eski oturum çerezleri geçerli kalır."""
    d = _read()
    d["key"] = base64.b64encode(_secrets.token_bytes(32)).decode()
    _write(d)


# ---- oturum --------------------------------------------------------------------------------
# İKİ JETON BİÇİMİ, BİLİNÇLİ ve GEÇİCİ (2026-08-14):
#   v2 (BUGÜN VERİLEN)  `<exp>.<iat>.<nonce>.<imza>`  — imzalanan ileti `v2.<exp>.<iat>.<nonce>`
#   v1 (ESKİ, YALNIZ OKUNUR) `<exp>.<nonce>.<imza>`   — imzalanan ileti `<exp>.<nonce>`
#
# ESKİ BİÇİM NEDEN GEÇERLİ KALIYOR: bu değişiklik CANLI bir panoya dağıtılıyor ve operatörün
# elindeki çerez v1'dir. Reddetseydik dağıtımın kendisi operatörü ANINDA dışarı atardı — yani
# "oturum kaybolmasın" diye yazılan yama, herkesin oturumunu kaybettirerek başlardı.
#
# ESKİ BİÇİM NEDEN YENİLENMİYOR: mutlak tavan `iat + SESSION_ABSOLUTE_MAX_S`tir ve v1 jetonu `iat`
# TAŞIMAZ. `exp - SESSION_TTL_S` ile geriye hesaplamak UYDURMA olurdu: o çıkarım, jetonun bugünkü
# TTL ile verildiğini VARSAYAR — TTL bir kez değiştiğinde varsayım sessizce yanlışlanır ve tavan
# gerçekte ölçmediğimiz bir sayıya dayanır. Ölçülemeyen tavana dayanıp yenilemek, tavanı hiç
# koymamakla aynı kapıya çıkar. Sonuç: v1 jetonu DOĞRULANIR, doğal ömrünü tamamlar (en fazla 12
# saat) ve operatörün bir sonraki girişi v2 verir. Geçiş penceresi kendiliğinden kapanır.
#
# İKİ BİÇİM BİRBİRİNE DÖNÜŞTÜRÜLEMEZ: (a) parça sayısı ayırt edicidir (3 vs 4) ve `nonce`
# `token_urlsafe`tir, nokta İÇERMEZ — yani bir v1 jetonu parçalanıp v2 gibi okunamaz; (b) v2'nin
# imzaladığı iletide `v2.` alan-ayırıcı öneki vardır, yani aynı anahtarla üretilmiş iki biçimin
# ileti uzayları kesişmez. İkisi birden gerekli değil; ikisi birden var, çünkü bu sınıftaki
# hataların bedeli geçerli-görünen sahte oturumdur.
def _sign(exp: int, iat: int) -> str:
    """v2 jetonunu üret. nonce iki eşzamanlı girişin aynı dizeyi üretmesini engeller (log
    korelasyonunu zorlaştırır, tekrar oynatmayı tespit edilebilir kılar)."""
    nonce = _secrets.token_urlsafe(12)
    msg = f"v2.{exp}.{iat}.{nonce}".encode()
    sig = base64.urlsafe_b64encode(hmac.new(_key(), msg, hashlib.sha256).digest()).decode().rstrip("=")
    return f"{exp}.{iat}.{nonce}.{sig}"


def _parse_session(token: str | None) -> tuple[int, int | None] | None:
    """İMZASI GEÇERLİ bir jetonun `(exp, iat)`ı; değilse None. `iat` None = ESKİ v1 jetonu.

    SÜREYE BAKMAZ — bu bilinçli bir iş bölümüdür: `verify_session` ve `refresh_session` süre
    kuralları BAKIMINDAN ayrışır (biri "geçerli mi", öteki "uzatılabilir mi" sorar) ama imza
    kuralı TEKTİR ve tek yerde durmalıdır.

    İMZA ÖNCE, SÜRE SONRA: süreyi önce kontrol etmek, imzası geçersiz bir çerez için farklı bir
    kod yolu (ve farklı zamanlama) yaratırdı. İkisi de sabit zamanlı karşılaştırmadan geçer."""
    if not token:
        return None
    parcalar = token.split(".")
    if len(parcalar) == 4:
        exp, iat, nonce, sig = parcalar
        msg = f"v2.{exp}.{iat}.{nonce}".encode()
    elif len(parcalar) == 3:
        exp, nonce, sig = parcalar
        iat = None
        msg = f"{exp}.{nonce}".encode()
    else:
        return None
    want = base64.urlsafe_b64encode(hmac.new(_key(), msg, hashlib.sha256).digest()).decode().rstrip("=")
    if not hmac.compare_digest(sig, want):
        return None
    try:
        return int(exp), (int(iat) if iat is not None else None)
    except ValueError:  # sessiz-yutma: imzası geçerli ama exp/iat'ı sayı olmayan bir çerezi biz üretmeyiz; yine de gelirse None oturumu REDDEDER — kapalı tarafa düşmek tek doğru cevaptır
        return None


def issue_session(ttl_s: int = SESSION_TTL_S) -> str:
    """Yeni oturum (v2). `exp` tavanla KIRPILIR ki `exp <= iat + SESSION_ABSOLUTE_MAX_S`
    değişmezliği ÜRETİM ANINDA kurulsun — `refresh_session`ın "uzatmıyorsa yenileme" kararı bu
    değişmezliğe dayanır ve dayandığı şeyin başka yerde bozulabilmesi kabul edilemez."""
    now = int(time.time())
    return _sign(min(now + ttl_s, now + SESSION_ABSOLUTE_MAX_S), now)


def verify_session(token: str | None) -> bool:
    ayristirilmis = _parse_session(token)
    if ayristirilmis is None:
        return False
    exp, _iat = ayristirilmis
    return exp > time.time()


def refresh_session(token: str | None) -> tuple[str, int] | None:
    """KAYAN OTURUM: gerekiyorsa `(yeni_jeton, kalan_saniye)`, gerekmiyorsa None.

    BEŞ RET dalı ve her birinin nedeni AYRI (hepsi None döner ama aynı şey değildirler):
      1. imza geçersiz / biçim bozuk → oturum zaten yok, yenilenecek bir şey de yok.
      2. jeton DÜŞMÜŞ (`exp <= now`) → yenileme bir dirilme kapısı DEĞİLDİR. Süresi geçmiş bir
         çerezle gelen istek 401 alır; onu tazelemek TTL'i tamamen anlamsız kılardı.
      3. ESKİ v1 jetonu (`iat` yok) → tavan ÖLÇÜLEMEZ, yenileme yok (yukarıdaki biçim notu).
      4. yarı-ömür GEÇMEMİŞ → gereksiz yazım yok. Her istekte `Set-Cookie` yazmak hem her yanıta
         yüz bayt ekler hem de çerezi durmadan yeniden yazan bir yüzey yaratır; oysa kazanç
         yalnızca ömrün ikinci yarısında gerçektir.
      5. yenileme hiçbir şeyi UZATMIYOR (`yeni_exp <= exp`) → mutlak tavanın son TTL penceresi.
         Jeton hâlâ GEÇERLİDİR ve öyle kalır; yalnız artık uzamaz ve orada doğal olarak düşer.

    YARI-ÖMÜR JETONUN KENDİ TTL'İNDEN ölçülür (`exp - iat`), modül sabitinden değil: `SESSION_TTL_S`
    yarın değişirse dünkü jetonlar yine kendi pencerelerine göre davranır — sabit, geçmişte
    verilmiş bir jetonun anlamını geriye dönük değiştiremez. Tamsayı aritmetiği:
    `now - iat > (exp - iat) / 2`  ⇔  `2*now > iat + exp`.

    TAVAN: yeni `exp` asla `iat + SESSION_ABSOLUTE_MAX_S`i geçmez. Tavana dayanmış bir jeton için
    yeni `exp` eskisini AŞMAZ — o hâlde yenileme hiçbir şey uzatmaz ve yapılmaz (5. ret dalı,
    tavanın son TTL penceresinde). Oturum orada doğal olarak düşer."""
    ayristirilmis = _parse_session(token)
    if ayristirilmis is None:
        return None
    exp, iat = ayristirilmis
    now = int(time.time())
    if exp <= now or iat is None:
        return None
    if 2 * now <= iat + exp:
        return None
    yeni_exp = min(now + SESSION_TTL_S, iat + SESSION_ABSOLUTE_MAX_S)
    if yeni_exp <= exp:
        return None
    return _sign(yeni_exp, iat), yeni_exp - now


def note_session_drop(ip: str) -> bool:
    """Bu IP için oturum-düşüşü olayı BASILSIN MI? (kayıt seli kapısı — `DROP_REPORT_GAP_S`)

    True dönen çağrı pencereyi kendi üstüne kapatır; bu yüzden çağıran olayı GERÇEKTEN basmalıdır.
    Ayırt edici sayı DEĞİL zaman: burada sorulan "kaç düşüş oldu" değil, "bu IP'nin düşüşü son
    beş dakikada zaten yazıldı mı"dır — pano 15 saniyede bir yokladığı için sayı ölçüsü aynı
    olayın tekrarını sayardı, olguyu değil."""
    now = time.time()
    for k, t in list(_DROP_REPORTED.items()):
        if now - t >= DROP_REPORT_GAP_S:
            _DROP_REPORTED.pop(k, None)     # defter IP başına sınırsız büyümesin
    if ip in _DROP_REPORTED:
        return False
    _DROP_REPORTED[ip] = now
    return True


# ---- kaba kuvvet ---------------------------------------------------------------------------
def _prune(ip: str, now: float) -> list[float]:
    xs = [t for t in _FAILS.get(ip, []) if now - t < FAIL_WINDOW_S]
    if xs:
        _FAILS[ip] = xs
    else:
        _FAILS.pop(ip, None)
    return xs


def locked_out(ip: str) -> bool:
    return len(_prune(ip, time.time())) >= FAIL_MAX


def note_failure(ip: str) -> None:
    now = time.time()
    _FAILS.setdefault(ip, []).append(now)
    _prune(ip, now)


def note_success(ip: str) -> None:
    _FAILS.pop(ip, None)


def retry_after_s(ip: str) -> int:
    xs = _prune(ip, time.time())
    if len(xs) < FAIL_MAX:
        return 0
    return max(1, int(FAIL_WINDOW_S - (time.time() - min(xs))))
