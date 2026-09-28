"""hermes_runtime.py — Hermes yansıma beyninin süreç-içi süpervizörü: bekleme döngüsü,
tetikleyiciler ve pano durum aynası.

Ne yapar: uygulama açılışında (serve.sh `MERIDIAN_AUTOSTART_HERMES=1` verir) bir daemon iş
parçacığı `_run` bekleme döngüsünü koşturur. Sistem sağlıklıyken (HALT yok, veri bayat değil)
canlı rejimin ufku dolunca — `reflection_every` yeni kapanmış işlem VE asgari takvim süresi,
rejim-dilimli katı-VE (`_horizon_ok`) — `hermes.reflect_once` çağrılır. Ufuk dolu değilse
`_bg_ready_regime` birikmiş kanıtlı bir canlı-dışı rejim seçer ve yansıma `background=True`
ile o rejime kapsanmış koşar; o da yoksa ısınma sprinti (`_warmup_sprint`) hiçbir şey ship
etmeden UCB önceliklerini ve sonda önbelleğini ısıtır (süre tavanlı, `_warmup_tavan_dk`).
Operatörün panodaki "düşün" düğmesi yansımayı KOŞMAZ (TSK-233): pano istek dosyası bırakır
(`YANSIMA_ISTEGI_FILE`; kabul kararı `yansima_istegi_karari`), bekleme döngüsü poll'unda alır ve
KENDİ kilidi altında koşar (`_yansima_istegini_isle`). `reflect_now()` süreç-içi/CLI yolu olarak
yaşar. `status()` süreç/ufuk/beyin durumunu döndürür ve state/hermes_status.json'a aynalanır
(panonun Hermes bölümü).

Değişmezler: beyin yalnız önerir — her yansıma `reflect.submit`ten geçer, ship kararını kapı
verir; tek yansıma kilidi (`_reflect_lock`) bekleme döngüsü ile elle tetiklemenin aynı anda
iki yansıma koşmasını engeller — ikisi de artık AYNI süreçte koştuğu için süreç-başı kilit
yeterlidir; öğrenme durumunun (hermes_status.json) TEK yazanı bekleme döngüsünün sürecidir,
pano yalnız okur; arka plan turunun ship yüzeyi seçilen rejimle sınırlıdır
(kanıt kendi rejimini terk etmez — kapsama `reflect_once(background=True)` dalında uygulanır
ve iki dosya birbirini adıyla gösterir); ısınma tavanının aşımı kadans değil anomalidir.

Okur/yazar: trades.jsonl, regime.json, goal.yaml, hermes_yansima_istegi.json (pano yazar) okur;
hermes_status.json yazar, işlediği isteği siler; watchdog'a `hermes_poll` nabzı atar; olayları
events.jsonl'a (obs) düşer."""
from __future__ import annotations
import datetime as dt
import os
import threading

from . import config, store, health, secrets, obs

STATUS_FILE = "hermes_status.json"
# ELLE YANSIMA İSTEĞİ (TSK-233). TEK yazanı pano ucudur (`api.api_hermes_reflect`); okuyanı ve sileni bekleme
# döngüsüdür (`_yansima_istegini_isle`). Durum dosyasından AYRI bir dosya: pano öğrenme durumuna yazmadan "düşün"
# diyebilsin diye — iki süreç aynı dosyayı yazınca birinin boş belleği ötekinin kaydını eziyordu.
YANSIMA_ISTEGI_FILE = "hermes_yansima_istegi.json"
REFLECTION_MIN_DAYS = int(os.environ.get("HERMES_REFLECTION_MIN_DAYS", "30"))   # Phase 3 overfitting horizon
WARMUP_EVERY_POLLS = int(os.environ.get("MERIDIAN_WARMUP_EVERY_POLLS", "12"))   # ısınma sprinti sıklığı (poll)

# ---- ISINMA SPRİNTİ SÜRE TAVANI ----------------------------------------------------------------
# 300 dk = 5 sa, ısınmanın NOMİNAL üst bandı (ölçülmüş aralık 1-5 sa). Tavan bir kısıtlama değil,
# ANOMALİ SINIRI: nominal bandın içinde kalan hiçbir koşum kesilmez; 5 saati aşan koşum tanım gereği
# artık nominal değildir ve döngüyü daha fazla rehin tutmasının hiçbir gerekçesi yoktur.
WARMUP_MAX_MIN_DEFAULT = 300


def _warmup_tavan_dk() -> float:
    """`HERMES_WARMUP_MAX_MIN` (dk) — HER ÇAĞRIDA okunur, modül yüklenirken DEĞİL.

    Neden çağrı anında: bu değer bir operatör kolu (canlıda bir bakım penceresinde daraltılmak
    istenebilir) ve modül-yükleme anında dondurulmuş bir env, süreç yeniden başlatılana kadar
    değişmez — yani kolun çevrildiği ama hiçbir şeyin değişmediği bir yanılsama üretirdi.

    BOZUK DEĞER SESSİZCE 0 OLMAZ: `float("abc")` istisnası yutulup 0'a düşülseydi tavan HER
    ısınmayı anında keserdi ve ısınma kadansı sessizce ölürdü — bekçi bile göremezdi, çünkü nabız
    atılmaya devam ederdi. Bozuk değer ADIYLA uyarılır ve varsayılana dönülür."""
    ham = os.environ.get("HERMES_WARMUP_MAX_MIN")
    if ham is None or not str(ham).strip():
        return float(WARMUP_MAX_MIN_DEFAULT)
    try:
        v = float(ham)
    except (TypeError, ValueError):
        obs.warn("hermes_warmup_max_min_gecersiz", value=str(ham)[:40],
                 fallback_min=WARMUP_MAX_MIN_DEFAULT,
                 detail="HERMES_WARMUP_MAX_MIN sayıya çevrilemedi — varsayılan tavana dönüldü; "
                        "0'a düşmek ısınma kadansını sessizce öldürürdü")
        return float(WARMUP_MAX_MIN_DEFAULT)
    if v <= 0:
        # 0/negatif = "tavan yok" DEĞİL, "her koşumu anında kes" olurdu. Operatör tavanı kaldırmak
        # isterse doğru kol devre dışı bırakmadır (MERIDIAN_WARMUP_SPRINTS=0), tavanı sıfırlamak değil.
        obs.warn("hermes_warmup_max_min_gecersiz", value=str(ham)[:40],
                 fallback_min=WARMUP_MAX_MIN_DEFAULT,
                 detail="HERMES_WARMUP_MAX_MIN sıfır ya da negatif — bu 'tavan yok' değil 'her "
                        "ısınmayı anında kes' anlamına gelirdi; varsayılan tavana dönüldü")
        return float(WARMUP_MAX_MIN_DEFAULT)
    return v


def _bg_ready_regime(trades: list, every: int, live_reg: str | None) -> str | None:
    """REJİM-HEDEFLİ ARKA PLAN YANSIMASI: canlı rejimin ufku dolmadığında boşta beklemek,
    diğer rejimlerin BİRİKMİŞ kanıtını israf etmekti (chop'ta yaşarken trend_up defterinde 80+
    işlem kullanılmadan duruyordu). Ufku DOLU (katı-VE, rejim-dilimli) canlı-dışı rejimlerden,
    son arka-plan yansımasından beri EN ÇOK yeni işlem birikmişi seçilir. Rejim başına taban:
    aynı kanıta ikinci kez yansıma yok — restart'ta da (taban açılışta kalıcı durumdan geri
    yüklenir: `_restored_bg_baselines`, TSK-229).

    GÜVENLİK BEYANI ARTIK KODDA KARŞILIĞI OLAN BİR CÜMLE. Beyan: "ship yalnız
    params_by_regime[o rejim]'i değiştirir — canlı davranış rejim dönene dek değişmez ve o güne
    kadar kapı+defterde denetlenmiştir." Bu cümle bir süre KARŞILIKSIZDI: bu fonksiyon
    `trend_up` döndürdüğünde `reflect_once` içindeki `!= "trend_up"` istisnası aramayı GLOBAL
    koşturuyor, `versioning.bump` '@' göremediği için düz `params`a yazıyordu — yani chop canlıyken
    chop davranışı, chop'un hiç sertifika vermediği kanıtla anında değişiyordu. UYGULAMA YERİ BU
    FONKSİYON DEĞİL: seçim burada, KAPSAMA `hermes.reflect_once(..., background=True)` dalındadır
    (aşağıdaki çağrı bayrağı taşır). Beyanı taşıyan yorumla onu uygulayan kodun ayrı dosyalarda
    olması bu kusurun kök nedeniydi; bu yüzden ikisi de birbirini ADIYLA gösterir."""
    baselines = _state.get("bg_reflect_by_regime") or {}
    best, best_n = None, 0
    for r in config.VALID_REGIMES:
        if r == live_reg:
            continue
        # K1 DURAKLATMA (EDG-2026-048 NO-GO, 2026-08-23): duraklatılmış rejime bg SERTİFİKASI
        # VERİLMEZ — verilseydi tur hermes gövdesinde atlanacaktı (bg_reflection_skipped_paused_
        # regime, ikinci savunma hattı); slotu burada hiç yakmamak, diğer rejimlerin birikmiş
        # kanıtına yol açar. Canlanma yalnız yeni kartla (config.URETIMI_DURAKLATILAN_REJIMLER).
        if r in config.URETIMI_DURAKLATILAN_REJIMLER:
            continue
        last_r = int(baselines.get(r, 0))
        if not _horizon_ok(trades, last_r, regime=r, min_trades=every):
            continue
        n_new = sum(1 for t in trades[last_r:] if str(t.get("regime")) == r)
        if n_new > best_n:
            best, best_n = r, n_new
    return best


def _red_neden_dagilimi(iz: list) -> dict:
    """Geçmeyen sondaların red gerekçelerini KOVALARA toplar → {kova: sayı}.

    NEDEN KOVA, NEDEN HAM METİN DEĞİL: `_gate_why` sayısal ayrıntı taşıyan bir cümle üretir
    ("skor marjı: -0.004 < 0.010"). Ham metni saymak her sonda için AYRI satır üretir ve
    "hangi kapı dalı baskın" sorusu cevapsız kalır — oysa `cleared=0` teşhisinin tek sorusu
    budur. Kova = cümlenin iki nokta ÖNCESİ, yani dalın adı.

    Yalnız `passes=False` satırlar sayılır: geçen sondanın gerekçesi yoktur."""
    import collections
    say = collections.Counter()
    for r in iz or []:
        if r.get("passes"):
            continue
        w = r.get("why")
        if not w:
            say["gerekçe ÖLÇÜLEMEDİ (iz `why` taşımıyor)"] += 1     # UYDURMA YASAĞI: boşluk gizlenmez
            continue
        say[str(w).split(":", 1)[0].strip()] += 1
    return dict(say)


