"""skills.py — the pipeline runner. Skills are bound into five DETERMINISTIC pipelines (§3), each
with a fixed trigger, fixed inputs, and a fixed output artifact — this is what makes the agent
auditable. Every run appends to pipeline_runs.jsonl; nothing the agent does is invisible.

At L0 the engine's deterministic core (regime.py, strategy.py) produces the pipeline artifacts.
The Claude skills are the brain's toolkit: LLM-driven skills are invoked by Hermes during
reflection/research; FMP-`req` skills enrich candidates once a key is present. Disabled skills are
recorded as skipped-with-reason, never faked.

2026-07-30 SKILL DENETİMİ: 68 klasörden 37'si `skills/_emekli/` altına ARŞİVLENDİ (22 emekli +
15 birleştirilen; silme yok, geri alınabilir) — geride 31 canlı SKILL.md kaldı. Arşivlenenlerin
kayıtları `retired: true` ile duruyor (kayıt silinmedi: dürüst envanter + geri dönüş yolu) ve
PIPELINES zincirlerinden çıkarıldı, çünkü zincirde durup her koşuda 'declared_not_run' yazılmak
"çalışıyor" izlenimi üretiyordu. Katalog taraması `_` ile başlayan dizinleri atlar."""
from __future__ import annotations
import datetime as dt
import re
import threading
from contextlib import contextmanager

from . import config, store

REGISTRY = "skills_registry.json"
# Kayıt defteri oku-değiştir-yaz ile güncelleniyor ve BUNU İKİ DAEMON İŞ PARÇACIĞI yapıyor
# (zamanlayıcı döngüsü pipeline_run içinde last_run damgalar, Hermes/pano gölge bayrağı yazar).
# memory.py'de aynı desen audit #19'da veri kaybına yol açmıştı: araya giren bir yazım, diğerinin
# değişikliğini yok eder — burada bir 'shadow' kararı ya da bir enable geri döner (denetim turu 30).
_REG_LOCK = threading.Lock()
RUNS = "pipeline_runs.jsonl"
SKILL_RECS = "skill_recommendations.jsonl"

# Safety/enforcement skills Hermes may NEVER shadow or disable — the constraint layer, not opinion.
PROTECTED = frozenset({"pre-trade-discipline-gate", "drawdown-circuit-breaker", "data-quality-checker",
                       "position-sizer", "portfolio-manager"})

# Which screener a plan's setup came from. Used to build skill_chain from the ACTUAL setup so per-skill
# attribution can differentiate screeners (the old hardcoded "vcp-screener*" — with a star — never
# key-matched the "vcp-screener" registry entry, so Axis-2 attribution stayed frozen for every trade).
_SCREENER_BY_SETUP = {"breakout_vcp": "vcp-screener", "pullback": "pullback-screener",
                      "episodic_pivot": "stockbee-episodic-pivot-analyzer",
                      "momentum_burst": "stockbee-momentum-burst-screener",
                      "exhaustion_hammer": "stockbee-exhaustion-hammer-screener",
                      "pead": "pead-screener",
                      "canslim": "canslim-screener"}


def screener_for(setup: str) -> str:
    return _SCREENER_BY_SETUP.get(setup, "vcp-screener")


# Skills whose logic the DETERMINISTIC engine actually EXECUTES natively (strategy.py / guard.py / broker.py /
# regime.py / health.py / earnings.py / data.py). Everything else in a pipeline is a SKILL.md folder authored
# for a Claude-agent context — enabled/available, but the deterministic engine does not run it. pipeline_run
# reports only these as truly "invoked" so the log can't claim a screener ran when only its label was present
# (e.g. canslim/pead/finviz were logged as invoked while only vcp+pullback actually scanned).
ENGINE_IMPLEMENTED = {
    "vcp-screener", "pullback-screener", "stockbee-momentum-burst-screener", "data-quality-checker",  # P2
    "stockbee-episodic-pivot-analyzer",
    # 2026-07-24: iki declared-only screener artık motor-uygulandı → scan_all'da HER ticker'da koşar,
    # karşı-olgusal defterde per-skill avg_r ölçülür (öğrenme artık kör değil). O gün ikisi de
    # ARMED_SETUPS dışıydı (canlı deftere sıfır risk); 2026-08-11 operatör onayıyla exhaustion_hammer
    # SİLAHLANDI (strategy.ARMED_SETUPS — gerekçe orada), pead DORMANT kalır. exhaustion-hammer KEYLESS
    # (anında ölçer); pead FMP-kapılı ama earnings.csv anahtarsız Nasdaq'tan dolduğu için ölçer
    # (veri yoksa dürüstçe None).
    "stockbee-exhaustion-hammer-screener", "pead-screener",
    # NOT eklendi: "canslim-screener" — evaluate_canslim scan_all'da güvenli no-op olarak KOŞAR ama
    # `earnings.canslim_fundamentals` + FMP nokta-zamanlı temel önbelleği (Faz C) inşa edilene kadar DAİMA
    # None döner. ENGINE_IMPLEMENTED'a erken eklemek pipeline_run'ı "invoked" yalanına sürükler (skills.py'nin
    # tam olarak önlediği dürüstlük ihlali) — helper landıktan SONRA eklenecek; o zamana dek declared-only.
    # 2026-07-23: artık gerçekten koşuyor — adapters/finviz.discover EVRENİ genişletir (REPLAY_UNIVERSE'e
    # bugünün momentum/kırılım listesini katar), dataset.load_live canlı döngüde çağırır. Karar yine
    # Meridian'ın vcp/pullback/momentum yasasının; Finviz yalnız "hangi hisselere bakılsın" evreni.
    "finviz-screener",
    "position-sizer", "pre-trade-discipline-gate", "earnings-calendar",                               # P3
    "drawdown-circuit-breaker", "portfolio-manager",                                                  # P4
}

_DESC_CACHE: dict | None = None

# Pipeline -> ordered skill chain (from §3). Presence here does not mean enabled — the registry decides.
PIPELINES = {
    # 2026-07-30 denetimi: arşivlenen skill'ler zincirlerden çıkarıldı (P1'de breadth-chart-analyst,
    # ftd-detector, us-market-bubble-detector, downtrend-duration-analyzer, sector-analyst; P3'te
    # breakout-trade-planner, scenario-analyzer, options-strategy-advisor; P5'te signal-postmortem,
    # news-reaction-failure-analyzer, trader-memory-core, trade-performance-coach,
    # stockbee-setup-fluency-trainer). Klasörleri skills/_emekli/ altında duruyor; geri getirilirse
    # adları buraya yeniden eklenir.
    "P1_REGIME": ["market-environment-analysis", "market-breadth-analyzer", "macro-regime-detector",
                  "ibd-distribution-day-monitor", "market-top-detector", "uptrend-analyzer",
                  "exposure-coach"],
    "P2_SCREEN": ["data-quality-checker", "vcp-screener", "pullback-screener", "canslim-screener",
                  "stockbee-momentum-burst-screener", "stockbee-episodic-pivot-analyzer",
                  "stockbee-exhaustion-hammer-screener", "pead-screener", "finviz-screener",
                  "theme-detector"],
    "P3_PLAN": ["position-sizer", "earnings-calendar", "economic-calendar-fetcher",
                "pre-trade-discipline-gate"],
    "P4_EXECUTE": ["drawdown-circuit-breaker", "portfolio-manager"],
    "P5_LEARN": ["weekly-performance-digest", "edge-pipeline-orchestrator", "backtest-expert",
                 "strategy-pivot-designer"],
}


