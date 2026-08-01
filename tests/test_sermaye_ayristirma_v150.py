"""test_sermaye_ayristirma_v150.py — SERMAYE TOHUM-AYRIŞTIRMASI (BT-1'in nakit ayağı).

ÖLÇÜLEN KUSUR (canlı state, 2026-08-01): `portfolio.json` cash = 94.457,91$ — 100.000$ başlangıçtan
`run.replay_seed`in ürettiği 95 satırlık ANTRENMAN defterinin −5.542,09$'ı düşülmüş hâli. Canlı-kâğıt
işlem sayısı SIFIR (ledgerstamp 95/95 replay_seed). İki ayrı zarar:

  GÖSTERİM — pano "Sermaye" diye bir antrenman artefaktı gösteriyordu.
  DAVRANIŞ — `broker.equity()` = start_equity + realized_pnl (broker.py:263) ve
             `loop._load_broker` start_equity'yi her turda START_EQUITY'ye sabitler; yani tohum
             zararı GERÇEK-CANLI çağın pozisyon boyutlarını kısıyordu. `peak_equity` = 102.520,45$
             ise simülasyonun tepesi ve de-risk rampası düşüşü ORADAN ölçüyordu.

BU DOSYANIN TAŞIDIĞI SÖZLEŞMELER:
  A. Araç davranışı  — kuru koşu varsayılan, canlı worker reddi, dolu pozisyon reddi, gerekçe eşiği.
  B. Yazımın kapsamı — kitabın DÖRT alanı taşınır; defterler (trades, equity_curve.points) ASLA.
  C. İdempotens      — ikinci uygulama `zaten_ayrisik` der ve tek bayt yazmaz.
  D. Beyan           — eğri işareti + `paper_equity_reset` olayı + monotonluk affı.
  E. Mutabakat       — `recompute`in üç kimliği reset SONRASI da YEŞİL kalır (ofset beyanlı) ve
                       resetten sonra kaybolan bir işlemi HÂLÂ yakalar (kimlik susturulmadı).
  F. Boyutlandırma   — reset ÖNCESİ/SONRASI qty farkı sentetik olarak GÖSTERİLİR. Bu davranış
                       değişikliği İSTENENDİR; belgelenmemiş bir yan etki olarak kalamaz.
  G. Yüzeyler        — /api/today köken bloğu + pano alanlarının varlığı.

HİÇBİR TEST CANLI STATE'E YAZMAZ: hepsi `sandbox_state` üzerinden koşar.
"""
from __future__ import annotations

import inspect
import json
import pathlib

import pytest

from meridian import broker as brk
from meridian import ledgerstamp, recompute, sermaye, store
from meridian.score import START_EQUITY

APP_JS = pathlib.Path(__file__).resolve().parent.parent / "meridian" / "web" / "app.js"


# =================================================================================================
# YARDIMCILAR — CANLI DİSK İZİNİN BİREBİR TAKLİDİ
# =================================================================================================
def _islem(i: int, ts_close: str, pnl: float, kaynak: str | None = ledgerstamp.REPLAY_SEED) -> dict:
    r = {"id": f"T{i:05d}", "ts_open": "2023-01-10", "ts_close": ts_close, "ticker": "AAA",
         "side": "long", "entry": 100.0, "exit": 101.0, "qty": 10, "r_multiple": 0.5,
         "pnl_pct": 0.01, "pnl_dollars": pnl, "costs": 5.0, "exit_reason": "target",
         "strategy_version": 4, "regime": "trend_up", "setup": "breakout_vcp", "bars_held": 5}
    if kaynak:
        r["kaynak"] = kaynak
    return r


