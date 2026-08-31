"""test_wpd_kardes_pit_v185.py — KARDEŞ-PIT DÜZELTMESİ: cf_backfill + shadow_variants
(2026-08-03; kardeşi `backtest.replay` bugün 89d4497'de kapandı, çivisi test_wpd_takvim_kapisi_v184).

ÖLÇÜLEN İHLAL (research/olcumler/wpd_earnings_failopen/RAPOR.md §4b, açık bilet):
`state/earnings.csv` PIT DEĞİLDİR — bugünden ~21 gün İLERİ bakan, sembol başına 1,0 tarih tutan bir
snapshot'tır; geçmiş çapa biriktirmez. Buna rağmen İKİ kardeş modül onu TARİHSEL bir karara
uyguluyordu:
  · `cf_backfill._plans_for_session` (kardeş-PIT bloğu) — `in_blackout(ticker, dstr)`, `dstr`
    2022→bugün aralığında bir seans. ÇAPA SEMBOLE ÇEVRİLDİ (2026-08-31): burada dosya adı + satır
    numarası yazıyordu ve EDG-2026-062'nin PIT sevki o dosyaya satır ekleyince çapa bir yorum
    satırına kaydı — `codelaw.stale_line_anchors` ötünce görüldü. (Eski çapayı bu şerhe AYNEN
    yazmak da olmazdı: tarayıcı onu yeni bir çapa sanar ve aynı kırmızıyı bir satır aşağıda
    yeniden üretirdi — ölçüldü, aynı turda.) Satır çapası kayar; sembol kaymaz,
  · `shadow_variants.in_blackout` — `in_blackout(ticker, date)`, `date` `shadow_lifecycle._seed`
    bacağında GEÇMİŞ seans.
Sonuç replay'dekiyle aynı sınıftı: kapı bu motorlarda ÖLÜ (ölçüldü: replay tarafında 390 planın
380'i, %97,4, yapısal olarak False dönüyordu) ama defter onu UYGULANMIŞ gibi taşıyordu.

DÜZELTMENİN İKİ AYRI BİÇİMİ — ve neden aynı olamazlar:
  A) `cf_backfill` TAMAMEN tarihseldir (canlı yolu YOKTUR) → `in_blackout` çağrısı SÖKÜLDÜ,
     tıpkı `backtest.replay`de olduğu gibi. Sayaç `run()` sonucunda (`earnings_gate`).
  B) `shadow_variants._judge` İKİ yerden çağrılır: (a) `record_cycle` — CANLI EOD turu, takvim
     PIT'tir, kapı aynen çalışmalıdır (canlı ile kıyas defterin ASIL sorusudur; kapıyı gölgede
     söküp canlıda bırakmak, ayrışmayı VARYANT farkı gibi okutan sahte bir sinyal üretirdi);
     (b) `shadow_lifecycle._seed` — GEÇMİŞ seanslar. Bu yüzden burada çağrı SÖKÜLMEZ, PIT
     KOŞULUNUN İÇİNE alınır (`_CANLI_TUR` çapası) ve tarihsel bacakta hiç çalışmaz.

BU TESTİN ÇİVİLERİ (v184'ün deseni): davranış TEK BAŞINA yetmez — bir gün koşul dışına taşınırsa
davranış testi geçmeye devam ederdi. O yüzden her iddia hem DAVRANIŞLA hem YORUMSUZ KAYNAK
TARAMASIYLA (`_kod`) çakılıdır.
"""
from __future__ import annotations

import datetime as dt
import inspect
import io
import re
import shutil
import tokenize
import types
from pathlib import Path

import pytest

from meridian import cf_backfill, config, earnings, guard, loop, shadow_variants as sv

ROOT = Path(__file__).resolve().parent.parent


