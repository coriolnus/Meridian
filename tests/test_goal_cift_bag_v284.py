"""test_goal_cift_bag_v284.py — ÇİFT-BAĞ ÇİVİSİ: `max_open_positions` ⟷ `position_size_r`.

NEDEN BU DOSYA VAR (operatör tasarım kapanışı, 2026-08-24 — kalem 20c "yönetişim asimetrisi")
  `max_open_positions` (slot) `guard.LIMIT_KEYS`tedir: Hermes ÖNEREMEZ, `state/bounds.yaml`da
  satırı YOKTUR, değiştiren yalnız operatördür. `position_size_r` ise bir ARAMA DEĞİŞKENİDİR
  (bounds.yaml'da satırı vardır). Ama İKİSİ BİRLİKTE pozisyon riskini belirler — birini tek başına
  oynatmak, öteki üzerinden SESSİZ bir kaldıraç değişikliğidir. Ölçülen olgu bir ÇİFTTİR:
  `EDG-2026-026` (kart research/cards/EDG-2026-026-slot20-boyut05.yaml) slot20 + 0,5R kolunu
  BİRLİKTE ölçtü; tek başına hiçbir uç ölçülmedi.

HÜKÜM (BAĞLAYICI — bu tur yeniden açılmadı)
  * `position_size_r` `LIMIT_KEYS`e ALINMAZ (arama uzayı kapatılmaz),
  * `state/bounds.yaml` satırına DOKUNULMAZ,
  * bunun yerine goal'a MAKİNE-OKUNUR bir çift-bağ kaydı iner (`limits.cift_bag_slot_boyut`) ve
    kapı çiftten YALNIZ BİRİ ölçülen değerinden ayrıldığında `REVIEW`a düşer.
  * `NO_GO` YOK: bu bir YASAK değil, bir İNSAN KAPISIDIR (L0'da REVIEW yine işlem yapar; hükmün
    işi görünürlük ve onay yüzeyi, işlemi kesmek değil).

ÜÇ ÇİVİ (brief'in şartı)
  (a) yalnız slot değişince   → REVIEW
  (b) yalnız boyut değişince  → REVIEW
  (c) ikisi BİRLİKTE değişince → REVIEW DEĞİL (normal yol işler — çift öneri meşrudur)

YASA 6 ÇİVİSİ: goal.yaml'a inen alanın OKUYUCUSU vardır (`guard.classify_gate` →
`guard.cift_bag_hukmu`) ve kaydın kendisi repo goal.yaml'ında GERÇEKTEN durur — okuyucusuz yazım
da, yazımsız okuyucu da burada kırmızı yanar.

Fikstürler SENTETİKTİR (sınır değerleri seçilebilir olsun diye); yalnız "kayıt gerçekten indi mi"
ve "davranış canlı yapılandırmada değişmedi mi" soruları repo dosyalarını OKUR (salt okuma).
"""
from __future__ import annotations

import pathlib

import pytest
import yaml

from meridian import guard

REPO = pathlib.Path(__file__).resolve().parent.parent
GOAL_YAML = REPO / "state" / "goal.yaml"
BOUNDS_YAML = REPO / "state" / "bounds.yaml"

# Ölçülen çift (EDG-2026-026) — bu iki sayı testin ÇAPASIDIR, kayıttan okunmaz: kayıt yanlış
# yazılırsa test onu doğrulamak yerine ONAYLARDI.
OLCULEN_SLOT = 20
OLCULEN_BOYUT = 0.5
KART = "EDG-2026-026"

CIFT_BAG_KAYDI = {"kart": KART, "max_open_positions": OLCULEN_SLOT,
                  "position_size_r": OLCULEN_BOYUT}

LIMITS = {"autonomy_level": 0, "max_position_r": 1.0, "max_open_positions": OLCULEN_SLOT,
          "max_daily_loss_pct": 3.0, "max_sector_exposure_pct": 40.0,
          "heat_hard_r": 5.0, "heat_review_r": 3.5, "corr_review": 0.85,
          "cift_bag_slot_boyut": dict(CIFT_BAG_KAYDI)}

