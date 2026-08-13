# DENETİM — SKILL ÇAĞRI İZİ (2026-08-13)

**Operatör sorusu:** "Hiç çağrılıp ne sonuç verdiği bilinmeyen bir skill nasıl veri üretebilir ki —
skill çağrı izini ölç, hangi skill ne zaman çağrılmış."

**Kapsam:** salt-okuma. Canlı A1 (`ubuntu@130.61.126.87`, `/opt/meridian`) + repo kodu. Yazma yok,
git yok, repo koduna dokunulmadı. Her iddia `dosya:satır` ya da canlı komut çıktısıyla bağlıdır.

---

## 0. YÖNETİCİ ÖZETİ — dört sayı, dört ayrı anlam

| Soru | Sayı | Kaynak |
|---|---|---|
| Kaç skill LLM'e **SUNULUYOR** (katalogda görünüyor + `skill_view` ile açılabilir)? | **30 / 30** | canlı istem dökümü `<available_skills>` bloğu |
| Kaç skill **ÇAĞRILABİLİR** (araç tanımı mevcut)? | **30 / 30** | istem gövdesindeki `skill_view` + `skills_list` araç şemaları |
| Kaç skill **FİİLEN İSTEME GİRDİ** (`-s` ön-yükleme)? | **13** (6.839 enjeksiyon) | `~/.hermes/skills/.usage.json` |
| Kaç skill'i **LLM KENDİ İRADESİYLE AÇTI** (`skill_view` aracı)? | **4** (11 çağrı) | `~/.hermes/logs/agent.log` + `.usage.json` |
| Bu çağrıların kaçının izi **MERİDİAN'IN KENDİ DEFTERLERİNDE** var? | **0** | aşağıda §2 |

**Hüküm — operatörün sezgisi doğru ama nedeni beklenenden farklı.** Skill'ler *çağrılıyor*: 30'unun
tamamı LLM'e sunuluyor, 13'ü her çağrıda isteme tam gövdesiyle basılıyor ve bugüne dek 6.839 kez
enjekte edilmiş. Ölçülemez olan **çağrı değil, çağrının Meridian tarafındaki İZİ**:

> **Meridian'ın hiçbir defteri bir skill ADI yazmıyor.** `agent_calls.jsonl` `on_yukleme_n: 6` der,
> `events.jsonl` `preloaded: 6` der, `agent_traces.jsonl` hiç alan taşımaz. Kaç tane olduğu yazılı,
> **hangileri olduğu yazılı değil.** Gerçek çağrı izi **üçüncü taraf bir deftere** —
> `~/.hermes/skills/.usage.json` — düşüyor ve Meridian o dosyayı **okumuyor**.

Yani "bilinmeyen" olan skill'in çağrılıp çağrılmadığı değil; Meridian'ın kendi kendine bunu
**soramıyor** olması. Defter var, sahibi başkası.

---

## 1. ÇAĞRI YOLU — skill'ler ajana FİİLEN nasıl geçiyor

### 1.1 Zincir (kod izi)

```
hermes._agent_call()                       meridian/hermes.py:1868   ← TÜM yerel-ajan çağrılarının tek kapısı
  └─ sync_agent_skills()                   meridian/hermes.py:1909 → :2899
       enabled seti → ~/.hermes/skills/<ad> symlink'leri
  └─ _skill_preload(kind, setups)          meridian/hermes.py:2948   ← tavan 8, kanıt-güdümlü sıralama
  └─ _agent_chat_cmd(bin, prompt, preload, model)   meridian/hermes.py:1832
       cmd = [hermes, "chat", "--accept-hooks", "-Q", "-q", <istem>, "-s", <skill>, …, "--model", <model>]
  └─ subprocess.run(cmd)                   meridian/hermes.py:1929
```

