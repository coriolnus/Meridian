"""test_edg095_goreli_ozdeslik_v494.py — EDG-2026-095 ardıl dilimi: kart-kaynaklı eşikler
(`--kart`), GÖRELİ özdeşlik kolu, damgalı kontrol asgarisi, yazım kümesi + ADIM-2 yazım
betiğinin defter-bağlaması/güven süzgeci/savunma dalları.

vNNN KİMLİK KAYDI: v494 seçildi çünkü ölçüm anında (2026-09-15)
`grep -rn v494 tests/ ops/ meridian/ research/ docs/` HİÇBİR eşleşme vermedi — çakışma yok,
taşıma yok (CLAUDE.md §2 vNNN kimlik kuralı). Komşular: v490 EDG-093, v491 vault dalga-2,
v492 EDG-094 — üçüne de dokunulmadı.

NE ÇİVİLER (kaynak: EDG-2026-095 kartının `esikler` + `ardil_dilim_gereksinimleri` blokları):
  * T1 — eşikler KARTTAN okunur (tek kaynak); kod tarafında donuk kopya YOK.
  * T2 — GÖRELİ özdeşlik kolu: ölçü max |1 − payda_oran|, küme = benimsemesiz VE plan-stop.
  * T3 — `kontrol_asgari_n`: damgalı satır asgarinin altındaysa PK-1 GEÇMEZ, BİLGİSİZDİR.
  * T4 — `yazim_kumesi`: düşük güvenli (koruma_oco) satırlar yazım kümesine GİRMEZ.
  * T5 — 094 KİPİ REGRESYONU: ardıl dilim eski kartın çıktısını değiştirmez.
  * T6 — B1 defter bağlaması: ölçüm künyesindeki db sha256 ≠ `--db` sha256 → çıkış 1.
  * T7 — güven süzgeci: `guven == "dusuk"` satır YAZILMAZ ve SAYILIR (bedel yasası).
  * T8 — B4 savunma dalları: "seq defterde yok" ve "sayım uyuşmazlığı → rollback".
  * T9 — B3: `qty_taban` VARKEN benimseme çapraz-kontrolü UYGULANMAZ (kart sırası).

TEK KAYNAK — FİKSTÜR GÖVDESİ KOPYALANMAZ. Sentetik defter kurucuları (`_db_kur`, `_islem`,
`_plan`, olay üreticileri) ve ops yardımcıları v492'den İTHAL edilir. İkinci bir gövde yazmak bu
deponun tekrar eden "iki kopya sessizce ayrışır" sınıfının ta kendisi olurdu (v401'in v382'den
ithal deseni).

AĞ YOK, CANLI DEFTER YOK: `olc_mod` fikstürü `sandbox_state`e bağlıdır (config.STATE tmp'ye
döner), ölçüm betiği `meridian.*` ithal etmez, gerçek kopya çivisi yalnız ortam değişkeniyle
açılır ve SALT-OKUR koşar.

MUTASYON KANITI bu dosyada KOŞMAZ; Rol-1'e teslim raporunda tablo hâlinde durur (CLAUDE.md §6).
"""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import shutil
import sqlite3
import subprocess
import sys

import pytest
import yaml

from tests.conftest import betikten_modul_yukle
from tests.test_edg094_r_yeniden_v492 import (  # noqa: F401 — `olc_mod` FİKSTÜRDÜR, çağrılmaz
    OLC, OPS, _benimseme, _db_kur, _extra, _islem, _koruma, _olaylar_yaz, _plan,
    _r_multiple_sha, olc_mod)

REPO = pathlib.Path(__file__).resolve().parents[1]
KART_094 = REPO / "research" / "cards" / "EDG-2026-094-gecmis-r-giris-riski-paydasi-yeniden-hesap.yaml"
KART_095 = REPO / "research" / "cards" / "EDG-2026-095-gecmis-r-goreli-ozdeslik-damgali-kontrol.yaml"

#: 094 ÇIKTI SÖZLEŞMESİ (ardıl dilim ÖNCESİ hâli, T5 regresyonunun ölçüsü). Sıra da kayıttır:
#: rapor tablosu bu sırayla basılır.
OZET_ALANLARI_094 = ("n", "benimsenmis_n", "benimsemesiz_n", "olculen_n", "olculemeyen_n",
                     "olculemeyen_oran", "benimsenmis_medyan_dR_oran", "benimsemesiz_max_abs_dR",
                     "esikler", "pk1", "kill_list_tetik")
ESIK_ALANLARI_094 = ("benimsenmis_ayrisma_medyan_alt", "benimsemesiz_ozdeslik_tol",
                     "olculemeyen_ust_oran", "kontrol_esitlik_tol")


