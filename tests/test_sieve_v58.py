"""test_sieve_v58.py — ELEME MUHASEBESİ + KÜNYE (2026-07-21).

Bu dosya, 866 testin YAKALAYAMADIĞI hata sınıfını hedefler. Neden yakalayamadılar? Çünkü her test
KENDİ fixture'ını kuruyor: üreticinin ve tüketicinin beklentisi aynı elden, aynı anda yazılıyor —
bu yüzden birbirlerinden AYRILAMIYORLAR. Canlıda ayrılmışlardı:

  * `trades.jsonl` ESKİ şemayla tohumlanmıştı (`setup`/`score` yok, `plan_id` = `P00001`) →
    90 gerçek işlemin 90'ı skor kalibrasyonundan ve gölge model eğitiminden SESSİZCE elendi.
    Panoda "gerçek 0 / simüle 241" yazıyordu; harmanlanmış tek sayı bunu gizliyordu.

Bu yüzden buradaki testler GERÇEK üreticileri çağırır (analytics.*, ShadowTradeOutcomeModel),
elle yazılmış beklenti sözlüklerini değil. Dört iddia:
  1. ELEME SAYILIR      — eski şemalı defter `sema:` elemesi ve ihlal üretir (asıl olayın testi).
  2. KURT MASALI YOK    — meşru `piyasa:` filtresi ihlal ÜRETMEZ (yoksa operatör uyarıyı susturur).
  3. SINIFSIZ NEDEN YOK — sınıflandırılmamış eleme nedeni reddedilir.
  4. KÜNYE ZORUNLU      — her kalibrasyon artefaktı payda + kaynak + zaman damgası taşır.
"""
from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from meridian import analytics, config, sieve, store
from meridian.shadow_model import ShadowTradeOutcomeModel as SM


@pytest.fixture
def seeded(sandbox_state):
    """Kum havuzu + gerçek goal/bounds (kalibrasyonlar goal() okur)."""
    repo = Path(__file__).resolve().parent.parent / "state"
    for f in ("goal.yaml", "bounds.yaml"):
        shutil.copy2(repo / f, sandbox_state / f)
    config.reload_config()
    from meridian import counterfactual as cf
    cf._LEDGER_IDS.update(mtime=None, ids=set())
    yield sandbox_state
    config.reload_config()


# ---------------------------------------------------------------- defter kurucular
def _eski_sema_trades(n: int = 40) -> list[dict]:
    """CANLIDAKİ defterin birebir eski şeması: `setup` YOK, `score` YOK, `plan_id` = `P00001`.
    Bunlar tam olarak 2026-07-21'de diskte duran 90 satırın şeklidir."""
    return [{"id": f"T{i}", "plan_id": f"P{i:05d}", "ticker": f"AAA{i}",
             "ts_open": "2026-05-01", "ts_close": "2026-05-08",
             "r_multiple": 1.0 if i % 2 else -0.8, "pnl_dollars": 500.0,
             "regime": "trend_up", "strategy_version": 1} for i in range(n)]


def _guncel_sema_trades(n: int = 40) -> list[dict]:
    """Sözleşmeye uyan defter — aynı üretici, uyumlu girdi."""
    return [{"id": f"T{i}", "plan_id": f"P-2026-05-0{1 + i % 8}-AAA{i}", "ticker": f"AAA{i}",
             "ts_open": "2026-05-01", "ts_close": "2026-05-08",
             "r_multiple": 1.0 if i % 2 else -0.8, "pnl_dollars": 500.0,
             "regime": "trend_up", "score": 60 + (i % 30), "setup": "breakout_vcp",
             "r_multiple_expected": 2.5, "mfe_r": 1.8, "mae_r": 0.4,
             "exit_reason": "target", "strategy_version": 1} for i in range(n)]