`AGENT_SKILLS_DIR = ~/.hermes/skills` (`meridian/hermes.py:2562`) — **tek, paylaşımlı** dizin
(§6.4'te bunun bedeli ölçülü).

### 1.2 Skill'ler SUNULUYOR mu, yoksa katalogda mı duruyor? → **SUNULUYOR**

Canlı istem dökümünden ölçüldü (`~/.hermes/sessions/request_dump_20260813_172602_a4307c_*.json`,
229.885 bayt — bu dosyalar yalnız başarısız isteklerde yazılıyor, 958 adet birikmiş):

* **Sistem istemi 106.558 karakter**, iki blok halinde:
  1. `<available_skills>` **kataloğu (10.228 kr)** — 95 skill girdisi, her biri ad + tek satır
     açıklama. Bunların **30'u Meridian'ın enabled seti; eksik olan YOK**
     (`enabled(30) ama KATALOGDA YOK: []`).
  2. **8 ön-yüklenen skill'in SKILL.md gövdesi tam metin olarak gömülü** — her birinin başında
     `[IMPORTANT: The user launched this CLI session with the "<ad>" skill preloaded. Treat its
     instructions as active guidance…]` aktivasyon notu.
* **Araç tanımları (18 adet)** arasında `skills_list` (86 kr) ve `skill_view` (360 kr) **var**:
  > `skill_view` — "Load a skill's full content or access its linked files…"
  > `skills_list` — "List available skills (name + description). Use skill_view(name) to load full content."
* Sistem istemi ayrıca **zorunluluk** dayatıyor (`## Skills (mandatory)`):
  > "Before replying, scan the skills below. If a skill matches or is even partially relevant to your
  > task, you **MUST** load it with `skill_view(name)` and follow its instructions."

**Sonuç:** ön-yüklenmemiş 22 skill de LLM tarafından **görülüyor ve açılabiliyor**. "Yalnız katalogda
duruyor, ajana sunulmuyor" hipotezi **ÖLÇÜLEREK ELENDİ**.

### 1.3 Ön-yükleme listeleri (canlı `_skill_preload` çıktısı, yan etkisiz koşum)

| kind | n | liste |
|---|---|---|
| `proposal` | 8 | backtest-expert, market-environment-analysis, macro-regime-detector, portfolio-manager, market-breadth-analyzer, edge-strategy-reviewer, position-sizer, pre-trade-discipline-gate |
| `review` / `explore` | 6 | stockbee-momentum-burst-screener, vcp-screener, market-environment-analysis, pre-trade-discipline-gate, position-sizer, pullback-screener |

`review`/`explore` listesi `screener_for(setup)` ile o günün setup'larına göre değişir — canlı
defterde ölçülen dağılım `on_yukleme_n ∈ {5, 6, 7, 8}`.

**Bu iki listenin BİRLEŞİMİ tam olarak 13 addır** ve `.usage.json`'daki 13 kayıtla **birebir**
örtüşür. Yani `-s` yolundan bugüne dek geçen skill kümesi kapalı ve 13 elemanlıdır.

### 1.4 `linked: 4` ne demek — **YANILTICI ALAN, KÖK NEDEN ÖLÇÜLDÜ**

`agent_skills_synced` olayındaki `linked`, **o senkronda YENİ KURULAN symlink sayısıdır**, bağlı
toplam değil (`meridian/hermes.py:2914` `linked.append(name)` yalnız `not os.path.exists(dst)`
dalında; `:2930` `out = {"enabled": …, "linked": linked, …}`). Toplam kapsamı ölçen ayrı fonksiyon
doğru cevabı veriyor:

```
agent_skill_coverage() → {'enabled': 30, 'linked': 30, 'missing': [], 'stale_linked': 0}
```
(`meridian/hermes.py:2936`)

**Ama `linked=4` bir arızayı işaret ediyordu ve arıza gerçek.** Canlı symlink yaşları:

```
2026-07-30T14:55:03   ← 26 skill (kuruluş)
2026-08-13T17:15:01   ← canslim-screener, economic-calendar-fetcher,
                        ibd-distribution-day-monitor, parabolic-short-trade-planner
```

Bu 4 skill sürekli silinip yeniden kuruluyor. **Kim siliyor — ölçüldü:**

* Bu 4 ad, kayıt defterinde `fmp = req` olan **tam kümedir** (diğer üç alan da aynı: `api_free=no`).
* Sprint kum havuzlarının kayıt defterinde bu 4'ü **`enabled: False`** (sandbox'ta FMP anahtarı yok →
  `reconcile_enablement()` kapatıyor): sprint `enabled` = 26, canlı = 30.
* Sprint defterinde **silme olayının kendisi**:
  ```
  /opt/meridian/state/sprint/20260813-151752/state/events.jsonl
  2026-08-13T15:20:13+00:00  agent_skills_synced  enabled=26  linked=0
    pruned=['parabolic-short-trade-planner','ibd-distribution-day-monitor',
            'canslim-screener','economic-calendar-fetcher']
  ```
* Canlı defterde 59 saniye sonra onarım: `2026-08-13T15:21:12  enabled=30  linked=4  pruned=[]`.

**Mekanizma:** `AGENT_SKILLS_DIR` tek ve paylaşımlı; sprint kum havuzu **canlı defterden izole ama
ajan skill dizininden İZOLE DEĞİL**. Her sprint, kendi (anahtarsız) enabled setine göre canlının
symlink'lerini **söküyor**. Söküm ile bir sonraki canlı senkron arasındaki pencerede o 4 skill
**canlı ajanın kataloğunda da yok** — yani sunulmuyor, `skill_view` ile açılamıyor. Bu, `dagit.sh`
kirli-ağaç kapısının ajan-katmanındaki karşılığı olan, henüz kapatılmamış bir sızıntıdır.

---

## 2. İZ — çağrı gerçekleşse defterde görünür müydü? **HAYIR (adıyla değil)**

### 2.1 `agent_traces.jsonl` şeması (canlı, 300 satır — halka tavanı `IZ_SATIR_TAVANI=300`)

```
alanlar: ts · iz_id · kind · model · deneme · alt · sonuc_sinifi · returncode
         stdout · stderr · ham_kr · tavan_kr · kirpildi
```
(yazıcı: `meridian/agent_telemetry.py:277-283`)

Örnek satır (2026-08-13T17:26:34):
```json
{"ts":"2026-08-13T17:26:34.382783+00:00","iz_id":"AC-…-proposal-2.0","kind":"proposal",
 "model":"gemini-flash-latest","deneme":2,"alt":0,"sonuc_sinifi":"dolu","returncode":0,
 "stdout":"{\"variable\": \"regime.vix_backwardation_gate\", …}","stderr":"⏎ session_id: … ⏎",
 "ham_kr":{"stdout":661,"stderr":36},"tavan_kr":8000,"kirpildi":false}
```

