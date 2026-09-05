"""tests/test_edg079_olcum_v426.py — EDG-2026-079 ÖLÇÜM betiğinin çivisi
(TSK-156 dilim-2 (a), TSK-066 girdisi, 2026-09-05).

NE ÖLÇER. `research/olcumler/edg079_replay_pit_denetimi/olcum.py` — kartın (`EDG-2026-079-
replay-defteri-pit-uyelik-denetimi.yaml`) K1 (işlem düzeyi survivorship sızıntısı, tohum/canlı
AYRI), K2 (evren düzeyi geç-katılan payı) ve pozitif kontrolünü (YOL-TUTARLI, rename eşlemesi
DAHİL) SENTETİK fikstürlerle doğru ölçtüğünü kanıtlar. AĞA ÇIKMAZ: `httpx` bu dosyada HİÇ
ÇAĞRILMAZ — betik zaten `--girdi-html` ile verilen dosyayı okur, hiçbir ağ isteği yapmaz. Bu
dosya AŞAĞIDAKİLERİ ölçer:
  (a) eşikler kartın YAPILANDIRILMIŞ `esikler:` alanından okunuyor, eksikse UYDURMUYOR
      (edg071/edg075 `esikleri_karttan_oku` emsali) — GERÇEK EDG-2026-079 kartına karşı sınanır;
  (b) `esik_bandlarini_ayristir` kartın serbest-metin eşik cümlesini (`p ≤ 0,02 → '...'; ...`)
      bant listesine ÇÖZÜYOR — eşik SAYILARI (0,02/0,10) bu test dosyasında da KODA YAZILMAZ,
      GERÇEK karttan okunan metinden türetilir; `hukum_sinifi_sec` sınır değerlerinde (≤/></<)
      doğru bandı seçiyor;
  (c) ticker/tarih normalizasyonu (`.`→`-`, upper; `ts_open` ISO'ya indirgeme, ayrıştırılamayan
      → None) UYDURMADAN çalışıyor;
  (d) `islem_uye_mi`: doğrudan üyelik, doğrudan sızıntı, RENAME eşlemesiyle üyelik (kaynak sınırı
      düzeltmesi — `SEMBOL_YENIDEN_ADLANDIRMA`, EQR→VMRK 2026-08-18), ts_open/ticker ölçülemeyen
      `(None, neden)` döner (paya girmez);
  (e) K1 (`k1_hesapla`): 6 işlemlik sentetik defter üstünde tohum/canlı AYRI raporlanıyor, `p`
      doğru, sızanlar listesi doğru, `n=0` iken `p`/`hukum_sinifi` None (bölme UYDURULMAZ);
  (f) MUTASYON 1 (CLAUDE.md §6 "çivi yeşili kanıt değildir"): `islem_uye_mi` HER ZAMAN True
      dönecek şekilde monkeypatch'lenirse `n_sizinti` GERÇEKTEN 0'a düşüyor — testin ana iddiası
      (`n_sizinti == 2`) bu dalı ISIRIYOR;
  (g) MUTASYON 2: rename defteri BOŞ verilirse (rename dalı fiilen devre dışı) EQR işlemi ARTIK
      sızıntı sayılıyor (`uye_mi` True'dan False'a düşüyor) — rename dalının GERÇEKTEN gerekli
      olduğunun kanıtı;
  (h) K2 (`k2_hesapla`): GERÇEK `REPLAY_UNIVERSE` YERİNE verilen sentetik evren listesiyle `q`
      doğru hesaplanıyor (kart notu: "REPLAY yerine verilen sentetik evren listesi");
  (i) POZİTİF KONTROL (`pozitif_kontrol`): kartın üç sentetik vakası (FERG giriş-öncesi/-sonrası,
      EQR rename) AYNI `islem_uye_mi` ile `tuttu=True` veriyor;
  (j) ADIM-0: üç girdinin sha256'sı `SHA256.txt`/kart metniyle eşleşmezse `gecerli=False` ve
      `olc()` bu turda K1/K2/pozitif_kontrol'ü KOŞTURMUYOR (üç alan None, Yasa 6 — sonuç YİNE
      üretiliyor);
  (k) `main()` CLI ucu (`--olc --trades ... --guncel-liste ... --girdi-html ... --kart ...
      --cikti ...`) UÇTAN UCA çalışıyor ve `sonuc.json` şemasının beklenen anahtarlarını taşıyor
      (betiğin GERÇEK çağrı BİÇİMİ, Rol-1'in koşacağı komut, burada bir kez sınanır).

KAPSAM DIŞI: kartın hükmü (Rol-1 verir, CLAUDE.md §3/§5) — bu dosya betiğin DOĞRU ÖLÇTÜĞÜNÜ
kanıtlar, "PIT evren zorunlu mu" kararı vermez. `meridian/*.py`ye bu betik/test HİÇ dokunmaz
(yalnız `REPLAY_UNIVERSE`/`SEMBOL_YENIDEN_ADLANDIRMA` OKUNUR). Gerçek `--girdi-html` (Wikipedia
ham HTML'i) bu ajan turunda hiç kullanılmadı — testler SENTETİK küçük HTML tablosu kullanır
(edg075 `tabloyu_ayristir`/`hedef_tablo_bul` yardımcıları, `research/olcumler/edg075_sp500_
tarihsel/olcum.py::tabloyu_ayristir`, aynı şemayla — Date/Added/Removed/Reason düz başlık,
edg075 fikstürü `_HTML_DUZ`'ün desenidir)."""
from __future__ import annotations

