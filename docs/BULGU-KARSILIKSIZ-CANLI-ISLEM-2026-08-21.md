# BULGU — CANLI DEFTERDE BROKER'DA KARŞILIĞI OLMAYAN İKİ İŞLEM (2026-08-21)

**Sınıf:** veri bütünlüğü · **Etki:** canlı kanıt tabanının **%25'i** · **Durum:** ÖLÇÜLDÜ, KÖK NEDEN AÇIK

## ÖLÇÜM

Operatörün "Alpaca'daki para panodakinden farklı" şikâyetini kovalarken çıktı.

`trades.jsonl`, 2026-08-01 reset'inden sonra **8 canlı işlem** taşıyor. Alpaca aktivite defteri
(TAM sayfalanmış, 55 kayıt, en eskisi 2026-07-14) ile kıyaslandığında **ikisinin broker'da HİÇ
fill'i yok**:

| kitap kaydı | id | kaynak damgası | plan_id | P&L | broker fill |
|---|---|---|---|---|---|
| `ALL` 2026-08-07 → 2026-08-07 | T00096 | **`live_paper`** | `P-2026-08-06-ALL-momentum_burst` | −450,38 | **0** |
| `VLO` 2026-08-10 → 2026-08-11 | T00097 | **`live_paper`** | `P-2026-08-07-VLO-exhaustion_hammer` | +728,37 | **0** |

Net etki **+277,99**. Diğer altı işlemin (NUE·MRK·MRNA·HUM·MRVL·LLY) hepsinin broker'da fill'i VAR.

## NEDEN ÖNEMLİ

1. **Kanıt tabanı kirli.** `sermaye.durum()` `canli_islem_n: 8` diyor; ölçülen gerçek **6 gerçek +
   2 karşılıksız**. Kitabın `realized_pnl 6.350,22`'si +277,99 karşılıksız kâr içeriyor.
2. **Öğrenme bunları kanıt sayıyor.** Yansıma ufku `trades.jsonl` üzerinden hesaplanıyor
   (`_horizon_ok`), yani karşılıksız işlemler ufku ilerletiyor ve rejim dilimlerine giriyor.
3. **Damga yanıltıyor.** `kaynak: live_paper` bu deponun tohum/canlı ayrımının TAM olarak
   güvendiği alan (`ledgerstamp`). Bu iki satır o ayrımı geçersiz kılıyor: damga "canlı" diyor,
   broker "böyle bir işlem olmadı" diyor.

## NE ÖLÇÜLDÜ, NE ÖLÇÜLMEDİ

**ÖLÇÜLDÜ:** iki işlemin broker'da fill'i yok (tam sayfalama, `after=2026-06-01`, 55 kayıt) ·
ikisi de `live_paper` damgalı · ikisinin de gerçek `plan_id`si ve `strategy_version 3`ü var ·
diğer altı işlemin fill'i var.

**ÖLÇÜLMEDİ (hipotez bile denmez, aday):** emir gönderildi mi · gönderildiyse reddedildi mi ·
motor dolumu broker onayı olmadan mı yazdı · gölge/ayna katmanı canlı deftere mi sızdı ·
Alpaca tarafında hesap sıfırlaması oldu mu. **Kök neden BULUNMADI.**

## KÖK NEDEN ADAYI (ölçüldü ama KANITLANMADI)

`loop._persist_trade` damgayı **KOD YOLUNA** göre basıyor, broker kanıtına göre DEĞİL:

    ledgerstamp.stamp(trade, ledgerstamp.LIVE_PAPER)   # broker onayı SORULMUYOR

Docstring'i *"bu fonksiyondan geçen her satır canlı kâğıt döngünün GERÇEKTEN kapattığı bir
işlemdir"* diyor — ama "gerçekten kapattığı" iç motorun (`PaperBroker`) kendi defteri için
doğru; Alpaca için değil. İç motor pozisyonu kapatırsa satır `live_paper` damgası alır, ayna
hiç dolmasa bile. Bu, deponun bildiği **`MIRROR_DRIFT`** sınıfının bir vakası olabilir.

**ADAY ARTIK HÜKÜM — EMİR DEFTERİ ÖLÇÜLDÜ (2026-08-21):**

    /v2/orders?status=all&after=2026-08-01 → 62 emir
    durum dağılımı: filled 19 · canceled 18 · held 11 · new 7 · expired 4 · replaced 1 · accepted 2
    ALL : **0 emir**
    VLO : **0 emir**

