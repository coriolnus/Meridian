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
    """Kalan iki red dalı: limit tavanı aşıldı · açılış planlanan stopun ALTINDA."""
    bars = {"GGG": _seri({D1: (120.0, 125.0, 119.0, 124.0)}),      # limit = 100·1,04 = 104
            "HHH": _seri({D1: (94.0, 101.0, 93.0, 100.5)})}        # tetik geldi ama açılış < stop
    bo = _bars_of(bars)
    gi.adim(D0, planlar=[_plan("P-g", "GGG"), _plan("P-h", "HHH")], bars_of=bo,
            regime_ok=True, params=PARAMS)
    gi.adim(D1, planlar=[], bars_of=bo, regime_ok=True, params=PARAMS)
    sat = {r["plan_id"]: r for r in gi.kayit_al()}
    assert sat["P-g"]["giris_reddi"] == "limit_asildi"
    assert sat["P-h"]["giris_reddi"] == "acilis_stop_altinda"
    assert all(sat[p]["R"] is None and sat[p]["cikis_neden"] == gi.GIRIS_YOK for p in sat)
    assert set(gi.GIRIS_REDLERI) >= {sat[p]["giris_reddi"] for p in sat}


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
    """YASA 6'NIN AÇIK KALEMİ, BEYANLA DEĞİL ÖLÇÜMLE.

    Bu görev (B1 Task 1) motoru doğurur ama okuyucusunu doğurmaz: dış okuyucu `meridian/api.py` →
    `golge_icra.ozet()` Task 2'nindir. Dolayısıyla BUGÜN canlı ağaçta iki artefakt `unread`tır ve
    `tests/test_codelaw_v59.py` ile `tests/test_golge_v2_yasam_dongusu_v132.py`nin genel ihlal
    çivileri KIRMIZIDIR. Bu bilinen ve ADI KONMUŞ bir açık kalemdir.

    `DECLARED_SINKS` BİLEREK KULLANILMADI: beyan "bu artefaktın üretimde okuyucusu YOK" demektir ve
    burada YANLIŞ olurdu — okuyucu var, henüz yazılmadı. Yanlış beyan, Task 2 okuyucuyu ekleyince
    `stale_sinks` ihlaline dönerdi; yani muafiyet borcu kapatmaz, sınıfını değiştirirdi.

    ÇİVİ ŞUNU ÖLÇER: ihlalin sebebi GERÇEKTEN dış okuyucu eksikliğidir. Motorun KENDİ kaynağı
    sentetik bir ağaca kopyalanır; okuyucusuz hâlde iki ad `violations`tadır, `ozet`i çağıran tek
    bir dış modül eklenince İKİSİ DE düşer. Task 2 tam olarak o modülü canlıya koyar.
    """
    (tmp_path / "golge_icra.py").write_text(_kaynak(), encoding="utf-8")
    okuyucusuz = codelaw.artifact_graph(str(tmp_path))
    assert sorted(okuyucusuz["violations"]) == sorted([gi.ACIK, gi.DEFTER]), \
        okuyucusuz["violations"]

    (tmp_path / "api.py").write_text(                       # Task 2'nin dış okuyucusunun taslağı
        "from . import golge_icra, store\n"
        "def golge_icra_ucu():\n"
        "    store.read_jsonl(golge_icra.DEFTER)\n"
        "    store.read_json(golge_icra.ACIK, {})\n"
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


def test_civi5_D0_KAPANISI_ve_CIKIS_SONRASI_barlar_sonucu_DEGISTIRMEZ(sandbox_state, tmp_path):
    """İki koşum, iki ağaç: (a) D0 barları uçurulmuş, (b) çıkıştan SONRAKİ barlar uçurulmuş.
    Satırlar (yazım anı hariç) BİREBİR aynı kalmalı — aksi hâlde motor geleceğe bakıyordur."""
    temiz = _pk1_kosusu()

    kirli = _pk1_bars()
    for tk in kirli:
        # D0 KAPANIŞI: girişte kullanılmamalı → uçur.
        kirli[tk] = pd.concat([kirli[tk], pd.DataFrame(
            [{"open": 500.0, "high": 900.0, "low": 1.0, "close": 700.0, "volume": 1.0}],
            index=pd.DatetimeIndex([pd.Timestamp(D0)], name="date"))]).sort_index()
        # ÇIKIŞ SONRASI: pencerenin son gününden sonraki bar → hiçbir satıra dokunmamalı.
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


# ============================ ÇİVİ 6 — PIT / kaynak_bar_hash ====================================
def test_civi6_bar_hash_ayni_barlar_AYNI_tek_hane_FARKLI():
    kesit = [["AAA", "2026-07-02", 101.0, 103.0, 100.0, 101.0, 2_000_000.0]]
    kesit2 = [["AAA", "2026-07-02", 101.0, 103.0, 100.0, 101.0, 2_000_000.0]]
    assert gi.bar_hash(kesit) == gi.bar_hash(kesit2) is not None
    for i in range(2, 7):
        bozuk = [list(kesit[0])]
        bozuk[0][i] = bozuk[0][i] + 0.01
        assert gi.bar_hash(bozuk) != gi.bar_hash(kesit), f"hane {i} hash'i değiştirmedi"


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
    assert ozet["hukum_dagilimi"] == {"GO": 1, "NO_GO": 1}, \
        "hüküm ELEME değil TANIdır: NO_GO planı da gölgeye girer (kart)"


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
