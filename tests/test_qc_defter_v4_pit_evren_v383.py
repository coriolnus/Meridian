"""v383 — EDG-2026-021 defter v4 (PIT S&P 500 evreni) + ⑤ Security Master delist sondası.

NUMARA TARAMASI (2026-09-03): `grep -rl v383 tests/ docs/ research/` BOŞ döndü; tests/ altındaki
en yüksek numara v382 idi. v383 SERBEST — çakışma yok, taşıma gerekmedi.

NE ÇİVİLER — defter QC'de OPERATÖR tarafından koşar, burada KOŞMAZ (QC'ye bağlanmak yasak).
Bu yüzden çiviler koşum sonucunu değil, KOŞMADAN ÖNCE ölçülebilen sözleşmeyi tutar:
  1. Aralık üreticisi CSV üyeliğini birebir yeniden üretir (60 örnek gün, sabit tohum).
  2. Üretilen parça dosyaları QC'nin ÖLÇÜLMÜŞ 32.000 karakter sınırının altında + ast geçer.
  3. Üretim deterministik (`--kontrol` bayt-aynı) ve kaynak sha'sı CSV ile eşit.
  4. v4 ANAHTAR'ı v3'ün eşik/sabitleriyle AYNI (kart guard'ı: eşik sonradan değişmez).
  5. Defter parçaları ast geçer, sürüm damgası v4, exec zinciri talimatla tutarlı.
  6. ⑤ sonda dosyası ast geçer ve 8 emekli sembolün 8'ini taşır; kıyas betiği yerel tabloyu okur.
  7. Üretici ve üretilen dosya `meridian`i İTHAL ETMEZ (obs'a ulaşan koşum yasağı).

KAYNAK ÇAPALARI SEMBOLDÜR, satır değil (CLAUDE.md §2): `PIT_ARALIKLARI`, `pit_uyeler`,
`ANAHTAR`, `CIKTI`, `SONDA_SEMBOLLER`.
"""

from __future__ import annotations

import ast
import hashlib
import random
import re
import subprocess
import sys
from pathlib import Path

import pytest

from tests.conftest import betikten_modul_yukle

KOK = Path(__file__).resolve().parents[1]
QC = KOK / "research" / "qc_dogrulama"
CSV = KOK / "research" / "pit_universe" / "sp500_uyelik_tarihi.csv"

URETICI = QC / "pit_araliklari_uret.py"
TALIMAT = QC / "OPERATOR_TALIMATI.md"
SONDA = QC / "qc_sonda_delist_8.py"
SEMA = QC / "cikti_semasi.md"
KIYAS = QC / "qc_sonda_delist_8_kiyas.py"

# QC'nin dosya başına sınırı — ÖLÇÜLDÜ (v3 turu, OPERATOR_TALIMATI.md v3 şerhi).
QC_KARAKTER_SINIRI = 32_000

# ⑤ RETIRED_SYMBOLS (meridian/adapters/data.py::RETIRED_SYMBOLS) — 8 kalem.
SEKIZ = ("ANSS", "DFS", "FI", "HES", "IPG", "K", "PARA", "WBA")

# v3 ANAHTAR'ın EŞİK/SABİT kümesi — 2026-09-03'te qc_defter_021_a.py'nin v3 hâlinden ast ile
# ÖLÇÜLDÜ ve buraya DONDURULDU. Kart guard'ı: ikinci koşum TANIM-EŞİTLEMEDİR, eşik-esnetme
# değildir; v4 bu sözlüğün tek bir değerini bile değiştiremez.
V3_ANAHTAR_DONMUS = {
    "PENCERE_BAS": "datetime(2020, 8, 1)",
    "PENCERE_SON": "datetime(2026, 7, 28)",
    "EVREN_N": 250,
    "UST_PCT": 0.2,
    "UFUKLAR": (10, 20),
    "BLOK": 21,
    "BOOT": 2000,
    "BOOT_IC": 600,
    "TOHUM": 20260801,
    "MIN_KESIT": 50,
    "MIN_DILIM": 30,
    "MALIYET_BPS": 10.0,
    "MALIYET_BPS_DUYARLILIK": 20.0,
    "RVOL_PENCERE": 20,
    "TURNOVER_PENCERE": 21,
    "PK_CIVI": 0.064,
    "PK_MERTEBE": 5.0,
    "PANEL_CARPANI": 2,
    "SPAN_TOLERANS": 2.0,
    "SHARES_BAYAT_GUN": 200,
    "TURNOVER_TAVAN": 1.0,
    "CAPRAZ_SEMBOL": 6,
    "CAPRAZ_TOL": 0.001,
    "CAPRAZ_MAKS_ORAN": 0.005,
    "CAPRAZ_BUYUK_TOL": 0.02,
    "DELIST_TAMPON_GUN": 10,
    "SONDA_GUN": 10,
    "YIL_LIMIT": None,
    "PARCA": 50,
}
# v4'ün EKLEMESİNE izin verilen TEK anahtar (evren kaynağı seçici — eşik değil).
V4_YENI_ANAHTARLAR = {"EVREN_KAYNAGI"}


