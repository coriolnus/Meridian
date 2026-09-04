"""shadow_variants.py — aynı günün canlı aday akışına farklı parametre kümeleriyle KÂĞIT karar uygulayan gölge-varyant karar defteri.

NE YAPAR. Kanıt hızı tek parametre kümesine bağlıydı: canlı strateji günde BİR karar akışı üretir
ve bir düğmenin etkisini sormanın iki yolu vardı — OOS replay (geçmişe bakar, pencereleri tükenir)
ya da canlıya ship edip beklemek (yavaş, sonuçlu). Bu modül aradaki eksik katmandır: her EOD
turunda `VARIANTS` sözlüğündeki her kol için "hangi adaylar sinyal üretirdi, kapı ne derdi, hangi
set silahlanırdı, geometri ne olurdu" ölçülür ve canlı kararla ayrışması satır satır deftere
yazılır. Kanıt hızı çarpanıdır, risk çarpanı değil. Ölçülen şey KARARDIR, portföy değil:
varyantların pozisyon ömrünü (fill → yönetim → çıkış → mark) kalıcı kâğıt kitaplarla izleyen ayrı
motor `shadow_lifecycle`tadır; bu modül o kitapların yalnız DIŞ OKUYUCUSUDUR (`--karne`).

KİLİT GİRİŞLER. `record_cycle` (loop.daily_cycle kancası: bir tur × tüm varyantlar; `bars`
verilirse yaşam-döngüsü motorunu da aynı kancadan koşturur), `VARIANTS` / `LIFECYCLE_KNOBS_V2`,
`validate_knobs` (uydurma düğme adı sessiz kalmaz), `_judge` (karar ve kitap katmanlarının
paylaştığı TEK kapı yolu), `summarize`/`render_summary` (`--ozet`), `summarize_books`/
`render_karne` (`--karne`), `main` (CLI).

YASALAR — GÖLGE KATMANI. (1) SIFIR YETKİ: bu defterden ship yolu YOKTUR; canlıya geçiş yalnız
OOS kapısından (prescreen/reflect). (2) KANUN ÇAĞRILIR, KOPYALANMAZ: tarama `strategy.scan_all`,
kapı `guard.classify_gate`, karartma `earnings.in_blackout`, kısma `broker.derisk_mult`/
`max_positions_at` — hepsi üretimin kendi fonksiyonları; ikinci kopya, defterin zamanla stratejiyi
değil KENDİNİ ölçmesi demekti. (3) KİTAP KOPYADIR, SALT OKUNUR: canlı `PaperBroker` nesnesine
erişilmez, loop bir projeksiyon geçirir; strategy.yaml'a, portfolio.json'a, kapıya ve hipotez
defterine hiçbir yazım yolu çıkmaz — canlı karara dokunamaz. (4) ÇOKLU-KARŞILAŞTIRMA PAYDASI
satırda taşınır: `k_variants` (karar) ile `k_lifecycle` (para) AYRI paydalardır ve tek sayıya
indirgenmez; çıkış-düğmeli kollar bu sette yoktur, çünkü giriş yolunda hiç okunmazlar — kontrol
koluyla karar-özdeş olur, paydayı sıfır ölçüm kazancıyla şişirirlerdi (testle çakılı:
tests/test_sadelestirme_v123.py). (5) PIT çapası: tohum (tarihsel) turda bugünün kazanç takvimi
konuşturulmaz (`_CANLI_TUR`). Nüfus tamdır: kanca candidates ∪ near_miss geçirir — gevşetilmiş
eşik kümesi her varyantın üretebileceği kümenin üst kümesidir.

OKUR: canlı P2/P3 girdileri çağrılabilirlerle loop'tan; bounds sözleşmesi; shadow_lifecycle'ın
kitap/işlem defterleri (yalnız okuma).  YAZAR: yalnız kendi defteri `state/shadow_variants.jsonl`.
"""
from __future__ import annotations

import os

from . import barclock, earnings, guard, obs, skills, store, strategy
from .broker import derisk_mult, max_positions_at

# Varsayılan AÇIK: tek yan etkisi kendi defterine yazmaktır (4b ile aynı gerekçe). Kapatma anahtarı
# yine de var — ölçüm bile olsa operatör bir katmanı susturabilmelidir.
ENABLED = os.environ.get("MERIDIAN_SHADOW_VARIANTS", "1") != "0"

LEDGER = "shadow_variants.jsonl"
MAX_ROWS_PER_VARIANT = 12         # satıra gömülen aday detayının tavanı (defter şişmesin)

