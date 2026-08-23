"""test_bayat_sermaye_koku_v213.py — AYNANIN YARIM BOYUTLU EMRİNİN KÖKÜ (5-6 Ağustos 2026 vakası).

ÖLÇÜLEN OLGU (canlı A1, salt-okunur ölçüm 2026-08-07; belge:
`docs/BAYAT-SERMAYE-KOK-2026-08-07.md`). 2026-08-05T22:10:01Z'de ayna NUE/EMR/BKNG için
25/37/22 adet gönderdi; iç motor ertesi sabah AYNI planları 54/64/43 adetle doldurdu ve
`broker_reconcile` dört `MIRROR_DRIFT` alarmı bastı — dördü de ADET sapması dedi, hiçbiri
SEBEBİNİ adlandırmadı.

KÖK, ayna kodunda değil KİTABIN TABANINDA: gönderim anında `portfolio.realized_pnl`
−5.542,09$ idi (1 Ağustos'ta 0,0'a taşınmıştı), yani `broker.equity()` = 94.457,91$ ve
`derisk_mult(94457.91, 100000)` = **0,4916**. Ertesi gün taban geri getirildi (100.000/0,0) ve
iç motor ÇARPAN 1,0 ile doldurdu. Aynı plan, iki farklı sermaye tabanı, 22 saat arayla.

BU DOSYANIN ÇİVİLEDİĞİ ÜÇ OLGU (hepsi davranış düzeyinde; hiçbiri metin eşleşmesi değil):

  K1  BOYUT TABANI `cash` DEĞİL `realized_pnl`DİR. `PaperBroker.equity()` nakdi HİÇ okumaz
      (broker.py `PaperBroker.equity` gövdesi — satır çapası sembole çevrildi, 2026-08-23:
      K5 kaymasında bayatladı). Yalnız `cash`i düzelten bir onarım panoyu düzeltir, boyutlandırmayı
      DÜZELTMEZ; yalnız `realized_pnl`i kıpırdatan bir yazım ise panoda görünmeden emir
      boyutunu yarılar. Canlı vakada olan İKİNCİSİDİR.

  K2  5 AĞUSTOS ARİTMETİĞİ BİREBİR. `derisk_mult(94457.91, 100000) == 0.4916` ve NUE'nün iki
      bacağı bu çarpanla tam olarak 25 (ayna) ve 54 (iç motor) veriyor. Rampanın sabitleri
      (%3 muafiyet, %8 taban) değişirse bu test ÖNCE düşer — vakanın sayıları belgede yazılı.

  K3  DEDEKTÖR BOŞLUĞU — "TERS ONARILMIŞ" KİTAP ÜÇ KİMLİĞİ DE YEŞİL BIRAKIR. `recompute`in
      üç kimliği (realized_pnl · cash_identity · equity_curve_tail) kitabın KENDİ İÇİNDE
      tutarlı olup olmadığını sorar; kitabın hangi TABANDA durduğunu sormaz. Beyan defteri
      (`sermaye_resetleri`) silinip kitap defterin eski tabanına geri çekilirse üçü de
      dürüstçe YEŞİL olur — canlıda 4 Ağustos 21:47'den 5 Ağustos 22:31'e kadar tam olarak bu
      hâl vardı ve hiçbir alarm ötmedi. Boyut tabanı ise 5.542,09$ aşağıdaydı.
      BU TEST BİR DEDEKTÖRÜN YOKLUĞUNU İDDİA ETMEZ (öyle bir test, dedektör eklenince
      düşerdi): kimliklerin NE ÖLÇTÜĞÜNÜ çiviler — "iç tutarlılık" ile "doğru taban" ayrı
      büyüklüklerdir ve birincisi ikincisini imâ etmez.

HİÇBİR TEST CANLI STATE'E YAZMAZ: `sandbox_state` üzerinden koşar. Davranış değiştirilmedi —
bu dosya yalnız ölçer.
"""
from __future__ import annotations

import math

import pytest

from meridian import broker as BR
from meridian import ledgerstamp, recompute, sermaye, store
from meridian.broker import DERISK_FLOOR_DD, PaperBroker, derisk_mult
from meridian.score import START_EQUITY

