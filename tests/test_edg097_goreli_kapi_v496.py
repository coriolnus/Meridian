"""tests/test_edg097_goreli_kapi_v496.py — EDG-2026-097 / EDG-2026-098 KART-PARAMETRELİ KAPILAR
(karşılaştırma betiğinin şemaları: A kipi mutlak ↔ göreli ↔ göreli-yalnız-anlamlı, katman i
taban ↔ kip listesi).

vNNN KİMLİK KAYDI: ölçüm anında (2026-09-15) `grep -rl v496 tests/ ops/ meridian/ research/
docs/` BOŞ döndü — çakışma yok, taşıma yok (CLAUDE.md §2 vNNN kimlik kuralı).

NE ÇİVİLER. EDG-2026-096 hükmü (KALDI—KAPI) iki kapının YANLIŞ BİRİMDE olduğunu ölçtü: (1) A
kipi ≡ PK-1 bit-eşitliği (1e-6) canlı-tazelenen bar tabanına karşı tutmaz; (2) katman i PK
tabanı (0,003) as-of değerinden türetilmişti, sabit-251 evrenine uygulanamazdı. Ardıl kart
EDG-2026-097 aynı iki soruyu BAŞKA BİRİMDE sorar: göreli tolerans + desen eşitliği, ve kipe
uygun PK (yalnız as-of/güncel-liste). Eşik YERİNDE DÜZELTİLMEZ — iki kart AYNI betikle koşar ve
betik hangi kapıyı kuracağını KARTIN EŞİK ADLARINDAN öğrenir.

Ölçülen şey SAYILAR DEĞİL (onlar gerçek veriyle A1'de doğar), SÖZLEŞMELERDİR:
  T1 — 097 kartıyla A kipi kapısı GÖRELİDİR: bacak başına `goreli_fark = |A−PK1| / |PK1|`,
       `yon_esit`, `ci0_disi_esit`; üçü birlikte geçer. PK-1 değeri SIFIRSA oran TANIMSIZDIR
       (None + neden), UYDURULMAZ.
  T2 — 097 kartıyla katman i kapısı bir KİP LİSTESİDİR: listede olmayan kip raporlanır ama
       kapıya GİRMEZ (`kapida: false`); listedeki bir kip CI-0-içiyse kapı DÜŞER.
  T3 — REGRESYON: 096 kartıyla eski iki kapı (mutlak tolerans + sayısal taban) BİREBİR durur.
  T4 — çıktı hangi şemayla koştuğunu BEYAN eder (`kapi_semasi`) ve kart kimliğini KARTTAN alır.
  T5 — bilinmeyen/eksik/çelişen eşik adı ÇIKIŞ 2'dir: varsayılan UYDURULMAZ.
  T6 — kill-list metinleri KARTIN KENDİ CÜMLELERİDİR; 096'da olup 097'de OLMAYAN kalem
       "kart bu kalemi taşımıyor" diye ADIYLA sayılır, sessizce kaybolmaz.
  T7 — GERÇEK EDG-096 çıktısı (env `EDG096_CIKTI`, yoksa skip) 097 kartıyla yeniden okunur:
       kapı mantığının gerçek sayılar üzerinde ne DEDİĞİNİN kanıtı. Hüküm YOK — Rol-1'in.
  T8 — AYNI gerçek çıktı 098 kartıyla (env `EDG096_CIKTI`, yoksa skip): göreli tolerans YALNIZ
       PK-1'in CI-0-DIŞI bacaklarına uygulanır. PK-1 referansı A1 koşumunun okuduğu dosyanın
       DEPODAKİ kopyasıdır ve sha256'sı gerçek çıktının künyesinden DOĞRULANIR — `pk1_anlamli`
       uydurulmaz. T8d karşıtlık çivisidir: AYNI girdi 097 kartıyla DÜŞER (birim değişti, veri
       değil).
  T9 — sentetik: CI-0-İÇİ bacakta %50 fark GEÇER (desen eşit), CI-0-DIŞI bacakta %6 DÜŞER,
       desen farkı tolerans uygulanmayan bacakta da DÜŞÜRÜR, hiçbir bacak anlamlı değilse
       eşiğin değeri None + NEDEN, `pk1_anlamli` yoksa bacak "geçti" SAYILMAZ.
  T10 — ayar alanı YOK ya da FALSE ise tur-1 (EDG-097) davranışı AYNEN; ayar mutlak şemayla ya
       da bayrak olmayan bir değerle gelirse ÇIKIŞ 2 (okunmayan ayar sessizce ölmez).
  T11 — beyan: RAPOR "Göreli uygulandı" sütununu ve İKİ maksimumu taşır; 097 raporuna SIZMAZ.
  T12 — AYRIŞMA ÇİVİSİ: EDG-2026-098 kartı depoya girdiği gün eşik/kill-list fikstürü onunla
       karşılaştırılır (kart yoksa skip — kartı Rol-1 koyar, ajan karta DOKUNMAZ).

BU DOSYA ÖLÇÜM KOŞMAZ: `k093` çalıştırılmaz, ağa çıkılmaz, kart dosyasına YAZILMAZ (yalnız
OKUNUR — eşik ve kill-list metni oradan gelir). T7 yalnız HAZIR çıktı dosyalarını okur.

FİKSTÜR TEK KAYNAKTAN: bacak/sonuç üreticileri v495'ten İTHAL EDİLİR, buraya KOPYALANMAZ —
kopya, üreticinin alan adları değiştiğinde sessizce ayrışır ve bu dosya "temiz" derdi
(tek-kaynak yasası, CLAUDE.md §4). PK-1 referans üreticisi BURADA ayrıca yazılır: v495'inki
`pk1_anlamli`yi sabit True verir, bu dosyanın sorduğu soru ise TAM OLARAK o alanın A kipiyle
eşleşip eşleşmediğidir (aynı ad değil, farklı sözleşme).

MUTASYON KANITI (bu dosyada KOŞMAZ, rapora yazılır — CLAUDE.md §6): her çivinin ısırdığı dal
rapor tablosundadır (şema seçimi, göreli oran, üçlü VE, kip listesi, eşik adı doğrulaması,
toleransın uygulandığı bacak kümesi, iki maksimum, ayar doğrulaması, rapor sütunu).
"""
from __future__ import annotations

import hashlib
import json
import os
import pathlib

import pytest
import yaml

from tests.conftest import betikten_modul_yukle
from tests.test_edg096_uyelik_kipi_v495 import KARSILASTIR, _sonuc

REPO = pathlib.Path(__file__).resolve().parents[1]
KARTLAR = REPO / "research" / "cards"
KART096 = KARTLAR / "EDG-2026-096-edg016-katman-ii-sagkalan-yanliligi.yaml"
KART097 = KARTLAR / "EDG-2026-097-edg016-katman-ii-sagkalan-goreli-tutarlilik.yaml"

#: EDG-093 PK-1 referans değerleri (kart `esikler` şerhinde yazılı olan altı bacağın @20
#: ucu). Burada SABİT olmaları ölçüm değil FİKSTÜRDÜR: sınanan şey oranın hesabıdır.
REF_I, REF_A1, REF_IIB = 0.006211, 0.004406, 0.0084


@pytest.fixture(scope="module")
def k096_modul():
    """Karşılaştırma betiği İTHAL EDİLİR (modül düzeyi temiz: argparse ana akışın içinde).
    Yükleme şasi yükleyicisiyledir — ham exec_module `__pycache__`e bakar ve boyut-koruyan bir
    düzenlemede BAYAT bytecode koşar (v334 sınıfı)."""
    return betikten_modul_yukle(KARSILASTIR, "v496_karsilastir096_modul")


def _pk1_ref(i20=REF_I, a1_20=REF_A1, iib_20=REF_IIB,
             i_anlamli=True, a1_anlamli=False, iib_anlamli=False):
    """EDG-093 sonucunun PK-1 detay bloğu — BACAK BAŞINA değer VE CI-0-dışılık.

    v495'in üreticisinden ayrı yazılır: orada `pk1_anlamli` sabit True'dur, burada sınanan şey
    tam olarak o alanın A kipiyle EŞLEŞMESİDİR. Varsayılanlar v495 `_sonuc` üreticisinin
    varsayılan CI-0-dışılık desenine (i: EVET, ii_a1: hayır, ii_b: hayır) UYAR — desen farkı
    ancak BİLEREK bozulduğunda görünsün diye."""
    detay = []
    for bacak, d20, anl in (("i_ust20_kohort_fazlasi", i20, i_anlamli),
                            ("ii_a1_kova_tabanli_fazla", a1_20, a1_anlamli),
                            ("ii_b_artik_ic_fazla", iib_20, iib_anlamli)):
        for ufuk, v in (("10", d20 / 2), ("20", d20)):
            detay.append({"bacak": bacak, "ufuk": ufuk, "pk1_deger": v, "pk1_anlamli": anl,
                          "edg016_deger": v, "yon_esit": True, "edg016_anlamli": anl,
                          "ci0_disi_esit": True})
    return {"kart": "EDG-2026-093", "damga_utc": "20260914T191231Z",
            "pk": {"pk1": {"kosdu": True, "detay": detay}}}


def _yaz(kok: pathlib.Path, ad: str, veri) -> pathlib.Path:
    p = kok / f"{ad}.json"
    p.write_text(json.dumps(veri, ensure_ascii=False), encoding="utf-8")
    return p