def _tohumlanmis_dunya(n: int = 3, pnl_her: float = -1000.0, kaynak=ledgerstamp.REPLAY_SEED) -> dict:
    """CANLI HÂLİN KÜÇÜK ÖLÇEĞİ: n tohum işlemi, kitap `run._reset_book_to`nun yazdığı gibi
    (nakit = başlangıç + Σ pnl), eğri o toplu yazımdan kalan noktalarla."""
    trades = [_islem(i, "2023-02-0%d" % (i + 1), pnl_her, kaynak) for i in range(n)]
    realized = round(n * pnl_her, 2)
    cash = round(START_EQUITY + realized, 2)
    store.write_jsonl(ledgerstamp.LEDGER, trades)
    store.write_json(sermaye.EQUITY, {"version": 4, "points": [["2023-01-12", START_EQUITY],
                                                               ["2023-02-03", cash]]})
    pf = {"cash": cash, "realized_pnl": realized, "last_id": n, "positions": {}, "armed": [],
          "pending_exits": {}, "last_date": "2023-02-03", "day_start_equity": cash,
          "alpaca_submitted": [], "broker_rejected": [], "peak_equity": round(START_EQUITY + 2500, 2)}
    store.write_json(sermaye.PORTFOLIO, pf)
    store.write_json("monotonic_state.json", {"peak_equity": pf["peak_equity"],
                                              "book_date": "2023-02-03", "trades": n})
    return pf


def _parmak_izi() -> dict:
    """Sandbox'taki her dosyanın (yol → mtime_ns, boyut) haritası. 'Tek bayt yazılmadı' iddiası
    ÖLÇÜLÜR, umut edilmez."""
    from meridian import config
    kok = pathlib.Path(config.STATE)
    return {str(p.relative_to(kok)): (p.stat().st_mtime_ns, p.stat().st_size)
            for p in kok.rglob("*") if p.is_file()}


def _rc(check: str) -> dict:
    return next(r for r in recompute.report()["rows"] if r["check"] == check)


# =================================================================================================
# A — ARAÇ DAVRANIŞI
# =================================================================================================
def test_A1_kuru_kosu_VARSAYILANDIR_ve_tek_bayt_yazmaz(sandbox_state):
    """Veri taşıyan bir aracın varsayılanı yazmak olamaz (`barrepair`/`ledgerstamp`/`dbmigrate`
    kuralı). Kuru koşu NE YAZILACAĞINI sayar; diskte hiçbir şey değişmez."""
    _tohumlanmis_dunya()
    once = _parmak_izi()
    r = sermaye.plan()
    assert r["applied"] is False and r["yazildi"] is False
    assert r["uygulanabilir"] is True and r["engeller"] == []
    # ne yazılacağı SAYILIR: dört alan + ofset
    assert r["yeni"] == {"cash": 100000.0, "realized_pnl": 0.0,
                         "day_start_equity": 100000.0, "peak_equity": 100000.0}
    assert r["ofset"] == 3000.0            # 100.000 − 97.000
    assert _parmak_izi() == once


def test_A2_durum_da_salt_okunurdur(sandbox_state):
    _tohumlanmis_dunya()
    once = _parmak_izi()
    d = sermaye.durum()
    assert d["ayrisik"] is False and d["kitap"]["n_pozisyon"] == 0
    assert _parmak_izi() == once


def test_A3_canli_worker_gorulurse_uygula_REDDEDILIR(sandbox_state, monkeypatch, capsys):
    """`barrepair`in AYNI ölçümü. Burada red gerekçesi kilitten DAHA güçlüdür: `loop._save_broker`
    her turda cash/realized_pnl'i diskten okuduğu hâliyle geri yazar — canlı worker koşarken yapılan
    reset bir sonraki tikte SESSİZCE geri alınırdı."""
    _tohumlanmis_dunya()
    once = _parmak_izi()
    monkeypatch.setattr(sermaye, "_worker_running", lambda: True)
    assert sermaye.main(["--uygula"]) == 2
    assert "REDDEDİLDİ" in capsys.readouterr().err
    assert _parmak_izi() == once           # red = HİÇBİR yazım
    # kuru koşu ve --durum canlı worker'a RAĞMEN çalışır (okuma kimseyi bozmaz)
    assert sermaye.main([]) == 0 and sermaye.main(["--durum"]) == 0
    assert _parmak_izi() == once


def test_A3b_worker_olcumu_KOPYALANMAZ_cagrilir(sandbox_state):
    """İki kopya = iki farklı 'canlı' tanımı. Bu satır o sınıfı kod düzeyinde kapatır."""
    assert "from .barrepair import _worker_running" in inspect.getsource(sermaye._worker_running)


