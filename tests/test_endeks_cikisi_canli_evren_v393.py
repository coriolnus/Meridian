"""test_endeks_cikisi_canli_evren_v393.py — 13 S&P 500 ENDEKS-ÇIKIŞI SEMBOLÜ YALNIZ CANLI EVRENDEN
ÇIKAR (TSK-116, 2026-09-03, operatör revize kararı).

BAĞLAM: `state/universe_drift.json` (2026-09-03 gece, kaynak wikipedia) 13 sembolün S&P 500'den
çıktığını ölçtü: AVB, BURL, CAG, EA, ENPH, EQR, LNG, MTCH, PINS, ROKU, SNAP, SPOT, VFC. Şirketlerin
HİÇBİRİ delist DEĞİL — hâlâ aktif işlem görüyorlar, yalnız endeks üyeliği bitti. Sabahki karar
"RETIRED_SYMBOLS'a taşı" idi ama bu REVİZE edildi: `REPLAY_UNIVERSE` tarihe duyarsız TEK bir
listedir (PIT değildir) ve bu 13 şirket geçmişte GERÇEKTEN S&P 500 üyesiydi (A1 ölçümü:
trade_plans'ta 10'u, trades'te 11'i geçiyor). Tam emeklilik geçmiş replay/backtest'i de etkiler ve
sağkalan yanlılığını ARTIRIR — bu yüzden yalnız CANLI evrenden (`LIVE_UNIVERSE`) çıkarılırlar;
`REPLAY_UNIVERSE` ve `RETIRED_SYMBOLS` (8 delist sembol) DEĞİŞMEZ.

Bu turun sözü: `LIVE_UNIVERSE = REPLAY_UNIVERSE eksi INDEX_EXITED` TEK yerde türetilir, canlı
tüketiciler (Finviz keşif filtresi, marketstream aboneliği, scheduler canlı taramaları, api.py
evren sayısı yüzeyleri, shortinterest/insider canlı çekimleri) buna geçer; replay tüketicileri
(backtest/recompute/cf_backfill/trend_shadow/component_ic) REPLAY_UNIVERSE'de KALIR.

TSK-143 EKİ (2026-09-05, bu turun ruling'i K1/K2): yukarıdaki "hiçbiri delist değil" hükmü YANLIŞ
ÇIKTI — Massive `/v3/reference/tickers` + S&P basın bültenleri üçünün (EA, AVB, EQR) GERÇEKTEN
delist olduğunu doğruladı; onlar artık `RETIRED_SYMBOLS`ta ve REPLAY_UNIVERSE'den de çıkarıldı
(251→248). Kalan 10'un "S&P 500 çıkışı; aktif" hükmü de tekti ama yalnız 4'ü (ENPH, MTCH, CAG,
VFC) için doğruydu; altısı (BURL, ROKU, SPOT, LNG, PINS, SNAP) S&P 500'e HİÇ ÜYE OLMAMIŞ (bkz.
`data.py::EVREN_DISI_BEYANLI` şerhi). `INDEX_EXITED` adı KORUNDU (`EVREN_DISI_BEYANLI`nin AYNI
nesnesi, tek kaynak) ama artık 10 kayıt taşıyor — bu dosyadaki `BEKLENEN_13`/13 sayılı çiviler
`BEKLENEN_10`/10'a indirildi; testler tests/test_evren_emekliligi_v134.py'deki TSK-143 bölümüyle
BİRLİKTE okunmalı (RETIRED_SYMBOLS tarafı orada çivilenir).
"""
from __future__ import annotations

import inspect
import time

import pandas as pd

from meridian import dataset, store
from meridian.adapters import constituents, data, finviz
from tests.conftest import make_bars

# TSK-143 (2026-09-05): EA, AVB, EQR çıkarıldı — gerçek delist, RETIRED_SYMBOLS'a taşındı.
BEKLENEN_10 = {"BURL", "CAG", "ENPH", "LNG", "MTCH", "PINS", "ROKU", "SNAP", "SPOT", "VFC"}


def _events(name: str) -> list[dict]:
    return [e for e in store.read_jsonl("events.jsonl")
            if e.get("event") == name or e.get("kind") == name]


