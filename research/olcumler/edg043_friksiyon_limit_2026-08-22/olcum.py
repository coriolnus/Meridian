"""EDG-2026-043 — friksiyon-koşullu limit kapısı · ölçüm koşumu (2026-08-22).

KART: research/cards/EDG-2026-043-friksiyon-kosullu-limit.yaml (OKU-DOKUNMA).
Ölçüm ajanı karta DOKUNMAZ; hükmü Rol-1 işler. Bu betik HÜKÜM VERMEZ, sayı getirir.
OKUMA KURALI (kart, donuk): bu ölçümden B4 hükmü ÇIKARILMAZ — EDG-042 bandı beklenir.

NE YAPAR: edg032b şasisini (C+mb @5R · 251 sembol · 2022-01→2026-07) İKİ knob BİRLİKTE ile
koşar: (1) slippage_bps ∈ {15,25,35} enjeksiyonu (EDG-040 reçetesi AYNEN), (2) giriş yasası
silahlı — limit_pct_cap=0,01 + limit_atr_mult=0,5 kod varsayılanı (exe006 deseni AYNEN;
goal.yaml'a DOKUNULMAZ). ALTI HÜCRE: slip × dolum {yalniz_acilis (A), dinlenen_limit (B)}.
Kapı-KAPALI hücreler YENİDEN KOŞULMAZ (kill#4): edg040'ın DONMUŞ defterlerinden okunur.

════════ TASARIM: İKİ DONMUŞ REÇETE BİRLEŞTİRİLDİ, YENİDEN İCAT YOK ════════
1) edg040_friksiyon_2026-08-22/olcum.py — slip enjeksiyonu (`config.goal` sarmalayıcı,
   cache_clear taşınır) + ÖZ-SINAMA (likidite terimi ayrıştırılmış, 1e-9, kill#2) + şasi
   bayt-kıyası (kill#1, n_endeks_satir DARALTILMIŞ istisnası aynen) + eşlenik ay-kümeli
   bootstrap (B=5000, seed=20260812, birim=AY).
2) exe006b_o1_kimlik_2026-08-22/olcum.py — yasa_silahli(cap) bağlam yöneticisi (süreç-içi,
   goal.yaml dokunulmaz) + MERIDIAN_DINLENEN_LIMIT bayrağı (backtest reload) + KOL KİMLİĞİ
   DAMGASI: `dolum_kurali` sonucun KENDİSİNDEN (`replay` sarmalanıp BacktestResult'tan)
   doğrulanır — damga tutmazsa hücre ölçüm DEĞİLDİR, koşum DURUR (kill#3).
Referans şasi (edg032b) modül olarak yüklenir, SANDBOX BU dizine çevrilir (ortak desen;
imza tahmini YASAK — exe006 2026-08-17 dersi). `kosum(run, smoke)` yolu OLDUĞU GİBİ çağrılır.

════════ ÖZ-SINAMANIN B-KOLU GENİŞLEMESİ (edg040'tan TEK sapma; motor koddan okundu) ════════
edg040'ın G2 rekonstrüksiyonu `base_fill = next_open·(1+slip)` varsayar. DİNLENEN LİMİT
dolumunda motor `next_open`ı YEREL olarak `_limit`e yeniden bağlar (broker.py:571-573:
`if bar_low <= _limit: next_open = _limit`) — kancanın kaydettiği `next_open` ARGÜMANI o
dolumlarda etkin taban fiyat DEĞİLDİR. Rekonstrüksiyon bu dalı motorun KENDİ fonksiyonuyla
kurar: `broker.entry_limit_price(trigger, atr, law)` (aritmetik uydurulmadı) + motorun kendi
dallanma koşulları (trigger>0 · next_open>limit · bar_low≤limit) çağrı anında yakalanan
girdilerle (plan['entry_trigger'], kw['atr'], kw['bar_low'], yürürlükteki entry_law())
birebir yeniden izlenir. Her satırda `dolum_yolu` (acilis|dinlenen_limit) raporlanır;
A hücrelerinde dinlenen_dolum_n == 0 beklenir (bar_low geçilmez — yapısal). Çıkış sınamaları
(Ç1/Ç2) her iki kolda DEĞİŞMEZ (çıkış yolu dolum kuralından bağımsız).

ŞASİ KAPISI (kill#1): kontrol@5 kapı-KAPALI (bayrak=0, yasa YAMASIZ = sandbox goal'ün
etkisiz yasası atr_mult=100/cap=0.04, slip sarmalayıcı AÇIK @5) → edg032b TAM artefaktıyla
sha256 BAYT-ÖZDEŞ + referansın kendi ozdeslik() kapısı. Kontrol, reload+damga+kanca telleri
AÇIKKEN koşulur: bayt-özdeşlik böylece şasiyi VE bu betiğin TÜM tel donanımının nötrlüğünü
birlikte kanıtlar. Kontrol hücre DEĞİLDİR, K harcamaz (K=6 yalnız kapı-AÇIK hücreler).

Δ+CI (Ö1): her slip'te Δ(açık−kapalı), kapalı kol edg040 DONMUŞ defterinden
(islemler_tam_slip{15,25,35}.json). EŞLENİK ay-kümeli bootstrap, iki kol AYNI ayı görür.
A−B farkı da raporlanır (23c model-boşluğu bandı friksiyon altında) + exe006 kol-farkı
deseni (kaçan/dolan-ek/ort-R). Defteri olmayan slip → CI=None + neden; nokta tahmini yine
raporlanır. KAPALI HÜCRE YENİDEN KOŞULMAZ.

NET P&L KANONİK ALANDAN: `performans.net_pnl_trades` (islem.net_pnl YOK — exe006 tuzağı).
PF tam defterden: Σ(pnl>0)/|Σ(pnl<0)| (EDG-037 tanımı; edg040'ta birebir doğrulandı).

DİSİPLİN: UYDURMA YASAĞI (ölçülemeyen None + neden) · YASA-4 (sessiz-yutma işaretli) ·
git KOŞULMAZ · state/ YAZILMAZ (şasi sandbox'a yönlendirir; canlı goal.yaml sha izlenir) ·
test suite KOŞULMAZ · motor dosyaları YAMASIZ (tüm kancalar süreç-içi ve bloklu).
"""
import contextlib
import datetime as dt
import hashlib
import importlib
import importlib.util
import json
import os
import pathlib
import sys

