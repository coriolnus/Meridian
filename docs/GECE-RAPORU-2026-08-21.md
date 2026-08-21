# GECE RAPORU — 2026-08-21 → 22

Operatör: *"ben yatıyorum, döndüm diye yazana kadar hiç durmadan otonom devam et."*
Bu belge sabah okunmak için yazıldı: **ne ölçüldü, ne değişti, ne değişmedi ve neden.**

---

## 1 · SENİN ÜÇ BİLDİRİMİN — ikisi haklı, biri yanlış anlaşılmıştı

### (1) "Öğrenme ve antrenman çalışmıyor" → **İKİSİ DE BOZUK DEĞİL**

Hiçbir kod değişmedi. İkisi de **tasarım gereği bekliyordu**:

| | ölçüm | hüküm |
|---|---|---|
| **antrenman** | `should_run() → kos=False · sebep="saat_dilimi_disinda" · saat=21 · pencere=[22,6]` | ölçüm 21:53'te yapıldı, pencere **7 dakika sonra** açılıyordu. Diğer şartlar sağlanmış (`gecen_gun=6`, `taze_hipotez=3`) |
| **öğrenme** | `_horizon_progress: trades 6/5 ✓ · span_days 2/30 ✗` | `REFLECTION_MIN_DAYS=30` aşırı-uydurma ufku. Birim `active`, **0 restart**, kalp taze — düşmüş değil |

