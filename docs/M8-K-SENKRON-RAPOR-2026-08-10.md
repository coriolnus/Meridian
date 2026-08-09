# M8 — K-DEFTERİ ↔ KART SENKRON DENETİMİ (2026-08-10)

**Yazan:** WP-M M7+M8+M9 turu ajanı (salt-denetim; kartlara YAZILMADI).
**Okuyucu (YASA 6):** Rol-1 — U1-U5 kart/README düzeltme ÖNERİLERİ hüküm bekler; U6-U7 ölçüm-anlamı
kararıdır. İkinci okuyucu: bir sonraki WP-M mühendisi (K sayımına dokunmadan önce buradan başlar).
**Görev kaynağı:** keşif 2026-08-09 §WP-M M8 (`docs/KESIF-WP-MKP-2026-08-09.md:58`); ROADMAP:384
"K-defteri↔kart senkronu (retro kartlar)".

**Sınır beyanı:** `research/cards/` YALNIZ OKUNDU (tek bayt yazılmadı) · git komutu KOŞULMADI ·
canlıya/ssh'a DOKUNULMADI · state/'e YAZILMADI. Bu turda yazılan dosyalar: bu rapor +
`meridian/analytics.py` M9 referans-notu (ayrı kalem, K sayımına dokunmaz) + `tests/` v231.

**Denetim-anı beyanı:** kart seti denetim SIRASINDA canlıydı — KYS-2026-002, bu denetimin ilk
okumasında `registered` iken aynı gün içinde `measured_partial`a geçti (paralel KYS-002 ölçüm turu +
Rol-1 hükmü; kartın `verdict` bloğu 2026-08-10). Rapordaki tüm kart alıntıları SON okuma anına
(2026-08-10, bu raporun yazımı) göredir; U2'deki KYS-002 satırı bu tazelikle şerhlidir.

**Yerel-state bayatlık beyanı (UYDURMA YASAĞI):** yereldeki `state/oos_erosion.json` son yazımı
2026-07-30'da kalmış (R1 `pencere_id` damgası ve arşiv işareti YOK; 2 pencere, 1+554 sorgu),
`state/hypotheses.jsonl` 41 satır. Bunlar CANLI A1'in güncel hâli DEĞİLDİR (ROADMAP güncel kaydı
canlıda "oos_erosion 4 pencere R1" diyor). Bu rapor yerel sayıları yalnız MEKANİZMA kanıtı olarak
kullanır; hiçbir satırı "canlının bugünkü değeri" iddiasında değildir.

---

## 0. Mimari tespit — "K defteri" fiziksel olarak nedir?

Denetimin ilk bulgusu sayım hatasından önce gelir: **tek bir K-defteri dosyası YOK.** K yükü üç
ayrı kanalda yaşıyor ve yalnız ikisinin kod tüketicisi var:

| Kanal | Nerede yaşar | Kod tüketicisi |
|---|---|---|
| Araştırma-kartı K'sı (`k_registry` + grid `K+=N` beyanları) | `research/cards/*.yaml` (29 kart) + `research/cards/README.md` düzyazı endeksi | **YOK** — depoda `k_registry`yi ya da kart K'sını okuyan tek satır kod yok (grep: kod tarafındaki tek "research/cards" anmaları yorumdur — `meridian/faz5_cikis.py:28`, `meridian/reflect.py:42`; `k_registry` kodda yalnız `tests/test_kart_kimlik_v219.py:25`te, o da "dokunmaz" beyanıyla) |
| Oturum-içi kapı yoklaması `k_probes` | `state/hypotheses.jsonl` satırlarının `backtest.k_probes` alanı; prescreen raporları | `probgate.p_required_for(k_probes)` (cezanın kendisi) + `analytics.validation_trio` (`meridian/analytics.py:2554` toplar) |
| Oturumlar-arası pencere aşınması | `state/oos_erosion.json` | `oos_erosion.report()` → kapı ek-marjı; + `analytics.validation_trio` (`analytics.py:2550`) |

**Merkezi tüketici** = `analytics.validation_trio` (`meridian/analytics.py:2530`):
`n_trials = sorgu + kp` (`analytics.py:2550-2555`) → `validation.deflated_sharpe(ret, n_trials)`
(DSR K-cezası/deflasyon). Kart kanalı bu toplama **yapısal olarak girmiyor** (bkz. U6).

