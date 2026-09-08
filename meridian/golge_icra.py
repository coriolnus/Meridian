"""golge_icra.py — uyuyan (dormant) kurulum planlarının GÖLGE İCRA defteri + motoru. GERÇEK EMİR YOK.

NE YAPAR. `loop.daily_cycle`in ürettiği planlardan uyuyan olanlar bugün hiçbir icra yoluna
girmiyor: doğuyorlar, kapı hükmü alıyorlar ve orada kalıyorlar (31 plan / 0 işlem — "önden bağlı,
arkadan bağsız"). EDG-2026-049 aynı soruyu geçmişe dönük karşı-olguyla sordu ve NO-GO verdi, ama
n=6 idi. Bu modül ileriye dönük ve sermaye riski OLMAYAN bir örneklem üretir: plan doğduğu seansta
yakalanır, ertesi seansın AÇILIŞINDA gölge girişi denenir, ömrü boyunca CANLI çıkış yasalarıyla
yönetilir ve kapandığında tek bir R satırı yazılır. Canlı davranış DEĞİŞMEZ, canlı defterlere
DOKUNULMAZ.

KİLİT GİRİŞLER. `adim` (bir seans; tek çağıranı `loop.daily_cycle`in gölge bloğu olacaktır) ·
`ozet` (pano/api okuyucusunun tükettiği özet) · `kayit_al` / `acik_kayit` (ham defter okuyucuları) ·
`bar_hash` (PIT çapası).

YASALAR — GÖLGE KATMANI.
  SIFIR EMİR YETKİSİ. Bu modül hiçbir emir/onay/silahlanma yüzeyine ULAŞMAZ: ne `adapters.alpaca`,
  ne `loop`, ne `arming` ithal edilir; canlı `portfolio.json` / `trades.jsonl` /
  `trade_plans.jsonl` / `approvals.jsonl` adlarına tek bir yazma çağrısı yoktur. Yazdığı iki dosya
  `DEFTER` ve `ACIK`tır, başka hiçbir şey. (Kart kill#1, SIFIR TOLERANS.)
  ÜRETİME DOKUNULMAZ. Uyuyan planların DOĞUMU (`arming`, `strategy.scan_all`, `guard.classify_gate`,
  `loop.girise_uygun`) bu modülün konusu değildir; motor kendisine VERİLEN planları izler, hiçbirini
  üretmez ve hiçbirini kapı hükmüne göre ELEMEZ — kart "dormant planların TAMAMI gölgeye girer"
  der, hüküm (`hukum`) yalnız tanı olarak satıra damgalanır. (Kill#2.)
  YASALAR ÇAĞRILIR, KOPYALANMAZ. Çıkış kararı `strategy.manage_position`, dokunuş çıkışı
  `broker.PaperBroker._touch_exit`, giriş limiti `broker.entry_limit_price` /
  `broker.entry_law`tır. `exit.*` düğmelerinin hiçbiri bu dosyada ADIYLA geçmez: `params` sözlüğü
  olduğu gibi üretim fonksiyonuna verilir. İkinci bir eşik yorumu ilk düzeltmede çatallanırdı.
  MOTOR BİR KAPI YÜZEYİ DEĞİLDİR. Hiçbir fonksiyon kapı vokabülerinden bir karar sabiti DÖNDÜRMEZ;
  plandaki `gate_verdict` tüketilir. Bu yüzden `pitlaw` kapı sözleşmesi kaydına girmez.
  UYDURMA YASAĞI. Ölçülemeyen her değer `None` + ADLI neden: bar yoksa `kaynak_bar_hash=None` ve
  `olculemedi`; giriş hiç olmadıysa `R=None` (0 DEĞİL) ve `giris_reddi`. Bu satırlar `ozet`in K
  paydasına GİRMEZ.

BEYANLI KAPSAM SAPMALARI (ölçüldü — sessiz değil, yazılı).
  (1) DEFTER PLAN DÜZEYİNDEDİR, PORTFÖY DÜZEYİNDE DEĞİL. Boyutlandırma, sermaye, slot tavanı,
      de-risk çarpanı ve devre kesici KOŞMAZ; ölçülen büyüklük R'dir ("bu planlar R kazandırır
      mıydı"), sermaye eğrisi değil. Uyuyan planlar zaten hiçbir slot için yarışmadı; portföy yolu
      eklemek ölçülen soruyu değiştirirdi. Sürtünme (kayma/komisyon) bu yüzden fiyata İŞLENMEZ —
      kartın kontrol PK'sı gölge ile gerçek arasındaki farkı tam olarak "komisyon+kayma payı"
      toleransıyla sınar (`FARK_R_UST`).
  (2) `scale_out` ÇAĞRILMAZ. Canlı çıkış yolu üçlüdür (`manage_position` + `_touch_exit` +
      `PaperBroker.scale_out`) ve Rol-1 hükmü şuydu: üçüncüsü ancak broker DURUMUNDAN bağımsız
      çağrılabiliyorsa girer. ÖLÇÜLDÜ (AST, `self` erişimleri): `_touch_exit` hiç `self`
      kullanmıyor → durumdan bağımsız, ÇAĞRILIYOR; `scale_out` `self.cash` / `self.realized_pnl` /
      `self.slip` / `self.commission` kullanıyor → bir kitap ister, ÇAĞRILMIYOR. Sapmanın bugünkü
      etkisi ölçülmüştür: canlı `exit.scale_out_frac` varsayılanı 0'dır ve kısmi satış canlıda
      hiç ateşlememiştir; düğme açılırsa gölge ile canlı AYRIŞIR ve kontrol PK'sı bunu düşürerek
      gösterir — dürüstçe düşer. Çivi: bu iki saflık ölçümü teste çakılıdır.
  (3) GİRİŞ TETİĞİ SINANIR. Üretimin `PaperBroker.fill_entry`i tetik testi YAPMAZ (silahlı planı
      ertesi açılışta koşulsuz doldurur); burada "İLK UYGUN BAR" tanımı tetiği ister, bu yüzden
      barın en yükseği tetiğe ulaşmadıysa giriş olmaz. Sapma TEK YÖNLÜDÜR ve muhafazakârdır:
      üretimden DAHA AZ giriş üretir, gölgeyi iyimser göstermez.
  (4) PİVOT YOKTUR. İcra girdileri (`atr`, `pivot`) plan sözlüğünde değil `meta["entry_law"]` yan
      tablosundadır ve o tablo yalnız silahlı+REVIEW planlar için tutulur — uyuyan planda YOKTUR.
      `pivot=0.0` üretimin "bilinmiyor" değeridir ve erken itlaf dalı dürüstçe ateşlemez; `atr=None`
      ile giriş limiti yalnız yüzde tavanıyla kurulur (uydurma ATR yok).

OKUR: çağıranın geçirdiği barlar/rejim/etkin düğmeler + kendi iki dosyası.
YAZAR: yalnız `DEFTER` (kapanan gölge satırları) ve `ACIK` (açık gölge pozisyonlar + `son_seans`).
DIŞ OKUYUCU (Yasa 6): `meridian/api.py` → `ozet()` (bu planın ikinci görevinde bağlanır).
"""
from __future__ import annotations

