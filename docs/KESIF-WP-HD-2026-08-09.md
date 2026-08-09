# KEŞİF TURU — WP-H (Mühendislik Dayanıklılığı) + WP-D (Veri Bütünlüğü) — 2026-08-09

**Yazan:** keşif ajanı (SALT ÖLÇÜM + PLAN turu).
**Okuyucu (YASA 6):** Rol-1 (dalga önceliklendirmesi) + bir sonraki mühendis.
**Girdi:** `MERIDIAN_ENGINEERING_LOG.md` (fotoğraf, 2026-08-03 tepesi) + `ROADMAP.md` §WP-H(552)/
WP-D(512)/WP-S2(251)/WP-S(182) + `docs/SABAH-TRIYAJI-2026-08-09.md` + kod (koda karşı doğrulandı) +
A1 canlı salt-okuma (2026-08-09 ~14:2x UTC).

**Sınır beyanı:** git komutu KOŞULMADI (stash/diff/status/log dâhil); dağıtım YAPILMADI; `serve.sh`
KOŞULMADI; broker'a emir YOK; tam suite KOŞULMADI; `meridian/` ve `tests/` altında HİÇBİR dosyaya
DOKUNULMADI. A1'e yalnız salt-okur `systemctl show`/`journalctl`/`stat`/`grep` çalıştırıldı.
Depoda yazılan **TEK** dosya budur. UYDURMA YASAĞI: her iddia dosya:satır ya da canlı-çıktı kanıtlı;
ölçülemeyen "ölçülemedi" diye adlandırıldı.

---

## 0. YÖNETİCİ ÖZETİ (üç cümle)

1. **WP-H çekirdeği büyük oranda KAPALI** — H9 (SQLite defter + atomik/flock kapısı) ve H10 (PRAGMA
   gömülü + Litestream aşama-1 canlı) sahada; kalan otonom iş **tek bir sınıf:** H9 Kademe-B'nin
   bilerek ertelediği **~11 kapı-dışı yazımın `store.write_text`/kilitli-append'e taşınması** (kapı
   HAZIR: `store.py:306 write_text`).
2. **EN YÜKSEK OPERASYON ÖNCELİĞİ operatör-kapılı:** systemd `SuccessExitStatus=143` düzeltmesi
   birim dosyasında YAZILI (`deploy/oracle-a1/meridian.service:82`) ama CANLIYA İNMEDİ — A1'in
   `/etc` birimi 08-02 tarihli, canlı `SuccessExitStatus=` BOŞ ve **her restart exit-143 ile
   "FAILED" sayılıyor** (son 3 günde 6 kez, kanıt aşağıda). N1 bildirim kanalı bundan ÖNCE açılırsa
   her restart yanlış "FAILED" alarmı gönderir.
3. **WP-D'de otonom kod deliği KALMADI gibi** — `bars_integrity` sevk + kablolu, seans-içi boşluk
   dedektörü (`scheduler._intraday_gap_check`) kurulu; açık kalan iki kalem OPERATÖR/veri-kaynağı
   bloklu (`dataset.load↔bars_integrity` bağlama kararı + FMP planı) veya türetilmiş-artefakt
   yeniden-üretimi (o karara bağlı).

---

## (i) H9 / H10 / WP-D AÇIK İŞ

### H9 — Depolama atomiklik + kilit (Kademe A ✅ · Kademe B ÇEKİRDEK ✅ · çağrı-noktaları AÇIK)

**Sahada olan (koddan doğrulandı):**
- Merkezî atomik yazım: `store.py:242 _atomic_write` = `mkstemp → write → fsync → os.replace →
  dizin-fsync`. B1 sıfır-baytlık-dosya sınıfı kapalı.
- Süreçler-arası kilit: `store.py:138 file_lock` = süreç-içi RLock **+** `fcntl.flock`
  (`store.py:167`, `state/.locks/<ad>.lock`). B2 "süreç-içi kilit" tehlike sınıfı kapalı.