BURASI = pathlib.Path(__file__).resolve().parent
REPO = BURASI.parents[2]
REFERANS = REPO / "research" / "olcumler" / "edg032b_tamsatir_2026-08-13" / "olcum.py"
EDG032B = REFERANS.parent
EDG040 = REPO / "research" / "olcumler" / "edg040_friksiyon_2026-08-22"
sys.path.insert(0, str(REPO))

TABAN_BPS = 5.0                        # edg032b dünyasının kendi değeri (frozen goal: slippage_bps: 5)
SLIPLER = [15.0, 25.0, 35.0]           # kartın parameter_grid'i — DEĞİŞTİRİLEMEZ
TAVAN = 0.01                           # TEK tavan (kart: beyanlı sınır; tavan taraması DEĞİL)
KOLLAR = {"A": "yalniz_acilis", "B": "dinlenen_limit"}
BOOT_SEED = 20260812
BOOT_ITER = 5000
OZ_SINAMA_N = 20                       # edg040 kill#2 aynen: "ilk ≥20 giriş"
MOTOR_SHA_DOSYALAR = ("broker.py", "backtest.py")     # görev [6] + kart kill#5


def _sha_full(p: pathlib.Path) -> str | None:
    try:
        return hashlib.sha256(p.read_bytes()).hexdigest()
    except OSError:
        return None    # ölçülemedi (dosya yok/okunamadı)


def motor_sha() -> dict:
    d = {f: _sha_full(REPO / "meridian" / f) for f in MOTOR_SHA_DOSYALAR}
    d["state/goal.yaml"] = _sha_full(REPO / "state" / "goal.yaml")   # kill#5: canlı goal İZLENİR (yazılmaz)
    return d


def referans_modul():
    """Referans koşumu (edg032b) modül olarak yükler ve `SANDBOX`ını BU dizine çevirir.

    `__main__` bloğu `sys.argv`e bakıp iş yapıyor; modül olarak yüklerken argv geçici olarak
    boşaltılır ki içe aktarma bir koşum TETİKLEMESİN (iki reçetenin ortak deseni AYNEN)."""
    sp = importlib.util.spec_from_file_location("edg032b_ref", REFERANS)
    m = importlib.util.module_from_spec(sp)
    eski_argv = sys.argv
    sys.argv = [str(REFERANS)]
    try:
        sp.loader.exec_module(m)
    except SystemExit:                # `raise SystemExit(main())` deseni — içe aktarmada beklenir
        pass
    finally:
        sys.argv = eski_argv
    m.SANDBOX = BURASI                # ← artefakt koruması: referans dizine ASLA yazılmaz
    return m


@contextlib.contextmanager
def slip_enjekte(bps: float):
    """edg040 AYNEN: `config.goal` sarmalanır, dönen derin kopyaya `slippage_bps` yazılır.

    Dosya DEĞİŞMEZ (config sha'ları 032 kaydıyla bayt-aynı — şasinin kendi assert'i).
    `cache_clear` sarmalayıcıya taşınır (reload_config okuyucusu)."""
    from meridian import config as C
    asil = C.goal

    def sarmal():
        g = asil()
        g["slippage_bps"] = float(bps)
        return g

    sarmal.cache_clear = asil.cache_clear      # type: ignore[attr-defined]
    C.goal = sarmal
    try:
        yield
    finally:
        C.goal = asil


@contextlib.contextmanager
def yasa_silahli(cap: float):
    """exe006 AYNEN: limit bacağı `cap` tavanıyla silahlandırılır — YALNIZ bu süreçte, bu blokta.

    `state/goal.yaml` DEĞİŞMEZ (kill#5). `limit_atr_mult` kod varsayılanına (0.5) çekilir:
    canlıdaki/sandbox'taki 100.0 ATR bacağını yapısal olarak devre dışı bırakıyor ve o hâlde
    `cap` tek bağlayıcı olurdu. Kart bacağı SİLAHLI istiyor (universe, exe006 deseni AYNEN)."""
    from meridian import broker as B
    asil = B.entry_law
    yeni = {**asil(), "limit_atr_mult": B.ENTRY_LIMIT_ATR_MULT, "limit_pct_cap": cap}
    B.entry_law = lambda *a, **k: yeni
    try:
        yield yeni
    finally:
        B.entry_law = asil


@contextlib.contextmanager
def fiyat_kancalari(kayit: dict):
    """edg040 AYNEN + B-kolu genişlemesi: `PaperBroker.fill_entry`/`close_position` sarmalanır,
    HAM fiyat girdileri ve YUVARLANMAMIŞ dolum yakalanır. EK ALANLAR (dinlenen-limit
    rekonstrüksiyonu için, motor imzasından: broker.py:490-496): plan['entry_trigger'],
    kw['atr'], kw['bar_low'] + çağrı anında yürürlükteki entry_law() tavanları.

    Süreç-içi sınıf-yaması; motor DOSYASI yamasız (kill#5 sha kontrolü ayrıca kanıtlar)."""
    from meridian import broker as B
    asil_fill = B.PaperBroker.fill_entry
    asil_close = B.PaperBroker.close_position

    def fill(self, plan, next_open, ts, equity, **kw):
        pos = asil_fill(self, plan, next_open, ts, equity, **kw)
        if pos is not None:
            adv = kw.get("adv")
            law = B.entry_law()            # çağrı anında yürürlükteki yasa (silahlıysa silahlı)
            atr = kw.get("atr")
            bar_low = kw.get("bar_low")
            kayit["giris"].append({
                "ticker": pos.ticker, "ts": ts, "next_open": float(next_open),
                "adv": (float(adv) if adv else None),
                "fill_yuvarlanmamis": float(pos.entry), "qty": int(pos.qty),
                # rekonstrüksiyon girdileri (motor aritmetiğini birebir yeniden kurmak için):
                "stop": float(plan["stop"]), "size_r": float(plan["size_r"]),
                "size_mult": float(kw.get("size_mult", 1.0)), "equity": float(equity),
                "broker_slip": float(self.slip),
                # B-kolu genişlemesi — motorun kendi ifadesiyle (broker.py:537):
                "trigger_motor": float(plan.get("entry_trigger", next_open)),
                "atr": (float(atr) if atr is not None else None),
                "bar_low": (float(bar_low) if bar_low is not None else None),
                "law_pct_cap": float(law["limit_pct_cap"]),
                "law_atr_mult": float(law["limit_atr_mult"])})
        return pos

    def close(self, ticker, raw_exit, reason, ts):
        row = asil_close(self, ticker, raw_exit, reason, ts)
        kayit["cikis"].append({
            "ticker": ticker, "ts": ts, "raw_exit": float(raw_exit),
            "defter_exit": float(row["exit"]), "qty": int(row["qty"]),
            "broker_slip": float(self.slip), "reason": reason})
        return row

    B.PaperBroker.fill_entry = fill
    B.PaperBroker.close_position = close
    try:
        yield
    finally:
        B.PaperBroker.fill_entry = asil_fill
        B.PaperBroker.close_position = asil_close