# =================================================================================================
# a) Defterin KENDİSİ — INDEX_EXITED, LIVE_UNIVERSE, REPLAY_UNIVERSE/RETIRED_SYMBOLS DEĞİŞMEDİ
# =================================================================================================
def test_index_exited_defteri_ve_gerekce():
    """TSK-143 (2026-09-05) revizyonu: 10 sembol set eşitliği; her kayıt gerekçelidir ve gerekçe
    dört bilinen kategoriden birine düşer (S&P 500 çıkışı [tarihli] / S&P 400 üyesi / yabancı
    şirket / hiç üye olmadı) — eski turun HEPSİNE tek metin yazan hükmünün YANLIŞ olduğu tam bu
    testte ölçülmüştü (bkz. dosya başlığı TSK-143 eki)."""
    assert len(data.INDEX_EXITED) == 10, "defter elle bakımlıdır; sayı değiştiyse gerekçesi de yazılmalı"
    assert set(data.INDEX_EXITED) == BEKLENEN_10
    assert data.INDEX_EXITED is data.EVREN_DISI_BEYANLI, "tek kaynak: iki isim AYNI sözlüğe bağlı olmalı"
    for t, gerekce in data.INDEX_EXITED.items():
        assert gerekce.strip(), f"{t} gerekçesiz endeks-çıkışı edilmiş — hüküm gerekçesiz yazılmaz"
        assert ("S&P 500 çıkışı" in gerekce or "S&P 400 üyesi" in gerekce
                or "yabancı şirket" in gerekce or "hiç girmedi" in gerekce), \
            f"{t}: gerekçe metni bilinen dört kategoriden hiçbirine düşmüyor"
    # Yalnız gerçekten S&P 500'den ÇIKMIŞ (hiç üye olmamış değil) dördü tarihli "çıkışı" taşır.
    cikis_tasiyanlar = {t for t, g in data.INDEX_EXITED.items() if "S&P 500 çıkışı" in g}
    assert cikis_tasiyanlar == {"ENPH", "MTCH", "CAG", "VFC"}

    # Tek kapı büyük/küçük harf ayırt etmez.
    assert data.is_index_exited("roku") and data.is_index_exited("ROKU")
    assert not data.is_index_exited("") and not data.is_index_exited(None) and not data.is_index_exited("AAPL")


def test_retired_ve_index_exited_ayrik_kumeler():
    """İki defter AYNI ANDA doğru olamaz eğer kesişirse: bir sembol ya DELİST ya ENDEKS-ÇIKIŞI —
    ikisi bir arada hükümlenirse hangi sınıfın geçerli olduğu okunmaz olur."""
    kesisim = set(data.RETIRED_SYMBOLS) & set(data.INDEX_EXITED)
    assert not kesisim, f"delist ve endeks-çıkışı defterleri kesişiyor: {sorted(kesisim)}"


def test_replay_universe_degismedi():
    """TSK-143 (2026-09-05) günceli: REPLAY_UNIVERSE 251→248, RETIRED_SYMBOLS 8→11 — bu turun
    KENDİ KONUSU (EA/AVB/EQR gerçek delist çıktı, RETIRED_SYMBOLS'a taşındı; tests/test_evren_
    emekliligi_v134.py'de çivilenir). Kalan 10 (BEKLENEN_10) hâlâ endeks-çıkışı DEĞİL — hükmü
    beyanlı-aktif; onlar REPLAY_UNIVERSE'de KALMALI (silinmedi — yalnız canlı evrenden düşüyorlar)."""
    assert len(data.REPLAY_UNIVERSE) == 248, "REPLAY_UNIVERSE değişti — bu turun sözleşmesi bozuldu"
    assert len(data.RETIRED_SYMBOLS) == 11, "RETIRED_SYMBOLS değişti — bu turun sözleşmesi bozuldu"
    assert BEKLENEN_10 <= set(data.REPLAY_UNIVERSE), \
        "beyanlı-aktif sembollerden biri REPLAY_UNIVERSE'den silinmiş — geçmiş replay'i bozar"
    assert not ({"EA", "AVB", "EQR"} & set(data.REPLAY_UNIVERSE)), \
        "gerçek delist sembolü REPLAY_UNIVERSE'de kalmış — TSK-143 K1 geri alınmış"


def test_live_universe_turetilir():
    """LIVE_UNIVERSE TEK yerde türetilir (tek-kaynak yasası): REPLAY_UNIVERSE eksi INDEX_EXITED,
    238 sembol. TSK-143 SONRASI da 238 KALIR — 248 (REPLAY_UNIVERSE) eksi 10 (INDEX_EXITED), aynı
    3 sembolün her iki kümeden BİRLİKTE çıkmasının doğal sonucu (251-13 de 238'di). Mutasyon:
    LIVE_UNIVERSE REPLAY_UNIVERSE'e eşitlenirse bu çivi ötmeli."""
    assert len(data.LIVE_UNIVERSE) == 238
    assert set(data.LIVE_UNIVERSE) == set(data.REPLAY_UNIVERSE) - set(data.INDEX_EXITED)
    for t in BEKLENEN_10:
        assert t not in data.LIVE_UNIVERSE, f"{t} endeks-çıkışı ama LIVE_UNIVERSE'de kalmış"
    # RETIRED_SYMBOLS zaten REPLAY_UNIVERSE'de yok — LIVE_UNIVERSE de yapısal olarak onları taşımaz.
    assert not (set(data.RETIRED_SYMBOLS) & set(data.LIVE_UNIVERSE))