import hashlib
import json
import pathlib

import pytest

from tests.conftest import betikten_modul_yukle

KOK = pathlib.Path(__file__).resolve().parents[1]
BETIK_YOLU = KOK / "research" / "olcumler" / "edg079_replay_pit_denetimi" / "olcum.py"
KART_YOLU = KOK / "research" / "cards" / "EDG-2026-079-replay-defteri-pit-uyelik-denetimi.yaml"


def _olcum():
    return betikten_modul_yukle(BETIK_YOLU, "edg079_olcum")


def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


# ==================================================================================
# fikstür — TEK HTML tablosu, TEK trades defteri, TEK güncel liste; TÜM testler bunu paylaşır
# ==================================================================================
# Şema `_HTML_DUZ` (edg075 v420) ile AYNI: düz tek-satır başlık (Date/Added/Removed/Reason).
# TEK olay: FERG girişi 2026-08-05 (gerçek tarih, kart `bilinen_olaylar` — EDG-075/076 kartı).
# BİLEREK EQR/VMRK için satır YOK: gerçek "Historical components" tablosunun TEK KAYNAK SINIRI
# budur (`meridian/adapters/constituents.py` modül başlığı (f)) — VMRK bugünkü listede olduğu
# için tablo olmadan `as_of` her tarihte VMRK'yi üye sayar, EQR'yi HİÇ döndürmez; rename dalı bu
# yüzden GERÇEKTEN gereklidir (MUTASYON 2 bunu ısırır).
_HTML = """
<table>
<tr><th>Date</th><th>Added</th><th>Removed</th><th>Reason</th></tr>
<tr><td>August 5, 2026</td><td>FERG</td><td>ZZZOLD</td><td>market cap</td></tr>
</table>
"""

_GUNCEL_UYELER = ["AAPL", "MSFT", "FERG", "VMRK", "GOOGL"]          # 5 üyeli güncel liste

# 6 işlemlik trades defteri (5 replay_seed/tohum + 1 live_paper/canlı):
#   T1 AAPL  2022-01-10 tohum  → hiç dokunulmadı, HER ZAMAN üye
#   T2 FERG  2026-07-01 tohum  → giriş (08-05) ÖNCESİ → SIZINTI
#   T3 FERG  2026-08-10 tohum  → giriş SONRASI → ÜYE
#   T4 EQR   2026-06-01 tohum  → rename (EQR→VMRK 08-18) ÖNCESİ, VMRK üye → RENAME İLE ÜYE
#   T5 ZQXX  2023-05-01 tohum  → hiçbir zaman üye/eklenen DEĞİL → SIZINTI
#   T6 AAPL  2026-01-15 canlı  → ÜYE (canlı grubun tek ölçülebilir satırı)
_TRADES_ROWS = [
    {"seq": 1, "id": "T1", "ticker": "AAPL", "ts_open": "2022-01-10", "kaynak": "replay_seed", "r_multiple": 0.5},
    {"seq": 2, "id": "T2", "ticker": "FERG", "ts_open": "2026-07-01", "kaynak": "replay_seed", "r_multiple": -0.6},
    {"seq": 3, "id": "T3", "ticker": "FERG", "ts_open": "2026-08-10", "kaynak": "replay_seed", "r_multiple": 0.8},
    {"seq": 4, "id": "T4", "ticker": "EQR", "ts_open": "2026-06-01", "kaynak": "replay_seed", "r_multiple": 0.3},
    {"seq": 5, "id": "T5", "ticker": "ZQXX", "ts_open": "2023-05-01", "kaynak": "replay_seed", "r_multiple": -1.2},
    {"seq": 6, "id": "T6", "ticker": "AAPL", "ts_open": "2026-01-15", "kaynak": "live_paper", "r_multiple": 0.2},
]

