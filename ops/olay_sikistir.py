#!/usr/bin/env python3
# olay_sikistir.py — state/events.jsonl olay defterinin GEÇMİŞ AYLARINI parquet'e sıkıştırır
# (state/olaylar/AAAA-AA.parquet). Cari ay YAZILMAZ, defter KIRPILMAZ (yalnız sıkıştırır).
# Idempotent: ay dosyası varsa satır sayısı + içerik damgası kıyaslanır — aynıysa atlanır,
# FARKLIYSA `.yeni` yazılır ve rc=3 döner (sessiz üzerine yazma YOK). Bozuk JSON satırı ve
# AY'a atanamayan satır SAYILIP stderr'e raporlanır (Yasa 4). Arşivin OKUYUCUSU
# ops/olay_sorgu.py'dır (Yasa 6) — birleşik okur, parquet'lenen ay defterden süzülür.
# Koşum: .venv/bin/python ops/olay_sikistir.py --kuru — meridian İTHAL ETMEZ (obs'a ulaşamaz).
"""ops/olay_sikistir.py — OLAY DEFTERİNİN AYLIK PARQUET ARŞİVİ
(TSK-020 [UYGULA-2] adım 2, 2026-09-03).

NEDEN VAR. Defter 27.887 satır / 9 MB (ölçüm 2026-09-01) ve satır satır büyüyor; ölçülen ay
dağılımı 2026-07: 27.273 · 2026-08: 614 (2026-09-03). Her sorgu bugün 9 MB metni baştan
ayrıştırıyor. Kapanmış aylar bir daha DEĞİŞMEZ — onları sütunlu, sıkıştırılmış bir biçimde
dondurmak hem taramayı ucuzlatır hem de defterin ileride kırpılabilmesinin ÖN KOŞULUDUR.

ÜÇ ŞEYİ YAPMAZ — ve bunlar kapsam kararıdır, eksiklik değil:
  1. DEFTERİ KIRPMAZ. Kırpma AYRI bir karardır (adım 3): bugün defterin okuyucuları
     (`obs.recent`, pano, `ops/olay_sorgu.py`) hâlâ jsonl'e bakıyor. Bedel yasası: kazanç
     (sıkıştırma) ölçülüyor, bedel (okuyucuların ne kaybettiği) ölçülmeden kırpma yapılmaz.
  2. CARİ AYI YAZMAZ. Hâlâ yazılmakta olan bir ay dondurulamaz — dondurulsaydı arşiv daha
     doğduğu gün eskirdi ve her koşum FARK verirdi.
  3. SESSİZCE ÜZERİNE YAZMAZ. Var olan bir ay dosyası ancak İÇERİĞİ AYNIYSA "atlandı" olur.
     Farklıysa yenisi `AAAA-AA.parquet.yeni` adıyla YANINA yazılır, eskisine DOKUNULMAZ ve
     araç KIRMIZI (rc=3) döner: kıyas operatörün, karar operatörün.

AY ANAHTARI UTC'DİR — `ts` alanının UTC ayı (`ops/olay_sorgu.py::ay_ifadesi`, tek kaynak).
Ölçüldü (duckdb 1.5.5): `TimeZone` varsayılanı makinenin yerelidir ve ofsetsiz bir `ts` o
dilime göre çözülür; sertleştirme onu UTC'ye sabitler, yoksa aynı defter iki makinede iki
farklı aya bölünürdü. `ts`i olmayan ya da çözülemeyen satırın ayı NULL'dur: UYDURULMAZ,
sıkıştırılmaz, defterde kalır ve SAYILARAK raporlanır (uydurma yasağı + Yasa 4).

ARŞİVİN ŞEKLİ. İki sütun: `ay VARCHAR` + `ham VARCHAR` (satırın JSON metni). Neden yapısal
sütunlar değil: defterde 235 farklı anahtar var (ölçüm 2026-09-01) ve yapısal bir şema
seçilseydi arşiv o günkü anahtar kümesini dondururdu — yarın eklenen bir alan eski arşivde
GÖRÜNMEZ olurdu. `ham` ile arşiv defterin sadık kopyasıdır ve okuyucu bugünkü sorgu yüzeyini
`ham`dan AYNI ifadelerle türetir (tek-kaynak). BEDEL: sütunlu sıkıştırmanın alan-bazlı kazancı
alınmaz; kazanç yalnız ZSTD + tek sütunlu tekrar bastırmasıdır. `ay` sütunu bilerek YEDEKLİdir
(dosya adı da onu söyler): okuyucunun süzgeci dosya ADINA değil İÇERİĞE bakar, böylece yanlış
adlandırılmış bir dosya çift sayıma yol açamaz.

IDEMPOTENCY KIYASI = SATIR SAYISI + İÇERİK DAMGASI (`ops/olay_sorgu.py::ay_damgasi`).
Parquet BAYTLARI kıyaslanmaz: dosyaya gömülü üretici damgası DuckDB sürümüyle değişir ve
sürüm yükseltmesi YANLIŞ KIRMIZI verirdi. Damga `sha256(string_agg(ham ORDER BY ham))`dır —
tarama sırasından bağımsız; satır sayısı ayrıca kıyaslanır çünkü yinelenmiş satır yalnız
sayımda görünür.

KULLANIM:
    python ops/olay_sikistir.py --kuru            # ne yapacağını söyler, HİÇBİR ŞEY yazmaz
    python ops/olay_sikistir.py                   # tüm geçmiş ayları yaz
    python ops/olay_sikistir.py --ay 2026-07      # tek ay
    python ops/olay_sikistir.py --json            # satır-JSON çıktı
    python ops/olay_sikistir.py --dosya /yol/x.jsonl --hedef /yol/arsiv

ÇIKIŞ KODU: 0 = koştu (yazıldı/atlandı) · 2 = kullanım/dosya hatası · 3 = FARK bulundu
           (`.yeni` yazıldı, eskisi duruyor) · 4 = DuckDB'de düştü
"""

