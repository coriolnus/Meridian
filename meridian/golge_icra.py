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
  (3) GİRİŞ: İLK UYGUN BAR + STOP-AL DOLUMU. Üretimin `PaperBroker.fill_entry`i tetik testi
      YAPMAZ (silahlı planı ertesi açılışta koşulsuz doldurur); burada "İLK UYGUN BAR" tanımı
      tetiği ister — barın en yükseği tetiğe ulaşmadıysa giriş olmaz. Dolum fiyatı bir BUY-STOP
      emrinin fiyatıdır: `max(açılış, tetik)`. Açılış tetiğin altındaysa emir tetikte tetiklenir
      ve tetikten dolar; boşluklu açılışta (açılış ≥ tetik) açılıştan dolar.
      NEDEN BÖYLE (düzeltme 2026-09-12, inceleme M2-01): eski hâl kararı `high ≥ tetik` ile
      veriyor ama dolumu `open`dan yazıyordu. Açılış anında günün YÜKSEĞİ bilinmez; `open < tetik
      ≤ high` günlerinde bu, tetiğin ALTINDAN dolum yazmak (ve `high < tetik` günlerini günün
      sonucunu bilerek elemek) demekti — K1 (toplam R/CI) ve K2 (kazanma oranı) YUKARI yanlı
      olurdu. Sapma artık ADIYLA beyanlıdır ve her satırda `giris_kurali` alanında durur; yönü
      tek taraflı DEĞİL, TANIMLIDIR: üretimden daha az giriş (tetik şartı) + tetik-altı dolum
      YOK. Üretimin gap/limit/stop-altı kapıları aynen çağrılır (bkz. `_girisi_dene`).
  (4) PİVOT YOKTUR. İcra girdileri (`atr`, `pivot`) plan sözlüğünde değil `meta["entry_law"]` yan
      tablosundadır ve o tablo yalnız silahlı+REVIEW planlar için tutulur — uyuyan planda YOKTUR.
      `pivot=0.0` üretimin "bilinmiyor" değeridir ve erken itlaf dalı dürüstçe ateşlemez; `atr=None`
      ile giriş limiti yalnız yüzde tavanıyla kurulur (uydurma ATR yok).
  (5) REJİM KAPISI KÜRESELDİR. Dormant kolu KÜRESEL `regime_ok` ile ölçülür (karşı-olgu NORMAL
      icra yoludur: "bu planlar normal slotta işlem görseydi ne olurdu"); canlı KEŞİF SONDASININ
      gevşek kapısı (`loop.daily_cycle`: keşif pozisyonları için rejim adı trend_up/chop ise
      bütçe 0 olsa bile `regime_ok` sayılır) gölgeye UYGULANMAZ. Uyuyan plan canlıda BUGÜN yalnız
      keşif sondası olarak silahlanabildiği için bu bir sapmadır ve ADIYLA yazılıdır: gölge kolu
      SIKI kapıyla ölçülür, yani bütçe-0 seanslarında açık gölge pozisyonları `regime_flip` ile
      kapanır. Yön TEK TARAFLI DEĞİLDİR (erken çıkış kazananı da keser, kaybedeni de) ve kartın
      hipotezi "uyuyan kurulumlar NORMAL yolda R kazandırır mıydı" sorusudur — gevşek kapıyı
      kullanmak o soruyu keşif sondasının sorusuna çevirirdi. Kontrol kolu (PK 2) gerçek işlemin
      ikizidir ve gerçek işlemler de küresel kapıyla yönetilir; keşif kökenli gerçek işlemlerde
      bu sapma PK (2)'de fark olarak GÖRÜNÜR (gizlenmez).

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

