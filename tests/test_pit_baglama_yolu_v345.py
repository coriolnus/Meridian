"""v345 — PIT arşiv DİKİŞİ: `strategy.evaluate_episodic_pivot` / `evaluate_pead` param yolu.

EDG-2026-062 Görev 2. Görev 1 `meridian/earnings_pit.py`i (üç durumlu PIT çapası) yazdı; bu tur
onu iki sinyal üreticisine BAĞLAR — ve bağlamanın tek kabul edilebilir biçimi PARAMDIR:
`params["earnings.pit_arsiv"]` yokken canlı yol BİREBİR eskisidir. Emsal aynı dosyada:
`scan_entry`in `entry.armed_extra` paramı ("param üzerinden aktığı için canlı döngüyle yarışmaz").

BU DOSYANIN ÖLÇTÜĞÜ ŞEY BİR DEĞER DEĞİL, BİR AYRIMDIR — hangi kaynağın SORULDUĞU. Bir dönüş
değerini karşılaştırmak bunu ölçemez: iki kaynak da aynı gün aynı cevabı verebilir ve çivi,
dikiş TAMAMEN yanlış tarafa bağlanmışken de yeşil kalırdı. Bu yüzden ayrım YASAKLI ÇAĞRIYLA
ölçülür: sorulmaması gereken kaynak, sorulursa PATLAYAN bir sahteyle değiştirilir (`_patlayici`).
Yani çivi "doğru cevabı aldın mı" değil, "kime sordun" der.

NUMARA KİMLİKTİR: `v345` bu tur BOŞTU (`ls tests/ | grep v345` → hiçbir eşleşme, 2026-08-31).

SENTETİK ARŞİV `tests/test_earnings_pit_v344.py`TEN İTHAL EDİLİR (`arsiv_yaz`), kopyalanmaz:
CSV başlığı ve ufuk-çapası kuralı TEK gerçektir ve iki dosyada ayrışırsa bu dosyanın çivileri
sessizce hep-None üzerinden geçerdi (tek-kaynak yasası; `tests.conftest.make_bars` emsali).

`earnings_pit._SAYAC` MODÜL-DÜZEYİ DURUMDUR. Görev 2'de `tests/conftest._MODUL_DURUMLARI` kaydında
YOKTU ve sızıntı yalnız iki dosyanın (v344 + bu dosya) kendi autouse fikstürüyle kapalıydı. GÖREV
3'TE SINIF BÜYÜDÜ: `backtest.replay` ve `cf_backfill.run` sayacı ÜRETİM yolundan artırıyor, yani
`replay`/`run` çağıran her test dosyası onu kirletiyor ve hiçbiri temizlemekle yükümlü değil.
Kayıt Rol-1 kararıyla açıldı (`_MODUL_DURUMLARI` içinde `(_epit_mod, "_SAYAC")`) ve BURADA ÇİVİLİ:
`test_conftest_kaydi_pit_sayacini_YERINDE_sifirlar` — kayıt silinirse çivi kırmızıya döner.

BÖLÜM 2 (Görev 3) TARİHSEL ÇAĞIRANLARI ölçer: `backtest.replay` ve `cf_backfill` param sevkini
kurar mı, sayaç RAPORA girer mi, ve parametre cf'nin İKİ tarama koluna da ulaşır mı. Barlar ve
arşiv SENTETİKTİR — bu dosya `backtest`/`cf_backfill`i gerçek veriyle koşturmaz (kapsam: yol,
veri değil).
"""
from __future__ import annotations

import datetime as dt

import pytest

import meridian.backtest as backtest
import meridian.cf_backfill as cf_backfill
import meridian.config as config
import meridian.earnings as earn
import meridian.earnings_pit as earnings_pit
import meridian.strategy as strat
from tests.conftest import make_bars
from tests.test_earnings_pit_v344 import arsiv_yaz
from tests.test_pead_v93 import _pead_bars

PIT_PARAM = {"earnings.pit_arsiv": True}


@pytest.fixture(autouse=True)
def _pit_temiz():
    """Sayaç ve arşiv önbelleği hem ÖNCE hem SONRA sıfırlanır (v344 emsali): sayaç okuyan her çivi
    kendi çağrılarını sayar, ve bu dosyadan çıkan artık komşu dosyalara sızmaz."""
    earnings_pit.clear_cache()
    earnings_pit.sayac_sifirla()
    yield
    earnings_pit.clear_cache()
    earnings_pit.sayac_sifirla()


def _gun(temel: str, kaydir: int) -> str:
    return (dt.date.fromisoformat(temel) + dt.timedelta(days=kaydir)).isoformat()


def _ep_bars():
    """`test_decision_v3::test_episodic_pivot_requires_earnings_anchor` geometrisi: %8 boşluk +
    4× hacim. Çapa DIŞINDA her koşul sağlanır, yani dönüşü belirleyen TEK şey çapadır."""
    df = make_bars(120, seed=3, trend=0.002)
    df.loc[df.index[-1], "open"] = df["close"].iloc[-2] * 1.08
    df.loc[df.index[-1], "close"] = df["close"].iloc[-2] * 1.09
    df.loc[df.index[-1], "high"] = df["close"].iloc[-2] * 1.10
    df.loc[df.index[-1], "volume"] = df["volume"].iloc[-51:-1].mean() * 4.0
    return df, str(df["date"].iloc[-1])[:10]


