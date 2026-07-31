"""watchdog.py — Mekanizma Bekçisi (#1): 15+ periyodik dişlinin canlılık nabzı.

Panel bugüne dek VERİNİN tazeliğini gösteriyordu; MEKANİZMANIN kendisi sessizce durduğunda kimse
görmüyordu (canlı örnek: ısınma kadansı anomalisi günlerce 'not edildi' kaldı). Her mekanizma
koştuğunda `beat(ad)` damgalar; `report()` beklenen pencereyle karşılaştırır ve gecikenleri listeler.
Pencereler takvim-gerçekçi: seans-bağımlı işler hafta sonunu tolere eder (4 gün), haftalıklar 9 gün.

Yalnız GÖZLEM: bekçi hiçbir mekanizmayı yeniden başlatmaz, hiçbir kararı etkilemez — amber satır
üretir, teşhisi operatöre/paneline bırakır."""
from __future__ import annotations
import datetime as dt

import threading

from . import store

BEATS_FILE = "mechanism_beats.json"
_BEAT_LOCK = threading.Lock()   # canlıda görüldü: scheduler + hermes iş parçacıkları aynı dosyayı
                                # kilitsiz oku-değiştir-yaz yapınca nabızlar birbirini eziyordu

# ad → beklenen azami sessizlik (saniye). Yorumlar dürüst gerekçe: pencere neden bu genişlikte.
EXPECTED: dict[str, int] = {
    "scheduler_poll":   30 * 60,          # 300 sn'lik poll — 30 dk sessizlik = süreç ölü/kilitli
    # `hermes_poll` PENCERESİ 30 DK KALIR AMA ANLAMI 2026-07-31'DE (WP-H/H11) DEĞİŞTİ: nabzı artık
    # yalnız `_run` döngüsünün turu atmıyor, ISINMA SPRİNTİ de her sondada atıyor. Eskiden ısınma
    # koşarken (nominal 1-5 sa) döngü tura dönemiyor, nabız susuyor ve bekçi SAHTE bir
    # MECHANISM_STALE üretiyordu — mekanizma ölü değil MEŞGULdü. Nabzın sorduğu soru "döngü turladı
    # mı" değil, "hermes ipliği canlı ve ilerliyor mu"dur; ısınma içinden atılan nabız o soruya
    # DOĞRU cevap verir. Pencereyi ısınmaya göre genişletmek yanlış olurdu: o zaman gerçekten ölmüş
    # bir poll ipliği de saatlerce görünmezdi.
    "hermes_poll":      30 * 60,          # bekleme döngüsü + ısınma sprinti (sonda başına nabız)
    # `warmup_sprint` EŞİĞİ 8 SA'DA KALIR — VE ARTIK GERÇEK BİR ANOMALİ ÖLÇER. Nominal ~1-5 sa;
    # H11'den beri aramanın KENDİ süre tavanı var (HERMES_WARMUP_MAX_MIN, varsayılan 300 dk = 5 sa)
    # ve tavana takılan koşum kibarca kesilir. Yani 8 sa'lık bir sessizlik artık "ısınma uzun sürdü"
    # olamaz: tavan onu 5 saatte keserdi. Kalan tek açıklama tavanın ÇALIŞMAMASIDIR (iplik asıldı,
    # sonda içinde kilitlendi, süreç öldü) — eşiği eskiden gürültü üreten bir sayı, şimdi teşhis.
    "warmup_sprint":    8 * 3600,
    "cf_advance":       4 * 24 * 3600,    # seans-bağımlı: uzun hafta sonu + tatil toleransı
    "p5_calibrations":  4 * 24 * 3600,    # seans-bağımlı (P5 her döngüde)
    "mirror_reconcile": 4 * 24 * 3600,    # seans-bağımlı (alpaca modunda her döngüde)
    "crosscheck":       4 * 24 * 3600,    # seansta bir
    "earnings_refresh": 9 * 24 * 3600,    # haftalık (+2 gün pay)
    "arming_eval":      9 * 24 * 3600,    # haftalık (+2 gün pay)
    # ---- ÖĞRENME KADANSLARI (öğrenme-otomasyonu turu 2026-07-30; listeye temizlik turunda girdi) --
    # NEDEN GECİKMELİ GİRDİ: dört mekanizma `beat()` damgasını ZATEN atıyordu (scheduler._learning_
    # cadence → shadow_fit/axis2_cycle, hermes.backfill → opinion_backfill, sprint.maybe_start →
    # sprint_cadence) ama EXPECTED'de olmadıkları için `report()` onları hiç ARAMIYORDU. Nabız
    # atılıp kimsenin beklemediği bir mekanizma, durduğunda MECHANISM_STALE üretmez — yani bekçinin
    # kör noktası. Dördü de artık izleniyor.
    "shadow_fit":       4 * 24 * 3600,    # seans-bağımlı (öğrenme kadansı seans başına 1×)
    "axis2_cycle":      4 * 24 * 3600,    # seans-bağımlı (aynı kadansın 2. adımı)
    # DOLGU AYRI PENCERE: kadans her seans TETİKLENİR ama `backfill_budget()["tavan"] == 0` iken
    # damga ATILMAZ (bütçe kısılması bir arıza değil). Kuyruk boşaldığında da öyle. 9 gün =
    # "iki hafta boyunca hiç dolgu koşmadıysa gerçekten bakılmalı" — kısılmayı alarm sanmaz.
    "opinion_backfill": 9 * 24 * 3600,
    # SPRINT AYNI SINIF: `sprint.should_run` gece dilimi/aktif sprint/meşguliyet kapılarından
    # dönebilir; her seans koşması BEKLENMEZ. Haftalık pencere "antrenman tamamen durdu"yu yakalar.
    "sprint_cadence":   9 * 24 * 3600,
    # ---- TEMİZLİK TURUNDA EKLENEN KADANSLAR (2026-07-30) ---------------------------------------
    "y4_collect":       4 * 24 * 3600,    # seans-sonrası Y4 toplama (insider delta + short interest)
    "validation_report": 9 * 24 * 3600,   # haftalık kanıt raporu (+2 gün pay)
    "massive_verify":   9 * 24 * 3600,    # haftalık grouped-vs-zincir tutarlılık ölçümü
    "shadowlaw_drift":  9 * 24 * 3600,    # haftalık MEASURED_V3 kayma bekçisi
}


def _now() -> float:
    return dt.datetime.now(dt.timezone.utc).timestamp()


def beat(name: str) -> None:
    """Mekanizma koştu — damgala. Süreç-içi kilitle (iki daemon iş parçacığı aynı anda yazar);
    sayısal olmayan artık değerler yazımda ayıklanır. Bekçi asla mekanizmayı düşürmez."""
    try:
        with _BEAT_LOCK:
            beats = store.read_json(BEATS_FILE, {})
            beats = {k: v for k, v in beats.items() if isinstance(v, (int, float))}
            beats[name] = _now()
            store.write_json(BEATS_FILE, beats)
    except Exception as e:
        # Nabız yazılamazsa dedektörler "hiç koşmadı" gibi görünür ve bekçi KENDİ körlüğünü
        # üretkenlik sanır. Sessiz kalamaz.
        from . import obs
        obs.warn("watchdog_beat_write_failed", mechanism=name, error=f"{type(e).__name__}: {e}")


def report() -> dict:
    """{stale: [{name, gap_h, expected_h}], ok: n, never: [adlar]} — teşhis paneli buradan okur.
    Hiç damgalanmamış mekanizma 'never' listesinde (kurulumdan beri hiç koşmadı — en yüksek sesli hal)."""
    beats = store.read_json(BEATS_FILE, {})
    now = _now()
    stale, never, ok = [], [], 0
    for name, max_gap in EXPECTED.items():
        ts = beats.get(name)
        if ts is None:
            never.append(name)
            continue
        try:
            gap = now - float(ts)
        except (TypeError, ValueError):  # sessiz-yutma: sonuç KAYDA GEÇİYOR (never listesi) — bozuk damga dürüstçe "hiç koşmadı" sayılır, bilgi kaybolmaz
            never.append(name)                 # bozuk damga = hiç yok say (dürüst en-kötü varsayım)
            continue
        if gap > max_gap:
            stale.append({"name": name, "gap_h": round(gap / 3600, 1),
                          "expected_h": round(max_gap / 3600, 1)})
        else:
            ok += 1
    stale.sort(key=lambda x: -x["gap_h"])
    return {"stale": stale, "never": never, "ok": ok, "total": len(EXPECTED)}


ALARMED_FILE = "watchdog_alarmed.json"


def check_and_alarm() -> None:
    """v11 #1 — bayat-GEÇİŞ alarmı: bir mekanizma penceresini İLK aştığında bir kez MECHANISM_STALE
    (bildirim beyaz-listesinde → telefona düşer); toparlanınca kayıt silinir ki bir sonraki bayatlama
    yine görünsün. Her poll'da ucuz; bekçi felsefesi aynı — yalnız haber verir."""
    from . import obs
    rep = report()
    alarmed = set(store.read_json(ALARMED_FILE, []))
    now_stale = {x["name"] for x in rep["stale"]}
    for x in rep["stale"]:
        if x["name"] not in alarmed:
            obs.alarm("MECHANISM_STALE",
                      f"mekanizma gecikti: {x['name']} — {x['gap_h']} sa (pencere {x['expected_h']} sa)",
                      mechanism=x["name"], gap_h=x["gap_h"])
    store.write_json(ALARMED_FILE, sorted(now_stale))


# =============================================================================================
# BÜTÜNLÜK DEDEKTÖRLERİ (2026-07-21) — "koşuyor mu?" yetmiyor.
# Bugün bulunan hataların HEPSİ mevcut testlerden/denetimlerden geçti: karşı-olgusal defter ömrü
# boyunca boştu (ve 4 alt mekanizmayı aç bıraktı), barlar önbelleklenmiş walk-forward'ların altından
# sessizce değişti, silahlı planlar kayıtsız buharlaştı. Üç eksik soru:
#   1) ÜRETKENLİK  — mekanizma koşuyor ama ÜRETİYOR mu?
#   2) KORUNUM     — giren her plan kayıtlı bir terminal duruma ulaşıyor mu? (sessiz kayıp var mı?)
#   3) DETERMİNİZM — barlar, geçersiz kılınmadan sessizce değişti mi?
# Hepsi ucuz (dosya okuma/stat), yalnız GÖZLEM — hiçbir karara dokunmaz.
# =============================================================================================

_UNREADABLE: set = set()


def _n_jsonl(name: str) -> int:
    """Defter satır sayısı. OKUNAMAYAN defter 0 satır DEĞİLDİR: 0 dönmek, üretkenlik dedektörüne
    "mekanizma hiç üretmedi" dedirtir ve ölçüm arızası bulguya dönüşür (starved olayının aynısı).
    Artık okunamayan defter ayrıca kaydedilir ve raporda AYRI bir satır olarak görünür."""
    try:
        return len(store.read_jsonl(name))
    except Exception as e:
        from . import obs
        if name not in _UNREADABLE:
            _UNREADABLE.add(name)
            obs.warn("ledger_unreadable", ledger=name, error=f"{type(e).__name__}: {e}",
                     detail="bu defterin ölçümü GÜVENİLMEZ — 0 satır sanılmasın")
        return 0


