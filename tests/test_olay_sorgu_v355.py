"""v355 — `ops/olay_sorgu.py` çivileri (TSK-020 [UYGULA-2] adım 1).

NUMARA SEÇİMİ: `ls tests/ | grep -oE "v[0-9]{2,}" | sort -n` ile ölçüldü — en büyük alınmış
numara v354 idi (2026-09-01). v355 boştu; çakışma yok.

NEYİ ÇİVİLER (her biri ayrı bir sınıf):
  1. SÖZLEŞME KOMUT SATIRIDIR — her çivi aracı `subprocess` ile ÇAĞIRIR, `main()` import
     ETMEZ (vaka 2026-08-30: 18 çivi yeşilken `--uygula` sessizce yok sayılıyordu; çünkü
     çiviler fonksiyonu çağırıyordu, komutu değil).
  2. YASA 4 (sessiz yutma yok) — bozuk JSON satırı SAYILIR ve stderr'e RAPORLANIR.
  3. YASA 6 (okuyucusuz yazım yok) — araç TEK çıktı üretir: stdout. Hiçbir ara dosya,
     DB, parquet ya da kopya yazmaz.
  4. OBS SIZINTISI KAPALI — araç `meridian` paketini import ETMEZ. İki katmanlı ölçüm:
     (a) kaynak metninde `import meridian` yok, (b) GERÇEK koşumda `-X importtime` ile
     yüklenen modüller arasında `meridian` yok. Sebebi: pytest DIŞI koşan bir betik
     `meridian.obs`'a ulaşırsa canlı yerel deftere YAZAR (3 vaka, 2026-08-30).
  5. SERBEST SQL YALNIZ SELECT — başka ifade sınıfı gerekçeyle REDDEDİLİR; çok-ifadeli
     kaçış (`SELECT 1; DROP ...`) da reddedilir.

GERÇEK DEFTERE DOKUNULMAZ: her çivi `tmp_path` altına kendi sentetik jsonl'ini yazar.
`state/events.jsonl` bu dosyada hiç açılmaz.
"""

from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys

import pytest

from tests.conftest import betikten_modul_yukle

KOK = pathlib.Path(__file__).resolve().parents[1]
ARAC = KOK / "ops" / "olay_sorgu.py"

# Sentetik defter: iki gün, üç olay tipi, üç seviye. Sayılar ELLE doğrulanabilir olsun diye küçük.
SATIRLAR = [
    {"ts": "2026-01-01T09:00:00+00:00", "level": "info", "event": "daily_cycle", "candidates": 3},
    {"ts": "2026-01-01T10:00:00+00:00", "level": "warn", "event": "hotstate_down", "url": "http://x"},
    {"ts": "2026-01-01T11:00:00+00:00", "level": "warn", "event": "hotstate_down", "url": "http://y"},
    {"ts": "2026-01-02T09:00:00+00:00", "level": "alarm", "event": "breaker_trip", "detail": "kapak attı"},
    {"ts": "2026-01-02T10:00:00+00:00", "level": "warn", "event": "hotstate_down", "url": "http://z"},
]


def _defter_yaz(dizin: pathlib.Path, satirlar=SATIRLAR, bozuk: int = 0) -> pathlib.Path:
    """Sentetik jsonl yazar; `bozuk` kadar ayrıştırılamaz satırı ARAYA serpiştirir."""
    p = dizin / "olaylar.jsonl"
    govde = [json.dumps(s) for s in satirlar]
    for i in range(bozuk):
        govde.insert(min(1 + i * 2, len(govde)), "BU SATIR JSON DEGIL {{{ %d" % i)
    p.write_text("\n".join(govde) + "\n", encoding="utf-8")
    return p


def kos(*argv: str, cwd: pathlib.Path | None = None,
        ortam: dict[str, str] | None = None) -> subprocess.CompletedProcess:
    """Aracı OPERATÖRÜN koşacağı biçimde çağırır: komut satırı, `main()` değil.

    `ortam`: operatörün kabuğunda vereceği ek ortam değişkenleri (ör. `OLAY_SORGU_BELLEK`).
    MEVCUT ortamın ÜSTÜNE biner, yerine geçmez — `PATH`siz bir koşum aracı bulamazdı ve
    "ölçüm kırmızı" ile "araç koşamadı" karışırdı."""
    env = None
    if ortam:
        env = dict(os.environ)
        env.update(ortam)
    return subprocess.run(
        [sys.executable, str(ARAC), *argv],
        capture_output=True,
        text=True,
        cwd=str(cwd or KOK),
        env=env,
    )


# ---------------------------------------------------------------------------------------------
# 1. Hazır sorgular
# ---------------------------------------------------------------------------------------------

def test_ozet_olay_tipi_x_gun_sayimi(tmp_path):
    """`ozet` olay tipi × gün sayım tablosu verir; sayılar sentetik defterle ELLE doğrulanır."""
    p = _defter_yaz(tmp_path)
    r = kos("--dosya", str(p), "--sorgu", "ozet", "--json")
    assert r.returncode == 0, r.stderr
    satirlar = [json.loads(s) for s in r.stdout.splitlines() if s.strip()]
    gorulen = {(s["gun"], s["olay"]): s["adet"] for s in satirlar}
    assert gorulen == {
        ("2026-01-01", "daily_cycle"): 1,
        ("2026-01-01", "hotstate_down"): 2,
        ("2026-01-02", "breaker_trip"): 1,
        ("2026-01-02", "hotstate_down"): 1,
    }


