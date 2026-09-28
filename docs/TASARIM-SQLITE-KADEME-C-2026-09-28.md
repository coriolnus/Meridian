# TASARIM — SQLite Kademe C: `hypotheses.jsonl` + `validation_ledger.jsonl` → `meridian.db` (TSK-020 UYGULA-1)

Durum: **ONAYLI** — operatör 2026-09-28 07:2xZ (AskUserQuestion: tasarım 'Onaylıyorum'; canlı göç 'ilk sakin pencerede, Rol-1 yapar'). Sıra: ölçüm ✔ → bu belge ✔ → onay ✔ → kod. Yazan: Rol-1, 2026-09-28 07:0xZ.
Operatör kararı (2026-09-28, AskUserQuestion): "SQLite taşımasını sıraya al". Kaynak: `meridian/storage.py` docstring'i
ve ROADMAP TSK-020 kaydı — "Öğrenme-katmanı dosyaları (hypotheses/validation_ledger) Kademe C'ye ertelendi."
hafıza: A1 recall bu turda TSK-168 için koşuldu; Kademe C'ye özgü önceki karar kaydı yok (ROADMAP TSK-020 + TSK-128 notları okundu).

---

## 1. Ölçüm (2026-09-28, A1 salt-okur + yerel kod taraması)

| | `hypotheses.jsonl` | `validation_ledger.jsonl` |
|---|---|---|
| Canlı hacim | 60 satır · 128 KB · son yazım 2026-08-21 | 398 satır · 1,08 MB · son yazım 2026-08-21 |
| Anahtar evreni | 25 anahtar; 15'i her satırda, 10'u seyrek (`backtest` 35, `reject_reasons` 58, diğerleri 1–2) | 32 anahtar; 21'i her satırda, 11'i sonradan doğan (PARA-v3 341, `pencere_id` 194, `dd_mtm_*` 29) |
| Tip karışımı | `old`/`new`: float + int + None karışık | `oos_score`, `sharpe_gozlem`, `dsr` …: float + None |
| İç içe alanlar | `reject_reasons` (liste), `backtest`/`realized_detail`/`vs_benchmark_at_ship` (sözlük) | `degisen_params`, `oos_ozet`, `oos_components` (sözlük), `seri` (liste) |
| Yazan | `meridian/memory.py::record` (ekleme, `meridian-learn`), `meridian/memory.py::update_status` + `meridian/memory.py::writeback_outcome` (tam yeniden yazım, `meridian.service`) | `meridian/validation.py::record_candidate` (ekleme, `meridian-learn`) — tek yazar |
| Okuyan | memory, probgate, analytics, selfreview, shadowlaw, recompute, watchdog, api — hepsi `store.read_jsonl` üzerinden (tam okuma) | `meridian/validation.py::ledger` (son 200), analytics (son 200), shadowlaw (tam) |
| `meridian.db` (A1) | `schema_version`=1; altı varlığın ALTISI da `entity_meta.migrated_at` + `source_digest` DOLU | |

Notlar: `ret_seri`/`ret_n` (TSK-077, 2026-09-03) canlı defterde henüz YOK — öğrenme 08-21'den beri yazmıyor (TSK-204).
Test yüzeyi: `hypotheses.jsonl` 24, `validation_ledger.jsonl` 3 test dosyasında adıyla geçiyor; `tests/test_bayat_defter_kalintisi_v234.py`
ve `tests/test_deger_esitligi_deseni_v239.py` listeyi `storage.ENTITIES`ten türettiği için yeni varlıkları kendiliğinden kapsar.

## 2. Emsal: Kademe A+B örüntüsü (değişmeden devralınır)

Varlık kaydı (`ENTITIES`/`_TABLE`/`_KIND`/`_COLS` + `extra_json` kaçış alanı) · WAL + `busy_timeout` · `meridian/store.py::db_backed`
şeffaf yönlendirme (uygulama kodu değişmez) · `meridian/dbmigrate.py::apply` tek transaction + parite digesti + hatada karantina ·
kaynak dosya silinmez, `.migrated` olur · `--geri-al` · çevrimiçi yedek (`storage.backup_to`) · Litestream yalnız DB'yi replike eder.
`dbmigrate.apply` zaten ARTIMLIDIR: `migrated_at` dolu varlıkları `zaten_tasindi` diye atlar — altı eski varlık ikinci koşuda dokunulmaz kalır.

## 3. Ölçümle bulunan riskler — tasarımın asıl işi bunlar

