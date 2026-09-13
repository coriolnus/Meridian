"""meridian/olaylar.py — OLAY DEFTERİNİN BİRLEŞİK GÖRÜNÜMÜ (cari `events.jsonl` + aylık parquet
arşivi, TSK-137b / TSK-020 [UYGULA-2] adım-3, 2026-09-05).

NEDEN VAR. `ops/olay_sikistir.py --kirp` (adım-3) parquet'e ALINMIŞ VE DOĞRULANMIŞ geçmiş ayları
`state/events.jsonl`den DÜŞÜRÜR — kırpma sonrası jsonl yalnız CARİ AY + ÖNCEKİ AYI taşır (≥30 gün
garantisi). `limit=None` çağıran okuyucular (tüm tarihi isteyenler: `watchdog.integrity_report`,
`selfreview.build`, `ops/alarm_backlog_digest.py`) kırpmadan SONRA `store.read_jsonl("events.jsonl")`
ile çağırmaya devam ederse artık YARIM bir defter görürler — "tüm tarih" iddiası sessizce YALANA
döner. `tum_olaylar()` bu okuyucuların YENİ tek girişidir: jsonl + arşiv aylarını BİRLEŞTİRİR, kırpma
öncesi/sonrası AYNI SONUCU üretir (çivi: `tests/test_olay_kirpma_v415.py`).

"PARQUET KAZANIR" KURALI — `ops/olay_sorgu.py`DEKİ KURALLA AYNI, KOPYA DEĞİL BAĞIMSIZ UYGULAMA
(TEK GÖVDE BURADA MÜMKÜN DEĞİL). `ops/olay_sorgu.py` `meridian`ı ASLA import ETMEZ — bu, obs
sızıntısı kapısıdır ve `tests/test_olay_sorgu_v355.py::test_kaynakta_meridian_importu_yok` +
`test_gercek_kosumda_meridian_modulu_yuklenmez` (aynısı `test_olay_sikistir_v379.py`de) tarafından
STATİK + DAVRANIŞSAL olarak çivilenmiştir: pytest DIŞI koşan bir CLI aracı `meridian.obs`a ulaşırsa
canlı deftere YAZAR (3 vaka, 2026-08-30). Bu modül TERSİNE `meridian.store`/`meridian.config`e
bağlıdır (motorun "birleşik görünüm" ihtiyacı budur) — yani iki gövdeyi TEK gövdeye indirmek ya
CLI aracının meridian'a bağlanmasını (kapıyı kırar) ya da bu modülün ops/ scriptini import etmesini
(katman yönü ters döner — motor kendi üstündeki bir betiği import ETMEMELİDİR; bunu bugün
import-linter DEĞİL, v470'in kaynak-metni taraması denetler — `[tool.importlinter]` `ops`a değinmez) gerektirirdi. İkisi de
mevcut, korunan bir sözleşmeyi kırar. Bu yüzden İKİ AYRI GÖVDE, AYNI KURALI ayrı ortamlarda
(CLI'nin kendi bağımsız DuckDB bağlantısı / motorun paylaşılan `store` okuması) uygular — TEK-KAYNAK
YASASININ "kopya kaçınılmazsa türetme + ayrışma çivisi" istisnası budur. Ayrışma riski
`tests/test_olay_kirpma_v415.py`de ÖLÇÜLÜR: kırpma öncesi tam liste == `tum_olaylar()` çıktısı,
birebir (tekilleştirme dahil).

DUCKDB ZORUNLU BAĞIMLILIK, İSTEĞE BAĞLI DEĞİL (ölçüldü 2026-09-05): `pyproject.toml`de
`duckdb>=1.5` ANA bağımlılıktır (TSK-020 adım-1'de, 2026-09-01 aynı gün ana bağımlılığa taşındı) ve
kurulu sürüm 1.5.5'tir (`--python -c "import duckdb"` başarılı). `pyarrow` KURULU DEĞİL ve
`pyproject.toml`de HİÇ GEÇMİYOR — bu yüzden pyarrow geri-düşüş yolu YAZILMADI (kurulu olmayan bir
bağımlılık eklemek D2 kararının açıkça yasakladığı şey). `import duckdb` bu dosyanın TEPESİNDE
KOŞULSUZDUR: duckdb bir gün gerçekten kurulu değilse modülün KENDİSİ ImportError ile düşer — bu,
istenen FAIL-LOUD davranışın ta kendisidir (`None` dönüp "tam tarih" iddiasını sessizce yarım
bırakmak YERİNE, arşiv okunamadığını GÖRÜNÜR şekilde patlatmak).

ÇIKTI ŞEMASI `store.read_jsonl`İN ÜRETTİĞİ LİSTEYLE AYNIDIR: satır başına HAM sözlük (JSON'un
ayrıştırılmış hâli), sütunlu bir DuckDB satırı DEĞİL. Mevcut okuyucular listeleri `e.get(...)` ile
AYNEN kullanmaya devam eder — imza/çıktı şeması DEĞİŞMEZ (D2 kararı).

SIRALAMA: çıktı `ts` alanına göre ARTAN (en eskiden en yeniye) sıralıdır. `store.read_jsonl`in
DOĞAL (dosya-sırası) davranışıyla AYNI SONUCU verir (obs.py olayları HER ZAMAN artan ts ile ekler),
ama garantiyi dosya sırasına DEĞİL AÇIK SIRALAMAYA bağlar: çok-kaynaklı birleşimde (parquet
dosyaları + jsonl) dosya okuma sırası TEK BAŞINA bu garantiyi VERMEZ (DuckDB `read_parquet`
çok-dosyalı okumada satır sırasını garanti ETMEZ). `ts`i olmayan/boş satır en başa düşer (boş
dize < her ISO-8601 tarihi) — bu satırlar `ts`siz olduğu için zaten "ne zaman" sorusuna cevap
vermiyorlardı, konumları BİLGİ TAŞIMAZ.

`baslangic`/`bitis` (ISO-8601, dahil sınırlar) İSTEĞE BAĞLI son-işlem süzgeçleridir — BİRLEŞTİRME
SONRASI uygulanır (pushdown YOK: hangi parquet dosyasının okunacağına karar vermez). BEDEL: geniş
bir arşivde dar bir tarih aralığı istense bile TÜM arşiv dosyaları okunur — bu modül "yeni, küçük"
kalsın diye BİLİNÇLİ bir basitleştirmedir; bugünkü dört çağıran (hiçbiri bu iki parametreyi
KULLANMIYOR, tam tarih istiyorlar) için maliyet sıfırdır."""
from __future__ import annotations

