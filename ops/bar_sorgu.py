#!/usr/bin/env python3
# bar_sorgu.py — ops/bar_arsivle.py'nin yazdığı bölümlü parquet bar arşivini DuckDB ile
# sorgular (bellek içi; diske hiçbir DB dosyası yazılmaz). Arşivin YASA 6 OKUYUCUSU budur: bu araç
# olmasaydı arşiv üretilmemiş sayılırdı. Salt okunur — hiçbir dosyaya yazmaz. Koşum:
# .venv/bin/python ops/bar_sorgu.py --sorgu kapsam
"""ops/bar_sorgu.py — BAR ARŞİVİNİN DuckDB OKUMA YÜZEYİ
(TSK-020 [UYGULA-3] Task 2, 2026-09-07; tasarım: docs/TASARIM-BARS-PARQUET-DUCKDB-2026-09-06.md
§3.2).

NEDEN VAR. Arşivin gerekçesi "sıkıştırma" değil, SORULABİLİRLİKTİR: sembol başına CSV biçiminde
"hangi sembolün hangi aralıkta barı var", "dikiş nerede", "hangi seans eksik" soruları SQL'siz
cevaplanamıyordu. Üç hazır sorgu bu üç soruyu kapatır; `--sql` gerisini açar.

GÖRÜNÜM: `barlar` — `read_parquet` üstünde `sembol` (dosya adından) ve `ay` (tarihten) türetilmiş
iki ek sütun artı arşiv şemasının sekizi. Sembolün dosya ADINDAN gelmesi Task-1'in yerleşim
sözleşmesidir; `ay` ise İÇERİKTEN türer — dizin adına GÜVENİLMEZ, çünkü yanlış adlandırılmış bir
dizin sessizce yanlış aya sayım yaptırırdı. `ay`ın içerikten türemesi okuyucuyu YERLEŞİMDEN
BAĞIMSIZ kılan şeydir: `--ay` süzgeci hiç dizin olmayan `sembol` yerleşiminde de çalışır.

ÜÇ YERLEŞİM DE OKUNUR. Yazıcı `--bolum {sembol,yil,ay}` seçeneğini taşır (varsayılan `sembol`;
gerekçesi A1'in S4 ölçümü — 70 bin küçük dosya), yani arşiv üç şekilden birinde olabilir:
`<dizin>/<SEMBOL>.parquet` · `<dizin>/<YIL>/<SEMBOL>.parquet` ·
`<dizin>/<AAAA-AA>/<SEMBOL>.parquet`. Okuyucu üçünü de tarar (`*.parquet` + `*/*.parquet`) ve HANGİSİ olduğunu SORMAZ: yerleşimi
manifestten okuyup ona göre desen seçseydi, manifesti bozuk ya da eksik bir arşiv sessizce BOŞ
görünürdü. Karışık yerleşim (aynı sembol iki desende) yazıcının bölüm kapısıyla engellenir.

DOSYA LİSTESİ PYTHON TARAFINDA ÇIKARILIR, tek bir glob dizgesi DuckDB'ye verilmez: aksi hâlde
"arşiv boş" ile "arşiv yok" ayrımı DuckDB'nin hata metnine kalırdı ve araç boş bir tabloyu başarı
gibi basardı. Boş arşiv AÇIK bir hükümdür (rc 1 + hangi aracın doldurması gerektiği).

TAKVİM İTHAL EDİLİR, KOPYALANMAZ. `bosluk` alt komutu XNYS seans kümesini
`meridian.adapters.data`nın `_sessions` fonksiyonundan alır (kapsam sınırı da onun
`_SESSION_SPAN`ından) — yani `sanitize_bars`ın hayalet-seans kapısıyla AYNI takvim. ÖLÇÜLDÜ
(2026-09-07, `meridian/adapters/data.py` `CALENDAR` sabiti civarı): takvim adı `XNYS`, üretici
`pandas_market_calendars`, süreç başına bir kez üretilip küme olarak önbelleklenir. İkinci bir
tatil listesi yazmak, arşiv tarafının takvim güncellemelerinden sessizce kopması demekti.
Takvim ÖLÇÜLEMEZSE (modül yok/patladı) `bosluk` hüküm VERMEZ: rc 4 + gerekçe — "0 eksik" demek,
bilmediğimiz bir şeyi bilir gibi göstermek olurdu.

`dikis` VE ÖLÇÜLEMEZLİK. `ayarlama_olcegi` bugün arşivde HER ZAMAN NULL'dur, çünkü canlı CSV
önbelleğinde o sütun YOKTUR (Task-1 manifestinin `eksik_sutunlar` beyanı). Bu durumda alt komut
BOŞ SONUÇ DÖNDÜRMEZ gibi davranmaz — "ÖLÇÜLEMEDİ" beyanını manifestten okuyup stderr'e basar ve
0 satır gösterir. Sessiz boş sonuç, "dikiş yok" YALANIdır. BEYANIN KAPSAMI ARŞİVİN TAMAMIDIR,
seçilen küme DEĞİL (bulgu K1, 2026-09-08): süzülmüş kümede sayan bir kapı, ay sınırındaki gerçek
bir ölçek kesilmesini "cevaplanamaz" diye örterdi — cevap tam da düzeltilmiş sorguda dururken.

SELECT MUHAFIZI İTHALDİR. `--sql` yalnız TEK bir SELECT kabul eder ve kapının kendisi
`ops/olay_sorgu.py`nin `select_kapisi` fonksiyonudur (DuckDB'nin kendi ayrıştırıcısıyla
sınıflandırır; regex bir SQL ayrıştırıcısı değildir). Kopyalanmadı: iki muhafızın biri
güncellenip diğeri kalsaydı, bu araç kapalı sanılan bir kapı taşırdı.

ÖRNEK — TSK-159/EDG-082 tüketicisi ("as_of(t) üyeleri içinde barı olmayanlar"; üyelik listesi
kendi kaynağından gelir, burada `uyeler` görünümü olarak varsayılır):
    python ops/bar_sorgu.py --sql "SELECT u.sembol FROM uyeler u LEFT JOIN (
        SELECT DISTINCT sembol FROM barlar WHERE date <= DATE '2024-06-24') b
        USING (sembol) WHERE b.sembol IS NULL"

KULLANIM:
    python ops/bar_sorgu.py --sorgu kapsam
    python ops/bar_sorgu.py --sorgu bosluk --sembol AAPL
    python ops/bar_sorgu.py --sorgu dikis --ay 2024-06 --json
    python ops/bar_sorgu.py --sql "SELECT sembol, count(*) FROM barlar GROUP BY 1"
    python ops/bar_sorgu.py --dizin /yol/barlar --sorgu kapsam

ÇIKIŞ KODU: 0 = koştu · 1 = arşiv dizini yok ya da içinde parquet yok · 2 = kullanım hatası ·
           3 = `--sql` REDDEDİLDİ (tek SELECT değil) · 4 = ölçülemedi (takvim yok / DuckDB düştü).
"""

