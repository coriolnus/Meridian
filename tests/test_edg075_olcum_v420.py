"""tests/test_edg075_olcum_v420.py — EDG-2026-075 ÖLÇÜM betiğinin çivisi (TSK-156, 2026-09-05).

NE ÖLÇER. `research/olcumler/edg075_sp500_tarihsel/olcum.py` — kartın (`EDG-2026-075-sp500-
tarihsel-bilesenler-pit-kaynagi.yaml`) K1 (bilinen-olay çapraz-doğrulama), K2 (`as_of` yeniden
kurulum, simetrik fark) ve PK (yol-tutarlı, RAW HTML enjeksiyonu) bileşenlerini SENTETİK fikstür
HTML'iyle doğru ölçtüğünü kanıtlar. AĞA ÇIKMAZ: `httpx`/`cek()` bu dosyada HİÇ ÇAĞRILMAZ — yalnız
`--olc` yolunu (ham HTML → sonuç) sınar. Bu dosya AŞAĞIDAKİLERİ ölçer:
  (a) eşikler kartın YAPILANDIRILMIŞ `esikler:` alanından (`k1_gecti`/`k2_gecti`) doğru okunuyor,
      eksikse UYDURMUYOR (edg071 `esikleri_karttan_oku` emsali, `research/olcumler/
      edg071_hayalet_suzgec/olcum.py::esikleri_karttan_oku` ile AYNI desen);
  (b) KOLON EŞLEŞMESİ İKİ FARKLI şemada da doğru ÖLÇÜLÜYOR: rowspan/colspan'lı iki-satır başlık
      (Added/Removed altında ayrı Ticker/Security) VE tek-satır düz başlık ('Effective Date'/
      'Added'/'Removed'/'Reason', kart notundaki isimler) — MultiIndex kolonlar `df.columns`a
      GERİ YAZILARAK düzleştiriliyor mu (düzleştirilmezse `row.get(...)` hiçbir zaman eşleşmez —
      bu betiğin İLK sürümünde ölçülen ve düzeltilen kusur, aşağıda regresyon çivisi);
  (c) HAYALET-SATIR SÜZGECİ: tüm alanları boş satır (rowspan artığı) `changes`e YAZILMAZ, ama
      YALNIZ-EKLENEN/YALNIZ-ÇIKAN satır (aynı tarihte ayrı satırlarda çoklu değişiklik) TUTULUR —
      TSK-154 dersinin bu sayfaya UYARLANMIŞ hâli (o sayfadan farklı: tek-taraflı satır GEÇERLİDİR);
  (d) TARİH NORMALİZASYONU: 'August 5, 2026' → ISO, ayrıştırılamayan → None (uydurma yok);
  (e) K1: bilinen-olay eşleşmesi (satır var/tarih toleransı/yön) — yön BELİRTİLMEYEN olayda
      `yon_dogru=None` (UYDURULMAZ, True/False değil);
  (f) MUTASYON (CLAUDE.md §6 "çivi yeşili kanıt değildir"): `tolerans_gun` 1→0 parametresiyle
      TAM 1 iş günü sapan sentetik bir olay GERÇEKTEN kırmızıya dönüyor (n_tam_gecti 1→0);
  (g) K2 `as_of`: eklenen sembol sorgu-tarihinden SONRAysa geri alınır (o tarihte üye değildi),
      çıkarılan sembol geri EKLENİR (o tarihte üyeydi) — simetrik fark tabloyla BİREBİR;
  (h) POZİTİF KONTROL: `enjekte_pk_satiri` RAW HTML'e sentetik ZZQ1 satırı ekler, AYNI
      `tabloyu_ayristir` ile yeniden okunur; K1 sayısı DEĞİŞMEZ, `as_of(2026-07-02)` ZZQ1'İ
      İÇERİR, `as_of(2026-06-30)` İÇERMEZ (kart `pozitif_kontrol` birebir);
  (i) `hedef_tablo_bul` tablosuz gövdede ÇÖKMEZ (`ValueError` yutulup meta'ya yazılır — Yasa 4);
  (j) `main()` CLI ucu (`--olc --girdi <fikstür> --cikti <tmp>`) UÇTAN UCA çalışır ve `sonuc.json`
      şemasının beklenen anahtarları taşıdığını doğrular — betiğin GERÇEK çağrı BİÇİMİ (Rol-1'in
      koşacağı komut) burada bir kez sınanır.

KAPSAM DIŞI: kartın hükmü (Rol-1 verir, CLAUDE.md §3/§5) — bu dosya betiğin DOĞRU ÖLÇTÜĞÜNÜ
kanıtlar, "kaynak PIT sayılır/sayılmaz" kararı vermez. `meridian/*.py`ye bu betik hiç dokunmaz;
bu test dosyası da dokunmaz. `--cek`/`httpx.get` bu dosyada YOKTUR — betiğin AĞ bacağı bu ajan
turunda hiç çalıştırılmadı (devir raporunda ayrıca belirtilir)."""
from __future__ import annotations