import hashlib

import pandas as pd

from . import barclock, broker as brk, store, strategy

# ---- KART SABİTLERİ (EDG-2026-088; ölçümden ÖNCE donduruldu, kod bunları değiştiremez) ---------
# Eşikler kartın `esikler` bloğundan gelir ve env/parametre ile GEVŞETİLEMEZ (emsal: `faz5_cikis`in
# kart sabitleri bloğu). PENCERE_GUN kartın `pencere_gun_ust` alanıdır: 088 selefi 087'nin 45 gününü
# ARDIL kart olarak 120'ye taşıdı (öncül bayat hıza dayanıyordu; ölçülen hız ~1,7 plan/hafta →
# n≥30 için ~18 hafta). Sayı kartla AYNI olmak zorundadır — çivi ikisini karşılaştırır.
KART = "EDG-2026-088"
N_ALT = 30                  # asgari KAPANAN gölge işlem; altında hüküm YAZILMAZ
CI_ALT_R = 0.0              # blok-bootstrap CI95 alt sınırı bunun ÜSTÜNDE olmalı (sayım betiği ölçer)
KAZANMA_ALT = 0.40
PENCERE_GUN = 120
FARK_R_UST = 0.05           # kontrol PK'sı: |gölge R − gerçek R| ortalaması bu payın içinde

DEFTER = "golge_icra.jsonl"        # kapanan gölge işlemler (satır başına bir plan)
ACIK = "golge_icra_acik.json"      # açık gölge pozisyonlar + bekleyen girişler + `son_seans`