#: PIT ÇAPASININ ISINMA PENCERESİ — çıkış yasasının GİRİŞ ÖNCESİNE uzanan geriye bakışı.
#: ÖLÇÜLDÜ (`strategy.manage_position` gövdesi, 2026-09-12): giriş öncesine uzanan TEK okuma
#: `ind.atr(df, ATR_PERIOD)`tır (Wilder EWM; `min_periods=ATR_PERIOD`, true range bir önceki
#: kapanışı da ister → `ATR_PERIOD + 1` bar). Diğer geriye dönük pencereler ömre KELEPÇELİDİR ve
#: girişin öncesine geçemez: chandelier `iloc[-min(chand_lb, max(1, bars_held)):]`, giveback
#: `iloc[-bars_held:]`, erken itlaf yalnız son kapanış. `_touch_exit` tek bara bakar.
#: Sabit ÜRETİMDEN türetilir: ATR periyodu orada değişirse çapa penceresi kendiliğinden kayar
#: (ikinci bir "14" kopyası yazmak, iki yorumun sessizce ayrışması demekti).
#: EWM teorik olarak tüm geçmişe bağlıdır; kapsam bu yüzden SONSUZ değil TANIMLIDIR ve sınırı
#: burada ADIYLA durur — çapayı tüm seriye açmak `bar_n`i ve `ACIK` belgesini sınırsız şişirirdi.
LOOKBACK_BAR = strategy.ATR_PERIOD + 1

KOLLAR = ("dormant", "kontrol")            # `kol` alanının kapalı kümesi
BAR_KAYNAKLARI = ("state/bars", "arsiv")   # PIT çapasının kaynağı (canlı yol | tarihsel yeniden yürütme)

#: DEFTER SATIRININ TAM ALAN KÜMESİ — şema burada TEK YERDE yazılıdır ve her satır alanların
#: HEPSİNİ taşır (ölçülemeyen alan `None`, "yok" DEĞİL): eksik anahtar, okuyucunun `get`
#: varsayılanıyla sessizce dolar ve "yazılmadı" ile "ölçülemedi" ayrımı kaybolurdu.
SATIR_ALANLARI: tuple[str, ...] = (
    "ts", "plan_id", "ticker", "kurulum", "hukum", "kol", "ts_plan",
    "giris_ts", "giris_fiyat", "stop", "hedef", "giris_kurali",
    "cikis_ts", "cikis_fiyat", "cikis_neden", "R", "bar_n",
    "kaynak_bar_hash", "bar_kaynak", "strategy_version",
    "giris_reddi", "olculemedi",
)

#: GİRİŞ YASASININ ADI — her satırda durur. Okuyucu, satırın hangi dolum semantiğiyle üretildiğini
#: defterden bilir; kural değişirse eski satırlar ESKİ adıyla kalır ve iki kuşak karışmaz.
GIRIS_KURALI = "stop_al"

#: GİRİŞİN OLMAMA NEDENLERİ — kapalı küme. `cikis_neden` bu satırlarda daima `GIRIS_YOK`tur
#: (sınıf), `giris_reddi` ise ADIDIR (tanı). İkisini tek alana sıkıştırmak, çıkış sebebi
#: dağılımını (sayım betiğinin ham maddesi) giriş redleriyle karıştırırdı.
GIRIS_YOK = "giris_yok"
GIRIS_REDLERI = ("tetik_gelmedi", "gap_asildi", "limit_asildi", "acilis_stop_altinda", "bar_yok")

#: İşlenmiş plan kimliklerinin BEYANLI tavanı. Aynı planın iki kez gölgeye girmesini engelleyen
#: küme süresiz büyüseydi `ACIK` dosyası tek yönlü şişerdi; tavan aşıldığında en ESKİ kimlikler
#: düşer ve o planlar (defterde zaten satırı olduğu için) yalnız teorik olarak yeniden girebilir.
ISLENEN_TAVANI = 2000


