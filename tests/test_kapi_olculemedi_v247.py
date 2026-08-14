"""test_kapi_olculemedi_v247.py — ÖLÇÜLEMEDİ ≠ GEÇTİ (28f) + p=0,000'in İKİ GERÇEĞİ (28e).

Bu deponun en pahalı hata SINIFI: **ölçülemeyen bir şeyi geçmiş saymak.** ROADMAP §28f onu ship
kapısında adıyla yakaladı — H00029 (v0003, `entry.w_prox` None→0,15) `confirm_p=null`,
`confirm_n_valid=0` ile SHIP edildi; yani teyit yürüyüşü HİÇBİR HÜKÜM VERMEDEN atlandı ve
ölçülemeyen bir no-op canlıya çıktı. Aynı sınıf ikinci kez arama ayağında ölçüldü: dilimler VARKEN
olasılıksal yasa ölçemeyince kapı sessizce DAHA GEVŞEK bir yasaya (bileşik nokta-marj) düşüp
adayı GEÇİRİYORDU.

İKİ AYRI DÜZELTME, TEK İLKE — kapı kararı ÜÇ DEĞERLİdir: geçti · geçmedi · **ölçülemedi**.
Üçüncüsü ship'i ENGELLER (fail-closed) ve nedeni kayda ADIYLA girer. Bu bir EŞİK değişikliği
DEĞİL, TANIM düzeltmesidir: hiçbir eşiğe (P_BASE, P_CONFIRM, GATE_MARGIN, min_sample) dokunulmadı.

28e ise bir RAPORLAMA doğruluğu: `p = np.mean(arr > 0)` KESİN eşitsizlik olduğu için bit-bit AYNI
aday da 0,000 alıyordu. Defterdeki beş 0,000'ın DÖRDÜ no-op'tu (yapısal olarak atıl düğmeler),
biri gerçek felaket — ve defter ikisini ayırt edilemez yazıyordu. Ayrım EK alandır; `p`nin anlamı
ve `passes` hükmü DEĞİŞMEDİ.

GERİYE DÖNÜK DÜZELTME YOK: H00029 defterde ship olarak KALIR (retro-düzeltme tarihçeyi bozar).

Deterministik: sabit tohumlar, ağ yok, gerçek replay yok, canlı state'e yazım yok.
"""
from __future__ import annotations

import datetime as dt
import inspect
from pathlib import Path
import shutil

import pytest

from meridian import backtest, config, reflect, store
from meridian.oos_pipeline import OutOfSamplePipeline
from meridian.probgate import (PairedProbabilisticGate as Gate, META_FILE,
                               AYRIM_AYNI, AYRIM_KISMEN, AYRIM_FARKLI)
from tests import wf_fixtures as wf

N_BOOT = 600            # p'nin MC hatası ~0.02; buradaki iddialar 0.1+ uzakta


@pytest.fixture
def seeded(sandbox_state):
    """sandbox_state goal/bounds'u kopyalar; kapı meta-kalibrasyonu nötrlenir (eşik oynamasın).

    `strategy.yaml` BİLEREK KOPYALANMAZ: kopyalanırsa sandbox'ın incumbent sürümü depodaki canlı
    sürüme (bugün 4) eşitlenir ve `versioning.bump` adaya 5 verir — fikstür haritası sessizce
    ıskalar. Sürüm kimliği testin konusu değil; `_submit` zaten sürümden BAĞIMSIZ eşleştirir."""
    repo = Path(__file__).resolve().parent.parent / "state"
    for f in ("goal.yaml", "bounds.yaml"):
        src = repo / f
        if src.exists():
            shutil.copy2(src, sandbox_state / f)
    store.write_json(META_FILE, {"extra_p": 0.0})
    config.goal.cache_clear(); config.bounds.cache_clear()
    yield sandbox_state
    config.goal.cache_clear(); config.bounds.cache_clear()


