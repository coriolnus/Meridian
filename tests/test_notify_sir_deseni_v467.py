"""v467 — `meridian/notify.py::scrub` DESEN SÜZGECİ çivileri (TSK-012 açık kalem 1).

NUMARA SEÇİMİ: `ls tests | grep v467` BOŞ ölçüldü (2026-09-13); v468 alınmış, v467 serbestti.

ÖLÇÜLEN BOŞLUK. `scrub` bugüne kadar YALNIZ `secrets.ALLOWED` adlarının BİLİNEN değerlerini
maskeliyordu. Bilinmeyen/rotasyon-arası bir anahtar, bir hata dizgisindeki `Authorization:
Bearer …`, `?apikey=…` sorgu parametresi ya da URL'e gömülü parola OLDUĞU GİBİ dışarı çıkıyordu
(kalıcı kayıt: KEY/SECRET/PASS kara-listesi `DATABASE_URL`i kaçırdı, 2026-09-02). `scrub` bu
deponun dışarıya veri gönderen TEK süzgecidir — yalnız Telegram/webhook değil, arama korpusu
(`arama`), sohbet araç çıktısı (`sohbet`) ve denetçi istemi (`denetci_rota`) de ondan geçer.

NE ÇİVİLENİR:
  1. `_SIR_DESENLERI` tablosu: her satır AD + DERLENMİŞ desen taşır (ad çivilerin ve gelecek bir
     teşhisin okuduğu alandır — Yasa 6: okuyucusu bu dosyadır).
  2. Beş desenin HER BİRİ: sır maskelenir VE komşu metin korunur (bir alarm okunabilir kalmalı).
  3. Env satırı: değişken ADI TAM korunur, yalnız DEĞER maskelenir — ad sır değildir, hangi
     kimliğin sızdığını söyleyen tek bilgidir.
  4. Tırnaklı env değerinden sonra TIRNAK ARTIĞI kalmaz.
  5. NEGATİF KONTROL (bedel yasası): aşırı geniş bir desen alarm metnini okunmaz kılar —
     plan/tur kimlikleri, sha kısaltmaları, durum kodları, IP ve dağıtım numaraları DEĞİŞMEZ.
  6. `send()` yolu desen katmanından da geçer (bilinen-değer katmanı v34'te çivili; TEK-KAYNAK:
     burada o katman TEKRAR ölçülmez, `ALLOWED` bilerek boşaltılır).
  7. Maskeleme `obs` olayı ÜRETMEZ: `scrub` saf fonksiyondur (`notify` `obs`u yalnız `send`/
     `inbox` içinde, tembel olarak ithal eder — ölçüldü).

GERÇEK SIR KULLANILMAZ: aşağıdaki dizgeler sırların BİÇİMİDİR, kendileri değil.
"""
from __future__ import annotations

import re

import pytest

from meridian import notify

# ---------------------------------------------------------------------------------------------
# Sentetik sır BİÇİMLERİ — hiçbiri gerçek değildir, hiçbiri `secrets.ALLOWED` yolundan gelmez.
# ---------------------------------------------------------------------------------------------
OPENROUTER = "sk-or-v1-" + "a1b2c3d4" * 8            # 64 onaltılık karakter (gerçek biçim)
BEARER = "eyJhbGciOiJIUzI1NiJ9.PAYLOADPAYLOAD.SIGSIG"
SORGU_DEGERI = "abcdef1234567890"
PAROLA = "hunter2parola"
ENV_DEGERI = "abcdefgh12345678"

#: Maskelenmemesi ÖLÇÜLEN metin: alarm satırlarının gerçek sözlüğü (plan kimliği, tur jetonu,
#: sha kısaltması, HTTP durum kodu, A1 adresi, dağıtım sayacı, çivi numarası).
#: SEMBOL LİSTESİ NEGATİF KONTROLDEDİR (inceleme bulgusu 5, 2026-09-13): alarm metinlerinin en
#: sık taşıdığı dizge virgüllü bir sembol listesidir (`AAPL,MSFT,NVDA`) ve hiçbir desen ona
#: yapısal olarak dokunamaz (env deseni `AD=`/`AD:` önek+değer ister, url_sorgu `?param=`).
#: Risk teorik değil SIFIRDIR — ama süzgeç bir gün genişletilirse KAYIP sessiz olurdu; bedelin
#: adı çividir.
NEGATIF_KONTROL = ("T00901 · P-2026-09-13-AAPL-1 · sha 7eb8476 · healthz 503 · "
                   "130.61.126.87 · dagitim #41 · v447 · AAPL,MSFT,NVDA · "
                   "evren=AAPL,MSFT,TSLA,NVDA,AMZN")