def production_report() -> dict:
    """#1 ÜRETKENLİK: her mekanizmanın ÇIKTISI var mı? 'Hiç üretmemiş' (starved) ile 'eşik dolmamış'
    (waiting) DÜRÜSTÇE ayrılır — biri hata işareti, diğeri sabır. cf defteri ömrü boyunca 0 satırdaydı
    ve bunu hiçbir denetim söylemedi; bu fonksiyon onu ilk gün söylerdi."""
    def _cal(f, key):
        d = store.read_json(f, None)
        return None if d is None else (d.get(key) or 0)

    checks = [
        # (ad, üretim sayısı, "sağlıklı" eşiği, not)
        ("counterfactual_ledger", _n_jsonl("counterfactuals.jsonl"), 1, "karşı-olgusal kanıt satırı"),
        ("trades", _n_jsonl("trades.jsonl"), 1, "gerçek işlem"),
        ("hypotheses", _n_jsonl("hypotheses.jsonl"), 1, "öğrenme hipotezi"),
        ("score_calibration", _cal("score_calibration.json", "n"), 30, "skor→sonuç örneklemi"),
        ("exit_efficiency", _cal("exit_efficiency.json", "n"), 1, "MFE/MAE muhasebesi"),
        ("cf_fidelity", _cal("cf_fidelity.json", "n"), 5, "sim↔gerçek kesişimi"),
        ("near_miss", _cal("near_miss.json", "resolved_total"), 1, "eşik-altı karne"),
        ("llm_calibration", _cal("llm_calibration.json", "n_pairs"), 1, "LLM görüş-sonuç çifti"),
        ("gate_calibration", _cal("gate_calibration.json", "n_measured"), 1, "kapı meta-ölçümü"),
    ]
    # AYNA ÜRETKENLİĞİ (adapters.alpaca denetimi 2026-07-21): motor plan silahlandırıyor ama aynaya
    # tek emir gitmiyorsa bu 'sabır' değil ARIZADIR — eskiden hiçbir şey söylemezdi. Yalnız ayna
    # açıkken sorulur; iç broker modunda soru anlamsız (yanlış alarm üretmesin).
    from . import config as _cfg
    if getattr(_cfg, "BROKER", "internal") == "alpaca_paper":
        _pf = store.read_json("portfolio.json", {}) or {}
        if _pf.get("armed") or _pf.get("alpaca_submitted"):
            checks.append(("broker_mirror", len(_pf.get("alpaca_submitted") or []), 1,
                           "aynaya iletilmiş emir"))
    starved, waiting, ok = [], [], 0
    # ÜYELİK KAYNAĞI (adapters.constituents denetimi 2026-07-21): modül üç denetim boyunca düzeltildi
    # ama HİÇBİR üretim yolu onu çağırmıyordu — "koşuyor mu" değil "ÜRETİYOR mu" sorusunun en saf
    # örneği. Artık gerçek bir tüketicisi var (evren sapması) ve üretmediğinde bunu SÖYLÜYOR.
    try:
        from .adapters import constituents as _con
        _h = _con.health()
        if _h.get("ok") is False:
            starved.append({"name": "sp500_membership",
                            "note": f"üyelik kaynağı üretmiyor — {str(_h.get('error'))[:60]}"})
    except Exception as e:                       # dedektörün KENDİ arızası da sessiz kalmasın
        starved.append({"name": "sp500_membership", "note": f"dedektör hatası: {type(e).__name__}"})
    # KAZANÇ TAKVİMİ (earnings denetimi 2026-07-21): takvimde GELECEK tarih kalmazsa karartma guard'ı
    # herkes için sessizce KAPANIR — "sert guard" görünür, hiçbir şey engellemez.
    try:
        from . import earnings as _earn
        _cov = _earn.coverage()
        if _cov.get("inert"):
            starved.append({"name": "earnings_calendar",
                            "note": f"gelecek tarih yok (son: {_cov.get('max_date')}) — karartma guard'ı fiilen kapalı"})
    except Exception as e:
        from . import obs
        obs.warn("detector_subcheck_failed", check="earnings_calendar", error=f"{type(e).__name__}: {e}")
        starved.append({"name": "earnings_calendar", "note": f"KONTROL ÇALIŞMADI ({type(e).__name__}) — "
                        "karartma guard'ının durumu BİLİNMİYOR"})
    # VERİ KAYNAĞI ÜRETKENLİĞİ (adapters.data denetimi 2026-07-21): FMP anahtarı VAR ama seri
    # dönmüyorsa (429/kota) zincir sessizce Cboe'ye düşer ve TÜM bar geçmişi başka bir düzeltme
    # ölçeğine kayar. 'anahtar var' ile 'veri üretiyor' aynı şey değildir.
    try:
        from .adapters import fmp as _fmp
        if _fmp.available():
            _h = _fmp.health()
            if _h["calls"] and _h["ok"] is False:
                starved.append({"name": "fmp_source",
                                "note": f"anahtar var ama üretmiyor — {_h['last_error'][:60]}"})
    except Exception as e:
        from . import obs
        obs.warn("detector_subcheck_failed", check="fmp_source", error=f"{type(e).__name__}: {e}")
        starved.append({"name": "fmp_source", "note": f"KONTROL ÇALIŞMADI ({type(e).__name__}) — "
                        "veri kaynağının üretkenliği BİLİNMİYOR"})
    # MEKANİZMA SAĞLIĞI (2026-07-22): üretkenlik dedektörü "çıktı var mı" diye sorar; bir mekanizma
    # her çağrıda İSTİSNA atıyorsa çıktı da yoktur ama sebebi görünmezdi. Canlıda öz-değerlendirme ve
    # haftalık beceri revizyonu 860 kez üst üste çöktü ve pano "dikkat maddesi yok" gösterdi —
    # "sakin sistem" ile "ölü mekanizma" ayırt edilemiyordu. self_review.json artık kendi sağlığını
    # yazıyor; burada okunup AÇ (starved) sayılır.
    try:
        _mech = (store.read_json("self_review.json", {}) or {}).get("mechanisms") or {}
        for _mname, _mh in _mech.items():
            if isinstance(_mh, dict) and _mh.get("ok") is False:
                starved.append({"name": _mname,
                                "note": f"mekanizma İSTİSNA atıyor ({_mh.get('streak', '?')} kez üst "
                                        f"üste): {str(_mh.get('error') or '')[:70]}"})
    except Exception as e:
        from . import obs
        obs.warn("mechanism_health_read_failed", error=f"{type(e).__name__}: {e}")

    for name, n, need, note in checks:
        if n is None or n == 0:
            starved.append({"name": name, "note": note})          # HİÇ üretmemiş → hata şüphesi
        elif n < need:
            waiting.append({"name": name, "have": n, "need": need, "note": note})
        else:
            ok += 1
    return {"starved": starved, "waiting": waiting, "ok": ok, "total": len(checks)}


def conservation_report() -> dict:
    """#3 KORUNUM: giren her plan KAYITLI bir terminal duruma ulaşmalı — işleme dönüştü, kapıda
    reddedildi (NO_GO), ya da düşüşü OLAYLA kaydedildi. Hiçbirine uymayan plan = SESSİZ KAYIP
    (P4 buharlaşması ve seans atlaması tam olarak buydu; hiçbir alarm ötmemişti)."""
    plans = store.read_jsonl("trade_plans.jsonl")
    if not plans:
        return {"plans": 0, "unexplained": 0, "rows": []}
    traded = {str(t.get("plan_id")) for t in store.read_jsonl("trades.jsonl")}
    # düşüşü olayla kaydedilmiş planlar (taşıma/veto/broker reddi/süresi doldu)
    dropped = set()
    for e in store.read_jsonl("events.jsonl", limit=8000):
        ev = e.get("event") or ""
        if ev in ("armed_expired_no_bar", "armed_no_bar_carried", "llm_veto_strip",
                  "regressive_session_refused"):
            if e.get("plan_id"):
                dropped.add(str(e["plan_id"]))
        # BROKER REDDİ — GERÇEK İMZA (K1, 2026-07-30). Bu süzgeç `failed_broker_rejection` adlı bir
        # OLAY arıyordu; o ad hiçbir zaman olay olarak yayınlanmadı — loop.py onu yalnız plan ALANI
        # (pl['broker_status']) olarak yazar, yayılan olay ise obs.alarm(BROKER_REJECT). Dal ölüydü:
        # canlıdaki 4 red (UNP/NSC/TMO/RTX) `dropped` kümesine hiç giremiyor, korunum raporu onları
        # AÇIKLANAMAYAN sayıyor ya da cf no_fill'e yanlış sınıflıyordu. obs.alarm `alarm` alanını
        # fields'a koyar (obs.py:142), event adı ise "BROKER_REJECT <mesaj>" — imza budur.
        elif e.get("alarm") == "BROKER_REJECT" and e.get("plan_id"):
            dropped.add(str(e["plan_id"]))
    last = str((store.read_json("portfolio.json", {}) or {}).get("last_date") or "")
    # cf defteri "dolar mıydı?" sorusunu bilir: tetiği hiç gelmemiş plan (no_fill*) MEŞRU terminaldir.
    # Bu ayrım olmadan dedektör kurt masalı anlatır (43 bayrak → 12'si meşru no_fill çıktı).
    cf_fate = {}
    try:
        from . import counterfactual as _cf
        for r in _cf.resolved_rows(entered_only=False, include_near_miss=True):
            cf_fate[(str(r.get("date")), str(r.get("ticker")))] = str(r.get("status") or "")
    except Exception as e:
        # cf kaderi okunamazsa "neden işleme dönüşmedi" sorusu cevapsız kalır ve korunum raporu
        # sağlam planları AÇIKLANAMAYAN diye işaretler — ölçüm arızası, bulgu kılığına girer.
        from . import obs
        obs.warn("conservation_cf_fate_unavailable", error=f"{type(e).__name__}: {e}",
                 detail="açıklanamayan plan sayısı ŞİŞMİŞ olabilir")
    # CANLI dönem sınırı: replay tohumu planları trade_plans.jsonl'a yazar ama HİÇ olay kaydı tutmaz,
    # dolayısıyla "neden silahlanmadı" (seans-içi arming rekabeti) orada yapısal olarak görünmez.
    # Ölçüldü (2026-07-21): 31 bayrağın 30'u replay dönemiydi, 1'i GERÇEK canlı sızıntıydı (GS 07-14).
    # Bu yüzden sayı DÖNEME göre ayrılır: canlı = eyleme dönüşür sinyal, replay = kayıt körlüğü.
    live_start = ""
    for e in store.read_jsonl("events.jsonl", limit=20000):
        if e.get("event") == "daily_cycle" and e.get("date"):
            live_start = str(e["date"])
            break
    unexplained, replay_era, no_fill = [], 0, 0
    for p in plans:
        pid, d = str(p.get("id")), str(p.get("date") or "")
        if pid in traded or pid in dropped:
            continue
        if p.get("gate_verdict") == "NO_GO":            # kapıda öldü — terminal ve kayıtlı
            continue
        if last and d >= last:                          # hâlâ taze (bugünün planı) — henüz terminal değil
            continue
        if cf_fate.get((d, str(p.get("ticker"))), "").startswith("no_fill"):
            no_fill += 1                                # tetik hiç gelmedi — MEŞRU, kayıp değil
            continue
        if live_start and d < live_start:
            replay_era += 1                             # replay: olay defteri yok — körlük, sızıntı değil
            continue
        unexplained.append({"id": pid, "date": d, "ticker": p.get("ticker"),
                            "verdict": p.get("gate_verdict")})
    # HÜKMÜNÜ SÖYLE. Bu rapor `ok` alanı DÖNDÜRMÜYORDU; diğer altı dedektör döndürüyor. Panoda ve
    # her toplayıcıda `ok=None` görünüyordu — "geçti" de değil "kaldı" da değil, sessizlik. Hüküm
    # vermeyen bir dedektör, bakanı hiçbir şey öğrenmeden geçirir (2026-07-22).
    return {"ok": not unexplained,
            "plans": len(plans), "traded": len(traded & {str(p.get("id")) for p in plans}),
            "no_fill": no_fill, "replay_era": replay_era, "live_start": live_start,
            "unexplained": len(unexplained), "rows": unexplained[:8]}


