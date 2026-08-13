# Kurulum — OpenRouter ile GERÇEK ikinci beyin (`tencent/hy3:free`)

**Tarih:** 2026-08-14 · **Rol-1 (Fable)** · **Ön okuma:** `docs/TESHIS-BEYIN-ZINCIRI-ERISILEMEZ-MODEL-2026-08-13.md`
**Durum:** yol KEŞFEDİLDİ ve kodda doğrulandı · **anahtar girişi OPERATÖRDE** (ajan API anahtarı işlemez)

---

## 0. Neden bugün çalışmıyor (tek cümle)

`NOUS_MODEL = tencent/hy3:free` ayarlandı ama onu servis edecek **hiçbir kimlik yoktu**
(`OPENROUTER_API_KEY` yok, `NOUS_API_KEY` yok) ve istek Gemini ucuna gidip **HTTP 404** aldı.
24 saatte 33 çağrının 33'ü boş, 354 sn israf.

## 1. Ölçülen gerçek: sistemde İKİ ayrı beyin yolu var

Bu ayrım kritik — tek bir ayar ikisini birden düzeltmiyor.

| | **Yol A — öneri beyni** | **Yol B — ajan çağrısı** |
|---|---|---|
| kod | `hermes._propose_nous` → `_nous_text` (hermes.py:2211) | `hermes._agent_call` → yerel `hermes` CLI (hermes.py:1872) |
| taşıma | doğrudan HTTPS, OpenAI-uyumlu | alt süreç, `--model` bayrağı |
| **araç/skill kullanabilir mi** | **HAYIR** | **EVET** (`-s` ön-yükleme — skill katmanının tek yolu) |
| bugünkü israfı yapan | — | **EVET** (33 boş çağrı buradan) |
| OpenRouter'a hazır mı | **EVET, kod değişikliği YOK** | hayır — `--provider` geçilmiyor |

**Yol A neden hazır:** `_nous_text` tam olarak OpenRouter'ın sözleşmesini konuşuyor —
`POST {base}/chat/completions` · `Authorization: Bearer <anahtar>` · gövde `{model, max_tokens,
messages:[system,user]}`. Uç adresi `NOUS_ENDPOINT`ten okunuyor. Yani **üç sır** yeter.

**Yol B neden hazır değil:** `_agent_chat_cmd` (hermes.py:1836) CLI'ya yalnız `--model`
geçiyor; CLI'nın kendi yapılandırması `model.provider: gemini` olduğu için slug Gemini'ye
gidiyor. CLI `--provider` bayrağını **destekliyor** (`hermes chat --provider ...`) ve
OpenRouter'ı **birinci sınıf sağlayıcı olarak tanıyor** (`hermes config show` → `OpenRouter (not set)`).

## 2. Operatör adımları

### Adım 1 — OpenRouter anahtarı (YALNIZ OPERATÖR)

openrouter.ai'den anahtar al. **Ajan anahtar girmez, görmez, taşımaz.** İki yere gerekiyor
(aynı anahtar):

**(a) Meridian sır deposu — Yol A'yı açar.** Panodan *Ayarlar → Sırlar* ekranından, ya da:

```bash
ssh -i ~/.ssh/oci-a1.key ubuntu@130.61.126.87
cd /opt/meridian && .venv/bin/python -c "from meridian import secrets; secrets.set('NOUS_API_KEY', input('OpenRouter anahtari: ')); secrets.set('NOUS_ENDPOINT', 'https://openrouter.ai/api/v1'); secrets.clear_cache(); print('tamam')"
```

`NOUS_MODEL` zaten `tencent/hy3:free` — dokunma. TTL 300 sn, **restart gerekmez**.

**(b) hermes CLI kimlik dosyası — Yol B'nin ön şartı.** `/home/ubuntu/.hermes/.env`
dosyasına `OPENROUTER_API_KEY=<anahtar>` satırını ekle (dosyada şu an yalnız `GEMINI_API_KEY` var).

### Adım 2 — Yol A doğrulaması (anahtar girildikten hemen sonra)

```bash
ssh -i ~/.ssh/oci-a1.key ubuntu@130.61.126.87 'cd /opt/meridian && .venv/bin/python -c "from meridian import hermes; print(hermes._nous_local()); print((hermes._nous_text(\"iki kelimeyle merhaba de\", note=\"kurulum-sinama\") or \"BOS\")[:120])"'
```

Beklenen: birinci satır `False` (uzak uca geçildi), ikinci satır **dolu bir cevap**.
`False` gelmiyorsa `NOUS_ENDPOINT` yazılmamıştır.

### Adım 3 — Yol B: ⛔ UCUZ YOL DENENDİ ve ÇÜRÜDÜ → kod turu ZORUNLU