# =================================================================================================
# b) Finviz keşfi — endeks-çıkışı sembol canlı evrene GERİ GİREMEZ, eleme SESSİZ olmaz
# =================================================================================================
def test_finviz_endeks_disi_geri_giremez(sandbox_state, monkeypatch):
    """`tests/test_evren_emekliligi_v134.py::test_finviz_emekli_geri_giremez` ile AYNI desen, AYRI
    olay adıyla: RETIRED ile INDEX_EXITED karıştırılırsa "delist" hükmü yanlış sembole yapışır."""
    dataset._cache.clear()
    index_df = make_bars(n=300)
    istenen: list = []

    monkeypatch.setattr(dataset, "load", lambda use_cache=True, universe=None: ({}, index_df.copy()))
    monkeypatch.setattr(finviz, "discover_universe", lambda **k: ["ROKU", "NVDA"])

    def sahte_load_many(tickers, start, end, use_cache=True, **k):
        istenen.extend(tickers)
        return {t: make_bars(n=300) for t in tickers}

    monkeypatch.setattr(data, "load_many", sahte_load_many)

    bars, _ = dataset.load_live()

    assert "ROKU" not in istenen, "endeks-çıkışı sembol bar hattına sorulmuş"
    assert istenen == ["NVDA"], "yaşayan keşif sembolü elenmemeli"
    assert "ROKU" not in bars and "NVDA" in bars

    ev = _events("index_exited_symbol_rediscovered")
    assert ev, "endeks-çıkışı sembol SESSİZCE elendi — keşif kaynağının bayatlığı görünmez kaldı"
    assert "ROKU" in str(ev[-1].get("tickers")) and "NVDA" not in str(ev[-1].get("tickers"))
    # RETIRED olayı bu turda YANLIŞ tetiklenmemeli — sınıflar karışmasın.
    assert not _events("retired_symbol_rediscovered")
    dataset._cache.clear()


def test_finviz_iki_sinif_birlikte_dusebilir(sandbox_state, monkeypatch):
    """Aynı keşif turunda hem delist hem endeks-çıkışı sembol önerilirse İKİ AYRI olay yazılır —
    tek bir olayda karıştırılmaz (her sınıfın kendi hükmü, kendi okuyucusu)."""
    dataset._cache.clear()
    index_df = make_bars(n=300)

    monkeypatch.setattr(dataset, "load", lambda use_cache=True, universe=None: ({}, index_df.copy()))
    monkeypatch.setattr(finviz, "discover_universe", lambda **k: ["ANSS", "SNAP", "NVDA"])
    monkeypatch.setattr(data, "load_many", lambda tickers, start, end, use_cache=True, **k:
                         {t: make_bars(n=300) for t in tickers})

    bars, _ = dataset.load_live()

    assert set(bars) == {"NVDA"}
    ret_ev = _events("retired_symbol_rediscovered")
    idx_ev = _events("index_exited_symbol_rediscovered")
    assert ret_ev and "ANSS" in str(ret_ev[-1].get("tickers"))
    assert idx_ev and "SNAP" in str(idx_ev[-1].get("tickers"))
    dataset._cache.clear()


# =================================================================================================
# c) Bekçi — universe_drift() endeks-çıkışının geri girip girmediğini de sorar
# =================================================================================================
def test_universe_drift_index_exited_alanlari(sandbox_state, monkeypatch):
    """`retired_n`/`retired_in_universe` kardeşi: `index_exited_n` sabit 10 (TSK-143, 2026-09-05 —
    eskiden 13'tü, üçü RETIRED_SYMBOLS'a taşındı), `index_exited_in_live` normalde BOŞ (LIVE_
    UNIVERSE'in kendi tanımı zaten süzer). İki hükmün AYNI ANDA doğru olduğu ölçülür — biri
    diğerini sessizce değiştirmemeli."""
    monkeypatch.setattr(constituents, "current", lambda *a, **k: [])
    d = constituents.universe_drift()
    assert d["status"] == "unknown"
    assert d["index_exited_n"] == 10
    assert d["index_exited_in_live"] == []
    assert d["retired_n"] == 11, "endeks-çıkışı eklemesi delist sayacını bozmuş"

    uyeler = [t for t in data.REPLAY_UNIVERSE] + [f"X{i}" for i in range(300)]
    monkeypatch.setattr(constituents, "current", lambda *a, **k: uyeler)
    d = constituents.universe_drift()
    assert d["status"] == "ok"
    assert d["index_exited_n"] == 10 and d["index_exited_in_live"] == []
    assert d["retired_n"] == 11


def test_universe_drift_geri_giren_endeks_disi_ismi_GORUNUR_kilar(sandbox_state, monkeypatch):
    """Bekçinin değeri ancak ihlalde ölçülür: LIVE_UNIVERSE türetmesi bozulup endeks-çıkışı bir
    isim geri girerse rapor susmamalı."""
    monkeypatch.setattr(data, "LIVE_UNIVERSE", [*data.LIVE_UNIVERSE, "SNAP"])
    monkeypatch.setattr(constituents, "current", lambda *a, **k: [])
    assert constituents.universe_drift()["index_exited_in_live"] == ["SNAP"]


