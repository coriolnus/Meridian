"""validation_report.py — "hangi mekanizma/edge KANITLANIYOR?" sorusunun salt-okuma tek tablosu.

Dolu karşı-olgusal defter + gerçek işlem defteri üzerinden sistemin sinyal/edge kanıtını tek
raporda toplar: temel edge (kapı hükmü başına ve silahlanan dilim), skor kalibrasyonu, kurulum
katkısı, rejim edge'i, eşik karnesi (near-miss: hangi eşik masada para bırakıyor) ve cf↔gerçek
sadakati (simülasyona ne kadar güvenilebilir). SALT-OKUMA analizdir: hiçbir karar/kapı etkilenmez
ve KENDİ ölçümünü yapmaz — yalnız KAYITLI kanıtı (analytics kalibrasyonları, çözülmüş cf
satırları, defter sayımları) gösterir.

GİRİŞLER: `build` — makine-okunur rapor sözlüğü (evidence_base, base_edge, score_calibration,
setup_edge, regime_edge, near_miss, cf_fidelity); `render_text` — operatör için metin döküm
(`__main__` yolu basar); `_verdict` — n ve ortalama R'den hüküm cümlesi (taban MIN_N=30).

DEĞİŞMEZLER: her satır n ve anlamlılık taşır; yetersiz örneklemde "KANIT YOK (n=...)" der,
uydurmaz. Gerçek ve karşı-olgusal popülasyonlar AYRI raporlanır — havuzlanmış tek sayı, gerçek
işlemlerin sinyalini görünmez kılar; standart-hata yönteminin künyesi basılır ki "anlamlı"
damgasının dayanağı okunabilsin. Okur: counterfactual çözülmüş satırları, trades.jsonl ve
analytics raporları; hiçbir şey yazmaz."""
from __future__ import annotations

from . import store, analytics, counterfactual as cf

MIN_N = 30           # bir edge iddiasının anlamlı sayılması için asgari örneklem


def _edge(rows: list) -> dict:
    """Bir satır kümesinin edge özeti: girilen ve `r_multiple`ı ölçülmüş satırlarda n, ortalama R ve
    kazanma oranı. Ölçülecek satır yoksa n=0 ve diğerleri None — sıfır YAZILMAZ."""
    rms = [float(r["r_multiple"]) for r in rows if r.get("entered") and r.get("r_multiple") is not None]
    if not rms:
        return {"n": 0, "avg_r": None, "win_rate": None}
    return {"n": len(rms), "avg_r": round(sum(rms) / len(rms), 3),
            "win_rate": round(sum(1 for r in rms if r > 0) / len(rms), 3)}


def build() -> dict:
    """Makine-okunur kanıt raporunu kurar: kanıt tabanı, kapı hükmü başına temel edge, skor
    kalibrasyonu, kurulum/skill katkısı, rejim edge'i, eşik karnesi ve cf↔gerçek sadakati.
    SALT OKUMA — kendi ölçümünü yapmaz, yalnız KAYITLI kanıtı toplar."""
    rows = cf.resolved_rows(entered_only=False)                # tüm çözülmüş cf (near-miss dahil değil)
    rows_nm = cf.resolved_rows(entered_only=False, include_near_miss=True)
    real_n = len(store.read_jsonl("trades.jsonl"))

    # 1) TEMEL EDGE — verdict başına cf edge (asıl soru: strateji para kazanıyor mu?)
    by_verdict = {}
    for v in ("GO", "REVIEW", "NO_GO"):
        by_verdict[v] = _edge([r for r in rows if r.get("verdict") == v])
    taken = _edge([r for r in rows if r.get("taken")])         # o gün silahlanacak olanlar

    # 2) SKOR KALİBRASYONU (skor sonucu öngörüyor mu?)
    sc = analytics.score_calibration()

    # 3) EKRAN/KURULUM KATKISI
    attr = analytics.skill_attribution()
    setup_edge = {}
    for su in ("breakout_vcp", "pullback", "momentum_burst", "episodic_pivot"):
        setup_edge[su] = _edge([r for r in rows if r.get("setup") == su])

    # 4) REJİM EDGE (chop gerçekten zararlı mı? trend_up pozitif mi?)
    regime_edge = {}
    for rg in set(r.get("regime") for r in rows if r.get("regime")):
        regime_edge[rg] = _edge([r for r in rows if r.get("regime") == rg])

    # 5) EŞİK KARNESİ (near-miss: hangi eşik masada para bırakıyor)
    nm = analytics.near_miss_report()

    # 6) cf↔GERÇEK SADAKATİ (cf'ye ne kadar güvenebiliriz)
    fid = analytics.cf_fidelity()

    return {
        "evidence_base": {"cf_resolved": len(rows), "cf_resolved_incl_near_miss": len(rows_nm),
                          "real_trades": real_n},
        "base_edge": {"by_verdict": by_verdict, "taken": taken},
        "score_calibration": sc,
        "setup_edge": setup_edge,
        "skill_attribution": (attr or {}).get("skills"),
        "regime_edge": regime_edge,
        "near_miss": nm,
        "cf_fidelity": fid,
    }