FINGERPRINT_FILE = "bars_fingerprint.json"


def determinism_report(persist: bool = False) -> dict:
    """#3 DETERMİNİZM: barlar, wf-önbelleği geçersiz kılınMADAN sessizce değişti mi?

    ÖNEMLİ AYRIM (3. iterasyon — dedektörün kurt masalı anlatmaması için): bar dosyasının BÜYÜMESİ
    normal tazelemedir (bugünün mumu eklenir) ve walk-forward penceresi GEÇMİŞTE bittiği için sonucu
    DEĞİŞTİRMEZ → önbellek hâlâ geçerli, alarm yok. Tehlikeli olan GEÇMİŞİN yeniden yazılması: dosya
    KÜÇÜLÜR ya da yeniden-ölçeklenir (split/temettü düzeltmesi) — o zaman önbelleklenmiş walk-forward
    artık var olmayan barlara aittir. Bu yüzden yalnız KÜÇÜLME/kayıp dosya ihlal sayılır.
    persist: TABANI GÜNCELLE (2026-07-22 bulgusu). Bu üç dedektör "önceki durum ile şimdiki durum"
    kıyaslar; kıyası yapan her çağrı tabanı da yazarsa, iki okuma ARASINDA olan bir gerileme
    sessizce yeni tabana emilir. Canlıda tam bu oluyordu: `/api/diagnostics` salt-okunur bir GET
    ucu ama her pano yenilemesinde tabanı yeniden yazıyordu — yani PANOYU AÇIK TUTMAK dedektörü
    körleştiriyordu. Artık taban yalnız günlük döngü/zamanlayıcı turunda (persist=True) ilerler;
    okuma yolları yalnız kıyas yapar.
    """
    from . import config
    try:
        sizes = {p.name: p.stat().st_size for p in config.BARS.glob("*.csv")}
    except Exception:  # sessiz-yutma: sonuç KAYDA GEÇİYOR — dönen detay "kontrol atlandı" der, "temiz" demez
        return {"ok": True, "detail": "bar dizini okunamadı — kontrol atlandı"}
    rev = int(store.read_json("wf_cache_rev.json", {}).get("rev", 0))
    prev = store.read_json(FINGERPRINT_FILE, None)
    if persist:
        store.write_json(FINGERPRINT_FILE, {"sizes": sizes, "rev": rev, "n_files": len(sizes)})
    if not prev or not prev.get("sizes"):
        return {"ok": True, "detail": "ilk anlık görüntü kaydedildi", "n_files": len(sizes)}
    old = prev["sizes"]
    shrunk = [n for n, sz in old.items() if n in sizes and sizes[n] < sz]   # GEÇMİŞ yeniden yazıldı
    vanished = [n for n in old if n not in sizes]                           # dosya kayboldu
    grew = sum(1 for n, sz in old.items() if n in sizes and sizes[n] > sz)  # normal ekleme (zararsız)
    rev_bumped = rev > int(prev.get("rev", 0))
    if (shrunk or vanished) and not rev_bumped:
        return {"ok": False, "silent_bar_mutation": True, "shrunk": shrunk[:5], "vanished": vanished[:5],
                "detail": f"{len(shrunk)} bar dosyası KÜÇÜLDÜ/{len(vanished)} kayboldu ama wf-revizyon "
                          f"{rev} sabit — önbelleklenmiş walk-forward'lar yok olan barlara ait"}
    return {"ok": True, "appended": grew, "shrunk": len(shrunk), "rev_bumped": rev_bumped}


# =============================================================================================
# 7. DESEN — MAKULLÜK / EŞLEŞME (2026-07-21)
#
# Neden var: 2026-07-21'de motorun evrenin %18'inde karar verdiği bulundu. HER BİLEŞEN DOĞRUYDU —
# tazelik koruması, seans seçimi, tarama; üçünün de testi geçiyordu. Hata BİLEŞİMDEYDİ: doğru
# parçalar yanlış bir sistem sonucu üretiyordu. İlk altı desen bileşen bazlıdır ("üretiyor mu,
# koruyor mu, deterministik mi") ve bu sınıfı yapısal olarak göremez.
#
# Bu dedektör tek bir soruyu sorar: **üretilen sayı MAKUL mü?** — yani canlı oran, aynı yasanın
# backtest'te ürettiği orana benziyor mu, ve "0" bir sonuç mu yoksa bir arıza mı?
# Yalnız GÖZLEM: hiçbir kararı değiştirmez, yalnız "bu sayı beklenene benzemiyor" der.
# =============================================================================================

# NOT (2026-07-21): defter şeması artık burada DEĞİL — meridian/ledgers.py'deki yazılı sözleşmede.
# İki yerde tanımlamak, tam da bu denetimin bulduğu "aynı yasanın iki uygulaması" hatasını üretirdi.

PARITY_MIN_SESSIONS = 8        # bu kadar döngü birikmeden makullük yorumu yapılmaz (gürültü)
PARITY_MIN_COVERAGE = 0.90     # işlenen seans, evrenin en az bu oranını görmüş olmalı
PARITY_DRY_SESSIONS = 10       # tam kapsamalı bu kadar seansta HİÇ aday yoksa şüpheli


def events_since(days: int, limit_hint: int | None = None) -> list[dict]:
    """Olay defterinin TARİH tabanlı penceresi (K1, 2026-07-30).

    NEDEN SATIR LİMİTİ YETMİYOR: `limit=4000` nominal hacimde (~1.700/gün) ~2,3 gün demekti; ama
    `hotstate_down` seli defterin %60'ını tek olaya çevirdi (canlı sayım 2026-07-30: 26.319 satırın
    15.863'ü) ve pencere ~16 SAATE düştü. Sonuç: satır-limitli her tüketici geçmişe kör oldu —
    `universe_coverage` kontrolü "işlenen seanslar tam evreni gördü" diyordu, oysa aynı defterde
    164 atlanmış seans yazılıydı. Gürültü, dedektörleri kapatan bir saldırı yüzeyine dönüştü.

    MALİYET ~SIFIR: `store.read_jsonl` dosyanın TAMAMINI okuyup sonra dilimliyor (store.py:182-200),
    yani satır limiti I/O tasarrufu ETMİYORDU — yalnız görüş alanını daraltıyordu. Burada aynı okuma
    yapılır, filtre ts üzerinedir. `limit_hint` yalnız çok uzun defterlerde üst sınır olarak durur."""
    since = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=days)).isoformat()
    rows = store.read_jsonl("events.jsonl", limit=limit_hint)
    # ts YOKSA SATIR ATILMAZ: damgasız bir satırı pencere dışı saymak, ölçülemeyen şeyi "yok"
    # saymak olurdu. Damgasızlar korunur; sıralama ISO-8601 sözlüksel kıyasıyla yapılır (obs.py
    # tek yazar ve hep aynı biçimde yazar: isoformat(timespec="seconds"), hepsi +00:00).
    return [e for e in rows if not e.get("ts") or str(e["ts"]) >= since]


