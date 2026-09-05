"""tests/test_edg076_kart_olaylari_v421.py — EDG-2026-076 ÖLÇÜM betiğinin çivisi (TSK-156, 2026-09-05,
ajan dilimi).

NE ÖLÇER. `research/olcumler/edg075_sp500_tarihsel/olcum.py` — AYNI betik, EDG-2026-076 kartı
(`EDG-2026-076-sp500-tarihsel-bilesenler-dogrulanmis-olay-kumesi.yaml`) için genişletilen dört
yeni yüzeyi doğru ölçtüğünü kanıtlar:
  (a) K1 olay kümesi ARTIK KARTTAN okunuyor (`k1_olaylari_ve_beyan`) — kart `bilinen_olaylar` YAML
      listesi taşıyorsa ORADAN (`kaynak` → `yon_kaynak`, kopyalanmadan yeniden adlandırılır),
      taşımıyorsa (EDG-075 kartı gibi) modülün sabit `BILINEN_OLAYLAR`/`KART_BEYAN_N`sine AYNEN
      düşüyor — EDG-075'in geriye dönük davranışı BOZULMADI (regresyon: gerçek EDG-076 kartı 28
      olgu taşıyor, gerçek EDG-075 kartı hiç taşımıyor — ikisi de GERÇEK dosyalardan okunuyor);
  (b) K1n (`k1n_gelecek_olaylar`) — kartın `gelecek_olaylar` listesindeki henüz yürürlüğe girmemiş
      olguları sınıyor: tabloda YÜRÜRLÜK SATIRI YOK (a=False) VE as_of(bugün) yönle TUTARLI (b=True)
      olmalı; MUTASYON: sentetik tabloya olgunun yürürlük satırı ENJEKTE edilince a=True'ya döner
      ve olgu 'geçti' olmaktan ÇIKAR (n_gecti düşer) — betiğin bu ayrımı GERÇEKTEN yaptığının kanıtı;
  (c) rename_siniri raporu (`rename_siniri_raporu`) — K DEĞİL, eşik YOK, yalnız as_of(t1)/as_of(bugün)
      eski/yeni sembol üyeliğini RAPORLAR;
  (d) kart iç tutarlılığı + `--beklenen-sha` (`kart_ic_tutarliligi`, `adim0` genişlemesi, `olc` kapısı)
      — bilinen_olaylar tarihi > bugün ya da gelecek_olaylar tarihi <= bugün İSE ya da verilen
      `--beklenen-sha` ham dosyanın GERÇEK sha256'sıyla eşleşmiyorsa `adim_0_fizibilite.gecerli=False`
      + `neden`, ve K1/K1n/K2/pozitif_kontrol KOŞMAZ (o alanlar `None` — kart 'hüküm koşulamaz'
      DEMEZ, yalnız 'burada koşulmadı, nedeni budur' der — sonuç YİNE yazılır, Yasa 6).

MUTASYON 1 (`test_MUTASYON_kart_listesi_okunmazsa_...`) ve MUTASYON 2
(`test_MUTASYON_k1n_yururluk_satiri_enjekte_edilince_...`) brief'te İSİMLENDİRİLMİŞ iki regresyon
çivisidir — v420'deki `test_MUTASYON_*` deseniyle AYNI: iki koşulu DOĞRUDAN karşılaştırıp betiğin
gerçekten ayırt ettiğini gösterirler (kaynak dosyayı geçici bozup geri almazlar — o adım bu ajanın
KENDİ doğrulama sürecinde, devir raporunda ayrıca anlatılır).

KAPSAM DIŞI: kartın hükmü (Rol-1 verir). `--cek`/`httpx` bu dosyada YOKTUR. `research/cards/`
altındaki GERÇEK kart dosyalarına bu dosya hiç YAZMAZ — yalnız OKUR (EDG-076/EDG-075 kartları) ya
da tmp_path'e KENDİ küçük sentetik kart YAML'ını yazar (K1n/rename/tutarlılık/sha testleri — gerçek
407 satırlık tarihsel sayfaya ihtiyaç duymadan, tam kontrollü sentetik tablo ile eşleşsin diye).
v420 (`tests/test_edg075_olcum_v420.py`) bu turda HİÇ DEĞİŞMEDİ, AYNEN yeşil kalmalı (regresyon)."""
from __future__ import annotations

import json
import pathlib

import pytest
import yaml

