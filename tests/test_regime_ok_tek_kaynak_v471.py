"""test_regime_ok_tek_kaynak_v471.py — TSK-184: KÜRESEL rejim kapısı yüklemi TEK KAYNAKTIR.

ÖLÇÜLEN BOŞLUK (Rol-1, 2026-09-13). `rj["regime"] in ("trend_up", "chop") and
rj["exposure_budget_pct"] > 0` yüklemi DÖRT yerde BİREBİR kopyaydı: `backtest.replay` (replay
döngüsü), `loop.daily_cycle` (canlı günlük döngü), `shadow_lifecycle._seed` (gölge-v2 tohumu) ve
EDG-2026-088 PK (3) şasisi (`research/olcumler/edg088_golge_pilot/pk3_selef.py`, `rejim_of`).
Dördü de AYNI gerçeği söylüyordu ve TEK-KAYNAK YASASI'nın (CLAUDE.md §4) tarif ettiği sınıf tam
olarak budur: aynı kuralın iki kopyası SESSİZCE ayrışır. Bu kapı canlı kararı belirler —
`regime_flip` çıkışları ve yeni-giriş taramasının açık/kapalı hükmü buradan gelir — yani ayrışma
"biri hâlâ chop'ta işlem açıyor, öteki açmıyor" demektir ve HİÇBİR çivi bunu görmezdi.

BU DOSYANIN ÖLÇTÜĞÜ ÜÇ ŞEY:
  (A) DOĞRULUK TABLOSU — `regime.regime_ok` dört rejim × bütçe eksenini bugünküyle AYNI okur.
      Eksik alan davranışı DA aynıdır ve TASARIMDIR: `regime` yoksa KeyError; `regime` AÇIK bir
      rejimken `exposure_budget_pct` yoksa KeyError; `regime` KAPALI bir rejimken ikinci alan HİÇ
      okunmaz (kısa devre) ve KeyError ATILMAZ. Sessizce False döndürmek bir DAVRANIŞ DEĞİŞİKLİĞİ
      olurdu: bozuk bir rejim belgesi "kapı kapalı" diye sessizce yutulur, motor gürültüsüz yanlış
      karar verirdi (YASA 4 — sessiz yutma yok).
  (B) AYRIŞMA ÇİVİSİ — literal yüklem metni dört çağıranın HİÇBİRİNDE kalmamıştır ve dördü de
      `regime.regime_ok` ÇAĞIRIR. Bu çivi olmadan tek-kaynak bir NİYETTİR, bir YAPI değil: yarın
      biri "tek satır, elde yazayım" der ve kopya geri gelir.
  (C) SABİTİN DONUKLUĞU — `regime.REGIME_OK_REJIMLERI` kümesi kartlarda/ölçümlerde çapa olarak
      kullanılır; değeri burada AÇIKÇA donar, tabloyla birlikte değişmesi gerekir.

BAYT-ÖZDEŞLİK (kart sınıfı: motor karar yolu). Yüklem DEĞİŞMEDİ, taşındı — dolayısıyla replay
çıktısının bayt bayt aynı kalması BEKLENTİ değil ŞARTTIR. Kanıt bu dosyada değil, mevcut replay
determinizm çivilerindedir (`test_replay_sweep_v277.py`, `test_backtest_audit_v23.py`,
`test_golge_v2_yasam_dongusu_v132.py`) ve AŞAĞIDAKİ (D) BÖLÜMÜNDE: replay defterinin kanonik
sha256'sı değişiklikten ÖNCE ölçülüp donduruldu. Ölçüm yolunun (PK (3) şasisi) karşılığı TSK-184
raporundaki yeniden koşumdur (6/6 + R aynı).
"""
from __future__ import annotations

import pathlib

import pytest

from meridian import regime

REPO = pathlib.Path(__file__).resolve().parents[1]

#: Yüklemin DÖRT eski evi. Ayrışma çivisi bu listeyi tarar — yeni bir çağıran doğarsa buraya
#: EKLENİR (liste kopya değil, KAPSAM beyanıdır: taranmayan dosyada kopya sessizce yaşar).
CAGIRANLAR = (
    "meridian/backtest.py",
    "meridian/loop.py",
    "meridian/shadow_lifecycle.py",
    "research/olcumler/edg088_golge_pilot/pk3_selef.py",
)

