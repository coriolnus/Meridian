"""v379 — `ops/olay_sikistir.py` + `ops/olay_sorgu.py` BİRLEŞİK OKUMA çivileri
(TSK-020 [UYGULA-2] adım 2, 2026-09-03).

NUMARA SEÇİMİ: `ls tests/ | grep -oE "v[0-9]{3}" | sort -u | tail -1` ile ölçüldü — en büyük
alınmış numara v378 idi (2026-09-03). v379 boştu; `ls tests | grep -E "v379|v380"` boş döndü,
çakışma yok.

NEYİ ÇİVİLER (sınıf sınıf):
  1. SÖZLEŞME KOMUT SATIRIDIR — her çivi aracı `subprocess` ile ÇAĞIRIR, `main()` import
     ETMEZ (v355'ten devralınan disiplin; `--uygula` sessizce yok sayılıyordu vakası).
  2. AY ANAHTARI UTC'DİR — `ts` alanındaki OFSET hesaba katılır. Yerel saat dilimiyle
     ay sınırı kayarsa satır YANLIŞ dosyaya girer ve bir daha bulunamaz. Ölçüldü
     (duckdb 1.5.5): `TimeZone` varsayılanı MAKİNENİN yerelidir (bu makinede
     Europe/Istanbul) ve ofsetsiz bir `ts` o dilime göre çözülür → aynı defter iki
     makinede iki farklı aya düşerdi.
  3. CARİ AY YAZILMAZ — hâlâ yazılan bir ay dondurulamaz.
  4. IDEMPOTENT + SESSİZ ÜZERİNE YAZMA YOK — aynı içerik "atlandı", FARKLI içerik
     `.yeni` + KIRMIZI (rc=3). Sessiz üzerine yazma, arşivi kanıt olmaktan çıkarır.
  5. DEFTER KIRPILMAZ — adım 2 yalnız sıkıştırır (kırpma ayrı karar; okuyucular jsonl'e
     bakıyor). Koşum sonrası `state/events.jsonl` BAYT BAYT aynıdır.
  6. YASA 4 — bozuk JSON satırı ve AY'a atanamayan satır SAYILIR ve stderr'e raporlanır.
  7. YASA 6 — parquet'in OKUYUCUSU `ops/olay_sorgu.py`'dır ve bu ÖLÇÜLÜR: defterden
     geçmiş aylar SİLİNDİĞİNDE bile sorgu o ayları PARQUET'ten döndürür. Okuyucusu
     ölçülmemiş bir arşiv, üretilmemiş bir arşiftir.
  8. ÇİFT SAYIM YOK — parquet'lenmiş aylar jsonl tarafından SÜZÜLÜR (kural: PARQUET
     KAZANIR; bkz. `ops/olay_sorgu.py` başlığı).
  9. OBS SIZINTISI KAPALI — araç `meridian`ı import ETMEZ (statik + `-X importtime`).

GERÇEK DEFTERE DOKUNULMAZ: her çivi `tmp_path` altına kendi sentetik jsonl'ini yazar;
`state/events.jsonl` ve `state/olaylar/` bu dosyada hiç açılmaz.
"""

from __future__ import annotations

import datetime as _dt
import json
import pathlib
import subprocess
import sys

import pytest

KOK = pathlib.Path(__file__).resolve().parents[1]
SIKISTIR = KOK / "ops" / "olay_sikistir.py"
SORGU = KOK / "ops" / "olay_sorgu.py"


# ---------------------------------------------------------------------------------------------
# Sentetik defter — aylar KOŞUM ANINA GÖRE türetilir (sabit tarih yazılsaydı çivi bir sonraki
# ayda "cari ay" iddiasını kaybederdi: sabit bir ay er ya da geç GEÇMİŞ olur ve o gün çivi
# sessizce başka bir şeyi ölçmeye başlardı).
# ---------------------------------------------------------------------------------------------

_SIMDI = _dt.datetime.now(_dt.timezone.utc)


def _ay_kaydir(n: int) -> str:
    t = _SIMDI.year * 12 + (_SIMDI.month - 1) + n
    return f"{t // 12:04d}-{t % 12 + 1:02d}"


CARI = _ay_kaydir(0)
ONCEKI = _ay_kaydir(-1)
ONCESI = _ay_kaydir(-2)


def _satir(ay: str, gun: str, saat: str, event: str, **ek) -> dict:
    return {"ts": f"{ay}-{gun}T{saat}+00:00", "level": "info", "event": event, **ek}