ADV_CAP_YEREL = None                           # main'de broker.ADV_CAP_PCT'ten doldurulur (koddan)


def _fill_rekonstruksiyon(g: dict, s: float, cf: float, risk_pct: float) -> tuple[float, int, str]:
    """Motorun dolum aritmetiğinin BİREBİR kopyası (broker.py:537-612 + size_position:483-488),
    yalnız slip DIŞARIDAN verilir. edg040'ın dersi aynen: likidite payı ADV-kırpma-sonrası /
    NOMİNAL-kırpma-öncesi qty ile.

    B-KOLU DALI (bu kartın genişlemesi): motor `next_open > _limit` ve `bar_low <= _limit` ise
    tabanı `_limit`e bağlar (broker.py:571-573). `_limit` motorun KENDİ fonksiyonundan
    (`entry_limit_price`) — aritmetik uydurulmadı. Dönen üçüncü değer dolum yolu."""
    import math

    from meridian import broker as B
    next_open = g["next_open"]
    trigger = g["trigger_motor"]               # motor ifadesi: plan.get("entry_trigger", next_open)
    base = next_open
    yol = "acilis"
    if trigger > 0:
        lim = B.entry_limit_price(trigger, g["atr"],
                                  {"limit_pct_cap": g["law_pct_cap"],
                                   "limit_atr_mult": g["law_atr_mult"]})
        if next_open > lim:
            if g["bar_low"] is not None and g["bar_low"] <= lim:
                base = lim                     # dinlenen emir kendi fiyatından dolar (broker.py:573)
                yol = "dinlenen_limit"
            else:
                # motor bu dolumu REDDEDERDİ (entry_missed_limit); dolum yakalandıysa çelişki
                return float("nan"), 0, "CELISKI_red_olmaliydi"
    base_fill = base * (1.0 + s)
    risk_dollars = (g["size_r"] * max(0.0, g["size_mult"])) * risk_pct * g["equity"]
    per_share = base_fill - g["stop"]
    if per_share <= 0:
        return float("nan"), 0, yol            # motor reddederdi; dolum yakalandıysa çelişki
    qty = int(math.floor(risk_dollars / per_share))
    adv = g["adv"]
    if adv and adv > 0:
        cap = int(ADV_CAP_YEREL * adv)
        if qty > cap:
            qty = cap
        participation = qty / adv
        fill = base_fill * (1.0 + cf * participation)
    else:
        fill = base_fill
    return fill, qty, yol