def _arsiv(tmp_path, monkeypatch, satirlar, ad: str = "arsiv.csv"):
    """Sentetik PIT arşivini yazar ve `ARSIV_YOLU`nu ona çevirir (v344'ün `sentetik` fikstürünün
    bu dosyaya taşınmış hâli — ufuk çapası `arsiv_yaz` içinden gelir).

    `ad` NEDEN VAR: TEK bir çivi İKİ farklı arşivle iki koşum yapabiliyor (kapsam-içi/kapsam-dışı
    kıyası). Aynı dosyayı yeniden yazmak yeterli DEĞİLDİR — `earnings_pit`in önbellek anahtarı
    (yol, mtime)'dır ve iki yazım aynı mtime damgasına düşerse ikinci koşum sessizce BİRİNCİ
    arşivi okurdu; çivi o hâlde hiçbir şey ölçmezdi. Ayrı dosya = ayrı anahtar, garantili."""
    yol = arsiv_yaz(tmp_path, satirlar, ad=ad)
    monkeypatch.setattr(earnings_pit, "ARSIV_YOLU", yol)
    earnings_pit.clear_cache()
    return yol


def _patlayici(ad: str):
    """Sorulmaması gereken kaynağın yerine geçen sahte: çağrılırsa çiviyi ADIYLA düşürür."""
    def _f(*a, **k):
        raise AssertionError(f"{ad} ÇAĞRILDI — dikiş yanlış tarafa bağlı (çağrı: {a!r} {k!r})")
    return _f


def _canli_capa(sandbox_state, ticker: str, tarih: str):
    (sandbox_state / "earnings.csv").write_text(f"ticker,date\n{ticker},{tarih}\n")
    earn.clear_cache()


# ---------------------------------------------------------------------------------------------
# 1) PARAM YOKKEN — CANLI YOL BİREBİR AYNI (kartın kill maddesi)
# ---------------------------------------------------------------------------------------------
def test_ep_param_yokken_pit_arsivi_hic_sorulmaz(sandbox_state, tmp_path, monkeypatch):
    """Param YOK → `earnings_pit` HİÇ sorulmaz; hüküm canlı `earnings.days_since_report`ındır.

    ÇİFT KANIT: (a) PIT çapası patlayıcıdır — çağrılsaydı test ADIYLA düşerdi; (b) arşiv ayrıca
    TST hakkında SESSİZDİR (yalnız ufuk çapası var), yani dikiş sızsaydı cevap None'a düşer ve
    kurulum ateşlemezdi. Sinyalin ateşlemesi, sorulan kaynağın canlı defter olduğunu gösterir."""
    df, son = _ep_bars()
    _arsiv(tmp_path, monkeypatch, [])
    monkeypatch.setattr(earnings_pit, "days_since_report_pit", _patlayici("days_since_report_pit"))
    _canli_capa(sandbox_state, "TST", son)
    sig = strat.evaluate_episodic_pivot(df, {}, 80, "TST")
    assert sig is not None and sig.setup == "episodic_pivot"
    assert earnings_pit.sayac_oku() == {"true": 0, "false": 0, "olculemedi": 0}


def test_pead_param_yokken_pit_arsivi_hic_sorulmaz(sandbox_state, tmp_path, monkeypatch):
    """`evaluate_pead` simetrisi — aynı ayrım, `max_days=watch_days` penceresiyle."""
    df, rep = _pead_bars()
    _arsiv(tmp_path, monkeypatch, [])
    monkeypatch.setattr(earnings_pit, "days_since_report_pit", _patlayici("days_since_report_pit"))
    _canli_capa(sandbox_state, "T", rep)
    sig = strat.evaluate_pead(df, {}, 95, "T")
    assert sig is not None and sig.setup == "pead"
    assert earnings_pit.sayac_oku() == {"true": 0, "false": 0, "olculemedi": 0}


def test_ep_param_yokken_canli_false_kurulumu_dusurur(sandbox_state, tmp_path, monkeypatch):
    """Canlı yolun NEGATİF ucu da param'sız kalır: canlı defter boşken kurulum yok — ve bu
    dönüş PIT arşivinden GELMEZ (patlayıcı hâlâ yerinde, sayaç sıfır)."""
    df, _son = _ep_bars()
    _arsiv(tmp_path, monkeypatch, [])
    monkeypatch.setattr(earnings_pit, "days_since_report_pit", _patlayici("days_since_report_pit"))
    earn.clear_cache()                                      # sandbox'ta earnings.csv YOK
    assert strat.evaluate_episodic_pivot(df, {}, 80, "TST") is None
    assert earnings_pit.sayac_oku() == {"true": 0, "false": 0, "olculemedi": 0}


# ---------------------------------------------------------------------------------------------
# 2) PARAM VARKEN — PIT'SİZ CANLI KAYNAK HİÇ SORULMAZ (simetrik yasak)
# ---------------------------------------------------------------------------------------------
def test_ep_param_varken_canli_earnings_hic_sorulmaz(sandbox_state, tmp_path, monkeypatch):
    """Param VAR → PIT'siz `earnings.days_since_report` HİÇ çağrılmaz (yasanın bütün amacı bu:
    tarihsel yeniden yürütmede o kaynak SIFIR TOLERANSTIR). Çapa PIT arşivinden gelir ve
    kurulum ateşler — yani yasak yalnız 'çağırmadım' değil, 'doğru kaynağı sordum'la kanıtlı."""
    df, son = _ep_bars()
    _arsiv(tmp_path, monkeypatch, [("TST", _gun(son, -1), _gun(son, -1))])
    monkeypatch.setattr(earn, "days_since_report", _patlayici("earnings.days_since_report"))
    sig = strat.evaluate_episodic_pivot(df, dict(PIT_PARAM), 80, "TST")
    assert sig is not None and sig.setup == "episodic_pivot"
    assert earnings_pit.sayac_oku() == {"true": 1, "false": 0, "olculemedi": 0}