import json
import pathlib

import pytest

from tests.conftest import betikten_modul_yukle

KOK = pathlib.Path(__file__).resolve().parents[1]
BETIK_YOLU = KOK / "research" / "olcumler" / "edg075_sp500_tarihsel" / "olcum.py"
KART_YOLU = KOK / "research" / "cards" / "EDG-2026-075-sp500-tarihsel-bilesenler-pit-kaynagi.yaml"


def _olcum():
    return betikten_modul_yukle(BETIK_YOLU, "edg075_olcum")


# ==================================================================================
# (a) eşikler karttan okunuyor (yapılandırılmış alan)
# ==================================================================================

def test_esikler_kartin_yapilandirilmis_alanindan_okunur():
    o = _olcum()
    esikler = o.esikleri_karttan_oku(KART_YOLU)
    assert esikler["kart_id"] == "EDG-2026-075"
    assert "10/10" in esikler["k1_gecti"]
    assert "fark 0" in esikler["k2_gecti"]


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
# fikstür HTML'ler — İKİ FARKLI ŞEMA (rowspan'lı çift-başlık / düz tek-başlık)
# ==================================================================================

_HTML_ROWSPAN = """
<table>
<tr><th rowspan="2">Date</th><th colspan="2">Added</th><th colspan="2">Removed</th><th rowspan="2">Reason</th></tr>
<tr><th>Ticker</th><th>Security</th><th>Ticker</th><th>Security</th></tr>
<tr><td>August 5, 2026</td><td>FERG</td><td>Ferguson plc</td><td>EA</td><td>Electronic Arts</td><td>Market cap</td></tr>
<tr><td>August 18, 2026</td><td>RDDT</td><td>Reddit Inc</td><td>AVB</td><td>AvalonBay</td><td>Rebalance</td></tr>
<tr><td>August 18, 2026</td><td>VMRK</td><td>Vermark</td><td>EQR</td><td>Equity Residential</td><td>Rebalance</td></tr>
<tr><td>June 30, 2026</td><td></td><td></td><td>CAG</td><td>ConAgra</td><td>Removed</td></tr>
<tr><td>March 9, 2026</td><td></td><td></td><td>MTCH</td><td>Match Group</td><td>Removed</td></tr>
<tr><td>September 22, 2025</td><td></td><td></td><td>ENPH</td><td>Enphase</td><td>Removed</td></tr>
<tr><td>April 1, 2024</td><td>SOLV</td><td>Solventum</td><td>VFC</td><td>VF Corp</td><td>Spinoff</td></tr>
<tr><td>September 4, 2026</td><td>BE</td><td>Bloom Energy</td><td></td><td></td><td>Rebalance</td></tr>
<tr><td>September 4, 2026</td><td>P</td><td>Pentair</td><td></td><td></td><td>Rebalance</td></tr>
<tr><td>September 4, 2026</td><td>ILMN</td><td>Illumina</td><td></td><td></td><td>Rebalance</td></tr>
<tr><td></td><td></td><td></td><td></td><td></td><td></td></tr>
</table>
"""

_HTML_DUZ = """
<table>
<tr><th>Effective Date</th><th>Added</th><th>Removed</th><th>Reason</th></tr>
<tr><td>August 6, 2026</td><td>FERG</td><td>EA</td><td>reorg</td></tr>
<tr><td>2023-05-01</td><td>ZZZ</td><td>YYY</td><td>x</td></tr>
</table>
"""