def _submit(monkeypatch, inc_wf, cand_wf, **prop):
    """submit()'i fikstür walk'larla koştur — ship yetkisinin TAM yolu (guard→kapı→teyit→DSR/PBO).

    EŞLEŞTİRME SÜRÜM NUMARASIYLA DEĞİL, KİMLİKLE: `versioning.bump` aday sürümünü incumbent'ın
    sürümünden türetir ve o sayı sandbox'ın `strategy.yaml`ına bağlıdır. Sabit bir `{1: inc, 2: cand}`
    haritası, sürüm tabanı değiştiği an `KeyError` ile ya da (daha kötüsü) YANLIŞ fikstürle koşardı."""
    inc_v = int(config.load_strategy().get("version", 1))
    monkeypatch.setattr(backtest, "walk_forward",
                        lambda *a, **k: dict(inc_wf if k.get("strategy_version") == inc_v else cand_wf))
    monkeypatch.setattr(reflect.dataset, "load", lambda **k: (None, None))
    reflect._INC_CACHE.clear(); reflect._PROBE_CACHE.clear()
    return reflect.submit({"variable": "stop_loss_atr_mult", "new": 2.1, "source": "t",
                           "predicted_delta": 0.99, **prop})


def _kod(fn) -> str:
    """Kaynak-üzerinde iddia edenlerin KLASİK TUZAĞI: kusuru ANLATAN yorum, kusurun KENDİSİ sanılıp
    eşleşiyor. Bu dosyada gerçek bir vaka oldu — `# ESKİSİ: if conf.law == "probabilistic":` yorumu,
    aranan KOD satırından önce geldiği için sıralama iddiasını ters çevirdi. Yalnız YÜRÜTÜLEN
    gövdeye bakılır: docstring ve `#` yorumları atılır."""
    src = inspect.getsource(fn)
    doc = inspect.getdoc(fn)
    if doc:
        src = src.replace(doc, "")
    return "\n".join(s for s in src.splitlines() if not s.strip().startswith("#"))


# =================================================================================================
# 28f — SHIP KAPISI: "ÖLÇÜLEMEDİ" ARTIK "GEÇTİ" DEĞİL
# =================================================================================================
def test_28f_teyit_OLCULEMEZKEN_ship_ENGELLENIR(seeded, monkeypatch):
    """H00029'un SINIFI. Aday arama diliminde açık ara kazanıyor (search_p=1,0) ama teyit dilimi
    tabanın altında (6 < 21) → `confirm()` `law="legacy"`, `p=None`, `n_valid=0` döner ve gerekçesi
    LİTERAL olarak 'ship yetkisi bu kanıtla verilemez' der. ESKİ kod tam o satırda `if conf.law ==
    "probabilistic"` diyerek bloğun TAMAMINI atlıyor ve adayı SHIP ediyordu."""
    goal = config.goal()
    inc_s = wf.trades(120, 1, wf.S_LO, wf.S_END, 0.05)
    cand_s = [{**t, "r_multiple": round(t["r_multiple"] + 0.6, 3),
               "pnl_dollars": round(t["pnl_dollars"] + 240.0, 2)} for t in inc_s]
    inc_c, cand_c = wf.trades(6, 3, wf.S_END, wf.OOS_END, 0.0), wf.trades(6, 4, wf.S_END, wf.OOS_END, 0.0)
    wi, wc = wf.wf_from_trades(inc_s + inc_c, goal), wf.wf_from_trades(cand_s + cand_c, goal)
    # kurgu geçerliliği: ARAMA ayağı gerçekten geçiyor, düşen tek şey TEYİT olmalı
    passes, gate, _why = reflect._gate_eval(wi, wc, k_probes=1)
    assert passes and gate["gate_law"] == "probabilistic", "kurgu geçersiz: arama ayağı zaten düşüyor"
    assert len(wi["_trades_confirm"]) < 21 and len(wc["_trades_confirm"]) < 21, "kurgu geçersiz"

    res = _submit(monkeypatch, wi, wc)
    assert res["status"] != "shipped", (
        f"teyit ÖLÇÜLEMEZKEN ship edildi (H00029 sınıfı): confirm_p="
        f"{(res.get('gate') or {}).get('confirm_p')} n_valid={(res.get('gate') or {}).get('confirm_n_valid')}")
    g = res["gate"]
    assert g["confirm_durum"] == "olculemedi", g["confirm_durum"]
    assert g["confirm_p"] is None and g["confirm_n_valid"] == 0     # H00029'un tam parmak izi
    neden = res["hypothesis"]["reject_reasons"][0]
    assert "ÖLÇÜLEMEDİ" in neden and "fail-closed" in neden, neden


