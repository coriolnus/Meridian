"""test_altyapi_kucukler_v172.py — TEST-ALTYAPI + KÜÇÜKLER (2026-08-02).

DÖRT KALEM, TEK SINIF AİLESİ — "ölçülemedi, ölçüldü sanıldı":

  ① CONFTEST / `scheduler._state` SIZINTISI (test altyapısı). `test_regime_patch::
     test_scheduler_flag_survives_publish_lag` kısmi seçimlerde DÜŞÜYORDU: test yalnız
     `last_refetch_session`+`refetch_attempts` kuruyor, komşu bir testten devralınan
     `refetch_chase` merdiveni "son tarih doldu" dalına sokuyordu. Tek başına yeşil, paket
     içinde kırmızı — o an ölçülen şey dedektör değil SIRA'dır.

  ② `mutation.detector_red` DÜŞEN DEDEKTÖRÜ "BULGU YOK" SAYIYORDU (sahte-yeşil). C21'den beri
     `integrity_report` düşen dedektör için İSKELET döndürüyor (`starved: []` + `dedektor_dustu`);
     mutation.py iskeletin boş listesini "temiz" okuyordu. Sonuç: temel durum "TEMİZ" görünür,
     mutasyon "KAÇTI" (= körlük) sayılır — oysa görülüp görülmediği HİÇ ölçülmedi.

  ③ `intraday_shadow` yan tablonun İKİ bacağını okumuyordu. `entry_law[plan_id]` üç icra girdisi
     taşır; C18 yalnız `atr`i bağladı. `gap_at_submit` ÖLÇÜM DEĞİŞTİRİR (cancel grid noktasında
     canlı girmez, gölge girerdi → Faz 4b iyimser kanıt tabanı); `pivot` bugün hükmü değiştirmez
     ama çağrıyı canlı motorla argüman-argüman eşitler (C13'ün "bir motorda sessiz no-op" sınıfı).

  ④ WP-G kalanı: `bounds.yaml`daki emekli `regime.spy_sma_gate` satırı düşürüldü (8b6bbbc) ama
     DÜŞTÜĞÜ BEYAN EDİLMEMİŞTİ ve geri gelmesini yasaklayan bir çivi yoktu.

YÖNTEM: iddialar DAVRANIŞSAL. Sızıntı gerçek bir kirletici testle kurulur; düşen dedektör gerçek
bir istisna fırlatılarak üretilir; gölge motoru gerçekten koşturulup `fill_entry` çağrıları casusla
yakalanır. Her düzeltmenin yanında bir POZİTİF KONTROL vardır: düzeltmenin ölçtüğü farkı GERÇEKTEN
ürettiği ayrıca gösterilir — üretmeyen bir çivi koruma değil dekordur.
"""
from __future__ import annotations

import datetime as dt
import pathlib

import pytest
import yaml

from meridian import broker as BR, config, intraday_shadow, mutation, scheduler, store
from meridian.broker import PaperBroker

REPO = pathlib.Path(__file__).resolve().parent.parent

_SIMDI = dt.datetime(2026, 7, 27, 15, 40, 0, tzinfo=dt.timezone.utc)   # RTH içi (11:40 ET)


# =================================================================================================
# ① CONFTEST — `scheduler._state` sandbox girişinde BAŞLANGIÇ DEĞERİNE döner
# =================================================================================================
def _kirlet() -> None:
    """Kanıtlı vakanın kirleticisi: merdiven alanları bir sonraki teste taşınıyordu."""
    scheduler._state.update(refetch_chase="2026-07-17", refetch_sparse_attempts=3,
                            refetch_next_at="2026-07-18T20:00:00+00:00",
                            refetch_latest_bar="2026-07-17", last_refetch_coverage=0.0)