# ==================================================================================================
# yardımcılar
# ==================================================================================================
def _kod(fn) -> str:
    """Kaynağın YORUMSUZ hâli (v184'ten aynen). Yorumda geçen bir ad, o adın ÇAĞRILDIĞI anlamına
    gelmez — ve bu turda iki dosyanın da gerekçe blokları 'in_blackout' kelimesini içeriyor."""
    out = []
    for satir in inspect.getsource(fn).splitlines():
        govde = satir.split("#", 1)[0] if "#" in satir else satir
        if govde.strip():
            out.append(govde)
    return "\n".join(out)


#: KOD OLMAYAN token'lar — `_dosya_kodu` bunları BOŞLUĞA çevirir. `FSTRING_MIDDLE` yalnız
#: f-string'in DÜZ METİN parçasıdır; `{...}` içindeki ifade NAME/OP olarak gelir ve KALIR.
_KOD_DISI_TOKENLER = frozenset({tokenize.COMMENT, tokenize.STRING, tokenize.FSTRING_MIDDLE})


def _dosya_kodu(yol: Path) -> str:
    """Bir dosyanın yalnız KOD'u — yorumlar ve dizge METİNLERİ boşluğa çevrilmiş hâli. "Modül
    erişimi var mı" sorusunun üzerinde ölçüldüğü metin budur.

    NEDEN METİNLER ELENİR (2026-08-31, v345 turu): aşağıdaki `"earnings."` yüklemi bir PROXY'dir —
    "nokta var, demek ki modüle erişiliyor". Yanlış-pozitif biçimi bu dosyada zaten biliniyordu
    (`earnings_gate` bir METİN, erişim değil) ve o gün ada bakılarak elle geçilmişti. v345'te
    İKİNCİ biçim doğdu ve elle geçilemez: `eff["earnings.pit_arsiv"]` PIT dikişinin PARAM
    ANAHTARIDIR. Adı `strategy.py`nin dikişiyle BİREBİR aynı olmak zorundadır (tek-kaynak), yani
    "adı değiştir" bir seçenek değildi.

    NEDEN REGEX DEĞİL `tokenize` — VE BU FARK ÖLÇÜLDÜ (inceleme, 2026-08-31): bu yardımcının ilk
    yazımı dizge literallerini regex'le siliyordu ve f-ÖNEKLİ literalleri de bütün olarak
    siliyordu. Sonuç ölçüldü: `cf_backfill.py` gövdesinin %34'ü dedektörün göremediği bölgeye
    düştü ve `print(f"{earnings.in_blackout(t, d)}")` biçimindeki GERÇEK erişim, ESKİ yüklemde
    öterken YENİDE ötmez hâle geldi. Yani kazanç (yanlış-pozitifin kapanması) ölçülmüş, BEDEL
    (dedektörün körleşmesi) ölçülmemişti — bu deponun bedel yasasının ta kendisi.
    `tokenize` ikisini birden verir, çünkü ayrımı dilbilgisi yapar: Python 3.12'de (PEP 701)
    f-string'in `{...}` içindeki ifadesi ayrı NAME/OP token'larıdır, yalnız düz metin parçası
    `FSTRING_MIDDLE`tir. Yorum/dizge ayıklaması da AYNI geçişte ve doğru dilbilgisiyle olur —
    `split("#", 1)` sırasının kırılganlığı (içinde `#` geçen bir dizge) da böylece kapanır.
    Bu iddia BEYAN DEĞİL, ÇİVİLİDİR: `test_dosya_kodu_yuklemi_KENDI_KAPSAMINI_olcer`.

    KONUM KORUNUR (silme değil BOŞLUKLA doldurma): `from . import earnings` gibi satırların
    sütunu ve satır numarası değişmez, yoksa aşağıdaki ithal-satırı yüklemi (`startswith`)
    sessizce anlamını yitirirdi."""
    kaynak = yol.read_text()
    satirlar = [list(s) for s in kaynak.splitlines()]
    for tok in tokenize.generate_tokens(io.StringIO(kaynak).readline):
        if tok.type not in _KOD_DISI_TOKENLER:
            continue
        (sr, sc), (er, ec) = tok.start, tok.end
        for r in range(sr, er + 1):                      # çok satırlı literaller (üçlü tırnak)
            if not 1 <= r <= len(satirlar):
                continue
            satir = satirlar[r - 1]
            bas = sc if r == sr else 0
            son = ec if r == er else len(satir)
            for i in range(max(0, bas), min(len(satir), son)):
                satir[i] = " "
    return "\n".join("".join(s) for s in satirlar)


