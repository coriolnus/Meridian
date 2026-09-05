"""dataset.py — replay evreninin ORTAK yükleyicisi + backtest pencere sabitleri.

NE YAPAR: bar verisini ve pencere/dilim tanımlarını TEK yerde toplar ki reflect ve run birebir aynı
veri ve aynı bölmeler üzerinde değerlendirsin. Isınma yılı (2021) IS penceresinin önündedir — 252
günlük trend şablonu ilk işlem gününden itibaren geçerli olsun. Endeks (SPY) serisi sert bütünlük
kapısından geçemezse ve elde iyi bir süreç-içi kopya yoksa IndexUnavailable FIRLATILIR: boş endeksle
devam etmek "veri yok" demek değil, bilinmeyen bir rejimi UYDURMAK olurdu (uydurma yasağı).

KİLİT GİRİŞLER: load() (replay evreni: bars_by_ticker + index_bars, süreç-içi önbellekli; TSK-116
düzeltme turu 1, 2026-09-03: opsiyonel `universe=` — None ise REPLAY_UNIVERSE ve önbelleğe
yazar/okur, liste verilirse önbelleği ATLAR), load_live() (canlı tarama: LIVE_UNIVERSE + açık
pozisyon/silahlı planı olan endeks-çıkışı ticker'lar (`_canli_korunan_evren`) + Finviz keşfi;
`session` yalnız KAPANMIŞ seans için aynı-akşam bacağını açar), load_cached() (ağa hiç çıkmadan
yalnız diskteki CSV önbelleğinden —
havuz işçileri birbirinin barlarını yeniden yazmasın, tüm walk-forward'lar aynı donmuş barları
görsün), fetch_end() (çağrı başına BUGÜN; import anında donmuş sabit uzun ömürlü süreçte
zamanlayıcıyı kalıcı kilitlemişti), pencere sabitleri: FETCH_START, IS_START, OOS_START, OOS_END,
HOLDOUT_END (DONMUŞ — yuvarlanırsa aşınma parmak izi her gün değişir ve aşınma sayacı birikemez;
insana-rapor tazeliği holdout_report_end()'te), OOS_FOLDS + EMBARGO_DAYS (purged/embargolu ardışık
fold'lar), ROTATION_ID/PENCERE_ID + PENCERE_KIYAS_UYARISI + ARSIV_GEOMETRILER (pencere rotasyonu:
eski geometri arşivlenir, silinmez; farklı geometrilerin skorları habersiz kıyaslanamaz).

DEĞİŞMEZLER: walk-forward bölmeleri SABİTTİR (bugünü izlemez) — kapı tekrarlanabilir, holdout donmuş
ve yeniden-değerlendirilmeyen bir pencere kalır. LOOK-AHEAD KARANTİNASI: Finviz'in bugünkü listesi
geçmişe uygulanamaz — genişletme load()'a değil load_live'a konur ve `_cache`'i KİRLETMEZ (yeni
sözlük döner); aksi hâlde canlı tur cache'i genişletir ve gelecek bilgisi replay'e sızardı. Bozuk
endeks asla önbelleğe çivilenmez; geçici kesintide son iyi süreç-içi kopya servis edilir. Okunamayan
ticker SESSİZCE düşmez — ticker başına bir kez uyarı yazılır. Emekli (delist) semboller keşiften
evrene geri giremez ve eleme sebebiyle birlikte kayda geçer.

OKUR/YAZAR: adapters.data üzerinden state/bars/*.csv önbelleğini okur (load fetch edebilir,
load_cached asla etmez); kendisi diske yazmaz — yazım adapters.data'nın işidir; olaylar obs
defterine düşer.
"""
from __future__ import annotations
import datetime as dt
import pandas as pd
from .adapters import data

# Full fetch window (cached to state/bars/). 2021 = indicator warmup. FETCH_END tracks TODAY so live
# data stays current — the dashboard's "today" advances as new sessions publish, instead of freezing at
# a hardcoded date. (The free source is delayed, so the last real bar may lag a few days.)
FETCH_START = "2021-01-01"


def fetch_end() -> str:
    """TODAY, computed PER CALL. This was a module constant frozen at import time — fatal in the
    long-lived server process: new sessions were fetched to disk but windowed away by the frozen end
    date, so the scheduler saw latest_bar <= last_date forever and NEVER advanced the portfolio again
    (live evidence: cycles=1 while caches ran 2 sessions ahead)."""
    return dt.date.today().isoformat()


FETCH_END = fetch_end()   # import-time snapshot kept ONLY for display (run.py banner); never window with it