**Skill ile ilgili TEK BİR ALAN YOK.** Ham `stdout` içinde tesadüfen skill adı geçen satır sayısı: 12
(`stockbee-momentum-burst-screener` 8, `pullback-screener`/`exhaustion-hammer` 2'şer, `vcp-screener`
1) — bunlar **modelin cevabında geçen aday/atıf adlarıdır**, skill kullanımı kaydı değil. Ayrıca
`-Q` sessiz mod stdout'u yalnız son cevaba indirgediği için araç çağrıları çıktıda hiç görünmez.

### 2.2 `agent_calls.jsonl` (canlı, 770 satır, 2026-08-07T03:48 → 2026-08-13T17:26)

```
alanlar: ts · iz_id · tasiyici · kind · model · deneme · alt · sure_ms · sonuc_sinifi
         returncode · arac_cagri_n · arac_neden · on_yukleme_n · cikti_kr · hata_kr
         istem_kr · istem_ozet · istisna
```

* `on_yukleme_n` **sayıdır, liste değil** (`meridian/agent_telemetry.py:240`).
* `arac_cagri_n` = **770/770 satırda `None`** — `-Q` CLI oturum özetini bastırıyor, bu dürüstçe
  `arac_neden` ile beyan edilmiş. Yani "LLM araç çağırdı mı" sorusu **bu defterden hiç ölçülemiyor**.
* `sonuc_sinifi`: `bos` 750 / `dolu` 20 → **çağrıların %97,4'ü boş dönmüş** (ham izlerde neden
  yazılı: `Gemini HTTP 429 RESOURCE_EXHAUSTED` ve `HTTP 404`). Tüm zaman için `agent_call`
  olayında: 1.819 çağrının 1.467'si `empty=True` (%80,6).

### 2.3 `events.jsonl` (50.829 satır, 2026-07-14 → 2026-08-13)

| olay | n | skill ADI taşıyor mu |
|---|---|---|
| `agent_call` | 1.819 | **hayır** — yalnız `preloaded: <sayı>` (`meridian/hermes.py:2015`) |
| `agent_skills_synced` | 475 | kısmen — `pruned` listesi ad taşır, `linked` **sayı** |
| `agent_call_empty` | 752 | hayır |
| `agent_call_cooldown` | 1.760 | hayır |
| `agent_skill_preload_unknown` | **0** | (hiç tetiklenmemiş — ön-uçuş skill hatası yaşanmamış) |
| `skill_action_applied` | 8 | evet (yalnız `shadow`/`activate` kararları) |
| **`nous_call_skills`** | **2** | **EVET — `names: [...]` tam liste** |

### 2.4 KRİTİK BULGU: iz bir zamanlar VARDI, KALDIRILDI

`nous_call_skills`, çağrı başına **skill adlarını** yazan tek olaydı:

```json
{"ts":"2026-07-20T09:59:21+00:00","event":"nous_call_skills","kind":"review","preloaded":5,
 "names":["vcp-screener","pullback-screener","pre-trade-discipline-gate","position-sizer",
          "market-environment-analysis"]}
```

Son basıldığı an: **2026-07-20T10:06:49**. Bugün `grep -rn "nous_call_skills" meridian/` → **SIFIR
eşleşme**. `_agent_call` yeniden yazılırken bu olay `obs.log("agent_call", …, preloaded=len(preload))`
ile değiştirilmiş; **liste sayıya çökmüş** ve bir daha geri gelmemiş. Ölçüm boşluğu bir eksiklik
değil, bir **gerileme**dir.

---

## 3. `last_run` KİM YAZIYOR — LLM değil, DETERMİNİSTİK MOTOR

**Tek yazıcı:** `skills._touch_registry_run` (`meridian/skills.py:621`).
**Tek çağıran:** `skills.pipeline_run` (`meridian/skills.py:655-656`):

```python
invoked  = [s for s in en if s in ENGINE_IMPLEMENTED]      # skills.py:639
declared = [s for s in en if s not in ENGINE_IMPLEMENTED]  # skills.py:640
...
for s in invoked:                                          # skills.py:655
    _touch_registry_run(s, artifact)
```

`hermes.py` içinde `_touch_registry_run`'a **hiç çağrı yok**. Yani:

> **`last_run`, LLM çağrısını DEĞİL, deterministik boru hattı koşumunu damgalar.**
> Bir skill'in `last_run`'ı boş olması "LLM onu hiç kullanmadı" demek DEĞİLDİR;
> "deterministik motor onu koşturmadı" demektir. İkisi farklı katmanlardır ve
> pano bugün ikisini tek alanla temsil ediyor.

**Kanıt (canlı, 13 dolu kayıt):** `ENGINE_IMPLEMENTED` 13 elemanlı, enabled ile kesişimi 13 ve
`last_run` dolu olan kayıt sayısı **tam 13**. Örtüşme **birebir**, tesadüf değil.

Damga zamanları da bunu doğruluyor — hepsi **tek bir boru-hattı koşumundan**, 21 saniye içinde:

| skill | last_run | last_artifact |
|---|---|---|
| portfolio-manager, drawdown-circuit-breaker | 2026-08-12T20:44:37 | `state/trades.jsonl` |
| pead-screener, stockbee-episodic-pivot-analyzer, data-quality-checker, finviz-screener, stockbee-exhaustion-hammer-screener, stockbee-momentum-burst-screener, vcp-screener, pullback-screener | 2026-08-12T20:44:56 | `state/candidates.jsonl` |
| earnings-calendar, position-sizer, pre-trade-discipline-gate | 2026-08-12T20:44:57 | `state/trade_plans.jsonl` |

`pipeline_runs.jsonl` (117 satır) da **2026-08-12T20:44:58'de duruyor** — boru hattı defteri o günden
beri hiç yazılmamış, oysa `agent_calls.jsonl` 2026-08-13T17:26'ya kadar akıyor. İki katman zaten
ayrışmış durumda.

**Ek olarak:** 17 kayıtta `stale_last_run_cleared: 2026-07-15T08:54:23` alanı var — geçmişte
"declared-only" skill'lere yanlışlıkla basılan damgaların temizlendiği vaka. Aynı hatanın izi
kayıtta duruyor.

---

## 4. PAYDA DÜRÜSTLÜĞÜ — pano ne diyor, ölçüm ne diyor

Pano metni (`meridian/web/app.js:6418`):
> "… hüküm verilebilen skill / katalog · **N** gerçek katmanda hiç ölçülmemiş · **M** motor içi (aday değil)"

Eksen-2 evren muhasebesi (`meridian/skill_gorus.py:70-99`, canlı koşum):
```
{"evren": 8, "arsiv": 36, "korumali": 5, "llm_baglamli_motor_kosturmuyor": 18}
```

`llm_baglamli_motor_kosturmuyor` kovası (`skill_gorus.py:89-91`) şu tanıma dayanıyor:
`ad not in skills.ENGINE_IMPLEMENTED`.

### 4.1 Bu kova DOĞRU mu? → **Kendi amacı için EVET; "aktif" saymak için YETERSİZ**

Kova adı ne dediğini tam söylüyor: *deterministik motor bunları koşturmuyor.* Bu **doğru** ve
eksen-2'nin amacı (skill'e "görüş" atfetmek) için **doğru kapı** — `screener`/`skill_chain` yazılı
atıf yoksa görüş üretilemez. Ama operatörün sorduğu soru farklı: *bu 18 skill LLM tarafından
çağrılabiliyor mu, çağrılıyor mu?* Kovanın adı bunu cevaplamıyor, çünkü **ölçmüyor**.

### 4.2 Ölçüm: enabled 30 = motor-içi 13 + LLM-bağlamlı 17