#: BEŞİNCİ KOPYA — TSK-184 SIRASINDA BULUNDU (Rol-1 ölçümü DÖRT diyordu; gerçek BEŞTİ ve beşincisi
#: ZATEN AYRIŞMIŞTI). `shadow_variants.record_cycle`ın gölge-v2 yedek dalı aynı yüklemi `.get`
#: ile HOŞGÖRÜLÜ yazıyordu: eksik/None alanda KeyError yerine sessizce False. Sıkı yükleme
#: çevirmek DAVRANIŞ DEĞİŞİKLİĞİ olurdu (KeyError dıştaki `except`e düşer, gölge-v2 turu sessizce
#: atlanır), o yüzden hoşgörü KORUNDU ve BEYAN EDİLDİ — ayrışan yalnız hoşgörü, açık rejim KÜMESİ
#: artık tek kaynaktan gelir. Bu dosya bu yüzden İKİ liste taşır: küme literali BEŞİNDE de
#: yasaktır, `regime_ok` çağrısı yalnız DÖRDÜNDE aranır.
HOSGORULU_VARYANT = "meridian/shadow_variants.py"

#: Küme literalinin YASAK olduğu her yer (dört çağıran + hoşgörülü varyant).
LITERAL_TARANAN = (*CAGIRANLAR, HOSGORULU_VARYANT)

#: Yasak literal — kopyanın İMZASI. Metin burada TEK parça olarak durur ki aramanın ne aradığı
#: okunabilir olsun; taranan dosyalarda bu metnin BULUNMAMASI hükümdür.
YASAK_LITERAL = '("trend_up", "chop")'


def _kaynak(rel: str) -> str:
    return (REPO / rel).read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# (A) DOĞRULUK TABLOSU — bugünkü davranışın BİREBİR kopyası
# ---------------------------------------------------------------------------
#: (rejim, bütçe) → beklenen. Dört rejimin HEPSİ ve bütçenin üç bölgesi (pozitif / sıfır /
#: negatif) çarpılarak sayılır — "chop ama bütçe 0" hücresi tam da kapının canlıda en sık
#: kapandığı hücredir (`build_regime_json`: skor `min_exposure_score` altındaysa bütçe 0'a düşer).
TABLO = [
    ("trend_up", 80, True),
    ("trend_up", 1, True),
    ("trend_up", 0, False),
    ("trend_up", -1, False),
    ("chop", 45, True),
    ("chop", 1, True),
    ("chop", 0, False),
    ("chop", -5, False),
    ("trend_down", 15, False),
    ("trend_down", 0, False),
    ("high_vol", 25, False),
    ("high_vol", 0, False),
]


@pytest.mark.parametrize("rejim,butce,beklenen", TABLO)
def test_dogruluk_tablosu(rejim, butce, beklenen):
    assert regime.regime_ok({"regime": rejim, "exposure_budget_pct": butce}) is beklenen


def test_sabit_kume_DONUK():
    """Küme değişirse tablo da değişmek ZORUNDA — sabit sessizce genişlemesin."""
    assert regime.REGIME_OK_REJIMLERI == ("trend_up", "chop")
    # Sabit modülün kendi rejim adlarından türer (ikinci bir literal kopya DEĞİL).
    assert regime.REGIME_OK_REJIMLERI == (regime.TREND_UP, regime.CHOP)


def test_build_regime_json_ciktisi_YUKLEME_GIRER():
    """Üretici ile tüketici AYNI alan adlarını konuşuyor mu — parite, varsayım değil."""
    import pandas as pd

    rj = regime.build_regime_json(pd.DataFrame(), {}, "2026-09-13")
    assert {"regime", "exposure_budget_pct"} <= set(rj)
    assert regime.regime_ok(rj) is (rj["regime"] in regime.REGIME_OK_REJIMLERI
                                    and rj["exposure_budget_pct"] > 0)


# ---- eksik alan: BUGÜNKÜ davranış (ölçüldü 2026-09-13, taban çıkışı korunur) ----
def test_eksik_regime_alani_KeyError():
    with pytest.raises(KeyError) as e:
        regime.regime_ok({"exposure_budget_pct": 80})
    assert e.value.args[0] == "regime"