def test_28f_olculemedi_ile_gecmedi_AYRI_cumledir(seeded, monkeypatch):
    """Üç değerli hükmün OKUNABİLİRLİĞİ. 'Ölçemedim' ile 'ölçtüm ve reddettim' aynı statüyü
    paylaşabilir (defter sözleşmesi `memory.LEGAL_STATUS` bu dosyanın kapsamı dışında) ama AYNI
    CÜMLEYİ paylaşamaz — teşhis belgesinin bütün derdi bu iki kümeyi ayırmaktı."""
    goal = config.goal()
    # (a) ÖLÇÜLDÜ ve REDDETTİ: teyit dilimi dolu ama aday orada kaybediyor (kazananın-laneti)
    inc = wf.trades(120, 1, wf.S_LO, wf.S_END, 0.05) + wf.trades(40, 2, wf.S_END, wf.OOS_END, 0.05)
    cand = [{**t, "r_multiple": round(t["r_multiple"] + (0.6 if t["ts_open"] < wf.S_END else -0.6), 3),
             "pnl_dollars": round(t["pnl_dollars"] + (240.0 if t["ts_open"] < wf.S_END else -240.0), 2)}
            for t in inc]
    res_a = _submit(monkeypatch, wf.wf_from_trades(inc, goal), wf.wf_from_trades(cand, goal))
    assert res_a["status"] == "rejected_by_confirmation"
    assert res_a["gate"]["confirm_durum"] == "gecmedi"
    assert res_a["gate"]["confirm_p"] is not None, "ölçülmüş ret p TAŞIMALI"
    neden_a = res_a["hypothesis"]["reject_reasons"][0]

    # (b) ÖLÇÜLEMEDİ: aynı arama üstünlüğü, teyit dilimi tabanın altında
    inc_b = wf.trades(120, 1, wf.S_LO, wf.S_END, 0.05) + wf.trades(6, 3, wf.S_END, wf.OOS_END, 0.0)
    cand_b = [{**t, "r_multiple": round(t["r_multiple"] + 0.6, 3),
               "pnl_dollars": round(t["pnl_dollars"] + 240.0, 2)} for t in inc_b]
    res_b = _submit(monkeypatch, wf.wf_from_trades(inc_b, goal), wf.wf_from_trades(cand_b, goal))
    neden_b = res_b["hypothesis"]["reject_reasons"][0]

    assert res_b["gate"]["confirm_durum"] == "olculemedi"
    assert neden_a != neden_b, "ölçülmüş ret ile ölçülememe AYNI cümleyi yazıyor"
    assert "ÖLÇÜLEMEDİ" not in neden_a, f"ölçülmüş ret kendini ölçülemedi sanıyor: {neden_a}"
    assert res_a["gate"]["confirm_beyan"] != res_b["gate"]["confirm_beyan"]


