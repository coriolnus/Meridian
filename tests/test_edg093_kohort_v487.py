"""tests/test_edg093_kohort_v487.py — EDG-2026-093 ADIM-0 A kohort üreticisinin çivileri.

vNNN KİMLİK KAYDI: v487 seçildi çünkü ölçüm anında (2026-09-14) `tests/` altında v486
(`test_denetci_rota_reasoning_v486.py`) en yüksek numaraydı ve v487 BOŞTU — çakışma yok, taşıma yok.

NE ÇİVİLER (brief EDG-2026-093 ADIM-0 A, madde 3):
  (1) SHA KAPISI: beklenen sha tutmuyorsa üretici DURUR (çıkış 2) ve hata metni dosyayı ADIYLA
      anar; sha kaydında satır yoksa da durur (beklenen sha UYDURULMAZ).
  (2) CSV SÖZLEŞMESİ = ölçülen `sp500_uyelik_tarihi.csv` sözleşmesi: başlık `date,tickers` ·
      tarih ARTAN ve TEKRARSIZ · `tickers` alfabetik SIRALI, iç tekrar YOK · ardışık satırlar
      BİREBİR AYNI kümeyi taşımaz (adım fonksiyonu) · her takvim günü için "tarih ≤ t olan son
      satır" okuması as-of serisiyle BİREBİR aynı.
  (3) BOYUT BANDI KARTTAN okunur (koda sayı yazılmaz) ve bant dışı gün varsa çıkış ≠ 0.
  (4) BELİRSİZ TAVANI karttan okunur; tavanı aşan gün varsa çıkış ≠ 0.
  (5) PIT-PK: bilinen bir olay t-1/t geçişinde doğru yansır; yön ters kitaplanırsa PK DÜŞER.
  (6) ELLE EŞLEME ŞEMASI: `karar` sözlüğü DIŞI bir değer REDDEDİLİR; `esle:` biçimi zorunlu;
      eksik alan reddedilir.
  (7) `--kuru` HİÇBİR dosya yazmaz (verilen çıktı dizini BOŞ kalır).
  (8) TEK-KAYNAK: `as_of` EDG-075 betiğinden İTHAL edilir — kopya değil (aynı fonksiyon nesnesi).
  (9) GERÇEK GİRDİ tam koşumu — ham wikitext `.gitignore`'lu, CI'da YOK → `skipif`.
 (10) TUR-2 ÇOK-SEMBOLLÜ HÜCRE: `X/Y` biçimindeki ticker hücresi AYRI sembollere bölünür
      (S&P endeksleri iki hisse sınıfını ayrı bileşen sayar); bölünmezse kohorta hayalet bir
      "ticker" girer. Üretilen csv'de ayıraç taşıyan sembol KALMAZ.
 (11) TUR-2 YENİDEN ADLANDIRMA: gerekçe hücresi yeniden adlandırmayı AÇIKÇA söylüyorsa (sözlük
      eşleşmesi + borsa parantezinde sembol) karar `esle:<eski>-><yeni>` olur ve as-of
      yürütmesinde UYGULANIR; söylemiyorsa `belirsiz` KALIR (uydurma yok). İki yarım satırın
      eşlemesi ayrı bir jetondur (`cift:`) ve hiçbir sembolü yeniden yazmaz.

DİSİPLİN: çiviler SENTETİK fikstürlerle koşar (ağ yok); gerçek koşumun sayıları Rol-1'in
okuyacağı `adim0a_sonuc_<damga>.json`da. Mutasyon kanıtı devir raporunda.
"""
from __future__ import annotations

import csv
import datetime as dt
import hashlib
import io
import json
import pathlib

import pytest
import yaml

from tests.conftest import betikten_modul_yukle
# Sentetik MDY xlsx kurucusu TEK KOPYADIR: EDG-092 çivi dosyasındaki fikstür İTHAL edilir,
# kopyalanmaz (aynı okuyucunun aynı şeması; iki kopya sessizce ayrışırdı).
from tests.test_edg092_sp400_olcum_v484 import _xlsx_yaz

KOK = pathlib.Path(__file__).resolve().parents[1]
KOHORT_YOLU = KOK / "research" / "olcumler" / "edg093_midcap_pit" / "kohort.py"
GERCEK_HAM = (KOK / "research" / "olcumler" / "edg092_sp400_uyelik" / "ham"
              / "sp400_oldid_1373849406.wiki")
GERCEK_XLSX = (KOK / "research" / "olcumler" / "edg092_sp400_uyelik" / "girdi"
               / "mdy_holdings_2026-09-10.xlsx")
SP500_CSV = KOK / "research" / "pit_universe" / "sp500_uyelik_tarihi.csv"


def _modul():
    """Üreticiyi DOSYA YOLUNDAN, KAYNAKTAN DERLEYEREK yükler (`research/` altı paket değil).

    Ham `spec.loader.exec_module` YASAK (v334): o yol `__pycache__`e bakar ve zaman damgalı pyc'nin
    geçerlilik ölçütü yalnız (tam-saniye mtime, bayt boyutu) çiftidir — `kohort.py`de boyutu
    değiştirmeyen bir mutasyon (`<=`→`<`) aynı saniyede kalırsa BAYAT bytecode koşar ve bu
    dosyadaki çiviler YANLIŞ KODU yeşil yapardı (mutasyon kanıtı da sahte çıkardı).
    `sys_modules_kaydet=True`: betik kendi adını çözebilmeli."""
    return betikten_modul_yukle(KOHORT_YOLU, "edg093_kohort_test", sys_modules_kaydet=True)


kohort = _modul()


# ======================================================================================
# SENTETİK FİKSTÜRLER — küçük bir "S&P 4" evreni (400 yerine 4 üye; bant karttan okunduğu için
# eşikler de sentetik kartta küçültülür — kod sayı taşımaz, çivi bunu ölçer)
# ======================================================================================

WIKI_MINI = """Giriş düzyazısı.

{| class="wikitable sortable"
|-
! rowspan="2" | Date
! colspan="2" | Added
! colspan="2" | Removed
! rowspan="2" | Reason
|-
! Ticker || Security ||  Ticker ||  Security
|-
|March 2, 2021 || EEE || [[Epsilon]] || DDD || [[Delta]] || Piyasa değeri değişimi.<ref>{{cite web |url=https://example.org/e.pdf}}</ref>
|-
|February 2, 2021 || CCC || [[Gamma]] || BBB || [[Beta]] || Beta satın alındı.<ref>{{cite web |url=https://example.org/c.pdf}}</ref>
|-
|}
"""