def oz_sinama(kayit: dict, bps: float) -> dict:
    """kill#2 (edg040 AYNEN + dolum_yolu): enjeksiyonun FİYATA indiğinin kanıtı — kaynaktan
    yakalanan ham çiftler üstünde. G2 = motor aritmetiğinin birebir rekonstrüksiyonu; AYNI
    rekonstrüksiyon TABAN slip'le (5 bps) koşulup farkın açıldığı gösterilir (ayırt edicilik).
    Dönen sözlük mekanik sayımdır; geçti/düştü bayrağı taşır ama HÜKÜM Rol-1'in."""
    from meridian import broker as B
    global ADV_CAP_YEREL
    ADV_CAP_YEREL = float(B.ADV_CAP_PCT)       # sabitler KODDAN okunur, elle yazılmaz
    s = bps / 10000.0
    s_taban = TABAN_BPS / 10000.0
    cf = float(B.IMPACT_COEF)
    risk_pct = float(B.RISK_PCT_PER_R)
    girisler = kayit["giris"]
    cikislar = kayit["cikis"]

    def g_satir(g):
        fill = g["fill_yuvarlanmamis"]
        recon, q_etki, yol = _fill_rekonstruksiyon(g, s, cf, risk_pct)
        recon_taban, _, _ = _fill_rekonstruksiyon(g, s_taban, cf, risk_pct)
        rel = abs(fill / recon - 1.0) if recon == recon else None
        ham = fill / g["next_open"] - 1.0
        return {
            "ticker": g["ticker"], "ts": g["ts"],
            "G1_broker_slip_esit": g["broker_slip"] == s,
            "G2_recon_rel_fark": rel, "G2_gecti": (rel is not None and rel <= 1e-9),
            "recon_bayt_esit": recon == fill,
            "dolum_yolu": yol,
            "ayirt_edicilik_taban_rel_fark": (abs(fill / recon_taban - 1.0)
                                              if recon_taban == recon_taban else None),
            "qty_etki_recon": q_etki, "qty_nihai": g["qty"],
            "nominal_kirpildi": q_etki != g["qty"],
            "ham_bps": round(ham * 1e4, 6),
            # dinlenen dolumda taban next_open DEĞİL limit → ham_bps slip'ten sapar (beklenen);
            # likidite terimi ayrıştırması G2 rekonstrüksiyonunun içinde (acilis satırlarında
            # ham−s ≈ likidite terimi; dinlenen satırlarda ham "limitten dolum" farkını da taşır)
            "likidite_terimi_bps": (round((ham - s) * 1e4, 6) if yol == "acilis" else None)}

    def c_satir(c):
        beklenen = c["raw_exit"] * (1.0 - s)
        return {
            "ticker": c["ticker"], "ts": c["ts"], "reason": c["reason"],
            "C1_defter_exit_esit": round(beklenen, 4) == c["defter_exit"],
            "C1_mutlak_fark": abs(round(beklenen, 4) - c["defter_exit"]),
            "C2_fark": (1.0 - beklenen / c["raw_exit"]) - s,
            "C2_gecti": abs((1.0 - beklenen / c["raw_exit"]) - s) <= 1e-9,
            "broker_slip_esit": c["broker_slip"] == s,
            "raw_exit": c["raw_exit"], "defter_exit": c["defter_exit"]}

    g_detay = [g_satir(g) for g in girisler[:OZ_SINAMA_N]]
    c_detay = [c_satir(c) for c in cikislar[:OZ_SINAMA_N]]
    # TÜM yakalamalar da sınanır ve DÜŞENLER adıyla dökülür (edg040 dersi aynen)
    tum_g = [g_satir(g) for g in girisler]
    tum_c = [c_satir(c) for c in cikislar]
    g_bozuk = [d for d in tum_g if not (d["G1_broker_slip_esit"] and d["G2_gecti"])]
    c_bozuk = [d for d in tum_c if not (d["C1_defter_exit_esit"] and d["C2_gecti"])]

    n_g, n_c = len(g_detay), len(c_detay)
    gecti = (n_g >= OZ_SINAMA_N and n_c >= OZ_SINAMA_N
             and all(d["G1_broker_slip_esit"] and d["G2_gecti"] for d in g_detay)
             and all(d["C1_defter_exit_esit"] and d["C2_gecti"] for d in c_detay))
    return {
        "beklenen_slip": s, "impact_coef_koddan": cf,
        "adv_cap_koddan": ADV_CAP_YEREL, "risk_pct_koddan": risk_pct,
        "n_giris_yakalanan": len(girisler), "n_cikis_yakalanan": len(cikislar),
        "ilk20_giris": g_detay, "ilk20_cikis": c_detay,
        "n_ilk20_giris": n_g, "n_ilk20_cikis": n_c,
        "tum_girisler_G2_max_rel_fark": max((d["G2_recon_rel_fark"] for d in tum_g
                                             if d["G2_recon_rel_fark"] is not None), default=None),
        "tum_girisler_recon_bayt_esit_n": sum(1 for d in tum_g if d["recon_bayt_esit"]),
        "tum_girisler_nominal_kirpilan_n": sum(1 for d in tum_g if d["nominal_kirpildi"]),
        "dinlenen_dolum_n": sum(1 for d in tum_g if d["dolum_yolu"] == "dinlenen_limit"),
        "acilis_dolum_n": sum(1 for d in tum_g if d["dolum_yolu"] == "acilis"),
        "celiski_n": sum(1 for d in tum_g if d["dolum_yolu"] == "CELISKI_red_olmaliydi"),
        "ayirt_edicilik_taban_rel_min": min((d["ayirt_edicilik_taban_rel_fark"] for d in tum_g
                                             if d["ayirt_edicilik_taban_rel_fark"] is not None),
                                            default=None),
        "tum_bozuk_giris": g_bozuk, "tum_bozuk_cikis": c_bozuk,
        "tum_bozuk_giris_n": len(g_bozuk), "tum_bozuk_cikis_n": len(c_bozuk),
        "kill2_gecti": gecti,
        "olculemedi_nedeni": (None if (n_g >= OZ_SINAMA_N and n_c >= OZ_SINAMA_N) else
                              f"ilk-20 dolmadı: giriş={n_g} çıkış={n_c} — pencere kısa (duman?)"),
        "beyan": ("G2 = motor dolum aritmetiğinin (broker.py:537-612 + size_position) beklenen "
                  "slip'le BİREBİR rekonstrüksiyonu; likidite payı ADV-kırpma-sonrası/"
                  "nominal-kırpma-öncesi qty ile (edg040 dersi). B-KOLU: dinlenen dolumda taban "
                  "next_open değil entry_limit_price(trigger, atr, yürürlükteki yasa) — motorun "
                  "kendi fonksiyonu, aritmetik uydurulmadı; dolum_yolu her satırda açık. "
                  "ayirt_edicilik_* aynı rekonstrüksiyonun TABAN slip'le açması gereken farktır. "
                  "Ç1 defterin kendisine çivili; çıkış yolu dolum kuralından bağımsız."),
    }