from __future__ import annotations

import argparse
import pathlib
import sys

import duckdb
import pandas as pd

# ops/ altından doğrudan koşulduğunda `meridian` paketi ve kardeş `ops` modülleri bulunabilsin
# (kardeş betiklerin taşıdığı bootstrap satırının aynısı).
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from meridian import config as _config                       # noqa: E402
from meridian.adapters import data as _data                  # noqa: E402
from ops import bar_arsivle                                  # noqa: E402
from ops import olay_sorgu                                   # noqa: E402

#: MUHAFIZ İTHALDİR — kopya değil. Ad burada yeniden bağlanır ki çağrı yeri okunur olsun;
#: bağlanan NESNE `ops/olay_sorgu.py`nin fonksiyonunun TA KENDİSİDİR (kimlik çivisi v436'da).
select_kapisi = olay_sorgu.select_kapisi

SORGULAR = ("kapsam", "dikis", "bosluk")
#: Satır tavanları — kesme GÖRÜNÜR (tavan dolduğunda stderr'e uyarı düşer), sessiz değil.
VARSAYILAN_N = {"kapsam": 500, "dikis": 200, "bosluk": 500}

#: Sembol dosya ADINDAN gelir. Nokta yerine tire kuralı Task-1'in beyanıdır ve TERSİNMEZ
#: (`brk-b.parquet` → `BRK-B`); manifestteki `sembol_kaynagi` alanı bunu söyler.
_SEMBOL_IFADESI = "upper(regexp_extract(filename, '([^/]+)\\.parquet$', 1))"