# Walk-forward splits — FIXED (never track today) so the gate is reproducible and the holdout stays a
# frozen, never-re-evaluated window. IS = in-sample, OOS = gate window, HOLDOUT = human-only, never
# drives acceptance. Live paper trading advances past HOLDOUT_END; the gate never uses those bars.
#
# ==================================================================================================
# HOLDOUT ROTASYONU "R1" — UYGULANDI 2026-07-30 (operatör onayı: "holdout rotasyonunu da yap")
# ==================================================================================================
# NEDEN DÖNDÜ — İKİ ÖLÇÜLMÜŞ GEREKÇE, İKİSİ DE UYDURMA DEĞİL SAYILMIŞ:
#
# (1) AŞINMA LİMİTİ KAT KAT AŞTI, VE AŞMAYA DEVAM ETTİ. `oos_erosion` defteri R0 geometrisine sorulan
#     soruları sayıyor ve sayı bu rotasyon TASARLANIRKEN bile büyüdü — üç ölçüm, üç tarih:
#       Kural yazıldığında       290 sorgu (14,5× limit)
#       Rol 1 tasarımı yazıldığında 367 sorgu (18,4×)
#       R1 UYGULANDIĞINDA        **434 sorgu (21,7×)**   ← limit 20 (`EROSION_QUERY_LIMIT`)
#     Bu artış, gerekçenin kendisinin bir parçası: pencere biz onu tartışırken de aşınıyordu, yani
#     "biraz daha bekleyip toplayalım" seçeneği maliyetsiz DEĞİLDİ. Ek marj (`EROSION_EXTRA_MARGIN`) bir SEMPTOM
#     tedavisidir ve sahada bunu kanıtladı: PARA-v3 kabul sınavında aşınma marjı S2 adayını
#     vetoladı (2026-07-30). 434 kez sorulmuş bir pencere artık out-of-sample DEĞİLDİR ve hiçbir
#     marj onu yeniden out-of-sample yapmaz — tek gerçek çözüm pencereyi DÖNDÜRMEKTİR (analytics
#     `holdout_rotation_advice`, 2D değerlendiricisi; ÖNERİR, uygulamaz — uygulama operatör kararı).
#
# (2) ESKİ HOLDOUT YARI-TEMİZ, TAM TEMİZ DEĞİL — VE BU DÜRÜSTLÜK NOTU KODA GİRER. R0'ın holdout
#     dilimi [2025-12-31, 2026-07-10] kabul kararlarına HİÇ girmedi (kapı yasası onu okumaz), ama
#     İNSANA RAPORLANDI: pano ve tur raporları `holdout_score`u aylarca gösterdi. İnsan bir sayıyı
#     gördüyse, sonraki hipotezleri o sayıdan etkilenmiş olabilir — ölçmediğimiz ama VAR OLDUĞUNU
#     bildiğimiz bir seçilim kanalı. Bu yüzden o dilim R1'de **YARI-TEMİZ** sayılır: taze OOS verisi
#     olarak KULLANILIR (kanıt kıtlığı gerçek: n≈81-96'da P tavanı ~0,66), ama "hiç görülmemiş
#     veri" DİYE SUNULMAZ. Aradaki fark bu yorumun kendisidir ve rapora da girer.
#
# R1 ÇİFTE KAZANCI:
#   • EN ÇOK KAZILMIŞ ERKEN DİLİM SEARCH'TEN ÇIKAR: [2023-07-01, 2024-01-01) — 434 sorgunun
#     tamamının içinden geçtiği altı ay artık kapı penceresinde DEĞİL.
#   • ESKİ HOLDOUT'UN ~4 AYI TAZE OOS OLUR: [2026-01-01, 2026-04-30] kapı penceresine girer.
#   • YENİ DONDURULMUŞ HOLDOUT: [OOS_END, HOLDOUT_END] = [2026-04-30, 2026-07-30] — sıfır sorgu.
#
# BEDELİ AÇIKÇA YAZILI: parmak izi değişir → R0'ın p/ΔS/PARA sayıları R1'de KARŞILAŞTIRILAMAZ
# (bkz. `PENCERE_KIYAS_UYARISI`). Aşınma sayacı R1'de sıfırdan başlar; bu "aşınma yok" demek değil,
# "R1'de henüz ölçülmedi" demektir — R0 kayıtları SİLİNMEZ, `arsiv_R0` damgası alır.
ROTATION_ID = "R1"                     # yürürlükteki pencere kimliği — her yeni kayda damgalanır
ROTATION_DATE = "2026-07-30"           # R1'in uygulandığı gün (operatör onaylı)
ROTATION_PREV_ID = "R0"                # döndürülen geometri: arşivlenir, silinmez
PENCERE_ID = ROTATION_ID               # kayıt alanının adı (`pencere_id`) ile aynı okunsun diye