def _cf_rows(n: int = 40) -> list[dict]:
    return [{"id": f"CF-2026-05-01-B{i}-breakout_vcp", "date": "2026-05-01", "ticker": f"B{i}",
             "setup": "breakout_vcp", "score": 55 + (i % 40), "regime": "chop",
             "rr_expected": 2.5, "r_multiple_expected": 2.5, "status": "closed",
             "entered": True, "taken": False, "r_multiple": 0.6 if i % 3 else -1.0,
             "mfe_r": 1.2, "exit_reason": "target"} for i in range(n)]


# ================================================================ 1) ASIL OLAY
def test_eski_sema_defteri_score_calibrationda_sema_elemesi_uretir(seeded):
    """GERÇEK ÜRETİCİ, GERÇEK OLAY: eski şemalı 40 işlem + uyumlu 40 cf satırı.

    Eskiden `score_calibration` 241 (yalnız simüle) döndürür, pano bunu "n=241" diye gösterir ve
    gerçek işlemlerin TAMAMEN elendiği hiçbir yerde görünmezdi. Artık gerçek akış AYRI bir aşamadır:
    40 girdi / 0 çıktı → 'hepsi_elendi' + 'sema_elemesi' ihlali."""
    store.write_jsonl("trades.jsonl", _eski_sema_trades(40))
    store.write_jsonl("counterfactuals.jsonl", _cf_rows(40))

    out = analytics.score_calibration()
    assert out is not None and out["n"] == 40, "cf akışı beklendiği gibi çalışmalı"
    assert out["n_real"] == 0 and out["n_cf"] == 40, "canlı olayın birebir şekli: gerçek 0 / simüle 40"

    st = sieve.stages()
    gercek = st["score_calibration.gercek"]
    assert gercek["in"] == 40, "girdi sayılmadı — 'satır yoktu' ile 'satır elendi' hâlâ ayrılamıyor"
    assert gercek["out"] == 0
    assert sum(v for k, v in gercek["drops"].items() if k.startswith(sieve.SEMA)) == 40, \
        "40 satırın 40'ı da ŞEMA nedeniyle elenmiş olmalı"

    rep = sieve.report()
    assert rep["ok"] is False
    kurallar = {v["rule"] for v in rep["violations"] if v["stage"] == "score_calibration.gercek"}
    assert "hepsi_elendi" in kurallar and "sema_elemesi" in kurallar
    detay = next(v["detail"] for v in rep["violations"]
                 if v["stage"] == "score_calibration.gercek" and v["rule"] == "hepsi_elendi")
    assert "40" in detay and "elendi" in detay, "operatöre gösterilecek Türkçe açıklama eksik"


def test_eski_sema_defteri_golge_model_egitiminde_gercek_0_uretir(seeded):
    """'gerçek 0 / simüle 241'in doğduğu yer: `_features_of` → `return None`.

    Gölge model eski şemalı işlemlerin hiçbirini göremez. Model yine cf ile eğitilir (davranış
    korunur) ama artık payda YAZILI: n_real=0 ve "shadow_model.gercek" aşama dizgesi ihlal veriyor."""
    store.write_jsonl("trades.jsonl", _eski_sema_trades(40))
    store.write_jsonl("counterfactuals.jsonl", _cf_rows(60))

    X, y, n = SM._dataset()
    assert n == 60, "cf satırları eğitime girmeli (davranış korunuyor)"

    st = sieve.stages()
    assert st["shadow_model.gercek"]["in"] == 40
    assert st["shadow_model.gercek"]["out"] == 0, "eski şemalı GERÇEK işlemlerin hepsi elendi"
    assert st["shadow_model.cf"]["out"] == 60

    # kök neden ADIYLA sayılmalı: plan birleşmedi (P00001 ↔ P-YYYY-MM-DD-TICKER)
    assert st["shadow_model.gercek"]["drops"].get("sema:plan_join_yok") == 40

    rep = sieve.report()
    assert any(v["stage"] == "shadow_model.gercek" and v["rule"] == "hepsi_elendi"
               for v in rep["violations"]), "gölge modelin gerçek verisi sıfır ama kimse söylemiyor"

    m = SM().fit()
    m.save()
    prov = sieve.provenance_of(store.read_json("shadow_model.json", {}))
    assert prov is not None and prov["n_real"] == 0 and prov["n_cf"] == 60, \
        "n_fit tek başına yayınlanamaz — 'gerçek 0' künyede görünmeli"