# Tek yanlı ÇİFT: spin-off (yalnız giren) + ertesi gün piyasa değeri (yalnız çıkan) — EDG-092
# tanısındaki "ardışık kitaplama" deseni. Öneri kuralı bunu `esle:` yapmalı.
WIKI_TEK_YANLI = """{| class="wikitable sortable"
|-
! rowspan="2" | Date
! colspan="2" | Added
! colspan="2" | Removed
! rowspan="2" | Reason
|-
! Ticker || Security ||  Ticker ||  Security
|-
|December 2, 2021 ||  ||  || DDD || [[Delta]] || Market capitalization change.<ref>{{cite web |url=https://example.org/d.pdf}}</ref>
|-
|December 1, 2021 || EEE || [[Epsilon]] ||  ||  || Parent Corp spun off Epsilon.<ref>{{cite web |url=https://example.org/e.pdf}}</ref>
|-
|}
"""

# TUR-2 (1) ÇOK-SEMBOLLÜ HÜCRE: kaynak tablo bir şirketin iki hisse sınıfını TEK hücrede
# `AAX/AAY` biçiminde yazar. İki sembol de AYRI bileşendir; hücre BÖLÜNMEZSE `AAX/AAY` diye bir
# hayalet "ticker" kohorta girer (ölçüldü: gerçek tabloda 2 hücre, 163 csv satırının 146'sı).
WIKI_COK_SEMBOL = """{| class="wikitable sortable"
|-
! rowspan="2" | Date
! colspan="2" | Added
! colspan="2" | Removed
! rowspan="2" | Reason
|-
! Ticker || Security ||  Ticker ||  Security
|-
|March 2, 2021 || AAX/AAY || [[Alpha]] || DDD || [[Delta]] || Market capitalization change.
|-
|}
"""

# Aynı hücre ÇIKAN sütununda: geri sarma onu kümeye EKLER, yani bölünmezse hayalet ticker
# doğrudan csv'ye SIZAR (gerçek tablodaki `UAA/UA` çıkışının sentetik eşi).
WIKI_COK_SEMBOL_CIKAN = WIKI_COK_SEMBOL.replace(
    "|March 2, 2021 || AAX/AAY || [[Alpha]] || DDD || [[Delta]] ||",
    "|March 2, 2021 || EEE || [[Epsilon]] || AAX/AAY || [[Alpha]] ||")

# TUR-2 (2) YENİDEN ADLANDIRMA: gerekçe hücresi AÇIKÇA "changed its name and symbol to … (NYSE: NNN)"
# der. Geri sarmada `OOO` discard'ı ETKİSİZDİR (güncel küme `NNN` taşır) → `esle:OOO->NNN`.
WIKI_RENAME = """{| class="wikitable sortable"
|-
! rowspan="2" | Date
! colspan="2" | Added
! colspan="2" | Removed
! rowspan="2" | Reason
|-
! Ticker || Security ||  Ticker ||  Security
|-
|June 1, 2022 || PPP || [[Pi]] || NNN || [[Nu]] || Market capitalization change.
|-
|June 1, 2021 || OOO || [[Omicron]] || QQQ || [[Qoppa]] || Omicron Corp acquired Qoppa Corp. Post-merger, Omicron Corp changed its name and symbol to Nu Inc. (NYSE: NNN).
|-
|}
"""

_RENAME_GEREKCE = ("Omicron Corp acquired Qoppa Corp. Post-merger, Omicron Corp changed its name "
                   "and symbol to Nu Inc. (NYSE: NNN).")
# Aynı yapı, gerekçesinde yeniden adlandırma YOK → karar `belirsiz` KALIR (uydurma yok).
WIKI_RENAME_GEREKCESIZ = WIKI_RENAME.replace(_RENAME_GEREKCE, "Market capitalization change.")
# Gerekçede BORSA PARANTEZİ var ama yeniden adlandırma ANLATILMIYOR — sembolün varlığı tek başına
# eşleme gerekçesi DEĞİLDİR (EDG-092'nin ölçtüğü yanlış-pozitif sınıfının kardeşi).
WIKI_RENAME_PARANTEZ = WIKI_RENAME.replace(
    _RENAME_GEREKCE, "Omicron Corp acquired Nu Inc. (NYSE: NNN) in an all-cash transaction.")

# Yalnız giren, gerekçesi tanınmayan → öneri kuralı karar VEREMEZ, `belirsiz` kalır.
WIKI_BELIRSIZ = """{| class="wikitable sortable"
|-
! rowspan="2" | Date
! colspan="2" | Added
! colspan="2" | Removed
! rowspan="2" | Reason
|-
! Ticker || Security ||  Ticker ||  Security
|-
|December 1, 2021 || EEE || [[Epsilon]] ||  ||  || Gerekçe yazılmamış satır.
|-
|}
"""

KART093_MINI = {
    "card_id": "EDG-TEST-093",
    "veri_penceresi": "2021-01-01 → ölçüm günü; as-of günlük",
    "esikler": {"kohort_boyut_bant": [4, 4], "belirsiz_isim_gun_ust": 1},
}

# Tek yanlı satır çivileri için: bant GENİŞ (o fikstürlerde kohort 2-3 isim), tavan 12.
KART093_GENIS = {
    "card_id": "EDG-TEST-093-genis",
    "veri_penceresi": "2021-01-01 → ölçüm günü; as-of günlük",
    "esikler": {"kohort_boyut_bant": [1, 9], "belirsiz_isim_gun_ust": 12},
}

KART092_MINI = {
    "card_id": "EDG-TEST-092",
    "bilinen_olaylar": [
        {"sembol": "CCC", "yon": "giris", "tarih": "2021-02-02", "url": "https://example.org/c.pdf"},
        {"sembol": "BBB", "yon": "cikis", "tarih": "2021-02-02", "url": "https://example.org/c.pdf"},
        {"sembol": "EEE", "yon": "giris", "tarih": "2021-03-02", "url": "https://example.org/e.pdf"},
        {"sembol": "DDD", "yon": "cikis", "tarih": "2021-03-02", "url": "https://example.org/e.pdf"},
    ],
}


def _yaz(tmp: pathlib.Path, ad: str, metin: str) -> pathlib.Path:
    yol = tmp / ad
    yol.write_text(metin, encoding="utf-8")
    return yol


def _sha_kaydi(tmp: pathlib.Path, ad: str, hedef: pathlib.Path, sha: str | None = None) -> pathlib.Path:
    sha = sha or hashlib.sha256(hedef.read_bytes()).hexdigest()
    yol = tmp / ad
    yol.write_text(f"{sha}  {hedef.name}\n", encoding="utf-8")
    return yol


