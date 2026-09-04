"""v207 — ANTRENMAN KADANSI DAMGASI + EKSEN-2'nin "0 ÜRETİLDİ"si (2026-08-07).

İKİ BULGU, İKİ AYRI SINIF.

BULGU 1 — PANO YALAN SÖYLÜYORDU (ve v192'nin teşhisi ÖLÇÜMLE ÇÜRÜDÜ).
  Canlı ölçüm (Rol-1, 2026-08-07):
      scheduler_status.last_learn.antrenman = {fitted: True, n_fit: 2217,
                                               brier_train: 0.2428, ts: 2026-08-06T20:13:37}
      shadow_model.json                     = {fit_attempt_ts: None, fit_ts: None, n_fit: 2219}
  Kadans DÜN KOŞTU VE EĞİTTİ; damgası yoktu. Pano (damgayı DOĞRU okuduğu için) kırmızı
  "HİÇ KOŞMADI" basıyordu. v192 bunu "rozet doğru, kadans gerçekten koşmadı" diye kapatmıştı —
  o hüküm bu ölçümle YANLIŞLANDI ve bu dosya yanlışlamayı çiviliyor.

  KÖK NEDEN: `ShadowTradeOutcomeModel.save()` bir ÜSTÜNE-YAZMAYDI. `store.write_json` dosyayı
  tümüyle değiştirir ve `save()` ona sıfırdan kurulmuş bir sözlük veriyordu — dört damganın
  (fit_attempt_ts · fit_ts · fit_fingerprint · fit_skip_reason) hiçbiri o sözlükte yoktu.
      maybe_refit()   → damgaları yazar
      loop.P5_LEARN   → refit_and_save() → save() → DÖRDÜNÜ DE SİLER
  İki n_fit'in farkı (2217 ↔ 2219) doğrudan kanıttır: defteri EN SON yazan taraf kadans değil,
  iki satır daha görmüş olan P5_LEARN koluydu ve o kol damgasızdı.

  İKİNCİL ZARAR: silinen `fit_fingerprint` yüzünden "veri_seti_degismedi" kapısı hiç kapanmıyordu
  — kadans her seans yeniden fit ediyordu. Damga düzelince o kapı da geri açılır.

  DÜZELTME İKİ PARÇALI: (a) `save()` OKU-BİRLEŞTİR-YAZ oldu, (b) damga ÇAĞIRANIN değil FİİLİN
  yanına — `refit_and_save`e — taşındı. (b) olmadan (a) yetmezdi: fit'i atan ikinci yol
  (loop.P5_LEARN) hiçbir zaman damga BASMIYORDU, yalnız silmiyordu.

BULGU 2 — EKSEN-2'nin "0 ÜRETİLDİ"si DOĞRU ama NEDENSİZDİ.
  Canlı teşhis kovaları (last_learn.eksen2.teshis.sayim): gercek_katman_olculmemis 57 ·
  korumali 5 · gercek_katman_olculmemis_cf_dolu 3 · esik_araliginda 1 ·
  ornek_yetersiz_cf_de_yetersiz 1. Yani 67 skillin 60'ı üretimde HİÇ koşmamış, 5'i motor içi,
  hüküm verilebilen 2. Üreteç kanıt olmayan yerde öneri üretmiyor — DOĞRU davranış.
  Kusur üreteçte değil OKUMADA: "0 üretildi · 0 kaydedildi · 0 bekleyen · 0 otomatik uygulandı"
  bir BAŞARISIZLIK gibi okunuyordu. Doğru okuma KANIT YOKLUĞUdur ve ancak kovalar özete
  bağlanınca doğar. Ayrıca `motor_ici_esik_asan` (bugün pullback-screener) bir KARARDIR —
  bayrak BİLEREK yazılmaz — ve panonun hiçbir yerinde görünmüyordu.

UYDURMA YASAĞI HER İKİ BULGUDA DA ÖLÇÜLÜR: kova yoksa ÖLÇÜLEMEDİ (0 değil), motor-içi defteri
okunamazsa None (boş liste değil), fit damgası yoksa tarih künyeden ÇIKARILDIĞI yazılır.
"""
from __future__ import annotations

import json
import pathlib
import shutil
import subprocess

import pytest

from meridian import api, store

SRC = pathlib.Path(__file__).resolve().parents[1]
APPJS = (SRC / "meridian" / "web" / "app.js").read_text()
SM_SRC = (SRC / "meridian" / "shadow_model.py").read_text()
NODE = shutil.which("node")