def _warmup_sprint() -> None:
    """Boş-döngü ısınması: coordinate_descent_search'i SHIP ETMEDEN koştur — yalnız UCB
    önceliklerini + probe cache'ini ısıtmak için. Nothing ships (submit çağrılmaz) VE artık bu
    beyan DEFTER tarafında da geçerli: `record_session=False` ile resmî aşınma/doğrulama kaydı
    düşmez. En iyi probe'un özeti hermes_status'a yazılır (görünürlük). Ağ/veri hatası sessizce
    yutulur — ısınma asla döngüyü kırmaz.

    İKİ KUSUR BİRDEN KAPANIR, İKİSİ DE AYNI KÖKTEN:

      (1) POLL AÇLIĞI. Bu fonksiyon hermes bekleme döngüsünün KENDİ iş parçacığında koşar ve nominal
          süresi 1-5 saattir. O süre boyunca `_run` döngüsü bir sonraki tura dönemez, yani
          `watchdog.beat("hermes_poll")` ATILMAZ. Bekçinin `hermes_poll` penceresi 30 DAKİKAdır →
          ısınma her koştuğunda MECHANISM_STALE üretilir. Bu SAHTE bir alarmdır: mekanizma ölü değil,
          MEŞGULdür. Ve sahte alarmın maliyeti gerçek alarmdan yüksektir — operatörü alarm okumamaya
          eğitir. Çözüm: nabız artık sondadan sondaya, ısınmanın İÇİNDEN atılıyor. `hermes_poll`
          nabzının ısınma tarafından atıldığı bu yoruma yazılıdır: nabız "poll döngüsü turladı"
          demez, "hermes ipliği CANLI ve İLERLİYOR" der — bekçinin gerçekte sorduğu soru budur.

      (2) İPTAL EDİLEMEZLİK. 8 saati aşan bir ısınmada bekçinin elinde ALARM'dan başka araç yoktu.
          Artık aramanın kendisi bir süre tavanı taşıyor (`max_minutes`) ve tavana takılırsa KİBARCA
          kesiliyor — biten sondalarla dönüyor, kesinti damgalanıyor. Bekçi eşiği 8 saatte KALIR ve
          bu bilinçlidir: tavan 5 saat olduğuna göre 8 saatlik bir sessizlik artık "uzun sürdü"
          değil "tavan çalışmadı" demektir — yani eşik nihayet GERÇEK bir anomali ölçer.
    """
    try:
        from . import hermes, reflect, dataset
        from . import watchdog as _wd8
        # ISINMA DA KALP ATAR (TSK-233 tur 2): ısınma döngünün KENDİ ipliğinde 1-5 sa sürer ve o süre boyunca poll
        # dönmez. Kalp yalnız poll başında atılsaydı 15 dk'dan (KALP_PAY × poll) uzun her NORMAL ısınmada pano birimi
        # ölü sanır, operatörün "düşün" isteğini reddederdi. Başlangıçta işaret + kalp diske iner (pano ilk saniyeden
        # "ısınma sürüyor" diyebilsin); ilerledikçe `_nabiz` → `_kalp_tazele` kalbi taze tutar. İşaret CANLILIK
        # DEĞİLDİR — yalnız mesajın içeriğidir; canlılığın tek ölçüsü kalptir (`_dongu_canliligi`).
        _tavan = _warmup_tavan_dk()
        _state["isinma_suruyor"] = {"basladi": _now(), "tavan_dk": _tavan}
        _kalp_vur()
        bars, index = dataset.load()
        # önce sıradaki muhtemel yansımaların incumbent'ları (global + canlı + ufku dolu arka plan
        # rejimi) — yansıma anında kapı beklemesin; sonra sonda ısınması.
        def _nabiz(*_a, **_k):
            """İKİ nabız: ısınmanın kendi kadansı + poll ipliğinin canlılığı.

            v302'de TANIM YUKARI TAŞINDI ve bu bir biçim düzeltmesi DEĞİL, kusurun kendisiydi:
            eskiden `_nabiz` `reflect.prefill_incumbents` çağrısından SONRA tanımlanıyordu, yani
            o fazda nabız atmak YAPISAL olarak imkânsızdı. `prefill_incumbents` havuz bekleyişi
            tek blokta HAVUZ_ATALET_SN kadar sürebilir; o gün tavan 1800 sn'ydi ve bekçi penceresi
            de 1800 sn olduğundan bayat-geçiş garantiydi. (v318 tavanı ölçülen iş süresinden
            türetip ~9555 sn'ye çıkardı — eşitlik kalktı ama bu nabzı GEREKSİZ kılmaz, tam tersine
            zorunlu kılar: bekleyiş artık bekçi penceresinin kat kat üstünde sürebiliyor.) CANLI KANIT: 2026-08-24 alarmı 01:59:48'de düştü,
            `arama_havuzu_zaman_asimi biten=0` olayı 02:00:08'de — sonda döngüsü hiç başlamamıştı.

            İMZA `*_a, **_k`: aynı geri-çağırma İKİ dikişe birden bağlanıyor — aramanın
            `on_probe(i, total, ...)` dikişi ve havuz/sıralı bacakların argümansız `canlilik()`
            dikişi. Tek gövde, tek anlam: "bu iplik canlı ve ilerliyor".
            Nabız yazımı `store.write_json`dur (birkaç ms); en sık HAVUZ_NABIZ_SN'de bir atılır."""
            _wd8.beat("warmup_sprint")     # ısınmanın KENDİ kadansı ilerliyor
            _wd8.beat("hermes_poll")       # poll ipliği MEŞGUL ama CANLI — sahte alarm burada biter
            _kalp_tazele()                 # panonun canlılık ölçüsü de (kalp) aynı ilerlemeden beslenir (TSK-233)

        try:
            trades = store.read_jsonl("trades.jsonl")
            every = int((config.goal().get("reflection_every") or 5))
            live = store.read_json("regime.json", {}).get("regime")
            live = live if live in config.VALID_REGIMES else None
            bg = _bg_ready_regime(trades, every, live)
            # DUR YÜKLEMİ (TSK-246): `_stop.is_set` iki uzun çağrıya da ENJEKTE edilir — `reflect` bu
            # modülü tanımaz (import grafiği değişmez). SIGTERM → `learn_run._isaret` → `stop()` →
            # bayrak; uzun hesap onu kontrol noktalarında okuyup iner (ölçülen gecikme: v586).
            reflect.prefill_incumbents(bars, index, [None, live, bg], canlilik=_nabiz, durdurma=_stop.is_set)
        except Exception as e:
            obs.warn("incumbent_prefill_failed", error=f"{type(e).__name__}: {e}")
        # `record_session=False`: "Nothing ships" beyanı artık DEFTER tarafında da
        # doğru. Isınma her 12 poll'da bir koşar ve sonda başına resmî kayıt düşerken tek bir gecede
        # aşınma sayacını yüzlerle besliyordu (`EROSION_QUERY_LIMIT=20` ilk ısınma gecesinde aşılıyor,
        # +0.01 ek marj ömür boyu açık kalıyordu) — hiçbir şey ship edemeyen bir turun kapıyı KALICI
        # olarak sıkması. Sıfır kayıt bir muafiyet değil, beyanın uygulanması: ship yetkisi olmayan
        # tur resmî soru sormaz.
        # BÜTÇE ARTIK SABİT DEĞİL: `cleared: 0` ile biten her koşum bir sonrakini
        # bir kademe genişletir, ilk clearing tabana döndürür, süre tavanına takılan koşum duvarı
        # ÖLÇER. Yasa ve durum TEK YERDE (`hermes.warmup_budget`) — burada sayı yok, çağrı var.
        _wb = hermes.warmup_budget()
        res = reflect.coordinate_descent_search(bars, index, budget=int(_wb["budget"]),
                                                k_max=int(_wb["k_max"]), max_minutes=_tavan,
                                                on_probe=_nabiz, canlilik=_nabiz,
                                                durdurma=_stop.is_set,
                                                record_session=False)
        _wd8.beat("warmup_sprint")         # sonda HİÇ koşmadıysa da ısınma turladı: kadans nabzı düşmez
        _wd8.beat("hermes_poll")
        # DURDURMA BİR ÖLÇÜM DEĞİLDİR (TSK-246): `warmup_budget_feedback` `kesildi`yi SÜRE TAVANI sayar —
        # çarpanı yarıya indirir ve seviyeyi DUVAR olarak çakar. Süreç iniyor diye kesilen bir koşum
        # "bu genişlik pencereye sığmadı" demez; merdivene işlenseydi her dağıtım sahte bir duvar çakardı.
        _durduruldu = res.get("sebep") == reflect.DURDURMA_SEBEBI
        if not _durduruldu:
            try:
                hermes.warmup_budget_feedback(res)   # sonuç merdivene işlenir (bir sonraki koşumun kolu)
            except Exception as e:
                # YASA 4: merdiven yazımı düşerse bütçe SESSİZCE tabanda donar ve "kural koşuyor"
                # yanılsaması sürer. Ama koşumun KENDİSİ başarılıydı — kaydını bir defter hatasına
                # kurban etmek, ölçülmüş bir sonucu telemetri arızasıyla silmek olurdu.
                obs.warn("warmup_budget_feedback_failed", error=f"{type(e).__name__}: {e}",
                         detail="ısınma bütçe merdiveni güncellenemedi — sonraki koşum aynı bütçeyle "
                                "koşar (oto-ölçekleme bu tur ilerlemedi)")
        _state["last_warmup"] = {"at": _now(), "evaluated": res.get("evaluated"),
                                 "cleared": res.get("cleared"),
                                 "best": (res.get("best") or {}).get("variable"),
                                 # KESİNTİ PANODA GÖRÜNÜR: "3 sonda değerlendi" ile "10 sondanın
                                 # 3'ü değerlendi, kalanı kesildi" aynı karta yazılamaz.
                                 "kesildi": bool(res.get("kesildi")),
                                 "sebep": res.get("sebep"), "tavan_dk": _tavan,
                                 "kalan_sonda": res.get("kalan_sonda"),
                                 # MERDİVENİN HÂLİ PANODA GÖRÜNÜR: "40 sonda değerlendi" ile
                                 # "taban×4 bütçesiyle 40 sonda değerlendi" aynı şey değildir —
                                 # ikincisi kuralın çalıştığını da söyler (YASA 6: okuyucu /api/hermes).
                                 "butce": _wb["budget"], "butce_carpani": _wb["carpan"],
                                 "k_max": _wb["k_max"], "butce_formulu": _wb["formul"]}
        from . import obs
        # GEREKÇE DAĞILIMI LOG'A GİRER: `cleared=0` tek başına teşhis edilemez bir sayıdır.
        _nd = _red_neden_dagilimi(res.get("trace") or [])
        obs.log("warmup_sprint", evaluated=res.get("evaluated"), cleared=res.get("cleared"),
                neden_dagilim=_nd,
                best=(res.get("best") or {}).get("variable"),
                # `durduruldu`: kesinti süre tavanı DEĞİL durdurma isteğiydi → merdivene işlenmedi (TSK-246).
                # Okuyucu: olay defteri (`ops/olay_sorgu.py`) — "bu koşum neden merdiveni oynatmadı?"
                kesildi=bool(res.get("kesildi")), durduruldu=_durduruldu, tavan_dk=_tavan,
                kalan_sonda=res.get("kalan_sonda"),
                butce=_wb["budget"], butce_carpani=_wb["carpan"], k_max=_wb["k_max"])
    except Exception as e:
        _state["last_warmup"] = {"at": _now(), "error": type(e).__name__}
    finally:
        _state.pop("isinma_suruyor", None)   # ısınma bitti/düştü: işaret kalkar (poll sonu `_persist`i diske taşır)

_lock = threading.Lock()            # guards thread start/stop
_reflect_lock = threading.Lock()    # guarantees only ONE reflection runs at a time
_thread: threading.Thread | None = None
_stop = threading.Event()
_state: dict = {"reflections": 0, "last_reflection": None, "last_poll": None,
                "last_result": None, "last_variable": None, "started_at": None, "poll_seconds": None,
                # trade-count baseline at the LAST live or manual reflection — the standby loop's trigger AND
                # the honest "next auto-reflection" countdown both derive from it. It used to be a local in
                # _run(), so the dashboard invented its own (wrong) formula from total closed trades.
                # Background reflections do NOT move it (TSK-227 — they carry `bg_reflect_by_regime`).
                "last_reflect_at": None}


def _simdi() -> dt.datetime:
    """Şimdiki UTC anı — bu modülün TEK saati: damgalar (`_now`) ve yaş ölçümleri (`_kalp_canliligi`, `_yas_s`) aynı
    saatten okur; iki saat olsaydı damga ile yaşı ayrı saatlerden ölçülen bir kalp sessizce "gelecekte" kalabilirdi."""
    return dt.datetime.now(dt.timezone.utc)


