"""earnings.py — the earnings blackout. A swing-momentum entry taken right into an earnings print
is a coin flip on a gap, not an edge (Hard Rule 7: no fantasy fills). If state/earnings.csv exists
(rows: ticker,date  — one scheduled report date per line, YYYY-MM-DD), a plan whose date falls within
BLACKOUT_DAYS *before* the next scheduled report is not armed. No CSV -> no-op, so the gate is present
and testable now and simply activates the day an earnings feed (FMP) writes the file. Deterministic,
network-free: it only reads the file it is handed."""
from __future__ import annotations
import csv
import datetime as dt

from . import config

BLACKOUT_DAYS = 5   # no fresh entry within this many calendar days before a scheduled report

# --------------------------------------------------------------------------------------------------
# TAZELEME PENCERESİ SABİTLERİ — "2 GÜN MARJ" BULGUSUNUN KALICI VE BEYANLI HÂLİ (2026-08-01)
# --------------------------------------------------------------------------------------------------
# BULGU (temizlik turu C-avı, ROADMAP §4-④; ölçüm, tahmin değil): tazeleme penceresi [bugün-7,
# bugün+14], kadans HAFTALIK, BLACKOUT_DAYS = 5. Normal işleyişte bir sonraki tazelemeden hemen
# ÖNCEKİ asgari ileri kapsama 14-7 = 7 gün olur; karartma 5 gün ister → marj yalnız 2 GÜN.
#
# KARAR (Rol-1, 2026-08-01 mikro-tur): İLERİ PENCERE 14 → 21. Yukarıdaki bulgunun ucuz çözümü
# scheduler.py'nin `earnings_calendar_gave_up` dalında ZATEN adıyla yazılıydı ("ileri pencereyi
# genişletmek; Nasdaq ucu ANAHTARSIZ ve ~15 istek — kota maliyeti ≈ 0") ve karar verildi.
# Marj TÜRETİLDİĞİ için tek sabit değişti: 21 − 7 − 5 = 9 GÜN (2 değil). NE DEĞİŞMEDİ: karartma
# semantiği (`BLACKOUT_DAYS` aynı 5, `in_blackout` bit-bit aynı), kadans (haftalık isocalendar
# kapısı), fail-open yasası. Değişen TEK şey FETCH penceresinin ileri ucudur — yani takvimin ne
# kadar ilerisini GÖRDÜĞÜ; hangi planın karartıldığı DEĞİL. Maliyet: Nasdaq gün-başına sorgulanır,
# pencere 21 gün genişledi → tur başına ~7 ek anahtarsız istek.
#
# KÖK NEDEN NE DEĞİL (ikisi de ölçülüp ELENDİ, bkz. `margin_days` docstring'i):
#   * BMO/AMC belirsizliği DEĞİL — o per-sembol bir SAAT belirsizliğidir, marj ise takvimin
#     ileri KAPSAMASI ile kadans arasındaki farktan doğar; saat bilgisi marjı hiç etkilemez.
#   * Tarih kayması DEĞİL — kaynak (Nasdaq takvimi) gün-başına sorgulanır ve dönen `date` sorgunun
#     KENDİ günüdür; kayacak bir alan yok.
# KÖK NEDEN: üç sayının ARİTMETİĞİ (ileri pencere − kadans − karartma) ve o aritmetik hiçbir yerde
# YAZILI DEĞİLDİ; üç sayı üç ayrı dosyada gömülü duruyordu (pencere burada satır-içi literaldi,
# kadans scheduler'ın isocalendar kapısında, karartma yukarıdaki sabitte). Kalıcı çözüm: üç sayı da
# ADLANDIRILDI, marj onlardan TÜRETİLİYOR (`margin_days`) ve bir sonraki karar tahminle değil
# ölçümle verilebiliyor. DAVRANIŞ DEĞİŞMEDİ — değerler bugünkü değerlerin ta kendisi.
#
# NEDEN `config.py` DEĞİL: bu tur `config.py` paralel bir ajanın yüzeyinde (dosya-ayrıklık
# sözleşmesi) ve aynı dosyaya iki yazar çakışmadır. Sabitler burada TEK yerde ve tek modülün malı;
# `config.py`ye taşınması istenirse üç satırlık bir taşımadır (türetme `margin_days`te kalır).
REFRESH_BACK_DAYS = 7      # tazelemede geriye bakılan gün (PEAD çapası)
REFRESH_FWD_DAYS = 21      # tazelemede ileriye bakılan gün (karartma penceresini besleyen uç; 14→21, 2026-08-01)
REFRESH_CADENCE_DAYS = 7   # tazeleme kadansı — scheduler'ın HAFTALIK isocalendar kapısı (advance_once)

# --------------------------------------------------------------------------------------------------
# FMP YEDEĞİNE DÜŞME EŞİĞİ — KISMİ PENCERE (denetim C25 / FMP yarısı, 2026-08-02; OPERATÖR ONAYLI)
# --------------------------------------------------------------------------------------------------
# ÖNCEKİ HÂL: `refresh` FMP'yi YALNIZ `not rows` (TAM boşluk) hâlinde deniyordu. Nasdaq ucu gün
# başına sorgulanır ve düşen günü GÜN BAZINDA yutar; "20 iş gününün 19'u düştü" hâlinde tek gün
# satır döndürdüğü sürece tur "başarı" sayılıyor ve yedek HİÇ denenmiyordu. Kaçan gün-diliminde
# duyurulan bir rapor tarihi bir sonraki tazelemeye kadar BİLİNMEZ; `in_blackout` o sembolde (veri
# yokken FAIL-OPEN) False döner ve motor bilanço gününe pozisyonla girer. Sayaç yarısı 2026-08-02'de
# indi (`stats` + `earnings_refresh_window_partial`) ama o yalnız GÖRÜNÜRLÜKTÜ — hüküm yoktu.
#
# KARAR: gün kapsaması bu eşiğin ALTINDAYSA FMP yedeği DENENİR. Nasdaq'ın getirdiği satırlar
# ATILMAZ — yedek EKLENİR ve mevcut birleştirme kuralları ((ticker,date) anahtarı, bilinen saat
# bilinmeyeni ezer) aynen uygulanır.
#
# NEDEN 0,90 VE NEDEN SABİT: bu bir KOTA kararıdır, ölçümle ayarlanacak bir knob DEĞİL — arama
# uzayında yer almaz, `bounds.yaml`a girmez. FMP kazanç ucu TICKER BAŞINA bir istektir (250 evren =
# 250 istek = günlük kotanın tamamı), o yüzden yedek "her eksik günde" değil ancak pencerenin ONDA
# BİRİNDEN FAZLASI düştüğünde açılır. Kota etkisi DAR: FMP zaten tam-boşlukta deneniyordu; eklenen
# tek maliyet KISMİ günlerdir ve tazeleme haftalık olduğu için tavan haftada bir ekstra tam pastır.
# Ölçülemeyen kapsama (pencerede iş günü yok / adaptör sayacı doldurmadı) eşiği TETİKLEMEZ: None bir
# sayı değildir, "eksik" diye okumak uydurma olurdu.
#
# NE DEĞİŞMEDİ: karartma semantiği (`BLACKOUT_DAYS` = 5, `in_blackout` bit-bit aynı), tam-boşluk
# yolu (`not rows` → `refresh_from_fmp` + `earnings_refresh_empty`), `refresh_from_fmp`in kendi
# davranışı (dosyayı BAŞTAN yazması dahil — o "değiştirir" kusuru bu turun kapsamı DIŞINDA) ve
# `refresh`in dönüş sözleşmesi (Nasdaq yolunda hâlâ Nasdaq satır sayısı → scheduler'ın `n > 0`
# nabzı kaymaz).
EARNINGS_FMP_FALLBACK_COVERAGE = 0.90