SATIRLAR = [
    _satir(ONCESI, "01", "09:00:00", "daily_cycle", candidates=3),
    _satir(ONCESI, "02", "10:00:00", "hotstate_down", url="http://x"),
    _satir(ONCEKI, "01", "09:00:00", "daily_cycle", candidates=1),
    _satir(ONCEKI, "02", "10:00:00", "hotstate_down", url="http://y"),
    _satir(ONCEKI, "03", "11:00:00", "breaker_trip", detail="kapak attı"),
    _satir(CARI, "01", "09:00:00", "daily_cycle", candidates=7),
    _satir(CARI, "01", "10:00:00", "hotstate_down", url="http://z"),
]
GECMIS_ADET = {ONCESI: 2, ONCEKI: 3}


def _defter_yaz(dizin: pathlib.Path, satirlar=None, bozuk: int = 0, ek_ham=()) -> pathlib.Path:
    """Sentetik jsonl yazar; `bozuk` kadar ayrıştırılamaz satırı ARAYA serpiştirir,
    `ek_ham` ham metin satırlarını sona ekler."""
    p = dizin / "olaylar.jsonl"
    govde = [json.dumps(s) for s in (SATIRLAR if satirlar is None else satirlar)]
    for i in range(bozuk):
        govde.insert(min(1 + i * 2, len(govde)), "BU SATIR JSON DEGIL {{{ %d" % i)
    govde.extend(ek_ham)
    p.write_text("\n".join(govde) + "\n", encoding="utf-8")
    return p


def kos(betik: pathlib.Path, *argv: str, cwd: pathlib.Path | None = None):
    """Aracı OPERATÖRÜN koşacağı biçimde çağırır: komut satırı, `main()` değil."""
    return subprocess.run([sys.executable, str(betik), *argv],
                          capture_output=True, text=True, cwd=str(cwd or KOK))


def sikistir(*argv: str, cwd=None):
    return kos(SIKISTIR, *argv, cwd=cwd)


def sorgula(*argv: str, cwd=None):
    return kos(SORGU, *argv, cwd=cwd)


def _jsonl_cikti(r) -> list[dict]:
    return [json.loads(s) for s in r.stdout.splitlines() if s.strip()]


def _hedef(tmp_path: pathlib.Path) -> pathlib.Path:
    """Varsayılan hedef: defterin YANINDAKİ `olaylar/` dizini (state/events.jsonl →
    state/olaylar/)."""
    return tmp_path / "olaylar"


# ---------------------------------------------------------------------------------------------
# 1. SIKIŞTIRMA — geçmiş aylar yazılır, cari ay yazılmaz
# ---------------------------------------------------------------------------------------------

def test_gecmis_aylar_parquet_olur_cari_ay_yazilmaz(tmp_path):
    """Yalnız GEÇMİŞ aylar `AAAA-AA.parquet` olur; hâlâ yazılan cari ay dondurulmaz."""
    p = _defter_yaz(tmp_path)
    r = sikistir("--dosya", str(p))
    assert r.returncode == 0, r.stderr
    dosyalar = sorted(f.name for f in _hedef(tmp_path).iterdir())
    assert dosyalar == [f"{ONCESI}.parquet", f"{ONCEKI}.parquet"], dosyalar
    assert f"{CARI}.parquet" not in dosyalar


def test_cikti_ay_basina_satir_ve_bayt_verir(tmp_path):
    """stdout ay başına SATIR SAYISI ve BAYT verir; sayılar sentetik defterle ELLE doğrulanır
    ve bayt diskteki gerçek dosya boyutudur (beyan değil, ölçüm)."""
    p = _defter_yaz(tmp_path)
    r = sikistir("--dosya", str(p), "--json")
    assert r.returncode == 0, r.stderr
    satirlar = {s["ay"]: s for s in _jsonl_cikti(r)}
    assert set(satirlar) == set(GECMIS_ADET), satirlar
    for ay, adet in GECMIS_ADET.items():
        assert satirlar[ay]["satir"] == adet, satirlar[ay]
        assert satirlar[ay]["durum"] == "yazıldı"
        assert satirlar[ay]["bayt"] == (_hedef(tmp_path) / f"{ay}.parquet").stat().st_size


