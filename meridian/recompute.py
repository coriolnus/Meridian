"""recompute.py — AYNI SORUYU İKİ YOLDAN CEVAPLA (2026-07-22).

NEDEN VAR: 2026-07-21'de çıkan on üç hatanın hiçbiri istisna fırlatmadı. Hepsi aynı biçimde
davrandı — bir satır sessizce elendi, bir sayı küçüldü, kimse fark etmedi. Böyle bir hatayı
yakalayan tek şey, **aynı büyüklüğü birbirinden BAĞIMSIZ iki yoldan hesaplayıp karşılaştırmaktı**:
canlı döngü "aday: 0" diyordu, aynı önbellek barları doğrudan tarandığında 25 seansta 43 sinyal
çıkıyordu. Fark, hatanın kendisiydi (motor evrenin %18'inde karar veriyordu).

TASARIM KURALI (ihlal edilirse modül değersizleşir): iki yol GERÇEKTEN bağımsız olmalı. Aynı
fonksiyonu iki kez çağırmak hiçbir şey kanıtlamaz; sayıyı üreten muhasebe ile sayıyı taşıyan
defteri karşılaştırmak kanıtlar. Her denetim aşağıda "A yolu" ve "B yolu" diye açıkça yazılır.

Modül KARAR VERMEZ, düzeltmez, hiçbir şey yazmaz — yalnız "iki cevap tutmuyor" der.
"""
from __future__ import annotations

import ast

from . import store

# Kayan nokta ve komisyon yuvarlamaları için tolerans. Mutlak eşik $1: bunun altındaki fark
# muhasebe gürültüsüdür; üstü, kayıp/çift sayılmış işlem demektir.
MONEY_TOL = 1.0


def _start_equity() -> float:
    """Başlangıç sermayesi TEK kaynaktan okunur (score.START_EQUITY) — burada sabit yazmak,
    bu denetimin bulduğu 'aynı yasanın iki uygulaması' hatasının kendisi olurdu."""
    from .score import START_EQUITY
    return float(START_EQUITY)


def _f(x, d=0.0) -> float:
    try:
        return float(x)
    except (TypeError, ValueError):  # sessiz-yutma: biçimsiz/eksik tek alan; yalnız bu değer düşer, satır başına uyarı asıl sinyali log seline gömerdi
        return d


def _row(check: str, ok: bool, a, b, detail: str, a_yol: str, b_yol: str) -> dict:
    return {"check": check, "ok": bool(ok), "a": a, "b": b, "detail": detail,
            "a_yol": a_yol, "b_yol": b_yol}


_CORPUS_CACHE: dict = {}
# Orphan taramasının KÖK+dizin kesiti için kaynak metni (K1, 2026-07-30). `codelaw.artifact_graph`
# yalnız `store.*` çağrılarını ve .json/.jsonl adlarını çözer; yaml/csv/log/dizin artefaktları o
# grafın DIŞINDA. Bir adın gerçekten okuyucusuz olduğunu kanıtlamanın ucuz ve dürüst yolu:
# kaynak+betik ağacında adını aramak (denetimin kendi yöntemi).
# TESTLER KORPUSA GİRMEZ — bu bir tercih değil, denetimin KENDİ ölçütü (K1, 2026-07-30).
# Bu turun en önemli bulgusu şuydu: `crosscheck_report()`in tek çağıranı testlerdi ve bu
# "HİÇ OKUNMUYOR" sayıldı — haklı olarak, çünkü bir test üretim tüketicisi DEĞİLDİR. Korpusa
# tests/ dâhil edilirse dedektör kendi ölçütünü ihlal eder: yalnız testte adı geçen bir artefakt
# "okunuyor" görünür ve üretimdeki yetimliği gizlenir.
# CANLI OLARAK YAKALANDI: bu turda yazılan v122 testi sahte bir orphan kurmak için `server.log`
# adını string olarak içeriyordu ve tests/ korpusta olduğu sürece o ad ÜRETİMDE de bağışık hâle
# geliyordu — yani testin varlığı dedektörü kör ediyordu.
# ops/ ve deploy/ DÂHİLDİR: onlar gerçek işletim tüketicileridir (betikler dosyaları okur/taşır).
_CORPUS_GLOBS = (("meridian", "*.py"), ("ops", "*"), ("deploy", "*"), ("skills", "*.md"))


