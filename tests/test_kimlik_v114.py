"""test_kimlik_v114.py — operatör kimliği: geç bağlanan yol, 401 önceliği, kimlik uçlarının sınırı.

NEDEN BU DOSYA (2026-07-29 mini turu): 2026-07-28 akşamı eklenen giriş/oturum katmanı ertesi gün
suite'te **35 kırmızı + 1 hata** olarak patladı ve kırmızıların tamamı tek bir satırdan geliyordu:

    AUTH_FILE = config.STATE / "auth.json"      # meridian/auth.py, modül düzeyi

Yol `import meridian.auth` ANINDA donuyordu. `sandbox_state` fikstürü `config.STATE`i tmp'ye
yönlendirir ama auth onu HİÇ görmezdi: operatörün GERÇEK `state/auth.json`ını okumaya devam
ederdi. O dosyada parola kurulu olduğu için `_auth` sandbox'lı testlerde de "parola kurulu" görür
ve `_auth`'lu 51 ucun hepsi 401 dönerdi. Üstelik sıra bağımlıydı — süreç-içi `auth._FAILS` sayacı
testler arası taşınıyor, bir testin biriktirdiği başarısız giriş sonrakini 429 ile karşılıyordu.

Bu dosya kusuru DEĞİL, kusurun MÜMKÜN OLMASINI engelleyen sözleşmeleri çivileniyor:
  1. yol çağrı anında çözülür ve donmuş bir sabit geri gelemez;
  2. parola kuruluyken 401, doğrulama hatasından (400) ÖNCE gelir — kimliksiz kullanıcıya
     "bu isim geçersiz" bile söylenmez;
  3. kimlik uçlarının listesi büyümez ve yetkisiz olmaları sınırsız yetki demek değildir;
  4. güvenlik duruşu (0600, scrypt profili, HttpOnly/SameSite, sorguda token YOK) ölçülür.
"""
from __future__ import annotations

import inspect
import os
import pathlib

import pytest
from fastapi.testclient import TestClient

from meridian import api, auth, config

PAROLA = "cok-uzun-ve-guclu-parola-123"


def _client(monkeypatch, token=None):
    """`with` KULLANILMAZ: lifespan `_autostart()`i koşturur (zamanlayıcı/Hermes/ayna akışı)."""
    monkeypatch.setattr(api, "DASH_TOKEN", token)
    return TestClient(api.app)


# ---------------------------------------------------------------- 1) YOL: geç bağlama
def test_auth_dosyasi_yolu_CAGRI_ANINDA_cozulur(tmp_path, monkeypatch):
    """KÖK NEDEN ÇİVİSİ: `_auth_file()` `config.STATE`i o AN okur. Bu test kırmızıya dönerse
    35 kırmızının tamamı geri gelmiş demektir — buradaki tek satır, oradaki tüm kümedir."""
    bir, iki = tmp_path / "bir", tmp_path / "iki"
    monkeypatch.setattr(config, "STATE", bir)
    assert auth._auth_file() == bir / "auth.json"
    monkeypatch.setattr(config, "STATE", iki)
    assert auth._auth_file() == iki / "auth.json", (
        "yol import anında donmuş — `sandbox_state` config.STATE'i yönlendirse bile auth "
        "operatörün GERÇEK state/auth.json'unu okur ve her uç 401 döner")


def test_modul_duzeyinde_DONMUS_bir_yol_sabiti_YOK():
    """Sabiti geri koymak, düzeltmeyi geri almaktır — ve sessizce olur (hiçbir test 'yeni bir
    modül değişkeni' fark etmez). Bu yüzden yokluğu AÇIKÇA ölçülür."""
    assert not hasattr(auth, "AUTH_FILE"), (
        "auth.AUTH_FILE geri gelmiş: modül düzeyinde donmuş bir yol, `config.STATE`i "
        "değiştirebilen her çağıran için sessiz bir yalandır — `_auth_file()` kullan")
    src = inspect.getsource(auth)
    assert "config.STATE" in src, "yol artık config.STATE'ten türemiyor — yönlendirme kopmuş"