Arka plan rejim dalı da haklı olarak kapalı: `chop` tabanı zaten 887 (2026-08-17'de yansıdı),
`trend_down`/`high_vol` hiç işlem görmemiş.

**ÖLÇÜM TUZAĞI, KAYDA GEÇTİ:** `_bg_ready_regime`ı TAZE bir süreçte çağırınca `chop` döndü ve bir
an "arka plan dalı ateşlemeli ama ateşlemiyor" sandım. Yanlıştı — fonksiyon rejim-başına TABAN
kullanıyor, taze süreçte `_state` boştu. Canlı durum yüklenince cevap `None` oldu. **Durum taşıyan
bir fonksiyonu durumsuz çağırmak, ölçtüğü şeyi uydurur.**

### (2) "Alpaca'daki para panodakinden farklı" → **HAKLI**, ve fark ölçüldü

    broker equity (mark-to-market)      109.701,49
      − gerçekleşmemiş P&L                 −735,31
      = maliyet bazlı broker             108.966,18
      − broker'ın RESET GÜNÜ equity'si   −99.992,62   ← ÖLÇÜLDÜ (portfolio/history)
      = broker reset-sonrası kazanç        8.973,56
    kitap reset-sonrası kazanç             6.350,22
    ─────────────────────────────────────────────────
    AÇIKLANAMAYAN                          2.623,34

Reset günü iki taraf **mutabıktı** (kitap 100.000 ↔ broker 99.992,62). Ayrışma ondan **sonra**
doğdu — tarihî bir artefakt değil, **yaşayan bir kayıt eksiği**. Sistem ayrışmayı zaten biliyordu
(`sermaye_koken.ayrisik=True`) ama **köprüyü kurmuyordu**: sen iki sayı görüyor, aradaki terimleri
göremiyordun. Bir farkı BİLMEK ile AÇIKLAYABİLMEK ayrı şeydir.

Yapıldı: `sermaye.broker_mutabakati()` · `alpaca.equity_on()` · `/api/today` alanı.
Terimlerden biri ölçülemezse kalıntı **uydurulmaz** — `None` + neden (bilgisizliğimiz para farkı
gibi okunamaz). İki yönden kasıtlı-kırmızıyla sınandı.

**SANA KALAN:** 2.623,34'ün nereden geldiği HENÜZ BİLİNMİYOR. Köprü onu görünür yaptı, açıklamadı.

### (3) "Hangi işlemin ne kadar kazandırdığını göremiyorum" → **HAKLI**

İşlem satırı `tarih · sembol · çıkış · **R** · rejim · sapma` basıyordu. **Dolar yoktu** —
`pnl_dollars` yalnız çekmecedeydi, yani 15 işlemi tek tek açman gerekiyordu. Kuzey yıldızının
kendi cümlesi bunu zaten yasaklıyor: *"R-birimi geniş stopa YAPISAL ÖNYARGILIDIR; dolar merceği
olmadan sermaye kararı verilemez."* Para sütunu eklendi, **R kaldırılmadı** (yan yana).

---

## 2 · ROADMAP KALEMLERİ — sırayla

| kalem | sonuç |
|---|---|
| ısınma `cleared=0` gerekçesiz | ✅ `_gate_eval` gerekçeyi ÜRETİP ATIYORDU (YASA 6 tersi); iz `why` taşıyor, log `neden_dagilim` basıyor |
| `Ö-51c` ΔP&L bootstrap CI | ✅ dört tavanda da **CI sıfırı içeriyor** — hüküm değişmedi ama SERTLEŞTİ |
| `Ö-51b` ret kimliği | ✅ `entry_reject_ids` (neden → [(ticker,tarih)]); Ö1 artık distinkt PLAN paydasıyla hesaplanabilir |
| `tests/` §-atıf çevrimi | ✅ **kural düzeltildi** — çıplak `§N`'lerin çoğu ROADMAP atfı DEĞİLMİŞ; 23 dosya çevrildi, **88 atıf bilerek bırakıldı** |
| `Ö-49` çapa çürümesi kalanı | ✅ **yeniden ölçüldü: beş kusur zaten kapanmış** (`report()` 7,75 sn/576 parse → **1,75 sn/97 parse**) |
| `Ö-26` değer-eşitliği | ✅ **yeniden ölçüldü: "26 kapısız çift" bayat** — 13 kapalı, 5 bağlı, 9 gerekçeli; `_divergence_hesapla` **ayrık 0** |

---

## 3 · BU GECE ÖĞRENDİKLERİM (hepsi kendi hatamdan)

1. **Yasa beni yakaladı.** `alpaca.equity_on` eklemem bir satır çapasını bayatlattı ve
   `codelaw.report()["ok"]` anında `False` oldu. Düzeltme satır numarası güncellemek DEĞİL,
   **sembole çevirmek** oldu — doktrin: satır çapası sessizce çürür, sembol çapası yüksek sesle.
2. **Dizgi araması üç kez yanılttı.** `"neden_dagilim" in src` yardımcının ADINDA eşleşiyordu;
   `"ticker" in blok` kodun `t` değişkenini göremiyordu; çivi penceresi (`s[i:i+2200]`) kendi
   kendini ölçüyordu. Üçü de AST'ye çevrildi ve kasıtlı-kırmızıyla ısırdıkları doğrulandı.
3. **Hareketli ağaç.** Suite'i üç kez erken başlattım ve altından dosya değiştirdim. Doğrusu:
   **önce bütün düzenlemeler, sonra TEK otoriter suite.**
4. **Bayat kalemler bayatlığı ölçen kalemde bile var.** `Ö-49` ve `Ö-26`'nın ikisi de ölçüldüğünde
   büyük ölçüde kapanmış çıktı. Prozadan okumak ölçmek değildir.

---

## 4 · SANA KALANLAR — bende açılmayanlar

1. **`A1` korumayı kur** — emri verdin, icra canlıda (pano `koruma_kur`, üç kapı). Dört pozisyon
   çıplak, ölçülen duvar 56,4 saat. Ben broker emri veremem.
2. **`A2` bildirim kanalı kimliği** — `B2`(c) kararın bunu ŞART koşuyor; kimlik girilene dek
   politika yazılı ama **teslim etmiyor**.
3. **`B1` pullback silahsızlanması** kararı.
4. **Erişim:** QC login, FINVIZ.
5. **Yeni:** `broker_mutabakati`'nın gösterdiği **2.623,34** — kaynağı araştırılmalı.