# =================================================================================================
# d) Replay tüketicileri — statik kanıt: REPLAY_UNIVERSE okur, LIVE_UNIVERSE'e DOKUNMAZ
# =================================================================================================
def test_replay_tuketicileri_live_universe_KULLANMAZ():
    """Backtest/recompute/cf_backfill/trend_shadow/component_ic sağkalan yanlılığını ARTIRMAMAK
    için REPLAY_UNIVERSE'i kullanmaya DEVAM etmeli. Statik kanıt: fonksiyon kaynağı REPLAY_UNIVERSE
    OKUR ve LIVE_UNIVERSE adını hiç GEÇİRMEZ. Mutasyon: biri LIVE_UNIVERSE'e çevrilirse bu çivi
    ötmeli."""
    from meridian import cf_backfill, component_ic, recompute, trend_shadow

    hedefler = {
        "trend_shadow.run_cycle": trend_shadow.run_cycle,
        "cf_backfill.run": cf_backfill.run,
        "component_ic._load_universe": component_ic._load_universe,
        "recompute._universe_recompute": recompute._universe_recompute,
    }
    for ad, fn in hedefler.items():
        kaynak = inspect.getsource(fn)
        assert "REPLAY_UNIVERSE" in kaynak, f"{ad}: REPLAY_UNIVERSE referansı kayboldu"
        assert "LIVE_UNIVERSE" not in kaynak, \
            f"{ad}: replay tüketicisi LIVE_UNIVERSE'e geçmiş — sağkalan yanlılığını artırır (TSK-116)"


# =================================================================================================
# e) Canlı tüketiciler — statik kanıt: LIVE_UNIVERSE okur (regresyon bekçisi)
# =================================================================================================
def test_canli_tuketiciler_live_universe_okur():
    """Bu turun asıl değişikliği: shortinterest/insider artık LIVE_UNIVERSE okur; marketstream ise
    (r3'ten beri, Bulgu 4) DOĞRUDAN LIVE_UNIVERSE değil `dataset._canli_korunan_evren()` okur —
    TEK KAYNAK, positions ∪ armed. Statik kanıt — davranışsal testler ayrıca (b)/(f) ve
    scheduler/api dosya-sahipliği raporunda."""
    from meridian import marketstream
    from meridian.adapters import insider, shortinterest

    assert "_canli_korunan_evren" in inspect.getsource(marketstream.subscribed_symbols), \
        "marketstream artık dataset._canli_korunan_evren() üzerinden okumalı (armed dahil, TSK-116 r3)"
    assert "LIVE_UNIVERSE" in inspect.getsource(shortinterest._universe)
    assert "LIVE_UNIVERSE" in inspect.getsource(insider._universe)


# =================================================================================================
# f) DÜZELTME TURU 1 (2026-09-03, Rol-1 kararı) — `dataset.load()` taban daralması
#
# Önceki turun AÇIK KALEMİ: Finviz süzgeci `is_index_exited` eklense de `load()`'un TABANI hâlâ
# REPLAY_UNIVERSE'i sorduğu için `loop.daily_cycle`ın gördüğü `bars` sözlüğü 13 endeks-çıkışı
# sembolü İÇERMEYE devam ediyordu — "yalnız canlıdan çıkar" kararı aday taramasını KAPSAMIYORDU.
# Rol-1 kararı: `load(universe=...)` opsiyonel parametresi (None → REPLAY_UNIVERSE, BİREBİR eski
# davranış) + `_load_live_inner`ın `LIVE_UNIVERSE + korunan ticker'lar` ile çağırması
# (`_canli_korunan_evren`). AÇIK POZİSYON/SİLAHLI PLAN KORUMASI: portfolio.json İKİ kümeyi de
# (`positions`, `armed`) dataset katmanından erişilebilir taşıyor (marketstream.subscribed_symbols
# ile AYNI store.read_json yolu) — bu yüzden `load_live(..., ek_semboller=...)` gibi ayrı bir
# çağıran-taşımalı parametre AÇILMADI, dataset katmanı zaten yeterliydi.
# =================================================================================================
def test_load_varsayilan_hala_251_replay_birebir(sandbox_state, monkeypatch):
    """(c) `dataset.load()` parametre verilmeden (`universe=None`) hâlâ REPLAY_UNIVERSE'i sorar VE
    süreç-içi önbelleğe yazar/okur — replay/backtest/recompute davranışı BİREBİR (mevcut
    v134/v12/v7/v301/v291 çivileri bu yüzden bu turdan SONRA da yeşil kalmalı)."""
    dataset._cache.clear()
    istenen: list = []
    index_df = make_bars(n=300)

    def sahte_load_many(tickers, start, end, use_cache=True, **k):
        istenen.extend(tickers)
        return {t: make_bars(n=300) for t in tickers}

    monkeypatch.setattr(data, "load_bars", lambda t, s, e, **k: index_df.copy())
    monkeypatch.setattr(data, "load_many", sahte_load_many)

    bars1, _ = dataset.load(use_cache=False)
    assert istenen == list(data.REPLAY_UNIVERSE), "varsayılan çağrı REPLAY_UNIVERSE'i sormuyor"

    # ÖNBELLEĞE YAZILDI: ikinci varsayılan çağrı (use_cache=True) AĞA gitmeden AYNI nesneyi döner.
    istenen.clear()
    bars2, _ = dataset.load(use_cache=True)
    assert istenen == [], "varsayılan çağrı önbelleği atlamış"
    assert bars2 is bars1
    dataset._cache.clear()


