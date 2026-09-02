"""test_kayan_oturum_v245.py — KAYAN OTURUM + kimlik olay kaydı (2026-08-14).

NEDEN BU DOSYA — OPERATÖR ARIZASI: "arayüz bir süre sonra kayboluyor, bütün sekmeler için
geçerli". Kök neden koddan doğrulandı ve bir çizim hatası DEĞİLDİ:

    auth.SESSION_TTL_S = 12*3600  SABİT bir penceredir ve `api.py`de `set_cookie` YALNIZ İKİ
    yerde çağrılıyordu — giriş ve ilk-parola-kurulumu. Kullanımla yenilenen yol YOKTU.

Pano kesintisiz kullanılsa bile saat dolduğunda `_auth` 401 verir, `app.js:_yetkisizYakala` kapağı
açar; çerez sekmeler arasında ORTAK olduğu için hepsi AYNI ANDA düşer ve pano 15 saniyede bir
yokladığı için düşüş saniyeler içinde görünür.

BU DOSYA DÜZELTMEYİ DEĞİL, DÜZELTMENİN SINIRLARINI ÇİVİLER — çünkü "çerezi tazele" tek başına bir
güvenlik gerilemesidir: sınırsız yenilenen bir çerez, çalındığında SONSUZA kadar yaşar. Ölçülen
sözleşme şudur:
  1. yarı-ömrü geçmemiş jeton tazelenmez, geçmiş tazelenir  (gereksiz yazım yok / kayma çalışıyor)
  2. `iat + SESSION_ABSOLUTE_MAX_S` mutlak tavandır; tavana varan oturum kullanılsa bile düşer
  3. ESKİ üç-parçalı jeton DOĞRULANIR ama YENİLENMEZ — `iat` yoksa tavan ÖLÇÜLEMEZ ve ölçülemeyen
     bir tavana dayanıp yenilemek uydurmadır (UYDURMA YASAĞI)
  4. bozuk/imzasız jeton reddedilir (mevcut davranış korunur)
  5. kimlik olayları (giriş · tazeleme · düşüş) basılır ve İÇLERİNDE PAROLA/JETON GEÇMEZ
  6. `app.js`in 401 kapağı DEĞİŞMEDİ — sunucu tarafı bir gün geri alınırsa operatör kapısız kalmaz
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import pathlib
import time

import pytest
from fastapi.testclient import TestClient

from meridian import api, auth

PAROLA = "cok-uzun-ve-guclu-parola-123"
GUN = 86400


def _client(monkeypatch, token=None):
    """`with` KULLANILMAZ: lifespan `_autostart()`i koşturur (zamanlayıcı/Hermes/ayna akışı)."""
    monkeypatch.setattr(api, "DASH_TOKEN", token)
    return TestClient(api.app)


def _cerezle(c, tok):
    """Çerezi BAŞLIKTAN ver, httpx kavanozundan DEĞİL: kavanoz bir önceki yanıtın `Set-Cookie`ini
    kendiliğinden yutar ve testin hangi jetonu gönderdiği ölçülemez hâle gelirdi."""
    return {"cookie": f"{auth.COOKIE_NAME}={tok}"}


def _v1_jeton(exp: int) -> str:
    """ESKİ (v1) üç-parçalı jetonu ÜRET — üretim kodunda böyle bir üretici artık YOK ve olmamalı.

    Testin imza algoritmasını yeniden yazması normalde bir kopya-sürüklenmesi riskidir; burada
    BİLİNÇLİ ve gerekli: geriye uyum sözleşmesi ancak eski biçimden bir örnek üretilebiliyorsa
    ÖLÇÜLEBİLİR. Üretim tarafı v1'i yalnız OKUR (`auth._parse_session`), asla yazmaz — bu
    fonksiyon o asimetrinin test tarafındaki karşılığıdır."""
    nonce = "eskiNonce123"
    msg = f"{exp}.{nonce}".encode()
    sig = base64.urlsafe_b64encode(
        hmac.new(auth._key(), msg, hashlib.sha256).digest()).decode().rstrip("=")
    return f"{exp}.{nonce}.{sig}"


def _olaylar(sandbox) -> list[dict]:
    p = sandbox / "events.jsonl"
    if not p.exists():
        return []
    return [json.loads(s) for s in p.read_text().splitlines() if s.strip()]


def _cerez_basliklari(r) -> list[str]:
    return [v for v in r.headers.get_list("set-cookie") if v.startswith(auth.COOKIE_NAME + "=")]


# =================================================================================================
# 1) KAYMA — yarı-ömür kapısı
# =================================================================================================
def test_yari_omru_GECMEMIS_jeton_TAZELENMEZ(sandbox_state):
    """GEREKSİZ YAZIM YOK: her istekte `Set-Cookie` yazmak hem her yanıta yüz bayt ekler hem de
    çerezi durmadan yeniden yazan bir yüzey yaratır. Kazanç yalnız ömrün ikinci yarısında gerçek."""
    now = int(time.time())
    taze = auth._sign(now + 12 * 3600, now)
    assert auth.verify_session(taze) is True
    assert auth.refresh_session(taze) is None, "yeni verilmiş jeton daha ilk istekte tazeleniyor"

    # SINIR: yarı-ömrün TAM ÜSTÜ hâlâ "geçmemiş" sayılır (`2*now <= iat+exp`) — sınırın hangi
    # tarafta olduğu yazılı olmazsa bir gün sessizce öteki tarafa kayar.
    sinirda = auth._sign(now + 6 * 3600, now - 6 * 3600)
    assert auth.refresh_session(sinirda) is None, "yarı-ömür sınırı kapsayıcı taraftan kaymış"


def test_yari_omru_GECMIS_jeton_TAZELENIR_ve_iat_KORUNUR(sandbox_state):
    """KAYMANIN KENDİSİ + tavanın kaçamayacağı garanti: yeni jeton ESKİ `iat`ı taşır.

    `iat` tazelemede yenilenseydi mutlak tavan her yenilemede ileri kayar ve 7 günlük sınır
    hiçbir zaman gelmezdi — yani tavan kodda VAR, gerçekte YOK olurdu. Bu satır o farkı ölçer."""
    now = int(time.time())
    iat = now - 7 * 3600
    eski = auth._sign(iat + 12 * 3600, iat)          # 5 saat ömrü kaldı, yarısını geçti
    sonuc = auth.refresh_session(eski)
    assert sonuc is not None, "yarı-ömrü geçmiş jeton tazelenmedi — arıza aynen duruyor"
    yeni, kalan = sonuc
    assert auth.verify_session(yeni) is True
    yeni_exp, yeni_iat = auth._parse_session(yeni)
    assert yeni_iat == iat, "tazeleme `iat`ı ilerletti — mutlak tavan sonsuza kadar kaçar"
    assert yeni_exp > int(auth._parse_session(eski)[0]), "tazeleme ömrü uzatmadı"
    assert abs(kalan - auth.SESSION_TTL_S) <= 2, "çerez max-age'i yeni ömürle uyuşmuyor"


def test_DUSMUS_jeton_TAZELENMEZ_dirilme_kapisi_yok(sandbox_state):
    """Süresi geçmiş bir çerez 401 alır; onu tazelemek TTL'i tamamen anlamsız kılardı."""
    now = int(time.time())
    dusmus = auth._sign(now - 60, now - 12 * 3600 - 60)
    assert auth.verify_session(dusmus) is False
    assert auth.refresh_session(dusmus) is None, "düşmüş jeton yenilemeyle diriliyor"