def test_pead_param_varken_canli_earnings_hic_sorulmaz(sandbox_state, tmp_path, monkeypatch):
    """`evaluate_pead` simetrisi. PENCERE DE ÖLÇÜLÜR: rapor son barın 30 gün ÖNCESİNDEDİR —
    `max_days=2` ile None/False olurdu, `watch_days` (35) ile True. Yani dikiş pencereyi de
    doğru taşıyor."""
    df, _rep = _pead_bars()
    son = str(df["date"].iloc[-1])[:10]
    _arsiv(tmp_path, monkeypatch, [("T", _gun(son, -30), _gun(son, -30))])
    monkeypatch.setattr(earn, "days_since_report", _patlayici("earnings.days_since_report"))
    sig = strat.evaluate_pead(df, dict(PIT_PARAM), 95, "T")
    assert sig is not None and sig.setup == "pead"
    assert earnings_pit.sayac_oku() == {"true": 1, "false": 0, "olculemedi": 0}


# ---------------------------------------------------------------------------------------------
# 3) ÜÇÜNCÜ DURUM — None ve False AYNI KARARI verir, AYRI SAYILIR
# ---------------------------------------------------------------------------------------------
def test_ep_pit_none_kurulumu_dusurur_ve_olculemedi_sayar(sandbox_state, tmp_path, monkeypatch):
    """None (sembol kapsam dışı) → kurulum YOK. Karar False'unkiyle AYNIDIR ve olması gereken de
    budur: çapası ölçülemeyen bir gün hakkında kurulum kurmak uydurmadır. AYRIM KARARDA DEĞİL
    SAYAÇTADIR — `olculemedi` payı bu dikişin KAPSAM ölçüsüdür (kart eşiği ≥%95 onu okur)."""
    df, _son = _ep_bars()
    _arsiv(tmp_path, monkeypatch, [("BASKA", "2020-03-10", "2020-03-10")])
    monkeypatch.setattr(earn, "days_since_report", _patlayici("earnings.days_since_report"))
    assert strat.evaluate_episodic_pivot(df, dict(PIT_PARAM), 80, "TST") is None
    assert earnings_pit.sayac_oku() == {"true": 0, "false": 0, "olculemedi": 1}


def test_ep_pit_false_kurulumu_dusurur_ve_false_sayar(sandbox_state, tmp_path, monkeypatch):
    """False (sembol VAR, ufuk İÇİNDE, eşleşen rapor yok) → kurulum YOK, `false` sayacı artar.
    Bir önceki çiviyle birlikte okunur: aynı karar, AYRI kova."""
    df, son = _ep_bars()
    _arsiv(tmp_path, monkeypatch, [("TST", _gun(son, -60), _gun(son, -60))])
    monkeypatch.setattr(earn, "days_since_report", _patlayici("earnings.days_since_report"))
    assert strat.evaluate_episodic_pivot(df, dict(PIT_PARAM), 80, "TST") is None
    assert earnings_pit.sayac_oku() == {"true": 0, "false": 1, "olculemedi": 0}


def test_pead_pit_none_kurulumu_dusurur_ve_olculemedi_sayar(sandbox_state, tmp_path, monkeypatch):
    """`evaluate_pead` simetrisi — üçüncü durum orada da kurulumu düşürür ve ayrı sayılır."""
    df, _rep = _pead_bars()
    _arsiv(tmp_path, monkeypatch, [("BASKA", "2020-03-10", "2020-03-10")])
    monkeypatch.setattr(earn, "days_since_report", _patlayici("earnings.days_since_report"))
    assert strat.evaluate_pead(df, dict(PIT_PARAM), 95, "T") is None
    assert earnings_pit.sayac_oku() == {"true": 0, "false": 0, "olculemedi": 1}


# ---------------------------------------------------------------------------------------------
# 4) SICAK YOL BÜTÇESİ — dikiş `arsiv_ufku()`nu ÇAĞIRMAZ (K-2), İKİ ÜRETİCİDE DE
# ---------------------------------------------------------------------------------------------
def _ep_kurulum():
    """(fn, bars, ticker, arşiv satırları, rs) — ateşleyen episodic_pivot senaryosu."""
    df, son = _ep_bars()
    return (strat.evaluate_episodic_pivot, df, "TST",
            [("TST", _gun(son, -1), _gun(son, -1))], 80)


def _pead_kurulum():
    """`evaluate_pead` ikizi — rapor son bardan 30 gün önce (`watch_days` penceresi)."""
    df, _rep = _pead_bars()
    son = str(df["date"].iloc[-1])[:10]
    return (strat.evaluate_pead, df, "T", [("T", _gun(son, -30), _gun(son, -30))], 95)