def test_guncel_sema_defterinde_gercek_akis_kanit_uretir(seeded):
    """Kontrol ikizi: AYNI üreticiler, sözleşmeye uyan defter → sıfır `sema:` elemesi.
    (Yukarıdaki iki test, hatayı değil kurulumu ölçüyor olsaydı bu da kırılırdı.)"""
    store.write_jsonl("trades.jsonl", _guncel_sema_trades(40))
    out = analytics.score_calibration()
    assert out["n_real"] == 40 and out["n_cf"] == 0

    st = sieve.stages()["score_calibration.gercek"]
    assert st["in"] == 40 and st["out"] == 40 and st["drops"] == {}
    assert not [v for v in sieve.report()["violations"]
                if v["stage"].startswith("score_calibration")]


def test_rejimsiz_cf_kaniti_sayilir_ama_davranis_degismez(seeded):
    """ÜÇÜNCÜ CANLI OLAY: çözülmüş cf satırlarının %70'i `regime: "?"` taşıyordu, buna rağmen bir
    öneri üreteci o kanıttan `knob@rejim` tavsiyesi çıkarıyordu. Artık rejimsiz kanıt SAYILIR ve
    tırmandırılır — ama '?' kovası çıktıda yerinde kalır (muhasebe dürüstleşir, matematik değişmez)."""
    store.write_jsonl("counterfactuals.jsonl",
                      [{"id": f"C{i}", "entered": True, "r_multiple": 1.0, "status": "closed",
                        "regime": "chop" if i < 4 else "?"} for i in range(10)])
    edge = analytics.regime_edge()
    assert edge["?"]["n"] == 6 and edge["chop"]["n"] == 4, "davranış birebir korunmalı"

    st = sieve.stages()["regime_edge"]
    assert st["in"] == 10 and st["out"] == 4
    assert st["drops"]["sema:rejim_damgasız"] == 6
    assert any(v["rule"] == "sema_orani_yuksek" for v in sieve.report()["violations"]), \
        "%60 rejimsiz kanıt tek bozuk satırla aynı ağırlıkta olamaz"


# ================================================================ 2) KURT MASALI YOK
def test_mesru_piyasa_filtresi_ihlal_uretmez(seeded):
    """`cf_fidelity` cf satırlarının EZİCİ çoğunluğunu meşru olarak eler (alınmamış plan / gerçekte
    eşleşmemiş). Bu bir hata değil, sistemin çalıştığının kanıtıdır. Dedektör buna bağırırsa
    operatör uyarıyı susturmayı öğrenir ve gerçek `sema:` ihlali de görünmez olur."""
    store.write_jsonl("trades.jsonl", _guncel_sema_trades(40))
    rows = _cf_rows(40)
    for i, r in enumerate(rows):                 # 10 tanesi gerçekle örtüşsün, 30'u alınmamış olsun
        if i < 10:                               # anahtar: (tarih, ticker) — plan_id'den ayrıştırılan
            r.update(taken=True, date=f"2026-05-0{1 + i % 8}", ticker=f"AAA{i}")
    store.write_jsonl("counterfactuals.jsonl", rows)

    out = analytics.cf_fidelity()
    assert out is not None and out["n"] >= 5

    kes = sieve.stages()["cf_fidelity.kesisim"]
    assert kes["drops"], "eleme yapılmadıysa test bir şey kanıtlamıyor"
    assert all(k.startswith(sieve.PIYASA) for k in kes["drops"]), kes["drops"]

    ihlaller = [v for v in sieve.report()["violations"] if v["stage"] == "cf_fidelity.kesisim"]
    assert ihlaller == [], f"meşru piyasa filtresi ihlal sayıldı — kurt masalı: {ihlaller}"