def _kos(olc_mod, tmp_path, trades, plans=(), olaylar=(), kart="EDG-2026-095"):
    """Sentetik defteri kurup ölçümü İSTENEN KART kipinde koşar (varsayılan: bu kartın kipi)."""
    db = _db_kur(tmp_path / "defter.db", trades, plans)
    ol = _olaylar_yaz(tmp_path / "olaylar.json", list(olaylar))
    return olc_mod.olc(db, ol, "live_paper", None, kart)


def _oranli(seq, oran, pnl=250.0, payda=200.0, **ek):
    """payda_oran'ı İSTENEN değere oturtan satır: payda_eski_ima = payda × oran olacak şekilde
    `r_multiple` geriye çözülür (payda_oran = (pnl / r_eski) / payda)."""
    return _islem(seq, pnl_dollars=pnl, r_multiple=pnl / (payda * oran), **ek)


# ---------------------------------------------------------------------------
# T1 — eşikler KARTTAN (tek kaynak)
# ---------------------------------------------------------------------------
def test_T1a_ESIKLER_095_KARTINDAN_OKUNUR(olc_mod):
    """Kart TEK KAYNAKTIR: ölçüm betiği eşikleri YAML'dan okur, kopya tutmaz."""
    kart = yaml.safe_load(KART_095.read_text(encoding="utf-8"))
    assert olc_mod.esikler_oku("EDG-2026-095") == kart["esikler"]
    assert kart["esikler"] == {
        "benimsenmis_ayrisma_medyan_alt": 0.10,
        "benimsemesiz_goreli_ozdeslik_tol": 0.05,
        "olculemeyen_ust_oran": 0.10,
        "kontrol_esitlik_tol": 0.001,
        "kontrol_asgari_n": 1,
    }


def test_T1b_ESIKLER_094_KARTINDAN_OKUNUR(olc_mod):
    """Aynı yol 094 için de geçerlidir — iki kart, tek okuyucu."""
    kart = yaml.safe_load(KART_094.read_text(encoding="utf-8"))
    assert olc_mod.esikler_oku("EDG-2026-094") == kart["esikler"]
    assert kart["esikler"]["benimsemesiz_ozdeslik_tol"] == 0.01


def test_T1c_DONUK_ESIK_SOZLUGU_KALMADI(olc_mod):
    """Kod tarafında donuk eşik kopyası YOKTUR — kopya olsaydı kartla sessizce ayrışırdı."""
    assert not hasattr(olc_mod, "ESIKLER")


def test_T1d_BILINMEYEN_KART_DURDURUR(olc_mod):
    """Olmayan kart kimliği sessizce varsayılana DÜŞMEZ; ölçüm durur (uydurma yasağı)."""
    with pytest.raises(ValueError, match="kart"):
        olc_mod.esikler_oku("EDG-2026-000")


# ---------------------------------------------------------------------------
# T2 — GÖRELİ özdeşlik kolu
# ---------------------------------------------------------------------------
def test_T2a_GORELI_OZDESLIK_TOLERANS_ICINDE_GECER(olc_mod, tmp_path):
    """payda_oran 1,03 → |1 − oran| = 0,03 ≤ 0,05 → kol GEÇER."""
    sonuc = _kos(olc_mod, tmp_path, [_oranli(1, 1.03)], plans=[_plan("P-1")])
    e = sonuc["ozet"]["esikler"]["benimsemesiz_goreli_ozdeslik_tol"]
    assert sonuc["satirlar"][0]["payda_oran"] == pytest.approx(1.03, abs=1e-9)
    assert (e["deger"], e["esik"], e["yon"], e["n"]) == (pytest.approx(0.03, abs=1e-9), 0.05,
                                                        "<=", 1)
    assert e["gecti"] is True
    # Özdeşlik kolu kill-list'e DÜŞMEZ. (PK-1 kalemi burada zaten tetiktir: sentetik defterde
    # damgalı satır yok — T3a onu ayrıca çiviler.)
    assert not any("özdeşlik" in t for t in sonuc["ozet"]["kill_list_tetik"])


def test_T2b_GORELI_OZDESLIK_TOLERANS_DISINDA_KALIR(olc_mod, tmp_path):
    """payda_oran 1,06 → 0,06 > 0,05 → kol KALIR ve kill-list kalemi ADIYLA düşer."""
    sonuc = _kos(olc_mod, tmp_path, [_oranli(1, 1.06)], plans=[_plan("P-1")])
    e = sonuc["ozet"]["esikler"]["benimsemesiz_goreli_ozdeslik_tol"]
    assert e["deger"] == pytest.approx(0.06, abs=1e-9)
    assert e["gecti"] is False
    assert any("payda/veri kusuru" in t for t in sonuc["ozet"]["kill_list_tetik"])
    assert sonuc["hukum"] == "YOK — Rol-1"


