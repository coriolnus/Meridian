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

Look-ahead yasası (bkz. barclock): karar anı `as_of=barclock.now()` olay başına TEK kez; girdi
DEĞERLENDİRİLEN admissible barın OHLC'sinden, ASLA sıcak fiyattan; her satır 3 damgalı →
`as_of >= close_ts` sonradan denetlenebilir. Gözlem-önce gerekçesi: dakikalık bar öğrenmeye/backtest'e
girmez (OOS kanıtı yok) ve strateji GÜNLÜK kalibredir — ham dakikalık barda "karar" kategori
hatasıdır; tetik-geçiş ölçümü değildir (eşik kontrolüdür, gösterge hesaplamaz). Okur: barfeed
olayları, portfolio.json, trade_plans.jsonl; yazar: intraday_decisions.jsonl. Komşular: barclock,
hotstate, intraday_shadow, loop."""
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
        self.skipped = {"session": 0, "halt": 0, "stale": 0, "no_bars": 0}

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
        düşürmez (barfeed zaten ACK'ler; tüketici de kendi içinde savunur — kurt masalı değil, kaydeder)."""
        try:
            self._handle(fields)
        except Exception as e:  # sessiz-yutma DEĞİL: barfeed thread'i korunur, hata kaydedilir ve health'te görünür
            self.last_error = f"{type(e).__name__}: {e}"[:160]
            obs.warn("intraday_event_failed", error=self.last_error)

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
        elif fired and plan is not None:
            try:
                from . import intraday_shadow
                satir = intraday_shadow.planli_satir(plan, last, as_of)
                if satir is not None:
                    store.append_jsonl(intraday_shadow.PLANLI_ORDERS_FILE, satir)
                    intraday_shadow.planli_yazildi(satir)
                    self.shadow_planli_written += 1
            except Exception as e:
                self.last_error = f"shadow_planli: {type(e).__name__}: {e}"[:160]
                obs.warn("intraday_shadow_planli_failed", ticker=tk, error=self.last_error)
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
                "shadow_planli_written": 0, "submitted_4b": 0,
                "skipped": {}, "last_decision_at": None, "last_error": None, "mode": "observe"}
    c = _CONSUMER
    return {"ok": True, "enabled": ENABLED, "armed": _health.intraday_armed(),
            "events_handled": c.events_handled, "decisions_written": c.decisions_written,
            "watched": c.watched, "watched_planned": c.watched_planned,
            "decisions_armed": c.decisions_armed, "decisions_planned": c.decisions_planned,
            "shadow_written": c.shadow_written,
            "shadow_planli_written": c.shadow_planli_written,
            "submitted_4b": c.submitted_4b, "skipped": dict(c.skipped),
            "last_decision_at": c.last_decision_at, "last_error": c.last_error or None,
            "mode": "arm" if _health.intraday_armed() else "observe"}
