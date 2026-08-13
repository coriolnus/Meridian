"""EDG-2026-036b — PLAN DEFTERİ KAPSAMA RAPORU (canlı `trade_plans` şemasına karşı).

UYDURMA YASAĞI: hiçbir eksik alan doldurulmaz. Her alan üç kovadan BİRİNE düşer:
  dolu        = replay plan defterinde ≥1 satırda None-olmayan değer (n_dolu raporlanır)
  yapisal_bos = replay ÜRETMEZ; CANLI YAZAR basar (kod satırıyla gerekçelendirilir)
  eksik       = şemada var, defterde YOK ∨ hepsi None — NEDEN adıyla yazılır

Canlı şema UYDURULMADI: `taban_kunye.json` içinde A1'den SALT-OKUMA ile alınan
`PRAGMA table_info(trade_plans)` (19 tipli kolon; `seq` PK ve `extra_json` taşıyıcı hariç) +
canlı 409 satırda FİİLEN gözlenen extra_json alanları.

kullanım: olcum_plan_kapsama.py <taban_kunye.json> <planlar_yenileme.json> <cikti.json> [etiket]
"""
import datetime as dt
import hashlib
import json
import re
import sys
from pathlib import Path

KUNYE = Path(sys.argv[1])
PLANP = Path(sys.argv[2])
OUT = Path(sys.argv[3])
ETIKET = sys.argv[4] if len(sys.argv) > 4 else "kontrolgd"

# CANLI YAZARIN bastığı prosedürel/canlı-yol alanları — replay bunları YAPISAL OLARAK üretemez.
CANLI_YAZAR = {
    "broker_status": ("loop.py:270-290 `_broker_status_yaz` — CANLI aynanın (Alpaca) dolum/ret "
                      "durumu. Replay'de 'broker durumu' kavramı YOK: dolum backtest içinde "
                      "anında ve kesindir. Canlı defterde 4/409 dolu."),
    "operator_onayi": ("loop.py:427 ONAY_ALANI + loop.py:533 `store.update_jsonl` — OPERATÖR "
                       "onay damgası. Replay'de operatör yoktur. Canlı defterde 4/409 dolu."),
    "llm_opinion": ("hermes.py:3313-3319 `store.update_jsonl('trade_plans.jsonl', _patch_plans)` "
                    "— LLM görüş damgası YALNIZ canlı yolda basılır. Backtest'te `llm_opinion` "
                    "hiç geçmez → HİÇBİR replay tohumu üretemez (kartın `hukum_duzeltmesi` "
                    "maddesindeki KALICI SINIR). Canlı defterde 8/409 dolu."),
    "p_win_shadow": ("loop.py:1777 `plan['p_win_shadow'] = pw` — gölge modelin canlı döngüde "
                     "bastığı kazanma olasılığı. Canlı defterde 42/409 dolu."),
    "dormant_setup": ("cf_backfill.py:82/101/109 — uyuyan-kurulum (dormant) tarama yolunun "
                      "damgası; canlı tarama üretir, replay yolu değil. Canlı 42/409 dolu."),
    "exploration": ("keşif (exploration) damgası — canlı boyutlandırma yolunda basılır "
                    "(api.py:3514/3627 okuyucu). Canlı defterde 1/409 dolu."),
}

plans = json.loads(PLANP.read_text())
kunye = json.loads(KUNYE.read_text())
n = len(plans)

# ---- canlı şema (ölçülmüş — uydurulmadı) ------------------------------------------------------
sql_cols = [c["ad"] for c in kunye["canli_trade_plans_sema"]
            if c["ad"] not in ("seq", "extra_json")]
canli_sayim = kunye["plan_alan_sayimi"]           # canlı 409 satırda FİİLEN gözlenen alanlar
extra_cols = [a for a in sorted(canli_sayim) if a not in sql_cols]
CANLI_SEMA = tuple(sql_cols + extra_cols)
canli_n = kunye["plans_n"]

# ---- replay plan defterinin alan sayımı -------------------------------------------------------
sayim: dict[str, dict] = {}
for p in plans:
    for k, v in p.items():
        b = sayim.setdefault(k, {"var": 0, "dolu": 0, "tipler": {}, "ornek": None,
                                 "degerler": set()})
        b["var"] += 1
        if v is not None:
            b["dolu"] += 1
            if b["ornek"] is None:
                b["ornek"] = v
        b["tipler"][type(v).__name__] = b["tipler"].get(type(v).__name__, 0) + 1
        if len(b["degerler"]) <= 12:
            try:
                b["degerler"].add(v if not isinstance(v, (list, dict)) else str(v)[:60])
            except TypeError:
                b["degerler"].add("<hashsiz>")