# =================================================================================================
# 2) MUTLAK TAVAN — çalınmış çerezin ömür sınırı
# =================================================================================================
def test_MUTLAK_TAVAN_modul_duzeyinde_ve_makul(sandbox_state):
    """Sayı TEK YERDE ve okunur olmalı: tavan bir dağıtım ayarı değil, çalınmış bir çerezin
    yaşayabileceği en uzun süredir."""
    assert auth.SESSION_ABSOLUTE_MAX_S == 7 * GUN
    assert auth.SESSION_ABSOLUTE_MAX_S > auth.SESSION_TTL_S, (
        "tavan tek bir TTL'den kısa — kayan oturum hiç çalışmaz, her jeton doğrudan tavana çarpar")


def test_tavana_VARMIS_jeton_YENILENMEZ_dogal_olarak_duser(sandbox_state):
    """`exp` tavana dayanmışsa yenileme hiçbir şeyi uzatamaz; oturum orada biter ve operatör
    yeniden girer. Jeton hâlâ GEÇERLİDİR (kalan bir saati vardır) — 'yenilenmez' ile 'reddedilir'
    ayrı şeylerdir ve karıştırılırsa operatör kapıya bir saat erken çarpar."""
    now = int(time.time())
    iat = now - auth.SESSION_ABSOLUTE_MAX_S + 3600      # tavana 1 saat kaldı
    tavanda = auth._sign(iat + auth.SESSION_ABSOLUTE_MAX_S, iat)
    assert auth.verify_session(tavanda) is True, "tavana yaklaşan jeton erken reddedildi"
    assert auth.refresh_session(tavanda) is None, "tavan aşılıyor — çalınan çerez sonsuza yaşar"


