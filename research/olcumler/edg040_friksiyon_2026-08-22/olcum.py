"""EDG-2026-040 — friksiyon-dayanıklılık taraması · ölçüm koşumu (2026-08-22).

KART: research/cards/EDG-2026-040-friksiyon-dayaniklilik.yaml (OKU-DOKUNMA).
Ölçüm ajanı karta DOKUNMAZ; hükmü (Ö1/Ö2/Ö3) Rol-1 işler. Bu betik HÜKÜM VERMEZ, sayı getirir.

NE YAPAR: C+mb @5R dünyasını (edg032b şasisi AYNEN) `goal.slippage_bps` ∈ {15, 25, 35} ile
yeniden KOŞAR (K=3). Motor YAMASIZ: friksiyon dolum fiyatına iner → stop mesafesi → boyut →
ısı → HANGİ işlemlerin doğduğu değişir. EDG-037'nin yeniden-ölçeklemesinden farkı tam budur.

════════ TASARIM: ŞASİ YENİDEN KURULMAZ, ÇAĞRILIR (exe006b deseni AYNEN) ════════
Referans koşum (edg032b/olcum.py) importlib ile modül olarak yüklenir, `SANDBOX`ı BU dizine
çevrilir (artefakt koruması YAPISAL: edg032b'nin donmuş kanıtına tek bayt yazılamaz) ve
`kosum(run, smoke)` yolu OLDUĞU GİBİ çağrılır. İmza tahmini YOK (exe006 2026-08-17 dersi).

════════ ENJEKSİYON YÜZEYİ (koddan okundu, varsayılmadı) ════════
`backtest.replay` maliyeti goal SÖZLÜĞÜNDEN okur: backtest.py:238 `slip = float(goal.get(
"slippage_bps", 5))` → :240 `PaperBroker(START_EQUITY, slip, commission)` → broker.py:452
`self.slip = slippage_bps/10000`. Şasi o sözlüğü `config.goal()` üzerinden alır (derin kopya)
ve edg032b'nin kendi enjeksiyonları da (slot/size/zarf) AYNI yüklenmiş sözlüğe yapılır —
dosyalar DEĞİŞMEZ, config sha'ları 032 kaydıyla bayt-aynı kalır. Bu betiğin eklediği tek şey,
`config.goal` sarmalayıcısıyla o sözlüğe `slippage_bps` yazmaktır (aynı yüzey, bir adım önce).
FRİKSİYONUN DEĞDİĞİ ÜÇ SATIR (kart universe; bugünkü motorda): giriş broker.py:587
`next_open*(1+slip)`, çıkış :741 `raw_exit*(1-slip)`, kısmi satış :710 `level*(1-slip)`.

════════ ÖZ-SINAMA KAYNAKTAN (kill#2) — defter alanı yuvarlıdır, likidite etkisi vardır ═══════
Defter `entry` alanı 4 haneye YUVARLI ve replay `adv=` geçirdiği için dolumda likidite etkisi
vardır (broker.py:600 `fill = base_fill*(1+IMPACT_COEF·qty/adv)`; donmuş edg032b defterinde
ölçüldü: giriş kalıntısı 5,0017–5,3639 bps ∈ [slip + etki + yuvarlama]). (fill/next_open − 1)
== slip eşitliği 1e-9 toleransta bu yüzden ANCAK kaynaktan, yuvarlanmamış dolumla ve likidite
terimi AYRIŞTIRILARAK sınanabilir: `PaperBroker.fill_entry`/`close_position` sarmalanır
(süreç-içi; motor DOSYASI yamasız), ham girdiler (next_open, adv, raw_exit) ve yuvarlanmamış
dolum (pos.entry) yakalanır. Sınamalar:
  G1  broker.slip == bps/10000 (birebir eşitlik — enjeksiyonun broker'a indiğinin kanıtı)
  G2  |fill/(next_open·(1+IMPACT_COEF·qty/adv)) − 1 − slip| ≤ 1e-9   (giriş; adv yoksa payda 1)
  Ç1  round(raw_exit·(1−slip), 4) == defter['exit']  (çıkış; defterin KENDİSİNE çivili —
      slip yanlış olsaydı 4 hanede tutmazdı)
  Ç2  |(1 − raw_exit·(1−slip)/raw_exit) − slip| ≤ 1e-9
Ham (fill/next_open − 1) − slip kalıntısı (= likidite terimi) AYRICA raporlanır — gizlenmez.
Alan adları DEFTERDEN OKUNDU: entry/exit/qty/ts_open/ts_close/pnl_dollars/r_multiple (tahmin yok).

NET P&L KANONİK ALANDAN: `performans.net_pnl_trades` (islem.net_pnl alanı YOK — exe006
2026-08-17 tuzağı). PF şasi çıktısında YOK → tam defterden hesaplanır:
Σ(pnl>0)/|Σ(pnl<0)| — EDG-037 tanımı; donmuş edg032b defterinde 1,1119 doğrulandı (birebir).

SIRALAMA (kill kriterleri zorlar):
  [1] --smoke: kablo sınaması (kontrol@5 + slip15 hücresi, 2022-01→06 penceresi)
  [2] kontrol@5 TAM koşum → ŞASİ KONTROLÜ: islemler_tam/islemler(slim)/seanslar edg032b ile
      sha256 BAYT-ÖZDEŞ + referansın kendi `ozdeslik()` kapısı (032-cmb'ye karşı).
      ÖZDEŞ DEĞİLSE DUR (kill#1) — hücre koşulmaz. Kontrol, enjeksiyon sarmalayıcısı AÇIKKEN
      (bps=5) koşulur: bayt-özdeşlik böylece şasiyi VE enjeksiyon yüzeyinin nötrlüğünü birlikte
      kanıtlar; hücreler tabandan YALNIZ sayıyla ayrılır.
  [3] hücreler slip {15, 25, 35} — her birinde öz-sınama (kill#2) + şasi bütünlüğü (kill#3,
      sonuç `butunluk.gecerli`) + motor sha (kill#4, şasi `kill3_mtime` + bu betiğin kendi
      koşum-öncesi/sonrası tam-sha kaydı)
  [4] ΔP&L + CI: hücre vs taban(slip=5) — EŞLENİK ay-kümeli bootstrap B=5000 seed 20260812,
      yeniden örneklenen birim = AY, iki kol AYNI ayı görür (edg035 yöntemi, exe006 O3 biçimi)
  [5] AŞAMA-2 KAPISI (kartta donuk): slip15'te C+mb net P&L > 0 İSE B@slip15 (slot5+1,0R —
      edg023/026 "B_slot5_r10" kolu) ve C(mb'siz)@slip15 (slot20+0,5R, mb süzülü) koşulur
      (K+=2) + Ö3 için ΔP&L(C−B)@15 CI'ı. DEĞİLSE koşulmaz, "kapı kapalı, K'dan 2 düşer".

MB'SİZ KOL NASIL (Aşama-2): bugünkü motorda mb ARMED_SETUPS'un KENDİSİNDE ve SONDA
(strategy.py:1050); edg026'nın C'si mb'siz motorla koşmuştu, kanal enjeksiyonu yoktu. Şasi
ARMED_SETUPS'a assert koyar (değiştirilemez). Bu yüzden mb, `strat.scan_entry` SARMALANARAK
süzülür: dönen sinyal.setup == momentum_burst → None. scan_entry İLK-EŞLEŞME sıralıdır ve mb
SONDADIR (strategy.py:1090 `for setup in ARMED_SETUPS + extra: if setup in by_setup: return`)
— yani mb ancak öncekiler eşleşmediğinde döner; süzmek, listeden çıkarmakla BİREBİR eşdeğerdir.
Şasi kancası scan_entry'yi BU sarmalın üstüne sarar → n_sinyal sayacı süzülmüş akışı sayar
(tutarlı). Kanıt: sonuçta mb_islem_n == 0 + süzülen sinyal sayacı raporlanır.

DİSİPLİN: UYDURMA YASAĞI (ölçülemeyen None + neden) · YASA-4 (sessiz-yutma işaretli) ·
git KOŞULMAZ · state/ YAZILMAZ (şasi kendi sandbox'ına yönlendirir) · test suite KOŞULMAZ ·
motor dosyalarına DOKUNULMAZ (tüm yamalar süreç-içi ve bloklu; şasi restorasyon-assert'li).
"""
import contextlib
import datetime as dt
import hashlib
import importlib.util
import json
import pathlib
import sys

