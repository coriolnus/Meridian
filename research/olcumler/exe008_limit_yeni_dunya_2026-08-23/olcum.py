"""EXE-2026-008 — limit bacağı hüküm sınamasının B1-DÜNYASI tekrarı · ölçüm koşumu (2026-08-23).

KART: research/cards/EXE-2026-008-limit-bacagi-yeni-dunya.yaml (OKU-DOKUNMA; hüküm Rol-1'in).
Ölçüm ajanı karta DOKUNMAZ; bu betik HÜKÜM VERMEZ, sayı getirir. H1/H2/H3 okuması Rol-1'in işidir.

NE YAPAR: EXE-2026-006'nın K=8 grid'ini (4 tavan × 2 dolum kuralı) B1-dünyasında (edg032c
tabanı; ARMED üçlü) yeniden koşar. Bacak YALNIZ ölçüm kolunda silahlandırılır; `state/goal.yaml`
ve motor dosyaları DEĞİŞMEZ.

════════ ŞASİ: YENİDEN KURULMAZ, ÇAĞRILIR (edg032c/edg046/exe006 deseni AYNEN) ════════
edg032b/olcum.py importlib ile modül olarak yüklenir, `SANDBOX`ı BU dizine çevrilir (artefakt
koruması YAPISAL: ne edg032b ne exe006 ne edg032c dizinine tek bayt yazılabilir),
`ARMED_BEKLENEN`i B1 yasasına çevrilir (edg032c'nin BEYANLI TEK UYARLAMASI AYNEN; motor
ARMED_SETUPS B1'den saparsa koşum BAŞLAMADAN durur) ve `kosum(run, smoke)` yolu OLDUĞU GİBİ
çağrılır. HİÇBİR parametre enjeksiyonu YOK (9 koşum da merkez hücre: slot 20 · size 0,5R ·
zarf 5R).

════════ İKİ SİLAH (EXE-006'dan AYNEN devralınır) ════════
(1) `yasa_silahli(cap)`: `broker.entry_law` süreç-içi yamayla {limit_atr_mult: 0.5 (kod
    varsayılanı — canlıdaki 100.0 ATR bacağını yapısal öldürüyor, kart bacağı SİLAHLI istiyor),
    limit_pct_cap: cap} döndürür. `state/goal.yaml` DEĞİŞMEZ (kill). Her hücrede
    `cap < broker.MAX_ENTRY_GAP_PCT` assert'i (kill: kapı yapısal ateşlemez hücre GEÇERSİZ).
(2) `MERIDIAN_DINLENEN_LIMIT` bayrağı + `importlib.reload(backtest)`: dinlenen-limit (bar_low)
    dolum kuralı — EXE-005 H3 modeli; kural YALNIZ `broker.fill_entry` içinde uygulanır (kill).
KOL KİMLİĞİ KAPISI (exe006 Kritik-1 AYNEN): `backtest.replay` sarmalanır, `dolum_kurali`
damgası + `entry_reject_ids` (Ö-51b red kimlikleri) SONUCUN KENDİSİNDEN okunur; damga kola
uymazsa hücre ölçüm DEĞİLDİR ve koşum DURUR.

════════ DOLUM-KURALI ÖZ-SINAMASI (her silahlı hücrede) ════════
`PaperBroker.fill_entry` sarmalanır; her çağrıda limit yürürlükteki yasadan yeniden hesaplanır
(`entry_limit_price(trigger, atr, entry_law())` — yama aktifken yamalı yasa) ve:
  * yalniz_acilis kolunda: `bar_low` HİÇBİR çağrıda geçilmemiş olmalı (bayrak sızıntısı =
    kill işareti) ve açılışı limit üstü hiçbir çağrı POZİSYON dönmemeli.
  * dinlenen kolunda: `bar_low` HER çağrıda geçilmiş olmalı; `bar_low > limit` iken dolum
    YAZILMAMALI (fiyatın dokunmadığı limitten dolum = UYDURMA DOLUM, exe005 kill sınıfı);
    `bar_low <= limit` dolumunda fiyat bandı: limit·(1+slip) ≤ entry ≤
    limit·(1+slip)·(1+IMPACT_COEF·ADV_CAP_PCT) (impact üst sınırı: katılım ≤ ADV_CAP_PCT).
  * her iki kolda: sarmalayıcının gördüğü yasa {limit_atr_mult: 0.5, limit_pct_cap: cap}.
Öz-sınama düşerse hücre GEÇERSİZ ve koşum DURUR (sessizce geçilmez).

════════ ŞASİ KAPISI (kill — kart #2) ════════
Silahsız kontrol koşumu edg032c/kosum1 ile ÜÇ DEFTERDE (islemler_tam + islemler slim +
seanslar) sha256 BAYT-ÖZDEŞ olmalı; tam koşumda referans sha'ları TABAN_KUNYESI.json
(2026-08-23 tazelenmiş; guard v268) kaydının KENDİSİ olmalı (künye çivisi — edg046 AYNEN).
Düşerse ölçüm DURUR (exit 2). Duman kapısı edg032c/kosum1_smoke'a kıyaslanır.

Δ+CI (Ö3-devri): EŞLENİK ay-kümeli bootstrap — birim=AY, iki kol AYNI ayı görür, B=5000,
seed=20260812, yüzdelik (edg040/045/046/048 `delta_pnl_ci` AYNEN; aylar kontrol
seanslarından). BEYANLI FARK: EXE-006'nın Ö3'ü 42 aylık (işlemli aylar) tabandaydı; bu koşum
edg048 reçetesini izler (kontrol seans ayları = takvim tabanı). H2 CI: ay-kümeli bootstrap
(exe006 O2 yöntemi AYNEN — aylar ek-işlem aylarından).

MOTOR SHA (parent [6]): 4 dosya (broker/backtest/strategy/guard) hücre başı önce/sonra +
tazelenmiş künye `kosum1_once` kaydıyla kıyas; sapan hücre GEÇERSİZ ve koşum DURUR.

DİSİPLİN: UYDURMA YASAĞI (ölçülemeyen None + neden) · YASA-4 (sessiz-yutma işaretli) · git
KOŞULMAZ · state/ YAZILMAZ (şasi kendi sandbox'ına yönlendirir; bars symlink SALT-OKUNUR) ·
test suite KOŞULMAZ · motor/kart/ROADMAP dosyalarına DOKUNULMAZ · HÜKÜM YOK (monotonluk vb.
alanlar BETİMLEYİCİDİR; success_metric kuralını Rol-1 işletir).

KULLANIM (sıra zorunlu; her adım ayrı süreç):
  olcum.py duman     # [1] dar pencere: silahsız kontrol + şasi kapısı(smoke) + 1 silahlı hücre
  olcum.py kontrol   # [2] TAM silahsız kontrol + şasi kapısı (kill — düşerse DUR)
  olcum.py grid      # [3-4] 8 hücre TAM (şasi kapısı GEÇMEDEN koşulamaz)
  olcum.py analiz    # [4-6] H1 eğrisi · H2 (kol farkı + CI) · H3 oranları · Ö3 Δ+CI · sha dökümü
"""
from __future__ import annotations

