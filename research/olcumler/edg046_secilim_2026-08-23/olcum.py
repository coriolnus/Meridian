"""EDG-2026-046 — friksiyon-bilinçli seçilim · ölçüm koşumu (2026-08-23).

KART: research/cards/EDG-2026-046-friksiyon-bilincli-secilim.yaml (OKU-DOKUNMA; hüküm Rol-1'in).
Ölçüm ajanı karta DOKUNMAZ; bu betik HÜKÜM VERMEZ, sayı getirir. İKİ-DÜNYA karar kuralının
okunması Rol-1'in işidir — "aday/değil" yorumu bu betikte ve raporunda YOKTUR.

NE YAPAR: edg032c tabanının dünyasını (B1-sonrası; edg032b şasisi + ARMED_BEKLENEN=B1 uyarlaması
AYNEN) 4 hücrede koşar (K += 4):
  sabit_mevcut  = bugünkü model (sabit 5 bps + skor-sıralı seçilim) → ŞASİ KAPISI hücresi
  sabit_cezali  = sabit 5 bps dünya + ATR%-cezalı seçilim
  atr_mevcut    = ATR%-orantılı friksiyon dünyası + mevcut seçilim
  atr_cezali    = ATR%-orantılı dünya + ATR%-cezalı seçilim

════════ ŞASİ: YENİDEN KURULMAZ, ÇAĞRILIR (edg032c/edg040/exe006b deseni AYNEN) ════════
edg032b/olcum.py importlib ile modül olarak yüklenir, `SANDBOX`ı BU dizine çevrilir (artefakt
koruması YAPISAL), `ARMED_BEKLENEN`i B1 yasasına çevrilir (edg032c'nin BEYANLI TEK UYARLAMASI
AYNEN — taban kimliğinin parçası; motor ARMED_SETUPS B1'den saparsa koşum BAŞLAMADAN durur)
ve `kosum(run, smoke)` yolu OLDUĞU GİBİ çağrılır. HİÇBİR parametre enjeksiyonu YOK (4 hücre de
merkez: slot 20 · size 0,5R · zarf 5R).

════════ ENJEKSİYON YÜZEYLERİ (koddan okundu, varsayılmadı) ════════
(1) ATR%-ORANTILI DÜNYA — slip_i = 5bps × (ATR%_i / medyan-ATR%):
    Motorun slip'i broker örneğinde skalerdir: broker.py:476 `self.slip = slippage_bps/10000`;
    değdiği üç satır (edg040 tespiti, bugünkü motorda doğrulandı): giriş broker.py:611
    `base_fill = next_open*(1+self.slip)`, kısmi satış :734 `level*(1-self.slip)`, çıkış :765
    `raw_exit*(1-self.slip)`. Enjeksiyon: `PaperBroker.fill_entry/close_position/scale_out`
    SÜREÇ-İÇİ sarmalanır (edg040 fiyat-kancası deseni); fill çağrısı sırasında `self.slip`
    işlem-özel s_i'ye çevrilir, dönüşte tabana konur. ATR%_i = atr/entry_trigger; `atr` fill'e
    motorun kendisinin geçirdiği silahlanma-anı ATR'sidir (backtest.py:337 `atr=armed_atr.get(t)`;
    :543-544 `armed_atr[sig.ticker] = float(sig.atr) if >0 else None` — ölçülemedi → None).
    Çıkış/kısmi satış AYNI işlemin s_i'sini öder (ticker→s_i haritası; fill'de yazılır,
    kapanışta düşer). ATR ölçÜLEMEYEN girişte (motor None geçirir) s_i = TABAN 5 bps
    (slip=0 friksiyonsuz-dolum uydurması olurdu; sayısı raporlanır — UYDURMA YASAĞI).
(2) ATR%-CEZALI SEÇİLİM — skor' = skor − λ·z(ATR%), λ = 5 (TEK NOKTA DONUK, kill#3):
    Şasinin aday-sıralama yolu backtest.py:438 `candidates.sort(key=lambda s: s.score,
    reverse=True)` — kabul skor-sıralıdır (EDG-034 Faz-0 + keşif belgesi teyidi). Motor dosyası
    DEĞİŞTİRİLMEZ: `strat.scan_entry` sarmalanır, dönen sinyal bir vekil nesneye (proxy)
    sarılır; vekilin `score` özelliği YALNIZ o sort satırının lambda'sından okunduğunda
    (çağıran çerçevenin kod nesnesi `replay.__code__.co_consts` içindeki satır-438 lambda'sının
    KENDİSİ ise — sys._getframe deseni şasinin kendi kancasında emsalli) cezalı skoru döndürür;
    plan/defter/kapı okumaları HAM skoru görür. Böylece ceza yalnız SIRALAMAYA iner — kapının
    score_band okuması (guard.py:534-536 plan.get("score")) ve defter `score` alanı ham kalır
    (kill#4 koruması: ceza başka yüzeye sızmaz; kanıt: defter score alanları int + ham/sort
    okuma sayaçları). z, ADAY KÜMESİ içinde GÜNLÜK hesaplanır (PIT: yalnız plan alanları):
    gün sınırı `regime_mod.build_regime_json` sarmalayıcısından (scan bloğundan önce çağrılır,
    backtest.py:377); z = (ATR% − ort)/std, std popülasyon (ddof=0), aday kümesi içinde ATR
    ölçülemeyen sinyal z kümesine GİRMEZ ve cezası 0 (motorun kendi 'ölçülemedi → None' yasası
    izlenir); std=0 ya da n<2 → tüm cezalar 0 (sayılır).
    MEDYAN-ATR% ÇAPASI: sabit_mevcut hücresinde DOLAN girişlerin ATR% (atr/entry_trigger)
    medyanı (statistics.median; atr ölçülemeyenler dışarıda) — dört hücrede AYNI DONMUŞ skaler
    (cezalı hücrenin kendi seçiliminden türetilseydi dünya tanımı seçilime bağlanırdı).
    Duman kendi medyanını duman-sabit_mevcut'tan alır.

════════ ÖZ-SINAMA (kill#2) — satır başına beklenen slip, 1e-9, likidite ayrıştırılmış ════════
edg040 rekonstrüksiyonu satır-slip'li hâliyle AYNEN: G1 broker_slip == beklenen s_i (birebir);
G2 |fill / recon(s_i) − 1| ≤ 1e-9 (recon = broker.py:611-624 + size_position aritmetiğinin
birebir kopyası; likidite payı ADV-kırpma-sonrası/nominal-kırpma-öncesi qty ile — edg040 dersi);
Ç1 defter['exit'] == defter_yuvarla(raw_exit×(1−s_i), 4) — 045'in ALET DERSİ AYNEN: defter
yazımı round(...,4) AMA işlenen tipi reason yoluna göre KARMA (np.float64 bar-fiyat yolları /
Python-float plan-alanı yolları; edg045/olcum.py `defter_yuvarla` modeli birebir); Ç2
|(1−beklenen/raw_exit) − s_i| ≤ 1e-9. Çıkışın beklenen s_i'si kayıttan DEĞİL, o işlemin GİRİŞ
ATR%'sinden bağımsız yeniden türetilir (ticker bazında i. çıkış ↔ i. giriş; pozisyon tekil).
Kill#2 TÜM satırlara uygulanır (kart: "satır başına"), yalnız ilk-20'ye değil.

SEÇİLİM-FARKI SAYIMI (kart features_asof): cezalı hücrelerde sort-düzeyi (gün başına ham-sıra
↔ cezalı-sıra; kaç aday yer değiştirdi, kaç günde sıra değişti) + dört hücrede defter-düzeyi
(ticker, ts_open) kıyası kendi dünyasının mevcut hücresine karşı.

Δ+CI (kart, donuk): cezalının kıyası AYNI dünyadaki mevcut hücresine — Δ(sabit_cezali−
sabit_mevcut) ve Δ(atr_cezali−atr_mevcut); ek betimleyici Δ(atr_mevcut−sabit_mevcut) (dünya
etkisi). EŞLENİK ay-kümeli bootstrap B=5000 seed 20260812 (edg040 `delta_pnl_ci` AYNEN).

KILL'LER (karttan, donuk):
  kill#1 şasi kapısı: sabit_mevcut ≢ edg032c/kosum1 (üç defter sha256) → DUR (exit 2).
  kill#2 öz-sınama: satır-başına beklenen slip 1e-9'da düşerse hücre geçersiz → DUR + rapor.
  kill#3 λ: modül sabiti LAMBDA_CEZA=5.0 — koşum sırasında değiştirilemez (tek nokta donuk).
  kill#4 PIT: ceza YALNIZ sig.atr/entry_trigger plan alanlarından (menzil% YOK, ADV YOK).
  kill#5 iki-dünya: bu betik 4 hücrenin 4'ünü de koşar; tek-dünya hükmü zaten Rol-1'de yasak.
  + motor sha (broker/backtest/strategy/guard) hücre başı önce/sonra — değişirse hücre geçersiz.

DİSİPLİN: UYDURMA YASAĞI (ölçülemeyen None + neden) · YASA-4 (sessiz-yutma işaretli) · git
KOŞULMAZ · state/ YAZILMAZ (şasi kendi sandbox'ına yönlendirir) · test suite KOŞULMAZ · motor
dosyalarına DOKUNULMAZ (tüm yamalar süreç-içi; restorasyon ExitStack-finally + şasinin kendi
assert'leri) · karta/ROADMAP'e YAZILMAZ.

KULLANIM:
  olcum.py --smoke   # [1] DUMAN: dar pencere (2022-01→06) — dört tel birlikte
  olcum.py           # [2]-[5] TAM: şasi kapısı → medyan → 3 hücre → Δ+CI → grid raporu
"""
from __future__ import annotations