def test_A4_dolu_pozisyon_REDDEDILIR_ve_neden_soylenir(sandbox_state):
    """Açık pozisyon varken taban taşımak, o pozisyonun risk_dollars tabanını GERİYE DÖNÜK
    değiştirir — aynı pozisyon iki farklı sermayeye göre boyutlandırılmış olur."""
    pf = _tohumlanmis_dunya()
    pf["positions"] = {"AAA": {"ticker": "AAA", "qty": 10, "entry": 100.0}}
    store.write_json(sermaye.PORTFOLIO, pf)
    once = _parmak_izi()
    r = sermaye.uygula()
    assert r["ok"] is False and r["yazildi"] is False
    adlar = [e["ad"] for e in r["engeller"]]
    assert "dolu_pozisyon" in adlar
    engel = next(e for e in r["engeller"] if e["ad"] == "dolu_pozisyon")
    assert "AAA" in engel["ticker"] and len(engel["neden"]) > 60
    assert _parmak_izi() == once


def test_A5_kisa_gerekce_REDDEDILIR(sandbox_state):
    """YASA 4'ün buradaki karşılığı: taban taşımak geri alınabilir ama AÇIKLANAMAZ olamaz."""
    _tohumlanmis_dunya()
    once = _parmak_izi()
    r = sermaye.uygula("olmadı")
    assert r["ok"] is False and r["yazildi"] is False
    assert "gerekce_kisa" in [e["ad"] for e in r["engeller"]]
    assert _parmak_izi() == once
    # eşiğin kendisi de sınanır: tam sınırda geçer
    assert sermaye.plan("x" * sermaye.MIN_GEREKCE)["uygulanabilir"] is True
    assert sermaye.plan("x" * (sermaye.MIN_GEREKCE - 1))["uygulanabilir"] is False


# =================================================================================================
# B — YAZIMIN KAPSAMI
# =================================================================================================
def test_B1_uygula_kitabin_DORT_alanini_tasir(sandbox_state):
    _tohumlanmis_dunya()
    r = sermaye.uygula()
    assert r["ok"] is True and r["yazildi"] is True
    pf = store.read_json(sermaye.PORTFOLIO, {})
    assert pf["cash"] == 100000.0
    # ASIL DAVRANIŞ ALANI: `broker.equity()` cash'i DEĞİL bunu okur.
    assert pf["realized_pnl"] == 0.0
    assert pf["day_start_equity"] == 100000.0     # yoksa pano uydurma bir günlük kâr gösterirdi
    assert pf["peak_equity"] == 100000.0          # yoksa de-risk rampası hayali bir düşüş ölçerdi


def test_B2_dokunulmayanlar_YERINDE_kalir(sandbox_state):
    """Antrenman satırları öğrenmenin girdisidir; `last_id` yeni canlı satırların kimlik tabanıdır."""
    pf0 = _tohumlanmis_dunya()
    trades0 = store.read_jsonl(ledgerstamp.LEDGER)
    egri0 = store.read_json(sermaye.EQUITY, {})["points"]
    sermaye.uygula()
    assert store.read_jsonl(ledgerstamp.LEDGER) == trades0      # DEFTER DOKUNULMADI
    assert store.read_json(sermaye.EQUITY, {})["points"] == egri0   # EĞRİ NOKTALARI DOKUNULMADI
    pf = store.read_json(sermaye.PORTFOLIO, {})
    assert pf["last_id"] == pf0["last_id"] and pf["last_date"] == pf0["last_date"]