def test_parquet_ham_satiri_icerik_olarak_korur(tmp_path):
    """Parquet ham satırı KORUR: her anahtar/değer geri okunur ve `ay` sütunu dosya adıyla
    tutarlıdır. (Bedel: biçimsel boşluk normalize olabilir — anlam korunur.)"""
    p = _defter_yaz(tmp_path)
    assert sikistir("--dosya", str(p)).returncode == 0
    r = sorgula("--dosya", str(p), "--sql",
                f"SELECT ay, ham FROM read_parquet('{_hedef(tmp_path)}/{ONCEKI}.parquet')",
                "--json")
    assert r.returncode == 0, r.stderr
    satirlar = _jsonl_cikti(r)
    assert {s["ay"] for s in satirlar} == {ONCEKI}
    okunan = sorted((json.loads(s["ham"]) for s in satirlar), key=lambda d: d["ts"])
    beklenen = sorted((s for s in SATIRLAR if s["ts"].startswith(ONCEKI)), key=lambda d: d["ts"])
    assert okunan == beklenen


def test_ay_anahtari_utc_dir_yerel_saat_dilimi_kaydirmaz(tmp_path):
    """AY = `ts`in UTC ayı. Ofsetli bir `ts` ay sınırını GERİYE geçiyorsa satır ÖNCEKİ aya
    yazılır. Naif (ofsetsiz) `ts` de UTC sayılır — makinenin yereline göre DEĞİL.

    Ölçüldü (duckdb 1.5.5): `TimeZone` varsayılanı makine yerelidir; sertleştirme onu UTC'ye
    sabitlemeseydi bu iki satır bu makinede (Europe/Istanbul) bir aya, bir başkasında başka
    aya düşerdi — ve fark hiçbir yerde görünmezdi."""
    p = _defter_yaz(tmp_path, satirlar=[
        # ONCEKI ayın 1'i, saat 01:00 +03:00 → UTC ONCESI ayının son günü 22:00
        {"ts": f"{ONCEKI}-01T01:00:00+03:00", "level": "info", "event": "sinir_ofsetli"},
        # Ofsetsiz: UTC kabul edilir → ONCEKI ayında kalır
        {"ts": f"{ONCEKI}-01T01:00:00", "level": "info", "event": "sinir_naif"},
    ])
    assert sikistir("--dosya", str(p)).returncode == 0
    r = sorgula("--dosya", str(p), "--sql",
                "SELECT ay, json_extract_string(ham, '$.event') AS event "
                f"FROM read_parquet('{_hedef(tmp_path)}/*.parquet')", "--json")
    assert r.returncode == 0, r.stderr
    gorulen = {s["event"]: s["ay"] for s in _jsonl_cikti(r)}
    assert gorulen == {"sinir_ofsetli": ONCESI, "sinir_naif": ONCEKI}, gorulen


def test_defter_kirpilmaz(tmp_path):
    """Adım 2 YALNIZ sıkıştırır: defter BAYT BAYT aynı kalır (kırpma ayrı karardır —
    okuyucular hâlâ jsonl'e bakıyor)."""
    p = _defter_yaz(tmp_path)
    once = p.read_bytes()
    assert sikistir("--dosya", str(p)).returncode == 0
    assert p.read_bytes() == once


# ---------------------------------------------------------------------------------------------
# 2. IDEMPOTENCY — ikinci koşum atlar; içerik değişmişse KIRMIZI
# ---------------------------------------------------------------------------------------------

def test_ikinci_kosum_atlandi_der_ve_dosyayi_degistirmez(tmp_path):
    """İkinci koşum aynı içeriği YENİDEN YAZMAZ: 'atlandı' der ve dosya baytları değişmez."""
    p = _defter_yaz(tmp_path)
    assert sikistir("--dosya", str(p)).returncode == 0
    once = {f.name: f.read_bytes() for f in _hedef(tmp_path).iterdir()}
    r = sikistir("--dosya", str(p), "--json")
    assert r.returncode == 0, r.stderr
    assert {s["durum"] for s in _jsonl_cikti(r)} == {"atlandı"}, r.stdout
    assert {f.name: f.read_bytes() for f in _hedef(tmp_path).iterdir()} == once