import contextlib
import datetime as dt
import hashlib
import importlib
import importlib.util
import inspect
import json
import os
import pathlib
import shutil
import sys

BURASI = pathlib.Path(__file__).resolve().parent
REPO = BURASI.parents[2]
REFERANS = REPO / "research" / "olcumler" / "edg032b_tamsatir_2026-08-13" / "olcum.py"
EDG032C = REPO / "research" / "olcumler" / "edg032c_taban_2026-08-22"
KUNYE_YOL = EDG032C / "TABAN_KUNYESI.json"
sys.path.insert(0, str(REPO))

# ── kartın parameter_grid'i — DEĞİŞTİRİLEMEZ (K=8, ÇARPILARAK) ──────────────────────────────
TAVANLAR = [0.005, 0.01, 0.02, 0.03]
DOLUM_KURALLARI = ["yalniz_acilis", "dinlenen_limit"]

B1_YASA = ("breakout_vcp", "exhaustion_hammer", "momentum_burst")
MOTOR_DOSYALAR = ("broker.py", "backtest.py", "strategy.py", "guard.py")
BOOT_ITER = 5000
BOOT_SEED = 20260812
DUMAN_HUCRE = (0.005, "dinlenen_limit")   # [1]'in tek silahlı hücresi (exe006 dumanında sinyalli nokta)


def _sha(p: pathlib.Path) -> str | None:
    try:
        return hashlib.sha256(p.read_bytes()).hexdigest()
    except OSError:
        return None    # ölçülemedi (dosya yok/okunamadı)


def motor_sha() -> dict:
    return {f: _sha(REPO / "meridian" / f) for f in MOTOR_DOSYALAR}


def kunye_motor_kiyas(m: dict) -> dict:
    """Hücre anındaki motor sha'ları ↔ tazelenmiş künye kosum1_once kaydı (parent [6])."""
    kunye = json.loads(KUNYE_YOL.read_text())
    ref = kunye["motor_sha256"]["kosum1_once"]
    kiyas = {f: {"olculen": m[f], "kunye": ref[f]["sha256"], "esit": m[f] == ref[f]["sha256"]}
             for f in MOTOR_DOSYALAR}
    return {"dosyalar": kiyas, "kunyeyle_ayni": all(v["esit"] for v in kiyas.values())}


def state_sha() -> dict:
    """Kart kill'i: `state/goal.yaml` değişirse geçersiz — koşum başı/sonu sha kaydı."""
    return {f: _sha(REPO / "state" / f) for f in ("goal.yaml", "bounds.yaml")}


def referans_modul():
    """Şasiyi modül olarak yükler (edg032c deseni AYNEN): SANDBOX → BU dizin;
    ARMED_BEKLENEN → B1 yasası (BEYANLI TEK UYARLAMA); motor sapmışsa BAŞLAMADAN durur."""
    # Şasi KAYNAKTAN derlenir (2026-08-30): argv/SystemExit dansı AYNEN korunur, ama
    # `__pycache__` okunmaz — bayat bytecode on üç ölçümü birden sessizce bozabilirdi.
    # Yerel ithal: `sys.path` kurulumu modül başında yapılıyor. Gerekçe:
    # `ops/sasi_yukleyici.py` başlığı · kapı: tests/test_bayat_bytecode_v334.py §C.
    from ops.sasi_yukleyici import referans_sasi_yukle
    m = referans_sasi_yukle(REFERANS)
    m.SANDBOX = BURASI                # artefakt koruması: edg032b/exe006/edg032c'ye ASLA yazılmaz
    eski_beklenen = tuple(m.ARMED_BEKLENEN)
    m.ARMED_BEKLENEN = B1_YASA
    from meridian import strategy as _st
    assert tuple(_st.ARMED_SETUPS) == B1_YASA, \
        f"MOTOR B1 YASASINDAN SAPMIŞ: {_st.ARMED_SETUPS} ≠ {B1_YASA} — koşum durdu"
    return m, {"eski_ARMED_BEKLENEN": list(eski_beklenen), "yeni_ARMED_BEKLENEN": list(B1_YASA),
               "motor_ARMED_SETUPS": list(_st.ARMED_SETUPS),
               "beyan": ("edg032c TEK uyarlaması AYNEN: yüklenen şasi modülünün ARMED_BEKLENEN "
                         "sabiti B1 yasasına çevrildi (dünya-beklentisi; motor DEĞİL). "
                         "Parametre enjeksiyonu YOK (merkez hücre).")}