def registry() -> dict:
    return store.read_json(REGISTRY, {"skills": {}})


def enabled_in(pipeline: str) -> tuple[list[str], list[str]]:
    """Return (enabled, disabled) skill names for a pipeline, per the registry."""
    reg = registry().get("skills", {})
    en, dis = [], []
    for s in PIPELINES.get(pipeline, []):
        info = reg.get(s, {})
        (en if info.get("enabled") else dis).append(s)
    return en, dis


def reconcile_enablement() -> dict:
    """Flip KEY-GATED skills on/off to match current key availability — this is the 'auto-enable when the
    key lands' the registry reason promises. A skill that requires FMP/Alpaca (fmp=='req' / alpaca=='req')
    is enabled iff its style is active AND every required provider's key is present. Skills that need no
    key are left exactly as the registry has them, so agent/human decisions are never clobbered. Writes
    only when something actually changes. Call after a key is set/removed and on each skills read."""
    from .adapters import fmp, alpaca
    reg = registry()
    skills = reg.get("skills", {})
    fmp_ok, alp_ok = fmp.available(), alpaca.paper_available()
    changed = []
    for name, info in skills.items():
        if info.get("retired"):
            # 2026-07-30 denetimi: arşivlenmiş (emekli/birleştirilmiş) kayıt. Anahtar gelse bile
            # DİRİLTİLMEZ — klasörü skills/_emekli/ altında, zincirde üyeliği yok. Anahtar-kapısı
            # bu kararı ezerse denetimin gerekçesi de silinir (fmp='req' + anahtar mevcut olan iki
            # kayıt tam bunu yapıyordu). Geri dönüş yolu: 'retired' alanını kaldır + klasörü taşı.
            continue
        needs_fmp, needs_alp = info.get("fmp") == "req", info.get("alpaca") == "req"
        if not (needs_fmp or needs_alp):
            continue                                   # not key-gated — leave untouched
        if name in PROTECTED or name in ENGINE_IMPLEMENTED:
            # NEVER key-disable these: PROTECTED skills are the safety layer ('may never be shadowed or
            # disabled' — broker.py keeps enforcing them regardless of any key), and ENGINE_IMPLEMENTED
            # screeners run natively on keyless data. Registry metadata marking them fmp/alpaca 'req'
            # describes an ENHANCEMENT, not a dependency (audit #36: deleting the Alpaca key disabled
            # the PROTECTED portfolio-manager).
            continue
        if info.get("shadow"):
            continue                                   # an operator/Axis-2 shadow decision outranks key-gating (audit #38)
        required_ok = (not needs_fmp or fmp_ok) and (not needs_alp or alp_ok)
        style_ok = bool(info.get("style_active", True))
        want = style_ok and required_ok
        if want:
            reason = "enabled"
        elif not style_ok:
            reason = "bu stile uygun değil (kapalı)"   # off for STYLE, not a missing key
        else:
            missing = (["FMP_API_KEY"] if needs_fmp and not fmp_ok else []) + \
                      (["ALPACA_PAPER_KEY"] if needs_alp and not alp_ok else [])
            reason = f"{' + '.join(missing)} yok — Ayarlar'dan ekleyin"
        if want == bool(info.get("enabled")) and reason == info.get("reason"):
            continue                                   # nothing to change (state AND reason already correct)
        info["enabled"] = want
        info["mode"] = "active" if want else "disabled"
        info["reason"] = reason
        changed.append(name)
    if changed:
        store.write_json(REGISTRY, reg)
    return {"changed": changed, "fmp_ok": fmp_ok, "alpaca_ok": alp_ok}


def _skill_descriptions() -> dict:
    """One-line purpose of each skill, parsed once from skills/<name>/SKILL.md YAML frontmatter."""
    global _DESC_CACHE
    if _DESC_CACHE is not None:
        return _DESC_CACHE
    out: dict[str, str] = {}
    base = config.SKILLS
    if base.exists():
        for d in sorted(base.iterdir()):
            if d.name.startswith("_"):
                continue        # skills/_emekli/ arşivi (2026-07-30 denetimi) katalogda görünmez:
                                # arşiv bir skill değil, geri-alınabilir bir depo. Alt klasörleri de
                                # taranmaz, çünkü tarama tek seviyedir.
            f = d / "SKILL.md"
            if not f.exists():
                continue
            try:
                text = f.read_text(errors="ignore")[:4000]
            except Exception:  # sessiz-yutma: yardımcı G/Ç yolu; çağıran yokluğu zaten yedek değerle karşılıyor ve asıl okuma hatası store katmanında bir kez uyarılıyor
                continue
            m = re.search(r"(?ms)^description:\s*(.+?)\s*(?:\n\w[\w-]*:|\n---)", text)
            desc = (m.group(1) if m else "").replace("\n", " ").strip()
            out[d.name] = re.split(r"(?<=[.!?])\s", desc)[0][:220] if desc else ""
    _DESC_CACHE = out
    return out


# ==================================================================================================
# YAŞAM DÖNGÜSÜ — TEK YER (Ç3 kökü, 2026-08-09)
# ==================================================================================================
# ÖLÇÜLMÜŞ KUSUR. Kayıt defteri `retired: true` alanını 2026-07-30 denetiminden beri TAŞIYOR (36
# kayıt) ama `catalog()` o alanı ÇIKTIYA GEÇİRMİYORDU. Katalog 67 satırı DÜZ döküyordu; yani
# katalogtan beslenen HER tüketici (Eksen-2 teşhisi, pano özeti, hermes brifingi) arşivi canlı skill
# sanıyordu. Sayı doğruydu, ETİKET yanlıştı — "gercek_katman_olculmemis 57" satırının 36'sı fiilen
# ARŞİVDİ ve arşivin ölçülmemiş olması bir körlük değil, TANIMDIR.
#
# ALAN GEÇİRİLİR VE AYRIM TEK YERDEN OKUNUR. İki kova adı burada sabittir ve her tüketici bu iki
# yardımcıdan geçer; `info.get("retired")` sınamasını her çağıranın kendi başına yazması, aynı
# ayrımın altı ayrı yerde altı farklı biçimde bozulması demekti (`_SCREENER_BY_SETUP` yıldızı
# vakasının aynısı).
AKTIF, ARSIV = "aktif", "arsiv"


