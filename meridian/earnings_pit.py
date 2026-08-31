"""earnings_pit.py — kazanç raporunun NOKTA-ZAMANLI (PIT) arşivi: EDGAR 8-K dosyalama defteri.

Ne yapar: `research/edgar_facts/earnings_8k_tarihleri.csv` dosyasını (SEC EDGAR 8-K item 2.02
dökümü; `research/edgar_facts/betikler/` ile aylık tazelenir) okur ve tarihsel yolda sorulabilen
BİR soruyu cevaplar: "t seansında bu sembol bir kazanç raporunun ARDINDA mıydı — ve o rapor t
gününde GERÇEKTEN görünür müydü?". İkinci yarısı bu modülün bütün varlık sebebidir: arşiv her
satırda hem `report_date` (raporun ait olduğu gün) hem `filed` (SEC'e dosyalandığı gün) taşır,
yani görünürlük UYDURULMAZ, ÖLÇÜLÜR.

Neden ayrı bir modül: `earnings.days_since_report` aynı soruyu `state/earnings.csv` üzerinden
cevaplar ve o dosya bir PIT arşivi DEĞİL, bugünün ileri-pencere tazeleme önbelleğidir
(`earnings.takvim_ufku` docstring'i, kart EDG-2026-060). Tarihsel yeniden yürütmede o kaynağın
kullanılması `pitlaw.BILINEN_IHLALLER` altında ADIYLA sayılıydı (`backtest.py`, `cf_backfill.py`)
ve kayıt düzeltmenin iki yolunu yazıyordu: "ya çapa replay'de kesilir ya PIT arşivine bağlanır".
Bu modül İKİNCİ yoldur — ve yol 2026-08-31'de bağlandı: iki kayıt artık
`pitlaw.PIT_KORUMALI_ZINCIRLER`dedir (borç değil, KAPATILMIŞ yol), koruma `strategy`nin
`params["earnings.pit_arsiv"]` sevkidir ve bu modül o sevkin VARDIĞI kaynaktır
(`pitlaw.PIT_KAYNAKLAR` kaydı: `days_since_report_pit`).

Kilit girişler: `days_since_report_pit` (üç durumlu çapa), `arsiv_ufku` (kapsam + düşen satır
sayısı), `sayac_oku` / `sayac_sifirla` (üç durumun dağılımı), `clear_cache`.

ÜÇ DURUM VE NEDEN ÜÇ: `earnings.days_since_report` "o gün rapor yoktu" ile "o gün hakkında hiçbir
şey bilmiyoruz"u TEK False'a katlar; katlanan cevap sessizdir, çünkü çapayı ZORUNLU tutan bir
kurulum ikinci dünyada da ateşlemez ve dışarıdan "kurulum sinyal vermedi" gibi görünür. Burada
`None` ölçülemezliğin KENDİ değeridir (uydurma yasağı: sıfır ile "bilmiyorum" aynı şey değildir)
ve her çağrı üç kovadan birine sayılır — körlüğün belirtisi "hiçbir şey" olmasın diye.

MUHAFAZAKÂR GÖRÜNÜRLÜK (karttan, EDG-2026-062): `filed <= on_date - 1 gün`. Dosyalamanın KENDİ
günü DAHİL DEĞİLDİR. Gerekçe: 8-K'nın kabul saati (`acceptance`) çoğunlukla seans kapanışından
sonradır ve bu modül saat taşımaz; "aynı gün" saymak, kapalı-bar motoruna o seansın kararında
henüz var olmayan bir bilgiyi sızdırma riskidir. Eşitlik sınırı bu yüzden çivilidir.

Değişmezler: ağsız ve determinist — yalnız depo içindeki statik CSV okunur, `state/` altına HİÇ
yazılmaz ve `state/` altından HİÇ okunmaz. `meridian.obs`a ULAŞMAZ (import zinciri `config` ile
sınırlıdır ve çivi bunu statik olarak ölçer): bu modül tarihsel yeniden yürütmenin içinden,
pytest dışı koşumlarda da çağrılabilir olmalı ve canlı defteri kirletmemelidir.

Okur/yazar: `research/edgar_facts/earnings_8k_tarihleri.csv`i okur (mtime + YOL önbellekli),
hiçbir dosyaya yazmaz. Süreç-içi iki sayaç tutar ve ikisinin de okuyucusu vardır (Yasa 6):
`_dusen_satir` → `arsiv_ufku()["dusen"]`, `_SAYAC` → `sayac_oku()`."""
from __future__ import annotations

import csv
import datetime as dt
from pathlib import Path

from . import config