import datetime as _dt
import json
import os
import pathlib
import re

import duckdb

from . import config, store

_EVENTS = "events.jsonl"
_ARSIV_ALT_DIZIN = "olaylar"
_UTC = _dt.timezone.utc

#: BELLEK VE İPLİK TAVANI — ÜÇÜNCÜ KOPYA, BEYANLI (TSK-183, 2026-09-13).
#:
#: ÖLÇÜLEN BOŞLUK: bu bağlantı `duckdb.connect()` varsayılanıyla açılıyordu — `memory_limit`
#: sistem RAM'inin ~%80'i, `threads` çekirdek sayısı, `TimeZone` MAKİNENİN yereli (ölçüldü,
#: duckdb 1.5.5, bu makine: '6.3 GiB' / 8 / 'Europe/Istanbul'). Bu kod CANLI uvicorn işçisinin
#: ipliğinde koşar: `tum_olaylar()`u `watchdog.integrity_report`, `selfreview.build` ve
#: `ops/alarm_backlog_digest.py` çağırır. A1 dört çekirdeklidir ve `serve.sh` TEK işçi koşar —
#: tavansız bir arşiv taraması panonun tamamını cevapsız bırakabilirdi. `threads=1` gerekçesi
#: `meridian/sohbet.py::SORGU_IPLIK_TAVANI` ile AYNIDIR: tek işçinin ipliği dört çekirdeği
#: kendi okuması için kapatmamalı. BEDELİ (bedel yasası): büyük bir tarama artık TEK iplikte
#: koşar — dört-çekirdekli varsayılana göre en kötü ~4× yavaş; bugünkü yük (A1 2026-09-13:
#: arşiv 724 KB + defter 19,5 MB) için ölçülebilir fark beklenmez, ölçülmedi (None); yük
#: büyürse `OLAYLAR_IPLIK` benzeri bir env kanalı açılır, sabit sessizce yükseltilmez.
#:
#: TEK-KAYNAK İSTİSNASI, BEYANLI — ÜÇ TAVAN, ÜÇ KARAR, KOPYA DEĞİL:
#:   * `ops/olay_sorgu.py::BELLEK_TAVANI` (`OLAY_SORGU_BELLEK`, 2GB) operatörün ELLE koşturduğu
#:     CLI'ındır ve bar arşivi araçlarıyla paylaşılır — tabanı bilerek GENİŞTİR.
#:   * `meridian/sohbet.py::SORGU_BELLEK_TAVANI` (`SOHBET_SQL_BELLEK`, 512MB) MODEL yazımı SQL'i
#:     canlı istek ipliğinde koşturur — bilerek EN DARDIR.
#:   * BURASI motorun kendi defter okumasıdır: girdi jsonl + aylık parquet arşividir (olay
#:     defteri 27–56k satır/ay), sorgu iki VARCHAR sütunun düz taramasıdır. 1GB sohbetle aynı
#:     sınıfta, CLI'dan dardır — ve duckdb varsayılanının çok altındadır.
#: SABİT İTHAL EDİLEMEZ, BEYAN ŞERHLEDİR: `ops/olay_sorgu.py` `meridian`ı import ETMEZ (obs
#: sızıntısı kapısı, çivi v355) ve bu modül de `ops/` betiğini import ETMEZ (katman yönü:
#: motor `ops/` betiğini ithal etmez — denetimi v470 kaynak-metni taraması, import-linter değil). Yani
#: üç liste YAPISAL olarak ayrıdır; ayrışma ÖLÇÜLÜR: `tests/test_olaylar_tavan_v470.py`
#: (biçim deseni eşitliği + üç bağlantının çekirdek ayar eşitliği + karşılıklı atıf).
BELLEK_ENV_AD = "OLAYLAR_BELLEK"
BELLEK_VARSAYILAN = "1GB"
IPLIK_TAVANI = 1