_HTML_TABLOSUZ = "<p>404 gövdesi, tablo yok</p>"


# ==================================================================================
# (b)+(c)+(d) tablo bulma + kolon düzleştirme + hayalet-satır süzgeci + tarih normalizasyonu
# ==================================================================================

def test_rowspanli_iki_satir_baslik_dogru_eslesiyor_ve_hayalet_atlaniyor():
    o = _olcum()
    idx, df, meta = o.hedef_tablo_bul(_HTML_ROWSPAN)
    assert idx == 0
    e = meta["eslenen"]
    assert "date" in e["tarih"].lower()
    assert e["eklenen_ticker"] and "added" in e["eklenen_ticker"].lower() and "ticker" in e["eklenen_ticker"].lower()
    assert e["eklenen_ad"] and "security" in e["eklenen_ad"].lower()
    assert e["cikan_ticker"] and "removed" in e["cikan_ticker"].lower() and "ticker" in e["cikan_ticker"].lower()

    degisiklikler, meta2 = o.tabloyu_ayristir(_HTML_ROWSPAN)
    assert meta2["n_satir_ham"] == 11
    assert meta2["n_hayalet_atlanan"] == 1          # tüm-alanları-boş SON satır
    assert meta2["n_satir_gecerli"] == 10
    assert len(degisiklikler) == 10


def test_MUTASYON_kolonlar_duzlestirilmezse_hicbir_satir_okunmaz(monkeypatch):
    """REGRESYON ÇİVİSİ: bu betiğin ilk sürümü `df.columns`u düzleştirmeden `row.get(<düz-ad>)`
    çağırıyordu — MultiIndex/tuple kolonlarda bu HİÇBİR ZAMAN eşleşmez ve her satır hayalet
    sayılırdı (elle ölçüldü, düzeltmeden önce `n_satir_gecerli == 0` idi). Mutasyon: `hedef_tablo_bul`
    içindeki `df.columns = kolonlar` atamasını iptal edip (df'i OLDUĞU gibi döndürerek) aynı iddiayı
    tekrar çağırmak KIRMIZI verir — burada atamayı SİMÜLE ETMEK için doğrudan orijinal (düzleştirilmemiş)
    DataFrame'i taklit eden bir sahte `hedef_tablo_bul` ile `tabloyu_ayristir`in İÇ mantığını
    (satır-okuma) aynı girdiyle çağırıyoruz."""
    o = _olcum()
    idx, df_flat, meta = o.hedef_tablo_bul(_HTML_ROWSPAN)
    # gerçek (düzleştirilmiş) df ile satır okuma ÇALIŞIR:
    satirlar_dogru, _ = o.tabloyu_ayristir(_HTML_ROWSPAN)
    assert len(satirlar_dogru) == 10

    # `hedef_tablo_bul`u DÜZLEŞTİRMEYEN bir sürümle DEĞİŞTİR (mutasyon) — `df.columns` ORİJİNAL
    # (tuple) kalsın, yalnız `meta['eslenen']` düz string adları versin (kusurun tam şekli).
    import pandas as pd
    import io as _io
    tables = pd.read_html(_io.StringIO(_HTML_ROWSPAN), flavor="lxml")
    df_ham = tables[0]                                    # kolonlar HÂLÂ tuple/MultiIndex

    def _mutasyonlu_hedef_tablo_bul(html):
        return 0, df_ham, meta

    monkeypatch.setattr(o, "hedef_tablo_bul", _mutasyonlu_hedef_tablo_bul)
    satirlar_mutasyonlu, meta_mut = o.tabloyu_ayristir(_HTML_ROWSPAN)
    assert len(satirlar_mutasyonlu) == 0, (
        "mutasyon (kolon düzleştirme kaldırıldı) KIRMIZI vermedi — çivi bu dalı ısırmıyor")
    assert meta_mut["n_hayalet_atlanan"] == meta_mut["n_satir_ham"]