**Hipotez (benim tahminim):** CLI'nın `--provider` varsayılanı `auto` olduğuna göre,
yapılandırmadaki sabit `gemini`yi `auto`ya çekmek slug'a göre yönlendirmeyi açar ve kod
değişikliği gerekmez.

**ÖLÇÜM (2026-08-13 21:12Z, canlı) — HİPOTEZ ÇÜRÜDÜ:**

```
hermes config set model.provider auto          → ✓ Set model.provider = auto
hermes chat --model tencent/hy3:free           → HTTP 401: Missing Authentication header
hermes chat --model gemini-flash-latest        → HTTP 401: Missing Authentication header   ← ÇALIŞAN YOL DA KIRILDI
```

`auto`, slug'a göre yönlendirmiyor; **hiçbir kimliğe bağlanamıyor** ve auth başlığı hiç
göndermiyor. Yani ucuz yol yalnız işe yaramamakla kalmıyor, **mevcut çalışan Gemini ayağını
da düşürüyor**.

**GERİ ALINDI ve DOĞRULANDI** (aynı dakika): `hermes config set model.provider gemini` →
`gemini-flash-latest` yine dolu cevap veriyor. Kırık pencere ~50 saniye sürdü ve o aralıkta
**hiçbir üretim çağrısı yapılmadı** (son `agent_call` 13 dakika öncesineydi) — canlı etkilenmedi.

**DERS (bu belgenin en pahalı satırı):** karşı-sınama (`gemini bozulmadı mı`) **aynı komutta**
koşulduğu için arıza 50 saniyede yakalandı. Tek başına "tencent çalıştı mı" sorulsaydı,
cevap "hayır" olurdu ve **çalışan ayağın da düştüğü fark edilmezdi** — beyin zinciri gece
boyunca kapalı kalırdı. Sağlayıcı/model yönlendirmesi değiştiren her denemede karşı-sınama
ŞARTTIR.

**Kalan tek yol — dar kod turu (Rol-1 brief'ler, Opus uygular):** `_agent_chat_cmd`
(`meridian/hermes.py:1836`) CLI komutunu kuran TEK yerdir; model kimliği slash içeriyorsa
(OpenRouter slug biçimi) komuta `--provider openrouter` eklenmeli. `model.provider: gemini`
yapılandırmada **DEĞİŞMEDEN kalır** — böylece gemini ayağı bugünkü davranışını korur.
Doğrulama, yine iki yönlü: tencent dolu cevap **ve** gemini bozulmamış.

**Not — `.hermes/.env` kontrolü:** `hermes config show` çıktısında `OpenRouter` satırı
`(not set)` yerine maskeli bir değer göstermeli. Yer tutucu metin (`BURAYA_ANAHTAR` gibi)
yazıldıysa satır dolu **görünür ama 401 verir** — maskeli değerin gerçek anahtarın son
karakterleri olduğu doğrulanmalı.

## 3. Bilinmesi gereken sınır — ücretsiz katman kotası

`tencent/hy3:free` **ücretsiz** katmandır ve OpenRouter ücretsiz modellerde günlük istek
tavanı uygular. Meridian'ın kendi bütçesi `MERIDIAN_AGENT_RPD = 150` istek/gün
(`hermes.py`, `AGENT_RPD`). **Bu iki tavanın hangisinin önce dolduğu ÖLÇÜLMEDİ** — kurulum
sonrası ilk gün `agent_call` olaylarında 429/kota sınıfı aranmalı. Kota tavanı bizimkinden
düşükse `AGENT_RPD` ona çekilir; sistemin 429 için **soğuma defteri zaten var**
(`brain_cooldown.json`), yani kota dolarsa sessiz bozulma olmaz, geri çekilir.

## 4. Ne kazanılıyor — ve ne kazanılmıyor

**Kazanılan:** gerçekten **bağımsız** bir ikinci beyin. Bugüne kadar `nous` ve `gemini` aynı
Gemini kimliğine gidiyordu (hafıza: *beyin zinciri ölçümü*) — tek bir 429 iki ayağı birden
düşürüyordu. OpenRouter ayrı sağlayıcı, ayrı kota: zincir **ilk kez gerçekten yedekli** olur.

**Kazanılmayan — beyan:** ikinci beynin **kalitesi ölçülmedi**. `tencent/hy3:free` bu iş
yükünde (JSON şemalı hipotez üretimi + skill çağrısı) ne kadar iyi, bilinmiyor. Kurulduktan
sonra ölçülecek şey `same_model_ids`in boşalması DEĞİL — o ölçüt bugün zaten yanıltmıştı
(bkz. hafıza düzeltmesi) — **dolu-cevap oranı ve şema-geçerlilik oranıdır**.

**Ayrıca:** Yol B açılana kadar `_agent_call` israfı sürer. İsraf bugün ölçüldü: günde
~33 boş çağrı, ~354 sn. Yol A tek başına bunu **durdurmaz**.