# Yorumsuz gövde (v154/v160/v171/v194/v196 deseni): bir kuralın GEREKÇESİNİ anlatan yorum, o
# kuralın ihlali sanılmamalı — bu turda zorunlu, çünkü kaldırılan desen yorumda ADIYLA anlatılıyor.
KOD = "\n".join(l for l in APPJS.splitlines() if not l.lstrip().startswith("//"))

# Canlı ölçümün kendisi (Rol-1, 2026-08-07) — fikstür UYDURULMADI, kopyalandı.
CANLI_KOVALAR = {"gercek_katman_olculmemis": 57, "korumali": 5,
                 "gercek_katman_olculmemis_cf_dolu": 3, "esik_araliginda": 1,
                 "ornek_yetersiz_cf_de_yetersiz": 1}
CANLI_TOPLAM = 67
CANLI_OLCULEN = 2


def _seed(n_trade: int = 60):
    """`shadow_model.py::ShadowTradeOutcomeModel._dataset`in GERÇEK katmanını besler (v136'daki tohumun aynısı)."""
    plans, trades = [], []
    for i in range(n_trade):
        pid = f"P-V207-{i:03d}"
        plans.append({"id": pid, "date": f"2026-01-{(i % 28) + 1:02d}", "ticker": f"T{i}",
                      "score": 60 + (i % 30), "r_multiple_expected": 2.0 + (i % 3) * 0.5,
                      "regime_at_plan": "trend_up"})
        trades.append({"plan_id": pid, "regime": "trend_up",
                       "r_multiple": 1.0 if i % 3 else -1.0})
    store.write_jsonl("trade_plans.jsonl", plans)
    store.write_jsonl("trades.jsonl", trades)
    return plans, trades


def _durum() -> dict:
    return store.read_json("shadow_model.json", {}) or {}


# =================================================================================================
# 1 · KÖK NEDEN — `save()` ÜSTÜNE YAZIYORDU
# =================================================================================================
def test_save_KADANS_DAMGASINI_SILMIYOR(sandbox_state):
    """ÇEKİRDEK ÇİVİ. Damgalı bir deftere yapılan `save()`, damgaları KORUMAK zorunda.

    Eski davranış: `write_json`e sıfırdan sözlük → dördü de silinirdi. Canlıdaki "HİÇ KOŞMADI"
    yalanının tamamı bu tek satırdan doğuyordu."""
    from meridian import shadow_model as sm
    _seed()
    store.write_json(sm.STATE_FILE, {"fit_attempt_ts": "2026-08-06T20:13:37+00:00",
                                     "fit_ts": "2026-08-06T20:13:37+00:00",
                                     "fit_fingerprint": {"x": [1, 2]},
                                     "fit_skip_reason": None,
                                     "promotion": {"promoted": False, "n_live": 0}})
    sm.ShadowTradeOutcomeModel().fit().save()
    st = _durum()
    assert st["fit_attempt_ts"] == "2026-08-06T20:13:37+00:00", "deneme damgası SİLİNDİ"
    assert st["fit_ts"] == "2026-08-06T20:13:37+00:00", "fit damgası SİLİNDİ"
    assert st["fit_fingerprint"] == {"x": [1, 2]}, "parmak izi SİLİNDİ — kadansın kısılma kapısı"
    assert st["promotion"]["n_live"] == 0, "terfi kaydı SİLİNDİ"
    # SÖZLEŞME LİSTEDEN OKUNUR: yarın beşinci bir damga eklenirse bu test onu kendiliğinden
    # kapsar. Alan adlarını teste elle kopyalamak, listeyi sessizce ayrıştırmaya davetti.
    assert set(sm._DAMGA_ALANLARI) <= set(st), f"korunmayan damga alanı: {set(sm._DAMGA_ALANLARI) - set(st)}"
    # Model alanları yine TAM yazılır — koruma, kaydı yarım bırakmak değildir.
    assert st["w"] and st["n_fit"] >= sm.MIN_FIT_N


