"""test_kovab_borclar_v167.py — KOVA-B KALAN BORÇLAR (denetim 2026-08-02, C18 adversarial notu + tur borçları).

DÖRT KÜÇÜK BORÇ, İKİ SINIF:

  SINIF 1 — "TEK YASA, İKİ MOTOR" YARIM KABLOLU (C18'in adversarial notu). İki-motor turu E1 giriş
  limitinin ATR bacağını `backtest.replay` ve gölge-v2'ye bağladı; aynı boşluğu taşıyan İKİ motor
  daha vardı ve denetim notu bunu adıyla yazdı:
    * `mutation.build_state` — dedektör bataryasının yargıladığı TEMEL DURUMU üreten motor.
      `fill_entry`e `atr=` geçmiyordu → `entry_limit_price` `a > 0` dalına HİÇ giremiyor. Sonuç
      sinsi: yasanın ATR dalını bozan bir gelecek değişikliği, "dedektörler neyi göremiyor?"
      sorusunu ölçen fikstürde HİÇ İZ BIRAKMAZDI.
    * `intraday_shadow.record` — Faz 4b'nin kanıt tabanı. Aynı boşluk, ama burada kırılma TEK
      YÖNLÜ ve ÖLÇÜM DEĞİŞTİRİCİ: limit daima %1 tavanındayken gölge, canlının REDDEDECEĞİ
      dolumları `would_submit` diye yazar → "intraday icra açılsa ne olurdu?" sorusuna iyimser
      cevap verir.

  SINIF 2 — YASA 6: OKUYUCUSUZ YAZIM. İki alan üretildi, hiç okunmadı:
    * `BacktestResult.entry_rejects` (iki-motor turu) — hiçbir ÜRETİM yolu basmıyordu. Yazılıp
      okunmayan sayaç, hiç ölçülmemiş sayaçla aynı şeydir.
    * `composite_queue.status = measure_failed` (öğrenme turu, C14) — `nous_eval._akibet` genel
      dala düşüp beyne "kuyruk durumu: measure_failed" diyordu: `neden` alanı, yani beynin bir
      sonraki öneriyi değiştirmesini sağlayacak TEK bilgi, kayboluyordu.

YÖNTEM: iddialar DAVRANIŞSAL — motorlar gerçekten koşturulur, `fill_entry` çağrıları casusla
yakalanır, konsol çıktısı okunur. Kaynak metni okuyan tek çivinin (mutasyon çağrı yeri) yanında bir
POZİTİF KONTROL vardır: ATR bacağının fikstürde GERÇEKTEN bağladığı ayrıca gösterilir — bağlamayan
bir bacak koruma değil dekordur.
"""
from __future__ import annotations

import ast
import datetime as dt
import inspect
import pathlib

import pytest

from meridian import backtest, broker as BR, config, intraday_shadow, mutation, nous_eval, run, store
from meridian.broker import PaperBroker

MUT_SRC = pathlib.Path("meridian/mutation.py")

# OPERATÖR KARARI 2026-08-03 (goal.yaml `execution_v2` karar-yorumu; kart EXE-2026-001 hükmü + ölçüm
# research/olcumler/e1_grid_2026-08-03): E1 giriş limiti 0,5·ATR/%1 → 100·ATR/%4 yapıldı, yani
# YÜRÜRLÜKTE ATR bacağı bağlamaz. Aşağıdaki iki POZİTİF KONTROL, kablonun taşıdığı ATR'nin limiti
# DARALTABİLDİĞİNİ (bacağın dekor olmadığını) ölçer — bu bir MEKANİZMA iddiasıdır, yürürlük iddiası
# değil — ve yasa kaynağı bu yüzden eski kart varsayılanına AÇIKÇA sabitlenir.
KART_YASASI = {"limit_atr_mult": 0.5, "limit_pct_cap": 0.01}

_SIMDI = dt.datetime(2026, 7, 27, 15, 40, 0, tzinfo=dt.timezone.utc)   # RTH içi (11:40 ET)
_SEANS = "2026-07-27"