BURASI = pathlib.Path(__file__).resolve().parent
REPO = BURASI.parents[2]
REFERANS = REPO / "research" / "olcumler" / "edg032b_tamsatir_2026-08-13" / "olcum.py"
EDG032B = REFERANS.parent
sys.path.insert(0, str(REPO))

TABAN_BPS = 5.0                        # edg032b dünyasının kendi değeri (frozen goal: slippage_bps: 5)
ASAMA1_BPS = [15.0, 25.0, 35.0]        # kartın parameter_grid'i — DEĞİŞTİRİLEMEZ (K=3)
BOOT_SEED = 20260812
BOOT_ITER = 5000
OZ_SINAMA_N = 20                       # kart kill#2: "ilk ≥20 giriş"
MOTOR_SHA_DOSYALAR = ("broker.py", "backtest.py")   # görev maddesi 7 (şasi kill3 zaten 8 dosya izler)


def _sha_full(p: pathlib.Path) -> str | None:
    try:
        return hashlib.sha256(p.read_bytes()).hexdigest()
    except OSError:
        return None    # ölçülemedi (dosya yok/okunamadı)


def motor_sha() -> dict:
    return {f: _sha_full(REPO / "meridian" / f) for f in MOTOR_SHA_DOSYALAR}


def referans_modul():
    """Referans koşumu (edg032b) modül olarak yükler ve `SANDBOX`ını BU dizine çevirir.

    `__main__` bloğu `sys.argv`e bakıp iş yapıyor; modül olarak yüklerken argv geçici olarak
    boşaltılır ki içe aktarma bir koşum TETİKLEMESİN (exe006b deseni AYNEN)."""
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
    """`config.goal`u sarmalar: dönen derin kopyaya `slippage_bps` yazılır — YALNIZ bu blokta.

    Dosya DEĞİŞMEZ (config sha'ları 032 kaydıyla bayt-aynı kalır — şasinin kendi assert'i).
    Sarmalayıcıya `cache_clear` da takılır: şasinin `config.reload_config()` çağrısı
    modül-global `goal.cache_clear()` okur; taşımasaydık koşum ilk adımda düşerdi."""
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
def fiyat_kancalari(kayit: dict):
    """`PaperBroker.fill_entry`/`close_position` sarmalanır — HAM fiyat girdileri ve
    YUVARLANMAMIŞ dolum yakalanır (öz-sınamanın tek dürüst kaynağı; defter alanı 4 hane yuvarlı).

    Süreç-içi sınıf-yaması; motor DOSYASI yamasız (kill#4 sha kontrolü bunu ayrıca kanıtlar).
    Parametre adları motor imzasıyla BİREBİR (broker.py:490/731) — ad uydurma yok."""
    from meridian import broker as B
    asil_fill = B.PaperBroker.fill_entry
    asil_close = B.PaperBroker.close_position

    def fill(self, plan, next_open, ts, equity, **kw):
        pos = asil_fill(self, plan, next_open, ts, equity, **kw)
        if pos is not None:
            adv = kw.get("adv")
            kayit["giris"].append({
                "ticker": pos.ticker, "ts": ts, "next_open": float(next_open),
                "adv": (float(adv) if adv else None),
                "fill_yuvarlanmamis": float(pos.entry), "qty": int(pos.qty),
                # rekonstrüksiyon girdileri (motor aritmetiğini birebir yeniden kurmak için):
                "stop": float(plan["stop"]), "size_r": float(plan["size_r"]),
                "size_mult": float(kw.get("size_mult", 1.0)), "equity": float(equity),
                "broker_slip": float(self.slip)})
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