_K1_BANT_METNI = "p ≤ 0,02 → 'ihmal edilebilir'; 0,02 < p ≤ 0,10 → 'zorunlu'; p > 0,10 → 'survivorship'"
_K2_BANT_METNI = "q ≤ 0,10 → 'kabul'; q > 0,10 → 'yeniden kurulum'"


def _degisiklikler_ve_rename(o):
    degisiklikler, _ = o.tabloyu_ayristir(_HTML)
    rename = list(o.SEMBOL_YENIDEN_ADLANDIRMA)
    return degisiklikler, rename


def _guncel_set(o):
    return {o._normalize_ticker(g) for g in _GUNCEL_UYELER}


# ==================================================================================
# (a) eşikler GERÇEK karttan okunuyor
# ==================================================================================

def test_esikler_gercek_karttan_okunur():
    o = _olcum()
    esikler = o.esikleri_karttan_oku(KART_YOLU)
    assert esikler["kart_id"] == "EDG-2026-079"
    assert "0,02" in esikler["k1_gecti"] and "0,10" in esikler["k1_gecti"]
    assert "0,10" in esikler["k2_gecti"]


def test_esik_alani_eksikse_UYDURMAZ_value_error_atar(tmp_path):
    o = _olcum()
    bozuk = tmp_path / "bozuk.yaml"
    bozuk.write_text("card_id: X\nesikler:\n  k1_gecti: 'x'\n", encoding="utf-8")
    with pytest.raises(ValueError, match="k2_gecti"):
        o.esikleri_karttan_oku(bozuk)


def test_kart_sozluk_degilse_value_error(tmp_path):
    o = _olcum()
    bozuk = tmp_path / "liste.yaml"
    bozuk.write_text("- a\n- b\n", encoding="utf-8")
    with pytest.raises(ValueError, match="sözlük değil"):
        o.esikleri_karttan_oku(bozuk)


# ==================================================================================
# (b) eşik BANDI ayrıştırma + sınıflandırma — GERÇEK kart metniyle
# ==================================================================================

def test_esik_bandlarini_ayristir_gercek_k1_metni_uc_bant_verir():
    o = _olcum()
    esikler = o.esikleri_karttan_oku(KART_YOLU)
    bantlar = o.esik_bandlarini_ayristir(esikler["k1_gecti"], "p")
    assert len(bantlar) == 3
    assert bantlar[0]["esik"] == 0.02 and bantlar[0]["op"] == "≤"
    assert bantlar[1]["alt"] == 0.02 and bantlar[1]["esik"] == 0.10
    assert bantlar[2]["op"] == ">" and bantlar[2]["esik"] == 0.10
    # etiketler tırnaksız, kartın GERÇEK metni (uydurma yok — kod bu cümleleri KOPYALAMADI)
    assert "ihmal edilebilir" in bantlar[0]["etiket"]
    assert "survivorship" in bantlar[2]["etiket"]


def test_esik_bandlarini_ayristir_gercek_k2_metni_iki_bant_verir():
    o = _olcum()
    esikler = o.esikleri_karttan_oku(KART_YOLU)
    bantlar = o.esik_bandlarini_ayristir(esikler["k2_gecti"], "q")
    assert len(bantlar) == 2
    assert bantlar[0]["esik"] == bantlar[1]["esik"] == 0.10


def test_esik_bandi_kaliba_uymayan_metin_value_error():
    o = _olcum()
    with pytest.raises(ValueError, match="beklenen kalıba uymuyor"):
        o.esik_bandlarini_ayristir("bu cümlede eşik yok", "p")


