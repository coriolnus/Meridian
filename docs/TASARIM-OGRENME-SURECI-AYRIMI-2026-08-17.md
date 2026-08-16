# TASARIM — Öğrenme döngüsünün API sürecinden ayrılması (ROADMAP §2-50, "Tam A")

**Tarih:** 2026-08-17 (ölçümler 2026-08-16 UTC canlı sistemden) · **Rol-1 tasarımı** · **Operatör kapsam
kararı:** "Tam A: 1-5 hepsi" · **Sahibi:** WP3 (öğrenme döngüsü) + WP6 (sistem bütünlüğü)

---

## 1 · Sorun (ölçüldü, iddia edilmedi)

Operatör bildirdi: v248 dağıtımından sonra pano yavaşladı; Oracle panelinde toplam CPU **%25** —
4 OCPU'nun üçü kalıcı boşta.

`py-spy` ile ölçülen (canlı, pid 301965):

| ölçüm | değer |
|---|---|
| yakan iplik | `hermes-standby` (tek iplik, ana iplik değil) |
| yığın | `hermes_runtime._run → reflect.search_and_submit → coordinate_descent_search → _wf_cached → backtest.walk_forward → strategy.scan_entry` |
| API süreci CPU | %93-100, kesintisiz (672 sn / 720 sn duvar) |
| yük ortalaması | 1,14 (4 çekirdekte → **1 dolu, 3 boş**) |
| `/api/public/summary` | 2,6 / 14,0 / 3,3 sn |
| `/healthz` | 0,011 sn (ağır yola girmiyor) |
| 25 sn profil (50 Hz, 1392 örnek) | **patoloji YOK** — `storage.read_rows` %6,6 · json çözme %8,4 · `rolling.calc` %4,1 |
| 5 sn'de I/O | 0 KB, 0 `read()` → saf hesap |

**Kök neden:** öğrenme döngüsü API sunucusuyla **aynı süreçte** bir Python ipliği. GIL, pano
isteğini backtest hesabının arkasına diziyor. Üç çekirdek boşken pano 14 saniyeye çıkıyor.

**REGRESYON DEĞİL — ölçüldü.** Geçmiş altı aramanın süresi 1s55dk–3s14dk; bugünkü aynı bantta.
Yığındaki 8 modülün 7'si (`hermes`, `hermes_runtime`, `backtest`, `strategy`, `indicators`,
`storage`, `store`) v248 merge'inde AST düzeyinde hiç değişmedi; önbellek anahtarı `_param_parmak`
de aynı. Son `hermes_search_done` 2026-08-14 10:35'ti — sistem boştaydı, **dağıtımın restart'ı
uykudaki aramayı uyandırdı.** Dağıtım tetikledi, sebep olmadı.

**İşçi tavanı bir tasarım tercihi değil, bu kusurun yamasıdır.** `_havuz_tavani` =
`max(1, min(4, cpu−2))` → 4 çekirdekte 2 işçi. Kodun kendi gerekçesi:

> *"CANLI OLAY (2026-08-03, A1 4 OCPU): iki işçi iki saat %99,9 CPU'da koştu ve pano API'sini boğdu
> (8,8-10,4 sn) — operatör elle `renice` atmak zorunda kaldı. '-2' tam bu yüzden var."*