def test_conftest_scheduler_state_KIRLETME_bir_sonraki_teste_TASINMAZ(sandbox_state):
    """DAVRANIŞ: bu test sandbox'a girerken `_state` MODÜLÜN başlangıç değerindedir.

    ÇİFT KOŞULLU: hem kirletici alanlar YOK, hem de bilinen başlangıç anahtarları yerinde. Yalnız
    "refetch_chase yok" demek yetmezdi — `_state`i tümden boşaltan bir 'düzeltme' de o iddiayı
    geçerdi ve `advance_once` KeyError ile patlardı."""
    assert scheduler._state.get("refetch_chase") is None, \
        (f"`scheduler._state` kirli girildi: {scheduler._state.get('refetch_chase')!r} — komşu "
         f"testin merdiven artığı taşındı, suite SIRA BAĞIMLI")
    for alan in ("refetch_sparse_attempts", "refetch_next_at", "refetch_latest_bar"):
        assert scheduler._state.get(alan) is None, f"{alan} artığı taşındı: {scheduler._state[alan]!r}"
    for alan in ("last_processed", "last_tick", "cycles", "poll_seconds", "last_refetch_session"):
        assert alan in scheduler._state, \
            f"`{alan}` sıfırlamada KAYBOLDU — `_state` boşaltılmış, başlangıç değerine döndürülmemiş"
    assert scheduler._state["cycles"] == 0
    _kirlet()          # sıradaki test bunu GÖRMEMELİ (aşağıdaki ikiz, alfabetik olarak sonra koşar)


def test_conftest_scheduler_state_ZZ_ikinci_test_TEMIZ_girer(sandbox_state):
    """POZİTİF KONTROL ÇİFTİNİN İKİNCİ YARISI: yukarıdaki test `_state`i BİLEREK kirletti.

    Ad `..._ZZ_...` çünkü pytest dosya içinde TANIM SIRASINI korur ve çift ancak bu sırada anlam
    taşır; ad da sırayı okunur kılar. Bu test yeşilse sıfırlama GERÇEKTEN çalışıyor demektir —
    ilk testin tek başına yeşil olması hiçbir şey kanıtlamazdı (o zaten temiz bir süreçte koşar)."""
    assert scheduler._state.get("refetch_chase") is None, \
        ("bir önceki testin kirlettiği `refetch_chase` bu teste TAŞINDI — conftest sıfırlaması "
         "sandbox girişinde koşmuyor")
    assert scheduler._state.get("refetch_sparse_attempts") is None


def test_conftest_sifirlama_TABANI_uretim_modulunun_KENDI_literalinden_gelir():
    """FAZ İDDİASI (davranışla gösterilemez): taban elle yazılmış bir kopya DEĞİL, modülün kendi
    başlangıç değeridir — üretim tarafına eklenen bir alan sıfırlamayı sessizce eskitemez.

    `fmp._HEALTH` bugüne dek conftest'te KOPYA bir literalle sıfırlanıyordu; kopya bugün tutuyor
    ama tutmayı sürdüreceğinin garantisi yoktu. Çivi tam olarak o sürüklenmeyi ölçer."""
    # conftest `conftest` ADIYLA import EDİLEMEZ (pytest onu yol-türevli bir ad altında yükler);
    # yeniden import etmek İKİNCİ bir modül nesnesi ve İKİNCİ bir fotoğraf üretirdi — yani
    # koşumda gerçekten kullanılan tabanı değil, kopyasını ölçerdik. YÜKLÜ olan bulunur.
    import sys
    cf = next((m for m in sys.modules.values()
               if getattr(m, "__file__", "") and m.__file__.endswith("tests/conftest.py")), None)
    assert cf is not None, "yüklü conftest modülü bulunamadı — çivi ölçtüğünü sandığı şeyi ölçmüyor"
    from meridian.adapters import constituents as _con, fmp as _fmp, shortinterest as _si

    beklenen = {f"{m.__name__}.{a}" for m, a in ((scheduler, "_state"), (_fmp, "_HEALTH"),
                                                 (_con, "_HEALTH"), (_si, "_HEALTH"))}
    assert beklenen <= set(cf._MODUL_DURUMU0), \
        f"sıfırlama listesi eksik: {sorted(beklenen - set(cf._MODUL_DURUMU0))}"
    # ANAHTAR KÜMESİ ÜRETİMLE AYNI OLMALI: fotoğraf modülden alındıysa küme birebir tutar.
    assert set(cf._MODUL_DURUMU0["meridian.adapters.fmp._HEALTH"]) == set(_fmp.health()), \
        "fmp._HEALTH tabanı üretim sözlüğüyle ayrışmış — elle yazılmış literal sürüklenmesi"
    assert set(cf._MODUL_DURUMU0["meridian.scheduler._state"]) >= {
        "last_processed", "last_tick", "cycles", "started_at", "poll_seconds",
        "last_refetch_session"}