# BMO/AMC DARALTMASI — YOL VAR, ANAHTAR KAPALI. `time` alanı ölçüldü ve GERÇEK (2026-08-01, Nasdaq
# takvimi 6 gün / 1307 satır: time-not-supplied %65,7 · time-after-hours %19,7 · time-pre-market
# %14,5). Yani satırların ~%34'ünde baskının seans-öncesi mi seans-sonrası mı olduğu BİLİNİYOR.
# Bilindiğinde karartmanın YAKIN ucu bir gün daraltılabilir (bkz. `in_blackout`). Bu bir DAVRANIŞ
# kararıdır (kapı gevşetmek) ve bu turun yetkisinde değil → varsayılan KAPALI, davranış bit-bit aynı.
TIME_TIGHTEN = False

# {ticker: [date, ...]} cached by file mtime so a rewritten earnings.csv is picked up without restart
_CACHE: dict = {}
_CACHE_MTIME: float | None = None
# {(TICKER, date): "bmo"|"amc"} — YALNIZ kaynağın SÖYLEDİĞİ satırlar. Söylemediği satır burada HİÇ
# YOKTUR (uydurma yasağı: "bilinmiyor" bir değer değil, bir YOKLUKtur → report_time None döner).
_TIMES: dict = {}
# Son tazeleme penceresinin gün-kapsaması — SÜREÇ-İÇİ, BİLEREK DİSKE YAZILMAZ. Tek okuyucusu
# `calendar_untrustworthy()` ve tek yazarı `refresh()`; ikisi de CANLI WORKER'ın aynı sürecinde
# yaşar (scheduler tazeler, loop karar verir). Diske yazmak yeni bir state artefaktı ve onun
# artefakt-graf yükümlülüğünü doğururdu; kazanç sıfır, çünkü süreç yeniden doğduğunda "ölçülmedi"
# (None) demek zaten DOĞRU cevaptır — o süreç henüz hiçbir pencere görmedi.
_LAST_WINDOW: dict = {}


def _load() -> dict:
    global _CACHE, _CACHE_MTIME, _TIMES
    path = config.STATE / "earnings.csv"
    if not path.exists():
        _CACHE, _CACHE_MTIME, _TIMES = {}, None, {}
        return _CACHE
    mtime = path.stat().st_mtime
    if mtime == _CACHE_MTIME:
        return _CACHE
    out: dict[str, list[str]] = {}
    times: dict[tuple, str] = {}
    try:
        with path.open(newline="") as fh:
            for row in csv.reader(fh):
                if len(row) < 2:
                    continue
                tkr, d = row[0].strip().upper(), row[1].strip()
                if not tkr or tkr in ("TICKER", "SYMBOL"):    # tolerate a header line
                    continue
                try:
                    dt.date.fromisoformat(d)
                except ValueError:  # sessiz-yutma: biçimsiz/eksik tek alan; yalnız bu değer düşer, satır başına uyarı asıl sinyali log seline gömerdi
                    continue
                out.setdefault(tkr, []).append(d)
                # ÜÇÜNCÜ SÜTUN İSTEĞE BAĞLI: iki sütunlu ESKİ dosyalar aynen okunur (geriye
                # uyumluluk şart — canlıdaki dosya 2 sütunlu ve bu tur onu yeniden yazmaz).
                # Tanınmayan/boş değer YOK sayılır; "bilinmiyor" sözlüğe GİRMEZ.
                if len(row) >= 3:
                    tm = row[2].strip().lower()
                    if tm in ("bmo", "amc"):
                        times[(tkr, d)] = tm
    except Exception as e:
        # YASA 4 (2026-07-21) — BU SESSİZLİK PARA KAYBETTİRİR: takvim boş dönerse kazanç karartması
        # tamamen KAPANIR ve motor bilanço gününe pozisyonla girer. Hiçbir istisna yükselmez, hiçbir
        # test kırılmaz; yalnız "bugün karartma yok" der. Davranış korunuyor (boş takvim), sinyal var.
        try:
            from . import obs
            obs.warn("earnings_calendar_unreadable", path=str(path), error=f"{type(e).__name__}: {e}",
                     detail="karartma penceresi bu turda DEVRE DIŞI")
        except Exception:
            # sessiz-yutma: kayıt kanalının kendisi düştü — ikinci kanal yok; uyarı denemesi
            # takvim yüklemesini düşüremez.
            pass
        out, times = {}, {}
    for tkr in out:
        out[tkr] = sorted(set(out[tkr]))   # AYNI (ticker,date) iki kez yazılmışsa bir kez sayılır
    _CACHE, _CACHE_MTIME, _TIMES = out, mtime, times
    return out


def clear_cache() -> None:
    global _CACHE_MTIME
    _CACHE_MTIME = None


def report_time(ticker: str, on_date: str) -> str | None:
    """Bu rapor seans ÖNCESİ mi ("bmo") seans SONRASI mı ("amc")? Kaynak söylemediyse None.

    None ÜÇÜNCÜ HÂLDİR ve varsayılan değildir: takvimin %66'sı `time-not-supplied` döner (ölçüm
    2026-08-01) ve orada saat BİLİNMİYOR — "bmo say" ya da "amc say" ikisi de uydurma olurdu."""
    _load()
    return _TIMES.get(((ticker or "").upper(), str(on_date)[:10]))


def margin_days() -> int:
    """KARARTMA MARJI = ileri kapsama − kadans − karartma penceresi. Bugün: 21 − 7 − 5 = 9 GÜN.

    (2026-08-01 ÖNCESİ 14 − 7 − 5 = 2 GÜNDÜ; ileri pencere kararla 21'e çıkarıldı — bkz. modül
    başındaki KARAR bloğu. Karartma semantiği DEĞİŞMEDİ; genişleyen yalnız FETCH penceresidir.)

    NE ÖLÇER: iki tazeleme arasındaki EN KÖTÜ anda (bir sonraki tazelemeden hemen önce) takvimin
    ileri kapsaması `REFRESH_FWD_DAYS - REFRESH_CADENCE_DAYS` güne iner. Karartma `BLACKOUT_DAYS`
    gün ileriyi görmek zorundadır; fark MARJDIR. Marj ≤ 0 olursa `in_blackout` HERKES için False
    döner (veri yokken FAIL-OPEN) ve motor bilanço gününe pozisyonla girebilir.

    NEDEN BURADA VE TÜRETİLMİŞ: sayı sabit yazılsaydı, üç girdiden biri değiştiği gün sessizce
    yalan olurdu — bu depodaki "aynı yasa iki yerde, biri güncellenmemiş" kusurunun tam hâli.
    `earnings_calendar_gave_up` uyarısı ve `coverage()` bu değeri BURADAN okur."""
    return int(REFRESH_FWD_DAYS) - int(REFRESH_CADENCE_DAYS) - int(BLACKOUT_DAYS)


def refresh_window(today: dt.date | None = None) -> tuple[str, str]:
    """Tazelemenin SORACAĞI pencere — `refresh()` ile TEK tanımdan okunur (iki yerde iki pencere,
    `margin_days`ı sessizce yalan yapardı)."""
    t = today or dt.date.today()
    return str(t - dt.timedelta(days=REFRESH_BACK_DAYS)), str(t + dt.timedelta(days=REFRESH_FWD_DAYS))


def days_since_report(ticker: str, on_date: str, max_days: int = 2) -> bool:
    """PEAD/episodik-pivot çapası: on_date, ticker'ın bir kazanç raporundan sonraki max_days GÜN
    içinde mi? (rapor günü dahil). Veri yoksa False — kurulum uydurma tetiklemez."""
    try:
        d = dt.date.fromisoformat(str(on_date)[:10])
    except (ValueError, TypeError):  # sessiz-yutma: biçimsiz/eksik tek alan; yalnız bu değer düşer, satır başına uyarı asıl sinyali log seline gömerdi
        return False
    for ds in _load().get(str(ticker).upper(), []):
        try:
            e = dt.date.fromisoformat(ds)
        except ValueError:  # sessiz-yutma: biçimsiz/eksik tek alan; yalnız bu değer düşer, satır başına uyarı asıl sinyali log seline gömerdi
            continue
        if 0 <= (d - e).days <= max_days:
            return True
    return False