# --------------------------------------------------------------------------- yardımcılar

def _modul(yol: Path, ad: str):
    """Betiği KAYNAKTAN yükler (ham `exec_module` YASAK — v334: bayat `__pycache__` kaynağın
    önüne geçebilir). Yüklenen dosyalar meridian'a DOKUNMAZ, o yüzden obs'a da yazmaz."""
    return betikten_modul_yukle(yol, ad)


def _csv_satirlari():
    """CSV'yi (tarih_str, set[ticker]) olarak okur — üreticiden BAĞIMSIZ ikinci okuyucu."""
    import csv as _csv

    with CSV.open(newline="") as fh:
        r = _csv.reader(fh)
        next(r)
        return [(a[0], {t for t in a[1].split(",") if t}) for a in r]


def _anahtar_sozlugu(yol: Path) -> dict:
    """ANAHTAR'ı ast ile okur — dosyayı ÇALIŞTIRMADAN (QC importları yerelde yok)."""
    agac = ast.parse(yol.read_text(encoding="utf-8"))
    for d in ast.walk(agac):
        if isinstance(d, ast.Assign) and getattr(d.targets[0], "id", None) == "ANAHTAR":
            out = {}
            for k, v in zip(d.value.keys, d.value.values):
                try:
                    out[k.value] = ast.literal_eval(v)
                except Exception:
                    out[k.value] = ast.unparse(v)
            return out
    raise AssertionError(f"{yol.name} içinde ANAHTAR bulunamadı")


def _parca_dosyalari() -> list[Path]:
    return sorted(QC.glob("qc_defter_021_[d-z].py"))


def _ithal_adlari(kaynak: str) -> set[str]:
    """Dosyanın ithal ettiği KÖK modül adları (ast — metin taraması değil)."""
    adlar = set()
    for n in ast.walk(ast.parse(kaynak)):
        if isinstance(n, ast.Import):
            adlar |= {a.name.split(".")[0] for a in n.names}
        elif isinstance(n, ast.ImportFrom) and n.module:
            adlar.add(n.module.split(".")[0])
    return adlar


# --------------------------------------------------------------------------- 1. üretici

def test_uretici_var_ve_meridian_ithal_etmez():
    assert URETICI.exists(), "pit_araliklari_uret.py yok"
    adlar = _ithal_adlari(URETICI.read_text(encoding="utf-8"))
    assert "meridian" not in adlar, (
        f"üretici meridian ithal ediyor ({sorted(adlar)}) — pytest DIŞI koşumda canlı yerel "
        "deftere yazar (CLAUDE.md §2)")