# =================================================================================================
# ② MUTASYON KOŞUMU — düşen dedektör "bulgu yok" DEĞİL, "ÖLÇÜLEMEDİ"
# =================================================================================================
def _dusuk_rapor(dusen_ad: str) -> dict:
    """`integrity_report`in C21 yalıtım biçimi: iskelet + `dedektor_dustu` (watchdog.py:863)."""
    from meridian import watchdog as wd
    rep = {}
    for ad in ("production", "conservation", "determinism", "coherence", "monotonicity",
               "ownership", "parity"):
        if ad == dusen_ad:
            rep[ad] = {**wd._DEDEKTOR_BOS.get(ad, {}), "ok": False, "dedektor_dustu": True,
                       "olculemedi": True, "error": "RuntimeError: defter okunamadı"}
        else:
            rep[ad] = {**wd._DEDEKTOR_BOS.get(ad, {}), "ok": True}
    return rep


@pytest.mark.parametrize("dusen_ad", ["production", "conservation", "determinism", "coherence",
                                      "monotonicity", "ownership", "parity"])
def test_mutasyon_dusen_dedektor_ADIYLA_RAPORLANIR(sandbox_state, monkeypatch, dusen_ad):
    """ASIL DÜZELTME: düşen dedektör SESSİZ kalmıyor — adıyla hem `dusen` sözlüğüne hem koşum
    defterine düşüyor. Eskiden iskeletin boş listesi 'bulgu yok' diye okunuyordu ve çöküşün
    kendisi hiçbir yere yazılmıyordu.

    JETON İDDİASI BİLEREK İKİNCİ SIRADA VE ÇEKİNCELİ: yedi dedektörün ALTISINDA iskelet zaten boş
    liste taşır (`starved: []` vb.), yani "kırmızı jeton üretmedi" hükmü orada YAPISAL olarak
    bedavadır ve tek başına hiçbir şey kanıtlamaz. Yük taşıyan tek vaka `determinism`dir (iskeleti
    `{}` + düşen dal `ok: False`) ve onun kendi testi ayrıca var — bu satır yalnız gerileme
    koruması olarak duruyor, kanıt olarak değil."""
    from meridian import watchdog as wd
    monkeypatch.setattr(wd, "integrity_report", lambda persist=False: _dusuk_rapor(dusen_ad))

    log: list = []
    dusen: dict = {}
    red = mutation.detector_red(log, dusen)

    assert dusen_ad in dusen and "RuntimeError" in dusen[dusen_ad], \
        f"düşen dedektör AYRI raporlanmadı: {dusen!r}"
    assert any(dusen_ad in m and "DÜŞTÜ" in m for m in log), \
        f"düşen dedektör koşum defterine yazılmadı (YASA 4 — sessiz yutma): {log!r}"
    assert not any(j.startswith(f"{dusen_ad}:") for j in red), \
        f"düşen `{dusen_ad}` dedektörü kırmızı jeton üretti ({sorted(red)}) — çöküş 'yakalandı' sayılır"


def test_mutasyon_dusen_DETERMINIZM_yanlis_KIRMIZI_uretmez(sandbox_state, monkeypatch):
    """AYRI VAKA, AYRI SINIF: determinizm iskeleti `{}` ve düşen dal `ok: False` taşır.

    Koşulsuz `not rep["determinism"].get("ok")` okuması, ÇÖKEN bir dedektörü "sessiz bar mutasyonu
    YAKALANDI" diye raporlardı. Yanlış-yeşilden beter: yanlış KIRMIZI, üstelik BAŞKA bir bulgunun
    adıyla — operatör var olmayan bir bar mutasyonunu kovalardı."""
    from meridian import watchdog as wd
    monkeypatch.setattr(wd, "integrity_report", lambda persist=False: _dusuk_rapor("determinism"))

    dusen: dict = {}
    red = mutation.detector_red([], dusen)

    assert "determinism:silent_bar_mutation" not in red, \
        "çöken determinizm dedektörü 'sessiz bar mutasyonu' bulgusu diye raporlandı"
    assert dusen.get("determinism"), "düşen determinizm dedektörü hiç raporlanmadı"


