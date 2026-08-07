# ÖN-KAYIT — runbook.html tip rampası (D6)

**Yazıldığı an:** 2026-08-07, HİÇBİR ÖLÇÜM KOŞULMADAN ÖNCE.
**Eşikler bu dosyada donmuştur; ölçümden sonra değişmez** (CLAUDE.md §3).

## Soru

`meridian/web/runbook.html` üç rampa-dışı sabit ölçü taşıyor (BASELINE-2026-08-06 **T10**):

| Seçici | Bugünkü | Rampada mı? |
|---|---|---|
| `body` | `15px` | HAYIR |
| `h1` | `26px` | HAYIR |
| `h2` | `18px` | HAYIR |
| `code` | `.86em` | göreli — sabit değil |
| `em` | `.92em` | göreli — sabit değil |

DESIGN.md Rampa Kuralı: **10 · 11 · 12 · 13 · 14 · 17 · 20 · 24 · 28** px, başkası yok.

Soru **iki yönlüdür ve tek yönlü sorulmayacaktır:** gövde rampaya mı inmeli (15→14),
yoksa 15px uzun-metin için gerçekten doğru olup **sapma DESIGN.md'ye mi yazılmalı**?
İkinci şık meşru bir sonuçtur; kod değişikliği varsayılan DEĞİLDİR.

## Ölçüt (benchmark) — dışarıdan değil, ÜRÜNÜN KENDİSİNDEN

`meridian/web/index.html:1368` → `.md{line-height:1.8;font-size:14px;max-width:72ch}`

Bu, panonun **kendi uzun-metin prose sözleşmesidir** ve canlıda koşuyor. Uzun-metin
okunabilirliğini dışarıdan ithal bir sayıya değil, ürünün zaten sevk ettiği ölçüye karşı
sınıyoruz. Yan ölçüt: `index.html:1380` `.hint{font-size:14px;line-height:1.75;max-width:70ch}`.

## Kıyaslanacak dört spesifikasyon

| Ad | Boyut / satır-yük. / ölçü | Yüz |
|---|---|---|
| `MEVCUT` | 15px / 1.65 / 78ch | runbook'un bugünkü yığını (system-ui…Roboto) |
| `SADECE_BOYUT` | 14px / 1.65 / 78ch | aynı yığın — boyut etkisini YALNIZ başına ayırmak için |
| `ADAY` | 14px / 1.8 / 72ch | aynı yığın — rampa + evin uzun-metin telafisi |
| `OLCUT` | 14px / 1.8 / 72ch | Recursive Sans (panonun `.md`'si birebir) |

`OLCUT` ayrı bir yüzle ölçülür çünkü D5 jeton turu bu depoda **inmemiştir** (aşağı bkz.);
hüküm D5 indiğinde de ayakta kalmalı.

## Kill ölçütleri — ŞİMDİ donduruldu

**H0 (çürütülmeye çalışılan sav):** *"15px bu yüzey için gerçek bir uzun-metin gereğidir;
14px okumayı bozar."*

| # | Ölçüt | Eşik | Kaynak |
|---|---|---|---|
| **K1** | Aynı runbook METNİ ürünün BİRİNCİL yüzeyinde ≤14px'te okunuyor mu? | ikili evet/hayır | kaynak okuması |
| **K2** | `ADAY`ın ölçülen satır uzunluğu (CPL) | 45–75 bandında **ve** `OLCUT`unkinden ≥5 CPL düşük değil | tarayıcı |
| **K3** | `ADAY`ın ölçülen x-yüksekliği | `OLCUT`unkinden **0,5px**'ten fazla düşük olamaz | tarayıcı |

**K3'ün 0,5px çıpası nereden geliyor (ölçümden önce yazıldı):** DESIGN.md'nin bilerek kabul
edip sevk ettiği en büyük tipografik kayıp **−0,11px** cap-yüksekliğidir (Geist→Recursive
defteri, "Lost" tablosu); x-yüksekliği farkları orada 0,02px "gürültü" sayılmıştır. 0,5px,
sistemin şimdiye dek kabul ettiği en büyük kaybın ~5 katıdır — cömert ama keyfî değil.

**45–75 CPL bandı:** DESIGN.md bir CPL bandı YAZMIYOR. Bu yüzden geleneksel uzun-metin bandı
alınmıştır ve **ithal olduğu burada beyan edilir**. K2'nin ikinci bacağı (`OLCUT`a görelik)
ithal olmayan bacaktır; çelişirlerse ürüne-göreli bacak kazanır.

## Hüküm kuralı

- **K1 ∧ K2 ∧ K3 hepsi geçerse** → gövde rampaya iner (14px), telafi `OLCUT`tan alınır.
- **Herhangi biri düşerse** → `15px` KALIR ve sapma, düşen sayıyla birlikte DESIGN.md'ye
  Rampa Kuralı'nın ikinci yazılı istisnası olarak geçer.

Kod değişikliği hükmün sonucudur, önkoşulu değil.

## Başlık merdiveni — ayrı ve daha basit karar

`h1 26px` ve `h2 18px` rampa dışı olduğu için **her hâlükârda** değişir (K1-K3 gövdeyle ilgili).
Hangi basamağa gidecekleri iki ölçülmüş olguya bağlanır:

1. `docs/RUNBOOK.md`de kaç `h1` var? DESIGN.md Display (28px) = *"görünüm başına bir tane"*.
   Birden çoksa 28px elenir.
2. Panonun kendi uzun-metin başlık merdiveni: `.md h3`=20px, `.md h4`=17px — ikisi de rampada.

`h3` (12px) zaten rampadadır; dokunulmayacak.

## Göreli ölçüler

`.86em`/`.92em` Rampa Kuralı'nın lafzını ihlal etmez (kural *sabit* font-size'ları bağlar) ama
T10 onları bulgu olarak listeler. Ölçülecek: gövde 14px'te ne piksele düşüyorlar ve sabit rampa
basamağına çevrilirlerse hangi bağlamda kaç piksel oynuyor. `code` başlık içinde de geçiyor
(ölçüldü: 15 `##` başlığı, tamamı h2; h1/h3'te yok, başlıkta `em` yok) — bu yüzden sabitleme
yapılırsa başlık-içi `code` ayrıca ele alınmalıdır.

## Kapsam dışı (bilinçli)

- `index.html`, `app.js`, `api.py` — operatör talimatı, dokunulmaz.
- **Renk/jeton/yazı-tipi birliği.** Görev metni D5 "jeton birliği" turunun indiğini ve geriye
  yalnız tip rampasının kaldığını söylüyor. **BU DEPODA İNMEMİŞ:** `tests/test_jeton_birligi_v208.py`
  hiçbir dalda yok, `runbook.html` hâlâ kendi sözlüğünü (`--tx3:#8a8580`, soğuk saç telleri,
  Roboto yığını) taşıyor ve HEAD=main=`cffb9f3` temiz. Yani T10'un renk bacağı AÇIK kalıyor;
  bu tur onu KAPATMIYOR ve kapattığını iddia etmiyor.
