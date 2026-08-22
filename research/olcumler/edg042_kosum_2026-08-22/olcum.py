"""EDG-2026-042 · gerçek friksiyon — BETİMLEYİCİ ARA-KOŞUM ölçümü (kart: status=registered,
"BETİMLEYİCİ ara-koşum her zaman yapılabilir (hüküm taşımaz, damgası açık)").

GİRDİ : canli_ham.json  (canli_cek.py çıktısı — salt-okunur canlı snapshot)
ÇIKTI : sonuc.json      (bu dizine; state/'e, karta, motor dosyalarına TEK BAYT yazılmaz)

KARTIN DONUK KURALLARI (research/cards/EDG-2026-042-gercek-friksiyon-tahmini.yaml) AYNEN:
  K1  giriş        : E2 satırı — motor=="ayna" VE karar=="submitted" VE fill dolu.
                     Ölçü = satırda KAYITLI `fill_vs_resmi_acilis_bps` (kill #1/#2: payda yeniden
                     türetilmez, tarihçe çekilmez, boş alan tahminle doldurulmaz → olculemedi).
                     İşaret sözleşmesi E2'nin kendisi: aleyhte = +.
  K2  çıkış-hedef  : trades satırı — alpaca_fill_price dolu VE kaynak=="live_paper" VE
                     exit_reason ∈ {target, target_gap, regime_flip, time_stop, koruma_hedef}.
  K3  çıkış-stop   : aynı filtre, exit_reason ∈ {stop, stop_gap, koruma_stop}.
  K2/K3 kill #3    : broker_teyit "teyitli" DEĞİLSE satır olculemedi kovasına düşer ve bps
                     HESAPLANMAZ (karsiliksiz/teyitli SAYILMAZ). Teyitli satırda:
                     bps = −bps_delta(alpaca_fill_price, exit) — kartın DÜZELTİLMİŞ formülü
                     aynen (universe/DÜZELTME 2026-08-22); işaret cümlesi aynen: "long satışta
                     DÜŞÜK dolum aleyhte = +". [REÇETE DÜZELTMESİ 2026-08-22, Rol-1: donmuş
                     kopyada (sha eaf45a03…) eksi işareti YOKTU ve kartın işaret cümlesiyle
                     çelişiyordu; kart kazanır. Düzeltme, ölçülebilir teyitli satır sayısı HÂLÂ
                     0 iken yapıldı — hiçbir sayıya bakılarak seçilmedi. Eşik/karar kuralı
                     DEĞİŞMEDİ. Kartın işaret cümlesi yalnız LONG için yazılmıştır; bugünkü
                     live_paper örnekleminin 8/8'i long. Short satır çıkarsa reçete kartsız
                     genişletilemez.]
  kill #4          : kaynak=="replay_seed" satırı kıyasa girmez (ayrı sayılır).
  kill #5          : kovalar birleştirilmez.
  kill #6          : alpaca_fill_beyan ölçüm değildir (yalnız sayımı raporlanır).
  kill #7          : tek seans kova örnekleminin >%40'ıysa şerh zorunlu.
  EŞİKLER (donuk) : K1 n≥30 VE ≥10 seans · K2/K3 n≥15 VE ≥6 seans. EŞİK ALTINDA CI HESAPLANMAZ;
                     damga AYNEN: "ÖLÇÜLEMEDİ (n=X < eşik) — sayılar betimleyicidir,
                     istatistiksel hüküm taşımaz." Eşik üstünde seans-kümeli bootstrap CI
                     (B=5000, seed=20260812, yüzdelik) hesaplanır ama BU KOŞUM HÜKÜM İŞLEMEZ —
                     success_metric karar kuralını Rol-1 işler, bu betik karar kuralı içermez.

Model-farkı sütunu: bps − goal.slippage_bps (koşum günü künyesi snapshot'tan; kart beyanlı
sınır 5: sabitlenmez, künyelenir). UYDURMA YASAĞI: ölçülemeyen her kalem None + neden.
"""
import hashlib
import json
import random
import statistics as st
from pathlib import Path