# HABERSİZ KIYAS YASAĞI — tek cümle, üç tüketici (ledgers sözleşmesi, pano doğrulama satırı, rapor).
PENCERE_KIYAS_UYARISI = (
    "PENCERE R1 (2026-07-30 rotasyonu): R0 geometrisinde (OOS 2023-07-01→2025-12-31) ölçülmüş "
    "p/ΔS/PARA değerleri R1 değerleriyle KARŞILAŞTIRILAMAZ — aynı ada sahip iki farklı sınavdır. "
    "R0 kayıtları arşivde durur (arsiv_R0), silinmedi; habersiz kıyas YASAK.")

IS_START = "2022-01-01"                # R1'de AYNEN KORUNDU: IS tabanı taşınmaz (ısınma yılı 2021)
# 2026-07-20 PENCERE GENİŞLETMESİ (operatör onaylı): 250'lik evrende motor daha seçici — eski 18 aylık
# OOS penceresi 24 işlem üretiyor (min_sample 30 altı → skor dürüstçe tanımsız, olasılıksal dilim ince).
# OOS başlangıcı 12 ay geriye alındı (18→30 ay): AYNI istatistiksel çıtayla daha çok kanıt — gevşetme
# değil, örneklem büyütme. Kapı her karşılaştırmada iki tarafı da aynı pencerede yürüttüğünden
# elma-elma korunur; eski hipotez kayıtlarındaki sayılar kendi pencerelerinin bağlamında tarihsel kayıttır.
# 2026-07-30 R1 ROTASYONU: OOS 30 ay → 28 ay (851 gün) kaydırıldı; UZUNLUK neredeyse aynı, dilim
# TAZE — yani örneklem büyütmesi geri alınmadı, pencere ÖTELENDİ.
OOS_START = "2024-01-01"               # R1 (R0: 2023-07-01) — en çok kazılmış 6 ay Search'ten çıktı
OOS_END = "2026-04-30"                 # R1 (R0: 2025-12-31) — eski holdout'un ~4 ayı taze OOS oldu
# HOLDOUT SONU **DONDURULDU, YUVARLANMIYOR** — BEYAN EDİLMİŞ SAPMA (Rol 1 tasarımı "yuvarlanır"
# diyordu). ÖLÇÜLMÜŞ GEREKÇE: `oos_erosion.fingerprint` girdilerinin arasında `holdout_end` VAR.
# Bugünü izleyen bir holdout sonu, parmak izini HER GÜN değiştirir → aşınma sayacı her gün sıfırdan
# başlar → R1'in var olma sebebi olan ölçüm (④ "sayaç yeni pencerede birikmeye devam eder") yapısal
# olarak imkânsız hâle gelirdi. Yani "yuvarlanan holdout" ile "biriken aşınma sayacı" AYNI ANDA
# doğru olamaz; ikisinden aşınma ölçümü korunur, çünkü rotasyonun sebebi odur.
# Yuvarlanma İSTEĞİ kaybolmuyor: `holdout_report_end()` bugünü döner ve YALNIZ insana-rapor
# yolunda kullanılır (pencerelemeye ve parmak izine ASLA girmez). Holdout'un ileri taşınması
# SONRAKİ rotasyonda, operatör kararıyla olur — takvimle kendi kendine değil.
HOLDOUT_END = "2026-07-30"             # R1 (R0: 2026-07-10) = ROTATION_DATE, DONMUŞ

# Purged + embargoed multi-fold OOS: the gate requires a candidate to beat the incumbent across
# SEVERAL sequential windows (not one lucky window), and trades opened within EMBARGO_DAYS of a fold
# boundary are dropped from that fold so a position straddling the boundary can't leak across it.
# R1 TAKVİM FOLD'LARI: R0'ın çeyrek-hizalı deseni korunur (274/273/303 gün — R0: 275/275/364, yani
# DAHA dengeli). Bunlar TABANDIR: kapı yasası fold'ları incumbent'ın işlem dağılımından yeniden
# keser (`backtest.balanced_fold_bounds`, n-dengeli kesim) ve o kesim R1 geometrisinde kendiliğinden
# yeniden oluşur — takvim fold'ları yalnız dilimsiz/legacy yolun tabanı olarak durur.
OOS_FOLDS = ["2024-01-01", "2024-10-01", "2025-07-01", "2026-04-30"]   # -> 3 sequential folds (~9-10 ay)
EMBARGO_DAYS = 10

