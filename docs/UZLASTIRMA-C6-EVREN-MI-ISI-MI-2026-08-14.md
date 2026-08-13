# C6 uzlaştırma — "evren mi bağlıyor, ısı mı?" İKİSİ DE, ama huninin FARKLI KATLARINDA

**Tarih:** 2026-08-14 · **Rol-1 (Fable)** · **Kalem:** ROADMAP WP11-D (denetim C6) · **Durum:** ÇÖZÜLDÜ, ölçümle
**Bağlı kalemler:** WP11-A/15c (evren genişletme — bu uzlaştırmaya bağlı olarak ASKIDAYDI) · §3 FINVIZ önceliği

---

## 1. Çelişki neydi

İki kart aynı sisteme bakıp farklı şey söylüyor görünüyordu:

- `EDG-2026-026:47-49` — **"bağlayıcı kısıt EVREN (%99.55)"**
- `EDG-2026-035:57-59` — **"Bağlayıcı kaynak ısı zarfı"** (gerçekleşen tepe tam 5,000R)

Denetim bunu C6 olarak açtı ve evren genişletme kararını (15c) buna bağladı: hangisi bağlıyorsa
kaldıraç oradadır.

## 2. Ölçüm — aynı koşumların ham çıktılarından

**Seans düzeyi** (`edg026 sonuc.json` · `tasnif_birincil` = her seansın BİRİNCİL kısıt sınıfı):

| kol | evren_bagladi | tavan_sifir (slot) |
|---|---|---|
| B (slot5, 1,0R) | 397 seans · **%59,8** | 190 seans · %28,6 |
| **C (slot20, 0,5R)** | 658 seans · **%99,55** (CI [0,9898 · 1,0]) | **%0,0** (CI [0 · 0]) |

**Plan düzeyi** (aynı koşumların `nogo_neden_dagilim`ı):

| dünya | NO_GO toplam | heat_hard | sector_cap |
|---|---:|---:|---:|
| C (edg026) | 171 | **168** | 3 |
| **C+mb (edg035 kontrol = canlı paket)** | **607** | **607** | 8 |

## 3. Uzlaştırma

**Çelişki YOK — iki ölçüt iki AYRI KATI sayıyor:**

- **Huninin ÜSTÜ (seans):** günlerin %99,55'inde bizi sınırlayan şey **aday arzıdır** — o seans
  yeterli nitelikli aday çıkmamıştır. Slot tavanı bu katta **hiç** bağlamıyor (%0,0, CI sıfırda).
- **Huninin ALTI (plan):** aday çıkan seanslarda planı reddeden şey **ısı zarfıdır** — C+mb
  dünyasında NO_GO'nun **607/607'si** heat_hard.

Yani: *çoğu gün yukarıda açlık var; aday bulunan günlerde aşağıda tavan var.* İkisi ardışık
darboğazdır, rakip açıklama değil.

**EDG-026'nın kendi metni zaten ikisini de söylüyordu** ("bağlayıcı kısıt EVREN %99.55" ve
`zarf_kesfi`de "NO_GO 171'in 168'i heat_hard") — çelişki gibi okunmasının sebebi **paydaların
farklı olduğunun yazılmamasıydı**. Bu, bu deponun tekrar eden hatasının bir başka yüzü: *aynı
kelimeyle iki farklı büyüklüğü adlandırmak.*

## 4. 15c (evren genişletme) için ne demek

**ATIL DEĞİL — ama beklenen kazanç "daha çok işlem" DEĞİL.**

Ölçülen emsal, mb silahlanmasıdır: mb aday arzını artırdı ve sonuç **işlem 772→885 (+113)** iken
**plan-reddi 171→607 (3,5×)** oldu. Yani ek arz alta indi, bir kısmı işleme döndü, çoğu ısı
duvarına çarptı.

Buradan iki ayrı tez çıkar ve **karıştırılmamalıdır**:

- **HACİM TEZİ (zayıf):** daha çok isim → daha çok işlem. mb emsali bunu kısmen destekliyor ama
  doyum belirgin: arzın 3,5 katı reddi, 1,15 katı işlem üretti.
- **SEÇİLİM TEZİ (asıl kaldıraç, ÖLÇÜLMEDİ):** sabit 5R ısının içinde **daha iyi adaylar daha
  kötüleri yerinden eder**. Bu bir kalite iddiasıdır ve işlem sayısına bakarak sınanamaz —
  işlem-başı R ve sharpe ile sınanır.

Ve zarf tarafı kapalı: `EDG-2026-035` zarfı büyütmeyi ölçtü ve **kalite çöküyor**
(n 885→1052→1144 iken sharpe 0,521→0,278→0,369). Yani "ısı duvarını kaldıralım" bir çözüm değil.

## 5. Hüküm

**C6 KAPANDI.** 15c'nin askısı kalkar — ama gerekçesi değişir: evren genişletme **seans-düzeyi
açlığı** hedefler ve başarı ölçütü **işlem sayısı DEĞİL, işlem-başı R ve sharpe**dir. Kart-önce
açılacak bir 15c ölçümü bu ölçütle kurulmalı; "daha çok işlem" bir başarı işareti olarak
KABUL EDİLEMEZ (EDG-028/035 zarf hücreleri tam olarak bunu gösterdi: hacim arttı, kalite düştü).

## 6. Ölçülmedi — adıyla

- Bu uzlaştırma **mevcut koşumların ham çıktılarından** yapıldı; yeni koşum YOK, K harcanmadı.
- "Daha iyi adaylar kötüleri yerinden eder" tezi **ÖLÇÜLMEDİ** — 15c kartının konusudur.
- ~~`earnings_kapsami_yok` ayrı bir kısıt mı, not mu — ayrıştırılmadı.~~ **ÇÖZÜLDÜ (aynı gün,
  koddan):** bir kısıt DEĞİL. `earnings.py:619-624` bunu açıkça yazıyor: *"BU İŞARET BİR CEZA
  DEĞİL… karar yolu DEĞİŞMEZ (NO_GO yok, REVIEW'e düşürme yok). Yalnız GÖRÜNÜRLÜK."* Beyanlı
  bir fail-open notudur.
  **Sayının NO_GO'ya EŞİT çıkmasının sebebi de bulundu** ve bir ölçüm-hijyeni kalemidir:
  replay motorunda not `if not _ek` koşuluyla ekleniyor (`backtest.py:426-427`) ve replay'de
  tarihsel takvim uygulanmıyor (*"bugünün takvimi tarihsel plana uygulanmaz"*), yani `_ek`
  fiilen HER plan için boş → not **her plana** biniyor. `nogo_neden_dagilim` da onu bir "neden"
  kovası gibi sayıyor.
  **SONUÇ:** huninin üçüncü katı YOK; ama `nogo_neden_dagilim` evrensel bir notu gerçek
  kısıtlarla aynı listede sayıyor. 15c kartı bu kovayı **ayıklamalı**, yoksa "en sık NO_GO
  nedeni" diye okunabilir — `analytics.gate_veto_tally` aynı tuzağı `"NOT: "` önekiyle zaten
  kapatmış (kodun kendi yorumu: önek olmasaydı "planların ~%23'ü" gibi sahte bir veto kovası
  açardı). Ölçüm betiği o dersi almamış. *(ROADMAP WP5 — ölçüm hijyeni kalemi.)*