def test_load_custom_universe_onbellegi_kirletmez(sandbox_state, monkeypatch):
    """`universe=` verilen bir `load()` çağrısı süreç-içi önbelleği NE okur NE yazar — canlı yolun
    dar (LIVE_UNIVERSE) çağrısı, SONRAKİ bir varsayılan (replay, 251) çağrının tabanını
    DARALTMAMALI. Bu, `load_live`in Finviz genişletmesine uygulanan LOOK-AHEAD KARANTİNASIYLA AYNI
    gerekçedir — yalnız yönü ters (burada canlı DAR küme replay'in TAM kümesini kirletmesin diye)."""
    dataset._cache.clear()
    index_df = make_bars(n=300)
    monkeypatch.setattr(data, "load_bars", lambda t, s, e, **k: index_df.copy())
    monkeypatch.setattr(data, "load_many", lambda tickers, s, e, use_cache=True, **k:
                         {t: make_bars(n=300) for t in tickers})

    bars_replay, _ = dataset.load(use_cache=False)
    assert set(bars_replay) == set(data.REPLAY_UNIVERSE)

    dar = ["AAPL", "MSFT"]
    bars_canli, _ = dataset.load(use_cache=True, universe=dar)
    assert set(bars_canli) == set(dar)

    bars_replay2, _ = dataset.load(use_cache=True)
    assert set(bars_replay2) == set(data.REPLAY_UNIVERSE), \
        "custom çağrı sonrası varsayılan çağrı artık tam evreni görmüyor — önbellek kirlendi"
    assert bars_replay2 is bars_replay, "varsayılan önbellek custom çağrıyla EZİLMİŞ"
    dataset._cache.clear()


def test_load_live_taban_index_exited_disar_da_pozisyon_yokken(sandbox_state, monkeypatch):
    """(a) Pozisyon/silahlı plan YOKKEN `load_live()`ın döndürdüğü bar anahtarları ile INDEX_EXITED
    KESİŞMEZ — canlı adayların taban kümesi GERÇEKTEN LIVE_UNIVERSE'e daralır (bu turdan önce
    `load()`'un tabanı hâlâ REPLAY_UNIVERSE'di, bu çivi o boşluğu kapatır)."""
    dataset._cache.clear()
    monkeypatch.setattr(finviz, "discover_universe", lambda **k: [])
    index_df = make_bars(n=300)
    monkeypatch.setattr(data, "load_bars", lambda t, s, e, **k: index_df.copy())

    istenen: list = []

    def sahte_load_many(tickers, start, end, use_cache=True, **k):
        istenen.extend(tickers)
        return {t: make_bars(n=300) for t in tickers}

    monkeypatch.setattr(data, "load_many", sahte_load_many)

    bars, _ = dataset.load_live()

    assert set(istenen) == set(data.LIVE_UNIVERSE), "canlı taban artık LIVE_UNIVERSE değil"
    assert not (set(bars) & BEKLENEN_10), "endeks-çıkışı sembol pozisyonsuzken hâlâ bar hattında"
    dataset._cache.clear()


def test_load_live_acik_pozisyonda_endeks_disi_sembolun_bari_YUKLENIR(sandbox_state, monkeypatch):
    """(b) INDEX_EXITED içinden bir sembolde (ROKU) açık pozisyon VARKEN o sembolün barı canlı
    yolda YİNE yüklenir — manage_position/mirror çıkışı yönetebilsin diye. Diğer 12 endeks-çıkışı
    sembol HÂLÂ dışarıda: koruma YALNIZ pozisyonu olan sembole özeldir, hepsine genellenmez (yeni
    giriş yolu kapalı kalmaya devam eder)."""
    dataset._cache.clear()
    store.write_json("portfolio.json", {"positions": {"ROKU": {"qty": 10}}})
    monkeypatch.setattr(finviz, "discover_universe", lambda **k: [])
    index_df = make_bars(n=300)
    monkeypatch.setattr(data, "load_bars", lambda t, s, e, **k: index_df.copy())

    istenen: list = []

    def sahte_load_many(tickers, start, end, use_cache=True, **k):
        istenen.extend(tickers)
        return {t: make_bars(n=300) for t in tickers}

    monkeypatch.setattr(data, "load_many", sahte_load_many)

    bars, _ = dataset.load_live()

    assert "ROKU" in istenen and "ROKU" in bars, \
        "açık pozisyonlu endeks-çıkışı sembolün barı YÜKLENMEDİ — manage_position körleşir"
    diger_9 = BEKLENEN_10 - {"ROKU"}
    assert not (set(istenen) & diger_9), "pozisyonsuz endeks-çıkışı semboller de sızmış"

    ev = _events("index_exited_position_bars_kept")
    assert ev, "koruma sessizce uygulandı — hangi sembolün neden hâlâ tarandığı görünmüyor"
    assert "ROKU" in str(ev[-1].get("tickers"))
    dataset._cache.clear()