def test_icerik_degisince_yeni_yazilir_ve_kirmizi_doner(tmp_path):
    """Geçmiş ay defterde DEĞİŞMİŞSE sessiz üzerine yazma YOK: `.yeni` yazılır, rc=3,
    gerekçe stderr'de, ESKİ dosya dokunulmadan durur (operatör kıyaslasın diye)."""
    p = _defter_yaz(tmp_path)
    assert sikistir("--dosya", str(p)).returncode == 0
    hedef = _hedef(tmp_path) / f"{ONCEKI}.parquet"
    once = hedef.read_bytes()

    _defter_yaz(tmp_path, satirlar=SATIRLAR + [
        _satir(ONCEKI, "04", "12:00:00", "sonradan_geldi")])

    # Önce KURU koşum: farkı GÖRÜR, ama diske hiçbir şey yazmaz.
    r_kuru = sikistir("--dosya", str(p), "--kuru")
    assert r_kuru.returncode == 3, r_kuru.stdout + r_kuru.stderr
    assert not (_hedef(tmp_path) / f"{ONCEKI}.parquet.yeni").exists()

    r = sikistir("--dosya", str(p), "--json")
    assert r.returncode == 3, r.stdout + r.stderr
    durumlar = {s["ay"]: s["durum"] for s in _jsonl_cikti(r)}
    assert durumlar[ONCEKI] == "FARK", durumlar
    assert durumlar[ONCESI] == "atlandı", durumlar
    yeni = _hedef(tmp_path) / f"{ONCEKI}.parquet.yeni"
    assert yeni.exists(), "fark bulundu ama `.yeni` yazılmadı"
    assert hedef.read_bytes() == once, "ESKİ dosya üzerine yazıldı — kıyas imkânı yok oldu"
    assert ONCEKI in r.stderr and ".yeni" in r.stderr, r.stderr


def test_satir_sayisi_ayni_icerik_farkli_ise_de_yakalanir(tmp_path):
    """Kıyas SAYIM + İÇERİK damgasıdır: satır sayısı DEĞİŞMEDEN içerik değişirse de öter.
    (Yalnız sayım kıyaslansaydı bu vaka sessizce 'atlandı' derdi.)"""
    p = _defter_yaz(tmp_path)
    assert sikistir("--dosya", str(p)).returncode == 0
    degisik = [dict(s) for s in SATIRLAR]
    for s in degisik:
        if s["ts"].startswith(ONCEKI) and s["event"] == "breaker_trip":
            s["detail"] = "BAŞKA GEREKÇE"
    _defter_yaz(tmp_path, satirlar=degisik)
    r = sikistir("--dosya", str(p), "--json")
    assert r.returncode == 3, r.stdout
    assert {s["ay"]: s["durum"] for s in _jsonl_cikti(r)}[ONCEKI] == "FARK"


def test_kuru_kosum_hicbir_sey_yazmaz_ama_ne_yapacagini_soyler(tmp_path):
    """`--kuru` diske DOKUNMAZ (hedef dizin bile açılmaz) ama planı ay ay söyler."""
    p = _defter_yaz(tmp_path)
    r = sikistir("--dosya", str(p), "--kuru", "--json")
    assert r.returncode == 0, r.stderr
    assert not _hedef(tmp_path).exists(), "kuru koşum hedef dizini açtı"
    satirlar = {s["ay"]: s for s in _jsonl_cikti(r)}
    assert set(satirlar) == set(GECMIS_ADET)
    assert {s["durum"] for s in satirlar.values()} == {"yazılacak"}
    for ay, adet in GECMIS_ADET.items():
        assert satirlar[ay]["satir"] == adet
        assert satirlar[ay]["bayt"] is None, "yazılmamış dosyanın baytı UYDURULMUŞ"


# ---------------------------------------------------------------------------------------------
# 3. `--ay` — tek ay
# ---------------------------------------------------------------------------------------------

def test_ay_bayragi_yalniz_o_ayi_yazar(tmp_path):
    p = _defter_yaz(tmp_path)
    r = sikistir("--dosya", str(p), "--ay", ONCEKI)
    assert r.returncode == 0, r.stderr
    assert sorted(f.name for f in _hedef(tmp_path).iterdir()) == [f"{ONCEKI}.parquet"]


def test_ay_bayragi_cari_ayi_gerekceyle_reddeder(tmp_path):
    """Cari ay istense bile yazılmaz — SESSİZ atlama değil, GEREKÇELİ ret."""
    p = _defter_yaz(tmp_path)
    r = sikistir("--dosya", str(p), "--ay", CARI)
    assert r.returncode == 2, r.stdout
    assert CARI in r.stderr and "cari" in r.stderr.lower()
    assert not _hedef(tmp_path).exists()