def test_T2c_KORUMA_OCO_SATIRI_OZDESLIK_KUMESINE_GIRMEZ(olc_mod, tmp_path):
    """Düşük güvenli stop'lu satır (koruma_oco) özdeşlik kümesine GİRMEZ — kart adım-1 metni."""
    koruma_satiri = _oranli(2, 1.50, payda=600.0, plan_id="YOK", ticker="BBB")
    sonuc = _kos(olc_mod, tmp_path, [_oranli(1, 1.03), koruma_satiri],
                 plans=[_plan("P-1")], olaylar=[_koruma(ticker="BBB")])
    kaynaklar = {s["seq"]: (s["stop_kaynak"], s["guven"]) for s in sonuc["satirlar"]}
    assert kaynaklar == {1: ("plan", "yuksek"), 2: ("koruma_oco", "dusuk")}
    e = sonuc["ozet"]["esikler"]["benimsemesiz_goreli_ozdeslik_tol"]
    assert (e["n"], e["gecti"]) == (1, True)             # yalnız plan-stop satırı sayıldı
    assert e["deger"] == pytest.approx(0.03, abs=1e-9)   # 0,50 sapma kümeye GİRMEDİ


def test_T2d_BENIMSENMIS_SATIR_OZDESLIK_KUMESINE_GIRMEZ(olc_mod, tmp_path):
    """Benimseme görmüş satır özdeşlik kolunun kümesinde DEĞİLDİR (ayrışma kolunun kümesindedir)."""
    benimsenmis = _islem(1, qty=38, pnl_dollars=-500.0, r_multiple=-500.0 / 170.0)
    sonuc = _kos(olc_mod, tmp_path, [benimsenmis], plans=[_plan("P-1")], olaylar=[_benimseme()])
    e = sonuc["ozet"]["esikler"]["benimsemesiz_goreli_ozdeslik_tol"]
    assert (e["n"], e["deger"], e["gecti"]) == (0, None, None)
    assert sonuc["ozet"]["benimsenmis_n"] == 1


def test_T2e_MUTLAK_OZDESLIK_KOLU_095te_YOK(olc_mod, tmp_path):
    """095 kartında mutlak |ΔR| kolu YOKTUR (selef 094'te KALDI) — çıktıda da olmamalı."""
    sonuc = _kos(olc_mod, tmp_path, [_oranli(1, 1.03)], plans=[_plan("P-1")])
    assert "benimsemesiz_ozdeslik_tol" not in sonuc["ozet"]["esikler"]
    assert sonuc["kart_id"] == "EDG-2026-095"


# ---------------------------------------------------------------------------
# T3 — damgalı kontrol asgarisi
# ---------------------------------------------------------------------------
def test_T3a_DAMGALI_SIFIR_BILGISIZ(olc_mod, tmp_path):
    """Damgalı satır yoksa PK-1 GEÇMİŞ DEĞİL BİLGİSİZDİR; kill-list "yazım YOK" der."""
    sonuc = _kos(olc_mod, tmp_path, [_oranli(1, 1.03)], plans=[_plan("P-1")])
    oz = sonuc["ozet"]
    assert (oz["pk1"]["n"], oz["pk1"]["gecti"]) == (0, None)
    assert oz["pk1"]["neden"] == "damgalı satır < asgari"
    assert "PK-1 n=0 → bilgisiz, yazım YOK" in oz["kill_list_tetik"]
    asg = oz["esikler"]["kontrol_asgari_n"]
    assert (asg["deger"], asg["esik"], asg["yon"], asg["gecti"]) == (0, 1, ">=", False)


def test_T3b_DAMGALI_BIR_ESIT_GECER(olc_mod, tmp_path):
    """Asgariyi TAM karşılayan tek damgalı satır (hesap defterle eşit) PK-1'i GEÇİRİR."""
    rps, qty, pnl = 10.0, 38, 456.0
    extra = {"r_payda": "giris_riski", "qty_taban": qty, "r_payda_usd": qty * rps}
    sonuc = _kos(olc_mod, tmp_path,
                 [_islem(1, qty=qty, pnl_dollars=pnl, r_multiple=pnl / (qty * rps),
                         extra_json=json.dumps(extra))],
                 plans=[_plan("P-1")])
    oz = sonuc["ozet"]
    assert (oz["pk1"]["n"], oz["pk1"]["gecti"], oz["pk1"]["neden"]) == (1, True, None)
    assert oz["esikler"]["kontrol_asgari_n"]["gecti"] is True
    assert not any("bilgisiz" in t for t in oz["kill_list_tetik"])