def test_load_live_silahli_planda_endeks_disi_sembolun_bari_YUKLENIR(sandbox_state, monkeypatch):
    """Aynı koruma SİLAHLI (onaylanmış, henüz dolmamış) plana da uygulanır — bekleyen bir emrin
    barsız kalması açık pozisyon kadar gerçek bir kördür (bkz. loop.py'deki `_arm_yama` iç fonksiyonu,
    portfolio.json['armed'])."""
    dataset._cache.clear()
    store.write_json("portfolio.json", {"armed": [{"ticker": "SNAP", "id": "p1"}]})
    monkeypatch.setattr(finviz, "discover_universe", lambda **k: [])
    index_df = make_bars(n=300)
    monkeypatch.setattr(data, "load_bars", lambda t, s, e, **k: index_df.copy())

    istenen: list = []

    def sahte_load_many(tickers, start, end, use_cache=True, **k):
        istenen.extend(tickers)
        return {t: make_bars(n=300) for t in tickers}

    monkeypatch.setattr(data, "load_many", sahte_load_many)

    bars, _ = dataset.load_live()

    assert "SNAP" in istenen and "SNAP" in bars, "silahlı plandaki endeks-çıkışı sembolün barı YÜKLENMEDİ"
    dataset._cache.clear()


def test_canli_korunan_evren_pozisyonsuz_LIVE_UNIVERSE_dondurur(sandbox_state):
    """`_canli_korunan_evren()`in kendisi: portfolio.json boşken (ya da yokken) tam olarak
    LIVE_UNIVERSE'i döndürür — fazladan kopya/ekleme YOK."""
    assert dataset._canli_korunan_evren() == data.LIVE_UNIVERSE


# =================================================================================================
# g) DÜZELTME TURU 3 (2026-09-03, Rol-1 kararı — review.md) — önbellek EVREN İMZASIYLA anahtarlanır,
# kurtarma dalı imzaya sadık kalır, marketstream armed'ı da korur
#
# İnceleme Bulgu 1 (KRİTİK): r1'de custom (canlı) çağrı süreç-içi önbelleği NE okuyordu NE
# yazıyordu — "zararsız" sanılmıştı, ama `_load_live_inner` HER canlı pollde custom çağırdığı için
# (`_canli_korunan_evren()` asla None dönmez) canlı yolun kısayolu TAMAMEN devre dışı kalmıştı:
# `scheduler.py`nin 300sn kadanslı "cache-only poll" fazı her turda ~238 CSV'yi baştan okuyordu.
# Çözüm: önbellek EVREN İMZASIYLA anahtalanır (`_cache["custom"][imza]`), REPLAY'in düz
# `_cache["bars"]`/`_cache["index"]` çifti (dış testlerin doğrudan yazdığı ŞEKİL) DOKUNULMADAN kalır.
#
# İnceleme Ö-3 (ÖNEMLİ): endeks-bütünlük kurtarma dalı artık `custom` iken REPLAY süperseti DEĞİL,
# `uni`ye KIRPILMIŞ bir küme döner (`_kirp_kurtarma`).
#
# İnceleme Bulgu 4 (ÖNEMLİ): `marketstream.subscribed_symbols` artık `dataset._canli_korunan_evren()`
# okur (positions ∪ armed) — önceki asimetri (yalnız positions) kapandı.
# =================================================================================================
def test_load_custom_cache_ayni_imza_diskten_okumaz(sandbox_state, monkeypatch):
    """K-1: AYNI evrenle art arda `load(universe=...)` çağrısı DİSKTEN İKİNCİ KEZ OKUMAZ — canlı
    poll'un süreç-içi kısayolu geri geldi. FARKLI evren AYRI bir anahtarda durur (ikisi birbirini
    KİRLETMEZ). Mutasyon: imza anahtarlama kaldırılırsa (`slot[sig]` kısayolu silinirse) bu çivi
    ötmeli — okuma sayacı 1 yerine 2/3 olur."""
    dataset._cache.clear()
    index_df = make_bars(n=300)
    okuma_sayaci = {"n": 0}

    def sahte_load_many(tickers, start, end, use_cache=True, **k):
        okuma_sayaci["n"] += 1
        return {t: make_bars(n=300) for t in tickers}

    monkeypatch.setattr(data, "load_bars", lambda t, s, e, **k: index_df.copy())
    monkeypatch.setattr(data, "load_many", sahte_load_many)

    uni_a = ["AAPL", "MSFT"]
    bars1, _ = dataset.load(use_cache=True, universe=uni_a)
    assert okuma_sayaci["n"] == 1

    bars2, _ = dataset.load(use_cache=True, universe=uni_a)          # AYNI imza — DİSKE GİTMEMELİ
    assert okuma_sayaci["n"] == 1, "aynı evrenle ikinci çağrı yine diske gitti — önbellek isabet etmedi"
    assert bars2 is bars1

    uni_a_karisik_sira = ["MSFT", "AAPL"]                             # SIRA farklı, İMZA aynı olmalı
    bars2b, _ = dataset.load(use_cache=True, universe=uni_a_karisik_sira)
    assert okuma_sayaci["n"] == 1, "sıra-duyarsız imza beklenirdi (tuple(sorted(...)))"
    assert bars2b is bars1

    uni_b = ["NVDA", "AMD"]
    bars3, _ = dataset.load(use_cache=True, universe=uni_b)          # FARKLI imza — YENİ okuma
    assert okuma_sayaci["n"] == 2, "farklı evren AYRI bir okuma üretmeli"
    assert set(bars3) == set(uni_b) and bars3 is not bars1

    dataset.load(use_cache=False, universe=uni_a)                    # use_cache=False İSABETİ ATLAR
    assert okuma_sayaci["n"] == 3
    dataset._cache.clear()


