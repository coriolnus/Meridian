# DESEN ETÜDÜ — kategori taraması ve Meridian'a eşleme (2026-08-06)

**Soru:** "Otonom/algoritmik trading ajanını insan gözetiminde çalıştıran platformlar"
kategorisinde arayüzler operatöre hangi **işleri** sunuyor — ve bunların hangileri Meridian'ın
**bugün elinde olan** veriyle karşılanabilir?

**Statü:** salt-araştırma + eşleme. Kod yazılmadı, git koşulmadı, canlıya dokunulmadı.
Hüküm cümlesi kurulmadı (SUCCESS/PASS yok); sayı, gözlem ve eşleme verildi.

**Yöntem ve sınırları — önce bunlar:**

1. **Kategori tarafı** WebSearch/WebFetch ile resmî dokümantasyondan derlendi; her satır URL
   taşır, erişim tarihi 2026-08-06'dır. Ekran görüntüsü alınamadı (oturum açma gerektiren
   yüzeyler); dolayısıyla "şu widget şu köşede" türü yerleşim iddiası YOK — yalnız dokümante
   edilmiş **işlevler** kaydedildi. Doküman bulunamayan yer "ölçülemedi + neden" yazıldı.
2. **Meridian tarafı** `meridian/api.py`, `meridian/analytics.py`, `meridian/web/app.js` ve
   `state/*` dosyalarından **doğrulandı**; hiçbir alan adı hatırlanarak yazılmadı. "Gösteriliyor
   mu?" sorusu `app.js` içinde alan adının geçip geçmediğiyle ölçüldü — bu **kaba** bir ölçüttür
   ve sınırını beyan ediyorum: bir alanın `app.js`'te geçmesi onun *işi cevapladığı* anlamına
   gelmez (teşhis dökümünde bir satır olarak basılıyor olabilir). Bu yüzden Bölüm C'nin ölçütü
   "alan hiç render edilmiyor" değil, **"iş cevaplanmıyor"**tur; ikisi ayrı ayrı işaretlendi.
3. Bu etüt **dışarı bakar**. `docs/UX-SADELESTIRME-DENETIMI-2026-08-06.md` aynı günün **içeri
   bakan** denetimidir (Nielsen sezgiselleri, adım sayımı, kart sözleşmesi). İkisi kardeş
   dokümandır; bu dosya oradaki bulguları tekrar etmez.

---

## PAYDA — Meridian'ın bugün servis ettiği veri (koddan doğrulandı)

Eşlemenin paydası budur. `meridian/api.py` **69 rota** kaydediyor (`grep -c "@app.(get|post|put|delete)"`);
aşağıda iş-eşlemesi için kullanılanlar ve taşıdıkları alanlar var. Alan adları canlı koddan alındı.

### Uçlar ve taşıdıkları

| Uç | api.py satırı | Taşıdığı (doğrulanmış alanlar) |
|---|---|---|
| `/api/today` | 1054 | `heartbeat`, `heartbeat_age_seconds`, `stale`, `halted`, `regime`, `open_positions`, `todays_plans`, `todays_plan_date`, `day_pnl_pct`, `equity`, `current_exposure_pct`, `pending_count`, `armed_plans`, `alpaca_submitted`, `verdict_counts`, `mode`, `autonomy_level`, `broker`, `son_dongu{var,date,ts,yas_saat,candidates,plans,armed,regime,open_positions,data_ok,halted}`, `latest_session`, `kitap{realized_pnl,day_start_equity,peak_equity}`, `defter` (ledgerstamp sayımları), `sermaye_koken`, `inbox_count` |
| `/api/summary` | 962 | `goal`, `mode`, `autonomy_level`, `strategy_version`, `score_detail`, `ladder` |
| `/api/signals` | 1111 | `candidates`, `plans`, `as_of`, `latest_signal_date`, `latest_session`, `data_provider`, `candidate_review`, `ledger{plans_total,plans_shown,candidates_total,candidates_shown,cap}` |
| `/api/performance` | 1388 | `equity_curve`, `score_detail`, `kelly`, `tail_risk`, `slippage_measured`, `benchmark_relative`, `per_regime`, `per_skill`, `n_trades`, `recent_trades` |
| `/api/diagnostics` | 2255 | en geniş uç — `hud`, `scheduler`, `saglayicilar`, `ogrenme`, `gatekeeper{plans[gate_verdict,gate_reasons,gate_checks,llm_opinion,llm_veto],arming}`, `reconcile{ghosts,drift,stripped,hwm_pairs,partial_fills,failed_submissions}`, `icra{slipaj,kotumser_band,gece_gunduz}`, `risk{blackout_radar,earnings_pit}`, `mlops` (≈45 alan), `watchdog`, `sessiz_hat`, `alarm_butcesi`, `hotstate`, `marketstream`, `barfeed`, `intraday`, `integrity`, `coverage`, `pipeline`, `ledgers`, `ledger_contract`, `sieve` |
| `/api/plots` | 1236 | kurulum × rejim verim matrisi; hücre başına `n`, `mean_r`, `exits`, `recent` |
| `/api/alpaca` | 2891 | `paper_available`, `account{equity,cash,buying_power,positions[],open_orders[]}`, `reconcile`, `stream` |
| `/api/approvals` | 3103 | `level`, `inbox[{type,id,title,evidence,actions}]`, `pending` |
| `/api/alerts` | 1677 | `notify.inbox()` — ACK'lenmemiş alarmlar, imzaya göre gruplu |
| `/api/trade/{id}` | 3076 | tek işlemin tam kaydı + son 60 barlık OHLC serisi |
| `/api/skills` | 1170 | `counts`, `catalog`, `recommendations`, `revisions`, `revision_history`, `recent_runs` |
| `/api/hermes` | 2744 | `status`, `spend`, `recent`, `skill_recommendations`, `learning`, `scheduler`, `sprint`, `integrations` |
| `/api/agent` | 1156 | `scoreboard`, `hypotheses`, `calibration_scatter`, `calibration`, `skill_attribution` |
| `/api/spend` | 949 | `month`, `spent_usd`, `budget_usd`, `remaining_usd`, `over_budget`, `calls_this_month`, `thought_tokens`, `recent[30]` |
| `/api/market` | 1144 | `as_of`, `n`, `stale_n`, `retired_n`, `source`, `intraday`, `regime`, `rows[]` |
| `/api/events` | 956 | son 80 olay |
| `/api/selfreview` | 1668 | `attention`, `contradictions` |
| `/api/memory` | 1162 | `lessons_md`, `hypotheses` |
| Yazma yüzeyi | 1572–3304 | `/api/control/halt`, `/api/control/cancel_open`, `/api/control/learn_halt`, `/api/alpaca/close_all`, `/api/alpaca/submit_armed`, `/api/plan/{id}/onayla`, `/api/skills/apply`, `/api/skills/revision`, `/api/alerts/ack`, `/api/broker_reject/ack`, `/api/scheduler/advance`, `/api/sprint/start|stop`, `/api/halt`, `/api/resume` |

### Defterlerin taşıdığı kayıt-düzeyi kanıt

| Defter | Doğrulanmış alanlar |
|---|---|
| `trade_plans.jsonl` | `gate_verdict`, `gate_reasons[]`, **`gate_checks[{check,passed,severity,value,threshold,note}]`**, `skill_chain[]`, `score`, `setup`, `regime_at_plan`, `entry_trigger`, `stop`, `targets`, `size_r`, `dormant_setup`, `strategy_version` |
| `trades.jsonl` | `plan_id`, `r_multiple`, `mfe_r`, `mae_r`, `bars_held`, `exit_reason`, `costs`, `skill_chain[]`, `regime`, `setup`, `score`, `strategy_version`, `exploration` |
| `counterfactuals.jsonl` | **alınmamış planların simüle sonucu** — `taken`, `entered`, `r_multiple`, `mfe_r`, `mae_r`, `exit_reason`, `verdict`, `blocked_by` |
| `near_miss.json` | `resolved_total` (canlıda **4988**), `buckets{<blocked_by>:{n,entered,n_r,avg_r,by_regime{}}}`, `_kaynak` künyesi (`source:"yalnız-simüle"`, `n_real:0`) |
| `mirror_orders.json` | client-order-id başına `status`, `event`, `symbol`, `side`, `filled_qty`, `filled_avg_price`, `order_id`, `updated` |
| `pipeline_runs.jsonl` | `run_id`, `pipeline`, `started`, `finished`, `skills_invoked[]`, **`skills_declared_not_run[]`**, `skills_skipped[]`, `artifacts[]`, `status`, `error` |
| `spend.jsonl` | çağrı başına `ts`, `model`, `in_tokens`, `out_tokens`, `cost_usd`, `note`, `thought_tokens` |
| `events.jsonl` | canlıda ~9 MB; `agent_call{kind,model,attempt,empty,preloaded}` dâhil olay sözlüğü; LLM ham çıktısının **sır-maskeli 200 karakterlik özeti** (hermes.py:1570–1601 `_ham_ozet`) |
| `scoreboard.json` | `current_version` + sürüm başına `params`, `backtest_oos`, `baseline_verdict`, `baseline_source`, `baseline_n_trades`, `baseline_span_days` |
| `exit_efficiency.json` | çıkış nedeni başına `n`, `avg_mfe_r`, `avg_realized_r`, **`left_r`** (masada bırakılan R) |
| `mae_profile.json` | kazanan/kaybeden ayrı `medyan`, `ort`, `p90`, `maks` (R birimi) |
| `regime_edge.json` | rejim başına `n`, `avg_r`, `win_rate` + künye |

### Toplanıyor ama BİLEREK bağlanmamış (bunlar "fırsat" DEĞİL — beyanlı erteleme)

Etüt sırasında üç defter "yazılıyor, hiçbir uçtan servis edilmiyor, panoda hiç geçmiyor" diye
işaretlendi. Kaynak taraması bunların körlük değil **gerekçeli erteleme** olduğunu gösterdi
(`meridian/codelaw.py:308–323`) — bu yüzden Bölüm C'de kaldıraç olarak SAYILMADILAR:

| Defter | Neden bağlanmadı (codelaw beyanı, kısaltılmış) |
|---|---|
| `short_interest.json` (FINRA, anahtarsız, canlıda dolu) | kapıya kaçınma filtresi olarak bağlanması, karşı-olgusal defterde "filtreli vs filtresiz" **ölçüldükten sonraki** tura ertelendi |
| `insider_signals.json` | `kapsam.siniflama_hazir_mi` True olana kadar bilinçli erteleme — "bugün bağlanan bir okuyucu `siniflanamadi` dolu bir dosyayı sinyal sanardı" |
| `insider_trades.json` | dış tüketici 3 yıllık sınıflama penceresi dolmadan bağlanamaz (FMP ücretsiz planda `search` ucu 402) |

Bunları panoya koymak, ölçülmemiş bir şeyi ölçülmüş gibi göstermek olurdu. Kalemin sahibi
ölçüm sırasıdır, tasarım turu değil.

### Bugünkü yüzey

Yedi alan sayfası (`index.html:1497–1573`): **Genel Bakış · Veri Sağlığı · Koşu · Portföy ·
Öğrenme · Gözetim · Kilitler**, yirmi bölüm kabı. Üst barda kalıcı: HUD, durum hapı, dört
kademeli **KRİZ** grubu (`Soft Halt` · `Cancel-Open` · `Flatten` · `Halt Learning`) ve `HALT`.
Her sayfanın üstünde global **sessiz hat**. `⌘K` komut paleti (25+7 komut, iki adım onay).
`app.js` 7.511 satır — pano zaten yoğun; bu etüdün varsayımı "eksik pano" DEĞİL, "yanlış
birleştirilmiş iş" olabileceğidir.

---

## HÜKÜM SÖZLÜĞÜ (Bölüm B'de kullanılan dört değer)

| Değer | Anlamı |
|---|---|
| `zaten var, biçim açık` | İş bugün cevaplanıyor; veri de yüzey de yerinde. Kalan tartışma biçim/yerleşimdir, bu etüdün konusu değil. |
| `veri var ama gösterilmiyor — FIRSAT` | Alan(lar) canlı state'te ve/veya uçta var; iş bugün **cevaplanmıyor** (hiç render edilmiyor ya da parçaları farklı yerlerde durup birleşmiyor). |
| `veri yok — YENİ MODÜL ADAYI` | İş değerli ama girdisi bugün yok. Elenmez; **(a)** ne üretmeli, **(b)** mevcut veriden türetilebilir mi yoksa dış kaynak mı ister, **(c)** kaba büyüklük (S/M/L) ile aday yazılır. |
| `yasaya aykırı — REDDET` | Desen kategoride yaygın ama Meridian'ın yazılı bir yasasını çiğniyor. Yasa adıyla işaretlenir. |

**Büyüklük ölçeği:** `S` = tek okuma-ucu + görünüm (yeni defter yok) · `M` = yeni türetme +
kalıcı defter (kadans/geri-doldurma gerekir) · `L` = yeni veri hattı ya da dış bağımlılık
(sağlayıcı/kota/maliyet kararı; operatör kalemi).

**Kart kuralı:** bir aday **kenar iddiası** üretiyorsa (bir sinyalin/filtrenin kâr ettiğini
söylüyorsa) `research/cards/` ön-kayıt kartı ister ve bu, adayın notuna yazılır. Saf görünüm
ve saf türetme modülleri kart istemez.

**Elimizdeki dış kaynaklar** (yeni modül adaylarının (b) sütununu bunlar bağlar):
Alpaca (kâğıt ayna, canlı) · Massive (`adapters/massive.py`; arşiv derinliğinin meşru yolu —
plan yükseltmesi operatör kalemi) · FMP (ücretsiz katman; `page>=1`, `limit>100`, `search`
uçları 402 ölçüldü 2026-07-30) · EDGAR (`adapters/edgar_shares.py`) · FINRA short interest
(anahtarsız) · Cboe (gecikmeli) · Finviz Elite (anahtar operatör kalemi) · QuantConnect
(hesap var, **FREE**; ToS gereği **veri platformdan ÇIKAMAZ** — meşru desen ölçümün platform
içinde koşup dışarı yalnız hüküm-sayısının taşınması, `docs/QC-ENTEGRASYON-DEGERLENDIRMESI.md`
§0 ve §4).

---

# BÖLÜM A — KATEGORİ TARAMASI

Tarama **iş** temellidir, widget temelli değildir. Aynı iş birden çok platformda farklı biçimde
çıktığı için katalog **işe göre** birleştirildi; "hangi platform(lar)" sütunu kanıtı taşır.
Tüm URL'lere erişim tarihi **2026-08-06**. Hiçbir platformda **ekran görüntüsü alınmadı** (canlı
panolar oturum açma ardında) — bu yüzden yerleşim, renk, grafik-tipi (gauge/donut/pie) ve
rozet/streak gibi **görsel** iddialar bu etütte **ölçülemedi** sayıldı; yalnız resmî metinde
adı geçen işlevler kaydedildi.

Kısaltmalar: **QC** QuantConnect · **CMP** Composer · **ALP** Alpaca · **TV** TradingView ·
**FT** Freqtrade/FreqUI · **HB** Hummingbot · **IBKR** Interactive Brokers TWS.

## A.1 — Hayatta kalma ve süreç sağlığı

