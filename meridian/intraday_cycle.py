"""intraday_cycle.py — kapanmış dakikalık barların tüketicisi: sıfır-yetkili gözlem/gölge ölçümü ve
dar koşullu gönderim bacağı.

barfeed her yeni-bar olayında `IntradayConsumer.on_barfeed_event`i uyandırır (kayıt api._autostart'ta;
`consumer()` tekil örneği, `health()` durum özetini verir). Gözlem modu SIFIR YETKİLİDİR: yalnız
admissible (kapanmış) dakikalık barlarda günün planlarının tetik-geçişini ölçer ve
`intraday_decisions.jsonl`e 3 damgalı (decision_as_of / bar_t / close_ts) satır yazar — emir
göndermez, canlı defteri fill etmez, portfolio.json'a dokunmaz. İlgi kümesi günün plan üretiminin
TAMAMIdır (son EOD turunun `trade_plans.jsonl` satırları ∪ açık pozisyonlar ∪ silahlı planlar):
yalnız silahlı planları izlemek, silahlanma kuraklığında izlenen sembol sayısını sıfıra indiriyor ve
dakika-bar kanıt katmanını aç bırakıyordu. Yetki farkı satırda etikettir (`eod_armed`, `plan_source`)
— silahsız planın tetiğini ÖLÇMEK onu silahlandırmak değildir.

Gölge katmanı: tetik kesildiğinde `intraday_shadow.record` o anın TAM icra kararını (kapılar +
boyutlandırma + emir niyeti) KOPYA bir PaperBroker üzerinde hesaplar, kendi defterine yazar ve
nesneyi atar. Gölge iki kolludur: silahlı kolun defteri ve onu okuyan ölçümler (vs_eod, dakika-bar
çıkış ölçümü) değişmeden durur; planlı kol AYRI deftere (`intraday_shadow.PLANLI_ORDERS_FILE`) yazar
ki vs_eod eşleştirmesi sulanmasın. Gönderim bacağı (`_faz4b`) YALNIZ operatörün elle açtığı
state/INTRADAY_ARM bayrağıyla, silahlı kolun gölge satırı `would_submit` dediyse ve plan icra-uygunsa
gerçek bracket emrini TEK KAPIDAN (loop.mirror_submit_ve_kalicilastir) gönderir — güvenlik kapıları
EOD yoluyla aynı gövdeden uygulanır; bayrak kapalıyken davranış gözlem moduyla birebir aynıdır.
İKİNCİ (AYRI YETKİLİ) GÖNDERİM YOLU — SABAH KANCASI (`_pencere_gonderim`, EXE-2026-009 + K2):
tarama/emir tetiği 13:45'e kaydı (`barclock.ENTRY_WINDOW_ET_MIN`); pencere öncesi olaylar hiçbir
karar/gölge üretmez (`skipped["pencere"]`), pencere açılınca EOD'de pencere yasasıyla ERTELENMİŞ
silahlı gönderimler aynı tek kapıdan gider. Bu 4b'nin yetkisi DEĞİLDİR ve INTRADAY_ARM'a bağlı
değildir: kancanın gönderdiği planlar EOD kadansının zaten göndereceği planlardır — yetki EOD'den
devralınır, yalnız zamanlama pencereye taşınmıştır (gerekçe fonksiyon docstring'inde).

Look-ahead yasası (bkz. barclock): karar anı `as_of=barclock.now()` olay başına TEK kez; girdi
DEĞERLENDİRİLEN admissible barın OHLC'sinden, ASLA sıcak fiyattan; her satır 3 damgalı →
`as_of >= close_ts` sonradan denetlenebilir. Gözlem-önce gerekçesi: dakikalık bar öğrenmeye/backtest'e
girmez (OOS kanıtı yok) ve strateji GÜNLÜK kalibredir — ham dakikalık barda "karar" kategori
hatasıdır; tetik-geçiş ölçümü değildir (eşik kontrolüdür, gösterge hesaplamaz). Okur: barfeed
olayları, portfolio.json, trade_plans.jsonl; yazar: intraday_decisions.jsonl. Komşular: barclock,
hotstate, intraday_shadow, loop."""
from __future__ import annotations
import collections
import datetime as _dt
import os
import threading

from . import barclock, config, gecikme, hotstate, store, obs
from . import health as _health

INTRADAY_LOOKBACK = 390          # ~1 seans dakikası; read_bars tavanı
STALE_TOL_S = 120                # en yeni admissible bar bundan eskiyse karar/ölçüm yok (bayat fiyat)
DECISIONS_FILE = "intraday_decisions.jsonl"
PLANS_FILE = "trade_plans.jsonl"
ENABLED = os.environ.get("MERIDIAN_INTRADAY", "1") != "0"

# Günün plan üretimi — (plan_date, dosya mtime) anahtarlı ÖNBELLEK. Olay başına 390 satır JSON
# ayrıştırmak dakikalık kadansta gereksiz G/Ç'dir; mtime anahtarı yüzünden EOD turu dosyayı
# tazelediği an önbellek kendiliğinden düşer (zaman aşımı yok — bayatlık değil, doğruluk).
_PLANS_CACHE: tuple | None = None

# KARAR DÖNGÜSÜ TURU SÜRESİ (TSK-020 UYGULA-9 Faz B, tasarım T4) — `on_barfeed_event`in TAMAMI (v217'nin KILL#1
# düzeneğinin ölçtüğü "döngü" ile aynı sınır), olay başına bir gözlem. Kart EXE-2026-003 "p95 döngü enstrümanı yok"
# diyordu; bu alet CANLIDA veri biriktirir — ama GÖZLEMDİR: KILL#1 hükmü buradan OKUNMAZ, canlı çapa ayrı karttır
# (Faz C, tasarım §2).
# SONUÇ ETİKETİ (beyanlı, sabit küme; kullanıcı girdisinden türemez): `processed` = kapıları geçip işlenen olay
# (`events_handled` arttı), `skipped` = seans/pencere/HALT kapısında dönen olay (µs mertebesi), `error` = `_handle`
# istisnası yutuldu. Ayrım ŞART: kapı-önü dönüşler seans dışında ve pencere öncesinde olay akışının büyük kısmıdır;
# tek seride karışsalar p95'i işlenen olayların maliyetinden AŞAĞI çekerler — ölçüm aleti eşikten GEÇME yönünde sapar.
# KOVALAR (saniye): 250 µs … 10 s. Ölçek ÖLÇÜLDÜ (v217 KILL#1 düzeneği, 2026-09-28, bu ağaç, M3): 5 sembollük
# sentetik olay p95 1,17–1,46 ms, en kötü olay 5,0 ms — canlıda ilgi kümesi ~10+ sembol ve Redis okuması → işlenen
# olay beklenen bandı 1–25 ms; bu bantta sınırlar ~1,5–2× sık. Üst uç ağ dalları (`_pencere_gonderim`/`_faz4b` Alpaca
# REST) için 10 s. Kova içi ara değerleme kantili yaklaşık yapar; +%10'luk bir kaymayı `histogram_quantile`
# ÇÖZEMEZ — Faz C kartı istatistiğini buna göre kurar (ör. sabit sınır üstü pay).
DONGU_SONUCLARI = ("processed", "skipped", "error")
DONGU_SURESI = gecikme.Histogram(
    "meridian_intraday_cycle_seconds",
    "intraday decision-cycle turn duration per barfeed event (IntradayConsumer.on_barfeed_event), by outcome",
    kovalar=(0.00025, 0.0005, 0.001, 0.002, 0.003, 0.005, 0.0075, 0.01, 0.015, 0.025, 0.05, 0.1, 0.25, 0.5,
             1.0, 2.5, 5.0, 10.0),
    etiket="outcome", etiket_degerleri=DONGU_SONUCLARI)