def test_hukum_sinifi_sec_sinir_degerleri_dogru_bantlanir():
    o = _olcum()
    bantlar = o.esik_bandlarini_ayristir(_K1_BANT_METNI, "p")
    assert o.hukum_sinifi_sec(0.0, bantlar) == "ihmal edilebilir"
    assert o.hukum_sinifi_sec(0.02, bantlar) == "ihmal edilebilir"          # sınır DAHİL (≤)
    assert o.hukum_sinifi_sec(0.021, bantlar) == "zorunlu"
    assert o.hukum_sinifi_sec(0.10, bantlar) == "zorunlu"                  # üst sınır DAHİL (≤)
    assert o.hukum_sinifi_sec(0.101, bantlar) == "survivorship"


# ==================================================================================
# (c) normalizasyon
# ==================================================================================

def test_normalize_ticker_nokta_tire_ve_upper():
    o = _olcum()
    assert o._normalize_ticker("brk.b") == "BRK-B"
    assert o._normalize_ticker(" ferg ") == "FERG"
    assert o._normalize_ticker(None) is None
    assert o._normalize_ticker("") is None


def test_ts_open_tarihi_ayristirma():
    o = _olcum()
    assert o._ts_open_tarihi("2026-08-05") == "2026-08-05"
    assert o._ts_open_tarihi("2026-08-05T10:15:00") == "2026-08-05"        # saat kırpılır
    assert o._ts_open_tarihi("belirsiz-tarih") is None
    assert o._ts_open_tarihi(None) is None
    assert o._ts_open_tarihi("") is None


# ==================================================================================
# (d) islem_uye_mi — doğrudan üye / sızıntı / rename / ölçülemedi
# ==================================================================================

def test_islem_uye_mi_dogrudan_uye_asla_dokunulmayan_sembol():
    o = _olcum()
    degisiklikler, rename = _degisiklikler_ve_rename(o)
    uye_mi, neden = o.islem_uye_mi("AAPL", "2022-01-10", degisiklikler, _guncel_set(o), rename, {})
    assert uye_mi is True and neden is None


def test_islem_uye_mi_giris_oncesi_sizinti():
    o = _olcum()
    degisiklikler, rename = _degisiklikler_ve_rename(o)
    uye_mi, neden = o.islem_uye_mi("FERG", "2026-07-01", degisiklikler, _guncel_set(o), rename, {})
    assert uye_mi is False and neden is None


def test_islem_uye_mi_giris_sonrasi_uye():
    o = _olcum()
    degisiklikler, rename = _degisiklikler_ve_rename(o)
    uye_mi, neden = o.islem_uye_mi("FERG", "2026-08-10", degisiklikler, _guncel_set(o), rename, {})
    assert uye_mi is True and neden is None


def test_islem_uye_mi_hicbir_zaman_uye_olmayan_sizinti():
    o = _olcum()
    degisiklikler, rename = _degisiklikler_ve_rename(o)
    uye_mi, neden = o.islem_uye_mi("ZQXX", "2023-05-01", degisiklikler, _guncel_set(o), rename, {})
    assert uye_mi is False and neden is None


def test_islem_uye_mi_rename_ile_uye_eqr_vmrk():
    """Kaynak sınırı düzeltmesi: tabloda EQR/VMRK için satır YOK — doğrudan `EQR ∈ as_of` False
    çıkar, ama `SEMBOL_YENIDEN_ADLANDIRMA` (EQR→VMRK 2026-08-18) ile 'yeni ad' (VMRK) as_of'ta
    VAR ve işlem tarihi rename'den ÖNCE — üye SAYILIR."""
    o = _olcum()
    degisiklikler, rename = _degisiklikler_ve_rename(o)
    uye_mi, neden = o.islem_uye_mi("EQR", "2026-06-01", degisiklikler, _guncel_set(o), rename, {})
    assert uye_mi is True and neden is None


def test_islem_uye_mi_ts_open_ayristirilamiyorsa_olculemedi_None_doner():
    o = _olcum()
    degisiklikler, rename = _degisiklikler_ve_rename(o)
    uye_mi, neden = o.islem_uye_mi("AAPL", "gecersiz", degisiklikler, _guncel_set(o), rename, {})
    assert uye_mi is None and neden and "ts_open" in neden


def test_islem_uye_mi_ticker_boşsa_olculemedi_None_doner():
    o = _olcum()
    degisiklikler, rename = _degisiklikler_ve_rename(o)
    uye_mi, neden = o.islem_uye_mi("", "2026-01-01", degisiklikler, _guncel_set(o), rename, {})
    assert uye_mi is None and neden and "ticker" in neden


