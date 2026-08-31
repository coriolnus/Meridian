"""v344 — `meridian/earnings_pit.py` çivileri: PIT kazanç arşivi (EDGAR 8-K) okuyucusu.

EDG-2026-062 Görev 1. Bu modül, `earnings.days_since_report`in PIT'siz ikizinin yerine tarihsel
yolda kullanılacak ÜÇ DURUMLU çapayı taşır. Çivinin ölçtüğü asıl şey ÜÇÜNCÜ DURUMdur: "rapor
yok" (False) ile "bilmiyoruz" (None) bu modülde AYRI iki cevaptır — `earnings.days_since_report`
ikisini tek False'a katlıyordu ve `pitlaw.BILINEN_IHLALLER` bu katlamayı adıyla sayıyordu (kayıt
2026-08-31'de `pitlaw.PIT_KORUMALI_ZINCIRLER`e taşındı: borç kapandı, beyan sevke bağlandı).

NUMARA KİMLİKTİR: `v344` bu tur BOŞTU (`ls tests/ | grep v344` → hiçbir eşleşme, 2026-08-31).

GERÇEK ARŞİV ÖLÇÜMÜ (2026-08-31, `research/edgar_facts/earnings_8k_tarihleri.csv`):
17.535 ham satır · 17.407 TEKİL (symbol, report_date, filed) üçlüsü — yani 128 satır birebir
tekrardır ve `_arsiv_yukle` onları `earnings._load` emsalindeki gibi TEK sayar · 258 sembol ·
`filed` aralığı 2010-01-07 → 2026-07-31, 2.988 ayrık `filed` günü · `report_date` %100 dolu ·
`filed < report_date` olan satır YOK.

GERÇEK ARŞİV İDDİALARININ SIKILIĞI — BEYANLI SEÇİM: arşiv AYLIK tazelenen bir dosyadır
(`research/edgar_facts/betikler/`). Bu yüzden BÜYÜYEBİLEN uçlar `>=` ile, DEĞİŞMEMESİ gereken
uçlar `==` ile çivilendi: başlangıç günü ve sembol sayısı sabit beklenir, son gün ve satır sayısı
büyüyebilir, `dusen` HER ZAMAN sıfır olmalıdır (bir tazeleme biçimi bozarsa çivi ADIYLA öter).

`sandbox_state` KULLANILMAZ: `earnings_pit` `config.STATE`e hiç dokunmaz, `state/` altına yazmaz;
yalnız depo içindeki statik arşivi okur. Sentetik arşivler `tmp_path`e DOSYA olarak yazılır ve
`ARSIV_YOLU` monkeypatch ile oraya çevrilir (modül sabiti = tek enjeksiyon noktası).
"""
from __future__ import annotations

import ast
import datetime as dt
import os
import pathlib

import pytest

from meridian import earnings_pit


# ---------------------------------------------------------------------------------------------
# Sentetik arşiv yardımcıları
# ---------------------------------------------------------------------------------------------
BASLIK = "symbol,cik,filed,report_date,acceptance,items,accn"

# UFUK ÇAPASI — SENTETİK ARŞİVLERİN GÖRÜNMEZ ÖN KOŞULU. `days_since_report_pit` ufuk DIŞINDA
# None döner (sözleşme). Tek satırlık bir arşivde ufuk o tek `filed` gününe çöker ve "False
# bekliyorum" diye yazılan her çivi sessizce None üzerinden geçerdi — yani çivi hedeflediği dalı
# HİÇ ısırmazdı. Bu iki satır ufku 2015→2035 aralığına açar ki test tarihleri ufkun İÇİNDE kalsın.
UFUK_CAPASI = (("UFUK", "2015-01-05", "2015-01-05"), ("UFUK", "2035-01-05", "2035-01-05"))


def _satir(sym: str, filed: str, report_date: str) -> str:
    return f"{sym},1,{filed},{report_date},,,accn-{sym}-{filed}-{report_date}"