# =================================================================================================
# C18/a — MUTASYON MOTORU: fikstürün dolum yolu ATR taşır
# =================================================================================================
def _fill_casusu(monkeypatch) -> list:
    """`PaperBroker.fill_entry`e giden çağrıları kaydet (gerçek fonksiyon yine koşar)."""
    cagrilar: list = []
    asil = PaperBroker.fill_entry

    def sarmal(self, plan, next_open, ts, equity, **kw):
        cagrilar.append({"plan_id": plan.get("id"), "ticker": plan.get("ticker"),
                         "next_open": next_open, **kw})
        return asil(self, plan, next_open, ts, equity, **kw)

    monkeypatch.setattr(PaperBroker, "fill_entry", sarmal)
    return cagrilar


def test_c18_mutation_fill_yolu_ATR_TASIR(tmp_path, monkeypatch):
    """DAVRANIŞ: `build_state`in her dolumu `atr=` argümanıyla çağrılır ve İKİ DAL da koşar.

    Tek dallı bir fikstür iki dallı bir yasayı yarım ölçer: `entry_limit_price` "ATR ölçüldü"
    (min(mult·ATR, pct)) ve "ölçülemedi" (yalnız pct) dallarını AYRI işletir."""
    cagrilar = _fill_casusu(monkeypatch)

    mutation.build_state(tmp_path / "baseline")

    assert cagrilar, "fikstür hiç dolum denemedi — test ölçtüğünü sandığı şeyi ölçmüyor"
    assert all("atr" in c for c in cagrilar), \
        "`fill_entry` ATR argümanı OLMADAN çağrıldı — E1 limitinin ATR bacağı bu motorda hâlâ ölü"
    olculen = [c["atr"] for c in cagrilar if c["atr"] is not None]
    olculemeyen = [c for c in cagrilar if c["atr"] is None]
    assert olculen, "hiçbir dolum pozitif ATR taşımadı — `a > 0` dalı fikstürde hiç koşmuyor"
    assert olculemeyen, \
        "hiçbir dolum ATR=None taşımadı — 'ATR ölçülemedi' dalı (yalnız yüzde tavanı) hiç koşmuyor"


def test_c18_mutation_ATR_bacagi_GERCEKTEN_baglar(tmp_path, monkeypatch):
    """POZİTİF KONTROL: fikstür ATR'si yalnız TAŞINMIYOR, limiti DARALTIYOR.

    `FIXTURE_ATR_PCT` %2 seçilseydi 0,5·ATR = %1 = yüzde tavanı olur, `min()` ayırt etmez ve bacak
    dekora dönerdi — taşınıyor görünen, hiçbir şeyi değiştirmeyen bir argüman."""
    cagrilar = _fill_casusu(monkeypatch)
    mutation.build_state(tmp_path / "baseline")

    # MEKANİZMA: yasa kaynağı kart varsayılanında sabit (bkz. KART_YASASI) — yürürlükteki 100·ATR/%4
    # yasasında `min()` HİÇBİR ATR'yi ayırt etmez, yani ölçüm fikstürü değil kararı ölçerdi.
    yasa = BR.entry_law(KART_YASASI)
    daraltan = 0
    for c in cagrilar:
        if c["atr"] is None:
            continue
        tetik = float(c["next_open"])           # fikstürde tetik == açılış
        if BR.entry_limit_price(tetik, c["atr"], yasa) < BR.entry_limit_price(tetik, None, yasa):
            daraltan += 1
    assert daraltan > 0, ("fikstür ATR'si hiçbir dolumda limiti daraltmadı — bacak taşınıyor ama "
                          f"DEKOR (FIXTURE_ATR_PCT={mutation.FIXTURE_ATR_PCT}, yasa={yasa})")


def test_c18_mutation_cagri_YERI_atr_argumanini_gecirir():
    """FAZ İDDİASI (davranışla gösterilemez): argüman PLAN SÖZLÜĞÜNDEN değil AYRI argümandan gelir.

    Plan şeması iki motorda AYNI kalmak zorunda (test_differential_v60) — biri ATR'yi plana alan
    bir "düzeltme" yazarsa davranış testi yine yeşil kalır, sözleşme ise kırılmış olur."""
    agac = ast.parse(MUT_SRC.read_text())
    fills = [n for n in ast.walk(agac)
             if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
             and n.func.attr == "fill_entry"]
    assert fills, "mutation.py'de `fill_entry` çağrısı bulunamadı — test bayatlamış"
    for c in fills:
        kw = {k.arg for k in c.keywords}
        assert "atr" in kw, "`fill_entry` çağrısında `atr=` anahtar argümanı YOK"
        assert "reject_out" in kw, "`reject_out=` yok — reddedilen dolum sessizce yutulur (YASA 4)"
    kaynak = MUT_SRC.read_text()
    assert '"atr"' not in kaynak.split("def _build_ledgers")[1].split("plans.append")[0], \
        "ATR plan SÖZLÜĞÜNE yazılmış — defter şeması iki motorda ayrışır (test_differential_v60)"