def _pair(x) -> tuple:
    """Adaptörden gelen bir öğeyi (tarih, saat|None) ikilisine indirger. Düz dize de kabul edilir."""
    if isinstance(x, (tuple, list)):
        d = str(x[0])[:10]
        tm = str(x[1]).strip().lower() if len(x) > 1 and x[1] else None
        return (d, tm if tm in ("bmo", "amc") else None)
    return (str(x)[:10], None)


def refresh(tickers: list[str]) -> int:
    """#5 — birleşik tazeleme: BİRİNCİL kaynak Nasdaq takvimi (anahtarsız, evren-boyundan bağımsız
    ~15 istek: geriye REFRESH_BACK_DAYS [PEAD çapası] + ileriye REFRESH_FWD_DAYS [karartma
    penceresi]; marjı `margin_days()` söyler); Nasdaq boş dönerse FMP'ye düşülür (anahtar varsa;
    250 ticker = 250 istek = günlük kota — o yüzden yedek). Sonuç MEVCUT csv ile BİRLEŞTİRİLİR
    (kaynak değişimi geçmiş çapaları silmez).

    BİRLEŞTİRME YASASI — İKİ DAL, TEK BEYAN (denetim hafif bulgusu, 2026-08-02). Denetim bu
    docstring'in yalnız BİR dalı anlattığını ve iki dalın da yanlış tarafta olduğunu ölçtü:

      (i) NASDAQ DALI YALNIZ EKLİYORDU. Kazanç tarihi REVİZE edilip kaydığında (modülün kendi PIT
          bloğu "borsanın en çok REVİZE EDİLEN takvimlerinden biri" diyor) ESKİ tarih dosyada
          sonsuza dek kalıyordu: `in_blackout` HAYALET bir tarih için karartma uyguluyor,
          `coverage().future_dates` şişiyor ve o hayalet ertesi gün GEÇMİŞ çapaya (PEAD) dönüşüyordu.
          YENİ: kaynağın o turda DÖNDÜĞÜ ticker'lar için, kaynakta artık OLMAYAN GELECEK tarihler
          (bugün dâhil, tazeleme penceresinin İÇİNDE kalanlar) DÜŞÜLÜR. GEÇMİŞ ÇAPALAR KALIR —
          "geçmiş silinmez" sözü aynen korunur; emekliye ayrılan yalnız İLERİ-YÖNLÜ revizyondur.
          KANIT ŞARTI: yalnız gün kapsaması TAM (1,0) olan turda. Kısmi pencerede bir tarihin
          yokluğu revizyon DEĞİL, kaçan gün-dilimi olabilir; onu silmek karartmayı GERÇEKTEN
          daraltırdı (bu modülün en pahalı hata sınıfı). Ölçülemeyen kapsama (None) da tetiklemez.

     (ii) FMP DALI SESSİZCE DÜŞÜRÜYORDU. `refresh_from_fmp` dosyayı BAŞTAN yazıyor ve yalnız
          `failed` ticker'ların önbellek satırlarını kurtarıyordu; BAŞARIYLA çekilen bir ticker'ın
          Nasdaq'tan birikmiş tarihleri yazımdan sessizce düşüyordu — yani docstring'in "kaynak
          değişimi geçmiş çapaları silmez" cümlesi tam da kaynak değişimi anında ihlal ediliyor ve
          `days_since_report` (PEAD çapası) o sembollerde körelıyordu. YENİ: o yol da ÜST KÜME
          kuralına çekildi (mevcut takvimin TAMAMI ∪ FMP satırları) — C25 kısmi-yolundaki
          "yedek Nasdaq'ı EZMEZ" deseninin `refresh_from_fmp`in KENDİ yazımına uygulanmış hâli.

    İKİ DEĞİŞİKLİĞİN KARARTMAYA ETKİSİ ZIT YÖNDEDİR ve bilerek öyledir: (ii) fail-open'ı KAPATIR
    (kaybolan tarihler geri gelir → daha çok karartma), (i) yalnız kaynağın KENDİSİNİN geri
    çektiği hayalet tarihleri kaldırır (o tarihte rapor YOKTUR — orada karartma koruma değil
    gürültüdür). Her ikisi de olay basar: `earnings_future_revision_retired` ve
    `earnings_refresh_partial`.

    ÜÇÜNCÜ SÜTUN (`time`): kaynağın BMO/AMC alanı biliniyorsa yazılır, bilinmiyorsa BOŞ kalır.
    Karar yolunu BUGÜN etkilemez (`TIME_TIGHTEN=False`); alan birikmeye BUGÜN başlar çünkü geçmiş
    takvim geriye doğru zenginleşmez — bugün yazılmayan saat bilgisi bir daha gelmez.

    KISMİ PENCERE ARTIK SESSİZ DEĞİL (denetim C25, 2026-08-02): Nasdaq ucu gün başına sorgulanır ve
    düşen günü GÜN BAZINDA yutar. Eskiden "20 iş gününün 19'u düştü" ile "hepsi geldi" buraya AYNI
    şekilde geliyordu — tek gün satır döndürdüğü sürece tur "başarı" sayılıyor, kaç gün-diliminin
    kaçtığı HİÇBİR yere yazılmıyordu; yeni duyurulan bir kazanç tarihi kaçan dilimde kalırsa
    `in_blackout` o sembolde (veri yokken fail-open) False döner ve motor bilanço gününe pozisyonla
    girer. Artık adaptör `stats` sayacını doldurur, eksik kapsama `earnings_refresh_window_partial`
    olarak UYARI basar ve sayılar `earnings_refreshed`e alan olarak geçer.
    YEDEĞE DÜŞME EŞİĞİ ARTIK KISMİ PENCEREYİ DE KAPSIYOR (KOVA B, 2026-08-02, operatör onaylı):
    kapsama `EARNINGS_FMP_FALLBACK_COVERAGE`ın (0,90) ALTINDAYSA FMP yedeği denenir ve düşüş
    `earnings_fallback_partial_window` ile BEYAN EDİLİR. Nasdaq'ın getirdiği satırlar ATILMAZ —
    yedek onların ÜSTÜNE değil, YANINA eklenir (nihai yazım her ikisinin ÜST KÜMESİDİR). Eşiğin
    gerekçesi ve kota etkisi sabitin yanındadır. Karartma semantiği DEĞİŞMEDİ."""
    from .adapters import data as _da
    uni = {str(t).upper() for t in tickers}
    _s, _e = refresh_window()          # PENCERE TEK TANIMDAN (bkz. margin_days) — literal YOK
    # BOŞ KALIRSA "ÖLÇÜLMEDİ" DEMEKTİR, "kapsama tam" DEMEZ: `stats`i yalnız gerçek adaptör doldurur;
    # sahte/eski bir uygulama sözlüğe dokunmaz ve aşağıdaki alanlar None olarak (nedeniyle) geçer.
    _gun: dict = {}
    fetched = _da.nasdaq_earnings_window(_s, _e, with_time=True, stats=_gun)
    _gun_dusen = _gun.get("dusen")
    # PENCERENİN SAĞLIĞI KARAR YOLUNA BURADAN GEÇER (2026-08-03, Rol-1 A1). Eskiden bu ölçüm yalnız
    # bir UYARI metnine giriyordu — yani kısmi pencere görünürdü ama hiçbir kapıyı bağlamıyordu.
    # Kaydı `calendar_untrustworthy()` okur. `kapsama` None ise ölçülmedi demektir ve None hiçbir
    # eşiği tetiklemez (bu modülün her yerinde aynı kural).
    _LAST_WINDOW.clear()
    _LAST_WINDOW.update({"kapsama": _gun.get("kapsama"), "dusen": _gun_dusen,
                         "istenen": _gun.get("istenen"), "pencere": [_s, _e],
                         "at": dt.date.today().isoformat()})
    if _gun_dusen:
        from . import obs
        obs.warn("earnings_refresh_window_partial", source="nasdaq",
                 istenen=_gun.get("istenen"), cevaplayan=_gun.get("cevaplayan"),
                 dusen=_gun_dusen, dusen_gunler=",".join(_gun.get("dusen_gunler") or []),
                 kapsama=_gun.get("kapsama"), son_hata=_gun.get("son_hata"),
                 esik=EARNINGS_FMP_FALLBACK_COVERAGE,
                 detail="kazanç takvimi penceresi KISMİ geldi — kaçan gün-diliminde duyurulan bir "
                        "rapor tarihi bir sonraki tazelemeye kadar BİLİNMEZ ve karartma o sembolde "
                        "fail-open kalır. Kapsama eşiğin ALTINDAYSA FMP yedeği denenir ve düşüş "
                        "`earnings_fallback_partial_window` ile ayrıca beyan edilir; ÜSTÜNDEYSE bu "
                        "uyarı tek başına durur (eksik ama yedeği hak etmeyen pencere).")
    # ŞEKİL NORMALİZASYONU: adaptör `with_time=True` ile (tarih, "bmo"|"amc"|None) İKİLİSİ döner;
    # `with_time` verilmemiş/eski bir uygulama (ve testlerdeki sahteler) DÜZ tarih dizisi döner.
    # İkisi de kabul edilir — çağıranın kendi sözleşmesini kırmadan alan kazanmasının yolu bu.
    rows = [(t, *_pair(x)) for t, ds in fetched.items() if t in uni for x in ds]
    src = "nasdaq"
    if not rows:
        src = "fmp"
        n = refresh_from_fmp(tickers)
        if not n:
            # YASA 4 — HER İKİ KAYNAK DA BOŞ (2026-07-26). Bu yol SESSİZ dönüyordu: `refresh` 0
            # döndürüyor, çağıran onu "yeni satır yok" diye okuyor ve takvim OLDUĞU GİBİ kalıyordu.
            # Ama takvim bayatladığında (gelecek tarih kalmadığında) `in_blackout` herkes için
            # False döner, yani karartma guard'ı FAIL-OPEN kapanır ve motor bilanço gününe
            # pozisyonla girer. "Tazeleme koştu, yeni bir şey yoktu" ile "İKİ KAYNAK DA KONUŞMADI"
            # aynı sayıyla anlatılamaz; ikincisi bir arıza sinyalidir.
            from . import obs
            from .adapters import fmp as _fmp
            cov = coverage(tickers)
            obs.warn("earnings_refresh_empty", sources="nasdaq+fmp", universe=len(uni),
                     fmp_key_present=bool(_fmp.available()), fmp_quota_blocked=bool(_fmp.quota_blocked()),
                     known_tickers=cov.get("known_tickers"), future_dates=cov.get("future_dates"),
                     inert=cov.get("inert"),
                     detail="kazanç takvimi HİÇ tazelenemedi — takvim bayatlarsa karartma guard'ı "
                            "fail-open kapanır ve bilanço gününde işlem açılır")
        return n
    # BİRLEŞTİRME (ticker,date) ANAHTARLIDIR, (ticker,date,time) DEĞİL: aksi hâlde saati BİLİNEN ve
    # BİLİNMEYEN aynı rapor İKİ satır olur, `coverage().future_dates` şişer ve `_load` aynı tarihi
    # iki kez listeler. Bilinen saat bilinmeyeni EZER (bilgi kazanımı geri alınmaz), tersi olmaz.
    # SIRA ÖNEMLİ: `merged` AŞAĞIDAKİ FMP çağrısından ÖNCE alınır — `refresh_from_fmp` dosyayı
    # BAŞTAN yazar (o kusur bu turun kapsamı dışında, davranışı değişmedi) ve mevcut takvimin
    # bir kısmını düşürebilir; önce alınan bu anlık görüntü onu nihai yazımda GERİ KOYAR.
    prev = _load()
    merged: dict = {(t, d): _TIMES.get((t, d)) for t, ds in prev.items() for d in ds}

    # ---- KISMİ PENCEREDE FMP YEDEĞİ (C25 / FMP yarısı — eşik ve gerekçe: sabitin yanında) --------
    # HÜKÜM BURADA VERİLİR, ADAPTÖRDE DEĞİL: `nasdaq_earnings_window` yalnız SAYAR (kendi
    # docstring'inde beyanlı). Ölçülemeyen kapsama (None) eşiği tetiklemez — bkz. sabitin gerekçesi.
    _kapsama = _gun.get("kapsama")
    _fmp_yedek = None                  # None = DENENMEDİ · 0 = denendi, satır gelmedi (ikisi ayrı olgu)
    if _kapsama is not None and _kapsama < EARNINGS_FMP_FALLBACK_COVERAGE:
        from . import obs
        from .adapters import fmp as _fmp
        src = "nasdaq+fmp"             # kaynak damgası KARIŞIMI söyler; "nasdaq" demek yarım doğru olurdu
        _fmp_yedek = refresh_from_fmp(tickers)
        # FMP'nin YAZDIĞI dosyayı da birleştirmeye al. Nasdaq satırları AŞAĞIDA, en son uygulanır →
        # yedek onları EZEMEZ. Saat bilgisi yalnız BOŞKEN doldurulur (bilinen bilinmeyeni ezer yasası).
        _fmp_dosya = _load()
        for _t, _ds in _fmp_dosya.items():
            for _d in _ds:
                if merged.get((_t, _d)) is None:
                    merged[(_t, _d)] = _TIMES.get((_t, _d))
        obs.warn("earnings_fallback_partial_window", source="nasdaq->fmp",
                 kapsama=_kapsama, esik=EARNINGS_FMP_FALLBACK_COVERAGE,
                 istenen=_gun.get("istenen"), cevaplayan=_gun.get("cevaplayan"), dusen=_gun_dusen,
                 fmp_satir=_fmp_yedek, fmp_anahtar=bool(_fmp.available()),
                 fmp_kota_bloklu=bool(_fmp.quota_blocked()),
                 neden=(f"gün kapsaması {_kapsama} < eşik {EARNINGS_FMP_FALLBACK_COVERAGE} — kaçan "
                        f"gün-diliminde duyurulan bir rapor tarihi bir sonraki tazelemeye kadar "
                        f"BİLİNMEZ ve karartma o sembolde fail-open kalırdı"),
                 detail="KISMİ pencere yedeğe düşürdü (KOVA B, operatör onaylı eşik): Nasdaq'ın "
                        "getirdiği satırlar ATILMADI, FMP satırları yanlarına eklendi; karartma "
                        "semantiği ve tam-boşluk yolu DEĞİŞMEDİ. Yedek bu turda kotadan ticker "
                        "başına bir istek harcadı.")

    # ---- İLERİ-YÖNLÜ REVİZYON EMEKLİLİĞİ (denetim hafif bulgusu; gerekçe: refresh docstring'i (i))
    # NEDEN BURADA: `merged` artık BİRİKMİŞ takvimdir (prev + varsa FMP yedeği) ve `rows` kaynağın
    # BU TURDAKİ tam cevabıdır — ikisi ancak yan yanayken "kaynak bu tarihi geri çekti" denebilir.
    # NEDEN `rows` UYGULANMADAN ÖNCE: aşağıdaki döngü kaynağın GÜNCEL tarihlerini yazar; emeklilik
    # ondan sonra koşsaydı yeni yazılan satırı da düşürme riski taşırdı (aynı anahtar iki yasada).
    # ÇAKIŞMA YOK: FMP yedeği yalnız kapsama < 0,90 iken koşar, emeklilik yalnız kapsama == 1,0
    # iken — ikisi aynı turda BİRLİKTE çalışamaz (yani bir kaynağın getirdiğini diğeri silemez).
    _emekli: list = []
    if _kapsama == 1.0:
        _bugun = dt.date.today().isoformat()
        _konusan = {t for t, _d, _tm in rows}      # kaynak BU ticker hakkında konuştu
        _guncel = {(t, d) for t, d, _tm in rows}   # …ve bunlar onun BUGÜNKÜ cevabı
        # SESSİZ SEMBOL DOKUNULMAZ: tarihi pencerenin TAMAMEN dışına kayan sembol hiç dönmez ve
        # `_konusan`a girmez — onun eski tarihi KALIR. Bu bilinçli bir DAR kapsamdır: "kaynak
        # sustu" ile "kaynak geri çekti" aynı kanıt değildir.
        _emekli = [(t, d) for (t, d) in sorted(merged)
                   if t in _konusan and _bugun <= d <= _e and (t, d) not in _guncel]
        for _k in _emekli:
            merged.pop(_k, None)
        if _emekli:
            from . import obs
            obs.warn("earnings_future_revision_retired", source="nasdaq",
                     satir=len(_emekli), sembol=len({t for t, _ in _emekli}),
                     ornek=";".join(f"{t}:{d}" for t, d in _emekli[:8]),
                     pencere=f"{_s}..{_e}", kapsama=_kapsama,
                     detail="kaynak TAM kapsamalı pencerede bu GELECEK tarihleri artık bildirmiyor "
                            "→ revizyon emekliye ayrıldı (hayalet karartma + şişmiş future_dates "
                            "kaynağı). GEÇMİŞ çapalara DOKUNULMADI; kısmi/ölçülemeyen kapsamada bu "
                            "yol HİÇ çalışmaz (eksik gün-dilimini 'iptal' saymak karartmayı "
                            "gerçekten daraltırdı).")

    for t, d, tm in rows:
        if tm or (t, d) not in merged:
            merged[(t, d)] = tm or merged.get((t, d))
    # KAPI-DIŞI TAŞIMA (H9 Kademe C): elle mkstemp+os.replace (fsync YOK, flock YOK) → store.write_text.
    # STATE'e GÖRELİ ad ("earnings.csv") → kilit refresh_from_fmp ile PAYLAŞILIR (iki yol AYNI dosyayı
    # yazar; mutlak ad ayrı kilide düşer = kilit yok). Biçim (CSV başlık + satırlar) BİREBİR korunur.
    # YASA-6 OKUYUCU: _load() (satır ~111) → PEAD çapası + kazanç-karartma guard (in_blackout).
    from . import store
    _csv = "ticker,date,time\n" + "".join(
        f"{t},{d},{tm or ''}\n" for (t, d), tm in sorted(merged.items()))
    store.write_text("earnings.csv", _csv)
    clear_cache()
    _snapshot(src)                 # PIT birikim defteri (bkz. SNAPSHOT_FILE) — YAZIMDAN SONRA
    from . import obs
    obs.log("earnings_refreshed", source=src, new_rows=len(rows), total=len(merged),
            # SAAT ALANI KAÇ SATIRDA BİLİNİYOR — birikimin sayacı (ölçüm 2026-08-01: ~%34 bekleniyor)
            time_known=sum(1 for v in merged.values() if v),
            # GÜN KAPSAMASI (C25): "yeni satır sayısı" tek başına kapsamayı ANLATMAZ — 1 gün cevap
            # verip 19 gün düşse de `new_rows` pozitif görünür. Ölçülmediyse None + neden.
            gun_istenen=_gun.get("istenen"), gun_cevaplayan=_gun.get("cevaplayan"),
            gun_dusen=_gun.get("dusen"), gun_kapsama=_gun.get("kapsama"),
            # KISMİ-PENCERE YEDEĞİ (KOVA B): None = eşik tetiklenmedi/ölçülemedi, 0 = denendi ama
            # satır gelmedi (anahtar yok ya da kota) — iki olgu aynı sayıyla anlatılamaz.
            fmp_yedek=_fmp_yedek, fmp_yedek_esigi=EARNINGS_FMP_FALLBACK_COVERAGE,
            # İLERİ-YÖNLÜ REVİZYON: kaç hayalet GELECEK tarih emekliye ayrıldı. 0 = tur koştu,
            # revizyon yoktu; kapsama TAM değilse yol hiç koşmaz ve sayı yine 0'dır (ayrımı
            # `gun_kapsama` alanı verir — iki alan yan yana okunur).
            emekli_satir=len(_emekli),
            gun_olcum_yok=(None if _gun else "adaptör sayaç doldurmadı — kapsama ÖLÇÜLMEDİ"))
    return len(rows)