def bakir_state(run: str, smoke: bool) -> None:
    """Bakir sandbox (edg032c deseni): önceki artık state determinizmi/kıyası kirletmesin."""
    st = BURASI / f"state_{run}{'_smoke' if smoke else ''}"
    if st.exists():
        shutil.rmtree(st)


@contextlib.contextmanager
def yasa_silahli(cap: float):
    """Limit bacağını `cap` tavanıyla silahlandırır — YALNIZ bu süreçte, yalnız bu blok boyunca.
    EXE-006 AYNEN: `state/goal.yaml` DEĞİŞMEZ; `limit_atr_mult` kod varsayılanına (0.5) çekilir
    (canlıdaki 100.0 ATR bacağını yapısal öldürüyor — o hâlde grid'in ATR ekseni sessizce ölürdü)."""
    from meridian import broker as B
    assert cap < B.MAX_ENTRY_GAP_PCT, \
        f"KILL: cap={cap} >= MAX_ENTRY_GAP_PCT={B.MAX_ENTRY_GAP_PCT} — hücre GEÇERSİZ (yapısal ateşlemez)"
    asil = B.entry_law
    yeni = {**asil(), "limit_atr_mult": B.ENTRY_LIMIT_ATR_MULT, "limit_pct_cap": cap}
    B.entry_law = lambda *a, **k: yeni
    try:
        yield yeni
    finally:
        B.entry_law = asil


@contextlib.contextmanager
def dolum_oz_sinama(kural: str, kayit: dict):
    """`PaperBroker.fill_entry` sarmalanır — dolum kuralının YALNIZ orada ve DOĞRU uygulandığı
    çağrı düzeyinde sınanır (modül başlığındaki ÖZ-SINAMA bloğu). Motor dosyası DEĞİŞMEZ."""
    from meridian import broker as B
    asil = B.PaperBroker.fill_entry
    sig = inspect.signature(asil)

    def sarmal(self, *a, **k):
        ba = sig.bind(self, *a, **k)
        ba.apply_defaults()
        plan = ba.arguments["plan"]
        orig_open = float(ba.arguments["next_open"])
        atr = ba.arguments["atr"]
        bar_low = ba.arguments["bar_low"]
        trigger = float(plan.get("entry_trigger", orig_open) or 0.0)
        law = B.entry_law()
        if kayit["yasa_ilk"] is None:
            kayit["yasa_ilk"] = {kk: law.get(kk) for kk in
                                 ("limit_atr_mult", "limit_pct_cap", "version", "gap_behavior")}
        pos = asil(self, *a, **k)
        kayit["n_cagri"] += 1
        red = (ba.arguments["reject_out"] or {}).get("reason") if pos is None else None

        if kural == "yalniz_acilis" and bar_low is not None:
            kayit["ihlaller"].append({"tur": "bar_low_sizintisi", "ticker": plan.get("ticker"),
                                      "ts": ba.arguments["ts"], "bar_low": float(bar_low)})
        if kural == "dinlenen_limit" and bar_low is None:
            kayit["ihlaller"].append({"tur": "bar_low_gecilmedi", "ticker": plan.get("ticker"),
                                      "ts": ba.arguments["ts"]})
        if trigger <= 0:
            kayit["n_tetiksiz"] += 1
            return pos
        limit = B.entry_limit_price(trigger, atr, law)
        if orig_open <= limit:
            kayit["n_acilis_limit_alti"] += 1
            return pos
        # ── açılış limit ÜSTÜ dalı — dolum kuralının ayırt edildiği yer ──
        if kural == "yalniz_acilis":
            kayit["n_acilis_limit_ustu"] += 1
            if pos is not None:
                kayit["ihlaller"].append({"tur": "acilis_kolunda_limit_ustu_dolum",
                                          "ticker": plan.get("ticker"), "ts": ba.arguments["ts"],
                                          "open": orig_open, "limit": limit})
        else:
            if bar_low is not None and float(bar_low) <= limit:
                if pos is not None:
                    kayit["n_dinlenen_dolum"] += 1
                    taban_fiyat = limit * (1.0 + self.slip)
                    ust = taban_fiyat * (1.0 + B.IMPACT_COEF * B.ADV_CAP_PCT)
                    if not (taban_fiyat * (1 - 1e-9) <= pos.entry <= ust * (1 + 1e-9)):
                        kayit["ihlaller"].append({"tur": "dinlenen_dolum_fiyat_bandi_disi",
                                                  "ticker": plan.get("ticker"),
                                                  "ts": ba.arguments["ts"], "entry": pos.entry,
                                                  "beklenen_taban": taban_fiyat, "beklenen_ust": ust})
                    kayit["dinlenen_dolumlar"].append({"ticker": plan.get("ticker"),
                                                       "ts": ba.arguments["ts"],
                                                       "open": round(orig_open, 4),
                                                       "limit": round(limit, 4),
                                                       "bar_low": round(float(bar_low), 4),
                                                       "entry": round(float(pos.entry), 4)})
                else:
                    kayit["n_dinlenen_dolum_yolu_baska_red"] += 1
                    if red == "entry_missed_limit":
                        kayit["ihlaller"].append({"tur": "limite_dokunan_gun_missed_yazildi",
                                                  "ticker": plan.get("ticker"),
                                                  "ts": ba.arguments["ts"],
                                                  "bar_low": float(bar_low), "limit": limit})
            else:
                kayit["n_dinlenen_kacan"] += 1
                if pos is not None:
                    kayit["ihlaller"].append({"tur": "dokunulmayan_limitten_dolum_UYDURMA",
                                              "ticker": plan.get("ticker"), "ts": ba.arguments["ts"],
                                              "bar_low": (float(bar_low) if bar_low is not None else None),
                                              "limit": limit, "entry": float(pos.entry)})
        return pos

    B.PaperBroker.fill_entry = sarmal
    try:
        yield
    finally:
        B.PaperBroker.fill_entry = asil


