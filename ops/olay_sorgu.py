#!/usr/bin/env python3
# olay_sorgu.py — state/events.jsonl olay defterinin DuckDB sorgulayıcısı (ozet · son · tip · serbest SELECT)
# `grep | wc -l` zincirlerinin yerine geçer: defteri YERİNDE okur, ara dosya/DB üretmez,
# tek çıktısı stdout'tur. Bozuk JSON satırı atlanır ama SAYILIP stderr'e raporlanır (Yasa 4).
# BİRLEŞİK OKUR (2026-09-03): jsonl + `state/olaylar/AAAA-AA.parquet` arşivi (ops/olay_sikistir.py
# üretir) TEK `olaylar` görünümünde birleşir — parquet'lenmiş ay jsonl'den süzülür, çift sayım yok.
# Serbest `--sql` bir YAZMA MUHAFIZINDAN geçer: DuckDB'nin kendi ayrıştırıcısı tek SELECT olduğunu
# doğrular; COPY/ATTACH/INSTALL/DDL/DML ve `SELECT 1; DROP ...` kaçışı reddedilir. Bağlantı bellek
# içidir, temp_directory boşaltılır, eklenti oto-indirme kapatılır. Muhafız KUM HAVUZU DEĞİLDİR.
# Koşum: .venv/bin/python ops/olay_sorgu.py — meridian İTHAL ETMEZ (obs'a ulaşamaz).
"""ops/olay_sorgu.py — `state/events.jsonl` OLAY DEFTERİNİN DuckDB SORGULAYICISI
(TSK-020 [UYGULA-2] adım 1, 2026-09-01).

NEDEN VAR. Olay defteri 27.887 satır / 9 MB (ölçüm 2026-09-01) ve "son bir haftada hangi olay
kaç kere öttü" sorusu bugüne kadar `grep | wc -l` zincirleriyle soruluyordu: her soru yeni bir
tek-kullanımlık boru hattı, hiçbiri tekrarlanabilir değil. Bu araç defteri SQL yüzeyine açar.

DOĞRUDAN OKUR — ARA ARTEFAKT YOK (YASA 6). DuckDB dosyayı yerinde tarar: ne `.duckdb` dosyası,
ne kopya üretilir. Bağlantı BELLEK İÇİdir. Aracın TEK çıktısı stdout'tur, okuyucusu komutu yazan
operatördür. BU ARAÇ HİÇBİR ŞEY YAZMAZ — parquet arşivini `ops/olay_sikistir.py` üretir
([UYGULA-2] adım 2); bu araç onun OKUYUCUSUdur (Yasa 6: okuyucusuz yazım yok).

BİRLEŞİK OKUMA + ÇİFT SAYIM KURALI (2026-09-03, adım 2). `olaylar` görünümü İKİ kaynağın
birleşimidir: `state/olaylar/*.parquet` (geçmiş aylar) + `state/events.jsonl` (defterin kendisi).
Defter adım 2'de KIRPILMADIĞI için aynı satır İKİ kaynakta birden durabilir. Kural tek cümledir:
**PARQUET KAZANIR** — parquet'te bulunan her AY jsonl tarafından süzülür (`ay NOT IN (...)`).
  · Neden bu yön: tersi ("jsonl kazanır") seçilseydi, defter kırpılmadığı sürece parquet'ten
    HİÇBİR satır gelmezdi; arşiv okunmayan bir dosya olurdu ve Yasa 6'nın okuyucusu SÖZDE kalırdı.
  · Kuralın güvenlik ağı sıkıştırıcıdadır: bir ay parquet'lendikten SONRA o aya satır eklenirse
    `olay_sikistir.py` ikinci koşumda sayım+içerik damgası farkını görür, `.yeni` yazar ve
    KIRMIZI döner (sessizce eskimiş arşiv yok).
  · AY'a atanamayan satır (ts yok/çözülemiyor) ASLA süzülmez — o satırların ayı NULL'dur,
    sıkıştırıcı onları hiç yazmaz, birleşimde jsonl'den gelirler.
  · Geri dönüş yolu: `--yalniz-jsonl` arşivi yok sayar (kırpılmış defterde EKSİK sonuç verir).

AY ANAHTARI UTC'DİR. `ay` sütunu `ts`in UTC ayıdır (`AT TIME ZONE 'UTC'`), `gun`/`zaman`
sütunlarıysa `ts`in YAZILDIĞI hâlidir (TIMESTAMP cast ofseti yok sayar — ölçüldü). Gerçek
defterde ikisi ÇAKIŞIR: 27.887 satırın 27.887'si `+00:00` taşıyor (ölçüm 2026-09-03, 2026-07:
27.273 · 2026-08: 614). Ofsetli bir kaynak eklenirse ayrım görünür hâle gelir; bu yüzden
sütunlar ayrı adlarla durur, biri diğerinden TÜRETİLMEZ.

`read_json_objects`, `read_json_auto` DEĞİL — ÖLÇÜLMÜŞ GEREKÇE. `read_json_auto` bu defterde
tek sütun (`MAP(VARCHAR, JSON)`) veriyor, ama YALNIZCA defterde 235 farklı anahtar olduğu ve
bunun DuckDB'nin `map_inference_threshold` varsayılanını (200) AŞTIĞI için. Anahtar envanteri
200'ün altına düşerse aynı çağrı sessizce N tane GERÇEK sütuna döner ve `json_extract_string(
json, ...)` kullanan her sorgu "Referenced column json not found" ile kırılır. Bu ölçüldü
(4 anahtarlı sentetik dosya: 4 sütun) ve `map_inference_threshold=0` ile PİNLENEMEDİĞİ de
ölçüldü. `read_json_objects` sözleşme gereği her zaman TEK `json` sütunu verir — anahtar
sayısından bağımsız. Şema kararlılığı burada süsleme değil, çivinin dayanağıdır.

YASA 4 — BOZUK SATIR SESSİZCE YUTULMAZ. `ignore_errors=true` ayrıştırılamayan satırı ATMAZ,
yerine NULL satır koyar (ölçüldü) — bu yüzden atlanan satır sayısı TAHMİN değil, SAYIM'dır:
`count(*) FILTER (WHERE json IS NULL)`. Sayı sıfırdan büyükse stderr'e raporlanır. Sıfırsa
hiçbir şey basılmaz: bilgi taşımayan uyarı gürültüdür.

SERBEST SQL YALNIZ SELECT. `--sql` DuckDB'nin KENDİ ayrıştırıcısıyla (`extract_statements`)
sınıflandırılır — regex'le değil. Tek ifade olmalı ve tipi SELECT olmalı; ayrıca ilk jeton
kapısı vardır, çünkü `PRAGMA ...` ayrıştırıcıda SELECT görünüyor (ölçüldü) ama oturum durumunu
DEĞİŞTİREBİLİR. `COPY ... TO` (dosya yazar), `ATTACH` (dış DB açar), DDL/DML reddedilir.

KAPI BİR **YAZMA MUHAFIZIDIR, KUM HAVUZU DEĞİL**: `SELECT * FROM read_csv('/etc/hosts')` gibi
okumalar meşru SELECT'tir ve GEÇER (ölçüldü) — araç zaten operatörün kendi kabuk yetkisiyle
koşuyor, orada `cat` da var. Muhafızın sözü şudur: bu araç üzerinden diske YAZILMAZ ve dış
bağımlılık ÇEKİLMEZ. Bu yüzey bir bota/panoya ya da operatör-dışı bir çağırana bağlanırsa
sözleşme yeniden düşünülmelidir — o zaman okuma yüzeyi de sınırlanmalıdır.

BAĞLANTI SERTLEŞTİRMESİ (ölçüldü, duckdb 1.5.5 varsayılanları): `temp_directory` varsayılan
`.tmp` ve CWD-GÖRELİdir — büyük bir sıralama operatörün bulunduğu dizine sessizce `.tmp/`
döker; boşaltılır. `autoinstall_known_extensions`/`autoload_known_extensions` varsayılan
TRUE'dur — bir sorgu bilinmeyen bir fonksiyona dokunduğunda DuckDB AĞDAN eklenti indirebilir;
ikisi de kapatılır. `TimeZone` varsayılanı MAKİNENİN yerelidir (bu makinede `Europe/Istanbul`,
ölçüldü) — ofsetsiz bir `ts` o dilime göre çözülürdü ve aynı defter iki makinede iki farklı AYA
düşerdi (ölçüldü: naif `2026-03-01T02:00:00` → Istanbul'da `2026-02`, UTC'de `2026-03`);
`UTC`ye sabitlenir. Yerel bir defter okuyucusunun ne diske dökmeye, ne ağa çıkmaya, ne de
makinenin saat diliminden sonuç almaya işi vardır.

SQL YÜZEYİ. `olaylar` görünümü şu sütunları verir — adlar defterin KENDİ sözlüğüdür
(`ts`/`level`/`event`), uydurulmadı:
    ts     VARCHAR  — satırdaki ham `ts` (dokunulmaz)
    zaman  TIMESTAMP— `ts`in çözülmüş hâli; çözülemezse NULL (uydurma yasağı: substr tahmini YOK)
    gun    DATE     — `zaman`ın günü; `zaman` NULL ise NULL
    level  VARCHAR  — satırdaki `level`
    event  VARCHAR  — satırdaki `event`
    ay     VARCHAR  — `ts`in UTC ayı (`AAAA-AA`); çözülemezse NULL. Arşiv bölmesinin anahtarı.
    kaynak VARCHAR  — 'jsonl' | 'parquet'. Satırın NEREDEN geldiği: birleşim sessiz olmasın diye.
    json   JSON     — satırın TAMAMI; 235 alanın hepsi buradan `json_extract_string` ile okunur

KULLANIM:
    python ops/olay_sorgu.py                                   # ozet (olay tipi × gün)
    python ops/olay_sorgu.py --sorgu son --n 30                # son 30 olay
    python ops/olay_sorgu.py --sorgu tip --tip hotstate_down   # tek tipin dökümü
    python ops/olay_sorgu.py --sql "SELECT level, count(*) FROM olaylar GROUP BY 1"
    python ops/olay_sorgu.py --sorgu ozet --json               # satır-JSON (kesme YOK)
    python ops/olay_sorgu.py --dosya /yol/baska.jsonl          # başka defter
    python ops/olay_sorgu.py --yalniz-jsonl                    # arşivi yok say (ham defter)
    python ops/olay_sorgu.py --parquet-dizin /yol/arsiv        # başka arşiv dizini

BEDEL (metin kipi): `detay` sütunu okunur kalsın diye 100 karakterde KESİLİR ve kesik `…` ile
GÖRÜNÜR olur. Kaybedilen hiçbir şey yok değil — geri alma yolu `--json`, orada kesme yapılmaz.

ÇIKIŞ KODU: 0 = sorgu koştu · 2 = kullanım/dosya hatası · 3 = SQL reddedildi (SELECT değil)
           · 4 = sorgu DuckDB'de düştü
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json as _json
import pathlib
import re
import sys
import typing

import duckdb

KOK = pathlib.Path(__file__).resolve().parents[1]
VARSAYILAN_DEFTER = KOK / "state" / "events.jsonl"
#: Arşiv dizini defterin YANINDA durur (state/events.jsonl → state/olaylar/). Sabit bir mutlak
#: yol yazılsaydı `--dosya` ile başka bir deftere bakan koşum SESSİZCE canlı arşivi karıştırırdı.
ARSIV_ALT_DIZIN = "olaylar"

# İlk jeton kapısı: ayrıştırıcı SELECT dese bile yalnız bu jetonlarla BAŞLAYAN sorgu geçer.
# Gerekçe ÖLÇÜLDÜ (duckdb 1.5.5): PRAGMA'lar TEK sınıfa düşmüyor — `PRAGMA enable_profiling`
# StatementType.PRAGMA (tip kapısı yakalar) ama `PRAGMA version` ve `PRAGMA database_list`
# StatementType.SELECT görünüyor; onları YALNIZ bu jeton kapısı durdurur. İkisi de defterle
# ilgisiz introspeksiyon yüzeyidir ve bu araç bir olay sorgulayıcısıdır, DuckDB konsolu değil.
IZINLI_ILK_JETON = {"SELECT", "WITH", "FROM", "TABLE", "VALUES"}

DETAY_TAVAN = 100  # metin kipinde `detay` kesme sınırı; `--json` kesmez


#: Bağlantı sertleştirme ayarları. DEĞERLER ÖLÇÜLDÜ (duckdb 1.5.5 varsayılanları): temp_directory
#: '.tmp' (CWD-göreli — operatörün dizinine döker), iki eklenti bayrağı da True (ağdan indirir).
#: `SET` ifadeleri bağlantı açılır açılmaz, HERHANGİ bir kullanıcı sorgusundan ÖNCE koşar.
#: `TimeZone` 2026-09-03'te eklendi (adım 2): ay anahtarı UTC olmalı; varsayılan makine yerelidir
#: ve ofsetsiz bir `ts` makineye göre başka aya düşerdi (başlıktaki ölçüm).
SERTLESTIRME = (
    "SET temp_directory=''",
    "SET autoinstall_known_extensions=false",
    "SET autoload_known_extensions=false",
    "SET TimeZone='UTC'",
)


def baglanti_kur() -> duckdb.DuckDBPyConnection:
    """Bellek içi bağlantı açar ve `SERTLESTIRME` ayarlarını uygular (Yasa 6 + dış bağımlılık)."""
    con = duckdb.connect()          # BELLEK İÇİ: diske hiçbir DB dosyası yazılmaz
    for s in SERTLESTIRME:
        con.execute(s)
    return con


def sql_metni(yol: pathlib.Path) -> str:
    """Yolu DuckDB dize sabitine çevirir (tek tırnak ikilenir). Yol argv'den gelir; kaçış
    yapılmazsa tırnak içeren bir dizin adı sorguyu bozar."""
    return "'" + str(yol).replace("'", "''") + "'"


def arsiv_dizini(defter: pathlib.Path) -> pathlib.Path:
    """Defterin YANINDAKİ arşiv dizini (state/events.jsonl → state/olaylar/). Sıkıştırıcı da
    okuyucu da BU fonksiyondan türetir — iki yerde yazılsaydı sessizce ayrışırlardı."""
    return defter.parent / ARSIV_ALT_DIZIN


def parquet_dosyalari(dizin: pathlib.Path | None) -> list[pathlib.Path]:
    """Arşiv dizinindeki `*.parquet` dosyaları (adına göre sıralı). Dizin yoksa BOŞ liste —
    hata değil: sıkıştırıcı hiç koşmamış olabilir. `.yeni` uzantılı FARK dosyaları BİLEREK
    dışarıdadır: onlar operatörün kıyaslaması için duran adaylardır, kabul edilmiş arşiv değil."""
    if dizin is None or not dizin.is_dir():
        return []
    return sorted(p for p in dizin.glob("*.parquet") if p.is_file())


def ay_ifadesi(json_ifadesi: str) -> str:
    """`ts`in UTC ayını (`AAAA-AA`) veren SQL ifadesi — çözülemezse NULL (uydurma yasağı:
    substr tahmini YOK). Ay anahtarının TEK kaynağı burasıdır: sıkıştırıcı ve okuyucu aynı
    ifadeyi kullanır, yoksa arşivin bölmesi ile sorgunun süzgeci sessizce ayrışırdı."""
    return (f"strftime(try_cast(json_extract_string({json_ifadesi}, '$.ts') AS TIMESTAMPTZ) "
            "AT TIME ZONE 'UTC', '%Y-%m')")


def _okuma_ifadesi(yol: pathlib.Path) -> str:
    return (f"read_json_objects({sql_metni(yol)}, "
            "format='newline_delimited', ignore_errors=true)")


def jsonl_kaynak_sql(yol: pathlib.Path) -> str:
    """Defterin `(ay, ham)` yüzeyi — arşivin de birleşik görünümün de TEK jsonl kaynağı.

    `ham` satırın JSON metnidir. Ölçüldü (duckdb 1.5.5): `read_json_objects` belgenin metnini
    OLDUĞU GİBİ taşır, `CAST(json AS VARCHAR)` girdideki boşluğu da korur. Yine de sözleşme
    METİN AYNILIĞI değil İÇERİK AYNILIĞIdır: arşivin damgası bu metinden hesaplanır, dolayısıyla
    DuckDB bir gün normalize etmeye başlarsa bedel biçimsel boşluktur, anlam değil."""
    return (f"SELECT {ay_ifadesi('json')} AS ay, CAST(json AS VARCHAR) AS ham "
            f"FROM {_okuma_ifadesi(yol)} WHERE json IS NOT NULL")


def parquet_kaynak_sql(parquetler: list[pathlib.Path]) -> str:
    """Arşivin `(ay, ham)` yüzeyi. Şema jsonl yüzeyiyle AYNIdır: birleşim ancak böyle mümkün."""
    liste = "[" + ", ".join(sql_metni(p) for p in parquetler) + "]"
    return f"SELECT ay, ham FROM read_parquet({liste})"


def ay_damgasi(con: duckdb.DuckDBPyConnection, kaynak_sql: str, ay: str) -> tuple[int, str]:
    """Bir ayın (SATIR SAYISI, İÇERİK DAMGASI) çifti — idempotency kıyasının TEK ölçüsü.

    Damga PARQUET BAYTLARININ değil İÇERİĞİN sha256'sıdır: bayt kıyası DuckDB sürümü
    değiştiğinde (dosyaya gömülü üretici damgası) YANLIŞ KIRMIZI verirdi. Sıralama `ORDER BY
    ham` ile sabitlenir, böylece damga tarama sırasından bağımsızdır; satır sayısı ayrıca
    döner çünkü "aynı içerik, farklı sayı" (yinelenmiş satır) yalnız sayımda görünür."""
    sayi, damga = con.execute(
        f"SELECT count(*), sha256(coalesce(string_agg(ham, chr(10) ORDER BY ham), '')) "
        f"FROM ({kaynak_sql}) AS _k WHERE ay = ?", [ay]).fetchone()
    return int(sayi), str(damga)


def bozuk_sayimi(con: duckdb.DuckDBPyConnection, yol: pathlib.Path) -> int:
    """Ayrıştırılamayan satır SAYISI (tahmin değil sayım — `ignore_errors=true` bozuk satırı
    atmaz, NULL satır koyar: ölçüldü). İki araç da bu tek kaynaktan sayar."""
    return int(con.execute(
        f"SELECT count(*) FILTER (WHERE json IS NULL) FROM {_okuma_ifadesi(yol)}").fetchone()[0])


def bozuk_uyar(bozuk: int, dosya: pathlib.Path, akis=sys.stderr) -> None:
    """Ayrıştırılamayan satır sayısını raporlar (Yasa 4). Sıfırsa hiçbir şey basılmaz:
    bilgi taşımayan uyarı gürültüdür. İki araç da BU fonksiyondan geçer."""
    if bozuk:
        print(f"UYARI: {bozuk} satır JSON olarak ayrıştırılamadı ve atlandı "
              f"(dosya: {dosya}). Bu satırlar sonuçlara GİRMEDİ.", file=akis)


class Kaynak(typing.NamedTuple):
    """`gorunumu_kur`un hükmü: kaç satır bozuktu, hangi arşiv dosyaları okundu, hangi aylar
    jsonl'den SÜZÜLDÜ. Üçü de çağırana döner çünkü üçü de sonucun ANLAMINI değiştirir."""
    bozuk: int
    parquetler: list[pathlib.Path]
    aylar: list[str]
    aysiz_parquet: int


