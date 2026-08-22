"""WP1-23d KART-KANITI · ÖRNEKLEM ÖLÇÜMÜ (salt-okuma; state/'e ve canlıya yazmaz).

(A) CANLI: canli_ham.json (bu dizin) — gerçek stop dolumu sayımı:
    live_paper satırlarında exit_reason dağılımı; stop/stop_gap satırlarında
    alpaca_fill_price dolu mu, broker_teyit var mı (EDG-042 K3 ölçülebilirlik zinciri).
(B) REPLAY: donmuş edg032b tam defteri (research/olcumler/edg032b_tamsatir_2026-08-13/
    islemler_tam_kontrol.json, 885 satır) — exit_reason dağılımı + stop çıkışlarının
    P&L payı + çıkış notyoneli üzerinden "1 bps ek stop-slip = $X" duyarlılığı.
UYDURMA YASAĞI: hesaplanamayan alan None + neden.
"""
import json, os
from collections import defaultdict

D = os.path.dirname(os.path.abspath(__file__))
OUT = {"kalem": "WP1-23d kart-kaniti", "tarih": "2026-08-22"}

# ---------- (A) CANLI ----------
canli = json.load(open(os.path.join(D, "canli_ham.json")))
OUT["canli_cekim_zamani"] = canli.get("cekim_zamani")
OUT["canli_goal_slippage_bps"] = canli.get("goal_slippage_bps")
rows = canli["trades"]["satirlar"]
OUT["canli_toplam_satir"] = canli["trades"]["n"]

kaynak_sayim = defaultdict(int)
for r in rows:
    kaynak_sayim[r.get("kaynak")] += 1
OUT["canli_kaynak_dagilimi"] = dict(kaynak_sayim)

lp = [r for r in rows if r.get("kaynak") == "live_paper"]
er = defaultdict(int)
for r in lp:
    er[r.get("exit_reason")] += 1
OUT["canli_live_paper_n"] = len(lp)
OUT["canli_live_paper_exit_reason"] = dict(er)

STOP_REASONS = {"stop", "stop_gap", "koruma_stop"}   # EDG-042 K3 kovası tanımı
stop_rows = [r for r in lp if r.get("exit_reason") in STOP_REASONS]
def _ozet(r):
    return {k: r.get(k) for k in ("id", "ticker", "ts_close", "exit_reason", "exit",
                                  "alpaca_fill_price", "broker_teyit", "side")}
OUT["canli_stop_cikis_n"] = len(stop_rows)
OUT["canli_stop_cikis_satirlar"] = [_ozet(r) for r in stop_rows]
afp_dolu = [r for r in stop_rows if r.get("alpaca_fill_price") not in (None, "", 0)]
OUT["canli_stop_afp_dolu_n"] = len(afp_dolu)
teyitli = [r for r in afp_dolu if r.get("broker_teyit") == "teyitli"]
OUT["canli_stop_afp_dolu_teyitli_n"] = len(teyitli)
OUT["canli_stop_olculebilir_n_edg042_k3"] = len(teyitli)   # kill#3: teyitsiz kıyasa girmez

# hedef kovası (K2) kıyas için sayım
TGT = {"target", "target_gap", "koruma_hedef", "regime_flip", "time_stop"}
tgt_rows = [r for r in lp if r.get("exit_reason") in TGT]
tgt_afp = [r for r in tgt_rows if r.get("alpaca_fill_price") not in (None, "", 0)]
OUT["canli_k2_cikis_n"] = len(tgt_rows)
OUT["canli_k2_afp_dolu_n"] = len(tgt_afp)
OUT["canli_k2_afp_dolu_teyitli_n"] = len([r for r in tgt_afp if r.get("broker_teyit") == "teyitli"])

# ---------- (B) REPLAY (donmuş edg032b) ----------
LEDGER = "/Users/erdemozturk/AI-Trading/research/olcumler/edg032b_tamsatir_2026-08-13/islemler_tam_kontrol.json"
led = json.load(open(LEDGER))
OUT["replay_defter"] = LEDGER
OUT["replay_n"] = len(led)
top_pnl = sum(t["pnl_dollars"] for t in led)
OUT["replay_toplam_pnl"] = round(top_pnl, 2)