def _kosum(mod, kok: pathlib.Path, kart, ad: str, asof, guncel=None, sabit=None, pk1=None):
    """Betiği OPERATÖRÜN ÇAĞIRDIĞI BİÇİMDE (komut satırı sözleşmesi) koşar ve sonucu okur.

    Her koşum KENDİ çıktı dizinine yazar: damga saniye çözünürlüklüdür, aynı dizinde iki koşum
    aynı adı taşıyabilir ve ikinci sonuç birincinin üstüne yazardı."""
    cikti = kok / f"cikti_{ad}"
    argv = ["--asof", str(asof), "--kart", str(kart), "--cikti", str(cikti)]
    for bayrak, yol in (("--guncel", guncel), ("--sabit", sabit), ("--pk1-referans", pk1)):
        if yol is not None:
            argv += [bayrak, str(yol)]
    assert mod.main(argv) == 0
    jsonlar = sorted(cikti.glob("sonuc_096_*.json"))
    assert len(jsonlar) == 1, f"tek sonuç json beklendi: {jsonlar}"
    return json.loads(jsonlar[0].read_text(encoding="utf-8")), cikti


def _sabit_kunyesi(oran=0.05):
    return {"kaynak": "sınav", "n": 20, "sha256": "0" * 64, "kapsam_disi_n": 1,
            "kapsam_disi_oran": oran, "kapsam_disi_ornek": ["ZZA"], "neden": None}


@pytest.fixture
def uc_kip(tmp_path, sandbox_state):
    """Üç kip sonucu için üretici — çağıran A kipini ve CI-0-dışılık desenini seçer.

    B/C kipleri SABİTTİR (ii_b @20 eşiği geçer): bu dosyanın sorduğu soru A kipi kapısı ve
    katman i kapısıdır, hipotez kolu v495'in konusudur."""
    def kur(ad, a_i, a_a1, a_iib, a_i_anlamli=True, a_iib_anlamli=False,
            sabit_i_anlamli=True, guncel_i_anlamli=True, pk1=None):
        kok = tmp_path / ad
        kok.mkdir()
        yollar = {"kok": kok}
        yollar["asof"] = _yaz(kok, "asof", _sonuc("asof", a_i, a_a1, a_iib,
                                                  iib_anlamli=a_iib_anlamli,
                                                  i20_anlamli=a_i_anlamli))
        yollar["guncel"] = _yaz(kok, "guncel", _sonuc("guncel", 0.00644, 0.005512, 0.0283, True,
                                                      i20_anlamli=guncel_i_anlamli))
        yollar["sabit"] = _yaz(kok, "sabit", _sonuc("sabit", 0.002944, 0.005776, 0.0274, True,
                                                    kunye=_sabit_kunyesi(),
                                                    i20_anlamli=sabit_i_anlamli))
        yollar["pk1"] = _yaz(kok, "pk1", pk1 if pk1 is not None else _pk1_ref())
        return yollar
    return kur


# =================================================================================================
# T1 — 097: A KİPİ KAPISI GÖRELİDİR (oran + yön + CI-0-dışılık deseni)
# =================================================================================================
def _a_kapisi(mod, yollar, kart=KART097, ad="a"):
    sonuc, _ = _kosum(mod, yollar["kok"], kart, ad, yollar["asof"], yollar["guncel"],
                      yollar["sabit"], yollar["pk1"])
    return sonuc


def test_T1a_GORELI_KAPI_YUZDE_BIR_FARKI_GECER(k096_modul, uc_kip):
    """A kipi PK-1'den %1 AYRILIR: mutlak fark 1e-6 toleransını KAT KAT aşar ama GÖRELİ fark
    %5'in altındadır → kapı GEÇER. EDG-096'nın düştüğü yer tam burasıydı (bit-eşitlik yanlış
    birimdi); 097 bu farkı geçirmeli, yoksa ardıl kartın varlık sebebi ölçülmemiş olur."""
    y = uc_kip("t1a", REF_I * 1.01, REF_A1 * 1.01, REF_IIB * 1.01)
    s = _a_kapisi(k096_modul, y, ad="t1a")
    kapi = s["a_kipi_pk1_kapisi"]
    assert kapi["sema"] == "goreli"
    assert kapi["kiyaslanan_bacak_n"] == 6
    assert kapi["gecti"] is True, kapi
    assert abs(kapi["maks_goreli_fark"] - 0.01) < 1e-9, kapi["maks_goreli_fark"]
    assert kapi["maks_mutlak_fark"] > 1e-6, "mutlak fark eski toleransı aşmalıydı (fikstür bozuk)"
    for r in kapi["detay"]:
        assert abs(r["goreli_fark"] - 0.01) < 1e-9, r
        assert r["yon_esit"] is True and r["ci0_disi_esit"] is True and r["gecti"] is True
    assert s["esikler"]["a_kipi_pk1_goreli_tol"]["gecti"] is True
    assert abs(s["esikler"]["a_kipi_pk1_goreli_tol"]["deger"] - 0.01) < 1e-9
    assert not s["kill_list_tetik"], s["kill_list_tetik"]


def test_T1b_GORELI_KAPI_YUZDE_ALTI_FARKI_DUSURUR(k096_modul, uc_kip):
    """%6 göreli fark kartın %5 toleransını AŞAR → kapı DÜŞER ve kill-list kalemi tetiklenir.
    Düşmeseydi doğrulanmamış bir kod/veri yolundan sayı yayılırdı."""
    y = uc_kip("t1b", REF_I * 1.06, REF_A1 * 1.06, REF_IIB * 1.06)
    s = _a_kapisi(k096_modul, y, ad="t1b")
    kapi = s["a_kipi_pk1_kapisi"]
    assert kapi["gecti"] is False, kapi
    assert abs(kapi["maks_goreli_fark"] - 0.06) < 1e-9
    assert all(r["tolerans_ici"] is False for r in kapi["detay"])
    assert any("A kipi PK-1" in t["kalem"] for t in s["kill_list_tetik"]), s["kill_list_tetik"]


def test_T1c_YON_FARKI_BACAKTA_GORUNUR_ve_DUSURUR(k096_modul, uc_kip):
    """Yön ayrışırsa bacak DÜŞER ve `yon_esit` alanı bunu ADIYLA söyler.

    NOT (dürüst sınır): |A−PK1|/|PK1| ≤ 0,05 zaten AYNI işareti zorunlu kılar, yani yön koşulu
    tolerans geçerken tek başına ısırmaz — bu yüzden çivi ALAN düzeyinde ölçer: `yon_esit`
    False olmazsa (örn. sabit True döndüren bir mutasyon) burası kırılır."""
    y = uc_kip("t1c", -REF_I, REF_A1, REF_IIB)
    s = _a_kapisi(k096_modul, y, ad="t1c")
    detay = {(r["bacak"], r["ufuk"]): r for r in s["a_kipi_pk1_kapisi"]["detay"]}
    ters = detay[("i_ust20_kohort_fazlasi", "20")]
    assert ters["yon_esit"] is False, ters
    assert ters["gecti"] is False
    assert detay[("ii_b_artik_ic_fazla", "20")]["yon_esit"] is True
    assert s["a_kipi_pk1_kapisi"]["gecti"] is False


def test_T1d_CI0_DISILIK_DESENI_FARKLIYSA_TOLERANS_YETMEZ(k096_modul, uc_kip):
    """Oran %1 (tolerans içi) ve yön aynı, ama A kipi ii_b bacağı CI-0-DIŞI, PK-1 ise CI-0-İÇİ:
    kapı DÜŞMELİDİR. Kart "desen eşit" diyor — yalnız orana bakan bir kapı, aynı büyüklükte ama
    BAŞKA anlamlılıkta bir sonucu "aynı" sayardı."""
    y = uc_kip("t1d", REF_I * 1.01, REF_A1 * 1.01, REF_IIB * 1.01, a_iib_anlamli=True)
    s = _a_kapisi(k096_modul, y, ad="t1d")
    kapi = s["a_kipi_pk1_kapisi"]
    assert abs(kapi["maks_goreli_fark"] - 0.01) < 1e-9
    detay = {(r["bacak"], r["ufuk"]): r for r in kapi["detay"]}
    ayrik = detay[("ii_b_artik_ic_fazla", "20")]
    assert ayrik["tolerans_ici"] is True and ayrik["yon_esit"] is True
    assert ayrik["a_kipi_ci0_disi"] is True and ayrik["pk1_ci0_disi"] is False
    assert ayrik["ci0_disi_esit"] is False and ayrik["gecti"] is False
    assert kapi["gecti"] is False, kapi
    assert detay[("i_ust20_kohort_fazlasi", "20")]["gecti"] is True


def test_T1e_PK1_SIFIRSA_ORAN_TANIMSIZ_UYDURULMAZ(k096_modul, uc_kip):
    """PK-1 değeri SIFIRSA `|A−PK1|/|PK1|` TANIMSIZDIR: oran None + NEDEN, yön de None (sıfırın
    işareti yoktur) ve bacak "geçti" SAYILMAZ. Sıfıra bölmeyi "0 fark" ya da "sonsuz fark" diye
    yazmak, ölçülemeyeni ölçülmüş göstermek olurdu (uydurma yasağı)."""
    y = uc_kip("t1e", REF_I * 1.01, REF_A1 * 1.01, 0.001,
               pk1=_pk1_ref(iib_20=0.0))
    s = _a_kapisi(k096_modul, y, ad="t1e")
    kapi = s["a_kipi_pk1_kapisi"]
    detay = {(r["bacak"], r["ufuk"]): r for r in kapi["detay"]}
    sifir = detay[("ii_b_artik_ic_fazla", "20")]
    assert sifir["pk1_deger"] == 0.0
    assert sifir["goreli_fark"] is None and sifir["tolerans_ici"] is None
    assert sifir["yon_esit"] is None
    assert "SIFIR" in (sifir["neden"] or ""), sifir
    assert sifir["mutlak_fark"] == pytest.approx(0.001)
    assert sifir["gecti"] is None
    assert kapi["gecti"] is None, "ölçülemeyen bacak 'geçti' saydırmamalı"
    assert kapi["neden"]
    assert s["esikler"]["a_kipi_pk1_goreli_tol"]["gecti"] is None