def test_tavani_ASMIS_jeton_YENILENMEZ(sandbox_state):
    """Tavanın ÖTESİNDE bir `iat` (saat kayması, elle üretilmiş jeton): yenileme yine yok."""
    now = int(time.time())
    asmis = auth._sign(now + 3600, now - 8 * GUN)
    assert auth.refresh_session(asmis) is None, "tavanın ötesindeki jeton yenileniyor"


# =================================================================================================
# 3) GERİYE UYUM — v1 (üç parçalı) jeton
# =================================================================================================
def test_ESKI_uc_parcali_jeton_DOGRULANIR(sandbox_state):
    """DAĞITIM ANI ŞARTI: operatörün elindeki çerez v1'dir. Reddedilseydi bu yama, oturum
    kaybını önlemek için yazılıp herkesin oturumunu kaybettirerek başlardı."""
    v1 = _v1_jeton(int(time.time()) + 3600)
    assert auth.verify_session(v1) is True, "eski biçim jeton reddedildi — dağıtım operatörü atar"


def test_ESKI_uc_parcali_jeton_YENILENMEZ(sandbox_state):
    """UYDURMA YASAĞI'nın buradaki karşılığı: v1 `iat` TAŞIMAZ, yani mutlak tavanı ÖLÇÜLEMEZ.
    `exp - SESSION_TTL_S` ile geriye hesaplamak, jetonun bugünkü TTL ile verildiğini VARSAYMAK
    olurdu — TTL bir kez değişince varsayım sessizce yanlışlanır. Ölçülemeyen tavana dayanıp
    yenilemek, tavanı hiç koymamakla aynıdır. v1 doğal ömrünü tamamlar, sonraki giriş v2 verir."""
    now = int(time.time())
    v1 = _v1_jeton(now + 3600)                  # 12 saatlik pencerede yarı-ömrü ÇOKTAN geçmiş
    assert auth._parse_session(v1) == (now + 3600, None), "v1 ayrıştırması bozuldu"
    assert auth.refresh_session(v1) is None, (
        "eski biçim jeton yenileniyor — `iat` yokken tavan ölçülemez, yani ölçülmemiş bir sınıra "
        "dayanan bir yenileme yapılmış olur")


def test_YENI_jeton_dort_parcali_ve_iat_TASIR(sandbox_state):
    tok = auth.issue_session()
    assert tok.count(".") == 3, "yeni jeton v2 biçiminde değil — `iat` alanı kaybolmuş"
    exp, iat = auth._parse_session(tok)
    assert iat is not None and abs(iat - int(time.time())) <= 2
    assert exp - iat == auth.SESSION_TTL_S


# =================================================================================================
# 4) BOZUK JETON — mevcut davranış korunur
# =================================================================================================
@pytest.mark.parametrize("kotu", [
    None, "", "tekparca", "iki.parca", "bozuk.token.xyz", "1.2.3.4", "a.b.c.d.e",
    "9999999999.999.nonce.imzayok",
])
def test_bozuk_ya_da_IMZASIZ_jeton_reddedilir(sandbox_state, kotu):
    """Parça sayısı ne olursa olsun imza kapısı ÖNCE gelir: v2 biçimine benzeyen ama imzasız bir
    dize, sırf dört parçalı diye içeri giremez."""
    assert auth.verify_session(kotu) is False
    assert auth.refresh_session(kotu) is None