# ---- R0 GEOMETRİSİ: SİLİNMEDİ, ARŞİVLENDİ -------------------------------------------------------
# NEDEN KODDA DURUYOR: `arsiv_R0` damgasını atan yol (oos_erosion.arsivle) hangi parmak izinin R0
# olduğunu BİLMEK zorunda, ve testler R1'in gerçekten FARKLI bir geometri olduğunu R0'a bakarak
# çiviler. Değerleri buradan silmek, "eski kayıtlar karşılaştırılamaz" cümlesini doğrulanamaz bir
# iddiaya çevirirdi. RETRO DAMGA YASAĞI: bu sözlük eski KAYITLARIN İÇERİĞİNİ değiştirmez; yalnız
# hangi geometrinin arşivlendiğini beyan eder.
ARSIV_GEOMETRILER: dict[str, dict] = {
    "R0": {"is_start": "2022-01-01", "oos_start": "2023-07-01", "oos_end": "2025-12-31",
           "holdout_end": "2026-07-10", "embargo_days": 10,
           "folds": ["2023-07-01", "2024-04-01", "2025-01-01", "2025-12-31"],
           "arsivlendi": ROTATION_DATE, "sorgu_sayisi_arsivde": 434,
           "not": "R1 rotasyonuyla arşive alındı (aşınma 434/20 = 21,7×). Holdout dilimi "
                  "[2025-12-31, 2026-07-10] kabule HİÇ girmedi ama insana raporlandı → YARI-TEMİZ; "
                  "R1'de OOS'a alınan [2026-01-01, 2026-04-30] bu sıfatla kullanılır."},
}


def holdout_report_end() -> str:
    """İNSANA-RAPOR yolunun holdout sonu = BUGÜN. Pencerelemeye ve parmak izine ASLA girmez.

    Ayrı fonksiyon olmasının tek sebebi budur: `HOLDOUT_END` donmuş kalır (aşınma sayacı birikebilsin
    diye), ama "dondurulmuş holdout bugüne kadar uzanıyor" cümlesini rapor tarafı yine söyleyebilir.
    İki değeri tek sabitte birleştirmek, kapının reproducibility'siyle raporun tazeliğini aynı
    değişkene bindirmek olurdu — ve o değişken kapı tarafında kazanmak zorundadır.

    TEK TÜKETİCİSİ `analytics.holdout_rotation_advice` (pano → holdout durumu). YASA 6 gereği bu
    yazılıdır: tüketicisi olmayan bir "yuvarlanan holdout" fonksiyonu, yuvarlanma İSTEĞİNİ karşılamış
    gibi görünen ama hiçbir insana hiçbir şey söylemeyen bir dekor olurdu."""
    return fetch_end()


_cache: dict = {}


class IndexUnavailable(RuntimeError):
    """Endeks (SPY) serisi SERT bütünlük kapısından geçemedi ve elde iyi bir kopya da yok.

    Bu bir uyarı değil DURDURUCUdur: rejim sınıflaması (regime.classify → ind.atr(index_bars)),
    seans seçimi (loop: index'in son barı) ve karşılaştırma pencerelerinin TAMAMI bu tek seriye
    dayanır. Boş endeksle devam etmek "veri yok" demeyi değil, bilinmeyen bir rejimi UYDURMAYI
    getirir. Çağıranların hepsi (scheduler._run, run.worker, hermes_runtime, arming, reflect)
    istisnayı yakalayıp kaydeder — yani hata GÖRÜNÜR olur, sessizce boş kesitte karar alınmaz."""


def _index_hard_issues(index) -> list[dict]:
    """Endeks serisinin SERT bulguları. validate_bars ile AYNI şekil (dict listesi) döner — eski
    kod boş seride `["empty"]` diye DİZGİ listesi üretiyordu; canlı defterdeki
    `index_bars_invalid {"issues": ["empty"]}` satırlarının kaynağı buydu ve bulgu şekli
    tüketiciye göre değiştiği için makine tarafından okunamıyordu."""
    try:
        ok, issues = data.validate_bars(index, data.INDEX_SYMBOL)
    except Exception as e:
        # validate'in KENDİSİ patladıysa (kolon yok, bozuk tip) bu da sert bir bulgudur; eskiden
        # blanket `except: pass` ile yutuluyordu ve bozuk endeks GEÇERLİ sayılıyordu.
        return [{"severity": "hard", "code": "validate_failed", "detail": f"{type(e).__name__}: {e}"}]
    return [] if ok else [i for i in issues if i.get("severity") == "hard"]