def test_mutasyon_GERCEK_bulgu_hala_KIRMIZI(sandbox_state, monkeypatch):
    """POZİTİF KONTROL: yalıtım gerçek bulguları YUTMADI.

    Bu olmadan yukarıdaki üç test, `detector_red`i tümden sustursak da yeşil kalırdı."""
    from meridian import watchdog as wd
    rep = _dusuk_rapor("parity")
    rep["production"] = {**rep["production"], "starved": [{"name": "fmp_source"}]}
    rep["determinism"] = {**rep["determinism"], "ok": False}
    monkeypatch.setattr(wd, "integrity_report", lambda persist=False: rep)

    red = mutation.detector_red([], {})

    assert "production:fmp_source" in red, "koşan dedektörün GERÇEK bulgusu yutuldu"
    assert "determinism:silent_bar_mutation" in red, "gerçek determinizm bulgusu yutuldu"
    assert not any(j.startswith("parity:") for j in red)


def test_mutasyon_KARNESI_olculemedi_satirini_BASAR():
    """DAVRANIŞ (YASA 6 — okuyucusuz yazım yok): alan üretiliyorsa raporda GÖRÜNÜR.

    Düşen dedektör ayrı bir sözlüğe yazılıp karneye hiç basılmasaydı, hiç ölçülmemiş olmakla aynı
    kapıya çıkardı."""
    res = {"n_mutations": 2, "n_caught": 1, "n_missed": 1, "coverage_pct": 50.0,
           "baseline_clean": True, "baseline_red": [],
           "baseline_olculemedi": {"parity": "RuntimeError: x"},
           "olculemedi": {"truncate_trades_ledger": {"coherence": "OSError: y"}},
           "n_olculemedi": 1,
           "rows": [{"mutation": "a", "caught": True, "detectors": ["production:z"]},
                    {"mutation": "truncate_trades_ledger", "caught": False, "detectors": []}],
           "blind_spots": [{"mutation": "truncate_trades_ledger", "note": "defter kısaldı",
                            "olculemedi": ["coherence"]}]}

    rapor = mutation.format_report(res)

    assert "ÖLÇÜLEMEDİ" in rapor, f"karnede ölçülemedi satırı YOK:\n{rapor}"
    assert "coherence" in rapor and "OSError" in rapor, \
        f"düşen dedektörün ADI/hatası karnede görünmüyor:\n{rapor}"
    # temel durum satırı "TEMİZ" derken çekinceyi de taşımalı
    baz = [s for s in rapor.splitlines() if s.startswith("temel durum")][0]
    assert "DÜŞTÜ" in baz and "parity" in baz, \
        f"'temiz' iddiası, ölçülemeyen dedektörü gizliyor: {baz!r}"
    # KAÇANLAR listesinde de damga var: bu mutasyon körlük DEĞİL, ölçümsüzlük olabilir
    kacan = [s for s in rapor.splitlines() if "truncate_trades_ledger" in s and s.strip().startswith("✗")]
    assert kacan and "ÖLÇÜLEMEDİ" in kacan[0], \
        f"kaçan satırı düşen dedektörü söylemiyor — ölçülmemiş körlük ölçülmüş gibi okunur: {kacan!r}"


def test_mutasyon_KARNESI_temiz_kosumda_OLCULEMEDI_YOK_der():
    """POZİTİF KONTROL: satır sabit metin değil — hiçbir dedektör düşmediyse karne bunu SÖYLER.
    ("ölçüldü ve sıfır" bir bilgidir; basılmayan sayaç ölçülmemiş sayaçtır.)"""
    res = {"n_mutations": 1, "n_caught": 1, "n_missed": 0, "coverage_pct": 100.0,
           "baseline_clean": True, "baseline_red": [], "baseline_olculemedi": {},
           "olculemedi": {}, "n_olculemedi": 0,
           "rows": [{"mutation": "a", "caught": True, "detectors": ["production:z"]}],
           "blind_spots": []}

    rapor = mutation.format_report(res)

    assert "ÖLÇÜLEMEDİ: yok" in rapor, f"temiz koşumda ölçüm beyanı basılmadı:\n{rapor}"
    baz = [s for s in rapor.splitlines() if s.startswith("temel durum")][0]
    assert "DÜŞTÜ" not in baz, f"düşen dedektör yokken çekince uyduruldu: {baz!r}"