def test_sadece_piyasa_elemesi_olan_asama_temiz_kalir():
    """Kısmi `piyasa:` eleme (out>0) hiçbir ihlal üretmez."""
    doc = {"x": {"in": 50, "out": 12, "drops": {"piyasa:skor_eşik_altı": 38}, "ts": "t"}}
    rep = sieve.report(doc)
    assert rep["ok"] is True and rep["violations"] == []
    assert rep["stages"]["x"]["piyasa_drops"] == 38 and rep["stages"]["x"]["sema_drops"] == 0


def test_tam_piyasa_silinmesi_kritik_degil_ama_sema_silinmesi_kritik():
    """KURT MASALI SINIRI (2026-07-22, canlıda `eleme:llm_opinion_calibration:hepsi_elendi` yanlış
    pozitifi): girdinin %100'ü elense bile (out=0) elemelerin HEPSİ `piyasa:` ise bu 'veri elendi'
    değil 'bu kanıt türü henüz yok'tur (replay'de LLM görüşü yok gibi) — kritik OLAMAZ. Aynı tam
    silinme `sema:` yüzündense (şema hatası) kritiktir. Ayrım, dedektörün değerini korur."""
    saf_piyasa = {"y": {"in": 129, "out": 0, "drops": {"piyasa:llm_görüşü_yok": 129}, "ts": "t"}}
    rep = sieve.report(saf_piyasa)
    assert rep["ok"] is True, "saf piyasa silinmesi kırmızı yakmamalı (operatör kırmızıyı susturur)"
    assert not any(v["rule"] == "hepsi_elendi" for v in rep["violations"])

    semali = {"z": {"in": 129, "out": 0, "drops": {"sema:plan_join_yok": 129}, "ts": "t"}}
    rep2 = sieve.report(semali)
    assert rep2["ok"] is False
    assert any(v["rule"] == "hepsi_elendi" for v in rep2["violations"])
    assert any(v["rule"] == "sema_elemesi" for v in rep2["violations"])


def test_sema_orani_esigi_asinca_tirmandirilir():
    doc = {"x": {"in": 100, "out": 85, "drops": {"sema:eksik_alan:score": 15}, "ts": "t"}}
    rep = sieve.report(doc)
    sevs = {v["rule"]: v["severity"] for v in rep["violations"]}
    assert sevs["sema_elemesi"] == "hata"
    assert sevs["sema_orani_yuksek"] == "kritik", "sistematik uyumsuzluk tek satırla aynı ağırlıkta olamaz"


# ================================================================ 3) SINIFSIZ NEDEN YOK
def test_siniflandirilmamis_neden_reddedilir(seeded):
    sv = sieve.Sieve("t.deneme", persist=False)
    for kotu in ("eksik alan", "", "SEMA:score", "bug:score", None):
        with pytest.raises(ValueError):
            sv.drop(kotu)
    sv.drop("sema:eksik_alan:score")             # sınıflı neden geçer
    sv.drop("piyasa:skor_eşik_altı")
    assert sv.n_in == 2 and sv.n_out == 0
    assert sieve.classify("sema:x") == "sema" and sieve.classify("piyasa:x") == "piyasa"


def test_asamasiz_elek_kurulamaz():
    with pytest.raises(ValueError):
        sieve.Sieve("")


def test_from_kept_girdiyi_iki_kez_saymaz():
    """Pencere kırpması (son 100 / son 30) da bir elemedir; ama satır girdiye İKİNCİ kez sayılırsa
    payda uydurma biçimde şişer ve muhasebe kendi kendine yalan söyler."""
    sv = sieve.Sieve("t.pencere", persist=False)
    sv.keep(120)
    sv.drop("piyasa:taze_pencere_dışı", n=20, from_kept=True)
    assert sv.n_in == 120 and sv.n_out == 100


def test_elek_baglam_yoneticisi_istisnayi_yutmaz_ama_muhasebeyi_yazar(seeded):
    with pytest.raises(RuntimeError):
        with sieve.Sieve("t.patlak") as sv:
            sv.keep(3)
            sv.drop("sema:eksik_alan:score")
            raise RuntimeError("boom")
    st = sieve.stages()["t.patlak"]
    assert st["in"] == 4 and st["out"] == 3, "istisna anına kadarki muhasebe diske düşmeli"