def test_ozet_metin_ciktisi_hizali_tablodur(tmp_path):
    """Varsayılan çıktı stdout'a HİZALI tablodur: başlık satırı + ayraç + veri."""
    p = _defter_yaz(tmp_path)
    r = kos("--dosya", str(p), "--sorgu", "ozet")
    assert r.returncode == 0, r.stderr
    satirlar = r.stdout.splitlines()
    assert "gun" in satirlar[0] and "olay" in satirlar[0] and "adet" in satirlar[0]
    assert set(satirlar[1].strip()) <= {"-", " "} and "-" in satirlar[1], satirlar[1]
    # Hizalama: başlıktaki 'olay' sütununun başladığı kolon veri satırlarında da olay ile dolu.
    sutun = satirlar[0].index("olay")
    assert satirlar[2][sutun:].startswith(("daily_cycle", "hotstate_down", "breaker_trip"))


def test_son_n_olay_en_yeniden_eskiye(tmp_path):
    """`son --n` son N olayı verir; sıra ts'e göre YENİDEN ESKİYE."""
    p = _defter_yaz(tmp_path)
    r = kos("--dosya", str(p), "--sorgu", "son", "--n", "3", "--json")
    assert r.returncode == 0, r.stderr
    satirlar = [json.loads(s) for s in r.stdout.splitlines() if s.strip()]
    assert len(satirlar) == 3
    assert [s["ts"] for s in satirlar] == [
        "2026-01-02T10:00:00+00:00",
        "2026-01-02T09:00:00+00:00",
        "2026-01-01T11:00:00+00:00",
    ]


def test_tip_filtresi_yalniz_o_tipi_dokur(tmp_path):
    """`tip --tip <ad>` YALNIZ o olay tipini döker; başka tip sızmaz."""
    p = _defter_yaz(tmp_path)
    r = kos("--dosya", str(p), "--sorgu", "tip", "--tip", "hotstate_down", "--json")
    assert r.returncode == 0, r.stderr
    satirlar = [json.loads(s) for s in r.stdout.splitlines() if s.strip()]
    assert len(satirlar) == 3
    assert {s["olay"] for s in satirlar} == {"hotstate_down"}


def test_tip_sorgusu_tip_bayragi_olmadan_reddedilir(tmp_path):
    """`--sorgu tip` `--tip` olmadan SESSİZCE her şeyi dökmez — gerekçeyle reddeder."""
    p = _defter_yaz(tmp_path)
    r = kos("--dosya", str(p), "--sorgu", "tip")
    assert r.returncode != 0
    assert "--tip" in r.stderr


# ---------------------------------------------------------------------------------------------
# 2. Serbest SQL — yalnız SELECT
# ---------------------------------------------------------------------------------------------

def test_serbest_select_calisir(tmp_path):
    """`--sql` ile serbest SELECT `olaylar` görünümü üzerinden koşar."""
    p = _defter_yaz(tmp_path)
    r = kos("--dosya", str(p), "--sql",
            "SELECT level, count(*) AS adet FROM olaylar GROUP BY 1 ORDER BY 1", "--json")
    assert r.returncode == 0, r.stderr
    satirlar = [json.loads(s) for s in r.stdout.splitlines() if s.strip()]
    assert {s["level"]: s["adet"] for s in satirlar} == {"alarm": 1, "info": 1, "warn": 3}


@pytest.mark.parametrize("kotu", [
    "DROP TABLE olaylar",
    "CREATE TABLE z (a INT)",
    "INSERT INTO olaylar VALUES (1)",
    "COPY (SELECT 1) TO 'kacak.csv'",
    "ATTACH 'kacak.db'",
    "SELECT 1; DROP TABLE olaylar",        # çok-ifadeli kaçış
    # İKİ PRAGMA, İKİ AYRI KAPI (ölçüldü, duckdb 1.5.5 — M2 mutasyonu bu ayrımı açığa çıkardı):
    "PRAGMA enable_profiling",             # StatementType.PRAGMA -> TİP kapısı yakalar
    "PRAGMA version",                      # StatementType.SELECT -> yalnız İLK-JETON kapısı yakalar
    "PRAGMA database_list",                # aynı sınıf; introspeksiyon yüzeyi sızmasın
])
def test_select_disi_ifade_gerekceyle_reddedilir(tmp_path, kotu):
    """SELECT dışı her ifade sınıfı REDDEDİLİR ve red GEREKÇELİDİR (sessiz düşme yok)."""
    p = _defter_yaz(tmp_path)
    r = kos("--dosya", str(p), "--sql", kotu)
    assert r.returncode != 0, f"reddedilmedi: {kotu!r} / stdout={r.stdout!r}"
    assert "SELECT" in r.stderr, r.stderr
    assert not r.stdout.strip(), "reddedilen sorgu yine de çıktı bastı"


def test_reddedilen_copy_dosya_yazmaz(tmp_path):
    """COPY reddi SÖZDE değil: reddedilen sorgu diske hiçbir şey bırakmaz."""
    p = _defter_yaz(tmp_path)
    once = {f.name for f in tmp_path.iterdir()}
    r = kos("--dosya", str(p), "--sql", f"COPY (SELECT 1) TO '{tmp_path}/kacak.csv'")
    assert r.returncode != 0
    # Reddin BİZİM kapıdan geldiğini de ölç: yoksa çivi araç HİÇ YOKKEN de yeşil olur
    # (kırmızı turda tam bunu yaptı — vakumlu yeşil).
    assert "SELECT" in r.stderr, r.stderr
    assert {f.name for f in tmp_path.iterdir()} == once


# ---------------------------------------------------------------------------------------------
# 3. YASA 4 — bozuk satır sessizce yutulmaz
# ---------------------------------------------------------------------------------------------