# ---------------------------------------------------------------------------
# T4 — yazım kümesi
# ---------------------------------------------------------------------------
def test_T4_YAZIM_KUMESI_DUSUK_GUVENLIYI_DISLAR(olc_mod, tmp_path):
    """Yazım kümesi = ölçülebilen VE güveni düşük OLMAYAN satırlar; dışlanan SAYILIR
    (bedel yasası: neyi kaybettiğimiz de ölçülür)."""
    sonuc = _kos(olc_mod, tmp_path,
                 [_islem(1), _islem(2, plan_id="YOK", ticker="BBB"),
                  _islem(3, plan_id="YOK2", ticker="CCC")],
                 plans=[_plan("P-1")], olaylar=[_koruma(ticker="BBB")])
    oz = sonuc["ozet"]
    assert oz["olculen_n"] == 2 and oz["olculemeyen_n"] == 1
    assert oz["yazim_kumesi"] == {"seq": [1], "n": 1, "dislanan_dusuk_guven_n": 1}


# ---------------------------------------------------------------------------
# T5 — 094 kipi regresyonu
# ---------------------------------------------------------------------------
def test_T5a_094_KIPI_OZET_SOZLESMESI_DEGISMEDI(olc_mod, tmp_path):
    """Ardıl dilim eski kartın çıktı YÜZEYİNİ değiştirmez: alanlar ve SIRALARI birebir."""
    sonuc = _kos(olc_mod, tmp_path, [_islem(1)], plans=[_plan("P-1")], kart="EDG-2026-094")
    oz = sonuc["ozet"]
    assert tuple(oz) == OZET_ALANLARI_094
    assert tuple(oz["esikler"]) == ESIK_ALANLARI_094
    assert "yazim_kumesi" not in oz
    assert sonuc["kart_id"] == "EDG-2026-094"
    assert oz["pk1"]["neden"] == "damgalı kapanmış işlem yok"


def test_T5b_094_VARSAYILAN_KIP(olc_mod, tmp_path):
    """`--kart` verilmeyen çağrı GERİYE UYUMLUDUR: 094 kipi (v492'nin bütün çağrı yerleri)."""
    db = _db_kur(tmp_path / "defter.db", [_islem(1)], [_plan("P-1")])
    ol = _olaylar_yaz(tmp_path / "olaylar.json", [])
    assert olc_mod.olc(db, ol)["kart_id"] == "EDG-2026-094"


def test_T5c_094_SAYILARI_DEGISMEDI(olc_mod, tmp_path):
    """Sentetik defterde 094 kipinin SAYILARI: mutlak özdeşlik kolu yerinde, dR = 0."""
    sonuc = _kos(olc_mod, tmp_path, [_islem(1)], plans=[_plan("P-1")], kart="EDG-2026-094")
    oz = sonuc["ozet"]
    assert (oz["n"], oz["benimsenmis_n"], oz["benimsemesiz_n"], oz["olculemeyen_n"]) == (1, 0, 1, 0)
    assert oz["benimsemesiz_max_abs_dR"] == 0.0
    assert oz["esikler"]["benimsemesiz_ozdeslik_tol"]["esik"] == 0.01
    assert oz["esikler"]["benimsemesiz_ozdeslik_tol"]["gecti"] is True


GERCEK_DB = os.environ.get("EDG094_DB")
GERCEK_OLAYLAR = os.environ.get("EDG094_OLAYLAR")
GERCEK_CIKTI = os.environ.get("EDG094_CIKTI")

#: Ardıl dilim ÖNCESİ gerçek koşumun ozet alanları — regresyonun ölçüsü (T5d). Dosya depo
#: DIŞINDADIR (scratchpad); yoksa çivi atlanır, çünkü "ölçemedik" ile "kötü" ayrı şeylerdir.
REGRESYON_ALANLARI = ("n", "benimsenmis_n", "benimsemesiz_n", "olculen_n", "olculemeyen_n",
                      "olculemeyen_oran", "benimsenmis_medyan_dR_oran", "benimsemesiz_max_abs_dR")


def _referans_sonuc():
    """EDG094_CIKTI dizinindeki EN ESKİ `sonuc_094_*.json` — ardıl dilim öncesi taban."""
    if not GERCEK_CIKTI:
        return None
    adaylar = sorted(pathlib.Path(GERCEK_CIKTI).glob("sonuc_094_*.json"))
    if not adaylar:
        return None
    return json.loads(adaylar[0].read_text(encoding="utf-8"))


@pytest.mark.skipif(not (GERCEK_DB and GERCEK_OLAYLAR and GERCEK_CIKTI),
                    reason="EDG094_DB / EDG094_OLAYLAR / EDG094_CIKTI verilmedi — gerçek "
                           "defter kopyası bu koşumda yok")