@pytest.mark.parametrize("kur", [_ep_kurulum, _pead_kurulum], ids=["episodic_pivot", "pead"])
def test_dikis_arsiv_ufkunu_dogrudan_cagirmaz(kur, sandbox_state, tmp_path, monkeypatch):
    """`arsiv_ufku()` O(n) TÜREV taşır (ölçüm 2026-08-31: 0,52 ms/çağrı; cf ölçeğinde dakikalar).
    Dikiş onu ÇAĞIRMAZ — yalnız `days_since_report_pit` çağırır, ufku o kendi içinde bir kez sorar.

    ÇİVİ SAYAR, YASAKLAMAZ: `days_since_report_pit` ufku kendi gövdesinde çağırdığı için toplam
    sıfır olamaz. Ölçülen şey, DİKİŞİN ek bir çağrı EKLEMEDİĞİDİR — çağrı başına en fazla bir.

    İKİ ÜRETİCİ DE ÖLÇÜLÜR (B-5, inceleme 2026-08-31): önceden yalnız `episodic_pivot` korunuyordu
    ve `evaluate_pead` dikişine fazladan bir `arsiv_ufku()` çağrısı eklense HİÇBİR çivi ötmezdi —
    simetrik bir dikişin tek taraflı çivisi, korunduğu sanılan yarıyı korumaz."""
    fn, df, ticker, satirlar, rs = kur()
    _arsiv(tmp_path, monkeypatch, satirlar)
    sayim = {"n": 0}
    gercek = earnings_pit.arsiv_ufku

    def _sayan(*a, **k):
        sayim["n"] += 1
        return gercek(*a, **k)

    monkeypatch.setattr(earnings_pit, "arsiv_ufku", _sayan)
    monkeypatch.setattr(earn, "days_since_report", _patlayici("earnings.days_since_report"))
    assert fn(df, dict(PIT_PARAM), rs, ticker) is not None
    assert sum(earnings_pit.sayac_oku().values()) == 1, "çapa tam bir kez sorulmalı"
    assert sayim["n"] == 1, f"dikiş fazladan ufuk çağırdı: {sayim['n']}"


# ---------------------------------------------------------------------------------------------
# 5) PARAM DOĞRULUK SÖZLEŞMESİ — falsy değer CANLI yola düşer (B-6)
# ---------------------------------------------------------------------------------------------
@pytest.mark.parametrize("deger", [False, None, 0, ""], ids=["False", "None", "sifir", "bos"])
def test_param_FALSY_ise_canli_yol_kullanilir(deger, sandbox_state, tmp_path, monkeypatch):
    """Anahtar `params.get(...)` ile DOĞRULUK olarak okunur, "var mı" diye DEĞİL. Yani
    `{"earnings.pit_arsiv": False}` PIT'i AÇMAZ — canlı yola düşer.

    NEDEN ÇİVİLİ: Görev 3 bu anahtarı `True` kuracak, ama bir yapılandırma katmanı onu `False`
    yazdığında beklenen davranış "PIT kapalı"dır. Sözleşme yazısız kalsaydı, `in params` biçimine
    masum görünen bir yeniden yazım (`if "earnings.pit_arsiv" in params`) `False`u SESSİZCE PIT'e
    çevirirdi — hiçbir şey kırılmadan çapanın KAYNAĞI değişirdi ve bu, tam olarak bu dosyanın
    ölçmek için var olduğu ayrımdır."""
    df, son = _ep_bars()
    _arsiv(tmp_path, monkeypatch, [])
    monkeypatch.setattr(earnings_pit, "days_since_report_pit", _patlayici("days_since_report_pit"))
    _canli_capa(sandbox_state, "TST", son)
    sig = strat.evaluate_episodic_pivot(df, {"earnings.pit_arsiv": deger}, 80, "TST")
    assert sig is not None and sig.setup == "episodic_pivot"
    assert earnings_pit.sayac_oku() == {"true": 0, "false": 0, "olculemedi": 0}


# =============================================================================================
# BÖLÜM 2 (Görev 3) — TARİHSEL ÇAĞIRANLAR: backtest.replay + cf_backfill
# =============================================================================================
# Bölüm 1 dikişin KENDİSİNİ ölçtü (hangi kaynağa soruluyor). Bu bölüm dikişin AÇILDIĞINI ölçer:
# tarihsel iki motor param sevkini kuruyor mu, ve davranış değişimi RAPORA giriyor mu (kart
# kill-list 4: "davranış değişimi raporsuz kalamaz"). Sayaç, bağlamanın tek gözlemlenebilir
# ürünüdür — sıfır kalırsa "PIT'e bağladık" cümlesi bir beyandır, ölçüm değil.
_REPLAY_BASLA, _REPLAY_BITIS = "2022-06-01", "2023-01-01"


def _replay_evreni(monkeypatch):
    """Sentetik replay evreni (`test_engine`in duman fikstürünün ikizi) — GERÇEK bar verisi YOK.
    SECTORS `monkeypatch.setitem` ile kurulur: doğrudan yazım ÜRETİM sözlüğünü kalıcı kirletir ve
    `conftest._no_production_global_mutation` testi ADIYLA düşürür (2026-07-22 vakası)."""
    from meridian.backtest import SECTORS
    for t in ("AAA", "BBB"):
        monkeypatch.setitem(SECTORS, t, "tech")
    idx = make_bars(300, seed=1, trend=0.0009)
    bars = {"AAA": make_bars(300, seed=2, breakout_at=240),
            "BBB": make_bars(300, seed=3, breakout_at=200)}
    return bars, idx


def _replay_kos(bars, idx):
    return backtest.replay(config.default_strategy()["params"], bars, idx, config.goal(),
                           _REPLAY_BASLA, _REPLAY_BITIS, strategy_version=1)


