# WP7-24b ölçümü — SOUL kilidi HÂLÂ SINANMADI, ama teşhis DEĞİŞTİ

**Tarih:** 2026-08-14 · **Rol-1 (Fable)** · **Kalem:** ROADMAP WP7 / 24b ("SOUL kilidi açıldı ama HİÇ SINANMADI")
**Sonuç:** 24b **AÇIK KALIR** — ama artık *neden* sınanamadığı ve *hangi enstrümanla* sınanacağı ölçülü.

---

## 1. Önce enstrüman sorunu: Meridian kendi defterinden bunu ÖLÇEMİYOR

| ölçüm | sonuç |
|---|---|
| `agent_call` olaylarında `tool_calls` | **926/926 = −1** (yani "bilinmiyor") |
| `agent_traces.jsonl` ham stdout/stderr'da araç izi | **0/300 satır** |

Sebep kodda ZATEN yazılı (`hermes.py`, `_agent_tool_calls` çevresi): sayaç CLI'nın **oturum
özetinden** ayrıştırılıyor, ama biz `-Q` bayrağını geçiyoruz ve `-Q` tam olarak o özeti
bastırıyor. Yani **`tool_calls = −1` YAPISALDIR** — JSON ayrıştırması için gereken bayrak,
araç sayacını yok ediyor. İki gereksinim çatışıyor ve bugün sessizce ikincisi kaybediyor.

**Bu bir "veri yok" hâli değil, bir "veri var sanılıyor" hâlidir:** alan defterde duruyor,
her satırda dolu görünüyor, ve hep aynı şeyi söylüyor.

## 2. Enstrüman NEREDE var: CLI'nın kendi döküm deposu

`~/.hermes/sessions/` altında **1.036 `request_dump_*.json`**. Bunlar *başarılı oturum* değil,
**hata dökümleridir** (`reason` + `error` alanları). Ama modele gönderilen mesaj geçmişini
taşıdıkları için, modelin DAHA ÖNCE yaptığı araç çağrıları içlerinde görünür.

**Ölçülen: 202 mesaj gerçek `tool_calls` taşıyor.** Yani model araç KULLANIYOR.

⚠ TUZAK (v242'nin testi tam bunu uyarıyor, `tests/test_skill_cagri_izi_v242.py:19`): bu
dosyalarda ham metin olarak `skill_view` aramak **1.950/gün** gibi sayılar verir — çünkü her
istekte 18 aracın TANIMI gönderiliyor. Tanım ≠ çağrı. Aşağıdaki sayılar `messages[].tool_calls`
üzerinden, yani gerçek çağrılardan.

## 3. ASIL BULGU — model araç kullanıyor ama SKILL araçlarını değil

| araç | çağrı | pay |
|---|---:|---:|
| `search_files` | 129 | **%63,9** |
| `read_file` | 43 | %21,3 |
| `execute_code` | 31 | %15,3 |
| **`skill_view`** | **5** | **%2,5** |
| `session_search` | 3 | %1,5 |
| `terminal` · `skills_list` | 1 + 1 | %1,0 |

**Teşhis değişiyor.** Bugüne kadarki okuma "SOUL yasağı katalogu kilitledi, model araç
çağıramıyor"du. Ölçüm bunu **kısmen çürütüyor**: model 202 kez araç çağırmış — kilitli değil.
Kilitli olan **skill yolu**: model bilgiye `skill_view` ile değil, **ham dosya aramasıyla**
(`search_files` + `read_file` = %85) gidiyor.

Bu farklı bir sorundur ve farklı bir çözüm ister: yasağı kaldırmak (2026-08-13'te yapıldı)
gerekli olabilir ama **yeterli değil** — model, katalog varken bile ham aramayı tercih ediyor.
Muhtemel nedenler ÖLÇÜLMEDİ (hipotez): `skill_view`ın araç açıklaması zayıf · `-s` ile
ön-yüklenen içerik zaten yeterli geliyor · ham arama daha "tanıdık" bir refleks.

## 4. SOUL düzeltmesi neden hâlâ sınanmadı

2026-08-13 gününde döküm sayısı 79, **gerçek araç çağrısı 0**. Bu "düzeltme işe yaramadı"
DEĞİLDİR — o gün model **hiç cevap veremiyordu**: aynı günün dökümlerinde 550 kez
`gemini_model_not_found HTTP 404` ve bunların 527'si `tencent/hy3:free`.

**Yani SOUL düzeltmesi bir kesintinin içine indi.** Düzeltme 2026-08-13'te yapıldı, model aynı
gün ulaşılamaz durumdaydı, ve ulaşılabilir hâle gelmesi (OpenRouter yönlendirmesi, v244)
gecenin sonunda oldu. Sınama için **düzeltme sonrası ilk tam öğrenme penceresi** gerekiyor.

Döküm deposunun tarihsel özeti, bu gece bulunan iki arızayı da bağımsız olarak doğruluyor:

| hata | n | model |
|---|---:|---|
| `gemini_model_not_found` (404) | 550 | `tencent/hy3:free` 527 |
| `gemini_rate_limited` (429) | 478 | `gemini-3.5-flash` 481 |
| 401 / 400 / 503 | 8 | (biri bu gecenin bozuk-anahtar denemesi) |

25 nemotron dökümünün tamamı **v244 ÖNCESİNE** ait ve hepsi `Gemini returned HTTP 404` —
yani sağlayıcı yönlendirmesi düzelmeden önceki çağrılar. Düzeltmeden sonra yeni döküm YOK
(dökümler yalnız HATADA yazıldığı için bu olumlu bir işarettir, ama tek başına kanıt değildir).

## 5. Hüküm

- **24b AÇIK KALIR.** "Sınanmadı" hükmü korunur; artık gerekçesi ölçülü: düzeltme bir kesintinin
  içine indi, ve Meridian'ın kendi defteri bunu ölçemiyor.
- **YENİ KALEM (WP7):** `tool_calls` alanı yapısal olarak −1. Bir gösterge her satırda
  "bilinmiyor" diyorsa, o bir gösterge değil gürültüdür. İki yol var ve ikisi de ölçülebilir:
  (a) `-Q`yu kaldırıp daha dolu çıktıyı ayrıştırmak — **bu gece ölçüldü ki `_extract_json`
  düşünce panelini zaten aşıyor**, yani risk sanıldığı kadar büyük olmayabilir; (b) sayacı
  CLI özetinden değil, `~/.hermes/sessions` döküm deposundan (ya da MCP tarafından) türetmek.
- **YENİ KALEM (WP7):** asıl duvar "yasak" değil **tercih**: %85 ham dosya araması, %2,5
  `skill_view`. Katalogu açmak yetmiyorsa, skill yolunun ham aramadan daha CAZİP olması gerekir
  — bu bir SOUL/araç-açıklaması tasarım işidir ve kart-önce ölçülmelidir.

## 6. Ölçülmedi — adıyla

- Döküm deposu **yalnız hataları** taşıyor; başarılı oturumlarda araç kullanımı **ölçülemedi**.
  Yani %2,5 rakamı BAŞARISIZ oturumların karnesidir ve başarılı oturumlara genellenemez.
  Bu sınır, hükmün "24b açık kalır" olmasının bir başka gerekçesidir.
- `skill_view`ın neden tercih edilmediği ÖLÇÜLMEDİ — yukarıdaki üç sebep hipotezdir.
- v244 sonrası araç kullanımı ölçülmedi (henüz yeterli oturum yok).