def test_T1f_OLCULEN_BACAK_DUSUSU_OLCULEMEYENI_MASKELEMEZ(k096_modul, uc_kip):
    """ÜÇLÜ VE: bir bacak KESİN düşerken (oran %6) başka bir bacak ÖLÇÜLEMEZSE kapı None DEĞİL
    False olmalıdır — "ölçülemedi" bir düşüşü yutarsa kill-list sessizleşir."""
    y = uc_kip("t1f", REF_I * 1.06, REF_A1 * 1.01, 0.001, pk1=_pk1_ref(iib_20=0.0))
    s = _a_kapisi(k096_modul, y, ad="t1f")
    kapi = s["a_kipi_pk1_kapisi"]
    durumlar = [r["gecti"] for r in kapi["detay"]]
    assert False in durumlar and None in durumlar, durumlar
    assert kapi["gecti"] is False, kapi


# =================================================================================================
# T2 — 097: KATMAN i KAPISI BİR KİP LİSTESİDİR
# =================================================================================================
def test_T2a_LISTEDE_OLMAYAN_KIP_KAPIYA_GIRMEZ(k096_modul, uc_kip):
    """Sabit-251 kipi katman i'de CI-0-İÇİ olsa bile kapı GEÇER: 097 kartı PK'yi yalnız as-of ve
    güncel-liste kiplerinde ister (2020+ penceresinde sabit evrende ana etki ayrı bir sorudur).
    Kip listede olmadığı hâlde RAPORLANIR — sessizce düşerse okuyucu "ölçülmedi" ile "kapıya
    girmedi"yi ayıramaz (bedel yasası)."""
    y = uc_kip("t2a", REF_I, REF_A1, REF_IIB, sabit_i_anlamli=False)
    s = _a_kapisi(k096_modul, y, ad="t2a")
    e = s["esikler"]["katman_i_pk_kipler"]
    assert e["esik"] == ["asof", "guncel"]
    assert e["gecti"] is True, e
    detay = {d["kip"]: d for d in e["detay"]}
    assert set(detay) == {"asof", "guncel", "sabit"}
    assert detay["sabit"]["kapida"] is False
    assert detay["sabit"]["ci0_disi"] is False and detay["sabit"]["gecti"] is False
    assert detay["asof"]["kapida"] is True and detay["guncel"]["kapida"] is True
    assert not s["kill_list_tetik"], s["kill_list_tetik"]


def test_T2b_LISTEDEKI_KIP_CI0_ICIYSE_KAPI_DUSER(k096_modul, uc_kip):
    """As-of kipi katman i'de CI-0-İÇİ olursa kapı DÜŞER ve kartın "ölçüm bilgisiz" kalemi
    tetiklenir — sinyal yolu o pencerede yoksa hiçbir sayı yorumlanamaz."""
    y = uc_kip("t2b", REF_I, REF_A1, REF_IIB, a_i_anlamli=False)
    s = _a_kapisi(k096_modul, y, ad="t2b")
    e = s["esikler"]["katman_i_pk_kipler"]
    assert e["gecti"] is False, e
    assert any("katman i" in t["kalem"] for t in s["kill_list_tetik"]), s["kill_list_tetik"]


def test_T2c_SAYISAL_TABAN_YOKTUR(k096_modul, uc_kip):
    """097'de katman i eşiği bir LİSTEDİR, sayısal taban DEĞİL: as-of değeri EDG-096'nın 0,003
    tabanının ALTINDA olsa bile CI-0-dışı pozitifse kapı GEÇER. Gizli bir sayısal taban
    kalsaydı, kart "taban yok" derken kod başka bir kapı kurardı (tek-kaynak yasası)."""
    y = uc_kip("t2c", 0.0005, REF_A1, REF_IIB)
    s = _a_kapisi(k096_modul, y, ad="t2c")
    e = s["esikler"]["katman_i_pk_kipler"]
    assert e["gecti"] is True, e
    assert {d["kip"]: d["ort"] for d in e["detay"]}["asof"] == 0.0005


# =================================================================================================
# T3 — REGRESYON: 096 KARTIYLA ESKİ İKİ KAPI BİREBİR
# =================================================================================================
def test_T3a_096_KARTI_MUTLAK_KAPIYI_KURAR(k096_modul, uc_kip):
    """096 kartıyla A kipi kapısı MUTLAK kalır: 1e-5 ayrışma 1e-6 toleransını aşar → düşer ve
    alan adları ESKİ (`maks_mutlak_fark`). Ardıl kartın kodu eskisini bozsaydı, EDG-096'nın
    yayımlanmış hükmü artık kendi çıktısıyla yeniden üretilemezdi."""
    y = uc_kip("t3a", REF_I + 1e-5, REF_A1, REF_IIB)
    s, _ = _kosum(k096_modul, y["kok"], KART096, "t3a", y["asof"], y["guncel"], y["sabit"],
                  y["pk1"])
    kapi = s["a_kipi_pk1_kapisi"]
    assert kapi["sema"] == "mutlak"
    assert kapi["kiyaslanan_bacak_n"] == 6
    assert kapi["maks_mutlak_fark"] == pytest.approx(1e-5)
    assert kapi["gecti"] is False
    assert "goreli_fark" not in kapi["detay"][0], "096 çıktısına 097 alanı sızmış"
    assert "maks_goreli_fark" not in kapi
    e = s["esikler"]
    assert set(e) == set(yaml.safe_load(KART096.read_text(encoding="utf-8"))["esikler"])
    assert e["a_kipi_pk1_tutarlilik_tol"]["esik"] == 0.000001
    assert e["a_kipi_pk1_tutarlilik_tol"]["gecti"] is False
    assert e["a_kipi_pk1_tutarlilik_tol"]["deger"] == pytest.approx(1e-5)


def test_T3b_096_KARTI_SAYISAL_TABANI_KURAR(k096_modul, uc_kip):
    """096 kartıyla katman i kapısı ÜÇ kipte sayısal tabandır: sabit kipi 0,002944 < 0,003
    olduğu için DÜŞER (EDG-096'nın ölçtüğü kill-list 2'nin ta kendisi)."""
    y = uc_kip("t3b", REF_I, REF_A1, REF_IIB)
    s, _ = _kosum(k096_modul, y["kok"], KART096, "t3b", y["asof"], y["guncel"], y["sabit"],
                  y["pk1"])
    e = s["esikler"]["katman_i_pk_20g_alt"]
    assert e["esik"] == 0.003
    assert e["gecti"] is False, e
    assert {d["kip"]: d["gecti"] for d in e["detay"]} == {"asof": True, "guncel": True,
                                                          "sabit": False}
    assert all("kapida" not in d for d in e["detay"]), "taban şemasına kip listesi alanı sızmış"


def test_T3c_096_KARTI_ii_b_ve_OLCULEMEYEN_ESIKLERI_DEGISMEZ(k096_modul, uc_kip):
    """Ortak iki eşik iki kartta da AYNI kapıyı kurar — ardıl kart onlara dokunmadı."""
    y = uc_kip("t3c", REF_I, REF_A1, REF_IIB)
    s096, _ = _kosum(k096_modul, y["kok"], KART096, "t3c96", y["asof"], y["guncel"], y["sabit"],
                     y["pk1"])
    s097, _ = _kosum(k096_modul, y["kok"], KART097, "t3c97", y["asof"], y["guncel"], y["sabit"],
                     y["pk1"])
    for ad in ("ii_b_artik_ic_20g_alt", "olculemeyen_sabit_liste_ust_oran"):
        assert s096["esikler"][ad]["gecti"] == s097["esikler"][ad]["gecti"] is True
        assert s096["esikler"][ad]["deger"] == s097["esikler"][ad]["deger"]
    assert s096["tablo"] == s097["tablo"], "tablo kart şemasından ETKİLENMEMELİ"


# =================================================================================================
# T4 — ŞEMA BEYANI ve KART KİMLİĞİ
# =================================================================================================
def test_T4_KAPI_SEMASI_ve_KART_ID_CIKTIDA_BEYAN_EDILIR(k096_modul, uc_kip):
    """Çıktı hangi kapıyla koştuğunu SÖYLEMELİ: aynı dosya adı (`sonuc_096_*.json`) iki farklı
    kapı şeması taşıyabilir ve okuyucu (Rol-1) hangisinin hükmünü işlediğini ancak beyandan
    bilir. Kart kimliği de KARTTAN gelir — gömülü kimlik, 097 koşumunu 096 diye etiketlerdi."""
    y = uc_kip("t4", REF_I, REF_A1, REF_IIB)
    s97, cikti97 = _kosum(k096_modul, y["kok"], KART097, "t497", y["asof"], y["guncel"],
                          y["sabit"], y["pk1"])
    s96, _ = _kosum(k096_modul, y["kok"], KART096, "t496", y["asof"], y["guncel"], y["sabit"],
                    y["pk1"])
    assert s97["kapi_semasi"] == {"a_kipi": "goreli", "katman_i": "kip_listesi"}
    assert s96["kapi_semasi"] == {"a_kipi": "mutlak", "katman_i": "taban"}
    assert s97["kart_id"] == s97["kart"] == "EDG-2026-097"
    assert s96["kart_id"] == s96["kart"] == "EDG-2026-096"
    assert s97["esik_adlari"]["a_kipi"] == "a_kipi_pk1_goreli_tol"
    assert s97["esik_adlari"]["katman_i"] == "katman_i_pk_kipler"
    assert s97["hukum"] == "YOK — Rol-1" and s96["hukum"] == "YOK — Rol-1"
    # K beyanı da KARTTAN gelir: 097 koşumunda 096'nın deneme kimlikleri yazmaz.
    kart97 = yaml.safe_load(KART097.read_text(encoding="utf-8"))
    assert s97["k_beyani"]["trial_ids"] == list(kart97["k_registry"]["trial_ids"])
    assert all("EDG-096-" not in x for x in s97["k_beyani"]["satirlar"]), s97["k_beyani"]
    rapor = sorted(cikti97.glob("RAPOR_096_*.md"))[0].read_text(encoding="utf-8")
    assert rapor.startswith("# EDG-2026-097 "), rapor.splitlines()[0]
    for parca in ("**Hüküm:** YOK — Rol-1", "## Kart eşikleri", "## Kill-list tetikleri",
                  "asof, guncel", "Göreli fark"):
        assert parca in rapor, f"RAPOR'da eksik: {parca}"


