"""test_fis_tekillestirme_v296.py — FİŞ KUYRUĞU AYNI ALANI ÜÇ KEZ FİŞLİYOR (2026-08-25).

ÖLÇÜLEN KUSUR (canlı `state/nous_fisler.json`): defterde **12 fiş** var ama bunlar **DÖRT** gerçek
kalem. Her haftalık koşu aynı gözlemi yeniden fişliyor:

    backtest_full.avg_r eksik      → fiş 1, 4, 9   (alan: sonuc_hukmu.tavan_durumu.durum)
    tahmin_isabeti n=1             → fiş 2, 5, 10  (alan: edge_hukmu.criteria.tahmin_isabeti.status)
    hotstate surec_ici_sayac null  → fiş 3, 6      (alan: coverage_ariza.hotstate)
    m2m dd / kuyruk ölçülemedi     → fiş 7, 8

KÖK NEDEN: `_fis_yaz` tekilleştirmeyi ÖNERİ KİMLİĞİ (`anahtar` = N00007) üzerinden yapıyordu. Ama
her koşuda beyin AYNI gözlem için YENİ bir öneri satırı üretiyor ve `_oneri_kaydet` ona YENİ bir id
veriyor — yani anahtar her hafta değişiyor ve "aynı öneri iki fiş üretmez" kapısı hiç kapanmıyordu.
Fişin kimliği ÖNERİ değil GÖZLEMİN ADRESİ (`alan`) olmalıydı.

BEDELİ: kuyruk üç kat şişik görünüyor (operatör "12 açık iş" sanıyor, gerçek dört) ve tekrarlar
önceliği bozuyor — aynı sorun üç YÜKSEK satır üretiyor.

BU BİR SUSTURMA DEĞİL BİR TEKİLLEŞTİRMEDİR: hiçbir gözlem düşmüyor. Tekrar sayısı `gorulme`
sayacında SAYILI duruyor (tekrar bir SİNYALDİR: her koşuda yeniden görülen sorun, bir kez görülenden
farklıdır), her tekrarın öneri kimliği `tekrarlar` izinde duruyor ve o kimlikler
`improvement_proposals.jsonl` satırlarının TAM metnine işaret ediyor. Yalnızca aynı gözlemin N.
kopyası AYRI BİR KUYRUK SATIRI olmuyor. Fiş kapandığında (durum değişince) alan yeniden açılabilir —
kalıcı susturma YOK.

HİÇBİR TEST LLM ÇAĞIRMAZ ve HİÇBİR TEST CANLI STATE'E YAZMAZ (`sandbox_state`).
"""
from __future__ import annotations

import pytest

from meridian import nous_eval, obs, store

_ALAN_A = "sonuc_hukmu.tavan_durumu.durum"
_ALAN_B = "edge_hukmu.criteria.tahmin_isabeti.status"


def _oneri(**ek) -> dict:
    """Kabul edilmiş TASARIM şekilli bir öneri (boru bunu FİŞ yoluna sokar)."""
    o = {"alan": _ALAN_A,
         "gozlem": "sonuc_hukmu.tavan_durumu.durum 'olculemedi' — backtest_full.avg_r yok",
         "oneri": "karne üreticisine backtest_full.avg_r alanını bas",
         "beklenen_etki": "tavan durumu ölçülebilir olur",
         "onerilen_olcum": "sonuc_hukmu.tavan_durumu.durum alanı",
         "oncelik": "yuksek", "sekil": "tasarim",
         "kanit_atifi": ["backtest_full", "tavan_durumu"]}
    o.update(ek)
    return o


@pytest.fixture
def olaylar(monkeypatch):
    kayit: list[dict] = []
    monkeypatch.setattr(obs, "log", lambda ev, **kw: kayit.append({"ev": ev, **kw}) or {})
    return kayit


def _defter() -> dict:
    return store.read_json(nous_eval.FISLER_FILE, {})


def _fis(alan: str) -> dict:
    for f in _defter().get("fisler") or []:
        if f.get("alan") == alan and str(f.get("durum") or "fislendi") == "fislendi":
            return f
    raise AssertionError(f"{alan} için AÇIK fiş yok")


