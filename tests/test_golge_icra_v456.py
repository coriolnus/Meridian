"""test_golge_icra_v456.py — EDG-2026-088 GÖLGE İCRA MOTORU (B1 Task 1). GERÇEK EMİR YOK.

NUMARA TAŞIMASI (2026-09-08): plan bu dosyaya **v455** demişti; teslim anında v455 ÜÇ KEZ doluydu —
`tests/test_roadmap_arsiv_sayimi_v455.py` ve `tests/test_soul_denetimi_rota_v455.py` ana checkout'ta
BİRLEŞMİŞ, `tests/test_arama_api_v455.py` ise paralel bir ajanın uçuşundaydı. Numara KİMLİKTİR ve
çakışmada AZ ÇAPALI taraf taşınır: bu dosyaya hiçbir yerden çapa yoktu, ötekiler zaten main'deydi →
v456 alındı. SONUÇ: planın v455/v456/v457 bloğu KAYAR — Task 2 kadans çivisi v457, Task 3 sayım
çivisi v458 olmalıdır (Rol-1 kalemi). Ölçüm: tüm worktree'ler + ana checkout tarandı, v456 boştu.

Turun ÇİVİLERİ (plan: docs/superpowers/plans/2026-09-08-golge-pilot-b1.md, Task 1):
  1) KILL#1 SIFIR EMİR — yasak emir/onay yüzeylerinin TAMAMI patlayan sahtelerle değiştirilip tam
     bir gölge pencere koşulur; hiçbiri çağrılmaz ve `state/` altında YALNIZ iki dosya doğar.
  2) KILL#3 AYNI FONKSİYON — `strategy.manage_position` casusla sarılır: açık pozisyon başına
     seansta TAM BİR çağrı, ve casusun `exit_reason`ı satırdaki `cikis_neden`e BİREBİR düşer.
     Kaynak taraması: motorda `exit.*` düğme adı YOK (ikinci uygulama yasağı).
  3) KILL#2 ÜRETİME DOKUNMAMA — `arming` ithal EDİLMEZ; canlı plan/aday/onay defterlerine yazma
     çağrısı YOK (`codelaw.artifact_graph` yazar kümesi).
  4) PK (1) SENTETİK — beş plan, beş bilinen fiyat yolu, R'ler EL HESABIYLA birebir.
  5) İLERİ-DÖNÜKLÜK YOK — plan D kapanışında doğar, giriş D+1 AÇILIŞINDA; D'nin kapanışı ve çıkış
     barından SONRAKİ barlar sonucu DEĞİŞTİRMEZ.
  6) PIT / `kaynak_bar_hash` — aynı barlar aynı hash; tek hane değişince hash değişir; tüketilmeyen
     sembol hash'i değiştirmez; bar eksikse hash None + `olculemedi` ve satır K'ye SAYILMAZ.
  7) ALAN KÜMESİ — yazılan satır kartın `olcum_plani` alanlarını KAPSAR (kart ↔ kod tek kaynak).
  8) İKİ KOL — dormant ve normal plan aynı seansta `kol` ile ayrışır, `ozet` ikisini ayrı sayar.
  9) İDEMPOTENS — aynı `dstr` ikinci kez: 0 yeni satır, `son_seans` değişmez.
  + Rol-1 hükmü 8'in ÖLÇÜMÜ: `_touch_exit` broker durumundan bağımsız (çağrılır), `scale_out`
    değil (çağrılmaz, beyanlı sapma) — ikisi de AST ile kaynağa çakılı.
  + Kart sabitleri (eşik/pencere/n) kartın YAML'ıyla karşılaştırılır: eşik kodda gevşetilemez.
  + `pitlaw`: motor bir KAPI YÜZEYİ değildir (karar sabiti döndüren fonksiyon yok).

CANLI STATE'E YAZAN TEST YOK: motora dokunan her test `sandbox_state` içinde koşar.
"""
from __future__ import annotations

import ast
import json
import pathlib
import re

import pandas as pd
import pytest

from meridian import codelaw, config, golge_icra as gi, pitlaw, store, strategy

ROOT = pathlib.Path(__file__).resolve().parent.parent
KAYNAK = ROOT / "meridian" / "golge_icra.py"
KART_YOLU = ROOT / "research" / "cards" / "EDG-2026-088-uyuyan-kurulum-golge-pilot.yaml"

D0, D1, D2, D3 = "2026-07-01", "2026-07-02", "2026-07-03", "2026-07-06"

#: Sentetik senaryonun ORTAK düğmeleri. `time_stop_days=2` PK (1)'in (c) yolunu kısaltmak içindir;
#: bu ad TESTTE geçer, motorda GEÇMEZ (Çivi 2'nin kaynak taraması tam bunu sınar).
PARAMS = {"exit.time_stop_days": 2}


# ============================ kurgu yardımcıları =================================================
def _seri(gunler: dict, taban: float = 100.0, isinma: int = 30, hacim: float = 2_000_000.0):
    """`{tarih: (o,h,l,c)}` → DataFrame. Öncesine DÜZ bir ısınma serisi eklenir (ATR penceresi).

    Her sayı ELLE konur: rastgelelik yok, aynı girdi aynı çıktı — el hesabının şartı budur.
    """
    ilk = pd.Timestamp(min(gunler))
    isin = list(pd.bdate_range(end=ilk - pd.Timedelta(days=1), periods=isinma))
    rows = [{"open": taban, "high": taban, "low": taban, "close": taban, "volume": hacim}
            for _ in isin]
    idx = list(isin)
    for t in sorted(gunler):
        o, h, lo, c = gunler[t]
        rows.append({"open": o, "high": h, "low": lo, "close": c, "volume": hacim})
        idx.append(pd.Timestamp(t))
    return pd.DataFrame(rows, index=pd.DatetimeIndex(idx, name="date"))


def _plan(pid, tk, *, trig=100.0, stop=95.0, hedef=110.0, kurulum="pullback",
          hukum="REVIEW", dormant=True, tarih=D0):
    return {"id": pid, "date": tarih, "ticker": tk, "setup": kurulum, "score": 70,
            "entry_trigger": trig, "stop": stop, "targets": [hedef], "profit_target": hedef,
            "gate_verdict": hukum, "dormant_setup": dormant, "size_r": 1.0,
            "strategy_version": 3}


def _bars_of(bars: dict):
    return lambda t: bars.get(t)


def _pk1_bars():
    """PK (1)'in beş yolu — her bar elle yazıldı, her R elle hesaplanabilir.

    AAA sert stop · BBB hedef · CCC time_stop · DDD regime_flip (D1'de doğar) · EEE tetik gelmedi.
    """
    return {
        "AAA": _seri({D1: (101.0, 103.0, 100.0, 101.0), D2: (99.0, 99.0, 90.0, 91.0)}),
        "BBB": _seri({D1: (101.0, 103.0, 100.0, 101.0), D2: (105.0, 112.0, 104.0, 111.0)}),
        "CCC": _seri({D1: (101.0, 103.0, 100.0, 101.0), D2: (101.0, 102.0, 100.0, 101.0),
                      D3: (100.5, 101.0, 100.0, 100.5)}),
        "DDD": _seri({D1: (100.0, 100.0, 100.0, 100.0), D2: (101.0, 103.0, 100.0, 101.0),
                      D3: (102.0, 103.0, 101.0, 102.0)}),
        "EEE": _seri({D1: (95.5, 96.0, 94.0, 95.0)}),
    }


def _pk1_kosusu(bars=None, params=None):
    """Beş planlık tam gölge pencere: D0 doğum → D1 giriş → D2 çıkışlar/karar → D3 kapanışlar.

    `regime_ok` D2'de FALSE'tur: o kapanışta CCC zaten time_stop'a ulaşmıştır (yasa sırası time_stop'u
    ÖNCE sınar), DDD ise 1 bar tutuşla rejim dalına düşer — iki dal tek seansta ayrışır.
    """
    bars = bars or _pk1_bars()
    bo, prm = _bars_of(bars), (params or PARAMS)
    planlar = [_plan("P-a", "AAA"), _plan("P-b", "BBB"), _plan("P-c", "CCC"),
               _plan("P-e", "EEE")]
    gi.adim(D0, planlar=planlar, bars_of=bo, regime_ok=True, params=prm)
    gi.adim(D1, planlar=[_plan("P-d", "DDD", tarih=D1)], bars_of=bo, regime_ok=True, params=prm)
    gi.adim(D2, planlar=[], bars_of=bo, regime_ok=False, params=prm)
    gi.adim(D3, planlar=[], bars_of=bo, regime_ok=True, params=prm)
    return {r["plan_id"]: r for r in gi.kayit_al()}


def _kaynak() -> str:
    return KAYNAK.read_text(encoding="utf-8")


def _agac() -> ast.Module:
    return ast.parse(_kaynak())