from __future__ import annotations

import argparse
import datetime as _dt
import pathlib
import re
import sys

import duckdb

# Sertleştirme, ay ifadesi, kaynak SQL'leri ve damga TEK KAYNAKTAN gelir: kopyalansaydı bu iki
# araç sessizce ayrışırdı (biri UTC'ye göre bölerken diğeri yerel saate göre sorabilirdi).
# Betik olarak koşulduğunda `sys.path[0]` bu dosyanın dizinidir (ops/), bu yüzden düz import
# yeter — `sys.path` ELLE genişletilmez (o, depo kökünü ve `meridian`ı import yoluna açardı).
import olay_sorgu

AY_DESENI = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")

DURUM_YAZILDI = "yazıldı"
DURUM_YAZILACAK = "yazılacak"     # yalnız `--kuru`
DURUM_ATLANDI = "atlandı"
DURUM_FARK = "FARK"

BASLIKLAR = ["ay", "satir", "bayt", "durum", "dosya"]


def cari_ay(simdi: _dt.datetime | None = None) -> str:
    """İçinde bulunduğumuz UTC ayı. Yerel saat KULLANILMAZ: ay anahtarı UTC olduğu için
    "cari" tanımının da UTC olması gerekir, yoksa ayın ilk/son saatlerinde araç kendi
    anahtarıyla çelişirdi."""
    return (simdi or _dt.datetime.now(_dt.timezone.utc)).strftime("%Y-%m")


def _yeni_yolu(hedef_dosya: pathlib.Path) -> pathlib.Path:
    """`AAAA-AA.parquet` → `AAAA-AA.parquet.yeni` (uzantı DEĞİŞTİRİLMEZ, EKLENİR: `.yeni`
    dosyası arşiv dizininde `*.parquet` taramasına da girmemelidir)."""
    return hedef_dosya.with_name(hedef_dosya.name + ".yeni")