def test_imza_anahtari_donunce_TUM_oturumlar_duser(sandbox_state):
    """`rotate_key()` sözleşmesi (parola sızdıysa tek çare) kayan oturumla BOZULMADI."""
    auth.set_password(PAROLA)
    tok = auth.issue_session()
    assert auth.verify_session(tok) is True
    auth.rotate_key()
    assert auth.verify_session(tok) is False, "anahtar döndü ama eski oturum hâlâ geçerli"
    assert auth.refresh_session(tok) is None, "anahtarı dönmüş jeton yenileniyor"


# =================================================================================================
# 5) HTTP KATMANI — çerez gerçekten tazeleniyor mu, ve çerezi YAZAN yollar çakışıyor mu
# =================================================================================================
def test_yetkili_istekte_cerez_TAZELENIR_ve_durus_ozellikleri_KORUNUR(sandbox_state, monkeypatch):
    """Uçtan uca: yarı-ömrü geçmiş çerezle gelen yetkili istek 200 döner VE tazelenmiş çerezi
    taşır. Öznitelikler (`HttpOnly`, `SameSite=Strict`, `Path=/`) tazelemede de yerinde —
    `_oturum_cerez_basligi` tek kaynak olmasaydı burası sessizce gevşeyebilirdi."""
    auth.set_password(PAROLA)
    now = int(time.time())
    iat = now - 7 * 3600
    eski = auth._sign(iat + 12 * 3600, iat)
    c = _client(monkeypatch, None)
    r = c.get("/api/summary", headers=_cerezle(c, eski))
    assert r.status_code == 200, f"tazelenebilir çerezle yetkili uç düştü ({r.status_code})"
    ck = _cerez_basliklari(r)
    assert len(ck) == 1, f"oturum çerezi tazelenmedi ya da birden çok kez yazıldı: {ck}"
    dusuk = ck[0].lower()
    assert "httponly" in dusuk, "tazelenen çerez JS'e açık — tek XSS kalıcı erişim demektir"
    assert "samesite=strict" in dusuk, "tazelenen çerezde CSRF kapısı açık"
    assert "path=/" in dusuk, "tazelenen çerezin kapsamı daralmış — pano yollarında düşer"
    yeni_tok = ck[0].split(";")[0].split("=", 1)[1]
    assert yeni_tok != eski and auth.verify_session(yeni_tok) is True
    assert auth._parse_session(yeni_tok)[1] == iat, "tazelemede `iat` ilerledi"


def test_taze_cerezle_gelen_istek_Set_Cookie_TASIMAZ(sandbox_state, monkeypatch):
    auth.set_password(PAROLA)
    c = _client(monkeypatch, None)
    r = c.get("/api/summary", headers=_cerezle(c, auth.issue_session()))
    assert r.status_code == 200
    assert _cerez_basliklari(r) == [], "yarı-ömrü geçmemiş çerez her istekte yeniden yazılıyor"


def test_LOGOUT_cerezi_tazeleyiciyle_EZILMEZ(sandbox_state, monkeypatch):
    """EN SİNSİ TUZAK: tazeleyici yığının en dışındadır, yani `/api/logout`un silme başlığından
    SONRA yazardı. Tarayıcı aynı ada iki `Set-Cookie` görünce SONUNCUYU uygular — çıkış sessizce
    çalışmaz olurdu ve hiçbir yerde hata görünmezdi."""
    auth.set_password(PAROLA)
    now = int(time.time())
    iat = now - 7 * 3600
    eski = auth._sign(iat + 12 * 3600, iat)          # tazelenmeye HAZIR bir çerez
    assert auth.refresh_session(eski) is not None, "test kurulumu yanlış: bu çerez tazelenmiyor"
    c = _client(monkeypatch, None)
    r = c.post("/api/logout", headers=_cerezle(c, eski))
    assert r.status_code == 200
    ck = _cerez_basliklari(r)
    assert len(ck) == 1, f"çıkış yanıtında birden çok oturum çerezi: {ck}"
    deger = ck[0].split(";")[0].split("=", 1)[1].strip('"')
    assert deger == "", f"çıkış çerezi silmiyor, tazeleyici üstüne yazmış: {ck[0]}"