def test_CANLI_SIRA_kadans_sonra_P5LEARN_damgayi_YASATIYOR(sandbox_state):
    """CANLI VAKANIN BİREBİR YENİDEN OYNATIMI (2026-08-06 gecesi).

    Kadans koşar ve damgalar; ardından iki satır daha düşer ve loop.py'deki "P5_LEARN" aşaması doğrudan
    `refit_and_save()` çağırır. Eskiden bu ikinci çağrı damgaları siliyordu ve pano
    "HİÇ KOŞMADI" diyordu — n_fit'in kadanstakinden (2217) büyük olması (2219) o silinmenin
    kanıtıydı. Artık ikinci çağrı damgayı SİLMEZ, İLERLETİR."""
    from meridian import shadow_model as sm
    plans, trades = _seed()
    kadans = sm.maybe_refit()
    assert kadans["fitted"] is True
    assert _durum()["fit_attempt_ts"], "kadans damgayı hiç yazmadı"

    plans.append({"id": "P-V207-YENI", "date": "2026-02-01", "ticker": "ZZ", "score": 88,
                  "r_multiple_expected": 3.0, "regime_at_plan": "trend_up"})
    trades.append({"plan_id": "P-V207-YENI", "regime": "trend_up", "r_multiple": 2.0})
    store.write_jsonl("trade_plans.jsonl", plans)
    store.write_jsonl("trades.jsonl", trades)
    sm.ShadowTradeOutcomeModel.refit_and_save()          # loop.P5_LEARN kolu

    st = _durum()
    assert st["n_fit"] > kadans["n_fit"], "ikinci fit yeni satırı görmedi — vaka yeniden kurulmadı"
    assert st.get("fit_attempt_ts"), "P5_LEARN kolu deneme damgasını SİLDİ (canlı kusurun ta kendisi)"
    assert st.get("fit_ts"), "P5_LEARN kolu fit damgasını SİLDİ"
    assert st.get("fit_fingerprint"), "P5_LEARN kolu parmak izini SİLDİ"


def test_parmak_izi_YASADIGI_icin_kadans_kendini_kisabiliyor(sandbox_state):
    """İKİNCİL ZARARIN KAPANIŞI: silinen parmak izi yüzünden kadans her seans yeniden fit
    ediyordu. P5_LEARN kolu araya girse bile kapı kapanmalı."""
    from meridian import shadow_model as sm
    _seed()
    assert sm.maybe_refit()["fitted"] is True
    sm.ShadowTradeOutcomeModel.refit_and_save()          # araya giren P5_LEARN kolu
    ikinci = sm.maybe_refit()
    assert ikinci["fitted"] is False and ikinci["reason"] == "veri_seti_degismedi"


def test_save_OKU_BIRLESTIR_YAZ_kaynakta(sandbox_state):
    """KAYNAK ÇİVİSİ: `save()` bir daha sıfırdan sözlük yazmasın. Davranış testi bugünü korur,
    bu satır yarınki bir 'sadeleştirme'yi durdurur."""
    i = SM_SRC.index("def save(self)")
    dilim = SM_SRC[i:SM_SRC.index("@classmethod", i)]
    assert "store.read_json(STATE_FILE" in dilim, "`save()` mevcut defteri OKUMUYOR — üstüne yazıyor"
    assert "{**mevcut," in dilim, "`save()` birleştirmiyor"


def test_damga_FIILIN_yaninda_CAGIRANIN_degil():
    """Damga `refit_and_save`te (fit'in kendisi) atılır. Çağırana asmak, üçüncü bir çağıran
    doğduğunda kusuru geri getirir — canlı vaka zaten o sınıfın ikinci nüksüydü."""
    i = SM_SRC.index("def refit_and_save(cls)")
    dilim = SM_SRC[i:SM_SRC.index("def is_promoted", i)]
    assert "_damga_yaz(fit_attempt_ts=" in dilim, "deneme damgası fiilin yanında değil"
    assert '"fit_ts": now' in dilim, "fit damgası fiilin yanında değil"


# =================================================================================================
# 2 · İKİ DAMGA, İKİ AYRI OLGU
# =================================================================================================
def test_fit_EDILEN_dal_HER_IKI_damgayi_birakir(sandbox_state):
    from meridian import shadow_model as sm
    _seed()
    sm.maybe_refit()
    st = sm.training_status()
    assert st["son_deneme_ts"] is not None
    assert st["son_fit_ts"] is not None
    assert st["son_fit_kaynak"] == "damga", "fit tarihi künyeden ÇIKARILDI — damga basılmamış"