def test_c18_mutation_TEMEL_DURUM_islemsiz_GO_plani_birakmaz(tmp_path):
    """ATR bacağı bağlandıktan sonra da temel durum TEMİZ kalmalı: GO damgalı her plan bir işlem
    satırı üretir. Kirli bir temelde her mutasyon "yakalandı" görünür ve kapsama sayısı yalan söyler
    — modülün kendi ilk tasarım kararı budur."""
    st = mutation.build_state(tmp_path / "baseline")
    planlar = mutation.rjsonl(st, "trade_plans.jsonl")
    islemler = mutation.rjsonl(st, "trades.jsonl")
    go = [p for p in planlar if p.get("gate_verdict") != "NO_GO"]
    assert go, "fikstürde hiç GO plan yok — ölçüm anlamsız"
    assert len(islemler) == len(go), \
        (f"{len(go)} GO plan ama {len(islemler)} işlem — ATR limiti dolumları düşürdü ve temel durum "
         f"'sessiz kayıp' ile kirlendi")


# =================================================================================================
# C18/b — GÖLGE MOTORU (intraday_shadow): ATR canlı motorun YAN TABLOSUNDAN gelir
# =================================================================================================
@pytest.fixture
def saat(monkeypatch):
    from meridian import barclock
    monkeypatch.setattr(barclock, "now", lambda: _SIMDI)
    intraday_shadow.reset_dedup()
    yield _SIMDI
    intraday_shadow.reset_dedup()


def _plan(**kw) -> dict:
    p = {"id": "P-2026-07-27-AAA", "ticker": "AAA", "side": "long", "entry_trigger": 105.0,
         "stop": 95.0, "profit_target": 130.0, "size_r": 1.0, "r_multiple_expected": 2.5,
         "regime_at_plan": "chop", "strategy_version": 4, "setup": "breakout_vcp", "score": 80}
    p.update(kw)
    return p


def _bar(o=100.0, h=112.0, l=99.0, c=110.0) -> dict:
    t = _SIMDI - dt.timedelta(minutes=2)
    return {"t": t.strftime("%Y-%m-%dT%H:%M:00Z"), "o": o, "h": h, "l": l, "c": c, "v": 5000.0}


def _kitap(state, *, entry_law=None):
    """Kapıların HEPSİ ölçülebilir — gölge, kaynağı olmayan kapıyı fail-closed sayar."""
    kitap = {"cash": 100_000.0, "realized_pnl": 0.0, "last_id": 0, "positions": {},
             "armed": [], "peak_equity": 100_000.0, "day_start_equity": 100_000.0}
    if entry_law is not None:
        kitap["entry_law"] = entry_law
    store.write_json("portfolio.json", kitap)
    store.write_json("heartbeat.json", {"ts": "2026-07-27T13:56:11+00:00", "day_pnl_pct": 0.0})
    store.write_json("data_quality.json", {"date": "2026-07-24", "data_halt": False})


def test_c18_golge_fill_ATR_yan_TABLODAN_gelir(sandbox_state, saat, monkeypatch):
    """DAVRANIŞ: `entry_law[plan_id].atr` ne ise `fill_entry`e O gider — yeniden HESAPLANMAZ.

    İkinci bir ATR hesabı, modülün başlığındaki hatanın kendisi olurdu: iki hesap zamanla ayrışır
    ve gölge defteri EOD'yi değil KENDİNİ ölçmeye başlar."""
    plan = _plan()
    _kitap(sandbox_state, entry_law={plan["id"]: {"atr": 3.25, "limit": 106.6, "law": "E1-v1"}})
    cagrilar = _fill_casusu(monkeypatch)

    satir = intraday_shadow.record(plan, _bar(o=100.0), _SIMDI)

    assert satir is not None and cagrilar, "gölge satırı yazılmadı — test ölçtüğünü ölçmüyor"
    assert cagrilar[0]["atr"] == 3.25, \
        f"gölge `fill_entry`e ATR taşımadı ({cagrilar[0].get('atr')!r}) — limit hâlâ %1 tavanında"
    assert satir["atr"] == 3.25 and "entry_law" in satir["atr_kaynak"], \
        "satır hangi ATR ile karar verildiğini BEYAN etmiyor (YASA 6 okuyucusu yok)"


