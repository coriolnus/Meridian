# Teşhis — alarm kutusunun %68'i IEX seyrekliğini "akış kesintisi" sanıyor

**Tarih:** 2026-08-14 · **Rol-1 (Fable)** · **Sınıf:** ölçüt-kalibrasyonu (kod hatası DEĞİL)
**Durum:** kök neden **KANITLI** (ayırt edici ölçüm koşuldu) · düzeltme önerisi aşağıda

---

## 1. Operatörün şikâyeti ve ölçülen tablo

Operatör üç kez bildirdi: *"alarm kutusunda gene benzer alarmlar birikmiş"*. Ölçüm
(canlı `state/events.jsonl`, son 24 saat, yalnız warn/error seviyesi):

| olay | n / 24sa | pay |
|---|---:|---:|
| **`intraday_gap_detected`** | **408** | **~%68** |
| `bars_integrity_period_excluded` | 58 | %10 |
| `bar_ghost_session_dropped` | 19 | %3 |
| `korumasiz_motor_disi_pozisyon` | **13** | %2 |
| diğer 10 sınıf | ~100 | %17 |

Kronik: 2026-08-06'dan beri **her gün 192-408** arası. Defterde toplam 33.288 uyarı birikmiş.

**Asıl zarar oranda:** gerçekten para riski taşıyan sinyal — `korumasiz_motor_disi_pozisyon`
(broker'da canlı stop'u olmayan pozisyon) — günde **13** kez konuşuyor; gürültü **408**.
Yani en önemli alarm, en gürültülü alarmın **1/31'i** kadar görünür.

## 2. Ayırt edici ölçüm — kanıt

Hipotez: seans-içi akış **IEX**'tir (ölçüldü: `marketstream.FEED = "iex"`,
`meridian/marketstream.py:30` varsayılanı). IEX ABD hacminin küçük bir payını basar; orta
ölçekli bir isimde bazı dakikalarda **hiç IEX baskısı olmaz**. O dakikalar "akış koptu" değil,
"bu borsada işlem geçmedi" demektir.

Sınama — alarmın bildirdiği somut boşluğu iki beslemede yan yana sorduk
(LMT, 2026-08-12, alarm kaydı: `13:34-13:37Z, eksik_dk 4`):

```
iex :  8 bar   13:30 13:31 13:32 13:33 ····· ····· ····· ····· 13:38 13:39 13:40 13:41
sip : 16 bar   13:30 13:31 13:32 13:33 13:34 13:35 13:36 13:37 13:38 13:39 13:40 13:41 …
```

**Eksik dört dakika, alarmın bildirdiği dört dakikanın tam kendisi** — ve konsolide beslemede
o dakikaların **dördü de dolu**. Hisse kesintisiz işlem görüyordu; susan şey **piyasa değil,
tek borsa** idi.

Hüküm: `intraday_gap_detected` / `tur="sembol"` sınıfı, bu beslemede **yapısal seyrekliği
ölçüyor**. Bir arıza raporlamıyor.

## 3. Dedektör hatalı DEĞİL — beklenti yanlış zemine kurulu

`barsarchive.gap_scan` iyi yazılmış ve birçok tuzağı zaten kapatıyor: XNYS takviminden gerçek
seans aralığı, yarım gün/tatil ayrımı, takvim yoksa "ölçülemedi" (uydurma yasağına uygun),
arşiv açılmamışsa hüküm vermeme, akış-kesintisinin içindeki sembol boşluğunu **iki kez
saymama**, kenar etkisi için iki yanlı bağlam şartı.

Kusur bunların hiçbirinde değil, **beklentinin zemininde**: "seansın her dakikasında bu
sembolden bir baskı olmalı" cümlesi **konsolide-besleme kalitesinde** bir beklentidir.
IEX'e uygulandığında her gün yüzlerce kez ve **haklı olarak** ateşlenir — ölçtüğü şey gerçektir,
ama o gerçek bir **arıza değildir**.

Dedektörün `tur="akis"` ayrımı zaten **doğru olan**dır: bütün sembollerde aynı anda susma =
gerçek soket/besleme kesintisi. Ayrım kodda var, kalibrasyon yok.

## 4. Bugünün ikinci kez aynı köke çarpması

Bu, **aynı gün içinde IEX zemininin ürettiği İKİNCİ ölçüm yanılsamasıdır**:

1. **TCA (EDG-2026-037 → 038):** slipaj ölçütü IEX günlük açılışıydı; konsolideye taşınınca
   "~9 kat" → "~7 kat" ve "4/4 aleyhte" → "3/4" oldu. Ölçütün hatası ölçülen büyüklükle
   aynı mertebedeydi.
2. **Bu teşhis:** seans-içi boşluk beklentisi IEX'e kurulu; günde ~200-400 sahte-sınıf alarm.

**Ders (tek cümle):** *hangi beslemeye baktığımız, ölçtüğümüz şeyin ne olduğunu değiştiriyor —
ve bunu iki ayrı yerde, iki ayrı gün fark ettik.* Beslemenin kimliği bir **ölçüt künyesidir**
ve her ölçümün yanında yazılı durmalıdır.

**NOT — GÜNLÜK bar verisi bundan etkilenmez:** `adapters/data.py` dünün IEX-damgalı günlük
satırlarını konsolide SIP barıyla değiştiriyor (data.py:1076 bandı). Etkilenen şey **seans-içi
dakika akışı** ve ondan türeyen boşluk alarmıdır. Strateji kararlarının bağlı olduğu günlük
defter bu teşhisin kapsamı DIŞINDADIR.