def test_as_of_onbellek_tarih_basina_bir_kez_kurulur():
    """Performans notu (kart `olcum_plani`): AYNI tarih için `as_of` İKİNCİ kez ÇAĞRILMAZ —
    önbellek sözlüğü paylaşılan iki çağrı arasında BÜYÜMEZ (tek anahtar kalır)."""
    o = _olcum()
    degisiklikler, rename = _degisiklikler_ve_rename(o)
    onbellek: dict = {}
    o.islem_uye_mi("AAPL", "2026-07-01", degisiklikler, _guncel_set(o), rename, onbellek)
    o.islem_uye_mi("FERG", "2026-07-01", degisiklikler, _guncel_set(o), rename, onbellek)
    assert list(onbellek.keys()) == ["2026-07-01"]


# ==================================================================================
# (e)+(f)+(g) K1 — 6 işlemlik senaryo, tohum/canlı ayrımı + İKİ MUTASYON
# ==================================================================================

def _k1_bantlari(o):
    return o.esik_bandlarini_ayristir(_K1_BANT_METNI, "p")


def test_k1_hesapla_tohum_canli_ayrimi_ve_sizinti_sayimi_dogru():
    o = _olcum()
    degisiklikler, rename = _degisiklikler_ve_rename(o)
    k1 = o.k1_hesapla(_TRADES_ROWS, degisiklikler, _guncel_set(o), rename, _k1_bantlari(o))

    tohum = k1["tohum"]
    assert tohum["n"] == 5
    assert tohum["n_uye"] == 3            # AAPL, FERG(sonrası), EQR(rename)
    assert tohum["n_sizinti"] == 2         # FERG(öncesi), ZQXX
    assert tohum["p"] == pytest.approx(0.4)
    assert tohum["olculemedi_n"] == 0
    assert {s["ticker"] for s in tohum["sizanlar"]} == {"FERG", "ZQXX"}
    assert tohum["hukum_sinifi"] == "survivorship"       # p=0.4 > 0.10

    canli = k1["canli"]
    assert canli["n"] == 1 and canli["n_uye"] == 1 and canli["n_sizinti"] == 0
    assert canli["p"] == pytest.approx(0.0)
    assert canli["hukum_sinifi"] == "ihmal edilebilir"


def test_k1_hesapla_olculemeyen_satir_paya_girmez():
    o = _olcum()
    degisiklikler, rename = _degisiklikler_ve_rename(o)
    trades = list(_TRADES_ROWS) + [
        {"seq": 7, "id": "T7", "ticker": "AAPL", "ts_open": None, "kaynak": "replay_seed", "r_multiple": 0.1},
    ]
    k1 = o.k1_hesapla(trades, degisiklikler, _guncel_set(o), rename, _k1_bantlari(o))
    assert k1["tohum"]["olculemedi_n"] == 1
    assert k1["tohum"]["n"] == 5           # 6 tohum satırından 1'i ölçülemedi, PAYA GİRMEDİ


def test_k1_hesapla_n_sifirsa_p_ve_hukum_None():
    o = _olcum()
    degisiklikler, rename = _degisiklikler_ve_rename(o)
    k1 = o.k1_hesapla([], degisiklikler, _guncel_set(o), rename, _k1_bantlari(o))
    assert k1["tohum"]["n"] == 0
    assert k1["tohum"]["p"] is None
    assert k1["tohum"]["hukum_sinifi"] is None