def test_c18_golge_yan_tablo_YOKSA_atr_None_ve_BEYANLI(sandbox_state, saat, monkeypatch):
    """UYDURMA YASAĞI: tabloda satır yoksa ATR uydurulmaz — None kalır ve satır bunu SÖYLER."""
    _kitap(sandbox_state, entry_law={})     # tohumlanmış defter / eski silahlı plan hâli
    cagrilar = _fill_casusu(monkeypatch)

    satir = intraday_shadow.record(_plan(), _bar(o=100.0), _SIMDI)

    assert cagrilar[0]["atr"] is None, "ATR yokken 0.0/varsayılan uyduruldu"
    assert satir["atr"] is None and "ÖLÇÜLEMEDİ" in satir["atr_kaynak"], \
        f"ölçülemeyen ATR beyan edilmiyor: {satir['atr_kaynak']!r}"


def test_c18_golge_UC_HAL_ayri_cumle(sandbox_state, saat):
    """"tablo yok" bir KOPUKLUK, "atr None" MEŞRU bir ölçümsüzlüktür. Tek cümleye katlanırsa
    operatör gölge defterinde bir kabloyu kopmuş göremezdi."""
    plan = _plan()
    _kitap(sandbox_state, entry_law={plan["id"]: {"atr": None, "limit": 106.05}})
    satir = intraday_shadow.record(plan, _bar(o=100.0), _SIMDI)

    assert satir["atr"] is None and "var ama" in satir["atr_kaynak"], \
        f"'satır var, ATR None' hâli 'satır yok' ile aynı cümleye katlandı: {satir['atr_kaynak']!r}"
    assert "satır YOK" not in satir["atr_kaynak"], f"yanlış cümle: {satir['atr_kaynak']!r}"


def test_c18_golge_ATR_limiti_BAGLAR_kacan_dolum_gorunur(sandbox_state, saat, monkeypatch):
    """POZİTİF KONTROL + ASIL BULGU: dar ATR'de gölge artık canlının REDDEDECEĞİ dolumu YAZMIYOR.

    Aynı bar iki kez ölçülür: (a) yan tabloda dar bir ATR var → limit ATR bacağıyla kurulur ve
    açılış onun ÜSTÜNDE kalır → `blocked` + `red_nedeni=entry_missed_limit`; (b) tablo boş →
    yalnız yüzde tavanı → `would_submit`. Eski kod (b)'yi HER İKİ hâlde de yazıyordu.

    MEKANİZMA: ölçülen şey, yan tablodaki ATR'nin gölgenin dolum kararını GERÇEKTEN değiştirmesidir
    (kablo canlı mı). Yasa kaynağı bu yüzden kart varsayılanına sabitlenir — yürürlükteki 100·ATR/%4
    yasasında iki limit AYNI sayıdır, iki dal ayrışmaz ve kablonun kopması test edilemez olurdu."""
    plan = _plan()
    _asil = BR.entry_law
    monkeypatch.setattr(BR, "entry_law", lambda override=None: _asil(override or KART_YASASI))
    yasa = BR.entry_law()
    dar_atr = 0.2                                   # 0,5·0,2 = 0,10 < %1·105 = 1,05
    dar_limit = BR.entry_limit_price(plan["entry_trigger"], dar_atr, yasa)
    genis_limit = BR.entry_limit_price(plan["entry_trigger"], None, yasa)
    assert dar_limit < genis_limit, "kurgu bozuk: dar ATR limiti daraltmıyor"
    acilis = (dar_limit + genis_limit) / 2.0        # İKİ limitin ARASINDA açan bar

    _kitap(sandbox_state, entry_law={plan["id"]: {"atr": dar_atr, "limit": dar_limit}})
    dar_satir = intraday_shadow.record(plan, _bar(o=acilis, h=acilis + 5, l=acilis - 1), _SIMDI)

    intraday_shadow.reset_dedup()
    store.write_jsonl(intraday_shadow.ORDERS_FILE, [])       # dedup defteri de sıfırlanır
    _kitap(sandbox_state, entry_law={})
    genis_satir = intraday_shadow.record(plan, _bar(o=acilis, h=acilis + 5, l=acilis - 1), _SIMDI)

    assert dar_satir["status"] == "blocked:broker_kurali", \
        f"ATR limiti bağlamadı — gölge hâlâ iyimser dolum yazıyor ({dar_satir['status']})"
    assert dar_satir["red_nedeni"] == BR.EV_MISSED_LIMIT, \
        f"kaçan dolumun SINIFI satırda yok ({dar_satir['red_nedeni']!r}) — teşhis yutuldu"
    assert genis_satir["status"] == "would_submit", \
        "ATR'siz dalda da bloklandı — pozitif kontrol çürük, test farkı ölçmüyor"


