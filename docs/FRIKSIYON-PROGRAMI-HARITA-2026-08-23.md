# FRİKSİYON PROGRAMI — BİRLEŞİK HARİTA (2026-08-23, Rol-1)

Tek soru etrafında yedi kart: **replay'in dünyası gerçek icra dünyasına ne kadar yakın, fark
hangi yönde ve kaç dolara mal oluyor?** Bu belge hüküm üretmez — yedi kartın hükümlerini tek
resimde birleştirir. Yetkili kaynak her zaman kartların kendisi (`research/cards/`).

## 1. Zincirin resmi

```
EDG-038 (ölçüt)  →  EDG-040 (duyarlılık)  →  EDG-042 (gerçek bant, birikiyor)
                         │                        │
                         ├── EDG-043 (koşullu limit — hüküm 042 bandına ASKIDA)
                         ├── EDG-045 (stop-slip — Ö1 ATEŞLEDİ, şerhler düştü)
                         └── EDG-046 (friksiyon-bilinçli seçilim — KANITSIZ, kapandı)
EDG-047 (yakın-pencere — Ö1 ATEŞLEDİ, karar §5)   [icra-penceresi kolu]
```

## 2. Kart kart durum

| Kart | Soru | Hüküm | Durum |
|---|---|---|---|
| **EDG-2026-038** | Friksiyon hangi ölçütle sayılır? | Kanonik payda = konsolide açılış (D1); isim-içi varyans 15↔134 bps | ✅ measured — ölçüt donuk |
| **EDG-2026-040** | Paket ek friksiyona ne kadar dayanır? | Başabaş **5-15 bps/bacak**; +10 bps'te paket NEGATİF; hasar fiyat-kanallı. **ŞERH (045'ten):** tüm hücreler stop-slip=0 dünyasında koştu — bant İYİMSER tarafta | ✅ measured + ACİL şemsiyesi tahtada |
| **EDG-2026-042** | GERÇEK friksiyon bandı ne? (n=4'ten çıkış) | Hüküm YOK — eşikler dolmadı. K1 betimleyici: **medyan +15,0 bps** (bandın üst sınırında), dağılım vahşi (−131..+327). K2/K3 damga bekliyor | 🔄 measuring — haftalık otomatik (Cts 10:29; ilk anlamlı tekrar **08-29**); K1 eşiği ~4-6 hafta |
| **EDG-2026-043** | Limit koşullu icra P&L'i kurtarır mı? | Altı Δ CI'sı da 0-içi; tek kârlı hücre slip15_B. **HÜKÜM ASKIDA** — okuma kuralı 042'nin gerçek bandını bekliyor | ⏸ measured/askıda |
| **EDG-2026-045** | Bar-içi stop slipajı=0 varsayımı ne saklıyor? | **Ö1 ATEŞLEDİ:** 10 bps stop-slip tek başına **−5.697** [−7.604, −4.004]; üç CI de sıfır-dışı. Paket 10 bps'te pozitif kalıyor (+18.109). EDG-040 bandına + replay hükümlerine şerh düştü | ✅ measured — şerhler işlendi |
| **EDG-2026-046** | Seçilim ATR%-cezalı olursa friksiyon dünyasında korunur mu? | **KANITSIZ — kapandı.** İki dünyada da +10,7k/+11,5k nokta ama ATR-dünyası CI 0-içi; kazancın dünya-bağımsızlığı = friksiyon kanalı değil stil eğimi. Yan-bulgu: sabit-5bps modeli ATR-modele göre −2.115 [−4.056, −547] şişiriyor | ✅ measured — canlanma: 042 bandı + yeni λ-kartı |
| **EDG-2026-047** | Açılıştan 15 dk beklemek riski gerçekten düşürür mü (bizim veri)? | **Ö1 ATEŞLEDİ:** Δ%menzil **−%42,3** [−%44,3, −%40,1] — dış ölçümün birebir replikasyonu. Bedel: sürüklenme medyan +4,65 bps (|m2| 55,4 — geniş) | ✅ measured — karar §5 `B-PENCERE-KAYDIR` |

## 3. Bugün bildiklerimiz (üç cümle)

1. **Replay defteri sistematik İYİMSER:** üç bağımsız gösterge aynı yönde — stop-slip=0 varsayımı
   anlamlı şişiriyor (045, −5.697@10bps), sabit-5bps dünya modeli ATR-orantılı modele göre şişiriyor
   (046 yan-bulgu, −2.115, model-şartlı), gerçek giriş friksiyonu betimleyici medyanı model
   değerinin 3 katı (042-K1, +15 bps, hükümsüz).
2. **Paket bugünkü kanıtla ÖLMÜYOR:** 10 bps stop-slip altında bile +18.1k; ama başabaş bandı
   (5-15) ile betimleyici gerçek (medyan 15) tehlikeli biçimde komşu — kesin söz 042'nin
   eşikli koşumlarına kaldı.
3. **"Friksiyonu akıllıca yönet" kollarından ikisi kapandı, biri askıda:** seçilim-cezası kanıtsız
   (046), koşullu-limit askıda (043→042), pencere-kaydırma ölçüldü ve operatör kararına hazır
   (047: −%42 risk ↔ +4,65 bps bedel).

## 4. Açık uçlar ve sahipleri

- **042 birikimi** (takvim; Cts otomatik) → K1 eşiği dolunca 040-şerhi/043-askısı/046-canlanması
  birlikte yeniden okunur. K2/K3 `broker_teyit` damgasının ilk reconcile turunu bekliyor.
- **`B-PENCERE-KAYDIR`** (operatör) → EVET ise kart-önce canlı değişikliği.
- **`B-E1-LIMIT`** (operatör) → E1 hükmü yeniden açık, kanıt düşük-güçlü; varsayılan: bacak kapalı.
- **D5** → 042 bandına park (değişmedi).
- Kısa-satır reçetesi: 042 kartının işaret cümlesi yalnız LONG için yazılı — short satır doğarsa
  reçete KARTSIZ genişletilemez (kartın kendi notu).