def test_LOGIN_yanitinda_TEK_cerez_vardir(sandbox_state, monkeypatch):
    """Elinde tazelenebilir eski bir çerez varken yeniden giriş: yanıt YALNIZ yeni oturumu
    yazmalı. İki başlık olsaydı hangisinin kazandığı tarayıcı sırasına kalırdı."""
    auth.set_password(PAROLA)
    now = int(time.time())
    iat = now - 7 * 3600
    eski = auth._sign(iat + 12 * 3600, iat)
    c = _client(monkeypatch, None)
    r = c.post("/api/login", json={"password": PAROLA}, headers=_cerezle(c, eski))
    assert r.status_code == 200
    ck = _cerez_basliklari(r)
    assert len(ck) == 1, f"giriş yanıtında birden çok oturum çerezi: {ck}"
    yeni_tok = ck[0].split(";")[0].split("=", 1)[1]
    assert auth._parse_session(yeni_tok)[1] > iat, "giriş eski oturumun `iat`ını devraldı"


def test_ESKI_bicimli_cerez_calisir_ama_TAZELENMEZ_uctan_uca(sandbox_state, monkeypatch):
    """Dağıtım anının birebir provası: operatörün tarayıcısındaki v1 çerez."""
    auth.set_password(PAROLA)
    v1 = _v1_jeton(int(time.time()) + 3600)
    c = _client(monkeypatch, None)
    r = c.get("/api/summary", headers=_cerezle(c, v1))
    assert r.status_code == 200, "eski çerez dağıtımdan sonra çalışmıyor — operatör anında düşer"
    assert _cerez_basliklari(r) == [], "eski biçim çerez tazelendi — ölçülemeyen tavana dayanıldı"


# =================================================================================================
# 6) KİMLİK OLAYLARI — "kim ne zaman girdi" sorusunun cevabı
# =================================================================================================
def test_BASARILI_giris_olay_basar_ve_PAROLA_JETON_GECMEZ(sandbox_state, monkeypatch):
    """ÖLÇÜLEN BOŞLUK (2026-08-14): başarılı girişler HİÇ kaydedilmiyordu — yalnız `password_set`
    ve `login_failed` olay basıyordu. Broker durdurma yüzeyi taşıyan bir panoda bir sızıntıdan
    sonra sorulan şey "kaç kez yanlış denendi" değil, "başka biri İÇERİ GİRDİ Mİ"dir.

    DİZGİ ÇİVİSİ: defterin TAMAMINDA ne parola ne de verilen jeton geçebilir. Deftere yazılan bir
    sır, sızan bir sırdır — üstelik `events.jsonl` panodan okunabilir bir yüzeydir."""
    auth.set_password(PAROLA)
    c = _client(monkeypatch, None)
    r = c.post("/api/login", json={"password": PAROLA})
    assert r.status_code == 200
    tok = _cerez_basliklari(r)[0].split(";")[0].split("=", 1)[1]

    olaylar = _olaylar(sandbox_state)
    giris = [o for o in olaylar if o.get("event") == "login_ok"]
    assert len(giris) == 1, f"başarılı giriş kaydedilmedi: {[o.get('event') for o in olaylar]}"
    assert giris[0].get("ip") == "testclient", "olay istemci IP'sini taşımıyor"
    assert giris[0].get("ts"), "olay zaman damgası taşımıyor"

    ham = (sandbox_state / "events.jsonl").read_text()
    assert PAROLA not in ham, "PAROLA olay defterine düşmüş"
    assert tok not in ham, "OTURUM JETONU olay defterine düşmüş — çalınabilir bir kimlik"
    for parca in tok.split("."):
        assert parca not in ham, f"jetonun bir parçası ({parca[:8]}…) deftere düşmüş"


