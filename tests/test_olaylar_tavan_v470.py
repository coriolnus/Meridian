"""v470 — `meridian/olaylar.py` DuckDB bağlantısının BELLEK/İPLİK TAVANI (TSK-183).

NUMARA SEÇİMİ: `ls tests | grep v470` BOŞ (2026-09-13) — çakışma yok.

ÖLÇÜLEN BOŞLUK (2026-09-13). `meridian/olaylar.py::_SERTLESTIRME` üç ayar taşıyordu
(`temp_directory`, iki eklenti bayrağı) ve `_baglanti_kur()` `duckdb.connect()` varsayılanıyla
koşuyordu: `memory_limit` = sistem RAM'inin ~%80'i, `threads` = çekirdek sayısı, `TimeZone` =
MAKİNENİN yereli. Ölçüm (duckdb 1.5.5, bu makine): '6.3 GiB' / 8 / 'Europe/Istanbul'. Bu bağlantı
CANLI uvicorn işçisinin ipliğinde açılır (`watchdog.integrity_report`, `selfreview.build` ve
`ops/alarm_backlog_digest.py` `tum_olaylar()`u çağırır) — tavansız bir arşiv taraması A1'in
(4 OCPU / 24 GB) RAM'ini ve dört çekirdeğini tüketebilirdi. Kardeşleri ZATEN tavanlıydı:
`ops/olay_sorgu.py::SERTLESTIRME` (`OLAY_SORGU_BELLEK`, 2GB) ve `meridian/sohbet.py::
_sorgu_sinirlari` (`SOHBET_SQL_BELLEK`, 512MB + `threads=1`). Bu dosya ÜÇÜNCÜ kopyanın tavanını
ve üç kopyanın ÇEKİRDEK AYNILIĞINI çiviler.

NE ÇİVİLENİR:
  (a) varsayılan tavan YÜRÜR ve duckdb varsayılanı DEĞİLDİR — değer duckdb'nin KENDİ biçimiyle
      (`current_setting`) ölçülür: "SET koştu" ile "tavan yürüdü" ayrı iddialardır.
  (b) `OLAYLAR_BELLEK` ortam değişkeni tavanı ÇAĞRI ANINDA değiştirir (geri alma yolu).
  (c) `threads` = 1 ve `TimeZone` = UTC.
  (d) BOZUK ortam değeri: `obs.warn` + VARSAYILANA düşüş; istisna YOK, `SystemExit` YOK
      (canlı işçi bir yazım hatası yüzünden düşmemeli) ve tavan SESSİZCE yok OLMAZ ('-2GB'
      duckdb'ce kabul edilir ve tavanı 16383.9 PiB yapardı — sinsi sınıf).
  (e) AYRIŞMA: üç yüzeyin sertleştirme ÇEKİRDEĞİ (temp_directory + iki eklenti bayrağı +
      TimeZone) EŞİT; biçim deseni `ops/olay_sorgu.py::BELLEK_BICIMI` ile AYNEN aynı; üç kopya
      birbirine ADIYLA atıf verir. Kopya kaçınılmazdır (`ops` ithal EDİLEMEZ — obs sızıntısı
      kapısı; `meridian` kendi üstündeki betiği ithal ETMEZ — katman yönü), bu yüzden tek-kaynak
      yasasının "türetme + ayrışma çivisi" istisnası BEYANLI olarak kullanılır.
  (f) BEDEL (Bedel yasası): tavan meşru bir taramayı `duckdb.OutOfMemoryException` ile DÜŞÜRÜR;
      `tum_olaylar` bunu YUTMAZ, çağırana AYNEN yükseltir (Yasa 4) — okuyucuların onu nasıl
      karşıladığı `meridian/olaylar.py` şerhinde ADIYLA yazılıdır ve burada ölçülür.

ÖLÇÜLEN DEĞERLER (duckdb 1.5.5, 2026-09-13 — TAHMİN DEĞİL): duckdb girdide ONLUK birim okur
('1GB' = 10^9 bayt) ama İKİLİ birimle rapor eder. '1GB' → "953.6 MiB", '3GB' → "2.7 GiB",
'512MB' → "488.2 MiB", '2GB' → "1.8 GiB". Tavansız varsayılan bu makinede "6.3 GiB".

GERÇEK DEFTERE DOKUNULMAZ: arşiv okuyan çiviler `sandbox_state` altında kendi parquet'ini yazar.
"""

from __future__ import annotations

import pathlib
import re

import duckdb
import pytest