#: Arşivin yolu — MODÜL SABİTİ ve testlerin TEK enjeksiyon noktası
#: (`monkeypatch.setattr(earnings_pit, "ARSIV_YOLU", tmp)` + `clear_cache()`).
#: `config.ROOT`tan türetilir, yeniden hesaplanmaz: emsal `adapters/edgar_shares.SHARES_FILE`.
ARSIV_YOLU: Path = config.ROOT / "research" / "edgar_facts" / "earnings_8k_tarihleri.csv"

#: SYM -> [(report_date, filed), ...] — sıralı ve TEKİL.
_CACHE: dict[str, list[tuple[str, str]]] = {}
#: Önbellek anahtarı (yol, mtime). `earnings._load` YALNIZ mtime kullanır ve o KENDİ sorusu için
#: doğrudur (yol orada sabittir); burada yol TEST ENJEKSİYONUYLA değişir, dolayısıyla anahtara
#: girmek zorundadır — aksi hâlde aynı mtime'lı iki ayrı arşiv birbirinin yerine okunurdu.
_CACHE_ANAHTAR: tuple | None = None
#: Biçimsiz/eksik satır sayısı — SESSİZCE DÜŞMEZ, `arsiv_ufku()["dusen"]` onu okur (Yasa 6).
_dusen_satir: int = 0

#: YÜKLEME NESLİ — `_CACHE` içeriği her GERÇEKTEN değiştiğinde artar. `_CACHE_ANAHTAR` bu iş için
#: YETMEZ: `None` iki AYRI durumu birden kodlar (dosya yok · `clear_cache` çağrıldı), yani ona
#: bağlanan bir memo iki farklı arşivi aynı anahtar altında karıştırabilirdi. Nesil monotondur ve
#: yalnız içerik değişiminde artar → memo anahtarı olarak AYRIMSIZ değildir.
_NESIL: int = 0
#: `arsiv_ufku`nun O(n) türevinin memosu ve onu üreten nesil. Gerekçe `arsiv_ufku` docstring'inde.
_UFUK_MEMO: dict | None = None
_UFUK_MEMO_NESIL: int = -1

#: Üç durumun dağılımı. Sıfır ile "hiç sorulmadı" ayrı şeylerdir; toplam çağrı sayısı üçünün
#: toplamıdır ve `olculemedi` payı bu modülün KAPSAM ölçüsüdür.
_SAYAC: dict[str, int] = {"true": 0, "false": 0, "olculemedi": 0}
_DONUS: dict[str, bool | None] = {"true": True, "false": False, "olculemedi": None}


def _tarih(deger) -> dt.date | None:
    """ISO tarihi çözer; çözemezse None (istisna yükseltmez, varsayılan uydurmaz)."""
    try:
        return dt.date.fromisoformat(str(deger)[:10])
    except (ValueError, TypeError):  # sessiz-yutma: biçimsiz/eksik TEK tarih alanı; kayıp sessiz değildir — satır `_dusen_satir` sayacına düşer ve `arsiv_ufku()["dusen"]` onu okur
        return None


def _arsiv_yukle() -> dict[str, list[tuple[str, str]]]:
    """Arşivi mtime+YOL önbellekli okur: SYM -> [(report_date, filed), ...], sıralı ve tekil.

    Dosya yoksa boş sözlük (arıza değil: arşiv bu kurulumda yoksa cevap "ölçülemedi"dir).
    Dosya değişmediyse disk HİÇ okunmaz (`earnings._load` emsali).

    TEKİLLEŞTİRME ÖLÇÜLDÜ, VARSAYILMADI (2026-08-31): 17.535 ham satırın 17.407'si tekil
    (symbol, report_date, filed) üçlüsüdür — 128 satır birebir tekrardır (aynı raporun birden
    fazla 8-K düzeltmesi/eki). Tekrarı saymak `arsiv_ufku()["n_tarih"]`i etkilemez ama çapa
    döngüsünü boş yere gezdirirdi; `earnings._load`un `sorted(set(...))` emsali burada da geçerli.

    BİÇİMSİZ SATIR SESSİZCE DÜŞMEZ: sembolü boş ya da iki tarihinden biri çözülemeyen satır
    `_dusen_satir`a eklenir. DOSYANIN KENDİSİ okunamıyorsa istisna YÜKSELİR ve bu bilinçlidir —
    17 bin satırlık bir arşivin okunamamasını "ölçülemedi"ye çevirmek, tarihsel yürütmenin tamamını
    sessizce None'a düşürür ve o sessizlik tam olarak bu modülün var olma sebebine aykırıdır."""
    global _CACHE, _CACHE_ANAHTAR, _dusen_satir, _NESIL
    yol = Path(ARSIV_YOLU)
    if not yol.exists():
        # NESİL yalnız GEÇİŞTE artar: dosya yokken her çağrı `{}` atar, koşulsuz artırmak nesli
        # her çağrıda ilerletir ve memo HİÇ tutmazdı (memo sessizce ölü olurdu — ölçülmeyen bedel).
        if _CACHE or _CACHE_ANAHTAR is not None:
            _NESIL += 1
        _CACHE, _CACHE_ANAHTAR, _dusen_satir = {}, None, 0
        return _CACHE
    anahtar = (str(yol), yol.stat().st_mtime)
    if anahtar == _CACHE_ANAHTAR:
        return _CACHE
    kova: dict[str, set[tuple[str, str]]] = {}
    dusen = 0
    with yol.open(newline="", encoding="utf-8") as fh:
        for satir in csv.DictReader(fh):
            sym = (satir.get("symbol") or "").strip().upper()
            rd, fl = _tarih(satir.get("report_date")), _tarih(satir.get("filed"))
            if not sym or rd is None or fl is None:
                dusen += 1
                continue
            kova.setdefault(sym, set()).add((rd.isoformat(), fl.isoformat()))
    _CACHE = {sym: sorted(satirlar) for sym, satirlar in kova.items()}
    _CACHE_ANAHTAR, _dusen_satir = anahtar, dusen
    _NESIL += 1
    return _CACHE