# =================================================================================================
# ③ GÖLGE MOTORU — yan tablonun `pivot` + `gap_at_submit` bacakları
# =================================================================================================
@pytest.fixture
def saat(monkeypatch):
    from meridian import barclock
    monkeypatch.setattr(barclock, "now", lambda: _SIMDI)
    intraday_shadow.reset_dedup()
    yield _SIMDI
    intraday_shadow.reset_dedup()


def _fill_casusu(monkeypatch) -> list:
    """`PaperBroker.fill_entry`e giden çağrıları kaydet (gerçek fonksiyon yine koşar)."""
    cagrilar: list = []
    asil = PaperBroker.fill_entry

    def sarmal(self, plan, next_open, ts, equity, **kw):
        cagrilar.append({"plan_id": plan.get("id"), **kw})
        return asil(self, plan, next_open, ts, equity, **kw)

    monkeypatch.setattr(PaperBroker, "fill_entry", sarmal)
    return cagrilar


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


def test_golge_PIVOT_ve_GAP_yan_TABLODAN_fill_entry_e_gecer(sandbox_state, saat, monkeypatch):
    """DAVRANIŞ: `entry_law[plan_id]` ne taşıyorsa `fill_entry`e O gider — yeniden HESAPLANMAZ.

    C13'ün kapattığı kopukluk sınıfı: bir motor argümanı geçirmiyorsa knob terfi ettiğinde o
    motorda SESSİZ NO-OP olur ve iki motor ayrışır. Gölge o listede kalan son motordu."""
    plan = _plan()
    _kitap(sandbox_state, entry_law={plan["id"]: {"atr": 3.25, "limit": 106.6, "law": "E1-v1",
                                                  "pivot": 104.5, "gap_at_submit": False}})
    cagrilar = _fill_casusu(monkeypatch)

    satir = intraday_shadow.record(plan, _bar(o=100.0), _SIMDI)

    assert satir is not None and cagrilar, "gölge satırı yazılmadı — test ölçtüğünü ölçmüyor"
    c = cagrilar[0]
    assert "pivot" in c and "gap_at_submit" in c, \
        f"`fill_entry` iki bacak OLMADAN çağrıldı ({sorted(c)}) — canlı çağrıyla argüman ayrışması"
    assert c["pivot"] == 104.5, f"yapı çizgisi taşınmadı: {c['pivot']!r}"
    assert c["gap_at_submit"] is False, f"gönderim-anı hâli taşınmadı: {c['gap_at_submit']!r}"
    assert satir["pivot"] == 104.5 and satir["gap_at_submit"] is False, \
        "satır hangi girdilerle karar verildiğini BEYAN etmiyor (YASA 6 okuyucusu yok)"


def test_golge_yan_tablo_YOKSA_iki_bacak_da_OLCULEMEDI_ve_BEYANLI(sandbox_state, saat, monkeypatch):
    """UYDURMA YASAĞI: tabloda satır yoksa pivot 0.0 (=bilinmiyor), gap None KALIR.

    `gap_at_submit=False` yazmak "gap YOKTU" iddiasını uydurmak olurdu; broker sözleşmesinde
    None = "bu motorda gönderim anı YOK" ve veto ateşlemez — beyan edilmiş kapsam farkı."""
    _kitap(sandbox_state, entry_law={})     # tohumlanmış defter / yasa öncesi silahlanmış plan
    cagrilar = _fill_casusu(monkeypatch)

    satir = intraday_shadow.record(_plan(), _bar(o=100.0), _SIMDI)

    assert cagrilar[0]["pivot"] == 0.0, f"pivot yokken bir değer uyduruldu: {cagrilar[0]['pivot']!r}"
    assert cagrilar[0]["gap_at_submit"] is None, \
        f"ölçülemeyen gönderim anı False'a çevrildi (uydurma): {cagrilar[0]['gap_at_submit']!r}"
    assert satir["pivot"] is None and satir["gap_at_submit"] is None
    for alan in ("pivot_kaynak", "gap_at_submit_kaynak"):
        assert "ÖLÇÜLEMEDİ" in satir[alan] and "satır YOK" in satir[alan], \
            f"ölçülemeyen bacak beyan edilmiyor: {alan}={satir[alan]!r}"


