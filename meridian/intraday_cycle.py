"""intraday_cycle.py — Faz 4 KAPANMIŞ-BAR TÜKETİCİSİ (GÖZLEM-MODU / Faz 4a).

barfeed her yeni-bar olayında `on_barfeed_event`i uyandırır. GÖZLEM-MODU (SIFIR YETKİ): admissible
(kapanmış) dakikalık barlarda GÜNÜN TÜM PLANLARININ TETİK-GEÇİŞİNİ ölçer ve `intraday_decisions.jsonl`e
3 damgalı (decision_as_of / bar_t / close_ts) yazar. Emir GÖNDERMEZ, CANLI DEFTERİ fill ETMEZ,
portfolio.json'a DOKUNMAZ.

TÜM PLANLAR (sadeleştirme turu, 2026-07-30): gözlem katmanı bugüne dek YALNIZ `portfolio.json.armed`
listesindeki planları izliyordu. Canlıdaki ölçüm sonucu: son EOD turunda 10 plan üretildi, 0'ı
silahlandı, açık pozisyon yok → izlenen ticker sayısı SIFIR, yani aç bir intraday yığını hiçbir kanıt
biriktirmiyordu. Faz 5/6'nın ("dakika-hassas icra EOD'ye ne katardı?") kanıt tabanı silahlanma
kuraklığına rehin kalıyordu. Artık ilgi kümesi GÜNÜN PLAN ÜRETİMİNİN TAMAMIdır (en son EOD turunun
`trade_plans.jsonl` satırları) ∪ açık pozisyonlar ∪ silahlı planlar.

YETKİ FARKI KAYBOLMADI — SATIRDA ETİKET OLARAK DURUR: `eod_armed` alanının anlamı BİREBİR aynıdır
("bu plan portfolio.json.armed içinde mi"), yanına `plan_source` ("armed" / "planned") eklendi.
Silahsız bir planın tetik geçişini ÖLÇMEK, onu silahlandırmak değildir: bu dosya hâlâ hiçbir emir
göndermez ve INTRADAY_ARM bayrağına dokunmaz. 4b gölge kancası da BİLEREK yalnız SİLAHLI planlarda
çalışır (aşağıda) — gölge defterinin nüfusu değişmedi, `vs_eod` eşleştirmesi bozulmadı.

GÖLGE KATMANI (Faz 4b, 2026-07-27): tetik KESİLDİĞİNDE `intraday_shadow.record` çağrılır ve o anın
TAM icra kararı (kapılar + boyutlandırma + emir niyeti) hesaplanıp kendi defterine yazılır. Sıfır
yetki cümlesi gölgeyi de kapsar: gölge boyutlandırmayı KOPYA bir PaperBroker üzerinde simüle eder
ve nesneyi atar — canlı defter fill EDİLMEZ, emir gönderilmez, INTRADAY_ARM bayrağına dokunulmaz.
Kanca bilerek minimaldir: look-ahead mantığı (admissible bar + as_of) burada zaten çözülmüştür ve
gölge onu İKİNCİ kez yazmaz, hazır üçlüyü (plan, bar, as_of) devralır.

NEDEN GÖZLEM-ÖNCE (Faz 4 tasarım sentezi): (1) mrd:bars öğrenmeye/backtest'e girmez → dakikalık kararın
OOS kanıtı YOK; (2) strateji GÜNLÜK-kalibre (252-bar ısınma, haftalık resample, time_stop_days) → ham
dakikalık barda 'karar' KATEGORİ HATASIDIR; (3) otonom intraday silahlanma yeni ve SONUÇLU (arming.py:
'silahlanma otomatik değildir'). Gerçek silahlanma (Faz 4b) YALNIZ operatörün elle açtığı
state/INTRADAY_ARM bayrağı + EOD ile BİREBİR aynı güvenlik kapılarıyla açılır — bu dosyada henüz YOK.

TETİK-GEÇİŞ ÖLÇÜMÜ kategori hatası DEĞİLDİR: dakikalık barın high'ı bir EŞİĞİ (entry_trigger) geçti mi —
strateji GİRDİSİ değil, eşik kontrolü. 'Dakika-hassas icra EOD next-open'a kıyasla ne kazandırırdı'yı
ölçer; gösterge HESAPLAMAZ.

LOOK-AHEAD (bkz. barclock): karar anı `as_of=barclock.now()` olay başına TEK kez; yalnız admissible
(kapanmış) barlar; girdi DEĞERLENDİRİLEN admissible barın OHLC'sinden, ASLA sıcak fiyattan (get_price);
her satır 3 damgalı → `as_of >= close_ts` sonradan denetlenebilir.
"""
from __future__ import annotations
import os

from . import barclock, config, hotstate, store, obs
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


def reset_plans_cache() -> None:
    """Plan önbelleğini boşalt (testler + seans dönüşü) — `intraday_shadow.reset_dedup` deseni.
    Süreç-içi bir önbelleğin testler arası sızması, testin kendi kurmadığı veriyle 'geçmesi' demektir."""
    global _PLANS_CACHE
    _PLANS_CACHE = None