def refresh_from_fmp(tickers: list[str]) -> int:
    """Evrenin kazanç tarihlerini FMP'den çekip state/earnings.csv'ye yazar (ticker,date). Hem PEAD
    çapasını hem MEVCUT kazanç-karartma guard'ını (bugüne dek boş veriyle no-op'tu) gerçek veriyle
    besler. Anahtar yoksa 0 döner; kısmi hata bir ticker'ı atlar, dosyayı bozmaz.

    YAZIM ÜST KÜMEDİR (denetim hafif bulgusu, 2026-08-02 — `refresh` docstring'i (ii) ile AYNI yasa):
    dosya BAŞTAN yazılır ama içeriği "MEVCUT takvimin TAMAMI ∪ bu turun FMP satırları"dır. Eskiden
    yalnız `failed` ticker'ların önbellek satırları kurtarılıyordu; yani BAŞARIYLA çekilen bir
    ticker'ın Nasdaq'tan birikmiş tarihleri sessizce DÜŞÜYORDU (`days_since_report` körelir,
    `in_blackout` o tarihlerde fail-open'a düşerdi). Kaynak değişimi geçmiş çapaları SİLMEZ.
    DÖNÜŞ DEĞERİ DEĞİŞMEDİ: hâlâ "bu turda elde edilen satır" sayısıdır (FMP'nin döndürdükleri +
    düşen ticker'lardan kurtarılanlar), dosyadaki TOPLAM değil — `refresh`in `if not n` kapısı ve
    scheduler'ın nabzı o sayıya yaslanıyor."""
    from .adapters import fmp
    if not fmp.available():
        return 0
    import time as _t
    rows, failed = [], []
    for t in tickers:
        try:
            for d in fmp.earnings_dates(t, strict=True):   # hata YUTULMAZ: eksik ≠ "kazanç yok"
                rows.append((t.upper(), d))
        except Exception:  # sessiz-yutma: yardımcı/telemetri yolu; başarısızlığı karara girmez ve çağıran yedek değerle aynen devam eder
            failed.append(t.upper())
            if fmp.quota_blocked():                        # kota bitti: kalanı denemek anlamsız
                failed.extend(x.upper() for x in tickers[tickers.index(t) + 1:])
                break
            continue
        _t.sleep(0.1)                                     # polite delay — refetch ile aynı görgü kuralı
    if not rows:
        return 0
    # KISMİ BAŞARISIZLIK KORUMASI (adapters.fmp denetimi, tur 4 — 2026-07-21):
    # Eskiden dosya, gelen ne varsa ONUNLA ÜZERİNE YAZILIYORDU. Kota pasın ortasında biterse
    # (bugün oldu) 100 ticker gelir, 150'si düşerdi; in_blackout() veri yokken FAIL-OPEN olduğu için
    # o 150 isimde KAZANÇ GÜNÜ işlem açılırdı — sert bir guard sessizce no-op'a dönerdi.
    # Çözüm: yaz değil BİRLEŞTİR; başarısız ticker'ların ESKİ tarihleri korunur ve durum kaydedilir.
    # SAAT SÜTUNU DA AYNI YOLDAN KORUNUR: FMP kazanç ucu BMO/AMC vermez (adapters.fmp.earnings_dates
    # yalnız `date` okur), ama dosyayı bu yol da BAŞTAN yazar — `_TIMES` anlık görüntüsü olmasa
    # Nasdaq'ın biriktirdiği saat bilgisini bir FMP tazelemesi SESSİZCE silerdi (aynı ders, sütun
    # ölçeğinde). `prev`i almak `_TIMES`i de tazeler; ayrı bir `_load()` çağrısı gerekmez.
    prev = _load()
    _bilinen = dict(_TIMES)
    if failed:
        from . import obs
        for t in failed:
            for d in prev.get(t, []):
                rows.append((t, d))
        obs.warn("earnings_refresh_partial", ok=len(tickers) - len(failed), failed=len(failed),
                 kept_from_cache=len({t for t in failed if prev.get(t)}))
    # ÜST KÜME (bkz. docstring): `rows` YALNIZ bu turun kazanımıdır ve dönüş değeri odur; DOSYAYA
    # yazılan küme ise mevcut takvimin TAMAMIYLA birleştirilmiş hâlidir. İki kümenin ayrı tutulması
    # kasıtlı — "kaç satır getirdim" ile "takvimde kaç satır var" aynı sayı değildir.
    _yazilacak = ({(t, d) for t, ds in prev.items() for d in ds}
                  | {(str(t).upper(), str(d)[:10]) for t, d in rows})
    # KAPI-DIŞI TAŞIMA (H9 Kademe C): bkz. refresh() — STATE'e göreli "earnings.csv" adı kilidi
    # refresh() ile PAYLAŞTIRIR (iki yol aynı dosyayı yazar). Biçim BİREBİR korunur.
    from . import store
    _csv = "ticker,date,time\n" + "".join(
        f"{t},{d},{_bilinen_saat(_bilinen, t, d)}\n" for t, d in sorted(_yazilacak))
    store.write_text("earnings.csv", _csv)
    clear_cache()
    _snapshot("fmp")               # PIT birikim defteri — bu yol da takvimi BAŞTAN yazar
    return len(set(rows))