BASLIKLAR = {
    "kapsam": ["sembol", "ilk", "son", "satir"],
    "dikis": ["sembol", "tarih", "onceki_olcek", "olcek"],
    "bosluk": ["sembol", "eksik", "ilk_eksik", "son_eksik", "ornek"],
}


def arsiv_dizini() -> pathlib.Path:
    """Varsayılan arşiv dizini — Task-1'in varsayılanıyla AYNI kaynaktan türer (`config.STATE` +
    aracın `VARSAYILAN_HEDEF_ALT` sabiti). İki yerde yazılsaydı yazıcı ile okuyucu sessizce
    farklı dizinlere bakabilirdi."""
    return pathlib.Path(_config.STATE) / bar_arsivle.VARSAYILAN_HEDEF_ALT


#: Yazıcının ürettiği ÜÇ yerleşimin desenleri — `sembol` düzeyi köktedir, `yil`/`ay` bir dizin
#: altındadır. Desenler burada TEK yerde durur; `bolum` adlarının kendisi yazıcının sabitidir.
YERLESIM_DESENLERI = ("*.parquet", "*/*.parquet")


def parquet_dosyalari(dizin: pathlib.Path) -> list[pathlib.Path]:
    """Arşivdeki parquet dosyaları — üç yerleşim de taranır (gerekçe modül başlığında).
    Sıralı ve TEKİL döner ki sorgu planı ve satır sırası koşumdan koşuma kaymasın."""
    return sorted({p for desen in YERLESIM_DESENLERI
                   for p in dizin.glob(desen) if p.is_file()})


def gorunum_sql(dosyalar: list[pathlib.Path]) -> str:
    liste = "[" + ", ".join(olay_sorgu.sql_metni(p) for p in dosyalar) + "]"
    sutunlar = ", ".join(bar_arsivle.SUTUNLAR)
    return (f"SELECT {_SEMBOL_IFADESI} AS sembol, strftime(date, '%Y-%m') AS ay, {sutunlar} "
            f"FROM read_parquet({liste}, hive_partitioning=false, filename=true)")


def _suzgec_kosullari(sembol: str | None, ay: str | None) -> tuple[list[str], list]:
    """SÜZGEÇ GRAMERİ — TEK KAYNAK (bulgu K6, 2026-09-08). (koşul listesi, parametreler).

    `kapsam`/`bosluk`/`_kapsam_disi_uyar` bu grameri `_suzgec` metnini üreterek kullanır;
    `dikis` ise koşulları DIŞ `WHERE`ine kendisi diziyor (pencere hesabı içeride, süzgeç
    dışarıda). `olcek_olculdu_mu` bu grameri BİLEREK kullanmaz: kapı TÜM arşivde ölçer (K1,
    2026-09-08 — süzülmüş kümede sayan kapı ay-sınırı dikişini kaçırıyordu). İki tüketici, İKİ FARKLI BİÇİM ama TEK gramer: kurallar burada
    yazılırsa `--yil` gibi üçüncü bir süzgeç ya da sembol normalizasyonundaki bir değişiklik
    tüm alt komutlara AYNI ANDA iner. Kopyalansaydı `dikis` sessizce eski kuralla süzerdi ve
    hiçbir çivi bunu görmezdi.

    Süzgeç SQL'e METİN olarak gömülmez — argv'den gelen bir sembol adı sorguyu bozabilirdi."""
    kosullar, parametreler = [], []
    if sembol:
        kosullar.append("sembol = ?")
        parametreler.append(sembol.upper())
    if ay:
        kosullar.append("ay = ?")
        parametreler.append(ay)
    return kosullar, parametreler


def _suzgec(sembol: str | None, ay: str | None) -> tuple[str, list]:
    """(WHERE parçası, parametreler) — `_suzgec_kosullari`nın METİN sarmalayıcısı."""
    kosullar, parametreler = _suzgec_kosullari(sembol, ay)
    return (" WHERE " + " AND ".join(kosullar)) if kosullar else "", parametreler


# ---------------------------------------------------------------------------------------------
# Alt komutlar
# ---------------------------------------------------------------------------------------------