def parity_report() -> dict:
    """Canlı üretim oranları ile beklenen oranların kıyası. Her satır: {check, ok, detail}."""
    from . import config as _cfg, notify as _nt
    rows = []
    cycles = [e for e in store.read_jsonl("events.jsonl", limit=4000)
              if e.get("event") == "daily_cycle"]
    recent = cycles[-30:]

    # 1) EVREN KAPSAMASI — kararların alındığı seans evreni gerçekten görüyor mu?
    #    (bulunan hatanın ta kendisi: %18'lik yanlı kesitte karar)
    # TARİH TABANLI PENCERE (K1): satır limiti bu kontrolü kör ediyordu — bkz. events_since().
    _cov_ev = events_since(30)
    defer = [e for e in _cov_ev
             if e.get("event") in ("session_deferred_for_coverage", "universe_coverage_low")]
    low = [e for e in defer if e.get("event") == "universe_coverage_low"]
    # SEANS ATLAMA — DEDEKTÖRÜN KÖR NOKTASI KAPATILIYOR (K1, 2026-07-30). Bu kontrol yalnız
    # `universe_coverage_low`a bakıyordu ve o olay canlıda 0 kez ateşlenmiş; bu yüzden ok=True
    # diyordu. Oysa `session_bar_never_published` 164 kez düşmüş: motor 164 seansı kapsama
    # yüzünden TERK ETMİŞ ve dedektör "işlenen seanslar tam evreni gördü" diye rapor veriyordu.
    # İKİ İMZA BİRDEN okunur: tarihsel 164 satır `event` adıyla yazıldı (warn dönemi), K1'den
    # sonraki satırlar DATA_QUALITY alarmı olduğu için adı `kind` alanında taşıyor. Yalnız yeni
    # imzayı okumak dedektörü geçmişe kör bırakırdı — `failed_broker_rejection` dersinin tersi.
    skipped = [e for e in _cov_ev
               if e.get("event") == "session_bar_never_published"
               or e.get("kind") == "session_bar_never_published"]
    _cov_ok = not low and not skipped
    if skipped:
        _det = (f"{len(skipped)} seans evren kapsaması yetersiz olduğu için ATLANDI (son: "
                f"{skipped[-1].get('session')} %{100*float(skipped[-1].get('universe_coverage') or 0):.0f}) "
                f"— kaynak yayınlamıyor")
    elif low:
        _det = (f"{len(low)} seansta evren kapsaması yetersizdi (son: "
                f"{low[-1].get('date')} %{100*float(low[-1].get('coverage', 0)):.0f})")
    else:
        _det = "işlenen seanslar tam evreni gördü"
    rows.append({"check": "universe_coverage", "ok": _cov_ok, "detail": _det})

    # 2) TARAMA VERİMİ — tam kapsamalı seanslarda hiç aday çıkmıyorsa bu 'seçicilik' değil şüphe
    if len(recent) >= PARITY_MIN_SESSIONS:
        dry = sum(1 for e in recent[-PARITY_DRY_SESSIONS:] if not e.get("candidates"))
        n = min(len(recent), PARITY_DRY_SESSIONS)
        rows.append({"check": "scan_yield", "ok": dry < n,
                     "detail": f"son {n} döngünün {dry}'inde HİÇ aday yok"
                               + (" — tarama yolu şüpheli" if dry >= n else "")})

    # 3) KANIT KAYNAĞI — kalibrasyon yalnız SİMÜLASYONDAN besleniyorsa öğrenme gerçeğe değmiyor
    sc = store.read_json("score_calibration.json", {}) or {}
    n_real, n_cf = sc.get("n_real"), sc.get("n_cf")
    if n_real is not None:
        trades = _n_jsonl("trades.jsonl")
        rows.append({"check": "evidence_source", "ok": not (trades >= 20 and not n_real),
                     "detail": f"kalibrasyon: gerçek {n_real} / simüle {n_cf} (kapalı işlem {trades})"
                               + (" — gerçek işlemler kalibrasyona GİRMİYOR" if trades >= 20 and not n_real else "")})

    # 4) AYNA EŞLEŞMESİ — ayna açıkken silahlı plan çıkıyor ama emir gitmiyorsa kopukluk var
    if getattr(_cfg, "BROKER", "internal") == "alpaca_paper":
        pf = store.read_json("portfolio.json", {}) or {}
        armed_seen = any(e.get("armed") for e in recent)
        sent = len(pf.get("alpaca_submitted") or [])
        rows.append({"check": "mirror_parity", "ok": not (armed_seen and sent == 0),
                     "detail": f"silahlı plan görüldü={armed_seen}, aynaya giden emir={sent}"})

    # 5) CF SADAKATİ — birleşme MÜMKÜN mü? ("veri birikmiyor" ile "anahtar tutmuyor" AYRI şeyler)
    #    Canlıda bulundu: cf_fidelity plan_id'yi `P-YYYY-MM-DD-TICKER` diye ayrıştırıyordu ama
    #    replay'den tohumlanmış işlemler `P00140` şemasındaydı → 90 işlemin 90'ı da elendi ve
    #    mekanizma SONSUZA KADAR None döndü. Üretkenlik dedektörü "aç" diyordu; NEDEN'i söylemiyordu.
    trades_all = store.read_jsonl("trades.jsonl")
    joinable = sum(1 for t in trades_all if str(t.get("plan_id") or "").startswith("P-")
                   and len(str(t.get("plan_id")).split("-")) >= 5)
    fid = store.read_json("cf_fidelity.json", None)
    if len(trades_all) >= 10:
        ok = joinable > 0
        rows.append({"check": "cf_fidelity_join", "ok": ok,
                     "detail": f"{joinable}/{len(trades_all)} işlem cf ile birleştirilebilir kimlik taşıyor"
                               + ("" if ok else " — ANAHTAR TUTMUYOR: sim↔gerçek karşılaştırması hiç kurulamaz")})
        if ok and fid is not None and fid.get("n", 0) >= 10:
            good = bool(fid.get("fidelity_ok"))
            rows.append({"check": "cf_fidelity_quality", "ok": good,
                         "detail": f"n={fid.get('n')} korelasyon={fid.get('corr')} sapma={fid.get('mean_diff_r')}R"
                                   + ("" if good else " — simülasyon gerçeğe UYMUYOR; cf-beslemeli her "
                                                      "kalibrasyon (gölge model, silahlanma, near-miss) bu "
                                                      "iskontoyla okunmalı")})

    # 6) LLM GÖRÜŞ↔SONUÇ — damga düşüyor ama çift birikmiyor mu? (join/kapanış kopukluğu)
    lc = store.read_json("llm_calibration.json", None)
    if lc is not None:
        stamped = sum(1 for pl in store.read_jsonl("trade_plans.jsonl") if pl.get("llm_opinion"))
        pairs = int(lc.get("n_pairs") or 0)
        closed_ids = {str(t.get("plan_id")) for t in trades_all}
        stamped_closed = sum(1 for pl in store.read_jsonl("trade_plans.jsonl")
                             if pl.get("llm_opinion") and str(pl.get("id")) in closed_ids)
        ok = not (stamped_closed >= 5 and pairs == 0)
        rows.append({"check": "llm_pair_join", "ok": ok,
                     "detail": f"görüş damgalı plan={stamped} (kapanmış {stamped_closed}) · çift={pairs}"
                               + ("" if ok else " — kapanan işlemler görüş çiftine dönüşmüyor")})
        rule_n = 30
        if lc.get("promoted") and pairs < rule_n:
            rows.append({"check": "llm_promotion_rule", "ok": False,
                         "detail": f"terfi işaretli ama yalnız {pairs} çift var (kural >={rule_n})"})

    # 7) DEFTER ŞEMASI — tüketicinin İHTİYAÇ DUYDUĞU alanlar satırlarda gerçekten var mı?
    #    Canlıda bulundu: trades.jsonl satırlarında `setup` ve `score` YOKTU (eski şemayla
    #    tohumlanmış defter), oysa broker ikisini de yazıyor. Hata sessiz: `.get()` None döner,
    #    satır ilgili kalibrasyondan ELENİR. "gerçek 0 / simüle 241" tam olarak bunun sonucuydu.
    #    Kaynak: meridian/ledgers.py — YAZILI sözleşme (zorunlu alanlar + anahtar biçimi + izinli
    #    yazarlar). Dedektör sözleşmeyi tekrar TANIMLAMAZ, ona bakar (tek kaynak).
    from . import ledgers as _lg
    for _fname in _lg.CONTRACTS:
        _v = _lg.validate_live(_fname)
        if _v["rows"] < 5:
            continue
        rows.append({"check": f"ledger_contract:{_fname.split('.')[0]}", "ok": _v["ok"],
                     "detail": (f"{_fname}: {_v['violations']} — bu satırlar ilgili kalibrasyondan "
                                f"SESSİZCE elenir") if not _v["ok"]
                               else f"{_fname}: sözleşmeye uyuyor ({_v['rows']} satır)"})
    _wv = _lg.writer_violations()
    if _wv:
        rows.append({"check": "ledger_writers", "ok": False,
                     "detail": f"beyan edilmemiş yazar/eksik beyan: {_wv}"})

    # 7c-bis) OLAY DEFTERİNİ TEK OLAYIN ELE GEÇİRMESİ (K1, 2026-07-30) — META DEDEKTÖR.
    #     Canlı bulgu: `hotstate_down` defterin %60'ı (26.319 satırın 15.863'ü). Zarar tek bir
    #     gürültüden çok daha büyük: PENCERELİ HER TÜKETİCİ köreldi — parity (4000), notify.inbox
    #     (4000), selfreview (4000), otonomi merdiveni (400). `universe_coverage` bu yüzden "tam
    #     evreni gördü" diyordu, oysa aynı defterde 164 atlanmış seans yazılıydı. Yani gürültü,
    #     dedektörleri kapatan bir yüzeye dönüştü ve bunu ölçen hiçbir şey yoktu.
    #     Bu satır o sınıfı KALICI olarak sorar: bir olay defteri domine ediyorsa, o olayın kendisi
    #     onarılana kadar tüm pencereli ölçümlerin şüpheli olduğu GÖRÜNÜR olur.
    _dom_win = events_since(2)
    if len(_dom_win) >= 500:
        _counts: dict[str, int] = {}
        for e in _dom_win:
            _counts[str(e.get("event") or "?")] = _counts.get(str(e.get("event") or "?"), 0) + 1
        _top, _n = max(_counts.items(), key=lambda kv: kv[1])
        _share = _n / len(_dom_win)
        # %40: bu eşiğin ALTINDA tek olayın 4000-satırlık pencereyi 1 günün altına düşürmesi
        # mümkün değil (nominal hacim ~1.700/gün). Üstünde ise pencereli tüketiciler ölçtüklerini
        # sandıkları tarihi görmüyor demektir.
        rows.append({"check": "event_ledger_domination", "ok": _share < 0.40,
                     "detail": (f"son 2 günün %{100*_share:.0f}'i tek olay: `{_top}` ({_n}/"
                                f"{len(_dom_win)}) — PENCERELİ tüm tüketiciler (parite/inbox/"
                                f"selfreview/otonomi) bu kadar daralmış bir tarih görüyor")
                     if _share >= 0.40 else
                     f"en sık olay `{_top}` defterin %{100*_share:.0f}'i — pencereler sağlam"})

    # 7c-ter) SÜREN REDIS KESİNTİSİ ALARMA TÜRETİLİR (K1, 2026-07-30).
    #     `hotstate_down` her flap'te yeniden ateşleniyor (kenar bekçisi `ok is not False`, ve her
    #     başarılı işlem ok'u True'ya alıyor) ama HİÇBİR alarm jetonu türetilmiyordu: 15.863 uyarı,
    #     0 bildirim. hotstate `EXPECTED` nabız listesinde de yok — orada olması hotstate.py'nin
    #     `beat()` çağırmasını gerektirir, o yüzden kesinti burada OLAY DEFTERİNDEN türetiliyor.
    #     streamhealth aynı sorunu DOWN_REASSERT_S kısıtlamasıyla çözdü; hotstate o deseni almadı
    #     (kısıtlamanın kendisi hotstate.py'de yapılmalı — bu turun kapsamı dışında, bkz. K1-NOTU).
    _hot_down = [e for e in events_since(1) if str(e.get("event")) == "hotstate_down"]
    if _hot_down:
        rows.append({"check": "hotstate_sustained_down", "ok": False,
                     "detail": (f"son 24 saatte {len(_hot_down)} `hotstate_down` — Redis sıcak "
                                f"katmanı flap'te; son hata: "
                                f"{str(_hot_down[-1].get('error') or '?')[:80]}. İntraday Faz 2-4 "
                                f"zinciri bu katmana bağlı")})

    # 7d-bis) ÜÇ DAMGA — LOOK-AHEAD İDDİASININ CANLI DENETÇİSİ (K1, 2026-07-30).
    #     intraday_shadow.py:241 "as_of >= close_ts sonradan denetlenebilir" diye söz veriyor;
    #     bugüne kadar o denetimi yapan tek şey fixture'lı birim testlerdi. Diskteki GERÇEK
    #     satırlara bakan hiçbir canlı dedektör yoktu — yani iddia test ortamında doğru, sahada
    #     DENETİMSİZDİ. Kontrol UCUZ (iki alan kıyası) ve tam olarak Faz 5 kanıtının dayandığı
    #     şeyi korur: karar anı barın KAPANIŞINDAN önce olamaz.
    for _r in intraday_stamp_report()["rows"]:
        rows.append({"check": f"intraday_damga:{_r['ledger'].split('.')[0]}", "ok": _r["ok"],
                     "detail": _r["detail"]})

    # 7b) YENİDEN HESAP — aynı büyüklüğü BAĞIMSIZ iki yoldan hesapla, tut(may)an farkı göster.
    #     Canlı hatayı bulan yöntem tam buydu: döngü "aday: 0" diyordu, aynı barlar doğrudan
    #     tarandığında 43 sinyal çıkıyordu. Tek bir yol asla kendi hatasını göremez.
    from . import recompute as _rc
    for _r in _rc.report()["rows"]:
        rows.append({"check": f"yeniden_hesap:{_r['check']}", "ok": _r["ok"],
                     "detail": f"{_r['detail']}  [A={_r['a_yol']} · B={_r['b_yol']}]"})

    # 7c) ELEME MUHASEBESİ — hangi satır NEDEN düştü? "veri yok" ile "veri elendi" AYRI şeylerdir.
    #     Defteri sieve.py yazıyor; burada yalnız okunur. Yazan var, okuyan yoksa kanıt üretilip
    #     tüketilmemiş olur — bu denetimin bulduğu hata sınıfının kendisi.
    from . import sieve as _sv
    for _v in _sv.report()["violations"]:
        rows.append({"check": f"eleme:{_v['stage']}:{_v['rule']}", "ok": False,
                     "detail": _v["detail"]})

    # 7d) TÜKETİCİSİ OLMAYAN ARTEFAKT — "üretilip tüketilmeyen kanıt" sınıfının canlı dedektörü.
    #     Yedi desen raporunun kendisi de bir dönem hiçbir panelde okunmuyordu; bu satır o sınıfı
    #     kod düzeyinde sürekli sorar (statik tarama, ucuz).
    try:
        from . import codelaw as _cl
        _ag = _cl.artifact_graph()
        _orphan = [a for a, info in (_ag.get("artifacts") or {}).items()
                   if info.get("unread") and a not in getattr(_cl, "DECLARED_SINKS", {})]
        if _orphan:
            # ARTEFAKT KİMLİĞİ SATIRDA TAŞINIR (K1, 2026-07-30): alarm jetonu bu satırdan
            # türetiliyor ve `parity:artifact_unread` TEK genel jetondu — mandal (integrity_alarmed)
            # dolu kaldığı sürece YENİ bir artefakt okumasız kalsa hiç alarm üretilmiyordu. Akranları
            # (stale:{artifact}, regress:{field}, clobber:{file}.{field}) artefakt-başına jeton
            # taşıyor; `orphans` alanı check_integrity_and_alarm'a aynı disiplini kurma imkânı verir.
            # Pano tarafı DEĞİŞMEZ: check adı ve detail metni aynı kaldı, tek satır olarak çizilir.
            rows.append({"check": "artifact_unread", "ok": False,
                         "orphans": sorted(_orphan),
                         "detail": f"{len(_orphan)} artefakt yazılıyor ama hiçbir modül okumuyor: "
                                   f"{', '.join(sorted(_orphan)[:5])} — üretilip tüketilmeyen kanıt"})
    except Exception as e:
        from . import obs
        obs.warn("artifact_graph_failed", error=f"{type(e).__name__}: {e}")

    # 7e) BEYİN ERİŞİLEBİLİRLİĞİ — kota dolduğunda sistem deterministik önericiye düşer ve BUNU
    #     kimse söylemezdi: canlıda üç gün boyunca 45 kez 429 + 92 kez "boş yanıt" üretti, pano
    #     yalnız "beyin: nous" yazıyordu. Düşüş MEŞRU bir davranıştır; GÖRÜNMEZ olması değil.
    try:
        from . import hermes_runtime as _hr
        _hs = _hr.status() or {}
        _av = _hs.get("brain_availability") or {}
        # ÖLÇÜM ARIZASI ≠ ÖLÇÜLECEK ŞEY YOK (2026-07-26). Boş sözlük "hermes hiç koşmamış" demektir
        # ve o hâlde satır ÇIKMAZ (taze kurulumda kurt masalı yasağı + mutasyon tabanının temizliği).
        # `error` ise ölçümün kendisinin düştüğünü söyler: sessiz kalmak, körlüğü sağlıkla aynı
        # göstermek olurdu — dedektörün öldüğü an tam da hiçbir şey duyulmayan andır.
        if _av.get("error"):
            rows.append({"check": "brain_availability", "ok": False,
                         "detail": f"erişilebilirlik ölçümü ÇALIŞMADI ({_av['error']}) — hangi "
                                   f"beynin hazır olduğu BİLİNMİYOR; bozunma tespiti kör"})
        elif _av:
            _ready = [n for n, a in _av.items() if (a or {}).get("ready")]
            _cool = {n: round((a or {}).get("cooling_s") or 0) for n, a in _av.items()
                     if (a or {}).get("cooling_s")}
            rows.append({"check": "brain_availability", "ok": bool(_ready),
                         "detail": (f"hazır sağlayıcı: {', '.join(_ready)}" if _ready else
                                    "HİÇBİR LLM beyni hazır değil — öneri katmanı deterministik "
                                    "önericiye düştü (meşru ama körlemesine çalışmamalı)")
                                   + (f" · soğumada: {_cool}" if _cool else "")})
        # 7e-2) ZİNCİR YEDEKLİ Mİ — "hazır sağlayıcı: nous, gemini" satırı bir SAYIM yapıyordu ama
        #       o sayım AD sayıyordu, KOTA değil. Canlıda iki ad tek modele (gemini-3.5-flash)
        #       gidiyordu: yedeklilik raporlanıyor, gerçekte yoktu. Bağımsız uç sayısı ÖLÇÜLMEDİĞİ
        #       için burada da üretilmez; yalnız ölçülen olgu (model kimliği eşitliği) konuşur.
        #       Tek beyin varken satır ok=True kalır — kurt masalı yasağı.
        _ch = _hs.get("brain_chain") or {}
        _same = _ch.get("same_model_ids") or []
        if _ch.get("error"):        # ölçüm arızası — yukarıdaki `_av` ile aynı ayrım
            rows.append({"check": "brain_chain_distinct", "ok": False,
                         "detail": f"zincir ölçümü ÇALIŞMADI ({_ch['error']}) — yedeklilik "
                                   f"denetimi kör"})
        elif _ch:
            _rdy = _ch.get("ready") or []
            _mode, _prov = _ch.get("nous_mode"), _ch.get("agent_config_provider")
            # İKİNCİ ÖLÇÜLEN OLGU: PAYLAŞILAN ÜST-AKIŞ (2026-07-26). Model kimliği eşitliği tek
            # yakalama yolu değildi — yerel ajan modunda nous'un model kimliği ÖLÇÜLEMEZ (None) ve
            # o hâlde `same_model_ids` boş kalır, satır yeşile döner. Ama `~/.hermes/config.yaml`
            # içindeki `model.provider` OKUNAN bir olgudur: orada "gemini" yazıyorsa zincirin nous
            # ayağı ile gemini ayağı AYNI kotaya bakıyor demektir. Bu bir çıkarım değil; canlıda
            # yedek sağlayıcı, tükenmiş kimliğin ikinci adıydı ve elbette 429'u absorbe edemedi.
            _shared = bool(_mode == "local_agent" and _prov and _prov != "nous"
                           and _prov in _rdy and "nous" in _rdy)
            _kunye = f" · nous modu: {_mode or '—'} · ajan sağlayıcısı: {_prov or '—'}"
            if _same:
                _d = (f"{_same} AYNI model kimliğiyle çağrılıyor "
                      f"({_ch.get('models', {}).get(_same[0][0])}) — zincirin yedekli "
                      f"olduğu ÖLÇÜLMEMİŞTİR; tek kota tüm ayakları birden düşürür. "
                      f"Operatör kaldıracı: Claude anahtarı ekle ya da NOUS_MODEL'i "
                      f"Google dışı bir modele çevir.")
            elif _shared:
                _d = (f"yerel ajan {_prov} üst-akışına kurulu — {_prov} ile aynı kota; iki ayak "
                      f"tek kimliğe bakıyor ve yedeklilik ÖLÇÜLMEMİŞTİR. Operatör kaldıracı: "
                      f"ajanın sağlayıcısını değiştir ya da bağımsız bir anahtar ekle.")
            else:
                _d = (f"model kimlikleri ayrık ({_ch.get('models')}) · bağımsız uç sayısı "
                      f"ölçülmüyor")
            rows.append({"check": "brain_chain_distinct",
                         "ok": not ((len(_rdy) > 1 and _same) or _shared),
                         "detail": _d + _kunye})
    except Exception as e:
        from . import obs
        obs.warn("brain_availability_check_failed", error=f"{type(e).__name__}: {e}")

    # 7f) ALARM TESLİMİ — "alarm yazıldı" ile "alarm ULAŞTI" ayrı şeylerdir. Bütün gün kurulan
    #     dedektörler alarm üretiyor; kanal bağlı değilse hiçbiri operatöre gitmez ve bu boşluk
    #     sessizdi (canlıda 23 MECHANISM_STALE yazıldı, 0'ı teslim edildi).
    _und = store.read_json("notify_undelivered.json", {}) or {}
    _tot = int(_und.get("_toplam") or 0)
    _ack = store.read_json(_nt.ACK_FILE, {}) or {}   # YASA 6 dış okuyucu: artefaktı store ile OKUR
    _absorbed = int(_ack.get("absorbed") or 0)
    # KALINTI = BİRİKEN − OPERATÖRÜN GÖRDÜĞÜ (2026-07-26). `_toplam` kümülatiftir ve azalmaz; satır
    # bir kez kırmızıya döndüğünde sonsuza dek kırmızı kalıyordu. Kalıcı kırmızı bir dedektör,
    # hiç olmayan bir dedektörle aynıdır: operatör ona bakmayı bırakır. Sayaç yine SIFIRLANMAZ
    # (yapısal boşluğun tarihi kaybolmaz); yalnız GÖRÜLMÜŞ kısmı düşülür.
    _kalan = max(0, _tot - _absorbed)
    _cfg = bool(_nt.configured())
    if _tot:
        _tokens = ", ".join(f"{k}×{v}" for k, v in sorted(_und.items()) if not k.startswith("_"))
        # Metin, `notify.configured()` GERÇEĞİNDEN üretilir. Eski hâli kanal bağlıyken bile
        # "bildirim kanalı yapılandırılmamış" diyordu — sayaç geçmişte birikmiş olabilir ve o metin
        # bugünün durumunu YANLIŞ anlatıyordu; yanlış teşhis yanlış müdahaleyi doğurur.
        if _kalan == 0:
            _detail = (f"birikmiş {_tot} alarmın tamamı okundu (ACK ile soğuruldu) — "
                       f"kalıntı yok ({_tokens})")
        elif _cfg:
            _detail = (f"kanal bağlı, {_kalan} birikmiş (ACK ile soğurulur) — bu yığın kanal "
                       f"YOKKEN toplandı ({_tokens}); teslim edilmiş değil, yalnız yerel gelen "
                       f"kutusunda duruyor")
        else:
            _detail = (f"{_kalan} alarm TESLİM EDİLEMEDİ ({_tokens}) — bildirim kanalı "
                       f"yapılandırılmamış (Telegram/webhook). Dedektörler çalışıyor ama "
                       f"kimse duymuyor.")
        # ACK'İN SAHİBİ (2026-07-26): `ack_by` yazılıyordu ve hiçbir yerde OKUNMUYORDU (alan
        # düzeyinde yasa 6). Kalıntının DÜŞÜLMÜŞ olması bir eylemdir ve her eylemin bir faili
        # vardır: satır "bu yığını kim, ne zaman kapattı"yı da taşımalı. Alan YOKSA eklenmez —
        # eski ACK dosyaları için "operator" yazmak ölçülmemiş bir faili uydurmak olurdu.
        if _ack.get("ack_by"):
            _detail += f" · ack: {_ack['ack_by']}@{_ack.get('ack_ts')}"
        rows.append({"check": "alarm_delivery", "ok": _kalan == 0, "detail": _detail})
    # 7g) KANALIN KENDİSİ — ayrı bir satır, çünkü yukarıdaki BİRİKMİŞ YIĞINI anlatır, bu ise
    #     YAPISAL BOŞLUĞU: "operatöre ulaşan bir yol var mı". Ve bu boşluk OKUNDU işaretiyle
    #     KAPANMAZ — operatörün "gördüm"ü bir bildirim kanalını var etmez; yerel gelen kutusu
    #     yalnız alarmın GÖRÜLDÜĞÜNÜ kanıtlar, kanalın varlığını değil.
    #
    #     KAPI: `_tot > 0` YA DA kanal bağlı. BİLİNÇLİ SAPMA ve bilinen kör nokta: kapının asıl
    #     işlevi MUTASYON TEMELİNİ TEMİZ tutmak — taze bir sandbox state'te teslim edilecek hiçbir
    #     şey yokken "kanal yok" demek kurt masalıdır, üstelik kirli bir temelde her mutasyon
    #     "yakalandı" görünür ve kapsama sayısı yalan söyler (mutation.py bunu haklı olarak
    #     reddediyor). Bedeli: TAZE bir kurulumda kanal-yokluğu tespiti ancak İLK kayıptan sonra
    #     başlar — yani bir alarm mutlaka duyulmadan kaybolur. Kanal BAĞLIYSA satır yığından
    #     bağımsız çıkar; yeşil satır operatöre kanalın hâlâ ayakta olduğunu söyler.
    if _tot or _cfg:
        rows.append({"check": "notify_channel", "ok": _cfg,
                     "detail": ("uzak bildirim kanalı bağlı (Telegram/webhook)" if _cfg
                                else "uzak bildirim kanalı YOK — pano açılmadan operatöre ulaşan "
                                     "hiçbir yol yok; alarmlar yalnız yerel gelen kutusunda birikir")
                               + (f" · son okundu: {_ack.get('ack_ts')}" if _ack.get("ack_ts") else
                                  " · yerel gelen kutusu hiç okunmadı")})

    # 7h) ÖĞRENME DÖNGÜSÜ AÇIK MI — `learning_loop_open.json` bugüne dek YAZILIYOR ama hiçbir
    #     dedektör/pano tarafından OKUNMUYORDU (kendi beyanı "makullük dedektörü toplamı okur" diyordu
    #     ve bu DOĞRU DEĞİLDİ — yasa 6 ihlali, üstelik beyanın kendisiyle örtülmüş hâli).
    #     Döngü kapanamıyorsa hiçbir hipotez terminale ulaşmaz, kalibrasyon beslenmez ve ajan
    #     dışarıdan "meşgul" görünür. Dosya YOKSA (ya da `_close_loop` onu boşalttıysa) satır HİÇ
    #     çıkmaz: kapanmış bir döngü için kırmızı satır bir kurt masalıdır ve mutasyon bataryasının
    #     temel durumunu kirletirdi.
    from . import rollback as _rb
    _ll = store.read_json(_rb.OPEN_LOOP_FILE, {}) or {}
    if _ll.get("reason"):
        _diag = ("parent_row_exists", "parent_row_has_score", "ship_hypothesis_exists",
                 "ship_gate_incumbent_oos", "baseline_verdict")
        _dtxt = " · ".join(f"{k}={_ll[k]}" if k in _ll else f"{k}=ölçülmedi" for k in _diag)
        rows.append({"check": "learning_loop", "ok": False,
                     "detail": f"öğrenme döngüsü KAPANMIYOR ({_ll['reason']}, {_ll.get('n', '?')}. tur) "
                               f"· v{_ll.get('version', '?')}→ebeveyn {_ll.get('parent', '?')} "
                               f"· {_dtxt} — hiçbir hipotez terminale ulaşmaz, kalibrasyon beslenmez"})

    # 8) ÖLÇÜLEN EDGE — her rejimde negatifse bu bir SONUÇTUR ve görünür olmalı (karar değil, uyarı)
    re_ = store.read_json("regime_edge.json", {}) or {}
    meas = {k: v for k, v in re_.items() if isinstance(v, dict) and (v.get("n") or 0) >= 20}
    if meas:
        neg = [k for k, v in meas.items() if (v.get("avg_r") or 0) < 0]
        _shown = ", ".join(f"{k}:{meas[k].get('avg_r')}" for k in list(meas)[:3])
        rows.append({"check": "measured_edge", "ok": len(neg) < len(meas),
                     "detail": f"{len(neg)}/{len(meas)} rejimde ölçülen ort. R negatif ({_shown})"})
    return {"rows": rows, "ok": all(r["ok"] for r in rows), "n_cycles": len(recent)}