PLAN = {"ticker": "AAA", "sector": "tech", "size_r": 0.5, "r_multiple_expected": 3.0, "score": 90}
PORT = {"open_positions": 0, "sector_counts": {}, "day_pnl_pct": 0.0,
        "open_risk_r": 1.0, "max_corr": 0.1}
REG = {"exposure_budget_pct": 60, "leading_sectors": ["tech"]}
PARAMS = {"entry.min_score": 60, "position_size_r": OLCULEN_BOYUT}

KONTROL_ADI = "cift_bag_slot_boyut"


def _kapi(*, slot=OLCULEN_SLOT, boyut=OLCULEN_BOYUT, kayit=CIFT_BAG_KAYDI, params_ek=None):
    """(hüküm, nedenler, {kontrol_adı: karar_ağacı_satırı}) — saf çağrı, disk/ağ/state yok."""
    limits = {**LIMITS, "max_open_positions": slot}
    if kayit is None:
        limits.pop("cift_bag_slot_boyut", None)
    else:
        limits["cift_bag_slot_boyut"] = dict(kayit)
    params = {**PARAMS, "position_size_r": boyut}
    if boyut is None:
        params.pop("position_size_r", None)
    params.update(params_ek or {})
    detay: list = []
    hukum, nedenler = guard.classify_gate(PLAN, PORT, REG, {"limits": limits}, params,
                                          detail_out=detay)
    return hukum, list(nedenler), {d["check"]: d for d in detay}


# ================================================================================================
# ÇAPA — fikstür gerçekten temiz mi? (bu düşerse aşağıdaki her çivinin anlamı kayar)
# ================================================================================================
def test_capa_olculen_ciftte_kapi_TEMIZ_GO_verir():
    hukum, nedenler, satirlar = _kapi()
    assert (hukum, nedenler) == ("GO", []), f"fikstür kirli: {nedenler}"
    assert satirlar[KONTROL_ADI]["passed"] is True
    assert satirlar[KONTROL_ADI]["note"] is None, "geçen kontrol not YAZMAZ"
    assert satirlar[KONTROL_ADI]["severity"] == "soft"


# ================================================================================================
# ÜÇ ÇİVİ
# ================================================================================================
def test_a_YALNIZ_slot_degisince_REVIEWa_duser_ve_nedeni_ADIYLA_yazar():
    hukum, nedenler, satirlar = _kapi(slot=15)
    assert hukum == "REVIEW", f"tek-bacaklı slot değişikliği kapıdan sessizce geçti: {nedenler}"
    cift = [n for n in nedenler if "çift-bağ KIRILDI" in n]
    assert cift, f"neden ADIYLA yazılmadı: {nedenler}"
    # OYNAYAN uç adıyla anılmalı; DURAN uç da metinde olmalı (okuyan hangi çifti arayacağını bilsin)
    assert "`max_open_positions` TEK BAŞINA" in cift[0], cift[0]
    assert "position_size_r" in cift[0] and KART in cift[0], cift[0]
    assert satirlar[KONTROL_ADI]["passed"] is False
    assert satirlar[KONTROL_ADI]["severity"] == "soft", "NO_GO sınıfına kaydı — hüküm bunu reddetti"


def test_b_YALNIZ_boyut_degisince_REVIEWa_duser_ve_nedeni_ADIYLA_yazar():
    hukum, nedenler, satirlar = _kapi(boyut=0.4)
    assert hukum == "REVIEW", f"tek-bacaklı boyut değişikliği kapıdan sessizce geçti: {nedenler}"
    cift = [n for n in nedenler if "çift-bağ KIRILDI" in n]
    assert cift, f"neden ADIYLA yazılmadı: {nedenler}"
    assert "`position_size_r` TEK BAŞINA" in cift[0], cift[0]
    assert "max_open_positions" in cift[0] and KART in cift[0], cift[0]
    assert satirlar[KONTROL_ADI]["passed"] is False
    assert satirlar[KONTROL_ADI]["severity"] == "soft"


