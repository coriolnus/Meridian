"""tests/test_edg092_sp400_olcum_v484.py — EDG-2026-092 ölçüm aracının çivileri.

vNNN KİMLİK KAYDI: v484 seçildi çünkü ölçüm anında (2026-09-14) `tests/` altındaki en yüksek
numara v483 (`test_geridolum_ileri_dolum_v483.py`) idi ve v484 BOŞTU — çakışma yok, taşıma yok.

NE ÇİVİLER (brief EDG-2026-092, madde 5):
  (1) WİKİTEXT AYRIŞTIRICI: çok satırlı hücre · `[[Ad|Görünen]]` · `<ref>…</ref>` temizleme ·
      "Month D, YYYY" tarih · veri satırında `rowspan` ile tarih devralma · çözülemeyen tarihin
      ADIYLA raporlanması · tablonun `id`ye DEĞİL BAŞLIK SÜTUNLARINA göre bulunması (Rol-1 notu:
      S&P 500 sayfasında `id="changes"` var ama S&P 400 dışındaki sayfalarda olmayabilir; ayrıca
      ayrıştırıcı `Date` ve `Effective Date` başlıklarının İKİSİNİ de tanımalı).
  (2) K1 sentetik: bulundu · bulunamadı · ±1 iş günü toleransı (Cuma→Pazartesi köprüsü).
  (3) PK-1 (gelecek olay) negatif kontrolü: yürürlük satırı TABLODA görünürse olgu DÜŞER.
  (4) PK-2 rename raporu: kartın `rename_vakalari` tarihlerinde tablo satırları + as_of davranışı
      RAPORLANIR; yeniden-adlandırma bir ÜYELİK DEĞİŞİKLİĞİ olarak SAYILMAZ.
  (5) MDY xlsx okuyucusu (stdlib `zipfile` — openpyxl venv'de YOK, ölçüldü 2026-09-14): nakit satırı
      (`CASH_USD`) beyanla dışarıda kalır.
  (6) `kart_beyan_n != olculen_n` AYRIŞMA çivisi (EDG-076 deseni).
  (7) `--beklenen-sha` uyuşmazlığında çıkış kodu 2 ve K1/PK'lerin KOŞMAMASI.
  (8) Kill-list #5: PK'lerden biri düşerse `yayin_engeli` açılır ve markdown raporda K1 kapsama
      SAYISI YAYILMAZ.
  (9) TEK-KAYNAK ayrışma çivisi: `olc` modülünün K1/as_of/tarih/sembol yardımcıları EDG-075
      betiğinden İTHAL edilir — KOPYA DEĞİL (aynı fonksiyon nesnesi).

DİSİPLİN: çiviler yalnız SENTETİK fikstürlerle koşar (ağ yok, gerçek ham girdi yok); gerçek koşum
Rol-1'in okuyacağı `sonuc_*.json` + `rapor_*.md`de. Mutasyon kanıtı devir raporunda.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import importlib.util
import json
import pathlib
import sys
import zipfile

import pytest

KOK = pathlib.Path(__file__).resolve().parents[1]
OLC_YOLU = KOK / "research" / "olcumler" / "edg092_sp400_uyelik" / "olc.py"


def _modul():
    """Ölçüm aracını DOSYA YOLUNDAN yükler (research/ altı paket değil — edg075 betiği de öyle)."""
    spec = importlib.util.spec_from_file_location("edg092_olc_test", OLC_YOLU)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["edg092_olc_test"] = mod
    spec.loader.exec_module(mod)
    return mod


olc = _modul()


# ======================================================================================
# SENTETİK FİKSTÜRLER
# ======================================================================================

WIKI_MINI = """Giriş düzyazısı — tablo DEĞİL.