def yasam_dongusu(info: dict | None) -> str:
    """Kayıt satırının yaşam döngüsü kovası: `arsiv` (emekli/birleştirilmiş) ya da `aktif`.

    Kayıtta OLMAYAN bir ad `aktif` sayılır ve bu bilinçlidir: klasörü `skills/` altında duran ama
    deftere hiç girmemiş bir skill, ARŞİVLENMİŞ değildir — kayıt eksiğidir ve `envanter()` onu
    `kayitsiz_klasor` diye ADIYLA raporlar."""
    return ARSIV if (info or {}).get("retired") else AKTIF


def aktif_katalog(cat: list[dict] | None = None) -> list[dict]:
    """Katalogun YALNIZ aktif kesiti — karar/öneri üreten her kol buradan okur.

    Arşiv kayıtları `enabled=False` olduğu için bugünkü kollar onları zaten eliyordu; ama ELEME
    ile TANIM AYRI şeylerdir. Arşiv "aday olup elenen" değil "aday hiç olmayan"dır ve bu ayrım
    kovaların adına yansımadıkça sayım doğru, etiket yanlış kalır."""
    return [c for c in (catalog() if cat is None else cat) if c.get("yasam_dongusu") != ARSIV]


def envanter() -> dict:
    """KLASÖR ↔ KAYIT ENVANTERİ — "kaç skill var?" sorusunun tek ölçülmüş cevabı.

    NEDEN VAR. Aynı kütüphane üç ayrı sayıyla anılıyordu (38 / 37 / 36) ve üçü de farklı bir şeyi
    sayıyordu: `ls skills/_emekli` DOSYA sayardı (README.md dâhil → 38), dizin sayımı GİT-İZSİZ boş
    bir mezar taşını (`skills/_emekli/shadow`) da sayınca 37 veriyordu, kayıt defteri ise gerçek arşiv
    KAYITLARINI (36). O mezar taşı v121'de HAYALET sınıfına alınıp DİZİNİ kaldırıldı — çünkü aşağıdaki
    `fark` kovaları onu ADIYLA yakaladı (`arsiv_dizin_ama_kayitsiz` + `arsiv_dizin_skill_md_yok`; ölçüm
    docs/CIFT-KAYNAK-TARAMASI-2026-08-09.md §245). BUGÜN dizin = SKILL.md = kayıt = 36 ve `ls`in fazlası
    yalnız README.md'dir (`arsiv_disi_girdi` kovası) — yani üçlü ayrışma kapandı, ama üç payda hâlâ AYRI
    ölçülür ki mezar taşı geri belirirse `fark` onu yine ADIYLA döksün. Sayılar çelişmiyordu; PAYDALARI
    farklıydı ve hiçbiri yazılı değildi. Bu fonksiyon üç paydayı da ölçer ve farkı ADIYLA döker — bir
    daha tahminle tartışılmasın diye.

    SAF OKUMA: hiçbir şeye yazmaz, hiçbir kaydı düzeltmez."""
    reg = registry().get("skills", {})
    kayit_aktif = sorted(k for k, v in reg.items() if yasam_dongusu(v) == AKTIF)
    kayit_arsiv = sorted(k for k, v in reg.items() if yasam_dongusu(v) == ARSIV)
    base = config.SKILLS
    ars = base / "_emekli"
    def _dizinler(p):
        return sorted(d.name for d in p.iterdir() if d.is_dir()) if p.exists() else []
    def _skillli(p):
        return sorted(d.name for d in p.iterdir() if d.is_dir() and (d / "SKILL.md").exists()) \
            if p.exists() else []
    klasor_aktif = [a for a in _skillli(base) if not a.startswith("_")]
    klasor_aktif_dizin = [a for a in _dizinler(base) if not a.startswith("_")]
    arsiv_dizin, arsiv_skillli = _dizinler(ars), _skillli(ars)
    girdi_sayisi = len(list(ars.iterdir())) if ars.exists() else 0
    return {
        "kayit": {"toplam": len(reg), "aktif": len(kayit_aktif), "arsiv": len(kayit_arsiv)},
        "klasor": {"aktif_dizin": len(klasor_aktif_dizin), "aktif_skill_md": len(klasor_aktif),
                   "arsiv_girdi": girdi_sayisi, "arsiv_dizin": len(arsiv_dizin),
                   "arsiv_skill_md": len(arsiv_skillli)},
        "fark": {
            # Her sapma ADIYLA çıkar: bir sayı diğerinden büyükse SEBEBİ okunabilsin.
            "arsiv_dizin_ama_kayitsiz": sorted(set(arsiv_dizin) - set(kayit_arsiv)),
            "kayitli_arsiv_ama_dizinsiz": sorted(set(kayit_arsiv) - set(arsiv_dizin)),
            "arsiv_dizin_skill_md_yok": sorted(set(arsiv_dizin) - set(arsiv_skillli)),
            "kayitsiz_klasor": sorted(set(klasor_aktif) - set(reg)),
            "kayitli_aktif_klasorsuz": sorted(set(kayit_aktif) - set(klasor_aktif)),
            "arsiv_disi_girdi": max(0, girdi_sayisi - len(arsiv_dizin)),   # README.md gibi dosyalar
        },
        "hukum": ("DOĞRU ENVANTER = KAYIT DEFTERİ ∩ KLASÖR. Aktif küme kayıt ve klasörde AYNI "
                  "sayıdaysa sayı ölçülmüştür; ayrışıyorsa `fark` alanı hangi tarafın eksik "
                  "olduğunu söyler. `ls` çıktısı bir envanter DEĞİLDİR: dosya sayar."),
    }


def catalog() -> list[dict]:
    """The full skill library as Hermes should see it: name, one-line purpose (SKILL.md), category /
    mode / key-requirements (registry), and LIVE performance (attribution — n, win_rate, avg_r). This
    is the toolkit briefing the brain reasons with when it improves the system."""
    from . import analytics
    reg = registry().get("skills", {})
    descs = _skill_descriptions()
    attr = {s["skill"]: s for s in analytics.skill_attribution().get("skills", [])}
    names = sorted(set(list(reg.keys()) + list(descs.keys())))
    out = []
    for name in names:
        info, a = reg.get(name, {}), attr.get(name, {})
        out.append({
            "name": name, "description": descs.get(name, ""),
            "category": info.get("category"), "enabled": bool(info.get("enabled")),
            "mode": info.get("mode"), "shadow": bool(info.get("shadow")),
            "pipeline": info.get("pipeline"), "protected": name in PROTECTED,
            # YAŞAM DÖNGÜSÜ ARTIK ÇIKTIDA (Ç3, 2026-08-09). Kayıt defteri bunu BİLİYORDU ve katalog
            # düşürüyordu; düşen alan, arşivi canlı sanan bir teşhis kovası ve 67'lik bir pano
            # paydası üretti. İki alan birden taşınır: ham `retired` (kaynağın kendi dili) ve
            # `yasam_dongusu` (tüketicinin okuduğu kova adı) — ikisi TEK yardımcıdan türer.
            "retired": bool(info.get("retired")), "yasam_dongusu": yasam_dongusu(info),
            "requires": [k.upper() for k in ("fmp", "alpaca") if info.get(k) == "req"],
            "n": a.get("n", 0), "win_rate": a.get("win_rate"), "avg_r": a.get("avg_r"),
            # CF KATMANI DA TAŞINIR (H5, 2026-07-30). `skill_attribution` bu iki alanı ZATEN
            # üretiyordu ama katalog onları düşürüyordu — yani hermes'in gördüğü skill brifingi ve
            # H5'in kanıt eşiği, geniş örneklemli cf katmanını HİÇ göremiyordu. Gerçek katmanın n'i
            # çoğu skill için 0-4 arasında; karar yalnız oradan verilemez.
            "n_cf": a.get("n_cf", 0), "cf_avg_r": a.get("cf_avg_r"),
        })
    return out