def load(use_cache: bool = True, universe: list[str] | None = None) -> tuple[dict, pd.DataFrame]:
    """Return (bars_by_ticker, index_bars) for the replay universe. Cached in-process.

    `universe` (TSK-116, 2026-09-03, Rol-1 kararı): `None` (varsayılan) REPLAY_UNIVERSE sorar ve
    düz `_cache["bars"]`/`_cache["index"]` çiftini kullanır — replay/backtest/recompute davranışı
    BİREBİR, hiçbir çağıranın imzası ya da şekli değişmedi (dış testler bu iki anahtara doğrudan
    yazıyor/okuyor, bkz. test_finviz_v81.py). Bir LİSTE verilirse (canlı yolun LIVE_UNIVERSE +
    korunan ticker çağrısı, bkz. `_load_live_inner`) AYRI bir bölmede (`_cache["custom"][imza]`)
    hafızaya alınır — imza `tuple(sorted(upper(ticker)))`.

    ÖNBELLEK TASARIMI r3'te DEĞİŞTİ (düzeltme turu 3, 2026-09-03 — review Bulgu 1, "bedel yasası"):
    r1'de custom çağrı önbelleği NE okuyor NE yazıyordu ("zararsız" sanılmıştı) — ama `_load_live_inner`
    HER canlı pollde custom çağırdığı için (`_canli_korunan_evren()` asla None dönmez) canlı yolun
    süreç-içi kısayolu TAMAMEN devre dışı kalmıştı: `scheduler.py`nin "cache-only poll" fazı (300sn
    kadans, günde ~288 tur) her turda ~238 CSV'yi baştan okuyup sanitize ediyordu — SEYREK FAZ'ın var
    oluş sebebi olan maliyeti tam da onun içinde yeniden ödetiyordu. ÇÖZÜM: custom evren de kendi
    imzasıyla hafızaya alınır — AYNI imzayla (canlı poll AYNI LIVE_UNIVERSE+korunan kümesini ister,
    yalnız pozisyon/silahlı-plan değiştiğinde kayar) ikinci çağrı DİSKTEN OKUMAZ. LOOK-AHEAD
    KARANTİNASI GEÇERLİLİĞİNİ KORUR: custom bölme REPLAY'in `_cache["bars"]`ına hiç yazmaz/okumaz,
    kendi ayrı anahtarında durur — replay'in donmuş barlarına hâlâ karışmaz, yalnız KENDİ evreni
    kendi kendini kirletmiyor.

    BOZUK-ENDEKS KURTARMA DALI (`have_good`) İMZAYA SADIK KALIR (review Ö-3): önceki tasarım
    `custom`'a BAKMADAN REPLAY-ölçekli `_cache["bars"]`'ı (251, 13 endeks-çıkışı DAHİL) dönüyordu —
    "zararsız superset" savı yalnız replay/backtest için doğrudur; canlı/aday-tarama yolunda `bars`
    aday havuzunun KENDİSİdir (`loop.daily_cycle`), yani "fazla" burada D2/D4'ün "yeni giriş
    üretmez" garantisini bozar. Artık kurtarma dalı ÖNCE kendi imzalı bölmesine (`slot[sig]`) bakar;
    yoksa REPLAY'in `_cache["bars"]`'ını `uni`ye KIRPAR (`{t: v for t, v in ... if t in uni}`) —
    döndürülen anahtar kümesi HER ZAMAN `uni`nin alt kümesidir, asla üst kümesi değil.

    Raises IndexUnavailable when the index series fails the HARD integrity gate and no previously
    good in-process copy exists."""
    custom = universe is not None
    uni = list(universe) if custom else data.REPLAY_UNIVERSE
    sig = tuple(sorted({str(t).upper() for t in uni})) if custom else None
    slot = _cache.setdefault("custom", {}) if custom else None

    def _kirp_kurtarma():
        """Kurtarma dalı ortak gövdesi (Ö-3): önce AYNI imzalı önceki sonuç, yoksa REPLAY
        önbelleğinin `uni`ye kırpılmış hâli — asla REPLAY'in tam süperseti DEĞİL."""
        if not custom:
            return _cache["bars"], _cache["index"]
        onceki = slot.get(sig)
        if onceki is not None:
            return onceki
        taban = _cache.get("bars") or {}
        istenen = set(uni)
        return {t: v for t, v in taban.items() if t in istenen}, _cache["index"]

    if custom:
        if use_cache and sig in slot:
            return slot[sig]
    elif _cache.get("bars") is not None and use_cache:
        return _cache["bars"], _cache["index"]
    end = fetch_end()                                  # per-call TODAY — never the import-time snapshot
    index = data.load_bars(data.INDEX_SYMBOL, FETCH_START, end, use_cache=use_cache)
    bars = data.load_many(uni, FETCH_START, end, use_cache=use_cache)
    # the ONE series that drives regime classification was the only one never validated
    hard = _index_hard_issues(index)
    if hard:
        from . import obs
        have_good = _cache.get("index") is not None and len(_cache["index"]) > 0
        obs.warn("index_bars_invalid", issues=hard[:5],
                 codes=",".join(str(i.get("code")) for i in hard[:5]),
                 rows=0 if index is None else int(len(index)),
                 action="son iyi kopya kullanıldı" if have_good else "SERT DURUŞ",
                 detail="endeks serisi rejim/seans seçiminin TEK dayanağıdır; bozuk endeksle "
                        "karar alınmaz")
        if have_good:
            # transient all-source outage during a cache-bypassing refetch must NOT pin an empty
            # dataset for the rest of the session (the scheduler would then run daily_cycle on zero
            # data) — keep the last good in-process copy instead.
            return _kirp_kurtarma()
        # BOZUK ENDEKSİ ASLA ÖNBELLEĞE ÇİVİLEME: eskiden buraya düşen tur `_cache["index"] = <boş>`
        # yazıyordu ve süreç ömrü boyunca HER `load(use_cache=True)` o boş seriyi sessizce servis
        # ediyordu — tek bir geçici kesinti kalıcı bir yanlış duruma dönüşüyordu.
        raise IndexUnavailable(
            "endeks (%s) sert bütünlük kapısını geçemedi: %s" %
            (data.INDEX_SYMBOL, ", ".join(str(i.get("code")) for i in hard)))
    if not bars and _cache.get("bars"):
        return _kirp_kurtarma()
    if custom:
        slot[sig] = (bars, index)
    else:
        _cache["bars"], _cache["index"] = bars, index
    return bars, index