def hucre_kos(ref, run: str, bps: float, kural: str, cap: float | None, smoke: bool) -> dict:
    """Tek koşum: bayrak kur + backtest reload → slip enjekte + kancalar (+ yasa) → ŞASİYİ ÇAĞIR
    → kol kimliği damgasını SONUÇTAN doğrula → öz-sınama + özet çıkar.

    `cap=None` = yasa YAMASIZ (kapı-KAPALI kontrol; sandbox goal'ün etkisiz yasası yürürlükte)."""
    os.environ["MERIDIAN_DINLENEN_LIMIT"] = "1" if kural == "dinlenen_limit" else "0"
    from meridian import backtest as BT
    importlib.reload(BT)                          # bayrak modül düzeyinde okunuyor (backtest.py:61)
    ref.backtest = BT                             # referans modül yeniden yüklenen BT'yi görsün
    if BT.DINLENEN_LIMIT != (kural == "dinlenen_limit"):
        raise AssertionError(f"bayrak kola uymadı: istenen={kural} DINLENEN_LIMIT={BT.DINLENEN_LIMIT}")

    # DAMGAYI YAKALA (exe006 Kritik-1 AYNEN): `BacktestResult.dolum_kurali` sonuç json'una
    # taşınmıyor → `replay` sarmalanıp damga kaynağından, sonucun KENDİSİNDEN okunur.
    yakalanan: dict = {}
    asil_replay = BT.replay

    def _sarmal(*a, **k):
        r = asil_replay(*a, **k)
        yakalanan["damga"] = getattr(r, "dolum_kurali", None)
        yakalanan["red_kimlik"] = getattr(r, "entry_reject_ids", None)
        return r

    BT.replay = _sarmal
    ref.HUCRELER.setdefault(run, {})              # {} = C+mb merkezi AYNEN (slot20 + 0,5R)
    kayit = {"giris": [], "cikis": []}
    yasa_kaydi = None
    try:
        with contextlib.ExitStack() as yigin:
            yigin.enter_context(slip_enjekte(bps))
            yigin.enter_context(fiyat_kancalari(kayit))
            if cap is not None:
                yasa_kaydi = yigin.enter_context(yasa_silahli(cap))
            ref.kosum(run, smoke=smoke)           # ŞASİ: referansın kendi yolu, dokunulmadan
    finally:
        BT.replay = asil_replay

    ek = "_smoke" if smoke else ""
    outdir = (BURASI / "smoke") if smoke else BURASI
    d = json.loads((outdir / f"sonuc_{run}{ek}.json").read_text())
    defter = json.loads((outdir / f"islemler_tam_{run}{ek}.json").read_text())

    perf = d.get("performans") or {}
    islem = d.get("islem") or {}
    # enjeksiyon şasinin kendi kaydında görünmeli (backtest.py:238 okuyucusunun kanıtı)
    kayitli_bps = ((d.get("replay") or {}).get("cost_model") or {}).get("slippage_bps")
    if kayitli_bps != float(bps):
        raise AssertionError(
            f"ENJEKSİYON ŞASİYE İNMEDİ: cost_model.slippage_bps={kayitli_bps} beklenen={bps} — DUR")

    # KOL KİMLİĞİ KAPISI (kill#3, exe006 Kritik-1 AYNEN): damgasız koşumda "bayrak açıktı ama
    # vaka yoktu" ile "bayrak hiç uygulanmadı" AYIRT EDİLEMEZ. Damga tutmazsa hücre ölçüm
    # DEĞİLDİR ve koşum DURUR — sessizce geçilmez.
    damga = yakalanan.get("damga")
    if damga != kural:
        raise AssertionError(
            f"KOL KİMLİĞİ TUTMADI: beklenen={kural} damga={damga} — hücre ölçüm DEĞİL, koşum DURUR")

    oz = oz_sinama(kayit, bps)
    (outdir / f"oz_sinama_{run}{ek}.json").write_text(
        json.dumps(oz, ensure_ascii=False, indent=1), encoding="utf-8")
    # HAM yakalama da diske: teşhis yeniden-koşum istemesin (edg040 dersi)
    (outdir / f"yakalama_{run}{ek}.json").write_text(
        json.dumps(kayit, ensure_ascii=False), encoding="utf-8")

    # PF tam defterden (şasi çıktısında yok; EDG-037 tanımı — edg040'ta birebir doğrulandı)
    poz = sum(float(t["pnl_dollars"]) for t in defter if float(t["pnl_dollars"]) > 0)
    neg = sum(float(t["pnl_dollars"]) for t in defter if float(t["pnl_dollars"]) < 0)
    pf = round(poz / abs(neg), 4) if neg < 0 else None
    pf_neden = None if neg < 0 else "kayıp bacağı boş (Σpnl<0 yok) — PF payda sıfır, TANIMSIZ"

    red_kimlik = {k: sorted(set(map(tuple, v)))
                  for k, v in (yakalanan.get("red_kimlik") or {}).items()}
    ozet = {
        "kosum": run, "slippage_bps": float(bps), "smoke": smoke,
        "dolum_kurali": kural, "dolum_kurali_damgasi": damga,
        "kol_kimligi_gecti": damga == kural,
        "yasa": ({k: yasa_kaydi[k] for k in ("limit_atr_mult", "limit_pct_cap", "version")}
                 if yasa_kaydi else {"silahli": False,
                                     "beyan": "yasa YAMASIZ — sandbox goal'ün etkisiz yasası"}),
        "hucre_sasi": d.get("hucre"),
        "islem_n": islem.get("n"),
        "net_pnl_trades": perf.get("net_pnl_trades"),     # KANONİK (islem.net_pnl YOK — bilinen tuzak)
        "net_pnl_equity": perf.get("net_pnl_equity"),
        "pf": pf, "pf_olculemedi_nedeni": pf_neden,
        "maxdd_kanonik": perf.get("maxdd_kanonik"), "maxdd_m2m": perf.get("maxdd_m2m"),
        "sharpe": perf.get("sharpe"), "sharpe_measurable": perf.get("sharpe_measurable"),
        "avg_r": perf.get("avg_r"), "win_rate": perf.get("win_rate"),
        "total_return": perf.get("total_return"),
        # kompozisyon/NO_GO sayaçları (kart features_asof; ham sayaçlar, hüküm yok)
        "kompozisyon": {
            "toplam_plan": islem.get("toplam_plan"),
            "silahlanan_plan": islem.get("silahlanan_plan"),
            "verdict_dagilim": islem.get("verdict_dagilim"),
            "nogo_neden_dagilim": islem.get("nogo_neden_dagilim"),
            "entry_rejects": islem.get("entry_rejects"),
            "exit_reason_dagilim": islem.get("exit_reason_dagilim"),
            "setup_bazinda": islem.get("setup_bazinda"),
        },
        "entry_missed_limit_olay": int((islem.get("entry_rejects") or {}).get("entry_missed_limit", 0)),
        "entry_missed_limit_distinkt_plan": len(red_kimlik.get("entry_missed_limit", [])),
        "red_kimlik_distinkt_n": {k: len(v) for k, v in red_kimlik.items()},
        "red_kimlik": red_kimlik,
        "dinlenen_dolum_n": oz["dinlenen_dolum_n"],       # A kolunda 0 beklenir (yapısal)
        "butunluk_gecerli": (d.get("butunluk") or {}).get("gecerli"),
        "kill3_temiz": (d.get("kill3_mtime") or {}).get("temiz"),
        "oz_sinama_kill2_gecti": oz["kill2_gecti"],
        "oz_sinama_olculemedi": oz["olculemedi_nedeni"],
        "cost_model_kaydi": (d.get("replay") or {}).get("cost_model"),
    }
    (outdir / f"hucre_{run}{ek}.json").write_text(
        json.dumps(ozet, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"  [{run}{ek}] bps={bps} kural={kural} damga={damga} cap={cap} "
          f"n={ozet['islem_n']} net={ozet['net_pnl_trades']} pf={pf} dd={ozet['maxdd_kanonik']} "
          f"missed={ozet['entry_missed_limit_olay']} dinlenen_dolum={ozet['dinlenen_dolum_n']} "
          f"kill2={oz['kill2_gecti']} bütünlük={ozet['butunluk_gecerli']} kill3={ozet['kill3_temiz']}",
          flush=True)
    return ozet


def sasi_kontrolu(ref, smoke: bool) -> dict:
    """kill#1 (edg040 AYNEN): kontrol@5 koşumu edg032b'nin DONMUŞ artefaktıyla BAYT-ÖZDEŞ mi?

    Üç dosya da tutmalı: islemler_tam, islemler(slim), seanslar. Ek olarak referansın KENDİ
    `ozdeslik()` kapısı da (032-cmb soyuna karşı) çağrılır. `n_endeks_satir` DARALTILMIŞ
    istisnası edg040'tan aynen (koşum-günü künyesi; pencere-içi dünya bayt kıyasıyla sınanır)."""
    ek = "_smoke" if smoke else ""
    yerel_dir = (BURASI / "smoke") if smoke else BURASI
    ref_dir = (EDG032B / "smoke") if smoke else EDG032B
    ciftler = {
        "islemler_tam": (yerel_dir / f"islemler_tam_kontrol{ek}.json",
                         ref_dir / f"islemler_tam_kontrol{ek}.json"),
        "islemler_slim": (yerel_dir / f"islemler_kontrol{ek}.json",
                          ref_dir / f"islemler_kontrol{ek}.json"),
        "seanslar": (yerel_dir / f"seanslar_kontrol{ek}.json",
                     ref_dir / f"seanslar_kontrol{ek}.json"),
    }
    sonuc = {}
    for ad, (y, r) in ciftler.items():
        sy, sr = _sha_full(y), _sha_full(r)
        sonuc[ad] = {"yerel_sha256": sy, "edg032b_sha256": sr,
                     "bayt_ozdes": (sy is not None and sy == sr),
                     "olculemedi_nedeni": (None if (sy and sr) else
                                           f"dosya okunamadı: yerel={bool(sy)} ref={bool(sr)}")}
    gecti = all(v["bayt_ozdes"] for v in sonuc.values())

    ozdeslik_032 = {"kostu": False, "gecti": None, "neden": None, "aciklanmis_fark": None}
    try:
        ref.ozdeslik(smoke=smoke)          # referansın kendi kapısı (032-cmb; exit 2 = düştü)
        ozdeslik_032 = {"kostu": True, "gecti": True, "neden": None, "aciklanmis_fark": None}
    except SystemExit as e:
        ozdeslik_032 = {"kostu": True, "gecti": (e.code in (None, 0)),
                        "neden": f"ozdeslik exit={e.code}", "aciklanmis_fark": None}
    # AÇIKLANMIŞ-FARK İSTİSNASI (edg040 AYNEN, DARALTILMIŞ): yalnız `replay` bloğu düştüyse VE
    # o blokta farklı TEK anahtar `n_endeks_satir` ise (koşum-günü önbellek uzunluğu künyesi).
    if ozdeslik_032["kostu"] and not ozdeslik_032["gecti"]:
        try:
            oz_dosya = json.loads((yerel_dir / f"ozdeslik{ek}.json").read_text())
            be = oz_dosya.get("sonuc_blok_esitligi") or {}
            dusen = [k for k, v in be.items() if not v]
            fark = (oz_dosya.get("blok_fark_ozet") or {}).get("replay") or {}
            y, r = fark.get("yerel") or {}, fark.get("ref_032") or {}
            farkli = [k for k in set(y) | set(r) if y.get(k) != r.get(k)]
            if (dusen == ["replay"] and farkli == ["n_endeks_satir"]
                    and all(oz_dosya.get("bayt_ozdeslik", {}).values())):
                ozdeslik_032["gecti"] = True
                ozdeslik_032["aciklanmis_fark"] = {
                    "alan": "replay.n_endeks_satir",
                    "yerel": y.get("n_endeks_satir"), "ref_032": r.get("n_endeks_satir"),
                    "neden": ("endeks önbelleği koşum-günü uzunluğu (pencereye kırpılmaz); "
                              "pencere-içi dünya defter/seans BAYT kıyasıyla sınandı ve ÖZDEŞ")}
        except (OSError, json.JSONDecodeError) as e:
            ozdeslik_032["neden"] += f" · fark dosyası okunamadı: {e}"   # sessiz-yutma değil
    out = {"bayt_kiyas_edg032b": sonuc, "kill1_bayt_gecti": gecti,
           "referans_ozdeslik_032cmb": ozdeslik_032,
           "kill1_gecti": bool(gecti and ozdeslik_032["gecti"])}
    (yerel_dir / f"sasi_kontrolu{ek}.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"  ŞASİ KONTROLÜ{ek}: bayt={gecti} ozdeslik032={ozdeslik_032['gecti']} → "
          f"{'GEÇTİ' if out['kill1_gecti'] else 'DÜŞTÜ — ölçüm DURUR'}", flush=True)
    return out


def delta_pnl_ci(taban_defter: list, hucre_defter: list, aylar: list[str]) -> dict:
    """edg040 AYNEN: EŞLENİK ay-kümeli bootstrap (edg035 yöntemi, exe006 O3 biçimi):
    birim = AY, iki kol AYNI ayı görür, B=5000, seed=20260812, yüzdelik CI. Dönen = hücre−taban."""
    import numpy as np
    M = len(aylar)

    def seri(defter):
        pnl = {a: 0.0 for a in aylar}
        disi = 0
        for t in defter:
            a = str(t["ts_open"])[:7]
            if a not in pnl:
                disi += 1                  # takvim dışı ay — sayılır, sessiz düşmez (YASA-4)
                continue
            pnl[a] += float(t.get("pnl_dollars") or 0.0)
        return np.array([pnl[a] for a in aylar], dtype=float), disi

    A_t, disi_t = seri(taban_defter)
    A_h, disi_h = seri(hucre_defter)
    rng = np.random.default_rng(BOOT_SEED)
    idx = np.arange(M)
    f = np.empty(BOOT_ITER)
    for i in range(BOOT_ITER):
        pick = rng.choice(idx, size=M, replace=True)     # EŞLENİK: aynı çekiliş iki kola
        f[i] = float(A_h[pick].sum()) - float(A_t[pick].sum())
    lo = round(float(np.percentile(f, 2.5)), 2)
    hi = round(float(np.percentile(f, 97.5)), 2)
    nokta = round(float(A_h.sum() - A_t.sum()), 2)
    return {"delta_pnl": nokta, "ci95": [lo, hi], "n_ay": M,
            "takvim_disi_islem": {"taban": disi_t, "hucre": disi_h},
            "sifir_disinda": ("evet (CI-alt > 0)" if lo > 0 else
                              "evet (CI-üst < 0)" if hi < 0 else "hayır (0 içinde)"),
            "yontem": ("EŞLENİK ay-kümeli bootstrap · yeniden örneklenen birim = AY "
                       "(iki kol AYNI ayı görür) · B=5000 · seed=20260812 · yüzdelik")}


def envanter_yap(smoke: bool) -> dict:
    """[1] ENVANTER: edg040 kapalı-kapı DONMUŞ kanıtının sayımı — hangi slip'in TAM işlem
    defteri var, edg040'ın kendi kill kapıları o hücrede ne demişti. KAPALI HÜCRE KOŞULMAZ."""
    out = {"kaynak_dizin": str(EDG040), "kapali_hucreler": {}, "beyan":
           ("CI, Δ(açık−kapalı) eşlenik ay-kümelidir ve kapalı kolun İŞLEM DEFTERİNİ ister. "
            "Defteri olmayan slip için CI=None+neden; nokta tahmini (hucre özetinden) yine "
            "raporlanır. Kapalı hücreler ASLA yeniden koşulmaz (kill#4 — çift sayım yasak).")}
    try:
        grid = json.loads((EDG040 / "sonuc_grid.json").read_text())
    except (OSError, json.JSONDecodeError) as e:
        grid = {}
        out["sonuc_grid_okunamadi"] = str(e)     # sessiz-yutma değil
    ek = "_smoke" if smoke else ""
    kaynak_dir = (EDG040 / "smoke") if smoke else EDG040
    slipler = [15] if smoke else [15, 25, 35]
    for s_int in slipler:
        run = f"slip{s_int}"
        p = kaynak_dir / f"islemler_tam_{run}{ek}.json"
        sha = _sha_full(p)
        rec: dict = {"islemler_tam_dosyasi": str(p), "mevcut": sha is not None, "sha256": sha}
        if sha is not None:
            defter = json.loads(p.read_text())
            rec["n_islem"] = len(defter)
        h = ((grid.get("hucreler") or {}).get(run) or {}) if not smoke else {}
        rec["edg040_hucre_ozeti"] = ({
            "islem_n": h.get("islem_n"), "net_pnl_trades": h.get("net_pnl_trades"),
            "pf": h.get("pf"), "maxdd_kanonik": h.get("maxdd_kanonik"),
            "oz_sinama_kill2_gecti": h.get("oz_sinama_kill2_gecti"),
            "butunluk_gecerli": h.get("butunluk_gecerli"), "kill3_temiz": h.get("kill3_temiz")}
            if h else None)
        rec["ci_kurulabilir"] = sha is not None
        rec["ci_kurulamaz_nedeni"] = (None if sha is not None else
                                      "kapalı kolun donmuş defteri yok — yeniden koşmak kill, "
                                      "CI kurulamaz")
        out["kapali_hucreler"][run] = rec
    if not smoke:
        out["edg040_kapilari"] = {
            "sasi_kill1_gecti": ((grid.get("sasi_kontrolu") or {}).get("kill1_gecti")),
            "kill4_motor_ayni": grid.get("kill4_motor_ayni"),
            "motor_sha256": grid.get("motor_sha256_once")}
    return out


def main() -> int:
    smoke = "--smoke" in sys.argv
    ek = "_smoke" if smoke else ""
    motor_once = motor_sha()
    ref = referans_modul()
    print(f"referans şasi yüklendi · SANDBOX={ref.SANDBOX} (edg032b dizinine YAZILMAZ)", flush=True)

    rapor: dict = {
        "kart": "EDG-2026-043", "smoke": smoke,
        "olcum_zamani": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "motor_sha256_once": motor_once,
        "tavan": TAVAN,
    }

    # [1] ENVANTER — kapalı-kapı donmuş kanıt sayımı (koşum yok, salt okuma)
    envanter = envanter_yap(smoke)
    rapor["envanter"] = envanter
    (BURASI / f"envanter{ek}.json").write_text(
        json.dumps(envanter, ensure_ascii=False, indent=1), encoding="utf-8")
    for run, rec in envanter["kapali_hucreler"].items():
        print(f"  ENVANTER {run}: defter={'VAR' if rec['mevcut'] else 'YOK'} "
              f"n={rec.get('n_islem')} ci_kurulabilir={rec['ci_kurulabilir']}", flush=True)

    # [2]/[3] KONTROL@5 kapı-KAPALI (yasa YAMASIZ, bayrak=0; slip teli + reload + damga teli
    # AÇIK — nötrlük de sınanır) → ŞASİ KAPISI (kill#1)
    kontrol = hucre_kos(ref, "kontrol", TABAN_BPS, "yalniz_acilis", cap=None, smoke=smoke)
    rapor["kontrol_slip5_kapali"] = kontrol
    sk = sasi_kontrolu(ref, smoke)
    rapor["sasi_kontrolu"] = sk
    if not sk["kill1_gecti"]:
        rapor["DURDU"] = "kill#1: kontrol@5 kapı-KAPALI edg032b ile bayt-özdeş DEĞİL — hücre koşulmadı"
        (BURASI / f"sonuc_grid{ek}.json").write_text(
            json.dumps(rapor, ensure_ascii=False, indent=1), encoding="utf-8")
        print("KILL#1 DÜŞTÜ — ölçüm DURDU (hücre koşulmadı); şasi teşhisi Rol-1'e", flush=True)
        return 2

    outdir = (BURASI / "smoke") if smoke else BURASI
    seanslar = json.loads((outdir / f"seanslar_kontrol{ek}.json").read_text())
    aylar = sorted({str(r["date"])[:7] for r in seanslar})

    # [4] ALTI HÜCRE (smoke: yalnız slip15_A + slip15_B — kablo): slip × {A, B}, cap=0,01
    bps_liste = [15.0] if smoke else SLIPLER
    hucreler: dict = {}
    for bps in bps_liste:
        for kol, kural in KOLLAR.items():
            run = f"slip{int(bps)}_{kol}"
            try:
                h = hucre_kos(ref, run, bps, kural, cap=TAVAN, smoke=smoke)
            except AssertionError as e:
                rapor["DURDU"] = f"{run}: {e}"    # kol kimliği / enjeksiyon kapısı — koşum DURUR
                rapor["hucreler"] = hucreler
                (BURASI / f"sonuc_grid{ek}.json").write_text(
                    json.dumps(rapor, ensure_ascii=False, indent=1), encoding="utf-8")
                print(f"KAPI DÜŞTÜ ({run}): {e} — ölçüm DURDU", flush=True)
                return 2
            hucreler[run] = h
            if not h["oz_sinama_kill2_gecti"] and not smoke:
                rapor["DURDU"] = f"kill#2: {run} öz-sınaması düştü — sonraki hücre koşulmadı"
                rapor["hucreler"] = hucreler
                (BURASI / f"sonuc_grid{ek}.json").write_text(
                    json.dumps(rapor, ensure_ascii=False, indent=1), encoding="utf-8")
                print(f"KILL#2 DÜŞTÜ ({run}) — ölçüm DURDU", flush=True)
                return 2
    rapor["hucreler"] = {k: {a: b for a, b in v.items() if a != "red_kimlik"}
                         for k, v in hucreler.items()}     # tam listeler hucre_*.json'da

    # [5] Δ+CI: her slip'te A−kapalı, B−kapalı (kapalı kol edg040 DONMUŞ defterinden) + A−B
    kaynak_dir = (EDG040 / "smoke") if smoke else EDG040
    delta: dict = {}
    for bps in bps_liste:
        s_int = int(bps)
        run_kapali = f"slip{s_int}"
        blok: dict = {}
        env = envanter["kapali_hucreler"].get(run_kapali) or {}
        kapali_defter = None
        if env.get("mevcut"):
            kapali_defter = json.loads(
                (kaynak_dir / f"islemler_tam_{run_kapali}{ek}.json").read_text())
        A_defter = json.loads((outdir / f"islemler_tam_slip{s_int}_A{ek}.json").read_text())
        B_defter = json.loads((outdir / f"islemler_tam_slip{s_int}_B{ek}.json").read_text())
        if kapali_defter is not None:
            blok["acikA_eksi_kapali"] = delta_pnl_ci(kapali_defter, A_defter, aylar)
            blok["acikB_eksi_kapali"] = delta_pnl_ci(kapali_defter, B_defter, aylar)
            blok["kapali_kaynak"] = {"dosya": env["islemler_tam_dosyasi"] if not smoke else
                                     str(kaynak_dir / f"islemler_tam_{run_kapali}{ek}.json"),
                                     "sha256": _sha_full(kaynak_dir /
                                                         f"islemler_tam_{run_kapali}{ek}.json")}
        else:
            neden = env.get("ci_kurulamaz_nedeni") or "kapalı defter envanterde yok"
            kapali_net = (env.get("edg040_hucre_ozeti") or {}).get("net_pnl_trades")
            blok["acikA_eksi_kapali"] = {
                "delta_pnl": (round(hucreler[f"slip{s_int}_A"]["net_pnl_trades"] - kapali_net, 2)
                              if None not in (hucreler[f"slip{s_int}_A"]["net_pnl_trades"], kapali_net)
                              else None),
                "ci95": None, "ci_olculemedi_nedeni": neden,
                "nokta_kaynagi": "hucre özet net_pnl_trades farkı (defter yok, CI kurulamadı)"}
            blok["acikB_eksi_kapali"] = {
                "delta_pnl": (round(hucreler[f"slip{s_int}_B"]["net_pnl_trades"] - kapali_net, 2)
                              if None not in (hucreler[f"slip{s_int}_B"]["net_pnl_trades"], kapali_net)
                              else None),
                "ci95": None, "ci_olculemedi_nedeni": neden,
                "nokta_kaynagi": "hucre özet net_pnl_trades farkı (defter yok, CI kurulamadı)"}
        # A−B farkı (23c model-boşluğu bandı friksiyon altında) — iki kol da BU koşumdan
        blok["A_eksi_B"] = delta_pnl_ci(B_defter, A_defter, aylar)
        # exe006 kol-farkı deseni: dinlenen kolda DOLAN ama açılış kolunda KAÇAN işlemler
        ak = {(t.get("ticker"), t.get("ts_open")) for t in A_defter}
        yalniz_b = [t for t in B_defter if (t.get("ticker"), t.get("ts_open")) not in ak]
        rler = [float(t["r_multiple"]) for t in yalniz_b if t.get("r_multiple") is not None]
        blok["kol_farki"] = {
            "kacan_A_olay": hucreler[f"slip{s_int}_A"]["entry_missed_limit_olay"],
            "kacan_A_distinkt_plan": hucreler[f"slip{s_int}_A"]["entry_missed_limit_distinkt_plan"],
            "dinlenen_kolda_DOLAN_ek_islem": len(yalniz_b),
            "ek_islem_ort_r": (round(sum(rler) / len(rler), 4) if rler else None),
            "ek_islem_ort_r_olculemedi": (None if rler else
                                          "ek işlem yok ya da r_multiple boş — ort-R ÖLÇÜLEMEDİ"),
            "ek_islem_n_r": len(rler)}
        delta[f"slip{s_int}"] = blok
        for ad in ("acikA_eksi_kapali", "acikB_eksi_kapali", "A_eksi_B"):
            b = blok[ad]
            print(f"  Δ[slip{s_int}·{ad}]: {b.get('delta_pnl')} CI95={b.get('ci95')} "
                  f"({b.get('sifir_disinda', b.get('ci_olculemedi_nedeni'))})", flush=True)
    rapor["delta"] = delta

    # [6] motor + canlı goal sha — koşum sonrası
    motor_sonra = motor_sha()
    rapor["motor_sha256_sonra"] = motor_sonra
    rapor["kill5_motor_goal_ayni"] = (motor_once == motor_sonra)
    if motor_once != motor_sonra:
        print("KILL#5: motor/goal sha koşum sırasında DEĞİŞTİ — ilgili hücreler geçersiz (raporda)",
              flush=True)

    yol = BURASI / f"sonuc_grid{ek}.json"
    yol.write_text(json.dumps(rapor, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"yazıldı: {yol}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