# --- VARYANT TANIMLARI — TEK SÖZLÜK ----------------------------------------------------------------
# İLK SET, ÖLÇÜM KANITLARINDAN TÜRETİLDİ (uydurma yok):
#   V1  entry.min_rvol=1.5        G2/S2 ölçümü: Δ-0.046 AMA fold 3/3 kazanıyor + CVaR iyileşiyor →
#                                 "kapıdan geçmedi ama ölmedi" sınıfı; canlı akışta günlük kanıt hak eder.
#   V2  stop 3.0 + breakeven 0    G3b çıkış reformu: geniş stop + BE kapatma (BE'nin erken düz-çıkış
#                                 ürettiği şüphesi ölçülmedi; iki düğme BİRLİKTE anlamlı, ayrı ayrı değil).
#   V4  min_volume_ratio 1.0 (bounds TABANI) + min_rvol 1.5   TAKAS: darboğaz turu hacim×1.5 eşiğinin
#                                 aday kuraklığının baş sorumlusu olduğunu ölçtü; rvol tabanı onun
#                                 yerine kaliteyi tutabilir mi? Tek düğme bunu SORAMAZ — takas iki düğmelidir.
#   V5  (boş) KONTROL             mevcut varsayılan. Kontrol kolu OLMADAN diğer dördünün "farkı" bir
#                                 sayı değil bir izlenimdir: aynı gün, aynı akış, aynı kod yolu.
# Düğme adları/aralıkları `state/bounds.yaml` sözleşmesindendir; `validate_knobs()` bunu KOŞU ANINDA
# doğrular (uydurma düğme adı sessizce "etkisiz varyant" gibi görünürdü — en sinsi hata sınıfı).
#
# ÇIKARILDI 2026-07-30 — V3 (scale_out 0.5 @ 2.0R, Batch L #8), V6 (early_kill_pivot=1, PARA-v3 E1:
# para_delta +0.0688 / P 0.659), V7 (early_kill + scale_out 0.5, PARA-v3 E4: fold 3/3 / P 0.612).
# GEREKÇE: v1 GİRİŞ kararını ölçer; bu üç kolun düğmeleri ÇIKIŞ/FILL ömründe okunur, giriş yolunda
# HİÇ okunmaz → üçü de kontrol kolu V5 ile KARAR-ÖZDEŞTİ. Ölçüm kazancı SIFIR, bedeli gerçek:
# `k_variants` paydasını şişirip gerçekten ayrışan kolların (V1/V2/V4) çoklu-karşılaştırma cezasını
# artırıyorlardı. V3 ilk setten beri paydadaydı ve eski "geometriyi arm anında değiştirir → görünür"
# gerekçesi bu ölçümle YANLIŞLANDI. E1/E4'ün kanıt birikimi BAŞKA KANALDAN yürüyor (haftalık
# prescreen yeniden-ölçümü) — gölge katmanı o soruyu v1'de ölçemez, ölçebilir gibi görünmesi
# uydurma olurdu. GÖLGE-v2 yaşam-döngüsü motoru gelince üçü de geri eklenecek: o katman fill →
# yönetim → çıkış → mark izlediği için bu düğmeler orada GERÇEKTEN ayrışır.

# v2'YE KADAR SETE ALINMAYACAK DÜĞMELER — kural burada TEK YERDE yazılı ve testle çakılı. Liste bir
# görüş değil bir ÖLÇÜM sonucudur: bu anahtarların hiçbiri `strategy.scan_all` / `guard.classify_gate`
# yolunda okunmaz (kanıt: yukarıdaki ÇIKARILDI notu + v123 çivisi). Yeni bir kol bunlardan birini
# taşıyorsa v1'de karar-özdeş olur ve paydayı bedavaya şişirir.
LIFECYCLE_KNOBS_V2 = frozenset({
    "exit.early_kill_pivot", "exit.early_kill_bars",     # strategy.manage_position ömrü
    "exit.scale_out_frac", "exit.scale_out_r",           # broker.scale_out (FILL) ömrü
})

VARIANTS: dict[str, dict] = {
    "V1": {"label": "min_rvol 1.5 (G2/S2 kolu)",
           "knobs": {"entry.min_rvol": 1.5}},
    "V2": {"label": "stop 3.0 ATR + breakeven KAPALI (G3b çıkış kolu)",
           "knobs": {"stop_loss_atr_mult": 3.0, "exit.breakeven_r": 0.0}},
    "V4": {"label": "hacim tabanı 1.0 ↔ min_rvol 1.5 TAKASI",
           "knobs": {"entry.min_volume_ratio": 1.0, "entry.min_rvol": 1.5}},
    "V5": {"label": "KONTROL — mevcut varsayılan", "knobs": {}},
}

# Bu turda UYGULANAN ve UYGULANMAYAN kapılar SATIRA YAZILIR. "Hangi kapıyla ölçüldü" sorusu, kapının
# kendisi kadar önemlidir (4b'nin `gate_inputs_as_of` dersi): eksik kapı, gölge setini canlıdan daha
# CÖMERT gösterir ve fark "varyant iyi" diye okunur.
# `earnings.in_blackout` YALNIZ CANLI TURDA uygulanır (kardeş-PIT düzeltmesi — aşağıdaki
# `_CANLI_TUR` bloğu): tohumlama bacağında kapı KONUŞMAZ ve satır bunu `olculemedi_seed` diye söyler.
GATES_APPLIED = ("guard.classify_gate", "earnings.in_blackout")
GATES_SKIPPED = {
    "mirror_busy": "aynada bekleyen emir/yetim kontrolü — varyantın ayna emri YOKTUR, kavram tanımsız",
    "shadow_veto": "terfili gölge modelin REVIEW vetosu — model terfili değilse canlıda da no-op; "
                   "terfi durumu güne bağlı olduğu için varyant setine sokmak ölçümü oynak yapardı",
}

# --- KARDEŞ-PIT ÇAPASI ----------------------------------------------------------------------------
# `state/earnings.csv` bir İLERİ-PENCERE snapshot'ıdır (bugünden ~21 gün ileri, sembol başına 1,0
# tarih): yalnız BUGÜNÜN turunun kararı için PIT'tir. `_judge` iki yerden çağrılır —
#   (a) bu modülün kendi EOD turu (`record_cycle` → `_decide_variant`): tarih CANLI turun tarihidir,
#       takvim PIT'tir, kapı aynen çalışır (`loop.daily_cycle` ile birebir);
#   (b) `shadow_lifecycle._seed` (aynı kancanın içinden, GEÇMİŞ seanslar): tarih tarihseldir ve
#       bugünün takvimini o karara uygulamak `backtest.replay`in bıraktığı ihlalin ta
#       kendisidir (kardeşi `cf_backfill.py`de aynı gün kapatıldı).
# ÇAPA: turu açan tarih `record_cycle`ta damgalanır; `_judge` yalnız O tarihte takvimi konuşturur.
# NEDEN TARİH KARŞILAŞTIRMASI DEĞİL DE ÇAPA: canlı EOD turu "bugün"ü değil SON KAPANMIŞ SEANSI
# işler ve evren-kapsaması ertelemesi onu birkaç gün geriye alabilir (loop.py'deki `_deferred_for_coverage` yerel değişkeni).
# `date < bugün` kuralı o turları da tarihsel sayar ve CANLI davranışı değiştirirdi — düzeltmenin
# tek sözü "canlı bit-bit korunur"ken bunu yapmak, kapatmaya çalıştığımız sınıfın aynısı olurdu.
# ÇAPA YOKSA (`None`) DAVRANIŞ ESKİSİ: tur açılmamışsa (doğrudan `_judge` çağrısı) kimse "bu karar
# tarihseldir" demiş değildir; ölçülmemiş bir yolda kapıyı sessizce kapatmak, bu turda kapatılan
# uydurmanın ters yönlü hâli olurdu. Üretimde çapasız yol YOKTUR: `shadow_lifecycle.run_cycle`ın
# tek çağıranı `record_cycle`tır ve çapa ondan ÖNCE damgalanır (yapısal test v185'te).
_CANLI_TUR: dict = {"date": None}