def _now() -> str:
    """Şimdiki UTC zamanı, saniye çözünürlüklü ISO dizgesi olarak (tüm damgaların tek kaynağı)."""
    return _simdi().isoformat(timespec="seconds")


def _brain() -> str:
    """Aktif beyin: HERMES_BRAIN_ORDER zincirinde anahtarı hazır VE soğumada olmayan ilk sağlayıcı
    (claude/nous/gemini), hiçbiri yoksa deterministik. Görüntü katmanı da bu tek kaynaktan okur.
    Soğuma farkının kökeni ölçülmüş bir vaka: gemini üç gün 429 yerken pano hâlâ bir LLM beyni gösteriyordu, yani
    deterministik yola düşüş LLM görüşü gibi okunuyordu — bozunmanın gizlenmesi tam olarak budur."""
    try:
        from . import hermes
        return hermes.active_brain()
    except Exception:  # sessiz-yutma: isteğe bağlı bağımlılık yok — yokluğu kusur değil yapılandırma; içe aktarma denemesinin kendisi zaten cevaptır
        return "deterministic"


def _brain_availability() -> dict:
    """Sağlayıcı başına {credentials, ready, cooling_s, reason} — bozunma NEDENİ panoda okunur olsun.
    İSTİSNA `{}` DEĞİL `{"error": ...}` DÖNER — gerekçesi için bkz. `_brain_chain`."""
    try:
        from . import hermes
        return hermes.brain_availability()
    except Exception as e:
        return {"error": type(e).__name__}


def _brain_chain() -> dict:
    """Zincirin YEDEKLİLİĞİ hakkında yalnız ölçülen olgular (bkz. hermes.brain_chain_facts):
    ad saymak kota saymak değildir. Bağımsız uç sayısı burada da ÜRETİLMEZ.

    İSTİSNA ARTIK YUTULMUYOR: boş sözlük dönmek "hermes hiç koşmadı" (taze kurulum)
    ile "ÖLÇÜM ARIZALANDI" (hermes import'u/çağrısı düştü) arasındaki farkı siliyordu — ve bekçi
    tarafındaki `if _ch:` kapısı ikisini birden düşürüyordu. Yani yedeklilik denetiminin KENDİSİ
    bozulduğunda pano hiçbir şey söylemiyor, kör noktayı sessizlik gibi gösteriyordu. Hata SINIFI
    ölçülen bir olgudur; `{}` yerine onu döndürmek uydurma değil kayıttır."""
    try:
        from . import hermes
        return hermes.brain_chain_facts()
    except Exception as e:
        return {"error": type(e).__name__}


def _horizon_ok(trades: list, last_at: int, min_days: int = REFLECTION_MIN_DAYS,
                regime: str | None = None, min_trades: int = 1) -> bool:
    """Phase 3 time-clustering guardrail — STRICT AND: the trades accrued SINCE the last reflection must
    number >= min_trades AND span >= min_days of MARKET time (measured from trade timestamps, so it holds
    under fast paper-advance too). With `regime`, both conditions are measured WITHIN that regime's trades
    only — a reflection that would tune the live regime must be backed by enough time IN that regime.
    (The old '>=2 distinct regimes' OR-branch is deliberately GONE: it let N trades clustered in a few
    days bypass the calendar floor entirely — the exact overfit this guardrail exists to prevent.)"""
    new = trades[last_at:]
    if regime:
        new = [t for t in new if str(t.get("regime")) == str(regime)]
    if len(new) < max(1, int(min_trades)):
        return False
    ds = [str(t.get("ts_close") or t.get("ts_open") or "")[:10] for t in new]
    ds = [d for d in ds if d]
    if len(ds) < 2:
        return False
    try:
        return (dt.date.fromisoformat(max(ds)) - dt.date.fromisoformat(min(ds))).days >= min_days
    except Exception:  # sessiz-yutma: biçimsiz/eksik tek alan; yalnız bu değer düşer, satır başına uyarı asıl sinyali log seline gömerdi
        return False


def _horizon_progress(trades: list, last_at: int, regime: str | None,
                      min_trades: int, min_days: int = REFLECTION_MIN_DAYS) -> dict:
    """Observable horizon state for the dashboard: how far along BOTH strict-AND conditions are
    (trades accrued + calendar span, within `regime` when given). Keeps the countdown honest — a
    count-only 'hazır' while the horizon still blocks was exactly the dishonest-status bug class."""
    new = trades[last_at:]
    if regime:
        new = [t for t in new if str(t.get("regime")) == str(regime)]
    ds = sorted(d for d in (str(t.get("ts_close") or t.get("ts_open") or "")[:10] for t in new) if d)
    span = 0
    if len(ds) >= 2:
        try:
            span = (dt.date.fromisoformat(ds[-1]) - dt.date.fromisoformat(ds[0])).days
        except Exception:  # sessiz-yutma: biçimsiz/eksik tek alan; yalnız bu değer düşer, satır başına uyarı asıl sinyali log seline gömerdi
            span = 0
    return {"regime": regime, "trades": len(new), "trades_needed": max(1, int(min_trades)),
            "span_days": span, "min_days": min_days,
            "ready": len(new) >= max(1, int(min_trades)) and span >= min_days}


def _yansima_vadesi(trades: list, last_at: int, every: int, live_reg: str | None) -> bool:
    """YANSIMA VADESİNİN TEK TANIMI: son yansımadan beri ≥ `every` kapanış VE canlı rejimde katı-VE ufuk
    (`_horizon_ok`). Bekleme döngüsü (`_run`) otomatik yansımayı BUNUNLA ateşler; `yansima_kapisi`
    (pano geri sayımı + bekçinin öğrenme-canlılık alarmı, TSK-204) "vade doldu"yu BUNUNLA söyler.
    Döngüde satır-içi bir kopya kalsaydı iki tanım sessizce ayrışabilirdi (tek-kaynak yasası)."""
    return (len(trades) - int(last_at) >= int(every)
            and _horizon_ok(trades, int(last_at), regime=live_reg, min_trades=every))


def _durum_tabani() -> tuple[bool, dict, dict]:
    """`(icerde, disk, taban)` — `status()` ile `yansima_kapisi()`nin ORTAK durum tabanı.

    SÜREÇ-İÇİ Mİ? (Ö-50) Döngü kendi systemd biriminde koşuyorsa BU süreçte iplik YOKTUR ve
    `_state` boş varsayılanlarla durur — o hâlde yetkili kaynak DİSKtir (`STATUS_FILE`)."""
    icerde = bool(_thread and _thread.is_alive())
    disk = (store.read_json(STATUS_FILE, {}) or {}) if not icerde else {}
    taban = {**_state, **disk} if not icerde else dict(_state)
    return icerde, disk, taban


def yansima_kapisi(taban: dict | None = None) -> dict:
    """YANSIMA KAPISININ GÖZLEMLENEBİLİR HÂLİ — TEK HESAP YERİ. Okuyucular: `status()` (pano geri
    sayımı, /api/hermes) ve `watchdog._learning_liveness` (ÖĞRENME DURDU alarmının (A) ayağı, TSK-204).
    İkisi de buradan okur; bekçi kapıyı KENDİSİ hesaplamaz (ikinci kapı uygulaması yok).

    `vade_doldu` = `_yansima_vadesi` (döngünün ateşleme yüklemi). `vade_ts` = vadeyi DOLDURAN kapanışın
    damgası (`ts_close`, yoksa `ts_open`): tabandan sonraki önekler aynı yüklemle taranır ve ilk doğru
    olan önekin son kapanışı alınır — yüklem öneklerde tekdüzedir (sayım da takvim açıklığı da yalnız
    artar). Ölçülemezse `vade_ts` None ve `vade_ts_neden` NEDENİ söyler (uydurma yok). Canlı rejim
    ŞİMDİKİ rejimdir: vade, döngünün BU poll'da soracağı soruya göre ölçülür.
    `taban` verilmezse süreç-içi/disk ayrımı `status()` ile AYNI kuralla (`_durum_tabani`) kurulur."""
    if taban is None:
        taban = _durum_tabani()[2]
    every = int(config.goal().get("reflection_every", 5))
    trades = store.read_jsonl("trades.jsonl")
    closed = len(trades)
    base = taban.get("last_reflect_at")
    # Honest countdown: how many NEW trades must close before the standby loop reflects again. The old UI
    # formula was `every - closed_trades`, which is 0 for any book with more trades than `every` — i.e. it
    # always read "hazır" (ready), which was simply false. Computed here so there is ONE source of truth.
    since = max(0, closed - int(base)) if base is not None else 0
    # Horizon computed FRESH on every read (not only in the standby loop's healthy branch), so the
    # dashboard shows the real gate even during HALT/stale and before the first poll.
    live_reg = store.read_json("regime.json", {}).get("regime")
    live_reg = live_reg if live_reg in config.VALID_REGIMES else None
    # TABAN YOKSA (döngü bu kurulumda hiç koşmamış): `_restored_baseline` ilk açılışta tabanı defter
    # uzunluğuna kurar — birikmiş kapanışlar üzerine yansıma YOK. Vade bu yüzden "dolmadı"dır; uydurma değil türetme.
    last_at = int(base) if base is not None else closed
    horizon = _horizon_progress(trades, last_at, live_reg, every)
    vade = _yansima_vadesi(trades, last_at, every, live_reg)
    vade_ts, vade_neden = None, None
    if vade:
        for k in range(max(last_at, 0) + 1, closed + 1):
            if _yansima_vadesi(trades[:k], last_at, every, live_reg):
                son = trades[k - 1]
                vade_ts = son.get("ts_close") or son.get("ts_open") or None
                if vade_ts is None:
                    vade_neden = (f"vadeyi dolduran kapanış (defter sırası {k}) ts_close/ts_open "
                                  f"taşımıyor — vadenin başladığı an ÖLÇÜLEMEDİ")
                break
    return {"reflection_every": every, "closed_trades": closed, "last_reflect_at": base,
            "trades_since_last_reflection": since, "trades_until_next": max(0, every - since),
            "horizon": horizon, "horizon_ready": horizon["ready"], "horizon_regime": live_reg,
            "vade_doldu": bool(vade), "vade_ts": vade_ts, "vade_ts_neden": vade_neden,
            "son_isinma": taban.get("last_warmup")}


def _persist() -> None:
    """Bellekteki `_state`i beyin/model/zincir olgularıyla birlikte STATUS_FILE'a yazar.

    DÜRÜST BOZUNMA: deterministik yola düşülmüşse `brain_degraded=True` açıkça kaydedilir —
    LLM'siz koşum LLM görüşü gibi okunamaz."""
    try:
        from . import hermes
        model = hermes.active_model()
    except Exception:  # sessiz-yutma: isteğe bağlı bağımlılık yok — yokluğu kusur değil yapılandırma; içe aktarma denemesinin kendisi zaten cevaptır
        model = None
    brain = _brain()
    store.write_json(STATUS_FILE, {**_state, "brain": brain, "model": model, "updated": _now(),
                                   "brain_availability": _brain_availability(),
                                   "brain_chain": _brain_chain(),
                                   # DÜRÜST BOZUNMA: deterministik yola düştüysek bu dosyada AÇIKÇA yazar.
                                   "brain_degraded": brain == "deterministic"})