# CF KOLUNUN ORANLARI (Rol 1 tasarım kararı, 2026-07-30 temizlik turu). Sabit DEĞİL, TÜREV:
# ikisi de `min_n`den türer, yani eşik tek yerde ayarlanınca kol da onunla birlikte kayar.
CF_REAL_FRACTION = 0.5    # cf-destekli kolun istediği ASGARİ gerçek örneklem = min_n'in yarısı
CF_SAMPLE_MULT = 5        # ve ASGARİ cf örneklemi = min_n'in 5 katı


def _cf_arm(s: dict, min_n: int) -> bool:
    """cf-destekli uygunluk kolu — "yeter mi?" sorusuna İKİNCİ bir evet yolu (hüküm değil).

    TASARIM KARARININ İKİ YARISI ve NEDENLERİ:
      (1) cf KANITI TEK BAŞINA ÖNERİ TETİKLEYEMEZ. Bu yüzden gerçek katman hâlâ ÖLÇÜLMÜŞ olmalı
          (`avg_r is not None`) ve hâlâ `min_n`in YARISINA ulaşmalı. Karşı-olgusal defterin
          sadakati ölçülmüş ve SINIRLI (`analytics.cf_fidelity` — korelasyon + sapma raporlanır);
          sadakati sınırlı bir defterin tek başına bir skill'i gölgeye atması, ölçülmemiş bir
          kısıtı canlı stratejiye uygulamak olurdu.
      (2) AMA GÖRMEZDEN DE GELİNEMEZ. `axis2_diagnosis`ın canlı ölçümü (2026-07-30) yapısal körlüğü
          sayıyla gösterdi: stockbee-momentum-burst n=0 / n_cf=1080, vcp-screener n=91 / n_cf=1004.
          En büyük örneklemli kanıt, YALNIZ gerçek katmana bakan bir eşiğin gözünde YOKTU.
    HÜKÜM YİNE GERÇEK KATMANDAN: aşağıdaki yön karşılaştırmaları (`avg_r <= -0.15` / `>= 0.30`)
    DEĞİŞMEDİ ve `cf_avg_r`ye BAKMAZ. Bu kol yalnız "örneklem yeterli mi" kapısını açar — cf'nin
    yaptığı tek şey, yarı örneklemli bir gerçek ölçümün masaya oturmasına izin vermektir."""
    n, n_cf = (s.get("n") or 0), (s.get("n_cf") or 0)
    return n >= (min_n * CF_REAL_FRACTION) and n_cf >= (min_n * CF_SAMPLE_MULT)


def recommend_from_attribution(min_n: int = 8) -> list[dict]:
    """Deterministic Axis-2 signal (no LLM): from per-skill attribution, flag skills to SHADOW (chronic
    negative avg_r over >= min_n trades, not protected, currently enabled) and skills to LEAN ON (strong
    positive avg_r). Advisory — surfaced for the operator; not auto-applied.

    ÖRNEKLEM KAPISI İKİ KOLLUDUR (2026-07-30): gerçek katman `n >= min_n` VEYA cf-destekli kol
    (`_cf_arm`). cf-destekli bir öneri `kanit: "gercek+cf"` taşır ve rationale'inde cf payını
    AÇIKÇA yazar — kanıt türü şeffaf olmadan operatör iki farklı sertlikteki iddiayı aynı sanardı."""
    recs = []
    for s in aktif_katalog():          # ARŞİV ADAY DEĞİL (Ç3): `enabled=False` zaten eliyordu ama
                                       # eleme ile TANIM ayrı şeydir — arşiv aday HİÇ olmaz
        if s["protected"] or s["avg_r"] is None:
            continue
        gercek_kol = (s["n"] or 0) >= min_n
        cf_kol = (not gercek_kol) and _cf_arm(s, min_n)
        if not (gercek_kol or cf_kol):
            continue
        # KANIT KÜNYESİ: cf-destekli satır, gerçek-katman satırıyla AYNI güçte okunamaz.
        kanit = "gercek" if gercek_kol else "gercek+cf"
        cf_not = ("" if gercek_kol else
                  f" · cf payı: gerçek n={s['n']} (eşiğin yarısı {min_n * CF_REAL_FRACTION:g}), "
                  f"cf n={s.get('n_cf')} (eşiğin {CF_SAMPLE_MULT}×'i {min_n * CF_SAMPLE_MULT}), "
                  f"cf ort {s.get('cf_avg_r')}R — HÜKÜM gerçek katmandan, cf yalnız örneklem kolu")
        ortak = {"skill": s["name"], "avg_r": s["avg_r"], "n": s["n"],
                 "n_cf": s.get("n_cf") or 0, "cf_avg_r": s.get("cf_avg_r"), "kanit": kanit}
        if s["avg_r"] <= -0.15 and s["enabled"] and not s["shadow"]:
            recs.append({**ortak, "action": "shadow",
                         "rationale": f"{s['n']} işlemde ort. {s['avg_r']}R — sürekli zarar; "
                                      f"gölgeye alınmalı{cf_not}"})
        elif s["avg_r"] >= 0.30:
            recs.append({**ortak, "action": "lean_in",
                         "rationale": f"{s['n']} işlemde ort. +{s['avg_r']}R — güçlü katkı{cf_not}"})
    recs.sort(key=lambda r: (r["action"] != "shadow", r["avg_r"]))
    return recs


def record_recommendation(rec: dict, source: str = "hermes") -> bool:
    """Log an Axis-2 skill recommendation as PENDING (operator applies it). Dedups: skips if an identical
    un-applied recommendation for the same skill already exists. Refuses protected/unknown skills."""
    skill, action = rec.get("skill"), rec.get("action")
    if not skill or skill in PROTECTED or action not in ("shadow", "activate", "lean_in"):
        return False
    if skill not in registry().get("skills", {}):
        return False
    pending_ts = applied_ts = ""
    for r in store.read_jsonl(SKILL_RECS):
        if r.get("skill") == skill and r.get("action") == action:
            if r.get("pending") and not r.get("applied"):
                pending_ts = max(pending_ts, str(r.get("ts", "")))
            if r.get("applied"):
                applied_ts = max(applied_ts, str(r.get("ts", "")))
    if pending_ts and pending_ts > applied_ts:
        return False   # a genuinely OPEN pending rec exists — no duplicate. An old pending row that a
                       # LATER applied row superseded must NOT block forever (audit #37: after one
                       # apply cycle the same skill+action could never be recommended again).
    store.append_jsonl(SKILL_RECS, {
        "ts": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), "skill": skill,
        "action": action, "rationale": rec.get("rationale", ""), "source": source,
        "pending": True, "applied": False})
    return True