def test_fit_EDILMEYEN_dal_da_DENEME_damgasi_birakir(sandbox_state):
    """'veri değişmedi' dalı bir BAŞARISIZLIK değil, kadansın disiplini — ama yine de bir
    DENEMEDİR ve damga bırakmak zorundadır. Yoksa sessiz bir duruş taze görünür."""
    from meridian import shadow_model as sm
    _seed()
    sm.maybe_refit()
    ilk_fit = _durum()["fit_ts"]
    ilk_deneme = _durum()["fit_attempt_ts"]
    store.write_json(sm.STATE_FILE, {**_durum(), "fit_attempt_ts": "2000-01-01T00:00:00+00:00"})
    r = sm.maybe_refit()
    assert r["fitted"] is False and r["reason"] == "veri_seti_degismedi"
    st = _durum()
    assert st["fit_attempt_ts"] != "2000-01-01T00:00:00+00:00", "deneme damgası İLERLEMEDİ"
    assert st["fit_ts"] == ilk_fit, "fit edilmeyen dal FİT damgasını ilerletti — iki olgu birleşti"
    assert st["fit_skip_reason"] == "veri_seti_degismedi"
    assert ilk_deneme is not None


def test_ESIK_ALTI_dal_DENEME_birakir_FIT_birakmaz(sandbox_state):
    """MIN_FIT_N altı: denendi (damga), kurulamadı (fit damgası YOK). İkisini tek alanda
    tutmak, kurulamamış bir modeli 'taze fit' diye okutur."""
    from meridian import shadow_model as sm
    _seed(n_trade=5)
    r = sm.maybe_refit()
    assert r["fitted"] is False and r["reason"] == "esik_alti"
    st = _durum()
    assert st.get("fit_attempt_ts"), "eşik-altı dalı DENEME damgası bırakmadı"
    assert st.get("fit_ts") is None, "kurulamamış fit FİT damgası bıraktı"
    assert "esik_alti" in str(st.get("fit_skip_reason"))
    assert st.get("fit_fingerprint") is None, "kurulamamış fit veri setini 'işlendi' ilan etti"


def test_basarisiz_deneme_ONCEKI_fit_damgasini_KORUR(sandbox_state):
    """AYRILIĞIN ASIL SINAVI: deneme ilerlerken fit YERİNDE kalır. Aynı alan olsalardı, başarısız
    bir deneme 'model az önce fit edildi' derdi."""
    from meridian import shadow_model as sm
    _seed()
    sm.maybe_refit()
    fit_ts = _durum()["fit_ts"]
    deneme_ts = _durum()["fit_attempt_ts"]
    assert fit_ts and deneme_ts
    # Defterleri boşalt → sıradaki fit eşik altında kalır (veri seti DEĞİŞTİ, kapı açık).
    store.write_jsonl("trades.jsonl", [])
    store.write_jsonl("trade_plans.jsonl", [])
    r = sm.maybe_refit()
    assert r["fitted"] is False
    st = _durum()
    assert st["fit_ts"] == fit_ts, "başarısız deneme FİT damgasını ezdi"
    assert st["fit_attempt_ts"] != deneme_ts or st["fit_skip_reason"], "deneme kayda geçmedi"


def test_yarida_kalan_fit_SESSIZ_kalmiyor(sandbox_state, monkeypatch):
    """YASA 4: fit patlarsa defterde 'denendi ama bitmedi' yazar. Deneme damgası fit'ten ÖNCE
    atıldığı için, çöken bir fit hiç denenmemiş gibi okunamaz."""
    from meridian import shadow_model as sm
    _seed()
    monkeypatch.setattr(sm.ShadowTradeOutcomeModel, "fit",
                        lambda self, *a, **k: (_ for _ in ()).throw(RuntimeError("bozuk defter")))
    with pytest.raises(RuntimeError):
        sm.ShadowTradeOutcomeModel.refit_and_save()
    st = _durum()
    assert st.get("fit_attempt_ts"), "çöken fit hiçbir iz bırakmadı"
    assert st.get("fit_skip_reason") == "fit_basladi_bitmedi"
    assert st.get("fit_ts") is None


# =================================================================================================
# 3 · PANO — "HİÇ KOŞMADI" YALNIZ GERÇEKTEN DAMGA YOKKEN
# =================================================================================================
def test_nabiz_HIC_KOSMADI_yalniz_damga_YOKKEN(sandbox_state):
    """Rozetin sözleşmesi: kadans koştuysa kırmızı olamaz. Canlıda damga silindiği için
    kırmızıydı — kusur rozette değil damgadaydı, ama sözleşme rozet üstünden ölçülür."""
    from meridian import analytics, shadow_model as sm
    _seed()
    assert analytics.learning_automation()["nabiz"]["shadow_fit"]["hic_kosmadi"] is True
    sm.maybe_refit()
    nb = analytics.learning_automation()["nabiz"]["shadow_fit"]
    assert nb["hic_kosmadi"] is False, "kadans KOŞTU ama pano hâlâ 'HİÇ KOŞMADI' diyor"
    assert nb["bayat"] is False