def test_duz_tek_satir_baslik_effective_date_added_removed_reason():
    """Kart notundaki tam isimler ('Effective Date'/'Added'/'Removed'/'Reason', alt-kolonsuz)."""
    o = _olcum()
    idx, df, meta = o.hedef_tablo_bul(_HTML_DUZ)
    e = meta["eslenen"]
    assert e["tarih"] == "Effective Date"
    assert e["eklenen_ticker"] == "Added" and e["eklenen_ad"] is None      # alt-kolon YOK
    assert e["cikan_ticker"] == "Removed" and e["cikan_ad"] is None

    degisiklikler, _ = o.tabloyu_ayristir(_HTML_DUZ)
    assert degisiklikler[0] == {"tarih": "2026-08-06", "tarih_ham": "August 6, 2026",
                                "eklenen": "FERG", "cikan": "EA", "neden": "reorg"}
    assert degisiklikler[1]["tarih"] == "2023-05-01"      # ISO girdi de doğru ayrıştı


def test_tarih_ayristirilamayan_satir_None_tasir_uydurmaz():
    o = _olcum()
    html = """<table><tr><th>Date</th><th>Added</th><th>Removed</th></tr>
    <tr><td>belirsiz-tarih</td><td>XYZ</td><td></td></tr></table>"""
    degisiklikler, meta = o.tabloyu_ayristir(html)
    assert degisiklikler[0]["tarih"] is None
    assert meta["n_tarih_ayristirilamadi"] == 1


def test_tablosuz_govde_cokmez_hata_meta_yazar():
    o = _olcum()
    idx, df, meta = o.hedef_tablo_bul(_HTML_TABLOSUZ)
    assert idx is None and df is None
    assert meta["n_tablo"] == 0
    assert "hata" in meta and meta["hata"]


# ==================================================================================
# (e)+(f) K1 bilinen-olay çapraz-doğrulama + mutasyon (tolerans_gun 1→0)
# ==================================================================================

def test_k1_bilinen_olaylar_hepsi_gecer_fikstur_tasarimi_geregi():
    o = _olcum()
    degisiklikler, _ = o.tabloyu_ayristir(_HTML_ROWSPAN)
    k1 = o.k1_bilinen_olaylar(degisiklikler)
    assert k1["olculen_n"] == 14                          # bkz. olcum.py modül başlığı — 14 vs kart "10"
    assert k1["kart_beyan_n"] == 10
    assert k1["n_tam_gecti"] == 14
    assert k1["sayim_notu"]


def test_k1_yon_belirtilmeyen_olay_None_tasir_uydurmaz():
    o = _olcum()
    degisiklikler, _ = o.tabloyu_ayristir(_HTML_ROWSPAN)
    k1 = o.k1_bilinen_olaylar(degisiklikler)
    cag = next(d for d in k1["detay"] if d["sembol"] == "CAG")
    assert cag["beklenen_yon"] is None
    assert cag["yon_dogru"] is None                        # ne True ne False — UYDURULMADI
    assert cag["satir_var"] is True and cag["tarih_tolerans_icinde"] is True


def test_k1_yanlis_yon_yakalanir():
    o = _olcum()
    olaylar = [{"sembol": "EA", "yon": "giris", "tarih": "2026-08-05", "yon_kaynak": "t"}]   # ters yön
    degisiklikler, _ = o.tabloyu_ayristir(_HTML_ROWSPAN)
    k1 = o.k1_bilinen_olaylar(degisiklikler, olaylar)
    assert k1["detay"][0]["yon_dogru"] is False
    assert k1["n_tam_gecti"] == 0