def pending_recommendations() -> list[dict]:
    """Un-applied recommendations, newest-first, deduped by skill. An APPLIED marker shadows any OLDER
    pending row for the same skill (M3): apply_skill_action APPENDS a {applied:True} row rather than
    flipping the original {pending:True} one, so without this the apply button and the (N) badge never
    cleared and every re-click appended another row (unbounded growth)."""
    seen, out = set(), []
    for r in reversed(store.read_jsonl(SKILL_RECS)):   # newest-first
        sk = r.get("skill")
        if sk in seen:
            continue
        if r.get("applied"):        # handled — shadow any older pending row for this skill
            seen.add(sk)
            continue
        if r.get("pending"):
            seen.add(sk); out.append(r)
    return out


def apply_skill_action(skill: str, action: str) -> dict:
    """Apply a REVERSIBLE Axis-2 skill action. Refuses protected skills and unknown names. 'shadow' keeps
    the skill running but marks it under-review (does not touch the deterministic live engine, which never
    executes LLM skills); 'activate' clears shadow. Logged; fully reversible."""
    if action not in ("shadow", "activate"):
        return {"ok": False, "reason": f"unknown action '{action}'"}
    if skill in PROTECTED:
        return {"ok": False, "reason": f"'{skill}' korumalı — gölgelenemez/kapatılamaz"}
    # kilit: OKUMA+YAZMA aynı kilit altında olmalı — aynı anda koşan pipeline damgası bu kararı
    # ezmesin (memory.py'deki audit #19 kayıp-güncelleme deseninin aynısı; turu 30)
    with _REG_LOCK:
        reg = registry()
        info = reg.get("skills", {}).get(skill)
        if info is None:
            return {"ok": False, "reason": f"'{skill}' kayıtlı değil"}
        info["shadow"] = (action == "shadow")
        if action == "shadow":
            info["mode"] = "shadow"; info["reason"] = "gölge (Axis-2 incelemesi)"
        else:
            info["mode"] = "active" if info.get("enabled") else info.get("mode", "disabled")
            info["reason"] = "enabled" if info.get("enabled") else info.get("reason", "")
        store.write_json(REGISTRY, reg)
    store.append_jsonl(SKILL_RECS, {"ts": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                                    "skill": skill, "action": action, "applied": True})
    return {"ok": True, "skill": skill, "action": action}


def _touch_registry_run(skill: str, artifact: str | None):
    with _REG_LOCK:
        reg = registry()
        if skill in reg.get("skills", {}):
            reg["skills"][skill]["last_run"] = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
            if artifact:
                reg["skills"][skill]["last_artifact"] = artifact
            store.write_json(REGISTRY, reg)


@contextmanager
def pipeline_run(pipeline: str, artifact: str | None = None):
    """Context manager that logs one pipeline run (start/finish/status/error) to pipeline_runs.jsonl."""
    en, dis = enabled_in(pipeline)
    # HONEST split: only enabled skills with native engine code are actually INVOKED; the rest are enabled but
    # DECLARED-ONLY (SKILL.md folders the deterministic engine can't run). Previously every enabled skill was
    # logged as invoked — so canslim/pead/finviz/theme/episodic/exhaustion showed as "invoked" while only
    # vcp+pullback scanned. The dashboard/attribution can now tell "ran" from "available".
    invoked = [s for s in en if s in ENGINE_IMPLEMENTED]
    declared = [s for s in en if s not in ENGINE_IMPLEMENTED]
    started = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    run = {"run_id": f"{pipeline}-{started}", "pipeline": pipeline, "started": started,
           "finished": None, "skills_invoked": invoked, "skills_declared_not_run": declared,
           "skills_skipped": dis, "artifacts": [artifact] if artifact else [], "status": "running", "error": None}
    try:
        yield run
        run["status"] = "ok"
    except Exception as e:  # stop-on-failure: a bad pipeline is logged, not hidden
        run["status"] = "error"
        run["error"] = f"{type(e).__name__}: {e}"
        raise
    finally:
        run["finished"] = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
        store.append_jsonl(RUNS, run)
        for s in invoked:                     # only skills that actually ran get their run-count/last-run touched
            _touch_registry_run(s, artifact)


# ==================================================================================================
# H5 — SKILL ÖZ-YÖNETİMİ: KANIT EŞİĞİNDE OTOMATİK GÖLGELEME (Hermes paketi, 2026-07-30)
# ==================================================================================================
# NEDEN. `recommend_from_attribution` iki yıldır doğru sayıyı üretiyordu ve hiçbir şey OLMUYORDU:
# öneri `pending` olarak deftere yazılıyor, operatörün panodaki düğmesini bekliyordu. Yani atıf
# ölçümü (Axis-2'nin bütün amacı) bir KARARA hiç bağlanmamıştı — "üretilip tüketilmeyen kanıt"
# deseninin skill katmanındaki hâli. Operatör yönü (2026-07-30): "self-learning'i daha aktif/
# efektif kullan".
#
# NE DEĞİŞTİ, NE DEĞİŞMEDİ.
#   * DEĞİŞMEDİ: PROTECTED beşlisi ASLA gölgelenmez (güvenlik/kısıt katmanı — kanıt ne derse desin).
#     ENGINE_IMPLEMENTED skilleri de dokunulmaz (deterministik motor onları çalıştırır; "gölge"
#     etiketi orada anlamsız bir yalan olurdu).
#   * DEĞİŞMEDİ: eşiğin ALTINDAKİ her şey yine ADVİSORY — `pending` öneri, operatör düğmesi.
#   * DEĞİŞTİ: eşiği AŞAN kanıt otomatik uygulanır (registry'ye `shadow` yazılır), olay defterine
#     kaydedilir ve panoya DUYURU olarak çıkar. Karar geri alınabilir (`activate`).
#
# EŞİK NEDEN BU KADAR SERT. `recommend_from_attribution` advisory eşiği avg_r <= −0,15 / n >= 8.
# OTOMATİK yol için o taban fazla gevşek: 8 işlemde −0,15R, gürültüden ayırt edilemez. Otomatik
# eşik ÜÇ KOŞULU BİRLİKTE ister ve üçü FARKLI kanıt katmanından gelir (tek katmanın kusuru kararı
# tek başına veremesin):
#   (1) cf katmanı: n_cf >= AUTO_CF_MIN_N ve cf_avg_r <= AUTO_AVG_R  (geniş örneklem, simüle çıkış)
#   (2) gerçek katman AYNI YÖNDE: avg_r < 0                          (küçük örneklem, gerçek çıkış)
#   (3) skill ŞU AN etkin ve gölgede değil                           (aksi hâlde karar zaten verilmiş)
# cf katmanının kusuru beyanlıdır (statik-bracket simülasyonu çıkışı gerçekten farklı ölçer) — bu
# yüzden cf TEK BAŞINA karar vermez; gerçek katmanın işaretiyle DOĞRULANMASI şarttır.
AUTO_CF_MIN_N = 20          # cf örneklem tabanı: bunun altında otomatik karar YOK (advisory kalır)
AUTO_AVG_R = -0.30          # cf ortalama R eşiği — advisory eşiğin (−0,15) iki katı sertlik
AUTO_MAX_PER_RUN = 1        # tek koşuda en çok bir skill: toplu bir yanlış-pozitif dalgası olmasın
AUTO_ANNOUNCE = "skill_auto_shadow.json"   # panonun duyuru kartı bu dosyadan okunur


