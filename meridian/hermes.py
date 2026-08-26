"""hermes.py — Meridian'ın öneri üreten beyni: durum okur, TEK değişkenlik bir hipotez kurar ve
onu karar yetkisi olmayan bir danışman olarak kapıya sunar.

Ne yapar: defter/rejim/skill durumundan bir kanıt paketi kurar, beyin zincirindeki ilk hazır
sağlayıcıdan (Claude → Nous → Gemini) tek-değişkenlik bir hipotez ister ve `reflect.submit`e
teslim eder. Beyin boş dönerse ya da öneri kapıdan dönerse üretim pencerelerinde sistematik
koordinat-inişi araması (`reflect.search_and_submit`) koşulur. Canlıda ayrık bir tmux
oturumunda `--loop` ile yaşar; anahtar yokken deterministik yola düşer — döngü asla ölmez.

Kilit girişler: `reflect_once` (tek canlı yansıma: LLM önerisi → bakir düğme → arama),
`propose_with_llm` (beyin zinciri: bütçe kapısı, soğuma, boş-cevap sınıflandırması),
`propose_virgin_knob` (beyinsiz turda hiç denenmemiş düğmeden deterministik öneri, guard
ön-denetimli), arka plan süzgeci (`background=True` turunda `@`siz öneri sertifikalı rejime
çivilenir; farklı-rejim/sertifikasız öneri `_bg_on_eleme_kaydi` ile reddedilir).

Değişmezler: tek-değişken yasası (buradaki her kısıt guard.py'de AYRICA zorlanır — istem öneri,
guard yasadır); öneri=danışma, karar=kapı — tek ship yetkisi `reflect.submit`tedir ve hermes
strategy.yaml'a asla elle dokunmaz; aylık bütçe kapısı (`spend.over_budget`) tüm ücretli
beyinleri kapatır; aramanın K sondası kazananın-laneti cezası olarak `probes_tested` ile
kapıya beyan edilir.

Okur/yazar: bounds.yaml, goal.yaml, regime.json, hypotheses.jsonl (bağlam; memory üzerinden)
okur; events.jsonl'a olay (obs), spend.jsonl'a maliyet, agent_calls/agent_traces defterlerine
çağrı telemetrisi yazar; `SEARCH_PROGRESS` canlı arama durumunu /api/hermes → panoya taşır.
YAŞAYAN UYARI: arka plan süzgecinin retleri hypotheses.jsonl'a DEĞİL events.jsonl'a yazılır —
hipotez defterinin sekiz tüketicisi satırı duruma bakmadan sayar (ölü-aile ilanı, öğrenme-
canlılık alarmı, selfreview pencereleri, kamuya açık ship-oranı paydası) ve reddedilen öneri
"aday" değildir; deftere aday gibi girmesi öneri uzayını daraltır ve alarm maskeler."""
from __future__ import annotations
import argparse
import calendar
import json
import os
import sys
import threading
import time

from . import config, store, memory, reflect, health, obs, secrets
# 2026-08-13: şema enum'unun TEK kaynağı için modül düzeyinde gerekli (aşağıda
# HYP_SCHEMA sabit bir sözlük). Döngü YOK: `skills` MODÜL DÜZEYİNDE yalnız `config`+`store` çeker.
# NOT (2026-08-13): `skills.catalog()` artık ÇAĞRI ANINDA buraya geri bakıyor
# (`skills._ajan_skill_dizini` → `AGENT_SKILLS_DIR`) — ajan kullanım sayacının yolu TEK yerde
# tanımlı kalsın diye. Bu bir modül-düzeyi döngüsü DEĞİLDİR (geç ithal + `getattr` savunması);
# yukarıdaki cümlenin koruduğu özellik — skills'in modül düzeyinde hermes'i çekmemesi — DURUYOR.
from . import skills as _skills
from . import agent_telemetry as _at        # çağrı telemetrisi + ham iz + MASKELEME

MODEL = os.environ.get("HERMES_MODEL", "claude-opus-4-8")

# Live view of the running coordinate-descent search, published per probe and read by
# hermes_runtime.status() → /api/hermes → dashboard. A search runs ~a dozen walk-forwards (many minutes);
# without this the operator sees only "reflecting: true" and cannot tell progress from a hang.
SEARCH_PROGRESS: dict = {}

# Bellekteki `SEARCH_PROGRESS`in SÜREÇLER-ARASI nüshası (Ö-50). Okuyucu sözleşmesi ÜÇ DEĞERLİDİR
# ve `search_progress_oku()`dadır — "dosya yok / bayat" ile "arama yok" AYNI ŞEY DEĞİLDİR.
SEARCH_PROGRESS_FILE = "search_progress.json"


def _progress(**alanlar) -> None:
    """SEARCH_PROGRESS'in TEK yazım kapısı (2026-08-12 asılı-arama vakası): her yazım
    `updated_at` (UTC ISO, kanonik `memory.now_iso`) damgası taşır.

    NEDEN: canlı vakada bayrak günlerce `running=True` kaldı ve "bu bayrak EN SON ne zaman
    yazıldı?" sorusunun defter-üstü cevabı YOKTU — teşhis, olay defterinden geriye saat saymakla
    yapıldı. Damga o cevabı bayrağın kendisine koyar (hermes_runtime:522 aynı sözlüğü /api/hermes'e
    aynen render eder; asılı aramada saat DONMUŞ görünür — sinyalin kendisi budur).

    Sprint'in bayatlık yasasına (`sprint._arama_durumu`) BİLEREK GİRMEZ: parmak izi faz/i/total/değişken/
    değer beşlisidir; damga ize girseydi içeriksiz her yazım "ilerleme" gibi okunur, bayatlık
    yasası körleşirdi. Damga parmak-izine EK sinyaldir, parçası değil.

    DİSK AYNASI (2026-08-17, Ö-50 süreç ayrımı): bellek sözlüğü artık `SEARCH_PROGRESS_FILE`a da
    yansıtılır. NEDEN: öğrenme döngüsü kendi systemd birimine taşınınca bu sözlüğün İKİ tüketicisi
    (`hermes_runtime.status` → pano, `sprint._arama_durumu` → sprint kapısı) başka SÜREÇTE kalır ve
    orada sözlük boş görünür. `sprint`in muhafazakâr yedeği ("okunamıyorsa MEŞGUL say") bu durumda
    ATEŞLENMEZ — sözlük okunamaz değil, BOŞtur → `running` falsy → koşan aramanın üstüne antrenman
    başlatılırdı. Ayna bu yüzden kozmetik değil EMNİYET kalemidir.
    Yazım burada, çünkü burası tek kapıdır: üç üretici de otomatik kapsanır, yeni yazım yolu
    açılmaz. Kısma (throttle) YOK ve gerekmiyor — her yazım bir sondanın (walk-forward backtest)
    ardından gelir, yani saniyeler-dakikalar aralıklı; dosya küçük ve yazım atomiktir."""
    SEARCH_PROGRESS.update(dict(alanlar, updated_at=memory.now_iso()))
    _progress_aynala()


def _progress_aynala() -> None:
    """`SEARCH_PROGRESS`i diske yansıtır. Yazım düşerse arama DURMAZ (YASA 4: beyanlı yutma —
    ayna bir teşhis/emniyet yüzeyidir, arama onun başarısına bağlı değildir; düşerse okuyucular
    'ölçülemedi' görür ve muhafazakâr tarafa düşer, sessizce 'meşgul değil' okumazlar)."""
    try:
        store.write_json(SEARCH_PROGRESS_FILE, dict(SEARCH_PROGRESS))
    except Exception as e:  # sessiz-yutma: ayna yazımı düşse bile arama sürmeli; okuyucu tarafı bayatlıktan ölçülemedi der ve muhafazakâr tarafa düşer
        obs.warn("search_progress_ayna_yazilamadi", error=f"{type(e).__name__}: {e}",
                 detail="disk aynası yazılamadı — tüketiciler 'ölçülemedi' görecek (muhafazakâr taraf)")


def _progress_temizle() -> None:
    """Bayrağı sıfırlar — `SEARCH_PROGRESS.clear()`in KAPIDAN GEÇEN hâli.

    NEDEN VAR: `_progress`in docstring'i kendini "TEK yazım kapısı" ilan ediyordu ama çıplak bir
    `.clear()` çağrısı (eski `_reflect_once_govde` girişi) kapıyı ATLIYORDU. Bellekte bu zararsızdı
    (aynı sözlük); diske aynayınca zararlı olurdu: dosya `running=True` DONAR ve sprint kapısı
    sonsuza dek kapalı kalırdı. Temizleme de kapıdan geçer."""
    SEARCH_PROGRESS.clear()
    _progress_aynala()


def search_progress_oku(ayni_surec: bool = False) -> dict:
    """Arama ilerlemesini SÜREÇLER-ARASI okur. Tüketici: pano (`hermes_runtime.status`) ve sprint
    kapısı (`sprint._arama_durumu`) — ikisi de Ö-50 ayrımından sonra başka süreçte olabilir.

    ÜÇ DEĞERLİ, ve bu ayrım UYDURMA YASAĞInın gereğidir: "dosya yok / bayrak bayat" ile "arama
    koşmuyor" AYNI ŞEY DEĞİLDİR. İkisini birleştirmek tam olarak Ö-50'nin kapattığı tuzaktır
    (boş sözlük sessizce "meşgul değil" diye okunuyordu).

      durum="kosuyor"     — kayıt var ve `running` doğru
      durum="yok"         — kayıt var, `running` yanlış (arama gerçekten koşmuyor)
      durum="olculemedi"  — dosya yok / bozuk / damgasız. ÇAĞIRAN MUHAFAZAKÂR TARAFA DÜŞER.

    EŞİK BURADA YOK — `yas_s` (damganın yaşı, saniye) döner ve bayatlık hükmünü her tüketici KENDİ
    yasasıyla verir (sprint'in `ARAMA_BAYAT_SAAT`i onun kanunudur, bu modülün değil; ayrıca
    `hermes → sprint` içe aktarımı döngü olurdu). Yeni eşik icat EDİLMEDİ (madde 3).

    `ayni_surec=True` verilirse bellekteki sözlük yetkilidir (öğrenme döngüsünün KENDİ süreci
    içindeki çağrılar) — disk turu boşuna yapılmaz."""
    import datetime as _dt
    # KAYNAK SIRASI (2026-08-17, suite 12 kırmızıyla öğretti): BELLEK DOLUYSA BELLEK YETKİLİDİR.
    # İlk hâlde varsayılan doğrudan diske gidiyordu ve bu YANLIŞTI: aynı süreçte koşan bir yazar
    # (bekleme döngüsü, ya da `SEARCH_PROGRESS`i doğrudan kuran testler) belleği diskten DAHA TAZE
    # tutar — diske düşmek o süreci kendi yazdığı bayrağa kör bırakırdı.
    # EMNİYET BOZULMUYOR, çünkü ayrımın kapattığı tuzak "BOŞ bellek" tuzağıydı: öğrenme kendi
    # biriminde koşarken sprint'in belleği boştur → disk okunur → doğru cevap. Dolu bellek ise
    # zaten o süreçte gerçek bir yazarın varlığının kanıtıdır.
    ham = dict(SEARCH_PROGRESS) if (ayni_surec or SEARCH_PROGRESS) else store.read_json(SEARCH_PROGRESS_FILE, None)
    if ham is None:
        # DOSYA YOKLUĞU = ARAMA YOK (2026-08-17, suite 7 kırmızıyla düzeltti; `_kalp_canliligi`
        # ile AYNI hüküm — tutarlı olmak zorundayım). Gerekçe mekanizmada: `_progress` bayrağı
        # aramanın BAŞINDA yazar, yani koşan bir arama varsa dosya VARDIR. Yokluğu bir ölçüm
        # boşluğu değil, "hiç arama koşmadı"nın kanıtıdır.
        # ÖNCE "olculemedi" DİYORDUM ve bu sprint'i kalıcı MEŞGUL'e kilitliyordu: temiz bir
        # kurulumda dosya hiç doğmaz, sprint hiç başlayamazdı. Muhafazakârlık iyidir, kilitlemek
        # değil. Yazım DÜŞERSE sessiz kalmıyoruz — `_progress_aynala` uyarı basıyor.
        return {"durum": "yok", "kayit": {}, "yas_s": None,
                "neden": f"{SEARCH_PROGRESS_FILE} yok — arama başlamamış (bayrak arama başında yazılır)"}
    if not isinstance(ham, dict):
        return {"durum": "olculemedi", "kayit": {}, "yas_s": None,
                "neden": f"{SEARCH_PROGRESS_FILE} sözlük değil: {type(ham).__name__}"}
    if not ham:
        # BOŞ SÖZLÜK = temizlenmiş bayrak (`_progress_temizle`) — bu ÖLÇÜLDÜ, arama yok demektir.
        return {"durum": "yok", "kayit": {}, "yas_s": None, "neden": None}
    dmg = ham.get("updated_at")
    if dmg:
        try:
            yas = max(0.0, (_dt.datetime.now(_dt.timezone.utc)
                            - _dt.datetime.fromisoformat(dmg)).total_seconds())
        except (TypeError, ValueError):  # sessiz-yutma: bozuk damga YUTULMUYOR, "olculemedi" olarak ÇAĞIRANA DÖNÜYOR ve neden alanında ham değer taşınıyor — çağıran muhafazakâr tarafa düşer
            return {"durum": "olculemedi", "kayit": ham, "yas_s": None,
                    "neden": f"updated_at çözümlenemedi: {dmg!r}"}
    else:
        # DAMGASIZ KAYIT "ÖLÇÜLEMEDİ" DEĞİLDİR (2026-08-17, suite 12 kırmızıyla düzeltti).
        # İlk hâlde damgasız bir `running=True`yu "ölçülemedi" sayıyordum; yanlıştı. `olculemedi`
        # BİLGİ YOKLUĞU içindir (dosya yok/bozuk), bilgi EKSİKLİĞİ için değil: `running` alanı
        # başlı başına bir olgudur. Üstelik asıl tüketici (`sprint._arama_durumu`) damgayı HİÇ
        # kullanmıyor — yaşı kendi parmak-izi saatiyle (`_ARAMA_GOZLEM`) ölçüyor ve `_progress`
        # docstring'i damganın parmak izine BİLEREK girmediğini yazıyor. Tüketicinin istemediği
        # bir şartı dayatmıştım; `yas_s` None döner, `durum` yine ölçülür.
        yas = None
    return {"durum": "kosuyor" if ham.get("running") else "yok",
            "kayit": ham, "yas_s": yas, "neden": None}

HYP_SCHEMA = {
    "type": "object",
    "properties": {
        # `variable@regime` AÇIKÇA YAZILIR: açıklama "exactly one key from bounds.yaml"
        # diyordu ama bağlamdaki `note_regime_conditional` rejim-koşullu biçimi ÖNERİYORDU — model
        # iki çelişen talimat görüyordu ve rejim düğmesini kullanmaktan kaçınıyordu. Şema hâlâ TEK
        # değişken ister; `@regime` soneki o değişkenin yalnız bir rejimdeki değerini hedefler.
        # K1 DURAKLATMA (EDG-2026-048 NO-GO, 2026-08-23): örnek '@chop'tan '@trend_down'a çevrildi
        # ve duraklatma şemaya YAZILDI — şema teşviki, @chop üretiminin üç yüzeyinden biriydi.
        # Kod tarafı fail-closed: model yine de '@chop' üretirse `_reflect_once_govde` düşürür
        # (config.URETIMI_DURAKLATILAN_REJIMLER). Canlanma yalnız yeni kartla.
        "variable": {"type": "string",
                     "description": "exactly one key from bounds.yaml; optionally suffixed '@regime' "
                                    "to tune that key for ONE regime only (e.g. 'exit.trail_atr_mult@trend_down'). "
                                    "Still counts as one variable. '@chop' is PAUSED "
                                    "(EDG-2026-048 NO-GO) — never propose an '@chop' variable."},
        "new": {"type": "number", "description": "proposed value, on-step and in-range"},
        "rationale": {"type": "string"},
        "predicted_direction": {"type": "string", "enum": ["improve_oos_score", "worsen_oos_score"]},
        "predicted_delta": {"type": "number", "description": "expected OOS score change, e.g. 0.03"},
        "confidence": {"type": "number", "description": "0..1"},
        # Tanımsız kalınca modeller buraya sektör/kurulum adı yazıyordu; alan `guard`/analytics
        # tarafından tüketiliyor ve serbest metin sessizce "bilinmeyen rejim" oluyordu.
        "regime": {"type": "string",
                   "description": "the regime this hypothesis targets: one of "
                                  + "/".join(config.VALID_REGIMES) + ", or 'all' when it is universal"},
        "skill_recommendation": {
            "type": ["object", "null"],
            "description": "OPTIONAL Axis-2 note: recommend shadowing an underperforming skill or leaning "
                           "on a strong one, from skill_library performance. Advisory (operator applies).",
            "properties": {
                "skill": {"type": "string", "description": "a name from skill_library (never a protected one)"},
                # 2026-08-13: enum ARTIK TÜRETİLİR. Elle yazılı üçlü, `skills` tarafındaki
                # uygulayıcı kümesiyle sessizce ayrışmıştı ve "Uygula" düğmesi bu ayrışmadan
                # ölüyordu. Sıra korunur (çivi): tuple sıralı, `list()` onu bozmaz.
                "action": {"type": "string", "enum": list(_skills.ONERILEBILIR_EYLEMLER)},
                "rationale": {"type": "string"},
            },
            "required": ["skill", "action", "rationale"],
            "additionalProperties": False,
        },
    },
    "required": ["variable", "new", "rationale", "predicted_direction", "predicted_delta", "confidence", "regime"],
    "additionalProperties": False,
}

SYSTEM = """You are Hermes, the research brain of Meridian, a paper-trading agent. You do NOT trade
and you do NOT edit files. You propose ONE change to ONE strategy parameter, and the engine decides
— through an out-of-sample backtest gate — whether it ships. A rejection is a result, not a failure.

Hard rules (also enforced in code — you cannot bypass them):
- Change EXACTLY ONE variable, and only a key that exists in bounds.yaml.
- The new value must be inside the variable's [min,max] and land on its step.
- Never touch goal.yaml, the limits block, or autonomy_level. Those are immutable to you.
- Read lessons.md FIRST. Never re-propose a value lessons.md marks as a failed dead end.
- State a falsifiable prediction (predicted_direction + predicted_delta) and a calibrated confidence.
- Score by regime, not as one blur. An edge that only exists in one regime is a real finding.
- '@chop' targets are PAUSED (card EDG-2026-048 measured opening the chop slice as harmful,
  NO-GO): never propose an '@chop' variable. Existing @chop records and their grading are
  untouched; the pause lifts only with a new pre-registered card.

You improve the system along TWO axes:
  Axis-1 (primary, THIS output): tune ONE strategy parameter — auto-validated by the backtest gate.
  Axis-2 (optional): the context gives you `skill_library` — your full 67-skill toolkit, each with its
  live contribution (avg_r over n trades). Use it. A skill with a chronically NEGATIVE avg_r over a real
  sample is dragging the book; a strongly POSITIVE one is where the edge lives. If you see a clear case,
  add a `skill_recommendation` (shadow the loser, or lean on the winner). This is ADVISORY — the operator
  applies it — because the deterministic backtest does not execute the LLM skills, so it cannot gate them.
  Never recommend a protected skill (skill_library marks them). Omit the recommendation if nothing is clear.
  SAMPLE FLOOR IS NOT OPTIONAL: `skill_library.sample_gate` carries the exact thresholds. A skill below
  the floor has NOISE, not performance — do not call it "strong", "chronic" or "clear". If you write a
  recommendation anyway, put the raw n and n_cf in the rationale and say the sample is below the floor.
  Your rationale is stored next to the MEASURED n; a claim the numbers do not support is visible.

Grounding rules:
- Cite in `rationale` WHICH evidence item motivates the change (by its key name in the context or the
  evidence pack). A rationale that cites nothing is a guess wearing the clothes of an argument.
- If no evidence supports any change, pick the lowest-risk exploratory step and SAY so in `rationale`,
  with a LOW confidence. An honest "I am exploring" is worth more than a confident story.
- Do not re-propose a (variable, value) pair that appears as rejected in recent_hypotheses. The gate
  already answered that question; repeating it spends a walk-forward to learn nothing.
Return only the structured hypothesis (with an optional skill_recommendation)."""


LESSONS_CAP = 4000       # prompt'a giren lessons.md tavanı (karakter) — aşımı BEYAN edilir
TRADES_IN_CONTEXT = 15   # 25'ten indirildi: en yeni işlemler sinyal, kuyruk token
SKILL_DOES_CAP = 80      # ölçülü skill açıklaması bu uzunluğa kırpılır


def _gate_anchor() -> dict:
    """ÖLÇEK ÇIPASI: `predicted_delta` hangi ölçekte okunur ve kapı fiilen NE ister?

    Model her turda bir sayı tahmin ediyordu ama o sayının BÜYÜK mü küçük mü olduğunu bilmiyordu:
    kapının marjı (0.02) prompt'ta hiç yoktu. Çıpasız bir tahmin kalibre edilemez — ve kalibrasyon
    bu sistemin öğrenme iddiasının tam merkezinde.

    Değerler KAYNAKTAN okunur (reflect'in sabitleri + karne), burada YENİDEN YAZILMAZ: ikinci bir
    kopya kapı eşiği değiştiğinde sessizce yalan söylerdi."""
    sb = store.read_json("scoreboard.json", {}) or {}
    cur = sb.get("current_version")
    row = ((sb.get("versions") or {}).get(str(cur)) or {}) if cur is not None else {}
    return {
        "incumbent_version": cur,
        # None = bu sürüm için OOS ÖLÇÜLMEDİ (ör. operatör tabanı). Uydurulmaz; kapı zaten her
        # yansımada incumbent'ı yeniden walk-forward'la ölçer (reflect.run_reflection).
        "incumbent_published_oos": row.get("backtest_oos"),
        "gate_margin": reflect.GATE_MARGIN,
        "tail_margin_r": reflect.TAIL_MARGIN_R,
        "rule": (f"legacy_margin law: candidate OOS must exceed incumbent OOS + {reflect.GATE_MARGIN}. "
                 f"probabilistic law (when the walk-forward yields a search slice): P(delta_S>0) must "
                 f"clear the required threshold, which RISES with the number of candidates tried that "
                 f"session (winner's-curse penalty). BOTH laws additionally require: a majority of "
                 f"walk-forward folds won (at least 2 folds must carry evidence), and OOS tail risk "
                 f"(VaR and CVaR) must not worsen by more than {reflect.TAIL_MARGIN_R}R. Incumbent and "
                 f"candidate OOS must both be measurable (>= goal.min_sample)."),
        "note": (f"Read predicted_delta on THIS scale: a change that does not clear about "
                 f"{reflect.GATE_MARGIN} of OOS score cannot ship under the margin law. Predicting a "
                 f"delta far above that without evidence is not ambition, it is miscalibration."),
    }


def _compact_hypotheses(rows: list) -> list:
    """Geçmiş hipotezlerin KARAR alanları — `backtest` yükü (fold/kuyruk dökümü, satır başına ~1.4k
    karakter) prompt'a girmez.

    SYSTEM artık "reddedilmiş (variable,value) çiftini tekrar önerme" diyor; o kuralın uygulanabilmesi
    için çiftin GÖRÜNÜR olması gerekir. 2.2k karakterlik bir satırda çift, walk-forward dökümünün
    içinde kayboluyordu — kural yazılıydı ama okunabilir değildi."""
    out = []
    for h in rows:
        out.append({k: h.get(k) for k in
                    ("id", "variable", "old", "new", "regime", "status", "reject_reasons",
                     "predicted_delta", "confidence", "source", "ts")})
    return out


def build_context() -> str:
    """Beynin göreceği TÜM bağlamı tek JSON metnine toplar: hedef, sınırlar, güncel strateji,
    dersler, son işlemler, skor tablosu, rejim penceresi, son hipotezler, kapı çıpası, ajanın kendi
    kalibrasyonu, skill atıfları ve kütüphanesi.

    SESSİZ KIRPMA YOK: dersler `LESSONS_CAP`ı aşarsa kırpılır ama kırpıldığı metinde SÖYLENİR —
    model okumadığı bir şeyi okuduğunu sanmasın."""
    goal = config.goal()
    bounds = config.bounds()
    strat = config.load_strategy()
    lessons = (config.STATE / "lessons.md")
    lessons_txt = lessons.read_text() if lessons.exists() else "(none yet)"
    # SESSİZ KIRPMA YOK: tavanı aşan dersler kırpılır ama kırpıldığı SÖYLENİR. Sessizce kısaltılmış
    # bir "Read lessons.md FIRST" talimatı, modele okumadığı bir şeyi okuduğunu sandırırdı.
    if len(lessons_txt) > LESSONS_CAP:
        lessons_txt = (f"[... KIRPILDI: yalnız son {LESSONS_CAP} karakter gösteriliyor "
                       f"(tam metin {len(lessons_txt)} karakter) ...]\n" + lessons_txt[-LESSONS_CAP:])
    trades = store.read_jsonl("trades.jsonl", limit=TRADES_IN_CONTEXT)
    scoreboard = store.read_json("scoreboard.json", {})
    regime = store.read_json("regime.json", {})
    hyps = memory.all_hypotheses()[-8:]
    from . import analytics
    calib = analytics.calibration()
    # Phase 3.2 — regime context: WHICH markets produced the recent realized deltas, so Hermes knows a param
    # that only helped in one regime is a regime-specific finding, not a universal improvement (anti-overfit).
    regimes_recent = {}
    for t in trades:
        r = t.get("regime")
        if r:
            regimes_recent[r] = regimes_recent.get(r, 0) + 1
    regime_window = {"current": regime.get("regime"), "recent_trade_regimes": regimes_recent,
                     "distinct_regimes": len(regimes_recent),
                     "note": "The realized deltas below came from THESE regimes. If your recent trades sit in "
                             "one regime, do not overfit a structurally-sound parameter to that single market."}
    return json.dumps({
        "goal": goal, "bounds": bounds, "current_strategy": strat,
        "lessons_md": lessons_txt, "recent_trades": trades,
        "scoreboard": scoreboard, "regime": regime, "regime_window": regime_window,
        "recent_hypotheses": _compact_hypotheses(hyps),
        "gate_anchor": _gate_anchor(),                       # predicted_delta'nın ölçeği + kapının kuralı
        "your_calibration": calib,  # Brier + hit-rate of your own past confidence — stay honest with yourself
        "skill_attribution": analytics.skill_attribution(),  # per-skill avg_r/win_rate (Axis-2 evolve signal)
        "vs_benchmark": analytics.benchmark_relative(),      # are you beating SPY, or just riding beta?
        "skill_library": _skill_library(),                   # your full toolkit + how each skill performs
        # K1 DURAKLATMA (EDG-2026-048): reklam edilen rejim listesi duraklatılanları TAŞIMAZ —
        # bağlam istemi de bir üretim teşvikidir (şema örneğiyle aynı sınıf, aynı gerekçe).
        "note_regime_conditional": "You may tune one knob for one regime with 'variable@regime' "
                                    f"(regimes: {', '.join(r for r in config.VALID_REGIMES if r not in config.URETIMI_DURAKLATILAN_REJIMLER)}"
                                    "; '@chop' is PAUSED, EDG-2026-048); it stays one_variable_only.",
    }, indent=2)


def _skill_library() -> dict:
    """Axis-2 için skill kütüphanesi — ÖLÇÜLENLER tam, ölçülmeyenler yalnız adıyla.

    Axis-2 önerisi (shadow/lean_in) tanımı gereği ÖLÇÜME dayanmak zorundadır: SYSTEM "chronically
    NEGATIVE avg_r over a real sample" der. Yani `n == 0` olan bir skill'in açıklaması karar girdisi
    DEĞİLDİR — 63 ölçülmemiş skill'in tarifleri prompt'un en büyük tek bloğuydu (18k karakter) ve
    tek bir kararı bile besleyemiyordu. Ölçülenler + korumalılar tam satır kalır (korumalılar
    kalır ki model yanlışlıkla onları önermesin ve "listede yoktu" diyemesin); geri kalanı
    `unmeasured` ad listesine iner — toolkit'in TAMAMI hâlâ görünür, yalnız tarifsiz."""
    from . import skills
    olculu, olcusuz = [], []
    for s in skills.catalog():
        n = s.get("n") or 0
        if n >= 1 or s.get("protected"):
            does = str(s.get("description") or "")
            if len(does) > SKILL_DOES_CAP:
                does = does[:SKILL_DOES_CAP - 1] + "…"
            # cf KATMANI DA GÖRÜNÜR (2026-08-13). Ölçülen arıza: model `n=1`lik bir skill için
            # "Strong live performance of 0.918 avg_r" yazdı — çünkü gördüğü SATIRDA örneklemin
            # yeterli olup olmadığını söyleyen HİÇBİR ŞEY yoktu ve karşı-olgusal katman (bu skill'de
            # n_cf=12, cf ort 0,328) prompt'a hiç girmiyordu. `skills.catalog()` iki alanı ZATEN
            # üretiyor; burada düşürmek, modeli tek işlemlik bir kanıtla baş başa bırakmaktı.
            olculu.append({"name": s["name"], "does": does, "on": s["enabled"],
                           "avg_r": s["avg_r"], "n": s["n"],
                           "n_cf": s.get("n_cf") or 0, "cf_avg_r": s.get("cf_avg_r"),
                           "needs": s["requires"],
                           "protected": s["protected"], "shadow": s["shadow"]})
        else:
            olcusuz.append(s["name"])
    # EŞİK PROMPT'TA YAZILI VE KAYNAKTAN OKUNUR. Sayıyı burada elle yazmak, `skills.MIN_N`
    # değiştiği gün modele eski eşiği anlatmak olurdu (bu dosyanın `_gate_anchor` dersi birebir aynı).
    esik = {"min_n": skills.MIN_N,
            "cf_arm": {"real_min": skills.MIN_N * skills.CF_REAL_FRACTION,
                       "cf_min": skills.MIN_N * skills.CF_SAMPLE_MULT}}
    return {"measured_or_protected": olculu,
            "unmeasured": olcusuz,
            "sample_gate": esik,
            "note": "unmeasured skills have n=0 live trades: no evidence exists to shadow or lean on "
                    "them, so only their names are listed. Axis-2 recommendations must cite avg_r/n. "
                    f"SAMPLE FLOOR (`sample_gate`): a skill clears it only with n >= {esik['min_n']} "
                    f"real trades, OR n >= {esik['cf_arm']['real_min']:g} real AND n_cf >= "
                    f"{esik['cf_arm']['cf_min']:g} counterfactual rows. Below the floor the avg_r is "
                    "NOISE, not performance: never call it 'strong' or 'chronic'. You may still note "
                    "it, but you must write the raw n and n_cf in the rationale and say the sample is "
                    "below the floor — the operator's ledger stamps the measured n either way."}


def _claude_text(user: str, *, note: str, schema: dict | None = None,
                 max_tokens: int = 4000) -> str | None:
    """Claude çağrısının TEK GÖVDESİ — METİN döner, ayrıştırma çağıranın işi.

    NEDEN AYRIŞTIRILDI (nous sistem-değerlendirme katmanı): Katman B beyin zincirini
    hipotez ÜRETMEK için değil MEKANİZMA DEĞERLENDİRMESİ için çağırıyor — aynı taşıma, farklı görev.
    İkinci bir HTTP gövdesi yazmak, `spend.record` muhasebesinin, `cache_control` sözleşmesinin ve
    boş-cevap sınıflandırmasının İKİ KOPYAYA çıkması demekti; bu dosyanın tarihi tam olarak "iki
    kopya sessizce ayrışır" hatalarıyla dolu (bkz. `_user_prompt`in tek-talimat-kaynağı notu).
    Sözleşme: SYSTEM statik ve önbelleklenmiş kalır, GÖREV user-prompt yolundan girer."""
    try:
        import anthropic
    except ImportError:
        print("[hermes] anthropic SDK not installed; falling back to deterministic proposer")
        _trace_note(EMPTY_NO_CALL, detail="anthropic SDK yok")
        return None
    from . import secrets
    api_key = secrets.get("HERMES_API_KEY") or secrets.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("[hermes] no HERMES_API_KEY; falling back to deterministic proposer")
        _trace_note(EMPTY_NO_CALL, detail="anahtar yok")
        return None
    from . import spend
    if spend.over_budget():
        s = spend.summary()
        print(f"[hermes] monthly budget spent (${s['spent_usd']}/${s['budget_usd']}); "
              f"falling back to the free deterministic proposer")
        _trace_note(EMPTY_NO_CALL, detail="aylık bütçe dolu")
        return None
    client = anthropic.Anthropic(api_key=api_key)
    _fmt = ({"type": "json_schema", "schema": schema} if schema else {"type": "text"})
    # SÜRE ÖLÇÜMÜ (`tasiyici="http"`): zincirin bu bacağında alt süreç YOKTUR, yani
    # `-Q`/araç sayısı gibi olgular da yoktur (`arac_cagri_n=None` = ÖLÇÜLEMEDİ). Ölçülen tek şey
    # duvar süresidir ve o da "gece koşusu neden 40 dk sürdü" sorusunun bu bacaktaki payıdır.
    _kr = _at.Kronometre()
    try:
        resp = client.messages.create(
            model=MODEL, max_tokens=max_tokens,
            thinking={"type": "adaptive"},
            output_config={"effort": "high", "format": _fmt},
            # cache the fully-static system prompt (two-axis briefing) so it isn't billed at full input price
            # every reflection — the standby loop fires far more often than the 5-min cache TTL.
            system=[{"type": "text", "text": SYSTEM, "cache_control": {"type": "ephemeral"}}],
            messages=[{"role": "user", "content": user}],
        )
    except BaseException as e:
        # İSTİSNA DA BİR SONUÇTUR: 429/529/ağ kopması bugün yalnız `_rate_limited` sınıflamasına
        # gidiyor ve SÜRESİ hiçbir yerde yazmıyordu. Satır yazılır, istisna AYNEN yukarı gider.
        _at.kaydet(kind=note, model=MODEL, deneme=1, alt=0, sure_ms=_kr.dur(),
                   sonuc_sinifi=_at.SINIF_BOS, tasiyici=_at.TASIYICI_HTTP, arac_cagri_n=None,
                   istem=user, stderr=f"{type(e).__name__}: {e}", istisna=type(e).__name__)
        raise
    _kr.dur()
    try:                                             # meter the call — cost is only known after it returns
        u = getattr(resp, "usage", None)
        if u is not None:
            cache_read = getattr(u, "cache_read_input_tokens", 0) or 0
            spend.record(getattr(u, "input_tokens", 0), getattr(u, "output_tokens", 0), MODEL,
                         note=f"{note} (cache_read={cache_read})")
    except Exception:  # sessiz-yutma: yardımcı/telemetri yolu; başarısızlığı karara girmez ve çağıran yedek değerle aynen devam eder
        pass
    text = next((b.text for b in resp.content if b.type == "text"), None)
    _at.kaydet(kind=note, model=MODEL, deneme=1, alt=0, sure_ms=_kr.ms,
               sonuc_sinifi=(_at.SINIF_DOLU if text else _at.SINIF_BOS),
               tasiyici=_at.TASIYICI_HTTP, arac_cagri_n=None, istem=user, stdout=text,
               stop_reason=str(getattr(resp, "stop_reason", "") or "") or None)
    if not text:
        # 200 döndü ama metin bloğu yok: yalnız araç/düşünme bloğu ya da durdurma sebebi. "Başarılı"
        # sayılıp sessizce None dönmek, tam da kalibrasyonun neden hiç çift biriktirmediğinin cevabıydı.
        blocks = ",".join(sorted({getattr(b, "type", "?") for b in (resp.content or [])})) or "yok"
        _trace_note(EMPTY_TOOL_ONLY if "tool_use" in blocks else EMPTY_NO_TEXT,
                    detail=f"bloklar={blocks} stop={getattr(resp, 'stop_reason', '?')}")
        return None
    return text


def propose_with_claude() -> dict | None:
    """Claude kolundan TEK tek-değişkenli hipotez ister; metin boşsa ya da şema ayrıştırması
    düşerse None döner (uydurma yok — zincir bir sonraki sağlayıcıya düşer).

    Talimat TEK KAYNAKTAN (`_user_prompt`) gelir; şema API'de zorlanır (with_schema=True)."""
    # TEK TALİMAT KAYNAĞI: burada inline bir kopya vardı ve `_user_prompt` ile
    # ayrışabiliyordu — üstelik bu yol `evidence_pack()`i HİÇ eklemiyordu, yani en pahalı beyin
    # ölçülmüş kalibrasyonları görmeden öneri üretiyordu. Şema API'de zorlandığı için sözleşme
    # metni tekrarlanmaz (with_schema=True).
    text = _claude_text(_user_prompt(with_schema=True), note="reflect", schema=HYP_SCHEMA)
    if not text:
        return None
    hyp = _parse_hyp(text)
    if hyp is None:
        return None
    hyp["source"] = "hermes"
    return hyp


# ================= ÇOK-SAĞLAYICILI BEYİN (Nous Hermes · Gemini · Claude · deterministik) =================
# Operatör isteği: beyin Nous hermes-agent'a ve OAuth'lu Gemini'a bağlanabilsin. MİMARİ YASA
# DEĞİŞMEZ: hangi LLM konuşursa konuşsun yalnızca ÖNERİR — tek değişken, OOS walk-forward kapısı, ufuk
# koruması ve rollback aynen kalır. "Sürekli kendini güncelleyen döngü" bu kapılı yansıma döngüsüdür;
# beyin takılabilir, yasa takılabilir değil. Zincir: HERMES_BRAIN_ORDER sırasıyla anahtarı hazır olan ilk
# sağlayıcı; hata/boş cevapta zincir bir sonrakine düşer; hiçbiri yoksa ücretsiz deterministik önerici.
NOUS_DEFAULT_ENDPOINT = "https://inference.nousresearch.com/v1"
NOUS_DEFAULT_MODEL = "Hermes-4-405B"
# SABİT ALIAS (canlı 404 vakası): anahtar SAĞLAMKEN (models-list HTTP 200) üretim
# çağrısı 404 veriyordu — canlı ajan config'indeki `gemini-3.5-flash` Google listesinden KALKMIŞTI
# ve buradaki eski çıplak ad (`gemini-3.1-pro`) o listede HİÇ yoktu (yalnız `-preview` türevi).
# Google sürüm adlarını döndürüyor (resmî örnekler 3.6-flash'a geçti); çıplak sürüm adına
# çivilenmek aynı 404 sınıfını yeniden üretir. Operatör tercihi ("gemini 3.1 pro
# olmalı") ALIAS ÜZERİNDEN KORUNUR: `gemini-pro-latest` bu yazım anında `gemini-3.1-pro-preview`ı
# gösteriyor ve Google modeli yeniledikçe alias'la birlikte taşınır. Pano metni K1 gereği bu
# sabitten türetilir (api.api_secrets → model_defaults), elle senkron gerekmez.
GEMINI_DEFAULT_MODEL = "gemini-pro-latest"
# BİLİNEN-ÖLÜ AD GÖÇÜ HARİTASI: yerel hermes-agent config'inde (model.default) DURAN
# ölü bir ad kendi kendine iyileşmez — `config_ensure_integrations` bu haritayla sabit alias'a
# çevirir ve OLAYLAR (`gemini_dead_model_migrated`; sessiz değiştirme YASAK). Harita YALNIZ
# bilinen-ölü adları taşır; TANINMAYAN adlar SERBEST GEÇER (elimizdeki model listesi kesitti ve
# gelecekteki geçerli adlar — ör. gemini-3.6-flash — kırılmamalı). Rol eşleşmesi korunur:
# hızlı-görev (flash) → flash alias'ı, pro → pro alias'ı.
GEMINI_DEAD_MODEL_MAP = {
    "gemini-3.5-flash": "gemini-flash-latest",   # canlı config'teki ölü ad (üretim 404)
    "gemini-3.1-pro": "gemini-pro-latest",       # eski repo varsayılanı — listede yalnız -preview var
}

# ==================================================================================================
# GÖÇ TEK YOLU KAPATIYORDU — ÇAĞRI ANI AÇIKTA KALDI (2026-08-13, canlı ölçüm)
# --------------------------------------------------------------------------------------------------
# ÖLÇÜLEN ARIZA: `GEMINI_DEFAULT_MODEL` DOĞRU (`gemini-pro-latest`), göç de doğru çalışıyor —
# ama canlıda BUGÜNKÜ 20 `agent_call` olayının hepsi `model="gemini-3.5-flash"` taşıyor. Sebep
# izlendi: `_agent_call` model zincirini `GEMINI_DEFAULT_MODEL`den DEĞİL, SIRLARDAN kuruyor
# (`NOUS_MODEL` → `NOUS_FALLBACK_MODEL`, aşağıda `_nous_model_zinciri`) ve seçilen ad CLI'ya
# `--model` ile geçiliyor (`_agent_chat_cmd`). Göç YALNIZ `~/.hermes/config.yaml`ın
# `model.default` alanını onarıyordu (`config_ensure_integrations`) — sır tarafına HİÇ bakmıyordu.
# Yani "ölü ad kendi kendine iyileşmez" dersi bir yolda öğrenilmiş, ikizi açık bırakılmıştı.
#
# İKİ KATMANLI ONARIM:
#   (1) YAPILANDIRMA ANI  — `config_ensure_integrations` (DURUYOR): config'teki ölü adı göçürür.
#   (2) ÇAĞRI ANI (BU TUR) — `_nous_model_zinciri`: sırdan gelen ad ölüyse alias'a ÇEVRİLİR ve olay
#       basılır. Bu katman zorunludur çünkü sır dosyası bizim yeniden yazacağımız bir yüzey DEĞİL
#       (operatörün `.env`i; sırra yazmak sır-yazma yasağına girer) ve config göçü onu kapsamaz.
# Sessiz değiştirme YASAK: her göç `agent_model_olu_ad_gocuruldu` satırı yazar (süreç başına ad
# başına BİR kez — çağrı ~5 dakikada bir koşuyor, her turda warn basmak alarmı gürültüye çevirirdi).
#
# TANINMAYAN AD SERBEST GEÇER: elimizdeki liste bir KESİTTİR; gelecekteki geçerli bir adı (ör.
# `gemini-3.6-flash`) "ölü" damgalamak, onarım kılığında bir arıza olurdu.
#
# --------------------------------------------------------------------------------------------------
# OLAY YAYINI ÇEVİRİYE DEĞİL ÇAĞRIYA BAĞLIDIR (2026-08-13 düzeltmesi, otoriter suite bulgusu)
# --------------------------------------------------------------------------------------------------
# ÖLÇÜLEN KUSUR: ilk hâlde `canonical_model` HER çağrı yerinde olay basıyordu — RAPORLAMA yüzeyleri
# dahil. `hermes_runtime.status()` (yani `/api/hermes`) `active_model()` + `_model_id()` üzerinden
# iki `obs.warn` doğuruyordu; `tests/test_api_contract.py::test_hermes_status_..._mid_search`
# teardown'unda CANLI `state/events.jsonl`e iki satır DÜŞTÜ ("CANLI state'e YAZILDI"). Aynı sınıf
# Ajanın kendi raporunda da beyan edilmişti ("sandbox'sız smoke sondasının yan etkisi").
# KUSUR TEST DEĞİL YAYIN YERİYDİ: bir pano isteği, bir import ya da bir bağlantı sondası
# operatörün defterine "göç oldu" satırı YAZAMAZ — o defter üretim kanıtıdır ve panonun okuma
# yapması bir üretim olayı değildir.
# AYRIM: ÇEVİRİ her yerde olur (rapor edilen kimlik ile çağrılan kimlik ayrışmamalı — test_3b),
# ama OLAY yalnız modelin GERÇEKTEN çağrıldığı iki yerde basılır: `_nous_model_zinciri`
# (→ `_agent_call`) ve `_gemini_call`. Bayrak `olay=False` ile VARSAYILAN SESSİZDİR: ileride
# eklenecek yeni bir okuma yüzeyi, unutulduğunda defter yazmak yerine susar (güvenli taraf).
# Sessiz-değiştirme yasağı KORUNUR — üretim yolu ~5 dakikada bir koşuyor, göç ilk gerçek çağrıda
# zaten deftere düşüyor; tekilleştirme kümesi de yalnız olay basıldığında işaretlenir (sessiz
# geçiş kümeyi kirletirse gerçek çağrının olayı yutulurdu).
# ==================================================================================================
_OLU_MODEL_OLAYLI: set = set()


def canonical_model(ad: str | None, *, kaynak: str = "?", olay: bool = False) -> str | None:
    """Bilinen-ölü model adını sabit alias'a çevirir; tanınmayan/boş ad AYNEN geçer.

    `kaynak` yalnız olay satırı içindir (hangi yüzeydeki ad göçtü) — davranışa girmez.
    `olay=True` YALNIZ gerçek çağrı yolundan verilir (bkz. üstteki "olay yayını" notu): çeviri her
    yerde aynı, defter yazımı yalnız modele gerçekten gidildiğinde."""
    if not ad:
        return ad
    yeni = GEMINI_DEAD_MODEL_MAP.get(str(ad).strip())
    if not yeni:
        return ad
    anahtar = (kaynak, str(ad).strip())
    if olay and anahtar not in _OLU_MODEL_OLAYLI:
        _OLU_MODEL_OLAYLI.add(anahtar)
        obs.warn("agent_model_olu_ad_gocuruldu", kaynak=kaynak, eski=str(ad).strip(), yeni=yeni,
                 detail="çağrı anında BİLİNEN-ÖLÜ model adı görüldü (üretim 404 sınıfı) ve sabit "
                        "alias'a çevrildi; rol korundu (flash→flash-latest, pro→pro-latest). "
                        "KALICI ONARIM OPERATÖRDE: sır dosyasındaki adı güncelle — bu katman "
                        "her çağrıda yeniden çevirir ama sırra YAZMAZ (sır-yazma yasağı).")
    return yeni


def gemini_model(*, olay: bool = False) -> str:
    """Gemini çağrılarının TEK model kaynağı: sır override'ı → repo varsayılanı → ölü-ad göçü.

    Bu ifade (`secrets.get("GEMINI_MODEL") or GEMINI_DEFAULT_MODEL`) dört yerde elle kopyalanmıştı
    (üretim çağrısı, bağlantı sondası, yerel ajan geçişi, `_model_id`) — yani ölü-ad kontrolünü
    dört ayrı yere yazmak ya da bir yerini unutmak gerekiyordu. Tek kapı, bu turun kapattığı
    kusurun (aynı gerçeğin ikinci evi) burada tekrarlanmasını önler.

    `olay=True` yalnız `_gemini_call`den gelir — sonda/rapor/config yüzeyleri sessiz okur."""
    return canonical_model(secrets.get("GEMINI_MODEL") or GEMINI_DEFAULT_MODEL,
                           kaynak="GEMINI_MODEL", olay=olay)


def _nous_model_zinciri() -> list:
    """`_agent_call`in model düşüş zinciri — ÇAĞRI ANINDA ölü-ad kontrolünden geçirilmiş hâli.

    Tekilleştirme GÖÇTEN SONRA yapılır: iki sır aynı alias'a göçerse zincir tek elemana iner ve bu
    DOĞRUDUR (aynı modeli iki kez denemek "yedeklilik" değildir; canlıda tam bu yanılsama ölçüldü —
    `brain_chain_facts` docstring'i). Hiç ad yoksa `[None]` = "CLI kendi varsayılanını kullansın".

    Bu fonksiyon GERÇEK ÇAĞRI yoludur (`_agent_call`) — göç olayını basan iki yerden biri."""
    ham = [canonical_model(secrets.get("NOUS_MODEL"), kaynak="NOUS_MODEL", olay=True),
           canonical_model(secrets.get("NOUS_FALLBACK_MODEL"), kaynak="NOUS_FALLBACK_MODEL",
                           olay=True)]
    return [m for m in dict.fromkeys(ham) if m] or [None]


DEFAULT_BRAIN_ORDER = "claude,nous,gemini"

# DÜŞÜNCE BÜTÇESİ: gemini-3.x DÜŞÜNEN bir ailedir ve düşünce tokenları ÜRETİM tavanından
# yenir. Eski istek `maxOutputTokens: 4000` gönderiyordu, düşünce ayarı YOKTU; canlı ölçüm
# (gemini-3.5-flash, aynı yansıma prompt'u) şunu verdi:
#     thoughtsTokenCount=3838 + candidatesTokenCount=144 ≈ 4000 · finishReason=MAX_TOKENS
# yani cevap JSON'un rationale alanının ORTASINDA kesiliyordu → _parse_hyp None → defterde
# "unparseable" (YANLIŞ sınıf: biçim değil, BÜTÇE arızası). Aynı prompt'la yapılan canlı doğrulama:
#     {"thinkingConfig": {"thinkingBudget": 0}, "maxOutputTokens": 8000}
#       → HTTP 200 · finishReason=STOP · thoughtsTokenCount alanı HİÇ YOK (düşünce kapandı)
#       → candidatesTokenCount=256 · _parse_hyp sözlük döndü.
# thinkingBudget=0 API tarafından kabul edildi, 3.x varyantını (thinkingLevel) denemeye gerek kalmadı.
# maxOutputTokens 8000 EMNİYET PAYIDIR: düşünce ileride tekrar açılırsa/kapanmazsa cevap yine sığar.
GEMINI_THINKING_BUDGET = int(os.environ.get("HERMES_GEMINI_THINKING_BUDGET", "0"))
GEMINI_MAX_OUTPUT_TOKENS = int(os.environ.get("HERMES_GEMINI_MAX_OUTPUT_TOKENS", "8000"))

# AYNI SINIF, İKİNCİ SAĞLAYICI (2026-08-27): PORTAL (OpenAI-uyumlu) ayağı yukarıdaki düzeltmeyi HİÇ
# ALMADI. `_nous_text` gövdesi `max_tokens: 4000` sabitini gönderiyordu ve nemotron ailesi de DÜŞÜNEN
# bir ailedir — akıl yürütme tokenları CEVAPTAN ÖNCE, aynı üretim tavanından yenir.
# CANLI ÖLÇÜM (A1, state/spend.jsonl): nvidia/nemotron ailesine 13 çağrı, **7'si TAM out_tokens=4000**
# (%54) — 5x super-120b + 1x ultra-550b reflect, 1x super-120b nous_eval; girdi ~23-27k token.
# SAĞLAYICI SONDASI mekanizmayı gösterdi: ultra @ max_tokens=60 → finish_reason=length + içerik
# modelin DÜŞÜNCE ÖN-EKİ (reasoning=62); ultra @ max_tokens=2000 → finish_reason=stop + geçerli JSON.
#
# TAVAN NEREDEN TÜRÜYOR (ve neden 4000'in "biraz üstü" DEĞİL): o 7 satır SAĞDAN SANSÜRLÜDÜR —
# tavanda kesilen bir örnek "ihtiyaç ≥4000" der, ihtiyacın NE OLDUĞUNU söylemez. Gerçek istem
# üzerinde ölçülmüş TEK akıl-yürütme sayısı gemini bacağınınkidir (thoughtsTokenCount=3838, aynı
# yansıma prompt'u, GEMINI_THINKING_BUDGET yorumu). Tavan o ölçümden türer: 3838 × 4 ≈ 15,4k → 16000.
# Fatura yok (iki model de :free; OpenRouter GET /api/v1/key usage=0 all-time), platform tavanı
# istek/dakika ve istek/gün cinsindendir — token cinsinden DEĞİL. Yani marj bedelsizdir.
# GERÇEK İHTİYACI ARTIK OLAY ÖLÇECEK: bu turda eklenen `truncated` sınıfı her kesilmede
# `reasoning=N` yazar, yani bir daha çarpılırsa sayı sansürsüz görünür ve tavan ölçüyle ayarlanır.
NOUS_MAX_TOKENS = int(os.environ.get("HERMES_NOUS_MAX_TOKENS", "16000"))

# AKIL YÜRÜTME KOLU — VARSAYILAN KAPALI, BİLEREK. OpenRouter'ın `reasoning` parametresinin bu uçtaki
# TAM şekli BU DEPODAN DOĞRULANAMADI: openrouter.ai çıkış vekilince kapalı ve burada anahtar yok.
# UYDURMA YASAĞI istek gövdesi için de geçerlidir — doğrulanmamış alan canlıya VARSAYILAN gitmez.
# Boşken alan gövdeye HİÇ konmaz (çivi: test_nous_reasoning_control_is_absent_unless...), yani bu
# turun davranış değişikliği YALNIZ tavan + sınıflandırmadır.
# AÇMADAN ÖNCE SONDA ŞART, ve dikkat: `exclude` bir BÜTÇE ayarı DEĞİLDİR — düşünceyi cevaptan gizler,
# ÜRETİLMESİNİ engellemez, yani tavanı aynen yer. Bütçeyi kurtaran ayar düşünceyi KAPATANdır
# (gemini'de thinkingBudget=0'ın yaptığı). İkisini karıştırmak bu sınıfı ikinci kez doğurur.
NOUS_REASONING_EFFORT = (os.environ.get("HERMES_NOUS_REASONING_EFFORT") or "").strip().lower()

# ============ 429 SOĞUMA DEFTERİ + BOŞ-CEVAP SINIFLANDIRMASI =============
# Canlı defterde 45x hermes_brain_failed vardı ve HEPSİ aynı gemini free-tier 429'uydu — üç gün
# boyunca, her yansıma turunda yeniden. Geri çekilme YOKTU: kotayı yiyen sağlayıcı bir sonraki turda
# hiçbir şey hatırlamadan yeniden aranıyordu. Mevcut iki emniyet de absorbe edemedi:
#   • kimlik havuzu: sağlayıcı başına TEK anahtar var (round_robin tek elemanlı listede kimliktir) ve
#     o anahtarın kendi kaydı zaten `last_status: exhausted / 429` diyor — döndürecek ikinci kimlik yok;
#   • fallback_providers: YEREL ajanın (hermes CLI) config'inde yaşar, yani yalnız _agent_call yolunu
#     korur. _propose_gemini() Meridian'ın KENDİ httpx çağrısıdır — o zincire hiç uğramaz.
# Üstelik zincirin iki ayağı (nous-yerel ve gemini) aynı üst-akış kotasına bakıyordu: yerel ajan
# model.provider=gemini ile kuruluydu. "Yedek sağlayıcı" aslında aynı tükenmiş kimliğin ikinci adıydı.
BRAIN_COOLDOWN_FILE = "brain_cooldown.json"
BRAIN_COOLDOWN_BASE_S = int(os.environ.get("HERMES_BRAIN_COOLDOWN_S", "900"))
BRAIN_COOLDOWN_MAX_S = int(os.environ.get("HERMES_BRAIN_COOLDOWN_MAX_S", "21600"))

# "Boş" TEK bir şey değildi: aşağıdaki beş durum aynı hermes_brain_empty satırına katlanıyordu ve
# üstelik BAŞARISIZ çağrılar da (429 istisnası sonrası hyp=None) aynı satırı bir kez daha yazıyordu.
# Bu yüzden 92 boş ≈ 44 çift-sayım + 48 gerçek sessiz bozunma idi. Ayrım artık olayda görünür.
EMPTY_NO_CALL = "no_call"            # çağrı HİÇ yapılmadı (oran bütçesi/ikili yok/soğuma) — cevap değil
EMPTY_NO_TEXT = "no_text"            # taşıma 200, gövdede metin yok
EMPTY_REFUSAL = "refusal"            # model reddetti / güvenlik bloğu (finishReason/blockReason)
EMPTY_TOOL_ONLY = "tool_call_only"   # yalnız araç çağrısı döndü, içerik parçası yok
EMPTY_UNPARSEABLE = "unparseable"    # metin var, JSON değil
EMPTY_SCHEMA = "schema_invalid"      # JSON var, zorunlu alanlar (variable/new) yok
EMPTY_TRUNCATED = "truncated"        # üretim token tavanında kesildi — biçim sorunu DEĞİL, bütçe sorunu
EMPTY_UNKNOWN = "unknown"
# Cevap gelmediği için "boş" sayılamayacak durumlar: bunlar hermes_brain_empty ÜRETMEZ.
_NOT_A_RESPONSE = (EMPTY_NO_CALL,)

_BRAIN_TRACE = threading.local()      # sağlayıcı fonksiyonları imzalarını değiştirmeden neden bildirir


def _trace_note(reason: str, detail: str | None = None) -> None:
    """Sağlayıcı yolu 'boş' dönerken NEDENİNİ bırakır. İş parçacığına özel: arka plan dolgu/inceleme
    iş parçacıkları aynı anda koşar, modül düzeyinde tek kutu birbirinin nedenini ezerdi."""
    _BRAIN_TRACE.reason, _BRAIN_TRACE.detail = reason, detail


def _trace_take() -> tuple[str | None, str | None]:
    """Bu iş parçacığında bırakılmış 'boş cevap' nedenini (sebep, ayrıntı) alır ve kutuyu TEMİZLER —
    aynı neden ikinci bir olaya yapışmasın."""
    r, d = getattr(_BRAIN_TRACE, "reason", None), getattr(_BRAIN_TRACE, "detail", None)
    _BRAIN_TRACE.reason = _BRAIN_TRACE.detail = None
    return r, d


def brain_cooldown(provider: str) -> float:
    """Sağlayıcının sahadan alınmasına kaç saniye kaldı (0 = hazır)."""
    row = (store.read_json(BRAIN_COOLDOWN_FILE, {}) or {}).get(provider) or {}
    try:
        return max(0.0, float(row.get("until") or 0) - time.time())
    except (TypeError, ValueError):  # sessiz-yutma: biçimsiz/eksik tek alan; yalnız bu değer düşer, satır başına uyarı asıl sinyali log seline gömerdi
        return 0.0


def brain_stand_down(provider: str, reason: str, retry_after: float | None = None) -> float:
    """Sağlayıcıyı ÜSTEL (tavanlı) bir süre sahadan al. Sağlayıcının kendi bildirdiği retry_after
    tabandan kısaysa yok sayılır: gemini 'retry in 11.8s' der ama tükenen kota GÜNLÜKTÜR — 12 sn
    sonra dönmek 45 başarısızlığı üreten davranışın ta kendisiydi."""
    def _mut(cur):
        """Soğuma kaydını yerinde günceller: seriyi 1 artırır, üstel (tavanlı) süreyi hesaplar ve
        `until`/`seconds`/`streak`/`reason` alanlarını yazar."""
        row = cur.get(provider) or {}
        streak = int(row.get("streak") or 0) + 1
        secs = min(BRAIN_COOLDOWN_BASE_S * (2 ** (streak - 1)), BRAIN_COOLDOWN_MAX_S)
        if retry_after:
            secs = min(max(secs, float(retry_after)), BRAIN_COOLDOWN_MAX_S)
        cur[provider] = {"until": time.time() + secs, "seconds": secs, "streak": streak,
                         "reason": reason, "since": memory.now_iso()}
        return True
    doc = store.update_json(BRAIN_COOLDOWN_FILE, _mut, default={})
    return float(doc[provider]["seconds"])


def brain_recovered(provider: str) -> None:
    """Sağlayıcı kullanılabilir bir cevap üretti — soğuma ve seri sıfırlanır (yalnız kayıt varsa yazar)."""
    def _mut(cur):
        """Sağlayıcının soğuma kaydını siler; kayıt yoksa False döner (gereksiz yazım olmaz)."""
        return cur.pop(provider, None) is not None
    store.update_json(BRAIN_COOLDOWN_FILE, _mut, default={})


def brain_pause(provider: str, reason: str, seconds: float) -> float:
    """DÜZ (üstel OLMAYAN) kısa dinlenme: seriyi ARTIRMAZ ve var olan daha uzun bir cezayı KISALTMAZ.

    NEDEN `brain_stand_down`DAN AYRI (2026-08-04 canlı vakası): o fonksiyonun ölçtüğü olgu
    "sağlayıcı KOTAM BİTTİ dedi"dir ve cezanın üstel büyümesi oradan meşrudur. Burada ölçülen olgu
    bambaşkadır: hat çalıştı, süreç koştu, model SUSTU. Susan bir modeli aynı üstel merdivene
    bindirmek üç turda hattı 6 saat kilitliyordu — hem de kotası dolmamış BİRİNCİ modeli de
    kapsayarak. Kısa pencere birinciyi bir sonraki turda yeniden denenebilir bırakır."""
    def _mut(cur):
        """Kısa dinlenmeyi yerinde yazar: `until` mevcut cezayla MAX'lanır (uzun bir ceza
        kısaltılmaz) ve `streak` olduğu gibi bırakılır (bu bir kota cezası değildir)."""
        row = cur.get(provider) or {}
        try:
            mevcut = float(row.get("until") or 0)
        except (TypeError, ValueError):  # sessiz-yutma: biçimsiz/eksik tek alan; yalnız bu değer düşer, satır başına uyarı asıl sinyali log seline gömerdi
            mevcut = 0.0
        until = max(mevcut, time.time() + float(seconds))
        cur[provider] = {**row, "until": until, "seconds": round(until - time.time(), 1),
                         "streak": int(row.get("streak") or 0),   # seri ARTMAZ: bu bir kota cezası değil
                         "reason": reason, "since": memory.now_iso()}
        return True
    doc = store.update_json(BRAIN_COOLDOWN_FILE, _mut, default={})
    return max(0.0, float(doc[provider]["until"]) - time.time())


def _rate_limited(exc: BaseException) -> tuple[bool, float | None]:
    """İstisna kota/oran sınırı mı? (429 · RESOURCE_EXHAUSTED · quota). Varsa Retry-After saniyesi."""
    resp = getattr(exc, "response", None)
    code = getattr(resp, "status_code", None)
    retry = None
    try:
        ra = (getattr(resp, "headers", None) or {}).get("retry-after")
        retry = float(ra) if ra else None
    except (TypeError, ValueError):  # sessiz-yutma: biçimsiz/eksik tek alan; yalnız bu değer düşer, satır başına uyarı asıl sinyali log seline gömerdi
        retry = None
    if code in (429, 529):
        return True, retry
    s = f"{type(exc).__name__}: {exc}".lower()
    if "429" in s or "too many requests" in s or "resource_exhausted" in s or "quota" in s:
        return True, retry
    return False, retry


def _provider_cooldown(p: str) -> float:
    """Sağlayıcının soğuması — nous YEREL ajan üzerinden konuşuyorsa ajanın soğuması da onu bağlar
    (aynı üst-akış kimliği: yerel ajan gemini sağlayıcısıyla kurulu)."""
    rem = brain_cooldown(p)
    if p == "nous":
        try:
            if _nous_local():
                rem = max(rem, brain_cooldown("agent"))
        except Exception:  # sessiz-yutma: yardımcı G/Ç yolu; çağıran yokluğu zaten yedek değerle karşılıyor ve asıl okuma hatası store katmanında bir kez uyarılıyor
            pass
    return rem


def brain_availability() -> dict:
    """Pano/teşhis: her sağlayıcı için {ready, cooling_s, reason} — DÜRÜST bozunma görünürlüğü.
    Anahtar DEĞERİ yok; yalnız 'kimlik var mı' ve 'soğumada mı'."""
    out = {}
    for p in brain_order():
        rem = _provider_cooldown(p)
        row = (store.read_json(BRAIN_COOLDOWN_FILE, {}) or {}).get(p) or {}
        out[p] = {"credentials": _provider_ready(p), "cooling_s": round(rem, 1),
                  "ready": bool(_provider_ready(p) and rem <= 0),
                  "reason": row.get("reason") if rem > 0 else None,
                  # HANGİ MODELE gidiyor — iki ayağın aynı kimliğe gittiği ancak burada görülür
                  # (nous ve gemini ikisi de gemini-3.5-flash'a gidiyordu).
                  "model_id": _model_id(p)}
    return out


def _model_id(p: str) -> str | None:
    """O sağlayıcıya GİDECEK model kimliği — `active_model()`in sağlayıcı-bağımsız hâli.

    NOUS'TA İKİ AYRI DÜNYA VAR ve varsayılan yalnız birinde meşrudur:
      * PORTAL modu — istek bizim kurduğumuz gövdeyle gider ve model alanını BİZ yazarız; NOUS_MODEL
        boşsa `NOUS_DEFAULT_MODEL` gerçekten gidecek olan modeldir. Varsayılan bir ÖLÇÜMDÜR.
      * YEREL AJAN modu — istek `hermes` ikilisine devredilir; hangi modele gideceğini onun KENDİ
        yapılandırması (`~/.hermes/config.yaml`) belirler. NOUS_MODEL boşken buraya varsayılanı
        yazmak UYDURMADIR: kimse o modeli seçmemiştir. Üstelik bu uydurma sayı `brain_chain_facts`
        içinde "model kimlikleri ayrık" hükmüne dönüşüyordu — yani ölçülmemiş bir yedeklilik
        iddiasının kaynağı tam da buydu. Ölçülemeyen değer None kalır."""
    if p == "claude":
        return MODEL
    if p == "nous":
        if _nous_local() and not (secrets.get("NOUS_MODEL") or "").strip():
            return None
        # ÇAĞRI ANIYLA AYNI AD (2026-08-13): `_agent_call` sırdaki ölü adı alias'a
        # çevirerek çağırıyor (`_nous_model_zinciri`). Raporlanan kimlik çevirmeden
        # geçseydi "ne çağırdığımız" ile "ne rapor ettiğimiz" ayrışır ve bu turun
        # kapattığı çift-kaynak sınıfının YENİSİ doğardı. OLAY BASILMAZ (`olay=False`,
        # 2026-08-13 düzeltmesi): burası RAPOR yüzeyi — bir pano isteği operatörün
        # defterine "göç oldu" satırı yazamaz; olayı gerçek çağrı yolu basar.
        return canonical_model(secrets.get("NOUS_MODEL"), kaynak="NOUS_MODEL") \
            or NOUS_DEFAULT_MODEL
    if p == "gemini":
        return gemini_model()
    return None


def brain_chain_facts() -> dict:
    """ZİNCİR GERÇEKTEN YEDEKLİ Mİ — YALNIZ DOĞRUDAN SAYILABİLİR OLGULAR.

    CANLI KANIT: `DEFAULT_BRAIN_ORDER` üç ad taşıyor ama claude kimliksiz (atlanıyor) ve nous ile
    gemini AYNI model kimliğiyle çağrılıyordu (gemini-3.5-flash). Pano iki yeşil çip gösterirken
    arkada tek kota vardı; "üç beyin" bir SAYIM değil bir VARSAYIMDI.

    BURADA BAĞIMSIZ UÇ SAYISI ÜRETİLMEZ. Yerel ajanın çağrı başına hangi upstream'e gittiği
    ölçülmüyor; ölçülmemiş bir sayı uydurmak — ya da bir ayağın soğumasını ölçülmemiş başka bir
    ayağa kopyalamak — bu maddenin düzeltmeye çalıştığı hatanın ta kendisi olurdu. Bu yüzden
    `independent_upstreams` bilerek None döner ve NEDENİ yanında durur (canslim deseni).
    Raporlanan tek şey `same_model_ids`'tir ve o bir çıkarım değil: elimizdeki iki dizginin
    eşitliği. Operatör bir Claude anahtarı girer ya da NOUS_MODEL'i Google dışı bir modele
    çevirirse bu ölçüm kendiliğinden düzelir."""
    order = brain_order()
    ready = [p for p in order if _provider_ready(p)]
    models = {p: _model_id(p) for p in order}
    same = sorted({tuple(sorted((a, b))) for a in ready for b in ready
                   if a != b and models.get(a) and models.get(a) == models.get(b)})
    return {"order": order, "ready": ready, "models": models,
            "same_model_ids": [list(pair) for pair in same],
            "nous_mode": ("local_agent" if _nous_local()
                          else ("portal" if (secrets.get("NOUS_ENDPOINT") or "").strip() else "-")),
            "agent_config_provider": _agent_provider(),
            "independent_upstreams": None,
            "independent_upstreams_reason":
                "yerel ajanın çağrı başına hangi uca gittiği ÖLÇÜLMÜYOR — bağımsız uç sayısı "
                "uydurulmaz. Yedeklilik iddiası ancak model kimlikleri FARKLIYSA desteklenir."}


def brain_order() -> list[str]:
    """Beyin zincirinin sırası: HERMES_BRAIN_ORDER (sır → ortam → varsayılan) virgüllü listesi.

    Yalnız TANINAN sağlayıcılar (claude/nous/gemini) geçer; bilinmeyen adlar sessizce elenir."""
    raw = secrets.get("HERMES_BRAIN_ORDER") or os.environ.get("HERMES_BRAIN_ORDER") or DEFAULT_BRAIN_ORDER
    known = {"claude", "nous", "gemini"}
    return [p.strip().lower() for p in raw.split(",") if p.strip().lower() in known]


def _provider_ready(p: str) -> bool:
    """Sağlayıcının KİMLİK BİLGİSİ hazır mı (anahtar/token, nous'ta yerel kurulum da yeter).

    Yalnız kimlik bilgisini ölçer — soğumayı DEĞİL; "şu an konuşabilen beyin" için
    `active_brain()` ikisini birlikte bakar."""
    if p == "claude":
        return bool(secrets.get("HERMES_API_KEY") or secrets.get("ANTHROPIC_API_KEY"))
    if p == "nous":
        return bool(secrets.get("NOUS_API_KEY")) or _hermes_bin() is not None   # yerel kurulum anahtar istemez
    if p == "gemini":
        return bool(secrets.get("GEMINI_API_KEY") or secrets.get("GEMINI_OAUTH_TOKEN"))
    return False


def active_brain() -> str:
    """ŞU AN gerçekten konuşabilen beyin. Eskiden yalnız 'anahtar var mı' bakıyordu: gemini üç gündür
    429 yerken pano hâlâ bir LLM beyni gösteriyordu ve deterministik yola düşüş görünmüyordu. Soğumada
    olan sağlayıcı atlanır — hiçbiri kalmazsa cevap DÜRÜSTÇE 'deterministic'tir."""
    for p in brain_order():
        if _provider_ready(p) and _provider_cooldown(p) <= 0:
            return p
    return "deterministic"


def active_model() -> str | None:
    """ŞU AN konuşacak beynin model kimliği = `_model_id`in AKTİF sağlayıcıya uygulanmış hâli.

    İKİ KOPYA BİRLEŞTİRİLDİ. Bu gövde `_model_id`in satır satır ikiziydi ve
    ikizler AYRIŞMIŞTI: `_model_id("nous")`e eklenen UYDURMA KORUMASI ("yerel ajan +
    `NOUS_MODEL` yok → hangi modele gidildiğini CLI'nın kendi config'i belirler, biz bilmeyiz →
    None") buraya hiç taşınmamıştı. ÖLÇÜLDÜ: aynı yapılandırmada `_model_id('nous')`
    dürüstçe None derken `active_model()` `'Hermes-4-405B'` döndürüyordu — yani HİÇ ÇAĞRILMAMIŞ
    bir model adı `hermes_status.json`da, panoda ve künye alanlarında durabiliyordu. Korumayı elle
    kopyalamak aynı sınıfı ÜÇÜNCÜ kez doğururdu; tek kaynağa bağlamak kapatır. (Ölü-ad çevirisi ve
    "rapor yüzeyi olay basmaz" kuralı `_model_id`in içinde AYNEN duruyor.)

    ÇAĞIRANLAR None'U TAŞIYOR — ölçüldü, varsayılmadı: `hermes_runtime._persist`/`status` zaten
    `model = None` yolunu taşıyor (test_brain_resilience_v66: deterministik yolda
    `disk["model"] is None`), pano `s.model || '—'` basıyor (web/app.js), `candidate_review` ve
    `chain_text` künyelerindeki `model_istenen` okuması None'a karşı korumalı."""
    return _model_id(active_brain())


def _parse_hyp(text: str) -> dict | None:
    """LLM çıktısından hipotez JSON'u — kod bloğu çitleri toleranslı, şekil doğrulamalı.

    None dönerken NEDENİ _trace_note ile bırakır: "boş" tek bir şey değildi ve üç ayrı arıza (hiç
    metin yok / metin var ama JSON değil / JSON var ama şema tutmuyor) aynı satıra katlanıyordu.
    Sınıf farkı teşhisin tamamı: ilki taşıma sorunu, ikincisi prompt-biçim sorunu, üçüncüsü model
    sorunudur ve üçü ayrı düzeltme ister."""
    if not text or not text.strip():
        _trace_note(EMPTY_NO_TEXT)
        return None
    t = text.strip()
    if t.startswith("```"):
        t = t.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
    try:
        hyp = json.loads(t)
    except json.JSONDecodeError:  # sessiz-yutma: yardımcı G/Ç yolu; çağıran yokluğu zaten yedek değerle karşılıyor ve asıl okuma hatası store katmanında bir kez uyarılıyor
        try:
            hyp = json.loads(_unwrap_strings(t))   # CLI paneli uzun stringleri sarmalar (string-içi ham \n)
        except json.JSONDecodeError:  # sessiz-yutma: yardımcı G/Ç yolu; çağıran yokluğu zaten yedek değerle karşılıyor ve asıl okuma hatası store katmanında bir kez uyarılıyor
            # KUYRUK DA BASILIR. `t[:120]` yalnız BAŞI gösteriyordu; oysa KESİLME
            # kuyrukta görünür. gemini bacağının günlerce yanlış sınıfta durmasının sebebi tam
            # buydu: baş sağlıklı bir JSON gibi okunuyor, kesik uç hiç görünmüyor — `truncated`
            # (bütçe sorunu) ile `unparseable` (biçim sorunu) aynı satıra katlanıyordu ve ikisi
            # AYRI düzeltme ister. Uzunluk da olgudur: tavana dayanmış bir gövde kendini söyler.
            # Kısa metinde baş ve son ÇAKIŞIR — aynı gövdeyi iki kez basmak izi uzatır, bilgi eklemez.
            detail = (f"len={len(t)} · {t}" if len(t) <= 160
                      else f"len={len(t)} · baş:{t[:80]} · son:{t[-80:]}")
            _trace_note(EMPTY_REFUSAL if _looks_like_refusal(t) else EMPTY_UNPARSEABLE, detail=detail)
            return None
    if not isinstance(hyp, dict) or not hyp.get("variable") or hyp.get("new") is None:
        _trace_note(EMPTY_SCHEMA, detail=",".join(sorted(hyp)[:6]) if isinstance(hyp, dict) else type(hyp).__name__)
        return None
    return hyp


# Reddi "bozuk JSON"dan ayırmak gerekiyor: ilki prompt/politika sorunudur (yeniden denemek işe yaramaz),
# ikincisi ayrıştırma sorunudur (biçim onarımı işe yarar). Aynı kovaya atmak ikisini de görünmez ediyordu.
_REFUSAL_MARKS = ("i can't", "i cannot", "i'm unable", "i am unable", "as an ai",
                  "yapamam", "yardımcı olamam", "üzgünüm", "sorry, i")


def _looks_like_refusal(t: str) -> bool:
    """Metnin BAŞI (ilk 400 karakter) bilinen ret kalıplarından birini taşıyor mu?

    Reddi "bozuk JSON"dan ayırmak için: ilki prompt/politika sorunudur (yeniden deneme işe
    yaramaz), ikincisi biçim sorunudur — aynı kovaya atmak ikisini de görünmez ediyordu."""
    head = (t or "")[:400].lower()
    return any(m in head for m in _REFUSAL_MARKS)


# Kanıt paketi karakter tavanı. 1400 → 6200: H1 karnesi + H2 aile hafızası + eşik eğrisi
# özeti + kuyruk durumu eklendi ve paket CANLI DEFTERDE 5.769 karakter ÖLÇÜLDÜ. Tavan o ölçümün
# ~%7 üstünde: bugün hiçbir alan düşmüyor (3.600'de component_ic + weekly_attention +
# dormant_setup_evidence düşüyordu — yani Aşama 1.2'nin bileşen-IC kanıtı, bir kör noktayı
# kapatmak için ekleneni bir başkasını açarak kesiyordu). Tavan KALDIRILMADI çünkü prompt şişmesi
# bağlam diyetinin (öneri #3) tersine çalışır; büyüme payı bilinçli olarak dar tutuldu ve tavan
# dolduğunda ne düşeceği artık BEYAN EDİLMİŞ (EVIDENCE_PRIORITY).
EVIDENCE_CAP = 6200


class _SkipHermesPack(Exception):
    """H-paketinin KASITLI atlanması (boş defter) — arıza değil, uydurma yasağının uygulanması."""


def evidence_pack() -> str:
    """#5 — kanıt paketi: kalibrasyon motorlarının ÖZETİ öneri prompt'una girer ki LLM genel-geçer
    değil kanıt-güdümlü önersin ("chop'ta w_vol düşür çünkü skor kalibrasyonu ... diyor"). Yalnız
    diskteki raporlar okunur (ucuz, deterministik); dosya yoksa alan atlanır — uydurma satır yok.
    Tavan ~1400 karakter: prompt şişmez."""
    import json as _json
    pack = {}
    try:
        sc = store.read_json("score_calibration.json", None)
        if sc:
            # GERÇEK dilim önce: havuzlanmış IC cf ağırlıklıdır ve beyne "skorun tahmin gücü"
            # diye sunulursa ölçülmemiş bir sinyale dayanarak öneri üretir.
            _re = sc.get("real") if isinstance(sc.get("real"), dict) else None
            if _re:
                pack["score_calibration"] = {"rank_ic": _re.get("rank_ic"), "n": _re.get("n"),
                                             "kaynak": "gerçek", "anlamli": _re.get("anlamli"),
                                             "monotone": sc.get("monotone_hint")}
            elif "real" in sc:
                # YENİ ŞEMA + GERÇEK DİLİM ÖLÇÜLEMEDİ. Havuzlanmış sayıyı yedek diye koymak, beyne
                # "işte skorun tahmin gücü" diye ALINMAMIŞ hipotetik girişlerin IC'sini sunmaktı ve
                # LLM onu prompt'ta gerekçe olarak alıntılıyordu. Sayı yerine ANALİZİN
                # KENDİ HÜKMÜ gider: ölçülmemiş olduğu, bir sayının içinde saklanmadan söylenir.
                pack["score_calibration"] = {"skor_kalibrasyonu": sc.get("verdict")
                                             or "gerçek dilim ÖLÇÜLMEDİ — skorun tahmin gücü bilinmiyor"}
            else:
                # GERÇEK eski-şema dosyası (`real` anahtarı HİÇ yok): elde yalnız havuzlanmış değer
                # var ve kaynağı adıyla etiketlenerek verilir — sessizce düşürmek de kanıt kaybıdır.
                pack["score_calibration"] = {"rank_ic": sc.get("rank_ic"), "n": sc.get("n"),
                                             "kaynak": "havuzlanmış",
                                             "monotone": sc.get("monotone_hint")}
        # BİLEŞEN IC — KOMPAKT. Beyin bugüne kadar yalnız BİLEŞİK skorun
        # IC'sini görüyordu ve o sayı sıfıra yakın olduğu için "skor işe yaramıyor" diye okunup
        # hipotezler kör bir yere, çoğunlukla çıkış knob'larına akıyordu. Bileşen kırılımı olmadan
        # "hangi ağırlığı hangi yöne?" sorusu kanıta bağlanamaz. Yalnız ÖLÇÜLEBİLEN hücreler ve
        # yalnız gerçek katman gider — ölçülemeyeni prompt'a koymak, beynin onu kanıt sanmasıdır.
        try:
            _cl = __import__("meridian.component_ic", fromlist=["compact_lines"]).compact_lines()
            if _cl:
                pack["component_ic"] = _cl
        except Exception as e:
            obs.warn("evidence_component_ic_failed", error=f"{type(e).__name__}: {e}")
        # MAE KARNESİ (K1 devri, 3b): `exit_efficiency`in ikizi. MFE çıkış kuralını yargılar, MAE
        # STOP kuralını — ve bugüne kadar beyin yalnız birini görüyordu, yani stop knob'unu (en
        # yoğun ölü aile: 21 deneme) KÖR öneriyordu.
        mp = store.read_json("mae_profile.json", None)
        if mp and mp.get("n"):
            pack["mae_profile"] = {"winners_p90_r": (mp.get("kazananlar") or {}).get("p90"),
                                   "losers_median_r": (mp.get("kaybedenler") or {}).get("medyan"),
                                   "losers_p90_r": (mp.get("kaybedenler") or {}).get("p90"),
                                   "verdict": mp.get("hukum")}
        ee = store.read_json("exit_efficiency.json", None)
        if ee:
            pack["exit_efficiency"] = {"avg_left_r": ee.get("avg_left_r"),
                                       "worst_reason": ee.get("worst_reason"),
                                       "worst_left_r": ee.get("worst_left_r")}
        gc = store.read_json("gate_calibration.json", None)
        if gc and gc.get("n_measured"):
            pack["ship_calibration"] = {"median_realized_over_predicted": gc.get("median_ratio"),
                                        "n": gc.get("n_measured"), "gate_extra_p": gc.get("extra_p")}
        lc = store.read_json("llm_calibration.json", None)
        if lc and (lc.get("n_pairs") or lc.get("cf_pairs")):
            pack["your_own_opinion_calibration"] = {"real_pairs": lc.get("n_pairs"),
                                                    "r_gap": lc.get("r_gap"),
                                                    "sim_pairs": lc.get("cf_pairs")}
        ar = store.read_json("arming_report.json", None)
        if ar and ar.get("cf_report"):
            pack["dormant_setup_evidence"] = {k: {"n": v.get("n"), "avg_r": v.get("avg_r")}
                                              for k, v in ar["cf_report"].items()}
        de = store.read_json("shadow_model.json", None)
        if de and de.get("promotion"):
            pack["shadow_model"] = {"promoted": de["promotion"].get("promoted"),
                                    "live_pairs": de["promotion"].get("n_live")}
        sr = store.read_json("self_review.json", None)
        if sr:
            pack["weekly_attention"] = [a["why"] for a in (sr.get("attention") or [])[:3]]
            pack["contradictions"] = [c["detail"] for c in (sr.get("contradictions") or [])[:2]]
        # cf-tarih bootstrap bulguları — ajanın hipotezlerini bunlara demirlemesi için birinci-sınıf:
        re = store.read_json("regime_edge.json", None)       # chop zararlı mı, trend_up pozitif mi?
        if re:
            pack["regime_edge_cf"] = {rg: {"avg_r": v.get("avg_r"), "n": v.get("n")}
                                      for rg, v in re.items() if (v.get("n") or 0) >= 30}
        nm = store.read_json("near_miss.json", None)          # hangi eşik masada +R bırakıyor
        if nm and nm.get("buckets"):
            leaves = {b: v.get("avg_r") for b, v in nm["buckets"].items()
                      if (v.get("n_r") or 0) >= 30 and (v.get("avg_r") or 0) > 0.03}
            if leaves:
                pack["thresholds_leaving_edge"] = leaves    # ör. {"rs":0.109} → rs eşiği gevşetmeyi öner
        # ---- HERMES ETKİNLEŞTİRME PAKETİ H1+H2+H3 ----------------------------------
        # ÜÇÜ DE `analytics` ÜZERİNDEN GELİR, SYSTEM'e HİÇBİR ŞEY EKLENMEZ: SYSTEM statik kalır
        # (AST testiyle çivilenmiş), bütün yeni kanıt USER-PROMPT yolundan girer. Sebebi tek:
        # SYSTEM prompt önbelleğe alınıyor (cache_control) ve içine değişken metin girdiği gün
        # önbellek her turda ıskalanır — maliyet sessizce katlanır.
        try:
            _a = __import__("meridian.analytics", fromlist=["hermes_scorecard"])
            _card = _a.hermes_scorecard()
            # BOŞ DEFTER → ALAN EKLENMEZ. Modülün baştan beri yazılı kuralı: "dosya yoksa alan
            # atlanır — uydurma satır yok". Hipotez defteri boşken "tahmin isabetin ÖLÇÜLMEDİ" ve
            # "32 düğmenin 32'si hiç önerilmemiş" satırları TEKNİK olarak doğru ama BİLGİ TAŞIMIYOR;
            # boş bir kurulumda prompt'u kanıt kılığında gürültüyle doldururlar (test_efficiency_v8
            # bu dürüstlüğü çiviliyor ve haklı).
            if not ((_card.get("families") or {}).get("n_hipotez")):
                raise _SkipHermesPack("hipotez defteri BOŞ — H1/H2 karnesi eklenmedi (uydurma yok)")
            # H1 — SENİN KENDİ KARNEN. Sayı yoksa "ölçülemedi" hükmü gider (boş karne "her şey
            # yolunda" diye okunmasın); bugün gerçek: TEK çift var ve YÖNÜ ters çıktı.
            _pb = _card.get("prediction_band") or {}
            pack["your_prediction_accuracy"] = {
                "n_pairs": _pb.get("n"), "verdict": _pb.get("hukum"),
                "band": _pb.get("band"), "direction_hits": _pb.get("yon_isabeti")}
            # H2 — ÖLÜ AİLELER + HİÇ DENENMEMİŞ DÜĞMELER. İkinci satır 15 gündür aynı 14 düğmede
            # dönmenin panzehiri: kör noktanın kendisi kanıt olarak prompt'a girer.
            _f = _card.get("families") or {}
            pack["dead_knob_families"] = {
                "families": {k: {"tried": v["denendi"], "shipped": v["ship"],
                                 "values": v["denenen_degerler"]}
                             for k, v in list((_f.get("olu_aileler") or {}).items())[:6]},
                "busiest_family": _f.get("en_yogun_aile"),
                "busiest_share": _f.get("en_yogun_pay"),
                "never_proposed_knobs": _f.get("hic_onerilmemis_dugmeler"),
                "never_proposed_count": _f.get("hic_onerilmemis_sayi"),
                "cost_note": _f.get("beyan")}
            pack["do_not_propose"] = _card.get("do_not")
            _tc = _card.get("threshold_curve") or {}
            if _tc:
                pack["threshold_curve"] = {"live_min_score": _tc.get("canli_min_score"),
                                           "verdict": _tc.get("verdict"),
                                           "cross_note": _tc.get("capraz_not"),
                                           "curve": _tc.get("egri_ozet")}
            _q = _card.get("composite_queue") or {}
            if _q:
                pack["composite_queue"] = {
                    "pending": _q.get("n_bekleyen"), "measured": _q.get("n_olculen"),
                    # OKUYUCUSU (YASA 6): `measure_failed` damgasını okuyan taraf BURASIDIR —
                    # beyin, kuyruğa attığı fikrin ölçülüp ölçülmediğini görmeden aynı fikri her
                    # hafta yeniden üretiyordu. "Ölçüm denendi ve DÜŞTÜ" ile "sırada bekliyor" aynı
                    # cümle değildir: ilki bir arıza sinyali, ikincisi normal bir kuyruk hâli.
                    "measure_failed": _q.get("n_basarisiz"),
                    "measuring": _q.get("n_olculuyor"),
                    "last_failure": _q.get("son_basarisiz"),
                    "weekly_budget_left": _q.get("butce_kalan"),
                    "how": ("propose a MULTI-knob idea as {\"composite\": {knob: value, ...}} — it is "
                            "NOT rejected by the one-variable law; it goes to the prescreen "
                            "measurement queue. Ship path unchanged: gate + operator.")}
        except _SkipHermesPack:  # sessiz-yutma: KASITLI atlama sinyali (boş defter); uyarı basmak "arıza" gibi okunurdu ve uydurma yasağının uygulanması arıza değildir
            pass
        except Exception as e:
            # H-paketi kanıtı düşerse GERİSİ AYAKTA KALIR: eski kanıt paketi birebir eski hâline
            # döner. Sessiz kalmaz — hermes'in kendi karnesini görmediği bir tur, "daha aktif
            # öğrenme" iddiasının tam olarak çöktüğü turdur.
            obs.warn("evidence_hermes_package_failed", error=f"{type(e).__name__}: {e}",
                     detail="H1/H2/H3 kanıtı prompt'a GİRMEDİ — hermes kendi karnesini görmüyor")
    except Exception as e:
        # YASA 4: kanıt paketi sessizce boşalırsa LLM ölçülmüş kalibrasyonları HİÇ
        # görmeden öneri üretir — çıktı yine geçerli görünür, yalnız dayanağı yoktur. "Üretilip
        # tüketilmeyen kanıt" ile aynı kök (yasa 6): kanıt vardı, kimseye ulaşmadı.
        obs.warn("evidence_pack_partial", error=f"{type(e).__name__}: {e}", keys=sorted(pack.keys()))
    if not pack:
        return ""
    return _render_pack(pack)


# KANIT PAKETİ ÖNCELİK SIRASI — tavan dolduğunda NE düşer, KARAR olarak yazılı.
# NEDEN GEREKTİ (3b'de ölçüldü): eski kod `_json.dumps(pack)[:1400]` idi, yani (a) paketi ORTASINDAN
# kesiyordu — dilim geçerli JSON bile değildi ve hermes bozuk metin okuyordu; (b) kesme SÖZLÜK
# EKLEME SIRASINA göre oluyordu, dolayısıyla EN YENİ eklenen kanıt (tam olarak H1/H2 karnesi:
# hermes'in kendi tahmin isabeti ve ölü aileleri) HER TURDA ilk düşen şey olurdu. Ölçüm: H-paketiyle
# paket 5.769 karaktere çıktı ve 3.600 tavanında yeni alanların TAMAMI kesiliyordu — "daha aktif
# öğrenme" turunun eklediği kanıt, hiç prompt'a girmeyecekti.
# Artık kesme ALAN DÜZEYİNDE: en düşük öncelikli alanlar TÜMDEN düşer, hangileri düştüğü prompt'a
# yazılır, ve JSON her zaman geçerli kalır. Sıra bir DEĞER YARGISIDIR ve burada görünür:
# hermes'in KENDİ karnesi (H1) ve mezarlığı (H2) en üstte, çünkü onları görmemesi bu turun
# çözdüğü sorunun kendisidir.
EVIDENCE_PRIORITY: tuple[str, ...] = (
    "your_prediction_accuracy",     # H1 — kendi tahmin isabetin
    "dead_knob_families",           # H2 — ölü aileler + hiç denenmemiş düğmeler
    "do_not_propose",               # H2 — YAPMA listesi (makine-okunur)
    "composite_queue",              # H3 — bileşik yolun varlığı ve bütçesi
    "score_calibration",
    "component_ic",
    "thresholds_leaving_edge",
    "regime_edge_cf",
    "exit_efficiency",
    "mae_profile",
    "threshold_curve",
    "ship_calibration",
    "your_own_opinion_calibration",
    "weekly_attention",
    "contradictions",
    "dormant_setup_evidence",
    "shadow_model",
)


def _render_pack(pack: dict) -> str:
    """Paketi tavana SIĞDIR — alan düşürerek, ortadan kesmeyerek. Düşen alanlar prompt'ta ADIYLA
    görünür: eksik kanıt, sessiz eksik kanıttan iyidir (hermes 'bunu görmedim' diyebilsin)."""
    import json as _json
    sira = [k for k in EVIDENCE_PRIORITY if k in pack]
    sira += [k for k in pack if k not in EVIDENCE_PRIORITY]      # beyan edilmemiş alan EN SONA
    secili: dict = {}
    dusen: list[str] = []
    for k in sira:
        aday = {**secili, k: pack[k]}
        if len(_json.dumps(aday)) <= EVIDENCE_CAP:
            secili = aday
        else:
            dusen.append(k)
    if dusen:
        obs.warn("evidence_pack_fields_dropped", cap=EVIDENCE_CAP, dropped=dusen,
                 kept=sorted(secili.keys()),
                 detail="kanıt paketi tavana çarptı — DÜŞÜK öncelikli alanlar tümden düşürüldü "
                        "(ortadan kesme YOK; JSON geçerli kaldı)")
    govde = _json.dumps(secili)
    ek = (f"\n[NOT: kanıt tavanı ({EVIDENCE_CAP} karakter) doldu; şu alanlar bu tura GİRMEDİ: "
          f"{', '.join(dusen)}]" if dusen else "")
    return ("\n\nEVIDENCE PACK (measured calibrations — ground your proposal in these numbers, "
            "cite which evidence motivates the change):\n" + govde + ek)


def _field_contract() -> str:
    """Alan sözleşmesini HYP_SCHEMA'DAN render et — elle yazma.

    NEDEN TÜRETİLMİŞ: şema ile prompt'taki alan listesi iki ayrı elle yazılmış kaynak olsaydı
    zamanla AYRIŞIRLARDI ve ayrıştıkları gün model, şemanın istemediği bir alanı üretip
    `_parse_hyp`ta sessizce düşerdi. Tek kaynak: şema değişince bu metin de değişir."""
    props = HYP_SCHEMA["properties"]
    req = set(HYP_SCHEMA["required"])
    satir = []
    for ad, spec in props.items():
        tip = spec.get("type")
        tip = "|".join(tip) if isinstance(tip, list) else tip
        parca = [f"{ad} ({tip}{'' if ad in req else ', optional'})"]
        if spec.get("enum"):
            parca.append("one of: " + ", ".join(spec["enum"]))
        if spec.get("description"):
            parca.append(spec["description"])
        if spec.get("properties"):          # iç içe nesne (skill_recommendation) — alanları da yazılır
            ic = []
            for k, v in spec["properties"].items():
                ic.append(k + ("[" + "|".join(v["enum"]) + "]" if v.get("enum") else ""))
            parca.append("fields: {" + ", ".join(ic) + "}")
        satir.append("- " + " — ".join(parca))
    return "\n".join(satir)


def _example_hypothesis() -> str:
    """bounds.yaml'daki GERÇEK bir anahtarla dolu, tek satırlık örnek.

    Boş bir şema tarifi ile dolu bir örnek aynı şey değildir: sağlayıcıların (nous/gemini) biçim
    hataları neredeyse tamamen "nasıl görünmeli"yi görmemekten geliyordu. Örnek bounds'tan üretilir,
    uydurma bir anahtar taşımaz — kopyalayıp yapıştıran bir model bile geçerli bir öneri üretir."""
    b = config.bounds()
    ad = next(iter(sorted(b)), "entry.rs_rating_min")
    spec = b.get(ad) or {}
    lo, step = spec.get("min", 0), spec.get("step", 1)
    deger = lo + step                                  # aralıkta ve adım üzerinde, tanımı gereği
    if str(spec.get("type", "")) == "int":
        deger = int(deger)
    else:
        deger = round(float(deger), 6)
    return json.dumps({
        "variable": ad, "new": deger,
        "rationale": "cite the evidence key that motivates this, e.g. gate_anchor or your_calibration",
        "predicted_direction": HYP_SCHEMA["properties"]["predicted_direction"]["enum"][0],
        "predicted_delta": 0.03, "confidence": 0.55, "regime": "all",
    })


# ================= ÜRETEÇ KEŞİF DENGESİ ==========================================
# ÖLÇÜLDÜ (canlı defter, 41 hipotez / 32 düğme): denemelerin %51,2'si TEK düğmede
# (`stop_loss_atr_mult`; 21 deneme, 0 ship) ve bounds'taki 32 düğmenin 18'i HİÇ hipotez taşımadı.
# Üreteç kendi tarihini GÖRMÜYORDU: ölü aile istatistiği ve kör nokta ölçülüyor (H2/`dead_families`)
# ama istemde yalnız ham veri olarak, kanıt paketinin İÇİNDE ve tavana çarpınca DÜŞEBİLİR hâlde
# duruyordu. Bu blok o iki gerçeği YÖNLENDİRMEYE çevirir — kota değil: kapı tek hakem kalır, beyin
# yine serbesttir, ama gerekçesiz ölü-aile tekrarı istemde AÇIKÇA caydırılır ve bakir düğmeler
# aralıklarıyla birlikte görünür olur.
#
# UYDURMA YASAĞI / TEK KAYNAK: "hiç önerilmemiş düğme" listesi ve "ölü aile" hükmü BURADA YENİDEN
# HESAPLANMAZ — ikisi de `analytics.dead_families()`ten (H2) alınır, aile tanımı bile onun
# `_knob_family`'sidir. İkinci bir sayım, panodaki "ölü aile" ile istemdeki "ölü aile"nin sessizce
# ayrışması demekti (analytics'in kendi notu: `dugme_aileleri` H2'den gelir, yeniden sayılmaz).
EXPLORE_WINDOW = 12          # "son N öneri" penceresi — keşif payının ölçüldüğü kuyruk uzunluğu
VIRGIN_IN_PROMPT = 12        # isteme yazılan bakir düğme tavanı (aşımı SAYIYLA beyan edilir)
DEAD_FAMILIES_IN_PROMPT = 5  # isteme yazılan ölü aile tavanı (aynı beyan kuralı)


def _h2_families() -> dict:
    """H2'nin GERÇEK hesabı (`analytics.dead_families`). Düşerse BOŞ döner ve bu SESSİZ DEĞİLDİR:
    kanıtsız kalan bir tur, "üreteç kendi tarihini görüyor" iddiasının çöktüğü turdur (YASA 4)."""
    try:
        _a = __import__("meridian.analytics", fromlist=["dead_families"])
        return _a.dead_families() or {}
    except Exception as e:
        obs.warn("hermes_h2_families_failed", error=f"{type(e).__name__}: {e}",
                 detail="H2 aile hafızası okunamadı — keşif bölümleri isteme GİRMEDİ (uydurulmadı)")
        return {}


def _dead_family_min_n() -> int:
    """"Ölü aile" eşiği H2'nin SABİTİNDEN okunur — istemde ikinci bir sayı yazmak, eşik değiştiği gün
    beyne yanlış tanımı öğretirdi."""
    try:
        return int(__import__("meridian.analytics", fromlist=["DEAD_FAMILY_MIN_N"]).DEAD_FAMILY_MIN_N)
    except Exception as e:
        obs.warn("hermes_dead_family_min_n_failed", error=f"{type(e).__name__}: {e}")
        return 3


def virgin_knobs() -> list[dict]:
    """H2'nin bakir düğme listesi + bounds aralıkları + canlı değer. YENİ SAYIM YOK: adlar H2'den
    gelir, buradaki tek katkı her ada bounds SATIRINI ve strategy.yaml'daki mevcut değeri iliştirmek.

    Aralık olmadan liste yönlendirme değil, ad dökümüdür: beyin `entry.min_rvol` adını görüp hangi
    değerin makul olduğunu bilemez ve düğmeyi kullanmaz (ölçülen davranışın ta kendisi)."""
    fam = _h2_families()
    adlar = fam.get("hic_onerilmemis_dugmeler")
    if not isinstance(adlar, list) or not adlar:
        return []
    try:
        b = config.bounds()
        params = (config.load_strategy() or {}).get("params", {}) or {}
    except Exception as e:
        obs.warn("hermes_virgin_bounds_unreadable", error=f"{type(e).__name__}: {e}",
                 detail="bounds/strategy okunamadı — bakir düğme bölümü ÜRETİLMEDİ")
        return []
    out, eksik = [], []
    for k in adlar:
        spec = b.get(k)
        if not spec:
            eksik.append(k)          # H2 listesi bounds'tan türer; ayrışma olduysa ADIYLA görünsün
            continue
        out.append({"knob": k, "min": spec["min"], "max": spec["max"], "step": spec["step"],
                    "type": spec["type"], "live": params.get(k)})
    if eksik:
        obs.warn("hermes_virgin_knob_not_in_bounds", knobs=eksik,
                 detail="H2 bakir listesindeki ad bounds'ta yok — iki kaynak ayrışmış")
    return out


def exploration_share(n: int = EXPLORE_WINDOW, *, fam: dict | None = None,
                      bakir: list | None = None) -> dict:
    """KEŞİF PAYI KARNESİ (YASA 6) — üretecin kendi dağılımı, ölçülür ve TÜKETİLİR.

    `fam`/`bakir` ENJEKTE EDİLEBİLİR (`analytics.system_telemetry`in `edge`/`sonuc` deseni): istem
    kurulurken H2 zaten okunuyor ve aynı defteri bir daha saymak yalnız maliyet değil TUTARSIZLIK
    riskidir — iki okuma arasına düşen bir yazım, istemdeki iki bölümün farklı sayılar taşımasına
    yol açardı.

    Üç sayı, üçü de defterin kendisinden:
      * `aile_dagilimi` — son N önerinin hangi ailelere düştüğü (aile tanımı H2'nin `_knob_family`si).
      * `bakir_isabet`  — kaç öneri kendi ailesine defterdeki İLK dokunuştu (yani o an bakirdi).
        H2'nin BUGÜNKÜ bakir listesiyle KARIŞTIRILMAZ: o liste "hiç dokunulmamış" düğmelerdir ve
        tanımı gereği defterde satırları yoktur; oraya bakan bir isabet ölçümü yapısal olarak hep
        0 verirdi. Buradaki soru geçmişe dönüktür: "bu öneri bir kapıyı İLK kez mi açtı?"
      * `olu_aile_tekrari` — kaç öneri, H2'nin BUGÜN ölü ilan ettiği bir aileye düştü. Sınıflandırma
        BUGÜNKÜ hükme göredir (öneri anındaki hâline göre değil) ve bu bir SAPMA olarak beyan edilir:
        H2 anlık bir görüntü üretir, geçmişe dönük yeniden sayım İKİNCİ bir ölü-aile tanımı olurdu.

    Ölçülemeyen None (uydurma yasağı): boş defterde üç alan da None döner, sebebiyle birlikte.

    DÖRDÜNCÜ SAYI — `on_eleme` (D1'in YASA-6 okuyucusu): yukarıdaki üç sayı YALNIZ
    DEFTERE GİREBİLMİŞ önerileri görür, yani "hayatta kalan"ı. `on_eleme`, defterden ÖNCEKİ arka
    plan korkuluğunda düşen ve orada çivilenen önerileri taşır — "üretim" ile "hayatta kalan"
    böylece AYRI iki sayı olur (D1 gerekçesinin ta kendisi). Defter BOŞ olsa bile ölçülür:
    ön-eleme sayımı hipotez defterinden BAĞIMSIZDIR ve boş defterde onu da None yapmak, ölçülmüş
    bir sayıyı ölçülemedi diye yazmak olurdu."""
    hyps = memory.all_hypotheses()
    toplam = len(hyps)
    on_eleme = bg_on_eleme_karnesi()
    beyan = ("bakir isabet = öneri kendi ailesine defterdeki İLK dokunuş mu; ölü aile sınıflandırması "
             "H2'nin BUGÜNKÜ hükmüdür (öneri anındaki değil) — H2 anlık görüntü üretir ve geçmişe "
             "dönük ikinci bir tanım yazılmadı; `on_eleme` DEFTER ÖNCESİ korkuluğu sayar (üretim ≠ "
             "hayatta kalan) ve kümülatif değil PENCERELİdir")
    if not toplam:
        return {"pencere": n, "n_olculen": 0, "n_defter": 0, "aile_dagilimi": None,
                "en_yogun_aile": None, "en_yogun_pay": None, "bakir_isabet": None,
                "olu_aile_tekrari": None, "bakir_dugme_kalan": None, "on_eleme": on_eleme,
                "beyan": "hipotez defteri BOŞ — keşif payı ÖLÇÜLEMEDİ (uydurulmadı)"}
    try:
        _a = __import__("meridian.analytics", fromlist=["_knob_family"])
        _aile = _a._knob_family
    except Exception as e:
        obs.warn("hermes_exploration_family_fn_failed", error=f"{type(e).__name__}: {e}",
                 detail="aile fonksiyonu okunamadı — keşif payı ÖLÇÜLEMEDİ (ikinci tanım yazılmadı)")
        return {"pencere": n, "n_olculen": 0, "n_defter": toplam, "aile_dagilimi": None,
                "en_yogun_aile": None, "en_yogun_pay": None, "bakir_isabet": None,
                "olu_aile_tekrari": None, "bakir_dugme_kalan": None,
                "beyan": "analytics._knob_family okunamadı — ölçüm YOK"}
    fam = _h2_families() if fam is None else fam
    olu_kume = set((fam.get("olu_aileler") or {}).keys())
    pencere = hyps[-n:] if n and n > 0 else hyps
    bas = toplam - len(pencere)
    dagilim: dict[str, int] = {}
    bakir_ad, olu_ad = [], []
    n_bakir = n_olu = 0
    for i, h in enumerate(pencere):
        f = _aile(h.get("variable"))
        dagilim[f] = dagilim.get(f, 0) + 1
        # SAYIM ÖNERİ BAŞINADIR, AİLE BAŞINA DEĞİL: aile başına sayılsaydı bir ailenin İLK
        # dokunuşu, o ailenin penceredeki BÜTÜN tekrarlarını da "bakir isabet" diye sayardı —
        # tam olarak ölçmek istediğimiz şeyin tersi (yoğunlaşma, keşif kılığında görünürdü).
        if not any(_aile(x.get("variable")) == f for x in hyps[:bas + i]):
            n_bakir += 1
            if f not in bakir_ad:
                bakir_ad.append(f)
        if f in olu_kume:
            n_olu += 1
            if f not in olu_ad:
                olu_ad.append(f)
    m = len(pencere)
    sirali = dict(sorted(dagilim.items(), key=lambda kv: (-kv[1], kv[0])))
    en_yogun = next(iter(sirali), None)
    return {
        "pencere": n, "n_olculen": m, "n_defter": toplam,
        "aile_dagilimi": sirali,
        "en_yogun_aile": en_yogun,
        "en_yogun_pay": (round(sirali[en_yogun] / m, 3) if en_yogun else None),
        "bakir_isabet": {"n": n_bakir, "oran": round(n_bakir / m, 3), "aileler": bakir_ad},
        "olu_aile_tekrari": {"n": n_olu, "oran": round(n_olu / m, 3), "aileler": olu_ad},
        "bakir_dugme_kalan": len(virgin_knobs() if bakir is None else bakir),
        "on_eleme": on_eleme,
        "beyan": beyan,
    }


def _exploration_sections() -> str:
    """İki KANIT bölümü, istem gövdesine (user-prompt) eklenir — SYSTEM'e DEĞİL.

    NEDEN USER-PROMPT: SYSTEM statik bir sabittir (AST testiyle çivili) ve `cache_control: ephemeral`
    yalnız bayt bayt aynı metinde isabet eder; içine değişken metin girdiği gün önbellek her turda
    ıskalar ve maliyet sessizce katlanır. Aynı gerekçe H1/H2/H3 paketinde de yazılı.

    NEDEN KANIT PAKETİNİN İÇİNDE DEĞİL: `_render_pack` tavana çarpınca alanları ÖNCELİK SIRASINA
    göre TÜMDEN düşürür. Bu turun tek çözdüğü şey bu iki bölümün beyne ulaşması; onları düşebilir
    bir kuyruğa koymak, işi yapmadan yapmış görünmekti. Paketteki `dead_knob_families` ham VERİYİ
    taşır (adlar), buradaki bölüm YÖNLENDİRMEYİ ve bounds ARALIKLARINI taşır — ikisi farklı iştir.

    BOŞ DEFTERDE HİÇBİR ŞEY YAZILMAZ: `evidence_pack`teki `_SkipHermesPack` ile aynı kural. Sıfır
    hipotezde "32 düğmenin 32'si bakir" teknik olarak doğru ama bilgi taşımaz ve istemi kanıt
    kılığında gürültüyle doldurur."""
    fam = _h2_families()
    if not fam or not fam.get("n_hipotez"):
        return ""
    L = ["\n\nEXPLORATION BALANCE (your own history — evidence, NOT a quota; the OOS gate remains "
         "the only judge and you stay free to propose anything in bounds.yaml):"]

    # ---- (A) ÖLÜ AİLELER ------------------------------------------------------------------------
    olu = list((fam.get("olu_aileler") or {}).items())
    if olu:
        L.append(f"\n(A) DEAD KNOB FAMILIES — tried repeatedly, NEVER shipped "
                 f"({_dead_family_min_n()}+ tries, 0 ships):")
        for k, v in olu[:DEAD_FAMILIES_IN_PROMPT]:
            L.append(f"  - {k}: {v.get('denendi')} tries, {v.get('ship')} shipped, "
                     f"outcomes {v.get('durumlar')}, values already tried {v.get('denenen_degerler')}")
        if len(olu) > DEAD_FAMILIES_IN_PROMPT:
            L.append(f"  (+{len(olu) - DEAD_FAMILIES_IN_PROMPT} more dead families not shown)")
        pay = fam.get("en_yogun_pay")
        if fam.get("en_yogun_aile") and pay is not None:
            L.append(f"  Concentration: {round(float(pay) * 100)}% of ALL hypotheses ever written sit in "
                     f"ONE family ({fam.get('en_yogun_aile')}).")
        L.append("  If your hypothesis comes from one of these families, your `rationale` MUST name a "
                 "failure reason DIFFERENT from the outcomes listed above and say what changed since. "
                 "Returning without that is not forbidden — it is expensive: each return grows the "
                 "family error budget K, which RAISES p_required and makes your own candidate harder "
                 "to ship.")

    # ---- (B) BAKİR DÜĞMELER ---------------------------------------------------------------------
    bakir = virgin_knobs()
    if bakir:
        L.append(f"\n(B) NEVER-PROPOSED KNOBS — {fam.get('hic_onerilmemis_sayi')} of the bounds.yaml "
                 f"universe has NEVER carried a single hypothesis. Ranges are given so you can "
                 f"actually reason about a value:")
        for r in bakir[:VIRGIN_IN_PROMPT]:
            canli = "unset" if r["live"] is None else r["live"]
            L.append(f"  - {r['knob']} [{r['min']}..{r['max']} step {r['step']}, {r['type']}] live={canli}")
        if len(bakir) > VIRGIN_IN_PROMPT:
            L.append(f"  (+{len(bakir) - VIRGIN_IN_PROMPT} more never-proposed knobs not shown)")
        L.append("  live=unset means the knob is absent from strategy.yaml — it is wired but "
                 "effectively off today, so proposing it turns a dormant mechanism ON.")
        L.append("  This is the widest unexplored part of the search space. If you can build a "
                 "plausible, evidence-CITED thesis for one of them, prefer it. If you cannot, say so "
                 "in `rationale` and propose what you can — an honest 'no thesis for the virgin "
                 "knobs yet' is a result, not a failure.")

    # ---- KEŞİF PAYI (ölçüm bölüme demir atar: yönlendirme sayıyla gerekçelenir) ------------------
    ks = exploration_share(fam=fam, bakir=bakir)
    if ks.get("n_olculen"):
        bi, ot = ks.get("bakir_isabet") or {}, ks.get("olu_aile_tekrari") or {}
        L.append(f"\n  Your last {ks['n_olculen']} proposals: family spread {ks['aile_dagilimi']}; "
                 f"first-ever-touch of a knob {bi.get('n')}/{ks['n_olculen']} "
                 f"({bi.get('oran')}); landed in an already-dead family {ot.get('n')}/{ks['n_olculen']} "
                 f"({ot.get('oran')}).")
    # ---- ÖN-ELEME: beyin, önerilerinin defter ÖNCESİ ne olduğunu da GÖRMELİ -------
    # Ölçülen körlük tam buydu: 47 öneri arka plan korkuluğunda düştü ve beyin bunu HİÇ görmedi —
    # aynı düğmeyi tekrar tekrar önermesinin (kart `yan_bulgu`: 37/47 iki değişkende) bir ayağı bu.
    # SAYI SIFIRSA SATIR YAZILMAZ: boş bir "0 rejected" satırı her turda token yakar ve hiçbir şey
    # anlatmaz.
    _oe = ks.get("on_eleme") or {}
    _red, _cvl = (_oe.get("reddedilen") or {}), (_oe.get("rejimlendirilen") or {})
    if _red.get("n") or _cvl.get("n"):
        L.append(f"\n  Background pre-filter (last {_oe.get('pencere')} events, NOT cumulative): "
                 f"{_cvl.get('n')} global proposal(s) were PINNED to the certified regime "
                 f"(x -> x@regime, they still had to clear guard + gate), "
                 f"{_red.get('n')} were REJECTED outright {_red.get('nedenler')}. A background round "
                 f"can only tune the regime it is certified for — propose 'knob@<that regime>' "
                 f"directly when you know it.")
    return "\n".join(L)


def _user_prompt(with_schema: bool = False) -> str:
    """TEK talimat kaynağı — üç sağlayıcı yolu da buradan geçer.

    `with_schema=True` (Claude): şema API tarafından ZORLANIR (`output_config.format`), o yüzden alan
    sözleşmesini prompt'a ikinci kez koymak yalnız token yakardı.
    `with_schema=False` (nous / gemini): şema zorlaması YOK — sözleşme, dolu örnek ve sert biçim
    cümlesi prompt'a girer. İki yol AYNI talimatı paylaşır; eskiden Claude yolunda ayrı bir inline
    metin vardı ve iki kopya sessizce ayrışabiliyordu (sağlayıcıya göre farklı davranan bir beyin,
    ölçülen şeyin ne olduğunu belirsizleştirir).

    `_exploration_sections()` HER İKİ dalda da eklenir ve kanıt paketinden SONRA gelir: yönlendirme,
    dayandığı sayıları (ölü aile / bakir düğme) okuduktan sonra okunmalı."""
    bas = ("Here is the current state. Read lessons.md first, score by regime, then propose ONE "
           "single-variable change most likely to raise the out-of-sample score.")
    if with_schema:
        return bas + "\n\n" + build_context() + evidence_pack() + _exploration_sections()
    return (bas + "\n\nReturn ONE hypothesis with exactly these fields:\n"
            + _field_contract()
            + "\n\nExample of a well-formed answer (shape only — do NOT copy the values):\n"
            + _example_hypothesis()
            # Ölçülen iki arıza: nous'un çıktı paneli JSON'un etrafına düzyazı koyuyordu, gemini
            # ```json çitleri basıyordu. İkisi de _extract_json'da kurtarılmaya çalışılıyor; kaynakta
            # engellemek kurtarma yolundan ucuzdur ve sessiz kayıp riskini sıfırlar.
            + "\n\nOutput RAW JSON only — no markdown fences, no prose before or after, "
              "exactly one object.\n\n"
            + build_context() + evidence_pack() + _exploration_sections())


def _hermes_bin() -> str | None:
    """Yerel hermes-agent ikilisi: HERMES_LOCAL_BIN env → PATH → bilinen kurulum yerleri. None = kurulu değil."""
    import shutil
    cand = os.environ.get("HERMES_LOCAL_BIN")
    if cand and os.path.exists(cand):
        return cand
    w = shutil.which("hermes")
    if w:
        return w
    for p in (os.path.expanduser("~/.hermes/bin/hermes"), os.path.expanduser("~/.local/bin/hermes")):
        if os.path.exists(p):
            return p
    return None


def _nous_local() -> bool:
    """Nous beyni YEREL mi çalışır? NOUS_ENDPOINT=='local' → zorla yerel; boşsa yerel ikili varsa yerel
    (uygulamanın parçası — operatör isteği), yoksa Portal API'ye düşer."""
    ep = (secrets.get("NOUS_ENDPOINT") or "").strip().lower()
    if ep == "local":
        return True
    if ep:
        return False
    return _hermes_bin() is not None


AGENT_RPM = int(os.environ.get("MERIDIAN_AGENT_RPM", "6"))     # ücretsiz katman güvenli tavanları —
AGENT_RPD = int(os.environ.get("MERIDIAN_AGENT_RPD", "150"))   # bugün canlıda yaşandı: kota sessizce bitti
AGENT_BUDGET_FILE = "agent_budget.json"


def _agent_budget_take(max_wait: float = 0.0) -> bool:
    """Token-kova: dakika penceresi (RPM) + gün sayacı (RPD). RPM doluysa ve max_wait izin veriyorsa
    slot açılana dek bekler; yoksa False → çağıran deterministik yoluna düşer (fail-open). RPD dolunca
    günde BİR kez uyarır — sessiz açlık yasak."""
    import time as _t
    import datetime as _dt
    st = store.read_json(AGENT_BUDGET_FILE, {})
    today = str(_dt.date.today())
    if st.get("date") != today:
        st = {"date": today, "day": 0, "minute": [], "warned": False}
    now = _t.time()
    st["minute"] = [x for x in (st.get("minute") or []) if now - x < 60]
    if int(st.get("day", 0)) >= AGENT_RPD:
        if not st.get("warned"):
            st["warned"] = True
            obs.warn("agent_budget_exhausted", rpd=AGENT_RPD,
                     detail="günlük ajan çağrı bütçesi doldu — deterministik yollar devrede")
        store.write_json(AGENT_BUDGET_FILE, st)
        return False
    if len(st["minute"]) >= AGENT_RPM:
        wait = 60.0 - (now - min(st["minute"])) + 0.5
        if wait > max_wait:
            obs.log("agent_rpm_deferred", wait_s=round(wait, 1), kind="skipped")
            store.write_json(AGENT_BUDGET_FILE, st)
            return False
        _t.sleep(wait)
        now = _t.time()
        st["minute"] = [x for x in st["minute"] if now - x < 60]
    st["minute"].append(now)
    st["day"] = int(st.get("day", 0)) + 1
    store.write_json(AGENT_BUDGET_FILE, st)
    return True


def _agent_budget_refund(reason: str) -> bool:
    """AĞA HİÇ ÇIKMAMIŞ ÇAĞRIYI GÜN SAYACINDAN GERİ AL.

    CANLI VAKA: yapılandırmasız yerel CLI hiçbir sağlayıcıya bağlanmadan `exit(1)` ediyordu, ama
    `_agent_budget_take` çağrıdan ÖNCE düştüğü için ölü zincir 150/150'lik RPD kotasını 06:19'da
    yaktı. Gerçek Gemini kotası EL DEĞMEMİŞken aday incelemesi tüm gün bütçe-reddi yedi: sayaç
    korumaya çalıştığı şeyi (sağlayıcı kotası) ölçmüyordu.

    NEDEN İADE, NEDEN "HİÇ ALMA" DEĞİL: yapılandırmasızlık ancak çağrının SONUCUNDAN bilinir
    (CLI'yi çalıştırmadan yapılandırmasını ölçmek ikinci bir alt süreç demektir — her çağrıya bir
    süreç eklemek, korumaya çalıştığımız maliyetten büyük). Bu yüzden düşüm önce alınır, hüküm
    sonra kesinleşir. Yarış güvenliği `store.update_json` kilidindedir (oku-değiştir-yaz atomik).

    RPM DAMGASI BİLEREK İADE EDİLMEZ. RPD sağlayıcı kotasını korur — yapılandırmasız çağrı ona
    hiç dokunmadı, iade edilir. RPM damgası ise AYNI ZAMANDA yerel süreç-doğurma hızının tek
    freni ve yapılandırmasız çağrı bir süreci GERÇEKTEN doğurdu (ölçülmüş yerel maliyet). İkisini
    birden iade etmek, ölü bir CLI'yi poll başına sınırsız kez çalıştırmanın önünü açardı.

    Dönüş: iade YAPILDI mı (gün damgası değiştiyse ya da sayaç zaten 0 ise yapılacak bir şey yok)."""
    import datetime as _dt
    today = str(_dt.date.today())
    iade = {"oldu": False}

    def _mut(st):
        """GÜN (RPD) sayacından bir düşüm iade eder; gün damgası bugünün değilse ya da sayaç
        zaten 0 ise dokunmaz (dünün sayacını değiştirmek bugünü iki kez muhasebe etmek olurdu)."""
        if st.get("date") != today or int(st.get("day", 0) or 0) <= 0:
            return False            # dünün sayacına dokunmak, bugünü iki kez muhasebe etmektir
        st["day"] = int(st["day"]) - 1
        iade["oldu"] = True
        return True

    try:
        store.update_json(AGENT_BUDGET_FILE, _mut, default={})
    except Exception as e:
        # YASA 4: iade düşerse SESSİZ kalmak, (d) kaleminin canlıda çalıştığını sanmak demektir —
        # sayaç yanlış kalır ve bunu söyleyen tek satır olmaz. Karar akışı bozulmaz (çağıran zaten
        # None dönüyor), yalnız muhasebe kaybı adıyla deftere düşer.
        obs.warn("agent_budget_refund_failed", reason=reason, error=f"{type(e).__name__}: {e}",
                 detail="ağa çıkmamış çağrının bütçe iadesi yazılamadı — gün sayacı fazla okuyor")
        return False
    return iade["oldu"]


# ==================================================================================================
# BÜTÇE ÖZ-AYARI — STATİK TAVANLAR KOTA DURUMUNDAN TÜRETİLİR
# ==================================================================================================
# NEDEN. `MERIDIAN_BACKFILL_MAX_DAYS=40` ve `HERMES_SEARCH_BUDGET=10` sabit sayılardı ve ikisi de
# GERÇEKTEN KALAN kotadan habersizdi. İki yönde de yanlıştı: kota bolken tavan boşuna alçak
# (kanıt kuyruğu gereksiz yavaş erirdi), kota tükenmişken tavan boşuna yüksek (her plan-günü bir
# `agent_budget_take` reddine çarpar, defteri `agent_rpm_deferred` ile doldurur ve hiçbir iş çıkmaz).
#
# TÜRETİM TEK FONKSİYONDA (`quota_state`) ve iki tüketicisi var. Formül:
#
#     kalan          = max(0, AGENT_RPD − agent_budget.json["day"])      # bugünkü kalan çağrı hakkı
#     soguma         = hermes.brain_cooldown("agent") > 0                # havuz 429 yemiş mi
#     dolgu_tavani   = 0                       eğer soguma
#                    = floor(kalan × BACKFILL_SHARE)   aksi hâlde
#
# `BACKFILL_SHARE` NEDEN VAR (yani neden "kalanın tamamı" değil): dolgu ÇEVRİMDIŞI bir iştir ve
# aynı kovadan içen CANLI yollar var — gece başına ~1 öneri (`propose_with_llm`), seans başına
# 1 aday incelemesi (`review_candidates`), keşif yuvası sıralaması (`rank_explore`), haftada bir
# mekanizma değerlendirmesi (`nous_eval`). Kalanın tamamını dolguya vermek, ertesi sabah canlı
# yolun kotasız kalması demekti — ve canlı yol sessizce deterministik moda düşerdi (fail-open).
# ORAN ÖLÇÜMDEN GELİR: canlı `agent_budget.json` bugün day=10/RPD=150 okuyor, yani canlı yolun
# ölçülmüş tüketimi kotanın ~%7'si. Üçte bir pay, o tüketimin ~5 katını rezerve bırakır.
BACKFILL_SHARE = 1.0 / 3.0
# Dolgu gün başına EN AZ bu kadar plan-günü dener (kota neredeyse dolu olsa bile): sıfır tavan,
# 93 günlük kuyruğun HİÇ erimemesi demektir ve "bütçe kıstı" ile "mekanizma öldü" ayırt edilemez.
BACKFILL_MIN = 1
SEARCH_BUDGET_MAX = 20      # arama tavanının üst sınırı (CPU: budget × walk-forward)


def quota_state() -> dict:
    """AJAN KOTASININ TEK ÖLÇÜMÜ — bütün dinamik tavanlar buradan türer.

    `agent_budget.json` GÜN sayacı + `brain_cooldown` ajan penceresi. Gün damgası bugüne ait
    değilse sayaç SIFIR sayılır — `_agent_budget_take` de aynı sıfırlamayı yapar (dünün sayacına
    bakıp bugünü kısmak, kotayı iki kez harcamış gibi davranmaktır)."""
    import datetime as _dt
    st = store.read_json(AGENT_BUDGET_FILE, {}) or {}
    gun = int(st.get("day", 0)) if st.get("date") == str(_dt.date.today()) else 0
    kalan = max(0, AGENT_RPD - gun)
    try:
        soguma = float(brain_cooldown("agent"))
    except Exception as e:
        # YASA 4: soğuma okunamazsa tavanı SESSİZCE yüksek bırakmak, bilinen-ölü sağlayıcıyı
        # dövmektir. Muhafazakâr taraf "soğumada say" değil "bilinmiyor de ve söyle"dir; tavan
        # yine hesaplanır ama nedeni defterde durur.
        obs.warn("quota_state_cooldown_unreadable", error=f"{type(e).__name__}: {e}")
        soguma = 0.0
    return {"rpd": AGENT_RPD, "rpm": AGENT_RPM, "kullanilan": gun, "kalan": kalan,
            "kalan_oran": round(kalan / AGENT_RPD, 3) if AGENT_RPD else None,
            "agent_cooldown_s": round(soguma, 1), "soguma_aktif": soguma > 0}


def _env_override(name: str) -> int | None:
    """Env değişkeni SET EDİLMİŞSE onun değeri kazanır — türetim ona DOKUNMAZ. Bozuk değer
    sessizce yutulmaz: uyarı düşer ve türetime geri dönülür (yanlış bir sayıyla koşmaktansa
    ölçülmüş bir sayıyla koşmak)."""
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return None
    try:
        return int(raw)
    except ValueError:
        obs.warn("budget_env_override_invalid", var=name, value=raw,
                 detail="env override sayı değil — türetilmiş tavan kullanılıyor")
        return None


def backfill_budget() -> dict:
    """GECE BAŞINA EN ÇOK KAÇ PLAN-GÜNÜ dolgulanır. Dönüş türetimin TAMAMINI taşır ki panoda
    "neden 3?" sorusu dosyaya bakmadan cevaplanabilsin (sabit sihirli sayı yasağının ikizi:
    türetilmiş bir sayı da, türetimi görünmüyorsa sihirlidir)."""
    q = quota_state()
    ov = _env_override("MERIDIAN_BACKFILL_MAX_DAYS")
    if ov is not None:
        return {**q, "tavan": max(0, ov), "kaynak": "env:MERIDIAN_BACKFILL_MAX_DAYS",
                "formul": "operatör override — türetim devre dışı"}
    if q["soguma_aktif"]:
        return {**q, "tavan": 0, "kaynak": "turetim",
                "formul": f"ajan havuzu soğumada ({q['agent_cooldown_s']} sn) → tavan 0"}
    tavan = max(BACKFILL_MIN, int(q["kalan"] * BACKFILL_SHARE))
    return {**q, "tavan": tavan, "kaynak": "turetim",
            "formul": f"max({BACKFILL_MIN}, floor(kalan {q['kalan']} × {round(BACKFILL_SHARE, 3)})) "
                      f"= {tavan}"}


def search_budget() -> dict:
    """KOORDİNAT-İNİŞİ ARAMA TAVANI — kota durumuna bağlı, AMA TERS YÖNDE. BEYAN EDİLMİŞ SAPMA.

    Turun yönergesi "bol kota → tavan yukarı, soğumada → sıfıra" diyordu ve bu DOLGU için doğrudur
    (dolgu her plan-günü için bir LLM çağrısı yakar). Arama için YANLIŞ olurdu ve nedeni ölçülebilir:
    `SEARCH_BUDGET` bir LLM bütçesi DEĞİL, bir CPU bütçesidir — `reflect.search_and_submit`ın
    koşturacağı walk-forward sayısı. Kotayla tek ilişkisi ROLDÜR: beyin zinciri soğumadayken
    (`brain_cooldown`) ya da kota bittiğinde `propose_with_llm` boş döner ve hipotez üreten TEK
    mekanizma bu aramadır. Yönergeyi harfiyen uygulamak — soğumada tavanı 0 yapmak — üretecin son
    kolunu tam da diğerleri düştüğü gece kesmek olurdu.

    O yüzden ilişki ters kurulur ve SINIRLIDIR: taban `SEARCH_BUDGET` (eski sabit davranış), beyin
    yokken `SEARCH_BUDGET_MAX`a kadar açılır. Tavan asla 0 olmaz ve asla sınırsız büyümez."""
    q = quota_state()
    ov = _env_override("HERMES_SEARCH_BUDGET")
    if ov is not None:
        return {**q, "tavan": max(1, ov), "kaynak": "env:HERMES_SEARCH_BUDGET",
                "formul": "operatör override — türetim devre dışı"}
    beyinsiz = bool(q["soguma_aktif"] or q["kalan"] <= 0)
    tavan = min(SEARCH_BUDGET_MAX, SEARCH_BUDGET * 2) if beyinsiz else SEARCH_BUDGET
    return {**q, "tavan": tavan, "kaynak": "turetim",
            "formul": (f"beyin kolu {'KAPALI' if beyinsiz else 'açık'} → "
                       f"{'min(%d, %d×2)' % (SEARCH_BUDGET_MAX, SEARCH_BUDGET) if beyinsiz else 'taban'}"
                       f" = {tavan}"),
            "beyan": ("CPU bütçesi — kotayla ilişkisi TERSTİR: beyin susunca hipotez üreten tek "
                      "mekanizma arama olur, o gece kısılamaz")}


# ==================================================================================================
# ISINMA SPRİNTİ OTO-ÖLÇEKLEMESİ (operatör ops-kuralı, ÖLÇÜM DEĞİL: kart gerekmez)
# ==================================================================================================
# CANLI OLGU: `warmup_sprint` her ~4,4 saatte bir koşuyor ve serisi `evaluated 10→20→30,
# cleared: 0, best: null`. Bütçe SABİTTİ (`hermes_runtime`de `HERMES_WARMUP_BUDGET` varsayılanı 10),
# yani "hiçbir aday kapıyı geçmedi" olgusu bir sonraki koşumun HİÇBİR şeyini değiştirmiyordu:
# mekanizma aynı duvara aynı hızla, süresiz olarak çarpıyordu.
#
# YASA — DETERMİNİSTİK, TEK YÖNLÜ, GERİ DÖNÜŞLÜ:
#   cleared == 0            → çarpan ×2 (tavana kadar)   ve k_max bir kademe genişler
#   cleared  > 0            → çarpan 1'e DÖNER (taban)   ve k_max tabana döner
#   arama süre-tavanına takıldı (`kesildi`) → ÇARPAN BÜYÜMEZ; bir kademe geri iner ve o seviye
#                              DUVAR olarak kaydedilir (bir daha üstüne çıkılmaz)
#
# TAVAN NEDEN "DUVAR" DİYE ÖLÇÜLÜR, SABİT SAYIYLA YAZILMAZ: brief'in tavanı "H11 süre-tavanı içinde
# kalan maksimum"dur ve o sayı makineye, veri boyutuna ve önbellek sıcaklığına bağlıdır — burada bir
# sayı UYDURMAK, tam da düzeltmeye çalıştığımız "sabit sihirli tavan" sınıfını geri getirirdi. Süre
# tavanına takılan koşum, o makinede "fazla" nın ÖLÇÜMÜDÜR; merdiven onu duvar sayar. `WARMUP_SCALE_MAX`
# yalnız mutlak bir emniyet bandıdır (ölçüm hiç gelmezse sonsuza dek büyümeyi engeller).
#
# DÜRÜST BEYAN — BU KURAL `cleared`I ARTIRMAYABİLİR (ölçüldü, 2026-08-06, yerel defter n=353 sonda):
# sondaların %36'sı (128/353) incumbent'tan YÜKSEK OOS üretti ama yalnız 6'sı TAM KAPIYI geçti.
# Yani `cleared: 0`ın bağlayıcı kısıtı "aday yok" değil KAPI'dır; üstelik kapıya giden K = planlanan
# TOPLAM sonda sayısıdır (`reflect.coordinate_descent_search` → `_gate_eval(k_probes=total)`), yani
# bütçeyi büyütmek kazananın-laneti cezasını da büyütür ve çıtayı YÜKSELTİR. Bu kuralın ölçülmüş
# faydası `cleared` değil KAPSAMA'dır: ısınmanın asıl işi UCB önceliklerini ve sonda önbelleğini
# ısıtmaktır (`record_session=False` — hiçbir şey ship etmez), ve geniş tarama onu doğrudan besler.
WARMUP_BUDGET_BASE = 10          # `hermes_runtime._warmup_sprint`in bugünkü sabiti — taban AYNEN korunur
WARMUP_SCALE_MAX = 8             # mutlak emniyet bandı: taban × 8'den öteye ölçüm olmadan çıkılmaz
WARMUP_KMAX_BASE = 2             # bugünkü k_max
WARMUP_KMAX_MAX = 4              # kademe tavanı (bounds adımının 4 katı = düğmenin uçları)
WARMUP_SCALE_FILE = "warmup_scale.json"


def warmup_budget() -> dict:
    """ISINMA SPRİNTİNİN BU KOŞUMDAKİ BÜTÇESİ + kmax — türetimin TAMAMIYLA birlikte.

    Taban `HERMES_WARMUP_BUDGET`tir (operatör kolu) ve artık SABİT DEĞİL TABANDIR: merdiven yalnız
    yukarı, yalnız `cleared == 0` olgusuyla açılır ve ilk clearing'de tabana düşer.

    NOT — `HERMES_SEARCH_BUDGET` BU YOLA GİRMEZ: o değişken `SEARCH_BUDGET` → `search_budget()`
    üzerinden GERÇEK yansımanın (ship yetkili) arama tavanını besler. İkisini burada birleştirmek,
    canlı birimin `HERMES_SEARCH_BUDGET=8` satırını ısınmanın tabanına sessizce taşırdı (10→8) —
    yani bir dağıtım notu olmadan davranış değişirdi. Ayrık kalır; adlandırma operatör kalemi."""
    st = store.read_json(WARMUP_SCALE_FILE, {}) or {}
    ov = _env_override("HERMES_WARMUP_BUDGET")
    taban = max(1, ov) if ov is not None else WARMUP_BUDGET_BASE
    kaynak = "env:HERMES_WARMUP_BUDGET" if ov is not None else "varsayılan"
    duvar = st.get("duvar")
    carpan = max(1, int(st.get("carpan", 1) or 1))
    carpan = min(carpan, int(duvar) if duvar else WARMUP_SCALE_MAX, WARMUP_SCALE_MAX)
    kademe = max(0, carpan.bit_length() - 1)          # ×1→0, ×2→1, ×4→2, ×8→3
    k_max = min(WARMUP_KMAX_MAX, WARMUP_KMAX_BASE + kademe)
    budget = taban * carpan
    return {"taban": taban, "taban_kaynagi": kaynak, "carpan": carpan, "duvar": duvar,
            "budget": budget, "k_max": k_max, "kademe": kademe,
            # `reflect.coordinate_descent_search` plan kapağı: sonda genişliği bütçeden TÜRER
            # (`probes[:max(budget*4, 40)]`) — burada ikinci bir genişlik sayısı tanımlamak, aynı
            # yasanın iki yerde yaşayıp sessizce ayrışması demekti.
            "sonda_tavani": max(budget * 4, 40),
            "formul": f"taban {taban} ({kaynak}) × çarpan {carpan}"
                      + (f" [duvar ×{duvar}]" if duvar else "") + f" = {budget}; "
                      f"k_max {WARMUP_KMAX_BASE}+{kademe} = {k_max}",
            "son": st.get("son")}


def warmup_budget_feedback(res: dict | None) -> dict:
    """Bir ısınma koşumunun sonucunu merdivene işle. Çağıran: `hermes_runtime._warmup_sprint`.

    `res` = `coordinate_descent_search` dönüşü (`cleared`/`evaluated`/`kesildi`). None ya da hatalı
    koşum merdivene DOKUNMAZ: ölçülemeyen bir koşumdan "temizlenemedi" hükmü çıkarmak, arızayı
    bütçe kararına çevirmek olurdu (UYDURMA YASAĞI'nın bütçe tarafındaki hâli)."""
    if not isinstance(res, dict):
        return warmup_budget()
    onceki = warmup_budget()
    cleared = int(res.get("cleared") or 0)
    kesildi = bool(res.get("kesildi"))
    yeni, duvar, sebep = onceki["carpan"], onceki["duvar"], None
    # MERDİVEN DUVARA DAYANDI MI? Büyüme dalının koşulunun tam TERSİ; burada AYRICA hesaplanır
    # çünkü aşağıdaki `elif` zinciri "girmedi" bilgisini kaybediyor ve kaybettiği için yedi gün
    # boyunca kimse mekanizmanın durduğunu göremedi (2026-08-24 teşhisi).
    _tavan = min(int(duvar) if duvar else WARMUP_SCALE_MAX, WARMUP_SCALE_MAX)
    _kilitli = (not kesildi) and cleared == 0 and onceki["carpan"] >= _tavan
    if kesildi:
        # SÜRE TAVANI ÖLÇÜMDÜR: bu makinede bu genişlik H11 penceresine SIĞMADI. Bir kademe geri
        # in ve seviyeyi duvar olarak çivile — aksi hâlde merdiven her turda aynı tavana çarpıp
        # yarım ölçümler üretirdi (ve `kesildi` zaten K sayımını dürüst tutmak için sonda kırpar).
        yeni = max(1, onceki["carpan"] // 2)
        duvar = max(1, onceki["carpan"] // 2)
        sebep = "sure_tavani"
    elif cleared > 0:
        yeni, sebep = 1, "cleared>0"
    elif onceki["carpan"] < min(int(duvar) if duvar else WARMUP_SCALE_MAX, WARMUP_SCALE_MAX):
        yeni, sebep = min(onceki["carpan"] * 2,
                          int(duvar) if duvar else WARMUP_SCALE_MAX, WARMUP_SCALE_MAX), "cleared=0"

    def _mut(st):
        """Merdiven durumunu yazar: yeni çarpan, (varsa) duvar kademesi ve son koşumun künyesi
        (evaluated/cleared/kesildi + zaman damgası).

        `kilit_ardisik`: merdiven ÜST ÜSTE kaç turdur duvara çarpıyor. Bir BAYATLIK ÖLÇÜSÜDÜR —
        duvar meşru bir ölçümdür ama süresi yoktur ve yeniden sınanmaz; sayaç, "bu duvar ne
        kadar zamandır sorgulanmadı?" sorusunu cevaplanabilir kılar. Kilit dışındaki HER dal
        (clearing, süre tavanı, gerçek büyüme) onu SIFIRLAR: seriler birbirinin kuyruğuna
        eklenmemeli, yoksa sayı "kesintisiz kilit" demeyi bırakır."""
        st["carpan"] = int(yeni)
        st["duvar"] = int(duvar) if duvar else None
        st["kilit_ardisik"] = (int(st.get("kilit_ardisik") or 0) + 1) if _kilitli else 0
        import datetime as _dtw
        st["son"] = {"evaluated": res.get("evaluated"), "cleared": cleared, "kesildi": kesildi,
                     "at": _dtw.datetime.now(_dtw.timezone.utc).isoformat(timespec="seconds")}
        return True

    store.update_json(WARMUP_SCALE_FILE, _mut, default={})
    sonraki = warmup_budget()
    if _kilitli:
        # SESSİZ DURUŞ YOK (2026-08-24). `warmup_budget_scaled` yalnız DEĞİŞİMDE basar; kilitliyken
        # hiçbir şey değişmediği için canlıda yedi gün / 154 koşum boyunca tek satır düşmedi ve
        # mekanizmanın durduğu ancak `state/warmup_scale.json`a elle bakınca görüldü.
        # BU SATIR HİÇBİR ŞEYİ DEĞİŞTİRMEZ — bütçe, k_max ve eşik aynen kalır; yalnız duruş GÖRÜNÜR.
        _ard = int((store.read_json(WARMUP_SCALE_FILE, {}) or {}).get("kilit_ardisik") or 0)
        obs.log("warmup_merdiven_kilitli", carpan=sonraki["carpan"], duvar=sonraki["duvar"],
                budget=sonraki["budget"], k_max=sonraki["k_max"], cleared=cleared,
                evaluated=res.get("evaluated"), ardisik=_ard,
                detail=("ısınma merdiveni DUVARA DAYALI: `cleared=0` büyümeyi istiyor ama çarpan "
                        "zaten duvarda, yani bütçe ve k_max DEĞİŞMİYOR. Duvar bir ÖLÇÜMDÜR (bu "
                        "genişlik bu makinede H11 penceresine sığmamıştı) ama SÜRESİ YOKTUR ve "
                        "yeniden sınanmaz — `ardisik` o duvarın kaç turdur sorgulanmadığını sayar. "
                        "Duvarı gevşetmek bir ÖLÇÜM işidir, bir ops kararı değil: merdiveni açmak "
                        "sonda sayısını artırır, K büyür ve ön eleme eşiği SIKILAŞIR (EDG-2026-058) "
                        "— etkinin yönü ölçülmeden bilinmiyor."))
    if yeni != onceki["carpan"] or (duvar and duvar != onceki["duvar"]):
        obs.log("warmup_budget_scaled", sebep=sebep, evaluated=res.get("evaluated"), cleared=cleared,
                kesildi=kesildi, carpan_onceki=onceki["carpan"], carpan_yeni=sonraki["carpan"],
                butce_onceki=onceki["budget"], butce_yeni=sonraki["budget"],
                k_max_onceki=onceki["k_max"], k_max_yeni=sonraki["k_max"], duvar=sonraki["duvar"],
                detail=("ısınma sprinti hiçbir adayı kapıdan geçiremedi — SONRAKİ koşumun bütçesi ve "
                        "k_max'ı bir kademe genişletildi (deterministik ops kuralı; ilk clearing'de "
                        "tabana döner)" if sebep == "cleared=0" else
                        "ısınma bir aday temizledi — merdiven TABANA döndü; geniş tarama artık "
                        "gerekmiyor ve geniş K kapıyı boşuna sıkardı" if sebep == "cleared>0" else
                        "ısınma H11 süre tavanına takıldı: bu genişlik bu makinede pencereye SIĞMIYOR "
                        "— kademe geri alındı ve seviye DUVAR olarak çivilendi (tavan uydurulmaz, "
                        "ölçülür)"))
    return sonraki


def backfill_queue() -> dict:
    """DOLGU KUYRUĞUNUN KARNE SATIRI (YASA 6 tüketicisi: analytics + /api/diagnostics).

    `backfill_opinions`ın İŞ LİSTESİYLE AYNI KURALI kullanır — ikinci bir "görüşsüz" tanımı
    yazmak, panonun gösterdiği kuyrukla mekanizmanın erittiği kuyruğun sessizce ayrışması demekti.
    Yani: sonucu BİLİNEN (kapanmış işlem) ama görüşü OLMAYAN planlar, güne göre gruplu.

    `gorussuz_toplam` AYRI SAYILIR ve bilerek daha büyüktür: sonucu henüz bilinmeyen planlar da
    görüşsüzdür ama dolgu onlara DOKUNAMAZ (kalibrasyon çifti için sonuç şart). İki sayıyı tek
    satırda birleştirmek, kuyruğun neden erimediğini açıklanamaz yapardı."""
    plans = store.read_jsonl("trade_plans.jsonl")
    outcome_ids = {str(t.get("plan_id")) for t in store.read_jsonl("trades.jsonl")
                   if t.get("r_multiple") is not None}
    gunler: dict = {}
    gorussuz = 0
    for p in plans:
        if "llm_opinion" in p:
            continue
        gorussuz += 1
        day = p.get("date")
        if day and str(p.get("id")) in outcome_ids:
            gunler.setdefault(str(day), 0)
            gunler[str(day)] += 1
    bt = backfill_budget()
    sirali = sorted(gunler)
    return {"gorussuz_toplam": gorussuz, "n_plan": len(plans),
            "dolgulanabilir_gun": len(sirali), "dolgulanabilir_satir": sum(gunler.values()),
            "en_eski": sirali[0] if sirali else None, "en_yeni": sirali[-1] if sirali else None,
            "gece_tavani": bt["tavan"], "tavan_kaynagi": bt["kaynak"], "tavan_formulu": bt["formul"],
            "tahmini_gece": (None if not sirali or bt["tavan"] <= 0
                             else -(-len(sirali) // bt["tavan"])),
            "beyan": ("dolgu YALNIZ sonucu bilinen planlara dokunur (kalibrasyon çifti sonuç ister); "
                      "`gorussuz_toplam` bu yüzden daha büyüktür ve bir arıza DEĞİLDİR")}


def _agent_reply_missing(stdout: str) -> bool:
    """Boş-oturum imzası (canlıda görüldü): CLI özeti 'Messages: N' der; N<=1 = yalnız kullanıcı
    mesajı, model hiç cevap vermedi (kota/arka uç). Özet yoksa cevap var sayılır (parse karar verir)."""
    import re as _re
    m = _re.search(r"Messages:\s*(\d+)", stdout or "")
    return bool(m and int(m.group(1)) <= 1)


def _agent_tool_calls(stdout: str) -> int:
    """CLI özetinden araç-çağrı sayısını çıkar ('Messages: N (M user, K tool calls)'). MCP araçlarını
    ajanın gerçekten KULLANIP kullanmadığını ölçmek için — sıfır ise MCP yatırımı atıl demektir.
    Özet yoksa/eşleşmezse -1 (bilinmiyor)."""
    import re as _re
    m = _re.search(r"(\d+)\s+tool calls?", stdout or "")
    return int(m.group(1)) if m else -1


# ---- YAPILANDIRMASIZ CLI İMZALARI ---------------------------
# İMZALAR ÖLÇÜLDÜ, TAHMİN EDİLMEDİ — kurulu hermes-agent kaynağından okundu (2026-08-02):
#   hermes_cli/main.py `cmd_chat`: ilk-koşum bekçisi `_has_any_provider_configured()` False iken
#   STDOUT'a "It looks like Hermes isn't configured yet ..." basar, TTY yoksa
#   hermes_cli/setup.py `print_noninteractive_setup_guidance` rehberini ekler
#   ("hermes config set model.default your-model-name" · "Or set OPENROUTER_API_KEY / OPENAI_API_KEY
#   in your environment") ve `sys.exit(1)` eder. Yani süreç AĞA HİÇ ÇIKMAZ: ne sağlayıcıya istek
#   gider, ne kota harcanır, ne de 429 alınır.
# NEDEN AYRI SINIF: bu çıktı `_agent_reply_missing`/rc!=0 kapısından "boş cevap" olarak geçiyordu
# ve `agent_call_empty` → `_pool_exhausted` → `brain_stand_down("agent")` zincirini besliyordu.
# Yapılandırmasızlık KOTA DEĞİLDİR; 429-backoff'unu onunla kirletmek iki arızayı tek satırda
# birleştirir ve altı gün süren sessiz ölümün teşhisini imkânsız kılar (canlı vaka).
AGENT_UNCONFIGURED_SIGNS = (
    "config set model.default",      # rehberin config kolu
    "OPENROUTER_API_KEY",            # rehberin env-değişkeni kolu
    "isn't configured yet",          # ilk-koşum bekçisinin kendi cümlesi (rehber metni değişse de kalır)
)


def _agent_unconfigured_sign(stdout: str, stderr: str) -> str | None:
    """Çıktıda yapılandırma-hatası imzası var mı? Varsa EŞLEŞEN imza, yoksa None.

    YALNIZ BOŞ-CEVAP YOLUNDA çağrılır: dolu bir modelin cevabında bu dizeler geçebilir (ajan
    yapılandırmadan söz edebilir) ve o hâlde arıza yoktur. Sınıflandırmayı cevabın VARLIĞINDAN
    bağımsız yapmak, konuşan bir modeli 'yapılandırmasız' ilan ederdi."""
    hay = f"{stdout or ''}\n{stderr or ''}"
    for sign in AGENT_UNCONFIGURED_SIGNS:
        if sign in hay:
            return sign
    return None


# ---- KOTA İMZALARI ------------------------------------------------------------
# `_rate_limited` bir İSTİSNA sınıflandırır (httpx yolu); yerel ajan yolunda istisna YOKTUR — elde
# yalnız bir süreç çıktısı vardır. Boş bir cevabın "kota bitti" mi yoksa "model sustu" mu olduğunu
# ayıran tek DOĞRUDAN kanıt bu çıktıdaki imzadır. İkisini ayırmamak, susan bir modelin cezasını
# kota cezası merdivenine bindiriyordu (canlı: `agent_call_empty ... cooldown_s=21600`).
AGENT_QUOTA_SIGNS = ("too many requests", "resource_exhausted", "insufficient_quota",
                     "quota", "rate limit", "rate_limit")


def _agent_quota_sign(stdout: str, stderr: str) -> str | None:
    """Boş cevabın gövdesinde GERÇEK kota/oran-sınırı imzası var mı? Varsa imza, yoksa None.

    `_agent_unconfigured_sign` ile aynı disiplin: YALNIZ boş-cevap yolunda çağrılır. Dolu bir
    cevabın metni 'quota' kelimesini geçirebilir ve orada hiçbir arıza yoktur. 429/529 sayısı
    KELİME SINIRIYLA aranır — oturum özetindeki bir süre/jeton sayısının içine gömülü '429'
    kota sanılırsa, sınıflandırma tam da düzeltmeye çalıştığı hatayı üretirdi."""
    import re as _re
    hay = f"{stdout or ''}\n{stderr or ''}".lower()
    for sign in AGENT_QUOTA_SIGNS:
        if sign in hay:
            return sign
    m = _re.search(r"\b(429|529)\b", hay)
    return m.group(1) if m else None


# ---- HAM ÇIKTI ÖZETİ — KÖRLÜĞÜN SONU ------------------------------------------
# CANLI VAKA: `agent_call kind=review model=gemini-3.5-flash attempt=1 empty=true tool_calls=-1`
# → yedek de boş → `review_fallback_empty`. Defterde bu üç satırdan BAŞKA hiçbir şey yoktu ve
# üçü de aynı şeyi söylüyordu: "boş". `-Q` altında `tool_calls=-1` YAPISALDIR (sessiz mod oturum
# özetini bastırır), yani "empty" kararı fiilen `returncode != 0 or not stdout.strip()`e iner —
# ve bu iki olgunun HİÇBİRİ deftere yazılmıyordu. Süreç ne dedi, hangi kodla öldü, stderr ne
# taşıdı: hepsi yutuluyordu. Sınıflandırıcılar (`_agent_unconfigured_sign`, `_agent_quota_sign`)
# çıktıyı OKUYOR ama SAKLAMIYORdu — yani hiçbir imzaya uymayan bir arıza sonsuza dek görünmezdi.
# BU YÜZDEN ÖZET SIR SIZDIRMAZ: alt sürecin ortamında `MERIDIAN_DASH_TOKEN`/`GEMINI_API_KEY`
# yaşıyor (birim `EnvironmentFile` + devralınan ortam) ve bir CLI hata mesajı bunları yankılayabilir.
# Defter git-izsizdir ama panodan okunur; maskeleme DESENLE yapılır, gerçek sır değerleri OKUNMADAN
# (sır okumak için `secrets.get` çağırmak, sızıntı yüzeyini teşhis uğruna genişletmek olurdu).
#
# GÖVDE TAŞINDI: desenler ve uygulama artık `agent_telemetry`de yaşıyor,
# çünkü HAM İZ DEFTERİ de aynı maskelemeyi ister ve İKİNCİ BİR UYGULAMA YASAKTIR — iki kopya
# sessizce ayrışır, ayrışan taraf sızdırır. Bu ad ve imza KORUNDU: eski sözleşme (`_ham_ozet`
# 200 karakterde beyanlı kırpar, maskeleme kırpmadan ÖNCE koşar) buradan sınanıyor ve `_agent_call`
# ile `agent_skill_preload_unknown` yolları bu adı çağırıyor.


def _ham_ozet(metin: str | None, limit: int = 200) -> str:
    """Alt süreç çıktısının DEFTERE YAZILABİLİR özeti — gövde: `agent_telemetry.maskele`.

    ANSI sökülür, satır sonları görünür tek karaktere katlanır (tek satırlık olay alanı), sır
    DESENLERİ maskelenir, sonra kırpılır. SIRA ÖNEMLİ (maskeleme kırpmadan ÖNCE): önce kırpsaydık
    200. karakterde ikiye bölünen bir anahtarın ilk yarısı maskesiz kalırdı — yarım sır da sırdır."""
    return _at.maskele(metin, limit)


# ---- YEREL ÖN-UÇUŞ HATASI: BİLİNMEYEN SKILL -----------------------------------
# ÖLÇÜLDÜ, TAHMİN EDİLMEDİ (yerel kurulum v0.18.2, 2026-08-06):
#   `hermes chat --accept-hooks -Q -q "say hi" -s yok-boyle-bir-skill --model gemini-3.5-flash`
#   → rc=1 · stdout="Error: Unknown skill(s): yok-boyle-bir-skill" · süre 0,9 sn · AĞA ÇIKMAZ.
# Aynı koşumda GEÇERSİZ bir model adı (`--model gemini-9.9-yok-boyle-model`) rc=0 + DOLU cevap
# üretti: CLI bilinmeyen modeli sessizce varsayılana düşürüyor. Yani canlı `empty=true` imzasının
# kaynağı model adı OLAMAZ — ön-uçuş argüman hatası olabilir ve imzası birebir uyuyor:
#   * rc!=0 → `empty=True` (stdout dolu olsa bile: "Error:" satırı cevap değildir),
#   * `-Q` yüzünden oturum özeti yok → `tool_calls=-1`,
#   * hata MODELDEN ÖNCE olduğu için zincirin İKİNCİ modeli de aynen düşer → `review_fallback_empty`,
#   * çıktıda ne kota ne yapılandırma imzası var → eski kod hiçbir sınıfa koyamayıp "kota/arka uç" derdi.
# BU KOTA DEĞİLDİR ve MODEL SUSMASI DA DEĞİLDİR: yerel bir liste bayatlamıştır (ajan küratörü
# linkleri silebiliyor — bkz. `sync_agent_skills`). Ceza değil ONARIM ister.
AGENT_UNKNOWN_SKILL_RE = r"[Uu]nknown skill\(s\):\s*([^\n\r]+)"


def _agent_unknown_skills(stdout: str, stderr: str) -> list:
    """Çıktı "bu skill'leri tanımıyorum" mu dedi? Dönüş: ADLAR (yoksa boş liste).

    Ad listesi ÇIKTIDAN okunur, tahmin edilmez: hangi adın düştüğünü bilmeden ön-yükleme listesini
    komple boşaltmak, çalışan skill'leri de cezalandırıp ajanı bilgisiz bırakırdı."""
    import re as _re
    m = _re.search(AGENT_UNKNOWN_SKILL_RE, f"{stdout or ''}\n{stderr or ''}")
    if not m:
        return []
    ham = m.group(1).strip().rstrip(".")
    return [p.strip() for p in ham.replace(";", ",").split(",") if p.strip()]


# ---- CLI SESSİZ MODU (`-Q`) — SÜRÜM DERSİ --------------------------------------------
# KÖK NEDEN (canlı vaka): `-q` SESSİZLİK DEĞİL, SORGU bayrağıdır (`-q QUERY, --query QUERY`) —
# sessiz mod AYRI bir bayraktır: `-Q, --quiet` ("suppress banner, spinner, and tool previews. Only
# output the final ..."). ÖLÇÜLDÜ: yerel kurulum v0.18.2, A1 v0.19.0 — ikisinde de ayrım aynı.
# `-Q` olmadan stdout'a banner + "Query: <istemin yankısı>" + oturum özeti karışıyor ve
# `_extract_json` YANKININ İÇİNDEKİ bağlam-JSON'unu yakalıyordu: `candidate_review_empty_parse`
# olayı canlıda tam bunu yazdı (parse_ok=true · on_filtre_n=0 · ham_ilk="Query: You advise...").
# Yani model dolu ve doğru cevap verirken kayıt boş çıkıyordu — arıza modelde değil, komut satırında.
QUIET_FLAG = "-Q"
# argparse/click "bilinmeyen bayrak" imzaları (ÖLÇÜLDÜ: `hermes chat -Z` → stderr
# "hermes: error: unrecognized arguments: -Z", rc=2 — main() hiç koşmaz, ağa çıkılmaz).
CLI_UNKNOWN_FLAG_SIGNS = ("unrecognized arguments", "no such option", "Unknown option")
_quiet_flag_ok = True          # süreç-içi öğrenme: bir kez 'desteklenmiyor' denince tekrar denenmez

# ==================================================================================================
# SAĞLAYICI YÖNLENDİRMESİ — `--model` DOĞRUYDU, İSTEK YANLIŞ UCA GİDİYORDU
# --------------------------------------------------------------------------------------------------
# ÖLÇÜLEN ARIZA (canlı, 24 saat): `_agent_chat_cmd` CLI'ya YALNIZ `--model` geçiyordu; yerel hermes
# CLI'nın kendi yapılandırması `model.provider: gemini` olduğu için bir OpenRouter slug'ı
# (`nvidia/...:free`) GEMINI ucuna gidip `HTTP 404` alıyordu. 33 çağrının 33'ü boş, ~354 sn israf,
# tüm ajan çağrılarının %46'sı. Kanıt: docs/TESHIS-BEYIN-ZINCIRI-ERISILEMEZ-MODEL-2026-08-13.md.
#
# NEDEN `config set model.provider auto` DEĞİL: ucuz yol DENENDİ ve ÇÜRÜDÜ (2026-08-13 21:12Z,
# canlı) — `auto` slug'a göre yönlendirmiyor, hiçbir kimliğe bağlanamıyor ve auth başlığı hiç
# göndermiyor: hem tencent hem `gemini-flash-latest` 401 verdi, yani ÇALIŞAN ayak da düştü. Geri
# alındı. Kural bu turda kodda yaşar, CLI yapılandırmasında DEĞİL: `model.provider: gemini`
# yapılandırmada AYNEN kalır ve slug taşımayan adlar (`gemini-flash-latest`) bugünkü davranışını
# BİT BİT korur — bayrak eklenmez, CLI kendi varsayılanına gider.
#
# NEDEN KİMLİK ŞARTI VAR: kimlik yokken slug'a `--provider openrouter` eklemek 404'ü "Provider
# resolver returned an empty API key" hatasına ÇEVİRİR — daha iyi değil, yalnız BAŞKA bir arıza.
# (ÖLÇÜLDÜ: bayrak CLI'da VAR ve tanınıyor; anahtarsız çağrıda tam bu cümleyi basıyor.)
#
# KİMLİK YÜZEYİ — HANGİSİ SSoT (bu turun asıl kararı):
#   Soru "Meridian'ın bir anahtarı var mı" DEĞİL, "ALT SÜREÇ olarak koşan CLI bir anahtar
#   GÖREBİLİYOR mu"dur. CLI'nın gördüğü iki yüzey vardır ve yalnız ikisi:
#     (1) süreç ortamı — `_agent_call._kos` alt süreci `env={**os.environ, ...}` ile doğurur,
#     (2) `~/.hermes/.env` — CLI'nın KENDİ kimlik dosyası (Gemini ayağı da bu dosyadan besleniyor;
#         `_agent_env_has_key` aynı dosyayı zaten bu amaçla okuyor).
#   `secrets.get("OPENROUTER_API_KEY")` BİLEREK KULLANILMADI: `secrets` zinciri env'den SONRA
#   `state/secrets.json` ve GCP Secret Manager'a bakar ve o iki kaynak alt sürece HİÇ GEÇMEZ —
#   yani kasada anahtar varken `secrets.get` True derdi, CLI ise anahtarsız kalırdı. Bu tam olarak
#   bu turun kapattığı sınıftır ("ayar yapıldı sanılıyor, ulaşılamıyor"): yanlış yüzeye bakan bir
#   kapı, arızayı düzeltmek yerine ADINI değiştirirdi. Env kolu zaten kapsanıyor — `secrets.get`in
#   BİRİNCİ kaynağı da os.environ'dır, biz doğrudan oraya bakınca aynı vakayı doğru gerekçeyle
#   yakalarız.
#   `secrets.ALLOWED` KONTROL EDİLDİ: `OPENROUTER_API_KEY` listede YOK ve bu turda EKLENMEDİ —
#   eklemek panodan `state/secrets.json`a yazmayı açardı, ama o dosya CLI'ya görünmez: operatör
#   anahtarı girer, ✓ görür ve çağrı yine düşerdi. Anahtarın gideceği yer `~/.hermes/.env`tir
#   (kurulum belgesi Adım 1b) ve oraya YAZMAK bu brief'in kapsamı dışındadır (sır yazma yolu).
#
# SAĞLAYICI ADI SABİTTE: ikinci beyin başka bir toplayıcıya taşınırsa tek satır değişir.
AGENT_SLUG_PROVIDER = "openrouter"
# CLI'nin o sağlayıcı için okuduğu env/`.env` anahtar adı (ÖLÇÜLDÜ: CLI'nin yapılandırmasız
# rehberi bu adı söylüyor — `AGENT_UNCONFIGURED_SIGNS` içinde de aynı ad geçiyor).
AGENT_SLUG_PROVIDER_ENV = "OPENROUTER_API_KEY"


def _agent_slug_provider_ready() -> bool:
    """Alt süreç olarak koşacak CLI, OpenRouter kimliğini GÖREBİLİYOR mu? (değer ASLA okunmaz/dönmez)

    İki yüzey, ikisi de CLI'nin gerçekten okuduğu yerler: süreç ortamı (alt sürece miras kalır) ve
    `~/.hermes/.env`. Gerekçesi yukarıdaki blokta; kısaca: Meridian'ın kasası CLI'ya görünmez, o
    yüzden `secrets.get` burada YANLIŞ CEVAP verirdi."""
    if (os.environ.get(AGENT_SLUG_PROVIDER_ENV) or "").strip():
        return True
    # None = dosya VAR ama okunamadı → "kimlik yok" SAYILIR (yönlendirme eklenmez). Ölçülemeyen bir
    # kimliğe dayanıp bayrak eklemek, çalışan 404 yolunu okunamayan bir hataya çevirebilirdi;
    # güvenli taraf bugünkü davranışı korumaktır.
    return _agent_env_has((AGENT_SLUG_PROVIDER_ENV,)) is True


def _agent_provider_for(model: str | None) -> str | None:
    """Bu model kimliği için CLI'ya geçilecek `--provider` (yoksa None = bayrak EKLENMEZ).

    Kural: kimlik SLASH içeriyorsa OpenRouter slug biçimidir (`saglayici/model[:etiket]`);
    çıplak adlar (`gemini-flash-latest`) CLI'nin kendi varsayılanına bırakılır."""
    if not model or "/" not in model:
        return None
    if not _agent_slug_provider_ready():
        return None
    return AGENT_SLUG_PROVIDER


def _agent_chat_cmd(bin_: str, prompt: str, preload: tuple, model: str | None) -> list:
    """CLI `chat` komutunun TEK KURULUM YERİ. İki bayrak iki AYRI iş yapar ve karıştırılırsa arıza
    sessizdir: `-q` istemi taşır, `-Q` çıktıyı yalnız son cevaba indirger.

    SAF KALIR — olay BASMAZ, dosya YAZMAZ: bu kurucu üç ayrı yerden (ilk deneme + iki onarım
    yeniden-koşumu) çağrılıyor ve buradan olay basmak tek bir çağrıyı deftere üç kez yazardı."""
    cmd = [bin_, "chat", "--accept-hooks"]
    if _quiet_flag_ok:
        cmd.append(QUIET_FLAG)
    cmd += ["-q", prompt]
    for sk in preload:
        cmd += ["-s", sk]
    if model:
        cmd += ["--model", model]
        prov = _agent_provider_for(model)
        if prov:
            cmd += ["--provider", prov]
    return cmd


def _cli_unknown_flag(out) -> bool:
    """Süreç 'bu bayrağı tanımıyorum' mu dedi? (yalnız sıfır-dışı çıkışta anlamlı)."""
    if out.returncode == 0:
        return False
    t = f"{out.stdout or ''}\n{out.stderr or ''}"
    return any(s in t for s in CLI_UNKNOWN_FLAG_SIGNS) and QUIET_FLAG in t


def _quiet_flag_unsupported_warn(out) -> None:
    """`-Q` desteklenmiyor: SÜREÇ BAŞINA BİR uyarı + kalıcı geri düşüş. Sessiz düşmek yasak —
    `-Q`suz çıktı yankı taşır ve ayrıştırıcı yanlış JSON yakalayabilir; operatör bunu bilmeli."""
    global _quiet_flag_ok
    if _quiet_flag_ok:
        _quiet_flag_ok = False
        obs.warn("agent_cli_flag_unsupported", flag=QUIET_FLAG, returncode=out.returncode,
                 stderr_ilk=str(out.stderr or out.stdout or "")[:160].replace("\n", " ⏎ "),
                 detail=f"yerel CLI {QUIET_FLAG} (sessiz mod) bayrağını tanımadı — bu çağrı ve "
                        f"sonrakiler bayraksız koşuyor. RİSK: banner/istem yankısı stdout'a karışır "
                        f"ve JSON ayrıştırıcı yankıdaki bloğu yakalayabilir (2026-08-02 canlı vakası). "
                        f"Kalıcı çözüm: hermes-agent'ı -Q destekleyen sürüme yükselt.")


# ==================================================================================================
# KÜNYE "İSTENEN"İ DEĞİL "CEVAP VEREN"İ TAŞIR (canlı ölçüm 2026-08-13)
# --------------------------------------------------------------------------------------------------
# ÖLÇÜLEN ARIZA (canlı A1, 2026-08-13 — olay defterinden birebir):
#     20:37:26  agent_call kind=review model=tencent/hy3:free      attempt=1 empty=True  rc=1
#     20:37:31  agent_call kind=review model=gemini-flash-latest   attempt=2 empty=False rc=0
#     20:37:32  candidate_review.json yazıldı → "model": "tencent/hy3:free"
# Görüşü İKİNCİ model yazdı, künye BİRİNCİYİ söylüyordu. Sebep `review_candidates`in `active_model()`
# çağırmasıydı: o fonksiyon YAPILANDIRMAYI okur (`NOUS_MODEL` sırrı), zincirin hangi ayağının
# GERÇEKTEN konuştuğunu değil. BEDELİ ÖLÇÜLDÜ: tencent 56 çağrının 56'sında boş döndü ama pano
# haftalarca `TENCENT/HY3:FREE` yazdı — hatalı künye arızayı GİZLEDİ. Künye doğru olsaydı başlıkta
# `gemini-flash-latest` görünür, ayrışma ilk gün fark edilirdi.
#
# NEDEN YAN KANAL, DÖNÜŞ TÜRÜ DEĞİL: `_agent_call`in bugünkü dönüşü `str | None` ve altı üretim
# çağıranı var (`_propose_nous_local`, `review_candidates`, `rank_explore`, `_review_plans_batch`,
# `chain_text`, `skill_evolve.propose_skill_revision`) + ~30 test iddiası; hepsi metni doğrudan
# kullanıyor. Dönüşü tuple'a çevirmek altısını birden kırardı; bu turun kapsamı KÜNYE, taşıma
# sözleşmesi değil.
#
# NEDEN threading.local: emsali bu modülde ZATEN VAR (`_BRAIN_TRACE`/`_trace_note`) ve gerekçesi
# aynen geçerli — arka plan dolgu kolu ile inceleme kolu AYNI ANDA `_agent_call` koşabilir
# (hermes_runtime sondası + asenkron backfill iş parçacığı); modül düzeyinde tek kutu birinin
# künyesini ötekine yazardı. EŞZAMANLILIK VARSAYIMI AÇIK BEYAN: okuyucu, çağrıyı YAPAN iş
# parçacığının kendisidir (bugün öyle — `review_candidates` çağrıyı ve okumayı aynı gövdede yapar).
# Başka bir iş parçacığından okumak ÖLÇÜLEMEDİ döndürür; uydurma değil, dürüst boşluk.
#
# TÜKETEN OKUMA (`_trace_take` emsali): okuyunca kutu boşalır — ikinci bir okuyucu bayat bir künyeyi
# taze sanamaz. Bir sonraki `_agent_call` girişte kutuyu zaten temizler (erken dönüşler dahil).
# ==================================================================================================
AGENT_MODEL_YOK_KAYIT = ("cevap veren model ÖLÇÜLEMEDİ: bu iş parçacığında tamamlanmış bir ajan "
                         "çağrısı kaydı yok (çağrı hiç yapılmadı, cevapsız döndü ya da künye başka "
                         "bir iş parçacığında kaldı)")
AGENT_MODEL_YOK_ZINCIR = ("cevap veren model ÖLÇÜLEMEDİ: model zinciri adsızdı (NOUS_MODEL / "
                          "NOUS_FALLBACK_MODEL sırrı yok) — CLI kendi varsayılanına gitti ve o adı "
                          "bize bildirmiyor")
_AGENT_SON_MODEL = threading.local()


def _agent_model_sifirla() -> None:
    """Kutuyu boşalt — HER `_agent_call` girişinde, erken dönüşlerden ÖNCE."""
    _AGENT_SON_MODEL.model, _AGENT_SON_MODEL.neden = None, AGENT_MODEL_YOK_KAYIT
    _AGENT_SON_MODEL.iz_id = None


def _agent_model_kaydet(model: str | None) -> None:
    """Dolu cevabı GERÇEKTEN veren denemenin model adı (`None` = zincir adsızdı → CLI varsayılanı)."""
    _AGENT_SON_MODEL.model = model or None
    _AGENT_SON_MODEL.neden = None if model else AGENT_MODEL_YOK_ZINCIR


def _agent_iz_kaydet(iz_id: str | None) -> None:
    """Cevabı veren denemenin TELEMETRİ anahtarı (`agent_calls.jsonl` → `iz_id`) — Ö-39 atıf join'i.

    AYRI YAZICI, BİLİNÇLİ: ad `models` döngü değişkeninden, anahtar telemetri YAZIMININ dönüşünden
    gelir; iki farklı olgu tek çağrıya katlansaydı `_agent_model_kaydet(model)` çağrısının metni
    değişir ve o metni donduran ölçüm çivisi (`test_ogrenme_hafiza_kunye_v245::test_c1`) yan
    kanalın kendi ölçümünü kaybederdi. Ad tek başına "HANGİ çağrı" sorusunu cevaplamaz — aynı
    model gün içinde onlarca kez konuşur; bir atıf satırından ham izine (süre, deneme,
    ön-yükleme, stdout) ancak bu anahtarla inilir. Telemetri yazımı düşerse None kalır ve
    UYDURULMAZ: sahte bir anahtar, var olmayan bir satıra işaret eden ÖLÜ bir join olurdu."""
    _AGENT_SON_MODEL.iz_id = iz_id or None


def cevap_veren_model() -> tuple[str | None, str | None]:
    """SON `_agent_call`in cevabını veren model → `(model, ölçülemedi_nedeni)`; biri hep None'dır.

    UYDURMA YASAĞI: ölçülemezse `(None, neden)` döner — `active_model()`e (yapılandırma) SESSİZCE
    düşmez. Okuma TÜKETİR (bkz. üstteki blok)."""
    m = getattr(_AGENT_SON_MODEL, "model", None)
    n = getattr(_AGENT_SON_MODEL, "neden", AGENT_MODEL_YOK_KAYIT)
    _AGENT_SON_MODEL.model, _AGENT_SON_MODEL.neden = None, AGENT_MODEL_YOK_KAYIT
    return (m, None) if m else (None, n or AGENT_MODEL_YOK_KAYIT)


def cevap_veren_iz() -> str | None:
    """SON `_agent_call`in telemetri anahtarı (`agent_calls.jsonl` → `iz_id`); yoksa None.

    AYRI OKUYUCU, AYNI KUTU: `cevap_veren_model()` künyeyi tüketir ama `iz_id`ye dokunmaz —
    ikisi tek dönüşte katlansaydı bugünkü altı çağıranın hepsinin sözleşmesi değişirdi (aynı
    gerekçeyle yan kanal seçilmişti). Okuma yine TÜKETİR ve kutu her `_agent_call` girişinde
    zaten sıfırlanır, yani bayat bir anahtar taze sanılamaz."""
    i = getattr(_AGENT_SON_MODEL, "iz_id", None)
    _AGENT_SON_MODEL.iz_id = None
    return i or None


def _agent_call(prompt: str, preload: tuple = (), kind: str = "generic",
                timeout: int = 300, max_wait: float = 0.0) -> str | None:
    """TÜM yerel-ajan çağrılarının tek kapısı: skill senkronu + -s ön-yükleme + oran bütçesi +
    model düşüş zinciri (NOUS_MODEL → NOUS_FALLBACK_MODEL; boş oturumda bir kez düşer). None = çağrı
    yapılamadı/cevapsız — çağıran fail-open davranır. Ham stdout döner; parse çağıranın işi.

    TELEMETRİ: KOŞAN HER ALT SÜREÇ ölçülür ve `agent_calls.jsonl`e bir
    satır düşer — süre, deneme no, alt-koşum no (onarım yeniden-koşumları), model, araç sayısı,
    çıktı boyutu, sonuç sınıfı. Süre ÖLÇÜM ANINDA yazılır: iki olay damgasının farkı çağrının
    süresi DEĞİLDİR (arada bütçe bekleyişi, skill senkronu ve süreç doğuşu vardır). Aynı koşumun
    tam stdout+stderr'ı sır-maskeli olarak `agent_traces.jsonl`e iner (modül 2) ve iki defter
    `iz_id` ile birleşir.

    ÇAĞRI YAPILMADAN dönülen üç yol (ikili yok · soğuma · bütçe reddi) deftere YAZILMAZ ve bu
    bilinçlidir: süresi olmayan bir şeyin "çağrı süresi" satırı, ortalamayı sessizce aşağı çeker.
    O üç hâl zaten kendi olaylarını basıyor (`agent_call_cooldown`, `agent_budget_denied`).

    KÜNYE YAN KANALI: dolu cevabı veren denemenin model adı `cevap_veren_model()` ile okunur (dönüş
    türü DEĞİŞMEDİ). Kutu burada, HER erken dönüşten önce sıfırlanır — önceki bir çağrının künyesi
    bu çağrının cevabı sanılamaz."""
    import subprocess
    _agent_model_sifirla()
    bin_ = _hermes_bin()
    if not bin_:
        return None
    rem = brain_cooldown("agent")
    if rem > 0 and _pool_window_renewed():
        # KOTA PENCERESİ YENİLENDİ: elimizdeki soğuma DÜNKÜ havuz tükenmesinden
        # kuruldu ve o işaret sağlayıcının son günlük sıfırlamasından ÖNCEYE ait — yani BUGÜNÜN
        # kotası hakkında hiçbir şey söylemiyor. Canlıda görülen sonuç: taze kota penceresi hiç
        # denenmeden yedek modele düşülüyor, yedek susunca 6 saat daha kilitleniyordu. İşaret
        # temizlenir ve birinci GERÇEKTEN yoklanır; yoklama başarısızsa zincirin sonundaki
        # sınıflandırma işareti yeniden kurar (mevcut davranış).
        brain_recovered("agent")
        obs.log("agent_pool_window_reset", kind=kind, iptal_edilen_soguma_s=round(rem, 1),
                reset_utc_hour=POOL_QUOTA_RESET_UTC_HOUR,
                detail="havuz-tükenme işareti son günlük kota sıfırlamasından ESKİ — soğuma "
                       "kaldırıldı, birinci model gerçekten yoklanıyor")
        rem = 0.0
    if rem > 0:
        # Ajanın kimlik havuzu 429 yemişti ve bunu KENDİ kaydında yazıyordu; yine de her turda yeni bir
        # süreç başlatılıyordu. Süreç başlatmadan dön: bilinen-ölü sağlayıcıyı dövmek kotayı geri getirmez.
        obs.log("agent_call_cooldown", kind=kind, remaining_s=round(rem, 1),
                detail="kimlik havuzu tükenmiş — dinlenme penceresi; deterministik yol devrede")
        return None
    try:
        sync_agent_skills()
    except Exception:  # sessiz-yutma: yardımcı/telemetri yolu; başarısızlığı karara girmez ve çağıran yedek değerle aynen devam eder
        pass
    # ÇAĞRI ANI ÖLÜ-AD KONTROLÜ (2026-08-13): zincir SIRLARDAN kurulur ve göç yalnız ajan
    # config'ini kapsıyordu — sırdaki ölü ad her çağrıda 404 üretiyordu (canlı: 20/20 `agent_call`
    # `model=gemini-3.5-flash`). Bkz. `_nous_model_zinciri` üstündeki ölçüm/gerekçe.
    models = _nous_model_zinciri()
    son_stdout = son_stderr = ""      # zincirin SON denemesinin ham çıktısı — boş-sınıfı tailde ayrılır
    son_rc: int | None = None         # ve ÇIKIŞ KODU: `-Q` altında boşluk ölçütünün yarısı budur

    def _kos(cmd_, *, deneme: int, alt: int):
        """Alt süreci KOŞ ve SÜRESİNİ ölç. Dönüş: (CompletedProcess, süre_ms).

        ZAMAN AŞIMI DA BİR ÖLÇÜMDÜR: `subprocess.run(timeout=…)` `TimeoutExpired` fırlatır ve bu
        istisna bugüne dek defterde HİÇ görünmüyordu (çağıranlar onu yukarıda yutuyor). Takılan
        çağrı tam da C2-1'in cevaplamak istediği soruydu — satır yazılır, sonra istisna AYNEN
        yukarı gider (davranış değişmez)."""
        kr = _at.Kronometre()
        with kr:
            try:
                out_ = subprocess.run(cmd_, capture_output=True, text=True, timeout=timeout,
                                      env={**os.environ, "NO_COLOR": "1", "TERM": "dumb"})
            except subprocess.TimeoutExpired as e:
                _at.kaydet(kind=kind, model=model, deneme=deneme, alt=alt, sure_ms=kr.dur(),
                           sonuc_sinifi=_at.SINIF_ZAMAN_ASIMI, returncode=None,
                           arac_cagri_n=None, on_yukleme_n=len(preload),
                           on_yukleme=list(preload), istem=prompt,
                           stdout=(e.stdout if isinstance(e.stdout, str) else None),
                           stderr=(e.stderr if isinstance(e.stderr, str) else None),
                           zaman_asimi_s=timeout)
                raise
        return out_, kr.ms

    def _telemetri(out_, sure_ms: float, *, deneme: int, alt: int, sinif: str) -> dict | None:
        """Bir koşumun telemetri + ham iz satırlarını yaz (sınıf ÇAĞIRANDA bilinir).

        DÖNÜŞ: yazılan telemetri satırı (ya da yazım düşerse None) — `iz_id` oradan alınır ve
        künye kutusuna konur (Ö-39 atıf defterinin `agent_calls.jsonl` join anahtarı). Anahtarı
        burada YENİDEN ÜRETMEK yerine yazılan satırdan okumak bilinçlidir: `iz_kimligi` ts/kind/
        deneme/alt'tan türer ve ikinci bir türetim, damga biçimi bir gün değişirse sessizce
        ayrışan İKİNCİ bir anahtar üretirdi."""
        tc = _agent_tool_calls(out_.stdout)
        return _at.kaydet(
            kind=kind, model=model, deneme=deneme, alt=alt, sure_ms=sure_ms,
            sonuc_sinifi=sinif, returncode=out_.returncode,
            # -1 = ÖLÇÜLEMEDİ (`-Q` özeti bastırır) → deftere None yazılır, 0 DEĞİL.
            arac_cagri_n=(tc if tc >= 0 else None),
            # ADLAR DA YAZILIR (2026-08-13 — GERİLEME ONARIMI): `on_yukleme_n` tek
            # başına "kaç skill" der, "hangileri" demez. Onarımın tam gerekçesi ve hacim
            # ölçümü `agent_telemetry.skill_adlari` üstündeki blokta. `preload` bu kapanışta
            # GEÇ okunur ve bu bilinçlidir: ön-uçuş onarımı (`Unknown skill(s)`) listeyi
            # KÜÇÜLTEBİLİR ve deftere gerçekten GÖNDERİLEN liste yazılmalıdır, istenen değil.
            on_yukleme_n=len(preload), on_yukleme=list(preload), istem=prompt,
            stdout=out_.stdout, stderr=out_.stderr)

    for attempt, model in enumerate(models):
        if not _agent_budget_take(max_wait if attempt == 0 else 0.0):
            return None
        alt = 0                       # onarım yeniden-koşumlarının sayacı (aynı deneme içinde)
        # --accept-hooks: config'teki hooks_auto_accept ile birlikte koruma hook'unu başsız çağrıda
        # otomatik onaylar (aksi halde 'not allowlisted' → hook ateşlemez, savunma sessizce ölürdü).
        cmd = _agent_chat_cmd(bin_, prompt, preload, model)
        out, sure_ms = _kos(cmd, deneme=attempt + 1, alt=alt)
        if QUIET_FLAG in cmd and _cli_unknown_flag(out):
            # GERİYE-UYUM (tek atımlık): `-Q` tanımayan bir CLI sürümü. Bayrak hatası AĞA ÇIKMAZ
            # (argparse `main()`den önce düşer) → (d) gereği bütçe iade edilir ve düşüm yeniden alınır.
            _telemetri(out, sure_ms, deneme=attempt + 1, alt=alt, sinif=_at.SINIF_CLI_BAYRAK)
            _agent_budget_refund("cli_flag_unsupported")
            _quiet_flag_unsupported_warn(out)
            if not _agent_budget_take(0.0):
                return None
            alt += 1
            cmd = _agent_chat_cmd(bin_, prompt, preload, model)     # artık `-Q`suz (bayrak öğrenildi)
            out, sure_ms = _kos(cmd, deneme=attempt + 1, alt=alt)
        # BOŞLUK ÖLÇÜTÜ `-Q` İLE GENİŞLEDİ (ölçüldü, cli.py tek-sorgu sessiz kolu): sessiz modda
        # stdout YALNIZ son cevabı taşır — ne banner, ne "Messages: N" özeti. Yani
        # `_agent_reply_missing` sinyalini kaybeder ve cevapsız bir koşum (rc=0 + boş stdout,
        # hata stderr'e gider) "dolu cevap" gibi geri dönerdi: ayrıştırıcı boş metinle uğraşır,
        # defterde `agent_call_empty` HİÇ yazmazdı. Boş stdout artık ölçütün parçası.
        empty = (out.returncode != 0 or not (out.stdout or "").strip()
                 or _agent_reply_missing(out.stdout))
        # ÖN-UÇUŞ ARGÜMAN HATASI ONARILIR, CEZALANDIRILMAZ. Ölçülmüş imza: rc=1 + stdout
        # "Error: Unknown skill(s): X" + 0,9 sn + AĞA ÇIKMAMA. Zincirin ikinci modeli aynı listeyle
        # aynen düşerdi (hata modelden ÖNCE), yani bu satır olmadan tek bayat symlink hattı komple
        # susturuyordu. Onarım: DÜŞEN adlar çıktıdan okunur, ön-yükleme listesinden çıkarılır ve
        # çağrı BİR KEZ yeniden koşulur — bütçe iade edilerek, çünkü çağrı sağlayıcıya hiç gitmedi.
        if empty and preload:
            eksik = _agent_unknown_skills(out.stdout, out.stderr)
            kalan = tuple(s for s in preload if s not in set(eksik))
            if eksik and len(kalan) < len(preload):
                _telemetri(out, sure_ms, deneme=attempt + 1, alt=alt,
                           sinif=_at.SINIF_ON_UCUS_SKILL)
                iade = _agent_budget_refund(f"agent_skill_unknown:{kind}")
                obs.warn("agent_skill_preload_unknown", kind=kind, eksik=list(eksik)[:12],
                         n_eksik=len(eksik), n_kalan=len(kalan), attempt=attempt + 1,
                         model=model or "varsayılan", returncode=out.returncode,
                         butce_iade=iade, ham_stdout=_ham_ozet(out.stdout),
                         detail=f"yerel CLI ön-yüklenen skill(ler)i tanımadı ({', '.join(eksik[:5])}) — "
                                f"çağrı AĞA ÇIKMADI, bu kota DEĞİLDİR (soğuma yazılmaz, RPD iade "
                                f"edilir). Düşen adlar listeden çıkarılıp çağrı bir kez yeniden "
                                f"koşuluyor. KALICI ONARIM: `sync_agent_skills` symlink'leri "
                                f"(ajan küratörü silmiş olabilir) ya da skills/ kataloğu.")
                preload = kalan
                if not _agent_budget_take(0.0):
                    return None
                alt += 1
                cmd = _agent_chat_cmd(bin_, prompt, preload, model)
                out, sure_ms = _kos(cmd, deneme=attempt + 1, alt=alt)
                empty = (out.returncode != 0 or not (out.stdout or "").strip()
                         or _agent_reply_missing(out.stdout))
        son_stdout, son_stderr = out.stdout or "", out.stderr or ""
        son_rc = out.returncode
        tcalls = _agent_tool_calls(out.stdout)
        # (c) BOŞ CEVABIN İKİ SINIFI AYRIŞIR: imza varsa CLI ağa çıkmadan yapılandırma rehberi
        # bastı (yapılandırmasız), yoksa gerçekten cevapsız kalındı (kota/arka uç).
        unconf = _agent_unconfigured_sign(out.stdout, out.stderr) if empty else None
        _tel_satir = _telemetri(out, sure_ms, deneme=attempt + 1, alt=alt,
                                sinif=(_at.SINIF_YAPILANDIRMASIZ if unconf
                                       else (_at.SINIF_BOS if empty else _at.SINIF_DOLU)))
        # SKILL ADLARI GERİ GELDİ (2026-08-13) — GERİLEME ONARIMI, YENİ ÖZELLİK DEĞİL.
        # 2026-07-20'ye kadar `nous_call_skills` olayı çağrı başına `names: [...]` tam listesini
        # yazıyordu; `_agent_call` yeniden yazılırken liste `preloaded: <sayı>`ya çöktü ve bir daha
        # geri gelmedi (kanıt + hacim ölçümü: `agent_telemetry.skill_adlari` üstündeki blok,
        # docs/DENETIM-SKILL-CAGRI-IZI-2026-08-13.md). `preloaded` SİLİNMEDİ: bugünkü
        # okuyucular sayıyı okumaya devam etsin, yeni alan onun YANINA gelsin.
        _sk_adlar, _sk_kirpildi = _at.skill_adlari(preload)
        obs.log("agent_call", kind=kind, preloaded=len(preload), skills=_sk_adlar,
                # Kırpılan sayı HER SATIRDA yazılır (0 olsa bile): alanın yokluğu bu depoda
                # "sıfır sanılır" sınıfına giriyor (bkz. `agent_tooluse.json` `olculemeyen` dersi).
                skills_kirpildi_n=_sk_kirpildi, model=model or "varsayılan",
                attempt=attempt + 1, empty=empty, tool_calls=tcalls, unconfigured=bool(unconf),
                # SÜRE OLAYA DA KONUR: `agent_calls.jsonl` tam ölçümü taşır ama olay
                # defterini tek başına okuyan biri (canlı journal takibi) süreyi orada da görmeli —
                # aksi halde iki damganın farkını "çağrı süresi" sanma hatası geri döner.
                sure_ms=round(sure_ms, 1), alt_kosum=alt,
                # `-Q` altında `tool_calls=-1` YAPISALDIR ve `empty` fiilen "rc!=0 ya da boş stdout"a
                # iner — o iki olgu deftere yazılmadan hiçbir boş çağrı teşhis edilemez.
                returncode=out.returncode, stdout_kr=len(out.stdout or ""),
                stderr_kr=len(out.stderr or ""))
        if unconf:
            # (d) bütçe iadesi + (c) SOĞUMA YAZILMAZ ve zincir DENENMEZ: yapılandırmasız bir CLI
            # ikinci modelde de yapılandırmasızdır — denemek ikinci bir süreci boşuna doğurur.
            iade = _agent_budget_refund(f"agent_unconfigured:{kind}")
            obs.warn("agent_unconfigured", kind=kind, imza=unconf, attempt=attempt + 1,
                     model=model or "varsayılan", returncode=out.returncode,
                     butce_iade=iade, cooldown_yazildi=False,
                     detail=f"yerel CLI yapılandırılmamış (imza: {unconf!r}) — çağrı AĞA ÇIKMADI; "
                            f"bu kota DEĞİLDİR: havuz soğuması yazılmaz, RPD sayacı iade edilir "
                            f"(iade={iade}). Onarım: GEMINI_API_KEY ile açılış senkronu ya da "
                            f"panodan anahtar girişi.")
            return None
        if not empty:
            try:                                     # #4 telemetri: MCP araç kullanımını biriktir
                st = store.read_json("agent_tooluse.json", {"calls": 0, "with_tools": 0, "total_tools": 0})
                if tcalls >= 0:
                    st["calls"] += 1
                    st["with_tools"] += 1 if tcalls > 0 else 0
                    st["total_tools"] += tcalls
                else:
                    # `-Q` OTURUM ÖZETİNİ BASTIRIR → araç sayısı ÖLÇÜLEMEZ. Ayrı sayaç, çünkü
                    # ölçülemeyeni `calls`a katmak oranı sessizce seyreltir; hiç saymamak ise
                    # sayacı dondurup "MCP hiç kullanılmadı" gibi okuturdu (eksik alan = sıfır
                    # sanılır sınıfı). Sayı burada durur ve `integrations_status` onu YAYINLAR.
                    st["olculemeyen"] = int(st.get("olculemeyen", 0)) + 1
                store.write_json("agent_tooluse.json", st)
            except Exception:  # sessiz-yutma: yardımcı G/Ç yolu; çağıran yokluğu zaten yedek değerle karşılıyor ve asıl okuma hatası store katmanında bir kez uyarılıyor
                pass
            # CEVABI VEREN DENEME BUDUR (zincirin kaçıncı ayağı olursa olsun) — künye buradan çıkar.
            _agent_model_kaydet(model)
            # İz anahtarı da AYNI denemeden gelir: "kim konuştu" ile "hangi çağrıda konuştu" bu
            # noktada eşlenmezse atıf satırı ham izine (agent_calls/agent_traces) hiç bağlanamaz.
            _agent_iz_kaydet((_tel_satir or {}).get("iz_id"))
            return out.stdout
    # ZİNCİR UZUNLUĞU DÜRÜST BİLDİRİLİR: canlı defterde bu satır "tüm model zinciri cevapsız" diyordu
    # ama tried=1'di — NOUS_FALLBACK_MODEL hiç ayarlanmamıştı, yani "düşüş zinciri" tek elemanlıydı.
    # Yedeğin YOKLUĞU, yedeğin BAŞARISIZLIĞI gibi okunuyordu.
    exhausted = _pool_exhausted()
    # BOŞ YEDEK ≠ BİTMİŞ KOTA. Canlı satır: `agent_call kind=review
    # model=tencent/hy3:free attempt=2 empty=true` → `agent_call_empty pool_exhausted="gemini"
    # cooldown_s=21600`. İki olgu tek cezaya katlanmıştı: (i) havuzun kendi kaydı tükenmişlik
    # diyordu, (ii) YEDEK model (başka bir üst-akış!) boş döndü. (ii) hakkında havuzun söyleyecek
    # hiçbir şeyi yok: hat çalıştı, süreç koştu, model konuşmadı. Çıktıda kota imzası YOKSA cezayı
    # üstel merdivene bindirmek 6 saatlik bir kilit üretiyor ve kotası dolmamış BİRİNCİ modeli de
    # kapsıyordu. Ayrım imzaya dayanır — tahmine değil.
    kota_imza = _agent_quota_sign(son_stdout, son_stderr)
    yedek_sustu = len(models) > 1 and not kota_imza
    cooled, sinif = 0.0, None
    if yedek_sustu:
        # Kısa pencere havuzun durumundan BAĞIMSIZ kurulur ve bunun iki ayrı gerekçesi var:
        # (i) havuz ne derse desin, susan yedek hakkında söylediği şey ölçülmemiştir; (ii) havuz
        # işareti bayat olduğu için düştüğünde eski kod HİÇ soğuma yazmıyordu — yani (1) numaralı
        # düzeltme tek başına, ölü bir zinciri her turda yeniden doğuran bir delik açardı.
        sinif = "fallback_empty"
        cooled = brain_pause("agent", f"fallback_empty:{kind}", BRAIN_COOLDOWN_BASE_S)
    elif exhausted:
        # Havuzun kendi kaydı 'exhausted/429' diyor: rotasyon absorbe EDEMEZ (sağlayıcı başına tek
        # kimlik). Ajanı da soğumaya al, yoksa her poll yeni bir süreçle aynı duvara çarpar.
        sinif = "pool_exhausted"
        cooled = brain_stand_down("agent", f"pool_exhausted:{exhausted}")
    if yedek_sustu:
        obs.warn("review_fallback_empty", kind=kind, model=models[-1] or "varsayılan",
                 chain=len(models), pool_exhausted=exhausted, cooldown_s=round(cooled, 1),
                 detail=f"yedek model boş döndü ve çıktıda KOTA İMZASI YOK — bu 'kota bitti' değil, "
                        f"'hat çalıştı, model sustu' sınıfıdır. Bu yüzden üstel havuz cezası "
                        f"(tavan {BRAIN_COOLDOWN_MAX_S} sn) YAZILMAZ; yalnız {BRAIN_COOLDOWN_BASE_S} "
                        f"sn'lik düz yeniden-deneme penceresi kurulur ve BİRİNCİ model bir sonraki "
                        f"turda yeniden denenebilir kalır.")
    obs.warn("agent_call_empty", kind=kind, tried=len(models), chain=len(models),
             fallback_model_configured=bool(secrets.get("NOUS_FALLBACK_MODEL")),
             pool_exhausted=exhausted, cooldown_s=round(cooled, 1), cooldown_sinifi=sinif,
             kota_imzasi=kota_imza,
             # HAM KANIT — bir daha KÖR kalmamak için. Bu üç alan olmadan defterdeki "boş"
             # satırı hiçbir teşhis taşımıyordu: hangi çıkış kodu, süreç ne dedi, stderr ne taşıdı.
             # Maskeleme desenle yapılır (bkz. `_ham_ozet`); gerçek sır değerleri OKUNMAZ.
             returncode=son_rc, ham_stdout=_ham_ozet(son_stdout), ham_stderr=_ham_ozet(son_stderr),
             detail=f"model zinciri cevapsız (zincir uzunluğu {len(models)}) — kota/arka uç; "
                    f"deterministik yol devrede")
    return None


def _propose_nous_local() -> dict | None:
    """Yerelde kurulu hermes-agent'ı TEK ATIMLIK headless çağırır — artık _agent_call kapısından
    (oran bütçesi + düşüş zinciri). None → beyin zinciri bir sonrakine düşer."""
    text = _agent_call(_user_prompt() +
                       "\n\nYou have Meridian's skill library available — consult the loaded skills to "
                       "ground your reasoning (screeners, gate law, regime analysis). Your FINAL message "
                       "must be ONLY the JSON object — no prose or markdown around it.",
                       preload=tuple(_skill_preload("proposal")), kind="proposal",
                       timeout=300, max_wait=45.0)
    if text is None:
        # ÇAĞRI HİÇ YAPILMADI (ikili yok / oran bütçesi / havuz soğuması). Bu "boş cevap" DEĞİLDİR:
        # cevapsızlık ile cevapsız-kalmak farklı arızalardır ve tek satırda birleşince ikisi de kaybolur.
        _trace_note(EMPTY_NO_CALL, detail="yerel ajan çağrısı yapılamadı")
        return None
    return _parse_hyp(_extract_json(text))


def _unwrap_strings(t: str) -> str:
    """hermes-agent'ın çıktı paneli ~80 sütunda SATIR SARMALAR — uzun bir JSON string'inin içine ham
    satır sonu + girinti düşer, ki bu JSON'da illegaldir (canlıda bulundu: rationale alanı). Onarım:
    yalnız STRING İÇİNDEKİ ham \n(+takip eden girinti) tek boşluğa katlanır; yapısal satır sonlarına
    dokunulmaz (kaçışlar korunur)."""
    out, ins, esc, i = [], False, False, 0
    while i < len(t):
        c = t[i]
        if ins:
            if esc:
                out.append(c); esc = False
            elif c == "\\":
                out.append(c); esc = True
            elif c == '"':
                out.append(c); ins = False
            elif c == "\n":
                out.append(" ")
                i += 1
                while i < len(t) and t[i] == " ":
                    i += 1
                continue
            else:
                out.append(c)
        else:
            if c == '"':
                ins = True
            out.append(c)
        i += 1
    return "".join(out)


def _balanced_json(t: str, start: int) -> str | None:
    """`start`ten sonraki İLK `{`ten başlayıp süslü parantezleri dengeleyerek tam JSON nesnesini
    keser. Nesne bulunamaz ya da denge kapanmazsa None (kesik gövde uydurulmaz)."""
    depth = 0
    i = t.find("{", start)
    if i < 0:
        return None
    for j in range(i, len(t)):
        if t[j] == "{":
            depth += 1
        elif t[j] == "}":
            depth -= 1
            if depth == 0:
                return t[i:j + 1]
    return None


def _extract_json(text: str) -> str:
    """hermes-agent CLI çıktısından CEVAP JSON'unu ayıkla. KRİTİK: CLI, prompt'u başa echo'lar
    ("Query: …") — prompt'umuz koca bir JSON bağlamı taşıdığı için 'ilk dengeli nesneyi al' yaklaşımı
    CEVABI değil ECHO'yu yakalıyordu (canlıda bulundu). Cevap ╭─…╮ paneli içindedir: SON panelin
    içinden ayıkla; panel yoksa metindeki SON dengeli nesneye düş (cevap her zaman echo'dan sonra)."""
    import re
    t = re.sub(r"\x1b\[[0-9;]*[A-Za-z]", "", text or "")
    top = t.rfind("╭─")
    if top >= 0:
        body_start = t.find("\n", top)
        bot = t.find("╰─", top)
        panel = t[body_start + 1: bot if bot > 0 else len(t)]
        panel = re.sub(r"[│╭╮╰╯─]", " ", panel)
        got = _balanced_json(panel, 0)
        if got:
            return got
    # panel bulunamadı: echo'yu atlamak için SON dengeli nesneyi tara
    best, pos = None, 0
    while True:
        got = _balanced_json(t, pos)
        if got is None:
            break
        best = got
        pos = t.find(got, pos) + len(got)
    return best or t


def _nous_portal_model() -> str:
    """PORTAL (uzak, OpenAI-uyumlu) Nous ucuna GERÇEKTEN giden model adı — `_nous_text`in istek
    gövdesine yazdığı değerin TEK kaynağı.

    NEDEN TEK KAYNAK: `chain_text` künyesi bu ayağın modelini de bildirmek zorunda ve aynı
    ifadeyi ikinci kez yazmak, bu turun kapattığı sınıfın ("iki kopya sessizce ayrışır") tam
    kendisiydi. Varsayılan burada UYDURMA DEĞİLDİR ve ayrım `_model_id` docstring'inde yazılı:
    portal modunda gövdeyi BİZ kuruyoruz, yani `NOUS_DEFAULT_MODEL` gerçekten GİDEN addır (yerel
    ajan modunda değildi — orada adı CLI'nın kendi config'i seçer, bu yüzden orası None döner).
    ÖLÜ-AD GÖÇÜ UYGULANMAZ, bilerek: `GEMINI_DEAD_MODEL_MAP` Google adlarını taşır, portal ucu
    Nous/OpenRouter kimliği ister — çeviri burada adı ONARMAZ, BOZARDI."""
    return secrets.get("NOUS_MODEL") or NOUS_DEFAULT_MODEL


def _nous_text(user: str, *, note: str) -> str | None:
    """Nous'un UZAK ucunun (OpenAI-uyumlu) tek gövdesi — metin döner. Bkz. `_claude_text` notu."""
    import httpx
    base = (secrets.get("NOUS_ENDPOINT") or NOUS_DEFAULT_ENDPOINT).rstrip("/")
    model = _nous_portal_model()
    govde = {"model": model, "max_tokens": NOUS_MAX_TOKENS,
             "messages": [{"role": "system", "content": SYSTEM},
                          {"role": "user", "content": user}]}
    if NOUS_REASONING_EFFORT:             # doğrulanmamış alan yalnız operatör açarsa gövdeye girer
        govde["reasoning"] = {"effort": NOUS_REASONING_EFFORT}
    r = httpx.post(f"{base}/chat/completions",
                   headers={"Authorization": f"Bearer {secrets.get('NOUS_API_KEY')}",
                            "Content-Type": "application/json"},
                   json=govde, timeout=120.0)
    r.raise_for_status()
    d = r.json()
    u = d.get("usage") or {}
    # AKIL YÜRÜTME TOKENLARI: OpenAI-uyumlu uçta burada raporlanır (gemini'de thoughtsTokenCount) ve
    # `completion_tokens` içinde GÖRÜNMEZLER. Alt alanı taşımayan uçlar var → ölçülmediğinde None
    # kalır ve `spend.record` satıra HİÇ yazmaz: "0" yazmak ölçülmemişi ölçülmüş göstermek olurdu.
    akil = (u.get("completion_tokens_details") or {}).get("reasoning_tokens")
    from . import spend
    spend.record(u.get("prompt_tokens", 0), u.get("completion_tokens", 0), model, note=note,
                 thought_tokens=akil)
    ch = (d.get("choices") or [{}])[0] or {}
    msg = ch.get("message") or {}
    txt = str(msg.get("content") or "")
    finish = str(ch.get("finish_reason") or "")
    # KESİLME KONTROLÜ METİN KONTROLÜNDEN ÖNCE GELİR — `_gemini_text`teki sıranın aynısı ve buradaki
    # KUSURUN TA KENDİSİ: eskiden finish_reason ayrımı aşağıdaki `if not txt.strip()` bloğunun
    # İÇİNDEYDİ. Kesilen cevap BOŞ DEĞİLDİR (içinde düşünce ön-eki vardır), o yüzden bu ayrıma HİÇ
    # UĞRAMIYORDU: yarım metin çağırana dönüyor, `_parse_hyp` JSON bulamıyor ve defter "unparseable"
    # yazıyordu — biçim suçlanıyor, asıl arıza (bütçe) görünmez kalıyordu. Kısmî metin zaten
    # kullanılamaz; doğru adla boş dönmek hem sınıfı hem düzeltmeyi görünür kılar.
    if finish == "length":
        _trace_note(EMPTY_TRUNCATED,
                    detail=f"reasoning={akil}, completion={u.get('completion_tokens')}, "
                           f"cap={NOUS_MAX_TOKENS}")
        return None
    if not txt.strip():                   # 200 OK ama içerik yok — sebebi ayır (araç çağrısı / red)
        if msg.get("tool_calls") or msg.get("function_call"):
            _trace_note(EMPTY_TOOL_ONLY, detail=f"finish_reason={finish or '?'}")
        elif finish in ("content_filter", "refusal"):
            _trace_note(EMPTY_REFUSAL, detail=f"finish_reason={finish}")
        else:
            _trace_note(EMPTY_NO_TEXT, detail=f"finish_reason={finish or '?'}")
        return None
    return txt


def _propose_nous() -> dict | None:
    """Nous Hermes beyni: YEREL hermes-agent (varsayılan, kuruluysa — uygulamanın parçası) ya da
    NOUS_ENDPOINT'teki OpenAI-uyumlu uç (Nous Portal / uzak sunucu)."""
    if _nous_local():
        return _propose_nous_local()
    txt = _nous_text(_user_prompt(), note="reflect (nous)")
    return _parse_hyp(txt) if txt else None


def _gemini_call(user: str, *, note: str) -> str | None:
    """Gemini'nin tek gövdesi — metin döner. Bkz. `_claude_text` notu."""
    import httpx
    # GERÇEK ÇAĞRI YOLU (2026-08-13): göç olayını basan iki yerden biri — `_nous_model_zinciri`in
    # gemini ikizi. Sonda (`ping_brain`), rapor (`active_model`/`_model_id`) ve yerel-ajan config
    # yüzeyleri AYNI çeviriyi sessiz alır; defter yazımı yalnız modele gerçekten gidildiğinde olur.
    model = gemini_model(olay=True)
    headers = {"Content-Type": "application/json"}
    key = secrets.get("GEMINI_API_KEY")
    if key:
        headers["x-goog-api-key"] = key
    else:
        headers["Authorization"] = f"Bearer {secrets.get('GEMINI_OAUTH_TOKEN')}"
    # SÜRE ÖLÇÜMÜ (`tasiyici="http"`) — bkz. `_claude_text`teki aynı blok.
    _kr = _at.Kronometre()
    try:
        r = httpx.post(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                       headers=headers,
                       json={"system_instruction": {"parts": [{"text": SYSTEM}]},
                             "contents": [{"role": "user", "parts": [{"text": user}]}],
                             # düşünce bütçesi AÇIKÇA kapalı: yoksa düşünce tokenları üretim tavanını yer
                             # ve cevap JSON'un ortasında kesilir (ölçüm: GEMINI_THINKING_BUDGET yorumu).
                             "generationConfig": {"response_mime_type": "application/json",
                                                  "thinkingConfig": {"thinkingBudget": GEMINI_THINKING_BUDGET},
                                                  "maxOutputTokens": GEMINI_MAX_OUTPUT_TOKENS}},
                       timeout=120.0)
        r.raise_for_status()
    except BaseException as e:
        _at.kaydet(kind=note, model=model, deneme=1, alt=0, sure_ms=_kr.dur(),
                   sonuc_sinifi=_at.SINIF_BOS, tasiyici=_at.TASIYICI_HTTP, arac_cagri_n=None,
                   istem=user, stderr=f"{type(e).__name__}: {e}", istisna=type(e).__name__)
        raise
    _kr.dur()
    d = r.json()
    um = d.get("usageMetadata") or {}
    from . import spend
    # düşünce tokenları FATURALANAN çıktıdır: defterde ayrı alanda görünür (düşünce kapalıyken alan
    # cevapta hiç bulunmaz → 0). Maliyet formülü DEĞİŞMEDİ; bkz. spend.record notu.
    spend.record(um.get("promptTokenCount", 0), um.get("candidatesTokenCount", 0), model,
                 note=note, thought_tokens=um.get("thoughtsTokenCount", 0))
    metin = _gemini_text(d) or None       # metin yoksa nedeni _gemini_text zaten işaretledi
    _at.kaydet(kind=note, model=model, deneme=1, alt=0, sure_ms=_kr.ms,
               sonuc_sinifi=(_at.SINIF_DOLU if metin else _at.SINIF_BOS),
               tasiyici=_at.TASIYICI_HTTP, arac_cagri_n=None, istem=user, stdout=metin,
               returncode=r.status_code)
    return metin


def _propose_gemini() -> dict | None:
    """Gemini — GEMINI_API_KEY (AI Studio) YA DA operatörün kendi OAuth akışından gelen
    GEMINI_OAUTH_TOKEN (Bearer). Token yenilemeyi operatör/kendi aracı yapar; motor yalnızca kullanır."""
    txt = _gemini_call(_user_prompt(), note="reflect (gemini)")
    return _parse_hyp(txt) if txt else None


def _gemini_text(d: dict) -> str:
    """200 OK bir Gemini gövdesinden METNİ çıkar ve metin KULLANILAMAZSA nedeni sınıflandır. Canlıda
    'başarılı ama kullanılamaz' cevaplar vardı; hepsi tek bir 'empty' satırına düşüyordu. Ayrı sebepler
    ayrı şey söyler: promptFeedback.blockReason = politika reddi, finishReason=SAFETY = güvenlik bloğu,
    parts yalnız functionCall = model araç çağırdı, finishReason=MAX_TOKENS = üretim TAVANDA kesildi.

    MAX_TOKENS metin DOLUYKEN de gelir ve o metin YARIM JSON'dur (2026-07-26 canlı ölçüm: düşünce
    tokenları 4000'lik tavanın 3838'ini yiyince cevap rationale'ın ortasında kesildi). Eskiden bu kısmî
    metin _parse_hyp'e gidip 'unparseable' sınıfına düşüyordu — YANLIŞ ad: biçim değil bütçe arızası,
    ve yanlış ad üç gün boyunca doğru düzeltmeyi (düşünce bütçesi) görünmez kıldı. Bu yüzden kesilme
    kontrolü metin kontrolünden ÖNCE gelir: kısmî JSON zaten kullanılamaz, doğru adla boş döneriz."""
    fb = (d.get("promptFeedback") or {}).get("blockReason")
    if fb:
        _trace_note(EMPTY_REFUSAL, detail=f"blockReason={fb}")
        return ""
    cand = (d.get("candidates") or [{}])[0] or {}
    parts = ((cand.get("content") or {}).get("parts") or [])
    text = "".join(str(p.get("text") or "") for p in parts if isinstance(p, dict))
    finish = str(cand.get("finishReason") or "")
    if finish == "MAX_TOKENS":
        um = d.get("usageMetadata") or {}
        # ölçülmeyen alan UYDURULMAZ: cevapta yoksa None yazılır (düşünce kapalıyken alan hiç gelmez).
        _trace_note(EMPTY_TRUNCATED,
                    detail=f"thoughts={um.get('thoughtsTokenCount')}, "
                           f"candidates={um.get('candidatesTokenCount')}, cap={GEMINI_MAX_OUTPUT_TOKENS}")
        return ""
    if text.strip():
        return text
    if any(isinstance(p, dict) and ("functionCall" in p or "function_call" in p) for p in parts):
        _trace_note(EMPTY_TOOL_ONLY, detail=f"finishReason={finish or '?'}")
    elif finish in ("SAFETY", "RECITATION", "BLOCKLIST", "PROHIBITED_CONTENT"):
        _trace_note(EMPTY_REFUSAL, detail=f"finishReason={finish}")
    else:
        _trace_note(EMPTY_NO_TEXT, detail=f"finishReason={finish or '?'}")
    return ""


def ping_brain(provider: str) -> dict:
    """Salt-okunur erişilebilirlik + kimlik testi ({ok, detail} — asla anahtar sızmaz). Model listesi
    ucuna GET: emir/üretim yok, maliyet ~sıfır."""
    import httpx
    try:
        if provider == "nous":
            if _nous_local():
                bin_ = _hermes_bin()
                if not bin_:
                    return {"ok": False, "detail": "yerel hermes-agent bulunamadı (kur: hermes-agent.nousresearch.com)"}
                import subprocess
                try:
                    v = subprocess.run([bin_, "--version"], capture_output=True, text=True, timeout=15)
                    ver = (v.stdout or v.stderr or "").strip().splitlines()[0][:60] if (v.stdout or v.stderr) else "?"
                    return {"ok": v.returncode == 0, "detail": f"yerel hermes-agent · {ver}"}
                except Exception as e:
                    return {"ok": False, "detail": f"yerel ikili çalışmadı ({type(e).__name__})"}
            if not secrets.get("NOUS_API_KEY"):
                return {"ok": False, "detail": "NOUS_API_KEY girilmemiş (ya da NOUS_ENDPOINT=local ile yerel kur)"}
            base = (secrets.get("NOUS_ENDPOINT") or NOUS_DEFAULT_ENDPOINT).rstrip("/")
            r = httpx.get(f"{base}/models",
                          headers={"Authorization": f"Bearer {secrets.get('NOUS_API_KEY')}"}, timeout=12)
            if r.status_code in (401, 403):
                return {"ok": False, "detail": "anahtar reddedildi"}
            r.raise_for_status()
            n = len((r.json() or {}).get("data", []))
            return {"ok": True, "detail": f"bağlandı · {n} model görünür"}
        if provider == "gemini":
            key, tok = secrets.get("GEMINI_API_KEY"), secrets.get("GEMINI_OAUTH_TOKEN")
            if not key and not tok:
                return {"ok": False, "detail": "GEMINI_API_KEY veya GEMINI_OAUTH_TOKEN girilmemiş"}
            headers = {"x-goog-api-key": key} if key else {"Authorization": f"Bearer {tok}"}
            r = httpx.get("https://generativelanguage.googleapis.com/v1beta/models",
                          headers=headers, timeout=12)
            if r.status_code in (401, 403):
                return {"ok": False, "detail": "kimlik reddedildi" + ("" if key else " — OAuth token süresi dolmuş olabilir")}
            r.raise_for_status()
            models = [str(m.get("name", "")).split("/")[-1] for m in (r.json() or {}).get("models", [])]
            want = gemini_model()
            hit = want in models
            close = [m for m in models if "3.1" in m or "gemini-3" in m][:3]
            extra = f" · '{want}' listede ✓" if hit else (f" · '{want}' listede YOK — yakın: {', '.join(close) or 'bulunamadı'}")
            return {"ok": True, "detail": f"bağlandı · {len(models)} model{extra}"}
    except httpx.HTTPStatusError as e:
        return {"ok": False, "detail": f"HTTP {e.response.status_code}"}
    except Exception as e:
        return {"ok": False, "detail": f"bağlanılamadı ({type(e).__name__})"}
    return {"ok": False, "detail": "bilinmeyen sağlayıcı"}


# Yerli sağlayıcı: harness "gemini" id'sini ve GEMINI_API_KEY env adını yerel olarak tanır
# (auth.py ProviderConfig) — OpenAI-uyumlu dolambaç GEREKMEZ (canlıda "Unknown provider: openai" ile bulundu).

# ---- YEREL CLI YAPILANDIRMA ÖLÇÜMÜ --------------------------
# `hermes config get` SÖZLEŞMESİ ÖLÇÜLDÜ (kurulu sürüm, 2026-08-02) — tahmin edilmedi:
#   • AYARLI anahtar  → stdout = ÇIPLAK değer, stderr boş, rc=0
#   • AYARSIZ anahtar → stdout BOŞ, stderr = "Config key not set: <key>", rc=1
#   • `config` alt komutu `cmd_chat`in ilk-koşum bekçisine GİRMEZ; yani yapılandırmasız bir kurulumda
#     bile ölçüm yapılabilir (rehber metnini yalnız `chat` basar).
# Ölçmeden yazılmış bir sürüm "rc!=0 → ölçülemedi" derdi ve tam da teşhis etmesi gereken hâli
# (yapılandırmasız CLI) ölçülemez sayardı.
CFG_UNSET_SIGN = "Config key not set"
GEMINI_ENV_NAMES = ("GEMINI_API_KEY", "GOOGLE_API_KEY")   # CLI'nin Gemini için okuduğu env adları


def _agent_cfg_get(bin_: str, key: str) -> tuple[str | None, str]:
    """(değer, durum) — durum: "ayarli" | "ayarsiz" | "olculemedi".

    UYDURMA YASAĞI: değer yalnız "ayarli" hâlinde doludur. "ayarsiz" hükmü SADECE ölçülmüş imzayla
    verilir; imzasız bir hata (bozuk ikili, izin hatası, sürüm farkı) "yok" değil "BİLİNMİYOR"dur —
    ikisini birleştirmek, ölçüm arızasını yapılandırma arızası gibi okutur ve yanlış onarımı tetikler."""
    import subprocess
    try:
        r = subprocess.run([bin_, "config", "get", key], capture_output=True, text=True, timeout=30)
    except Exception:
        # sessiz-yutma: istisna BİLGİ KAYBETMEDEN "olculemedi" durumuna çevriliyor — bu yolun tek
        # tüketicisi `local_agent_config_state` ve o, "olculemedi"yi hüküm vermeden yukarı taşıyıp
        # açılış senkronunu DURDURUYOR (`local_agent_config_olculemedi` uyarısı orada basılır).
        # Burada ayrıca uyarmak aynı olguyu iki kez bağırırdı; yutulan tek şey istisnanın TÜRÜ ve
        # onun karara etkisi yok: asılan da, izin reddeden de, bulunamayan da ölçülemeyendir.
        return None, "olculemedi"
    out = (r.stdout or "").strip()
    if r.returncode == 0 and out:
        return out.splitlines()[-1].strip(), "ayarli"
    if CFG_UNSET_SIGN in (r.stderr or ""):
        return None, "ayarsiz"
    return None, "olculemedi"


def _agent_env_path() -> str:
    """`~/.hermes/.env` — `sync_local_agent_gemini` ile AYNI yoldan türetilir (modül sabiti DEĞİL:
    o dosya da `expanduser` çağrısını çalışma anında yapar ve testler tek noktadan yönlendirir)."""
    return os.path.join(os.path.expanduser("~/.hermes"), ".env")


def _agent_env_has(names: tuple) -> bool | None:
    """`~/.hermes/.env` DOLU bir `names` satırı taşıyor mu? None = dosya okunamadı.

    DEĞER HİÇBİR ZAMAN OKUNMAZ/DÖNMEZ/LOGLANMAZ — yalnız satırın varlığı ve boş olmadığı. Dosyanın
    YOKLUĞU bir ölçüm arızası değil, ölçülmüş bir yokluktur (canlı vaka: A1 taşınmasında ~/.hermes
    hiç taşınmadı) — o yüzden None değil False döner.

    AD KÜMESİ PARAMETRELENDİ (gövde bit bit aynı): aynı dosya artık iki soruya cevap
    veriyor — Gemini anahtar satırı (`local_agent_config_state`) ve OpenRouter kimliği
    (`_agent_slug_provider_ready`). İkinci bir ayrıştırıcı yazmak, aynı biçimi iki yerde
    yorumlayan iki davranış demekti (`export ` öneki, tırnak soyma, boş-değer ayrımı)."""
    path = _agent_env_path()
    if not os.path.exists(path):
        return False
    try:
        with open(path) as fh:
            for line in fh:
                s = line.strip()
                if s.startswith("export "):
                    s = s[7:]
                k, sep, v = s.partition("=")
                if sep and k.strip() in names and v.strip().strip("'\""):
                    return True
        return False
    except OSError:
        # sessiz-yutma: dosya VAR ama okunamadı (izin/G-Ç). Bu "anahtar yok" DEĞİLDİR ve öyle
        # dönmek yanlış onarımı tetiklerdi: çağıran False'u ölçülmüş yokluk sayıp CLI'yi yeniden
        # yapılandırırdı. None döndürmek arızayı KORUR — `local_agent_config_state` onu
        # "yapilandirilmis=None"a çevirir, açılış senkronu koşmaz ve neden defterde uyarı olur.
        return None


def _agent_env_has_key() -> bool | None:
    """`~/.hermes/.env` DOLU bir GEMINI anahtar satırı taşıyor mu? (sözleşme AYNEN)."""
    return _agent_env_has(GEMINI_ENV_NAMES)


def local_agent_config_state() -> dict:
    """YEREL CLI'NİN YAPILANDIRMA DURUMU — ÖLÇÜLÜR, VARSAYILMAZ (açılış senkron-doğrulamasının girdisi).

    Canlı vakanın kök nedeni tam olarak buydu: hiçbir bekçi "yerel ajan yapılandırılmış mı" diye
    SORMUYORDU. Bu fonksiyon o soruyu iki bağımsız kanaldan ölçer — CLI'nin kendi config'i
    (`model.default`) ve `~/.hermes/.env` anahtar satırı — ve ölçemediğini ölçemedi diye yazar.

    Dönüş: {kurulu, model, model_durum, env_anahtar, yapilandirilmis, neden}
      yapilandirilmis: True (iki kanal da dolu) · False (en az biri ÖLÇÜLMÜŞ boş) · None (ölçülemedi)."""
    bin_ = _hermes_bin()
    if not bin_:
        return {"kurulu": False, "model": None, "model_durum": "olculemedi", "env_anahtar": None,
                "yapilandirilmis": None, "neden": "yerel hermes-agent ikilisi bulunamadı"}
    model, model_durum = _agent_cfg_get(bin_, "model.default")
    env_key = _agent_env_has_key()
    modelsiz = None if model_durum == "olculemedi" else (model_durum == "ayarsiz")
    if modelsiz is True or env_key is False:
        eksik = [ad for ad, yok in (("model.default ayarsız", modelsiz is True),
                                    ("~/.hermes/.env Gemini anahtar satırı yok", env_key is False)) if yok]
        yap, neden = False, " + ".join(eksik)
    elif modelsiz is None or env_key is None:
        # Kısmi ölçüm bir hüküm değildir: "ölçemediğim yer boştu" demek uydurmadır ve YANLIŞ TARAFA
        # düşerdi — ölçülemeyen bir CLI'yi yeniden yapılandırmak, çalışan bir kurulumu bozabilir.
        yap, neden = None, (f"model ölçümü={model_durum}"
                            f" · env ölçümü={'okunamadı' if env_key is None else 'ok'}")
    else:
        yap, neden = True, None
    return {"kurulu": True, "model": model, "model_durum": model_durum, "env_anahtar": env_key,
            "yapilandirilmis": yap, "neden": neden}


def sync_local_agent_gemini(enable: bool) -> dict:
    """Panodan girilen GEMINI_API_KEY'i YEREL hermes-agent'a taşır — operatör anahtarı TEK yerden
    (Ayarlar) girer, terminal/.env adımı yoktur. enable=True: mevcut model bloğu yedeklenir, ajanın
    .env'ine OPENAI_API_KEY yazılır (Gemini'ın OpenAI-uyumlu ucu bu adı okur) ve provider/base_url/model
    Gemini'a çevrilir. enable=False (anahtar silindi): .env satırı kaldırılır, yedeklenen Nous ayarı
    geri yüklenir. Anahtar değeri hiçbir yerde loglanmaz/yansıtılmaz.

    `senkron_ts`: HER dönüşte ISO damga bulunur — başarıda da,
    reddte de, istisnada da. Panonun okuduğu satır "senkron OK" derken o cümlenin NE ZAMAN
    ölçüldüğünü söylemiyordu; canlı vakada altı gün önceki bir OSError'un sonucu taze bir hüküm gibi
    okundu. Damgasız bir durum satırı, bayatladığını kendisi söyleyemez."""
    import subprocess
    ts = memory.now_iso()
    bin_ = _hermes_bin()
    if not bin_:
        return {"ok": False, "detail": "yerel hermes-agent kurulu değil", "senkron_ts": ts}
    home = os.path.expanduser("~/.hermes")
    env_path = os.path.join(home, ".env")
    backup_path = os.path.join(home, "meridian-model-backup.json")

    def _cfg(key, val):
        """Yerel hermes-agent config anahtarını `config set` ile yazar (30 sn zaman aşımı)."""
        subprocess.run([bin_, "config", "set", key, val], capture_output=True, text=True, timeout=30)

    def _cfg_get(key):
        """Config anahtarını TEK ölçüm yolundan (`_agent_cfg_get`) okur; ayarsız anahtar "" döner."""
        # TEK ÖLÇÜM YOLU (`_agent_cfg_get`): yedekleme burada, teşhis `local_agent_config_state`te
        # aynı sözleşmeyi okumalı — iki ayrı ayrıştırıcı sessizce ayrışırdı. Davranış aynı: ayarsız
        # anahtar (stdout boş) "" olarak yedeklenir ve geri yüklemede atlanır.
        return _agent_cfg_get(bin_, key)[0] or ""

    def _write_env(key_value: str | None):
        """`~/.hermes/.env` dosyasını yeniden yazar: eski GEMINI/GOOGLE anahtar satırları süzülür,
        `key_value` verilmişse GEMINI_API_KEY olarak eklenir. Yazım `store.write_text` üzerinden
        ve dosya İZNİ açıkça 0600'e çekilir (sır diskte)."""
        lines = []
        if os.path.exists(env_path):
            with open(env_path) as fh:
                lines = [l for l in fh.read().splitlines()
                         if not l.startswith(("GEMINI_API_KEY=", "GOOGLE_API_KEY="))]
        if key_value:
            lines.append(f"GEMINI_API_KEY={key_value}")
        # KAPI-DIŞI TAŞIMA: elle mkstemp+os.replace (fsync YOK, flock YOK) → store.write_text.
        # env_path (~/.hermes/.env) STATE DIŞI → store mutlak adı olduğu gibi kullanır (kendi kilidi;
        # tek yazar). 0600 auth._write ile AYNI sınıf (sır: GEMINI_API_KEY diskte): store'un mkstemp-0600'ü
        # TESADÜFİdir, DEVREDİLMEZ — açık os.chmod KALIR. YASA-6 OKUYUCU: hermes-agent ikili dosyası .env'den
        # GEMINI_API_KEY okur (+ bu fonksiyon mevcut satırları süzmek için okur).
        store.write_text(env_path, "\n".join(lines) + "\n")
        os.chmod(env_path, 0o600)

    try:
        if enable:
            key = secrets.get("GEMINI_API_KEY")
            if not key:
                return {"ok": False, "detail": "GEMINI_API_KEY boş", "senkron_ts": ts}
            if not os.path.exists(backup_path):   # ilk geçişte mevcut (Nous) ayarı yedekle
                prev = {"provider": _cfg_get("model.provider"), "base_url": _cfg_get("model.base_url"),
                        "default": _cfg_get("model.default")}
                # KAPI-DIŞI TAŞIMA: düz open(w)+json.dump (atomik DEĞİL, fsync/flock YOK)
                # → store.write_json. backup_path (~/.hermes/...) STATE DIŞI → mutlak ad, kendi kilidi.
                # YASA-6 OKUYUCU: aşağıdaki geri-yükleme dalı (json.load) disable'da Nous ayarını geri alır.
                store.write_json(backup_path, prev)
            _write_env(key)
            model = gemini_model()
            _cfg("model.provider", "gemini")            # yerli sağlayıcı — base_url override'ı KALDIRILIR
            subprocess.run([bin_, "config", "unset", "model.base_url"], capture_output=True, text=True, timeout=30)
            _cfg("model.default", model)
            obs.log("local_agent_switched", to="gemini", model=model, senkron_ts=ts)
            return {"ok": True, "detail": f"yerel ajan Gemini'a geçti · {model}", "senkron_ts": ts}
        else:
            _write_env(None)
            restored = None
            if os.path.exists(backup_path):
                with open(backup_path) as fh:
                    prev = json.load(fh)
                for k, v in (("model.provider", prev.get("provider")),
                             ("model.base_url", prev.get("base_url")),
                             ("model.default", prev.get("default"))):
                    if v:
                        _cfg(k, v)
                restored = prev.get("default")
                os.unlink(backup_path)
            obs.log("local_agent_switched", to="restored", model=restored, senkron_ts=ts)
            return {"ok": True, "detail": f"yerel ajan eski ayara döndü · {restored or 'değişmedi'}",
                    "senkron_ts": ts}
    except Exception as e:
        return {"ok": False, "detail": f"senkron hatası ({type(e).__name__})", "senkron_ts": ts}


REVIEW_SKILLS = ("vcp-screener", "pullback-screener", "pre-trade-discipline-gate",
                 "position-sizer", "market-environment-analysis")
AGENT_SKILLS_DIR = os.path.expanduser("~/.hermes/skills")
AGENT_CONFIG = os.path.expanduser("~/.hermes/config.yaml")


def _repo_root() -> str:
    """Depo kökünün mutlak yolu (`config.ROOT`) — skill/config bağlantılarının TEK taban kaynağı."""
    from . import config as _cfg
    return str(_cfg.ROOT)


def config_ensure_integrations() -> dict:
    """Yerel hermes-agent config.yaml'ına Meridian entegrasyonlarını IDEMPOTENT yazar (Tier 1+2):
      • mcp_servers.meridian — salt-okunur veri sunucumuz (analytics/cf/near-miss/rejim/kalibrasyon)
      • hooks.pre_tool_call — koruma hook'u (state/secrets/mode/emir yüzeylerini sert bloklar)
      • prompt_caching.cache_ttl → 1h (oturum-arası önek önbelleği; saf maliyet)
      • credential_pool_strategies — 429 rotasyon stratejisi (havuz varsa devreye girer)
      • model.default ÖLÜ-AD GÖÇÜ — bilinen-ölü Gemini adı sabit alias'a çevrilir (aşağıda)
    Yalnız DEĞİŞİKLİK varsa yazar (churn yok), yazmadan önce .bak alır. hermes-agent config'i kendi
    yeniden yazabildiği için (skill curator gibi) standby döngüsünde tazelenir. Dönüş: {changed:[...]}."""
    import yaml
    bin_ = _hermes_bin()
    if not bin_ or not os.path.exists(AGENT_CONFIG):
        return {"ok": False, "detail": "yerel hermes-agent/config yok"}
    try:
        with open(AGENT_CONFIG) as fh:
            cfg = yaml.safe_load(fh) or {}
    except Exception as e:
        return {"ok": False, "detail": f"config okunamadı ({type(e).__name__})"}
    changed = []
    # ÖLÜ-MODEL GÖÇÜ (HTTP 404 kökü): bu senkron `model.default`ı bugüne dek KORUYORDU —
    # Google bir modeli listeden kaldırınca config'te duran ad her üretim çağrısında 404 yiyor ve
    # kendi kendine ASLA iyileşmiyordu (canlı vaka: gemini-3.5-flash; anahtar sağlam, models-list 200).
    # Yalnız BİLİNEN-ölü adlar çevrilir (GEMINI_DEAD_MODEL_MAP); tanınmayan adlar serbest geçer —
    # elimizdeki liste kesit, gelecekteki geçerli bir modeli "ölü" damgalamak yanlış onarım olurdu.
    # Olay (`gemini_dead_model_migrated`) BAŞARILI yazımdan SONRA basılır: yazılamayan bir göçü
    # "göçtü" diye olaylamak, panoya gerçekleşmemiş bir onarım okuturdu. Sessiz değiştirme YASAK.
    gocen = None                                   # (eski, yeni) — olay yazım başarısına bağlı
    model_blk = cfg.get("model")
    if isinstance(model_blk, dict):
        eski_ad = str(model_blk.get("default") or "")
        yeni_ad = GEMINI_DEAD_MODEL_MAP.get(eski_ad)
        if yeni_ad:
            model_blk["default"] = yeni_ad
            gocen = (eski_ad, yeni_ad)
            changed.append(f"model.default({eski_ad}→{yeni_ad})")
    repo = _repo_root()
    guard = os.path.join(repo, "ops", "meridian-guard.sh")
    desired_mcp = {"command": sys.executable, "args": ["-m", "meridian.mcp_server"],
                   "env": {"PYTHONPATH": repo, "MERIDIAN_ROOT": repo},
                   "tools": {"resources": False, "prompts": False}}
    # MCP sunucusu
    servers = cfg.setdefault("mcp_servers", {}) if isinstance(cfg.get("mcp_servers", {}), dict) else {}
    cfg["mcp_servers"] = servers
    if servers.get("meridian") != desired_mcp:
        servers["meridian"] = desired_mcp
        changed.append("mcp_servers.meridian")
    # koruma hook'u (matcher: yazma/terminal araçları)
    desired_hook = [{"matcher": "terminal|write_file|patch|edit|apply_patch",
                     "command": guard, "timeout": 10}]
    hooks = cfg.setdefault("hooks", {}) if isinstance(cfg.get("hooks", {}), dict) else {}
    cfg["hooks"] = hooks
    if hooks.get("pre_tool_call") != desired_hook:
        hooks["pre_tool_call"] = desired_hook
        changed.append("hooks.pre_tool_call")
    # başsız (non-TTY) çağrıda first-use consent çalışmaz — koruma hook'u HER ZAMAN koşmalı. Tek hook
    # bizim ve config'i biz kontrol ediyoruz, o yüzden auto-accept güvenli (asıl savunma hook'un kendisi).
    if cfg.get("hooks_auto_accept") is not True:
        cfg["hooks_auto_accept"] = True
        changed.append("hooks_auto_accept")
    # prompt cache 1h
    pc = cfg.setdefault("prompt_caching", {}) if isinstance(cfg.get("prompt_caching", {}), dict) else {}
    cfg["prompt_caching"] = pc
    if pc.get("cache_ttl") != "1h":
        pc["cache_ttl"] = "1h"
        changed.append("prompt_caching.cache_ttl")
    # 429 rotasyon stratejisi (havuz olmadan zararsız; havuz gelince devreye girer)
    strat = cfg.setdefault("credential_pool_strategies", {}) \
        if isinstance(cfg.get("credential_pool_strategies", {}), dict) else {}
    cfg["credential_pool_strategies"] = strat
    for prov, mode in (("gemini", "round_robin"), ("anthropic", "least_used"),
                       ("openrouter", "round_robin")):
        if strat.get(prov) != mode:
            strat[prov] = mode
            changed.append(f"credential_pool_strategies.{prov}")
    # FALLBACK PROVIDER (#1, en yüksek kaldıraç): gemini free-tier 429 dolunca ajan boş dönüyordu ve TÜM
    # Tier 1+2 (dolgu/inceleme/MCP/kalibrasyon) uykuya geçiyordu. hermes fallback_providers 429'da OTOMATİK
    # devreye girer → Nous Portal'ın ÜCRETSİZ modeline düşer (operatörün kredisi yok, ücretsiz model şart).
    # Model secret'tan yapılandırılabilir; birincil sağlayıcı zaten nous ise fallback eklenmez (döngü olmaz).
    prim = (cfg.get("model") or {}).get("provider")
    if prim and prim != "nous":
        nous_model = secrets.get("NOUS_FALLBACK_MODEL") or "tencent/hy3:free"
        desired_fb = [{"provider": "nous", "model": nous_model}]
        if cfg.get("fallback_providers") != desired_fb:
            cfg["fallback_providers"] = desired_fb
            changed.append("fallback_providers")
    elif cfg.get("fallback_providers"):          # birincil nous'a döndüyse fallback'i temizle
        cfg.pop("fallback_providers")
        changed.append("fallback_providers(temizlendi)")
    if not changed:
        return {"ok": True, "changed": []}
    try:
        import shutil
        shutil.copy2(AGENT_CONFIG, AGENT_CONFIG + ".meridian.bak")
        # KAPI-DIŞI TAŞIMA: elle mkstemp+os.replace (fsync YOK, flock YOK) → store.write_text.
        # AGENT_CONFIG (~/.hermes/config.yaml) STATE DIŞI → mutlak ad, kendi kilidi. Biçim (safe_dump:
        # allow_unicode, default_flow_style=False, sort_keys=False) BİREBİR korunur — stream yerine string
        # döndürülüp aynı baytlar yazılır. .bak kopyası (shutil.copy2) manuel kurtarma anlık görüntüsüdür,
        # düz-yazım kapsamı DIŞINDA bilinçli bırakıldı (tam dosya kopyası, tek okuyucu operatör).
        # YASA-6 OKUYUCU: config_ensure_integrations (yeniden okur) + integrations_status + hermes-agent ikili.
        store.write_text(AGENT_CONFIG,
                         yaml.safe_dump(cfg, allow_unicode=True, default_flow_style=False, sort_keys=False))
        if gocen:
            # YASA-6 OKUYUCU: pano olay akışı (events.jsonl) + operatör teşhisi — göç görünür olmalı,
            # sessiz ad değiştirme yasak (aynı ilke: landing uydurma-rakam vakası, sabit≠gerçek).
            obs.log("gemini_dead_model_migrated", eski=gocen[0], yeni=gocen[1],
                    detail="yerel ajan config'indeki model adı Google listesinden kalkmış (üretim "
                           "404 sınıfı) — sabit alias'a taşındı; rol korundu (flash→flash-latest, "
                           "pro→pro-latest)")
        obs.log("agent_integrations_synced", changed=changed)
        return {"ok": True, "changed": changed}
    except Exception as e:
        return {"ok": False, "detail": f"yazılamadı ({type(e).__name__})"}


def integrations_status() -> dict:
    """Panel/teşhis için: hangi Hermes entegrasyonu canlı + görüş dolgusu iş listesi. Ucuz (yalnız
    config + state okur; ajan çağırmaz)."""
    import yaml
    out = {"mcp": False, "guard_hook": False, "prompt_cache": None, "pool_keys": {},
           "backfill_pending": 0, "fallback": None, "tool_use": None}
    try:
        with open(AGENT_CONFIG) as fh:
            cfg = yaml.safe_load(fh) or {}
        out["mcp"] = "meridian" in (cfg.get("mcp_servers") or {})
        out["guard_hook"] = any("meridian-guard" in (h.get("command") or "")
                                for h in (cfg.get("hooks", {}).get("pre_tool_call") or []))
        out["prompt_cache"] = (cfg.get("prompt_caching") or {}).get("cache_ttl")
        fb = cfg.get("fallback_providers") or []
        out["fallback"] = f"{fb[0]['provider']}·{fb[0]['model']}" if fb else None
    except Exception:  # sessiz-yutma: ağ/sağlayıcı hatası bu yolun NORMAL hâli; çağıran boş sonuç üzerinden yedek kaynağa düşer ve kaynak seçimi ayrıca kaydedilir
        pass
    try:
        # ÇAĞRI TELEMETRİSİ — YASA 6'nın DIŞ OKUYUCUSU BURASIDIR ve okuma bilerek
        # BURADA yapılır: `codelaw.artifact_graph` yalnız `store.read_jsonl(<sabit>)` çağrısını
        # görür, `agent_telemetry.ozet()`in içindeki okumayı göremez. Yani defteri "dış tüketicisi
        # var" yapan şey tam olarak bu satırdır — muafiyet değil, gerçek bir tüketici.
        # Bu alan `/api/hermes` gövdesinde AKAR; pano KARTI sonraki UI dalgasının işidir (bkz.
        # TASARIM-YONU, Öğrenme yüzeyi) — veri hazır, çizim henüz yok.
        out["agent_calls"] = _at.ozet(store.read_jsonl(_at.CAGRI_DEFTERI, limit=_at.OZET_ORNEK))
    except Exception as e:
        # YASA 4: sessizce atlanırsa pano "hiç ajan çağrısı yok" diye okur — oysa ölçüm okunamadı.
        obs.warn("agent_telemetry_ozet_unavailable", error=f"{type(e).__name__}: {e}",
                 detail="çağrı telemetrisi özeti ÜRETİLEMEDİ — alan yazılmadı (0 DEĞİL)")
    tu = store.read_json("agent_tooluse.json", None)          # #4: MCP araç kullanım oranı
    if tu and (tu.get("calls") or tu.get("olculemeyen")):
        # `olculemeyen` AYRI YAYINLANIR (`-Q` sonrası): sessiz mod oturum özetini
        # bastırdığı için araç sayısı okunamayan çağrılar var. Oranı onlarla seyreltmek uydurma,
        # onları hiç göstermemek ise donmuş bir sayacı "kullanılmadı" diye okutmak olurdu.
        out["tool_use"] = {"calls": tu.get("calls", 0), "with_tools": tu.get("with_tools", 0),
                           "total_tools": tu.get("total_tools", 0),
                           "olculemeyen": tu.get("olculemeyen", 0),
                           "rate": (round(tu.get("with_tools", 0) / tu["calls"], 2)
                                    if tu.get("calls") else None)}
    # havuz: sağlayıcı başına anahtar SAYISI + sağlığı (DEĞER YOK). Sağlık alanı sonradan eklendi:
    # "2 anahtar var" ile "2 anahtarın 2'si de tükenmiş" panoda aynı görünüyordu ve rotasyonun neden
    # işe yaramadığı hiçbir yerden okunamıyordu.
    health_ = pool_health()
    out["pool_keys"] = {p: h["keys"] for p, h in health_.items()}
    out["pool_health"] = health_
    out["pool_exhausted"] = _pool_exhausted()
    try:                                             # dolgu bekleyen: sonucu bilinen ama görüşsüz plan
        plans = store.read_jsonl("trade_plans.jsonl")
        trades = store.read_jsonl("trades.jsonl")
        oids = {str(t.get("plan_id")) for t in trades if t.get("r_multiple") is not None}
        out["backfill_pending"] = sum(1 for p in plans
                                      if "llm_opinion" not in p and str(p.get("id")) in oids)
    except Exception as e:
        # YASA 4: defter okuması düşerse alan HİÇ yazılmaz ve pano "dolgu bekleyen yok" gibi okur —
        # kalibrasyon borcu görünmez birikir (2026-07-21'de gate_checks'in 144/144 boş kalması ile
        # aynı desen: eksik alan, sıfır değeri gibi görünür).
        obs.warn("backfill_pending_unavailable", error=f"{type(e).__name__}: {e}")
    return out


AGENT_AUTH_FILE = os.path.expanduser("~/.hermes/auth.json")
POOL_EXHAUSTED_WINDOW_S = int(os.environ.get("HERMES_POOL_EXHAUSTED_WINDOW_S", "3600"))
# GÜNLÜK KOTA SIFIRLAMA SINIRI. Serbest katman kotası GÜNLÜKTÜR: her gün bu UTC
# saatinde yenilenir ve o andan itibaren dünkü tükenme işareti BUGÜN hakkında hiçbir şey söylemez.
# Saati koda gömmedik — sağlayıcıya göre değişir ve gömülü bir sayı yanlış sağlayıcıda SESSİZCE
# yanlış kalırdı; dosyadaki diğer sağlayıcı ayarlarıyla aynı desen (env ile taşınır).
POOL_QUOTA_RESET_UTC_HOUR = int(os.environ.get("HERMES_POOL_QUOTA_RESET_UTC_HOUR", "7"))
# Havuz satırı `last_status_at` TAŞIMIYORSA tükenmeyi İLK GÖRDÜĞÜMÜZ an buraya çivilenir. Eskiden
# zamansız işaret `_pool_exhausted`i SONSUZA DEK "tükenmiş" okutuyordu (`not last_status_at` dalı):
# kota her gün yenilenirken işaret hiç eskimiyor, hat 6 saatte bir kendini yeniden kilitliyordu.
POOL_SEEN_FILE = "pool_exhausted_seen.json"


def _quota_reset_epoch(now: float | None = None) -> float:
    """EN SON günlük kota-sıfırlama sınırı (epoch, UTC). Bu sınırdan ÖNCE konmuş bir tükenme
    işareti geçmiş bir kota penceresine aittir ve bugünkü bir karara girmemelidir."""
    now = time.time() if now is None else float(now)
    t = time.gmtime(now)
    boundary = float(calendar.timegm((t.tm_year, t.tm_mon, t.tm_mday,
                                      POOL_QUOTA_RESET_UTC_HOUR, 0, 0, 0, 0, 0)))
    return boundary if boundary <= now else boundary - 86400.0


def _pool_seen_at(prov: str, now: float) -> float:
    """Havuz tükenme işaretinin SON-TÜKENME-ZAMANI; havuz dosyası taşımıyorsa BİZİM ilk gözlem
    anımız çivilenir (bir kez yazılır, sonraki okumalar aynı anı döndürür)."""
    def _mut(cur):
        """İlk gözlem anını sağlayıcı adına BİR KEZ çiviler; kayıt varsa dokunmaz (False)."""
        if cur.get(prov):
            return False
        cur[prov] = now
        return True
    doc = store.update_json(POOL_SEEN_FILE, _mut, default={})
    try:
        return float(doc.get(prov) or now)
    except (TypeError, ValueError):  # sessiz-yutma: biçimsiz/eksik tek alan; yalnız bu değer düşer, satır başına uyarı asıl sinyali log seline gömerdi
        return now


def _pool_seen_clear(prov: str) -> None:
    """İşaret düştü (havuz sağlandı ya da pencere yenilendi) — çivi kaldırılır ki bir sonraki
    tükenme KENDİ zamanıyla damgalansın.

    ÖNCE KİLİTSİZ OKUMA: `_pool_exhausted` panonun her yoklamasında koşar ve SAĞLIKLI yol buradan
    geçer. Koşulsuz `update_json` her yoklamada bir kilit dosyası doğurup boşuna G/Ç yapardı —
    yazacak bir şey yokken kilit almak, ölçmediğimiz bir maliyeti sessizce ekler."""
    if not (store.read_json(POOL_SEEN_FILE, {}) or {}).get(prov):
        return
    store.update_json(POOL_SEEN_FILE, lambda cur: cur.pop(prov, None) is not None, default={})


def _pool_window_renewed() -> bool:
    """Ajan soğuması HAVUZ TÜKENMESİNDEN mi kuruldu ve o işaret son kota sıfırlamasından ÖNCE mi?

    Üç koşul da aranır ve üçü de ayrı bir yanlış-pozitifi kapatır: (i) soğumanın nedeni havuz
    tükenmesi değilse (ör. gerçek 429 merdiveni ya da başka bir ceza) DOKUNULMAZ; (ii) soğuma bu
    kota penceresi İÇİNDE kurulduysa taze bilgidir, yoklama yapılmaz; (iii) havuz ŞU AN hâlâ
    taze-tükenmiş diyorsa (bugün yeniden 429 yemiş) işaret geçerlidir."""
    row = (store.read_json(BRAIN_COOLDOWN_FILE, {}) or {}).get("agent") or {}
    if not str(row.get("reason") or "").startswith("pool_exhausted:"):
        return False
    try:
        kuruldu = float(row.get("until") or 0) - float(row.get("seconds") or 0)
    except (TypeError, ValueError):  # sessiz-yutma: biçimsiz/eksik tek alan; yalnız bu değer düşer, satır başına uyarı asıl sinyali log seline gömerdi
        return False
    if not kuruldu or kuruldu > _quota_reset_epoch():
        return False
    return _pool_exhausted() is None


def pool_health() -> dict:
    """Kimlik havuzunun SAĞLIĞI — sağlayıcı başına {keys, exhausted, healthy, last_error_code}.
    ASLA anahtar/token DEĞERİ okunmaz, dönülmez, loglanmaz: yalnız sayı ve durum etiketi. Bu dosya
    açık metin kimlik taşır; buradan dışarı çıkan tek şey sayaçlardır."""
    out: dict[str, dict] = {}
    try:
        with open(AGENT_AUTH_FILE) as fh:
            auth = json.load(fh) or {}
    except Exception:  # sessiz-yutma: yardımcı G/Ç yolu; çağıran yokluğu zaten yedek değerle karşılıyor ve asıl okuma hatası store katmanında bir kez uyarılıyor
        return out
    for prov, keys in (auth.get("credential_pool") or {}).items():
        if not isinstance(keys, list):
            continue
        rows = [k for k in keys if isinstance(k, dict)]
        bad = [k for k in rows if str(k.get("last_status")) == "exhausted"
               or int(k.get("last_error_code") or 0) == 429]
        newest = max((float(k.get("last_status_at") or 0) for k in bad), default=0.0)
        out[str(prov)] = {"keys": len(keys), "exhausted": len(bad), "healthy": len(keys) - len(bad),
                          "last_error_code": next((k.get("last_error_code") for k in bad
                                                   if k.get("last_error_code")), None),
                          "last_status_at": newest or None}
    return out


def _agent_provider() -> str | None:
    """Yerel ajanın YAPILANDIRILMIŞ sağlayıcısı. Kritik teşhis: burada 'gemini' yazıyordu, yani beyin
    zincirinin 'nous' ayağı ile 'gemini' ayağı AYNI üst-akış kotasına bakıyordu — yedek sağlayıcı,
    tükenmiş kimliğin ikinci adıydı ve elbette 429'u absorbe edemedi."""
    try:
        import yaml
        with open(AGENT_CONFIG) as fh:
            return ((yaml.safe_load(fh) or {}).get("model") or {}).get("provider")
    except Exception:  # sessiz-yutma: yardımcı G/Ç yolu; çağıran yokluğu zaten yedek değerle karşılıyor ve asıl okuma hatası store katmanında bir kez uyarılıyor
        return None


def _pool_exhausted() -> str | None:
    """Ajanın sağlayıcısının havuzunda kullanılabilir TEK bir kimlik kalmadıysa sağlayıcı adı, yoksa
    None. Tükenme işareti İKİ ölçütü birden geçmelidir: (1) yakın geçmişte konmuş olmalı (pencere),
    (2) İÇİNDE BULUNDUĞUMUZ kota penceresine ait olmalı — yani son günlük sıfırlamadan SONRA.

    (2) SONRADAN eklendi (canlı, 2026-08-04): dünkü işaret sıfırlamadan sonra da 'tükenmiş' okunuyor,
    taze kota penceresi HİÇ denenmeden yedek modele düşülüyordu. Zamansız işaret (havuz satırında
    `last_status_at` yok) daha da kötüsüydü: eski kod onu SONSUZA dek tükenmiş sayıyordu. Artık
    ölçülemeyen zaman uydurulmaz da yok sayılmaz da — ilk gözlem anı çivilenir ve o eskir."""
    prov = _agent_provider()
    h = pool_health().get(str(prov or ""), None)
    if not h or not h.get("keys") or h.get("healthy") or not h.get("exhausted"):
        if prov:
            _pool_seen_clear(str(prov))
        return None
    now = time.time()
    try:
        seen = float(h.get("last_status_at") or 0)
    except (TypeError, ValueError):  # sessiz-yutma: biçimsiz/eksik tek alan; yalnız bu değer düşer, satır başına uyarı asıl sinyali log seline gömerdi
        seen = 0.0
    seen = seen or _pool_seen_at(str(prov), now)
    if seen <= _quota_reset_epoch(now) or now - seen >= POOL_EXHAUSTED_WINDOW_S:
        _pool_seen_clear(str(prov))       # işaret bayat: bir sonraki tükenme kendi zamanıyla damgalanır
        return None
    return str(prov)


def register_pool_key(provider: str, api_key: str, label: str = "meridian") -> dict:
    """Kimlik havuzuna bir yedek anahtar ekler (hermes auth add) — aynı sağlayıcı 429/kota yerse ajan
    otomatik rotasyonla ayakta kalır (gemini free-tier boş-oturum sorununun çözümü). Anahtar değeri
    loglanmaz. provider ör. 'gemini'|'anthropic'|'openrouter'. Dönüş: {ok, detail}."""
    import subprocess
    bin_ = _hermes_bin()
    if not bin_:
        return {"ok": False, "detail": "yerel hermes-agent kurulu değil"}
    if not (provider and api_key):
        return {"ok": False, "detail": "provider ve anahtar gerekli"}
    try:
        r = subprocess.run([bin_, "auth", "add", provider, "--type", "api-key",
                            "--api-key", api_key, "--label", label],
                           capture_output=True, text=True, timeout=30)
        ok = r.returncode == 0
        obs.log("pool_key_registered", provider=provider, ok=ok)   # anahtar DEĞERİ yok
        return {"ok": ok, "detail": "havuz anahtarı eklendi" if ok
                else f"eklenemedi: {(r.stderr or '').strip()[-120:]}"}
    except Exception as e:
        return {"ok": False, "detail": f"hata ({type(e).__name__})"}


def _agent_skill_plani(repo: str, enabled: set) -> tuple[list, list]:
    """Ajan skill dizininde YAPILACAK değişikliğin PLANI: (bağlanacak, sökülecek). UYGULAMAZ.

    NEDEN AYRI FONKSİYON (2026-08-13): kum havuzu yolu "ne OLURDU"yu deftere yazmak zorunda
    (aşağıda, fail-visible) ama uygulamamalı. Planı `sync_agent_skills` içinde bir kez, burada bir
    kez yazmak `_kur_kum_havuzu`nun kendi gerekçesindeki hatanın aynısı olurdu — aynı yasanın iki
    uygulaması sessizce ayrışır ve ayrışan taraf ölçümü yalanlar. Tek tarama, iki tüketici."""
    baglanacak, sokulecek = [], []
    for name in sorted(enabled):
        if os.path.isdir(os.path.join(repo, name)) and not os.path.exists(os.path.join(AGENT_SKILLS_DIR, name)):
            baglanacak.append(name)
    if not os.path.isdir(AGENT_SKILLS_DIR):
        return baglanacak, sokulecek                   # dizin YOK: sökülecek bir şey de yok
    kok = os.path.realpath(repo)
    for entry in sorted(os.listdir(AGENT_SKILLS_DIR)):
        dst = os.path.join(AGENT_SKILLS_DIR, entry)
        if not os.path.islink(dst):
            continue                                   # ajanın kendi dizinleri — dokunma
        try:
            target = os.path.realpath(dst)
        except OSError:  # sessiz-yutma: yardımcı G/Ç yolu; çağıran yokluğu zaten yedek değerle karşılıyor ve asıl okuma hatası store katmanında bir kez uyarılıyor
            continue
        if target.startswith(kok) and entry not in enabled:
            sokulecek.append(entry)
    return baglanacak, sokulecek


def _agent_bagli_toplam(enabled: set) -> int:
    """ENABLED setinin kaçı ajan dizinine FİİLEN bağlı? (olayın `kapsam` alanının paydası).

    `agent_skill_coverage()`ten AYRI durur ve bu bilinçli: o fonksiyon `skills.catalog()`u kendi
    çağırır (kayıt defteri + atıf analitiği), yani senkron yolunda ikinci kez ödenecek bir maliyet.
    Burada `enabled` zaten elimizde; tek `listdir` yeter."""
    if not os.path.isdir(AGENT_SKILLS_DIR):
        return 0
    bagli = {e for e in os.listdir(AGENT_SKILLS_DIR)
             if os.path.islink(os.path.join(AGENT_SKILLS_DIR, e))}
    return len(enabled & bagli)


def sync_agent_skills() -> dict:
    """Yerel ajanın skill seti = Meridian'ın ENABLED seti — birebir. İki yönde eşitler:
    (1) etkin olup linklenmemiş skill'ler symlink'lenir; (2) Meridian'ın DEVRE DIŞI bıraktığı ya da
    silinen skill'lerin linkleri sökülür (canlıda yakalanan kusur: 8 kapalı skill ajanda hâlâ
    aktifti — motorun 'kenar yok' dediği bilgiyle ajan düşünmeye devam ediyordu). YALNIZ bizim
    repoya çözümlenen symlink'lere dokunulur — ajanın kendi builtin klasörleri kutsaldır.

    KUM HAVUZU BU DİZİNE YAZMAZ (2026-08-13 — ölçülmüş sızıntının kapatılması). `AGENT_SKILLS_DIR`
    HOST GENELİNDE TEK ve PAYLAŞIMLIDIR; sprint kum havuzu ise kendi (anahtarsız) enabled setini
    hesaplar ve o setle canlının symlink'lerini söküyordu — kanıt, mekanizma ve zincir
    `sprint.kum_havuzunda` üstünde yazılı. İKİ ONARIM YOLU VARDI ve seçim ÖLÇÜLEBİLİRLİĞE göre
    yapıldı:
      (A) SPRINT'E KENDİ DİZİNİNİ VER — bu tur reddedildi, ama İMKÂNSIZ OLDUĞU İÇİN DEĞİL.
          ÖLÇÜLDÜ, VARSAYILMADI (yerel hermes-agent kaynağı v0.18.2, 2026-08-13):
            `tools/skill_usage.py:81` `_skills_dir() = get_hermes_home() / "skills"`
            `hermes_constants.py:56-67` `HERMES_HOME` env değişkeni VARSA o, yoksa `~/.hermes`.
          Yani skill dizinini taşımanın bir kolu GERÇEKTEN var. Bedeli şu: `HERMES_HOME` skill
          dizinini değil TÜM ajan evini taşır — `auth.json` (kimlik havuzu), `config.yaml`
          (MCP/hook/model), `logs/`, `sessions/`. Boş bir eve işaret eden sprint'in ajan çağrıları
          KİMLİKSİZ ve YAPILANDIRMASIZ kalır ve tamamı düşer; yani "izolasyon" adına sprint'in
          ölçüm yolunu kapatmış olurduk. Çalışması için yeni evin auth/config'inin de bağlanması
          (ve üçüncü-taraf ev düzeninin bizim sözleşmemiz hâline gelmesi) gerekir — bu ayrı bir
          karardır ve canlı bir sprint koşumuyla doğrulanmadan alınmamalıdır (Rol-1'e kalan kalem).
      (B) KUM HAVUZU PAYLAŞIMLI DİZİNİ DEĞİŞTİRMEZ — seçildi. Yerel, BURADAN sınanabilir ve canlı
          davranışı AYNEN korur. Kum havuzunun ajan çağrıları da bozulmaz: `-s` listesi zaten KUM
          HAVUZUNUN KENDİ enabled setinden süzülür (`_skill_preload`), yani sandbox kapalı saydığı
          bir skill'i hiçbir zaman yüklemez — sökmesi de zaten gereksizdi. (B) (A)'nın ÖNÜNÜ
          KAPATMAZ: ayrı ev bir gün kurulursa bu kapı zararsız bir no-op'a döner.
    BAĞLAMA da yapılmaz, yalnız sökme değil: bağlama da PAYLAŞIMLI dizinin mutasyonudur ve kum havuzu
    canlının kapattığı bir skill'i açık sayarsa (mutasyon sprint'i) onu canlı ajanın kataloğuna
    SOKARDI — `sync_agent_skills`in var oluş sebebinin tam tersi. Atlama SESSİZ DEĞİLDİR: gerçekten
    bir değişiklik engellendiyse olay ADIYLA ve NE OLURDU listesiyle yazılır."""
    from . import skills as _sk
    from . import sprint as _sp
    repo = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "skills")
    enabled = {s2["name"] for s2 in _sk.catalog() if s2.get("enabled")}
    kum = _sp.kum_havuzunda()
    if not kum:
        os.makedirs(AGENT_SKILLS_DIR, exist_ok=True)   # kum havuzunda DİZİN BİLE yaratılmaz
    baglanacak, sokulecek = _agent_skill_plani(repo, enabled)
    if kum:
        if baglanacak or sokulecek:
            obs.warn("agent_skills_sync_atlandi_kum_havuzu", enabled=len(enabled),
                     olurdu_baglanacak=baglanacak[:10], olurdu_sokulecek=sokulecek[:10],
                     n_baglanacak=len(baglanacak), n_sokulecek=len(sokulecek),
                     dizin=AGENT_SKILLS_DIR,
                     detail="sprint kum havuzu PAYLAŞIMLI ajan skill dizinine yazmaz (v242) — bu "
                            "senkron ATLANDI. Kum havuzunun enabled seti canlınınkinden KÜÇÜKTÜR "
                            "(sandbox'ta sağlayıcı anahtarı yok), yani uygulansaydı canlı ajanın "
                            "kataloğundan skill SÖKÜLÜRDÜ (2026-08-13 vakası: dört `fmp=req` skill). "
                            "Kum havuzunun kendi çağrıları etkilenmez: `-s` listesi zaten kum "
                            "havuzunun kendi enabled setinden süzülüyor.")
        return {"enabled": len(enabled), "yeni_baglanan": [], "pruned": [],
                "atlandi": "kum_havuzu", "olurdu_baglanacak": baglanacak,
                "olurdu_sokulecek": sokulecek}
    linked, pruned = [], []
    for name in baglanacak:
        try:
            os.symlink(os.path.join(repo, name), os.path.join(AGENT_SKILLS_DIR, name))
            linked.append(name)
        except OSError:  # sessiz-yutma: yardımcı G/Ç yolu; çağıran yokluğu zaten yedek değerle karşılıyor ve asıl okuma hatası store katmanında bir kez uyarılıyor
            pass
    for entry in sokulecek:
        try:
            os.unlink(os.path.join(AGENT_SKILLS_DIR, entry)); pruned.append(entry)
        except OSError:  # sessiz-yutma: yardımcı/telemetri yolu; başarısızlığı karara girmez ve çağıran yedek değerle aynen devam eder
            pass
    # ALAN ADI DEĞİŞTİ: `linked` → `yeni_baglanan` (2026-08-13). ESKİ AD YANILTIYORDU ve bunun
    # ÖLÇÜLMÜŞ bir bedeli var: `linked` bu olayda "O SENKRONDA YENİ KURULAN symlink sayısı" demekti,
    # ama `agent_skill_coverage()` AYNI SÖZCÜĞÜ "enabled ∩ bağlı TOPLAMI" anlamında kullanıyor (pano
    # onu öyle okuyor ve orada doğru). Aynı ad, iki anlam → canlı `linked: 4` satırını okuyan denetim
    # "30 enabled'ın yalnız 4'ü bağlı" sandı (docs/DENETIM-SKILL-CAGRI-IZI-2026-08-13.md).
    # Çare yalnız yeniden adlandırma değil: TOPLAM KAPSAM da aynı satıra yazılır, böylece olayı tek
    # başına okuyan birinin ikinci bir yere bakması gerekmez. `yeni_baglanan_adlar` `pruned` ile
    # simetriktir — söküleni adıyla yazıp bağlananı sayıyla yazmak, iki yönü asimetrik okuturdu.
    bagli_toplam = _agent_bagli_toplam(enabled)
    out = {"enabled": len(enabled), "yeni_baglanan": linked, "pruned": pruned,
           "bagli_toplam": bagli_toplam}
    if linked or pruned:
        obs.log("agent_skills_synced", enabled=len(enabled),
                yeni_baglanan=len(linked), yeni_baglanan_adlar=linked[:10], pruned=pruned[:10],
                bagli_toplam=bagli_toplam, kapsam=f"{bagli_toplam}/{len(enabled)}")
    return out


def agent_skill_coverage() -> dict:
    """Panel için: enabled set ↔ ajan linkleri kapsamı (eksik/bayat görünür olsun).

    BURADAKİ `linked` = enabled ∩ bağlı TOPLAMI (pano bunu böyle okur ve doğrudur). `agent_skills_synced`
    OLAYINDAKİ aynı sözcük 2026-08-13'e kadar "o senkronda YENİ kurulan" demekti ve çakışma bir denetimi
    yanlış okuttu; olay tarafı `yeni_baglanan`a çevrildi (gerekçe `sync_agent_skills` içinde). Bu ad
    DEĞİŞMEDİ çünkü tüketicisi `meridian/web/app.js` ve orada anlamı zaten toplamdır."""
    from . import skills as _sk
    enabled = {s2["name"] for s2 in _sk.catalog() if s2.get("enabled")}
    linked = set()
    if os.path.isdir(AGENT_SKILLS_DIR):
        linked = {e for e in os.listdir(AGENT_SKILLS_DIR)
                  if os.path.islink(os.path.join(AGENT_SKILLS_DIR, e))}
    return {"enabled": len(enabled), "linked": len(enabled & linked),
            "missing": sorted(enabled - linked)[:5], "stale_linked": len(linked - enabled)}


def _skill_preload(kind: str, setups: tuple = ()) -> list:
    """Çağrı türüne göre -s ön-yükleme listesi (ajanın TÜM enabled seti zaten erişilebilir —
    ön-yükleme yalnız en ilgili bilgiyi bağlama sabitler; tavan 8, bağlam şişmez)."""
    from . import skills as _sk
    names = []
    if kind == "review" or kind == "explore":
        names += [_sk.screener_for(su) for su in setups]
        names += list(REVIEW_SKILLS)
        # #5 verimlilik: kürasyon dışında KANITLA iyi (gerçek n>=5, avg_r>0) skill'ler de aday havuzuna
        # girsin — yoksa aşağıdaki skor-sıralaması yalnız REVIEW_SKILLS içinden seçer, ölçülmüş kazananlar
        # (ör. yüksek avg_r'li bir screener) hiç önyüklenmezdi. Tavan yine 8; sadece havuz zenginleşir.
        try:
            from . import analytics as _an5
            winners = sorted((a for a in _an5.skill_attribution().get("skills", [])
                              if (a.get("n") or 0) >= 5 and (a.get("avg_r") or 0) > 0),
                             key=lambda a: -(a.get("avg_r") or 0))[:4]
            names += [a["skill"] for a in winners]
        except Exception:  # sessiz-yutma: geç bağlanan yardımcı modül/çağrı; asıl karar bu değere bağlı değil ve çağıran yokluğu yedek değerle karşılıyor
            pass
    else:                                              # proposal: KÜRATÖRLÜ çekirdek (alfabetik kategori
        # taraması 'edge-*' ailesine 8 slotu kaptırıyordu — rejim/kapı/çıkış bilgisi dışarıda kalmıştı),
        # kalan slotlar kategori önceliğiyle dolar.
        names += ["backtest-expert", "market-environment-analysis", "pre-trade-discipline-gate",
                  "position-sizer", "macro-regime-detector", "portfolio-manager",
                  "market-breadth-analyzer", "edge-strategy-reviewer"]
        prio = ("strategy-research", "market-analysis", "risk-management")
        cat = {s2["name"]: s2 for s2 in _sk.catalog() if s2.get("enabled")}
        names += [n for p2 in prio for n, i2 in sorted(cat.items()) if i2.get("category") == p2]
    seen, out = set(), []
    enabled = {s2["name"] for s2 in _sk.catalog() if s2.get("enabled")}
    # katalog boşsa (taze sandbox/kurulum) süzgeci atla — istenen adlara güven; katalog varken
    # devre-dışı skill ASLA yüklenmez (canlı davranış).
    known = enabled if enabled else set(filter(None, names))
    for n in names:
        if n and n in known and n not in seen:
            seen.add(n); out.append(n)
    # #4 KANIT-GÜDÜMLÜ SIRALAMA: ölçülmüş katkı varken kürasyon ölçüme yerini bırakır. Skor =
    # gerçek ort.R (n>=5) yoksa 0.5·cf ort.R (n_cf>=10) yoksa 0 (ölçüsüzler kürasyon sırasını korur —
    # kararlı sıralama). Ölçülmüş-kötü (gerçek n>=10, ort.R<=-0.15) ön-yüklemeden DÜŞER (ajan yine
    # erişebilir; yalnız bağlam slotu harcanmaz). Çekirdek üçlü asla düşmez.
    CORE = {"pre-trade-discipline-gate", "position-sizer", "backtest-expert"}
    try:
        from . import analytics as _an
        attr = {a["skill"]: a for a in _an.skill_attribution().get("skills", [])}
    except Exception:  # sessiz-yutma: geç bağlanan yardımcı modül/çağrı; asıl karar bu değere bağlı değil ve çağıran yokluğu yedek değerle karşılıyor
        attr = {}
    def _score(n):
        """Skill'in kanıt skoru: ölçülmüş gerçek ort.R (n≥5), yoksa 0,5 × cf ort.R (n_cf≥10),
        yoksa 0,0 — ölçüsüzler kürasyon sırasını korur."""
        a = attr.get(n) or {}
        if (a.get("n") or 0) >= 5 and a.get("avg_r") is not None:
            return float(a["avg_r"])
        if (a.get("n_cf") or 0) >= 10 and a.get("cf_avg_r") is not None:
            return 0.5 * float(a["cf_avg_r"])
        return 0.0
    def _bad(n):
        """ÖLÇÜLMÜŞ-KÖTÜ mü: gerçek n≥10 ve ort.R ≤ −0,15. Çekirdek üçlü asla kötü sayılmaz
        (ön-yüklemeden düşmez); eleme yalnız bağlam slotunu boşaltır, ajan skill'e yine erişir."""
        a = attr.get(n) or {}
        return n not in CORE and (a.get("n") or 0) >= 10 and (a.get("avg_r") or 0) <= -0.15
    out = [n for n in out if not _bad(n)]
    # ÇEKİRDEK KIRPMAYA DA DAYANIR: eskiden CORE yalnız _bad() elemesinden korunuyordu,
    # sıralama+kırpmadan DEĞİL. Gerçek kanıt birikip ölçülen ort.R hafif negatife düşünce
    # (pre-trade-discipline-gate ve position-sizer: -0.054) çekirdek ikili listenin dibine kaydı ve
    # out[:8] onları sessizce attı — ajan disiplin kapısı ve pozisyon boyutlandırıcı olmadan
    # düşünmeye başladı. Ölçüm çekirdeği sıralar, ama listeden ÇIKARAMAZ.
    out.sort(key=lambda n: -_score(n))
    top = out[:8]
    # Ölçüm SIRALAR, ama çekirdeği listeden ÇIKARAMAZ: eksik kalan her çekirdek üye, en düşük
    # skorlu çekirdek-dışı üyenin yerine geçer. Sıra ölçüme ait; varlık garantisi çekirdeğe.
    for n in (n for n in out if n in CORE and n not in top):
        disposable = [m for m in reversed(top) if m not in CORE]
        if not disposable:
            break
        top[top.index(disposable[0])] = n
    return top


def _warn_review_empty(asama: str, text: str, raw: str, *, parse_ok: bool,
                       ham: list, reviews: list, detail: str) -> None:
    """İKİNCİ GÖRÜŞÜN İKİ SESSİZ ÖLÜM NOKTASI TEK OLAYA BAĞLANIR (2026-08-02 canlı vakası).

    `review_candidates` cevabı kaydedemeden döndüğünde eskiden HİÇBİR iz kalmıyordu: çağıran
    (`review_candidates_async._bg`) yalnız istisna yolunu görüyordu, ham metin kayboluyordu ve
    "Gemini dolu cevap verdi ama kayıt yok" teşhis EDİLEMİYORDU. Bu yardımcı, kayıtsız-dönüşün
    HER yolunu (`asama`) aynı olay adıyla, ayırt edici alanlarla basar — davranışı değiştirmez.
    `ham_ilk`: model cevabının ilk 220 karakteri (sır değil — bizim metnimiz değil, modelin
    cevabı); repr ile tek satıra düzleştirilir ki defter satırı bölünmesin."""
    reddedilen = []
    for r in ham:
        if any(r is ok for ok in reviews):
            continue
        v = r.get("opinion") if isinstance(r, dict) else f"<{type(r).__name__}>"
        reddedilen.append(str(v)[:40])
        if len(reddedilen) >= 5:
            break
    obs.warn("candidate_review_empty_parse", asama=asama,
             text_len=len(text or ""), extract_len=len(raw or ""), parse_ok=bool(parse_ok),
             on_filtre_n=len(ham), son_filtre_n=len(reviews), reddedilen_gorusler=reddedilen,
             ham_ilk=repr((text or "")[:220]), detail=detail)


# ================================================================================================
# ADAY İNCELEME SIKIŞIKLIK DEFTERİ — canlı vaka: 2026-07-31'den beri backlog
# aynı tarihi 5 dakikada bir deniyor, model zinciri cevapsız, günlük 150'lik ajan RPD bütçesinin
# TAMAMI review'e yanıyordu (08-06/07/08 ölçümü: 75 deneme × 2 model = 150 çağrı, 19:21'de
# `agent_budget_exhausted`, gün sonuna dek sessizlik) ve `candidate_review*` ailesi 08-02'den beri
# TEK OLAY basmamıştı — başarısızlık `text is None` erken-dönüşünde olaysız yutuluyordu.
# Defter üç şeyi kalıcılaştırır ve HEPSİ candidate_review.json'ın `backlog` anahtarında yaşar
# (YASA-6 okuyucu zinciri hazır: api.py /api/candidates dosyayı OLDUĞU GİBİ panoya servis eder;
# ayrıca review_backlog her turda okur — ayrı dosya codelaw DECLARED_SINKS beyanı gerektirirdi):
#   tamam     — hangi seanslar GERÇEK görüş aldı (tek `date` işaretçisi çok-tarih izleyemiyordu;
#               08-06 başarısı 08-07'yi yeniden hedef yapardı — sonsuz sarkaç).
#   gecersiz  — N gerçek denemede görüş üretilemeyen seansların KALICI işareti (tarih+neden+deneme);
#               kalibrasyon defteri boşluğu dürüstçe işaretli kalır, sahte review üretilmez ve
#               backlog SONRAKİ görüşsüz tarihe ilerler (en-yeni-tarih donması biter).
#   denemeler — tarih başına ardışık başarısızlık sayacı + üstel geri-çekilme penceresi
#               (taban 300 sn, her başarısızlıkta ×2, tavan 3600 sn): 5 dakikalık scheduler
#               kadansı korunur ama başarısız tarih için süreç doğurma hızı saatte 1'e iner —
#               olay gürültüsü makullük bekçisini beslemez, RPD bütçesi öneri yoluna kalır.
# N=12 GEREKÇESİ ve SAYIM KURALI: eşik `n_llm` üzerinden işler — yalnız ajan katmanının GERÇEKTEN
# koşup görüş üretemediği denemeler sayılır (agent_bos/json_parse/filtre/plan_yok). Soğuma/bütçe
# reddi/ikili-yokluğu (`agent_cagri_yok`/`ikili_yok`) sayılMAZ: modele hiç sorulmamış bir tarihi
# "incelenemez" ilan etmek ölçülmemiş hüküm olurdu (UYDURMA YASAĞI). 12 gerçek deneme, üstel
# geri-çekilmeyle ≤ ~1 gün duvar saati ve ≤ 24 alt-süreç eder (eski spin: günde 150) — parse
# tesadüflerine cömert, bütçeye merhametli.
# ================================================================================================
REVIEW_GECERSIZ_N = int(os.environ.get("MERIDIAN_REVIEW_GECERSIZ_N", "12"))
REVIEW_BEKLEME_TABAN_S = int(os.environ.get("MERIDIAN_REVIEW_BEKLEME_TABAN_S", "300"))
REVIEW_BEKLEME_TAVAN_S = int(os.environ.get("MERIDIAN_REVIEW_BEKLEME_TAVAN_S", "3600"))
REVIEW_BACKLOG_PENCERE = 5          # onarım geçidiyle aynı ufuk: son 5 seans telafi kapsamında
_REVIEW_LLM_ASAMALARI = frozenset({"agent_bos", "json_parse", "filtre", "plan_yok"})
_REVIEW_DEFTER_TAVAN = 24           # tamam/gecersiz/denemeler haritaları en yeni 24 tarihle sınırlı


def _review_backlog_defteri(doc: dict | None = None) -> dict:
    """candidate_review.json içindeki `backlog` anahtarını üç haritasıyla normalize eder.
    `doc` verilirse (update_json mutator'ı içinden) diskten İKİNCİ kez okumaz."""
    src = doc if doc is not None else (store.read_json("candidate_review.json", {}) or {})
    bl = (src.get("backlog") or {}) if isinstance(src, dict) else {}
    return {"tamam": dict(bl.get("tamam") or {}),
            "gecersiz": dict(bl.get("gecersiz") or {}),
            "denemeler": dict(bl.get("denemeler") or {})}


def _review_bekleme_s(n: int) -> int:
    """Ardışık n. başarısızlıktan sonraki bekleme: taban·2^(n-1), tavanlı. n=1 → 300 sn (mevcut
    5 dk kadansıyla aynı — ilk tekrar cezasız), n≥5 → 3600 sn."""
    return int(min(REVIEW_BEKLEME_TABAN_S * (2 ** max(0, int(n) - 1)), REVIEW_BEKLEME_TAVAN_S))


def _review_defteri_buda(defter: dict) -> None:
    """Haritaları en yeni _REVIEW_DEFTER_TAVAN tarihle sınırla — dosya panoya olduğu gibi servis
    edilir (api /api/candidates), sınırsız büyüme HTTP gövdesini şişirirdi. ISO tarih anahtarları
    sözlükçe sıralanabilir; en eskiler düşer."""
    for ad in ("tamam", "gecersiz", "denemeler"):
        m = defter.get(ad) or {}
        if len(m) > _REVIEW_DEFTER_TAVAN:
            for k in sorted(m)[:-_REVIEW_DEFTER_TAVAN]:
                m.pop(k, None)


def _agent_gun_sayaci() -> int:
    """RPD gün sayacının anlık değeri — `_agent_call` öncesi/sonrası kıyası, alt sürecin GERÇEKTEN
    koşup koşmadığının ölçülmüş imzasıdır (koşum = düşüm; ağa çıkmayan koşumlar iade edilir, yani
    fark 0 kalır ve `agent_cagri_yok` sınıfına düşer — tahmin değil, bütçe defterinin kendisi)."""
    return int((store.read_json(AGENT_BUDGET_FILE, {}) or {}).get("day") or 0)


def _review_deneme_isle(day: str, asama: str) -> dict:
    """Başarısız inceleme denemesini deftere işler: ardışık sayaç + geri-çekilme penceresi +
    (eşikte) kalıcı `gecersiz` işareti. Kilitli oku-değiştir-yaz; dönüş güncel kayıt + gecersiz
    bayrağı. Olay basmaz — basan `_review_atla` (defter ve olay ayrı sorumluluk)."""
    import time as _t
    sonuc: dict = {}

    def _isle(doc):
        """Kilitli mutasyon: o günün deneme sayacını (toplam + LLM) artırır, geri-çekilme
        penceresini yeniden hesaplar ve LLM denemesi `REVIEW_GECERSIZ_N`e ulaştıysa günü kalıcı
        `gecersiz` işaretine taşıyıp deneme satırını düşürür."""
        defter = _review_backlog_defteri(doc)
        rec = dict(defter["denemeler"].get(day) or {"n": 0, "n_llm": 0, "ilk_ts": memory.now_iso()})
        rec["n"] = int(rec.get("n") or 0) + 1
        if asama in _REVIEW_LLM_ASAMALARI:
            rec["n_llm"] = int(rec.get("n_llm") or 0) + 1
        rec["son_asama"] = asama
        rec["son_ts"] = memory.now_iso()
        rec["bekleme_s"] = _review_bekleme_s(rec["n"])
        rec["sonraki_epoch"] = round(_t.time() + rec["bekleme_s"], 1)
        gecersiz = int(rec.get("n_llm") or 0) >= REVIEW_GECERSIZ_N
        if gecersiz:
            defter["gecersiz"][day] = {"neden": asama, "deneme": rec["n"],
                                       "deneme_llm": rec["n_llm"], "ilk_ts": rec.get("ilk_ts"),
                                       "ts": rec["son_ts"]}
            defter["denemeler"].pop(day, None)     # işaret kalıcı — sayaç görevini tamamladı
        else:
            defter["denemeler"][day] = rec
        _review_defteri_buda(defter)
        doc["backlog"] = defter
        sonuc.update(rec, gecersiz=gecersiz)
        return True

    store.update_json("candidate_review.json", _isle, {})
    if sonuc.get("gecersiz"):
        obs.warn("candidate_review_gecersiz", date=day, neden=asama,
                 deneme=sonuc.get("n"), deneme_llm=sonuc.get("n_llm"),
                 detail=f"{REVIEW_GECERSIZ_N} gerçek denemede görüş üretilemedi — seans kalıcı "
                        f"'review_gecersiz' işaretlendi (son aşama: {asama}). Kalibrasyon defteri "
                        f"boşluğu dürüstçe açık kalır; sahte review yazılmaz, backlog sonraki "
                        f"görüşsüz seansa ilerler.")
    return sonuc


def _review_atla(day: str | None, asama: str, *, uyari: bool, detail: str, **alanlar) -> None:
    """KAYITSIZ DÖNÜŞ YASAĞI: `review_candidates` görüş KAYDEDEMEDEN döndüğü her yol buradan
    geçer — önce defter (deneme sayacı/geri-çekilme/gecersiz eşiği), sonra olay. Tarih bilinmiyorsa
    (hiç plan yok) defter atlanır ama olay yine basılır: sessiz yol kalmaz."""
    rec = _review_deneme_isle(day, asama) if day else {}
    (obs.warn if uyari else obs.log)(
        "candidate_review_skipped", date=day, asama=asama,
        deneme=rec.get("n"), deneme_llm=rec.get("n_llm"), bekleme_s=rec.get("bekleme_s"),
        detail=detail, **alanlar)


def review_candidates(dstr: str | None = None) -> dict | None:
    """ADAY DANIŞMA KATMANI — yerel ajan (skill kütüphanesiyle) bugünün adaylarına İKİNCİ GÖRÜŞ verir.
    YETKİ SINIRI: bu inceleme yalnız bilgilendirir; kapı kararlarını (GO/REVIEW/NO_GO), silahlanmayı
    veya emirleri ASLA değiştirmez — 'aday seçimi LLM'e' isteği bilinçli olarak danışman olarak bağlandı,
    çünkü seçim otoritesini LLM'e vermek deterministik kapı yasasını delerdi. İlgili Meridian skill'leri
    oturuma önceden yüklenir (-s); sonuç state/candidate_review.json'a atomik yazılır, Adaylar sayfası
    gösterir. Yerel ajan yoksa/hata verirse None döner ama ASLA SESSİZCE DEĞİL: her kayıtsız
    dönüş `candidate_review_skipped`/`candidate_review_empty_parse` basar ve sıkışıklık defterine
    (backlog anahtarı) işlenir — 2026-07-31→08-08 canlı vakasında `text is None` yolu 10 gün boyunca
    olaysız yutmuş, aile 08-02'den beri tek satır konuşmamıştı."""
    import subprocess
    plans = store.read_jsonl("trade_plans.jsonl")
    day = dstr or max([p.get("date") for p in plans if p.get("date")], default=None)
    todays = [p for p in plans if p.get("date") == day]
    bin_ = _hermes_bin()
    if not bin_:
        _review_atla(day, "ikili_yok", uyari=True,
                     detail="yerel hermes CLI bulunamadı (HERMES_LOCAL_BIN → PATH → ~/.hermes) — "
                            "danışma katmanı bu seansı inceleyemedi; kurulum/symlink onarımı gerekir")
        return None
    if not todays:
        _review_atla(day, "plan_yok", uyari=bool(dstr),
                     detail=("istenen seans için plan satırı yok — inceleme konusuz; tarih "
                             "backlog'dan geldiyse plan defteri ile inceleme defteri ayrışmış demektir"
                             if dstr else
                             "hiç plan yok — inceleyecek aday üretilmemiş (taze kurulum/boş defter)"))
        return None
    ctx = {"date": day, "regime": store.read_json("regime.json", {}).get("regime"),
           "plans": [{k: p.get(k) for k in ("ticker", "setup", "entry_trigger", "stop", "profit_target",
                                            "size_r", "score", "gate_verdict", "gate_reasons", "skill_chain")}
                     for p in todays]}
    prompt = ("You advise Meridian's candidate pipeline. Using your preloaded Meridian skills "
              "(read the relevant SKILL.md methodology first), give a SECOND OPINION on each candidate "
              "below. You do NOT decide — the deterministic gate already ruled; you annotate. "
              "You also have Meridian read-only MCP tools (meridian_regime, meridian_calibrations, "
              "meridian_near_miss, meridian_cf_summary, meridian_candidate_context) — query them for "
              "live context (regime, which thresholds leave money, a ticker's decision-time plan) "
              "before opining. Respond with ONLY this JSON: {\"reviews\":[{\"ticker\":str,"
              "\"opinion\":\"destekle|çekimser|karşı\",\"note\":str<=200}]}\n\n" +
              json.dumps(ctx, ensure_ascii=False) + _opinion_history())
    _setups = tuple({p2.get("setup") for p2 in todays if p2.get("setup")})
    butce_once = _agent_gun_sayaci()
    # Künye kutusu ÇAĞRIDAN ÖNCE de boşaltılır: `_agent_call` bunu kendi girişinde zaten yapıyor,
    # ama garantiyi OKUYAN tarafta tutmak sözleşmeyi çağrılana bağımlı olmaktan çıkarır (saplanmış
    # bir `_agent_call` — testler, ileride bir sarmalayıcı — kutuya hiç dokunmaz ve o hâlde bayat
    # bir künye bu seansın görüşüne yapıştırılırdı).
    _agent_model_sifirla()
    text = _agent_call(prompt, preload=tuple(_skill_preload("review", _setups)),
                       kind="review", timeout=300, max_wait=90.0)   # asenkron iş parçacığı bekleyebilir
    if text is None:
        # KAYITSIZ DÖNÜŞ #0 — 2026-07-31→08-08 canlı vakasının TAM DÜŞTÜĞÜ YOL: `_agent_call`
        # None döndürüyor (zincir cevapsız / havuz soğuması / RPD reddi) ve buradaki dönüş 10 gün
        # boyunca aileden tek olay basmadan yuttu. Sınıf ayrımı ÖLÇÜMDÜR: RPD gün sayacı değiştiyse
        # alt süreç gerçekten koştu (agent_bos — gecersiz eşiğine sayılır), değişmediyse çağrı hiç
        # yapılamadı (agent_cagri_yok — tarihe fatura edilmez; ayrıntı agent_call_* olaylarında).
        kosum_var = _agent_gun_sayaci() != butce_once
        _review_atla(day, "agent_bos" if kosum_var else "agent_cagri_yok", uyari=False,
                     soguma_s=round(brain_cooldown("agent"), 1), butce_gun=_agent_gun_sayaci(),
                     detail=("model zinciri koştu ama cevapsız — görüş üretilemedi (ham kanıt "
                             "agent_call_empty/review_fallback_empty olaylarında)" if kosum_var else
                             "yerel ajan çağrısı hiç yapılamadı (soğuma penceresi ya da RPD/RPM "
                             "bütçe reddi — ayrıntı agent_call_cooldown/agent_budget_* olaylarında)"))
        return None
    raw = _extract_json(text)
    parse_ok, parse_err, data = True, None, None
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:  # sessiz-yutma: BURASI kayıp yol DEĞİL — ilk deneme CLI'nın satır-sarmalamasına takılır, hemen altındaki ikinci deneme (_unwrap_strings) onarım denemesidir; ikinci de düşerse bilgi YOK OLMAZ: aşağıda candidate_review_empty_parse (asama=json_parse, parse_ok=False, istisna adı) basılır.
        try:
            data = json.loads(_unwrap_strings(raw))
        except Exception as e:
            parse_ok, parse_err = False, type(e).__name__
    if not parse_ok:
        # KAYITSIZ DÖNÜŞ #1 — cevap geldi ama JSON'a çevrilemedi (canlı vaka 2026-08-02: Gemini dolu
        # cevap verdi, kayıt yoktu, sebep görünmüyordu). Davranış AYNI (None); yalnız görünür oldu.
        _warn_review_empty("json_parse", text, raw, parse_ok=False, ham=[], reviews=[],
                           detail=f"model cevabı JSON'a çevrilemedi ({parse_err}); iki deneme de "
                                  f"düştü — görüş kaydedilmedi, danışma katmanı bu seans sessiz")
        _review_deneme_isle(day, "json_parse")     # gerçek deneme — gecersiz eşiğine sayılır
        return None
    ham = list(data.get("reviews") or [])
    reviews = [r for r in ham
               if isinstance(r, dict) and r.get("ticker")
               and r.get("opinion") in ("destekle", "çekimser", "karşı")]
    if not reviews:
        # KAYITSIZ DÖNÜŞ #2 — JSON ayrıştı ama şekil/enum süzgeci geriye görüş bırakmadı.
        _warn_review_empty("filtre", text, raw, parse_ok=True, ham=ham, reviews=reviews,
                           detail=f"JSON ayrıştı ({len(ham)} ham görüş) ama şekil/enum süzgecinden "
                                  f"sıfır görüş çıktı — kayıt yok")
        _review_deneme_isle(day, "filtre")         # gerçek deneme — gecersiz eşiğine sayılır
        return None
    # KÜNYE: CEVABI VEREN MODEL. Eskiden burada `active_model()` vardı ve o
    # YAPILANDIRMAYI okuyordu — canlıda görüşü `gemini-flash-latest` yazarken künye
    # `tencent/hy3:free` diyordu (ölçüm `cevap_veren_model` üstündeki blokta). Ölçülemezse alan
    # None + neden; `active_model()`e SESSİZCE dönülmez (uydurma yasağı).
    # GERİYE UYUM: eski kayıtlarda `model` alanı "İSTENEN"i taşır ve RETRO-DÜZELTİLMEZ. Yeni
    # kayıtlar anlamlarını kendileri beyan eder: `model_kaynagi` alanı VARSA `model` = cevap veren;
    # alan YOKSA kayıt eski sözleşmedendir. İki anlamın aynı ada binmemesi için "istenen" değer de
    # kendi ADIYLA yazılır (`model_istenen`) — ayrışma artık dosyanın kendisinden ölçülebilir.
    _cevap_model, _model_neden = cevap_veren_model()
    res = {"date": day, "model": _cevap_model, "brain": active_brain(),
           "model_kaynagi": "cevap_veren", "model_olculemedi": _model_neden,
           "model_istenen": active_model(),
           "reviews": reviews[:20], "ts": memory.now_iso(),
           "note": "danışma katmanı — kapı kararını değiştirmez"}
    if _cevap_model and res["model_istenen"] and _cevap_model != res["model_istenen"]:
        # AYRIŞMA GÖRÜNÜR OLUR: tam da haftalarca gizlenen olgu. Uyarı değil kayıt — zincirin
        # yedeğe düşmesi bir ARIZA değildir; arıza, düştüğünün SÖYLENMEMESİYDİ.
        obs.log("candidate_review_model_ayrismasi", date=day, cevap_veren=_cevap_model,
                istenen=res["model_istenen"],
                detail="görüşü zincirin yedek ayağı yazdı — künye artık cevap vereni taşıyor; "
                       "birincil ayağın neden boş döndüğü agent_call/agent_call_empty olaylarında")

    def _yaz(doc):
        """Başarı yolunun tek atomik yazımı: günü `tamam`a işler, o güne ait deneme sayacını ve
        (varsa) kalıcı `gecersiz` işaretini DÜŞÜRÜR — gerçek görüş her işaretten güçlüdür — ve
        belgeyi yeni kayıtla değiştirirken sıkışıklık defterini korur."""
        # BAŞARI YOLU AYNI KAYDI YAZAR (fark yalnız taşıma): sıkışıklık defteri (`backlog`)
        # kaybolmaz, seans `tamam`a işlenir, varsa deneme sayacı ve (elle koşumda kapanmış olabilecek)
        # gecersiz işareti düşer — GERÇEK görüş her işaretten güçlüdür. Kilitli tek atomik yazım.
        defter = _review_backlog_defteri(doc)
        defter["tamam"][day] = res["ts"]
        defter["denemeler"].pop(day, None)
        defter["gecersiz"].pop(day, None)
        _review_defteri_buda(defter)
        doc.clear()
        doc.update(res, backlog=defter)
        return True

    store.update_json("candidate_review.json", _yaz, {})
    obs.log("candidate_review", date=day, n=len(reviews), brain=active_brain())
    try:
        # KÜNYE DAMGAYLA BİRLİKTE İNER (Ö-39): `res` zaten bu çağrının ölçülmüş künyesini taşıyor
        # (`cevap_veren_model()` yukarıda TÜKETEREK okundu) — atıf defterine oradan geçer, ikinci
        # bir okuma yapılmaz. `iz_id` ayrı kutudan alınır; ölçülemezse None kalır (uydurma yok).
        _stamp_llm_opinions(day, reviews,      # görüşler plan satırlarına GERİ-damgalanır
                            kunye={"model": _cevap_model, "model_olculemedi": _model_neden,
                                   "model_kaynagi": "cevap_veren",
                                   "model_istenen": res["model_istenen"],
                                   "iz_id": cevap_veren_iz(), "kind": "review", "backfill": False})
    except Exception as e:
        obs.warn("llm_stamp_failed", error=f"{type(e).__name__}: {e}")
    return res


def _opinion_history(k: int = 5) -> str:
    """Ajanın KENDİ karnesi: son k gerçek görüş-sonuç çifti, prompt'a somut ders olarak.
    Toplu kalibrasyon sayısı deseni göstermez; 'NVDA'da karşı demiştin → +2.1R' gösterir. Veri yoksa
    boş dize (uydurma ders yok)."""
    plans = {pl.get("id"): pl for pl in store.read_jsonl("trade_plans.jsonl")}
    rows = []
    for t in reversed(store.read_jsonl("trades.jsonl")):
        op = (plans.get(t.get("plan_id")) or {}).get("llm_opinion")
        if op and t.get("r_multiple") is not None:
            r = float(t["r_multiple"])
            verdict = "isabet" if ((op == "destekle" and r > 0) or (op == "karşı" and r <= 0)) else \
                      ("yanılgı" if op in ("destekle", "karşı") else "nötr")
            rows.append(f"{t.get('ticker')}: sen '{op}' dedin → {'+' if r > 0 else ''}{r:.2f}R ({verdict})")
        if len(rows) >= k:
            break
    if not rows:
        return ""
    return ("\n\nYOUR RECENT CALLS (learn from your own pattern before opining):\n- "
            + "\n- ".join(rows))


# ==================================================================================================
# ATIF DEFTERİ (Ö-39 / WP7 "künye turu" — Rol-1 tasarım-kapanışı 2026-08-24, YOL (b))
# --------------------------------------------------------------------------------------------------
# SORU: "yetkili danışman HANGİ modeldi?" — terfi 2026-08-14'te açıldığından beri canlı bir soru
# (`AUTHORITY_CHANGE`: R farkı 0.638, n=100) ve bugüne dek KALICI hiçbir defterde cevabı yoktu:
#   · plan satırı taşıyamaz — `test_authority_boundaries_v77::test_c3` `llm_opinion` dışında anahtar
#     yazılmasını YASAKLIYOR (yetki sınırı yasası; ikinci alan = yasa değişikliği);
#   · `candidate_review.json` TEK-BELGE deposudur (`doc.clear()`), yalnız SON günü tutar;
#   · `agent_calls.jsonl` modeli taşır ama TICKER ve PLAN GÜNÜ yoktur — ve `backfill_opinions`
#     bugünkü çağrıyla AYLAR öncesine damga vurur (canlı: 2026-08-16 koşumu 2026-02-26 ve
#     2026-04-14 planlarını damgaladı), yani zaman-yakınlığı join'i YAPISAL olarak yanlıştır.
# ÇÖZÜM: yasayı kırmadan AYRI append-only defter. Satır plan_id ↔ künye ↔ `iz_id` üçlüsünü taşır ve
# `backfill` bayrağıyla geriye-damgayı KENDİ BEYAN EDER — okuyucu artık tahmin etmez, OKUR.
# OKUYUCUSU İLK GÜNDEN BAĞLI (YASA 6 / uyuyan-yol dersi): `analytics.llm_opinion_calibration`
# `model_kirilim` kovalarını buradan kurar. Sözleşme: `ledgers.CONTRACTS["plan_atif.jsonl"]`.
# ==================================================================================================
PLAN_ATIF_DEFTERI = "plan_atif.jsonl"

KUNYE_DAMGA_VERILMEDI = ("cevap veren model ÖLÇÜLEMEDİ: damgayı çağıran künye paketi vermedi — bu "
                         "yol künyeyi hiç okumuyor (satır atıfsızdır, 'ölçtük ve ad yoktu' DEĞİL)")


def _plan_atif_yaz(day: str, damgalananlar: list, kunye: dict | None) -> int:
    """Damgalanan her plan için `plan_atif.jsonl`e BİR satır yazar; dönüş: yazılan satır sayısı.

    UYDURMA YASAĞI: künye ölçülemediyse `model` None kalır ve `model_olculemedi` nedeni taşır;
    `model_istenen` (yapılandırma adı) ASLA `model`e kopyalanmaz — v245 künye kusurunun deftere
    düşmüş hâli tam olarak o kopyaydı. Künye paketi hiç verilmediyse `model_kaynagi` da None olur:
    "cevap veren" beyanı ölçülmemiş bir satıra basılamaz.
    YAZIM ÇAĞIRANI DÜŞÜRMEZ (telemetri emsali): atıf bir ÖLÇÜM yoludur, arızası damgalamayı
    öldürmemeli — ama SESSİZ de kalmaz (YASA 4), `plan_atif_write_failed` ile adıyla kaydedilir."""
    if not damgalananlar:
        return 0
    k = kunye or {}
    model = k.get("model") or None
    neden = k.get("model_olculemedi") if model is None else None
    if model is None and not neden:
        neden = KUNYE_DAMGA_VERILMEDI
    ts = memory.now_iso()
    satirlar = [{"ts": ts, "plan_id": pid, "ticker": tkr, "plan_date": day,
                 "kind": k.get("kind"), "model": model, "model_olculemedi": neden,
                 "model_kaynagi": k.get("model_kaynagi"), "model_istenen": k.get("model_istenen"),
                 "iz_id": k.get("iz_id"), "backfill": bool(k.get("backfill"))}
                for pid, tkr in damgalananlar]
    try:
        # KİLİT: dolgu iş parçacığı ile inceleme kolu AYNI ANDA damgalayabilir (ikisi de bu
        # fonksiyona iner); kilitsiz append satırları birbirinin içine yazabilirdi.
        with store.file_lock(PLAN_ATIF_DEFTERI):
            for s in satirlar:
                store.append_jsonl(PLAN_ATIF_DEFTERI, s)
    except Exception as e:
        obs.warn("plan_atif_write_failed", defter=PLAN_ATIF_DEFTERI, gun=day, n=len(satirlar),
                 error=f"{type(e).__name__}: {e}",
                 detail="atıf satırları YAZILAMADI — damgalama normal tamamlandı; bu satırların "
                        "yokluğu 'künye yoktu' DEĞİL 'atıf kaydedilemedi' demektir")
        return 0
    return len(satirlar)


def _stamp_llm_opinions(day: str, reviews: list, kunye: dict | None = None) -> None:
    """Kademe-1 (LLM danışman katmanı): inceleme P3'ten DAKİKALAR SONRA asenkron iner — bu yüzden görüş
    plan satırlarına geriye dönük damgalanır (alpaca_fill_price backfill kalıbı). İki yere yazılır:
    trade_plans.jsonl (kalibrasyon defterinin join'i + panel çipleri) ve portfolio.json'daki silahlı
    planlar (P4 dolum-anı vetosu — YALNIZ terfiden sonra — oradan okur). Yetki yok: damga bilgidir.

    `kunye` (Ö-39): görüşü ÜRETEN çağrının künye paketi —
    `{model, model_olculemedi, model_kaynagi, model_istenen, iz_id, kind, backfill}`. Damganın
    KENDİSİ okumaz, ÇAĞIRAN verir: künye kutusu tüketen-okumalıdır ve burada okunsaydı iki çağıran
    (`review_candidates` · `backfill_opinions`) sırayla okuyup birbirinin künyesini boşaltırdı.
    Verilmezse satır yine yazılır ama NEDENİYLE (`KUNYE_DAMGA_VERILMEDI`)."""
    op_by_ticker = {str(r.get("ticker")): r.get("opinion") for r in reviews if r.get("ticker")}
    if not op_by_ticker:
        return
    # KİLİTLİ oku-değiştir-yaz: bu damga, zamanlayıcı iş parçacığının AYNI dosyaya
    # yazdığı anlarda araya giriyordu; kilitsiz hâlde döngünün planlarını bayat kopyayla ezebilirdi.
    counters: dict = {"plans": 0, "damgalananlar": []}

    def _patch_plans(plans):
        """trade_plans.jsonl satırlarına o günün LLM görüşünü damgalar (yalnız aynı gün + aynı
        ticker + `llm_opinion` HENÜZ YOKKEN — var olan damga ezilmez); damgalanan sayısını sayar
        ve damgalanan satırların (kimlik, ticker) çiftini biriktirir — atıf defterinin girdisi
        BUDUR: ezilmeyen bir satır atfedilirse aynı görüş iki kez atfedilmiş olurdu."""
        n = 0
        vurulan = []
        for pl in plans:
            if pl.get("date") == day and pl.get("ticker") in op_by_ticker and "llm_opinion" not in pl:
                pl["llm_opinion"] = op_by_ticker[pl["ticker"]]
                vurulan.append((pl.get("id"), pl.get("ticker")))
                n += 1
        counters["plans"] = n
        counters["damgalananlar"] = vurulan
        return n > 0

    store.update_jsonl("trade_plans.jsonl", _patch_plans)
    patched = counters["plans"]
    def _patch_cf(rows):                                 # #4: cf defteri de damgalanır — görüş↔sonuç
        """Karşı-olgusal (cf) defter satırlarını aynı kuralla damgalar; eşik-altı `near_miss`
        gölge adaylar ATLANIR (onlar LLM görüşü almaz)."""
        hit = False                                      # çiftleri simüle satırlardan haftalar içinde birikir
        for r in (rows or []):
            if r.get("near_miss"):                       # eşik-altı gölge adaylar LLM görüşü almaz
                continue
            if r.get("date") == day and r.get("ticker") in op_by_ticker and "llm_opinion" not in r:
                r["llm_opinion"] = op_by_ticker[r["ticker"]]
                hit = True
        return hit

    store.update_json("cf_open.json", _patch_cf, [])
    def _patch_pf(pf):                                   # CANLI DEFTER — kilitsiz dokunulmaz
        """portfolio.json'daki SİLAHLI planlara aynı damgayı basar (P4 dolum-anı vetosu oradan
        okur). Silahlı plan yoksa dokunmaz; var olan `llm_opinion` ezilmez."""
        if not pf or not pf.get("armed"):
            return False
        changed = False
        for pl in pf["armed"]:
            if pl.get("date") == day and pl.get("ticker") in op_by_ticker and "llm_opinion" not in pl:
                pl["llm_opinion"] = op_by_ticker[pl["ticker"]]
                changed = True
        return changed

    store.update_json("portfolio.json", _patch_pf, None)
    atif_n = _plan_atif_yaz(day, counters["damgalananlar"], kunye)
    # ATIF SAYISI OLAYA DA KONUR: `n` ile `atif_n` ayrışırsa (yazım düştü ya da çağıran künyesiz
    # geldi) bu tek satırdan görülür — iki sayıyı tek alana katlamak arızayı gizlerdi.
    obs.log("llm_opinions_stamped", date=day, n=patched, atif_n=atif_n,
            atif_kunyeli=bool((kunye or {}).get("model")))


def rank_explore(cands: list, timeout: int = 60) -> str | None:
    """BONUS: keşif modunda tek 0.25R slot için yarışan, KAPIYI ZATEN GEÇMİŞ GO adayları arasından
    yerel ajan BİR ticker seçer. Yetki sınırı dar ve yapısal: seçim yalnız eşitler arasında sıralamadır —
    boyut, karar, emir üretemez; cevap yoksa/bozuksa None → skor sırası devralır (fail-open).
    Kısa zaman aşımı: EOD döngüsünde nadir (bütçe %0) ve ≤60 sn kabul edilebilir."""
    import subprocess
    bin_ = _hermes_bin()
    if not bin_ or len(cands) < 2:
        return None
    menu = "\n".join(f"- {c['ticker']}: setup={c.get('setup')} skor={c.get('score')} RR={c.get('rr')}"
                      for c in cands)
    prompt = ("You are Meridian's exploration-probe selector. ALL candidates below already passed the "
              "discipline gate; pick the ONE best evidence-gathering probe for a 0.25R micro position "
              "in a budget-0 regime.\n" + menu +
              "\n\nRespond with ONLY the ticker symbol. No prose.")
    try:
        text = _agent_call(prompt,
                           preload=tuple(_skill_preload("explore", tuple({c.get("setup") for c in cands if c.get("setup")}))),
                           kind="explore", timeout=timeout, max_wait=0.0)   # döngü asla bloklanmaz
        if text is None:
            return None
        valid = {c["ticker"] for c in cands}
        for tok in reversed(text.upper().split()):           # panel süsleri arasından SON geçerli sembol
            t = tok.strip(".,:;!│╰╯╭╮*`'\"")
            if t in valid:
                obs.log("explore_slot_llm_pick", ticker=t, among=sorted(valid))
                return t
    except Exception:  # sessiz-yutma: ağ/sağlayıcı hatası bu yolun NORMAL hâli; çağıran boş sonuç üzerinden yedek kaynağa düşer ve kaynak seçimi ayrıca kaydedilir
        pass
    return None


def _review_plans_batch(day: str, subset: list) -> list:
    """Bir günün BELİRLİ plan alt-kümesine yerel ajandan görüş al (review_candidates'ın çekirdeği).
    KARAR-ANI bilgisi verilir (tetik/stop/hedef/skor/kapı) — SONUÇ (r_multiple) ASLA verilmez, yoksa
    kalibrasyonun öngörü geçerliliği çöker. Dönüş: geçerli reviews listesi (boşsa [])."""
    if not subset:
        return []
    ctx = {"date": day, "regime": (subset[0].get("regime_at_plan")
                                   or store.read_json("regime.json", {}).get("regime")),
           "plans": [{k: p.get(k) for k in ("ticker", "setup", "entry_trigger", "stop", "profit_target",
                                            "size_r", "score", "gate_verdict", "gate_reasons", "skill_chain")}
                     for p in subset]}
    prompt = ("You advise Meridian's candidate pipeline. Using your preloaded Meridian skills "
              "(read the relevant SKILL.md methodology first), give a SECOND OPINION on each candidate "
              "below AS OF ITS DECISION DATE — you are told ONLY what was known at signal time; the "
              "outcome is deliberately withheld so your opinion stays a genuine prediction. You do NOT "
              "decide — annotate only. Respond with ONLY this JSON: {\"reviews\":[{\"ticker\":str,"
              "\"opinion\":\"destekle|çekimser|karşı\",\"note\":str<=200}]}\n\n"
              + json.dumps(ctx, ensure_ascii=False))
    _setups = tuple({p2.get("setup") for p2 in subset if p2.get("setup")})
    text = _agent_call(prompt, preload=tuple(_skill_preload("review", _setups)),
                       kind="backfill", timeout=300, max_wait=30.0)
    if text is None:
        return []
    raw = _extract_json(text)
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:  # sessiz-yutma: yardımcı G/Ç yolu; çağıran yokluğu zaten yedek değerle karşılıyor ve asıl okuma hatası store katmanında bir kez uyarılıyor
        try:
            data = json.loads(_unwrap_strings(raw))
        except json.JSONDecodeError:  # sessiz-yutma: yardımcı G/Ç yolu; çağıran yokluğu zaten yedek değerle karşılıyor ve asıl okuma hatası store katmanında bir kez uyarılıyor
            return []
    return [r for r in (data.get("reviews") or [])
            if isinstance(r, dict) and r.get("ticker")
            and r.get("opinion") in ("destekle", "çekimser", "karşı")]


def backfill_opinions(max_days: int | None = None) -> dict:
    """ÇEVRİMDIŞI GÖRÜŞ DOLGUSU (Hermes batch özelliğinden esinli).
    Kalibrasyon aylar yerine GÜNLERDE anlamlılığa ulaşsın diye: SONUCU ZATEN BİLİNEN ama LLM görüşü
    OLMAYAN geçmiş planları yerel ajana KARAR-ANI bilgisiyle (sonuç gizli) toplu inceletir ve görüşü
    trade_plans + cf defterine geriye damgalar. Look-ahead YOK → öngörü geçerliliği korunur; terfiyi
    sahte tetiklemez. Rate bütçesine saygılı: gün başına 1 çağrı, max_days tavanı, bütçe kuruyunca durur.
    OTOMATİK KADANS: `max_days=None` → tavan `backfill_budget()`ten TÜRETİLİR (kalan
    ajan kotasının payı; havuz soğumadaysa 0). Eskiden tek tetik pano düğmesiydi ve sabit 40'tı;
    yani kuyruk YALNIZ operatör hatırlarsa eriyordu. Açık bir sayı verilirse (operatörün elle
    hızlandırması / testler) o sayı AYNEN geçerlidir — türetim ezilmez, atlanır.
    Yalnız operatör/haftalık tetikler (token disiplini). Dönüş: {days_processed, stamped, remaining}."""
    if max_days is None:
        _bt = backfill_budget()
        max_days = int(_bt["tavan"])
        if max_days <= 0:
            # KISILMA SESSİZ DEĞİLDİR (YASA 4): "kuyruk erimedi" ile "kuyruk erimeye çalıştı ama
            # kota yoktu" ayrı hâllerdir; ikincisi normaldir, birincisi arızadır.
            obs.log("backfill_progress", islenen=0, tavan=0, kaynak=_bt["kaynak"],
                    formul=_bt["formul"], detail="bütçe kıstı — dolgu bu gece koşmadı")
            return {"days_processed": 0, "opinions_stamped": 0, "days_remaining": None,
                    "rows_remaining": None, "butce": _bt}
    plans = store.read_jsonl("trade_plans.jsonl")
    trades = store.read_jsonl("trades.jsonl")
    # sonucu bilinen plan_id'ler: gerçek kapanmış işlem (terfi-kritik GERÇEK çift kaynağı). cf satırları
    # plan_id taşımaz; cf_buckets yalnız gösterge ve terfiye girmez — bu yüzden dolgu gerçek işleme demirli.
    outcome_ids = {str(t.get("plan_id")) for t in trades if t.get("r_multiple") is not None}
    # iş listesi: sonucu bilinen AMA görüşü olmayan planlar, güne göre gruplu (en eskiden yeniye)
    todo: dict = {}
    for p in plans:
        day = p.get("date")
        if not day or "llm_opinion" in p:
            continue
        if str(p.get("id")) in outcome_ids:
            todo.setdefault(day, []).append(p)
    days = sorted(todo)
    total_remaining = sum(len(v) for v in todo.values())
    processed, stamped = 0, 0
    for day in days[:max_days]:
        reviews = _review_plans_batch(day, todo[day])
        # KÜNYE HEMEN BURADA OKUNUR (Ö-39): kutu tüketen-okumalıdır ve bir sonraki `_agent_call`
        # (döngünün bir sonraki günü) onu GİRİŞTE sıfırlar — okuma geciktirilirse künye kaybolur.
        # Bu yol eskiden künyeyi HİÇ okumuyordu: dolgu, aylar öncesine atıfsız damga vuruyordu ve
        # Ö-39'un canlı kanıtı (2026-02-26 / 2026-04-14 damgaları) tam buradan çıkmıştı.
        _dolgu_model, _dolgu_neden = cevap_veren_model()
        _dolgu_iz = cevap_veren_iz()
        if not reviews:                       # bütçe kurudu / cevapsız → dur (kalanı sonraki turda)
            if not _agent_budget_take(0.0):
                break
            continue
        _stamp_llm_opinions(day, reviews,
                            kunye={"model": _dolgu_model, "model_olculemedi": _dolgu_neden,
                                   "model_kaynagi": "cevap_veren",
                                   "model_istenen": active_model(),
                                   "iz_id": _dolgu_iz, "kind": "backfill", "backfill": True})
        processed += 1
        stamped += len({r["ticker"] for r in reviews})
    if processed:
        try:
            from . import analytics
            analytics.llm_opinion_calibration()      # dolgudan sonra kalibrasyonu tazele
        except Exception:  # sessiz-yutma: isteğe bağlı bağımlılık yok — yokluğu kusur değil yapılandırma; içe aktarma denemesinin kendisi zaten cevaptır
            pass
    out = {"days_processed": processed, "opinions_stamped": stamped,
           "days_remaining": max(0, len(days) - processed), "rows_remaining": total_remaining}
    obs.log("opinion_backfill", **out)
    # İLERLEME AYRI BİR OLAYDIR: `opinion_backfill` bir KOŞU özetidir; `backfill_progress` KUYRUĞUN
    # halidir (kalan gün/satır). 93 günlük bir kuyruğun birkaç gecede eridiğini ancak ikincisi
    # gösterir — ve kuyruk ERİMİYORSA bunu ancak ikincisi ele verir.
    obs.log("backfill_progress", islenen=processed, damgalanan=stamped, tavan=max_days,
            kalan_gun=out["days_remaining"], kalan_satir=total_remaining,
            detail="çevrimdışı görüş dolgusu — kalibrasyon kuyruğu")
    try:
        from . import watchdog as _wd
        _wd.beat("opinion_backfill")
    except Exception as e:
        obs.warn("backfill_beat_failed", error=f"{type(e).__name__}: {e}",
                 detail="mekanizma nabzı yazılamadı — bekçi bu kadansı bayat sanabilir")
    return out


def backfill_opinions_async(max_days: int | None = None):
    """Döngüyü/isteği bloklamadan dolgu koştur (uzun sürebilir — gün başına LLM çağrısı).

    DÖNÜŞ: başlatılan Thread — `review_candidates_async` ile AYNI sözleşme. Eskiden thread
    yaratılıp ATILIYORDU (`...start()` dönüşü kullanılmıyordu), yani hiçbir çağıran onu
    bekleyemez, durumunu soramaz, kapatamazdı: iş parçacığı yaratıldığı anda görünmez olurdu.
    Bunun iki bilinen bedeli var ve ikisi de kardeş fonksiyonda ZATEN öğrenilmişti:
      * kısa ömürlü bir süreçte (`python -m meridian.run --once`) daemon thread çıkışta
        öldürülür ve dolgu SESSİZCE kaybolur — hiçbir istisna fırlamaz;
      * testte thread kendi fikstürünü AŞAR; `config.STATE` sandbox'tan canlıya geri
        döndükten sonra yazarsa operatörün defterine test artefaktı düşer.
    Thread'i döndürmek bu iki sorunu ÇÖZMEZ ama çağırana çözme İMKÂNI verir; tutamağı
    olmayan bir iş parçacığı, tanım gereği yönetilemez."""
    import threading

    def _bg():
        """Arka plan gövdesi: dolguyu koşar; istisna iş parçacığını sessizce düşürmesin diye
        `opinion_backfill_failed` uyarısına çevrilir."""
        try:
            backfill_opinions(max_days)
        except Exception as e:
            obs.warn("opinion_backfill_failed", error=f"{type(e).__name__}: {e}")
    t = threading.Thread(target=_bg, name="opinion-backfill", daemon=True)
    t.start()
    return t


def review_candidates_async(dstr: str | None = None):
    """Döngüyü bloklamadan incele: scheduler thread'i 300 sn'lik bir LLM sürecini bekleyemez.

    DÖNÜŞ: başlatılan Thread — çağıran KISA ÖMÜRLÜ bir süreçse (`python -m meridian.run --once`)
    join etmek ZORUNDADIR. Bulundu: daemon thread, süreç çıkışında öldürülüyordu, yani
    tek-atışlık her koşuda ikinci görüş SESSİZCE kayboluyordu. Üstelik telafisi de yoktu — zamanlayıcı
    o seansı "zaten işlendi" görüp bir daha tetiklemediği için o gün SONSUZA KADAR görüşsüz kalıyordu.
    Hiçbir istisna fırlamadı; panoda yalnız bir hafta önceki görüş duruyordu.
    """
    import threading

    def _bg():
        """Arka plan gövdesi: aday incelemesini koşar; istisna `candidate_review_failed`
        uyarısına çevrilir (sessiz kayıp yok)."""
        try:
            review_candidates(dstr)
        except Exception as e:
            obs.warn("candidate_review_failed", error=f"{type(e).__name__}: {e}")
    t = threading.Thread(target=_bg, name="candidate-review", daemon=True)
    t.start()
    return t


def review_backlog(max_sessions: int = 1) -> dict:
    """TELAFİ: planı olan ama görüşü OLMAYAN en yeni seans(lar)ı incele — SIKIŞIKLIK KORUMALI.

    Tek bir kaçırılmış pencere, o seansı kalıcı olarak görüşsüz bırakıyordu (döngü aynı seansı ikinci
    kez işlemez). Danışma katmanının kanıt üretmesi buna bağlı: LLM görüş↔sonuç kalibrasyonu ancak
    kapanan planların görüşü varsa birikir.

    SERTLEŞTİRME (canlı vaka 2026-07-31→08-08, ölçüldü): eski `dates[:max_sessions]` şekli
    yalnız EN YENİ tarihi deniyordu ve o tarih incelenemez hâldeyken her şey donuyordu — scheduler
    5 dakikada bir aynı tarihi dövdü, model zinciri cevapsızdı, günlük 150'lik RPD bütçesinin tamamı
    review'e yandı (75 deneme × 2 model; 19:21'de `agent_budget_exhausted`) ve öneri yolu dahil tüm
    ajan katmanı aç kaldı. Üç kural bunu bitirir:
      1. GERİ-ÇEKİLME — başarısız tarih `denemeler` kaydındaki `sonraki_epoch`tan önce YENİDEN
         DENENMEZ (üstel pencere, bkz. `_review_bekleme_s`); bekleyen turlar OLAYSIZ döner, çünkü
         değişen hiçbir şey yokken 5 dakikada bir basılan `candidate_review_backlog` satırı bilgi
         değil gürültüdür (günde ~276 satırdı).
      2. KALICI İŞARET + İLERLEME — `REVIEW_GECERSIZ_N` gerçek denemede görüş üretilemeyen tarih
         `gecersiz` işaretlenir (bkz. `_review_deneme_isle`) ve sıradaki görüşsüz tarih hedef olur;
         pencere `REVIEW_BACKLOG_PENCERE` seansla sınırlı — daha eski boşluklar bu telafinin değil
         kanıt dolgusunun (backfill_opinions) işidir.
      3. TARAMA, EN YENİ GÖRÜŞLÜ SEANSTA DURUR — `tamam`/`date` işaretine varınca kırılır; gecersiz
         işaretli tarihler atlanarak GEÇİLİR. Başarı yolu aynen korunur: review yazılır, işaretçi
         ilerler, olay `reviewed` dolu basılır."""
    import time as _t
    plans = store.read_jsonl("trade_plans.jsonl")
    if not plans:
        return {"reviewed": [], "detail": "plan yok"}
    kayit = store.read_json("candidate_review.json", {}) or {}
    have = str(kayit.get("date") or "")
    defter = _review_backlog_defteri(kayit)
    dates = sorted({str(p.get("date")) for p in plans if p.get("date")}, reverse=True)
    now = _t.time()
    todo, bekleyen, atlanan_gecersiz = [], [], []
    for d in dates[:REVIEW_BACKLOG_PENCERE]:
        if d in defter["gecersiz"]:
            atlanan_gecersiz.append(d)
            continue                                   # kalıcı işaret: atla ve İLERLE (donma biter)
        if d == have or d in defter["tamam"]:
            break                                      # en yeni görüşlü seans — gerisi dolgunun işi
        sonraki = float((defter["denemeler"].get(d) or {}).get("sonraki_epoch") or 0.0)
        if sonraki > now:
            bekleyen.append(d)
            break                                      # canlı hedef beklemede — eskiye sıçranmaz
        todo.append(d)
        if len(todo) >= max_sessions:
            break
    if not todo:
        # Deneme yok, işaret yok, değişen durum yok — olay da yok. (Sessiz-yutma değil: yutulan bir
        # başarısızlık yok; her gerçek deneme/işaret kendi olayını zaten basıyor.)
        return {"reviewed": [], "requested": [], "already": have,
                "bekleyen": bekleyen, "gecersiz": atlanan_gecersiz,
                "detail": "sıradaki iş yok (bekleme penceresi / işaretli / güncel)"}
    done = []
    for d in todo:
        r = review_candidates(d)
        if r:
            done.append(d)
    defter_son = _review_backlog_defteri()
    gecersiz_yeni = [d for d in todo if d in defter_son["gecersiz"]]
    obs.log("candidate_review_backlog", requested=todo, reviewed=done, already=have,
            gecersiz_yeni=gecersiz_yeni, gecersiz_n=len(defter_son["gecersiz"]))
    return {"reviewed": done, "requested": todo, "already": have,
            "bekleyen": bekleyen, "gecersiz_yeni": gecersiz_yeni}


def propose_with_llm() -> dict | None:
    """Beyin zinciri: sırayla hazır olan ilk sağlayıcı önerir; hata/boş yanıt zinciri düşürmez, bir
    sonraki sağlayıcı dener. Aylık bütçe kapısı TÜM ücretli beyinleri kapatır (deterministik kalır).
    Dönen hipotez kaynak etiketi taşır — defterde hangi beynin önerdiği her zaman okunur."""
    from . import spend
    if spend.over_budget():
        obs.log("hermes_budget_gate", detail="aylık bütçe dolu — ücretli beyinler kapalı")
        return None
    why: dict[str, str] = {}
    for p in brain_order():
        if not _provider_ready(p):
            why[p] = "no_credentials"
            continue
        rem = _provider_cooldown(p)
        if rem > 0:
            # SAHADAN ALINDI: kota yiyen sağlayıcıyı her turda yeniden aramak 45 özdeş 429 üretmişti.
            why[p] = "cooldown"
            obs.log("hermes_brain_cooldown", provider=p, remaining_s=round(rem, 1),
                    detail="kota/oran sınırı sonrası dinlenmede — zincir bir sonrakine geçiyor")
            continue
        _trace_take()                     # önceki turdan artık neden kalmasın
        try:
            hyp = (propose_with_claude() if p == "claude"
                   else _propose_nous() if p == "nous" else _propose_gemini())
        except Exception as e:
            limited, retry_after = _rate_limited(e)
            cooled = brain_stand_down(p, "rate_limit" if limited else "error", retry_after) if limited else 0.0
            obs.warn("hermes_brain_failed", provider=p, error=f"{type(e).__name__}: {e}",
                     rate_limited=limited, cooldown_s=round(cooled, 1))
            # BAŞARISIZLIK BOŞLUK DEĞİLDİR. Eskiden burada hyp=None kalıp aşağıdaki hermes_brain_empty
            # de yazılıyordu: her 429 defterde İKİ kez, biri yanlış sınıfta görünüyordu (92 boşun ~44'ü).
            why[p] = "failed"
            continue
        if hyp:
            hyp["source"] = f"hermes:{p}"
            brain_recovered(p)            # kullanılabilir cevap geldi — soğuma ve seri sıfırlanır
            return hyp
        reason, detail = _trace_take()
        reason = reason or EMPTY_UNKNOWN
        why[p] = reason
        if reason in _NOT_A_RESPONSE:
            # çağrı hiç yapılamadı → "boş cevap" diye kaydetmek defteri kirletir; ayrı olay.
            obs.log("hermes_brain_skipped", provider=p, reason=reason, detail=detail)
            continue
        # BAŞARILI AMA KULLANILAMAZ: katman yukarıya "sorun yok" der, kanıt üretmez. Sınıfı olayda
        # görünür — LLM görüş↔sonuç kalibrasyonu tam da bu yüzden hiç çift biriktirememişti.
        obs.warn("hermes_brain_empty", provider=p, reason=reason, detail=detail)
    obs.warn("hermes_brain_unavailable", providers=why,
             detail="hiçbir beyin kullanılabilir öneri üretmedi — DETERMİNİSTİK önerici devrede")
    return None


# ==================================================================================================
# ZİNCİR KÜNYESİ — "CEVABI KİM VERDİ" (`candidate_review` deseninin kardeşi)
# --------------------------------------------------------------------------------------------------
# ESKİ HÂL: `out.update({..., "model": active_model()})` — yani künye zincir KOŞTUKTAN SONRA
# YAPILANDIRMAYI yeniden okuyordu. Zincirin bütün varlık sebebi ayakların DÜŞMESİ olduğu için bu
# alan tam da düşüş olduğunda yanlış oluyordu: metni ikinci ayak yazarken künye birinciyi söylüyordu.
# `candidate_review`de ölçülen bedel buydu — `tencent/hy3:free` 56 çağrıda 0 cevap verdi, pano
# haftalarca onun adını yazdı ve HATALI KÜNYE ARIZAYI GİZLEDİ. Bu, aynı kusurun ikinci eviydi
# ve tüketicisi Katman-B'nin kalıcı defterleridir (bkz. aşağıdaki tüketici listesi).
#
# OKUMA NOKTASI NEDEN AYAK BAŞINA (bu blok tam olarak bir tuzağı kapatıyor):
# `cevap_veren_model()` TÜKETEN bir okumadır (okuyunca kutuyu boşaltır) ve kutuyu YALNIZ
# `_agent_call` doldurur — zincirin dört ayağından YALNIZ BİRİ (nous + yerel ajan) oradan geçer.
# Kutuyu ayak ayrımı yapmadan tek yerde okumak, düzelttiğimiz kusuru TERS YÖNDE üretirdi:
#   · nous-yerel BOŞ → gemini DOLU  ⇒ kutu boş; gemini'nin künyesi sessizce None olurdu.
#   · claude ilk denemede DOLU      ⇒ kutu bu turda hiç yazılmadı; aynı iş parçacığındaki ÖNCEKİ
#     bir `_agent_call`in tüketilmemiş künyesi claude'un cevabına YAPIŞIRDI (bayat künye).
# Bu yüzden her ayak künyesini KENDİ çağrısının yanında bildirir ve kutu yalnız kendi çağrısını
# yapan ayakta okunur. Doğruluğun kanıtı üç yapısal olguya dayanır: (i) kutuyu yazan tek yer
# `_agent_model_kaydet` (dolu cevabı veren denemenin içinde), (ii) `_agent_call` kutuyu GİRİŞTE
# sıfırlar (erken dönüşler dahil) — yani okuduğumuz şey her zaman BİZİM çağrımıza aittir,
# (iii) kutu `threading.local` ve okuyucu çağrıyı yapan iş parçacığının kendisidir.
# Diğer üç ayak için künye ölçüm değil OLGUDUR: gövdenin isteğe YAZDIĞI adın aynı kaynağı
# (`MODEL` sabiti · `_nous_portal_model()` · `gemini_model()`) — bu yüzden onlarda "ölçülemedi"
# hâli yoktur. Kalan pay dürüstçe beyan edilir: gemini/portal adları sır okumasıdır ve sır önbelleği
# (TTL 300 sn) çağrı ile künye arasında yenilenirse ad ayrışabilir; ölçülen bir vaka YOKTUR ve bu
# pencere `active_model()`in kapattığımız SAĞLAYICI-SEÇİMİ hatasıyla aynı sınıfta değildir.
#
# TÜKETİCİLER (ADIYLA, ölçüldü): tek üretim tüketicisi `nous_eval.haftalik_degerlendirme`
# (`nous_eval.haftalik_degerlendirme`) — `cevap.get("text"/"beyin"/"model"/"neden")` VE ÜÇ KÜNYE
# BEYANINI (`model_kaynagi`/`model_olculemedi`/`model_istenen`) okur; hepsini iki kalıcı deftere
# yazar: `nous_eval_runs.json` (`_kosu_kaydet`) ve `improvement_proposals.jsonl`
# (`_oneri_kaydet` → satır alanları `model` + üç beyan; ledgers sözleşmesinde ZORUNLU DEĞİL, yani
# None meşru ve eski satırlar retro-damgalanmaz).
# BEYANLARIN TAŞINMASI 2026-08-24'TE KAPANDI (WP7-40): o güne dek beyanlar bu fonksiyonun dönüşünde
# ÖLÜYORDU — defterler çıplak `model` alanını taşıyor, "cevap veren mi, istenen mi?" sorusu
# defterden cevaplanamıyordu. Zincir beyan vermezse tüketici NEDEN uydurmaz, "beyansız dönüş" diye
# kaydeder (`nous_eval.KUNYE_BEYANSIZ_DONUS`); metin enjekte edildiği yolda zincir HİÇ çağrılmaz ve
# o hâl de adıyla yazılır (`nous_eval.KUNYE_ZINCIR_CAGRILMADI`).
# Pano ikisini de None-korumalı basar (`web/app.js`: `p.model || "—"`). Sözleşme EK ALANLA
# genişledi, mevcut anahtarların adı/şekli DEĞİŞMEDİ — `.get()` okuyan tüketici kırılmaz.
# ==================================================================================================
ZINCIR_MODEL_YOK = ("cevap veren model YOK: beyin zincirinden dolu metin çıkmadı — ayak başına "
                    "sebep `neden` alanında")


def chain_text(prompt: str, *, kind: str, preload: tuple = (), timeout: int = 300,
               max_wait: float = 0.0, note: str | None = None) -> dict:
    """BEYİN ZİNCİRİNİN GENEL METİN YOLU — `propose_with_llm` ile AYNI disiplin, farklı GÖREV.

    NEDEN VAR (nous sistem-değerlendirme katmanı): Katman B beyni bir hipotez üretmek
    için değil, MEKANİZMALARI DEĞERLENDİRMEK için çağırır. `propose_with_llm` hipoteze özeldir
    (`_parse_hyp`, `hyp["source"]`, tek-değişken sözleşmesi) ve o yolu genel amaçlı hâle getirmek
    hipotez yolunu kırılgan yapardı. Bu fonksiyon zincirin YALNIZ taşıma katmanını paylaşır:
    sıra (`brain_order`), hazır-olma, 429 soğuması, bütçe kapısı, boş-cevap sınıflandırması.

    SYSTEM'E DOKUNULMAZ. Görev metni, telemetri ve şema sözleşmesi TAMAMEN `prompt` içinden girer —
    yani user-prompt yolundan. SYSTEM statik bir sabittir (AST testiyle çivili) ve içine görev metni
    sızdığı gün `cache_control` her turda ıskalar; maliyet sessizce katlanır.

    DÖNÜŞ: {"text", "beyin", "model", "model_kaynagi", "model_olculemedi", "model_istenen",
    "neden": {sağlayıcı: sebep}} — `text=None` ise `neden` zincirin HER ayağının niçin cevap
    vermediğini taşır. "Çağrı yapılamadı" ile "cevap boş geldi" ayrı sınıflardır
    (`_NOT_A_RESPONSE`) ve tek satıra katlanmazlar. Künye sözleşmesi için bkz. üstteki blok."""
    from . import spend
    # "İSTENEN" ZİNCİR GİRİŞİNDE ÖLÇÜLÜR, sonunda değil: `active_model()` yapılandırmayı okur ve
    # zincir KOŞARKEN yapılandırma değişir (bir ayak 429 yiyip soğumaya girince `active_brain`
    # kayar). Koşu bittikten sonra okumak, "ne istedik" sorusunu koşunun KENDİ yan etkisiyle
    # cevaplamak olurdu — düşen ayak listeden silinmiş görünür ve ayrışma kendini gizlerdi.
    _istenen = active_model()
    out: dict = {"text": None, "beyin": None, "model": None,
                 # KÜNYE SÖZLEŞMESİ — `candidate_review` deseninin aynısı: alan VARSA
                 # `model` = CEVABI VEREN; alan YOKSA kayıt eski sözleşmedendir ("istenen"i taşır)
                 # ve RETRO-DÜZELTİLMEZ. İki anlam iki ad: "istenen" `model_istenen`de durur.
                 "model_kaynagi": "cevap_veren", "model_olculemedi": ZINCIR_MODEL_YOK,
                 "model_istenen": _istenen, "neden": {}}
    if spend.over_budget():
        out["neden"]["*"] = "monthly_budget"
        obs.log("nous_chain_budget_gate", kind=kind,
                detail="aylık bütçe dolu — ücretli beyinler kapalı")
        return out
    for p in brain_order():
        if not _provider_ready(p):
            out["neden"][p] = "no_credentials"
            continue
        rem = _provider_cooldown(p)
        if rem > 0:
            out["neden"][p] = "cooldown"
            obs.log("nous_chain_cooldown", provider=p, kind=kind, remaining_s=round(rem, 1))
            continue
        _trace_take()                      # önceki turdan artık neden kalmasın
        kunye, kunye_neden = None, None    # BU AYAĞIN künyesi — okuma noktası ayağın kendi yanında
        try:
            if p == "claude":
                txt = _claude_text(prompt, note=note or kind, max_tokens=8000)
                kunye = MODEL              # `_claude_text` gövdesi bu SABİTİ gönderir (import'ta bağlı)
            elif p == "nous":
                # YEREL ajan varsa O kullanılır (skill kütüphanesi + MCP araçları onun yolunda).
                if _nous_local():
                    txt = _agent_call(prompt, preload=preload, kind=kind, timeout=timeout,
                                      max_wait=max_wait)
                    # TÜKETEN OKUMA — ÇAĞRININ HEMEN YANINDA ve YALNIZ BU AYAKTA (bkz. üstteki blok).
                    kunye, kunye_neden = cevap_veren_model()
                else:
                    txt = _nous_text(prompt, note=note or kind)
                    kunye = _nous_portal_model()      # istek gövdesindeki adın TEK kaynağı
            else:
                txt = _gemini_call(prompt, note=note or kind)
                kunye = gemini_model()     # `_gemini_call`in URL'ye yazdığı adın AYNI kaynağı
        except Exception as e:
            limited, retry_after = _rate_limited(e)
            cooled = brain_stand_down(p, "rate_limit" if limited else "error", retry_after) if limited else 0.0
            obs.warn("nous_chain_failed", provider=p, kind=kind, error=f"{type(e).__name__}: {e}",
                     rate_limited=limited, cooldown_s=round(cooled, 1))
            out["neden"][p] = "failed"
            continue
        if txt and str(txt).strip():
            brain_recovered(p)
            out.update({"text": txt, "beyin": p, "model": kunye,
                        # UYDURMA YASAĞI: ölçülemeyen künye `active_model()`e (yapılandırma)
                        # SESSİZCE DÜŞMEZ — None kalır ve NEDENİ yanında durur.
                        "model_olculemedi": None if kunye else (kunye_neden or ZINCIR_MODEL_YOK)})
            if kunye and _istenen and kunye != _istenen:
                # AYRIŞMA GÖRÜNÜR OLUR (candidate_review'deki kardeşinin aynısı): zincirin yedeğe
                # düşmesi bir ARIZA değildir; arıza, düştüğünün SÖYLENMEMESİYDİ. Uyarı değil kayıt.
                obs.log("nous_chain_model_ayrismasi", kind=kind, beyin=p, cevap_veren=kunye,
                        istenen=_istenen,
                        detail="metni zincirin İSTENENDEN BAŞKA bir ayağı/modeli yazdı — künye "
                               "artık cevap vereni taşıyor; istenen ayağın neden boş döndüğü "
                               "nous_chain_empty/nous_chain_skipped olaylarında")
            return out
        reason, detail = _trace_take()
        reason = reason or EMPTY_UNKNOWN
        out["neden"][p] = reason
        if reason in _NOT_A_RESPONSE:
            obs.log("nous_chain_skipped", provider=p, kind=kind, reason=reason, detail=detail)
            continue
        obs.warn("nous_chain_empty", provider=p, kind=kind, reason=reason, detail=detail)
    obs.warn("nous_chain_unavailable", kind=kind, providers=out["neden"],
             detail="beyin zincirinin hiçbir ayağı metin döndürmedi")
    return out


# How hard the live search works when a single smart move doesn't clear the gate. A ±1-step move almost
# never beats +0.02 OOS, so the old fallback (propose_deterministic → one move) shipped nothing and the live
# strategy never evolved. The coordinate-descent search tries several values across ALL knobs through the
# SAME gate. Modest defaults bound the background cost (~budget walk_forwards); env-overridable.
SEARCH_BUDGET = int(os.environ.get("HERMES_SEARCH_BUDGET", "10"))
SEARCH_KMAX = int(os.environ.get("HERMES_SEARCH_KMAX", "3"))

# DETERMİNİSTİK BAKİR-DÜĞME YOLU — dağıtım anahtarı. Varsayılan AÇIK; `HERMES_VIRGIN_FALLBACK=0`
# ile kapatılırsa `reflect_once` birebir eski hâline döner (beyin yoksa doğrudan aramaya düşer).
VIRGIN_FALLBACK = os.environ.get("HERMES_VIRGIN_FALLBACK", "1") != "0"


def _virgin_value(spec: dict, live):
    """Bakir bir düğme için TEK deterministik değer: aralığın ORTA NOKTASI, adıma oturtulmuş.

    Orta nokta seçilir çünkü bakir bir düğmede "hangi yön" sorusunun kanıtı YOKTUR — bir adımlık
    hareket, hiç ölçülmemiş bir aralıkta ölçüm değil dokunuştur. Orta nokta canlı değerin ta
    kendisiyse (ör. aç/kapa düğmesinde) aralığın DENENMEMİŞ yarısına bir adım gidilir; o da no-op
    ise None döner ve çağıran bir SONRAKİ bakir düğmeye geçer (sessiz atlama değil: olaya yazılır).
    """
    lo, hi, step, typ = spec["min"], spec["max"], spec["step"], spec["type"]
    from . import guard as _g

    def _snap(x):
        """Değeri düğmenin ADIM ızgarasına oturtur, [min, max] aralığına kıstırır ve tipe göre
        yuvarlar (int → tam sayı, float → 4 hane) — sınır dışı ya da ızgara dışı değer üretilmez."""
        v = lo + round((float(x) - lo) / step) * step
        v = min(hi, max(lo, v))
        return int(round(v)) if typ == "int" else round(float(v), 4)

    orta_ham = (float(lo) + float(hi)) / 2.0
    orta = _snap(orta_ham)
    if live is None or not _g._equalish(live, orta, typ):
        return orta
    yon = 1 if float(live) <= orta_ham else -1
    v = _snap(float(live) + yon * step)
    return None if _g._equalish(live, v, typ) else v


def propose_virgin_knob() -> dict | None:
    """BEYİN YOKKEN ÜRETİLEN TEK DETERMİNİSTİK HAREKET — bakir düğmelerden (N00002).

    ESKİ HÂL: beyin zinciri boş dönünce `reflect_once` TEK bir akıllı hamle
    üretmeden doğrudan koordinat-inişi aramasına düşüyordu; `reflect.propose_deterministic` hermes'in
    yolunda HİÇ çağrılmıyordu (yalnız `reflect --auto` CLI'sinde). Yani "beyinsiz gecede tek hamle"
    yuvası BOŞTU. Arama sırası zaten denenmemiş düğmeleri öne alıyor (`_ucb_rank` → +inf) ama arama
    sondaları DEFTERE YAZILMAZ: bakir düğme aramada denense bile "hiç önerilmemiş" kalır, yani kör
    nokta kapanmaz ve H2 karnesi hiç değişmez.

    YENİ HÂL: yuva, H2'nin bakir listesinden deterministik bir öneriyle doldurulur. Öneri normal
    boru hattından geçer (`reflect.submit` → guard → OOS kapısı → sürüm) — ship yetkisi DEĞİŞMEDİ.
    K/`k_probes` muhasebesi de değişmez: `probes_tested` alanı YAZILMAZ, yani submit onu 1 okur —
    tek-adaylı bir öneri için LLM yolunun bugün yaptığının birebir aynısı.

    GUARD ÖN-DENETİMİ ZORUNLU: guard'a takılan bir öneri deftere `rejected_by_guard` satırı yazar ve
    düğme "denenmiş" olur — yani bakir listesinden HİÇ ÖLÇÜLMEDEN düşer. Ön-denetim aynı guard'ı
    aynı argümanlarla (gerçek aylık kota dahil) çağırır, geçmeyeni ADIYLA atlar."""
    from . import guard as _g
    kn = virgin_knobs()
    if not kn:
        obs.log("hermes_virgin_none", detail="bakir düğme kalmadı ya da H2 listesi okunamadı — "
                                             "deterministik yol öneri ÜRETMEDİ, arama devrede")
        return None
    try:
        current = config.load_strategy()
        params = current.get("params", {}) or {}
        bounds = config.bounds()
        goal = config.goal()
        hyps = memory.all_hypotheses()
        accepted = memory.accepted_this_month()
    except Exception as e:
        obs.warn("hermes_virgin_state_unreadable", error=f"{type(e).__name__}: {e}",
                 detail="deterministik bakir yol kurulamadı — arama devrede")
        return None
    atlanan = []
    for r in kn:
        var = r["knob"]
        spec = bounds.get(var)
        if not spec:
            atlanan.append(f"{var}:bounds_yok")
            continue
        new = _virgin_value(spec, params.get(var))
        if new is None:
            atlanan.append(f"{var}:no_op")
            continue
        v = _g.validate_change({"variable": var, "new": new}, params, bounds, goal, hyps, accepted,
                               params_by_regime=current.get("params_by_regime"))
        if not v.ok:
            atlanan.append(f"{var}={new}:{'; '.join(v.reasons)[:80]}")
            continue
        # ÖNERİ SÖZLÜĞÜ BURADA KURULUR, `reflect._proposal` ÇAĞRILMAZ: h1b yasa-çivisi
        # (`test_hermes_audit_v28`) hermes'in `reflect` üzerinden YALNIZ kapı yollarını çağırmasını
        # şart koşar (`submit` / `search_and_submit`). Özel bir yardımcıya uzanmak o sınırı deler.
        prop = {
            # KAYNAK ETİKETİ AYRI: defterde "deterministic" (reflect'in sezgisel yolu) ile bakir
            # düğme yolu ayırt edilemezse bu turun etkisi ölçülemez.
            "source": "deterministic:virgin",
            "variable": var, "new": new, "old": params.get(var),
            "rationale": (f"keşif: `{var}` bounds.yaml'da var ama defterde HİÇ hipotez taşımamış "
                          f"(H2 bakir listesi, {len(kn)} düğme); aralığın orta noktası ölçülüyor"),
            "predicted_direction": "improve_oos_score",
            # TAHMİN KAPININ KENDİ MARJINA ÇIPALANIR: bakir bir düğmede beklenti YOKTUR, o yüzden
            # uydurulmuş bir sayı yerine "en azından barajı geçmeli" denir. Tahmin H1 karnesinde
            # ölçülür — yani bu yolun iyimserliği zamanla kanıtla görünür olur.
            "predicted_delta": float(reflect.GATE_MARGIN),
            # SABİT VE DÜŞÜK, KALİBRASYONDAN TÜRETİLMEZ: geçmiş isabet oranı bu düğme hakkında
            # HİÇBİR ŞEY söylemez (düğme hiç denenmedi); oradan güven türetmek, ilgisiz bir tarihi
            # kanıt gibi taşımaktı. 0.35 bir keşif önceliğidir, bir iddia değil.
            "confidence": 0.35,
            "regime": store.read_json("regime.json", {}).get("regime", "any"),
            # AXIS-2 NOTU EKLENMEZ: skill tavsiyesi düğme keşfiyle ilgisizdir ve `submit` onu
            # deftere PENDING yazar — bu yol sessizce skill tavsiyesi üretmemeli.
            "skill_recommendation": None,
        }
        obs.log("hermes_virgin_proposal", variable=var, new=new, old=params.get(var),
                n_bakir=len(kn), skipped=atlanan[:6])
        return prop
    obs.warn("hermes_virgin_no_valid_candidate", n_bakir=len(kn), skipped=atlanan[:12],
             detail="bakir düğmelerin HİÇBİRİ guard'dan geçmedi — deterministik yol öneri üretmedi")
    return None


# =================================================================================================
# ARKA PLAN ÖN-ELEMESİ: D1 (KAYIT) + D2 (ÇİVİLEME)
# =================================================================================================
# ÖLÇÜLEN (kart `verdict.olcum`, canlı defterden MOTOR DEĞİŞMEDEN ÖNCE):
# `hermes_bg_proposal_rejected` 47 kez ateşledi (2026-08-02T14:00 → 2026-08-13T17:26) ve bu 47
# önerinin HİÇBİRİ hipotez defterine girmedi. Sertifika 47/47'de BİLİNİYORDU (hepsi `chop`,
# `None(auto)` SIFIR) — korkuluk KÖRLÜKTEN değil AYRIMSIZLIKTAN kesiyordu. 46/47 düz global.
# Kusur kapının HÜKMÜNDE değil GÖRÜNÜRLÜĞÜNDEydi: "üretim" ile "hayatta kalan" aynı sayıya
# katlanıyordu ("52 aslında 23" bulgusunun kökü).
BG_RED_DAMGA = "REDDEDILDI"      # D1 damgası — reddedilen öneri ADAY DEĞİLDİR, ayrı damga taşır
BG_ON_ELEME_PENCERE = 4000       # karne penceresi: olay defterinin son N satırı


def _bg_on_eleme_kaydi(proposal: dict | None, *, pvar: str, certified, red_nedeni: str) -> None:
    """D1 — REDDEDİLEN ÖNERİNİN TAM KAYDI, REDDEDİLDİ damgasıyla.

    ESKİ HÂL yalnız `variable` + `bg_regime` yazıyordu: kayıttan NE ÖNERİLDİĞİ (eski/yeni değer,
    hangi üretici, hangi gerekçe) okunamıyordu, yani reddin kendisi de sayılabilir bir kayıt
    değildi. Bu fonksiyon o kaydı tamamlar ve REDDİN NEDENİNİ makine-okunur bir alana koyar
    (`red_nedeni` ∈ {`global_sertifikasiz`, `farkli_rejim`}); okuyucusu `bg_on_eleme_karnesi`.

    DAMGA NEREYE KONDU ve NEDEN `hypotheses.jsonl` DEĞİL — ÖLÇÜLDÜ, SEÇİLDİ, GEREKÇELENDİ.
    Kill kriteri MUTLAK: "D1 kaydı öneri defterine GERÇEK öneri gibi girerse geçersiz —
    reddedilen öneri 'aday' değildir; ayrı damga şart, yoksa o bulgunun TERS YÖNÜ doğar (sayı bu kez
    ŞİŞER)". Hipotez defterinin TÜM tüketicileri tarandı; sekizi satırı DURUMA BAKMADAN sayar ve
    ÜÇÜ yalnız sayı şişirmez, ÖĞRENME DÖNGÜSÜNÜ BOZAR:
      (a) `analytics.dead_families` (`analytics.py` → `dead_families`) durum süzgeci TAŞIMAZ ve
          `DEAD_FAMILY_MIN_N = 3`'tür. Ölçülen dağılımda `entry.w_turnover` 21 satır demektir →
          aile ANINDA "ölü" ilan edilir, düğme `hermes.virgin_knobs()`un bakir listesinden DÜŞER.
          Yani reddedilen öneriler öneri UZAYINI daraltırdı — düzeltmenin tam tersi.
      (b) `watchdog._learning_liveness` (`watchdog.py` → `_learning_liveness`) yaşı `ts`ten ölçer ve 168 saatte
          "öğrenme durdu" der. TAZE bir satır bu alarmı SIFIRLAR — bu kusuru gösterebilecek TEK
          alarm, kusurun kendi kaydıyla maskelenirdi.
      (c) `selfreview`ın 25/15 satırlık pencereleri (`selfreview._near_miss_attention` +
          `selfreview.contradictions`) düğmeyi "denendi" sayar ve kanıt→hipotez dikkat satırlarını BASTIRIR; ayrıca satır başına gerçek
          bir hipotezi pencereden DIŞARI iter.
    Ek olarak `api.py` → `api_public_summary` (`/api/public/summary`) → `hypotheses_total` KAMUYA AÇIK ship-oranının
    PAYDASIdır (landing.js:68) ve `selfreview.build` + `web/app.js:5945` `startswith("rejected")`
    süzgeciyle reddi GERÇEK KAPI REDDİYLE aynı kovaya koyar. Bu tüketicilerin HİÇBİRİ bu turun
    dosya sınırında değildir, dolayısıyla kill kriteri hipotez defterinde SAĞLANAMAZDI.

    SEÇİLEN YER: `events.jsonl` — `ledgers.CONTRACTS`ta SÖZLEŞMELİ bir defterdir (yazar `obs.py`,
    tüketiciler `api`/`watchdog`/`selfreview`/`notify`/`analytics`), aday sayan HİÇBİR tüketicisi
    yoktur, ve kayıt oraya AYRI DAMGAYLA girer — "ayrı damga" şartının en sert biçimi. Ayrıca
    D2'den sonra bu dalın nüfusu ölçülen 47'den 1'e iner: `@`siz öneriler artık ÇİVİLENİP
    `reflect.submit`e gider ve GERÇEK bir defter satırı (guard/kapı reddi ya da ship) üretir —
    yani "üretim deftere girsin" isteğinin ASIL gövdesini D2 karşılar, D1 artığı kapatır.

    KAYIT DÜŞERSE TUR DÜŞMEZ: muhasebe kanalının arızası öğrenme turunu öldürmemeli — ama sessiz
    de kalmaz (aşağıdaki ikinci uyarı)."""
    p = proposal if isinstance(proposal, dict) else {}
    try:
        obs.warn("hermes_bg_proposal_rejected",
                 # ESKİ ALANLAR BİREBİR DURUYOR: kartın retro ölçümü (47 sayımı + değişken
                 # dağılımı) bu iki alandan okundu; adlarını değiştirmek kanıt zincirini koparırdı.
                 variable=pvar or "(global)", bg_regime=certified,
                 # --- D1: REDDEDİLDİ DAMGASI + TAM ÖNERİ KAYDI ---
                 damga=BG_RED_DAMGA, red_nedeni=red_nedeni,
                 old=p.get("old"), new=p.get("new"), source=p.get("source"),
                 # Gerekçe KIRPILIR: olay defteri satır-başına küçük kalmalı (27k+ satır, tam
                 # dosya taranarak okunuyor); tam metin zaten öneriyi üreten olayda durur.
                 rationale=str(p.get("rationale") or "")[:240],
                 detail="arka plan turunda GLOBAL ya da farklı-rejim öneri reddedildi — canlı "
                        "olmayan rejimin kanıtı yalnız o rejimin params_by_regime'ine girebilir")
    except Exception as e:  # sessiz-yutma: kayıt kanalının arızası ÖĞRENME TURUNU düşürmemeli — red zaten uygulandı, yalnız muhasebesi eksik kaldı ve o eksiklik ikinci bir uyarıyla ADIYLA duyuruluyor
        try:
            obs.warn("hermes_bg_on_eleme_kaydi_dustu", error=f"{type(e).__name__}: {e}",
                     variable=pvar or "(global)",
                     detail="D1 kaydı YAZILAMADI — ret uygulandı ama defterde izi yok; ön-eleme "
                            "karnesi bu turu SAYAMAZ (uydurma yerine eksik sayılır)")
        except Exception:  # sessiz-yutma: ikinci kayıt kanalı da düştü — üçüncü bir kanal YOK ve muhasebe denemesi çağıranı düşüremez
            pass


def bg_on_eleme_karnesi(olaylar: list | None = None, n: int = BG_ON_ELEME_PENCERE) -> dict:
    """ÖN-ELEME KARNESİ (YASA 6 okuyucusu) — "üretim" ile "hayatta kalan" AYRI iki sayı.

    D1 kaydının TÜKETİCİSİ budur: `exploration_share()` bunu kendi karnesine gömer,
    `analytics.hermes_scorecard()` o karneyi olduğu gibi dışa verir (`analytics.py` → `hermes_scorecard`) → pano.
    Okuyucusuz bir damga, bugün düzelttiğimiz kusurun ikinci kuşağı olurdu.

    İKİ SAYI, İKİSİ DE OLAY DEFTERİNDEN:
      * `reddedilen` — korkuluğun DÜŞÜRDÜĞÜ öneriler, nedenine göre kırılımlı. `red_nedeni`
        taşımayan satırlar `damgasiz` kovasına düşer ve UYDURULMAZ: damga bu turda eklendi, ondan
        önceki 47 satır retro damga yasağı gereği damgasız kalır ve öyle SAYILIR.
      * `rejimlendirilen` — D2'nin KURTARDIĞI öneriler (`x` → `x@<sertifika>`). Bu sayı bir
        BAŞARI İDDİASI DEĞİLDİR: çivilenen öneri guard/bounds ve probgate'ten yine geçmek
        zorundadır. Ölçtüğü tek şey "kapıya HİÇ ULAŞAMAMA" kusurunun kapandığıdır (kartın `sinir`
        bloğu: ship sayısı DEĞİL, kapıya ULAŞAN öneri sayısı).

    PENCERE BEYANLIDIR: olay defterinin son `n` satırı taranır, yani sayılar KÜMÜLATİF DEĞİLDİR.
    `olaylar` enjekte edilebilir (`exploration_share`in `fam`/`bakir` deseni) — aynı defteri iki
    kez taramak yalnız maliyet değil, iki okuma arasına düşen bir yazımla TUTARSIZLIK riskidir."""
    beyan = (f"olay defterinin son {n} satırı tarandı — sayılar KÜMÜLATİF DEĞİL, pencerelidir; "
             f"`damgasiz` kovası damga eklenmeden önce yazılmış satırlardır (retro damga yasağı)")
    if olaylar is None:
        try:
            olaylar = store.read_jsonl("events.jsonl", limit=n)
        except Exception as e:
            obs.warn("hermes_on_eleme_karnesi_okunamadi", error=f"{type(e).__name__}: {e}",
                     detail="olay defteri okunamadı — ön-eleme ÖLÇÜLEMEDİ (sıfır YAZILMADI)")
            return {"pencere": n, "reddedilen": None, "rejimlendirilen": None,
                    "beyan": "olay defteri okunamadı — ön-eleme ÖLÇÜLEMEDİ (uydurulmadı)"}
    nedenler: dict[str, int] = {}
    n_red = n_cvl = 0
    son_red = son_cvl = None
    for e in olaylar:
        ad = e.get("event")
        if ad == "hermes_bg_proposal_rejected":
            n_red += 1
            k = str(e.get("red_nedeni") or "damgasiz")
            nedenler[k] = nedenler.get(k, 0) + 1
            son_red = {"ts": e.get("ts"), "variable": e.get("variable"),
                       "bg_regime": e.get("bg_regime"), "red_nedeni": e.get("red_nedeni")}
        elif ad == "hermes_bg_proposal_rejimlendi":
            n_cvl += 1
            son_cvl = {"ts": e.get("ts"), "eski": e.get("eski"), "yeni": e.get("yeni"),
                       "sertifika": e.get("sertifika")}
    return {"pencere": n,
            "reddedilen": {"n": n_red, "damga": BG_RED_DAMGA,
                           "nedenler": dict(sorted(nedenler.items())), "son": son_red},
            "rejimlendirilen": {"n": n_cvl, "son": son_cvl},
            "beyan": beyan}


def reflect_once(target_regime: str | None = "auto", *, background: bool = False) -> dict:
    """Tek canlı yansıma — gövde `_reflect_once_govde`de (tasarım gerekçeleri orada).

    GÜVENLİK AĞI (2026-08-12 asılı-arama vakası): gövde HANGİ yoldan çıkarsa çıksın —
    normal dönüş, içerideki phase="error" yolu ya da bugün var olmayan bir istisna
    yolu — bayrak `running=True` BIRAKILAMAZ. Mevcut hata-yolu yazımları DURUYOR; bu ağ yalnız
    onların kaçırdığı bir çıkışta devreye girer (normalde no-op: bayrak zaten temizlenmiştir).
    Kadans tarafındaki bayatlık yasası (`sprint._arama_durumu`) aynı sınıfın SÜREÇ-DIŞI emniyetidir;
    bu ağ ise bayrağı asılı bırakmamanın SÜREÇ-İÇİ birinci hattıdır."""
    try:
        return _reflect_once_govde(target_regime, background=background)
    finally:
        if SEARCH_PROGRESS.get("running"):
            _progress(running=False, phase="error", kaynak="reflect_once_finally_agi")


def _reflect_once_govde(target_regime: str | None = "auto", *, background: bool = False) -> dict:
    """One live reflection. A single smart move (Claude, if a key is set) is tried first; if it doesn't
    clear the gate — or there's no key — we fall through to the systematic COORDINATE-DESCENT SEARCH across
    all knobs on the PRODUCTION windows. That is the escape from the ±1 trap that lets the live strategy
    actually evolve. submit() (inside both paths) remains the SOLE ship authority — the gate is unchanged.
    target_regime: the regime the CALLER's horizon guardrail certified ("auto" → read regime.json now).
    The standby loop passes its certified regime so a regime flip between the horizon check and the search
    (the walk takes minutes) can't retarget the ship into an uncertified regime.

    `background` (C16) — ARKA PLAN TURU: CANLI OLMAYAN bir rejimin birikmiş kanıtıyla
    koşulan yansıma (`hermes_runtime._bg_ready_regime` seçer). Bu bayrak olmadan çağrı, kanıtın hangi
    rejimden geldiğini BİLMİYORDU ve `_bg_ready_regime`in emniyet beyanı ("ship yalnız
    params_by_regime[o rejim]'i değiştirir — canlı davranış rejim dönene dek değişmez") kodda
    KARŞILIKSIZDI: bg rejimi `trend_up` olduğunda aşağıdaki `!= "trend_up"` istisnası devreye giriyor,
    arama GLOBAL koşuyor ve düz `params`a ship ediyordu — yani chop canlıyken chop davranışı, chop'un
    hiç sertifika vermediği kanıtla ANINDA değişiyordu (canlı state'te birebir doğrulandı: regime=chop,
    bg=trend_up, params_by_regime dört rejimde de boş).

    SEÇİLEN VARYANT: TURU ATLAMAK DEĞİL, ARAMAYI O REJİME ZORLAMAK. Gerekçe: "bg rejimi canlıdan
    farklıysa atla" kuralı bg yansımasının TANIMINI siler (bg turu zaten her zaman canlı-dışı bir
    rejimdir — özelliğin varlık sebebi budur) ve chop'ta yaşarken trend_up defterindeki 57 işlemi
    yeniden israfa çevirirdi. Zorlama ise beyanı GERÇEK yapar: her sonda `var@{rejim}` olur,
    `versioning.bump` onu `params_by_regime[rejim]`e yazar, canlı davranış rejim dönene dek değişmez.
    Atlama yalnız SON ÇARE olarak kalır: rejim adı geçerli değilse (kapsanamıyorsa) tur koşmaz —
    çünkü kapsanamayan bir bg turu, tam olarak kapatılan deliğin kendisidir."""
    _progress_temizle()          # kapıdan geçen temizleme — disk aynası da sıfırlanır (Ö-50)
    # --- K1 DURAKLATMA (EDG-2026-048 NO-GO, 2026-08-23): duraklatılmış rejime SERTİFİKALI arka
    # plan turu HİÇ koşmaz. Koşsaydı hem D2 çivilemesi hem rejim-zorlamalı arama her sondayı
    # `var@chop`a çevirirdi — üretim yasağının tam kendisi. Atlama sessiz değil OLAYDIR
    # (`bg_reflection_skipped_unscoped` emsali). Notlandırma/teyit yolları bu daldan bağımsız;
    # canlanma yalnız yeni kartla (config.URETIMI_DURAKLATILAN_REJIMLER).
    if background and target_regime in config.URETIMI_DURAKLATILAN_REJIMLER:
        obs.warn("bg_reflection_skipped_paused_regime", target_regime=str(target_regime),
                 kart="EDG-2026-048",
                 detail="'@chop' üretimi duraklatıldı (EDG-2026-048 NO-GO) — bg turu koşmadı; "
                        "mevcut @chop kayıtları/notlandırma/teyit kapıları aynen, canlanma "
                        "yalnız yeni kartla")
        _progress(running=False, phase="skipped")
        return {"status": "bg_regime_paused", "regime": target_regime,
                "beyan": "'@chop' üretim duraklatması (EDG-2026-048 NO-GO) — tur atlandı"}
    proposal = propose_with_llm()
    if proposal is None and VIRGIN_FALLBACK:
        # BEYİNSİZ TUR ARTIK BOŞ GEÇMİYOR: tek akıllı hamle yuvası bakir bir düğmeyle doldurulur.
        # Öneri üretilemezse (bakir kalmadı / hepsi guard'a takıldı) davranış BİREBİR eski hâl —
        # doğrudan koordinat-inişi aramasına düşülür.
        proposal = propose_virgin_knob()
    if proposal is not None:
        # A Claude var@regime proposal must target the CERTIFIED regime (or be global): the horizon
        # guardrail certified evidence for ONE regime — shipping an override into a different, never-
        # certified regime through this side door would bypass the whole guardrail.
        pvar = str(proposal.get("variable") or "")
        preg = pvar.split("@", 1)[1] if "@" in pvar else None
        certified = None if target_regime == "auto" else target_regime
        # --- D2 — ÇİVİLEME: `@`SİZ ÖNERİ ATILMAZ, SERTİFİKALI REJİME YENİDEN YAZILIR --
        # KORKULUK BOZULMUYOR, GÜÇLENİYOR. Korkuluğun invaryantı
        # "kanıt kendi rejimini terk etmesin"di; RET bu invaryantı sağlar ama işi çöpe atar, YENİDEN
        # YAZIM aynı invaryantı sağlar ve işi korur: `chop` sertifikalı kanıt yalnız
        # `params_by_regime["chop"]`i değiştirir, canlı-DIŞI rejimin kanıtı düz `params`a SIZMAZ
        # (o delik kapalı kalır).
        # ÜÇ ŞART DA ZORUNLU, ÜÇÜ DE ÖLÇÜLMÜŞ BİR VAKAYA KARŞILIK GELİR:
        #   `background`            — CANLI tur DEĞİŞMEZ; global muafiyet canlıda meşrudur.
        #   `preg is None`          — zaten rejim-hedefli öneri yeniden yazılmaz (aşağıdaki dallar).
        #   `certified in VALID_REGIMES` — sertifika BİLİNMİYORSA (`auto`/None) hiçbir şey değişmez:
        #       hangi rejimin sertifikalı olduğu UYDURULAMAZ. Geçersiz bir rejim ADI da çivilenmez —
        #       o turda arama zaten `bg_reflection_skipped_unscoped` ile hiç koşmaz (aşağısı), yani
        #       kapsanamayan bir tura öneri çakmak, kimsenin notlandıramayacağı bir değişken üretirdi.
        # `pvar` BOŞSA çivilenmez: `@chop` biçiminde adsız bir değişken üretmek uydurma olurdu.
        # YENİDEN YAZILAN ÖNERİ MUAF DEĞİLDİR: aşağıdaki `reflect.submit` yolu guard/bounds
        # doğrulamasını AYNEN uygular (`guard.validate_change` → base params/bounds/regime kontrolü)
        # ve düşerse öneri düşer — kartın beyanlı sınırı: "kurtarılan önerilerin İYİ olduğu İDDİA
        # EDİLMİYOR; probgate'ten yine geçmek zorundadır".
        if background and pvar and preg is None and certified in config.VALID_REGIMES:
            _eski = pvar
            pvar, preg = f"{_eski}@{certified}", certified
            proposal = {**proposal, "variable": pvar,
                        # GEREKÇE DE YENİDEN YAZILIR: defterde "bu öneri global doğdu, rejime
                        # çivilendi" okunabilmeli — sessiz dönüşüm bu turun düzelttiği kusurun
                        # ta kendisidir.
                        "rationale": (f"[rejime çivilendi: {_eski} → {pvar}; arka plan turu "
                                      f"{certified} sertifikalı — kanıt kendi rejimini terk etmiyor] "
                                      + str(proposal.get("rationale") or ""))}
            obs.log("hermes_bg_proposal_rejimlendi", eski=_eski, yeni=pvar, sertifika=certified,
                    source=proposal.get("source"),
                    detail="arka plan turunda GLOBAL doğan öneri ATILMADI, sertifikalı rejime "
                           "ÇİVİLENDİ — guard/bounds doğrulaması reflect.submit'te AYNEN koşar")
        if background and (preg is None or (certified is not None and preg != certified)):
            # C16 (b) BACAĞI: sertifika kontrolü `preg is None` hâline DE uygulanır — ama YALNIZ arka
            # plan turunda. Global muafiyet ("or be global", aşağıdaki dal) CANLI turda meşrudur:
            # canlı rejimin kanıtı düz `params`ı da meşru biçimde ayarlar. Arka plan turunda AYNI
            # muafiyet, canlı-DIŞI bir rejimin kanıtıyla canlı davranışı değiştirme ruhsatına dönüşür
            # — LLM/bakir-düğme yolu, aramayı rejime zorlamanın etrafından dolaşan bir yan kapıdır.
            # D2'DEN SONRA BU DAL İKİ VAKAYA İNER (ölçüm: 1/47 + 0/47) ve İKİSİ DE KASITLIDIR:
            #   (1) `preg is not None and preg != certified` — FARKLI rejime giden öneri. Korkuluğun
            #       ASIL hedefi budur; çivileme onu KURTARMAZ, çünkü kurtarmak kanıtı sahibi olmayan
            #       bir rejime taşımak olurdu.
            #   (2) `certified` bilinmiyor (`auto`/None) ya da geçerli bir rejim adı değil — sertifika
            #       uydurulamaz, bugünkü ret AYNEN sürer.
            _neden = "farkli_rejim" if preg is not None else "global_sertifikasiz"
            _bg_on_eleme_kaydi(proposal, pvar=pvar, certified=certified, red_nedeni=_neden)
            proposal = None                     # fall through to the (bg-regime-scoped) search
        elif preg is not None and certified is not None and preg != certified:
            obs.warn("hermes_proposal_uncertified_regime", variable=pvar, certified=certified)
            proposal = None                     # fall through to the (certified-regime) search
        # --- K1 DURAKLATMA (EDG-2026-048): yukarıdaki dallardan SAĞ ÇIKAN '@chop' hedefli öneri
        # de üretimden düşer — kaynağı LLM ya da bakir-düğme, tur canlı ya da bg fark etmez
        # (canlı-chop turunda preg == certified olduğundan yukarıdaki dallar onu YAKALAMAZ; bg
        # sertifikası chop olan tur zaten gövde başında atlandı). Reddedilen öneri hipotez
        # defterine GİRMEZ (aday değildir, D1 emsali); arama yoluna düşülür ve o kapsam da
        # aşağıda duraklatılmış rejime verilmez. Canlanma yalnız yeni kartla.
        if proposal is not None and preg in config.URETIMI_DURAKLATILAN_REJIMLER:
            obs.warn("hermes_proposal_paused_regime", variable=pvar, kart="EDG-2026-048",
                     detail="duraklatılmış rejime ('@chop') öneri üretilmez — EDG-2026-048 NO-GO; "
                            "canlanma yalnız yeni kartla")
            proposal = None                     # fall through to the (paused-regime-free) search
    if proposal is not None:
        obs.log("hermes_proposal", source=proposal.get("source", "llm"), variable=proposal["variable"], new=proposal["new"])
        result = reflect.submit(proposal)
        obs.log("hermes_result", source=proposal.get("source", "llm"), status=result.get("status"))
        if result.get("status") == "shipped":
            return result
        # the single idea didn't ship — don't give up, run the systematic search instead
    from . import dataset
    bars, index = dataset.load()
    # Phase 3 dynamic regime profiles: when the LIVE regime is a non-default one (the horizon guardrail
    # just certified enough trades + calendar span IN that regime), target the search at it — every probe
    # becomes var@{regime}, graded only on that regime's slice, shipping into params_by_regime. Under
    # trend_up (the regime the global params were tuned in, ~90% of the book) the search stays global:
    # the slice would be nearly the whole book anyway, and global ships must remain possible.
    # BU İSTİSNA CANLI TURA AİTTİR (C16): gerekçesi "trend_up canlıdır, dilimi zaten
    # defterin tamamıdır" cümlesine dayanır. Arka plan turunda o cümle YANLIŞtır ve istisna sessizce
    # sertifikasız bir global ship yetkisine dönüşür — `background` dalı onu kapatır.
    live_reg = store.read_json("regime.json", {}).get("regime") if target_regime == "auto" else target_regime
    if background:
        # ARKA PLAN TURU: `trend_up` İSTİSNASI BURADA GEÇERSİZDİR. O istisnanın gerekçesi ("defterin
        # ~%90'ı trend_up, dilim zaten tüm defter") YALNIZCA trend_up CANLI iken doğrudur; arka plan
        # turunda trend_up canlı DEĞİLDİR ve global ship, o rejimin kanıtıyla BAŞKA bir rejimin
        # (canlının) davranışını anında değiştirir. Ship yüzeyi bu yüzden rejimle sınırlanır.
        search_regime = live_reg if live_reg in config.VALID_REGIMES else None
        if search_regime is None:
            # KAPSANAMAYAN BG TURU KOŞMAZ. Alternatif "global koş" olurdu ve bu tam olarak kapatılan
            # deliktir. Sessiz de geçmez: atlama bir olaydır, çünkü bg turlarının hiç koşmadığı bir
            # sistem "arka plan öğrenmesi açık" diye rapor edilmeye devam ederdi.
            obs.warn("bg_reflection_skipped_unscoped", target_regime=str(target_regime),
                     detail="arka plan yansıması KAPSANAMADI (geçerli rejim adı yok) — global ship "
                            "yetkisiyle koşmak yerine tur atlandı; canlı-dışı kanıt global params'a "
                            "giremez")
            _progress(running=False, phase="skipped")
            return {"status": "bg_regime_unscoped", "regime": target_regime,
                    "beyan": ("arka plan turu rejimle sınırlanamadı — global ship yetkisiyle "
                              "koşulmadı (C16)")}
    else:
        # K1 DURAKLATMA (EDG-2026-048): duraklatılmış rejim CANLI turda da arama kapsamı OLMAZ —
        # kapsamlansaydı her sonda `var@chop` üretirdi. Kapsam globale düşer (Faz-3 öncesi
        # davranış; canlı rejimin kanıtıyla global ship canlı turda MEŞRUDUR — yukarıdaki C16
        # gerekçesindeki "or be global" muafiyeti). Chop dilimine ÖZGÜ ayar arayışı, ancak yeni
        # bir kartla duraklatma kalkınca geri gelir.
        search_regime = (live_reg if live_reg in config.VALID_REGIMES and live_reg != "trend_up"
                         and live_reg not in config.URETIMI_DURAKLATILAN_REJIMLER else None)
    # TAVAN ARTIK TÜRETİLİR (bütçe öz-ayarı): `SEARCH_BUDGET` sabiti TABAN olarak durur
    # (env override yolu birebir aynı); `search_budget()` kota durumuna göre onu açar. Türetimin
    # KENDİSİ olaya yazılır — "bugün neden 20 sonda koştu?" sorusu defterden cevaplanabilsin.
    _sb = search_budget()
    obs.log("hermes_search_start", budget=_sb["tavan"], k_max=SEARCH_KMAX, windows="production",
            regime=search_regime or "global", butce_kaynagi=_sb["kaynak"], butce_formulu=_sb["formul"])
    # The incumbent walk-forward runs BEFORE any probe and takes ~90s. Without naming that phase the UI sits
    # on a bare "başlıyor…" for a minute and a half — indistinguishable from a hang (exactly how this whole
    # observability bug was found). Name it, so a slow baseline never looks like a crash.
    _progress(running=True, phase="incumbent", i=0, total=None)

    def _on_probe(i, total, var, new, cand_oos, inc_oos, passes, best):
        """Arama geri çağrısı: her sondada canlı ilerlemeyi (`SEARCH_PROGRESS`, pano okur) günceller
        ve `hermes_search_probe` olayını basar. Karar VERMEZ — yalnız görünürlük."""
        _progress(running=True, phase="probing" if i else "planned", i=i, total=total,
                  variable=var, new=new,
                  candidate_oos=cand_oos, incumbent_oos=inc_oos, passes=passes, best=best)
        obs.log("hermes_search_probe", i=i, total=total, variable=var, new=new,
                candidate_oos=cand_oos, incumbent_oos=inc_oos, passes=passes)

    try:
        result = reflect.search_and_submit(bars, index, config.goal(), windows=None,
                                           budget=_sb["tavan"], k_max=SEARCH_KMAX, on_probe=_on_probe,
                                           regime=search_regime)
    except Exception:
        # never leave the dashboard showing a phantom in-flight search after a crash
        _progress(running=False, phase="error")
        raise
    s = result.get("search", {})
    obs.log("hermes_search_done", evaluated=s.get("evaluated"), cleared=s.get("cleared"),
            status=result.get("status"), best=s.get("best"))
    _progress(running=False, phase="done", status=result.get("status"),
              evaluated=s.get("evaluated"), cleared=s.get("cleared"), best=s.get("best"))
    return result


def _closed_count() -> int:
    """Kapanmış işlem sayısı = trades.jsonl satır sayısı (bekleme döngüsünün tetik tabanı)."""
    return len(store.read_jsonl("trades.jsonl"))


def loop(poll_seconds: int = 1800) -> None:
    """Standby loop: every 30 min read the heartbeat; reflect only when reflection_every new trades
    have closed and the system is healthy (not stale, not halted)."""
    goal = config.goal()
    every = int(goal["reflection_every"])
    from . import hermes_runtime as _hr
    last_reflect_at = _hr._restored_baseline()   # survive restarts — same fix as the in-process path
    print(f"[hermes] standby — will reflect every {every} closed trades. Model={MODEL}. baseline={last_reflect_at}")
    while True:
        try:
            if health.halted():
                print("[hermes] HALT present — watching, not reflecting.")
            elif health.stale(900):
                print("[hermes] heartbeat stale >15m — watching, not reflecting.")
            else:
                n = _closed_count()
                # SAME Phase-3 strict-AND horizon as the in-process supervisor (hermes_runtime): the VM/tmux
                # path must not reflect on raw trade count alone — that was the exact overfitting hole.
                from . import hermes_runtime as hr
                trades = store.read_jsonl("trades.jsonl")
                live_reg = store.read_json("regime.json", {}).get("regime")
                live_reg = live_reg if live_reg in config.VALID_REGIMES else None
                if n - last_reflect_at >= every and hr._horizon_ok(trades, last_reflect_at,
                                                                   regime=live_reg, min_trades=every):
                    reflect_once(target_regime=live_reg)
                    last_reflect_at = n
                    # persist so a tmux restart doesn't reset the 30-day horizon clock
                    st = store.read_json(hr.STATUS_FILE, {})
                    st["last_reflect_at"] = n
                    store.write_json(hr.STATUS_FILE, st)
                else:
                    hz = hr._horizon_progress(trades, last_reflect_at, live_reg, every)
                    print(f"[hermes] waiting — {n - last_reflect_at}/{every} new trades; horizon "
                          f"{hz['trades']}/{hz['trades_needed']} trades, {hz['span_days']}/{hz['min_days']}d "
                          f"in regime {live_reg or 'any'}.")
        except Exception as e:
            print(f"[hermes] error: {type(e).__name__}: {e}")
        time.sleep(poll_seconds)


def main(argv=None):
    """Hermes CLI'ı: `--kesif` keşif payı karnesi + bakir düğmeleri JSON basar (hiçbir şey
    YAZMAZ), `--once` tek yansıma koşar, aksi hâlde bekleme döngüsünü (`--poll` saniye) başlatır."""
    ap = argparse.ArgumentParser(description="Hermes — Meridian's reflection brain")
    ap.add_argument("--once", action="store_true", help="run a single reflection now")
    ap.add_argument("--loop", action="store_true", help="run the 30-min standby loop")
    ap.add_argument("--poll", type=int, default=1800)
    # YASA 6 TÜKETİCİSİ: keşif payı ölçülüp kimseye ulaşmazsa üretilmemiş sayılır. Karneyi basan
    # yollar (analytics.system_telemetry / /api/diagnostics) BAŞKA dosyaların malı; bu tur onlara
    # dokunmadı, ölçümün kendi okunabilir yüzeyi buraya kondu.
    ap.add_argument("--kesif", action="store_true",
                    help="keşif payı karnesi + bakir düğme listesi (JSON) — hiçbir şey yazmaz")
    args = ap.parse_args(argv)
    if args.kesif:
        print(json.dumps({"kesif_payi": exploration_share(), "bakir_dugmeler": virgin_knobs()},
                         ensure_ascii=False, indent=2, default=str))
    elif args.once:
        reflect_once()
    else:
        loop(poll_seconds=args.poll)


if __name__ == "__main__":
    main()