def integrity_report(persist: bool = False) -> dict:
    """YEDİ dedektörü tek çağrıda topla (teşhis paneli + öz-değerlendirme buradan okur).
    7. desen (parity/makullük) 2026-07-21'de eklendi: ilk altısı bileşen bazlıdır ve 'doğru
    parçalar, yanlış sistem sonucu' sınıfını göremez — motorun evrenin %18'inde karar verdiği
    hata tam olarak o sınıftandı."""
    return {"production": production_report(), "conservation": conservation_report(),
            "determinism": determinism_report(persist=persist), "coherence": coherence_report(),
            "monotonicity": monotonicity_report(persist=persist),
            "ownership": ownership_report(persist=persist), "parity": parity_report()}


# ---- PANO İÇİN KISA ÖMÜRLÜ ÖNBELLEK (2026-07-28) -------------------------------------------
# `integrity_report()` /api/diagnostics'in en pahalı parçası (ölçüm: statik analiz önbelleklendikten
# sonra ~1 sn; kalanı 61 JSONL + 97 CSV okuması). Pano bunu her Operasyon açılışında yeniden
# hesaplatıyordu.
#
# NEDEN AYRI FONKSİYON, `integrity_report`'a DOKUNMADAN: o fonksiyonun iki çağıranı `persist=True`
# ile geliyor — check_integrity_and_alarm ("taban YALNIZ burada ilerler") ve mutation.py'nin
# strateji mutasyon kararı. Yan etkili ve karara giren bir yolu önbelleklemek tabanı dondurur ve
# mutasyonu bayat veriyle besler. Bu sarmalayıcı YALNIZ okuyan pano içindir ve persist ALMAZ.
#
# NEDEN SADECE TTL, state mtime damgası DEĞİL: önce `state/` parmak izine bağlı bir kapı yazıldı
# ve ölçüldü — canlı worker 12 saniyede `events.jsonl` ile `mirror_orders.json`'ı yazıyor.
# `events.jsonl` raporun GERÇEK girdisi (parity_report onu dört yerde okur), dolayısıyla içeriğe
# dayalı geçersizleştirme "hiç önbellekleme"ye çöküyordu: dört ardışık çağrının üçü yeniden
# hesaplandı. Damga kaldırıldı; bayatlık TTL ile SINIRLANIR ve `age` olarak DIŞARI VERİLİR.
# Pano gördüğü raporun kaç saniye önce hesaplandığını söyler — taze gibi göstermez.
_INTEGRITY_CACHE: dict = {}
INTEGRITY_TTL_S = 20.0