def yeni_oz_kayit() -> dict:
    return {"yasa_ilk": None, "n_cagri": 0, "n_tetiksiz": 0, "n_acilis_limit_alti": 0,
            "n_acilis_limit_ustu": 0, "n_dinlenen_dolum": 0,
            "n_dinlenen_dolum_yolu_baska_red": 0, "n_dinlenen_kacan": 0,
            "dinlenen_dolumlar": [], "ihlaller": []}


def oz_degerlendir(kayit: dict, kural: str, cap: float) -> dict:
    yasa = kayit["yasa_ilk"]
    yasa_dogru = (yasa is not None and yasa["limit_pct_cap"] == cap
                  and yasa["limit_atr_mult"] == 0.5)
    gecti = (not kayit["ihlaller"]) and yasa_dogru and kayit["n_cagri"] > 0
    return {"kural": kural, "cap": cap, "yasa_gorulen": yasa, "yasa_dogru": yasa_dogru,
            "sayimlar": {kk: kayit[kk] for kk in
                         ("n_cagri", "n_tetiksiz", "n_acilis_limit_alti", "n_acilis_limit_ustu",
                          "n_dinlenen_dolum", "n_dinlenen_dolum_yolu_baska_red",
                          "n_dinlenen_kacan")},
            "dinlenen_dolum_ornekleri": kayit["dinlenen_dolumlar"][:20],
            "dinlenen_dolum_n": kayit["n_dinlenen_dolum"],
            "ihlal_n": len(kayit["ihlaller"]), "ihlaller_ilk50": kayit["ihlaller"][:50],
            "gecti": gecti,
            "beyan": ("fiyat bandı: limit·(1+slip) ≤ entry ≤ limit·(1+slip)·(1+IMPACT_COEF·"
                      "ADV_CAP_PCT) — katılım ≤ ADV_CAP_PCT olduğundan üst sınır yapısal; "
                      "birebir rekonstrüksiyon (edg046 kill#2 modeli) bu kartın kapsamında değil, "
                      "bant mekanik ve tavizsiz")}