def _rapor_serisi(sym: str, adim: int = 7):
    """Replay penceresini KESİNTİSİZ kaplayan sentetik rapor serisi (`filed == report_date`).

    TEK SATIR YETMEZ VE BU ÖLÇÜLDÜ: replay her seansı taramaz (rejim/slot kapıları) — tek raporlu
    bir arşivle 42 çağrının hiçbiri pencereye düşmedi ve "True görünür mü" çivisi True ÜRETMEDEN
    kırmızıya döndü, yani ölçmek istediği şeyi değil fikstürün şansını ölçüyordu. `adim` gün
    aralıklı seri, `pead.watch_days` (35) penceresinden dar olduğu için HANGİ seans taranırsa
    taransın çapa vardır. Seri sentetiktir: gerçek arşivin kapsaması bu çivinin konusu değildir."""
    ilk = dt.date.fromisoformat(_REPLAY_BASLA) - dt.timedelta(days=adim)
    son = dt.date.fromisoformat(_REPLAY_BITIS)
    gunler, g = [], ilk
    while g <= son:
        gunler.append((sym, g.isoformat(), g.isoformat()))
        g += dt.timedelta(days=adim)
    return gunler


def _cf_dunyasi(sandbox_state, monkeypatch):
    """`cf_backfill.run` için sentetik dünya — `test_cf_backfill_v14`ün fikstürünün ikizi
    (ağ yok, gerçek bar CSV'si yok: sandbox `bars/` altına sentetik seriler yazılır)."""
    import shutil
    from pathlib import Path
    from meridian.adapters import data as _data
    from meridian.backtest import SECTORS
    repo = Path(__file__).resolve().parent.parent / "state"
    for f in ("goal.yaml", "bounds.yaml", "strategy.yaml"):
        shutil.copy2(repo / f, sandbox_state / f)
    config.goal.cache_clear()
    config.bounds.cache_clear()
    monkeypatch.setattr(_data, "REPLAY_UNIVERSE", ["SPY", "AAA"])
    monkeypatch.setattr(_data, "validate_bars", lambda df, t: (True, []))   # veri kapısı başka yerde çivili
    monkeypatch.setitem(SECTORS, "AAA", "tech")
    for t, seed, bo in (("SPY", 1, None), ("AAA", 2, 330)):
        make_bars(n=340, seed=seed, breakout_at=bo).to_csv(config.BARS / f"{t.lower()}.csv", index=False)


# ---------------------------------------------------------------------------------------------
# 6) backtest.replay — sevk kuruldu, sayaç RAPORDA
# ---------------------------------------------------------------------------------------------
def test_replay_earnings_gate_PIT_ARSIV_blogunu_tasir(sandbox_state, tmp_path, monkeypatch):
    """`BacktestResult.earnings_gate` üç kovalı `pit_arsiv` bloğunu taşır VE blok DOLUDUR.

    TOPLAMIN SIFIRDAN BÜYÜK OLMASI ASIL ÖLÇÜMDÜR, biçim değil: sayaç yalnız
    `days_since_report_pit` çağrıldığında artar, o da yalnız `params["earnings.pit_arsiv"]`
    doğruyken çağrılır. Yani bu satır "replay'in `eff`i dikişe ulaştı" cümlesinin kanıtıdır —
    sevk düşerse toplam sessizce sıfıra iner ve blok BOŞ değil, YALAN olurdu (üç sıfır, "hiç
    sorulmadı" ile "hep ölçülemedi"yi aynı piksele koyar)."""
    _arsiv(tmp_path, monkeypatch, [("AAA", "2022-07-01", "2022-07-01")])
    bars, idx = _replay_evreni(monkeypatch)
    res = _replay_kos(bars, idx)
    pit = res.earnings_gate["pit_arsiv"]
    assert set(pit) == {"true", "false", "olculemedi"}
    assert all(isinstance(v, int) for v in pit.values())
    assert sum(pit.values()) > 0, ("replay HİÇ PIT çapası sormadı — `eff[\"earnings.pit_arsiv\"]` "
                                   "sevki dikişe ulaşmıyor (çivi aksi hâlde boş geçerdi)")
    # "ESKİ SAYAÇLAR EZİLMEDİ" İDDİASI BURADAN KALDIRILDI (inceleme 2026-08-31, K6). Yazılı
    # hâli `get("plan", 0) == get("olculemedi_replay", 0)` idi ve bu fikstürde hiçbir plan
    # kapıya girmediği için `0 == 0`a düşüyordu: iddia gibi duran, hiçbir şey ölçmeyen bir satır.
    # Süs bir assertion, yokluğundan beterdir — okuyucuya korunmayan bir şeyin korunduğunu söyler.
    # Karartma sayaçlarının taşındığını ölçen çivi ZATEN var ve doğru yerde:
    # `test_wpd_takvim_kapisi_v184::test_replay_sayaci_sonuca_baglanir`.


def test_replay_kosum_basinda_PIT_sayacini_sifirlar(sandbox_state, tmp_path, monkeypatch):
    """`_SAYAC` süreç-içi ve monotondur: koşum başında sıfırlanmazsa rapor, aynı süreçte daha önce
    koşmuş her taramanın çağrılarını da taşır — yani "bu koşumun kapsaması" diye okunan sayı
    sürecin ÖMRÜNÜ ölçerdi. Önceki koşumun artığı taklit edilir; rapor onu TAŞIMAMALIDIR."""
    _arsiv(tmp_path, monkeypatch, [("AAA", "2022-07-01", "2022-07-01")])
    bars, idx = _replay_evreni(monkeypatch)
    earnings_pit._SAYAC["olculemedi"] = 5000            # "önceki koşumun artığı"
    pit = _replay_kos(bars, idx).earnings_gate["pit_arsiv"]
    assert pit["olculemedi"] < 5000, f"artık taşındı — koşum başı sıfırlama yok: {pit}"
    assert sum(pit.values()) > 0, "sıfırlama okumadan SONRAYA kaymış olabilir (rapor boş)"


