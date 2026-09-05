#!/usr/bin/env python3
# olay_sikistir.py — state/events.jsonl olay defterinin GEÇMİŞ AYLARINI parquet'e sıkıştırır
# (state/olaylar/AAAA-AA.parquet). Cari ay YAZILMAZ. Varsayılan KIRPMAZ (yalnız sıkıştırır);
# `--kirp` ile İSTENİRSE parquet'e alınmış VE doğrulanmış eski aylar (cari+önceki ay HARİÇ)
# jsonl'den ATOMİK düşürülür (adım 3, TSK-137b, 2026-09-05) — worker aktifken `--zorla` olmadan
# REDDEDİLİR. Idempotent: ay dosyası varsa satır sayısı + içerik damgası kıyaslanır — aynıysa
# atlanır, FARKLIYSA `.yeni` yazılır ve rc=3 döner (sessiz üzerine yazma YOK). Bozuk JSON satırı
# ve AY'a atanamayan satır SAYILIP stderr'e raporlanır (Yasa 4). Arşivin OKUYUCUSU
# ops/olay_sorgu.py + meridian/olaylar.py'dır (Yasa 6) — birleşik okur, parquet'lenen ay
# defterden süzülür. Koşum: .venv/bin/python ops/olay_sikistir.py --kuru — meridian İTHAL
# ETMEZ (obs'a ulaşamaz).
"""ops/olay_sikistir.py — OLAY DEFTERİNİN AYLIK PARQUET ARŞİVİ + KIRPMA
(TSK-020 [UYGULA-2] adım 2-3, 2026-09-03 / 2026-09-05).

NEDEN VAR. Defter 27.887 satır / 9 MB (ölçüm 2026-09-01) ve satır satır büyüyor; ölçülen ay
dağılımı 2026-07: 27.273 · 2026-08: 614 (2026-09-03). Her sorgu bugün 9 MB metni baştan
ayrıştırıyor. Kapanmış aylar bir daha DEĞİŞMEZ — onları sütunlu, sıkıştırılmış bir biçimde
dondurmak hem taramayı ucuzlatır hem de defterin kırpılabilmesinin ÖN KOŞULUDUR.

VARSAYILAN HÂLÂ İKİ ŞEYİ YAPMAZ — ve bunlar kapsam kararıdır, eksiklik değil:
  1. DEFTERİ KIRPMAZ (`--kirp` VERİLMEDİKÇE). Adım 2 (2026-09-03) kırpmayı bilerek ertelemişti:
     bedel yasası — kazanç (sıkıştırma) ölçülüp bedel (okuyucuların ne kaybettiği) ölçülmeden
     kırpma yapılmaz. Adım 3 (2026-09-05) bedeli ÖLÇTÜ ve kapattı: `limit=None` okuyucular
     (`watchdog.integrity_report`, `selfreview.build`, `ops/alarm_backlog_digest.py`)
     `meridian/olaylar.py::tum_olaylar()`e taşındı (birleşik görünüm, kırpma öncesi/sonrası AYNI
     sonuç) — bkz. `--kirp` bölümü altında.
  2. CARİ AYI YAZMAZ. Hâlâ yazılmakta olan bir ay dondurulamaz — dondurulsaydı arşiv daha
     doğduğu gün eskirdi ve her koşum FARK verirdi.

SESSİZCE ÜZERİNE YAZMAZ (her iki modda da). Var olan bir ay dosyası ancak İÇERİĞİ AYNIYSA
"atlandı" olur. Farklıysa yenisi `AAAA-AA.parquet.yeni` adıyla YANINA yazılır, eskisine
DOKUNULMAZ ve araç KIRMIZI (rc=3) döner: kıyas operatörün, karar operatörün. `--kirp` bu FARK
durumunu asla görmezden gelmez — aşağıya bakınız.

--KIRP: PARQUET'E ALINMIŞ VE DOĞRULANMIŞ AYLARI JSONL'DEN DÜŞÜRÜR (varsayılan KAPALI). Hedef
kümesi = sıkıştırma adaylarından (`ay < cari ay`) CARİ AYA EN YAKIN olanı (önceki ay) HARİÇ
hepsi — yani jsonl'de kırpma sonrası KALAN = cari ay + önceki ay (≥30 gün garantisi, iki ay asla
28 günden kısa olamaz). Bir ay ANCAK şu ikisi de doğruysa kırpma adayıdır: (a) bu koşunun
sıkıştırma adımı o ayı "yazıldı" ya da "atlandı" durumuna soktu (yani arşiv İÇERİK OLARAK
jsonl'le EŞLEŞİYOR — "FARK" durumundaki bir ay ASLA kırpılmaz); (b) o ay < önceki ay. HERHANGİ
BİR ADAY AYDA "FARK" bulunursa TÜM kırpma reddedilir (rc=5) — hiçbir ay silinmez, "kısmi
kırpma güvenli kırpmadır" varsayımı YOKTUR.

ATOMİKLİK + ÇİFT DOĞRULAMA: kırpılacak satırlar arşivin KENDİSİNDEN (`ham` sütunu, jsonl'den
YENİDEN sorgulanmadan) okunur ve jsonl'in RAW satırlarıyla METİN eşleşmesiyle çıkarılır; yeni
içerik `dosya`nın yanındaki bir tmp dosyaya yazılır, fsync edilir, SONRA DuckDB ile YENİDEN
taranır (kaldırılan aylardan hiçbiri kalmamalı, toplam satır BEKLENENLE eşit olmalı, bozuk satır
sayısı DEĞİŞMEMELİ) — bu ikinci doğrulama GEÇMEZSE tmp silinir, ORİJİNAL DOSYAYA DOKUNULMAZ,
rc=5. Yalnız İKİ doğrulama da geçerse `os.replace` ile ATOMİK olarak üzerine alınır.

WORKER KAPISI: gerçek (kuru olmayan) `--kirp` koşumu `meridian.service`in DURUMUNU ölçer
(`systemctl is-active` — A1'de gerçek servis; yerelde systemctl yoksa ÖLÇÜLEMEDİ sayılır). Servis
AKTİFSE ya da DURUM ÖLÇÜLEMİYORSA (yerel makine) kırpma `--zorla` VERİLMEDEN REDDEDİLİR (rc=5) —
worker `append_jsonl` ile eşzamanlı yazarken jsonl'i yeniden yazmak veri kaybı riski taşır. Bu
kapı YALNIZ kırpma adımını korur: sıkıştırma (arşive YAZMA) her zaman güvenlidir ve worker
durumundan bağımsız çalışır. Test seçeneği: `MERIDIAN_KIRPMA_TEST_WORKER_AKTIF=1/0` ortam
değişkeni gerçek `systemctl` çağrısının YERİNE geçer (subprocess ile çağrılan aracın süreç ortamı
kalıtımla taşır — `monkeypatch.setenv` bunu ayarlar).

MANİFEST (`state/olaylar/manifest.json`, D3 Yasa 6 okuyucusu = bu kapının KENDİSİ + gelecekteki
bekçi sensörü, ROADMAP'e not): her kırpılan ay için {satir, damga, dosya, kirpma_ts} kaydı ATOMİK
eklenir/güncellenir — mevcut kayıtlar KORUNUR. Bu, kırpmanın AUDIT İZİDİR: hangi ay ne zaman,
hangi içerikle (damga) kırpıldı.

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
    python ops/olay_sikistir.py                   # tüm geçmiş ayları yaz (KIRPMAZ)
    python ops/olay_sikistir.py --ay 2026-07      # tek ay
    python ops/olay_sikistir.py --json            # satır-JSON çıktı
    python ops/olay_sikistir.py --dosya /yol/x.jsonl --hedef /yol/arsiv
    python ops/olay_sikistir.py --kirp --kuru     # kırpma ÖNİZLEME (hiçbir şey silinmez)
    python ops/olay_sikistir.py --kirp            # sıkıştır + doğrulanmış eski ayları KIRP
    python ops/olay_sikistir.py --kirp --zorla    # worker durumu ölçülemese/aktif olsa bile kırp

ÇIKIŞ KODU: 0 = koştu (yazıldı/atlandı/kırpıldı) · 2 = kullanım/dosya hatası · 3 = FARK bulundu
           (`.yeni` yazıldı, eskisi duruyor) · 4 = DuckDB'de düştü · 5 = kırpma REDDEDİLDİ
           (worker aktif/ölçülemedi, doğrulama tutarsız, ya da FARK bulunan bir ay kırpma
           kapsamındaydı) — jsonl bu durumda BAYT BAYT dokunulmamış kalır.
"""