def clear_cache() -> None:
    """Arşiv önbelleğini geçersiz kılar (bir sonraki `_arsiv_yukle()` diskten yeniden okur).
    Ufuk memosu da AÇIKÇA düşürülür: nesil zaten yeniden yüklemede artacaktır, ama `clear_cache`in
    sözleşmesi "önbellekleri düşür"dür ve o sözleşmenin dolaylı bir yan etkiye dayanması, memoyu
    sonradan başka bir yerden besleyen birinin sessizce bayat cevap almasına kapı açardı."""
    global _CACHE_ANAHTAR, _UFUK_MEMO, _UFUK_MEMO_NESIL
    _CACHE_ANAHTAR = None
    _UFUK_MEMO, _UFUK_MEMO_NESIL = None, -1


def _ufuk_turet(ars: dict) -> dict:
    """Ufkun O(n) TÜREVİ — `arsiv_ufku`nun memoize ettiği asıl iş. AYRI FONKSİYON OLMASI bilinçli:
    "yükleme başına bir kez koşuyor" iddiası ancak türev SAYILABİLİR bir yüzeyse çivilenebilir
    (çivi bunu monkeypatch ile sayar); gövdenin içinde kalsaydı iddia ölçülemez, yani beyan olurdu."""
    gunler = sorted({fl for satirlar in ars.values() for (_rd, fl) in satirlar})
    if not gunler:
        return {"ilk": None, "son": None, "n_tarih": 0, "n_sembol": len(ars),
                "dusen": _dusen_satir,
                "neden": "PIT kazanç arşivi BOŞ — ufuk ölçülemez (uydurma aralık yok)"}
    return {"ilk": gunler[0], "son": gunler[-1], "n_tarih": len(gunler),
            "n_sembol": len(ars), "dusen": _dusen_satir, "neden": None}


def arsiv_ufku() -> dict:
    """Arşivin KAPSADIĞI `filed` aralığı — `days_since_report_pit`in None'unun OKUYUCUSU (Yasa 6).

    `filed` üzerinden ölçülür, `report_date` üzerinden DEĞİL: sorulan soru "bu tarih hakkında
    bilgimiz var mıydı" ve bilginin var olma anı dosyalama anıdır. `dusen` alanı biçimsiz
    satırların sayısıdır — sıfırdan farklıysa arşivin biçimi kaymıştır.

    Boş arşivde `ilk`/`son` None ve `neden` doludur (`earnings.takvim_ufku` emsali): uydurma
    aralık yoktur.

    MEMOİZE (2026-08-31, EDG-2026-062 Görev 2 düzeltme turu — Rol-1 kararı). Türev O(n)'dir
    (17.407 satır üzerinde küme + ~2.988 günlük `sorted`) ve `days_since_report_pit` onu HER
    çağrıda soruyordu: ölçülen maliyet 0,52 ms/çağrı, cf ölçeğinde ~4-5 dk. Görev 3 bu yolu
    SICAK yapar (replay + cf'nin iki `scan_all` çağrısı), yani bedel ölçülüp bırakılamazdı.
    Türev artık YÜKLEME BAŞINA bir kez koşar (`_NESIL` anahtarlı memo; `clear_cache` düşürür).
    SÖZLEŞME BİREBİR AYNI: her çağrı yine `_arsiv_yukle()`den geçer (mtime değişimi hâlâ
    yakalanır) ve yine TAZE bir dict döner — memo kopyalanarak verilir, çağıran onu ezemez."""
    global _UFUK_MEMO, _UFUK_MEMO_NESIL
    ars = _arsiv_yukle()
    if _UFUK_MEMO is None or _UFUK_MEMO_NESIL != _NESIL:
        _UFUK_MEMO, _UFUK_MEMO_NESIL = _ufuk_turet(ars), _NESIL
    return dict(_UFUK_MEMO)