def test_T5d_GERCEK_KOPYADA_094_REGRESYONU(olc_mod):
    """Gerçek A1 kopyasında 094 kipi ÖNCEKİ sonucun sayılarını birebir tekrar eder (SALT-OKUR,
    hiçbir dosya yazılmaz — `olc()` doğrudan çağrılır)."""
    referans = _referans_sonuc()
    if referans is None:
        pytest.skip("EDG094_CIKTI dizininde ardıl dilim öncesi `sonuc_094_*.json` yok")
    sonuc = olc_mod.olc(GERCEK_DB, GERCEK_OLAYLAR)
    assert sonuc["kart_id"] == "EDG-2026-094"
    for alan in REGRESYON_ALANLARI:
        assert sonuc["ozet"][alan] == referans["ozet"][alan], alan
    assert sonuc["ozet"]["esikler"] == referans["ozet"]["esikler"]
    assert sonuc["ozet"]["kill_list_tetik"] == referans["ozet"]["kill_list_tetik"]


@pytest.mark.skipif(not (GERCEK_DB and GERCEK_OLAYLAR),
                    reason="EDG094_DB / EDG094_OLAYLAR verilmedi")
def test_T5e_GERCEK_KOPYADA_095_KIPI_KOLLARI(olc_mod):
    """Gerçek kopyada 095 kipi: göreli kol ölçülebilir, PK-1 damgalı satır YOKKEN BİLGİSİZ."""
    sonuc = olc_mod.olc(GERCEK_DB, GERCEK_OLAYLAR, "live_paper", None, "EDG-2026-095")
    oz = sonuc["ozet"]
    e = oz["esikler"]["benimsemesiz_goreli_ozdeslik_tol"]
    assert e["n"] >= 1 and e["deger"] is not None
    assert oz["pk1"]["gecti"] is None                  # damgalı satır bekleniyor, bugün yok
    assert oz["yazim_kumesi"]["n"] == oz["olculen_n"] - oz["yazim_kumesi"]["dislanan_dusuk_guven_n"]


# ---------------------------------------------------------------------------
# ADIM-2 ortamı (KOMUT SATIRI sözleşmesi — CLAUDE.md §1)
# ---------------------------------------------------------------------------
def _ops(args):
    return subprocess.run([sys.executable, str(OPS), *args], capture_output=True, text=True)


@pytest.fixture
def ortam(olc_mod, tmp_path):
    """Üç satırlı defter + ölçümü: (1) plan-stop = yüksek güven, (2) koruma_oco = DÜŞÜK güven,
    (3) stop yok = ölçülemedi."""
    db = _db_kur(tmp_path / "defter.db",
                 [_islem(1), _islem(2, plan_id="YOK", ticker="BBB"),
                  _islem(3, plan_id="YOK2", ticker="CCC")],
                 [_plan("P-1")])
    ol = _olaylar_yaz(tmp_path / "olaylar.json", [_koruma(ticker="BBB")])
    cikti = tmp_path / "cikti"
    olc_mod.main(["--db", str(db), "--olaylar", str(ol), "--cikti", str(cikti)])
    olcum_yolu = sorted(cikti.glob("sonuc_094_*.json"))[-1]
    sonuc = json.loads(olcum_yolu.read_text(encoding="utf-8"))
    assert sonuc["ozet"]["olculen_n"] == 2 and sonuc["ozet"]["olculemeyen_n"] == 1
    return {"db": db, "olaylar": ol, "olcum": olcum_yolu, "yedek": tmp_path / "yedek",
            "cikti": cikti, "sonuc": sonuc}


# ---------------------------------------------------------------------------
# T6 — B1 defter bağlaması
# ---------------------------------------------------------------------------
def test_T6a_BASKA_DEFTER_UYGULA_CIKIS_1(ortam, tmp_path):
    """Ölçüm başka bir defter anına aitse yazım BAŞLAMAZ — yedek bile alınmaz."""
    baska = _db_kur(tmp_path / "baska.db", [_islem(1)], [_plan("P-1")])
    once = hashlib.sha256(baska.read_bytes()).hexdigest()
    p = _ops(["--db", str(baska), "--olcum", str(ortam["olcum"]),
              "--yedek-dizin", str(ortam["yedek"]), "--uygula"])
    assert p.returncode == 1, (p.stdout, p.stderr)
    assert "başka bir defter anına ait" in p.stderr
    assert not ortam["yedek"].exists()
    assert hashlib.sha256(baska.read_bytes()).hexdigest() == once