(18'in biri — `institutional-flow-tracker` — aktif ama `enabled: False`; katalogda 31 aktif kayıt var,
30'u enabled.)

| katman | n | `-s` ile isteme girdi mi | LLM `skill_view` ile açtı mı |
|---|---|---|---|
| MOTOR-İÇİ (13) | 13 | 8'i evet, **5'i hiç** | 4'ü evet, 9'u hiç |
| LLM-BAĞLAMLI (17) | 17 | 5'i evet, **12'si hiç** | **0** |

**Tam tablo (canlı `.usage.json` × kayıt defteri):**

| skill | katman | sunuldu | `-s` yüklendi (n · son) | `skill_view` (n · son) |
|---|---|---|---|---|
| pre-trade-discipline-gate | MOTOR | ✓ | 1132 · 2026-08-13T17:26 | **1 · 2026-08-10T07:13** |
| market-environment-analysis | LLM | ✓ | 1131 · 2026-08-13T17:26 | hiç |
| position-sizer | MOTOR | ✓ | 1131 · 2026-08-13T17:26 | hiç |
| pullback-screener | MOTOR | ✓ | 1113 · 2026-08-13T17:13 | hiç |
| vcp-screener | MOTOR | ✓ | 1097 · 2026-08-13T17:13 | **3 · 2026-08-13T14:18** |
| stockbee-exhaustion-hammer-screener | MOTOR | ✓ | 712 · 2026-08-13T17:13 | **5 · 2026-08-13T14:03** |
| stockbee-momentum-burst-screener | MOTOR | ✓ | 421 · 2026-08-13T17:13 | hiç |
| backtest-expert | LLM | ✓ | 18 · 2026-08-13T17:26 | hiç |
| edge-strategy-reviewer | LLM | ✓ | 18 · 2026-08-13T17:26 | hiç |
| macro-regime-detector | LLM | ✓ | 18 · 2026-08-13T17:26 | hiç |
| market-breadth-analyzer | LLM | ✓ | 18 · 2026-08-13T17:26 | hiç |
| portfolio-manager | MOTOR | ✓ | 18 · 2026-08-13T17:26 | hiç |
| stockbee-episodic-pivot-analyzer | MOTOR | ✓ | 12 · 2026-08-05T19:54 | **2 · 2026-08-05T07:43** |
| canslim-screener | LLM | ✓ | **hiç** | hiç |
| economic-calendar-fetcher | LLM | ✓ | **hiç** | hiç |
| edge-pipeline-orchestrator | LLM | ✓ | **hiç** | hiç |
| exposure-coach | LLM | ✓ | **hiç** | hiç |
| ibd-distribution-day-monitor | LLM | ✓ | **hiç** | hiç |
| market-top-detector | LLM | ✓ | **hiç** | hiç |
| parabolic-short-trade-planner | LLM | ✓ | **hiç** | hiç |
| strategy-pivot-designer | LLM | ✓ | **hiç** | hiç |
| theme-detector | LLM | ✓ | **hiç** | hiç |
| trading-skills-navigator | LLM | ✓ | **hiç** | hiç |
| uptrend-analyzer | LLM | ✓ | **hiç** | hiç |
| weekly-performance-digest | LLM | ✓ | **hiç** | hiç |
| data-quality-checker | MOTOR | ✓ | **hiç** | hiç |
| drawdown-circuit-breaker | MOTOR | ✓ | **hiç** | hiç |
| earnings-calendar | MOTOR | ✓ | **hiç** | hiç |
| finviz-screener | MOTOR | ✓ | **hiç** | hiç |
| pead-screener | MOTOR | ✓ | **hiç** | hiç |

*(`sunuldu` = `<available_skills>` kataloğunda listelendi ve `skill_view` aracıyla açılabilir
durumdaydı — 30/30.)*

### 4.3 HÜKÜM: bu bir payda şişmesi DEĞİL, bir **kullanım kusuru**

Operatörün ikilemine cevap:
> *"Çağrılamıyorsa 'aktif' sayılmaları payda şişirmesidir; çağrılabiliyor ama çağrılmıyorsa ayrı bir
> kusurdur. HANGİSİ?"*

**İKİNCİSİ — ölçüldü.** 30'unun tamamı katalogda listeleniyor ve `skill_view` aracı tanımlı, yani
**çağrılabiliyorlar**. 17'si (12 LLM-bağlamlı + 5 motor-içi) hiçbir isteme hiç girmemiş ve LLM
hiçbirini kendiliğinden açmamış. Bu bir "aktif diye sayma" hatası değil; **sunulan ama kullanılmayan
kapasite**dir.

### 4.4 Kullanılmamanın ölçülmüş NEDENİ: istem içinde birbiriyle çelişen iki talimat

Aynı sistem isteminin içinde:

* **Hermes çekirdeği (`## Skills (mandatory)`)**:
  > "…you **MUST** load it with `skill_view(name)` and follow its instructions. Err on the side of loading…"
* **Meridian brifingi (`~/.hermes/SOUL.md` → sistem isteminin 1236. karakteri)**:
  > "- Meridian'dan gelen istekler tek bir JSON nesnesi ister. YALNIZCA istenen JSON'u döndür;
  >   **araç çağrısı**, dosya değişikliği, düzyazı ekleme **yok**."

Aynı brifing iki satır önce şunu da diyor: *"Bir soru geldiğinde önce ilgili skill'in SKILL.md'sini
oku, metodolojiyi ORADAN uygula"* — ama SKILL.md'yi okumanın **tek yolu `skill_view` aracıdır** ve
o araç yasaklanmıştır. Talimat, kendi ön-koşulunu yasaklıyor.

Ölçülen sonuç: **1.113 ajan oturumunda 11 `skill_view` + 1 `skills_list` = 12 skill aracı çağrısı
(%1,1).** Model, iki talimattan yasaklayana uyuyor. Bu, kapasitenin neden atıl kaldığının
**davranışsal kanıtıdır**, tahmini değil.

Karşılaştırma — aynı pencerede TÜM araç çağrıları:
```
search_files 155 · read_file 56 · execute_code 29 · skill_view 11 · session_search 3 · skills_list 1
```
Model araç kullanmayı biliyor ve kullanıyor; kullanmadığı özellikle **skill araçları**.

---

## 5. ZAMAN SERİSİ — hangi skill ne zaman çağrıldı

### 5.1 LLM'İN KENDİ AÇTIĞI SKILL'LER — tam liste (12 çağrı, eksiksiz)

Kaynak: `~/.hermes/logs/agent.log{,.1,.2,.3}` `agent.tool_executor: tool skill_view` satırları,
oturum kimliğiyle `agent.turn_context` istemine bağlanarak. Hedef skill ataması
`.usage.json`'daki `view_count`/`last_viewed_at` ile çaprazlandı — **11 çağrı ↔ 11 `view_count`
toplamı birebir tutuyor.**

| # | zaman (UTC) | araç | oturum | model | çağıran | hedef skill |
|---|---|---|---|---|---|---|
| 1 | 2026-08-04 13:29:13 | `skill_view` | 20260804_132428_b9dc76 | gemini-3.5-flash | Meridian `review` | vcp-screener |
| 2 | 2026-08-05 07:42:34 | `skill_view` | 20260805_074056_95d403 | gemini-3.5-flash | Meridian `review` | stockbee-episodic-pivot-analyzer |
| 3 | 2026-08-05 07:43:00 | `skill_view` | 20260805_074056_95d403 | gemini-3.5-flash | Meridian `review` | stockbee-episodic-pivot-analyzer |
| 4 | 2026-08-10 07:13:16 | `skills_list` | 20260810_071256_b645ad | gemini-3.5-flash | Meridian `review` | (katalog listesi) |
| 5 | 2026-08-10 07:13:18 | `skill_view` | 20260810_071256_b645ad | gemini-3.5-flash | Meridian `review` | stockbee-exhaustion-hammer-screener |
| 6 | 2026-08-10 07:13:23 | `skill_view` | 20260810_071256_b645ad | gemini-3.5-flash | Meridian `review` | pre-trade-discipline-gate |
| 7 | 2026-08-11 07:32:09 | `skill_view` | 20260811_073153_e571da | gemini-3.5-flash | Meridian `review` | vcp-screener |
| 8 | 2026-08-12 20:11:53 | `skill_view` | 20260812_201137_e636a1 | gemini-3.5-flash | Meridian `review` | stockbee-exhaustion-hammer-screener |
| 9 | 2026-08-12 20:11:55 | `skill_view` | 20260812_201137_e636a1 | gemini-3.5-flash | Meridian `review` | stockbee-exhaustion-hammer-screener |
| 10 | 2026-08-13 14:03:04 | `skill_view` | 20260813_140258_2d7884 | gemini-flash-latest | Meridian `review` (**sprint**) | stockbee-exhaustion-hammer-screener |
| 11 | 2026-08-13 14:03:06 | `skill_view` | 20260813_140258_2d7884 | gemini-flash-latest | Meridian `review` (**sprint**) | stockbee-exhaustion-hammer-screener |
| 12 | 2026-08-13 14:18:05 | `skill_view` | 20260813_141757_571ff0 | gemini-flash-latest | Meridian `review` (**sprint**) | vcp-screener |

**12/12'si Meridian'ın kendi otomatik `review` çağrısından** (`agent.turn_context` istemi:
*"You advise Meridian's candidate pipeline. Using your preloaded Meridian skills…"*). Pencerede
kayıtlı 1.113 oturumun 1.111'i bu aday-danışma istemini taşıyor; kalan 2'si de Meridian kaynaklı
(2026-08-04 01:13/01:14, istem: *"SYSTEM prompt'undaki görev (tek parametre hipotezi) BU TURDA
GEÇERLİ DEĞİL…"*) ve ikisi de skill aracı çağırmadı. **Operatörün elle açtığı bir oturum yok** —
yani 11 `skill_view`'ın tamamı otomatik yoldan gelmiştir, insan eliyle değil.

**Pencere sınırı (beyan):** `agent.log` ailesi **2026-07-30 14:40 → 2026-08-13 17:26** arasını
kapsıyor. Bu tarihten öncesi log rotasyonuyla düşmüştür → **ÖLÇÜLEMEDİ** (defter yok, tahmin
yazılmadı). `.usage.json` kayıtları da 2026-08-02'de oluşmuş, ondan öncesi kümülatif sayaçta yok.

### 5.2 `-s` ÖN-YÜKLEME ZAMAN SERİSİ — sayı var, ad **YOK**

`agent_calls.jsonl` / `events.jsonl` gün bazında (canlı, `tasiyici=yerel_ajan`):

| gün | agent_call | kind dağılımı |
|---|---|---|
| 2026-08-07 | 124 | review 150* |
| 2026-08-08 | 151 | review |
| 2026-08-09 | 156 | review 148 · proposal 2 |
| 2026-08-10 | 151 | review 150 |
| 2026-08-11 | 150 | review 150 |
| 2026-08-12 | 29 | review 21 · proposal 5 · backfill 3 |
| 2026-08-13 | 9 | proposal 9 |

*(olay defteri ile telemetri defteri gün kesitinde bir kaç satır ayrışıyor — telemetri 2026-08-07
03:48'de başlıyor.)*

**Bu tablodan "hangi skill" çıkarılamaz.** `on_yukleme_n` dağılımı yalnız şunu verir:
`{6: 739, 8: 16, 5: 3, 0: 12}`. Adları ancak `_skill_preload`'u **yeniden koşturup türeterek**
tahmin edebilirdim — ki bu defterde olmayan bir şeyi "olmuş" saymak olurdu, **UYDURMA YASAĞI**.
→ **skill × tarih zaman serisi `-s` yolu için ÖLÇÜLEMEDİ; neden: defterde alan yok
(`nous_call_skills` kaldırıldı, §2.4).**

Elde kalan tek çapa: `.usage.json`'daki **kümülatif** `use_count` + **yalnız son** `last_used_at`.
Yani "kaç kez" ve "en son ne zaman" biliniyor, **"hangi günlerde" bilinmiyor**.

### 5.3 Tutarlılık denetimi (iki bağımsız defter aynı şeyi söylüyor mu?)

```
2026-08-02'den beri agent_call (canlı):  1.151 çağrı · toplam ön-yükleme slotu: 6.939
~/.hermes/skills/.usage.json toplam use_count:                                  6.839
```
%98,6 örtüşme. Fark (100 slot), `.usage.json`'ın **2026-08-02T14:28**'de oluşmasıyla açıklanır — o
günün ilk 14 saatindeki çağrılar sayaca girmemiş. Bu, `use_count`'un gerçekten **`-s` enjeksiyon
sayacı** olduğunun bağımsız doğrulamasıdır.

Kaynak kod doğrulaması (`~/.hermes/hermes-agent/`):
* `tools/skill_usage.py:783` `bump_use` — *"Called when a skill is actively used (e.g. **loaded into
  the prompt path**…)"*; çağıranı `agent/skill_commands.py:597` (`build_preloaded_skills_prompt` →
  `-s` yolu).
* `tools/skill_usage.py:771` `bump_view` — *"Called from `skill_view()`"*; çağıranı
  `tools/skills_tool.py:1796` `_skill_view_with_bump`.

> **İki sayaç iki AYRI olguyu ölçüyor ve karıştırılırsa teşhis çöker:**
> `use_count` = *Meridian bu skill'i isteme bastı* · `view_count` = *LLM bu skill'i kendisi açtı*.

---

## 6. ÖLÇÜM BOŞLUKLARI — adıyla

### B1 — `agent_calls.jsonl` / `agent_traces.jsonl` / `agent_call` olayı skill ADI taşımıyor
Üç defter de yalnız `on_yukleme_n` / `preloaded` sayısını yazıyor
(`meridian/agent_telemetry.py:240`, `meridian/hermes.py:2015`). *Hangi* skill'in hangi çağrıda
bulunduğu Meridian tarafından **hiç bilinemez**. **Gerileme:** bu bilgi `nous_call_skills` olayında
vardı, 2026-07-20'den beri kaldırılmış (§2.4).

### B2 — Araç kullanımı `-Q` altında ölçülemiyor
`arac_cagri_n` canlı defterde **770/770 satırda `None`**. Sessiz mod CLI oturum özetini bastırdığı
için `_agent_tool_calls` (`meridian/hermes.py:1693`) hiçbir şey yakalayamıyor. Boşluk dürüstçe
`arac_neden` alanıyla beyan edilmiş — ama sonuç yine de körlük: **LLM'in skill açıp açmadığı
Meridian'ın kendi defterinden okunamıyor.** (Bu denetim onu ancak ajanın **kendi** log'undan
çıkarabildi.)