def sorgu_kapsam(con: duckdb.DuckDBPyConnection, sembol, ay, n) -> list[tuple]:
    nerede, parametreler = _suzgec(sembol, ay)
    return con.execute(
        f"SELECT sembol, min(date) AS ilk, max(date) AS son, count(*) AS satir FROM barlar"
        f"{nerede} GROUP BY sembol ORDER BY sembol LIMIT {int(n)}", parametreler).fetchall()


def olcek_olculdu_mu(con: duckdb.DuckDBPyConnection) -> int:
    """ARŞİVİN TAMAMINDA `ayarlama_olcegi` DOLU kaç satır var? 0 ise dikiş sorusu ÖLÇÜLEMEZ.

    KAPI SÜZGEÇSİZDİR (bulgu K1, 2026-09-08). Eskiden `--sembol`/`--ay` ile SÜZÜLMÜŞ kümede
    sayıyordu ve bu, `sorgu_dikis`in pencereyi tüm seriye taşıyarak kapattığı sınıfı KAPIDAN
    geri sokuyordu: `ayarlama_olcegi` Ocak'ta DOLU, Şubat'ta hiç yazılmamışsa (kısmi geri-dolum)
    `--ay <Şubat>` süzülmüş kümede 0 DOLU satır sayar, "bu arşivde cevaplanamaz" denir ve
    `sorgu_dikis` HİÇ çağrılmazdı — oysa Şubat'ın ilk seansı GERÇEK bir dikiştir
    (onceki_olcek=1.0 → olcek=NULL). Kapı ile sorgunun ölçtüğü küme artık AYNI kaynaktan
    (süzgeçsiz `barlar`) gelir; beyan yalnız "arşivin TAMAMINDA hiç dolu ölçek yok" hâlinde
    doğrudur ve yalnız o hâlde basılır."""
    return int(con.execute(
        "SELECT count(*) FROM barlar WHERE ayarlama_olcegi IS NOT NULL").fetchone()[0])


def sorgu_dikis(con: duckdb.DuckDBPyConnection, sembol, ay, n) -> list[tuple]:
    """`ayarlama_olcegi` bir ÖNCEKİ BARA göre değişen günler. İlk bar dikiş DEĞİLDİR (öncesi
    yok — `onceki_olcek IS NULL` satırı hüküm taşımaz, ölçülemezlik taşır).

    LAG PENCERESİ TÜM (FİLTRESİZ) SERİ ÜZERİNDE HESAPLANIR; `--sembol`/`--ay` yalnız SONUÇ
    satırlarına (pencere hesaplandıktan SONRA, dış WHERE'de) uygulanır (bulgu C1, 2026-09-08).
    Filtre İÇERİ alınsaydı (`FROM barlar{nerede}` ile pencereden ÖNCE) `--ay` ay-sınırındaki
    GERÇEK bir dikişi kaçırırdı: filtrelenmiş kümede ayın ilk günü artık o PARTITION'ın kendisi
    ilk satırı olur, `onceki_olcek` NULL çıkar ve dış `WHERE onceki_olcek IS NOT NULL` bu satırı
    SESSİZCE elerdi — 0 satır "bu ayda dikiş yok" sanılırdı, oysa yalnız filtre yüzünden
    GÖRÜNMEZ olmuştur. `PARTITION BY sembol` çok-sembollü sahnede de korunur: bir sembolün SON
    günü ile başka bir sembolün İLK günü asla dikiş SAYILMAZ (pencere sembol sınırını aşmaz).

    DIŞ SÜZGEÇ GRAMERİ KOPYALANMAZ, `_suzgec_kosullari`ndan alınır (bulgu K6, 2026-09-08):
    ilk düzeltme `sembol = ?` / `ay = ?` kurallarını buraya ELLE kopyalamıştı ve o an aynı
    gerçeğin ikinci kaynağı doğdu — `_suzgec`e eklenecek üçüncü bir süzgeç dört alt komutta
    uygulanır, `dikis`te SESSİZCE uygulanmazdı (tek-kaynak yasası). Biçim ayrı (burada dış
    WHERE'e ekleniyor, orada metin üretiliyor), GRAMER tek."""
    suzgec_kosullari, dis_parametreler = _suzgec_kosullari(sembol, ay)
    dis_kosullar = ["onceki_olcek IS NOT NULL",
                    "olcek IS DISTINCT FROM onceki_olcek"] + suzgec_kosullari
    return con.execute(
        "SELECT sembol, tarih, onceki_olcek, olcek FROM ("
        "  SELECT sembol, ay, date AS tarih, ayarlama_olcegi AS olcek, "
        "         lag(ayarlama_olcegi) OVER (PARTITION BY sembol ORDER BY date) AS onceki_olcek "
        "  FROM barlar) AS _d "
        f"WHERE {' AND '.join(dis_kosullar)} "
        f"ORDER BY sembol, tarih LIMIT {int(n)}", dis_parametreler).fetchall()


