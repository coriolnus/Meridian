# RAPOR — 25c DİRİLTME ADAYLARI DEĞERLENDİRMESİ (2026-08-23)

**Kapsam:** Envanterin (`docs/DENETIM-OLU-BILESEN-ENVANTERI-2026-08-13.md` §D-3) dört diriltme
adayından **kalan üçü**. Dördüncüsü (`no_trade_before_bars`) bu listede DEĞİL: Rol-1 ölçümü
(2026-08-13) envanterin DİRİLT hükmünü AŞTI — doğru muamele DAMGALA çıktı ve K5 turunda
uygulandı (goal.yaml yorumu düzeltildi, `guard.LIMIT_KEYS` → `guard.REPLAY_WARMUP_KEYS`).

**Bu rapor HÜKÜM VERMEZ.** Her aday için bugünkü (2026-08-23) kod gerçeği + üç seçeneğin
(DİRİLT / DAMGALA / KALDIR) artı-eksisi yazılıdır; hüküm operatöründür.

**Ölçüm şerhi (uydurma yasağı):** bu değerlendirme worktree'den yazıldı — `state/` boş (yalnız
git-izli goal/bounds var). Canlı sayılar (E2 satır sayısı, params_by_regime canlı içeriği,
hipotez defteri) **buradan ölçülemedi**; canlıya dair her sayı envanterin 2026-08-13 ölçümüdür
ve öyle etiketlenmiştir. Hüküm öncesi tazelenmesi gereken sayılar her adayın altında listeli.

---

## Aday 1 — `params_by_regime` (4 harita; envanter gününde 4'ü de BOŞ)

**Envanter hükmü (2026-08-13):** "Rejim-koşullu ayar makinesi tam kablolu ve hiç kullanılmıyor
— ya rejim-örneklem birikimi iş kalemi olur, ya haritalar kaldırılıp `resolve_params` sadeleşir."

**Bugünkü kod gerçeği (envanterden beri DEĞİŞTİ — iki büyük gelişme):**
- **Yakıt hattı KURULDU:** envanter "mekanizma canlı, yakıt yok" diyordu. 2026-08-14'ten beri
  arka plan yansıması (C16) canlı-DIŞI rejimin birikmiş kanıtıyla koşuyor ve **D2 çivilemesi**
  (EDG-2026-041; `hermes._reflect_once_govde`) `@`siz önerileri `var@{sertifikalı rejim}`e
  yeniden yazıyor; rejim-zorlamalı arama her sondayı `var@{rejim}` yapıyor. Ship gerçekleşirse
  `versioning.bump` doğrudan `params_by_regime[rejim]`e yazar. Yani haritalar artık ÜRETİM
  hattının hedef yüzeyi — atıl bir cep değil.
- **`@chop` dilimi BİLEREK KAPALI:** EDG-2026-048 NO-GO (2026-08-23) ile `@chop` üretimi
  duraklatıldı (K1; `config.URETIMI_DURAKLATILAN_REJIMLER`). `params_by_regime["chop"]`ın boş
  kalması artık bir kuraklık belirtisi değil, ÖLÇÜLMÜŞ POLİTİKA.
- Değişmeyen: `config.resolve_params` (config.py) boş haritada kimlik fonksiyonu; probgate
  ship kapısı (c-3 ezilme zinciri) hâlâ hiçbir ship geçirmedi — haritaların DOLU olduğu bir
  gün henüz yaşanmadı (envanter ölçümü: 52 öneri, 0 ship).

**Seçenekler:**

| seçenek | artı | eksi |
|---|---|---|
| **DİRİLT** (bugünkü yörünge: bg turları + D2 beslemeye devam; ayrıca rejim-dilimli örneklem birikimini izleyen bir pano kalemi) | Kablo UÇTAN UCA hazır ve v247 testli; boşta duran canlı-dışı kanıt israf edilmiyor; ilk rejim-ship'i kendiliğinden buraya düşecek | "Diriltme"nin gerçekleşmesi probgate'i geçen İLK ship'e bağlı — c-3 ezilmesi sürerse haritalar sonsuza dek boş kalır ve kalem sahte-açık durur |
| **DAMGALA** (haritalara/panoya "bugüne dek 0 ship — boş olması ölçüm, chop'unki politika" beyanı) | Dürüst; sıfır risk; @chop duraklatmasıyla tutarlı | Damga hızla bayatlar: ilk bg-ship haritayı doldurduğu gün beyan yanlışlanır (bayat-beyan sınıfı, §4-49 dersi) |
| **KALDIR** (haritaları sil, `resolve_params`ı sadeleştir) | Yüzey küçülür | 2026-08-14'te ÖLÇÜMLE kurulan D2/C16 makinesinin hedef yüzeyini söker — daha iki hafta önce bilinçli yatırım yapılan mekanizmayı geri almak olur; `REGIME_EXIT_KEYS`/`@regime` doğrulama zinciri (guard) anlamsızlaşır; geri dönüşü pahalı |