def test_sandboxta_parola_KURULU_DEGIL_yani_auth_no_op(sandbox_state, monkeypatch):
    """Geç bağlamanın testlerdeki karşılığı: sandbox'ta auth.json YOKTUR → parola kurulmamıştır →
    `_auth` no-op'tur → auth katmanı ÖNCESİNDEKİ test davranışı aynen geri gelir."""
    assert not (sandbox_state / "auth.json").exists()
    assert auth.password_set() is False
    c = _client(monkeypatch, None)
    assert c.get("/api/summary").status_code == 200, (
        "sandbox'ta parola kurulu görünüyor — auth hâlâ canlı state/auth.json'u okuyor")


# ---------------------------------------------------------------- 2) 401 ÖNCELİĞİ
def test_parola_kuruluyken_401_dogrulama_hatasindan_ONCE_gelir(sandbox_state, monkeypatch):
    """TASARIM KARARI (korunur): kimliksiz çağırana doğrulama bilgisi SIZDIRILMAZ.

    `POST /api/secrets/{bilinmeyen-ad}` kimlikli kullanıcıya 400 "unknown secret name" döner —
    yani hangi adların GEÇERLİ olduğunu ayırt etmeye yarar. Kimliksiz kullanıcı bu farkı
    görmemeli: `_auth` gövde/ad doğrulamasından ÖNCE çalışır, cevap her hâlükârda 401'dir.
    Aksi halde uç, parolayı hiç bilmeyen birine sır ADI numaralandırma imkânı verirdi."""
    auth.set_password(PAROLA)
    c = _client(monkeypatch, None)
    r = c.post("/api/secrets/KESINLIKLE-BOYLE-BIR-AD-YOK", json={"value": "x"})
    assert r.status_code == 401, (
        f"kimliksiz çağrıya {r.status_code} döndü — 400 dönmek 'bu ad geçersiz' bilgisini "
        f"parolayı bilmeyen birine sızdırır (ad numaralandırma)")
    # POZİTİF KONTROL: aynı istek KİMLİKLİ iken gerçekten 400 döner, yani yukarıdaki 401 bir
    # örtme değil, bir ÖNCELİK — uç doğrulamayı hâlâ yapıyor.
    assert c.post("/api/login", json={"password": PAROLA}).status_code == 200
    r2 = c.post("/api/secrets/KESINLIKLE-BOYLE-BIR-AD-YOK", json={"value": "x"})
    assert r2.status_code == 400, "kimlikli çağrıda doğrulama hatası artık görünmeli"


def test_auth_govde_dogrulamasindan_once_cagrilir_yapisal_olarak():
    """Yukarıdaki davranış tek bir uçta değil, YAPIDA olmalı: `_auth(request)` gövdeye dokunan
    ilk satırlardan önce gelir. Kaynak üzerinden ölçülür ki yeni uçlar da aynı sırayı miras alsın."""
    src = inspect.getsource(api.api_set_secret)
    auth_at = src.index("_auth(request)")
    kontrol_at = src.index("secrets_mod.ALLOWED")
    assert auth_at < kontrol_at, "_auth ad doğrulamasından SONRA çağrılıyor — 401 önceliği kırık"


# ---------------------------------------------------------------- 3) KİMLİK UÇLARININ SINIRI
def test_kimlik_uclari_listesi_BUYUMEDI():
    """İstisna listesi sessizce büyüyebilen bir şeydir; büyüdüğünde burada tartışılsın."""
    assert set(api.KIMLIK_UCLARI) == {
        "/api/login", "/api/logout", "/api/session", "/api/setup-password"}, (
        "kimlik uçları listesi değişmiş — her yeni yol `_auth`SIZ bir yüzeydir ve gerekçesi "
        "api.py'de yazılmak zorundadır")


def test_kimlik_uclari_gercekten_auth_CAGIRMAZ():
    """Liste ile kod ayrışabilir: listede olup `_auth` çağıran bir uç, listeyi yalan yapar."""
    for fn in (api.api_login, api.api_logout, api.api_session, api.api_setup_password):
        assert "_auth(request)" not in inspect.getsource(fn), (
            f"{fn.__name__} hem kimlik ucu listesinde hem `_auth` çağırıyor — kapalı kapıya "
            f"girmenin yolu kapının kendisi olamaz")


def test_session_ucu_hesap_durumu_SIZDIRMAZ(sandbox_state, monkeypatch):
    """/api/session yetkisizdir; o yüzden döndürdüğü alan kümesi DAR olmak zorundadır."""
    c = _client(monkeypatch, None)
    d = c.get("/api/session").json()
    assert set(d) == {"authenticated", "password_set", "tls"}, (
        f"/api/session alan kümesi genişlemiş: {sorted(d)} — bu uç kimliksiz okunur, "
        f"sermaye/pozisyon/rejim gibi hiçbir hesap durumu buradan geçemez")