def gorunumu_kur(con: duckdb.DuckDBPyConnection, yol: pathlib.Path,
                 parquet_dizin: pathlib.Path | None = None) -> Kaynak:
    """`olaylar` görünümünü kurar (jsonl + arşiv birleşik) ve `Kaynak` hükmünü döndürür.

    Bozuk satırlar görünümün DIŞINDA bırakılır (`json IS NOT NULL`) ama önce SAYILIR —
    "atlandı" ile "hiç yoktu" bu araçta aynı görünmez (Yasa 4).

    ÇİFT SAYIM KURALI (başlıkta gerekçesi): arşivde bulunan her AY jsonl'den süzülür. Süzgeç
    `ay IS NULL OR ay NOT IN (...)` biçimindedir — `NOT IN` tek başına yazılsaydı ayı NULL olan
    satırlar (ts yok/çözülemiyor) SQL'in üç-değerli mantığı yüzünden SESSİZCE düşerdi."""
    jsonl = jsonl_kaynak_sql(yol)
    bozuk = bozuk_sayimi(con, yol)

    parquetler = parquet_dosyalari(parquet_dizin)
    aylar: list[str] = []
    aysiz_parquet = 0
    if parquetler:
        for ay, adet in con.execute(
                f"SELECT ay, count(*) FROM ({parquet_kaynak_sql(parquetler)}) AS _p "
                "GROUP BY ay ORDER BY 1").fetchall():
            if ay is None:
                aysiz_parquet = int(adet)   # süzgece giremez → çift sayım riski; çağıran UYARIR
            else:
                aylar.append(str(ay))

    if parquetler:
        suzgec = ""
        if aylar:
            suzgec = ("WHERE ay IS NULL OR ay NOT IN ("
                      + ", ".join(sql_metni(a) for a in aylar) + ")")
        birlesik = (f"SELECT ay, ham, 'parquet' AS kaynak FROM ({parquet_kaynak_sql(parquetler)}) AS _p "
                    f"UNION ALL "
                    f"SELECT ay, ham, 'jsonl' AS kaynak FROM ({jsonl}) AS _j {suzgec}")
    else:
        birlesik = f"SELECT ay, ham, 'jsonl' AS kaynak FROM ({jsonl}) AS _j"

    con.execute(f"""
        CREATE VIEW olaylar AS
        SELECT
            json_extract_string(ham, '$.ts')                           AS ts,
            try_cast(json_extract_string(ham, '$.ts') AS TIMESTAMP)    AS zaman,
            CAST(try_cast(json_extract_string(ham, '$.ts') AS TIMESTAMP) AS DATE) AS gun,
            json_extract_string(ham, '$.level')                        AS level,
            json_extract_string(ham, '$.event')                        AS event,
            ay                                                         AS ay,
            kaynak                                                     AS kaynak,
            CAST(ham AS JSON)                                          AS json
        FROM ({birlesik}) AS _b
    """)
    return Kaynak(int(bozuk), parquetler, aylar, aysiz_parquet)