def takvim_yukle(con: duckdb.DuckDBPyConnection) -> tuple[int, tuple]:
    """XNYS seanslarını geçici bir tabloya (`seanslar`) koyar; (satır, kapsam aralığı) döner.

    Kaynak `meridian.adapters.data` — ithal, kopya değil. `_SESSION_SPAN` modül GLOBALİdİR ve
    ancak `_sessions()` çağrıldıktan SONRA dolar: bu yüzden değer modülden ÇAĞRI SONRASI okunur,
    ithal anında bağlanmaz (bağlansaydı hep boş tuple görülürdü)."""
    ses = _data._sessions()
    span = _data._SESSION_SPAN
    if not ses or not span:
        return 0, ()
    df = pd.DataFrame({"gun": sorted(ses)})
    con.register("_seans_kaynak", df)
    try:
        con.execute("CREATE OR REPLACE TEMP TABLE seanslar AS "
                    "SELECT CAST(gun AS DATE) AS gun FROM _seans_kaynak")
    finally:
        con.unregister("_seans_kaynak")
    return len(ses), span


def sorgu_bosluk(con: duckdb.DuckDBPyConnection, sembol, ay, n, span) -> list[tuple]:
    """Her sembolün KENDİ kapsamı (ilk↔son bar) içinde, takvimde seans olup barı OLMAYAN günler.

    Kapsam takvim aralığıyla da kesişir: `_SESSION_SPAN` dışındaki bir tarih hakkında takvimin
    hükmü YOKTUR (`_calendar_scan` ile aynı disiplin) ve orada "eksik" demek uydurma olurdu.
    Boşluğu OLMAYAN sembol de satır olarak döner — "0 eksik" ile "hiç bakılmadı" aynı
    görünmemeli."""
    nerede, parametreler = _suzgec(sembol, ay)
    lo, hi = span
    # KURULUŞ ÜÇ ADIMDIR (beklenen → eksik → özet), TEK BİR BÜYÜK JOIN DEĞİL. ÖLÇÜLDÜ
    # (duckdb 1.5.5, 2026-09-07): korelasyonlu bir `NOT EXISTS`i LEFT JOIN'in ON koşuluna koymak
    # "Cannot perform non-inner join on subquery" ile düşüyor. Anti-join düz bir CTE üzerinde
    # `LEFT JOIN … IS NULL` olarak yazılır.
    return con.execute(
        f"WITH kapsam AS (SELECT sembol, min(date) AS ilk, max(date) AS son FROM barlar{nerede} "
        "                GROUP BY sembol), "
        "     beklenen AS (SELECT k.sembol, s.gun FROM kapsam k JOIN seanslar s "
        "                    ON s.gun BETWEEN greatest(k.ilk, CAST(? AS DATE)) "
        "                                 AND least(k.son, CAST(? AS DATE))), "
        f"     mevcut AS (SELECT sembol, date FROM barlar{nerede}), "
        "     eksikler AS (SELECT b.sembol, b.gun FROM beklenen b "
        "                    LEFT JOIN mevcut m ON m.sembol = b.sembol AND m.date = b.gun "
        "                   WHERE m.sembol IS NULL) "
        "SELECT k.sembol, count(e.gun) AS eksik, min(e.gun) AS ilk_eksik, "
        "       max(e.gun) AS son_eksik, "
        "       coalesce(list_slice(list(e.gun ORDER BY e.gun) "
        "                           FILTER (WHERE e.gun IS NOT NULL), 1, 5), []) AS ornek "
        "FROM kapsam k LEFT JOIN eksikler e ON e.sembol = k.sembol "
        f"GROUP BY k.sembol ORDER BY k.sembol LIMIT {int(n)}",
        parametreler + [lo, hi] + parametreler).fetchall()