import contextlib
import datetime as dt
import hashlib
import importlib.util
import json
import math
import pathlib
import statistics
import sys
import types

BURASI = pathlib.Path(__file__).resolve().parent
REPO = BURASI.parents[2]
REFERANS = REPO / "research" / "olcumler" / "edg032b_tamsatir_2026-08-13" / "olcum.py"
EDG032C = REPO / "research" / "olcumler" / "edg032c_taban_2026-08-22"
sys.path.insert(0, str(REPO))

TABAN_BPS = 5.0                 # bugünkü model (frozen goal: slippage_bps 5) — dünya çapası
LAMBDA_CEZA = 5.0               # kart: z-skor başına 5 puan — TEK NOKTA DONUK (kill#3)
BOOT_SEED = 20260812
BOOT_ITER = 5000
B1_YASA = ("breakout_vcp", "exhaustion_hammer", "momentum_burst")   # edg032c uyarlaması AYNEN
SORT_SATIR_BEKLENEN = "candidates.sort(key=lambda s: s.score, reverse=True)"
MOTOR_SHA_DOSYALAR = ("broker.py", "backtest.py", "strategy.py", "guard.py")

# hücre tanımı: (dünya, seçilim) — dördü de merkez parametreli ({} → şasi MERKEZ'i)
HUCRELER = {
    "sabit_mevcut": ("sabit", "mevcut"),
    "sabit_cezali": ("sabit", "cezali"),
    "atr_mevcut":   ("atr",   "mevcut"),
    "atr_cezali":   ("atr",   "cezali"),
}

# ── DEFTER-YENİDEN-KURMA YUVARLAMASI — edg045/olcum.py `defter_yuvarla` modeli AYNEN ──
# Motor: broker.py:790 `"exit": round(exit_fill, 4)`; işlenen TİP reason yoluna göre değişir
# (bar-fiyatı yolları pandas .loc → np.float64.__round__; plan-alanı yolları Python float →
# Python round). Karma model edg045'te kayıtlı defterlerde 885/885 doğrulandı.
NP_YUVARLANAN_REASONLAR = frozenset(
    {"stop_gap", "target_gap", "time_stop", "regime_flip", "eod_markout", "delisted_markout"})


def defter_yuvarla(x: float, reason: str) -> float:
    """Motorun round(exit_fill, 4) yazımını reason'ın TİP yoluyla birebir yeniden kurar."""
    import numpy as np
    if reason in NP_YUVARLANAN_REASONLAR:
        return float(round(np.float64(x), 4))
    return round(x, 4)


def _sha_full(p: pathlib.Path) -> str | None:
    try:
        return hashlib.sha256(p.read_bytes()).hexdigest()
    except OSError:
        return None    # ölçülemedi (dosya yok/okunamadı)


def motor_sha() -> dict:
    return {f: _sha_full(REPO / "meridian" / f) for f in MOTOR_SHA_DOSYALAR}


def referans_modul():
    """edg032b şasisini modül olarak yükler; SANDBOX'ı BU dizine çevirir; ARMED_BEKLENEN'i
    B1 yasasına çevirir (edg032c'nin beyanlı TEK uyarlaması AYNEN); motoru B1'e assert'ler."""
    sp = importlib.util.spec_from_file_location("edg032b_ref", REFERANS)
    m = importlib.util.module_from_spec(sp)
    eski_argv = sys.argv
    sys.argv = [str(REFERANS)]
    try:
        sp.loader.exec_module(m)
    except SystemExit:                # `__main__` bloğu — içe aktarmada beklenir (desen AYNEN)
        pass
    finally:
        sys.argv = eski_argv
    m.SANDBOX = BURASI                # artefakt koruması: edg032b dizinine ASLA yazılmaz
    eski_beklenen = tuple(m.ARMED_BEKLENEN)
    m.ARMED_BEKLENEN = B1_YASA
    from meridian import strategy as _st
    assert tuple(_st.ARMED_SETUPS) == B1_YASA, \
        f"MOTOR B1 YASASINDAN SAPMIŞ: {_st.ARMED_SETUPS} ≠ {B1_YASA} — koşum durdu"
    return m, {"eski_ARMED_BEKLENEN": list(eski_beklenen),
               "yeni_ARMED_BEKLENEN": list(B1_YASA),
               "motor_ARMED_SETUPS": list(_st.ARMED_SETUPS)}