def _kart(tmp: pathlib.Path, ad: str, icerik: dict) -> pathlib.Path:
    yol = tmp / ad
    yol.write_text(yaml.safe_dump(icerik, allow_unicode=True), encoding="utf-8")
    return yol


def _duzenek(tmp_path: pathlib.Path, wikitext: str = WIKI_MINI,
             uyeler: list[str] | None = None, kart093: dict | None = None) -> dict:
    """Sentetik bir tam koşum düzeneği: ham + xlsx + iki kart + iki sha kaydı + çıktı kökü."""
    uyeler = uyeler if uyeler is not None else ["AAA", "CCC", "EEE", "FFF"]
    ham = _yaz(tmp_path, "mini.wiki", wikitext)
    xlsx = _xlsx_yaz(tmp_path, [(f"{t} Corp", t) for t in uyeler])
    return {
        "ham": ham, "xlsx": xlsx,
        "ham_kaydi": _sha_kaydi(tmp_path, "HAM_SHA.txt", ham),
        "xlsx_kaydi": _sha_kaydi(tmp_path, "XLSX_SHA.txt", xlsx),
        "kart093": _kart(tmp_path, "kart093.yaml", kart093 or KART093_MINI),
        "kart092": _kart(tmp_path, "kart092.yaml", KART092_MINI),
        "cikti": tmp_path / "cikti",
    }


def _argv(d: dict, *ek: str) -> list[str]:
    return ["--ham", str(d["ham"]), "--xlsx", str(d["xlsx"]),
            "--ham-sha-kaydi", str(d["ham_kaydi"]), "--xlsx-sha-kaydi", str(d["xlsx_kaydi"]),
            "--kart", str(d["kart093"]), "--kart092", str(d["kart092"]),
            "--bugun", "2021-04-01", *ek]


def _sonuc_json(cikti: pathlib.Path) -> dict:
    yollar = sorted((cikti / "research" / "olcumler" / "edg093_midcap_pit").glob("adim0a_sonuc_*.json"))
    assert yollar, "sonuç JSON yazılmadı"
    return json.loads(yollar[-1].read_text(encoding="utf-8"))


# ======================================================================================
# (1) SHA KAPISI
# ======================================================================================

def test_A1_sha_uyusmazligi_DURDURUR_ve_dosyayi_adiyla_anar(tmp_path, capsys):
    d = _duzenek(tmp_path)
    rc = kohort.main(_argv(d, "--kuru", "--beklenen-sha", "0" * 64))
    assert rc == 2
    hata = capsys.readouterr().err
    assert "ham wikitext" in hata and d["ham"].name in hata
    assert "sha256 UYUŞMUYOR" in hata


def test_A2_sha_kaydinda_satir_yoksa_DURUR_beklenen_sha_uydurulmaz(tmp_path, capsys):
    d = _duzenek(tmp_path)
    d["ham_kaydi"].write_text("deadbeef  baska_dosya.wiki\n", encoding="utf-8")
    rc = kohort.main(_argv(d, "--kuru"))
    assert rc == 2
    assert "UYDURULAMAZ" in capsys.readouterr().err


def test_A3_sha_kapisi_gecince_kosum_TAMAMLANIR(tmp_path):
    d = _duzenek(tmp_path)
    assert kohort.main(_argv(d, "--kuru")) == 0


# ======================================================================================
# (2) CSV SÖZLEŞMESİ
# ======================================================================================

def _sozlesme_olc(metin: str) -> dict:
    satirlar = list(csv.reader(io.StringIO(metin)))
    veri = satirlar[1:]
    kumeler = [tuple(r[1].split(",")) for r in veri]
    return {
        "baslik": satirlar[0],
        "tarihler": [r[0] for r in veri],
        "artan": all(veri[i][0] < veri[i + 1][0] for i in range(len(veri) - 1)),
        "tekrarsiz": len({r[0] for r in veri}) == len(veri),
        "sirali": all(list(k) == sorted(k) for k in kumeler),
        "ic_tekrar": any(len(k) != len(set(k)) for k in kumeler),
        "ardisik_ayni": any(kumeler[i] == kumeler[i + 1] for i in range(len(kumeler) - 1)),
    }


def test_B1_uretilen_csv_OLCULEN_sp500_sozlesmesine_uyar(tmp_path):
    d = _duzenek(tmp_path)
    assert kohort.main(_argv(d, "--uygula", "--cikti", str(d["cikti"]))) == 0
    metin = (d["cikti"] / "research" / "pit_universe" / "sp400_uyelik_tarihi.csv").read_text()
    o = _sozlesme_olc(metin)
    assert o["baslik"] == ["date", "tickers"]
    assert o["artan"] and o["tekrarsiz"] and o["sirali"]
    assert not o["ic_tekrar"]
    assert not o["ardisik_ayni"], "adım fonksiyonu: ardışık satırlar BİREBİR aynı küme olamaz"
    assert metin.endswith("\n") and "\r" not in metin


@pytest.mark.skipif(not SP500_CSV.exists(), reason="sp500_uyelik_tarihi.csv yok")
def test_B2_emsal_dosya_AYNI_sozlesme_kapisindan_gecer(tmp_path):
    """Sözleşme kapısı UYDURULMADI: emsal dosyanın kendisi de (ardışık-aynı maddesi HARİÇ —
    emsalde 2.024 kopya satır var, ölçüldü) aynı ölçütlerden geçer."""
    o = _sozlesme_olc(SP500_CSV.read_text(encoding="utf-8"))
    assert o["baslik"] == ["date", "tickers"]
    assert o["artan"] and o["tekrarsiz"] and o["sirali"] and not o["ic_tekrar"]


def test_B3_as_of_okumasi_her_takvim_gunu_icin_BIREBIR(tmp_path):
    """"tarih ≤ t olan son satır" okuması, üreticinin günlük as-of serisiyle aynı sonucu vermeli —
    yoksa dosya adım fonksiyonunu KAYIPLI örneklemiş olur."""
    d = _duzenek(tmp_path)
    kart = kohort.OLC.kart_yukle(d["kart093"])
    wikitext = d["ham"].read_text(encoding="utf-8")
    degisiklikler, _ = kohort.OLC.tabloyu_ayristir(wikitext)
    guncel, _ = kohort.OLC.mdy_tickerlari(d["xlsx"])
    gun_listesi = kohort.gunler(kohort.OLC.pencere_baslangici_karttan(kart), "2021-04-01")
    seri = kohort.uyelik_serisi(degisiklikler, set(guncel), gun_listesi)
    satirlar = kohort.csv_satirlari(seri, gun_listesi)

    for g in gun_listesi:
        son = [s for s in satirlar if s[0] <= g][-1]
        assert set(son[1].split(",")) == set(seri[g]), f"{g} için as-of okuması ayrıştı"