def _takvim_pit_mi(date) -> bool:
    """Bu karar, elimizdeki takvimin PIT olduğu tur mu? (gerekçe: `_CANLI_TUR` bloğu)"""
    capa = _CANLI_TUR.get("date")
    return capa is None or str(date) == str(capa)


def validate_knobs(bounds: dict) -> list[dict]:
    """Her varyantın her düğmesi bounds SÖZLEŞMESİNDE var mı, aralık/adım içinde mi?

    NEDEN GEREKLİ: `{**eff, "entry.min_rvvol": 1.5}` gibi bir yazım hatası hiçbir istisna üretmez —
    strategy o anahtarı okumaz, varyant "etkisiz" görünür ve defter aylarca 'fark yok' der. Uydurma
    yasağının bu modüldeki karşılığı: tanımlı olmayan düğme SESSİZ KALMAZ."""
    out = []
    for vid, spec in VARIANTS.items():
        for k, v in spec["knobs"].items():
            b = bounds.get(k)
            if b is None:
                out.append({"variant": vid, "knob": k, "hata": "bounds.yaml'da TANIMSIZ düğme"})
                continue
            try:
                lo, hi = float(b["min"]), float(b["max"])
            except (KeyError, TypeError, ValueError) as e:
                # SESSİZ DEĞİL: hata TÜRÜ satıra taşınır ve `record_cycle` turu atlar. Doğrulayıcının
                # kendi körlüğünü gizlemesi, doğrulamamaktan daha kötüdür.
                out.append({"variant": vid, "knob": k,
                            "hata": f"bounds satırı biçimsiz ({type(e).__name__})"})
                continue
            if not (lo <= float(v) <= hi):
                out.append({"variant": vid, "knob": k, "yeni": v,
                            "hata": f"aralık dışı [{lo}, {hi}]"})
    return out


def _book_state(book: dict, limits: dict, sector_of) -> dict:
    """Kopya kitap projeksiyonundan kapı girdileri. `derisk_mult`/`max_positions_at` ÜRETİMİN
    fonksiyonlarıdır — kısma rampası burada yeniden yazılmaz.

    `max_open` neden `limits["max_open_positions"]` (kısılmış tavan DEĞİL): canlı P3 slot sayısını ham
    tavandan hesaplar, kısma FILL anında broker'da uygulanır. Gölge arm-anını ölçüyor, o yüzden aynı
    tavanı kullanır; kısma çarpanı satıra BİLGİ olarak yazılır (ertesi açılışın qty'sini o belirler)."""
    pos = book.get("positions") or {}
    eq = float(book.get("equity") or 0.0)
    peak = float(book.get("peak_equity") or eq)
    sector_ct: dict = {}
    for t in pos:
        s = pos[t].get("sector") or sector_of(t)
        sector_ct[s] = sector_ct.get(s, 0) + 1
    return {
        "n_open": len(pos),
        "open_risk_r": sum(float(p.get("size_r") or 0.0) for p in pos.values()),
        "sector_ct": sector_ct,
        "size_mult": derisk_mult(eq, peak),
        "max_open": int(limits["max_open_positions"]),
        "throttled_max_open": max_positions_at(eq, peak, limits["max_open_positions"]),
        "equity": eq, "peak_equity": peak,
    }


def _signals(tickers, params, tail_of, rs_of):
    """Varyant parametreleriyle SİLAHLANABİLİR sinyaller. `scan_all` ÇAĞRILIR (kanun kopyalanmaz);
    dilim reçetesi `tail_of` ile canlı P2'den GELİR — pencere kayması "aynı akış" iddiasını bozardı.

    Tek sembolün patlaması turu düşürmez: sebebi sayılır ve rapora girer, sessizce elenmez."""
    out, failed = [], []
    for tk in tickers:
        try:
            found = strategy.scan_all(tail_of(tk), params, rs_of(tk), ticker=tk)
        except Exception as e:
            failed.append({"ticker": tk, "error": f"{type(e).__name__}: {str(e)[:80]}"})
            continue
        sig = next((found[su] for su in strategy.ARMED_SETUPS if su in found), None)
        if sig is not None:
            out.append(sig)
    # Canlı P2 ile AYNI SIRA: skora göre azalan. Sıra kozmetik değil — slot tükendiğinde kimin
    # silahlandığını sıra belirler, yani yanlış sıralama varyant setini sessizce değiştirir.
    out.sort(key=lambda s: s.score, reverse=True)
    return out, failed