DIZIN = Path(__file__).resolve().parent
HAM = DIZIN / "canli_ham.json"

K2_NEDEN = ("target", "target_gap", "regime_flip", "time_stop", "koruma_hedef")
K3_NEDEN = ("stop", "stop_gap", "koruma_stop")
ESIK = {"giris": {"n": 30, "seans": 10},
        "cikis_hedef": {"n": 15, "seans": 6},
        "cikis_stop": {"n": 15, "seans": 6}}
B, SEED = 5000, 20260812


def bps_delta(a, b):
    """meridian.broker.bps_delta ile AYNI formül — motor dosyasına dokunmadan kopya:
    (a/b − 1) × 10000, taraflardan biri ölçülemezse None (0.0 = 'slipaj yoktu' yalanı olurdu)."""
    try:
        x, y = float(a), float(b)
    except (TypeError, ValueError):
        return None
    if y == 0:
        return None
    return round((x / y - 1.0) * 10000.0, 3)


def yuzdelik(sirali, q):
    """Yüzdelik (lineer interpolasyon, dahil-dahil) — küçük n'de statistics.quantiles
    exclusive uçları taşırır; betimleyici çıktı için median_low/high oyunu yerine tek tanım."""
    if not sirali:
        return None
    if len(sirali) == 1:
        return sirali[0]
    k = (len(sirali) - 1) * q
    alt, ust = int(k), min(int(k) + 1, len(sirali) - 1)
    return round(sirali[alt] + (sirali[ust] - sirali[alt]) * (k - int(k)), 3)


def betimleyici(satirlar, kova_adi, slip):
    """Kova başına kartın betimleyici çıktısı. `satirlar`: [{ticker, tarih, bps}] — bps HEPSİNDE
    dolu (olculemedi satırları buraya GİRMEZ, ayrı raporlanır)."""
    n = len(satirlar)
    esik = ESIK[kova_adi]
    if n == 0:
        return {"n": 0, "seans_sayisi": 0,
                "damga": (f"ÖLÇÜLEMEDİ (n=0 < {esik['n']}) — sayılar betimleyicidir, "
                          "istatistiksel hüküm taşımaz."),
                "esik": esik, "esik_dolu": False, "ci": None,
                "medyan_bps": None, "p25_bps": None, "p75_bps": None,
                "min_bps": None, "maks_bps": None,
                "en_buyuk_seans_payi_pct": None, "tek_seans_serhi_gerekli": None,
                "medyan_model_farki_bps": None, "satir_dokumu": []}
    bps = sorted(r["bps"] for r in satirlar)
    seanslar = {}
    for r in satirlar:
        seanslar.setdefault(r["tarih"], []).append(r["bps"])
    n_seans = len(seanslar)
    pay = max(len(v) for v in seanslar.values()) / n * 100.0
    esik_dolu = (n >= esik["n"] and n_seans >= esik["seans"])
    ci = None
    if esik_dolu:
        # seans-kümeli yüzdelik bootstrap (kart: B=5000, seed=20260812; kümeleme birimi=SEANS)
        rng = random.Random(SEED)
        kume = list(seanslar.values())
        medyanlar = []
        for _ in range(B):
            secim = [x for _ in kume for x in kume[rng.randrange(len(kume))]]
            medyanlar.append(st.median(secim))
        medyanlar.sort()
        ci = {"alt": yuzdelik(medyanlar, 0.025), "ust": yuzdelik(medyanlar, 0.975),
              "B": B, "seed": SEED, "kumeleme": "seans"}
        damga = f"n={n}, seans={n_seans} — eşik dolu; CI hesaplandı, HÜKÜM Rol-1'de (bu koşum betimleyicidir)."
    else:
        damga = (f"ÖLÇÜLEMEDİ (n={n} < {esik['n']}) — sayılar betimleyicidir, "
                 "istatistiksel hüküm taşımaz.")
    med = st.median(bps)
    return {"n": n, "seans_sayisi": n_seans, "damga": damga,
            "esik": esik, "esik_dolu": esik_dolu, "ci": ci,
            "medyan_bps": round(med, 3),
            "p25_bps": yuzdelik(bps, 0.25), "p75_bps": yuzdelik(bps, 0.75),
            "min_bps": bps[0], "maks_bps": bps[-1],
            "en_buyuk_seans_payi_pct": round(pay, 1),
            "tek_seans_serhi_gerekli": pay > 40.0,   # kill #7 — CI'sız betimleyicide de beyan edilir
            "medyan_model_farki_bps": (round(med - slip, 3) if slip is not None else None),
            "satir_dokumu": [{"ticker": r["ticker"], "tarih": r["tarih"], "bps": r["bps"],
                              "model_farki_bps": (round(r["bps"] - slip, 3)
                                                  if slip is not None else None)}
                             for r in sorted(satirlar, key=lambda x: (x["tarih"], x["ticker"]))]}


