"""test_replay_uyelik_suzgeci_v427.py — TSK-159 S2 / EDG-2026-082: `backtest.replay`/`walk_forward`e
opsiyonel ÜYELİK SÜZGECİ (`uyelik: Callable[[str], set[str]] | None`).

NEDEN VAR: EDG-2026-082 tohumu, aday taramasını işlem tarihindeki PIT üyelikle (`uyelik(t) =
as_of(t)`) süzüp eski (üyeliksiz) tohumla kıyaslayacak — ama ölçüm koşmadan ÖNCE motorun kendisi
KANITLAMALI: (a) süzgeç TAM AÇIKKEN (herkes üye) bugünkü davranışı BİREBİR üretir, (b) TAM
KAPALIYKEN (kimse üye değil) sıfır işlem verir, (c) süzgeç YALNIZ yeni aday aramayı daraltır —
zaten AÇIK bir pozisyonun yönetimini/çıkışını hiç etkilemez. Kart adım-0 (a)(b) fizibilite
çivileri ve kartın "pozitif_kontrol" maddesi burada koşar; kartın kendisine dokunulmaz.

SENTETİK SAHNE: `strategy.scan_entry` gerçek strateji taraması yerine tek bir sembol (MEM) için
KOŞULLARDAN BAĞIMSIZ, deterministik bir `EntrySignal` üretecek şekilde monkeypatch'lenir (diğer
iki sembol, AAA/BBB, hiç sinyal üretmez — yalnız "3-5 sembollük evren" şartını dolduran DEKOR).
NEDEN GERÇEK TARAMA DEĞİL: gerçek `scan_entry`nin rastgele-yürüyüş sentetik barlarda NE ZAMAN
ateşleyeceği (RS/rejim/konsolidasyon eşikleri) öngörülemez — tam da bu testin ihtiyaç duyduğu
"birebir bu tarihte gir/çık" kesinliğini vermez. Süzgecin KENDİSİ test edilir, strateji taraması
DEĞİL (o zaten `test_differential_v60.py`/`test_backtest_audit_v23.py`nin konusu). Rejim/maruziyet
bütçesi YALNIZ endeks barlarından hesaplanır (`replay`in `idx_slice`i) — MEM'in üye olup olmaması
o hesaba hiç girmez, yani süzgecin AÇIP KAPAMASI rejim zamanlamasını DEĞİŞTİRMEZ (aşağıdaki
sahnenin öngörülebilir olmasının nedeni budur, bkz. `_taban_zaman_cizelgesi`).

Deterministik sahnede MEM, pozisyonda değilken HER seansta (izin veren rejim/bütçe günlerinde) bir
sinyal alır ve 200 seanslık pencerede birden çok işlem üretir — bu bir iddia değil, `sandbox_state`li
gerçek bir `replay()` koşumunun (bu dosyanın yazımı sırasında) ÖLÇÜLMÜŞ çıktısıdır; testler kesin
tarih/sebep listesini VARSAYMAZ, yalnız tabanın (`uyelik=None`) kendi çıktısını referans alıp
kıyaslar (bkz. `test_acik_pozisyon_uyelikten_cikinca_normal_kapanir_mutasyon2_hedefi`'ndeki sahne
varsayımı kontrolü — sabitler kayarsa test KIRMIZI YAZI ile uyarır, sessizce yanlış geçmez).
"""
from __future__ import annotations

import json

import pytest

from meridian import backtest, config
from meridian import strategy as strategy_mod
from meridian.strategy import EntrySignal
from tests.conftest import make_bars


def _valid_ohlc(df):
    """`make_bars` open/close'un high/low sınırlarını aşabilir (rastgele gürültü) — burada strateji
    taramasını KOŞMUYORUZ (scan_entry monkeypatch'li) o yüzden bu testin sonucu için ZORUNLU
    değildir, ama broker/ATR hesapları YİNE DE tutarlı OHLC bekler; `test_differential_v60.py`nin
    aynı adlı yardımcısındaki gerekçe burada da geçerli (bağımsız, küçük bir kopya — tek-kaynak
    yasası konusu değil: her test dosyası bu üç satırlık normalize adımını kendi kurar, deseni
    `test_differential_v60.py`/`test_kovab_ikimotor_v164.py` gibi başka dosyalarda da görürsünüz)."""
    df = df.copy()
    df["high"] = df[["open", "high", "close"]].max(axis=1)
    df["low"] = df[["open", "low", "close"]].min(axis=1)
    return df


N_BARS = 200
TICKERS = {"MEM": 2, "AAA": 3, "BBB": 4}   # MEM sinyal alır; AAA/BBB dekor (hiç sinyal almaz)
EVREN = set(TICKERS)