def arsiv_yaz(tmp_path: pathlib.Path, satirlar, *, capa: bool = True, ad: str = "arsiv.csv"):
    """Sentetik arşiv dosyası yazar ve yolunu döner. `satirlar`: (sym, filed, report_date) demetleri
    ya da ham dize (biçimsiz satır çivileri için)."""
    hepsi = list(satirlar) + (list(UFUK_CAPASI) if capa else [])
    govde = [BASLIK] + [s if isinstance(s, str) else _satir(*s) for s in hepsi]
    yol = tmp_path / ad
    yol.write_text("\n".join(govde) + "\n", encoding="utf-8")
    return yol


@pytest.fixture(autouse=True)
def _temiz_onbellek():
    """Her çivi kendi arşivini görür: önbellek hem önce hem SONRA sıfırlanır (sonra da şart —
    aksi hâlde bu dosyadan çıkan bayat önbellek komşu test dosyalarına sızardı)."""
    earnings_pit.clear_cache()
    earnings_pit.sayac_sifirla()
    yield
    earnings_pit.clear_cache()
    earnings_pit.sayac_sifirla()


@pytest.fixture
def sentetik(tmp_path, monkeypatch):
    """`(satirlar, **kw) -> yol` — arşivi yazar VE `ARSIV_YOLU`nu ona çevirir."""
    def kur(satirlar, **kw):
        yol = arsiv_yaz(tmp_path, satirlar, **kw)
        monkeypatch.setattr(earnings_pit, "ARSIV_YOLU", yol)
        earnings_pit.clear_cache()
        return yol
    return kur


# ---------------------------------------------------------------------------------------------
# 1) GERÇEK ARŞİV — yükleme ve ufuk
# ---------------------------------------------------------------------------------------------
gercek_arsiv = pytest.mark.skipif(
    not earnings_pit.ARSIV_YOLU.exists(),
    reason="research/edgar_facts/earnings_8k_tarihleri.csv yok (veri dosyası)")


@gercek_arsiv
def test_gercek_arsiv_yuklenir():
    """258 sembol, 17.407 tekil satır, SIFIR düşen — ölçüm 2026-08-31."""
    ars = earnings_pit._arsiv_yukle()
    assert len(ars) == 258
    assert sum(len(v) for v in ars.values()) >= 17407
    assert earnings_pit.arsiv_ufku()["dusen"] == 0


@gercek_arsiv
def test_gercek_arsiv_ufku():
    ufuk = earnings_pit.arsiv_ufku()
    assert ufuk["ilk"] == "2010-01-07"
    assert ufuk["son"] >= "2026-07-31"
    assert ufuk["n_tarih"] >= 2988
    assert ufuk["n_sembol"] == 258
    assert ufuk["neden"] is None


@gercek_arsiv
def test_gercek_arsivde_filed_report_dateten_once_degil():
    """PIT sözleşmesinin veri tarafı: hiçbir satır raporundan ÖNCE dosyalanmış olamaz."""
    ars = earnings_pit._arsiv_yukle()
    ihlal = [(s, rd, fl) for s, satirlar in ars.items() for rd, fl in satirlar if fl < rd]
    assert ihlal == []


# ---------------------------------------------------------------------------------------------
# 2) BOŞ ARŞİV — ufuk ölçülemez, uydurma aralık yok
# ---------------------------------------------------------------------------------------------
def test_bos_arsiv_ufku_none_ve_neden(sentetik):
    sentetik([], capa=False)
    ufuk = earnings_pit.arsiv_ufku()
    assert ufuk["ilk"] is None and ufuk["son"] is None
    assert ufuk["n_tarih"] == 0 and ufuk["n_sembol"] == 0
    assert ufuk["neden"] and "BOŞ" in ufuk["neden"]


def test_arsiv_dosyasi_yoksa_bos(tmp_path, monkeypatch):
    monkeypatch.setattr(earnings_pit, "ARSIV_YOLU", tmp_path / "yok.csv")
    earnings_pit.clear_cache()
    assert earnings_pit._arsiv_yukle() == {}
    assert earnings_pit.arsiv_ufku()["neden"] is not None