# --- CANLI VAKANIN SAYILARI (A1 ölçümü 2026-08-07; kaynaklar belgede satır satır yazılı) -------
TOHUM_PNL = -5542.09          # Σ trades.pnl_dollars (95 satır, hepsi replay_seed)
DEFTER_TABANI = 94457.91      # START_EQUITY + TOHUM_PNL — 1 Ağustos ÖNCESİ kitap
BEYANLI_TABAN = 100000.0      # 1 Ağustos'ta taşınan taban (SR-20260801T151429+0000)
CANLI_CARPAN = 0.4916         # derisk_mult(94457.91, 100000) — aynanın 5 Ağustos'ta kullandığı
# VAKANIN GÜNÜNDE YÜRÜRLÜKTE OLAN RAMPA (2026-08-12'de eklendi — DONDURULMUŞ VAKA YASASI):
# 5 Ağustos'ta `derisk_mult`in bandı 0,03 / 0,08'di ve 0,4916 O BANDIN sayısıdır. 2026-08-12'de
# operatör bandı 0,15 / 0,36'ya taşıdı (goal.yaml `limits.derisk_*_dd`; karar penceresi §E.1/§E.3)
# ve BUGÜNKÜ bantla aynı çekilme %5,5 → çarpan 1,0 verir. Vaka testinin işi tarihi YENİDEN
# ÜRETMEKtir, bugünü değil: bant artık PARAMETRE olduğu için o günkü değer ADIYLA geçirilir
# (uydurma yok, sessiz kayma yok). Bugünkü bandı ölçen çiviler ayrı dosyada
# (tests/test_derisk_rampa_kablosu_v237.py) — ikisi karıştırılırsa vaka her bant değişiminde
# "çürür" ve tarihî kanıt kaybolurdu.
RAMPA_2026_08 = {"full_dd": 0.03, "floor_dd": 0.08}

# NUE planı — canlı defterden birebir (`P-2026-08-05-NUE`).
NUE_TETIK = 274.57            # plan `entry_trigger` — aynanın bacağı bunu kullandı
NUE_STOP = 257.4033
NUE_ICMOTOR_DOLUM = 273.6478074547237   # iç motorun 6 Ağustos açılış dolumu
NUE_SIZE_R = 0.89
ALPACA_EQUITY = 100012.07     # `alpaca_orders_sent` olayındaki `equity` — ALPACA hesabı, kitap DEĞİL


def _islem(i: int, pnl: float) -> dict:
    return {"id": f"T{i:05d}", "ts_open": "2023-01-10", "ts_close": f"2023-02-{i + 1:02d}",
            "ticker": "AAA", "side": "long", "entry": 100.0, "exit": 101.0, "qty": 10,
            "r_multiple": 0.5, "pnl_pct": 0.01, "pnl_dollars": pnl, "costs": 5.0,
            "exit_reason": "target", "strategy_version": 4, "regime": "trend_up",
            "setup": "breakout_vcp", "bars_held": 5, "kaynak": ledgerstamp.REPLAY_SEED}


def _tohum_defteri(toplam: float = TOHUM_PNL, n: int = 3) -> None:
    """Canlı hâlin küçük ölçeği: n tohum (replay_seed) işlemi, toplamı `toplam`."""
    her = round(toplam / n, 2)
    satirlar = [_islem(i, her) for i in range(n - 1)]
    satirlar.append(_islem(n - 1, round(toplam - her * (n - 1), 2)))
    store.write_jsonl(ledgerstamp.LEDGER, satirlar)


# =================================================================================================
# K1 — BOYUT TABANI `cash` DEĞİL `realized_pnl`
# =================================================================================================
def test_equity_nakdi_okumaz_boyut_tabani_realized_pnl_dir():
    """`cash`i 100.000'e çekmek boyutlandırmayı DÜZELTMEZ; `realized_pnl` tabanı belirler.

    Canlı vakada kitap tam olarak bu iki alandan İKİNCİSİYLE bozuldu — pano nakdi doğru
    gösterirken ayna yarım boyutta emir gönderdi."""
    b = PaperBroker(START_EQUITY, slippage_bps=5, commission_per_share=0.0)
    b.cash = BEYANLI_TABAN          # "nakit düzeltildi" — kozmetik
    b.realized_pnl = TOHUM_PNL      # taban HÂLÂ defterin eski tabanında
    assert b.equity() == pytest.approx(DEFTER_TABANI, abs=1e-6)

    b.realized_pnl = 0.0            # ASIL davranış alanı düzeltilince taban geri gelir
    assert b.equity() == pytest.approx(BEYANLI_TABAN, abs=1e-6)