def test_replay_raporu_TRUE_sayisini_GORUNUR_kilar(sandbox_state, tmp_path, monkeypatch):
    """KİLL-LIST 4 (karttan): davranış değişimi raporsuz kalamaz — True sayısı GÖRÜNÜR olmalı.

    ÇİVİ DEĞERİ SABİTLEMEZ ve sabitlememelidir: arşiv aylık tazelenir, bugünkü ölçülü taban
    (gerçek evren + gerçek arşiv, replay'de True=0) yarın değişebilir ve o değişim bir ARIZA
    değildir. Ölçülen şey RAPORUN AYIRT EDİCİ GÜCÜdür: aynı barlar, aynı pencere, tek fark
    arşivin sembolü kapsayıp kapsamaması → rapor iki durumu AYIRIYOR mu?"""
    bars, idx = _replay_evreni(monkeypatch)
    _arsiv(tmp_path, monkeypatch, _rapor_serisi("ZZZ"), ad="kapsam_disi.csv")
    yok = _replay_kos(bars, idx).earnings_gate["pit_arsiv"]
    _arsiv(tmp_path, monkeypatch, _rapor_serisi("AAA"), ad="kapsam_ici.csv")
    var = _replay_kos(bars, idx).earnings_gate["pit_arsiv"]
    assert yok["true"] == 0 and yok["false"] == 0, f"kapsam dışı sembol False/True saydı: {yok}"
    assert var["true"] > 0, f"arşiv AAA'yı kapsıyor ama rapor tek True göstermiyor: {var}"
    # ÜÇÜNCÜ DURUM AYRI KOVADA KALIR: AAA kapsama girince `olculemedi` payı DÜŞER (BBB'ninki kalır).
    assert var["olculemedi"] < yok["olculemedi"]


# ---------------------------------------------------------------------------------------------
# 7) cf_backfill — aynı sevk, aynı rapor; ve parametre İKİ tarama koluna da ulaşır
# ---------------------------------------------------------------------------------------------
_CF_ARSIV = [("AAA", "2022-08-15", "2022-08-15")]
_CF_PENCERE = {"start": "2022-08-01", "end": "2022-10-01", "progress_every": 0}


def test_cf_backfill_ciktisi_PIT_ARSIV_blogunu_tasir(sandbox_state, tmp_path, monkeypatch):
    """`run()` dönüşünün (ve `cf_backfill_done` olayının) `earnings_gate`i aynı üç kovayı taşır.
    Kardeş motorun raporu ayrışamaz: cf defteri de tarihseldir ve aynı soruyu cevaplamalıdır.

    BU ÇİVİ YALNIZ BİÇİM ÖLÇER ve bu bilinçlidir: bloğun DOLU olduğunu ölçen çivi ayrıdır
    (`test_cf_taramasi_KAZANC_CAPASINA_ULASIR`), sevkin İKİ tarama koluna da ulaştığını ölçen de
    ayrıdır (`test_cf_param_IKI_scan_all_cagrisina_da_ulasir`) — bir kaba üç iş yaptırmak,
    hangisinin hangi sebeple kırıldığını okunmaz kılardı.

    TARİHÇE: 2026-09-02'ye kadar burada toplam SIFIRDI ve bu bir ARIZA DEĞİL ölçülmüş bir sınırdı
    (tarama kuyruğu `date` taşımıyordu). EDG-2026-068 kartıyla kuyruk kardeş `backtest.replay`
    biçimine döndü; sıfır beyanı kapandı, bu çivinin yüklemi ise DEĞİŞMEDİ."""
    _arsiv(tmp_path, monkeypatch, _CF_ARSIV)
    _cf_dunyasi(sandbox_state, monkeypatch)
    out = cf_backfill.run(**_CF_PENCERE)
    assert out["sessions"] > 0, "fikstür hiç seans işlemedi — çivi hiçbir şey kanıtlamaz"
    pit = out["earnings_gate"]["pit_arsiv"]
    assert set(pit) == {"true", "false", "olculemedi"}
    assert all(isinstance(v, int) for v in pit.values())
    # Kardeşiyle aynı gerekçeyle (K6) burada da süs bir eşitlik YOK: karartma sayaçlarının
    # `out`a taşındığını `test_wpd_kardes_pit_v185::test_cf_backfill_sayaci_SONUCA_baglanir`
    # ölçüyor, ve o çivi fikstürün plan üretip üretmemesine bağlı değil.


def test_cf_backfill_kosum_basinda_PIT_sayacini_sifirlar(sandbox_state, tmp_path, monkeypatch):
    """`backtest.replay` ile AYNI gerekçe (kardeş simetrisi): sıfırlanmayan sayaç, cf raporunu
    aynı süreçte daha önce koşmuş her taramanın artığıyla şişirir — "bu koşumun kapsaması" diye
    okunan sayı sürecin ÖMRÜNÜ ölçerdi."""
    _arsiv(tmp_path, monkeypatch, _CF_ARSIV)
    _cf_dunyasi(sandbox_state, monkeypatch)
    earnings_pit._SAYAC["olculemedi"] = 5000            # "önceki koşumun artığı"
    out = cf_backfill.run(**_CF_PENCERE)
    # HÜKÜM KARDEŞİYLE AYNI YÜKLEMDE (`< 5000`), `== {0,0,0}` DEĞİL (inceleme 2026-08-31, K5):
    # toplam-sıfır bu çivinin konusu DEĞİL, bir alttaki çivinin konusudur. Eşitlik yazılsaydı,
    # cf'nin veri kuyruğu düzeldiği gün bu çivi "koşum başı sıfırlama yok" diyerek kırmızıya
    # dönerdi — sıfırlama pekâlâ çalışırken YANLIŞ TEŞHİS koyan bir çivi, teşhis koymayandan
    # beterdir (aranan kusur, gösterdiği yerde değildir).
    # O GÜN GELDİ (2026-09-02, EDG-2026-068): kuyruk `date` taşımaya başladı, toplam sıfır olmaktan
    # çıktı ve bu yüklem HİÇ DEĞİŞMEDEN yeşil kaldı — K5 incelemesinin öngörüsü ÖLÇÜLDÜ.
    assert out["earnings_gate"]["pit_arsiv"]["olculemedi"] < 5000, \
        "artık taşındı — koşum başı sıfırlama yok"