# ======================================================================================
# (3)/(4) KAPILAR — EŞİKLER KARTTAN
# ======================================================================================

def test_C1_boyut_bandi_KARTTAN_okunur(tmp_path):
    d = _duzenek(tmp_path)
    kart = kohort.OLC.kart_yukle(d["kart093"])
    assert kohort.esikleri_karttan_al(kart)["kohort_boyut_bant"] == [4, 4]


def test_C2_kart_esigi_yoksa_UYDURULMAZ():
    with pytest.raises(ValueError, match="UYDURAMAZ"):
        kohort.esikleri_karttan_al({"card_id": "X", "esikler": {"belirsiz_isim_gun_ust": 1}})
    with pytest.raises(ValueError, match="UYDURAMAZ"):
        kohort.esikleri_karttan_al({"card_id": "X", "esikler": {"kohort_boyut_bant": [1, 2]}})


def test_C3_bant_disi_gun_CIKIS_KODUNU_bozar(tmp_path):
    """Güncel liste 4 yerine 6 isim taşırsa her gün bant dışıdır → çıkış ≠ 0 ve kapı DÜŞER."""
    d = _duzenek(tmp_path, uyeler=["AAA", "CCC", "EEE", "FFF", "GGG", "HHH"])
    rc = kohort.main(_argv(d, "--uygula", "--cikti", str(d["cikti"])))
    assert rc != 0
    sonuc = _sonuc_json(d["cikti"])
    assert sonuc["kapi"]["boyut_bandi_gecti"] is False
    assert sonuc["kohort"]["bant_disi_gun_n"] == sonuc["pencere"]["gun_n"]
    assert sonuc["hukum"] == "YOK — Rol-1"


def test_C4_belirsiz_tavani_asilinca_CIKIS_KODU_bozulur(tmp_path):
    """Tavanı 0'a çeken kartla, `belirsiz` kararlı bir tek-yanlı satır kapıyı DÜŞÜRÜR."""
    kart = dict(KART093_MINI)
    kart["esikler"] = {"kohort_boyut_bant": [1, 9], "belirsiz_isim_gun_ust": 0}
    d = _duzenek(tmp_path, wikitext=WIKI_BELIRSIZ, uyeler=["AAA", "EEE"], kart093=kart)
    rc = kohort.main(_argv(d, "--uygula", "--cikti", str(d["cikti"]), "--bugun", "2022-04-01"))
    assert rc != 0
    sonuc = _sonuc_json(d["cikti"])
    assert sonuc["kapi"]["belirsiz_tavani_gecti"] is False
    assert sonuc["belirsiz"]["gun_max"] >= 1
    assert sonuc["esleme"]["karar_sayimi"] == {"belirsiz": 1}


def test_C5_belirsiz_yalnizca_SATIR_TARIHINDEN_ONCEKI_gunleri_etkiler():
    belirsiz = [{"satir": {"tarih": "2021-06-01", "eklenen": "EEE", "cikan": None}}]
    seri = kohort.belirsiz_gun_serisi(belirsiz, ["2021-05-31", "2021-06-01", "2021-06-02"])
    assert seri["2021-05-31"] == ["EEE"]
    assert seri["2021-06-01"] == [] and seri["2021-06-02"] == []


# ======================================================================================
# (5) PIT-PK
# ======================================================================================

def test_D1_bilinen_olay_t_1_ve_t_gununde_DOGRU_yansir(tmp_path):
    d = _duzenek(tmp_path)
    assert kohort.main(_argv(d, "--uygula", "--cikti", str(d["cikti"]))) == 0
    pk = _sonuc_json(d["cikti"])["pit_pk"]
    assert pk["ornek_n"] == 4 and pk["gecti_n"] == 4 and pk["hepsi_gecti"] is True
    kayit = {(o["sembol"], o["yon"]): o for o in pk["detay"]}
    giris = kayit[("EEE", "giris")]
    assert giris["t_1_uye"] is False and giris["t_uye"] is True and giris["gecis_gunu"] == "2021-03-02"
    cikis = kayit[("DDD", "cikis")]
    assert cikis["t_1_uye"] is True and cikis["t_uye"] is False and cikis["gecis_gunu"] == "2021-03-02"


def test_D2_yon_ters_kitaplanirsa_PK_DUSER(tmp_path):
    """Kart olayının yönü tabloyla çelişirse PK o olayda düşmeli — aksi hâlde PK hiçbir şey ölçmez."""
    ters = dict(KART092_MINI)
    ters["bilinen_olaylar"] = [
        {"sembol": "EEE", "yon": "cikis", "tarih": "2021-03-02", "url": "https://example.org/e.pdf"}]
    d = _duzenek(tmp_path)
    d["kart092"] = _kart(tmp_path, "kart092_ters.yaml", ters)
    assert kohort.main(_argv(d, "--uygula", "--cikti", str(d["cikti"]))) == 0
    pk = _sonuc_json(d["cikti"])["pit_pk"]
    assert pk["gecti_n"] == 0 and pk["hepsi_gecti"] is False


def test_D3_tohum_SABIT_ve_ADIYLA_kayitli(tmp_path):
    d = _duzenek(tmp_path)
    assert kohort.main(_argv(d, "--uygula", "--cikti", str(d["cikti"]))) == 0
    pk = _sonuc_json(d["cikti"])["pit_pk"]
    assert pk["tohum_adi"] == "EDG-2026-093"
    assert pk["tohum"] == int(hashlib.sha256(b"EDG-2026-093").hexdigest()[:8], 16)


def test_D4_pencere_disi_olay_OLCULEMEDI_sayilir_uydurulmaz():
    seri = {g: frozenset({"AAA"}) for g in kohort.gunler("2021-01-01", "2021-01-10")}
    pk = kohort.pk_pit(seri, [{"sembol": "ZZZ", "yon": "giris", "tarih": "2030-01-01"}],
                       kohort.gunler("2021-01-01", "2021-01-10"))
    assert pk["detay"][0]["gecti"] is None and pk["olculemedi_n"] == 1
    assert "ölçülemedi" in pk["detay"][0]["neden"]


# ======================================================================================
# (6) ELLE EŞLEME ŞEMASI
# ======================================================================================

def _kayit(karar: str) -> dict:
    return {"satir": {"tarih": "2021-12-01", "eklenen": "EEE", "cikan": None, "satir_no": 1},
            "karar": karar, "gerekce": "Parent Corp spun off Epsilon.", "kaynak": {}}