# EXE-2026-012 ALETİ — KILL#1 CANLI ÇAPASI, TUR İÇİ ATIF (TSK-020 UYGULA-9 Faz C; kart
# research/cards/EXE-2026-012-kill1-canli-capa.yaml, `olcum_plani` ALET (1)–(5)). Her işlenen/hatalı olayın tur süresi X
# ile AYNI olayda planli kol dalında geçen süre Z yan yana, YUVARLAMASIZ kaydedilir; hükmü (Y = X − Z, R = p95(X)/p95(Y))
# Rol-1'in betiği okur. Kova çözünürlüğü (%33–100) +%10'u ayırt edemediği için bu kayıt `DONGU_SURESI`nin YERİNE değil
# YANINDA durur:
#   (1) X = `DONGU_SURESI`ne işlenen değerin KENDİSİ (`gecikme.Olcum` çıkış değeri) — İKİNCİ KRONOMETRE YOK.
#   (2) Z = `_handle_symbol` planli dal gövdesinin süresi (hata dalı dahil), olaydaki semboller üzerinden TOPLANIR,
#       AYNI saatle (`gecikme._saat`). Silahlı dal ve plansız semboller Z'ye GİRMEZ.
#   (3) Kayıt süreç belleğinde, seans başına; yalnız `processed` ve `error` — `skipped` KAYDEDİLMEZ (kapı-önü µs
#       dönüşleri p95'i işlenen olayın maliyetinden aşağı çekerdi). Alan sırası `ATIF_ALANLARI`. Kayıt olay turu
#       KAPANDIKTAN sonra eklenir → X'e GİRMEZ.
#   (4) Toplu yazım `state/` altında tek defter (`ATIF_DEFTERI`), seans başına TEK satır, olay turunun ölçümü DIŞINDA:
#       seans kapısında dönen ilk olayda ya da kayıtlı bir olayın seansı tampondakinden farklıysa; ayrıca işçinin
#       DÜZGÜN kapanışında (`api._lifespan` kapanış kolu → `IntradayConsumer.kapanista_bosalt`). Nedenin değer sözlüğü
#       `ATIF_BOSALTMA`. Boş tampon satır YAZMAZ. Takas + yazım `_atif_kilit` altında (kapanış boşaltması lifespan iş
#       parçacığından gelir, barfeed daemon iş parçacığı kapanışta durmaz). Satır süreç başlangıç damgasını
#       (`_SUREC_BASLANGIC`) + pid'i taşır: seans içi yeniden başlatmayı okuyucu bununla ayırır (yeniden başlatmada
#       kaybolan ya da kapanışta kısmen yazılan tampon, o seansın satırında seans açılışından SONRAKİ bir damgayla
#       görünür; aynı seansın satırları (seans, surec_baslangic, pid) ile birleştirilir). DİSK: ~109 KB/seans (sentetik;
#       gerçek değer ADIM-0c) × ~252 seans ≈ 27 MB/yıl; aletin ömrü 20–40 seans ≈ 2–4 MB; rotasyon YOK — alet emekli
#       edilince yazım sökülür, defter silinmez (hüküm kesiti research/ altına dondurulur). Yazım kilitsiz dosya
#       eklemesidir (emsal defterlerle aynı, tek yazar): SIGKILL/OOM yazımın ortasında keserse son satır yarım kalabilir —
#       okuyucu onu bozuk satır olarak ayıklar, seans eksik sayılır.
#   (5) Kapatma: `MERIDIAN_TUR_ATIF=0` (intraday_shadow ENABLED deseni; import anında okunur, varsayılan AÇIK).
# SINIR (kart kill_list, tasarım §2): OTOMATİK KAPI YOK — hiçbir motor kodu bu defteri okuyup planli kolu
# kapatamaz/açamaz; okuyucu motor DIŞINDADIR (research/olcumler/exe012_kill1_canli/, Rol-1). BEDEL (kart
# beyanli_sinirlar 4): kayıt + toplu yazım sıcak yolda ÖLÇÜLMEYEN bir ektir; planli dal kronometresi (iki saat okuması)
# X'in İÇİNDEDİR. İkisinin ölçüsü tests/test_exe012_alet_v606.py G bölümünde.
ATIF_ENABLED = os.environ.get("MERIDIAN_TUR_ATIF", "1") != "0"
ATIF_KART = "EXE-2026-012"
ATIF_DEFTERI = "exe012_tur_atif.jsonl"
ATIF_ALANLARI = ("outcome", "x_s", "z_s", "ofset_s", "planli_giris", "planli_yazim")
# Olay kaydı — alan SIRASI `ATIF_ALANLARI`dan türer (tek kaynak); kurucu yalnız ADLA doldurulur (`_atif_kaydet`).
AtifOlay = collections.namedtuple("AtifOlay", ATIF_ALANLARI)
# `bosaltma` alanının değer sözlüğü (B dilimi okuyucusu için): seans kapısında dönen ilk olay · kayıtlı olayın seansı
# değişti · işçinin düzgün kapanışı (seans ortasındaysa satır KISMİ seanstır).
ATIF_BOSALTMA = ("seans_kapandi", "seans_degisti", "kapanis")
# Süreç başlangıç damgası (duvar saati, UTC) ve olay ofsetinin tabanı (X/Z ile AYNI saat: ofset = olayın X ölçümünün
# başladığı an − bu okuma). Modül içe aktarımı süreç açılışındadır (`api._autostart` tüketiciyi orada kaydeder).
_SUREC_BASLANGIC = _dt.datetime.now(_dt.timezone.utc).isoformat()
_SUREC_SAAT0 = gecikme._saat()