def test_P5LEARN_tek_basina_kossa_da_nabiz_KIRMIZI_kalmiyor(sandbox_state):
    """Kadans hiç koşmasa bile fit'i atan taraf damga bırakır — 'fit koştu ama pano hiç
    koşmadı diyor' sınıfı böyle kapanır."""
    from meridian import analytics, shadow_model as sm
    _seed()
    sm.ShadowTradeOutcomeModel.refit_and_save()          # YALNIZ loop.P5_LEARN kolu
    assert analytics.learning_automation()["nabiz"]["shadow_fit"]["hic_kosmadi"] is False


def test_api_SON_DENEME_ve_SON_FIT_ayri_alanlar(sandbox_state):
    ogr = {"antrenman": {"kuruldu": True, "n_fit": 2219, "brier_train": 0.2428,
                         "son_fit_ts": "2026-08-06T20:13:37+00:00", "son_fit_kaynak": "damga",
                         "son_deneme_ts": "2026-08-07T20:10:00+00:00",
                         "son_atlama_nedeni": "veri_seti_degismedi",
                         "terfi": {"promoted": False, "n_live": 0, "promote_min_n": 30}}}
    out = api._ogrenme_blogu(ogr, None)
    assert out["son_fit"]["ts"] == "2026-08-06T20:13:37+00:00"
    assert out["son_deneme"]["ts"] == "2026-08-07T20:10:00+00:00"
    assert out["son_deneme"]["damga_var"] is True
    assert out["son_deneme"]["atlama_nedeni"] == "veri_seti_degismedi"
    # BEYAN GÜNCEL OLMALI: v192 metni "damgayı yalnız maybe_refit yazar" diyordu ve artık YANLIŞ.
    assert "fit_attempt_ts" in out["son_fit"]["beyan"] and "fit_ts" in out["son_fit"]["beyan"]


def test_api_damga_YOKSA_son_deneme_bunu_SOYLUYOR(sandbox_state):
    out = api._ogrenme_blogu({"antrenman": {"son_deneme_ts": None, "terfi": {}}}, None)
    assert out["son_deneme"]["damga_var"] is False and out["son_deneme"]["ts"] is None


def test_api_fit_tarihinin_KAYNAGI_beyan_ediliyor(sandbox_state):
    """`kunye` = fit'in kendi damgası yok, tarih kayıt künyesinden ÇIKARILDI. v207 öncesi
    canlının hâli buydu; ayrımı yazmayan bir tarih, çıkarımı damga gibi gösterir."""
    from meridian import shadow_model as sm
    store.write_json(sm.STATE_FILE, {"w": [0.1] * 7, "mu": [0] * 6, "sd": [1] * 6, "n_fit": 2219,
                                     "_kaynak": {"generated": "2026-08-06T20:13:37+00:00"}})
    st = sm.training_status()
    assert st["son_fit_kaynak"] == "kunye" and st["son_fit_ts"] == "2026-08-06T20:13:37+00:00"
    assert api._ogrenme_blogu({"antrenman": st}, None)["son_fit"]["kaynak"] == "kunye"


# =================================================================================================
# 4 · EKSEN-2 — "0 ÜRETİLDİ" = KANIT YOKLUĞU
# =================================================================================================
def test_eksen2_ozeti_CANLI_KOVALARI_tasiyor():
    oz = api._eksen2_ozeti({"kovalar": CANLI_KOVALAR})
    assert oz["durum"] == "dolu"
    assert oz["toplam_skill"] == CANLI_TOPLAM
    assert oz["olculmemis"] == 60          # 57 + 3 (cf dolu olan da ÖLÇÜLMEMİŞTİR)
    assert oz["korumali"] == 5
    assert oz["olculen"] == CANLI_OLCULEN
    assert oz["oran"] == round(2 / 67, 4)
    assert str(CANLI_TOPLAM) in oz["payda"], "çubuk paydası BEYAN EDİLMEMİŞ"
    assert dict(oz["dokum"]) == CANLI_KOVALAR
    assert "KANIT YOKLUĞU" in oz["neden"]