# =================================================================================================
# (a) AYNI ALAN İÇİN İKİNCİ FİŞ YENİ SATIR AÇMAZ
# =================================================================================================
def test_ayni_alan_ikinci_fis_YENI_SATIR_acmaz(sandbox_state, olaylar):
    """Kusurun ta kendisi: üç koşu, üç FARKLI öneri kimliği, TEK gözlem → kuyrukta TEK satır."""
    for i, kimlik in enumerate(("N00001", "N00004", "N00009")):
        nous_eval.boru([_oneri(id=kimlik)], hafta=f"2026-W3{i}")
    doc = _defter()
    assert doc["n"] == 1, (f"aynı alan {doc['n']} satır açtı — kuyruk şişiyor, operatör "
                           f"'{doc['n']} açık iş' sanıyor")


# =================================================================================================
# (b) SAYAÇ ARTAR — TEKRAR BİLGİSİ KAYBOLMAZ
# =================================================================================================
def test_tekrar_SAYACI_artar(sandbox_state, olaylar):
    """Tekilleştirme SUSTURMA değil: kaçıncı kez görüldüğü SAYILI durur (tekrar bir sinyaldir)."""
    for i, kimlik in enumerate(("N00001", "N00004", "N00009")):
        nous_eval.boru([_oneri(id=kimlik)], hafta=f"2026-W3{i}")
    assert _fis(_ALAN_A)["gorulme"] == 3, "tekrar sayısı yutuldu — 3 kez görülen sorun 1 gibi duruyor"


def test_her_tekrarin_oneri_KIMLIGI_izde_durur(sandbox_state, olaylar):
    """HİÇBİR GÖZLEM DÜŞMEZ: iz, `improvement_proposals.jsonl` satırlarına işaret eden kimlikleri
    taşır — tam metin orada, kuyruk satırı şişmiyor."""
    for i, kimlik in enumerate(("N00001", "N00004", "N00009")):
        nous_eval.boru([_oneri(id=kimlik)], hafta=f"2026-W3{i}")
    iz = [t.get("anahtar") for t in _fis(_ALAN_A).get("tekrarlar") or []]
    assert iz == ["N00001", "N00004"], f"katlanan fişlerin kimlikleri kayboldu: {iz}"
    assert _fis(_ALAN_A)["anahtar"] == "N00009", "baş satır EN YENİ öneriyi göstermiyor"


# =================================================================================================
# (c) GÖZLEM METNİ TAZELENİR — EN YENİSİ KALIR
# =================================================================================================
def test_gozlem_metni_TAZELENIR(sandbox_state, olaylar):
    nous_eval.boru([_oneri(id="N00001", gozlem="ilk gözlem: alan boş")], hafta="2026-W30")
    nous_eval.boru([_oneri(id="N00004", gozlem="yeni gözlem: alan artık 'olculemedi' diyor",
                           oneri="üreticiyi düzelt")], hafta="2026-W31")
    f = _fis(_ALAN_A)
    assert f["gozlem"] == "yeni gözlem: alan artık 'olculemedi' diyor"
    assert f["oneri"] == "üreticiyi düzelt", "gözlem tazelendi ama öneri eskide kaldı (karma satır)"
    assert f["hafta"] == "2026-W30" and f["son_hafta"] == "2026-W31", "ilk/son görülme ayrımı yok"


def test_oncelik_YUKSELIRSE_gizlenmez(sandbox_state, olaylar):
    """Tekrar, önceliği SESSİZCE düşürmemeli: birleşen satır en AĞIR önceliği taşır."""
    nous_eval.boru([_oneri(id="N00001", oncelik="dusuk")], hafta="2026-W30")
    nous_eval.boru([_oneri(id="N00004", oncelik="yuksek")], hafta="2026-W31")
    assert _fis(_ALAN_A)["oncelik"] == "yuksek"


