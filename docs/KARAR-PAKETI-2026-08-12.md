# KARAR PAKETİ — 2026-08-12 ölçüm dalgası (8 kart, ~15 hücre)

> Operatör penceresi bu belgeyle kurulur. Her satır: ölçülen sayı + donuk-eşik durumu + Rol-1 önerisi.
> İlke: sayılar hükümden önce gelir — CI çürütürse öneri düşer (ROADMAP §2-11 ön-kayıt).

## A. SONUÇLANMIŞ HÜKÜMLER

### 1) EDG-023 — Rampa 15/36 (kâğıt) · ✅ ölçüldü
| | A: 3/8 (mevcut) | B: 15/36 |
|---|---|---|
| işlem | 135 (29.5/yıl) | 410 (89.6/yıl) — fark CI [+210,+342] |
| net P&L | **−7.761$** | +775$ |
| max-dd | %7.8 | %17.8 (×2.29 → kill#3) |
| işlem-R / sharpe | −0.078 / −0.97 | +0.032 / +0.02 |

**Öneri: BENİMSE (yalnız kâğıt; gerçek-para 3/8 sabit).** kill#3 otomatik-hükmü engelledi — karar operatörün; %17.8 dd kâğıtta öğrenme bedeli, karşılığı 3× işlem + eksiden artıya.

### 2) EDG-026 — Slot 20 + 0.5R · ✅ ölçüldü
| | B (slot5, 1R) | C (slot20, 0.5R) |
|---|---|---|
| işlem | 410 | **772** (CI [+271,+455]) |
| net P&L | +775$ | **+9.869$** |
| max-dd | %17.8 | **%12.4 (DÜŞTÜ)** |
| sharpe | 0.018 | **0.285** |

**Öneri: KOŞULSUZ BENİMSE** (üç kill temiz; operatör ön-kararı ısı-10R kayıtlı). **ZARF KEŞFİ:** gerçek ısı-tavanı `heat_hard_r=5.0R` motor sabiti — ölçülen C fiilen ≤5R koştu ve bu sonuçları verdi. **Ayrı karar: zarf 5→10** (EDG-028/T10 ölçüyor — aşağıda).

### 3) EDG-025 — momentum_burst silahlanma · ✅ ölçüldü → **OTOMATİK SİLAHLANMA YOK**
Donuk üçlü eşik: (i) replay CI>0 **DÜŞTÜ kıl payı** (CI [−0.0046, +0.5606], n=106) · (ii) portföy-etkisi GEÇTİ (+11.9k$) · (iii) çelişki ÇÖZÜLDÜ (−0.114R hiç ölçüm değilmiş — prompt figürü).
**Öneri: dormant KALSIN.** Manuel silahlanma takdirin — ama dikkat işareti: 2026 yakın-dönem mb iki bacakta da zayıf (cf H2 −1.03 n=7; replay 2026 +0.014 n=16). Rol-1 tavsiyesi: bekle, yıllık kırılım düzelirse yeniden.

### 4) EDG-027 — Çıkış kolları (scale-out ½@1.5R · chandelier 20) · ✅ 4/4 hücre → **İKİSİ DE KAPALI**
- scale-out: B −0.141R / C −0.123R (CI'lar tam negatif; C'de 24k$ yıkım) — kök MEKANİK (bankalama-barı trail kusuru, §2-13); kavram-cevabı **EDG-029'da** (aşağıda).
- chandelier: B etkisiz / C sınırda-negatif (CI üst −0.0003) — mevcut ATR-trail yeterli.
**Öneri: ikisini de benimseme** (zaten kapalılar — değişiklik yok).

## B. BEKLENEN HÜKÜMLER (koşumlar sürüyor — indikçe dolacak)

### 5) EDG-024 — Eşik retro-kanıt (hacim 1.25× / RS 65, 3-hücre atıf) · 🔄
_Ölçülecek: eklenen işlemlerin gerçek-R'si hücre başına CI. CI>0 → OOS-kapılı gevşetme önerisi; değilse eşikler kanıtla doğrulanır._

### 6) EDG-028 — Isı: zarf-10 + modülasyon · ✅ ölçüldü → **ZARF-10 ÖNERİLMEZ, modülasyon otomatiği YOK**
| | C@5 (mevcut zarf) | T10 (zarf-10) |
|---|---|---|
| işlem | 772 | 882 (CI [+59,+166]) |
| net P&L | **+9.869$** | +1.266$ (nokta −8.6k) |
| sharpe / işlem-R | **0.285 / 0.057** | 0.037 / 0.026 |

**Öneri: 5R ZARFINDA KAL** — 10R'nin eklediği işlemler kalitesiz ("ISI 10R" ön-kararınla çelişen ölçüm; karar senin). Y1 rejim-harita kıl-payı düştü (avg-R CI üst +0.029), Y2 vol-hedef net kötü → ikisi de otomatik uygulanMADI. Yapısal bulgu: rejim kapısı 5R dünyasında zaten doğal modülasyon (motor high_vol/trend_down'da girmiyor) — dosya ölçülmüş-red ile kapanır.

### 7) EDG-029 — Scale-out DÜZELTİLMİŞ · ✅ ölçüldü → **KAVRAM ELENDİ, DOSYA KAPANDI**
Düzeltilmiş haliyle bile CI-negatif (B −0.053R / C −0.045R, ikisi tam-negatif). Düzeltme kusur-payını geri aldı (+0.087R) ama kalan zarar kavramın kendisi: 1.5R'de yarı-bankalama kuyruk-kazananları feda ediyor. **Karar gerekmez** — alet kapalı kalır; §2-13 latent-kusur notuna indi.

### 8) EDG-030 — Rejim-eşiği 40→{30,20} · 🔄
_Eklenen-işlem R'si CI>0 ∧ dd sınırlı → gevşetme adayı; CI-negatif → %41'lik karartma kanıtla haklı._

### 9) EDG-031 — Turnover ağırlığı · ✅ ölçüldü → **w=0 DOĞRULANDI, karar gerekmez**
w005 −3.5k$/w010 −4.3k$ (CI 0-içi, medyan negatif; sharpe düşüyor). Takas aleyhte: kaybedilenler +R'li, eklenenler −R'li — kesitsel sinyal gerçek ama bileşik-ağırlık olarak seçilimi bozuyor. Kablo w=0'da; hermes arama-uzayında kalır (elle ağırlık yok).

## C. PENCERE SONRASI ZORUNLU ADIMLAR (sıra donuk — §2-11)
1. **FİNAL-PAKET doğrulama replay'i:** seçilen tam kombinasyon tek koşumda ölçülür (etkileşimler toplamsal varsayılmaz), sayı pakete damgalanır.
2. **TEK goal/bounds dağıtımı** (suite yeşil şartıyla).
3. **OPT Faz-1 kablolama** (bir sonraki tur monkeypatch'siz).

## D. PENCEREYE GİRMEYEN AÇIK KONULAR (hatırlatma)
- Beyin-anahtarı canlı doğrulaması (Gemini flash-latest ilk gerçek review — bu geceki döngüde izlenecek)
- Bu geceki EOD: exhaustion_hammer'ın ilk silahlı döngüsü + near-miss dirilişi (canlı triyaj yarın)
- N1 bildirim token'ı · VLO ayna kararı · lean login (§3)