def test_T6b_BASKA_DEFTER_KURU_DA_CIKIS_1(ortam, tmp_path):
    """Kuru koşum da bağlamayı DOĞRULAR — yanlış eşleştirme kuru koşumda fark edilmeli."""
    baska = _db_kur(tmp_path / "baska.db", [_islem(1)], [_plan("P-1")])
    p = _ops(["--db", str(baska), "--olcum", str(ortam["olcum"]),
              "--yedek-dizin", str(ortam["yedek"]), "--kuru"])
    assert p.returncode == 1, (p.stdout, p.stderr)
    assert "başka bir defter anına ait" in p.stderr
    assert "KURU KOŞUM" not in p.stdout


def test_T6c_DOGRU_DEFTER_GECER(ortam):
    """Bağlama tutuyorsa kuru koşum normal akar (kontrol: çivi her şeyi reddetmiyor)."""
    p = _ops(["--db", str(ortam["db"]), "--olcum", str(ortam["olcum"]),
              "--yedek-dizin", str(ortam["yedek"]), "--kuru"])
    assert p.returncode == 0, p.stderr
    assert "KURU KOŞUM" in p.stdout


def test_T6d_KUNYESIZ_OLCUM_REDDEDILIR(ortam, tmp_path):
    """Künyesinde db sha256 OLMAYAN ölçüm "belki doğrudur" diye geçirilmez (uydurma yasağı)."""
    bozuk = json.loads(ortam["olcum"].read_text(encoding="utf-8"))
    bozuk["girdi_kunyesi"]["db"].pop("sha256")
    yol = tmp_path / "kunyesiz.json"
    yol.write_text(json.dumps(bozuk, ensure_ascii=False), encoding="utf-8")
    p = _ops(["--db", str(ortam["db"]), "--olcum", str(yol),
              "--yedek-dizin", str(ortam["yedek"]), "--uygula"])
    assert p.returncode == 1, (p.stdout, p.stderr)
    assert "sha256" in p.stderr
    assert not ortam["yedek"].exists()


# ---------------------------------------------------------------------------
# T7 — güven süzgeci
# ---------------------------------------------------------------------------
def test_T7a_KURU_KOSUM_DUSUK_GUVENLIYI_SAYAR(ortam):
    """Hedef 1 satırdır (plan-stop); düşük güvenli satır AYRICA sayılır."""
    p = _ops(["--db", str(ortam["db"]), "--olcum", str(ortam["olcum"]),
              "--yedek-dizin", str(ortam["yedek"]), "--kuru"])
    assert p.returncode == 0, p.stderr
    assert "Hedef satır: 1" in p.stdout
    assert "atlanan_dusuk_guven=1" in p.stdout
    assert "seq=2" not in p.stdout


def test_T7b_UYGULA_DUSUK_GUVENLI_SATIRA_YAZMAZ(ortam):
    """Kart kill-list 5: düşük güvenli stop'lu satır yazım kümesine GİRMEZ."""
    r_sha = _r_multiple_sha(ortam["db"])
    p = _ops(["--db", str(ortam["db"]), "--olcum", str(ortam["olcum"]),
              "--yedek-dizin", str(ortam["yedek"]), "--uygula", "--bugun", "2026-09-15"])
    assert p.returncode == 0, p.stderr
    assert "yazilan=1 atlanan=0 hedef=1" in p.stdout
    assert "atlanan_dusuk_guven=1" in p.stdout
    assert _r_multiple_sha(ortam["db"]) == r_sha          # eski R alanına DOKUNULMADI
    assert _extra(ortam["db"], 1)["r_multiple_giris"] == pytest.approx(1.25)
    assert _extra(ortam["db"], 2) == {}                   # düşük güvenli satır BOŞ kaldı
    assert _extra(ortam["db"], 3) == {}                   # ölçülemeyen satır BOŞ kaldı


# ---------------------------------------------------------------------------
# T8 — B4 savunma dalları
# ---------------------------------------------------------------------------
def test_T8a_SEQ_DEFTERDE_YOKSA_CIKIS_1_VE_GERI_ALINIR(ortam, tmp_path):
    """Ölçümdeki seq defterde yoksa yazım DURUR ve defter DEĞİŞMEZ."""
    olcum = json.loads(ortam["olcum"].read_text(encoding="utf-8"))
    for s in olcum["satirlar"]:
        if s["olculebildi"] and s["guven"] != "dusuk":
            s["seq"] = 999
    yol = tmp_path / "kayik.json"
    yol.write_text(json.dumps(olcum, ensure_ascii=False), encoding="utf-8")
    r_sha = _r_multiple_sha(ortam["db"])
    p = _ops(["--db", str(ortam["db"]), "--olcum", str(yol),
              "--yedek-dizin", str(ortam["yedek"]), "--uygula"])
    assert p.returncode == 1, (p.stdout, p.stderr)
    assert "defterde YOK" in p.stderr
    assert _r_multiple_sha(ortam["db"]) == r_sha
    assert _extra(ortam["db"], 1) == {} and _extra(ortam["db"], 2) == {}