Reddedilmiş DEĞİL, iptal edilmiş DEĞİL — **HİÇ GÖNDERİLMEMİŞ.** Olay defteri de aynı şeyi
söylüyor ve o defter bu günleri KAPSIYOR (61.511 satır, 2026-07-14 → 2026-08-21; ALL/VLO'nun
işlem günlerinde 10.426 olay var):

    alpaca_submit olayı: 19 kez · semboller:
      AMGN BDX BKNG CRM DE EMR HUM LLY MRK MRNA MRVL NSC NUE PANW RTX TMO UNP
    → ALL ve VLO bu listede YOK.

Ve `alpaca_submit` BAŞARISIZLIKLARI da logluyor ("stop price must be greater than current
price", "qty rounds to 0"), yani "denendi ama hata verdi" olsaydı görünürdü. **Deneme bile
yapılmamış.** İç motor bu iki pozisyonu
tamamen kendi defterinde açıp kapatmış ve ayna bir emir denemesi BİLE yapmamış. Yani kusur
"emir gönderildi ama dolmadı" değil, **"emir hiç doğmadı ama defter dolmuş sayıldı"**.

## ✅ KÖK NEDEN TAMAMLANDI (2026-08-21, ölçümle)

Zincirin son halkası bulundu. `submit_plan` **ONAY ANINDA** çağrılıyor
(`loop.py:743`, kendi ifadesiyle *"aynaya gönderim ONAY ANINDA tek kapıdan denendi"*).
Olay defteri:

    plan_operator_approved : 7 olay      ← yalnızca 7 plan onaylanmış
    alpaca_submit          : 19 olay · 17 sembol
    ALL : 145 olay — hiçbiri onay/silahlanma/gönderim DEĞİL
    VLO : 334 olay — aynı
    MRK : alpaca_submit VAR

**ZİNCİR:**
1. İç motor (`PaperBroker`) stratejiyi **onaydan BAĞIMSIZ** koşar — pozisyonu kendi defterinde açar.
2. Alpaca aynası **YALNIZ onaylanmış** planları gönderir.
3. `ALL`/`VLO` hiç onaylanmadı → hiç gönderilmedi → broker'da hiç var olmadı.
4. İç motor onları kendi işaretlerinde kapattı (stop / target).
5. `loop._persist_trade` satırı **`live_paper`** damgaladı.

**KUSUR TANIMSALDIR VE ASIL MESELE BUDUR:** `live_paper` damgası *"canlı döngünün İÇ MOTORU
bunu kapattı"* demektir; *"broker bunu uyguladı"* DEMEZ. Ama iki tüketici de ikincisini
varsayıyor — operatör panoda "canlı işlem" okuyor, öğrenme döngüsü `_horizon_ok` ile onu
canlı KANIT sayıyor. Damganın adı ile taşıdığı anlam AYRIŞMIŞ durumda.

**BU BİR "BOZUK KOD" DEĞİL, EKSİK BİR AYRIMDIR:** onaysız planların iç motorda koşması
tasarım gereği olabilir (kâğıt motor stratejiyi tam koşar). Eksik olan, defterin bu iki sınıfı
AYIRMASI: *broker-teyitli* ↔ *yalnız-iç-motor*. Bugün ikisi de tek damga altında.

## ARAŞTIRILAN VE ELENEN BİR SİNYAL

`mirror_divergence` alanı umut vericiydi: karşılıksız iki işlemin ikisi de `None` taşıyor,
broker'da fill'i olan beşinin hepsi sayı taşıyor. Ama **NUE istisnası bu sinyali çürüttü** —
NUE'nin broker'da 7 fill'i (3 alış + 4 satış) VAR ve `mirror_divergence` yine `None`.
Yani `None`, "broker'da karşılık yok"un GÜVENİLİR göstergesi DEĞİLDİR; örtüşme var, kural yok.
Panoda o sütun `None` iken **"—"** basıyor ve bu tire hiçbir şey ayırt etmiyor.

## SIRADAKİ ADIM (kart-önce)

Bu bir ölçüm kartı ister: "canlı defterdeki her işlemin broker'da karşılığı VAR MI" sorusunu
**sürekli** ölçen bir mutabakat — bugünkü tek seferlik kıyas değil. Kart yazılmadan kod
değiştirilmez; ama `sermaye.broker_mutabakati()` köprüsü bu bulgunun görünür kalmasını sağlıyor.

**Bu bulgu 2.623,34'lük açıklanamayan kalıntıyı AÇIKLAMIYOR** — tersine, karşılıksız işlemler
çıkarılırsa kalıntı **2.901,33**'e ÇIKAR. İki ayrı kusur olabilir.