# =================================================================================================
# T5 — EŞİK ADI DOĞRULAMASI: BİLİNMEYEN / EKSİK / ÇELİŞEN → ÇIKIŞ 2
# =================================================================================================
def _kart_yaz(kok: pathlib.Path, ad: str, esikler: dict, kill=None) -> pathlib.Path:
    p = kok / f"{ad}.yaml"
    p.write_text(yaml.safe_dump(
        {"card_id": "EDG-2026-SINAV", "esikler": esikler,
         "kill_list": kill if kill is not None else ["A kipi PK-1 sınav kalemi"],
         "k_registry": {"trial_ids": ["SINAV-1"]}},
        allow_unicode=True, sort_keys=False), encoding="utf-8")
    return p


def _sinav_esikleri(**degisiklik):
    e = {"ii_b_artik_ic_20g_alt": 0.015, "a_kipi_pk1_goreli_tol": 0.05,
         "katman_i_pk_kipler": ["asof", "guncel"],
         "olculemeyen_sabit_liste_ust_oran": 0.20}
    e.update(degisiklik)
    return e


@pytest.mark.parametrize("ad,esikler,beklenen", [
    ("bilinmeyen", _sinav_esikleri(ii_b_artik_ic_30g_alt=0.02), "ii_b_artik_ic_30g_alt"),
    ("a_kipi_eksik", {k: v for k, v in _sinav_esikleri().items()
                      if k != "a_kipi_pk1_goreli_tol"}, "a_kipi"),
    ("a_kipi_celisik", _sinav_esikleri(a_kipi_pk1_tutarlilik_tol=1e-6), "a_kipi"),
    ("katman_i_eksik", {k: v for k, v in _sinav_esikleri().items()
                        if k != "katman_i_pk_kipler"}, "katman_i"),
    ("katman_i_celisik", _sinav_esikleri(katman_i_pk_20g_alt=0.003), "katman_i"),
    ("zorunlu_eksik", {k: v for k, v in _sinav_esikleri().items()
                       if k != "olculemeyen_sabit_liste_ust_oran"},
     "olculemeyen_sabit_liste_ust_oran"),
])
def test_T5a_ESIK_ADI_SORUNU_CIKIS_2_ve_AD_YAZILIR(k096_modul, uc_kip, capsys, ad, esikler,
                                                   beklenen):
    """Eşik adı bilinmiyor, eksik ya da ÇELİŞİKSE (aynı kapı için iki ad) koşum DURUR: çıkış 2 ve
    sorunlu ad stderr'e ADIYLA yazılır. Varsayılan seçmek, kartın istemediği bir kapıyı sessizce
    kurar ve "ölçüldü" görünen bir hükmü kartın dışından üretirdi (uydurma yasağı)."""
    y = uc_kip(f"t5_{ad}", REF_I, REF_A1, REF_IIB)
    kart = _kart_yaz(y["kok"], f"kart_{ad}", esikler)
    with pytest.raises(SystemExit) as e:
        k096_modul.main(["--asof", str(y["asof"]), "--kart", str(kart),
                         "--cikti", str(y["kok"] / f"cikti_{ad}")])
    assert e.value.code == 2
    assert beklenen in capsys.readouterr().err


def test_T5b_KIP_LISTESINDE_BILINMEYEN_KIP_ADI_CIKIS_2(k096_modul, uc_kip, capsys):
    """Kip listesi bilinmeyen bir kip adı taşıyorsa koşum DURUR — sessizce yok saymak, kartın
    istediği kapının bir bacağını ölçülmeden geçirirdi."""
    y = uc_kip("t5b", REF_I, REF_A1, REF_IIB)
    kart = _kart_yaz(y["kok"], "kart_kip", _sinav_esikleri(
        katman_i_pk_kipler=["asof", "gunce"]))
    with pytest.raises(SystemExit) as e:
        k096_modul.main(["--asof", str(y["asof"]), "--kart", str(kart),
                         "--cikti", str(y["kok"] / "cikti_t5b")])
    assert e.value.code == 2
    assert "gunce" in capsys.readouterr().err


def test_T5c_KART_ID_YOKSA_CIKIS_2(k096_modul, uc_kip, capsys):
    """Kart kimliği YOKSA çıktı hangi kartın koşumu olduğunu söyleyemez — kimliği uydurmak
    yerine koşum durur."""
    y = uc_kip("t5c", REF_I, REF_A1, REF_IIB)
    kart = y["kok"] / "kart_kimliksiz.yaml"
    kart.write_text(yaml.safe_dump({"esikler": _sinav_esikleri(), "kill_list": ["x"]},
                                   allow_unicode=True), encoding="utf-8")
    with pytest.raises(SystemExit) as e:
        k096_modul.main(["--asof", str(y["asof"]), "--kart", str(kart),
                         "--cikti", str(y["kok"] / "cikti_t5c")])
    assert e.value.code == 2
    assert "card_id" in capsys.readouterr().err


# =================================================================================================
# T6 — KILL-LIST METNİ KARTIN KENDİ CÜMLESİDİR
# =================================================================================================
def test_T6a_TETIKLENEN_METINLER_097_KARTINDAN(k096_modul, uc_kip):
    """Dört kalem birden tetiklenir ve her metin KARTIN KENDİ CÜMLESİDİR (kopya metin yok).
    Kopya olsaydı kart cümlesi değiştiğinde çıktı eski cümleyi taşır ve Rol-1 yanlış kalemi
    işlerdi (tek-kaynak yasası)."""
    y = uc_kip("t6a", REF_I * 1.06, REF_A1 * 1.06, REF_IIB * 1.06, a_i_anlamli=False)
    kok = y["kok"]
    # B ve C kiplerini de düşür: ii_b CI-0-İÇİ + sabit liste kapsam dışı payı %25.
    y["guncel"] = _yaz(kok, "guncel_dusuk", _sonuc("guncel", 0.00644, 0.005512, 0.0283, False))
    y["sabit"] = _yaz(kok, "sabit_dusuk", _sonuc("sabit", 0.002944, 0.005776, 0.0274, False,
                                                 kunye=_sabit_kunyesi(0.25)))
    s = _a_kapisi(k096_modul, y, ad="t6a")
    kart = yaml.safe_load(KART097.read_text(encoding="utf-8"))
    tetik = s["kill_list_tetik"]
    assert len(tetik) == 4, [t["anahtar"] for t in tetik]
    assert {t["anahtar"] for t in tetik} == {"a_kipi_pk1", "katman_i_pk", "b_ve_c_ci0_ici",
                                             "sabit_olculemeyen"}
    for t in tetik:
        assert t["kalem"] in kart["kill_list"], f"kill-list metni kartta YOK: {t['kalem']}"
    assert s["kill_list_muhasebesi"]["kart_kalem_n"] == len(kart["kill_list"]) == 4
    assert s["kill_list_muhasebesi"]["eslesmeyen_kart_kalemleri"] == []


def test_T6b_096DA_OLUP_097DE_OLMAYAN_KALEM_ADIYLA_SAYILIR(k096_modul, uc_kip):
    """096'nın "as-of kipi çıktısı EDG-093 sonucundan ayrışırsa" kalemi 097'de YOKTUR (097 aynı
    soruyu 1. kalemde soruyor). Eşleme sessizce kaybolmaz: satır ADIYLA durur, durumu None'dır
    ve TETİKLENMİŞ SAYILMAZ."""
    y = uc_kip("t6b", REF_I * 1.06, REF_A1 * 1.06, REF_IIB * 1.06)
    s = _a_kapisi(k096_modul, y, ad="t6b")
    satirlar = {d["anahtar"]: d for d in s["kill_list_muhasebesi"]["durumlar"]}
    assert satirlar["asof_regresyonu"]["kalem"] is None
    assert satirlar["asof_regresyonu"]["durum"] is None
    assert satirlar["asof_regresyonu"]["aday_n"] == 0
    assert "TAŞIMIYOR" in satirlar["asof_regresyonu"]["neden"]
    assert "asof_regresyonu" not in {t["anahtar"] for t in s["kill_list_tetik"]}
    # 096 kartıyla AYNI fikstür: kalem VARDIR ve A kipi düştüğü için TETİKLENİR.
    s96, _ = _kosum(k096_modul, y["kok"], KART096, "t6b96", y["asof"], y["guncel"], y["sabit"],
                    y["pk1"])
    assert "asof_regresyonu" in {t["anahtar"] for t in s96["kill_list_tetik"]}


# =================================================================================================
# T7 — GERÇEK EDG-096 ÇIKTISI, 097 KARTIYLA (hazır dosyalar; ölçüm KOŞMAZ)
# =================================================================================================
def _gercek_cikti():
    yol = os.environ.get("EDG096_CIKTI")
    if not yol:
        pytest.skip("EDG096_CIKTI verilmedi — gerçek çıktı kolu ATLANDI (sayı uydurulmaz)")
    p = pathlib.Path(yol)
    if not p.is_dir():
        pytest.skip(f"EDG096_CIKTI dizini yok: {p}")
    return p