def _bilinen_saat(bilinen: dict, t: str, d: str) -> str:
    return bilinen.get((t, d)) or ""


# --------------------------------------------------------------------------------------------------
# PIT BİRİKİM DEFTERİ — `state/history/earnings_snapshots.jsonl` (D kalemi, 2026-08-01)
# --------------------------------------------------------------------------------------------------
# SORUN (EDG-011'i ASKI'ya düşüren): `earnings.csv` TEK bir ANLIK GÖRÜNTÜdür. Haftalık tazeleme onu
# `os.replace` ile bütünüyle değiştirir; yani "bugün ne biliniyordu" sorusunun cevabı yalnız BUGÜN
# için vardır. Kazanç takvimi, borsanın en çok REVİZE EDİLEN takvimlerinden biridir (tarih kayar,
# şirket teyit eder, sağlayıcı düzeltir) — ve revizyonun kendisi ölçülebilir bir olgudur. Tarihsel
# takvim hiç birikmediği için PIT'li bir kazanç ölçümü (EDG-011) bugün YAPILAMIYOR.
#
# ÇÖZÜM: her tazelemeden SONRA o anki takvimin TAMAMI, fetch damgasıyla, EKLENİR. Semantik dar ve
# net: "bu (ticker,date,time) üçlüleri, `fetch_date` gününde biliniyordu." Geriye dönük hiçbir şey
# kurtarmaz — birikim BUGÜN başlar, çünkü kaçırılan hafta bir daha gelmez (arşiv mantığının aynısı).
#
# NEDEN YAZIMDAN SONRA, ÖNCE DEĞİL: PIT damgası "o gün bilinen"i ister. Tazeleme MEVCUT takvimle
# BİRLEŞTİRDİĞİ için yazım sonrası hâl, o günün bilgisinin üst kümesidir; yazım öncesi hâl ise ZATEN
# bir önceki tazelemenin anlık görüntüsünde durur. Yani "önce" almak aynı veriyi iki kez yazardı.
#
# YASA 6 — OKUYUCU BEYANI: bugünkü tüketici `snapshot_stats()` → `/api/diagnostics` `risk` bloğu
# (sayaç: kaç anlık görüntü, hangi aralık, kaç kayıt). ASIL tüketici GELECEKTEKİ ölçüm turlarıdır
# (EDG-011 kartı yeniden açıldığında). Bu, YASA 6'nın yasakladığı "kimsenin bilmediği okunmayan
# artefakt" değil, BEYAN EDİLMİŞ ve sayacı panoda duran bir BİRİKİM DEFTERİdir — tıpkı
# `barsarchive`ın seans-içi arşivi gibi (aynı gerekçe, aynı desen).
SNAPSHOT_FILE = "history/earnings_snapshots.jsonl"