def reset_plans_cache() -> None:
    """Plan önbelleğini boşalt (testler + seans dönüşü) — `intraday_shadow.reset_dedup` deseni.
    Süreç-içi bir önbelleğin testler arası sızması, testin kendi kurmadığı veriyle 'geçmesi' demektir."""
    global _PLANS_CACHE
    _PLANS_CACHE = None


class IntradayConsumer:
    """Tek tüketici (barfeed callback'i). Kendi thread'i YOK — barfeed daemon thread'inde koşar."""

    def __init__(self):
        """Tüketiciyi sıfır sayaçlarla kurar: olay/karar sayaçları, izlenen nüfus, iki kolun gölge
        sayaçları, 4b gönderim sayacı ve atlama nedenleri.

        Hepsi SÜREÇ-İÇİdir (restart'ta sıfırlanır); kalıcı iz defterlerdedir."""
        self.events_handled = 0
        self.decisions_written = 0
        self.last_decision_at: str | None = None
        self.last_error: str = ""
        self.watched = 0
        self.watched_planned = 0        # ilgi kümesinin PLAN nüfusundan geleni (silahlanma kuraklığı görünür olsun)
        # NÜFUS AYRIMI SAYAÇTA: defterin `fired` toplamı artık SİLAHSIZ planları da
        # içeriyor. Dış tüketici (api) toplamı bölmeden okuduğu için, ayrımı ÜRETİCİ tarafında
        # sayıyoruz — yoksa panodaki "fired" sayısı sessizce anlam değiştirir ve kimse görmez.
        # Bunlar SÜREÇ-İÇİ sayaçlardır (restart'ta sıfırlanır); defter toplamı api'de kalır.
        self.decisions_armed = 0
        self.decisions_planned = 0
        self.shadow_written = 0          # Faz 4b gölge satırı sayacı (kanca çalıştı mı görünür olsun)
        # İKİ KOL, İKİ SAYAÇ (kart EXE-2026-003 kill#3): `shadow_written` SİLAHLI kolun sayısıdır ve
        # panoda o adla okunuyor (app.js "gölge kararı"). Yeni kolu ona eklemek, silahli kolun
        # sayımını değiştirmek olurdu — kartın derhal geri alma sebebi.
        self.shadow_planli_written = 0
        # FAZ 4B SAYACI: gönderilen GERÇEK bracket sayısı — gölge sayaçlarından AYRI
        # (gölge ölçümdür, bu icradır; ikisini tek sayaçta toplamak kartın kill#3 sınıfı bir
        # anlam kaymasıdır). Süreç-içi; kalıcı iz E2 defteri + olay defterindedir.
        self.submitted_4b = 0
        # `pencere`: RTH açık ama sabah tetik penceresi (EXE-009+K2) henüz açılmamış — 13:30-13:45
        # arası olaylar tarama/karar üretmez; ayrı sayaç, çünkü `session` "seans dışı" demektir ve
        # iki olguyu tek adda ezmek panoda pencere kaymasını görünmez kılardı.
        self.skipped = {"session": 0, "pencere": 0, "halt": 0, "stale": 0, "no_bars": 0}
        # sabah kancasının gönderim sayacı (pencere açılınca bekleyen silahlı planlar tek kapıdan)
        self.pencere_gonderim_n = 0
        # EXE-2026-012 ALETİ (tur içi atıf; modül başındaki ATIF bloğu): olay başı birikimler — `on_barfeed_event`
        # her olayda sıfırlar, `_handle_symbol`un planli dalı doldurur — ve seans tamponu (`_atif_bosalt` deftere
        # indirir). SÜREÇ-İÇİ; bayrak kapalıyken hiçbiri değişmez.
        self._atif_z = 0.0
        self._atif_giris = 0
        self._atif_yazim = 0
        self._atif_seans: str | None = None
        self._atif_olaylar: list[AtifOlay] = []
        # Tampon takası + defter yazımı bu kilidin ALTINDA (kapanış boşaltması başka iş parçacığından gelir). Yeniden
        # girişli: `_atif_kaydet` kilidi tutarken seans değişimi/kapısı için `_atif_bosalt`ı çağırır.
        self._atif_kilit = threading.RLock()

    # ---- ilgi kümesi: açık pozisyonlar ∪ silahlı ∪ GÜNÜN TÜM PLANLARI (O(≤ plan tavanı)) ----
    def _interest_set(self, pf: dict, planned: dict) -> set:
        """İlgi kümesi: günün planları ∪ açık pozisyonlar ∪ silahlı planlar (hepsi BÜYÜK harf ticker).

        Salt-okuma; bu kümenin dışındaki semboller olay akışında görmezden gelinir."""
        out = set(planned)
        for t in (pf.get("positions") or {}):
            out.add(str(t).upper())
        for pl in (pf.get("armed") or []):
            tk = pl.get("ticker")
            if tk:
                out.add(str(tk).upper())
        return out

    @staticmethod
    def _armed_plan(tk: str, pf: dict) -> dict | None:
        """Portföyün `armed` listesinde bu ticker'a ait plan varsa onu döner, yoksa None.

        Silahlı nüsha kararı üreten kopyadır (keşif sondası boyutu, gate_reasons onda yaşar)."""
        for pl in (pf.get("armed") or []):
            if str(pl.get("ticker", "")).upper() == tk:
                return pl
        return None

    @staticmethod
    def _planned(pf: dict) -> dict:
        """EN SON EOD turunun plan satırları → {TICKER: plan}. Nüfus `portfolio.json.last_date` ile
        çapalanır: o tarih, bu seansın işlem kararlarını üreten turun tarihidir (planlar kapanışta
        kurulur, ertesi açılışta dolar). Rastgele "en son satırlar" almak, bir gün EOD turu düşerse
        gözlemi sessizce BAYAT bir plan kümesine bağlardı — tarih çapası bunu görünür kılar.

        BAŞARISIZLIKTA BOŞ SÖZLÜK: plan defteri okunamazsa gözlem eski davranışına (yalnız
        pozisyon/silahlı) düşer — yani ölçüm daralır, DURMAZ; ve daralma sayaçta görünür."""
        global _PLANS_CACHE
        pdate = pf.get("last_date")
        if not pdate:
            return {}
        # DAMGA ARTIK `store.stamp`: plan defteri SQLite'a taşındığında
        # dosya `.migrated` ekiyle donar; mtime tabanlı önbellek anahtarı bir daha DEĞİŞMEZ ve
        # gözlem katmanı sonsuza kadar ilk turun plan nüfusunu gösterirdi. (0, 0) = defter yok.
        mt = store.stamp(PLANS_FILE)
        if mt == (0, 0):
            return {}
        if _PLANS_CACHE is not None and _PLANS_CACHE[0] == (pdate, mt):
            return _PLANS_CACHE[1]
        out = {}
        for row in store.read_jsonl(PLANS_FILE):
            if row.get("date") != pdate:
                continue
            tk = str(row.get("ticker") or "").upper()
            if tk:
                out.setdefault(tk, row)     # aynı ticker'da ilk satır tutulur (uyuyan-kurulum ikizi)
        _PLANS_CACHE = ((pdate, mt), out)
        return out

    def on_barfeed_event(self, fields: dict) -> None:
        """barfeed daemon thread'inden çağrılır. HATA YUTULUR: bir sembolün/olayın hatası tur/thread'i
        düşürmez (barfeed zaten ACK'ler; tüketici de kendi içinde savunur — kurt masalı değil, kaydeder).

        TUR SÜRESİ `DONGU_SURESI`ne işlenir (sonuç etiketiyle). Sarma davranışı DEĞİŞTİRMEZ: dönüş, sayaçlar ve
        yutma sözleşmesi aynı; `except` dalının kendisi yükseltirse (ör. uyarı kanalı düştü) istisna `sure_olc`tan
        AYNEN geçer ve süre yine `error` etiketiyle kaydedilir.

        EXE-2026-012 ALETİ (`ATIF_ENABLED`): olay başı birikimler turdan ÖNCE sıfırlanır; tur KAPANDIKTAN sonra
        (`finally` — X ölçülmüş, istisna yolunda da) `_atif_kaydet` olayı seans tamponuna ekler. Ölçülen turun
        DIŞINDADIR; kaydın arızası yakalanır ve adıyla uyarıya düşer — temiz tur temiz döner, özgün istisna AYNEN
        geçer."""
        atif = ATIF_ENABLED
        if atif:
            self._atif_z, self._atif_giris, self._atif_yazim = 0.0, 0, 0
        seans_kapisi0 = self.skipped["session"]
        olcum = gecikme.sure_olc(DONGU_SURESI, "error")
        try:
            with olcum:
                n0 = self.events_handled
                try:
                    self._handle(fields)
                except Exception as e:  # sessiz-yutma DEĞİL: barfeed thread'i korunur, hata kaydedilir ve health'te görünür
                    self.last_error = f"{type(e).__name__}: {e}"[:160]
                    obs.warn("intraday_event_failed", error=self.last_error)
                else:
                    olcum.etiket_degeri = "processed" if self.events_handled != n0 else "skipped"
        finally:
            if atif:
                try:
                    self._atif_kaydet(olcum, self.skipped["session"] != seans_kapisi0)
                except Exception as e:
                    # ALET ARIZASI TURU DÜŞÜREMEZ (inceleme I-1): temiz tur temiz döner, `except` kolunun kendi
                    # istisnası maskelenmez; kayıp adıyla (yalnız TÜR) uyarıya düşer, `last_error`a DOKUNULMAZ.
                    try:
                        obs.warn("exe012_atif_kayit_dustu", tur=type(e).__name__,
                                 detail="EXE-2026-012 tur-içi atıf kaydı düştü — bu olay tampona girmedi; canlı "
                                        "karar turu etkilenmedi")
                    except Exception:  # sessiz-yutma: uyarı kanalının kendisi düştü — alet arızası turun dönüşünü ve özgün istisnasını maskeleyemez
                        pass

    def _atif_kaydet(self, olcum, seans_kapisinda: bool) -> None:
        """EXE-2026-012 ALET (3)/(4) — olay turu KAPANDIKTAN sonra çağrılır: bu çağrının süresi X'e GİRMEZ.

        `processed`/`error` olayı seans tamponuna TEK kayıt olarak eklenir (`ATIF_ALANLARI` sırası): X = ölçüm
        nesnesinin çıkış süresi (histograma işlenen değerin kendisi), Z ve planli giriş/yazım sayıları bu olayın
        birikimleri, ofset = X ölçümünün başladığı an − `_SUREC_SAAT0`. `skipped` KAYDEDİLMEZ. Tampon iki anda
        deftere iner: kayıtlı olayın seansı tampondakinden farklıysa (önce eski seans yazılır) ve seans kapısında
        dönen bir olayda (seans bitti). Tampon `_atif_kilit` altında değişir. Yazım hatası `_atif_bosalt`ta adıyla
        uyarıya düşer; bu fonksiyondan yükselen başka bir arızayı `on_barfeed_event` yakalar ve adıyla uyarıya çevirir
        (tur düşmez)."""
        sonuc = olcum.etiket_degeri
        with self._atif_kilit:
            if sonuc in ("processed", "error") and olcum.sure is not None:
                seans = barclock.session_date()
                if self._atif_olaylar and seans != self._atif_seans:
                    self._atif_bosalt("seans_degisti")
                self._atif_seans = seans
                self._atif_olaylar.append(AtifOlay(
                    outcome=sonuc, x_s=olcum.sure, z_s=self._atif_z, ofset_s=olcum.baslangic - _SUREC_SAAT0,
                    planli_giris=self._atif_giris, planli_yazim=self._atif_yazim))
            elif seans_kapisinda and self._atif_olaylar:
                self._atif_bosalt("seans_kapandi")

    def kapanista_bosalt(self) -> None:
        """İşçinin DÜZGÜN kapanışında seans tamponunu deftere indirir (`bosaltma: kapanis`; EXE-2026-012 ALET (4)).

        Tek çağıranı `api._lifespan` kapanış kolu (`api._kapanis_atif_bosalt`) — YALNIZ bu tüketicinin o yaşam
        döngüsünde `_autostart` tarafından barfeed'e KAYDEDİLDİĞİ durumda. Boş tampon satır yazmaz. Barfeed daemon iş
        parçacığı kapanışta durdurulmaz; takas + yazım `_atif_kilit` altındadır. Seans ortasında bir kapanışın satırı
        KISMİ seanstır (sonraki süreç aynı seansa yeni `surec_baslangic` ile yazar → kart kuralıyla pencere dışı)."""
        self._atif_bosalt("kapanis")

    def _atif_bosalt(self, neden: str) -> None:
        """EXE-2026-012 ALET (4) — seans tamponunu `state/` altındaki `ATIF_DEFTERI`ne TEK satır olarak ekler, boşaltır.

        Satır: kart, şema, seans, süreç başlangıç damgası + pid (seans içi yeniden başlatma tespiti), boşaltma nedeni
        (`ATIF_BOSALTMA`), yazım anı, alan adları, olay sayısı ve olay listesi (yuvarlamasız). BOŞ TAMPON SATIR YAZMAZ.
        Takas + yazım `_atif_kilit` altında (yeniden girişli; kapanış boşaltması başka iş parçacığından gelir).
        YAZIM DÜŞERSE tampon YİNE boşalır ve kayıp ADIYLA uyarıya düşer (seans + olay sayısı): her sonraki kapı-önü
        olayda yeniden deneyen bir tampon hem sınırsız büyür hem uyarı seli üretirdi. Seans defterde görünmez; okuyucu
        onu eksik seans olarak adlandırır. Sıcak yolun `last_error` alanına DOKUNULMAZ (alet arızası karar hattının
        arızası değildir)."""
        with self._atif_kilit:
            olaylar, seans = self._atif_olaylar, self._atif_seans
            if not olaylar:
                return                                    # boş tampon SATIR YAZMAZ (n:0 satırı yok)
            self._atif_olaylar = []
            try:
                store.append_jsonl(ATIF_DEFTERI, {
                    "kart": ATIF_KART, "sema": 1, "seans": seans,
                    "surec_baslangic": _SUREC_BASLANGIC, "pid": os.getpid(), "bosaltma": neden,
                    "yazim_ts": barclock.now().isoformat(), "alanlar": list(ATIF_ALANLARI),
                    "n": len(olaylar), "olaylar": olaylar})
            except Exception as e:
                obs.warn("exe012_defter_yazim_dustu", seans=seans, n=len(olaylar),
                         error=f"{type(e).__name__}: {e}"[:160],
                         detail="EXE-2026-012 tur-içi atıf defteri yazılamadı — bu seansın kaydı KAYIP (hüküm "
                                "penceresinde eksik seans olarak görünür); canlı karar döngüsü etkilenmedi")

    def _handle(self, fields: dict) -> None:
        """Tek bir barfeed olayını işler: seans/HALT kapılarını geçer, ilgi kümesini kurar ve olaydaki
        her ilgili sembolü `_handle_symbol`a verir.

        FAIL-CLOSED: RTH dışıysa (takvim yoksa dahil) ya da kill-switch açıksa hiçbir şey yapmaz,
        yalnız `skipped` sayacını artırır. Olay başına TEK karar anı kullanılır (çapraz-sembol
        tutarlılığı)."""
        as_of = barclock.now()                          # olay başına TEK karar anı (çapraz-sembol tutarlı)
        if not barclock.is_market_open(as_of):          # RTH dışı (mcal yok → fail-closed)
            self.skipped["session"] += 1
            return
        # SABAH TETİK PENCERESİ (EXE-2026-009 + K2): tarama/emir tetiği 13:45'e kaydı — pencere
        # öncesi olaylar karar/gölge/gönderim ÜRETMEZ (fail-closed, RTH kapısıyla aynı desen).
        # Sayaç ayrı: kayma panoda görünür kalır, "seans dışı" ile karışmaz.
        if not barclock.is_entry_window(as_of):
            self.skipped["pencere"] += 1
            return
        if _health.halted():                            # kill-switch
            self.skipped["halt"] += 1
            return
        self.events_handled += 1
        armed = _health.intraday_armed()                # Faz 4a: False beklenir (gözlem)
        pf = store.read_json("portfolio.json", {}) or {}
        # SABAH KANCASI (EXE-009+K2): pencere açıldı — EOD'de pencere yasasıyla ERTELENMİŞ silahlı
        # gönderimler burada tek kapıdan gider. Kancanın hatası gözlem hattını düşüremez.
        try:
            self._pencere_gonderim(pf)
        except Exception as e:
            self.last_error = f"pencere_gonderim: {type(e).__name__}: {e}"[:160]
            obs.warn("pencere_gonderim_dustu", error=self.last_error,
                     detail="sabah gönderim kancası düştü — planlar silahlı kaldı, bir sonraki "
                            "bar olayı yeniden dener (fail-closed retry); son kemer İŞ-2-EOD")
        planned = self._planned(pf)
        interest = self._interest_set(pf, planned)
        self.watched = len(interest)
        self.watched_planned = len(planned)
        for tk in [s.upper() for s in str(fields.get("syms", "")).split(",") if s]:
            if tk in interest:
                self._handle_symbol(tk, as_of, pf, armed, planned)

    def _pencere_gonderim(self, pf: dict) -> None:
        """SABAH GÖNDERİM KANCASI (EXE-2026-009 + K2) — EOD gönderiminin ERTELENMİŞ yarısı.

        YENİ BİR YETKİ DEĞİLDİR (4b'nin INTRADAY_ARM yetkisiyle karıştırılmaz): buradan giden
        planlar EOD kadansının ZATEN silahlayıp göndereceği planlardır — pencere yasası
        (loop.mirror_submit_armed) akşam gönderimini erteledi, kanca aynı gönderimi pencere
        açılınca AYNI TEK KAPIDAN yapar. Emir tipi/boyut/kapılar birebir EOD yoluyla aynı gövdede.

        İDEMPOTENS: koşul (silahlı ∧ dedup-kümesinde-değil) kendini söndürür — başarılı gönderim
        `alpaca_submitted`a yazılır, veto/ret silahlı kümeden düşer; bir sonraki bar olayında koşul
        boş kalır. Arıza dalında (ağ/anahtar) plan silahlı kalır ve sonraki olay yeniden dener
        (4b'nin fail-closed retry deseni). Akşam sermaye nabzından boyutlanır (`eq_kaynak=nabiz`
        makbuzda görünür); kapanış→pencere arasında kitabı yazan kadans yok — taban bayat değil.
        Kanca hiç koşamazsa (akış/Redis ölü) son kemer İŞ-2-EOD geç-gönderimidir (pencere_muaf)."""
        if config.BROKER != "alpaca_paper":
            return                                       # ayna kapalı: kanca sıfır dokunuş (gözlem safiyeti)
        gonderilmis = set(pf.get("alpaca_submitted") or [])
        bekleyen = [p.get("id") for p in (pf.get("armed") or [])
                    if p.get("id") and p.get("id") not in gonderilmis]
        if not bekleyen:
            return
        from . import loop as _loop
        res = _loop.mirror_submit_ve_kalicilastir(source="pencere_gonderim")
        self.pencere_gonderim_n += int(res.get("submitted") or 0)
        obs.log("pencere_gonderim", n_bekleyen=len(bekleyen),
                submitted=res.get("submitted", 0), ok=bool(res.get("ok")),
                dropped=len(res.get("dropped_ids") or []),
                detail="EXE-009+K2 sabah kancası: pencere açıldı, ertelenmiş silahlı gönderimler "
                       "tek kapıdan denendi" + ("" if res.get("ok")
                                                else f" — {str(res.get('detail') or '')[:120]}"))

    def _handle_symbol(self, tk: str, as_of, pf: dict, armed: bool, planned: dict) -> None:
        """Tek sembolün gözlem/karar turu: sıcak durumdan barları okur, yalnız KAPANMIŞ ve taze
        barları alır, plan varsa tetik-geçişini ölçer ve kararı gözlem defterine yazar.

        Tetik kesildiyse iki AYRI kola gider: silahlı plan → gölge kaydı (+ INTRADAY_ARM açıksa
        Faz 4b gerçek gönderim denemesi), silahlanmamış GO/REVIEW planı → ayrı planlı-kol defteri.
        Bar yoksa/bayatsa sembol atlanır, tur DÜŞMEZ; kol hataları yutulmaz, sayaç + uyarı ile
        görünür."""
        raw = hotstate.read_bars(tk, INTRADAY_LOOKBACK)
        if not raw:                                     # Redis down / bar yok → sembol atlanır, tur düşmez
            self.skipped["no_bars"] += 1
            return
        # yalnız KAPANMIŞ barlar + dedupe-by-t (ilk giriş tutulur — u-düzeltmesi/tekrar geri sarmaz)
        seen, bars = set(), []
        for b in barclock.admissible_bars(raw, as_of):
            t = b.get("t")
            if t and t not in seen:
                seen.add(t)
                bars.append(b)
        if not bars:
            return
        last = bars[-1]
        if not barclock.is_fresh(last.get("t"), STALE_TOL_S, as_of):   # bayat kapanmış bar → eski fiyat, atla
            self.skipped["stale"] += 1
            obs.log("intraday_stale_skip", ticker=tk, bar_t=last.get("t"))
            return
        # ÖLÇÜM (A): plan varsa TETİK-GEÇİŞ (eşik kontrolü, strateji girdisi DEĞİL).
        # SIRA ÖNEMLİ: SİLAHLI plan öncelenir — aynı ticker hem silahlı hem plan defterinde olabilir
        # ve silahlı kopya (keşif sondası boyutu, gate_reasons) kararı üreten NÜSHADIR.
        plan = self._armed_plan(tk, pf)
        is_armed_plan = plan is not None
        if plan is None:
            plan = planned.get(tk)
        trigger = fired = None
        if plan is not None:
            try:
                trigger = float(plan.get("entry_trigger"))
                fired = float(last.get("h")) >= trigger    # bu admissible barın HIGH'ı eşiği geçti mi (h yoksa float(None)→yakalanır)
            except (TypeError, ValueError):  # sessiz-yutma: plan biçimsiz entry_trigger; ölçüm None kalır, satır yine audit'lenir, karar bu değere bağlı değil
                trigger = fired = None
        ct = barclock.close_ts(last.get("t"))
        store.append_jsonl(DECISIONS_FILE, {
            "ts": barclock.now().isoformat(), "ticker": tk, "source": "intraday_minute",
            "decision_as_of": as_of.isoformat(), "bar_t": last.get("t"),
            "close_ts": ct.isoformat() if ct else None, "admissible_bars": len(bars),
            # `eod_armed` ANLAMI DEĞİŞMEDİ: "bu plan portfolio.json.armed içinde mi". Yetki farkı
            # satırda etiket olarak yaşar; `plan_source` hangi nüfustan geldiğini söyler.
            "last_close": last.get("c"), "eod_armed": is_armed_plan,
            "plan_source": ("armed" if is_armed_plan else "planned" if plan is not None else None),
            "plan_id": (plan or {}).get("id"),
            "entry_trigger": trigger, "fired": fired, "armed_mode": bool(armed)})
        self.decisions_written += 1
        if plan is not None:
            if is_armed_plan:
                self.decisions_armed += 1
            else:
                self.decisions_planned += 1
        self.last_decision_at = barclock.now().isoformat()
        # GÖLGE (Faz 4b): tetik kesildiyse TAM icra kararını hesapla ve KENDİ defterine yaz.
        # Hata gölgede kalır: ölçüm katmanının arızası gözlem hattını düşüremez (gözlem satırı
        # yukarıda ZATEN yazıldı) — ama sessiz de kalmaz, sayaç + uyarı ile görünür.
        # SİLAHLI KOL — 2026-07-27'den beri aynı, v217'de BAYT DÜZEYİNDE değişmedi. `vs_eod` ve
        # EXE-2026-002'nin gerçek-çift hattı YALNIZ bu kolun defterini okur.
        if fired and is_armed_plan:
            satir = None
            try:
                from . import intraday_shadow
                satir = intraday_shadow.record(plan, last, as_of)
                if satir is not None:
                    self.shadow_written += 1
            except Exception as e:
                self.last_error = f"shadow: {type(e).__name__}: {e}"[:160]
                obs.warn("intraday_shadow_failed", ticker=tk, error=self.last_error)
            # FAZ 4B (2026-08-11, operatör onaylı): bayrak açıksa ve gölge o anın kapılarıyla
            # `would_submit` dediyse GERÇEK gönderim denenir. `satir` gölgenin DÖNÜŞÜDÜR — aynı
            # girdi, aynı kapı ölçümü; gölge satırı yazılmadıysa (dedup: bu seans zaten kayıtlı /
            # biçimsiz girdi / gölge kapalı) 4b de denemez → plan başına seansta EN FAZLA bir
            # gönderim denemesi, gölge-kaydıyla eşlikte. GÖLGE KAYDI KALIR (yukarıda zaten yazıldı).
            if armed:
                try:
                    self._faz4b(plan, satir, tk, pf, as_of)
                except Exception as e:
                    self.last_error = f"faz4b: {type(e).__name__}: {e}"[:160]
                    obs.warn("intraday_4b_failed", ticker=tk, plan_id=(plan or {}).get("id"),
                             error=self.last_error)
        # PLANLI KOL (kart EXE-2026-003, v217): tetiği kesilen ama SİLAHLANMAMIŞ GO/REVIEW planları.
        # NÜFUS 2026-07-30'da BİLEREK daraltılmıştı ve gerekçesi doğruydu: silahlanmamış plan iç
        # EOD defterinde hiç dolmaz, o yüzden gölge satırı `vs_eod`ta `n_unpaired`e düşer ve
        # "gölge-vs-EOD friksiyon farkı" ölçümünü sulandırırdı. O gerekçe KALKMADI, ÇÖZÜLDÜ:
        # yeni kol AYRI BİR DEFTERE yazıyor, yani silahli kolun defteri de onu okuyan iki ölçüm
        # (`vs_eod`, `faz5_cikis`) de bu satırları HİÇ GÖRMÜYOR. Kazanılan şey nüfustur: dakika-
        # hassas icra sorusu, sıfır ek pazar riskiyle çok daha geniş bir örneklemden ölçülebilir.
        #
        # YAZIM NEDEN BURADA: `intraday_shadow` modülünün TEK lağımı `ORDERS_FILE`dır ve bu bir
        # çividir (test_intraday_shadow_v105::test_statik_hicbir_emir_yolu_yok) — silahli kolun
        # bayt-değişmezliğinin bir parçası. Nüfus kararını (hangi plan, hangi kol) zaten bu dosya
        # veriyor; ikinci defter de o kararın yanında yaşıyor. Hesap gölge katmanında, yazım burada.
        # SIRA: önce diske, SONRA tekilleştirme işareti — ters sırada bir yazım hatası planı
        # "yazıldı" sayardı ve o plan o seans bir daha hiç denenmezdi.
        #
        # EXE-2026-012 ALET (2): Z = bu dal gövdesinin süresi (hata dalı dahil), AYNI saatle (`gecikme._saat`);
        # olay başına toplanır (`_atif_z`). `_atif_yazim` satır DİSKE indikten sonra sayılır. Bayrak kapalıyken
        # saat okunmaz, sayaç değişmez.
        elif fired and plan is not None:
            t_atif = gecikme._saat() if ATIF_ENABLED else None
            try:
                from . import intraday_shadow
                satir = intraday_shadow.planli_satir(plan, last, as_of)
                if satir is not None:
                    store.append_jsonl(intraday_shadow.PLANLI_ORDERS_FILE, satir)
                    if t_atif is not None:
                        self._atif_yazim += 1
                    intraday_shadow.planli_yazildi(satir)
                    self.shadow_planli_written += 1
            except Exception as e:
                self.last_error = f"shadow_planli: {type(e).__name__}: {e}"[:160]
                obs.warn("intraday_shadow_planli_failed", ticker=tk, error=self.last_error)
            finally:
                if t_atif is not None:
                    self._atif_giris += 1
                    self._atif_z += gecikme._saat() - t_atif
        # Faz 4b GÖNDERİM BACAĞI ARTIK YUKARIDA (silahlı kol). Eski
        # `intraday_arm_flag_on_but_4b_not_built` uyarısı kaldırıldı: cümlesi ("4b uygulanmadı")
        # artık YANLIŞ olurdu ve yanlış bir uyarı, susan bir uyarıdan tehlikelidir. Bayrak açıkken
        # gönder(eme)me artık sessiz değil — her dal kendi olayını yazar (intraday_4b_*).


    # ---- FAZ 4B — GERÇEK İNTRADAY GÖNDERİM (operatör onayı 2026-08-11) -------------------------
    def _faz4b(self, plan: dict, satir: dict | None, tk: str, pf: dict, as_of) -> None:
        """Tetik kesişimi + INTRADAY_ARM → TEK KAPIDAN gerçek bracket gönderimi.

        KAPI SIRASI (her ret ADIYLA olay defterine düşer — sessizlik yok):
          1. gölge eşliği   : `satir` bu olayda yazılan gölge satırıdır; `would_submit` değilse
                              (kapı blokladı ya da satır hiç yazılmadı) GÖNDERİM DENENMEZ. Gölgenin
                              kapı ölçümü (`intraday_shadow._gates`) üretimin kendi fonksiyonlarıyla
                              o ANDA yeniden değerlendirilir — EOD kapı ailesinin intraday karşılığı.
          2. icra-uygunluk  : (setup ARMED_SETUPS'ta VE kapı GO) YA DA operatör-onaylı plan
                              (loop.operator_onayli). Keşif sondası gibi silahlı-ama-ikisi-de-değil
                              planlar 4b'den GEÇMEZ (onların gönderim anı kendi tetikleyicisinindir).
          3. seans (4G)     : süresi dolmuş plan GÖNDERİLMEZ — planlar tek seans geçerli
                              (operator_onay_ver'in seans yasasıyla aynı kıyas: plan.date, kitabın
                              işlediği son seanstan ESKİYSE seviyeler bayattır).
          4. idempotens (c) : Alpaca tarafında aynı coid'li AÇIK emir ya da sembolde pozisyon varsa
                              atla. Taşıma arızasında FAIL-CLOSED: çift-gönderim DIŞLANAMIYORSA
                              gönderilmez (ölçülemeyen dedup, dedup değildir).
          5. TEK KAPI       : loop.mirror_submit_ve_kalicilastir(sadece_plan_id=…) — HALT + E1-v2
                              yasası + de-risk + `alpaca_submitted` dedup'ı + E2 satırı + kalıcılık
                              EOD yoluyla AYNI gövdeden. EOD döngüsü de aynı dedup kümesini okuduğu
                              için intraday-gönderilmiş planı İKİNCİ kez göndermez.
        Dolmadan kalan 4b girişi EOD bayat-tetik süpürmesinde temizlenir (v210 politikası — DOĞRU
        davranış); koruma bacakları v220/v221 kemerleriyle zaten muaf."""
        if satir is None or satir.get("status") != "would_submit":
            return                                   # gölge satırı sebebi zaten taşıyor (blocked:* / dedup)
        plan_id = plan.get("id")
        from . import loop as _loop, strategy as _strat
        uygun = ((str(plan.get("setup") or "") in _strat.ARMED_SETUPS
                  and str(plan.get("gate_verdict") or "") == "GO")
                 or _loop.operator_onayli(plan))
        if not uygun:
            obs.log("intraday_4b_uygun_degil", ticker=tk, plan_id=plan_id,
                    setup=plan.get("setup"), gate_verdict=plan.get("gate_verdict"),
                    detail="INTRADAY_ARM açık ama plan icra-uygun değil — (setup silahlı VE kapı GO) "
                           "ya da operatör onayı gerekir; yalnız gözlem yazıldı")
            return
        pdate, book_at = str(plan.get("date") or ""), str(pf.get("last_date") or "")
        if not pdate or (book_at and pdate < book_at):
            obs.warn("intraday_4b_suresi_dolmus", ticker=tk, plan_id=plan_id,
                     plan_date=pdate or None, kitap_seansi=book_at or None,
                     detail="süresi dolmuş plan GÖNDERİLMEZ (4G) — planlar tek seans geçerli, "
                            "seviyeleri bayat")
            return
        if config.BROKER != "alpaca_paper":
            obs.log("intraday_4b_ayna_kapali", ticker=tk, plan_id=plan_id, broker=config.BROKER,
                    detail="INTRADAY_ARM açık ama ayna arka ucu kapalı — gönderim yolu yok")
            return
        from .adapters import alpaca
        if not alpaca.paper_available():
            obs.warn("intraday_4b_anahtar_yok", ticker=tk, plan_id=plan_id,
                     detail="ALPACA_PAPER_KEY yok — 4b gönderimi atlandı (yalnız gözlem)")
            return
        # (c) ÇİFT-GÖNDERİM YASAK — Alpaca-tarafı kontrol (kitaptaki `alpaca_submitted` dedup'ı tek
        # kapının içinde AYRICA koşar; burası restart/yarış pencerelerine karşı ikinci kemerdir).
        acik = alpaca.orders(status="open", limit=100, nested=True)
        if not alpaca.transport()["ok"]:
            obs.warn("intraday_4b_dedup_olculemedi", ticker=tk, plan_id=plan_id,
                     detail="açık emir listesi okunamadı — çift-gönderim DIŞLANAMADI, gönderim "
                            "atlandı (fail-closed; bir sonraki tetik olayı yeniden dener)")
            return
        if any(str(o.get("client_order_id") or "") == str(plan_id) for o in (acik or [])):
            obs.log("intraday_4b_dedup_emir", ticker=tk, plan_id=plan_id,
                    detail="aynı coid'li emir Alpaca'da zaten canlı — ikinci gönderim yok (idempotent)")
            return
        apos = alpaca.positions()
        if not alpaca.transport()["ok"]:
            obs.warn("intraday_4b_dedup_olculemedi", ticker=tk, plan_id=plan_id,
                     detail="pozisyon listesi okunamadı — çift-gönderim DIŞLANAMADI, gönderim "
                            "atlandı (fail-closed)")
            return
        if any(str(p.get("symbol") or "").upper() == tk for p in (apos or [])):
            obs.log("intraday_4b_dedup_pozisyon", ticker=tk, plan_id=plan_id,
                    detail="sembolde Alpaca pozisyonu zaten var — ikinci giriş yok (idempotent)")
            return
        res = _loop.mirror_submit_ve_kalicilastir(barclock.session_date(as_of),
                                                  source="intraday_4b", sadece_plan_id=plan_id)
        r0 = (res.get("results") or [{}])[0]
        if res.get("ok") and res.get("submitted"):
            self.submitted_4b += 1
            law = r0.get("law") or {}
            # (e) "would_submit yerine submitted OLAYI": gölge DEFTERİ olduğu gibi kaldı (silahlı
            # kolun şeması/kayıt sayımı kill#3 gereği dokunulmaz); İCRANIN kaydı bu olay + tek
            # kapının E2 satırıdır (motor="ayna", kaynak="intraday_4b").
            obs.log("intraday_4b_submitted", ticker=tk, plan_id=plan_id, coid=plan_id,
                    qty=r0.get("qty"), limit=law.get("limit"), mode=law.get("mode"),
                    tif=law.get("tif"), stop=plan.get("stop"), target=plan.get("profit_target"),
                    detail="Faz 4b: tetik kesişimi + INTRADAY_ARM + icra-uygun plan → GERÇEK "
                           "bracket gönderildi (gölge kaydı ayrıca duruyor)")
        else:
            obs.warn("intraday_4b_gonderilemedi", ticker=tk, plan_id=plan_id,
                     detail=str(res.get("detail") or r0.get("detail") or "?")[:200])