## 5. Öneri — üç kademe (karar operatörün)

**K1 — beslemeyi künyeye yaz (ucuz, hemen).** `intraday_gap_detected` mesajına `feed=iex`
damgası ve tek satır açıklama: *"IEX tek borsadır; sembol-boşluğu çoğu vakada seyreklik
olabilir"*. Alarm sayısı düşmez ama **yanlış okunmaz**.

**K2 — sembol-boşluğunu seviye düşür (asıl kazanç).** `tur="sembol"` olaylarını `warn`dan
bilgi seviyesine indir; `tur="akis"` (bütün sembollerde eş-anlı susma) `warn` kalır — o
gerçekten kesintidir. Böylece kutuda kalan sinyal gerçek sinyal olur ve
`korumasiz_motor_disi_pozisyon` gibi para-riskli satırlar **31 kat daha görünür** hâle gelir.

**K3 — beslemeye göre kalibrasyon (doğrusu, ama şartlı).** Eşiği besleme kimliğinden türet:
`FEED=iex` iken sembol-boşluğu eşiği belirgin yükselir ya da kapanır; `FEED=sip` olursa
bugünkü hassasiyet **doğru** hassasiyettir. Bu, SIP aboneliği geldiği gün otomatik doğru
davranmayı sağlar.

**Rol-1 önerisi: K1+K2 birlikte** (tek kod turu, dar yüzey), K3 SIP kararı gündeme geldiğinde.
Bunların hiçbiri veri kaybı yaratmaz — olay defterine yazım sürer, değişen yalnız **seviye
ve künye**dir.

## 6. Oran ölçümü — örneklem taraması (aynı gün eklendi)

Yukarıdaki tek-vaka kanıtı mekanizmayı gösteriyordu ama **oranı** vermiyordu. Kapatıldı:
geçmiş seansların `tur="sembol"` alarm havuzundan (**n=1717**) sabit tohumla (`20260814`)
**15 rastgele alarm** çekildi ve her biri kendi penceresinde iki beslemeye soruldu.

| sembol | gün | alarmın bildirdiği aralık | iex | sip | hüküm |
|---|---|---|---:|---:|---|
| HWM | 2026-08-12 | 13:55-13:59Z | 1 | 6 | seyreklik |
| ADBE | 2026-08-06 | 16:18-16:20Z | 1 | 4 | seyreklik |
| AMT | 2026-08-12 | 16:33-16:37Z | 1 | 6 | seyreklik |
| CCL | 2026-08-10 | 18:31-18:34Z | 1 | 5 | seyreklik |
| EQR | 2026-08-07 | 19:25-19:27Z | 1 | 4 | seyreklik |
| DG | 2026-08-12 | 14:11-14:15Z | 1 | 6 | seyreklik |
| APD | 2026-08-03 | 15:40-15:43Z | 1 | 5 | seyreklik |
| DHR | 2026-08-06 | 17:52-17:56Z | 1 | 6 | seyreklik |
| VLO | 2026-08-07 | 18:26-18:30Z | 1 | 6 | seyreklik |
| MRVL | 2026-08-12 | 18:28-18:31Z | 1 | 5 | seyreklik |
| BDX | 2026-08-11 | 14:20-14:28Z | 1 | 10 | seyreklik |
| ZBH | 2026-08-10 | 16:22-16:25Z | 1 | 5 | seyreklik |
| DHR | 2026-08-03 | 16:42-16:46Z | 1 | 6 | seyreklik |
| DLTR | 2026-08-12 | 18:29-18:34Z | 1 | 6 | seyreklik |
| TMO | 2026-08-10 | 17:15-17:20Z | 1 | 7 | seyreklik |

**SEYREKLİK 15 · GERÇEK-KESİNTİ 0 · ÖLÇÜLEMEDİ 0.**

Her vakada IEX penceresinde **tek** bar var, konsolidede **4-10**. Yani örneklemin tamamı
aynı mekanizma; 15/15. Desen ayrıca gün ve saat boyunca dağınık (03-12 Ağustos, 13:55-19:27Z)
— bir olaya, bir sembole ya da bir saate bağlı DEĞİL, **yapısal**.

Bu oranla K2 (sembol-boşluğunu bilgi seviyesine indirme) önerisi **ölçüye dayanır**:
örneklemde susturulacak hiçbir gerçek kesinti yok.

## 7. Açık — ölçülmedi, uydurulmadı

- Örneklem **15/1717** (%0,9) ve tamamı `tur="sembol"`. 15/15 tek yönlü çıktığı için
  mekanizma güçlü desteklenir, ama **"gerçek kesinti oranı sıfırdır" İDDİA EDİLMEZ** —
  ölçülen şey "bu örneklemde sıfır"dır. Nadir gerçek kesinti K2'den sonra `tur="akis"`
  kanalında görünmeye devam eder (o kanal `warn` kalıyor).
- `tur="akis"` sınıfının son 24 saatteki sayısı bu turda ayrıştırılmadı.
- Ölçüm penceresi alarmın kendi `aralik` alanından türetildi (+1 dk kapanış); pencere
  sınırındaki bar sayımı bu yüzden bir bar oynayabilir — hüküm 4-10 kat farka dayandığı
  için bu duyarlılık sonucu değiştirmez.