# ---------------------------------------------------------------------------------------------
# 3) ÖNBELLEK — mtime + YOL (earnings._load emsali, yol boyutu eklenmiş)
# ---------------------------------------------------------------------------------------------
def test_onbellek_ayni_dosyada_diski_okumaz(sentetik, monkeypatch):
    yol = sentetik([("AAA", "2020-03-10", "2020-03-10")])
    ilk = earnings_pit._arsiv_yukle()
    okuma = {"n": 0}
    gercek_open = pathlib.Path.open

    def sayan_open(self, *a, **kw):
        if self == yol:
            okuma["n"] += 1
        return gercek_open(self, *a, **kw)

    monkeypatch.setattr(pathlib.Path, "open", sayan_open)
    ikinci = earnings_pit._arsiv_yukle()
    assert okuma["n"] == 0            # mtime değişmedi → disk HİÇ okunmadı
    assert ikinci == ilk


def test_onbellek_yol_degisince_yeniden_okur(tmp_path, monkeypatch):
    """İKİ DOSYANIN mtime'ı EŞİTLENİR ve bu çivinin bütün gücü oradadır: eşitlemezsek dosyalar
    ardışık yazıldığı için mtime'lar zaten farklı olur, önbellek kendiliğinden düşer ve çivi
    "anahtarda yol var" iddiasını HİÇ ölçmeden yeşil kalırdı (yanlış sebeple yeşil)."""
    a = arsiv_yaz(tmp_path, [("AAA", "2020-03-10", "2020-03-10")], ad="a.csv")
    b = arsiv_yaz(tmp_path, [("BBB", "2020-03-10", "2020-03-10")], ad="b.csv")
    os.utime(a, (1_700_000_000, 1_700_000_000))
    os.utime(b, (1_700_000_000, 1_700_000_000))
    assert a.stat().st_mtime == b.stat().st_mtime
    monkeypatch.setattr(earnings_pit, "ARSIV_YOLU", a)
    earnings_pit.clear_cache()
    assert "AAA" in earnings_pit._arsiv_yukle()
    monkeypatch.setattr(earnings_pit, "ARSIV_YOLU", b)
    # clear_cache ÇAĞRILMADAN: önbellek anahtarı YOLU da taşır, yoksa b sessizce a olarak okunurdu
    assert "BBB" in earnings_pit._arsiv_yukle()
    assert "AAA" not in earnings_pit._arsiv_yukle()


def test_clear_cache_diski_yeniden_okutur(sentetik):
    yol = sentetik([("AAA", "2020-03-10", "2020-03-10")])
    assert "BBB" not in earnings_pit._arsiv_yukle()
    yol.write_text("\n".join([BASLIK, _satir("BBB", "2020-03-10", "2020-03-10")]) + "\n",
                   encoding="utf-8")
    earnings_pit.clear_cache()
    assert "BBB" in earnings_pit._arsiv_yukle()


# ---------------------------------------------------------------------------------------------
# 4) ÜÇ DURUM — None (ölçülemedi) / True (rapor ardında) / False (rapor yok, ÖLÇÜLDÜ)
# ---------------------------------------------------------------------------------------------
R = "2020-03-10"          # rapor günü — ufuk çapasının (2015→2035) İÇİNDE


def _gun(temel: str, kaydir: int) -> str:
    return (dt.date.fromisoformat(temel) + dt.timedelta(days=kaydir)).isoformat()


def test_none_bicimsiz_tarih(sentetik):
    sentetik([("AAA", R, R)])
    assert earnings_pit.days_since_report_pit("AAA", "10.03.2020") is None
    assert earnings_pit.days_since_report_pit("AAA", None) is None


def test_none_bos_arsiv(sentetik):
    sentetik([], capa=False)
    assert earnings_pit.days_since_report_pit("AAA", R) is None


