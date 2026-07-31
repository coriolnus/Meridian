"""hermes.py — the brain. Reads state, forms ONE single-variable hypothesis with Claude, and
submits it through the SAME guarded pipeline the deterministic proposer uses (guard -> backtest
gate -> version bump -> memory). Hermes never edits strategy.yaml by hand; the engine decides what
ships. Every constraint stated to Hermes here is ALSO enforced in guard.py (Hard Rule 6) — this
prompt is a suggestion, guard.py is the law.

Runs on the VM in a detached tmux session (installed LAST, §7). Falls back to the deterministic
proposer when HERMES_API_KEY is absent, so the loop is never dead."""
from __future__ import annotations
import argparse
import json
import os
import sys
import threading
import time

from . import config, store, memory, reflect, health, obs, secrets

MODEL = os.environ.get("HERMES_MODEL", "claude-opus-4-8")

# Live view of the running coordinate-descent search, published per probe and read by
# hermes_runtime.status() → /api/hermes → dashboard. A search runs ~a dozen walk-forwards (many minutes);
# without this the operator sees only "reflecting: true" and cannot tell progress from a hang.
SEARCH_PROGRESS: dict = {}

HYP_SCHEMA = {
    "type": "object",
    "properties": {
        # `variable@regime` AÇIKÇA YAZILIR (2026-07-27): açıklama "exactly one key from bounds.yaml"
        # diyordu ama bağlamdaki `note_regime_conditional` rejim-koşullu biçimi ÖNERİYORDU — model
        # iki çelişen talimat görüyordu ve rejim düğmesini kullanmaktan kaçınıyordu. Şema hâlâ TEK
        # değişken ister; `@regime` soneki o değişkenin yalnız bir rejimdeki değerini hedefler.
        "variable": {"type": "string",
                     "description": "exactly one key from bounds.yaml; optionally suffixed '@regime' "
                                    "to tune that key for ONE regime only (e.g. 'exit.trail_atr_mult@chop'). "
                                    "Still counts as one variable."},
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
                "action": {"type": "string", "enum": ["shadow", "activate", "lean_in"]},
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
- Score by regime, not as one blur. An edge that only exists in chop is a real finding.

You improve the system along TWO axes:
  Axis-1 (primary, THIS output): tune ONE strategy parameter — auto-validated by the backtest gate.
  Axis-2 (optional): the context gives you `skill_library` — your full 67-skill toolkit, each with its
  live contribution (avg_r over n trades). Use it. A skill with a chronically NEGATIVE avg_r over a real
  sample is dragging the book; a strongly POSITIVE one is where the edge lives. If you see a clear case,
  add a `skill_recommendation` (shadow the loser, or lean on the winner). This is ADVISORY — the operator
  applies it — because the deterministic backtest does not execute the LLM skills, so it cannot gate them.
  Never recommend a protected skill (skill_library marks them). Omit the recommendation if nothing is clear.

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
        "vs_benchmark": analytics.benchmark_relative(),      # are you beating SPY, or just riding beta? (#33)
        "skill_library": _skill_library(),                   # your full toolkit + how each skill performs
        "note_regime_conditional": "You may tune one knob for one regime with 'variable@regime' "
                                    f"(regimes: {', '.join(config.VALID_REGIMES)}); it stays one_variable_only.",
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
            olculu.append({"name": s["name"], "does": does, "on": s["enabled"],
                           "avg_r": s["avg_r"], "n": s["n"], "needs": s["requires"],
                           "protected": s["protected"], "shadow": s["shadow"]})
        else:
            olcusuz.append(s["name"])
    return {"measured_or_protected": olculu,
            "unmeasured": olcusuz,
            "note": "unmeasured skills have n=0 live trades: no evidence exists to shadow or lean on "
                    "them, so only their names are listed. Axis-2 recommendations must cite avg_r/n."}


def _claude_text(user: str, *, note: str, schema: dict | None = None,
                 max_tokens: int = 4000) -> str | None:
    """Claude çağrısının TEK GÖVDESİ — METİN döner, ayrıştırma çağıranın işi.

    NEDEN AYRIŞTIRILDI (2026-07-30, nous sistem-değerlendirme katmanı): Katman B beyin zincirini
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
    resp = client.messages.create(
        model=MODEL, max_tokens=max_tokens,
        thinking={"type": "adaptive"},
        output_config={"effort": "high", "format": _fmt},
        # cache the fully-static system prompt (two-axis briefing) so it isn't billed at full input price
        # every reflection — the standby loop fires far more often than the 5-min cache TTL.
        system=[{"type": "text", "text": SYSTEM, "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": user}],
    )
    try:                                             # meter the call — cost is only known after it returns
        u = getattr(resp, "usage", None)
        if u is not None:
            cache_read = getattr(u, "cache_read_input_tokens", 0) or 0
            spend.record(getattr(u, "input_tokens", 0), getattr(u, "output_tokens", 0), MODEL,
                         note=f"{note} (cache_read={cache_read})")
    except Exception:  # sessiz-yutma: yardımcı/telemetri yolu; başarısızlığı karara girmez ve çağıran yedek değerle aynen devam eder
        pass
    text = next((b.text for b in resp.content if b.type == "text"), None)
    if not text:
        # 200 döndü ama metin bloğu yok: yalnız araç/düşünme bloğu ya da durdurma sebebi. "Başarılı"
        # sayılıp sessizce None dönmek, tam da kalibrasyonun neden hiç çift biriktirmediğinin cevabıydı.
        blocks = ",".join(sorted({getattr(b, "type", "?") for b in (resp.content or [])})) or "yok"
        _trace_note(EMPTY_TOOL_ONLY if "tool_use" in blocks else EMPTY_NO_TEXT,
                    detail=f"bloklar={blocks} stop={getattr(resp, 'stop_reason', '?')}")
        return None
    return text


def propose_with_claude() -> dict | None:
    # TEK TALİMAT KAYNAĞI (2026-07-27): burada inline bir kopya vardı ve `_user_prompt` ile
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
# Operatör isteği (2026-07-19): beyin Nous hermes-agent'a ve OAuth'lu Gemini'a bağlanabilsin. MİMARİ YASA
# DEĞİŞMEZ: hangi LLM konuşursa konuşsun yalnızca ÖNERİR — tek değişken, OOS walk-forward kapısı, ufuk
# koruması ve rollback aynen kalır. "Sürekli kendini güncelleyen döngü" bu kapılı yansıma döngüsüdür;
# beyin takılabilir, yasa takılabilir değil. Zincir: HERMES_BRAIN_ORDER sırasıyla anahtarı hazır olan ilk
# sağlayıcı; hata/boş cevapta zincir bir sonrakine düşer; hiçbiri yoksa ücretsiz deterministik önerici.
NOUS_DEFAULT_ENDPOINT = "https://inference.nousresearch.com/v1"
NOUS_DEFAULT_MODEL = "Hermes-4-405B"
GEMINI_DEFAULT_MODEL = "gemini-3.1-pro"   # operatör tercihi (2026-07-19): "gemini 3.1 pro olmalı"
DEFAULT_BRAIN_ORDER = "claude,nous,gemini"

# DÜŞÜNCE BÜTÇESİ (2026-07-26): gemini-3.x DÜŞÜNEN bir ailedir ve düşünce tokenları ÜRETİM tavanından
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

# ============ 429 SOĞUMA DEFTERİ + BOŞ-CEVAP SINIFLANDIRMASI (v66, 2026-07-22) ============
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
        return cur.pop(provider, None) is not None
    store.update_json(BRAIN_COOLDOWN_FILE, _mut, default={})


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
                  # (2026-07-26: nous ve gemini ikisi de gemini-3.5-flash'a gidiyordu).
                  "model_id": _model_id(p)}
    return out


def _model_id(p: str) -> str | None:
    """O sağlayıcıya GİDECEK model kimliği — `active_model()`in sağlayıcı-bağımsız hâli.

    NOUS'TA İKİ AYRI DÜNYA VAR ve varsayılan yalnız birinde meşrudur (2026-07-26):
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
        return secrets.get("NOUS_MODEL") or NOUS_DEFAULT_MODEL
    if p == "gemini":
        return secrets.get("GEMINI_MODEL") or GEMINI_DEFAULT_MODEL
    return None


def brain_chain_facts() -> dict:
    """ZİNCİR GERÇEKTEN YEDEKLİ Mİ — YALNIZ DOĞRUDAN SAYILABİLİR OLGULAR (2026-07-26).

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
    raw = secrets.get("HERMES_BRAIN_ORDER") or os.environ.get("HERMES_BRAIN_ORDER") or DEFAULT_BRAIN_ORDER
    known = {"claude", "nous", "gemini"}
    return [p.strip().lower() for p in raw.split(",") if p.strip().lower() in known]


def _provider_ready(p: str) -> bool:
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
    p = active_brain()
    if p == "claude":
        return MODEL
    if p == "nous":
        return secrets.get("NOUS_MODEL") or NOUS_DEFAULT_MODEL
    if p == "gemini":
        return secrets.get("GEMINI_MODEL") or GEMINI_DEFAULT_MODEL
    return None


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
            # KUYRUK DA BASILIR (2026-07-27). `t[:120]` yalnız BAŞI gösteriyordu; oysa KESİLME
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
    head = (t or "")[:400].lower()
    return any(m in head for m in _REFUSAL_MARKS)


# Kanıt paketi karakter tavanı. 1400 → 6200 (3b): H1 karnesi + H2 aile hafızası + eşik eğrisi
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
            # diye sunulursa ölçülmemiş bir sinyale dayanarak öneri üretir (2026-07-26).
            _re = sc.get("real") if isinstance(sc.get("real"), dict) else None
            if _re:
                pack["score_calibration"] = {"rank_ic": _re.get("rank_ic"), "n": _re.get("n"),
                                             "kaynak": "gerçek", "anlamli": _re.get("anlamli"),
                                             "monotone": sc.get("monotone_hint")}
            elif "real" in sc:
                # YENİ ŞEMA + GERÇEK DİLİM ÖLÇÜLEMEDİ. Havuzlanmış sayıyı yedek diye koymak, beyne
                # "işte skorun tahmin gücü" diye ALINMAMIŞ hipotetik girişlerin IC'sini sunmaktı ve
                # LLM onu prompt'ta gerekçe olarak alıntılıyordu (2026-07-26). Sayı yerine ANALİZİN
                # KENDİ HÜKMÜ gider: ölçülmemiş olduğu, bir sayının içinde saklanmadan söylenir.
                pack["score_calibration"] = {"skor_kalibrasyonu": sc.get("verdict")
                                             or "gerçek dilim ÖLÇÜLMEDİ — skorun tahmin gücü bilinmiyor"}
            else:
                # GERÇEK eski-şema dosyası (`real` anahtarı HİÇ yok): elde yalnız havuzlanmış değer
                # var ve kaynağı adıyla etiketlenerek verilir — sessizce düşürmek de kanıt kaybıdır.
                pack["score_calibration"] = {"rank_ic": sc.get("rank_ic"), "n": sc.get("n"),
                                             "kaynak": "havuzlanmış",
                                             "monotone": sc.get("monotone_hint")}
        # BİLEŞEN IC — KOMPAKT (Aşama 1.2, 2026-07-28). Beyin bugüne kadar yalnız BİLEŞİK skorun
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
        # ---- HERMES ETKİNLEŞTİRME PAKETİ H1+H2+H3 (2026-07-30) --------------------------------
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
        # YASA 4 (2026-07-21): kanıt paketi sessizce boşalırsa LLM ölçülmüş kalibrasyonları HİÇ
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
    "do_not_propose",               # H2 — §5 YAPMA listesi (makine-okunur)
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


# ================= ÜRETEÇ KEŞİF DENGESİ (N00002, 2026-07-30) =====================================
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

    Ölçülemeyen None (uydurma yasağı): boş defterde üç alan da None döner, sebebiyle birlikte."""
    hyps = memory.all_hypotheses()
    toplam = len(hyps)
    beyan = ("bakir isabet = öneri kendi ailesine defterdeki İLK dokunuş mu; ölü aile sınıflandırması "
             "H2'nin BUGÜNKÜ hükmüdür (öneri anındaki değil) — H2 anlık görüntü üretir ve geçmişe "
             "dönük ikinci bir tanım yazılmadı")
    if not toplam:
        return {"pencere": n, "n_olculen": 0, "n_defter": 0, "aile_dagilimi": None,
                "en_yogun_aile": None, "en_yogun_pay": None, "bakir_isabet": None,
                "olu_aile_tekrari": None, "bakir_dugme_kalan": None,
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
    (uygulamanın parçası — operatör isteği 2026-07-19), yoksa Portal API'ye düşer."""
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


# ==================================================================================================
# BÜTÇE ÖZ-AYARI — STATİK TAVANLAR KOTA DURUMUNDAN TÜRETİLİR (öğrenme otomasyonu turu, 2026-07-30)
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
    (#4) ajanın gerçekten KULLANIP kullanmadığını ölçmek için — sıfır ise MCP yatırımı atıl demektir.
    Özet yoksa/eşleşmezse -1 (bilinmiyor)."""
    import re as _re
    m = _re.search(r"(\d+)\s+tool calls?", stdout or "")
    return int(m.group(1)) if m else -1


def _agent_call(prompt: str, preload: tuple = (), kind: str = "generic",
                timeout: int = 300, max_wait: float = 0.0) -> str | None:
    """TÜM yerel-ajan çağrılarının tek kapısı (#1): skill senkronu + -s ön-yükleme + oran bütçesi +
    model düşüş zinciri (NOUS_MODEL → NOUS_FALLBACK_MODEL; boş oturumda bir kez düşer). None = çağrı
    yapılamadı/cevapsız — çağıran fail-open davranır. Ham stdout döner; parse çağıranın işi."""
    import subprocess
    bin_ = _hermes_bin()
    if not bin_:
        return None
    rem = brain_cooldown("agent")
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
    models = [m for m in dict.fromkeys([secrets.get("NOUS_MODEL"),
                                        secrets.get("NOUS_FALLBACK_MODEL")]) if m] or [None]
    for attempt, model in enumerate(models):
        if not _agent_budget_take(max_wait if attempt == 0 else 0.0):
            return None
        # --accept-hooks: config'teki hooks_auto_accept ile birlikte koruma hook'unu başsız çağrıda
        # otomatik onaylar (aksi halde 'not allowlisted' → hook ateşlemez, savunma sessizce ölürdü).
        cmd = [bin_, "chat", "--accept-hooks", "-q", prompt]
        for sk in preload:
            cmd += ["-s", sk]
        if model:
            cmd += ["--model", model]
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout,
                             env={**os.environ, "NO_COLOR": "1", "TERM": "dumb"})
        empty = out.returncode != 0 or _agent_reply_missing(out.stdout)
        tcalls = _agent_tool_calls(out.stdout)
        obs.log("agent_call", kind=kind, preloaded=len(preload), model=model or "varsayılan",
                attempt=attempt + 1, empty=empty, tool_calls=tcalls)
        if not empty:
            if tcalls >= 0:                          # #4 telemetri: MCP araç kullanımını biriktir
                try:
                    st = store.read_json("agent_tooluse.json", {"calls": 0, "with_tools": 0, "total_tools": 0})
                    st["calls"] += 1
                    st["with_tools"] += 1 if tcalls > 0 else 0
                    st["total_tools"] += tcalls
                    store.write_json("agent_tooluse.json", st)
                except Exception:  # sessiz-yutma: yardımcı G/Ç yolu; çağıran yokluğu zaten yedek değerle karşılıyor ve asıl okuma hatası store katmanında bir kez uyarılıyor
                    pass
            return out.stdout
    # ZİNCİR UZUNLUĞU DÜRÜST BİLDİRİLİR: canlı defterde bu satır "tüm model zinciri cevapsız" diyordu
    # ama tried=1'di — NOUS_FALLBACK_MODEL hiç ayarlanmamıştı, yani "düşüş zinciri" tek elemanlıydı.
    # Yedeğin YOKLUĞU, yedeğin BAŞARISIZLIĞI gibi okunuyordu.
    exhausted = _pool_exhausted()
    cooled = 0.0
    if exhausted:
        # Havuzun kendi kaydı 'exhausted/429' diyor: rotasyon absorbe EDEMEZ (sağlayıcı başına tek
        # kimlik). Ajanı da soğumaya al, yoksa her poll yeni bir süreçle aynı duvara çarpar.
        cooled = brain_stand_down("agent", f"pool_exhausted:{exhausted}")
    obs.warn("agent_call_empty", kind=kind, tried=len(models), chain=len(models),
             fallback_model_configured=bool(secrets.get("NOUS_FALLBACK_MODEL")),
             pool_exhausted=exhausted, cooldown_s=round(cooled, 1),
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


def _nous_text(user: str, *, note: str) -> str | None:
    """Nous'un UZAK ucunun (OpenAI-uyumlu) tek gövdesi — metin döner. Bkz. `_claude_text` notu."""
    import httpx
    base = (secrets.get("NOUS_ENDPOINT") or NOUS_DEFAULT_ENDPOINT).rstrip("/")
    model = secrets.get("NOUS_MODEL") or NOUS_DEFAULT_MODEL
    r = httpx.post(f"{base}/chat/completions",
                   headers={"Authorization": f"Bearer {secrets.get('NOUS_API_KEY')}",
                            "Content-Type": "application/json"},
                   json={"model": model, "max_tokens": 4000,
                         "messages": [{"role": "system", "content": SYSTEM},
                                      {"role": "user", "content": user}]},
                   timeout=120.0)
    r.raise_for_status()
    d = r.json()
    u = d.get("usage") or {}
    from . import spend
    spend.record(u.get("prompt_tokens", 0), u.get("completion_tokens", 0), model, note=note)
    ch = (d.get("choices") or [{}])[0] or {}
    msg = ch.get("message") or {}
    txt = str(msg.get("content") or "")
    if not txt.strip():                   # 200 OK ama içerik yok — sebebi ayır (araç çağrısı / kesilme)
        if msg.get("tool_calls") or msg.get("function_call"):
            _trace_note(EMPTY_TOOL_ONLY, detail=f"finish_reason={ch.get('finish_reason') or '?'}")
        elif str(ch.get("finish_reason") or "") in ("content_filter", "refusal"):
            _trace_note(EMPTY_REFUSAL, detail=f"finish_reason={ch.get('finish_reason')}")
        else:
            _trace_note(EMPTY_NO_TEXT, detail=f"finish_reason={ch.get('finish_reason') or '?'}")
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
    model = secrets.get("GEMINI_MODEL") or GEMINI_DEFAULT_MODEL
    headers = {"Content-Type": "application/json"}
    key = secrets.get("GEMINI_API_KEY")
    if key:
        headers["x-goog-api-key"] = key
    else:
        headers["Authorization"] = f"Bearer {secrets.get('GEMINI_OAUTH_TOKEN')}"
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
    d = r.json()
    um = d.get("usageMetadata") or {}
    from . import spend
    # düşünce tokenları FATURALANAN çıktıdır: defterde ayrı alanda görünür (düşünce kapalıyken alan
    # cevapta hiç bulunmaz → 0). Maliyet formülü DEĞİŞMEDİ; bkz. spend.record notu.
    spend.record(um.get("promptTokenCount", 0), um.get("candidatesTokenCount", 0), model,
                 note=note, thought_tokens=um.get("thoughtsTokenCount", 0))
    return _gemini_text(d) or None        # metin yoksa nedeni _gemini_text zaten işaretledi


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
            want = secrets.get("GEMINI_MODEL") or GEMINI_DEFAULT_MODEL
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


def sync_local_agent_gemini(enable: bool) -> dict:
    """Panodan girilen GEMINI_API_KEY'i YEREL hermes-agent'a taşır — operatör anahtarı TEK yerden
    (Ayarlar) girer, terminal/.env adımı yoktur. enable=True: mevcut model bloğu yedeklenir, ajanın
    .env'ine OPENAI_API_KEY yazılır (Gemini'ın OpenAI-uyumlu ucu bu adı okur) ve provider/base_url/model
    Gemini'a çevrilir. enable=False (anahtar silindi): .env satırı kaldırılır, yedeklenen Nous ayarı
    geri yüklenir. Anahtar değeri hiçbir yerde loglanmaz/yansıtılmaz."""
    import subprocess
    bin_ = _hermes_bin()
    if not bin_:
        return {"ok": False, "detail": "yerel hermes-agent kurulu değil"}
    home = os.path.expanduser("~/.hermes")
    env_path = os.path.join(home, ".env")
    backup_path = os.path.join(home, "meridian-model-backup.json")

    def _cfg(key, val):
        subprocess.run([bin_, "config", "set", key, val], capture_output=True, text=True, timeout=30)

    def _cfg_get(key):
        r = subprocess.run([bin_, "config", "get", key], capture_output=True, text=True, timeout=30)
        return (r.stdout or "").strip().splitlines()[-1].strip() if r.stdout else ""

    def _write_env(key_value: str | None):
        lines = []
        if os.path.exists(env_path):
            with open(env_path) as fh:
                lines = [l for l in fh.read().splitlines()
                         if not l.startswith(("GEMINI_API_KEY=", "GOOGLE_API_KEY="))]
        if key_value:
            lines.append(f"GEMINI_API_KEY={key_value}")
        import tempfile
        fd, tmp = tempfile.mkstemp(dir=home)
        with os.fdopen(fd, "w") as fh:
            fh.write("\n".join(lines) + "\n")
        os.replace(tmp, env_path)
        os.chmod(env_path, 0o600)

    try:
        if enable:
            key = secrets.get("GEMINI_API_KEY")
            if not key:
                return {"ok": False, "detail": "GEMINI_API_KEY boş"}
            if not os.path.exists(backup_path):   # ilk geçişte mevcut (Nous) ayarı yedekle
                prev = {"provider": _cfg_get("model.provider"), "base_url": _cfg_get("model.base_url"),
                        "default": _cfg_get("model.default")}
                with open(backup_path, "w") as fh:
                    json.dump(prev, fh)
            _write_env(key)
            model = secrets.get("GEMINI_MODEL") or GEMINI_DEFAULT_MODEL
            _cfg("model.provider", "gemini")            # yerli sağlayıcı — base_url override'ı KALDIRILIR
            subprocess.run([bin_, "config", "unset", "model.base_url"], capture_output=True, text=True, timeout=30)
            _cfg("model.default", model)
            obs.log("local_agent_switched", to="gemini", model=model)
            return {"ok": True, "detail": f"yerel ajan Gemini'a geçti · {model}"}
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
            obs.log("local_agent_switched", to="restored", model=restored)
            return {"ok": True, "detail": f"yerel ajan eski ayara döndü · {restored or 'değişmedi'}"}
    except Exception as e:
        return {"ok": False, "detail": f"senkron hatası ({type(e).__name__})"}


REVIEW_SKILLS = ("vcp-screener", "pullback-screener", "pre-trade-discipline-gate",
                 "position-sizer", "market-environment-analysis")
AGENT_SKILLS_DIR = os.path.expanduser("~/.hermes/skills")
AGENT_CONFIG = os.path.expanduser("~/.hermes/config.yaml")


def _repo_root() -> str:
    from . import config as _cfg
    return str(_cfg.ROOT)


def config_ensure_integrations() -> dict:
    """Yerel hermes-agent config.yaml'ına Meridian entegrasyonlarını IDEMPOTENT yazar (Tier 1+2):
      • mcp_servers.meridian — salt-okunur veri sunucumuz (analytics/cf/near-miss/rejim/kalibrasyon)
      • hooks.pre_tool_call — koruma hook'u (state/secrets/mode/emir yüzeylerini sert bloklar)
      • prompt_caching.cache_ttl → 1h (oturum-arası önek önbelleği; saf maliyet)
      • credential_pool_strategies — 429 rotasyon stratejisi (havuz varsa devreye girer)
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
    repo = _repo_root()
    guard = os.path.join(repo, "ops", "meridian-guard.sh")
    desired_mcp = {"command": sys.executable, "args": ["-m", "meridian.mcp_server"],
                   "env": {"PYTHONPATH": repo, "MERIDIAN_ROOT": repo},
                   "tools": {"resources": False, "prompts": False}}
    changed = []
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
        import tempfile
        shutil.copy2(AGENT_CONFIG, AGENT_CONFIG + ".meridian.bak")
        fd, tmp = tempfile.mkstemp(dir=os.path.dirname(AGENT_CONFIG))
        with os.fdopen(fd, "w") as fh:
            yaml.safe_dump(cfg, fh, allow_unicode=True, default_flow_style=False, sort_keys=False)
        os.replace(tmp, AGENT_CONFIG)
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
    tu = store.read_json("agent_tooluse.json", None)          # #4: MCP araç kullanım oranı
    if tu and tu.get("calls"):
        out["tool_use"] = {"calls": tu["calls"], "with_tools": tu.get("with_tools", 0),
                           "total_tools": tu.get("total_tools", 0),
                           "rate": round(tu.get("with_tools", 0) / tu["calls"], 2)}
    # havuz: sağlayıcı başına anahtar SAYISI + sağlığı (DEĞER YOK). Sağlık alanı v66'da eklendi:
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
    None. Yalnız YAKIN geçmişteki tükenme sayılır (pencere) — eski bir kayıt sonsuza dek bloklamasın."""
    prov = _agent_provider()
    h = pool_health().get(str(prov or ""), None)
    if not h or not h.get("keys") or h.get("healthy"):
        return None
    if h.get("exhausted") and (not h.get("last_status_at")
                               or time.time() - float(h["last_status_at"]) < POOL_EXHAUSTED_WINDOW_S):
        return str(prov)
    return None


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


def sync_agent_skills() -> dict:
    """Yerel ajanın skill seti = Meridian'ın ENABLED seti — birebir. İki yönde eşitler:
    (1) etkin olup linklenmemiş skill'ler symlink'lenir; (2) Meridian'ın DEVRE DIŞI bıraktığı ya da
    silinen skill'lerin linkleri sökülür (canlıda yakalanan kusur: 8 kapalı skill ajanda hâlâ
    aktifti — motorun 'kenar yok' dediği bilgiyle ajan düşünmeye devam ediyordu). YALNIZ bizim
    repoya çözümlenen symlink'lere dokunulur — ajanın kendi builtin klasörleri kutsaldır."""
    from . import skills as _sk
    repo = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "skills")
    enabled = {s2["name"] for s2 in _sk.catalog() if s2.get("enabled")}
    os.makedirs(AGENT_SKILLS_DIR, exist_ok=True)
    linked, pruned = [], []
    for name in sorted(enabled):
        src, dst = os.path.join(repo, name), os.path.join(AGENT_SKILLS_DIR, name)
        if os.path.isdir(src) and not os.path.exists(dst):
            try:
                os.symlink(src, dst); linked.append(name)
            except OSError:  # sessiz-yutma: yardımcı G/Ç yolu; çağıran yokluğu zaten yedek değerle karşılıyor ve asıl okuma hatası store katmanında bir kez uyarılıyor
                pass
    for entry in os.listdir(AGENT_SKILLS_DIR):
        dst = os.path.join(AGENT_SKILLS_DIR, entry)
        if not os.path.islink(dst):
            continue                                   # ajanın kendi dizinleri — dokunma
        try:
            target = os.path.realpath(dst)
        except OSError:  # sessiz-yutma: yardımcı G/Ç yolu; çağıran yokluğu zaten yedek değerle karşılıyor ve asıl okuma hatası store katmanında bir kez uyarılıyor
            continue
        if target.startswith(os.path.realpath(repo)) and entry not in enabled:
            try:
                os.unlink(dst); pruned.append(entry)
            except OSError:  # sessiz-yutma: yardımcı/telemetri yolu; başarısızlığı karara girmez ve çağıran yedek değerle aynen devam eder
                pass
    out = {"enabled": len(enabled), "linked": linked, "pruned": pruned}
    if linked or pruned:
        obs.log("agent_skills_synced", enabled=len(enabled), linked=len(linked), pruned=pruned[:10])
    return out


def agent_skill_coverage() -> dict:
    """Panel için: enabled set ↔ ajan linkleri kapsamı (eksik/bayat görünür olsun)."""
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
        a = attr.get(n) or {}
        if (a.get("n") or 0) >= 5 and a.get("avg_r") is not None:
            return float(a["avg_r"])
        if (a.get("n_cf") or 0) >= 10 and a.get("cf_avg_r") is not None:
            return 0.5 * float(a["cf_avg_r"])
        return 0.0
    def _bad(n):
        a = attr.get(n) or {}
        return n not in CORE and (a.get("n") or 0) >= 10 and (a.get("avg_r") or 0) <= -0.15
    out = [n for n in out if not _bad(n)]
    # ÇEKİRDEK KIRPMAYA DA DAYANIR (2026-07-22): eskiden CORE yalnız _bad() elemesinden korunuyordu,
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


def review_candidates(dstr: str | None = None) -> dict | None:
    """ADAY DANIŞMA KATMANI — yerel ajan (skill kütüphanesiyle) bugünün adaylarına İKİNCİ GÖRÜŞ verir.
    YETKİ SINIRI: bu inceleme yalnız bilgilendirir; kapı kararlarını (GO/REVIEW/NO_GO), silahlanmayı
    veya emirleri ASLA değiştirmez — 'aday seçimi LLM'e' isteği bilinçli olarak danışman olarak bağlandı,
    çünkü seçim otoritesini LLM'e vermek deterministik kapı yasasını delerdi. İlgili Meridian skill'leri
    oturuma önceden yüklenir (-s); sonuç state/candidate_review.json'a atomik yazılır, Adaylar sayfası
    gösterir. Yerel ajan yoksa/hata verirse sessizce None (döngüye asla dokunmaz)."""
    import subprocess
    bin_ = _hermes_bin()
    if not bin_:
        return None
    plans = store.read_jsonl("trade_plans.jsonl")
    day = dstr or max([p.get("date") for p in plans if p.get("date")], default=None)
    todays = [p for p in plans if p.get("date") == day]
    if not todays:
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
    text = _agent_call(prompt, preload=tuple(_skill_preload("review", _setups)),
                       kind="review", timeout=300, max_wait=90.0)   # asenkron iş parçacığı bekleyebilir
    if text is None:
        return None
    raw = _extract_json(text)
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:  # sessiz-yutma: yardımcı G/Ç yolu; çağıran yokluğu zaten yedek değerle karşılıyor ve asıl okuma hatası store katmanında bir kez uyarılıyor
        data = json.loads(_unwrap_strings(raw))
    reviews = [r for r in (data.get("reviews") or [])
               if isinstance(r, dict) and r.get("ticker")
               and r.get("opinion") in ("destekle", "çekimser", "karşı")]
    if not reviews:
        return None
    res = {"date": day, "model": active_model(), "brain": active_brain(),
           "reviews": reviews[:20], "ts": memory.now_iso(),
           "note": "danışma katmanı — kapı kararını değiştirmez"}
    store.write_json("candidate_review.json", res)
    obs.log("candidate_review", date=day, n=len(reviews), brain=active_brain())
    try:
        _stamp_llm_opinions(day, reviews)      # Kademe-1: görüşler plan satırlarına GERİ-damgalanır
    except Exception as e:
        obs.warn("llm_stamp_failed", error=f"{type(e).__name__}: {e}")
    return res


def _opinion_history(k: int = 5) -> str:
    """v10 #4 — ajanın KENDİ karnesi: son k gerçek görüş-sonuç çifti, prompt'a somut ders olarak.
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


def _stamp_llm_opinions(day: str, reviews: list) -> None:
    """Kademe-1 (LLM danışman katmanı): inceleme P3'ten DAKİKALAR SONRA asenkron iner — bu yüzden görüş
    plan satırlarına geriye dönük damgalanır (alpaca_fill_price backfill kalıbı). İki yere yazılır:
    trade_plans.jsonl (kalibrasyon defterinin join'i + panel çipleri) ve portfolio.json'daki silahlı
    planlar (P4 dolum-anı vetosu — YALNIZ terfiden sonra — oradan okur). Yetki yok: damga bilgidir."""
    op_by_ticker = {str(r.get("ticker")): r.get("opinion") for r in reviews if r.get("ticker")}
    if not op_by_ticker:
        return
    # KİLİTLİ oku-değiştir-yaz (2026-07-21): bu damga, zamanlayıcı iş parçacığının AYNI dosyaya
    # yazdığı anlarda araya giriyordu; kilitsiz hâlde döngünün planlarını bayat kopyayla ezebilirdi.
    counters = {"plans": 0}

    def _patch_plans(plans):
        n = 0
        for pl in plans:
            if pl.get("date") == day and pl.get("ticker") in op_by_ticker and "llm_opinion" not in pl:
                pl["llm_opinion"] = op_by_ticker[pl["ticker"]]
                n += 1
        counters["plans"] = n
        return n > 0

    store.update_jsonl("trade_plans.jsonl", _patch_plans)
    patched = counters["plans"]
    def _patch_cf(rows):                                 # #4: cf defteri de damgalanır — görüş↔sonuç
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
        if not pf or not pf.get("armed"):
            return False
        changed = False
        for pl in pf["armed"]:
            if pl.get("date") == day and pl.get("ticker") in op_by_ticker and "llm_opinion" not in pl:
                pl["llm_opinion"] = op_by_ticker[pl["ticker"]]
                changed = True
        return changed

    store.update_json("portfolio.json", _patch_pf, None)
    obs.log("llm_opinions_stamped", date=day, n=patched)


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
    """ÇEVRİMDIŞI GÖRÜŞ DOLGUSU (Hermes batch özelliğinden esinli, kanıt debisi turu 2026-07-20).
    Kalibrasyon aylar yerine GÜNLERDE anlamlılığa ulaşsın diye: SONUCU ZATEN BİLİNEN ama LLM görüşü
    OLMAYAN geçmiş planları yerel ajana KARAR-ANI bilgisiyle (sonuç gizli) toplu inceletir ve görüşü
    trade_plans + cf defterine geriye damgalar. Look-ahead YOK → öngörü geçerliliği korunur; terfiyi
    sahte tetiklemez. Rate bütçesine saygılı: gün başına 1 çağrı, max_days tavanı, bütçe kuruyunca durur.
    OTOMATİK KADANS (2026-07-30): `max_days=None` → tavan `backfill_budget()`ten TÜRETİLİR (kalan
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
        if not reviews:                       # bütçe kurudu / cevapsız → dur (kalanı sonraki turda)
            if not _agent_budget_take(0.0):
                break
            continue
        _stamp_llm_opinions(day, reviews)
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
    join etmek ZORUNDADIR. 2026-07-22'de bulundu: daemon thread, süreç çıkışında öldürülüyordu, yani
    tek-atışlık her koşuda ikinci görüş SESSİZCE kayboluyordu. Üstelik telafisi de yoktu — zamanlayıcı
    o seansı "zaten işlendi" görüp bir daha tetiklemediği için o gün SONSUZA KADAR görüşsüz kalıyordu.
    Hiçbir istisna fırlamadı; panoda yalnız bir hafta önceki görüş duruyordu.
    """
    import threading

    def _bg():
        try:
            review_candidates(dstr)
        except Exception as e:
            obs.warn("candidate_review_failed", error=f"{type(e).__name__}: {e}")
    t = threading.Thread(target=_bg, name="candidate-review", daemon=True)
    t.start()
    return t


def review_backlog(max_sessions: int = 1) -> dict:
    """TELAFİ: planı olan ama görüşü OLMAYAN en son seans(lar)ı incele.

    Tek bir kaçırılmış pencere, o seansı kalıcı olarak görüşsüz bırakıyordu (döngü aynı seansı ikinci
    kez işlemez). Danışma katmanının kanıt üretmesi buna bağlı: LLM görüş↔sonuç kalibrasyonu ancak
    kapanan planların görüşü varsa birikir."""
    plans = store.read_jsonl("trade_plans.jsonl")
    if not plans:
        return {"reviewed": [], "detail": "plan yok"}
    have = str((store.read_json("candidate_review.json", {}) or {}).get("date") or "")
    dates = sorted({str(p.get("date")) for p in plans if p.get("date")}, reverse=True)
    todo = [d for d in dates[:max_sessions] if d != have]
    done = []
    for d in todo:
        r = review_candidates(d)
        if r:
            done.append(d)
    obs.log("candidate_review_backlog", requested=todo, reviewed=done, already=have)
    return {"reviewed": done, "requested": todo, "already": have}


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


def chain_text(prompt: str, *, kind: str, preload: tuple = (), timeout: int = 300,
               max_wait: float = 0.0, note: str | None = None) -> dict:
    """BEYİN ZİNCİRİNİN GENEL METİN YOLU — `propose_with_llm` ile AYNI disiplin, farklı GÖREV.

    NEDEN VAR (nous sistem-değerlendirme katmanı, ROADMAP §3.2): Katman B beyni bir hipotez üretmek
    için değil, MEKANİZMALARI DEĞERLENDİRMEK için çağırır. `propose_with_llm` hipoteze özeldir
    (`_parse_hyp`, `hyp["source"]`, tek-değişken sözleşmesi) ve o yolu genel amaçlı hâle getirmek
    hipotez yolunu kırılgan yapardı. Bu fonksiyon zincirin YALNIZ taşıma katmanını paylaşır:
    sıra (`brain_order`), hazır-olma, 429 soğuması, bütçe kapısı, boş-cevap sınıflandırması.

    SYSTEM'E DOKUNULMAZ. Görev metni, telemetri ve şema sözleşmesi TAMAMEN `prompt` içinden girer —
    yani user-prompt yolundan. SYSTEM statik bir sabittir (AST testiyle çivili) ve içine görev metni
    sızdığı gün `cache_control` her turda ıskalar; maliyet sessizce katlanır.

    DÖNÜŞ: {"text", "beyin", "model", "neden": {sağlayıcı: sebep}} — `text=None` ise `neden`
    zincirin HER ayağının niçin cevap vermediğini taşır. "Çağrı yapılamadı" ile "cevap boş geldi"
    ayrı sınıflardır (`_NOT_A_RESPONSE`) ve tek satıra katlanmazlar."""
    from . import spend
    out: dict = {"text": None, "beyin": None, "model": None, "neden": {}}
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
        try:
            if p == "claude":
                txt = _claude_text(prompt, note=note or kind, max_tokens=8000)
            elif p == "nous":
                # YEREL ajan varsa O kullanılır (skill kütüphanesi + MCP araçları onun yolunda).
                txt = (_agent_call(prompt, preload=preload, kind=kind, timeout=timeout,
                                   max_wait=max_wait) if _nous_local()
                       else _nous_text(prompt, note=note or kind))
            else:
                txt = _gemini_call(prompt, note=note or kind)
        except Exception as e:
            limited, retry_after = _rate_limited(e)
            cooled = brain_stand_down(p, "rate_limit" if limited else "error", retry_after) if limited else 0.0
            obs.warn("nous_chain_failed", provider=p, kind=kind, error=f"{type(e).__name__}: {e}",
                     rate_limited=limited, cooldown_s=round(cooled, 1))
            out["neden"][p] = "failed"
            continue
        if txt and str(txt).strip():
            brain_recovered(p)
            out.update({"text": txt, "beyin": p, "model": active_model()})
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

    ESKİ HÂL (2026-07-30 öncesi): beyin zinciri boş dönünce `reflect_once` TEK bir akıllı hamle
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


def reflect_once(target_regime: str | None = "auto") -> dict:
    """One live reflection. A single smart move (Claude, if a key is set) is tried first; if it doesn't
    clear the gate — or there's no key — we fall through to the systematic COORDINATE-DESCENT SEARCH across
    all knobs on the PRODUCTION windows. That is the escape from the ±1 trap that lets the live strategy
    actually evolve. submit() (inside both paths) remains the SOLE ship authority — the gate is unchanged.
    target_regime: the regime the CALLER's horizon guardrail certified ("auto" → read regime.json now).
    The standby loop passes its certified regime so a regime flip between the horizon check and the search
    (the walk takes minutes) can't retarget the ship into an uncertified regime."""
    SEARCH_PROGRESS.clear()
    proposal = propose_with_llm()
    if proposal is None and VIRGIN_FALLBACK:
        # BEYİNSİZ TUR ARTIK BOŞ GEÇMİYOR: tek akıllı hamle yuvası bakir bir düğmeyle doldurulur.
        # Öneri üretilemezse (bakir kalmadı / hepsi guard'a takıldı) davranış BİREBİR eski hâl —
        # doğrudan koordinat-inişi aramasına düşülür.
        proposal = propose_virgin_knob()
    if proposal is not None:
        # A Claude var@regime proposal must target the CERTIFIED regime (or be global): the horizon
        # guardrail certified evidence for ONE regime — shipping an override into a different, never-
        # certified regime through this side door would bypass the whole guardrail (audit #27).
        pvar = str(proposal.get("variable") or "")
        preg = pvar.split("@", 1)[1] if "@" in pvar else None
        certified = None if target_regime == "auto" else target_regime
        if preg is not None and certified is not None and preg != certified:
            obs.warn("hermes_proposal_uncertified_regime", variable=pvar, certified=certified)
            proposal = None                     # fall through to the (certified-regime) search
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
    live_reg = store.read_json("regime.json", {}).get("regime") if target_regime == "auto" else target_regime
    search_regime = live_reg if live_reg in config.VALID_REGIMES and live_reg != "trend_up" else None
    # TAVAN ARTIK TÜRETİLİR (bütçe öz-ayarı, 2026-07-30): `SEARCH_BUDGET` sabiti TABAN olarak durur
    # (env override yolu birebir aynı); `search_budget()` kota durumuna göre onu açar. Türetimin
    # KENDİSİ olaya yazılır — "bugün neden 20 sonda koştu?" sorusu defterden cevaplanabilsin.
    _sb = search_budget()
    obs.log("hermes_search_start", budget=_sb["tavan"], k_max=SEARCH_KMAX, windows="production",
            regime=search_regime or "global", butce_kaynagi=_sb["kaynak"], butce_formulu=_sb["formul"])
    # The incumbent walk-forward runs BEFORE any probe and takes ~90s. Without naming that phase the UI sits
    # on a bare "başlıyor…" for a minute and a half — indistinguishable from a hang (exactly how this whole
    # observability bug was found). Name it, so a slow baseline never looks like a crash.
    SEARCH_PROGRESS.update(running=True, phase="incumbent", i=0, total=None)

    def _on_probe(i, total, var, new, cand_oos, inc_oos, passes, best):
        SEARCH_PROGRESS.update(running=True, phase="probing" if i else "planned", i=i, total=total,
                               variable=var, new=new,
                               candidate_oos=cand_oos, incumbent_oos=inc_oos, passes=passes, best=best)
        obs.log("hermes_search_probe", i=i, total=total, variable=var, new=new,
                candidate_oos=cand_oos, incumbent_oos=inc_oos, passes=passes)

    try:
        result = reflect.search_and_submit(bars, index, config.goal(), windows=None,
                                           budget=_sb["tavan"], k_max=SEARCH_KMAX, on_probe=_on_probe,
                                           regime=search_regime)
    except Exception:
        # never leave the dashboard showing a phantom in-flight search after a crash (audit #28)
        SEARCH_PROGRESS.update(running=False, phase="error")
        raise
    s = result.get("search", {})
    obs.log("hermes_search_done", evaluated=s.get("evaluated"), cleared=s.get("cleared"),
            status=result.get("status"), best=s.get("best"))
    SEARCH_PROGRESS.update(running=False, phase="done", status=result.get("status"),
                           evaluated=s.get("evaluated"), cleared=s.get("cleared"), best=s.get("best"))
    return result


def _closed_count() -> int:
    return len(store.read_jsonl("trades.jsonl"))


def loop(poll_seconds: int = 1800) -> None:
    """Standby loop: every 30 min read the heartbeat; reflect only when reflection_every new trades
    have closed and the system is healthy (not stale, not halted)."""
    goal = config.goal()
    every = int(goal["reflection_every"])
    from . import hermes_runtime as _hr
    last_reflect_at = _hr._restored_baseline()   # survive restarts — same fix as the in-process path (#25)
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
                    # persist so a tmux restart doesn't reset the 30-day horizon clock (#25)
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