def test_B3_egriye_NOKTA_eklenmez_cunku_tohum_sinirini_kaydirirdi(sandbox_state):
    """BU TESTİN KENDİSİ BİR TASARIM KARARININ BEKÇİSİDİR.

    `ledgerstamp.seed_boundary()` tohum penceresinin sınırını EĞRİNİN SON NOKTASININ TARİHİNDEN
    okur (tek yazar `run.replay_seed`). Reset günü eğriye bir nokta eklenseydi sınır bugüne kayar
    ve bundan SONRAKİ her canlı satır `replay_seed` diye damgalanırdı — yani bu turun kapattığı
    kusuru, onu kapatan araç geri açardı. İşaret ayrı zarf anahtarında durur."""
    _tohumlanmis_dunya()
    sinir_once = ledgerstamp.seed_boundary()["replay_end"]
    n_once = len(store.read_json(sermaye.EQUITY, {})["points"])
    sermaye.uygula()
    eq = store.read_json(sermaye.EQUITY, {})
    assert len(eq["points"]) == n_once
    assert ledgerstamp.seed_boundary()["replay_end"] == sinir_once
    # ve işaret gerçekten YAZILDI (beyan kayboldu değil, yeri değişti)
    assert len(eq[sermaye.CURVE_MARK_KEY]) == 1


# =================================================================================================
# C — İDEMPOTENS
# =================================================================================================
def test_C1_ikinci_uygula_ZATEN_AYRISIK_der_ve_tek_bayt_yazmaz(sandbox_state):
    _tohumlanmis_dunya()
    sermaye.uygula()
    once = _parmak_izi()
    r2 = sermaye.uygula()
    assert r2["ok"] is False and r2["yazildi"] is False
    assert "zaten_ayrisik" in [e["ad"] for e in r2["engeller"]]
    assert _parmak_izi() == once
    assert len(sermaye.resetler()) == 1 and sermaye.ofset() == 3000.0


def test_C2_ayrisikligin_kaniti_NAKIT_DEGIL_kayittir(sandbox_state):
    """Canlı çağ kâr ederse nakit 100.000'den ayrılır — ayrışıklık SÜRER. Kanıt kitaptaki kayıttır."""
    _tohumlanmis_dunya()
    sermaye.uygula()
    pf = store.read_json(sermaye.PORTFOLIO, {})
    pf["cash"] = 104_321.0                       # canlı çağ kâr etti
    store.write_json(sermaye.PORTFOLIO, pf)
    assert sermaye.ayrisik() is True and sermaye.ofset() == 3000.0
    assert sermaye.plan()["uygulanabilir"] is False


# =================================================================================================
# D — BEYAN (işaret + olay + af)
# =================================================================================================
def test_D1_egri_isareti_ONCEKI_YENI_GEREKCE_tasir(sandbox_state):
    _tohumlanmis_dunya()
    g = "tohum zararı canlı sermayeden ayrıştırıldı — canlı çağ 100k tabanından başlar"
    sermaye.uygula(g)
    m = store.read_json(sermaye.EQUITY, {})[sermaye.CURVE_MARK_KEY][0]
    assert m["onceki_deger"] == 97000.0 and m["yeni_deger"] == 100000.0
    assert m["gerekce"] == g and m["tip"] == "paper_equity_reset"
    assert m["egri_son_nokta"] == ["2023-02-03", 97000.0]
    assert len(m["not"]) > 40                    # eğri neden SİLİNMEDİ — okurun sorusu yanıtlı


def test_D2_olay_yazilir_ve_ESKI_YENI_TOHUM_LEDGERSTAMP_tasir(sandbox_state):
    _tohumlanmis_dunya()
    g = "antrenman tohumu ayrıştırıldı; canlı çağ temiz tabandan başlasın diye"
    sermaye.uygula(g)
    ev = [e for e in store.read_jsonl("events.jsonl") if e.get("event") == sermaye.EVENT]
    assert len(ev) == 1
    e = ev[0]
    assert e["eski_cash"] == 97000.0 and e["yeni_cash"] == 100000.0 and e["ofset"] == 3000.0
    assert e["eski_realized_pnl"] == -3000.0 and e["yeni_realized_pnl"] == 0.0
    assert e["tohum_pnl_usd"] == -3000.0
    assert e["ledgerstamp_replay_seed_n"] == 3 and e["ledgerstamp_live_paper_n"] == 0
    assert e["gerekce"] == g and len(e["gerekce"]) >= sermaye.MIN_GEREKCE