@contextlib.contextmanager
def mb_suz(sayac: dict):
    """AŞAMA-2 mb'siz kol: `strat.scan_entry` sonucu momentum_burst ise None'a süzülür.

    scan_entry İLK-EŞLEŞME sıralı ve mb SONDA (strategy.py:1090) → süzme, ARMED_SETUPS'tan
    çıkarmakla birebir eşdeğer; ARMED_SETUPS'a dokunulmaz (şasinin kendi assert'leri geçerli
    kalır). Şasi kancası bu sarmalın ÜSTÜNE sarar → n_sinyal süzülmüş akışı sayar (tutarlı)."""
    from meridian import backtest as BT
    asil = BT.strat.scan_entry

    def sarmal(*a, **k):
        sig = asil(*a, **k)
        if sig is not None and getattr(sig, "setup", None) == "momentum_burst":
            sayac["suzulen_mb_sinyal"] = sayac.get("suzulen_mb_sinyal", 0) + 1
            return None
        return sig

    BT.strat.scan_entry = sarmal
    try:
        yield
    finally:
        BT.strat.scan_entry = asil


def _fill_rekonstruksiyon(g: dict, s: float, cf: float, risk_pct: float) -> tuple[float, int]:
    """Motorun dolum aritmetiğinin BİREBİR kopyası (broker.py:587-600 + size_position:483-488),
    yalnız slip DIŞARIDAN verilir. Aynı işlem sırası, aynı floor — float'ta özdeşlik beklenir.

    NOT (ilk turun dersi, 2026-08-22): dolum fiyatındaki likidite payı NİHAİ qty ile DEĞİL,
    ADV-kırpması sonrası / NOMİNAL-kırpma ÖNCESİ qty ile hesaplanır (nominal kırpma
    broker.py:607'de fiyattan SONRA gelir). İlk sürüm pos.qty (nihai) kullandığı için
    nominal-kırpılan girişlerde sahte fark üretti (5/20, hepsi artı yönde — tutarlı)."""
    import math
    base_fill = g["next_open"] * (1.0 + s)
    risk_dollars = (g["size_r"] * max(0.0, g["size_mult"])) * risk_pct * g["equity"]
    per_share = base_fill - g["stop"]
    if per_share <= 0:
        return float("nan"), 0                 # motor reddederdi; dolum yakalandıysa çelişki
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
    return fill, qty