@pytest.fixture(scope="module")
def gercek(tmp_path_factory):
    """A1'de koşmuş EDG-096 çıktısı — ÜÇ kip sonucu + o turun `sonuc_096` kaydı.

    PK-1 REFERANSI: A1'deki `sonuc_093` PK-1 dosyası bu dizinde YOKTUR; elimizdeki tek kayıt o
    turun kapı detayındaki `pk1_deger` sütunudur. Referans ONDAN yeniden kurulur ve
    `pk1_anlamli` BİLEREK yazılmaz — o alan ölçülmedi, uydurulmaz. Sonuç: kapının CI-0-dışılık
    bileşeni ÖLÇÜLEMEZ, tolerans bileşeni ÖLÇÜLÜR (üçlü VE'de kesin düşüş maskelenmez)."""
    kok = _gercek_cikti()
    def tek(desen):
        bulunan = sorted(kok.glob(desen))
        if len(bulunan) != 1:
            pytest.skip(f"EDG096_CIKTI içinde tek dosya beklendi ({desen}): {bulunan}")
        return json.loads(bulunan[0].read_text(encoding="utf-8"))
    kipler = {"asof": tek("sonuc_093_2*.json"), "guncel": tek("sonuc_093_guncel_*.json"),
              "sabit": tek("sonuc_093_sabit_*.json")}
    s096 = tek("sonuc_096_*.json")
    tmp = tmp_path_factory.mktemp("edg097_gercek")
    yollar = {ad: _yaz(tmp, ad, veri) for ad, veri in kipler.items()}
    detay = [{"bacak": r["bacak"], "ufuk": r["ufuk"], "pk1_deger": r["pk1_deger"]}
             for r in s096["a_kipi_pk1_kapisi"]["detay"]]
    yollar["pk1"] = _yaz(tmp, "pk1", {"kart": "EDG-2026-093",
                                      "damga_utc": s096["pk1_referansi"].get("damga"),
                                      "pk": {"pk1": {"kosdu": True, "detay": detay}}})
    yollar["kok"] = tmp
    yollar["kipler"] = kipler
    yollar["s096"] = s096
    return yollar


@pytest.fixture(scope="module")
def gercek_097(gercek, k096_modul):
    sonuc, cikti = _kosum(k096_modul, gercek["kok"], KART097, "gercek097", gercek["asof"],
                          gercek["guncel"], gercek["sabit"], gercek["pk1"])
    return sonuc, cikti


def test_T7a_GERCEK_KATMAN_I_KIP_LISTESI_KAPISI_GECER(gercek_097, gercek):
    """Gerçek sayılarla: katman i @20 as-of ve güncel-liste kiplerinde CI-0-dışı pozitiftir →
    097 kapısı GEÇER; sabit-251 kipi CI-0-İÇİdir ama LİSTEDE OLMADIĞI için kapıya girmez.
    EDG-096'nın kill-list 2'si tam buradan tetiklenmişti — kapı birimi değişince aynı veri
    başka hüküm verir (sayılar Rol-1'indir, burada yalnız kapı mantığı ölçülür)."""
    s, _ = gercek_097
    e = s["esikler"]["katman_i_pk_kipler"]
    detay = {d["kip"]: d for d in e["detay"]}
    for kip in ("asof", "guncel"):
        ham = gercek["kipler"][kip]["kosumlar"]["dahil"]["bacaklar"]["i_ust20_kohort_fazlasi"]
        assert detay[kip]["ort"] == ham["20"]["ort"], "değer girdi dosyasından OKUNMUYOR"
        assert detay[kip]["kapida"] is True and detay[kip]["gecti"] is True
    assert detay["sabit"]["kapida"] is False
    assert detay["sabit"]["gecti"] is False, "sabit kipi CI-0-dışı çıktı — fikstür değişmiş"
    assert e["gecti"] is True, e


def test_T7b_GERCEK_ii_b_ve_OLCULEMEYEN_KAPILARI_GECER(gercek_097, gercek):
    """Hipotez kolu (B ya da C'de ii_b @20 ≥ 0,015 ve CI-0-dışı) ve sabit liste kapsam payı
    kapısı gerçek sayılarla GEÇER; değerler girdi dosyalarından OKUNUR, yeniden hesaplanmaz."""
    s, _ = gercek_097
    e = s["esikler"]["ii_b_artik_ic_20g_alt"]
    beklenen = max(gercek["kipler"][k]["kosumlar"]["dahil"]["bacaklar"]
                   ["ii_b_artik_ic_fazla"]["20"]["ic"] for k in ("guncel", "sabit"))
    assert e["deger"] == beklenen and e["gecti"] is True
    o = s["esikler"]["olculemeyen_sabit_liste_ust_oran"]
    assert o["deger"] == gercek["kipler"]["sabit"]["sabit_liste_kunyesi"]["kapsam_disi_oran"]
    assert o["gecti"] is True


def test_T7c_GERCEK_GORELI_FARK_BAGIMSIZ_HESAPLA_AYNI(gercek_097, gercek):
    """Kapının yazdığı `goreli_fark`, AYNI iki sayıdan bağımsızca hesaplanan orana EŞİTTİR —
    oranın paydası (PK-1) ve payı (mutlak fark) karışsaydı kapı başka bir şey ölçerdi."""
    s, _ = gercek_097
    alanlar = dict(mod_bacaklari())
    for r in s["a_kipi_pk1_kapisi"]["detay"]:
        ham = (gercek["kipler"]["asof"]["kosumlar"]["dahil"]["bacaklar"]
               [r["bacak"]][r["ufuk"]])
        a = ham[alanlar[r["bacak"]]]
        assert r["a_kipi_deger"] == a, r
        assert r["goreli_fark"] == pytest.approx(abs(a - r["pk1_deger"]) / abs(r["pk1_deger"]))
        assert r["ci0_disi_esit"] is None, "PK-1 anlamlılığı ölçülmedi — eşitlik UYDURULMAMALI"


def test_T7d_GERCEK_A_KIPI_KAPISI_ve_KILL_LIST_DURUMU(gercek_097):
    """A kipi kapısının gerçek veri üzerindeki HÜKMÜ (Rol-1'in değil, kapının): altı bacağın
    göreli farkları ve kartın %5 toleransı karşılaştırılır; kapı düşerse kartın 1. kalemi
    TETİKLENİR, geçerse hiçbir kalem tetiklenmez. Çivi kapının KENDİ detayıyla TUTARLI olmasını
    ölçer — böylece sayı değişse de mantık ölçülmüş kalır."""
    s, _ = gercek_097
    kapi = s["a_kipi_pk1_kapisi"]
    tol = s["esikler"]["a_kipi_pk1_goreli_tol"]["esik"]
    assert kapi["sema"] == "goreli" and kapi["kiyaslanan_bacak_n"] == 6
    oranlar = [r["goreli_fark"] for r in kapi["detay"]]
    assert all(o is not None for o in oranlar)
    assert kapi["maks_goreli_fark"] == max(oranlar)
    asan = [r for r in kapi["detay"] if r["goreli_fark"] > tol]
    assert kapi["gecti"] is (False if asan else None), (kapi["gecti"], asan)
    anahtarlar = {t["anahtar"] for t in s["kill_list_tetik"]}
    assert ("a_kipi_pk1" in anahtarlar) is bool(asan)
    assert "katman_i_pk" not in anahtarlar and "b_ve_c_ci0_ici" not in anahtarlar
    assert "sabit_olculemeyen" not in anahtarlar


def test_T7e_GERCEK_KOSUM_HUKUM_YAZMAZ_ve_RAPOR_OKUNUR(gercek_097):
    """Gerçek koşumda da hüküm YOKTUR ve RAPOR okunabilir (okuyan: Rol-1 masası — Yasa 6)."""
    s, cikti = gercek_097
    assert s["hukum"] == "YOK — Rol-1" and s["kart_id"] == "EDG-2026-097"
    assert s["kapi_semasi"] == {"a_kipi": "goreli", "katman_i": "kip_listesi"}
    raporlar = sorted(cikti.glob("RAPOR_096_*.md"))
    assert len(raporlar) == 1
    metin = raporlar[0].read_text(encoding="utf-8")
    for parca in ("**Hüküm:** YOK — Rol-1", "## Kip × bacak tablosu", "## Kart eşikleri",
                  "## Katman i kapısı", "## Kill-list tetikleri"):
        assert parca in metin, f"RAPOR'da eksik bölüm: {parca}"


def mod_bacaklari():
    """Bacak → değer alanı eşlemesi TEK KAYNAKTAN (karşılaştırma betiği) okunur; kopya bir
    eşleme, `ii_b`nin korelasyon (`ic`) olduğunu unutur ve sessizce None kıyaslardı."""
    return betikten_modul_yukle(KARSILASTIR, "v496_bacak_eslemesi").BACAKLAR


