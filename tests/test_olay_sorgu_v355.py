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


def kos(*argv: str, cwd: pathlib.Path | None = None) -> subprocess.CompletedProcess:
    """Aracı OPERATÖRÜN koşacağı biçimde çağırır: komut satırı, `main()` değil."""
    return subprocess.run(
        [sys.executable, str(ARAC), *argv],
        capture_output=True,
        text=True,
        cwd=str(cwd or KOK),
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
