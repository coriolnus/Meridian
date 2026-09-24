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
                     HESAPLANMAZ (karsiliksiz/teyitli SAYILMAZ). Teyitli satırda kartın
                     R2 (2026-08-24) BİRLEŞİK formülü AYNEN:
                         aleyhte_bps = yon_isareti × bps_delta(alpaca_fill_price, exit)
                         yon_isareti = −1  side=="long"  (kapanış SATIŞ  → DÜŞÜK dolum aleyhte = +)
                         yon_isareti = +1  side=="short" (kapanış ALIŞ   → YÜKSEK dolum aleyhte = +)
                     side bu iki değerin DIŞINDAysa (boş/None/bilinmeyen) bps HESAPLANMAZ,
                     satır olculemedi kovasına nedeniyle düşer — yön bilinmeden işaret seçmek
                     UYDURMADIR ve "varsayılan long" YASAKTIR (short satırı ters ölçerdi).
                     [TARİHÇE — 2026-08-22, Rol-1: donmuş kopyada (sha eaf45a03…) eksi işareti
                     YOKTU ve kartın işaret cümlesiyle çelişiyordu; kart kazandı. O düzeltme
                     ölçülebilir teyitli satır sayısı HÂLÂ 0 iken yapıldı ve YALNIZ LONG için
                     yazılıydı — açık kalem olarak damgalanmıştı.]
                     [R2 — 2026-08-24: kart açık kalemi KAPATTI (kart bloğu
                     `r2_short_isaret_sozlesmesi_2026_08_24`); bu dosya o kart metnini UYGULAR,
                     semantiği KENDİ TÜRETMEZ. Eşikler ve karar kuralları DEĞİŞMEDİ. Bugün
                     defterde short satır YOKTUR (893/893 side="long"; broker.py `side="long"`
                     SABİTİ yazar) — bu yüzden değişiklik gerçek örneklemde BAYT-ÖZDEŞ çıktı
                     üretir (ozdeslik.json) ve sentetik satırlarla sınanmıştır (sinama.json).]
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
import datetime as dt
import hashlib
import json
import random
import statistics as st
from pathlib import Path

DIZIN = Path(__file__).resolve().parent
HAM = DIZIN / "canli_ham.json"

K2_NEDEN = ("target", "target_gap", "regime_flip", "time_stop", "koruma_hedef")
K3_NEDEN = ("stop", "stop_gap", "koruma_stop")
#: P-3 / AYRIK — K1'i BÖLEN SINIR (operatör kararı 2026-08-31: "AYRIK, ts anahtarıyla").
#: 1345 sabitinin CANLIYA İNDİĞİ an. ÖLÇÜLDÜ, türetilmedi: A1'de `barclock.py` mtime
#: 2026-08-23T14:53:43Z (depodaki karşılığı d8030c0). Satır `ts` (GÖNDERİM anı) ile bölünür,
#: `pencere` damgasıyla DEĞİL: damgaya göre bölmek kaydırma öncesi 13 DAMGASIZ satırı her iki
#: koldan düşürürdü (EXE-009 kill#3 geriye dönük etiketlemeyi yasaklar) ve n=17'lik örneklem
#: 4'e inerdi. `ts` ile bölmek etiket YAZMAK değil, defterde zaten kayıtlı iki ÖLÇÜLMÜŞ olguyu
#: karşılaştırmaktır.
#: BEYANLI SINIR — TEK SINIR: bu reçete YALNIZ bir rejim sınırı tanır. İkinci bir pencere
#: değişikliği olursa reçete KARTSIZ GENİŞLETİLEMEZ (R2'nin short-satır beyanıyla aynı kalıp);
#: yeni sınır kart hükmüyle gelir, koda sessizce ikinci bir eşik eklenmez.
PENCERE_SINIRI = "2026-08-23T14:53:43+00:00"