def test_28f_DILIMSIZ_fikstur_dunyasinda_davranis_DEGISMEDI(seeded, monkeypatch):
    """SAPMA SINIRI. Dilim YOKSA teyit mekanizması o ortamda hiç YÜRÜRLÜKTE DEĞİLDİR (fikstür/
    sandbox; arama ayağı da orada legacy marj yasasında koşuyor) — olmayan bir sınavdan kalmak diye
    bir şey yok. Fail-closed yalnız 'yasa yürürlükte ama ölçüm yok' hâline biner. Bu ayrım
    olmasaydı düzeltme, ölçüm ortamının tamamını kilitlerdi."""
    inc = {"oos_score": 0.10, "oos_folds": [], "oos_tail_risk": None, "holdout_score": None, "params": {}}
    cand = {"oos_score": 0.30, "oos_folds": [], "oos_tail_risk": None, "holdout_score": None, "params": {}}
    assert not OutOfSamplePipeline.has_slices(inc), "kurgu geçersiz: fikstür dilim taşıyor"
    res = _submit(monkeypatch, inc, cand)
    assert res["status"] == "shipped", res
    assert res["gate"]["confirm_durum"] == "yasa_yururlukte_degil"
    assert res["gate"]["gate_law"] == "legacy_margin"


def test_28f_arama_ayagi_dilim_VARKEN_legacy_marja_DUSMEZ(seeded):
    """İKİNCİ DELİK (aynı sınıf, arama ayağında). `evaluate_search` dilim sınırı çözülemediğinde
    `law="legacy"` döner; eski kod bunu 'dilim yok' hâliyle AYNI dala sokup BİLEŞİK nokta-marj
    yasasına düşüyordu. Ölçüldü: `passes=True, gate_law=legacy_margin, search_p=None, why=''` —
    yani hiçbir olasılıksal kanıt olmadan 'geçti'. Yasa yürürlükteyken ölçememek, başka bir yasaya
    göre geçmek DEĞİLDİR."""
    goal = config.goal()
    inc = wf.trades(120, 1, wf.S_LO, wf.S_END, 0.05) + wf.trades(40, 2, wf.S_END, wf.OOS_END, 0.05)
    cand = wf.trades(120, 11, wf.S_LO, wf.S_END, 0.06) + wf.trades(40, 12, wf.S_END, wf.OOS_END, 0.06)
    wi, wc = wf.wf_from_trades(inc, goal), wf.wf_from_trades(cand, goal)
    # aday BİLEŞİK marj yasasını rahatça geçecek kadar iyi görünsün (0.30 > 0.10 + 0.02)
    wi = {**wi, "oos_score": 0.10, "oos_split": {**wi["oos_split"], "search_end": "BOZUK-SINIR"}}
    wc = {**wc, "oos_score": 0.30, "oos_split": {**wc["oos_split"], "search_end": "BOZUK-SINIR"}}
    assert OutOfSamplePipeline.has_slices(wi) and OutOfSamplePipeline.has_slices(wc), "kurgu geçersiz"

    passes, gate, why = reflect._gate_eval(wi, wc, k_probes=1)
    assert passes is False, (f"dilimler VARKEN ölçülemeyen aday geçti "
                             f"(gate_law={gate['gate_law']}, search_p={gate['search_p']})")
    assert gate["gate_law"] == "olculemedi", gate["gate_law"]
    assert gate["magnitude_durum"] == "olculemedi", gate["magnitude_durum"]
    assert "ÖLÇÜLEMEDİ" in why and "fail-closed" in why, why


def test_28f_olculemedi_kaydi_BILESIK_damgasi_TASIMAZ(seeded):
    """BİRİM YALANI YASAĞI. Ölçülemeyen bir satıra 'eski_bilesik_marj' basmak, o satırda bir ÖLÇEK
    varmış gibi konuşmak olurdu — oysa ölçüm YOK. `probgate.BILESIK_DAMGALAR` bilinmeyen damgayı
    zaten SAYMAZ ve sayaçta adıyla gösterir (meta-kalibrasyonun birim borcu dersi)."""
    goal = config.goal()
    inc = wf.trades(120, 1, wf.S_LO, wf.S_END, 0.05) + wf.trades(40, 2, wf.S_END, wf.OOS_END, 0.05)
    wi = wf.wf_from_trades(inc, goal)
    wi = {**wi, "oos_score": 0.10, "oos_split": {**wi["oos_split"], "search_end": "BOZUK-SINIR"}}
    wc = {**wi, "oos_score": 0.30}
    _p, gate, _w = reflect._gate_eval(wi, wc, k_probes=1)
    assert gate["yasa_surumu"] == "olculemedi", gate["yasa_surumu"]
    assert gate["yasa_surumu"] not in ("para_v3", "eski_bilesik_marj")