from meridian import obs, olaylar

KOK = pathlib.Path(__file__).resolve().parents[1]

#: ÖLÇÜLDÜ (duckdb 1.5.5, 2026-09-13): '1GB' girdisi ikili birimle böyle raporlanır.
BEKLENEN_VARSAYILAN_BELLEK = "953.6 MiB"        # `OLAYLAR_BELLEK` verilmediğinde: '1GB'
BEKLENEN_ORTAM_BELLEGI = "2.7 GiB"              # `OLAYLAR_BELLEK=3GB` verildiğinde

#: `tests/test_olay_sorgu_v355.py::BOZUK_TAVANLAR` ile AYNI SINIFLAR (kopya değil, aynı kapının ikinci
#: yüzeyi): birim yok · uydurma birim · işaretli değer · boş dize. '-2GB' listenin EN ÖNEMLİ
#: üyesidir: duckdb onu KABUL EDER ve tavan 16383.9 PiB olur — koruma sessizce kapanırdı.
BOZUK_TAVANLAR = ["2 gigabayt", "2GBB", "GB", "2", "", "512 MB fazlası", "-2GB"]
GECERLI_TAVANLAR = ["1GB", "512MB", "1.5GiB", "2gb", "  2GB  ", "2 GB", "1TB", "256MiB"]

#: ÜÇ YÜZEYİN PAYLAŞTIĞI SERTLEŞTİRME ÇEKİRDEĞİ — bellek/iplik BİLEREK dışarıdadır (onlar
#: yüzeye göre AYRI kararlardır ve beyanları şerhlerde durur).
CEKIRDEK_AYARLAR = ("temp_directory", "autoinstall_known_extensions",
                    "autoload_known_extensions", "TimeZone")


def _ayar(con, ad: str):
    return con.execute(f"SELECT current_setting('{ad}')").fetchone()[0]


def _cekirdek(con) -> dict:
    return {ad: _ayar(con, ad) for ad in CEKIRDEK_AYARLAR}


def _olay_sorgu_modulu():
    """`ops.olay_sorgu` — TESTTE ithal edilir, MOTOR kodunda değil. Betik `meridian`ı import
    etmez (v355 bunu statik + davranışsal olarak çiviler), yani bu ithal obs sızıntısı açmaz."""
    import ops.olay_sorgu as mod
    return mod


# ---------------------------------------------------------------------------------------------
# (a)+(b)+(c) TAVANLAR YÜRÜYOR MU
# ---------------------------------------------------------------------------------------------

def test_bellek_tavani_varsayilan_1GB():
    """Ortam değişkeni verilmediğinde 1GB yürür — ve bu, duckdb'nin RAM'in ~%80'i olan
    varsayılanı DEĞİLDİR. İkinci iddia AYNI KOŞUMDA ölçülür (biçim bir gün değişse bile
    "tavan konmuş" iddiası ayakta kalsın): ham bağlantının değeri farklı olmalıdır."""
    con = olaylar._baglanti_kur()
    try:
        olculen = _ayar(con, "memory_limit")
    finally:
        con.close()
    assert olculen == BEKLENEN_VARSAYILAN_BELLEK, olculen
    ham = duckdb.connect()
    try:
        tavansiz = _ayar(ham, "memory_limit")
    finally:
        ham.close()
    assert olculen != tavansiz, (
        f"tavan duckdb varsayılanıyla AYNI ({olculen}) — `SET memory_limit` yürümemiş olabilir")


def test_bellek_tavani_ORTAM_DEGISKENIYLE_ayarlanir(monkeypatch):
    """`OLAYLAR_BELLEK` tavanı KOD DEĞİŞTİRMEDEN açar/daraltır (geri alma yolu). Ortam ÇAĞRI
    ANINDA okunur: import anında dondurulsaydı canlıda birim dosyasına yazılan değer ancak
    süreç yeniden başlayınca yürürdü ve test tarafı `importlib.reload` gerektirirdi."""
    monkeypatch.setenv(olaylar.BELLEK_ENV_AD, "3GB")
    con = olaylar._baglanti_kur()
    try:
        assert _ayar(con, "memory_limit") == BEKLENEN_ORTAM_BELLEGI
    finally:
        con.close()


def test_iplik_tavani_TEK():
    """`threads=1` — A1 dört çekirdeklidir ve `serve.sh` TEK uvicorn işçisi koşar; bu bağlantı
    o işçinin ipliğinde açılır. `meridian/sohbet.py` ile AYNI gerekçe, AYNI değer."""
    con = olaylar._baglanti_kur()
    try:
        assert int(_ayar(con, "threads")) == 1
    finally:
        con.close()


