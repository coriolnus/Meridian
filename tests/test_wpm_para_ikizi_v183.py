"""v183 — PARA İKİZİ: ÖLÇEK BORCUNUN KAPANMASI (WP-M, 2026-08-03, Rol-1 kararı = Seçenek 1).

TEŞHİS (v182 turu): `probgate.refresh_meta_calibration`ın 2026-07-30'daki "para damgalı çifti ATLA"
çözümü birim karışımını kapattı ama mekanizmayı MUHAFAZAKÂR yapmadı — ÖLDÜRDÜ. para_v3 altında
hiçbir YENİ çift sayılamıyordu: `n_measured` META_MIN_N'e yapısal olarak ulaşamıyor, `extra_p`
sonsuza dek 0 kalıyor, yani sistematik iyimserliği cezalandıran emniyet SESSİZCE kapalı kalıyordu.

BU TURUN ÜÇ CÜMLESİ:

  1. **Gerçekleşmenin PARA ikizi ölçülür; hüküm BİLEŞİK kalır.** `rollback` artık
     `realized_detail.delta_para` yazıyor. Geri-alma kararı, `goal.rollback_if_worse_by` eşiği ve
     `realized_delta`ın kendisi TEK SATIR değişmedi — birimi değiştirmek, eşiği ölçümsüz
     değiştirmek olurdu. Ölçülemeyen üç yol (like-for-like replay · ebeveyn yedekten · min_sample
     altı) None + NEDEN yazar; ölçülemeyen sayı sıfır sayılmaz.

  2. **Damga beyaz-listesi: bilinmeyen damga para VARSAYILMAZ.** Eski ölçüt "damga GÜNCEL yasaya
     eşitse atla"ydı ve yalnız bugünkü etiket için doğruydu: etiket `para_v4` olduğu gün bütün
     `para_v3` satırları sessizce bileşik gerçekleşmeyle bölünmeye başlardı — aynı hata, hiçbir test
     kırılmadan. Ölçüt tersine çevrildi; NEGATİF TEST bu dosyanın çekirdeğidir.

  3. **`extra_p = 0` üç ayrı gerçeği anlatıyordu, artık üçü ayrı yazılıyor.** `olculdu` (ölçtüm,
     düzeltme gerekmedi) · `kurak` (kanıt birikmedi, mekanizma canlı) · `askida_olcek_borcu` (çift
     ÜRETİLİYOR ama eşleştirilemiyor). Bekçi için üçüncüsü sabır değil ARIZAdır ve `starved` kovası
     onu bir ÜRETİM arızası gibi gösteriyordu.
"""
from __future__ import annotations

import datetime as _dt
import pathlib

import pytest
import yaml

from meridian import config, memory, probgate, rollback, store, versioning
from meridian import watchdog as wd

SRC = pathlib.Path(__file__).resolve().parent.parent / "meridian"


@pytest.fixture
def seeded(sandbox_state):
    config.reload_config()
    yield sandbox_state
    config.reload_config()


def _goal(min_sample: int = 5) -> dict:
    return {**config.goal(), "min_sample": min_sample}


def _kur(version: int = 4, parent: int = 3) -> None:
    config.HISTORY.mkdir(parents=True, exist_ok=True)
    (config.HISTORY / f"v{parent:04d}.yaml").write_text(yaml.safe_dump(
        {"version": parent, "parent": None, "params": config.default_strategy()["params"]}))
    (config.STATE / "strategy.yaml").write_text(yaml.safe_dump(
        {"version": version, "parent": parent, "params": config.default_strategy()["params"]}))


def _islemler(n: int, version: int, pnl: float, r: float = 0.1,
              baslangic=_dt.date(2025, 7, 1)) -> list[dict]:
    """Defter satırları — `pnl_dollars` PARA cetvelinin, `r_multiple` bileşik cetvelin girdisi."""
    rows = []
    for i in range(n):
        d = (baslangic + _dt.timedelta(days=i * 7)).isoformat()
        rows.append({"id": f"T{version}{i:03d}", "strategy_version": version,
                     "ts_open": d, "ts_close": d, "r_multiple": r, "pnl_dollars": pnl,
                     "regime": "chop"})
    return rows