def _plan_of(sig, date: str, sector: str, limits: dict, version: int) -> dict:
    """Sinyalden plan sözlüğü — canlı P3'ün ürettiği ALANLARIN kapının okuduğu alt kümesi.

    Kapının okuduğu her alan burada var (guard sözleşmesi): entry_trigger/stop/size_r/sector/score/
    r_multiple_expected/regime_at_plan/setup. Kimlik `SV-` önekli: bu satır bir plan DEĞİLDİR ve
    `trade_plans.jsonl` kimlik biçimiyle (PLAN_ID_RE) ASLA karışmamalıdır — karışırsa canlı defterin
    eşleştirmeleri (trades.plan_id, cf) hayali bir planla eşleşmeye çalışır."""
    return {"id": f"SV-{date}-{sig.ticker}", "date": date, "ticker": sig.ticker, "side": "long",
            "entry_trigger": sig.entry_trigger, "stop": sig.stop, "targets": [sig.profit_target],
            "profit_target": sig.profit_target, "r_per_share": sig.r_per_share,
            "size_r": min(sig.size_r, limits["max_position_r"]),
            "r_multiple_expected": round((sig.profit_target - sig.entry_trigger) / sig.r_per_share, 2)
            if sig.r_per_share else None,
            "sector": sector, "score": sig.score, "setup": sig.setup,
            "dormant_setup": False, "strategy_version": version,
            "skill_chain": [skills.screener_for(sig.setup), "position-sizer",
                            "pre-trade-discipline-gate"]}


def _judge(sigs: list, date: str, *, sector_of, max_corr_of, params: dict, regime: dict,
           goal: dict, limits: dict, version: int, bk: dict,
           eg: dict | None = None) -> tuple[list, list, list]:
    """Sinyal listesi → (yargılanan satırlar, silahlanan satırlar, silahlanan PLANLAR).

    KAPI YOLU BURADA TEK YERDE. v1 bunu CANLI kitabın projeksiyonuna karşı koşturur (karar
    ayrışmasını ölçmek için), gölge-v2 ise kolun KENDİ kitabına karşı (o kolun kendi portföy
    kısıtları vardır). Aynı hüküm, iki farklı portföy girdisi — ikinci bir kapı uygulaması YOK.

    Üçüncü dönüş değeri (`armed_plans`) `[{"plan": {...}, "pivot": float}]` biçimindedir: pivot
    plan SÖZLÜĞÜNE konmaz, YAN haritada taşınır (`backtest.replay`in `armed_pivots` deseni ve aynı
    gerekçe — pivot bir defter alanı değil `broker.py::PaperBroker.fill_entry`e giden bir İCRA girdisidir).

    `eg`: KAZANÇ-KAPISI SAYACI (kardeş-PIT). Verilirse yerinde doldurulur; dönüş
    ÜÇLÜSÜ DEĞİŞMEZ — `shadow_lifecycle` bu üçlüyü açıyor ve arity değişikliği ölçümle ilgisiz bir
    kırmızı üretirdi (dosya-ayrıklık sözleşmesi: o dosyaya bu turda dokunulmuyor)."""
    # Tur başına BİR kez: `_takvim_pit_mi` sembole değil TARİHE bakar (aday başına çağırmak aynı
    # cevabı 250 kez üretirdi — `loop`taki "tur başına bir yüklem" kuralının aynısı).
    pit = _takvim_pit_mi(date)
    sector_ct = dict(bk["sector_ct"])
    armed, judged, armed_plans = [], [], []
    slots = bk["max_open"] - bk["n_open"]
    open_risk = bk["open_risk_r"]
    for sig in sigs:
        sector = sector_of(sig.ticker)
        plan = _plan_of(sig, date, sector, limits, version)
        portfolio = {"open_positions": bk["n_open"] + len(armed),
                     "sector_counts": sector_ct,
                     # 0.0 arm ANINDA — canlı P3 ile BİREBİR (loop.py'deki gerekçe: backtest de
                     # devre kesiciyi arm'da değil FILL'de uygular; buraya gerçek gün P&L'i koymak
                     # gölgeyi canlıdan ayrıştırırdı).
                     "day_pnl_pct": 0.0,
                     "open_risk_r": open_risk + sum(float(a["size_r"]) for a in armed),
                     "max_corr": max_corr_of(sig.ticker)}
        verdict, reasons = guard.classify_gate(plan, portfolio, regime, goal, params)
        # ---- KARDEŞ-PIT DÜZELTMESİ — gerekçe `_CANLI_TUR` bloğunda. CANLI turda hiçbir
        # şey değişmedi (aynı çağrı, aynı koşul, aynı sıra, aynı etiket); TARİHSEL (tohum) turda
        # `in_blackout` HİÇ ÇAĞRILMIYOR: ne veto ne etiket. `earnings_blackout` orada False değil
        # None — "karartma yok" ile "ölçemedik" aynı şey değildir ve False demek, bu turda
        # `coverage:"known"` yalanıyla birlikte kapatılan uydurmanın ta kendisiydi.
        if pit:
            bl = earnings.in_blackout(sig.ticker, date)
            _cov = "known" if earnings.known(sig.ticker) else "no_calendar_data"
        else:
            bl, _cov = None, "olculemedi_seed"
        if eg is not None:
            eg["plan"] = eg.get("plan", 0) + 1
            eg["pit" if pit else "olculemedi_seed"] = eg.get("pit" if pit else "olculemedi_seed", 0) + 1
        if verdict != "NO_GO" and bl:
            verdict, reasons = "NO_GO", list(reasons) + ["kazanç öncesi karartma (earnings blackout)"]
        row = {"ticker": sig.ticker, "setup": sig.setup, "score": sig.score,
               "entry_trigger": round(float(sig.entry_trigger), 4),
               "stop": round(float(sig.stop), 4),
               "profit_target": round(float(sig.profit_target), 4),
               "r_per_share": round(float(sig.r_per_share), 4) if sig.r_per_share else None,
               "size_r": plan["size_r"], "rr": plan["r_multiple_expected"],
               "rvol20": sig.rvol20, "verdict": verdict, "why": list(reasons)[:3],
               "earnings_blackout": bool(bl) if bl is not None else None,
               "earnings_coverage": _cov}
        if verdict != "NO_GO" and slots > 0:
            row["would_arm"] = True
            armed.append(row)
            armed_plans.append({"plan": plan, "pivot": float(getattr(sig, "pivot", 0.0) or 0.0)})
            sector_ct[sector] = sector_ct.get(sector, 0) + 1
            slots -= 1
        else:
            row["would_arm"] = False
        judged.append(row)
    return judged, armed, armed_plans