- Kapılı yollar: `write_json` (`store.py:292`), `write_jsonl` (`store.py:420`), `write_text`
  (`store.py:306`) — üçü de `file_lock` + `_atomic_write` alır. `db_backed` dalında flock YOK
  (bilerek: SQLite kendi kilidini alır, çift-kilit sırası riski).

**AÇIK — H9'un kendi bıraktığı kuyruk (log satır 599-604; koda karşı YENİDEN doğrulandı 2026-08-09):**
Bu, WP-H'nin tek adlı otonom açık kalemidir. `store.py:306-320` docstring'i kendi envanterini tutar;
kod bugün hâlâ şöyle:

| # | Yol | Kanıt (dosya:satır) | Kusur sınıfı | Kapı-dışı mı? |
|---|---|---|---|---|
| 1 | `memory.py` lessons.md | `memory.py:212` `(config.STATE/LESSONS).write_text(text)` | ATOMİK-DEĞİL (düz write_text KIRPAR → okuyucu yarım/BOŞ görür → sessiz "ders yok") | EVET (store import var, write_text KULLANMIYOR) |
| 2 | `run.py` scoreboard arşivi | `run.py:172` `(config.HISTORY/f"scoreboard-{stamp}.json").write_text(...)` | ATOMİK-DEĞİL (aynı kırpma sınıfı) | EVET (store import bile yok) |
| 3 | `skill_evolve.py` taslak | `skill_evolve.py:170` `open(draft_path,"w")` → `os.replace` (232-233) | düz open-w taslak; sonra atomik replace | EVET |
| 4 | `hermes.py` env + agent-config | `hermes.py:2339-2342` (env), `2470-2473` (AGENT_CONFIG) | `mkstemp+os.replace` var ama **fsync YOK, flock YOK** | EVET |
| 5 | `auth._write` | `auth.py:87-96` `tmp = path.with_suffix(".json.tmp")` (SABİT tmp adı) → `os.replace` | **fsync YOK, flock YOK, SABİT TMP ADI** → iki süreç aynı `.json.tmp`'ye yazar, atomiklik iddiası biter | EVET (EN TEHLİKELİ tekil) |
| 6 | `config.dump_yaml` | `config.py:306-317` `mkstemp+os.replace` | fsync YOK, flock YOK (strategy.yaml SICAK-yeniden-yüklenir, eşzamanlı okunur) | EVET |
| 7 | `earnings.py` ×2 | `earnings.py:392-397`, `475-480` `mkstemp+os.replace` | fsync YOK, flock YOK | EVET |
| 8 | `adapters/data._write_bars` | `data.py:135-139` `mkstemp+os.replace` | fsync YOK, flock YOK | EVET |
| 9 | `sprint_run._write_live_status` | log 315 (sprint durum yazımı) | fsync YOK, flock YOK | EVET |
| 10 | `store.append_jsonl` düz-append | `store.py:365-376` `open(path,"a")` — kilit YOK, atomik değil | append-only doğru biçim; ama **oku-değiştir-yaz** çağrı-noktaları kilidi ÇAĞIRAN'dan bekler | KAPI-İÇİ ama kilitsiz |

**POZİTİF BULGU (H9-komşusu, bu turda koddan doğrulandı):** SABAH TRİYAJI'nın "Kalem 8" (E2 defteri
kilitsiz oku-değiştir-yaz) **düzeltilmiş görünüyor.** `loop.py` (mtime 2026-08-09T16:47) artık
ENTRY_LEDGER oku-değiştir-yaz'ı `store.file_lock(ENTRY_LEDGER)` altında sarıyor:
`loop.py:52-59` (append), `93-101` (tavan budaması read→write), `1920-1925` (yanıltıcı "atomik"
yorumu düzeltilmiş) — hepsi "KİLİT (KALEM 8, 2026-08-09)" yorumlu. Yani triyajın (08:55 UTC) açık
saydığı bu kalem, sonraki bir çalışmayla kod düzeyinde kapanmış. **NOT:** commit durumu git
kısıtı gereği DOĞRULANMADI; yalnız çalışma-ağacı içeriği ölçüldü.