def _hipotez(version_to: int = 4, damga: str | None = "para_v3", predicted: float = 0.10) -> None:
    store.append_jsonl("hypotheses.jsonl", {
        "id": "H00001", "version_to": version_to, "status": "live", "variable": "entry.min_score",
        "predicted_delta": predicted, "backtest": ({"confirm_yasa_surumu": damga} if damga else {})})


# =================================================================================================
# 1. PARA İKİZİ — ÖLÇÜLÜR, KAYDA GİRER, HÜKME GİRMEZ
# =================================================================================================
def test_ikiz_olculur_ve_realized_detail_delta_paraya_yazilir(seeded):
    """Uçtan uca: `evaluate_outcomes` pozitif kolunda writeback yaparken ikiz de düşer."""
    _kur()
    g = _goal(5)
    store.write_jsonl("trades.jsonl", _islemler(6, 4, 300.0) + _islemler(6, 3, 100.0))
    _hipotez()
    rollback.evaluate_outcomes(g)

    h = memory.all_hypotheses()[-1]
    det = h["realized_detail"]
    assert det["delta_para"] is not None, det.get("para_ikizi")
    ikiz = det["para_ikizi"]
    assert ikiz["olculdu"] is True and ikiz["neden"] is None
    assert ikiz["hukum_verir"] is False
    # TEK PAYDA: iki taraf da AYNI span ile normalize edildi.
    assert ikiz["span_days"] is not None
    assert ikiz["cur_para"] > ikiz["par_para"], "çocuk daha çok para kazandı, ikiz bunu görmüyor"
    assert det["delta_para"] == pytest.approx(ikiz["cur_para"] - ikiz["par_para"], abs=1e-6)


def test_HUKUM_BILESIK_kalir_ikiz_karara_GIRMEZ(seeded):
    """Turun sınır çizgisi: `realized_delta` bileşik skor farkıdır ve öyle KALIR."""
    _kur()
    g = _goal(5)
    cur, par = _islemler(6, 4, 300.0), _islemler(6, 3, 100.0)
    store.write_jsonl("trades.jsonl", cur + par)
    _hipotez()
    sonuc = rollback.evaluate_outcomes(g)

    from meridian import score as score_mod
    bilesik = round(score_mod.score(cur, g) - score_mod.score(par, g), 4)
    h = memory.all_hypotheses()[-1]
    assert h["realized_delta"] == bilesik, "gerçekleşen delta para ölçeğine kaymış"
    assert sonuc["delta"] == bilesik
    assert h["realized_detail"]["delta_para"] != h["realized_delta"], \
        "iki cetvel aynı sayıya düşmüş — test ayrımı kanıtlayamıyor"


def test_karar_yolu_kaynakta_paraya_DOKUNMAZ():
    """Kaynak çivisi: ikiz yalnız yardımcı bloktadır. Karar/eşik satırlarının bulunduğu bölgede
    `delta_para` GEÇMEZ — geçseydi bir gün eşik sessizce para ölçeğine kayardı."""
    src = (SRC / "rollback.py").read_text()
    yardimci, geri_kalan = src.split("def _overturn_log", 1)
    assert "delta_para" in yardimci, "ikiz yardımcısı yerinde değil"
    assert "delta_para" not in geri_kalan, "karar bölgesinde para alanı geçiyor"
    assert geri_kalan.count("_ikizi_yaz(") == 2, "iki writeback yolunun ikisi de ikizi yazmalı"
    assert 'realized_delta=karar["delta"]' in geri_kalan and "realized_delta=delta," in geri_kalan
    assert geri_kalan.count('float(goal["rollback_if_worse_by"])') == 2, "eşik yolu değişmiş"