# ---------------------------------------------------------------------------------------------

def _ayristirici() -> argparse.ArgumentParser:
    a = argparse.ArgumentParser(
        prog="ops/bar_sorgu.py",
        description="ops/bar_arsivle.py'nin yazdığı parquet bar arşivini DuckDB ile sorgular "
                    "(salt okunur).",
        epilog="Serbest sorguda `barlar` görünümü: sembol, ay, date, open, high, low, close, "
               "volume, kaynak, ayarlama_olcegi.",
    )
    a.add_argument("--dizin", type=pathlib.Path, default=None,
                   help="arşiv dizini (varsayılan: config.STATE/barlar)")
    # default=None BİLEREK (`ops/olay_sorgu.py` dersi): "operatör açıkça verdi mi" ile "varsayılan
    # devrede" ayrımı olmadan `--sql --sorgu kapsam` çelişkisi SESSİZCE yok sayılırdı.
    a.add_argument("--sorgu", choices=SORGULAR, default=None, help="hazır sorgu")
    a.add_argument("--sembol", default=None, help="yalnız bu sembol")
    a.add_argument("--ay", default=None, help="yalnız bu ay (AAAA-AA)")
    a.add_argument("--sql", default=None, help="serbest sorgu — YALNIZ tek SELECT")
    a.add_argument("--n", type=int, default=None, help="satır tavanı (sorguya göre varsayılan)")
    a.add_argument("--json", action="store_true", dest="json_kipi", help="satır-JSON bas")
    return a


def main(argv: list[str] | None = None) -> int:
    args = _ayristirici().parse_args(argv)

    if args.sql is not None:
        catisan = [ad for ad, deger in (("--sorgu", args.sorgu), ("--sembol", args.sembol),
                                        ("--ay", args.ay), ("--n", args.n)) if deger is not None]
        if catisan:
            print(f"HATA: `--sql` ile birlikte {', '.join(catisan)} birlikte kullanılamaz — "
                  "serbest sorguda süzgeci ve tavanı SQL'in kendisi taşır (WHERE/LIMIT). Bayrak "
                  "sessizce yok sayılmaz.", file=sys.stderr)
            return 2
    elif args.sorgu is None:
        print(f"HATA: `--sorgu` ({'|'.join(SORGULAR)}) ya da `--sql` verilmelidir — varsayılan "
              "bir sorgu YOKTUR (hangi soruyu sorduğun sessizce seçilmez).", file=sys.stderr)
        return 2

    dizin = args.dizin or arsiv_dizini()
    if not dizin.is_dir():
        print(f"HATA: arşiv dizini bulunamadı: {dizin} — önce `ops/bar_arsivle.py --uygula`.",
              file=sys.stderr)
        return 1

    dosyalar = parquet_dosyalari(dizin)
    if not dosyalar:
        print(f"HATA: {dizin} altında {' ya da '.join(YERLESIM_DESENLERI)} deseninde hiç dosya "
              f"yok — arşiv BOŞ. Doldurmak için: "
              f"`ops/bar_arsivle.py --hedef {dizin} --uygula`.", file=sys.stderr)
        return 1

    con = olay_sorgu.baglanti_kur()
    try:
        try:
            con.execute(f"CREATE OR REPLACE TEMP VIEW barlar AS {gorunum_sql(dosyalar)}")
        except duckdb.Error as e:
            print(f"HATA: arşiv okunamadı ({dizin}): {e}", file=sys.stderr)
            return 4

        if args.sql is not None:
            gerekce = select_kapisi(con, args.sql)
            if gerekce is not None:
                print(f"HATA: sorgu reddedildi — {gerekce}", file=sys.stderr)
                return 3
            try:
                imlec = con.execute(args.sql)
                basliklar = [d[0] for d in imlec.description]
                satirlar = imlec.fetchall()
            except duckdb.Error as e:
                print(f"HATA: sorgu düştü: {e}", file=sys.stderr)
                return 4
            tavan = None
        else:
            n = args.n if args.n is not None else VARSAYILAN_N[args.sorgu]
            basliklar = BASLIKLAR[args.sorgu]
            tavan = n
            try:
                if args.sorgu == "kapsam":
                    satirlar = sorgu_kapsam(con, args.sembol, args.ay, n)
                elif args.sorgu == "dikis":
                    # SÜZGEÇSİZ kapı (K1): beyan yalnız arşivin TAMAMI boşken doğrudur.
                    dolu = olcek_olculdu_mu(con)
                    if dolu == 0:
                        _olculemedi_beyani(dizin)
                        satirlar = []
                    else:
                        satirlar = sorgu_dikis(con, args.sembol, args.ay, n)
                else:
                    seans_sayisi, span = takvim_yukle(con)
                    if seans_sayisi == 0:
                        print("HATA: seans takvimi ÖLÇÜLEMEDİ "
                              f"({_data.CALENDAR}; `pandas_market_calendars` yok ya da düştü) — "
                              "`bosluk` hüküm VERMEZ. '0 eksik' basmak, bilinmeyen bir şeyi "
                              "bilir gibi göstermek olurdu.", file=sys.stderr)
                        return 4
                    satirlar = sorgu_bosluk(con, args.sembol, args.ay, n, span)
                    _kapsam_disi_uyar(con, args.sembol, args.ay, span)
            except duckdb.Error as e:
                print(f"HATA: sorgu düştü ({args.sorgu}): {e}", file=sys.stderr)
                return 4
    finally:
        con.close()

    bas = olay_sorgu.json_bas if args.json_kipi else olay_sorgu.tablo_bas
    bas(basliklar, satirlar, sys.stdout)

    if tavan is not None and len(satirlar) >= tavan:
        print(f"UYARI: satır TAVANI doldu ({tavan}) — sonuç KESİLMİŞ olabilir; `--n` ile büyüt.",
              file=sys.stderr)
    return 0


