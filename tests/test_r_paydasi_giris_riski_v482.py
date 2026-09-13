"""TSK-187 — canlı/replay `r_multiple` PAYDASI: hisse-başı GİRİŞ RİSKİ (`qty_taban × r_per_share`).

NE ÇİVİLER. `broker.Position.qty_taban` alanını, `fill_entry`in ADV/nominal daraltmalarından
SONRAKİ adedi tabana yazmasını, eski kayıtların yüklemede göçmesini (`qty_taban` yoksa `qty`),
`close_position` paydasının bütçe dolarından (`risk_dollars`) giriş riskine geçmesini, işlem
satırının `r_payda`/`r_payda_usd` damgasını, ölçek-çıkışının tabanı DEĞİŞTİRMEMESİNİ,
`loop._adet_benimse`nin tabanı da benimsemesini ve gölge ↔ canlı R PARİTESİNİ.

KARARIN KAYNAĞI. Kart `research/cards/EDG-2026-091-canli-r-paydasi-kaynagi.yaml`
(`hukum_2026_09_13`, `karar_operatore` (b) — operatör kararı 2026-09-13). Geriye dönük yeniden
hesap YOKTUR: eski satırlar damgasızdır ve damgasızlık "payda = bütçe dolarları" demektir.

NEDEN PAYDA DEĞİŞTİ (tek cümle). Kitap girişte donan BÜTÇEYE (`size_r · %1 · özsermaye`) bölüyor,
gölge motor hisse-başı riske bölüyordu; `loop._adet_benimse` aynanın adedini benimsediğinde
(kitap 17 → ayna 38) bütçe payda AYNI kalıp pay ikiye katlanıyor ve aynı fiyat yolu iki motorda
iki farklı R yazıyordu. Yeni payda adetle birlikte hareket eder.

YASA 6 — OKUYUCU BEYANI DEĞİL, ÖLÇÜMDÜR (tur-2 düzeltmesi). Tur 1'de bu blok iki okuyucu BEYAN
ediyordu ve birincisi KODDA YOKTU: `r_payda` dizgesi `edg088_golge_pilot/` altındaki hiçbir
dosyada geçmiyordu (inceleme bulgusu, BLOKLAYICI). Beyan artık gerçeğe çekildi ve çiviyle bağlandı
(`test_t4_*`):
  (a) OKUYUCU — `research/olcumler/edg088_golge_pilot/sayim.py::kontrol_olc` (EDG-088 PK (2)):
      gerçek satırın `r_payda` damgasını (üst düzey ya da `extra_json` zarfı) okur; YALNIZ
      `broker.R_PAYDA_GIRIS` damgalı satır gölge R'siyle kıyaslanır, damgasız (eski bütçe paydalı)
      ve yabancı damgalı satırlar `birim_eski_n` / `birim_eski_idler` / `birim_notu` altında AYRI
      raporlanır. Çivisi:
      `tests/test_edg088_sayim_v461.py::test_A5_DAMGASIZ_gercek_satir_KIYASA_girmez_ve_ADIYLA_sayilir`
      (ve aynı dosyadaki kardeş A5 çivileri: zarf okuması, bozuk zarf, tüm-çiftler-eski, tek-kaynak).
  (b) `r_payda_usd` satırın kendi paydasını TAŞIR — R geriye dönük yeniden hesap OLMADAN
      denetlenebilir (pay = R × payda). Bu bir ALAN sözleşmesidir; bugün otomatik bir karne
      okuyucusu YOKTUR ve olmadığı burada AÇIKÇA yazılıdır (beyan ≠ okuyucu).
Olay okuyucuları: `r_payda_gocu` ve `r_payda_gecersiz` `state/events.jsonl`a düşer — pano olay
çekmecesi + `obs.recent` mevcut okuyuculardır (yeni bir sink doğmaz).

SAYILAR EL HESABIDIR. Her beklenti aynı ilkel değerlerden (dolum, stop, adet, çıkış) test içinde
yeniden türetilir VE üç haneli literalle çivilenir; literal ile türetme ayrışırsa çivi öter.
"""
from __future__ import annotations