#: BİÇİM DOĞRULAMASI — `ops/olay_sorgu.py::BELLEK_BICIMI` İLE AYNEN AYNI DESEN (ithal edilemez;
#: yukarıdaki yön yasağı). İki ÖLÇÜLMÜŞ arıza sınıfını tutar (v355 ölçümü, duckdb 1.5.5):
#: '2 gigabayt' → `SET memory_limit` DuckDB hatası verir; '-2GB' → duckdb KABUL EDER ve tavan
#: "16383.9 PiB" olur, yani KORUMA SESSİZCE KAPANIR (sinsi olan budur). `\s*` grupları süs
#: değildir: ' 2 GB ' duckdb'ce kabul edilir, reddedilseydi kapı meşru bir değeri kırardı.
BELLEK_BICIMI = re.compile(r"^\s*\d+(\.\d+)?\s*(KB|MB|GB|TB|KiB|MiB|GiB)\s*$", re.IGNORECASE)

# `ops/olay_sorgu.py::SERTLESTIRME` İLE AYNI DEĞERLER (ölçüldü, duckdb 1.5.5) — bağımsız
# uygulama, aynı gerekçe: `temp_directory` varsayılanı CWD-göreli '.tmp' (operatörün/servisin
# çalıştığı dizine sessizce döker), eklenti oto-indirme varsayılanı TRUE (yerel bir defter
# okuyucusunun ağ yüzeyi olmamalı).
# `TimeZone` 2026-09-13'te EKLENDİ ve BUGÜNKÜ DAVRANIŞI DEĞİŞTİRMEZ — ölçüldü: bu bağlantının
# TEK sorgusu `SELECT ay, ham FROM read_parquet(...)`tır, iki sütun da VARCHAR'dır ve SQL
# tarafında hiçbir `ts` aya çevrilmez (ay/UTC dönüşümü `_ay_anahtari`de, saf Python'da). O hâlde
# NEDEN: ayar ÜÇ YÜZEYİN PAYLAŞTIĞI ÇEKİRDEĞİN parçasıdır (`ops/olay_sorgu.py::SERTLESTIRME`
# ve onun üzerinden `meridian/sohbet.py`) ve çekirdeğin AYNI olması ayrışma çivisinin ölçtüğü
# şeydir; ayrıca bu modülde bir gün SQL'e taşınacak bir ay/ts süzgeci (bugün son-işlem, saf
# Python) makinenin yerel saatiyle konuşup iki makinede iki farklı ay üretemez.
_SERTLESTIRME = (
    "SET temp_directory=''",
    "SET autoinstall_known_extensions=false",
    "SET autoload_known_extensions=false",
    "SET TimeZone='UTC'",
)