def test_bozuk_satir_sayisi_stderr_e_raporlanir(tmp_path):
    """Ayrıştırılamayan satırlar ATLANIR ama SAYILARAK stderr'e raporlanır (Yasa 4)."""
    p = _defter_yaz(tmp_path, bozuk=2)
    r = kos("--dosya", str(p), "--sorgu", "ozet", "--json")
    assert r.returncode == 0, r.stderr
    # SAYI + BİRİM BİRLİKTE: yalnız "2" aransaydı tmp_path yolundaki herhangi bir "2" de
    # çiviyi yeşil yapardı (sayı hiç raporlanmasa bile). Ölçülen şey mesajın KENDİSİ.
    assert "2 satır" in r.stderr, r.stderr
    # Sağlam satırların sayımı bozuk satırlardan ETKİLENMEZ.
    satirlar = [json.loads(s) for s in r.stdout.splitlines() if s.strip()]
    assert sum(s["adet"] for s in satirlar) == len(SATIRLAR)


def test_bozuk_satir_yokken_uyari_basilmaz(tmp_path):
    """Temiz defterde uyarı YOKTUR — gürültü üretmez (yoksa uyarı bilgi taşımaz)."""
    p = _defter_yaz(tmp_path)
    r = kos("--dosya", str(p), "--sorgu", "ozet")
    assert r.returncode == 0, r.stderr
    assert "ayrıştırılamadı" not in r.stderr


def test_olmayan_dosya_gerekceyle_duser(tmp_path):
    """Olmayan defter SESSİZCE boş tablo vermez — yolu adıyla anan hata ile düşer."""
    yok = tmp_path / "yok.jsonl"
    r = kos("--dosya", str(yok), "--sorgu", "ozet")
    assert r.returncode != 0
    assert str(yok) in r.stderr


# ---------------------------------------------------------------------------------------------
# 4. YASA 6 — tek çıktı stdout; ara artefakt yok
# ---------------------------------------------------------------------------------------------

def test_arac_hicbir_ara_dosya_uretmez(tmp_path):
    """DuckDB defteri DOĞRUDAN okur: ne DB, ne parquet, ne kopya (Yasa 6)."""
    p = _defter_yaz(tmp_path)
    once = {f.name for f in tmp_path.iterdir()}
    for argv in (("--sorgu", "ozet"), ("--sorgu", "son", "--n", "2"),
                 ("--sql", "SELECT count(*) AS n FROM olaylar")):
        r = kos("--dosya", str(p), *argv)
        assert r.returncode == 0, r.stderr
    assert {f.name for f in tmp_path.iterdir()} == once


def test_kaynakta_meridian_importu_yok():
    """Kaynak metni `meridian`ı import ETMEZ — obs sızıntısı yolu kapalı (statik ölçüm)."""
    kaynak = ARAC.read_text(encoding="utf-8")
    kod = [s for s in kaynak.splitlines() if not s.lstrip().startswith("#")]
    suclu = [s for s in kod if "import meridian" in s or "from meridian" in s]
    assert not suclu, suclu
    assert "sys.path.insert" not in "\n".join(kod), "depo kökü sys.path'e eklenmiş — import yolu açılıyor"


def test_gercek_kosumda_meridian_modulu_yuklenmez(tmp_path):
    """DAVRANIŞSAL ölçüm: `-X importtime` ile GERÇEK koşumda yüklenen modüller arasında
    `meridian` YOKTUR. Statik grep'ten farklı bir sınıf: dolaylı import de yakalanır."""
    p = _defter_yaz(tmp_path)
    r = subprocess.run(
        [sys.executable, "-X", "importtime", str(ARAC), "--dosya", str(p), "--sorgu", "ozet"],
        capture_output=True, text=True, cwd=str(KOK),
    )
    assert r.returncode == 0, r.stderr
    yuklenen = [s.rsplit("|", 1)[-1].strip()
                for s in r.stderr.splitlines() if s.startswith("import time:")]
    sizan = [m for m in yuklenen if m == "meridian" or m.startswith("meridian.")]
    assert not sizan, f"meridian modülü yüklendi: {sizan}"


# ---------------------------------------------------------------------------------------------
# 5. BEDEL — `detay` kesme davranışı ÖLÇÜLÜR (beyan edilen bedelin çivisi)
# ---------------------------------------------------------------------------------------------

UZUN_DETAY = "D" * 300


def _uzun_defter(dizin: pathlib.Path) -> pathlib.Path:
    return _defter_yaz(dizin, satirlar=[
        {"ts": "2026-01-01T09:00:00+00:00", "level": "warn", "event": "uzun_olay",
         "detail": UZUN_DETAY},
    ])


def test_metin_kipinde_detay_100_karakterde_kesilir(tmp_path):
    """Metin kipinde `detay` 100 karakterde kesilir ve kesik `…` ile GÖRÜNÜR olur.

    Bedel yasası: kesme BEYAN edildi, burada ÖLÇÜLÜYOR — beyan edilip ölçülmeyen bedel,
    ölçülmemiş bir kayıptır."""
    p = _uzun_defter(tmp_path)
    r = kos("--dosya", str(p), "--sorgu", "son")
    assert r.returncode == 0, r.stderr
    veri = r.stdout.splitlines()[2]
    sutun = r.stdout.splitlines()[0].index("detay")
    basilan = veri[sutun:].rstrip()
    assert basilan.endswith("…"), f"kesik imi yok: {basilan[-20:]!r}"
    assert basilan == "D" * 100 + "…", f"kesme 100 karakterde değil: {len(basilan) - 1}"
    assert UZUN_DETAY not in r.stdout, "metin kipinde tam detay basılmış — kesme etkisiz"