def test_kitap_beyanli_tabanda_iken_carpan_1_0():
    """Kontrol grubu: taban yerindeyken kısma YOKTUR — vakadaki 0,4916 bir kaza değil, ölçülen
    bir çekilmenin karşılığıdır."""
    b = PaperBroker(START_EQUITY, slippage_bps=5, commission_per_share=0.0)
    b.realized_pnl = 0.0
    assert derisk_mult(b.equity(), BEYANLI_TABAN) == 1.0


# =================================================================================================
# K2 — 5 AĞUSTOS ARİTMETİĞİ BİREBİR
# =================================================================================================
def test_derisk_carpani_canli_vakanin_sayisini_verir():
    """`derisk_mult(94457.91, 100000)` = 0,4916 — O GÜNKÜ bantla (RAMPA_2026_08). Rampanın
    FORMÜLÜ değişirse (yuvarlama, sınır yönü, doğrusallık) burası hâlâ ÖNCE düşer; bandın
    operatör kararıyla taşınması ise artık testi çürütmez (bkz. RAMPA_2026_08 gerekçesi)."""
    dd = (BEYANLI_TABAN - DEFTER_TABANI) / BEYANLI_TABAN
    assert RAMPA_2026_08["full_dd"] < dd < RAMPA_2026_08["floor_dd"]   # o günkü rampanın İÇİNDE
    assert derisk_mult(DEFTER_TABANI, BEYANLI_TABAN, RAMPA_2026_08) == CANLI_CARPAN
    # BUGÜNKÜ bant aynı çekilmeyi kısmıyor — vakanın "aynı sayı bugün çıkmaz" hâli de ÖLÇÜLÜ
    # kalsın (yarın biri bandı okumadan bu dosyaya bakarsa yanlış sonuç çıkarmasın).
    assert derisk_mult(DEFTER_TABANI, BEYANLI_TABAN) == 1.0
    assert dd < DERISK_FLOOR_DD


def test_nue_iki_bacagin_adedi_birebir_yeniden_uretilir():
    """AYNI PLAN, İKİ SERMAYE TABANI, 22 SAAT ARAYLA → 25 ve 54 adet.

    Ayna bacağı (2026-08-05T22:10:01Z): boyut `eq` = Alpaca hesabı (100.012,07$) üzerinden
    ölçülür ama ÇARPAN kitaptan gelir (`derisk_mult(eq_now, peak)`), ve o gün kitap defterin
    eski tabanındaydı → 0,4916. R-payı planın TETİK fiyatından çıkar.
    İç motor bacağı (2026-08-06 açılışı): taban geri gelmişti → çarpan 1,0; R-payı GERÇEKLEŞEN
    dolumdan çıkar. İki bacağın farkı ne bir emir hatası ne bir slipajdır: KİTABIN ARADA
    DEĞİŞMESİDİR."""
    # --- ayna bacağı: kısılmış çarpan ---
    risk_ayna = NUE_SIZE_R * BR.RISK_PCT_PER_R * ALPACA_EQUITY * CANLI_CARPAN
    qty_ayna = int(math.floor(risk_ayna / (NUE_TETIK - NUE_STOP)))
    assert qty_ayna == 25, f"ayna bacağı yeniden üretilemedi: {qty_ayna}"

    # --- iç motor bacağı: çarpan 1,0 ---
    b = PaperBroker(START_EQUITY, slippage_bps=5, commission_per_share=0.0)
    b.realized_pnl = 0.0                                   # taban iade edilmişti
    qty_ic, risk_ic = b.size_position(NUE_ICMOTOR_DOLUM, NUE_STOP, NUE_SIZE_R, b.equity())
    assert risk_ic == pytest.approx(890.0, abs=0.01)       # canlı defterdeki `risk_dollars`
    assert qty_ic == 54, f"iç motor bacağı yeniden üretilemedi: {qty_ic}"

    # Sapmanın kendisi: canlı `MIRROR_DRIFT` satırı (içeride 54, Alpaca'da 25).
    assert qty_ic - qty_ayna == 29