def _gun(delta: int) -> str:
    return (dt.date.today() + dt.timedelta(days=delta)).isoformat()


def _takvim_yaz(sandbox_state, satirlar) -> None:
    p = sandbox_state / "earnings.csv"
    p.write_text("ticker,date\n" + "".join(f"{t},{d}\n" for t, d in satirlar))
    earnings.clear_cache()


@pytest.fixture(autouse=True)
def _capa_temiz():
    """`_CANLI_TUR` SÜREÇ-İÇİ bir damgadır; testler arasında sızarsa bir testin canlı turu
    diğerinin tarihsel kararını PIT gösterir (v184'ün `_LAST_WINDOW` fikstürüyle aynı gerekçe)."""
    sv._CANLI_TUR["date"] = None
    yield
    sv._CANLI_TUR["date"] = None


def _sig(ticker: str, *, score: float = 80.0):
    """`_judge`in okuduğu ALANLARIN asgari taşıyıcısı (scan_all'ın EntrySignal'ı yerine): tarama
    bu testin konusu değil, KARARIN kazanç kapısına bağlı kısmı konusu."""
    return types.SimpleNamespace(
        ticker=ticker, setup="breakout_vcp", score=score, entry_trigger=100.0, stop=95.0,
        profit_target=115.0, r_per_share=5.0, rvol20=2.0, size_r=0.5, pivot=99.5, atr=2.0)


def _judge_cagir(monkeypatch, date: str, tickers=("AAPL",), eg=None):
    """`_judge`i gerçek kapı yasasıyla değil SABİT bir verdict'le koştur: ölçtüğümüz şey
    `classify_gate`in hükmü değil, kazanç kapısının o hükmü DEĞİŞTİRİP değiştirmediğidir.
    (Gerçek kapı bu fikstürde 'exposure_budget %0' diyerek hepsini NO_GO yapıyor ve karartmanın
    etkisi ölçülemez hâle geliyordu — sabit hüküm, ölçülen şeyi yalıtır.)"""
    monkeypatch.setattr(sv.guard, "classify_gate", lambda *a, **k: ("GO", []))
    goal = config.goal()
    limits = goal["limits"]
    bk = sv._book_state({"positions": {}, "equity": 100000.0, "peak_equity": 100000.0},
                        limits, lambda t: "tech")
    return sv._judge([_sig(t) for t in tickers], date, sector_of=lambda t: "tech",
                     max_corr_of=lambda t: 0.0, params={}, regime={"regime": "trend_up"},
                     goal=goal, limits=limits, version=1, bk=bk, eg=eg)


# ==================================================================================================
# A) cf_backfill — TAMAMEN TARİHSEL MOTOR: çağrı SÖKÜLDÜ
# ==================================================================================================
def test_cf_backfill_in_blackout_CAGIRMAZ():
    """ÇEKİRDEK ÇİVİ (yapı). Bugünün takvimini 2022→bugün seanslarına uygulayan yol TAMAMEN kapalı.
    Kaynak taraması YORUMSUZ gövde üzerinde: dosyanın gerekçe bloğu `in_blackout` kelimesini
    ADIYLA anıyor ve ham metin araması yanlış alarm verirdi (v184'ün ilk yazımındaki hata)."""
    assert "in_blackout" not in _kod(cf_backfill._plans_for_session)
    assert "in_blackout" not in _kod(cf_backfill.run)