@pytest.mark.parametrize("kotu", ["2026", "26-01", "2026-13-01", "bugun"])
def test_ay_bayragi_bozuk_bicimi_reddeder(tmp_path, kotu):
    p = _defter_yaz(tmp_path)
    r = sikistir("--dosya", str(p), "--ay", kotu)
    assert r.returncode == 2, r.stdout
    assert "AAAA-AA" in r.stderr, r.stderr


def test_defterde_olmayan_ay_bos_dosya_uretmez(tmp_path):
    """Defterde bulunmayan bir ay için BOŞ parquet yazılmaz — gerekçeyle reddedilir.
    (Boş dosya, 'o ay sıkıştırıldı' yalanını diske yazardı.)"""
    p = _defter_yaz(tmp_path)
    r = sikistir("--dosya", str(p), "--ay", "2019-01")
    assert r.returncode == 2, r.stdout
    assert "2019-01" in r.stderr
    assert not (_hedef(tmp_path) / "2019-01.parquet").exists()


def test_olmayan_defter_gerekceyle_duser(tmp_path):
    yok = tmp_path / "yok.jsonl"
    r = sikistir("--dosya", str(yok))
    assert r.returncode == 2
    assert str(yok) in r.stderr


# ---------------------------------------------------------------------------------------------
# 4. YASA 4 — bozuk satır ve AY'sız satır sessizce yutulmaz
# ---------------------------------------------------------------------------------------------

def test_bozuk_satir_sayilip_stderr_e_raporlanir(tmp_path):
    p = _defter_yaz(tmp_path, bozuk=2)
    r = sikistir("--dosya", str(p), "--json")
    assert r.returncode == 0, r.stderr
    assert "2 satır" in r.stderr, r.stderr
    # Sağlam satırların sayımı bozuk satırlardan ETKİLENMEZ.
    assert {s["ay"]: s["satir"] for s in _jsonl_cikti(r)} == GECMIS_ADET


def test_ay_a_atanamayan_satir_sikistirilmaz_ve_raporlanir(tmp_path):
    """`ts`i olmayan ya da çözülemeyen satır bir AYA atanamaz: UYDURULMAZ, sıkıştırılmaz,
    defterde kalır — ve SAYILARAK stderr'e raporlanır (Yasa 4)."""
    p = _defter_yaz(tmp_path, satirlar=SATIRLAR + [
        {"level": "warn", "event": "ts_yok"},
        {"ts": "cok-bozuk-zaman", "level": "warn", "event": "ts_bozuk"},
    ])
    r = sikistir("--dosya", str(p), "--json")
    assert r.returncode == 0, r.stderr
    assert "2 satır" in r.stderr and "ay" in r.stderr.lower(), r.stderr
    assert {s["ay"]: s["satir"] for s in _jsonl_cikti(r)} == GECMIS_ADET
    r2 = sorgula("--dosya", str(p), "--sql",
                 f"SELECT count(*) AS n FROM read_parquet('{_hedef(tmp_path)}/*.parquet')",
                 "--json")
    assert _jsonl_cikti(r2)[0]["n"] == sum(GECMIS_ADET.values())


# ---------------------------------------------------------------------------------------------
# 5. BİRLEŞİK OKUMA (olay_sorgu) — çift sayım yok, parquet GERÇEKTEN okunuyor
# ---------------------------------------------------------------------------------------------

def test_birlesik_ozet_sayimi_jsonl_toplamina_esit(tmp_path):
    """ÇİFT SAYIM YOK: parquet yazıldıktan sonra `ozet` toplamı defterdeki satır sayısına
    EŞİT kalır (parquet'lenen aylar jsonl tarafından süzülür)."""
    p = _defter_yaz(tmp_path)
    once = sorgula("--dosya", str(p), "--sorgu", "ozet", "--json")
    assert once.returncode == 0, once.stderr
    toplam_once = sum(s["adet"] for s in _jsonl_cikti(once))
    assert toplam_once == len(SATIRLAR)

    assert sikistir("--dosya", str(p)).returncode == 0
    sonra = sorgula("--dosya", str(p), "--sorgu", "ozet", "--json")
    assert sonra.returncode == 0, sonra.stderr
    assert sum(s["adet"] for s in _jsonl_cikti(sonra)) == len(SATIRLAR)