# ---------------------------------------------------------------------------------------------
# Hazır sorgular — sütun ADLARI çıktının sözleşmesidir (`--json` anahtarları da bunlar)
# ---------------------------------------------------------------------------------------------

# Okunur özet: `detail` yoksa `error`, o da yoksa satırın TAMAMI. Hiçbir şey UYDURULMAZ —
# alan yoksa ham satır basılır, "-" ya da boş dize değil.
_DETAY = ("coalesce(json_extract_string(json, '$.detail'), "
          "json_extract_string(json, '$.error'), CAST(json AS VARCHAR))")

SORGULAR = {
    "ozet": (
        "SELECT gun, event AS olay, string_agg(DISTINCT level, ',') AS seviye, "
        "       count(*) AS adet "
        "FROM olaylar GROUP BY gun, event "
        "ORDER BY gun DESC NULLS LAST, adet DESC, olay LIMIT ?"
    ),
    "son": (
        f"SELECT ts, level AS seviye, event AS olay, {_DETAY} AS detay "
        "FROM olaylar ORDER BY zaman DESC NULLS LAST, ts DESC LIMIT ?"
    ),
    "tip": (
        f"SELECT ts, level AS seviye, event AS olay, {_DETAY} AS detay "
        "FROM olaylar WHERE event = ? ORDER BY zaman DESC NULLS LAST, ts DESC LIMIT ?"
    ),
}

