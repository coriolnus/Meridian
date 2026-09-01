#!/usr/bin/env python3
# olay_sorgu.py — state/events.jsonl olay defterinin DuckDB sorgulayıcısı (ozet · son · tip · serbest SELECT)
# `grep | wc -l` zincirlerinin yerine geçer: defteri YERİNDE okur, ara dosya/DB/parquet üretmez,
# tek çıktısı stdout'tur. Bozuk JSON satırı atlanır ama SAYILIP stderr'e raporlanır (Yasa 4).
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
ne parquet, ne kopya üretilir. Bağlantı BELLEK İÇİdir. Aracın TEK çıktısı stdout'tur, okuyucusu
komutu yazan operatördür. (Parquet sıkıştırma [UYGULA-2] adım 2'dir — burada YOK.)

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
ikisi de kapatılır. Yerel bir defter okuyucusunun ne diske dökmeye ne ağa çıkmaya işi vardır.

SQL YÜZEYİ. `olaylar` görünümü şu sütunları verir — adlar defterin KENDİ sözlüğüdür
(`ts`/`level`/`event`), uydurulmadı:
    ts     VARCHAR  — satırdaki ham `ts` (dokunulmaz)
    zaman  TIMESTAMP— `ts`in çözülmüş hâli; çözülemezse NULL (uydurma yasağı: substr tahmini YOK)
    gun    DATE     — `zaman`ın günü; `zaman` NULL ise NULL
    level  VARCHAR  — satırdaki `level`
    event  VARCHAR  — satırdaki `event`
    json   JSON     — satırın TAMAMI; 235 alanın hepsi buradan `json_extract_string` ile okunur

KULLANIM:
    python ops/olay_sorgu.py                                   # ozet (olay tipi × gün)
    python ops/olay_sorgu.py --sorgu son --n 30                # son 30 olay
    python ops/olay_sorgu.py --sorgu tip --tip hotstate_down   # tek tipin dökümü
    python ops/olay_sorgu.py --sql "SELECT level, count(*) FROM olaylar GROUP BY 1"
    python ops/olay_sorgu.py --sorgu ozet --json               # satır-JSON (kesme YOK)
    python ops/olay_sorgu.py --dosya /yol/baska.jsonl          # başka defter

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

import duckdb

KOK = pathlib.Path(__file__).resolve().parents[1]
VARSAYILAN_DEFTER = KOK / "state" / "events.jsonl"

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
SERTLESTIRME = (
    "SET temp_directory=''",
    "SET autoinstall_known_extensions=false",
    "SET autoload_known_extensions=false",
)


def baglanti_kur() -> duckdb.DuckDBPyConnection:
    """Bellek içi bağlantı açar ve `SERTLESTIRME` ayarlarını uygular (Yasa 6 + dış bağımlılık)."""
    con = duckdb.connect()          # BELLEK İÇİ: diske hiçbir DB dosyası yazılmaz
    for s in SERTLESTIRME:
        con.execute(s)
    return con


def _sql_metni(yol: pathlib.Path) -> str:
    """Yolu DuckDB dize sabitine çevirir (tek tırnak ikilenir). Yol argv'den gelir; kaçış
    yapılmazsa tırnak içeren bir dizin adı sorguyu bozar."""
    return "'" + str(yol).replace("'", "''") + "'"


def gorunumu_kur(con: duckdb.DuckDBPyConnection, yol: pathlib.Path) -> int:
    """`olaylar` görünümünü kurar ve AYRIŞTIRILAMAYAN SATIR SAYISINI döndürür (Yasa 4).

    Bozuk satırlar görünümün DIŞINDA bırakılır (`json IS NOT NULL`) ama önce SAYILIR —
    "atlandı" ile "hiç yoktu" bu araçta aynı görünmez."""
    kaynak = (
        f"read_json_objects({_sql_metni(yol)}, "
        "format='newline_delimited', ignore_errors=true)"
    )
    bozuk = con.execute(
        f"SELECT count(*) FILTER (WHERE json IS NULL) FROM {kaynak}"
    ).fetchone()[0]

    con.execute(f"""
        CREATE VIEW olaylar AS
        SELECT
            json_extract_string(json, '$.ts')                           AS ts,
            try_cast(json_extract_string(json, '$.ts') AS TIMESTAMP)    AS zaman,
            CAST(try_cast(json_extract_string(json, '$.ts') AS TIMESTAMP) AS DATE) AS gun,
            json_extract_string(json, '$.level')                        AS level,
            json_extract_string(json, '$.event')                        AS event,
            json                                                        AS json
        FROM {kaynak}
        WHERE json IS NOT NULL
    """)
    return int(bozuk)


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

    sorgu_adi = args.sorgu or "ozet"
    if args.sql is None and sorgu_adi == "tip" and not args.tip:
        print("HATA: `--sorgu tip` için `--tip <olay_adi>` zorunludur — filtresiz döküm "
              "istiyorsan `--sorgu son` kullan.", file=sys.stderr)
        return 2

    con = baglanti_kur()
    try:
        try:
            bozuk = gorunumu_kur(con, args.dosya)
        except duckdb.Error as e:
            # Sinyalli: defter okunamadıysa boş tablo basmak YERİNE gerekçeyle düşülür.
            print(f"HATA: defter okunamadı ({args.dosya}): {e}", file=sys.stderr)
            return 2

        if bozuk:
            print(f"UYARI: {bozuk} satır JSON olarak ayrıştırılamadı ve atlandı "
                  f"(dosya: {args.dosya}). Bu satırlar sonuçlara GİRMEDİ.", file=sys.stderr)

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