# ================================================================ 4) KÜNYE ZORUNLU
# Elle kopyalanmış sözlük YOK: künye iddiası GERÇEK üretici fonksiyonlardan sürülür. Yeni bir
# kalibrasyon üreticisi eklenip bu listeye yazılmazsa gözden kaçar; yazılırsa künyesiz geçemez.
PRODUCERS = [
    ("score_calibration", lambda: analytics.score_calibration()),
    ("llm_opinion_calibration", lambda: analytics.llm_opinion_calibration()),
    ("exit_efficiency", lambda: analytics.exit_efficiency()),
    ("cf_fidelity", lambda: analytics.cf_fidelity()),
    ("near_miss_report", lambda: analytics.near_miss_report()),
    ("regime_edge", lambda: analytics.regime_edge()),
    ("shadow_model.promotion", lambda: SM.evaluate_promotion()),
    ("shadow_model.state", lambda: (SM().fit().save(), store.read_json("shadow_model.json", {}))[1]),
]


def _kanit_defteri() -> None:
    """Her üreticinin GERÇEKTEN çıktı vereceği kadar uyumlu kanıt (eşikler: 30 / 10 / 5)."""
    trades = _guncel_sema_trades(40)
    plans = []
    for i, t in enumerate(trades):
        t["llm_opinion"] = "destekle" if i % 2 else "karşı"
        plans.append({"id": t["plan_id"], "date": "2026-05-01", "ticker": t["ticker"],
                      "setup": "breakout_vcp", "score": t["score"], "entry_trigger": 100.0,
                      "stop": 95.0, "gate_verdict": "GO", "strategy_version": 1,
                      "llm_opinion": t["llm_opinion"], "p_win_shadow": 0.55,
                      "regime_at_plan": "trend_up", "r_multiple_expected": 2.5})
    rows = _cf_rows(60)
    for i, r in enumerate(rows):
        r["llm_opinion"] = "destekle" if i % 2 else "karşı"
        if i < 12:                                # cf ↔ gerçek kesişimi (cf_fidelity ≥5 ister)
            r.update(taken=True, date="2026-05-0" + str(1 + i % 8), ticker=f"AAA{i}")
        if i >= 40:                               # eşik-altı gölge adaylar (near_miss_report)
            r.update(near_miss=True, blocked_by=["entry.min_score"])
    store.write_jsonl("trades.jsonl", trades)
    store.write_jsonl("trade_plans.jsonl", plans)
    store.write_jsonl("counterfactuals.jsonl", rows)


@pytest.mark.parametrize("ad,uretici", PRODUCERS, ids=[p[0] for p in PRODUCERS])
def test_her_kalibrasyon_artefakti_kunye_tasir(seeded, ad, uretici):
    """KURAL: hiçbir toplulaştırılmış sayı PAYDASI ve KAYNAĞI olmadan var olamaz.
    'gerçek 0 / simüle 241' tam olarak bu kural olmadığı için görünmezdi."""
    _kanit_defteri()
    art = uretici()
    assert art is not None, f"{ad}: üretici çıktı vermedi — test bir şey kanıtlamıyor"

    prov = sieve.provenance_of(art)
    assert prov is not None, f"{ad}: künye (`{sieve.PROV_KEY}`) yok — paydasız sayı yayınlanıyor"
    assert isinstance(prov.get("n_total"), int), f"{ad}: payda yok"
    assert prov.get("generated"), f"{ad}: üretim zaman damgası yok (bayat sayı taze görünür)"
    assert prov.get("source"), f"{ad}: kaynak beyanı yok"

    if "n_real" in prov or "n_cf" in prov:
        assert prov["n_real"] + prov["n_cf"] == prov["n_total"], \
            f"{ad}: kırılım paydayı tutmuyor — {prov}"
    else:
        # kırılım anlamsız olabilir (kesişim, dışarıdan matris) AMA bu AÇIKÇA yazılmalı
        assert prov["source"] in (sieve.SRC_INTERSECTION, sieve.SRC_UNKNOWN_INPUT), \
            f"{ad}: kırılım yok ve nedeni beyan edilmemiş ({prov['source']})"