def test_eksen2_kova_YOKSA_OLCULEMEDI_sifir_DEGIL():
    """UYDURMA YASAĞI: '67 skillin 2'si ölçüldü' ile 'kaç skill olduğunu bilmiyoruz' aynı
    piksele düşemez. Kova yoksa hüküm de yoktur — 'kanıt yok' bile İLAN EDİLEMEZ."""
    for yuk in (None, {}, {"kovalar": None}, {"kovalar": {}}):
        oz = api._eksen2_ozeti(yuk)
        assert oz["durum"] == "ÖLÇÜLEMEDİ"
        assert oz["toplam_skill"] is None and oz["olculen"] is None
        assert oz["oran"] is None and oz["payda"] is None
        assert len(oz["neden"]) >= 20 and "ÖLÇÜLEMEDİ" in oz["neden"]


def test_eksen2_BILINMEYEN_kova_OLCULMUS_sayilir():
    """`axis2_diagnosis`in dal yapısı: `gercek_katman_olculmemis*` dışındaki HER kova
    `avg_r is not None` dalından gelir. Sabit ad listesi tutmak, yarın doğacak bir kovayı
    sessizce yanlış saymak olurdu."""
    oz = api._eksen2_ozeti({"kovalar": {"gercek_katman_olculmemis": 4, "korumali": 1,
                                        "yepyeni_kova_2027": 3}})
    assert oz["toplam_skill"] == 8 and oz["olculmemis"] == 4 and oz["korumali"] == 1
    assert oz["olculen"] == 3


def test_motor_ici_defter_OKUNAMAZSA_None_bos_liste_DEGIL(sandbox_state):
    """'aşan yok' ÖLÇÜLMÜŞ bir sıfırdır; 'defter okunamadı' bir körlüktür."""
    assert api._eksen2_motor_ici() is None
    store.write_json("axis2_status.json", {"otomatik": {"motor_ici_esik_asan": []}})
    assert api._eksen2_motor_ici() == []


def test_motor_ici_ESIK_ASAN_yuke_giriyor(sandbox_state):
    """Canlıda bugün `pullback-screener` bu kolda: eşiği AŞTI ama motor-içi olduğu için bayrak
    BİLEREK yazılmadı. Bu bir KARARDIR ve görünmezse ölçüm hiç olmamış gibi okunur."""
    store.write_json("axis2_status.json", {"otomatik": {"motor_ici_esik_asan": [
        {"skill": "pullback-screener", "n_cf": 21, "cf_avg_r": -1.0, "n": 4, "avg_r": -1.0,
         "zaten_golgede": True, "why": "kanıt eşiği AŞILDI ama skill MOTOR-İÇİ"}]}})
    out = api._ogrenme_blogu({"antrenman": {"terfi": {}},
                              "eksen2": {"kovalar": CANLI_KOVALAR, "uretilen": 0}}, None)
    mi = out["eksen2"]["ozet"]["motor_ici_esik_asan"]
    assert mi and mi[0]["skill"] == "pullback-screener"


def test_ogrenme_blogu_eksen2_ozetini_EKLIYOR_girdiyi_bozmadan(sandbox_state):
    ogr = {"antrenman": {"terfi": {}}, "eksen2": {"kovalar": CANLI_KOVALAR, "uretilen": 0}}
    out = api._ogrenme_blogu(ogr, None)
    assert out["eksen2"]["ozet"]["olculen"] == CANLI_OLCULEN
    assert "ozet" not in ogr["eksen2"], "zenginleştirme girdiyi MUTASYONA uğrattı"


def test_eksen2_yuku_HIC_yoksa_ozet_uretilmiyor(sandbox_state):
    """Kadans hiç koşmamışsa `eksen2` None gelir; uydurma bir özet doğmamalı."""
    out = api._ogrenme_blogu({"antrenman": {"terfi": {}}, "eksen2": None}, None)
    assert out["eksen2"] is None


# =================================================================================================
# 5 · PANO DAVRANIŞI (Node — şablon dilimleri FİİLEN koşturulur)
# =================================================================================================
_HARNESS = """
const esc = s => String(s == null ? "" : s).replace(/[&<>"']/g, c =>
  ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const trn = (x, d = 0) => { const n = Number(x); return (x == null || !Number.isFinite(n)) ? "—"
  : n.toLocaleString("tr-TR", { minimumFractionDigits: d, maximumFractionDigits: d }); };
%(cubuk)s
%(govde)s
%(hucre)s
%(serit)s
%(kova)s
const o = %(o)s;
const ex = o.eksen2;
%(dilim)s
process.stdout.write(JSON.stringify({sonDenemeRow, eksen2Blok}));
"""