# ---------------------------------------------------------------------------------------------
# CEZA SARMALAYICISI — sıralama-hedefli vekil (proxy); plan/defter/kapı HAM skoru görür
# ---------------------------------------------------------------------------------------------
def sort_lambda_bul():
    """backtest.py:438 sort lambda'sının KOD NESNESİNİ bulur (satır kaynaktan doğrulanır)."""
    from meridian import backtest
    kaynak = pathlib.Path(backtest.__file__)
    satirlar = kaynak.read_text(encoding="utf-8").splitlines()
    hitler = [i for i, ln in enumerate(satirlar, 1) if SORT_SATIR_BEKLENEN in ln]
    assert len(hitler) == 1, \
        f"aday-sıralama satırı tekil bulunamadı ({len(hitler)} eşleşme) — enjeksiyon noktası kayıp, DUR"
    satir = hitler[0]
    adaylar = [c for c in backtest.replay.__code__.co_consts
               if isinstance(c, types.CodeType) and c.co_name == "<lambda>"
               and c.co_firstlineno == satir]
    assert len(adaylar) == 1, f"sort lambda kod nesnesi tekil değil (n={len(adaylar)}, satır {satir})"
    kod = adaylar[0]
    assert kod.co_freevars == (), "sort lambda'sı serbest değişken taşıyor — desen beklenmedik, DUR"
    return kod, satir


class _CezaliAday:
    """scan_entry sinyalinin vekili. `score` YALNIZ sort-lambda'sından okunduğunda cezalı;
    diğer tüm okumalar (plan üretimi, candidate_log, kapı girdisi) HAM sinyal skorudur."""
    __slots__ = ("_sig", "_durum", "_cezali_deger")

    def __init__(self, sig, durum):
        object.__setattr__(self, "_sig", sig)
        object.__setattr__(self, "_durum", durum)
        object.__setattr__(self, "_cezali_deger", None)

    def __getattr__(self, ad):                       # score DIŞINDAKİ her şey sinyale iletilir
        return getattr(object.__getattribute__(self, "_sig"), ad)

    @property
    def score(self):
        d = object.__getattribute__(self, "_durum")
        if sys._getframe(1).f_code is d["lambda_kod"]:
            if not d["z_hazir"]:
                _z_uygula(d)
            d["sort_okuma_n"] += 1
            return object.__getattribute__(self, "_cezali_deger")
        d["ham_okuma_n"] += 1
        return object.__getattribute__(self, "_sig").score


def _z_uygula(d: dict) -> None:
    """Günün aday kümesi üzerinde z(ATR%) hesaplar, her vekile cezalı skoru yazar ve ham↔cezalı
    sıra farkını kaydeder. ATR ölçülemeyen sinyal z kümesine GİRMEZ, cezası 0 (uydurma yok)."""
    tampon = d["tampon"]
    olculen: list[tuple] = []
    for p in tampon:
        sig = object.__getattribute__(p, "_sig")
        a = float(sig.atr) if sig.atr else 0.0
        t_ = float(sig.entry_trigger) if sig.entry_trigger else 0.0
        if a > 0 and t_ > 0:
            olculen.append((p, a / t_))
        else:
            d["atr_olculemeyen_aday_n"] += 1
    for p in tampon:                                            # varsayılan: ceza 0
        object.__setattr__(p, "_cezali_deger",
                           float(object.__getattribute__(p, "_sig").score))
    n = len(olculen)
    sd = 0.0
    if n >= 2:
        vals = [v for _, v in olculen]
        mu = sum(vals) / n
        sd = math.sqrt(sum((v - mu) ** 2 for v in vals) / n)    # popülasyon (ddof=0)
    if sd > 0:
        for p, v in olculen:
            z = (v - mu) / sd
            object.__setattr__(p, "_cezali_deger",
                               float(object.__getattribute__(p, "_sig").score) - LAMBDA_CEZA * z)
    else:
        d["sd_sifir_tur_n"] += 1
    m = len(tampon)
    ham = sorted(range(m), key=lambda i: -float(object.__getattribute__(tampon[i], "_sig").score))
    cez = sorted(range(m), key=lambda i: -float(object.__getattribute__(tampon[i], "_cezali_deger")))
    kayan = sum(1 for i in range(m) if ham[i] != cez[i])
    d["tur_kayitlari"].append({"tarih": d["gun"], "aday_n": m, "z_kumesi_n": n,
                               "kayan_aday_n": kayan, "sira_degisti": kayan > 0})
    d["z_hazir"] = True


def yeni_ceza_durumu(lambda_kod) -> dict:
    return {"lambda_kod": lambda_kod, "tampon": [], "z_hazir": False, "gun": None,
            "sort_okuma_n": 0, "ham_okuma_n": 0, "atr_olculemeyen_aday_n": 0,
            "sd_sifir_tur_n": 0, "gun_sonu_sortsuz_n": 0, "tur_kayitlari": []}


@contextlib.contextmanager
def ceza_sarmala(durum: dict):
    """`strat.scan_entry`i sarmalar (vekil döndürür) + gün sınırını `build_regime_json`dan izler.
    Şasi kendi kancalarını BUNLARIN ÜSTÜNE sarar (edg040 mb_suz emsali) — sayaçlar tutarlı."""
    from meridian import backtest as BT
    asil_scan = BT.strat.scan_entry
    asil_regime = BT.regime_mod.build_regime_json

    def scan_sarmal(*a, **k):
        if durum["z_hazir"]:                     # yedek sınır (esas sınır regime sarmalında)
            durum["tampon"] = []
            durum["z_hazir"] = False
        sig = asil_scan(*a, **k)
        if sig is None:
            return None
        p = _CezaliAday(sig, durum)
        durum["tampon"].append(p)
        return p

    def regime_sarmal(idx_df, params_, asof):
        tarih = str(asof)[:10]
        if tarih != durum["gun"]:
            if durum["tampon"] and not durum["z_hazir"]:
                durum["gun_sonu_sortsuz_n"] += 1  # sessiz-yutma değil: sayılır (YASA-4)
            durum["tampon"] = []
            durum["z_hazir"] = False
            durum["gun"] = tarih
        return asil_regime(idx_df, params_, asof)

    BT.strat.scan_entry = scan_sarmal
    BT.regime_mod.build_regime_json = regime_sarmal
    try:
        yield
    finally:
        BT.strat.scan_entry = asil_scan
        BT.regime_mod.build_regime_json = asil_regime