# ŞEMA (satır başına bir anlık görüntü):
#   fetch_date  "YYYY-MM-DD"  — takvimin BİLİNDİĞİ gün (PIT anahtarı)
#   fetched_at  ISO-8601 UTC  — tam damga (aynı gün iki tazeleme ayırt edilebilsin)
#   source      "nasdaq"|"fmp" — hangi uç yazdı
#   tickers/rows/future_dates/time_known — sayaçlar (defteri açmadan okunabilsin)
#   kayitlar    [[TICKER, "YYYY-MM-DD", "bmo"|"amc"|null], ...]  — DÜZ üçlü liste, iç içe sözlük
#               DEĞİL: ölçüm turu bunu doğrudan bir tabloya çevirir (sözlük her okumada düzleştirme
#               ister ve düzleştirme kodu her turda yeniden yazılırdı).
def _snapshot(source: str = "") -> dict | None:
    """Tazeleme sonrası takvimin TAMAMINI PIT damgasıyla deftere EKLE (append-only).

    AYNI GÜN + AYNI İÇERİK İKİ KEZ YAZILMAZ: `refresh` bir gün içinde birden çok kez koşabilir
    (elle tetik, yeniden başlatma). İçerik değişmediyse ikinci satır bilgi TAŞIMAZ, yalnız defteri
    şişirir ve "kaç kez tazelendi" sayacını yalan yapar. İçerik DEĞİŞTİYSE aynı gün ikinci satır
    YAZILIR — revizyon tam olarak ölçmek istediğimiz şeydir.

    Hata YUTULUR ve UYARILIR (YASA 4): defter bir birikimdir, tazelemenin kendisi değil. Yazım
    düşerse o haftanın anlık görüntüsü kaybolur (kayıp gerçek) ama karartma guard'ı çalışmaya
    devam eder — deftere yazamamak takvimi tazelememek için gerekçe değildir."""
    import hashlib
    from . import store
    try:
        data = _load()
        kayitlar = [[t, d, _TIMES.get((t, d))] for t, ds in sorted(data.items()) for d in ds]
        ozet = hashlib.sha256(repr(kayitlar).encode()).hexdigest()[:16]
        bugun = dt.date.today().isoformat()
        onceki = store.read_jsonl(SNAPSHOT_FILE)
        if onceki and onceki[-1].get("fetch_date") == bugun and onceki[-1].get("digest") == ozet:
            return None                       # aynı gün, aynı içerik → bilgi yok, satır yok
        row = {"fetch_date": bugun,
               "fetched_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
               "source": source or None, "digest": ozet,
               "tickers": len(data), "rows": len(kayitlar),
               "future_dates": sum(1 for _, d, _ in kayitlar if d >= bugun),
               "time_known": sum(1 for _, _, tm in kayitlar if tm),
               "kayitlar": kayitlar}
        store.append_jsonl(SNAPSHOT_FILE, row)
        return row
    except Exception as e:
        try:
            from . import obs
            obs.warn("earnings_snapshot_failed", error=f"{type(e).__name__}: {e}",
                     detail="PIT birikim defterine yazılamadı — bu tazelemenin anlık görüntüsü "
                            "KAYIP (geriye dönük kurtarılamaz); karartma guard'ı etkilenmedi")
        except Exception:  # sessiz-yutma: kayıt kanalının kendisi düştü; tazeleme düşürülemez
            pass
        return None