def _bos_belge(simdi=None) -> dict:
    """Boş gölge belgesi: şema, kart kimliği, kuruluş anı, PENCERE BEYANI ve üç boş kova."""
    return {"schema": SEMA, "kart": KART, "kurulus": _ts(simdi), "son_seans": None,
            "pencere_baslangic": None, "atlanan_seanslar": [],
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


def _capa_nedeni(kesitler) -> str:
    """`bar_hash` None döndüyse NEDENİ: hiç kesit yok mu, yoksa bir HANE mi eksik?

    "Ölçülemedi" adsız bırakılamaz: hacim sütunu olmayan bir kaynak ile hiç bar tüketmemiş bir
    plan aynı hükmü alır ama AYNI OLGU değildir.
    """
    return "kesit_yok" if not kesitler else "hane_eksik"


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
    return bar, _kesit_kur(r, d, ticker)


def _kesit_kur(r, d, ticker: str) -> list:
    """Tek bar satırından hash kesiti — `(ticker, tarih, o, h, l, c, hacim)`.

    TEK YAZIM: hem seans barı (`_bar_kesiti`) hem ısınma barları (`_isinma_kesitleri`) bu kurucuyu
    çağırır; iki kesit biçimi ayrışsaydı aynı bar iki farklı hash üretirdi.
    """
    hacim = float(r["volume"]) if "volume" in r.index else None
    return [str(ticker), str(pd.Timestamp(d).date()), float(r["open"]), float(r["high"]),
            float(r["low"]), float(r["close"]), hacim]


def _isinma_kesitleri(df, d: pd.Timestamp, ticker: str, n: int = LOOKBACK_BAR) -> list:
    """Giriş barından ÖNCEKİ `n` barın kesitleri (ATR ısınma penceresi) — yoksa boş liste.

    NEDEN ÇAPADA (inceleme M2-03/M4-05): CLOSE(D) fazı `strategy.manage_position`a `df.loc[:d]`in
    TAMAMINI verir ve trail/breakeven kararı `ind.atr(df, ATR_PERIOD)` üzerinden kurulur. Giriş
    öncesi bir barın OHLC'si değişirse ATR → trail → çıkış (fiyat/neden/R) değişebilir; çapa o
    barları kapsamasaydı `kaynak_bar_hash` AYNI kalır ve PIT doğrulaması sessizce yanlış-pozitif
    verirdi. Pencere `.iloc` ile DEĞİL maske + `tail` ile alınır: yinelenen indeks damgası
    (`.loc` iki satır döndürür) bu yolda satırı patlatmaz.
    """
    if df is None or n <= 0:
        return []
    onceki = df[df.index < d]
    return [_kesit_kur(r, t, ticker) for t, r in onceki.tail(int(n)).iterrows()]


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
    # BAR KAYNAĞI KAPALI KÜMEDİR VE ZORLANIR (inceleme M4-09): küme "beyanlı" olup denetlenmezse
    # PIT çapasının KAYNAĞI bir etiketten ibaret kalır ve kill#6 mekanik kancasız olur. Uydurma
    # yasağının tersi değil aynısı: bilinmeyen bir kaynak adı sessizce deftere yazılamaz.
    if bar_kaynak not in BAR_KAYNAKLARI:
        raise ValueError(f"bar_kaynak beyanlı kümede değil: {bar_kaynak!r} "
                         f"(geçerli: {list(BAR_KAYNAKLARI)})")
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
    atlanan_seanslar: list = list(doc.get("atlanan_seanslar") or [])
    satirlar: list[dict] = []

    # ---- 0. ATLANAN SEANS İZİ (inceleme M1-02) -----------------------------------------------
    # Kanca P2 kapısının İÇİNDEDİR: HALT / bozuk veri / bütçe 0 / kitap dolu turlarında — ve
    # `golge_icra_failed` ile düşen turlarda — `adim` HİÇ çağrılmaz. O seansların barları açık
    # pozisyonlar tarafından TÜKETİLMEZ: dokunulan stop görülmez, `bars_held` eksik sayılır. Eski
    # hâlde satır yine de TAM çapayla K'ye giriyordu; yani delikli bir küme tam gibi damgalanıyordu.
    # Artık delik ADIYLA sayılır ve satır K DIŞINA düşer (hash None).
    if son is not None:
        atlanan_gunler: set[str] = set()
        for poz in acik.values():
            df = bars_of(poz["ticker"])
            if df is None:
                continue
            ara = [t for t in df.index if pd.Timestamp(son) < t < d]
            if not ara:
                continue
            poz["eksik_bar"] = int(poz.get("eksik_bar") or 0) + len(ara)
            poz["atlanan_bar"] = int(poz.get("atlanan_bar") or 0) + len(ara)
            atlanan_gunler.update(str(t.date()) for t in ara)
        if atlanan_gunler:
            atlanan_seanslar = sorted(set(atlanan_seanslar) | atlanan_gunler)

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
            # SAYAÇ BURADA ARTMAZ (inceleme M1-07): pid `acik`ten DÜŞMEDİĞİ için aynı eksik gün
            # faz 2'de yeniden görülür ve orada BİR KEZ sayılır. İki artış, tek eksik güne
            # `bar_eksik:2` yazdırıyordu — K üyeliği doğruydu ama tanı sayısı yanlıştı.
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
    # PENCERE BEYANI (kart: "B1 DAĞITIMINDAN itibaren ≤120 gün"). İlk `adim` hangi SEANSTA
    # koştuysa pencerenin kökü odur ve bir daha DEĞİŞMEZ. Kökü defterin ilk satırından okumak
    # (eski hâl) saati sistematik olarak geç başlatıyordu: ilk kapanış dağıtımdan günler-haftalar
    # sonra doğar, yani `gecen_gun` eksik sayılır ve `doldu` hak edilmeden True olabilirdi.
    # SIRA: SATIRLAR ÖNCE, `ACIK` SONRA (inceleme M1-03/M4-06). İki yazım tek işlem DEĞİLDİR
    # (`append_jsonl` düz ekleme, `write_json` kilit+atomik) ve aradaki bir çökme eski sırada
    # KALICI KAYIP üretiyordu: `son_seans` ilerlemiş, kapanan pozisyon `acik`ten düşmüş, satır
    # hiç yazılmamış — ve idempotens kapısı o seansı bir daha koşturmaz. Yeni sırada aynı çökme
    # MÜKERRER üretir; mükerrer okuyucuda kapanır (`tekillestir`), kayıp kapanmaz.
    for satir in satirlar:
        store.append_jsonl(DEFTER, satir)
    store.write_json(ACIK, {"schema": SEMA, "kart": KART,
                            "kurulus": doc.get("kurulus") or _ts(simdi),
                            "pencere_baslangic": doc.get("pencere_baslangic") or str(dstr),
                            "atlanan_seanslar": atlanan_seanslar,
                            "son_seans": str(dstr), "bekleyen_giris": bekleyen,
                            "acik": acik, "islenen": islenen})
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
    df = bars_of(kayit["ticker"])
    bar, kesit = _bar_kesiti(df, d, kayit["ticker"])
    if bar is None:
        return _giris_yok_satiri(kayit, dstr, "bar_yok", [], simdi, bar_kaynak,
                                 olculemedi="bar_yok"), None
    tetik, stop = float(kayit["tetik"]), float(kayit["stop"])
    if tetik > 0 and bar["high"] < tetik:
        return _giris_yok_satiri(kayit, dstr, "tetik_gelmedi", [kesit], simdi, bar_kaynak), None
    # STOP-AL DOLUMU (beyanlı sapma 3): buy-stop emri tetikte tetiklenir ve tetikten dolar;
    # açılış zaten tetiğin üstündeyse (boşluk) açılıştan dolar. Tetik ÖLÇÜLEMEMİŞSE (`0.0`)
    # tetik yasası hiç uygulanmaz ve üretimin davranışı kalır: açılıştan dolum.
    dolum = max(bar["open"], tetik) if tetik > 0 else bar["open"]
    # GAP MUHAFIZI — ÜRETİMİN KENDİ SABİTİYLE (`broker.MAX_ENTRY_GAP_PCT`), kopya değil İTHAL.
    # `fill_entry` bu kapıyı limit tavanından ÖNCE uygular; sıra korunur ki iki motorun REDDİ aynı
    # ADI taşısın. Bugünkü yapılandırmada ikisi aynı fiyatta bağlar (%4) — ama `limit_pct_cap`
    # goal'de %10'a kadar açılabilir ve o zaman gölge girer, canlı reddederdi (sapma gölge LEHİNE).
    if tetik > 0 and dolum > tetik * (1.0 + brk.MAX_ENTRY_GAP_PCT):
        return _giris_yok_satiri(kayit, dstr, "gap_asildi", [kesit], simdi, bar_kaynak), None
    if tetik > 0 and dolum > brk.entry_limit_price(tetik, None):
        return _giris_yok_satiri(kayit, dstr, "limit_asildi", [kesit], simdi, bar_kaynak), None
    if dolum <= stop:
        return _giris_yok_satiri(kayit, dstr, "acilis_stop_altinda", [kesit], simdi,
                                 bar_kaynak), None
    poz = {k: kayit[k] for k in ("plan_id", "ticker", "kurulum", "hukum", "kol", "ts_plan",
                                 "stop", "hedef", "strategy_version")}
    poz.update({"giris_ts": str(dstr), "giris_fiyat": dolum, "trail_stop": stop,
                "r_per_share": dolum - stop, "pivot": 0.0, "bars_held": 0,
                "hi_water": dolum, "lo_water": dolum, "pre_scale_stop": None,
                "bekleyen_cikis": None, "eksik_bar": 0, "atlanan_bar": 0,
                "tuketilen": _isinma_kesitleri(df, d, kayit["ticker"]) + [kesit]})
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
        # TSK-187: taban da NOMİNALDİR (1 hisse) — bu nesne `_touch_exit` için kurulur ve
        # `close_position`a hiç girmez, ama tabanı 0 bırakmak "ölçülemedi" demek olurdu ve
        # yanlıştır: bu defterin adedi BİLİNİYOR, nominal olarak 1'dir.
        qty_taban=1,
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
                  giris_kurali=GIRIS_KURALI,
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
    atlanan = int(poz.get("atlanan_bar") or 0)
    kesitler = poz.get("tuketilen") or []
    h = None if eksik else bar_hash(kesitler)
    # NEDEN ÜÇ DALLI: "seans atlandı" (kanca hiç koşmadı), "bar eksik" (seans koştu, bar yoktu) ve
    # "hash kurulamadı" (barlar tamdı ama bir HANE eksikti — ör. hacim sütunu yok) AYRI olgulardır.
    # Üçüncüsü eskiden `olculemedi=None` ile sessizce K dışına düşüyordu: NEDENSİZ ölçülemezlik.
    olcum_nedeni = (f"seans_atlandi:{atlanan}" if atlanan else
                    f"bar_eksik:{eksik}" if eksik else
                    f"hash_yok:{_capa_nedeni(kesitler)}" if h is None else None)
    return _satir(ts=_ts(simdi), plan_id=poz["plan_id"], ticker=poz["ticker"],
                  kurulum=poz["kurulum"], hukum=poz["hukum"], kol=poz["kol"],
                  ts_plan=poz["ts_plan"], giris_ts=poz["giris_ts"],
                  giris_fiyat=round(float(poz["giris_fiyat"]), 4), stop=float(poz["stop"]),
                  hedef=float(poz["hedef"]), giris_kurali=GIRIS_KURALI, cikis_ts=str(dstr),
                  cikis_fiyat=round(float(cikis), 4), cikis_neden=str(neden), R=r,
                  bar_n=len(kesitler), kaynak_bar_hash=h,
                  bar_kaynak=bar_kaynak, strategy_version=poz["strategy_version"],
                  olculemedi=olcum_nedeni)


# ==================================================================================================
# K PAYDASI — TEK KAYNAK. Motorun `ozet`i de sayım betiği de BU yüklemleri çağırır.
# ==================================================================================================
def olculdu(satir: dict) -> bool:
    """Satırın R'si ÖLÇÜLMÜŞ, PIT çapası TAM ve bar kaynağı BEYANLI kümeden mi?
    (Kol sormaz — iki kol için de aynı ölçüt.)

    Tetiği hiç gelmeyen plan (`R=None`) ve çapası yarım kalan satır (`kaynak_bar_hash=None`)
    TANIdır: ölçülmemiştir, üzerine hiçbir hüküm kurulamaz. `bar_kaynak` şartı kill#6'nın okuyucu
    tarafıdır: `adim` küme dışı bir kaynağı zaten reddeder, ama deftere BAŞKA bir yoldan (eski
    sürüm, elle düzenleme, ikinci yazıcı) düşmüş bir satır K'ye sessizce giremez.
    """
    return (satir.get("R") is not None and bool(satir.get("kaynak_bar_hash"))
            and satir.get("bar_kaynak") in BAR_KAYNAKLARI)


def sayilir(satir: dict) -> bool:
    """Satır K paydasına girer mi? `kol == dormant` ∧ `olculdu`.

    KOL SÜZGECİ YÜKLÜDÜR (düzeltme 2026-09-12, inceleme M3-01/M4-01). Kartın hipotezi YALNIZ
    uyuyan planlar içindir; kontrol kolu (o seans silahlanan normal planların gölge eşlenikleri)
    PK (2)'nin SADAKAT ölçüsüdür, K popülasyonu DEĞİL. Kol süzülmeyince canlı strateji kolunun
    R'si hipotezin paydasına karışıyordu ve n≥30 eşiği kontrol satırlarıyla dolabiliyordu —
    "eşiği hak etmeden geçme" yönünde yanlı.

    TEK YAZIM: sayım betiği bu fonksiyonu İTHAL EDER (`sayim.sayilir is golge_icra.sayilir`),
    ikinci kez yazmaz.
    """
    return satir.get("kol") == KOLLAR[0] and olculdu(satir)


def olculemeyen_neden(satir: dict) -> str:
    """Ölçülemeyen satırın NEDENİ — tek sözlük, iki okuyucu (`ozet` ve sayım betiği).

    Öncelik: satırın kendi `olculemedi` damgası → giriş reddi → beyanlı küme dışı bar kaynağı →
    çapasızlık (R ölçülmüşken) → R'nin hiç ölçülmemiş olması. "Çapa yok" ile "R yok" AYRI
    olgulardır ve tek ada sıkıştırılırsa okuyucu hangisinin olduğunu defterden bilemez.
    """
    if satir.get("olculemedi"):
        return str(satir["olculemedi"])
    if satir.get("giris_reddi"):
        return str(satir["giris_reddi"])
    if satir.get("bar_kaynak") not in BAR_KAYNAKLARI:
        return f"bar_kaynak_bilinmiyor:{satir.get('bar_kaynak')!r}"
    return "capa_yok" if satir.get("R") is not None else "R_yok"


def tekillestir(satirlar: list[dict]) -> tuple[list[dict], int]:
    """`plan_id` başına SON satır + MÜKERRER sayısı. Sıra korunur.

    NEDEN OKUYUCUDA (inceleme M1-03/M4-06): yazım sırası artık "satırlar önce, `ACIK` sonra"dır
    ve bu, çökmeyi KAYIPTAN MÜKERRERE çevirir. Mükerrer yalnız okuyucuda kapanabilir: her plan tam
    bir satır üretir, yeniden koşum onu AYNI plan kimliğiyle yazar, son yazım en güncel olandır.
    `plan_id`siz satır (şema bozuk) tekilleştirmeye GİRMEZ — ortak boş anahtar altında birbirini
    yerdi.
    """
    out: list[dict] = []
    indeks: dict[str, int] = {}
    mukerrer = 0
    for r in satirlar:
        pid = str(r.get("plan_id") or "")
        if not pid:
            out.append(r)
            continue
        if pid in indeks:
            out[indeks[pid]] = r
            mukerrer += 1
        else:
            indeks[pid] = len(out)
            out.append(r)
    return out, mukerrer


# ==================================================================================================
# ÖZET — DIŞ OKUYUCUNUN (api) YÜZEYİ. HÜKÜM YOKTUR.
# ==================================================================================================
def ozet(gun: int = PENCERE_GUN) -> dict:
    """Defterin betimleyici özeti — HİÇBİR EŞİK HÜKMÜ DÖNDÜRMEZ.

    Hüküm (CI, kazanma eşiği, GEÇER/KALIR) sayım betiğinin ve Rol-1'in işidir; bir pano ucunun
    hüküm cümlesi üretmesi, eşiği kartın dışında ikinci kez yorumlamak olurdu. Burada yalnız
    sayılar, dağılımlar, pencere durumu, bedel ve ÖLÇÜLEMEYENLER vardır.

    K PAYDASI (kart hükmü 5) = `sayilir`: UYUYAN KOLUN kapanan ve R'si ÖLÇÜLMÜŞ satırları. Tetiği
    hiç gelmeyen plan (`giris_yok`, `R=None`), PIT çapası yarım kalan satır
    (`kaynak_bar_hash=None`) ve KONTROL kolu TANIdır, paydada değildir — eksik K, eşiği hak
    etmeden geçme yönünde yanlıdır; kontrol kolu ise BAŞKA bir popülasyondur (PK 2'nin sadakat
    ölçüsü) ve hipotezin paydasına karışırsa ölçü geçersizleşir.

    İKİ KÜME, İKİ DAĞILIM: `hukum_dagilimi`/`kurulum_kirilimi`/`cikis_neden_dagilimi` K'nin,
    `giren_*` ve `kol_kirilimi` gölgeye GİREN tüm satırların dağılımıdır.
    """
    satirlar, mukerrer_n = tekillestir(kayit_al())
    doc = acik_kayit()
    sayilan = [r for r in satirlar if sayilir(r)]
    olculemeyen = [{"plan_id": r.get("plan_id"), "kol": r.get("kol"),
                    "neden": olculemeyen_neden(r)}
                   for r in satirlar if not olculdu(r)]
    n = len(sayilan)
    n_kontrol = len([r for r in satirlar if r.get("kol") == KOLLAR[1] and olculdu(r)])
    rler = [float(r["R"]) for r in sayilan]
    kazanan = [x for x in rler if x > 0]
    kaybeden = [x for x in rler if x < 0]
    ilk_satir_ts = min((str(r.get("ts")) for r in satirlar if r.get("ts")), default=None)
    baslangic = doc.get("pencere_baslangic")
    gecen = _gecen_gun(baslangic)
    pencere_neden = None
    if not baslangic:
        pencere_neden = ("pencere beyanı YOK (`acik.pencere_baslangic`) — gölge adımı hiç "
                         "koşmamış ya da belge eski şemada; geçen gün ÖLÇÜLEMEDİ (0 DEĞİL)")
    elif gecen is None:
        pencere_neden = f"pencere beyanı ayrıştırılamadı ({baslangic!r}) — geçen gün ÖLÇÜLEMEDİ"
    # BEDELİN PAYI DA PAYDASI DA AYNI PENCEREDEN: pencere dışı (eski kuşak/geri dolum) satırlar
    # paya girseydi satır/gün şişerdi ve "bedel ölçüldü" iddiası yanlış sayı taşırdı.
    pencere_ici = ([r for r in satirlar if str(r.get("ts") or "")[:10] >= str(baslangic)]
                   if baslangic else [])
    return {
        "kart": KART,
        "n": n,
        "n_kontrol": n_kontrol,
        "mukerrer_n": mukerrer_n,
        "atlanan_seanslar": list(doc.get("atlanan_seanslar") or []),
        "n_acik": len(doc.get("acik") or {}),
        "n_bekleyen_giris": len(doc.get("bekleyen_giris") or {}),
        "son_seans": doc.get("son_seans"),
        "toplam_r": round(sum(rler), 6) if n else None,
        "kazanma_orani": round(len(kazanan) / n, 4) if n else None,
        "pf": (round(sum(kazanan) / abs(sum(kaybeden)), 4) if kaybeden else None),
        # K DAĞILIMLARI (payda = `sayilan`, yani dormant ∧ ölçülmüş)
        "hukum_dagilimi": _dagilim(sayilan, "hukum"),
        "kurulum_kirilimi": _dagilim(sayilan, "kurulum"),
        "cikis_neden_dagilimi": _dagilim(sayilan, "cikis_neden"),
        # GİREN DAĞILIMLARI (payda = gölgeye giren TÜM satırlar). Kartın tanı maddesi
        # ("dormant planların TAMAMI gölgeye girer, GO/REVIEW/NO_GO dağılımı tanı olarak
        # raporlanır") bu popülasyonu sorar; K dağılımı ona cevap VEREMEZ çünkü girişi hiç
        # olmayan plan K'de yoktur.
        "giren_n": len(satirlar),
        "kol_kirilimi": _dagilim(satirlar, "kol"),
        "giren_hukum_dagilimi": _dagilim(satirlar, "hukum"),
        "giren_kurulum_kirilimi": _dagilim(satirlar, "kurulum"),
        "pencere": {"baslangic": baslangic,
                    "baslangic_kaynagi": ("acik.pencere_baslangic" if baslangic else None),
                    "ilk_satir_ts": ilk_satir_ts, "gun": int(gun), "gecen_gun": gecen,
                    "doldu": bool(n >= N_ALT and gecen is not None and gecen <= int(gun)),
                    "suresi_doldu": bool(gecen is not None and gecen > int(gun)),
                    "neden": pencere_neden},
        "bedel": {"satir_gun": (round(len(pencere_ici) / gecen, 3)
                                if gecen and gecen > 0 else None),
                  "bayt": _defter_bayti(),
                  # YAPISAL SIFIR BEYANI, SAYAÇ DEĞİL: motorun ithal kapanışında ağ/LLM yüzeyi
                  # YOKTUR (`barclock`·`broker`·`store`·`strategy` → hiçbiri httpx/hermes/spend
                  # görmez) ve `adim` hiçbir istek yapmaz. Buraya bir sayaç koymak, ölçülmeyen
                  # bir şeyi "ölçtüm" gibi sunardı; alan beyanın KENDİSİDİR ve çivisi alanın
                  # yerinde durduğunu kontrol eder (inceleme M4-12).
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