def load_live(use_cache: bool = True, session: str | None = None) -> tuple[dict, pd.DataFrame]:
    """CANLI ileri-yürüyen tarama evreni: REPLAY_UNIVERSE + Finviz'in BUGÜNKÜ momentum/kırılım keşfi.
    YALNIZ scheduler'ın canlı çağrısı kullanır; replay/backtest/yansıma ASLA (look-ahead bias).

    `session`: AYNI-AKŞAM BACAĞININ KAPISI (2026-07-30). Verilirse — ve yalnız verilirse — Alpaca
    IEX bacağı zincirin sonunda devreye girebilir. Değer GERÇEKTEN KAPANMIŞ bir seans olmalıdır
    (tek yasa: scheduler._last_closed_session); seans İÇİNDE çağrılırsa sağlayıcı KISMİ günlük bar
    döndürür ve o bar kapanış sanılırdı. Kapının burada olmasının sebebi 1. kuralın aynısıdır:
    `load()` hem replay hem canlı yolun ortak girişidir, bu yüzden "bugünün temsilî barı" iznini
    load_live DIŞINDA hiçbir çağıran veremez — replay 2023'ü yürütürken bugünün barını GÖREMEZ.

    İKİ SIKI KURAL:
      1. LOOK-AHEAD KARANTİNASI: Finviz'in bugünkü listesi geçmişe uygulanamaz. Bu yüzden genişletme
         `load()`'a DEĞİL buraya konur ve `_cache`'i KİRLETMEZ — `{**bars, ...}` yeni bir sözlüktür,
         `_cache["bars"]` dokunulmadan kalır. Aksi hâlde canlı tur cache'i genişletir, sonraki
         reflect'in çağırdığı sonraki `load()` aynı genişletilmiş cache'i okur ve gelecek bilgisi 2023 replay'ine sızardı.
      2. DÜRÜST BOZUNMA: Finviz düşükse `discover_universe()` boş döner (olayı kendi yazar) ve evren
         sessizce REPLAY_UNIVERSE'e iner. Finviz ekstra ticker'ların barı FMP zincirinden gelir;
         barı çekilemeyen ticker zaten `load_many` içinde düşer (tarama onu görmez).

    TABAN ARTIK LIVE_UNIVERSE (TSK-116 düzeltme turu 1, 2026-09-03, Rol-1 kararı): önceki turda bu
    fonksiyonun tabanı (`load()`) hâlâ REPLAY_UNIVERSE'i sorup 13 endeks-çıkışı sembolü `bars`e
    dahil ediyordu — yalnız Finviz'in yeniden-keşfi engelleniyordu, ki `extra`nın zaten `bars`'ta
    olan bir ismi hiç içermemesi yüzünden bu süzgeç fiilen no-op'tu. Artık `_load_live_inner`
    `load(universe=...)`u AÇIKÇA `LIVE_UNIVERSE + korunan ticker'lar` ile çağırıyor (bkz.
    `_canli_korunan_evren`): `loop.daily_cycle`ın gördüğü aday havuzu GERÇEKTEN 244 sembole daralır
    (TSK-143 2026-09-05 İKİNCİ revizyonu — sayı ÖNCEKİ turda 238'di, hiç S&P 500 üyesi olmamış 6
    sembol operatör kararıyla LIVE_UNIVERSE'e geri döndüğü için 244'e YÜKSELDİ; bkz. data.py
    ENDEKS_CIKISI_BEYANLI/HIC_UYE_BEYANLI şerhi) (+ açık pozisyon/silahlı planı olan endeks-çıkışı
    ticker'lar, YALNIZ çıkış yönetimi için — yeni giriş üretmezler, çünkü kapı/arming katmanı
    skor/sinyal üretimini bu `bars` kümesinden türetir)."""
    with data.live_session_leg(session):
        return _load_live_inner(use_cache=use_cache)