def test_28f_ship_yolunda_OLCULEMEDI_dali_shipten_ONCE_gelir(seeded):
    """KOD DÜZENİ ÇİVİSİ. Fail-closed dalı, `versioning.commit` (ship) satırından ÖNCE gelmeli;
    sonra gelirse 'engelledi' cümlesi doğru olmaz. `test_golge_hukum_passes_semantigine_SIZAMAZ`
    ile aynı yöntem: iddia yorumda değil, KAYNAK SIRASINDA."""
    src = _kod(reflect._submit_locked)          # yorumlar ATILIR (bkz. `_kod` beyanı)
    i_olcum = src.index('gate["confirm_durum"] == "olculemedi"')
    i_ship = src.index("versioning.commit(candidate)")
    assert i_olcum < i_ship, "ölçülemedi dalı ship satırından SONRA — engelleme iddiası boş"
    # ...ve eski delik geri gelmesin: `if conf.law == "probabilistic"` TEK BAŞINA teyidi yönetemez
    assert src.index("_teyit_yururlukte") < src.index('if conf.law == "probabilistic":'), \
        "üç değerli hüküm, iki değerli `conf.law` dalından SONRA kuruluyor"
    # ...ve ÖLÇÜLEMEDİ dalı `return` ile çıkmalı: hükmü yazıp akışa devam etmek ship'i engellemez
    kuyruk = src[i_olcum: i_olcum + 900]
    assert 'return {"status": "rejected_by_confirmation"' in kuyruk, \
        "ölçülemedi dalı hükmü yazıyor ama akıştan ÇIKMIYOR — ship yolu açık kalır"


# =================================================================================================
# 28e — p = 0,000 İKİ AYRI GERÇEĞİ SÖYLÜYORDU
# =================================================================================================
def _noop_ve_felaket(goal):
    inc = wf.trades(90, 1, wf.S_LO, wf.S_END, 0.05)
    noop = [dict(t) for t in inc]                                   # bit-bit AYNI
    felaket = [{**t, "r_multiple": round(t["r_multiple"] - 0.5, 3),
                "pnl_dollars": round(t["pnl_dollars"] - 200.0, 2)} for t in inc]
    g = Gate(goal, n_boot=N_BOOT, seed=42)
    return (g.evaluate(inc, noop, wf.S_LO, wf.S_END),
            g.evaluate(inc, felaket, wf.S_LO, wf.S_END))


def test_28e_noop_ile_felaket_ARTIK_ayri_hukum(seeded):
    """Defterin beş `P=0,000`ından DÖRDÜ no-op'tu (H00046/49/50/51 — yapısal olarak atıl düğmeler),
    biri gerçek felaketti (H00031, ort.Δ −0,0921). İkisi de aynı `p` ve aynı `why` alıyordu.
    Artık `ayrim` ikisini AYIRIR — ve 'düğme atıl' bir kalite reddi DEĞİL, kendi başına bir
    hükümdür (§2-25a atıl-düğme ayıklama adayı)."""
    r_noop, r_bad = _noop_ve_felaket(config.goal())
    assert r_noop.p == r_bad.p == 0.0, "kurgu geçersiz: iki taraf aynı p'yi vermiyor"

    assert r_noop.ayrim == AYRIM_AYNI and r_noop.ayrim_n == r_noop.n_valid
    assert r_bad.ayrim == AYRIM_FARKLI and r_bad.ayrim_n == 0
    assert "AYIRT EDİLEMEZ" in r_noop.why, r_noop.why
    assert "AYIRT EDİLEMEZ" not in r_bad.why, (
        f"gerçek kayıp 'ayırt edilemez' diye okunuyor: {r_bad.why}")
    # ...ve gerekçe dizgesi ESKİ tüketicileri kırmadan taşınmalı (sprint/para testleri bu parçayı arar)
    assert "P(ΔS>0)" in r_noop.why and "P(ΔS>0)" in r_bad.why