**Hüküm öncesi tazelenecek canlı sayı:** `state/history/` son sürümlerde `params_by_regime`
içeriği + bg turlarının ship/ret sayımı (`hermes_bg_proposal_*` olayları, 08-14 sonrası).

---

## Aday 2 — `pessimistic_band_v2.ampirik_*` (`ampirik_bps` / `ampirik_n` / `ampirik_guncelleme`)

**Envanter hükmü (2026-08-13):** "E2 defteri 10 satır; kalibratör yazılı ve bekliyor. DOĞRU
şekilde boş — ama akışı besleyen kalem yok. E2 satır debisini artıran bir kalem gerekir."

**Bugünkü kod gerçeği:**
- Kalibratör YAŞIYOR ve BAĞLI: `analytics.pessimistic_band_update` (analytics.py:4159) E2
  defterinden (`entry_execution.jsonl`, `fill` dolu satırlar) ölçüyor; `api.py:4356`
  (`kotumser_band`) pano yüzeyine taşıyor. Alanlar None doğar, ölçüm birikince dolar —
  goal.yaml E3 blok beyanı aynen geçerli ("varsayılan sayı yazmak, ölçülmemişi ölçülmüş
  göstermek olurdu").
- E2 debisi dolum sayısına bağlı; dolum sayısı stratejinin işlem debisine. Slot20+0,5R paketi
  (2026-08-12) işlem debisini yapısal olarak artırdı (EDG-026: 772 vs 410 işlem/koşum) —
  E2'nin kendiliğinden dolma hızı envanter gününe göre muhtemelen yükseldi (canlı satır sayısı
  buradan ölçülemedi — tazelenecek).

**Seçenekler:**

| seçenek | artı | eksi |
|---|---|---|
| **DİRİLT** (E2 debisini İZLEYEN bir eşik kalemi: örn. "n≥30 dolum olduğunda kalibratör hükmü panoda ana sütun olur") | Bandın literatür tahmini (20 bps) ilk kez ÖLÇÜMLE sınanır; karne paydası gerçeğe oturur | Debi zorla artırılamaz — "dolum üret" diye işlem açmak ölçüm uğruna strateji bozmak olur; kalem uzun süre BEKLEMEDE görünür |
| **DAMGALA** (mevcut hâli beyanla: "doğru şekilde boş — kalibratör canlı, eşik n'e bağlı") | Sıfır maliyet; goal.yaml + analytics zaten bu beyanı taşıyor (yarım damga fiilen var) | Hiçbir şeyi hızlandırmaz; `null` alanlar panoda süresiz durur (operatör gözünde "bitmemiş iş" görüntüsü) |
| **KALDIR** (ampirik_* alanlarını sök) | Üç satır azalır | ÇALIŞAN ve doğru-boş bir ölçüm mekanizmasının çıktı yuvasını söker; kalibratör yazacak yer bulamaz → E3'ün "ampirik üstündür" tasarımı ölür; uydurma yasağının örnek uygulamasını (dürüst None) yok eder |

**Hüküm öncesi tazelenecek canlı sayı:** canlı `state/entry_execution.jsonl` satır sayısı +
`fill` dolu satır sayısı (kalibratörün kendi `n`i; `/api/...` kotumser_band çıktısı yeterli).

---

## Aday 3 — Skill `shadow` bayrağı ↔ `strategy.ARMED_SETUPS`

**Envanter hükmü (2026-08-13):** "Registry 'gölge' diyor, motor silahlı koşuyor
(pullback-screener vakası). Ya bayrak ARMED_SETUPS'a bağlanır, ya bayrak damgalanır —
ikisinden biri şart."

**Bugünkü kod gerçeği (envanterden beri DEĞİŞTİ):**
- **Canlı vaka ÇÖZÜLDÜ ama yapısal boşluk DURUYOR:** envanterin örneği `pullback` idi;
  2026-08-22'de OPERATÖR KARARIYLA (B1; kart EDG-2026-039, kanıt asimetrisi) `pullback`
  ARMED_SETUPS'tan çıkarıldı (strategy.py — bugün üçlü: breakout_vcp, exhaustion_hammer,
  momentum_burst). Yani o çelişki bayrak yoluyla değil, TUPLE düzenlemesiyle kapandı — tam da
  "gerçek düğme tuple'dır" bulgusunu doğrulayan yoldan.