def hucre_kos(ref, cap: float, kural: str, smoke: bool) -> dict:
    """Tek hücre: bayrak+reload → yasa yaması → şasiyi ÇAĞIR → kol kimliği + öz-sınama kapıları."""
    run = f"cap{cap}_{kural}"
    ek = "_smoke" if smoke else ""
    os.environ["MERIDIAN_DINLENEN_LIMIT"] = "1" if kural == "dinlenen_limit" else "0"
    from meridian import backtest as BT
    importlib.reload(BT)                          # bayrak modül düzeyinde okunuyor (exe006 AYNEN)
    ref.backtest = BT
    if BT.DINLENEN_LIMIT != (kural == "dinlenen_limit"):
        raise AssertionError(f"bayrak kola uymadı: istenen={kural} DINLENEN_LIMIT={BT.DINLENEN_LIMIT}")

    ref.HUCRELER.setdefault(run, {})              # merkez hücre — parametre enjeksiyonu YOK
    bakir_state(run, smoke)
    m_once = motor_sha()

    yakalanan: dict = {}
    asil_replay = BT.replay

    def _sarmal(*a, **k):
        r = asil_replay(*a, **k)
        yakalanan["damga"] = getattr(r, "dolum_kurali", None)
        yakalanan["red_kimlik"] = getattr(r, "entry_reject_ids", None)
        return r

    BT.replay = _sarmal
    oz_kayit = yeni_oz_kayit()
    try:
        with yasa_silahli(cap) as yasa, dolum_oz_sinama(kural, oz_kayit):
            ref.kosum(run, smoke=smoke)           # ŞASİ: referansın kendi yolu, dokunulmadan
    finally:
        BT.replay = asil_replay
    m_sonra = motor_sha()

    # KOL KİMLİĞİ KAPISI (exe006 Kritik-1 AYNEN): damga tutmazsa hücre ölçüm DEĞİL, koşum DURUR
    damga = yakalanan.get("damga")
    if damga != kural:
        raise AssertionError(
            f"KOL KİMLİĞİ TUTMADI: beklenen={kural} damga={damga} — hücre ölçüm DEĞİL, koşum DURUR")

    outdir = (BURASI / "smoke") if smoke else BURASI
    d = json.loads((outdir / f"sonuc_{run}{ek}.json").read_text())
    defter = json.loads((outdir / f"islemler_tam_{run}{ek}.json").read_text())

    oz = oz_degerlendir(oz_kayit, kural, cap)
    (outdir / f"oz_sinama_{run}{ek}.json").write_text(
        json.dumps(oz, ensure_ascii=False, indent=1), encoding="utf-8")

    islem = d.get("islem") or {}
    perf = d.get("performans") or {}
    rejects = dict(islem.get("entry_rejects") or {})
    kiyas = kunye_motor_kiyas(m_once)
    ozet = {
        "run": run, "smoke": smoke, "limit_pct_cap": cap, "dolum_kurali": kural,
        "dolum_kurali_damgasi": damga,
        "yasa": {kk: yasa[kk] for kk in ("limit_atr_mult", "limit_pct_cap", "version")},
        "entry_rejects": rejects,
        "entry_missed_limit": int(rejects.get("entry_missed_limit", 0)),
        # Ö-51b: distinkt reddedilen plan kimliği (payda) — olay sayacı DEĞİL
        "red_kimlik": {kk: sorted(set(map(tuple, v)))
                       for kk, v in (yakalanan.get("red_kimlik") or {}).items()},
        # NET P&L KANONİK ALANDAN (exe006 düzeltmesi AYNEN: islem.net_pnl YOK)
        "net_pnl_trades": perf.get("net_pnl_trades"),
        "net_pnl_equity": perf.get("net_pnl_equity"),
        "islem_n": islem.get("n"),
        "maxdd_kanonik": perf.get("maxdd_kanonik"), "sharpe": perf.get("sharpe"),
        "avg_r": perf.get("avg_r"), "win_rate": perf.get("win_rate"),
        "setup_bazinda": islem.get("setup_bazinda"),
        "butunluk_gecerli": (d.get("butunluk") or {}).get("gecerli"),
        "oz_sinama_gecti": oz["gecti"],
        "dinlenen_dolum_n": oz["dinlenen_dolum_n"],
        "motor_sha_once": m_once, "motor_sha_sonra": m_sonra,
        "motor_sha_ayni": m_once == m_sonra,
        "motor_kunye_kiyas": kiyas,
    }
    (outdir / f"hucre_{run}{ek}.json").write_text(
        json.dumps(ozet, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"  [{run}{ek}] damga={damga} n={ozet['islem_n']} net={ozet['net_pnl_trades']} "
          f"missed_limit={ozet['entry_missed_limit']} dinlenen_dolum={oz['dinlenen_dolum_n']} "
          f"öz-sınama={oz['gecti']} motor_ayni={ozet['motor_sha_ayni']} "
          f"künye_ayni={kiyas['kunyeyle_ayni']}", flush=True)
    if not oz["gecti"]:
        raise AssertionError(f"ÖZ-SINAMA DÜŞTÜ ({run}): ihlal_n={oz['ihlal_n']} "
                             f"yasa_dogru={oz['yasa_dogru']} — hücre GEÇERSİZ, koşum DURUR")
    if not ozet["motor_sha_ayni"]:
        raise AssertionError(f"MOTOR SHA hücre içinde değişti ({run}) — hücre GEÇERSİZ, koşum DURUR")
    if not kiyas["kunyeyle_ayni"]:
        raise AssertionError(f"MOTOR SHA künyeden sapmış ({run}) — dünya kimliği tutmuyor, DURUR")
    return ozet


def kontrol_kos(ref, smoke: bool) -> dict:
    """Silahsız kontrol: bayrak KAPALI, yasa YAMASIZ — şasi kapısının öznesi."""
    ek = "_smoke" if smoke else ""
    os.environ["MERIDIAN_DINLENEN_LIMIT"] = "0"
    from meridian import backtest as BT
    importlib.reload(BT)
    ref.backtest = BT
    assert BT.DINLENEN_LIMIT is False, "kontrol kolunda bayrak açık — kol kirli, DUR"
    bakir_state("kontrol", smoke)
    m_once = motor_sha()
    ref.kosum("kontrol", smoke=smoke)             # ŞASİ AYNEN — hiçbir yama aktif değil
    m_sonra = motor_sha()
    kiyas = kunye_motor_kiyas(m_once)
    out = {"run": "kontrol" + ek, "motor_sha_once": m_once, "motor_sha_sonra": m_sonra,
           "motor_sha_ayni": m_once == m_sonra, "motor_kunye_kiyas": kiyas}
    if not out["motor_sha_ayni"] or not kiyas["kunyeyle_ayni"]:
        raise AssertionError("MOTOR SHA kontrol koşumunda tutmadı — DUR")
    return out


def sasi_kapisi(smoke: bool) -> dict:
    """Kill (kart #2): silahsız kontrol ↔ edg032c/kosum1 üç defterde bayt-özdeş (edg046 AYNEN)."""
    ek = "_smoke" if smoke else ""
    yerel_dir = (BURASI / "smoke") if smoke else BURASI
    ref_dir = EDG032C / ("kosum1_smoke" if smoke else "kosum1")
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
        sy, sr = _sha(y), _sha(r)
        sonuc[ad] = {"yerel_sha256": sy, "edg032c_sha256": sr,
                     "bayt_ozdes": (sy is not None and sy == sr),
                     "olculemedi_nedeni": (None if (sy and sr) else
                                           f"dosya okunamadı: yerel={bool(sy)} ref={bool(sr)}")}
    kunye_tutarli = None
    if not smoke:
        kunye = json.loads(KUNYE_YOL.read_text())
        ks = kunye["determinizm_kaniti"]["kapi_sha256"]
        kunye_tutarli = (sonuc["islemler_tam"]["edg032c_sha256"] == ks["islemler_tam_kontrol.json"]
                         and sonuc["islemler_slim"]["edg032c_sha256"] == ks["islemler_kontrol.json"]
                         and sonuc["seanslar"]["edg032c_sha256"] == ks["seanslar_kontrol.json"])
    gecti = all(v["bayt_ozdes"] for v in sonuc.values()) and (kunye_tutarli is not False)
    out = {"bayt_kiyas_edg032c": sonuc, "kunye_sha_tutarli": kunye_tutarli, "kill_gecti": gecti}
    (yerel_dir / f"sasi_kapisi{ek}.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"  ŞASİ KAPISI{ek}: bayt={all(v['bayt_ozdes'] for v in sonuc.values())} "
          f"künye_tutarlı={kunye_tutarli} → {'GEÇTİ' if gecti else 'DÜŞTÜ — ölçüm DURUR'}", flush=True)
    return out


# ---------------------------------------------------------------------------------------------
# Δ+CI reçeteleri
# ---------------------------------------------------------------------------------------------
def delta_pnl_ci(taban_defter: list, hucre_defter: list, aylar: list[str]) -> dict:
    """EŞLENİK ay-kümeli bootstrap (edg040/045/046/048 AYNEN): birim = AY, iki kol AYNI ayı
    görür, B=5000, seed=20260812, yüzdelik CI."""
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
            "yontem": ("EŞLENİK ay-kümeli bootstrap · birim = AY (iki kol AYNI ayı görür) · "
                       "B=5000 · seed=20260812 · yüzdelik")}