def _fn(ad: str) -> str:
    """Fonksiyon dilimi (v198 `_fn` deseninin aynısı)."""
    if f"function {ad}(" in APPJS:
        i = APPJS.index(f"function {ad}(")
        parcalar = []
        for ln in APPJS[i:].splitlines(keepends=True):
            parcalar.append(ln)
            if ln.rstrip("\n") == "}":
                break
        return "".join(parcalar)
    i = APPJS.index(f"const {ad} = ")
    return APPJS[i:APPJS.index("\n", i) + 1]


def _kova_sozlugu() -> str:
    i = APPJS.index("const KOVA_TR = {")
    return APPJS[i:APPJS.index("\n};", i) + 3]


def _ogrenme_dilimi() -> str:
    """`sonDenemeRow` + `eksen2Blok` — bitişik ve kendi kendine yeterli."""
    bas = APPJS.index("    const sonDenemeRow = (() => {")
    son = APPJS.index('    return `<div class="card rise"><h2 class="t">Öğrenme beslemesi', bas)
    return APPJS[bas:son]


def _ciz(o: dict) -> dict:
    if NODE is None:
        pytest.skip("node yok")
    betik = _HARNESS % {"cubuk": _fn("hucreCubuk"), "govde": _fn("hucreGovde"),
                        "hucre": _fn("ozetHucre"), "serit": _fn("ozetSerit"),
                        "kova": _kova_sozlugu(), "o": json.dumps(o, ensure_ascii=False),
                        "dilim": _ogrenme_dilimi()}
    p = subprocess.run([NODE, "-e", betik], capture_output=True, text=True, timeout=60)
    assert p.returncode == 0, f"öğrenme dilimi Node'da patladı:\n{p.stderr}"
    return json.loads(p.stdout)


_DOLU = {
    "son_deneme": {"ts": "2026-08-07T20:10:00+00:00", "atlama_nedeni": "veri_seti_degismedi",
                   "damga_var": True},
    "eksen2": {"uretilen": 0, "kaydedilen": 0, "bekleyen_toplam": 0, "otomatik_uygulanan": 0,
               "kovalar": CANLI_KOVALAR,
               "ozet": {"durum": "dolu", "toplam_skill": 67, "olculen": 2, "olculmemis": 60,
                        "korumali": 5, "oran": 0.0299,
                        "payda": "katalogda beyan edilen skill sayısı (67)",
                        "neden": "67 skillin 60'ı gerçek katmanda HİÇ ölçülmemiş, 5'i motor-içi "
                                 "(aday değil); hüküm verilebilir olan 2. Üreteç kanıt olmayan "
                                 "yerde öneri ÜRETMEZ — '0 üretildi' bir arıza değil, KANIT "
                                 "YOKLUĞUdur.",
                        "motor_ici_esik_asan": [
                            {"skill": "pullback-screener", "n_cf": 21, "cf_avg_r": -1.0,
                             "n": 4, "avg_r": -1.0}]}},
}
_BOS = {
    "son_deneme": {"ts": None, "atlama_nedeni": None, "damga_var": False},
    "eksen2": {"uretilen": 0, "kaydedilen": 0, "bekleyen_toplam": 0, "otomatik_uygulanan": 0,
               "kovalar": {},
               "ozet": {"durum": "ÖLÇÜLEMEDİ", "toplam_skill": None, "olculen": None,
                        "olculmemis": None, "korumali": None, "oran": None, "payda": None,
                        "neden": "Eksen-2 teşhis kovaları yükte YOK — üretecin sessizliği "
                                 "ÖLÇÜLEMEDİ. Bu bir 'kanıt yok' hükmü değildir.",
                        "motor_ici_esik_asan": None}},
}


@pytest.fixture(scope="module")
def dolu():
    return _ciz(_DOLU)


@pytest.fixture(scope="module")
def bos():
    return _ciz(_BOS)


def test_pano_damga_VARKEN_HIC_KOSMADI_demiyor(dolu):
    assert "damga YOK" not in dolu["sonDenemeRow"]
    assert "2026-08-07 20:10" in dolu["sonDenemeRow"]
    assert "veri_seti_degismedi" in dolu["sonDenemeRow"]


def test_pano_damga_YOKKEN_bunu_ADIYLA_soyluyor(bos):
    assert "damga YOK" in bos["sonDenemeRow"] and "hiç denenmedi" in bos["sonDenemeRow"]