{|  class="wikitable sortable" id="changes"
|-
! rowspan="2" | Date
! colspan="2" | Added
! colspan="2" | Removed
! rowspan="2" | Reason
|-
! Ticker || Security ||  Ticker ||  Security
|-
|August 20, 2026 || AAA || [[Alpha Corporation]] || BBB || [[Beta Inc]] || Beta satın alındı.<ref>{{cite web |url=https://example.org/a.pdf |title=A}}</ref>
|-
| rowspan=2 | July 1, 2026
|CCC
|[[Gamma Holdings|Gamma]]
|DDD
|Delta Co.
|Piyasa değeri değişimi.<ref name="r1">{{cite web |url=https://example.org/b.pdf}}
</ref>
|-
| EEE || [[Epsilon]] || FFF || [[Zeta]] || Piyasa değeri değişimi.<ref name="r1" />
|-
|çözülemez-tarih || GGG || [[Eta]] || HHH || [[Theta]] || Tarihi ayrıştırılamayan satır
|-
|}
"""

# `id` YOK, başlık "Effective Date" — ayrıştırıcı tabloyu BAŞLIKTAN tanımalı (Rol-1 notu).
# ÖNÜNE hedef OLMAYAN bir tablo konur (gerçek sayfalarda "constituents" tablosu önce gelir):
# "ilk tabloyu al" ya da "id'ye çivile" diyen bir ayrıştırıcı bu fikstürde DÜŞER.
WIKI_IDSIZ = """{| class="wikitable sortable" id="constituents"
|-
! Symbol !! Security !! GICS Sector
|-
| AAPL || [[Apple Inc.]] || Information Technology
|-
| MSFT || [[Microsoft]] || Information Technology
|-
|}

{| class="wikitable sortable"
|-
! data-sort-type="date" rowspan="2" | Effective Date
! colspan="2" | Added
! colspan="2" | Removed
! rowspan="2" | Reason
! rowspan="2" | Refs
|-
! Ticker || Security || Ticker || Security
|-
|| August 5, 2026
|| KKK
|| [[Kappa]]
|| LLL
|| [[Lambda]]
|| Değişim
|| <ref>{{cite web |url=https://example.org/c.pdf}}</ref>
|-
|}
"""

KART_MINI = {
    "card_id": "EDG-TEST-092",
    "esikler": {
        "bilinen_olay_kapsama_alt": 0.90,
        "bilinen_olay_n_alt": 2,
        "pencere_satir_alt": 2,
        "guncel_liste_kesisim_alt": 0.98,
    },
    "veri_penceresi": "2020-07-27 → ölçüm günü",
    "bilinen_olaylar": [
        {"sembol": "AAA", "yon": "giris", "tarih": "2026-08-20", "url": "https://example.org/a.pdf"},
        {"sembol": "BBB", "yon": "cikis", "tarih": "2026-08-20", "url": "https://example.org/a.pdf"},
    ],
    "gelecek_olaylar": [
        {"sembol": "XXX", "yon": "giris", "tarih": "2026-09-21", "url": "https://example.org/z"},
        {"sembol": "AAA", "yon": "cikis", "tarih": "2026-09-21", "url": "https://example.org/z"},
    ],
    "rename_vakalari": [
        {"tarih": "2026-07-01", "not": "Delta Co. birleşti, birleşik şirket DYN adını aldı — tablo satırı CCC↑ DDD↓; DZZ→DYN bir ÜYELİK değişikliği DEĞİL"},
    ],
}


def _kart_yaz(tmp_path: pathlib.Path, kart: dict) -> pathlib.Path:
    import yaml
    yol = tmp_path / "kart.yaml"
    yol.write_text(yaml.safe_dump(kart, allow_unicode=True), encoding="utf-8")
    return yol


def _xlsx_yaz(tmp_path: pathlib.Path, satirlar: list[tuple[str, str]]) -> pathlib.Path:
    """Asgari xlsx: yalnız `xl/sharedStrings.xml` + `xl/worksheets/sheet1.xml` (okuyucunun okuduğu
    iki parça). Gerçek MDY dosyasının şeması: 5. satır başlık (Name·Ticker·…), veri 6'dan itibaren."""
    basliklar = [("Fund Name:", "MDY"), ("Ticker Symbol:", "MDY"), ("Holdings:", "As of 10-Sep-2026"),
                 ("", ""), ("Name", "Ticker")]
    hepsi = basliklar + satirlar
    havuz: list[str] = []
    for a, b in hepsi:
        for v in (a, b):
            if v not in havuz:
                havuz.append(v)
    ss = ('<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" count="%d">' % len(havuz)
          + "".join(f"<si><t>{v}</t></si>" for v in havuz) + "</sst>")
    hucreler = []
    for i, (a, b) in enumerate(hepsi, start=1):
        hucreler.append(
            f'<row r="{i}"><c r="A{i}" t="s"><v>{havuz.index(a)}</v></c>'
            f'<c r="B{i}" t="s"><v>{havuz.index(b)}</v></c></row>')
    sheet = ('<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>'
             + "".join(hucreler) + "</sheetData></worksheet>")
    yol = tmp_path / "mdy.xlsx"
    with zipfile.ZipFile(yol, "w") as z:
        z.writestr("xl/sharedStrings.xml", ss)
        z.writestr("xl/worksheets/sheet1.xml", sheet)
    return yol


# ======================================================================================
# (1) WİKİTEXT AYRIŞTIRICI
# ======================================================================================

def test_wikitext_cok_satirli_hucre_ve_link_ve_ref():
    degisiklikler, meta = olc.tabloyu_ayristir(WIKI_MINI)
    assert meta["eslenen"]["tarih"] == "Date"
    assert meta["eslenen"]["eklenen_ticker"] == "Added_Ticker"
    assert meta["eslenen"]["cikan_ticker"] == "Removed_Ticker"
    ccc = [r for r in degisiklikler if r["eklenen"] == "CCC"]
    assert len(ccc) == 1, "çok satırlı hücreli satır ayrıştırılamadı"
    assert ccc[0]["cikan"] == "DDD"
    assert ccc[0]["eklenen_ad"] == "Gamma", "[[Ad|Görünen]] görünen adı alınmalı"
    assert "<ref" not in (ccc[0]["neden"] or ""), "ref temizlenmedi"
    assert ccc[0]["neden"] == "Piyasa değeri değişimi."
    assert "https://example.org/b.pdf" in ccc[0]["urller"]


def test_wikitext_tarih_ve_rowspan_devralma():
    degisiklikler, _ = olc.tabloyu_ayristir(WIKI_MINI)
    tarihler = {r["eklenen"]: r["tarih"] for r in degisiklikler}
    assert tarihler["AAA"] == "2026-08-20", "'August 20, 2026' ISO'ya çevrilmedi"
    assert tarihler["CCC"] == "2026-07-01"
    assert tarihler["EEE"] == "2026-07-01", "rowspan'lı tarih hücresi ikinci satıra devralınmadı"
    assert tarihler["GGG"] is None, "çözülemeyen tarih None olmalı (uydurma yasağı)"


def test_adim0_cozulemeyen_tarihi_adiyla_raporlar():
    a0 = olc.adim0(WIKI_MINI, {"ham_yol": "x", "sha256": "y"}, kart=KART_MINI, bugun="2026-09-14")
    adlar = [k["eklenen"] for k in a0["tarih_cozulemeyen_satirlar"]]
    assert "GGG" in adlar, "çözülemeyen tarih satırı ADIYLA raporlanmadı"
    assert a0["tarih_cozulemeyen_n"] == 1
    assert a0["pencere_satir_n"] == 3
    assert a0["pencere_satir_yeterli"] is True   # kart eşiği 2


def test_tablo_idye_civilenmemis_baslik_sutunlarindan_bulunur():
    """Rol-1 notu: S&P 500 tarihsel sayfasının tablosu `id`ye göre DEĞİL, başlıklara göre bulunmalı;
    'Effective Date' de 'Date' gibi tanınmalı."""
    degisiklikler, meta = olc.tabloyu_ayristir(WIKI_IDSIZ)
    assert meta["eslenen"]["tarih"] == "Effective_Date"
    assert [r["eklenen"] for r in degisiklikler] == ["KKK"]
    assert degisiklikler[0]["tarih"] == "2026-08-05"
    assert degisiklikler[0]["cikan"] == "LLL"


def test_hayalet_satir_atlanir():
    hayaletli = WIKI_MINI.replace("|çözülemez-tarih", "|\n|\n|\n|\n|\n|\n|-\n|çözülemez-tarih")
    degisiklikler, meta = olc.tabloyu_ayristir(hayaletli)
    assert meta["hayalet_atlanan_n"] >= 1
    assert all(r["eklenen"] or r["cikan"] or r["tarih_ham"] or r["neden"] for r in degisiklikler)


WIKI_REF = """{| class="wikitable sortable"
|-
! rowspan="2" | Date
! colspan="2" | Added
! colspan="2" | Removed
! rowspan="2" | Reason
|-
! Ticker || Security || Ticker || Security
|-
|March 2, 2026 || MMM || [[Mu]] || NNN || [[Nu]] || Gerçek gerekçe.<ref>REF İÇİ DÜZ METİN {{cite web |url=https://example.org/r.pdf |title=Alfa || Beta}}</ref>
|-
|}
"""


def test_ref_metni_nedene_sizmaz_url_saklanir():
    """`<ref>` bloğu METİNDEN ÇIKAR (içindeki düz metin gerekçeye SIZMAZ) ama `url=` adresi
    SAKLANIR — kaynaksız satır sayısı ölçülebilsin diye (sessizce atmak Yasa 4 ihlali olurdu)."""
    degisiklikler, _ = olc.tabloyu_ayristir(WIKI_REF)
    assert len(degisiklikler) == 1
    r = degisiklikler[0]
    assert r["neden"] == "Gerçek gerekçe.", "ref içindeki düz metin gerekçeye sızdı"
    assert "REF İÇİ DÜZ METİN" not in (r["neden"] or "")
    assert r["urller"] == ["https://example.org/r.pdf"]


def test_hucre_bolme_sablon_icindeki_ayiraci_bolmez():
    """`{{…}}` İÇİNDEKİ `||` hücre sınırı DEĞİLDİR — derinlik duyarsız bir bölücü bu satırı
    fazladan hücreye böler ve sütun hizası kayar."""
    assert olc.derinlik_bol("a || {{x |t=A || B}} || c", "||") == ["a ", " {{x |t=A || B}} ", " c"]
    degisiklikler, _ = olc.tabloyu_ayristir(WIKI_REF)
    r = degisiklikler[0]
    assert (r["eklenen"], r["cikan"]) == ("MMM", "NNN"), "şablon içi `||` sütun hizasını kaydırdı"
    assert r["tarih"] == "2026-03-02"


# ======================================================================================
# (2) K1 SENTETİK
# ======================================================================================

def test_k1_bulundu_bulunamadi_ve_is_gunu_toleransi():
    degisiklikler, _ = olc.tabloyu_ayristir(WIKI_MINI)
    olaylar = [
        {"sembol": "AAA", "yon": "giris", "tarih": "2026-08-20", "yon_kaynak": "t"},   # birebir
        {"sembol": "CCC", "yon": "giris", "tarih": "2026-06-30", "yon_kaynak": "t"},   # 1 iş günü önce
        {"sembol": "YOK", "yon": "giris", "tarih": "2026-08-20", "yon_kaynak": "t"},   # tabloda yok
        {"sembol": "BBB", "yon": "giris", "tarih": "2026-08-20", "yon_kaynak": "t"},   # yön YANLIŞ
    ]
    k1 = olc.k1_kapsama(degisiklikler, olaylar, kart_beyan_n=4)
    d = {x["sembol"]: x for x in k1["detay"]}
    assert d["AAA"]["satir_var"] and d["AAA"]["tarih_tolerans_icinde"] and d["AAA"]["yon_dogru"] is True
    assert d["CCC"]["tarih_tolerans_icinde"] is True, "±1 iş günü toleransı tutmadı"
    assert d["YOK"]["satir_var"] is False
    assert d["BBB"]["yon_dogru"] is False
    assert k1["olculen_n"] == 4 and k1["n_tam_gecti"] == 2
    assert k1["kapsama_orani"] == pytest.approx(0.5)


def test_k1_hafta_sonu_koprusu_bir_is_gunu():
    """2026-08-20 Perşembe; 2026-08-21 Cuma = 1 iş günü. Cuma→Pazartesi köprüsü de 1 iş günüdür,
    takvim günü DEĞİL — `_is_gunu_farki_icinde` (EDG-075'ten İTHAL) bunu ölçer."""
    assert olc.ORTAK._is_gunu_farki_icinde("2026-08-21", "2026-08-24", 1) is True   # Cu→Pzt
    assert olc.ORTAK._is_gunu_farki_icinde("2026-08-20", "2026-08-24", 1) is False  # Pe→Pzt = 2


def test_k1_kart_beyan_ayrismasi():
    """`kart_beyan_n != olculen_n` AYRIŞMA olarak işaretlenir (EDG-076 deseni) — betik hiçbir
    tarafı ZORLAMAZ."""
    degisiklikler, _ = olc.tabloyu_ayristir(WIKI_MINI)
    olaylar = [{"sembol": "AAA", "yon": "giris", "tarih": "2026-08-20", "yon_kaynak": "t"}]
    assert olc.k1_kapsama(degisiklikler, olaylar, kart_beyan_n=1)["beyan_ayrismasi"] is False
    ayrisan = olc.k1_kapsama(degisiklikler, olaylar, kart_beyan_n=54)
    assert ayrisan["beyan_ayrismasi"] is True
    assert ayrisan["olculen_n"] == 1 and ayrisan["kart_beyan_n"] == 54


# ======================================================================================
# (3) PK-1 — GELECEK OLAY NEGATİF KONTROLÜ
# ======================================================================================

def test_pk1_gelecek_olay_tabloda_gorunurse_duser():
    degisiklikler, _ = olc.tabloyu_ayristir(WIKI_MINI)
    uyeler = ["CCC", "EEE", "AAA", "ZZZ"]
    temiz = olc.pk1_gelecek_olaylar(degisiklikler, KART_MINI, uyeler, "2026-09-14")
    assert temiz["calisti"] is True and temiz["n"] == 2 and temiz["n_gecti"] == 2
    assert temiz["tuttu"] is True

    kirli = dict(KART_MINI)
    kirli["gelecek_olaylar"] = [{"sembol": "AAA", "yon": "giris", "tarih": "2026-08-20"}]
    dusen = olc.pk1_gelecek_olaylar(degisiklikler, kirli, uyeler, "2026-09-14")
    assert dusen["detay"][0]["yururluk_satiri_var"] is True
    assert dusen["n_gecti"] == 0 and dusen["tuttu"] is False


# ======================================================================================
# (4) PK-2 — RENAME RAPORU
# ======================================================================================

def test_pk2_rename_raporu_as_of_ve_degisiklik_saymama():
    degisiklikler, _ = olc.tabloyu_ayristir(WIKI_MINI)
    uyeler = ["CCC", "EEE", "AAA", "DYN"]
    rapor = olc.pk2_rename_raporu(degisiklikler, KART_MINI, uyeler, "2026-09-14")
    assert rapor["calisti"] is True
    vaka = rapor["detay"][0]
    assert vaka["tarih"] == "2026-07-01"
    assert {r["eklenen"] for r in vaka["tablodaki_satirlar"]} == {"CCC", "EEE"}
    # kartın KENDİ işaretleri okunur: `X↑ Y↓` beklenen satır, `X→Y` yeniden-adlandırma çifti
    assert vaka["beklenen_satir"] == {"eklenen": "CCC", "cikan": "DDD"}
    assert vaka["beklenen_satir_var"] is True
    assert vaka["rename_cifti"] == {"eski": "DZZ", "yeni": "DYN"}
    assert vaka["rename_degisiklik_olarak_kitaplandi"] is False
    assert vaka["rename_cifti_as_of"]["yeni_as_of_bugun_uye_mi"] is True
    assert vaka["gecti"] is True and rapor["tuttu"] is True
    semboller = {s["sembol"]: s for s in vaka["not_sembolleri"]}
    assert "DYN" in semboller, "kart notundaki sembol raporlanmadı"
    assert semboller["DYN"]["satirda_var_mi"] is False
    assert vaka["eski_yeni_ayrimi"] is None, "kartta eski/yeni ALANI yok — etiketlenmemeli"


def test_pk2_rename_cifti_kitaplanmissa_duser():
    """`X→Y` çiftinin bir ucu o tarihte eklenen/çıkan olarak yazılıysa yeniden adlandırma ÜYELİK
    DEĞİŞİKLİĞİ olarak kitaplanmıştır — vaka DÜŞER."""
    degisiklikler, _ = olc.tabloyu_ayristir(WIKI_MINI)
    kirli = dict(KART_MINI)
    kirli["rename_vakalari"] = [{"tarih": "2026-07-01",
                                 "not": "tablo satırı CCC↑ DDD↓; DDD→DYN üyelik değişikliği DEĞİL"}]
    rapor = olc.pk2_rename_raporu(degisiklikler, kirli, ["CCC", "EEE"], "2026-09-14")
    assert rapor["detay"][0]["rename_degisiklik_olarak_kitaplandi"] is True
    assert rapor["detay"][0]["gecti"] is False and rapor["tuttu"] is False


def test_pk2_beklenen_satir_yoksa_duser():
    degisiklikler, _ = olc.tabloyu_ayristir(WIKI_MINI)
    kirli = dict(KART_MINI)
    kirli["rename_vakalari"] = [{"tarih": "2026-07-01", "not": "tablo satırı QQQ↑ RRR↓"}]
    rapor = olc.pk2_rename_raporu(degisiklikler, kirli, ["CCC"], "2026-09-14")
    assert rapor["detay"][0]["beklenen_satir_var"] is False
    assert rapor["tuttu"] is False


def test_pk2_gerekce_taramasi_kapi_degil_rapor():
    """ÖLÇÜLMÜŞ YANLIŞ-POZİTİF (2026-09-14): gerçek bir üyelik değişikliğinin gerekçesinde
    'renamed' geçebilir — gerekçe metni KAPI olamaz, yalnız RAPORdur."""
    renameli = WIKI_MINI.replace("Beta satın alındı.", "Beta renamed itself; ticker change.")
    degisiklikler, _ = olc.tabloyu_ayristir(renameli)
    rapor = olc.pk2_rename_raporu(degisiklikler, KART_MINI, ["AAA", "CCC", "EEE", "DYN"], "2026-09-14")
    bulunan = rapor["yeniden_adlandirma_gerekceli_satirlar"]
    assert [r["eklenen"] for r in bulunan] == ["AAA"]
    assert rapor["yeniden_adlandirma_gerekceli_n"] == 1
    assert rapor["gerekce_taramasi_kapi_mi"] is False
    assert rapor["tuttu"] is True, "gerekçe metni tek başına PK-2'yi DÜŞÜREMEZ"


# ======================================================================================
# (5) MDY XLSX OKUYUCU
# ======================================================================================

def test_mdy_okuyucu_nakit_satirini_beyanla_eler(tmp_path):
    yol = _xlsx_yaz(tmp_path, [("Alpha Corporation", "AAA"), ("U.S. Dollar", "CASH_USD"),
                               ("Gamma Holdings", "CCC")])
    tickerlar, meta = olc.mdy_tickerlari(yol)
    assert tickerlar == ["AAA", "CCC"]
    assert meta["haric_tutulan"] == ["CASH_USD"]
    assert meta["haric_gerekcesi"]
    assert meta["ham_satir_n"] == 3 and meta["as_of"] == "As of 10-Sep-2026"


def test_pk3_kesisim_ve_tautoloji_beyani(tmp_path):
    degisiklikler, _ = olc.tabloyu_ayristir(WIKI_MINI)
    pk3 = olc.pk3_guncel_liste(degisiklikler, ["AAA", "CCC", "EEE"], 0.98, "2026-09-14")
    assert pk3["kesisim_orani"] == pytest.approx(1.0)
    assert pk3["tuttu"] is True
    assert pk3["tautoloji"]["liste_sonrasi_degisiklik_n"] == 0
    assert "tohum" in pk3["tautoloji"]["beyan"].lower()
    # tanı: her satır 1-giren/1-çıkan ise as_of pencere başında da aynı büyüklük olmalı
    assert pk3["tani"]["as_of_pencere_basi_n"] == 3


# ======================================================================================
# (7) --beklenen-sha KAPISI
# ======================================================================================

def test_beklenen_sha_uyusmazliginda_cikis_2_ve_olcum_kosmaz(tmp_path):
    girdi = tmp_path / "sp400.wiki"
    girdi.write_text(WIKI_MINI, encoding="utf-8")
    kart = _kart_yaz(tmp_path, KART_MINI)
    cikti = tmp_path / "cikti"
    rc = olc.main(["--girdi", str(girdi), "--kart", str(kart), "--bugun", "2026-09-14",
                   "--cikti-dizin", str(cikti), "--beklenen-sha", "0" * 64])
    assert rc == 2, "sha uyuşmazlığı çıkış 2 vermeli"
    sonuclar = list(cikti.glob("sonuc_*.json"))
    assert len(sonuclar) == 1, "sonuç YİNE yazılmalı (Yasa 6) — yalnız ölçüm koşmaz"
    s = json.loads(sonuclar[0].read_text(encoding="utf-8"))
    assert s["adim0"]["gecerli"] is False
    assert s["k1"] is None and s["pk1"] is None and s["pk3"] is None
    assert "beklenen-sha" in s["adim0"]["neden"]


def test_beklenen_sha_dogruysa_olcum_kosar(tmp_path):
    girdi = tmp_path / "sp400.wiki"
    girdi.write_text(WIKI_MINI, encoding="utf-8")
    sha = hashlib.sha256(girdi.read_bytes()).hexdigest()
    kart = _kart_yaz(tmp_path, KART_MINI)
    cikti = tmp_path / "cikti"
    mdy = _xlsx_yaz(tmp_path, [("Alpha Corporation", "AAA"), ("Gamma", "CCC"), ("Epsilon", "EEE")])
    rc = olc.main(["--girdi", str(girdi), "--kart", str(kart), "--bugun", "2026-09-14",
                   "--cikti-dizin", str(cikti), "--beklenen-sha", sha,
                   "--guncel-liste", str(mdy)])
    assert rc == 0
    s = json.loads(list(cikti.glob("sonuc_*.json"))[0].read_text(encoding="utf-8"))
    assert s["adim0"]["gecerli"] is True
    assert s["k1"]["olculen_n"] == 2
    assert s["hukum"] == "YOK — Rol-1"
    assert s["esikler"]["bilinen_olay_kapsama_alt"] == 0.90


# ======================================================================================
# (8) KILL-LIST #5 — PK DÜŞERSE KAPSAMA YAYILMAZ
# ======================================================================================

def test_pk_duserse_yayin_engeli_ve_kapsama_raporda_yok():
    """PK-2 DÜŞÜRÜLÜR: kartın `X→Y` yeniden-adlandırma çifti o tarihte eklenen/çıkan olarak
    kitaplanmış — yani kaynak rename'i üyelik değişikliği gibi yazmış."""
    kirli = dict(KART_MINI)
    kirli["rename_vakalari"] = [{"tarih": "2026-08-20",
                                 "not": "tablo satırı AAA↑ BBB↓; AAA→BBB üyelik değişikliği DEĞİL"}]
    sonuc = olc.olc(WIKI_MINI, kirli, {"ham_yol": "x"}, ["AAA", "CCC", "EEE"],
                    bugun="2026-09-14", pk4=None)
    assert sonuc["pk2"]["tuttu"] is False
    assert sonuc["yayin_engeli"]["engel"] is True
    assert any("PK-2" in n for n in sonuc["yayin_engeli"]["neden"])
    assert sonuc["k1_kapsama_yayinlanabilir"] is None
    rapor = olc.rapor_markdown(sonuc)
    assert "YAYIN ENGELİ" in rapor
    assert "KAPSAMA ORANI:" not in rapor, "PK düşmüşken kapsama oranı rapora YAYILDI (kill #5)"


def test_pk_tutarsa_kapsama_yayinlanir():
    sonuc = olc.olc(WIKI_MINI, KART_MINI, {"ham_yol": "x"}, ["AAA", "CCC", "EEE"],
                    bugun="2026-09-14", pk4=None)
    assert sonuc["yayin_engeli"]["engel"] is False
    assert sonuc["k1_kapsama_yayinlanabilir"] == pytest.approx(1.0)
    assert "KAPSAMA ORANI:" in olc.rapor_markdown(sonuc)


# ======================================================================================
# (9) TEK-KAYNAK AYRIŞMA ÇİVİSİ
# ======================================================================================

def test_ortak_yardimcilar_edg075ten_ithal_kopya_degil():
    """`olc` modülü K1/as_of/tarih/sembol yardımcılarını EDG-075 betiğinden İTHAL eder; kopya
    tutulsaydı iki taraf sessizce ayrışırdı (tek-kaynak yasası). İki koşul: (a) `ORTAK` GERÇEKTEN
    EDG-075 dosyası, (b) bu adların HİÇBİRİ `olc.py`de yeniden tanımlı değil."""
    beklenen = (KOK / "research" / "olcumler" / "edg075_sp500_tarihsel" / "olcum.py").resolve()
    assert pathlib.Path(olc.ORTAK.__file__).resolve() == beklenen
    for ad in ("_tarihi_isoya_cevir", "_tick", "_hucre", "_kolon_bul", "_is_gunu_farki_icinde",
               "as_of", "k1_bilinen_olaylar", "k1n_gelecek_olaylar", "k1_olaylari_ve_beyan",
               "kart_ic_tutarliligi", "pencereye_kirp"):
        assert hasattr(olc.ORTAK, ad), f"{ad} EDG-075 betiğinde yok — ithal kırıldı"
        assert ad not in vars(olc), f"{ad} olc.py'de YENİDEN TANIMLANMIŞ — tek-kaynak ihlali (kopya)"


def test_esikler_karttan_okunur_kod_kopyalamaz(tmp_path):
    kart = _kart_yaz(tmp_path, KART_MINI)
    e = olc.esikleri_karttan_oku(kart)
    assert e["bilinen_olay_kapsama_alt"] == 0.90 and e["pencere_satir_alt"] == 2
    eksik = dict(KART_MINI)
    eksik["esikler"] = {"bilinen_olay_kapsama_alt": 0.9}
    with pytest.raises(ValueError, match="bilinen_olay_n_alt"):
        olc.esikleri_karttan_oku(_kart_yaz(tmp_path, eksik))


def test_k1_nokta_tasiyan_sembol_normallesir():
    """Kart literali "MOG.A", tablo tarafı `_tick` ile "MOG-A" — kart tarafı normalleşmezse olay
    SESSİZCE 'bulunamadı' sayılır (ilk gerçek koşumda tam bu oldu, 2026-09-14)."""
    kart = dict(KART_MINI)
    kart["bilinen_olaylar"] = [{"sembol": "MOG.A", "yon": "giris", "tarih": "2026-08-20", "url": "u"}]
    olaylar, beyan_n, normalizasyon = olc.olay_kumesi(kart)
    assert olaylar[0]["sembol"] == "MOG-A" and beyan_n == 1
    assert normalizasyon == [{"kart_literali": "MOG.A", "normal": "MOG-A",
                             "kural": "ORTAK._tick — tablo tarafıyla AYNI fonksiyon"}]
    noktali = WIKI_MINI.replace("|| AAA ||", "|| MOG.A ||")
    degisiklikler, _ = olc.tabloyu_ayristir(noktali)
    k1 = olc.k1_kapsama(degisiklikler, olaylar, kart_beyan_n=1)
    assert k1["n_tam_gecti"] == 1, "noktalı sembol eşleşmedi — normalizasyon kırık"


def test_veri_penceresi_karttan_turetilir():
    assert olc.pencere_baslangici_karttan(KART_MINI) == "2020-07-27"
    with pytest.raises(ValueError):
        olc.pencere_baslangici_karttan({"veri_penceresi": "tarih yok"})


# ======================================================================================
# PK-4 — YOL TUTARLILIĞI (aynı ayrıştırıcı + aynı K1 ikinci sayfada)
# ======================================================================================

def test_pk4_ayni_ayristirici_ikinci_sayfada(tmp_path):
    pk_kart = {"bilinen_olaylar": [{"sembol": "KKK", "yon": "giris", "tarih": "2026-08-05"},
                                   {"sembol": "LLL", "yon": "cikis", "tarih": "2026-08-05"}]}
    pk = olc.pk4_yol_tutarli(WIKI_IDSIZ, pk_kart, "2020-01-01", "2026-09-14")
    assert pk["calisti"] is True and pk["n"] == 2 and pk["n_tam_gecti"] == 2
    assert pk["tuttu"] is True
    bozuk = dict(pk_kart)
    bozuk["bilinen_olaylar"] = pk_kart["bilinen_olaylar"] + [
        {"sembol": "QQQ", "yon": "giris", "tarih": "2026-08-05"}]
    assert olc.pk4_yol_tutarli(WIKI_IDSIZ, bozuk, "2020-01-01", "2026-09-14")["tuttu"] is False


def test_tarih_damgasi_olculur_uydurulmaz():
    d = olc.damga()
    assert dt.date.fromisoformat(d[:10]) <= dt.date.today() + dt.timedelta(days=1)