VARSAYILAN_N = {"ozet": 50, "son": 20, "tip": 50}


# ---------------------------------------------------------------------------------------------
# SELECT kapısı
# ---------------------------------------------------------------------------------------------

def _bas_yorumlari_at(sql: str) -> str:
    """İlk-jeton kapısı için baştaki boşluk ve yorumları soyar. Yalnız KAPI kararı için
    kullanılır; DuckDB'ye giden metin DEĞİŞTİRİLMEZ."""
    s = sql
    while True:
        yeni = s.lstrip()
        if yeni.startswith("--"):
            _, _, yeni = yeni.partition("\n")
        elif yeni.startswith("/*"):
            _, _, yeni = yeni.partition("*/")
        else:
            return yeni
        s = yeni


def select_kapisi(con: duckdb.DuckDBPyConnection, sql: str) -> str | None:
    """Sorgu tek bir SELECT değilse RED GEREKÇESİNİ döndürür; kabulde None.

    Sınıflandırma DuckDB'nin KENDİ ayrıştırıcısıyla yapılır — regex bir SQL ayrıştırıcısı
    değildir ve `SELECT 1; DROP ...` gibi çok-ifadeli kaçışları güvenilir biçimde ayıramaz."""
    try:
        ifadeler = con.extract_statements(sql)
    except Exception as e:
        # Sinyalli: ayrıştırılamayan sorgu SESSİZCE geçmez, gerekçe çağırana döner (Yasa 4).
        return f"SQL ayrıştırılamadı ({type(e).__name__}): {e}"

    if len(ifadeler) != 1:
        return (f"yalnız TEK bir SELECT ifadesi kabul edilir; {len(ifadeler)} ifade bulundu "
                "(çok-ifadeli sorgu reddedilir)")

    tip = str(ifadeler[0].type).rsplit(".", 1)[-1]
    if tip != "SELECT":
        return f"yalnız SELECT kabul edilir; bu sorgu {tip} sınıfında"

    jeton = re.match(r"([A-Za-z_]+)", _bas_yorumlari_at(sql))
    if jeton is None or jeton.group(1).upper() not in IZINLI_ILK_JETON:
        bulunan = jeton.group(1).upper() if jeton else "(yok)"
        return (f"yalnız SELECT kabul edilir; sorgu {bulunan} ile başlıyor "
                f"(izinli ilk jetonlar: {', '.join(sorted(IZINLI_ILK_JETON))})")
    return None