def test_load_custom_kurtarma_dali_uni_alt_kumesi_dondurur(sandbox_state, monkeypatch):
    """Ö-3: endeks-bütünlük kurtarma dalı (`have_good`) `custom` iken REPLAY-ölçekli süperseti (251,
    endeks-çıkışı sembol DAHİL) DÖNMEZ — dönen anahtar kümesi HER ZAMAN `universe`nin alt kümesidir.
    `_cache["index"]`in dolu olması TİPİKTİR (review: `arming._measure`/`hermes_runtime.
    _warmup_sprint` aynı süreçte parametresiz `load()` çağırıp önbelleği REPLAY tabanıyla ısıtır).
    Mutasyon: kurtarma dalı `custom`a bakmadan `_cache["bars"], _cache["index"]` dönecek şekilde eski
    hâline alınırsa bu çivi ötmeli (ROKU sızar)."""
    dataset._cache.clear()
    index_df = make_bars(n=300)
    monkeypatch.setattr(data, "load_bars", lambda t, s, e, **k: index_df.copy())
    monkeypatch.setattr(data, "load_many", lambda tickers, s, e, use_cache=True, **k:
                         {t: make_bars(n=300) for t in tickers})

    # 1) ISINMA: bir REPLAY çağrısı (parametresiz — arming/hermes_runtime deseni) önbelleği REPLAY
    # tabanıyla doldurur; bu evren ROKU'yu (endeks-çıkışı) İÇERİR (gerçek REPLAY_UNIVERSE'in KENDİSİ).
    bars_replay, _ = dataset.load(use_cache=False)
    assert "ROKU" in bars_replay and set(bars_replay) == set(data.REPLAY_UNIVERSE)

    # 2) ENDEKS BOZULUR: aynı süreçte custom (canlı) bir çağrı gelir — sert bütünlük kapısı düşer.
    monkeypatch.setattr(dataset, "_index_hard_issues",
                        lambda idx: [{"severity": "hard", "code": "kirli_test"}])
    dar = ["AAPL", "MSFT"]                                            # ROKU bu evrende YOK
    bars_kurtarma, idx_kurtarma = dataset.load(use_cache=True, universe=dar)

    assert set(bars_kurtarma) <= set(dar), \
        f"kurtarma dalı istenenin ÜSTÜNDE döndü: {set(bars_kurtarma) - set(dar)}"
    assert "ROKU" not in bars_kurtarma, "endeks-çıkışı sembol kurtarma dalından CANLI yola sızdı"
    assert idx_kurtarma is not None
    dataset._cache.clear()


def test_load_custom_kurtarma_dali_kendi_imzasini_onceler(sandbox_state, monkeypatch):
    """`_kirp_kurtarma()` ÖNCE kendi imzalı önceki sonucuna bakar (REPLAY'i kırpmadan önce) — aynı
    custom evren daha önce başarıyla yüklenmişse, endeks bozulduğunda o TAM sonuç (REPLAY'den
    kırpılmış bir alt küme değil) geri gelir. `use_cache=False` İLE OUTER imza-kısayolu BİLEREK
    ATLANIR: aksi hâlde `if use_cache and sig in slot: return slot[sig]` kısayolu `_index_hard_
    issues`e HİÇ uğramadan döner ve bu test yanlışlıkla `test_load_custom_cache_ayni_imza_diskten_
    okumaz`ı tekrar etmiş olur — asıl hedeflenen kod yolu (`_kirp_kurtarma` içindeki `slot.get(sig)`
    önceliği) hiç çalışmamış olur (bu YANLIŞ hâliyle bir kez yazılıp mutasyonla yakalandı)."""
    dataset._cache.clear()
    index_df = make_bars(n=300)
    monkeypatch.setattr(data, "load_bars", lambda t, s, e, **k: index_df.copy())
    monkeypatch.setattr(data, "load_many", lambda tickers, s, e, use_cache=True, **k:
                         {t: make_bars(n=300) for t in tickers})

    # 1) REPLAY ISINMASI: `_cache["index"]` dolar — `have_good` şartı bundan sonra sağlanır.
    dataset.load(use_cache=False)

    # 2) Aynı custom evren BİR KEZ başarıyla yüklenir (`slot[sig]` dolar).
    dar = ["AAPL", "MSFT", "NVDA"]
    bars_once, _ = dataset.load(use_cache=True, universe=dar)
    assert set(bars_once) == set(dar)

    # 3) Endeks bozulur; `use_cache=False` OUTER kısayolu atlar — kurtarma dalına GERÇEKTEN girilir.
    monkeypatch.setattr(dataset, "_index_hard_issues",
                        lambda idx: [{"severity": "hard", "code": "kirli_test"}])
    bars_kurtarma, _ = dataset.load(use_cache=False, universe=dar)
    assert bars_kurtarma is bars_once, "kendi imzalı önbellek isabeti yerine REPLAY kırpması izlendi"
    dataset._cache.clear()


