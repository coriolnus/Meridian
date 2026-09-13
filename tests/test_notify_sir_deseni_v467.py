"""test_notify_sir_deseni_v467.py — `notify.scrub` DESEN süzgeci (TSK-012).

NUMARA SEÇİMİ: `ls tests | grep -oE "v[0-9]{2,}"` içinde v467/v466/v468 hiçbiri yoktu (ölçüldü,
bu tur) — çakışma yok.

NEDEN VAR (inceleme K-notu, 2026-09-08; kalıcı kayıt "sir-suzgeci-url-gomulu-parola"): `scrub()`
yalnız `secrets.ALLOWED`teki BİLİNEN adların BİLİNEN DEĞERİNİ maskeliyordu. Bir KEY/SECRET/PASS
kara-listesi `DATABASE_URL` gibi bir adı kaçırdığı gibi, rotasyon-arası/hiç-ayarlanmamış bir
anahtar da, bir hata dizgisinin taşıdığı `Authorization: Bearer …` de, bir `?apikey=…` sorgu
parametresi de, URL'e gömülü `kullanici:parola@` de bu modülün TEK çıkış kapısından (`send`)
OLDUĞU GİBİ geçerdi — `notify` dışarıya veri gönderen TEK yoldur.

NEYİ ÇİVİLER (beş ayrı sınıf, `notify._SIR_DESENLERI`):
  1. OpenRouter anahtarı (`sk-or-v1-` + 64 hex)
  2. `Authorization: Bearer <jeton>` başlığı
  3. URL sorgu parametresi (`?apikey=…` / `&token=…` vb.)
  4. URL'e gömülü kimlik (`://kullanici:parola@`)
  5. env satırı sızıntısı (`ALPACA_..._SECRET=değer` biçiminde bir hata/log dökümü)

Her sınıf İKİ yönden ölçülür: DEĞER maskelenir + KOMŞU METİN (öncesi/sonrası) KORUNUR — ikincisi
olmadan "hepsini `***` yap" gibi aşırı geniş bir desen de aynı testten geçerdi (bedel yasası).

NEGATİF KONTROL (tek test, beş desenin TAMAMINA karşı): görev kimliği (`T00901`), plan kimliği
(`P-2026-…`), sha kısaltması, HTTP durum kodu ve çıplak bir IP hiçbirini TETİKLEMEZ — desen
GENİŞLETİLMEZ kararının (bedel yasası) canlı kanıtı budur.

`send()` YOLU AYRICA ÇİVİLENMEZ: `send()` zaten her zaman `scrub()`tan geçiyordu (bu turdan
ÖNCE de) ve bu yol `tests/test_notify_obs_audit_v34.py::test_n1b_send_scrubs_the_payload`
tarafından ÇİVİLİ. Aynı iddiayı iki dosyada tutmak, tek bir bayatlamayı iki kırmızıya çevirirdi
(v382 dersi) — burada TEKRAR YAZILMAZ, yalnız İTHAL EDİLİR (bu dosya çalıştığında o test de
suite'in bir parçasıdır, ayrıca çağrılmaz).

OBS OLAYI YOK — ÖLÇÜLDÜ VE BİLİNÇLİ KARAR: `notify.py`nin üst-düzey importları `obs` İÇERMEZ
(yalnız `send()` teslimat-hatası dalı GECİKMELİ import eder, döngüsel import kaçışı). `scrub()`
saf bir metin fonksiyonu olarak KALIR — maskeleme bir `obs` olayı ÜRETMEZ, dolayısıyla bu dosyanın
hiçbir testi `sandbox_state` İSTEMEZ (gerçek `state/`e dokunacak hiçbir yan etki yok)."""
from __future__ import annotations

from meridian import notify


# ---------------------------------------------------------------------------------------------
# 1-5. BEŞ DESEN — DEĞER maskelenir + KOMŞU METİN korunur
# ---------------------------------------------------------------------------------------------