def _verdict(n, avg_r, min_n=MIN_N):
    """n ve ortalama R'den hüküm cümlesi üretir. n taban örneklemin altındaysa "KANIT YOK (n=…)" —
    yetersiz örneklemde edge iddiası BASILMAZ."""
    if not n or n < min_n:
        return f"KANIT YOK (n={n or 0}<{min_n})"
    if avg_r is None:
        return "—"
    return ("EDGE VAR ✓" if avg_r > 0.05 else "EDGE YOK ✗" if avg_r < -0.05 else "NÖTR ~") + f" ({avg_r:+.3f}R)"


def render_text() -> str:
    """`build()` raporunu operatör için numaralı metin dökümüne çevirir (her satır n ve hükmüyle).
    SALT OKUMA — hiçbir şey yazmaz."""
    r = build()
    L = []
    eb = r["evidence_base"]
    L.append(f"KANIT TABANI: {eb['cf_resolved']} çözülmüş cf (near-miss dahil {eb['cf_resolved_incl_near_miss']}) · {eb['real_trades']} gerçek işlem")
    L.append("")
    L.append("1) TEMEL EDGE (strateji para kazanıyor mu?)")
    for v, e in r["base_edge"]["by_verdict"].items():
        L.append(f"   {v:7} → {_verdict(e['n'], e['avg_r'])}" + (f" · kazanma {e['win_rate']}" if e['win_rate'] is not None else ""))
    t = r["base_edge"]["taken"]
    L.append(f"   SİLAHLANAN → {_verdict(t['n'], t['avg_r'])}" + (f" · kazanma {t['win_rate']}" if t['win_rate'] is not None else ""))
    L.append("")
    sc = r["score_calibration"]
    if sc:
        L.append(f"2) SKOR KALİBRASYONU: rank-IC {sc['rank_ic']} (n={sc['n']}) · monoton mu: {sc.get('monotone_hint')}")
        # AYRIŞTIRMA: tek satırlık havuzlanmış IC, 22:1 cf ağırlığıyla gerçek işlemlerin
        # sinyalini görünmez kılıyordu. İki popülasyon AYRI raporlanır; hüküm gerçek dilimindir.
        _r, _c = sc.get("real"), sc.get("cf")
        if _r or _c:
            # `se_yontem` KÜNYESİ BASILIR: analytics onu YAZIYOR ama hiçbir okuyucusu
            # yoktu (yasa 6). Alan boş bir etiket değil, anlamlılık iddiasının DAYANAĞI: standart
            # hata i.i.d. VARSAYIMIYLA hesaplanıyor. Gerçek işlemler güne/ticker'a kümelenmişse o
            # varsayım iyimserdir ve "anlamlı" damgası olduğundan dar bir aralıktan gelir —
            # okuyucunun bunu bilmeden 'anlamlı' kelimesine yaslanması yanlış bir kesinliktir.
            L.append(f"     gerçek: {_r['rank_ic']} (n={_r['n']}, anlamlı: {_r.get('anlamli')}"
                     f", se yöntemi: {_r.get('se_yontem') or 'kaydedilmemiş'})"
                     if _r else "     gerçek: n<30 — ÖLÇÜLMEDİ")
            L.append(f"     karşı-olgusal: {_c['rank_ic']} (n={_c['n']}, anlamlılık ölçülmedi — "
                     f"gözlemler güne/ticker'a kümelenmiş)" if _c else "     karşı-olgusal: n<30")
            L.append(f"     HÜKÜM: {sc.get('verdict')}")
        for q in sc.get("quintiles", []):
            L.append(f"     skor {q['score_lo']:.0f}-{q['score_hi']:.0f}: ort {q['avg_r']:+.3f}R · kazanma {q['win_rate']} (n={q['n']})")
    else:
        L.append("2) SKOR KALİBRASYONU: KANIT YOK (n<30)")
    L.append("")
    L.append("3) KURULUM EDGE (hangi kurulum para kazanıyor)")
    for su, e in r["setup_edge"].items():
        L.append(f"   {su:15} → {_verdict(e['n'], e['avg_r'])}")
    L.append("")
    L.append("4) REJİM EDGE (chop gerçekten zararlı mı?)")
    for rg, e in sorted(r["regime_edge"].items()):
        L.append(f"   {rg:10} → {_verdict(e['n'], e['avg_r'])}" + (f" · kazanma {e['win_rate']}" if e['win_rate'] is not None else ""))
    L.append("")
    nm = r["near_miss"]
    L.append(f"5) EŞİK KARNESİ (near-miss, toplam {nm.get('resolved_total', 0)})")
    for b, d in (nm.get("buckets") or {}).items():
        L.append(f"   {b:8} eşiği altı → {_verdict(d.get('n_r', 0), d.get('avg_r'), min_n=10)} (giriş {d.get('entered')})")
    L.append("")
    fid = r["cf_fidelity"]
    if fid:
        L.append(f"6) cf↔GERÇEK SADAKATİ: korelasyon {fid.get('corr')} · sapma {fid.get('mean_diff_r')}R (n={fid.get('n')}) · GÜVENİLİR: {fid.get('fidelity_ok')}")
    else:
        L.append("6) cf↔GERÇEK SADAKATİ: KANIT YOK (kesişim <5 alınan-gerçek çift)")
    return "\n".join(L)


if __name__ == "__main__":
    print(render_text())