def integrity_report_cached() -> tuple[dict, float]:
    """Panonun okuduğu bütünlük raporu + raporun KAÇ SANİYE ÖNCE hesaplandığı.

    `age` 0.0 ise rapor bu istekte hesaplandı. Üst sınır INTEGRITY_TTL_S.
    `persist` YOK ve olmayacak — bkz. yukarıdaki gerekçe."""
    import time as _t
    now = _t.monotonic()
    hit = _INTEGRITY_CACHE.get("v")
    if hit is not None:
        rep, at = hit
        if (now - at) < INTEGRITY_TTL_S:
            return rep, round(now - at, 1)
    rep = integrity_report()          # persist=False — taban ilerlemez, yan etki yok
    _INTEGRITY_CACHE["v"] = (rep, now)
    return rep, 0.0


INTRADAY_STAMP_LEDGERS = ("intraday_decisions.jsonl", "intraday_shadow_orders.jsonl")


def intraday_stamp_report(sample: int = 500) -> dict:
    """ÜÇ DAMGA denetimi: `decision_as_of >= close_ts` diskteki gerçek satırlarda tutuyor mu?

    Bu, Faz 4a/4b'nin TEK yapısal iddiasıdır: karar, barın kapanışından ÖNCE alınmış olamaz
    (look-ahead kapalı). İddia iki defterin yazım satırında beyan ediliyor ve bugüne kadar yalnız
    fixture'lı birim testlerle denetleniyordu.

    BOŞ DEFTER İHLAL DEĞİLDİR: iki defter de henüz 0 satır (4a saha açlığı — bilinen ve ROADMAP'te
    izlenen durum). "Damga tutmuyor" ile "denetlenecek satır yok" AYRI hükümlerdir; ikincisi
    ok=True + açık bir not döner, aksi halde dedektör her gün sahte kırmızı yakardı."""
    rows = []
    for name in INTRADAY_STAMP_LEDGERS:
        recs = store.read_jsonl(name, limit=sample)
        if not recs:
            rows.append({"ledger": name, "ok": True, "rows": 0, "violations": 0,
                         "detail": f"{name}: defter boş — denetlenecek satır yok (damga iddiası "
                                   f"henüz sınanamıyor)"})
            continue
        bad, unstamped = [], 0
        for r in recs:
            a, c = r.get("decision_as_of"), r.get("close_ts")
            if not a or not c:
                unstamped += 1
                continue
            # ISO-8601 damgalar aynı biçimde (barclock üretir) — sözlüksel kıyas yeterli DEĞİL:
            # ofset farkı sıralamayı bozar. Ayrıştırılamayan damga İHLAL değil, ÖLÇÜLEMEZ sayılır.
            try:
                if dt.datetime.fromisoformat(str(a)) < dt.datetime.fromisoformat(str(c)):
                    # `ticker` İKİ defterde de yazılıyor (intraday_cycle.py:126, intraday_shadow.py:231)
                    # — `plan_id`'ye düşen bir yedek yazmak, olmayan bir şema ayrışmasını beyan
                    # etmek olurdu (test_no_undeclared_field_alias_appears bunu haklı olarak yakalar).
                    bad.append(r.get("ticker") or "?")
            except ValueError:  # sessiz-yutma: ayrıştırılamayan damga İHLAL sayılmaz (yanlış look-ahead suçlaması üretirdi) ama YUTULMAZ da — `unstamped` sayacına girer ve detail metninde "iddia doğrulanamaz" olarak raporlanır
                unstamped += 1
        ok = not bad and not unstamped
        det = f"{name}: {len(recs)} satır"
        if bad:
            det += (f" — {len(bad)} satırda decision_as_of < close_ts (LOOK-AHEAD: "
                    f"{', '.join(map(str, bad[:5]))})")
        if unstamped:
            det += f" — {unstamped} satırda üç damga eksik/ayrıştırılamaz (iddia doğrulanamaz)"
        if ok:
            det += " — üç damga tutuyor (karar barın kapanışından sonra)"
        rows.append({"ledger": name, "ok": ok, "rows": len(recs),
                     "violations": len(bad) + unstamped, "detail": det})
    return {"rows": rows, "ok": all(r["ok"] for r in rows)}