def test_cf_backfill_modulun_TAMAMINDA_kapi_cagrisi_yok():
    """Sökme kısmi olmamalı: modülün başka bir yerinde (ör. `run` içine kopyalanmış bir 'hızlı
    kontrol') aynı çağrı yeniden doğarsa ihlal geri gelir, üstelik bu kez adı olmadan."""
    govde = _dosya_kodu(ROOT / "meridian" / "cf_backfill.py")
    assert "in_blackout" not in govde
    # `earnings.` = modüle ERİŞİM. Metin biçimleri (`earnings_gate` sayaç anahtarı,
    # `"earnings.pit_arsiv"` param anahtarı) bu yüklemin konusu değildir ve `_dosya_kodu`
    # tarafından elenir — gerekçe orada.
    assert "earnings." not in govde, "modül hâlâ çağrılıyor"
    importlar = [s for s in govde.splitlines() if s.startswith(("import ", "from "))]
    assert not [s for s in importlar if "earnings" in s], \
        "kullanılmayan içe aktarma kalmış — çağrı yolu hâlâ açık görünür"


def test_dosya_kodu_yuklemi_KENDI_KAPSAMINI_olcer(tmp_path):
    """DEDEKTÖRÜN KENDİSİNİ SINAYAN ÇİVİ — yukarıdaki yüklemin KAPSAMI beyan değil ÖLÇÜMDÜR.

    NEDEN VAR (inceleme 2026-08-31): `_dosya_kodu`nun ilk yazımı yanlış-pozitifi kapatırken
    f-string'lerin İÇİNİ de kör etmişti ve bunu hiçbir çivi göstermiyordu — dedektörün kaybı,
    tanımı gereği, hiçbir kırmızıyla haber verilmez. Kazanç ölçülüp bedel ölçülmediğinde
    körlüğün belirtisi HİÇBİR ŞEYDİR (bedel yasası). Bu çivi iki yönü birden çakar:
      · elenmesi GEREKENLER (docstring · yorum · param anahtarı · sayaç anahtarı · f-string'in
        DÜZ METİN parçası) gövdede KALMAZ,
      · görünmesi GEREKENLER (düz erişim VE f-string ifadesi içindeki erişim) gövdede KALIR.

    AYRICA BİR SÜRÜM VARSAYIMINI ÇAKAR: f-string ifadesinin ayrı token gelmesi PEP 701'dir
    (Python 3.12+). Yorumlayıcı geri alınırsa dedektör sessizce körleşmez — bu çivi öter."""
    ornek = tmp_path / "ornek_kaynak.py"
    ornek.write_text(
        'def f(t, d):\n'
        '    """docstring: earnings.in_blackout"""\n'
        '    # yorum: earnings.in_blackout\n'
        '    eff["earnings.pit_arsiv"] = True\n'
        '    out["earnings_gate"] = eg\n'
        '    duz = earnings.in_blackout(t, d)\n'
        '    print(f"{earnings.known(t)} · duz metin earnings.metinparcasi")\n'
        '    from . import earnings_pit\n', encoding="utf-8")
    kod = _dosya_kodu(ornek)
    # (a) YANLIŞ-POZİTİF KAPALI — metin biçimleri elenmiş
    assert "earnings.pit_arsiv" not in kod, "param anahtarı (dizge) elenmemiş"
    assert "earnings_gate" not in kod, "sayaç anahtarı (dizge) elenmemiş"
    assert "docstring" not in kod and "yorum:" not in kod, "docstring/yorum elenmemiş"
    assert "earnings.metinparcasi" not in kod, "f-string'in DÜZ METİN parçası elenmemiş"
    # (b) KÖRLÜK KAPALI — iki gerçek erişim biçimi de GÖRÜNÜR
    assert "earnings.in_blackout" in kod, "düz modül erişimi kayboldu — dedektör KÖR"
    assert "earnings.known" in kod, "f-string İÇİNDEKİ modül erişimi kayboldu — dedektör KÖR"
    # (c) KONUM KORUNDU — ithal yüklemi sütuna bakar (`startswith`), biçim bozulamaz
    assert "    from . import earnings_pit" in kod.splitlines()