def ort_r_ay_ci(islemler: list[dict]) -> dict:
    """H2 CI: ay-kümeli bootstrap (exe006 O2 yöntemi AYNEN) — birim=AY (işlemlerin kendi
    ayları), B=5000, seed=20260812, yüzdelik. r_multiple'sız satır sayılır, sessiz düşmez."""
    import numpy as np
    gruplar: dict[str, list[float]] = {}
    r_yok = 0
    for t in islemler:
        if t.get("r_multiple") is None:
            r_yok += 1                     # YASA-4: sayılır
            continue
        gruplar.setdefault(str(t["ts_open"])[:7], []).append(float(t["r_multiple"]))
    tum = [r for g in gruplar.values() for r in g]
    if not tum:
        return {"ort_r": None, "n_islem": 0, "r_multiple_bos_n": r_yok,
                "olculemedi_nedeni": "işlem yok ya da r_multiple boş — ort-R ÖLÇÜLEMEDİ"}
    aylar = sorted(gruplar)
    M = len(aylar)
    nokta = round(float(np.mean(tum)), 4)
    if M < 2:
        return {"ort_r": nokta, "ci95": None, "n_islem": len(tum), "n_ay_kumesi": M,
                "r_multiple_bos_n": r_yok,
                "olculemedi_nedeni": "ay kümesi < 2 — kümeli CI hesaplanamaz"}
    rng = np.random.default_rng(BOOT_SEED)
    f = np.empty(BOOT_ITER)
    for i in range(BOOT_ITER):
        pick = rng.choice(M, size=M, replace=True)
        havuz = [r for j in pick for r in gruplar[aylar[j]]]
        f[i] = float(np.mean(havuz)) if havuz else 0.0
    lo = round(float(np.percentile(f, 2.5)), 4)
    hi = round(float(np.percentile(f, 97.5)), 4)
    return {"ort_r": nokta, "ci95": [lo, hi], "n_islem": len(tum), "n_ay_kumesi": M,
            "r_multiple_bos_n": r_yok,
            "sifir_disinda": ("evet (CI-alt > 0)" if lo > 0 else
                              "evet (CI-üst < 0)" if hi < 0 else "hayır (0 içinde)"),
            "yontem": "ay-kümeli bootstrap · B=5000 · seed=20260812 · yüzdelik aralığı"}