def test_28e_p_alaninin_ANLAMI_degismedi(seeded):
    """`p` TÜKETİCİSİ OLAN BİR ALAN (pano, arming, defter, meta-kalibrasyon). Ayrım EK alandır;
    `p` hâlâ tam olarak `ort(ΔS > 0)`dır ve `passes` hâlâ yalnız ondan gelir."""
    goal = config.goal()
    r_noop, r_bad = _noop_ve_felaket(goal)
    for r in (r_noop, r_bad):
        assert r.p == 0.0 and r.passes is False
        assert r.p_required == Gate.p_required_for(1)
    # ort.Δ ayrımı ZATEN taşıyordu ama hükme girmiyordu — ikisi tutarlı olmalı
    assert r_noop.mean_delta == 0.0 and r_bad.mean_delta < 0.0

    # gerçek (ve GEÇEN) bir aday "ayrisiyor" demeli — ayrım yalnız no-op'u işaretlemiyor, sınıflıyor
    inc = wf.trades(90, 1, wf.S_LO, wf.S_END, 0.05)
    iyi = [{**t, "r_multiple": round(t["r_multiple"] + 0.5, 3),
            "pnl_dollars": round(t["pnl_dollars"] + 200.0, 2)} for t in inc]
    r_iyi = Gate(goal, n_boot=N_BOOT, seed=42).evaluate(inc, iyi, wf.S_LO, wf.S_END)
    assert r_iyi.passes is True and r_iyi.ayrim == AYRIM_FARKLI and r_iyi.why == ""


def test_28e_ayrim_kapi_kaydina_EK_alan_olarak_girer(seeded):
    """YASA 6 (okuyucusuz yazım yok) tersi de geçerli: hüküm verilen bir ayrım KAYDA girmezse
    hiçbir okuyucu onu göremez. Ayrım hem `GateResult` alanı hem de kapı kaydı alanıdır."""
    goal = config.goal()
    r_noop, _r = _noop_ve_felaket(goal)
    alan = r_noop.as_gate_fields("search")
    assert alan["search_ayrim"] == AYRIM_AYNI and alan["search_ayrim_n"] == r_noop.n_valid
    assert alan["search_p"] == 0.0, "p alanı ayrımdan etkilenmemeli"
    # ...ve tam kapı kaydında da görünmeli (reflect üzerinden, gerçek yol)
    inc = wf.trades(90, 1, wf.S_LO, wf.S_END, 0.05) + wf.trades(40, 2, wf.S_END, wf.OOS_END, 0.05)
    wi = wf.wf_from_trades(inc, goal)
    wc = wf.wf_from_trades([dict(t) for t in inc], goal)
    _p, gate, _w = reflect._gate_eval(wi, wc, k_probes=1)
    assert gate["search_ayrim"] == AYRIM_AYNI, gate.get("search_ayrim")
    import json
    json.dumps(gate, ensure_ascii=False)          # kapı kaydı JSON-güvenli kalmalı (/api 500 dersi)


def test_28e_ayrim_olcutu_ESIK_ICAT_ETMEZ(seeded):
    """EŞİK UYDURMA YASAĞI. Ayrım bir tolerans SEÇMEZ; IEEE-754'ün o büyüklükte temsil edebildiği
    TEK ULP'yi (`np.spacing`) kullanır — yani kodun kendi kayan-nokta gerçeğini. Kaynak-üzerinde
    iddia: gövdede sabit bir tolerans literali OLMAMALI."""
    import re
    kod = _kod(Gate.evaluate)          # docstring + yorumlar ATILIR (bkz. `_kod` beyanı)
    assert "np.spacing(" in kod, "ayrım ölçütü ULP'den türemiyor"
    i = kod.index("n_ayni = int(")
    satir = kod[kod.rindex("\n", 0, i) if "\n" in kod[:i] else 0: kod.index("\n", i)]
    assert not re.search(r"1e-\d+|0\.0{3,}\d", satir), f"ayrım satırında icat edilmiş tolerans: {satir}"

    # ...ve ölçütün BEYANI kayda giriyor (okuyucu tanımı tahmin etmek zorunda kalmasın)
    r_noop, _r = _noop_ve_felaket(config.goal())
    assert "np.spacing" in r_noop.extra["ayrim_olcut"]