@pytest.mark.parametrize("slot,boyut", [(15, 0.65), (25, 0.4), (10, 1.0)])
def test_c_IKISI_BIRLIKTE_degisince_REVIEW_DEGIL_normal_yol_isler(slot, boyut):
    """Çift öneri MEŞRUDUR — çivi yasak değil, tek-bacaklılığa karşı bir insan kapısıdır."""
    hukum, nedenler, satirlar = _kapi(slot=slot, boyut=boyut)
    assert satirlar[KONTROL_ADI]["passed"] is True, f"çift öneri bayrak yedi: {nedenler}"
    assert not [n for n in nedenler if "çift-bağ" in n], nedenler
    assert hukum == "GO", f"çift öneri normal yolu tıkadı: {nedenler}"


# ================================================================================================
# HÜKMÜN SINIRLARI — NO_GO YOK, ÖLÇÜLEMEDİ HÜKÜM DEĞİL, KAYIT YOKSA DAVRANIŞ AYNI
# ================================================================================================
def test_cift_bag_ASLA_NO_GO_uretmez():
    """Tek-bacaklı değişiklik bir YASAK değil bir İNSAN KAPISIDIR: sert listeye asla girmez."""
    for slot, boyut in ((15, OLCULEN_BOYUT), (OLCULEN_SLOT, 0.4)):
        hukum, nedenler, _ = _kapi(slot=slot, boyut=boyut)
        assert hukum != "NO_GO", f"çift-bağ sert vetoya dönüştü ({slot}/{boyut}): {nedenler}"


def test_kayit_YOKSA_hukum_ve_karar_agaci_DEGISMEZ():
    """Geriye uyum + fail-safe: kaydı taşımayan bir goal sözlüğü (eski kopya, sentetik fikstür)
    bugünkü davranışı BİREBİR korur — satır bile açılmaz."""
    hukum, nedenler, satirlar = _kapi(slot=15, kayit=None)
    assert (hukum, nedenler) == ("GO", [])
    assert KONTROL_ADI not in satirlar


def test_params_None_iken_karar_agaci_12li_sozlesmesi_AYNEN_durur():
    """`test_mutborc_guard_classify_gate_v148` + `test_sektor_tavani_ayristirma_v245`in dondurduğu
    12'li ad listesi bu turda BÜYÜMEZ: boyut ucu `params` yüzeyinden okunur, `params=None` iken
    ölçülecek bir çift YOKTUR."""
    detay: list = []
    guard.classify_gate(PLAN, PORT, REG, {"limits": {**LIMITS, "max_open_positions": 15}}, None,
                        detail_out=detay)
    assert [d["check"] for d in detay] == [
        "exposure_budget", "max_open_positions", "sector_cap", "daily_loss_breaker",
        "position_size", "rr_floor", "heat_hard",
        "sector_stacking", "heat_review", "correlation", "leading_sector", "rr_marginal"]


def test_boyut_ucu_OLCULEMEZSE_hukum_degismez_ama_satir_SEBEBINI_TASIR():
    """UYDURMA YASAĞI: eksik uç 0 ya da varsayılan SAYILMAZ. Hüküm değişmez (fail-open — çift-bağ
    bir risk vetosu değil), ama satır "tavan tuttu" görüntüsü vermez."""
    hukum, nedenler, satirlar = _kapi(slot=15, boyut=None)
    assert hukum == "GO" and nedenler == [], nedenler
    satir = satirlar[KONTROL_ADI]
    assert satir["passed"] is True and satir["value"] is None
    assert "ÖLÇÜLEMEDİ" in (satir["note"] or ""), satir
    assert "position_size_r" in (satir["note"] or ""), satir


def test_saf_fonksiyon_dogrudan_da_okunabilir_ve_dort_durumu_ayirir():
    """Hüküm yalnız argümanlarının fonksiyonudur (guard SAFTIR) — dışarıdan çağrılabilir olması
    denetimin şartı."""
    assert guard.cift_bag_hukmu({}, PARAMS)[0] == "yok"
    assert guard.cift_bag_hukmu(LIMITS, PARAMS)[0] == "temiz"
    assert guard.cift_bag_hukmu(LIMITS, {"entry.min_score": 60})[0] == "olculemedi"
    assert guard.cift_bag_hukmu({**LIMITS, "max_open_positions": 15}, PARAMS)[0] == "kirildi"
    # ÇİFT birlikte oynadıysa kırılma YOK
    assert guard.cift_bag_hukmu({**LIMITS, "max_open_positions": 15},
                                {**PARAMS, "position_size_r": 0.65})[0] == "temiz"