| iş | platform(lar) | operatörün cevapladığı soru | tipik biçim | neyi çözüyor |
|---|---|---|---|---|
| Döngünün hâlâ döndüğünü doğrulama | FT, HB | "Süreç ayakta ama döngü dönüyor mu?" | `/health` → son bot-döngüsü damgası; HB alt çubuk: CPU, bellek, aktif thread, oturum süresi | "Ekran donuk mu, bot mu öldü" ayrımı — sessiz ölüm |
| Kesinti anını getiriyle **aynı eksende** görme | QC | "Gece koştu mu, ne zaman düştü, yeniden mi dağıtıldı?" | Strategy Equity üzerinde **"Meta"** serisi: dağıtım / durdurma / runtime-error damgaları eğrinin üstünde | Hayatta-kalmayı ayrı bir "status" kutusu yerine zaman ekseninde cevaplar |
| Karar üretiminin sürdüğünü, emirden **bağımsız** doğrulama | QC | "Son sinyalini ne zaman üretti?" | **Insights** sekmesi (sayfalamalı, JSON indirilir, UTC damgalı) | "Emir yok" ile "sinyal yok"u ayırır — emir yokluğunun iki farklı nedeni var |
| Kesintiye dayanıklılığı **önceden** ayarlama | QC | "Broker bağlantısı koparsa ne olacak?" | Dağıtım sihirbazında otomatik yeniden başlatma: en fazla **5 kez**, yalnız algoritma **≥5 dk** koşmuşsa | Geçici kesintiyi kalıcı ölüme dönüştürmeme + kodlama hatasında sonsuz restart döngüsünü engelleme |
| Kurulum mu strateji mi bozuk ayrımı | HB | "Sorun stratejide mi kurulumda mı?" | `doctor` → kurulum sağlık denetimi | Yanlış katmanda hata avlamayı önler |

## A.2 — Mod ve kimlik dürüstlüğü ("hangi gerçeklikteyim?")

| iş | platform(lar) | operatörün cevapladığı soru | tipik biçim | neyi çözüyor |
|---|---|---|---|---|
| Kâğıt mı gerçek mi doğrulama | FT, HB, ALP, TV | "Bu emir gerçek para mı harcayacak?" | FT `/show_config` → `dry_run` alanı · HB konnektör adında `paper_trade` son eki + `status` satırı · ALP sol üstte paper/live hesap seçici · TV "Trade" menüsünde Paper Trading gerçek brokerlarla **aynı listede** | Kategorinin en pahalı kaza sınıfı: yanlış modda olduğunu bilmemek |
| Kâğıdın **nerede yalan söylediğini** bilme | ALP, TV, FT | "Simülasyon neyi taklit etmiyor?" | ALP: paper varsayılan $100.000; borrow fees **"Coming Soon!"** (canlıda var) · TV: sembol başına tek pozisyon, GTC yok, komisyon/kaldıraç ayrı · FT backtest varsayımları: "All orders are filled at the requested price (no slippage)…", "Backtesting will **never** replace running a strategy in dry-run mode" | Paper→canlı sapmasının kaynaklarını **önceden** adlandırır |
| Panodaki sonucun **hangi koda** ait olduğunu doğrulama | QC | "Gördüğüm sonuç hangi sürümden?" | **Code** sekmesi: dağıtılan proje dosyaları + "Clone Algorithm" | Yerel kopya ile canlı arasındaki sessiz sürüm kayması |
| Emri kimin koyduğunu ayırma | IBKR | "Bu emri bot mu ben mi koydum?" | `orderStatus.clientId` + kalıcı `permId` | İnsan-bot çift-emir karışıklığı |
| Botun hangi kimlikle bağlandığını yönetme | ALP | "Bu anahtar hangi hesaba gidiyor?" | Her paper hesap için **ayrı** anahtar; base URL paper panosunda gösterilir | Paper anahtarıyla canlıya bağlanma hatası |

## A.3 — Karar zincirinin denetimi ("neden yaptı / neden yapmadı?")

| iş | platform(lar) | operatörün cevapladığı soru | tipik biçim | neyi çözüyor |
|---|---|---|---|---|
| Sinyal → emir → dolum zincirini uçtan uca denetleme | QC, ALP, IBKR | "Sinyal emre, emir doluma dönüştü mü?" | QC **Orders** sekmesi: gönderim/güncelleme/iptal/dolum olayları, ET damgalı, sayfalamalı, **CSV indirilir** · ALP emir durum sözlüğü · IBKR Activity Panel Orders | Zincirin hangi halkasında koptuğunu adlandırır |
| "Neden çalışmıyor" ayrımını **adlandırılmış** duruma indirme | IBKR, ALP | "Reddedildi mi, bekletiliyor mu, iptal mi?" | IBKR durum sözlüğü: PendingSubmit, PreSubmitted, Submitted, ApiCancelled, Cancelled, Filled, **Inactive** + `whyHeld` ("Reason order is not working") · ALP: `new, partially_filled, filled, done_for_day, canceled, expired, replaced, pending_cancel, pending_replace` + nadir `rejected, suspended, calculated` | Sessiz başarısızlığı adlandırır — "hiçbir şey olmadı" belirsizliğini kaldırır |
| **Eylemsizliğin** nedenini görünür kılma | FT, CMP | "Sinyal var ama neden girmiyor?" | FT `/locks` (kilitli çiftler + `reason` alanı) + log `Pair <pair> is currently locked` · CMP "Neden nakit tutuyor": %0,001 ücret tamponu, clearing minimumu (Alpaca $1 / Apex $5), kesirli işleme uygun olmayan hisse, dolmayan emir | **Kategorinin en değerli deseni:** "hiçbir şey olmadı" ekranını "şu yüzden hiçbir şey olmadı"ya çevirir |
| Kapasite/doygunluk okuma | FT | "Yeni sinyal gelse alabilir miyim?" | `/count` → kullanılan / mevcut trade (`max_open_trades`) | "Sinyal vardı ama girmedi" vakasının en sık nedeni |
| Uzun soluklu icranın ilerlemesini izleme | IBKR | "Bu algo emrinin ne kadarı bitti?" | Accumulate/Distribute Summary: gönderilen/alınan/kalan adet, son işlem fiyatı, ortalama fiyat, son artıştan bu yana geçen süre, sonraki artışa kalan süre; doğrusal ilerleme dolgusu | Uzun icrada belirsizlik |
| Tek işlemi emir düzeyine kadar açma | FT, QC | "Bu trade'in altındaki emirlere ne oldu?" | FT `/order <trade_id>`, `/reload_trade <id>` ("Only works in live") | Bot defteri ile borsa arasındaki uyuşmazlık teşhisi |

## A.4 — İcra kalitesi ve simülasyon-gerçek boşluğu

| iş | platform(lar) | operatörün cevapladığı soru | tipik biçim | neyi çözüyor |
|---|---|---|---|---|
| **Canlının backtest'ten sapmasını ölçme ve kökünü adlandırma** | QC | "Canlı simülasyondan sapıyor mu, neden?" | Eşzamanlı **OOS backtest** eğrisi canlının üstüne bindirilir ("mükemmel mutabakat = tam örtüşme"); sapma **kapalı bir neden listesine** indirgenir: reality modeling error, market impact, dolum zamanlaması (backtest anlık vs canlı ~500 ms), tick dilim boyu (1 ms vs 70 ms), split ayarı, açılış/kapanış açık artırma gecikmesi, hesap küçüklüğünden yuvarlama, restart sonrası non-deterministik durum | Kök-neden avını kapalı listeye indirger; **"bilinmiyor" demeyi zorlaştırır** |
| Fill'leri fiyat + komisyonla denetleme | IBKR | "Bugün ne doldu, kaça, ne komisyonla?" | Trade Log: Action, Quantity, Price, Exchange, Date/Time, Order ID, **Commissions**, Account, Yield | İcra kalitesi ve maliyet denetimi |
| Parça parça fill'i tek anlamlı rakama indirme | IBKR | "Bu sembolde günü net ne kapattım?" | Trade Summary: gün içi tüm alım/satımlar underlying'e göre gruplanmış, ortalama alış/satış + Net | Fill parçalanmasının yarattığı okuma yükü |
| Bar-içi dolum varsayımını sınama | TV | "Dolumlar gerçekçi mi?" | Broker emulator: emir bar kapanışından sonra dolar, açılış high'a yakınsa **open→high→low→close** sırası varsayılır, bar içinde **gap yok**; **Bar Magnifier** alt zaman diliminden OHLC çeker | Backtest kârının varsayımdan mı geldiğini **test edilebilir** kılar |
| Ölçüm koşullarını görünür ve değiştirilebilir kılma | TV | "Bu sonuç hangi varsayımla çıktı?" | **Properties**: Initial capital (varsayılan **1.000.000**), Order size, Pyramiding, Commission, **Slippage** (tick), Margin long/short — buradaki değer **koddakini ezer** ve raporu anında değiştirir | "Aynı strateji, farklı sonuç" bulmacasını çözer |
| Yapısal olarak geçersiz ölçüm rejimini adlandırma | TV | "Bu sonuca güvenebilir miyim?" | Non-standard grafik uyarısı (Heikin Ashi, Renko → sonuçlar gerçek piyasa koşullarını **yansıtmaz**); varsayılan aralıkta yalnız **son 9000 işlem** için tekil veri | Sahte güveni yapısal düzeyde keser |
| Örneklem kuraklığını aşma **ve bedelini beyan etme** | TV | "Grafikteki barlar yetmiyor" | **Deep Backtesting**: 2M bara / 1M işleme kadar; sonuçlar **yalnız** rapor sekmesinde — **grafikte gösterilmez** | Derinliği açarken kaybolan görsel doğrulamayı sessiz bırakmaz |

## A.5 — Performans muhasebesi

| iş | platform(lar) | operatörün cevapladığı soru | tipik biçim | neyi çözüyor |
|---|---|---|---|---|
| Kapanmış vs açık ayrımıyla K/Z okuma | FT | "Gerçekten kazandım mı, açıklar mı taşıyor?" | `/profit` → ROI (closed trades) ve ROI (all trades) **ayrı satır**; + profit factor, winrate, expectancy, max drawdown, ort. süre | Gerçekleşmemiş kârı gerçekleşmiş sanma hatası |
| **"Hiç işlem yapmasaydım"a karşı ölçme** | HB, QC, CMP, TV | "Bot değer kattı mı, piyasa mı taşıdı?" | HB `history`: **Hold Portfolio Value** vs Current Portfolio Value, Trade P&L, **Fees Paid** ayrı satır, Total P&L, Return % · QC Benchmark (varsayılan SPY) · CMP "Add Benchmarks" · TV **Buy&hold return** | Betayı alfadan ayırır — bir getiri sayısının gizleyebileceği en önemli şey |
| Çıkış nedeni dağılımını okuma | FT | "Neden çıktım — ROI mi, stop mu, sinyal mi?" | `/stats` (= `/exits`, `/entries`, `/mix_tags`): çıkış nedenine göre kazanç/kayıp + ort. tutma süresi | Stratejinin hangi mekanizmayla kazandığını/kaybettiğini ayırır |
| İşlem kalitesinin **dağılımını** görme | TV | "Tek bir şanslı işlem mi taşıyor?" | Trades analysis: percent profitable, avg winning/losing trade, **ratio avg win/avg loss**, largest win/loss, **avg # bars in trades / winning / losing** | Ortalamanın arkasındaki dağılımı ve tutma süresini açar |
| Katkıyı ayrıştırma (çift / varlık / strateji) | FT, HB, CMP | "Kâr tek bir yerden mi geliyor?" | FT `/performance` (çifte göre) · HB Instances içinde controller kırılımı (ID, connector, pair, realized/unrealized/net PNL, volume) · CMP `holding-stats` "direct and symphony allocations by holding" | Konsantrasyon riski + çok-strateji portföyünde atıf |
| Bakiyenin **işlem-dışı** nedenle değişmesini açıklama | ALP | "Bakiyem neden değişti, işlem yapmadım?" | Account Activities: işlem tarafı **FILL**; işlem-dışı **DIV, INT, FEE, CFEE, CSD, CSW, JNLC, SSP (split), SSO (spinoff), MA, REORG** vb. | K/Z sapmasının strateji mi kurumsal olay/ücret mi olduğunu ayırır |
| Riske göre düzeltilmiş okuma | TV, CMP, QC | "Getiri alınan riskin karşılığı mı?" | TV: Sharpe, Sortino, Profit factor, **Margin calls** · CMP: Annualized return, Sharpe, Max drawdown, **Calmar** · QC bannerında **PSR** | Ham getiri yanılsaması |
| Zaman-serisi ritmi | FT | "Son 7 gün / 8 hafta / 6 ay nasıl gitti?" | `/daily <n>`, `/weekly <n>`, `/monthly <n>` | Tek-gün gürültüsünü trendden ayırma |

## A.6 — Risk, fren ve durdurma

| iş | platform(lar) | operatörün cevapladığı soru | tipik biçim | neyi çözüyor |
|---|---|---|---|---|
| **Aciliyet seviyesini seçme** (üç kademe) | FT, QC, HB | "Ne kadar sert durdurayım?" | FT: `/pause` (yeni giriş yok, açıklar **kendi kurallarıyla** biter) → `/stop` → `initial_state: stopped` (yeniden başlatmada da durur) · QC: **Stop** (yürütmeyi durdurur) vs **Liquidate** (kill switch: hepsini satar, sonra durdurur) — **iki ayrı düğme** · HB: STOP (kademeli) vs force-stop ikonu | Yanlışlıkla pozisyon kapatmayı önler; "panik" ile "kontrollü fren"i ayırır |
| Durdurmanın **açık emirlere** etkisini bilme | FT, HB | "Durdurursam asılı emirlerim ne olur?" | FT `cancel_open_orders_on_exit` ayarı · HB `stop` = "cancel all active orders", `exit` = "Exit and cancel all outstanding orders" | Yetim emir riski — "durdurdum sandım" |
| Gözetimsiz koşuda otomatik fren | FT, HB | "Ben uyurken kanamayı kim durdurur?" | FT protections: **StoplossGuard** (lookback içinde n stop → `stop_duration` boyunca dur), **MaxDrawdown**, **LowProfitPairs** (çift bazlı), **CooldownPeriod** (mum-sonu "waterfall" koruması) · HB `kill_switch_mode` + `kill_switch_rate` (−5 = %5 zarar; yeni işlem olmadan, yalnız fiyat hareketiyle de tetiklenir) | Zincirleme zararın sınırlanması; cerrahi kesme (tüm botu durdurmadan) |
| **İptali olmayan aksiyondan önce ön-uçuş** | IBKR, ALP | "Bu emri gönderirsem ne olur?" | IBKR Preview / Check Margin Impact; API tarafında `Order.WhatIf = true` → "instead of sending the order … it will undergo a credit check for the expected post-trade margin requirement" · ALP `alpaca order submit --dry-run` | Geri alınamaz eylemin maliyetini **önce** gösterir |
| Frenin **nerede** durduğunu bilme (bot mu borsa mı) | FT | "Bot ölürse stop'um yine çalışır mı?" | `stoploss` vs `stoploss_on_exchange` — borsa tarafı "no potential network overhead"; ama "Do not set too low/tight stoploss … greater risk of missing fill" | Tek nokta arıza; "koruma vardı sandım" |
| Portföy düzeyinde risk okuma | IBKR | "Toplam maruziyetim ne?" | Risk Navigator: Risk Dashboard, Report Viewer, **Portfolio Relative P&L Graph** ("değerin, dayanak fiyatındaki yüzde değişimlere göre nasıl değişeceği") | Pozisyon-bazlı bakıştan portföy-bazlı bakışa geçiş |

