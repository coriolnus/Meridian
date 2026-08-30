#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EDG-2026-057 — `leading_sector` kapısının reddettiği DOKUNULMAMIŞ planların karşı-olgusal ölçümü.

BU BETİK HÜKÜM ÜRETMEZ. Sayı üretir; hükmü Rol-1 işler.

Kart: research/cards/EDG-2026-057-leading-sector-kapisi.yaml (ön-kayıtlı, eşik DONMUŞ = 0).
K DONMUŞ: TEK kohort (`leading_sector_ret_islemsiz`), TEK eksen. Alt-kırılım YOK.

AŞAMALAR
  [A] KÜNYE KAPISI      — edg032c donmuş tabanının motor sha256'sı ölçüm anında doğrulanır.
                          Eşleşmezse kill#2 ateşler ve KARŞI-OLGUSAL KOŞUM KOŞULMAZ.
  [B] TEST KÜMESİ       — künyeden BAĞIMSIZ (yalnız iki defteri okur). Her hâlde koşar:
                          dışlama sayıları + sızıntı kontrolü + çakışma sayısı.
  [C] KARŞI-OLGUSAL     — [A] kapısına bağlı. Kapı kapalıysa None + neden (UYDURMA YASAĞI).
  [D] İSTATİSTİK        — ay-kümeli bootstrap. Fonksiyon burada TANIMLI ve sentetik veriyle
                          ÖZ-SINANIR (kohort verisi olmadan da doğruluğu gösterilebilsin diye);
                          kohorda ancak [C] koştuysa uygulanır.

