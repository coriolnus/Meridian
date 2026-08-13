# Teşhis — beyin zincirinin birinci ayağı ERİŞİLEMEZ bir modele bağlı

**Tarih:** 2026-08-13 · **Rol-1 (Fable)** · **Sınıf:** "ayar yapıldı sanılıyor, ulaşılamıyor"
**Durum:** kök neden KANITLI · düzeltme OPERATÖRDE (sır deposu yazımı — ajan yetkisi dışında)

---

## 1. Bulgu

Operatör isteği (2026-08-13): *"tencent/hy3:free'yi nous birincil yap"*. İstek **ad düzeyinde
uygulandı** — `state/secrets.json` içinde `NOUS_MODEL = "tencent/hy3:free"`. Ama model
**hiçbir zaman cevap üretmedi**: son 24 saatte 33 çağrının **33'ü boş**, başarı **0**.

Uygulayan (Rol-1) modelin **erişilebilirliğini doğrulamadı**. Bu ölçüm o eksiği kapatıyor.

## 2. Kök neden — zincir, kanıtla

| Halka | Ölçülen değer | Kaynak |
|---|---|---|
| `NOUS_MODEL` | `tencent/hy3:free` | `secrets.get` canlıda |
| `NOUS_ENDPOINT` | `None` | `secrets.get` canlıda |
| `_nous_local()` | **True** (endpoint boş + hermes ikilisi var) | `meridian/hermes.py:1332` |
| Yerel hermes CLI sağlayıcısı | **`provider: gemini`** | `~/.hermes/config.yaml` canlıda |
| Sonuç | `--model tencent/hy3:free` **Gemini ucuna** gidiyor | — |
| Gerçekleşen | `API call failed after 3 retries: Gemini returned HTTP 404` | `state/agent_traces.jsonl` |

**Ve asıl kapanış:** `tencent/hy3:free` OpenRouter/Nous kimliği ister; canlıda

```
OPENROUTER_API_KEY = YOK
NOUS_API_KEY       = YOK
GEMINI_API_KEY     = VAR
```

Yani model **yapı gereği erişilemez** — yönlendirme düzeltilse bile onu servis edecek kimlik yok.

Bu, `meridian/hermes.py:504-505`'te 2026-07-26'da zaten yazılmış olan arızanın **tekrarı**:
*"zincirin iki ayağı (nous-yerel ve gemini) aynı üst-akış kotasına bakıyordu: yerel ajan
`model.provider=gemini` ile kuruluydu."* Ders kayıtlıydı, yeni model eklenirken uygulanmadı.

## 3. Maliyet — ölçülen

Son 24 saat, `agent_call` olaylarından:

| model | sonuç | n | toplam | ortalama |
|---|---|---:|---:|---:|
| `tencent/hy3:free` | **BOŞ** | 33 | **353,7 sn** | 10,7 sn |
| `gemini-flash-latest` | DOLU | 38 | 347,2 sn | 9,1 sn |
| `gemini-3.5-flash` | DOLU | 1 | 32,8 sn | 32,8 sn |

- Bütün çağrıların **%46'sı garantili başarısız**.
- Her LLM adımı, işe yarayan cevaba varmadan önce ~10,7 sn'yi 3 yeniden-denemeye harcıyor.
- Bu, operatörün bildirdiği "arayüz ağırlaştı / işlemci %52" tablosunun **bir bileşenidir**
  (tek sebebi olduğu iddia EDİLMEZ — ölçülmedi).
- Şu an tarihsel `llm_opinions` dolgusu koşuyor (2025-07 tarihlerinde) ve her seans 2 çağrı
  yapıyor; dolgu bitene kadar israf **doğrusal olarak birikir**.

## 4. Neden düzeltme operatörde

`NOUS_MODEL` `state/secrets.json`da yaşıyor. Ajanın sır deposuna yazması engellendi
(sınıflandırıcı kapısı — **doğru davranış**, bu depo operatörün). Değişiklik operatörün
kendi elinden geçmeli.

**TTL 300 sn** (`secrets.py:21`) → değişiklik **servis restart'ı GEREKTİRMEZ**, koşan worker
5 dakika içinde kendi okur. Sprint/pozisyon riski yok.

## 5. İki yol — operatör seçer

### Yol A — israfı durdur (geri alınabilir, 1 komut)

`NOUS_MODEL`i kaldır. Zincir `NOUS_FALLBACK_MODEL = gemini-flash-latest`e düşer.

```bash
ssh -i ~/.ssh/oci-a1.key ubuntu@130.61.126.87 'cd /opt/meridian && cp -p state/secrets.json backups/secrets.json.bak-$(date -u +%Y%m%dT%H%M%SZ) && .venv/bin/python -c "from meridian import secrets; secrets.delete(\"NOUS_MODEL\"); secrets.clear_cache(); print(\"NOUS_MODEL:\", secrets.get(\"NOUS_MODEL\"))"'
```

**BEYAN — bu bir ödünleşmedir, kazanç değil:** ardından `nous` ve `gemini` **aynı kimliğe**
gider (tek beyin). Bu, hafızadaki *beyin-zinciri* dersinin bilinen hâlidir. Ama bugünkü
gerçek de zaten budur: tencent 56 denemede 0 cevap ürettiği için **kaybedilen yetenek yok**,
yalnız kaybedilen zaman geri alınıyor.

### Yol B — istenen şeyi gerçekten kur (gerçek ikinci beyin)

`OPENROUTER_API_KEY` (veya `NOUS_API_KEY` + `NOUS_ENDPOINT`) tanımla. **Anahtarı yalnız
operatör girer** — ajan API anahtarı işlemez. Anahtar girildikten sonra yerel hermes CLI'nın
sağlayıcı yönlendirmesi de düzeltilmeli (`~/.hermes/config.yaml` → o model için
`provider: openrouter`), yoksa ad doğru olsa da istek yine Gemini'ye gider.

**Öneri:** önce A (israf bugün durur, geri alınabilir), sonra fırsat olunca B.

## 6. Açık kalan — kalıcı düzeltme (kod)

Bugünkü arıza **sessizce** yaşandı: sistem 33 kez 404 aldı ve bunu bir alarma çevirmedi.
`agent_call` olayında `unconfigured` alanı VAR ama bu vakada `false` basılıyor — yani
"model erişilemez" durumu **sınıflandırılmıyor**.

Kalıcı kapı önerisi (ROADMAP'e kalem): bir modelin üst üste N çağrıda %100 boş dönmesi
→ `model_unreachable` alarmı + o modeli zincirden **geçici düşürme** (soğuma defteri
`brain_cooldown.json` deseni zaten var, 429 için kurulu; 404/ölü-ad için kurulu DEĞİL).
Böylece "ad değişti ama ulaşılamıyor" sınıfı bir daha sessiz kalmaz.