def _sahne():
    """Endeks + 3 sembollük sentetik bar evreni. `idx` rejim/maruziyet bütçesini üretir (MEM'in
    üye olup olmamasından BAĞIMSIZ — `replay` bu hesabı yalnız `index_bars`ten kurar)."""
    idx = _valid_ohlc(make_bars(N_BARS, seed=7, trend=0.0006))
    bars = {t: _valid_ohlc(make_bars(N_BARS, seed=s, trend=0.0008)) for t, s in TICKERS.items()}
    return bars, idx


def _mem_sinyali(bars_df, params, rs_rating_value, ticker="?"):
    """`strategy.scan_entry` YERİNE geçen deterministik saplama: yalnız MEM için, pozisyonda
    DEĞİLKEN sorulduğu HER seansta aynı biçimde bir `EntrySignal` üretir (fiyat o günün kapanışına
    göre ölçeklenir, R:R sabit 3,0 — kapının R:R tabanını rahatça geçer). AAA/BBB için hep None:
    evrende varlar (uyelik testinde 'üye ama hiç sinyal almayan sembol' rolünü oynarlar) ama
    hiçbir işlem üretmezler — testin MEM'e odaklanmasını sadeleştirir."""
    if ticker != "MEM":
        return None
    close = float(bars_df["close"].iloc[-1])
    entry = close * 1.001
    stop = entry * 0.95
    r_per_share = entry - stop
    target = entry + 3.0 * r_per_share
    return EntrySignal(ticker=ticker, setup="momentum_breakout", entry_trigger=entry, pivot=entry,
                       stop=stop, atr=r_per_share / 2.0, rs_rating=80, score=80,
                       profit_target=target, size_r=0.5, r_per_share=r_per_share,
                       notes="v427-sentetik-sinyal")


@pytest.fixture
def sahne(sandbox_state, monkeypatch):
    """`sandbox_state`: goal/bounds sandbox'tan okunur, canlı `state/`e dokunulmaz. `scan_entry`
    saplaması `meridian.strategy` MODÜL NESNESİNE yazılır — `backtest.py`nin `from . import
    strategy as strat` içe aktarımı AYNI modül nesnesine bakar, yani `strategy.scan_entry`
    çağrısı da bu saplamayı görür (iki ad, tek nesne)."""
    monkeypatch.setattr(strategy_mod, "scan_entry", _mem_sinyali)
    bars, idx = _sahne()
    params = config.default_strategy()["params"]
    goal = config.goal()
    dates = [str(x.date()) for x in idx["date"]]
    return {"bars": bars, "idx": idx, "params": params, "goal": goal,
           "start": dates[0], "end": dates[-1]}


def _replay(sahne, **kw):
    return backtest.replay(sahne["params"], sahne["bars"], sahne["idx"], sahne["goal"],
                           sahne["start"], sahne["end"], strategy_version=1, **kw)


def _kimlik(trades):
    """İşlemin YOL KİMLİĞİ: sembol/tarih/çıkış-sebebi — sermaye BÜYÜKLÜĞÜNDEN bağımsız alanlar.
    `qty`/`pnl_dollars`/`r_multiple` gibi BÜYÜKLÜK alanları BİLEREK dışarıda bırakılır: bir önceki
    işlemin süzülüp süzülmediği aynı koşumda BİLEŞİK sermaye eğrisini (`peak_equity`,
    `brk.derisk_mult`) değiştirir — pay tam SAYI hisseye yuvarlanır, yani ondan sonraki pozisyonun
    payı ve dolayısıyla `r_multiple`'ı BİR SONRAKİ ONDALIK BASAMAKTA kayabilir (ÖLÇÜLDÜ: bu testin
    yazımı sırasında aynı işlem iki koşumda 0,587 ↔ 0,588 verdi — aynı gün, aynı sebep, aynı fiyat
    seviyeleri, yalnız bileşik payda farklı). Bu BEKLENEN bir yan etkidir, süzgecin kendisinin bir
    kusuru DEĞİL. Süzgecin doğruluğu YOL kimliğinde (hangi sembol, ne zaman, hangi sebeple) ölçülür;
    işlemin ÖNÜNDE süzülmüş başka işlem YOKSA (bkz. mutasyon-2 testi) büyüklük alanları da dahil TAM
    eşitlik geçerli bir ölçüttür ve orada AYRICA sınanır."""
    return [(t["ticker"], t["ts_open"], t["ts_close"], t["exit_reason"]) for t in trades]