### B3 — Gerçek çağrı izi ÜÇÜNCÜ TARAF defterinde ve Meridian onu okumuyor
`~/.hermes/skills/.usage.json` + `~/.hermes/logs/agent.log` sorunun tam cevabını taşıyor. Repo'da
bu iki yolu okuyan **tek satır kod yok**. Sahibi Hermes CLI; budama/rotasyon politikası da onun
(agent.log 5 MB'da dönüyor → tarihsel iz sessizce kayboluyor).

### B4 — Kum havuzu sprint'leri canlı ajanın skill dizinini bozuyor
`AGENT_SKILLS_DIR` (`hermes.py:2562`) tek ve paylaşımlı. Sprint (FMP anahtarsız) 4 `fmp=req`
skill'i canlının symlink'lerinden **söküyor** (kanıt: sprint defterinde
`2026-08-13T15:20:13 pruned=[parabolic-short-trade-planner, ibd-distribution-day-monitor,
canslim-screener, economic-calendar-fetcher]`). Söküm ile bir sonraki canlı senkron arası
**pencerenin süresi ölçülmedi** (senkron 5 dakikada bir standby döngüsünde koşuyor → üst sınır
~5 dk, ama bu **türetilmiş**, ölçülmüş değil). O pencerede canlı ajan bu 4 skill'i **görmüyor**.

### B5 — `last_run` iki ayrı olguyu tek alanda temsil ediyor
Deterministik boru-hattı damgası, pano ve okuyucular tarafından "skill kullanıldı" gibi
okunabiliyor. LLM katmanının karşılığı olan alan **yok**. Bunun bir kez zarar verdiğinin izi
kayıtta duruyor: 17 kayıtta `stale_last_run_cleared: 2026-07-15T08:54:23`.

### B6 — `agent_skills_synced.linked` alanının anlamı yanıltıcı
Olayda `linked` = *yeni kurulan* symlink sayısı; `agent_skill_coverage()`'ta `linked` =
*enabled ∩ bağlı* toplamı. **Aynı ad, iki anlam.** Olayı tek başına okuyan biri "30 enabled'ın
yalnız 4'ü bağlı" sanır (bu denetimin ön-ölçümünde de tam olarak bu olmuştu).

### B7 — `pipeline_runs.jsonl` durmuş
Son satır **2026-08-12T20:44:58**; `agent_calls.jsonl` 2026-08-13T17:26'ya kadar akıyor. Boru
hattı damgası ile LLM katmanının **zaten** ayrıştığının kanıtı. Durmasının nedeni bu kartın
kapsamı dışında → **ÖLÇÜLMEDİ**, ayrı kalem.

### B8 — `-s` yolunun tarih bazlı zaman serisi kurtarılamıyor
`.usage.json` kümülatif sayaç + tek `last_used_at` tutuyor; gün gün dağılım yok. `-s` listeleri
defterde olmadığı için geriye dönük **rekonstrüksiyon imkânsız**. Bugünden itibaren kaydedilmezse
bu geçmiş kalıcı olarak kayıptır.

---

## 7. ÖNERİ — çağrı izini görünür kılmak için EN KÜÇÜK değişiklik

> Kod yazılmadı; öneridir. Sıra maliyet/kazanç oranına göredir.

### Ö1 (ZORUNLU · ~1 satır) — kaldırılan alanı geri koy
`meridian/hermes.py:2015`'teki `agent_call` olayına ad listesini ekle:

```python
obs.log("agent_call", kind=kind, preloaded=len(preload),
        skills=list(preload),          # ← TEK EKLEME
        model=…, attempt=…, empty=…, …)
```

Bu, 2026-07-20'de kaybedilen `nous_call_skills` bilgisini **var olan olaya** geri getirir. Yeni
defter, yeni şema, yeni okuyucu gerekmez. Tavan riski yok: `preload` en fazla 8 kısa ad
(~200 bayt/olay). §B1'i kapatır ve §B8'i **bugünden ileriye** açar.

**Simetrik ikinci satır:** `meridian/agent_telemetry.py:236` satırına `on_yukleme` (liste) alanı —
`on_yukleme_n`'in yanına, onu silmeden. Telemetri defteri ile olay defteri `iz_id` ile birleştiği
için tek yer bile yeterlidir; ikisi de yapılırsa defterler kendi başlarına okunabilir kalır.

### Ö2 (YÜKSEK KAZANÇ · ~15 satır) — ajanın kendi sayacını Meridian'a bağla
`~/.hermes/skills/.usage.json` sorunun cevabını **zaten** taşıyor ve kimse okumuyor (§B3). Küçük
bir okuyucu (`skills.ajan_kullanim()` gibi) bu dosyayı okuyup `catalog()` çıktısına iki alan
eklesin:

* `ajan_yukleme_n` (= `use_count`) — *Meridian isteme kaç kez bastı*
* `ajan_acilma_n` (= `view_count`) + `son_acilma` — ***LLM kaç kez kendisi açtı***

**Bu ikincisi bugün sistemde HİÇ karşılığı olmayan sinyaldir** ve operatörün sorusunun tam
cevabıdır. Pano "31 aktif skill" derken artık *"…30'u sunuluyor, 13'ü isteme giriyor, 4'ü LLM
tarafından açılmış"* diyebilir. Dosya yoksa alanlar `None` + neden (UYDURMA YASAĞI'na uygun).

### Ö3 (DÜRÜSTLÜK · 0 satır kod, 2 satır metin) — SOUL.md çelişkisini kaldır
`~/.hermes/SOUL.md`'deki *"araç çağrısı … yok"* yasağı, aynı istemin *"skill'in SKILL.md'sini oku"*
talimatının **ön-koşulunu** yasaklıyor (§4.4). Ölçülen bedel: 1.113 oturumda 12 skill aracı çağrısı.
Önerilen düzeltme — yasağı **çıktı biçimine** daraltmak, araç kullanımına değil:

> "…**CEVABIN** yalnızca istenen JSON nesnesi olsun (düzyazı/markdown yok). Karar vermeden önce
> ilgili skill'i `skill_view` ile açabilirsin; dosya değiştirme ve terminal komutu yasaktır."

Bu, operatör onayı isteyen tek kalemdir (canlı ajan davranışını değiştirir) ve **§4.3'teki kusurun
tek gerçek kaldıracıdır** — Ö1/Ö2 kusuru *görünür* kılar, Ö3 *giderir*.

### Ö4 (SIZINTI KAPISI) — sprint'e kendi skill dizinini ver
`AGENT_SKILLS_DIR`'ı sabit yol yerine state-dizinine bağlı hale getir (ya da sprint koşumunda
`HOME`/`HERMES_HOME` ayır). §B4'teki canlı-kum havuzu sızıntısı kapanır. "Canlı defterden izole"
vaadi ancak o zaman ajan katmanı için de doğru olur.