def _record(res: dict, *, arka_plan: bool) -> bool:
    """Biten bir yansımanın sonucunu `_state`e işler (sayaç, zaman damgası, durum, değişken). Dönüş: sonuç
    İŞLENDİ mi — durdurmayla KESİLEN tur işlenmez (False; aşağıdaki TSK-248 paragrafı).

    CANLI ve ELLE yansımada (`arka_plan=False`) geri sayım tabanını (`last_reflect_at`) da güncel
    defter uzunluğuna çeker: elle tetiklenen yansıma da bekleme döngüsünün tetiğini ileri iter, aynı
    işlemler üzerinde tekrarlanmaz.

    ARKA PLAN yansıması (`arka_plan=True`) `last_reflect_at`a DOKUNMAZ (TSK-227): o alan canlı
    rejimin vade yükleminin (`_yansima_vadesi`) tek zaman tabanı ve bekçinin öğrenme-canlılık
    alarmının (A) ayağının (`yansima_kapisi`) tabanıdır. Taşısaydı, canlı sayaç `reflection_every`e
    ulaşmadan araya giren her arka plan turu sayacı sıfırlardı → canlı yansıma hiç ateşlemez (livelock),
    (A) vadeyi hiç görmez. Arka plan turunun KENDİ tabanı çağrı yerinde taşınır
    (`bg_reflect_by_regime[rejim]`, `_bg_ready_regime` okur). Parametre ZORUNLU ve yalnız-ADLA: yeni
    bir çağrı yeri türünü beyan etmeden yazılamaz — varsayılan olsaydı beyansız bir arka plan yolu
    canlı tabanı yine sessizce taşırdı (kusurun sınıfı).

    KESİLEN TUR SAYILMAZ (TSK-248, operatör kararı A, 2026-09-28): sonuç `reflect.DURDURULDU_STATUS`
    taşıyorsa (öğrenme süreci durdurulurken tur `_gate_eval`den önce kesildi — hiçbir deftere yazılmadı)
    HİÇBİR alan oynamaz — sayaç, damga, sonuç, değişken, taban; beyanlı olay düşer, False döner. Ya hep ya
    hiç: kısmi güncelleme yok, durum dosyası turdan ÖNCEKİ hâliyle tutarlı kalır. Taban ilerleseydi yeniden
    başlayan süreç aynı kanıtı YOK sayardı; sayaç ilerleseydi pano hiç olmamış bir yansıma gösterirdi. Süreç
    yeniden başlayınca taban diskten geri yüklenir (`_restored_baseline`) ve aynı kanıtla yeniden denenir —
    sonsuz tekrar yok, tekrar yalnız yeniden başlatmada olur.
    NEDEN BURADA (çağrı yerinde "çağırma" değil): üç çağrı yeri de (canlı · arka plan · elle) bu fonksiyondan
    geçer — kural TEK yerde yaşar, yarın eklenecek bir çağrı yeri onu unutamaz; TSK-227'nin çağrı-yeri beyan
    çivisi (`_record(hermes.reflect_once(...), arka_plan=...)` biçimi, v560 test_5) de aynen korunur. Arka plan
    rejim tabanı çağrı yerinde taşındığı için çağıran dönüşe bakar."""
    if _tur_kesildi(res, arka_plan=arka_plan):
        return False
    _state["reflections"] += 1
    _state["last_reflection"] = _now()
    _state["last_result"] = res.get("status")
    _state["last_variable"] = (res.get("hypothesis") or {}).get("variable")
    if arka_plan:
        return True
    # reset the countdown baseline. A MANUAL reflection must push the standby trigger out too — otherwise
    # the loop would immediately re-reflect on the very same trades.
    _state["last_reflect_at"] = len(store.read_jsonl("trades.jsonl"))
    return True


def _tur_kesildi(res, *, arka_plan: bool) -> bool:
    """Yansıma sonucu durdurma isteğiyle KESİLMİŞ mi (TSK-248)? Kesildiyse beyanlı olayı düşürür ve True döner.

    Okuyucu: olay defteri (`ops/olay_sorgu.py`, journal) — "durdurmada hangi tur yarıda kaldı, taban neydi?"
    Kesintinin NEREDE olduğunu (`asama`) sonuç taşır; reflect katmanı kendi olayını ayrıca düşürür
    (`submit_durdurma_istegiyle_kesildi` / `search_durdurma_istegiyle_kesildi`)."""
    from . import reflect
    if not (isinstance(res, dict) and res.get("status") == reflect.DURDURULDU_STATUS):
        return False
    obs.log("yansima_turu_sayilmadi", arka_plan=bool(arka_plan), asama=res.get("asama"), sebep=res.get("sebep"),
            last_reflect_at=_state.get("last_reflect_at"),
            detail="yansıma turu DURDURMA İSTEĞİYLE kesildi (süreç iniyor) — K/aşınma ve hipotez defterine "
                   "yazılmadı, ship yok; tur SAYILMADI: sayaç ve tabanlar İLERLEMEDİ, süreç yeniden "
                   "başlayınca aynı kanıtla yeniden dener (TSK-248)")
    return True


def _restored_baseline() -> int:
    """The reflection baseline for a fresh process: RESTORE the persisted last_reflect_at from
    hermes_status.json. Re-baselining to the current ledger length on every start silently discarded all
    span accrued since the last real reflection — under the strict-AND >=30-day horizon, routine daily
    restarts would reset the calendar clock forever and auto-reflection could NEVER fire (livelock).
    min() guards against a re-seeded (shorter) ledger; a first-ever run keeps the original design
    (baseline = current length: never reflect on the pre-existing backlog)."""
    n_now = len(store.read_jsonl("trades.jsonl"))
    persisted = store.read_json(STATUS_FILE, {}).get("last_reflect_at")
    return min(int(persisted), n_now) if isinstance(persisted, (int, float)) else n_now


def _restored_bg_baselines() -> dict:
    """Taze sürecin ARKA PLAN rejim tabanları (TSK-229) — `_restored_baseline`in rejim-başına ikizi: AYNI kaynak
    (STATUS_FILE, `_persist` yazar) ve AYNI sınır (`min(değer, defter uzunluğu)`, her rejime ayrı ayrı).

    NEDEN: `_persist` `bg_reflect_by_regime`i diske yazıyordu ama açılışta hiçbir yol onu geri okumuyordu. Taze süreçte
    alan yoktu, `_bg_ready_regime` her rejimin TÜM geçmişini yeni kanıt sayıyordu ve önceki sürecin zaten yansıdığı AYNI
    kanıtla arka plan yansımasını yeniden başlatıyordu (ölçüldü 2026-09-26: diskte `{"trend_down": 21}` varken taze süreç
    trend_down'u yeniden seçti). Bedeli gereksiz bir LLM+arama turuydu; canlı taban (`last_reflect_at`) TSK-227'den beri
    bundan etkilenmiyor.

    SINIR: defter kısalmış ya da yeniden tohumlanmışsa kalıcı taban defterin ötesini gösterir; kırpılmasaydı
    `trades[taban:]` defter o uzunluğa ulaşana dek boş kalır, rejim yeni kanıtı ne olursa olsun hiç seçilmezdi.

    ELEME, SESSİZ DEĞİL: tam sayı olmayan değer (bool dahil — JSON `true` Python'da int'tir; kesirli de: `_persist` yalnız
    `len(defter)` yazar), negatif değer ve sözlük olmayan alan ELENİR, `hermes_bg_taban_elendi` uyarısı her eleneni rejim
    adı ve gerekçesiyle taşır. Düzeltilmez, elenir: sayıya çevrilemeyen değer `_bg_ready_regime`in `int()`inde her poll'u
    istisnaya düşürürdü (arka plan ve ısınma dalı birlikte ölür); negatif taban `trades[-k:]` ile defterin SONUNU okurdu
    (yanlış kanıt penceresi). Elenen rejim tabansız sayılır = geri yüklemesiz bugünkü davranış; uydurma taban yazılmaz.
    Anahtarlar süzülmez: seçici yalnız `config.VALID_REGIMES`i okur, tanımadığı anahtar zararsızdır.

    Dosya ya da alan yoksa `{}` — bugünkü davranış; yokluk bozukluk değildir, uyarı yok."""
    n_now = len(store.read_jsonl("trades.jsonl"))
    disk = store.read_json(STATUS_FILE, {})
    ham = disk.get("bg_reflect_by_regime") if isinstance(disk, dict) else None
    if ham is None:
        return {}
    if not isinstance(ham, dict):
        obs.warn("hermes_bg_taban_elendi", alan_tipi=type(ham).__name__, elenen={},
                 detail="bg_reflect_by_regime sözlük değil — hiçbir arka plan tabanı geri yüklenmedi; "
                        "seçici her rejimi tabansız sayar (geri yüklemesiz davranış)")
        return {}
    geri: dict = {}
    elenen: dict = {}
    for rejim, deger in ham.items():
        if isinstance(deger, bool) or not isinstance(deger, int):
            elenen[str(rejim)] = f"tam sayı değil: {type(deger).__name__} {deger!r:.40}"
        elif deger < 0:
            elenen[str(rejim)] = f"negatif: {deger}"
        else:
            geri[str(rejim)] = min(deger, n_now)
    if elenen:
        obs.warn("hermes_bg_taban_elendi", alan_tipi="dict", elenen=elenen,
                 detail="bozuk arka plan tabanı geri yüklenmedi — elenen rejim tabansız sayılır "
                        "(geri yüklemesiz davranış); uydurma taban yazılmadı")
    return geri


_acilis_senkron_calisti = False      # SÜREÇ BAŞINA bir kez (start/stop döngüsü tekrarlatmaz)


def _acilis_senkron_dogrula() -> dict:
    """AÇILIŞ SENKRON-DOĞRULAMASI — SÜREÇ BAŞINA BİR KEZ.

    CANLI VAKA (6 gün sessiz ölüm): A1 taşınmasında `~/.hermes` yapılandırması TAŞINMADI (hiçbir
    dağıtım kanalının parçası değildi), `sync_local_agent_gemini` yalnız operatör panodan anahtar
    GİRDİĞİNDE koşan TEK-ATIMLIK bir yol olduğu için kendini onarmadı ve hiçbir bekçi "yerel ajan
    yapılandırılmış mı" diye sormuyordu. LLM ikinci-görüşü altı gün boyunca ölü kaldı; defterde
    yalnız "boş cevap" satırları vardı.

    KAPI ÜÇ AŞAMALIDIR VE HER AŞAMA ÖLÇÜMDÜR:
      1. Meridian'ın kendi kasasında GEMINI_API_KEY var mı — yoksa yapılacak bir şey YOKTUR
         (anahtarsız bir senkron, olmayan bir anahtarı taşımaya çalışmaktır).
      2. Yerel CLI ölçülür (`hermes.local_agent_config_state`): model.default + ~/.hermes/.env.
      3. ÖLÇÜLMÜŞ eksiklik varsa (ve yalnız o zaman) `sync_local_agent_gemini(True)` koşar.
    ÖLÇÜLEMEYEN durum ONARILMAZ ama SESSİZ de kalmaz: uyarı düşer. "Bilinmiyor"u "bozuk" sayıp
    çalışan bir kurulumu yeniden yapılandırmak, kapının önlemeye çalıştığı zararın ta kendisidir."""
    from . import hermes
    ts = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    try:
        if not (secrets.get("GEMINI_API_KEY") or "").strip():
            return {"yapildi": False, "sebep": "gemini_anahtari_yok", "senkron_ts": ts}
        durum = hermes.local_agent_config_state()
        yap = durum.get("yapilandirilmis")
        if yap is True:
            return {"yapildi": False, "sebep": "cli_zaten_yapilandirilmis",
                    "model": durum.get("model"), "senkron_ts": ts}
        if yap is None:
            obs.warn("local_agent_config_olculemedi", neden=durum.get("neden"),
                     kurulu=durum.get("kurulu"), model_durum=durum.get("model_durum"),
                     detail="yerel ajan yapılandırması ÖLÇÜLEMEDİ — açılış senkronu koşmadı; "
                            "bilinmeyeni bozuk sayıp yeniden yapılandırmak çalışan kurulumu bozardı")
            return {"yapildi": False, "sebep": "olculemedi", "neden": durum.get("neden"),
                    "senkron_ts": ts}
        res = hermes.sync_local_agent_gemini(True)
        obs.log("local_agent_resynced", ok=bool(res.get("ok")), neden=durum.get("neden"),
                model_durum=durum.get("model_durum"), env_anahtar=durum.get("env_anahtar"),
                detail=str(res.get("detail"))[:160], senkron_ts=res.get("senkron_ts", ts))
        return {"yapildi": True, "ok": bool(res.get("ok")), "neden": durum.get("neden"),
                "detail": res.get("detail"), "senkron_ts": res.get("senkron_ts", ts)}
    except Exception as e:
        # YASA 4: bu yol bir ÖZ-ONARIM yoludur; düşerse sessizce yutmak, onarımın koştuğu
        # yanılsamasını üretir (canlı vakanın kök nedeniyle aynı sınıf). Döngü yine de kurulur —
        # açılış doğrulaması hermes bekleme döngüsünü rehin alamaz.
        obs.warn("local_agent_acilis_senkron_hatasi", error=f"{type(e).__name__}: {e}",
                 detail="açılış senkron-doğrulaması düştü — yerel ajan yapılandırması BİLİNMİYOR")
        return {"yapildi": False, "sebep": f"hata: {type(e).__name__}", "senkron_ts": ts}