# =================================================================================================
# 2. ÖLÇÜLEMEYEN ÜÇ YOL — NONE + NEDEN (UYDURMA YASAĞI)
# =================================================================================================
def test_like_for_like_yolunda_ikiz_OLCULEMEZ_ve_nedeni_yazilir(seeded):
    """Kararın iki tarafı replay'in ürettiği listelerdir; canlı dilimlerden hesaplanan bir para
    farkı KARARIN ikizi olmazdı — başka bir sorunun cevabı olurdu."""
    ikiz = rollback._para_ikizi(_islemler(6, 4, 300.0), _islemler(6, 3, 100.0), _goal(5),
                                {"yontem": "like_for_like_replay_v1"}, False)
    assert ikiz["olculdu"] is False and ikiz["delta_para"] is None
    assert "replay" in ikiz["neden"] and "KARARIN ikizi olmazdı" in ikiz["neden"]


def test_ebeveyn_YEDEKten_geldiginde_ikiz_OLCULEMEZ(seeded):
    """`par_trades` min_sample altındaysa ebeveyn skoru karneden/kapıdan gelir — ebeveynin işlem
    listesi yoktur, para tarafı ölçülemez."""
    ikiz = rollback._para_ikizi(_islemler(6, 4, 300.0), _islemler(1, 3, 100.0), _goal(5),
                                {"yontem": rollback.LEGACY_YONTEM}, True)
    assert ikiz["olculdu"] is False and ikiz["delta_para"] is None
    assert "YEDEK" in ikiz["neden"] and "min_sample" in ikiz["neden"]


def test_money_score_olculemezse_SIFIR_yazilmaz(seeded):
    """min_sample altı bir taraf: bilinmeyen skor, sıfır skor gibi okunamaz (§4)."""
    ikiz = rollback._para_ikizi(_islemler(3, 4, 300.0), _islemler(3, 3, 100.0), _goal(50),
                                {"yontem": rollback.LEGACY_YONTEM}, False)
    assert ikiz["olculdu"] is False and ikiz["delta_para"] is None
    assert "money_score ölçülemedi" in ikiz["neden"]
    assert "sıfır sayılmaz" in ikiz["neden"]


def test_yedek_yolunda_ucdan_uca_ikiz_None_ama_HUKUM_yazilir(seeded):
    """Uçtan uca: ebeveyn ince → karar karne yedeğinden verilir, hipoteze `realized_delta` YİNE
    yazılır (döngü kapanır) ama `delta_para` None + neden'dir."""
    _kur()
    g = _goal(5)
    store.write_jsonl("trades.jsonl", _islemler(6, 4, 300.0) + _islemler(1, 3, 100.0))
    versioning.update_scoreboard(3, live_score=0.10)
    _hipotez()
    rollback.evaluate_outcomes(g)

    h = memory.all_hypotheses()[-1]
    assert h.get("realized_delta") is not None, "öğrenme döngüsü kapanmadı"
    assert h["realized_detail"]["delta_para"] is None
    assert "YEDEK" in h["realized_detail"]["para_ikizi"]["neden"]


# =================================================================================================
# 3. DAMGA BEYAZ-LİSTESİ — NEGATİF TEST (dirilme-hatası sınıfı)
# =================================================================================================
def test_BILINMEYEN_damga_SAYILMAZ_ikizi_OLSA_BILE(seeded):
    """TURUN ÇEKİRDEK NEGATİF TESTİ. Yarının `para_v4`ü bugünün koduna bilinmeyen bir damgadır;
    "herhâlde paradır" diye sayılsaydı, yeni yasanın ilk gününde birim karışımı sessizce geri
    gelirdi. Bilinmeyen damga = ölçülmemiş birim = SAYILMAZ."""
    for i in range(6):
        store.append_jsonl("hypotheses.jsonl", {
            "id": f"X{i}", "predicted_delta": 0.10, "realized_delta": 0.005,
            "realized_detail": {"delta_para": 0.005},     # ikiz VAR ama damga bilinmiyor
            "backtest": {"confirm_yasa_surumu": "para_v4"}})
    out = probgate.refresh_meta_calibration()
    assert out["n_measured"] == 0, "bilinmeyen damgalı satır sayılmış"
    assert out["olcek_karisimi_atlanan"] == 6
    assert out["atlama_dagilimi"]["bilinmeyen_damga"] == 6
    assert out["atlama_dagilimi"]["para_ikizi_yok"] == 0
    assert out["extra_p"] == 0.0 and out["durum"] == probgate.DURUM_ASKIDA