class IntradayConsumer:
    """Tek tüketici (barfeed callback'i). Kendi thread'i YOK — barfeed daemon thread'inde koşar."""

    def __init__(self):
        self.events_handled = 0
        self.decisions_written = 0
        self.last_decision_at: str | None = None
        self.last_error: str = ""
        self.watched = 0
        self.watched_planned = 0        # ilgi kümesinin PLAN nüfusundan geleni (silahlanma kuraklığı görünür olsun)
        # NÜFUS AYRIMI SAYAÇTA (2026-07-30): defterin `fired` toplamı artık SİLAHSIZ planları da
        # içeriyor. Dış tüketici (api) toplamı bölmeden okuduğu için, ayrımı ÜRETİCİ tarafında
        # sayıyoruz — yoksa panodaki "fired" sayısı sessizce anlam değiştirir ve kimse görmez.
        # Bunlar SÜREÇ-İÇİ sayaçlardır (restart'ta sıfırlanır); defter toplamı api'de kalır.
        self.decisions_armed = 0
        self.decisions_planned = 0
        self.shadow_written = 0          # Faz 4b gölge satırı sayacı (kanca çalıştı mı görünür olsun)
        self.skipped = {"session": 0, "halt": 0, "stale": 0, "no_bars": 0}

    # ---- ilgi kümesi: açık pozisyonlar ∪ silahlı ∪ GÜNÜN TÜM PLANLARI (O(≤ plan tavanı)) ----
    def _interest_set(self, pf: dict, planned: dict) -> set:
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
        # DAMGA ARTIK `store.stamp` (WP-H/H9, 2026-07-31): plan defteri SQLite'a taşındığında
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
        düşürmez (barfeed zaten ACK'ler; tüketici de kendi içinde savunur — kurt masalı değil, kaydeder)."""
        try:
            self._handle(fields)
        except Exception as e:  # sessiz-yutma DEĞİL: barfeed thread'i korunur, hata kaydedilir ve health'te görünür
            self.last_error = f"{type(e).__name__}: {e}"[:160]
            obs.warn("intraday_event_failed", error=self.last_error)

    def _handle(self, fields: dict) -> None:
        as_of = barclock.now()                          # olay başına TEK karar anı (çapraz-sembol tutarlı)
        if not barclock.is_market_open(as_of):          # RTH dışı (mcal yok → fail-closed)
            self.skipped["session"] += 1
            return
        if _health.halted():                            # kill-switch
            self.skipped["halt"] += 1
            return
        self.events_handled += 1
        armed = _health.intraday_armed()                # Faz 4a: False beklenir (gözlem)
        pf = store.read_json("portfolio.json", {}) or {}
        planned = self._planned(pf)
        interest = self._interest_set(pf, planned)
        self.watched = len(interest)
        self.watched_planned = len(planned)
        for tk in [s.upper() for s in str(fields.get("syms", "")).split(",") if s]:
            if tk in interest:
                self._handle_symbol(tk, as_of, pf, armed, planned)

    def _handle_symbol(self, tk: str, as_of, pf: dict, armed: bool, planned: dict) -> None:
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
        # NÜFUS BİLEREK DARALTILDI (2026-07-30): gözlem tüm planlara açıldı ama gölge YALNIZ SİLAHLI
        # planda çalışır. Gerekçe ölçümün geçerliliğidir: `intraday_shadow.vs_eod` gölge dolumunu
        # GERÇEK EOD dolumuyla eşleştirir; silahlanmamış bir plan EOD'de hiç dolmaz, o yüzden her
        # satırı `n_unpaired`e düşer ve "gölge-vs-EOD friksiyon farkı" ölçümünü sulandırırdı.
        if fired and is_armed_plan:
            try:
                from . import intraday_shadow
                if intraday_shadow.record(plan, last, as_of) is not None:
                    self.shadow_written += 1
            except Exception as e:
                self.last_error = f"shadow: {type(e).__name__}: {e}"[:160]
                obs.warn("intraday_shadow_failed", ticker=tk, error=self.last_error)
        # Faz 4a: gözlem tamam, KARAR YOK. Bayrak açık olsa bile Faz 4b (gerçek silahlanma) HENÜZ YOK —
        # sessizce silahlamak yerine GÖRÜNÜR bir uyarı (operatör bayrağı erken açtıysa yanlış beklenti kurmasın).
        if armed:
            obs.warn("intraday_arm_flag_on_but_4b_not_built", ticker=tk,
                     detail="INTRADAY_ARM açık ama Faz 4b silahlama bacağı henüz uygulanmadı — yalnız gözlem")


_CONSUMER: IntradayConsumer | None = None


def consumer() -> IntradayConsumer:
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
                "skipped": {}, "last_decision_at": None, "last_error": None, "mode": "observe"}
    c = _CONSUMER
    return {"ok": True, "enabled": ENABLED, "armed": _health.intraday_armed(),
            "events_handled": c.events_handled, "decisions_written": c.decisions_written,
            "watched": c.watched, "watched_planned": c.watched_planned,
            "decisions_armed": c.decisions_armed, "decisions_planned": c.decisions_planned,
            "shadow_written": c.shadow_written, "skipped": dict(c.skipped),
            "last_decision_at": c.last_decision_at, "last_error": c.last_error or None,
            "mode": "arm" if _health.intraday_armed() else "observe"}
