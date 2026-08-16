# Meridian

Kendi stratejisini **ölçerek** iyileştiren, ABD hisseleri üzerinde çalışan bir **araştırma**
ajanı. S&P 500'ü tarar, swing-momentum işlemleri planlar, **kâğıt üzerinde** (Alpaca paper)
boyutlandırıp girer, kapanan her işlemi notlar ve stratejisini sabit bir kum havuzunun içinde
yeniden yazar — **hak etmeden tek bir dolara dokunamaz.**

> **Araştırma sistemi. Paper modu. Yatırım tavsiyesi değildir.** Meridian, "bir ajan dürüstçe
> edge öğrenebilir mi?" sorusunu incelemek için kurulmuş bir araştırma düzeneğidir. Sevk edilen
> otonomi seviyesinde (L0) gerçek para işlemez.

Ürün **döngünün kendisidir, alfa değil**: gerçekçi sürtünmeler, örneklem-dışı kapılar, geri
yazılan sonuçlar, otomatik geri alma. "Skor yükseldi" ile "edge bulundu" asla karıştırılmaz.
Uygulanan her kural **prompt'ta değil kodda** yaşar: Hermes'e söylenen her şeyi `guard.py` zorlar.

---

## Sistem bir bakışta

Tek süreçte (FastAPI) iki döngü + bir kontrol düzlemi; tek durum dizini (`state/`):

- **İşlem döngüsü** — kapanan her XNYS seansında bir kez: veri tazele → rejimi etiketle →
  kurulumları tara → risk kapıları → GO/REVIEW/NO_GO → Alpaca paper emri → defter.
- **Öğrenme döngüsü (Hermes)** — tek-değişkenli parametre hipotezleri üretir; hepsi tek kapıdan
  (`reflect.submit` → `guard` → walk-forward ölçüm → teyit yürüyüşü) geçmeden hiçbir şey ship
  edilmez; ship sonrası gerçekleşen sonuç tahminle karşılaştırılır, kötüyse otomatik geri alınır.
- **Kontrol düzlemi** — pano + JSON read-model + HALT/onay yüzeyi (`meridian/api.py`).

Görsel harita: **`workflow-diagram.html`** (etkileşimli; iki kulvar, düğüm başına açıklama,
log oynatıcı). Modül-modül tam envanter: **`docs/MODUL-ENVANTERI-2026-08-15.md`**.

## Bileşenler — katman katman

96 Python modülü, ~67k satır. Görev cümleleri her modülün kendi başlık docstring'inde yaşar;
aşağısı anlatı, tam tablo envanterdedir.

**1. Giriş & kadans.** `api.py` FastAPI uygulaması — pano, 73 yol (58'i `/api/…`; ölçüm:
`len([r for r in api.app.routes if hasattr(r, "methods")])`, 2026-08-16), kimlik doğrulama, HALT/onay
yazma yüzeyi; 24/7 kadansı uygulama açılışında iki iplikle başlatır: `scheduler.py` (günlük
döngünün zamanlayıcısı) ve `hermes_runtime.py` (öğrenme bekleme döngüsü). `loop.py` günlük paper
döngüsünün kendisidir; `intraday_cycle.py` kapanmış-bar gözlem tüketicisi. `run.py` bilinçli bir
nöbetçi taştır: ikinci bir kadans yasası yaşamasın diye çalışmayı reddeder (tohumlama `--replay`
yolu yaşar).

**2. Sinyal çekirdeği (saf).** `strategy.py` — I/O'suz, saatsiz, ağsız saf sinyal; yalnız kapalı
barlar; yürürlükteki kurulum kümesi `strategy.ARMED_SETUPS`'tır (README'ye liste yazılmaz —
bayatlar). `regime.py` her işlemi trend_up/trend_down/chop/high_vol etiketler; `score.py` PARA-v3
bileşik skoru; `indicators.py` saf teknik gösterge yaprağı; `earnings.py` kazanç karartması.

**3. Kısıt & yasa katmanı.** `guard.py` gerçek kısıt katmanıdır: öneri doğrulama
(`validate_change` — tek-değişken şekli, `bounds.yaml` üyeliği, tip/aralık/adım, no-op, kota) ve
işlem kapısı (`classify_gate` — GO/REVIEW/NO_GO, sektör/ısı tavanları). `health.py` kalp atışı +
HALT/LEARN_HALT; `codelaw.py` iki statik kod yasasını tarar; `ledgers.py` defter sözleşmeleri;
`ledgerstamp.py`/`provenance.py` kaynak damgaları; `integrity_registry.py`, `sieve.py`,
`validation.py` (DSR/PSR + PBO/CSCV), `validation_report.py`, `recompute.py` (aynı soruyu iki
yoldan cevapla) denetim ailesi.