def test_parquet_lenen_ay_jsonl_den_suzulur_kaynak_gorunur(tmp_path):
    """KURAL: parquet KAZANIR — parquet'lenmiş ayın satırları jsonl'de DURSA DA birleşik
    görünüme parquet'ten girer. `kaynak` sütunu bunu GÖRÜNÜR kılar (kural beyanla değil
    ölçümle yaşar)."""
    p = _defter_yaz(tmp_path)
    assert sikistir("--dosya", str(p)).returncode == 0
    r = sorgula("--dosya", str(p), "--sql",
                "SELECT ay, kaynak, count(*) AS adet FROM olaylar GROUP BY 1,2 ORDER BY 1",
                "--json")
    assert r.returncode == 0, r.stderr
    gorulen = {(s["ay"], s["kaynak"]): s["adet"] for s in _jsonl_cikti(r)}
    assert gorulen == {(ONCESI, "parquet"): 2, (ONCEKI, "parquet"): 3, (CARI, "jsonl"): 2}, gorulen


def test_defterden_silinen_aylar_parquet_ten_okunur(tmp_path):
    """YASA 6 — parquet'in OKUYUCUSU BU. Defterden geçmiş aylar SİLİNSE bile sorgu o
    ayları döndürür. Bu çivi olmadan 'okuyucu var' bir BEYAN olurdu: parquet hiç
    okunmasa da bütün sayım çivileri yeşil kalırdı (jsonl zaten her şeyi taşıyor)."""
    p = _defter_yaz(tmp_path)
    assert sikistir("--dosya", str(p)).returncode == 0
    # KIRPMA BENZETİMİ (adım 3'ün kararı henüz alınmadı; burada YALNIZ okuyucu ölçülüyor):
    _defter_yaz(tmp_path, satirlar=[s for s in SATIRLAR if s["ts"].startswith(CARI)])

    r = sorgula("--dosya", str(p), "--sorgu", "ozet", "--json")
    assert r.returncode == 0, r.stderr
    assert sum(s["adet"] for s in _jsonl_cikti(r)) == len(SATIRLAR)

    # `son` ve `tip` de birleşiktir — yalnız `ozet` değil.
    r_son = sorgula("--dosya", str(p), "--sorgu", "son", "--n", "50", "--json")
    assert len({s["ts"] for s in _jsonl_cikti(r_son)}) == len(SATIRLAR)
    r_tip = sorgula("--dosya", str(p), "--sorgu", "tip", "--tip", "breaker_trip", "--json")
    assert [s["olay"] for s in _jsonl_cikti(r_tip)] == ["breaker_trip"], r_tip.stdout


def test_ay_siz_satirlar_birlesimde_kaybolmaz(tmp_path):
    """AY'ı NULL olan satır (ts yok/çözülemiyor) arşive girmez — ve birleşimde de DÜŞMEZ.

    SQL'in üç-değerli mantığı bu satırları sessizce yutmaya hazırdır: süzgeç yalnız
    `ay NOT IN (...)` olsaydı `NULL NOT IN (...)` → NULL → satır elenirdi ve defterdeki
    2 satır hiçbir sorguda GÖRÜNMEZDİ. Kaybın sessiz olduğu yerde çivi gerekir."""
    satirlar = SATIRLAR + [
        {"level": "warn", "event": "ts_yok"},
        {"ts": "cok-bozuk-zaman", "level": "warn", "event": "ts_bozuk"},
    ]
    p = _defter_yaz(tmp_path, satirlar=satirlar)
    assert sikistir("--dosya", str(p)).returncode == 0
    r = sorgula("--dosya", str(p), "--sorgu", "ozet", "--n", "99", "--json")
    assert r.returncode == 0, r.stderr
    assert sum(s["adet"] for s in _jsonl_cikti(r)) == len(satirlar)
    r2 = sorgula("--dosya", str(p), "--sql",
                 "SELECT count(*) AS n FROM olaylar WHERE ay IS NULL", "--json")
    assert _jsonl_cikti(r2)[0]["n"] == 2, r2.stdout


def test_parquet_kullanildiginda_stderr_bunu_soyler(tmp_path):
    """Sonucun NEREDEN geldiği görünür: birleşik okuma yapıldığında stderr kaç ayın
    parquet'ten geldiğini söyler. Sessiz birleştirme, sorgunun anlamını gizler."""
    p = _defter_yaz(tmp_path)
    r_once = sorgula("--dosya", str(p), "--sorgu", "ozet")
    assert "parquet" not in r_once.stderr.lower(), r_once.stderr
    assert sikistir("--dosya", str(p)).returncode == 0
    r = sorgula("--dosya", str(p), "--sorgu", "ozet")
    assert r.returncode == 0, r.stderr
    assert "parquet" in r.stderr.lower() and ONCEKI in r.stderr, r.stderr