def test_MUTASYON_uye_mi_hep_true_olursa_sizinti_sifirlanir(monkeypatch):
    """REGRESYON ÇİVİSİ: `k1_hesapla` `islem_uye_mi`i modül-düzeyi ADIYLA çağırır — bu fonksiyon
    monkeypatch'lenip HER ZAMAN (True, None) dönecek şekilde bozulursa (sızıntı asla
    yakalanmaz), `n_sizinti` GERÇEKTEN 0'a düşer. Ana iddia (`n_sizinti == 2`, yukarıdaki test)
    bu mutasyonu YAKALAR — mutasyon koşulmadan çivi yeşil olsa bile bu ayrı doğrulama, çivinin
    GERÇEKTEN bu dalı ısırdığını gösterir (CLAUDE.md §6)."""
    o = _olcum()
    degisiklikler, rename = _degisiklikler_ve_rename(o)
    dogru = o.k1_hesapla(_TRADES_ROWS, degisiklikler, _guncel_set(o), rename, _k1_bantlari(o))
    assert dogru["tohum"]["n_sizinti"] == 2

    monkeypatch.setattr(o, "islem_uye_mi", lambda *a, **k: (True, None))
    mutasyonlu = o.k1_hesapla(_TRADES_ROWS, degisiklikler, _guncel_set(o), rename, _k1_bantlari(o))
    assert mutasyonlu["tohum"]["n_sizinti"] == 0, (
        "MUTASYON dalını çivi ISIRMIYOR: uye_mi hep True olsa da sızıntı hâlâ sayılıyor")


def test_MUTASYON_rename_defteri_bos_verilirse_eqr_sizinti_sayilir():
    """MUTASYON 2 (kart `girdi_kimligi.rename_defteri` dalı): rename defteri BOŞ verilirse (rename
    dalı fiilen devre dışı kalırsa) EQR işlemi ARTIK üye SAYILMAZ — rename dalının bu ölçümde
    GERÇEKTEN gerekli olduğunun kanıtı (monkeypatch'e gerek yok: parametre değişimi yeterli
    mutasyon — edg075 `tolerans_gun=0` deseniyle AYNI disiplin)."""
    o = _olcum()
    degisiklikler, rename = _degisiklikler_ve_rename(o)
    dogru_uye_mi, _ = o.islem_uye_mi("EQR", "2026-06-01", degisiklikler, _guncel_set(o), rename, {})
    assert dogru_uye_mi is True

    mutasyonlu_uye_mi, neden = o.islem_uye_mi("EQR", "2026-06-01", degisiklikler, _guncel_set(o), [], {})
    assert mutasyonlu_uye_mi is False, (
        "MUTASYON dalını çivi ISIRMIYOR: rename defteri boşken de EQR hâlâ üye sayılıyor")
    assert neden is None            # False bir ÖLÇÜM sonucu — 'olculemedi' DEĞİL


# ==================================================================================
# (h) K2 — GERÇEK REPLAY_UNIVERSE YERİNE sentetik evren
# ==================================================================================

def test_k2_hesapla_sentetik_evren_ile_dogru_q():
    o = _olcum()
    degisiklikler, _rename = _degisiklikler_ve_rename(o)
    bantlar = o.esik_bandlarini_ayristir(_K2_BANT_METNI, "q")
    # 4 sembollü sentetik evren: AAPL/MSFT hep üye, FERG 2022-01-01'de DEĞİL (08-05'te girdi),
    # ZQXX hiçbir zaman üye değil → t_evren=2022-01-01'de 2/4 üye-olmayan, q=0.5
    evren = ["AAPL", "MSFT", "FERG", "ZQXX"]
    # ikinci kesit BİLEREK 2026-09-01 verildi (kartın gerçek varsayılanı 2024-01-01'dir — FERG'in
    # GERÇEK giriş tarihi 2026-08-05'ten SONRAKİ bir tarih seçilmezse iki kesit AYNI çıkar ve
    # fonksiyonun iki tarihi BAĞIMSIZ hesapladığı gösterilemez; bu yalnız BU testin seçimidir).
    k2 = o.k2_hesapla(evren, degisiklikler, _guncel_set(o), "2022-01-01", bantlar,
                      ikinci_kesit="2026-09-01")
    assert k2["n_evren"] == 4
    assert set(k2["uye_olmayanlar"]) == {"FERG", "ZQXX"}
    assert k2["q"] == pytest.approx(0.5)
    assert k2["hukum_sinifi"] == "yeniden kurulum"
    # ikinci kesit (2026-09-01, FERG artık üye — girişi 08-05 GEÇTİ): yalnız ZQXX kalır, BİLGİ amaçlı
    assert set(k2["ikinci_kesit"]["uye_olmayanlar"]) == {"ZQXX"}
    assert k2["ikinci_kesit"]["q"] == pytest.approx(0.25)


def test_k2_hesapla_evren_bossa_q_None():
    o = _olcum()
    degisiklikler, _rename = _degisiklikler_ve_rename(o)
    bantlar = o.esik_bandlarini_ayristir(_K2_BANT_METNI, "q")
    k2 = o.k2_hesapla([], degisiklikler, _guncel_set(o), "2022-01-01", bantlar)
    assert k2["n_evren"] == 0 and k2["q"] is None and k2["hukum_sinifi"] is None


