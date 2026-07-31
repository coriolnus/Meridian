# TRADING DENETİMİ — 2026-07-31 (v2 prompt, MOD: TAM)
Denetçi: Rol 1 (quant-PM çerçevesi). Kanıt: defter ölçümleri (bu gece, komut çıktıları oturum
kaydında) + 8 web-araştırma ajanı (6-başlık filosu + 2 hedefli kapanış) + koşan ön-kayıtlı ölçümler.
Kural: rakamsız iddia yok; kaynaksız "best practice" yok; kaynaksız pratik görüş **[pratisyen kanaati]**.

## YÖNETİCİ ÖZETİ (tek paragraf)
Sistem bugün paraya değmez ama makinesi paraya değer: mevcut tek aile (EOD kırılma, 250 mega-cap)
pozitif edge kanıtı üretmedi (t=−1,91, n=95 — üstelik o defter büyük gövdesiyle survivorship'li
replay tohumu çıktı: BT-1) ve kazançların önemli kısmı beta (aynı pencerede SPY'a karşı
−%0,64/işlem). En büyük tek risk, ölçüm zemininin kendisiydi — BT-1/BT-2 (tohum-damgasızlık +
hayalet seanslar) kapanmadan hiçbir yeni hüküm güvenilir değil; ikisinin de düzeltmesi bu gece
yazıldı/koşuyor. İlk yapılacak tek şey: **çıkış mimarisi paketinin K-cezalı ölçümü** (koşuyor) —
çünkü ödeme oranı 0,97 × kazanma %36,8 kombinasyonu, sinyal hiç düzelmese bile tek başına
kaybettiren bir çıkış tasarımının imzası ve bu, tamamen bizim kontrolümüzdeki tek büyük kaldıraç.

## SKOR KARTI (0-10; toplam 39/100 → kural: önce ölçüm altyapısı, sonra yeni aile)
| # | Boyut | Puan | Tek cümle |
|---|---|---|---|
| 1 | Edge netliği | 2 | Mevcut ailenin karşı-taraf cevabı jenerik (sürü/eksik-tepki) ve en arbitrajlı segmentte; pozitif kanıt yok |
| 2 | Backtest geçerliliği | 3 | Disiplin makinesi güçlü (donmuş holdout, K-cezası) ama mevcut defter replay-tohumlu+survivorship (BT-1) ve barlar hayalet-seanslı (BT-2) |
| 3 | İstatistiksel güven | 2 | n=95 (tohumlu), t=−1,91 — hiçbir yönde hüküm yok; gerçek canlı n≈0 |
| 4 | Çıkış-dağılım tutarlılığı | 1 | 4/95 hedef, 33/95 zaman-stopu, maks 2,69R, ödeme 0,97 — momentum ailesine mean-reversion çıkışı |
| 5 | Maliyet gerçekçiliği | 7 | 10,0 bps round-trip, ADV-duyarlı model; canlıda doğrulanmadı (Schwarz vd. 2025 retail bandı 7-46bps) |
| 6 | Risk mimarisi | 5 | corr_max kapıda + derisk rampası + sektör tavanı VAR; ısı tavanı yalnız-gösterge, DD yönetişimi yazılı-belge değil |
| 7 | Rejim farkındalığı | 4 | Kapı var ama aile EN İYİ rejiminde bile negatif (trend_up −$52/işlem) ve chop'ta işlem sürüyor |
| 8 | Atribüsyon görünürlüğü | 3 | Alfa/beta ilk kez bu gece ölçüldü; aile×rejim tabloları bu gece kuruldu; hiçbiri kablolu değil |
| 9 | Deney disiplini | 8 | K-cezası, DSR/PBO, donmuş holdout, gölge kitaplar, kill-kriteri kültürü — sistemin en güçlü boyutu |
| 10 | Veri varlığı kullanımı | 4 | Kazanç takvimi yalnız blackout'ta; transkript sıfır; insider bu gece açıldı; SI ölçülüp dürüstçe kapatıldı |

## BULGULAR (şiddet-kodlu)
- **BT-1 (KRİTİK):** n=95 "canlı defter"in gövdesi tek-sürümlü replay tohumu (T00001→, 2023-02
  başlangıç, proje Temmuz-2026 doğumlu) — survivorship'li bugünkü evrenle; satırlarda kaynak
  damgası yok; kalibrasyon/karne bunu canlı sanıyor. KAPATMA: `kaynak: replay_seed|live_paper`
  damgası + gerçek-canlı sayacın panoya çıkması (yarınki turda). Bilinen replay-iyimserliği
  (~+0.018) ile mutlak PnL iyimser üst sınır.