@pytest.mark.parametrize("karar", ["esle:DDD->EEE", "cift:DDD->EEE", "dusur", "belirsiz"])
def test_E1_sozlukteki_kararlar_KABUL_edilir(karar):
    kohort.esleme_dogrula([_kayit(karar)])


@pytest.mark.parametrize("karar", ["esle", "ESLE:DDD->EEE", "esle:DDD>EEE", "kaldir", "", "yok",
                                   "cift", "cift:DDD>EEE"])
def test_E2_sozluk_disi_karar_REDDEDILIR(karar):
    with pytest.raises(kohort.GirdiHatasi):
        kohort.esleme_dogrula([_kayit(karar)])


def test_E3_eksik_alan_REDDEDILIR():
    kayit = _kayit("belirsiz")
    kayit.pop("gerekce")
    with pytest.raises(kohort.GirdiHatasi, match="eksik alan"):
        kohort.esleme_dogrula([kayit])


def test_E4_ardisik_kitaplama_cifti_CIFT_onerilir_gerekce_TABLODAN(tmp_path):
    d = _duzenek(tmp_path, wikitext=WIKI_TEK_YANLI, uyeler=["AAA", "EEE"], kart093=KART093_GENIS)
    assert kohort.main(_argv(d, "--uygula", "--cikti", str(d["cikti"]),
                             "--bugun", "2022-04-01")) == 0
    metin = (d["cikti"] / "research" / "pit_universe" / "sp400_elle_esleme.yaml").read_text()
    # YAML ÇAPASI YASAK: `&id001`/`*id001` iki kaydı aynı nesneye bağlar ve Rol-1'in bir kaydı
    # elle düzenlemesi ötekini de değiştirmiş gibi görünür (ölçüldü 2026-09-14, ilk koşumda vardı).
    assert "&id" not in metin and "*id" not in metin
    tablo = yaml.safe_load(metin)
    assert len(tablo) == 2
    # TUR-2: iki YARIM SATIR eşlemesi ARTIK `cift:` — `esle:` yeniden adlandırma kimliğine
    # ayrıldı ve as-of yürütmede UYGULANIR; aynı jetonu iki farklı davranışa vermek tuzaktı.
    assert {k["karar"] for k in tablo} == {"cift:DDD->EEE"}
    for k in tablo:
        assert "spun off" in k["gerekce"] and "Market capitalization" in k["gerekce"]
        assert k["kaynak"]["urller"]


def test_E5_cift_karari_degisiklik_listesini_DEGISTIRMEZ(tmp_path):
    """`cift:` bir ANOTASYONDUR: iki yarım satırın aynı olaya ait olduğunu kaydeder, sembolleri
    YENİDEN YAZMAZ. Yazsaydı `cift:AMCX->CNXC` AMCX'i kohorttan tamamen silerdi (ölçüldü)."""
    degisiklikler = [{"tarih": "2021-12-02", "eklenen": None, "cikan": "DDD", "satir_no": 0,
                      "alt_no": 0},
                     {"tarih": "2021-12-01", "eklenen": "EEE", "cikan": None, "satir_no": 1,
                      "alt_no": 0}]
    tablo = [{"satir": {"satir_no": 0, "alt_no": 0, "tarih": "2021-12-02", "eklenen": None,
                        "cikan": "DDD"},
              "karar": "cift:DDD->EEE", "gerekce": "x", "kaynak": {}}]
    kalan, belirsiz, rapor = kohort.esleme_uygula(degisiklikler, tablo)
    assert [(r.get("eklenen"), r.get("cikan")) for r in kalan] == [(None, "DDD"), ("EEE", None)]
    assert belirsiz == [] and rapor["uygulanan_esleme_n"] == 0


def test_E6_dusur_karari_degisikligi_LISTEDEN_CIKARIR():
    degisiklikler = [{"tarih": "2021-12-01", "eklenen": "EEE", "cikan": None, "satir_no": 7},
                     {"tarih": "2021-11-01", "eklenen": "AAA", "cikan": "BBB", "satir_no": 8}]
    tablo = [{"satir": {"satir_no": 7, "tarih": "2021-12-01", "eklenen": "EEE", "cikan": None},
              "karar": "dusur", "gerekce": "x", "kaynak": {}}]
    kalan, belirsiz, _ = kohort.esleme_uygula(degisiklikler, tablo)
    assert [r["satir_no"] for r in kalan] == [8] and belirsiz == []


def test_E7_esleme_dosyasi_URETICI_CIKTISIDIR_yeniden_uretilir(tmp_path):
    """TUR-2: yaml ÜRETİLMİŞ dosyadır — her `--uygula` onu YENİDEN ÜRETİR. Elle düzenlenmiş bir
    karar tablosu `--esleme` ile AÇIK yoldan verilir (üretilmiş dosyayı elle düzenleme yasağı)."""
    d = _duzenek(tmp_path, wikitext=WIKI_TEK_YANLI, uyeler=["AAA", "EEE"], kart093=KART093_GENIS)
    yol = d["cikti"] / "research" / "pit_universe" / "sp400_elle_esleme.yaml"
    yol.parent.mkdir(parents=True, exist_ok=True)
    yol.write_text("- bozuk: kayit\n", encoding="utf-8")

    assert kohort.main(_argv(d, "--uygula", "--cikti", str(d["cikti"]),
                             "--bugun", "2022-04-01")) == 0
    tablo = yaml.safe_load(yol.read_text(encoding="utf-8"))
    assert {k["karar"] for k in tablo} == {"cift:DDD->EEE"}
    assert _sonuc_json(d["cikti"])["esleme"]["kaynak"] == "mekanik öneri (yeniden üretildi)"


def test_E8_esleme_ACIK_yoldan_verilince_OKUNUR(tmp_path):
    d = _duzenek(tmp_path, wikitext=WIKI_TEK_YANLI, uyeler=["AAA", "EEE"], kart093=KART093_GENIS)
    elle = tmp_path / "elle.yaml"
    elle.write_text(yaml.safe_dump(
        [{"satir": {"tarih": "2021-12-01", "eklenen": "EEE", "cikan": None, "satir_no": 1,
                    "alt_no": 0},
          "karar": "belirsiz", "gerekce": "Rol-1 kararı", "kaynak": {}},
         {"satir": {"tarih": "2021-12-02", "eklenen": None, "cikan": "DDD", "satir_no": 0,
                    "alt_no": 0},
          "karar": "belirsiz", "gerekce": "Rol-1 kararı", "kaynak": {}}],
        allow_unicode=True), encoding="utf-8")
    kohort.main(_argv(d, "--uygula", "--cikti", str(d["cikti"]), "--esleme", str(elle),
                      "--bugun", "2022-04-01"))
    sonuc = _sonuc_json(d["cikti"])
    assert sonuc["esleme"]["kaynak"] == "dosyadan okundu"
    assert sonuc["esleme"]["karar_sayimi"] == {"belirsiz": 2}