## A.7 — Bildirim ve uzaktan gözetim

| iş | platform(lar) | operatörün cevapladığı soru | tipik biçim | neyi çözüyor |
|---|---|---|---|---|
| Panoya bakmadan olay bazlı haber alma | QC, TV, FT | "Bir şey olduğunda bana haber verilsin" | QC: Email (10 KB) / SMS (1600 kr.) / Telegram / **Webhook**; olaylar yalnız **Order Events** ve **Insights** (hata/durma bu listede **yok**) · TV: Strategy Alerts → "Order fills and alert() function calls", **geçmiş barlar için bildirim gönderilmez**, webhook 2FA zorunlu · FT: Telegram komut seti + WebSocket akışı | Sürekli izleme yükünü kaldırır — ama kapsamın sınırı beyanlıdır |
| Terminal/SSH olmadan hata avı | FT, HB, QC | "Bir şey ters gitti, log ne diyor?" | FT `/logs [limit]` · HB Log Pane (Ctrl+T) + `hbot logs` · QC **Logs** sekmesi: "Filter logs" araması + tam dosya indirme (yeniden dağıtımdan sonra korunur), log kotası var, `if (LiveMode)` ile koşullu loglama öneriliyor | Operatör sürtünmesi + teşhis erişimi |
| Yeniden başlatmadan ayar tazeleme | FT | "Config'i değiştirdim, süreci öldürmeden uygulanır mı?" | `/reload_config` | Yeniden başlatmanın pozisyon/emir durumunu bozma riski |

## A.8 — Kanıtı dışarı çıkarma

| iş | platform(lar) | operatörün cevapladığı soru | tipik biçim | neyi çözüyor |
|---|---|---|---|---|
| Ham kaydı indirip bağımsız doğrulama | QC | "Bu veriyi kendi hesabımla çapraz kontrol edebilir miyim?" | Orders → **CSV**; Insights → **JSON**; Logs → tam dosya | Panonun görsel yorumuna bağımlılığı kırar |
| Canlı sonucu araştırma ortamına çekme | QC | "Yeniden dağıtımlar arası tarihçeyi birleştirebilir miyim?" | Research Environment **Live Analysis**: `ReadLiveAlgorithm`, `ReadLiveOrders` (sayfalamalı); **her dolum olayı kendi deployment Id'sini taşır** | Restart'ların böldüğü tarihçeyi tek defterde birleştirir |
| Geçmiş koşuları sorgulama | HB | "Kapattığım botun kayıtları nerede?" | `/archived-bots` router: arşiv veritabanları, trades, orders, executor kayıtları | Kanıt sürekliliği |

## A.9 — Evren, envanter ve filo