def _decide_variant(vid: str, spec: dict, date: str, tickers: list, *, tail_of, rs_of, sector_of,
                    max_corr_of, eff: dict, regime: dict, goal: dict, limits: dict, version: int,
                    bk: dict) -> dict:
    """Tek varyantın o günkü KÂĞIT kararı. Emir yok, dosya yok, canlı nesne yok.

    `_sigs`/`_armed_plans` alanları ALT ÇİZGİ ile başlar ve `record_cycle` onları satıra YAZMADAN
    ÖNCE çıkarır: gölge-v2 yaşam-döngüsü motoru (aynı kanca) taramayı ikinci kez koşmasın diye
    devredilirler. Defter şeması DEĞİŞMEZ — bu iki alan diske hiç ulaşmaz."""
    params = {**eff, **spec["knobs"]}
    sigs, scan_failed = _signals(tickers, params, tail_of, rs_of)
    # KAZANÇ-KAPISI SAYACI (kardeş-PIT) — satıra girer, `summarize` okur (YASA 6).
    # Bu defterin satırları CANLI turdan doğduğu için burada `olculemedi_seed` 0 olmalıdır ve
    # sayacın asıl işi budur: "0 plan etkilendi" beyanı, beyan değil ÖLÇÜM olarak taşınır.
    eg: dict[str, int] = {}
    judged, armed, armed_plans = _judge(sigs, date, sector_of=sector_of, max_corr_of=max_corr_of,
                                        params=params, regime=regime, goal=goal, limits=limits,
                                        version=version, bk=bk, eg=eg)
    return {"variant": vid, "label": spec["label"], "knobs": dict(spec["knobs"]),
            "_sigs": sigs, "_armed_plans": armed_plans, "earnings_gate": eg,
            "signal_n": len(sigs), "would_arm_n": len(armed),
            "verdicts": {v: sum(1 for r in judged if r["verdict"] == v)
                         for v in ("GO", "REVIEW", "NO_GO")},
            "would_arm": [r["ticker"] for r in armed],
            "detail": judged[:MAX_ROWS_PER_VARIANT],
            "detail_truncated": max(0, len(judged) - MAX_ROWS_PER_VARIANT),
            "scan_failed": scan_failed[:5], "scan_failed_n": len(scan_failed)}


def record_cycle(date: str, tickers: list, *, tail_of, rs_of, sector_of, max_corr_of,
                 eff: dict, regime: dict, goal: dict, limits: dict, bounds: dict,
                 book: dict, live_armed: list, version: int, explore_mode: bool = False,
                 write: bool = True, bars: dict | None = None, index_bars=None,
                 regime_ok: bool | None = None) -> list[dict] | None:
    """Bir EOD turu × tüm varyantlar → defter satırları. Dönüş: yazılan satırlar ya da None (kapalı).

    `tail_of`/`rs_of`/`sector_of`/`max_corr_of` ÇAĞRILABİLİRDİR ve canlı P2/P3'ten gelir: tarama
    dilimi, RS haritası, sektör ve korelasyon girdisi böylece TEK yerde (loop) tanımlı kalır ve gölge
    onların ikinci bir sürümünü tutmaz.

    `bars`/`index_bars`/`regime_ok` VERİLİRSE gölge-v2 YAŞAM-DÖNGÜSÜ motoru da AYNI kancadan koşar
    (`shadow_lifecycle.run_cycle`): fill → yönetim → çıkış → mark. Verilmezse v1 davranışı BİREBİR
    aynıdır — karar defteri yaşam-döngüsü motoruna bağımlı DEĞİLDİR ve onun arızası bu turu düşürmez.

    `write=False` testler için: satırlar üretilir, DEFTERE YAZILMAZ (canlı state'e yazan test yok)."""
    if not ENABLED:
        return None
    # KARDEŞ-PIT ÇAPASI — turu AÇAN tarih burada damgalanır ve `_judge` yalnız bu
    # tarihte takvimi konuşturur. Damga `_decide_variant` döngüsünden ve `_sl.run_cycle` (tohum
    # bacağı ONUN İÇİNDE koşar) çağrısından ÖNCE atılmalıdır; sırası bozulursa tohum seansları
    # kendilerini canlı sanar ve düzeltme sessizce geri alınır (yapısal test v185'te).
    _CANLI_TUR["date"] = str(date)
    bad = validate_knobs(bounds)
    if bad:
        # ÖLÇÜLEMEYEN ÖLÇÜLMEMİŞ KALIR: tanımsız/aralık-dışı düğmeyle koşmak, "fark yok" diyen sahte
        # bir kanıt üretirdi. Tur atlanır ve sebebi görünür olur.
        obs.warn("shadow_variants_knob_invalid", n=len(bad), detail=str(bad)[:200])
        return None

    tickers = sorted({str(t).upper() for t in tickers if t})
    bk = _book_state(book, limits, sector_of)
    as_of = barclock.now().isoformat()
    live = sorted({str(t).upper() for t in live_armed if t})
    rows, sigs_by_variant = [], {}
    for vid, spec in VARIANTS.items():
        try:
            res = _decide_variant(vid, spec, date, tickers, tail_of=tail_of, rs_of=rs_of,
                                  sector_of=sector_of, max_corr_of=max_corr_of, eff=eff,
                                  regime=regime, goal=goal, limits=limits, version=version, bk=bk)
        except Exception as e:
            # Bir varyantın arızası diğerlerini rehin ALMAZ; sessiz de kalmaz.
            obs.warn("shadow_variant_failed", variant=vid, error=f"{type(e).__name__}: {e}")
            continue
        # DEVİR ALANLARI DEFTERE GİRMEZ: yaşam-döngüsü motoru taramayı ikinci kez koşmasın diye
        # sinyaller/planlar buradan devredilir, ama satır şeması AYNEN korunur.
        sigs_by_variant[vid] = res.pop("_sigs", None)
        res.pop("_armed_plans", None)
        arm = set(res["would_arm"])
        row = {
            "date": date, "decision_as_of": as_of, "strategy_version": version,
            # ÇOKLU-KARŞILAŞTIRMA PAYDASI (k_probes kardeşi) — satırda taşınır, sonradan hatırlanmaz.
            "k_variants": len(VARIANTS),
            "authority": "paper_only", "regime": regime.get("regime"),
            "exposure_budget_pct": regime.get("exposure_budget_pct"),
            "explore_mode": bool(explore_mode),
            "flow_n": len(tickers),
            **res,
            # CANLI İLE KIYAS — defterin asıl sorusu: karar AYRIŞTI mı?
            "live_armed": live,
            "only_variant": sorted(arm - set(live)),
            "only_live": sorted(set(live) - arm),
            "shared_n": len(arm & set(live)),
            "book_as_of": {k: bk[k] for k in ("n_open", "open_risk_r", "size_mult", "max_open",
                                              "throttled_max_open", "equity", "peak_equity")},
            "gates_applied": list(GATES_APPLIED), "gates_skipped": dict(GATES_SKIPPED),
        }
        rows.append(row)
        if write:
            store.append_jsonl(LEDGER, row)
    if rows:
        obs.log("shadow_variants_cycle", date=date, variants=len(rows), flow_n=len(tickers),
                arm_n={r["variant"]: r["would_arm_n"] for r in rows},
                detail="GÖLGE VARYANT — kâğıt karar, emir/ship yolu YOK")
    if bars is not None:
        # GÖLGE-v2: aynı kanca, ayrı defter. Arızası KARAR defterini rehin ALMAZ (v1 deseni) — bu
        # satırlar düşerse yukarıdaki `rows` zaten diske yazıldı ve tur aynen tamamlanır.
        try:
            from . import shadow_lifecycle as _sl
            _sl.run_cycle(date, tickers=tickers, tail_of=tail_of, rs_of=rs_of, sector_of=sector_of,
                          max_corr_of=max_corr_of, eff=eff, regime=regime,
                          regime_ok=bool(regime_ok) if regime_ok is not None
                          else (regime.get("regime") in ("trend_up", "chop")
                                and (regime.get("exposure_budget_pct") or 0) > 0),
                          goal=goal, limits=limits, version=version, bars=bars,
                          index_bars=index_bars, sigs_by_variant=sigs_by_variant,
                          live_armed=live, write=write)
        except Exception as e:
            obs.warn("shadow_lifecycle_failed", error=f"{type(e).__name__}: {e}")
    return rows