# ======================================================================================
# (7) --kuru HİÇBİR DOSYA YAZMAZ
# ======================================================================================

def test_F1_kuru_kosum_hicbir_dosya_yazmaz(tmp_path):
    d = _duzenek(tmp_path)
    d["cikti"].mkdir()
    assert kohort.main(_argv(d, "--kuru", "--cikti", str(d["cikti"]))) == 0
    assert list(d["cikti"].rglob("*")) == [], "kuru koşum dosya YAZDI"


def test_F2_uygula_cikti_olmadan_REDDEDILIR(tmp_path):
    d = _duzenek(tmp_path)
    with pytest.raises(SystemExit):
        kohort.main(_argv(d, "--uygula"))


def test_F3_kip_bayragi_ZORUNLU(tmp_path):
    d = _duzenek(tmp_path)
    with pytest.raises(SystemExit):
        kohort.main(_argv(d))


# ======================================================================================
# (8) TEK-KAYNAK
# ======================================================================================

def test_G1_as_of_EDG075ten_ITHAL_kopya_degil():
    """`as_of` ve tablo ayrıştırıcısı üreticide YENİDEN YAZILMAZ: biri EDG-075, öteki EDG-092
    betiğinden gelir. Kimlik dosya yolundan ölçülür — `kaynaktan_yukle` her çağrıda TAZE kod
    nesnesi üretir, o yüzden `is` ile kod nesnesi karşılaştırması yanıltıcı olurdu."""
    assert pathlib.Path(kohort.ORTAK.__file__).parts[-2:] == ("edg075_sp500_tarihsel", "olcum.py")
    assert pathlib.Path(kohort.OLC.__file__).parts[-2:] == ("edg092_sp400_uyelik", "olc.py")
    assert callable(kohort.ORTAK.as_of)
    kaynak = KOHORT_YOLU.read_text(encoding="utf-8")
    assert "def as_of" not in kaynak, "as_of üreticide YENİDEN YAZILMIŞ (tek-kaynak ihlali)"
    assert "def tabloyu_ayristir" not in kaynak, "ayrıştırıcı KOPYALANMIŞ (tek-kaynak ihlali)"


def test_G2_uretici_meridiani_ITHAL_ETMEZ():
    kaynak = KOHORT_YOLU.read_text(encoding="utf-8")
    for satir in kaynak.splitlines():
        s = satir.strip()
        assert not (s.startswith("import meridian") or s.startswith("from meridian")), satir


# ======================================================================================
# (10) TUR-2 — ÇOK SEMBOLLÜ HÜCRE BÖLÜNÜR
# ======================================================================================

@pytest.mark.parametrize("hucre, beklenen, bolundu", [
    ("UA/UAA", ["UA", "UAA"], True),
    ("UAA/UA", ["UAA", "UA"], True),
    ("AAX, AAY", ["AAX", "AAY"], True),
    ("BRK-B", ["BRK-B"], False),
    ("AAA", ["AAA"], False),
    (None, [], False),
    # Ticker biçimine UYMAYAN parça varsa hücre BÖLÜNMEZ ve durum raporlanır (uydurma yok).
    ("ALPHA CORP/BETA CORP", ["ALPHA CORP/BETA CORP"], False),
])
def test_I1_sembolleri_bol_ayiracla_boler_ticker_disini_BOLMEZ(hucre, beklenen, bolundu):
    assert kohort.sembolleri_bol(hucre) == (beklenen, bolundu)


def test_I2_cok_sembollu_hucre_IKI_AYRI_SEMBOL_uretir(tmp_path):
    """`AAX/AAY` hücresi iki satır üretir; bölünmezse kohortta `AAX/AAY` hayalet sembolü kalırdı."""
    d = _duzenek(tmp_path, wikitext=WIKI_COK_SEMBOL, uyeler=["AAA", "AAX", "AAY"],
                 kart093=KART093_GENIS)
    assert kohort.main(_argv(d, "--uygula", "--cikti", str(d["cikti"]))) == 0
    metin = (d["cikti"] / "research" / "pit_universe" / "sp400_uyelik_tarihi.csv").read_text()
    semboller = {s for satir in list(csv.reader(io.StringIO(metin)))[1:] for s in satir[1].split(",")}
    assert "AAX/AAY" not in semboller, "çok-sembollü hücre BÖLÜNMEDİ — hayalet ticker kohorta girdi"
    assert {"AAX", "AAY", "DDD"} <= semboller
    sonuc = _sonuc_json(d["cikti"])
    assert sonuc["cok_sembollu_hucre"]["bolunen_n"] == 1
    assert sonuc["cok_sembollu_hucre"]["bolunen"][0]["semboller"] == ["AAX", "AAY"]
    # Bölünme ÖNCESİ gün: iki sınıf da üye DEĞİL; SONRASI: ikisi de üye.
    satirlar = {r[0]: set(r[1].split(",")) for r in list(csv.reader(io.StringIO(metin)))[1:]}
    ilk = satirlar[min(satirlar)]
    assert "AAX" not in ilk and "AAY" not in ilk and "DDD" in ilk


def test_I3_cikan_sutunundaki_cok_sembollu_hucre_csvye_SIZMAZ(tmp_path):
    """Hücre ÇIKAN sütunundaysa geri sarma onu kümeye EKLER — bölünmezse hayalet ticker doğrudan
    csv'ye girer (gerçek tabloda tam olarak bu oldu: `UAA/UA` çıkışı 146 satıra sızmıştı)."""
    d = _duzenek(tmp_path, wikitext=WIKI_COK_SEMBOL_CIKAN, uyeler=["AAA", "EEE"],
                 kart093=KART093_GENIS)
    assert kohort.main(_argv(d, "--uygula", "--cikti", str(d["cikti"]))) == 0
    metin = (d["cikti"] / "research" / "pit_universe" / "sp400_uyelik_tarihi.csv").read_text()
    semboller = {s for r in list(csv.reader(io.StringIO(metin)))[1:] for s in r[1].split(",")}
    assert "AAX/AAY" not in semboller and {"AAX", "AAY"} <= semboller
    sonuc = _sonuc_json(d["cikti"])
    assert sonuc["cok_sembollu_hucre"]["csv_ayirac_tasiyan_satir_n"] == 0
    assert sonuc["cok_sembollu_hucre"]["csv_ayirac_tasiyan_semboller"] == []


# ======================================================================================
# (11) TUR-2 — YENİDEN ADLANDIRMA (`esle:`) TABLONUN KENDİ GEREKÇESİNDEN, UYGULANIR
# ======================================================================================