def ay_yaz(con: duckdb.DuckDBPyConnection, kaynak_sql: str, ay: str,
           hedef_dosya: pathlib.Path) -> int:
    """Bir ayı parquet olarak yazar ve DOSYA BOYUTUNU döndürür.

    Sıralama KRONOLOJİKtir (`ts`, sonra `ham`): arşiv insan gözüyle de okunabilir kalsın diye.
    Eşitlikte `ham` devreye girer — sıralama deterministik olmazsa aynı içerik iki farklı
    dosya üretirdi (kıyas içerik damgasıyla yapıldığı için bu bir doğruluk sorunu değil,
    ama arşivin tekrarlanabilirliği ucuza alınan bir özelliktir)."""
    hedef_dosya.parent.mkdir(parents=True, exist_ok=True)
    con.execute(
        f"COPY (SELECT ay, ham FROM ({kaynak_sql}) AS _k "
        f"WHERE ay = {olay_sorgu.sql_metni(ay)} "
        f"ORDER BY try_cast(json_extract_string(ham, '$.ts') AS TIMESTAMP), ham) "
        f"TO {olay_sorgu.sql_metni(hedef_dosya)} (FORMAT PARQUET, COMPRESSION ZSTD)")
    return hedef_dosya.stat().st_size


def ay_isle(con: duckdb.DuckDBPyConnection, kaynak_sql: str, ay: str,
            hedef_dosya: pathlib.Path, kuru: bool) -> tuple[dict, str | None]:
    """Tek ayın kararını verir → (çıktı satırı, stderr'e yazılacak gerekçe | None).

    Karar üç dallıdır: dosya yok → yaz · dosya var ve içerik AYNI → atla · dosya var ve içerik
    FARKLI → `.yeni` (kuru koşumda yazmadan) + gerekçe."""
    sayi, damga = olay_sorgu.ay_damgasi(con, kaynak_sql, ay)

    if not hedef_dosya.exists():
        if kuru:
            # bayt UYDURULMAZ: yazılmamış dosyanın boyutu ÖLÇÜLEMEZ (uydurma yasağı → None).
            return {"ay": ay, "satir": sayi, "bayt": None, "durum": DURUM_YAZILACAK,
                    "dosya": str(hedef_dosya)}, None
        bayt = ay_yaz(con, kaynak_sql, ay, hedef_dosya)
        return {"ay": ay, "satir": sayi, "bayt": bayt, "durum": DURUM_YAZILDI,
                "dosya": str(hedef_dosya)}, None

    a_sayi, a_damga = olay_sorgu.ay_damgasi(
        con, olay_sorgu.parquet_kaynak_sql([hedef_dosya]), ay)
    if (sayi, damga) == (a_sayi, a_damga):
        return {"ay": ay, "satir": sayi, "bayt": hedef_dosya.stat().st_size,
                "durum": DURUM_ATLANDI, "dosya": str(hedef_dosya)}, None

    yeni = _yeni_yolu(hedef_dosya)
    gerekce = (f"FARK: {ay} — defterde {sayi} satır (damga {damga[:12]}…), arşivde {a_sayi} "
               f"satır (damga {a_damga[:12]}…). Var olan dosyaya DOKUNULMADI")
    if kuru:
        return {"ay": ay, "satir": sayi, "bayt": None, "durum": DURUM_FARK,
                "dosya": str(yeni)}, gerekce + f"; kuru koşum — `{yeni.name}` YAZILMADI."
    bayt = ay_yaz(con, kaynak_sql, ay, yeni)
    return ({"ay": ay, "satir": sayi, "bayt": bayt, "durum": DURUM_FARK, "dosya": str(yeni)},
            gerekce + f"; aday `{yeni.name}` olarak yazıldı — kıyasla ve karar ver.")


def _ayristirici() -> argparse.ArgumentParser:
    a = argparse.ArgumentParser(
        prog="ops/olay_sikistir.py",
        description="Olay defterinin GEÇMİŞ aylarını `AAAA-AA.parquet` olarak arşivler "
                    "(cari ay hariç; defter KIRPILMAZ).",
        epilog="Arşivin okuyucusu: ops/olay_sorgu.py (jsonl + parquet birleşik okur).",
    )
    a.add_argument("--dosya", type=pathlib.Path, default=olay_sorgu.VARSAYILAN_DEFTER,
                   help="okunacak jsonl defteri (varsayılan: state/events.jsonl)")
    a.add_argument("--hedef", type=pathlib.Path, default=None,
                   help="arşiv dizini (varsayılan: defterin yanındaki `olaylar/`)")
    a.add_argument("--ay", default=None, help="yalnız bu ayı sıkıştır (AAAA-AA)")
    a.add_argument("--kuru", action="store_true",
                   help="HİÇBİR ŞEY yazma, ne yapacağını söyle")
    a.add_argument("--json", action="store_true", dest="json_kipi",
                   help="satır-JSON bas")
    return a