# ---------------------------------------------------------------------------------------------
# Biçimleme
# ---------------------------------------------------------------------------------------------

def _hucre(v) -> str:
    """Değeri metne çevirir. None BOŞ dizeye çevrilir — `0` ile `bilmiyorum` karışmasın diye
    sayıya DÖNÜŞTÜRÜLMEZ (uydurma yasağı)."""
    if v is None:
        return ""
    if isinstance(v, (_dt.date, _dt.datetime)):
        return v.isoformat()
    return str(v)


def _json_guvenli(v):
    if isinstance(v, (_dt.date, _dt.datetime)):
        return v.isoformat()
    return str(v)


def tablo_bas(basliklar: list[str], satirlar: list[tuple], akis) -> None:
    """Hizalı tablo basar. Sayısal sütunlar sağa, metin sütunları sola yaslanır."""
    hucreler = [[_hucre(v) for v in s] for s in satirlar]
    for r, s in zip(hucreler, satirlar):
        for i, ham in enumerate(s):
            if basliklar[i] == "detay" and len(r[i]) > DETAY_TAVAN:
                r[i] = r[i][:DETAY_TAVAN] + "…"     # bedel: kesik GÖRÜNÜR; tamı `--json`'da
    sayisal = [
        all(isinstance(s[i], (int, float)) or s[i] is None for s in satirlar) and bool(satirlar)
        for i in range(len(basliklar))
    ]
    genis = [max(len(basliklar[i]), *(len(r[i]) for r in hucreler)) if hucreler
             else len(basliklar[i]) for i in range(len(basliklar))]

    def yasla(metin: str, i: int) -> str:
        return metin.rjust(genis[i]) if sayisal[i] else metin.ljust(genis[i])

    print("  ".join(yasla(b, i) for i, b in enumerate(basliklar)).rstrip(), file=akis)
    print("  ".join("-" * genis[i] for i in range(len(basliklar))), file=akis)
    for r in hucreler:
        print("  ".join(yasla(r[i], i) for i in range(len(basliklar))).rstrip(), file=akis)
    if not hucreler:
        print("(0 satır)", file=akis)