def auto_shadow_from_evidence(apply: bool = True) -> dict:
    """Atıf kanıtı eşiği aşan skilleri OTOMATİK gölgeye al; aşmayanları advisory öneri olarak yaz.

    `apply=False`: hiçbir şey yazılmaz — yalnız ne yapılacağı döner (testler ve `--kuru` CLI için).
    DÖNÜŞ: {"uygulanan": [...], "advisory": [...], "atlanan": [...], "esik": {...}}

    Kilitli desen: registry yazımı `apply_skill_action` üzerinden gider, yani `_REG_LOCK` altında
    okuma+yazma birlikte olur. Doğrudan `store.write_json(REGISTRY, ...)` yazmak, eşzamanlı koşan
    pipeline damgasının bu kararı EZMESİ demekti (audit #19 kayıp-güncelleme deseni)."""
    from . import obs
    uygulanan, advisory, atlanan, dogrulama, motor_ici = [], [], [], [], []
    for s in aktif_katalog():          # ARŞİV: ne otomatik karar adayı ne eşik doğrulaması adayı —
                                       # emekli bir kaydın gölge bayrağı bir KARAR değil bir kalıntıdır
        ad = s["name"]
        if s["protected"]:
            continue                                  # PROTECTED: aday HİÇ olmaz, mutlak kural
        cf_n_, cf_r_ = s.get("n_cf") or 0, s.get("cf_avg_r")
        esik_asti = (cf_r_ is not None and cf_n_ >= AUTO_CF_MIN_N and cf_r_ <= AUTO_AVG_R
                     and s.get("avg_r") is not None and s["avg_r"] < 0)
        if ad in ENGINE_IMPLEMENTED:
            # MOTOR-İÇİ SKİLL: `shadow` bayrağı burada YALNIZCA bir inceleme etiketidir — deterministik
            # motor (strategy.py/guard.py/broker.py) skill'i bayraktan BAĞIMSIZ çalıştırmaya devam eder
            # (bkz. `apply_skill_action` beyanı). Otomatik yazım bu yüzden BURADA YAPILMAZ: yapılsaydı
            # sistem "zararlı skill'i gölgeye aldım" diye kaydeder, davranış HİÇ değişmezdi — skills.py'nin
            # baştan beri önlediği "invoked yalanı"nın aynısı, ters yönde.
            # ÖLÇÜM YİNE YAPILIR ve AYRI KOVAYA yazılır: kanıt eşiğini aşan bir motor-içi skill, bir
            # BAYRAK sorunu değil bir STRATEJİ sorunudur (knob/kapı değişikliği gerekir) ve hermes'in
            # görmesi gereken şey tam olarak budur. Bu kova hiçbir şey UYGULAMAZ.
            if esik_asti:
                motor_ici.append({
                    "skill": ad, "n_cf": cf_n_, "cf_avg_r": cf_r_, "n": s.get("n"),
                    "avg_r": s.get("avg_r"), "zaten_golgede": bool(s["shadow"]),
                    "why": ("kanıt eşiği AŞILDI ama skill MOTOR-İÇİ: registry'ye `shadow` yazmak "
                            "davranışı DEĞİŞTİRMEZ (motor bayraktan bağımsız koşar). Gerçek aksiyon "
                            "knob/kapı düzeyindedir — otomatik bayrak yazımı YAPILMADI.")})
            continue
        if not s["enabled"] or s["shadow"]:
            # ZATEN GÖLGEDE olan skiller karar adayı değildir — ama eşiğin KENDİSİNİ doğrulamak için
            # ölçülürler: "insan/operatör eliyle gölgelenmiş bir skill, otomatik eşiği de aşıyor mu?"
            # Eşik gerçekten iyiyse geçmiş kararlarla ÖRTÜŞMELİ; örtüşmüyorsa eşik ya kör ya gevşek.
            # Bu, mekanizmanın kendi karnesidir ve hiçbir şeyi UYGULAMAZ.
            if s["shadow"]:
                cf_n0, cf_r0 = s.get("n_cf") or 0, s.get("cf_avg_r")
                if cf_r0 is not None and cf_n0 >= AUTO_CF_MIN_N and cf_r0 <= AUTO_AVG_R \
                        and (s.get("avg_r") is not None and s["avg_r"] < 0):
                    dogrulama.append({"skill": ad, "n_cf": cf_n0, "cf_avg_r": cf_r0,
                                      "avg_r": s.get("avg_r"), "n": s.get("n"),
                                      "why": "zaten gölgede VE otomatik eşiği de aşıyor — eşik "
                                             "geçmiş kararla ÖRTÜŞÜYOR"})
                else:
                    dogrulama.append({"skill": ad, "n_cf": cf_n0, "cf_avg_r": cf_r0,
                                      "avg_r": s.get("avg_r"), "n": s.get("n"),
                                      "why": "zaten gölgede ama otomatik eşiği AŞMIYOR — eşik bu "
                                             "kararı kendi başına vermezdi (kör nokta ya da eşik sert)"})
            continue
        cf_n, cf_r = s.get("n_cf") or 0, s.get("cf_avg_r")
        gercek_r = s.get("avg_r")
        kanit = {"skill": ad, "n_cf": cf_n, "cf_avg_r": cf_r, "n": s.get("n"), "avg_r": gercek_r}
        if cf_r is None or cf_n < AUTO_CF_MIN_N or cf_r > AUTO_AVG_R:
            continue
        if gercek_r is None or gercek_r >= 0:
            # cf sert biçimde negatif ama GERÇEK katman doğrulamıyor (ya ölçülemedi ya pozitif).
            # Otomatik karar YOK — advisory'ye düşer ve NEDEN otomatik olmadığı yazılır.
            kanit["why"] = (f"cf {cf_n} örnekte {cf_r}R (eşik {AUTO_AVG_R}) ama gerçek katman "
                            f"doğrulamıyor (avg_r={gercek_r}) — otomatik karar YOK, advisory")
            advisory.append(kanit)
            if apply:
                record_recommendation({"skill": ad, "action": "shadow", "avg_r": cf_r, "n": cf_n,
                                       "rationale": kanit["why"]}, source="h5_auto_advisory")
            continue
        if len(uygulanan) >= AUTO_MAX_PER_RUN:
            kanit["why"] = f"koşu tavanı ({AUTO_MAX_PER_RUN}) doldu — sıradaki koşuya kaldı"
            atlanan.append(kanit)
            continue
        kanit["why"] = (f"cf {cf_n} örnekte {cf_r}R (eşik {AUTO_AVG_R}) VE gerçek katman aynı yönde "
                        f"({s.get('n')} işlemde {gercek_r}R) — KANIT EŞİĞİ AŞILDI")
        if apply:
            res = apply_skill_action(ad, "shadow")
            if not res.get("ok"):
                kanit["why"] += f" | UYGULANAMADI: {res.get('reason')}"
                atlanan.append(kanit)
                continue
            store.append_jsonl(SKILL_RECS, {
                "ts": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                "skill": ad, "action": "shadow", "rationale": kanit["why"],
                "source": "h5_auto", "pending": False, "applied": True, "otomatik": True})
            obs.log("skill_auto_shadowed", skill=ad, cf_avg_r=cf_r, n_cf=cf_n,
                    avg_r=gercek_r, n=s.get("n"), esik=AUTO_AVG_R)
        uygulanan.append(kanit)
    out = {"uygulanan": uygulanan, "advisory": advisory, "atlanan": atlanan,
           "esik_dogrulamasi": dogrulama, "motor_ici_esik_asan": motor_ici,
           "esik": {"cf_min_n": AUTO_CF_MIN_N, "cf_avg_r": AUTO_AVG_R,
                    "kosul": "cf eşiği AŞILDI **ve** gerçek katman aynı yönde **ve** skill etkin",
                    "max_per_run": AUTO_MAX_PER_RUN},
           "korunanlar": sorted(PROTECTED),
           "ts": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
           "beyan": ("PROTECTED beşlisi ve motor-içi skiller ASLA otomatik gölgelenmez. Karar GERİ "
                     "ALINABİLİR (activate). Eşik altındaki kanıt advisory kalır."),
           "uygulandi_mi": bool(apply)}
    if apply and (uygulanan or advisory or motor_ici):
        # PANO DUYURUSU: otonom bir karar sessiz kalmamalı. Dosya panonun skill kartında okunur.
        store.write_json(AUTO_ANNOUNCE, out)
    return out