def test_timezone_UTC():
    """`TimeZone='UTC'` — varsayılan MAKİNENİN yerelidir (bu makinede 'Europe/Istanbul',
    ölçüldü). Bugün bu bağlantı SQL tarafında hiçbir `ts`i aya çevirmiyor (`SELECT ay, ham FROM
    read_parquet(...)`, iki sütun da VARCHAR) — yani ayar DAVRANIŞI bugün değiştirmez; çivi
    ÇEKİRDEK AYNILIĞINI korur: üç bağlantının üçü de aynı saat diliminde konuşmalı, yoksa
    yarın SQL'e taşınacak bir ay süzgeci iki makinede iki farklı ay verir."""
    con = olaylar._baglanti_kur()
    try:
        assert _ayar(con, "TimeZone") == "UTC"
    finally:
        con.close()


# ---------------------------------------------------------------------------------------------
# (d) BOZUK ORTAM DEĞERİ — CANLI İŞÇİ DÜŞMEZ, TAVAN DA SESSİZCE YOK OLMAZ
# ---------------------------------------------------------------------------------------------

@pytest.fixture
def warn_kaydi(monkeypatch):
    """`obs.warn` çağrılarını yakalar — çivi deftere YAZMADAN uyarıyı ölçer."""
    kayit = []
    monkeypatch.setattr(obs, "warn", lambda event, **f: kayit.append((event, f)) or {})
    return kayit


@pytest.mark.parametrize("bozuk", BOZUK_TAVANLAR)
def test_BOZUK_ortam_degeri_UYARIR_ve_VARSAYILANA_duser(monkeypatch, warn_kaydi, bozuk):
    """Bozuk `OLAYLAR_BELLEK`: (1) istisna YOK — bu kod CANLI API işçisinin ipliğinde koşar ve
    bir ortam değişkeni yazım hatası `tum_olaylar`ı düşürmemeli; (2) tavan VARSAYILANA düşer,
    SINIRSIZA değil (uydurma yasağı: düşüşün kendisi beyanlıdır); (3) `obs.warn` ADI, VERİLEN
    DEĞERİ ve BEKLENEN BİÇİMİ taşır (Yasa 4: sessiz yutma yok)."""
    monkeypatch.setenv(olaylar.BELLEK_ENV_AD, bozuk)
    con = olaylar._baglanti_kur()
    try:
        assert _ayar(con, "memory_limit") == BEKLENEN_VARSAYILAN_BELLEK
    finally:
        con.close()
    assert len(warn_kaydi) == 1, warn_kaydi
    event, alanlar = warn_kaydi[0]
    assert event == "olaylar_bellek_tavani_bicimsiz", event
    assert alanlar.get("deger") == bozuk, alanlar
    assert olaylar.BELLEK_VARSAYILAN in str(alanlar.get("beklenen", "")) or \
        "GB" in str(alanlar.get("beklenen", "")), alanlar
    assert olaylar.BELLEK_ENV_AD in " ".join(str(v) for v in alanlar.values()), alanlar


def test_ISARETLI_deger_tavani_SESSIZCE_yok_etmez(monkeypatch, warn_kaydi):
    """SİNSİ SINIF, AYRI ÇİVİ: '-2GB' duckdb'ce KABUL EDİLİR ve tavanı 16383.9 PiB yapar —
    kod koşar, hiçbir şey ötmez, koruma KAPANMIŞTIR. Kapı bunu tutmazsa tavan bir daha hiç
    ölçülmez. (Ölçüm v355'te yapıldı; burada aynı sınıf ÜÇÜNCÜ yüzey için çivilenir.)"""
    monkeypatch.setenv(olaylar.BELLEK_ENV_AD, "-2GB")
    con = olaylar._baglanti_kur()
    try:
        olculen = _ayar(con, "memory_limit")
    finally:
        con.close()
    assert olculen == BEKLENEN_VARSAYILAN_BELLEK, olculen
    assert "PiB" not in olculen, f"tavan sessizce yok olmuş: {olculen}"
    assert warn_kaydi and warn_kaydi[0][0] == "olaylar_bellek_tavani_bicimsiz"