import pathlib

import pytest

from meridian import broker, store

KOK = pathlib.Path(__file__).resolve().parents[1]

# --- VRTX SENTETİK SAHNESİ (kartın ayrışma vakasının sayıları) ------------------------------------
VRTX_DOLUM = 559.37
VRTX_STOP = 530.34
VRTX_QTY = 17            # kitabın kendi boyutlaması (dolum − stop paydasıyla)
VRTX_AYNA = 38           # aynanın GERÇEKTEN var olan adedi — `_adet_benimse` bunu benimser
VRTX_CIKIS = 529.38
VRTX_RPS = VRTX_DOLUM - VRTX_STOP          # 29,03 $/hisse (kayan nokta: 29.029999999999973)


def _poz(qty: int, *, qty_taban: int | None = None, risk_dollars: float | None = None,
         ticker: str = "VRTX", entry: float = VRTX_DOLUM, stop: float = VRTX_STOP) -> broker.Position:
    """Sentetik açık pozisyon — motoru boyutlamadan geçirmeden, alanları AÇIKÇA kurar."""
    rps = entry - stop
    return broker.Position(
        plan_id="P-TSK187", ticker=ticker, side="long", entry=entry, stop=stop,
        trail_stop=stop, target=entry + 3 * rps, qty=qty,
        qty_taban=(qty if qty_taban is None else qty_taban),
        r_per_share=rps,
        risk_dollars=(qty * rps if risk_dollars is None else risk_dollars),
        size_r=1.0, ts_open="2026-09-01", hi_water=entry, lo_water=entry)


def _olaylar(ad: str) -> list[dict]:
    """`state/events.jsonl`daki verilen adlı olaylar (sandbox_state altında)."""
    return [e for e in store.read_jsonl("events.jsonl") if e.get("event") == ad]


# ==================================================================================================
# TASK 1 — `Position.qty_taban` + yükleme göçü
# ==================================================================================================
def test_t1_alan_var_ve_fill_entry_tabani_yazar():
    """`fill_entry` tabanı yazar ve taban = pozisyonun kendi adedi (daraltmalardan SONRA)."""
    b = broker.PaperBroker(equity=100_000, slippage_bps=0, commission_per_share=0.0)
    plan = {"id": "P1", "ticker": "X", "stop": 90.0, "profit_target": 130.0, "size_r": 1.0}
    pos = b.fill_entry(plan, next_open=100.0, ts="d1", equity=100_000)
    assert pos is not None
    assert pos.qty == 100 and pos.qty_taban == 100          # 1.000$ bütçe / 10$ hisse-başı risk


def test_t1_taban_ADV_DARALTMASINDAN_SONRAKI_adet():
    """Taban, likidite tavanı adedi KISTIKTAN sonraki adettir — bütçe adedi değil.

    ADV 2.000 hisse → tavan %2 = 40 hisse; bütçe 100 hisse isterdi. Taban 40 olmalı, yoksa
    payda hiç var olmamış 60 hisseyi de riskli sayar."""
    b = broker.PaperBroker(equity=100_000, slippage_bps=0, commission_per_share=0.0)
    plan = {"id": "P1", "ticker": "X", "stop": 90.0, "profit_target": 130.0, "size_r": 1.0}
    pos = b.fill_entry(plan, next_open=100.0, ts="d1", equity=100_000, adv=2_000)
    assert pos is not None and pos.qty == 40
    assert pos.qty_taban == 40