# =================================================================================================
# YASA 6/a — `entry_rejects`in ÜRETİM okuyucusu (run.replay_seed özeti)
# =================================================================================================
def _replay_seed_konsolu(monkeypatch, sonuc: backtest.BacktestResult) -> str:
    """`replay_seed`i sandbox'ta koştur, konsol çıktısını topla.

    KAPSAM (beyanlı): `dataset.load` ve son gün `loop.daily_cycle` yamalanır — ölçülen şey ret
    sayacının BASILIP BASILMADIĞIDIR, veri hattı ya da canlı döngü değil."""
    yazilan: list = []
    monkeypatch.setattr(run.console, "print", lambda *a, **k: yazilan.append(" ".join(str(x) for x in a)))
    monkeypatch.setattr(run.dataset, "load", lambda *a, **k: ({}, None))
    monkeypatch.setattr(run.backtest, "replay", lambda *a, **k: sonuc)
    monkeypatch.setattr(run.loop, "daily_cycle", lambda *a, **k: None)
    monkeypatch.setattr(run, "_reset_book_to", lambda *a, **k: {})
    run.replay_seed("2026-01-01", "2026-06-30")
    return "\n".join(yazilan)


def _sonuc(**kw) -> backtest.BacktestResult:
    return backtest.BacktestResult(trades=[], equity=[("2026-06-30", 100_000.0)], params={},
                                   start="2026-01-01", end="2026-06-30", **kw)


def test_yasa6_replay_ozeti_entry_missed_limit_BASAR(sandbox_state, monkeypatch):
    """SIFIR DA BASILIR: "ölçüldü ve sıfır" bir bilgidir; basılmayan sayaç ölçülmemiş sayaçtır."""
    cikti = _replay_seed_konsolu(monkeypatch, _sonuc(entry_rejects={}))
    assert BR.EV_MISSED_LIMIT in cikti, \
        f"replay özeti `{BR.EV_MISSED_LIMIT}` satırını basmadı — sayacın ÜRETİM okuyucusu yok:\n{cikti}"
    assert f"{BR.EV_MISSED_LIMIT}=0" in cikti, f"sıfır ret 'sıfır' diye yazılmadı:\n{cikti}"


def test_yasa6_replay_ozeti_SAYIYI_ve_diger_siniflari_tasir(sandbox_state, monkeypatch):
    """POZİTİF KONTROL: sayı gerçekten sayaçtan gelir (sabit metin değil) ve diğer ret sınıfları da
    görünür — `max_chase`/`open_below_stop` de kaçan dolumlardır."""
    cikti = _replay_seed_konsolu(monkeypatch, _sonuc(
        entry_rejects={BR.EV_MISSED_LIMIT: 37, "max_chase": 4}))
    assert f"{BR.EV_MISSED_LIMIT}=37" in cikti, f"sayaç değeri basılmadı:\n{cikti}"
    assert "max_chase=4" in cikti, f"diğer ret sınıfları düşürüldü:\n{cikti}"