# Kalp atışı bayatlık PAYI (Ö-50). Mutlak saniye DEĞİL, poll aralığının katı — yeni eşik icat
# etmemek için (madde 3): aralık değişirse pay kendiliğinden ölçeklenir. 3 = bir kaçırılan poll
# tolere edilir, ikisi edilmez.
KALP_PAY = 3


def _kalp_vur() -> None:
    """Döngünün "hâlâ buradayım" damgası + kalıcılaştırma. YALNIZ bekleme döngüsünün İPLİĞİ çağırır
    (`_run` poll başı + ısınmanın başı ve nabzı, `_kalp_tazele`): `_persist`in içine konsaydı
    `reflect_now` (döngüsüz bir süreçten elle tetikleme) de kalp atardı ve pano, döngü başka süreçte
    ölü olsa bile onu CANLI görürdü — ölçmediğimiz şeyi iddia etmiş olurduk. Pano isteğinin kabul
    kapısı da (`yansima_istegi_karari`) bu damgaya bakar: kalp yalanlasaydı istek ölü bir kuyruğa
    düşerdi."""
    _state["kalp"] = _now()
    _persist()


def _kalp_tazele() -> None:
    """UZUN ISINMANIN İÇİNDEN KALP (TSK-233 tur 2) — ısınma nabzı (`_warmup_sprint._nabiz`) çağırır.

    KADANS YENİ BİR SAYI DEĞİL: kalp en son `poll_seconds` (döngünün kendi kalp kadansı) kadar önce atıldıysa yeniden
    atılır. Normal (havuz) yolda nabız `reflect.HAVUZ_NABIZ_SN` (60 sn) aralıkla ve her sonda sonunda gelir; kalbin
    yaşı böylece ≈ poll + 60 sn'yi aşmaz, tolerans (`KALP_PAY × poll`) içinde kalır. SINIR (dürüst): havuz ölüp sıralı
    hesaba düşülen BOZULMUŞ yolda nabız yalnız her walk-forward sonunda gelir (ölçülmüş: 2 walk-forward 5065 sn, v302
    vakası) — o pencerede kalp bayatlar ve pano "ilerlemiyor" der; bu ısınmanın normali değil anomalisidir. Kısma şart:
    `_persist` beyin/zincir olgularını da okur ve önbellekten dönen sondalar nabzı saniyede defalarca atar.

    Poll aralığı bilinmiyorsa (döngü dışı çağrı) hiçbir şey yazılmaz — o hâlde kalbin bir toleransı da yoktur.
    Yazım düşerse ısınma DURMAZ (nabız bir telemetridir), ama sessiz de kalmaz."""
    poll = int(_state.get("poll_seconds") or 0)
    if poll <= 0:
        return
    yas, _neden = _yas_s(_state.get("kalp"))
    if yas is not None and yas < poll:
        return
    try:
        _kalp_vur()
    except Exception as e:
        obs.warn("hermes_isinma_kalbi_yazilamadi", error=f"{type(e).__name__}: {e}"[:300],
                 detail="ısınma sürerken kalp diske yazılamadı — pano birimi ölü sanabilir; ısınma sürüyor")


def _kalp_canliligi(disk: dict) -> tuple[bool | None, str | None]:
    """Diskteki kalp damgasından canlılık hükmü — `(canli, neden)`.

    ÜÇ DEĞERLİ: `None` = ÖLÇÜLEMEDİ. "Durdu" demek bir İDDİADIR ve ölçülmemiş hâlin adı değildir
    (UYDURMA YASAĞI); pano bu ikisini ayrı göstermeli."""
    import datetime as _dt
    if not disk:
        # HİÇ KAYIT YOK — bu bir ölçüm boşluğu DEĞİL, kanıttır: döngü bu kurulumda hiç koşmamış
        # (ne bu süreçte ne bir başkasında; `STATUS_FILE` ilk `_persist`te doğar). "Ölçülemedi"
        # demek burada dürüst değil AŞIRI-İHTİYATLI olurdu ve panoyu boş yere belirsiz gösterirdi.
        return False, None
    kalp, poll = disk.get("kalp"), int(disk.get("poll_seconds") or 0)
    if not kalp or poll <= 0:
        # Kayıt VAR ama damga yok: döngü kalp atışı olmayan bir sürümde koşmuş ya da yazım düşmüş.
        # Burada "durdu" demek uydurma olur — yaş gerçekten ölçülemez.
        return None, "kayıt var ama kalp damgası/poll aralığı yok — canlılık ÖLÇÜLEMEDİ"
    try:
        yas = (_simdi() - _dt.datetime.fromisoformat(kalp)).total_seconds()
    except (TypeError, ValueError):  # sessiz-yutma: bozuk damga YUTULMUYOR, canlılık None ("ölçülemedi") olarak dönüyor — "durdu" demek uydurma olurdu, pano ikisini ayrı gösterir
        return None, f"kalp damgası çözümlenemedi: {kalp!r}"
    if yas <= KALP_PAY * poll:
        return True, None
    return False, f"kalp atışı {yas:.0f}sn eski (eşik {KALP_PAY}×{poll}sn)"


def _arama_taze(disk: dict, search_durumu: str | None, search_yas: float | None) -> bool:
    """Diskteki arama ilerlemesi KOŞUYOR ve kalbin payı içinde TAZE mi — süreç-dışından görülen "bir yansıma şu an
    ilerliyor" olgusu. Tazelik ölçüsü `_kalp_canliligi`nin payıdır (`KALP_PAY × poll_seconds`); ikinci bir eşik icat
    edilmedi. Bayat `running=True` (SIGKILL'de diskte donar) koşuyor SAYILMAZ: donmuş bayrak düğmeyi sonsuza dek
    "meşgul"e kilitlerdi."""
    poll = int((disk or {}).get("poll_seconds") or 0)
    return (search_durumu == "kosuyor" and search_yas is not None and poll > 0
            and search_yas <= KALP_PAY * poll)


def _dongu_canliligi(icerde: bool, disk: dict, search_durumu: str | None,
                     search_yas: float | None) -> tuple[bool | None, str | None]:
    """Bekleme döngüsü CANLI mı — `(canli, neden)`. TEK kural; okuyucuları `status()` (panonun `active` alanı) ve
    `yansima_istegi_karari` (istek kabul kapısı). Süreç-içindeyse iplik yetkilidir; değilse kalp atışı, ve UZUN ARAMA
    kalbi bastırdığında taze arama ilerlemesi (ölçülmüş normal: arama 1s55dk–3s14dk, 2026-08-16)."""
    if icerde:
        return True, None
    alive, neden = _kalp_canliligi(disk)
    if alive is not True and _arama_taze(disk, search_durumu, search_yas):
        alive, neden = True, "kalp bayat ama arama ilerlemesi taze (uzun yansıma)"
    return alive, neden


def _yansiyor_mu(icerde: bool, disk: dict, search_durumu: str | None, search_yas: float | None) -> bool:
    """Şu an bir yansıma SÜRÜYOR mu — `status()["reflecting"]` ve pano isteğinin "meşgul" kapısı AYNI olgudan okur.

    Bu sürecin kilidi tutuluyorsa evet (eski anlam birebir). Döngü BAŞKA süreçteyse (`meridian-learn`) bu sürecin
    kilidi hiçbir şey söylemez — elle yansıma pano sürecinden taşındığından beri orada hep boştur; o zaman olgu
    diskteki taze arama ilerlemesidir (`_arama_taze`)."""
    return _reflect_lock.locked() or (not icerde and _arama_taze(disk, search_durumu, search_yas))


def _yas_s(damga, simdi: str | None = None) -> tuple[float | None, str | None]:
    """ISO damganın yaşı (sn) — `(yas, neden)`. Ölçülemezse yaş None ve NEDEN (uydurma yok; 0 "bilmiyorum" değildir)."""
    if not damga:
        return None, "damga yok"
    try:
        t0 = dt.datetime.fromisoformat(str(damga))
        t1 = dt.datetime.fromisoformat(simdi) if simdi else _simdi()
        return max(0.0, round((t1 - t0).total_seconds(), 1)), None
    except (TypeError, ValueError) as e:  # sessiz-yutma: çözümlenemeyen damga YUTULMUYOR — yaş None + neden olarak çağırana (olaya/yanıta) dönüyor
        return None, f"damga çözümlenemedi: {str(damga)[:40]!r} ({type(e).__name__})"


def _ufuk_notu(hz: dict) -> str:
    """Elle tetiklemenin atladığı ufuk kapısının DÜRÜST notu — ufuk doluysa boş. TEK metin kaynağı: `reflect_now`
    yanıtı, pano isteğinin yanıtı ve öğrenme tarafındaki elle yansıma kaydı aynı cümleyi taşır (operatör egemendir,
    kapıyı bilerek atlar; ama atlama GÖRÜNÜR olmalı)."""
    if hz.get("ready"):
        return ""
    return (" · not: otomatik ufuk kapısı henüz dolmadı "
            f"({hz.get('trades', 0)}/{hz.get('trades_needed', '?')} işlem, "
            f"{hz.get('span_days', 0)}/{hz.get('min_days', '?')} gün) — elle tetikleme bunu bilerek atlar")


def _elle_yansima_govdesi(durdurma=None) -> bool:
    """ELLE yansımanın TEK gövdesi — `reflect_now` (süreç-içi/CLI) ve pano isteği (`_yansima_istegini_isle`, öğrenme
    süreci) AYNI gövdeyi koşar; iki kopya ayrışırdı. Kilit ÇAĞIRANDA tutulur ve orada bırakılır.

    `arka_plan=False`: elle yansıma canlı geri sayımı (`last_reflect_at`) taşır — döngü aynı işlemler üzerinde hemen
    yeniden yansımasın (TSK-227 kararı). Hata `last_result`a sınıf adıyla düşer; döngüyü/çağıranı düşürmez.

    `durdurma` (TSK-248): YALNIZ öğrenme döngüsünün iş parçacığındaki istek yolu verir (`_stop.is_set`). `reflect_now`
    VERMEZ: döngüsüz koşabilir ve o an `_stop` önceki bir `stop()`tan kurulu kalmış olabilir — yüklem geçseydi elle
    yansıma başlamadan "kesilirdi". Dönüş: tur durdurmayla KESİLDİ mi (`_record` işlemedi — TSK-248)."""
    from . import hermes, reflect
    try:
        # İLETME YASASI TEK KAYNAKTAN: yüklem YOKSA anahtar hiç geçmez (`reflect_now`un çağrı yüzeyi BİREBİR eskisi).
        return not _record(hermes.reflect_once(**reflect.backtest.durdurma_kw(durdurma)), arka_plan=False)
    except Exception as e:
        _state["last_result"] = f"error: {type(e).__name__}"
    return False


