# ARAŞTIRMA — KALAN SKILL'LERİ ETKİN KULLANMANIN YOLU (2026-08-13)

**Operatör talimatı:** *"kalan skilleri daha efektif kullanmanın yolunu da aramalıyız."*

**Kapsam:** salt-okuma araştırma/tasarım. Kod YAZILMADI, repo koduna DOKUNULMADI, git komutu
koşulmadı. Canlı A1'e (`ubuntu@130.61.126.87`, `/opt/meridian`) yalnız salt-okuma Python betikleriyle
bakıldı. Her iddia bir `dosya:satır`, bir SKILL.md alıntısı ya da bir canlı ölçüm çıktısıyla bağlıdır.
Ölçülemeyen her kalem **ÖLÇÜLEMEDİ + neden** olarak yazılıdır.

**Ön koşul belge:** `docs/DENETIM-SKILL-CAGRI-IZI-2026-08-13.md` (bugünkü çağrı-izi denetimi). Bu
belge onun ÜZERİNE kurulur: denetim "kapasite atıl" dedi, bu belge "atıl kapasiteyi hangi karara,
hangi mekanizmayla, hangi metrikle bağlarız" sorusunu ölçerek cevaplar.

---

## 0. YÖNETİCİ ÖZETİ — beş ölçülmüş cümle

| # | Bulgu | Sayı | Kaynak |
|---|---|---|---|
| 1 | Aktif skill'lerin çoğu **sinyal değil bağlam/metodoloji** üretir — bu yüzden "aday listesi" beklentisiyle bakınca boş görünürler | 30 enabled: 9 sinyal · 10 bağlam · 5 kapı/teşhis · 6 metodoloji-rubrik | canlı `skills_registry.json` + 31 SKILL.md |
| 2 | LLM'e sorulan **9 ayrı karar noktası** var; bunların **7'si skill ön-yüklüyor**, 1'i boş liste ile çağırıyor, 1'i (Claude yolu) skill gövdesi HİÇ almıyor | 9 nokta | `hermes.py`, `nous_eval.py`, `skill_evolve.py` |
| 3 | Ana danışma yolu (`review`) **fiilen ölü**: son 7 günde 788 `agent_call`, 385 boş, tek 1 başarılı görüş | `sonuc_sinifi`: bos 750 / dolu 20 | canlı `agent_calls.jsonl` |
| 4 | **Ölçüm motoru hazır ve dolu duruyor:** sonucu bilinen ama görüşü olmayan **91 gün / 93 plan** kuyrukta; bugünkü bütçeyle bir koşuda 47 gün eritilebilir | kuyruk 93 · `backfill_budget().tavan = 47` | canlı `trade_plans.jsonl` × `trades.jsonl` |
| 5 | Terfi kapısının önündeki gerçek engel örneklem DEĞİL, **kova dengesizliği**: `destekle` kovası **BOŞ** | `n_pairs=4` · destekle 0 · çekimser 3 · karşı 1 · `r_gap=null` | canlı `llm_calibration.json` |