def test_cf_backfill_karartma_VETOSU_URETMEZ(sandbox_state, monkeypatch):
    """DAVRANIŞ. Takvim BUGÜN karartmadaki bir sembolü gösterse bile, cf planlarının hiçbiri
    'kazanç öncesi karartma' gerekçesi almaz — çünkü kapı bu motorda hiç konuşmuyor."""
    for f in ("goal.yaml", "bounds.yaml", "strategy.yaml"):
        shutil.copy2(ROOT / "state" / f, sandbox_state / f)
    config.goal.cache_clear(); config.bounds.cache_clear()
    _takvim_yaz(sandbox_state, [("AAA", _gun(1)), ("BBB", _gun(2)), ("CCC", _gun(0))])

    from tests.conftest import make_bars
    from meridian.adapters import data as _data
    from meridian.backtest import SECTORS
    monkeypatch.setattr(_data, "REPLAY_UNIVERSE", ["SPY", "AAA", "BBB", "CCC"])
    monkeypatch.setattr(_data, "validate_bars", lambda df, t: (True, []))
    for t in ("AAA", "BBB", "CCC"):
        monkeypatch.setitem(SECTORS, t, "tech")
    # Kapı hükmü SABİTLENİR: ölçülen şey karartmanın hükmü değiştirip değiştirmediğidir.
    monkeypatch.setattr(guard, "classify_gate", lambda *a, **k: ("GO", []))
    # Tarama da SABİTLENİR: sentetik barların o gün sinyal üretip üretmemesi bu ölçümün konusu
    # değil, ÜRETİLEN planın karartma gerekçesi alıp almadığı konusu. (Rastgele bir fikstürün
    # "0 plan" üretmesi testi sessizce boşa çıkarırdı — aşağıdaki `assert plans` o tuzağın çivisi.)
    from meridian import strategy as _strategy
    assert "breakout_vcp" in _strategy.ARMED_SETUPS

    def _sahte_scan(tail, params, rsv, ticker=None):
        if ticker in ("AAA", "BBB", "CCC"):
            return {"breakout_vcp": _strategy.EntrySignal(
                ticker=ticker, setup="breakout_vcp", entry_trigger=100.0, pivot=99.5, stop=95.0,
                atr=2.0, rs_rating=90, score=80, profit_target=115.0, size_r=0.5,
                r_per_share=5.0, notes="v185 fikstürü", rvol20=2.0)}
        return {}
    monkeypatch.setattr(_strategy, "scan_all", _sahte_scan)

    per = {"SPY": make_bars(n=340, seed=1, trend=0.0004).set_index("date").sort_index(),
           "AAA": make_bars(n=340, seed=2, trend=0.0006, breakout_at=330).set_index("date").sort_index(),
           "BBB": make_bars(n=340, seed=3, trend=0.0003).set_index("date").sort_index(),
           "CCC": make_bars(n=340, seed=4, trend=0.0005, breakout_at=332).set_index("date").sort_index()}
    idx = per["SPY"]
    d = idx.index[-1]
    strat_cfg = config.load_strategy()
    eg: dict = {}
    plans, _armed, _dorm, _nm, rj = cf_backfill._plans_for_session(
        d, str(d.date()), per, idx, strat_cfg["params"], strat_cfg.get("params_by_regime"),
        config.goal(), 1, eg)
    assert rj is not None and plans, "fikstür plan üretmedi — test hiçbir şey kanıtlamaz"
    for p in plans:
        assert p["gate_verdict"] == "GO", "karartma (ya da başka bir kol) hükmü değiştirdi"
        assert not [r for r in p["gate_reasons"] if "karartma" in str(r)]
    # SAYAÇ ÜRETİLDİ ve plan sayısıyla TUTUYOR (uydurma değil, bağlı ölçüm)
    assert eg == {"plan": len(plans), "olculemedi_cf": len(plans)}