def _source_corpus() -> str:
    """meridian/ + tests/ + ops/ + deploy/ + skills/ metinlerinin TEK dizgesi (mtime önbellekli).

    Boş dönerse çağıran hiçbir orphan iddiası KURMAZ: tarama yapılamadıysa "okuyucusu yok" demek,
    körlüğü bulguya çevirmek olurdu."""
    import pathlib
    root = pathlib.Path(__file__).resolve().parent.parent
    try:
        files = [p for sub, pat in _CORPUS_GLOBS for p in (root / sub).rglob(pat) if p.is_file()]
        stamp = (len(files), max((p.stat().st_mtime_ns for p in files), default=0))
    except OSError:  # sessiz-yutma: kaynak ağacı listelenemiyorsa iddia KURULAMAZ — boş korpus çağıranı susturur (aşağıdaki `bool(_src_text)` kapısı)
        return ""
    if _CORPUS_CACHE.get("stamp") == stamp:
        return _CORPUS_CACHE["text"]
    parts = []
    for p in files:
        try:
            parts.append(_code_only(p))
        except OSError:  # sessiz-yutma: tek dosya okunamadı; korpus eksik kalır ve eksik korpus yalnız DAHA AZ bulgu üretir (yanlış pozitif ÜRETMEZ)
            continue
    text = "\n".join(parts)
    _CORPUS_CACHE.update({"stamp": stamp, "text": text})
    return text


def _code_only(p) -> str:
    """Dosyanın YALNIZ KOD kısmı: yorumlar ve docstring'ler ATILIR (K1, 2026-07-30).

    NEDEN — BU DEDEKTÖR YAZILIRKEN CANLI OLARAK YAKALANDI: korpus ham metin olarak kurulunca
    dedektör sessizce kör kaldı, çünkü aradığı dosya adlarını bu modülün KENDİ açıklama yorumları
    ve docstring'i içeriyordu. Yani bir bulgunun gerekçesini yazmak, bulgunun kendisini yok
    ediyordu — kuyruğunu yiyen bir dedektör. İki tur denendi (önce `#` şeridi, sonra docstring) ve
    ikisi de aynı dersi verdi: `test_c7`nin hükmü burada da geçerli — "Yorum ve düzyazı yetki
    değildir". Bir dosyayı OKUMAK kod gerektirir; adını anmak okumak değildir.

    .py için AST kullanılır: `ast` yorumları hiç taşımaz, docstring'ler ayrıca düşürülür ve kalan
    ağaç yeniden metne çevrilir — yani geride SADECE gerçek kod (dizge sabitleri dâhil) kalır.
    Ayrıştırılamayan dosya ham metne düşer: körlük, yanlış pozitiften iyidir."""
    src = p.read_text(errors="ignore")
    if p.suffix != ".py":
        return "\n".join(ln.split("#", 1)[0] for ln in src.splitlines())
    try:
        tree = ast.parse(src)
    except SyntaxError:  # sessiz-yutma: ayrıştırılamayan modül ham metne düşer — bu yalnız DAHA AZ bulgu üretir (referans fazla görünür), yanlış pozitif üretmez
        return src
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        body = getattr(node, "body", None)
        if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) \
                and isinstance(body[0].value.value, str):
            body.pop(0)
            if not body:                      # gövdesi yalnız docstring'den oluşan tanım
                body.append(ast.Pass())
    try:
        return ast.unparse(tree)
    except Exception:  # sessiz-yutma: unparse edilemeyen ağaç ham metne düşer — bkz. yukarıdaki aynı gerekçe (körlük < yanlış pozitif)
        return src