**4. Öğrenme beyni.** `hermes.py` beyindir: bağlam kurar, LLM zinciriyle (claude → lokal ajan →
gemini) ya da zincir boşsa determinist `propose_virgin_knob` ile TEK değişkenli öneri üretir;
arka plan süzgeci sertifika-uyumsuz önerileri ele alır (28a). `reflect.py` tek ship kapısıdır:
guard → `backtest.walk_forward` (yeniden oynatım, IS/OOS/holdout) → `_gate_eval` ("TEK yasa":
büyüklük + fold çoğunluğu + kuyruk vetosu + drawdown vetosu; `probgate.py` P(ΔS>0) eşiği, K-sonda
cezalı) → `oos_pipeline.py` %30 Confirm teyidi (ölçülemeyen onay ship'i BLOKLAR) →
`versioning.py` sürüm + anlık görüntü → `rollback.py` otomatik geri alma. `memory.py` hipotez
defteri; `hermes_composite.py` çok-düğmeli fikirlerin ölçüm kuyruğu; `prescreen.py` kapının kendi
yasasıyla ön eleme; `sprint.py`/`sprint_run.py` kum havuzunda öğrenme antrenmanı; `baseline.py`,
`threshold_curve.py`, `component_ic.py`, `counterfactual.py`/`cf_backfill.py`, `oos_erosion.py`,
`mutation.py` (dedektör körlük haritası), `nous_eval.py` (haftalık öz-değerlendirme),
`shadowlaw.py`, `arming.py`, `selfreview.py`, `agent_telemetry.py`, `spend.py` (LLM bütçe
bekçisi), `olcum_araclari.py`, `faz5_cikis.py` ölçüm/denetim aileleridir.

**5. Gölge katman (sıfır yetki).** `shadow_model.py` (P(kazanç) damgası), `shadow_variants.py`,
`shadow_lifecycle.py`, `trend_shadow.py`, `intraday_shadow.py` — hiçbiri canlı karara dokunamaz;
kendi defterlerinde kanıt biriktirirler.

**6. Beceri katmanı (Eksen-2).** `skills.py` Claude trading becerilerini beş determinist boru
hattına bağlar; `skill_evolve.py` içerik evrimi; `skill_gorus.py` ön-kayıtlı görüş defteri.
Beceri sayısı sayfaya yazılmaz: `GET /api/public/summary → skills_live`.

**7. İcra.** `broker.py` gerçekçi sürtünmeli paper broker; `sermaye.py` antrenman tohumu ↔ canlı
sermaye ayrımı.

**8. Bar / akış altyapısı.** `marketstream.py` Alpaca kapanmış-bar WS dinleyicisi →
`hotstate.py` (Redis sıcak durum) → `barfeed.py`/`barclock.py` tüketiciler; `bararchive.py`/
`barsarchive.py` kalıcı arşiv, `barrepair.py` onarım; `mirror_stream.py` emir-durumu aynası;
`streamhealth.py` WS dinleyicilerinin ortak yasası; `dataset.py` yeniden-oynatım evreninin tek
yükleyicisi + sabit backtest pencereleri.

**9. Veri kenarı (`adapters/`).** `data.py` günlük OHLCV merkezi (Cboe birincil), `alpaca.py`
broker adaptörü (paper kilidi; LIVE yolu bayraklar olmadan reddedilir), `massive.py` EOD
sağlayıcı, `fmp.py` temel veri, `finviz.py` otonom aday kaynağı, `insider.py` Form 4,
`shortinterest.py` FINRA kısa pozisyon, `edgar_shares.py` as-of hisse sayımı,
`constituents.py` point-in-time S&P 500 üyeliği. `macro.py`/`news.py` emeklidir (güdük).
Yasa: kenar katman motoru tanımaz (importlinter sözleşme 1).

**10. Kalıcılık & yapılandırma.** `storage.py` defter çekirdeğinin SQLite arka ucu
(`state/meridian.db`, WAL; 6 varlık), `store.py` atomik yazım + flock + JSONL, `dbmigrate.py`
parite kanıtlı göç, `config.py` yol çözümü + değişmez `goal.yaml`/`bounds.yaml` yükleyicisi +
v01 tohumu.

**11. Gözlem, pano & operasyon.** `obs.py` yapısal JSON olaylar + ALARM_ jetonları;
`watchdog.py` 15+ dişlinin canlılık bekçisi; `analytics.py` pano read-model'i;
`marketview.py` evren görüntüsü; `notify.py` operatör bildirimi; `secrets.py`/`auth.py`/
`auth_cli.py` sır ve kimlik; `mcp_server.py` salt-okunur durumu lokal hermes-ajana MCP olarak açar.

## Durum yüzeyleri

| Yüzey | Ne | Nerede |
|---|---|---|
| `state/goal.yaml` | DEĞİŞMEZ hedef/risk sözleşmesi (Hermes dokunamaz) | repo + canlı |
| `state/bounds.yaml` | Parametre kum havuzu — aramanın sınırları | repo + canlı |
| `state/strategy.yaml` | Canlı, değişebilir parametre yüzeyi (kapıdan geçen ship'ler yazar) | yalnız canlı |
| `state/meridian.db` | İşlem/plan/portföy defter çekirdeği (SQLite) | yalnız canlı |
| `state/hypotheses.jsonl` | Hipotez defteri — kabul VE retler ölçülen sayılarla | yalnız canlı |
| `state/history/vNNNN.yaml` | Değişmez sürüm anlık görüntüleri | yalnız canlı |

Sayılar (eşikler, tavanlar, pozisyon boyutu) README'ye **bilerek** yazılmaz — adres söylenir,
değer söylenmez; pano canlı basar. (Bu sayfanın eski sürümleri sabit sayı taşıyıp iki kez
bayatladı; ders sayfaya işlendi.)

## Disiplin (ölçüm dürüstlüğü)

- **Kart-önce ölçüm:** `research/cards/` ön-kayıt kartı olmadan ölçüm kodu yazılmaz; eşik sonradan
  değişmez; denenen K, kapının eşiğini yükseltir (çok deneyen daha güçlü kanıt borçlanır).
- **Tek-değişken yasası:** bir öneri tek parametre değiştirir; bileşikler ship edilmez, ölçüm
  kuyruğuna gider.
- **UYDURMA YASAĞI:** ölçülemeyen şey None + nedenidir; "ölçtük, sıfır" ile "ölçemedik" aynı
  piksele düşemez.
- **Statik yasalar:** sessiz-yutma işaretli ve gerekçeli (YASA 4), okuyucusuz yazım yok (YASA 6) —
  `codelaw.py` tarar.
- **Örneklem hijyeni:** IS / Search-OOS (%70) / Confirm-OOS (%30) / dokunulmaz holdout;
  fold'lar ve kuyruk riski yalnız Search'te; teyit ortalaması tahmini DEFLATE eder.

## Otonomi merdiveni — canlı işlem *kazanılır*

```
L0  PAPER, TAM OTONOM            ← bugün burada. İnsan izler. Sıfır gerçek para.
L1  CANLI, HER EMİR ONAYLI       ← her emir onay kuyruğunda bekler; geçerlilik TEK SEANSTIR.
L2  CANLI, OTONOM                ← limits bloğunun içinde gerçek para.
```

Onayın ömrü **dakika değil seanstır**: `_enrich_stale_plans` bir planı `expired` damgalar (plan
tarihi son işlenmiş seanstan eskiyse) ve onay gelen kutusu süresi geçmiş planı göstermez.

İŞ BÖLÜMÜ AÇIK OLSUN — terfi ölçütlerini **ölçen** ile canlı modu **reddeden** aynı modül değildir:

- **Ölçen:** `analytics.py` (`L0->L1 promotion criteria`) — yeterli kapalı işlem, ≥2 rejimde
  pozitif skor, tüm dönem drawdown sözleşme içinde, tahmini tutan kabuller, açıklanamayan
  devre-kesici sıfır. Bu bir KARNEDİR; kapı değildir. Üç kalem (çekimleri kapalı broker anahtarı,
  elle çevrilen iki ortam bayrağı, telefonda kill-switch) kodda `manual=True` işaretlidir —
  ölçülmezler, operatör terfi anında elle doğrular.
- **Reddeden:** `guard.py` — TEK sert kural şudur: `autonomy_level < 1` iken canlı mod istenirse
  emir reddedilir (`live mode requested but autonomy_level<1 — refused`). Karnenin kalemlerini
  `guard.py` ZORLAMAZ; bayrağı çeviren operatördür.

Meridian bayrağı asla kendisi çevirmez; panonun **Today** sayfası paraya güvenilmekten ne kadar
uzak olduğunu basar.

## Çalıştırma (yerel)

```bash
uv sync --extra dev
uv run python -m meridian.run --dry-run --replay 2023-01-01:2026-07-10   # tohumlama (tek seferlik)
uv run pytest -q                                                          # test paketi (uzun; aşağıya bak)
MERIDIAN_AUTOSTART_CYCLE=1 CYCLE_POLL_SECONDS=300 \
  uv run uvicorn meridian.api:app --host 127.0.0.1 --port 8080            # pano + kadans (serve.sh bunu yapar)
uv run python -m meridian.reflect --auto                                  # determinist yansıma (LLM'siz)
```

> **DİKKAT:** Canlı sistem A1'de koşarken yerelde `./serve.sh` KOŞMA — çift emir riski
> (çalışma sözleşmesi: `CLAUDE.md` kural 5). `python -m meridian.run` 24/7 worker DEĞİLDİR —
> emekli; gerekçe modül docstring'inde.

## Dağıtım & operasyon (kanonik yol: Oracle A1)

- **Dağıtım yalnız `./dagit.sh` iledir** ve kapılıdır: temiz-ağaç → `uv audit` → `lint-imports`
  (5 mimari sözleşme) → rsync kuru-koşum → versiyonlu-state anahtar-düzeyi diff → bakım penceresi
  (durdur → bayt-doğrulamalı yedek → başlat) → sağlık doğrulaması. **Push dağıtım değildir;
  parametre değişikliği dağıtım istemez** (kapıdan ship edilir).
- **A1 üzerinde systemd:** `meridian.service` (uvicorn), `meridian-barsarchive`, gece yedeği
  (timer), tick-watchdog, litestream; ayrıntı `deploy/oracle-a1/` + `docs/RUNBOOK.md`.
- **Yedekler:** A1 gece tar'ı → operatör makinesine çekilir (`ops/pull-a1-backups.sh`, LaunchAgent).
- **Acil durdurma:** panodaki büyük kırmızı düğme = `state/HALT` dosyası; kaldırınca devam eder.
- `Dockerfile`/`docker-compose.yml`/`deploy.sh` + GCP betikleri **BAYATTIR** (K1, 2026-07-30):
  geri alınabilirlik için durur; ölçülmüş üç sapması düzeltilmeden kullanılamaz (eski README
  notu `docs/` denetimlerinde ve dosya başlarında yaşar).

## Test & doğrulama

- ~5.4k+ test, 319 dosya (`tests/`); adlandırma `test_<konu>_v<N>.py` — N, testin çivilendiği tur.
  `bounds.yaml` içindeki bazı düğmeler adlı testlerle mühürlüdür (ör. sıfır-etki kablolama çivileri).
- **Tam paket tek-otoriterdir ve uzundur** (4 çekirdekte ~50 dk): canlı-benzeri `state/` ve yerel
  servisler ister; taze klonda state-bağımlı aileler düşer (bkz. envanter §5 sınıflandırması).
- CI (`.github/workflows/ci.yml`) 15 dakikalık sınırıyla tam paketi TAŞIYAMAZ — bugüne dek hiçbir
  CI koşusu paketi bitirememiştir (zaman aşımı iptali). CI'ı hızlı bir duman alt-kümesine indirmek
  açık bir iyileştirme adayıdır; karar operatöründür.
- Hızlı yerel kapı: `ops/kapilar.sh` (lint-imports → audit → kapsam testleri) — tam paketin
  yerine geçmez.

## Belge haritası

| Belge | Ne |
|---|---|
| `ROADMAP.md` | Planların tek gerçek kaynağı: sözleşme, WP'ler, karar günlüğü, arşiv |
| `MERIDIAN_ENGINEERING_LOG.md` | "Şu an gerçekte ne var" — her oturum önce bunu okur |
| `docs/MODUL-ENVANTERI-2026-08-15.md` | 96 modülün katman katman envanteri + doğrulama |
| `workflow-diagram.html` | Etkileşimli sistem diyagramı (iki kulvar + iç akışlar) |
| `docs/RUNBOOK.md` | A1 işletim el kitabı (üretilir; `/runbook`'ta servis edilir) |
| `research/cards/` + `research/olcumler/` | Ön-kayıt kartları + ölçüm kanıtları |
| `DESIGN.md` / `PRODUCT.md` | Tasarım dili / ürün şeması |
| `docs/DENETIM-*`, `AUDIT-*` | Denetim ve teşhis ailesi |

---

_Meridian bir araştırma sistemidir. Paper modu. Yatırım tavsiyesi değildir._
