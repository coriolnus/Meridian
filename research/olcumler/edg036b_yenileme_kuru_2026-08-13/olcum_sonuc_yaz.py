"""EDG-2026-036b — SONUÇ DERLEYİCİ. Ham ölçüm dosyalarını tek `sonuc.json`a örer.

HÜKÜM YAZMAZ. Kartın üç ölçütünü (bütünlük / tüketici-tutarlılığı / dürüstlük) MEKANİK işaretler:
her ölçüt için ölçülmüş sayıyı ve karşılaştırma kuralını yazar; yorum Rol-1'e bırakılır.

kullanım: olcum_sonuc_yaz.py <asama1.json> <plan_kapsama.json> <islem_kapsama.json>
                             <ozdeslik.json> <taban_kunye.json> <cikti.json>
"""
import datetime as dt
import json
import sys
from pathlib import Path

A1 = json.loads(Path(sys.argv[1]).read_text())
PK = json.loads(Path(sys.argv[2]).read_text())
IK = json.loads(Path(sys.argv[3]).read_text())
OZ = json.loads(Path(sys.argv[4]).read_text())
KUN = json.loads(Path(sys.argv[5]).read_text())
OUT = Path(sys.argv[6])

W = [w for w in ("A", "B", "B_sv3", "B_svTOHUM", "B_literal") if f"olcum_{w}" in A1]


def g(w, *yol, vars=None):
    """iç içe sözlükten güvenli okuma — yoksa None (UYDURMA YASAĞI)."""
    cur = A1.get(f"olcum_{w}")
    for k in yol:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(k)
    return cur


def satir(ad, giris, ozet_fn):
    """Bir tüketici için tüm dünyaların özetini yan yana koyar."""
    return {"tuketici": ad, "giris_noktasi": giris,
            "dunyalar": {w: ozet_fn(w) for w in W}}


TABLO = []

TABLO.append(satir(
    "dsr_pbo_validation_trio", "analytics.py:2530 validation_trio → analytics.py:10 _trades()",
    lambda w: {"dsr_canli": g(w, "dsr_pbo_validation_trio", "dsr_canli"),
               "n_trials": g(w, "dsr_pbo_validation_trio", "n_trials"),
               "pbo": g(w, "dsr_pbo_validation_trio", "pbo"),
               "defter": g(w, "dsr_pbo_validation_trio", "defter")}))

TABLO.append(satir(
    "score_calibration", "analytics.py:829 → :848 `for t in _trades()`",
    lambda w: ({"_None": g(w, "score_calibration", "_None")}
               if g(w, "score_calibration", "_None") else
               {"n_real": g(w, "score_calibration", "n_real"),
                "n_cf": g(w, "score_calibration", "n_cf"),
                "gercek_rank_ic": g(w, "score_calibration", "katmanlar", "gercek", "rank_ic"),
                "gercek_n": g(w, "score_calibration", "katmanlar", "gercek", "n"),
                "gercek_anlamli": g(w, "score_calibration", "katmanlar", "gercek", "anlamli"),
                "gercek_kaynak": g(w, "score_calibration", "gercek_kaynak"),
                "verdict": g(w, "score_calibration", "verdict")})))

TABLO.append(satir(
    "component_ic", "component_ic.component_ic(write=True)",
    lambda w: ({"_None": g(w, "component_ic", "_None")} if g(w, "component_ic", "_None") else
               {"verdict": g(w, "component_ic", "verdict"),
                "n_gozlem": g(w, "component_ic", "n_gozlem"),
                "anlamli_sayim": g(w, "component_ic", "anlamli_sayim")})))

TABLO.append(satir(
    "threshold_curve", "threshold_curve.build()",
    lambda w: ({"_None": g(w, "threshold_curve", "_None")} if g(w, "threshold_curve", "_None") else
               {"verdict": g(w, "threshold_curve", "verdict"),
                "n_gozlem": g(w, "threshold_curve", "n_gozlem"),
                "canli_min_score": g(w, "threshold_curve", "canli_min_score"),
                "min_n": g(w, "threshold_curve", "min_n")})))

