# ENVANTER — WP-E 6 BOŞLUK SINIFI + E2 CANLI-GEÇİŞ (2026-08-22, SALT-KANIT)

**Kapsam:** ROADMAP §3 WP1 açık kalemi "WP-E 6 boşluk sınıfı (#1/#2/#5/#6/#7/#8) + E2 canlı-geçiş"
(ROADMAP.md:328; H0 tablosu ROADMAP.md:199; WP1 SIRASI ⑦ ROADMAP.md:113). Bu tur KOD DEĞİŞTİRMEZ,
HÜKÜM VERMEZ — kanıt getirir; kart/karar Rol-1'in. UYDURMA YASAĞI: ölçülemeyen her kalem None+neden.

**Ölçüm tabanı beyanı:** yerel `state/` canlı değildir; canlı sayılar A1'den (ubuntu@130.61.126.87)
**salt-okuma ssh-stdin** ile çekildi (emsal: `research/olcumler/exe007_broker_teyit_2026-08-22/canli_cek.py`;
betik `meridian.store` üzerinden yalnız OKUR, hiçbir dosya/emir/POST üretmez). Çekim zamanı:
**2026-08-22T18:43:46Z** (+ ek çekim aynı dakikalar). Ham çıktı EK-A'da aynen gömülü (scratchpad
kalıcı değil; kanıt bu belgede korunur). Kod kanıtları yereldeki main tepesinden (987b552).

---

## 1. ALTI BOŞLUK SINIFI NEREDEN GELİYOR — adlar ve tanımlar

Kaynak: `docs/TESHIS-WPE-AYNA-DOLUM-2026-08-10.md` §2 — teşhis **8 sınıf** çıkardı (B1-B8).
ROADMAP'in "(#1/#2/#5/#6/#7/#8)" gösterimi bu numaralamanın kendisidir; #3+#4 (koruma ailesi)
2026-08-10'da v232 ile kapatıldığı için başlıkta 6 kaldı. Sınıfların adı ve tek-cümle tanımı:

| # | Sınıf adı (teşhisteki) | Tanım (teşhis 2026-08-10) |
|---|---|---|
| #1 | `karar_cikisi_dolum_korlugu` | Karar-çıkışlarının (time_stop/regime_flip/giveback — fotoğrafta kapanışların %38'i) aynadaki GERÇEK dolum fiyatı hiçbir deftere yapısal olarak akmıyor (`DELETE /v2/positions` yeni coid doğurur, yama yalnız `by_coid[plan_id]` bacaklarını okur) |
| #2 | `tek_atis_yamasi` | Çıkış-dolum yaması yalnız AYNI TURDA kapananlara bakıyor; kaçırdığını bir daha denemiyor (giriş yarısı E2 her tur yeniden denerken — asimetri); arıza dalları yamaya hiç varmadan dönüyor |
| #3 | `koruma_oco_dolumu_zincir_disi` | Koruma-OCO dolumu (pozisyonun aynada GERÇEK kapanışı) hiçbir deftere bağlanmıyor + mutabakatta yanlış sınıf (`split_brain`) üretiyor |
| #4 | `koruma_x_cikis_kuyrugu_carpismasi` | Korumalı pozisyonda karar-çıkışı yapısal olarak başarısız: `close_engine_position` koruma OCO'sunu tanımıyor, rehinli hisse `DELETE` reddi + sonsuz `cikis_yetimi` |
| #5 | `kismi_dolum_sinifsiz` | Kısmi dolum üç halkada yanlış/eksik: E2 yaması ilk fotoğrafı donduruyor, geç dolum görünmez, SB-2'de `kismi_dolum` sınıfı yok |
| #6 | `fill_eq_now_anakronizmi` | SB-2 sınıflandırıcısı "dolum anının tabanı" diye BUGÜNÜN açılış öz sermayesini kıyaslıyor; yaşlı pozisyonda sebep UYDURULUYOR |
| #7 | `pencere_bosluklari` | `orders(limit=200)` sayfasız — pencereden taşan dolum "dolmadı" sanılıyor; noop/waiting/refused günleri reconcile'a hiç varmıyor |
| #8 | `motor_yetimi_kabul_yolu_yok` | Aynanın doldurduğu ama iç motorun doldurmadığı giriş ALARMDA bitiyor; üç ayrı olgu (giriş-yetimi · çıkış-gecikmesi · taşıma-gecikmesi) tek adla okunamıyor; kabul/kapatma yolu yok |