def test_eksen2_ozeti_BUYUK_DEGER_ve_PAYDA_BEYANLI_cubuk(dolu):
    """Kart sözleşmesi D2-a: büyük değer (`.pm-yield`) + payda-beyanlı çubuk (`.pm-conf`) + meta."""
    h = dolu["eksen2Blok"]
    assert 'class="pm-yield' in h and "2 / 67" in h
    assert 'class="pm-conf"' in h and 'data-payda="katalogda beyan edilen skill sayısı (67)"' in h
    assert 'class="pm-n"' in h and "60" in h and "hiç ölçülmemiş" in h


def test_serit_DORT_HUCRE_izgara_butcesi(dolu):
    """`.ozet-serit` 4 sütunluk sabit bir ızgaradır (index.html). Eksik hücre, ızgaranın
    zeminini boş sütun olarak ekrana basar — şeridin bütçesi bir tercih değil, CSS kuralı."""
    assert dolu["eksen2Blok"].count('class="pm-cell"') == 4


def test_uretimin_PAYDASI_katalog_DEGIL_hukum_verilebilen(dolu):
    """ÇEKİRDEK ÇİVİ: "0/67" üretecin 67 skilde başarısız olduğunu söylerdi. 65'inde ölçüm YOK —
    hüküm bile kurulamaz. Üretimin paydası hüküm verilebilen skill sayısıdır."""
    h = dolu["eksen2Blok"]
    assert 'data-payda="hüküm verilebilen skill (2)"' in h
    assert 'data-payda="hüküm verilebilen skill (67)"' not in h


def test_eksen2_KANIT_YOKLUGU_diye_okunuyor(dolu):
    h = dolu["eksen2Blok"]
    assert "Üretilen öneri" in h, "üretim sayısı kayboldu — şerit o dört sayının KENDİSİDİR"
    assert "kaydedildi" in h and "otomatik uygulandı" in h
    assert "KANIT YOKLUĞU" in h, "dört sıfır hâlâ nedensiz — başarısızlık gibi okunur"


def test_eksen2_kova_yoksa_ROZET_OLCULEMEDI_ve_KANIT_TABANI_cubuksuz(bos):
    h = bos["eksen2Blok"]
    assert 'class="pm-none"' in h, "ölçülemeyen hâl uydurma bir sayı bastı"
    assert "ÖLÇÜLEMEDİ" in h
    # Kanıt tabanının paydası ölçülemedi → o hücrenin çubuğu doğmaz; üretim hücresinin de
    # (payda hüküm verilebilen skill sayısıdır ve o da ölçülemedi).
    assert 'class="pm-conf"' not in h, "paydasız/oransız hâlde çubuk çizildi"


def test_motor_ici_karari_EKRANDA(dolu):
    h = dolu["eksen2Blok"]
    assert "Motor-içi eşiği aşan" in h and "pullback-screener" in h
    assert "bayrak BİLEREK yazılmadı" in h
    assert "knob/kapı" in h, "kararın gerekçesi yazılmamış — ihmal gibi okunur"


def test_motor_ici_OLCULEMEDI_ile_SIFIR_ayri(bos):
    assert "ÖLÇÜLEMEDİ (0 DEĞİL)" in bos["eksen2Blok"]
    sifir = _ciz({**_BOS, "eksen2": {**_BOS["eksen2"],
                                     "ozet": {**_BOS["eksen2"]["ozet"], "motor_ici_esik_asan": []}}})
    assert "ölçüldü, sıfır çıktı" in sifir["eksen2Blok"]
    assert 'class="pm-none"' in bos["eksen2Blok"]


def test_renk_yalniz_ANOMALIDE(dolu):
    """Kanıt yokluğu bir SAPMA değildir — şeridin hiçbir hücresi şiddet rengi taşımaz."""
    h = dolu["eksen2Blok"]
    assert "pm-yield mono-num warn" not in h and "pm-yield mono-num neg" not in h


# =================================================================================================
# 6 · SÖZDİZİMİ
# =================================================================================================
def test_node_check_gecer():
    if NODE is None:
        pytest.skip("node yok")
    p = subprocess.run([NODE, "--check", str(SRC / "meridian" / "web" / "app.js")],
                       capture_output=True, text=True, timeout=60)
    assert p.returncode == 0, p.stderr


def test_ikinci_kk_ozet_DOGMADI():
    """v198 sözleşmesi: `.kk-ozet` YALNIZ `kartOzeti`den doğar. Bu tur `ozetHucre` kullanır —
    kapak dilini ikinci bir yerde üretmez."""
    assert KOD.count('<span class="kk-ozet"') == 1