Yani "K-defteri ↔ kart senkronu"nun mekanik bir senkron kodu yok: senkron, Rol-1'in hükümleri
kartlara/README'ye elle işlemesiyle yürüyor. Aşağıdaki uyuşmazlıkların tamamı bu elle-yürüyen
sürecin bıraktığı boşluklardır — "sayaç retro kartları saymıyor" türü düzeltilecek bir sayaç
bulunamadı, çünkü kartları sayan sayaç hiç yok.

---

## 1. Uyuşmazlık listesi (kanıtlı)

### U1 (ORTA) — EXE-2026-001 K-aritmetiği: eksen yorumları TOPLAMSAL, kural ve kartın kendisi ÇARPIMSAL

- `EXE-2026-001-entry-execution.yaml:16` → `limit_offset` "3 kombinasyon → **K+=3**"
- `EXE-2026-001-entry-execution.yaml:17` → `gap_davranisi` "2 → **K+=2**"
  — iki satır yan yana **3+2=5** diye okunur.
- Oysa: kartın KENDİ trial_ids'i 6 grid hücresi sayıyor (`:26-27`: a/b/c × mkt/cancel) + R2 kararı
  `ref_limitsiz` (+1) = **7**; R1 revizyon metni grid'i açıkça "**3×2**" diye adlandırıyor
  (`:57-58`); ölçüm raporu hükmü "6 hücre koşuldu" diyor (status bloğu `:37`).
- Kural: "K grid'de ÇARPILARAK sayılır" (CLAUDE.md §3). Emsal: **aynı hata sınıfı** EDG-2026-002'de
  yakalanıp düzeltilmişti — `EDG-2026-002-volume-shock.yaml:15`: "3x2=6 KOMBINASYON -> K+=6 (ilk
  kayit K+=5 HATALIYDI; 2026-07-31 duzeltildi — grid carpiminda toplanmaz, carpilir)";
  `research/olcumler/s1_retro/RAPOR.md:199` "K 1 birim eksik kayıtlı".
- Net: beyan 5 ↔ harcanan 6 (+1 R2 = 7) → **1 birim eksik-sayım, EDG-002 vakasının birebir
  tekrarı, bu kez yakalanmamış.** Kart donuk — düzeltme önerisi §5/1.

### U2 (ORTA) — trial_ids geri-doldurma boşluğu: 8 kartta ölçüm koşmuş, kimlik hâlâ "pending"

`k_registry.trial_ids` kartın K'sını HANGİ koşuların harcadığını adlandırır; ölçüm bittiği hâlde
"pending-*" kalırsa kart↔ölçüm-defteri bağı kart içinden kurulamaz:

| Kart | k_registry satırı | status satırı | Durum |
|---|---|---|---|
| EDG-2026-001 | `:18` `[pending-S1-retro]` | `:19` **archived** | S1 somut id ÖNERMİŞ (`s1_retro/RAPOR.md:249`: `[S1-retro-2026-07-31-52wh]`) — işlenmemiş |
| EDG-2026-002 | `:21` `[pending-S1-retro]` | `:22` **archived** | S1 önerisi `RAPOR.md:254`: `[S1-retro-2026-07-31-volshock]` — işlenmemiş |
| EDG-2026-003 | `:20` `[pending]` | `:21` **measured** (K=4) | ölçüm dizini büyük olasılıkla `research/olcumler/wpr_olcum/` — ŞÜPHELİ (dizin↔kart eşlemesi bu turda doğrulanmadı) |
| EDG-2026-004 | `:19` `[pending]` | `:20` **archived** | muhtemel `max_olcum/` — ŞÜPHELİ (aynı neden) |
| EXE-2026-002 | `:76` `[pending-EXE-002-faz5]` | `:78` **measured** (v212, `meridian/faz5_cikis.py`) | koşan trial'ın adı kartta yok |
| EXE-2026-004 | `:72` `[pending-EXE-004-asama1-olcum]` | `:74` **measured_partial** | Aşama-1 ölçülmüş (`cf_cikis_sadakati_2026-08-09/`), id geri yazılmamış |
| EDG-2026-022 | `:53` `[pending-EDG-022-kisit-teshisi]` | `:55` **measured** | ölçüm `edg022_evren_kisit_2026-08-09/`, id geri yazılmamış |
| KYS-2026-002 | `:48` `[pending-KYS-002-r1-taban]` | `:50` **measured_partial** (PBO yarısı) | TAZE (denetim sırasında değişti; ölçüm `kys002_pbo_dsr_taban_2026-08-10/`) — geri-doldurma henüz beklenebilir gecikmede olabilir, ŞERHLİ |