TABLO.append(satir(
    "cf_fidelity", "analytics.cf_fidelity()",
    lambda w: g(w, "cf_fidelity")))

TABLO.append(satir(
    "mae_profile", "analytics.mae_profile()",
    lambda w: g(w, "mae_profile")))

TABLO.append(satir(
    "skills_attribution", "analytics.skill_attribution() — GERÇEK katman",
    lambda w: {"n_skill_gercek_katmanli": g(w, "skills_attribution", "n_skill_gercek_katmanli"),
               "skills": [{k: s.get(k) for k in ("skill", "ad", "n", "avg_r", "win_rate")}
                          for s in (g(w, "skills_attribution", "skills") or [])][:8],
               "axis2": g(w, "skills_axis2")}))

TABLO.append(satir(
    "edge_verdict", "analytics.py:1840 (Faz-6 kilidi #1)",
    lambda w: {"passed": g(w, "edge_verdict", "passed"), "failed": g(w, "edge_verdict", "failed"),
               "unmeasured": g(w, "edge_verdict", "unmeasured"),
               "zayif": g(w, "edge_verdict", "zayif"),
               "verdict": g(w, "edge_verdict", "verdict")}))

TABLO.append(satir(
    "result_verdict", "analytics.py:2287 (Faz-6 kilidi #2)",
    lambda w: {"passed": g(w, "result_verdict", "passed"),
               "failed": g(w, "result_verdict", "failed"),
               "unmeasured": g(w, "result_verdict", "unmeasured"),
               "zayif": g(w, "result_verdict", "zayif"),
               "verdict": g(w, "result_verdict", "verdict"),
               "criteria": g(w, "result_verdict", "criteria")}))

TABLO.append(satir(
    "variance_attribution", "shadowlaw.variance_attribution(n_boot=400, seed=20260813)",
    lambda w: {k: g(w, "variance_attribution", k)
               for k in ("n_trades", "n_blocks", "block_days", "sd_dusus", "ort_dusus",
                         "margin_scale", "dd_veto_gurultunun_disinda", "para_payi_tek_terim")}))

TABLO.append(satir(
    "llm_calibration", "analytics.llm_opinion_calibration() (hermes.py:3313 damgası)",
    lambda w: g(w, "llm_calibration")))

TABLO.append(satir(
    "hermes_reflect_sayaci", "watchdog/hermes yansıma kadansı — defter UZUNLUĞU kapısı",
    lambda w: g(w, "hermes_reflect_sayaci")))

TABLO.append(satir(
    "rollback_kapisi", "rollback.evaluate_outcomes girdileri (karar noktasına KADAR)",
    lambda w: g(w, "BAYRAK_rollback_kapisi")))

TABLO.append(satir(
    "learning_scorecard", "analytics.learning_scorecard(goal)",
    lambda w: g(w, "learning_scorecard")))

TABLO.append(satir(
    "net_kotumser", "analytics.net_kotumser()",
    lambda w: {"band": (g(w, "net_kotumser") or {}).get("band"),
               "ozet": {k: v for k, v in (g(w, "net_kotumser") or {}).items() if k != "band"}}))