tablo, kova = {}, {"dolu": [], "yapisal_bos": [], "eksik": []}
for alan in CANLI_SEMA:
    c = sayim.get(alan)
    canli_dolu = (canli_sayim.get(alan) or {}).get("dolu", 0)
    ortak = {"canli_dolu_n": canli_dolu, "canli_n": canli_n,
             "canli_kapsama_pct": round(100.0 * canli_dolu / canli_n, 2) if canli_n else None}
    if alan in CANLI_YAZAR and (c is None or c["dolu"] == 0):
        tablo[alan] = {"kova": "yapisal_bos", "defterde_var": bool(c), "n_dolu": 0,
                       "neden": CANLI_YAZAR[alan], **ortak}
        kova["yapisal_bos"].append(alan)
    elif c is None:
        tablo[alan] = {"kova": "eksik", "defterde_var": False, "n_dolu": 0,
                       "neden": ("backtest.replay plan sözlüğünde (backtest.py:340-360 + 429-430) "
                                 "bu anahtar HİÇ üretilmiyor"), **ortak}
        kova["eksik"].append(alan)
    elif c["dolu"] == 0:
        tablo[alan] = {"kova": "eksik", "defterde_var": True, "n_dolu": 0, "tipler": c["tipler"],
                       "neden": f"satırda VAR ama 0/{n} dolu — uydurulmadı, None bırakıldı",
                       **ortak}
        kova["eksik"].append(alan)
    else:
        g = {"kova": "dolu", "defterde_var": True, "n_dolu": c["dolu"], "n_satir": n,
             "kapsama_pct": round(100.0 * c["dolu"] / n, 2) if n else None,
             "tipler": c["tipler"], "ornek": c["ornek"],
             "farkli_deger_n": (len(c["degerler"]) if len(c["degerler"]) <= 12
                                else ">12 (kardinalite yüksek)"),
             "deger_kumesi": (sorted(map(str, c["degerler"])) if len(c["degerler"]) <= 12
                              else None), **ortak}
        if alan in CANLI_YAZAR:
            g["canli_yazar_serhi"] = CANLI_YAZAR[alan]
        tablo[alan] = g
        kova["dolu"].append(alan)

fazla = sorted(set(sayim) - set(CANLI_SEMA))

# ---- KİMLİK BİÇİMİ + KORUNUM ------------------------------------------------------------------
bicim = re.compile(r"^P-\d{4}-\d{2}-\d{2}-[A-Za-z.\-]+$")
pid = [p.get("id") for p in plans]
kimlik = {"n_dolu": sum(1 for x in pid if x),
          "canli_bicim_uyan_n": sum(1 for x in pid if x and bicim.match(str(x))),
          "tekil_n": len({x for x in pid if x}), "ornek": pid[0] if pid else None,
          "canli_defterde_gozlenen_ek_bicim": ("canlı planların bir kısmı "
                                               "`P-TARIH-TICKER-SETUP` (dormant yolu, "
                                               "cf_backfill.py:101) — replay yalnız "
                                               "`P-TARIH-TICKER` üretir")}
verdict_dagilim: dict[str, int] = {}
for p in plans:
    v = str(p.get("gate_verdict"))
    verdict_dagilim[v] = verdict_dagilim.get(v, 0) + 1

out = {
    "kart": "EDG-2026-036", "adim": f"plan defteri kapsama raporu ({ETIKET})",
    "olcum_zamani": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
    "defter": {"yol": str(PLANP), "n_satir": n, "boyut_bayt": PLANP.stat().st_size,
               "sha256": hashlib.sha256(PLANP.read_bytes()).hexdigest(),
               "satir_anahtar_sirasi": list(plans[0].keys()) if plans else None,
               "anahtar_kumesi_cesidi": len({tuple(sorted(p.keys())) for p in plans})},
    "canli_sema": {"n_alan": len(CANLI_SEMA),
                   "sql_tipli_kolon": sql_cols,
                   "extra_json_gozlenen": extra_cols,
                   "kaynak": ("A1 SALT-OKUMA: PRAGMA table_info(trade_plans) (seq/extra_json "
                              "hariç 19 kolon) + canlı 409 satırda gözlenen extra_json alanları"),
                   "kaynak_damgasi_var_mi": ("HAYIR — `kaynak` plan şemasında HİÇ YOK "
                                             "(storage.py:99-105 PLANS kolonları; canlı 409/409 "
                                             "satırda alan yok). Plan defteri tohum/canlı ayrımı "
                                             "YAPAMAZ; ayrım YALNIZ `trades.kaynak`ta var.")},
    "kapsama_tablosu": tablo,
    "kova_ozeti": {k: {"n": len(v), "alanlar": v} for k, v in kova.items()},
    "defterde_fazla_canli_semada_yok": fazla,
    "kimlik_bicimi": kimlik,
    "gate_verdict_dagilimi": verdict_dagilim,
    "beyan": ("Bu dosya HÜKÜM İÇERMEZ. Kovalar mekaniktir. Hiçbir alan doldurulmadı; "
              "canlı-yazar alanları adıyla ve kod satırıyla yapısal-boş sayıldı."),
}
OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1, default=str))

print(f"\n===== EDG-036b PLAN KAPSAMA [{ETIKET}] =====")
print(f"defter: {PLANP}  satır={n}")
print(f"canlı şema {len(CANLI_SEMA)} alan (19 SQL kolon + {len(extra_cols)} extra_json)")
for kv in ("dolu", "yapisal_bos", "eksik"):
    print(f"  {kv:12s} n={len(kova[kv]):2d}  {kova[kv]}")
print(f"defterde fazla: {fazla}")
print(f"plan kimliği: {kimlik['n_dolu']}/{n} dolu, biçim-uyan={kimlik['canli_bicim_uyan_n']}, "
      f"tekil={kimlik['tekil_n']}, örnek={kimlik['ornek']}")
print(f"gate_verdict: {verdict_dagilim}")
print(f"yazıldı: {OUT}")