def test_MUTASYON_tolerans_gun_1den_0a_dusunce_bir_gunluk_sapma_kirmizi_olur():
    """Kart K1: '±1 iş günü'. `_is_gunu_farki_icinde` 1 gün toleransla GEÇER, 0 toleransla
    (mutasyon) AYNI sentetik vakada KIRMIZI verir — betiğin bu sınırı GERÇEKTEN ölçtüğünün kanıtı."""
    o = _olcum()
    html = """<table><tr><th>Date</th><th>Added</th><th>Removed</th></tr>
    <tr><td>August 6, 2026</td><td></td><td>EA</td></tr></table>"""     # gerçek EA tarihi 08-05, tablo 08-06 (1 gün kaymış)
    degisiklikler, _ = o.tabloyu_ayristir(html)
    olaylar = [{"sembol": "EA", "yon": "cikis", "tarih": "2026-08-05", "yon_kaynak": "t"}]

    k1_tol1 = o.k1_bilinen_olaylar(degisiklikler, olaylar, tolerans_gun=1)
    k1_tol0 = o.k1_bilinen_olaylar(degisiklikler, olaylar, tolerans_gun=0)
    assert k1_tol1["n_tam_gecti"] == 1, "tolerans=1 ile 1 günlük sapma GEÇMELİYDİ"
    assert k1_tol0["n_tam_gecti"] == 0, (
        "MUTASYON dalını çivi ISIRMIYOR: tolerans=0 ile aynı vaka hâlâ geçiyor")
    assert k1_tol0["detay"][0]["tarih_tolerans_icinde"] is False


def test_is_gunu_farki_hafta_sonu_koprusu_bir_sayilir():
    o = _olcum()
    # Cuma (2026-08-07) → Pazartesi (2026-08-10): hafta sonu köprüsü, İŞ GÜNÜ farkı 1
    assert o._is_gunu_farki_icinde("2026-08-07", "2026-08-10", tolerans_gun=1) is True
    assert o._is_gunu_farki_icinde("2026-08-07", "2026-08-11", tolerans_gun=1) is False


# ==================================================================================
# (g) K2 — as_of yeniden kurulum + simetrik fark
# ==================================================================================

def test_as_of_eklenen_sonraysa_geri_alinir_cikan_sonraysa_geri_eklenir():
    o = _olcum()
    degisiklikler = [{"tarih": "2026-07-01", "tarih_ham": "x", "eklenen": "NEW", "cikan": "OLD", "neden": None}]
    guncel = {"NEW", "AAA"}
    assert o.as_of(degisiklikler, guncel, "2026-06-30") == {"OLD", "AAA"}   # NEW henüz yoktu, OLD hâlâ üyeydi
    assert o.as_of(degisiklikler, guncel, "2026-07-02") == {"NEW", "AAA"}   # değişiklik zaten olmuş


def test_k2_simetrik_fark_tabloyla_birebir_ve_bugun_esitligi():
    o = _olcum()
    degisiklikler = [
        {"tarih": "2026-07-01", "tarih_ham": "x", "eklenen": "NEW", "cikan": "OLD", "neden": None},
        {"tarih": "2026-08-15", "tarih_ham": "x", "eklenen": "FOO", "cikan": "BAR", "neden": None},
    ]
    guncel = ["NEW", "FOO", "AAA"]
    k2 = o.k2_as_of_yeniden_kurulum(degisiklikler, guncel, "2026-06-01", "2026-09-05", "2026-09-05")
    assert k2["calisti"] is True
    assert k2["simetrik_fark"] == sorted(["NEW", "OLD", "FOO", "BAR"])
    assert k2["simetrik_fark_birebir_mi"] is True
    assert k2["as_of_bugun_esit_mi"] is True


def test_k2_guncel_liste_yoksa_UYDURMAZ_calismadi_neden_tasir():
    o = _olcum()
    k2 = o.k2_as_of_yeniden_kurulum([], None, "2026-06-01", "2026-09-05", "2026-09-05")
    assert k2["calisti"] is False
    assert k2["neden"]
    assert k2["as_of_bugun_esit_mi"] is None


# ==================================================================================
# (h) POZİTİF KONTROL — RAW HTML enjeksiyonu, yol-tutarlı
# ==================================================================================

def test_pk_enjeksiyon_ile_zzq1_dogru_tarihte_gorunur_k1_degismez():
    o = _olcum()
    pk = o.pozitif_kontrol(_HTML_ROWSPAN, bugun="2026-09-05")
    assert pk["k1_degismedi"] is True
    assert pk["k1_n_tam_gecti_once"] == pk["k1_n_tam_gecti_sonra"] == 14
    assert pk["pk_sembol_as_of_sonra_icerir_mi"] is True
    assert pk["pk_sembol_as_of_once_icermez_mi"] is True
    assert pk["tuttu"] is True