- **BT-2 (KRİTİK):** Bar önbelleğinde hayalet seanslar (Memorial Day 2025 258/259 dosyada; 5
  sembolde bölünmemiş fiyat — BKNG +%2598 hayalet getirisi); component_ic/cf/R-tabloları kirli.
  KAPATMA: takvim kapısı + karantina + onarım ajanı KOŞUYOR; türetilmiş artefaktlar yeniden üretilecek.
- **BT-3 (MAJÖR):** Prescreen/backtest evreni point-in-time değil (bugünün üyeleri). Mid-cap
  ölçümü dahil her yeni ölçüm bu yanlılığı beyan etmek zorunda; PIT evren ayrı altyapı kalemi.
- **BT-4 (MAJÖR):** İşlem dönemi (2023-01→) ayı piyasası içermiyor — long-only sistem düşüş
  rejiminde hiç sınanmadı; rejim etiketlerinde high_vol n=3.
- **ED-1 (MAJÖR):** Çıkış-dağılım tutarsızlığı (skor kartı #4'ün gerekçesi; kural-mekaniği bulgusu,
  tohumdan bağımsız geçerli).
- **ED-2 (MAJÖR):** Aile en iyi rejiminde negatif; chop'ta işlem sürüyor (−$72/işlem) — rejim
  daraltma kanamayı azaltır ama kâra çevirmez (ölçüldü).
- **ED-3 (MİNÖR):** pullback kurulumu n=4, %0 kazanma, −$330/işlem — hüküm için küçük ama askı
  gerekçesi olarak yeterli; G4 tasarım girdisindeki cf −0,97R ile tutarlı.
- **RS-1 (MAJÖR→ERTELENMİŞ):** Isı tavanı yalnız-gösterge. Silahlanma bilinçli olarak pozitif-EV
  sonrasına ertelendi (vol-yönetimi edge yaratmaz, paketler — B&SC 2015 pozitif-Sharpe önkoşullu;
  Cederburg vd. maliyet-sonrası genellemeye itiraz).
- **RS-2 (MİNÖR):** DD yönetişimi mekanizmada var (derisk_mult, max_positions_at) ama tek yazılı
  belge değil — "hangi DD'de ne yapılır" tablosu OPERATÖR belgesine eklenmeli.
- **RS-3 (MİNÖR) [pratisyen kanaati]:** VCP-kırılma yaygın taranan retail deseni — çıkış izdihamı
  riski; katalizör-koşullandırma bunu da hafifletir.
- **YÜ-1 (MİNÖR):** Canlı TCA ölçülmedi (paper model 10bps; canlıda 2-4× kötüleşebilir — Schwarz
  vd. 2025); implementation-shortfall takibi canlıya geçişte zorunlu.
- **AT-1 (MAJÖR):** Atribüsyon kablosuz — alfa/beta + aile×rejim + tutuş-dilimi kırılımı
  result_verdict'e girecek (yarınki tur).
- **VA-1 (MAJÖR):** Veri varlıklarının çoğu atıl — transkriptler hiç, kazanç verisi yalnız
  kaçınma, insider bu gece EDGAR'la açıldı.

