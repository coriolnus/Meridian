"""test_golge_fit_gorunurlugu_v192.py — "ANTRENMAN HİÇ KOŞMAMIŞ" YANILSAMASI (2026-08-06).

OPERATÖR ŞİKÂYETİ: pano "antrenman hiç koşmamış" gösteriyor — oysa canlı defterde gölge model fit'i
KOŞUYOR (2026-08-05T22:10, n=2217, brier_train 0,2428, live_brier null, promoted false).

TEŞHİS (kod okumasıyla, ölçülmüş): ortada YALAN YOK, BİTİŞİKLİK KAZASI var. Kırmızı rozet
`ogrenme.nabiz.shadow_fit`ten gelir; o nabız `shadow_model.json:fit_attempt_ts`i ölçer ve o damgayı
YALNIZ `shadow_model.maybe_refit()` — yani zamanlayıcının seans-sonrası KADANSI — yazar. Canlıda
fit'i atan taraf ise `refit_and_save()`tir (loop'un P5_LEARN kolu) ve deneme damgasına HİÇ dokunmaz.
Yani rozet DOĞRU (kadans gerçekten koşmadı) ama yanındaki model TAZE, ve kart bunu hiçbir yerde
yazmıyordu. İki gerçek tek cümleye sıkışınca operatör "öğrenme ölmüş" okuyor.

BU TUR ÜÇÜNCÜ BİR GERÇEK ÜRETMEZ. `training_status()` `son_fit_ts` / `n_fit` / `brier_train`
alanlarını ZATEN taşıyordu ve okuyucusu yoktu (YASA 6 borcu). Eklenen tek yeni şey terfi hükmünün
NEDENİdir; o da uydurulmaz — eleme defterinden (`sieve`, "shadow_model.terfi" aşama dizgesi) okunur.

HÜKÜM ÜÇ DEĞERLİDİR: EVET / HAYIR / ÖLÇÜLEMEDİ. "Hayır" modelin tabanı yenemediğidir (bilgi),
"ölçülemedi" kıyas verisinin hiç birikmediğidir (kuraklık) — operatörün eylemi ikisinde farklıdır.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from meridian import api

SRC = Path(__file__).resolve().parent.parent
APPJS = (SRC / "meridian" / "web" / "app.js").read_text()
KOD = "\n".join(l for l in APPJS.splitlines() if not l.lstrip().startswith("//"))

MIN_N = 30          # ShadowTradeOutcomeModel.PROMOTE_MIN_N


def _terfi(**kw) -> dict:
    d = {"promoted": False, "n_live": 0, "live_brier": None, "baseline_brier": None,
         "promote_min_n": MIN_N}
    d.update(kw)
    return d


def _sieve(**stage) -> dict:
    return {"stages": {"shadow_model.terfi": stage}} if stage else {"stages": {}}


# =================================================================================================
# TERFİ HÜKMÜ — üç değerli, gerekçeli
# =================================================================================================
def test_kuraklik_HAYIR_degil_OLCULEMEDI(sandbox_state):
    """CANLI HÂL: live_brier null + n_live 0. "Terfi: HAYIR" demek modeli haksız yere suçlardı."""
    h = api._terfi_hukmu(_terfi(), _sieve(**{"in": 95, "out": 0,
                                             "drops": {"piyasa:gölge_tahmini_damgalanmamış": 95}}))
    assert h["karar"] == "ÖLÇÜLEMEDİ" and h["sinif"] == "ornek_kurakligi"
    assert "live_brier" in h["neden"] and "birikmedi" in h["neden"]
    # NEDEN ÖLÇÜMDEN GELİR: eleme defterinin sayıları gerekçeye girer (uydurma cümle değil).
    assert "95 işlem girdi, 0 çift çıktı" in h["neden"]
    assert "piyasa:gölge_tahmini_damgalanmamış" in h["neden"]


def test_esik_dolmadi_HAYIR_ve_sayiyi_yazar(sandbox_state):
    h = api._terfi_hukmu(_terfi(n_live=7, live_brier=0.21, baseline_brier=0.24), _sieve())
    assert h["karar"] == "HAYIR" and h["sinif"] == "esik_dolmadi"
    assert f"7/{MIN_N}" in h["neden"]


def test_tabani_yenemedi_HAYIR(sandbox_state):
    h = api._terfi_hukmu(_terfi(n_live=MIN_N, live_brier=0.26, baseline_brier=0.24), _sieve())
    assert h["karar"] == "HAYIR" and h["sinif"] == "tabani_yenemedi"
    assert "0.26" in h["neden"] and "0.24" in h["neden"]


def test_terfi_etti_EVET(sandbox_state):
    h = api._terfi_hukmu(_terfi(promoted=True, n_live=MIN_N, live_brier=0.19,
                                baseline_brier=0.24), _sieve())
    assert h["karar"] == "EVET" and h["sinif"] == "terfi_etti"


def test_taban_olculemediyse_HAYIR_denmez(sandbox_state):
    """Kıyas yoksa hüküm de yok — 'model yenemedi' demek ölçülmemiş bir iddia olurdu."""
    h = api._terfi_hukmu(_terfi(n_live=MIN_N, live_brier=0.2, baseline_brier=None), _sieve())
    assert h["karar"] == "ÖLÇÜLEMEDİ" and h["sinif"] == "taban_olculemedi"


def test_terfi_demeti_YOKSA_bile_hukum_uretir(sandbox_state):
    h = api._terfi_hukmu(None, None)
    assert h["karar"] == "ÖLÇÜLEMEDİ"                    # None → sessiz "HAYIR"a düşmez


# =================================================================================================
# ÖĞRENME BLOĞU ZENGİNLEŞTİRMESİ
# =================================================================================================
def test_son_fit_kadanstan_BAGIMSIZ_gorunur(sandbox_state):
    """ÇEKİRDEK ÇİVİ: kadans hiç koşmamışken (`hic_kosmadi`) bile fiilî fit tarihiyle görünür."""
    ogr = {"nabiz": {"shadow_fit": {"hic_kosmadi": True, "gecen_saat": None}},
           "antrenman": {"kuruldu": True, "n_fit": 2217, "n_real": 95, "n_cf": 2122,
                         "brier_train": 0.2428, "son_fit_ts": "2026-08-05T22:10:03+00:00",
                         "son_deneme_ts": None, "terfi": _terfi()}}
    out = api._ogrenme_blogu(ogr, _sieve(**{"in": 95, "out": 0, "drops": {"piyasa:x": 95}}))
    sf = out["son_fit"]
    assert sf["ts"] == "2026-08-05T22:10:03+00:00"
    assert sf["n"] == 2217 and sf["brier_train"] == 0.2428
    assert sf["terfi"]["karar"] == "ÖLÇÜLEMEDİ"
    # Kadans nabzı DOKUNULMADAN korunur: o borç ayrı bir turun (scheduler kancası) işidir.
    assert out["nabiz"]["shadow_fit"]["hic_kosmadi"] is True
    # BEYAN KARTTA: iki mekanizmanın ayrı olduğu yazılı olmalı, yoksa yanılsama geri gelir.
    assert "maybe_refit" in sf["beyan"] and "refit_and_save" in sf["beyan"]


def test_model_hic_kurulmadiysa_UYDURMA_tarih_yok(sandbox_state):
    out = api._ogrenme_blogu({"antrenman": {"kuruldu": False, "n_fit": None, "son_fit_ts": None,
                                            "brier_train": None, "terfi": _terfi()}}, None)
    sf = out["son_fit"]
    assert sf["ts"] is None and sf["n"] is None and sf["brier_train"] is None


def test_zenginlestirme_girdiyi_MUTASYONA_ugratmaz(sandbox_state):
    ogr = {"antrenman": {"terfi": _terfi()}}
    api._ogrenme_blogu(ogr, None)
    assert "son_fit" not in ogr


# =================================================================================================
# UÇ + PANO PARİTESİ (YASA 6: yazan alanın okuyucusu olacak)
# =================================================================================================
def test_diagnostics_ucu_son_fit_tasir(sandbox_state, monkeypatch):
    from fastapi.testclient import TestClient
    from meridian import store
    store.write_json("shadow_model.json",
                     {"w": [0.1, 0.2], "mu": [0, 0], "sd": [1, 1], "n_fit": 2217,
                      "brier_train": 0.2428,
                      "_kaynak": {"generated": "2026-08-05T22:10:03+00:00", "n_real": 95,
                                  "n_cf": 2122},
                      "promotion": {"n_live": 0, "live_brier": None, "baseline_brier": None,
                                    "promoted": False}})
    api._DIAG_CACHE.clear()
    with TestClient(api.app) as c:
        d = c.get("/api/diagnostics").json()
    sf = (d.get("ogrenme") or {}).get("son_fit")
    assert sf is not None, "uç `son_fit` taşımıyor — pano satırının kaynağı yok"
    assert sf["n"] == 2217 and sf["ts"] == "2026-08-05T22:10:03+00:00"
    assert sf["terfi"]["karar"] == "ÖLÇÜLEMEDİ"


def test_pano_son_fiti_OKUR(sandbox_state):
    assert "o.son_fit" in KOD, "app.js `son_fit`i okumuyor — API alanı okuyucusuz (YASA 6)"
    assert "Son fit" in KOD
    assert "ÖLÇÜLEMEDİ" in KOD, "üç değerli hüküm panoda iki değere sıkıştırılmış"
    assert "Terfi gerekçesi" in KOD, "hüküm var ama NEDENİ panoda yok"


def test_kadans_etiketi_fit_ile_KARISTIRILMAZ(sandbox_state):
    """Eski etiket ('antrenman (gölge model fit)') kadansı fit sanmaya davet ediyordu — kusurun
    görünen yüzü tam buydu. Etiket kadansı ADIYLA anmalı."""
    assert "antrenman (gölge model fit)" not in KOD
    assert "antrenman KADANSI" in KOD


def test_sieve_tek_okuma_ani(sandbox_state):
    """Aynı yanıtta iki `sieve.report()` çağrısı iki farklı 'kaç çift çıktı' cevabı üretebilirdi
    (bekçi raporunun v151 dersiyle bire bir aynı sınıf)."""
    apipy = (SRC / "meridian" / "api.py").read_text()
    gövde = apipy[apipy.index("def api_diagnostics"):]
    gövde = gövde[:gövde.index("\n@app.")]
    assert gövde.count('"meridian.sieve"') == 1                # eleme defteri TEK kez okunur
    assert gövde.count("_sieve_rep") >= 3                      # hesap + iki tüketici


@pytest.mark.parametrize("alan", ["ts", "n", "brier_train", "terfi", "beyan"])
def test_son_fit_semasi_sabit(sandbox_state, alan):
    out = api._ogrenme_blogu({"antrenman": {"terfi": _terfi()}}, None)
    assert alan in out["son_fit"]