**Kademe C (ertelenmiş, log 628):** öğrenme-katmanı dosyaları (hypotheses/validation_ledger).
Yukarıdaki #3 (skill_evolve) ve #4 (hermes) bu aileye komşu → dosya-ayrıklık gereği bu iki dosya
canlı öğrenme-katmanı turlarıyla ÇAKIŞIR; ayrı brief'te ya da o turlarla koordine.

### H10 — Litestream / PRAGMA / DuckLake

| Bileşen | Durum | Kanıt |
|---|---|---|
| PRAGMA seti (WAL + synchronous=NORMAL + busy_timeout + foreign_keys) | ✅ GÖMÜLÜ | `storage.py:137 PRAGMAS`, `:173` bağlantıda uygulanır, `:180` canlı-ölçüm yüzeyi |
| Litestream v0.5 aşama-1 (file-replica, aynı-disk) | ✅ CANLI | `litestream.yml:96/120` (kaynak `/opt/meridian/state/meridian.db` → replica `/home/ubuntu/replica/meridian.db`); birim aktif (triyaj EK §Birimler); log 431-435 kurulum kanıtı (snapshot + "replica sync" txid) |
| Litestream aşama-2 (OCI Object Storage S3-uyumlu bucket, off-box PITR) | 🔒 **OPERATÖR-BLOK** | `litestream.yml:26` "MEDYA + BÖLGE koruması AŞAMA-2'dir (OCI Object Storage S3-uyumlu bucket; anahtar OPERATÖRDE)"; §6 kalemi |
| DuckDB (opsiyonel okuma aracı, sıfır-risk ATTACH) | opsiyonel/ölçüm-tarafı | log 633 |
| DuckLake | 🚫 RED-ŞİMDİLİK | log 634 (251-sembol EOD'de katalog katmanı gereksiz) |

**HÜKÜM: H10'da otonom kod işi KALMADI.** PRAGMA gömülü, aşama-1 canlı; kalan tek şey aşama-2 =
saf operatör-blok (OCI bucket + anahtar). "Meridian'da SQLite YOK" el-kitabı varsayımı ZATEN
çürütülmüş (log 612 REDDEDİLDİ notu tarihçedir; H9 SQLite-backed defter geldi).

### WP-D — Veri Bütünlüğü

| Kalem | Durum | Kanıt / açık ne |
|---|---|---|
| BULGU-1 (karantina hayalet-seans) | ✅ TEYİT-TAM | log 513-517; 4/4 vaka karantinada, yeni kaçak %0 |
| `bars_integrity` defteri + kanonik tüketiciler | ✅ SEVK + KABLOLU | `data.py:404 INTEGRITY_FILE`, `:538 bars_integrity()`, `:572 integrity_exclude` (fail-open, `:539`); tüketiciler component_ic/cf_backfill/trend_shadow (log 519-520) |
| `dataset.load ↔ bars_integrity` bağlama | 🔒 **OPERATÖR** | `dataset.py:163 load()` yalnız INDEX serisi HARD-kapısını uygular (`:166 IndexUnavailable`); güvensiz-dönem DIŞLAMASINI (`integrity_exclude`) ÇAĞIRMIYOR → walk-forward/prescreen/reflect kirli dönemi hâlâ görüyor (log 521). Bağlamak SİSTEMİN NE ÖLÇTÜĞÜNÜ değiştirir → operatör kararı |
| Türetilmiş artefakt yeniden-üretimi (component_ic/cf/eşik eğrileri) güvensiz-dönem-dışlamalı | 📋 OTONOM-ama-KARARA-BAĞLI | ROADMAP 523-524; hesaplama otonom, ama SEMANTİĞİ yukarıdaki karara bağlı (kanonik tüketiciler zaten dışlıyor; dataset.load bağlanırsa kapsam genişler) |
| Seans-içi kesinti/boşluk tespiti (5.3) | ✅ KURULU (davranışsal kanıt bekliyor) | `scheduler.py:746 _intraday_gap_check` (takvim_yok/seans_disi/arsiv_yok dalları `:761`; `intraday_gap_detected` uyarısı `:789`; hata yolu `:824` "ÖLÇÜLMEDİ" beyanlı); takvim_yok zinciri v175'te kapandı (log 184-192). Kalan: gerçek boşlukta ilk davranışsal atış |
| earnings kapsaması 194/251 + fail-open daraltma | 🔒 kısmen VERİ-KAYNAĞI-BLOK | `earnings.py:213 refresh`, `:180 refresh_window`, fail-open yasası (`:242`), takvim-marjı 9 gün (`:164`, v147 çivili). Kapsama boşluğu FMP 402'den (SABAH TRİYAJI Kalem 7); FMP planı = operatör |
| BMO/AMC ileri-birikim | DÜŞÜK öncelik | ROADMAP 525 (EAP öldü; kalan değer blackout hassasiyeti) |

---

## (ii) DALGA-3 ÖRTÜŞMESİ (WP-N/WP-S sermaye bekçileri + WP-S2)

Görev bağlamındaki "dalga-3" = son WP-N kanıt-hızı dalgası + WP-S sermaye/koruma turu (SB bekçileri,
kill#4). WP-H'ye KOMŞULUK ve ÇAKIŞMA ölçümü:

- **SB-3 / SB-4 (✅ v216) — WP-H ile ÇAKIŞMAZ, TEMA-KOMŞU.** SB-4 (`ROADMAP:218`) `portfolio.json`'un
  `store` kapısı DIŞINDAN değiştiğini YAKALAYAN denetim bekçisi (içerik-sha ≠ damga parmak izi); SB-3
  (`ROADMAP:224`) `taban_kaymasi` satırı. Bunlar **İÇERİK/denetim** katmanı; H9 **yazım MEKANİZMASI**
  katmanı (atomik+kilit). Farklı katman, tamamlayıcı: H9 "yazım bütün ve serialize" der, SB-4 "kitap
  kapı-dışından değişti mi" der. **Kesişim noktası:** kapı-dışı yazımlar (H9 tablosundaki #1-#9) aynı
  zamanda SB-4'ün yakalayacağı "damgasız yazım" adaylarıdır — H9 çağrı-noktası taşıması SB-4'ün
  alarm yüzeyini KÜÇÜLTÜR (daha az kapı-dışı yol). Çatışma yok; H9 işi SB-4'ü DESTEKLER.
- **kill#4 (kısmen indi).** Faz-5 kilidi artık ÖLÇÜYOR (n_eşleşen 4/4, kill#4 %0 — log 539); ama
  **kill kapısının yalnız BOZULMA sınıflarına daraltılması AÇIK** (`ROADMAP:252/335`, kart
  `EXE-2026-002-R1`). WP-H ile ilgisiz (icra/ölçüm kalemi); bugün etki %0.
- **E2 defteri kilidi (Kalem 8):** dalga-3'ün WP-H'ye EN yakın dokunuşu. WP-S/WP-E defterinde
  (`entry_execution.jsonl`) bir **H9 mekanizma düzeltmesi** — oku-değiştir-yaz'ı `file_lock`'a aldı
  (yukarıda POZİTİF BULGU). Bu, H9 çağrı-noktası taşımasının bir örneğinin dalga içinde
  yapıldığını gösterir; kalan #1-#9 aynı disiplinin devamıdır.

**Örtüşme hükmü:** WP-H (H9 çağrı-noktaları) ile dalga-3 (SB bekçileri) AYNI dosyaya YAZMAZ —
SB bekçileri `guard.py`/`analytics.py`/`broker.py`/`_save_broker` yüzeyinde; H9 taşıması
`memory.py`/`run.py`/`auth.py`/`config.py`/`earnings.py`/`adapters/data.py`'de. Dosya-ayrıklık
sözleşmesi açısından ÇAKIŞMA YOK. Tek dikkat: H9 #3 (`skill_evolve.py`) ve #4 (`hermes.py`) canlı
öğrenme-katmanı turlarıyla çakışabilir → o ikisi ayrı/koordine.

---

## (iii) KART GEREKSİNİMLERİ + OPERATÖR-BLOKLARI (adıyla)

**Kart gereksinimi (ön-kayıt):**
- H9 çağrı-noktası taşıması, WP-D artefakt yeniden-üretimi, systemd düzeltmesi = **mühendislik/ops
  kalemleri, ölçüm-kartı GEREKMEZ** (eşik-hükmü üreten edge ölçümü değil; kart disiplini
  `research/cards/` yalnız ÖLÇÜM kodu içindir — CLAUDE.md §3). Çivi + brief + git yeter.
- `dataset.load↔bars_integrity` BAĞLANIRSA: strateji ne üzerinde ölçüyor değişir → bu bir **kapsam
  değişikliğidir**, karta değil OPERATÖR onayına tabidir (aşağıda).
- kill#4 daraltması: kart `EXE-2026-002-R1` ZATEN kayıtlı (ön şart: Ç3 katalog düzeltmesi).

**OPERATÖR-BLOKLARI (adıyla, §6):**
1. **OCI Object Storage bucket + S3-uyumlu anahtar** → H10 Litestream aşama-2 (off-box PITR).
   Always-Free 20GB yeter (log 632). Bu gelene dek RPO = aynı-disk (medya arızası kapsanmaz).
2. **FMP planı / Massive geçişi** → earnings kapsaması (194/251) + temel/kazanç/insider katmanı;
   FMP 402 canlı (`integrity.production.starved: fmp_source 402`, SABAH TRİYAJI Kalem 7).
3. **systemd bakım penceresi** → `SuccessExitStatus=143` canlıya inişi (kod hazır; operatör penceresi
   + elle test-ateşleme gerekir). Ayrıca **N1 bildirim kanalı token'ı** (bunun ÖNCESİNDE inmeli).
4. **`dataset.load↔bars_integrity` bağlama kararı** → WP-D kapsam değişikliği (operatör).
5. **ajan-git MEKANİK kapısı** (PATH-shim/wrapper) → süreç/araç-katmanı kararı (operatör);
   WP-H DEĞİL (aşağıda gerekçe).

---

## (iv) ÖNCELİKLENDİRİLMİŞ PLAN (otonom vs bloklu)

### A) OTONOM (kod-güvenli, operatör-bloksuz, kart gerekmez) — DALGAYA HAZIR

**A1 — [EN YÜKSEK-DEĞER OTONOM] H9 Kademe-B kapı-dışı yazım taşıması.**
H9'un tek adlı açık kalemi; kapı HAZIR (`store.py:306 write_text` + kilitli-append kalıbı).
Öncelik sırası (değer × risk × dosya-ayrıklık):
- **(a) auth._write SABİT-TMP-ADI** (`auth.py:87-96`) — tek başına en yüksek risk: iki süreç aynı
  `.json.tmp`'ye yazar. `store.write_text`'e taşı ya da `mkstemp` (tekil-tmp) + fsync + flock.
- **(b) memory.py lessons.md** (`memory.py:212`) + **run.py scoreboard arşivi** (`run.py:172`) —
  düz `write_text` KIRPMA sınıfı: okuyucu yarım/BOŞ görüp sessiz "ders yok"/"karne yok" okur.
  İkisi de `store.write_text`'e. (Ayrı dosyalar → tek brief'te toplanabilir.)
- **(c) config.dump_yaml / earnings ×2 / adapters.data._write_bars / sprint._write_live_status** —
  "atomik ama fsync/flock yok" kalıbı; `store.write_text`'e ya da `_atomic_write`+`file_lock`'a.
- **(ERTELE) skill_evolve.py + hermes.py** — öğrenme-katmanı; canlı turlarla çakışır (Kademe C
  komşusu). Ayrı/koordine brief.
Değeri: "süreç-içi kilit / yarım-dosya" tehlike sınıfını KALAN çağrı-noktalarında yapısal kapatır;
SB-4'ün kapı-dışı-yazım alarm yüzeyini küçültür (dalga-3 desteği). Çivi: kapı-dışı-yazım tarayıcısı
(H9 zaten yazar-tekliği taramasına sahip — log 267) genişletilir.

**A2 — WP-D türetilmiş-artefakt yeniden-üretimi (kanonik tüketici kapsamında).**
component_ic/cf/eşik-eğrileri güvensiz-dönem-dışlamalı yeniden üretimi ZATEN kanonik tüketicilerde
dışlanıyor; kapsamı genişletmeden bir "yeniden-üretim + ayrışma=0 teyidi" turu otonomdur. (dataset.load
kararı GELMEDEN kapsamı genişletme — o operatör.)

**A3 — Gözlemlenebilirlik otonom bacakları (WP-S2 komşusu, SABAH TRİYAJI'dan).**
`learning_stalled` türev göstergesi (`watchdog.py`/`analytics.py`) · `universe_drift=unknown`'ın
KENDİSİNİ alarm yapma (lxml ImportError sessiz geçmesin). Bunlar WP-H değil ama aynı "kurulu ≠
çalışır / sessiz susma" ailesinden; ucuz.

### B) OPERATÖR-KAPILI (kod hazır ya da karar bekliyor)

**B1 — [OPERASYON P1] systemd `SuccessExitStatus=143` canlıya iniş.**
Kod HAZIR (`meridian.service:82`, yorum 74-83). Canlı DEĞİL (aşağıda §Kanıt). Bakım penceresi +
birim migrasyonu (`sudo cp` + `daemon-reload` + restart) + elle test-ateşleme. **BAĞ:** N1 kanalı
açılmadan ÖNCE inmeli. Dağıtım penceresi planının adım-6'sıyla (birim migrasyonu, token-koruma)
aynı disiplin. Otonom-KOD ama operatör-PENCERE.

**B2 — H10 Litestream aşama-2.** OCI bucket + anahtar gelince (operatör). Kod/konfig kalıbı hazır
(`litestream.yml` aşama-2 bloğu şerhli).

**B3 — `dataset.load↔bars_integrity` bağlama.** Operatör kapsam kararı; sonra A2 genişler.

**B4 — earnings kapsama / FMP planı.** Veri-kaynağı kararı (FMP yükselt / Massive geç).

### C) WP-H'YE GİRMEZ (ayrı sınıf) — ajan-git mekanik kapısı
`SuccessExitStatus` bir RUNTIME dayanıklılık kalemidir (WP-H). Ama **ajan-git kapısı** (PATH-shim/
wrapper; `git stash`ın pre-stash kancası YOK) bir **geliştirme-süreci/araç-katmanı** kalemidir —
H8 (git) ailesinin kardeşi ama H8 kapandı; bu yeni bir süreç-sertleştirmesi, çalışan sistemin
dayanıklılığı değil. Karar operatörde (SABAH TRİYAJI Kalem 13). WP-H'ye SOKMA; ayrı tooling kalemi.

---

## KANIT DEFTERİ — systemd exit-143 (A1 canlı, salt-okuma, 2026-08-09 ~14:2x UTC)

```
systemctl show meridian:
  SuccessExitStatus=            <-- BOŞ (düzeltme canlıda DEĞİL)
  NRestarts=0
  ExecMainCode=0 / ExecMainStatus=0 / ActiveState=active / SubState=running
  Active since: Sun 2026-08-09 14:15:23 UTC   (Main PID 136441 = uv)

/etc/systemd/system/meridian.service (A1):
  "NO SuccessExitStatus line in /etc unit"    <-- satır A1'de HİÇ YOK
  mtime: 2026-08-02 16:52:45 UTC              <-- v225 değişikliği (yerel 08-09 12:45) İNMEMİŞ

journalctl -u meridian (son 3 gün) — HER restart exit-143:
  Aug 07 17:33:42  Main process exited, code=exited, status=143/n/a → Failed with result 'exit-code'
  Aug 08 22:15:44  status=143/n/a → Failed with result 'exit-code'
  Aug 09 01:19:31  status=143/n/a → Failed with result 'exit-code'
  Aug 09 02:34:02  status=143/n/a → Failed with result 'exit-code'
  Aug 09 11:46:13  status=143/n/a → Failed with result 'exit-code'
  Aug 09 14:15:22  status=143/n/a → Failed with result 'exit-code'

journalctl -u meridian-fail-notify.service (OnFailure her seferinde ateşliyor):
  [fail-notify] kanal yapilandirildi mi: False
  [fail-notify] NO-OP: TELEGRAM_BOT_TOKEN+CHAT_ID veya MERIDIAN_WEBHOOK_URL yok (operator kalemi)
```

**Neden 143:** ExecStart `uv run`dır; restart/stop'ta systemd SIGTERM yollar, `uv`nin çocuğu
(uvicorn) SIGTERM'le ölünce `uv` **143 (128+15) EXIT KODUYLA** çıkar. Varsayılan `SuccessExitStatus`
SİNYALLE ölmeyi temiz sayar ama `uv`nin PROPAGE ETTİĞİ 143 EXIT KODUNU saymaz → birim "failed" →
OnFailure → fail-notify (`meridian.service:74-82` yorumu bunu tam anlatıyor).
**Bugün zararsız** (kanal boş, NO-OP); **N1 açılınca her restart yanlış "FAILED" alarmı gönderir.**
İşte bu yüzden systemd düzeltmesi kanal-açılışının ÖN-ŞARTI (SABAH TRİYAJI §i Kalem 1, "kanal-
açılışında P1").

---

## ÖLÇÜLEMEYENLER (dürüst boşluklar)

- **loop.py Kalem-8 kilidinin commit durumu.** Git kısıtı gereği yalnız çalışma-ağacı içeriği
  ölçüldü (mtime 08-09T16:47, "KALEM 8, 2026-08-09" yorumlu). Commit'li mi, ayrı-oturum çalışma-ağacı
  değişikliği mi — DOĞRULANMADI (git koşulmadı).
- **Tam suite durumu.** Tek-otoriter kural + tur kısıtı gereği koşulmadı. Son referans 4133/0 @
  `4dbe688` (08-03). H9 çağrı-noktası taşıması indiğinde otoriter suite Rol-1'de koşmalı.
- **H9 tablosundaki #9 (`sprint._write_live_status`) satır-numarası** log'dan alındı; kod grep'i
  fonksiyonun `sprint.py:305` referansını gördü ama yazım gövdesinin tam satırı ayrıca
  numaralanmadı (kalıp doğrulandı, tekil satır değil).
- **14:15 UTC restart'ının sebebi** (dağıtım mı, elle mi) — journal'da exit-143 görüldü, tetikleyen
  komut ölçülmedi.

---

## DÖNÜŞ (özet)

- **En yüksek-değer OTONOM kalem:** H9 Kademe-B kapı-dışı yazım taşıması — önce `auth._write` sabit-tmp
  çakışması (`auth.py:87-96`), sonra `memory.py:212`/`run.py:172` kırpma-sınıfı düz yazımları
  `store.write_text`'e. Kapı hazır, operatör-bloksuz, kart gerekmez, dalga-3'ün SB-4 alarm yüzeyini
  küçültür.
- **systemd daemon-reload durumu:** düzeltme (`SuccessExitStatus=143`) birim dosyasında YAZILI
  (`deploy/oracle-a1/meridian.service:82`, yerel mtime 08-09 12:45) ama **CANLIDA DEĞİL** — A1 `/etc`
  birimi 08-02 tarihli, canlı `SuccessExitStatus=` BOŞ, her restart exit-143 ile "FAILED" (son 3
  günde 6 kez, fail-notify NO-OP'la kurtarıyor). daemon-reload + birim migrasyonu + restart bir
  bakım penceresi bekliyor (operatör); N1 kanalının ÖN-ŞARTI.
- **Belge yolu:** `docs/KESIF-WP-HD-2026-08-09.md`