def test_kunye_kirilim_da_kaynak_da_yoksa_uretilemez():
    """Künye uydurmaya karşı yapısal kilit: kırılım verilmediyse kaynak AÇIKÇA beyan edilmeli."""
    with pytest.raises(ValueError):
        sieve.provenance(100)
    assert sieve.provenance(100, 0, 100)["source"] == sieve.SRC_CF_ONLY
    assert sieve.provenance(100, 100, 0)["source"] == sieve.SRC_REAL_ONLY
    assert sieve.provenance(100, 40, 60)["source"] == sieve.SRC_MIXED
    assert sieve.provenance(0, 0, 0)["source"] == sieve.SRC_EMPTY


def test_regime_edge_kunyesi_rejim_sanilamaz(seeded):
    """CANLI TÜKETİCİ TUZAĞI: regime_edge.json'un KÖKÜ 'rejim adı → istatistik' haritasıdır ve iki
    tüketici (watchdog ölçülen-edge dedektörü, hermes kanıt paketi) `n` alanı olan HER sözlüğü rejim
    sayar. Künyede `n` olsaydı sahte bir rejim gibi sayılır ve watchdog'un 'her rejimde edge negatif'
    alarmını paydayı şişirerek SUSTURABİLİRDİ — yani künye eklemek yeni bir sessiz hata doğururdu."""
    _kanit_defteri()
    out = analytics.regime_edge()
    prov = sieve.provenance_of(out)
    assert prov is not None and "n" not in prov, "künye `n` taşıyamaz — rejim sanılır"
    rejim_gibi = {k: v for k, v in out.items()
                  if isinstance(v, dict) and (v.get("n") or 0) >= 20}
    assert sieve.PROV_KEY not in rejim_gibi
    assert set(out) - {sieve.PROV_KEY} <= set(config.VALID_REGIMES) | {"?"}


def test_kunye_gercek_ve_simule_kirilimini_ayirir(seeded):
    """Künyenin asıl işi: harmanlanmış tek rakamın arkasındaki iki paydayı ayırmak."""
    store.write_jsonl("trades.jsonl", _eski_sema_trades(40))     # gerçek → hepsi elenecek
    store.write_jsonl("counterfactuals.jsonl", _cf_rows(40))
    prov = sieve.provenance_of(analytics.score_calibration())
    assert prov["n_total"] == 40 and prov["n_real"] == 0 and prov["n_cf"] == 40
    assert prov["source"] == sieve.SRC_CF_ONLY, "yalnız simüle veriye dayanan sayı öyle etiketlenmeli"
    assert "score_calibration.gercek" in prov["stages"], "künye kendi eleme muhasebesine bağlanmalı"


# ================================================================ SIFIR YETKİ
def test_elek_hicbir_karar_vermez_ve_yalniz_kendi_dosyasini_yazar():
    """sieve.py SAYAR ve RAPOR EDER; karar vermez. Bir 'dürüstlük katmanı'nın kendisi yetki
    kazanırsa ölçtüğü şeyi bozar."""
    import ast
    import pathlib
    src = pathlib.Path("meridian/sieve.py").read_text()
    tree = ast.parse(src)
    called = {n.func.attr for n in ast.walk(tree)
              if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)}
    for yasak in ("commit", "dump_yaml", "submit", "write_heartbeat", "close_position", "halt"):
        assert yasak not in called, f"eleme muhasebesi yetki kullanıyor: {yasak}"
    yazilan = {n.args[0].value for n in ast.walk(tree)
               if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
               and n.func.attr in ("write_json", "write_jsonl", "append_jsonl", "update_json")
               and n.args and isinstance(n.args[0], ast.Constant)}
    assert yazilan <= {sieve.SIEVE_FILE} or not yazilan