def test_t1_eski_kayit_gocer_ve_olay_yazilir(sandbox_state, monkeypatch):
    """Eski `portfolio.json` kaydında `qty_taban` YOKTUR → yüklemede `qty`ye eşitlenir ve olay düşer.

    Göç SESSİZ OLAMAZ: taban sessizce 0 kalsaydı payda 0 olur ve o pozisyonun kapanış R'si
    uydurma bir 0,0 olarak deftere yazılırdı."""
    monkeypatch.setattr(broker, "_GOC_LOGLANDI", set())
    eski = {"plan_id": "P1", "ticker": "VRTX", "side": "long", "entry": VRTX_DOLUM,
            "stop": VRTX_STOP, "trail_stop": VRTX_STOP, "target": 600.0, "qty": VRTX_AYNA,
            "r_per_share": VRTX_RPS, "risk_dollars": 493.51, "size_r": 1.0,
            "ts_open": "2026-09-01"}
    gocmus = broker.qty_taban_goc(eski, kaynak="civi")
    assert gocmus["qty_taban"] == VRTX_AYNA
    assert "qty_taban" not in eski, "göç çağıranın sözlüğünü YERİNDE değiştirmemeli"
    ev = _olaylar("r_payda_gocu")
    assert len(ev) == 1 and ev[0]["kaynak"] == "civi" and ev[0]["ticker"] == "VRTX"
    # SÜREÇ BAŞINA BİR KEZ: ikinci kayıt olay ÜRETMEZ (defter satır seliyle şişmez)
    broker.qty_taban_goc({**eski, "ticker": "AAA"}, kaynak="civi")
    assert len(_olaylar("r_payda_gocu")) == 1


def test_t1_yeni_kayitta_goc_TABANI_EZMEZ(sandbox_state, monkeypatch):
    """`qty_taban` ZATEN varsa göç dokunmaz — benimsenmiş taban `qty`ye geri çekilemez."""
    monkeypatch.setattr(broker, "_GOC_LOGLANDI", set())
    yeni = {"ticker": "VRTX", "qty": 38, "qty_taban": 17}
    assert broker.qty_taban_goc(yeni, kaynak="civi")["qty_taban"] == 17
    assert _olaylar("r_payda_gocu") == []


def test_t1_loop_yuklemesi_gocu_UYGULAR(sandbox_state, monkeypatch):
    """DAVRANIŞ ÇİVİSİ: `loop._load_broker` eski defteri yükleyince taban dolu gelir."""
    from meridian import loop
    monkeypatch.setattr(broker, "_GOC_LOGLANDI", set())
    store.write_json("portfolio.json", {
        "cash": 100_000.0, "realized_pnl": 0.0, "last_id": 0,
        "positions": {"VRTX": {"plan_id": "P1", "ticker": "VRTX", "side": "long",
                               "entry": VRTX_DOLUM, "stop": VRTX_STOP, "trail_stop": VRTX_STOP,
                               "target": 600.0, "qty": VRTX_AYNA, "r_per_share": VRTX_RPS,
                               "risk_dollars": 493.51, "size_r": 1.0, "ts_open": "2026-09-01"}}})
    b, _meta = loop._load_broker()
    assert b.positions["VRTX"].qty_taban == VRTX_AYNA
    assert len(_olaylar("r_payda_gocu")) == 1


def test_t1_golge_defteri_yuklemesi_de_gocer(sandbox_state, monkeypatch):
    """Aynı göç varyant kitaplarında (`shadow_lifecycle`) ve gölge kopyasında (`intraday_shadow`)
    da koşar — üç yükleme yolu TEK göç yüklemini paylaşır (tek-kaynak yasası)."""
    monkeypatch.setattr(broker, "_GOC_LOGLANDI", set())
    from meridian import shadow_lifecycle
    bk = {"realized_pnl": 0.0, "trade_seq": 0, "start_equity": 100_000.0,
          "positions": {"VRTX": {"plan_id": "P1", "ticker": "VRTX", "side": "long",
                                 "entry": VRTX_DOLUM, "stop": VRTX_STOP, "trail_stop": VRTX_STOP,
                                 "target": 600.0, "qty": VRTX_AYNA, "r_per_share": VRTX_RPS,
                                 "risk_dollars": 493.51, "size_r": 1.0, "ts_open": "2026-09-01"}}}
    b = shadow_lifecycle._to_broker(bk, {"slippage_bps": 0, "commission_per_share": 0.0})
    assert b.positions["VRTX"].qty_taban == VRTX_AYNA
    kaynak = (KOK / "meridian" / "intraday_shadow.py").read_text(encoding="utf-8")
    assert "qty_taban_goc" in kaynak, "intraday_shadow kopyası göçü atlarsa tabanı 0 kalır"