SEMA = 1
KOLLAR = ("dormant", "kontrol")            # `kol` alanının kapalı kümesi
BAR_KAYNAKLARI = ("state/bars", "arsiv")   # PIT çapasının kaynağı (canlı yol | tarihsel yeniden yürütme)

#: DEFTER SATIRININ TAM ALAN KÜMESİ — şema burada TEK YERDE yazılıdır ve her satır alanların
#: HEPSİNİ taşır (ölçülemeyen alan `None`, "yok" DEĞİL): eksik anahtar, okuyucunun `get`
#: varsayılanıyla sessizce dolar ve "yazılmadı" ile "ölçülemedi" ayrımı kaybolurdu.
SATIR_ALANLARI: tuple[str, ...] = (
    "ts", "plan_id", "ticker", "kurulum", "hukum", "kol", "ts_plan",
    "giris_ts", "giris_fiyat", "stop", "hedef",
    "cikis_ts", "cikis_fiyat", "cikis_neden", "R", "bar_n",
    "kaynak_bar_hash", "bar_kaynak", "strategy_version",
    "giris_reddi", "olculemedi",
)

#: GİRİŞİN OLMAMA NEDENLERİ — kapalı küme. `cikis_neden` bu satırlarda daima `GIRIS_YOK`tur
#: (sınıf), `giris_reddi` ise ADIDIR (tanı). İkisini tek alana sıkıştırmak, çıkış sebebi
#: dağılımını (sayım betiğinin ham maddesi) giriş redleriyle karıştırırdı.
GIRIS_YOK = "giris_yok"
GIRIS_REDLERI = ("tetik_gelmedi", "limit_asildi", "acilis_stop_altinda", "bar_yok")

#: İşlenmiş plan kimliklerinin BEYANLI tavanı. Aynı planın iki kez gölgeye girmesini engelleyen
#: küme süresiz büyüseydi `ACIK` dosyası tek yönlü şişerdi; tavan aşıldığında en ESKİ kimlikler
#: düşer ve o planlar (defterde zaten satırı olduğu için) yalnız teorik olarak yeniden girebilir.
ISLENEN_TAVANI = 2000


def _bos_belge(simdi=None) -> dict:
    """Boş gölge belgesi: şema, kart kimliği, kuruluş anı ve üç boş kova."""
    return {"schema": SEMA, "kart": KART, "kurulus": _ts(simdi), "son_seans": None,
            "bekleyen_giris": {}, "acik": {}, "islenen": []}


def _ts(simdi=None) -> str:
    """GERÇEK yazım anı (tz-aware ISO). Seans tarihi AYRI alandır — retro-damga yasağı."""
    return (simdi or barclock.now()).isoformat()


# ==================================================================================================
# PIT ÇAPASI
# ==================================================================================================
def bar_hash(kesitler) -> str | None:
    """TÜKETİLEN barların içeriğinden türeyen sha256 — ya da ölçülemediyse `None`.

    Kesit = `(ticker, tarih, open, high, low, close, volume)`. Hash YALNIZ bu planın gerçekten
    OKUDUĞU barlardan türer: tüketilmeyen bir sembolün ya da tüketilmeyen bir günün barı hash'i
    DEĞİŞTİRMEZ, tek bir OHLCV hanesi değişirse DEĞİŞİR. Herhangi bir kesit ya da hane eksikse
    dönüş `None`'dır (kısmi bir çapa, çapa değildir) ve satır K paydasına girmez.

    NEDEN İÇERİK: bugünkü belirlenimcilik raporu bar dosyalarının yalnız BOYUTUNU tutuyor; boyut
    aynı kalarak değişen bir hane PIT çapasını sessizce çürütürdü.
    """
    ozet = hashlib.sha256()
    n = 0
    for k in kesitler or ():
        if not isinstance(k, (list, tuple)) or len(k) != 7:
            return None
        tk, tarih = k[0], k[1]
        if not isinstance(tk, str) or not isinstance(tarih, str):
            return None
        sayilar = []
        for x in k[2:]:
            if isinstance(x, bool) or not isinstance(x, (int, float)):
                return None
            sayilar.append(repr(float(x)))
        ozet.update(("|".join([tk, tarih, *sayilar]) + "\n").encode("utf-8"))
        n += 1
    return ozet.hexdigest() if n else None