| iş | platform(lar) | operatörün cevapladığı soru | tipik biçim | neyi çözüyor |
|---|---|---|---|---|
| Evrenin ne olduğunu ve **neden** o olduğunu doğrulama | FT | "Bot şu an neyi tarıyor?" | `/whitelist [sorted] [baseonly]`, `/blacklist`; CLI `test-pairlist` ("test the configuration of dynamic pairlists") | Dinamik listenin evreni **sessizce** daraltması |
| Stratejinin dönem dönem **neyi tuttuğunu** görme | CMP | "Sonucu hangi varlık üretti?" | **Historical Allocations** tablosu + grafiği; aynı tablo backtest'te **kaç gün işlem yapılacağını** da gösterir | "İyi backtest" ile "tek varlığın şansı"nı ayırır; sürtünme maliyetini seçimden **önce** görünür kılar |
| Yeniden dengeleme tetikleyicisini seçme | CMP | "Her gün mü, sapınca mı?" | **Calendar** (günlük: 51/49 olsa bile 50/50'ye döner) vs **Threshold** (drift eşiği; %10'da 60/40 aşılana dek işlem yok) | Gereksiz işlem (ücret+slippage) ile hedeften sapma arasındaki takası operatöre bırakır |
| İcra penceresini ve gecikmeyi bilme | CMP | "Şimdi mi olacak, yarın mı?" | Trading period **15:45–16:00 ET** (erken kapanışta 12:45–13:00); değişiklikler **bir sonraki** periyotta icra edilir; emirler **"not held"** (fiyat takdiri platformda) | "Neden hâlâ işlem görmedi" sorusunu ortadan kaldırır |
| Filo görünümü | FT, HB | "N botum var, hangisi kaybediyor?" | FreqUI Dashboard (çoklu bot API'sinden birleşik metrik) · HB Instances: Net PNL (quote/%), Volume Traded, Liquidity Placed, Unrealized PNL, Imbalance | Çoklu-örnek kör noktası |

## A.10 — AJAN GÖZLEMLENEBİLİRLİĞİ (LangSmith · Langfuse · AgentOps · W&B Weave · OTel GenAI)

**Bu aile Meridian'a en yakın olanıdır** ve etüdün asıl bulgusu buradan çıkıyor: Meridian bir
*trading* ürünü olduğu kadar bir **ajan gözetim** ürünüdür, ve trading panolarının hiç sormadığı
soruları bu hat soruyor.

| iş | platform(lar) | operatörün cevapladığı soru | tipik biçim | neyi çözüyor |
|---|---|---|---|---|
| **Tek bir kararı adım adım geri sarma** | LangSmith, Langfuse | "Dün gece verilen karar hangi girdilerden, hangi ara adımlardan geçti?" | İç içe koşu ağacı (trace = run kümesi; run ≈ OTel span); her adımın girdi/çıktısı ve zamanlaması açılır | Kararı "kutu çıktısı" olmaktan çıkarıp denetlenebilir zincire çevirir |
| Ajanın izlediği **yolu graf** olarak görme | Langfuse | "Ajan hangi düğümlerden geçti, nerede döngüye girdi?" | Agent graph — **Aggregated** (tekrar eden adım tek düğüm + sayaç, ör. `retrieve_docs (3/3)`, döngü kenarı) ↔ **Expanded** (her çağrı ayrı düğüm, döngü açılmış DAG) | "Yapı nasıl" ile "bu koşuda ne oldu"yu ayrı ayrı yanıtlar |
| Çok turlu bir oturumun tamamını tek akış olarak oynatma | LangSmith (Threads), Langfuse (Sessions) | "Bu koşu dizisinin bütünü nasıl gelişti?" | `sessionId` ile trace'ler birleşir; Messages / Turns / Details görünümleri | Tekil trace'in kaçırdığı bağlamı (önceki turların etkisi) geri verir |
| **Arızalı koşuları hedefli filtreyle bulma** | LangSmith | "Şu araç çağrısının hata verdiği koşuları nasıl bulurum?" | Filtre + tam-metin arama (ad, tip, metadata, tag, feedback, girdi/çıktı anahtar-değer, alt-koşu yol ifadesi ör. `generations.message.kwargs.tool_calls.name`) + **kaydedilebilir görünümler** | Binlerce koşuda iğneyi bulur; tekrar eden triyajı kaydedilmiş görünüme dönüştürür |
| **Token ve maliyet muhasebesini atfedilebilir kılma** | Langfuse, LangSmith | "Bu ay parayı ne yedi; hangi oturum/etiket?" | Usage type kovaları (`input`, `output`, `cached_tokens`, …); **ingested > inferred** önceliği; özel/kademeli model fiyatı; kullanıcı/tag kırılımı | "Model faturası" tek rakam olmaktan çıkıp **atfedilebilir** hale gelir |
| Latency dağılımını ve darboğazı ölçme | LangSmith | "Yavaşlık nerede: ilk token mı, araç mı, toplam mı?" | p50/p99 + ortalama; time-to-first-token; koşu-tipi kırılımı | "Yavaş" şikayetini ölçülebilir aşamaya indirger |
| Satıcı-bağımsız telemetri sözleşmesine oturma | OTel GenAI semconv | "Ölçümüm bir araca kilitli mi?" | `gen_ai.operation.name` ∈ {chat, embeddings, retrieval, execute_tool, invoke_agent, invoke_workflow, plan, …}; zorunlu `gen_ai.provider.name` + koşullu `error.type`; `gen_ai.usage.input_tokens/output_tokens`, `gen_ai.conversation.id`, `gen_ai.agent.name`, `gen_ai.tool.name` | Kelime dağarcığını standartlaştırır; araç değişse de ölçümün anlamı korunur |
| Ajan-özgü sayaçları **metrik** olarak izleme | OTel GenAI semconv | "Bir ajan koşusu kaç çıkarım, kaç araç çağrısı harcıyor?" | Histogramlar: `gen_ai.client.token.usage`, `gen_ai.client.operation.duration`, `gen_ai.invoke_agent.duration`, `gen_ai.invoke_agent.inference_calls`, `gen_ai.invoke_agent.tool_calls`, `gen_ai.execute_tool.duration` | "Ajan pahalı" iddiasını çağrı-sayımına indirger |
| **Yinelenen arızaları taksonomiye kümeleme** | LangSmith Engine | "Bu hafta hangi arıza sınıfı tekrarlıyor ve neden?" | 6 saatte bir otomatik tarama; kategori etiketli sorunlar (ör. "Silent tool error", "Hallucination"); her soruna katkı veren trace'ler + önerilen düzeltme | Tekil hata avcılığını **sınıf avına** çevirir |
| Üretim trafiğini örneklemle otomatik puanlama | LangSmith, Langfuse | "Canlı kalite bozuldu mu — insan beklemeden?" | Filtre + **örnekleme oranı** (ör. 0.1) + judge prompt; skor trace'e feedback olarak iliştirilir; değerlendirmenin kendisi de trace'lenir | Sürekli kalite ölçümünü insan kapasitesinden bağımsızlaştırır |
| **İnsan incelemesi kuyruğunu rubrikle işletme** | LangSmith | "Hangi çıktılar insan gözü bekliyor, ne kadar kaldı?" | Annotation queue: talimat + feedback key'leri (rubrik); durum akışı **Needs Review → Needs Others' Review → Completed** | İnsan onayını ad-hoc yorumdan çıkarıp **sayılabilir kuyruğa** alır |
| **Arızayı kalıcı regresyon testine sabitleme** | LangSmith, Langfuse | "Yanlış çıktıyı düzeltip bir daha bozulmasın diye sabitleyebilir miyim?" | İnceleme ekranında girdi/çıktı düzenleme + "Add to Dataset"; beklenen-çıktı eklenmiş üretim trace'i dataset item olur | Arızayı tek seferlik hatadan **kalıcı teste** çevirir |
| Kuralla otomatik triyaj kurma | LangSmith (Rules) | "Negatif geri bildirim alan her koşu otomatik incelemeye düşsün" | Rule = filtre + örnekleme oranı + eylem zinciri (kuyruğa ekle · dataset'e ekle · webhook · değerlendirici koştur · saklamayı uzat) | Elle triyajı yönetmeliğe çevirir |
| **Yeni sürümün eskisinden iyi olduğunu örnek düzeyinde kanıtlama** | LangSmith | "Bu değişiklik neyi düzeltti, **neyi bozdu**?" | Deney karşılaştırma: ≥2 experiment; feedback key başına **kırmızı = regresyon / yeşil = iyileşme**; örnek-başına detay + yan yana trace; JSON/YAML diff; baseline seçimi; "higher is better" yönü | "Daha iyi oldu" iddiasını **örnek düzeyinde** kanıta bağlar — toplam skorun gizlediği regresyonu açar |
| Regresyonda dağıtımı durdurma | Langfuse | "Bozan değişiklik canlıya çıkmasın" | Dataset + experiment koşusu CI/CD'ye bağlanır; regresyonda dağıtım bloklanır | Ölçümü **kapıya** dönüştürür |
| Prompt sürümünü yönetme ve geri alma | LangSmith, Langfuse | "Hangi sürüm canlıda, öncekine dönebilir miyim?" | Commit hash'li sürüm geçmişi + taşınabilir etiketler (`staging`, `production`); `pull_prompt("name:hash")`; sürüm-başına trace performansı | Prompt değişimini kod dağıtımından ayırırken izlenebilirliği korur |
| Üretim trace'ini **farklı model/prompt ile yeniden koşturma** | W&B Weave | "Aynı girdiyle başka model ne yapardı?" | Playground: "test new LLMs and custom models against production traces" | Karşı-olgusal denemeyi canlıya dokunmadan yapar |
| Eşik aşımında uyarı alma, **iki kademeli** | LangSmith, Langfuse | "Bozulma olduğunda beni kim uyandırıyor?" | LangSmith 5 alarm tipi (Run Count, Cost, Errors, Feedback Score, Latency) × agregasyon × 5/15 dk pencere · Langfuse **Warning + Alert** iki eşik, OK→WARNING→ALERT→**NO_DATA** geçişleri | Gözetimi "birinin bakması"na bağlı olmaktan çıkarır; **NO_DATA'yı ayrı bir hal sayar** |
| Ajan koşusunu insan onayında **duraklatıp** onayla/düzelt/reddet | LangChain HITL | "Riskli aracı çalıştırmadan önce insan onayı alabilir miyim?" | `interrupt_on` ile duracak araçlar; karar tipleri **approve / edit / reject / respond**; durum checkpointer ile **kalıcı**; `__interrupt__` alanında `value`, `resumable`; `Command(resume=…)` ile devam | "Ajan kendi başına icra etti" riskini kapıya bağlar; **duraklatılmış koşu kaybolmaz** |
| Oturum şelalesiyle zaman-tabanlı teşhis | AgentOps | "Hangi adım ne kadar sürdü, hata nerede patladı?" | Session Waterfall: LLM çağrıları, Action, Tool ve **Errors** zaman ekseninde; event-tipi kırılımı; oturumlar arası karşılaştırma | Adım süreleri ve hata konumunu tek görselde birleştirir |
| **Ölçümün sessizce kopmasını önleme** | Langfuse (best practices) | "Trace'lerim gerçekten okunabilir mi?" | İyi-trace sözleşmesi: araç çağrıları çağıran span'in altında; doğru observation tipi; HTTP/DB gürültüsü dışarıda; **kararlı isimler** — isim değişince "evaluators, dashboard queries, and saved filters … silently stop matching" | **Sessiz ölçüm kopması** (isim kayması) — Meridian'ın YASA 6 / artefakt-graf disipliniyle aynı sınıf |

## A.11 — Numerai (uzaktan bir tahmin modelini izleyen operatör)

| iş | operatörün cevapladığı soru | tipik biçim | neyi çözüyor |
|---|---|---|---|
| Gönderimi **statü zinciriyle** takip etme | "Bugünkü tahminim gerçekten gitti mi?" | 6 durumlu rozet: Pending → Running → Validating → Success; arıza tarafı Error / Failed (neden ayrıştırılır: sürüm uyuşmazlığı, timeout) | Sessiz gönderim kaybını görünür kılar |
| Otomatik koşunun **kaynak bütçesi** içinde kaldığını doğrulama | "Model zaman/bellek limitine mi çarptı?" | Koşu logu + sabit kota beyanı (1 CPU, 4 GB RAM, ≤10 dk) | Aralıklı arızayı "model kötü" değil "bütçe aşımı" olarak ayırır |
| **Skorun olgunlaşma eğrisini** izleme | "Bugünkü skor nihai mi, yoksa henüz erken mi?" | 20 adımlı zaman serisi: ilk skor tur kapandıktan **4 gün** sonra, final ~1 ay sonra | **Yarım-pişmiş skora bakıp karar vermeyi engeller** |
| Katkıyı korelasyondan ayırma | "İyi skorum kendi katkım mı, herkesin bildiğini mi tekrarlıyorum?" | İki ayrı seri: **CORR** (hedefle korelasyon) ve **MMC** (Meta Model'e katkı) | Ölçüyü "doğru mu" ile "eklediği bilgi var mı" olarak ikiye böler |
| Risk altındaki sermayeyi ve **kayıp tavanını** önden görme | "Bu tur en kötü ihtimalle ne kaybederim?" | `payout = stake × clip(payout_factor × score, −0.05, +0.05)`; `payout_factor = min(1, 72.000 / total_at_risk)` | Kayıp tavanını ve sistem-genişliğinde seyrelmeyi açık eder |
| Stake etmeden önce **doğrulama teşhisini** koşma | "Bu sinyal riske değer mi?" | Teşhis çalıştırma (5–10 dk) → performans/risk/potansiyel kazanç tablosu; "geçmişte iyi = gelecekte iyi değil" uyarısıyla birlikte | Canlı riski almadan ön-kontrol |
| Gönderim penceresini kaçırmanın sonucunu bilme | "Geç gönderdim; skorlanır mı?" | Pencere takvimi + kural: geç gönderim **skorlanır ama stake edilemez** ve Meta Model'e girmez | Kısmi başarısızlığı tam başarısızlıktan ayırır |

## A.12 — eToro copy-trading (ayrıştırılmış: gerçek gözetim işi ↔ katılım mühendisliği)

**Gerçek gözetim işleri** (Meridian'a taşınabilir sınıf):

| iş | operatörün cevapladığı soru | tipik biçim | neyi çözüyor |
|---|---|---|---|
| **Önceden konan kesme eşiği** | "Bu ne kadar düşerse bütünüyle kapansın?" | Copy Stop Loss: varsayılan yatırılanın %40'ı, %5–%95 arasında elle ayarlanır; sonradan değiştirilebilir | Tek bir kolun hesabı sürüklemesini **operatörün önceden** koyduğu tavanla sınırlar |
| **Ara kademe: duraklat** | "Kapatmadan yeni işlem almayı kesebilir miyim?" | "Pause Copy": yeni işlem açılmaz, mevcutlar SL/TP'yi izlemeye devam eder | "Ya hep ya hiç" ikilemini kırar |
| **Çıkışta pozisyonların kaderini seçme** | "Kapatırken satayım mı, devralayım mı?" | İki seçenekli çıkış: "Sell All" / "Keep All" | Çıkışın kendisini bir risk olayı olmaktan çıkarır |
| Gecikmeyi ve yeniden dengelemeyi beyan etme | "Param ne zaman dağılacak?" | Yatırımlarda 48 saat gecikme; yeniden dengeleme "7 iş gününe kadar"; min $200/trader, min $1/pozisyon | Gizli/gecikmeli yeniden dağıtımı görünür kılar |
| Sistemin **sınırlarını** okuma | "Bu korumalara ne kadar güvenebilirim?" | Risk uyarısı: emirler garantili değil, **CSL dahil**; kopyalanan tutarı aşan kayıplar mümkün | Yanlış güvenlik hissini kırar |

**Katılım mühendisliği** (gözetim DEĞİL — anti-referans; Bölüm B'de topluca reddedilir): tier
merdiveni (Cadet → Champion → Elite → Elite Pro) · tier'a bağlı rozetler ve kulüp yükseltmeleri ·
takipçi sayısı teşhiri · **ödeme için zorunlu içerik üretimi** (aylık ≥1 adet 100+ kelimelik
gönderi) · keşif sıralamasının "engagement metrics"e bağlanması · AUC üzerinden ödeme (kopyacı
toplamak doğrudan gelir) · strateji sohbeti.

---

# BÖLÜM B — MERİDİAN'A EŞLEME

Sütunlar: **(1)** veri var mı (uç/alan adıyla; yoksa "veri yok") · **(2)** bugün karşılanıyor mu,
hangi yüzeyde · **(3)** hüküm.

## B.0 — ÖNCE ELENENLER: yasaya aykırı desenler

Kategoride yaygın ama Meridian'ın yazılı bir yasasını çiğneyen **on desen sınıfı** reddedildi.
Bunlar Bölüm C'ye hiç girmez.

| # | Desen | Kategoride nerede (kanıt) | Çiğnediği yasa | Not |
|---|---|---|---|---|
| R1 | **Manuel emir girişi / one-click trade** | ALP panosunda "Trade" paneli (sembol·adet·tip·TIF) ve pozisyon satırında "Liquidate" · TV chart trading + DOM + order ticket (üç ayrı hızlı emir yüzeyi) · FT `/forcelong` `/forceshort` `/forceenter` `/forceexit` + REST `POST /forceenter` · HB `POST /trading/orders`, Gateway `swap` · IBKR Transmit / Order Ticket / ChartTrader / BookTrader · CMP "Invest" | **TEK EMİR-YOLU** (PRODUCT.md "**No manual order entry** (operator decision 2026-08-06)"; DESIGN.md "A second order path is forbidden by construction — E1 two-engine law: both engines read `broker.entry_law()`") | Yeni modül olsa bile yasak. **Karışmasın:** Meridian'ın `Flatten`/`close_all` bir ÇIKIŞ/panik kontrolüdür (giriş yolu değil) ve onay jetonu yoksa yalnız kuru-koşu raporlar (api.py:2965); `submit_armed` kendi mantığını kurmaz, `loop.mirror_submit_armed`e delege eder (api.py:2913, C8 denetimi) |
| R2 | **Liderlik tablosu / yarışma / rozet / tier merdiveni** | QC **Quant League** — yalnız ilk 20 görünen leaderboard + "Winner's Circle" · TV **The Leap** — leaderboard + "real cash, special prizes, and **bragging rights**" (TradeStation edisyonunda toplam $50.000; ADX edisyonunda MacBook Pro 16"/Longines/Rimowa) · Numerai leaderboard, dokümanın kendi ifadesiyle "mainly for bragging rights" + **Grandmasters tier** (yükseldikçe model slotu artar) · eToro Cadet→Champion→Elite→Elite Pro + Blue Badge + Club yükseltmeleri | **DOPAMİN YASAĞI** (DESIGN.md "Forbidden: … celebratory motion, sound, **gamification of any kind**"; "no-dopamine rule" bağlayıcı) | Tek operatörlü bir sistemde liderlik tablosunun paydası zaten yok; asıl sorun ödül-döngüsünün ölçümün yerine geçmesi |
| R3 | **Sosyal kopyalama / strateji vitrini** | eToro CopyTrader'ın tamamı · CMP **Symphony Database** — OOS Cumulative/Annualized Return, OOS Sharpe, OOS Max Drawdown, OOS Calmar sütunlarıyla **sıralanabilir** binlerce strateji + API'de symphony **copying** ucu + Discover akışı · QC league girdisini kendi hesabına klonlayıp canlıya alma | PRODUCT.md "**Not multi-tenant**; no external investors, clients, or team members view this system" + R2 | Vitrin, sıralanabilir bir liderlik tablosunun kılık değiştirmiş hâli |
| R4 | **Gerçek-para iması (bugün L0 kâğıt)** | CMP "Watch" (simüle $1000) ile "Invest" (gerçek sermaye) **aynı yüzeyde yan yana** · ALP paper/live **tek dropdown** arkasında · TV Strategy Tester varsayılan initial capital **1.000.000** ve rapor metriklerinin yanında "hipotetik" etiketi dokümante **değil** · TV The Leap sanal işlemi **gerçek nakitle** ödüllendiriyor · HB kâğıt bakiyeleri 1 BTC / 100.000 USDT / 10.000.000 HBOT · Numerai NMR stake + negatif skorda **burn** | PRODUCT.md L0 kâğıt + "not financial advice"; otonomi merdiveni **ajan tarafından çevrilemez** | Meridian'ın karşı-deseni zaten yerinde: `sermaye_koken` bloğu parayı gerçek-canlı / antrenman-tohumu diye ayırıyor (api.py:1089–1100) |
| R5 | **Kanıt kaydını silme yolu** | FT `/delete <trade_id>` = "Delete a specific trade from the Database"; REST `DELETE /trades/<tradeid>` | PRODUCT.md "approval is recorded as an *event* (**verdicts are never rewritten**)"; alarm ACK'i "hiçbir alarmı SİLMEZ" (api.py:1688) | Operatöre defter budama yetkisi verilmez; `watchdog.grant_amnesty` bile afı **görünür** bırakır (`amnestied` alanı) |
| R6 | **Gauge / donut / pie** | LangSmith pano seçenekleri: "line charts, stacked bars, KPIs, ranked bars, **donuts**, and tables" · Langfuse özel panolarda "**Pie charts** (proportional data)" | DESIGN.md "**Charts: bars and bullet graphs. Radial gauges, donuts and pie charts are forbidden.**" | Meridian bunu WP-P/P3'te zaten söktü (2 gauge → bullet-graph + gömülü trend + beklenen-aralık bandı) |
| R7 | **Rengin tek anlam kanalı olması** | IBKR emir durumu **11 renkle** kodlanıyor (light gray / light blue / pale purple / purple / dark blue / green / dark green / light green / pink / orange / red / maroon); metin etiketi eşliği dokümante değil — pale purple↔purple ve dark↔light green ayrımı renk-körü okuyucuda riskli | DESIGN.md beş renk rolü + CVD-güvenli + yön "always the **third** signal after sign and arrow"; "colour appears only on anomaly/significance" | Durum sözlüğünün kendisi (R7'nin taşıdığı bilgi) değerli — reddedilen **kodlama**, bilgi değil |
| R8 | **Ölçülmemişi ölçülmüş gibi sunma (örneklem paydasının gizlenmesi)** | LangSmith/Langfuse online eval'de örnekleme oranı (ör. **0.1**) skorun tüm trafiği temsil etmediği anlamına gelir; oran panoda gösterilmezse "ölçüldü" izlenimi yanıltıcıdır | **UYDURMA YASAĞI** + "evidence bars carry a **declared denominator** or are not drawn" (PRODUCT.md) | **Koşullu ret:** desenin kendisi (örneklemli otomatik puanlama) alınabilir, ama payda beyanı zorunlu. Meridian'ın `ledger{plans_total, plans_shown, cap}` ve `sieve` künyesi tam olarak bu disiplindir |
| R9 | **Ajanın kendi düzeltmesini önerip uygulaması** | LangSmith Engine yalnız teşhis vermiyor: "**proposed code fixes**" + otomatik üretilmiş değerlendirici sunuyor | NOUS **Katman D anayasal çekirdek KAPALIDIR** — "hakim kendi yasasına dokunamaz" (CORE_FILES/CORE_CONCEPTS, `CekirdekIhlali` + AUTHORITY_CHANGE alarmı, AST çivisi); ajan kendi skill'ini terfi ettiremez | **Koşullu:** öneri ÜRETMEK zaten var ve serbest (`nous_fisler` fiş kuyruğu, `improvement_proposals`); yasak olan **uygulamak** ve **değerlendiricinin kendisini** ajana yazdırmak |
| R10 | **Elle düzenlenen izleme listesi (ikinci evren yasası)** | ALP panosunda düzenlenebilir Watchlist | Yasa değil ama **tek-evren** disiplini: evren `state/bounds.yaml` + evren kararıyla belirlenir (canlıda 251 sembol, `RETIRED_SYMBOLS` emeklilik kaydı) | Elle liste, kapının paydasıyla panonun paydasını ayrıştırırdı — Meridian'ın tekrar eden kusur sınıfı |

**Elenen desen sınıfı: 10.** Bunların **9'u** yazılı bir yasayı çiğniyor (R1–R9); ikisi (**R8, R9**)
**koşullu ret** — çekirdek fikir payda ya da yetki beyanıyla alınabilir. **R10 bir yasa ihlali değil**,
tek-evren disiplininin ihlali; ayrı işaretlendi.

## B.1 — Hayatta kalma ve süreç sağlığı

| iş (Bölüm A) | (1) Veri var mı | (2) Bugün karşılanıyor mu | (3) HÜKÜM |
|---|---|---|---|
| Döngünün hâlâ döndüğünü doğrulama | `/api/today` → `heartbeat`, `heartbeat_age_seconds`, `stale`; `/api/diagnostics` → `scheduler{last_tick,poll_seconds,cycles}`, `sessiz_hat` (17 bekçi) | Evet — üst bar durum hapı + her sayfada sabit sessiz hat; sağlıklıyken tek sönük satır, renk yalnız sapmada | **zaten var, biçim açık** |
| Kesinti anını **getiriyle aynı eksende** görme (QC "Meta" serisi) | Kısmen: `equity_curve.points` + `events.jsonl` (restart/halt/breaker olayları ayrı defterde) | Hayır — eğri ve olaylar ayrı yüzeylerde; eğrinin üstünde dağıtım/durma damgası yok | **veri var ama gösterilmiyor — FIRSAT** |
| Karar üretiminin sürdüğünü **emirden bağımsız** doğrulama | `/api/today` → `son_dongu{candidates, plans, armed, yas_saat}`; `/api/signals` → `latest_signal_date` | Evet — "Dün gece" kartı (aday·plan·silahlı + yaş); `son_dongu` olay penceresinden bağımsız okunuyor (api.py:975–1051) | **zaten var, biçim açık** |
| Kesintiye dayanıklılığı önceden ayarlama (QC: ≤5 restart, ≥5 dk koşmuşsa) | Kısmen: `MERIDIAN_SUPERVISED` + `ops/com.meridian.agent.plist` LaunchAgent; restart politikası **systemd/launchd** katmanında | Panoda restart politikası (kaç kez, hangi koşulla) **gösterilmiyor**; restart olayları `events.jsonl`de | **veri var ama gösterilmiyor — FIRSAT** (düşük öncelik: politika kodda sabit, operatör RUNBOOK'tan okuyor) |
| Kurulum mu strateji mi bozuk ayrımı (HB `doctor`) | `/api/diagnostics` → `integrity`, `coverage`, `pipeline`, `saglayicilar`, `hotstate`, `marketstream`, `barfeed`, `ledger_contract` | Evet — Veri Sağlığı sayfası + sessiz hat; sağlayıcı/akış/defter katmanları ayrı ayrı | **zaten var, biçim açık** |

## B.2 — Mod ve kimlik dürüstlüğü

| iş | (1) Veri var mı | (2) Bugün karşılanıyor mu | (3) HÜKÜM |
|---|---|---|---|
| Kâğıt mı gerçek mi | `/api/today` → `mode`, `autonomy_level`, `broker`; `/api/alpaca` → `paper_available` | Evet — HUD çipi + `broker` alanı ("Alpaca · paper"). **DESIGN.md ayrıca borç yazıyor:** L1'e geçildiğinde köşe rozeti değil **yapısal** bir işlem taşımalı ("Mode must be legible from any pixel") | **zaten var, biçim açık** (L1 borcu tasarım turunun konusu, veri değil) |
| Kâğıdın **nerede yalan söylediğini** bilme | Kısmen: `cf_fidelity` (sim↔gerçek `corr`, `mean_diff_r`, `n`, `fidelity_ok`) panoda; `icra.kotumser_band` (`ampirik_bps`, None ise "ölçüm yok"); `counterfactual.advance` docstring'inde motor sınırı yazılı; ROADMAP §4'te cf sadakat sınırı beyanlı (trail/BE/chandelier/giveback/regime_flip/scale_out ve komisyon/ADV/impact **simüle EDİLMİYOR**) | Kısmen — sadakat **sayısı** panoda, sadakatin **sınır listesi** panoda değil (ROADMAP'te ve docstring'de) | **veri var ama gösterilmiyor — FIRSAT** (ALP'nin `borrow fees "Coming Soon!"` ve TV'nin non-standard-grafik uyarısıyla aynı sınıf: simülasyonun eksiğini ekranda beyan etmek) |
| Panodaki sonucun hangi koda ait olduğu (QC Code sekmesi) | `/api/summary` → `strategy_version`; `scoreboard.current_version`; `trades.strategy_version`, `trade_plans.strategy_version` | Evet — sürüm zaman çizelgesi (app.js:5535) + satır bazında sürüm damgası | **zaten var, biçim açık** |
| Emri kimin koyduğunu ayırma (IBKR `clientId`) | `loop.mirror_submit_armed(source=…)` — panodan gelen gönderim `source="pano"` ile damgalanıyor (api.py:2948); `obs.log("alpaca_submit_armed_endpoint", …)`; `scheduler_advance_manual` olayı | Kısmen — damga defterde, panoda "bunu zamanlayıcı mı ben mi tetikledim" ayrımı gösterilmiyor | **veri var ama gösterilmiyor — FIRSAT** |
| Botun hangi kimlikle bağlandığı | `/api/secrets` → hangi anahtar set, kaynağı, maskeli ipucu (tam değer asla dönmez); `/api/secrets/test/{provider}` | Evet — Kilitler & Yapılandırma → ayarlar | **zaten var, biçim açık** |

## B.3 — Karar zincirinin denetimi

| iş | (1) Veri var mı | (2) Bugün karşılanıyor mu | (3) HÜKÜM |
|---|---|---|---|
| Sinyal → emir → dolum zincirini uçtan uca denetleme | `portfolio.armed` + `portfolio.alpaca_submitted` + `mirror_orders.json` (coid başına `status`, `event`, `filled_qty`, **`filled_avg_price`**, `order_id`, `updated`) + `trades.plan_id` | **Kısmen — yalnız TOPLAM huni** ("silahlı → gönderilmiş → dolan", app.js:1749–1789; üç basamağın paydası ayrı olduğu beyanlı). Tek bir planın kendi emir kimliğine, durumuna ve **gerçekleşen dolum fiyatına** giden bir iz **yok**; `mirror_orders.json` yalnız `_stream_view` (akış sağlığı) için okunuyor (api.py:2271) | **veri var ama gösterilmiyor — FIRSAT** ⭐ (top-task ② doğrudan) |
| "Neden çalışmıyor" ayrımı (IBKR durum sözlüğü + `whyHeld`) | `reconcile.failed_submissions` (açık/ACK'li ayrık — `health.split_rejections`), `broker_rejected`, `armed[].broker_status`, `mirror_orders[].status/event` | Kısmen — açık broker reddi sayısı ve "gönderilecekte kaldı" uyarısı emir kartında; **reddin nedeni** yapılandırılmış bir sözlüğe bağlı değil | **veri var ama gösterilmiyor — FIRSAT** |
| **Eylemsizliğin nedenini görünür kılma** (FT `locks.reason`, CMP "neden nakit tutuyor") | `verdict_counts`, `gate_reasons[]`, `gate_checks[{check,passed,severity,value,threshold,note}]`, `regime.exposure_budget_pct`, `blackout_radar`, `halted`, `learn_halted`, `data_ok`, `session_deferred_for_coverage` olayı, `dormant_setup`, `scan_debt` | **Kısmen** — plan varsa çekmecede tam karar ağacı okunuyor (RECORD_VIEW.plan, app.js:6032–6038). Plan **yoksa** pano "bu seansta tarama adayı yok — huninin paydası kurulamadı" (app.js:2142) diyor: dürüst ama **nedensiz**. Girdilerin hepsi elde | **veri var ama gösterilmiyor — FIRSAT** ⭐ |
| Kapasite/doygunluk (FT `/count`) | `gate_checks` içinde `max_open_positions` (value/threshold `<5`), `sector_cap`, `exposure_budget`, `position_size`; `current_exposure_pct`; `portfolio_heat` | Kısmen — eşikler plan çekmecesinde; "şu an kaç slot boş" başlı başına bir gösterge değil | **veri var ama gösterilmiyor — FIRSAT** (düşük öncelik: `gate_checks` zaten cevabı taşıyor) |
| Uzun soluklu icranın ilerlemesi (IBKR A/D) | `reconcile.partial_fills[{ticker, coid, filled_qty, total_qty, fill_pct, realized_risk_r, open_risk_r}]` | Evet — mutabakat bölümünde | **zaten var, biçim açık** |
| Tek işlemi emir düzeyine kadar açma | `/api/trade/{id}` → tam kayıt + son 60 bar OHLC; `hwm_pairs` (iç trail ↔ Alpaca'ya giden son PATCH + `desync` bayrağı) | Evet — işlem çekmecesi + mutabakat | **zaten var, biçim açık** |

## B.4 — İcra kalitesi ve simülasyon-gerçek boşluğu

| iş | (1) Veri var mı | (2) Bugün karşılanıyor mu | (3) HÜKÜM |
|---|---|---|---|
| **Canlı-backtest sapmasının kökünü adlandırma** (QC reconciliation'ın kapalı neden listesi) | Girdi var: `icra.slipaj` (`entry_execution_summary` — gönderim/ret/veto, ret nedeni dağılımı, iki bps dağılımı, iki-motor mutabakatı), `cf_fidelity`, `slippage_measured`, `mirror_orders.filled_avg_price`, `trade_plans.entry_trigger`, bar verisi; ROADMAP §4'te replay iyimserliği **ölçülmüş** (~+0.018 motor sapması) | Kısmen — sapma **büyüklüğü** ölçülüyor ve gösteriliyor; **adlandırılmış neden sınıflandırması** (dolum zamanlaması / açılış-kapanış açık artırması / yuvarlama / split / restart) yok | **veri var ama gösterilmiyor — FIRSAT** |
| Fill'i fiyat + maliyetle denetleme | `trades.costs`, `trades.entry/exit`, `slippage_measured`, `icra.kotumser_band` | Evet — performans ve icra bölümleri | **zaten var, biçim açık** |
| Bar-içi dolum varsayımını sınama (TV Bar Magnifier) | Yok — `counterfactual.advance` günlük barla ilerliyor; alt zaman dilimi replay'i yok (intraday hattı ayrı: `barfeed`, `intraday_decisions.jsonl` gözlem modunda) | Hayır | **veri yok — YENİ MODÜL ADAYI** · (a) günlük-bar dolum varsayımını daha ince bar'la yeniden koşup farkı raporlar · (b) intraday bar hattı kısmen var ama tarihsel derinlik dış kaynak ister (Massive plan) · (c) **L** · **kart ZORUNLU** (dolum varsayımı değişirse kenar iddiası değişir) |
| Ölçüm koşullarını görünür kılma (TV Properties) | `state/bounds.yaml` (parametre kumbarası) + `state/goal.yaml` (başarı/risk sözleşmesi) — **ajanın asla düzenleyemediği** iki dosya; `scoreboard.versions[].params`; `guard.py` kilit listesi | Evet — Kilitler sayfası; PRODUCT.md bunların insan-sahipli olduğunun UI'da okunur olmasını istiyor | **zaten var, biçim açık** |
| Yapısal olarak geçersiz ölçüm rejimini adlandırma (TV non-standard grafik uyarısı) | `_kaynak`/`sieve.provenance` künyesi (`source:"yalnız-simüle"`, `n_real`, `n_cf`, `stages`), `ledger_source` (ledgerstamp), `holdout_note`, `defter` sayımları (gerçek-canlı vs replay tohumu) | Evet — provenance rozetleri + "gerçek/sim" çipleri (app.js:4012); `sermaye_koken` tohum etkisini ayırıyor | **zaten var, biçim açık** — kategoride Meridian'ın **önde** olduğu yer |
| Örneklem derinliğini açarken bedelini beyan etme | `ledger{plans_total: 390, plans_shown: 120, cap}`, `MAX_OPEN=2500` cf tavanı, `_SON_DONGU_KUYRUK` okuma penceresi | Kısmen — kırpma **beyan ediliyor** (2026-07-22 düzeltmesi) ama kırpılanı görmenin yolu yok | **veri var ama gösterilmiyor — FIRSAT** |

## B.5 — Performans muhasebesi

| iş | (1) Veri var mı | (2) Bugün karşılanıyor mu | (3) HÜKÜM |
|---|---|---|---|
| Kapanmış vs açık ayrımıyla K/Z | `kitap{realized_pnl, day_start_equity, peak_equity}`, `equity`, `day_pnl_pct`, `open_positions[].risk_dollars` | Evet — "Durum · KİTAP" kartı (api.py:1065–1080; tabanı türetmiyor, kitaptan okuyor) | **zaten var, biçim açık** |
| **"Hiç işlem yapmasaydım"a karşı ölçme** | `benchmark_relative` (SPY'a karşı, **maruziyet-düzeltmeli**: `_exposure_ratio` ortalama yatırımda-kalma oranı, 2000 bootstrap, sabit tohum 20260729), `alpha_beta` (`_sonuc_v.beta_duzeltilmis`) | Evet — MLOps bölümünde | **zaten var, biçim açık** — Meridian burada HB/QC/TV'nin hepsinden **daha titiz** (ham fark yerine maruziyet-düzeltmeli) |
| Çıkış nedeni dağılımı (FT `/stats`) | `exit_efficiency.reasons{stop, time_stop, stop_gap, …}` → her biri `n`, `n_cf`, `avg_mfe_r`, `avg_realized_r`, **`left_r`**; `/api/plots` hücrelerinde `exits` sayımı | **Kısmen** — panoda yalnız **iki sayı**: `avg_left_r` ve `worst_reason`/`worst_left_r` (app.js:3745–3748). Neden-başına kırılım (canlıda `stop` 892/1.613R, `time_stop` 904/0.686R, `stop_gap` 132/1.973R) gösterilmiyor | **veri var ama gösterilmiyor — FIRSAT** ⭐ |
| İşlem kalitesinin dağılımı (TV Trades analysis) | `score_detail` (n, score, avg_r, win_rate, max_drawdown, sharpe), `kelly`, `tail_risk` (blok-bootstrap VaR/CVaR), `mae_profile` (kazanan/kaybeden ayrı medyan/ort/p90/maks), `trades.bars_held` | Evet — performans + MAE profili | **zaten var, biçim açık** |
| Katkı ayrıştırma | `per_regime`, `per_skill`, `skill_attribution{n,wins,sum_r}`, `/api/plots` kurulum×rejim matrisi (hücre `n` + gürültü bandı: `|mean_r| > 1/√n` dışına çıkmadıkça renk YOK) | Evet — parsel matrisi (imza öğe) | **zaten var, biçim açık** — kategoride eşi yok (n-duyarlı nötr bant) |
| Bakiyenin **işlem-dışı** nedenle değişmesi (ALP Account Activities: DIV/FEE/SSP/REORG…) | Kısmen: `sermaye_resetleri` beyan defteri (`sermaye_koken.ofset_usd/ayrisik/reset_tarihi`), `trades.costs`; temettü/split/kurumsal olay muhasebesi **yok** (kâğıt ayna + kendi simülatörü) | Kısmen — sermaye reset beyanı panoda; kurumsal olay kalemi yok | **veri yok — YENİ MODÜL ADAYI** · (a) kitap değişimini "işlem / ücret / kurumsal olay / beyan" diye ayrıştıran mutabakat satırı · (b) Alpaca `account activities` ucundan **türetilebilir** (NTA sınıfları: DIV, INT, FEE, CFEE, SSP, SSO, MA, REORG) — dış kaynak elimizde · (c) **M** · kart gerekmez (muhasebe, kenar iddiası değil) |
| Zaman-serisi ritmi (FT daily/weekly/monthly) | `/api/digest` (günlük düz metin), `/api/digest/weekly` (7 günlük), `equity_curve` | Evet — dışa aktar bölümü + eğri | **zaten var, biçim açık** |
| **Skorun olgunlaşma eğrisi** (Numerai 20D2L deseni) | `score_detail.n` vs `goal.min_sample` (skor n<min_sample'da **None**), `hermes.status.trades_until_next`, `horizon{ready, trades, trades_needed, span_days, min_days}`, `IC_MIN_SAMPLE=30`, `defter` gerçek-canlı sayacı | **Kısmen** — "ölçülemedi + neden" doğru yazılıyor ve ufuk kapısı Hermes kartında görünüyor; ama "bu sayı **ne zaman** güvenilir olacak" tek bir olgunlaşma göstergesinde toplanmıyor | **veri var ama gösterilmiyor — FIRSAT** ⭐ |

## B.6 — Risk, fren ve durdurma

| iş | (1) Veri var mı | (2) Bugün karşılanıyor mu | (3) HÜKÜM |
|---|---|---|---|
| Aciliyet seviyesini seçme (üç/dört kademe) | `/api/control/halt`, `/api/control/cancel_open`, `/api/alpaca/close_all` (onay jetonsuz **kuru koşu**), `/api/control/learn_halt` | Evet — üst barda dört kademeli KRİZ grubu: `Soft Halt` → `Cancel-Open` → `Flatten ⚠` (çift onay) → `Halt Learning`; artı `HALT` | **zaten var, biçim açık** — QC'nin Stop/Liquidate ikilisinden **daha ayrıntılı**; ayrıca sahiplik denetimi var ("bu hesapta operatörün KENDİ pozisyonları da var") |
| Durdurmanın açık emirlere etkisi | `cancel_open` ayrı kol; `close_all` `foreign` listesini raporluyor | Evet | **zaten var, biçim açık** |
| Gözetimsiz koşuda otomatik fren | `goal.yaml` risk sözleşmesi, `breaker_tripped`, `daily_loss_breaker` gate check (`>-%3`), `max_drawdown`, `learn_halt`, `guard.py` | Evet — devre kesici + kapı ölçütleri. **Not:** ROADMAP §5 "equity-eğrisi otomatik risk kısma" bilinçli olarak YAPMA listesinde ("momentum sistemini dipte kapatır; yerine DD>1.5×beklenti insan-incelemeli alarm") | **zaten var, biçim açık** (HB kill-switch'in Meridian karşılığı bilinçli olarak insan-incelemeli) |
| **İptali olmayan aksiyondan önce ön-uçuş** (IBKR `WhatIf`, ALP `--dry-run`) | `close_all` onay jetonsuz kuru-koşu **var**; plan onayı iki adımlı (8 sn penceresi); `arming_report` ölçümü | Kısmen — `Flatten` kuru koşuyor; **plan onayı** için "onaylarsam ne olacak" ön-uçuşu (boyut, risk-R, sektör tavanı etkisi, kalan slot) tek yerde gösterilmiyor — girdiler `gate_checks` + `portfolio_heat` + `current_exposure_pct`'te | **veri var ama gösterilmiyor — FIRSAT** |
| Frenin nerede durduğu (bot mu borsa mı) | `hwm_pairs` (iç `trail_stop` ↔ Alpaca'ya giden son PATCH + `desync`), `reconcile.drift/ghosts/stripped`, `stream_ok` | Evet — mutabakat bölümü; `stream_ok` ham değil nabızla çarpılmış (`_stream_view`) | **zaten var, biçim açık** |
| Portföy düzeyinde risk | `portfolio_heat`, `current_exposure_pct`, `exposure_budget_pct`, `open_positions[].size_r` (ısı ölçülemezse **toplanmıyor** — eksik toplam gösterilmiyor) | Evet — Durum · POZİSYONLAR kartı | **zaten var, biçim açık** |

## B.7 — Bildirim ve uzaktan gözetim

| iş | (1) Veri var mı | (2) Bugün karşılanıyor mu | (3) HÜKÜM |
|---|---|---|---|
| Olay bazlı haber alma | Mekanizma tam: `notify.configured()`, `notify.send`, `obs.alarm` → `NOTIFY_TOKENS`, `/api/notify/test`, `notify_undelivered.json`; **kanal boş** (ROADMAP §6 md.2: "Telegram/webhook — teslim zinciri hazır, kanal boş") | Yerel gelen kutusu var (`/api/alerts`, imzaya göre gruplu, ACK "gördüm" işareti hiçbir alarmı silmez); uzak kanal yapılandırılmamış | **zaten var** (mekanizma) — eksik olan **operatör kalemi**, tasarım kalemi değil |
| **İki kademeli eşik + NO_DATA hali** (Langfuse: Warning/Alert + OK→WARNING→ALERT→**NO_DATA**) | `alarm_butcesi` (EEMUA 80/15/5 + <10/10dk tepe + duran alarm), `alarm_gunluk` (bastırılan sayısı **görünür**), `sessiz_hat`, `integrity_age_s`, `heartbeat_age_seconds`, "ölçülemedi" hali her metrikte var | Kısmen — "ölçülemedi" **metrik düzeyinde** var; **alarm durum makinesinde** NO_DATA ayrı bir hal değil (bekçi ya sapar ya sapmaz) | **veri var ama gösterilmiyor — FIRSAT** (düşük-orta: "bekçi ölçemedi" ile "bekçi temiz" ayrımı) |
| Terminal olmadan hata avı | `/api/events` (son 80), `/api/debug_export`, `/runbook` (auth'lu, 50 bölüm, alarm→çapa bağlı), `hermes` ham çıktı özeti (sır-maskeli 200 kr.) | Evet — Gözetim sayfası + olay akışı + runbook | **zaten var, biçim açık** |
| Yeniden başlatmadan ayar tazeleme | `/api/secrets/{name}` (POST/DELETE), `skills.reconcile_enablement()` ("anahtar gelince otomatik etkinleşme") | Evet | **zaten var, biçim açık** |

## B.8 — Kanıtı dışarı çıkarma

| iş | (1) Veri var mı | (2) Bugün karşılanıyor mu | (3) HÜKÜM |
|---|---|---|---|
| Ham kaydı indirip bağımsız doğrulama | `/api/report.csv` (16 kolonlu kapanmış-işlem defteri), `/api/state/snapshot` (tar.gz; DB'de **tutarlı** kopya — `storage.backup_to`, ham WAL kopyalanmıyor), `/api/debug_export`, `/api/digest`, `/api/digest/weekly` | Evet — Kilitler & Yapılandırma → ayarlar (detay katmanı) | **zaten var, biçim açık** |
| Canlı sonucu araştırma ortamına çekme (QC Live Analysis) | Defterler dosya olarak zaten okunabilir; `research/cards/` (24 kart) + sandbox kopya disiplini (`config.STATE` yönlendirme + mtime parmak izi) | Evet — ölçüm hattı zaten kart-disiplinli | **zaten var, biçim açık** |
| Sonucu üçüncü kişiye kanıt olarak gösterme (QC public URL) | `/api/public/summary` (landing sayfasının canlı beslemesi) | Evet, ama **bilinçli olarak dar** — PRODUCT.md: tek operatör, "no external investors, clients" | **zaten var** — genişletmek R3'e (vitrin) yaklaşırdı |

## B.9 — Evren, envanter ve filo

| iş | (1) Veri var mı | (2) Bugün karşılanıyor mu | (3) HÜKÜM |
|---|---|---|---|
| Evrenin ne olduğunu ve **neden** o olduğunu doğrulama | `/api/market` → `as_of`, `n` (canlıda 251), `stale_n`, `retired_n`, `source{bars, finviz_extra, finviz_reason}`, satır başına `retired`, `plans_n`, `last_plan_date`, `earnings_date`; `universe_drift`; `RETIRED_SYMBOLS` | Evet — Veri Sağlığı → evren tablosu; bayatlık **yalnız yaşayan sembole** soruluyor (emekli sembol sayaca girmiyor) | **zaten var, biçim açık** |
| Stratejinin dönem dönem neyi tuttuğu (CMP Historical Allocations) | `trades.jsonl` (ts_open/ts_close/qty/entry), `_exposure_ratio` günlük notional serisi, `equity_curve` | Kısmen — maruziyet oranı benchmark düzeltmesinin **içinde** hesaplanıyor; zaman içinde "ne tuttuk" serisi olarak çizilmiyor | **veri var ama gösterilmiyor — FIRSAT** (düşük öncelik: 95 kapanmış işlemde okuma değeri sınırlı) |
| İcra penceresi ve gecikme beyanı (CMP trading period) | `scheduler{last_tick, poll_seconds, cycles, learn_session, validation_week}`, `_enrich_stale_plans` → `expired`, `age_days`, `last_close`, `drift_pct`, `traded` | Evet — bayat-sinyal dürüstlüğü alanları plan satırında; süresi dolmuş plan **onaylanamaz** (uç 409 döner) | **zaten var, biçim açık** — kategoride Meridian'ın önde olduğu ikinci yer |
| Filo görünümü (FreqUI/HB Instances) | Yok ve **gerekmiyor** — tek örnek, tek operatör (PRODUCT.md) | — | **kapsam dışı** (yasa ihlali değil; paydası yok) |

## B.10 — AJAN GÖZLEMLENEBİLİRLİĞİ (eşlemenin ağırlık merkezi)

| iş | (1) Veri var mı | (2) Bugün karşılanıyor mu | (3) HÜKÜM |
|---|---|---|---|
| **Tek kararı adım adım geri sarma** | Parçalar var: `daily_cycle` olayı (`candidates/plans/armed/regime/data_ok/halted`) · `pipeline_runs.jsonl` (`run_id`, `started`, `finished`, `skills_invoked`, `skills_declared_not_run`, `skills_skipped`, `artifacts`, `status`, `error`) · `agent_call` olayları (`kind`, `model`, `attempt`, `empty`, `preloaded`) · `trade_plans.gate_checks` + `skill_chain` · `candidate_review` · `llm_opinion`/`llm_veto` | **Kısmen — ama TEK EKSENDE DEĞİL.** Pipeline koşuları kendi kartında (süre kolonlu, app.js:5750), kapı kararı plan çekmecesinde, LLM çağrıları olay akışında, aday incelemesi ayrı kartta. "Dün gecenin tek zaman çizelgesi" yok | **veri var ama gösterilmiyor — FIRSAT** ⭐ |
| Ajanın izlediği yolu graf olarak görme | `pipeline_runs` hat adları (P3_PLAN, P5_LEARN…) + `skills_invoked` + `artifacts` → statik graf `codelaw.artifact_graph`'ta zaten var | Kısmen — `workflow.html` bir **açıklayıcı** (statik anlatı), koşuya bağlı değil | **veri var ama gösterilmiyor — FIRSAT** (orta: `skills_declared_not_run` "beyan edildi koşmadı" farkı zaten en değerli sinyal ve gösteriliyor) |
| **Arızalı koşuları hedefli filtreyle bulma / kaydedilmiş görünüm** | `events.jsonl` (~9 MB, tam olay sözlüğü), `trade_plans.jsonl` (390 satır), `trades.jsonl`, `counterfactuals.jsonl` (7161) | **Hayır** — `/api/events` son **80** olay, `/api/signals` 390 planın **120**'sini (beyanlı tavan). Arama/filtre/kaydedilmiş görünüm yok; "bu sembolde geçmişte ne karar verdim" cevaplanamıyor | **veri var ama gösterilmiyor — FIRSAT** ⭐ |
| **Token ve maliyet muhasebesini atfedilebilir kılma** | `spend.jsonl` çağrı başına `ts`, `model`, `in_tokens`, `out_tokens`, `cost_usd`, `note`, `thought_tokens`; `/api/spend` → aylık toplam + `recent[30]`; `agent_budget.json` (rpm/rpd), `agent_tooluse.json` (`calls`, `with_tools`, `total_tools`), `agent_calls` (rpm_limit/rpd_limit) | **Kısmen** — panoya yalnız **aylık toplam + bütçe doldu mu** ulaşıyor (`/api/hermes` içindeki `spend` özeti). **`/api/spend` ucunun web tarafında HİÇ tüketicisi yok** (app.js'te `/api/spend` çağrısı sıfır). Çağrı-başına kırılım, model kırılımı, "gece koşusu ne tuttu" hiçbir yerde | **veri var ama gösterilmiyor — FIRSAT** ⭐ |
| Latency dağılımı / darboğaz | `pipeline_runs.started/finished` (hat düzeyinde süre — **gösteriliyor**, "SÜRE" kolonu); `store.io_stats` + `io_latency_high` uyarısı (p95); `prescreen.sure_s`. **Çağrı başına LLM süresi YOK** | Kısmen — hat süresi var, çağrı süresi yok | **veri yok — YENİ MODÜL ADAYI** (aşağıda C2-1) |
| Satıcı-bağımsız telemetri sözleşmesi (OTel GenAI) | `obs.log/warn/alarm` kendi sözlüğü + `codelaw.artifact_graph` + `ledgers.declared_writers` | Hayır — ama Meridian'ın **kendi** sözleşmesi zaten var ve daha sıkı (YASA 6: üretilen her alanın dış tüketicisi olmalı) | **kapsam dışı** — OTel'e taşınmak tek-operatörlü, CSP-self bir sistemde net kazanç vermez; **kalıcı isim disiplini** dersi ise zaten yürürlükte |
| **Yinelenen arızaları taksonomiye kümeleme** | `events.jsonl` olay sözlüğü (canlı ölçüm: son 3000 satırda `hotstate_down` 1607, `bar_cache_repaired` 401, `finviz_unavailable` 241, `session_deferred_for_coverage` 240…), `sieve` drop nedenleri (`sema:…`, `piyasa:…`), `watchdog` bekçileri, `alarm_gunluk` bastırma sayacı | Kısmen — alarm bütçesi ve bastırma **sayılıyor**; "bu hafta hangi arıza SINIFI tekrarlıyor" kümelemesi yok | **veri var ama gösterilmiyor — FIRSAT** |
| Örneklemli otomatik puanlama (online eval) | `gate_calibration`, `score_calibration` (+ 60 satırlık geçmiş), `llm_calibration` (buckets: destekle/çekimser/karşı → avg_r, n), `prediction_hit`, `calibration` (Brier + güvenilirlik binleri), `component_ic`, `shrunk_component_ic` | Evet — ve **R8'in istediği payda disiplini zaten yerinde** (IC_MIN_SAMPLE=30 altı None; `spearman_ic` tanımsızda 0.0 değil **None** döner) | **zaten var, biçim açık** — kategorinin "LLM-as-judge" katmanından **daha sıkı** (Brier + kalibrasyon binleri) |
| **İnsan inceleme kuyruğunu rubrikle işletme** | `/api/approvals` → `inbox[{type, id, title, evidence, actions}]` dört kaynaktan (silahlanma ölçümü · skill revizyon taslağı · Eksen-2 önerisi · onay bekleyen REVIEW planı); `inbox_count`; `onay_bekliyor` damgası (üç koşullu: REVIEW · onay yok · süresi dolmamış) | Evet — birleşik gelen kutusu; **NO_GO onaylanamaz** (guard sert reddi), süresi dolmuş plan onaylanamaz (409) | **zaten var, biçim açık** — LangSmith'in Needs Review→Completed akışının Meridian karşılığı; **eksik olan tek şey durum akışının kendisi** ("kim baktı, ne kadar kaldı") |
| **Arızayı kalıcı regresyon testine sabitleme** | Yok — canlı bir yanlış-kararı dondurulmuş fikstüre çeviren yol yok (test fikstürleri elle yazılıyor; bkz. da6bec3 vakası: v76 fikstürü elle onarıldı) | Hayır | **veri yok — YENİ MODÜL ADAYI** (C2-3) |
| **Yeni sürümün neyi bozduğunu örnek düzeyinde gösterme** | `scoreboard.versions[]` (`params`, `backtest_oos`, `baseline_verdict`, `baseline_source`, `baseline_n_trades`, `baseline_span_days`), `hypotheses.jsonl` (`predicted_delta` ↔ `realized_delta`, `reject_reasons`, `backtest.candidate_oos`), `per_regime`, `per_skill`, `oos_erosion` (pencere/fold kaydı), `shadow_variants`, `validation_trio`, `deflate`/`dsr` | **Kısmen** — sürüm zaman çizelgesi + hipotez kartları (tahmin↔gerçekleşen) var; **"bu sürüm neyi DÜZELTTİ, neyi BOZDU"** kırılımı (rejim/kurulum/skill başına regresyon) yok | **veri var ama gösterilmiyor — FIRSAT** ⭐ |
| Regresyonda dağıtımı durdurma | `dagit.sh` kapıları (temiz ağaç + tam suite + dry-run + mtime + doğrulama), `reflect._gate_eval` TEK hakem, `rollback_if_worse_by` | Evet — ölçüm zaten kapı | **zaten var, biçim açık** |
| **Otomatik geri-almanın (rollback) sicili** | `meridian/rollback.py` (`check_and_rollback`, `evaluate_outcomes`, `_overturn_log`, `_would_have`, `_para_ikizi`, `_no_parent_diagnostics`), `learning_loop_open.json`, `guard` `rollback_if_worse_by` | **Hayır** — `app.js` içinde "rollback" kelimesi **sıfır kez** geçiyor. PRODUCT.md'nin açık vaadi ("underperforming versions auto-rollback") panoda karşılıksız | **veri var ama gösterilmiyor — FIRSAT** ⭐ |
| Prompt/sürüm yönetimi ve geri alma | `hermes` SYSTEM promptu **statik ve AST-çivili** (bilinçli); `skills_registry` + `skill_evolve.revisions()` (revizyon geçmişi, son 10) + gölge modu (10 seans) + **ajan kendi skill'ini terfi ettiremez** | Evet — skill revizyon kartları + onay/ret | **zaten var, biçim açık** |
| Üretim izini farklı model/prompt ile yeniden koşturma (Weave Playground) | Kısmen: `sprint` (sandbox öğrenme antrenmanı, `budget`/`k_max`), `/api/hermes/reflect`, `reflect --auto`, `counterfactual` motoru; **prompt/model varyantıyla aynı gece için yeniden koşum** yok | Kısmen | **veri yok — YENİ MODÜL ADAYI** (düşük öncelik: `NOUS_MODEL` çeşitliliği zaten operatör kalemi; ayrıca "yerel LLM kurulmaz" kararı 2026-07-30) |
| Eşik alarmında uyandırma | `alarm_butcesi`, `watchdog`, `notify` zinciri | Evet (kanal boş — operatör kalemi) | **zaten var, biçim açık** |
| **Ajan koşusunu duraklatıp onayla/düzelt/reddet ve DEVAM ETTİR** | Yok — onay **plan düzeyinde** (`/api/plan/{id}/onayla`), koşu düzeyinde değil; gece hattı ortasında durup insan onayıyla devam eden bir checkpointer yok | Hayır | **veri yok — YENİ MODÜL ADAYI** (C2-5; L1 otonomi kademesinde yapısal hale gelir) |
| Ölçümün sessizce kopmasını önleme (kararlı isim sözleşmesi) | `codelaw.artifact_graph` (statik graf; literal dosya adı zorunluluğu beyanlı), `ledgers.declared_writers`, `codelaw._src_stamp`, YASA 6 denetimi, `stale_sinks` ihlali | Evet — ve **kod-düzeyinde zorlanıyor**, LangSmith'te yalnız "best practice" | **zaten var, biçim açık** — kategoride Meridian'ın **en önde** olduğu yer |

---

# BÖLÜM C — EN YÜKSEK KALDIRAÇLI İŞLER

## C1 — Mevcut veriyle beslenen ilk on

Seçim ölçütü: **iş cevaplanmıyor** (alanın `app.js`'te geçip geçmemesi değil) × veri canlı state'te
hazır × üç kanonik top-task'a katkı. Sıra kaldıraç sırasıdır, uygulama sırası değil.

### C1-1 · Reddedilen kararların karnesi — "kapım masada para bırakıyor mu?"
- **Operatörün sorusu:** "Bu eşik doğru mu? Reddettiklerim ne yapardı?"
- **Neden değerli:** Bir kapı ancak reddettikleriyle yargılanabilir. Kabul edilenlerin karnesi
  (parsel matrisi) zaten var; **reddedilenlerinki hiçbir yerde yok.** Kategoride bu işin karşılığı
  yalnız FT'nin `locks.reason`'ı kadar sığ — Meridian'ın elindeki kanıt çok daha derin.
- **Beslendiği veri:** `near_miss.json` → `resolved_total` (canlıda **4.988**),
  `buckets{<blocked_by>: {n, entered, n_r, avg_r, by_regime{}}}`, `_kaynak` künyesi
  (`source: "yalnız-simüle"`, `n_real: 0`) · `counterfactuals.jsonl` (**7.161** satır:
  `taken`, `entered`, `blocked_by`, `r_multiple`, `mfe_r`, `mae_r`, `verdict`).
- **Bugünkü durum:** `near_miss.json`ın **hiçbir uç tüketicisi yok** ve `app.js`'te adı geçmiyor;
  yalnız `selfreview._near_miss_attention` ondan **türetilmiş bir öneri** üretiyor
  (`/api/selfreview` → `attention`). Kanıt tablosu görünmez, hükmü görünür.
- **Dürüstlük şartı:** künye zorunlu — bu defter **yalnız-simüle** (`n_real: 0`). Gerçek kanıt
  gibi çizilirse R8'e düşer.

### C1-2 · Onaylanan planın emir yaşam-döngüsü izi — "onayım aynaya ulaştı mı, kaça doldu?"
- **Operatörün sorusu:** "Onayladığım plan hangi emre dönüştü, şu an hangi durumda, **kaça** doldu?"
- **Neden değerli:** Top-task ② tam olarak bu ve UX denetimi (B1) ölçtü: son bacak **hiçbir kalıcı
  geri bildirim taşımıyor**, yalnız geçici bir çekmece mesajı. Kategorinin en olgun deseni burada
  (QC Orders sekmesi, IBKR durum sözlüğü + `whyHeld`, ALP emir durumları).
- **Beslendiği veri:** `mirror_orders.json` → coid başına `status`, `event`, `symbol`, `side`,
  `filled_qty`, **`filled_avg_price`**, `order_id`, `updated` · `portfolio.armed` +
  `portfolio.alpaca_submitted` · `trade_plans.entry_trigger` (planlanan ↔ gerçekleşen farkı =
  emir-başına slipaj) · `reconcile.partial_fills`, `failed_submissions`.
- **Bugünkü durum:** Yalnız **toplam huni** çiziliyor ("silahlı → gönderilmiş → dolan",
  app.js:1749–1789, üç payda ayrı olduğu beyanlı). `mirror_orders.json` panoya hiç ulaşmıyor —
  `api.py:2271`'de yalnız `_stream_view` (akış sağlığı) için okunuyor.

### C1-3 · Gece koşusunun maliyet ve token karnesi — "bu düşünme ne tuttu?"
- **Operatörün sorusu:** "Dün gece kaç çağrı, kaç token, kaç dolar? Hangi kol yedi?"
- **Neden değerli:** Ajan gözlemlenebilirlik hattının **en yaygın** ve en olgun işi; kendi
  altyapı maliyeti olduğu için R4'e (gerçek-para iması) değmez. Beyin bütçesi dolduğunda sistem
  ücretsiz yola düşüyor — bu geçişin maliyeti bugün ancak "bütçe doldu" ikili bayrağıyla görünüyor.
- **Beslendiği veri:** `spend.jsonl` → çağrı başına `ts`, `model`, `in_tokens`, `out_tokens`,
  `cost_usd`, `note`, `thought_tokens` · `/api/spend` → `spent_usd`, `budget_usd`,
  `remaining_usd`, `over_budget`, `calls_this_month`, `thought_tokens`, `recent[30]` ·
  `agent_budget.json` (rpm/rpd) · `agent_tooluse.json` (`calls`, `with_tools`, `total_tools`) ·
  `agent_calls.rpm_limit/rpd_limit` · `agent_call` olayları (`kind`, `model`, `attempt`, `empty`).
- **Bugünkü durum:** **`/api/spend` ucunun web tarafında hiç çağıranı yok** (doğrulandı: `app.js`
  içinde `/api/spend` sıfır geçiyor). Panoya ulaşan tek şey `/api/hermes` içindeki aylık özet ve
  `over_budget` bayrağı. Model kırılımı, çağrı kırılımı, gece-başına maliyet: hiçbiri yok.

### C1-4 · Gecenin tek zaman çizelgesi — "karar adım adım nasıl oluştu?"
- **Operatörün sorusu:** "Dün gece ne oldu — sırasıyla?"
- **Neden değerli:** LangSmith/Langfuse'un birinci işi (trace geri sarma). Meridian'da parçaların
  **hepsi** var ama dört ayrı yüzeye dağılmış; operatör zihninde birleştiriyor.
- **Beslendiği veri:** `daily_cycle` olayı (`date`, `ts`, `candidates`, `plans`, `armed`,
  `regime`, `open_positions`, `data_ok`, `halted`) · `pipeline_runs.jsonl` (`run_id`, `pipeline`,
  `started`, `finished`, `skills_invoked`, `skills_declared_not_run`, `skills_skipped`,
  `artifacts`, `status`, `error`) · `agent_call` olayları · `trade_plans.gate_checks` +
  `skill_chain` · `candidate_review` · `arming_report`.
- **Bugünkü durum:** Pipeline koşuları kendi kartında (süre kolonlu, app.js:5750), kapı kararı
  plan çekmecesinde, LLM çağrıları olay akışında, aday incelemesi ayrı kartta.

### C1-5 · Otomatik geri-almanın sicili — "kendini gerçekten geri alıyor mu?"
- **Operatörün sorusu:** "Hangi sürüm geri alındı, neden, ne kadar sürdü — ve şu an açık bir
  öğrenme döngüsü var mı?"
- **Neden değerli:** PRODUCT.md'nin **açık vaadi** ("underperforming versions auto-rollback") ve
  konumlandırmanın dört sütunundan biri. Panoda karşılığı **yok**: `app.js` içinde "rollback"
  kelimesi **sıfır kez** geçiyor. Bir vaadin görünmezliği, vaadin kendisini ölçülemez yapar.
- **Beslendiği veri:** `meridian/rollback.py` (`check_and_rollback`, `evaluate_outcomes`,
  `_overturn_log`, `_would_have`, `_para_ikizi`, `_no_parent_diagnostics`,
  `sweep_orphan_hypotheses`) · `learning_loop_open.json` (açık döngü kaydı + sebep sayaçları) ·
  `scoreboard.versions[].baseline_verdict/baseline_source` · `guard` `rollback_if_worse_by` ·
  `hypotheses.status`.

### C1-6 · "Bu sürüm neyi düzeltti, NEYİ BOZDU" — regresyon kırılımı
- **Operatörün sorusu:** "v3→v4 net iyileşme mi, yoksa bir yerde kazanıp başka yerde mi kaybettim?"
- **Neden değerli:** Ajan gözlemlenebilirlik hattının en keskin deseni (LangSmith deney
  karşılaştırması: feedback key başına **kırmızı = regresyon / yeşil = iyileşme**, örnek-başına
  detay). Toplam skorun gizlediği tek şey budur; Meridian'ın kill-disiplini de tam buna dayanır.
- **Beslendiği veri:** `scoreboard.versions[]` (`params`, `backtest_oos`, `baseline_verdict`,
  `baseline_source`, `baseline_n_trades`, `baseline_span_days`) · `hypotheses.jsonl`
  (`predicted_delta` ↔ `realized_delta`, `reject_reasons`, `backtest.candidate_oos`, `dsr`,
  `dsr_dusuk`, `ship_modu`) · `per_regime`, `per_skill`, `skill_attribution` · `regime_edge` ·
  `oos_erosion` (pencere + fold kaydı) · `shadow_variants` · `validation_trio` · `deflate`.
- **Bugünkü durum:** Sürüm zaman çizelgesi (app.js:5535) + hipotez kartları var; **kırılım yok**.

### C1-7 · Denetim izinin tamamına erişim — "bu sembolde geçmişte ne karar verdim?"
- **Operatörün sorusu:** "AAPL'de son altı ayda kaç plan kuruldu, kaçı NO_GO oldu, neden?"
- **Neden değerli:** Kategorinin dördüncü işi (LangSmith hedefli filtre + **kaydedilebilir
  görünüm**). Meridian bugün "denetim izi" iddiasında bulunuyor ama defterin üçte birini
  gösteriyor — tavan **beyanlı** (2026-07-22 düzeltmesi), yani dürüst; ama iş cevaplanmıyor.
- **Beslendiği veri:** `trade_plans.jsonl` (**390** satır; uç `plans_shown: 120`) ·
  `candidates.jsonl` (**323**) · `events.jsonl` (~9 MB; uç son **80**) · `trades.jsonl` (95) ·
  `counterfactuals.jsonl` (7.161) · `/api/market` satırlarında zaten `plans_n` ve
  `last_plan_date` var (sembol ekseni hazır).
- **Not:** Tavanların kendisi bir performans kararıydı (`_SON_DONGU_KUYRUK` gerekçesi) — çözüm
  tavanı kaldırmak değil, **sorgulanabilir** kılmak.

### C1-8 · "Bugün neden hiçbir şey olmadı" — eylemsizliğin tek cümlelik nedeni
- **Operatörün sorusu:** "Sıfır aday. Bozuk mu, tasarım mı?"
- **Neden değerli:** FT `locks.reason` ve CMP "neden nakit tutuyor" desenlerinin birleşimi.
  Meridian bugün **dürüst** ("bu seansta tarama adayı yok — huninin paydası kurulamadı",
  app.js:2142) ama **nedensiz**; oysa nedeni taşıyan alanların hepsi elde.
- **Beslendiği veri:** `regime.exposure_budget_pct` (canlıda 0 → "bugün yeni risk yok") ·
  `verdict_counts` · `gate_reasons[]` + `gate_checks[{check, passed, value, threshold}]` ·
  `blackout_radar` (kazanç penceresi) · `halted` / `learn_halted` / `data_ok` ·
  `session_deferred_for_coverage` olayı (son 3000 olayda **240** kez) · `finviz_unavailable`
  (241) · `dormant_setup` · `scan_debt` · `stale_n`.

### C1-9 · Çıkış nedeni kırılımı — "hangi çıkış mekanizması masada para bırakıyor?"
- **Operatörün sorusu:** "Stop mu erken, zaman stopu mu geç, gap mi yiyor?"
- **Neden değerli:** FT `/stats` (çıkış nedenine göre kazanç/kayıp) kategorinin standardı;
  Meridian'ın verisi **daha zengin** (MFE'ye göre masada bırakılan R). ROADMAP'te çıkış reformu
  zaten açık kalem — kanıt panoda olmadan tartışma belgeye kaçıyor.
- **Beslendiği veri:** `exit_efficiency.json` → `reasons{<neden>: {n, n_cf, avg_mfe_r,
  avg_realized_r, left_r}}`; canlı ölçüm: `stop` n=892/left 1.613R · `time_stop` n=904/left
  0.686R · `stop_gap` n=132/left **1.973R** · toplam `avg_left_r` 1.105 · `mae_profile`
  (kazanan p90 0.713 ↔ kaybeden medyan 1.058) · `/api/plots` hücrelerindeki `exits` sayımı.
- **Bugünkü durum:** Panoda yalnız **iki sayı** (`avg_left_r` + en kötü neden, app.js:3745–3748).

### C1-10 · Skorun olgunlaşma göstergesi — "bu sayı ne zaman güvenilir olacak?"
- **Operatörün sorusu:** "Skor 'ölçülemedi' diyor. Ne kadar kaldı?"
- **Neden değerli:** Numerai'nin 20D2L deseni (skor gün gün olgunlaşır) — kategoride tek örneği o.
  Meridian **doğru** davranıyor (n<min_sample'da skor `None`, IC<30'da `None`) ama operatöre
  **mesafeyi** söylemiyor; "ölçülemedi" kalıcı bir duvar gibi okunuyor.
- **Beslendiği veri:** `score_detail.n` vs `goal.min_sample` · `IC_MIN_SAMPLE = 30` ·
  `hermes.status.trades_until_next` · `horizon{ready, regime, trades, trades_needed, span_days,
  min_days}` · `defter` (ledgerstamp: gerçek-canlı ↔ replay-tohumu ayrımı) ·
  `ladder.auto_progress{met, total}` + `l0_to_l1[]` (8 ölçüt, `manual` bayraklı) ·
  `cf_fidelity` kesişim sayacı ("kesişim <5 — alınan planlar birikiyor").

## C2 — Yeni modül isteyen ilk beş (maliyet sırasıyla)

Hiçbiri "verimiz yok" diye elenmedi; maliyetiyle aday yazıldı. Hüküm Rol-1'de.

### C2-1 · Çağrı-başına ajan telemetrisi — **S**
- **(a) Ne üretmeli:** her LLM/ajan çağrısı için `sure_ms` + `deneme` + `arac_cagri_n` +
  `bitis_nedeni` yazar; `spend.jsonl` satırıyla aynı kimlikte birleşir → "gece koşusu neden 40 dk
  sürdü, hangi çağrı takıldı".
- **(b) Türetilebilir mi:** **Hayır** — süre ölçüm anında yazılmalı; mevcut hiçbir defterde
  çağrı süresi yok (`pipeline_runs` yalnız **hat** düzeyinde `started`/`finished` taşıyor ve o
  zaten gösteriliyor). Dış kaynak **gerekmez**; yazım noktası `hermes` çağrı sarmalayıcısı,
  taşıyıcı defter `spend.jsonl` / `agent_call` olayı — ikisi de mevcut.
- **(c) Büyüklük:** **S** (tek okuma-ucu + görünüm; yeni defter yok).
- **Kart:** gerekmez (saf telemetri, kenar iddiası üretmez).

### C2-2 · Ham ajan-izi defteri (trace ledger) — **M**
- **(a) Ne üretmeli:** her ajan çağrısının **tam** girdi/çıktısı ve araç çağrıları, sır-maskeli
  ve budanabilir ayrı bir defterde → C1-4'ün zaman çizelgesini "adım adım geri sarma"ya çıkarır.
- **(b) Türetilebilir mi:** **Hayır** — bugün yalnız **200 karakterlik** sır-maskeli özet var
  (`hermes._ham_ozet`, hermes.py:1570–1601; ham çıktı deftere yazılmıyor). Maskeleme mekanizması
  (üç desen: adlı atama, `Bearer`, ≥24 karakterlik çıplak jeton) **hazır** ve yeniden kullanılır.
  Dış kaynak **gerekmez**. Maliyet uyarısı: `events.jsonl` canlıda zaten ~9 MB — bu defter
  **ayrı** olmalı ve budama kuralı doğuşta yazılmalı.
- **(c) Büyüklük:** **M** (yeni defter + budama + YASA 6 dış okuyucusu).
- **Kart:** gerekmez.

### C2-3 · Vakayı sabitleme: canlı arıza → dondurulmuş fikstür — **M**
- **(a) Ne üretmeli:** bir canlı yanlış-kararı (plan + `gate_checks` + bar penceresi + gerçekleşen
  sonuç) tek komutla `tests/` altında dondurulmuş bir regresyon vakasına çevirir.
- **(b) Türetilebilir mi:** girdilerin **hepsi** mevcut (`trade_plans`, `trades`,
  `counterfactuals`, `state/bars/*.csv`); eksik olan **dönüştürücünün kendisi** — bugün fikstürler
  elle yazılıyor (kanıt: da6bec3 vakası, v76 fikstürü elle onarıldı; 17→68 işlem). Dış kaynak
  **gerekmez**. Bu bir görünüm değil **mekanizma** adayıdır; LangSmith'in "Add to Dataset"
  deseninin Meridian karşılığı.
- **(c) Büyüklük:** **M** (yeni türetme + kalıcı fikstür deposu).
- **Kart:** gerekmez (regresyon koruması; kenar iddiası üretmez).

### C2-4 · İkinci motor diferansiyeli (yerel LEAN) — **L**
- **(a) Ne üretmeli:** aynı sinyalleri bağımsız bir motorda koşup **emir düzeyinde diff** üretir →
  "canlı-backtest sapması bizim motorun mu?" sorusunu QC'nin reconciliation deseninin en derin
  biçiminde cevaplar (B.4'teki adlandırılmış-neden listesi ancak bununla tamamlanır).
- **(b) Türetilebilir mi:** Veri **kendimizin** (Massive/Alpaca barları, LEAN'e custom data
  `LOCAL_FILE` ile okutulur). Dış bağımlılık **runtime**: LEAN motoru **Apache-2.0**, `lean-cli`
  ücretli katman ister ama motorun kendisi `dotnet`/`docker` ile CLI'sız koşar — **QC hesabı ya da
  ücretli katman gerekmez**. Oracle A1'e kurulmaz (yerel makine).
  Kaynak: `docs/QC-ENTEGRASYON-DEGERLENDIRMESI.md` §0 ve §2.
- **(c) Büyüklük:** **L** (yeni dış bağımlılık + çift-motor kanıt hattı).
- **Kart:** motor-diff'in kendisi kenar iddiası üretmez; **bir sinyalin hükmünü değiştirirse kart
  gerekir**.

### C2-5 · Delist-dahil evren arşivi (survivorship düzeltmesi) — **L**
- **(a) Ne üretmeli:** `near_miss` / `counterfactuals` defterlerinin **paydasını** delist edilmiş
  isimlerle tamamlar — yani C1-1'in karnesini survivorship yanlılığından kurtarır.
- **(b) Türetilebilir mi:** **Hayır — dış kaynak zorunlu.** Yerel arşivde ölçülen boşluk **%96,6**.
  Meşru tek yol **Massive plan yükseltmesi** (para kararı, **operatör kalemi**).
  **QC bu boşluğu dolduramaz:** veri platformdan çıkamaz — "internal LEAN use only … cannot be
  redistributed or converted in any format" + log-export yasağı (Terms 3.3(b)(xvi)); Rol-1 hükmü
  "yerel-indirme yolu İZLENMESİN, arşiv ihtiyacının meşru yolu Massive'dir". QC'nin meşru katkısı
  ayrı ve **bedava**: ölçüm platform içinde koşar, dışarı **yalnız hüküm-sayısı** taşınır
  (EDG-021 deseni). Kaynak: `docs/QC-ENTEGRASYON-DEGERLENDIRMESI.md` §0, §2, §3, §4.
- **(c) Büyüklük:** **L** (yeni veri hattı + sağlayıcı/kota/maliyet kararı).
- **Kart:** **ZORUNLU** — payda değişince her kenar iddiası yeniden ölçülür.

---

## KAPANIŞ — sayılar

| Ölçüm | Değer |
|---|---|
| İncelenen platform ailesi | **11** (QC · Composer · Alpaca · TradingView · Freqtrade/FreqUI · Hummingbot · IBKR TWS · Numerai · eToro · LangSmith/Langfuse/AgentOps/Weave · OTel GenAI semconv) |
| Kataloglanan iş satırı | **81** (A.1–A.12) |
| Elenen desen sınıfı | **10** (R1–R10) — yazılı yasa ihlali **9** (R1–R9; ikisi koşullu ret: R8, R9) + disiplin ihlali **1** (R10, yasa değil) |
| Eşleme satırı (Bölüm B, R1–R10 hariç) | **65** |
| — `zaten var, biçim açık` | **35** |
| — `veri var ama gösterilmiyor — FIRSAT` | **22** (10'u C1'e girdi) |
| — `veri yok — YENİ MODÜL ADAYI` | **6** (5'i C2'ye girdi; kalan biri düşük öncelikli Playground benzeri yeniden-koşum) |
| — `kapsam dışı` (yasa ihlali değil, paydası yok) | **2** (filo görünümü · OTel'e taşınma) |
| Meridian'ın kategoriden **önde** olduğu ölçülen yer | **5**: köken/künye disiplini (`sieve.provenance`, `ledger_source`, gerçek↔sim çipleri) · maruziyet-düzeltmeli benchmark · n-duyarlı nötr bant (parsel matrisi) · bayat-sinyal dürüstlüğü (`expired` → onay 409) · **kod-düzeyinde zorlanan** artefakt-graf/YASA 6 (LangSmith'te aynı ders yalnız "best practice") |
| Erişilemeyen kaynak (ölçülemedi + neden yazıldı) | help.etoro.com tüm varyantları **403** · IBKR Campus Risk Navigator dersi **403** · W&B Weave docs **403/404** · Numerai `diagnostics` sayfası **404** · Hummingbot `client/logs` **404** · Freqtrade `edge` **404** · tüm canlı panolar (oturum duvarı) → **görsel iddia yok** |

**Etüdün tek cümlelik okuması:** Meridian'ın panosu kategoriye göre eksik değil — **dürüstlük
katmanında açık ara önde, birleştirme katmanında geride.** Kategorinin trading kanadı (QC, ALP,
TV, FT, HB, IBKR) Meridian'ın zaten yaptığı işleri farklı biçimlerde yapıyor; asıl boşluk **ajan
gözlemlenebilirliği** kanadında: bir kararı tek eksende geri sarma, maliyeti atfetme, reddedilenin
karnesini tutma, regresyonu örnek düzeyinde gösterme ve geri-almanın sicilini yayımlama. Bu beşi
de yeni veri istemiyor — **yeni bir birleştirme istiyor.**

---

## KAYNAKLAR — hepsine erişim tarihi 2026-08-06

Bölüm A işe göre birleştirildiği için URL'ler satır içinde değil burada; her aile kendi
bloğunda. Bölüm B'nin Meridian tarafı URL taşımaz — kaynağı **bu depodaki koddur** ve satır
numaralarıyla metnin içinde verildi.

**QuantConnect** · docs.quantconnect.com üzerinden:
`/v2/cloud-platform/live-trading/results` · `/v2/cloud-platform/live-trading/reconciliation` ·
`/v2/cloud-platform/live-trading/getting-started` · `/v2/cloud-platform/live-trading/deployment` ·
`/v2/cloud-platform/live-trading/notifications` · `/v2/writing-algorithms/statistics/runtime-statistics` ·
`/v2/writing-algorithms/live-trading/charting-and-logging` · `/v2/research-environment/meta-analysis/live-analysis` ·
`/v2/cloud-platform/community/quant-league` · quantconnect.com/league/ ·
`/v2/cloud-platform/live-trading/brokerages/quantconnect-paper-trading`

**Composer** · help.composer.trade makaleleri: `/54-create-tutorial` · `/55-discover-tutorial` ·
`/63-trading-period` · `/65-how-does-composer-trade` · `/67-backtest-basics` · `/76-threshold-trading` ·
`/94-tutorial-following-symphonies` · `/149-why-is-my-symphony-holding-cash` · `/19-sharpe-ratio` ·
`/21-annualized-return` · `/38-calmar-ratio` · api.composer.trade/docs/index.html ·
composer.trade/trading-strategies

**Alpaca** · docs.alpaca.markets: `/us/docs/paper-trading` · `/us/docs/account-plans` ·
`/us/docs/orders-at-alpaca` · `/docs/working-with-positions` · `/docs/account-activities` ·
`/us/docs/alpacas-cli` · `/us/reference/getaccountportfoliohistory-1` ·
alpaca.markets/learn/start-paper-trading · alpaca.markets/learn/how-to-trade-options-with-alpaca
*(pano etiketleri için ek üçüncü-taraf kaynak: tradingfinder.com/brokers/alpaca-markets/dashboard/ —
yalnız "Trade"/"Watchlist"/"Edit" etiketleri için, resmî değil, ayrıca işaretli)*

**TradingView** · tradingview.com: `/support/solutions/43000764138-…-strategy-report-how-to-start/` ·
`/support/solutions/43000628599-strategy-properties/` · `/support/solutions/43000777193-initial-capital/` ·
`/support/solutions/43000666265-how-deep-backtesting-works/` · `/support/solutions/43000666199-what-is-deep-backtesting/` ·
`/support/solutions/43000481368-strategy-alerts/` · `/support/solutions/43000529348-how-to-configure-webhook-alerts/` ·
`/support/solutions/43000516466-paper-trading-main-functionality/` ·
`/support/folders/43000549214-…paper-trading/` · `/support/solutions/43000482760-…several-positions-per-symbol/` ·
`/pine-script-docs/concepts/strategies/` · `/charting-library-docs/latest/trading_terminal/account-manager/` ·
`/the-leap/` · `/blog/en/tradingview-leap-by-tradestation-results-52831/` · `/blog/en/the-leap-by-adx-winners-57396/`

**Freqtrade / FreqUI** · freqtrade.io/en/stable/: `rest-api/` · `telegram-usage/` · `freq-ui/` ·
`plugins/` · `configuration/` · `stoploss/` · `backtesting/` · `strategy-customization/` ·
`bot-basics/` · `utils/` · `faq/`

**Hummingbot** · hummingbot.org: `/client/` · `/client/status/` · `/client/history/` ·
`/client/start-stop/` · `/client/user-interface/` · `/client/commands-shortcuts/` ·
`/client/global-configs/kill-switch/` · `/client/global-configs/paper-trade/` · `/dashboard/` ·
`/dashboard/instances/` · `/hummingbot-api/routers/`

**Interactive Brokers TWS** · interactivebrokers.github.io/tws-api/: `order_submission.html` ·
`margin.html` · `executions_commissions.html` · ibkrguides.com/traderworkstation/:
`order-status-colors.htm` · `activity-panel.htm` · `trade-log.htm` · `monitor-order-progress.htm` ·
`check-margin-pre-order.htm` · `manage-orders-with-tws-algos.htm` · `understanding-risk-navigator.htm` ·
`real-time-activity-monitoring.htm`

**Numerai** · docs.numer.ai: `/` · `/numerai-tournament/submissions` ·
`/numerai-tournament/submissions/model-uploads` · `/numerai-tournament/scoring` ·
`/numerai-tournament/scoring/meta-model-contribution-mmc` · `/numerai-tournament/staking` ·
`/numerai-tournament/models` · `/numerai-signals/scoring`

**eToro** · etoro.com: `/copytrader/` · `/copytrader/how-it-works/` ·
`/customer-service/copytrading-risks/` · `/about/pro-investor-program-preview/`
*(Risk Score formülü ve "copy figures" alan listesi help.etoro.com'da — tüm varyantlar **403**
döndü; bu iki kalem "ölçülemedi" olarak işaretlendi, tabloya alınmadı.)*

**Ajan gözlemlenebilirliği** ·
docs.langchain.com/langsmith/: `observability-concepts` · `threads` · `filter-traces-in-application` ·
`dashboards` · `annotation-queues` · `rules` · `compare-experiment-results` ·
`prompt-engineering-concepts` · `alerts` · `engine-overview` · `log-llm-trace` ·
`add-human-in-the-loop` · docs.langchain.com/oss/python/langchain/human-in-the-loop ·
docs.smith.langchain.com/observability/how_to_guides/online_evaluations ·
langfuse.com/docs/: `observability/features/sessions` · `observability/features/agent-graphs` ·
`observability/features/token-and-cost-tracking` · `observability/best-practices` ·
`evaluation/overview` · `evaluation/evaluation-methods/llm-as-a-judge` ·
`evaluation/dataset-runs/datasets` · `prompt-management/overview` ·
`metrics/features/custom-dashboards` · `metrics/features/monitors` ·
github.com/open-telemetry/semantic-conventions-genai (+ `docs/gen-ai/gen-ai-metrics.md`) ·
docs.agentops.ai/v2/introduction · wandb.ai/site/weave/

**Meridian tarafı (kod, bu depo):** `meridian/api.py` · `meridian/analytics.py` ·
`meridian/counterfactual.py` · `meridian/rollback.py` · `meridian/hermes.py` · `meridian/notify.py` ·
`meridian/marketview.py` · `meridian/spend.py` · `meridian/codelaw.py` ·
`meridian/adapters/alpaca.py` · `meridian/web/app.js` · `meridian/web/index.html` ·
`state/*` (canlı defterler) · `DESIGN.md` · `PRODUCT.md` · `ROADMAP.md` ·
`docs/QC-ENTEGRASYON-DEGERLENDIRMESI.md` · `docs/UX-SADELESTIRME-DENETIMI-2026-08-06.md`