def ceza_on_sinama(lambda_kod) -> dict:
    """Ceza telinin SENTETİK ön-sınaması (koşumdan önce; motor koşmaz): gerçek sort-lambda kod
    nesnesi fonksiyona çevrilip 3 yapay sinyal üzerinde sıralama koşulur — cezalı sıranın elle
    hesaplanan beklentiye eşit olduğu ve sort-dışı okumanın HAM kaldığı assert'lenir."""
    NS = types.SimpleNamespace
    durum = yeni_ceza_durumu(lambda_kod)
    durum["gun"] = "sentetik"
    # ATR%: s1=0.02 · s2=0.08 · s3=0.04 → mu=14/300, sd(pop)=sqrt(((...)²)/3)
    sigs = [NS(score=90, atr=2.0, entry_trigger=100.0),
            NS(score=89, atr=8.0, entry_trigger=100.0),
            NS(score=88, atr=2.0, entry_trigger=50.0)]
    vek = [_CezaliAday(s, durum) for s in sigs]
    durum["tampon"] = list(vek)
    f = types.FunctionType(lambda_kod, {})           # gerçek lambda kodu → çağrılabilir
    sirali = sorted(vek, key=f, reverse=True)        # property sort-yolunu birebir tetikler
    vals = [0.02, 0.08, 0.04]
    mu = sum(vals) / 3
    sd = math.sqrt(sum((v - mu) ** 2 for v in vals) / 3)
    beklenen = [s.score - LAMBDA_CEZA * ((v - mu) / sd) for s, v in zip(sigs, vals)]
    bek_sira = [sigs[i].score for i in
                sorted(range(3), key=lambda i: -beklenen[i])]
    gercek_sira = [object.__getattribute__(p, "_sig").score for p in sirali]
    assert gercek_sira == bek_sira, f"ceza ön-sınaması: sıra {gercek_sira} ≠ beklenen {bek_sira}"
    assert bek_sira != [90, 89, 88], "ceza ön-sınaması ayırt edici değil (sıra zaten hamla aynı)"
    assert vek[0].score == 90 and isinstance(vek[0].score, int), \
        "sort-dışı okuma HAM değil — vekil sızdırıyor"
    assert durum["ham_okuma_n"] >= 1 and durum["sort_okuma_n"] == 3
    return {"gecti": True, "beklenen_cezali": [round(b, 6) for b in beklenen],
            "cezali_sira_skorlari": gercek_sira,
            "sort_okuma_n": durum["sort_okuma_n"], "ham_okuma_n": durum["ham_okuma_n"]}


# ---------------------------------------------------------------------------------------------
# DÜNYA KANCALARI — sabit: yalnız yakalama · atr: işlem-başına slip enjeksiyonu + yakalama
# ---------------------------------------------------------------------------------------------
def _beklenen_slip(atr, entry_trigger, dunya: str, medyan_atrpct: float | None):
    """(slip_orani, atrpct|None, olculemedi) — fill sarmalayıcısı ve öz-sınama AYNI türetimi
    kullanır (G1 tutarlılık çivisi; bağımsız doğrulama G2/Ç1'in fiyat aritmetiğidir)."""
    a = float(atr) if atr else 0.0
    t_ = float(entry_trigger) if entry_trigger else 0.0
    atrpct = (a / t_) if (a > 0 and t_ > 0) else None
    if dunya == "sabit":
        return TABAN_BPS / 10000.0, atrpct, False
    if atrpct is None:
        return TABAN_BPS / 10000.0, None, True      # ölçülemedi → taban (uydurma 0-slip yok)
    return (TABAN_BPS * (atrpct / medyan_atrpct)) / 10000.0, atrpct, False


@contextlib.contextmanager
def dunya_kancalari(kayit: dict, dunya: str, medyan_atrpct: float | None):
    """`PaperBroker.fill_entry/close_position/scale_out` sarmalanır. sabit dünyada `self.slip`e
    DOKUNULMAZ (yalnız ham yakalama — şasi kapısının nötrlük kanıtı); atr dünyasında üç slip
    satırının üçü de işlem-özel s_i ile çalışır. Süreç-içi; motor DOSYASI yamasız."""
    from meridian import broker as B
    asil_fill = B.PaperBroker.fill_entry
    asil_close = B.PaperBroker.close_position
    asil_scale = B.PaperBroker.scale_out
    harita = kayit["acik_slip"]

    def fill(self, plan, next_open, ts, equity, **kw):
        s_i, atrpct, olculemedi = _beklenen_slip(kw.get("atr"), plan.get("entry_trigger"),
                                                 dunya, medyan_atrpct)
        if dunya == "atr":
            if olculemedi:
                kayit["atr_olculemeyen_giris_deneme_n"] += 1
            eski = self.slip
            self.slip = s_i
            try:
                pos = asil_fill(self, plan, next_open, ts, equity, **kw)
                uygulanan = self.slip
            finally:
                self.slip = eski
        else:
            pos = asil_fill(self, plan, next_open, ts, equity, **kw)
            uygulanan = self.slip
        if pos is not None:
            if dunya == "atr":
                harita[pos.ticker] = uygulanan
            adv = kw.get("adv")
            kayit["giris"].append({
                "ticker": pos.ticker, "ts": ts, "next_open": float(next_open),
                "adv": (float(adv) if adv else None),
                "fill_yuvarlanmamis": float(pos.entry), "qty": int(pos.qty),
                "stop": float(plan["stop"]), "size_r": float(plan["size_r"]),
                "size_mult": float(kw.get("size_mult", 1.0)), "equity": float(equity),
                "atr": (float(kw["atr"]) if kw.get("atr") else None),
                "entry_trigger": (float(plan["entry_trigger"])
                                  if plan.get("entry_trigger") else None),
                "atrpct": atrpct, "atr_olculemedi": olculemedi,
                "broker_slip": float(uygulanan)})
        return pos

    def close(self, ticker, raw_exit, reason, ts):
        if dunya == "atr":
            s = harita.get(ticker)
            assert s is not None, \
                f"ATR dünyası: {ticker} slip haritasında yok — kapanış slip'i türetilemez, DUR"
            eski = self.slip
            self.slip = s
            try:
                row = asil_close(self, ticker, raw_exit, reason, ts)
                uygulanan = s
            finally:
                self.slip = eski
            harita.pop(ticker, None)
        else:
            row = asil_close(self, ticker, raw_exit, reason, ts)
            uygulanan = self.slip
        kayit["cikis"].append({
            "ticker": ticker, "ts": ts, "raw_exit": float(raw_exit),
            "defter_exit": float(row["exit"]), "qty": int(row["qty"]),
            "broker_slip": float(uygulanan), "reason": reason})
        return row

    def scale(self, pos, bar, params):
        if dunya == "atr":
            s = harita.get(pos.ticker)
            assert s is not None, \
                f"ATR dünyası: {pos.ticker} slip haritasında yok (scale_out) — DUR"
            eski = self.slip
            self.slip = s
            try:
                yapti = asil_scale(self, pos, bar, params)
            finally:
                self.slip = eski
        else:
            yapti = asil_scale(self, pos, bar, params)
        if yapti:
            kayit["scale_out_n"] += 1
        return yapti

    B.PaperBroker.fill_entry = fill
    B.PaperBroker.close_position = close
    B.PaperBroker.scale_out = scale
    try:
        yield
    finally:
        B.PaperBroker.fill_entry = asil_fill
        B.PaperBroker.close_position = asil_close
        B.PaperBroker.scale_out = asil_scale