# ==================================================================================================
# TASK 2 — `close_position` paydası + damga
# ==================================================================================================
def test_t2_VRTX_benimseme_sonrasi_R_HISSE_BASI_RISKE_bolunur(sandbox_state):
    """EL HESABI — kartın ayrışma vakası (kitap 17 / ayna 38).

      hisse-başı risk = 559,37 − 530,34            = 29,03 $
      payda (YENİ)    = 38 × 29,03                 = 1.103,14 $
      pay             = 38 × (529,38 − 559,37)     = −1.139,62 $
      R (YENİ)        = −1.139,62 / 1.103,14       = −1,033
      R (ESKİ, bütçe) = −1.139,62 / (17 × 29,03)   = −2,309      → |fark| ≈ 38/17 = 2,235×

    Sürtünme SIFIRDIR (slip 0 / komisyon 0) ki sayı payda değişikliğinin KENDİSİNİ ölçsün."""
    b = broker.PaperBroker(equity=100_000, slippage_bps=0, commission_per_share=0.0)
    pos = _poz(VRTX_QTY)                                   # taban = 17, bütçe payda = 17 × 29,03
    butce_payda = pos.risk_dollars
    pos.qty = VRTX_AYNA                                    # ayna adedi benimsendi…
    pos.qty_taban = VRTX_AYNA                              # …taban da onunla hareket eder
    b.positions["VRTX"] = pos
    row = b.close_position("VRTX", raw_exit=VRTX_CIKIS, reason="stop", ts="2026-09-10")

    pay = VRTX_AYNA * (VRTX_CIKIS - VRTX_DOLUM)
    assert row["pnl_dollars"] == pytest.approx(pay, abs=0.01)
    assert row["r_multiple"] == pytest.approx(pay / (VRTX_AYNA * VRTX_RPS), abs=1e-3)
    assert row["r_multiple"] == -1.033                      # el hesabının literali
    eski = round(pay / butce_payda, 3)
    assert eski == -2.309 and abs(eski / row["r_multiple"]) == pytest.approx(
        VRTX_AYNA / VRTX_QTY, abs=0.01)                     # eski payda ~2,24× büyük R yazıyordu
    # DAMGA: satır kendi paydasını TAŞIR (geriye dönük yeniden hesap olmadan denetlenebilsin)
    assert row["r_payda"] == "giris_riski"
    assert row["r_payda_usd"] == pytest.approx(VRTX_AYNA * VRTX_RPS, abs=0.01)
    assert row["r_payda_usd"] == pytest.approx(1103.14, abs=0.01)


def test_t2_damga_extra_jsona_duser_ve_geri_okunur(sandbox_state):
    """Damga tipli KOLON değildir → `extra_json`a düşer ve okumada geri gelir (Yasa 6 okuyucusu)."""
    from meridian import storage
    kolonlar = {ad for ad, _tip in storage._COLS[storage.TRADES]}
    assert "r_payda" not in kolonlar and "r_payda_usd" not in kolonlar
    b = broker.PaperBroker(equity=100_000, slippage_bps=0, commission_per_share=0.0)
    b.positions["VRTX"] = _poz(VRTX_QTY)
    row = b.close_position("VRTX", raw_exit=VRTX_CIKIS, reason="stop", ts="2026-09-10")
    store.append_jsonl("trades.jsonl", row)
    geri = store.read_jsonl("trades.jsonl")[-1]
    assert geri["r_payda"] == "giris_riski"
    assert geri["r_payda_usd"] == pytest.approx(VRTX_QTY * VRTX_RPS, abs=0.01)