def test_ayna_bacagi_kitap_tabani_yerindeyken_sapmazdi():
    """KARŞI-OLGU: aynı ayna kodu, taban yerinde olsaydı 51 adet gönderirdi — sapma 3'e
    (slipaj/tetik farkına) inerdi. Yani 29 adetlik sapmanın kaynağı ayna değil TABANDIR."""
    risk = NUE_SIZE_R * BR.RISK_PCT_PER_R * ALPACA_EQUITY * 1.0
    qty = int(math.floor(risk / (NUE_TETIK - NUE_STOP)))
    assert qty == 51
    assert 54 - qty == 3


# =================================================================================================
# K3 — DEDEKTÖR BOŞLUĞU: "ters onarılmış" kitap üç kimliği de YEŞİL bırakır
# =================================================================================================
def test_ters_onarilmis_kitap_uc_kimligi_de_YESIL_birakir(sandbox_state):
    """Kitap defterin eski tabanına çekilir ve beyan defteri BOŞSA `recompute` hiçbir şey
    söylemez — çünkü kimlikler İÇ TUTARLILIĞI ölçer, TABANI değil.

    Canlı karşılığı: 2026-08-04T21:47:54Z → 2026-08-05T22:31:56Z penceresi. Üç MAKULLÜK satırı
    yeşildi, `broker.equity()` ise 94.457,91$ idi ve ayna o pencerede emir gönderdi."""
    _tohum_defteri()
    store.write_json("portfolio.json", {
        "cash": DEFTER_TABANI, "realized_pnl": TOHUM_PNL, "last_id": 3, "positions": {},
        "armed": [], "pending_exits": {}, "last_date": "2026-08-04",
        "day_start_equity": DEFTER_TABANI, "peak_equity": BEYANLI_TABAN})
    store.write_json("equity_curve.json", {"version": 4,
                                           "points": [["2023-01-12", START_EQUITY],
                                                      ["2023-02-03", DEFTER_TABANI]]})

    rows = {r["check"]: r for r in recompute.report()["rows"]}
    for ad in ("realized_pnl", "cash_identity", "equity_curve_tail"):
        assert rows[ad]["ok"] is True, f"{ad} kırık çıktı — vakanın sessizliği yeniden üretilemedi"

    # …ve TAM O ANDA boyut tabanı 5.542,09$ aşağıdadır. Kimlikler bunu görmez.
    pf = store.read_json("portfolio.json", {})
    b = PaperBroker(START_EQUITY, slippage_bps=5, commission_per_share=0.0)
    b.cash, b.realized_pnl = pf["cash"], pf["realized_pnl"]
    assert b.equity() == pytest.approx(DEFTER_TABANI, abs=1e-6)
    assert derisk_mult(b.equity(), pf["peak_equity"], RAMPA_2026_08) == CANLI_CARPAN
    assert sermaye.ofset(pf) == 0.0        # beyan yok → ofset 0 → kimlikler "tutuyor" der


def test_beyan_yerindeyken_ayni_kitap_kimligi_KIRAR(sandbox_state):
    """AYNI kitap + beyan defteri DOLU → `realized_pnl` kimliği KIRILIR.

    Yani beyan yalnız bir muhasebe notu değil, tek DEDEKTÖR koludur: silindiği anda ters onarım
    görünmez hâle gelir. Bu, 2026-08-04 vakasının neden 5-6 Ağustos'ta emir boyutuna dönüştüğünü
    tek satırda açıklar."""
    _tohum_defteri()
    store.write_json("portfolio.json", {
        "cash": DEFTER_TABANI, "realized_pnl": TOHUM_PNL, "last_id": 3, "positions": {},
        "armed": [], "pending_exits": {}, "last_date": "2026-08-04",
        "day_start_equity": DEFTER_TABANI, "peak_equity": BEYANLI_TABAN,
        sermaye.RESET_KEY: [{"id": "SR-20260801T151429+0000", "ofset": -TOHUM_PNL}]})

    rows = {r["check"]: r for r in recompute.report()["rows"]}
    assert rows["realized_pnl"]["ok"] is False
    assert rows["cash_identity"]["ok"] is False
    # Ayrışmanın BÜYÜKLÜĞÜ canlı alarm metnindeki sayının aynısı: "5.542,09$ AYRIŞMA".
    assert abs(rows["realized_pnl"]["a"] - rows["realized_pnl"]["b"]) == pytest.approx(
        abs(TOHUM_PNL), abs=0.01)