def test_J1_acik_yeniden_adlandirma_ESLE_onerilir_gerekce_TABLODAN(tmp_path):
    d = _duzenek(tmp_path, wikitext=WIKI_RENAME, uyeler=["AAA", "PPP"], kart093=KART093_GENIS)
    assert kohort.main(_argv(d, "--uygula", "--cikti", str(d["cikti"]),
                             "--bugun", "2023-01-01")) == 0
    tablo = yaml.safe_load(
        (d["cikti"] / "research" / "pit_universe" / "sp400_elle_esleme.yaml").read_text())
    kayit = [k for k in tablo if k["karar"].startswith("esle:")]
    assert len(kayit) == 1 and kayit[0]["karar"] == "esle:OOO->NNN"
    assert "changed its name and symbol" in kayit[0]["gerekce"]
    assert kayit[0]["satir"]["etkisiz_semboller"] == ["OOO"]


def test_J2_gerekce_ACIK_degilse_karar_BELIRSIZ_kalir(tmp_path):
    """MDY'de `NNN` var / `OOO` yok bilgisi TANIdır, KARAR GEREKÇESİ OLAMAZ (tek kaynak tablo)."""
    d = _duzenek(tmp_path, wikitext=WIKI_RENAME_GEREKCESIZ, uyeler=["AAA", "PPP"],
                 kart093=KART093_GENIS)
    assert kohort.main(_argv(d, "--uygula", "--cikti", str(d["cikti"]),
                             "--bugun", "2023-01-01")) == 0
    tablo = yaml.safe_load(
        (d["cikti"] / "research" / "pit_universe" / "sp400_elle_esleme.yaml").read_text())
    assert [k["karar"] for k in tablo] == ["belirsiz"]
    sonuc = _sonuc_json(d["cikti"])
    assert sonuc["esleme"]["karar_sayimi"] == {"belirsiz": 1}
    assert sonuc["belirsiz"]["gun_max"] == 1


def test_J2b_borsa_parantezi_TEK_BASINA_eslemeye_yetmez(tmp_path):
    """Gerekçede sembol GEÇİYOR ama yeniden adlandırma ANLATILMIYOR → `belirsiz`. Metinde sembol
    görmek eşleme gerekçesi olsaydı, satın alma/spin-off satırları da yanlışlıkla eşlenirdi."""
    d = _duzenek(tmp_path, wikitext=WIKI_RENAME_PARANTEZ, uyeler=["AAA", "PPP"],
                 kart093=KART093_GENIS)
    assert kohort.main(_argv(d, "--uygula", "--cikti", str(d["cikti"]),
                             "--bugun", "2023-01-01")) == 0
    tablo = yaml.safe_load(
        (d["cikti"] / "research" / "pit_universe" / "sp400_elle_esleme.yaml").read_text())
    assert [k["karar"] for k in tablo] == ["belirsiz"]


def test_J3_esle_karari_AS_OF_YURUTMESINDE_uygulanir(tmp_path):
    """`esle:OOO->NNN` uygulanmazsa `NNN` pencere başında HAYALET üye kalır (etkisiz discard)."""
    d = _duzenek(tmp_path, wikitext=WIKI_RENAME, uyeler=["AAA", "PPP"], kart093=KART093_GENIS)
    assert kohort.main(_argv(d, "--uygula", "--cikti", str(d["cikti"]),
                             "--bugun", "2023-01-01")) == 0
    metin = (d["cikti"] / "research" / "pit_universe" / "sp400_uyelik_tarihi.csv").read_text()
    satirlar = {r[0]: set(r[1].split(",")) for r in list(csv.reader(io.StringIO(metin)))[1:]}
    ilk = satirlar[min(satirlar)]
    assert ilk == {"AAA", "QQQ"}, f"eşleme UYGULANMADI — pencere başı {sorted(ilk)}"
    sonuc = _sonuc_json(d["cikti"])
    assert sonuc["esleme"]["uygulanan_esleme_n"] == 1
    assert sonuc["esleme"]["karar_sayimi"].get("esle") == 1


def test_J4_esle_YALNIZ_kendi_satirina_uygulanir():
    """Sembol ikamesi TABLO GENELİNDE değil, kararın BAĞLI OLDUĞU satırda yapılır — küresel ikame
    aynı sembolü taşıyan alakasız satırları (ör. bir spin-off'un yeni hissesini) bozardı."""
    degisiklikler = [{"tarih": "2022-06-01", "eklenen": "OOO", "cikan": "QQQ", "satir_no": 3,
                      "alt_no": 0},
                     {"tarih": "2021-06-01", "eklenen": "OOO", "cikan": "RRR", "satir_no": 9,
                      "alt_no": 0}]
    tablo = [{"satir": {"satir_no": 3, "alt_no": 0, "tarih": "2022-06-01", "eklenen": "OOO",
                        "cikan": "QQQ"},
              "karar": "esle:OOO->NNN", "gerekce": "x", "kaynak": {}}]
    kalan, _, rapor = kohort.esleme_uygula(degisiklikler, tablo)
    assert [r["eklenen"] for r in kalan] == ["NNN", "OOO"]
    assert rapor["uygulanan_esleme_n"] == 1 and rapor["uygulanmayan_esleme"] == []


def test_J5_esle_satirda_karsiligi_YOKSA_sessizce_gecmez():
    """Uygulanamayan bir eşleme SESSİZCE yutulmaz — raporda ADIYLA durur (Yasa 4 ruhu)."""
    degisiklikler = [{"tarih": "2022-06-01", "eklenen": "XXX", "cikan": "YYY", "satir_no": 3,
                      "alt_no": 0}]
    tablo = [{"satir": {"satir_no": 3, "alt_no": 0, "tarih": "2022-06-01", "eklenen": "XXX",
                        "cikan": "YYY"},
              "karar": "esle:OOO->NNN", "gerekce": "x", "kaynak": {}}]
    _, _, rapor = kohort.esleme_uygula(degisiklikler, tablo)
    assert rapor["uygulanan_esleme_n"] == 0
    assert rapor["uygulanmayan_esleme"] == [{"satir_no": 3, "alt_no": 0, "karar": "esle:OOO->NNN"}]


def test_J6_belirsiz_ETKISIZ_SEMBOLU_sayar_satirin_ilk_hucresini_degil():
    """Etkisiz adım satırında belirsiz olan sembol, satırın `eklenen`i değil ETKİSİZ olandır
    (ör. `OMCL↑/COHR↓` satırında belirsiz olan `COHR`)."""
    belirsiz = [{"satir": {"tarih": "2022-07-05", "eklenen": "OMCL", "cikan": "COHR",
                           "etkisiz_semboller": ["COHR"]}}]
    seri = kohort.belirsiz_gun_serisi(belirsiz, ["2022-07-04", "2022-07-05"])
    assert seri["2022-07-04"] == ["COHR"] and seri["2022-07-05"] == []