# ---- ÜÇ KRİTİK BAYRAK -------------------------------------------------------------------------
bayraklar = {
    "sieve_butunluk_dedektoru": {
        "ilk_kuru_kosumda": "8 ihlal (4 kritik) — SLIM artefakt, alan eksikliğinden",
        "dunyalar": {w: {"ok": g(w, "BAYRAK_sieve", "ok"),
                         "n_violation": g(w, "BAYRAK_sieve", "n_violation"),
                         "kritik_n": g(w, "BAYRAK_sieve", "kritik_n"),
                         "violations": g(w, "BAYRAK_sieve", "violations"),
                         "stages": g(w, "BAYRAK_sieve", "stages")} for w in W}},
    "shadowlaw_kayma_bekcisi": {
        "ilk_kuru_kosumda": "ATEŞLEDİ — margin_scale 0,1908→0,9898 (kayıtlı n=95)",
        "dunyalar": {w: {"olculdu": g(w, "BAYRAK_shadowlaw_drift", "olculdu"),
                         "kayma": g(w, "BAYRAK_shadowlaw_drift", "kayma"),
                         "atesledi": bool(g(w, "BAYRAK_shadowlaw_drift", "kayma")),
                         "margin_scale": g(w, "BAYRAK_shadowlaw_drift", "olcum_ozet",
                                           "margin_scale"),
                         "kayitli_n_trades": g(w, "BAYRAK_shadowlaw_drift", "kayitli_n_trades"),
                         "olcum_ozet": g(w, "BAYRAK_shadowlaw_drift", "olcum_ozet")}
                     for w in W}},
    "rollback_kapisi": {
        "ilk_kuru_kosumda": "AÇILDI — ham_delta −0,1779 < −0,1 (cur_score −0,0534, par 0,1245)",
        "dagitim_engeli_mi": ("kapı AÇILIRSA evet: tohum, yürürlükteki sürümün (v5) paydasına "
                              "girer ve `rollback.check_and_rollback` geri-alma değerlendirmesini "
                              "TETİKLER — canlı sürüm v3'e dönebilir"),
        "dunyalar": {w: g(w, "BAYRAK_rollback_kapisi") for w in W}},
}

# ---- BÜTÜNLÜK: live_paper + portfolio ---------------------------------------------------------
lp_A = g("A", "live_paper_satirlari") or {}
butunluk = {
    "live_paper_bit_ayniligi": {
        w: {**(g(w, "live_paper_satirlari") or {}),
            "A_ile_bit_ayni": ((g(w, "live_paper_satirlari") or {}).get("sha_satirlar")
                               == lp_A.get("sha_satirlar"))}
        for w in W},
    "portfolio_realized_pnl": {w: g(w, "portfolio_realized_pnl") for w in W},
    "canli_realized_pnl": KUN.get("portfolio_realized_pnl"),
    "korunum_plan_islem": {w: g(w, "korunum_plan_islem") for w in W},
    "defter_sayaclari": {w: g(w, "_defter") for w in W},
}

# ---- KARTIN ÜÇ ÖLÇÜTÜ — MEKANİK İŞARET --------------------------------------------------------
def _isaret(w):
    lp = butunluk["live_paper_bit_ayniligi"].get(w, {})
    a = (lp.get("A_ile_bit_ayni") is True and lp.get("n") == 2
         and g(w, "portfolio_realized_pnl") == KUN.get("portfolio_realized_pnl"))
    # (b) tüketici tutarlılığı: hiçbir tüketici A'da ÖLÇÜLÜRKEN B'de None/ölçülemez olmayacak
    korlesen, acilan = [], []
    for t in TABLO:
        da, db = t["dunyalar"].get("A"), t["dunyalar"].get(w)

        def _bos(x):
            if x is None:
                return True
            if isinstance(x, dict):
                if "_None" in x or "_olculemedi" in x:
                    return True
                vals = [v for k, v in x.items() if not k.startswith("_")]
                return all(v is None or v == [] or v == {} for v in vals)
            return False
        if not _bos(da) and _bos(db):
            korlesen.append(t["tuketici"])
        if _bos(da) and not _bos(db):
            acilan.append(t["tuketici"])
    sv = bayraklar["sieve_butunluk_dedektoru"]["dunyalar"].get(w, {})
    b = (not korlesen) and (sv.get("kritik_n") == 0)
    # (c) dürüstlük: kaynak damgası ayrımı defterde duruyor mu?
    d = g(w, "_defter") or {}
    c = (d.get("live_paper_n") == 2 and d.get("replay_seed_n", 0) > 0
         and d.get("damgasiz_n") == 0)
    return {
        "a_BUTUNLUK": {"gecti": bool(a), "live_paper_bit_ayni": lp.get("A_ile_bit_ayni"),
                       "live_paper_n": lp.get("n"),
                       "realized_pnl": g(w, "portfolio_realized_pnl"),
                       "beklenen_realized_pnl": KUN.get("portfolio_realized_pnl")},
        "b_TUKETICI_TUTARLILIGI": {"gecti": bool(b), "korlesen_tuketiciler": korlesen,
                                   "acilan_tuketiciler": acilan,
                                   "sieve_kritik_n": sv.get("kritik_n"),
                                   "sieve_ihlal_n": sv.get("n_violation")},
        "c_DURUSTLUK": {"gecti": bool(c), "defter_sayaclari": d,
                        "plan_defterinde_kaynak_damgasi": PK["canli_sema"]["kaynak_damgasi_var_mi"]},
    }