# ---- SÖZLEŞMENİN BAŞARISIZLIK HÜKMÜ (K1, 2026-07-30) ---------------------------------------
# `state/goal.yaml:14` şunu yazıyor: failure_below: -0.04 — yani "30 günlük gerçekleşen getiri
# -%4'ün altına düşerse bu deney BAŞARISIZDIR". Hüküm 2026-07-14'te yazıldı ve BUGÜNE KADAR hiçbir
# kod onu okumadı: `guard.GOAL_KEYS` yalnız üyelik seti (drift koruması), `score.score_detail`
# hedef üçlüsünü composite'e katıyor ama failure tarafını asla. Deney başarısız olsa bunu
# söyleyecek tek satır kod yoktu. codelaw bunu göremez — artefakt yasası .json/.jsonl uzantısına
# bakar, yaml anahtar granülerliği yasanın DIŞINDA.
#
# NEDEN integrity_report'un İÇİNDE DEĞİL: o rapor YEDİ BÜTÜNLÜK deseni taşıyor ve hepsi
# "mekanizma üretiyor mu / kaybetmiyor mu / deterministik mi" sorusunu sorar. Bu ise bir
# PERFORMANS hükmü: mekanizma pekâlâ kusursuz çalışıp sonuç sözleşmenin altında olabilir. İki
# soruyu tek rapora katmak, panoda "bütünlük kırmızı" ile "strateji para kaybediyor"u aynı
# renge boyardı. Ayrı fonksiyon, ayrı jeton, ayrı alarm sınıfı.
def goal_failure_report() -> dict:
    """goal.yaml `failure_below` hükmünün ÖLÇÜMÜ. UYDURMA YASAĞI: örneklem min_sample'ın altındaysa
    `realized_30d` YOKTUR ve hüküm `failed=None` döner — "ölçtük, başarısız değil" DEĞİL,
    "henüz ölçülemiyor". Sıfır/False dönmek burada yanlış güven üretirdi."""
    from . import config
    goal = config.goal()
    thr = goal.get("failure_below")
    if thr is None:
        return {"failed": None, "threshold": None, "realized_30d": None,
                "detail": "goal.yaml'da failure_below tanımlı değil"}
    thr = float(thr)
    from . import score as _sc
    sd = _sc.score_detail(store.read_jsonl("trades.jsonl"), goal)
    r30 = sd.get("realized_30d")
    if r30 is None:
        return {"failed": None, "threshold": thr, "realized_30d": None,
                "n": sd.get("n"), "min_sample": sd.get("min_sample"),
                "detail": (f"{sd.get('n')}/{sd.get('min_sample')} kapanan işlem — 30g getiri "
                           f"ÖLÇÜLEMEZ, hüküm None (0.0 değil)")}
    r30 = float(r30)
    failed = r30 < thr
    return {"failed": bool(failed), "threshold": thr, "realized_30d": round(r30, 4),
            "n": sd.get("n"),
            "detail": (f"30g getiri {r30:+.2%} < başarısızlık eşiği {thr:+.2%} — SÖZLEŞME HÜKMÜ"
                       if failed else
                       f"30g getiri {r30:+.2%} ≥ başarısızlık eşiği {thr:+.2%}")}


def check_integrity_and_alarm() -> None:
    """Bütünlük ihlallerini bir kez alarmlar (bekçi felsefesi: yalnız haber verir, düzeltmez)."""
    from . import obs
    rep = integrity_report(persist=True)   # taban YALNIZ burada ilerler (tek sahip)
    prev = set(store.read_json("integrity_alarmed.json", []))
    now = set()
    # SÖZLEŞME HÜKMÜ (K1): mandal deseni akranlarıyla aynı — eşik altına düşüş bir kez alarmlanır,
    # yukarı çıkınca jeton düşer ve YENİDEN düşüşte yeniden alarmlanır. None (ölçülemez) jeton
    # üretmez: ölçülemeyen bir hüküm alarmlanamaz.
    try:
        _gf = goal_failure_report()
        if _gf.get("failed"):
            tok = "goal_failure"
            now.add(tok)
            if tok not in prev:
                obs.alarm(obs.ALARM_GOAL_FAILURE,
                          f"SÖZLEŞME BAŞARISIZLIK EŞİĞİ: {_gf['detail']}",
                          kind="goal_failure", realized_30d=_gf.get("realized_30d"),
                          threshold=_gf.get("threshold"), n=_gf.get("n"))
    except Exception as e:
        # YASA 4: hüküm ölçülemezse SESSİZ kalmaz. Buradaki istisna "deney başarısız değil" demek
        # değil, "başarısızlık kriterini ölçemedim" demektir; ikisi karıştırılamaz.
        obs.warn("goal_failure_check_failed", error=f"{type(e).__name__}: {e}")
    for s in rep["production"]["starved"]:
        tok = f"starved:{s['name']}"
        now.add(tok)
        if tok not in prev:
            obs.alarm("MECHANISM_STALE", f"mekanizma ÜRETMİYOR: {s['name']} — {s['note']} (0 çıktı)",
                      mechanism=s["name"], kind="starved")
    if rep["conservation"]["unexplained"]:
        tok = "conservation"
        now.add(tok)
        if tok not in prev:
            obs.alarm("MECHANISM_STALE",
                      f"KORUNUM İHLALİ: {rep['conservation']['unexplained']} plan kayıtsız kayboldu",
                      kind="conservation")
    if not rep["determinism"].get("ok"):
        tok = "determinism"
        now.add(tok)
        if tok not in prev:
            obs.alarm("DATA_QUALITY", f"SESSİZ BAR MUTASYONU: {rep['determinism'].get('detail')}",
                      kind="determinism")
    for pr in rep.get("parity", {}).get("rows", []):
        if pr.get("ok"):
            continue
        if pr["check"] == "learning_loop":
            # ÇİFT DUYURU (2026-07-26): bu satırın kaynağı `rollback._open_loop`, ve orası döngü
            # açıldığında ZATEN `learning_loop_open` uyarısını düşürüyor. Buradan ikinci kez
            # alarmlamak aynı olguyu iki kanaldan anlatır; dahası `now`a girerse mandal defterine
            # yapışır ve döngü kapanıp YENİDEN açıldığında bir daha hiç alarm üretemez. Bulgu
            # makullük satırında ve panoda görünür — `notify_channel` ile aynı gerekçe.
            continue
        if pr["check"] == "notify_channel":
            # DÖNGÜSELLİK (2026-07-26): "bildirim kanalı yok" bulgusunu BİLDİRİM KANALINDAN
            # duyurmak, tam da yokluğundan şikâyet ettiğimiz yolu kullanmak olurdu — üstelik
            # teslim edilemeyen alarm sayacını kendi kendine besler. Bulgu makullük satırında ve
            # panoda zaten görünür. `now`a EKLENMEZ: mandal defterine yapışsaydı, kanal sonradan
            # bağlanıp GERÇEKTEN bozulduğunda bu satır bir daha hiç alarm üretemezdi.
            continue
        if pr["check"] == "alarm_delivery":
            # KABUL EDİLEN DÖNGÜSELLİĞİN KALINTISI (2026-07-26): bu satır "şu kadar alarm teslim
            # EDİLEMEDİ" der; onu alarma çevirmek — kanal yokken — `notify_undelivered` sayacını
            # bir artırır, yani BULGUNUN KENDİSİ ölçtüğü yığını büyütür ve bir sonraki turda daha
            # büyük bir kalıntı raporlanır. Bulgu makullük satırında ve panoda zaten görünür.
            # `now`a EKLENMEZ: mandal defterine yapışsaydı yığın ACK ile soğurulup satır yeşile
            # döndükten sonra GERÇEKTEN yeniden biriktiğinde bir daha hiç alarm üretemezdi.
            # (`notify_channel` ile bire bir aynı üç gerekçe.)
            continue
        if pr["check"] == "artifact_unread":
            # ARTEFAKT-BAŞINA JETON (K1, 2026-07-30): tek `parity:artifact_unread` jetonu mandala
            # yapışınca, ESKİ bir orphan sürerken YENİ bir artefakt okumasız kaldığında alarm
            # üretilemiyordu (bugün mandal doluyken pencere fiilen açıktı). stale/regress/clobber
            # akranlarıyla aynı disiplin: kimlik jetona girer, küme değişimi alarm doğurur.
            for _a in (pr.get("orphans") or []):
                tok = f"unread:{_a}"
                now.add(tok)
                if tok not in prev:
                    obs.alarm("MECHANISM_STALE",
                              f"OKUNMAYAN ARTEFAKT: {_a} yazılıyor ama hiçbir modül okumuyor",
                              kind="parity", check=pr["check"], artifact=_a)
            continue
        tok = f"parity:{pr['check']}"
        now.add(tok)
        if tok not in prev:
            obs.alarm("MECHANISM_STALE",
                      f"MAKULLÜK: {pr['check']} — {pr['detail']}", kind="parity", check=pr["check"])
    for st in rep["coherence"]["stale"]:                       # #4 bayat türev (eski veriyle konuşan kalibrasyon)
        tok = f"stale:{st['artifact']}"
        now.add(tok)
        if tok not in prev:
            obs.alarm("MECHANISM_STALE",
                      f"BAYAT TÜREV: {st['artifact']} kaynağından {st['behind_h']} sa geride",
                      kind="coherence", artifact=st["artifact"])
    for rg in rep["monotonicity"].get("regressions", []):      # #5 ileri-only nicelik geri gitti
        tok = f"regress:{rg['field']}"
        now.add(tok)
        if tok not in prev:
            obs.alarm("DATA_QUALITY",
                      f"GERİLEME: {rg['field']} {rg['was']} → {rg['now']} (ileri-only olmalıydı)",
                      kind="monotonicity", field=rg["field"])
    for lo in rep["ownership"].get("lost", []):                # #6 sahiplenilmeyen yazıcı alanı ezdi
        tok = f"clobber:{lo['file']}.{lo['field']}"
        now.add(tok)
        if tok not in prev:
            obs.alarm("DATA_QUALITY",
                      f"ALAN EZİLDİ: {lo['file']}.{lo['field']} bir kez doluydu, şimdi kayıp",
                      kind="ownership", field=lo["field"])
    store.write_json("integrity_alarmed.json", sorted(now))


# --------- #4 TUTARLILIK: türetilmiş artefakt kaynağından taze mi? ---------
# Bar↔wf-cache hatasının GENEL hali: her türetilmiş dosya, beslendiği kaynaktan yeni olmalı. Kaynak
# büyümüş ama türev güncellenmemişse o türev SESSİZCE bayattır (canlıda bulundu: gölge model 7115 yeni
# cf satırına rağmen eski veriyle duruyordu).
DERIVED_SOURCES = {
    "score_calibration.json": ["counterfactuals.jsonl", "trades.jsonl"],
    "near_miss.json":         ["counterfactuals.jsonl"],
    "regime_edge.json":       ["counterfactuals.jsonl"],
    "cf_fidelity.json":       ["counterfactuals.jsonl", "trades.jsonl"],
    "exit_efficiency.json":   ["counterfactuals.jsonl", "trades.jsonl"],
    "llm_calibration.json":   ["trade_plans.jsonl", "trades.jsonl"],
    "shadow_model.json":      ["counterfactuals.jsonl", "trades.jsonl"],
    "self_review.json":       ["score_calibration.json", "near_miss.json"],
    # eşik eğrisi iki defterden de beslenir (gerçek + cf katmanı); defterler ilerleyip eğri
    # ilerlemiyorsa panodaki "en iyi eşik" cümlesi BAYAT bir örneklemden konuşuyor demektir
    # (Aşama 1.3, 2026-07-29)
    "threshold_curve.json":   ["counterfactuals.jsonl", "trades.jsonl"],
    # BİLEŞEN IC (K1, 2026-07-30): 1.4 karar girdisi. Üreticisi loop.py'de istisna yutup obs.warn'a
    # düşüyor — çağrı sessizce düşerse pano ve hermes kanıt paketi ESKİ IC tablosundan konuşur.
    # Akranlarının (score_calibration, threshold_curve, near_miss, regime_edge, cf_fidelity) hepsi
    # bu listedeydi, component_ic yoktu: bayatlığı ölçen tek dedektör onu hiç görmüyordu.
    "component_ic.json":      ["counterfactuals.jsonl", "trades.jsonl"],
    "arming_report.json":     ["counterfactuals.jsonl"],
    "scoreboard.json":        ["hypotheses.jsonl"],
    # eleme muhasebesi kalibrasyonlarla AYNI turda yazılır; defterler ilerleyip sieve ilerlemiyorsa
    # huni ölçümü bayat demektir ve "sıfır ihlal" yanıltıcı olur (2026-07-22)
    "sieve.json":             ["counterfactuals.jsonl", "trades.jsonl"],
    # defter ilerlerken ayna mutabakatı ilerlemiyorsa panodaki broker görünümü BAYAT konuşuyor
    # (adapters.alpaca denetimi 2026-07-21)
    "broker_reconcile.json":  ["portfolio.json"],
}
COHERENCE_GRACE_S = 3600      # 1 sa: bir sonraki döngü zaten tazeler — panik yok