def snapshot_stats(rows: list | None = None) -> dict:
    """Defterin SAYACI — YASA 6'nın bugünkü okuyucusu (`/api/diagnostics` `risk` bloğu).

    Defter YOKSA `anlik_goruntu=0` ve `ilk/son=None` döner: "birikim başlamadı" ile "birikim var
    ama boş" karışmaz. Ağır alan (`kayitlar`) DÖNMEZ — sayaç ucu, defterin kendisi değildir.

    `rows` DIŞARIDAN ENJEKTE EDİLEBİLİR ve dış tüketici (api) BÖYLE çağırır — `trend_shadow.ozet`
    ile AYNI desen ve AYNI gerekçe: `codelaw.artifact_graph` STATİK bir graftır ve okuma bu modülün
    içinde kalsaydı "kendi yazdığını kendi okuyan" sayılır, artefakt `unread` görünürdü. Dosya adı
    çağıranda LİTERAL geçer ki graf tüketiciyi GÖRSÜN."""
    from . import store
    rows = store.read_jsonl(SNAPSHOT_FILE) if rows is None else list(rows)
    return {"anlik_goruntu": len(rows),
            "ilk": rows[0].get("fetch_date") if rows else None,
            "son": rows[-1].get("fetch_date") if rows else None,
            "son_kayit": rows[-1].get("rows") if rows else None,
            "son_ticker": rows[-1].get("tickers") if rows else None,
            "son_saat_bilinen": rows[-1].get("time_known") if rows else None,
            "farkli_gun": len({r.get("fetch_date") for r in rows}) if rows else 0,
            "dosya": SNAPSHOT_FILE,
            "beyan": "PIT birikim defteri — tüketicisi gelecekteki kazanç ölçüm turları (EDG-011); "
                     "geriye dönük doldurulamaz, birikim yalnız ileri akar"}


def in_blackout(ticker: str, on_date: str, days: int = BLACKOUT_DAYS) -> bool:
    """True if `on_date` is within `days` calendar days *before* (or on) the ticker's next scheduled
    earnings date. Unknown ticker / no CSV -> False (never blocks when there is no information).

    BMO DARALTMASI (yol var, `TIME_TIGHTEN` ile KAPALI — 2026-08-01): `on_date` raporun TAM günüyse
    ve kaynak o raporu "bmo" (seans öncesi) diye biliyorsa, baskı `on_date`in AÇILIŞINDAN ÖNCE
    düşmüştür; plan ise bir SONRAKİ açılışta girer, yani pozisyon baskıya maruz kalmaz. Saat
    bilinmiyorsa (satırların ~%66'sı) hiçbir şey daralmaz — None mantığı, uydurma yok.
    Anahtar KAPALI çünkü bu bir kapı gevşetmesidir ve gevşetme kararı operatörün/öğrenmenin."""
    dates = _load().get((ticker or "").upper())
    if not dates:
        return False
    try:
        d0 = dt.date.fromisoformat(str(on_date)[:10])
    except ValueError:  # sessiz-yutma: biçimsiz/eksik tek alan; yalnız bu değer düşer, satır başına uyarı asıl sinyali log seline gömerdi
        return False
    for ds in dates:
        ed = dt.date.fromisoformat(ds)
        delta = (ed - d0).days
        if not (0 <= delta <= days):
            continue
        if TIME_TIGHTEN and delta == 0 and report_time(ticker, ds) == "bmo":
            continue
        return True
    return False


# --------------------------------------------------------------------------------------------------
# FAIL-OPEN'IN BEYANI — kapsam-dışı sembolde karartma kapısı SESSİZCE geçirgendi (2026-08-01)
# --------------------------------------------------------------------------------------------------
# ÖLÇÜM: evrenin 251 sembolünden 194'ü takvimde var, 57'si YOK. O 57'de `in_blackout` her zaman
# False döner — "kontrol edildi, temiz" ile "HİÇ VERİ YOK" plan kaydında AYNI görünürdü
# (`gate_checks.coverage` alanı 2026-07-21'de eklendi ama karar satırında, yani operatörün ve
# panonun ilk baktığı `gate_reasons`ta, iz yoktu).
# BU İŞARET BİR CEZA DEĞİL: veri yokluğu sembolün suçu değildir, karar yolu DEĞİŞMEZ (NO_GO yok,
# REVIEW'e düşürme yok). Yalnız GÖRÜNÜRLÜK — kapının o plan için konuşamadığı yazılı olsun.
# BİÇİM SÖZLEŞMESİ: metin "NOT: " ile başlar. Gerekçesi ölçülmüş bir yan etkidir —
# `analytics.gate_veto_tally` serbest metnin İLK İKİ KELİMESİNİ "veto ailesi" olarak sayar; önek
# olmasaydı bu not, kapının en sık vetosu gibi görünen bir kova açardı (planların ~%23'ü).
COVERAGE_NOTE = ("NOT: earnings_kapsami_yok — kazanç takvimi bu sembolü kapsamıyor; "
                 "karartma kapısı KONTROL EDEMEDİ (karar DEĞİŞMEDİ)")


def coverage_note(ticker: str) -> str | None:
    """Kapsam-dışı sembol için BEYANLI fail-open notu; kapsam içindeyse None (not yazılmaz)."""
    return None if known(ticker) else COVERAGE_NOTE


def coverage_tally(tickers) -> dict:
    """BİR TURUN kapsam sayacı — `coverage()` EVRENİ ölçer, bu ise o turda gerçekten PLANLANAN
    sembolleri. İkisi aynı sayı değildir (tarama zaten evrenin bir alt kümesini üretir) ve
    "bugün kaç plan karartma kontrolü OLMADAN geçti" sorusunun cevabı ikincisidir."""
    uni = [str(t).upper() for t in (tickers or [])]
    disi = [t for t in uni if not known(t)]
    return {"toplam": len(uni), "kapsanan": len(uni) - len(disi), "kapsam_disi": len(disi),
            "kapsam_disi_ornek": sorted(set(disi))[:12],
            # takvim TÜMÜYLE boşsa sayaç "hepsi kapsam dışı" der ve bu DOĞRUdur; ayrıca söylenir ki
            # okuyan "57 sembol eksik" ile "takvim hiç yok" arasını ayırabilsin
            "takvim_bos": not _load()}


def known(ticker: str) -> bool:
    """Bu sembol için takvimde HİÇ tarih var mı? in_blackout() False dönüyorsa iki şey demek olabilir:
    'kontrol edildi, temiz' ya da 'hiç veri yok'. İkisi aynı şey DEĞİL (denetim turu 11)."""
    return bool(_load().get((ticker or "").upper()))


def coverage(tickers: list | None = None) -> dict:
    """Karartma guard'ı GERÇEKTEN kaç sembolü koruyor? Canlıda 250 evrenin 181'i biliniyordu; kalan
    69'unda guard sessizce KAPALIYDI ve hiçbir yer bunu söylemiyordu. Ayrıca takvim bayatlarsa
    (gelecek tarih kalmazsa) guard herkes için kapanır — bunu da burada söylüyoruz."""
    import datetime as _dt
    data = _load()
    today = _dt.date.today().isoformat()
    future = sum(1 for ds in data.values() for d in ds if d >= today)
    all_dates = [d for ds in data.values() for d in ds]
    out = {"known_tickers": len(data), "future_dates": future,
           "max_date": max(all_dates) if all_dates else None,
           "inert": future == 0,          # gelecek tarih yoksa guard fiilen KAPALI
           # MARJ TÜRETİLİR, YAZILMAZ (bkz. margin_days): üç girdiden biri değişirse burası da
           # kendiliğinden değişir. `ileri_gun` ise ÖLÇÜLEN gerçek: takvim bugünden kaç gün
           # ileriyi görüyor. `ileri_gun < BLACKOUT_DAYS` = guard bugün fiilen kör.
           "marj_gun": margin_days(),
           "ileri_gun": ((dt.date.fromisoformat(max(all_dates)) - _dt.date.today()).days
                         if all_dates and max(all_dates) >= today else 0),
           "saat_bilinen": len(_TIMES)}    # BMO/AMC birikiminin sayacı (bkz. TIME_TIGHTEN)
    if tickers:
        uni = [str(t).upper() for t in tickers]
        unknown = [t for t in uni if t not in data]
        out.update({"universe": len(uni), "unknown": len(unknown), "unknown_sample": unknown[:12],
                    "covered_pct": round(100 * (len(uni) - len(unknown)) / max(1, len(uni)), 1)})
    return out