from tests.conftest import betikten_modul_yukle
from tests.test_edg075_olcum_v420 import _HTML_ROWSPAN

KOK = pathlib.Path(__file__).resolve().parents[1]
BETIK_YOLU = KOK / "research" / "olcumler" / "edg075_sp500_tarihsel" / "olcum.py"
KART_076_YOLU = KOK / "research" / "cards" / "EDG-2026-076-sp500-tarihsel-bilesenler-dogrulanmis-olay-kumesi.yaml"
KART_075_YOLU = KOK / "research" / "cards" / "EDG-2026-075-sp500-tarihsel-bilesenler-pit-kaynagi.yaml"


def _olcum():
    return betikten_modul_yukle(BETIK_YOLU, "edg076_olcum")


def _kart_076() -> dict:
    return yaml.safe_load(KART_076_YOLU.read_text(encoding="utf-8"))


# ==================================================================================
# (a) K1 olay kümesi KARTTAN — gerçek EDG-076/EDG-075 kartlarıyla
# ==================================================================================

def test_k1_olaylari_gercek_edg076_kartindan_28_olgu_okunur():
    o = _olcum()
    kart = _kart_076()
    olaylar, kart_beyan_n = o.k1_olaylari_ve_beyan(kart)
    assert len(olaylar) == 28
    assert kart_beyan_n == 28
    solv = next(x for x in olaylar if x["sembol"] == "SOLV")
    assert solv["yon"] == "giris" and solv["tarih"] == "2024-04-01"
    assert "prnewswire" in solv["yon_kaynak"]           # kart 'kaynak' alanı 'yon_kaynak'a TAŞINDI


def test_k1_olaylari_gercek_edg075_kartinda_liste_yok_geriye_donuk_14_olgu():
    o = _olcum()
    kart_075 = yaml.safe_load(KART_075_YOLU.read_text(encoding="utf-8"))
    olaylar, kart_beyan_n = o.k1_olaylari_ve_beyan(kart_075)
    assert len(olaylar) == 14 == len(o.BILINEN_OLAYLAR)
    assert kart_beyan_n == o.KART_BEYAN_N == 10
    assert olaylar == o.BILINEN_OLAYLAR


def test_k1_olaylari_liste_bos_veya_yok_ikisi_de_geriye_donuk_14():
    o = _olcum()
    olaylar_yok, n_yok = o.k1_olaylari_ve_beyan({"card_id": "X"})
    olaylar_bos, n_bos = o.k1_olaylari_ve_beyan({"card_id": "X", "bilinen_olaylar": []})
    assert len(olaylar_yok) == len(olaylar_bos) == 14
    assert n_yok == n_bos == o.KART_BEYAN_N


# ==================================================================================
# MUTASYON 1 — K1 listesi karttan GERÇEKTEN okunuyor mu (28 → 14 ayırt ediliyor mu)
# ==================================================================================

def test_MUTASYON_kart_listesi_okunmazsa_olculen_n_28den_14e_duser():
    """REGRESYON ÇİVİSİ (brief MUTASYON 1). Kartın `bilinen_olaylar` alanı SİLİNMİŞ bir kopyasıyla
    çağırmak — yani betiğin 'kart listesi okunamadı/BILINEN_OLAYLAR'a düştü' dalına AYNEN denk
    gelen girdiyle — `olculen_n`i 28'den 14'e düşürmeli. Bu iki çağrı FARKLI sonuç vermiyorsa betik
    K1'i gerçekten karttan OKUMUYOR, sabit listeye HER ZAMAN düşüyor demektir (çivi bunu ISIRIR)."""
    o = _olcum()
    kart_tam = _kart_076()
    olaylar_tam, n_tam = o.k1_olaylari_ve_beyan(kart_tam)
    kart_mutasyonlu = {k: v for k, v in kart_tam.items() if k != "bilinen_olaylar"}
    olaylar_mut, n_mut = o.k1_olaylari_ve_beyan(kart_mutasyonlu)

    degisiklikler, _ = o.tabloyu_ayristir(_HTML_ROWSPAN)
    k1_tam = o.k1_bilinen_olaylar(degisiklikler, olaylar_tam, kart_beyan_n=n_tam)
    k1_mut = o.k1_bilinen_olaylar(degisiklikler, olaylar_mut, kart_beyan_n=n_mut)

    assert k1_tam["olculen_n"] == 28
    assert k1_mut["olculen_n"] == 14, (
        "MUTASYON dalını çivi ISIRMIYOR: kart 'bilinen_olaylar' silinince hâlâ 28 dönüyor")
    assert k1_tam["olculen_n"] != k1_mut["olculen_n"]