def _canli_korunan_evren() -> list[str]:
    """LIVE_UNIVERSE + açık pozisyon/silahlı (onaylanmış, henüz dolmamış) plan taşıyan endeks-çıkışı
    ticker'lar (TSK-116 düzeltme turu 1, 2026-09-03, Rol-1 kararı: 'yalnız canlıdan çıkar' kararı
    açık pozisyonu barsız bırakmaz — manage_position/mirror çıkışı yönetebilsin diye barı YİNE
    yüklenir; yeni GİRİŞ zaten LIVE_UNIVERSE'in kendisi tarafından engellenir, çünkü endeks-çıkışı
    sembol aday havuzunda hiç görünmez).

    ÖLÇÜM: `portfolio.json` İKİ kümeyi de taşır — `positions` (açık pozisyonlar, dict) ve `armed`
    (onaylanmış/silahlı plan listesi, her biri kendi `ticker` alanıyla — bkz. loop.py'deki `_arm_yama` iç fonksiyonu).
    İkisi de dataset katmanından ERİŞİLEBİLİR: `store.read_json` aynı yol, `marketstream.
    subscribed_symbols`ın pozisyonlar için kullandığı YOLUN BİREBİR aynısı — o yüzden ek bir
    parametre (`load_live(..., ek_semboller=...)`) AÇILMADI, dataset katmanı zaten yeterli."""
    from . import store
    pf = store.read_json("portfolio.json", {}) or {}
    korunacak = {str(t).strip().upper() for t in (pf.get("positions") or {}).keys()}
    for pl in (pf.get("armed") or []):
        t = (pl or {}).get("ticker")
        if t:
            korunacak.add(str(t).strip().upper())
    korunan_endeks_disi = sorted(t for t in korunacak if data.is_index_exited(t))
    if not korunan_endeks_disi:
        return data.LIVE_UNIVERSE
    # SESSİZ İSTİSNA OLMAZ: LIVE_UNIVERSE'in "endeks-çıkışı sembol yok" kuralına neden bir istisna
    # açıldığı görünür olmalı — aksi hâlde "neden bu sembol hâlâ taranıyor" sorusu cevapsız kalır.
    from . import obs
    obs.log("index_exited_position_bars_kept", tickers=",".join(korunan_endeks_disi),
            n=len(korunan_endeks_disi),
            detail="endeks-çıkışı sembolde açık pozisyon/silahlı plan var — barı canlı yolda YİNE "
                   "yüklendi (yeni giriş üretmez, yalnız manage_position/mirror çıkışı yönetsin "
                   "diye); TSK-116 düzeltme turu 1, 2026-09-03")
    return data.LIVE_UNIVERSE + korunan_endeks_disi


def _load_live_inner(use_cache: bool = True) -> tuple[dict, pd.DataFrame]:
    """load_live'ın GÖVDESİ. Ayrı fonksiyon çünkü bacak kapısı bir `with` bloğudur ve `return`
    noktaları üçe dağılmıştı — kapıyı her çıkışta tek tek kapatmak, bir gün eklenen dördüncü
    çıkışta unutulurdu (bacak açık kalır ve sonraki çağıran onu miras alırdı)."""
    bars, index = load(use_cache=use_cache, universe=_canli_korunan_evren())
    try:
        from .adapters import finviz
        extra = [t for t in finviz.discover_universe(use_cache=use_cache) if t not in bars]
        # EMEKLİ SEMBOL GERİ GİREMEZ (2026-07-30). Finviz ekranı üçüncü taraf bir listedir ve delist
        # olmuş bir ismi (kalıntı kayıt, gecikmiş endeks) yeniden önerebilir; o isim buradan geçerse
        # tarama evrenine girer, barı çekilmeye çalışılır ve ölü bir sembol hakkında karar üretilir.
        emekli = [t for t in extra if data.is_retired(t)]
        # TSK-116, 2026-09-03: endeks-çıkışı AYRI bir hüküm sınıfıdır — RETIRED_SYMBOLS ile
        # INDEX_EXITED kesişmez (data.py'de çivilenir), o yüzden aynı ticker iki listeye BİRDEN
        # düşmez. Ayrı olay adıyla yazılır ki "delist" ile "S&P 500 çıkışı" karıştırılmasın.
        endeks_disi = [t for t in extra if data.is_index_exited(t)]
        if emekli or endeks_disi:
            extra = [t for t in extra if not data.is_retired(t) and not data.is_index_exited(t)]
            # SESSİZ FİLTRE OLMAZ: eleme kendi başına doğru davranıştır ama SEBEBİ görünmezse,
            # keşif kaynağının bayat bir evren servis ettiğini kimse öğrenemez. Olay o kaynağa
            # bakmak için yazılır — elenen sembole değil.
            from . import obs
            if emekli:
                obs.log("retired_symbol_rediscovered", tickers=",".join(sorted(emekli)), n=len(emekli),
                        detail="Finviz keşfi delist olmuş sembol önerdi — evrene ALINMADI "
                               "(data.RETIRED_SYMBOLS); keşif kaynağının listesi bayat olabilir")
            if endeks_disi:
                obs.log("index_exited_symbol_rediscovered", tickers=",".join(sorted(endeks_disi)),
                        n=len(endeks_disi),
                        detail="Finviz keşfi S&P 500 dışına çıkmış (ama aktif) sembol önerdi — "
                               "canlı evrene ALINMADI (data.INDEX_EXITED); geçmiş replay etkilenmez "
                               "(TSK-116, 2026-09-03)")
    except Exception as e:  # sessiz-yutma DEĞİL: Finviz keşfi düşse bile canlı tarama REPLAY_UNIVERSE ile sürer; olay burada yazılır ve evren daralması dürüstçe görünür
        from . import obs
        obs.warn("finviz_discover_failed", error=f"{type(e).__name__}: {e}",
                 detail="evren yalnız REPLAY_UNIVERSE — Finviz genişletmesi bu tur atlandı")
        return bars, index
    if not extra:
        return bars, index
    end = fetch_end()
    extra_bars = data.load_many(extra, FETCH_START, end, use_cache=use_cache)
    return {**bars, **extra_bars}, index          # YENİ sözlük — _cache mutasyona uğramaz