def test_D3_tepe_gerilemesi_YAZILI_AF_alir(sandbox_state):
    """Monotonluk dedektörü `peak_equity` küçülmesini haklı olarak bayraklar. Sessizce geçmek ya da
    kırmızı bırakmak yerine depoda zaten kurulu üçüncü yol: tam eşleşmeli, gerekçeli af."""
    from meridian import watchdog as wd
    _tohumlanmis_dunya()
    r = sermaye.uygula()
    assert r["af"]["verildi"] is True and r["af"]["was"] == 102500.0 and r["af"]["now"] == 100000.0
    a = wd._amnesty_index()["peak_equity"]
    assert a["was"] == 102500.0 and a["now"] == 100000.0 and len(a["reason"]) > 60
    assert a["by"] == "meridian.sermaye"
    # ve dedektör GERÇEKTEN susar (af iddiası değil, ÖLÇÜM)
    rep = wd.monotonicity_report()
    assert not [x for x in rep["regressions"] if x["field"] == "peak_equity"]
    assert [x for x in rep["amnestied"] if x["field"] == "peak_equity"]
    # AF YÜK TAŞIYOR MU? Kaldırılınca bayrak GERİ GELMELİ — yoksa bu test af olmadan da yeşil
    # kalır ve hiçbir şey kanıtlamaz (bu depoda "geçtiğinde bile bir şey kanıtlamayan test" sınıfı
    # ayrıca kayıtlı).
    store.write_json(wd.AMNESTY_FILE, [])
    assert [x for x in wd.monotonicity_report()["regressions"] if x["field"] == "peak_equity"]


def test_D3b_gerileme_YOKSA_af_verilmez(sandbox_state):
    """Gereksiz af, ileride GERÇEK bir kaybı sessizce yutabilecek bir muafiyet bırakırdı."""
    _tohumlanmis_dunya()
    store.write_json("monotonic_state.json", {"peak_equity": 99_000.0})
    r = sermaye.uygula()
    assert r["af"]["verildi"] is False and "gerileme yok" in r["af"]["neden"]


# =================================================================================================
# E — MUTABAKAT (recompute kimlikleri)
# =================================================================================================
def test_E1_reset_ONCESI_uc_kimlik_yesil(sandbox_state):
    """Taban ölçümü: tohumlanmış dünya zaten tutarlıdır (run._reset_book_to kimliği yazıyor)."""
    _tohumlanmis_dunya()
    for c in ("realized_pnl", "cash_identity", "equity_curve_tail"):
        assert _rc(c)["ok"] is True, c


def test_E2_reset_SONRASI_uc_kimlik_HALA_yesil(sandbox_state, monkeypatch):
    """Reset üç kimliği birden bozar — çünkü kitap yeni tabanda, defter eski tabanda. Ofset BEYAN
    edildiği için kimlik ölçmeye devam eder. Susturulsalardı bu satır bir şey kanıtlamazdı."""
    _tohumlanmis_dunya()
    sermaye.uygula()
    for c in ("realized_pnl", "cash_identity", "equity_curve_tail"):
        satir = _rc(c)
        assert satir["ok"] is True, (c, satir["detail"])
        assert "sermaye reset ofseti" in (satir["a_yol"] + satir["b_yol"])
        assert "beyanlı sermaye reset ofseti +3,000.00$" in satir["detail"]
    # OFSET YÜK TAŞIYOR MU? Beyan okunamazsa ÜÇÜ DE kırmızı yanar — yani reset gerçekten üç kimliği
    # birden bozuyor ve yeşilliği ofset sağlıyor (kimlikler susturulmuş DEĞİL).
    monkeypatch.setattr(recompute, "_sermaye_ofseti", lambda pf: 0.0)
    for c in ("realized_pnl", "cash_identity", "equity_curve_tail"):
        assert _rc(c)["ok"] is False, c