def report(deep: bool = False) -> dict:
    """Her satır: aynı büyüklüğün iki bağımsız hesabı + tutuyor mu.

    deep=True, önbellek barlarını okuyup evren kapsamasını YENİDEN hesaplar (pahalı; gece işi).
    """
    rows: list[dict] = []
    pf = store.read_json("portfolio.json", {}) or {}
    trades = store.read_jsonl("trades.jsonl")

    # 0) DEFTER ↔ BAR TUTARLILIĞI (2026-07-23). Kanıt: 21:15'te `bar_history_rewritten` +
    #    `corporate_action_cache_reset` ateşledi (GE HealthCare spin-off düzeltmesi) ve GE'nin
    #    Ocak 2023 barları 63$ bandından 78$ bandına taşındı. Ama 17:48'de o barlardan TÜRETİLMİŞ
    #    işlem defteri olduğu gibi kaldı: T00005 girişi 63.16, aynı günün bar açılışı 78.55.
    #    Hiçbir dedektör görmedi — tutarlılık dedektörü bayatlığı DOSYA ZAMANIYLA ölçer ve
    #    "barlar → trades.jsonl" kenarı o haritada hiç yoktu. Barlar altından değişince her
    #    R-katı, her skor sessizce başka bir dünyaya ait olur.
    #    A yolu: defterin kaydettiği giriş fiyatı.  B yolu: o günün barından OKUNAN açılış.
    if trades:
        sapan, karsilastirilan = [], 0
        for t in trades[-400:]:                      # tavan: pano yolu; gece işi tamamını görür
            tk, d0, e = t.get("ticker"), str(t.get("ts_open") or ""), t.get("entry")
            if not (tk and len(d0) == 10 and e):
                continue
            try:
                from .adapters import data as _dt
                # YALNIZ ÖNBELLEK: soru "motorun KULLANDIĞI barlar defterle tutuyor mu" — ağdaki taze
                # veri değil. Cache dosyası yoksa ATLA, ASLA ağa düşme. Bu hem doğru (motor cache'ten
                # okur) hem de mutation harness'ın sentetik ortamında gerçek AAPL barını çekip sahte
                # entry'yle karşılaştırıp yanlış-pozitif üretmesini önler (2026-07-23).
                if not _dt._cache_path(tk).exists():
                    continue
                bars = _dt.load_bars(tk, d0, d0, use_cache=True)
            except Exception:  # sessiz-yutma: tek sembolün barı okunamadı; bu satır KARŞILAŞTIRILMAMIŞ sayılır ve paydaya girmez — sessizce "uyumlu" saymak yasağın ta kendisi olurdu
                continue
            if bars is None or not len(bars):
                continue
            karsilastirilan += 1
            o = _f(bars.iloc[0]["open"])
            if o > 0 and abs(o - _f(e)) / o > 0.005:
                sapan.append({"id": t.get("id"), "ticker": tk, "date": d0,
                              "defter": round(_f(e), 2), "bar": round(o, 2)})
        if karsilastirilan:
            # BİLİNEN, TEŞHİS EDİLMİŞ SAPMA (2026-07-23): T00005/GE bir HAYALET işlemdir. GE
            # HealthCare spin-off'u (2023-01) barları geriye düzeltince eski bölünme-öncesi fiyattan
            # (63$) doğmuş bu işlem, düzeltilmiş barlarda (78$) kurulumu artık ateşlemediği için
            # motorun yeniden oynatmasında HİÇ üretilmiyor (salt-okunur probe: 95 işlem, GE 0).
            # Doğru düzeltme onu ÇIKARMAKtır (96→95); operatör bunu bir sonraki tam re-seed'e
            # erteledi. Kırmızı KALMALI ama artık "hesaplanamadı" gibi değil, teşhisiyle konuşuyor.
            bilinen = [s for s in sapan if s["id"] == "T00005" and s["ticker"] == "GE"]
            kalan = [s for s in sapan if s not in bilinen]
            detay = (f"{karsilastirilan} işlemin girişi kendi barının açılışıyla birebir"
                     if not sapan else
                     f"{karsilastirilan} işlemin {len(sapan)} tanesi kendi barından SAPIYOR — "
                     + ", ".join(f"{s['id']}/{s['ticker']} defter {s['defter']} ≠ bar {s['bar']}"
                                 for s in sapan[:4]))
            if bilinen and not kalan:
                detay += ("  · BİLİNEN HAYALET: GE HealthCare spin-off düzeltmesi; işlem yeniden "
                          "oynatmada üretilmiyor, bir sonraki re-seed'de düşecek (operatör kararı)")
            rows.append(_row("ledger_matches_bars", not sapan,
                             karsilastirilan - len(sapan), karsilastirilan, detay,
                             "trades.jsonl `entry` alanı", "adapters.data.load_bars açılışı"))

    # 1) GERÇEKLEŞEN K/Z — broker'ın koşan muhasebesi ile işlem defterinin toplamı
    #    A: broker her kapanışta portfolio.realized_pnl'i artırır (durum makinesi)
    #    B: trades.jsonl satırlarındaki pnl_dollars toplamı (defter)
    #    Ayrışma = kaybolmuş ya da iki kez sayılmış işlem. Hiçbir istisna fırlatmaz.
    if trades:
        a = _f(pf.get("realized_pnl"))
        b = sum(_f(t.get("pnl_dollars")) for t in trades)
        rows.append(_row("realized_pnl", abs(a - b) <= MONEY_TOL, round(a, 2), round(b, 2),
                         f"broker muhasebesi {a:,.2f}$ · defter toplamı {b:,.2f}$"
                         + ("" if abs(a - b) <= MONEY_TOL
                            else f" — {abs(a-b):,.2f}$ AYRIŞMA: işlem kaybolmuş ya da çift sayılmış"),
                         "portfolio.realized_pnl", "Σ trades.pnl_dollars"))

    # 2) NAKİT — pozisyon yokken nakit, başlangıç sermayesi + gerçekleşen K/Z olmak ZORUNDA
    #    A: broker'ın nakit hesabı   B: sermaye kimliği (başlangıç + gerçekleşen)
    if trades and not (pf.get("positions") or {}):
        a = _f(pf.get("cash"))
        b = _start_equity() + sum(_f(t.get("pnl_dollars")) for t in trades)
        rows.append(_row("cash_identity", abs(a - b) <= MONEY_TOL, round(a, 2), round(b, 2),
                         f"nakit {a:,.2f}$ · kimlik {b:,.2f}$ (açık pozisyon yok)"
                         + ("" if abs(a - b) <= MONEY_TOL else " — sermaye kimliği BOZUK"),
                         "portfolio.cash", "başlangıç + Σ pnl_dollars"))

    # 3) SERMAYE EĞRİSİ ↔ KİTAP — eğrinin son noktası kitabın söylediği sermaye mi?
    #    A: equity_curve.json son nokta   B: nakit + açık pozisyonların maliyeti
    eq = (store.read_json("equity_curve.json", {}) or {}).get("points") or []
    if eq and not (pf.get("positions") or {}):
        a = _f(eq[-1][1]) if isinstance(eq[-1], (list, tuple)) and len(eq[-1]) > 1 else None
        b = _f(pf.get("cash"))
        if a is not None:
            rows.append(_row("equity_curve_tail", abs(a - b) <= MONEY_TOL, round(a, 2), round(b, 2),
                             f"eğri sonu {a:,.2f}$ · kitap nakdi {b:,.2f}$"
                             + ("" if abs(a - b) <= MONEY_TOL
                                else " — panoda gösterilen eğri kitabı temsil ETMİYOR"),
                             "equity_curve.json[-1]", "portfolio.cash"))

    # 4) KARNE ↔ DEFTER — karnedeki işlem sayısı defterin uzunluğuna eşit mi?
    #    Karne, terfi/geri-alma kararlarının dayanağı: yanlış n, yanlış skor demektir.
    sb = store.read_json("scoreboard.json", {}) or {}
    cur = str(sb.get("current_version") or "")
    v = (sb.get("versions") or {}).get(cur) or {}
    if v.get("n_trades") is not None and trades:
        a, b = int(v["n_trades"]), len(trades)
        rows.append(_row("scoreboard_n_trades", a == b, a, b,
                         f"karne n={a} · defter n={b}"
                         + ("" if a == b else " — karne skoru YANLIŞ örneklem üzerinde hesaplanmış"),
                         f"scoreboard.versions[{cur}].n_trades", "len(trades.jsonl)"))

    # 5) KARŞI-OLGUSAL KORUNUMU — açık ve çözülmüş kümeler kesişemez, kimlik tekrarlanamaz
    #    A: cf_open.json kimlikleri   B: counterfactuals.jsonl kimlikleri
    #    Kesişim = aynı kanıtın iki kez sayılması (backfill yeniden koşarsa tam bu olur).
    open_ids = [str(r.get("id")) for r in (store.read_json("cf_open.json", []) or []) if r.get("id")]
    res_ids = [str(r.get("id")) for r in store.read_jsonl("counterfactuals.jsonl") if r.get("id")]
    if res_ids:
        both = set(open_ids) & set(res_ids)
        dup = len(res_ids) - len(set(res_ids))
        rows.append(_row("cf_conservation", not both and not dup, len(open_ids), len(res_ids),
                         f"açık {len(open_ids)} · çözülmüş {len(res_ids)} (tekil {len(set(res_ids))})"
                         + ("" if not both and not dup
                            else f" — {len(both)} kimlik İKİ kümede, {dup} tekrarlı satır: kanıt çift sayılıyor"),
                         "cf_open.json", "counterfactuals.jsonl"))

    # 6) KALİBRASYON PAYDASI — tüketici kaç satır GÖRDÜĞÜNÜ söylüyor, kaynakta kaç satır VAR?
    #    "gerçek 0 / simüle 241" hatası tam buradaydı: tüketici sessizce eliyordu, paydası küçülüyordu
    #    ve dışarıdan bakan bunu "veri yok" sanıyordu. A: kalibrasyonun beyan ettiği n. B: kaynağın
    #    kendisi baştan sayıldı.
    sc = store.read_json("score_calibration.json", None)
    if sc:
        # near-miss satırları BİLEREK dışarıda: eşik-altı gölge adaylar seçilim kalitesini ölçmez,
        # onları paydaya katmak dedektöre her turda sahte "%70 eleme" dedirtirdi. Dedektör
        # tüketicinin MEŞRU dışlamasını aynalar; aynalamazsa kurt masalı anlatır ve operatör
        # kırmızıyı yok saymayı öğrenir — o noktadan sonra gerçek ihlal de görünmez.
        entered = sum(1 for r in store.read_jsonl("counterfactuals.jsonl")
                      if r.get("entered") and r.get("r_multiple") is not None
                      and not r.get("near_miss"))
        a, b = int(_f(sc.get("n_cf"))), entered
        # Tüketici meşru sebeplerle daha az satır kullanabilir (ör. skoru olmayan). Ama %5'ten fazla
        # kayıp, "sessiz eleme" demektir ve NEDENİ yazılmalıdır (bkz. meridian/sieve.py).
        ok = b == 0 or a >= b * 0.95
        rows.append(_row("calibration_denominator", ok, a, b,
                         f"kalibrasyon n_cf={a} · kaynakta uygun satır={b}"
                         + ("" if ok else f" — {b-a} satır SESSİZCE elenmiş (%{100*(b-a)/max(b,1):.0f})"),
                         "score_calibration.n_cf", "counterfactuals.jsonl yeniden sayım"))
        n_real = int(_f(sc.get("n_real")))
        closed_real = sum(1 for t in trades if t.get("r_multiple") is not None)
        ok2 = closed_real == 0 or n_real >= closed_real * 0.95
        rows.append(_row("calibration_real_denominator", ok2, n_real, closed_real,
                         f"kalibrasyon n_real={n_real} · kapanmış gerçek işlem={closed_real}"
                         + ("" if ok2 else " — GERÇEK işlemler kalibrasyona girmiyor"),
                         "score_calibration.n_real", "trades.jsonl yeniden sayım"))

    # 7) HİPOTEZ KİMLİĞİ — kimlik asla yeniden kullanılmaz: en büyük kimlik ≥ satır sayısı
    #    A: defterdeki en büyük numara   B: satır sayısı. A < B ise numara geri sarmış demektir
    #    (canlıda wf_rev sayacında tam bu geri sarma görüldü: 4→1).
    hyp = store.read_jsonl("hypotheses.jsonl")
    if hyp:
        nums = [int(str(h.get("id", "H0"))[1:]) for h in hyp if str(h.get("id", "")).startswith("H")
                and str(h.get("id"))[1:].isdigit()]
        if nums:
            a, b = max(nums), len(hyp)
            uniq = len(set(nums))
            rows.append(_row("hypothesis_ids", a >= b and uniq == len(nums), a, b,
                             f"en büyük kimlik H{a:05d} · satır {b} · tekil {uniq}"
                             + ("" if a >= b and uniq == len(nums)
                                else " — kimlik GERİ SARMIŞ ya da tekrar kullanılmış: geçmiş üzerine yazılıyor"),
                             "max(id)", "len(hypotheses.jsonl)"))

    # 7) DEĞER MAKULLÜĞÜ — alan VAR ama içi anlamsızsa sözleşme "uyumlu" der, tüketici boş döner.
    #    (a) rejim etiketi: canlıda cf satırlarının %70'i "?" taşıyordu ve rejim bazlı HER dilimleme
    #        boşa düşüyordu; alan mevcut olduğu için hiçbir şema denetimi bunu göremiyordu.
    cf_rows = store.read_jsonl("counterfactuals.jsonl", limit=4000)
    if len(cf_rows) >= 20:
        unknown = sum(1 for r in cf_rows if str(r.get("regime") or "?") == "?")
        frac = unknown / len(cf_rows)
        rows.append(_row("regime_label_quality", frac <= 0.20,
                         f"%{100*frac:.0f} bilinmiyor", f"{len(cf_rows)-unknown}/{len(cf_rows)} etiketli",
                         f"kanıt satırlarının %{100*frac:.0f}'i rejimsiz"
                         + ("" if frac <= 0.20 else " — rejim bazlı her dilimleme ve `knob@rejim` "
                                                    "önerisi bu satırları GÖRMÜYOR"),
                         "counterfactuals.jsonl regime alanı", "VALID_REGIMES sayımı"))

    #    (b) plan risk boyutu bounds tavanının içinde mi? Sözleşme alanın VARLIĞINI denetler, DEĞERİNİ
    #        değil: bounds.yaml operatörün yazılı sınırıdır ve hiçbir defter satırı onu aşamaz.
    try:
        from . import config as _cfg
        lim = (_cfg.bounds() or {}).get("position_size_r") or {}
        lo, hi = lim.get("min"), lim.get("max")
        plans = [p for p in store.read_jsonl("trade_plans.jsonl") if p.get("size_r") is not None]
        if plans and lo is not None and hi is not None:
            bad = [p for p in plans if not (float(lo) <= float(p["size_r"]) <= float(hi))]
            worst = max((float(p["size_r"]) for p in bad), default=None)
            rows.append(_row("bounds_respected", not bad, len(bad), f"[{lo}, {hi}]",
                             f"{len(bad)}/{len(plans)} plan risk boyutu sınırların dışında"
                             + ("" if not bad else f" (en uç {worst}) — operatörün YAZILI sınırı aşılmış"),
                             "trade_plans.size_r", "bounds.yaml position_size_r"))
    except Exception as e:
        from . import obs
        obs.warn("bounds_recompute_failed", error=f"{type(e).__name__}: {e}")

    # 8) (deep) EVREN KAPSAMASI YENİDEN HESABI — bulunan asıl hatanın doğrudan dedektörü.
    #    A: döngünün işlediğini söylediği seans   B: önbellek barlarından yeniden hesaplanan kapsama
    if deep:
        rows.append(_universe_recompute())
    rows.append(_orphan_state_files())      # ucuz (dizin listesi + statik graf); her turda sorulur
    return {"rows": rows, "ok": all(r["ok"] for r in rows), "n": len(rows)}