def test_cf_backfill_sayaci_SONUCA_baglanir():
    """YASA 6: sayaç üretilir VE taşınır. `run()` dönüşünde/olayında görünmezse, 'bu defterde
    karartma etkisi sıfır' bilgisi hiçbir okuyucuya ulaşmaz — sessiz sıfır, beyanlı sıfır değildir."""
    src = _kod(cf_backfill.run)
    # SÖZLEŞME ÇAKILIR, TİP PARAMETRESİ DEĞİL (2026-08-31, inceleme K2). Bu satır önce
    # `"eg: dict[str, int] = {}"` dizgesini birebir arıyordu ve o yüklem KENDİ konusunun dışına
    # taştı: v345 sayaca üçüncü bir anahtar (`pit_arsiv`, değeri bir SÖZLÜK) ekleyince ilan
    # ölçülebilir biçimde YANLIŞ hâle geldi — ama düzeltilemedi, çünkü bu çivi onu mekanik
    # olarak koruyordu. Bir çivinin, yanlış olduğu ÖLÇÜLMÜŞ bir beyanı ayakta tutması, çivinin
    # kendi amacının tersidir. Çivinin ölçmek istediği şey sayaç KABININ VARLIĞIYDI.
    assert re.search(r"\beg: dict\[str, [^\]]+\] = \{\}", src), "sayaç kabı yok"
    assert "version, eg)" in src, "sayaç seans döngüsüne geçirilmiyor"
    assert '"earnings_gate": eg' in src, "sayaç `out` sözlüğüne (ve cf_backfill_done olayına) girmiyor"


def test_cf_backfill_DONUS_BESLISI_korunur():
    """Arity sözleşmesi: `_plans_for_session` hâlâ beşli döner ve sayaç OPSİYONEL bir parametredir.
    Dönüşü altılıya çıkarmak `tests/test_cf_backfill_v14.py`i, yani bu düzeltmeyle ilgisiz bir
    ölçümü kırardı — düzeltmenin bedeli kendi kapsamının dışına taşmamalı."""
    sig = inspect.signature(cf_backfill._plans_for_session)
    assert sig.parameters["eg"].default is None
    assert list(sig.parameters)[:8] == ["d", "dstr", "per", "idx", "params", "by_regime",
                                        "goal", "version"]


# ==================================================================================================
# B) shadow_variants — İKİ BACAK: canlı KORUNUR, tohum SUSAR
# ==================================================================================================
def test_shadow_canli_turda_kapi_AYNEN_calisir(sandbox_state, monkeypatch):
    """CANLI-YOL-KORUNDU ÇİVİSİ (davranış). Çapa turun tarihine eşitken takvim PIT'tir: veto da,
    'known' etiketi de aynen durur. Bu test olmadan 'temizlik' bir gün gölge kapısını da söker ve
    varyant seti canlıdan daha CÖMERT olur — defterin ayrışma sayısı sessizce anlamsızlaşırdı."""
    _takvim_yaz(sandbox_state, [("AAPL", _gun(1))])
    bugun = _gun(0)
    sv._CANLI_TUR["date"] = bugun
    judged, armed, _plans = _judge_cagir(monkeypatch, bugun)
    assert judged[0]["verdict"] == "NO_GO"
    assert "kazanç öncesi karartma (earnings blackout)" in judged[0]["why"]
    assert judged[0]["earnings_blackout"] is True
    assert judged[0]["earnings_coverage"] == "known"
    assert armed == []


def test_shadow_TARIHSEL_turda_kapi_KONUSMAZ(sandbox_state, monkeypatch):
    """ÇEKİRDEK ÇİVİ (davranış). AYNI takvim, AYNI sembol — tek fark kararın tarihi. Tohum bacağında
    veto YOK, etiket 'known' DEĞİL: satır ölçemediğini SÖYLER."""
    _takvim_yaz(sandbox_state, [("AAPL", _gun(1))])
    sv._CANLI_TUR["date"] = _gun(0)                     # canlı tur BUGÜN
    judged, armed, _plans = _judge_cagir(monkeypatch, "2023-03-14")  # tohum seansı — GEÇMİŞ
    assert judged[0]["verdict"] != "NO_GO"
    assert not [w for w in judged[0]["why"] if "karartma" in str(w)]
    assert judged[0]["earnings_coverage"] == "olculemedi_seed"
    assert len(armed) == 1