_LOAD_WARNED: set = set()   # ticker başına bir kez — evren 500 sembol, log seli olmasın


def _load_warn(ticker: str, exc: BaseException) -> None:
    """Okunamayan önbellek barı için ticker başına TEK KEZ uyarı yazar (evren yüzlerce sembol — log seli
    olmasın). Uyarı kanalının kendisi düşerse yükleme ASLA düşmez."""
    if ticker in _LOAD_WARNED:
        return
    _LOAD_WARNED.add(ticker)
    try:
        from . import obs
        obs.warn("cached_bars_unreadable", ticker=ticker, error=f"{type(exc).__name__}: {exc}",
                 detail="ticker replay evreninden düştü")
    except Exception:
        # sessiz-yutma: kayıt kanalının kendisi düştü — ikinci kanal yok; telemetri denemesi
        # veri yüklemesini ASLA düşüremez.
        pass


def load_cached() -> tuple[dict, pd.DataFrame]:
    """AĞA HİÇ ÇIKMADAN, yalnız YERLEŞMİŞ disk önbelleğinden yükle — load() ile aynı şekil.

    NEDEN (2026-07-21'de canlıda bulundu): load() bayat önbellekte fetch eder; fetch corporate-action
    tespitini tetikleyip bar CSV'lerini SİLİP YENİDEN YAZAR. Süreç havuzundaki her işçi kendi load()'unu
    çağırdığından, işçiler BİRBİRİNİN barlarını yeniden yazabiliyordu → aynı aramadaki sondalar FARKLI
    bar durumlarında ölçülüyordu (elma-armut). Kanıt: aynı incumbent 0.2043/0.1941/0.1130/0.0988.
    Bu yol fetch ETMEZ: ebeveyn load() ile önbelleği yerleştirir, işçiler o donmuş hali okur → tüm
    walk-forward'lar birebir aynı barlar üzerinde. Tek doğruluk kaynağı: diskteki CSV'ler."""
    end = fetch_end()

    def _read(t: str):
        """Tek tickerın disk önbelleğini okur, temizler ve pencereye kırpar. Dosya yoksa ya da temizlik
        sonrası boşsa None. AĞA ÇIKMAZ — bu yolun tüm varlık sebebi budur."""
        cp = data._cache_path(t)
        if not cp.exists():
            return None
        try:
            # TICKER ADIYLA GEÇİLİR (2026-07-30): sanitize artık takvim-dışı (hayalet seans) satırı
            # DÜŞÜRÜYOR ve olayı sembol adıyla yazıyor. Ad verilmezse defterde "?" görünür ve
            # "hangi sembolde" sorusu — havuz işçilerinde koşan tam da bu yol için — cevapsız kalır.
            df, _ = data.sanitize_bars(pd.read_csv(cp, parse_dates=["date"]), t)
            if df is None or df.empty:
                return None
            return data._window(df, FETCH_START, end)
        except Exception as e:
            # YASA 4 (2026-07-21): burada None dönmek, ticker'ı replay evreninden SESSİZCE düşürür.
            # Hata yok, istisna yok — yalnız daha küçük bir evren ve dolayısıyla başka bir backtest
            # sonucu. "Gerçek 0" bulgusunun aynı ailesi: kayıp satır kimseye sorulmadan eleniyor.
            _load_warn(t, e)
            return None

    index = _read(data.INDEX_SYMBOL)
    bars = {}
    for t in data.REPLAY_UNIVERSE:
        df = _read(t)
        if df is not None and not df.empty:
            bars[t] = df
    return bars, (index if index is not None else pd.DataFrame())