def _orphan_state_files() -> dict:
    """Diskteki her defter/artefaktın bir OKUYUCUSU var mı? Statik `artifact_graph` yalnız kodda
    YAZILAN adları görür; bir mekanizma çalışma anında hiç kimsenin okumadığı bir dosya üretirse
    (2026-07-22 mutasyon koşumu: `phantom_metrics.jsonl`) statik tarama onu göremez. Bu dedektör
    diskten gerçek dosya listesini alıp kaynaktaki okuyucularla ve beyan edilmiş kanallarla
    çapraz kontrol eder — 'üretilip tüketilmeyen kanıt' sınıfının çalışma-anı dedektörü."""
    from . import config
    try:
        from . import codelaw as _cl
        from . import ledgers as _lg
        g = _cl.artifact_graph()
        arts = g.get("artifacts") or {}
        sinks = set(getattr(_cl, "DECLARED_SINKS", {}))
        contracts = set(_lg.CONTRACTS)
        # kaynakta OKUNAN her ad (readers boş olsa da yazılıp okunuyorsa güvenli)
        read_names = {a for a, info in arts.items() if info.get("readers")}
        # `store.*` DIŞINDAN okunan dosyalar statik grafta görünmez ama gerçek tüketicileri vardır:
        # secrets.py kendi dosya erişimini kullanır. Bunları orphan saymak yanlış pozitif olurdu.
        accessor_read = {"secrets.json"}
        known = read_names | sinks | contracts | accessor_read
        # SQLite GEÇİŞİNİN İKİ YANLIŞ-POZİTİF SINIFI (WP-H/H9, 2026-07-31) — BEYAZ LİSTE DEĞİL,
        # TÜRETME. İkisi de bu dedektörün "okuyucusu yok" testinden kendiliğinden geçemez ama
        # ikisinin de kökeni BİLİNEN bir artefakttır; elle bir liste tutmak, hemen aşağıda
        # (K1 bloğunda) reddedilen hastalığın ta kendisi olurdu:
        #   (a) `<defter>.migrated` — `dbmigrate` taşıma sonrası kaynak dosyayı SİLMEZ, adını
        #       değiştirir. Arşivin okuyucusu yoktur ÇÜNKÜ arşiv olması istenmiştir (geri dönüş
        #       yolu). Kökü (`trades.jsonl`) `known` içindeyse arşiv de bilinir.
        #   (b) `meridian.db-wal` / `-shm` — SQLite'ın KENDİ yan dosyaları. Adları kaynakta
        #       geçmez ve geçmemelidir; `meridian.db` geçer. Yan dosya, ana dosyanın parçasıdır.
        from . import storage as _sg
        _db_yan = {f"{_sg.DB_NAME}{s}" for s in ("", "-wal", "-shm", "-journal")}
        known = known | _db_yan | {f"{n}.migrated" for n in known}
        orphans = []
        for f in config.STATE.glob("*.json*"):
            nm = f.name
            if nm in known:
                continue
            # boş dosya orphan sayılmaz (henüz üretilmemiş); dolu ve okuyucusuz ise bulgudur
            try:
                if f.stat().st_size <= 4:
                    continue
            except OSError:  # sessiz-yutma: dosya stat edilemiyorsa (yarış/silinme) orphan iddiası KURULAMAZ — atlamak dürüst, uydurma bulgu üretmekten iyidir
                continue
            orphans.append(nm)

        # ---- KÖR KESİT KAPATILDI: KÖK + .json* OLMAYAN ARTEFAKTLAR (K1, 2026-07-30) ----------
        # Tarama `config.STATE.glob("*.json*")` idi; yani üç şeyi HİÇ göremiyordu: (1) depo
        # KÖKÜNDEKİ artefaktlar, (2) `.log`/`.csv` gibi başka uzantılar, (3) DİZİNLER. Canlı
        # kanıt: kökteki `provenance_report.json` 8 gün bayat + sıfır referanslı duruyordu,
        # `state/server.log` 14 Temmuz'dan donuktu (aktif ikizi dashboard.log) ve
        # `state/bars_cboe_backup/` 11 MB, 56 dosya, sıfır referanslıydı — üçünü de hiçbir
        # dedektör görmüyordu. Üçü K1'de taşındı (docs/ ve backups/k1-emekli-20260730/), ama
        # ASIL onarım burası: kesit genişlemezse yarın aynı sınıf yeniden birikir.
        #
        # OKUYUCU TESTİ: ELLE BEYAZ LİSTE DEĞİL, KAYNAK TARAMASI. Bu kesitteki dosyalar `store.*`
        # dışından okunuyor (config.py yaml yükler, secrets kendi erişimini kullanır), yani
        # `codelaw.artifact_graph` onları GÖREMEZ ve "okuyucusu yok" demek yanlış olur. Elle bir
        # beyaz liste tutmak ise tam olarak bu turda onarılan hastalığın (monitoring.sh'ın 3/11
        # jetonu, NOTIFY_TOKENS'ın eski el listesi) yeniden üretilmesi olurdu: liste eskir, dedektör
        # sessizce kurt masalı anlatır. Bunun yerine denetimin KENDİ kullandığı kanıt yöntemi
        # uygulanır — adı kaynak ağacında ARA. `bars_cboe_backup`/`server.log` bulgusu tam böyle
        # kurulmuştu (grep → 0 sonuç); `bounds.yaml`/`goal.yaml` ise onlarca yerde geçer.
        _src_text = _source_corpus()

        def _unreferenced(nm: str) -> bool:
            return bool(_src_text) and nm not in _src_text

        for f in config.STATE.parent.glob("*.json*"):
            nm = f.name
            if nm in known or not _unreferenced(nm):
                continue
            try:
                if not f.is_file() or f.stat().st_size <= 4:
                    continue
            except OSError:  # sessiz-yutma: stat edilemeyen yol için orphan iddiası KURULAMAZ — bkz. yukarıdaki aynı gerekçe
                continue
            orphans.append(f"(kök) {nm}")
        # state/ altındaki .json* OLMAYAN dolu artefaktlar: log dosyaları ve yedek DİZİNLERİ tam
        # bu yolla görünmez kalıyordu (11 MB'lık `bars_cboe_backup/` ve donuk `server.log`).
        for f in config.STATE.iterdir():
            nm = f.name
            if nm in known or ".json" in nm or nm.startswith("."):
                continue
            if not _unreferenced(nm):
                continue
            try:
                if f.is_dir():
                    if any(f.iterdir()):        # boş dizin bulgu değildir
                        orphans.append(f"(dizin) {nm}/")
                elif f.stat().st_size > 4:
                    orphans.append(nm)
            except OSError:  # sessiz-yutma: stat/iterdir edilemeyen yol için orphan iddiası KURULAMAZ — bkz. yukarıdaki aynı gerekçe
                continue

        ok = not orphans
        return _row("orphan_state_files", ok, len(orphans), f"{len(arts)} bilinen artefakt",
                    ("her disk dosyasının bir okuyucusu/beyanı var" if ok
                     else f"{len(orphans)} dosya diskte var ama hiçbir modül okumuyor: "
                          f"{', '.join(sorted(orphans)[:5])} — üretilip tüketilmeyen kanıt"),
                    "state/*.json* + kök *.json* + state/ dizin-ve-diğer-uzantı listesi",
                    "codelaw.artifact_graph okuyucuları")
    except Exception as e:
        from . import obs
        obs.warn("orphan_scan_failed", error=f"{type(e).__name__}: {e}")
        return _row("orphan_state_files", False, None, None,
                    f"orphan taraması ÇALIŞMADI: {type(e).__name__} — dedektör körlüğü de bulgudur",
                    "state/*.json*", "codelaw.artifact_graph")