def test_golge_UC_HAL_ayri_cumle_pivot_ve_gap(sandbox_state, saat):
    """ÜÇLÜ AYRIM ÜÇ BACAKTA DA: "tablo yok" bir KOPUKLUK, "alan None" MEŞRU bir ölçümsüzlüktür.

    Tek cümleye katlanırsa operatör gölge defterinde kopmuş bir kabloyu göremezdi (C18'in ATR için
    yazdığı ders; bacağa özel değil)."""
    plan = _plan()
    _kitap(sandbox_state, entry_law={plan["id"]: {"atr": None, "limit": 106.05,
                                                  "pivot": None, "gap_at_submit": None}})
    satir = intraday_shadow.record(plan, _bar(o=100.0), _SIMDI)

    for alan in ("atr_kaynak", "pivot_kaynak", "gap_at_submit_kaynak"):
        assert "var ama" in satir[alan], \
            f"'satır var, alan None' hâli 'satır yok' ile aynı cümleye katlandı: {alan}={satir[alan]!r}"
        assert "satır YOK" not in satir[alan], f"yanlış cümle: {alan}={satir[alan]!r}"
    # ve üç cümle BİRBİRİNDEN farklı: "ölçülemedi" her bacakta aynı SONUCU doğurmuyor
    assert len({satir["atr_kaynak"], satir["pivot_kaynak"], satir["gap_at_submit_kaynak"]}) == 3, \
        "üç bacak aynı genel cümleye düştü — okuyucu hangi korumanın kapandığını bilemez"
    assert "early_kill_pivot" in satir["pivot_kaynak"]
    assert "veto" in satir["gap_at_submit_kaynak"]


def test_golge_UCUNCU_HAL_olculdu_cumlesi(sandbox_state, saat):
    """Üçlünün ÜÇÜNCÜ hâli de ayrı: değer ölçüldüyse cümle 'sabitlendi' der, 'yok/None' demez."""
    plan = _plan()
    _kitap(sandbox_state, entry_law={plan["id"]: {"atr": 3.25, "limit": 106.6,
                                                  "pivot": 104.5, "gap_at_submit": True}})
    satir = intraday_shadow.record(plan, _bar(o=100.0), _SIMDI)
    for alan in ("atr_kaynak", "pivot_kaynak", "gap_at_submit_kaynak"):
        assert "sabitlendi" in satir[alan] and "ÖLÇÜLEMEDİ" not in satir[alan], \
            f"ölçülmüş bacak 'ölçülemedi' diye beyan edildi: {alan}={satir[alan]!r}"
    # `gap_at_submit=False` da ÖLÇÜLMÜŞ bir değerdir — None ile karıştırılmamalı
    intraday_shadow.reset_dedup()
    store.write_jsonl(intraday_shadow.ORDERS_FILE, [])
    _kitap(sandbox_state, entry_law={plan["id"]: {"atr": 3.25, "pivot": 104.5,
                                                  "gap_at_submit": False}})
    s2 = intraday_shadow.record(plan, _bar(o=100.0), _SIMDI)
    assert "sabitlendi" in s2["gap_at_submit_kaynak"], \
        f"`False` (ölçülmüş) hâli 'None' (ölçülemedi) sayıldı: {s2['gap_at_submit_kaynak']!r}"