def test_parquet_dizini_yoksa_jsonl_tek_basina_okunur(tmp_path):
    """Sıkıştırıcı hiç koşmamışsa sorgu DÜŞMEZ: parquet dizini yoksa jsonl tek başına okunur."""
    p = _defter_yaz(tmp_path)
    r = sorgula("--dosya", str(p), "--sorgu", "ozet", "--json")
    assert r.returncode == 0, r.stderr
    assert sum(s["adet"] for s in _jsonl_cikti(r)) == len(SATIRLAR)


def test_yalniz_jsonl_bayragi_parqueti_yok_sayar(tmp_path):
    """`--yalniz-jsonl` ham defteri verir (parquet bayatsa geri dönüş yolu). Kırpılmış
    defterde bu, EKSİK sonuç demektir — ve öyle görünmelidir."""
    p = _defter_yaz(tmp_path)
    assert sikistir("--dosya", str(p)).returncode == 0
    _defter_yaz(tmp_path, satirlar=[s for s in SATIRLAR if s["ts"].startswith(CARI)])
    r = sorgula("--dosya", str(p), "--sorgu", "ozet", "--yalniz-jsonl", "--json")
    assert r.returncode == 0, r.stderr
    assert sum(s["adet"] for s in _jsonl_cikti(r)) == 2


def test_yalniz_jsonl_ile_parquet_dizini_sessizce_yok_sayilmaz(tmp_path):
    """Çelişen iki bayrak SESSİZCE yutulmaz — açık kullanım hatasıdır (`--uygula` sınıfı).

    RET BİZİM KAPIDAN GELMELİ: yalnız rc=2 + bayrak adları aransaydı çivi araç bu bayrakları
    HİÇ TANIMAZKEN de yeşil olurdu (argparse 'unrecognized arguments' der ve o da rc=2 +
    bayrak adı taşır — kırmızı turda tam bunu yaptı: vakumlu yeşil)."""
    p = _defter_yaz(tmp_path)
    r = sorgula("--dosya", str(p), "--yalniz-jsonl", "--parquet-dizin", str(tmp_path))
    assert r.returncode == 2, r.stdout
    assert "unrecognized" not in r.stderr, "bayraklar TANINMIYOR — ret argparse'tan geliyor"
    assert "--yalniz-jsonl" in r.stderr and "--parquet-dizin" in r.stderr
    assert "birlikte kullanılamaz" in r.stderr, r.stderr


def test_parquet_dizini_bayragi_baska_dizini_okur(tmp_path):
    """`--parquet-dizin` varsayılan yeri (defterin yanındaki `olaylar/`) EZER."""
    p = _defter_yaz(tmp_path)
    baska = tmp_path / "arsiv"
    assert sikistir("--dosya", str(p), "--hedef", str(baska)).returncode == 0
    assert not _hedef(tmp_path).exists()
    r = sorgula("--dosya", str(p), "--parquet-dizin", str(baska), "--sql",
                "SELECT kaynak, count(*) AS adet FROM olaylar GROUP BY 1 ORDER BY 1", "--json")
    assert r.returncode == 0, r.stderr
    assert {s["kaynak"]: s["adet"] for s in _jsonl_cikti(r)} == {"jsonl": 2, "parquet": 5}


# ---------------------------------------------------------------------------------------------
# 6. SERTLEŞTİRME DEVRALINIR + OBS SIZINTISI KAPALI
# ---------------------------------------------------------------------------------------------

def test_sikistirici_cwd_ye_tmp_dizini_dokmez(tmp_path):
    """v355'in sertleştirmesi DEVRALINIR: DuckDB'nin CWD-göreli `.tmp` dökümü kapalı."""
    p = _defter_yaz(tmp_path)
    is_dizini = tmp_path / "iscwd"
    is_dizini.mkdir()
    r = sikistir("--dosya", str(p), cwd=is_dizini)
    assert r.returncode == 0, r.stderr
    assert [f.name for f in is_dizini.iterdir()] == [], "cwd'ye artefakt döküldü"