# --- YASA 6 TÜKETİCİSİ: özet + CLI ---------------------------------------------------------------
def summarize(rows: list[dict], days: int = 10) -> dict:
    """Defterin ÖLÇÜMÜ — satırları ÇAĞIRAN okur (4b `summarize` ile aynı desen ve aynı gerekçe:
    kendi yazdığını kendi geri okuyan modül tüketici sayılmaz; okuma CLI'da/panoda yapılır)."""
    if not rows:
        return {"enabled": ENABLED, "variants": len(VARIANTS), "rows": 0, "days": 0,
                "per_variant": {}, "last_date": None, "dates": []}
    dates = sorted({r.get("date") for r in rows if r.get("date")})
    son = dates[-days:]
    per: dict = {}
    for r in rows:
        if r.get("date") not in son:
            continue
        vid = r.get("variant")
        p = per.setdefault(vid, {"label": r.get("label"), "knobs": r.get("knobs"), "days": 0,
                                 "signal_n": 0, "would_arm_n": 0, "only_variant_n": 0,
                                 "only_live_n": 0, "shared_n": 0, "scan_failed_n": 0,
                                 "earnings_olculemedi_n": 0})
        p["days"] += 1
        # KARDEŞ-PIT SAYACININ OKUYUCUSU (YASA 6): kaç karar, kazanç-karartma kapısı
        # KONUŞAMADAN alındı. Bu defter canlı turdan doğar, yani sayı 0 OLMALIDIR — 0'dan sapması
        # tohum satırlarının karar defterine sızdığını söyler ve `render_summary` onu bağırır.
        p["earnings_olculemedi_n"] += int((r.get("earnings_gate") or {}).get("olculemedi_seed") or 0)
        p["signal_n"] += int(r.get("signal_n") or 0)
        p["would_arm_n"] += int(r.get("would_arm_n") or 0)
        p["only_variant_n"] += len(r.get("only_variant") or [])
        p["only_live_n"] += len(r.get("only_live") or [])
        p["shared_n"] += int(r.get("shared_n") or 0)
        p["scan_failed_n"] += int(r.get("scan_failed_n") or 0)
    return {"enabled": ENABLED, "variants": len(VARIANTS), "rows": len(rows),
            "days": len(dates), "window_days": len(son), "dates": son,
            "last_date": dates[-1], "per_variant": per,
            "k_variants": len(VARIANTS), "gates_applied": list(GATES_APPLIED)}