def test_TAZELEME_olay_basar_ve_jeton_TASIMAZ(sandbox_state, monkeypatch):
    """TSK-106 (2026-09-02) ile HİZALANDI: defter (ip, yol) başına günlük özete indi, ama bu
    çivinin ölçtüğü şey DEĞİŞMEDİ — çiftin İLK tazelemesi hâlâ ANINDA basılır. Sözleşmenin
    görünürlük yarısı tam da budur, o yüzden burada ayırt edici alan da çivilenir (`ozet=False`):
    kesim bir gün "ilk olayı da beklet" diye evrilirse bu satır ötsün, sessizce kaybolmasın."""
    auth.set_password(PAROLA)
    now = int(time.time())
    iat = now - 7 * 3600
    eski = auth._sign(iat + 12 * 3600, iat)
    c = _client(monkeypatch, None)
    r = c.get("/api/summary", headers=_cerezle(c, eski))
    assert r.status_code == 200
    yeni_tok = _cerez_basliklari(r)[0].split(";")[0].split("=", 1)[1]

    tazeleme = [o for o in _olaylar(sandbox_state) if o.get("event") == "session_refresh"]
    assert len(tazeleme) == 1, "oturum tazelemesi hiçbir yere yazılmadı"
    assert tazeleme[0].get("ip") == "testclient"
    assert tazeleme[0].get("ozet") is False, tazeleme[0]   # TSK-106: ANINDA satır, özet değil
    ham = (sandbox_state / "events.jsonl").read_text()
    assert yeni_tok not in ham and eski not in ham, "tazeleme olayı jeton taşıyor"


def test_OTURUM_DUSUSU_olay_basar_ve_SEL_KAPISI_calisir(sandbox_state, monkeypatch):
    """Düşüş = çerez GELMİŞ ama doğrulanamamış. Çerezsiz 401 sıradan bir yetkisiz çağrıdır
    (bot taraması); ikisi aynı satırla bassaydı gerçek düşüş gürültüde kaybolurdu.

    SEL KAPISI: pano 15 sn'de bir yokluyor ve `rotate_key()` sonrası tarayıcı ölü çerezi max-age
    dolana kadar göndermeye devam eder — kapısız bir olay defteri saatlerce satırla doldururdu."""
    auth.set_password(PAROLA)
    now = int(time.time())
    dusmus = auth._sign(now - 60, now - 12 * 3600 - 60)
    c = _client(monkeypatch, None)

    assert c.get("/api/summary", headers=_cerezle(c, dusmus)).status_code == 401
    dususler = [o for o in _olaylar(sandbox_state) if o.get("event") == "session_drop"]
    assert len(dususler) == 1, "oturum düşüşü kaydedilmedi — operatörün gördüğü olay görünmez"
    assert dususler[0].get("ip") == "testclient"

    for _ in range(5):
        assert c.get("/api/summary", headers=_cerezle(c, dusmus)).status_code == 401
    assert len([o for o in _olaylar(sandbox_state) if o.get("event") == "session_drop"]) == 1, (
        "sel kapısı çalışmıyor — 15 saniyelik yoklama defteri satır seliyle doldurur")

    auth._DROP_REPORTED.clear()          # pencere kapanınca olay yeniden basılabilmeli
    assert c.get("/api/summary", headers=_cerezle(c, dusmus)).status_code == 401
    assert len([o for o in _olaylar(sandbox_state) if o.get("event") == "session_drop"]) == 2


def test_CEREZSIZ_401_dusus_olayi_BASMAZ(sandbox_state, monkeypatch):
    auth.set_password(PAROLA)
    c = _client(monkeypatch, None)
    assert c.get("/api/summary").status_code == 401
    assert [o for o in _olaylar(sandbox_state) if o.get("event") == "session_drop"] == [], (
        "çerezsiz yetkisiz çağrı 'oturum düştü' diye yazılıyor — defter gürültüye boğulur")


def test_KILITLENME_olay_basar(sandbox_state, monkeypatch):
    """`login_failed` sekiz kez yazılır, sonra kilit devreye girer ve o andan sonra HİÇBİR SATIR
    düşmezdi — defteri okuyan kişi saldırının DEVAM ETTİĞİ pencerede sessizlik görürdü."""
    auth.set_password(PAROLA)
    c = _client(monkeypatch, None)
    for _ in range(auth.FAIL_MAX):
        assert c.post("/api/login", json={"password": "yanlis-parola-123"}).status_code == 401
    assert c.post("/api/login", json={"password": PAROLA}).status_code == 429
    kilit = [o for o in _olaylar(sandbox_state) if o.get("event") == "login_locked_out"]
    assert len(kilit) == 1, "kaba-kuvvet kilidi sessiz — en kayda değer dal en sessiz olanıydı"
    assert kilit[0].get("retry_after_s", 0) > 0
    assert "yanlis-parola-123" not in (sandbox_state / "events.jsonl").read_text()