def json_bas(basliklar: list[str], satirlar: list[tuple], akis) -> None:
    """Satır-JSON basar — KESME YOK: metin kipinde kısaltılan `detay` burada tamdır."""
    for s in satirlar:
        print(_json.dumps(dict(zip(basliklar, s)), ensure_ascii=False, default=_json_guvenli),
              file=akis)


# ---------------------------------------------------------------------------------------------

def _ayristirici() -> argparse.ArgumentParser:
    a = argparse.ArgumentParser(
        prog="ops/olay_sorgu.py",
        description="state/events.jsonl olay defterini DuckDB ile DOĞRUDAN sorgular.",
        epilog="Serbest sorguda `olaylar` görünümü kullanılır: ts, zaman, gun, level, event, json.",
    )
    a.add_argument("--dosya", type=pathlib.Path, default=VARSAYILAN_DEFTER,
                   help="okunacak jsonl defteri (varsayılan: state/events.jsonl)")
    # default=None BİLEREK: "operatör açıkça verdi mi" ile "varsayılan devrede" ayrımı olmadan
    # `--sql --sorgu son` çelişkisi SESSİZCE yok sayılırdı (`--uygula` vakasının sınıfı).
    a.add_argument("--sorgu", choices=sorted(SORGULAR), default=None,
                   help="hazır sorgu (varsayılan: ozet)")
    a.add_argument("--n", type=int, default=None, help="satır tavanı (sorguya göre varsayılan)")
    a.add_argument("--tip", default=None, help="`--sorgu tip` için olay tipi (event alanı)")
    a.add_argument("--sql", default=None, help="serbest sorgu — YALNIZ tek SELECT")
    a.add_argument("--json", action="store_true", dest="json_kipi",
                   help="satır-JSON bas (kesme yok)")
    # default=None BİLEREK (aynı gerekçe `--sorgu`daki gibi): operatörün AÇIKÇA verdiği dizin ile
    # defterden türetilen varsayılan ayırt edilemezse `--yalniz-jsonl` çelişkisi sessizce yutulur.
    a.add_argument("--parquet-dizin", type=pathlib.Path, default=None, dest="parquet_dizin",
                   help="parquet arşiv dizini (varsayılan: defterin yanındaki `olaylar/`)")
    a.add_argument("--yalniz-jsonl", action="store_true", dest="yalniz_jsonl",
                   help="arşivi YOK SAY, yalnız jsonl defterini oku (kırpılmış defterde EKSİK)")
    return a