def test_eksik_butce_alani_ACIK_REJIMDE_KeyError():
    with pytest.raises(KeyError) as e:
        regime.regime_ok({"regime": "trend_up"})
    assert e.value.args[0] == "exposure_budget_pct"


def test_eksik_butce_alani_KAPALI_REJIMDE_KISA_DEVRE():
    """Kısa devre KORUNUR: rejim kümede değilse ikinci alan HİÇ okunmaz."""
    assert regime.regime_ok({"regime": "high_vol"}) is False
    assert regime.regime_ok({"regime": "bilinmeyen_rejim"}) is False


def test_donen_tip_BOOL():
    """`is True`/`is False` sözleşmesi: çağıranlar bu değeri `regime_ok: bool` olarak taşıyor."""
    for rj in ({"regime": "chop", "exposure_budget_pct": 45},
               {"regime": "chop", "exposure_budget_pct": 0},
               {"regime": "trend_down", "exposure_budget_pct": 99}):
        assert type(regime.regime_ok(rj)) is bool


# ---------------------------------------------------------------------------
# (B) AYRIŞMA ÇİVİSİ — literal kopya hiçbir çağıranda KALMAZ
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("rel", LITERAL_TARANAN)
def test_literal_yuklem_CAGIRANDA_YOK(rel):
    """Kopyanın geri gelmesi SESSİZ olamaz. Muafiyet yok: yüklem tek evde durur."""
    metin = _kaynak(rel)
    kotu = [i for i, s in enumerate(metin.splitlines(), 1) if YASAK_LITERAL in s]
    assert not kotu, (
        f"{rel}: rejim kümesi literali geri gelmiş (satır {kotu}) — "
        f"`regime.REGIME_OK_REJIMLERI` / `regime.regime_ok` kullanılmalı")


@pytest.mark.parametrize("rel", CAGIRANLAR)
def test_cagiranlar_TEK_KAYNAGI_CAGIRIR(rel):
    metin = _kaynak(rel)
    assert "regime_ok(" in metin, f"{rel}: `regime_ok` çağrısı yok"
    assert ("regime_mod.regime_ok(" in metin or "regime.regime_ok(" in metin), \
        f"{rel}: yüklem tek kaynaktan (`regime.regime_ok`) çağrılmıyor"


def test_hosgorulu_varyant_KUMEYI_TEK_KAYNAKTAN_ALIR():
    """Beşinci kopya: hoşgörü KORUNUR (`.get`), küme TEK KAYNAKTAN gelir — ikisi de ölçülür."""
    metin = _kaynak(HOSGORULU_VARYANT)
    assert "regime_mod.REGIME_OK_REJIMLERI" in metin, \
        f"{HOSGORULU_VARYANT}: açık rejim kümesi tek kaynaktan alınmıyor"
    assert 'regime.get("exposure_budget_pct") or 0) > 0' in metin, \
        f"{HOSGORULU_VARYANT}: hoşgörülü (.get) dal DEĞİŞMİŞ — davranış değişikliği, beyan gerekir"


def test_tek_GOVDE_var():
    """Yüklemin gövdesi YALNIZ `regime.py`de — ikinci bir `def regime_ok` doğarsa kırılır."""
    sayim = {}
    for kok in ("meridian", "research/olcumler/edg088_golge_pilot"):
        for f in sorted((REPO / kok).rglob("*.py")):
            n = f.read_text(encoding="utf-8").count("def regime_ok(")
            if n:
                sayim[str(f.relative_to(REPO))] = n
    assert sayim == {"meridian/regime.py": 1}, f"beklenmeyen gövde(ler): {sayim}"