# =================================================================================================
# 7) İSTEMCİ TARAFI DEĞİŞMEDİ
# =================================================================================================
def test_app_js_401_kapagi_DEGISMEDI():
    """Sunucu tarafındaki tazeleme istemcinin GÖRECEĞİ bir şey değildir (çerez HttpOnly'dir, JS
    okuyamaz) — pano yalnız 401 görmemeye başlar. Kapak mantığına dokunmak, sunucu bir gün geri
    alınırsa operatörü kapısız bırakırdı."""
    src = (pathlib.Path(__file__).resolve().parent.parent
           / "meridian" / "web" / "app.js").read_text()
    govde = src.split("function _yetkisizYakala(r) {", 1)
    assert len(govde) == 2, "_yetkisizYakala kaldırılmış — 401 kapağı artık yok"
    govde = govde[1].split("\n}", 1)[0]
    assert "r.status === 401" in govde, "401 kapısı kaldırılmış"
    assert "_JC.clear()" in govde, "401'de yanıt önbelleği temizlenmiyor — önceki operatörün "\
                                   "verisi bir sonrakine görünür"
    assert "kapiyiGoster(false" in govde, "401'de giriş kapağı açılmıyor"


def test_app_js_12_saat_iddiasini_ARTIK_yazmiyor():
    """YASA: kod ne yaptığını doğru anlatır. 'oturum 12 saatte dolar' satırı bu turda YANLIŞA
    döndü — aktif pano artık dolmuyor. Yanlış bir yorum, yokluğundan daha pahalıdır."""
    src = (pathlib.Path(__file__).resolve().parent.parent
           / "meridian" / "web" / "app.js").read_text()
    assert "oturum 12 saatte dolar" not in src, (
        "app.js hâlâ sabit 12 saatlik pencereyi anlatıyor — kayan oturumdan sonra bu bir yalan")


# =================================================================================================
# 8) MALİYET — iddia değil ölçüm
# =================================================================================================
def test_tazeleyicinin_disk_maliyeti_OLCULDU(sandbox_state, monkeypatch):
    """MALİYET İDDİA EDİLMEZ, SAYILIR. Middleware HER isteğe girer; bedeli `api.py`de yazılı ve
    burada çivili. Bir gün biri `refresh_session`ı imza doğrulamasından önce dallandırırsa ya da
    tazelemeyi her isteğe yayarsa, sayı burada değişir ve yorum sessizce eskimemiş olur.

    Ölçü birimi `auth._read()` çağrısıdır (imza anahtarı `state/auth.json`dan gelir)."""
    auth.set_password(PAROLA)
    now = int(time.time())
    iat = now - 7 * 3600
    taze = auth.issue_session()                       # jetonlar SAYAÇTAN ÖNCE üretilir —
    tazelenecek = auth._sign(iat + 12 * 3600, iat)    # üretimin kendisi de auth.json okur
    c = _client(monkeypatch, None)
    sayac = {"n": 0}
    asil = auth._read
    monkeypatch.setattr(auth, "_read", lambda: (sayac.__setitem__("n", sayac["n"] + 1), asil())[1])

    c.get("/healthz")
    assert sayac["n"] == 0, (
        f"çerezsiz istekte auth.json {sayac['n']} kez okundu — statik varlık ve sağlık yoklaması "
        f"yolları bedelsiz sanılan bir G/Ç kazandı")

    sayac["n"] = 0
    assert c.get("/api/summary", headers=_cerezle(c, taze)).status_code == 200
    assert sayac["n"] == 2, (
        f"yarı-ömür içi çerezli istek {sayac['n']} okuma yapıyor (beklenen 2: tazeleyici + _auth)")

    sayac["n"] = 0
    assert c.get("/api/summary", headers=_cerezle(c, tazelenecek)).status_code == 200
    assert sayac["n"] == 3, (
        f"tazeleme anı {sayac['n']} okuma yapıyor (beklenen 3: ayrıştırma + imzalama + _auth)")