# ==================================================================================
# (i) POZİTİF KONTROL — kartın üç sentetik vakası, YOL-TUTARLI
# ==================================================================================

def test_pozitif_kontrol_uc_vaka_tuttu():
    o = _olcum()
    degisiklikler, rename = _degisiklikler_ve_rename(o)
    pk = o.pozitif_kontrol(degisiklikler, _guncel_set(o), rename)
    assert pk["tuttu"] is True
    assert len(pk["detay"]) == 3
    for d in pk["detay"]:
        assert d["tuttu"] is True and d["olculen"] == d["beklenen"]


def test_pozitif_kontrol_rename_vakasi_dogru_isimlendirilmis():
    o = _olcum()
    degisiklikler, rename = _degisiklikler_ve_rename(o)
    pk = o.pozitif_kontrol(degisiklikler, _guncel_set(o), rename)
    eqr = next(d for d in pk["detay"] if d["ticker"] == "EQR")
    assert eqr["beklenen"] is True and eqr["olculen"] is True


# ==================================================================================
# (j) ADIM-0 — sha uyuşmazlığında gecerli False, K'lar None
# ==================================================================================

def _girdi_dosyalarini_yaz(tmp_path, trades_bozuk=False):
    trades_bytes = json.dumps({"rows": _TRADES_ROWS}).encode("utf-8")
    guncel_bytes = json.dumps(_GUNCEL_UYELER).encode("utf-8")
    html_bytes = _HTML.encode("utf-8")

    trades_p = tmp_path / "trades.json"
    guncel_p = tmp_path / "guncel.json"
    html_p = tmp_path / "changes.html"
    trades_p.write_bytes(trades_bytes)
    guncel_p.write_bytes(guncel_bytes)
    html_p.write_bytes(html_bytes)

    # SHA256.txt DOĞRU sha'larla yazılır; `trades_bozuk=True` ise DOSYA İÇERİĞİ SONRADAN
    # değiştirilir (kayıt hâlâ ESKİ içeriği gösterir) — gerçek bir uyuşmazlık senaryosu.
    (tmp_path / "SHA256.txt").write_text(
        f"{_sha(trades_bytes)}  trades.json\n{_sha(guncel_bytes)}  guncel.json\n", encoding="utf-8")

    kart_p = tmp_path / "kart.yaml"
    kart_p.write_text(
        "card_id: TEST-EDG-079\n"
        "esikler:\n"
        f"  k1_gecti: \"{_K1_BANT_METNI}\"\n"
        f"  k2_gecti: \"{_K2_BANT_METNI}\"\n"
        "girdi_kimligi:\n"
        f"  degisiklik_tablosu: \"sha256 {_sha(html_bytes)}\"\n",
        encoding="utf-8")

    if trades_bozuk:
        trades_p.write_bytes(trades_bytes + b"\n// bozuldu")   # SHA256.txt artık ESKİ içeriği gösterir

    return trades_p, guncel_p, html_p, kart_p


def test_adim0_sha_uyumsuzlugunda_gecerli_false_ve_klar_none(tmp_path):
    o = _olcum()
    trades_p, guncel_p, html_p, kart_p = _girdi_dosyalarini_yaz(tmp_path, trades_bozuk=True)

    sonuc = o.olc(trades_p, guncel_p, html_p, kart_yolu=kart_p)
    assert sonuc["adim_0"]["gecerli"] is False
    assert sonuc["adim_0"]["trades_sha_esit_mi"] is False
    assert sonuc["adim_0"]["neden"] and "trades" in sonuc["adim_0"]["neden"]
    assert sonuc["k1_tohum"] is None
    assert sonuc["k1_canli"] is None
    assert sonuc["k2"] is None
    assert sonuc["pozitif_kontrol"] is None
    assert sonuc["tablo_meta"] is None