**R1 — Sessiz boş okuma penceresi (ENGEL sınıfı).** `meridian/storage.py::active` varlık bazında DEĞİL, veritabanı bazında karar
verir: DB dosyası + şema varsa `_TABLE`'daki HER ad için True döner. A1'de DB var. İki ad `_TABLE`'a eklenip kod dağıtıldığı an, veri
henüz taşınmadan okumalar DB'ye gider: tablo yoksa istisna, tablo `CREATE IF NOT EXISTS` ile doğmuşsa BOŞ defter — öğrenme geçmişi
"yok" görünür (Kademe A+B'de bu pencere yoktu, çünkü altısı DB ile aynı koşuda doğdu).

**R2 — Süreçler-arası kayıp güncelleme (taşımanın kendisi KAPATMAZ).** `memory.update_status`/`writeback_outcome` defterin tamamını
okur, değiştirir, tamamını yeniden yazar; okuma yalnız süreç-içi `_HYP_LOCK` altındadır, dosya kilidi yalnız yazımı kapsar. Aynı anda
öğrenme süreci `memory.record` ile kilitsiz ekleme yapar. Okuma ile yazma arasına düşen ekleme, yeniden yazımda SİLİNİR. SQLite'a
taşımak bunu tek başına çözmez: `replace_rows` "hepsini sil + yaz" yapar ve okuma yine transaction dışında kalır. Bugün sessiz
(öğrenme 08-21'den beri kapalı), TSK-204 öğrenmeyi yeniden açınca canlanır.

**R3 — Kum havuzları geçmişi sessizce kaybeder.** Sprint ve ön-eleme kum havuzları `meridian.db`'yi BİLEREK kopyalamaz (izolasyon —
`meridian/sprint.py` SKIP_COPY şerhi) ve dosyayla çalışır. Göçten sonra canlıdaki dosya `.migrated` adını alır; kum havuzunda
`validation_ledger.jsonl` bulunmaz → kapının DSR deneme örneklemi (`validation.ledger`, son 200) boş başlar, PBO tabanı sıfırlanır.
`hypotheses.jsonl` için sprint zaten sıfırlıyor (`meridian/sprint.py::_reset_sandbox_state`), ama ön-eleme kum havuzu sıfırlamıyor —
aylık kabul kotası ve kimlik sayacı (`next_id`) orada da boş deftere göre hesaplanır. Sonuç: kum havuzu kapısı canlıdan farklı karar verir, uyarı yok.

**R4 — Ham okuyucular.** Motor içinde tek ham yol `meridian/api.py::api_state_snapshot` — `.migrated` arşivini ve DB yedeğini zaten
ekliyor (sorun yok). Dışarıda: `deploy/oracle-a1/RUNBOOK.md` operatöre `grep -c … state/validation_ledger.jsonl` önerir → göçten sonra
sessizce 0 der. `research/olcumler/*` betikleri donmuş kopyalar okur (canlıya dokunmaz, etkilenmez).

## 4. Tasarım

**D1 — Varlık kaydı.** İki ad `ENTITIES`'e "rows" türüyle eklenir. Kolonlar §1'deki ÖLÇÜLMÜŞ evrenden: her satırda bulunan skaler
alanlar tipli kolon; iç içe alanlar, seyrek alanlar ve tipi karışık alanlar (`old`/`new` — int/float/None) `extra_json`'a düşer
(Kademe A+B'nin `-0.0`/afinite dersi: tip kaybı parite digestini bozar, kaçış alanı kazanır). Tablo adları `hypotheses`,
`validation_ledger`. `SCHEMA_VERSION` 1→2 (yeni tablolar `CREATE IF NOT EXISTS`, eski altı tabloya dokunulmaz).

**D2 — Varlık bazında açılış kapısı (R1'in çözümü).** `active(name)` bir varlık için ancak DB'de o varlığın `entity_meta.migrated_at`
damgası DOLUYSA True döner. A1 ölçümü: altı eski varlığın altısında damga dolu → davranışları değişmez. Taze kurulum (DB yok) ve
`MERIDIAN_DB=off` yolları bugünkü gibi dosyaya düşer. Sonuç: kod dağıtıldığı an iki defter DOSYADAN okunmaya devam eder; ancak
`dbmigrate --uygula` parite kanıtıyla damgayı bastığı AN DB'ye geçer — geçiş tek transaction'ın COMMIT'idir, arada boş okuma anı yoktur.
Bedel: her okumada bir `entity_meta` sorgusu → süreç-içi önbellek (mevcut `_SCHEMA_OK` deseni), damga dolunca bir daha sorulmaz.

**D3 — Atomik oku-değiştir-yaz (R2'nin çözümü).** Yeni bir `update_rows(name, fn)` yardımcısı: DB yolunda `BEGIN IMMEDIATE` → oku →
`fn(satırlar)` → yaz → `COMMIT` (başka süreçlerin eklemesi transaction'ı bekler, kaybolmaz); dosya yolunda okuma+yazmayı birlikte
kapsayan dosya kilidi altında yapar. Eklemenin kilitsiz O_APPEND kararı (`tests/test_wph_store_kapi.py` gerekçesi) DEĞİŞMEZ — yani
dosya yolunda yarış yalnız DB'siz kiplerde (kum havuzu tek süreçtir; `MERIDIAN_DB=off` acil kipi) kalır ve bu beyanla kabul edilir. `memory.update_status` ve
`memory.writeback_outcome` bu yardımcıya geçer; iş mantıkları (geçiş yasası, terminal kilit) aynen `fn`'in içine taşınır.
Çivi: iki süreç (ya da iki bağlantı) arasında "okundu → araya ekleme → yazıldı" senaryosu → eklenen satır yaşamalı.

**D4 — Kum havuzu maddeleştirmesi (R3'ün çözümü).** Kum havuzu kurulurken DB'li her varlık için, kaynak `.migrated` olarak duruyorsa,
canlı DB'nin O ANKİ içeriği `storage.read_rows` ile (tutarlı okuma) kum havuzuna kanonik dosya adıyla yazılır; sonra sprint'in
kendi sıfırlaması bugünkü gibi üstüne yazar. Böylece kum havuzu bugünkü girdiyi görür (validation geçmişi dahil) ve DB kopyalanmaz
(izolasyon korunur). Çivi: göç edilmiş DB'li sahte canlı → kum havuzundaki `validation_ledger.jsonl` satır sayısı = DB satır sayısı.
Açık soru (ölçülecek, bu kalemin kapsamı DIŞI): Kademe A+B'nin `trade_plans`/`equity_curve`/`shadow_books` varlıkları kum havuzunda
bugün boş mu başlıyor ve bu bilinçli mi — D4 onları da maddeleştirirse sprint davranışı değişir; bu yüzden D4 yalnız iki yeni varlığa
uygulanır, eski altısı için ayrı ölçüm kalemi açılır.

**D5 — Sözleşme ve belge borcu.** `meridian/ledgers.py` CONTRACTS notu ("dosya sınırsız büyür") DB gerçeğine güncellenir (TSK-128
kırpması DB'de sorgu olur, kalem GATED kalır). `deploy/oracle-a1/RUNBOOK.md` grep satırı DB sorgusuyla değişir. `storage`/`dbmigrate`
şerhlerindeki "altı varlık" sayıları `len(ENTITIES)`'ten türeyen ifadeye çevrilir (tek-kaynak yasası).

**D6 — Geçiş reçetesi (canlı).** (1) Kod dağıtımı — D2 sayesinde iki defter DOSYADAN okunmaya devam eder, davranış değişmez.
(2) Sakin pencerede (piyasa kapalı, öğrenme kapalı zaten): worker + learn durdur → `dbmigrate` kuru koşum oku (iki varlık `tasinacak`,
altısı `zaten_tasindi`) → `--uygula` → parite satırları `tasindi` + `ok` → servisleri başlat. (3) Doğrula: `store.db_backed` iki ad için
True, `_n_jsonl` 60/398, pano öğrenme şeridi aynı sayıları gösteriyor, `.migrated` dosyaları yerinde. Geri alma: `dbmigrate --geri-al`.

## 5. Testler (uygulayıcı brief'ine girer)

D2 kapısı (damgasız varlık dosyadan okunur · damga basılınca DB'den · eski altısı etkilenmez · `MERIDIAN_DB=off`) · D3 yarış çivisi
(iki bağlantı) · D4 kum havuzu satır sayısı · parite digesti ölçülmüş tip karışımıyla (int/float/None `old`/`new`, iç içe sözlükler) ·
`dbmigrate` artımlı koşu (altı `zaten_tasindi` + iki `tasindi`) · kapsam: v57 · v129 · v130 · v182 · v234 · v239 · v62 · v76 · v555 ·
sprint/ön-eleme kum havuzu testleri · `hypotheses.jsonl` adını taşıyan 24 dosya. Motor değişikliği → Rol-1 tam suite + KILL#1.

## 6. Bedel yasası — ne kaybediyoruz

(a) İki defter artık `cat`/`grep` ile okunamaz; operatör okuması DB sorgusu ya da pano üzerinden olur (RUNBOOK güncellemesi bunu karşılar).
(b) `.migrated` dosyaları göç anında donar — sonrasında insan onları okursa bayat görür (Kademe A+B'deki bayat-defter süzgeci bu sınıfı
yönetir). (c) D2 her okumaya bir kez damga sorgusu ekler (önbellekli). (d) Litestream/yedek kapsamı iki defteri KAZANIR (bugün yalnız gece tar'ı var).

## 7. Operatöre sorulacaklar

1. Tasarım onayı (D1–D6).
2. Zamanlama: R2 bugün sessiz (öğrenme kapalı). Taşıma TSK-204 öğrenmeyi yeniden açmadan ÖNCE bitmeli — öneri: kod bu hafta, canlı
   göç (D6-2) ilk sakin pencerede (piyasa kapanışından sonra).