def test_28e_ayrim_passes_hukmune_SIZAMAZ(seeded):
    """KOD DÜZENİ ÇİVİSİ (gölge-yasa çivisiyle aynı yöntem): `passes` ayrımdan ÖNCE hesaplanır,
    yani ayrımın hükmü değiştirmesi kod düzeninde imkânsızdır. Ayrım RAPORLAR, karar VERMEZ."""
    src = _kod(Gate.evaluate)          # docstring + yorumlar ATILIR (bkz. `_kod` beyanı)
    i_p = src.index("passes = bool(p >= p_req)")
    assert i_p < src.index("n_ayni = int("), \
        "ayrım `passes` satırından ÖNCE üretiliyor — hükme sızabilir"
    assert "ayrim" not in src[i_p: i_p + 30]
    # ...ve `passes` hiçbir yerde ayrımla yeniden yazılmamalı (tek atama)
    assert src.count("passes = ") == 1, "passes birden fazla yerde atanıyor — ayrım sızabilir"


def test_28e_kismen_ayirt_edilemez_UCUNCU_sinif_olarak_gorunur(seeded):
    """Düğme YALNIZ BAZI bloklarda iş yapıyorsa bu ne saf no-op ne saf ayrışmadır. Üçüncü sınıf
    kaydedilir — yoksa 'kısmen atıl' bir düğme ya no-op ya tam-etkin diye okunurdu.

    KURGU BLOK GEOMETRİSİNDEN TÜRETİLDİ (uydurulmadı): blok boyu = medyan tutuş süresi, `[5,21]`
    güne kıstırılır; değişikliği TEK bloğa sıkıştırırsak, o bloğu HİÇ çekmeyen replikasyonlarda iki
    taraf bit-bit aynı kalır. Beklenen pay ≈ (1 − 1/B)^B → ~%37, yani sınıf gürültüyle değil
    YAPIYLA doğar."""
    goal = config.goal()
    inc = wf.trades(90, 1, wf.S_LO, wf.S_END, 0.05)
    g = Gate(goal, n_boot=N_BOOT, seed=42)
    bd = g.block_days_for(inc)                       # üreticinin KENDİ blok yasası — kopya değil
    lo = wf.S_LO
    hi = (dt.date.fromisoformat(lo) + dt.timedelta(days=bd)).isoformat()
    kismi = [{**t, "r_multiple": round(t["r_multiple"] - 0.8, 3),
              "pnl_dollars": round(t["pnl_dollars"] - 320.0, 2)} if lo <= t["ts_open"] < hi
             else dict(t) for t in inc]
    degisen = sum(1 for a, b in zip(inc, kismi) if a["r_multiple"] != b["r_multiple"])
    assert 0 < degisen < len(inc), f"kurgu geçersiz: {degisen}/{len(inc)} işlem değişti (tek blok bekleniyordu)"

    r = g.evaluate(inc, kismi, wf.S_LO, wf.S_END)
    assert r.ayrim == AYRIM_KISMEN, (f"tek bloğa sıkışmış değişiklik '{r.ayrim}' diye okundu "
                                     f"(ayrim_n={r.ayrim_n}/{r.n_valid})")
    assert 0 < r.ayrim_n < r.n_valid
    assert "KISMEN AYIRT EDİLEMEZ" in r.why, r.why
    # ...ve üç sınıf BİRBİRİNDEN ayrı kalmalı (kısmi, ne no-op ne tam ayrışma)
    assert r.ayrim not in (AYRIM_AYNI, AYRIM_FARKLI)
