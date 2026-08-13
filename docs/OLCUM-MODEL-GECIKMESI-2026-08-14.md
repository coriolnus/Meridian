# Model gecikmesi ölçümü — darboğaz model değil, AKIL YÜRÜTME UZUNLUĞU

**Tarih:** 2026-08-14 · **Rol-1 (Fable)** · **Yetki:** operatör ("hangisi en uygun sonuç veriyorsa nemotron modellerinden ona güncelleyebilirsin")
**Sonuç:** `NOUS_MODEL` → `nvidia/nemotron-3-super-120b-a12b:free` (UYGULANDI, canlıda doğrulandı)

---

## 1. Neden ölçüldü

OpenRouter'a geçtikten sonra `_agent_call` çağrıları **116-133 saniye** sürüyordu; Gemini yolu
~10 saniyeydi. "Yavaşlık nereden?" sorusunun iki rakip cevabı vardı ve ikisi farklı düzeltme
gerektiriyordu: **(a)** CLI'nın kendi yükü (skill yükleme, hook, MCP açılışı) · **(b)** modelin
üretim uzunluğu. Tahmin etmek yerine ayrıştırıldı.

## 2. Tasarım — aynı istem, üç yol

Tek ve aynı JSON-şemalı istem, üç taşımadan geçirildi: **HAM** (doğrudan OpenRouter HTTP —
yalnız model süresi) · **CLI0** (yerel `hermes chat`, skill YOK — model + CLI yükü) ·
**CLI7** (yedi skill ön-yüklü — dolgunun/incelemenin GERÇEK biçimi). Üç aday: `nemotron-3-ultra`
(550B), `nemotron-3-super` (120B), `gpt-oss-20b`. JSON geçerliliği her koşumda `_extract_json` ile
sınandı.

## 3. Ölçüm

| yol | ultra | **super** | gptoss |
|---|---:|---:|---:|
| HAM (model tek başına) | 4,0 sn · 143 tok | 3,9 sn · 168 tok | 3,8 sn · 164 tok |
| CLI0 (skill'siz) | 74,1 sn · 11.883 kr | **8,3 sn · 1.090 kr** | 41,0 sn · 340 kr |
| **CLI7 (7 skill — gerçek biçim)** | **455,8 sn · 24.213 kr** | **18,7 sn · 3.732 kr** | — |

**json_ok = True — dokuz koşumun dokuzunda.** Yani hiçbir aday biçim sözleşmesini bozmuyor;
ayrım yalnız süre ve üretim uzunluğunda.

## 4. Hüküm — (a) elendi, (b) doğrulandı

Ham API'de **üç model de ~4 saniye**. Yani ne model yavaş, ne ağ. CLI'ya girince ultra 74 sn'ye,
skill'le 456 sn'ye çıkıyor — ve **çıktı uzunluğu aynı yönde patlıyor** (143 → 11.883 → 24.213
karakter). Süre, üretilen akıl-yürütme metniyle birlikte artıyor: **darboğaz CLI yükü DEĞİL,
ultra'nın zengin bağlamda uzun uzun düşünmesi.**

CLI'nın kendi yükü de ölçüldü ve küçük: super HAM 3,9 sn → CLI0 8,3 sn, yani **~4,4 saniye**
sabit maliyet. Ultra'nın 70 saniyesi bu değil.

**GERÇEK İŞ BİÇİMİNDE (CLI7) FARK 24×** (455,8 ↔ 18,7). Aritmetiği: `MERIDIAN_AGENT_RPD=600`
bütçesi ultra ile **76 saate** karşılık gelirdi — yani günlük bütçe fiilen ulaşılamaz, dolgu
kuyruğu erimezdi. Super ile aynı bütçe **~3,1 saat**. Model değişikliği bir iyileştirme değil,
**bütçenin kullanılabilir olmasının şartı**.

## 5. Uygulanan

`NOUS_MODEL` = `nvidia/nemotron-3-super-120b-a12b:free` (sır deposu, TTL 300 sn — restart YOK).
Zincir: **super → `openai/gpt-oss-20b:free`**. İkisi de ücretsiz; **farklı soy** (NVIDIA ↔ OpenAI
açık-ağırlık), yani model-bazlı üst-sağlayıcı doygunluğuna (Gemma'nın bu gece 3/3 aldığı 429)
karşı gerçek bir yedek. `brain_chain_facts.same_model_ids` **boş kaldı**.

**CANLI DOĞRULAMA** (dağıtılmış kod, gerçek `_agent_call`): **5,6 saniye**, dolu cevap —
öncesi ultra ile 116-133 sn. Yaklaşık **21×**.

## 6. Ölçülmedi — adıyla

- **KALİTE ÖLÇÜLMEDİ.** Karşılaştırılan tek şey süre + biçim geçerliliği. "Super'in görüşleri
  ultra kadar iyi mi" sorusu **cevaplanmadı** ve bu bir hız-kalite takasıdır. Ölçütü şudur ve
  ancak bir öğrenme penceresi sonra bakılabilir: `analytics.llm_opinion_calibration` (görüş ↔
  gerçekleşen sonuç) + `probgate`e ULAŞAN öneri sayısı.
- **CLI7-gptoss koşulmadı** (yedek yolun skill'li maliyeti bilinmiyor). Yedek nadiren ateşlendiği
  için öncelik verilmedi; ateşlenirse `agent_call.sure_ms` zaten ölçecek.
- Her hücre **tek koşum**; varyans ölçülmedi. Fark 24× olduğu için hüküm varyansa duyarlı değil,
  ama "8,3 sn" gibi tek sayılar nokta-tahmindir.
- Ölçüm `MERIDIAN_AGENT_RPM=20` ile koşuldu (bütçe reddine takılmamak için); canlı RPM 6'dır ve
  bu ölçümün süre sonuçlarını etkilemez (seri koşum), yalnız reddi önler.