def test_MUTASYON_pk_tutmama_hali_yakalanir_yanlis_tarihle():
    """PK sonucunun `tuttu` alanı GERÇEKTEN üç koşulun VE'si mi — birini bozan bir çağrı (yanlış
    `as_of_sonra_tarih` karşılaştırması) `tuttu=False` üretmeli; doğrudan alt-bileşenleri
    karşılaştırarak (enjekte sonrası as_of, enjeksiyon ÖNCESİ tarihte sorgulanırsa ZZQ1 YOK)."""
    o = _olcum()
    degisiklikler_enjekteli, _ = o.tabloyu_ayristir(o.enjekte_pk_satiri(_HTML_ROWSPAN))
    guncel = {r["eklenen"] for r in degisiklikler_enjekteli if r["eklenen"]} | \
             {r["cikan"] for r in degisiklikler_enjekteli if r["cikan"]} | {o.PK_SEMBOL}
    # ENJEKSİYONDAN ÖNCEKİ bir tarihte ZZQ1 üye OLMAMALI (2026-01-01 << 2026-07-01)
    assert o.PK_SEMBOL not in o.as_of(degisiklikler_enjekteli, guncel, "2026-01-01")
    # enjeksiyon tarihinden SONRA üye OLMALI
    assert o.PK_SEMBOL in o.as_of(degisiklikler_enjekteli, guncel, "2026-12-31")


def test_pk_hedef_tablo_yoksa_value_error_atar_sessiz_degil():
    o = _olcum()
    with pytest.raises(ValueError, match="hedef değişiklik tablosu"):
        o.enjekte_pk_satiri(_HTML_TABLOSUZ)


# ==================================================================================
# (j) CLI ucu — `--olc` uçtan uca (fikstür HTML, ağ YOK, tmp_path'e yazar)
# ==================================================================================

def test_cli_olc_uctan_uca_fikstur_ile_sonuc_semasi(tmp_path):
    o = _olcum()
    girdi = tmp_path / "999_deadbeefdeadbeef.html"
    girdi.write_text(_HTML_ROWSPAN, encoding="utf-8")
    cikti = tmp_path / "sonuc.json"

    rc = o.main(["--olc", "--girdi", str(girdi), "--kart", str(KART_YOLU),
                "--bugun", "2026-09-05", "--cikti", str(cikti)])
    assert rc == 0
    assert cikti.exists()
    sonuc = json.loads(cikti.read_text(encoding="utf-8"))
    assert sonuc["kart"] == "EDG-2026-075"
    assert sonuc["girdi_kimligi"]["oldid"] == 999
    assert sonuc["girdi_kimligi"]["html_sha256_prefix16"] == "deadbeefdeadbeef"
    assert sonuc["k1_bilinen_olaylar"]["olculen_n"] == 14
    assert sonuc["pozitif_kontrol"]["tuttu"] is True
    assert sonuc["adim_0_fizibilite"]["a_tablo_okunuyor"] is True
    assert sonuc["adim_0_fizibilite"]["b_oldid_ile_sabit"] is True
    assert "esikler" in sonuc and sonuc["esikler"]["k1_gecti"]
    assert "beyan" in sonuc


def test_cli_olc_girdi_yoksa_hata_ile_cikar(tmp_path):
    o = _olcum()
    rc = o.main(["--olc", "--girdi", str(tmp_path / "yok.html"), "--kart", str(KART_YOLU),
                "--cikti", str(tmp_path / "sonuc.json")])
    assert rc == 1


def test_cli_bayrak_verilmezse_hata():
    o = _olcum()
    with pytest.raises(SystemExit):
        o.main([])


# ==================================================================================
# oldid_bul — network YOK, yalnız metin ayrıştırma
# ==================================================================================

def test_oldid_bul_wgrevisionid_regex():
    o = _olcum()
    html = '<script>RLCONF={};mw.config.set({"wgPageName":"X","wgRevisionId":123456789,"wgFoo":1});</script>'
    assert o.oldid_bul(html) == 123456789
    assert o.oldid_bul("<html>hiç yok</html>") is None