# =================================================================================================
# T8–T12 — EDG-2026-098: GÖRELİ TOLERANS YALNIZ PK-1'İN CI-0-DIŞI BACAKLARINDA
# =================================================================================================
# EDG-2026-097 ÖLÇÜLMEDEN GERİ ÇEKİLDİ: göreli %5 kapısı, PK-1'in CI-0-İÇİ (dolayısıyla sıfırdan
# ayırt edilemeyen) bir bacağında da hüküm veriyordu — gerçek EDG-096 çıktısında ii_b @20 bacağı
# 0,0089 ↔ 0,0084 idi ve göreli fark %5,95 çıkıyordu. O bacakta pay da payda da GÜRÜLTÜ; oran
# ANLAMSIZ BİRİMDEDİR. Ardıl kart EDG-2026-098 kapının birimini değiştirir (eşik yerinde
# düzeltilmez — yeni eşik = yeni kart, CLAUDE.md §5):
#     `a_kipi_pk1_goreli_yalniz_anlamli: true` → göreli tolerans YALNIZ PK-1'in CI-0-DIŞI
#     bacaklarına uygulanır; CI-0-İÇİ bacakta yalnız DESEN (yön + CI-0-dışılık) ölçülür ve
#     `goreli_fark` yine RAPORLANIR (bedel yasası: kapıdan çıkarmak, gizlemek değildir).
#: Kart ESİK/KILL blokları burada FİKSTÜRDÜR: kart dosyasını depoya Rol-1 koyar ve bu çiviler
#: onun VARLIĞINA bağlı değildir (ajan karta dokunmaz, CLAUDE.md §3). Kopya kaçınılmaz olduğu
#: için AYRIŞMA ÇİVİSİ vardır (T12): kart depoya girdiği gün blok onunla karşılaştırılır ve
#: sessizce ayrışamaz (tek-kaynak yasası, CLAUDE.md §4).
KART098_ID = "EDG-2026-098"
KART098_DESEN = "EDG-2026-098-*.yaml"
KART098_ESIKLER = {
    "ii_b_artik_ic_20g_alt": 0.015,
    "a_kipi_pk1_goreli_tol": 0.05,
    "a_kipi_pk1_goreli_yalniz_anlamli": True,
    "katman_i_pk_kipler": ["asof", "guncel"],
    "olculemeyen_sabit_liste_ust_oran": 0.20,
}
KART098_KILL = [
    "A kipi PK-1 ile desen (yön + CI-0-dışılık) altı bacakta eşit değil YA DA CI-0-dışı bacakta "
    "göreli fark > %5 → kod/veri yolu doğrulanmadı, sayı yayılmaz",
    "katman i @20 as-of ya da güncel-liste kipinde CI-0-içi → ölçüm bilgisiz",
    "B VE C'de ii_b @20 CI-0-içi → hipotez KALDI (pencere etkisi); EDG-016'ya şerh",
    "sabit-251 kapsam dışı payı > %20 → C kipi bilgisiz; yalnız B ile hüküm verilmez",
]
KART098_TRIAL = ["EDG-098-guncel-liste-ii-b-artik-ic-20g", "EDG-098-sabit251-ii-b-artik-ic-20g"]

#: Gerçek EDG-096 koşumunun (A1, 2026-09-15) A kipi ↔ PK-1 göreli farkları — T8 bunları
#: BAĞIMSIZCA yeniden hesaplar ve karşılaştırır; buradaki sayılar yalnız "fikstür değişmiş mi"
#: sorusunun cevabıdır (hüküm Rol-1'in).
GERCEK_ORAN_I20 = 0.021735630
GERCEK_ORAN_IIB20 = 0.059523810


def _kart098_yaz(kok: pathlib.Path, ad: str = "kart098", **degisiklik) -> pathlib.Path:
    """EDG-2026-098 kartının ESİK/KILL fikstürü — `degisiklik` ile tek alan oynatılır.

    `_kart_yaz` kullanılmaz: o sınav kartı sabit bir kill-list ve `EDG-2026-SINAV` kimliği
    taşır; buradaki çiviler kartın KENDİ kill-list cümlelerini ve kimliğini ölçer."""
    esikler = dict(KART098_ESIKLER)
    for anahtar, deger in degisiklik.items():
        if deger is None:
            esikler.pop(anahtar, None)
        else:
            esikler[anahtar] = deger
    p = kok / f"{ad}.yaml"
    p.write_text(yaml.safe_dump(
        {"card_id": KART098_ID, "esikler": esikler, "kill_list": list(KART098_KILL),
         "k_registry": {"trial_ids": list(KART098_TRIAL)}},
        allow_unicode=True, sort_keys=False), encoding="utf-8")
    return p


def _detay(kapi: dict) -> dict:
    return {(r["bacak"], r["ufuk"]): r for r in kapi["detay"]}


# -------------------------------------------------------------------------------------------------
# T8 — GERÇEK EDG-096 ÇIKTISI, 098 KARTIYLA (hazır dosyalar; ölçüm KOŞMAZ)
# -------------------------------------------------------------------------------------------------
@pytest.fixture(scope="module")
def gercek_pk1_yolu(gercek):
    """A1 koşumunun KULLANDIĞI PK-1 referansının ta kendisi — depodaki kopya sha256 ile
    DOĞRULANIR.

    T7'nin fikstürü PK-1'i kapı detayından yeniden kurar ve `pk1_anlamli`yi BİLEREK yazmaz (o
    alan orada ölçülmemiştir). 098 kapısının kararı TAM OLARAK o alana bağlıdır, dolayısıyla T8
    referansı uydurmak yerine A1'in okuduğu dosyayı okur: dosya ADI ve sha256'sı gerçek
    çıktının `girdi_damgasi` künyesinden gelir (tek-kaynak: kıyas ölçütü A1 kaydındadır)."""
    kayit = (gercek["s096"].get("girdi_damgasi") or {}).get("pk1_referans") or {}
    ad = pathlib.Path(str(kayit.get("yol") or "")).name
    if not ad:
        pytest.skip("gerçek çıktı PK-1 referans yolunu künyelemedi — kıyas ölçütü YOK")
    p = REPO / "research" / "olcumler" / "edg093_midcap_pit" / "olcum" / ad
    if not p.is_file():
        pytest.skip(f"A1 koşumunun PK-1 referansı depoda YOK: {ad}")
    bulunan = hashlib.sha256(p.read_bytes()).hexdigest()
    assert bulunan == kayit.get("sha256"), (
        f"depodaki PK-1 kopyası A1 koşumunun referansı DEĞİL: {bulunan} ≠ {kayit.get('sha256')}")
    return p


@pytest.fixture(scope="module")
def gercek_098(gercek, gercek_pk1_yolu, k096_modul, tmp_path_factory):
    kok = tmp_path_factory.mktemp("edg098_gercek")
    kart = _kart098_yaz(kok)
    return _kosum(k096_modul, kok, kart, "gercek098", gercek["asof"], gercek["guncel"],
                  gercek["sabit"], gercek_pk1_yolu)


def test_T8a_GERCEK_A_KIPI_KAPISI_GECER_CI0_ICI_BACAK_YALNIZ_DESEN(gercek_098, gercek,
                                                                   gercek_pk1_yolu):
    """GERÇEK sayılarla 098 kapısı: A kipi ↔ PK-1 GEÇER. EDG-097'yi düşüren ii_b @20 bacağı
    (%5,95 > %5) PK-1'de CI-0-İÇİdir → göreli tolerans UYGULANMAZ, yalnız desen ölçülür ve
    desen eşittir. CI-0-DIŞI olan iki `i` bacağında tolerans UYGULANIR ve %5'in altındadır.
    Sayılar Rol-1'indir; burada ölçülen şey kapının bu veriye NE DEDİĞİDİR."""
    s, _ = gercek_098
    kapi = s["a_kipi_pk1_kapisi"]
    assert kapi["sema"] == "goreli_yalniz_anlamli", kapi.get("sema")
    assert kapi["kiyaslanan_bacak_n"] == 6
    d = _detay(kapi)
    for ufuk in ("10", "20"):
        gated = d[("i_ust20_kohort_fazlasi", ufuk)]
        assert gated["pk1_ci0_disi"] is True and gated["goreli_uygulandi"] is True, gated
        assert gated["tolerans_ici"] is True and gated["gecti"] is True, gated
    for bacak in ("ii_a1_kova_tabanli_fazla", "ii_b_artik_ic_fazla"):
        for ufuk in ("10", "20"):
            r = d[(bacak, ufuk)]
            assert r["pk1_ci0_disi"] is False and r["goreli_uygulandi"] is False, r
            assert r["tolerans_ici"] is None, r
            assert r["goreli_fark"] is not None, "oran kapıdan çıktı diye GİZLENMEZ"
            assert r["ci0_disi_esit"] is True and r["yon_esit"] is True and r["gecti"] is True, r
    assert kapi["gecti"] is True, kapi


def test_T8b_GERCEK_ORANLAR_BAGIMSIZ_HESAPLA_AYNI_ve_IKI_MAKSIMUM(gercek_098, gercek,
                                                                  gercek_pk1_yolu):
    """Kapının yazdığı oranlar AYNI iki sayıdan bağımsızca yeniden hesaplanır. İKİ maksimum
    ayrı ayrı durur: `maks_goreli_fark` BÜTÜN bacakların (ii_b @20 = %5,95), eşiğe giren değer
    ise YALNIZ kapıdaki bacakların maksimumudur (%2,17) — ikisini tek sayıya indirmek ya kapıyı
    haksız düşürür ya da kaybedileni gizlerdi (bedel yasası)."""
    s, _ = gercek_098
    kapi = s["a_kipi_pk1_kapisi"]
    ham = json.loads(gercek_pk1_yolu.read_text(encoding="utf-8"))
    ref = {(r["bacak"], r["ufuk"]): r for r in ham["pk"]["pk1"]["detay"]}
    alanlar = dict(mod_bacaklari())
    kapidaki = []
    for r in kapi["detay"]:
        a_ham = gercek["kipler"]["asof"]["kosumlar"]["dahil"]["bacaklar"][r["bacak"]][r["ufuk"]]
        a = a_ham[alanlar[r["bacak"]]]
        rv = ref[(r["bacak"], r["ufuk"])]["pk1_deger"]
        assert r["a_kipi_deger"] == a and r["pk1_deger"] == rv, r
        assert r["goreli_fark"] == pytest.approx(abs(a - rv) / abs(rv)), r
        if r["goreli_uygulandi"]:
            kapidaki.append(r["goreli_fark"])
    assert kapi["maks_goreli_fark"] == pytest.approx(GERCEK_ORAN_IIB20), kapi["maks_goreli_fark"]
    assert kapi["maks_goreli_fark_kapida"] == pytest.approx(GERCEK_ORAN_I20)
    assert kapi["maks_goreli_fark_kapida"] == max(kapidaki)
    esik = s["esikler"]["a_kipi_pk1_goreli_tol"]
    assert esik["esik"] == 0.05 and esik["gecti"] is True
    assert esik["deger"] == pytest.approx(GERCEK_ORAN_I20), esik