#: Eşik DEĞERLERİ değişmedi (P-3 kova tanımını daralttı, eşiği değil). `giris_once` biçimsel
#: olarak aynı eşiği taşır — böylece kartın EDG-037'den miras DONUK damga metni ("n=X < eşik")
#: aynen basılır (operatör hükmü 2026-08-31: "damga biçimine dokunma, ayrı alan koy").
#: O kolun DONUKLUĞU damga metniyle değil `kalici_taban` alanıyla beyan edilir.
ESIK = {"giris_once": {"n": 30, "seans": 10},
        "giris_1345": {"n": 30, "seans": 10},
        "cikis_hedef": {"n": 15, "seans": 6},
        "cikis_stop": {"n": 15, "seans": 6}}
B, SEED = 5000, 20260812

#: Kartın R2 birleşik formülünün çarpanı (kart otoritesi; burada TÜRETİLMEZ, TAŞINIR).
#: Sözlükte OLMAYAN her yön "ölçülemedi"dir — varsayılan yön kabulü yasak (UYDURMA YASAĞI).
YON_ISARETI = {"long": -1, "short": +1}


def gonderim_kolu(ts_ham):
    """`ts` (gönderim anı) → "giris_once" | "giris_1345" | None.

    None = KOL BELİRLENEMEDİ. O satır hiçbir kola ATANMAZ, `olculemedi` kovasına nedeniyle
    düşer. "Varsayılan kol" kabulü YASAK — rejimi bilinmeden banda atamak, EXE-009 P-1'i doğuran
    sınıfın ta kendisidir (damga gönderim rejimini değil yazım rejimini söylüyordu) ve E2'nin
    ikame yasağıyla aynı sınıftır."""
    if not isinstance(ts_ham, str) or not ts_ham.strip():
        return None
    try:
        t = dt.datetime.fromisoformat(ts_ham.strip())
    except ValueError:
        return None
    if t.tzinfo is None:                 # saat dilimsiz damga kıyaslanamaz — uydurma yok
        return None
    return "giris_once" if t < dt.datetime.fromisoformat(PENCERE_SINIRI) else "giris_1345"


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
        _h = {"_hata": e2.get("_hata") or "entry_execution çekilemedi"}
        out["giris_once"], out["giris_1345"] = dict(_h), dict(_h)
    else:
        ayna_sub = [r for r in e2_rows
                    if r.get("motor") == "ayna" and r.get("karar") == "submitted"]
        fill_dolu = [r for r in ayna_sub if r.get("fill") is not None]
        kol_olcum = {"giris_once": [], "giris_1345": []}
        olculemedi = []
        for r in fill_dolu:
            v = r.get("fill_vs_resmi_acilis_bps")
            kayit = {"ticker": r.get("ticker"), "tarih": r.get("date"),
                     "plan_id": r.get("plan_id")}
            if v is None:                       # kill #2: tahmin YOK — olculemedi sayılır
                olculemedi.append({**kayit,
                                   "neden": "fill dolu ama fill_vs_resmi_acilis_bps boş — "
                                            "E2 ikame yasağı: payda yeniden türetilmez"})
                continue
            kol = gonderim_kolu(r.get("ts"))    # P-3: bölme anahtarı GÖNDERİM anı
            if kol is None:
                olculemedi.append({**kayit, "ts": r.get("ts"),
                                   "neden": "gönderim damgası `ts` okunamadı (boş/biçimsiz/saat "
                                            "dilimsiz) — kol belirlenemedi. Varsayılan kol kabulü "
                                            "YASAK (EXE-009 P-1 sınıfı); satır hiçbir kola "
                                            "atanmadı, bps hesaplanmadı."})
                continue
            kol_olcum[kol].append({"ticker": r.get("ticker"), "tarih": r.get("date"),
                                   "bps": float(v)})

        for kol in ("giris_once", "giris_1345"):
            out[kol] = betimleyici(kol_olcum[kol], kol, slip)
        # `giris_once` DONUKTUR — damga metni EDG-037 mirasıdır ve DEĞİŞMEDİ (operatör hükmü
        # 2026-08-31); donukluk AYRI alanla beyan edilir, yoksa "n=X < eşik" bir BEKLEYİŞ okunur.
        out["giris_once"]["kalici_taban"] = True
        out["giris_once"]["kalici_taban_beyan"] = (
            "kol DONUK — bu kolun icra yolu (EOD GTC → açılış dolumu) "
            f"{PENCERE_SINIRI}'de emekli oldu ve bir daha satır ÜRETMEYECEK. Kol eşik BEKLEMEZ "
            "ve hüküm üretemez: kalıcı betimleyici tabandır, 'yakında dolacak' diye sunulmaz. "
            "Damga biçimi EDG-037 mirasıdır ve korunmuştur; oradaki '< eşik' ifadesi bir "
            "bekleyişi DEĞİL, biçim yasasını gösterir.")
        out["giris_1345"]["kalici_taban"] = False
        # K DİSİPLİNİ: bölünme K'yı ÇARPMAZ. `parameter_grid` K TOPLAM = 3 kalır — `giris_1345`
        # `pending-042-giris` kaydının HALEFİDİR, `giris_once` bir deneme değil betimleyici
        # tabandır ve hüküm üretemediği için grid'de SAYILMAZ.
        out["giris_ortak"] = {
            "e2_toplam": e2.get("n"),
            "ayna_submitted": len(ayna_sub),
            "ayna_submitted_fill_bos": len(ayna_sub) - len(fill_dolu),
            "olculemedi": {"n": len(olculemedi), "satirlar": olculemedi},
            "pencere_siniri": PENCERE_SINIRI,
            "bolme_anahtari": "ts (gönderim anı) — `pencere` damgası DEĞİL",
            "k_disiplini": ("K TOPLAM = 3 korundu: giris_1345 `pending-042-giris` halefi, "
                            "giris_once grid'de sayılmaz (hüküm üretemez)"),
            "not": ("fill boş satır kovaya girmez (kart filtresi: fill dolu); dolmama oranı bu "
                    "kartın konusu değil. Havuzlanmış `giris` anahtarı P-3/AYRIK ile KALDIRILDI "
                    "— operatörün reddettiği karışık sayıyı üretmeye devam etmemesi için.")}

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
            # KARTIN BİRLEŞİK FORMÜLÜ (R2, 2026-08-24):
            #   aleyhte_bps = yon_isareti × bps_delta(alpaca_fill_price, exit)
            #   long  → −1 (kapanış SATIŞ: DÜŞÜK dolum aleyhte = +)
            #   short → +1 (kapanış ALIŞ : YÜKSEK dolum aleyhte = +)
            yon_ham = t.get("side")
            yon = yon_ham.strip().lower() if isinstance(yon_ham, str) else None
            isaret = YON_ISARETI.get(yon)
            if isaret is None:                  # R2: yön bilinmeden işaret UYDURULMAZ
                kova_olculemedi[kova].append(
                    {**kayit, "broker_teyit": teyit, "side": yon_ham,
                     "neden": (f"side={yon_ham!r} — kartın R2 işaret sözleşmesi yalnız "
                               "'long'/'short' için tanımlı; yön bilinmeden aleyhte işareti "
                               "seçilemez (varsayılan 'long' kabulü YASAK: short satırı ters "
                               "ölçerdi). bps hesaplanmadı.")})
                continue
            ham_v = bps_delta(t.get("alpaca_fill_price"), t.get("exit"))
            v = (None if ham_v is None else round(isaret * ham_v, 3))
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
                      "giris_once_n": out.get("giris_once", {}).get("n"),
                      "giris_1345_n": out.get("giris_1345", {}).get("n"),
                      "cikis_hedef_n": out.get("cikis_hedef", {}).get("n"),
                      "cikis_stop_n": out.get("cikis_stop", {}).get("n")},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