from __future__ import annotations

import argparse
import collections
import datetime as _dt
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

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


# =================================================================================================
# KIRPMA (adım 3, TSK-137b, 2026-09-05) — `--kirp`. Varsayılan KAPALI; yalnız bu bölümdeki
# fonksiyonlar `--kirp` verildiğinde çağrılır, aksi hâlde `main()` bunlara HİÇ dokunmaz.
# =================================================================================================

MANIFEST_ADI = "manifest.json"
#: `systemctl is-active`in YERİNE geçen test/operatör seçeneği — subprocess ile çağrılan bu
#: aracın süreç ortamı KALITIMLA taşınır (`monkeypatch.setenv` bunu doğrudan ayarlayabilir; bkz.
#: modül başlığı "SÖZLEŞME KOMUT SATIRIDIR" disiplini — env değişkeni bu disiplini BOZMAZ, `main()`
#: hâlâ import edilmiyor). "1" → aktif say, "0" → durgun say, yoksa GERÇEK systemctl'e bakılır.
WORKER_DURUM_ENV = "MERIDIAN_KIRPMA_TEST_WORKER_AKTIF"


def onceki_ay(simdi: _dt.datetime | None = None) -> str:
    """`cari_ay`dan BİR AY ÖNCESİ (UTC). Kırpma sonrası jsonl'de KALAN iki ay — cari + bu —
    ≥30 gün garantisini taşır (iki takvim ayı asla 28 günden kısa olamaz)."""
    s = simdi or _dt.datetime.now(_dt.timezone.utc)
    onceki_ay_no = s.month - 1 or 12
    onceki_yil = s.year - 1 if s.month == 1 else s.year
    return f"{onceki_yil:04d}-{onceki_ay_no:02d}"