def test_setup_password_bir_SIFIRLAMA_arka_kapisi_DEGIL(sandbox_state, monkeypatch):
    """İlk parolayı kurar; kurulduktan sonra 409. Aksi halde yetkisiz bir uç, parolayı bilmeyen
    birine parolayı DEĞİŞTİRME hakkı verirdi — yani kimlik katmanının tamamını iptal ederdi."""
    c = _client(monkeypatch, None)
    assert c.post("/api/setup-password", json={"password": PAROLA}).status_code == 200
    r = c.post("/api/setup-password", json={"password": "baska-bir-parola-999"})
    assert r.status_code == 409, (
        f"parola kurulduktan sonra setup-password {r.status_code} döndü — yetkisiz bir "
        f"'parolamı unuttum' arka kapısı açılmış olurdu")
    assert auth.verify_password(PAROLA), "ikinci çağrı parolayı DEĞİŞTİRMİŞ"


def test_login_yetkisiz_ama_SINIRSIZ_degil(sandbox_state, monkeypatch):
    """/api/login'in `_auth`sız olması "korumasız" demek DEĞİL: IP başına kayan pencere kilidi
    kaba kuvveti sınırlar. Bu, listedeki gerekçenin ölçülmüş hâli."""
    auth.set_password(PAROLA)
    c = _client(monkeypatch, None)
    for _ in range(auth.FAIL_MAX):
        assert c.post("/api/login", json={"password": "yanlis"}).status_code == 401
    r = c.post("/api/login", json={"password": "yanlis"})
    assert r.status_code == 429, f"kaba kuvvet kilidi çalışmadı ({r.status_code})"
    # DOĞRU parola bile kilit penceresinde geçmez — kilit kimliğe değil, IP'ye bakar
    assert c.post("/api/login", json={"password": PAROLA}).status_code == 429


def test_FAILS_sayaci_testler_arasi_TASINMAZ():
    """Sıra bağımlılığının ikinci kaynağı: `_FAILS` süreç-içi ve TestClient'ın IP'si her testte
    aynı ("testclient"). Bir önceki test 8 başarısız giriş biriktirdiyse, bu test daha ilk
    çağrısında 429 alırdı — kendi kurmadığı bir durumdan. conftest her sandbox'ta temizler."""
    assert auth._FAILS == {}, (
        "auth._FAILS önceki testten devredildi — conftest._clear_module_caches temizliği kopmuş; "
        "bu, tek başına yeşil / paket içinde kırmızı testler üretir")


# ---------------------------------------------------------------- 4) GÜVENLİK DURUŞU
def test_scrypt_profili_ve_0600_korunur(sandbox_state):
    """Duruş sayıları: zayıflatılırsa test düşer. `n`i düşürmek girişi hızlandırır ve kaba kuvveti
    de aynı oranda ucuzlatır — bu bir performans ayarı değil, bir güvenlik parametresidir."""
    assert auth._SCRYPT == {"n": 2 ** 15, "r": 8, "p": 1, "dklen": 32}
    auth.set_password(PAROLA)
    p = auth._auth_file()
    assert p.stat().st_mode & 0o777 == 0o600, "kimlik dosyası sahibi dışına açık"
    assert not p.with_suffix(".json.tmp").exists(), "geçici dosya bırakılmış"
    d = __import__("json").loads(p.read_text())
    assert "hash" in d and "salt" in d and PAROLA not in p.read_text(), "parola diskte düz duruyor"


def test_oturum_cerezi_HttpOnly_ve_SameSite_Strict(sandbox_state, monkeypatch):
    """XSS tek başına kalıcı erişime dönüşmemeli (HttpOnly) ve tek POST'la HALT/Flatten tetikleyen
    bir yüzey CSRF'ye açık olmamalı (SameSite=Strict)."""
    auth.set_password(PAROLA)
    c = _client(monkeypatch, None)
    r = c.post("/api/login", json={"password": PAROLA})
    assert r.status_code == 200
    ck = r.headers["set-cookie"].lower()
    assert "httponly" in ck, "oturum çerezi JS'e açık — tek XSS kalıcı erişim demektir"
    assert "samesite=strict" in ck, "CSRF kapısı açık"
    assert auth.COOKIE_NAME in r.headers["set-cookie"]