def _kesit_ekle(poz: dict, kesit) -> None:
    """Kesiti TÜKETİLENLERE ekler — AYNI SEANS İKİ KEZ SAYILMAZ.

    Bir plan girdiği seansta iki fazdan geçer (OPEN'da dolum, INTRADAY'de dokunuş kontrolü) ve
    ikisi de aynı barı okur. Kesiti iki kez yazmak `bar_n`i şişirir ve PIT çapasını "aynı barı iki
    kez tükettim" diye damgalardı; hash'in anlamı TÜKETİLEN BAR KÜMESİdir, okuma sayısı değil.
    """
    kesitler = poz.setdefault("tuketilen", [])
    if kesitler and kesitler[-1] and kesit and kesitler[-1][1] == kesit[1]:
        return
    kesitler.append(kesit)


def _bar_kesiti(df, d: pd.Timestamp, ticker: str):
    """`(bar sözlüğü, hash kesiti)` — bar yoksa `(None, None)`. Bar UYDURULMAZ.

    Hacim sütunu yoksa kesitin sayısal hanesi eksiktir ve `bar_hash` `None` döner: PIT çapası
    yarım tutulmaz.
    """
    if df is None or d not in df.index:
        return None, None
    r = df.loc[d]
    bar = {"open": float(r["open"]), "high": float(r["high"]),
           "low": float(r["low"]), "close": float(r["close"])}
    hacim = float(r["volume"]) if "volume" in r.index else None
    kesit = [str(ticker), str(d.date()), bar["open"], bar["high"], bar["low"], bar["close"], hacim]
    return bar, kesit


# ==================================================================================================
# DEFTER OKUYUCULARI
# ==================================================================================================
def kayit_al(n: int | None = None) -> list[dict]:
    """Kapanan gölge satırları (`n` verilirse SON `n` satır)."""
    return store.read_jsonl(DEFTER, limit=n)


def acik_kayit() -> dict:
    """Açık gölge belgesi — yoksa boş belge (dosyaya YAZILMADAN)."""
    doc = store.read_json(ACIK, None)
    return doc if isinstance(doc, dict) and doc.get("schema") == SEMA else _bos_belge()