def test_T8c_GERCEK_OTEKI_KAPILAR_ve_KILL_LIST_BOS(gercek_098, gercek):
    """Kartın öteki üç kapısı gerçek sayılarla GEÇER ve hiçbir kill-list kalemi TETİKLENMEZ;
    hüküm YOKTUR (Rol-1'in). Değerler girdi dosyalarından OKUNUR, yeniden hesaplanmaz."""
    s, _ = gercek_098
    e = s["esikler"]
    assert e["katman_i_pk_kipler"]["gecti"] is True, e["katman_i_pk_kipler"]
    kapida = {d["kip"]: d for d in e["katman_i_pk_kipler"]["detay"]}
    assert kapida["sabit"]["kapida"] is False and kapida["sabit"]["gecti"] is False
    beklenen = max(gercek["kipler"][k]["kosumlar"]["dahil"]["bacaklar"]
                   ["ii_b_artik_ic_fazla"]["20"]["ic"] for k in ("guncel", "sabit"))
    assert e["ii_b_artik_ic_20g_alt"]["deger"] == beklenen
    assert e["ii_b_artik_ic_20g_alt"]["gecti"] is True
    assert e["olculemeyen_sabit_liste_ust_oran"]["gecti"] is True
    assert e["olculemeyen_sabit_liste_ust_oran"]["deger"] == (
        gercek["kipler"]["sabit"]["sabit_liste_kunyesi"]["kapsam_disi_oran"])
    assert s["kill_list_tetik"] == [], s["kill_list_tetik"]
    assert s["kill_list_muhasebesi"]["eslesmeyen_kart_kalemleri"] == []
    assert s["hukum"] == "YOK — Rol-1" and s["kart_id"] == KART098_ID
    assert s["kapi_semasi"] == {"a_kipi": "goreli_yalniz_anlamli", "katman_i": "kip_listesi"}


def test_T8d_AYNI_GERCEK_GIRDI_097_KARTIYLA_DUSER(gercek, gercek_pk1_yolu, k096_modul,
                                                  tmp_path_factory):
    """KARŞITLIK ÇİVİSİ: AYNI gerçek girdiler 097 kartıyla (tur-1: göreli tolerans HER bacakta)
    kapıyı DÜŞÜRÜR — ii_b @20 %5,95 > %5. Kartın değiştirdiği şey veri değil BİRİMDİR; bu çivi
    olmadan 098'in "geçti"si kapı değişikliğinin değil fikstürün eseri olabilirdi."""
    kok = tmp_path_factory.mktemp("edg098_karsit")
    s, _ = _kosum(k096_modul, kok, KART097, "karsit097", gercek["asof"], gercek["guncel"],
                  gercek["sabit"], gercek_pk1_yolu)
    kapi = s["a_kipi_pk1_kapisi"]
    assert kapi["sema"] == "goreli"
    assert "goreli_uygulandi" not in kapi["detay"][0], "097 çıktısına 098 alanı sızmış"
    assert "maks_goreli_fark_kapida" not in kapi, "097 çıktısına 098 alanı sızmış"
    d = _detay(kapi)
    assert d[("ii_b_artik_ic_fazla", "20")]["tolerans_ici"] is False
    assert d[("i_ust20_kohort_fazlasi", "20")]["tolerans_ici"] is True
    assert kapi["gecti"] is False, kapi
    assert any("A kipi PK-1" in t["kalem"] for t in s["kill_list_tetik"]), s["kill_list_tetik"]


# -------------------------------------------------------------------------------------------------
# T9 — SENTETİK: ANLAMSIZ BACAKTA ORAN KAPIYA GİRMEZ, ANLAMLI BACAKTA GİRER
# -------------------------------------------------------------------------------------------------
def _k098(mod, y, ad, **degisiklik):
    kart = _kart098_yaz(y["kok"], f"kart_{ad}", **degisiklik)
    sonuc, cikti = _kosum(mod, y["kok"], kart, ad, y["asof"], y["guncel"], y["sabit"], y["pk1"])
    return sonuc, cikti


def test_T9a_CI0_ICI_BACAKTA_YUZDE_ELLI_FARK_GECER(k096_modul, uc_kip):
    """PK-1'in CI-0-İÇİ `ii_b` bacağında A kipi %50 AYRILIR: 098 kapısı GEÇER (desen eşit),
    çünkü o bacakta oranın payı da paydası da sıfırdan ayırt edilemez. `goreli_fark` yine
    RAPORLANIR — kapıdan çıkarmak, okuyucudan gizlemek değildir."""
    y = uc_kip("t9a", REF_I, REF_A1, REF_IIB * 1.5)
    s, _ = _k098(k096_modul, y, "t9a")
    kapi = s["a_kipi_pk1_kapisi"]
    d = _detay(kapi)
    for ufuk in ("10", "20"):
        r = d[("ii_b_artik_ic_fazla", ufuk)]
        assert r["goreli_uygulandi"] is False and r["tolerans_ici"] is None, r
        assert r["goreli_fark"] == pytest.approx(0.5), r
        assert r["gecti"] is True, r
    assert kapi["maks_goreli_fark"] == pytest.approx(0.5)
    assert kapi["maks_goreli_fark_kapida"] == pytest.approx(0.0)
    assert kapi["gecti"] is True, kapi
    assert s["esikler"]["a_kipi_pk1_goreli_tol"]["gecti"] is True
    assert s["kill_list_tetik"] == [], s["kill_list_tetik"]


def test_T9b_CI0_DISI_BACAKTA_YUZDE_ALTI_FARK_DUSURUR(k096_modul, uc_kip):
    """PK-1'in CI-0-DIŞI `i` bacağında %6 fark kartın %5 toleransını AŞAR → kapı DÜŞER ve
    kartın 1. kalemi tetiklenir. "Yalnız anlamlı bacakta ölç" kuralı toleransı KALDIRMAZ,
    uygulandığı yeri daraltır."""
    y = uc_kip("t9b", REF_I * 1.06, REF_A1, REF_IIB)
    s, _ = _k098(k096_modul, y, "t9b")
    kapi = s["a_kipi_pk1_kapisi"]
    d = _detay(kapi)
    for ufuk in ("10", "20"):
        r = d[("i_ust20_kohort_fazlasi", ufuk)]
        assert r["goreli_uygulandi"] is True and r["tolerans_ici"] is False, r
        assert r["gecti"] is False, r
    assert d[("ii_b_artik_ic_fazla", "20")]["gecti"] is True
    assert kapi["gecti"] is False, kapi
    assert kapi["maks_goreli_fark_kapida"] == pytest.approx(0.06)
    assert s["esikler"]["a_kipi_pk1_goreli_tol"]["gecti"] is False
    assert any("A kipi PK-1" in t["kalem"] for t in s["kill_list_tetik"]), s["kill_list_tetik"]


def test_T9c_CI0_ICI_BACAKTA_DESEN_FARKI_DUSURUR(k096_modul, uc_kip):
    """Tolerans uygulanmayan bacakta bile DESEN ölçülür: A kipi `ii_b` CI-0-DIŞI, PK-1 CI-0-İÇİ
    → bacak DÜŞER. Aksi hâlde "yalnız anlamlı bacakta ölç" kuralı, anlamsız bacağı tamamen
    kapının dışına çıkarır ve kart "desen eşit" derken kod hiçbir şey sormamış olurdu."""
    y = uc_kip("t9c", REF_I, REF_A1, REF_IIB, a_iib_anlamli=True)
    s, _ = _k098(k096_modul, y, "t9c")
    kapi = s["a_kipi_pk1_kapisi"]
    ayrik = _detay(kapi)[("ii_b_artik_ic_fazla", "20")]
    assert ayrik["goreli_uygulandi"] is False and ayrik["tolerans_ici"] is None
    assert ayrik["a_kipi_ci0_disi"] is True and ayrik["pk1_ci0_disi"] is False
    assert ayrik["ci0_disi_esit"] is False and ayrik["gecti"] is False, ayrik
    assert kapi["gecti"] is False, kapi


def test_T9d_HICBIR_BACAK_ANLAMLI_DEGILSE_TOLERANS_UYGULANMAZ_ve_ADIYLA_DURUR(k096_modul,
                                                                              uc_kip):
    """PK-1'in HİÇBİR bacağı CI-0-dışı değilse tolerans hiçbir yerde uygulanmaz: kapı desenle
    geçer ama eşik satırının DEĞERİ None'dır ve NEDEN bunu ADIYLA söyler — boş bir maksimumu
    "0 fark" diye yazmak, ölçülmemiş bir toleransı geçmiş göstermek olurdu (uydurma yasağı)."""
    y = uc_kip("t9d", REF_I * 3, REF_A1, REF_IIB, a_i_anlamli=False,
               pk1=_pk1_ref(i_anlamli=False))
    s, _ = _k098(k096_modul, y, "t9d")
    kapi = s["a_kipi_pk1_kapisi"]
    assert all(r["goreli_uygulandi"] is False for r in kapi["detay"]), kapi["detay"]
    assert kapi["maks_goreli_fark"] == pytest.approx(2.0)
    assert kapi["maks_goreli_fark_kapida"] is None
    assert kapi["gecti"] is True, kapi
    e = s["esikler"]["a_kipi_pk1_goreli_tol"]
    assert e["deger"] is None and e["gecti"] is True
    assert "UYGULANMADI" in (e["neden"] or ""), e