@pytest.fixture
def yalniz_desen(monkeypatch):
    """BİLİNEN-DEĞER katmanını KAPATIR: `ALLOWED` boş, `get` hep None. Böylece aşağıdaki her
    maskeleme YALNIZ desen katmanının eseridir — iki katman aynı çivide karışmaz (ve çivi
    operatörün gerçek sır deposunu hiç okumaz)."""
    monkeypatch.setattr(notify.secrets, "ALLOWED", [], raising=False)
    monkeypatch.setattr(notify.secrets, "get", lambda n, *a, **k: None)


# ---------------------------------------------------------------------------------------------
# 1. TABLO SÖZLEŞMESİ
# ---------------------------------------------------------------------------------------------
def test_desen_tablosu_ad_ve_derlenmis_desen_tasir():
    """Tablo modül sabitidir; her satırın ADI ve DERLENMİŞ deseni vardır. Ad, çivilerin
    parametrizasyonunu ve bir gün bir teşhisin 'hangi desen ısırdı' sorusunu besler."""
    tablo = notify._SIR_DESENLERI
    assert isinstance(tablo, tuple) and len(tablo) == 5, tablo
    adlar = [satir[0] for satir in tablo]
    assert len(set(adlar)) == len(adlar), f"desen adı tekrarlıyor: {adlar}"
    for satir in tablo:
        ad, desen = satir[0], satir[1]
        assert isinstance(ad, str) and ad, satir
        assert isinstance(desen, re.Pattern), f"{ad}: desen derlenmemiş ({type(desen)})"


# ---------------------------------------------------------------------------------------------
# 2. BEŞ DESEN × (maskelenir + komşu metin korunur)
# ---------------------------------------------------------------------------------------------
@pytest.mark.parametrize("ad,kirli,sizan,korunan", [
    ("openrouter",
     f"401 Unauthorized — OpenRouter anahtarı {OPENROUTER} reddedildi (retry 3)",
     OPENROUTER,
     ("401 Unauthorized", "OpenRouter", "(retry 3)")),
    ("bearer",
     f"httpx.HTTPStatusError: headers={{'Authorization': 'Bearer {BEARER}'}} → 401",
     BEARER,
     ("httpx.HTTPStatusError", "→ 401")),
    ("url_sorgu",
     f"GET https://api.example.test/v3/quote?symbol=AAPL&token={SORGU_DEGERI} → 429",
     SORGU_DEGERI,
     ("https://api.example.test/v3/quote", "symbol=AAPL", "→ 429")),
    ("url_kimlik",
     f"OperationalError: postgresql://meridian:{PAROLA}@db.internal:5432/meridian kapalı",
     PAROLA,
     ("postgresql://", "db.internal:5432/meridian", "kapalı")),
    ("env_satiri",
     f"birim dökümü: ALPACA_PAPER_SECRET={ENV_DEGERI} · sonraki satır",
     ENV_DEGERI,
     ("birim dökümü:", "ALPACA_PAPER_SECRET", "· sonraki satır")),
])
def test_bes_desen_maskeler_ve_komsu_metni_korur(yalniz_desen, ad, kirli, sizan, korunan):
    """Her desen için İKİ hüküm birden: sır ÇIKMAZ ve metnin geri kalanı OKUNUR kalır.
    Yalnız birincisi ölçülseydi `return '***'` de çiviyi geçerdi."""
    temiz = notify.scrub(kirli)
    assert sizan not in temiz, f"{ad}: sır maskelenmedi → {temiz!r}"
    assert "***" in temiz, f"{ad}: maske işareti yok → {temiz!r}"
    for parca in korunan:
        assert parca in temiz, f"{ad}: komşu metin kayboldu ({parca!r}) → {temiz!r}"


def test_bearer_oneki_korunur(yalniz_desen):
    """`Bearer ***` — önek SİLİNMEZ: hangi kimlik sınıfının sızdığı okunabilir kalmalı."""
    temiz = notify.scrub(f"Authorization: Bearer {BEARER}")
    assert temiz == "Authorization: Bearer ***", temiz