def _universe_recompute() -> dict:
    """Döngünün işlediği son seansta evrenin kaçta kaçının barı VARDI — barlardan yeniden say.

    Canlı hata buydu: seans tarihi endeksin (SPY) son barından seçiliyordu, ama o günün barı
    evrenin yalnız 46/250'sinde vardı; tazelik kapısı diğer 204'ü atlıyordu. Motor %18'lik yanlı
    bir kesitte karar verirken kapı 250 sembol üzerinde ölçüyordu. Hiçbir bileşen hatalı değildi.
    """
    try:
        from .adapters.data import REPLAY_UNIVERSE
        from . import config
        hb = store.read_json("heartbeat.json", {}) or {}
        session = hb.get("last_bar")
        if not session:
            return _row("universe_recompute", True, None, None,
                        "işlenmiş seans yok — yeniden hesap yapılmadı", "heartbeat.last_bar", "—")
        have = 0
        total = 0
        for t in REPLAY_UNIVERSE:
            p = config.BARS / f"{t}.csv"
            if not p.exists():
                total += 1
                continue
            total += 1
            try:
                # son satırın tarihini oku (tüm CSV'yi belleğe almadan)
                with p.open("rb") as fh:
                    fh.seek(0, 2)
                    size = fh.tell()
                    fh.seek(max(0, size - 4096))
                    tail = fh.read().decode("utf-8", "replace").strip().splitlines()
                last = tail[-1].split(",")[0][:10] if tail else ""
                if last >= str(session)[:10]:
                    have += 1
            except OSError as e:
                from . import obs
                obs.warn("universe_recompute_read_failed", ticker=t, error=str(e))
        cov = have / total if total else 0.0
        ok = cov >= 0.90
        return _row("universe_recompute", ok, f"%{100*cov:.1f}", f"{have}/{total}",
                    f"karar verilen seans ({session}) evrenin %{100*cov:.1f}'ini görüyordu"
                    + ("" if ok else " — MOTOR YANLI BİR KESİTTE KARAR VERİYOR"),
                    "heartbeat.last_bar", "state/bars/*.csv son tarih sayımı")
    except Exception as e:      # dedektörün kendi arızası SESSİZ kalmamalı (bkz. starved olayı)
        from . import obs
        obs.warn("universe_recompute_failed", error=f"{type(e).__name__}: {e}")
        return _row("universe_recompute", False, None, None,
                    f"yeniden hesap ÇALIŞMADI: {type(e).__name__} — dedektör körlüğü de bir bulgudur",
                    "heartbeat.last_bar", "state/bars/*.csv")


def render_text(deep: bool = False) -> str:
    rep = report(deep=deep)
    out = [f"YENİDEN HESAP · {rep['n']} denetim · {'TEMİZ' if rep['ok'] else 'AYRIŞMA VAR'}"]
    for r in rep["rows"]:
        out.append(f"  {'✓' if r['ok'] else '✗'} {r['check']}: {r['detail']}")
        out.append(f"      A={r['a_yol']}  B={r['b_yol']}")
    return "\n".join(out)


if __name__ == "__main__":
    import sys
    print(render_text(deep="--deep" in sys.argv))