def test_beyaz_liste_ICERIGI_bilesik_olanlarla_SINIRLI():
    """Beyaz liste bir SAYIM değil bir sözleşmedir: yalnız bileşik olduğu BİLİNEN iki damga."""
    assert probgate.BILESIK_DAMGALAR == frozenset({None, "eski_bilesik_marj"})
    from meridian import shadowlaw
    assert shadowlaw.YASA_SURUMU not in probgate.BILESIK_DAMGALAR
    src = (SRC / "probgate.py").read_text()
    assert "_law in BILESIK_DAMGALAR" in src, "ölçüt hâlâ eşitlik karşılaştırması"


def test_bilesik_damgalar_SAYILMAYA_devam_eder(seeded):
    """Mekanizma tarihiyle çalışır: damgasız (geçiş öncesi) ve `eski_bilesik_marj` satırlar
    bileşik ÷ bileşik olarak sayılır."""
    for i in range(3):
        store.append_jsonl("hypotheses.jsonl", {"id": f"A{i}", "predicted_delta": 0.10,
                                               "realized_delta": 0.005, "backtest": {}})
    for i in range(3):
        store.append_jsonl("hypotheses.jsonl", {
            "id": f"B{i}", "predicted_delta": 0.10, "realized_delta": 0.005,
            "backtest": {"confirm_yasa_surumu": "eski_bilesik_marj"}})
    out = probgate.refresh_meta_calibration()
    assert out["n_measured"] == 6 and out["olcek_karisimi_atlanan"] == 0
    assert out["extra_p"] == 0.05, "medyan 0,05 < 0,25 — sıkılaştırma çalışmıyor"


def test_para_damgali_satir_IKIZLE_SAYILIR_mekanizma_dirildi(seeded):
    """DİRİLME KANITI: para damgalı satırlar artık PARA ikiziyle sayılıyor — eskiden bu satırların
    hepsi atlanıyor ve `extra_p` yapısal olarak 0'da donuyordu."""
    from meridian import shadowlaw
    for i in range(5):
        store.append_jsonl("hypotheses.jsonl", {
            "id": f"P{i}", "predicted_delta": 0.10, "realized_delta": 999.0,   # bileşik: OKUNMAMALI
            "realized_detail": {"delta_para": 0.005},
            "backtest": {"confirm_yasa_surumu": shadowlaw.YASA_SURUMU}})
    out = probgate.refresh_meta_calibration()
    assert out["n_measured"] == 5 and out["olcek_karisimi_atlanan"] == 0
    assert out["durum"] == probgate.DURUM_OLCULDU
    # 999/0.10 okunsaydı medyan 9990 olurdu ve extra_p 0 kalırdı; 0.005/0.10 = 0.05 → +0.05.
    assert out["median_ratio"] == 0.05 and out["extra_p"] == 0.05


def test_para_damgali_ama_IKIZSIZ_satir_ATLANIR(seeded):
    """Geçiş öncesi writeback'ler (ikiz yazılmadan önce kapanmış satırlar) bileşik `realized_delta`
    taşır; onu para öngörüsüyle bölmek tam olarak yasaklanan karışımdır."""
    from meridian import shadowlaw
    for i in range(4):
        store.append_jsonl("hypotheses.jsonl", {
            "id": f"Q{i}", "predicted_delta": 0.10, "realized_delta": 0.005,
            "backtest": {"confirm_yasa_surumu": shadowlaw.YASA_SURUMU}})
    out = probgate.refresh_meta_calibration()
    assert out["n_measured"] == 0 and out["olcek_karisimi_atlanan"] == 4
    assert out["atlama_dagilimi"]["para_ikizi_yok"] == 4
    assert out["olcek_borcu"], "ölçüm borcu beyan edilmemiş"