def test_json_kipinde_detay_tam_basilir(tmp_path):
    """`--json` KESMEZ: metin kipinde kaybedilen tam 300 karakter burada geri alınır.
    Kesmenin meşruiyeti bu geri-alma yolunun VARLIĞINA dayanır."""
    p = _uzun_defter(tmp_path)
    r = kos("--dosya", str(p), "--sorgu", "son", "--json")
    assert r.returncode == 0, r.stderr
    satir = json.loads(r.stdout.splitlines()[0])
    assert satir["detay"] == UZUN_DETAY
    assert len(satir["detay"]) == 300
    assert "…" not in satir["detay"], "json kipinde kesik imi sızmış"


# ---------------------------------------------------------------------------------------------
# 6. BAĞLANTI SERTLEŞTİRMESİ — geçici dizin sızıntısı ve eklenti oto-indirme kapalı
# ---------------------------------------------------------------------------------------------

def test_kosum_cwd_ye_tmp_dizini_dokmez(tmp_path):
    """DuckDB varsayılan `temp_directory` '.tmp' ve CWD-GÖRELİdir (ölçüldü, 1.5.5): sertleştirme
    olmadan araç operatörün bulunduğu dizine sessizce `.tmp/` dökebilir. Koşum, ARACIN
    ÇALIŞTIĞI cwd'de yapılır ve o dizin koşumdan sonra da temiz olmalıdır."""
    p = _uzun_defter(tmp_path)
    is_dizini = tmp_path / "iscwd"
    is_dizini.mkdir()
    r = kos("--dosya", str(p), "--sorgu", "son", cwd=is_dizini)
    assert r.returncode == 0, r.stderr
    kalinti = [f.name for f in is_dizini.iterdir()]
    assert kalinti == [], f"cwd'ye artefakt döküldü: {kalinti}"


@pytest.mark.parametrize("ayar", ["autoinstall_known_extensions", "autoload_known_extensions"])
def test_eklenti_oto_indirme_kapali(tmp_path, ayar):
    """Eklenti oto-indirme/oto-yükleme KAPALI. Varsayılanı TRUE (ölçüldü): açık kalsaydı bir
    sorgu bilinmeyen bir fonksiyona dokunduğunda DuckDB AĞDAN eklenti çekebilirdi — yerel bir
    defter okuyucusunun ağ yüzeyi olmamalı. Ayarın kendisi SELECT ile ölçülüyor."""
    p = _defter_yaz(tmp_path)
    r = kos("--dosya", str(p), "--sql", f"SELECT current_setting('{ayar}') AS deger", "--json")
    assert r.returncode == 0, r.stderr
    assert json.loads(r.stdout.splitlines()[0])["deger"] in (False, "false"), r.stdout


def test_temp_directory_bosaltilmis(tmp_path):
    """`temp_directory` boşaltılmış — varsayılan '.tmp' değil."""
    p = _defter_yaz(tmp_path)
    r = kos("--dosya", str(p), "--sql", "SELECT current_setting('temp_directory') AS deger",
            "--json")
    assert r.returncode == 0, r.stderr
    assert json.loads(r.stdout.splitlines()[0])["deger"] == ""


# ---------------------------------------------------------------------------------------------
# 6b. BELLEK TAVANI (TSK-012 açık kalem 2)
#
# ÖLÇÜLEN BOŞLUK: sertleştirme temp dizinini, iki eklenti bayrağını ve saat dilimini ayarlıyordu
# ama `memory_limit` YOKTU → duckdb varsayılanı sistem RAM'inin ~%80'i. Bu araç A1'de ELLE, canlı
# uvicorn ile AYNI makinede koşar (4 OCPU / 24 GB): tavansız bir çapraz-birleştirme panoyu
# düşürebilirdi. Tavan ORTAMDAN ayarlanabilir ki A1'de ölçülen bir ihtiyaç kodu değiştirmeden
# karşılanabilsin. Değer duckdb'nin KENDİ biçimiyle ölçülür (`current_setting`), yazdığımız
# dizgeyle değil: "SET koştu" ile "tavan YÜRÜDÜ" ayrı iddialardır.
# ---------------------------------------------------------------------------------------------

def _bellek_ayari(tmp_path, ortam=None) -> str:
    p = _defter_yaz(tmp_path)
    r = kos("--dosya", str(p), "--sql", "SELECT current_setting('memory_limit') AS deger",
            "--json", ortam=ortam)
    assert r.returncode == 0, r.stderr
    return str(json.loads(r.stdout.splitlines()[0])["deger"])


#: DUCKDB İKİ BİRİM SİSTEMİ KULLANIR — ÖLÇÜLDÜ (1.5.5, 2026-09-13): girdi 'GB'/'MB' ONLUKTUR
#: (10^9 / 10^6 bayt), rapor ise İKİLİDİR (GiB/MiB). Bu yüzden '2GB' → "1.8 GiB", '256MB' →
#: "244.1 MiB". Beklenen değerler bu yüzden TAHMİN değil ÖLÇÜM'dür; "2.0 GiB" yazan bir çivi
#: doğru kodda kırmızı olurdu (ve '1GB' → "1.0 GiB" varsayımıyla ilk yazımında oldu).
BEKLENEN_VARSAYILAN_BELLEK = "1.8 GiB"          # `OLAY_SORGU_BELLEK` verilmediğinde: '2GB'
BEKLENEN_ORTAM_BELLEGI = "244.1 MiB"            # `OLAY_SORGU_BELLEK=256MB` verildiğinde