---

## 2. BUGÜNKÜ DURUM — sınıf × durum tablosu (kod kanıtı + canlı kanıt)

**Önce çerçeve gerçeği (Rol-1'in dikkatine, hüküm değil kanıt):** ROADMAP bu 6 sınıfı bugün H0
("TASARIM ARTEFAKTI YOK", ROADMAP.md:199) ve WP1 SIRASI ⑦'de "tasarım ister" (ROADMAP.md:113)
diye taşıyor. Oysa git tarihçesi iki kapatma commit'i içeriyor ve İKİSİ DE main'de:
- `ffdac50` (2026-08-10) — "WP-E #3+#4 koruma-ailesi düzeltme (v232)": iptal→kapat sırası + koruma dolumu kitaba.
- `531ea2b` (2026-08-12) — "WP-E kalan 6 boşluk KAPANDI (v234)": commit gövdesi #1/#2/#5/#6/#7/#8'i tek tek sayar.

ROADMAP'te v234 kapanışının HİÇBİR anlatısı yok (`grep "karar-çıkışı dolum\|retry-kuyruk\|exit_fill"
ROADMAP.md` → 0 satır). Mekanizmaların canlıda KOŞTUĞU bu turda ölçüldü (aşağıda satır satır) —
satır, Ö-49 (bayat-beyan) sınıfının ADAYIdır; hükmü ve tahta düzeltmesini Rol-1 verir. Karşı-okuma
da kayda geçsin: depo dersi "bir kalem ancak artefaktı canlıda doğrulanınca ✅" (ROADMAP.md:459) —
sınıf başına davranışsal kanıt eksikleri gerçekten var ve tabloda ayrı sütunda.

| # | Kod tarafı (dosya:satır) | Canlı kanıt (A1, 2026-08-22T18:43Z, salt-okuma) | Açık kalan (kanıt satırıyla) |
|---|---|---|---|
| #1 | KAPALI v234: `DELETE` cevabından `close_order_id` kuyruğa (`loop.py:150-165` blok + `loop.py:244-248` "KARAR KOLU"); reconcile yamalar | Mekanizma canlıda kurulu (`broker_reconcile.exit_fill` anahtarı VAR: `{bekleyen 1, yamalanan 2, vazgecilen 0}`); ama canlı 8 kapanışın exit_reason'ı stop 4 · target 2 · target_gap 1 · stop_gap 1 — **karar-çıkışı vakası 0** | "karar" kolunun canlı davranışsal kanıtı YOK (vaka hiç oluşmadı — ölçülemedi, mekanizma kusuru değil örneklem yokluğu) |
| #2 | KAPALI v234: `EXIT_FILL_KEY` kalıcı kuyruk, her reconcile turunda yeniden dener, `EXIT_FILL_MAX_TRIES=5`, tavan `EXIT_FILL_CAP=80`, vazgeçiş OLAYLI (`loop.py:165-195`, `loop.py:2973`) | **ÇALIŞIYOR:** yamalanan 2 · bekleyen 1 (`NUE`, kaynak=`bacak`, since 2026-08-19, **tries 3/5**, close_order_id null) · vazgeçilen 0; canlı trades'te `alpaca_fill_price` 5/8 dolu, `mirror_divergence` 5/8 (LLY icra sapması %1,208 ölçülmüş — `drift` kaydı) | NUE kaydı 2 tur içinde ya dolar ya tavana varır → dürüst-vazgeçiş (`None`+neden) dalının İLK canlı sınaması; izleme kalemi |
| #3 | KAPALI v232: `_koruma_dolumu_bul`/`_koruma_dolumu_isle` (`loop.py:3073-3120`) — koruma dolumu kitaba `koruma_stop|koruma_hedef` ile işlenir, `drift_sinifi=koruma_dolumu` (split_brain değil), fiyat okunamazsa İŞLENMEZ (None+neden) | Anahtar canlıda VAR ve boş: `positions.koruma_dolumu = []` — koruma dolumu vakası hiç oluşmadı | Davranışsal kanıt YOK (vaka 0; mirror_orders'ta held 12 emir duruyor — koruma bacakları dolarsa ilk kanıt oluşur) |
| #4 | KAPALI v232: `close_engine_position` DELETE'ten ÖNCE aynı sembolün koruma-SINIFI emirlerini iptal eder (`alpaca.py` fonksiyon docstring "ÇIPLAK PENCERE — BEYANLI" + `coid_sinifi` yeniden kullanımı, `alpaca.py:511-530`); iptal düşerse kapatma DENENMEZ | Dolaylı: `exit_orphans = []` (teşhisin öngördüğü sonsuz `cikis_yetimi` gürültüsü yok) | Korumalı-pozisyonda-karar-çıkışı bileşik vakası canlıda hiç yaşanmadı → doğrudan davranışsal kanıt YOK; teşhisin DOĞRULANAMADI notu (Alpaca DELETE-reddi dış-API semantiği) hâlâ canlıda tek senaryoyla sınanmadı |
| #5 | KAPALI v234: `_kismi_dolum_tespiti` (`loop.py:2745-2766`) emrin kendi `filled_qty vs qty` kanıtından sınıflar; E2 yaması `partially_filled` satırı DONDURMAZ (kısmi-tazeleme); sayaç `kismi_tazelenen` | Sayaç canlıda YAZILIYOR: `entry_slippage = {eslesen 0, yazilan 0, acilis_yok 0, kismi_tazelenen 0}` — vaka 0. Ö-53 ölçümü bağımsız teyit: canlı giriş emirlerinin HEPSİ tam doldu (AMGN 22→22 · BDX 40→40 · CRM 19→19 · EMR 37→37 · BKNG 22→22; ROADMAP.md:199) | Davranışsal kanıt YOK (kısmi dolum canlıda henüz hiç görülmedi — ölçülemedi) |
| #6 | KAPALI v234 + BU HAFTA GENİŞLETİLDİ: `dolum_eq` makbuz damgası + damga yoksa dürüst `olculemedi(anakronizm)` (`loop.py:1454-1455`, `loop.py:2562-2615`); Ö-53 (08-22): makbuza `eq_ayna` + `ayna_taban` sınıfı (v257) ve B+D kararı — ayna kitabın tabanıyla boyutlanır (`ayna_taban` dalı `loop.py:2651-2672`), kitap aynanın adedini benimser `_adet_benimse` (v258, `loop.py:2680`) | `size_law` 11 makbuz: `dolum_eq` dolu **9/11** · `eq_ayna` dolu **0/11** (v257 bugün indi; eski makbuza geri doldurma bilinçli YOK — uydurma olurdu). Sınıflandırıcı artık sebep UYDURMUYOR: qty_drift 4 kayıt `makbuzsuz_boyut`×3 (EMR 64/37 · BKNG 43/22 · AMGN 33/22) + `kitap_kaydi`×1 (MRNA 13/8) — teşhisin korktuğu `boyutlama_tabani/derisk_carpani` uydurması 0 | `eq_ayna`/üç-taban makbuzunun ve `_adet_benimse`nin İLK canlı davranışsal kanıtı yeni gönderim bekliyor (bugünkü 7 açık pozisyonun makbuzları alanı taşımıyor — ROADMAP.md:199 "İLERİYE DÖNÜK" şerhi) |
| #7 | KAPALI v234: `orders()`a `after/until` (B7a, `alpaca.py:316-334`), sayfalı çekim `_alpaca_emir_penceresi` + hedef `_emir_penceresi_hedefi` (14g ufuk, `loop.py:2773-2830`), tavan 5×200, kapsanamama BEYANLI (`kapsandi=False` + olay); B7b: noop/waiting/refused günleri `_reconcile_gunu_atlandi` OLAYLI (`loop.py:1232-1361`) | **ÇALIŞIYOR:** `emir_penceresi = {sayfa 1, n_emir 28, kapsandi TRUE, en_eski 2026-07-14, hedef 2026-08-19, neden null}` — pencere hedefi kuyruktaki NUE'den doğru türetilmiş | Kapanmış görünüyor; çok-sayfalı dal (sayfa>1) canlıda henüz hiç tetiklenmedi (bugünkü debide 28 emir tek sayfaya sığıyor) — tavan/beyan dalının davranışsal kanıtı doğal olarak yok |
| #8 | KISMEN v234: yetim ÜÇE ayrıldı `tasima_gecikmesi/cikis_gecikmesi/giris_yetimi` (`loop.py:3405-3451`), `engine_orphans_sinifli` reconcile'a yazılıyor; kod "SALT SINIFLANDIRMA — emir üretmez" der | Anahtar canlıda VAR: `engine_orphans_sinifli` mevcut, `engine_orphans = []`; broker'daki NVDA `external` sınıfında (motor emri değil — giriş-yetimi DEĞİL) | **Teşhisin kendi tarifiyle de AÇIK:** kabul-mü-kapat-mı POLİTİKASI operatör kararı gerektirir ve hiçbir yerde verilmedi (kod bilinçli emir üretmiyor); sınıf tam kapanışı = operatör politika kalemi |

**Bu haftanın işleri hangi sınıfa denk geldi (görev brifindeki liste, ölçülmüş karşılıklarıyla):**

| Bu haftanın işi | Denk geldiği sınıf/hat | Gerçek tarih + kanıt |
|---|---|---|
| E2 sayfalı pencere | **#7** (B7a/B7b) | Bu hafta DEĞİL — v234, 2026-08-12 (`531ea2b`); bu hafta üzerine Ö-52 `defter_teyit` "KIRPIK DEFTERDE KARŞILIKSIZ DENMEZ" tüketicisi bindi (`loop.py:3023-3029`, 55d72b3, 08-22) |
| exit-fill yaması | **#1+#2** | Bu hafta DEĞİL — v234, 2026-08-12 (`531ea2b`); canlıda bu hafta İLK davranışsal sayılar oluştu (yamalanan 2 · bekleyen 1) |
| broker_teyit (Ö-52 / `EXE-2026-007`) | Yeni boyut — 8 sınıfın hiçbiri değil; #1/#2'nin ölçtüğü "dolum fiyatı" boşluğunun yanına "işlem broker'da VAR MI" boşluğunu ekledi (teşhis bunu saymamıştı) | 08-21 bulgu + 08-22 kart measured (Ö1=%25: 8 canlı işlemin 2'si — ALL/VLO — broker'da hiç yok), damgalayıcı dağıtıldı (`cbcdeed`/`73055ed`) |
| eq_ayna + ayna_taban (Ö-53) | **#6 ailesi** (SB-2 dürüst-sınıf hattının devamı) + WP2 defter bütünlüğü | 08-22: kök neden (iki defter FARKLI sermaye tabanı, `416e4f0`) → v257 `eq_ayna`+`ayna_taban` → operatör B+D kararı v258 (`c726a19`); suite 6281/0 |
| dinlenen-limit ölçümleri | Sınıf değil — WP1-B **23c** hattı + E1 hüküm zinciri (E2 canlı-geçişin "yeniden hüküm" bacağı) | `EXE-2026-005` B kolu boş küme (yapısal, Ö-51d hükmü 08-22) · `EXE-2026-006` measured (E1 hükmü yeniden açıldı) · Ö-51b/51c kapandı → `B4` operatör kararı A+C (bacak KAPALI, gerekçe yeniden temellendi, `ba5dddb`) · `EDG-2026-043` K=6 ölçüldü, altı CI 0-içi, hüküm ASKIDA (`f25c625`) |

---

## 3. E2 CANLI-GEÇİŞ — defterin bugünkü doluluk/kapsama fotoğrafı (canlı, salt-okuma)

"Canlı-geçiş" çapası: ROADMAP.md:371/2414 — *"E2 defteri gerçek dolumla dolmaya devam eder;
canlı-geçiş kapısında E2 kanıtıyla yeniden hüküm"* (REF·limitsiz işletim noktasının, `EXE-2026-001-R2`,
gerçek dolum kanıtıyla yeniden yargılanması) + canlı-TCA rezervasyonu (denetim YÜ-1, ROADMAP.md:384).

### 3a. E2 defteri (`entry_execution.jsonl`, canlı)

| ölçü | değer |
|---|---|
| toplam satır | **30** (tarih aralığı 2026-08-05 → 2026-08-21) |
| motor kırılımı | ayna **15** · iç **15** (başka motor adı yok) |
| ayna `karar` dağılımı | submitted 15 (ret/kapı satırı yok) |
| ayna fill doluluk | **13/15 dolu** · 2 `fill=None` (fill_status: filled 13 · None 2) |
| alan tamlığı (ayna-submitted 15) | `fill/fill_qty/fill_status/fill_vs_resmi_acilis_bps/fill_vs_limit_bps` **beşi de 13/15** (dolan her satırda 5 alan tam — yarım satır yok) · `limit/plan_id/date` 15/15 |
| iç motor | fill 15/15 (simülasyon dolumu; açılış-bps totoloji beyanıyla — sayısal alan değil) |
| `fill=None` 2 satırın okunması | pencere borcu DEĞİL: `emir_penceresi.kapsandi=true` iken dolmamış → meşru "dolmadı" adayı (`dolmama_orani` paydası) |

### 3b. trades defteri (canlı)

| ölçü | değer |
|---|---|
| toplam | **893** = replay_seed 885 + live_paper **8** |
| canlı 8'in exit_reason'ı | stop 4 · target 2 · target_gap 1 · stop_gap 1 (**karar-çıkışı 0**) |
| `alpaca_fill_price` / `mirror_divergence` | **5/8** dolu (K2/K3 aday satırları); `alpaca_fill_beyan` 0 |
| `broker_teyit` damgası | **8/8 `None`** — Ö-52 damgalayıcısı dağıtıldı (08-22) ama İLK gerçek reconcile turu henüz koşmadı (son reconcile ts=2026-08-21; bugün Cumartesi). ROADMAP beklentisi: ilk turda 6 teyitli + 2 karşılıksız (ALL/VLO) + pano kırmızı satır (ROADMAP.md:175) |

### 3c. Kuyruklar + mutabakat (canlı)

| ölçü | değer |
|---|---|
| `exit_fill_pending` | 1 (NUE · bacak · since 08-19 · tries 3/5) · yamalanan 2 · vazgeçilen 0 |
| `mirror_exit_pending` | 0 |
| `emir_penceresi` | sayfa 1 · 28 emir · kapsandi true · hedef 2026-08-19 |
| `entry_slippage` sayaçları | artık reconcile'da (YASA-6 bulgusu kapalı): eslesen/yazilan/acilis_yok/kismi_tazelenen = 0/0/0/0 (o gün yeni dolum yoktu) |
| pozisyon mutabakatı | qty_drift 4 (makbuzsuz_boyut EMR/BKNG/AMGN · kitap_kaydi MRNA) · external [NVDA] · orphans/exit_orphans/ghosts boş · koruma_dolumu [] · icra drift 1 (LLY %1,208) |
| `mirror_orders` | 65 coid: filled 19 · canceled 21 · expired 4 · held 12 · new 7 · accepted 2 |

### 3d. "Canlı-geçiş" için eksik NE — ölçülmüş açık liste

1. **Örneklem, eşiğin altında (en büyük eksik):** `EDG-2026-042`nin DONUK eşikleri K1 n≥30 & ≥10 seans,
   K2/K3 n≥15 & ≥6 seans. Bugün: **K1 n=13 / 4 seans** (E2 ayna dolumları — 3a ile bire bir tutarlı),
   **K2/K3 ölçülebilir n=0** (5 aday satırın 5'i `broker_teyit` damgasız → kill kuralı düşürdü).
   Kart kendi beyanıyla K1 eşiğine ~4-6 hafta uzakta; otomatik haftalık koşum kurulu (her Cumartesi;
   ilk anlamlı tekrar 2026-08-29).
2. **Teyit boyutu henüz damgasız:** 8/8 canlı satır `broker_teyit=None`; ilk gerçek reconcile
   (2026-08-24 EOD, Pazartesi) basacak. Damga basılmadan Ö-54/EDG-042 çıkış kovaları ölçülemez.
3. **Karar-çıkışı dolum örneklemi 0:** #1 mekanizması canlıda hiç gerçek vakayla sınanmadı
   (canlı kapanışların tamamı dokunuş/gap çıkışı). E2'nin "öbür yarısı" ancak ilk time_stop/
   regime_flip/giveback kapanışında veri üretir.
4. **Koruma-dolumu ve kısmi-dolum örneklemleri 0:** #3/#5 dalları canlıda hiç ateşlenmedi;
   canlı-geçiş kapısında bu dilimler için tek kanıt kod+test olacak (davranışsal kanıt yok).
5. **`eq_ayna` makbuzları 0/11:** ayna-boyut tabanı bugünden İLERİYE kayıtlı; mevcut 7 açık
   pozisyonun sapması `makbuzsuz_boyut/kitap_kaydi` sınıfında kalmaya devam eder (geri doldurma
   bilinçli yasak). Adet ayrışmasının kapanması B+D'nin yeni-gönderim davranışına bağlı.
6. **E1 yeniden-hüküm bacağı ARTIK RAKAMLI ama ASKILI:** B4 kararı A+C ile bacak kapalı; tek açık
   argüman `EDG-2026-043`te ölçüldü (6 CI de 0-içi) ve hüküm OKUMA KURALI gereği `EDG-2026-042`nin
   gerçek-friksiyon bandını bekliyor (~4 hafta) — bant gelmeden B4 yeniden açılamaz (kill).
7. **Ufuk penceresi temizliği tek seferlik ölçüm:** Ö-52 bulgusundaki karşılıksız 2 satır bugünkü
   yansıma ufkunun ALTINDA (885/886 < 887) — ileride ufuk kayarsa yeniden bakmak gerekir; damga
   basılınca bu yapısal olarak görünür olacak.

---

## 4. KART-ADAYI ENVANTERİ (öneri değil ENVANTER — eşik/kill'ler kaynağındaki hâliyle)

| kalem | tür | eşik / kill (kaynaktan aynen) | bugünkü sayı | kaynak |
|---|---|---|---|---|
| E2 doluluk → gerçek friksiyon | KART VAR: `EDG-2026-042` (measuring, otomatik Cumartesi) | K1 n≥30 & ≥10 seans · K2/K3 n≥15 & ≥6 seans · kill: teyitsiz satır kıyasa giremez · karar kuralı EDG-040 başabaş [5-15] bps'e karşı | K1 13/4 seans (medyan +15,0 bps) · K2/K3 0 | ROADMAP.md:179 · `research/cards/EDG-2026-042-*` |
| B4 yeniden-açılma kapısı | KART VAR: `EDG-2026-043` (measured, hüküm ASKIDA) | kill: EDG-042 gerçek bandı gelmeden B4 yeniden açılamaz; hüküm yalnız banda düşen hücreden okunur | 6/6 CI 0-içi (A kolu −7,3k/−5,8k/−1,3k · B kolu +4,0k/+3,8k/+2,3k nokta) | ROADMAP.md:176 · `f25c625` |
| #8 giriş-yetimi kabul/kapatma politikası | OPERATÖR kalemi (kod bilinçli emir üretmez) | teşhis: "kabul-mü-kapat-mı politikası operatörde"; asgari teşhis adımı (sınıf ayrımı) v234'te yapıldı | canlı giriş-yetimi 0 (NVDA `external`) | TESHIS-WPE-AYNA-DOLUM §B8 · `loop.py:3405-3451` |
| Ö-52 damganın ilk gerçek turu | İZLEME (kart measured, iş bitmiş; doğrulama kalemi) | beklenen: 6 teyitli + 2 karşılıksız + `karsiliksiz_islem` alarmı | 8/8 None (2026-08-22T18:43Z) | ROADMAP.md:175 · bu belge §3b |
| NUE exit-fill kaydı | İZLEME | `EXIT_FILL_MAX_TRIES=5`; tavanda dürüst-vazgeçiş (fiyat None+neden, OLAYLI) | tries 3/5, since 08-19 | `loop.py:166` · bu belge §3c |
| Ö-53 kalıntı: mevcut 7 pozisyonun makbuzsuz sapması | İZLEME/politika-sonrası doğal erime | B+D yeni gönderimde işler; geriye doldurma YASAK (uydurma) | eq_ayna 0/11 · qty_drift 4 | ROADMAP.md:199 · bu belge §3c |
| ROADMAP satır tazeliği: "WP-E 6 boşluk sınıfı" H0'da | Rol-1 tahta kalemi (Ö-49 bayat-beyan ADAYI — hüküm verilmedi) | — | kod: `531ea2b`+`ffdac50` main'de · canlı: exit_fill/emir_penceresi/engine_orphans_sinifli anahtarları A1 reconcile'ında | ROADMAP.md:113/199/328 · bu belge §2 |
| Sınıf-başına davranışsal kanıt boşlukları (#1 karar-çıkışı · #3 koruma dolumu · #4 bileşik vaka · #5 kısmi dolum · #7 çok-sayfa dalı) | ÖRNEKLEM BEKLER (eşik oynatmak/vaka üretmek YASAK — 23b emsali) | — | hepsi 0 vaka | bu belge §2 tablo |

---

## EK-A — CANLI HAM ÇEKİM (A1, salt-okuma, 2026-08-22T18:43:46Z; betik: ssh-stdin, `meridian.store` üzerinden yalnız okuma)

```json
{"amac": "WPE-bosluk+E2-canli-gecis-envanteri", "cekim_zamani": "2026-08-22T18:43:46+00:00", "makine": "A1 (canli)",
 "e2": {"n_toplam": 30, "motor_kirilimi": {"ayna": 15, "ic": 15}, "ayna_karar_dagilimi": {"submitted": 15},
        "diger_motor_adlari": {}, "ayna_submitted_n": 15, "ayna_submitted_fill_dolu": 13, "ayna_submitted_fill_none": 2,
        "fill_status_dagilimi": {"filled": 13, "None": 2},
        "alan_tamlik_ayna_submitted": {"fill": 13, "fill_qty": 13, "fill_status": 13, "fill_vs_resmi_acilis_bps": 13,
                                       "fill_vs_limit_bps": 13, "limit": 15, "plan_id": 15, "date": 15},
        "ic_fill_dolu": 15, "ic_acilis_bps_beyanli": 0, "tarih_min": "2026-08-05", "tarih_maks": "2026-08-21"},
 "trades": {"n_toplam": 893, "kaynak_dagilimi": {"replay_seed": 885, "live_paper": 8},
            "exit_reason_dagilimi": {"regime_flip": 171, "stop": 383, "time_stop": 152, "target": 101, "stop_gap": 58, "target_gap": 28},
            "alpaca_fill_price_dolu": 5, "mirror_divergence_dolu": 5, "alpaca_fill_beyan_dolu": 0,
            "canli_n": 8, "canli_broker_teyit_dagilimi": {"None": 8}, "canli_alpaca_fill_price_dolu": 5,
            "canli_exit_reason_dagilimi": {"stop": 4, "target": 2, "target_gap": 1, "stop_gap": 1},
            "canli_ts_close_min": "2026-08-07", "canli_ts_close_maks": "2026-08-21"},
 "broker_reconcile": {"ts": "2026-08-21",
                      "anahtarlar": ["alive_order_syms", "api_ok", "date", "drift", "emir_penceresi", "entry_slippage",
                                     "exit_fill", "failed_submissions", "force_sync", "ghosts", "mirror_drift",
                                     "position_drift", "positions", "stripped", "trail_synced", "updated"],
                      "emir_penceresi": {"sayfa": 1, "n_emir": 28, "kapsandi": true, "en_eski": "2026-07-14", "hedef": "2026-08-19", "neden": null},
                      "entry_slippage": {"eslesen": 0, "yazilan": 0, "acilis_yok": 0, "kismi_tazelenen": 0},
                      "defter_teyit": null,
                      "exit_fill": {"bekleyen": 1, "yamalanan": 2, "vazgecilen": 0},
                      "pozisyon_koruma_dolumu": [], "drift_ozet": {}},
 "kuyruklar": {"exit_fill_pending_n": 1,
               "exit_fill_pending_ozet": {"P-2026-08-05-NUE": {"ticker": "NUE", "kaynak": "bacak", "since": "2026-08-19", "tries": 3, "close_order_id": null}},
               "mirror_exit_pending_n": 0, "size_law_n": 11, "size_law_dolum_eq_dolu": 9, "size_law_eq_ayna_dolu": 0,
               "acik_pozisyon_n": 7},
 "mirror_orders": {"n_coid": 65, "status_dagilimi": {"canceled": 21, "expired": 4, "filled": 19, "held": 12, "new": 7, "accepted": 2}}}
```

Ek çekim (aynı oturum, reconcile pozisyon ayrıntısı):

```json
{"position_drift": true,
 "positions_ozet": {"engine_orphans": [], "exit_orphans": [], "missing_on_alpaca": [],
                    "qty_drift": [{"ticker": "EMR", "local_qty": 64.0, "alpaca_qty": 37.0, "drift_sinifi": "makbuzsuz_boyut"},
                                  {"ticker": "BKNG", "local_qty": 43.0, "alpaca_qty": 22.0, "drift_sinifi": "makbuzsuz_boyut"},
                                  {"ticker": "AMGN", "local_qty": 33.0, "alpaca_qty": 22.0, "drift_sinifi": "makbuzsuz_boyut"},
                                  {"ticker": "MRNA", "local_qty": 13.0, "alpaca_qty": 8.0, "drift_sinifi": "kitap_kaydi"}],
                    "koruma_dolumu": [], "external": ["NVDA"]},
 "drift": [{"ticker": "LLY", "sim": 1229.8848, "alpaca": 1244.7433, "div_pct": 1.208, "drift_sinifi": "icra"}],
 "mirror_drift": true, "ghosts": [], "positions_anahtarlar": ["engine_orphans", "engine_orphans_sinifli", "exit_orphans", "external", "koruma_dolumu", "missing_on_alpaca", "qty_drift"]}
```

**Not (dürüstlük):** `broker_reconcile.defter_teyit = null` (ts=08-21 anlık görüntüsü damgalayıcı
dağıtımından ÖNCE) ile ROADMAP.md:175'in "canlı doğrulandı: defter_teyit={olculemedi 8}" beyanı
ÇELİŞMEZ — doğrulama dağıtım sonrası ayrık koşumdu, reconcile anlık görüntüsüne ilk gerçek tur
(2026-08-24 EOD) yazacak; satır damgaları da o turda basılır (bugün 8/8 None ölçüldü).