def test_T8b_SAYIM_UYUSMAZLIGI_ROLLBACK(ortam, monkeypatch):
    """"Yazılan ≠ beklenen" dalı: UPDATE 0 satır etkilemiş gibi davranırsa TRANSACTION GERİ
    ALINIR ve defter değişmez.

    NEDEN MONKEYPATCH: bu dal komut satırından TETİKLENEMEZ (SELECT satırı bulduktan sonra
    UPDATE'in eşleşmemesi normal koşulda imkânsız). Dalın kendisi gerçek bir transaction
    üzerinde koşar — geri alımın GERÇEKTEN olduğu defterden ölçülür."""
    ops_mod = betikten_modul_yukle(OPS, "edg094_ops_v494")
    gercek_connect = sqlite3.connect

    class _SahteImlec:
        rowcount = 0                                  # çapa-sentetik: UPDATE hiç satır etkilememiş gibi

    class _SifirlayanBaglanti:
        def __init__(self, con):
            self._con = con

        def execute(self, sql, *a):
            imlec = self._con.execute(sql, *a)
            return _SahteImlec() if sql.lstrip().upper().startswith("UPDATE") else imlec

        def close(self):
            self._con.close()

        @property
        def isolation_level(self):
            return self._con.isolation_level

        @isolation_level.setter
        def isolation_level(self, deger):
            self._con.isolation_level = deger

    class _Shim:
        Error = sqlite3.Error

        @staticmethod
        def connect(*a, **k):
            return _SifirlayanBaglanti(gercek_connect(*a, **k))

    monkeypatch.setattr(ops_mod, "sqlite3", _Shim)
    hedefler, dusuk = ops_mod.hedefleri_sec(ortam["sonuc"])
    assert (len(hedefler), dusuk) == (1, 1)
    r_sha = _r_multiple_sha(ortam["db"])
    with pytest.raises(RuntimeError, match="beklenenden"):
        ops_mod.uygula(ortam["db"], hedefler, "2026-09-15")
    assert _r_multiple_sha(ortam["db"]) == r_sha
    assert _extra(ortam["db"], 1) == {}                # geri alındı: hiçbir alan yazılmadı


def test_T8c_SAYIM_TUTARSA_YAZILIR(ortam):
    """Kontrol (T8b'nin negatifi): aynı yol dokunulmadan koşunca satır GERÇEKTEN yazılır."""
    ops_mod = betikten_modul_yukle(OPS, "edg094_ops_v494_kontrol")
    hedefler, _ = ops_mod.hedefleri_sec(ortam["sonuc"])
    assert ops_mod.uygula(ortam["db"], hedefler, "2026-09-15") == {
        "yazilan": 1, "atlanan": 0, "hedef": 1}
    assert _extra(ortam["db"], 1)["r_giris_damga"].endswith("2026-09-15")


# ---------------------------------------------------------------------------
# T9 — B3: qty_taban varken çapraz kontrol UYGULANMAZ
# ---------------------------------------------------------------------------
def test_T9a_QTY_TABAN_VARKEN_CAPRAZ_KONTROL_YOK(olc_mod, tmp_path):
    """`extra_json.qty_taban` BİRİNCİ kaynaktır: benimseme olayı defterdeki qty ile tutmasa bile
    satır ölçülür (çapraz kontrol YALNIZ olay yolunun sağlamasıdır — B3)."""
    sonuc = _kos(olc_mod, tmp_path,
                 [_islem(1, qty=20, extra_json=json.dumps({"qty_taban": 12}))],
                 plans=[_plan("P-1")], olaylar=[_benimseme(yeni=38)])
    s = sonuc["satirlar"][0]
    assert (s["qty_giris"], s["qty_giris_kaynak"]) == (12.0, "extra_json.qty_taban")
    assert (s["benimsenmis_mi"], s["olculebildi"], s["neden"]) == (True, True, None)
    assert s["r_yeni"] == pytest.approx(250.0 / (12.0 * 10.0))


def test_T9b_QTY_TABAN_YOKKEN_CAPRAZ_KONTROL_ISLER(olc_mod, tmp_path):
    """Kontrol (T9a'nın negatifi): `qty_taban` YOKKEN aynı veri satırı ÖLÇÜLEMEZ yapar."""
    sonuc = _kos(olc_mod, tmp_path, [_islem(1, qty=20)], plans=[_plan("P-1")],
                 olaylar=[_benimseme(yeni=38)])
    s = sonuc["satirlar"][0]
    assert (s["olculebildi"], s["neden"]) == (False, "benimseme yeni≠qty")