def coherence_report() -> dict:
    """#4 — türev bayatlığı. Kaynak güncellendiği halde türev eskiyse bayrak. Grace: 1 saat (döngü
    kadansı). Yalnız gözlem: hangi kalibrasyonun eski veriyle konuştuğunu görünür kılar."""
    # `store.mtime` ARKA UÇTAN BAĞIMSIZ (WP-H/H9, 2026-07-31): kaynakların dördü (trades,
    # trade_plans, portfolio, scoreboard) SQLite'a taşınabilir ve o an dosyaları `.migrated`
    # ekiyle DONAR — `os.path.getmtime` "kaynak hiç güncellenmiyor" derdi, yani bayatlık
    # dedektörü tam da ölçmek için var olduğu şeyi göremez hâle gelirdi.
    def _m(name):
        return store.mtime(name)
    stale, ok, absent = [], 0, []
    for art, srcs in DERIVED_SOURCES.items():
        a = _m(art)
        if a is None:
            absent.append(art); continue
        newest = max([m for m in (_m(s) for s in srcs) if m], default=None)
        if newest and a < newest - COHERENCE_GRACE_S:
            stale.append({"artifact": art, "behind_h": round((newest - a) / 3600, 1)})
        else:
            ok += 1
    stale.sort(key=lambda x: -x["behind_h"])
    return {"stale": stale, "ok": ok, "absent": absent, "total": len(DERIVED_SOURCES)}


# --------- #5 MONOTONLUK: ileri-only nicelikler geri gitmemeli ---------
MONOTONIC_FILE = "monotonic_state.json"
AMNESTY_FILE = "monotonic_amnesty.json"


def grant_amnesty(field: str, was, now, reason: str, by: str = "operatör") -> dict:
    """MEŞRU KÜÇÜLMENİN YAZILI KAYDI (2026-07-22).

    Monotonluk dedektörünün kör noktası: bir defterin KASITLI olarak yeniden kurulması (düzeltilmiş
    matematikle re-seed: 129 işlem → 96) ile SESSİZ KAYIP birebir aynı görünüyordu. İki çıkış vardı
    ve ikisi de yanlıştı: (a) bayrağı sonsuza kadar kırmızı bırak — operatör kırmızıyı yok saymayı
    öğrenir, kurt masalı; (b) `persist=True` ile tabanı sessizce ilerlet — o zaman GERÇEK bir kayıp
    da aynı sessizlikle emilir.

    Üçüncü yol: af, ama YAZILI ve TAM. Yalnız (alan, was, now) üçlüsü BİREBİR eşleşen küçülme
    bağışlanır; bir satır daha kaybolursa eşleşme bozulur ve bayrak geri gelir. Gerekçesiz af
    geçersizdir — "neden"i olmayan bir istisna, istisna değil sessizliktir."""
    if not str(reason).strip():
        raise ValueError("af GEREKÇESİZ olamaz — gerekçesiz istisna, sessizliğin kendisidir")
    kayit = {"field": str(field), "was": was, "now": now,
             "reason": str(reason).strip(), "by": str(by), "ts": _now_iso()}
    liste = store.read_json(AMNESTY_FILE, []) or []
    liste = [a for a in liste if a.get("field") != kayit["field"]]   # alan başına EN SON af geçerli
    liste.append(kayit)
    store.write_json(AMNESTY_FILE, liste)
    from . import obs
    obs.log("monotonic_amnesty_granted", field=field, was=was, now=now, reason=reason, by=by)
    return kayit


def _amnesty_index() -> dict:
    out = {}
    for a in (store.read_json(AMNESTY_FILE, []) or []):
        if isinstance(a, dict) and a.get("field") and str(a.get("reason") or "").strip():
            out[str(a["field"])] = a          # gerekçesiz kayıt AF SAYILMAZ
    return out


def _now_iso() -> str:
    import datetime as _dt
    return _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).isoformat()


def monotonicity_report(persist: bool = False) -> dict:
    """#5 — geriye-seans hatasının GENEL hali: bazı nicelikler ASLA azalmamalı (kitap tarihi, strateji
    sürümü, cache revizyonu, defter satır sayıları, tepe sermaye). Azalma = bozuk yazım, kötü restore
    ya da geri sarma. Son görülen değerler saklanır; azalırsa bayrak.
    persist: TABANI GÜNCELLE (2026-07-22 bulgusu). Bu üç dedektör "önceki durum ile şimdiki durum"
    kıyaslar; kıyası yapan her çağrı tabanı da yazarsa, iki okuma ARASINDA olan bir gerileme
    sessizce yeni tabana emilir. Canlıda tam bu oluyordu: `/api/diagnostics` salt-okunur bir GET
    ucu ama her pano yenilemesinde tabanı yeniden yazıyordu — yani PANOYU AÇIK TUTMAK dedektörü
    körleştiriyordu. Artık taban yalnız günlük döngü/zamanlayıcı turunda (persist=True) ilerler;
    okuma yolları yalnız kıyas yapar.
    """
    cur = {}
    try:
        pf = store.read_json("portfolio.json", {}) or {}
        cur["book_date"] = str(pf.get("last_date") or "")
        cur["peak_equity"] = float(pf.get("peak_equity") or 0)
    except Exception as e:
        from . import obs
        obs.warn("monotonicity_source_unreadable", source="portfolio.json",
                 error=f"{type(e).__name__}: {e}", detail="bu sayaçta gerileme tespiti DEVRE DIŞI")
    try:
        from . import config
        cur["strategy_version"] = int(config.load_strategy().get("version", 0))
    except Exception as e:
        from . import obs
        obs.warn("monotonicity_source_unreadable", source="strategy.yaml",
                 error=f"{type(e).__name__}: {e}", detail="sürüm gerilemesi tespiti DEVRE DIŞI")
    cur["wf_rev"] = int(store.read_json("wf_cache_rev.json", {}).get("rev", 0))
    # events/candidates 2026-07-22'de eklendi: mutasyon koşumu "olay defterinin üçte ikisi kayboldu"
    # ve "aday defteri boşaldı" senaryolarını HİÇBİR dedektörün görmediğini ölçtü. Teşhis geçmişinin
    # sessizce silinmesi, sonraki her soruşturmayı kör bırakır.
    for f, key in (("counterfactuals.jsonl", "cf_rows"), ("trades.jsonl", "trades"),
                   ("hypotheses.jsonl", "hypotheses"), ("events.jsonl", "events"),
                   ("candidates.jsonl", "candidates")):
        try:
            cur[key] = len(store.read_jsonl(f))
        except Exception as e:
            # Eksik sayaç, monotonluk dedektöründe "gerileme yok" diye OKUNUR. Defterin kısalıp
            # kısalmadığı bilinmiyorsa bunu söylemek zorunda.
            from . import obs
            obs.warn("monotonicity_source_unreadable", source=f, error=f"{type(e).__name__}: {e}",
                     detail="bu defterde kısalma tespiti DEVRE DIŞI")
    prev = store.read_json(MONOTONIC_FILE, None)
    if persist:
        store.write_json(MONOTONIC_FILE, cur)
    if not prev:
        return {"ok": True, "detail": "ilk anlık görüntü kaydedildi", "tracked": len(cur)}
    aff = _amnesty_index()
    regressions, amnestied = [], []
    for k, v in cur.items():
        p = prev.get(k)
        if p is None:
            continue
        if (isinstance(v, str) and v and p and v < p) or (isinstance(v, (int, float)) and v < p):
            row = {"field": k, "was": p, "now": v}
            a = aff.get(k)
            # AF TAM EŞLEŞMELİ: aynı alanda bir satır DAHA kaybolursa (now düşerse) ya da taban
            # değişirse eşleşme bozulur ve ihlal geri döner. Af bir alanı kalıcı olarak susturmaz.
            if a and a.get("was") == p and a.get("now") == v:
                amnestied.append({**row, "reason": a.get("reason"), "by": a.get("by"), "ts": a.get("ts")})
            else:
                regressions.append(row)
    return {"ok": not regressions, "regressions": regressions,
            "amnestied": amnestied, "tracked": len(cur)}


# --------- #6 SAHİPLİK: yazan, sahibi olmadığı alanı ezmemeli ---------
OWNERSHIP_FILE = "ownership_state.json"
# nabız: bu alanlar bir kez dolduktan sonra KAYBOLMAMALI (canlıda bulundu: /api/halt nabzı yalnız
# note ile yazınca rejim/bütçe siliniyordu → HUD "rejim yok" gösterdi).
OWNED_FIELDS = {"heartbeat.json": ["regime", "exposure_budget_pct", "equity", "last_bar"]}


def ownership_report(persist: bool = False) -> dict:
    """#6 — alan ezilmesi. Bir dosyada BİR KEZ dolmuş kritik alan sonradan None/kayıp olduysa, onu
    sahiplenmeyen bir yazıcı üzerine yazmış demektir (nabız ezilmesi sınıfı).
    persist: TABANI GÜNCELLE (2026-07-22 bulgusu). Bu üç dedektör "önceki durum ile şimdiki durum"
    kıyaslar; kıyası yapan her çağrı tabanı da yazarsa, iki okuma ARASINDA olan bir gerileme
    sessizce yeni tabana emilir. Canlıda tam bu oluyordu: `/api/diagnostics` salt-okunur bir GET
    ucu ama her pano yenilemesinde tabanı yeniden yazıyordu — yani PANOYU AÇIK TUTMAK dedektörü
    körleştiriyordu. Artık taban yalnız günlük döngü/zamanlayıcı turunda (persist=True) ilerler;
    okuma yolları yalnız kıyas yapar.
    """
    prev = store.read_json(OWNERSHIP_FILE, {}) or {}
    lost, cur = [], {}
    for fname, fields in OWNED_FIELDS.items():
        d = store.read_json(fname, {}) or {}
        seen = prev.get(fname, {})
        st = {}
        for f in fields:
            has = d.get(f) is not None
            st[f] = bool(has or seen.get(f))          # "bir kez dolmuş" hafızası
            if seen.get(f) and not has:
                lost.append({"file": fname, "field": f})
        cur[fname] = st
    if persist:
        store.write_json(OWNERSHIP_FILE, cur)
    return {"ok": not lost, "lost": lost}