### Ö5 (KÜÇÜK · adlandırma) — `agent_skills_synced.linked` alanını yeniden adlandır
`linked` → `yeni_baglanan`; toplam kapsam için `bagli_toplam=len(enabled & linked)` ekle (§B6).
Bu denetimin ön-ölçümünde bile yanlış okunmuş bir alandır.

---

## EK — ölçüm komutları (yeniden üretilebilirlik)

Tüm ölçümler şu kalıpla, salt-okuma olarak koşuldu:
```
ssh -i ~/.ssh/oci-a1.key ubuntu@130.61.126.87 'cd /opt/meridian && ./.venv/bin/python -' < betik.py
```

Okunan canlı kaynaklar:
`/opt/meridian/state/{skills_registry.json, agent_calls.jsonl, agent_traces.jsonl, events.jsonl,
pipeline_runs.jsonl}` · `/opt/meridian/state/sprint/*/state/{agent_calls.jsonl, events.jsonl,
skills_registry.json}` · `~/.hermes/skills/{.usage.json, symlink'ler}` · `~/.hermes/sessions/*.json`
(958 başarısız istek dökümü) · `~/.hermes/logs/agent.log{,.1,.2,.3}` · `~/.hermes/config.yaml` ·
`~/.hermes/SOUL.md` · `~/.hermes/hermes-agent/{tools/skill_usage.py, tools/skills_tool.py,
agent/skill_commands.py, hermes_cli/_parser.py}`.

Repo kaynakları: `meridian/hermes.py` · `meridian/skills.py` · `meridian/agent_telemetry.py` ·
`meridian/skill_gorus.py` · `meridian/web/app.js`.