def worker_aktif_mi() -> bool | None:
    """`meridian.service` ŞU AN aktif mi? True/False ÖLÇÜLDÜĞÜNDE; YEREL makinede (systemctl
    yok) ya da komut beklenmeyen bir şey döndürdüğünde None (ÖLÇÜLEMEDİ — uydurma yasağı).

    Çağıran None'ı 'aktif VARSAY' okumalıdır (fail-safe): kırpma yalnız AÇIKÇA durgun ölçüldüğünde
    (`False`) ya da `--zorla` ile serbest kalır."""
    zorlanan = os.environ.get(WORKER_DURUM_ENV)
    if zorlanan is not None:
        return zorlanan.strip() == "1"
    systemctl = shutil.which("systemctl")
    if systemctl is None:
        return None  # yerel makine (örn. macOS) — systemctl yok, durum ÖLÇÜLEMEDİ
    try:
        r = subprocess.run([systemctl, "is-active", "meridian.service"],
                            capture_output=True, text=True, timeout=5)
    except (OSError, subprocess.SubprocessError):
        return None  # sessiz-yutma DEĞİL: None zaten "ölçülemedi" hükmüdür, çağıran fail-safe okur
    durum = r.stdout.strip()
    if durum == "active":
        return True
    if durum in ("inactive", "failed", "unknown"):
        return False
    return None  # beklenmeyen çıktı — UYDURULMAZ, ölçülemedi say


def manifest_yolu(hedef: pathlib.Path) -> pathlib.Path:
    return hedef / MANIFEST_ADI