def test_uretici_60_ornek_gunde_csv_uyeligini_birebir_uretir():
    """Aralıklar CSV'nin AS-OF okumasını birebir vermeli: bir CSV satırının tarihinde o satırın
    ticker kümesi; iki satır ARASINDAKİ günde bir ÖNCEKİ satırın kümesi (adım fonksiyonu)."""
    d = _modul(QC / "qc_defter_021_d.py", "qc_defter_021_d")
    satirlar = _csv_satirlari()
    rng = random.Random(20260903)
    # ilk + son + 58 rastgele satır (sabit tohum → çivi deterministik)
    idx = [0, len(satirlar) - 1] + rng.sample(range(len(satirlar)), 58)
    for i in idx:
        tarih, beklenen = satirlar[i]
        assert d.pit_uyeler(tarih) == beklenen, f"{tarih} satırında üyelik ayrıştı"
    # satır ARASI günler: bir sonraki satırdan önceki her gün önceki satırın kümesidir
    from datetime import date as _date, timedelta as _td

    ara = 0
    for i in rng.sample(range(len(satirlar) - 1), 40):
        t0 = _date.fromisoformat(satirlar[i][0])
        t1 = _date.fromisoformat(satirlar[i + 1][0])
        if (t1 - t0).days < 2:
            continue
        ara += 1
        orta = t0 + _td(days=(t1 - t0).days // 2)
        assert d.pit_uyeler(orta) == satirlar[i][1], f"{orta} (satır arası) üyelik ayrıştı"
    assert ara >= 10, f"satır-arası örneklem çok küçük ({ara}) — çivi ısırmıyor"


def test_her_csv_satiri_ve_her_sinir_gunu_birebir():
    """60 ÖRNEK ZAYIF DETEKTÖRDÜR: tek bir ticker'ın tek bir günlük sınır kayması örneklemin
    arasından geçebilir (ÖLÇÜLDÜ — mutasyon turu). Tarama TÜKETİCİ: 2.718 satır tarihinin
    tamamı + her satırın BİR GÜN ÖNCESİ (sınır günü). Maliyet ~1 sn."""
    d = _modul(QC / "qc_defter_021_d.py", "qc_defter_021_d_tam")
    satirlar = _csv_satirlari()
    ayrik = [t for t, kume in satirlar if d.pit_uyeler(t) != kume]
    assert not ayrik, f"{len(ayrik)} satır tarihinde üyelik ayrıştı: {ayrik[:5]}"
    from datetime import date as _date, timedelta as _td

    sinir, n = [], 0
    for i in range(1, len(satirlar)):
        onceki_gun = (_date.fromisoformat(satirlar[i][0]) - _td(days=1)).isoformat()
        if onceki_gun <= satirlar[i - 1][0]:
            continue                      # ardışık takvim günü — sınır günü yok
        n += 1
        if d.pit_uyeler(onceki_gun) != satirlar[i - 1][1]:
            sinir.append(onceki_gun)
    assert n > 1000, f"sınır günü örneklemi beklenenden küçük: {n}"
    assert not sinir, f"{len(sinir)} sınır gününde üyelik ayrıştı: {sinir[:5]}"


def test_veri_araligi_disinda_uyelik_bostur_ve_beyanli():
    """CSV 2026-06-30'da bitiyor, defter penceresi 2026-07-28'e gidiyor. Taşıma UYDURMADIR —
    veri sonrası gün BOŞ küme döner ve dosya bunu BEYAN eder."""
    d = _modul(QC / "qc_defter_021_d.py", "qc_defter_021_d_b")
    assert d.pit_uyeler("2026-07-15") == set()
    assert d.pit_uyeler("1990-01-01") == set()
    assert d.pit_veri_icinde("2026-07-15") is False
    assert d.pit_veri_icinde(d.PIT_VERI_SON) is True
    assert d.PIT_VERI_SON == _csv_satirlari()[-1][0]


# --------------------------------------------------------- 2. üretilen dosyalar: sınır + ast

def test_uretilen_parcalar_32k_altinda_ve_ast_gecer():
    parcalar = _parca_dosyalari()
    assert parcalar, "üretilmiş qc_defter_021_d.py yok"
    for p in parcalar:
        kaynak = p.read_text(encoding="utf-8")
        assert len(kaynak) < QC_KARAKTER_SINIRI, (
            f"{p.name} {len(kaynak)} karakter — QC'nin ÖLÇÜLMÜŞ {QC_KARAKTER_SINIRI} sınırını "
            "aşıyor; üretici alfabetik bölmeliydi")
        ast.parse(kaynak)  # sözdizimi


def test_pit_uyeler_saf_python():
    """numpy/pandas yok: defter QC'de _b'den ÖNCE koşar ve QC'nin import yükünü taşımamalı."""
    parcalar = _parca_dosyalari()
    assert parcalar, "üretilmiş parça yok — çivi boşa öter"
    for p in parcalar:
        adlar = _ithal_adlari(p.read_text(encoding="utf-8"))
        assert not (adlar & {"numpy", "pandas", "meridian"}), (
            f"{p.name} saf-Python değil: {sorted(adlar)}")


def test_butunluk_bekcisi_eksik_parcayi_yakalar():
    """Operatör parçalardan birini yüklemeyi unutursa evren SESSİZCE yarım kalmamalı."""
    d = _modul(QC / "qc_defter_021_d.py", "qc_defter_021_d_c")
    rapor = d.pit_butunluk()
    assert rapor["tam"] is True, rapor
    assert rapor["yuklu_ticker"] == d.PIT_BEKLENEN_TICKER == len(d.PIT_ARALIKLARI)
    # mutasyon: bir ticker düşerse bütünlük bekçisi ÖTMELİ
    kayip = next(iter(d.PIT_ARALIKLARI))
    d.PIT_ARALIKLARI.pop(kayip)
    assert d.pit_butunluk()["tam"] is False


def test_cok_parcali_bolunme_yolu_gercekten_kosuyor():
    """K-1 REGRESYONU: bütünlük bekçisi ARALIK LİTERALİNİN değil PARÇA ZİNCİRİNİN sonuna aittir.
    Eski kurulumda bekçi d.py'nin sonundaydı ve koşulu totolojiydi → iki+ parçada d.py TEK BAŞINA
    yüklenirken RuntimeError atıyor, e.py'nin `update()`ine sıra GELMİYORDU. Yani brief'in vaat
    ettiği 'gerekirse alfabetik böl' yolu ÖLÜ KODdu. Bu çivi yolu KOŞTURUR."""
    u = _modul(URETICI, "pit_araliklari_uret_bolunme")
    _s, araliklar, dosyalar, sha = u._uret(12_000)     # küçük tavan → zorunlu bölünme
    assert len(dosyalar) >= 3, f"tavan 12.000 bölünme üretmedi: {sorted(dosyalar)}"
    alan: dict = {}
    for ad in sorted(dosyalar):                       # d → e → f → … (alfabetik = yükleme sırası)
        assert len(dosyalar[ad]) < 12_000, f"{ad} tavanı aştı"
        exec(compile(dosyalar[ad], ad, "exec"), alan)
    assert alan["pit_butunluk"]()["tam"] is True
    assert len(alan["PIT_ARALIKLARI"]) == len(araliklar)
    # zincirin ORTASINDA durmak bağırmalı: son parça olmadan bekçi ötmeli
    yarim: dict = {}
    for ad in sorted(dosyalar)[:-1]:
        exec(compile(dosyalar[ad], ad, "exec"), yarim)
    assert yarim["pit_butunluk"]()["tam"] is False
    with pytest.raises(RuntimeError):        # zincirin sonundaki bekçi YARIM tabloda ötmeli
        exec(compile(u.BEKCI, "bekci", "exec"), yarim)
    assert u.BEKCI in dosyalar[sorted(dosyalar)[-1]], "bekçi SON parçada değil"
    assert u.BEKCI not in dosyalar[sorted(dosyalar)[0]], (
        "bekçi hâlâ ilk parçada — iki+ parçada d.py tek başına yüklenirken patlar (K-1)")


# ------------------------------------------------------- 3. determinizm + kaynak kimliği

def test_kontrol_bayragi_bayt_ayni():
    """`--kontrol` yeniden üretip diskle kıyaslar; çıkış kodu 0 ise bayt-aynı."""
    r = subprocess.run([sys.executable, str(URETICI), "--kontrol"],
                       cwd=str(KOK), capture_output=True, text=True, timeout=300)
    assert r.returncode == 0, f"--kontrol bayt-aynı DEĞİL:\n{r.stdout}\n{r.stderr}"
    assert "BAYT-AYNI" in r.stdout, r.stdout


def test_pit_kaynak_sha256_csv_ile_esit():
    d = _modul(QC / "qc_defter_021_d.py", "qc_defter_021_d_d")
    beklenen = hashlib.sha256(CSV.read_bytes()).hexdigest()
    assert d.PIT_KAYNAK_SHA256 == beklenen, (
        "üretilen dosya BAŞKA bir CSV'den doğmuş — kart artefaktı sessizce ölür")
    assert d.PIT_URETIM_DAMGASI["kaynak_sha256"] == beklenen
    # damga SAAT taşımaz: taşısaydı `--kontrol` her koşumda kırmızı olurdu (determinizm).
    damga = repr(d.PIT_URETIM_DAMGASI)
    assert not re.search(r"\d{4}-\d\d-\d\dT\d\d:", damga), (
        "üretim damgasında duvar saati var — bayt-aynılık ölçülemez olur")


# ------------------------------------------------------------------- 4. kart guard'ı: ANAHTAR

def test_v4_anahtar_v3_esik_ve_sabitleriyle_ayni():
    a = _anahtar_sozlugu(QC / "qc_defter_021_a.py")
    for k, v in V3_ANAHTAR_DONMUS.items():
        assert k in a, f"v4 ANAHTAR'ında {k} KAYBOLDU"
        assert a[k] == v, f"EŞİK/SABİT DEĞİŞTİ: {k} v3={v!r} v4={a[k]!r} — kart guard'ı ihlali"
    fazla = set(a) - set(V3_ANAHTAR_DONMUS)
    assert fazla == V4_YENI_ANAHTARLAR, (
        f"v4 ANAHTAR'ına izinsiz anahtar eklendi/eksildi: {sorted(fazla)}")
    assert a["EVREN_KAYNAGI"] == "pit_sp500"


# ------------------------------------- 4b. v4'ün ASIL sözleşmesi: _b'nin PIT katmanları (Ö-3)
# Dördü de "sessizce v3'e dönme" yollarıdır. Biri düşerse JSON yine `"kaynak": "pit_sp500"`
# der ve hiçbir şey ötmez — tam olarak sessiz gerileme sınıfı. Dosya QC importları olmadan
# KOŞMAZ, o yüzden ast/regex ile ölçülür.

def _b_kaynak() -> str:
    return (QC / "qc_defter_021_b.py").read_text(encoding="utf-8")


def test_b_d_yoksa_RuntimeError_atar():
    """(a) `_d` yüklenmemişse _b DURMALI — sessizce dolar-hacim evrenine dönmemeli."""
    kaynak = _b_kaynak()
    kosullar = [n for n in ast.walk(ast.parse(kaynak))
                if isinstance(n, ast.If) and "pit_uyeler" in ast.unparse(n.test)
                and "not in" in ast.unparse(n.test)]
    assert kosullar, "'pit_uyeler not in globals()' kapısı yok"
    govde = " ".join(ast.unparse(x) for k in kosullar for x in k.body)
    assert "RuntimeError" in govde, f"kapı DUR vermiyor: {govde[:200]}"
    assert "qc_defter_021_d" in govde, "hata metni eksik parçayı ADIYLA söylemiyor"


def test_b_ikinci_katman_havuz_suzgeci_H2b_de_de_var():
    """(b) universe_history seçiciyi UYGULAMAYABİLİR (ham liste döner). Havuz süzgeci yalnız
    seçicide kalsaydı üst-N kırpması PIT dışı isimlerle dolar ve v4 sessizce v3'e dönerdi."""
    kaynak = _b_kaynak()
    assert kaynak.count("PIT_HAVUZ") >= 3, "PIT_HAVUZ tek yerde — ikinci katman yok"
    assert re.search(r"if\s+tk\s+not\s+in\s+PIT_HAVUZ:\s*\n\s*continue", kaynak), (
        "H2b aday döngüsünde havuz süzgeci bulunamadı")
    # süzgeç H2b'nin ADAY döngüsünde olmalı (seçicinin içinde değil)
    _, _, sonrasi = kaynak.partition("uyeler_bugun = pit_uyeler(ts)")
    assert sonrasi, "H2b'de gün gün as-of üyelik araması yok"
    assert "if tk not in PIT_HAVUZ:" in sonrasi.split("aday.sort(")[0]


def test_b_evren_uye_pit_uyeligiyle_AND_lenir():
    """(c) `evren_uye` gün gün as-of üyelikle AND'lenmeli; tarihsiz HAVUZ yeterli DEĞİL."""
    kaynak = _b_kaynak()
    atama = re.search(r'B\["evren_uye"\] = \(_uy & \(B\["pit_rutbe"\][^\n]*', kaynak)
    assert atama, "PIT modunda evren_uye ataması beklenen biçimde değil"
    assert "EVREN_N" in atama.group(0), "EVREN_N tavanı kalkmış"
    # `_uy` gün gün üyelikten gelmeli — havuzdan değil
    assert re.search(r'_uy = B\["pit_uye"\]\.to_numpy\(\)', kaynak)
    assert 'B["pit_uye"]' in kaynak and "PIT_HAVUZ" not in atama.group(0)


def test_b_rutbe_uye_ICI_alinir():
    """(d) Rütbe ÜYELER ARASINDA alınır. Panel geneli üzerinden alınsaydı üst-250'nin bir kısmı
    PIT dışı isimlerle dolar ve kesit SESSİZCE daralırdı."""
    kaynak = _b_kaynak()
    assert re.search(r'B\[_uy\]\.groupby\("tarih"\)\["dolar_hacim"\]\s*\n?\s*\.rank\(',
                     kaynak), "üye-içi rütbe deseni (B[_uy].groupby…rank) yok"
    assert 'B["pit_rutbe"]' in kaynak


# --------------------------------------------------- 5. defter parçaları + exec zinciri

def test_defter_parcalari_ast_gecer():
    for ad in ("a", "b", "c", "d"):
        p = QC / f"qc_defter_021_{ad}.py"
        assert p.exists(), f"{p.name} yok"
        ast.parse(p.read_text(encoding="utf-8"))


def test_defter_surumu_v4():
    kaynak = (QC / "qc_defter_021_c.py").read_text(encoding="utf-8")
    for d in ast.walk(ast.parse(kaynak)):
        if isinstance(d, ast.Assign) and getattr(d.targets[0], "id", None) == "CIKTI":
            alanlar = {k.value: v for k, v in zip(d.value.keys, d.value.values)}
            assert ast.literal_eval(alanlar["defter_surumu"]) == "v4"
            assert "kapsama" in ast.unparse(alanlar["evren"]), (
                "evren bloğunda kapsama ölçümü yok — v4'ün tek yeni raporu odur")
            return
    raise AssertionError("qc_defter_021_c.py içinde CIKTI bulunamadı")


def _v4_bolumu() -> str:
    """Talimatın YALNIZ v4 bölümü — v2/v3 kayıtlarındaki bayat hücreler karışmasın."""
    metin = TALIMAT.read_text(encoding="utf-8")
    bas = metin.index("## v4 (2026-09-03) — PIT evren")
    kalan = metin[bas:]
    kes = kalan.find("\n## §0")
    return kalan if kes < 0 else kalan[:kes]


def test_exec_zinciri_talimatla_tutarli():
    """Talimatın v4 bölümündeki tek hücre sırası ile dosya gerçeği ve bağımlılık yönü UYUŞMALI."""
    siralar = re.findall(r"for _p in \(([^)]*)\):", _v4_bolumu())
    assert siralar, "talimatın v4 bölümünde exec zinciri yok"
    son = [s.strip().strip("\"'") for s in siralar[-1].split(",") if s.strip()]
    assert son == ["a", "d", "b", "c"], f"talimattaki v4 sırası beklenmedik: {son}"
    # dosya gerçeği: sıradaki her parça diskte var
    for p in son:
        assert (QC / f"qc_defter_021_{p}.py").exists(), f"talimat {p} diyor, dosya yok"
    # bağımlılık yönü: _b PIT yardımcısını KULLANIR → _d ondan ÖNCE gelmeli
    b = (QC / "qc_defter_021_b.py").read_text(encoding="utf-8")
    assert "pit_uyeler" in b, "_b PIT süzgecini kullanmıyor — v4 evreni bağlanmamış"
    assert son.index("d") < son.index("b")
    assert son.index("a") < son.index("b") < son.index("c")


def test_talimat_v4_bolumu_ve_hedef_dosya():
    metin = TALIMAT.read_text(encoding="utf-8")
    assert "## v4 (2026-09-03) — PIT evren" in metin
    assert "research/olcumler/qc_dogrulama/sonuc_021_v4.json" in metin
    assert "<<<SONUC_021_JSON_BASLANGIC>>>" in metin
    # v2/v3 adımları BAYAT işaretli olmalı: aynı dosyada iki zıt hücre duruyor, operatör
    # hangisinin geçerli olduğunu ARAMAK zorunda kalmamalı (tek-kaynak yasası).
    assert "BAYAT" in metin
    v4 = _v4_bolumu()
    assert "lean cloud push" in v4, "yükleme sözleşmesi (Rol-1 push eder) yazılmamış"
    assert "sonda_delist_8.json" in metin


def test_dort_parca_da_qc_sinirinin_altinda():
    """Sınırın KARAKTER mi BAYT mı sayıldığı ÖLÇÜLMEDİ → ikisini de tut (dar olan kazanır)."""
    for ad in ("a", "b", "c", "d"):
        kaynak = (QC / f"qc_defter_021_{ad}.py").read_text(encoding="utf-8")
        assert len(kaynak) < QC_KARAKTER_SINIRI, f"_{ad}: {len(kaynak)} karakter"
        assert len(kaynak.encode("utf-8")) < QC_KARAKTER_SINIRI, (
            f"_{ad}: {len(kaynak.encode('utf-8'))} bayt")


def test_sema_belgesi_v4_ile_ayrismiyor():
    """Ö-1: JSON şeması iki yerde anlatılıyor (kod + cikti_semasi.md). Tek-kaynak yasası:
    belge v3'te donarsa hükmü yazan Rol-1 YANLIŞ ŞEMAYI okur."""
    sema = SEMA.read_text(encoding="utf-8")
    assert "## v4 (2026-09-03)" in sema, "şema belgesinde v4 bandı yok"
    assert '"v4"' in sema, "şema belgesi defter_surumu 'v4' demiyor"
    assert 'for _p in ("a", "d", "b", "c")' in sema, "şema belgesinde v4 exec zinciri yok"
    for alan in ("evren.kapsama", "evren.kaynak", "tanimlar.evren", "sonuc_021_v4.json"):
        assert alan in sema, f"şema belgesinde {alan} yok"


def test_qc_dosya_siniri_TEK_sayi():
    """Ö-4: repo aynı gerçek için iki sayı taşıyordu (32.000 / 64.000). 64.000'li satırlar
    BAYAT işaretsiz duramaz — yoksa gelecekteki bölme kararı yanlış tabana oturur."""
    for yol in (TALIMAT, SEMA):
        for no, hat in enumerate(yol.read_text(encoding="utf-8").splitlines(), 1):
            if "64.000" in hat:
                assert "BAYAT" in hat, (
                    f"{yol.name}:{no} işaretsiz 64.000 sınırı taşıyor: {hat.strip()[:90]}")
    v4 = _v4_bolumu()
    assert "32.000" in v4, "sınırın TEK kaynağı v4 bandında yazılı değil"
    # tek kaynak: üretici ve çivi aynı sayıda
    u = URETICI.read_text(encoding="utf-8")
    assert "QC_TAVAN = 32_000" in u
    assert QC_KARAKTER_SINIRI == 32_000


# ----------------------------------------------------------------- 6. ⑤ delist sondası

def test_sonda_ast_gecer_ve_sekiz_sembolu_tasir():
    assert SONDA.exists(), "qc_sonda_delist_8.py yok"
    kaynak = SONDA.read_text(encoding="utf-8")
    ast.parse(kaynak)
    assert len(kaynak) < QC_KARAKTER_SINIRI, f"{SONDA.name} {len(kaynak)} karakter"
    semboller = None
    for d in ast.walk(ast.parse(kaynak)):
        if isinstance(d, ast.Assign) and getattr(d.targets[0], "id", None) == "SONDA_SEMBOLLER":
            semboller = tuple(ast.literal_eval(d.value))
    assert semboller is not None, "SONDA_SEMBOLLER yok"
    assert set(semboller) == set(SEKIZ), f"8 sembolün 8'i yok: {semboller}"
    assert "<<<SONDA_DELIST_JSON_BASLANGIC>>>" in kaynak
    assert "<<<SONDA_DELIST_JSON_SON>>>" in kaynak
    assert not (_ithal_adlari(kaynak) & {"meridian"})


def test_sonda_adlari_defter_globalsiyla_CAKISMIYOR():
    """Ku-1: sonda `exec(..., globals())` ile AYNI namespace'e koşuyor. Defterin bir adını
    ezerse 'paylaşılan durum' vakasının aynı sınıfı tekrarlar (bkz. QuantBook paylaşılmaz)."""
    def _ust_duzey(kaynak):
        adlar = set()
        for n in ast.parse(kaynak).body:
            if isinstance(n, (ast.FunctionDef, ast.ClassDef)):
                adlar.add(n.name)
            elif isinstance(n, ast.Assign):
                adlar |= {t.id for t in n.targets if isinstance(t, ast.Name)}
            elif isinstance(n, ast.For) and isinstance(n.target, ast.Name):
                adlar.add(n.target.id)
        return adlar

    sonda_adlari = _ust_duzey(SONDA.read_text(encoding="utf-8"))
    defter = set()
    for ad in ("a", "b", "c", "d"):
        defter |= _ust_duzey((QC / f"qc_defter_021_{ad}.py").read_text(encoding="utf-8"))
    # `for _x in …` gövdesindeki atamalar ast.For'un içinde kalır; en riskli ikisi ADIYLA:
    assert "_tic" not in sonda_adlari and "_sid" not in sonda_adlari
    cakisan = sonda_adlari & defter
    assert not cakisan, f"sonda defterin adlarını EZİYOR: {sorted(cakisan)}"


def test_sonda_WARNING_tarihini_delist_alanina_YAZMAZ():
    """Ö-5: DelistingType.WARNING delist gününden BİR GÜN ÖNCE gelir. Aynı alana yazılsaydı
    kıyas sistematik 'AYRIK -1 gün' üretir ve wp-qc-5'in çakışma-istisnasını SAHTE tetiklerdi."""
    kaynak = SONDA.read_text(encoding="utf-8")
    assert "_sec_olay" not in kaynak, "eski `_delisted or olaylar` düşüşü hâlâ duruyor"
    assert "qc_uyari_tarihi" in kaynak, "WARNING için ayrı alan yok"
    atama = re.search(r'kayit\["qc_delist_tarihi"\] = sorted\(([^)]*)\)', kaynak)
    assert atama and "_delisted" in atama.group(1) and "olaylar" not in atama.group(1), (
        f"qc_delist_tarihi yalnız DELISTED olayından dolmuyor: {atama and atama.group(1)}")


def test_kiyas_uyari_tipini_ayri_etiketler_ve_gosterir():
    """Ö-5'in okuma tarafı: operatör 'AYRIK' ile 'yalnız uyarı geldi'yi ayırt edebilmeli."""
    k = _modul(KIYAS, "qc_sonda_delist_8_kiyas_uyari")
    qc = {"semboller": [{"ticker": "ANSS", "qc_delist_tarihi": None,
                         "qc_uyari_tarihi": "2025-07-17", "neden": "tipi DELISTED DEĞİL"}]}
    a = {x["ticker"]: x for x in k.kiyasla(qc)["satirlar"]}
    assert a["ANSS"]["mutabakat"] == "QC_UYARI_TIPI"
    assert a["ANSS"]["fark_gun"] is None, "uyarı tarihi kıyasa GİRMEMELİ"
    assert a["ANSS"]["uyari_fark_gun"] == -1, "uyarı TANI alanı hesaplanmıyor"
    kaynak = KIYAS.read_text(encoding="utf-8")
    assert '"qc_neden"' in kaynak.split("_yaz_tablo(r[")[-1] or 'qc_neden' in \
        kaynak.split("_yaz_tablo(r[")[-1], "insan-okur çıktı qc_neden'i göstermiyor"
    assert '"qc_uyari_tarihi"' in kaynak.split("_yaz_tablo(r[")[-1]


def test_kiyas_betigi_yerel_tabloyu_okuyabiliyor():
    """Kıyas betiği yerel tarihleri KODDAN ve BELGEDEN okur; elle kopyalanmış tarih taşımaz."""
    assert KIYAS.exists(), "qc_sonda_delist_8_kiyas.py yok"
    k = _modul(KIYAS, "qc_sonda_delist_8_kiyas")
    assert "meridian" not in _ithal_adlari(KIYAS.read_text(encoding="utf-8"))
    tablo = k.yerel_tablo()
    assert set(tablo) == set(SEKIZ), f"yerel tablo 8 sembolü vermedi: {sorted(tablo)}"
    for t, satir in tablo.items():
        assert re.fullmatch(r"\d{4}-\d\d-\d\d", satir["retired_delist"]), (t, satir)
        assert re.fullmatch(r"\d{4}-\d\d-\d\d", satir["uyelik_son_gorulme"]), (t, satir)
        assert satir["massive_delisted_utc"] is None or re.fullmatch(
            r"\d{4}-\d\d-\d\d", satir["massive_delisted_utc"]), (t, satir)
    # ÖLÇÜLMÜŞ boşluk: PARA'nın üçüncü otoritesi YOK (wp-qc-5) — uydurulmadı
    assert tablo["PARA"]["massive_delisted_utc"] is None
    assert tablo["ANSS"]["retired_delist"] == "2025-07-18"


def test_kiyas_gun_gune_kiyaslar():
    k = _modul(KIYAS, "qc_sonda_delist_8_kiyas_b")
    qc = {"semboller": [{"ticker": "ANSS", "qc_delist_tarihi": "2025-07-18", "neden": None},
                        {"ticker": "DFS", "qc_delist_tarihi": None, "neden": "yol yok"}]}
    r = k.kiyasla(qc)
    a = {x["ticker"]: x for x in r["satirlar"]}
    assert a["ANSS"]["mutabakat"] == "AYNI" and a["ANSS"]["fark_gun"] == 0
    assert a["DFS"]["mutabakat"] == "QC_OLCULEMEDI" and a["DFS"]["fark_gun"] is None
    assert a["WBA"]["mutabakat"] == "QC_SONDASINDA_YOK"
    qc2 = {"semboller": [{"ticker": "ANSS", "qc_delist_tarihi": "2025-07-21", "neden": None}]}
    a2 = {x["ticker"]: x for x in k.kiyasla(qc2)["satirlar"]}
    assert a2["ANSS"]["mutabakat"] == "AYRIK" and a2["ANSS"]["fark_gun"] == 3


@pytest.mark.parametrize("bayrak", ["--yerel-tablo"])
def test_kiyas_komut_satiri_sozlesmesi(bayrak):
    """ops sözleşmesi KOMUT SATIRIdır (CLAUDE.md §1) — main() değil."""
    r = subprocess.run([sys.executable, str(KIYAS), bayrak],
                       cwd=str(KOK), capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, r.stderr
    for t in SEKIZ:
        assert t in r.stdout