Üstelik hot faz (`coordinate_descent_search:127` → `_wf_cached` incumbent walk'ı) havuza **hiç
girmiyor**; havuz yalnız `_parallel_prefill_probes` fazında (satır 171). Üç belirti tek köke bağlı.

## 2 · Reddedilen yaklaşımlar

**C · Yalnız systemd CPU sınırı** — **çürük, ölçümle.** GIL çekişmesi süreç *içinde*. `CPUQuota`
öğrenmeyi yavaşlatır, panoyu hızlandırmaz: pano yine aynı GIL'i bekler, yalnız daha uzun.

**B · Incumbent fazını da havuza sok** — kökü çözmez. Koordine eden iplik hâlâ API sürecinde GIL
tutar (sonuç birleştirme, önbellek yazımı, kapı değerlendirmesi). Payı azaltır, sınıfı kapatmaz.
**A'dan SONRA anlamlı hâle gelir** ve o zaman "bonus" olur.

## 3 · Seçilen tasarım (A)

### 3.1 Bileşenler

| # | değişiklik | emsal | boyut |
|---|---|---|---|
| 1 | `meridian.service`: `MERIDIAN_AUTOSTART_HERMES=1` → `0` | — | XS |
| 2 | `meridian/learn_run.py` — döngüyü ön planda koşturan ince koşucu | `sprint_run.py` | S |
| 3 | `deploy/oracle-a1/meridian-learn.service` | `meridian-sprint@.service` | S |
| 4 | `SEARCH_PROGRESS` süreçler-arası olgu hâline gelir | `_persist()`/`STATUS_FILE` | **M — asıl iş** |
| 5 | Pano `start`/`stop`/`reflect_now` düğmeleri öbür süreci yönetir | `MERIDIAN_SPRINT_SYSTEMCTL` | M |

### 3.2 Zaten hazır olan (ek iş YOK)

- **Eşzamanlılık kilidi:** `reflect._ProcessLock` — `state/.reflect.lock` üzerinde `fcntl.flock`,
  BLOKSUZ. Docstring'i bu senaryoyu adıyla öngörmüş: *"süreç-içi `_reflect_lock` İKİNCİ BİR SÜRECİ
  durduramaz… kaybeden dürüst 'locked' cevabı alır."* Ayrı süreçte yansıma **zaten korunmuş.**
- **`_state` kalıcılığı:** `_persist()` `_state`i `STATUS_FILE`a yazıyor. Pano bu tarafı diskten
  okuyabilir hâle zaten yakın.
- **Kapı:** `api.py:411` `MERIDIAN_AUTOSTART_HERMES == "1"` — kapatmak kod değişikliği istemiyor.

### 3.3 Kalem 4 — neden KOZMETİK DEĞİL, GÜVENLİK kalemi

`SEARCH_PROGRESS` (`hermes.py:53`) saf bellek. **Üç tüketicisi var** ve ikisi süreç ayrımında
sessizce bozulur:

1. `hermes_runtime.status()` → pano. Bozulma: `active: false` + boş ilerleme. **Görünür, zararsız.**
2. `sprint._arama_durumu` → sprint kapısı. **TEHLİKELİ.** Docstring varsayımı açık:
   *"zamanlayıcı ve api AYNI SÜREÇTEDİR — daemon thread."* Ayrımdan sonra sözlük **okunamaz olmaz,
   BOŞ olur** → `running` falsy → "meşgul değil". Muhafazakâr yedek ("okunamıyorsa MEŞGUL say")
   bu yüzden **ateşlenmez** ve sprint, koşan bir aramanın üstüne antrenman başlatır.
3. `reflect.py:1557` — asılı-arama teşhis referansı.

Bu, deponun tekrar eden kusur sınıfının (*"üretici X yazar, tüketici Y okur"*) tam bir örneği ve
ayrım onu **üretmeden önce** kapatılmalı.

**Çözüm — tek yazım kapısı zaten var.** `hermes.py:57-68` `SEARCH_PROGRESS`in TEK yazım kapısıdır
(2026-08-12 asılı-arama vakasından kalma). Disk aynası **oraya** eklenir; üç üreticinin hepsi
otomatik kapsanır. Yeni bir yazım yolu AÇILMAZ.

**Okuyucu sözleşmesi (üç değerli, uydurma yasağına uygun):**

| durum | anlam | tüketici davranışı |
|---|---|---|
| dosya var, `running=true`, taze | arama koşuyor | sprint BAŞLAMAZ · pano ilerlemeyi gösterir |
| dosya var, `running=false` | arama yok | sprint başlayabilir |
| **dosya yok / bayat / okunamıyor** | **ÖLÇÜLEMEDİ** | sprint **MEŞGUL sayar** (muhafazakâr taraf korunur) · pano "ölçülemedi" yazar, "durdu" DEĞİL |

Bayatlık eşiği `sprint.ARAMA_BAYAT_SAAT`ten türetilir — **yeni eşik icat edilmez** (madde 3).

**Canlılık (`active`):** ipliğin `is_alive()`i yerine **kalp atışı**. `learn_run` her turda
`STATUS_FILE`a `heartbeat` damgası yazar; okuyucu yaşı eşikle karşılaştırır. Gerekçe: `systemctl
is-active` yalnız sürecin *var* olduğunu söyler, *ilerlediğini* söylemez — asılı bir döngü "active"
görünürdü. Kalp atışı ikisini de ölçer.

### 3.4 Kalem 5 — düğme yolu

Pano `start`/`stop` düğmeleri artık `hermes_runtime.start()/stop()` çağıramaz (o süreçte döngü yok).
Emsal `MERIDIAN_SPRINT_SYSTEMCTL` yolu: `systemctl start|stop meridian-learn`, `sudo -n` ile.
`reflect_now` (elle tetikleme) API sürecinde KALIR — tek seferlik, kısa, ve `_ProcessLock` onu
öğrenme sürecine karşı zaten koruyor.

### 3.5 Birim dosyası kararları

`meridian-sprint@.service` sertleştirmesi birebir devralınır. Farklar ve gerekçeleri:

- `Restart=always` (sprint'te `no`) — bekleme döngüsü kalıcı bir hizmet, tek seferlik iş değil.
- `CPUWeight=` API biriminden **düşük** — çekişmede pano kazanır. Bu bir CPU *tavanı* değil
  *ağırlık*: boştaki çekirdekler öğrenmeye tam açık kalır (asıl amaç buydu).
- `MERIDIAN_AUTOSTART_HERMES=1` bu birimde; `meridian.service`te `0`.
- Arama düğmeleri (`MERIDIAN_SEARCH_MAX_MIN`, `HERMES_SEARCH_BUDGET`, `MERIDIAN_PARALLEL_PROBES`)
  bu birime TAŞINIR — iki yerde durursa ayrışırlar (`dagit [1c]` bunu yakalar ama önce doğru kur).

## 4 · Kapsam DIŞI (bilinçli)

- **`_havuz_tavani` `cpu−1`'e çıkarılmaz.** Ayrım indikten SONRA, **ölçüm kartıyla**. 2026-08-03
  vakası tam o tavanla yaşandı; kazanç duvar-saati cinsinden ölçülmeden eşik değişmez (madde 3).
- **Faz-1'in fold-paralelliği** ayrı kalem (B).
- **Öğrenme mantığı değişmez.** Bu bir yerleşim değişikliğidir; arama sonuçları bit-özdeş kalmalı
  (`_PROBE_CACHE` anahtarlı, determinizm sıraya değil anahtara dayanıyor — `_havuz_tavani`
  docstring'i bunu beyan ediyor).

## 5 · Doğrulama (ölçüm-önce)

Ayrım "işe yaradı" denmeden ÖNCE yazılan ölçüt — kart `research/cards/` altına ön-kayıtla:

| ölçüt | bugünkü taban (ölçüldü) | kabul |
|---|---|---|
| `/api/public/summary` p95, arama KOŞARKEN | 14,0 sn | **< 1,0 sn** |
| toplam CPU kullanımı, arama koşarken | %25 (1/4 çekirdek) | **> %40** |
| arama duvar-saati | 1s55dk – 3s14dk | **artmamalı** (bit-özdeşlik değil, bant içi) |
| arama sonuçları | — | `_PROBE_CACHE` anahtarları **bit-özdeş** |
| sprint kapısı | (bugün aynı süreç) | ayrımdan sonra da koşan aramada **BAŞLAMAMALI** |

**Kill:** sprint kapısı ayrımdan sonra koşan aramanın üstüne başlarsa tasarım GEÇERSİZ — geri alınır
(kalem 4 yanlış kurulmuş demektir).

## 6 · Dağıtım penceresi

Yazım sırasında canlıda bir arama koşuyor (21:03:48'de başladı, 1s55dk–3s14dk bandı). **Dağıtım o
arama bitmeden yapılmaz** — restart onu öldürür ve bir öğrenme turu çöpe gider. `hermes_search_done`
olayı beklenir.