olcutler = {w: _isaret(w) for w in W if w != "A"}

# ---- DAMGA TASARIMI — ölçülmüş girdiler + seçenek matrisi -------------------------------------
damga = {
    "beyan": "ÖNERİDİR, HÜKÜM DEĞİLDİR. Her seçeneğin ölçülmüş sonucu yanında yazılıdır.",
    "zorunlu": {
        "kaynak": {"deger": "replay_seed",
                   "gerekce": ("ledgerstamp.REPLAY_SEED — `run.py:203` tohum yolunun damgası. "
                               "Damgasız satır `belirsiz` sayılır ve 13 tüketici bunu canlı "
                               "kanıt sanar (EDG-036 aşama-0)."),
                   "olculen": {w: (g(w, "_defter") or {}).get("replay_seed_n") for w in W}}},
    "strategy_version": {
        "secenekler": {
            "sv=5 (yürürlükteki sürüm)": {
                "olculen_rollback": bayraklar["rollback_kapisi"]["dunyalar"].get("B"),
                "etki": "tohum v5'in PAYDASINA girer"},
            "sv=3 (replay'in kendi ürettiği; sandbox strategy.yaml)": {
                "olculen_rollback": bayraklar["rollback_kapisi"]["dunyalar"].get("B_sv3"),
                "etki": "tohum EBEVEYN (v3) paydasına girer"},
            "sv=90 (tohuma AYRI sürüm-uzayı)": {
                "olculen_rollback": bayraklar["rollback_kapisi"]["dunyalar"].get("B_svTOHUM"),
                "etki": "tohum hiçbir canlı sürümün paydasına girmez"}},
    },
    "tohum_parti_kimligi": {
        "onerilen_alanlar": {
            "tohum_parti": "EDG-036b-2026-08-13",
            "tohum_kaynak_sha256": A1["tohum_kaynagi"]["sha256"],
            "tohum_plan_sha256": A1["tohum_kaynagi"]["plan_sha256"],
            "motor_kunyesi": OZ.get("motor_sha_farki_beklenen"),
            "replay_penceresi": "2022-01-01 → 2026-07-30",
            "evren_n": 251},
        "gerekce": ("kart kill#3 'yeni tohum yürürlükteki paketle üretilmemişse (sha uyuşmazlığı) "
                    "→ geçersiz' — parti kimliği bu kontrolü SONRADAN da yapılabilir kılar")},
    "EDG037_friksiyon_serhi": {
        "metin": ("Bu defter `slippage_bps=5` + `commission_per_share` varsayımıyla ÜRETİLDİ. "
                  "EDG-037 (TCA) ilk ölçümünde bu varsayım ~9 KAT İYİMSER çıktı. Tohum GÜNCEL "
                  "PAKETİ temsil eder ama İYİMSER FRİKSİYONU taşır — GERÇEKLEŞEN İCRA DEĞİLDİR."),
        "gerekce": "kart `hukum_duzeltmesi.friksiyon_serhi` — damgada AÇIKÇA taşınmalı",
        "olculen_maliyet_modeli": A1.get("tohum_kaynagi", {}).get("cost_model")},
    "llm_opinion_kalici_sinir": {
        "metin": ("Bu tohum `llm_opinion` ÜRETEMEZ (hermes.py:3313 canlı yolda basılır; "
                  "backtest'te alan hiç geçmez). `llm_opinion_calibration` tohumdan "
                  "BESLENEMEZ ve bu DOĞRUDUR."),
        "olculen_plan_kapsamasi": PK["kapsama_tablosu"].get("llm_opinion")},
}