def _olculemedi_beyani(dizin: pathlib.Path) -> None:
    """`dikis` sorusunun ölçülemez olduğunu SÖYLER ve gerekçeyi manifestten okur (manifestin
    ikinci Yasa 6 okuyucusu burasıdır — birincisi yazıcının idempotency kapısı)."""
    try:
        eksik = bar_arsivle.manifest_oku(dizin).get("eksik_sutunlar", {})
    except RuntimeError as e:
        # Sinyalli: manifest bozuksa gerekçe UYDURULMAZ, okunamadığı söylenir.
        print(f"UYARI: manifest okunamadı ({e}) — beyan kaynağı gösterilemiyor.",
              file=sys.stderr)
        eksik = {}
    ilgili = sorted({s for s, sutunlar in eksik.items() if "ayarlama_olcegi" in (sutunlar or [])})
    print("ÖLÇÜLEMEDİ: arşivin TAMAMINDA `ayarlama_olcegi` DOLU tek satır yok — dikiş sorusu bu "
          "arşivde cevaplanamaz. Gerekçe kaynağı manifestteki `eksik_sutunlar` beyanıdır "
          f"(sütunu eksik sembol sayısı: {len(ilgili)}); canlı CSV önbelleğinde o sütun YOKTUR. "
          "0 satır 'dikiş yok' DEMEK DEĞİLDİR.", file=sys.stderr)


def _kapsam_disi_uyar(con: duckdb.DuckDBPyConnection, sembol, ay, span) -> None:
    """Bir serinin barları takvimin KAPSADIĞI aralığın dışına taşıyorsa, o bölge hakkında
    `bosluk` hüküm vermemiştir — bunu söylemek zorundayız (sessiz kısmi kapsama, tam kapsama
    gibi okunur)."""
    nerede, parametreler = _suzgec(sembol, ay)
    lo, hi = span
    n = int(con.execute(
        f"SELECT count(*) FROM (SELECT sembol, min(date) AS ilk, max(date) AS son FROM barlar"
        f"{nerede} GROUP BY sembol) AS _k "
        "WHERE _k.ilk < CAST(? AS DATE) OR _k.son > CAST(? AS DATE)",
        parametreler + [lo, hi]).fetchone()[0])
    if n:
        print(f"UYARI: {n} sembolün barları takvim kapsamının ({lo}…{hi}) DIŞINA taşıyor — o "
              "bölgede eksik seans ARANMADI (takvimin hükmü yok).", file=sys.stderr)


if __name__ == "__main__":
    sys.exit(main())