def yeni_kayit() -> dict:
    return {"giris": [], "cikis": [], "acik_slip": {}, "scale_out_n": 0,
            "atr_olculemeyen_giris_deneme_n": 0}


# ---------------------------------------------------------------------------------------------
# ÖZ-SINAMA — kill#2: satır başına beklenen slip; likidite terimi ayrıştırılmış (1e-9)
# ---------------------------------------------------------------------------------------------
def _fill_rekonstruksiyon(g: dict, s: float, cf: float, risk_pct: float,
                          adv_cap: float) -> tuple[float, int]:
    """Motorun dolum aritmetiğinin BİREBİR kopyası (broker.py:611-624 + size_position:501-512),
    yalnız slip DIŞARIDAN. Likidite payı ADV-kırpma-sonrası/nominal-kırpma-ÖNCESİ qty ile
    (edg040 ilk-tur dersi AYNEN)."""
    base_fill = g["next_open"] * (1.0 + s)
    risk_dollars = (g["size_r"] * max(0.0, g["size_mult"])) * risk_pct * g["equity"]
    per_share = base_fill - g["stop"]
    if per_share <= 0:
        return float("nan"), 0
    qty = int(math.floor(risk_dollars / per_share))
    adv = g["adv"]
    if adv and adv > 0:
        cap = int(adv_cap * adv)
        if qty > cap:
            qty = cap
        participation = qty / adv
        fill = base_fill * (1.0 + cf * participation)
    else:
        fill = base_fill
    return fill, qty


def oz_sinama(kayit: dict, dunya: str, medyan_atrpct: float | None) -> dict:
    from meridian import broker as B
    cf = float(B.IMPACT_COEF)
    adv_cap = float(B.ADV_CAP_PCT)
    risk_pct = float(B.RISK_PCT_PER_R)
    s_taban = TABAN_BPS / 10000.0

    girisler = kayit["giris"]
    cikislar = kayit["cikis"]

    # çıkışın beklenen s_i'si: ticker bazında i. çıkış ↔ i. giriş (pozisyon tekil — FIFO)
    g_sira: dict[str, list] = {}
    for g in girisler:
        g_sira.setdefault(g["ticker"], []).append(g)
    c_sayac: dict[str, int] = {}

    def g_satir(g):
        s_bek, _, _ = _beklenen_slip(g["atr"], g["entry_trigger"], dunya, medyan_atrpct)
        fill = g["fill_yuvarlanmamis"]
        recon, q_recon = _fill_rekonstruksiyon(g, s_bek, cf, risk_pct, adv_cap)
        rel = abs(fill / recon - 1.0) if recon == recon else None
        recon_taban, _ = _fill_rekonstruksiyon(g, s_taban, cf, risk_pct, adv_cap)
        ham = fill / g["next_open"] - 1.0
        return {"ticker": g["ticker"], "ts": g["ts"],
                "beklenen_slip_bps": round(s_bek * 1e4, 6),
                "G1_broker_slip_esit": g["broker_slip"] == s_bek,
                "G2_recon_rel_fark": rel,
                "G2_gecti": (rel is not None and rel <= 1e-9),
                "recon_bayt_esit": recon == fill,
                "ayirt_edicilik_taban_rel_fark": (abs(fill / recon_taban - 1.0)
                                                  if recon_taban == recon_taban else None),
                "qty_recon": q_recon, "qty_nihai": g["qty"],
                "nominal_kirpildi": q_recon != g["qty"],
                "ham_bps": round(ham * 1e4, 6),
                "likidite_terimi_bps": round((ham - s_bek) * 1e4, 6)}   # ayrıştırılmış (gizlenmez)

    def c_satir(c):
        t = c["ticker"]
        i = c_sayac.get(t, 0)
        c_sayac[t] = i + 1
        g = (g_sira.get(t) or [None] * (i + 1))[i] if i < len(g_sira.get(t, [])) else None
        if g is None:
            return {"ticker": t, "ts": c["ts"], "reason": c["reason"],
                    "eslesme": None, "C1_defter_exit_esit": False, "C2_gecti": False,
                    "olculemedi_nedeni": "çıkışa eşlenecek giriş kaydı yok — eşleme bozuk"}
        s_bek, _, _ = _beklenen_slip(g["atr"], g["entry_trigger"], dunya, medyan_atrpct)
        beklenen = c["raw_exit"] * (1.0 - s_bek)
        bek_defter = defter_yuvarla(beklenen, c["reason"])
        c2 = (1.0 - beklenen / c["raw_exit"]) - s_bek
        return {"ticker": t, "ts": c["ts"], "reason": c["reason"],
                "beklenen_slip_bps": round(s_bek * 1e4, 6),
                "C1_defter_exit_esit": bek_defter == c["defter_exit"],
                "C1_mutlak_fark": abs(bek_defter - c["defter_exit"]),
                "C2_fark": c2, "C2_gecti": abs(c2) <= 1e-9,
                "G1c_broker_slip_esit": c["broker_slip"] == s_bek,
                "raw_exit": c["raw_exit"], "defter_exit": c["defter_exit"]}

    tum_g = [g_satir(g) for g in girisler]
    tum_c = [c_satir(c) for c in cikislar]
    g_bozuk = [d for d in tum_g if not (d["G1_broker_slip_esit"] and d["G2_gecti"])]
    c_bozuk = [d for d in tum_c if not (d.get("C1_defter_exit_esit") and d.get("C2_gecti")
                                        and d.get("G1c_broker_slip_esit"))]
    gecti = (len(tum_g) > 0 and len(tum_c) > 0 and not g_bozuk and not c_bozuk)
    slipler = sorted(d["beklenen_slip_bps"] for d in tum_g)
    return {
        "dunya": dunya, "medyan_atrpct": medyan_atrpct,
        "impact_coef_koddan": cf, "adv_cap_koddan": adv_cap, "risk_pct_koddan": risk_pct,
        "n_giris": len(tum_g), "n_cikis": len(tum_c),
        "slip_bps_dagilimi": ({"min": slipler[0], "medyan": statistics.median(slipler),
                               "max": slipler[-1]} if slipler else None),
        "G2_max_rel_fark": max((d["G2_recon_rel_fark"] for d in tum_g
                                if d["G2_recon_rel_fark"] is not None), default=None),
        "recon_bayt_esit_n": sum(1 for d in tum_g if d["recon_bayt_esit"]),
        "nominal_kirpilan_n": sum(1 for d in tum_g if d["nominal_kirpildi"]),
        "C1_gecen_n": sum(1 for d in tum_c if d.get("C1_defter_exit_esit")),
        "atr_olculemeyen_giris_deneme_n": kayit["atr_olculemeyen_giris_deneme_n"],
        "atr_olculemeyen_dolan_n": sum(1 for g in girisler if g["atr_olculemedi"]),
        "scale_out_n": kayit["scale_out_n"],
        "ilk20_giris": tum_g[:20], "ilk20_cikis": tum_c[:20],
        "tum_bozuk_giris": g_bozuk[:50], "tum_bozuk_giris_n": len(g_bozuk),
        "tum_bozuk_cikis": c_bozuk[:50], "tum_bozuk_cikis_n": len(c_bozuk),
        "kill2_gecti": gecti,
        "beyan": ("G2 = motor dolum aritmetiğinin satır-başına beklenen slip'le BİREBİR "
                  "rekonstrüksiyonu (likidite payı ayrıştırılmış, edg040 dersi); Ç1 defterin "
                  "kendisine çivili — yuvarlama edg045 defter_yuvarla KARMA modeli (np/Python, "
                  "reason yoluna göre). Kill#2 TÜM satırlara uygulanır (kart: satır başına)."),
    }