# ==================================================================================================
# BİR SEANS — faz sırası `shadow_lifecycle.step`ten alınmıştır (kaynak ADIYLA yazılıdır)
# ==================================================================================================
def adim(dstr: str, *, planlar: list[dict], bars_of, regime_ok: bool, params: dict,
         simdi=None, bar_kaynak: str = "state/bars") -> dict:
    """Bir seansın gölge adımı. Dönüş: o adımın SAYIM özeti (satır değil).

    FAZ SIRASI — `shadow_lifecycle.step`in olay düzeninin aynısıdır ve o düzen de kendi kaynağını
    (`backtest.replay`in olay sırası) adıyla yazar. Sıra bir "yasa" değil bir OLAY DÜZENİDİR ve
    ileri-dönüklüğü olmayan tek düzendir; onu çağırmanın yolu yok (iki motor da kendi takvimini
    kurar), o yüzden burada da tek yardımcıya çıkarıldı:
      1) OPEN(D)     — bir önceki kapanışta verilmiş çıkış kararları bu açılışta icra edilir,
                       sonra bekleyen girişler bu açılışta denenir.
      2) INTRADAY(D) — `broker.PaperBroker._touch_exit` (sert stop / hedef / boşluk) bar içinde.
      3) CLOSE(D)    — `strategy.manage_position` KAPALI bara bakar; kararı ERTESİ açılışa yazar.
    D'nin KAPANIŞI girişte KULLANILMAZ: plan D kapanışında doğar, girişi D+1 açılışındadır.

    GİRİŞ TEK ATIMLIKTIR. Üretimde silahlı küme her seans sıfırlanır ("bar-yok = tatil/delisting,
    plan gerçekten dolmaz"); burada da bekleyen giriş bir sonraki seansta ya dolar ya ADIYLA
    (`giris_reddi`) düşer — süresiz bekleyen bir plan, tetiği aylar sonra gelen bir girişi bugünün
    planı gibi sayardı.

    İDEMPOTENT: `dstr` en son işlenen seanstan yeni değilse hiçbir satır yazılmaz, `son_seans`
    değişmez ve dönüşte `atlandi` alanı doludur.

    KOL KAPSAMI ÇAĞIRANINDIR: motor kendisine verilen her planı izler ve `dormant_setup`
    damgasından `kol` türetir; hangi planların geçirileceği (kart: uyuyan planların TAMAMI + kontrol
    kolunda yalnız gerçek işlemler) çağıranın kararıdır.
    """
    doc = acik_kayit()
    son = doc.get("son_seans")
    if son is not None and str(dstr) <= str(son):
        return {"seans": str(dstr), "atlandi": "islenmis_seans", "son_seans": son,
                "yeni_satir": 0, "acik": len(doc.get("acik") or {}),
                "bekleyen_giris": len(doc.get("bekleyen_giris") or {})}

    d = pd.Timestamp(dstr)
    acik: dict = dict(doc.get("acik") or {})
    bekleyen: dict = dict(doc.get("bekleyen_giris") or {})
    islenen: list = list(doc.get("islenen") or [])
    satirlar: list[dict] = []

    # ---- 1a. OPEN(D): bir önceki kapanışın çıkış kararları ----------------------------------
    # Karar TEK ATIMLIKTIR (üretimde `pending_exits` her seans boşaltılır): barı olmayan bir gün
    # kararı düşürür ve kapanışta yeniden sorulur.
    for pid in list(acik):
        poz = acik[pid]
        neden = poz.get("bekleyen_cikis")
        poz["bekleyen_cikis"] = None
        if not neden:
            continue
        bar, kesit = _bar_kesiti(bars_of(poz["ticker"]), d, poz["ticker"])
        if bar is None:
            poz["eksik_bar"] = int(poz.get("eksik_bar") or 0) + 1
            continue
        _kesit_ekle(poz, kesit)
        satirlar.append(_kapanis_satiri(poz, dstr, bar["open"], str(neden), simdi, bar_kaynak))
        acik.pop(pid, None)

    # ---- 1b. OPEN(D): bekleyen girişler -------------------------------------------------------
    for pid, kayit in sorted(bekleyen.items()):
        satir, poz = _girisi_dene(kayit, d, dstr, bars_of, simdi, bar_kaynak)
        if satir is not None:
            satirlar.append(satir)
        if poz is not None:
            acik[pid] = poz
    bekleyen = {}

    # ---- 2. INTRADAY(D): dokunuş çıkışları ----------------------------------------------------
    # `_touch_exit` broker DURUMUNDAN bağımsızdır (ölçüldü: gövdesinde hiç `self` yok), bu yüzden
    # bir kitap kurmadan, üretimin KENDİ fonksiyonu ve KENDİ `Position` sınıfıyla çağrılır.
    # `scale_out` çağrılmaz — gerekçe ve ölçüm modül başlığındaki beyanlı sapma (2).
    for pid in list(acik):
        poz = acik[pid]
        bar, kesit = _bar_kesiti(bars_of(poz["ticker"]), d, poz["ticker"])
        if bar is None:
            poz["eksik_bar"] = int(poz.get("eksik_bar") or 0) + 1
            continue
        _kesit_ekle(poz, kesit)
        p = _pozisyon_nesnesi(poz)
        ex = brk.PaperBroker._touch_exit(None, p, bar)
        poz["hi_water"], poz["lo_water"] = p.hi_water, p.lo_water
        poz["pre_scale_stop"] = p.pre_scale_stop
        if ex:
            satirlar.append(_kapanis_satiri(poz, dstr, ex[0], ex[1], simdi, bar_kaynak))
            acik.pop(pid, None)
        else:
            poz["bars_held"] = int(poz.get("bars_held") or 0) + 1

    # ---- 3. CLOSE(D): yönetim kararı (icrası ERTESİ açılışta) ---------------------------------
    for pid in list(acik):
        poz = acik[pid]
        df = bars_of(poz["ticker"])
        if df is None or d not in df.index:
            continue
        dec = strategy.manage_position(
            df.loc[:d].reset_index(),
            {"entry": poz["giris_fiyat"], "stop": poz["stop"], "trail_stop": poz["trail_stop"],
             "r_per_share": poz["r_per_share"], "pivot": poz["pivot"]},
            params, int(poz.get("bars_held") or 0), regime_ok)
        poz["trail_stop"] = dec.trail_stop
        if dec.exit_now:
            poz["bekleyen_cikis"] = dec.exit_reason

    # ---- 3b. CLOSE(D): bu seansın planları yakalanır (girişi D+1 açılışında) -------------------
    yeni = 0
    for plan in planlar or []:
        pid = str(plan.get("id") or "")
        if not pid or pid in acik or pid in bekleyen or pid in islenen:
            continue
        bekleyen[pid] = _bekleyen_kayit(plan, dstr)
        islenen.append(pid)
        yeni += 1
    if len(islenen) > ISLENEN_TAVANI:
        islenen = islenen[-ISLENEN_TAVANI:]

    # ---- defter ----
    # DÜZ SÖZLÜK KURULUR, OKUNAN NESNE MUTASYONA UĞRATILMAZ: `store.read_json` köken takibi açıkken
    # okuduğunu bir sarmalayıcıya koyar; onu yerinde değiştirip geri yazmak, yazım yolunu okuma
    # katmanının açık/kapalı olmasına bağlardı.
    store.write_json(ACIK, {"schema": SEMA, "kart": KART,
                            "kurulus": doc.get("kurulus") or _ts(simdi),
                            "son_seans": str(dstr), "bekleyen_giris": bekleyen,
                            "acik": acik, "islenen": islenen})
    for satir in satirlar:
        store.append_jsonl(DEFTER, satir)
    return {"seans": str(dstr), "atlandi": None, "son_seans": str(dstr),
            "yeni_satir": len(satirlar), "yeni_plan": yeni,
            "acik": len(acik), "bekleyen_giris": len(bekleyen)}


