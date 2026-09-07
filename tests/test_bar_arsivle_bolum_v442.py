"""v442 — `ops/bar_arsivle.py` BÖLÜMLEME seçeneği (`--bolum {sembol,yil,ay}`) ve
`ops/bar_sorgu.py`nin üç yerleşimi birden okuması (TSK-020 [UYGULA-3], 2026-09-07).

NUMARA SEÇİMİ: `ls tests | grep -o 'v[0-9]*' | sort -V | tail -1` ile ölçüldü (2026-09-07) —
ağaçtaki en büyük numara v439; v440/v441 bu turda paralel yürüyen kardeş ajanlara ayrılmış
(brief beyanı), v442 BOŞ. Çakışma yok.

NEDEN VAR — ÖLÇÜM TASARIMI ÇÜRÜTTÜ. A1'deki ilk gerçek koşum (S4, 2026-09-07) ay/sembol
bölümlemesinin GÜNLÜK barlarda çöktüğünü gösterdi: 260 sembol × ~273 ay ≈ 70 bin küçük parquet
dosyası; koşum 480 s tavanında bitmedi (RC=124) ve YARIM hâlde bile 134 MB tuttu — kaynağı olan
CSV 60 MB iken. Sebep ölçüldü: günlük barda bir ay dosyası ~21 satırdır ve o boyutta parquet
footer + şema metadata + ZSTD blok yükü İÇERİKTEN büyüktür. Bölümleme artık bir SEÇENEKTİR ve
varsayılanı `sembol` (sembol başına TEK dosya, ~5,7 bin satır).

NEYİ ÇİVİLER:
  1. VARSAYILAN `sembol` — `<hedef>/<SEMBOL>.parquet`; dosya sayısı SEMBOL SAYISINA eşit.
  2. `yil` — `<hedef>/<YIL>/<SEMBOL>.parquet`; `ay` — eski yerleşim (UYUMLULUK).
  3. MANİFEST BEYANI — manifest `bolum` alanı taşır; kayıt ANAHTARI bölüme göre şekillenir.
  4. DÜZEN UYUŞMAZLIĞI DURDURUR — farklı bölümle koşulunca rc 5, hedefe DOKUNULMAZ, gerekçe
     `--temizle`yi söyler. (Karışık yerleşim, okuyucuda sembolü İKİ KEZ sayardı.)
  5. `--temizle` YALNIZ KAYITLI dosyaları siler — manifestte olmayan (yabancı) dosyaya
     DOKUNMAZ; kuru koşumda hiçbir şey silinmez.
  6. `--ay` süzgeci YALNIZ `--bolum ay` ile — sembol/yıl düzeninde dosya bir AYın değil
     sembolün/yılın TAMAMIdır; ay süzgeci YARIM dosya yazıp manifeste "tam" diye kaydederdi.
  7. OKUYUCU ÜÇ DÜZENİ DE OKUR — `ops/bar_sorgu.py` `kapsam` sonucu üç yerleşimde AYNIdır.
  8. BEDEL YASASI — rapor dosya sayısı + toplam bayt + CSV bayt oranı basar; ve sentetik
     3 sembol × 30 ay veride sembol düzeninin toplam baytı ay düzeninin ALTINDADIR (ölçülür).

GERÇEK DEFTERE DOKUNULMAZ: her çivi `sandbox_state` altında, kendi `tmp_path` dizininde koşar;
araçlar SÜREÇ İÇİNDE `main([...])` ile çağrılır (gerekçe v435 başlığında: `sanitize_bars`
`meridian.obs`a ulaşır ve `subprocess` yamayı görmez).
"""

from __future__ import annotations

import json

import pytest

from meridian.adapters import data as _data
from ops import bar_arsivle, bar_sorgu


# ---------------------------------------------------------------------------------------------
# Sentetik defter — tarihler GERÇEK XNYS seanslarından gelir (uydurma tarih `sanitize_bars`ın
# takvim kapısında hayalet sayılır ve çivi ölçtüğünü sandığı şeyi ölçmez).
# ---------------------------------------------------------------------------------------------

def _ay_seanslari(ay: str) -> list[str]:
    """`ay` (AAAA-AA) içindeki TÜM XNYS seansları. Takvimin TEK kaynağı `_sessions`."""
    return sorted(g for g in _data._sessions() if g.startswith(ay))