def _istek_ttl(poll_seconds) -> dict:
    """ELLE İSTEĞİN SÜRE AŞIMI (TSK-233 tur 2) — `{"ttl_s", "formul"}`. UYGULAYANI öğrenme döngüsüdür
    (`_yansima_istegini_isle`); döngü değerini `_state["istek_ttl"]` ile diske YAYIMLAR, pano yanıtı oradan okur — iki
    süreç iki ayrı ortamdan iki ayrı TTL hesaplamasın (tek kaynak).

    TÜRETME: pano isteği yalnız döngü kalp atarken kabul eder; kabul edilmiş bir isteğin MEŞRU en uzun bekleyişi,
    döngünün o an koştuğu en uzun işin bitmesi + bir sonraki poll'dur. Döngünün en uzun SINIRLI işi ısınmadır, sınırı
    `_warmup_tavan_dk()` (anomali sınırı: bu süreyi aşan koşum tanım gereği artık nominal değildir); yansıma aramaları
    ölçülmüş 1s55dk–3s14dk (2026-08-16) ile bu bandın içindedir. Poll payı olarak kabul kapısının AYNI toleransı
    (`KALP_PAY × poll_seconds`) eklenir: TTL = tavan_dk × 60 + KALP_PAY × poll (varsayılan 300 dk + 15 dk = 5 sa 15 dk).
    Bunu aşmış istek hiçbir meşru bekleyişle açıklanamaz — birim kapalı ya da takılıydı ve operatörün o anki niyetinin
    bağlamı (defter, ufuk) bayatladı: koşmak yerine düşürülür, yeni tıklama taze bağlamla koşar.
    `MERIDIAN_SEARCH_MAX_MIN` BİLEREK taban alınmadı: o tavan duvar saatini bağlamaz, yalnız taze sonda hesaplarını
    atlatır (`reflect.coordinate_descent_search` docstring'i) — üst sınır olarak okunamaz.
    Poll aralığı bilinmiyorsa TTL None: tolerans uydurulmaz, süre aşımı denetlenmez (uydurma yasağı)."""
    poll = int(poll_seconds or 0)
    if poll <= 0:
        return {"ttl_s": None, "formul": "poll_seconds bilinmiyor — süre aşımı uygulanmaz"}
    tavan = _warmup_tavan_dk()
    return {"ttl_s": tavan * 60 + KALP_PAY * poll,
            "formul": f"ısınma tavanı {tavan:g} dk × 60 + KALP_PAY {KALP_PAY} × poll {poll} sn"}


def yansima_istegi_karari(kaynak: str) -> dict:
    """PANO SÜRECİ (TSK-233): "şimdi düşün" isteği KABUL edilebilir mi? YAZMAZ — istek dosyasını pano ucu yazar
    (`api.api_hermes_reflect`, dosyanın TEK yazanı); burası öğrenme döngüsünün durumunu DİSKTEN okur ve karar verir.

    Dört cevap (`status`):
      "busy"/"bekleyen_istek"   — işlenmemiş (ya da işlenmekte olan) bir istek zaten var; ikincisi bırakılmaz.
      "busy"/"yansima_suruyor"  — bir yansıma sürüyor (`_yansiyor_mu`, `status()["reflecting"]` ile aynı olgu).
      "unavailable"             — döngü poll ETMİYOR (kalp bayat — eşik `KALP_PAY × poll_seconds`, `_kalp_canliligi`in
                                  TEK kuralı: bir kaçırılan poll tolere edilir, ikisi edilmez) ya da canlılık
                                  ÖLÇÜLEMEDİ. İstek BIRAKILMAZ: alınmayacak istek ölü bir kuyruktur ve operatöre
                                  "düşünüyor" yanılsaması verir. `systemctl` alt süreci ÇAĞRILMAZ — kalp yeter.
      "queued"                  — `istek` alanı yazılacak yükü taşır (istek anı, kaynak, ufuk notu).
    Ufuk-kapısı atlama notu (`_ufuk_notu`) yanıtın `detail`inde ve istekte korunur."""
    icerde, disk, taban = _durum_tabani()
    bekleyen = store.read_json(YANSIMA_ISTEGI_FILE, None)
    if bekleyen is not None:
        b = bekleyen if isinstance(bekleyen, dict) else {}
        yas, yas_neden = _yas_s(b.get("istek_at"))
        son = taban.get("son_elle_istek") or {}
        isleniyor = (son.get("durum") == "kosuyor" and b.get("istek_id") is not None
                     and son.get("istek_id") == b.get("istek_id"))
        # TTL'i UYGULAYAN yayımlar (`_istek_ttl`); yayımlanmamışsa (eski sürüm/hiç koşmamış döngü) None — uydurulmaz.
        ttl = taban.get("istek_ttl") if isinstance(taban.get("istek_ttl"), dict) else {}
        ttl_s = ttl.get("ttl_s") if isinstance(ttl.get("ttl_s"), (int, float)) else None
        bayat = (yas > ttl_s) if (yas is not None and ttl_s is not None) else None
        if bayat:
            durum_metni = (f" — süre aşımı (TTL {ttl_s:.0f} sn) AŞILDI: öğrenme süreci alınca KOŞMADAN düşürecek; "
                           "birim yeniden poll edince tekrar dene")
        elif isleniyor:
            durum_metni = " — öğrenme süreci onu ŞU AN işliyor"
        else:
            durum_metni = " — öğrenme süreci bir sonraki poll'unda alacak"
        return {"status": "busy", "neden": "bekleyen_istek",
                "bekleyen": dict(bekleyen) if isinstance(bekleyen, dict) else bekleyen,
                "bekleyen_yas_s": yas, "bekleyen_yas_neden": yas_neden, "ttl_s": ttl_s, "bayat": bayat,
                "detail": ("zaten bir düşünme isteği var"
                           + (f" ({yas:.0f} sn önce bırakıldı)" if yas is not None else " (yaşı ölçülemedi)")
                           + durum_metni + "; ikinci istek bırakılmadı")}
    try:
        from . import hermes
        okuma = hermes.search_progress_oku(ayni_surec=icerde)
        s_durum, s_yas = okuma.get("durum"), okuma.get("yas_s")
    except Exception as e:  # sessiz-yutma: arama ilerlemesi ölçülemedi — "olculemedi" olarak kapıya giriyor; koşan arama VARSAYILMAZ, canlılık kalpten ölçülür ve yanıtta görünür
        s_durum, s_yas = f"olculemedi: {type(e).__name__}", None
    if _yansiyor_mu(icerde, disk, s_durum, s_yas):
        return {"status": "busy", "neden": "yansima_suruyor", "detail": "zaten bir düşünme sürüyor"}
    canli, neden = _dongu_canliligi(icerde, disk, s_durum, s_yas)
    if canli is not True:
        bas = ("öğrenme biriminin canlılığı ÖLÇÜLEMEDİ" if canli is None
               else "öğrenme birimi çalışmıyor ya da poll etmiyor")
        return {"status": "unavailable", "neden": "ogrenme_dongusu_poll_etmiyor", "canlilik_neden": neden,
                "detail": (f"{bas} — istek alınmadı ({neden or 'durum kaydı yok: döngü bu kurulumda hiç koşmamış'}). "
                           "Döngü ısınma sürerken de kalp atar; kalp bayatsa döngü durmuş ya da ilerlemiyor. "
                           "İstek bırakılmadı, birim yeniden kalp attığında tekrar dene.")}
    hz = yansima_kapisi(taban)["horizon"]
    notu = _ufuk_notu(hz)
    poll = int(taban.get("poll_seconds") or 0)
    import uuid
    # `istek_id` KİMLİKTİR: `istek_at` saniye çözünürlüklüdür, iki istek aynı saniyeye düşebilir — "bu istek zaten
    # koştu mu" sorusu damgayla değil kimlikle cevaplanır (`_yansima_istegini_isle`).
    istek = {"istek_id": uuid.uuid4().hex, "istek_at": _now(), "kaynak": str(kaynak)[:80],
             "ufuk_hazir": bool(hz.get("ready")),
             "ufuk_notu": notu.strip(" ·") or None}
    # ISINMA SÜRÜYORSA (döngünün yayımladığı işaret — canlılık DEĞİL, yalnız mesajın içeriği): istek ısınma bitince,
    # bir sonraki poll'da koşar. Operatör saatler sürebilecek bekleyişi BİLEREK görsün.
    isinma = taban.get("isinma_suruyor") if isinstance(taban.get("isinma_suruyor"), dict) else None
    if isinma:
        i_yas, _in = _yas_s(isinma.get("basladi"))
        tavan_dk = isinma.get("tavan_dk")
        detay = ("istek bırakıldı — ısınma sürüyor"
                 + (f" ({i_yas / 60:.0f} dk'dır" if i_yas is not None else " (süresi ölçülemedi")
                 + (f", tavanı {tavan_dk:g} dk)" if isinstance(tavan_dk, (int, float)) else ")")
                 + ": istek ısınma bitince, döngünün bir sonraki poll'unda koşar" + notu)
    else:
        detay = ("istek bırakıldı — öğrenme süreci bir sonraki poll'unda"
                 + (f" (≤{poll} sn)" if poll > 0 else "")
                 + " alıp koşacak; süren bir yansıma varsa o bittikten sonra" + notu)
    return {"status": "queued", "horizon_ready": bool(hz.get("ready")), "istek": istek,
            "isinma_suruyor": bool(isinma), "detail": detay}


def _yansima_istegini_sil() -> None:
    """İşlenen (ya da süresi aşılıp düşürülen) isteği siler. Silinemezse (izin/disk) SESSİZ değil: uyarı düşer ve aynı
    istek bir sonraki poll'da `son_elle_istek` kimlik eşleşmesiyle TANINIR, yeniden koşmaz (`_yansima_istegini_isle`).

    NEDEN KİLİTSİZ (`store.file_lock` ALINMAZ) VE NEDEN GÜVENLİ — doğrusallaştırılabilirlik (linearizability):
      1. Pano (TEK yazan) yeni isteği YALNIZ dosya YOKKEN yazar; "yok mu?" denetimi ile yazım aynı dosya kilidi altında,
         tek atomik adımdır (`api.api_hermes_reflect`).
      2. Bu fonksiyon yalnız bu sürecin az önce OKUDUĞU isteği siler; o istek okunduğu andan silindiği ana dek dosyada
         kesintisiz durur (öğrenme tarafı dosyayı yeniden yazmaz, yalnız siler).
      3. Dolayısıyla o aralıkta panonun her "yok mu?" denetimi dosyayı GÖRÜR ve reddeder; yeni bir istek ancak bu
         silme GÖZLEMLENEBİLİR biçimde TAMAMLANDIKTAN sonra (`unlink` atomiktir) yazılabilir. Silme hiçbir zaman
         henüz işlenmemiş YENİ bir isteği yutamaz.
    Kilit bu yüzden güvenlik EKLEMEZ, yalnız risk ekler: bu fonksiyon `_reflect_lock` TUTULURKEN çağrılır; buraya dosya
    kilidi koymak "yansıma kilidi → dosya kilidi" sırasını doğurur. Bugün pano dosya kilidi altında yansıma kilidini
    yalnız GÖZLER (`locked()`), ALMAZ — döngü yok; ama yarın o gözlem bir `acquire`a dönerse sessiz bir kilit-sırası
    terslenmesi (deadlock) doğar. Kazancı olmayan riski almıyoruz."""
    try:
        (config.STATE / YANSIMA_ISTEGI_FILE).unlink(missing_ok=True)
    except OSError as e:
        obs.warn("hermes_yansima_istegi_silinemedi", error=f"{type(e).__name__}: {e}"[:300],
                 detail="işlenen elle yansıma isteği silinemedi — aynı istek yeniden KOŞMAZ, pano 'bekleyen istek' "
                        "görür; dosya elle silinmeli")