def render_summary(rows: list[dict], days: int = 10) -> str:
    """`--ozet` metni. BOŞ DEFTER SAHTE BİR 'HER ŞEY YOLUNDA' GÖSTERMEZ — ne eksik olduğunu söyler."""
    s = summarize(rows, days)
    if not s["rows"]:
        return ("gölge-varyant defteri BOŞ (state/shadow_variants.jsonl).\n"
                f"Tanımlı varyant: {s['variants']} — ilk satırlar İLK EOD DÖNGÜSÜNDE doğar "
                "(loop.daily_cycle P3 kancası). Canlı worker koşuyorsa bu akşamın turunu bekler.\n"
                "Sandbox'ta denemek için: tests/test_sadelestirme_v123.py")
    out = [f"gölge-varyant defteri — {s['rows']} satır, {s['days']} gün "
           f"(son {s['window_days']} gün özetlendi; en son {s['last_date']})",
           f"  k_variants={s['k_variants']} (ÇOKLU-KARŞILAŞTIRMA PAYDASI — 'en iyi varyant' seçimi "
           f"bu sayıyla cezalandırılmalıdır)",
           f"  uygulanan kapılar: {', '.join(s['gates_applied'])}",
           "  varyant                                          gun sinyal silah  yalnizV yalnizCanli ortak"]
    for vid, p in sorted(s["per_variant"].items()):
        out.append(f"  {vid} {str(p['label'])[:44]:<44} {p['days']:>3} {p['signal_n']:>6} "
                   f"{p['would_arm_n']:>6} {p['only_variant_n']:>8} {p['only_live_n']:>11} "
                   f"{p['shared_n']:>5}")
        if p["scan_failed_n"]:
            out.append(f"      TARAMA HATASI: {p['scan_failed_n']} sembol (ölçülemeyen ölçülmemiş kaldı)")
        if p["earnings_olculemedi_n"]:
            out.append(f"      KAZANÇ KAPISI KONUŞMADI: {p['earnings_olculemedi_n']} karar "
                       "(tarihsel tarih — bugünün takvimi geçmiş karara UYGULANMAZ, kardeş-PIT)")
    out.append("  NOT: bu defterden ship yolu YOKTUR — canlıya geçiş yalnız OOS kapısından "
               "(prescreen/reflect) geçer.")
    return "\n".join(out)


# --- GÖLGE-v2 KARNESİ (YASA 6 tüketicisi: CLI + test; pano SONRAKİ tur) ---------------------------
# BU MODÜL, YAŞAM-DÖNGÜSÜ DEFTERİNİN DIŞ OKUYUCUSUDUR. Bilinçli bir ayrım: `shadow_lifecycle` YAZAR,
# burası OKUR. Kendi yazdığını kendi geri okuyan bir modül tüketici sayılmaz (4b'nin ve `codelaw`un
# aynı dersi) — okuma başka bir modülde olduğu için karne gerçek bir tüketicidir.
def summarize_books(books: dict, trades: list[dict], goal: dict, k_lifecycle: int | None = None) -> dict:
    """Varyant × {n_islem, ort_R, PF, para, maxDD, açık_poz} + KONTROL koluna (V5) göre fark.

    PARA SÜTUNU `shadowlaw.ret_c_v3`TİR — kapının PARA-v3 altında okuduğu TEK terimin ta kendisi
    (probgate ile aynı ölçek). İkinci bir para tanımı yazmak, karneyi kapıdan ayrıştırırdı; o zaman
    "gölgede iyi görünen kol" ile "kapıdan geçebilecek kol" farklı sayılara bakardı.

    ÖLÇÜLEMEYEN None'DIR, 0.0 DEĞİL: işlem yoksa ort_R yok; zarar eden işlem yoksa PF tanımsız
    (bölme sıfıra); eğri iki noktadan kısaysa süre yok, dolayısıyla para yok. Bir sayı uydurmak,
    henüz kanıt üretmemiş bir kolu "vasat ama ölçülmüş" gibi göstermek olurdu."""
    from . import score as _score, shadowlaw as _law
    per: dict = {}
    for vid, bk in sorted(books.items()):
        tr = [t for t in trades if t.get("variant") == vid]
        rs = [float(t.get("r_multiple") or 0.0) for t in tr]
        wins = sum(float(t.get("pnl_dollars") or 0.0) for t in tr
                   if float(t.get("pnl_dollars") or 0.0) > 0)
        loss = -sum(float(t.get("pnl_dollars") or 0.0) for t in tr
                    if float(t.get("pnl_dollars") or 0.0) < 0)
        curve = [float(e) for _, e in (bk.get("equity_curve") or [])]
        dates = [str(dd) for dd, _ in (bk.get("equity_curve") or [])]
        para, span = None, None
        if len(curve) >= 2 and curve[0] > 0:
            try:
                import datetime as _dt
                span = max(1.0, (_dt.date.fromisoformat(dates[-1])
                                 - _dt.date.fromisoformat(dates[0])).days)
                para = round(_law.ret_c_v3(curve[-1] / curve[0] - 1.0, span), 4)
            except (TypeError, ValueError) as e:
                # SESSİZ DEĞİL: süre para teriminin PAYDASIDIR; biçimsiz bir tarih onu sessizce
                # kaydırırsa karne yanlış bir kolu öne çıkarır. Ölçülemeyen ölçülmemiş kalır.
                obs.warn("shadow_karne_span_unmeasurable", variant=vid,
                         error=f"{type(e).__name__}: {e}")
        per[vid] = {
            "label": (arms_label(vid) or bk.get("variant")),
            "n_islem": len(tr), "n_tohum": sum(1 for t in tr if t.get("seeded")),
            "ort_R": round(sum(rs) / len(rs), 3) if rs else None,
            "PF": round(wins / loss, 3) if loss > 0 else None,
            "para": para, "span_days": span,
            "maxDD": round(_score.max_drawdown(curve), 4) if len(curve) >= 2 else None,
            "acik_poz": len(bk.get("positions") or {}),
            "equity": round(curve[-1], 2) if curve else None,
            "last_date": bk.get("last_date"),
        }
    ctrl = per.get("V5") or {}
    for vid, p in per.items():
        for alan in ("para", "ort_R"):
            a, c = p.get(alan), ctrl.get(alan)
            p[f"{alan}_delta"] = round(a - c, 4) if (a is not None and c is not None) else None
    return {"k_lifecycle": int(k_lifecycle or len(per)), "arms": len(per), "per_variant": per,
            "trades": len(trades), "seeded": sum(1 for t in trades if t.get("seeded")),
            # goal anahtarı düşerse bu yedek konuşur; goal'daki değerle EŞİT tutulur (envanter
            # #16, 2026-08-22; latent 20≠30 ayrıklığı burada kapatıldı — v239 test_8a çivisi).
            "min_sample": int(goal.get("min_sample", 30))}