def test_E3_kimlik_SUSTURULMADI_resetten_sonraki_kayip_YAKALANIR(sandbox_state):
    """EN ÖNEMLİ MUTABAKAT TESTİ. Ofsetli kimlik hâlâ bir KİMLİKTİR: reset sonrası deftere bir
    canlı işlem girer ve kitap onu saymazsa satır KIRMIZI yanmalı. Yanmıyorsa ofset kimliği
    ölçmüyor, gizliyor demektir."""
    _tohumlanmis_dunya()
    sermaye.uygula()
    trades = store.read_jsonl(ledgerstamp.LEDGER)
    trades.append(_islem(99, "2026-08-05", 750.0, ledgerstamp.LIVE_PAPER))
    store.write_jsonl(ledgerstamp.LEDGER, trades)     # defterde var, kitapta YOK
    assert _rc("realized_pnl")["ok"] is False
    assert _rc("cash_identity")["ok"] is False
    # kitap işlemi görünce kimlik yeniden yeşile döner
    pf = store.read_json(sermaye.PORTFOLIO, {})
    pf["realized_pnl"], pf["cash"] = 750.0, 100_750.0
    store.write_json(sermaye.PORTFOLIO, pf)
    assert _rc("realized_pnl")["ok"] is True and _rc("cash_identity")["ok"] is True


def test_E4_resetsiz_depoda_ofset_SIFIR_ve_davranis_DEGISMEZ(sandbox_state):
    """Modül, reset yapılmamış bir depoda tamamen görünmez olmalı."""
    _tohumlanmis_dunya()
    assert sermaye.ofset() == 0.0
    assert recompute._sermaye_ofseti(store.read_json(sermaye.PORTFOLIO, {})) == 0.0
    assert recompute._ofset_notu(0.0) == ""


# =================================================================================================
# F — BOYUTLANDIRMA (istenen davranış değişikliği, belgeli)
# =================================================================================================
def test_F1_reset_ONCESI_SONRASI_qty_farki_GOSTERILIR(sandbox_state):
    """BU TURUN AMACI TAM OLARAK BUDUR — kozmetik değil davranışsal.

    `loop._load_broker` her turda `PaperBroker(START_EQUITY, …)` kurup üstüne diskten
    `realized_pnl`i basar; `broker.equity()` = start_equity + realized_pnl. Yani boyutlandırma
    tabanı `cash` DEĞİL `realized_pnl`dir — ve reset onu sıfırlar. Fark burada SENTETİK olarak
    ölçülür, iddia edilmez."""
    _tohumlanmis_dunya(n=3, pnl_her=-1000.0)

    def _taban_ve_qty():
        pf = store.read_json(sermaye.PORTFOLIO, {})
        b = brk.PaperBroker(START_EQUITY, 5.0, 0.0)
        b.cash, b.realized_pnl = pf["cash"], pf["realized_pnl"]     # loop._load_broker'ın aynısı
        eq = b.equity()
        qty, risk = b.size_position(entry_fill=100.0, stop=98.0, size_r=1.0, equity=eq)
        return eq, qty, risk

    eq_once, qty_once, risk_once = _taban_ve_qty()
    sermaye.uygula()
    eq_sonra, qty_sonra, risk_sonra = _taban_ve_qty()

    assert eq_once == 97_000.0 and eq_sonra == 100_000.0        # taban 100k'ya döndü
    assert qty_sonra > qty_once                                  # ve boyut GERÇEKTEN büyüdü
    assert (qty_once, qty_sonra) == (int(risk_once / 2.0), int(risk_sonra / 2.0))
    # oran, tabanların oranıdır — tohum zararı artık boyutu kısmıyor
    assert risk_sonra / risk_once == pytest.approx(100_000.0 / 97_000.0, rel=1e-9)


def test_F2_cash_TEK_BASINA_boyutlandirmayi_degistirmezdi(sandbox_state):
    """KUSURUN KENDİSİNİN TESTİ: yalnız `cash`i 100.000'e çekmek KOZMETİK olurdu. Bu satır, ileride
    biri `realized_pnl` sıfırlamasını 'gereksiz' diye kaldırırsa kırmızı yanar."""
    _tohumlanmis_dunya(n=3, pnl_her=-1000.0)
    pf = store.read_json(sermaye.PORTFOLIO, {})
    b = brk.PaperBroker(START_EQUITY, 5.0, 0.0)
    b.cash, b.realized_pnl = 100_000.0, pf["realized_pnl"]        # YALNIZ nakit resetlendi
    assert b.equity() == 97_000.0                                 # boyutlandırma tabanı DEĞİŞMEDİ