sonuc = {
    "kart": "EDG-2026-036",
    "asama": "1 (kuru koşum) — TEKRAR, DÜZELTİLMİŞ ARTEFAKTLA + PLAN DEFTERİ",
    "olcum_zamani": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
    "olcum_ajani_beyani": A1["olcum_ajani_beyani"],
    "kapsam_disi_beyani": (
        "ÖLÇÜLMEDİ (uydurulmadı): (1) `equity_curve.json` — gerçek yenileme yolu run.py:204 "
        "onu da yazar; bu şasi `res.equity`yi diske SERİLEŞTİRMEZ, o yüzden her iki dünyada da "
        "CANLI eğri duruyor. Ölçülen 15 tüketicinin HİÇBİRİ bu dosyayı okumadığı için kıyas "
        "bozulmaz, ama aşama-2'de yazılması ŞARTTIR (ledgerstamp.seed_boundary bu dosyanın "
        "son noktasını + mtime çiftini okur). (2) `rollback._karar_girdisi` (would_have replay'i) "
        "— bar tabanı ister, KOŞULMADI; rapor karar noktasına KADARki girdilerdir."),
    "ozdeslik_kapisi_kill1": {
        "gecti": OZ.get("kill1_gecti"), "bayt_ozdeslik": OZ.get("bayt_ozdeslik"),
        "sonuc_blok_esitligi": OZ.get("sonuc_blok_esitligi"),
        "islemler_sha256": OZ.get("dosya_sha256", {}).get("yerel", {}).get("islemler"),
        "ref_032_islemler_sha256": OZ.get("dosya_sha256", {}).get("ref_032", {}).get("islemler")},
    "tohum_kaynagi": A1["tohum_kaynagi"],
    "canli_taban": A1["canli_taban"],
    "dunyalar": A1["dunyalar"],
    "PLAN_DEFTERI_KAPSAMA": {
        "canli_sema": PK["canli_sema"], "kova_ozeti": PK["kova_ozeti"],
        "kapsama_tablosu": PK["kapsama_tablosu"], "kimlik_bicimi": PK["kimlik_bicimi"],
        "gate_verdict_dagilimi": PK["gate_verdict_dagilimi"], "defter": PK["defter"],
        "defterde_fazla_canli_semada_yok": PK["defterde_fazla_canli_semada_yok"]},
    "ISLEM_DEFTERI_KAPSAMA": {
        "canli_sema": IK["canli_sema"], "kova_ozeti": IK["kova_ozeti"],
        "defter": IK["defter"]},
    "TUKETICI_TABLOSU_A_vs_B": TABLO,
    "UC_KRITIK_BAYRAK": bayraklar,
    "BUTUNLUK": butunluk,
    "KART_UC_OLCUTU_MEKANIK": olcutler,
    "DAMGA_TASARIMI": damga,
    "YAN_BULGU_1_ROLLBACK_KAPISI_ARTEFAKT_DEGIL_GOAL": {
        "soru": ("036 ilk kuru koşumu rollback kapısının AÇILDIĞINI (ham_delta −0,1779) ölçtü ve "
                 "bunu tohum/artefakt sorunu bağlamında raporladı. Bu koşumda kapı AÇILMIYOR "
                 "(+0,0328). Fark ARTEFAKTTAN mı GOAL'DEN mi?"),
        "ayristirma_2x2": json.loads(
            (Path(__file__).resolve().parent / "skor_ayristirma.json").read_text()),
        "olculen": ("score_mod.score() TAM-SATIR ve SLIM defter için AYNI değeri veriyor "
                    "(0,1573 / −0,0534). Tek çevrilen değişken `goal.max_drawdown`: 0,08 → 0,16."),
        "kanit": ("canlı `state/goal.yaml` mtime 2026-08-13T01:26:41Z — 036 ilk kuru koşumundan "
                  "(01:12-01:23) SONRA yazılmış (v238 arıza turu, commit 62727d6 01:07). Yani ilk "
                  "koşum ESKİ hedefle (max_dd 0,08) ölçmüştü."),
        "sonuc": ("rollback kapısının açılması ARTEFAKT KUSURU DEĞİLDİ ve tohum yenilemesinin "
                  "sonucu da değil; yürürlükteki hedefle kapı KAPALI kalıyor.")},
    "YAN_BULGU_2_SHADOWLAW_CANLIDA_DA_ATESLIYOR": {
        "olculen": {"A_canli_bugun": 0.2795, "A_yalniz_replay_seed_95": 0.2819,
                    "B_yenileme": 0.7404, "kayitli_MEASURED_V3": 0.1908,
                    "MONEY_GATE_MARGIN": 0.004},
        "yontem": ("bağımsız süreç, TEK ÇAĞRI (shadowlaw.variance_drift kanonik n_boot=2000/"
                   "seed=42, başka hiçbir ölçüm önce koşmadı) — olcum_drift_kontrol.py"),
        "sonuc": ("kayma bekçisi BUGÜNKÜ CANLI DEFTERDE de ateşliyor (türetilen marj 0,006 ≠ "
                  "yürürlükteki 0,004). Yenileme bunu YARATMIYOR, BÜYÜTÜYOR (0,015). Bayrak "
                  "yenilemeye ATFEDİLEMEZ; ayrı bir kalem."),
        "ilk_kosumla_fark": ("036 ilk koşumu A için 0,1893 (kayma YOK) ölçmüştü; aynı goal "
                             "değişikliği (max_dd 0,08→0,16) bu farkı da açıklıyor — sd_dusus "
                             "0,0339 iki koşumda AYNI, yani defter değişmedi.")},
    "YAN_BULGU_3_PLAN_DEFTERI_LLM_DAMGASINI_SILIYOR": {
        "olculen": {w: (A1.get(f"olcum_{w}", {}).get("llm_calibration") or {})
                    .get("n_plans_with_opinion") for w in W},
        "mekanizma": ("run.py:283 `store.write_jsonl('trade_plans.jsonl', _keep)` plan defterinin "
                      "TAMAMINI ezer. Canlı defterdeki 8 `llm_opinion` damgası (hermes.py:3319) "
                      "yenilemede YOK OLUR: koruyucu B'de yalnız live_paper planlarıyla gelen 1 "
                      "damga kalır, harfi harfine yolda (B_literal) 0 kalır."),
        "etki": ("llm_opinion_calibration çifti A'da 4 → B'de 1 → B_literal'de 0. Tüketici "
                 "KÖRLEŞMİYOR ama kanıt tabanı daralıyor — aşama-2'de `llm_opinion` taşıyan "
                 "planların KORUNMASI ayrı bir prosedür adımı olarak gerekir.")},
}
OUT.write_text(json.dumps(sonuc, ensure_ascii=False, indent=1, default=str))
print(f"yazıldı: {OUT}")
for w, o in olcutler.items():
    print(f"  {w:11s} a={o['a_BUTUNLUK']['gecti']}  b={o['b_TUKETICI_TUTARLILIGI']['gecti']} "
          f"(körleşen={len(o['b_TUKETICI_TUTARLILIGI']['korlesen_tuketiciler'])}, "
          f"sieve_kritik={o['b_TUKETICI_TUTARLILIGI']['sieve_kritik_n']})  "
          f"c={o['c_DURUSTLUK']['gecti']}")