- Motor registry'yi hâlâ HİÇ okumuyor (`strategy.py`de `skills` geçen üretim satırı yok);
  `skills.py`nin kendi beyanı da bu ("KARAR ÇEKİRDEĞİ KAYIT DEFTERİNİ ZATEN OKUMUYOR",
  skills.py:71-75 civarı). Bu turda ezen tarafa 25d c-5 damgası kondu (ARMED_SETUPS satırı).
- Bayrak tarafının damga işi (pano rozeti "LLM-YÜZEYİ — trading davranışını değiştirmez")
  ROADMAP kararıyla **WP7'de yaşıyor** (25b satırı oraya taşındı, C10) — bu adayın "damgala"
  kolu kısmen başka bir iş paketinin sahasında.

**Seçenekler:**

| seçenek | artı | eksi |
|---|---|---|
| **DİRİLT** (`scan_all`/`scan_entry` motor-içi skiller için registry `shadow`ını okusun) | Tek gerçek kalır; operatörün panodaki "gölgele" düğmesi gerçek olur; auto_shadow kanıt eşiği (skills.py) davranışa bağlanır | Deterministik motorun girdi yüzeyine KİLİTSİZ, LLM-elinin değdiği bir JSON girer (guard saflık yasasının ruhuna aykırı; yırtık-okuma riski recommend.py'de bile beyanlı); silahlanma yetkisi iki yüzeye bölünür (tuple + bayrak) ve sessiz-ayrışma sınıfı geri gelir; kart-önce ölçüm ister (strateji-kimliği değişikliği) |
| **DAMGALA** (WP7 rozeti + bu turda konan c-5 EZER damgası; tuple tek yetkili beyan edilir) | Ucuz, dürüst, bugünkü fiilî düzenin adı konur; pullback vakasının çözüm yolu (operatör kararı + tuple + kart) zaten bu modeli doğruladı | İki-gerçek yüzeyi kalıcılaşır: registry'de `shadow:true` yazan motor-içi bir skill yine silahlı koşabilir — operatör rozeti okumazsa aynı tuzak tekrarlanır (auto_shadow'un "motor_ici_esik_asan" kovası bunu raporlar ama durduramaz) |
| **KALDIR** (motor-içi skiller için registry `enabled`/`mode`/`shadow` yazımını kes) | YASA 6 sertliği (okuyucusuz-etki alanı kalmaz); yanıltıcı düğme yüzeyi tamamen kalkar | Bayraklar LLM istem/pano yüzeyinde OKUNUYOR (hermes symlink/ön-yükleme + katalog) — "okuyucusuz" değiller, yalnız KARAR-yolunda ölü; kaldırmak auto_shadow kanıt kayıtlarını ve Axis-2 tavsiye zincirini kırar; envanter bile bunu KALDIR değil DAMGALA sınıfına koymuştu |

**Hüküm öncesi tazelenecek canlı sayı:** canlı registry'de motor-içi (`ENGINE_IMPLEMENTED` ∩
ARMED_SETUPS-eşlemeli) skill'lerden `shadow:true`/`enabled:false` yazılı olan var mı
(pullback-screener kaydının bugünkü hâli dahil) — varsa DAMGALA kolunun "aynı tuzak" eksisi
hâlâ canlı bir vakadır, yoksa teorik risktir.

---

## Özet tablo (hüküm operatöre)

| aday | envanter hükmü | bugünkü gerçek | en ucuz dürüst yol | en kalıcı yol |
|---|---|---|---|---|
| params_by_regime | dirilt-ya-kaldır | yakıt hattı KURULDU (D2/C16); chop politikayla kapalı | DAMGALA (bayatlama riskli) | DİRİLT (yörünge zaten bu) |
| ampirik_* | debi kalemi | kalibratör bağlı, debi slot20'yle arttı (ölçülmedi) | DAMGALA (fiilen yarı-damgalı) | DİRİLT (eşik kalemiyle) |
| shadow↔ARMED | bağla-ya-damgala | canlı vaka tuple yoluyla çözüldü; yapısal boşluk sürüyor | DAMGALA (WP7 rozeti + c-5) | DİRİLT (kart-önce, saflık bedeli büyük) |