def test_none_ufuk_disi_iki_uc(sentetik):
    """Ufuk sözleşmesi: arşivin BAŞLAMADIĞI ya da BİTTİĞİ yerde cevap 'rapor yok' DEĞİL,
    'ölçülemedi'dir. Bu, `earnings.days_since_report`in sessiz False'unun tam karşıtıdır."""
    sentetik([("AAA", R, R)], capa=False)      # ufuk tek güne çöker: [R, R]
    assert earnings_pit.days_since_report_pit("AAA", _gun(R, -1)) is None
    assert earnings_pit.days_since_report_pit("AAA", _gun(R, +1)) is None


def test_none_sembol_arsivde_hic_yok(sentetik):
    """Kapsam dışı sembol: tarih ufkun İÇİNDE ama sembol hakkında hiçbir satır yok → None."""
    sentetik([("AAA", R, R)])
    assert earnings_pit.days_since_report_pit("ZZZ", _gun(R, +1)) is None
    assert earnings_pit.days_since_report_pit("", _gun(R, +1)) is None


def test_true_rapor_ardinda(sentetik):
    sentetik([("AAA", R, R)])
    assert earnings_pit.days_since_report_pit("AAA", _gun(R, +1)) is True
    assert earnings_pit.days_since_report_pit("aaa", _gun(R, +2)) is True   # sembol büyük/küçük


def test_false_ufuk_ici_eslesme_yok(sentetik):
    """Sembol VAR, tarih ufkun İÇİNDE, eşleşen satır yok → 'rapor yok' ÖLÇÜLDÜ (False, None değil)."""
    sentetik([("AAA", R, R)])
    assert earnings_pit.days_since_report_pit("AAA", _gun(R, +3)) is False   # max_days aşıldı
    assert earnings_pit.days_since_report_pit("AAA", _gun(R, -30)) is False  # rapordan ÖNCE


def test_false_filed_esit_gun_dahil_degil(sentetik):
    """MUHAFAZAKÂR GÖRÜNÜRLÜK EŞİTLİK SINIRI: filed == on_date → HENÜZ GÖRÜNMEZ.

    report_date=R, filed=R, on_date=R: gün farkı 0 ve max_days=2 içinde, yani PIT'siz çapa True
    derdi. Burada False'tur — dosyalamanın kendi günü dahil değildir. Bir sonraki gün True."""
    sentetik([("AAA", R, R)])
    assert earnings_pit.days_since_report_pit("AAA", R) is False
    assert earnings_pit.days_since_report_pit("AAA", _gun(R, +1)) is True


def test_gec_dosyalama_pead_penceresi(sentetik):
    """GEÇ DOSYALAMA — bu modülün PIT'siz ikizinden AYRILDIĞI yer.

    report_date=R ama filed=R+5 (ölçüldü: gerçek arşivde 17.535 satırın 1.620'si geç dosyalama).
    PIT'siz çapa R+1'de True derdi (rapor tarihine bakar); burada R+1'de rapor HENÜZ GÖRÜNMEZ."""
    sentetik([("AAA", _gun(R, 5), R)])
    assert earnings_pit.days_since_report_pit("AAA", _gun(R, +1)) is False
    # PEAD penceresi (max_days=35): dosyalama görünür olduktan sonra çapa döner
    assert earnings_pit.days_since_report_pit("AAA", _gun(R, +6), max_days=35) is True
    assert earnings_pit.days_since_report_pit("AAA", _gun(R, +35), max_days=35) is True
    assert earnings_pit.days_since_report_pit("AAA", _gun(R, +36), max_days=35) is False
    # filed günü (R+5) hâlâ dahil değil: R+5'te görünürlük yok
    assert earnings_pit.days_since_report_pit("AAA", _gun(R, +5), max_days=35) is False