# ==================================================================================================
# EKSEN-2 ÜRETECİNİN KADANSI + SESSİZLİĞİNİN TEŞHİSİ (öğrenme otomasyonu turu, 2026-07-30)
# ==================================================================================================
# TEŞHİS — "üretici hiç koşmuyor" DEĞİL, "üretici koşuyor ve HİÇBİR ŞEY üretmiyor, sebebi de hiçbir
# yerde yazmıyor". Üretici İKİ TANE ve ikisi de bulundu:
#
#   (a) `recommend_from_attribution()` — deterministik Eksen-2 sinyali. TEK çağıranı
#       `reflect._proposal` (reflect.py:643) ve oradan çıktısı yalnızca öneri sözlüğünün
#       `skill_recommendation` alanına gömülür; deftere ancak o öneri `reflect._submit_locked`e
#       (reflect.py:706) ulaşırsa yazılır. Yani üreteç, BİR HİPOTEZ ÖNERİSİNİN YAN ÜRÜNÜYDÜ.
#       Ve hermes'in canlı yollarının İKİSİ de o alanı boş bırakır: beyin zinciri (`propose_with_llm`)
#       alanı hiç doldurmaz, bakir-düğme yolu ise BİLEREK `None` yazar (hermes.py, "AXIS-2 NOTU
#       EKLENMEZ" notu). Sonuç: canlı gecede üreteç sonuçsuz koşar.
#   (b) `auto_shadow_from_evidence()` — H5 (bugün eklendi), `loop.py:848`den çağrılır; yani
#       `daily_cycle` ⊂ "yeni seansın barı geldi" rehineliğinde (bkz. scheduler._learning_cadence).
#
# EŞİK ÖLÇÜMÜ (canlı katalog, 2026-07-30 — DEĞİŞTİRİLMEDİ, ÖLÇÜLDÜ):
#     position-sizer              n=95  avg_r=−0,042   n_cf=0      → PROTECTED, aday değil
#     pre-trade-discipline-gate   n=95  avg_r=−0,042   n_cf=0      → PROTECTED, aday değil
#     vcp-screener                n=91  avg_r=+0,000   n_cf=1004   → eşik aralığında (−0,15..+0,30)
#     pullback-screener           n=4   avg_r=−1,000   n_cf=21     → n<8; zaten gölgede
#     stockbee-momentum-burst     n=0   avg_r=None     n_cf=1080   → GERÇEK katman BOŞ
#     stockbee-episodic-pivot     n=0   avg_r=None     n_cf=1      → GERÇEK katman BOŞ
# Yani `recommend_from_attribution()` = [] DÜRÜST bir sonuçtur: eşiği geçen skill YOK. Ama eşiğin
# YAPISAL bir körlüğü var ve ölçüm onu gösteriyor: eşik YALNIZ gerçek katmana bakıyor (`n`,`avg_r`)
# ve `catalog()`ün BUGÜN taşımaya başladığı cf katmanını (`n_cf`,`cf_avg_r`) hiç okumuyor. En büyük
# örneklemli iki skill (1080 ve 1004 cf satırı) gerçek katmanda n=0/n=91 olduğu için üretecin
# gözünde YOK. EŞİK BU TURDA DEĞİŞTİRİLMEDİ (yönerge: "kafadan değiştirme") — teşhis raporlanır ve
# `axis2_cycle` her koşuda hangi kolun kimi elediğini SAYIYLA yazar, ki eşik tartışması bir daha
# tahminle değil ölçümle yapılsın.
AXIS2_FILE = "axis2_status.json"      # kadansın son koşusu (okuyan: analytics + api)