# =================================================================================================
# G — YÜZEYLER (api + pano)
# =================================================================================================
@pytest.fixture
def client(sandbox_state, monkeypatch):
    from fastapi.testclient import TestClient

    from meridian import api
    monkeypatch.setattr(api, "DASH_TOKEN", "")
    return TestClient(api.app)


def test_G1_api_today_koken_blogunu_TASIR(client, sandbox_state):
    _tohumlanmis_dunya()
    d = client.get("/api/today").json()
    k = d["sermaye_koken"]
    assert {"gercek_canli_sermaye", "canli_islem_n", "tohum_etkisi_usd", "reset_tarihi"} <= set(k)
    assert k["gercek_canli_sermaye"] == 97000.0 and k["canli_islem_n"] == 0
    assert k["tohum_etkisi_usd"] == -3000.0
    assert k["tohum_etkisi_durum"] == "sermayeden_dusuluyor" and k["reset_tarihi"] is None
    assert k["renk"] == "notr"                    # canlı P&L 0 → NÖTR (kırmızı/yeşil değil)


def test_G2_api_today_reset_SONRASI_ayristirildi_der_SIFIR_demez(client, sandbox_state):
    """Brief kuralı: reset sonrası tohum etkisi 0 YAZILMAZ — ölçülmüş değeriyle durur, DURUMU
    değişir. 0 yazmak, ölçülmüş bir olguyu silmek olurdu."""
    _tohumlanmis_dunya()
    sermaye.uygula()
    k = client.get("/api/today").json()["sermaye_koken"]
    assert k["gercek_canli_sermaye"] == 100000.0
    assert k["tohum_etkisi_usd"] == -3000.0        # SIFIR DEĞİL
    assert k["tohum_etkisi_durum"] == "ayristirildi"
    assert "ayrıştırıldı" in k["tohum_etkisi_ibare"]
    assert k["reset_tarihi"] and k["ayrisik"] is True and k["ofset_usd"] == 3000.0


def test_G3_damgasiz_defterde_tohum_etkisi_NONE_uydurma_sifir_DEGIL(client, sandbox_state):
    """UYDURMA YASAĞI. Damgasız bir defterde `replay_seed` toplamı 0.0 çıkar — ama bu 'etki yok'
    değil 'ölçülemedi'dir. Canlı Mac kopyasındaki hâl tam budur (95/95 belirsiz)."""
    _tohumlanmis_dunya(kaynak=None)
    k = client.get("/api/today").json()["sermaye_koken"]
    assert k["tohum_etkisi_usd"] is None
    assert k["belirsiz_islem_n"] == 3 and k["tohum_islem_n"] == 0
    assert "ÖLÇÜLEMEDİ" in k["tohum_etkisi_neden"]


def test_G3b_bayat_nabiz_BEYAN_edilir(sandbox_state):
    """Büyük sayı `today.equity`den gelir ve o da NABIZDAN okunur. Reset anı ile worker'ın ilk turu
    ARASINDA pano iki farklı sermaye bilir; sessiz kalmak bu turun kapattığı hâlin tekrarı olurdu."""
    _tohumlanmis_dunya()
    # ÜÇÜNCÜ HÂL: nabız hiç yazılmamışsa cevap "ayrışma yok" DEĞİL "kıyas yapılamadı"dır.
    assert sermaye.koken()["nabiz_ayrisik"] is None
    store.write_json("heartbeat.json", {"equity": 97_000.0, "regime": "trend_up"})
    assert sermaye.koken()["nabiz_ayrisik"] is False       # nabız kitapla aynı → sessiz
    sermaye.uygula()                                        # kitap 100k'ya taşındı, nabız 97k kaldı
    k = sermaye.koken()
    assert k["nabiz_ayrisik"] is True and k["nabiz_sermaye"] == 97_000.0
    assert k["gercek_canli_sermaye"] == 100_000.0           # otorite KİTAP, nabız değil
    assert any("nabız" in u for u in sermaye.durum()["uyarilar"])
    assert "nabiz_ayrisik" in APP_JS.read_text()            # pano da susmuyor