@pytest.mark.parametrize("gecerli", GECERLI_TAVANLAR)
def test_GECERLI_bicimler_UYARMADAN_gecer(monkeypatch, warn_kaydi, gecerli):
    """KAPININ BEDELİ ÖLÇÜLÜR (Bedel yasası): doğrulama meşru bir değeri reddederse kazanılan
    teşhis değil, kaybedilen tavanın kendisidir. Ondalık, küçük harf, iç/dış boşluk ve yedi
    birimin hepsi GEÇER — ve duckdb de kabul eder (bağlantı açılır)."""
    monkeypatch.setenv(olaylar.BELLEK_ENV_AD, gecerli)
    con = olaylar._baglanti_kur()
    try:
        assert _ayar(con, "memory_limit")            # duckdb değeri kabul etti
    finally:
        con.close()
    assert warn_kaydi == [], f"meşru değer reddedildi: {gecerli!r} → {warn_kaydi}"


def test_bozuk_deger_SystemExit_ATMAZ(monkeypatch, warn_kaydi):
    """SÖZLEŞME: bu KÜTÜPHANE katmanıdır. `ops/olay_sorgu.py` emsali (v355): süreç öldüren kapı
    YALNIZ CLI'nındır. Burada süreç öldürmek bir yana, istisna bile atılmaz — `tum_olaylar`
    canlı teşhis yüzeyinin okuma yoludur ve bir env yazım hatası onu kapatmamalı."""
    monkeypatch.setenv(olaylar.BELLEK_ENV_AD, "2 gigabayt")
    con = olaylar._baglanti_kur()            # ← atarsa çivi burada kırmızı
    con.close()
    assert warn_kaydi, "bozuk değer sessizce yutuldu — uyarı yok"


# ---------------------------------------------------------------------------------------------
# (e) AYRIŞMA ÇİVİLERİ — ÜÇ KOPYA, TEK ÇEKİRDEK
# ---------------------------------------------------------------------------------------------

def test_bicim_deseni_olay_sorgu_ile_AYNEN_ESITTIR():
    """Biçim doğrulaması İKİ DOSYADA ayrı ayrı durur (ithal edilemez: `meridian` kendi üstündeki
    `ops/` betiğini import ETMEZ, `ops` da `meridian`ı — iki yönlü kapı). Kopya kaçınılmazsa
    ayrışma ÖLÇÜLÜR: desen metni ve bayrakları BİREBİR eşit olmalı. Biri gevşerse (ör. `-`
    işaretine izin verilirse) bu çivi kırmızı olur."""
    mod = _olay_sorgu_modulu()
    assert olaylar.BELLEK_BICIMI.pattern == mod.BELLEK_BICIMI.pattern, (
        f"biçim deseni AYRIŞTI:\n  olaylar   : {olaylar.BELLEK_BICIMI.pattern!r}\n"
        f"  olay_sorgu: {mod.BELLEK_BICIMI.pattern!r}")
    assert olaylar.BELLEK_BICIMI.flags == mod.BELLEK_BICIMI.flags
    assert olaylar.BELLEK_BICIMI.flags & re.IGNORECASE


def test_sertlestirme_CEKIRDEGI_UC_YUZEYDE_ESIT():
    """DAVRANIŞSAL ayrışma çivisi: üç bağlantı AÇILIR ve çekirdek ayarlar `current_setting` ile
    okunur (kaynak metni değil, YÜRÜYEN değer). Üçüncü yüzey `meridian/sohbet.py`nin yoludur:
    bağlantıyı `ops.olay_sorgu.baglanti_kur()`dan alır, üstüne KENDİ bellek/iplik tavanını
    (`_sorgu_sinirlari`) uygular — o daraltma ÇEKİRDEĞE DOKUNMAMALIDIR."""
    from meridian import sohbet
    mod = _olay_sorgu_modulu()
    a = olaylar._baglanti_kur()
    b = mod.baglanti_kur()
    c = mod.baglanti_kur()
    try:
        sohbet._sorgu_sinirlari(c)
        cek_a, cek_b, cek_c = _cekirdek(a), _cekirdek(b), _cekirdek(c)
    finally:
        a.close(); b.close(); c.close()
    assert cek_a == cek_b, f"olaylar ↔ olay_sorgu ayrıştı:\n  {cek_a}\n  {cek_b}"
    assert cek_b == cek_c, f"olay_sorgu ↔ sohbet ayrıştı:\n  {cek_b}\n  {cek_c}"
    assert cek_a["TimeZone"] == "UTC" and cek_a["temp_directory"] == ""
    assert cek_a["autoinstall_known_extensions"] in (False, "false")
    assert cek_a["autoload_known_extensions"] in (False, "false")