def test_bellek_tavani_varsayilan_2GB(tmp_path):
    """Ortam değişkeni VERİLMEDİĞİNDE varsayılan tavan yürür — ve bu 6,3 GiB'lik (RAM'in ~%80'i)
    duckdb varsayılanı DEĞİLDİR. Değer duckdb'nin KENDİ biçimiyle ölçülür.

    TABAN 1GB→2GB YÜKSELTİLDİ (TSK-012 düzeltme turu, 2026-09-13). Gerekçe ÖLÇÜLDÜ: bu bağlantı
    `ops/bar_sorgu.py` ve `ops/bar_arsivle.py` ile PAYLAŞILIR ve bar arşivi bu makinede 1.350.678
    satırdır (260 CSV, başlıklar dahil; `cat state/bars/*.csv | wc -l`, 2026-09-13). `temp_
    directory` BOŞ olduğu için diske taşma yolu kapalıdır: 1GB'da taşan bir birleştirme YAVAŞLAMAZ,
    OOM ile DÜŞER. Tavan hâlâ tavandır — 6,3 GiB'lik duckdb varsayılanının çok altındadır."""
    assert _bellek_ayari(tmp_path) == BEKLENEN_VARSAYILAN_BELLEK


def test_bellek_tavani_ORTAM_DEGISKENIYLE_ayarlanir(tmp_path):
    """`OLAY_SORGU_BELLEK` verildiğinde O değer yürür — operatör A1'de tavanı kod değiştirmeden
    daraltıp genişletebilmeli (geri alma yolu)."""
    assert _bellek_ayari(tmp_path, {"OLAY_SORGU_BELLEK": "256MB"}) == BEKLENEN_ORTAM_BELLEGI


def test_bellek_tavani_sohbetin_tavaniyla_AYNI_KAYNAKTAN_GELMEZ():
    """TEK-KAYNAK İSTİSNASI, BEYANLI. `meridian/sohbet.py` kendi bağlantısına 512MB koyar; bu
    araç 1GB'a kadar açıktır ve İKİSİ BİLEREK AYRIDIR (canlı API işçisi ile elle koşan CLI aynı
    bütçeyi paylaşmaz). Kopya DEĞİL, iki ayrı karardır — ve bu çivi ayrılığın BEYAN EDİLDİĞİNİ
    ölçer: iki dosya birbirine şerhle atıf vermezse ayrılık bir gün "unutulmuş kopya" sanılır."""
    kaynak = ARAC.read_text(encoding="utf-8")
    assert "OLAY_SORGU_BELLEK" in kaynak
    assert "SOHBET_SQL_BELLEK" in kaynak, (
        "sorgulayıcı sohbetin tavanına şerhle atıf vermiyor — ayrılık beyansız kalır")
    sohbet_kaynak = (KOK / "meridian" / "sohbet.py").read_text(encoding="utf-8")
    assert "OLAY_SORGU_BELLEK" in sohbet_kaynak, (
        "sohbet CLI tavanına şerhle atıf vermiyor — beyan tek yönlü kalır")
    assert "import meridian" not in kaynak and "from meridian" not in kaynak, (
        "beyan ŞERHLE yapılır, İTHALLE değil: ops betiği meridian'a ulaşırsa obs sızıntısı açılır")


def test_bellek_tavani_serhi_PAYLASILAN_YUZEYI_ADIYLA_beyan_eder():
    """ŞERH BİR ARAYÜZ BEYANIDIR. `BELLEK_TAVANI` yalnız bu aracın değil, `baglanti_kur`u çağıran
    ÜÇ ops aracının daha tavanıdır; hangi araçların paylaştığı ADIYLA yazılmazsa taban bir gün
    "yalnız olay sorgulayıcısının işi" sanılarak daraltılır ve bar araçları sessizce OOM olur.
    Yükseltme yolu da ADIYLA yazılır: `OLAY_SORGU_BELLEK` kodu değiştirmeden tavanı açar."""
    kaynak = ARAC.read_text(encoding="utf-8")
    for beyan in ("ops/bar_sorgu.py", "ops/bar_arsivle.py", "ops/olay_sikistir.py",
                  "OLAY_SORGU_BELLEK=4GB"):
        assert beyan in kaynak, f"paylaşılan yüzey/yükseltme yolu beyansız: {beyan}"


# ---------------------------------------------------------------------------------------------
# 6c. BOZUK TAVAN BİÇİMİ — ÇIKIŞ KODU SÖZLEŞMESİNİN İÇİNDE KALIR (inceleme bulgusu 2, 2026-09-13)
#
# ÖLÇÜLEN BOŞLUK: `OLAY_SORGU_BELLEK=2 gigabayt` gibi bir değer `SET memory_limit='…'` anında
# DuckDB hatası veriyordu; `con = baglanti_kur()` çağrısı `main()`in try bloğunun DIŞINDA
# durduğu için hata HAM TRACEBACK olarak sızıyor ve süreç 1 ile çıkıyordu — aracın kendi
# belgelediği 0/2/3/4 sözleşmesinin DIŞINDA bir kod. Bozuk bir ortam değişkeni bir KULLANIM
# HATASIDIR; kodu 2'dir.
#
# DEĞER BASILIR: maskelenmez, çünkü bu bir ölçü birimi dizgesidir (sır değil) ve operatör neyi
# yanlış yazdığını göremezse mesaj teşhis etmez.
# ---------------------------------------------------------------------------------------------