def main():
    ham = json.loads(HAM.read_text())
    slip_ham = ham.get("goal_slippage_bps")
    try:
        slip = float(slip_ham)
    except (TypeError, ValueError):
        slip = None                            # uydurma yok: model-farkı sütunu None kalır
    out = {"kart": "EDG-2026-042", "kosum": "betimleyici_ara_kosum",
           "kosum_izni": "kart status notu: 'operatör isterse BETİMLEYİCİ ara-koşum her zaman yapılabilir (hüküm taşımaz, damgası açık)'",
           "cekim_kunyesi": {"dosya": "canli_ham.json",
                             "sha256": hashlib.sha256(HAM.read_bytes()).hexdigest(),
                             "cekim_zamani": ham.get("cekim_zamani"),
                             "makine": ham.get("makine")},
           "model_varsayimi_bps": slip,
           "model_varsayimi_kaynak": "goal.slippage_bps (koşum günü, canlı snapshot)"}

    # ── K1 GİRİŞ — E2 ayna dolumları ─────────────────────────────────────────────
    e2 = ham.get("entry_execution") or {}
    e2_rows = e2.get("satirlar")
    if e2_rows is None:
        out["giris"] = {"_hata": e2.get("_hata") or "entry_execution çekilemedi"}
    else:
        ayna_sub = [r for r in e2_rows
                    if r.get("motor") == "ayna" and r.get("karar") == "submitted"]
        fill_dolu = [r for r in ayna_sub if r.get("fill") is not None]
        olcum, olculemedi = [], []
        for r in fill_dolu:
            v = r.get("fill_vs_resmi_acilis_bps")
            if v is None:                       # kill #2: tahmin YOK — olculemedi sayılır
                olculemedi.append({"ticker": r.get("ticker"), "tarih": r.get("date"),
                                   "plan_id": r.get("plan_id"),
                                   "neden": "fill dolu ama fill_vs_resmi_acilis_bps boş — "
                                            "E2 ikame yasağı: payda yeniden türetilmez"})
            else:
                olcum.append({"ticker": r.get("ticker"), "tarih": r.get("date"),
                              "bps": float(v)})
        out["giris"] = betimleyici(olcum, "giris", slip)
        out["giris"]["olculemedi"] = {"n": len(olculemedi), "satirlar": olculemedi}
        out["giris"]["kova_disi"] = {
            "e2_toplam": e2.get("n"),
            "ayna_submitted": len(ayna_sub),
            "ayna_submitted_fill_bos": len(ayna_sub) - len(fill_dolu),
            "not": "fill boş satır kovaya girmez (kart filtresi: fill dolu); dolmama oranı bu kartın konusu değil"}

    # ── K2/K3 ÇIKIŞ — trades, broker-teyit kapısı ────────────────────────────────
    tr = ham.get("trades") or {}
    tr_rows = tr.get("satirlar")
    if tr_rows is None:
        out["cikis_hedef"] = {"_hata": tr.get("_hata") or "trades çekilemedi"}
        out["cikis_stop"] = {"_hata": tr.get("_hata") or "trades çekilemedi"}
    else:
        lp = [t for t in tr_rows if t.get("kaynak") == "live_paper"]
        afp = [t for t in lp if t.get("alpaca_fill_price") is not None]
        kova_olcum = {"cikis_hedef": [], "cikis_stop": []}
        kova_olculemedi = {"cikis_hedef": [], "cikis_stop": []}
        siniflanamayan = []
        for t in afp:
            er = t.get("exit_reason")
            kova = ("cikis_hedef" if er in K2_NEDEN
                    else "cikis_stop" if er in K3_NEDEN else None)
            kayit = {"id": t.get("id"), "ticker": t.get("ticker"),
                     "tarih": (t.get("ts_close") or "")[:10], "exit_reason": er}
            if kova is None:                    # kill #5 gölgesi: bilinmeyen neden kovaya ezilmez
                siniflanamayan.append({**kayit, "neden": "exit_reason kartın iki kova listesinde de yok"})
                continue
            teyit = t.get("broker_teyit")
            if teyit != "teyitli":              # kill #3: teyitsiz satırın bps'i HESAPLANMAZ
                kova_olculemedi[kova].append(
                    {**kayit, "broker_teyit": teyit,
                     "neden": ("broker_teyit damgası basılmamış (alan boş) — teyitsiz satır "
                               "kıyasa giremez, karsiliksiz/teyitli SAYILMAZ" if teyit is None
                               else f"broker_teyit={teyit!r} — 'teyitli' değil, bps hesaplanmaz")})
                continue
            # KARTIN FORMÜLÜ (universe, DÜZELTME 2026-08-22): aleyhte_bps =
            # −bps_delta(alpaca_fill_price, exit). Long satışta DÜŞÜK dolum aleyhte = +.
            ham_v = bps_delta(t.get("alpaca_fill_price"), t.get("exit"))
            v = (None if ham_v is None else round(-ham_v, 3))
            if v is None:
                kova_olculemedi[kova].append(
                    {**kayit, "broker_teyit": teyit,
                     "neden": "bps_delta hesaplanamadı (taraflardan biri sayı değil/sıfır) — uydurma yok"})
            else:
                kova_olcum[kova].append({"ticker": t.get("ticker"),
                                         "tarih": kayit["tarih"], "bps": v})
        for kova in ("cikis_hedef", "cikis_stop"):
            out[kova] = betimleyici(kova_olcum[kova], kova, slip)
            out[kova]["olculemedi"] = {"n": len(kova_olculemedi[kova]),
                                       "satirlar": kova_olculemedi[kova]}
        out["cikis_ortak"] = {
            "trades_toplam": tr.get("n"),
            "kaynak_disi_replay_seed": sum(1 for t in tr_rows if t.get("kaynak") == "replay_seed"),
            "kaynak_disi_diger": sum(1 for t in tr_rows
                                     if t.get("kaynak") not in ("replay_seed", "live_paper")),
            "live_paper": len(lp),
            "live_paper_afp_bos": len(lp) - len(afp),
            "alpaca_fill_beyan_dolu": sum(1 for t in tr_rows
                                          if t.get("alpaca_fill_beyan") is not None),
            "siniflanamayan_exit_reason": siniflanamayan,
            "not": ("kill #4: replay_seed kıyasa girmedi · kill #6: alpaca_fill_beyan ölçüm değil, "
                    "yalnız sayıldı · afp boş live_paper satırı kovaya girmez (kart filtresi)")}

    (DIZIN / "sonuc.json").write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"yazildi": "sonuc.json",
                      "giris_n": out.get("giris", {}).get("n"),
                      "cikis_hedef_n": out.get("cikis_hedef", {}).get("n"),
                      "cikis_stop_n": out.get("cikis_stop", {}).get("n")},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