# =================================================================================================
# (d) FARKLI ALAN YENİ SATIR AÇAR — TEKİLLEŞTİRME FAZLA KAPSAMAZ
# =================================================================================================
def test_FARKLI_alan_YENI_satir_acar(sandbox_state, olaylar):
    nous_eval.boru([_oneri(id="N00001", alan=_ALAN_A)], hafta="2026-W30")
    nous_eval.boru([_oneri(id="N00002", alan=_ALAN_B)], hafta="2026-W30")
    doc = _defter()
    assert doc["n"] == 2, "farklı alanlar tek satıra katlandı — tekilleştirme FAZLA kapsıyor"
    assert _fis(_ALAN_A)["gorulme"] == 1 and _fis(_ALAN_B)["gorulme"] == 1


def test_alansiz_fis_ESKI_kimlik_tekilligini_korur(sandbox_state, olaylar):
    """`alan` boşsa katlanacak adres YOKTUR: eski kimlik-tekilliği yürürlükte kalır, iki AYRI
    kimlik iki AYRI satır açar (boş adres hepsini tek satıra yığsaydı bu bir susturma olurdu)."""
    nous_eval.boru([_oneri(id="N00001", alan="")], hafta="2026-W30")
    nous_eval.boru([_oneri(id="N00001", alan="")], hafta="2026-W30")
    nous_eval.boru([_oneri(id="N00002", alan="")], hafta="2026-W31")
    assert _defter()["n"] == 2


# =================================================================================================
# KAPANAN FİŞ YENİDEN AÇILABİLİR — KALICI SUSTURMA YOK
# =================================================================================================
def test_KAPANAN_fis_yeniden_ACILIR(sandbox_state, olaylar):
    nous_eval.boru([_oneri(id="N00001")], hafta="2026-W30")
    doc = _defter()
    doc["fisler"][0]["durum"] = "kapandi"
    store.write_json(nous_eval.FISLER_FILE, doc)
    nous_eval.boru([_oneri(id="N00004")], hafta="2026-W33")
    doc = _defter()
    assert doc["n"] == 2, "kapanmış fiş yeni gözlemi yuttu — tekilleştirme KALICI SUSTURMAYA döndü"
    assert _fis(_ALAN_A)["anahtar"] == "N00004"
    assert [f for f in doc["fisler"] if f["durum"] == "kapandi"][0]["anahtar"] == "N00001"


# =================================================================================================
# AYNI ÖNERİNİN YENİDEN İŞLENMESİ SAYACI ŞİŞİRMEZ (eski sözleşme korunur)
# =================================================================================================
def test_ayni_onerinin_yeniden_islenmesi_SAYACI_artirmaz(sandbox_state, olaylar):
    """Boru iki kez koşarsa (tekrar-ayrıştırma yolu) bu YENİ bir gözlem değildir. Sayaç DİSTİNCT
    öneri sayar; aynı kimliğin ikinci işlenişi hiçbir şeyi değiştirmez."""
    for _ in range(3):
        nous_eval.boru([_oneri(id="N00007")], hafta="2026-W32")
    doc = _defter()
    assert doc["n"] == 1 and doc["fisler"][0]["gorulme"] == 1