def test_url_sorgu_parametre_ADI_korunur(yalniz_desen):
    """`?apikey=***` — parametre ADI kalır, DEĞER gider: hangi anahtarın sızdığı görülebilmeli."""
    temiz = notify.scrub(f"https://x.test/y?apikey={SORGU_DEGERI}&sembol=AAPL")
    assert temiz == "https://x.test/y?apikey=***&sembol=AAPL", temiz


def test_url_kimligi_kullanici_ve_parolayi_birlikte_maskeler(yalniz_desen):
    """URL-gömülü kimlikte KULLANICI ADI da maskelenir: `DATABASE_URL` vakasında sızan çift
    kullanıcı+paroladır ve kullanıcı adı tek başına da bir kimliktir."""
    temiz = notify.scrub(f"postgresql://meridian:{PAROLA}@db.internal:5432/meridian")
    assert temiz == "postgresql://***:***@db.internal:5432/meridian", temiz


# ---------------------------------------------------------------------------------------------
# 3-4. ENV SATIRI: AD TAM KORUNUR · TIRNAK ARTIĞI KALMAZ
# ---------------------------------------------------------------------------------------------
@pytest.mark.parametrize("ad", ["ALPACA_PAPER_SECRET", "TELEGRAM_BOT_TOKEN",
                                "OPENROUTER_API_KEY", "HINDSIGHT_RETAIN_TOKEN"])
def test_env_satiri_degisken_adini_TAM_korur(yalniz_desen, ad):
    """AD SIR DEĞİLDİR — hangi kimliğin sızdığını söyleyen TEK bilgidir ve rotasyon kararı ona
    bakar. Maskelenen yalnız DEĞERDİR."""
    temiz = notify.scrub(f"{ad}={ENV_DEGERI}")
    assert temiz == f"{ad}=***", temiz


@pytest.mark.parametrize("kirli", [
    'TELEGRAM_BOT_TOKEN="abcdefgh1234"',
    "TELEGRAM_BOT_TOKEN='abcdefgh1234'",
])
def test_tirnakli_env_degerinden_sonra_tirnak_artigi_kalmaz(yalniz_desen, kirli):
    """Tırnaklı değerde kapanış tırnağı DEĞER GRUBUNA dahildir: artık bir `"` kalırsa metin
    bozulur ve 'maskelendi mi' sorusu gözle okunamaz hâle gelir."""
    temiz = notify.scrub(kirli)
    assert temiz == "TELEGRAM_BOT_TOKEN=***", temiz
    assert '"' not in temiz and "'" not in temiz, temiz


@pytest.mark.parametrize("ayirac", ["=", ": ", " = ", ":", " : "])
def test_env_satiri_AYIRACI_KORUR(yalniz_desen, ayirac):
    """AYIRAÇ DEĞİŞMEZ (inceleme bulgusu 4, 2026-09-13). Desen hem `=` hem `:` kabul ediyordu ama
    değişim her zaman `=` yazıyordu: `HINDSIGHT_API_KEY: …` satırı `HINDSIGHT_API_KEY=***` olarak
    çıkıyor ve JSON/YAML dökümü maskelendikten sonra o BİÇİMİ KAYBEDİYORDU. Sızıntı yok, ama
    maskelenmiş metin hâlâ ORİJİNALİN OKUNABİLİR HÂLİ olmalıdır: operatör bir birim dökümüyle bir
    JSON gövdesini ayırt edebilmeli. Ayıracın çevresindeki boşluk da korunur."""
    temiz = notify.scrub(f"HINDSIGHT_API_KEY{ayirac}{ENV_DEGERI}")
    assert temiz == f"HINDSIGHT_API_KEY{ayirac}***", temiz


def test_kisa_env_degeri_maskelenmez_OLCULEN_SINIR(yalniz_desen):
    """Sekiz karakterden KISA değer sır sayılmaz (bilinen-değer katmanının ≥8 eşiğiyle aynı):
    `TELEGRAM_CHAT_ID=42` gibi satırlar okunur kalmalı."""
    assert notify.scrub("TELEGRAM_BOT_TOKEN=kisa") == "TELEGRAM_BOT_TOKEN=kisa"