def _yansima_istegini_isle() -> bool:
    """ÖĞRENME SÜRECİ (TSK-233): panonun bıraktığı elle yansıma isteğini poll'da alır — koştuysa True.

    * İstek yoksa hiçbir şey yapmaz (poll maliyeti tek dosya varlık denetimi).
    * Kilit doluysa (bu süreçte başka bir yansıma koşuyor) istek BEKLER, KAYBOLMAZ: dosyaya dokunulmaz, bir sonraki
      poll yeniden dener.
    * Kilidi alınca: alınış olayı (`hermes_yansima_istegi_alindi`, istek anından GECİKMEYLE) + `son_elle_istek`
      kaydı ("kosuyor", ufuk notuyla — elle tetikleme kapıyı atlar ama bu kayıtta görünür) diske yazılır; elle
      yansıma gövdesi (`_elle_yansima_govdesi`, `arka_plan=False`) koşar; istek SİLİNİR ve kayıt "bitti" + sonuçla
      kalıcılaşır.
    SİLME YANSIMADAN SONRA: istek dosyası yansıma boyunca durur → pano o sürede ikinci isteği "meşgul" diye reddeder.
    Süreç yansıma ortasında ölürse (SIGKILL, `TimeoutStopSec`) istek kalır ve yeniden başlayan döngü onu koşar —
    operatörün istediği yansıma sessizce kaybolmaz. Aynı süreçte aynı istek (silme düştüyse) ikinci kez KOŞMAZ.
    DURDURMA (TSK-248): yansıma dur yüklemiyle (`_stop.is_set`) koşar; tur kesilirse SIGKILL'deki beyanın AYNISI
    uygulanır — istek SİLİNMEZ, kayıt `durum="durduruldu"` olur ("bitti" değil: tur sayılmadı), yeniden başlayan
    döngü isteği koşar. Pano bu durumu okumaz (yalnız "kosuyor"u karşılaştırır); bekleyen istek "bir sonraki
    poll'da alınacak" diye görünür — doğru olan da budur.
    HALT/bayat veri denetlenmez: elle tetikleme bunları hiç denetlemedi (`reflect_now` birebir); ship kapısı
    (`reflect.submit`) öğrenme durdurmasını zaten uygular."""
    ham = store.read_json(YANSIMA_ISTEGI_FILE, None)
    if ham is None:
        return False
    if not _reflect_lock.acquire(blocking=False):
        return False
    try:
        ist = ham if isinstance(ham, dict) else {}
        onceki = _state.get("son_elle_istek") or {}
        if ist.get("istek_id") is not None and onceki.get("istek_id") == ist.get("istek_id") \
                and onceki.get("durum") in ("bitti", "bayat"):
            _yansima_istegini_sil()          # silinemeyip kalmış, ZATEN karara bağlanmış istek — ikinci yansıma YOK
            return False
        alindi = _now()
        gecikme, gecikme_neden = _yas_s(ist.get("istek_at"), simdi=alindi)
        # SÜRE AŞIMI (tur 2): meşru en uzun bekleyişi aşmış istek KOŞMAZ, yaşıyla düşürülür (türetme `_istek_ttl`).
        # Yaşı ölçülemeyen istek düşürülmez — yaş uydurulmaz; alınış olayı `gecikme_neden` taşır.
        ttl = _istek_ttl(_state.get("poll_seconds"))
        if ttl["ttl_s"] is not None and gecikme is not None and gecikme > ttl["ttl_s"]:
            _state["son_elle_istek"] = {"istek_id": ist.get("istek_id"), "istek_at": ist.get("istek_at"),
                                        "kaynak": ist.get("kaynak"), "durum": "bayat", "yas_s": gecikme,
                                        "ttl_s": ttl["ttl_s"], "dusuruldu_at": alindi}
            obs.warn("hermes_yansima_istegi_bayat", istek_id=ist.get("istek_id"), istek_at=ist.get("istek_at"),
                     kaynak=ist.get("kaynak"), yas_s=gecikme, ttl_s=ttl["ttl_s"], ttl_formul=ttl["formul"],
                     detail="elle yansıma isteği süre aşımını geçmiş — KOŞMADAN düşürüldü (birim kapalı/takılıydı); "
                            "operatör yeniden tıklarsa taze bağlamla koşar")
            _yansima_istegini_sil()
            _persist()
            return False
        kayit = {"istek_id": ist.get("istek_id"), "istek_at": ist.get("istek_at"), "kaynak": ist.get("kaynak"),
                 "alindi_at": alindi, "gecikme_s": gecikme, "durum": "kosuyor"}
        _state["son_elle_istek"] = kayit
        kesildi = False                      # gövde koşmadan istisna çıkarsa bugünkü davranış: istek silinir
        try:
            hz = yansima_kapisi(dict(_state))["horizon"]
            kayit.update(ufuk_hazir=bool(hz.get("ready")), ufuk_notu=_ufuk_notu(hz).strip(" ·") or None)
            obs.log("hermes_yansima_istegi_alindi", istek_id=kayit["istek_id"], istek_at=kayit["istek_at"],
                    kaynak=kayit["kaynak"], alindi_at=alindi, gecikme_s=gecikme, gecikme_neden=gecikme_neden,
                    istek_bicimi=None if isinstance(ham, dict) else f"sözlük değil: {type(ham).__name__}",
                    ufuk_hazir=kayit["ufuk_hazir"], ufuk_notu=kayit["ufuk_notu"],
                    detail="pano isteği öğrenme sürecinde alındı — elle yansıma bu süreçte koşuyor")
            _persist()                       # "kosuyor" işareti panoya görünsün (uzun yansıma boyunca)
            kesildi = _elle_yansima_govdesi(durdurma=_stop.is_set)
        finally:
            if kesildi:
                kayit.update(durum="durduruldu", durduruldu_at=_now())   # istek KALIR — docstring (TSK-248)
            else:
                _yansima_istegini_sil()
                kayit.update(durum="bitti", bitti_at=_now(), sonuc=_state.get("last_result"))
            _persist()
    finally:
        _reflect_lock.release()
    return True


def _run(poll_seconds: int) -> None:
    """Bekleme döngüsünün gövdesi: `poll_seconds` aralıkla yoklar, koşulları ölçer ve tek bir dalı
    seçer — yansıma / arka plan yansıması / ısınma sprinti / atlama.

    Tek-kapı: bütün dallar `_reflect_lock`u bloksuz almaya çalışır, aynı anda YALNIZ BİR yansıma
    koşar. HALT ya da bayat veri varsa hiçbir dal koşmaz. Her poll'da durum diske yazılır (poll
    BAŞLARKEN de) ve `_warm_skip` tokeni "koşmadı" ile "koşamaz"ı ayırt eder. Açılış senkron-
    doğrulaması süreç başına bir kez, `start()` içinde değil BURADA koşar (açılışı bloklamasın)."""
    from . import hermes
    global _acilis_senkron_calisti
    if not _acilis_senkron_calisti:
        _acilis_senkron_calisti = True
        # Döngünün İÇİNDE, `start()` içinde DEĞİL: ölçüm+senkron birkaç alt süreç koşturur ve
        # `start()` uygulama açılışında (api.py startup) senkron çağrılır — orada bloklamak,
        # yavaş/asılı bir CLI'nin panoyu açılışta rehin alması demekti.
        _state["local_agent_sync"] = _acilis_senkron_dogrula()
    every = int(config.goal().get("reflection_every", 5))
    if _state.get("last_reflect_at") is None:
        _state["last_reflect_at"] = _restored_baseline()
    # Arka plan rejim tabanları da AYNI desenle geri yüklenir (TSK-229): süreç başına bir kez ve aşağıdaki ilk `_persist`ten
    # ÖNCE — o yazım diski `_state`le ezer, sonra okunsa geri yüklenecek bir şey kalmazdı. Alan süreçte zaten varsa
    # (aynı süreçte stop→start) süreç-içi değer diskten tazedir, yeniden okunmaz. Geri yüklenecek taban yoksa alan
    # KURULMAZ: bugünkü hâl birebir (seçici yokluğu boş sözlük sayar).
    if _state.get("bg_reflect_by_regime") is None:
        geri = _restored_bg_baselines()
        if geri:
            _state["bg_reflect_by_regime"] = geri
    _state.update(started_at=_now(), poll_seconds=poll_seconds)
    _state["istek_ttl"] = _istek_ttl(poll_seconds)   # UYGULAYAN yayımlar, pano okur (TSK-233 tur 2)
    _persist()
    while not _stop.is_set():
        try:
            _state["last_poll"] = _now()
            _kalp_vur()     # poll BAŞLARKEN yaz: aşağıdaki yansıma dakikalar sürebilir ve tek yazma
                            # poll sonundaysa dosya o süre boyunca donar, panoda "hiç poll yapılmadı"
                            # görünür (gözlem boşluğu).
            from . import watchdog as _wd7
            _wd7.beat("hermes_poll")
            try:
                from . import hermes as _hm3
                _hm3.sync_agent_skills()   # canlıda görüldü: hermes-agent küratörü linkleri silebiliyor —
                _hm3.config_ensure_integrations()  # aynı öz-onarım: MCP/hook/cache/pool config'i tazele
            except Exception:              # her poll'da ucuz eşitleme = sürekli öz-onarım
                # sessiz-yutma: kalıcı bozukluk bir SONRAKİ poll'da yine denenir ve start() yolundaki
                # AYNI çağrı uyarıyı zaten yazar; burada uyarmak aynı olayı günde yüzlerce kez tekrarlardı.
                pass
            # PANO İSTEĞİ (TSK-233): operatörün "düşün" isteği BU süreçte, BU kilit altında koşar — öğrenme durumunun
            # tek yazanı bu döngüdür. Sağlık dallarından ÖNCE ve onlardan bağımsız: elle tetikleme HALT/bayat veriyi hiç
            # denetlemedi (`reflect_now` birebir). Kilit doluysa istek bekler; aşağıdaki zincir her durumda koşar.
            _yansima_istegini_isle()
            if not health.halted() and not health.stale(900):
                trades = store.read_jsonl("trades.jsonl")
                last_at = int(_state["last_reflect_at"])
                # Phase 3 STRICT-AND guardrail, scoped to the LIVE regime (the one a new reflection would
                # tune): >= reflection_every trades AND >= min_days span, both within that regime.
                live_reg = store.read_json("regime.json", {}).get("regime")
                live_reg = live_reg if live_reg in config.VALID_REGIMES else None
                horizon = _horizon_ok(trades, last_at, regime=live_reg, min_trades=every)
                _state["horizon_ready"] = bool(horizon)
                _state["horizon_regime"] = live_reg
                # ISINMA SPRİNTİ NEDEN KOŞMADI: sprint bu elif zincirinin SON dalı, yani her poll'da
                # önceki dallara yeniliyor olabilir. 0/12'yi "birazdan koşar" diye göstermek yanlış
                # vaat: arka plan yansıması sırayı sürekli tutuyorsa sayaç ASLA ilerlemez. Nedeni
                # burada tokenle yaz ki pano "koşmadı" ile "koşamaz"ı ayırt edebilsin.
                _state["_warm_skip"] = None
                if health.learn_halted():
                    # F8-A3 (operatör kararı 2026-08-23): kanonik kol adı yazılır; eski
                    # "learning_halted" dönem sonuna dek eşanlamlı-okunur (status() içindeki
                    # kol_adi çevirisi eski PERSİST edilmiş değerleri de sayaçla yakalar).
                    _state["last_result"] = "halt_learning"        # ısınma da duraklar: operatör tam sessizlik istedi
                    _state["_warm_skip"] = "learn_halted"
                # ATEŞLEME YÜKLEMİ TEK TANIMDIR (`_yansima_vadesi`): bekçinin "vade doldu ama yansıma yok"
                # ayağı (TSK-204) aynı yüklemi `yansima_kapisi` üzerinden okur — satır-içi kopya ayrışırdı.
                elif _yansima_vadesi(trades, last_at, every, live_reg) and _reflect_lock.acquire(blocking=False):
                    try:
                        # pass the CERTIFIED regime: the search takes minutes, and a regime flip in the
                        # meantime must not retarget the ship into a regime the horizon never certified.
                        _state["_warm_skip"] = "reflect"
                        # DUR YÜKLEMİ (TSK-248): `_stop.is_set` yansıma zincirine ENJEKTE edilir (`_warmup_sprint`
                        # deseni). Kesilen tur SAYILMAZ: `_record` işlemez, taban sabit kalır.
                        _record(hermes.reflect_once(target_regime=live_reg, durdurma=_stop.is_set), arka_plan=False)
                    finally:
                        _reflect_lock.release()
                elif (bg := _bg_ready_regime(trades, every, live_reg)) and \
                        os.environ.get("MERIDIAN_BG_REFLECT", "1") == "1" and \
                        _reflect_lock.acquire(blocking=False):
                    try:
                        _state["_warm_skip"] = "bg_reflect"
                        obs.log("bg_reflection_start", regime=bg,
                                detail="canlı ufuk dolu değil — birikmiş kanıtlı rejim arka planda işleniyor")
                        # `background=True` ARKA PLAN TURUNUN KİMLİĞİDİR: `reflect_once` bu
                        # bayrak olmadan kanıtın canlı-dışı bir rejimden geldiğini BİLEMİYORDU ve
                        # bg=trend_up hâlinde ship yüzeyi GLOBAL oluyordu. Bayrak, aramayı `bg`
                        # rejimine zorlar ve global (@'sız) önerileri o turda reddettirir.
                        # `arka_plan=True`: canlı geri sayım (`last_reflect_at`) TAŞINMAZ — bu tur yalnız
                        # kendi rejim tabanını taşır (TSK-227; gerekçe `_record`da).
                        # Kesilen arka plan turu da SAYILMAZ: `_record` işlemezse rejim tabanı İLERLEMEZ (TSK-248).
                        if _record(hermes.reflect_once(target_regime=bg, background=True, durdurma=_stop.is_set),
                                   arka_plan=True):
                            _state.setdefault("bg_reflect_by_regime", {})[bg] = len(trades)
                    finally:
                        _reflect_lock.release()
                elif os.environ.get("MERIDIAN_WARMUP_SPRINTS", "1") == "1" and \
                        _reflect_lock.acquire(blocking=False):
                    # ISINMA SPRINTİ: yansıma ateşlemeye HAK KAZANMADI (ufuk dolmadı) ama işlemci
                    # boşta. Sandbox koordinat araması koştur — HİÇBİR ŞEY SHIP ETMEDEN, yalnız UCB
                    # önceliklerini ısıtmak için (probe'lar defter-kalıcı çıkmaz yaratmaz — bilinçli tasarım).
                    # Gerçek yansıma ateşlediğinde arama bilgili sıralamadan başlar. Sık koşmasın diye
                    # WARMUP_EVERY_POLLS pollda bir.
                    try:
                        _state["_warm_ticks"] = _state.get("_warm_ticks", 0) + 1
                        if _state["_warm_ticks"] % WARMUP_EVERY_POLLS == 0:
                            _warmup_sprint()
                    finally:
                        _reflect_lock.release()
                elif os.environ.get("MERIDIAN_WARMUP_SPRINTS", "1") != "1":
                    _state["_warm_skip"] = "disabled"
                else:
                    _state["_warm_skip"] = "lock_busy"   # başka bir yansıma kilidi tutuyor
            else:
                _state["_warm_skip"] = "halted_or_stale"
            _persist()
        except Exception as e:
            _state["last_result"] = f"error: {type(e).__name__}"
            _persist()
        _stop.wait(poll_seconds)
    _persist()