# =================================================================================================
# DEFTERDEKİ MEVCUT TEKRARLAR DA KATLANIR (canlıdaki 12 → 4)
# =================================================================================================
def test_defterdeki_MEVCUT_tekrarlar_katlanir(sandbox_state, olaylar):
    """Yalnız ileriye dönük tekilleştirme canlıdaki 12 satırı 12 bırakırdı — operatörün gördüğü
    sayı değişmezdi. Katlama AÇIK satırlara uygulanır, kapanmışlara DOKUNMAZ."""
    eski = {"fisler": [
        {"anahtar": "N00001", "alan": _ALAN_A, "durum": "fislendi", "hafta": "2026-W30",
         "gozlem": "eski gözlem", "oneri": "eski öneri", "oncelik": "yuksek"},
        {"anahtar": "N00002", "alan": _ALAN_B, "durum": "fislendi", "hafta": "2026-W30",
         "gozlem": "b gözlemi", "oneri": "b önerisi", "oncelik": "orta"},
        {"anahtar": "N00004", "alan": _ALAN_A, "durum": "fislendi", "hafta": "2026-W31",
         "gozlem": "orta gözlem", "oneri": "orta öneri", "oncelik": "yuksek"},
        {"anahtar": "N00009", "alan": _ALAN_A, "durum": "fislendi", "hafta": "2026-W32",
         "gozlem": "son gözlem", "oneri": "son öneri", "oncelik": "yuksek"},
    ], "n": 4}
    store.write_json(nous_eval.FISLER_FILE, eski)
    nous_eval.boru([_oneri(id="N00012", alan=_ALAN_B, gozlem="b yeniden")], hafta="2026-W33")
    doc = _defter()
    assert doc["n"] == 2, f"mevcut tekrarlar katlanmadı: {[f['anahtar'] for f in doc['fisler']]}"
    assert _fis(_ALAN_A)["gorulme"] == 3 and _fis(_ALAN_A)["gozlem"] == "son gözlem"
    assert _fis(_ALAN_B)["gorulme"] == 2 and _fis(_ALAN_B)["gozlem"] == "b yeniden"
    assert doc["n"] == len(doc["fisler"])


# =================================================================================================
# SAYAÇ EKRANDA OKUNUR: OLAY + KALEM + UÇ
# =================================================================================================
def test_sayac_OLAYA_yazilir(sandbox_state, olaylar):
    nous_eval.boru([_oneri(id="N00001")], hafta="2026-W30")
    nous_eval.boru([_oneri(id="N00004")], hafta="2026-W31")
    ev = [e for e in olaylar if e["ev"] == nous_eval.OLAY_FIS]
    assert len(ev) == 2
    assert ev[0]["gorulme"] == 1 and ev[1]["gorulme"] == 2
    assert "2. kez" in ev[1]["detail"], "tekrar bilgisi olay metninde okunmuyor"
    assert "otomatik uygulama yolu YOK" in ev[1]["detail"], "fişin anayasal cümlesi kayboldu"


def test_sayac_boru_KALEMINDE_doner(sandbox_state, olaylar):
    nous_eval.boru([_oneri(id="N00001")], hafta="2026-W30")
    out = nous_eval.boru([_oneri(id="N00004")], hafta="2026-W31")
    assert out["kalemler"][0]["gorulme"] == 2
    assert out["ozet"]["fis_birlesen"] == 1 and out["ozet"]["fis_yeni"] == 0


def test_kuru_kosumda_sayac_UYDURULMAZ(sandbox_state, olaylar):
    """UYDURMA YASAĞI: `yaz=False` defteri okumaz da yazmaz da — sayaç ÖLÇÜLEMEZ, 1 yazılmaz."""
    nous_eval.boru([_oneri(id="N00001")], hafta="2026-W30", yaz=False)
    ev = [e for e in olaylar if e["ev"] == nous_eval.OLAY_FIS][0]
    assert ev["gorulme"] is None and ev["gorulme_olculemedi"]
    assert store.read_json(nous_eval.FISLER_FILE, None) is None


def test_UCTA_pano_rozeti_EN_YENI_oneriyle_eslesir(sandbox_state, olaylar):
    """PANO REGRESYON ÇİVİSİ: kart `fis.anahtarlar` içinde ÖNERİNİN id'sini arar ve bulamazsa
    'fişlenmedi — boru bu satırı işlemedi' UYARISI basar. Birleşen satırın başı en yeni öneriye
    dönmezse boru doğru çalışırken pano YANLIŞ alarm verirdi (alarm yorgunluğu)."""
    from meridian import api
    nous_eval.boru([_oneri(id="N00001")], hafta="2026-W30")
    nous_eval.boru([_oneri(id="N00004")], hafta="2026-W31")
    d = api._nous_fisler()
    assert d["n"] == 1 and d["n_acik"] == 1
    assert "N00004" in d["anahtarlar"], "pano bu haftanın önerisini 'fişlenmemiş' gösterirdi"
    assert d["fisler"][0]["gorulme"] == 2, "sayaç uca taşınmıyor — ekranda okunamaz"