def test_golge_GAP_VETOSU_cancel_noktasinda_ATESLER(sandbox_state, saat, monkeypatch):
    """POZİTİF KONTROL + ASIL BULGU: bacak taşınıyor değil, HÜKMÜ DEĞİŞTİRİYOR.

    `gap_behavior=cancel` grid noktasında canlı iki motor da girmez. Eski gölge argümanı hiç
    geçirmediği için None ile koşuyordu → veto ateşlemiyordu → canlının REDDEDECEĞİ dolumu
    `would_submit` diye yazıyordu. Aynı bar iki kez ölçülür: (a) gap=True → blocked+veto;
    (b) gap=False → would_submit. Yürürlükteki canlı nokta `marketable_limit`, yani bugün fark
    SIFIR — kırılma grid çevrildiği gün SESSİZCE açılırdı, o yüzden çivi burada."""
    plan = _plan()
    _yasa = BR.entry_law({"gap_behavior": BR.GAP_VETO})
    assert _yasa["gap_behavior"] == BR.GAP_VETO, "kurgu bozuk: veto noktası kurulamadı"
    monkeypatch.setattr(BR, "entry_law", lambda override=None: _yasa)

    _kitap(sandbox_state, entry_law={plan["id"]: {"atr": 3.25, "pivot": 104.5,
                                                  "gap_at_submit": True}})
    veto_satiri = intraday_shadow.record(plan, _bar(o=100.0), _SIMDI)

    intraday_shadow.reset_dedup()
    store.write_jsonl(intraday_shadow.ORDERS_FILE, [])
    _kitap(sandbox_state, entry_law={plan["id"]: {"atr": 3.25, "pivot": 104.5,
                                                  "gap_at_submit": False}})
    temiz_satir = intraday_shadow.record(plan, _bar(o=100.0), _SIMDI)

    assert veto_satiri["status"] == "blocked:broker_kurali", \
        f"gap vetosu ateşlemedi — gölge hâlâ canlının reddedeceği dolumu yazıyor ({veto_satiri['status']})"
    assert veto_satiri["red_nedeni"] == BR.EV_GAP_VETO, \
        f"vetonun SINIFI satırda yok ({veto_satiri['red_nedeni']!r}) — teşhis yutuldu"
    assert temiz_satir["status"] == "would_submit", \
        "gap=False dalında da bloklandı — pozitif kontrol çürük, test farkı ölçmüyor"


def test_golge_JETON_ADLARI_degismedi(sandbox_state, saat):
    """PANO SÖZLEŞMESİ: `status` jetonu sabit sözlükten gelir (app.js SH_TR sabit bir çeviri
    tablosu tutuyor). Yeni bir jeton orada çevrilmeden HAM görünürdü — teşhis ayrı alanda
    (`red_nedeni`), sınıf yerinde kalır."""
    plan = _plan()
    _kitap(sandbox_state, entry_law={plan["id"]: {"atr": 3.25, "pivot": 104.5,
                                                  "gap_at_submit": False}})
    satir = intraday_shadow.record(plan, _bar(o=100.0), _SIMDI)
    assert satir["status"] == "would_submit" or satir["status"].startswith("blocked:"), \
        f"gölge yeni bir status jetonu üretti: {satir['status']!r}"


def test_golge_defter_SOZLESMESI_bozulmadi(sandbox_state, saat):
    """Yeni alanlar eklendi ama `intraday_shadow_orders.jsonl` sözleşmesi (ledgers.CONTRACTS)
    hâlâ tutuyor — zorunlu alanların hiçbiri kaybolmadı."""
    from meridian import ledgers as lg
    plan = _plan()
    _kitap(sandbox_state, entry_law={plan["id"]: {"atr": 3.25, "pivot": 104.5,
                                                  "gap_at_submit": False}})
    satir = intraday_shadow.record(plan, _bar(o=100.0), _SIMDI)
    ihlaller = lg.validate_row(intraday_shadow.ORDERS_FILE, satir)
    assert not ihlaller, f"gölge satırı defter sözleşmesini ihlal etti: {ihlaller}"