def test_token_URL_sorgusundan_KABUL_EDILMEZ(sandbox_state, monkeypatch):
    """URL'ler sunucu loglarına, tarayıcı geçmişine ve `Referer` başlığına düşer. DOĞRU token bile
    sorgudan geçmemeli — bu satır bir davranışı değil, 2026-07-28'de verilmiş bir KARARI korur."""
    c = _client(monkeypatch, "GECERLI-ASCII-TOKEN")
    assert c.get("/api/summary", params={"token": "GECERLI-ASCII-TOKEN"}).status_code == 401
    assert c.get("/api/summary",
                 headers={"x-meridian-token": "GECERLI-ASCII-TOKEN"}).status_code == 200


def test_auth_yazimi_canli_state_bekcisine_GORUNUR(sandbox_state, monkeypatch):
    """auth.py store disiplininin DIŞINDA yazar (bkz. test_gaps_final_v52 istisna gerekçesi) —
    ama bu, canlı-yazım bekçisini KÖRLEŞTİRMEZ: `_write` atomik son adımı `os.replace` ile atar
    ve conftest tam o boğazı sarar. İstisnanın bedeli ölçülür, varsayılmaz."""
    gorulen: list[str] = []
    asil = os.replace
    monkeypatch.setattr(os, "replace", lambda s, d, *a, **k: (gorulen.append(str(d)), asil(s, d, *a, **k))[1])
    auth.set_password(PAROLA)
    assert any(pathlib.Path(g).name == "auth.json" for g in gorulen), (
        "auth._write artık os.replace'ten geçmiyor — canlı state bekçisinin göremediği bir "
        "yazım yolu açıldı ve sır dosyası sessizce canlıya düşebilir")


def test_parola_en_az_12_karakter(sandbox_state):
    with pytest.raises(ValueError):
        auth.set_password("kisa")
    assert not auth.password_set(), "reddedilen parola yine de kurulmuş"


# ---------------------------------------------------------------- 5) AYNI TURUN İKİNCİ BULGUSU
# Bir koşuda hata izleri `../Documents/Claude/AI-Trading/tests/...` yollarını gösteriyordu ve bu,
# "suite İKİZ bir checkout'tan test topluyor" diye okundu — saatler o varsayımla harcanabilirdi.
# ÖLÇÜLDÜ, ikiz checkout YOK: `~/Documents/Claude/AI-Trading` bu deponun kendisine giden bir
# SEMBOLİK BAĞ. Yollar bayat bytecode'dan geliyordu: pytest'in yeniden yazdığı `.pyc` dosyaları
# `co_filename`i DERLEME anındaki yoldan saklar ve geçerlilik denetimi kaynağın mtime+boyutuna
# bakar — aynı dosya olduğu için önbellek "taze" sayılır ve sembolik yol koşudan koşuya taşınır.
# Zararsız görünür ama kanıtı kirletir: hata izi, var olmayan bir ikinci depoyu işaret eder.
def test_hata_izlerindeki_yol_gercek_dosya_yoluyla_AYNI():
    """`co_filename` ile `__file__` ayrışıyorsa bytecode bayattır ve hata izleri yanlış depoyu
    gösterir. Çözüm: `tests/__pycache__` ve `meridian/__pycache__` temizlenir."""
    co = pathlib.Path(test_hata_izlerindeki_yol_gercek_dosya_yoluyla_AYNI.__code__.co_filename)
    assert co.resolve() == pathlib.Path(__file__).resolve(), (
        f"hata izi yolu ({co}) gerçek dosya yolundan ({__file__}) farklı — bayat pytest bytecode. "
        f"Hata izleri var olmayan bir ikiz checkout'u işaret eder. Temizle: "
        f"`find . -name '__pycache__' -type d -exec rm -rf {{}} +`")


def test_uretim_ve_test_paketleri_AYNI_kokten_gelir():
    """İkiz bir checkout gerçekten olsaydı burası yakalardı: testler bir kökten, üretim kodu
    başka bir kökten gelirse test ettiğin şey koştuğun şey değildir."""
    import meridian
    mer_kok = pathlib.Path(meridian.__file__).resolve().parent.parent
    test_kok = pathlib.Path(__file__).resolve().parent.parent
    assert mer_kok == test_kok, (
        f"testler {test_kok} altından, `meridian` {mer_kok} altından geliyor — suite koştuğun "
        f"kodu ölçmüyor")