def start(poll_seconds: int = 300) -> dict:
    """Bekleme döngüsünü daemon iş parçacığı olarak başlatır; zaten koşuyorsa yenisini AÇMAZ
    (`{"already_running": True}`). Başlamadan önce ajan skill seti ve entegrasyon config'ini
    eşitler (öz-onarım)."""
    global _thread
    with _lock:
        if _thread and _thread.is_alive():
            return {"already_running": True}
        _stop.clear()
        try:
            from . import hermes as _hm2
            _hm2.sync_agent_skills()               # ajan skill seti = enabled seti (başlangıçta eşitle)
            _hm2.config_ensure_integrations()      # MCP/hook/cache/pool config'i başlangıçta kur
        except Exception:  # sessiz-yutma: geç bağlanan yardımcı modül/çağrı; asıl karar bu değere bağlı değil ve çağıran yokluğu yedek değerle karşılıyor
            pass
        _thread = threading.Thread(target=_run, args=(poll_seconds,), name="hermes-standby", daemon=True)
        _thread.start()
    return {"started": True, "poll_seconds": poll_seconds}


def stop() -> dict:
    """Durdurma olayını kurar — döngü bir sonraki uyanışında çıkar (iş parçacığını beklemez)."""
    _stop.set()
    return {"stopping": True}


def reflect_now() -> dict:
    """Kick off ONE reflection in a BACKGROUND thread (operator-triggered) and return immediately. The
    coordinate-descent search runs several walk-forwards and can take minutes — far too long to block an
    HTTP request (browser/proxy timeouts, a stuck worker). Poll status()['reflecting'] for completion.
    Refuses if a reflection is already running.

    PANO UCU BUNU ÇAĞIRAMAZ (TSK-233; sınıf çivisi v564): bu fonksiyon BU süreçte yansıma koşar ve durum dosyasını
    BU sürecin `_state`inden yazar — döngüsü başka süreçte olan pano sürecinde çağrılınca öğrenme sürecinin kaydını
    (`last_reflect_at`, `bg_reflect_by_regime`, `kalp`) eziyordu. Pano `yansima_istegi_karari` + istek dosyası
    yoluyla öğrenme sürecine devreder. Burası süreç-içi/CLI yoludur; gövde `_elle_yansima_govdesi` ile ORTAKTIR."""
    if _reflect_lock.locked():
        return {"status": "busy", "detail": "zaten bir düşünme sürüyor"}
    # Operator override: the manual button deliberately bypasses the standby horizon (the operator is
    # sovereign), but the bypass must be VISIBLE — report the gate state honestly instead of hiding it.
    st = status()
    hz = st.get("horizon") or {}
    note = _ufuk_notu(hz)

    def _bg():
        """Arka plan iş parçacığının gövdesi: tek yansımayı koşar, sonucu kaydeder, durumu yazar.

        Kilidi bloksuz alır — alamazsa sessizce döner (tek-kapı: aynı anda tek yansıma). Hata
        `last_result`a sınıf adıyla düşer (`_elle_yansima_govdesi`); `_persist` + kilit bırakma her hâlde koşar."""
        if not _reflect_lock.acquire(blocking=False):
            return
        try:
            _elle_yansima_govdesi()
        finally:
            _persist()
            _reflect_lock.release()
    threading.Thread(target=_bg, name="hermes-reflect-now", daemon=True).start()
    _persist()
    return {"status": "started", "horizon_ready": bool(hz.get("ready")),
            "detail": "arama başladı — birkaç dakika sürebilir (arka planda)" + note}


def status() -> dict:
    """Panonun okuduğu tek durum modeli: `_state` + canlılık, beyin/model, arama ilerlemesi ve
    DÜRÜST geri sayım.

    "Sonraki yansımaya kaç işlem kaldı" ve ufuk ilerlemesi HER çağrıda TAZE ölçülür (HALT/bayat
    hâlde ve ilk poll'dan önce de) — tek kaynak burasıdır, arayüz kendi formülünü üretmez."""
    # SÜREÇ-İÇİ Mİ? (Ö-50) — kural `_durum_tabani`da, `yansima_kapisi` ile ORTAK (tek taban kuralı).
    icerde, disk, taban = _durum_tabani()
    # F8-A3 GEÇİŞ OKUYUCUSU (2026-08-23): üretici artık kanonik "halt_learning" yazar; diskte
    # RESTART-ÖNCESİ persist edilmiş eski "learning_halted" hâlâ yaşayabilir. Okuyucu deseni
    # (durum_sozlugu geçiş rejimi): eşanlamlıyı kanonik ada çevir ve SAY — sayaç uzun süre 0
    # kalınca eski adın ölümü kanıtlanır, düşürme kararı Rol-1'de. `kol_adi` tanımadığını
    # DEĞİŞTİRMEZ ("rejected_by_backtest" gibi kol-olmayan değerler aynen geçer, sayılmaz).
    if isinstance(taban.get("last_result"), str):
        from . import durum_sozlugu as _dsz
        taban["last_result"] = _dsz.kol_adi(taban["last_result"])
    try:
        from . import hermes
        model = hermes.active_model()
        okuma = hermes.search_progress_oku(ayni_surec=icerde)
        search, search_durumu, search_yas = okuma["kayit"], okuma["durum"], okuma["yas_s"]
    except Exception:  # sessiz-yutma: geç bağlanan yardımcı modül/çağrı; asıl karar bu değere bağlı değil ve çağıran yokluğu yedek değerle karşılıyor
        model, search, search_durumu, search_yas = None, {}, "olculemedi", None
    # CANLILIK: süreç-içindeyse iplik yetkili; değilse KALP ATIŞI. `systemctl is-active` bilerek
    # KULLANILMADI — o yalnız sürecin VAR olduğunu söyler, İLERLEDİĞİNİ değil; asılı bir döngü
    # "active" görünürdü. Kalp atışı ikisini birden ölçer. Yaş ölçülemiyorsa `active` None kalır
    # (UYDURMA YASAĞI: "durdu" demek bir iddiadır, ölçülmemiş hâlin adı değildir).
    # UZUN ARAMA KALBİ BASTIRIR — ve bu bir istisna değil, ÖLÇÜLMÜŞ normaldir: geçmiş altı
    # aramanın süresi 1s55dk–3s14dk (2026-08-16 günlük ölçümü). O saatler boyunca poll dönmez,
    # yani kalp bayatlar; ama arama ilerlemesi TAZE ise döngü kanıtlı biçimde çalışıyordur.
    # Tazelik ölçüsü yine kalbin payıdır — ikinci bir eşik icat edilmedi. Kural TEK yerde
    # (`_dongu_canliligi`): pano isteğinin kabul kapısı (`yansima_istegi_karari`) da oradan okur.
    alive, alive_neden = _dongu_canliligi(icerde, disk, search_durumu, search_yas)
    # DÜRÜST GERİ SAYIM + UFUK: tek hesap yeri `yansima_kapisi` (bekçinin öğrenme-canlılık alarmı da
    # oradan okur — TSK-204). Pano burada yalnız alanları taşır, formül üretmez.
    kapi = yansima_kapisi(taban)
    brain = _brain()
    return {**taban, "active": alive, "active_neden": alive_neden, "surec_ici": icerde,
            "search_durumu": search_durumu, "brain": brain, "model": model,
            "brain_availability": _brain_availability(), "brain_chain": _brain_chain(),
            "brain_degraded": brain == "deterministic",
            "reflection_every": kapi["reflection_every"], "closed_trades": kapi["closed_trades"],
            "trades_since_last_reflection": kapi["trades_since_last_reflection"],
            "trades_until_next": kapi["trades_until_next"],
            "horizon": kapi["horizon"], "horizon_ready": kapi["horizon_ready"],
            "horizon_regime": kapi["horizon_regime"],
            "search": search,                      # live coordinate-descent progress (probe i/total, best)
            # SÜREÇ-DIŞINDA da doğru (TSK-233): elle yansıma pano sürecinden taşındı, o süreçteki kilit hep boştur.
            "reflecting": _yansiyor_mu(icerde, disk, search_durumu, search_yas)}