def test_marketstream_armed_plani_da_korur(sandbox_state, monkeypatch):
    """Bulgu 4: `subscribed_symbols()` artık `armed` (onaylı, henüz dolmamış plan) bir endeks-çıkışı
    sembolü de LIVE_UNIVERSE dışına düşürmez — WS aboneliğinde sıcak-fiyat kör noktası kapandı."""
    from meridian import marketstream
    store.write_json("portfolio.json", {"armed": [{"ticker": "SNAP", "id": "p1"}]})

    out = marketstream.subscribed_symbols()

    assert "SNAP" in out, "armed plandaki endeks-çıkışı sembol WS aboneliğinden düşmüş"
    diger_9 = BEKLENEN_10 - {"SNAP"}
    assert not (set(out) & diger_9), "pozisyonsuz/armed-dışı endeks-çıkışı semboller de sızmış"


def test_marketstream_pozisyonlar_hala_en_basta(sandbox_state, monkeypatch):
    """Regresyon: `_canli_korunan_evren()`e geçiş, 'pozisyonlar EN BAŞTA' sırasını BOZMAMALI —
    marketstream'in kendi manuel `positions` öneki hâlâ önde durur."""
    from meridian import marketstream
    store.write_json("portfolio.json", {"positions": {"ZZZZ": {"qty": 1}}})

    out = marketstream.subscribed_symbols()

    assert out[0] == "ZZZZ", "pozisyon artık listenin başında değil"


def test_load_live_universe_suresi_sicak_soguk(sandbox_state, monkeypatch, capsys):
    """K-1 ÖLÇÜMÜ (review'in sorduğu soru): tek `load(universe=LIVE_UNIVERSE)` çağrısının süresi —
    SOĞUK (238 sentetik CSV'yi GERÇEK diskten okur + sanitize eder) vs SICAK (evren-imzalı önbellek
    isabeti, disk YOK). Ölçülen şey `_cache` isabet/ıskasının maliyetidir (ağ zinciri değil — o
    canlıda ayrı, bu ölçümün kapsamı dışında); sayı raporda kullanılır, sonuca dair sıkı bir eşik
    yoktur (ortam-bağımlı bir zamanlama testi CI'da gevşek olmalı)."""
    dataset._cache.clear()
    uni = list(data.LIVE_UNIVERSE)
    index_df = make_bars(n=300)

    bars_dir = sandbox_state / "bars"
    for t in uni:
        make_bars(n=300).to_csv(bars_dir / f"{t}.csv", index=False)

    def gercek_disk_load_many(tickers, start, end, use_cache=True, **k):
        out = {}
        for t in tickers:
            df = pd.read_csv(bars_dir / f"{t}.csv", parse_dates=["date"])
            df2, _ = data.sanitize_bars(df, t)
            if df2 is not None and len(df2) > 50:
                out[t] = df2
        return out

    monkeypatch.setattr(data, "load_bars", lambda t, s, e, **k: index_df.copy())
    monkeypatch.setattr(data, "load_many", gercek_disk_load_many)

    t0 = time.perf_counter()
    bars_cold, _ = dataset.load(use_cache=True, universe=uni)
    t_soguk = time.perf_counter() - t0

    t1 = time.perf_counter()
    bars_warm, _ = dataset.load(use_cache=True, universe=uni)
    t_sicak = time.perf_counter() - t1

    assert set(bars_cold) == set(uni)
    assert bars_warm is bars_cold, "sıcak çağrı önbellek isabetiyle AYNI nesneyi dönmeli"
    with capsys.disabled():
        oran = t_soguk / max(t_sicak, 1e-9)
        print(f"\n[TSK-116 r3 ÖLÇÜM] evren={len(uni)} SOĞUK={t_soguk * 1000:.1f}ms "
              f"SICAK={t_sicak * 1000:.3f}ms oran≈{oran:.0f}x (sandbox, sentetik CSV, ağ YOK)")
    dataset._cache.clear()