def test_G4_canli_islem_varsa_renk_NOTR_DEGIL(sandbox_state):
    """Boyanma kuralının diğer yarısı: gerçek canlı P&L varsa renk gelir."""
    _tohumlanmis_dunya()
    trades = store.read_jsonl(ledgerstamp.LEDGER)
    trades.append(_islem(9, "2026-08-05", 420.0, ledgerstamp.LIVE_PAPER))
    store.write_jsonl(ledgerstamp.LEDGER, trades)
    k = sermaye.koken()
    assert k["canli_islem_n"] == 1 and k["canli_pnl_usd"] == 420.0 and k["renk"] == "poz"


def test_G5_pano_koken_blogunu_OKUR_ve_tek_islevden_cizer(sandbox_state):
    """YASA 6: alan yazıldı ve OKUNUYOR. İki yüzey (kenar şeridi + Bugün kahramanı) AYNI işlevi
    çağırır — iki kopya olsaydı biri bayatlar ve pano kendi içinde çelişirdi."""
    js = APP_JS.read_text()
    assert "sermaye_koken" in js
    assert js.count("sermayeKokenSatiri(") >= 3          # 1 tanım + 2 yüzey (şerit + kahraman)
    assert js.count("sermayeIbaresi(") >= 2              # 1 tanım + kahraman kartı
    # KISA/İBARELİ KİPLER: dar şeritte gerekçe metni kısalır, ibare AYRI SATIRA iner (`.acct .r b`
    # nowrap taşır — değerin yanına kelime eklemek satırı taşırırdı).
    assert "ibareyle: true" in js and "kisa: true" in js
    assert "SERMAYE_RENK" in js and "notr" in js
    # NÖTR HÂL GERÇEKTEN NÖTRDÜR: `notr` bir sınıf adına değil BOŞ dizgeye eşlenir
    assert 'notr: ""' in js.replace("'", '"')


def test_G6_terminal_ve_pano_AYNI_hesabi_okur(sandbox_state):
    """İki hesap olsaydı operatörün terminali ile pano aynı gün farklı bir 'gerçek-canlı sermaye'
    söyleyebilirdi. CLI durumu köken bloğunu KOPYALAMAZ, gömer."""
    _tohumlanmis_dunya()
    assert sermaye.durum()["koken"] == sermaye.koken()
    from meridian import api
    assert "sermaye.koken" in inspect.getsource(api.api_today).replace("_sr.", "sermaye.")


# =================================================================================================
# H — CLI YÜZEYİ (uçtan uca, JSON dahil)
# =================================================================================================
def test_H1_cli_json_makine_okunur_ve_kuru_kosu_yazmaz(sandbox_state, monkeypatch, capsys):
    _tohumlanmis_dunya()
    monkeypatch.setattr(sermaye, "_worker_running", lambda: False)
    once = _parmak_izi()
    assert sermaye.main(["--json"]) == 0
    r = json.loads(capsys.readouterr().out)
    assert r["applied"] is False and r["ofset"] == 3000.0
    assert _parmak_izi() == once
    assert sermaye.main(["--durum", "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["koken"]["canli_islem_n"] == 0


def test_H2_cli_uygula_yazar_ve_ikinci_kez_1_doner(sandbox_state, monkeypatch, capsys):
    _tohumlanmis_dunya()
    monkeypatch.setattr(sermaye, "_worker_running", lambda: False)
    assert sermaye.main(["--uygula", "--gerekce", "tohum ayrıştırması: canlı çağ temiz tabandan"]) == 0
    assert store.read_json(sermaye.PORTFOLIO, {})["cash"] == 100000.0
    capsys.readouterr()
    assert sermaye.main(["--uygula", "--gerekce", "tohum ayrıştırması: canlı çağ temiz tabandan"]) == 1
    assert "zaten_ayrisik" in capsys.readouterr().out