# ======================================================================================
# (9) GERÇEK GİRDİ — ham `.gitignore`'lu, CI'da YOK
# ======================================================================================

@pytest.mark.skipif(not (GERCEK_HAM.exists() and GERCEK_XLSX.exists()),
                    reason="ham wikitext / MDY xlsx yerelde yok (.gitignore — CI'da bulunmaz)")
def test_H1_gercek_girdilerle_TAM_kosum_kapilari_gecer(tmp_path):
    cikti = tmp_path / "cikti"
    rc = kohort.main(["--uygula", "--cikti", str(cikti), "--ham", str(GERCEK_HAM),
                      "--xlsx", str(GERCEK_XLSX), "--bugun", "2026-09-14"])
    assert rc == 0
    sonuc = _sonuc_json(cikti)
    esikler = sonuc["esikler"]["kohort_boyut_bant"]
    assert esikler[0] <= sonuc["kohort"]["boyut_min"]
    assert sonuc["kohort"]["boyut_max"] <= esikler[1]
    assert sonuc["kohort"]["bant_disi_gun_n"] == 0
    assert sonuc["belirsiz"]["gun_max"] <= sonuc["esikler"]["belirsiz_isim_gun_ust"]
    assert sonuc["pit_pk"]["ornek_n"] == kohort.PK_OLAY_N
    assert sonuc["pit_pk"]["hepsi_gecti"] is True
    assert sonuc["hukum"] == "YOK — Rol-1"
    metin = (cikti / "research" / "pit_universe" / "sp400_uyelik_tarihi.csv").read_text()
    o = _sozlesme_olc(metin)
    assert o["baslik"] == ["date", "tickers"]
    assert o["artan"] and o["tekrarsiz"] and o["sirali"] and not o["ic_tekrar"]
    assert not o["ardisik_ayni"]
    assert dt.date.fromisoformat(o["tarihler"][0]) == dt.date(2020, 7, 27)
    # TUR-2 KANITI: gerçek tabloda `UA/UAA` ve `UAA/UA` hücreleri vardı ve bölünmeden 163 csv
    # satırının 146'sında hayalet ticker olarak duruyordu (inceleme ölçümü, 2026-09-14).
    semboller = {s for r in list(csv.reader(io.StringIO(metin)))[1:] for s in r[1].split(",")}
    assert not [s for s in semboller if "/" in s], "çok-sembollü hücre csv'ye SIZDI"
    assert {"UA", "UAA"} <= semboller, "iki hisse sınıfı da AYRI üye olmalı"
    assert sonuc["cok_sembollu_hucre"]["csv_ayirac_tasiyan_satir_n"] == 0
    assert sonuc["cok_sembollu_hucre"]["bolunen_n"] == 2


@pytest.mark.skipif(not (GERCEK_HAM.exists() and GERCEK_XLSX.exists()),
                    reason="ham wikitext / MDY xlsx yerelde yok (.gitignore — CI'da bulunmaz)")
def test_H2_gercek_tabloda_ACIK_yeniden_adlandirma_ESLENIR_kalani_BELIRSIZ(tmp_path):
    """Gerçek tabloda AÇIKÇA yazan tek yeniden adlandırma `HTA→HR`dir (gerekçe: "changed its name
    and symbol to … (NYSE: HR)"). `CHK`/`BRKS` sınıfı gerekçe hücresinde SEMBOL vermez → belirsiz
    KALIR; MDY'deki varlık/yokluk karar gerekçesi OLAMAZ."""
    cikti = tmp_path / "cikti"
    assert kohort.main(["--uygula", "--cikti", str(cikti), "--ham", str(GERCEK_HAM),
                        "--xlsx", str(GERCEK_XLSX), "--bugun", "2026-09-14"]) == 0
    tablo = yaml.safe_load(
        (cikti / "research" / "pit_universe" / "sp400_elle_esleme.yaml").read_text())
    esle = [k["karar"] for k in tablo if k["karar"].startswith("esle:")]
    assert esle == ["esle:HTA->HR"]
    belirsiz = {s for k in tablo if k["karar"] == "belirsiz"
                for s in (k["satir"].get("etkisiz_semboller") or [])}
    assert {"CHK", "BRKS", "PSTG"} <= belirsiz, "açık olmayan vakalar UYDURULMUŞ"


@pytest.mark.skipif(not (GERCEK_HAM.exists() and GERCEK_XLSX.exists()),
                    reason="ham wikitext / MDY xlsx yerelde yok (.gitignore — CI'da bulunmaz)")
def test_H3_cift_kararli_CIKAN_isimler_kohortta_DURUYOR(tmp_path):
    """`cift:` ANOTASYON kalmalı: uygulansaydı çıkan isim (ör. `AMCX`) çıkış tarihinden ÖNCEKİ
    günlerde de kohorttan silinirdi. Boyut bandı bu bozulmayı YUTAR (birkaç isimlik kayma) —
    o yüzden bant değil, İSİM düzeyinde ölçülür."""
    cikti = tmp_path / "cikti"
    assert kohort.main(["--uygula", "--cikti", str(cikti), "--ham", str(GERCEK_HAM),
                        "--xlsx", str(GERCEK_XLSX), "--bugun", "2026-09-14"]) == 0
    metin = (cikti / "research" / "pit_universe" / "sp400_uyelik_tarihi.csv").read_text()
    satirlar = [(r[0], set(r[1].split(","))) for r in list(csv.reader(io.StringIO(metin)))[1:]]

    def _uye(sembol: str, gun: str) -> bool:
        return sembol in [k for t, k in satirlar if t <= gun][-1]

    # Tablonun KENDİ çıkış tarihleri (`cift:` kararlarının çıkan ucu) — bir gün ÖNCESİNDE üye.
    for sembol, cikis in (("AMCX", "2020-12-02"), ("STRA", "2021-08-03"), ("PRG", "2022-04-06"),
                          ("BFH", "2022-11-02"), ("PACW", "2023-04-05"), ("KSS", "2023-10-03")):
        onceki = (dt.date.fromisoformat(cikis) - dt.timedelta(days=1)).isoformat()
        assert _uye(sembol, onceki), f"{sembol} çıkışından önce kohortta YOK — `cift:` uygulanmış"
        assert not _uye(sembol, cikis), f"{sembol} çıkış gününde hâlâ kohortta"