#: HER DEĞER ÖLÇÜLDÜ (duckdb 1.5.5, 2026-09-13 — doğrulama EKLENMEDEN ÖNCEKİ davranış):
#:   '2 gigabayt' → rc 1 + ham traceback · '2GBB' → rc 1 + ham traceback  (sözleşme DIŞI)
#:   '-2GB'       → rc 0 ve `memory_limit` = "16383.9 PiB"                (TAVAN SESSİZCE YOK OLUR)
#: İkinci sınıf daha sinsidir: araç KOŞAR, hiçbir şey ötmez, ama korumanın kendisi kapanmıştır.
BOZUK_TAVANLAR = ["2 gigabayt", "2GBB", "GB", "2", "", "512 MB fazlası", "-2GB"]
#: '2 GB' (iç boşluk) ve '  2GB  ' (dış boşluk) DuckDB'ce KABUL EDİLİR (ölçüldü) — desendeki
#: `\s*` grupları bu yüzden vardır, süs değildirler. '700KB' BİLEREK DIŞARIDA: biçimi geçerlidir
#: ama o tavanda `gorunumu_kur` OOM olur ve rc 2'yi BAŞKA bir gerekçeyle (defter okunamadı)
#: döndürür — "biçim geçerli" ile "tavan yeterli" ayrı hükümlerdir.
GECERLI_TAVANLAR = ["2GB", "512MB", "1.5GiB", "2gb", "  2GB  ", "2 GB", "1TB", "256MiB"]


def _taze_arac(monkeypatch, deger: str | None):
    """`ops/olay_sorgu.py`yi KAYNAKTAN TAZE yükler — `BELLEK_TAVANI` ortamı İMPORT ANINDA okur,
    yani env'i değiştirmek tek başına yetmez. `sys.modules`a kaydedilmez: `ops.olay_sorgu`nun
    önbellekteki kopyası (ve onu tutan bar araçları) bu çividen ETKİLENMEZ."""
    if deger is None:
        monkeypatch.delenv("OLAY_SORGU_BELLEK", raising=False)
    else:
        monkeypatch.setenv("OLAY_SORGU_BELLEK", deger)
    return betikten_modul_yukle(ARAC, "olay_sorgu_taze")


@pytest.mark.parametrize("bozuk", BOZUK_TAVANLAR)
def test_BOZUK_tavan_rc2_ve_gerekce_ADI_DEGERI_BICIMI_tasir(tmp_path, bozuk):
    """Operatörün koşacağı BİÇİMDE: bozuk `OLAY_SORGU_BELLEK` → rc 2 (kullanım hatası),
    stderr'de DEĞİŞKEN ADI + VERİLEN DEĞER + BEKLENEN BİÇİM, stdout BOŞ. Ham traceback YOK:
    yığın izi operatöre "hangi env değişkenini nasıl yazacağım" sorusunu cevaplamaz."""
    p = _defter_yaz(tmp_path)
    r = kos("--dosya", str(p), "--sorgu", "son", ortam={"OLAY_SORGU_BELLEK": bozuk})
    assert r.returncode == 2, f"rc={r.returncode} · stderr={r.stderr!r}"
    assert r.stdout == "", r.stdout
    assert "OLAY_SORGU_BELLEK" in r.stderr, r.stderr
    assert repr(bozuk) in r.stderr, f"verilen değer basılmadı: {r.stderr!r}"
    for birim in ("KB", "MB", "GB", "TB", "KiB", "MiB", "GiB"):
        assert birim in r.stderr, f"beklenen biçimde {birim} yok: {r.stderr!r}"
    assert "Traceback" not in r.stderr, r.stderr


@pytest.mark.parametrize("gecerli", GECERLI_TAVANLAR)
def test_GECERLI_tavan_bicimleri_KABUL_edilir(tmp_path, gecerli):
    """Kapının BEDELİ ölçülür (Bedel yasası): doğrulama meşru bir değeri reddederse kazanılan
    şey teşhis değil, kaybedilen şey aracın kendisidir. Ondalık ('1.5GiB'), küçük harf ('2gb'),
    dış boşluk ('  2GB  ') ve yedi birimin hepsi GEÇER — ve DuckDB de kabul eder (rc 0)."""
    p = _defter_yaz(tmp_path)
    r = kos("--dosya", str(p), "--sorgu", "son", ortam={"OLAY_SORGU_BELLEK": gecerli})
    assert r.returncode == 0, f"rc={r.returncode} · stderr={r.stderr!r}"


def test_bozuk_tavan_KUTUPHANE_yolunda_SystemExit_ATMAZ(monkeypatch):
    """TASARIM KARARI, ÖLÇÜLDÜ. `baglanti_kur` bir KÜTÜPHANE fonksiyonudur ve onu `meridian/
    sohbet.py` CANLI API işçisinin ipliğinde de çağırır. Orada `_arac_kos`un `except Exception`
    kalkanı araç arızasını metne çevirir ("döngü ölmez"); `SystemExit` BaseException'dır ve o
    kalkanı DELERDİ — bir ortam değişkeni yazım hatası canlı istek ipliğini düşürürdü.
    Bu yüzden kütüphane katmanı `BellekTavaniHatasi(ValueError)` ATAR, süreci ÖLDÜRMEZ."""
    mod = _taze_arac(monkeypatch, "2 gigabayt")
    with pytest.raises(Exception) as ei:            # ← canlı yoldaki kalkanın TA KENDİSİ
        mod.baglanti_kur()
    assert isinstance(ei.value, mod.BellekTavaniHatasi), type(ei.value)
    assert isinstance(ei.value, ValueError), type(ei.value)
    assert not isinstance(ei.value, SystemExit), (
        "kütüphane katmanı süreci öldürüyor — canlı `except Exception` kalkanı delinir")
    assert "OLAY_SORGU_BELLEK" in str(ei.value) and "'2 gigabayt'" in str(ei.value), str(ei.value)


def test_CLI_KAPISI_ayni_hatayi_cikis_kodu_2ye_cevirir(monkeypatch, capsys):
    """Çıkış kodu eşlemesi TEK YERDE, `baglanti_kur_cli`dedir: dört aracın dördü de aynı kapıdan
    geçer, dördünün de sözleşmesinde 2 = kullanım hatasıdır. Kapı stderr'e yazar (Yasa 4: sessiz
    yutma yok) ve `SystemExit(2)` atar."""
    mod = _taze_arac(monkeypatch, "2 gigabayt")
    with pytest.raises(SystemExit) as ei:
        mod.baglanti_kur_cli()
    assert ei.value.code == 2, ei.value.code
    assert "OLAY_SORGU_BELLEK" in capsys.readouterr().err