def test_adim0_sha256_txt_yoksa_gecerli_false(tmp_path):
    """`SHA256.txt` HİÇ yoksa (girdi dizini eksik/yanlış) — 'eşleşmiyor' ile 'kayıt yok' AYNI
    piksele düşer: ikisi de `gecerli=False` üretir, UYDURMA YOK (beklenen sha None kalır)."""
    o = _olcum()
    trades_p, guncel_p, html_p, kart_p = _girdi_dosyalarini_yaz(tmp_path)
    (tmp_path / "SHA256.txt").unlink()
    sonuc = o.olc(trades_p, guncel_p, html_p, kart_yolu=kart_p)
    assert sonuc["adim_0"]["gecerli"] is False
    assert sonuc["adim_0"]["trades_sha256_beklenen"] is None


def test_adim0_gecerliyse_klar_kosar(tmp_path):
    o = _olcum()
    trades_p, guncel_p, html_p, kart_p = _girdi_dosyalarini_yaz(tmp_path)
    sonuc = o.olc(trades_p, guncel_p, html_p, kart_yolu=kart_p, evren=["AAPL", "MSFT", "FERG", "ZQXX"])
    assert sonuc["adim_0"]["gecerli"] is True
    assert sonuc["k1_tohum"] is not None and sonuc["k1_tohum"]["n"] == 5
    assert sonuc["k2"] is not None
    assert sonuc["pozitif_kontrol"]["tuttu"] is True


# ==================================================================================
# (k) CLI ucu — `--olc` UÇTAN UCA (Rol-1'in koşacağı GERÇEK çağrı biçimi)
# ==================================================================================

def test_cli_olc_uctan_uca_sonuc_semasi(tmp_path):
    o = _olcum()
    trades_p, guncel_p, html_p, kart_p = _girdi_dosyalarini_yaz(tmp_path)
    cikti_p = tmp_path / "sonuc.json"

    rc = o.main(["--olc", "--trades", str(trades_p), "--guncel-liste", str(guncel_p),
                "--girdi-html", str(html_p), "--kart", str(kart_p), "--cikti", str(cikti_p),
                "--t-evren", "2022-01-01"])
    assert rc == 0
    assert cikti_p.exists()
    sonuc = json.loads(cikti_p.read_text(encoding="utf-8"))
    assert sonuc["kart"] == "TEST-EDG-079"
    assert sonuc["adim_0"]["gecerli"] is True
    assert sonuc["k1_tohum"]["n"] == 5
    assert sonuc["k1_canli"]["n"] == 1
    assert sonuc["pozitif_kontrol"]["tuttu"] is True
    assert "k2" in sonuc and sonuc["k2"] is not None       # GERÇEK REPLAY_UNIVERSE (--evren verilmedi)
    assert "esikler" in sonuc and sonuc["esikler"]["k1_gecti"]
    assert "beyan" in sonuc


def test_cli_bayrak_verilmezse_hata():
    o = _olcum()
    with pytest.raises(SystemExit):
        o.main(["--trades", "x", "--guncel-liste", "y", "--girdi-html", "z"])


def test_cli_zorunlu_bayrak_eksikse_sistem_cikisi():
    o = _olcum()
    with pytest.raises(SystemExit):
        o.main(["--olc"])           # --trades/--guncel-liste/--girdi-html eksik


# ==================================================================================
# gerçek REPLAY_UNIVERSE/SEMBOL_YENIDEN_ADLANDIRMA GERÇEKTEN meridian'dan OKUNUYOR (kopya değil)
# ==================================================================================

def test_replay_universe_ve_rename_defteri_meridiandan_okunur():
    o = _olcum()
    from meridian.adapters.data import REPLAY_UNIVERSE as gercek_evren
    from meridian.adapters.constituents import SEMBOL_YENIDEN_ADLANDIRMA as gercek_rename
    assert o.REPLAY_UNIVERSE is gercek_evren
    assert o.SEMBOL_YENIDEN_ADLANDIRMA is gercek_rename


def test_tabloyu_ayristir_ve_as_of_edg075ten_ithal_kopya_degil():
    """Tek-kaynak yasası: `tabloyu_ayristir`/`as_of` edg079'un KENDİ gövdesi DEĞİL, edg075
    modülünün AYNI fonksiyon nesnesidir (sys.path ile içe aktarım, kopya değil)."""
    o = _olcum()
    import sys as _sys
    edg075 = _sys.modules["olcum"]
    assert edg075.__file__.endswith("edg075_sp500_tarihsel/olcum.py")
    assert o.tabloyu_ayristir is edg075.tabloyu_ayristir
    assert o.as_of is edg075.as_of