def _bekleyen_kayit(plan: dict, dstr: str) -> dict:
    """Plandan gölge takibinin ihtiyaç duyduğu ALANLAR — plan sözlüğü OLDUĞU GİBİ saklanmaz.

    Defter süresiz büyümesin ve gölge, planın icra dışı alanlarına (onay/ret/skill zinciri) bağlı
    hâle gelmesin diye kopya DAR tutulur. `dormant_setup` damgası `kol`a çevrilir: kolun adı
    satırda ADIYLA durur, okuyucu plan defterine geri dönmek zorunda kalmaz.
    """
    hedefler = plan.get("targets") or []
    return {"plan_id": str(plan.get("id") or ""), "ticker": str(plan.get("ticker") or ""),
            "kurulum": str(plan.get("setup") or "?"),
            "hukum": (str(plan["gate_verdict"]) if plan.get("gate_verdict") else None),
            "kol": KOLLAR[0] if plan.get("dormant_setup") else KOLLAR[1],
            "ts_plan": str(plan.get("date") or dstr),
            "tetik": float(plan.get("entry_trigger") or 0.0),
            "stop": float(plan.get("stop") or 0.0),
            "hedef": float(plan.get("profit_target") or (hedefler[0] if hedefler else 0.0) or 0.0),
            "strategy_version": plan.get("strategy_version")}


def _girisi_dene(kayit: dict, d: pd.Timestamp, dstr: str, bars_of, simdi, bar_kaynak):
    """`(defter satırı | None, açık pozisyon | None)` — girişin TEK ATIMI.

    Üretimin giriş yasası ÇAĞRILIR (`broker.entry_limit_price` / `broker.entry_law`), yeniden
    yazılmaz. `atr=None` çünkü icra girdileri uyuyan planın yan tablosunda YOKTUR; limit o zaman
    yalnız yüzde tavanıyla bağlar ve bu üretimin kendi davranışıdır.
    """
    bar, kesit = _bar_kesiti(bars_of(kayit["ticker"]), d, kayit["ticker"])
    if bar is None:
        return _giris_yok_satiri(kayit, dstr, "bar_yok", [], simdi, bar_kaynak,
                                 olculemedi="bar_yok"), None
    tetik, stop = float(kayit["tetik"]), float(kayit["stop"])
    if tetik > 0 and bar["high"] < tetik:
        return _giris_yok_satiri(kayit, dstr, "tetik_gelmedi", [kesit], simdi, bar_kaynak), None
    acilis = bar["open"]
    if tetik > 0 and acilis > brk.entry_limit_price(tetik, None):
        return _giris_yok_satiri(kayit, dstr, "limit_asildi", [kesit], simdi, bar_kaynak), None
    if acilis <= stop:
        return _giris_yok_satiri(kayit, dstr, "acilis_stop_altinda", [kesit], simdi,
                                 bar_kaynak), None
    poz = {k: kayit[k] for k in ("plan_id", "ticker", "kurulum", "hukum", "kol", "ts_plan",
                                 "stop", "hedef", "strategy_version")}
    poz.update({"giris_ts": str(dstr), "giris_fiyat": acilis, "trail_stop": stop,
                "r_per_share": acilis - stop, "pivot": 0.0, "bars_held": 0,
                "hi_water": acilis, "lo_water": acilis, "pre_scale_stop": None,
                "bekleyen_cikis": None, "eksik_bar": 0, "tuketilen": [kesit]})
    return None, poz