def test_shadow_tarihsel_bacakta_blackout_FALSE_DEGIL_None(sandbox_state, monkeypatch):
    """'Karartma yok' ile 'ölçemedik' aynı şey değildir. `False` yazmak, bu turda kaldırılan
    `coverage:"known"` yalanının ikinci kopyası olurdu (UYDURMA YASAĞI: ölçülemeyen None + neden)."""
    _takvim_yaz(sandbox_state, [("AAPL", _gun(1))])
    sv._CANLI_TUR["date"] = _gun(0)
    judged, _armed, _plans = _judge_cagir(monkeypatch, "2023-03-14")
    assert judged[0]["earnings_blackout"] is None


def test_shadow_kapi_cagrisi_PIT_KOSULUNUN_ICINDE_yasar():
    """ÇEKİRDEK ÇİVİ (yapı) — v184'ün 'düşürme bloğu yüklemin içinde yaşar' testinin kardeşi.
    Davranış tek başına yetmez: çağrının `pit` koşuluna BAĞLI olduğu kanıtlanmalı, yoksa bir gün
    koşulun dışına taşınır ve tarihsel bacakta takvim yeniden konuşmaya başlar."""
    src = _kod(sv._judge)
    assert "pit = _takvim_pit_mi(date)" in src
    blok = src.split("if pit:")
    assert len(blok) == 2, "PIT koşulu yok ya da birden fazla yerde"
    dal = blok[1].split("else:")[0]
    assert "earnings.in_blackout(sig.ticker, date)" in dal, "çağrı PIT dalının dışında"
    assert src.count("earnings.in_blackout(") == 1, "kapının ikinci bir çağrı yolu var"


def test_shadow_yuklem_ADAY_BASINA_DEGIL_tur_basina_olculur():
    """`_takvim_pit_mi` TARİHE bakar; aday başına çağırmak 250 sembollük turda aynı cevabı 250 kez
    üretirdi (v184'ün 'tur başına bir yüklem' kuralı — ölçüme hiçbir şey katmayan sistem çağrısı)."""
    src = _kod(sv._judge)
    assert src.count("_takvim_pit_mi(") == 1
    assert src.index("_takvim_pit_mi(") < src.index("for sig in sigs:")


def test_shadow_capa_tur_ACILIRKEN_damgalanir():
    """ÇAPA SIRASI. Damga `_decide_variant` döngüsünden VE `_sl.run_cycle` (tohum bacağı onun
    İÇİNDE koşar) çağrısından önce atılmalı; sonra atılırsa tohum seansları kendini canlı sanar."""
    src = _kod(sv.record_cycle)
    assert '_CANLI_TUR["date"] = str(date)' in src
    assert src.index('_CANLI_TUR["date"]') < src.index("_decide_variant(")
    assert src.index('_CANLI_TUR["date"]') < src.index("run_cycle(")


def test_shadow_capasiz_cagri_ESKI_davranisi_korur(sandbox_state, monkeypatch):
    """BİLİNÇLİ VARSAYILAN: çapa yokken (üretimde böyle bir yol yok — `run_cycle`ın tek çağıranı
    `record_cycle`tır) kapı ESKİSİ gibi çalışır. Ters varsayılan, ölçülmemiş bir yolda kapıyı
    sessizce kapatırdı: bu turda kapatılan uydurmanın yön değiştirmiş hâli."""
    _takvim_yaz(sandbox_state, [("AAPL", _gun(1))])
    assert sv._CANLI_TUR["date"] is None
    judged, _armed, _plans = _judge_cagir(monkeypatch, _gun(0))
    assert judged[0]["verdict"] == "NO_GO", "çapasız yolda kapı susmuş — varsayılan ters çevrilmiş"
    assert judged[0]["earnings_coverage"] == "known"