# ==================================================================================
# (b) K1n — sentetik kart + sentetik tablo (tam kontrollü, tmp_path'e yazılan kart YAML'ı)
# ==================================================================================

_HTML_K1N_TEMEL = """
<table>
<tr><th>Date</th><th>Added</th><th>Removed</th></tr>
<tr><td>January 15, 2026</td><td>ALPHA</td><td>BETA</td></tr>
<tr><td>March 1, 2026</td><td>GAMMA</td><td>DELTA</td></tr>
</table>
"""

_HTML_K1N_ENJEKTELI = """
<table>
<tr><th>Date</th><th>Added</th><th>Removed</th></tr>
<tr><td>January 15, 2026</td><td>ALPHA</td><td>BETA</td></tr>
<tr><td>March 1, 2026</td><td>GAMMA</td><td>DELTA</td></tr>
<tr><td>September 21, 2026</td><td>FUT1</td><td></td></tr>
</table>
"""

_SENTETIK_KART_K1N = {
    "card_id": "TEST-076-K1N",
    "gelecek_olaylar": [
        {"sembol": "FUT1", "yon": "giris", "tarih": "2026-09-21", "kaynak": "test"},
        {"sembol": "FUT2", "yon": "cikis", "tarih": "2026-09-21", "kaynak": "test"},
    ],
}
_GUNCEL_UYELER_K1N = ["ALPHA", "GAMMA", "FUT2"]     # FUT1 HENÜZ üye değil, FUT2 HÂLÂ üye


def test_k1n_tabloda_yururluk_satiri_yok_ve_asof_beklenen_gibi_ise_gecer():
    o = _olcum()
    degisiklikler, _ = o.tabloyu_ayristir(_HTML_K1N_TEMEL)
    k1n = o.k1n_gelecek_olaylar(degisiklikler, _SENTETIK_KART_K1N, _GUNCEL_UYELER_K1N, "2026-09-05")
    assert k1n["calisti"] is True
    assert k1n["n"] == 2 and k1n["n_gecti"] == 2
    fut1 = next(d for d in k1n["detay"] if d["sembol"] == "FUT1")
    fut2 = next(d for d in k1n["detay"] if d["sembol"] == "FUT2")
    assert fut1["yururluk_satiri_var"] is False and fut1["as_of_beklenen_gibi"] is True and fut1["gecti"] is True
    assert fut2["yururluk_satiri_var"] is False and fut2["as_of_beklenen_gibi"] is True and fut2["gecti"] is True


def test_MUTASYON_k1n_yururluk_satiri_enjekte_edilince_olgu_kalir():
    """REGRESYON ÇİVİSİ (brief MUTASYON 2). Girdiye 2026-09-21 satırı (FUT1) ENJEKTE edilince
    `yururluk_satiri_var` True'ya döner ve olgu 'geçti' olmaktan ÇIKMALI — betiğin GERÇEKTEN
    tabloyu okuyup henüz-gerçekleşmemiş olguyu ayırt ettiğinin kanıtı (temel/enjekteli AYNI kart,
    AYNI --bugun, tek fark tablo satırı)."""
    o = _olcum()
    temel, _ = o.tabloyu_ayristir(_HTML_K1N_TEMEL)
    enjekteli, _ = o.tabloyu_ayristir(_HTML_K1N_ENJEKTELI)

    k1n_temel = o.k1n_gelecek_olaylar(temel, _SENTETIK_KART_K1N, _GUNCEL_UYELER_K1N, "2026-09-05")
    k1n_enjekteli = o.k1n_gelecek_olaylar(enjekteli, _SENTETIK_KART_K1N, _GUNCEL_UYELER_K1N, "2026-09-05")

    fut1_temel = next(d for d in k1n_temel["detay"] if d["sembol"] == "FUT1")
    fut1_enjekteli = next(d for d in k1n_enjekteli["detay"] if d["sembol"] == "FUT1")
    assert fut1_temel["yururluk_satiri_var"] is False and fut1_temel["gecti"] is True
    assert fut1_enjekteli["yururluk_satiri_var"] is True, (
        "MUTASYON dalını çivi ISIRMIYOR: enjekte edilen yürürlük satırı algılanmadı")
    assert fut1_enjekteli["gecti"] is False
    assert k1n_temel["n_gecti"] == 2
    assert k1n_enjekteli["n_gecti"] == 1, "enjeksiyon n_gecti'yi 2'den 1'e düşürmeliydi"


