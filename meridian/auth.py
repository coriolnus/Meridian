"""auth.py — operatör kimliği: parola doğrulama + imzalı oturum çerezi.

NEDEN VAR (2026-07-28, Oracle Cloud dağıtımı öncesi): pano bugüne kadar YALNIZ `--host 127.0.0.1`
bağlanmasıyla korunuyordu. `MERIDIAN_DASH_TOKEN` hiçbir yerde ayarlı değildi, dolayısıyla
`api._auth` 51 uçta çağrılıyor ama hepsinde anında dönüyordu — fiilen kimlik doğrulaması yoktu.
Genel bir IP'ye çıkıldığı an bu, hesap durumunu okuyan ve HALT/DEVAM/Flatten/mutasyon tetikleyen
bir yüzeyin yetkisiz açılması demektir.

TASARIM KARARLARI ve GEREKÇELERİ

* **Parola diskte asla düz durmaz.** `hashlib.scrypt` (stdlib; yeni bağımlılık yok) ile
  tuzlanmış türetme. Parametreler RFC 7914'ün etkileşimli-giriş profilinden: n=2^15, r=8, p=1.
  Doğrulama `hmac.compare_digest` ile sabit zamanlı — `!=` ilk uyumsuz baytta kısa devre yapar
  ve hash'i bayt bayt kurtarmaya izin verir (CWE-208).

* **Oturum ÇEREZDE, localStorage'da DEĞİL.** Eski akış token'ı `localStorage`'a yazıyordu; orası
  JavaScript'e açıktır, yani tek bir XSS kalıcı erişim demektir. Çerez `HttpOnly` olduğunda JS
  onu okuyamaz. `SameSite=Strict` çapraz-site istek sahteciliğini (CSRF) kapatır — HALT ve
  Flatten gibi tek POST'la iş gören uçlar için bu teorik bir kaygı değildir.

* **Oturum durumsuz ve İMZALI.** `<exp>.<nonce>.<hmac>` — sunucu tarafında oturum tablosu yok,
  yani yeniden başlatma oturumları düşürmez ama imza anahtarı değişirse HEPSİ düşer. Anahtar
  diskte (0600) tutulur; yoksa üretilir.

* **URL'de token YOK.** Eski `_auth` `?token=` kabul ediyordu ve indirme bağlantıları token'ı
  oraya koyuyordu. URL'ler sunucu loglarına, tarayıcı geçmişine ve `Referer` başlığına düşer.
  Çerez tabanlı oturum indirmelerde de çalışır, çünkü tarayıcı onu kendiliğinden gönderir.

* **Kaba kuvvet sınırlanır.** IP başına kayan pencere; eşiği aşınca kilit. Sayaç süreç-içidir:
  tek süreçli dağıtımda yeterli, yatay ölçeklenirse paylaşımlı bir depoya taşınmalıdır (bu
  dosyada başka bir iddiada bulunulmuyor).
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
def issue_session(ttl_s: int = SESSION_TTL_S) -> str:
    """`<exp>.<nonce>.<imza>` — durumsuz. nonce iki eşzamanlı girişin aynı dizeyi üretmesini
    engeller (log korelasyonunu zorlaştırır, tekrar oynatmayı tespit edilebilir kılar)."""
    exp = str(int(time.time()) + ttl_s)
    nonce = _secrets.token_urlsafe(12)
    msg = f"{exp}.{nonce}".encode()
    sig = base64.urlsafe_b64encode(hmac.new(_key(), msg, hashlib.sha256).digest()).decode().rstrip("=")
    return f"{exp}.{nonce}.{sig}"


def verify_session(token: str | None) -> bool:
    if not token or token.count(".") != 2:
        return False
    exp, nonce, sig = token.split(".")
    msg = f"{exp}.{nonce}".encode()
    want = base64.urlsafe_b64encode(hmac.new(_key(), msg, hashlib.sha256).digest()).decode().rstrip("=")
    # İMZA ÖNCE, SÜRE SONRA: süreyi önce kontrol etmek, imzası geçersiz bir çerez için farklı bir
    # kod yolu (ve farklı zamanlama) yaratırdı. İkisi de sabit zamanlı karşılaştırmadan geçer.
    if not hmac.compare_digest(sig, want):
        return False
    try:
        return int(exp) > time.time()
    except ValueError:  # sessiz-yutma: imzası geçerli ama exp'i sayı olmayan bir çerezi biz üretmeyiz; yine de gelirse False oturumu REDDEDER — kapalı tarafa düşmek tek doğru cevaptır
        return False


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