ADV_CAP_YEREL = None                           # main'de broker.ADV_CAP_PCT'ten doldurulur (koddan)


def oz_sinama(kayit: dict, bps: float) -> dict:
    """kill#2: enjeksiyonun FİYATA indiğinin kanıtı — kaynaktan yakalanan ham çiftler üstünde.

    G2 = beklenen slip'le motor aritmetiğinin birebir rekonstrüksiyonu; ayrıca AYNI
    rekonstrüksiyon TABAN slip'le (5 bps) koşulup farkın BÜYÜK çıktığı gösterilir (ayırt
    edicilik: sınama yanlış slip'i yakalayabilir). Dönen sözlük mekanik sayımdır; geçti/düştü
    bayrağını da taşır ama HÜKÜM Rol-1'in."""
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
        recon, q_etki = _fill_rekonstruksiyon(g, s, cf, risk_pct)
        recon_taban, _ = _fill_rekonstruksiyon(g, s_taban, cf, risk_pct)
        rel = abs(fill / recon - 1.0) if recon == recon else None
        ham = fill / g["next_open"] - 1.0
        return {
            "ticker": g["ticker"], "ts": g["ts"],
            "G1_broker_slip_esit": g["broker_slip"] == s,
            "G2_recon_rel_fark": rel, "G2_gecti": (rel is not None and rel <= 1e-9),
            "recon_bayt_esit": recon == fill,
            "ayirt_edicilik_taban_rel_fark": (abs(fill / recon_taban - 1.0)
                                              if recon_taban == recon_taban else None),
            "qty_etki_recon": q_etki, "qty_nihai": g["qty"],
            "nominal_kirpildi": q_etki != g["qty"],
            "ham_bps": round(ham * 1e4, 6),
            "likidite_terimi_bps": round((ham - s) * 1e4, 6)}   # gizlenmez (beyanlı)

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
    # TÜM yakalamalar da sınanır ve DÜŞENLER adıyla dökülür (ilk turda 7 çıkış anonim kalmıştı)
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
        "ayirt_edicilik_taban_rel_min": min((d["ayirt_edicilik_taban_rel_fark"] for d in tum_g
                                             if d["ayirt_edicilik_taban_rel_fark"] is not None),
                                            default=None),
        "tum_bozuk_giris": g_bozuk, "tum_bozuk_cikis": c_bozuk,
        "tum_bozuk_giris_n": len(g_bozuk), "tum_bozuk_cikis_n": len(c_bozuk),
        "kill2_gecti": gecti,
        "olculemedi_nedeni": (None if (n_g >= OZ_SINAMA_N and n_c >= OZ_SINAMA_N) else
                              f"ilk-20 dolmadı: giriş={n_g} çıkış={n_c} — pencere kısa (duman?)"),
        "beyan": ("G2 = motor dolum aritmetiğinin (broker.py:587-600 + size_position) beklenen "
                  "slip'le BİREBİR rekonstrüksiyonu; likidite payı ADV-kırpma-sonrası/"
                  "nominal-kırpma-öncesi qty ile (ilk turun dersi). ayirt_edicilik_* aynı "
                  "rekonstrüksiyonun TABAN slip'le koştuğunda AÇMASI gereken farktır. Kartın "
                  "(fill/next_open−1)==slip formülü sabit-slip varsayar; ham kalıntı "
                  "likidite_terimi_bps sütununda AÇIK. Ç1 defterin kendisine çivili."),
    }