def test_desen_disi_ad_maskelenmez_OLCULEN_BOSLUK(yalniz_desen):
    """ÖLÇÜLEN SINIR, gizlenmiş değil BEYAN EDİLMİŞ boşluk: env deseni yalnız BEYAN EDİLEN
    önekleri (ALPACA·OPENROUTER·NOUS·TELEGRAM·MERIDIAN·HINDSIGHT) tanır. Öneksiz bir ad
    (`X_KEY=…`) bu katmandan GEÇER — desen o adları da kapsayacak kadar genişletilirse
    (`[A-Z_]*KEY=`) alarm metnindeki her büyük-harfli alan maskelenmeye aday olur ve bedel
    okunabilirliktir. Genişletme AYRI bir karardır; bu çivi kararın bugünkü hâlini GÖRÜNÜR kılar."""
    assert notify.scrub(f"X_KEY={ENV_DEGERI}") == f"X_KEY={ENV_DEGERI}"


# ---------------------------------------------------------------------------------------------
# 5. NEGATİF KONTROL — BEDEL YASASI
# ---------------------------------------------------------------------------------------------
def test_negatif_kontrol_listesi_degismez(yalniz_desen):
    """Alarm metninin GERÇEK sözlüğü maskelenmez. Bu çivi kırılırsa kazanılan gizlilik değil,
    kaybedilen okunabilirliktir — ve o kayıp sessiz olurdu."""
    assert notify.scrub(NEGATIF_KONTROL) == NEGATIF_KONTROL


@pytest.mark.parametrize("zararsiz", [
    "zararsız metin",
    "Bearer token eksik — başlık hiç kurulmadı",
    "https://api.example.test/v3/quote?symbol=AAPL&limit=30",
    "rsync://arsiv.local/olaylar tamam",
    "devre kesici: günlük kayıp -2.30% — yeni giriş durdu",
])
def test_zararsiz_metin_dokunulmadan_gecer(yalniz_desen, zararsiz):
    """Süzgecin yanlış-pozitifi ölçülür: sır BİÇİMİ taşımayan satır bit-bit aynı çıkar."""
    assert notify.scrub(zararsiz) == zararsiz


# ---------------------------------------------------------------------------------------------
# 6. send() YOLU
# ---------------------------------------------------------------------------------------------
def test_send_desen_sirrini_da_maskeler(monkeypatch):
    """Gönderim yolu desen katmanından GEÇER. (Bilinen-değer katmanının send çivisi v34'tedir —
    TEK-KAYNAK: burada tekrarlanmaz, ölçülen YENİ katmandır.)"""
    giden = {}
    monkeypatch.setattr(notify.secrets, "ALLOWED", [], raising=False)
    monkeypatch.setattr(notify.secrets, "get", lambda n, *a, **k: {
        "TELEGRAM_BOT_TOKEN": "bot-jetonu", "TELEGRAM_CHAT_ID": "42"}.get(n))
    monkeypatch.setattr(notify, "_post",
                        lambda url, payload, timeout=8.0: giden.update(payload) or True)
    assert notify.send(f"veri sağlayıcı 401: {OPENROUTER} · Bearer {BEARER}") is True
    assert OPENROUTER not in giden["text"], giden["text"]
    assert BEARER not in giden["text"], giden["text"]
    assert "veri sağlayıcı 401" in giden["text"], giden["text"]


# ---------------------------------------------------------------------------------------------
# 7. SAF FONKSİYON — obs olayı YOK
# ---------------------------------------------------------------------------------------------
def test_scrub_obs_olayi_uretmez(sandbox_state, yalniz_desen):
    """Maskeleme KAYIT ÜRETMEZ. Gerekçe ölçüldü: `notify` `obs`u modül düzeyinde ithal etmez
    (yalnız `send`/`inbox` içinde, tembel). Bir maskeleme olayı yazılsaydı, sırrı taşıyan metnin
    varlığı hakkında bir iz defterde kalır ve `scrub`ın saflığı (arama korpusu ve sohbet araç
    çıktısı onu satır satır çağırır) kaybolurdu."""
    from meridian import config
    defter = config.STATE / "events.jsonl"
    once = defter.read_bytes() if defter.exists() else b""
    notify.scrub(f"ALPACA_PAPER_SECRET={ENV_DEGERI} · Bearer {BEARER}")
    sonra = defter.read_bytes() if defter.exists() else b""
    assert sonra == once, "scrub olay yazdı — saf fonksiyon değil"
