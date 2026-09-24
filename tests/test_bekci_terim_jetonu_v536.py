"""test_bekci_terim_jetonu_v536.py — bekçi brifingi terim korunumu KISA KARARLI JETONLA (TSK-138).

VAKA (A1, ölçüldü 2026-09-24): bekçi brifinginin teslim öncesi kural geçişinde korunmalı terim
listesi (`veri_terimleri`) ölçülemedi kalemlerinin TAM GÖRÜNEN ADIYDI; `soul_denetimi.terim_ihlali`
birebir alt-dize arar. Ad sayı taşıyan bir mesaj (`MECHANISM_STALE mekanizma gecikti: hermes_poll —
0.6 sa (pencere 0.5 sa) (kadans_olculemedi)`) ya da `… (toplu)` son ekli bir tarayıcı etiketi olduğu
için model kalemi adıyla ansa bile "eksik" sayıldı; 09-17→09-24 bekçi koşumlarının 6'sının 5'i ham
teslim edildi (09-21/22/24 üçü bu mekanik ihlalle). Düzeltme: kalem başına kısa kararlı jeton.

Aşağıdaki A1 ihlal metinleri `events.jsonl` `brifing_kural_denetimi` olaylarından AYNEN alındı.
"""
from __future__ import annotations

import importlib

import pytest

from ops import soul_denetimi


@pytest.fixture
def bekci():
    m = importlib.import_module("ops.bekci_brifingi")
    return importlib.reload(m)


def _b(ad, **kanit):
    """`ham["bildirilecek"]` öğesinin şekli: tarama kalemi `kalem` altında, kanıtı onun içinde."""
    return {"anahtar": f"olculemedi|{ad}", "sinif": "olculemedi", "ad": ad, "sebep": "ilk_gecis",
            "kalem": {"ad": ad, "deger": None, "kanit": dict(kanit)}}


#: A1'de ihlal üreten gerçek adlar (2026-09-07 · 09-13 · 09-21 · 09-22 · 09-24).
A1_TOPLU = _b("kadans_olculemedi (toplu)", neden="kadans_olculemedi", toplu=True, olay_sayisi=73)
A1_DONUK = _b("donuk_alan_yok (toplu)", neden="donuk_alan_yok", toplu=True, olay_sayisi=4)
A1_MEKANIZMA = _b("MECHANISM_STALE mekanizma gecikti: hermes_poll — 0.6 sa (pencere 0.5 sa) (kadans_olculemedi)",
                  neden="kadans_olculemedi",
                  olay="MECHANISM_STALE mekanizma gecikti: hermes_poll — 0.6 sa (pencere 0.5 sa)")
A1_SPRINT = _b("MECHANISM_STALE mekanizma gecikti: warmup_sprint — 8.0 sa (pencere 8.0 sa) (kadans_olculemedi)",
               neden="kadans_olculemedi",
               olay="MECHANISM_STALE mekanizma gecikti: warmup_sprint — 8.0 sa (pencere 8.0 sa)")
A1_ERTELEME = _b("session_deferred_for_coverage (kadans_olculemedi)", neden="kadans_olculemedi",
                 olay="session_deferred_for_coverage")
A1_RECONCILE = _b("reconcile_atlandi (kadans_olculemedi)", neden="kadans_olculemedi", olay="reconcile_atlandi")


def _ham(*kalemler, diger=()):
    return {"bildirilecek": [*kalemler, *diger]}


# ---------------------------------------------------------------------------------------------
# jeton seçimi
# ---------------------------------------------------------------------------------------------

def test_T1_toplu_kalem_nedenine_indirgenir(bekci):
    assert bekci._korunacak_terim(A1_TOPLU) == "kadans_olculemedi"
    assert bekci._korunacak_terim(A1_DONUK) == "donuk_alan_yok"


def test_T2_mekanizma_gecikmesi_mekanizma_adina_indirgenir(bekci):
    assert bekci._korunacak_terim(A1_MEKANIZMA) == "hermes_poll"
    assert bekci._korunacak_terim(A1_SPRINT) == "warmup_sprint"


def test_T3_olay_adi_bastaki_tanimlayiciya_indirgenir(bekci):
    assert bekci._korunacak_terim(A1_ERTELEME) == "session_deferred_for_coverage"
    assert bekci._korunacak_terim(A1_RECONCILE) == "reconcile_atlandi"


def test_T4_kanitsiz_kalem_tam_ada_doner(bekci):
    """ts_bozuk sınıfı gibi olay/toplu taşımayan kalem: eski davranış (tam ad)."""
    kalem = _b("zaman_damgasi_ayristirilamadi", neden="ts_bozuk", adet=41)
    assert bekci._korunacak_terim(kalem) == "zaman_damgasi_ayristirilamadi"