# =================================================================================================
# 4. DURUM ALANI — ÜÇ DEĞER, ÜÇ AYRI CÜMLE
# =================================================================================================
def test_durum_UC_DEGER_ve_extra_p_askida_kurakta_SIFIR(seeded):
    # (a) KURAK: sayılabilir çift var ama eşik altı, atlanan YOK → mekanizma canlı
    store.append_jsonl("hypotheses.jsonl", {"id": "K0", "predicted_delta": 0.10,
                                           "realized_delta": 0.005, "backtest": {}})
    kurak = probgate.refresh_meta_calibration()
    assert kurak["durum"] == probgate.DURUM_KURAK
    assert kurak["n_measured"] == 1 and kurak["extra_p"] == 0.0
    assert "henüz ölçülemedi" in kurak["durum_beyan"]

    # (b) ASKIDA: sayılamayan çift belirdi → kuraklık DEĞİL
    store.append_jsonl("hypotheses.jsonl", {
        "id": "A0", "predicted_delta": 0.10, "realized_delta": 0.005,
        "backtest": {"confirm_yasa_surumu": "para_v3"}})
    askida = probgate.refresh_meta_calibration()
    assert askida["durum"] == probgate.DURUM_ASKIDA
    assert askida["extra_p"] == 0.0, "askıda yer-tutucu ofset yazılmış"
    assert "KURAKLIK DEĞİLDİR" in askida["durum_beyan"]

    # (c) ÖLÇÜLDÜ: eşik doldu
    for i in range(5):
        store.append_jsonl("hypotheses.jsonl", {"id": f"O{i}", "predicted_delta": 0.10,
                                               "realized_delta": 0.005, "backtest": {}})
    olculdu = probgate.refresh_meta_calibration()
    assert olculdu["durum"] == probgate.DURUM_OLCULDU
    assert olculdu["extra_p"] > 0.0 and "ÖLÇÜLDÜ" in olculdu["durum_beyan"]


def test_durum_diske_yazilir(seeded):
    store.append_jsonl("hypotheses.jsonl", {
        "id": "A0", "predicted_delta": 0.10, "realized_delta": 0.005,
        "backtest": {"confirm_yasa_surumu": "para_v3"}})
    probgate.refresh_meta_calibration()
    diskte = store.read_json(probgate.META_FILE, {})
    assert diskte["durum"] == probgate.DURUM_ASKIDA and diskte["durum_beyan"]


# =================================================================================================
# 5. BEKÇİ — ASKIDA ≠ AÇ
# =================================================================================================
def test_bekci_askidayi_STARVED_saymaz(seeded):
    """Askıda bir mekanizma çift ÜRETİYOR ama eşleştiremiyor: bunu 'hiç üretmemiş' diye raporlamak,
    ölçüm borcunu üretim arızası gibi göstermekti — operatör yanlış yerde arardı."""
    store.write_json("gate_calibration.json", {"n_measured": 0, "durum": "askida_olcek_borcu",
                                               "durum_beyan": "ASKIDA — 4 çift sayılamadı"})
    rep = wd.production_report()
    assert "gate_calibration" not in {s["name"] for s in rep["starved"]}
    askida = {s["name"]: s for s in rep["askida"]}
    assert "gate_calibration" in askida
    assert askida["gate_calibration"]["beyan"].startswith("ASKIDA")


def test_bekci_KURAGI_eskisi_gibi_AC_sayar(seeded):
    """Kuraklık gerçekten üretimsizliktir — bu turda o okuma DEĞİŞMEDİ."""
    store.write_json("gate_calibration.json", {"n_measured": 0, "durum": "kurak"})
    rep = wd.production_report()
    assert "gate_calibration" in {s["name"] for s in rep["starved"]}
    assert rep["askida"] == []


def test_bekci_ESKI_SEMA_dosyada_BIREBIR_eski_davranis(seeded):
    """`durum` alanı olmayan (geçiş öncesi) dosyada davranış bit-bit eskisi gibi kalır."""
    store.write_json("gate_calibration.json", {"n_measured": 0})
    rep = wd.production_report()
    assert "gate_calibration" in {s["name"] for s in rep["starved"]} and rep["askida"] == []
    store.write_json("gate_calibration.json", {"n_measured": 3})
    rep2 = wd.production_report()
    assert "gate_calibration" not in {s["name"] for s in rep2["starved"]}
    assert rep2["askida"] == []