def test_UC_KOPYA_birbirine_ADIYLA_atif_verir():
    """TEK-KAYNAK İSTİSNASI BEYANLIDIR. Üç tavan bilerek AYRIDIR (canlı defter okuması / elle
    koşan CLI / canlı sohbet ipliği) — ama ayrılık BEYANSIZ kalırsa bir gün "unutulmuş kopya"
    sanılıp biri silinir. Her dosya diğer ikisini ADIYLA anmalı."""
    olaylar_kaynak = (KOK / "meridian" / "olaylar.py").read_text(encoding="utf-8")
    sorgu_kaynak = (KOK / "ops" / "olay_sorgu.py").read_text(encoding="utf-8")
    sohbet_kaynak = (KOK / "meridian" / "sohbet.py").read_text(encoding="utf-8")
    for ad in ("OLAY_SORGU_BELLEK", "SOHBET_SQL_BELLEK"):
        assert ad in olaylar_kaynak, f"olaylar.py kardeş tavana atıf vermiyor: {ad}"
    assert "OLAYLAR_BELLEK" in sorgu_kaynak, "olay_sorgu.py üçüncü kopyayı beyan etmiyor"
    assert "OLAYLAR_BELLEK" in sohbet_kaynak, "sohbet.py üçüncü kopyayı beyan etmiyor"
    assert "import ops" not in olaylar_kaynak and "from ops" not in olaylar_kaynak, (
        "beyan ŞERHLE yapılır, İTHALLE değil: motor kendi üstündeki betiği import etmez")


# ---------------------------------------------------------------------------------------------
# (f) BEDEL — TAVAN GERÇEKTEN DÜŞÜRÜR VE DÜŞÜŞ GÖRÜNÜRDÜR
# ---------------------------------------------------------------------------------------------

def test_bedel_serhi_OOM_SINIFINI_ve_OKUYUCULARI_ADIYLA_tasir():
    """BEDEL YASASI'nın belge bacağı. Tavan bir kazanç değil bir TAKASTIR: RAM'e sığmayan meşru
    bir tarama artık `OutOfMemoryException` ile DÜŞER (`temp_directory` boş olduğu için diske
    taşma yolu da kapalıdır). Bedel şerhte ADIYLA yazılmazsa bir gün "tavan bedava" sanılır;
    okuyucuların bu istisnayı NASIL karşıladığı da ölçülmüş olmalı, varsayılmış değil."""
    kaynak = (KOK / "meridian" / "olaylar.py").read_text(encoding="utf-8")
    for beyan in ("OutOfMemoryException", "watchdog.integrity_report", "selfreview",
                  "alarm_backlog_digest", "OLAYLAR_BELLEK=4GB"):
        assert beyan in kaynak, f"bedel/okuyucu beyanı eksik: {beyan}"


def test_baglanti_ARIZASI_tum_olaylar_tarafindan_YUTULMAZ(sandbox_state, monkeypatch):
    """YASA 4, DAVRANIŞSAL. Tavan aşıldığında DuckDB `OutOfMemoryException` atar; `tum_olaylar`
    bunu YUTUP yarım liste döndürmemelidir — yarım bir defter "tüm tarih" iddiasını sessizce
    YALANA çevirir (modül başlığındaki sözleşme). İstisna çağırana AYNEN çıkar; okuyucuların
    üçünün de onu nasıl gördüğü şerhte yazılıdır.

    OOM gerçek bir arşivle üretilmez (gigabaytlık parquet gerekirdi): bağlantı kurucu ölçülen
    İSTİSNA SINIFINI atar — ölçülen sınıf, uydurma değil (`_duckdb.OutOfMemoryException`)."""
    arsiv = sandbox_state / "olaylar"
    arsiv.mkdir(parents=True, exist_ok=True)
    kur = duckdb.connect()
    try:
        kur.execute(
            "COPY (SELECT '2026-01' AS ay, '{\"ts\": \"2026-01-02T00:00:00+00:00\"}' AS ham) "
            f"TO '{arsiv / 'olaylar-2026-01.parquet'}' (FORMAT PARQUET)")
    finally:
        kur.close()
    assert olaylar.tum_olaylar(), "ön koşul: arşiv okunabiliyor olmalı (çivi boşa ötmesin)"

    def _patlat():
        raise duckdb.OutOfMemoryException("Out of Memory Error: could not allocate block")

    monkeypatch.setattr(olaylar, "_baglanti_kur", _patlat)
    with pytest.raises(duckdb.OutOfMemoryException):
        olaylar.tum_olaylar()