byr = defaultdict(lambda: {"n": 0, "pnl": 0.0, "exit_notyonel": 0.0, "neg_pnl": 0.0})
for t in led:
    b = byr[t["exit_reason"]]
    b["n"] += 1
    b["pnl"] += t["pnl_dollars"]
    b["exit_notyonel"] += t["qty"] * t["exit"]
    if t["pnl_dollars"] < 0:
        b["neg_pnl"] += t["pnl_dollars"]
tot_neg = sum(b["neg_pnl"] for b in byr.values())
tablo = {}
for k, b in sorted(byr.items(), key=lambda kv: -kv[1]["n"]):
    tablo[k] = {"n": b["n"],
                "n_pay_pct": round(100.0 * b["n"] / len(led), 2),
                "pnl": round(b["pnl"], 2),
                "neg_pnl": round(b["neg_pnl"], 2),
                "neg_pnl_pay_pct": round(100.0 * b["neg_pnl"] / tot_neg, 2) if tot_neg else None,
                "exit_notyonel": round(b["exit_notyonel"], 2),
                "bps_basina_dolar": round(b["exit_notyonel"] * 1e-4, 2)}
OUT["replay_exit_reason_tablosu"] = tablo
OUT["replay_toplam_neg_pnl"] = round(tot_neg, 2)

def _kova(adlar):
    n = sum(tablo[a]["n"] for a in adlar if a in tablo)
    pnl = sum(tablo[a]["pnl"] for a in adlar if a in tablo)
    neg = sum(tablo[a]["neg_pnl"] for a in adlar if a in tablo)
    noty = sum(tablo[a]["exit_notyonel"] for a in adlar if a in tablo)
    return {"n": n, "n_pay_pct": round(100.0 * n / len(led), 2),
            "pnl": round(pnl, 2), "neg_pnl": round(neg, 2),
            "neg_pnl_pay_pct": round(100.0 * neg / tot_neg, 2) if tot_neg else None,
            "exit_notyonel": round(noty, 2),
            "bps_basina_dolar": round(noty * 1e-4, 2)}

# 23d varsayımının DOĞRUDAN dokunduğu satırlar: bar-içi "stop" (eff_stop'ta dolmuş sayılır).
# "stop_gap" AYRI mekanik: açılış fiyatında dolmuş sayılır (gerçek bir baskı fiyatı) — varsayım
# "açılışta piyasa emri açılış fiyatını alır"dır, eff_stop iyimserliği değil; ama stop→MARKET
# tavansızlığı ona da değer. İkisi ayrı ayrı + birleşik verilir, karıştırılmaz.
OUT["replay_kova_stop_bar_ici"] = _kova(["stop"])
OUT["replay_kova_stop_gap"] = _kova(["stop_gap"])
OUT["replay_kova_stop_birlesik"] = _kova(["stop", "stop_gap"])
OUT["replay_kova_edg040_basabas_baglami"] = {
    "aciklama": "EDG-040 basabas 5-15 bps/BACAK (tum bacaklar). Bu tablo YALNIZ stop-cikis "
                "bacagina ek slip uygulansa kaci goturur sorusunun statik (yeniden-olcekleme) "
                "cevabini verir; motor tepkisi (boyut/secilim) ICINDE DEGIL — EDG-040'in kendi "
                "uyarisi aynen gecerli.",
    "stop_bar_ici_10bps_statik_dolar": round(_kova(["stop"])["exit_notyonel"] * 10e-4, 2),
    "stop_birlesik_10bps_statik_dolar": round(_kova(["stop", "stop_gap"])["exit_notyonel"] * 10e-4, 2),
    "edg032b_taban_pnl": round(top_pnl, 2),
}

# scaled_out stop satırları (kısmi satış sonrası runner stop'u — mekanik aynı, not için)
so = [t for t in led if t["exit_reason"] in ("stop", "stop_gap") and t.get("scaled_out")]
OUT["replay_stop_scaled_out_n"] = len(so)

json.dump(OUT, open(os.path.join(D, "sonuc.json"), "w"), indent=2, ensure_ascii=False)
print(json.dumps(OUT, indent=2, ensure_ascii=False))