# ---------------------------------------------------------------------------------------------
# ANALİZ — H1 eğrisi · H2 kol farkı+CI · H3 oranları · Ö3 Δ+CI (koşum yok; defterlerden)
# ---------------------------------------------------------------------------------------------
def analiz() -> int:
    sk = json.loads((BURASI / "sasi_kapisi.json").read_text())
    if not sk["kill_gecti"]:
        sys.exit("analiz: şasi kapısı GEÇMEMİŞ — analiz koşulmaz")

    hucreler: dict[tuple, dict] = {}
    defterler: dict[tuple, list] = {}
    for cap in TAVANLAR:
        for kural in DOLUM_KURALLARI:
            run = f"cap{cap}_{kural}"
            hucreler[(cap, kural)] = json.loads((BURASI / f"hucre_{run}.json").read_text())
            defterler[(cap, kural)] = json.loads(
                (BURASI / f"islemler_tam_{run}.json").read_text())

    seanslar = json.loads((BURASI / "seanslar_kontrol.json").read_text())
    aylar = sorted({str(r["date"])[:7] for r in seanslar})
    kontrol_defter = json.loads((BURASI / "islemler_tam_kontrol.json").read_text())
    kontrol_net = round(sum(float(t.get("pnl_dollars") or 0.0) for t in kontrol_defter), 2)

    def kimlik(t):
        return (t["ticker"], str(t["ts_open"])[:10])

    kol_farki: dict[str, dict] = {}
    o3: dict[str, dict] = {}
    h3: dict[str, dict] = {}
    for cap in TAVANLAR:
        a = hucreler[(cap, "yalniz_acilis")]
        b = hucreler[(cap, "dinlenen_limit")]
        da = defterler[(cap, "yalniz_acilis")]
        db = defterler[(cap, "dinlenen_limit")]
        ak = {kimlik(t) for t in da}
        yalniz_b = [t for t in db if kimlik(t) not in ak]
        yalniz_a = [t for t in da if kimlik(t) not in {kimlik(t2) for t2 in db}]
        # açılış kolunun DİSTİNKT kaçan-plan kimlikleri (Ö-51b)
        kacan_kimlik = {tuple(x) for x in (a.get("red_kimlik") or {}).get("entry_missed_limit", [])}
        # kimlik-süzülü H2: dinlenen defterinde, açılış kolunda KAÇAN kimliğiyle eşleşen işlemler
        kacan_dolan = [t for t in db if kimlik(t) in kacan_kimlik]
        c = str(cap)
        kol_farki[c] = {
            "kacan_olay_acilis": a["entry_missed_limit"],
            "kacan_distinkt_plan_acilis": len(kacan_kimlik),
            "dinlenen_kolda_DOLAN_ek_islem": len(yalniz_b),
            "yerinden_olan_yalniz_acilis": len(yalniz_a),
            "yerinden_olan_ort_r": (round(sum(float(t["r_multiple"]) for t in yalniz_a
                                              if t.get("r_multiple") is not None)
                                          / max(1, sum(1 for t in yalniz_a
                                                       if t.get("r_multiple") is not None)), 4)
                                    if any(t.get("r_multiple") is not None for t in yalniz_a)
                                    else None),
            # H2 — EXE-006-birebir eksen: EK işlemlerin ort-R'si + CI (kıyaslanabilirlik sözleşmesi)
            "H2_ek_islem": ort_r_ay_ci(yalniz_b),
            # H2 — Ö-51b kimlik-süzülü eksen (beyanlı EK; exe006'da yoktu — pay saf değildi)
            "H2_kimlik_suzulu_kacan_dolan": ort_r_ay_ci(kacan_dolan),
            "net_pnl_yalniz_acilis": a["net_pnl_trades"],
            "net_pnl_dinlenen": b["net_pnl_trades"],
            "delta_pnl_nokta": (round(b["net_pnl_trades"] - a["net_pnl_trades"], 2)
                                if None not in (a["net_pnl_trades"], b["net_pnl_trades"]) else None),
        }
        # Ö3-devri: her tavanda Δ(dinlenen−açılış) + eşlenik CI
        o3[c] = delta_pnl_ci(da, db, aylar)
        # H3 — dinlenen dolum oranı (iki tanım, ikisi de beyanlı)
        dol_n = int(b.get("dinlenen_dolum_n") or 0)
        dolan_kimlikte = {kimlik(t) for t in db} & kacan_kimlik
        h3[c] = {
            "dinlenen_dolum_n": dol_n,
            "dinlenen_islem_n": b["islem_n"],
            "oran_kol_ici": (round(dol_n / b["islem_n"], 4) if b["islem_n"] else None),
            "kacan_plan_dinlenende_dolan_n": len(dolan_kimlikte),
            "oran_kacan_plan_dolumu": (round(len(dolan_kimlikte) / len(kacan_kimlik), 4)
                                       if kacan_kimlik else None),
            "oran_olculemedi_nedeni": (None if kacan_kimlik else
                                       "açılış kolunda distinkt kaçan plan yok — payda sıfır, TANIMSIZ"),
            "tanim": ("oran_kol_ici = dinlenen kolda 'açılış limitüstü ama gün içi limit "
                      "dokunuşuyla dolan' işlem / kol işlem sayısı (öz-sınama sayacından); "
                      "oran_kacan_plan_dolumu = açılış kolunun DİSTİNKT kaçan planlarından "
                      "dinlenen kolda (ticker, gün) kimliğiyle dolanların payı (Ö-51b)"),
        }

    # H1 verisi — EĞRİ (dört tavan; mekanik fark işaretleri BETİMLEYİCİDİR, hüküm Rol-1'in)
    def egri(kural):
        y = [hucreler[(cap, kural)]["net_pnl_trades"] for cap in TAVANLAR]
        farklar = [round(y[i + 1] - y[i], 2) for i in range(len(y) - 1)]
        return {"tavanlar": TAVANLAR, "net_pnl": y, "ardisik_fark": farklar,
                "mekanik_monoton_artan": all(f > 0 for f in farklar),
                "mekanik_monoton_azalan": all(f < 0 for f in farklar)}

    rapor = {
        "kart": "EXE-2026-008",
        "olcum_zamani": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "pencere": {"start": "2022-01-01", "end": "2026-07-30"},
        "sasi_kapisi": sk,
        "kontrol_net_pnl": kontrol_net,
        "hucre_tablosu": [
            {"cap": cap, "kural": kural,
             **{kk: hucreler[(cap, kural)][kk] for kk in
                ("islem_n", "net_pnl_trades", "entry_missed_limit", "dinlenen_dolum_n",
                 "oz_sinama_gecti", "butunluk_gecerli", "motor_sha_ayni")}}
            for cap in TAVANLAR for kural in DOLUM_KURALLARI],
        "H1_egri": {"dinlenen_limit": egri("dinlenen_limit"),
                    "yalniz_acilis": egri("yalniz_acilis"),
                    "beyan": ("mekanik_monoton_* alanları aritmetik işarettir, hüküm DEĞİL; "
                              "H1 hükmünü kartın success_metric kuralıyla Rol-1 verir")},
        "kol_farki_H2": kol_farki,
        "H3_dinlenen_dolum": h3,
        "O3_delta_pnl_ci": o3,
        "ci_taban_beyani": ("Ö3 ayları kontrol seanslarından (edg048 reçetesi AYNEN; "
                            f"n_ay={len(aylar)}); EXE-006'nın Ö3'ü 42 aylık işlemli-ay "
                            "tabanındaydı — fark BEYANLIDIR, iki CI ailesi aynı yöntem farklı "
                            "ay tabanı. H2 CI'ı exe006 O2 yöntemi AYNEN (işlem aylarından)."),
        "motor_sha_hucre_ozeti": {
            f"cap{cap}_{kural}": hucreler[(cap, kural)]["motor_kunye_kiyas"]["kunyeyle_ayni"]
            for cap in TAVANLAR for kural in DOLUM_KURALLARI},
        "hukum_yok": ("Bu dosya HÜKÜM İÇERMEZ; kartın success_metric/kill kurallarını Rol-1 "
                      "işletir. UYDURMA YASAĞI gereği ölçülemeyenler None + neden taşır."),
    }
    (BURASI / "sonuc_grid.json").write_text(
        json.dumps(rapor, ensure_ascii=False, indent=1), encoding="utf-8")
    print("── ANALİZ ──")
    for cap in TAVANLAR:
        c = str(cap)
        f = kol_farki[c]
        print(f"  cap={c:<6} kaçan_plan={f['kacan_distinkt_plan_acilis']:<3} "
              f"ek_dolan={f['dinlenen_kolda_DOLAN_ek_islem']:<3} "
              f"H2ek={f['H2_ek_islem'].get('ort_r')} CI={f['H2_ek_islem'].get('ci95')} "
              f"Δ={o3[c]['delta_pnl']} CI={o3[c]['ci95']} {o3[c]['sifir_disinda']}")
    print(f"yazıldı: {BURASI / 'sonuc_grid.json'}")
    return 0