def test_k1n_asof_dali_cikis_sembol_asofda_yoksa_kalir():
    """(b) dalı: yon=cikis olan bir olgu as_of(bugün)'de ARTIK ÜYE DEĞİLSE (beklenenin tersi —
    sanki zaten çıkmış gibi) 'kalır' (gecti=False), UYDURULMAZ True SAYILMAZ."""
    o = _olcum()
    degisiklikler, _ = o.tabloyu_ayristir(_HTML_K1N_TEMEL)
    kart = {"gelecek_olaylar": [{"sembol": "FUT2", "yon": "cikis", "tarih": "2026-09-21", "kaynak": "t"}]}
    guncel_fut2_yok = ["ALPHA", "GAMMA"]              # FUT2 YOK — as_of(bugün) onu içermiyor
    k1n = o.k1n_gelecek_olaylar(degisiklikler, kart, guncel_fut2_yok, "2026-09-05")
    d = k1n["detay"][0]
    assert d["as_of_beklenen_gibi"] is False
    assert d["gecti"] is False


def test_k1n_yon_belirtilmeyen_olgu_None_tasir_uydurmaz_gecmez():
    o = _olcum()
    degisiklikler, _ = o.tabloyu_ayristir(_HTML_K1N_TEMEL)
    kart = {"gelecek_olaylar": [{"sembol": "FUT3", "yon": None, "tarih": "2026-09-21", "kaynak": "t"}]}
    k1n = o.k1n_gelecek_olaylar(degisiklikler, kart, ["ALPHA"], "2026-09-05")
    d = k1n["detay"][0]
    assert d["as_of_beklenen_gibi"] is None           # UYDURULMADI — ne True ne False
    assert d["gecti"] is False                        # None ISPAT SAYILMAZ, geçmez


def test_k1n_kartta_gelecek_olaylar_yoksa_calismadi_dondurur():
    o = _olcum()
    k1n = o.k1n_gelecek_olaylar([], {"card_id": "X"}, ["A"], "2026-09-05")
    assert k1n == {"calisti": False, "neden": "kartta gelecek_olaylar yok"}


def test_k1n_guncel_liste_yoksa_UYDURMAZ_calismadi_dondurur():
    o = _olcum()
    k1n = o.k1n_gelecek_olaylar([], _SENTETIK_KART_K1N, None, "2026-09-05")
    assert k1n["calisti"] is False
    assert k1n["neden"]


# ==================================================================================
# (c) rename_siniri raporu — K DEĞİL, eşik YOK, yalnız RAPOR
# ==================================================================================

def test_rename_siniri_raporu_alanlari_dolu_ve_dogru():
    o = _olcum()
    kart = {"rename_siniri": [{"eski": "OLD1", "yeni": "NEW1", "tarih": "2026-06-15", "kaynak": "t"}]}
    degisiklikler = [{"tarih": "2026-06-15", "tarih_ham": "x", "eklenen": "NEW1", "cikan": "OLD1", "neden": None}]
    guncel = ["NEW1"]
    rapor = o.rename_siniri_raporu(degisiklikler, kart, guncel, "2026-06-01", "2026-09-05")
    assert rapor["calisti"] is True
    d = rapor["detay"][0]
    assert d["eski"] == "OLD1" and d["yeni"] == "NEW1" and d["tarih"] == "2026-06-15"
    assert d["as_of_t1_eski_var"] is True and d["as_of_t1_yeni_var"] is False    # t1 < rename: hâlâ OLD1
    assert d["as_of_bugun_eski_var"] is False and d["as_of_bugun_yeni_var"] is True  # bugün > rename: NEW1


def test_rename_siniri_raporu_kartta_yoksa_calismadi_dondurur():
    o = _olcum()
    rapor = o.rename_siniri_raporu([], {"card_id": "X"}, ["A"], "2026-06-01", "2026-09-05")
    assert rapor == {"calisti": False, "neden": "kartta rename_siniri yok"}


# ==================================================================================
# (d) kart iç tutarlılığı + --beklenen-sha — `olc()` uçtan uca, sentetik kart tmp_path'e yazılarak
# ==================================================================================