def test_NEGATIF_TAVAN_reddedilir_SESSIZ_KORUMA_KAYBI(tmp_path):
    """KAPININ ASIL KAZANCI BU VAKADA ÖLÇÜLÜR. `OLAY_SORGU_BELLEK=-2GB` DuckDB'ce KABUL EDİLİYOR
    ve `memory_limit`i "16383.9 PiB" yapıyordu (ölçüldü 2026-09-13): araç rc 0 ile koşuyor, hiçbir
    şey ötmüyor, ama tavan PRATİKTE KALKMIŞ oluyordu — koruma sessizce kayboluyordu. Desen bir
    işaret kabul etmez; bu yüzden değer kapıda ÖLÜR."""
    p = _defter_yaz(tmp_path)
    r = kos("--dosya", str(p), "--sql", "SELECT current_setting('memory_limit') AS deger",
            "--json", ortam={"OLAY_SORGU_BELLEK": "-2GB"})
    assert r.returncode == 2, f"rc={r.returncode} · stdout={r.stdout!r}"
    assert "PiB" not in r.stdout, r.stdout


def test_TiB_REDDEDILIR_OLCULEN_SINIR(tmp_path):
    """ÖLÇÜLEN SINIR, gizlenmiş değil BEYAN EDİLMİŞ boşluk (X_KEY deseninin kardeşi). DuckDB'nin
    kendi hata metni dört ikili birim sayar (KiB, MiB, GiB, TiB) ama bu kapının birim listesi
    Rol-1'in hükmettiği listedir ve TiB TAŞIMAZ: `4TiB` yazan bir operatör rc 2 alır. Bedel
    ölçülmüştür ve küçüktür (bu araç 24 GB'lık bir makinede koşar); genişletme AYRI bir karardır
    ve bu çivi kararın bugünkü hâlini GÖRÜNÜR kılar — sessiz bırakılsaydı bir gün "araç bozuk"
    diye teşhis edilirdi."""
    p = _defter_yaz(tmp_path)
    r = kos("--dosya", str(p), "--sorgu", "son", ortam={"OLAY_SORGU_BELLEK": "4TiB"})
    assert r.returncode == 2, f"rc={r.returncode} · stderr={r.stderr!r}"
    assert "'4TiB'" in r.stderr, r.stderr


def test_CANLI_YOL_cli_kapisindan_GECMEZ():
    """Beyanın öteki yarısı: `meridian/sohbet.py` süreç öldüren kapıyı KULLANMAZ. Bu çivi bir gün
    biri "tek tip olsun" diye canlı yolu `baglanti_kur_cli`ye çevirirse öter."""
    sohbet_kaynak = (KOK / "meridian" / "sohbet.py").read_text(encoding="utf-8")
    # ŞERH KOD DEĞİLDİR: `baglanti_kur_cli` adı sohbet.py'nin BEYAN şerhinde geçer (ve geçmesi
    # gerekir — ayrım orada anlatılıyor). Ölçülen şey ÇAĞRI'dır, yani kod satırları.
    kod = "\n".join(s for s in sohbet_kaynak.splitlines() if not s.lstrip().startswith("#"))
    assert "baglanti_kur_cli" not in kod, (
        "canlı API yolu CLI kapısından geçiyor — bozuk bir env değeri uvicorn işçisini düşürür")
    assert "_os_mod.baglanti_kur()" in kod, "canlı yol kütüphane çağrısını kaybetti"


# ---------------------------------------------------------------------------------------------
# 7. ÇIKIŞ KODU SÖZLEŞMESİ — dört vakanın DÖRDÜ de çivili
# ---------------------------------------------------------------------------------------------

def test_cikis_kodu_0_sorgu_kostu(tmp_path):
    p = _defter_yaz(tmp_path)
    assert kos("--dosya", str(p), "--sorgu", "ozet").returncode == 0


def test_cikis_kodu_2_kullanim_ve_dosya_hatasi(tmp_path):
    """rc=2 İKİ kullanım sınıfını da kapsar: olmayan dosya VE eksik/çelişen bayrak."""
    p = _defter_yaz(tmp_path)
    assert kos("--dosya", str(tmp_path / "yok.jsonl")).returncode == 2
    assert kos("--dosya", str(p), "--sorgu", "tip").returncode == 2


def test_cikis_kodu_3_sql_reddedildi(tmp_path):
    p = _defter_yaz(tmp_path)
    r = kos("--dosya", str(p), "--sql", "DROP TABLE olaylar")
    assert r.returncode == 3, r.stderr


def test_cikis_kodu_4_sorgu_duduk(tmp_path):
    """rc=4 = kapıdan GEÇTİ ama DuckDB'de düştü. rc=3'ten AYRI olması gerekir: biri 'sorman
    yasak', diğeri 'sordun, cevaplanamadı' — tek koda katlanırsa teşhis kaybolur."""
    p = _defter_yaz(tmp_path)
    r = kos("--dosya", str(p), "--sql", "SELECT olmayan_sutun FROM olaylar")
    assert r.returncode == 4, f"rc={r.returncode} stderr={r.stderr}"
    assert "sorgu düştü" in r.stderr