def axis2_diagnosis(min_n: int = 8) -> dict:
    """ÜRETECİN SESSİZLİĞİNİN SATIR SATIR MUHASEBESİ — her skill hangi eşik kolunda elendi?

    "0 öneri" tek başına iki BAMBAŞKA hâli aynı gösterir: (1) kanıt var ama eşiği geçmiyor,
    (2) kanıt hiç ölçülmemiş. İkisini ayırmak için her skill bir KOVAYA düşer ve kova adı sebebin
    kendisidir. Hiçbir şey UYGULAMAZ, hiçbir eşiği DEĞİŞTİRMEZ.

    ÜÇÜNCÜ HÂL AYRILDI (Ç3, 2026-08-09): `arsiv`. Emekli/birleştirilmiş kayıtlar "ölçülmemiş"
    DEĞİLDİR — ölçülecek bir şeyleri YOKTUR, çünkü zincirde üyelikleri yok ve klasörleri
    `skills/_emekli/` altında. Eskiden hepsi `gercek_katman_olculmemis` kovasına düşüyordu ve o
    kova, 36 arşiv kaydıyla şişmiş hâlde "üretecin körlüğü" diye okunuyordu. Sayı doğruydu,
    ETİKET yanlıştı; ve yanlış etiket, olmayan bir kusuru sürekli rapor eden bir alarmdır."""
    kova: dict[str, list] = {}
    for s in catalog():
        ad, n, avg = s["name"], (s.get("n") or 0), s.get("avg_r")
        satir = {"skill": ad, "n": n, "avg_r": avg,
                 "n_cf": s.get("n_cf") or 0, "cf_avg_r": s.get("cf_avg_r")}
        if s.get("yasam_dongusu") == ARSIV:
            # EN BAŞTA: arşiv, `protected`ten de önce gelir. Bir gün emekliye ayrılan korumalı bir
            # kayıt olursa onun kovası da "korumalı aday" değil ARŞİV olmalıdır.
            k = ARSIV
        elif s["protected"]:
            k = "korumali"
        elif avg is None:
            # GERÇEK KATMAN BOŞ. Bu bir "nötr" değil bir ÖLÇÜLMEMİŞLİKTİR ve cf katmanı doluysa
            # üretecin körlüğünün TAM ADRESİ burasıdır — kova adı onu söyler.
            k = "gercek_katman_olculmemis_cf_dolu" if (s.get("n_cf") or 0) > 0 \
                else "gercek_katman_olculmemis"
        elif n < min_n and not _cf_arm(s, min_n):
            # cf kolu da tutmadıysa örneklem GERÇEKTEN yetersizdir. Kova adı hangi kolun
            # eksik kaldığını söyler ki "biraz daha veri lazım" ile "cf defteri de boş" ayrılsın.
            k = ("ornek_yetersiz_cf_de_yetersiz" if (satir["n_cf"] or 0) < min_n * CF_SAMPLE_MULT
                 else "ornek_yetersiz_gercek_katman_yarim")
        else:
            # BURADAN İTİBAREN hüküm YALNIZ gerçek katmandan verilir (cf kolu örneklem kapısıydı).
            if avg <= -0.15:
                k = "shadow_esigi_asildi" if (s["enabled"] and not s["shadow"]) else "zaten_golgede"
            elif avg >= 0.30:
                k = "lean_in_esigi_asildi"
            else:
                k = "esik_araliginda"
            if n < min_n:
                k += "_cf_destekli"      # yarı örneklemli gerçek ölçüm, cf koluyla masaya oturdu
        kova.setdefault(k, []).append(satir)
    return {"kovalar": {k: v for k, v in sorted(kova.items())},
            "sayim": {k: len(v) for k, v in sorted(kova.items())},
            # PAYDA KAYNAĞI ÇIKTIDA (Ç3 · C10): pano paydayı SABİT YAZMAZ, buradan okur. `arsiv`
            # kovası paydanın DIŞINDADIR — "ölçülmüş / aktif küme" oranı, arşivi bölene de paydaya
            # da katmaz. Sayı burada üretilir çünkü kovaları üreten dal yapısı burada.
            "arsiv_kova": ARSIV,
            "aktif_payda": sum(len(v) for k, v in kova.items() if k != ARSIV),
            "esik": {"min_n": min_n, "shadow_avg_r": -0.15, "lean_in_avg_r": 0.30,
                     # BEYAN GÜNCELLENDİ (2026-07-30 temizlik turu): cf katmanı ARTIK OKUNUYOR —
                     # ama yalnız ÖRNEKLEM kolunda. Eski metin ("cf OKUNMUYOR") artık yanlış
                     # olurdu ve bu alan tam da eşiğin ne yaptığını okunur kılmak için var.
                     "cf_kol": {"gercek_asgari": min_n * CF_REAL_FRACTION,
                                "cf_asgari": min_n * CF_SAMPLE_MULT},
                     "katman": ("hüküm YALNIZ gerçek (n, avg_r); cf katmanı (n_cf, cf_avg_r) "
                                "YALNIZ örneklem kolunda okunur — cf tek başına öneri TETİKLEMEZ")},
            "beyan": ("shadow/lean_in EŞİKLERİ bu turda DEĞİŞTİRİLMEDİ (−0,15 / +0,30); değişen "
                      "yalnız ÖRNEKLEM kapısıdır ve o da cf'yi hükme değil uygunluğa sokar. "
                      "`gercek_katman_olculmemis_cf_dolu` kovası hâlâ kalan körlüğü ölçer: gerçek "
                      "katman HİÇ ölçülmemişse (avg_r None) cf kolu da açılamaz — bilerek. "
                      "`arsiv` kovası AYRIDIR ve paydaya girmez (Ç3): emekli kayıt ölçülmemiş "
                      "değil, ölçülecek olmayan kayıttır.")}


def axis2_cycle(apply: bool = True) -> dict:
    """EKSEN-2 KADANSI — üreteci bir hipotez önerisinin yan ürünü olmaktan ÇIKARIR.

    ÜÇ İŞ, hepsi mevcut mekanizmalarla (yeni yetki YOK):
      1. `recommend_from_attribution()` koşar ve çıkanlar `record_recommendation` ile PENDING
         yazılır — eskiden bu yalnız deterministik bir öneri ship yoluna girdiğinde oluyordu.
      2. `auto_shadow_from_evidence()` koşar — H5'in kendi eşikleri, kendi PROTECTED/motor-içi
         korumaları. `loop.py`deki çağrısı YERİNDE KALIR (iki koşu zararsız: eşiği geçen skill
         ilkinde gölgelenir, ikincisinde "zaten gölgede" diye elenir).
      3. Üretim OLMADIYSA nedeni sayıyla yazılır (`axis2_diagnosis`) — sessiz bir sıfır, ölçülmüş
         bir sıfır değildir.

    `apply=False`: hiçbir şey yazılmaz, ne yapılacağı döner (testler + kuru koşu)."""
    from . import obs
    kaydedilen, reddedilen = [], []
    recs = recommend_from_attribution()
    for r in recs:
        if not apply:
            kaydedilen.append(r)
            continue
        (kaydedilen if record_recommendation(r, source="axis2_cadence") else reddedilen).append(r)
    otomatik = auto_shadow_from_evidence(apply=apply)
    teshis = axis2_diagnosis()
    out = {"ts": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
           "uretilen": recs, "kaydedilen": kaydedilen,
           # REDDEDİLEN = zaten AÇIK bir pending var (dedup). Bir arıza değil ama sayılmalı:
           # "üretti ama yazmadı" ile "hiç üretmedi" tek satırda birleşirse kadans ölü görünür.
           "yinelenen": reddedilen,
           "otomatik": {k: otomatik.get(k) for k in
                        ("uygulanan", "advisory", "atlanan", "motor_ici_esik_asan", "esik")},
           "bekleyen_toplam": len(pending_recommendations()),
           "teshis": teshis, "uygulandi_mi": bool(apply)}
    if apply:
        store.write_json(AXIS2_FILE, out)
    obs.log("axis2_cycle", uretilen=len(recs), kaydedilen=len(kaydedilen),
            yinelenen=len(reddedilen), bekleyen=out["bekleyen_toplam"],
            otomatik_uygulanan=len(otomatik.get("uygulanan") or []),
            kovalar=teshis["sayim"],
            detail="Eksen-2 üreteci kadansta koştu — çıktısı bir hipotez önerisine bağlı DEĞİL")
    return out