def hucre_kos(ref, run: str, bps: float, smoke: bool) -> dict:
    """Tek hücre: slip enjekte → fiyat kancaları tak → ŞASİYİ ÇAĞIR → öz-sınama + özet çıkar."""
    ref.HUCRELER.setdefault(run, HUCRE_TANIMLARI[run])
    kayit = {"giris": [], "cikis": []}
    mb_sayac: dict = {}
    mbsiz = run.startswith("Cmbsiz")
    with contextlib.ExitStack() as yigin:
        yigin.enter_context(slip_enjekte(bps))
        yigin.enter_context(fiyat_kancalari(kayit))
        if mbsiz:
            yigin.enter_context(mb_suz(mb_sayac))
        ref.kosum(run, smoke=smoke)               # ŞASİ: referansın kendi yolu, dokunulmadan

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

    oz = oz_sinama(kayit, bps)
    (outdir / f"oz_sinama_{run}{ek}.json").write_text(
        json.dumps(oz, ensure_ascii=False, indent=1), encoding="utf-8")
    # HAM yakalama da diske: teşhis yeniden-koşum istemesin (ilk turda 7 çıkış anonim kalmıştı)
    (outdir / f"yakalama_{run}{ek}.json").write_text(
        json.dumps(kayit, ensure_ascii=False), encoding="utf-8")

    # PF tam defterden (şasi çıktısında yok; EDG-037 tanımı — donmuş defterde 1,1119 doğrulandı)
    poz = sum(float(t["pnl_dollars"]) for t in defter if float(t["pnl_dollars"]) > 0)
    neg = sum(float(t["pnl_dollars"]) for t in defter if float(t["pnl_dollars"]) < 0)
    pf = round(poz / abs(neg), 4) if neg < 0 else None
    pf_neden = None if neg < 0 else "kayıp bacağı boş (Σpnl<0 yok) — PF payda sıfır, TANIMSIZ"

    ozet = {
        "kosum": run, "slippage_bps": float(bps), "smoke": smoke,
        "hucre_sasi": d.get("hucre"),
        "mbsiz_kol": mbsiz, "suzulen_mb_sinyal": (mb_sayac.get("suzulen_mb_sinyal") if mbsiz else None),
        "mb_islem_n": islem.get("mb_islem_n"),
        "islem_n": islem.get("n"),
        "net_pnl_trades": perf.get("net_pnl_trades"),     # KANONİK (islem.net_pnl YOK — bilinen tuzak)
        "net_pnl_equity": perf.get("net_pnl_equity"),
        "pf": pf, "pf_olculemedi_nedeni": pf_neden,
        "maxdd_kanonik": perf.get("maxdd_kanonik"), "maxdd_m2m": perf.get("maxdd_m2m"),
        "sharpe": perf.get("sharpe"), "sharpe_measurable": perf.get("sharpe_measurable"),
        "avg_r": perf.get("avg_r"), "win_rate": perf.get("win_rate"),
        "total_return": perf.get("total_return"),
        # kompozisyon ayrıştırması (kart: hasar FİYAT mı SEÇİLİM mi — ham sayaçlar, hüküm yok)
        "kompozisyon": {
            "toplam_plan": islem.get("toplam_plan"),
            "silahlanan_plan": islem.get("silahlanan_plan"),
            "verdict_dagilim": islem.get("verdict_dagilim"),
            "nogo_neden_dagilim": islem.get("nogo_neden_dagilim"),
            "entry_rejects": islem.get("entry_rejects"),
            "exit_reason_dagilim": islem.get("exit_reason_dagilim"),
            "setup_bazinda": islem.get("setup_bazinda"),
            "silahli_plan_size_r": islem.get("silahli_plan_size_r"),
        },
        "butunluk_gecerli": (d.get("butunluk") or {}).get("gecerli"),
        "kill3_temiz": (d.get("kill3_mtime") or {}).get("temiz"),
        "oz_sinama_kill2_gecti": oz["kill2_gecti"],
        "oz_sinama_olculemedi": oz["olculemedi_nedeni"],
        "cost_model_kaydi": (d.get("replay") or {}).get("cost_model"),
    }
    (outdir / f"hucre_{run}{ek}.json").write_text(
        json.dumps(ozet, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"  [{run}{ek}] bps={bps} n={ozet['islem_n']} net={ozet['net_pnl_trades']} "
          f"pf={pf} dd={ozet['maxdd_kanonik']} sharpe={ozet['sharpe']} "
          f"kill2={oz['kill2_gecti']} bütünlük={ozet['butunluk_gecerli']} kill3={ozet['kill3_temiz']}")
    return ozet


HUCRE_TANIMLARI = {
    # AŞAMA-1: C+mb dünyası AYNEN (merkez slot20 + 0,5R + 5R zarf) — tek değişken slip
    "kontrol": {},          # şasinin kendi tabanı (edg032b) — bayt-özdeşlik kapısının nesnesi
    "slip15": {}, "slip25": {}, "slip35": {},
    # AŞAMA-2 (koşullu): edg023/026 kolları — B = slot5 + 1,0R ("B_slot5_r10");
    # C(mb'siz) = slot20 + 0,5R, mb scan-süzülü ("C_slot20_r05"in bugünkü motordaki karşılığı)
    "B_slip15": {"slot": 5, "size": 1.0},
    "Cmbsiz_slip15": {},
}


def sasi_kontrolu(ref, smoke: bool) -> dict:
    """kill#1: kontrol@5 koşumu edg032b'nin DONMUŞ artefaktıyla BAYT-ÖZDEŞ mi (sha256)?

    Üç dosya da tutmalı: islemler_tam (birincil işlem defteri), islemler (slim), seanslar.
    Ek olarak referansın KENDİ `ozdeslik()` kapısı da (032-cmb soyuna karşı) çağrılır."""
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
    # AÇIKLANMIŞ-FARK İSTİSNASI (2026-08-22 duman bulgusu, DARALTILMIŞ): referans ozdeslik'in
    # `replay` bloğundaki `n_endeks_satir` KOŞUM-GÜNÜ künyesidir — `len(index)` TAM önbellek
    # uzunluğudur, pencereye kırpılmaz; canlı sistem 2026-08-13'ten beri ~5 seans eklemiş
    # (1403→1408). Pencere-içi dünya değişimi ZATEN defter/seans BAYT kıyasıyla sınanıyor
    # (kill#1'in kart tanımı) ve o kıyas bu istisnadan etkilenmez. İstisna YALNIZ şu durumda
    # işler: ozdeslik'in düşen TEK bloğu `replay` VE o blokta farklı TEK anahtar
    # `n_endeks_satir`. Başka her fark yine DURDURUR.
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
          f"{'GEÇTİ' if out['kill1_gecti'] else 'DÜŞTÜ — ölçüm DURUR'}")
    return out