def main(argv: list[str] | None = None) -> int:
    args = _ayristirici().parse_args(argv)

    if not args.dosya.exists():
        print(f"HATA: olay defteri bulunamadı: {args.dosya}", file=sys.stderr)
        return 2

    # `--sql` hazır sorgu bayraklarını SESSİZCE yok saymaz: çelişki açık kullanım hatasıdır.
    if args.sql is not None:
        catisan = [ad for ad, deger in
                   (("--sorgu", args.sorgu), ("--tip", args.tip), ("--n", args.n))
                   if deger is not None]
        if catisan:
            print(f"HATA: `--sql` ile birlikte {', '.join(catisan)} kullanılamaz — serbest "
                  "sorguda satır tavanını ve filtreyi SQL'in kendisi taşır (LIMIT/WHERE). "
                  "Bayrak sessizce yok sayılmaz.", file=sys.stderr)
            return 2

    # Çelişki sessizce yutulmaz: "arşivi yok say" ile "şu arşivi oku" aynı anda söylenemez.
    if args.yalniz_jsonl and args.parquet_dizin is not None:
        print("HATA: `--yalniz-jsonl` ile `--parquet-dizin` birlikte kullanılamaz — biri arşivi "
              "yok saymayı, diğeri belirli bir arşivi okumayı söyler. Bayrak sessizce yok "
              "sayılmaz.", file=sys.stderr)
        return 2

    sorgu_adi = args.sorgu or "ozet"
    if args.sql is None and sorgu_adi == "tip" and not args.tip:
        print("HATA: `--sorgu tip` için `--tip <olay_adi>` zorunludur — filtresiz döküm "
              "istiyorsan `--sorgu son` kullan.", file=sys.stderr)
        return 2

    arsiv = None if args.yalniz_jsonl else (args.parquet_dizin or arsiv_dizini(args.dosya))

    con = baglanti_kur()
    try:
        try:
            kaynak = gorunumu_kur(con, args.dosya, arsiv)
        except duckdb.Error as e:
            # Sinyalli: defter okunamadıysa boş tablo basmak YERİNE gerekçeyle düşülür.
            print(f"HATA: defter okunamadı ({args.dosya}): {e}", file=sys.stderr)
            return 2

        bozuk_uyar(int(kaynak.bozuk), args.dosya)

        # Sonucun ANLAMI kaynağa bağlı: birleşik okumada bazı aylar arşivden gelir ve o aylar
        # defterden SÜZÜLÜR. Bunu söylememek, sorguyu sessizce başka bir soruya çevirirdi.
        if kaynak.parquetler:
            print(f"BİLGİ: birleşik okuma — {len(kaynak.parquetler)} parquet dosyası; "
                  f"şu aylar ARŞİVden geldi ve defterden süzüldü: {', '.join(kaynak.aylar)}. "
                  f"Ham defter için `--yalniz-jsonl`.", file=sys.stderr)
        if kaynak.aysiz_parquet:
            print(f"UYARI: arşivde AY'ı boş {kaynak.aysiz_parquet} satır var — bu satırlar "
                  f"defterden süzülemez, ÇİFT SAYILMIŞ olabilirler (arşiv elle mi düzenlendi?).",
                  file=sys.stderr)

        if args.sql is not None:
            gerekce = select_kapisi(con, args.sql)
            if gerekce is not None:
                print(f"HATA: sorgu reddedildi — {gerekce}", file=sys.stderr)
                return 3
            sql, parametreler = args.sql, []
        else:
            sql = SORGULAR[sorgu_adi]
            n = args.n if args.n is not None else VARSAYILAN_N[sorgu_adi]
            parametreler = [args.tip, n] if sorgu_adi == "tip" else [n]

        try:
            imlec = con.execute(sql, parametreler)
            basliklar = [d[0] for d in imlec.description]
            satirlar = imlec.fetchall()
        except duckdb.Error as e:
            # Sinyalli: DuckDB hatası sessizce boş sonuca çevrilmez.
            print(f"HATA: sorgu düştü: {e}", file=sys.stderr)
            return 4

        (json_bas if args.json_kipi else tablo_bas)(basliklar, satirlar, sys.stdout)
        return 0
    finally:
        con.close()


if __name__ == "__main__":
    sys.exit(main())