# ---------------------------------------------------------------------------------------------
def main() -> int:
    mod = sys.argv[1] if len(sys.argv) > 1 else ""
    st0 = state_sha()
    kod = 0
    if mod == "duman":
        ref, uyarlama = referans_modul()
        print(f"şasi yüklendi · SANDBOX={ref.SANDBOX.name} · uyarlama={uyarlama['yeni_ARMED_BEKLENEN']}",
              flush=True)
        k = kontrol_kos(ref, smoke=True)
        sk = sasi_kapisi(smoke=True)
        rapor = {"kart": "EXE-2026-008", "adim": "duman", "uyarlama_beyani": uyarlama,
                 "kontrol": k, "sasi_kapisi_smoke": sk}
        if not sk["kill_gecti"]:
            rapor["DURDU"] = "duman şasi kapısı düştü — silahlı hücre koşulmadı"
            kod = 2
        else:
            cap, kural = DUMAN_HUCRE
            rapor["silahli_hucre"] = hucre_kos(ref, cap, kural, smoke=True)
        (BURASI / "duman_raporu.json").write_text(
            json.dumps(rapor, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"yazıldı: {BURASI / 'duman_raporu.json'}")
    elif mod == "kontrol":
        ref, uyarlama = referans_modul()
        print(f"şasi yüklendi · SANDBOX={ref.SANDBOX.name}", flush=True)
        k = kontrol_kos(ref, smoke=False)
        sk = sasi_kapisi(smoke=False)
        (BURASI / "kontrol_raporu.json").write_text(json.dumps(
            {"kart": "EXE-2026-008", "adim": "kontrol_tam", "uyarlama_beyani": uyarlama,
             "kontrol": k, "sasi_kapisi": sk}, ensure_ascii=False, indent=1), encoding="utf-8")
        if not sk["kill_gecti"]:
            print("KILL: şasi kapısı DÜŞTÜ — ölçüm DURUR (teşhis Rol-1'e)")
            kod = 2
    elif mod == "grid":
        sk = json.loads((BURASI / "sasi_kapisi.json").read_text())
        if not sk["kill_gecti"]:
            sys.exit("grid: şasi kapısı GEÇMEMİŞ — 8 hücre koşulamaz (sıra zorunlu)")
        dr = json.loads((BURASI / "duman_raporu.json").read_text())
        if "DURDU" in dr:
            sys.exit("grid: duman DURDU damgalı — önce teşhis")
        ref, _ = referans_modul()
        print(f"şasi yüklendi · SANDBOX={ref.SANDBOX.name} · K=8 TAM başlıyor", flush=True)
        for cap in TAVANLAR:
            for kural in DOLUM_KURALLARI:
                # SÜRDÜRME KAPISI (BEYANLI; 2026-08-23 grid süreci dışarıdan öldürüldü):
                # hücreler bağımsız (hücre başı bakir sandbox + reload + yama-restore);
                # TÜM kapıları geçmiş hücre yeniden koşulmaz, yarım hücre baştan koşulur.
                run = f"cap{cap}_{kural}"
                hy = BURASI / f"hucre_{run}.json"
                if hy.exists():
                    h = json.loads(hy.read_text())
                    if (h.get("dolum_kurali_damgasi") == kural and h.get("oz_sinama_gecti")
                            and h.get("motor_sha_ayni")
                            and (h.get("motor_kunye_kiyas") or {}).get("kunyeyle_ayni")):
                        print(f"  [{run}] onceki kosumdan TAMAM (kapilar gecmis) — atlaniyor",
                              flush=True)
                        continue
                hucre_kos(ref, cap, kural, smoke=False)
        print("8 hücre tamam — analiz ayrı süreçte: olcum.py analiz")
    elif mod == "analiz":
        kod = analiz()
    else:
        sys.exit("kullanım: olcum.py {duman|kontrol|grid|analiz}")
    st1 = state_sha()
    if st0 != st1:
        print(f"KILL: repo state/ sha koşum içinde DEĞİŞTİ: önce={st0} sonra={st1} — GEÇERSİZ")
        kod = 2
    (BURASI / f"state_sha_{mod}.json").write_text(json.dumps(
        {"once": st0, "sonra": st1, "ayni": st0 == st1}, ensure_ascii=False, indent=1),
        encoding="utf-8")
    return kod


if __name__ == "__main__":
    raise SystemExit(main())