def test_shadow_sayaci_SATIRA_ve_OZETE_baglanir(sandbox_state, monkeypatch):
    """YASA 6 zinciri: `_judge` sayar → `_decide_variant` satıra koyar → `summarize` okur →
    `render_summary` yazar. Halkanın herhangi bir yeri kopuksa '0 plan etkilendi' bir ÖLÇÜM değil
    yine bir BEYAN olur."""
    _takvim_yaz(sandbox_state, [("AAPL", _gun(1))])
    sv._CANLI_TUR["date"] = _gun(0)
    eg: dict = {}
    _judge_cagir(monkeypatch, _gun(0), tickers=("AAPL", "MSFT"), eg=eg)
    assert eg == {"plan": 2, "pit": 2}, "canlı turda hiçbir karar ölçümsüz kalmamalı"

    assert '"earnings_gate": eg' in _kod(sv._decide_variant)
    ozet = sv.summarize([{"date": "2026-08-03", "variant": "V1", "label": "x", "knobs": {},
                          "signal_n": 2, "would_arm_n": 1, "k_variants": 4,
                          "earnings_gate": {"plan": 2, "olculemedi_seed": 2}}])
    assert ozet["per_variant"]["V1"]["earnings_olculemedi_n"] == 2
    assert "KAZANÇ KAPISI KONUŞMADI" in sv.render_summary(
        [{"date": "2026-08-03", "variant": "V1", "label": "x", "knobs": {}, "signal_n": 2,
          "would_arm_n": 1, "k_variants": 4,
          "earnings_gate": {"plan": 2, "olculemedi_seed": 2}}])


def test_shadow_canli_defterde_olculemedi_SIFIR_olmali(sandbox_state, monkeypatch):
    """'0 SATIR ETKİLENDİ' ÇİVİSİ: v1 karar defteri CANLI turdan doğar, yani `olculemedi_seed`
    sayacı 0 kalmalıdır. 0'dan sapma, tohum satırlarının karar defterine sızdığını söyler."""
    _takvim_yaz(sandbox_state, [("AAPL", _gun(1))])
    sv._CANLI_TUR["date"] = _gun(0)
    eg: dict = {}
    _judge_cagir(monkeypatch, _gun(0), tickers=("AAPL", "MSFT", "KO"), eg=eg)
    assert eg.get("olculemedi_seed", 0) == 0


# ==================================================================================================
# C) CANLI MOTOR — kardeş temizliği canlı kapıyı SÖKMEDİ
# ==================================================================================================
def test_canli_motor_in_blackout_CAGIRMAYA_DEVAM_eder():
    """v184'ün aynı adlı testinin bu turdaki tekrarı ve gerekçesi aynı: düzeltme YALNIZ tarihsel
    yollardadır. Canlı motorda takvim PIT'tir ve karartma vetosu aynen durur."""
    src = _kod(loop.daily_cycle)
    assert "earnings.in_blackout(" in src
    assert 'greasons = list(greasons) + ["kazanç öncesi karartma (earnings blackout)"]' in src


def test_gates_applied_beyani_HALA_dogru():
    """Gölge defterinin satırı 'hangi kapılarla ölçüldüm' der. Canlı bacakta kapı UYGULANDIĞI için
    beyan doğru kalır — ama tohum bacağının istisnası aynı yerde YAZILI olmalı, yoksa beyan bir gün
    kapsamından geniş okunur (bayat beyan, yokluğundan beterdir)."""
    assert "earnings.in_blackout" in sv.GATES_APPLIED
    src = (ROOT / "meridian" / "shadow_variants.py").read_text()
    i = src.index("GATES_APPLIED = ")
    assert "olculemedi_seed" in src[max(0, i - 400):i], "istisna beyanı GATES_APPLIED'ın yanında değil"