def _kod_dizgeleri() -> set[str]:
    """Modülün DOCSTRING OLMAYAN dizge sabitleri.

    Ham metin taraması BURADA YANLIŞ CEVAP VERİR: modül başlığı beyanlı sapmayı anlatırken
    `scale_out`u ve `exit.*` düğmelerini ADIYLA anmak ZORUNDADIR (beyan, adını söylemeyen bir
    beyan değildir). Yasak olan şey o adları KOD olarak kullanmaktır — ayrım metnin biçimi değil,
    AST'deki yeridir.
    """
    tree = _agac()
    docs = {id(n.body[0].value) for n in ast.walk(tree)
            if isinstance(n, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
            and ast.get_docstring(n, clean=False) is not None}
    return {n.value for n in ast.walk(tree)
            if isinstance(n, ast.Constant) and isinstance(n.value, str) and id(n) not in docs}


def _kod_adlari() -> set[str]:
    """Kodda GEÇEN adlar (öznitelik · değişken · tanım) — şerh ve başlık metni GİRMEZ."""
    out: set[str] = set()
    for n in ast.walk(_agac()):
        if isinstance(n, ast.Attribute):
            out.add(n.attr)
        elif isinstance(n, ast.Name):
            out.add(n.id)
        elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            out.add(n.name)
    return out


def _self_erisimleri(sinif: str, fn_adi: str) -> list[str]:
    """`meridian/broker.py` içindeki bir metodun `self.<x>` erişimleri — SAFLIK ÖLÇÜSÜ."""
    tree = ast.parse((ROOT / "meridian" / "broker.py").read_text(encoding="utf-8"))
    for c in ast.walk(tree):
        if isinstance(c, ast.ClassDef) and c.name == sinif:
            for fn in c.body:
                if isinstance(fn, ast.FunctionDef) and fn.name == fn_adi:
                    return sorted({n.attr for n in ast.walk(fn) if isinstance(n, ast.Attribute)
                                   and isinstance(n.value, ast.Name) and n.value.id == "self"})
    raise AssertionError(f"{sinif}.{fn_adi} kaynakta bulunamadı — çapa çürüdü")


# ============================ ÇİVİ 4 — PK (1) SENTETİK ===========================================
def test_civi4_pk1_bes_yolun_R_leri_EL_HESABIYLA_birebir(sandbox_state):
    """Beş bilinen fiyat yolu. Giriş 101, stop 95 → R payda = 6,0 (dördünde de).

      AAA: stop 95     → (95−101)/6      = −1,000000
      BBB: hedef 110   → (110−101)/6     = +1,500000
      CCC: time_stop, ERTESİ açılış 100,5 → (100,5−101)/6 = −0,083333
      DDD: regime_flip, ERTESİ açılış 102 → (102−101)/6   = +0,166667
      EEE: tetik (100) hiç gelmedi (en yüksek 96) → R = None, 0 DEĞİL.
    """
    sat = _pk1_kosusu()
    assert set(sat) == {"P-a", "P-b", "P-c", "P-d", "P-e"}, sat.keys()

    assert sat["P-a"]["cikis_neden"] == "stop" and sat["P-a"]["cikis_fiyat"] == 95.0
    assert sat["P-a"]["R"] == pytest.approx(-1.0, abs=1e-9)
    assert sat["P-b"]["cikis_neden"] == "target" and sat["P-b"]["cikis_fiyat"] == 110.0
    assert sat["P-b"]["R"] == pytest.approx(1.5, abs=1e-9)
    assert sat["P-c"]["cikis_neden"] == "time_stop" and sat["P-c"]["cikis_fiyat"] == 100.5
    assert sat["P-c"]["R"] == pytest.approx(-0.5 / 6.0, abs=1e-6)
    assert sat["P-d"]["cikis_neden"] == "regime_flip" and sat["P-d"]["cikis_fiyat"] == 102.0
    assert sat["P-d"]["R"] == pytest.approx(1.0 / 6.0, abs=1e-6)

    # (e) UYDURMA YASAĞI: R sıfır DEĞİL, None — ve nedeni ADIYLA yazılı.
    assert sat["P-e"]["cikis_neden"] == gi.GIRIS_YOK
    assert sat["P-e"]["R"] is None and sat["P-e"]["giris_fiyat"] is None
    assert sat["P-e"]["giris_reddi"] == "tetik_gelmedi"

    toplam = sum(r["R"] for r in sat.values() if r["R"] is not None)
    assert toplam == pytest.approx(0.5 + 0.5 / 6.0, abs=1e-6), toplam
    ozet = gi.ozet()
    assert ozet["n"] == 4, "R'si ölçülmeyen satır K paydasına girmiş"
    assert ozet["toplam_r"] == pytest.approx(0.5 + 0.5 / 6.0, abs=1e-6)
    assert ozet["kazanma_orani"] == pytest.approx(0.5)


def test_civi4_giris_ALTINCI_satir_toplami_DEGISTIRIR(sandbox_state):
    """Mutasyon kardeşi: bir satır daha eklenince toplam R DEĞİŞMELİ (sayaç ölü değil)."""
    once = _pk1_kosusu()
    onceki = sum(r["R"] for r in once.values() if r["R"] is not None)
    bars = {"FFF": _seri({"2026-07-08": (101.0, 112.0, 100.0, 111.0)})}   # giriş 101 → hedef 110
    bo = _bars_of(bars)
    gi.adim("2026-07-07", planlar=[_plan("P-f", "FFF", tarih="2026-07-07")],
            bars_of=bo, regime_ok=True, params=PARAMS)
    gi.adim("2026-07-08", planlar=[], bars_of=bo, regime_ok=True, params=PARAMS)
    assert gi.ozet()["toplam_r"] == pytest.approx(onceki + 1.5, abs=1e-6)


def test_civi4_giris_redlerinin_TAMAMI_adiyla_ayrisir(sandbox_state):
    """Kalan iki red dalı: limit tavanı aşıldı · DOLUM planlanan stopun ALTINDA.

    TUR 2 (A1, stop-al semantiği): `acilis_stop_altinda` artık AÇILIŞLA değil DOLUMLA ölçülür.
    Tetiği olan bir planda dolum `max(açılış, tetik) > stop` olduğu için bu dal YALNIZ tetiği
    ölçülemeyen (`tetik=0`) planda ateşler — sahne ona göre kuruldu (eski sahne "açılış 94, tetik
    100" idi ve yeni yasada GİRİŞ üretir: tetikten dolum 100 > stop 95).
    """
    bars = {"GGG": _seri({D1: (120.0, 125.0, 119.0, 124.0)}),      # gap tavanı = 100·1,04 = 104
            "HHH": _seri({D1: (94.0, 101.0, 93.0, 100.5)})}        # tetiksiz plan: dolum = açılış
    bo = _bars_of(bars)
    gi.adim(D0, planlar=[_plan("P-g", "GGG"), _plan("P-h", "HHH", trig=0.0)], bars_of=bo,
            regime_ok=True, params=PARAMS)
    gi.adim(D1, planlar=[], bars_of=bo, regime_ok=True, params=PARAMS)
    sat = {r["plan_id"]: r for r in gi.kayit_al()}
    # SIRA ÜRETİMİN SIRASIDIR: `fill_entry` önce max-chase, sonra limit tavanı sınar. Bugünkü
    # yapılandırmada ikisi AYNI fiyatta bağlar (%4), yani bu sahnede ÖNCE gap kapısı ateşler;
    # `limit_asildi` dalı daha sıkı bir tavanla ölçülür (A1 limit çivisi).
    assert sat["P-g"]["giris_reddi"] == "gap_asildi"
    assert sat["P-h"]["giris_reddi"] == "acilis_stop_altinda"
    assert all(sat[p]["R"] is None and sat[p]["cikis_neden"] == gi.GIRIS_YOK for p in sat)
    assert set(gi.GIRIS_REDLERI) >= {sat[p]["giris_reddi"] for p in sat}


# ================ ÇİVİ 4b — GİRİŞ KURALI: STOP-AL (Rol-1 hükmü A1, inceleme M2-01) ==============
def _giris_kosusu(bar, *, trig=100.0, stop=95.0, pid="P-x", tk="XXX"):
    """Tek plan: D0'da doğar, D1'de giriş denenir. Dönüş: (`ACIK` belgesi, plan_id→satır)."""
    bars = {tk: _seri({D1: bar})}
    bo = _bars_of(bars)
    gi.adim(D0, planlar=[_plan(pid, tk, trig=trig, stop=stop)], bars_of=bo,
            regime_ok=True, params=PARAMS)
    gi.adim(D1, planlar=[], bars_of=bo, regime_ok=True, params=PARAMS)
    return gi.acik_kayit(), {r["plan_id"]: r for r in gi.kayit_al()}


def test_A1_open_TETIGIN_ALTINDA_ise_dolum_TETIKTEN_yazilir(sandbox_state):
    """M2-01'in ileri-bakışı KAPANDI: karar `high ≥ tetik` ile verilip dolum açılıştan yazılıyordu.

    Açılış anında günün yükseği BİLİNMEZ; `open < tetik ≤ high` günlerinde tetiğin ALTINDAN dolum
    yazmak K1/K2'yi yukarı yanlı yapardı. Stop-al semantiğinde dolum `max(açılış, tetik)`tır.
    """
    doc, sat = _giris_kosusu((98.0, 103.0, 97.0, 102.0))          # açılış 98 < tetik 100 ≤ high 103
    poz = doc["acik"]["P-x"]
    assert poz["giris_fiyat"] == pytest.approx(100.0), "dolum tetiğin ALTINDAN yazıldı"
    assert poz["r_per_share"] == pytest.approx(5.0), "R paydası ham açılıştan kuruldu"
    assert sat == {}, "giriş olduğu hâlde satır yazıldı"


def test_A1_open_TETIGIN_USTUNDE_ise_dolum_ACILISTAN_yazilir(sandbox_state):
    """Boşluklu açılış: `açılış ≥ tetik` ise dolum AÇILIŞTIR (stop emri boşlukta açılıştan dolar)."""
    doc, _ = _giris_kosusu((101.0, 103.0, 100.0, 102.0))
    assert doc["acik"]["P-x"]["giris_fiyat"] == pytest.approx(101.0)
    assert doc["acik"]["P-x"]["r_per_share"] == pytest.approx(6.0)


def test_A1_high_TETIGE_ULASMAZSA_giris_YOKTUR(sandbox_state):
    """Tetiğe hiç dokunulmayan günde stop emri dolmaz — R None, neden ADIYLA."""
    doc, sat = _giris_kosusu((95.5, 96.0, 94.0, 95.0))
    assert not doc["acik"], doc["acik"]
    assert sat["P-x"]["giris_reddi"] == "tetik_gelmedi" and sat["P-x"]["R"] is None


def test_A1_limit_tavani_DOLUM_fiyatina_uygulanir_ACILISA_DEGIL(sandbox_state, monkeypatch):
    """Tavan DOLUM fiyatıyla ölçülür. Yasa üretimden OKUNUR: `limit_pct_cap` %1'e çekilince
    tavan 101 olur ve tetiğin %2 üstünde açılan bar reddedilir; aynı yasada tetiğin ALTINDA
    açılan bar tetikten (100 ≤ 101) DOLAR — yani kapı dolum fiyatına bakar."""
    # YASA DEĞİL YAPILANDIRMA yamalanır: `entry_law` düğmeyi `config.goal()`tan okur. Önbellek
    # SEVİYESİNE (`_goal_cached`) yazılır — `config.goal`ın kendisini değiştirmek `cache_clear`
    # özniteliğini düşürür ve `sandbox_state` kapanışını kırardı (ölçüldü).
    from meridian import config
    monkeypatch.setattr(config, "_goal_cached",
                        lambda: {"execution_v2": {"limit_pct_cap": 0.01}})
    _, sat = _giris_kosusu((102.0, 105.0, 101.0, 104.0))          # dolum 102 > tavan 101
    assert sat["P-x"]["giris_reddi"] == "limit_asildi", sat

    store.write_jsonl(gi.DEFTER, [])
    store.write_json(gi.ACIK, {})
    doc, sat2 = _giris_kosusu((98.0, 103.0, 97.0, 102.0))         # dolum 100 ≤ tavan 101
    assert sat2 == {}, sat2
    assert doc["acik"]["P-x"]["giris_fiyat"] == pytest.approx(100.0)


def test_F3_BEYANLI_SAPMALAR_besincisi_REJIM_KAPISINI_yazar():
    """M1-01 çürütüldü ama BEYANSIZDI: sapma listesine (5) olarak girdi.

    Beyan, adını söylemeyen bir beyan değildir: gölge kolunun KÜRESEL (sıkı) rejim kapısıyla
    ölçüldüğü ve canlı keşif sondasının gevşek kapısının UYGULANMADIĞI başlıkta yazılı olmalı.
    """
    ham = _kaynak()
    bas = ham.index("BEYANLI KAPSAM SAPMALARI")
    blok = ham[bas:ham.index("OKUR:", bas)]
    assert "(5)" in blok, "beşinci sapma beyanı kayboldu"
    for jeton in ("regime_ok", "keşif"):
        assert jeton in blok, f"beyan `{jeton}` sözcüğünü taşımıyor — sapma adıyla yazılmamış"


def test_F2_GAP_MUHAFIZI_uretimin_SABITIYLE_aynalanir(sandbox_state):
    """M1-09: üretim `fill_entry` İKİ kapı uygular (max-chase + limit tavanı); gölge yalnız
    limiti sınıyordu. `limit_pct_cap` %4'ün üstüne çıkarılırsa gölge girer, canlı reddederdi —
    sapma gölge LEHİNE, yani beyanlı sapmaların TERSİ yönde. Sabit broker'dan İTHAL edilir.
    """
    from meridian import broker as brk
    _, sat = _giris_kosusu((106.0, 110.0, 105.0, 109.0))      # tetik 100 → gap tavanı 104
    assert sat["P-x"]["giris_reddi"] == "gap_asildi", sat
    assert "gap_asildi" in gi.GIRIS_REDLERI

    # ÜRETİM AYNI SAHNEDE AYNI KAPIYI UYGULAR — kıyas ÖLÇÜLÜR, varsayılmaz.
    red: dict = {}
    b = brk.PaperBroker(equity=100_000.0, slippage_bps=0.0, commission_per_share=0.0)
    b.fill_entry({"id": "P-x", "ticker": "XXX", "entry_trigger": 100.0, "stop": 95.0,
                  "profit_target": 110.0, "size_r": 1.0},
                 next_open=106.0, ts="2026-07-02", equity=100_000.0, reject_out=red)
    assert red.get("reason") == "max_chase", red
    assert red.get("tavan_pct") == brk.MAX_ENTRY_GAP_PCT


def test_A1_satir_GIRIS_KURALINI_adiyla_tasir(sandbox_state):
    """Sapma BEYANLIDIR ve satırdadır: okuyucu hangi giriş yasasıyla ölçüldüğünü defterden bilir."""
    bars = {"XXX": _seri({D1: (98.0, 103.0, 97.0, 102.0), D2: (99.0, 99.0, 90.0, 91.0)})}
    bo = _bars_of(bars)
    gi.adim(D0, planlar=[_plan("P-x", "XXX")], bars_of=bo, regime_ok=True, params=PARAMS)
    gi.adim(D1, planlar=[], bars_of=bo, regime_ok=True, params=PARAMS)
    gi.adim(D2, planlar=[], bars_of=bo, regime_ok=True, params=PARAMS)
    sat = gi.kayit_al()[0]
    assert "giris_kurali" in gi.SATIR_ALANLARI
    assert sat["giris_kurali"] == gi.GIRIS_KURALI == "stop_al"
    # Dolum tetikten (100), stop 95 → R = (95 − 100)/5 = −1,0 (ham açılıştan olsaydı −0,6 çıkardı)
    assert sat["giris_fiyat"] == pytest.approx(100.0)
    assert sat["R"] == pytest.approx(-1.0, abs=1e-9)


# ============================ ÇİVİ 1 — KILL#1 SIFIR EMİR ========================================
_YASAK_ALPACA = ("submit_plan", "submit_bracket", "submit_protective_oco", "cancel_order",
                 "cancel_open_entries", "close_engine_position", "close_all", "replace_order_stop")
_YASAK_LOOP = ("mirror_submit_armed", "mirror_submit_ve_kalicilastir", "operator_onay_ver",
               "operator_ret_ver")


def test_civi1_yasak_emir_yuzeylerinin_HICBIRI_cagrilmaz(sandbox_state, monkeypatch):
    """Yasak yüzeylerin TAMAMI patlayıcı sahtelerle değiştirilir; tam bir pencere koşar.

    Sahteler `AssertionError` atar: motor onlardan birine ULAŞSA test kırmızıya döner. Bu, "emir
    yolu yok" iddiasının GÖZLENEBİLİR biçimidir — ithal grafiğine bakmak yalnız statik yolu görür.
    """
    from meridian import loop
    from meridian.adapters import alpaca

    def _patlat(ad):
        def _f(*a, **k):
            raise AssertionError(f"GÖLGE MOTOR GERÇEK EMİR YÜZEYİNE DOKUNDU: {ad}")
        return _f

    for ad in _YASAK_ALPACA:
        assert hasattr(alpaca, ad), f"yasak yüzey kaydı çürüdü: alpaca.{ad}"
        monkeypatch.setattr(alpaca, ad, _patlat(f"alpaca.{ad}"))
    for ad in _YASAK_LOOP:
        assert hasattr(loop, ad), f"yasak yüzey kaydı çürüdü: loop.{ad}"
        monkeypatch.setattr(loop, ad, _patlat(f"loop.{ad}"))

    sat = _pk1_kosusu()
    assert len(sat) == 5, "pencere koşmadı — çivi hiçbir şey kanıtlamaz"


def test_civi1_yazilan_dosya_kumesi_TAM_OLARAK_iki_defterdir(sandbox_state):
    """`state/` altında motorun doğurduğu dosyalar: yalnız `DEFTER` + `ACIK`.

    `.locks/` HARİÇTİR ve bu bir muafiyet değil BEYANDIR: kilit dizini `store.write_json`ın
    kapısıdır (her yazar oradan geçer), gölge defterinin bir artefaktı değildir.
    """
    kok = pathlib.Path(config.STATE)
    once = {p.name for p in kok.iterdir()}
    _pk1_kosusu()
    yeni = {p.name for p in kok.iterdir()} - once - {".locks"}
    assert yeni == {gi.DEFTER, gi.ACIK}, f"beklenmedik dosya doğdu: {sorted(yeni)}"


def test_civi1_modul_emir_ve_uretim_yuzeylerini_ITHAL_ETMEZ():
    """Statik ayak: ithal grafiğinde `alpaca` / `loop` / `arming` YOKTUR (Çivi 1 + Çivi 3)."""
    yasak = {"alpaca", "loop", "arming", "hermes", "spend", "httpx", "requests"}
    adlar: set[str] = set()
    for n in ast.walk(_agac()):
        if isinstance(n, ast.Import):
            adlar |= {a.name.split(".")[-1] for a in n.names}
        elif isinstance(n, ast.ImportFrom):
            adlar |= {a.name.split(".")[-1] for a in n.names}
            if n.module:
                adlar |= {n.module.split(".")[-1]}
    assert not (adlar & yasak), f"gölge motor yasak modülü ithal ediyor: {sorted(adlar & yasak)}"


# ============================ ÇİVİ 2 — KILL#3 AYNI FONKSİYON ====================================
def test_civi2_manage_position_pozisyon_basina_TAM_BIR_KEZ_cagrilir(sandbox_state, monkeypatch):
    """Casus: çıkış kararının TEK kaynağı üretim fonksiyonudur ve seansta pozisyon başına bir kez
    sorulur. İki çağrı, iki kez ilerletilen bir yönetim barı demek olurdu."""
    cagri: list[tuple] = []
    gercek = strategy.manage_position

    def _casus(bars, position, params, bars_held, regime_ok):
        cagri.append((str(position["entry"]), bars_held))
        return gercek(bars, position, params, bars_held, regime_ok)

    monkeypatch.setattr(strategy, "manage_position", _casus)
    bars = _pk1_bars()
    bo = _bars_of(bars)
    gi.adim(D0, planlar=[_plan("P-a", "AAA"), _plan("P-c", "CCC")], bars_of=bo,
            regime_ok=True, params=PARAMS)
    assert cagri == [], "açık pozisyon yokken yönetim çağrıldı"
    gi.adim(D1, planlar=[], bars_of=bo, regime_ok=True, params=PARAMS)
    assert len(cagri) == 2, f"D1'de iki açık pozisyon için {len(cagri)} çağrı: {cagri}"


def test_civi2_casusun_exit_reason_i_satira_BIREBIR_duser(sandbox_state, monkeypatch):
    """Çıkış NEDENİ motorda yeniden adlandırılmaz: üretim fonksiyonunun döndürdüğü dizge satıra
    olduğu gibi iner. Motorun kendi sözlüğüne çevirmesi, sebep dağılımını sessizce yeniden
    etiketlerdi (sayım betiğinin ham maddesi tam olarak o dağılımdır)."""
    monkeypatch.setattr(strategy, "manage_position",
                        lambda *a, **k: strategy.ManageDecision(True, "CASUS_NEDENI", 95.0))
    bars = {"CCC": _pk1_bars()["CCC"]}
    bo = _bars_of(bars)
    gi.adim(D0, planlar=[_plan("P-c", "CCC")], bars_of=bo, regime_ok=True, params=PARAMS)
    gi.adim(D1, planlar=[], bars_of=bo, regime_ok=True, params=PARAMS)
    gi.adim(D2, planlar=[], bars_of=bo, regime_ok=True, params=PARAMS)
    sat = gi.kayit_al()
    assert len(sat) == 1 and sat[0]["cikis_neden"] == "CASUS_NEDENI", sat


@pytest.mark.parametrize("dugme", ["exit.time_stop_days", "exit.trail_atr_mult",
                                   "exit.giveback_pct", "exit.early_kill_pivot",
                                   "exit.scale_out_frac"])
def test_civi2_motor_govdesinde_exit_dugmesi_ADIYLA_gecmez(dugme):
    """İKİNCİ UYGULAMA YASAĞI: eşiği motorun kendisi okursa iki yorum doğar ve ilk düzeltmede
    çatallanır. `params` sözlüğü OLDUĞU GİBİ üretim fonksiyonuna verilir."""
    gecen = [s for s in _kod_dizgeleri() if dugme in s]
    assert gecen == [], f"gölge motor `{dugme}` düğmesini KODDA yorumluyor: {gecen}"


def test_civi2_ROL1_hukmu_8_saflik_OLCUMU_kaynaga_cakilidir():
    """Rol-1 hükmü 8'in dayanağı bir GÖRÜŞ değil bir ÖLÇÜMDÜR ve burada donar.

    `_touch_exit` broker DURUMUNU hiç okumaz → kitap kurmadan çağrılabilir → çağrılır.
    `scale_out` sermaye/komisyon/kayma durumunu okur ve YAZAR → çağrılamaz → beyanlı sapma.
    Üretim tarafında biri değişirse (ör. `_touch_exit`e `self` girerse) bu test kırılır ve
    sapma beyanı yeniden hüküm ister — beyan sessizce bayatlayamaz.
    """
    assert _self_erisimleri("PaperBroker", "_touch_exit") == [], \
        "`_touch_exit` artık broker durumunu okuyor — gölge motor onu durumsuz çağıramaz"
    assert set(_self_erisimleri("PaperBroker", "scale_out")) >= {"cash", "realized_pnl"}, \
        "`scale_out` artık durumsuz olabilir — beyanlı sapma (2) yeniden değerlendirilmeli"
    assert "scale_out" not in _kod_adlari(), \
        "sapma beyanı ile kod ayrıştı: motor `scale_out` çağırıyor ama başlık çağırmadığını yazıyor"
    assert "_touch_exit" in _kod_adlari(), "dokunuş çıkışı üretimin fonksiyonundan gelmiyor"
    assert "scale_out" in _kaynak(), \
        "sapma BEYANI kayboldu: adını söylemeyen bir sapma beyanı, beyan değildir"


def test_civi2_dokunus_cikisi_URETIMIN_fonksiyonundan_gelir(sandbox_state, monkeypatch):
    """Dokunuş çıkışı da kopyalanmaz: `broker.PaperBroker._touch_exit` yamalanınca satır değişir."""
    from meridian import broker as brk
    monkeypatch.setattr(brk.PaperBroker, "_touch_exit",
                        lambda self, pos, bar: (77.5, "CASUS_DOKUNUS"))
    bars = {"AAA": _pk1_bars()["AAA"]}
    bo = _bars_of(bars)
    gi.adim(D0, planlar=[_plan("P-a", "AAA")], bars_of=bo, regime_ok=True, params=PARAMS)
    gi.adim(D1, planlar=[], bars_of=bo, regime_ok=True, params=PARAMS)
    sat = gi.kayit_al()
    assert len(sat) == 1 and sat[0]["cikis_neden"] == "CASUS_DOKUNUS"
    assert sat[0]["cikis_fiyat"] == 77.5


# ============================ ÇİVİ 3 — KILL#2 ÜRETİME DOKUNMAMA =================================
@pytest.mark.parametrize("defter", ["trade_plans.jsonl", "candidates.jsonl", "approvals.jsonl",
                                    "trades.jsonl", "portfolio.json"])
def test_civi3_canli_defterlere_YAZAR_degil(defter):
    """`codelaw.artifact_graph` yazar kümesi: gölge motor canlı icra defterlerinin YAZARI DEĞİLDİR."""
    g = codelaw.artifact_graph()
    yazarlar = (g["artifacts"].get(defter) or {}).get("writers") or []
    assert "golge_icra.py" not in yazarlar, f"{defter} yazarları: {yazarlar}"


def test_civi3_motorun_yazdigi_artefaktlar_TAM_OLARAK_iki_defterdir():
    """Statik ayak: tarayıcının gördüğü yazım çağrıları da yalnız iki adı taşır."""
    g = codelaw.artifact_graph()
    yazdiklari = sorted(ad for ad, v in g["artifacts"].items()
                        if "golge_icra.py" in (v.get("writers") or []))
    assert yazdiklari == sorted([gi.ACIK, gi.DEFTER]), yazdiklari


def test_civi3_YASA6_bugun_ACIK_ve_kapatan_sey_DIS_OKUYUCUDUR(tmp_path):
    """YASA 6'NIN MEKANİĞİ, BEYANLA DEĞİL ÖLÇÜMLE — SENTETİK AĞAÇTA.

    KAPSAM GÜNCELLENDİ (2026-09-12, inceleme M4-10). Docstring'in eski hâli "BUGÜN canlı ağaçta
    iki artefakt `unread`tır ve v59/v132 KIRMIZIDIR" diyordu; o açık kalem Task 2'de KAPANDI
    (`meridian/api.py` → `_golge_icra_karne`). Bu çivi canlı hükmü VERMEZ: canlı ölçüm
    `tests/test_golge_icra_kadans_v457.py` içindeki dış-okuyucu çivisidir. Burada ölçülen şey
    codelaw'ın DAVRANIŞIDIR: okuyucusuz bir ağaçta iki ad `violations`ta doğar, `ozet`i çağıran
    tek bir dış modül eklenince İKİSİ DE düşer — yani ihlalin sebebi gerçekten okuyucu
    eksikliğidir, başka bir şey değil.

    `DECLARED_SINKS` BİLEREK KULLANILMADI: beyan "bu artefaktın üretimde okuyucusu YOK" demektir
    ve YANLIŞ olurdu — okuyucu vardır.

    TASLAK LİTERAL AD OKUR: canlı ağaçta `store.read_jsonl(golge_icra.DEFTER)` biçimi ÇÖZÜLMEZ
    (`codelaw._global_consts` çakışan `DEFTER` adını düşürür — `mukerrerlik.py` aynı adı taşır),
    o yüzden gerçek `api.py` de literal yazar. Taslak onu AYNI biçimde kurar ki sentetik ölçüm
    canlı biçimin provası olsun.
    """
    (tmp_path / "golge_icra.py").write_text(_kaynak(), encoding="utf-8")
    okuyucusuz = codelaw.artifact_graph(str(tmp_path))
    assert sorted(okuyucusuz["violations"]) == sorted([gi.ACIK, gi.DEFTER]), \
        okuyucusuz["violations"]

    (tmp_path / "api.py").write_text(                       # dış okuyucunun CANLI biçimdeki provası
        "from . import golge_icra, store\n"
        "def golge_icra_ucu():\n"
        f'    store.read_jsonl("{gi.DEFTER}")\n'
        f'    store.read_json("{gi.ACIK}", {{}})\n'
        "    return golge_icra.ozet()\n", encoding="utf-8")
    okuyuculu = codelaw.artifact_graph(str(tmp_path))
    assert okuyuculu["violations"] == [], okuyuculu["violations"]
    for ad in (gi.DEFTER, gi.ACIK):
        assert okuyuculu["artifacts"][ad]["unread"] is False
        assert ad not in codelaw.DECLARED_SINKS, \
            "gerçek okuyucusu OLACAK artefakt lağım listesine yazılmış — beyan yanlış sınıfta"


def test_civi3_motor_KAPI_YUZEYI_degildir():
    """`pitlaw` kapı sözleşmesi: karar sabiti (`GO`/`NO_GO`/`REVIEW`) DÖNDÜREN yeni bir yüzey
    doğmadı. Doğsaydı kayıtsız kapı yüzeyi olurdu ve yasa orada kör kalırdı."""
    kayitsiz = pitlaw.kapi_sozlesme_denetimi()["kayitsiz"]
    assert not [k for k in kayitsiz if k["yer"].startswith("golge_icra.py")], kayitsiz


# ============================ ÇİVİ 5 — İLERİ-DÖNÜKLÜK YOK =======================================
def test_civi5_giris_D_ARTI_BIR_ACILISINDA_olur(sandbox_state):
    """Plan D kapanışında doğar, girişi D+1'in AÇILIŞINDADIR — D+1'in kapanışı ya da yükseği değil."""
    bars = {"AAA": _pk1_bars()["AAA"]}
    bo = _bars_of(bars)
    gi.adim(D0, planlar=[_plan("P-a", "AAA")], bars_of=bo, regime_ok=True, params=PARAMS)
    doc = gi.acik_kayit()
    assert list(doc["bekleyen_giris"]) == ["P-a"] and not doc["acik"], "D0'da giriş oldu"
    gi.adim(D1, planlar=[], bars_of=bo, regime_ok=True, params=PARAMS)
    poz = gi.acik_kayit()["acik"]["P-a"]
    assert poz["giris_ts"] == D1 and poz["giris_fiyat"] == 101.0, poz


def test_civi5_D0_KAPANISI_GIRISTE_kullanilmaz(sandbox_state):
    """D0 (plan doğum) barı GİRİŞ kararını ve fiyatını DEĞİŞTİRMEZ — ileri-dönüklük yok.

    KAPSAM DARALTILDI (tur 2, inceleme M4-05): D0 barı YÖNETİM geçmişinde MEŞRUDUR
    (`manage_position` ATR'yi giriş öncesi barlardan da kurar) ve tur 2'den beri PIT çapasına
    GİRER. Bu yüzden bu çivi artık `kaynak_bar_hash` eşitliği İSTEMEZ — onun değişmesi doğru
    davranıştır ve kendi çivisi vardır (`test_D_GIRIS_ONCESI_bar_degisince_HASH_DEGISIR`).
    Eskiden hash de kıyasa giriyordu ve çivi "çapa eksik" olgusunu ERDEM diye mühürlüyordu.
    """
    temiz = _pk1_kosusu()
    kirli = _pk1_bars()
    for tk in kirli:
        kirli[tk] = pd.concat([kirli[tk], pd.DataFrame(
            [{"open": 500.0, "high": 900.0, "low": 1.0, "close": 700.0, "volume": 1.0}],
            index=pd.DatetimeIndex([pd.Timestamp(D0)], name="date"))]).sort_index()

    store.write_jsonl(gi.DEFTER, [])
    store.write_json(gi.ACIK, {})
    ikinci = _pk1_kosusu(bars=kirli)

    disarida = {"ts", "kaynak_bar_hash"}
    for pid in temiz:
        a = {k: v for k, v in temiz[pid].items() if k not in disarida}
        b = {k: v for k, v in ikinci[pid].items() if k not in disarida}
        assert a == b, f"{pid}: D0 kapanışı giriş/çıkış sonucunu değiştirdi\n{a}\n{b}"


def test_civi5_CIKIS_SONRASI_barlar_sonucu_ve_CAPAYI_DEGISTIRMEZ(sandbox_state):
    """Çıkıştan SONRAKİ barlar hiçbir satıra dokunmaz — hash DAHİL (tüketilmemiş bar çapada yok)."""
    temiz = _pk1_kosusu()
    kirli = _pk1_bars()
    for tk in kirli:
        kirli[tk] = pd.concat([kirli[tk], pd.DataFrame(
            [{"open": 5.0, "high": 9.0, "low": 0.5, "close": 7.0, "volume": 1.0}],
            index=pd.DatetimeIndex([pd.Timestamp("2026-07-10")], name="date"))]).sort_index()

    store.write_jsonl(gi.DEFTER, [])
    store.write_json(gi.ACIK, {})
    ikinci = _pk1_kosusu(bars=kirli)

    for pid in temiz:
        a = {k: v for k, v in temiz[pid].items() if k != "ts"}
        b = {k: v for k, v in ikinci[pid].items() if k != "ts"}
        assert a == b, f"{pid}: ileri-dönük bar sonucu değiştirdi\n{a}\n{b}"


# ============================ D — PIT ÇAPASININ KAPSAMI (M2-03 / M4-05) =========================
def _capa_kosusu(seri):
    """AAA tek planı: D0 doğum → D1 giriş → D2 sert stop. Dönüş: kapanan satır."""
    bo = _bars_of({"AAA": seri})
    gi.adim(D0, planlar=[_plan("P-a", "AAA")], bars_of=bo, regime_ok=True, params=PARAMS)
    gi.adim(D1, planlar=[], bars_of=bo, regime_ok=True, params=PARAMS)
    gi.adim(D2, planlar=[], bars_of=bo, regime_ok=True, params=PARAMS)
    return gi.kayit_al()[0]


def test_D_GIRIS_ONCESI_bar_degisince_HASH_DEGISIR(sandbox_state):
    """Çapa TÜKETİLEN pencereyi kapsar: yönetim yasası giriş ÖNCESİ barları da okur.

    `strategy.manage_position` ilk satırda `ind.atr(df, ATR_PERIOD)` çağırır ve ATR bir EWM'dir —
    yani trail/breakeven kararı giriş öncesi barlara BAĞLIDIR. Çapa yalnız pozisyon ömrünü
    kapsasaydı, giriş öncesi bir OHLC hanesi değişip çıkışı kaydırabilir ve `kaynak_bar_hash` AYNI
    kalırdı: PIT doğrulaması sessizce yanlış-pozitif verirdi.
    """
    ilk = _capa_kosusu(_pk1_bars()["AAA"])
    store.write_jsonl(gi.DEFTER, [])
    store.write_json(gi.ACIK, {})

    kirli = _pk1_bars()["AAA"].copy()
    onceki = kirli.index[kirli.index < pd.Timestamp(D1)][-1]      # GİRİŞ barından bir ÖNCEKİ bar
    kirli.loc[onceki, "high"] = float(kirli.loc[onceki, "high"]) + 1.0
    ikinci = _capa_kosusu(kirli)

    assert ikinci["R"] == ilk["R"], "senaryo değişti — kıyas artık çapayı ölçmüyor"
    assert ikinci["kaynak_bar_hash"] != ilk["kaynak_bar_hash"], \
        "giriş öncesi bar çapada YOK — PIT kapsamı tüketilen pencereden DAR"
    assert ilk["bar_n"] == gi.LOOKBACK_BAR + 2, ilk["bar_n"]   # ısınma + giriş barı + çıkış barı


def test_D_ISINMA_PENCERESI_DISINDAKI_bar_hash_i_DEGISTIRMEZ(sandbox_state):
    """Kapsam TANIMLIDIR, sonsuz değil: `LOOKBACK_BAR`dan geride kalan bar çapaya GİRMEZ.

    Çapayı tüm geçmişe açmak `bar_n`i ve ACIK belgesini sınırsız şişirirdi; pencere yönetim
    yasasının ÖLÇÜLEN geriye bakışından türetilir (`strategy.ATR_PERIOD` + 1).
    """
    ilk = _capa_kosusu(_pk1_bars()["AAA"])
    store.write_jsonl(gi.DEFTER, [])
    store.write_json(gi.ACIK, {})

    kirli = _pk1_bars()["AAA"].copy()
    uzak = kirli.index[0]                                        # 30 bar geride — pencere DIŞI
    kirli.loc[uzak, "high"] = float(kirli.loc[uzak, "high"]) + 5.0
    ikinci = _capa_kosusu(kirli)
    assert ikinci["kaynak_bar_hash"] == ilk["kaynak_bar_hash"], \
        "çapa ısınma penceresinden DAHA geriye uzanıyor — kapsam tanımsız"


def test_D_CAPA_BEDELI_ACIK_belgesinde_OLCULUR(sandbox_state):
    """BEDEL YASASI: kapsam genişledi — ne KAYBEDİLDİĞİ de ölçülür.

    Bedel `ACIK` belgesindedir (açık pozisyon başına `LOOKBACK_BAR` kesit); DEFTER satırı
    büyümez çünkü hash sabit uzunlukta bir sha256'dır. ÖLÇÜLEN (2026-09-12, bu sahnede):
    ısınma kesitleri 930 bayt/pozisyon, ACIK belgesinin tamamı 1.649 bayt (tek açık pozisyon). Canlıda aynı anda
    açık gölge pozisyon sayısı kadar çarpılır (bugün ≤ birkaç düzine) — üst sınır burada çivili.
    """
    bars = {"AAA": _pk1_bars()["AAA"]}
    bo = _bars_of(bars)
    gi.adim(D0, planlar=[_plan("P-a", "AAA")], bars_of=bo, regime_ok=True, params=PARAMS)
    gi.adim(D1, planlar=[], bars_of=bo, regime_ok=True, params=PARAMS)
    poz = gi.acik_kayit()["acik"]["P-a"]
    assert len(poz["tuketilen"]) == gi.LOOKBACK_BAR + 1, "ısınma penceresi taşınmıyor"
    isinma_bayt = len(json.dumps(poz["tuketilen"][:gi.LOOKBACK_BAR]))
    print(f"\nD-BEDEL ÖLÇÜMÜ: ısınma kesitleri {isinma_bayt} bayt/pozisyon · "
          f"ACIK belgesi {len(json.dumps(gi.acik_kayit()))} bayt")
    assert isinma_bayt < 1500, f"ısınma bedeli beklenenden büyük: {isinma_bayt} bayt"

    gi.adim(D2, planlar=[], bars_of=bo, regime_ok=True, params=PARAMS)
    sat = gi.kayit_al()[0]
    assert len(sat["kaynak_bar_hash"]) == 64, "defter satırı sabit uzunlukta çapa taşımıyor"


def test_D_LOOKBACK_BAR_yonetim_yasasindan_TURETILIR():
    """Sabit ELLE yazılmaz: ATR periyodu üretimin kendi sabitinden okunur (tek-kaynak)."""
    assert gi.LOOKBACK_BAR == strategy.ATR_PERIOD + 1


# ============================ ÇİVİ 6 — PIT / kaynak_bar_hash (devam) ============================


# ============================ ÇİVİ 6 — PIT / kaynak_bar_hash ====================================
def test_civi6_bar_hash_ayni_barlar_AYNI_tek_hane_FARKLI():
    kesit = [["AAA", "2026-07-02", 101.0, 103.0, 100.0, 101.0, 2_000_000.0]]
    kesit2 = [["AAA", "2026-07-02", 101.0, 103.0, 100.0, 101.0, 2_000_000.0]]
    assert gi.bar_hash(kesit) == gi.bar_hash(kesit2) is not None
    for i in range(2, 7):
        bozuk = [list(kesit[0])]
        bozuk[0][i] = bozuk[0][i] + 0.01
        assert gi.bar_hash(bozuk) != gi.bar_hash(kesit), f"hane {i} hash'i değiştirmedi"


#: ALTIN ÖZET — bilinen iki kesitin sha256'sı. BİLİNÇLİ DONMA: hash SÖZLEŞMESİ (kesit biçimi,
#: ayraç, `repr(float(x))` gösterimi, satır sonu, kesit sırası) değişirse bu çivi BİLEREK kırılır
#: ve değişiklik bir karar olur — sessizce yeni bir çapa kuşağı doğmaz. Değer ÖLÇÜLDÜ (2026-09-12).
G2_ALTIN_OZET = "fb4c43dd4d78aafa7cc491ab917c9af507a4f11ac6e6b14225fe560963d53592"
G2_K1 = ["AAA", "2026-07-02", 101.0, 103.0, 100.0, 101.0, 2_000_000.0]
G2_K2 = ["BBB", "2026-07-03", 50.0, 51.0, 49.0, 50.5, 1_000_000.0]


def test_G2_bar_hash_ICERIGI_her_haneyi_ve_kesit_SIRASINI_kapsar():
    """M4-04: çivi tek kesitin yalnız SAYISAL hanelerini oynatıyordu.

    Hayatta kalan mutantlar adıyla: hash satırından `tk, tarih`i düşürmek · ilk kesitten sonra
    `break` · kesitleri sıralamak. Üçü de artık ısırır.
    """
    temel = gi.bar_hash([G2_K1, G2_K2])
    assert temel is not None

    for hangi in (0, 1):                      # BİRİNCİ ve İKİNCİ kesit — ikisi de hash'e girer
        for i in range(7):                    # ticker (0) ve tarih (1) DAHİL her hane
            bozuk = [list(G2_K1), list(G2_K2)]
            bozuk[hangi][i] = (bozuk[hangi][i] + 0.5 if i >= 2
                               else str(bozuk[hangi][i]) + "X")
            assert gi.bar_hash(bozuk) != temel, f"kesit {hangi} hane {i} hash'i değiştirmedi"

    assert gi.bar_hash([G2_K2, G2_K1]) != temel, "kesit SIRASI hash'e girmiyor"
    assert gi.bar_hash([G2_K1]) != temel, "ikinci kesit hash'e girmiyor (erken `break` mutantı)"
    assert temel == G2_ALTIN_OZET, "hash SÖZLEŞMESİ değişti — bu bir karardır, sessiz olamaz"


def test_G2_PK1_satirlarinin_bar_n_degerleri_CIVILIDIR(sandbox_state):
    """`bar_n` hiçbir çivide iddia edilmiyordu: `_kesit_ekle`nin tekilleştirmesi ölçüsüzdü.

    ISINMA + ÖMÜR: giriş barından geriye `LOOKBACK_BAR` ısınma barı, sonra giriş barı ve ömür
    barları. AAA/BBB girişte + çıkışta iki bar, CCC/DDD üç bar (kapanış kararı ERTESİ açılışta
    icra edilir), EEE hiç girmedi → yalnız baktığı tek bar.
    """
    sat = _pk1_kosusu()
    lb = gi.LOOKBACK_BAR
    assert {pid: sat[pid]["bar_n"] for pid in sorted(sat)} == {
        "P-a": lb + 2, "P-b": lb + 2, "P-c": lb + 3, "P-d": lb + 2, "P-e": 1}


def test_civi6_eksik_hane_ve_bos_kume_hash_URETMEZ():
    """Yarım çapa çapa değildir: eksik hacim ya da hiç kesit → None (uydurma hash yok)."""
    assert gi.bar_hash([["AAA", "2026-07-02", 101.0, 103.0, 100.0, 101.0, None]]) is None
    assert gi.bar_hash([]) is None and gi.bar_hash(None) is None


def test_civi6_TUKETILMEYEN_sembolun_bari_hash_i_degistirmez(sandbox_state):
    """Hash TÜKETİLEN barlardan türer: aynı pencerede ilgisiz bir sembolün barını değiştirmek
    yazılmış satırların çapasına DOKUNMAZ."""
    ilk = _pk1_kosusu()
    store.write_jsonl(gi.DEFTER, [])
    store.write_json(gi.ACIK, {})
    bars = _pk1_bars()
    bars["ZZZ"] = _seri({D1: (1.0, 2.0, 0.5, 1.5), D2: (9.0, 9.0, 9.0, 9.0)})
    ikinci = _pk1_kosusu(bars=bars)
    for pid in ilk:
        assert ilk[pid]["kaynak_bar_hash"] == ikinci[pid]["kaynak_bar_hash"], pid


def test_civi6_bar_eksikse_hash_None_olculemedi_dolu_ve_K_disinda(sandbox_state):
    """Ömrünün ortasında barı olmayan plan: çapa YARIM → `kaynak_bar_hash=None`, `olculemedi`
    ADIYLA dolu ve satır `ozet`in K paydasına GİRMEZ (eksik K eşiği hak etmeden geçirir)."""
    bars = {"KKK": _seri({D1: (101.0, 103.0, 100.0, 101.0),      # giriş
                          D3: (99.0, 99.0, 90.0, 91.0)})}        # D2 BARI YOK → stop D3'te
    bo = _bars_of(bars)
    gi.adim(D0, planlar=[_plan("P-k", "KKK")], bars_of=bo, regime_ok=True, params=PARAMS)
    gi.adim(D1, planlar=[], bars_of=bo, regime_ok=True, params=PARAMS)
    gi.adim(D2, planlar=[], bars_of=bo, regime_ok=True, params=PARAMS)
    gi.adim(D3, planlar=[], bars_of=bo, regime_ok=True, params=PARAMS)
    sat = gi.kayit_al()
    assert len(sat) == 1, sat
    assert sat[0]["kaynak_bar_hash"] is None
    assert (sat[0]["olculemedi"] or "").startswith("bar_eksik"), sat[0]
    assert sat[0]["R"] is not None, "R ölçülebiliyordu, silinmemeli — satır yalnız K DIŞIDIR"
    ozet = gi.ozet()
    assert ozet["n"] == 0 and ozet["toplam_r"] is None
    assert [o["neden"] for o in ozet["olculemeyen"]] == [sat[0]["olculemedi"]]


def test_civi6_bar_kaynagi_satira_ADIYLA_yazilir(sandbox_state):
    """Rol-1 hükmü 2: PIT çapasının KAYNAĞI satırdadır — canlı yol `state/bars`, tarihsel yol arşiv."""
    bars = {"AAA": _pk1_bars()["AAA"]}
    bo = _bars_of(bars)
    gi.adim(D0, planlar=[_plan("P-a", "AAA")], bars_of=bo, regime_ok=True, params=PARAMS,
            bar_kaynak="arsiv")
    gi.adim(D1, planlar=[], bars_of=bo, regime_ok=True, params=PARAMS, bar_kaynak="arsiv")
    gi.adim(D2, planlar=[], bars_of=bo, regime_ok=True, params=PARAMS, bar_kaynak="arsiv")
    assert gi.kayit_al()[0]["bar_kaynak"] == "arsiv"
    assert set(gi.BAR_KAYNAKLARI) == {"state/bars", "arsiv"}


# ============================ ÇİVİ 7 — ALAN KÜMESİ (kart ↔ kod) =================================
def _kartin_satir_alanlari() -> set[str]:
    """Kartın `olcum_plani` satırındaki `satır: {...}` alan listesi — TEK KAYNAK kartın kendisidir."""
    ham = KART_YOLU.read_text(encoding="utf-8")
    m = re.search(r"satır:\s*\{([^}]*)\}", ham)
    assert m, "kartın alan listesi bulunamadı — kart ↔ kod bağı çürüdü"
    govde = re.sub(r"\([^)]*\)", "", m.group(1))     # parantezli açıklamalar alan adı değildir
    return {p.strip() for p in govde.split(",") if p.strip()}


def test_civi7_satir_semasi_KARTIN_alanlarini_kapsar():
    eksik = _kartin_satir_alanlari() - set(gi.SATIR_ALANLARI)
    assert not eksik, f"kart bu alanları istiyor, şemada yok: {sorted(eksik)}"


def test_civi7_yazilan_her_satir_semanin_TAMAMINI_tasir(sandbox_state):
    """Eksik anahtar, okuyucunun `get` varsayılanıyla sessizce dolar: "yazılmadı" ile "ölçülemedi"
    ayrımı kaybolurdu. Bir alan düşerse bu test kırılır (mutasyon (e))."""
    for r in _pk1_kosusu().values():
        assert set(r) == set(gi.SATIR_ALANLARI), \
            f"{r.get('plan_id')}: {set(gi.SATIR_ALANLARI) ^ set(r)}"


def test_civi7_kart_sabitleri_KARTLA_ayni_ve_kodda_gevsetilemez():
    """Eşik/pencere/n kartın YAML'ından okunur ve kodla karşılaştırılır: kod eşiği gevşetemez."""
    ham = KART_YOLU.read_text(encoding="utf-8")
    def _oku(alan):
        m = re.search(rf"^\s*{alan}:\s*([0-9.]+)", ham, re.M)
        assert m, f"kartta {alan} yok"
        return float(m.group(1))
    assert gi.KART == "EDG-2026-088"
    assert gi.N_ALT == _oku("n_alt_plan") == 30
    assert gi.CI_ALT_R == _oku("ci_alt_R_ust")
    assert gi.KAZANMA_ALT == _oku("kazanma_alt")
    assert gi.PENCERE_GUN == _oku("pencere_gun_ust") == 120
    assert gi.FARK_R_UST == _oku("golge_gercek_fark_R_ust")


# ============================ ÇİVİ 8 — İKİ KOL ==================================================
def test_civi8_dormant_ve_normal_plan_KOL_ile_ayrisir(sandbox_state):
    """PK (2)'nin paydası: aynı seansın iki kolu satırda ayrışır ve `ozet` ikisini ayrı sayar."""
    bars = {"AAA": _pk1_bars()["AAA"], "BBB": _pk1_bars()["BBB"]}
    bo = _bars_of(bars)
    gi.adim(D0, planlar=[_plan("P-a", "AAA", dormant=True, hukum="NO_GO"),
                         _plan("P-b", "BBB", dormant=False, hukum="GO")],
            bars_of=bo, regime_ok=True, params=PARAMS)
    gi.adim(D1, planlar=[], bars_of=bo, regime_ok=True, params=PARAMS)
    gi.adim(D2, planlar=[], bars_of=bo, regime_ok=True, params=PARAMS)
    sat = {r["plan_id"]: r for r in gi.kayit_al()}
    assert sat["P-a"]["kol"] == "dormant" and sat["P-b"]["kol"] == "kontrol"
    ozet = gi.ozet()
    assert ozet["kol_kirilimi"] == {"dormant": 1, "kontrol": 1}
    assert ozet["giren_hukum_dagilimi"] == {"GO": 1, "NO_GO": 1}, \
        "hüküm ELEME değil TANIdır: NO_GO planı da gölgeye girer (kart)"


def test_A2_K_paydasi_YALNIZ_dormant_kolunu_sayar(sandbox_state):
    """M3-01/M4-01: kontrol kolu PK (2)'nin sadakat ölçüsüdür, kartın hipotezinin PAYDASI değil.

    Aynı defterde iki kol: K bir satır sayar (uyuyan), kontrol satırı TANIda görünür ama
    n/toplam_r/kazanma_orani'na KARIŞMAZ.
    """
    bars = {"AAA": _pk1_bars()["AAA"], "BBB": _pk1_bars()["BBB"]}
    bo = _bars_of(bars)
    gi.adim(D0, planlar=[_plan("P-a", "AAA", dormant=True),
                         _plan("P-b", "BBB", dormant=False)],
            bars_of=bo, regime_ok=True, params=PARAMS)
    gi.adim(D1, planlar=[], bars_of=bo, regime_ok=True, params=PARAMS)
    gi.adim(D2, planlar=[], bars_of=bo, regime_ok=True, params=PARAMS)
    sat = {r["plan_id"]: r for r in gi.kayit_al()}
    assert sat["P-a"]["R"] is not None and sat["P-b"]["R"] is not None, "iki kol da kapanmadı"

    ozet = gi.ozet()
    assert ozet["n"] == 1, "kontrol kolu K paydasına karıştı"
    assert ozet["n_kontrol"] == 1, "kontrol kolu hiç sayılmıyor — tanı kayboldu"
    # Uyuyan kol AAA'dır: sert stop → R = −1. Kontrol kolu BBB (+1,5) toplama GİRMEZ.
    assert ozet["toplam_r"] == pytest.approx(-1.0, abs=1e-9)
    assert ozet["kazanma_orani"] == pytest.approx(0.0)
    assert ozet["giren_n"] == 2 and ozet["kol_kirilimi"] == {"dormant": 1, "kontrol": 1}


def test_A2_sayilir_yuklemi_OLCULDU_ile_KOL_u_BIRLIKTE_sorar():
    """Yüklem TEK YERDE yazılıdır ve iki şartı da taşır (sayım betiği bunu İTHAL eder)."""
    olculmus = {"kol": "dormant", "R": 0.5, "kaynak_bar_hash": "a" * 64,
                "bar_kaynak": gi.BAR_KAYNAKLARI[0]}
    assert gi.sayilir(olculmus) is True
    assert gi.sayilir({**olculmus, "kol": "kontrol"}) is False, "kol süzgeci yok"
    assert gi.sayilir({**olculmus, "R": None}) is False
    assert gi.sayilir({**olculmus, "kaynak_bar_hash": None}) is False
    assert gi.sayilir({**olculmus, "bar_kaynak": "foo"}) is False, "bar kaynağı süzgeci yok"
    # `olculdu` kol SORMAZ: kontrol kolunun PK (2) paydası bu yüklemle kurulur.
    assert gi.olculdu({**olculmus, "kol": "kontrol"}) is True


# ============================ ÇİVİ 9 — İDEMPOTENS ===============================================
def test_civi9_ayni_seans_ikinci_kez_HICBIR_SATIR_yazmaz(sandbox_state):
    bars = _pk1_bars()
    bo = _bars_of(bars)
    gi.adim(D0, planlar=[_plan("P-a", "AAA")], bars_of=bo, regime_ok=True, params=PARAMS)
    ilk = gi.adim(D1, planlar=[], bars_of=bo, regime_ok=True, params=PARAMS)
    n_once, doc_once = len(gi.kayit_al()), gi.acik_kayit()
    ikinci = gi.adim(D1, planlar=[_plan("P-b", "BBB")], bars_of=bo, regime_ok=True, params=PARAMS)
    assert ikinci["atlandi"] == "islenmis_seans" and ikinci["yeni_satir"] == 0
    assert ilk["atlandi"] is None
    assert len(gi.kayit_al()) == n_once
    assert gi.acik_kayit()["son_seans"] == doc_once["son_seans"] == D1
    assert list(gi.acik_kayit()["bekleyen_giris"]) == [], "atlanan seansta plan yakalandı"


def test_civi9_ayni_plan_IKI_KEZ_golgeye_girmez(sandbox_state):
    """Plan defteri kırpılıp yeniden okunsa bile aynı plan ikinci kez satır üretmez."""
    bars = {"AAA": _pk1_bars()["AAA"]}
    bo = _bars_of(bars)
    p = _plan("P-a", "AAA")
    gi.adim(D0, planlar=[p], bars_of=bo, regime_ok=True, params=PARAMS)
    gi.adim(D1, planlar=[p], bars_of=bo, regime_ok=True, params=PARAMS)
    gi.adim(D2, planlar=[p], bars_of=bo, regime_ok=True, params=PARAMS)
    assert len(gi.kayit_al()) == 1, gi.kayit_al()


# ============================ ÖZET: HÜKÜM YOK, BEDEL VAR ========================================
def test_ozet_bos_defterde_SAHTE_iyimserlik_uretmez(sandbox_state):
    """Kanıt yokken sayı uydurulmaz: n=0'da toplam/oran/PF None'dır (0.0 DEĞİL) ve pencere DOLMAZ."""
    o = gi.ozet()
    assert o["n"] == 0
    assert o["toplam_r"] is None and o["kazanma_orani"] is None and o["pf"] is None
    assert o["pencere"]["doldu"] is False and o["pencere"]["baslangic"] is None
    assert o["bedel"]["ag_cagri"] == 0 and o["bedel"]["llm_cagri"] == 0


def test_ozet_HICBIR_ESIK_HUKMU_dondurmez(sandbox_state):
    """Hüküm sayım betiğinin ve Rol-1'in işidir. Pano ucu 'geçti/kaldı' üretirse eşik kartın
    dışında ikinci kez yorumlanmış olurdu."""
    _pk1_kosusu()
    ham = json.dumps(gi.ozet(), ensure_ascii=False).lower()
    for yasak in ("gecti", "geçti", "kaldi", "kaldı", "hukum:", "go", "no_go"):
        if yasak in ("go", "no_go"):
            continue     # `hukum_dagilimi` kovaları plan hükmünün TANISIdır, motorun hükmü değil
        assert yasak not in ham, f"özet hüküm cümlesi taşıyor: {yasak}"
    assert "esik" not in ham and "eşik" not in ham


def test_ozet_bedeli_ve_pencereyi_OLCER(sandbox_state):
    """Bedel yasası: satır/gün ve defter baytı raporlanır; ağ/LLM çağrısı YAPISAL olarak sıfırdır."""
    _pk1_kosusu()
    o = gi.ozet()
    assert o["bedel"]["bayt"] and o["bedel"]["bayt"] > 0
    assert o["bedel"]["satir_gun"] is None or o["bedel"]["satir_gun"] >= 0
    assert o["pencere"]["gun"] == gi.PENCERE_GUN
    assert o["pencere"]["doldu"] is False, "n=4 < 30 iken pencere DOLMUŞ görünüyor"
    assert o["n_acik"] == 0 and o["son_seans"] == D3


def test_ozet_acik_pozisyonlari_ve_bekleyen_girisleri_SAYAR(sandbox_state):
    bars = {"CCC": _pk1_bars()["CCC"]}
    bo = _bars_of(bars)
    gi.adim(D0, planlar=[_plan("P-c", "CCC")], bars_of=bo, regime_ok=True, params=PARAMS)
    assert gi.ozet()["n_bekleyen_giris"] == 1 and gi.ozet()["n_acik"] == 0
    gi.adim(D1, planlar=[], bars_of=bo, regime_ok=True, params=PARAMS)
    assert gi.ozet()["n_acik"] == 1 and gi.ozet()["n_bekleyen_giris"] == 0


# ============================ C — DEFTER BÜTÜNLÜĞÜ (M1-02/03/07, M2-04, M4-06/09) ===============
def test_C1_DEFTER_ONCE_ACIK_SONRA_yazilir_cokme_KAYIP_uretmez(sandbox_state, monkeypatch):
    """Yazım sırası: satırlar ÖNCE diske, `ACIK` SONRA.

    Ters sırada (eski hâl) iki yazım arasındaki bir çökme KALICI KAYIP üretirdi: `son_seans`
    ilerlemiş, kapanan pozisyon `acik`ten düşmüş, satır hiç yazılmamış ve idempotens kapısı
    seansı yeniden koşturmaz. Yeni sırada aynı çökme MÜKERRER üretir — ve mükerrer okuyucuda
    kapanır (`plan_id` başına son satır), kayıp kapanmaz.
    """
    bars = {"AAA": _pk1_bars()["AAA"]}
    bo = _bars_of(bars)
    gi.adim(D0, planlar=[_plan("P-a", "AAA")], bars_of=bo, regime_ok=True, params=PARAMS)
    gi.adim(D1, planlar=[], bars_of=bo, regime_ok=True, params=PARAMS)

    gercek_write = store.write_json

    def _patla(ad, *a, **k):
        if ad == gi.ACIK:
            raise RuntimeError("ACIK yazımı düştü (sentetik çökme)")
        return gercek_write(ad, *a, **k)

    monkeypatch.setattr(store, "write_json", _patla)
    with pytest.raises(RuntimeError):
        gi.adim(D2, planlar=[], bars_of=bo, regime_ok=True, params=PARAMS)
    monkeypatch.setattr(store, "write_json", gercek_write)

    assert len(gi.kayit_al()) == 1, "satır ACIK yazımından ÖNCE diske düşmemiş — KAYIP riski"
    assert gi.acik_kayit()["son_seans"] == D1, "ACIK ilerlemiş ama satır yazılmamış olabilirdi"


def test_C1_MUKERRER_plan_id_TEKILLESTIRILIR_son_satir_kazanir(sandbox_state):
    """Çökme sonrası yeniden koşum aynı planı iki kez yazabilir; okuyucu TEKİLLEŞTİRİR."""
    bars = {"AAA": _pk1_bars()["AAA"]}
    bo = _bars_of(bars)
    gi.adim(D0, planlar=[_plan("P-a", "AAA")], bars_of=bo, regime_ok=True, params=PARAMS)
    gi.adim(D1, planlar=[], bars_of=bo, regime_ok=True, params=PARAMS)
    gi.adim(D2, planlar=[], bars_of=bo, regime_ok=True, params=PARAMS)
    ilk = gi.kayit_al()[0]
    ikinci = {**ilk, "R": ilk["R"] + 0.25}
    store.write_jsonl(gi.DEFTER, [ilk, ikinci])

    o = gi.ozet()
    assert o["n"] == 1, "mükerrer satır K paydasını şişirdi"
    assert o["toplam_r"] == pytest.approx(ikinci["R"], abs=1e-9), "son satır kazanmadı"
    assert o["mukerrer_n"] == 1, "mükerrerlik TANIda görünmüyor"


def test_C2_ATLANAN_SEANS_satirda_IZ_birakir_ve_K_disina_duser(sandbox_state):
    """Kancanın koşmadığı seans (HALT / bütçe 0 / kitap dolu / `golge_icra_failed`) İZSİZ kalmaz.

    Atlanan günde dokunulan stop görülmez ve `bars_held` eksik sayılır; satır yine de TAM çapayla
    K'ye girerse ölçüm delikli bir kümeyi tam gibi damgalar.
    """
    bars = {"CCC": _seri({D1: (101.0, 103.0, 100.0, 101.0),
                          D2: (101.0, 102.0, 100.0, 101.0),
                          D3: (100.5, 101.0, 100.0, 100.5),
                          "2026-07-07": (99.0, 99.0, 90.0, 91.0)})}
    bo = _bars_of(bars)
    gi.adim(D0, planlar=[_plan("P-c", "CCC")], bars_of=bo, regime_ok=True,
            params={"exit.time_stop_days": 9})
    gi.adim(D1, planlar=[], bars_of=bo, regime_ok=True, params={"exit.time_stop_days": 9})
    # D2 ve D3 ATLANDI (kanca koşmadı) — sonraki çağrı doğrudan 2026-07-07'dir.
    gi.adim("2026-07-07", planlar=[], bars_of=bo, regime_ok=True,
            params={"exit.time_stop_days": 9})

    doc = gi.acik_kayit()
    assert doc["atlanan_seanslar"], "atlanan seans ACIK belgesinde iz bırakmadı"
    sat = gi.kayit_al()
    assert len(sat) == 1 and sat[0]["R"] is not None, sat
    assert sat[0]["kaynak_bar_hash"] is None, "delikli kesit TAM çapa gibi damgalandı"
    assert (sat[0]["olculemedi"] or "").startswith("seans_atlandi:"), sat[0]["olculemedi"]
    assert gi.ozet()["n"] == 0, "atlanan seanslı satır K paydasına girdi"


def test_C3_tek_eksik_gun_bar_eksik_BIR_sayilir(sandbox_state):
    """M1-07: bekleyen çıkışı olan pozisyonda eksik gün faz 1a + faz 2'de İKİ KEZ sayılıyordu."""
    bars = {"KKK": _seri({D1: (101.0, 103.0, 100.0, 101.0),      # giriş
                          D3: (99.0, 99.0, 90.0, 91.0)})}        # D2 BARI YOK
    bo = _bars_of(bars)
    gi.adim(D0, planlar=[_plan("P-k", "KKK")], bars_of=bo, regime_ok=True, params=PARAMS)
    gi.adim(D1, planlar=[], bars_of=bo, regime_ok=False, params=PARAMS)   # kapanışta regime_flip
    assert gi.acik_kayit()["acik"]["P-k"]["bekleyen_cikis"] == "regime_flip"
    gi.adim(D2, planlar=[], bars_of=bo, regime_ok=True, params=PARAMS)    # bar YOK
    gi.adim(D3, planlar=[], bars_of=bo, regime_ok=True, params=PARAMS)
    sat = gi.kayit_al()
    assert len(sat) == 1, sat
    assert sat[0]["olculemedi"] == "bar_eksik:1", "tek eksik gün iki kez sayıldı"


def test_C4_HASH_kurulamayinca_NEDENI_adiyla_yazilir(sandbox_state):
    """M2-04: `eksik_bar == 0` iken hash None dönerse satır NEDENSİZ K dışına düşüyordu."""
    hacimsiz = _seri({D1: (101.0, 103.0, 100.0, 101.0),
                      D2: (99.0, 99.0, 90.0, 91.0)}).drop(columns=["volume"])
    bo = _bars_of({"VVV": hacimsiz})
    gi.adim(D0, planlar=[_plan("P-v", "VVV")], bars_of=bo, regime_ok=True, params=PARAMS)
    gi.adim(D1, planlar=[], bars_of=bo, regime_ok=True, params=PARAMS)
    gi.adim(D2, planlar=[], bars_of=bo, regime_ok=True, params=PARAMS)
    sat = gi.kayit_al()[0]
    assert sat["kaynak_bar_hash"] is None and sat["R"] is not None
    assert sat["olculemedi"] == "hash_yok:hane_eksik", sat["olculemedi"]
    o = gi.ozet()
    assert o["n"] == 0 and [x["neden"] for x in o["olculemeyen"]] == ["hash_yok:hane_eksik"]


def test_C5_BAR_KAYNAGI_kume_disi_ise_ADIM_REDDEDER(sandbox_state):
    """M4-09: `BAR_KAYNAKLARI` kapalı küme diye BEYANLI ama hiçbir yerde ZORLANMIYORDU."""
    bo = _bars_of({"AAA": _pk1_bars()["AAA"]})
    with pytest.raises(ValueError) as e:
        gi.adim(D0, planlar=[_plan("P-a", "AAA")], bars_of=bo, regime_ok=True, params=PARAMS,
                bar_kaynak="foo")
    assert "bar_kaynak" in str(e.value)
    for ad in gi.BAR_KAYNAKLARI:                      # POZİTİF KONTROL: kapı her şeyi reddetmiyor
        store.write_json(gi.ACIK, {})
        gi.adim(D0, planlar=[], bars_of=bo, regime_ok=True, params=PARAMS, bar_kaynak=ad)


def test_C5_KUME_DISI_bar_kaynagi_satiri_K_disinda_birakir(sandbox_state):
    """Deftere (eski sürüm / elle) küme dışı bir kaynak düşerse satır K'ye GİRMEZ, ADIYLA düşer."""
    bars = {"AAA": _pk1_bars()["AAA"]}
    bo = _bars_of(bars)
    gi.adim(D0, planlar=[_plan("P-a", "AAA")], bars_of=bo, regime_ok=True, params=PARAMS)
    gi.adim(D1, planlar=[], bars_of=bo, regime_ok=True, params=PARAMS)
    gi.adim(D2, planlar=[], bars_of=bo, regime_ok=True, params=PARAMS)
    bozuk = {**gi.kayit_al()[0], "bar_kaynak": "elle_yazilmis"}
    store.write_jsonl(gi.DEFTER, [bozuk])
    o = gi.ozet()
    assert o["n"] == 0, "beyanlı küme dışı kaynaklı satır K paydasına girdi"
    assert o["olculemeyen"][0]["neden"].startswith("bar_kaynak_bilinmiyor:"), o["olculemeyen"]


# ============================ B — PENCERE SAATİ (M1-08 / M2-02) =================================
def test_B_pencere_saati_ACIK_BEYANINDAN_olculur_ilk_satirdan_DEGIL(sandbox_state, monkeypatch):
    """Pencere kökü DAĞITIM anıdır (ilk `adim` seansı), defterin ilk satırının yazım anı DEĞİL.

    Kart penceresi "B1 dağıtımından itibaren ≤120 gün"dür. Kök ilk satıra bağlanınca geçen gün
    SİSTEMATİK olarak eksik sayılıyordu (ilk kapanış dağıtımdan günler/haftalar sonra doğar) →
    `suresi_doldu` geç, `doldu` erken: "eşiği hak etmeden geçme" yönünde yanlı.
    SAHNE: pencere D0'da açılır, ilk satır 10 gün SONRA yazılır → geçen gün 10 olmalı, 0 değil.
    """
    import datetime as dt

    from meridian import barclock
    bars = {"AAA": _pk1_bars()["AAA"]}
    bo = _bars_of(bars)
    gi.adim(D0, planlar=[_plan("P-a", "AAA")], bars_of=bo, regime_ok=True, params=PARAMS)
    assert gi.acik_kayit()["pencere_baslangic"] == D0, "pencere beyanı ilk adımda yazılmadı"

    yazim = dt.datetime(2026, 7, 11, tzinfo=dt.timezone.utc)      # D0 + 10 gün
    gi.adim(D1, planlar=[], bars_of=bo, regime_ok=True, params=PARAMS, simdi=yazim)
    gi.adim(D2, planlar=[], bars_of=bo, regime_ok=True, params=PARAMS, simdi=yazim)
    assert gi.acik_kayit()["pencere_baslangic"] == D0, "sonraki adım pencere beyanını EZDİ"

    monkeypatch.setattr(barclock, "now", lambda: yazim)
    p = gi.ozet()["pencere"]
    assert p["baslangic"] == D0 and p["baslangic_kaynagi"] == "acik.pencere_baslangic"
    assert p["gecen_gun"] == 10, "saat defterin ilk satırından sayılmış"
    assert str(p["ilk_satir_ts"]).startswith("2026-07-11"), p
    assert p["suresi_doldu"] is False and p["doldu"] is False


def test_B_pencere_BEYANI_YOKSA_gecen_gun_None_ve_NEDEN_adiyla(sandbox_state):
    """Beyan yoksa saat UYDURULMAZ: `gecen_gun` None + adlı neden (0 ya da "ilk satır" DEĞİL)."""
    p = gi.ozet()["pencere"]
    assert p["baslangic"] is None and p["gecen_gun"] is None
    assert p["doldu"] is False and p["suresi_doldu"] is False
    assert p["neden"], "pencere ölçülemedi ama nedeni yazılmadı"


def test_B_bedel_satir_gun_PAY_ve_PAYDA_ayni_pencereden(sandbox_state, monkeypatch):
    """Bedel yasası: pay (pencere içi satır) ile payda (pencere günü) AYNI pencereyi ölçer.

    Pencere dışı bir satır paya girerse satır/gün şişer ve "bedel ölçüldü" iddiası yanlış sayı
    taşır.
    """
    import datetime as dt

    from meridian import barclock
    yazim = dt.datetime(2026, 7, 11, tzinfo=dt.timezone.utc)
    bars = {"AAA": _pk1_bars()["AAA"]}
    bo = _bars_of(bars)
    gi.adim(D0, planlar=[_plan("P-a", "AAA")], bars_of=bo, regime_ok=True, params=PARAMS)
    gi.adim(D1, planlar=[], bars_of=bo, regime_ok=True, params=PARAMS, simdi=yazim)
    gi.adim(D2, planlar=[], bars_of=bo, regime_ok=True, params=PARAMS, simdi=yazim)
    # PENCERE ÖNCESİ bir satır defterin başına elle konur (eski kuşak / geri dolum artefaktı).
    eski = dict(gi.kayit_al()[0])
    eski.update({"plan_id": "P-eski", "ts": "2026-01-02T00:00:00+00:00"})
    store.write_jsonl(gi.DEFTER, [eski] + gi.kayit_al())

    monkeypatch.setattr(barclock, "now", lambda: yazim)
    o = gi.ozet()
    assert o["pencere"]["gecen_gun"] == 10
    assert o["bedel"]["satir_gun"] == pytest.approx(1 / 10, abs=1e-9), \
        "pay pencere DIŞI satırı da saymış (pay/payda ayrı pencereler)"


# ============================ H — DEFTER SÖZLEŞMESİ (ledgers) ===================================
def test_H_golge_defteri_SOZLESMEDE_ve_alanlar_SEMADAN_turetilir(sandbox_state):
    """Açık kalem kapandı: gölge defteri `ledgers.CONTRACTS`ta.

    ALANLAR KOPYA DEĞİL TÜRETME: sözleşme motorun şemasının KENDİSİNİ taşır — ikinci bir alan
    listesi, tam olarak bu sözleşmenin var olma sebebi olan sessiz ayrışmayı üretirdi.
    """
    from meridian import ledgers
    c = ledgers.CONTRACTS[gi.DEFTER]
    assert c.required is gi.SATIR_ALANLARI, "alan listesi KOPYALANMIŞ (türetme değil)"
    assert c.writers == ("golge_icra.py",) and c.key == "plan_id"
    assert gi.ACIK not in ledgers.CONTRACTS, "durum belgesi defter sözleşmesine sokulmuş"

    # MOTORUN YAZDIĞI GERÇEK SATIR sözleşmeye uyar (fikstür değil, üreticinin kendi satırı).
    bars = {"AAA": _pk1_bars()["AAA"]}
    bo = _bars_of(bars)
    gi.adim(D0, planlar=[_plan("P-2026-07-01-AAA", "AAA")], bars_of=bo, regime_ok=True,
            params=PARAMS)
    gi.adim(D1, planlar=[], bars_of=bo, regime_ok=True, params=PARAMS)
    gi.adim(D2, planlar=[], bars_of=bo, regime_ok=True, params=PARAMS)
    assert ledgers.validate_row(gi.DEFTER, gi.kayit_al()[0]) == []
    assert ledgers.validate_live(gi.DEFTER)["ok"] is True


def test_H_golge_yazari_STATIK_TARAMADA_gorunur():
    """`writer_violations`: beyan edilen yazar gerçekten yazıyor, beyan edilmeyen yazar yok."""
    from meridian import ledgers
    v = ledgers.writer_violations()
    assert gi.DEFTER not in v, v.get(gi.DEFTER)
    assert "golge_icra.py" in ledgers.declared_writers().get(gi.DEFTER, set())


def test_H_ACIK_belgesinin_sozlesme_DISI_kalma_gerekcesi_YAZILI():
    """Muafiyet BEYANLA olur: durum belgesinin neden defter sayılmadığı şerhte yazılı."""
    from meridian import ledgers
    ham = pathlib.Path(ledgers.__file__).read_text(encoding="utf-8")
    bas = ham.index(f'"{gi.DEFTER}": Contract(')
    blok = ham[max(0, bas - 1500):bas]
    assert gi.ACIK in blok and "DURUM" in blok.upper(), \
        "ACIK belgesinin sözleşme dışı kalma gerekçesi yazılmamış"


# ============================ YASA 4 / ÇAPA YASASI ==============================================
def test_yasa4_motorde_isaretsiz_sessiz_yakalayici_YOK():
    hits = [h for h in codelaw.scan_source(_kaynak(), "golge_icra.py")]
    assert hits == [], f"işaretsiz sessiz yakalayıcı: {hits}"


def test_capa_yasasi_motorde_satir_capasi_YOK():
    """Satır çapası (`dosya.py:NNN`) yasağı motor dosyasında da geçerlidir — satır kayar, yasa kırılır."""
    ihlal = [(n, m.group(0)) for n, s in enumerate(_kaynak().splitlines(), 1)
             if codelaw._CAPA_MUAFIYETI not in s
             for m in codelaw._CAPA_DESENI.finditer(s)]
    assert ihlal == [], ihlal