def test_cf_taramasi_KAZANC_CAPASINA_ULASIR(sandbox_state, tmp_path, monkeypatch):
    """cf tarama kuyruğu `date`i SÜTUN olarak taşır → kazanç çapası GERÇEKTEN sorulur.

    BEYANLI-SIFIR DÖNEMİ KAPANDI — EDG-2026-068 kartıyla, 2026-09-02; eski kayıt tarihçe.

    TARİHÇE (`test_cf_taramasi_bugun_KAZANC_CAPASINA_ULASAMAZ`, 2026-08-31 Görev 3'te ölçülmüştü):
    `_plans_for_session` kuyruğu `dfp.loc[:d].reset_index(drop=True)` ile kuruyordu — `date`
    İNDEKSTİ ve `drop=True` onu SÜTUNA çevirmeden ATIYORDU; kardeş `backtest.replay` ise aynı
    satırı drop'suz yazıyordu. İki kazanç-çapalı üretici çapayı `bars["date"]`in son gününden
    okur (`evaluate_pead` → `"date" not in bars.columns`; `evaluate_episodic_pivot` →
    `last_date is None`), yani ikisi de ÇAPADAN ÖNCE None dönüyordu: PIT sevki doğru kuruluyken
    çapa hiç sorulmuyor, cf'de `pit_arsiv` {0,0,0} kalıyordu. O kayıt "kuyruk bir gün `date`
    taşımaya başlarsa bu bir KART kararıdır, sessizce alınacak bir yan etki değil" diyordu —
    karar EDG-2026-068 ile alındı, kuyruk kardeşiyle TEK biçime döndü.

    ÖLÇÜLEN İKİ ŞEY AYRI KATMANDIR ve ikisi birden gerekir:
      (a) KUYRUK BİÇİMİ — `scan_all`a giden HER çerçeve `date` taşır (`all`, "biri taşıdı" değil).
          cf seansta İKİ kez tarar (karar kolu `eff` + near-miss `rx`); tek kolun düzelmesi
          ötekini sessizce eski biçimde bırakırdı ve fark hiçbir çıktıda görünmezdi.
      (b) ÇAPANIN SORULDUĞU — biçim doğruyken de çapa erişilemez kalabilir. Kartın kill maddesi
          bunu adıyla yazar: "`date` sütunu varken `pit_arsiv` {0,0,0} kalırsa çapa hâlâ
          erişilemez, hipotez çürük". Sayaç, dikişin ucunun ARŞİVE vardığının tek gözlemlenebilir
          ürünüdür; biçim çivisi tek başına onu ölçemez.

    POZİTİF KONTROL YOL-TUTARLIDIR (kart; vaka 2026-08-25): çapa doğrudan bir `evaluate_*`
    çağrısıyla değil, `cf_backfill.run` → `_plans_for_session` PORTFÖY YOLUNDAN geçilerek
    sorulur — tek-enstrümanlı PK portföy-yolu hatalarına kördür. Fikstür arşivi (`_CF_ARSIV`)
    pencere içinde `filed <= seans-1` kaydı taşır, yani sayacın konuşacak verisi VARDIR."""
    _arsiv(tmp_path, monkeypatch, _CF_ARSIV)
    _cf_dunyasi(sandbox_state, monkeypatch)
    gercek_scan = strat.scan_all
    tarihli: list[bool] = []

    def _sayan_scan(bars, params, rs_rating_value, ticker="?"):
        tarihli.append("date" in bars.columns)
        return gercek_scan(bars, params, rs_rating_value, ticker)

    monkeypatch.setattr(strat, "scan_all", _sayan_scan)
    out = cf_backfill.run(**_CF_PENCERE)
    assert tarihli, "hiç tarama koşmadı — çivi hiçbir şey kanıtlamaz"
    assert all(tarihli), ("cf tarama kuyruğu `date` taşımıyor — kuyruk kardeş `backtest.replay` "
                         "biçiminden ayrıştı ve iki kazanç-çapalı üretici çapadan ÖNCE None "
                         f"dönüyor (taşıyan/toplam: {sum(tarihli)}/{len(tarihli)})")
    pit = out["earnings_gate"]["pit_arsiv"]
    # `olculemedi` SAYILMAZ (inceleme sıkılaştırması 2026-09-02): o kova dört kısa-devre yolundan
    # beslenir (boş arşiv / biçimsiz tarih / ufuk dışı / sembol arşivde yok) ve arşiv yolu komple
    # kırıldığında 360 çağrının tamamı oraya düşer — `sum > 0` o dünyada da yeşil kalırdı, yani
    # çivi kartın kill-2'sinin ("çapa hâlâ erişilemez") tam yakalamak istediği arızaya kördü.
    # true+false = çapa SORULDU ve arşivden CEVAP ALDI (yön fark etmez); dikişin kanıtı budur.
    assert pit["true"] + pit["false"] > 0, (
        "kuyruk `date` taşıyor ama PIT çapası arşivden hiç CEVAP almadı — dikişin ucu arşive "
        f"varmıyor (kart EDG-2026-068 kill maddesi; olculemedi kanıt sayılmaz): {pit}")