def _pozisyon_nesnesi(poz: dict) -> brk.Position:
    """Gölge kaydından ÜRETİMİN `broker.Position` nesnesi — `_touch_exit`in okuduğu alanlarla.

    `qty`/`risk_dollars` NOMİNALDİR (1 hisse): bu defter portföy değil PLAN düzeyindedir ve R
    fiyatlardan türer (beyanlı sapma 1). Su işaretleri (`hi_water`/`lo_water`) taşınır çünkü
    `_touch_exit` onları yerinde günceller.
    """
    return brk.Position(
        plan_id=poz["plan_id"], ticker=poz["ticker"], side="long",
        entry=float(poz["giris_fiyat"]), stop=float(poz["stop"]),
        trail_stop=float(poz["trail_stop"]), target=float(poz["hedef"]), qty=1,
        r_per_share=float(poz["r_per_share"]), risk_dollars=float(poz["r_per_share"]),
        size_r=1.0, ts_open=str(poz["giris_ts"]), bars_held=int(poz.get("bars_held") or 0),
        hi_water=float(poz.get("hi_water") or 0.0), lo_water=float(poz.get("lo_water") or 0.0),
        pivot=float(poz.get("pivot") or 0.0),
        pre_scale_stop=(None if poz.get("pre_scale_stop") is None
                        else float(poz["pre_scale_stop"])))


def _satir(**alanlar) -> dict:
    """Şemanın TAMAMINI taşıyan defter satırı: verilmeyen her alan açıkça `None`."""
    return {ad: alanlar.get(ad) for ad in SATIR_ALANLARI}


def _giris_yok_satiri(kayit: dict, dstr: str, red: str, kesitler: list, simdi, bar_kaynak: str,
                      olculemedi: str | None = None) -> dict:
    """Girişi hiç olmayan planın satırı: `R=None` (0 DEĞİL), neden ADIYLA `giris_reddi`de."""
    return _satir(ts=_ts(simdi), plan_id=kayit["plan_id"], ticker=kayit["ticker"],
                  kurulum=kayit["kurulum"], hukum=kayit["hukum"], kol=kayit["kol"],
                  ts_plan=kayit["ts_plan"], stop=kayit["stop"], hedef=kayit["hedef"],
                  cikis_ts=str(dstr), cikis_neden=GIRIS_YOK, R=None,
                  bar_n=len(kesitler), kaynak_bar_hash=bar_hash(kesitler),
                  bar_kaynak=bar_kaynak, strategy_version=kayit["strategy_version"],
                  giris_reddi=red, olculemedi=olculemedi)


def _kapanis_satiri(poz: dict, dstr: str, cikis: float, neden: str, simdi,
                    bar_kaynak: str) -> dict:
    """Kapanan gölge işlemin satırı. R = (çıkış − giriş) / (giriş − stop).

    Eksik bar görülmüşse çapa YARIM demektir: `kaynak_bar_hash` `None` olur ve satır `ozet`in K
    paydasına GİRMEZ — R yine yazılır (ölçülen fiyatlardan türer) ama üzerine hüküm kurulmaz.
    """
    rps = float(poz["r_per_share"])
    r = round((float(cikis) - float(poz["giris_fiyat"])) / rps, 6) if rps > 0 else None
    eksik = int(poz.get("eksik_bar") or 0)
    kesitler = poz.get("tuketilen") or []
    return _satir(ts=_ts(simdi), plan_id=poz["plan_id"], ticker=poz["ticker"],
                  kurulum=poz["kurulum"], hukum=poz["hukum"], kol=poz["kol"],
                  ts_plan=poz["ts_plan"], giris_ts=poz["giris_ts"],
                  giris_fiyat=round(float(poz["giris_fiyat"]), 4), stop=float(poz["stop"]),
                  hedef=float(poz["hedef"]), cikis_ts=str(dstr),
                  cikis_fiyat=round(float(cikis), 4), cikis_neden=str(neden), R=r,
                  bar_n=len(kesitler),
                  kaynak_bar_hash=(None if eksik else bar_hash(kesitler)),
                  bar_kaynak=bar_kaynak, strategy_version=poz["strategy_version"],
                  olculemedi=(f"bar_eksik:{eksik}" if eksik else None))