def arms_label(vid: str) -> str | None:
    """Kol etiketi — v1 kolları burada, yaşam-döngüsü kolları `shadow_lifecycle`ta tanımlı."""
    if vid in VARIANTS:
        return VARIANTS[vid]["label"]
    from . import shadow_lifecycle as _sl
    spec = _sl.LIFECYCLE_ONLY.get(vid)
    return spec["label"] if spec else None


def render_karne(books: dict, trades: list[dict], goal: dict, k_lifecycle: int | None = None) -> str:
    """`--karne` metni. BOŞ DEFTER SAHTE BİR 'HER ŞEY YOLUNDA' GÖSTERMEZ."""
    s = summarize_books(books, trades, goal, k_lifecycle)
    if not s["per_variant"]:
        return ("gölge-v2 kitapları BOŞ.\n"
                "İlk kitap İLK EOD DÖNGÜSÜNDE doğar (loop.daily_cycle kancası → "
                "shadow_lifecycle.run_cycle) ve o turda son 5 seans TOHUMLANIR (N00005).\n"
                "Sandbox'ta denemek için: tests/test_golge_v2_yasam_dongusu_v132.py")
    ms = s["min_sample"]
    out = [f"gölge-v2 KARNESİ — {s['arms']} kol, {s['trades']} kapanan işlem "
           f"({s['seeded']} tohum), k_lifecycle={s['k_lifecycle']}",
           f"  k_lifecycle ÇOKLU-KARŞILAŞTIRMA PAYDASIDIR (karar defterinin k_variants'ından AYRI: "
           f"orada kollar karar-özdeş, burada kitapları ayrışıyor)",
           f"  para = shadowlaw.ret_c_v3 (PARA-v3, kapının okuduğu TEK terim) · "
           f"min_sample={ms} altındaki kol bir SONUÇ değil bir BAŞLANGIÇTIR",
           "  kol  islem tohum   ortR      PF    para  dParaV5   maxDD  acik  etiket"]
    for vid, p in sorted(s["per_variant"].items()):
        def _f2(x, w=7, nd=3):
            """Karne hücresi biçimlendirici: None ise sağa yaslı `n/a`, değilse `w` genişlikte `nd` ondalıklı sayı.
            Ölçülemeyen değer sıfır gibi gösterilmez."""
            return f"{'   n/a':>{w}}" if x is None else f"{x:>{w}.{nd}f}"
        out.append(f"  {vid:<4} {p['n_islem']:>5} {p['n_tohum']:>5} {_f2(p['ort_R'])} "
                   f"{_f2(p['PF'])} {_f2(p['para'], 7, 4)} {_f2(p['para_delta'], 8, 4)} "
                   f"{_f2(p['maxDD'], 7, 4)} {p['acik_poz']:>5}  {str(p['label'])[:38]}")
        if p["n_islem"] < ms:
            out.append(f"       ÖRNEKLEM YETERSİZ: {p['n_islem']}/{ms} — bu satır bir kanıt DEĞİL, "
                       "bir birikim göstergesidir")
    out.append("  NOT: bu kitaplardan ship yolu YOKTUR — canlıya geçiş yalnız OOS kapısından "
               "(prescreen/reflect) geçer.")
    return "\n".join(out)


def _load_books() -> tuple[dict, list, int]:
    """Yaşam-döngüsü defterlerini DIŞARIDAN oku (yazan modül `shadow_lifecycle`)."""
    from . import shadow_lifecycle as _sl
    doc = store.read_json(_sl.BOOKS_FILE, None) or {}
    return (doc.get("variants") or {}), store.read_jsonl(_sl.TRADES_FILE), doc.get("k_lifecycle")


def main(argv: list[str] | None = None) -> int:
    """CLI girişi: `--varyantlar` tanımlı kolları, `--karne` gölge-v2 kitap karnesini, aksi hâlde karar
    defteri özetini yazar (`--json` ile makine okunur). Yalnız RAPORLAR — hiçbir defteri değiştirmez,
    canlıya ship yolu yoktur. Dönüş: çıkış kodu."""
    import argparse
    import json
    from . import config as _config
    p = argparse.ArgumentParser(prog="python -m meridian.shadow_variants",
                                description="2.4 gölge-varyant portföyleri — kâğıt karar defteri "
                                            "+ gölge-v2 yaşam-döngüsü karnesi (SIFIR yetki; ship yolu yok)")
    p.add_argument("--ozet", action="store_true", help="karar defteri özetini yaz ve çık")
    p.add_argument("--karne", action="store_true", help="gölge-v2 kitap karnesini yaz ve çık")
    p.add_argument("--gun", type=int, default=10, metavar="N", help="--ozet: son N günü özetle")
    p.add_argument("--varyantlar", action="store_true", help="tanımlı varyantları listele ve çık")
    p.add_argument("--json", action="store_true", help="çıktıyı JSON olarak ver")
    a = p.parse_args(argv)
    if a.varyantlar:
        from . import shadow_lifecycle as _sl
        for vid, spec in _sl.arms().items():
            kol = "karar+kitap" if vid in VARIANTS else "yalnız KİTAP (yaşam-döngüsü kolu)"
            print(f"{vid}  {spec['label']}  [{kol}]\n     {spec['knobs'] or '(kontrol — düğme yok)'}")
        print(f"\nk_variants={len(VARIANTS)} (karar) · k_lifecycle={len(_sl.arms())} (kitap) · "
              f"uygulanan kapılar: {', '.join(GATES_APPLIED)}")
        for k, v in GATES_SKIPPED.items():
            print(f"UYGULANMAYAN {k}: {v}")
        return 0
    if a.karne:
        books, trades, k = _load_books()
        if a.json:
            print(json.dumps(summarize_books(books, trades, _config.goal(), k), indent=1,
                             ensure_ascii=False))
        else:
            print(render_karne(books, trades, _config.goal(), k))
        return 0
    rows = store.read_jsonl(LEDGER)
    if a.json:
        print(json.dumps(summarize(rows, a.gun), indent=1, ensure_ascii=False))
    else:
        print(render_summary(rows, a.gun))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