# ---------------------------------------------------------------------------------------------
# 5) BİÇİMSİZ SATIR — sessizce düşmez, SAYILIR
# ---------------------------------------------------------------------------------------------
def test_bicimsiz_satir_dusene_dusar_sifir_sayilmaz(sentetik):
    """Üç bozuk satır (boş sembol · biçimsiz filed · eksik sütun) `dusen`e düşer; sağlam satır
    yüklenir. `dusen == 0` ile "üç satır kayboldu" AYNI görünemez — Yasa 6 okuyucusu budur."""
    sentetik([
        ("AAA", R, R),
        ",1,2020-03-10,2020-03-10,,,accn-bos-sembol",
        "BBB,1,10.03.2020,2020-03-10,,,accn-bicimsiz-filed",
        "CCC,1",
    ])
    ars = earnings_pit._arsiv_yukle()
    assert earnings_pit.arsiv_ufku()["dusen"] == 3
    assert set(ars) == {"AAA", "UFUK"}          # bozuk satır hayalet sembol YARATMAZ
    assert ars["AAA"] == [(R, R)]


def test_dusen_sayaci_yeniden_yuklemede_tazelenir(sentetik):
    yol = sentetik([("AAA", R, R), "CCC,1"])
    assert earnings_pit.arsiv_ufku()["dusen"] == 1
    yol.write_text("\n".join([BASLIK, _satir("AAA", R, R)]) + "\n", encoding="utf-8")
    earnings_pit.clear_cache()
    assert earnings_pit.arsiv_ufku()["dusen"] == 0     # eski sayı taşınmaz


# ---------------------------------------------------------------------------------------------
# 6) SAYAÇ ÜÇLÜSÜ — her çağrı sayılır
# ---------------------------------------------------------------------------------------------
def test_sayac_uclusu_her_cagriyi_sayar(sentetik):
    sentetik([("AAA", R, R)])
    assert earnings_pit.sayac_oku() == {"true": 0, "false": 0, "olculemedi": 0}
    earnings_pit.days_since_report_pit("AAA", _gun(R, +1))    # True
    earnings_pit.days_since_report_pit("AAA", _gun(R, +9))    # False
    earnings_pit.days_since_report_pit("AAA", _gun(R, +2))    # True
    earnings_pit.days_since_report_pit("ZZZ", _gun(R, +1))    # None (sembol yok)
    earnings_pit.days_since_report_pit("AAA", "bozuk")        # None (biçimsiz)
    assert earnings_pit.sayac_oku() == {"true": 2, "false": 1, "olculemedi": 2}


def test_sayac_bos_arsiv_none_unu_olculemedi_sayar(sentetik):
    """SAYAÇ SÖZLEŞMESİ DAL DAL ÖLÇÜLÜR. `test_sayac_uclusu_her_cagriyi_sayar` `olculemedi`nin
    yalnız İKİ yolunu geziyordu (kapsam dışı sembol + biçimsiz tarih); None'un DÖRT yolu var ve
    kalan ikisi çivisizdi — yani `_say` o dallardan sessizce düşürülebilirdi.

    BURASI: arşiv BOŞ. Dönüş None'dur ve o çağrı `olculemedi` kovasına DÜŞMELİDİR; düşmezse
    kapsam ölçüsü (`olculemedi` payı) sistematik olarak OLDUĞUNDAN İYİ görünür — körlüğün
    belirtisi yine hiçbir şey olurdu."""
    sentetik([], capa=False)
    assert earnings_pit.sayac_oku() == {"true": 0, "false": 0, "olculemedi": 0}
    assert earnings_pit.days_since_report_pit("AAA", R) is None
    assert earnings_pit.sayac_oku() == {"true": 0, "false": 0, "olculemedi": 1}