def test_mantiksal_deger_sayi_SAYILMAZ():
    """`float(True) == 1.0` — bool bir slot/boyut değildir; sessizce "1" sayılırsa çivi yalan söyler."""
    assert guard.cift_bag_hukmu({**LIMITS, "max_open_positions": True}, PARAMS)[0] == "olculemedi"
    assert guard.cift_bag_hukmu(LIMITS, {**PARAMS, "position_size_r": True})[0] == "olculemedi"
    assert guard.cift_bag_hukmu(LIMITS, {**PARAMS, "position_size_r": "yarım"})[0] == "olculemedi"


# ================================================================================================
# YASA 6 + YETKİ SINIRI — KAYIT GERÇEKTEN İNDİ Mİ, VE HÜKMÜN REDDETTİĞİ İKİ ŞEY YAPILMADI MI
# ================================================================================================
def test_yasa6_kayit_repo_goal_yamlinda_DURUYOR_ve_olculen_cifti_tasiyor():
    limits = yaml.safe_load(GOAL_YAML.read_text(encoding="utf-8"))["limits"]
    kayit = limits.get("cift_bag_slot_boyut")
    assert isinstance(kayit, dict), "çift-bağ kaydı goal.yaml'dan düştü — çivi okuyucusuz kaldı"
    assert kayit["max_open_positions"] == OLCULEN_SLOT
    assert float(kayit["position_size_r"]) == OLCULEN_BOYUT
    assert KART in str(kayit.get("kart")), "kart atfı yok — ölçümsüz bir çift beyan edilmiş olurdu"
    # Kayıt YÜRÜRLÜKTEKİ zarfla tutarlı: canlı slot da 20 olmalı, yoksa kapı doğduğu gün REVIEW der.
    assert limits["max_open_positions"] == OLCULEN_SLOT


def test_yasa6_kaydin_OKUYUCUSU_guard_ve_GU1_surukleme_kapisi_kapali():
    assert "cift_bag_slot_boyut" in guard.LIMIT_KEYS, \
        "GU1: limits'e inen her ad LIMIT_KEYS ∪ REPLAY_WARMUP_KEYS'te olmalı"
    limits = yaml.safe_load(GOAL_YAML.read_text(encoding="utf-8"))["limits"]
    assert not (set(limits) - guard.LIMIT_KEYS - guard.REPLAY_WARMUP_KEYS)


def test_hukum_position_size_ri_LIMIT_KEYSe_ALMADI_ve_bounds_satiri_DOKUNULMADI():
    """Tasarım kapanışının AÇIKÇA reddettiği iki şey. Biri yapılırsa bu tur geçersizdir."""
    assert "position_size_r" not in guard.LIMIT_KEYS, \
        "arama uzayı kapatıldı — hüküm bunu reddetti (çivi yasak değil, insan kapısıdır)"
    assert "position_size_r" not in guard.GOAL_KEYS
    b = yaml.safe_load(BOUNDS_YAML.read_text(encoding="utf-8"))["position_size_r"]
    assert b == {"min": 0.1, "max": 1.0, "step": 0.1, "type": "float"}, \
        f"bounds.yaml position_size_r satırı DEĞİŞTİ: {b}"


def test_hermes_cift_bag_kaydini_ONEREMEZ():
    """Kayıt bir OPERATÖR KALEMİDİR: çiviyi ajanın kendisi sökemez."""
    bounds = {"position_size_r": {"min": 0.1, "max": 1.0, "step": 0.1, "type": "float"}}
    goal = {"limits": dict(LIMITS), "max_accepted_changes_per_month": 8}
    for ad in ("cift_bag_slot_boyut", "limits.cift_bag_slot_boyut"):
        v = guard.validate_change({"variable": ad, "new": 1}, {"position_size_r": 0.5},
                                  bounds, goal, [], 0)
        assert v.ok is False and any("immutable" in r for r in v.reasons), (ad, v.reasons)