# --------------------------------------------------------------------------------------------------
# TAKVİM GÜVENİLMEZLİĞİ — FAIL-CLOSED SEMBOLE DEĞİL, TAKVİME BAĞLI (2026-08-03, Rol-1 kararı A1)
# --------------------------------------------------------------------------------------------------
# ÖLÇÜLEN AYRIM (WP-D KALEM 3 raporu, research/olcumler/wpd_earnings_failopen/RAPOR.md):
#   "194/251 kapsama" bir KORUMA ölçüsü DEĞİL — önümüzdeki ~4 haftada rapor veren sembol sayısıdır.
#   Kapsam-dışı 59 sembolün büyük çoğunluğu raporu UFKUN ÖTESİNDE olduğu için bilinmiyor ve raporu
#   4 hafta ötede olan bir sembol zaten 5 günlük karartmaya GİREMEZ. Bu yüzden "sembol bilinmiyor →
#   karart" (seçenek A3) 390 planın 70'ini kilitler ve karşılığında neredeyse hiç risk kapatmaz.
#
# GERÇEK ARIZA BAŞKA BİR ŞEY ve CANLIDA GERÇEKLEŞTİ: 2026-07-25'te takvimde tek satır vardı
# (`TEST,2025-06-24`) ve `MECHANISM_STALE` "karartma guard'ı fiilen kapalı (0 çıktı)" dedi — kapı
# 59 sembolde değil, 251 SEMBOLÜN 251'İNDE geçirgendi. Ve `covered_pct` bunu GÖRÜNMEZ kılar
# (0/251 iken bile bir yüzde üretir). Yani ölçü aleti, ölçmesi gereken arızaya kördü.
#
# BU YÜZDEN KAPI TAKVİME BAĞLANDI: "bu SEMBOLÜ bilmiyorum" fail-open kalır (beyanlı, COVERAGE_NOTE);
# "bu TAKVİM karartma ufkunu taşıyamıyor" ise fail-closed olur ve TÜM sembolleri etkiler.
#
# ÜÇ SEBEP, ÜÇÜ DE ÖLÇÜLEBİLİR (tahmin yok):
#   ufuk_tukendi  — `ileri_gun < BLACKOUT_DAYS`: takvim karartma penceresinin SONUNU göremiyor,
#                   yani bugün karartmada olan bir sembolü kaçırıyor olabiliriz. (`inert`, yani
#                   hiç gelecek tarih kalmaması, bunun ileri_gun=0 hâlidir; ayrı sebep adıyla
#                   raporlanır çünkü operatöre farklı bir şey anlatır.)
#   kismi_pencere — son tazeleme penceresinin gün-kapsaması EARNINGS_FMP_FALLBACK_COVERAGE altında:
#                   kaçan gün-diliminde duyurulan bir rapor tarihi BİLİNMİYOR olabilir.
#
# İKİ ŞEY BİLEREK TETİKLEMİYOR:
#   (1) TAKVİM DOSYASI HİÇ YOKSA. Modülün açılış sözleşmesi "No CSV -> no-op, so the gate is present
#       and testable now and simply activates the day an earnings feed writes the file". Dosyanın
#       hiç olmaması "kapı bozuldu" değil "kapı henüz silahlanmadı" demektir; onu fail-closed'a
#       çevirmek taze kurulumu ve tüm replay/fikstür yollarını kilitlerdi — AYRI ve çok daha büyük
#       bir karar. Bayat/eksik BİR TAKVİM ise arızadır ve tetikler (2026-07-25 vakası tam budur).
#   (2) `kapsama` ÖLÇÜLMEMİŞSE (None). Süreç yeni doğmuş ve henüz pencere görmemiş olabilir;
#       None bir sayı değildir, "eksik" diye okumak uydurma olurdu (bu modülün her yerinde aynı kural).
CALENDAR_UNTRUSTWORTHY_NOTE = ("NOT: earnings_takvimi_guvenilmez — {sebep}; karartma kapısı BU TURDA "
                               "HİÇBİR sembolde konuşamıyor, plan GO yerine REVIEW'e düştü")


def last_refresh_window() -> dict:
    """Son tazeleme penceresinin süreç-içi sağlık kaydı (bu süreçte hiç tazeleme olmadıysa boş)."""
    return dict(_LAST_WINDOW)


def calendar_untrustworthy(tickers: list | None = None) -> dict | None:
    """TAKVİMİN KENDİSİ karartma ufkunu taşıyabiliyor mu? Taşıyorsa None (kapı normal çalışır).

    Taşıyamıyorsa `{"sebep", "detay", ...}` döner ve ÇAĞIRAN o turda tüm sembolleri karartma
    varsayılanına düşürür. Gerekçe ve iki bilinçli istisna yukarıdaki blokta.

    TUR BAŞINA BİR KEZ ÇAĞRILMALI, aday başına değil: `coverage()` `_load()`u tetikler ve o her
    çağrıda `stat()` yapar — 250 adaylık bir turda 250 sistem çağrısı, ölçtüğümüz şeye hiçbir şey
    katmadan maliyet olurdu."""
    if not (config.STATE / "earnings.csv").exists():
        return None                      # kapı henüz SİLAHLANMADI — istisna (1), yukarıda gerekçeli
    cov = coverage(tickers) or {}
    ileri = cov.get("ileri_gun")
    if ileri is not None and int(ileri) < BLACKOUT_DAYS:
        return {"sebep": ("takvimde hiç gelecek tarih kalmadı" if cov.get("inert")
                          else f"takvim yalnız {int(ileri)} gün ileri görüyor"),
                "kod": "takvim_atil" if cov.get("inert") else "ufuk_tukendi",
                "ileri_gun": int(ileri), "blackout_days": BLACKOUT_DAYS,
                "max_date": cov.get("max_date"), "known_tickers": cov.get("known_tickers")}
    kap = _LAST_WINDOW.get("kapsama")
    if kap is not None and float(kap) < EARNINGS_FMP_FALLBACK_COVERAGE:
        return {"sebep": f"son tazeleme penceresinin yalnız %{round(float(kap) * 100, 1)}'i geldi",
                "kod": "kismi_pencere", "kapsama": float(kap),
                "esik": EARNINGS_FMP_FALLBACK_COVERAGE, "dusen": _LAST_WINDOW.get("dusen"),
                "pencere": _LAST_WINDOW.get("pencere"), "olculdu": _LAST_WINDOW.get("at")}
    return None


def blackout_radar(tickers: list, on_date: str) -> dict:
    """öneri 2b — karartma radarı: 'neden işlem yapmadı?' sorusunu panelde cevaplar. Verilen evren
    için bugün karartmada olan semboller + bilinen bir SONRAKİ rapor tarihi. CSV boşsa dürüstçe
    empty=True döner (radar 'veri yok' der, boş liste 'karartma yok' gibi OKUNMAZ)."""
    data = _load()
    rows = []
    for t in tickers:
        ds = data.get(str(t).upper())
        if not ds:
            continue
        try:
            d0 = dt.date.fromisoformat(str(on_date)[:10])
        except ValueError:  # sessiz-yutma: biçimsiz/eksik tek alan; yalnız bu değer düşer, satır başına uyarı asıl sinyali log seline gömerdi
            break
        nxt = next((x for x in ds if dt.date.fromisoformat(x) >= d0), None)
        if in_blackout(t, on_date):
            rows.append({"ticker": str(t).upper(), "next_report": nxt,
                         "days_left": (dt.date.fromisoformat(nxt) - d0).days if nxt else None})
    return {"empty": not data, "date": on_date, "blackout": sorted(rows, key=lambda r: r["ticker"]),
            "known_tickers": len(data)}