def test_T9c_R2_HUKMU_B3u_YAZIYOR(olc_mod):
    """Hüküm metni bu sırayı AÇIKÇA söyler — kod ile metin ayrışırsa ölçüm hangi tanımla
    koştuğunu yanlış damgalar."""
    assert "qty_taban" in olc_mod.HUKUMLER["R2"]
    assert "UYGULANMAZ" in olc_mod.HUKUMLER["R2"]


# ---------------------------------------------------------------------------
# 095 kipinin çıktı dosyası: adı KART numarasını taşır
# ---------------------------------------------------------------------------
def test_T10_095_CIKTI_DOSYA_ADI_KART_NUMARASINI_TASIR(olc_mod, tmp_path):
    """İki kartın çıktıları aynı dizinde KARIŞMAZ — dosya adı kart numarasını taşır."""
    db = _db_kur(tmp_path / "defter.db", [_islem(1)], [_plan("P-1")])
    ol = _olaylar_yaz(tmp_path / "olaylar.json", [])
    cikti = tmp_path / "cikti"
    assert olc_mod.main(["--db", str(db), "--olaylar", str(ol), "--cikti", str(cikti),
                         "--kart", "EDG-2026-095"]) == 0
    assert sorted(p.name.split("_")[0] for p in cikti.glob("*_095_*")) == ["RAPOR", "sonuc"]
    assert not list(cikti.glob("*_094_*"))
    rapor = sorted(cikti.glob("RAPOR_095_*.md"))[-1].read_text(encoding="utf-8")
    assert rapor.startswith("# EDG-2026-095 ")
    assert "## Yazım kümesi" in rapor


def test_T11_094_CIKTI_DOSYA_ADI_DEGISMEDI(olc_mod, tmp_path):
    """Regresyon: 094 kipi hâlâ `sonuc_094_*.json` üretir (ops betiğinin `--olcum` girdisi)."""
    db = _db_kur(tmp_path / "defter.db", [_islem(1)], [_plan("P-1")])
    ol = _olaylar_yaz(tmp_path / "olaylar.json", [])
    cikti = tmp_path / "cikti"
    assert olc_mod.main(["--db", str(db), "--olaylar", str(ol), "--cikti", str(cikti)]) == 0
    assert len(list(cikti.glob("sonuc_094_*.json"))) == 1
    assert len(list(cikti.glob("RAPOR_094_*.md"))) == 1


def test_T13_YAZIM_KUMESI_ILE_OPS_HEDEFLERI_AYNI(olc_mod, ortam):
    """AYRIŞMA ÇİVİSİ (tek-kaynak yasası): "hangi satır yazılır" sorusunun İKİ uygulaması var —
    ölçüm tarafında `yazim_kumesi`, ops tarafında `hedefleri_sec` — çünkü iki dünya birbirini
    İTHAL EDEMEZ. Kopya kaçınılmazsa ayrışma çivisi zorunludur: AYNI defter üzerinde ikisi aynı
    seq listesini ve aynı dışlama sayısını vermeli."""
    sonuc_095 = olc_mod.olc(ortam["db"], ortam["olaylar"], "live_paper", None, "EDG-2026-095")
    ops_mod = betikten_modul_yukle(OPS, "edg094_ops_v494_ayrisma")
    hedefler, atlanan_dusuk = ops_mod.hedefleri_sec(sonuc_095)
    yk = sonuc_095["ozet"]["yazim_kumesi"]
    assert [s["seq"] for s in hedefler] == yk["seq"] == [1]
    assert atlanan_dusuk == yk["dislanan_dusuk_guven_n"] == 1
    assert olc_mod.DUSUK_GUVEN == ops_mod.DUSUK_GUVEN


def test_T12_KOPYA_DEFTER_YEDEGI_BAGLAMAYI_KIRAR(ortam, tmp_path):
    """OPERATÖR TUZAĞI, AÇIKÇA ÇİVİLENİR: ölçüm defterin KOPYASINDA yapılıp yazım CANLI dosyaya
    denenirse (sqlite backup farklı bayt üretir) bağlama TUTMAZ ve yazım olmaz. Reçete:
    ADIM-1 ile ADIM-2 AYNI dosya üzerinde, worker durmuşken koşar."""
    kopya = tmp_path / "kopya.db"
    shutil.copy2(ortam["db"], kopya)
    with sqlite3.connect(str(kopya)) as con:            # kopya canlıda ilerlemiş gibi değişir
        con.execute("UPDATE trades SET bars_held = 7 WHERE seq = 3")
    p = _ops(["--db", str(kopya), "--olcum", str(ortam["olcum"]),
              "--yedek-dizin", str(ortam["yedek"]), "--uygula"])
    assert p.returncode == 1, (p.stdout, p.stderr)
    assert "başka bir defter anına ait" in p.stderr
    assert _extra(kopya, 1) == {}