def test_t2_olcek_cikisi_TABANI_DEGISTIRMEZ(sandbox_state):
    """Bankalanan bacak + kalan bacak ORİJİNAL adedin ölçeğinde tek satırdır.

      giriş 100 / stop 90 → hisse-başı risk 10 $, adet 100, taban 100 (payda 1.000 $)
      bankalama 120'de 50 hisse → 50 × 20 = 1.000 $   ·   kalan 50 hisse 130'da → 50 × 30 = 1.500 $
      R = (1.000 + 1.500) / (100 × 10) = 2,500        ← taban 50'ye düşseydi 5,000 yazardı"""
    b = broker.PaperBroker(equity=100_000, slippage_bps=0, commission_per_share=0.0)
    plan = {"id": "P1", "ticker": "X", "stop": 90.0, "profit_target": 130.0, "size_r": 1.0}
    pos = b.fill_entry(plan, next_open=100.0, ts="d1", equity=100_000)
    q0, taban0 = pos.qty, pos.qty_taban
    assert b.scale_out(pos, {"high": 120.0}, {"exit.scale_out_r": 2.0, "exit.scale_out_frac": 0.5})
    assert pos.qty == q0 - q0 // 2 and pos.qty_taban == taban0 == q0
    row = b.close_position("X", raw_exit=130.0, reason="target", ts="d2")
    banked, runner = (q0 // 2) * 20, (q0 - q0 // 2) * 30
    assert row["r_multiple"] == pytest.approx((banked + runner) / (q0 * 10.0), abs=1e-3)
    assert row["r_multiple"] == 2.5 and row["r_payda_usd"] == pytest.approx(1000.0, abs=0.01)


def test_t2_gecersiz_payda_ADIYLA_uyarir_SESSIZ_DEGIL(sandbox_state):
    """Payda ≤ 0 (göç görmemiş taban ya da bozuk stop) → R 0.0 ama SESSİZ DEĞİL (Yasa 4).

    UYDURMA YASAĞI KAYDI: 0.0 burada "ölçülemedi"nin yerine geçen bir sayı DEĞİLDİR — damga
    `olculemedi` olur ve `r_payda_usd` None kalır, yani okuyucu bu satırı R kıyasından ELER."""
    b = broker.PaperBroker(equity=100_000, slippage_bps=0, commission_per_share=0.0)
    b.positions["A"] = _poz(VRTX_QTY, qty_taban=0, ticker="A")   # göç görmemiş eski kayıt
    row = b.close_position("A", raw_exit=VRTX_CIKIS, reason="stop", ts="2026-09-10")
    assert row["r_multiple"] == 0.0
    assert row["r_payda"] == "olculemedi" and row["r_payda_usd"] is None
    ev = _olaylar("r_payda_gecersiz")
    assert len(ev) == 1 and ev[0]["ticker"] == "A" and ev[0]["qty_taban"] == 0
    # ikinci dal: hisse-başı risk ≤ 0 (stop girişin ÜSTÜNDE — bozuk kurulum)
    bozuk = _poz(10, ticker="B", entry=100.0, stop=100.0)
    b.positions["B"] = bozuk
    row2 = b.close_position("B", raw_exit=95.0, reason="stop", ts="2026-09-10")
    assert row2["r_multiple"] == 0.0 and row2["r_payda"] == "olculemedi"
    assert len(_olaylar("r_payda_gecersiz")) == 2


def test_t2_golge_ile_PARITE(sandbox_state):
    """Aynı dolum/stop/çıkış → gölge motorun R'si ile kitabın R'si AYNI (±0,001).

    Paritenin anlamı: iki motor artık AYNI BİRİMDE konuşuyor (hisse-başı risk). Sürtünmesiz
    kurulum: gölge motor komisyon/slipaj taşımaz, kitap taşıyabilir — kıyas ancak ikisi de
    sıfırken payda değişikliğinin KENDİSİNİ ölçer.

    BÜTÇE PAYDA BİLEREK AYRIK (`risk_dollars=1000`, gerçek bir 1R bütçesi): eski formül
    270/1.000 = 0,270 yazardı ve parite ANCAK yeni payda ile kurulur — çivi kendi hedefini ısırır."""
    import datetime as dt
    from meridian import golge_icra
    giris, stop, cikis, qty = 101.0, 95.0, 110.0, 30
    b = broker.PaperBroker(equity=100_000, slippage_bps=0, commission_per_share=0.0)
    b.positions["T"] = _poz(qty, ticker="T", entry=giris, stop=stop, risk_dollars=1000.0)
    kitap = b.close_position("T", raw_exit=cikis, reason="target", ts="2026-09-10")
    golge = golge_icra._kapanis_satiri(
        {"plan_id": "P1", "ticker": "T", "kurulum": "breakout_vcp", "hukum": "GO", "kol": "planli",
         "ts_plan": "2026-09-01", "giris_ts": "2026-09-02", "giris_fiyat": giris, "stop": stop,
         "hedef": 120.0, "strategy_version": 3, "r_per_share": giris - stop, "tuketilen": []},
        "2026-09-10", cikis, "target", dt.datetime(2026, 9, 10, tzinfo=dt.timezone.utc), "eod")
    assert golge["R"] == pytest.approx(1.5, abs=1e-9)              # (110 − 101) / 6
    assert kitap["r_multiple"] == pytest.approx(golge["R"], abs=0.001)


def test_t2_mfe_mae_DEGISMEDI(sandbox_state):
    """MFE/MAE HİSSE-BAŞI R'dir ve bu tur onlara DOKUNULMADI — adet ölçeği girmez."""
    b = broker.PaperBroker(equity=100_000, slippage_bps=0, commission_per_share=0.0)
    pos = _poz(VRTX_QTY)
    pos.hi_water, pos.lo_water = VRTX_DOLUM + 2 * VRTX_RPS, VRTX_DOLUM - 0.5 * VRTX_RPS
    b.positions["VRTX"] = pos
    pos.qty = pos.qty_taban = VRTX_AYNA                     # adet benimsendi — MFE/MAE ETKİLENMEZ
    row = b.close_position("VRTX", raw_exit=VRTX_CIKIS, reason="stop", ts="2026-09-10")
    assert row["mfe_r"] == pytest.approx(2.0, abs=1e-3)
    assert row["mae_r"] == pytest.approx(0.5, abs=1e-3)


# ==================================================================================================
# TASK 3 — `_adet_benimse` tabanı da benimser
# ==================================================================================================
def test_t3_adet_benimseme_TABANI_DA_TASIR(sandbox_state):
    """Ayrışmanın KAYNAĞI: kitap aynanın adedini benimserken taban geride kalırsa payda donar.

    Kitap 17 → ayna 38 benimsenir; `qty` ve `qty_taban` BİRLİKTE hareket eder, yoksa R yine
    17 hissenin riskine bölünür ve tam olarak TSK-187'nin kapattığı ~2,24× şişme geri gelir."""
    from meridian import loop
    b = broker.PaperBroker(equity=100_000, slippage_bps=0, commission_per_share=0.0)
    b.positions["VRTX"] = _poz(VRTX_QTY)
    out: dict = {}
    yeni = loop._adet_benimse(b, "VRTX", VRTX_QTY, VRTX_AYNA, "2026-09-10", out)
    assert yeni == float(VRTX_AYNA)
    poz = b.positions["VRTX"]
    assert poz.qty == VRTX_AYNA and poz.qty_taban == VRTX_AYNA
    # ve kapanış R'si benimsenen adedin riskine bölünür
    row = b.close_position("VRTX", raw_exit=VRTX_CIKIS, reason="stop", ts="2026-09-10")
    assert row["r_multiple"] == -1.033
    assert row["r_payda_usd"] == pytest.approx(VRTX_AYNA * VRTX_RPS, abs=0.01)


def test_t3_sozluk_pozisyonda_da_taban_benimsenir(sandbox_state):
    """Eski çağıranlar pozisyonu SÖZLÜK olarak taşıyabiliyor — o dalda da taban geride kalmaz."""
    from meridian import loop

    class _Kitap:
        positions = {"X": {"ticker": "X", "qty": 17, "qty_taban": 17}}

    out: dict = {}
    assert loop._adet_benimse(_Kitap(), "X", 17, 38, "2026-09-10", out) == 38.0
    assert _Kitap.positions["X"] == {"ticker": "X", "qty": 38, "qty_taban": 38}


# ==================================================================================================
# TASK 4 — YASA 6: BEYAN EDİLEN OKUYUCU GERÇEKTEN VAR MI (tur-2, inceleme bloklayıcısı)
# ==================================================================================================
#: Bu dosyanın başındaki okuyucu beyanının hedefi. Yol DİZGE olarak burada durur çünkü çivinin
#: ölçtüğü şey tam olarak "beyan edilen dosya gerçekten bu alanı okuyor mu"dur.
PK2_SAYAC = KOK / "research" / "olcumler" / "edg088_golge_pilot" / "sayim.py"


def test_t4_beyan_edilen_OKUYUCU_dosyasi_VAR_ve_alani_OKUR():
    """Tur 1'in bloklayıcısı: docstring "sayim.py damgayı ayırır" diyordu, `r_payda` o dizinde
    HİÇ geçmiyordu. Okuyucusuz alan, Yasa 6'nın tam tanımıyla üretilmemiş bir alandır.

    Hangi değişiklikte kırılır: sayaçtan birim kapısı sökülürse (damga okuması ya da `birim_eski`
    sayacı kalkarsa) çivi öter ve beyan yeniden ölçülmeye zorlanır."""
    assert PK2_SAYAC.is_file(), PK2_SAYAC
    kaynak = PK2_SAYAC.read_text(encoding="utf-8")
    assert "r_payda" in kaynak, "beyan edilen okuyucu `r_payda` alanına HİÇ dokunmuyor"
    assert "def kontrol_olc" in kaynak and "r_payda_damgasi(" in kaynak, kaynak[:200]
    assert "birim_eski_n" in kaynak and "birim_eski_idler" in kaynak


def test_t4_okuyucu_damgayi_MOTORUN_SABITINDEN_alir_dizgeyi_YAZMAZ():
    """Tek-kaynak: sabit `broker.R_PAYDA_GIRIS`tir; sayaç onu İTHAL eder. Dizgeyi ikinci kez
    yazsaydı motorda ad değişince kapı sessizce HİÇBİR satırı elemezdi."""
    assert broker.R_PAYDA_GIRIS == "giris_riski"
    assert broker.R_PAYDA_OLCULEMEDI == "olculemedi"
    kaynak = PK2_SAYAC.read_text(encoding="utf-8")
    assert "brk.R_PAYDA_GIRIS" in kaynak, "sayaç damgayı motordan İTHAL etmiyor"
    assert f'"{broker.R_PAYDA_GIRIS}"' not in kaynak, "damga dizgesi sayaçta İKİNCİ kez yazılı"


def test_t4_motorun_yazdigi_damga_SABITIN_KENDISIDIR(sandbox_state):
    """Satırdaki değer sabitle aynı NESNEdir — `close_position` dizgeyi yerinde yazmıyor."""
    b = broker.PaperBroker(equity=100_000, slippage_bps=0, commission_per_share=0.0)
    b.positions["VRTX"] = _poz(VRTX_QTY)
    row = b.close_position("VRTX", raw_exit=VRTX_CIKIS, reason="stop", ts="2026-09-10")
    assert row["r_payda"] is broker.R_PAYDA_GIRIS