# ---------------------------------------------------------------------------
# (D) BAYT-ÖZDEŞLİK — replay defteri DEĞİŞMEDİ
# ---------------------------------------------------------------------------
# Yüklem taşındı, DEĞİŞMEDİ. Bu bölümün işi o cümleyi bir İDDİA olmaktan çıkarıp ÖLÇÜM yapmaktır:
# `backtest.replay` sentetik ve ağsız bir evrende koşar, ürettiği defterin (işlemler + sermaye
# eğrisi + plan kaydı + ret sayaçları) kanonik sha256'sı DONDURULMUŞTUR. Çapa değeri TSK-184
# DEĞİŞİKLİĞİNDEN ÖNCEKİ `backtest.py` ile ölçüldü (literal yüklem hâlâ yerindeyken) — yani
# "sonucu gördükten sonra yazılmış" bir eşik değil, ÖNCEKİ dünyanın imzasıdır.
#
# FIXTURE SEÇİMİ ÖLÇÜLDÜ, SEÇİLMEDİ (2026-09-13). İlk deneme `test_engine.py`in replay smoke
# evreniydi; MUTASYON onu ELEDİ: `REGIME_OK_REJIMLERI`den "chop" düşürüldüğünde özet DEĞİŞMEDİ,
# çünkü o evren SIFIR işlem üretiyor ve `regime_ok` replay'de YALNIZ açık pozisyon yönetimine
# (`strategy.manage_position` → `regime_flip` çıkışı) girer — giriş taraması bütçeyi ayrıca ve
# BAĞIMSIZ okur. Yani çivi yeşildi ama KÖRDÜ. `_mini_evren` (v124'ün sıfır-etki çivisinin
# evreni) ölçüldü ve seçildi: kapı 174/340 seansta çevriliyor VE defterdeki tek çıkış
# `regime_flip` — yüklemin replay'de gerçekten okunduğu tek yol.
MINI_EVREN_TICKERS = ("AAPL", "MSFT", "NVDA", "JPM", "XOM", "UNH")
REPLAY_PENCERE = ("2022-01-03", "2023-04-28")
REPLAY_OZET_SHA256 = "93475dc96637028d790bc5a02608423e73a68df4acf3a943d3510cae4f70d6ff"
#: ↑ ÖLÇÜLDÜ 2026-09-13, TSK-184 ÖNCESİ `backtest.py` ile (literal yüklem satırı hâlâ yerinde).


def _mini_evren(n=340, seed=4):
    from tests.conftest import make_bars

    bars = {t: make_bars(n, seed=seed + i, trend=0.0008, breakout_at=200 + 7 * i)
            for i, t in enumerate(MINI_EVREN_TICKERS)}
    return bars, make_bars(n, seed=seed + 99, trend=0.0005)


def _replay_smoke():
    from meridian import backtest, config

    bars, index = _mini_evren()
    return backtest.replay(config.default_strategy()["params"], bars, index, config.goal(),
                           *REPLAY_PENCERE)


def _ozet(res) -> str:
    import hashlib
    import json
    kanon = json.dumps({"trades": res.trades, "equity": res.equity,
                        "plan_log": res.plan_log, "candidate_log": res.candidate_log,
                        "entry_rejects": res.entry_rejects, "earnings_gate": res.earnings_gate},
                       sort_keys=True, default=str)
    return hashlib.sha256(kanon.encode("utf-8")).hexdigest()


def test_replay_defteri_BAYT_OZDES():
    assert _ozet(_replay_smoke()) == REPLAY_OZET_SHA256


def test_replay_smoke_YUKLEMI_GERCEKTEN_OKUR():
    """Çivinin ISIRDIĞINI ölçer — üç koşul birden, yoksa özet yüklemden bağımsız donar.

    (1) kapı fixture'da hem AÇIK hem KAPALI seanslar üretir, (2) defter BOŞ DEĞİLDİR,
    (3) en az bir çıkış `regime_flip`tir — `regime_ok`un replay'deki TEK etki yolu.
    """
    import pandas as pd

    from meridian import config, regime as regime_mod

    _, index = _mini_evren()
    params = config.default_strategy()["params"]
    i2 = index.set_index(pd.DatetimeIndex(index["date"]))
    hukum = [regime.regime_ok(regime_mod.build_regime_json(
        i2.loc[:d].reset_index(drop=True), params, str(d.date())))
        for d in i2.index if REPLAY_PENCERE[0] <= str(d.date()) <= REPLAY_PENCERE[1]]
    assert any(hukum) and not all(hukum), \
        f"fixture kapıyı çevirmiyor (açık={sum(hukum)}/{len(hukum)}) — çivi kör"

    res = _replay_smoke()
    assert res.trades, "defter boş — bayt-özdeşlik çivisi boş defter üzerinde kurulamaz"
    assert any(t.get("exit_reason") == "regime_flip" for t in res.trades), \
        "hiçbir çıkış `regime_flip` değil — `regime_ok` bu defterde HİÇ okunmuyor, çivi kör"