def _arsiv_dizini() -> pathlib.Path:
    """Arşiv dizini `config.STATE`in YANINDADIR — HER ÇAĞRIDA taze okunur (sandbox'lar
    `config.STATE`i monkeypatch eder; yolu import anında dondurmak sandbox'ları canlı
    `state/`e yazdırırdı — bkz. `store._state` aynı gerekçe)."""
    return config.STATE / _ARSIV_ALT_DIZIN


def _parquet_dosyalari() -> list[pathlib.Path]:
    """Arşivdeki `*.parquet` dosyaları (ada göre sıralı). Dizin yoksa BOŞ liste — hata DEĞİL:
    sıkıştırıcı hiç koşmamış olabilir. `.yeni` uzantılı FARK adayları BİLEREK dışarıdadır
    (`ops/olay_sikistir.py` emsali: onlar operatörün kıyaslaması için duran adaylardır)."""
    d = _arsiv_dizini()
    if not d.is_dir():
        return []
    return sorted(p for p in d.glob("*.parquet") if p.is_file())


def _sql_metni(yol: pathlib.Path) -> str:
    return "'" + str(yol).replace("'", "''") + "'"


def _bellek_tavani() -> str:
    """Yürüyen bellek tavanı. `OLAYLAR_BELLEK` ÇAĞRI ANINDA okunur; biçimi tutmuyorsa UYARI
    yazılır ve VARSAYILANA düşülür — istisna ATILMAZ.

    NEDEN İSTİSNA DEĞİL (kardeşinden BİLEREK ayrılan tek nokta): `ops/olay_sorgu.py` bir
    KÜTÜPHANE+CLI ikilisidir ve bozuk tavanda `BellekTavaniHatasi(ValueError)` atar — orada
    çağıran ya operatörün kabuğudur ya da `meridian/sohbet.py`in `except Exception` kalkanıdır.
    BURASI canlı teşhis yüzeyinin OKUMA yoludur: `watchdog.integrity_report` bir istisnayı
    yalıtır ama dedektörleri arşivsiz yavaş yola düşürür, `selfreview.build` ve
    `ops/alarm_backlog_digest.py` ise RAPORU tamamen kaybeder. Bir ortam değişkeni yazım
    hatasının bedeli "haftalık rapor üretilmedi" olmamalı.
    DÜŞÜŞ BEYANLIDIR, SESSİZ DEĞİL (uydurma yasağı + Yasa 4): tavan SINIRSIZA değil
    VARSAYILANA düşer ve `obs.warn` ADI, VERİLEN DEĞERİ ve BEKLENEN BİÇİMİ taşır — operatör
    neyi nasıl düzelteceğini uyarının kendisinden okur. Değer MASKELENMEZ: bu bir ölçü birimi
    dizgesidir, sır değildir.
    ÇAĞRI ANINDA OKUMA, import anında DEĞİL: tavan `_baglanti_kur`un her çağrısında ölçülür,
    yani birim dosyasında değişen bir değer süreç yeniden başlar başlamaz yürür ve çivi tarafı
    modülü yeniden yüklemek zorunda kalmaz (import anında yazılan bir `obs.warn` ise motorun
    her import zincirine sızardı)."""
    deger = os.environ.get(BELLEK_ENV_AD, BELLEK_VARSAYILAN)
    if BELLEK_BICIMI.match(deger):
        return deger
    from . import obs
    obs.warn("olaylar_bellek_tavani_bicimsiz", deger=deger,
             beklenen="<sayı><birim>, birim KB|MB|GB|TB|KiB|MiB|GiB (örn. '1GB', '512MB')",
             dusulen=BELLEK_VARSAYILAN, degisken=BELLEK_ENV_AD,
             detail=f"{BELLEK_ENV_AD} biçimi tanınmadı — DuckDB bağlantısı VARSAYILAN tavanla "
                    f"({BELLEK_VARSAYILAN}) açıldı, tavansız DEĞİL. İşaretli değer ('-2GB') "
                    f"DuckDB'ce kabul edilir ve tavanı sessizce yok ederdi.")
    return BELLEK_VARSAYILAN