Karşı-örnek (desen ÇALIŞABİLİYOR): 08-01→08-03 dalgasının kartları (EDG-005..008, 010, 012..017,
020, 021, KYS-001) trial_ids'i gerçek koşu adlarıyla doldurmuş; EXE-001'in id İÇERİĞİ de tam
(7 id). Boşluk üç kümede: ilk 07-31 dalgası (EDG-001..004) + en yeni 08-07..08-10 dalgası
(EXE-002/004, EDG-022, KYS-002). Not: `registered` durumundaki kartlarda (EDG-019, EXE-003)
"pending-*" MEŞRUDUR — ölçüm henüz koşmadı; onlar bu listede değildir.

### U3 (ORTA) — README endeksi (K-defterinin insan-okur yüzü) bayat: aktif liste 8/8 yanlış

`research/cards/README.md:7-14` "Aktif kartlar" sekiz kart sayıyor; sekizinin de kart-içi durumu
artık farklı:

| README satırı (beyanı) | Kartın gerçek durumu |
|---|---|
| `:7` EDG-017 "registered 2026-08-02" | **archived** 2026-08-02 ~21:05 (`EDG-2026-017:32-33`) |
| `:8` EDG-018 "registered 2026-08-02" | **askiya_veri_kapisi** 2026-08-02 ~19:30 (`EDG-2026-018:37-38`) |
| `:9` EDG-020 "registered 2026-08-02" | **archived** 2026-08-03 (`EDG-2026-020`) |
| `:10` EDG-021 "registered 2026-08-03" | **measured** 2026-08-03 (`EDG-2026-021`) |
| `:11` KYS-001 "registered 2026-08-02" | **archived** 2026-08-02 ~22:30 (`KYS-2026-001`) |
| `:12` EXE-001 "registered" | **measured** 2026-08-03 (+R2 2026-08-07) (`EXE-2026-001:30`) |
| `:13` EDG-001 "registered" | **archived** 2026-07-31 (`EDG-2026-001:19`) |
| `:14` EDG-002 "registered" | **archived** 2026-07-31 (`EDG-2026-002:22`) |

Ters yönde: bugün GERÇEKTEN aktif (registered) iki kart — EDG-2026-019 (2026-08-09) ve
EXE-2026-003 (2026-08-09) — README'nin aktif listesinde **hiç yok** (KYS-2026-002 de kayıt +
kısmî-ölçüm yaşadı ve endekste hiç görünmedi).
Ayrıca `README.md:29-34` "Kart-adayı yeni bulgular" bölümü KIYAS-KİRLENMESİ'ni "Rol 1 tasarımı
bekliyor" diye tutuyor; oysa KYS-2026-001 kartı doğmuş, ölçülmüş ve **arşivlenmiş** bile
(halefi KYS-2026-002 de kayıtlı). Ve `README.md:37` "EDG-2026-019 KULLANILMADI … **numara
emekli**" diyor; EDG-2026-019 numarası 2026-08-09'da skill-görüş kartına BİLİNÇLİ olarak verildi
(`tests/test_kart_kimlik_v219.py:10`: "üçüncü seferde numara grep'lendi → EDG-2026-019 (o an
gerçekten boştu)") — kararın kendisi meşru görünse de README'deki emeklilik beyanı yürürlükte
sanılabilir: endeks kendi kartlarıyla çelişiyor.

### U4 (ORTA; eşlemeler ŞÜPHELİ) — Retro kuyruğun kartsızları: K yükü yalnız düzyazıda

`README.md:16-27` retro kuyruğu "S1 ajanı biçimlendirecek; ölçümler ÖNCE koşmuştu, K-defterine
sayılı" diye açar. Bugünkü hâl:

- **Kart dosyası HİÇ doğmamış retro ölçümler:** EAP large-cap (ölçüm dizini
  `research/olcumler/eap_olcum/` DURUYOR) · Insider CMP · Short-interest (FINRA 24 ay; README
  "12 hücre 0" → K yükü ~12? — ŞÜPHELİ, kartsız olduğu için beyan yok) · PEAD üçlüsü. Bunların
  K'sı yalnız README düzyazısında ve (EAP için) ENG-LOG'da yaşıyor; kart şeması (`k_registry`)
  hiçbirine açılmamış. Retro kuyruğun "biçimlendirilecek" vaadi bu dördü için 10 gündür askıda.
- **ŞÜPHELİ eşlemeler (karar Rol-1'in):** README `:21` "Çıkış paketi P1/P2/P3 (**K=3**)" ↔
  EDG-2026-003-rampa-p3 kartı **K+=4** (2×2 çarpım; `EDG-2026-003:14`). README `:22-26`
  "Uzun-ufuk mega-cap trend kolu (**K=2**)" ↔ EDG-2026-009-trend-kolu-rafine **K+=4**
  (`EDG-2026-009:16`). İki okuma da mümkün: (a) README satırları kart-öncesi ORİJİNAL ölçümler,
  EDG-003/009 bunların HALEF kartları — o zaman orijinallerin K'sı (3+2) hâlâ kartsız; (b) aynı
  ölçümün iki kaydı — o zaman K beyanları (3↔4, 2↔4) çelişiyor. Hangisi olduğuna bu denetim
  karar VEREMEZ (ölçüm dizinleri `cikis_paketi/` ve `trend_kolu/` ile `wpr_olcum/` /
  `trend_rafine/` ayrı ayrı duruyor — iki ölçümün ayrı olduğu okuma (a)'yı destekliyor ama
  hüküm Rol-1'de).

### U5 (DÜŞÜK) — "Beyan edilen K" ↔ "harcanan K" ayrımının makine-okunur alanı yok

Dört kart, harcanmamış/sayılmayan K'yı DÜZYAZIYLA beyan ediyor — dürüst, ama şemasız:

- EDG-2026-011 (`:29-30`): grid K+=2, `trial_ids: [inplay_olcum/ASKI — K harcanmadı]` — trial_ids
  alanına gömülü serbest metin.
- EDG-2026-006: K+=1 beyan; status "kill#2 ÖN-ADIMDA tetiklendi (ikiz koşum HİÇ AÇILMADI — K
  tasarrufu)".
- EDG-2026-018 (`:50`): "K-muhasebesi: kapı hücresi harcandı, sinyal hücresi HARCANMADI" — üstelik
  harcanan "kapı hücresi" ön-kayıt grid'inde K olarak HİÇ beyan edilmemişti (`:22` yalnız sinyal
  hücresi K+=1; `RAPOR_018.md:213-215` de K muhasebesini açıkça Rol-1'e bırakır).
- BASE-2026-001: `trial_ids: [karne — K sayılmaz (eşiksiz tanı)]` — yine alan-içi düzyazı.

Sonuç: kart popülasyonundan "toplam harcanan K" TEK bir sayıya indirilemiyor — beyan/harcama
ayrımı alan olarak yok, düzyazı gömmeleri makine-okunurluğu bozuyor. (Bu bir uyuşmazlık değil
KURAL BOŞLUĞU; şema kararı Rol-1'in — §5/5.)

### U6 (YAPISAL) — Kart K'sı merkezi K-cezasına (DSR n_trials) hiç girmiyor; beyan da bunu söylemiyor

`analytics.validation_trio` n_trials'ı iki kanaldan toplar (`analytics.py:2550-2555`): aşınma
sorguları + hipotez `k_probes`. Araştırma kartlarının K'sı (29 kartta beyanlı onlarca hücre)
bu toplama GİRMİYOR — kartları okuyan kod yok (§0). Bu kısmen SAVUNULABİLİR (kart ölçümleri
sandbox'ta koşar ve canlı OOS penceresine soru sormaz; `oos_erosion.py:21-25` "SANDBOX SAYMAZ —
BİLİNÇLİ" beyanı bu ayrımı zaten çizer) — ama `n_trials_beyan` (`analytics.py:2575-2577`)
alt-sınır gerekçesi olarak YALNIZ retro-damga yasağını sayıyor; kart-kanalının dışarıda kaldığı
beyanı yok. Karar Rol-1'in: (a) beyanı genişlet ("kart-kanalı sayılmaz çünkü ...") ya da
(b) sayımı genişlet (DSR n_trials'a kart K'sı girer — ölçüm-anlamı DEĞİŞİR, deflasyon büyür).
Bu turda İKİSİ DE YAPILMADI (rapor-önce sözleşmesi).

### U7 (YAN BULGU; M8 kapsamına bitişik) — "ömür-boyu" iddiası ↔ rotasyon-yerel sayım

`validation_trio` docstring'i n_trials'ın aşınma bacağını "aşınma defterinin **ömür-boyu** sorgu
sayısı" diye adlandırır (`analytics.py:2535-2536`); ama okuduğu `oos_erosion.report().toplam_sorgu`
R1'den (2026-07-30) beri YALNIZ yürürlükteki rotasyonun pencerelerini toplar
(`oos_erosion.py:205-214`; arşiv ayrı blokta, toplama bilinçli olarak katılmaz). Yani rotasyonla
R0'ın sorgu yükü DSR n_trials'tan düştü (kanıt: `oos_erosion.arsivle` docstring'i R0 için "434
sorgu" anar; yereldeki bayat kopya R0-dönemi 555 sorgu taşıyor). Kapı ek-marjı için rotasyon-yerel
sayım DOĞRU (report() kendi gerekçesini yazmış: iki sınav kâğıdı toplanmaz); DSR için hangisinin
doğru olduğu — "seçilim baskısı rotasyonla sıfırlanır mı?" — bir ölçüm-anlamı sorusudur ve
docstring ile davranış bugün AYNI ŞEYİ SÖYLEMİYOR. Karar Rol-1'in; bu tur yalnız kaydeder.

---

## 2. Çift-sayım denetimi — BULUNAMADI

- `state/hypotheses.jsonl` (yerel, 41 satır): `k_probes` taşıyan 14 satırın değişkenleri tamamı
  canlı-knob aileleri (`exit.scale_out_frac`, `entry.w_prox`, `regime.min_exposure_score`,
  `entry.rs_rating_min`, `exit.breakeven_r`, `entry.w_rs`, `entry.max_ext_atr`,
  `exit.profit_target_r`, `exit.giveback_pct`, `entry.rs_rating_min@trend_up`,
  `exit.time_stop_days`, `entry.min_volume_ratio`) — kart aileleriyle (52wh/volume-shock/…)
  kesişim YOK; kart ölçümleri hypotheses defterine yazmıyor.
- Sandbox beyanı (`oos_erosion.py:21-25`): araştırma/ön-eleme koşumları resmî aşınma sayacına
  yapısal olarak giremez → kart ölçümü + erosion çift-sayımı mekanik olarak kapalı.
- prescreen `k_probes` ↔ kuyruk `k_probes` ayrımı kodda beyanlı (`prescreen.py:507-509`
  "iki farklı sayaç tek alana yazılmaz").

Şerh: bu hüküm YEREL kopya üzerindendir; canlı defterde kart-aileli bir hipotez satırı
belirmişse görünmez (bayatlık beyanı yukarıda). Sınıf olarak beklenmez — hermes yalnız bounds
knob'ları önerir.

## 3. Temiz çıkanlar (denetimin lehte bulguları)

- EDG-2026-002'nin K+=5→6 düzeltmesi kartın İÇİNDE, tarihli ve gerekçeli (`:15`) — S1 önerisi
  (`s1_retro/RAPOR.md:199,257`) İŞLENMİŞ. (trial_ids bacağı hariç — o U2'de.)
- Çarpım kuralı taranan grid'lerde tutarlı uygulanmış: EDG-003 (2×2→4), EDG-009 (2×2→4;
  trial_ids A-D dört koşuyu tek tek sayıyor), EDG-017 (K+=2 "çarpımla"), KYS-001 (K+=2). Tek
  istisna U1 (EXE-001 yorum satırları).
- 08-01→08-03 dalgasında trial_ids geri-doldurma disiplini çalışmış (U2'deki karşı-örnek listesi).
- Kill/eşik alanlarında ölçüm-sonrası oynama İZİ YOK: "eşikler ölçümden ÖNCE donmuştu, DEĞİŞMEDİ"
  beyanı yeni kartlarda (EXE-004:74, EDG-022:55) açıkça taşınıyor.

## 4. Kod düzeltmesi hükmü — bu turda YAPILMADI, gerekçesi

M8 sözleşmesi "senkron mekanizması kodda basit bir boşluksa (ör. sayaç retro kartları saymıyor)
düzeltme serbest+testli" der. Denetim sonucu: **kartları sayan sayaç yok** (§0) — dolayısıyla
"retro kartı saymayan sayaç" diye düzeltilecek mekanik boşluk da yok. Kart K'sını koda bağlamak
(U6-b) yeni bir tüketici İCAT etmek ve DSR çıktısını değiştirmek olur = ölçüm-anlamı değişikliği →
rapor-önce kuralı gereği Rol-1'e. U7 de aynı sınıf (n_trials'ın kapsamı). U1-U5 kart/README
düzeltmeleridir ve kartlar bu tur DONUK.

## 5. Rol-1'e öneri listesi (bu tur YAZILMADI; hüküm + uygulama Rol-1'de)

1. **EXE-001 yorum aritmetiği** (U1): `:16-17` eksen yorumlarını çarpım diline çek
   ("3×2=6 → K+=6 (çarpım)" + R2 ile toplam 7); EDG-002 düzeltme-üslubu emsal.
2. **trial_ids geri-doldurma** (U2): EDG-001/002 için S1'in hazır önerilerini işle
   (`RAPOR.md:249,254`); EDG-003/004, EXE-002/004, EDG-022 (+ taze KYS-002) için koşu adlarını
   Rol-1 doğrulayıp yazsın (bu rapor dizin eşlemelerini ŞÜPHELİ bıraktı — uydurma id yazılmasın).
3. **README endeks tazeleme** (U3): aktif liste (8 bayat çıkar; gerçek-aktif EDG-019 + EXE-003
   girer, KYS-002'nin güncel durumu işlenir) + kart-adayı bölümünden KYS satırı + `:37`
   numara-notunun 019-yeniden-kullanımıyla uzlaştırılması.
4. **Retro kartsızlar kararı** (U4): EAP/Insider/Short-interest/PEAD için ya kart aç ya da README
   satırlarına "kartsız-kapanmış (kill-list kaynaklı; K yükü şu)" kalıcı beyanı düş; Çıkış-paketi
   ve Trend satırlarının EDG-003/009 ile ilişkisini (halef mi aynı mı) hükme bağla.
5. **Şema kararı** (U5): `k_registry`ye `harcanan_K` / `sayilmama_nedeni` gibi makine-okunur alan
   (trial_ids içine düzyazı gömme pratiği bitsin).
6. **n_trials kapsam beyanı** (U6/U7): `n_trials_beyan`a kart-kanalı ve arşiv-rotasyon
   alt-sınırlarını ekle YA DA sayımı genişlet — ikisi de ölçüm-anlamı kararı; hangisi seçilirse
   `validation_trio` docstring'indeki "ömür-boyu" ifadesi davranışla eşitlensin.

---

**Sayım özeti:** 29 kart tarandı (15 archived · 9 measured/measured_partial · 2 registered ·
2 askı · 1 karne; KYS-002 denetim sırasında registered→measured_partial geçti — denetim-anı
beyanı yukarıda). Uyuşmazlık: **7 başlık** (U1-U7) — 1 K-aritmetiği (1 birim eksik-sayım,
kanıtlı) · 8 kartta trial_ids geri-doldurma boşluğu (biri TAZE-şerhli) · README endeksi 8/8
bayat + 2 iç çelişki · 4 kartsız retro ölçüm + 2 ŞÜPHELİ eşleme · 1 şema boşluğu ·
2 yapısal/beyan boşluğu (U6, U7). Çift-sayım: bulunamadı. Kod düzeltmesi: yapılmadı (gerekçe §4).