def manifest_oku(hedef: pathlib.Path) -> dict:
    """Kırpma kapısının KENDİSİNİN okuduğu manifest (D3 Yasa 6 okuyucusu). Dosya yoksa BOŞ
    sözlük — henüz hiç kırpma olmamış demektir, hata değil."""
    yol = manifest_yolu(hedef)
    if not yol.exists():
        return {"kirpilan_aylar": {}}
    try:
        icerik = json.loads(yol.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        # Sinyalli: bozuk manifest sessizce boşmuş gibi davranılmaz — "daha önce ne kırpıldı"
        # bilgisi güvenilmiyorsa yeni kırpmanın audit izi de güvenilmez hâle gelir.
        raise RuntimeError(f"manifest okunamadı ({yol}): {type(e).__name__}: {e}") from e
    icerik.setdefault("kirpilan_aylar", {})
    return icerik


def manifest_guncelle(hedef: pathlib.Path, yeni_kayitlar: dict) -> None:
    """Manifesti ATOMİK günceller: mevcut kayıtlar KORUNUR, `yeni_kayitlar`daki aylar
    eklenir/üzerine yazılır (tmp + fsync + os.replace — aynı disiplin `kirp_uygula`daki jsonl
    yazımıyla)."""
    mevcut = manifest_oku(hedef)
    mevcut["kirpilan_aylar"].update(yeni_kayitlar)
    mevcut["guncellendi"] = _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")
    hedef.mkdir(parents=True, exist_ok=True)
    yol = manifest_yolu(hedef)
    fd, tmp_adi = tempfile.mkstemp(dir=str(hedef), prefix=".manifest-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(mevcut, f, ensure_ascii=False, indent=2, sort_keys=True)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_adi, yol)
    except Exception:
        try:
            os.unlink(tmp_adi)
        except OSError:  # sessiz-yutma: temizlik denemesi başarısız olsa da asıl hata yukarı fırlatılıyor, ikinci bir hata onu gizlemesin
            pass
        raise


def kirpma_hedeflerini_belirle(satirlar: list[dict], onceki: str) -> tuple[list[str], str | None]:
    """Bu koşunun sıkıştırma sonuçlarından (`satirlar`, `ay_isle` çıktıları) KIRPMA adaylarını
    çıkarır: `ay < onceki` VE durum `yazıldı`/`atlandı` (arşiv içerik olarak jsonl'le EŞLEŞİYOR).

    Dönüş: (hedefler, red_gerekcesi). HERHANGİ bir aday ay `FARK` durumundaysa (2. eleman
    dolu) hedefler BOŞ liste döner — "kısmi kırpma güvenli kırpmadır" varsayımı YOKTUR, bir
    ayın doğrulanamaması TÜM kırpmayı durdurur."""
    adaylar = [s for s in satirlar if s["ay"] < onceki]
    farklar = [s["ay"] for s in adaylar if s["durum"] == DURUM_FARK]
    if farklar:
        return [], (f"kırpma REDDEDİLDİ — şu aylarda arşiv/defter İÇERİK olarak EŞLEŞMİYOR "
                    f"(FARK): {', '.join(sorted(farklar))}. Hiçbir ay kırpılmadı; önce FARK'ı "
                    f"çözün (`.yeni` dosyalarını inceleyin).")
    hazir = [s["ay"] for s in adaylar if s["durum"] in (DURUM_YAZILDI, DURUM_ATLANDI)]
    return sorted(hazir), None


def kirp_uygula(con: duckdb.DuckDBPyConnection, dosya: pathlib.Path, hedef: pathlib.Path,
                hedefler: list[str], defterdeki: dict[str, int],
                bozuk_once: int) -> tuple[dict | None, str | None]:
    """DOĞRULANMIŞ `hedefler` aylarını defterden KALICI olarak düşürür. Dönüş: (rapor, None)
    başarıda; (None, gerekçe) İÇ DOĞRULAMA tutarsızsa — bu durumda hiçbir şey silinmez, tmp
    dosya (varsa) temizlenir, ORİJİNAL DOSYAYA DOKUNULMAZ.

    KALDIRMA KÜMESİ ARŞİVİN KENDİSİNDEN OKUNUR (jsonl'den YENİDEN sorgulanmaz): her hedef ayın
    `ham` satırları parquet dosyasından bir `Counter`e toplanır, sonra ORİJİNAL dosyanın HAM
    satırları (strip edilmiş) bu sayaçla eşleştirilir — eşleşen satır (ve yalnız o kadarı, tekrar
    eden satırlar için de) DÜŞÜRÜLÜR. Bu, "arşiv içerik olarak eşleşiyor" hükmünü (ay_isle'nin
    zaten verdiği) satır-metni düzeyinde TEKRAR sınar: `ham` DuckDB'nin `read_json_objects`
    çıktısıdır ve İÇERİK eşitliği garantilidir ama METİN eşitliği (biçimsel boşluk) garanti
    DEĞİLDİR (`ops/olay_sikistir.py` üst başlığı, "ARŞİVİN ŞEKLİ" bölümü) — bu yüzden aşağıda
    kaldırılan satır SAYISI beklenenle (arşivdeki satır sayısı) kıyaslanır; sapma varsa hiçbir
    şey yazılmaz (metin eşleşmesi arşiv sayımıyla tutarsız demektir)."""
    kaldirilacak: collections.Counter = collections.Counter()
    for ay in hedefler:
        p = hedef / f"{ay}.parquet"
        for (ham,) in con.execute(
                f"SELECT ham FROM ({olay_sorgu.parquet_kaynak_sql([p])}) AS _p "
                "WHERE ay = ?", [ay]).fetchall():
            kaldirilacak[ham] += 1

    kalan_sayac = collections.Counter(kaldirilacak)
    tutulan: list[str] = []
    kaldirilan_n = 0
    with open(dosya, encoding="utf-8") as f:
        for satir in f:
            anahtar = satir.strip()
            if anahtar and kalan_sayac.get(anahtar, 0) > 0:
                kalan_sayac[anahtar] -= 1
                kaldirilan_n += 1
                continue
            tutulan.append(satir)

    beklenen_kaldirilan = sum(defterdeki.get(ay, 0) for ay in hedefler)
    if kaldirilan_n != beklenen_kaldirilan:
        return None, (f"İÇ DOĞRULAMA TUTARSIZ — satır-metni eşleşmesiyle kaldırılan satır sayısı "
                      f"({kaldirilan_n}) arşivdeki beklenen sayıdan ({beklenen_kaldirilan}) "
                      f"FARKLI; hiçbir şey silinmedi (bkz. fonksiyon docstring'i).")

    hedef.mkdir(parents=True, exist_ok=True)
    fd, tmp_adi = tempfile.mkstemp(dir=str(dosya.parent), prefix=f".{dosya.name}-kirpma-",
                                    suffix=".tmp")
    tmp_yolu = pathlib.Path(tmp_adi)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as tf:
            tf.writelines(tutulan)
            tf.flush()
            os.fsync(tf.fileno())

        # İKİNCİ (BAĞIMSIZ) DOĞRULAMA: tmp dosya DuckDB ile YENİDEN taranır. Hedeflenen
        # aylardan HİÇBİRİ kalmamalı, bozuk satır sayısı DEĞİŞMEMELİ, toplam GEÇERLİ satır
        # beklenenle eşitlenmeli. Satır-metni eşleşmesindeki olası bir körlüğü (normalize
        # edilmiş boşluk gibi) BURADA yakalar — kabul ancak bu da geçerse olur.
        yeni_ay_satirlari = con.execute(
            f"SELECT ay, count(*) FROM ({olay_sorgu.jsonl_kaynak_sql(tmp_yolu)}) "
            "AS _k GROUP BY ay").fetchall()
        yeni_toplam = sum(int(n) for _, n in yeni_ay_satirlari)
        yeni_hedef_aylar = {str(ay) for ay, _ in yeni_ay_satirlari if ay is not None} & set(hedefler)
        yeni_bozuk = olay_sorgu.bozuk_sayimi(con, tmp_yolu)

        toplam_once = sum(defterdeki.values())
        # `defterdeki` yalnız AY'A ATANABİLEN satırları taşır (main()'deki `ay_satirlari`dan,
        # ay IS NOT NULL süzgeciyle) — AYSIZ satırlar kırpmadan ETKİLENMEZ, toplam beklentiye
        # dahil edilmez (onlar zaten `tutulan`da kalır, kaldırma kümesine hiç girmezler).
        beklenen_toplam = toplam_once - beklenen_kaldirilan

        if yeni_hedef_aylar or yeni_toplam != beklenen_toplam or yeni_bozuk != bozuk_once:
            return None, (
                f"İÇ DOĞRULAMA (ikinci geçiş) TUTARSIZ — hedef aylardan kalan: "
                f"{sorted(yeni_hedef_aylar) or 'yok'}; yeni toplam {yeni_toplam} "
                f"(beklenen {beklenen_toplam}); bozuk satır {yeni_bozuk} (önceki {bozuk_once}). "
                f"Hiçbir şey silinmedi.")

        once_bayt = dosya.stat().st_size
        os.replace(tmp_adi, dosya)
        try:
            dizin_fd = os.open(str(dosya.parent), os.O_RDONLY)
            try:
                os.fsync(dizin_fd)
            finally:
                os.close(dizin_fd)
        except OSError:  # sessiz-yutma: dizin fsync bazı dosya sistemlerinde desteklenmez, veri zaten os.replace ile atomik taşındı — bu yalnız durabilite için EK bir katman
            pass
    except Exception:
        if tmp_yolu.exists():
            try:
                tmp_yolu.unlink()
            except OSError:  # sessiz-yutma: temizlik denemesi — asıl hata zaten yukarı fırlatılıyor
                pass
        raise

    sonra_bayt = dosya.stat().st_size
    return {"kaldirilan_aylar": hedefler, "kaldirilan_satir": kaldirilan_n,
            "once_bayt": once_bayt, "sonra_bayt": sonra_bayt}, None


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
    a.add_argument("--kirp", action="store_true",
                   help="sıkıştırdıktan SONRA doğrulanmış eski ayları (cari+önceki ay hariç) "
                        "jsonl'den DÜŞÜR (varsayılan KAPALI; `--ay` ile birlikte kullanılamaz)")
    a.add_argument("--zorla", action="store_true",
                   help="`--kirp` ile: worker aktif/ölçülemez olsa bile kırpmayı ZORLA (yalnız "
                        "bakım penceresinde kullan)")
    return a


def main(argv: list[str] | None = None) -> int:
    args = _ayristirici().parse_args(argv)

    if not args.dosya.exists():
        print(f"HATA: olay defteri bulunamadı: {args.dosya}", file=sys.stderr)
        return 2

    if args.kirp and args.ay is not None:
        print("HATA: `--kirp` ile `--ay` birlikte kullanılamaz — kırpma TÜM defterin retention "
              "penceresiyle ilgilidir (cari+önceki ay hariç HEPSİ), tek bir ayı hedeflemez. "
              "Yalnız bir ayı sıkıştırmak istiyorsan `--kirp` VERME.", file=sys.stderr)
        return 2

    # TEK `simdi` — `cari_ay`/`onceki_ay` AYNI ANDAN türer (ay sınırında iki ayrı `now()` çağrısı
    # teorik olarak farklı ay verebilirdi; bu, o teorik yarışı kapatır).
    simdi_dt = _dt.datetime.now(_dt.timezone.utc)
    simdiki = cari_ay(simdi_dt)
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

        if not args.kirp:
            return 3 if gerekceler else 0

        # ------------------------------------------------------------------------------------
        # KIRPMA — yalnız `--kirp` verildiğinde buraya girilir. Sıkıştırma sonuçları (`satirlar`)
        # zaten hesaplandı; kırpma bunların ÜZERİNE ek bir adımdır, sıkıştırmayı TEKRARLAMAZ.
        #
        # BEDEL/BİLİNEN SINIR: `--kirp` verildiğinde çıkış kodu ARTIK kırpmanın kendi hükmünü
        # taşır (0=başarılı/yapılacak-ay-yok, 5=reddedildi) — kırpma HEDEFİ OLMAYAN bir ayda
        # (örn. `onceki`nin kendisinde) bulunan bir FARK, `gerekceler` üzerinden stderr'e YİNE
        # basılır (yukarıdaki döngü) ama tek başına rc'yi 3'e ÇEVİRMEZ. Sessiz DEĞİL (sinyal
        # stderr'de duruyor), ama İKİ ayrı hükmü TEK exit kodunda taşıyamıyoruz — bu turun
        # kapsamı dışında bırakıldı (nadir vaka: kırpma hedefi olmayan bir ayın SONRADAN
        # değişmesi).
        # ------------------------------------------------------------------------------------
        onceki = onceki_ay(simdi_dt)
        hedefler, red_gerekce = kirpma_hedeflerini_belirle(satirlar, onceki)
        if red_gerekce:
            print(f"HATA: kırpma REDDEDİLDİ (olay_kirpma_reddedildi) — {red_gerekce}",
                  file=sys.stderr)
            return 5

        if not hedefler:
            print(f"KIRPMA: kaldırılacak ay yok (defter zaten cari+önceki ayı — {onceki} ve "
                  f"sonrası — taşıyor, ya da eski aylar henüz arşive alınmadı).", file=sys.stderr)
            return 0

        if args.kuru:
            print(f"KIRPMA ÖNİZLEME (kuru koşum, HİÇBİR ŞEY silinmedi): şu aylar "
                  f"KALDIRILACAK: {', '.join(hedefler)}", file=sys.stderr)
            return 0

        aktif = worker_aktif_mi()
        if aktif is not False and not args.zorla:
            durum_metni = "AKTİF" if aktif else "ÖLÇÜLEMEDİ (yerel makine — systemctl yok/beklenmeyen çıktı)"
            print(f"HATA: kırpma REDDEDİLDİ (olay_kirpma_reddedildi) — worker durumu: "
                  f"{durum_metni}. Eşzamanlı yazıcıyla (`append_jsonl`) çakışma riski. Yalnız "
                  f"bakım penceresinde ve worker DURGUNKEN kırp; ölçüm/zorlama için `--zorla` "
                  f"(yalnız bakım penceresinde kullan).", file=sys.stderr)
            return 5

        bozuk_once = olay_sorgu.bozuk_sayimi(con, args.dosya)
        rapor, ic_gerekce = kirp_uygula(con, args.dosya, hedef, hedefler, defterdeki, bozuk_once)
        if ic_gerekce:
            print(f"HATA: kırpma REDDEDİLDİ (olay_kirpma_reddedildi) — {ic_gerekce}",
                  file=sys.stderr)
            return 5

        manifest_kayitlar = {}
        kirpma_ts = _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")
        for ay in hedefler:
            p = hedef / f"{ay}.parquet"
            ay_sayi, ay_damga = olay_sorgu.ay_damgasi(con, olay_sorgu.parquet_kaynak_sql([p]), ay)
            manifest_kayitlar[ay] = {"satir": ay_sayi, "damga": ay_damga, "dosya": str(p),
                                     "kirpma_ts": kirpma_ts}
        manifest_guncelle(hedef, manifest_kayitlar)

        print(f"KIRPILDI: {', '.join(rapor['kaldirilan_aylar'])} — "
              f"{rapor['kaldirilan_satir']} satır düşürüldü; defter {rapor['once_bayt']} → "
              f"{rapor['sonra_bayt']} bayt (manifest: {manifest_yolu(hedef)})", file=sys.stderr)
        return 0
    finally:
        con.close()


if __name__ == "__main__":
    sys.exit(main())