def test_openrouter_anahtari_maskelenir_komsu_metin_korunur():
    anahtar = "sk-or-v1-" + ("0123456789abcdef" * 4)
    out = notify.scrub(f"nous düşüş zinciri denedi: key={anahtar} 429 aldı")
    assert anahtar not in out
    assert "key=***" in out
    assert out.startswith("nous düşüş zinciri denedi: ")
    assert out.endswith(" 429 aldı")


def test_bearer_basligi_maskelenir_komsu_metin_korunur():
    out = notify.scrub("istek başlığı reddedildi: Authorization: Bearer abcDEF1234567890xyz — 401")
    assert "abcDEF1234567890xyz" not in out
    assert "Authorization: Bearer ***" in out
    assert out.startswith("istek başlığı reddedildi: ")
    assert out.endswith(" — 401")


def test_url_sorgu_parametresi_maskelenir_komsu_parametre_korunur():
    out = notify.scrub(
        "hata: GET https://api.example.com/v1/data?token=abcdef1234567890&user=42 → 500")
    assert "abcdef1234567890" not in out
    assert "?token=***&user=42" in out, out
    assert out.startswith("hata: GET https://api.example.com/v1/data?token=***")
    assert out.endswith(" → 500")


def test_url_gomulu_kimlik_maskelenir_host_korunur():
    out = notify.scrub("yedek DB bağlantısı: postgres://opuser:s3cr3tPW@db.internal:5432/meridian koptu")
    assert "opuser" not in out and "s3cr3tPW" not in out
    assert "postgres://***:***@db.internal:5432/meridian" in out, out
    assert out.startswith("yedek DB bağlantısı: ")
    assert out.endswith(" koptu")


def test_env_satiri_sizintisi_maskelenir_govde_korunur():
    out = notify.scrub("ENV DUMP: ALPACA_PAPER_SECRET=abcd1234efgh sistemde bulundu")
    assert "abcd1234efgh" not in out
    # Değişken ADI sır DEĞİLDİR ve bilgi taşır (hangi kimlik sızdı): tam ad KORUNUR, yalnız değer
    # maskelenir (inceleme bulgusu 1, 2026-09-13 — ilk sürüm adı `ALPACA=***`e kırpıyordu).
    assert "ALPACA_PAPER_SECRET=***" in out, out
    assert "ALPACA=***" not in out, out
    assert out.startswith("ENV DUMP: ")
    assert out.endswith(" sistemde bulundu")


# ---------------------------------------------------------------------------------------------
# 6. NEGATİF KONTROL — beş desenin TAMAMI birden ölçülür
# ---------------------------------------------------------------------------------------------

def test_negatif_kontrol_gorev_plan_sha_healthz_ip_DEGISMEZ():
    """Desen GENİŞLETİLMEZ kararının (bedel yasası) canlı kanıtı: görev kimliği, plan kimliği,
    sha kısaltması, HTTP durum kodu ve çıplak IP hiçbir deseni TETİKLEMEZ."""
    metin = "T00901 · P-2026-09-13-AAPL-1 · sha 7eb8476 · healthz 503 · 130.61.126.87"
    assert notify.scrub(metin) == metin


# ---------------------------------------------------------------------------------------------
# 7. MUTASYON KANITI İÇİN ÇAPA — desen tablosunun VARLIĞI
# ---------------------------------------------------------------------------------------------

def test_sir_desenleri_tablosu_bes_giris_tasir():
    """`_SIR_DESENLERI` tam beş girişlidir — mutasyon kanıtının hedefi budur: bir girişi silmek
    ilgili yukarıdaki testi kırmızı yapar (rapor: `.../scratchpad/tsk012/rapor_tsk012.md`)."""
    assert len(notify._SIR_DESENLERI) == 5
    adlar = {ad for ad, _ in notify._SIR_DESENLERI}
    assert adlar == {"openrouter", "bearer", "url_sorgu", "url_kimlik", "env_satiri"}