# =================================================================================================
# adım-0 (a) — süzgeç TAM AÇIK (herkes her seans üye) → bugünkü davranışla BİREBİR (json.dumps eşit)
# =================================================================================================
def test_adim0a_tam_acik_uyelik_bugunku_davranisla_birebir(sahne):
    """POZİTİF KONTROL + adım-0(a): `uyelik=None` ve `uyelik=<herkes-her-zaman-üye>` AYNI koşumu
    üretmeli. Aynı zamanda `uyelik`in SEANS BAŞINA BİR KEZ çağrıldığını da ölçer (aşağıdaki
    `cagrilar` sayacı) — MUTASYON 1 hedefi ("süzgeç üyeliği yok sayıp HER ZAMAN süzerse" bu testin
    ilk yarısını kırar; "uyelik'i sembol başına çağırırsa" ikinci yarısını kırar)."""
    taban = _replay(sahne, uyelik=None)
    assert taban.trades, "sahne hiç işlem üretmedi — kıyas VACUOUS olurdu (test_the_comparison_is_not_vacuous dersi)"
    assert len(taban.trades) >= 5, f"beklenenden az işlem ({len(taban.trades)}) — sahne zayıfladı, testin gücü düşük"

    cagrilar: list[str] = []

    def herkes_her_zaman(d):
        cagrilar.append(d)
        return set(EVREN)

    acik = _replay(sahne, uyelik=herkes_her_zaman)

    assert json.dumps(taban.trades, sort_keys=True) == json.dumps(acik.trades, sort_keys=True), \
        "uyelik tam açıkken (herkes üye) çıktı bugünkü davranıştan (uyelik=None) SAPTI"
    assert len(cagrilar) > 0, "uyelik hiç çağrılmadı — tarama koşmadı, kıyas boş"
    assert len(cagrilar) == len(set(cagrilar)), \
        f"uyelik AYNI seans için birden çok kez çağrıldı ({len(cagrilar) - len(set(cagrilar))} tekrar) — seans başına bir kez olmalı, sembol başına DEĞİL"


# =================================================================================================
# adım-0 (b) — süzgeç TAM KAPALI (kimse hiç üye değil) → 0 işlem
# =================================================================================================
def test_adim0b_tam_kapali_uyelik_sifir_islem(sahne):
    kapali = _replay(sahne, uyelik=lambda d: set())
    assert kapali.trades == [], f"uyelik hiçbir zaman kimseyi üye saymıyorken işlem üretti: {kapali.trades}"


# =================================================================================================
# ÜYELİK ZAMANA GÖRE DEĞİŞİYOR — yeni ADAY arama süzülür, açık pozisyon YÖNETİMİ süzülmez
# =================================================================================================
def test_uyelik_oncesi_giris_suzulur_sonraki_islemler_bozulmadan_devam_eder(sahne):
    """MEM tabanın İLK girişinden önce üye değil; üyelik tabanın İLK işleminin KAPANIŞ gününden
    (`ts_close`) itibaren SONSUZA KADAR başlar. NEDEN `ts_close` VE `ts_open` DEĞİL: giriş, sinyalin
    doğduğu CLOSE(D) seansından BİR gün SONRA (D+1 açılışında) dolar — yani tabanın ikinci girişini
    (`ts_open`) üreten TARAMA GÜNÜ, ilk işlemin kapandığı gündür (MEM o gün pozisyonu boşaltır ve
    AYNI seansın CLOSE(D) fazında tekrar taranabilir hâle gelir). Eşiği `ts_open`a göre kursaydık
    tarama gününü BİR gün geç kapatır, ikinci girişi de bir gün öteler ve kimliği yanlışlıkla kırardı
    (bu, testin ilk yazımında GERÇEKTEN ölçülen bir hataydı — kalıcı ders burada).

    Tabanın İLK girişi (bkz. `taban.trades[0]`) hiç doğmaz, ama 2..N arası işlemleri YOL KİMLİĞİNDE
    (bkz. `_kimlik`) BİREBİR aynı kalır — süzgeç yalnız YASAKLI dönemdeki aday aramayı kesiyor,
    rejim/bütçe zamanlamasını ya da MEM'in kendi fiyat yolunu bozmuyor."""
    taban = _replay(sahne, uyelik=None)
    assert len(taban.trades) >= 2, "sahne en az iki döngü üretmeli (birini düşürüp gerisini kıyaslamak için)"
    tarama_esigi = taban.trades[0]["ts_close"]

    def sonradan_uye(d):
        return set(EVREN) if d >= tarama_esigi else set()

    sonraki = _replay(sahne, uyelik=sonradan_uye)

    assert _kimlik(sonraki.trades) == _kimlik(taban.trades)[1:], (
        "üyelik-öncesi giriş süzülmedi ya da sonraki işlemler bozuldu")
    assert all(t["ts_open"] >= tarama_esigi for t in sonraki.trades), \
        "üyelik başlamadan işlem açılmış — süzgeç geçmişe sızdı"