def test_T9e_OLCULEMEYEN_PK1_ANLAMLILIGI_BACAGI_GECTI_SAYDIRMAZ(k096_modul, uc_kip, tmp_path):
    """PK-1 satırında `pk1_anlamli` YOKSA toleransın uygulanıp uygulanmayacağı BİLİNEMEZ:
    `goreli_uygulandi` None, bacak "geçti" SAYILMAZ ve kapı None'dır. Varsayılan seçmek
    (uygula / uygulama) kartın sormadığı bir kapıyı sessizce kurardı."""
    pk1 = _pk1_ref()
    for satir in pk1["pk"]["pk1"]["detay"]:
        if satir["bacak"] == "ii_b_artik_ic_fazla":
            satir.pop("pk1_anlamli")
    y = uc_kip("t9e", REF_I, REF_A1, REF_IIB, pk1=pk1)
    s, _ = _k098(k096_modul, y, "t9e")
    kapi = s["a_kipi_pk1_kapisi"]
    bilinmeyen = _detay(kapi)[("ii_b_artik_ic_fazla", "20")]
    assert bilinmeyen["goreli_uygulandi"] is None, bilinmeyen
    assert bilinmeyen["pk1_ci0_disi"] is None and bilinmeyen["ci0_disi_esit"] is None
    assert bilinmeyen["gecti"] is None, bilinmeyen
    assert kapi["gecti"] is None, kapi
    assert kapi["neden"]


# -------------------------------------------------------------------------------------------------
# T10 — ALAN YOK / FALSE → TUR-1 (EDG-097) DAVRANIŞI AYNEN
# -------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("ad,degisiklik", [
    ("alan_yok", {"a_kipi_pk1_goreli_yalniz_anlamli": None}),
    ("alan_false", {"a_kipi_pk1_goreli_yalniz_anlamli": False}),
])
def test_T10a_ALAN_YOK_ya_da_FALSE_ISE_TUR1_DAVRANISI(k096_modul, uc_kip, ad, degisiklik):
    """Alan YOKSA ya da FALSE ise kapı tur-1'deki gibi HER bacakta göreli ölçer: CI-0-İÇİ `ii_b`
    bacağındaki %50 fark kapıyı DÜŞÜRÜR. 097'nin yayımlanmış davranışı ardıl kartın kodunda
    yaşamaya devam etmeli — yoksa o kartın hükmü kendi çıktısıyla yeniden üretilemezdi."""
    y = uc_kip(f"t10_{ad}", REF_I, REF_A1, REF_IIB * 1.5)
    s, _ = _k098(k096_modul, y, f"t10{ad}", **degisiklik)
    kapi = s["a_kipi_pk1_kapisi"]
    assert kapi["sema"] == "goreli", kapi.get("sema")
    assert s["kapi_semasi"]["a_kipi"] == "goreli"
    assert "goreli_uygulandi" not in kapi["detay"][0], kapi["detay"][0]
    assert "maks_goreli_fark_kapida" not in kapi
    assert _detay(kapi)[("ii_b_artik_ic_fazla", "20")]["tolerans_ici"] is False
    assert kapi["gecti"] is False, kapi
    assert s["esikler"]["a_kipi_pk1_goreli_tol"]["deger"] == pytest.approx(0.5)


def test_T10b_ALAN_MUTLAK_SEMAYLA_BIRLIKTE_CIKIS_2(k096_modul, uc_kip, capsys):
    """Ayar alanı MUTLAK şemayla birlikte verilirse koşum DURUR (çıkış 2): mutlak kapı bu alanı
    okumaz ve alan sessizce ÖLÜ kalırdı — kart bir şey isterken kod başkasını kurardı."""
    y = uc_kip("t10b", REF_I, REF_A1, REF_IIB)
    kart = _kart098_yaz(y["kok"], "kart_t10b", a_kipi_pk1_goreli_tol=None,
                        a_kipi_pk1_tutarlilik_tol=1e-6)
    with pytest.raises(SystemExit) as e:
        k096_modul.main(["--asof", str(y["asof"]), "--kart", str(kart),
                         "--cikti", str(y["kok"] / "cikti_t10b")])
    assert e.value.code == 2
    assert "a_kipi_pk1_goreli_yalniz_anlamli" in capsys.readouterr().err


def test_T10c_ALAN_BOOL_DEGILSE_CIKIS_2(k096_modul, uc_kip, capsys):
    """Ayar alanı bir BAYRAKTIR: sayı/metin verilirse koşum DURUR. Python'da boş olmayan her
    dizge doğrudur — "hayir" yazan bir kart sessizce kapıyı AÇARDI."""
    y = uc_kip("t10c", REF_I, REF_A1, REF_IIB)
    kart = _kart098_yaz(y["kok"], "kart_t10c", a_kipi_pk1_goreli_yalniz_anlamli="hayir")
    with pytest.raises(SystemExit) as e:
        k096_modul.main(["--asof", str(y["asof"]), "--kart", str(kart),
                         "--cikti", str(y["kok"] / "cikti_t10c")])
    assert e.value.code == 2
    assert "a_kipi_pk1_goreli_yalniz_anlamli" in capsys.readouterr().err


# -------------------------------------------------------------------------------------------------
# T11 — BEYAN: ŞEMA ADI, AYAR SATIRI ve RAPOR SÜTUNU
# -------------------------------------------------------------------------------------------------
def test_T11a_RAPOR_GORELI_UYGULANDI_SUTUNU_TASIR(k096_modul, uc_kip):
    """RAPOR okuyanı (Rol-1 masası) hangi bacağın kapıya girdiğini SÜTUNDAN görmeli: oran
    yazılıp "uygulandı mı" yazılmazsa okuyucu %5,95'i düşmüş bir kapı sanır (Yasa 6)."""
    y = uc_kip("t11a", REF_I, REF_A1, REF_IIB * 1.5)
    s, cikti = _k098(k096_modul, y, "t11a")
    metin = sorted(cikti.glob("RAPOR_096_*.md"))[0].read_text(encoding="utf-8")
    assert metin.startswith(f"# {KART098_ID} "), metin.splitlines()[0]
    assert "goreli_yalniz_anlamli" in metin
    assert "Göreli uygulandı" in metin, "bacak tablosunda sütun YOK"
    assert "kapıdaki bacaklarda" in metin
    for parca in ("## Kart eşikleri", "## Katman i kapısı", "## Kill-list tetikleri"):
        assert parca in metin, f"RAPOR'da eksik bölüm: {parca}"
    # Ayar alanı eşik tablosunda ADIYLA durur: kapı DEĞİLDİR, ama görünmez de değildir.
    ayar = s["esikler"]["a_kipi_pk1_goreli_yalniz_anlamli"]
    assert ayar["gecti"] is None and ayar["esik"] is True
    assert ayar["deger"] == ["i_ust20_kohort_fazlasi@10", "i_ust20_kohort_fazlasi@20"], ayar
    assert "KAPI DEĞİL" in (ayar["neden"] or "") or "KAPI DEĞİL" in (ayar["tanim"] or ""), ayar
    assert "a_kipi_pk1_goreli_yalniz_anlamli" in metin


def test_T11b_097_RAPORUNDA_SUTUN_YOKTUR(k096_modul, uc_kip):
    """REGRESYON: 097 kartının raporu 098 sütununu TAŞIMAZ — tur-1 çıktısı bu turda değişmedi."""
    y = uc_kip("t11b", REF_I, REF_A1, REF_IIB)
    _, cikti = _kosum(k096_modul, y["kok"], KART097, "t11b", y["asof"], y["guncel"], y["sabit"],
                      y["pk1"])
    metin = sorted(cikti.glob("RAPOR_096_*.md"))[0].read_text(encoding="utf-8")
    assert "Göreli fark" in metin
    assert "Göreli uygulandı" not in metin, "097 raporuna 098 sütunu sızmış"
    assert "goreli_yalniz_anlamli" not in metin


# -------------------------------------------------------------------------------------------------
# T12 — AYRIŞMA ÇİVİSİ: KART DEPOYA GİRDİĞİNDE FİKSTÜR ONUNLA KARŞILAŞTIRILIR
# -------------------------------------------------------------------------------------------------
def test_T12_DEPODAKI_098_KARTI_FIKSTURLE_AYNI(k096_modul):
    """Kart dosyasını depoya Rol-1 koyar (ajan karta dokunmaz). Girdiği gün bu çivi fikstürle
    kartı karşılaştırır: eşik adları, değerleri, kill-list cümleleri ve deneme kimlikleri
    ayrışırsa T8–T11 başka bir kartı ölçüyor demektir ve bunu sessiz bırakmak tek-kaynak
    yasasının ihlali olurdu. Kart henüz yoksa çivi ATLANIR (kaldıramayacağı bir şeyi kırmaz)."""
    bulunan = sorted(KARTLAR.glob(KART098_DESEN))
    if not bulunan:
        pytest.skip(f"EDG-2026-098 kartı depoda henüz YOK ({KART098_DESEN}) — Rol-1 koyacak")
    assert len(bulunan) == 1, bulunan
    kart = yaml.safe_load(bulunan[0].read_text(encoding="utf-8"))
    assert kart["card_id"] == KART098_ID
    assert kart["esikler"] == KART098_ESIKLER, "fikstür kart eşiklerinden AYRIŞTI"
    assert list(kart["kill_list"]) == KART098_KILL, "fikstür kart kill-list'inden AYRIŞTI"
    assert list(kart["k_registry"]["trial_ids"]) == KART098_TRIAL
    # Kart GERÇEKTEN 098 şemasını kurar: eşik adları betiğin kapı seçicisinden geçer.
    sema = k096_modul.kapi_semasi_sec(kart["esikler"])
    assert sema["a_kipi"] == "goreli_yalniz_anlamli"
    assert sema["a_kipi_esik_adi"] == "a_kipi_pk1_goreli_tol"
    assert sema["katman_i"] == "kip_listesi"