def test_sayac_ufuk_disi_none_unu_olculemedi_sayar(sentetik):
    """None'un DÖRDÜNCÜ yolu: tarih arşivin `filed` ufkunun DIŞINDA (iki uç da). İki çağrı, iki
    `olculemedi` — ve hiçbiri `false` kovasına sızmaz (ufuk dışı 'rapor yok' DEĞİLDİR)."""
    sentetik([("AAA", R, R)], capa=False)      # ufuk tek güne çöker: [R, R]
    assert earnings_pit.days_since_report_pit("AAA", _gun(R, -1)) is None
    assert earnings_pit.days_since_report_pit("AAA", _gun(R, +1)) is None
    assert earnings_pit.sayac_oku() == {"true": 0, "false": 0, "olculemedi": 2}


def test_ufuk_turevi_YUKLEME_basina_bir_kez_kosar(sentetik, monkeypatch):
    """SICAK YOL BÜTÇESİ (B-4, Rol-1 kararı 2026-08-31). Ufuk türevi O(n)'dir ve `arsiv_ufku`
    onu her çağrıda yeniden hesaplıyordu; `days_since_report_pit` de her çağrıda `arsiv_ufku`
    çağırır → maliyet ÇAĞRI başına O(n) (0,52 ms; cf ölçeğinde ~4-5 dk). Artık YÜKLEME başına.

    ÇİVİ TÜREVİ SAYAR, SÜREYİ DEĞİL: süre ölçen bir çivi makineye bağlı ve gürültülü olurdu;
    sayılan şey sözleşmenin kendisidir. Sekiz çağrı, TEK türev."""
    sentetik([("AAA", R, R)])
    sayim = {"n": 0}
    gercek = earnings_pit._ufuk_turet
    monkeypatch.setattr(earnings_pit, "_ufuk_turet",
                        lambda ars: (sayim.__setitem__("n", sayim["n"] + 1), gercek(ars))[1])
    for _ in range(4):
        earnings_pit.arsiv_ufku()
        earnings_pit.days_since_report_pit("AAA", _gun(R, +1))
    assert sayim["n"] == 1, f"ufuk türevi {sayim['n']} kez koştu — memo tutmuyor"


def test_ufuk_memosu_YENI_ARSIVDE_bayat_kalmaz(sentetik, tmp_path, monkeypatch):
    """Memonun İKİNCİ yarısı — ve asıl riski: hızlanma doğruysa ama TAZELEME yanlışsa, ufuk
    sessizce BAYAT kalır ve `days_since_report_pit` yanlış dünyada hüküm verir (ufuk-dışı sanılan
    bir tarih None döner: "ölçülemedi" diye kaydedilen bir ÖLÇÜM HATASI).

    `clear_cache()` BİLEREK ÇAĞRILMIYOR: onu çağırmak memoyu AÇIKÇA düşürür ve çivi, asıl
    taşıyıcı olan NESİL anahtarını hiç sınamadan geçerdi. Burada yalnız arşiv DEĞİŞİR
    (`ARSIV_YOLU` başka dosyaya döner) — tazelemeyi `_arsiv_yukle`nin nesil artışı yapmalıdır."""
    sentetik([("AAA", R, R)])
    assert earnings_pit.arsiv_ufku()["ilk"] == "2015-01-05"      # ufuk çapası (2015→2035)
    yeni = arsiv_yaz(tmp_path, [("BBB", "2021-06-07", "2021-06-07")], capa=False, ad="arsiv2.csv")
    monkeypatch.setattr(earnings_pit, "ARSIV_YOLU", yeni)
    ufuk = earnings_pit.arsiv_ufku()
    assert (ufuk["ilk"], ufuk["son"]) == ("2021-06-07", "2021-06-07"), f"memo bayat kaldı: {ufuk}"


def test_sayac_okuma_kopyadir_ve_sifirlanir(sentetik):
    sentetik([("AAA", R, R)])
    earnings_pit.days_since_report_pit("AAA", _gun(R, +1))
    goruntu = earnings_pit.sayac_oku()
    goruntu["true"] = 999                                      # çağıran sayacı EZEMEZ
    assert earnings_pit.sayac_oku()["true"] == 1
    earnings_pit.sayac_sifirla()
    assert earnings_pit.sayac_oku() == {"true": 0, "false": 0, "olculemedi": 0}