def _kaynak_tavanlari() -> tuple[str, ...]:
    """Bağlantının KAYNAK tavanları — `_SERTLESTIRME`den AYRI durur çünkü değerleri ÇAĞRI
    ANINDA (ortamdan) ölçülür; çekirdek sertleştirme ise donuktur ve üç yüzeyde AYNIDIR."""
    return (f"SET memory_limit='{_bellek_tavani()}'", f"SET threads={int(IPLIK_TAVANI)}")


def _baglanti_kur() -> duckdb.DuckDBPyConnection:
    """Bellek içi bağlantı: çekirdek sertleştirme + kaynak tavanları (yukarıdaki gerekçeler).

    BEDEL BEYANI (Bedel yasası). Tavan bedava değildir: RAM'e sığmayan MEŞRU bir arşiv taraması
    artık yavaşlamaz, `duckdb.OutOfMemoryException` ("Out of Memory Error…") ile DÜŞER —
    `temp_directory` BOŞ olduğu için diske taşma yolu da kapalıdır (ölçüldü, duckdb 1.5.5: dar
    tavanda taşan sorgu tam bu istisnayı atar ve mesajı geçici dizin olmadığını söyler).
    İstisna `tum_olaylar`dan çağırana AYNEN çıkar — yutulmaz, yarım liste dönmez (Yasa 4: yarım
    bir defter 'tüm tarih' iddiasını sessizce yalana çevirirdi; çivi v470).
    OKUYUCULAR BUNU NASIL KARŞILIYOR — ÖLÇÜLDÜ (2026-09-13, üç çağıranın üçü de GÖRÜNÜR):
      * `watchdog.integrity_report`: paylaşılan okuma try/except ile yalıtılmış →
        `obs.warn("integrity_shared_events_read_failed")` + her dedektör kendi (arşivsiz,
        kırpılmış) okumasına düşer. Hüküm üretilir, kapsam kaybı UYARIYLA görünür.
      * `selfreview.build`: kendi kalkanı YOK. Haftalık yolda `selfreview.weekly()` onu
        `mechanism_failed("self_review", …)` ile ALARMLAR ve yükseltir; `scheduler` da
        `obs.warn("selfreview_failed")` yazar ve haftayı 'yapıldı' İŞARETLEMEZ (yeniden dener).
        Emekli `/api/selfreview` ucunda ise istisna HTTP 500 olur — `/api/diagnostics`
        `self_review.json`ı dosyadan okur, bu yoldan ETKİLENMEZ.
      * `ops/alarm_backlog_digest.py`: `ozet_kur()` `main()`in kalkanı dışındadır → ham
        traceback + çıkış 1, yani aracın 0/1/2 sözleşmesinin DIŞINDA bir kod (operatörün
        terminalinde GÖRÜNÜR ama gerekçesiz). AÇIK KALEM, bu turun kapsamı DEĞİL.
    GERİ ALMA YOLU KOD DEĞİŞTİRMEDEN AÇIKTIR: `OLAYLAR_BELLEK=4GB` (systemd birim dosyasında
    `Environment=`), süreç yeniden başlar başlamaz yürür."""
    con = duckdb.connect()
    for s in _SERTLESTIRME + _kaynak_tavanlari():
        con.execute(s)
    return con