def _aylar(baslangic_yil: int, baslangic_ay: int, adet: int) -> list[str]:
    cikti = []
    y, a = baslangic_yil, baslangic_ay
    for _ in range(adet):
        cikti.append(f"{y:04d}-{a:02d}")
        a += 1
        if a == 13:
            y, a = y + 1, 1
    return cikti


def _csv_yaz(dizin, ad: str, gunler: list[str], baslangic: float = 100.0) -> None:
    """`date,open,high,low,close,volume` — canlı önbelleğin ölçülmüş şeması. Fiyatlar yumuşak
    ilerler; sıçrama yazılsaydı `sanitize_bars` satırı karantinaya alır, sayım kayardı."""
    dizin.mkdir(parents=True, exist_ok=True)
    satirlar = ["date,open,high,low,close,volume"]
    for i, g in enumerate(gunler):
        c = baslangic + (i % 40) * 0.25
        satirlar.append(f"{g},{c:.2f},{c + 0.5:.2f},{c - 0.5:.2f},{c + 0.2:.2f},{1000000 + i}")
    (dizin / ad).write_text("\n".join(satirlar) + "\n", encoding="utf-8")


OCAK = "2024-01"
SUBAT = "2024-02"


@pytest.fixture
def kaynak(tmp_path):
    """İki aylık AAPL + tek aylık MSFT — v435'in fikstürüyle aynı şekil, tüm seanslarla."""
    d = tmp_path / "bars_kaynak"
    ocak, subat = _ay_seanslari(OCAK), _ay_seanslari(SUBAT)
    if not ocak or not subat:
        pytest.skip("takvim ölçülemedi — XNYS seansları yok")
    _csv_yaz(d, "aapl.csv", ocak + subat)
    _csv_yaz(d, "msft.csv", ocak, baslangic=300.0)
    return d


@pytest.fixture
def hedef(tmp_path):
    return tmp_path / "barlar_hedef"


def _dosyalar(kok):
    return sorted(p.relative_to(kok).as_posix() for p in kok.rglob("*") if p.is_file())


def _parquetler(kok):
    return sorted(p.relative_to(kok).as_posix() for p in kok.rglob("*.parquet"))