# ---------------------------------------------------------------------------------------------
# ŞASİ KAPISI (kill#1) + Δ/CI + seçilim farkı
# ---------------------------------------------------------------------------------------------
def sasi_kapisi(smoke: bool) -> dict:
    ek = "_smoke" if smoke else ""
    yerel_dir = (BURASI / "smoke") if smoke else BURASI
    ref_dir = EDG032C / ("kosum1_smoke" if smoke else "kosum1")
    ciftler = {
        "islemler_tam": (yerel_dir / f"islemler_tam_sabit_mevcut{ek}.json",
                         ref_dir / f"islemler_tam_kontrol{ek}.json"),
        "islemler_slim": (yerel_dir / f"islemler_sabit_mevcut{ek}.json",
                          ref_dir / f"islemler_kontrol{ek}.json"),
        "seanslar": (yerel_dir / f"seanslar_sabit_mevcut{ek}.json",
                     ref_dir / f"seanslar_kontrol{ek}.json"),
    }
    sonuc = {}
    for ad, (y, r) in ciftler.items():
        sy, sr = _sha_full(y), _sha_full(r)
        sonuc[ad] = {"yerel_sha256": sy, "edg032c_sha256": sr,
                     "bayt_ozdes": (sy is not None and sy == sr),
                     "olculemedi_nedeni": (None if (sy and sr) else
                                           f"dosya okunamadı: yerel={bool(sy)} ref={bool(sr)}")}
    # tam koşumda künye çivisi: kıyasladığımız referans dosyalar TABAN_KUNYESI kaydının kendisi mi
    kunye_tutarli = None
    if not smoke:
        kunye = json.loads((EDG032C / "TABAN_KUNYESI.json").read_text())
        ks = kunye["determinizm_kaniti"]["kapi_sha256"]
        kunye_tutarli = (sonuc["islemler_tam"]["edg032c_sha256"] == ks["islemler_tam_kontrol.json"]
                         and sonuc["islemler_slim"]["edg032c_sha256"] == ks["islemler_kontrol.json"]
                         and sonuc["seanslar"]["edg032c_sha256"] == ks["seanslar_kontrol.json"])
    gecti = all(v["bayt_ozdes"] for v in sonuc.values()) and (kunye_tutarli is not False)
    out = {"bayt_kiyas_edg032c": sonuc, "kunye_sha_tutarli": kunye_tutarli,
           "kill1_gecti": gecti}
    (yerel_dir / f"sasi_kapisi{ek}.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"  ŞASİ KAPISI{ek}: bayt={all(v['bayt_ozdes'] for v in sonuc.values())} "
          f"künye_tutarlı={kunye_tutarli} → {'GEÇTİ' if gecti else 'DÜŞTÜ — ölçüm DURUR'}")
    return out


def delta_pnl_ci(taban_defter: list, hucre_defter: list, aylar: list[str]) -> dict:
    """EŞLENİK ay-kümeli bootstrap (edg040/edg035 AYNEN): birim = AY, iki kol AYNI ayı görür,
    B=5000, seed=20260812, yüzdelik CI."""
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


def defter_secilim_farki(a_defter: list, b_defter: list) -> dict:
    """Defter-düzeyi seçilim farkı: (ticker, ts_open) kümeleri (mekanik sayım, hüküm yok)."""
    ka = {(t["ticker"], str(t["ts_open"])) for t in a_defter}
    kb = {(t["ticker"], str(t["ts_open"])) for t in b_defter}
    return {"n_a": len(a_defter), "n_b": len(b_defter),
            "ortak_n": len(ka & kb), "yalniz_a_n": len(ka - kb), "yalniz_b_n": len(kb - ka),
            "yalniz_a_ornek": sorted(ka - kb)[:15], "yalniz_b_ornek": sorted(kb - ka)[:15]}