**HÜKÜM.** "Kalan skilleri etkin kullanmak" bugün **yeni skill devreye almakla değil, var olan tek
ölçülebilir karar noktasını (görüş kalibrasyonu) çalışır hale getirmekle** başlar. 93 satırlık dolgu
kuyruğu, bir skill kompozisyonu A/B'sini **~20 dakikalık ajan zamanı ve 93/150 RPD ile** hükme
bağlayabilecek tek mekanizmadır. Diğer tüm eşleşmeler ya ölçülemez (bugün karşılığı olan metrik yok)
ya da ölçüm motoru boş (aday üretimi 2026-08-07'den beri durmuş).

---

## [A] ENVANTER — her aktif skill NE ÜRETİR, NEREYE BAĞLANABİLİR

### A.0 Sayım künyesi (canlı, `state/skills_registry.json`)

```
kayıt toplamı 67 · enabled 30 · aktif ama enabled=False 1 (institutional-flow-tracker, FMP kapısı)
arşiv 36 (skills/_emekli/) · korumalı 5 · motor-içi (ENGINE_IMPLEMENTED) 13
```

`skill_gorus.evren()` canlı çıktısı: `{"evren": 8, "arsiv": 36, "korumali": 5,
"llm_baglamli_motor_kosturmuyor": 18}`.

**ÜRETİM SINIFI tanımları** (bu belgenin ayrımı — kayıt defterinde böyle bir alan YOKTUR, sınıf
SKILL.md'nin `## Output` / `## Output Format` bölümünden okunarak atanmıştır):

* **SİNYAL** — ticker düzeyinde aday/plan üretir (screener).
* **BAĞLAM** — piyasa/rejim düzeyinde skor ya da durum üretir (0-100 kompozit, rejim etiketi).
* **KAPI/TEŞHİS** — bir kararı bloklar ya da bir veri/pozisyon kümesini denetler.
* **METODOLOJİ** — çalıştırılacak bir rubrik/kriter listesi üretir; çıktısı hüküm değil, hüküm VERME
  BİÇİMİDİR.

### A.1 Envanter tablosu (30 enabled + 1 kapalı-aktif)

`-s` = Meridian isteme bastı (`use_count`) · `view` = LLM kendi açtı (`view_count`) — kaynak canlı
`~/.hermes/skills/.usage.json`, 2026-08-13T18:31 anlık.

| # | skill | sınıf | girdi | çıktı biçimi | motor | `-s` | `view` |
|---|---|---|---|---|---|---|---|
| 1 | **vcp-screener** | SİNYAL | S&P500 evreni + OHLCV (FMP req) | aday listesi + 3-fazlı pivot/tightness skoru; tarihsel modda ileri-sonuç istatistiği | ✅ | 1097 | **3** |
| 2 | **pullback-screener** | SİNYAL | trend içi OHLCV | `strategy.evaluate_pullback` motor-yerleşik; SKILL.md yalnız 697 bayt, `scripts/` YOK | ✅ | 1113 | 0 |
| 3 | **stockbee-momentum-burst-screener** | SİNYAL | OHLCV (FMP req) | %4 kırılım / aralık-genişleme / hacim skorlu aday listesi | ✅ | 421 | 0 |
| 4 | **stockbee-exhaustion-hammer-screener** | SİNYAL | OHLCV (FMP req) | undercut-reclaim + fitil geometrisi skorlu aday listesi | ✅ | 712 | **5** |
| 5 | **stockbee-episodic-pivot-analyzer** | SİNYAL | katalizör JSON + OHLCV | EP-günü skoru + PEAD'e devir kuralı | ✅ | 12 | **2** |
| 6 | **pead-screener** | SİNYAL | FMP kazanç takvimi ya da EP çıktısı | haftalık mum + kırmızı-mum geri çekilme sinyali | ✅ | **hiç** | 0 |
| 7 | **finviz-screener** | SİNYAL | doğal dil → FinViz filtre URL'i | CSV satırları / tarayıcı; Meridian'da yalnız **evren genişletici** | ✅ | **hiç** | 0 |
| 8 | **canslim-screener** | SİNYAL | FMP req (temel veri) | CANSLIM 7-bileşen raporu | ✗ (motor `evaluate_canslim` **daima None** — PIT temel yok) | **hiç** | 0 |
| 9 | **parabolic-short-trade-planner** | SİNYAL | FMP req + intraday 5dk | 3 fazlı short planı + FSM tetik çözümü | ✗ | **hiç** | 0 |
| 10 | **market-environment-analysis** | BAĞLAM | küresel piyasa/döviz/emtia | risk-on/off değerlendirmesi + rapor | ✗ | 1131 | 0 |
| 11 | **macro-regime-detector** | BAĞLAM | çapraz-varlık oranları (RSP/SPY, getiri eğrisi, kredi) | 5 rejim sınıfı (Concentration/Broadening/Contraction/Inflationary/Transitional) | ✗ | 18 | 0 |
| 12 | **market-breadth-analyzer** | BAĞLAM | TraderMonty açık CSV | 6-bileşenli 0-100 genişlik skoru (anahtarsız) | ✗ | 18 | 0 |
| 13 | **uptrend-analyzer** | BAĞLAM | Monty Uptrend Ratio CSV | 5-bileşenli 0-100 skor + 7 seviyeli bölge | ✗ | **hiç** | 0 |
| 14 | **market-top-detector** | BAĞLAM | FMP + **WebSearch** (breadth, put/call) | 6-bileşenli 0-100 tepe olasılığı + risk bölgesi | ✗ | **hiç** | 0 |
| 15 | **ibd-distribution-day-monitor** | BAĞLAM | QQQ/SPY OHLCV (FMP req) | d5/d15/d25 dağıtım günü sayacı + NORMAL/CAUTION/HIGH/SEVERE | ✗ | **hiç** | 0 |
| 16 | **theme-detector** | BAĞLAM | FinViz (+FMP opsiyonel) | tema listesi + yaşam-döngüsü analizi (JSON rapor) | ✗ | **hiç** | 0 |
| 17 | **economic-calendar-fetcher** | BAĞLAM | FMP req | ham JSON olay listesi → asistan etkiyi değerlendirip MD üretir | ✗ | **hiç** | 0 |
| 18 | **earnings-calendar** | BAĞLAM | FMP req | haftalık kazanç MD tablosu (>$2B) | ✅ | **hiç** | 0 |
| 19 | **exposure-coach** | BAĞLAM→KARAR | **yukarı-akış skill JSON'ları** (breadth, uptrend, regime, top_risk…) | `{exposure_ceiling_pct, bias, participation, recommendation: NEW_ENTRY_ALLOWED\|…, component_scores, inputs_missing}` | ✗ | **hiç** | 0 |
| 20 | **institutional-flow-tracker** | BAĞLAM | 13F (FMP req) | kurumsal akım + güvenilirlik notu | ✗ | *enabled=False* | — |
| 21 | **pre-trade-discipline-gate** | KAPI | plan + checklist + devre-kesici artefaktı | JSON karar + `checklist_answers` + jurnal satırı | ✅ 🛡 | 1132 | **1** |
| 22 | **position-sizer** | KAPI/HESAP | giriş/stop/risk parametreleri | pay adedi (fixed-fractional / ATR / Kelly) + sektör yoğunluk kontrolü | ✅ 🛡 | 1131 | 0 |
| 23 | **drawdown-circuit-breaker** | KAPI | trader-memory state (gerçekleşen P&L) | `COOLDOWN/HALTED/TRADING_HALTED` kararı | ✅ 🛡 | **hiç** | 0 |
| 24 | **portfolio-manager** | TEŞHİS | Alpaca MCP/REST | tahsis + risk + rebalans önerisi | ✅ 🛡 | 18 | 0 |
| 25 | **data-quality-checker** | TEŞHİS | analiz dokümanı/metin | JSON bulgu (ERROR/WARNING) + MD rapor — **advisory** | ✅ 🛡 | **hiç** | 0 |
| 26 | **backtest-expert** | METODOLOJİ | strateji kuralları + backtest sonucu | `reports/backtest_eval_*.json` — boyut skorları + kırmızı bayraklar + hüküm | ✗ | 18 | 0 |
| 27 | **edge-strategy-reviewer** | METODOLOJİ | `strategy_drafts/*.yaml` | `review.yaml` — **8 ağırlıklı kriter + PASS/REVISE/REJECT + confidence** | ✗ | 18 | 0 |
| 28 | **strategy-pivot-designer** | METODOLOJİ | backtest yineleme geçmişi | durgunluk tespiti + yapısal pivot önerileri | ✗ | **hiç** | 0 |
| 29 | **edge-pipeline-orchestrator** | METODOLOJİ | uçtan uca edge boru hattı | aşama koşumu + dışa aktarım | ✗ | **hiç** | 0 |
| 30 | **weekly-performance-digest** | METODOLOJİ | kapanmış tez YAML'ı (**Meridian'da HİÇ olmadı**) | rapor şablonu + **kohort etiketleri** + süreç-uyum rubriği | ✗ | **hiç** | 0 |
| 31 | **trading-skills-navigator** | META/YÖNLENDİRME | doğal dil hedef + kısıtlar | kararlı JSON: `primary_workflow`, `setup_bundle`, `suggested_skills`, `honest_gap` | ✗ | **hiç** | 0 |

🛡 = `skills.PROTECTED` (asla gölgelenmez) · ✅ = `skills.ENGINE_IMPLEMENTED` (deterministik motor
gerçekten koşturur).

### A.2 Envanterden çıkan üç ölçülmüş gerçek

**(a) SKILL.md'lerin çoğu boş kabuk DEĞİL — kendi kodu var.** 31 skill dizininin **30'unda
`scripts/` klasörü** duruyor (tek istisna `pullback-screener`: yalnız 697 baytlık SKILL.md, çünkü
mantığı `strategy.evaluate_pullback` içinde motora gömülü). Yani "skill = doküman" tezi **yanlıştır**;
skill = *doküman + çalıştırılabilir betik*.

**(b) Ama hiçbiri Meridian'ın motoruna bağlı DEĞİL.** 31 SKILL.md'de `meridian/*.py`,
`strategy.py`, `ENGINE_IMPLEMENTED`, `ARMED_SETUPS` desenlerinin toplam eşleşmesi: **3**
(`trading-skills-navigator` 1, `pullback-screener` 1, `pead-screener` 1 — üçü de anlatı atfı, kod
sözleşmesi değil). Ters yön de aynı: `meridian/skills.py:56` ölçümü — *"`strategy.py` içinde `skills`
geçen SIFIR satır var"*. Tek yapısal bağ `_SCREENER_BY_SETUP` sözlüğüdür
(`meridian/skills.py:85-90`) ve o da yalnız **atıf etiketi** üretir, davranış üretmez.

**(c) Sınıf, kullanımı belirlemiş.** `-s` ile isteme giren 13 skill'in 7'si SİNYAL/KAPI sınıfından;
hiç girmeyen 17'nin 12'si BAĞLAM ya da METODOLOJİ sınıfından. Ön-yükleme seçici
(`hermes._skill_preload`, `hermes.py:3055`) kanıt-güdümlüdür ve kanıt yalnız SİNYAL sınıfında birikir
(`analytics.skill_attribution` ancak `skill_chain`'e yazılmış screener'lar için `avg_r` üretir). Yani
**bağlam ve metodoloji skill'leri, ölçülemedikleri için ön-yüklenmiyor; ön-yüklenmedikleri için de
ölçülemiyorlar.** Kısır döngünün adı budur ve [D] pilotu tam olarak bu döngüyü kırmak için tasarlandı.

---

## [B] MERİDİAN'IN LLM'E SORDUĞU YERLER — 9 karar noktası

Ortak taşıma: `hermes._agent_call` (`hermes.py:1872`) → `_agent_chat_cmd` (`hermes.py:1836`) →
`hermes chat --accept-hooks -Q -q <istem> -s <skill> … --model <model>`. Ön-yükleme tavanı **8**
(`_skill_preload`, `hermes.py:3118`).

| # | nokta | kod | `kind` | ön-yüklenen | girdide NE veriliyor | çıktıdan NE bekleniyor | hangi kapıya gidiyor | bugünkü canlı hâl |
|---|---|---|---|---|---|---|---|---|
| **D1** | **Aday ikinci görüşü** | `hermes.review_candidates` `hermes.py:3272` | `review` | `_skill_preload("review", setups)` → bugün 6 ad | `{date, regime, plans:[ticker, setup, entry_trigger, stop, profit_target, size_r, score, gate_verdict, gate_reasons, skill_chain]}` + `_opinion_history()` (son 5 görüş↔sonuç) | `{"reviews":[{ticker, opinion:"destekle\|çekimser\|karşı", note<=200}]}` | `candidate_review.json` → `trade_plans.llm_opinion` → **terfi sonrası** `loop._llm_veto_filter` (`loop.py:1006`): yalnız REVIEW+karşı dolum vetosu | **fiilen ölü** — 739 çağrı, 281 iz `bos` / 1 `dolu`; son 7 günde 1 başarılı görüş, 1.397 `candidate_review_backlog` |
| **D2** | **Geçmiş görüş dolgusu** | `hermes._review_plans_batch` `hermes.py:3485` · `backfill_opinions` `:3521` | `backfill` | D1 ile AYNI liste | D1 ile aynı payload, **`regime_at_plan`** ile; sonuç (`r_multiple`) **bilinçle gizli** | D1 ile aynı JSON | `_stamp_llm_opinions` → `trade_plans` + `cf_open` → `analytics.llm_opinion_calibration` | **ÇALIŞIYOR** — 3 çağrı, **3/3 `dolu`**; kuyruk 91 gün / 93 satır; tavan 47/koşum |
| **D3** | **Keşif slotu sıralaması** | `hermes.rank_explore` `hermes.py:3453` | `explore` | `_skill_preload("explore", setups)` — D1 ile aynı | kapıyı GEÇMİŞ GO adaylarının `ticker/setup/score/rr` menüsü | **tek ticker sembolü**, düzyazı yok | 0.25R mikro pozisyon slotu; cevap yoksa skor sırası (fail-open) | **ölçülemez** — 102 `explore_slot_llm_pick` olayı var ama `trades.jsonl`'de `exploration=True` işlem sayısı **0** |
| **D4** | **Hipotez üretimi (yerel ajan)** | `hermes._propose_nous_local` `hermes.py:2121` → `propose_with_llm` `:3702` | `proposal` | `_skill_preload("proposal")` → küratörlü 8 ad | `build_context()` (`hermes.py:178`) + `evidence_pack()` + `_exploration_sections()`; içinde **`skill_library`** = ölçülen skill'lerin `avg_r/n/n_cf/cf_avg_r`'si + ölçülmeyenlerin yalnız adı (`_skill_library`, `hermes.py:221`) | `HYP_SCHEMA` JSON: tek değişken `{variable, new, rationale, predicted_delta, confidence…}` | `reflect.submit()` → OOS walk-forward kapısı → `shipped` / `rejected_by_*` | **ÇALIŞIYOR** — son 14 izin 13'ü `dolu`; ama **13 yerel-ajan önerisinin 0'ı ship etti** |
| **D5** | **Eksen-2 skill eylemi** (D4'ün İKİNCİ çıktı kanalı) | `HYP_SCHEMA.properties.skill/action` `hermes.py:76-83` | (D4 ile aynı çağrı) | (aynı) | (aynı) | `{skill, action: shadow\|activate\|lean_in, rationale}` | `skill_recommendations.jsonl` → pano gelen kutusu → **operatör onayı** (`api.py:1778`) | çalışıyor — 14 kayıt: 8 `applied`, 6 `pending`; son: `pullback-screener` shadow (uygulandı 2026-08-12) |
| **D6** | **Skill revizyon taslağı** | `skill_evolve.draft_revision` `skill_evolve.py:155` | `skill_revision` | **sabit tek ad**: `("backtest-expert",)` | mevcut SKILL.md'nin ilk 4.000 karakteri + `skill_attribution` satırı + `exit_efficiency` + `lessons.md` kuyruğu | `<REVISED>…</REVISED>` tam SKILL.md + `RATIONALE:` tek satır | `SKILL.md.v2-draft` → pano → **operatör onayı** | **atıl** — `skill_revision_week_failed` 436 kez (son: 2026-07-21, `AttributeError`), bugün `weak_skills()` = `[]` (eşik: n≥15 **ve** avg_r≤-0,10; hiçbir skill karşılamıyor) |
| **D7** | **Haftalık sistem değerlendirmesi** | `nous_eval.haftalik_degerlendirme` → `hermes.chain_text` `nous_eval.py:695` | `system_eval` | **`preload=()` — BOŞ** | `analytics.system_telemetry()` (haftalık telemetri) + `onceki_akibet()` (kendi karnesi) | yapılandırılmış öneri listesi (`sekil`: tasarım/parametre/çekirdek_hakkında; `oncelik`) | `nous_fisler.json` + hermes kuyruğu + anayasal red süzgeci | çalışıyor — 3 hafta koştu (W31 `kosulamadi`, W32 5/5 kabul, W33 4/4 kabul), 8 fiş |
| **D8** | **Arka plan öneri turu** | `hermes._reflect_once_govde(background=True)` `hermes.py:3957` | `proposal` | D4 ile aynı | D4 ile aynı | D4 ile aynı | ek kapı: `hermes_bg_proposal_rejected` (`hermes.py:4002`) — global/farklı-rejim öneri REDDEDİLİR | D4 ile ortak defter; ayrı sayaç yok |
| **D9** | **Hipotez üretimi (Claude API)** | `hermes.propose_with_claude` `hermes.py:344` | — | **YOK** — `-s` yolu Claude'da mevcut değil; skill bilgisi yalnız `build_context().skill_library` METADATA'sı | D4 ile aynı bağlam, şema API tarafında zorlanır | `HYP_SCHEMA` JSON | D4 ile aynı kapı | **kapalı** — `brain_availability().claude.credentials = false`; tarihsel: **4 shipped / 8 öneri (tek ship eden kaynak)** |

### B.1 Karar noktalarının bütçe künyesi (canlı `agent_calls.jsonl`)

| `kind` | n | medyan süre | istem boyutu (medyan kr) | sonuç |
|---|---|---|---|---|
| `review` | 739 | 10.905 ms | 1.099 | ezici çoğunluk boş |
| `backfill` | 3 | 12.404 ms | 873 | 3/3 dolu |
| `proposal` | 16 | 20.843 ms | 50.791 | 13/14 dolu |
| `nous_eval` | 1 | 7.473 ms | 49.744 | 1/1 dolu |

Kota: `quota_state()` → `rpd 150 · rpm 6 · kullanılan 9 · kalan 141`.
Türetilen dolgu tavanı: `backfill_budget()` → `47` (`max(1, floor(141 × 0,333))`).

**Ön-yükleme slotunun gerçek bedeli ÖLÇÜLDÜ.** Sistem istemi 106.558 karakter; bunun 10.228'i skill
KATALOĞU, kalanın büyük kısmı **8 ön-yüklenen skill'in SKILL.md gövdesinin tam metni**
(denetim §1.2). Bugünkü `review` ön-yüklemesinin 6 gövdesi toplam **32.700 bayt**
(exhaustion-hammer 5.409 + vcp 7.936 + market-env 6.764 + pre-trade 5.753 + position-sizer 6.141 +
pullback 697) ≈ **~8k token/çağrı**. Yani bir slot, skill'in büyüklüğüne göre **~0,2k–6k token**
arasında bir kalemdir (en küçük: pullback 697 B; en büyük aday: canslim 25.606 B).

---

## [C] EŞLEŞTİRME MATRİSİ — hangi skill hangi karar noktasında

**KARTIN EN SIKI KURALI:** ölçülemeyen eşleşme ÖNERİLMEZ. Aşağıda önce **kullanılabilir metrik
envanteri** yazılıdır; matrise yalnız bu envanterden bir satıra bağlanabilen eşleşmeler girmiştir.
Ölçülemeyenler C.3'te adıyla ve nedeniyle reddedilmiştir.

### C.1 Bugün var olan metrikler (kullanılabilir ölçüm envanteri)

| kod | metrik | nerede | bugünkü değeri | neyi ölçebilir |
|---|---|---|---|---|
| **M1** | `llm_calibration.json`: `n_pairs`, `buckets{destekle,çekimser,karşı}{n,win_rate,avg_r}`, `r_gap`, `promoted` | `analytics.py:1074` | `n_pairs=4` · destekle **0** · çekimser 3 · karşı 1 · `r_gap=null` · `promoted=false` | D1/D2 görüşünün SİNYAL taşıyıp taşımadığı |
| **M2** | `hermes_result` olayı / `hypotheses.jsonl.status` (kaynak kırılımlı) | `hermes.py:4012` | claude 4 shipped/8 · **hermes:nous 0/6** · **hermes:gemini 0/7** · virgin 0/8 | D4/D8/D9 önerisinin kapıyı geçme oranı |
| **M3** | `skill_recommendations.jsonl` `pending`/`applied` | `api.py:1778` | 14 kayıt: 8 applied, 6 pending | D5 skill-eylem önerisinin **operatör kabul oranı** |
| **M4** | `analytics.skill_attribution()` — skill başına `n/avg_r/n_cf/cf_avg_r` | `analytics.py:79` | 7 skill ölçülü (`vcp` n=91, `pre-trade`/`position-sizer` n=97, `pullback` n=4, `exhaustion` n=1, `momentum_burst` n=1, `EP` n=0) | YALNIZ `skill_chain`'e yazılan screener'lar |
| **M5** | `skill_gorus` görüş defteri + kart (`KART_N_MIN=30`, `CI 0.95`, `FDR q=0.1`, rank-IC etkisi 0,05) | `skill_gorus.py` | yüzeyler: `aday-siralayici`, `cikis` ölçülüyor; `rejim`, `boyut`, `aday-uretec` ölçülmüyor | skill'in KARAR YÜZEYİNDEKİ ayrıştırıcılığı |
| **M6** | `nous_eval_runs.json` `n_uretilen/n_kabul/n_dusen` + `nous_fisler.json` `durum` | `nous_eval.py` | W32 5/5, W33 4/4, 8 fiş | D7 önerisinin kabul/düşme oranı |
| **M7** | `.usage.json` `use_count` / `view_count` | üçüncü taraf (`~/.hermes/skills/`) | 13 kayıt; toplam view **11** | **süreç** metriği: yüklendi mi / model kendi açtı mı |
| **M8** | `agent_calls.jsonl` `sure_ms`, `istem_kr`, `sonuc_sinifi` | `agent_telemetry.py` | B.1 tablosu | **bedel** |

**Metrik OLMAYAN, ama sıkça metrik sanılan:** `component_ic.json` skorun 8 HAM BİLEŞENİNİN IC'sini
ölçer (`rs, tight, vol, prox, rvol20, mom12_1, rmom, turnover21`) — **skill düzeyinde bir alanı
YOKTUR**. Bir skill'in katkısını `component_ic` ile ölçme önerisi bu belgede **reddedilmiştir**
(kartın ölçülebilirlik şartını karşılamaz).

### C.2 KABUL EDİLEN EŞLEŞMELER

Her satırda üç zorunlu alan doludur. Sıra, ölçülebilirlik gücüne göredir.

---

#### E1 — `edge-strategy-reviewer` × **D2 (dolgu görüşü)** ⭐ pilot adayı

* **MEKANİZMA (somut).** D2 istemi modelden 3-değerli bir hüküm ister (`destekle|çekimser|karşı`)
  ama **hükmü nasıl üreteceğini söyleyen tek satır yoktur**. `edge-strategy-reviewer` SKILL.md'si tam
  olarak bunu taşır: 8 ağırlıklı kriter (C1 Edge Plausibility 20, C2 Overfitting Risk 20, C3 Sample
  Adequacy 15, C4 Regime Dependency 10, **C5 Exit Calibration 10 — "Stop-loss, reward-to-risk"**,
  C6 Risk Concentration 10, **C7 Execution Realism 10**, C8 Invalidation Quality 5) ve **eşikli hüküm
  mantığı**: *"C1 or C2 severity=fail → immediate REJECT · confidence >= 70, no fail findings → PASS ·
  confidence < 35 → REJECT · Otherwise → REVISE"*. Bu üçlü (PASS/REVISE/REJECT) Meridian'ın
  (destekle/çekimser/karşı) üçlüsüne **birebir** oturur. C5 ve C7, D2 isteminin ZATEN taşıdığı
  alanlardan hesaplanabilir: `entry_trigger`/`stop`/`profit_target` → R:R, `gate_reasons` → icra
  gerçekçiliği. Yani skill, mevcut payload'a **yeni veri değil, karar kuralı** ekler — dış veri
  bağımlılığı YOK (`api_free=yes`, kayıt defteri).
* **ÖLÇÜLEBİLİRLİK.** **M1.** Ana ölçüt `r_gap = avg_r(destekle) − avg_r(karşı)`; ikincil ölçütler
  kova dolulukları (`destekle.n`, `karşı.n` — terfi eşiği her ikisinde ≥8) ve `çekimser` payı.
  Kol-A (bugünkü 6'lı ön-yükleme) ile Kol-B (6 + bu skill) aynı kuyruk üzerinde koşulur; ölçüm
  `analytics.llm_opinion_calibration()`'ın ZATEN yazdığı alanlardan okunur, **yeni metrik
  gerekmez**.
* **BEDEL.** SKILL.md **3.553 bayt** (~0,9k token) — envanterdeki **en ucuz metodoloji skill'i**.
  Bugünkü `review` ön-yüklemesi 6 slot kullanıyor, tavan 8 → **boş slot var, kimse düşmez**.
  46 çağrılık bir kolda toplam ek yük ≈ **41 KB ≈ 10k token**. Süre: `backfill` medyanı 12,4 sn;
  ek gövde ölçülebilir bir gecikme eklemez (istem 873 kr → ~4,4k kr; hâlâ `proposal` isteminin
  1/10'u). Kota: kol başına ~46 RPD (bütçe 150).
* **KAYIT ŞERHİ.** Bu skill kayıt defterinde `mode: available` (`active` değil) ama `enabled: true`
  ve `use_count = 18` — yani `proposal` yolunda **fiilen ön-yükleniyor**. `_skill_preload` süzgeci
  yalnız `enabled`e bakar (`hermes.py:3084`), `mode` alanına değil; ön-yükleme engeli YOKTUR.
  Ayrıca `fmp=-`, `api_free=yes` → sprint budama kümesinin (E.3) dışındadır.

---

#### E2 — `weekly-performance-digest` × **D2 (dolgu görüşü)** ⭐ pilot adayı

* **MEKANİZMA (somut).** Ölçülen arıza: **`destekle` kovası boş** (M1). Model, üçlü enumdan **hiç
  risk almayan** seçeneği (`çekimser`) seçiyor — ve `_opinion_history` (`hermes.py:3394`) yalnız
  `destekle`/`karşı`yı *isabet/yanılgı* diye etiketlediği için çekimser **asla yanılmıyor**. Bu
  skill'in içine katlanmış **kohort etiket sözlüğü** ayrımı zorlar: `STRONG_WINNER` (5 günlük getiri
  ≥ %8 veya MFE ≥ %12, stop yok) · `WORKED` (≥ %4 veya MFE ≥ %6) · `FAILED_STOP` · `FAILED_FADE`
  (≤ −%2, stop yok) · `CHOPPY_FAILURE` · `NEUTRAL` · `PENDING`. Bu 7 etiketin 6'sı **taahhütlüdür**;
  yalnız `NEUTRAL` kaçış sunar. Aynı SKILL.md'nin *"clean-process loss ≠ execution mistake"* kuralı
  da doğrudan D2'nin sorusudur (plan kurala uygunsa kayıp bir bulgu değildir).
* **ÖLÇÜLEBİLİRLİK.** **M1**, iki ölçütle: (i) `çekimser` payının düşüşü — bugünkü taban **3/4 =
  %75**; (ii) `destekle.n ≥ 8` ve `karşı.n ≥ 8` kova eşiklerinin dolması (terfi kuralının kendisi,
  `analytics.py:1069-1071`). Her ikisi de mevcut dosyadan okunur.
* **BEDEL.** SKILL.md **10.117 bayt** (~2,5k token). E1 ile birlikte Kol-B'nin ek yükü **13.670
  bayt ≈ 3,4k token/çağrı**; 46 çağrıda ≈ **157k token**. Slot: 6→8, tavan tam dolar, **hiçbir mevcut
  skill düşmez** (`_skill_preload` tavanı 8, `hermes.py:3118`).
* **DÜRÜST ŞERH.** Bu skill'in kendi betiği `state/theses/*.yaml` okur ve SKILL.md'nin kendisi
  yazıyor: *"Meridian has never had this directory"*. Yani **betiği koşturmak değil, rubriğini
  okutmak** önerilir; ön-yükleme (`-s`) tam da bunu yapar (gövde metni isteme basılır, betik
  koşmaz).

---

#### E3 — `backtest-expert` × **D4 (hipotez üretimi)**

* **MEKANİZMA (somut).** D4'ün TEK kapısı OOS walk-forward'dır ve **13 yerel-ajan önerisinin 13'ü de
  `rejected_by_backtest` ile düştü** (M2). `backtest-expert` SKILL.md'si bu kapının reddetme
  nedenlerini önceden adlandırır: *"Seek Plateaus, Not Peaks — Good: profitable with stop loss
  anywhere from 1.5% to 3.0%; Bad: only works with stop loss at exactly 2.13%"* ve `Common Failure
  Patterns` listesi (1 parameter sensitivity · 2 regime-specific · 4 small sample · 6
  over-optimization). Yani mekanizma: **öneriyi üretmeden önce kapının reddetme desenini okutmak.**
* **ÖLÇÜLEBİLİRLİK.** **M2** — kaynak kırılımlı ship oranı (`hermes_result` olayı). Bugünkü taban
  net: `hermes:nous` 0/6, `hermes:gemini` 0/7.
* **BEDEL.** **ZATEN ÖN-YÜKLÜ** (`_skill_preload("proposal")` küratörlü listesinin ilk adı,
  `hermes.py:3077`; `use_count=18`). Ek bedel **SIFIR**.
* **HÜKÜM: PİLOTA GİRMEZ.** Skill zaten yüklü ve sonuç 0/13. Yani bu eşleşme **ölçüldü ve işe
  yaramadı** — pilot değil, *negatif kanıt* satırıdır. Buradaki gerçek kaldıraç skill eklemek değil,
  D4'ün istem boyutudur (medyan **50.791 karakter**): bir sonraki turun sorusu "hangi skill" değil,
  "50k karakterin hangisi karara giriyor" olmalıdır.

---

#### E4 — `trading-skills-navigator` × **D1/D2 (görüş) ve D4 (öneri)**

* **MEKANİZMA (somut).** 2026-08-13'te SOUL.md kilidi açıldı: *"ANALİZ SIRASINDA ARAÇ KULLANMAK
  SERBEST — özellikle `skill_view`"* (canlı `~/.hermes/SOUL.md`, mtime 18:17:34Z). Artık model
  ön-yüklenmemiş 22 skill'i **kendi açabilir** — ama hangisini açacağını bilmiyor. Bu skill'in tek
  işi budur: doğal dil hedeften `primary_workflow` + `suggested_skills` + `honest_gap` döndüren
  **kararlı JSON öneri motoru**; SKILL.md'si *"It recommends and explains only"* diye sınırını da
  yazıyor (yetki devri riski yok).
* **ÖLÇÜLEBİLİRLİK.** **M7** — `.usage.json` `view_count` (ve `last_viewed_at`) **kol öncesi/sonrası
  farkı**. Bugünkü taban kesin: toplam `view_count = 11`, 4 skill'de. Kol-B'nin 46 çağrısı boyunca
  `view_count` toplamı artmıyorsa navigatörün etkisi **SIFIR ölçülür**.
* **BEDEL.** SKILL.md **11.871 bayt** (~3k token); slot alır. **Ayrıca gizli bedel ölçüldü:** her
  `skill_view` bir araç turudur ve `-Q` altında Meridian bunu göremez (`tool_calls = −1`, 770/770
  satır) → gecikme yalnız `sure_ms` üzerinden dolaylı ölçülür.
* **HÜKÜM: PİLOTA GİRMEZ (bu turda).** Gerekçe: iki değişken (rubrik + navigatör) aynı kolda
  ölçülürse hangisinin katkı verdiği ayrıştırılamaz. Navigatör **ikinci tur** adayıdır ve doğal yeri
  D1/D2 değil, **istemi zaten dev olan D4**'tür (orada slot rekabeti asıl sorundur).

---

#### E5 — `exposure-coach` × **D1 (canlı aday görüşü)**

* **MEKANİZMA (somut).** `pre-trade-discipline-gate` SKILL.md'sinin kural listesi şunu yazıyor:
  gate blokluyor eğer *"exposure-coach recommendation is `REDUCE_ONLY` or `CASH_PRIORITY`"*. Yani
  **Meridian'ın kendi kapı skill'i, exposure-coach'un çıktısını bir GİRDİ olarak beyan ediyor** ama
  o çıktı bugün hiç üretilmiyor (`-s` hiç, `last_run` null). exposure-coach `{exposure_ceiling_pct,
  bias, participation, recommendation: NEW_ENTRY_ALLOWED|…, inputs_missing}` üretir — D1 isteminde
  bugün `regime` alanı TEK KELİMEDİR (`trend_up`/`chop`/…); bu skill onu bir tavan + bir izin
  kararına çevirir.
* **ÖLÇÜLEBİLİRLİK.** **M1** (D1 hattı canlıysa) — görüş↔R eşleşmesi.
* **BEDEL.** SKILL.md 6.952 bayt; **ama asıl bedel veri**: skill `inputs_provided`/`inputs_missing`
  ile çalışır ve yukarı-akış (breadth, uptrend, regime, top_risk) JSON'ları Meridian'da
  üretilmiyor — girdisiz koşarsa `inputs_missing` dolu, güven düşük çıkar.
* **HÜKÜM: BU TURDA ÖLÇÜLEMEZ.** Gerekçe **canlı ölçüm**: D1 hattının girdisi yok — `candidates.jsonl`
  son satır **2026-08-07** (VLO), `pipeline_runs.jsonl` son satır **2026-08-12T20:44:58**. Aday
  üretilmeyen bir hatta ikinci görüş pilotu koşulamaz. Kalem, aday üretimi geri döndüğünde
  yeniden açılmalıdır.

---

#### E6 — `market-top-detector` · `uptrend-analyzer` · `market-breadth-analyzer` · `ibd-distribution-day-monitor` × D1/D2

* **MEKANİZMA.** Dördü de 0-100 kompozit **BAĞLAM** skoru üretir ve D1/D2'nin tek-kelimelik `regime`
  alanını zenginleştirir.
* **HÜKÜM: D2'DE MEKANİZMASI YOK — REDDEDİLDİ.** Gerekçe SKILL.md alıntılarıyla: `market-top-detector`
  *"WebSearch Access: Required to collect S&P 500 breadth (50DMA %) and CBOE Put/Call ratio data"* +
  *"All manually collected data should be from the most recent 3 business days"*; `uptrend-analyzer`
  *"Internet connection to fetch CSV data from GitHub"*; `market-breadth-analyzer` TraderMonty **güncel**
  CSV'si. Dolgu kuyruğunun **91 gününün 88'i 2023-2025 tarihli**tir — bu skill'ler o tarihler için
  **veri üretemez**. Ön-yüklemek yalnız token yakar ve modele elinde olmayan bir girdiyi ima eder
  (uydurma riski). D1 (bugünün adayı) için mekanizma geçerlidir; ama D1 bugün girdisizdir (E5).

---

#### E7 — `data-quality-checker` × D7 (haftalık sistem değerlendirmesi)

* **MEKANİZMA (somut).** D7 **`preload=()` ile, yani SIFIR skill ile** çağrılıyor
  (`nous_eval.py:696`) ve görevi telemetride *"ölçülmeyen mekanizmalar, kopuk kablolar, boş
  defterler"* aramak (`nous_eval.py:9`). `data-quality-checker` tam olarak bir **denetim rubriği**
  üretir: ölçek tutarsızlığı, gösterim hatası, tarih/gün uyuşmazlığı, tahsis toplamı hatası, birim
  uyuşmazlığı → JSON `finding` (ERROR/WARNING) + *"Advisory mode — flags issues as warnings for human
  review, not as blockers"*. D7'nin çıktı disiplini (fiş → operatör) ile aynı yetki seviyesindedir.
* **ÖLÇÜLEBİLİRLİK.** **M6** — `nous_eval_runs.json`'daki `n_uretilen / n_kabul / n_dusen` +
  `dusme_nedenleri`. Taban ölçülü: W32 5 üretildi / 5 kabul, W33 4/4, düşme nedeni yok.
* **BEDEL.** 5.942 bayt (~1,5k token); D7'de bugün **8 slotun 8'i boş**, rekabet yok. Kadans
  haftalık → yılda ~52 çağrı, kota etkisi ihmal edilebilir.
* **HÜKÜM: GEÇERLİ AMA İKİNCİ SIRA.** Ölçülebilir ve ucuz; ancak kadansı haftalık olduğu için hüküm
  **8 haftadan önce** verilemez (n=8 koşum). Pilot için fazla yavaş; kalıcı iyileştirme olarak
  önerilir.

---

### C.3 REDDEDİLEN EŞLEŞMELER — adıyla ve nedeniyle

| eşleşme | red gerekçesi (ölçülmüş) |
|---|---|
| herhangi bir skill × **D3 (keşif slotu)** | 102 `explore_slot_llm_pick` olayına karşılık `trades.jsonl`'de `exploration=True` işlem **0**. Sonuç metriği hiç doğmamış → katkı **ölçülemez**. |
| herhangi bir skill × **D6 (revizyon taslağı)** | `weak_skills()` canlıda **`[]`** (eşik n≥15 **ve** avg_r≤−0,10). Aday yok → mekanizma tetiklenmiyor; ayrıca `skill_revision_week_failed` 436 kayıt. |
| `canslim-screener` × herhangi | Motor karşılığı (`evaluate_canslim`) **daima `None` döner** — PIT temel veri yok (`skills.py:112-115`). Ölçülecek çıktı üretmiyor. |
| `portfolio-manager` / `institutional-flow-tracker` × D1/D2 | Alpaca/13F canlı hesap durumu gerektirir; D2 geçmiş tarihlidir → look-ahead riski. `institutional-flow-tracker` ayrıca `enabled=False`. |
| herhangi bir skill × **`component_ic`** ile ölçüm | `component_ic.json` **skorun 8 ham bileşenini** ölçer; skill boyutu yoktur. Kartın ölçülebilirlik şartını karşılamaz. |
| `theme-detector`, `economic-calendar-fetcher`, `parabolic-short-trade-planner`, `strategy-pivot-designer`, `edge-pipeline-orchestrator` × herhangi | Bu turda hiçbir karar noktasının çıktısına bağlanan bir metrik yok; katkıları ancak yeni bir defter açılırsa ölçülebilir → **öneri üretilmedi** (uydurma yasağı). |

---

## [D] EN KÜÇÜK İLK ADIM — pilot önerisi

> **PİLOT-S1: "Karar Rubriği" kolu — 2 skill × 1 karar noktası (D2), 91 günlük dolgu kuyruğu üzerinde
> A/B.**

### D.1 Neden D2 (dolgu), D1 (canlı review) değil

Üç ölçüm bunu zorunlu kılıyor:

1. **D1'in girdisi yok.** `candidates.jsonl` son satır 2026-08-07, `pipeline_runs.jsonl` son satır
   2026-08-12T20:44:58. Aday üretilmiyor.
2. **D1'in taşıyıcısı boğuk.** Son 7 gün: 788 `agent_call`, 385 `agent_call_empty`, 756
   `agent_call_cooldown`, 1.397 `candidate_review_backlog`, **1** başarılı `candidate_review`.
3. **D2 çalışıyor ve kuyruğu dolu.** `backfill` izleri **3/3 `dolu`**; kuyruk **91 gün / 93 satır**,
   hepsi **sonucu bilinen** (`r_multiple` dolu) ve **görüşü olmayan** planlar. Sonuç istemde
   **bilinçle gizlenir** (`hermes.py:3498`) → öngörü geçerliliği korunur, terfi sahte tetiklenmez.

### D.2 Tasarım

| kalem | Kol-A (kontrol) | Kol-B (deney) |
|---|---|---|
| ön-yükleme | bugünkü `_skill_preload("review", setups)` — 6 ad: `stockbee-exhaustion-hammer-screener, vcp-screener, market-environment-analysis, pre-trade-discipline-gate, position-sizer, pullback-screener` | aynı 6 **+ `edge-strategy-reviewer` + `weekly-performance-digest`** (toplam 8 = tavan) |
| kuyruk payı | tarih gün-numarası **tek** | tarih gün-numarası **çift** |
| beklenen n | ~45 gün / ~46 çift | ~46 gün / ~47 çift |

Kuyruk kompozisyonu ölçüldü: setup dağılımı `breakout_vcp 88 · pullback 4 · momentum_burst 1`;
tarih aralığı **2023-01-31 → 2026-08-06**; gün başına medyan 1 plan. Kollar aynı setup karışımını
alır (tarih paritesi setup ile ilişkisiz).

**Kol etiketi geriye dönük kurtarılabilir:** kol, planın `date` alanının fonksiyonudur, yani
`trade_plans.jsonl`'den yeniden türetilir. Bu yüzden pilot **v242'nin dağıtımını BEKLEMEZ** (v242
yine de gereklidir — bkz. [E]).

### D.3 Ölçüt — mevcut metrikten, yeni defter YOK

Birincil (M1, `analytics.llm_opinion_calibration()` çıktısı):

1. **`r_gap` = avg_r(destekle) − avg_r(karşı)**, kol başına. Terfi eşiği `LLM_PROMOTE_R_GAP = 0,3`
   (`analytics.py:1071`).
2. **Kova doluluğu**: `destekle.n ≥ 8` **ve** `karşı.n ≥ 8` (`LLM_PROMOTE_MIN_BUCKET = 8`).
3. **`çekimser` payı** — bugünkü taban **3/4 = %75**.

İkincil (M8): kol başına medyan `sure_ms`, `istem_kr`, `sonuc_sinifi` dağılımı.
Üçüncül (M7, **bedava**): koşum öncesi/sonrası `.usage.json` `view_count` toplamı — SOUL.md kilidinin
açılmasının davranışa yansıyıp yansımadığının **ilk ölçümü** (bkz. E.6).

### D.4 Kaç örneklemde hüküm verilir — ARİTMETİK ÖLÇÜLDÜ

Bugünkü `n_pairs = 4`. Kuyrukta **93** satır, hepsi sonucu bilinen ve `plan_id` taşıyan planlar
(`trades.jsonl`'de 97 işlemin **97'sinde** `plan_id` ve `r_multiple` dolu).

| adım | işlem | sonuç |
|---|---|---|
| bugün | — | `n_pairs = 4` |
| 1. koşum | `backfill_opinions()` tavan **47** gün (`max(1, floor(141 × 0,333))`) | ≈ **51** çift |
| 2. koşum (ertesi gün ya da kota tazelenince) | kalan 44 gün | ≈ **95** çift (taze pencere tavanı 100) |

* **n ≥ 30 eşiği 1. koşumda aşılır** (47 gün ≈ 47 yeni çift → 51 > 30).
* **Kol başına n ≈ 46**, yani her iki kol da tek başına `LLM_PROMOTE_MIN_PAIRS = 30` tabanını geçer.
* **Duvar saati:** `backfill` medyanı **12.404 ms**; 47 çağrı ≈ **9,7 dakika**; iki koşum ≈ **20
  dakika** ajan zamanı.
* **Kota:** 93 çağrı / 150 RPD. Tek güne sığar ama **iki güne bölünmesi önerilir** — RPM 6 sınırı ve
  `review` hattının artık payı için.
* **Token:** Kol-B'nin ek yükü 13.670 bayt/çağrı × ~46 = **~630 KB ≈ 157k token**. Kol-A ek yük
  **0**.

**İstatistik şerhi (uydurma yasağı).** n≈46/kol ile `r_gap` farkı **nokta tahmindir**; kolların
farkı güven aralığıyla okunmalıdır. Depoda hazır araç var: `skill_gorus.bootstrap_p` ve
`skill_gorus.bh_fdr` (`KART_CI = 0,95`, `KART_FDR_Q = 0,1`). Kartın eşiği **önceden** yazılmalı ve
sonradan değiştirilmemelidir.

### D.5 BAŞARISIZLIK ÖLÇÜTÜ — neyi görürsek "işe yaramadı" deriz

| kod | gözlem | hüküm |
|---|---|---|
| **F1** | `r_gap(Kol-B) ≤ r_gap(Kol-A)` | rubrik ön-yüklemesi **katkı vermedi** — dosya kapanır, ikinci skill denenmez |
| **F2** | Kol-B'de `destekle.n < 8` **veya** `karşı.n < 8` (Kol-A ile aynı hâlde) | hüküm **"ÖLÇÜLEMEDİ"** — arıza skill'de değil, enum teşvikindedir (bkz. E.7); pilot tekrarlanmaz, önce teşvik düzeltilir |
| **F3** | Kol-B'de `çekimser` payı ≥ Kol-A | rubrik **hedge davranışını kırmadı** — mekanizma iddiası çürüdü |
| **F4** | Kol-B'nin `sonuc_sinifi = bos` oranı, Kol-A'dan **≥10 puan** yüksek | uzayan istem **taşıyıcıyı bozuyor** — bedel katkıyı yiyor, kol geri alınır |
| **F5** | Her iki kolda `r_gap` **negatif** | danışman katmanı **ters sinyal** taşıyor — `llm_promoted()` yolu (loop.py:1006) kalıcı olarak kapalı tutulur ve bu bir **bulgudur**, başarısızlık değil |

**Pilotun "başarı" tanımı da dar yazılıdır:** `r_gap(Kol-B) − r_gap(Kol-A) ≥ 0,15` **ve** Kol-B'nin
her iki kovası ≥8. Bunun altındaki her sonuç "işe yaramadı"dır.

### D.6 Pilotun DEĞİŞTİRDİĞİ tek şey

`hermes._skill_preload("review", …)`'in döndürdüğü listeye iki ad eklemek — **tavan 8 zaten var, hiçbir
mevcut skill düşmez**, `CORE` koruması (`hermes.py:3095`) etkilenmez. Kapı yasası, silahlanma,
boyutlandırma, çıkış: **hiçbiri dokunulmaz**. `review_candidates`'ın yetki sınırı zaten yazılı ve
değişmez: *"bu inceleme yalnız bilgilendirir; kapı kararlarını (GO/REVIEW/NO_GO), silahlanmayı veya
emirleri ASLA değiştirmez"* (`hermes.py:3274`).

---

## [E] YAPISAL ENGELLER — çözülmeden pilotun anlamı daralır

### E.1 v242 çalışma ağacında duruyor: COMMIT EDİLMEMİŞ, DAĞITILMAMIŞ ⛔

**Ölçüm.** Yerel: `git diff --stat meridian/` → `agent_telemetry.py +56 · hermes.py +161 ·
skills.py +124 · sprint.py +45`. Canlı: `grep -c "skill_adlari" meridian/hermes.py` → **0**;
`grep -c "ajan_acilma_n" meridian/skills.py` → **0**. Canlı dosya damgaları: `hermes.py` 2026-08-13
13:41, `skills.py` 14:16 — v242 öncesi.

İçeriği (yereldeki hâliyle): `agent_call` olayına `skills=<liste>` + `skills_kirpildi_n`
(`hermes.py:2031-2035`), `agent_telemetry.skill_adlari` tek uygulama (`:130`),
`skills.ajan_kullanim()` → katalogda `ajan_yukleme_n` / `ajan_acilma_n` (`skills.py:381-464`),
`sprint.kum_havuzunda()` izolasyon kapısı (`sprint.py:287+`).

**Pilota etkisi:** PİLOTU BLOKLAMAZ (kol, tarihten türetilir — D.2), ama **v242 olmadan bu pilotun
dışındaki hiçbir çağrının hangi skill'i taşıdığı bilinemez.** Yani pilot sonrası genelleme yapılamaz.
**Öneri:** pilot koşumundan ÖNCE dağıtılsın; maliyeti sıfıra yakın, kazancı kalıcı.

### E.2 `.usage.json` üçüncü taraf kırılganlığı

Dosya sahibi Hermes CLI (`~/.hermes/hermes-agent/tools/skill_usage.py`): `bump_use` `-s` yolunda,
`bump_view` `skill_view()` içinde. Üç kırılganlık **ölçülü**:

1. **Kümülatif sayaç, gün kırılımı yok** — `use_count` + tek `last_used_at`. Bugünkü toplam 6.839.
   Pilotun `view_count` ölçümü bu yüzden **koşum öncesi/sonrası fark** olarak alınmalıdır (mutlak
   değer bilgi taşımaz).
2. **`agent.log` 5 MB'da döner** — tarihsel iz sessizce kaybolur; denetim penceresi 2026-07-30 →
   2026-08-13 ile sınırlıydı.
3. **Şema bizim değil.** v242'nin okuyucusu bunu doğru ele alıyor: dosya yoksa alanlar `None` +
   neden (`skills.py:360`), *"BU 'SIFIR KULLANIM' DEĞİLDİR"*. Bu sözleşme korunmalı.

### E.3 Sprint kum havuzu canlı skill dizinini hâlâ buduyor — BUGÜN de oldu

**Ölçüm (canlı symlink `mtime`'ları, 2026-08-13T18:31):** 26 skill `2026-07-30T14:55:03`, **4 skill
`2026-08-13T17:15:01`** — `canslim-screener`, `economic-calendar-fetcher`,
`ibd-distribution-day-monitor`, `parabolic-short-trade-planner`. Bunlar tesadüfi bir dörtlü değil:
kayıt defterinde `fmp=req` olan **ve** `PROTECTED` de `ENGINE_IMPLEMENTED` de OLMAYAN **tam
kümedir** (koruma kuralı `skills.py:184`). Kum havuzunda FMP anahtarı yoktur →
`reconcile_enablement` onları kapatır → `sync_agent_skills` paylaşımlı
`~/.hermes/skills` dizininden **söker**; canlı senkron bir sonraki turda onarır. O pencerede canlı
ajan bu dördünü **görmez** — katalogda yoktur, `skill_view` ile açılamaz.

`agent_skill_coverage()` şu an `{enabled: 30, linked: 30, missing: [], stale_linked: 0}` — yani
onarılmış hâli. Kapı (`sprint.kum_havuzunda()`) yerelde yazılmış, **canlıda yok** (E.1).

**Pilota etkisi:** Kol-B'nin iki skill'i (`edge-strategy-reviewer`, `weekly-performance-digest`)
`fmp=-`, `api_free=yes` olduğu için **budama kümesinin dışındadır** → pilot bu sızıntıdan
etkilenmez. Ama bir sonraki tur bir FMP skill'ini denerse etkilenir.

### E.4 SKILL.md ↔ kod bağı yok (ölçülü)

* 31 SKILL.md'de Meridian kod atfı: **3 eşleşme** (üçü de anlatı; sözleşme değil).
* `strategy.py` içinde `skills` geçen satır: **0** (`skills.py:56`).
* Kayıt defterini okuyanlar yalnız üç yer: `enabled_in()`, `reconcile_enablement()`, `catalog()` —
  hiçbiri motor davranışına girmez.
* Bunun ölçülmüş bedeli kayıtta duruyor: `lean_in` eylemi **öneri olarak** doğar ama uygulayıcısı
  yoktur — *"kayıt defterinde bu eylemi karşılayan alan bulunmuyor ve deterministik motor kayıt
  defterini okumuyor"* (`skills.py:73-75`). Canlı kanıt: `stockbee-exhaustion-hammer-screener`
  `lean_in` önerisi 2026-08-12'den beri `pending`.
* **Sonuç:** bir skill'in SKILL.md'sini iyileştirmek, o skill motor-içiyse bile **motorun
  davranışını değiştirmez**. LLM-bağlamlı skill'ler içinse SKILL.md **tek** etki yoludur. Bu, [C]'de
  METODOLOJİ sınıfının neden en yüksek kaldıraç olduğunun yapısal nedenidir: onların etkisi zaten
  yalnız metinden geçer, yani kopuk bağ onları **yaralamaz**.

### E.5 Görüş hattının besleyicisi durmuş

`candidates.jsonl` son satır **2026-08-07** · `pipeline_runs.jsonl` son satır
**2026-08-12T20:44:58** · `trade_plans.jsonl` son plan **2026-08-07** (1 adet).
`agent_calls.jsonl` ise 2026-08-13T17:26'ya kadar akıyor. İki katman **ayrışmış** durumda: LLM
konuşuyor, boru hattı susuyor. Bu kalem bu kartın kapsamı dışıdır ve **ÖLÇÜLMEDİ** (neden ayrı bir
iştir), ama D1 pilotunu imkânsız kıldığı için burada adıyla duruyor.

### E.6 SOUL.md kilidi AÇILDI ama HİÇ SINANMADI

`~/.hermes/SOUL.md` mtime **2026-08-13T18:17:34Z**; son `agent_call` **2026-08-13T17:26:34Z**;
ölçüm anı 18:31. Yani **kilidin açılmasından bu yana tek bir ajan çağrısı koşmadı.** Yeni metin:

> *"Meridian'dan gelen istekler tek bir JSON nesnesi ister. CEVABIN yalnızca istenen JSON olsun:
> düzyazı ekleme, dosya değiştirme yok. ANALİZ SIRASINDA ARAÇ KULLANMAK SERBEST — özellikle
> `skill_view`."*

Pilotun **bedava üçüncül ölçümü** budur: 93 çağrılık dolgu, kilidin davranışa yansıyıp yansımadığının
ilk gerçek sınavıdır. Taban kesin: `view_count` toplamı **11**, dördü dışında tüm skill'lerde 0.

### E.7 `çekimser` teşviki — terfinin önündeki asıl duvar

Yapısal ve ölçülü: `llm_opinion_calibration` terfi için **hem `destekle` hem `karşı` kovasında ≥8**
örnek ister (`analytics.py:1070`) ve `r_gap` yalnız ikisi de doluysa hesaplanır — bugün `r_gap =
null`, çünkü **`destekle` kovası boş**. Aynı anda `_opinion_history` (`hermes.py:3394`) modele kendi
karnesini gösterirken yalnız `destekle`/`karşı`yı *isabet/yanılgı* diye etiketliyor, `çekimser`
**"nötr"**. Yani hep `çekimser` diyen bir model **hiç yanılmaz ve hiç terfi etmez**. Pilot bunu
ölçer (F2/F3); ama pilot F2 ile düşerse **çözüm skill değil, teşvik tasarımıdır** ve o ayrı bir
karardır (operatör kalemi).

### E.8 `-Q` körlüğü sürüyor

`agent_calls.jsonl`'de `tool_calls = −1` **770/770 satırda** — `-Q` sessiz mod CLI oturum özetini
bastırdığı için `_agent_tool_calls` (`hermes.py:1697`) hiçbir şey yakalayamıyor. Yani "model pilot
sırasında `skill_view` çağırdı mı" sorusu **Meridian'ın kendi defterinden okunamaz**; yalnız
üçüncü-taraf `.usage.json` `view_count` farkından okunur (E.2'nin kırılganlığıyla birlikte).

---

## EK-1 — ÖLÇÜLEMEYENLER (uydurma yasağı beyanı)

| kalem | neden ölçülemedi |
|---|---|
| Skill × tarih zaman serisi (`-s` yolu) | Defterde alan yok; `.usage.json` kümülatif. v242 dağıtılana kadar **ileriye dönük** de yok. |
| Bir skill ön-yüklemesinin tek başına katkısı (bugüne kadar) | Hiç A/B koşulmadı; tüm çağrılar aynı listeyle gitti. Tarihsel veriden ayrıştırılamaz. |
| `rank_explore` (D3) katkısı | 102 seçim, 0 `exploration` işlemi — sonuç değişkeni hiç doğmamış. |
| D8 (arka plan turu) ayrı katkısı | D4 ile aynı `kind="proposal"` defterine yazıyor; ayrı sayaç yok. |
| Sprint budama penceresinin SÜRESİ | Senkron kadansından türetilebilir (~5 dk üst sınır) ama **ölçülmedi**; türetim ölçüm sayılmaz. |
| Aday üretiminin 2026-08-07'de neden durduğu | Bu kartın kapsamı dışı; ayrı iş kalemi. |
| `nous_eval` (D7) önerilerinin **gerçekleşen** etkisi | `nous_fisler.json` 8 fişin hepsi `durum: fislendi` — hiçbiri sonuçlanmamış; etki metriği yok. |

## EK-2 — Ölçüm komutları (yeniden üretilebilirlik)

Tüm ölçümler salt-okuma, tek kalıpla:
```
ssh -i ~/.ssh/oci-a1.key ubuntu@130.61.126.87 'cd /opt/meridian && ./.venv/bin/python -' < betik.py
```

Okunan canlı kaynaklar: `/opt/meridian/state/{skills_registry.json, agent_calls.jsonl,
agent_traces.jsonl, events.jsonl, trade_plans.jsonl, trades.jsonl, candidates.jsonl,
pipeline_runs.jsonl, llm_calibration.json, component_ic.json, skill_recommendations.jsonl,
nous_eval_runs.json, nous_fisler.json}` · `/opt/meridian/skills/*/SKILL.md` (31 dosya, 352 KB) ·
`~/.hermes/{SOUL.md, skills/.usage.json, skills/*}`.

Çağrılan canlı fonksiyonlar (yan etkisiz): `hermes._skill_preload`, `hermes.quota_state`,
`hermes.backfill_budget`, `hermes.search_budget`, `hermes.brain_availability`,
`hermes.brain_chain_facts`, `hermes.agent_skill_coverage`, `skills.catalog`,
`analytics.skill_attribution`, `skill_gorus.evren`, `skill_gorus.defter`, `skill_evolve.weak_skills`,
`skill_evolve.pending_drafts`, `strategy.ARMED_SETUPS`.

Repo kaynakları: `meridian/{hermes.py, skills.py, analytics.py, agent_telemetry.py, skill_gorus.py,
skill_evolve.py, nous_eval.py, loop.py, reflect.py, mcp_server.py, sprint.py, api.py}`.