# ==================================================================================================
# ÖZET — DIŞ OKUYUCUNUN (api) YÜZEYİ. HÜKÜM YOKTUR.
# ==================================================================================================
def ozet(gun: int = PENCERE_GUN) -> dict:
    """Defterin betimleyici özeti — HİÇBİR EŞİK HÜKMÜ DÖNDÜRMEZ.

    Hüküm (CI, kazanma eşiği, GEÇER/KALIR) sayım betiğinin ve Rol-1'in işidir; bir pano ucunun
    hüküm cümlesi üretmesi, eşiği kartın dışında ikinci kez yorumlamak olurdu. Burada yalnız
    sayılar, dağılımlar, pencere durumu, bedel ve ÖLÇÜLEMEYENLER vardır.

    K PAYDASI (kart hükmü 5): KAPANAN ve R'si ÖLÇÜLMÜŞ satırlar. Tetiği hiç gelmeyen plan
    (`giris_yok`, `R=None`) ve PIT çapası yarım kalan satır (`kaynak_bar_hash=None`) TANIdır,
    paydada değildir — eksik K, eşiği hak etmeden geçme yönünde yanlıdır.
    """
    satirlar = kayit_al()
    doc = acik_kayit()
    sayilan = [r for r in satirlar
               if r.get("R") is not None and r.get("kaynak_bar_hash")]
    olculemeyen = [{"plan_id": r.get("plan_id"), "kol": r.get("kol"),
                    "neden": r.get("olculemedi") or r.get("giris_reddi") or "R_yok"}
                   for r in satirlar
                   if r.get("R") is None or not r.get("kaynak_bar_hash")]
    n = len(sayilan)
    rler = [float(r["R"]) for r in sayilan]
    kazanan = [x for x in rler if x > 0]
    kaybeden = [x for x in rler if x < 0]
    baslangic = min((str(r.get("ts")) for r in satirlar if r.get("ts")), default=None)
    gecen = _gecen_gun(baslangic)
    return {
        "kart": KART,
        "n": n,
        "n_acik": len(doc.get("acik") or {}),
        "n_bekleyen_giris": len(doc.get("bekleyen_giris") or {}),
        "son_seans": doc.get("son_seans"),
        "toplam_r": round(sum(rler), 6) if n else None,
        "kazanma_orani": round(len(kazanan) / n, 4) if n else None,
        "pf": (round(sum(kazanan) / abs(sum(kaybeden)), 4) if kaybeden else None),
        "hukum_dagilimi": _dagilim(sayilan, "hukum"),
        "kurulum_kirilimi": _dagilim(sayilan, "kurulum"),
        "kol_kirilimi": _dagilim(sayilan, "kol"),
        "cikis_neden_dagilimi": _dagilim(sayilan, "cikis_neden"),
        "pencere": {"baslangic": baslangic, "gun": int(gun), "gecen_gun": gecen,
                    "doldu": bool(n >= N_ALT and gecen is not None and gecen <= int(gun)),
                    "suresi_doldu": bool(gecen is not None and gecen > int(gun))},
        "bedel": {"satir_gun": (round(len(satirlar) / gecen, 3)
                                if gecen and gecen > 0 else None),
                  "bayt": _defter_bayti(),
                  "ag_cagri": 0, "llm_cagri": 0},
        "olculemeyen": olculemeyen,
    }


def _dagilim(satirlar: list[dict], alan: str) -> dict:
    """`alan` değerine göre sayım — ölçülemeyen değer `?` kovasına düşer, sessizce KAYBOLMAZ."""
    out: dict[str, int] = {}
    for r in satirlar:
        k = str(r.get(alan) if r.get(alan) is not None else "?")
        out[k] = out.get(k, 0) + 1
    return dict(sorted(out.items()))


def _gecen_gun(baslangic: str | None) -> int | None:
    """Pencerenin açılışından bugüne geçen TAM gün — ölçülemezse `None` (0 DEĞİL)."""
    if not baslangic:
        return None
    t0 = barclock.parse_utc(baslangic)
    if t0 is None:
        return None
    return max(0, int((barclock.now() - t0).days))


def _defter_bayti() -> int | None:
    """Defterin disk bedeli (bayt). DB arka ucunda BAYT ÖLÇÜLEMEZ (damga bir revizyondur) → `None`."""
    if store.db_backed(DEFTER):
        return None
    return int(store.stamp(DEFTER)[1])