def _say(anahtar: str) -> bool | None:
    """Sayacı günceller ve o durumun dönüş değerini verir — üç kovanın TEK çıkış kapısı.
    Sayma ile dönme aynı satırda olur; ayrı olsalardı bir dal sessizce sayılmadan dönebilirdi."""
    _SAYAC[anahtar] += 1
    return _DONUS[anahtar]


def days_since_report_pit(ticker: str, on_date: str, max_days: int = 2) -> bool | None:
    """PIT çapası: `on_date` seansında `ticker` bir kazanç raporunun ardında MIYDI — ve o rapor
    o gün GERÇEKTEN görünür müydü? ÜÇ DURUM döner ve her çağrı `_SAYAC`a sayılır.

    None → ÖLÇÜLEMEDİ. Dört yolu vardır ve dördü de "rapor yok" DEĞİLDİR: `on_date` biçimsiz ·
        arşiv boş · `on_date` arşivin `filed` ufkunun DIŞINDA (arşivin başlamadığı ya da bittiği
        yer hakkında hüküm verilemez) · sembol arşivde HİÇ yok (kapsam dışı).
    True → ∃ satır: `0 <= (on_date - report_date).days <= max_days` VE `filed <= on_date - 1 gün`.
    False → sembol VAR, tarih ufkun İÇİNDE, eşleşen satır YOK — "rapor yok" ÖLÇÜLDÜ.

    `max_days` çağıranın penceresidir: PEAD ekranı geniş (ör. 35 gün), episodik pivot dardır.
    Geç dosyalama ikisini AYIRIR: `report_date=R, filed=R+5` satırında `on_date=R+1` cevabı
    False'tur (rapor henüz dosyalanmamıştı) ama `on_date=R+6` PEAD penceresinde True'dur.

    ÖLÇÜLMÜŞ SINIR — UFUK GLOBAL, KAPSAM SEMBOL-BAZLI: sembol arşivde varken kendi kapsaması
    başlamamışsa cevap False'tur (ölçüm 2026-08-31: CF penceresinde 1.238 satır; en sert vaka
    BLK — 8 satır hepsi 2024-10, 724 seans False, gerçekte 11 rapor). Sembol-bazlı ufuk AYRI
    tasarım kararıdır; kapsama eşiği (kart: ≥%95) bu sınıfı ölçer."""
    d = _tarih(on_date)
    if d is None:
        return _say("olculemedi")
    ufuk = arsiv_ufku()                      # `_arsiv_yukle`u da tetikler
    if ufuk["ilk"] is None:
        return _say("olculemedi")
    if not (_tarih(ufuk["ilk"]) <= d <= _tarih(ufuk["son"])):
        return _say("olculemedi")
    satirlar = _arsiv_yukle().get(str(ticker).upper())
    if not satirlar:
        return _say("olculemedi")
    # MUHAFAZAKÂR GÖRÜNÜRLÜK: dosyalamanın KENDİ günü DAHİL DEĞİL (modül başlığındaki gerekçe).
    gorunur_son = d - dt.timedelta(days=1)
    for rd, fl in satirlar:
        # Tarihlerin ISO geçerliliği `_arsiv_yukle` tarafından GARANTİ EDİLİR (biçimsizi `dusen`e
        # düşürür); burada bir istisna yakalamak ölü bir dal olurdu.
        rapor, dosyalama = dt.date.fromisoformat(rd), dt.date.fromisoformat(fl)
        if 0 <= (d - rapor).days <= max_days and dosyalama <= gorunur_son:
            return _say("true")
    return _say("false")


def sayac_oku() -> dict:
    """Üç durumun dağılımı — `_SAYAC`ın okuyucusu (Yasa 6). Kopya döner: çağıran sayacı ezemez."""
    return dict(_SAYAC)


def sayac_sifirla() -> None:
    """Sayaçları YERİNDE sıfırlar (yeni sözlük ATAMAZ: `_SAYAC`a tutulan referanslar kopmasın —
    `tests/conftest._MODUL_DURUMLARI` dersi)."""
    _SAYAC.update({"true": 0, "false": 0, "olculemedi": 0})
