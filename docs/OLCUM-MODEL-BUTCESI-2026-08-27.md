# ÖLÇÜM — LLM çağrı bütçesi: `max_tokens` ve `timeout` (2026-08-27)

**Neden var.** `meridian/hermes.py`in OpenRouter yolu tek bir `max_tokens: 4000` (satır ~2630) ve
tek bir `timeout: 120.0` (satır ~2633) gönderiyor. İkisi de BİZİM koyduğumuz sayılar — sağlayıcının
dayattığı bir şey değil — ve ikisi de ölçülmeden seçilmiş. Bu belge o iki sayıyı ölçümle değiştirmek
isteyen için taban verisidir.

**Uyarı, dosyanın kendi sınırı:** her model için TEK ölçüm alındı ve free-tier kapasite
PAYLAŞIMLIDIR. Hız dalgalanır. Eyleme değer olan tek tek saniyeler değil, **oran** ve **büyüklük
mertebesi**.

## 1. Sağlayıcının gerçek tavanları

`GET https://openrouter.ai/api/v1/models` (kimlik gerektirmez):

| model | context_length | max_completion_tokens | fiyat (prompt/compl) |
|---|---|---|---|
| `nvidia/nemotron-3-ultra-550b-a55b:free` | 1.000.000 | **65.536** | 0 / 0 |
| `nvidia/nemotron-3-super-120b-a12b:free` | 262.144 | **235.929** | 0 / 0 |

Yürürlükteki `max_tokens: 4000` → Ultra'nın izin verdiğinin **%6'sı**, Super'in **%1,7'si**.
Tipik girdimiz 23–27k token, yani bağlam penceresinin ~%10'u. Sayı keyfî ve aşırı muhafazakâr.

## 2. Kota ve maliyet — ölçüldü, ithal edilmedi

`GET https://openrouter.ai/api/v1/key` (Bearer):

```
is_free_tier: False      → ≥10 USD kredi alınmış ⇒ :free modeller 1.000 istek/gün kademesinde
limit: None              → anahtarda kredi tavanı yok
usage: 0                 → TÜM ZAMANLARIN harcaması sıfır
```

Platform tavanı (OpenRouter dokümanı, `:free` modeller): **20 istek/dakika · 1.000 istek/gün**.
Meridian'ın KENDİ tavanı `AGENT_RPD = 150`; ölçüm günü kullanım **1**. Yani bağlayan taraf
sağlayıcı değil, kendi koyduğumuz sayı.

`state/spend.jsonl`daki `cost_usd` bu modeller için UYDURMADIR (`price_for()` model adını
tanımayıp Opus fiyatına düşüyor); sağlayıcının `usage: 0` cevabı bunu bağımsız olarak doğruluyor.

## 3. Üretim hızı

Aynı prompt, `max_tokens: 3000`, ikisi de tavana dayandı (`finish_reason=length`):

| model | süre | token | **hız** |
|---|---|---|---|
| Super 120B-A12B | 22.937 ms | 3.000 | **130,8 tok/sn** |
| Ultra 550B-A55B | 116.213 ms | 3.000 | **25,8 tok/sn** |

**Ultra Super'den 5 kat yavaş.**

## 4. Bundan çıkan sert sonuç

120 saniyelik zaman aşımında Ultra ancak **~2.970 token** üretebilir — yani yürürlükteki
`max_tokens: 4000`'e **hiç ulaşamaz**. Ultra yolunda bağlayan taraf tavan değil ZAMAN AŞIMIDIR;
çağrı token bütçesi dolmadan zaman aşımında ölür.

Ve ikisini AYRI AYRI değiştirmek işe yaramaz: yalnız `max_tokens` yükseltilirse kesilme zaman
aşımına dönüşür — arıza adı değişir, sonucu değişmez.

## 5. Kesilmenin canlı izi

`state/spend.jsonl`: **13 nemotron çağrısının 7'si TAM 4000 `out_tokens`da bitmiş (%54)** —
2026-08-13 · 08-14 (×2) · 08-16 (×2) · 08-17 · 08-21; notlar `reflect (nous)` ve `nous_eval`.

Doğrudan yoklama mekanizmayı gösteriyor: düşünen model, cevaptan ÖNCE reasoning tokenı harcar.
Tavan yetmezse **cevabı değil düşüncesinin başını** döndürür:

```
Ultra  max_tokens=60    → 29.519 ms · finish=length · içerik: 'The user asks: "Reply with ONLY…'
Ultra  max_tokens=2000  →  5.399 ms · finish=stop   · içerik: '{"ok":true,"n":7}'
Super  max_tokens=60    →  3.379 ms · finish=stop   · içerik: '{"ok":true,"n":7}'
```

Meridian bu sınıfı GEMINI için zaten teşhis edip düzeltmişti (`thinkingBudget: 0` +
`maxOutputTokens: 8000`, gerekçesi `hermes.py`de yazılı). OpenRouter yolu o düzeltmeyi hiç almadı.

**Çıkarım sınırı, beyanlı:** kesilmelerin ayrıştırma hatasına dönüştüğü ÇIKARIMDIR, birebir
eşleştirilmedi. Aynı pencerede `nous_eval_unparseable` 2, `candidate_review_empty_parse` 22 var.
Ayrıca `agent_call_empty` 709 ve `review_fallback_empty` 459 **BAŞKA bir kod yolundadır**
(yerel ajan CLI) ve bu bulgu onları açıklamaz.

## 6. Türetilmiş bütçe tablosu

Hesap: `süre ≈ istenen_token ÷ ölçülen hız`, üstüne bağlantı/gecikme payı.

| çağrı sınıfı | model | max_tokens | timeout | hesap |
|---|---|---|---|---|
| interaktif (operatör bekliyor) | Super | 2.000 | 60 sn | 15 sn + bol pay |
| özet/rapor | Super | 8.000 | 120 sn | 61 sn |
| uzun sentez | Super | 16.384 | 180 sn | 125 sn |
| hüküm, kısa çıktı | Ultra | 4.000 | 240 sn | 155 sn |
| arka plan derin (yansıma) | Ultra | 16.384 | 900 sn | 635 sn — **yalnız async** |

Tek global sayı yanlıştır: iki model arasında 5 kat hız farkı var ve aynı elbise ikisine de uymaz.
Doğru birim **model × çağrı sınıfı → (max_tokens, timeout)**.

## 7. Daha iyi çare: akış (streaming)

Akışla çağırıldığında zaman aşımını tahmin etmeye gerek kalmaz: tokenlar geldikçe görülür,
duvar-saati bütçesi uygulanır, ve bütçe dolduğunda **kısmi çıktı kaybolmaz**. Bugün kesilen bir
çağrının 4.000 tokenı tamamen çöpe gidiyor.

Ayrıca `finish_reason` deftere YAZILMALI: onsuz "bitti" ile "kesildi" ayırt edilemez, ve bir
BÜTÇE arızası yanlışlıkla BİÇİM arızası ("unparseable") olarak sınıflanır — bu turda düzeltilmek
istenen kusurun ta kendisi budur.
