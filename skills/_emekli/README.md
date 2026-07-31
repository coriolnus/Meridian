# skills/_emekli — arşiv (2026-07-30 skill denetimi)

Bu dizin **silinmiş** skill'ler değil, **arşivlenmiş** skill'ler tutar. 68 klasörlük kütüphane
denetlendi; 37 klasör buraya taşındı, geride 31 canlı skill kaldı. Kayıt defterindeki
(`state/skills_registry.json`) girdileri de silinmedi: `retired: true` ile duruyorlar, böylece
envanter dürüst kalır ve geri dönüş tek adımdır.

İki grup var: **emekli** (programa hizmet etmiyor) ve **birleştirilen** (çekirdek sezgisi başka bir
SKILL.md'ye katlandı).

## Kayıt defterinde ne değişti

| Alan | Değer |
|---|---|
| `enabled` | `false` |
| `mode` | `disabled` |
| `reason` | emekli: `programa hizmet etmiyor (2026-07-30 denetimi)` · birleştirilen: `birleştirildi → <hedef>` |
| `retired` | `true` — `reconcile_enablement()` bu kayıtları atlar: anahtar gelse bile diriltilmez |
| `retired_folder` | `skills/_emekli/<ad>` |
| `retired_from_pipeline` | taşınmadan önceki boru hattı beyanı (geri dönüş için) |
| `pipeline` | `null` — `skills.py PIPELINES` zincirlerinden de çıkarıldılar |

## Geri getirme (tam tersi, üç adım)

1. `skills/_emekli/<ad>` klasörünü `skills/<ad>` konumuna taşı.
2. Kayıttan `retired`, `retired_at`, `retired_folder`, `merged_into`, `denetim_notu` alanlarını
   kaldır; `retired_requires` varsa değerlerini `fmp`/`alpaca` alanlarına GERİ YAZ (arşiv kaydı
   anahtar-kapısı adayı olmaktan çıkarıldığı için bu alanlar `-` yapılmıştı, özgün gereksinim
   `retired_requires`ta duruyor); `enabled`, `mode` ve `reason` alanlarını amaçlanan duruma getir
   (`skills.py` kilitli deseniyle yaz).
3. Gerçekten bir boru hattına girecekse `skills.py PIPELINES` zincirine adını ekle — aksi hâlde
   `pipeline` alanını `null` bırak; zincirde durup hiç koşmamak denetimin kapattığı kusurdur.

## Emekli (22 klasör)

Hüküm gerekçeleri denetim tablosundan alınmıştır.

| Skill | Gerekçe (denetim) |
|---|---|
| `cot-contrarian-detector` | Program tamamen ABD hisse senedi swing üzerine kurulu; |
| `dividend-growth-pullback-screener` | Uzun vadeli temettü-büyüme yatırımı programın hiçbir §3 kalemine hizmet etmiyor; |
| `downtrend-duration-analyzer` | İki haftadır her P1 koşusunda declared_not_run, motor karşılığı yok, FMP bağımlılığı kayıtla çelişiyor ve G3b'nin tutma-süresi sorusu replay ile zaten ölçülüyor — programa hizmet etmiyor. |
| `edge-signal-aggregator` | Değer üretebilmesi 6 üst-akış skill'in düzenli çıktı üretmesine bağlı (biri disabled, hiçbiri koşmuyor); |
| `kanchi-dividend-review-monitor` | Programın stili temettü taşımıyor (style_active=false bunu zaten söylüyor) ve girdisi olan temettü portföyü Meridian'da mevcut değil; |
| `kanchi-dividend-sop` | Programa hizmet etmiyor ve iki temettü screener'ıyla iç içe geçmiş beş skill'lik atıl bir küme oluşturuyor; |
| `kanchi-dividend-us-tax-accounting` | Aktivasyonu ucuz ama üreteceği değer sıfır: sistemde ne temettü portföyü ne çoklu hesap türü var; |
| `news-reaction-failure-analyzer` | İki-adımlı zincirin ilk adımı stil gereği kapalı, FMP anahtarı yok ve §3'te hizmet ettiği kalem yok — tek başına değer üretemeyen ikinci adım; |
| `options-strategy-advisor` | Program opsiyon yönüne kapı açmıyor (§3'te kalem yok, §5 veri alımını yasaklıyor) ve operatör intake'te bilinçli reddetmiş — atıl P3 slotu; |
| `pair-trade-screener` | Stil dışı (registry gerekçesi), motor yok, sıfır kullanım izi, hiçbir §3 kalemine hizmet etmiyor; |
| `scenario-analyzer` | 59 koşuda sıfır gerçek kullanım + 18-aylık ufuk EOD swing programının hiçbir kalemine hizmet etmiyor; |
| `sector-analyst` | Edge yolu §5 YAPMA listesinde çürütülmüş, Y3'ün gerçek ihtiyacı (sektör üyeliği) bu skill değil; |
| `shadow` | Skill değil, boş bir klasör artığı; |
| `skill-designer` | Var olmayan bir pipeline'a kayıtlı, hiç çağrılmamış ve sıfır ürün vermiş meta hat; |
| `skill-idea-miner` | Vaat ettiği launchd tetikleyicisi kurulmamış, hattın hiçbir ürünü yok; |
| `skill-integration-tester` | Doğruladığı mimari (CLAUDE.md iş akışları) bu repoda hiç var olmamış; |
| `stanley-druckenmiller-investment` | Girdisi olan 8 skill'in çıktısı üretilmiyor, sentezlediği karar (maruziyet/tahsis) zaten regime.py + guard katmanının deterministik yetkisi; |
| `stockbee-20pct-study` | İleri dönük sonuç ölçümünü counterfactuals.jsonl (7159 satır) zaten deterministik yapıyor, katalizör araştırması G5'te motor kalemi olarak planlı; |
| `technical-analyst` | Girdisi (chart image) otonom motorda üretilmiyor, hiçbir §3 kalemine hizmet etmiyor ve 15 günlük koşu günlüğünde tek iz yok; |
| `trader-memory-core` | Motor karar+sonuç hafızasını zaten memory.py ve cf/ledger defterleriyle tutuyor; |
| `us-stock-analysis` | Hiçbir pipeline'a bağlı olmayan, hiç çağrılmamış, deterministikleştirilemez (web-arama LLM işi) genel amaçlı bir skill; |
| `value-dividend-screener` | Stil kapısı zaten kapatmış, anahtar bağımlılığı karşılanmıyor, §3'te hizmet edeceği kalem yok ve dividend-growth-pullback-screener + kanchi ailesiyle kapsam çakışıyor — kayıt defterinde ölü… |

## Birleştirilen (15 klasör)

Her birinin çekirdek sezgisi hedef dosyada **"Folded in: <ad>"** başlıklı bir bölüm olarak duruyor.

| Skill | Katlandığı hedef | Gerekçe (denetim) |
|---|---|---|
| `breadth-chart-analyst` | `market-breadth-analyzer` | Aynı P1_REGIME zincirinde market-breadth-analyzer ile işlev çakışıyor ve motor zaten index-türevi breadth proxy'sini kendisi üretiyor; |
| `breakout-trade-planner` | `docs/G3B-CIKIS-REFORMU-NOTLARI.md` | İşlevi motorun strategy.py+loop.py plan yolu ve motor-uygulanmış position-sizer/pre-trade-discipline-gate tarafından tamamen soğurulmuş; |
| `dual-axis-skill-reviewer` | `trading-skills-navigator` | skill_evolve.py taslakları operatöre skorsuz gidiyor; |
| `earnings-trade-analyzer` | `pead-screener` | pead-screener ile birebir alan çakışması var ve stil kararıyla zaten kapalı — işe yarar 5-faktör bileşenleri (gap boyutu, MA konumu) pead-screener referanslarına not düşülüp klasör emekli e… |
| `edge-candidate-agent` | `edge-pipeline-orchestrator` | Yedi klasörlük edge-* ailesi (hint-extractor, concept-synthesizer, strategy-designer, candidate-agent, strategy-reviewer, signal-aggregator, orchestrator) tek iş akışının parçaları ve prelo… |
| `edge-concept-synthesizer` | `edge-pipeline-orchestrator` | Bu skill zaten edge-pipeline-orchestrator'ın 'concepts' aşamasının sarmaladığı script; |
| `edge-hint-extractor` | `edge-pipeline-orchestrator` | SKILL.md'nin kendisi 'observe→abstract→design→pipeline' zincirinin ilk aşaması olduğunu söylüyor; |
| `edge-strategy-designer` | `edge-pipeline-orchestrator` | Orchestrator'ın 'drafts' aşamasının script'i; |
| `trade-hypothesis-ideator` | `edge-pipeline-orchestrator` | Hermes aynı işi motor içinde tek-değişkenli hipotez+guard+backtest kapısıyla yapıyor; |
| `ftd-detector` | `macro-regime-detector` | İşlev regime.py follow_through proxy'sinde zaten canlı; |
| `market-news-analyst` | `market-environment-analysis` | market-environment-analysis zaten haber/sentiment kapsıyor ve Hermes'te fiilen kullanılıyor; |
| `signal-postmortem` | `backtest-expert` | İşlevi motordaki cf/attribution döngüsüyle bire bir çakışıyor; |
| `stockbee-setup-fluency-trainer` | `weekly-performance-digest` | Vaat ettiği ileri-dönük MFE/MAE/sonuç ölçümünü counterfactual.py + analytics.skill_attribution zaten deterministik ve daha büyük örneklemle yapıyor; |
| `trade-performance-coach` | `weekly-performance-digest` | Aynı P5 zincirinde hiç koşmayan weekly-performance-digest ile işlevi (dönemsel insan-okur performans raporu) çakışıyor; |
| `us-market-bubble-detector` | `market-top-detector` | P1'de market-top-detector/macro-regime-detector ile işlev çakışması var ve Y3 dörtlüsü aynı ihtiyacı ölçülebilir deterministik kurallarla karşılayacak — SKILL.md'nin nicel eşik tabloları Y3… |

## Bilinen atıf kalıntısı

Canlı bazı SKILL.md/reference dosyaları hâlâ bu adları anıyor (ör. "use `us-stock-analysis`
instead", "feed into `technical-analyst`", `trader-memory-core` şema yolları). Bu turda yalnız
**işlevsel** bağ düzeltildi — `edge-pipeline-orchestrator`'ın aşama script'leri artık canlı yolu
deneyip arşive düşüyor — ve birleştirme hedeflerindeki atıflar güncellendi. PROTECTED beşlisinin
(`pre-trade-discipline-gate`, `drawdown-circuit-breaker`, `data-quality-checker`, `position-sizer`,
`portfolio-manager`) dosyalarına bilinçli olarak dokunulmadı; onlardaki `trader-memory-core`
atıfları bu README ile bir adımda çözülür. `trading-skills-navigator`'ın
`assets/metadata_snapshot.json` anlık görüntüsü de yeniden üretilmedi — arşivlenmiş bir adı
önerebilir.

Denetimin tam tablosu ve her skill için motor/kullanım kanıtı: 2026-07-30 skill denetimi çıktısı
(68 klasör, 10 paralel ajan).