def _parquet_oku(dosyalar: list[pathlib.Path]) -> tuple[list[dict], set[str]]:
    """Arşivdeki TÜM satırları (ayrıştırılmış sözlük olarak) + arşivde bulunan AY kümesini
    döndürür. Ay kümesi jsonl tarafını süzmek için kullanılır (parquet kazanır)."""
    if not dosyalar:
        return [], set()
    con = _baglanti_kur()
    try:
        liste = "[" + ", ".join(_sql_metni(p) for p in dosyalar) + "]"
        satirlar = con.execute(f"SELECT ay, ham FROM read_parquet({liste})").fetchall()
    finally:
        con.close()
    aylar = {str(ay) for ay, _ in satirlar if ay is not None}
    olaylar = [json.loads(ham) for _, ham in satirlar]
    return olaylar, aylar


def _ay_anahtari(ts) -> str | None:
    """`ts`in UTC ayı (`AAAA-AA`) — `ops/olay_sorgu.py::ay_ifadesi`nin SQL kuralıyla AYNI
    semantiği saf Python'da uygular (bkz. modül başlığı: tek gövde iki tarafta mümkün değil).

    Naif (ofsetsiz) `ts` UTC SAYILIR (DuckDB bağlantısının `TimeZone='UTC'` sertleştirmesiyle
    aynı davranış — `ops/olay_sikistir.py` sertleştirmesi de bunu yapar). Ofsetli `ts` UTC'ye
    ÇEVRİLİR. Çözülemeyen/boş `ts` → None (uydurma yasağı): bu satırlar sıkıştırıcı tarafından
    da hiç arşive alınmaz, dolayısıyla hiçbir zaman jsonl'den süzülmemeleri GEREKİR — None
    döndürmek bunu `not in aylar` ile otomatik sağlar (None bir ay kümesinde asla YOKTUR)."""
    if not ts:
        return None
    try:
        d = _dt.datetime.fromisoformat(str(ts))
    except ValueError:  # sessiz-yutma: çözülemeyen ts UYDURULMAZ — None döner, bu satır ay kümesinde asla YOKTUR ve jsonl'den hiç süzülmez (docstring'teki uydurma yasağı)
        return None
    if d.tzinfo is None:
        d = d.replace(tzinfo=_UTC)
    else:
        d = d.astimezone(_UTC)
    return d.strftime("%Y-%m")


def tum_olaylar(baslangic: str | None = None, bitis: str | None = None) -> list[dict]:
    """Olay defterinin BİRLEŞİK (jsonl + parquet arşivi) görünümü — TAM TARİH, kırpmadan
    ETKİLENMEZ. `limit=None` okuyucuların (tüm tarih isteyenler) YENİ tek girişi.

    `baslangic`/`bitis` verilirse sonuç `ts >= baslangic` / `ts <= bitis` (ISO-8601 sözlüksel
    kıyas, `watchdog.events_since` ile aynı kural) ile süzülür — dahil sınırlar, ikisi de
    isteğe bağlı. Çağıran vermezse (bugünkü dört okuyucu böyle) TAM LİSTE döner."""
    dosyalar = _parquet_dosyalari()
    arsiv_olaylari, arsiv_aylari = _parquet_oku(dosyalar)

    guncel = store.read_jsonl(_EVENTS)
    if arsiv_aylari:
        # PARQUET KAZANIR: arşive alınmış her AY güncel defterden SÜZÜLÜR — çift sayım yok.
        # Kırpma (D1) sonrası bu satırlar zaten jsonl'de YOKTUR (fiziksel olarak silinmiş); bu
        # süzgeç kırpma ÖNCESİ geçiş dönemini (sıkıştırılmış ama henüz kırpılmamış ay) de
        # doğru ele alır — `ops/olay_sorgu.py`nin aynı kuralla çözdüğü GEÇİŞ senaryosu.
        guncel = [e for e in guncel if _ay_anahtari(e.get("ts")) not in arsiv_aylari]

    birlesik = arsiv_olaylari + guncel
    birlesik.sort(key=lambda e: str(e.get("ts") or ""))

    if baslangic is not None:
        birlesik = [e for e in birlesik if str(e.get("ts") or "") >= baslangic]
    if bitis is not None:
        birlesik = [e for e in birlesik if str(e.get("ts") or "") <= bitis]
    return birlesik