def delta_pnl_ci(taban_defter: list, hucre_defter: list, aylar: list[str]) -> dict:
    """EŞLENİK ay-kümeli bootstrap (edg035 yöntemi, exe006 O3 biçimi): birim = AY,
    iki kol AYNI ayı görür, B=5000, seed=20260812, yüzdelik CI."""
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


def main() -> int:
    smoke = "--smoke" in sys.argv
    ek = "_smoke" if smoke else ""
    motor_once = motor_sha()
    ref = referans_modul()
    print(f"referans şasi yüklendi · SANDBOX={ref.SANDBOX} (edg032b dizinine YAZILMAZ)")

    rapor: dict = {
        "kart": "EDG-2026-040", "smoke": smoke,
        "olcum_zamani": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "motor_sha256_once": motor_once,
    }

    # [1]+[2] KONTROL@5 (enjeksiyon yüzeyi AÇIK — nötrlük de sınanır) → ŞASİ KONTROLÜ (kill#1)
    kontrol = hucre_kos(ref, "kontrol", TABAN_BPS, smoke)
    rapor["kontrol_slip5"] = kontrol
    sk = sasi_kontrolu(ref, smoke)
    rapor["sasi_kontrolu"] = sk
    if not sk["kill1_gecti"]:
        rapor["DURDU"] = "kill#1: kontrol@5 edg032b ile bayt-özdeş DEĞİL — hücre koşulmadı"
        (BURASI / f"sonuc_grid{ek}.json").write_text(
            json.dumps(rapor, ensure_ascii=False, indent=1), encoding="utf-8")
        print("KILL#1 DÜŞTÜ — ölçüm DURDU (hücre koşulmadı); şasi teşhisi Rol-1'e")
        return 2

    outdir = (BURASI / "smoke") if smoke else BURASI
    taban_defter = json.loads((outdir / f"islemler_tam_kontrol{ek}.json").read_text())
    seanslar = json.loads((outdir / f"seanslar_kontrol{ek}.json").read_text())
    aylar = sorted({str(r["date"])[:7] for r in seanslar})

    # [3]+[4] AŞAMA-1 hücreleri (smoke'ta yalnız slip15 — kablo; tamda üçü de)
    bps_liste = [15.0] if smoke else ASAMA1_BPS
    hucreler = {}
    delta = {}
    for bps in bps_liste:
        run = f"slip{int(bps)}"
        h = hucre_kos(ref, run, bps, smoke)
        hucreler[run] = h
        if not h["oz_sinama_kill2_gecti"] and not smoke:
            rapor["DURDU"] = f"kill#2: {run} öz-sınaması düştü — sonraki hücre koşulmadı"
            rapor["hucreler"] = hucreler
            (BURASI / f"sonuc_grid{ek}.json").write_text(
                json.dumps(rapor, ensure_ascii=False, indent=1), encoding="utf-8")
            print(f"KILL#2 DÜŞTÜ ({run}) — ölçüm DURDU")
            return 2
        hd = json.loads((outdir / f"islemler_tam_{run}{ek}.json").read_text())
        delta[run] = delta_pnl_ci(taban_defter, hd, aylar)
        print(f"  Δ[{run}]: {delta[run]['delta_pnl']} CI95={delta[run]['ci95']} "
              f"({delta[run]['sifir_disinda']})")
    rapor["hucreler"] = hucreler
    rapor["delta_pnl_vs_taban"] = delta

    # [5] AŞAMA-2 KAPISI (kartta donuk): slip15'te C+mb net P&L > 0 ise B + C(mb'siz) @15
    if smoke:
        rapor["asama2"] = {"degerlendirilmedi": "duman koşumu — kapı yalnız TAM koşumda işler"}
    else:
        net15 = hucreler["slip15"]["net_pnl_trades"]
        if net15 is None:
            rapor["asama2"] = {"kapi": "ÖLÇÜLEMEDİ", "neden": "slip15 net_pnl_trades None",
                               "kosuldu": False, "K_notu": "K'dan 2 düşer (koşulamadı)"}
        elif net15 > 0:
            print(f"  AŞAMA-2 KAPISI AÇIK (slip15 net={net15} > 0) → B@15 + C(mb'siz)@15 (K+=2)")
            a2 = {}
            for run in ("B_slip15", "Cmbsiz_slip15"):
                a2[run] = hucre_kos(ref, run, 15.0, smoke)
            bd = json.loads((outdir / "islemler_tam_B_slip15.json").read_text())
            cd = json.loads((outdir / "islemler_tam_Cmbsiz_slip15.json").read_text())
            o3 = delta_pnl_ci(bd, cd, aylar)        # ΔP&L(C − B) @ slip15 (Ö3 girdisi)
            rapor["asama2"] = {"kapi": f"AÇIK (slip15 net={net15} > 0)", "kosuldu": True,
                               "hucreler": a2, "O3_delta_pnl_C_eksi_B_slip15": o3}
            print(f"  Ö3 Δ(C−B)@15: {o3['delta_pnl']} CI95={o3['ci95']} ({o3['sifir_disinda']})")
        else:
            rapor["asama2"] = {"kapi": f"KAPALI (slip15 net={net15} ≤ 0)", "kosuldu": False,
                               "K_notu": "kapı kapalı, K'dan 2 düşer (kart success_metric, donuk)"}
            print(f"  AŞAMA-2 KAPISI KAPALI (slip15 net={net15} ≤ 0) — K'dan 2 düşer")

    motor_sonra = motor_sha()
    rapor["motor_sha256_sonra"] = motor_sonra
    rapor["kill4_motor_ayni"] = (motor_once == motor_sonra)
    if motor_once != motor_sonra:
        print("KILL#4: motor sha koşum sırasında DEĞİŞTİ — ilgili hücreler geçersiz (raporda)")

    yol = BURASI / f"sonuc_grid{ek}.json"
    yol.write_text(json.dumps(rapor, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"yazıldı: {yol}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