def _manifest(hedef):
    return json.loads((hedef / bar_arsivle.MANIFEST_ADI).read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------------------------
# 1-2. ÜÇ YERLEŞİM
# ---------------------------------------------------------------------------------------------

def test_VARSAYILAN_bolum_SEMBOL_sembol_basina_TEK_dosya(sandbox_state, kaynak, hedef, capsys):
    """Bayrak verilmezse yerleşim `sembol`dür: iki sembol → İKİ parquet (ay sayısına bakmaz)."""
    rc = bar_arsivle.main(["--kaynak-dizin", str(kaynak), "--hedef", str(hedef), "--uygula"])
    assert rc == 0, capsys.readouterr().err
    assert _parquetler(hedef) == ["AAPL.parquet", "MSFT.parquet"]
    assert bar_arsivle.VARSAYILAN_BOLUM == bar_arsivle.BOLUM_SEMBOL


def test_SEMBOL_duzeni_dosya_sayisi_SEMBOL_SAYISINA_esit(sandbox_state, tmp_path, hedef, capsys):
    """A1 vakasının çekirdeği: dosya sayısı AY sayısıyla ÇARPILMAZ. Üç sembol, 30 ay → 3 dosya."""
    kaynak = tmp_path / "bars_genis"
    aylar = _aylar(2022, 1, 30)
    gunler = [g for ay in aylar for g in _ay_seanslari(ay)]
    if len(gunler) < 400:
        pytest.skip(f"takvim ölçülemedi — 30 ayda {len(gunler)} seans bulundu")
    for i, ad in enumerate(("aapl.csv", "msft.csv", "nvda.csv")):
        _csv_yaz(kaynak, ad, gunler, baslangic=100.0 + 50 * i)

    rc = bar_arsivle.main(["--kaynak-dizin", str(kaynak), "--hedef", str(hedef), "--uygula"])
    assert rc == 0, capsys.readouterr().err
    assert len(_parquetler(hedef)) == 3, _parquetler(hedef)


def test_YIL_duzeni_yil_dizinlerine_yazar(sandbox_state, kaynak, hedef, capsys):
    rc = bar_arsivle.main(["--kaynak-dizin", str(kaynak), "--hedef", str(hedef),
                           "--bolum", "yil", "--uygula"])
    assert rc == 0, capsys.readouterr().err
    assert _parquetler(hedef) == ["2024/AAPL.parquet", "2024/MSFT.parquet"]


def test_AY_duzeni_UYUMLULUK_eski_yerlesim(sandbox_state, kaynak, hedef, capsys):
    """`ay` seçeneği v435'in ölçtüğü yerleşimi AYNEN üretir — uyumluluk kasten korunur."""
    rc = bar_arsivle.main(["--kaynak-dizin", str(kaynak), "--hedef", str(hedef),
                           "--bolum", "ay", "--uygula"])
    assert rc == 0, capsys.readouterr().err
    assert _parquetler(hedef) == ["2024-01/AAPL.parquet", "2024-01/MSFT.parquet",
                                  "2024-02/AAPL.parquet"]


def test_BILINMEYEN_bolum_rc2(sandbox_state, kaynak, hedef):
    with pytest.raises(SystemExit) as e:
        bar_arsivle.main(["--kaynak-dizin", str(kaynak), "--hedef", str(hedef),
                          "--bolum", "gun"])
    assert e.value.code == 2


# ---------------------------------------------------------------------------------------------
# 3. MANİFEST BEYANI
# ---------------------------------------------------------------------------------------------

def test_MANIFEST_bolum_alani_tasir_ve_kayit_ANAHTARI_boluma_gore(sandbox_state, kaynak, hedef):
    bar_arsivle.main(["--kaynak-dizin", str(kaynak), "--hedef", str(hedef), "--uygula"])
    m = _manifest(hedef)
    assert m["bolum"] == "sembol"
    kayit = m["semboller"]["AAPL"]
    assert {"sha256", "satir", "ilk", "son"} <= set(kayit), kayit
    assert kayit["satir"] == len(_ay_seanslari(OCAK)) + len(_ay_seanslari(SUBAT))


def test_MANIFEST_YIL_duzeninde_yil_anahtarli(sandbox_state, kaynak, hedef):
    bar_arsivle.main(["--kaynak-dizin", str(kaynak), "--hedef", str(hedef),
                      "--bolum", "yil", "--uygula"])
    m = _manifest(hedef)
    assert m["bolum"] == "yil"
    assert set(m["semboller"]["AAPL"]) == {"2024"}


def test_MANIFEST_AY_duzeninde_ay_anahtarli(sandbox_state, kaynak, hedef):
    bar_arsivle.main(["--kaynak-dizin", str(kaynak), "--hedef", str(hedef),
                      "--bolum", "ay", "--uygula"])
    m = _manifest(hedef)
    assert m["bolum"] == "ay"
    assert set(m["semboller"]["AAPL"]) == {OCAK, SUBAT}


def test_SEMBOL_duzeninde_IDEMPOTENT(sandbox_state, kaynak, hedef, capsys):
    bar_arsivle.main(["--kaynak-dizin", str(kaynak), "--hedef", str(hedef), "--uygula"])
    capsys.readouterr()
    once = {p: p.stat().st_mtime_ns for p in hedef.rglob("*.parquet")}
    rc = bar_arsivle.main(["--kaynak-dizin", str(kaynak), "--hedef", str(hedef), "--uygula"])
    cikti = capsys.readouterr().out
    assert rc == 0
    assert cikti.count("atlandı") == 2, cikti
    assert {p: p.stat().st_mtime_ns for p in hedef.rglob("*.parquet")} == once


# ---------------------------------------------------------------------------------------------
# 4. DÜZEN UYUŞMAZLIĞI DURDURUR
# ---------------------------------------------------------------------------------------------

def test_FARKLI_BOLUMLE_kosum_rc5_ve_hedefe_DOKUNMAZ(sandbox_state, kaynak, hedef, capsys):
    bar_arsivle.main(["--kaynak-dizin", str(kaynak), "--hedef", str(hedef),
                      "--bolum", "ay", "--uygula"])
    capsys.readouterr()
    once = _dosyalar(hedef)

    rc = bar_arsivle.main(["--kaynak-dizin", str(kaynak), "--hedef", str(hedef),
                           "--bolum", "sembol", "--uygula"])
    hata = capsys.readouterr().err
    assert rc == 5, hata
    assert "--temizle" in hata and "ay" in hata and "sembol" in hata
    assert _dosyalar(hedef) == once, "uyuşmazlıkta hedefe DOKUNULDU"


def test_AYNI_BOLUMLE_kosum_DURMAZ(sandbox_state, kaynak, hedef, capsys):
    bar_arsivle.main(["--kaynak-dizin", str(kaynak), "--hedef", str(hedef),
                      "--bolum", "yil", "--uygula"])
    capsys.readouterr()
    rc = bar_arsivle.main(["--kaynak-dizin", str(kaynak), "--hedef", str(hedef),
                           "--bolum", "yil", "--uygula"])
    assert rc == 0, capsys.readouterr().err


def test_BOLUMSUZ_MANIFEST_ay_sayilir(sandbox_state, kaynak, hedef, capsys):
    """`--bolum` seçeneğinden ÖNCEKİ araç sürümünün yazdığı manifestte `bolum` alanı YOKTUR;
    o arşiv AY yerleşimindedir. Alan yoksa `ay` varsayılır ve `--bolum sembol` DURUR."""
    bar_arsivle.main(["--kaynak-dizin", str(kaynak), "--hedef", str(hedef),
                      "--bolum", "ay", "--uygula"])
    yol = hedef / bar_arsivle.MANIFEST_ADI
    m = json.loads(yol.read_text(encoding="utf-8"))
    m.pop("bolum")
    yol.write_text(json.dumps(m), encoding="utf-8")
    capsys.readouterr()

    rc = bar_arsivle.main(["--kaynak-dizin", str(kaynak), "--hedef", str(hedef), "--uygula"])
    assert rc == 5, capsys.readouterr().err


# ---------------------------------------------------------------------------------------------
# 5. --temizle
# ---------------------------------------------------------------------------------------------

def test_TEMIZLE_eski_duzeni_siler_YABANCI_dosyaya_DOKUNMAZ(sandbox_state, kaynak, hedef,
                                                            capsys):
    bar_arsivle.main(["--kaynak-dizin", str(kaynak), "--hedef", str(hedef),
                      "--bolum", "ay", "--uygula"])
    yabanci_kok = hedef / "notlar.txt"
    yabanci_kok.write_text("elle konmuş", encoding="utf-8")
    yabanci_parquet = hedef / OCAK / "YABANCI.parquet"
    yabanci_parquet.write_bytes(b"manifeste kayitli DEGIL")
    capsys.readouterr()

    rc = bar_arsivle.main(["--kaynak-dizin", str(kaynak), "--hedef", str(hedef),
                           "--bolum", "sembol", "--uygula", "--temizle"])
    hata = capsys.readouterr().err
    assert rc == 0, hata
    assert yabanci_kok.is_file(), "yabancı dosya SİLİNDİ"
    assert yabanci_parquet.is_file(), "manifeste kayıtlı olmayan parquet SİLİNDİ"
    assert not (hedef / OCAK / "AAPL.parquet").exists(), "eski düzen dosyası kaldı"
    assert not (hedef / SUBAT).exists(), "boşalan bölüm dizini kaldı"
    assert (hedef / "AAPL.parquet").is_file() and (hedef / "MSFT.parquet").is_file()
    assert _manifest(hedef)["bolum"] == "sembol"


def test_TEMIZLE_KURU_kosumda_HICBIR_SEY_silmez(sandbox_state, kaynak, hedef, capsys):
    bar_arsivle.main(["--kaynak-dizin", str(kaynak), "--hedef", str(hedef),
                      "--bolum", "ay", "--uygula"])
    capsys.readouterr()
    once = _dosyalar(hedef)

    rc = bar_arsivle.main(["--kaynak-dizin", str(kaynak), "--hedef", str(hedef),
                           "--bolum", "sembol", "--temizle"])
    yakala = capsys.readouterr()
    assert rc == 0, yakala.err
    assert _dosyalar(hedef) == once, "KURU koşum sildi"
    assert "silinecek" in yakala.err.lower(), yakala.err


# ---------------------------------------------------------------------------------------------
# 6. `--ay` süzgeci YALNIZ `--bolum ay` ile
# ---------------------------------------------------------------------------------------------

@pytest.mark.parametrize("bolum", ["sembol", "yil"])
def test_AY_suzgeci_SEMBOL_ve_YIL_duzeninde_rc2(sandbox_state, kaynak, hedef, capsys, bolum):
    rc = bar_arsivle.main(["--kaynak-dizin", str(kaynak), "--hedef", str(hedef),
                           "--bolum", bolum, "--ay", OCAK, "--uygula"])
    hata = capsys.readouterr().err
    assert rc == 2, hata
    assert "--ay" in hata and "--bolum ay" in hata
    assert not hedef.exists(), "kullanım hatasında hedef YARATILDI"


def test_AY_suzgeci_AY_duzeninde_calisir(sandbox_state, kaynak, hedef, capsys):
    rc = bar_arsivle.main(["--kaynak-dizin", str(kaynak), "--hedef", str(hedef),
                           "--bolum", "ay", "--ay", SUBAT, "--uygula"])
    assert rc == 0, capsys.readouterr().err
    assert _parquetler(hedef) == ["2024-02/AAPL.parquet"]


# ---------------------------------------------------------------------------------------------
# 7. OKUYUCU ÜÇ DÜZENİ DE OKUR
# ---------------------------------------------------------------------------------------------

@pytest.mark.parametrize("bolum", ["sembol", "yil", "ay"])
def test_BAR_SORGU_uc_duzende_AYNI_kapsam(sandbox_state, kaynak, tmp_path, capsys, bolum):
    hedef = tmp_path / f"barlar_{bolum}"
    assert bar_arsivle.main(["--kaynak-dizin", str(kaynak), "--hedef", str(hedef),
                             "--bolum", bolum, "--uygula"]) == 0
    capsys.readouterr()

    rc = bar_sorgu.main(["--dizin", str(hedef), "--sorgu", "kapsam", "--json"])
    yakala = capsys.readouterr()
    assert rc == 0, yakala.err
    kayitlar = {json.loads(s)["sembol"]: json.loads(s)
                for s in yakala.out.strip().splitlines()}
    ocak, subat = _ay_seanslari(OCAK), _ay_seanslari(SUBAT)
    assert set(kayitlar) == {"AAPL", "MSFT"}
    assert kayitlar["AAPL"]["satir"] == len(ocak) + len(subat)
    assert kayitlar["AAPL"]["ilk"] == ocak[0] and kayitlar["AAPL"]["son"] == subat[-1]
    assert kayitlar["MSFT"]["satir"] == len(ocak)


def test_BAR_SORGU_SEMBOL_duzeninde_AY_suzgeci_icerikten_turer(sandbox_state, kaynak, hedef,
                                                               capsys):
    """`ay` sütunu DİZİN adından değil TARİHTEN türer — sembol düzeninde dizin YOKTUR ve
    ay süzgeci yine de çalışır."""
    assert bar_arsivle.main(["--kaynak-dizin", str(kaynak), "--hedef", str(hedef),
                             "--uygula"]) == 0
    capsys.readouterr()
    rc = bar_sorgu.main(["--dizin", str(hedef), "--sorgu", "kapsam", "--ay", SUBAT, "--json"])
    yakala = capsys.readouterr()
    assert rc == 0, yakala.err
    kayitlar = [json.loads(s) for s in yakala.out.strip().splitlines()]
    assert [k["sembol"] for k in kayitlar] == ["AAPL"]
    assert kayitlar[0]["satir"] == len(_ay_seanslari(SUBAT))


# ---------------------------------------------------------------------------------------------
# 8. BEDEL YASASI — kazanç ÖLÇÜLÜR, bedel de ÖLÇÜLÜR
# ---------------------------------------------------------------------------------------------

def test_BEDEL_raporu_dosya_sayisi_bayt_ve_CSV_orani_basar(sandbox_state, kaynak, hedef,
                                                           capsys):
    rc = bar_arsivle.main(["--kaynak-dizin", str(kaynak), "--hedef", str(hedef), "--uygula"])
    hata = capsys.readouterr().err
    assert rc == 0, hata
    assert "BEDEL" in hata, hata
    assert "dosya" in hata and "bayt" in hata and "oran" in hata, hata
    toplam = sum(p.stat().st_size for p in hedef.rglob("*.parquet"))
    assert str(toplam) in hata, f"ölçülen toplam bayt raporda yok ({toplam}): {hata}"


def test_BEDEL_KURU_kosumda_bayt_UYDURULMAZ(sandbox_state, kaynak, hedef, capsys):
    rc = bar_arsivle.main(["--kaynak-dizin", str(kaynak), "--hedef", str(hedef)])
    hata = capsys.readouterr().err
    assert rc == 0, hata
    assert "ÖLÇÜLEMEDİ" in hata, hata


def test_OPERATOR_KOSUMU_bolum_gocu_uctan_uca(sandbox_state, kaynak, hedef, capsys):
    """YENİ BAYRAKLARIN OPERATÖR BİÇİMİNDE, GERÇEK argv İLE zinciri (teslim kapısı, vaka
    2026-08-30: 18 çivi yeşilken `--uygula` sessizce yok sayılıyordu). Zincir: kuru koşum →
    varsayılan yerleşimle yaz → oku → yanlış bölümle koş (DURUR) → `--temizle` ile göç → oku."""
    ortak = ["--kaynak-dizin", str(kaynak), "--hedef", str(hedef)]

    assert bar_arsivle.main(ortak) == 0
    assert not hedef.exists(), "kuru koşum yazdı"

    assert bar_arsivle.main(ortak + ["--uygula"]) == 0
    assert (hedef / "AAPL.parquet").is_file()
    assert bar_sorgu.main(["--dizin", str(hedef), "--sorgu", "kapsam"]) == 0
    capsys.readouterr()

    assert bar_arsivle.main(ortak + ["--bolum", "yil", "--uygula"]) == 5, "yanlış bölüm DURMADI"
    assert (hedef / "AAPL.parquet").is_file(), "durduğu hâlde hedefe dokundu"
    capsys.readouterr()

    assert bar_arsivle.main(ortak + ["--bolum", "yil", "--temizle", "--uygula"]) == 0
    assert not (hedef / "AAPL.parquet").exists(), "eski düzen dosyası kaldı"
    assert (hedef / "2024" / "AAPL.parquet").is_file()
    capsys.readouterr()

    assert bar_sorgu.main(["--dizin", str(hedef), "--sorgu", "kapsam", "--json"]) == 0
    yakala = capsys.readouterr()
    kayitlar = {json.loads(s)["sembol"] for s in yakala.out.strip().splitlines()}
    assert kayitlar == {"AAPL", "MSFT"}, yakala.err


def test_SEMBOL_duzeni_toplam_bayt_AY_duzeninin_ALTINDA(sandbox_state, tmp_path, capsys):
    """A1 vakasının ölçülebilir çekirdeği: 3 sembol × 30 ay günlük barda sembol düzeninin
    TOPLAM baytı ay düzeninin altındadır. Sayılar rapora yazılır (bedel yasası)."""
    kaynak = tmp_path / "bars_bedel"
    aylar = _aylar(2022, 1, 30)
    gunler = [g for ay in aylar for g in _ay_seanslari(ay)]
    if len(gunler) < 400:
        pytest.skip(f"takvim ölçülemedi — 30 ayda {len(gunler)} seans bulundu")
    for i, ad in enumerate(("aapl.csv", "msft.csv", "nvda.csv")):
        _csv_yaz(kaynak, ad, gunler, baslangic=100.0 + 50 * i)

    olcum = {}
    for bolum in ("sembol", "ay"):
        h = tmp_path / f"barlar_{bolum}"
        assert bar_arsivle.main(["--kaynak-dizin", str(kaynak), "--hedef", str(h),
                                 "--bolum", bolum, "--uygula"]) == 0
        parquetler = list(h.rglob("*.parquet"))
        olcum[bolum] = (len(parquetler), sum(p.stat().st_size for p in parquetler))
    capsys.readouterr()

    csv_bayt = sum(p.stat().st_size for p in kaynak.glob("*.csv"))
    mesaj = (f"seans={len(gunler)} csv={csv_bayt}B "
             f"sembol={olcum['sembol'][0]} dosya/{olcum['sembol'][1]}B "
             f"ay={olcum['ay'][0]} dosya/{olcum['ay'][1]}B")
    assert olcum["sembol"][0] == 3 and olcum["ay"][0] == 3 * len(aylar), mesaj
    assert olcum["sembol"][1] < olcum["ay"][1], mesaj
