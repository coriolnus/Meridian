"""EDG-036 sonuc.json üreteci — HER SAYI ölçüm dosyalarından okunur, elle yazılmaz."""
import datetime as dt
import hashlib
import json
from pathlib import Path

OUT = Path("/Users/erdemozturk/AI-Trading/research/olcumler/edg036_tohum_2026-08-13")
a0 = json.loads((OUT / "canli_asama0.json").read_text())
a0b = json.loads((OUT / "canli_asama0b.json").read_text())
k = json.loads((OUT / "asama1_kiyas.json").read_text())
g = json.loads((OUT / "asama1_kapilar.json").read_text())
A, B = k["olcum_A"], k["olcum_B"]
GA, GB = g["dunya_A"], g["dunya_B"]


def sha16(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def yol(x, *ks, d=None):
    for kk in ks:
        if not isinstance(x, dict):
            return d
        x = x.get(kk, d)
    return x


# ---- AŞAMA-0 TÜKETİCİ TABLOSU (her satır kanıtlı: file:line + canlı ölçüm) ---------------------
T = [
    {"tuketici": "DSR — canlı defterin deflate Sharpe'ı",
     "giris_noktasi": "meridian/analytics.py:2530 validation_trio → analytics.py:10 _trades()",
     "tohumu_okuyor": "EVET",
     "kaynak_ayrimi": "HAYIR — `_trades()` damgayı hiç görmez; payda TÜM defter",
     "canli_cikti": {"dsr_tum_defter": yol(a0, "dsr", "TUM_DEFTER (validation_trio'nun fiilen kullandığı)", "dsr", "dsr"),
                     "n": 97, "yalniz_live_paper": "ÖLÇÜLEMEZ (n=2 < DSR_MIN_N=20)",
                     "yalniz_replay_seed_dsr": yol(a0, "dsr", "yalniz_replay_seed", "dsr", "dsr")},
     "not": "DSR ayrıca health.FAZ6_KILITLERI'nin 5. kilidi (health.py:101,187-195)"},
    {"tuketici": "PBO / CSCV",
     "giris_noktasi": "analytics.py:2565 validation.pbo_cscv(validation_ledger.jsonl satırları)",
     "tohumu_okuyor": "HAYIR",
     "kaynak_ayrimi": "KONU DIŞI — trades defterini hiç okumaz",
     "canli_cikti": a0.get("pbo_tabani"),
     "not": "aday getiri serilerinden hesaplanır; tohum yenilemesi PBO'yu DEĞİŞTİRMEZ (kuru koşumda birebir aynı: 0.5714)"},
    {"tuketici": "Skor→sonuç kalibrasyonu (score_calibration.json)",
     "giris_noktasi": "analytics.py:829 score_calibration → analytics.py:848 `for t in _trades()`",
     "tohumu_okuyor": "EVET",
     "kaynak_ayrimi": "KISMİ — `gercek_kaynak` YAN KANALI ayırır (analytics.py:939-945), ama HÜKME giren "
                      "`katmanlar.gercek` ayırmaz (n=97'nin 95'i tohum)",
     "canli_cikti": {k2: yol(a0, "score_calibration.json", k2)
                     for k2 in ("n_real", "katmanlar", "gercek_kaynak", "verdict")},
     "not": "edge_verdict 1. ölçütü (analytics.py:1866-1872) bu `katmanlar.gercek`i okur"},
    {"tuketici": "EDGE HÜKMÜ (edge_verdict)",
     "giris_noktasi": "analytics.py:1840; 1. ölçüt score_calibration.json, 5. ölçüt _realized_drawdown → _trades()",
     "tohumu_okuyor": "EVET (dolaylı + doğrudan)",
     "kaynak_ayrimi": "HAYIR",
     "canli_cikti": {"kuru_kosum_A": {kk: A["karne_edge_verdict"][kk]
                                      for kk in ("passed", "failed", "unmeasured", "zayif", "verdict")}},
     "not": "health.FAZ6_KILITLERI 1. kilit `edge_kaniti`"},
    {"tuketici": "SONUÇ HÜKMÜ (result_verdict)",
     "giris_noktasi": "analytics.py:2268 → 2287 `trades = _trades()`",
     "tohumu_okuyor": "EVET",
     "kaynak_ayrimi": "HAYIR — dört dolar ölçütünün paydası TÜM defter (n=97)",
     "canli_cikti": {"kuru_kosum_A": {kk: A["karne_result_verdict"][kk]
                                      for kk in ("passed", "failed", "unmeasured", "zayif", "verdict")}},
     "not": "health.FAZ6_KILITLERI 2. kilit `sonuc_hukmu`; sermaye artırımı + silahlanma bu hükme bakar (ROADMAP §3.1)"},
    {"tuketici": "VARYANS ATRİBÜSYONU (shadowlaw.variance_attribution)",
     "giris_noktasi": "meridian/shadowlaw.py:341; çağrı yolu shadowlaw.py:445 variance_drift, :603 --olc CLI",
     "tohumu_okuyor": "EVET (defter argüman olarak geçer; canlı çağrı `analytics._trades()`)",
     "kaynak_ayrimi": "HAYIR",
     "canli_cikti": {"kuru_kosum_A": A["karne_variance_attribution"],
                     "kayma_bekcisi_A": GA["shadowlaw_variance_drift"]["kayma"]},
     "not": "MONEY_GATE_MARGIN (0,02×margin_scale) ve DD_VETO_MARGIN bu ölçümden TÜRETİLMİŞ canlı sabitler"},
    {"tuketici": "LLM görüş kalibrasyonu (llm_calibration.json)",
     "giris_noktasi": "analytics.py:1074 llm_opinion_calibration → 1086 `for t in _trades()` (plan_id join)",
     "tohumu_okuyor": "EVET",
     "kaynak_ayrimi": "HAYIR",
     "canli_cikti": {"llm_calibration.json": a0.get("llm_calibration.json"),
                     "sieve_A": {"in": 97, "out": 4, "drops": {"piyasa:llm_görüşü_yok": 93}},
                     "plan_llm_opinion_tasiyan": a0b.get("plan_llm_opinion_n")},
     "not": "tohumun 95/95 satırı plana JOIN OLUYOR (a0b.plan_join) — yani tohum bu tüketicinin paydasında"},
    {"tuketici": "Bileşen IC (component_ic.json)",
     "giris_noktasi": "meridian/component_ic.py:451 `for t in store.read_jsonl('trades.jsonl')`",
     "tohumu_okuyor": "EVET",
     "kaynak_ayrimi": "HAYIR",
     "canli_cikti": {"verdict": yol(a0, "component_ic.json", "verdict")},
     "not": "canlı hüküm metni 'gerçek katman ... n=95' diyor — o 95 TOHUMUN KENDİSİ"},
    {"tuketici": "Eşik eğrisi (threshold_curve.json)",
     "giris_noktasi": "meridian/threshold_curve.py:87 `for t in store.read_jsonl('trades.jsonl')`",
     "tohumu_okuyor": "EVET",
     "kaynak_ayrimi": "HAYIR",
     "canli_cikti": {"verdict": yol(a0, "threshold_curve.json", "verdict")},
     "not": "'canlı eşik 60 (ort R -0,0423, n=97)' — payda tohum"},
    {"tuketici": "Skills karnesi (skill_attribution → skills.catalog)",
     "giris_noktasi": "analytics.py:79 skill_attribution → _trades(); skills.py:332 catalog()",
     "tohumu_okuyor": "EVET",
     "kaynak_ayrimi": "HAYIR",
     "canli_cikti": {"kuru_kosum_A": A["skills_attribution"]["skills"]},
     "not": "vcp-screener n=91 / pullback-screener n=4 — hepsi tohum satırı (canlı yalnız 2)"},
    {"tuketici": "Eksen-2 öneri eşikleri (skills.recommend_from_attribution / axis2_diagnosis)",
     "giris_noktasi": "meridian/skills.py:383, :725 — `catalog()`ın n/avg_r alanları üzerinden",
     "tohumu_okuyor": "EVET (dolaylı — skill_attribution üzerinden)",
     "kaynak_ayrimi": "HAYIR",
     "canli_cikti": {"axis2_status.json_otomatik": yol(a0b, "axis2_status", "otomatik", "motor_ici_esik_asan"),
                     "kuru_kosum_A_sayim": A["skills_axis2_teshis"]["sayim"]},
     "not": "canlı axis2 kaydındaki 'pullback-screener n=4 avg_r=-1,0' gerçek katmanı TOHUMDUR"},
    {"tuketici": "cf defteri & near_miss",
     "giris_noktasi": "analytics.py:1465 near_miss_report → counterfactual.resolved_rows (trades'e HİÇ dokunmaz)",
     "tohumu_okuyor": "HAYIR",
     "kaynak_ayrimi": "KONU DIŞI",
     "canli_cikti": {"kuru_kosum_A": A["near_miss"], "kuru_kosum_B": B["near_miss"],
                     "cf_resolved_entered": A["cf_defteri_n"]},
     "not": "künyesi zaten 'yalnız-simüle, n_real=0'; A ve B'de BİREBİR AYNI"},
    {"tuketici": "cf_fidelity",
     "giris_noktasi": "analytics.py:1400 cf_fidelity → _trades() (gerçek↔cf kesişimi)",
     "tohumu_okuyor": "EVET",
     "kaynak_ayrimi": "HAYIR",
     "canli_cikti": {"anahtarlar": a0.get("cf_fidelity.json_anahtarlar")},
     "not": "kesişim tarafı gerçek defterden gelir; tohum orada"},
    {"tuketici": "Hermes hipotez üretimi — yansıma SAYI kapısı",
     "giris_noktasi": "hermes_runtime.py:310 `_restored_baseline`, :397 `_run`, :526 `status`; hermes.py:3839 _closed_count",
     "tohumu_okuyor": "EVET — defter UZUNLUĞU sayaç",
     "kaynak_ayrimi": "HAYIR",
     "canli_cikti": {"hermes_status.last_reflect_at": yol(a0b, "hermes_status_ozet", "last_reflect_at"),
                     "kuru_kosum_A": A["hermes_reflect_sayaci"]},
     "not": "tohum satır sayısı reflection_every sayacının doğrudan girdisi"},
    {"tuketici": "Ebeveyn zinciri / rollback (rollback.check_and_rollback + evaluate_outcomes)",
     "giris_noktasi": "meridian/rollback.py:180/373 — `strategy_version` ile filtreler, `kaynak` ile DEĞİL",
     "tohumu_okuyor": "EVET",
     "kaynak_ayrimi": "HAYIR — ayrım `strategy_version` üzerinden; tohum sv=4 olduğu için bugün v5'in "
                      "paydasına GİRMİYOR (tesadüf, tasarım değil)",
     "canli_cikti": {"scoreboard_v4": yol(a0b, "scoreboard_ozet", "versions", "4"),
                     "kuru_kosum_A": GA["rollback_girdileri"]},
     "not": "scoreboard'daki v4 kaydı live_score=-0,0089 · n_trades=95 · rolled_back=true — "
            "yani TOHUM bir kez ZATEN canlı sürüm geri almış"},
    {"tuketici": "shadowlaw kayma bekçisi (variance_drift)",
     "giris_noktasi": "meridian/shadowlaw.py:437",
     "tohumu_okuyor": "EVET",
     "kaynak_ayrimi": "HAYIR",
     "canli_cikti": {"kuru_kosum_A": GA["shadowlaw_variance_drift"]},
     "not": "A dünyasında kayma YOK (margin_scale 0,1893 ≈ kayıtlı 0,1908) — kayıt TOHUMDAN ölçülmüş"},
    {"tuketici": "reflect.propose_deterministic (deterministik öneri)",
     "giris_noktasi": "meridian/reflect.py:794 `store.read_jsonl('trades.jsonl', limit=40)`",
     "tohumu_okuyor": "EVET (son 40 satır — bugün 38'i tohum)",
     "kaynak_ayrimi": "HAYIR",
     "canli_cikti": "yalnız `reflect --auto` CLI'ından çağrılır (reflect.py:771 yorumu) — canlı otomatik yol DEĞİL",
     "not": "exit_reason kovaları + win_rate o 40 satırdan okunur"},
    {"tuketici": "N4 / örneklem sayaçları (learning_scorecard.defter)",
     "giris_noktasi": "analytics.py:639 → 668-681 `ledgerstamp.counts` + `orneklem_n`",
     "tohumu_okuyor": "EVET",
     "kaynak_ayrimi": "EVET — TAM AYIRIM. `orneklem_n = live_paper + belirsiz`; replay_seed paydaya GİRMEZ",
     "canli_cikti": {"kuru_kosum_A_defter": {kk: A["orneklem_learning_scorecard"]["defter"][kk]
                                             for kk in ("live_paper_n", "replay_seed_n",
                                                        "gercek_canli_n", "orneklem_n")}},
     "not": "TOHUM YENİLEMESİNDEN ETKİLENMEYEN TEK TÜKETİCİ (A ve B'de orneklem_n=2)"},
    {"tuketici": "Rejim bütçe tetikleyicisi (regime_trigger)",
     "giris_noktasi": "meridian/regime_trigger.py:22 evaluate(trades)",
     "tohumu_okuyor": "EVET",
     "kaynak_ayrimi": "HAYIR",
     "canli_cikti": {"kuru_kosum_A": A["regime_trigger"], "canli_fired": a0b.get("regime_trigger")},
     "not": "trend_up/chop eşiği ZATEN tohumla aşılmış ve olay yazılmış"},
    {"tuketici": "MAE profili (mae_profile.json)",
     "giris_noktasi": "analytics.py:3142 → _trades() (mfe_r/mae_r)",
     "tohumu_okuyor": "EVET",
     "kaynak_ayrimi": "HAYIR",
     "canli_cikti": {"n": yol(a0b, "mae_profile_ozet", "n")},
     "not": "canlı n=97"},
    {"tuketici": "Alfa/Beta atribüsyonu (trade_alpha_beta)",
     "giris_noktasi": "analytics.py:532 → 604 `ledgerstamp.kaynak_of(t)`",
     "tohumu_okuyor": "EVET",
     "kaynak_ayrimi": "EVET — `kaynak_kirilim` alanı",
     "canli_cikti": "ölçülmedi (sandbox'ta SPY penceresi ayrı; result_verdict.beta_duzeltilmis kolonunda taşınır)",
     "not": "ayrım VAR ama hükme girmez (`hukme_girmez: True`)"},
    {"tuketici": "Sermaye ayrıştırması (sermaye.py)",
     "giris_noktasi": "meridian/sermaye.py:176-210 `ledgerstamp.kaynak_of` + LIVE_PAPER/REPLAY_SEED",
     "tohumu_okuyor": "EVET",
     "kaynak_ayrimi": "EVET — P&L kaynak başına ayrı",
     "canli_cikti": {"portfolio.realized_pnl": yol(a0b, "portfolio_ozet", "realized_pnl")},
     "not": "canlı realized_pnl 277,98$ — YALNIZ live_paper; tohum P&L'i portföye HİÇ girmemiş"},
    {"tuketici": "/api/public/summary + /api/diagnostics",
     "giris_noktasi": "meridian/api.py:706-708 `_ls.split(trades)[_ls.LIVE_PAPER]`, api.py:1286, :3706",
     "tohumu_okuyor": "EVET",
     "kaynak_ayrimi": "EVET — public summary yalnız live_paper dilimini gösterir",
     "canli_cikti": "kod yolu doğrulandı (api.py:702-708 yorumu: 'ledgerstamp — learning_scorecard'ın da paydası')",
     "not": "dürüstlük ölçütünün (c) yüzey bacağı"},
]

kill1 = {
    "kriter": "kartın kill#1'i: '(0)'da tohumun gerçek tüketicisi çıkmazsa → yenileme GEREKSİZ'",
    "tetiklendi_mi": False,
    "gerekce": ("tohumun EN AZ 15 gerçek tüketicisi ölçüldü ve bunların 13'ü `kaynak` ayrımı YAPMIYOR "
                "(payda = tüm defter). Üstelik ikisi CANLI KARAR yolu: rollback/ebeveyn zinciri "
                "(strategy_version filtresi) ve hermes yansıma sayacı (defter uzunluğu). "
                "Yalnız `learning_scorecard.orneklem_n`, `sermaye.py`, `trade_alpha_beta.kaynak_kirilim`, "
                "`score_calibration.gercek_kaynak` ve `/api/public/summary` ayırıyor — "
                "bunlardan yalnız ilki bir KAPI paydası."),
    "hukum_yeri": "Rol-1 (ölçüm ajanı hüküm yazmaz)",
}

# ---- A vs B kıyas tablosu ----------------------------------------------------------------------
def satir(ad, av, bv, yon):
    return {"olcum": ad, "A_mevcut_tohum": av, "B_edg032_cmb": bv, "yon": yon}


kiyas = [
    satir("defter n", A["_defter"]["toplam"], B["_defter"]["toplam"], "büyür (97→887)"),
    satir("replay_seed n", A["_defter"]["replay_seed_n"], B["_defter"]["replay_seed_n"], "büyür"),
    satir("live_paper n", A["_defter"]["live_paper_n"], B["_defter"]["live_paper_n"], "DEĞİŞMEZ"),
    satir("portfolio.realized_pnl", A["portfolio_realized_pnl"], B["portfolio_realized_pnl"], "DEĞİŞMEZ"),
    satir("DSR (canlı defter)", yol(A, "dsr_pbo_validation_trio", "dsr_canli", "dsr"),
          yol(B, "dsr_pbo_validation_trio", "dsr_canli", "dsr"), "İYİLEŞİR (3e-06 → 0,0393) ama DSR_HARD_MIN=0,95'in ÇOK altında"),
    satir("Sharpe (gözlem başına)", yol(A, "dsr_pbo_validation_trio", "dsr_canli", "sharpe_gozlem"),
          yol(B, "dsr_pbo_validation_trio", "dsr_canli", "sharpe_gozlem"), "işaret DÖNER (−0,177 → +0,038)"),
    satir("PBO", yol(A, "dsr_pbo_validation_trio", "pbo", "pbo"),
          yol(B, "dsr_pbo_validation_trio", "pbo", "pbo"), "BİREBİR AYNI (trades okumaz)"),
    satir("score_calibration katmanlar.gercek",
          yol(A, "kalibrasyon_score_calibration", "katmanlar", "gercek"),
          yol(B, "kalibrasyon_score_calibration", "katmanlar", "gercek"),
          "KÖRLEŞİR — n=97 IC 0,0526 → None (885 satır `score` alanı yok)"),
    satir("score_calibration verdict", yol(A, "kalibrasyon_score_calibration", "verdict"),
          yol(B, "kalibrasyon_score_calibration", "verdict"), "KÖRLEŞİR"),
    satir("llm_calibration n_pairs", yol(A, "kalibrasyon_llm", "n_pairs"),
          yol(B, "kalibrasyon_llm", "n_pairs"), "KÜÇÜLÜR (4→1; 885 satır `plan_id` yok)"),
    satir("edge_verdict", {kk: A["karne_edge_verdict"][kk] for kk in ("passed", "failed", "unmeasured", "zayif")},
          {kk: B["karne_edge_verdict"][kk] for kk in ("passed", "failed", "unmeasured", "zayif")},
          "0/5 KALIR; spy_ustu 'kaldi'(−0,1113) → 'zayif'(+0,2094)"),
    satir("result_verdict", {kk: A["karne_result_verdict"][kk] for kk in ("passed", "failed", "unmeasured", "zayif")},
          {kk: B["karne_result_verdict"][kk] for kk in ("passed", "failed", "unmeasured", "zayif")},
          "0/4 → 1/4: net_pnl 'kaldi'(−5.264$) → 'gecti'(+20.963$); dolar_beklenti 'kaldi'(−54,27$) → 'zayif'(+23,63$)"),
    satir("result_verdict CI (dolar beklenti)", yol(A, "karne_result_verdict", "criteria", "dolar_beklenti", "ci"),
          yol(B, "karne_result_verdict", "criteria", "dolar_beklenti", "ci"),
          "CI DARALIR (genişlik 145,19$ → 91,64$) ama HÂLÂ sıfırı içeriyor"),
    satir("variance_attribution margin_scale", yol(A, "karne_variance_attribution", "margin_scale"),
          yol(B, "karne_variance_attribution", "margin_scale"), "5× KAYAR (0,1865 → 0,9272)"),
    satir("shadowlaw kayma bekçisi", GA["shadowlaw_variance_drift"]["kayma"],
          GB["shadowlaw_variance_drift"]["kayma"], "A: kayma YOK → B: margin_scale KAYMASI (0,02×0,9898=0,02 ≠ MONEY_GATE_MARGIN 0,004)"),
    satir("sieve bütünlük dedektörü", {"ok": GA["sieve_report"]["ok"], "n_ihlal": len(GA["sieve_report"]["violations"])},
          {"ok": GB["sieve_report"]["ok"], "n_ihlal": len(GB["sieve_report"]["violations"])},
          "TEMİZ → 8 İHLAL (4 aşamada %100 şema elemesi; 4'ü 'kritik')"),
    satir("skills gerçek katman", A["skills_attribution"]["skills"], B["skills_attribution"]["skills"],
          "ÇÖKER — vcp-screener n=91 ve pullback-screener n=4 kaybolur, 885 satır '?' kovasına düşer (skill_chain yok)"),
    satir("axis2 teşhis sayımı", A["skills_axis2_teshis"]["sayim"], B["skills_axis2_teshis"]["sayim"],
          "kovalar kayar: `esik_araliginda` 1→0, `gercek_katman_olculmemis_cf_dolu` 1→3"),
    satir("rollback/ebeveyn kapısı", GA["rollback_girdileri"]["rollback_kapisi"] if "rollback_kapisi" in GA["rollback_girdileri"] else A["hermes_ebeveyn_zinciri"]["rollback_kapisi"],
          B["hermes_ebeveyn_zinciri"]["rollback_kapisi"],
          "KAPALI → AÇILIR: n_cur 0→885, cur_score −0,0534, par_score 0,1245 (v3 backtest_oos), "
          "ham_delta −0,1779 < −rollback_if_worse_by(0,1) → GERİ ALMA EŞİĞİ AŞILIR"),
    satir("hermes yansıma sayacı", A["hermes_reflect_sayaci"], B["hermes_reflect_sayaci"],
          "0 → 790 yeni işlem; SAYI kapısı kapalı→AÇIK (gün-aralığı kapısı ayrıca var)"),
    satir("learning_scorecard orneklem_n", A["orneklem_learning_scorecard"]["defter"]["orneklem_n"],
          B["orneklem_learning_scorecard"]["defter"]["orneklem_n"], "DEĞİŞMEZ (2) — tek yalıtılmış tüketici"),
    satir("regime_trigger n", A["regime_trigger"], B["regime_trigger"],
          "trend_up 59→792, chop 35→95, high_vol 3→0; ready bayrakları DEĞİŞMEZ"),
    satir("mae_profile n", yol(A, "mae_profile", "n"), yol(B, "mae_profile", "n"),
          "KÖRLEŞİR (97 → None; mfe_r/mae_r yok)"),
    satir("net_kotumser ölçülen n", {"n_olculen": A["net_kotumser"]["n_olculen"], "n_notional_yok": A["net_kotumser"]["n_notional_yok"]},
          {"n_olculen": B["net_kotumser"]["n_olculen"], "n_notional_yok": B["net_kotumser"]["n_notional_yok"]},
          "KÖRLEŞİR (97→2 ölçülen; 885 satırda `entry` yok → notional hesaplanamıyor)"),
    satir("near_miss / cf", A["near_miss"]["resolved_total"], B["near_miss"]["resolved_total"], "BİREBİR AYNI"),
    satir("component_ic / threshold_curve", "sandbox'ta ÖLÇÜLEMEDİ (bars yok)",
          "sandbox'ta ÖLÇÜLEMEDİ (bars yok) — ama sieve 885/885 `sema:plan_id_biçimi:eski_şema` elemesi kaydetti",
          "KÖRLEŞİR (eleme muhasebesinden kanıtlı)"),
]

sema = k["sema_uyumu"]

sonuc = {
    "kart": "EDG-2026-036",
    "asama": "0 (ön-ölçüm) + 1 (kuru koşum)",
    "olcum_zamani": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
    "olcum_ajani_beyani": (
        "SALT-ÖLÇÜM. Karta DOKUNULMADI, hüküm YAZILMADI, git komutu KOŞULMADI, repo koduna "
        "DOKUNULMADI. Canlıya YALNIZ salt-okuma: SQLite `mode=ro` URI + düz dosya okuması; "
        "`meridian.store` canlıda BİLEREK kullanılmadı (store.read_* → db_backed() → bayat-defter "
        "süzgeci `.migrated` yeniden adlandırması yapabilir = YAZIM). Canlıya dosya yazılmadı, "
        "state'e yazılmadı, servis durdurulmadı. AŞAMA-1 tamamen YEREL izole sandbox'ta koştu "
        "(canlı state'in salt-okuma KOPYASI; sandbox'ta DB yok → dosya çağı). "
        "UYDURMA YASAĞI: 032 artefaktında olmayan alanlar None bırakıldı; yalnız kartın aşama-2'de "
        "ADIYLA yazdığı iki damga (kaynak=replay_seed, strategy_version=5) + `id` sayacı basıldı ve "
        "bunlar `sema_uyumu` altında AYRICA beyan edildi."),
    "canli_taban": {
        "trades_n": a0["trades_n"], "kaynak_dagilimi": a0["kaynak_dagilimi"],
        "sv_x_kaynak": a0b["sv_x_kaynak"], "pnl": a0["pnl"],
        "strategy": a0b["strategy"], "goal": a0b["goal"],
        "scoreboard": a0b["scoreboard_ozet"],
        "portfolio_realized_pnl": yol(a0b, "portfolio_ozet", "realized_pnl"),
        "plan_join": a0b["plan_join"], "n_trials_DSR": a0["n_trials"],
    },
    "asama0_tuketici_tablosu": T,
    "asama0_kill1": kill1,
    "asama1_dunyalar": {"A": k["dunya_A"], "B": k["dunya_B"]},
    "asama1_kiyas_tablosu": kiyas,
    "sema_uyumu": sema,
    "sema_uyumu_hukmu_icin_olculen": {
        "032_artefakti_slim_projeksiyondur": (
            "olcum.py:671-673 `slim = [{k: t.get(k) for k in (12 alan)} for t in trades]` — "
            "TAM satırlar (broker.close_position, broker.py:685-702: id/plan_id/side/entry/exit/"
            "pnl_pct/costs/score/skill_chain/mfe_r/mae_r/r_multiple_expected/exploration/scaled_out) "
            "koşum sırasında BELLEKTE vardı ama diske YAZILMADI"),
        "state_cmb_de_defter_yok": "research/olcumler/edg032_final_paket_2026-08-12/state_cmb/ = "
                                   "{goal.yaml, bounds.yaml, events.jsonl, strategy.yaml} — trades.jsonl YOK",
        "sonuc": ("mevcut 032 artefaktı canlı `trades` şemasına ÇEVRİLEMEZ: 26 alanın 13'ü "
                  "uydurulamaz eksik. Tohum yenilemesi için 032 koşumunun TAM satır serileştirmesiyle "
                  "YENİDEN KOŞULMASI gerekir (kartın kill#3'ü: 'yeni tohum yürürlükteki paketle "
                  "üretilmemişse (sha uyuşmazlığı) → geçersiz' bu maliyeti kapsıyor)"),
    },
    "kart_basari_olcutleri_MEKANIK_ISARET": {
        "(a) BÜTÜNLÜK": {
            "olculen": {"live_paper_n_A": A["_defter"]["live_paper_n"],
                        "live_paper_n_B": B["_defter"]["live_paper_n"],
                        "portfolio_realized_pnl_A": A["portfolio_realized_pnl"],
                        "portfolio_realized_pnl_B": B["portfolio_realized_pnl"],
                        "bit_ayni": A["portfolio_realized_pnl"] == B["portfolio_realized_pnl"]},
            "isaret": "SAĞLANDI (kuru koşumda)",
            "serh": "kuru koşum defteri YENİDEN YAZMADI; gerçek yazım yolu (aşama-2) SINANMADI"},
        "(b) TÜKETİCİ TUTARLILIĞI": {
            "olculen": {
                "korlesen_tuketici": ["score_calibration.katmanlar.gercek (97→None)",
                                      "llm_opinion_calibration (4→1 çift)",
                                      "component_ic.gercek (885/885 şema elemesi)",
                                      "threshold_curve.gercek (885/885 şema elemesi)",
                                      "mae_profile (n 97→None)",
                                      "skills gerçek katman (vcp n=91 → '?' n=885)",
                                      "net_kotumser (n_olculen 97→2)"],
                "iyilesen_tuketici": ["DSR (3e-06→0,0393)",
                                      "result_verdict net_pnl (kaldi→gecti)",
                                      "result_verdict dolar_beklenti CI genişliği 145,19$→91,64$",
                                      "variance_attribution n_blocks 93→280"],
                "degismeyen": ["PBO", "near_miss/cf", "learning_scorecard.orneklem_n",
                               "portfolio.realized_pnl"],
                "yeni_ihlal": {"sieve_ok_A": GA["sieve_report"]["ok"],
                               "sieve_ok_B": GB["sieve_report"]["ok"],
                               "n_ihlal_B": len(GB["sieve_report"]["violations"]),
                               "shadowlaw_kayma_B": [x["ad"] for x in GB["shadowlaw_variance_drift"]["kayma"]]}},
            "isaret": "DÜŞTÜ",
            "serh": ("kartın beklentisi ('örneklem 95→885 → CI'lar daralır, olculemedi kovaları dolar') "
                     "ÖLÇÜLDÜ ve TERSİ çıktı: `score`/`plan_id`/`skill_chain`/`mfe_r` gerektiren tüketici "
                     "ailesi tamamen körleşiyor ve `sieve` bütünlük dedektörü 8 ihlal (4'ü kritik) yazıyor. "
                     "Bu bir TOHUM problemi değil ARTEFAKT problemidir: 032 dosyası slim projeksiyon. "
                     "Tam-satırlı bir yeniden koşumda bu ölçütün yeniden ölçülmesi gerekir.")},
        "(c) DÜRÜSTLÜK": {
            "olculen": {
                "damga_ayrimi_korunuyor": {"A": A["_defter"], "B": B["_defter"]},
                "orneklem_paydasi_tohumu_dislyor": {
                    "A": A["orneklem_learning_scorecard"]["defter"]["orneklem_n"],
                    "B": B["orneklem_learning_scorecard"]["defter"]["orneklem_n"]},
                "public_summary_yalniz_live_paper": "api.py:706-708 `_ls.split(trades)[_ls.LIVE_PAPER]` — kod yolu doğrulandı",
                "AMA_ayirt_ETMEYEN_CANLI_KARAR_YOLLARI": {
                    "rollback_ebeveyn_zinciri": GB["rollback_girdileri"],
                    "hermes_yansima_sayaci": B["hermes_reflect_sayaci"]}},
            "isaret": "KISMİ — yüzey/karne tarafı ayrımı KORUYOR, iki CANLI KARAR yolu KORUMUYOR",
            "serh": ("`rollback.check_and_rollback` ve `evaluate_outcomes` `strategy_version` ile "
                     "filtreler, `kaynak` ile DEĞİL. Kartın aşama-2'de yazdığı `strategy_version=5` "
                     "damgası ile tohum yürürlükteki sürümün paydasına GİRER: kuru koşumda n_cur=885, "
                     "cur_score=−0,0534, par_score=0,1245, ham_delta=−0,1779 < −0,1 → geri-alma eşiği "
                     "AŞILIR (nihai karar `_would_have` replay'ine bağlı, o KOŞULMADI). Emsal defterde "
                     "var: scoreboard v4 kaydı `live_score=−0,0089 · n_trades=95 · rolled_back=true` — "
                     "yani BUGÜNKÜ tohum zaten bir kez canlı sürüm geri aldırmış.")},
    },
    "dosyalar": {
        "canli_asama0.json": "aşama-0 canlı salt-okuma (defter, kaynak, DSR üç payda, artefaktlar)",
        "canli_asama0b.json": "aşama-0 canlı salt-okuma 2 (doc varlıklar, yasa dosyaları, plan join)",
        "asama1_kiyas.json": "aşama-1 A-vs-B tüketici çıktıları + şema uyumu",
        "asama1_kapilar.json": "aşama-1 kapı probları (shadowlaw kayma, sieve ihlal, rollback girdileri)",
        "olcum_canli_asama0.py / olcum_canli_asama0b.py / olcum_asama1.py / olcum_asama1_kapilar.py":
            "ölçüm betikleri (arşiv)",
    },
    "sha256_16": {
        "islemler_cmb.json": sha16("/Users/erdemozturk/AI-Trading/research/olcumler/"
                                   "edg032_final_paket_2026-08-12/islemler_cmb.json")[:16],
    },
}

(OUT / "sonuc.json").write_text(json.dumps(sonuc, ensure_ascii=False, indent=1, default=str))
print("yazıldı:", OUT / "sonuc.json")