# ---------------------------------------------------------------------------------------------
# HÜCRE KOŞUMU
# ---------------------------------------------------------------------------------------------
def hucre_kos(ref, run: str, smoke: bool, medyan_atrpct: float | None,
              lambda_kod) -> dict:
    dunya, secilim = HUCRELER[run]
    if dunya == "atr":
        assert medyan_atrpct is not None and medyan_atrpct > 0, \
            "ATR dünyası medyan çapası olmadan koşulamaz — sıra bozuk, DUR"
    ref.HUCRELER.setdefault(run, {})                 # merkez hücre (parametre enjeksiyonu YOK)
    kayit = yeni_kayit()
    ceza_durumu = yeni_ceza_durumu(lambda_kod) if secilim == "cezali" else None
    m_once = motor_sha()

    with contextlib.ExitStack() as yigin:
        yigin.enter_context(dunya_kancalari(kayit, dunya, medyan_atrpct))
        if ceza_durumu is not None:
            yigin.enter_context(ceza_sarmala(ceza_durumu))
        ref.kosum(run, smoke=smoke)                  # ŞASİ: referansın kendi yolu, dokunulmadan

    m_sonra = motor_sha()
    ek = "_smoke" if smoke else ""
    outdir = (BURASI / "smoke") if smoke else BURASI
    d = json.loads((outdir / f"sonuc_{run}{ek}.json").read_text())
    defter = json.loads((outdir / f"islemler_tam_{run}{ek}.json").read_text())

    oz = oz_sinama(kayit, dunya, medyan_atrpct)
    (outdir / f"oz_sinama_{run}{ek}.json").write_text(
        json.dumps(oz, ensure_ascii=False, indent=1), encoding="utf-8")
    (outdir / f"yakalama_{run}{ek}.json").write_text(
        json.dumps({k: v for k, v in kayit.items() if k != "acik_slip"},
                   ensure_ascii=False), encoding="utf-8")

    # seçilim farkı (sort-düzeyi) — yalnız cezalı hücrelerde ölçülebilir
    sort_farki = None
    if ceza_durumu is not None:
        turlar = ceza_durumu["tur_kayitlari"]
        sort_farki = {
            "tur_n": len(turlar),
            "sira_degisen_tur_n": sum(1 for t in turlar if t["sira_degisti"]),
            "kayan_aday_toplam": sum(t["kayan_aday_n"] for t in turlar),
            "aday_toplam": sum(t["aday_n"] for t in turlar),
            "sort_okuma_n": ceza_durumu["sort_okuma_n"],
            "ham_okuma_n": ceza_durumu["ham_okuma_n"],
            "atr_olculemeyen_aday_n": ceza_durumu["atr_olculemeyen_aday_n"],
            "sd_sifir_tur_n": ceza_durumu["sd_sifir_tur_n"],
            "gun_sonu_sortsuz_n": ceza_durumu["gun_sonu_sortsuz_n"],
        }
        (outdir / f"secilim_sort_{run}{ek}.json").write_text(
            json.dumps({"ozet": sort_farki, "turlar": turlar},
                       ensure_ascii=False, indent=1), encoding="utf-8")

    perf = d.get("performans") or {}
    islem = d.get("islem") or {}
    poz = sum(float(t["pnl_dollars"]) for t in defter if float(t["pnl_dollars"]) > 0)
    neg = sum(float(t["pnl_dollars"]) for t in defter if float(t["pnl_dollars"]) < 0)
    pf = round(poz / abs(neg), 4) if neg < 0 else None
    pf_neden = None if neg < 0 else "kayıp bacağı boş (Σpnl<0 yok) — PF paydası sıfır, TANIMSIZ"
    score_hep_int = all(isinstance(t.get("score"), int) for t in defter) if defter else None

    ozet = {
        "kosum": run, "smoke": smoke,
        "kol_kimligi": {                              # kol kimliği damgası (exe006 Kritik-1 emsali)
            "dunya": dunya, "secilim": secilim,
            "lambda_ceza": (LAMBDA_CEZA if secilim == "cezali" else None),
            "medyan_atrpct": (medyan_atrpct if dunya == "atr" else None),
            "goal_slippage_bps_kaydi": ((d.get("replay") or {}).get("cost_model") or {}).get("slippage_bps"),
            "goal_kaydi_notu": ("goal.slippage_bps 5'te SABİT kalır (dosyaya/sözlüğe dokunulmadı); "
                                "atr dünyasında gerçek slip işlem-başına broker sarmalayıcısından — "
                                "kanıt öz-sınama G1/G2" if dunya == "atr" else
                                "sabit dünya: broker slip'ine hiç dokunulmadı"),
            "uygulanan_slip_bps": (oz.get("slip_bps_dagilimi")),
            "defter_score_hep_int": score_hep_int,    # ceza deftere sızmadı kanıtı
        },
        "hucre_sasi": d.get("hucre"),
        "islem_n": islem.get("n"),
        "net_pnl_trades": perf.get("net_pnl_trades"),   # KANONİK (islem.net_pnl YOK — bilinen tuzak)
        "net_pnl_equity": perf.get("net_pnl_equity"),
        "pf": pf, "pf_olculemedi_nedeni": pf_neden,
        "maxdd_kanonik": perf.get("maxdd_kanonik"), "maxdd_m2m": perf.get("maxdd_m2m"),
        "sharpe": perf.get("sharpe"), "avg_r": perf.get("avg_r"),
        "win_rate": perf.get("win_rate"), "total_return": perf.get("total_return"),
        "setup_bazinda": islem.get("setup_bazinda"),
        "exit_reason_dagilim": islem.get("exit_reason_dagilim"),
        "verdict_dagilim": islem.get("verdict_dagilim"),
        "toplam_plan": islem.get("toplam_plan"), "silahlanan_plan": islem.get("silahlanan_plan"),
        "entry_rejects": islem.get("entry_rejects"),
        "secilim_farki_sort": sort_farki,
        "butunluk_gecerli": (d.get("butunluk") or {}).get("gecerli"),
        "sasi_kill3_temiz": (d.get("kill3_mtime") or {}).get("temiz"),
        "oz_sinama_kill2_gecti": oz["kill2_gecti"],
        "motor_sha_once": m_once, "motor_sha_sonra": m_sonra,
        "motor_sha_ayni": m_once == m_sonra,
    }
    (outdir / f"hucre_{run}{ek}.json").write_text(
        json.dumps(ozet, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"  [{run}{ek}] dünya={dunya} seçilim={secilim} n={ozet['islem_n']} "
          f"net={ozet['net_pnl_trades']} pf={pf} dd={ozet['maxdd_kanonik']} "
          f"kill2={oz['kill2_gecti']} bütünlük={ozet['butunluk_gecerli']} "
          f"motor_sha_ayni={ozet['motor_sha_ayni']}")
    return ozet


def medyan_hesapla(smoke: bool) -> float | None:
    """MEDYAN-ATR% çapası: sabit_mevcut hücresinde DOLAN girişlerin ATR%'sinden (beyanlı;
    ölçülemeyenler dışarıda). Değer künyelenir; atr hücrelerine SABİT geçirilir."""
    ek = "_smoke" if smoke else ""
    outdir = (BURASI / "smoke") if smoke else BURASI
    yak = json.loads((outdir / f"yakalama_sabit_mevcut{ek}.json").read_text())
    atrpcts = [g["atrpct"] for g in yak["giris"] if g["atrpct"] is not None]
    olculemeyen = sum(1 for g in yak["giris"] if g["atrpct"] is None)
    if not atrpcts:
        (outdir / f"medyan_atrpct{ek}.json").write_text(json.dumps(
            {"medyan_atrpct": None,
             "olculemedi_nedeni": "sabit_mevcut girişlerinde ölçülebilir ATR% yok"},
            ensure_ascii=False, indent=1), encoding="utf-8")
        return None
    med = float(statistics.median(atrpcts))
    out = {"medyan_atrpct": med, "n_olculen": len(atrpcts), "n_olculemeyen": olculemeyen,
           "min": min(atrpcts), "max": max(atrpcts),
           "tanim": ("sabit_mevcut hücresinde DOLAN girişlerin ATR% (fill'e giden armed_atr / "
                     "plan entry_trigger) medyanı — statistics.median; ölçülemeyen (atr None) "
                     "girişler kümeye girmez. Dört hücrede AYNI DONMUŞ skaler.")}
    (outdir / f"medyan_atrpct{ek}.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"  medyan-ATR%{ek}: {med:.6f} (n={len(atrpcts)}, ölçülemeyen={olculemeyen})")
    return med


# ---------------------------------------------------------------------------------------------
def main() -> int:
    smoke = "--smoke" in sys.argv
    ek = "_smoke" if smoke else ""
    outdir = (BURASI / "smoke") if smoke else BURASI
    motor_once = motor_sha()
    ref, uyarlama = referans_modul()
    lambda_kod, sort_satir = sort_lambda_bul()
    on = ceza_on_sinama(lambda_kod)
    print(f"referans şasi yüklendi · SANDBOX={ref.SANDBOX} · sort-lambda satır={sort_satir} · "
          f"ceza ön-sınaması geçti={on['gecti']}")

    rapor: dict = {
        "kart": "EDG-2026-046", "smoke": smoke,
        "olcum_zamani": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "motor_sha256_once": motor_once,
        "uyarlama_beyani": {**uyarlama,
                            "beyan": ("edg032c TEK uyarlaması AYNEN: yüklenen şasi modülünün "
                                      "ARMED_BEKLENEN sabiti B1 yasasına çevrildi (dünya-"
                                      "beklentisi; motor DEĞİL). Parametre enjeksiyonu YOK.")},
        "enjeksiyon_noktalari": {
            "aday_siralama": f"meridian/backtest.py:{sort_satir} `{SORT_SATIR_BEKLENEN}`",
            "slip_satirlari": "broker.py:611 (giriş) · :734 (kısmi satış) · :765 (çıkış) — "
                              "self.slip (broker.py:476); sarmalayıcı süreç-içi",
            "atr_kaynagi": "backtest.py:543-544 armed_atr[sig.ticker] (silahlanma-anı ATR; "
                           "ölçülemedi→None) → fill_entry atr kw (backtest.py:337)",
        },
        "ceza_on_sinamasi": on,
        "lambda_ceza": LAMBDA_CEZA, "taban_bps": TABAN_BPS,
    }

    def yaz_ve_cik(kod: int) -> int:
        rapor["motor_sha256_sonra"] = motor_sha()
        rapor["motor_sha_ayni_toplam"] = (motor_once == rapor["motor_sha256_sonra"])
        (BURASI / f"sonuc_grid{ek}.json").write_text(
            json.dumps(rapor, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"yazıldı: {BURASI / f'sonuc_grid{ek}.json'}")
        return kod

    hucreler: dict = {}

    # [A] sabit_mevcut → ŞASİ KAPISI (kill#1)
    hucreler["sabit_mevcut"] = hucre_kos(ref, "sabit_mevcut", smoke, None, lambda_kod)
    sk = sasi_kapisi(smoke)
    rapor["sasi_kapisi"] = sk
    rapor["hucreler"] = hucreler
    if not sk["kill1_gecti"]:
        rapor["DURDU"] = "kill#1: sabit_mevcut edg032c/kosum1 ile bayt-özdeş DEĞİL — hücre koşulmadı"
        print("KILL#1 DÜŞTÜ — ölçüm DURDU; şasi teşhisi Rol-1'e")
        return yaz_ve_cik(2)
    if not hucreler["sabit_mevcut"]["oz_sinama_kill2_gecti"]:
        rapor["DURDU"] = "kill#2: sabit_mevcut öz-sınaması düştü — kablo tutmuyor"
        print("KILL#2 DÜŞTÜ (sabit_mevcut) — ölçüm DURDU")
        return yaz_ve_cik(2)
    if not hucreler["sabit_mevcut"]["motor_sha_ayni"]:
        rapor["DURDU"] = "motor sha sabit_mevcut koşumu içinde değişti — hücre geçersiz"
        print("MOTOR SHA DEĞİŞTİ (sabit_mevcut) — ölçüm DURDU")
        return yaz_ve_cik(2)

    # [B] medyan-ATR% çapası (sabit_mevcut dolumlarından — atr hücrelerinden ÖNCE donar)
    medyan = medyan_hesapla(smoke)
    rapor["medyan_atrpct"] = medyan
    if medyan is None:
        rapor["DURDU"] = "medyan-ATR% ölçülemedi — ATR dünyası kurulamaz"
        return yaz_ve_cik(2)

    # [C] kalan hücreler (dumanda da dört tel: sabit_cezali+atr_mevcut atlanır, atr_cezali koşulur)
    kalan = ["atr_cezali"] if smoke else ["sabit_cezali", "atr_mevcut", "atr_cezali"]
    for run in kalan:
        h = hucre_kos(ref, run, smoke, medyan, lambda_kod)
        hucreler[run] = h
        if not h["oz_sinama_kill2_gecti"]:
            rapor["DURDU"] = f"kill#2: {run} öz-sınaması düştü — sonraki hücre koşulmadı"
            print(f"KILL#2 DÜŞTÜ ({run}) — ölçüm DURDU")
            return yaz_ve_cik(2)
        if not h["motor_sha_ayni"]:
            rapor["DURDU"] = f"motor sha {run} koşumu içinde değişti — hücre geçersiz"
            print(f"MOTOR SHA DEĞİŞTİ ({run}) — ölçüm DURDU")
            return yaz_ve_cik(2)

    # [D] Δ+CI (kart kuralı: cezalı ↔ AYNI dünyanın mevcut hücresi) + dünya etkisi (betimleyici)
    if not smoke:
        seanslar = json.loads((outdir / "seanslar_sabit_mevcut.json").read_text())
        aylar = sorted({str(r["date"])[:7] for r in seanslar})
        defterler = {run: json.loads((outdir / f"islemler_tam_{run}.json").read_text())
                     for run in HUCRELER}
        rapor["delta_ci"] = {
            "sabit_cezali_vs_sabit_mevcut": delta_pnl_ci(
                defterler["sabit_mevcut"], defterler["sabit_cezali"], aylar),
            "atr_cezali_vs_atr_mevcut": delta_pnl_ci(
                defterler["atr_mevcut"], defterler["atr_cezali"], aylar),
            "dunya_etkisi_atr_mevcut_vs_sabit_mevcut_BETIMLEYICI": delta_pnl_ci(
                defterler["sabit_mevcut"], defterler["atr_mevcut"], aylar),
        }
        rapor["secilim_farki_defter"] = {
            "sabit_cezali_vs_sabit_mevcut": defter_secilim_farki(
                defterler["sabit_mevcut"], defterler["sabit_cezali"]),
            "atr_cezali_vs_atr_mevcut": defter_secilim_farki(
                defterler["atr_mevcut"], defterler["atr_cezali"]),
            "not": "a = mevcut hücre, b = cezalı hücre; anahtar (ticker, ts_open)",
        }
        for ad, dd in rapor["delta_ci"].items():
            print(f"  Δ[{ad}]: {dd['delta_pnl']} CI95={dd['ci95']} ({dd['sifir_disinda']})")
    else:
        rapor["delta_ci"] = {"degerlendirilmedi": "duman — kablo sınaması; Δ/CI yalnız TAM koşumda"}

    rapor["hukum_yok"] = ("Bu rapor HÜKÜM İÇERMEZ. İKİ-DÜNYA karar kuralının okunması Rol-1'in; "
                          "'aday/değil' yorumu bu betikte yasak.")
    return yaz_ve_cik(0)


if __name__ == "__main__":
    raise SystemExit(main())