def _sentetik_kart_yaz(tmp_path: pathlib.Path, **ek) -> pathlib.Path:
    kart = {
        "card_id": "TEST-076-TUTARLILIK",
        "esikler": {"k1_gecti": "x", "k1n_gecti": "y", "k2_gecti": "z"},
        "bilinen_olaylar": [{"sembol": "ALPHA", "yon": "giris", "tarih": "2026-01-15", "kaynak": "t"}],
        **ek,
    }
    yol = tmp_path / "kart_sentetik.yaml"
    yol.write_text(yaml.safe_dump(kart, allow_unicode=True), encoding="utf-8")
    return yol


def test_kart_ic_tutarliligi_gecerli_normal_durumda():
    o = _olcum()
    kart = {"bilinen_olaylar": [{"sembol": "A", "tarih": "2026-01-01"}],
            "gelecek_olaylar": [{"sembol": "B", "tarih": "2026-09-21"}]}
    t = o.kart_ic_tutarliligi(kart, "2026-09-05")
    assert t["gecerli"] is True and t["ihlaller"] == []


def test_kart_ic_tutarliligi_gelecek_tarih_bugunden_once_ise_ihlal():
    o = _olcum()
    kart = {"gelecek_olaylar": [{"sembol": "B", "tarih": "2026-09-05"}]}   # tarih == bugün, > OLMALIYDI
    t = o.kart_ic_tutarliligi(kart, "2026-09-05")
    assert t["gecerli"] is False
    assert t["ihlaller"]


def test_kart_ic_tutarliligi_bilinen_tarih_bugunden_sonra_ise_ihlal():
    o = _olcum()
    kart = {"bilinen_olaylar": [{"sembol": "A", "tarih": "2026-09-06"}]}   # bugünden SONRA
    t = o.kart_ic_tutarliligi(kart, "2026-09-05")
    assert t["gecerli"] is False
    assert t["ihlaller"]


def test_olc_kart_ic_tutarsizsa_gecerli_false_ve_klar_none(tmp_path):
    o = _olcum()
    kart_yolu = _sentetik_kart_yaz(tmp_path, gelecek_olaylar=[{"sembol": "B", "yon": "giris", "tarih": "2026-09-05", "kaynak": "t"}])
    kart = yaml.safe_load(kart_yolu.read_text(encoding="utf-8"))
    esikler = o.esikleri_karttan_oku(kart_yolu)
    girdi_kimligi = {"oldid": 1, "html_sha256_tam": "x" * 64, "ham_yol": "x"}

    sonuc = o.olc(_HTML_ROWSPAN, esikler, girdi_kimligi, ["ALPHA"], kart, bugun="2026-09-05")

    assert sonuc["adim_0_fizibilite"]["gecerli"] is False
    assert sonuc["adim_0_fizibilite"]["neden"]
    assert sonuc["k1_bilinen_olaylar"] is None
    assert sonuc["k1n_gelecek_olaylar"] is None
    assert sonuc["k2_as_of_yeniden_kurulum"] is None
    assert sonuc["pozitif_kontrol"] is None


def test_olc_esikler_k1n_gecti_karttan_gecirilir(tmp_path):
    o = _olcum()
    kart_yolu = _sentetik_kart_yaz(tmp_path)
    esikler = o.esikleri_karttan_oku(kart_yolu)
    assert esikler["k1n_gecti"] == "y"
    assert esikler["k1_gecti"] == "x" and esikler["k2_gecti"] == "z"


def test_olc_beklenen_sha_yanlissa_gecerli_false(tmp_path):
    o = _olcum()
    kart_yolu = _sentetik_kart_yaz(tmp_path, bilinen_olaylar=[{"sembol": "ALPHA", "yon": "giris", "tarih": "2026-01-15", "kaynak": "t"}])
    kart = yaml.safe_load(kart_yolu.read_text(encoding="utf-8"))
    esikler = o.esikleri_karttan_oku(kart_yolu)
    girdi_kimligi = {"oldid": 1, "html_sha256_tam": "irrelevant", "ham_yol": "x"}

    sonuc = o.olc(_HTML_ROWSPAN, esikler, girdi_kimligi, ["ALPHA"], kart, bugun="2026-09-05",
                 beklenen_sha="0" * 64)

    assert sonuc["adim_0_fizibilite"]["e_sha_esit_mi"] is False
    assert sonuc["adim_0_fizibilite"]["gecerli"] is False
    assert sonuc["adim_0_fizibilite"]["neden"]
    assert sonuc["k1_bilinen_olaylar"] is None