def main(argv: list[str] | None = None) -> int:
    args = _ayristirici().parse_args(argv)

    if not args.dosya.exists():
        print(f"HATA: olay defteri bulunamadı: {args.dosya}", file=sys.stderr)
        return 2

    simdiki = cari_ay()
    if args.ay is not None:
        if not AY_DESENI.match(args.ay):
            print(f"HATA: `--ay` biçimi AAAA-AA olmalı (örn. 2026-07); verilen: {args.ay!r}",
                  file=sys.stderr)
            return 2
        if args.ay >= simdiki:
            print(f"HATA: {args.ay} cari ay ({simdiki}) ya da sonrası — hâlâ yazılmakta olan "
                  "bir ay dondurulamaz; arşivlenen ay bir daha DEĞİŞMEMELİDİR.",
                  file=sys.stderr)
            return 2

    hedef = args.hedef or olay_sorgu.arsiv_dizini(args.dosya)

    con = olay_sorgu.baglanti_kur()
    try:
        kaynak_sql = olay_sorgu.jsonl_kaynak_sql(args.dosya)
        try:
            olay_sorgu.bozuk_uyar(olay_sorgu.bozuk_sayimi(con, args.dosya), args.dosya)
            ay_satirlari = con.execute(
                f"SELECT ay, count(*) FROM ({kaynak_sql}) AS _k GROUP BY ay ORDER BY 1"
            ).fetchall()
        except duckdb.Error as e:
            # Sinyalli: defter okunamadıysa "sıkıştıracak ay yok" demek YERİNE gerekçeyle düşülür.
            print(f"HATA: defter okunamadı ({args.dosya}): {e}", file=sys.stderr)
            return 2

        aysiz = sum(int(n) for ay, n in ay_satirlari if ay is None)
        if aysiz:
            print(f"UYARI: {aysiz} satır bir AY'a atanamadı (`ts` yok ya da çözülemiyor) ve "
                  f"SIKIŞTIRILMADI — defterde kalıyor, arşive girmiyor (dosya: {args.dosya}).",
                  file=sys.stderr)
        defterdeki = {str(ay): int(n) for ay, n in ay_satirlari if ay is not None}

        if args.ay is not None:
            if args.ay not in defterdeki:
                print(f"HATA: {args.ay} defterde YOK — boş bir arşiv dosyası yazılmaz "
                      f"('o ay sıkıştırıldı' yalanı diske düşmesin). Defterdeki aylar: "
                      f"{', '.join(sorted(defterdeki)) or '(yok)'}", file=sys.stderr)
                return 2
            adaylar = [args.ay]
        else:
            adaylar = [a for a in sorted(defterdeki) if a < simdiki]

        satirlar, gerekceler = [], []
        try:
            for ay in adaylar:
                kayit, gerekce = ay_isle(con, kaynak_sql, ay, hedef / f"{ay}.parquet", args.kuru)
                satirlar.append(kayit)
                if gerekce:
                    gerekceler.append(gerekce)
        except duckdb.Error as e:
            # Sinyalli: yarım kalan arşivleme sessizce "başarılı" görünmez.
            print(f"HATA: arşivleme düştü ({e}) — bu ana kadar yazılanlar diskte duruyor.",
                  file=sys.stderr)
            return 4

        if args.json_kipi:
            olay_sorgu.json_bas(BASLIKLAR, [tuple(s[b] for b in BASLIKLAR) for s in satirlar],
                                sys.stdout)
        else:
            olay_sorgu.tablo_bas(BASLIKLAR, [tuple(s[b] for b in BASLIKLAR) for s in satirlar],
                                 sys.stdout)

        for g in gerekceler:
            print(g, file=sys.stderr)
        return 3 if gerekceler else 0
    finally:
        con.close()


if __name__ == "__main__":
    sys.exit(main())