def test_cf_param_IKI_scan_all_cagrisina_da_ulasir(sandbox_state, tmp_path, monkeypatch):
    """cf seansta İKİ KEZ tarar: sıkı eşiklerle `eff` (karar kolu) ve gevşek eşiklerle `rx`
    (near-miss gölge kolu). PARAMETRE İKİSİNE DE ULAŞMALIDIR.

    NEDEN AYRI ÇİVİ: `rx` `eff`ten türetilir, yani bugün doğru olması bir TÜRETME YAN ETKİSİDİR,
    beyan değil. Biri parametreyi `eff`e değil doğrudan `scan_all` çağrısına yazsaydı, gölge kolu
    sessizce PIT'siz takvime düşerdi — karar defteri PIT, near-miss defteri değil; ve fark hiçbir
    çıktıda görünmezdi (near-miss satırları ayrı bir ölçüm yüzeyidir).

    KOL KİMLİĞİ İŞARETLE ÖLÇÜLÜR, EŞİK DEĞERİYLE DEĞİL: `relax_for_near_miss` sarılıp dönüşüne
    bir işaret konur. Eşik kıyası (ör. `entry.min_score` 60 vs 50) yarın taban eşik 50'ye
    inerse iki kolu AYIRT EDEMEZ hâle gelir ve çivi sessizce tek kolu ölçmeye başlardı."""
    _arsiv(tmp_path, monkeypatch, [])
    from meridian.adapters import data as _data
    from meridian.backtest import SECTORS
    monkeypatch.setattr(_data, "validate_bars", lambda df, t: (True, []))
    monkeypatch.setitem(SECTORS, "AAA", "tech")
    per = {"SPY": make_bars(n=340, seed=1, trend=0.0004).set_index("date").sort_index(),
           "AAA": make_bars(n=340, seed=2, trend=0.0006, breakout_at=330).set_index("date").sort_index()}
    idx = per["SPY"]

    gercek_scan, gercek_relax = strat.scan_all, strat.relax_for_near_miss
    gorulen: list[tuple[bool, bool]] = []

    def _isaretli_relax(eff):
        rx = gercek_relax(eff)
        rx["__near_miss_kolu__"] = True          # kolu ADIYLA taşıyan işaret (bilinmeyen param: no-op)
        return rx

    def _sayan_scan(bars, params, rs_rating_value, ticker="?"):
        gorulen.append((bool(params.get("__near_miss_kolu__")),
                        bool(params.get("earnings.pit_arsiv"))))
        return gercek_scan(bars, params, rs_rating_value, ticker)

    monkeypatch.setattr(strat, "relax_for_near_miss", _isaretli_relax)
    monkeypatch.setattr(strat, "scan_all", _sayan_scan)
    strat_cfg = config.load_strategy()
    d = idx.index[-1]
    cf_backfill._plans_for_session(d, str(d.date()), per, idx, strat_cfg["params"],
                                   strat_cfg.get("params_by_regime"), config.goal(), 1)
    assert {kol for kol, _pit in gorulen} == {False, True}, \
        f"iki tarama kolu koşmadı — çivi tek kolu ölçüyor olabilir: {gorulen}"
    assert gorulen and all(pit for _kol, pit in gorulen), \
        f"parametre bir tarama koluna ULAŞMIYOR (kol, pit) = {gorulen}"


# ---------------------------------------------------------------------------------------------
# 8) TESTLER-ARASI SIZINTI — sayaç artık ÜRETİM yolundan artıyor, kayıt conftest'te
# ---------------------------------------------------------------------------------------------
def test_conftest_kaydi_pit_sayacini_YERINDE_sifirlar():
    """`_SAYAC` Görev 3'ten itibaren `replay`/`run` çağıran HER test dosyasında kirlenir ve o
    dosyaların hiçbiri temizlemekle yükümlü değildir (`scheduler._state` sınıfı). Kayıt
    `tests/conftest._MODUL_DURUMLARI`ta; bu çivi mekanizmayı DOĞRUDAN koşturur — kayıt silinirse
    kırmızıya döner.

    YERİNDE SIFIRLAMA AYRICA ÖLÇÜLÜR: mekanizma `clear()+update()` yapar, yeni sözlük ATAMAZ.
    Atasaydı `earnings_pit` içinde `_SAYAC`a tutulan referans kopardı ve sıfırlama hiçbir şeye
    dokunmamış olurdu (`_fmp._HEALTH` dersi, 2026-07-26)."""
    from tests import conftest as _cf
    kimlik = earnings_pit._SAYAC
    earnings_pit._SAYAC["true"] = 7
    earnings_pit._SAYAC["olculemedi"] = 11
    _cf._clear_module_caches()
    assert earnings_pit.sayac_oku() == {"true": 0, "false": 0, "olculemedi": 0}, \
        "conftest kaydı yok: sayaç testler arası taşınıyor"
    assert earnings_pit._SAYAC is kimlik, "sıfırlama yeni sözlük atadı — dış referanslar koptu"