# =================================================================================================
# ④ WP-G — emekli `regime.spy_sma_gate` bounds'tan DÜŞTÜ ve geri gelemez
# =================================================================================================
def test_wpg_bounds_ta_spy_sma_gate_SATIRI_YOK():
    """SESSİZ-DİRİLİŞ ÇİVİSİ: emekli knob arama uzayında yer TUTAMAZ.

    Hüküm EDG-2026-005 ile verildi (kill#1 tetiklendi, doğrudan etki OOS'ta TAM SIFIR) ve
    `regime.spy_sma_gate` PANO GÖSTERGESİNE emekli edildi — `blocks_new_entries` SABİT False.
    Satır bounds'ta kaldığı sürece makine onu ÖRNEKLEMEYE devam eder ve sonucu yapısal olarak
    sabit bir eksene bütçe yakar (6 değerlendirme böyle harcandı). Eşik değişikliği DEĞİLDİR:
    düşen şey bir sınır değil, hükümsüz bir eksendir."""
    b = config.bounds()
    assert "regime.spy_sma_gate" not in b, \
        ("emekli knob bounds'a GERİ GELDİ — makine etkisiz bir ekseni yeniden örnekler "
         "(EDG-2026-005 hükmü: gösterge, kapı değil)")
    # dosyadan da doğrula: `config.bounds()` önbellekli ve bir fikstür onu yamalayabilir
    ham = yaml.safe_load((REPO / "state" / "bounds.yaml").read_text())
    assert "regime.spy_sma_gate" not in ham, "satır bounds.yaml dosyasında duruyor"


def test_wpg_bounds_MEZAR_TASI_nereye_emekli_oldugunu_YAZIYOR():
    """YASA 6 + geri-alınabilirlik: düşen satırın NEREYE gittiği ve diriliş çivisinin NEREDE
    olduğu dosyada yazılı olmalı. Beyansız bir düşürme, altı ay sonra 'bu neden yok?' sorusuna
    cevapsız kalır ve satır iyi niyetle geri eklenir."""
    metin = (REPO / "state" / "bounds.yaml").read_text()
    assert "MEZAR TAŞI" in metin and "spy_sma_gate" in metin, "düşen satırın beyanı yok"
    assert "EDG-2026-005" in metin, "emeklilik kartı (hüküm kaynağı) yazılmamış"
    assert "regime.py" in metin, "yasanın NEREDE yaşamaya devam ettiği yazılmamış"
    assert "test_altyapi_kucukler_v172" in metin and "test_hafta3b_v125" in metin, \
        "sessiz-diriliş çivilerinin YERİ yazılmamış — mezar taşı okuyucusunu bulamaz"


def test_wpg_kalan_Y3_satirlari_ve_KAPALI_konumlari_DURUYOR():
    """POZİTİF KONTROL: düşürme komşularını yutmadı. Bir satır silinirken yanındakileri de
    götüren bir düzenleme, en sık yapılan bounds hatasıdır ve sessizdir."""
    b = config.bounds()
    for k in ("regime.vix_backwardation_gate", "portfolio.sector_cap", "portfolio.heat_cap"):
        assert k in b, f"{k} bounds'tan DÜŞTÜ — düşürme komşusunu götürdü"
        assert float(b[k]["min"]) == 0, f"{k} kapalı konumu (0) kayboldu"


def test_wpg_emekli_knob_KARAR_YOLUNU_hala_degistirmiyor():
    """İKİNCİ SAVUNMA HATTI (satır geri gelse DAHİ): knob 1 + endeks 200-SMA'nın ALTINDA iken
    kapı yine de yeni girişi KAPATMAZ — `blocks_new_entries` sabit False.

    Bu çivinin ikizi test_hafta3b_v125'te yaşıyor; buradaki kopya BİLEREK dar tutuldu (yalnız
    `entry_gates` hükmü), çünkü mezar taşı iki dosyaya birden atıf yapıyor ve atıflardan biri
    bayatlarsa mezar taşı yalan söylerdi."""
    import pandas as pd
    from meridian import regime
    dusen = pd.DataFrame({"close": [200.0 - i * 0.3 for i in range(260)]})
    eg = regime.entry_gates(dusen, {"regime.spy_sma_gate": 1})
    assert eg["spy_sma_gate"]["hukum"] == "altinda", "gösterge ÖLDÜ — emeklilik ölçümü de götürdü"
    assert eg["spy_sma_gate"]["blocks_new_entries"] is False, "emekli knob karar yolunu geri açtı"
    assert eg["blocks_new_entries"] is False and eg["blocking"] == []