def test_T5_gorunen_adda_gecmeyen_jeton_kullanilmaz(bekci):
    """Model yalnız gördüğünü koruyabilir: jeton adda yoksa tam ada dönülür."""
    kalem = _b("başka bir görünen ad", olay="gizli_olay_adi")
    assert bekci._korunacak_terim(kalem) == "başka bir görünen ad"
    toplu = _b("etiket (toplu)", neden="adda_olmayan_neden", toplu=True)
    assert bekci._korunacak_terim(toplu) == "etiket (toplu)"


def test_T6_liste_yalniz_olculemedi_kalemlerinden_sirali_ve_tekil(bekci):
    takili = {"anahtar": "takili|x", "sinif": "takili", "ad": "warmup_merdiven_kilitli",
              "sebep": "ilk_gecis", "kalem": {"kanit": {"olay": "warmup_merdiven_kilitli"}}}
    ham = _ham(A1_RECONCILE, A1_MEKANIZMA, A1_TOPLU, A1_ERTELEME, A1_TOPLU, diger=[takili])
    assert bekci._korunacak_terimler(ham) == [
        "reconcile_atlandi", "hermes_poll", "kadans_olculemedi", "session_deferred_for_coverage"]


# ---------------------------------------------------------------------------------------------
# gerçek `terim_ihlali` ile davranış — A1 vakaları
# ---------------------------------------------------------------------------------------------

#: Kalemleri adıyla anan ama uzun satırları KENDİ cümlesiyle yeniden ifade eden bir model metni —
#: A1'de her koşumda ham teslime düşen biçim.
YENIDEN_IFADE = (
    "Bugün ölçülemeyen üç şey var: hermes_poll yarım saatlik pencereyi biraz aştı; "
    "warmup_sprint 8 saattir sessiz. reconcile_atlandi ve session_deferred_for_coverage için ritim "
    "kurulamadı (kadans_olculemedi, 73 olay). donuk_alan_yok sınıfında 4 olay var."
)


def test_T7_A1_yeniden_ifadesi_ARTIK_ihlal_uretmez(bekci):
    ham = _ham(A1_TOPLU, A1_DONUK, A1_MEKANIZMA, A1_SPRINT, A1_ERTELEME, A1_RECONCILE)
    assert soul_denetimi.terim_ihlali(YENIDEN_IFADE, bekci._korunacak_terimler(ham)) == []


def test_T8_eski_tam_ad_listesi_ayni_metinde_IHLAL_uretirdi(bekci):
    """Negatif kontrol — düzeltmeden ÖNCEKİ sözleşme: aynı metin tam adlarla altı ihlal üretir.
    Bu çivi 'jeton sayesinde geçti'nin 'kontrol hiçbir şeyi ölçmüyor'dan ayırt edilmesini sağlar."""
    ham = _ham(A1_TOPLU, A1_DONUK, A1_MEKANIZMA, A1_SPRINT, A1_ERTELEME, A1_RECONCILE)
    eski = [b["ad"] for b in bekci._olculemeyenler(ham)]
    assert len(soul_denetimi.terim_ihlali(YENIDEN_IFADE, eski)) == 6


def test_T9_kalemi_HIC_anmayan_metin_hala_ihlaldir(bekci):
    """Korunum gevşemedi, biçime tolerans verdi: susturulan kalem yine yakalanır."""
    ham = _ham(A1_MEKANIZMA, A1_ERTELEME)
    metin = "Bugün session_deferred_for_coverage ölçülemedi; başka kayda değer bir şey yok."
    ihlal = soul_denetimi.terim_ihlali(metin, bekci._korunacak_terimler(ham))
    assert ihlal == ["`hermes_poll` çıktıda YOK (susturulamaz terim)"]


# ---------------------------------------------------------------------------------------------
# bağlantı — kural geçişi YENİ listeyi gönderir
# ---------------------------------------------------------------------------------------------

def test_T10_kural_gecisi_kisa_jeton_listesini_gecir_e_verir(bekci, monkeypatch, sandbox_state):
    yakalanan = {}

    def _sahte_gecir(**kw):
        yakalanan.update(kw)
        return soul_denetimi.Gecis(metin="tamam", beyan="", hukum=None, cagri_n=1, yeniden_uretim=False)

    monkeypatch.setattr(bekci.soul_denetimi, "gecir", _sahte_gecir)
    monkeypatch.setattr(bekci.denetci_rota, "profil_model_kimligi", lambda *a, **k: None)
    ham = _ham(A1_MEKANIZMA, A1_TOPLU)
    metin, dal = bekci._kural_gecisi("cevap", "istem", ham)
    assert (metin, dal) == ("tamam", "llm")
    assert yakalanan["veri_terimleri"] == ["hermes_poll", "kadans_olculemedi"]