def test_yasa6_replay_ozeti_OLCULMEMIS_sayaci_ayri_soyler(sandbox_state, monkeypatch):
    """UYDURMA YASAĞI'nın ikiz maddesi: None ("hiç ölçülmedi") {} ("ölçüldü, sıfır") DEĞİLDİR."""
    cikti = _replay_seed_konsolu(monkeypatch, _sonuc(entry_rejects=None))
    assert "ÖLÇÜLEMEDİ" in cikti, f"ölçülmemiş sayaç 0 gibi sunuldu:\n{cikti}"
    assert f"{BR.EV_MISSED_LIMIT}=0" not in cikti, \
        f"None sayaç sıfır diye basıldı — uydurma:\n{cikti}"


# =================================================================================================
# YASA 6/b — `measure_failed` akıbetinin OKUNABİLİR cümlesi (nous_eval._akibet)
# =================================================================================================
def _oneri(**kw) -> dict:
    p = {"hafta": "2026-W30", "alan": "mekanizma", "oneri": "x", "sekil": "parametre",
         "kuyruk": "evet", "kuyruk_id": "Q-1"}
    p.update(kw)
    return p


def test_c14_akibet_measure_failed_NEDENI_basar():
    """DAVRANIŞ: özel dal + `neden` alanı. Eskiden genel dala düşüyordu ("kuyruk durumu:
    measure_failed") ve beyin bir sonraki haftanın önerisini değiştirecek TEK bilgiyi görmüyordu."""
    kuyruk = {"Q-1": {"id": "Q-1", "status": "measure_failed",
                      "neden": "ölçüm süreci ÖLÜ (pid yoklaması ESRCH)"}}

    cumle = nous_eval._akibet(_oneri(), kuyruk)

    assert "ÖLÇÜM DÜŞTÜ" in cumle, f"özel dal yok, genel dala düşüyor: {cumle!r}"
    assert "ESRCH" in cumle, f"`neden` alanı cümleye girmiyor: {cumle!r}"
    assert "kuyruk durumu:" not in cumle, f"hâlâ genel dal metni: {cumle!r}"


def test_c14_akibet_measure_failed_NEDEN_YOKSA_uydurmaz():
    """Damgayı basan taraf gerekçe yazmamışsa 'boş' DENİR — uydurulmuş bir sebep, beynin bir sonraki
    önerisini yanlış yöne çevirirdi."""
    cumle = nous_eval._akibet(_oneri(), {"Q-1": {"id": "Q-1", "status": "measure_failed"}})

    assert "ÖLÇÜM DÜŞTÜ" in cumle and "BOŞ" in cumle, f"boş neden dürüstçe söylenmiyor: {cumle!r}"


def test_c14_akibet_DIGER_durumlar_bozulmadi():
    """POZİTİF KONTROL: yeni dal komşularını yutmadı (measured/measuring/pending hâlâ kendi
    cümlelerini veriyor) ve BİLİNMEYEN bir durum hâlâ genel dala düşüyor."""
    for st, iz in (("measured", "ÖLÇÜLDÜ"), ("measuring", "ÖLÇÜLÜYOR"), ("pending", "SIRADA")):
        c = nous_eval._akibet(_oneri(), {"Q-1": {"id": "Q-1", "status": st, "result": {"a": 1}}})
        assert iz in c, f"{st} dalı bozuldu: {c!r}"
    bilinmeyen = nous_eval._akibet(_oneri(), {"Q-1": {"id": "Q-1", "status": "yepyeni_durum"}})
    assert "kuyruk durumu: yepyeni_durum" in bilinmeyen, \
        f"bilinmeyen durum sessizce 'ölçüm düştü' sayıldı: {bilinmeyen!r}"


def test_c14_akibet_measure_failed_OKUYUCUSU_kaynakta_var():
    """FAZ İDDİASI: dal `_akibet`in İÇİNDE yaşar — biri onu bir sarmalayıcıya taşırsa davranış
    testleri yeşil kalır ama H1'in prompt yolu (onceki_akibet → _akibet) yine kör kalırdı."""
    kaynak = inspect.getsource(nous_eval._akibet)
    assert 'st == "measure_failed"' in kaynak, "`measure_failed` dalı `_akibet` gövdesinde değil"
    assert "neden" in kaynak, "`neden` alanı okunmuyor"