Koşum:  .venv/bin/python research/olcumler/edg057_leading_sector_2026-08-24/olc.py
"""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import sys
from collections import Counter

import numpy as np
import pandas as pd

REPO = "/Users/erdemozturk/AI-Trading"
CIKTI = os.path.join(REPO, "research/olcumler/edg057_leading_sector_2026-08-24")

PLANS = os.path.join(REPO, "state/trade_plans.jsonl")
LEDGER = os.path.join(REPO, "state/trades.jsonl")
KUNYE = os.path.join(REPO, "research/olcumler/edg032c_taban_2026-08-22/TABAN_KUNYESI.json")

OLCUT = "leading_sector"          # kartın izole ettiği TEK ölçüt
KOHORT = "leading_sector_ret_islemsiz"

# ---- ÖN-KAYITLI, DONMUŞ (kart: features_asof + success_metric). OYNATILMAZ. ----
BOOT_B = 5000
BOOT_SEED = 20260812
BOOT_BIRIM = "AY"                 # işlem-düzeyi bootstrap YASAK: ay-içi bağımlılığı yok sayar
ESIK = 0.0                        # kararın eşiği; ölçümden ÖNCE donduruldu


# =================================================================================================
# [A] KÜNYE KAPISI
# =================================================================================================
def _sha256(yol: str) -> str:
    h = hashlib.sha256()
    with open(yol, "rb") as fh:
        for blok in iter(lambda: fh.read(1 << 20), b""):
            h.update(blok)
    return h.hexdigest()


def kunye_kapisi() -> dict:
    """edg032c künyesindeki motor sha256'larını ŞİMDİKİ dosyalarla karşılaştırır.

    Kart kill#2: 'edg032c künyesi (motor sha) ölçüm anında tabanla eşleşmezse geçersiz.'
    Bu fonksiyon HÜKÜM vermez; eşleşme tablosunu ve `gecti` bayrağını döndürür.
    """
    kunye = json.load(open(KUNYE, encoding="utf-8"))
    beklenen = kunye["motor_sha256"]["kosum1_once"]
    # kosum2_sonra ile iç tutarlılık: künyenin kendisi dört noktada sabit olduğunu iddia ediyor.
    sonra = kunye["motor_sha256"]["kosum2_sonra"]
    ic_tutarli = all(beklenen[f]["sha256"] == sonra[f]["sha256"] for f in beklenen)

    satirlar = []
    for dosya, kayit in sorted(beklenen.items()):
        yol = os.path.join(REPO, "meridian", dosya)
        var = os.path.exists(yol)
        simdi = _sha256(yol) if var else None
        satirlar.append({
            "dosya": f"meridian/{dosya}",
            "taban_sha256": kayit["sha256"],
            "simdiki_sha256": simdi,
            "esitmi": (simdi == kayit["sha256"]),
            "taban_mtime_ns": kayit["mtime_ns"],
            "simdiki_mtime_ns": (os.stat(yol).st_mtime_ns if var else None),
        })
    gecti = all(s["esitmi"] for s in satirlar) and ic_tutarli
    return {
        "gecti": gecti,
        "kunye_dosyasi": KUNYE,
        "kunye_dondurma_utc": kunye.get("dondurma_tarihi_utc"),
        "kunye_son_tarihce_utc": (kunye.get("kunye_tarihcesi") or [{}])[-1].get("tarih_utc"),
        "kunye_ici_tutarli_kosum1_vs_kosum2": ic_tutarli,
        "dosyalar": satirlar,
        "uyusmayan": [s["dosya"] for s in satirlar if not s["esitmi"]],
        "kill2_atesledi": (not gecti),
    }


# =================================================================================================
# [B] TEST KÜMESİ  —  künyeden bağımsız
# =================================================================================================
def _oku(yol: str) -> list[dict]:
    satirlar = []
    with open(yol, encoding="utf-8") as fh:
        for ham in fh:
            ham = ham.strip()
            if ham:
                satirlar.append(json.loads(ham))
    return satirlar


def _takilan_olcutler(p: dict) -> list[str] | None:
    """`meridian/topviews.py::_reddi_et` ile AYNI mantık — ikinci bir yol icat EDİLMEDİ.

    Yapısal iz yoksa None döner ('ret yok' DEĞİL, 'yazılmamış').
    """
    cks = p.get("gate_checks")
    if not isinstance(cks, list) or not cks:
        return None
    return [c.get("check") for c in cks
            if isinstance(c, dict) and c.get("passed") is False]


def test_kumesi() -> dict:
    """`leading_sector`da takılmış VE hiç işleme dönmemiş planlar.

    İŞLEME DÖNME EŞLEŞTİRMESİ: `meridian/topviews.py::topviews` içindeki `islem_by_plan`
    kurgusunun AYNISI — `str(trade.plan_id)` → `str(plan.id)`. Başka eşleştirme yolu YOK.
    """
    planlar = _oku(PLANS)
    islemler = _oku(LEDGER)

    # --- topviews.py ile bayt-aynı birleştirme ---
    islem_by_plan: dict[str, list[dict]] = {}
    for t in islemler:
        pid = t.get("plan_id")
        if pid:
            islem_by_plan.setdefault(str(pid), []).append(t)

    plan_id_kumesi = {str(p.get("id")) for p in planlar if p.get("id")}
    id_benzersiz = len(plan_id_kumesi) == len(planlar)

    iz_yok = [p for p in planlar if _takilan_olcutler(p) is None]
    takilan = [p for p in planlar if (_takilan_olcutler(p) or []) and
               OLCUT in _takilan_olcutler(p)]

    isleme_donen = [p for p in takilan if islem_by_plan.get(str(p.get("id")))]
    kalan = [p for p in takilan if not islem_by_plan.get(str(p.get("id")))]

    # --- SIZINTI KONTROLÜ (kart kill#3): kalanın HİÇBİRİ işleme dönmüş olmayacak ---
    sizanlar = [str(p.get("id")) for p in kalan if islem_by_plan.get(str(p.get("id")))]
    sizinti_temiz = (len(sizanlar) == 0)
    # ikinci, bağımsız yönlü kontrol: hiçbir işlemin plan_id'si kalan kümesinde OLMAYACAK
    kalan_idler = {str(p.get("id")) for p in kalan}
    ters_sizanlar = sorted({str(t["plan_id"]) for t in islemler
                            if t.get("plan_id") and str(t["plan_id"]) in kalan_idler})
    sizinti_temiz = sizinti_temiz and not ters_sizanlar

    # --- ÇAKIŞMA (kart beyanli_sinirlar (3)): yalnız-leading_sector mi, çoklu mu? ---
    yalniz = [p for p in kalan if _takilan_olcutler(p) == [OLCUT]]
    coklu = [p for p in kalan if len(_takilan_olcutler(p)) > 1]
    olcut_sayisi_dagilimi = dict(sorted(Counter(len(_takilan_olcutler(p))
                                                for p in kalan).items()))

    tarihler = sorted(str(p.get("date"))[:10] for p in kalan)
    aylar = sorted({t[:7] for t in tarihler})

    # --- DIŞLAMA YAPISI: dışlamanın test kümesini hangi zaman dilimine indirdiği.
    #     SONUÇ istatistiği DEĞİL (hiçbir R hesaplanmıyor) — K'ya SAYILMAZ; kartın
    #     "dışlama sayıyla kanıtlanır" şartının bütünlük tarafı. ---
    _yil = lambda xs: dict(sorted(Counter(str(p.get("date"))[:4] for p in xs).items()))
    dislama_yapisi = {
        "olcutte_takilan_yil": _yil(takilan),
        "isleme_donen_yil": _yil(isleme_donen),
        "test_kumesi_yil": _yil(kalan),
        "tum_plan_defteri_yil": _yil(planlar),
        "isleme_donen_plan_orani_yil": {
            y: f"{_yil(isleme_donen).get(y, 0)}/{n}"
            for y, n in _yil(takilan).items()},
        "beyan": ("SONUÇ istatistiği DEĞİL, dışlamanın bütünlük kanıtı. Alt-dilim analizi "
                  "YAPILMADI: hiçbir R/beklenti bu kırılımda hesaplanmadı."),
    }

    # --- BEYAN: dışlama işlem-tabanlıdır (kartın kuralı). `broker_status` DIŞLAMADA
    #     KULLANILMADI; yalnız "dokunulmamışlık" beyanının sınırı olarak RAPORLANIR. ---
    broker_dagilimi = dict(sorted(Counter(str(p.get("broker_status")) for p in kalan).items()))
    brokera_gitmis = [str(p.get("id")) for p in kalan
                      if p.get("broker_status") not in (None, "", "none")]

    return {
        "kohort": KOHORT,
        "olcut": OLCUT,
        "kaynak": {"planlar": PLANS, "islemler": LEDGER,
                   "not": "YEREL defterler; canlı okunmadı"},
        "esleştirme_yolu": ("meridian/topviews.py::topviews -> islem_by_plan "
                            "(str(trade.plan_id) -> str(plan.id)); ikinci mantık icat edilmedi"),
        "plan_defteri_n": len(planlar),
        "islem_defteri_n": len(islemler),
        "plan_id_benzersiz": id_benzersiz,
        "gate_checks_izi_olmayan_plan_n": len(iz_yok),
        "dislama": {
            "olcutte_takilan_n": len(takilan),
            "bunlardan_isleme_donen_plan_n": len(isleme_donen),
            "bu_planlardan_dogmus_islem_n": sum(len(islem_by_plan[str(p["id"])])
                                                for p in isleme_donen),
            "test_kumesi_n": len(kalan),
            "aritmetik_tutuyor": len(takilan) - len(isleme_donen) == len(kalan),
        },
        "sizinti_kontrolu": {
            "ileri_yon_sizan_plan": sizanlar,
            "ters_yon_sizan_plan": ters_sizanlar,
            "temiz": sizinti_temiz,
            "kural": "kart kill#3 — işleme DÖNMÜŞ tek bir plan sızarsa geçersiz",
        },
        "cakisma": {
            "yalniz_leading_sector_n": len(yalniz),
            "coklu_olcut_n": len(coklu),
            "takilan_olcut_sayisi_dagilimi": olcut_sayisi_dagilimi,
            "sinir": ("kart beyanli_sinirlar (3): çoklu-ölçüt planlarda kapı TEK BAŞINA "
                      "sorumlu değildir"),
        },
        "dislama_yapisi": dislama_yapisi,
        "test_kumesi_pencere": {
            "ilk_plan": tarihler[0] if tarihler else None,
            "son_plan": tarihler[-1] if tarihler else None,
            "ay_kume_n": len(aylar),
            "not": "ay_kume_n = ay-kümeli bootstrap'ın küme sayısıdır",
        },
        "dokunulmamislik_serhi": {
            "broker_status_dagilimi": broker_dagilimi,
            "brokera_gitmis_ama_islem_olmamis_plan_n": len(brokera_gitmis),
            "brokera_gitmis_plan_idler": brokera_gitmis,
            "beyan": ("bu planlar İŞLEME DÖNMEDİ, o yüzden kartın dışlama kuralına göre test "
                      "kümesindedir; ama bir mekanizma onları GÖNDERMEYİ seçmiştir — kartın "
                      "'dokunulmamıştır' beyanının sınırı budur. Dışlamada KULLANILMADI."),
        },
        "test_kumesi_plan_idler": sorted(str(p.get("id")) for p in kalan),
        "dislanan_plan_idler": sorted(str(p.get("id")) for p in isleme_donen),
    }


# =================================================================================================
# [C] KARŞI-OLGUSAL KOŞUM — donmuş edg032c kasası
# =================================================================================================
REF_SASI = os.path.join(REPO, "research/olcumler/edg032b_tamsatir_2026-08-13/olcum.py")
B1_YASA = ("breakout_vcp", "exhaustion_hammer", "momentum_burst")
REPLAY_END = "2026-07-30"          # edg032c künyesi: pencere.end — kasa sınırı
AS_OF_GENIS = "2026-08-12"         # önbellekteki son endeks barı (yalnız S3 sınaması için)


def kasa_kur() -> dict:
    """edg032c donmuş kasasını kurar: edg032b şasisi + EDG-022 donmuş config'ler + disk barları.

    Şasi AYNEN yüklenir (edg032c/olcum.py::referans_modul deseni); TEK uyarlama şasinin
    dünya-beklentisi sabiti (`ARMED_BEKLENEN` → B1). Motor DEĞİŞTİRİLMEZ.
    `ref.kosum()` ÇAĞRILMAZ — bu kart tam-portföy replay'i değil, plan-başı karşı-olgusal ister.
    """
    sys.path.insert(0, REPO)
    # Şasi KAYNAKTAN derlenir (2026-08-30): argv/SystemExit dansı AYNEN korunur, ama
    # `__pycache__` okunmaz — bayat bytecode on üç ölçümü birden sessizce bozabilirdi.
    # Yerel ithal: `sys.path` kurulumu modül başında yapılıyor. Gerekçe:
    # `ops/sasi_yukleyici.py` başlığı · kapı: tests/test_bayat_bytecode_v334.py §C.
    from ops.sasi_yukleyici import referans_sasi_yukle
    ref = referans_sasi_yukle(REF_SASI)
    ref.SANDBOX = pathlib.Path(CIKTI)              # artefakt koruması: edg032b dizinine yazılmaz
    ref.ARMED_BEKLENEN = B1_YASA
    st_dir = ref.hazirla("edg057")

    from meridian import config
    config.STATE, config.BARS, config.HISTORY = st_dir, st_dir / "bars", st_dir / "history"
    config.reload_config()

    import yaml
    from meridian import backtest, dataset, indicators as ind, regime as regime_mod
    from meridian import score as score_mod, strategy as strat

    # ---- ŞASİ KİMLİK ÇİVİLERİ (şasinin kendi assert'leri AYNEN) ----
    kimlik = {}
    cmb = json.load(open(os.path.join(REPO,
        "research/olcumler/edg032_final_paket_2026-08-12/sonuc_cmb.json"), encoding="utf-8"))
    for f in ("goal.yaml", "strategy.yaml", "bounds.yaml"):
        beklenen = cmb["config_sha256_16"][f]["sandbox"]
        gercek = _sha256(str(st_dir / f))[:16]
        assert gercek == beklenen, f"ŞASİ KİMLİĞİ BOZUK: {f} {gercek} != {beklenen}"
        kimlik[f] = gercek
    assert tuple(strat.ARMED_SETUPS) == B1_YASA, f"MOTOR B1'DEN SAPMIŞ: {strat.ARMED_SETUPS}"
    assert not hasattr(backtest, "wpg_overlay_day"), "motor YAMALI — ölçüm geçersiz"
    yasak = [m for m in sys.modules if m in ref.YASAK]
    assert not yasak, f"yasaklı modül ithal edilmiş: {yasak}"
    assert backtest.DINLENEN_LIMIT is False, "DINLENEN_LIMIT açık — taban dolum kuralı değil"

    # ---- HÜCRE: edg032c künyesindeki MERKEZ (slot 20 · 0.5R · zarf enjeksiyonu YOK) ----
    stg = yaml.safe_load((st_dir / "strategy.yaml").read_text())
    params = dict(stg["params"])
    by_regime = stg.get("params_by_regime") or None
    goal = config.goal()
    assert float(goal["limits"]["heat_hard_r"]) == 5.0
    goal["limits"]["max_open_positions"] = 20
    params["position_size_r"] = 0.5

    # ---- MALİYET MODELİ: tabanla AYNI, indirim YOK ----
    slip_bps = float(goal.get("slippage_bps", 5))
    comm = float(goal.get("commission_per_share", 0.0))
    assert slip_bps == 5.0 and comm == 0.0, f"maliyet modeli tabandan sapmış: {slip_bps}/{comm}"

    # ---- ERKEN İTLAF ATIL MI? (pivot kaydı olmadığı için ŞART) ----
    early_kill = int(params.get("exit.early_kill_pivot", 0))
    assert early_kill == 0, ("exit.early_kill_pivot açık — plan defteri `pivot` taşımıyor, "
                             "pivot=0.0 ile koşmak DAVRANIŞ DEĞİŞTİRİRDİ")

    bars, index = dataset.load_cached()
    # `load_cached` tarih SÜTUNLU çerçeveler döner; replay `_indexed` ile tarihi İNDEKSE alır.
    # Aynı dönüşüm burada da motorun KENDİ fonksiyonuyla yapılır (ikinci uygulama yok).
    per = backtest._indexed(bars)
    return {"ref": ref, "per": per, "st_dir": st_dir, "config": config, "backtest": backtest,
            "ind": ind, "regime_mod": regime_mod, "score_mod": score_mod, "strat": strat,
            "brk": backtest.brk, "params": params, "by_regime": by_regime, "goal": goal,
            "bars": bars, "index": index, "slip_bps": slip_bps, "comm": comm,
            "kimlik": {"config_sha16": kimlik, "sasi_sha256": _sha256(REF_SASI),
                       "armed_setups": list(strat.ARMED_SETUPS),
                       "dinlenen_limit": backtest.DINLENEN_LIMIT,
                       "early_kill_pivot": early_kill,
                       "chandelier_lookback": float(params.get("exit.chandelier_lookback", 0)),
                       "scale_out_frac": float(params.get("exit.scale_out_frac", 0.0)),
                       "params_by_regime_bos": all(not v for v in (by_regime or {}).values()),
                       "hucre": {"slot": 20, "position_size_r": 0.5, "heat_hard_r": 5.0},
                       "maliyet": {"slippage_bps": slip_bps, "commission_per_share": comm}}}


class PITIhlali(AssertionError):
    """Karar anına (t) göre GELECEK bar taşıyan bir çerçeve bir karar fonksiyonuna verildi."""


class PITBekcisi:
    """Her karar çağrısında verilen çerçevenin son barı ≤ karar günü mü — SAYARAK doğrular.

    Kart kill#4'ün doğrudan uygulaması. Yapısal koruma da var (her çağrıya `.loc[:d]` dilimi
    verilir), bu bekçi o yapının HER ÇAĞRIDA tuttuğunu KANITLAR: sayaç raporlanır, tek ihlal
    `PITIhlali` yükseltir ve koşumu durdurur.
    """

    def __init__(self) -> None:
        self.kontrol = 0
        self.ihlal: list[str] = []

    def cerceve(self, df, d, nerede: str, tarih_kolonu: str | None = None):
        son = (df[tarih_kolonu].max() if tarih_kolonu else df.index.max())
        self.kontrol += 1
        if son > d:
            self.ihlal.append(f"{nerede}: son_bar={son} > karar_gunu={d}")
            raise PITIhlali(self.ihlal[-1])
        return df


def rejim_tablosu(idx, takvim, params, regime_mod, bekci: PITBekcisi) -> dict:
    """Karar günü → (regime, exposure_budget_pct). Plandan BAĞIMSIZ, bir kez hesaplanır.

    `regime_ok` yalnız bu ikisini okur (backtest.replay CLOSE(D) satırı AYNEN).
    PIT: her gün için endeks yalnız `.loc[:d]`e dilimlenir ve bekçiden geçer.
    """
    out = {}
    for d in takvim:
        dilim = bekci.cerceve(idx.loc[:d], d, "regime.index")
        rj = regime_mod.build_regime_json(dilim.reset_index(), params, str(d.date()))
        out[d] = (rj["regime"], rj["exposure_budget_pct"])
    return out


def plan_kosu(plan: dict, kasa: dict, takvim: list, rejim: dict, bekci: PITBekcisi,
              *, giris_tarihi: str | None = None, son_bar=None) -> dict:
    """TEK planın karşı-olgusal koşusu — donmuş kasanın KENDİ fonksiyonlarıyla.

    Faz sırası `backtest.replay` ile BİREBİR: OPEN(D) bekleyen çıkış → OPEN(D) dolum →
    INTRADAY(D) dokunma çıkışı → CLOSE(D) trail/rejim/zaman → son barda markout.
    İkinci bir çıkış yasası YAZILMADI; `broker._touch_exit` + `strategy.manage_position`
    çağrılır.

    İZOLASYON (beyanlı): portföy bağlamı YOK — slot/ısı/sektör tavanı, günlük zarar devre
    kesicisi ve risk-azaltma çarpanı UYGULANMAZ. Kart tam da bu bağlamı (kapıyı) kaldırıp
    planın kendi beklentisini soruyor.
    """
    bt, brk, strat, ind = kasa["backtest"], kasa["brk"], kasa["strat"], kasa["ind"]
    params, by_regime, goal = kasa["params"], kasa["by_regime"], kasa["goal"]
    cfg, score_mod = kasa["config"], kasa["score_mod"]
    t = plan["ticker"]
    df = kasa["per"][t]
    if son_bar is not None:
        df = df.loc[:son_bar]

    pdate = pd.Timestamp(giris_tarihi or plan["date"])
    sonra = [d for d in takvim if d > pdate]
    if not sonra:
        return {"plan_id": plan["id"], "dolum": False, "neden": "takvimde sonraki seans yok"}
    dfill = sonra[0]                     # replay: CLOSE(D)'de silahlan, OPEN(D+1)'de dol
    if dfill not in df.index:
        # replay `armed`ı her gün sıfırlar: barsız seansta plan DÜŞER (taşınmaz)
        return {"plan_id": plan["id"], "dolum": False, "neden": "dolum seansında bar yok"}

    # ATR — SİNYAL BARINDA (plan günü), yalnız t'ye dek barlarla. Kayıtta yok, motorun kendi
    # `indicators.atr`ıyla PIT olarak yeniden ölçülür (uydurma yok: ölçülemezse None).
    sinyal_dilim = df.loc[:pdate]
    atr = None
    if len(sinyal_dilim) >= strat.ATR_PERIOD + 1:
        bekci.cerceve(sinyal_dilim, pdate, "atr.signal_bar")
        _a = ind.atr(sinyal_dilim.reset_index(), strat.ATR_PERIOD).iloc[-1]
        atr = float(_a) if pd.notna(_a) and float(_a) > 0 else None

    broker = brk.PaperBroker(score_mod.START_EQUITY, kasa["slip_bps"] / 10000.0, kasa["comm"])
    rej: dict = {}
    adv_dilim = bekci.cerceve(df.loc[:dfill], dfill, "adv.frame")
    pos = broker.fill_entry(plan, float(df.loc[dfill, "open"]), str(dfill.date()),
                            score_mod.START_EQUITY,
                            size_mult=1.0,                       # portföy risk-azaltması YOK
                            adv=bt._adv(adv_dilim, dfill),       # motorun kendi nedensel ADV'si
                            pivot=0.0,                           # kayıtta yok; erken itlaf ATIL
                            atr=atr, gap_at_submit=None,
                            bar_low=None,                        # DINLENEN_LIMIT=False (taban)
                            reject_out=rej)
    if pos is None:
        return {"plan_id": plan["id"], "dolum": False, "neden": rej.get("reason", "?"),
                "red_detay": rej}

    prev_eff = dict(params)
    bekleyen: str | None = None
    kalan_takvim = [d for d in takvim if d >= dfill]
    kapanis = None
    for d in kalan_takvim:
        # ---- 1. OPEN(D): bekleyen çıkış ----
        if bekleyen and d in df.index:
            kapanis = broker.close_position(t, float(df.loc[d, "open"]), bekleyen, str(d.date()))
            break
        # ---- 2. INTRADAY(D): dokunma çıkışı ----
        if d in df.index:
            bar = df.loc[d]
            broker.scale_out(pos, {"high": bar["high"], "low": bar["low"], "open": bar["open"]},
                             prev_eff)
            ex = broker._touch_exit(pos, {"open": bar["open"], "high": bar["high"],
                                          "low": bar["low"]})
            if ex:
                kapanis = broker.close_position(t, ex[0], ex[1], str(d.date()))
                break
            pos.bars_held += 1
        # ---- 3. CLOSE(D): trail / rejim / zaman stopu ----
        rg, exp = rejim[d]
        regime_ok = rg in ("trend_up", "chop") and exp > 0
        eff = cfg.resolve_params(params, by_regime, rg)
        prev_eff = eff
        if d in df.index:
            df_t = bekci.cerceve(df.loc[:d], d, "manage_position.frame").reset_index()
            dec = strat.manage_position(df_t, {"entry": pos.entry, "stop": pos.stop,
                                               "trail_stop": pos.trail_stop,
                                               "r_per_share": pos.r_per_share,
                                               "pivot": pos.pivot},
                                        eff, pos.bars_held, regime_ok)
            pos.trail_stop = dec.trail_stop
            if dec.exit_now:
                bekleyen = dec.exit_reason
    if kapanis is None:
        # kasa penceresi bitti — taban `eod_markout` / `delisted_markout` kuralı AYNEN
        d = kalan_takvim[-1]
        if d in df.index:
            kapanis = broker.close_position(t, float(df.loc[d, "close"]), "eod_markout",
                                            str(d.date()))
        else:
            son_d = df.loc[:d].index.max()
            kapanis = broker.close_position(t, float(df.loc[son_d, "close"]),
                                            "delisted_markout", str(son_d.date()))
    return {"plan_id": plan["id"], "dolum": True, "ticker": t, "plan_date": str(pdate.date()),
            "ts_open": kapanis["ts_open"], "ts_close": kapanis["ts_close"],
            "r_multiple": float(kapanis["r_multiple"]), "exit_reason": kapanis["exit_reason"],
            "bars_held": kapanis.get("bars_held"), "qty": kapanis["qty"]}


# =================================================================================================
# [D] AY-KÜMELİ BOOTSTRAP  (ön-kayıtlı: B=5000, seed=20260812, birim=AY)
# =================================================================================================
def ay_kumeli_bootstrap_ci(degerler: list[float], aylar: list[str],
                           b: int = BOOT_B, seed: int = BOOT_SEED) -> dict:
    """Ortalama R için %95 ay-kümeli bootstrap CI.

    Kurgu EDG-022/EDG-023'ten AYNEN: ay adları yerine-koymalı çekilir, seçilen ayların TÜM
    gözlemleri havuzlanır, istatistik havuzda hesaplanır. İşlem-düzeyi (iid) çekim YASAK —
    ay-içi bağımlılığı yok sayar ve CI'yı sahte biçimde daraltır.
    """
    if len(degerler) != len(aylar):
        raise ValueError("degerler ve aylar aynı uzunlukta olmalı")
    kume: dict[str, list[float]] = {}
    for v, a in zip(degerler, aylar):
        kume.setdefault(a, []).append(float(v))
    adlar = sorted(kume)
    m = len(adlar)
    if m < 2 or len(degerler) < 2:
        return {"lo": None, "hi": None, "orta": None, "n": len(degerler), "ay_kume_n": m,
                "olculemedi_neden": "ay kümesi < 2 — kümeli bootstrap tanımsız"}
    diziler = {a: np.asarray(kume[a], dtype=float) for a in adlar}
    rng = np.random.default_rng(seed)
    idx = np.arange(m)
    ort = np.empty(b, dtype=float)
    for i in range(b):
        sec = rng.choice(idx, size=m, replace=True)
        havuz = np.concatenate([diziler[adlar[j]] for j in sec])
        ort[i] = havuz.mean()
    return {
        "lo": float(np.percentile(ort, 2.5)),
        "hi": float(np.percentile(ort, 97.5)),
        "orta": float(np.median(ort)),
        "n": len(degerler),
        "ay_kume_n": m,
        "B": b,
        "seed": seed,
        "birim": BOOT_BIRIM,
        "olculemedi_neden": None,
    }


def bootstrap_oz_sinamasi() -> dict:
    """Bootstrap fonksiyonunun SENTETİK veriyle öz-sınaması (kohort verisi kullanılmaz).

    Amaç: [C] koşulamasa bile istatistik ucunun doğru ve deterministik olduğu gösterilebilsin.
    Üç çivi: (a) determinizm, (b) sıfır-merkezli veride CI sıfırı içerir,
    (c) ay-kümeli CI, iid işlem-düzeyi CI'dan DAHA GENİŞ (ay-içi bağımlılık varken).
    """
    rng = np.random.default_rng(7)
    n_ay, n_ic = 18, 9
    aylar, degerler = [], []
    for k in range(n_ay):
        ay_etki = rng.normal(0.0, 0.8)              # ay-içi bağımlılık (ortak şok)
        for _ in range(n_ic):
            aylar.append(f"2025-{k % 12 + 1:02d}-K{k}")
            degerler.append(ay_etki + rng.normal(0.0, 0.3))

    a = ay_kumeli_bootstrap_ci(degerler, aylar)
    b = ay_kumeli_bootstrap_ci(degerler, aylar)
    determinist = (a["lo"] == b["lo"] and a["hi"] == b["hi"] and a["orta"] == b["orta"])

    # iid (işlem-düzeyi) karşılaştırma — YALNIZ öz-sınama için; kohorda KULLANILMAZ
    r2 = np.random.default_rng(BOOT_SEED)
    arr = np.asarray(degerler, dtype=float)
    iid = np.empty(BOOT_B)
    for i in range(BOOT_B):
        iid[i] = arr[r2.integers(0, len(arr), len(arr))].mean()
    iid_lo, iid_hi = float(np.percentile(iid, 2.5)), float(np.percentile(iid, 97.5))

    return {
        "a_determinizm": {"gecti": bool(determinist),
                          "not": "aynı seed iki çağrıda bayt-aynı CI verdi"},
        "b_sifir_merkezli_ci_sifiri_iceriyor": {
            "gecti": bool(a["lo"] <= 0.0 <= a["hi"]),
            "ci": [a["lo"], a["hi"]]},
        "c_ay_kumeli_iid_den_genis": {
            "gecti": bool((a["hi"] - a["lo"]) > (iid_hi - iid_lo)),
            "ay_kumeli_genislik": a["hi"] - a["lo"],
            "iid_genislik": iid_hi - iid_lo,
            "not": "ay-içi bağımlılık varken iid bootstrap CI'yı sahte-daraltır"},
        "beyan": "SENTETİK veri; kohort sayılarıyla ilgisi YOKTUR",
    }


# =================================================================================================
# KOHORT KOŞUSU + İSTATİSTİK
# =================================================================================================
_REJIM_ONBELLEK: dict = {}


def kohort_kos(planlar: list[dict], kasa: dict, *, son_bar: str, kaydir_is_gunu: int = 0,
               bekci: PITBekcisi | None = None) -> dict:
    """Verilen planları donmuş kasada koşar. `son_bar` = kasanın sağ sınırı (as_of)."""
    bekci = bekci or PITBekcisi()
    idx = kasa["index"].set_index("date").sort_index()
    ub = pd.Timestamp(son_bar)
    takvim = [d for d in idx.index if d <= ub]
    ilk = min(pd.Timestamp(p["date"]) for p in planlar)
    gerekli = [d for d in takvim if d >= ilk]
    # Rejim tablosu plandan BAĞIMSIZDIR (yalnız endeks + params) → (ilk, son_bar) başına bir kez.
    # Önbellek sonucu DEĞİŞTİRMEZ; üç koşumun (ana/S1/S3) aynı tabloyu yeniden hesaplamasını önler.
    anahtar = (str(ilk.date()), str(son_bar))
    if anahtar in _REJIM_ONBELLEK:
        rejim = _REJIM_ONBELLEK[anahtar]
    else:
        rejim = rejim_tablosu(idx, gerekli, kasa["params"], kasa["regime_mod"], bekci)
        _REJIM_ONBELLEK[anahtar] = rejim

    # ---- REJİM MUTABAKATI: donmuş kasanın hesabı, planın KENDİ kaydıyla uyuşuyor mu? ----
    mutabakat = {"etiket_ayni": 0, "etiket_farkli": 0, "butce_ayni": 0, "butce_farkli": 0,
                 "kasa_butcesi_sifir": 0, "ornekler": []}
    for p in planlar:
        dd = pd.Timestamp(p["date"])
        if dd not in rejim:
            continue
        rg, exp = rejim[dd]
        mutabakat["etiket_ayni" if rg == p.get("regime_at_plan") else "etiket_farkli"] += 1
        canli = next((c.get("value") for c in p["gate_checks"]
                      if c.get("check") == "exposure_budget"), None)
        if canli is not None:
            ayni = (float(canli) == float(exp))
            mutabakat["butce_ayni" if ayni else "butce_farkli"] += 1
            if not ayni and len(mutabakat["ornekler"]) < 5:
                mutabakat["ornekler"].append({"plan_id": p["id"], "date": p["date"],
                                              "canli_butce": canli, "kasa_butce": exp})
        if exp <= 0:
            mutabakat["kasa_butcesi_sifir"] += 1

    satirlar, dolmayan = [], []
    for p in planlar:
        gt = None
        if kaydir_is_gunu:
            sonra = [d for d in takvim if d > pd.Timestamp(p["date"])]
            if len(sonra) <= kaydir_is_gunu:
                dolmayan.append({"plan_id": p["id"], "neden": "kaydırma takvimi aştı"})
                continue
            gt = str(sonra[kaydir_is_gunu - 1].date())
        r = plan_kosu(p, kasa, takvim, rejim, bekci, giris_tarihi=gt, son_bar=ub)
        (satirlar if r.get("dolum") else dolmayan).append(r)
    return {"islemler": satirlar, "dolmayan": dolmayan, "bekci": bekci,
            "son_bar": son_bar, "kaydirma_is_gunu": kaydir_is_gunu,
            "rejim_mutabakati": mutabakat}


def istatistik(satirlar: list[dict], etiket: str) -> dict:
    """Kartın istediği beş büyüklük + ay-kümeli CI. BAŞKA istatistik hesaplanmaz."""
    if not satirlar:
        return {"etiket": etiket, "n": 0, "olculemedi_neden": "kohortta dolan işlem yok"}
    r = [s["r_multiple"] for s in satirlar]
    aylar = [s["ts_open"][:7] for s in satirlar]
    stop_nedenleri = {"stop", "stop_gap"}
    ci = ay_kumeli_bootstrap_ci(r, aylar)
    return {
        "etiket": etiket,
        "n": len(r),
        "toplam_r": round(float(np.sum(r)), 4),
        "ortalama_r": round(float(np.mean(r)), 5),
        "stop_payi": round(sum(1 for s in satirlar
                               if s["exit_reason"] in stop_nedenleri) / len(r), 4),
        "kazanma": round(sum(1 for x in r if x > 0) / len(r), 4),
        "ci95_ay_kumeli": {k: (round(v, 5) if isinstance(v, float) else v) for k, v in ci.items()},
        "ay_kume_n": ci["ay_kume_n"],
        "esik": ESIK,
        "ci_esige_gore": ("CI-ALT > eşik" if (ci["lo"] is not None and ci["lo"] > ESIK)
                          else "CI-ÜST < eşik" if (ci["hi"] is not None and ci["hi"] < ESIK)
                          else "CI eşiği İÇERİYOR"),
        "cikis_nedeni_dagilimi": dict(sorted(Counter(s["exit_reason"]
                                                     for s in satirlar).items())),
    }


# =================================================================================================
# PIT ÖZ-SINAMALARI — üçü de KOŞULUR
# =================================================================================================
def pit_sinamalari(ana: dict, kasa: dict, planlar: list[dict]) -> dict:
    ana_r = {s["plan_id"]: s["r_multiple"] for s in ana["islemler"]}

    # ---- S1: TARİH KAYDIRMA — giriş +5 iş günü; sonuç DEĞİŞMELİ ----
    k = kohort_kos(planlar, kasa, son_bar=REPLAY_END, kaydir_is_gunu=5)
    k_r = {s["plan_id"]: s["r_multiple"] for s in k["islemler"]}
    ortak = sorted(set(ana_r) & set(k_r))
    degisen = [p for p in ortak if abs(ana_r[p] - k_r[p]) > 1e-9]
    s1 = {
        "ad": "S1_tarih_kaydirma",
        "tasarim": ("her plan +5 iş günü kaydırılmış girişle yeniden koşuldu; koşum giriş "
                    "tarihini gerçekten okuyorsa sonuçlar DEĞİŞMELİ (değişmezse sabit/gelecek "
                    "pencere şüphesi)"),
        "kosuldu": True,
        "ortak_islem_n": len(ortak), "degisen_n": len(degisen),
        "degisen_pay": round(len(degisen) / len(ortak), 4) if ortak else None,
        "kaydirilmis_ortalama_r": (round(float(np.mean(list(k_r.values()))), 5) if k_r else None),
        "gecti": bool(ortak) and len(degisen) / len(ortak) > 0.5,
        "yorum_yok": "sayı verildi; hüküm Rol-1'in",
    }

    # ---- S2: GELECEK-BAR ERİŞİM ASSERT'İ ----
    b = ana["bekci"]
    s2 = {
        "ad": "S2_gelecek_bar_erisim_assert",
        "tasarim": ("her karar çağrısına verilen çerçevenin son barı, karar gününden BÜYÜK "
                    "olamaz; `PITBekcisi` bunu her çağrıda sayarak doğrular ve tek ihlalde "
                    "`PITIhlali` yükseltip koşumu durdurur. Yapısal koruma da var: her çağrıya "
                    "`.loc[:d]` dilimi verilir, tam çerçeve HİÇ geçilmez"),
        "kosuldu": True,
        "kontrol_n": b.kontrol, "ihlal_n": len(b.ihlal), "ihlaller": b.ihlal[:10],
        "gecti": (len(b.ihlal) == 0 and b.kontrol > 0),
    }

    # ---- S3: İKİ as_of AYNI SONUÇ ----
    g = kohort_kos(planlar, kasa, son_bar=AS_OF_GENIS)
    g_r = {s["plan_id"]: s["r_multiple"] for s in g["islemler"]}
    g_kapanis = {s["plan_id"]: s["ts_close"] for s in g["islemler"]}
    ortak3 = sorted(set(ana_r) & set(g_r))
    # dar as_of'ta markout ile kesilenler DIŞARIDA: onların farkı sınır etkisidir, sızıntı değil
    kesilen = [s["plan_id"] for s in ana["islemler"] if s["exit_reason"] in
               ("eod_markout", "delisted_markout")]
    kiyas = [p for p in ortak3 if p not in kesilen]
    ayni = [p for p in kiyas if abs(ana_r[p] - g_r[p]) < 1e-12]
    farkli = [p for p in kiyas if abs(ana_r[p] - g_r[p]) >= 1e-12]
    s3 = {
        "ad": "S3_iki_as_of_ayni_sonuc",
        "tasarim": (f"aynı kohort iki `as_of` ile koşuldu: {REPLAY_END} (kasa sınırı) ve "
                    f"{AS_OF_GENIS} (önbellekteki son bar). as_of sonrası bilgi sızmıyorsa, "
                    f"dar pencerede markout'a KESİLMEMİŞ her planın sonucu AYNI olmalı"),
        "kosuldu": True,
        "kiyaslanan_n": len(kiyas), "ayni_n": len(ayni), "farkli_n": len(farkli),
        "farkli_plan_idler": farkli[:10],
        "markout_kesilen_disarida_n": len(kesilen),
        "gecti": (len(farkli) == 0 and len(kiyas) > 0),
    }
    return {"sinamalar": [s1, s2, s3],
            "ozet": f"{sum(1 for x in (s1, s2, s3) if x['gecti'])}/3 geçti",
            "olculemedi_neden": None}


# =================================================================================================
# KILL LİSTESİ — her madde AYRI AYRI, kart sırasıyla
# =================================================================================================
def kill_kontrolleri(kapi: dict, kume: dict, cf: dict, pit: dict, ist: dict) -> list[dict]:
    n_islem = ist.get("n", 0)
    n_plan = kume["dislama"]["test_kumesi_n"]
    s_ad = {s["ad"]: s for s in pit["sinamalar"]}
    return [
        {"no": 1, "kural": "n < 30 → hüküm YOK, betimleyici damga",
         "olculen": {"plan_n": n_plan, "karsi_olgusal_islem_n": n_islem},
         "atesledi": bool(n_islem < 30),
         "not": (f"kohort n (karşı-olgusal İŞLEM) = {n_islem}; plan n = {n_plan}. Kartın "
                 f"metrik listesi (toplam R/ortalama R/stop payı/kazanma) İŞLEM düzeyidir, "
                 f"eşik bu n'e uygulandı")},
        {"no": 2, "kural": "edg032c künyesi (motor sha) ölçüm anında eşleşmezse geçersiz",
         "olculen": {"kosum_oncesi": kapi["gecti"], "kosum_sonrasi": cf["kunye_kosum_sonrasi"],
                     "uyusmayan": kapi["uyusmayan"] + cf["kunye_sonra_uyusmayan"]},
         "atesledi": bool(not kapi["gecti"] or not cf["kunye_kosum_sonrasi"]),
         "not": "künye koşum BAŞINDA ve SONUNDA alındı; ikisi de tabanla eşit olmalı"},
        {"no": 3, "kural": "test kümesine işleme DÖNMÜŞ tek bir plan sızarsa geçersiz",
         "olculen": {"ileri": kume["sizinti_kontrolu"]["ileri_yon_sizan_plan"],
                     "ters": kume["sizinti_kontrolu"]["ters_yon_sizan_plan"]},
         "atesledi": bool(not kume["sizinti_kontrolu"]["temiz"]),
         "not": "iki yönlü kontrol koşuldu"},
        {"no": 4, "kural": "karşı-olgusal koşum gelecek bar okursa geçersiz (üç PIT sınaması)",
         "olculen": {s: s_ad[s]["gecti"] for s in s_ad},
         "atesledi": bool(any(not s_ad[s]["gecti"] for s in s_ad)),
         "not": (f"S2 bekçisi {s_ad['S2_gelecek_bar_erisim_assert']['kontrol_n']} çerçeve "
                 f"kontrolünde {s_ad['S2_gelecek_bar_erisim_assert']['ihlal_n']} ihlal buldu")},
        {"no": 5, "kural": "eşik (sıfır) ölçümden sonra oynatılırsa geçersiz",
         "olculen": {"karttaki_esik": 0.0, "betikteki_esik": ESIK},
         "atesledi": bool(ESIK != 0.0),
         "not": "eşik betikte sabit; kart dosyası SALT OKUNDU, değiştirilmedi"},
        {"no": 6, "kural": "alt-dilim/ikinci eksen eklenirse geçersiz — K donmuştur",
         "olculen": {"kohort_n": 1, "kohortlar": [KOHORT], "eksen_n": 1,
                     "ci_uretilen_ana_olcum_n": 1},
         "atesledi": False,
         "not": ("ANA ÖLÇÜM tek: `leading_sector_ret_islemsiz`, tek eksen, TEK CI. Sektör/rejim/"
                 "yıl alt-kırılımı ARANMADI. Ayrıca üretilen DUYARLILIK koşusu (3 broker-reddi "
                 "planı hariç) ve plan-düzeyi payda AYRI etiketlidir; hangisinin K'ya sayılacağı "
                 "Rol-1'in muhasebesidir — ölçüm ajanı karar vermez")},
    ]


# =================================================================================================
def main() -> int:
    os.makedirs(CIKTI, exist_ok=True)

    print("== [A] KÜNYE KAPISI (koşum ÖNCESİ) ==")
    kapi = kunye_kapisi()
    for s in kapi["dosyalar"]:
        print(f"   {'OK ' if s['esitmi'] else 'FARK'}  {s['dosya']:22s} "
              f"taban={s['taban_sha256'][:16]}  simdi={(s['simdiki_sha256'] or 'YOK')[:16]}")
    print(f"   -> gecti={kapi['gecti']}")
    if not kapi["gecti"]:
        print("KÜNYE KAPISI KAPALI (kill#2) — karşı-olgusal koşum KOŞULMAZ. DUR.")
        return 2

    print("\n== [B] TEST KÜMESİ ==")
    kume = test_kumesi()
    d = kume["dislama"]
    print(f"   {OLCUT} takilan {d['olcutte_takilan_n']} · isleme donen "
          f"{d['bunlardan_isleme_donen_plan_n']} · TEST KUMESI {d['test_kumesi_n']} "
          f"(aritmetik={d['aritmetik_tutuyor']}, sizinti_temiz="
          f"{kume['sizinti_kontrolu']['temiz']})")
    print(f"   yalniz-{OLCUT} {kume['cakisma']['yalniz_leading_sector_n']} / "
          f"coklu {kume['cakisma']['coklu_olcut_n']}")

    print("\n== [C] DONMUŞ KASA KURULUYOR (edg032c) ==")
    kasa = kasa_kur()
    print(f"   sasi={os.path.basename(REF_SASI)} sha={kasa['kimlik']['sasi_sha256'][:16]} · "
          f"ARMED={kasa['kimlik']['armed_setups']}")
    print(f"   config sha16={kasa['kimlik']['config_sha16']} · maliyet={kasa['kimlik']['maliyet']}")
    print(f"   evren={len(kasa['bars'])} sembol · endeks={len(kasa['index'])} satir")

    planlar = _oku(PLANS)
    id2 = {str(p["id"]): p for p in planlar}
    test_planlar = [id2[i] for i in kume["test_kumesi_plan_idler"]]
    assert len(test_planlar) == d["test_kumesi_n"]

    print(f"\n== KARSI-OLGUSAL KOSUM (n_plan={len(test_planlar)}, as_of={REPLAY_END}) ==")
    ana = kohort_kos(test_planlar, kasa, son_bar=REPLAY_END)
    print(f"   dolan islem={len(ana['islemler'])} · dolmayan={len(ana['dolmayan'])}")
    print(f"   dolmama nedenleri="
          f"{dict(sorted(Counter(x['neden'] for x in ana['dolmayan']).items()))}")

    ist = istatistik(ana["islemler"], "ana_165")
    print(f"   n={ist['n']} · toplam_R={ist['toplam_r']} · ortalama_R={ist['ortalama_r']} · "
          f"stop_payi={ist['stop_payi']} · kazanma={ist['kazanma']}")
    print(f"   CI95 ay-kumeli=[{ist['ci95_ay_kumeli']['lo']}, {ist['ci95_ay_kumeli']['hi']}] "
          f"({ist['ay_kume_n']} ay) -> {ist['ci_esige_gore']}")

    # ---- DUYARLILIK (Rol-1 talebi): 3 broker-reddi planı HARİÇ ----
    haric = set(kume["dokunulmamislik_serhi"]["brokera_gitmis_plan_idler"])
    duyarli_satir = [s for s in ana["islemler"] if s["plan_id"] not in haric]
    ist_d = istatistik(duyarli_satir, "duyarlilik_broker_reddi_haric")
    print(f"   [duyarlilik] n={ist_d['n']} ortalama_R={ist_d.get('ortalama_r')} "
          f"CI=[{ist_d.get('ci95_ay_kumeli',{}).get('lo')}, "
          f"{ist_d.get('ci95_ay_kumeli',{}).get('hi')}]")

    # ---- PLAN-DÜZEYİ PAYDA (betimleyici, CI YOK — ikinci çıkarımsal deneme açmamak için) ----
    plan_duzeyi = {
        "payda": "165 plan (dolmayanlar 0R sayılırsa)",
        "n_plan": len(test_planlar), "dolan": len(ana["islemler"]),
        "dolmayan": len(ana["dolmayan"]),
        "ortalama_r_dolmayan_sifir": round(
            float(np.sum([s["r_multiple"] for s in ana["islemler"]])) / len(test_planlar), 5),
        "ci_uretilmedi_neden": ("aynı hipotez için ikinci bir çıkarımsal deneme K'yı gizlice "
                                "büyütürdü (kart kill#6). Betimleyici sayıdır"),
    }

    print("\n== PIT ÖZ-SINAMALARI ==")
    pit = pit_sinamalari(ana, kasa, test_planlar)
    for s in pit["sinamalar"]:
        print(f"   {s['ad']:32s} gecti={s['gecti']}")

    # künye koşum SONRASI
    kapi_sonra = kunye_kapisi()
    cf = {"kosuldu": True, "as_of": REPLAY_END,
          "kunye_kosum_sonrasi": kapi_sonra["gecti"],
          "kunye_sonra_uyusmayan": kapi_sonra["uyusmayan"],
          "kasa_kimligi": kasa["kimlik"],
          "izolasyon_beyani": [
              "portföy bağlamı UYGULANMADI: slot/ısı/sektör tavanı, günlük zarar devre kesicisi,"
              " risk-azaltma çarpanı (size_mult=1.0) — kart bu bağlamı kaldırıp planın kendi"
              " beklentisini soruyor",
              "equity sabit 100.000 (score.START_EQUITY); R ölçek-değişmezdir, yalnız qty"
              " yuvarlaması/ADV/notional tavanı ikinci derece etki bırakır",
              "pivot=0.0 — plan defteri pivot taşımaz; donmuş params'ta"
              " exit.early_kill_pivot=0 olduğu ASSERT'lendi, yani davranış BİREBİR",
              "ATR sinyal barında motorun kendi indicators.atr'ıyla PIT olarak yeniden ölçüldü"
              " (kayıtta yok); ölçülemezse None (uydurma yok)",
              "bar_low=None — DINLENEN_LIMIT=False, taban dolum kuralı AYNEN",
              f"kasa sağ sınırı {REPLAY_END} (edg032c pencere.end); orada açık kalan pozisyon"
              " tabanın eod_markout kuralıyla kapatıldı",
          ],
          "rejim_mutabakati": ana["rejim_mutabakati"],
          "cikis_nedeni_dagilimi": dict(sorted(Counter(x["exit_reason"]
                                                       for x in ana["islemler"]).items())),
          "regime_flip_ilk_barda_n": sum(1 for x in ana["islemler"]
                                         if x["exit_reason"] == "regime_flip"
                                         and (x.get("bars_held") or 0) <= 1),
          "dolmayan_dagilimi": dict(sorted(Counter(x["neden"]
                                                   for x in ana["dolmayan"]).items())),
          "dolmayan_detay": ana["dolmayan"]}

    killer = kill_kontrolleri(kapi, kume, cf, pit, ist)
    print("\n== KILL ==")
    for kk in killer:
        print(f"   #{kk['no']} {'ATESLEDI' if kk['atesledi'] else 'temiz':9s} {kk['kural'][:60]}")

    sonuc = {
        "card_id": "EDG-2026-057",
        "kohort": KOHORT,
        "hukum": None,
        "hukum_notu": "Bu dosya HÜKÜM İÇERMEZ. Ölçüm ajanı sayı üretir; hükmü Rol-1 işler.",
        "kunye_kapisi_once": kapi,
        "kunye_kapisi_sonra": kapi_sonra,
        "test_kumesi": kume,
        "karsi_olgusal": cf,
        "istatistik": {
            "on_kayitli_kurulum": {"B": BOOT_B, "seed": BOOT_SEED, "birim": BOOT_BIRIM,
                                   "esik": ESIK, "olcu": "ortalama R",
                                   "eslenik_notu": ("kartın 'eşlenik' ibaresi bu deponun standart "
                                                    "kurulumunun adıdır; TEK kohortta eşlenecek "
                                                    "ikinci kol yoktur, ölçü ay-kümeli CI'ya "
                                                    "indirgenir")},
            "ANA": ist,
            "duyarlilik_broker_reddi_haric": ist_d,
            "plan_duzeyi_payda_betimleyici": plan_duzeyi,
            "bootstrap_oz_sinamasi_sentetik": bootstrap_oz_sinamasi(),
        },
        "islemler": ana["islemler"],
        "pit_sinamalari": pit,
        "kill_kontrolleri": killer,
    }
    with open(os.path.join(CIKTI, "sonuc.json"), "w", encoding="utf-8") as fh:
        json.dump(sonuc, fh, ensure_ascii=False, indent=1)
    with open(os.path.join(CIKTI, "pit_sinama.json"), "w", encoding="utf-8") as fh:
        json.dump(pit, fh, ensure_ascii=False, indent=1)
    print(f"\nyazildi: {CIKTI}/sonuc.json, pit_sinama.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