# ---------------------------------------------------------------------------------------------
# 7) İZOLASYON ÇİVİSİ — modül `meridian.obs`a ULAŞMAZ, `config.STATE`e DOKUNMAZ
# ---------------------------------------------------------------------------------------------
# NEDEN STATİK ÖLÇÜM, `sys.modules` DEĞİL: `tests/conftest.py` toplama anında `meridian.obs`u
# ZATEN import eder (`_MODUL_DURUMLARI` fotoğrafı için). Yani `sys.modules` üzerinden sorulan
# soru bu suite içinde HER ZAMAN "yüklü" der ve çivi hiçbir şey ölçmez — yanlış sebeple yeşil.
# Sorulan gerçek soru şudur: `import meridian.earnings_pit` NEYİ YÜKLER, ve bu modülün kaynağında
# `obs`a giden bir ad (geç import dahil) var mı?
MERIDIAN_DIZIN = pathlib.Path(earnings_pit.__file__).resolve().parent


def _import_adlari(agac: ast.AST, *, fonksiyon_govdesi_dahil: bool) -> set[str]:
    """Ağaçta anılan MERIDIAN modül adları. `fonksiyon_govdesi_dahil=False` yalnız İTHAL ANINDA
    koşan import'ları verir (fonksiyon gövdeleri atlanır) — `import x` gerçekte neyi yükler."""
    adlar: set[str] = set()

    def gez(dugum):
        for cocuk in ast.iter_child_nodes(dugum):
            if (isinstance(cocuk, (ast.FunctionDef, ast.AsyncFunctionDef))
                    and not fonksiyon_govdesi_dahil):
                continue
            if isinstance(cocuk, ast.ImportFrom):
                kok = (cocuk.module or "").split(".")
                if cocuk.level:                                   # from . import x / from .x import y
                    adlar.update([kok[0]] if cocuk.module else [a.name.split(".")[0]
                                                                for a in cocuk.names])
                elif kok[0] == "meridian":                        # from meridian[.x] import y
                    adlar.update([kok[1]] if len(kok) > 1 else [a.name.split(".")[0]
                                                                for a in cocuk.names])
            elif isinstance(cocuk, ast.Import):
                for a in cocuk.names:                             # import meridian.x
                    parca = a.name.split(".")
                    if parca[0] == "meridian" and len(parca) > 1:
                        adlar.add(parca[1])
            gez(cocuk)

    gez(agac)
    return adlar


def _ithal_kapanimi(baslangic: str) -> set[str]:
    gorulen: set[str] = set()
    kuyruk = [baslangic]
    while kuyruk:
        ad = kuyruk.pop()
        if ad in gorulen:
            continue
        gorulen.add(ad)
        yol = MERIDIAN_DIZIN / f"{ad}.py"
        if not yol.exists():           # alt paket (adapters/) — .py dosyası yok, izlenmez
            continue
        agac = ast.parse(yol.read_text(encoding="utf-8"))
        kuyruk.extend(_import_adlari(agac, fonksiyon_govdesi_dahil=False))
    return gorulen


def _agac():
    return ast.parse(pathlib.Path(earnings_pit.__file__).read_text(encoding="utf-8"))


def test_modul_obsa_ulasmaz():
    dogrudan = _import_adlari(_agac(), fonksiyon_govdesi_dahil=True)
    assert "obs" not in dogrudan            # geç (fonksiyon-içi) import kaçış deliği de kapalı
    assert dogrudan == {"config"}           # tek meridian bağımlılığı
    assert "obs" not in _ithal_kapanimi("earnings_pit")


def test_modul_config_stateye_dokunmaz():
    """`state/` bu modülün dünyasında YOK: ne okur ne yazar (arşiv depo içinde statiktir)."""
    dokunulan = {d.attr for d in ast.walk(_agac()) if isinstance(d, ast.Attribute)}
    assert dokunulan & {"STATE", "HISTORY", "BARS"} == set()
