"""research/olcumler/edg082_pit_tohum/olcum.py — EDG-2026-082 ÖLÇÜM aracı (TSK-159 S2, 2026-09-06).

NE ÖLÇER. Kart `research/cards/EDG-2026-082-tohum-pit-uyelik-suzgeci-kiyasi.yaml`nin hipotezi:
aynı parametre/hedef/takvimle üç koşum — TABAN (`uyelik=None`, bugünkü davranış), A
(`uyelik(t)=as_of(t)`, saf S&P PIT), B (`as_of(t) ∪ data.HIC_UYE_BEYANLI`) — arasında kapı
hükümlerinin SINIFI (OOS composite eşiği, DSR, PBO) DEĞİŞİYOR mu; EDG-079'un ölçtüğü 95 sızıntı
işlemin A'da tamamen düşüp düşmediği, B'de yalnız hiç-üye 39'unun kalıp kalmadığı.

ROL: ÖLÇÜM ajanı. AĞA ÇIKMAZ (yalnız verilen dosyalar/`--bars-dir` okunur), karta DOKUNMAZ,
`meridian/*.py`ye DOKUNMAZ (yalnız İTHAL EDER — `backtest.replay/walk_forward`in `uyelik`
parametresi TSK-159 S2'de main'e zaten indi, bu betik onu ÇAĞIRIR), canlı `state/`e YAZMAZ.
Motor "saf hesap"tır (`backtest.py` modül başlığı: "state'e yazmaz; bar/goal okur") — ama
`sanitize_bars`/`measurement_bars` NADİR olay yollarında (`_note_ghost`) `obs.warn` çağırabilir;
bu yüzden bu betik o ikisini HİÇ ÇAĞIRMAZ, kendi MİNİMAL temizliğini yapar (`temiz_bar_oku`) ve
ATLANAN iki adımı (`ATLANAN_TEMIZLIK_ADIMLARI`) sonuçta AÇIKÇA beyan eder (Yasa 6).

GİRDİLER (`--olc` bunları OKUR, yazmaz):
  --bars-dir <dizin>     `<dizin>/<sembol-küçük-harf>.csv` (state/bars ile AYNI ad kuralı,
                         `data._cache_path`in kopyası DEĞİL — aynı formülü BAĞIMSIZ uygular çünkü
                         `data.py`ye dokunmak yerine dosya adı formülünü READ-ONLY tekrarlamak
                         daha ucuz bir bağ; formül üç satırlık ve TEK YERDE, `bar_dosya_yolu`).
  --girdi-html <html>    "Historical components of the S&P 500" değişiklik tablosunun ham HTML'i.
  --guncel-liste <json>  güncel S&P 500 üyelik listesi (liste[str]).
  --kart <yaml>          varsayılan EDG-2026-082 kartı (yalnız OKUNUR — eşikler/K kimlikleri).
  --sizanlar <json>      EDG-2026-079 `sonuc.json`u (95 sızıntının (ticker, ts_open) çiftleri,
                         `k1_tohum.sizanlar` + `k1_tohum.n` eski-tohum işlem sayısı çapası).
  --manifest-kontrol <json>  önceki bir `sonuc.json` — bar manifestosu (sha256'lar) EŞİT mi.
  --baslangic/--bitis    replay/tanımlayıcı istatistik penceresi (varsayılan 2022-01-01/2026-09-05).
  --cikti <json>         çıktı yolu (varsayılan bu dizinde `sonuc.json`).
  --yalniz TABAN|A|B     yalnız BİR koşumu çalıştırır (üçü de HÂLÂ adım-0 fizibilitesini ister).

ÜÇ KOŞUM, İKİ AYRI PENCERE. Betimleyici istatistikler (`n_islem`/`avg_r`/`medyan_r`/
`kazanma_orani`/sızıntı kontrolü) `--baslangic`–`--bitis` (TAM mevcut bar penceresi, eski tohumla
kıyas için) üzerinden `backtest.replay` ile; kapı hükümleri (`oos_score`, DSR, PBO) AYRICA
`backtest.walk_forward` ile CANLI fold tanımından (`meridian.dataset.IS_START/OOS_START/OOS_END/
HOLDOUT_END/OOS_FOLDS/EMBARGO_DAYS` — `reflect._default_windows`in okuduğu AYNI sabitler,
kopyalanmadı) kurulur; HOLDOUT_END (2026-07-30) `--bitis`ten (2026-09-05) ÖNCE donduğu için bu
ikinci pencere BİRİNCİNİN bir ALT-ARALIĞIDIR — iki ayrı `replay` koşumu (biri `walk_forward`
içinde gizli) kaçınılmazdır, birleştirilemez.

TABLO AYRIŞTIRMA + `as_of`: KOPYALANMADI. `research/olcumler/edg075_sp500_tarihsel/olcum.py`
`sys.path` ile İÇE AKTARILIR (`_edg075_yukle`, `edg079`nun AYNI deseni — tek-kaynak yasası).
RENAME SON-İŞLEMİ: `meridian.adapters.constituents.SEMBOL_YENIDEN_ADLANDIRMA` (YALNIZ sabit
içe aktarımı — `constituents.as_of`in KENDİ satırlarının bir KOPYASI, edg079'un `islem_uye_mi`
deseniyle AYNI ruh): rename `tarih`inden ÖNCEKİ bir sorgu için o tarihte GEÇERLİ olan ESKİ adla
değiştirilir (`pit_as_of`).

A/B UYELİK FONKSİYONLARI: `uyelik_fonksiyonlarini_kur` A ve B'nin İKİSİ İÇİN TEK bir tarih→üyelik
önbelleği (`onbellek_a`) paylaştırır — B, A'nın zaten kurduğu `as_of(d)` sonucunu YENİDEN KURMAZ,
yalnız `data.HIC_UYE_BEYANLI` ile BİRLEŞTİRİR (kart adım-0(d) süre kuralının ucuzlaması, ayrıca
raporlanır: `sure_kurali`).

SIZINTI KONTROLÜ: EDG-079'un 95 sızıntı (ticker, ts_open) çiftinin TABAN'ın KENDİ işlem kümesinde
GERÇEKTEN bulunanları (`eslesen` — TABAN'ın eski tohumla BİREBİR aynı olmaması beklenir, bkz.
`taban_sapma_kontrolu`) A'da ve B'de ne oldu diye izlenir. "Hiç-üye 39" ayrı bir alan DEĞİL,
`data.HIC_UYE_BEYANLI` (6 sembol) üyeliğiyle TÜRETİLİR: `eslesen` içindeki tickerı bu 6 sembolden
biri olanlar `hic_uye_esen` — B'nin uyelik fonksiyonu bu 6 sembolü KOŞULSUZ üye saydığı için
`hic_uye_esen`in TAMAMI B'de KALMALI, geri kalanı (`eslesen - hic_uye_esen`, "geç-katılan"/
"çıkış-sonrası") B'de de A'da da DÜŞMELİ.

DSR/PBO YAPISAL OLARAK NONE (Yasa 4 uydurma yasağı — önceki ajanın keşif notu, DOĞRULANDI): PBO
(`validation.pbo_cscv`) `PBO_MIN_ADAY` (8) AYRI aday ister — bu ölçüm TEK karttan K=2 (A, B) üretir,
ve PBO'nun ham maddesi zaten `validation_ledger.jsonl`teki RESMÎ kapı değerlendirmeleridir (bu
izole ölçüm hiçbirini yazmaz/okumaz — `pbo_cscv(rows=[])` AÇIKÇA boş listeyle çağrılır, `state/
validation_ledger.jsonl`e ASLA dokunulmaz). DSR (`validation.deflated_sharpe`) teknik olarak
`trial_sharpes=None` ile "sıfır-beceri null" yaklaşımına düşüp GÖZLEM serisinden hesaplanabilirdi,
ama `n_trials` (bu adayın "kaç deneme arasından seçildiği") bu ölçümün DIŞINDA tanımlı bir SAYI
DEĞİL — kartın K grid'i (A, B) bir ARAMA değil bir ÖN-KAYITLI KIYASTIR, `n_trials` uydurmak
(`reflect._gate_eval`in aşınma-defteri + k_probes toplamının BİR KOPYASI olmayan bir sayı) Yasa
4'ün TAM ihlali olurdu. Bu yüzden DSR de `dsr_kapi(None, live=False)` ile GERÇEK "olculemedi"
şeklini alır (fonksiyonun KENDİSİ çağrılır, şekli UYDURULMAZ). SONUÇ: kapı hüküm sınıfı kıyası
YALNIZ OOS composite üzerinden — payda `n/3` DEĞİL `n/1` (DSR/PBO paydaya GİRMEZ, ama alanları
`None` + neden ile HÂLÂ RAPORLANIR, sessizce atılmaz).

DİSİPLİN: UYDURMA YASAĞI (ölçülemeyen `None` + neden). YASA 4 (sessiz-yutma işaretli + gerekçe).
YASA 6 (okuyucu: `sonuc.json` → Rol-1 karta+K defterine işler; kart/ROADMAP/günlük bu betik
tarafından YAZILMAZ). ÇAPA YASAĞI: bu dosyada `dosya.py:NNN` biçimi hiç kullanılmaz."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import importlib
import json
import pathlib
import statistics
import sys
import time

import pandas as pd
import yaml

from meridian import backtest, config, dataset as dataset_mod, validation
from meridian.adapters import data as data_mod
from meridian.adapters.constituents import SEMBOL_YENIDEN_ADLANDIRMA

KOK = pathlib.Path(__file__).resolve().parents[3]
SANDBOX = pathlib.Path(__file__).resolve().parent
KART_YOLU = KOK / "research" / "cards" / "EDG-2026-082-tohum-pit-uyelik-suzgeci-kiyasi.yaml"
EDG075_DIR = KOK / "research" / "olcumler" / "edg075_sp500_tarihsel"

VARSAYILAN_BASLANGIC = "2022-01-01"
VARSAYILAN_BITIS = "2026-09-05"

# `sanitize_bars`/`measurement_bars` (meridian/adapters/data.py) ghost-session/izole-düzeltilmemiş-
# satır bulununca `obs.warn` çağırır (`_note_ghost`) — bu betik obs'a ULAŞMAMALI (ajan kuralı,
# pytest-dışı koşumda canlı yerel deftere yazar). `temiz_bar_oku` bu iki adımı BİLEREK ATLAR.
ATLANAN_TEMIZLIK_ADIMLARI = (
    "takvim_kapisi_XNYS_hayalet_seans_suzgeci",
    "izole_duzeltilmemis_satir_karantinasi",
)


# ======================================================================================
# edg075 olcum.py'yi sys.path ile İÇE AKTAR — KOPYALAMA DEĞİL (edg079 emsali, tek-kaynak yasası)
# ======================================================================================

def _edg075_yukle():
    """`research/olcumler/edg075_sp500_tarihsel/olcum.py`yi `sys.path` ile içe aktarır. Modül adı
    ("olcum") bu depoda JENERİKTİR — `sys.modules`'taki olası YANLIŞ önbellek bu betiğin KENDİ
    dosya yoluyla doğrulanır; eşleşmezse yeniden yüklenir (edg079 `_edg075_yukle` ile BİREBİR
    aynı desen — iki kopya sessizce ayrışmasın)."""
    dizin = str(EDG075_DIR)
    if dizin not in sys.path:
        sys.path.insert(0, dizin)
    beklenen = str(EDG075_DIR / "olcum.py")
    mevcut = sys.modules.get("olcum")
    if mevcut is not None and getattr(mevcut, "__file__", None) == beklenen:
        return mevcut
    sys.modules.pop("olcum", None)
    return importlib.import_module("olcum")


_edg075 = _edg075_yukle()
_edg075_tabloyu_ayristir = _edg075.tabloyu_ayristir
_edg075_as_of = _edg075.as_of


# ======================================================================================
# KART OKUMA — eşikler ÇALIŞMA ANINDA okunur, koda kopyalanmaz (edg071/edg075/edg079 emsali)
# ======================================================================================

def esikleri_karttan_oku(kart_yolu: pathlib.Path = KART_YOLU) -> dict:
    kart = yaml.safe_load(pathlib.Path(kart_yolu).read_text(encoding="utf-8"))
    if not isinstance(kart, dict):
        raise ValueError(f"kart sözlük değil: {kart_yolu}")
    esikler = kart.get("esikler")
    if not isinstance(esikler, dict):
        raise ValueError(f"kart 'esikler' alanı yok/sözlük değil: {kart_yolu}")
    for anahtar in ("k1_gecti", "k2_gecti"):
        if anahtar not in esikler:
            raise ValueError(f"kart eşiği '{anahtar}' bulunamadı ({kart_yolu}) — betik eşiği UYDURAMAZ")
    return {"k1_gecti": str(esikler["k1_gecti"]), "k2_gecti": str(esikler["k2_gecti"]),
            "kart_id": kart.get("card_id"), "kart_yolu": str(kart_yolu)}


def kart_yukle(kart_yolu: pathlib.Path = KART_YOLU) -> dict:
    kart = yaml.safe_load(pathlib.Path(kart_yolu).read_text(encoding="utf-8"))
    if not isinstance(kart, dict):
        raise ValueError(f"kart sözlük değil: {kart_yolu}")
    return kart


# ======================================================================================
# BAR OKUMA — TEMİZ OKUMA (sanitize_bars/measurement_bars OBS'A ULAŞABİLİR, ÇAĞRILMAZ)
# ======================================================================================

def bar_dosya_yolu(bars_dir, ticker: str) -> pathlib.Path:
    """`state/bars/<ticker>.csv` dosya-adı formülünün (`data._cache_path`) READ-ONLY tekrarı —
    küçük harf + '.'→'-' (BRK.B gibi semboller dosya adında noktalı olmasın)."""
    return pathlib.Path(bars_dir) / f"{str(ticker).lower().replace('.', '-')}.csv"


def temiz_bar_oku(bars_dir, ticker: str) -> tuple:
    """(df|None, meta). NaN/negatif OHLC satırı düşer, yinelenen tarih SONUNCUSU tutulur,
    kronolojik SIRALANIR, high/low OHLC zarfına KENETLENİR — bunların HİÇBİRİ obs çağırmaz.
    ATLANAN: takvim/hayalet-seans süzgeci ve izole-düzeltilmemiş-satır karantinası (`data.py::
    sanitize_bars`in `_note_ghost` yoluyla `obs.warn` çağırdığı İKİ adım) — `ATLANAN_TEMIZLIK_
    ADIMLARI`da BEYAN edilir, sessizce atlanmaz (Yasa 6)."""
    yol = bar_dosya_yolu(bars_dir, ticker)
    if not yol.exists():
        return None, {"bulundu": False, "sha256": None, "yol": str(yol)}
    ham = yol.read_bytes()
    sha = hashlib.sha256(ham).hexdigest()
    df = pd.read_csv(yol, parse_dates=["date"])
    n0 = len(df)
    df = df.dropna(subset=["open", "high", "low", "close"])
    df = df[(df[["open", "high", "low", "close"]] > 0).all(axis=1)]
    n_dropped = n0 - len(df)
    d0 = int(df["date"].duplicated().sum())
    if d0:
        df = df.drop_duplicates("date", keep="last")
    df = df.sort_values("date").reset_index(drop=True)
    hi = df[["open", "high", "low", "close"]].max(axis=1)
    lo = df[["open", "high", "low", "close"]].min(axis=1)
    df = df.assign(high=df["high"].where(df["high"] >= hi, hi),
                   low=df["low"].where(df["low"] <= lo, lo))
    meta = {"bulundu": True, "yol": str(yol), "sha256": sha, "n_satir_ham": n0,
            "n_dropped_nan_negatif": n_dropped, "n_dedup": d0, "n_satir_temiz": len(df),
            "atlanan_temizlik_adimlari": list(ATLANAN_TEMIZLIK_ADIMLARI)}
    return df.reset_index(drop=True), meta


def barlari_yukle(bars_dir, evren: list, index_symbol: str) -> dict:
    """(bars: dict[ticker, df], index_bars: df, bar_manifesti: dict[dosya_adi, sha256],
    eksik: list[ticker]). Endeks barı BULUNAMAZSA/BOŞSA ValueError (girdi zorunlu — uydurma yok)."""
    bars: dict = {}
    manifest: dict = {}
    eksik: list = []
    for t in evren:
        df, meta = temiz_bar_oku(bars_dir, t)
        if df is None or df.empty:
            eksik.append(t)
            continue
        bars[t] = df
        manifest[bar_dosya_yolu(bars_dir, t).name] = meta["sha256"]
    idx_df, idx_meta = temiz_bar_oku(bars_dir, index_symbol)
    if idx_df is None or idx_df.empty:
        raise ValueError(f"endeks barı bulunamadı/boş: {index_symbol} ({bars_dir}) — uydurulamaz")
    manifest[bar_dosya_yolu(bars_dir, index_symbol).name] = idx_meta["sha256"]
    return {"bars": bars, "index_bars": idx_df, "bar_manifesti": manifest, "eksik": eksik}


def manifest_kontrol(mevcut_manifest: dict, onceki_sonuc_yolu) -> dict:
    """`--manifest-kontrol <önceki sonuc.json>` — bar manifestosu (sha256'lar) BİREBİR eşit mi.
    Değilse `gecerli=False` + farklı dosyalar listelenir (kill: değiştiyse geçersiz, kart §5)."""
    onceki = json.loads(pathlib.Path(onceki_sonuc_yolu).read_text(encoding="utf-8"))
    onceki_manifest = ((onceki.get("girdi_kimligi") or {}).get("bar_manifesti")) or {}
    esit = mevcut_manifest == onceki_manifest
    fark = None
    if not esit:
        tum = sorted(set(mevcut_manifest) | set(onceki_manifest))
        fark = [d for d in tum if mevcut_manifest.get(d) != onceki_manifest.get(d)]
    return {"calisti": True, "gecerli": esit, "n_fark": len(fark) if fark else 0,
            "fark_dosyalar": fark, "onceki_sonuc_yolu": str(onceki_sonuc_yolu)}


# ======================================================================================
# GÜNCEL LİSTE + DEĞİŞİKLİK TABLOSU + PIT `as_of` (rename son-işlemiyle)
# ======================================================================================

def guncel_liste_oku(yol) -> list:
    veri = json.loads(pathlib.Path(yol).read_text(encoding="utf-8"))
    if not isinstance(veri, list):
        raise ValueError(f"güncel liste bir liste değil: {yol}")
    return [str(s).strip().upper() for s in veri if str(s).strip()]


def degisiklikleri_yukle(html_yolu) -> tuple:
    """(degisiklikler, meta, sha256). `_edg075_tabloyu_ayristir`e AYNEN devreder — KOPYALAMA YOK."""
    ham = pathlib.Path(html_yolu).read_bytes()
    sha = hashlib.sha256(ham).hexdigest()
    degisiklikler, meta = _edg075_tabloyu_ayristir(ham.decode("utf-8"))
    return degisiklikler, meta, sha


def pit_as_of(degisiklikler: list, guncel_set: set, tarih: str) -> set:
    """`_edg075_as_of` + `constituents.SEMBOL_YENIDEN_ADLANDIRMA` son-işlemi — `constituents.
    as_of`in KENDİ satırlarıyla AYNI kural (sabit YALNIZ İTHAL EDİLDİ, kopyalanmadı): rename
    `tarih`inden ÖNCEKİ bir sorgu için o tarihte GEÇERLİ olan ESKİ adla değiştirilir."""
    uyeler = set(_edg075_as_of(degisiklikler, guncel_set, tarih))
    for rn in SEMBOL_YENIDEN_ADLANDIRMA:
        if rn["tarih"] > tarih and rn["yeni"] in uyeler:
            uyeler.discard(rn["yeni"])
            uyeler.add(rn["eski"])
    return uyeler


def uyelik_fonksiyonlarini_kur(degisiklikler: list, guncel_liste: list, hic_uye=None) -> dict:
    """TABAN(None)/A(as_of)/B(as_of ∪ hiç-üye) uyelik fonksiyonlarını + PAYLAŞILAN tarih-başına
    önbelleği kurar. `hic_uye` verilmezse `data.HIC_UYE_BEYANLI` anahtarları kullanılır (test
    kendi kümesini VEREBİLİR — sentetik evren gerçek sembol adı taşımayabilir).

    B, A'nın ZATEN kurduğu `pit_as_of(d)` sonucunu YENİDEN HESAPLAMAZ — aynı `onbellek` sözlüğünü
    okur, yalnız hiç-üye kümesiyle BİRLEŞTİRİR (kart adım-0(d) süre kuralının ucuzlaması)."""
    guncel_set = {s.upper() for s in guncel_liste}
    hic_uye_set = set(hic_uye) if hic_uye is not None else set(data_mod.HIC_UYE_BEYANLI)
    onbellek: dict = {}
    cagrilar_a: list = []
    cagrilar_b: list = []

    def _al(d: str) -> set:
        if d not in onbellek:
            onbellek[d] = pit_as_of(degisiklikler, guncel_set, d)
        return onbellek[d]

    def a_fn(d: str) -> set:
        cagrilar_a.append(d)
        return set(_al(d))

    def b_fn(d: str) -> set:
        cagrilar_b.append(d)
        return set(_al(d)) | hic_uye_set

    return {"TABAN": None, "A": a_fn, "B": b_fn, "_onbellek": onbellek,
            "_cagrilar_a": cagrilar_a, "_cagrilar_b": cagrilar_b, "_hic_uye_set": hic_uye_set}


# ======================================================================================
# KOŞUM — betimleyici istatistik (replay, TAM pencere) + kapı hükümleri (walk_forward, CANLI fold)
# ======================================================================================

def koşum_calistir(uyelik_fn, params: dict, bars: dict, index_bars, goal: dict,
                   baslangic: str, bitis: str, strategy_version: int) -> dict:
    """Betimleyici istatistikler: `backtest.replay` TAM `[baslangic, bitis]` penceresinde.
    `trades` çıktı sözlüğüne DAHİLDİR (sızıntı kontrolü + sonraki kıyaslar için) — `ana()` bunu
    `sonuc.json`a yazmadan ÖNCE ÇIKARIR (Yasa 6 istisnası değil — büyük bir ara veri, kalıcı
    kanıt gövdesi K1/K1_tohum defterinde zaten EDG-079'da var; burada yalnız SAYI+ÖZET kalır)."""
    t0 = time.perf_counter()
    res = backtest.replay(params, bars, index_bars, goal, baslangic, bitis,
                          strategy_version=strategy_version, uyelik=uyelik_fn)
    sure = time.perf_counter() - t0
    trades = res.trades
    n = len(trades)
    r_degerler = [float(t["r_multiple"]) for t in trades if t.get("r_multiple") is not None]
    avg_r = round(sum(r_degerler) / len(r_degerler), 4) if r_degerler else None
    medyan_r = round(statistics.median(r_degerler), 4) if r_degerler else None
    kazanan = sum(1 for r in r_degerler if r > 0)
    kazanma_orani = round(kazanan / len(r_degerler), 4) if r_degerler else None
    return {"n_islem": n, "avg_r": avg_r, "medyan_r": medyan_r, "kazanma_orani": kazanma_orani,
            "olculemedi_r_n": n - len(r_degerler), "sure_replay_s": round(sure, 3), "trades": trades}


def kapi_hukumleri(uyelik_fn, params: dict, bars: dict, index_bars, goal: dict,
                   strategy_version: int) -> dict:
    """Kapı hükümleri: `backtest.walk_forward` CANLI fold tanımıyla (`dataset.IS_START/OOS_START/
    OOS_END/HOLDOUT_END/OOS_FOLDS/EMBARGO_DAYS` — `reflect._default_windows`in okuduğu AYNI
    sabitler). DSR/PBO YAPISAL OLARAK None (modül başlığı — validation_ledger bu izole ölçümde
    yok, `n_trials` uydurulamaz): `dsr_kapi(None, ...)`/`pbo_kapi(pbo_cscv(rows=[]), ...)` GERÇEK
    fonksiyonlar ÇAĞRILIR (şekilleri uydurulmaz), girdi None/boş olduğu İÇİN "olculemedi" döner."""
    t0 = time.perf_counter()
    wf = backtest.walk_forward(params, bars, index_bars, goal,
                               dataset_mod.IS_START, dataset_mod.OOS_START, dataset_mod.OOS_END,
                               dataset_mod.HOLDOUT_END, strategy_version=strategy_version,
                               oos_folds=dataset_mod.OOS_FOLDS, embargo_days=dataset_mod.EMBARGO_DAYS,
                               uyelik=uyelik_fn)
    sure = time.perf_counter() - t0
    oos_score = wf.get("oos_score")
    oos_durum = "olculdu" if oos_score is not None else "olculemedi"
    pbo_olcum = validation.pbo_cscv(rows=[])           # validation_ledger'a HİÇ dokunmaz (boş liste)
    dsr_kapi = validation.dsr_kapi(None, live=False)
    pbo_kapi = validation.pbo_kapi(pbo_olcum, live=False)
    return {"oos_score": oos_score, "oos_durum": oos_durum,
            "n_trades_graded": wf.get("n_trades_graded"), "n_trades_total": wf.get("n_trades_total"),
            "sure_walk_forward_s": round(sure, 3),
            "dsr_kapi": dsr_kapi,
            "dsr_neden": ("DSR yapısal olarak None: n_trials bu izole K=2 kıyasında ARAMA-tanımlı "
                          "bir sayı değil (reflect._gate_eval aşınma-defteri+k_probes toplamının "
                          "bir kopyası olmadan uydurulamaz) — dsr_kapi(None,...) GERÇEK 'olculemedi' şekli"),
            "pbo_kapi": pbo_kapi,
            "pbo_neden": (f"PBO yapısal olarak olculemedi: validation_ledger.jsonl bu izole ölçümde "
                          f"okunmaz/yazılmaz, pbo_cscv(rows=[]) → {pbo_olcum.get('neden')}")}


# ======================================================================================
# SIZINTI KONTROLÜ — EDG-079'un 95 çifti TABAN/A/B'de
# ======================================================================================

def islem_ciftleri(trades: list) -> set:
    return {(str(t.get("ticker", "")).upper(), str(t.get("ts_open", ""))[:10]) for t in trades}


def taban_sapma_kontrolu(taban_trades: list, edg079_sonuc: dict) -> dict:
    """Kill-list #2: TABAN eski tohumla (`k1_tohum.n`) işlem SAYISINDA > %25 sapıyorsa kıyas
    çapası GEÇERSİZ — sapma açıklanır (parametre/sürüm farkı), PIT etkisiyle KARIŞTIRILMAZ."""
    n_eski = (edg079_sonuc.get("k1_tohum") or {}).get("n")
    if n_eski is None:
        return {"calisti": False, "neden": "edg079 sonucunda k1_tohum.n yok — sapma ÖLÇÜLEMEDİ"}
    n_yeni = len(taban_trades)
    oran = (abs(n_yeni - n_eski) / n_eski) if n_eski else None
    kill = bool(oran is not None and oran > 0.25)
    return {"calisti": True, "n_eski_tohum": n_eski, "n_taban": n_yeni,
            "sapma_orani": round(oran, 4) if oran is not None else None,
            "kill_tetiklendi": kill,
            "neden": ("işlem sayısı sapması muhtemelen parametre/strateji-sürümü farkından "
                      "(bkz. sonuç 'strateji_surumu' alanı) — PIT etkisiyle KARIŞTIRILMAZ, kart "
                      "kill-list #2 gereği ayrı raporlanır" if kill else None)}


def sizinti_kontrolu(taban_trades: list, a_trades: list, b_trades: list,
                     edg079_sonuc: dict, hic_uye=None) -> dict:
    """EDG-079'un 95 (ticker, ts_open) sızıntı çiftinin TABAN'ın KENDİ işlem kümesinde bulunanları
    (`eslesen`) A'da/B'de ne oldu. "Hiç-üye 39" `data.HIC_UYE_BEYANLI` (6 sembol) ÜYELİĞİYLE
    TÜRETİLİR — ayrı bir kayıt DEĞİL (tek-kaynak yasası)."""
    sizanlar = ((edg079_sonuc.get("k1_tohum") or {}).get("sizanlar")) or []
    sizan_ciftler = {(str(s["ticker"]).upper(), str(s["ts_open"])[:10]) for s in sizanlar}
    hic_uye_set = set(hic_uye) if hic_uye is not None else set(data_mod.HIC_UYE_BEYANLI)

    taban_set = islem_ciftleri(taban_trades)
    a_set = islem_ciftleri(a_trades)
    b_set = islem_ciftleri(b_trades)

    eslesen = sizan_ciftler & taban_set
    kalan_a = eslesen & a_set
    hic_uye_esen = {c for c in eslesen if c[0] in hic_uye_set}
    diger_esen = eslesen - hic_uye_esen
    kalan_b_hic_uye = hic_uye_esen & b_set
    kalan_b_diger = diger_esen & b_set

    return {
        "n_edg079_sizinti": len(sizan_ciftler),
        "n_eslesen_tabanda": len(eslesen),
        "eslesme_orani": round(len(eslesen) / len(sizan_ciftler), 4) if sizan_ciftler else None,
        "n_hic_uye_esen": len(hic_uye_esen), "n_diger_esen": len(diger_esen),
        "n_kalan_a": len(kalan_a), "kalan_a_ornek": sorted(kalan_a)[:10],
        "n_kalan_b_hic_uye": len(kalan_b_hic_uye), "n_kalan_b_diger": len(kalan_b_diger),
        "beklenen": {"kalan_a": 0, "kalan_b_hic_uye": len(hic_uye_esen), "kalan_b_diger": 0},
        "tutarli": (len(kalan_a) == 0 and len(kalan_b_hic_uye) == len(hic_uye_esen)
                   and len(kalan_b_diger) == 0),
    }


# ======================================================================================
# ADIM-0 FİZİBİLİTE — (a) tam-açık birebir, (b) tam-kapalı sıfır işlem, (c) as_of kuramama, (d) süre
# ======================================================================================

def adim0_fizibilite(taban_res, params: dict, bars: dict, index_bars, goal: dict,
                     baslangic: str, bitis: str, strategy_version: int,
                     degisiklikler: list, guncel_liste: list) -> dict:
    """(a)(b): kart pozitif_kontrolü — `uyelik=<tüm evren>` TABAN'la BİREBİR, `uyelik=<boş küme>`
    sıfır işlem verir mi. (c): `as_of` kuramama oranı endeks takviminin HER seansında. (d) süre
    kuralı `sure_kurali_uygula`da AYRI raporlanır (gerçek A/B koşumları üzerinden — burada
    SENTETİK bir üçüncü/dördüncü replay ÇALIŞTIRILMAZ, TABAN zaten hesaplanmış `taban_res`ten
    devralınır)."""
    tum_evren = set(bars.keys())
    acik = backtest.replay(params, bars, index_bars, goal, baslangic, bitis,
                           strategy_version=strategy_version, uyelik=lambda d: set(tum_evren))
    a_birebir = json.dumps(taban_res["trades"], sort_keys=True) == json.dumps(acik.trades, sort_keys=True)

    kapali = backtest.replay(params, bars, index_bars, goal, baslangic, bitis,
                             strategy_version=strategy_version, uyelik=lambda d: set())
    b_sifir = (kapali.trades == [])

    guncel_set = {s.upper() for s in guncel_liste}
    tarihler = sorted({str(x)[:10] for x in pd.to_datetime(index_bars["date"])})
    kuramama = 0
    for d in tarihler:
        try:
            pit_as_of(degisiklikler, guncel_set, d)
        except Exception:  # sessiz-yutma: bu SAYAÇ — hangi tarihin kurulamadığı c_kuramama_orani ile raporlanır, atlanmaz
            kuramama += 1
    denenen = len(tarihler)
    kuramama_orani = (kuramama / denenen) if denenen else None

    return {"a_tam_acik_birebir": a_birebir, "a_n_islem_acik": len(acik.trades),
            "a_n_islem_taban": len(taban_res["trades"]),
            "b_tam_kapali_sifir_islem": b_sifir, "b_n_islem_kapali": len(kapali.trades),
            "c_kuramama_orani": kuramama_orani, "c_kuramama_n": kuramama, "c_denenen_n": denenen,
            "gecerli": bool(a_birebir and b_sifir and
                           (kuramama_orani is None or kuramama_orani <= 0.05))}


def sure_kurali_uygula(taban_sure: float, a_sure: float, b_sure: float) -> dict:
    """Kill-list #3: A/B'nin replay süresi TABAN'ın ×2'sini AŞARSA önbellek düzeltilmeden hüküm
    yok. `sure` burada `sure_replay_s` (betimleyici replay) — `sure_walk_forward_s` AYRI raporlanır
    ama bu kapıya GİRMEZ (kart adım-0(d) metni yalnız 'replay süresi' der)."""
    a_tavan = a_sure <= 2 * taban_sure if taban_sure else None
    b_tavan = b_sure <= 2 * taban_sure if taban_sure else None
    return {"taban_sure_s": round(taban_sure, 3), "a_sure_s": round(a_sure, 3),
            "b_sure_s": round(b_sure, 3), "a_tavan_asilmadi": a_tavan, "b_tavan_asilmadi": b_tavan,
            "kill_tetiklendi": bool(a_tavan is False or b_tavan is False)}


# ======================================================================================
# KAPI HÜKÜM SINIFI KIYASI — TABAN vs A, TABAN vs B ({oos_esik, dsr, pbo}, payda n/1)
# ======================================================================================

def kapi_sinifi_kiyasla(taban_kapi: dict, aday_kapi: dict) -> dict:
    oos_ayni = taban_kapi["oos_durum"] == aday_kapi["oos_durum"]
    dsr_ayni = (taban_kapi["dsr_kapi"]["dsr_durum"] == aday_kapi["dsr_kapi"]["dsr_durum"])
    pbo_ayni = (taban_kapi["pbo_kapi"]["durum"] == aday_kapi["pbo_kapi"]["durum"])
    return {
        "oos_ayni_mi": oos_ayni, "dsr_ayni_mi_YAPISAL": dsr_ayni, "pbo_ayni_mi_YAPISAL": pbo_ayni,
        "olculebilen_kapi_sayisi": 1, "olculebilen_kapi_ayni_sayisi": int(oos_ayni),
        "hukum_sinifi_n": "1/1" if oos_ayni else "0/1",
        "beyan": ("payda n/3 DEĞİL n/1: DSR ve PBO bu ölçümde HER İKİ koşumda da yapısal olarak "
                  "'olculemedi' (None) — bu ikisinin 'aynı' çıkması ölçülmüş bir denklik değil "
                  "yapısal bir sabit, kapı hüküm sınıfı sayımına KATILMAZ (kart notu + brief keşfi)"),
    }


# ======================================================================================
# ANA (--olc) — argparse
# ======================================================================================

def _delta(taban_ozet: dict, aday_ozet: dict, anahtar: str):
    a, b = taban_ozet.get(anahtar), aday_ozet.get(anahtar)
    if a is None or b is None:
        return None
    return round(b - a, 4)


def _ozet_kur(betimleyici: dict, kapi: dict) -> dict:
    ozet = {k: v for k, v in betimleyici.items() if k != "trades"}
    ozet.update(kapi)
    return ozet


def calistir(*, bars_dir, girdi_html, guncel_liste_yolu, kart_yolu=KART_YOLU,
            baslangic=VARSAYILAN_BASLANGIC, bitis=VARSAYILAN_BITIS,
            sizanlar_yolu=None, manifest_kontrol_yolu=None, yalniz=None,
            evren=None, index_symbol=None) -> dict:
    """Uçtan-uca ölçüm (CLI'nin de çağırdığı GERÇEK gövde — testler bunu doğrudan çağırabilir,
    bar/HTML/güncel-liste dosya yollarını kendi tmp fikstürleriyle vererek)."""
    evren = list(evren) if evren is not None else list(data_mod.REPLAY_UNIVERSE)
    index_symbol = index_symbol or data_mod.INDEX_SYMBOL

    yukleme = barlari_yukle(bars_dir, evren, index_symbol)
    bars, index_bars, bar_manifesti = yukleme["bars"], yukleme["index_bars"], yukleme["bar_manifesti"]

    manifest_sonuc = (manifest_kontrol(bar_manifesti, manifest_kontrol_yolu)
                      if manifest_kontrol_yolu else {"calisti": False, "neden": "--manifest-kontrol verilmedi"})

    guncel_liste = guncel_liste_oku(guncel_liste_yolu)
    degisiklikler, tablo_meta, html_sha = degisiklikleri_yukle(girdi_html)
    guncel_liste_sha = hashlib.sha256(pathlib.Path(guncel_liste_yolu).read_bytes()).hexdigest()

    strategy = config.load_strategy()
    params = strategy["params"]
    strategy_version = int(strategy.get("version", 1))
    goal = config.goal()
    params_sha = hashlib.sha256(json.dumps(params, sort_keys=True).encode("utf-8")).hexdigest()

    fonksiyonlar = uyelik_fonksiyonlarini_kur(degisiklikler, guncel_liste)

    if manifest_sonuc.get("calisti") and not manifest_sonuc.get("gecerli"):
        # KILL (kart §5): manifest değiştiyse hiçbir sayı üretilmez/yayılmaz.
        return {"kart": esikleri_karttan_oku(kart_yolu), "girdi_kimligi": {
                    "bar_manifesti": bar_manifesti, "html_sha256": html_sha,
                    "guncel_liste_sha256": guncel_liste_sha, "params_sha256": params_sha,
                    "strateji_surumu": strategy_version},
                "manifest_kontrolu": manifest_sonuc,
                "gecerli": False, "neden": "bar manifestosu önceki koşumdan FARKLI — kill (kart §5)",
                "olcum_zamani": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")}

    koşumlar = ["TABAN", "A", "B"] if not yalniz else [yalniz]
    betimleyici: dict = {}
    kapi: dict = {}
    for ad in koşumlar:
        betimleyici[ad] = koşum_calistir(fonksiyonlar[ad], params, bars, index_bars, goal,
                                         baslangic, bitis, strategy_version)
        kapi[ad] = kapi_hukumleri(fonksiyonlar[ad], params, bars, index_bars, goal, strategy_version)

    adim_0 = {}
    if "TABAN" in betimleyici:
        adim_0 = adim0_fizibilite(betimleyici["TABAN"], params, bars, index_bars, goal,
                                  baslangic, bitis, strategy_version, degisiklikler, guncel_liste)
        if all(k in betimleyici for k in ("TABAN", "A", "B")):
            adim_0["sure_kurali"] = sure_kurali_uygula(
                betimleyici["TABAN"]["sure_replay_s"], betimleyici["A"]["sure_replay_s"],
                betimleyici["B"]["sure_replay_s"])

    sizinti = {"calisti": False, "neden": "--sizanlar verilmedi"}
    sapma = {"calisti": False, "neden": "--sizanlar verilmedi"}
    if sizanlar_yolu and all(k in betimleyici for k in ("TABAN", "A", "B")):
        edg079_sonuc = json.loads(pathlib.Path(sizanlar_yolu).read_text(encoding="utf-8"))
        sizinti = sizinti_kontrolu(betimleyici["TABAN"]["trades"], betimleyici["A"]["trades"],
                                   betimleyici["B"]["trades"], edg079_sonuc)
        sizinti["calisti"] = True
        sapma = taban_sapma_kontrolu(betimleyici["TABAN"]["trades"], edg079_sonuc)

    ozetler = {ad: _ozet_kur(betimleyici[ad], kapi[ad]) for ad in koşumlar}

    kiyas = {}
    if "TABAN" in ozetler:
        for ad in ("A", "B"):
            if ad in ozetler:
                kiyas[ad] = {
                    "delta_n_islem": ozetler[ad]["n_islem"] - ozetler["TABAN"]["n_islem"],
                    "delta_avg_r": _delta(ozetler["TABAN"], ozetler[ad], "avg_r"),
                    "delta_medyan_r": _delta(ozetler["TABAN"], ozetler[ad], "medyan_r"),
                    "delta_kazanma_orani": _delta(ozetler["TABAN"], ozetler[ad], "kazanma_orani"),
                    "delta_oos_score": _delta(ozetler["TABAN"], ozetler[ad], "oos_score"),
                    "kapi_sinifi": kapi_sinifi_kiyasla(kapi["TABAN"], kapi[ad]),
                }

    sonuc = {
        "kart": esikleri_karttan_oku(kart_yolu),
        "girdi_kimligi": {
            "bar_manifesti": bar_manifesti, "bar_eksik": yukleme["eksik"],
            "html_sha256": html_sha, "html_yolu": str(girdi_html),
            "guncel_liste_sha256": guncel_liste_sha, "guncel_liste_yolu": str(guncel_liste_yolu),
            "params_sha256": params_sha, "strateji_surumu": strategy_version,
            "tablo_meta": tablo_meta,
        },
        "manifest_kontrolu": manifest_sonuc,
        "adim_0": adim_0,
        "taban": ozetler.get("TABAN"), "a": ozetler.get("A"), "b": ozetler.get("B"),
        "kiyas": kiyas,
        "sizinti_kontrolu": sizinti,
        "taban_sapma_kontrolu": sapma,
        "pozitif_kontrol": {"adim_0_a_b": adim_0, "not": "kart pozitif_kontrol maddesi adim_0(a)/(b) İLE AYNI çivi"},
        "esikler": esikleri_karttan_oku(kart_yolu),
        "gecerli": True,
        "beyan": ("obs'a ulaşan sanitize_bars/measurement_bars ÇAĞRILMADI — bkz. girdi_kimligi."
                  "tablo_meta ve her bar kaydının 'atlanan_temizlik_adimlari' alanı; DSR/PBO "
                  "yapısal None (bkz. kapi_hukumleri.dsr_neden/pbo_neden); validation_ledger.jsonl "
                  "bu ölçümde HİÇ okunmadı/yazılmadı"),
        "olcum_zamani": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
    }
    return sonuc


def ana(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--olc", action="store_true", required=True)
    ap.add_argument("--bars-dir", required=True)
    ap.add_argument("--girdi-html", required=True)
    ap.add_argument("--guncel-liste", required=True)
    ap.add_argument("--kart", default=str(KART_YOLU))
    ap.add_argument("--baslangic", default=VARSAYILAN_BASLANGIC)
    ap.add_argument("--bitis", default=VARSAYILAN_BITIS)
    ap.add_argument("--cikti", default=str(SANDBOX / "sonuc.json"))
    ap.add_argument("--yalniz", choices=("TABAN", "A", "B"), default=None)
    ap.add_argument("--sizanlar", default=None)
    ap.add_argument("--manifest-kontrol", default=None)
    # `--evren`/`--index-symbol`: VARSAYILAN None = ÜRETİM davranışı (REPLAY_UNIVERSE + SPY,
    # `calistir()`in kendi varsayılanı) BİREBİR korunur. Yalnız test/hata-ayıklama kaçış kapısı —
    # küçük sentetik evrenle "GERÇEK çağrı biçimi"ni (edg075 emsali, madde (j)) küçük ölçekte
    # sınamak için (248 sembollük gerçek evren birim testinde pratik değil).
    ap.add_argument("--evren", default=None,
                    help="virgülle ayrılmış sembol listesi (varsayılan: data.REPLAY_UNIVERSE)")
    ap.add_argument("--index-symbol", default=None,
                    help="endeks sembolü (varsayılan: data.INDEX_SYMBOL — 'SPY')")
    ns = ap.parse_args(argv)

    evren = [s.strip() for s in ns.evren.split(",") if s.strip()] if ns.evren else None
    sonuc = calistir(bars_dir=ns.bars_dir, girdi_html=ns.girdi_html,
                     guncel_liste_yolu=ns.guncel_liste, kart_yolu=pathlib.Path(ns.kart),
                     baslangic=ns.baslangic, bitis=ns.bitis, sizanlar_yolu=ns.sizanlar,
                     manifest_kontrol_yolu=ns.manifest_kontrol, yalniz=ns.yalniz,
                     evren=evren, index_symbol=ns.index_symbol)

    cikti_yolu = pathlib.Path(ns.cikti)
    cikti_yolu.parent.mkdir(parents=True, exist_ok=True)
    cikti_yolu.write_text(json.dumps(sonuc, indent=2, sort_keys=True, ensure_ascii=False, default=str),
                          encoding="utf-8")
    print(f"yazildi: {cikti_yolu}")
    return 0 if sonuc.get("gecerli") else 1


if __name__ == "__main__":
    raise SystemExit(ana())