@pytest.mark.parametrize("ayar,beklenen", [
    ("autoinstall_known_extensions", ("false", False)),
    ("autoload_known_extensions", ("false", False)),
    ("TimeZone", ("UTC",)),
    ("temp_directory", ("",)),
])
def test_sorgu_sertlestirmesi_dort_ayarda_da_yurur(tmp_path, ayar, beklenen):
    """Sertleştirme TEK KAYNAKTAN gelir (`olay_sorgu.SERTLESTIRME`) ve dördü de ölçülür.
    `TimeZone` bu turda EKLENDİ: ay anahtarının makineye göre kaymaması ona bağlı."""
    p = _defter_yaz(tmp_path)
    r = sorgula("--dosya", str(p), "--sql", f"SELECT current_setting('{ayar}') AS deger", "--json")
    assert r.returncode == 0, r.stderr
    assert _jsonl_cikti(r)[0]["deger"] in beklenen, r.stdout


def test_sertlestirme_sikistiricida_kopyalanmamis():
    """TEK-KAYNAK YASASI: sıkıştırıcı sertleştirme ayarlarını KENDİ yazmaz, sorgulayıcıdan
    alır. İki kopya sessizce ayrışırdı (biri sertleşir, diğeri kalır)."""
    kaynak = SIKISTIR.read_text(encoding="utf-8")
    kod = "\n".join(s for s in kaynak.splitlines() if not s.lstrip().startswith("#"))
    for yasak in ("SET temp_directory", "SET autoinstall", "SET autoload", "SET TimeZone"):
        assert yasak not in kod, f"sertleştirme kopyalanmış: {yasak}"
    assert "olay_sorgu" in kod, "sıkıştırıcı sorgulayıcıdan türetmiyor"


def test_kaynakta_meridian_importu_yok():
    """Kaynak metni `meridian`ı import ETMEZ — obs sızıntısı yolu kapalı (statik ölçüm)."""
    kaynak = SIKISTIR.read_text(encoding="utf-8")
    kod = [s for s in kaynak.splitlines() if not s.lstrip().startswith("#")]
    suclu = [s for s in kod if "import meridian" in s or "from meridian" in s]
    assert not suclu, suclu
    assert "sys.path.insert" not in "\n".join(kod)


def test_gercek_kosumda_meridian_modulu_yuklenmez(tmp_path):
    """DAVRANIŞSAL ölçüm: `-X importtime` ile GERÇEK koşumda `meridian` YÜKLENMEZ —
    pytest DIŞI koşan bir betik `meridian.obs`'a ulaşırsa canlı deftere YAZAR."""
    p = _defter_yaz(tmp_path)
    r = subprocess.run(
        [sys.executable, "-X", "importtime", str(SIKISTIR), "--dosya", str(p)],
        capture_output=True, text=True, cwd=str(KOK),
    )
    assert r.returncode == 0, r.stderr[-2000:]
    yuklenen = [s.rsplit("|", 1)[-1].strip()
                for s in r.stderr.splitlines() if s.startswith("import time:")]
    sizan = [m for m in yuklenen if m == "meridian" or m.startswith("meridian.")]
    assert not sizan, f"meridian modülü yüklendi: {sizan}"


# ---------------------------------------------------------------------------------------------
# 7. RUNBOOK BAŞLIK SÖZLEŞMESİ — betik operatör-yüzlüdür
# ---------------------------------------------------------------------------------------------

def test_betik_shebang_sonrasi_baslik_blogu_tasiyor():
    """`ops/runbook_uret.py::betik_basliklari` shebang'ten SONRAKİ bitişik `#` bloğunu okur.
    Betik BETIK_KUMESI'ne (Rol-1 kararı) eklendiğinde başlığın HAZIR olması gerekir;
    yalnız docstring taşısaydı RUNBOOK girdisi SESSİZCE BOŞ çıkardı."""
    satirlar = SIKISTIR.read_text(encoding="utf-8").splitlines()
    assert satirlar[0].startswith("#!"), "shebang yok"
    blok = []
    for s in satirlar[1:]:
        if not s.startswith("#"):
            break
        blok.append(s.lstrip("#").strip())
    baslik = " ".join(b for b in blok if b)
    assert "olay_sikistir.py" in baslik and "parquet" in baslik.lower(), baslik
    assert "meridian" in baslik.lower(), "başlık obs-sızıntısı sözleşmesini taşımıyor"