def test_olc_beklenen_sha_dogruysa_koşar(tmp_path):
    import hashlib
    o = _olcum()
    kart_yolu = _sentetik_kart_yaz(tmp_path, bilinen_olaylar=[{"sembol": "ALPHA", "yon": "giris", "tarih": "2026-01-15", "kaynak": "t"}])
    kart = yaml.safe_load(kart_yolu.read_text(encoding="utf-8"))
    esikler = o.esikleri_karttan_oku(kart_yolu)
    girdi_kimligi = {"oldid": 1, "html_sha256_tam": "x", "ham_yol": "x"}
    dogru_sha = hashlib.sha256(_HTML_ROWSPAN.encode("utf-8")).hexdigest()

    sonuc = o.olc(_HTML_ROWSPAN, esikler, girdi_kimligi, ["ALPHA"], kart, bugun="2026-09-05",
                 beklenen_sha=dogru_sha)

    assert sonuc["adim_0_fizibilite"]["e_sha_esit_mi"] is True
    assert sonuc["adim_0_fizibilite"]["gecerli"] is True
    assert sonuc["k1_bilinen_olaylar"] is not None
    assert sonuc["k1_bilinen_olaylar"]["olculen_n"] == 1


def test_olc_beklenen_sha_verilmezse_e_sha_esit_mi_None_uydurmaz(tmp_path):
    o = _olcum()
    kart_yolu = _sentetik_kart_yaz(tmp_path)
    kart = yaml.safe_load(kart_yolu.read_text(encoding="utf-8"))
    esikler = o.esikleri_karttan_oku(kart_yolu)
    girdi_kimligi = {"oldid": 1, "html_sha256_tam": "x", "ham_yol": "x"}
    sonuc = o.olc(_HTML_ROWSPAN, esikler, girdi_kimligi, ["ALPHA"], kart, bugun="2026-09-05")
    assert sonuc["adim_0_fizibilite"]["e_sha_esit_mi"] is None
    assert sonuc["adim_0_fizibilite"]["gecerli"] is True


# ==================================================================================
# v420 regresyon — AYNEN yeşil kalmalı (bu dosyada AYRICA çağrılarak, tam suite koşumu Rol-1'e ait)
# ==================================================================================

def test_cli_olc_uctan_uca_edg076_kartiyla_k1n_ve_rename_alanlari_da_var(tmp_path):
    """CLI ucu — `--olc --kart <EDG-076> --beklenen-sha <girdi hash'i>` gerçek çağrı biçiminde
    (Rol-1'in koşacağı komutun ŞEKLİ, gerçek ham dosya OLMADAN — sentetik fikstür kullanılır)."""
    import hashlib
    o = _olcum()
    girdi = tmp_path / "999_deadbeefdeadbeef.html"
    girdi.write_text(_HTML_ROWSPAN, encoding="utf-8")
    cikti = tmp_path / "sonuc.json"
    dogru_sha = hashlib.sha256(_HTML_ROWSPAN.encode("utf-8")).hexdigest()

    rc = o.main(["--olc", "--girdi", str(girdi), "--kart", str(KART_076_YOLU),
                "--bugun", "2026-09-05", "--beklenen-sha", dogru_sha, "--cikti", str(cikti)])
    assert rc == 0
    sonuc = json.loads(cikti.read_text(encoding="utf-8"))
    assert sonuc["kart"] == "EDG-2026-076"
    assert sonuc["k1_bilinen_olaylar"]["olculen_n"] == 28
    assert sonuc["k1_bilinen_olaylar"]["kart_beyan_n"] == 28
    # --guncel-liste verilmedi → k1n/rename UYDURMAZ, "calisti":False + neden ile döner (anahtar
    # YİNE VAR, Yasa 6) — bu test yalnız CLI KABLOLAMASINI (yeni alanların şemada bulunduğunu) sınar.
    assert "k1n_gelecek_olaylar" in sonuc and sonuc["k1n_gelecek_olaylar"]["calisti"] is False
    assert "rename_siniri_raporu" in sonuc and sonuc["rename_siniri_raporu"]["calisti"] is False
    assert sonuc["adim_0_fizibilite"]["e_sha_esit_mi"] is True
    assert "esikler" in sonuc and sonuc["esikler"]["k1n_gecti"]