def test_sql_ile_hazir_sorgu_bayraklari_sessizce_yok_sayilmaz(tmp_path):
    """`--sql` yanında `--sorgu`/`--tip`/`--n` SESSİZCE yok sayılmaz — açık kullanım hatası.
    (`--uygula` sessizce yok sayılıyordu vakasının sınıfı: yok sayılan bayrak, operatöre
    yapılmamış bir işi yapılmış gösterir.)"""
    p = _defter_yaz(tmp_path)
    for fazla in (("--sorgu", "son"), ("--tip", "hotstate_down"), ("--n", "5")):
        r = kos("--dosya", str(p), "--sql", "SELECT count(*) AS n FROM olaylar", *fazla)
        assert r.returncode == 2, f"{fazla} sessizce yutuldu (rc={r.returncode})"
        assert fazla[0] in r.stderr, r.stderr
        assert not r.stdout.strip(), "çelişkili çağrı yine de sonuç bastı"


def test_nobetci_query_fonksiyonuyla_yazma_bugun_duckdb_tarafindan_reddediliyor(tmp_path):
    """NÖBETÇİ ÇİVİ — bugünkü gerçeği sabitler, yarın gevşerse öter.

    `SELECT * FROM query('COPY ... TO ...')` ilk-jeton ve tip kapılarının İKİSİNDEN de geçer
    (dıştan bakınca düz bir SELECT'tir). Bugün yazma OLMUYOR, ama bunu BİZİM kapımız değil
    DuckDB'nin kendi ayrıştırıcısı engelliyor: `query()` yalnız tek SELECT kabul eder ve
    Parser Error verir (rc=4). Yani bu yüzeydeki güvenlik ÖDÜNÇTÜR. DuckDB bir gün `query()`
    içinde COPY'ye izin verirse bu çivi kırılır ve kapının kendi savunmasını kazanması
    gerektiğini söyler. Ölçülen şey İKİSİ BİRDEN: hata sinyali VE diskte dosya olmaması."""
    p = _defter_yaz(tmp_path)
    hedef = tmp_path / "kacak_q.csv"
    once = {f.name for f in tmp_path.iterdir()}
    r = kos("--dosya", str(p), "--sql",
            f"SELECT * FROM query('COPY (SELECT 1) TO ''{hedef}''')")
    assert r.returncode != 0, r.stdout
    assert not hedef.exists(), "query() üzerinden dosya YAZILDI — kapı artık kendi savunmasını kazanmalı"
    assert {f.name for f in tmp_path.iterdir()} == once


# ---------------------------------------------------------------------------------------------
# 8. RUNBOOK — üretici başlığı BOŞ çıkarmıyor (üretim KOŞULMADAN ölçülür)
# ---------------------------------------------------------------------------------------------

def test_runbook_ureticisi_olay_sorgu_basligini_bos_cikarmiyor():
    """`ops/runbook_uret.py::betik_basliklari` bu aracın başlığını OKUYABİLMELİ.

    NEDEN AYRI ÇİVİ: ayrıştırıcı shebang'ten SONRAKİ bitişik `#` bloğunu okur. Docstring'i
    GÖRMEZ. Araç yalnız docstring taşısaydı RUNBOOK girdisi SESSİZCE BOŞ çıkardı — belge
    üretilir, bölüm açılır, içi boş olurdu (Yasa 6'nın en sinsi biçimi: okuyucu var, içerik yok).
    Üretim KOŞULMAZ: ölçülen şey yalnız ayrıştırıcının bu dosyadan ne çıkardığı."""
    U = betikten_modul_yukle(KOK / "ops" / "runbook_uret.py", "runbook_uret")
    basliklar = {b["yol"]: b["baslik"] for b in U.betik_basliklari()}
    assert "ops/olay_sorgu.py" in basliklar, (
        f"araç BETIK_KUMESI'nde yok: {sorted(basliklar)}")
    baslik = basliklar["ops/olay_sorgu.py"]
    assert baslik.strip(), "başlık BOŞ çıktı — shebang sonrası bitişik `#` bloğu yok"
    # İçerik iddiası: başlık aracın NE OLDUĞUNU söylemeli, yalnız dolu olmamalı.
    assert "olay_sorgu.py" in baslik and "DuckDB" in baslik, baslik
    assert "meridian" in baslik.lower(), "başlık obs-sızıntısı sözleşmesini taşımıyor"


def test_runbook_uretimi_olay_sorgu_bolumunu_dolu_uretiyor():
    """ÜRETİLEN belge (BELLEKTE, diske YAZILMADAN) bu araç için DOLU bir bölüm içeriyor.

    Bir önceki çivi ayrıştırıcıyı ölçer; bu çivi ÜRÜNÜ ölçer — ikisi ayrı sınıftır: başlık
    okunabilir olduğu hâlde belge şablonu bölümü boş bırakabilirdi. `uret()` saf bir
    fonksiyondur (v154 de onu böyle çağırır), dosya YAZILMAZ: üretim Rol-1'in tur kapanışı
    işidir (CLAUDE.md §8) ve bu çivi o işi YAPMAZ, yalnız sonucunu önceden ölçer."""
    U = betikten_modul_yukle(KOK / "ops" / "runbook_uret.py", "runbook_uret")
    belge = U.uret()
    baslik_satiri = "## `ops/olay_sorgu.py` {#"
    assert baslik_satiri in belge, "üretilen belgede araç bölümü açılmamış"
    bolum = belge[belge.index(baslik_satiri):]
    son = bolum.find("\n## ", 1)
    bolum = bolum[:son] if son > 0 else bolum
    govde = bolum.split("\n", 1)[1].strip()
    assert govde, "bölüm AÇILDI ama İÇİ BOŞ — Yasa 6'nın sinsi biçimi"
    assert "DuckDB" in govde, f"bölüm gövdesi başlıktan beslenmemiş: {govde[:200]!r}"