def test_acik_pozisyon_uyelikten_cikinca_normal_kapanir_mutasyon2_hedefi(sahne):
    """MUTASYON 2 HEDEFİ: MEM ilk girişte (2022-01-07) üye; pozisyon AÇIKKEN, kapanmadan önce
    (2022-01-15 < kapanış 2022-01-28) üyelikten SONSUZA KADAR çıkar. Süzgeç yalnız ADAY aramaya
    uygulanıyorsa: (1) bu tek pozisyon tabanla BİREBİR (dolar alanları DAHİL — bu koşumda ondan
    ÖNCE hiç işlem yok, yani sermaye eğrisi hiç sapmamış olur, tam eşitlik burada GEÇERLİ bir
    ölçüttür) kapanır, (2) üyelik bir daha hiç açılmadığı için SONRAKİ giriş hiç doğmaz (toplam 1
    işlem). Süzgeç pozisyon YÖNETİMİNE de (yanlışlıkla) uygulanırsa pozisyon üyeliği kaybettiği anda
    dondurulur/atlanır ve gerçek `time_stop` yerine seans sonunda `eod_markout`la kapanır — bu test
    o mutasyonu KIRMIZI yapar (bkz. rapor'daki mutasyon kanıtı)."""
    taban = _replay(sahne, uyelik=None)
    assert taban.trades, "sahne hiç işlem üretmedi — mutasyon-2 hedefi ölçülemez"
    ilk = taban.trades[0]
    kayip_tarihi = "2022-01-15"
    assert ilk["ts_open"] < kayip_tarihi < ilk["ts_close"], (
        f"sahne varsayımı bozuldu: ilk işlem {ilk['ts_open']}→{ilk['ts_close']}, "
        f"{kayip_tarihi} bu aralıkta değil — sabitleri güncelle")

    def uyelikten_cikar(d):
        return set(EVREN) if d < kayip_tarihi else set()

    sonraki = _replay(sahne, uyelik=uyelikten_cikar)

    assert sonraki.trades == [ilk], (
        "açık pozisyon üyelikten çıkınca tabanla BİREBİR kapanmadı (çıkış fazı süzülmüş olabilir) "
        f"— alınan: {sonraki.trades}")


# =================================================================================================
# walk_forward → replay'e AYNEN geçiriyor mu (başka çağıranlar DOKUNULMAZ, varsayılan None)
# =================================================================================================
def test_walk_forward_uyelik_parametresini_replaye_gecirir(sahne, monkeypatch):
    yakalanan: dict = {}
    orijinal_replay = backtest.replay

    def casus_replay(*args, **kwargs):
        yakalanan.update(kwargs)
        return orijinal_replay(*args, **kwargs)

    monkeypatch.setattr(backtest, "replay", casus_replay)

    dates = [str(x.date()) for x in sahne["idx"]["date"]]
    isaret = lambda d: set()  # kimlik karşılaştırması için — davranışın kendisi bu testin konusu değil

    backtest.walk_forward(sahne["params"], sahne["bars"], sahne["idx"], sahne["goal"],
                          dates[0], dates[100], dates[150], dates[-1], uyelik=isaret)

    assert yakalanan.get("uyelik") is isaret, \
        f"walk_forward, uyelik parametresini replay'e AYNEN geçirmedi: {yakalanan.get('uyelik')!r}"


def test_walk_forward_uyelik_varsayilani_None_diger_cagiranlar_dokunulmaz(sahne, monkeypatch):
    """Varsayılan `uyelik=None`: eski çağrı biçimi (reflect/prescreen/baseline — kwarg hiç
    verilmez) `replay`e `uyelik=None` geçirir, yani bugünkü davranış BİREBİR korunur."""
    yakalanan: dict = {}
    orijinal_replay = backtest.replay

    def casus_replay(*args, **kwargs):
        yakalanan.update(kwargs)
        return orijinal_replay(*args, **kwargs)

    monkeypatch.setattr(backtest, "replay", casus_replay)
    dates = [str(x.date()) for x in sahne["idx"]["date"]]

    backtest.walk_forward(sahne["params"], sahne["bars"], sahne["idx"], sahne["goal"],
                          dates[0], dates[100], dates[150], dates[-1])

    assert yakalanan.get("uyelik") is None