_CONSUMER: IntradayConsumer | None = None


def consumer() -> IntradayConsumer:
    """Süreçteki TEK tüketiciyi döner, yoksa ilk çağrıda kurar (tembel singleton)."""
    global _CONSUMER
    if _CONSUMER is None:
        _CONSUMER = IntradayConsumer()
    return _CONSUMER


def health() -> dict:
    """Pano/API görünürlüğü. Hiç kurulmamışsa ok=None (üçüncü hâl). intraday_decisions.jsonl ÖZETİNİ
    (kararların görünür tüketicisi) DIŞ modül olan api.py okur — 'kendi yazdığını kendi okuyan tüketici
    değildir' yasası (codelaw artifact_graph); bu yüzden özet burada değil, api'de eklenir."""
    if _CONSUMER is None:
        return {"ok": None, "enabled": ENABLED, "armed": _health.intraday_armed(),
                "events_handled": 0, "decisions_written": 0, "watched": 0, "watched_planned": 0,
                "decisions_armed": 0, "decisions_planned": 0, "shadow_written": 0,
                "shadow_planli_written": 0, "submitted_4b": 0, "pencere_gonderim_n": 0,
                "skipped": {}, "last_decision_at": None, "last_error": None, "mode": "observe"}
    c = _CONSUMER
    return {"ok": True, "enabled": ENABLED, "armed": _health.intraday_armed(),
            "events_handled": c.events_handled, "decisions_written": c.decisions_written,
            "watched": c.watched, "watched_planned": c.watched_planned,
            "decisions_armed": c.decisions_armed, "decisions_planned": c.decisions_planned,
            "shadow_written": c.shadow_written,
            "shadow_planli_written": c.shadow_planli_written,
            "submitted_4b": c.submitted_4b, "pencere_gonderim_n": c.pencere_gonderim_n,
            "skipped": dict(c.skipped),
            "last_decision_at": c.last_decision_at, "last_error": c.last_error or None,
            "mode": "arm" if _health.intraday_armed() else "observe"}