## FAZ 3 — KARŞI TARAF TABLOSU (+ "neden hâlâ sömürülmemiş?")
| Aile | Kim kaybediyor, neden | Neden hâlâ açık olabilir | Durum |
|---|---|---|---|
| Mevcut: mega-cap kırılma | Jenerik sürü/eksik-tepki | Cevap yok — en likit segment, koruma mekanizması yok | Negatif eğilim ölçüldü; katalizör-koşula evrilecek |
| Insider küme-alım | Yasal bilgi asimetrisi | Large-cap'te KORUNMUYOR — ÖLÇÜLDÜ: EDGAR 62 çeyrek (2011-2026), 3.893 olay, 18 hücrede çoklu-sınama sonrası 0; olay-çalışması üst sınırı +%0,06; pozitif kontrol geçti (boru hattı momentum'u saptıyor) | **EDGE YOK — kapalı** |
| Short squeeze | Kalabalık pozisyonun zorunlu çözülmesi | — | ÖLÇÜLDÜ: bizim evren/ufukta edge yok; kapalı |
| PEAD (klasik) | Kurumsal eksik-tepki | Large-cap'te KORUNMUYOR: 2006'dan beri ölü (Martineau CFR; Subrahmanyam repl. t=1,43 mikro-cap hariç); sürüklenme geç-pencerede (B&T 1990) — ufkumuza da ters | YAPMA |
| **Kazanç-öncesi duyuru primi (EAP)** | Duyuru belirsizliğinden kaçan erken satıcı + dikkat mekaniği (Frazzini-Lamont 2007; Barber vd. JFE 2013 — large-cap'te güçlü; Savor-Wilson JF 2016 risk-temelli kalıcılık) | Beta-sıçrama riski taşımak isteyen az; takvim-bağlı, kapasiteli | **4/4 kontrol GEÇTİ — tek yeni-aile adayı**; ABD-decay bizim evrende ölçülecek |
| 52-hafta-zirvesi | Çapa yanlılığı (George-Hwang 2004) | — | VCP'nin akademik ikizi — bağımsız aile DEĞİL; VCP-korelasyon ölçümü yeter |
| Endeks rekonstitüsyonu | Endeks fonu mekanik akışı | KORUNMUYOR: etki 2010'lardan beri ~0 (Greenwood-Sammon); olaylar evrenimizin dışında | ÇIKARILDI |
| Sektör rotasyonu + takvim | Mandat ataleti / akış takvimi | Literatür ETF/endeks-düzeyi; tekil-hisse 5-20g mimarimizle yapısal uyumsuz; takvim bacağı decay'li | ÇIKARILDI (ileride ayrı "portföy risk-on/off katmanı" teklifi olabilir) |

## FAZ 4 — ALFA/BETA (ölçüldü; BT-1 çekincesiyle)
İşlem pencerelerinde defter −%0,225 vs SPY +%0,411 → kaba alfa **−%0,64/işlem**; kazanan işlemler
SPY'ın +%1,89 koştuğu pencerelerde (timing değil beta). BT-1 nedeniyle bu, "kuralların karakteri"
ölçümüdür, canlı performans değil — survivorship alfayı daha da iyimser gösterir (gerçek muhtemelen
daha kötü). Kablolama: result_verdict'e beta-düzeltilmiş kolon (yarın). Timing-vs-seçim ayrımı:
tutuş-dilimi × giriş-günü-SPY kırılımı tasarlandı, atribüsyon kablosuyla birlikte gelir.

## FAZ 7C — DEĞİŞTİR / EKLE / BIRAK (efor S/M/L · etki düşük/orta/yüksek)
**DEĞİŞTİR**
1. Çıkış paketi (teşhis: momentum'a mean-reversion çıkışı; kanıt: ED-1 rakamları + aritmetik
   0,97→~2+ zorunluluğu + hakemli boşluk beyanı [kısa-ufukta literatür yok — kanıtı BİZ üretiyoruz];
   aksiyon: P1/P2/P3 K=3 ön-kayıtlı prescreen KOŞUYOR → geçen paket gölge-v2'ye) · M · YÜKSEK
2. Katalizör-koşullu giriş + rejim daraltma (kanıt: ED-2, beta bulgusu; aksiyon: kazanç-penceresi
   koşullandırma ölçümü + chop'ta giriş kapatmanın gölge ölçümü) · M · ORTA
3. Defter kaynak-damgası + gerçek-canlı sayaç (kanıt: BT-1; aksiyon: yarınki tur) · S · YÜKSEK
   (ölçüm güvenilirliği)
**EKLE**
4. Atribüsyon kablosu — alfa/beta + aile×rejim + tutuş-dilimi result_verdict'te (AT-1) · S · YÜKSEK
5. Insider ailesi — EDGAR IC hükmüne bağlı; geçerse canlı besleme günlük Form-4 API adaptörü · M · ORTA-YÜKSEK
6. Karşı-taraf + neden-açık iki-soru kapısı hermes istemine · S · ORTA
7. PIT-evren altyapısı (BT-3'ün kalıcı çözümü; mid-cap ölçümünün önkoşulu) · L · YÜKSEK
**BIRAK**
8. Klasik PEAD large-cap'te (kaynaklı gerekçe yukarıda) · — · —
9. pullback kurulumu askıya (ED-3; kanıt eşiği: yeniden açmak için prescreen'de P≥0,95) · S · DÜŞÜK

## FAZ 7D — ROADMAP (ön-kayıtlı ölçüm planları; ROADMAP.md §3.0b'ye işlendi)
Sıra ve kill-kriterleri §3.0b'de; standart: her deney metrik+eşik+örneklem+kill ÖNCEDEN yazılı,
aşama kapıları (fikir→geçmiş-ölçüm→gölge→küçük-canlı→tam), tek-değişken (paket=tek birim),
öldürme eşiği yaşatma eşiğinden önce.
