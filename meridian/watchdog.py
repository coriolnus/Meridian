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


# ============ ASKIDA-FARKINDALIK (v192, 2026-08-06 — operatör alarm-hijyeni şikâyeti) ============
# CANLI KANIT (24 sa, Rol-1 ölçümü): alarm defterinin ~112 satırı tek bir cümleydi —
# "MECHANISM_STALE hermes_poll 0,5-0,7 sa (pencere 0,5)". İki AYRI kusur onu üretiyordu ve ikisi de
# bu blokta kapanıyor:
#
#   (a) ASKIDA ≠ GECİKMİŞ. `hermes_poll` nabzı, hermes ipliği kota soğumasındayken ya da kimlik
#       havuzu tükenmişken SEYREKLEŞİR — mekanizma ölü değil, BEKLEMEYE ALINMIŞTIR (v188 tam bu
#       hâli `brain_cooldown.json` + `_pool_exhausted` ile yazıyor). Onu "gecikti" diye alarmlamak,
#       sistemin kendi bildirdiği bilinen ve MEŞRU bir hâli arıza diye operatöre yollamaktır.
#       Emsal aynı dosyada: `production_report` kapı meta-kalibrasyonunu `askida` kovasına ayırıyor
#       (WP-M ölçek borcu turu) — "sayamıyorum" ile "üretmiyorum" ayrımının bekçi tarafındaki ikizi.
#       ÖNEMLİ: askıda olan mekanizma OK sayılmaz; kendi kovasında görünür (panoda dürüst kalır),
#       yalnız ALARM üretmez.
#
#   (b) HİSTEREZİS + GÜNLÜK TEKİLLEŞTİRME. Mandal (ALARMED_FILE) yalnız "şu an bayat olanlar"ı
#       tutuyordu: pencere sınırında salınan bir mekanizma (0,5 sa pencerede 0,5-0,7 sa'lık nabız)
#       her toparlanışta mandaldan düşüyor, her yeniden aşımda YENİ alarm yazıyordu — çırpınma
#       (flapping) alarm-yorgunluğunun ders kitabı hâli. ROADMAP WP-P'nin EEMUA 191 bütçesi
#       ≤10 alarm/gün yazar; tek mekanizma tek başına 112 yazıyordu. Kural: aynı mekanizma, aynı
#       UTC günü, EN FAZLA `GUNLUK_ALARM_TAVANI` kez. Eşik-aşımı sürerken tekrar yok (mandal, eski
#       davranış); kapanıp yeniden aşmak hâlâ MEŞRU bir yeni olaydır ama günlük tavana tabidir.
#       Bastırılan her satır SESSİZ DEĞİL: `ALARM_GUNLUK_FILE` sayacına yazılır ve `report()` onu
#       dışarı verir — bastırma kayda geçmezse bekçi kendi körlüğünü hijyen sanardı.
GUNLUK_ALARM_TAVANI = 1                  # mekanizma başına / UTC günü başına azami MECHANISM_STALE
ALARM_GUNLUK_FILE = "watchdog_alarm_gunluk.json"

# Askıda-sondası olan mekanizmalar. Sonda YALNIZ mekanizma zaten pencereyi aşmışken koşar (pano her
# poll'da report() çağırır — kota/havuz dosyalarını boşuna okumak pahalıya gelir).
_ASKIDA_SONDALARI = ("hermes_poll",)


def _hermes_askida() -> dict | None:
    """hermes ipliği BEKLEMEYE mi alındı? {neden, detay, kalan_s} ya da None (askıda değil).

    İki kaynak, ikisi de v188'in yazdığı yerler: (1) kimlik havuzu tükenmesi (`_pool_exhausted` —
    kendi pencere/kota-sıfırlama testleri içinde), (2) beyin soğuma defteri (`brain_cooldown.json`;
    `agent` satırı yerel-ajan yolunu, sağlayıcı satırları doğrudan çağrıyı bağlar). Hiçbiri yoksa
    None döner ve mekanizma NORMAL bayatlık yoluna gider — yani bu sonda hiçbir gerçek arızayı
    örtmez, yalnız sistemin kendi beyan ettiği bekleme hâlini alarmdan ayırır.

    `_pool_exhausted` ÖZEL AD, VE BİLEREK: onun tek kamusal sarmalayıcısı `hermes_runtime.status()`
    ve o fonksiyon `trade_plans.jsonl` + `trades.jsonl` defterlerini baştan okur (dolgu-bekleyen
    sayacı için). Bekçi sondası her bayat poll'da koşar; tam teşhis paketini çağırmak, bir bayrağı
    okumak için iki büyük defteri taramak olurdu. Kırılganlığı beyan ediyoruz: `_pool_exhausted`in
    imzası değişirse bu sonda `watchdog_askida_probe_failed` uyarısıyla DÜŞER ve fail-closed dalı
    alarmı yeniden basar — sessiz bir bozulma yolu yok."""
    from . import hermes
    havuz = hermes._pool_exhausted()
    if havuz:
        return {"neden": "havuz_tukendi", "kalan_s": None,
                "detay": f"kimlik havuzunda kullanılabilir kimlik yok (sağlayıcı: {havuz})"}
    # SOĞUMA DEFTERİ DOĞRUDAN OKUNMAZ — `brain_availability()` üzerinden sorulur. İki gerekçe:
    # (1) o fonksiyon yerel-ajan soğumasını nous ayağına ZATEN katlıyor (hermes._provider_cooldown);
    # (2) `brain_cooldown.json` `codelaw.DECLARED_SINKS`te "yalnız hermes okur" beyanıyla duruyor —
    # buradan `store.read_json` ile okumak o beyanı sessizce bayatlatırdı (stale_sink ihlali).
    durum = hermes.brain_availability() or {}
    en_uzun, kim, gerekce = 0.0, None, None
    for p, row in durum.items():
        rem = float((row or {}).get("cooling_s") or 0)
        if rem > en_uzun:
            en_uzun, kim, gerekce = rem, p, (row or {}).get("reason")
    ajan = float(hermes.brain_cooldown("agent"))
    if ajan > en_uzun:
        en_uzun, kim, gerekce = ajan, "agent", "yerel ajan havuzu soğumada"
    if en_uzun <= 0:
        return None
    return {"neden": "kota_sogumasi", "kalan_s": round(en_uzun, 1),
            "detay": f"beyin soğumada: {kim} — {round(en_uzun / 60, 1)} dk kaldı"
                     + (f" ({gerekce})" if gerekce else "")}


def _askida_mi(name: str) -> dict | None:
    """Mekanizma için askıda-sondası. Sonda DÜŞERSE askıda SAYILMAZ (fail-closed: ölçemediğim bir
    beklemeyi 'meşru bekleme' diye alarmı bastırmak, bekçinin var olma sebebini silerdi) ve düşüş
    obs'a yazılır — YASA 4."""
    if name not in _ASKIDA_SONDALARI:
        return None
    try:
        return _hermes_askida()
    except Exception as e:
        from . import obs
        obs.warn("watchdog_askida_probe_failed", mechanism=name, error=f"{type(e).__name__}: {e}")
        return None                          # ölçülemedi → normal bayatlık yolu (alarm BASILIR)


def report() -> dict:
    """{stale: [{name, gap_h, expected_h}], askida: [...], ok: n, never: [adlar]} — teşhis paneli
    buradan okur. Hiç damgalanmamış mekanizma 'never' listesinde (kurulumdan beri hiç koşmadı — en
    yüksek sesli hal). Penceresini aşmış AMA sistemin kendi beyanıyla beklemeye alınmış mekanizma
    `askida` listesindedir: ne OK'tir ne alarmlıktır (v192)."""
    beats = store.read_json(BEATS_FILE, {})
    now = _now()
    stale, never, askida, ok = [], [], [], 0
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
            satir = {"name": name, "gap_h": round(gap / 3600, 1),
                     "expected_h": round(max_gap / 3600, 1)}
            sus = _askida_mi(name)
            if sus:
                askida.append({**satir, **sus})
            else:
                stale.append(satir)
        else:
            ok += 1
    stale.sort(key=lambda x: -x["gap_h"])
    askida.sort(key=lambda x: -x["gap_h"])
    # GÜNLÜK SAYAÇ BURADAN DÖNMEZ (bilinçli): `watchdog_alarm_gunluk.json`ın DIŞ okuyucusu
    # `api.py`dir (codelaw: kendi yazdığını kendi okuyan tüketici sayılmaz). Raporun içine de
    # koymak aynı dosyayı tek istekte İKİ AYRI ANDA okumak olurdu — panoda iki farklı "kaç alarm
    # bastırıldı" cevabı doğabilirdi (WP-P/P1 dersi).
    return {"stale": stale, "never": never, "askida": askida, "ok": ok, "total": len(EXPECTED)}


ALARMED_FILE = "watchdog_alarmed.json"


def _bugun(now: float | None = None) -> str:
    """UTC gün damgası. `_now()` üzerinden okunur ki testler saati çivileyebilsin."""
    return dt.datetime.fromtimestamp(now if now is not None else _now(),
                                     dt.timezone.utc).strftime("%Y-%m-%d")


def _gunluk_oku() -> dict:
    """Günlük alarm defteri; gün döndüyse SIFIRLANIR (dünün tavanı bugünü susturamaz).

    BOZUK ŞEMA TAZE DEFTERE DÖNER: bu sayaç bir HİJYEN aracıdır, karar kaynağı değil. Bozuk bir
    dosya yüzünden `check_and_alarm` istisna atsaydı bekçi tam da var olma sebebini (haber vermek)
    kaybederdi — üstelik çağıran scheduler poll'u da yanında götürürdü."""
    doc = store.read_json(ALARM_GUNLUK_FILE, {})
    if not isinstance(doc, dict) or doc.get("gun") != _bugun() \
            or not isinstance(doc.get("mekanizmalar"), dict):
        return {"gun": _bugun(), "mekanizmalar": {}}
    return doc


def check_and_alarm() -> None:
    """v11 #1 — bayat-GEÇİŞ alarmı: bir mekanizma penceresini İLK aştığında bir kez MECHANISM_STALE
    (bildirim beyaz-listesinde → telefona düşer); toparlanınca kayıt silinir ki bir sonraki bayatlama
    yine görünsün. Her poll'da ucuz; bekçi felsefesi aynı — yalnız haber verir.

    v192 İKİ EK KAPI: (1) askıda mekanizma `report()`ta zaten `stale` dışındadır → alarm yok,
    sayaç var; (2) aynı mekanizma-aynı UTC günü en fazla `GUNLUK_ALARM_TAVANI` alarm — çırpınan
    pencere sınırı bir günü 112 satırla dolduramaz (EEMUA ≤10/gün bütçesi, ROADMAP WP-P)."""
    from . import obs
    rep = report()
    alarmed = set(store.read_json(ALARMED_FILE, []))
    now_stale = {x["name"] for x in rep["stale"]}
    doc = _gunluk_oku()
    mek = doc["mekanizmalar"]
    kirli = False                             # sayaç DEĞİŞMEDİYSE yazma: bu fonksiyon 300 sn'lik
                                              # poll'da koşuyor ve koşulsuz yazım günde 288 gereksiz
                                              # atomik yazım + IO p95 gürültüsü ederdi (sakin bir
                                              # sistemde defterde değişecek hiçbir şey yok)

    def _satir(ad: str) -> dict:
        row = mek.get(ad)
        if not isinstance(row, dict):         # bozuk tek satır defterin tamamını düşürmez
            row = {}
            mek[ad] = row
        return row

    for x in rep["askida"]:
        satir = _satir(x["name"])
        satir["askida"] = int(satir.get("askida") or 0) + 1
        satir["son_askida_neden"] = x.get("neden")
        kirli = True
    for x in rep["stale"]:
        ad = x["name"]
        if ad in alarmed:
            continue                          # HİSTEREZİS: aşım sürüyor, aynı olgu ikinci kez anlatılmaz
        satir = _satir(ad)
        satir["son_gap_h"] = x["gap_h"]
        kirli = True
        if int(satir.get("alarm") or 0) >= GUNLUK_ALARM_TAVANI:
            # TEKİLLEŞTİRME TAVANI: bastırıldı ama KAYITLI — sayaç panoda görünür, hüküm kaybolmaz.
            satir["bastirilan"] = int(satir.get("bastirilan") or 0) + 1
            continue
        satir["alarm"] = int(satir.get("alarm") or 0) + 1
        obs.alarm("MECHANISM_STALE",
                  f"mekanizma gecikti: {ad} — {x['gap_h']} sa (pencere {x['expected_h']} sa)",
                  mechanism=ad, gap_h=x["gap_h"])
    # GÜN DÖNÜŞÜ DE BİR DEĞİŞİKLİKTİR: dünkü defter diskte kalırsa `api._alarm_gunluk` bugünün
    # sayaçları yerine dünün tablosunu servis eder ("bugün 7 alarm" diye okunan dünkü sayı).
    if kirli or store.read_json(ALARM_GUNLUK_FILE, {}).get("gun") != doc["gun"]:
        store.write_json(ALARM_GUNLUK_FILE, doc)
    store.write_json(ALARMED_FILE, sorted(now_stale))
    # #8 KORUMA (v209): bu poll'un kadansı (300 sn) bir RİSK kalemi için doğru olan kadanstır —
    # `check_integrity_and_alarm` günde bir kez koşar ve korumasız bir pozisyonu bir SONRAKİ seansa
    # taşırdı. Kendi try'ı var: koruma dedektörünün arızası mekanizma bekçisini GÖTÜREMEZ (aynı
    # yalıtım disiplini `integrity_report._tut`ta yazılı).
    try:
        check_koruma_and_alarm()
    except Exception as e:
        obs.warn("koruma_dedektoru_dustu", error=f"{type(e).__name__}: {e}",
                 detail="koruma bekçisi bu poll'da hüküm veremedi — mekanizma bekçisi koştu; "
                        "ölçülemeyen hüküm 'koruma var' sayılmaz")


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
    # ASKIDA ≠ AÇ (2026-08-03, WP-M ölçek borcu turu). Bu dedektörün TEK ayrımı "üretti mi?"ydi ve
    # kapı meta-kalibrasyonunda o soru YANLIŞ soruydu: mekanizma çift ÜRETİYOR ama birim borcu
    # yüzünden onları SAYAMIYOR. `n_measured=0` görüp "aç" demek, bir ölçüm borcunu bir üretim
    # arızası gibi raporlamaktı — operatör yanlış yerde arardı. `probgate` artık durumu adıyla
    # yazıyor; bekçi onu OKUR ve üçüncü bir kova açar. Dosya yoksa/eski şemadaysa `durum` None'dır
    # ve davranış BİREBİR eskisi gibi kalır (geriye uyum).
    _gate_durum = (store.read_json("gate_calibration.json", {}) or {}).get("durum")
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

    askida = []
    for name, n, need, note in checks:
        if name == "gate_calibration" and _gate_durum == "askida_olcek_borcu":
            # Çift ÜRETİLİYOR ama birim borcu yüzünden eşleştirilemiyor: ne aç, ne sabırlı.
            askida.append({"name": name, "have": n, "need": need, "note": note,
                           "durum": _gate_durum,
                           "beyan": (store.read_json("gate_calibration.json", {}) or {}
                                     ).get("durum_beyan")})
        elif n is None or n == 0:
            starved.append({"name": name, "note": note})          # HİÇ üretmemiş → hata şüphesi
        elif n < need:
            waiting.append({"name": name, "have": n, "need": need, "note": note})
        else:
            ok += 1
    return {"starved": starved, "waiting": waiting, "askida": askida, "ok": ok,
            "total": len(checks)}


def conservation_report(olaylar: list[dict] | None = None) -> dict:
    """#3 KORUNUM: giren her plan KAYITLI bir terminal duruma ulaşmalı — işleme dönüştü, kapıda
    reddedildi (NO_GO), ya da düşüşü OLAYLA kaydedildi. Hiçbirine uymayan plan = SESSİZ KAYIP
    (P4 buharlaşması ve seans atlaması tam olarak buydu; hiçbir alarm ötmemişti).

    `olaylar`: ham olay satırları elden verilebilir (v181 tek-okuma paylaşımı). PENCERE YASASI
    DEĞİŞMEZ — aşağıdaki `_gun` yine plan defterinden türer, yalnız süzülen liste paylaşılır."""
    plans = store.read_jsonl("trade_plans.jsonl")
    if not plans:
        return {"plans": 0, "unexplained": 0, "rows": []}
    traded = {str(t.get("plan_id")) for t in store.read_jsonl("trades.jsonl")}
    # PENCERE SATIR DEĞİL TARİH TABANLI, VE HÜKÜM VERİLEN PLANLARDAN TÜRETİLİR (C6, 2026-08-02).
    # Eski hâli `limit=8000` / `limit=20000` idi. Ölçüm (yerel defter, 27.403 satır): 8000 satır
    # yalnız SON 3 günü kapsıyordu ve K1'in az aşağıda yazdığı BROKER_REJECT düzeltmesi bugünkü
    # canlı defterde ÖLÜYDÜ — 4 reddin (UNP/NSC/TMO/RTX) satır indeksleri sondan 15-19 bin geride,
    # hepsi pencerenin DIŞINDA; rapor onları hâlâ "kayıtsız kayboldu" diye sayıyordu. Aynı dosyada
    # `events_since()` (bkz. aşağıda) tam bu ders için yazılmıştı ve parity_report ona geçirilmiş,
    # korunum raporu geçirilmemişti.
    #
    # PENCEREYİ NEDEN PLAN DEFTERİ BELİRLİYOR: bu rapor plan defterinin TAMAMINA hüküm verir —
    # sabit bir gün sayısı (7/30/90) seçmek aynı körlüğü daha yavaş biçimde geri getirirdi. En eski
    # plan hangi güne aitse pencere oraya kadar açılır; replay tohumu planları için bu "tüm defter"
    # demektir ve maliyeti sıfırdır (`store.read_jsonl` dosyayı zaten tam okuyup sonra dilimler).
    _tarihler = [str(p.get("date")) for p in plans if p.get("date")]
    try:
        _en_eski = dt.date.fromisoformat(min(_tarihler)) if _tarihler else None
        _gun = max(30, (dt.date.today() - _en_eski).days + 2) if _en_eski else 3650
    except Exception as e:
        # SESSİZ DEĞİL: plan tarihi ISO değilse pencere DARALTILMAZ, tam defter okunur — ölçüm
        # aracının biçim hatası yüzünden dedektörün görüş alanını kısmak, C6'nın ta kendisidir.
        _gun = 3650
        from . import obs
        obs.warn("conservation_plan_date_unparsable", error=f"{type(e).__name__}: {e}",
                 detail="pencere tam deftere açıldı (daraltma YOK)")
    pencere = events_since(_gun, olaylar=olaylar)   # TEK okuma: `dropped` ve `live_start` bundan
    dropped = set()
    for e in pencere:
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
    # SINIR DEFTERİN TAMAMINDAN OKUNUR, PENCEREDEN DEĞİL (C6): `limit=20000` ile ilk daily_cycle
    # 2026-07-22 görünüyordu, defterdeki GERÇEK ilk daily_cycle ise 2026-07-10 — aradaki 12 günde
    # açıklanamayan her plan `replay_era` ("körlük, sızıntı değil") sayılıp sessizce düşerdi.
    # Yukarıdaki pencere en eski PLANA kadar açık olduğu için ilk daily_cycle'ı yapısal olarak
    # kapsar (planlar daima olay defterinden eskidir ya da onunla yaşıttır).
    live_start = ""
    for e in pencere:
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
    except Exception as e:
        # FAIL-CLOSED (C22, 2026-08-02). Eski hâli `{"ok": True, "detail": "kontrol atlandı"}` idi ve
        # işaretinin gerekçesi ("sonuç KAYDA GEÇİYOR") FİİLEN YANLIŞTI: hiçbir obs.warn basılmıyordu
        # ve `detail` metnini okuyan TEK bir tüketici yoktu — üç tüketicinin (bu dosya :1086,
        # mutation.py:315, pano `_patOK`) üçü de yalnız `ok`a bakar. Yani ÖLÇÜLEMEYEN bir hüküm
        # "temiz" kılığında yeşile boyanıyordu; UYDURMA YASAĞI'nın tam karşılığı.
        # `olculemedi` MAKİNE-OKUNUR: alarm katmanı bunu "SESSİZ BAR MUTASYONU" diye değil
        # "ÖLÇÜLEMEDİ" diye adlandırır (bkz. check_integrity_and_alarm) — ölçülemeyen bir hükmü
        # ihlal diye anlatmak da bir uydurmadır.
        from . import obs
        obs.warn("determinism_bars_unreadable", error=f"{type(e).__name__}: {e}",
                 detail="bar dizini okunamadı — sessiz bar mutasyonu bu turda ÖLÇÜLEMEDİ "
                        "(taban ilerletilmedi; kanıt duruyor, tespit bir tur ertelendi)")
        return {"ok": False, "olculemedi": True, "error": f"{type(e).__name__}: {e}",
                "detail": "bar dizini okunamadı — ÖLÇÜLEMEDİ ('temiz' DEĞİL)"}
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


# ---- DEDEKTÖRLER ARASI TEK OKUMA (v181, 2026-08-03) -----------------------------------------
# CANLI ŞİKÂYET: "pano çok yavaşlamış" — ölçüm: `/api/diagnostics` 8,8-10,4 sn. Kökün bir yarısı
# burada: `integrity_report` olay defterini YEDİ KEZ baştan sona okuyup ayrıştırıyordu (parity 4×,
# korunum 1×, monotonluk 1×, defter-sözleşmesi 1× — sonuncusu ledgers.py'de, bu turun kapsamı
# dışında). C6'dan sonra pencereler TARİH tabanlı olduğu için hiçbiri satır limiti kullanmıyor ve
# `store.read_jsonl` zaten dosyanın TAMAMINI okuyup sonra dilimliyor (store.py:329-354) — yani
# yedi tam ayrıştırma, aynı 31 bin satır için. Rapor başına BİR okuma yeter: her pencere aynı ham
# listeden süzülür ve sonuç bit-bit aynıdır (pencere hesabının kendisi değişmiyor).
#
# NEDEN DEDEKTÖRLERE KWARG OLARAK GEÇİRİLMİYOR: C21'in yalıtım + DEĞERLEME SIRASI sözleşmesi,
# dedektörleri ARGÜMANSIZ saplamalarla değiştiren testlerle çivili (test_denetim_gozetim_v158:
# `def _patla(): raise ...`). Sweep'in `olaylar=` geçirmesi o saplamaları TypeError'a çevirirdi —
# yani bir hız düzeltmesi, kendisinden çok daha değerli bir sözleşmenin denetimini kırardı.
# Paylaşım bu yüzden bağlamdan akar; dedektör imzaları DEĞİŞMEZ. Opsiyonel `olaylar=` parametresi
# yine de her dedektörde durur: bağımsız çağıran (ve eşitlik çivisi) aynı listeyi ELDEN verebilsin.
#
# İPLİK-YEREL, MODÜL-GLOBAL DEĞİL: canlıda scheduler, hermes ve API iplikleri AYNI süreçte koşuyor.
# Global bir kutu, bir ipliğin okumasını başka bir ipliğin turunda YAŞI BEYANSIZ biçimde bayat
# gösterirdi — bu deponun kovaladığı kusur sınıfı. İpliğin kendi turu bitince kutu boşalır.
_PAYLASIM = threading.local()


def _olay_satirlari(limit: int | None = None, olaylar: list[dict] | None = None) -> list[dict]:
    """Olay defterinin HAM satırları: elden verilmişse o liste, yoksa turun paylaşılan okuması,
    o da yoksa diskten taze okuma. `limit` semantiği `store.read_jsonl` ile BİREBİR aynıdır
    (son `limit` satır) — paylaşılan liste dilimlenir, yeniden okunmaz."""
    rows = olaylar if olaylar is not None else getattr(_PAYLASIM, "olaylar", None)
    if rows is None:
        return store.read_jsonl("events.jsonl", limit=limit)
    return rows[-limit:] if limit else rows


def events_since(days: int, limit_hint: int | None = None,
                 olaylar: list[dict] | None = None) -> list[dict]:
    """Olay defterinin TARİH tabanlı penceresi (K1, 2026-07-30).

    NEDEN SATIR LİMİTİ YETMİYOR: `limit=4000` nominal hacimde (~1.700/gün) ~2,3 gün demekti; ama
    `hotstate_down` seli defterin %60'ını tek olaya çevirdi (canlı sayım 2026-07-30: 26.319 satırın
    15.863'ü) ve pencere ~16 SAATE düştü. Sonuç: satır-limitli her tüketici geçmişe kör oldu —
    `universe_coverage` kontrolü "işlenen seanslar tam evreni gördü" diyordu, oysa aynı defterde
    164 atlanmış seans yazılıydı. Gürültü, dedektörleri kapatan bir saldırı yüzeyine dönüştü.

    MALİYET ~SIFIR: `store.read_jsonl` dosyanın TAMAMINI okuyup sonra dilimliyor (store.py:182-200),
    yani satır limiti I/O tasarrufu ETMİYORDU — yalnız görüş alanını daraltıyordu. Burada aynı okuma
    yapılır, filtre ts üzerinedir. `limit_hint` yalnız çok uzun defterlerde üst sınır olarak durur.

    `olaylar` (v181): ham satırlar elden verilebilir — aynı turda ikinci kez okumamak için."""
    since = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=days)).isoformat()
    rows = _olay_satirlari(limit=limit_hint, olaylar=olaylar)
    # ts YOKSA SATIR ATILMAZ: damgasız bir satırı pencere dışı saymak, ölçülemeyen şeyi "yok"
    # saymak olurdu. Damgasızlar korunur; sıralama ISO-8601 sözlüksel kıyasıyla yapılır (obs.py
    # tek yazar ve hep aynı biçimde yazar: isoformat(timespec="seconds"), hepsi +00:00).
    return [e for e in rows if not e.get("ts") or str(e["ts"]) >= since]


# ---- EVREN KAPSAMASI: ŞU AN ile GEÇMİŞİN AYRILMASI (v206, 2026-08-07) --------------------------
# ÖLÇÜLEN ÇELİŞKİ (canlı A1, 2026-08-07): satır "165 seans evren kapsaması yetersiz olduğu için
# ATLANDI (son: 2026-07-29 %17) — kaynak yayınlamıyor" diyordu. Aynı defterde ölçülen gerçek:
#   * 165 sayısı OLAY sayısıdır, SEANS sayısı değil — yerel defter kopyasında 165 olay yalnız
#     YEDİ ayrık seansa aitti ve 159'u TEK seansa (2026-07-15) düşmüştü. O 159, scheduler'ın
#     `_rehydrate` düzeltmesinden (2026-07-22, scheduler.py:185) önceki tavan-unutma fırtınasıdır:
#     bir sayaç kusurunun kalıntısı, ikinci bir sayaç kusuru tarafından "165 seans" diye okunmuş.
#   * son atlanan seans 2026-07-29 — hükmün verildiği günden DOKUZ gün önce. Aradaki seanslarda
#     ölçülen kapsama 1,0 / 1,0 / 1,0 / 1,0 / 1,0 / 1,0 / 0,996 idi (canlı
#     `session_deferred_for_coverage` olayları). Yani BUGÜN kapsama sorunu YOK.
# Kusurun sınıfı: KALICI KIRMIZI. Bu deponun `alarm_delivery` satırında 2026-07-26'da tam olarak
# aynı hastalık tedavi edilmişti ("_toplam kümülatiftir ve azalmaz; satır bir kez kırmızıya
# döndüğünde sonsuza dek kırmızı kalıyordu... Kalıcı kırmızı bir dedektör, hiç olmayan bir
# dedektörle aynıdır") — reçete de aynıdır: HÜKÜM güncel pencereye bakar, KÜMÜLATİF SAYI ayrı bir
# alanda GÖRÜNÜR kalır ve ihlal ÜRETMEZ. İyileşme "hiç olmadı"ya çevrilmez; yalnız bayrak düşer.
#
# PENCERE NEDEN "SON N SEANS", NEDEN N=5: pencere DUVAR SAATİ değil SEANS sayar, çünkü kusurun
# yarısı tam olarak olay-sayısını-seans-sanmaktı; 159 olaylık tek bir fırtına, seans ekseninde
# bir (1) seanstır. N ise bekçinin uydurduğu bir sayı DEĞİL, motorun kendi yasasıdır:
# `loop.UNIVERSE_LAG_MAX_D` (=5) motorun bir seansın barını kovalamayı sürdürdüğü ufuktur — o
# ufkun ötesinde motor zaten pes etmiştir, yani orası TARİHTİR. Eşik de aynı yerden okunur
# (`loop.UNIVERSE_MIN_COVERAGE`) — scheduler.py:890'daki "tek yasa, tek ölçüm" ile aynı gerekçe.
KAPSAMA_PENCERE_SEANS = 5        # yedek beyan; asıl kaynak loop.UNIVERSE_LAG_MAX_D
KAPSAMA_ESIK = 0.90              # yedek beyan; asıl kaynak loop.UNIVERSE_MIN_COVERAGE

# Hangi olay hangi ALANDA seans kimliğini taşır. Adlar `event` ya da (alarma yükseltilmiş imzada)
# `kind` alanından okunur — K1'in dersi: yalnız yeni imzayı okumak dedektörü geçmişe kör bırakır.
_KAPSAMA_SEANS_ALANI: dict[str, str] = {
    "session_bar_never_published":    "session",        # İHLAL: seans atlandı
    "universe_coverage_low":          "date",           # İHLAL: hiçbir yakın seansta kapsama yok
    "session_deferred_for_coverage":  "index_session",  # SAĞLIKLI: T+1 ertelemesi (tasarım gereği)
    "session_bar_arrived_late":       "session",        # SAĞLIKLI: merdiven geç barı yakaladı
    "daily_cycle":                    "date",           # SAĞLIKLI: seans gerçekten işlendi
}
_KAPSAMA_IHLAL = ("session_bar_never_published", "universe_coverage_low")


def _yuzde(oran: float) -> str:
    """Ölçülen oranı yüzde olarak yazar. `:.0f` KULLANILMAZ: ölçülen 0,996'yı "%100" diye yazmak,
    tam kapsamayı KANITLANMAMIŞKEN iddia etmektir (bu dosyanın kovaladığı sınıfın küçük hâli)."""
    return f"%{100 * float(oran):.4g}"


def _kapsama_penceresi() -> tuple[int, float]:
    """Hüküm penceresi (seans) ve kapsama eşiği — İKİSİ DE motorun kendi sabitlerinden okunur."""
    try:
        from . import loop as _lp
        return (max(1, int(getattr(_lp, "UNIVERSE_LAG_MAX_D", KAPSAMA_PENCERE_SEANS))),
                float(getattr(_lp, "UNIVERSE_MIN_COVERAGE", KAPSAMA_ESIK)))
    except Exception as e:
        # YASA 4: sessiz-yutma DEĞİL. Motor sabitleri okunamazsa bekçi susmaz, kendi BEYANLI
        # yedeğiyle hüküm verir ve bunu duyurur — pencereyi ölçemeyen bir bekçi, penceresi
        # olmayan bir bekçiden daha tehlikelidir (sessizce başka bir yasaya göre hüküm verirdi).
        from . import obs
        obs.warn("kapsama_penceresi_okunamadi", error=f"{type(e).__name__}: {e}",
                 detail="motor sabitleri (UNIVERSE_LAG_MAX_D/MIN_COVERAGE) okunamadı — bekçi "
                        "watchdog'daki beyanlı yedek değerlerle hüküm veriyor")
        return KAPSAMA_PENCERE_SEANS, KAPSAMA_ESIK


def _kapsama_satiri(olaylar: list[dict]) -> dict:
    """`universe_coverage` satırı: HÜKÜM güncel pencereden, TARİH ayrı alandan.

    Sözleşmeler:
      * ÖLÇÜLEMEDİ ≠ 0 ≠ TEMİZ. Pencerede hiç kapsama kanıtı yoksa sayılar None döner ve metin
        "ÖLÇÜLEMEDİ" der — "işlenen seanslar tam evreni gördü" cümlesi kanıtsız KURULMAZ.
      * Bekçi ZAYIFLAMAZ: güncel penceredeki her ihlal hâlâ ok=False üretir. Seans kimliği OLMAYAN
        bir ihlal olayı GÜNCEL sayılır — tarihlendiremediğimiz bir ihlali "geçmiş" saymak, ölçemediğimiz
        şeyi lehimize yorumlamak olurdu.
      * Tarihsel sayı KAYBOLMAZ ama İHLAL ÜRETMEZ; ayrıca AYRIK SEANS ile OLAY SAYISI ayrı ayrı
        yazılır (kusurun ta kendisi bu ikisini birbirine karıştırmaktı)."""
    pencere_n, esik = _kapsama_penceresi()

    kanit: list[tuple[str, dict]] = []
    for e in olaylar:
        ad = str(e.get("event") or "")
        if ad not in _KAPSAMA_SEANS_ALANI:
            ad = str(e.get("kind") or "")          # alarma yükseltilmiş imza adı `kind`'da taşır
            if ad not in _KAPSAMA_SEANS_ALANI:
                continue
        kanit.append((ad, e))

    def _seans(ad: str, e: dict) -> str | None:
        v = e.get(_KAPSAMA_SEANS_ALANI[ad])
        return str(v) if v else None

    def _kapsama(e: dict) -> float | None:
        for alan in ("universe_coverage", "coverage"):
            v = e.get(alan)
            if v is not None:
                try:
                    return float(v)
                except (TypeError, ValueError):
                    # sessiz-yutma: ayrıştırılamayan bir ÖLÇÜ, ölçünün YOKLUĞUdur — None döner ve
                    # metin o cümleyi hiç kurmaz. Uyarı basılmaz çünkü bu dal bozuk satır BAŞINA
                    # ateşlenir: tek bozuk defter satırı, alarm bütçesini tek başına yakabilirdi
                    # (EEMUA). Bozukluk zaten defter sözleşmesi dedektörünün (`ledger_contract`)
                    # işidir; burada yapılacak tek dürüst şey, olmayan ölçüyü UYDURMAMAKtır.
                    return None
        return None

    # Seans ekseni: ISO tarihler sözlüksel sıralamada kronolojiktir (obs tek yazar, tek biçim).
    seanslar = sorted({s for ad, e in kanit if (s := _seans(ad, e))})
    pencere = set(seanslar[-pencere_n:])

    guncel, tarihsel = [], []
    for ad, e in kanit:
        if ad not in _KAPSAMA_IHLAL:
            continue
        s = _seans(ad, e)
        (guncel if (s is None or s in pencere) else tarihsel).append((ad, e, s))

    # TARİHSEL MUHASEBE: ayrık seans ve olay sayısı AYRI. (165 olay = 7 seans; 159'u tek seansta.)
    _ihl_hepsi = guncel + tarihsel
    _ayrik = sorted({s for _a, _e, s in _ihl_hepsi if s})
    _seanssiz = sum(1 for _a, _e, s in _ihl_hepsi if not s)
    _guncel_seans = sorted({s for _a, _e, s in guncel if s})

    ok = not guncel
    satir: dict = {
        "check": "universe_coverage", "ok": ok,
        "pencere_seans": pencere_n, "kapsama_esigi": esik,
        "guncel_ihlal_seans": len(_guncel_seans) + sum(1 for _a, _e, s in guncel if not s),
        "guncel_ihlal_olay": len(guncel),
        "tarihsel_ihlal_seans": len(_ayrik) + _seanssiz,
        "tarihsel_ihlal_olay": len(_ihl_hepsi),
        "tarihsel_son_seans": (_ayrik[-1] if _ayrik else None),
        "olculemedi": False,
    }

    if not kanit:
        # ÖLÇÜLEMEDİ: kapsamayı konuşan tek bir satır bile yok. Bu "temiz" DEĞİLDİR.
        satir.update(olculemedi=True, guncel_ihlal_seans=None, guncel_ihlal_olay=None,
                     tarihsel_ihlal_seans=None, tarihsel_ihlal_olay=None,
                     detail=(f"ÖLÇÜLEMEDİ: defter penceresinde tek bir kapsama kanıtı yok "
                             f"(atlama/erteleme/işlenmiş seans) — kapsama hükmü VERİLEMEDİ, "
                             f"'temiz' DEĞİL; hüküm penceresi son {pencere_n} seans, "
                             f"eşik {_yuzde(esik)}"))
        return satir

    # SON ÖLÇÜLEN KAPSAMA: pencerenin en yeni, kapsama TAŞIYAN kanıtı. (Metin bunu uydurmaz —
    # ölçü yoksa cümle de kurulmaz.)
    _son_olcum = None
    for ad, e in kanit:
        s, c = _seans(ad, e), _kapsama(e)
        if c is not None and (s is None or s in pencere):
            _son_olcum = (s, c, ad)
    satir["son_olculen_kapsama"] = None if _son_olcum is None else _son_olcum[1]

    # TARİHSEL GÖVDE: sayı GÖRÜNÜR kalır, ama ETİKETİ hükme göre değişir. Güncel pencerede ihlal
    # varken bu toplamın bir kısmı ZATEN güncel ihlaldir; ona toptan "İHLAL DEĞİL" demek, az önce
    # düzelttiğimiz karıştırmanın simetrik hâli olurdu.
    _tarih_govde = (f"{len(_ayrik) + _seanssiz} ayrık seans / {len(_ihl_hepsi)} alarm satırı"
                    + (f", sonuncusu {_ayrik[-1]}" if _ayrik else "")) if _ihl_hepsi else ""
    _tarih_notu = (f" · DEFTER TOPLAMI (30 günlük okuma penceresi): {_tarih_govde}"
                   if _tarih_govde else "")
    _olcum_notu = ""
    if _son_olcum is not None:
        _olcum_notu = (f", son ölçülen kapsama {_yuzde(_son_olcum[1])}"
                       + (f" ({_son_olcum[0]})" if _son_olcum[0] else ""))

    if guncel:
        _atlanan = [s for _a, _e, s in guncel if _a == "session_bar_never_published"]
        _dusuk = [(_e, s) for _a, _e, s in guncel if _a == "universe_coverage_low"]
        parcalar = []
        if _atlanan:
            _u = sorted({s for s in _atlanan if s})
            # LİSTE KIRPILIRSA BUNU SÖYLE: "4 seans ATLANDI (a, b, c)" okuyucuya dördüncüyü
            # arattırır ve sayının yanlış olduğunu düşündürür — kırpma GÖRÜNÜR olmalı.
            _gos = ("…, " if len(_u) > 3 else "") + ", ".join(_u[-3:])
            parcalar.append(f"{len(_u) or len(_atlanan)} seans ATLANDI"
                            + (f" ({_gos})" if _u else " (seans kimliği YOK)"))
        if _dusuk:
            _ue = sorted({s for _e, s in _dusuk if s})
            _c = _kapsama(_dusuk[-1][0])
            parcalar.append(f"{len(_ue) or len(_dusuk)} seansta kapsama yetersiz"
                            + (f" (son: {_ue[-1]} {_yuzde(_c)})" if _ue and _c is not None else ""))
        # KAYNAK İDDİASI ÖLÇÜMDEN TÜRER: "kaynak yayınlamıyor" ancak GÜNCEL pencerede atlama
        # varsa kurulabilir — ve o zaman bile geçmiş zamanla, çünkü ölçtüğümüz şey o seanslardır.
        satir["detail"] = (f"GÜNCEL (son {pencere_n} seans): " + " · ".join(parcalar)
                           + (" — bu seanslarda kaynak barı yayınlamadı" if _atlanan else "")
                           + _olcum_notu + _tarih_notu)
        return satir

    # GÜNCEL PENCERE TEMİZ. Tarih varsa görünür kalır, bayrak DÜŞER.
    # PENCERENİN YAŞI YAZILIR: kanıt akışı durursa (motor sustuysa) pencere DONAR ve yeşil kalır —
    # bu davranış eski hükümde de vardı, ama görünmezdi. Motorun ölümü başka dedektörlerin işi
    # (nabız/mekanizma sağlığı); burada yapılacak dürüst şey, hükmün hangi güne dayandığını
    # SÖYLEMEKTİR. Yeni bir eşik/alarm icat edilmez (alarm bütçesi yasası).
    satir["detail"] = (f"GÜNCEL (son {pencere_n} seans, son kanıt "
                       f"{seanslar[-1] if seanslar else 'seanssız'}): kapsama ihlali YOK — "
                       f"{len(pencere)} seansta evren eşiği ({_yuzde(esik)}) tuttu"
                       + (f"{_olcum_notu}; kaynak YAYINLIYOR" if _son_olcum is not None else "")
                       + (f" · TARİHSEL (hüküm penceresinin DIŞINDA, İHLAL DEĞİL): {_tarih_govde}"
                          if _tarih_govde else ""))
    return satir


def parity_report(olaylar: list[dict] | None = None) -> dict:
    """Canlı üretim oranları ile beklenen oranların kıyası. Her satır: {check, ok, detail}.

    `olaylar`: ham olay satırları elden verilebilir (v181). Bu rapor defteri DÖRT kez okuyordu
    (aşağıdaki 4000-satırlık dilim + 30/2/1 günlük üç pencere); dördü de aynı listeden süzülür."""
    from . import config as _cfg, notify as _nt
    rows = []
    cycles = [e for e in _olay_satirlari(limit=4000, olaylar=olaylar)
              if e.get("event") == "daily_cycle"]
    recent = cycles[-30:]

    # 1) EVREN KAPSAMASI — kararların alındığı seans evreni gerçekten görüyor mu?
    #    (bulunan hatanın ta kendisi: %18'lik yanlı kesitte karar)
    # TARİH TABANLI PENCERE (K1): satır limiti bu kontrolü kör ediyordu — bkz. events_since().
    # SEANS ATLAMA — DEDEKTÖRÜN KÖR NOKTASI KAPATILIYOR (K1, 2026-07-30). Bu kontrol yalnız
    # `universe_coverage_low`a bakıyordu ve o olay canlıda 0 kez ateşlenmiş; bu yüzden ok=True
    # diyordu. Oysa `session_bar_never_published` 164 kez düşmüş: motor o seansları kapsama
    # yüzünden TERK ETMİŞ ve dedektör "işlenen seanslar tam evreni gördü" diye rapor veriyordu.
    # İKİ İMZA BİRDEN okunur: tarihsel satırlar `event` adıyla yazıldı (warn dönemi), K1'den
    # sonraki satırlar DATA_QUALITY alarmı olduğu için adı `kind` alanında taşıyor. Yalnız yeni
    # imzayı okumak dedektörü geçmişe kör bırakırdı — `failed_broker_rejection` dersinin tersi.
    # HÜKÜM ile TARİH v206'da AYRILDI (bkz. `_kapsama_satiri`): okuma penceresi (30 gün) tarihi
    # taşımayı sürdürür, `ok` yalnız son N SEANSA bakar.
    rows.append(_kapsama_satiri(events_since(30, olaylar=olaylar)))

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
    _dom_win = events_since(2, olaylar=olaylar)
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
    _hot_down = [e for e in events_since(1, olaylar=olaylar)
                 if str(e.get("event")) == "hotstate_down"]
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
    # KANAL BAĞLIYKEN DÜŞEN TESLİMAT (C7, 2026-08-02): `obs._maybe_notify` artık `notify.send`
    # False dönerse de sayar. Bu satırın metni bu ayrımı YAPMAK ZORUNDA — yığının "kanal YOKKEN
    # toplandığını" söylemek, yığın kanal BAĞLIYKEN düşen teslimatlardan oluşuyorsa uydurmadır.
    _fail = int(_und.get("_teslim_hatasi") or 0)
    if _tot:
        _tokens = ", ".join(f"{k}×{v}" for k, v in sorted(_und.items()) if not k.startswith("_"))
        # Metin, `notify.configured()` GERÇEĞİNDEN üretilir. Eski hâli kanal bağlıyken bile
        # "bildirim kanalı yapılandırılmamış" diyordu — sayaç geçmişte birikmiş olabilir ve o metin
        # bugünün durumunu YANLIŞ anlatıyordu; yanlış teşhis yanlış müdahaleyi doğurur.
        if _kalan == 0:
            _detail = (f"birikmiş {_tot} alarmın tamamı okundu (ACK ile soğuruldu) — "
                       f"kalıntı yok ({_tokens})")
        elif _cfg:
            _detail = (f"kanal bağlı, {_kalan} birikmiş (ACK ile soğurulur) — "
                       + (f"bunun {_fail} tanesi kanal BAĞLIYKEN teslim EDİLEMEDİ "
                          f"(notify.send False döndü — uzak uç cevap vermiyor)"
                          if _fail else "bu yığın kanal YOKKEN toplandı")
                       + f" ({_tokens}); teslim edilmiş değil, yalnız yerel gelen "
                         f"kutusunda duruyor")
        else:
            _detail = (f"{_kalan} alarm TESLİM EDİLEMEDİ ({_tokens}) — bildirim kanalı "
                       f"yapılandırılmamış (Telegram/webhook). Dedektörler çalışıyor ama "
                       f"kimse duymuyor."
                       + (f" Ayrıca {_fail} teslimat kanal BAĞLIYKEN düşmüştü." if _fail else ""))
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


# DÜŞEN DEDEKTÖRÜN İSKELETİ (C21): yalnız tüketicilerin KÖŞELİ PARANTEZLE indekslediği alanlar.
# Boş liste "bulgu yok" demez, "bu turda ölçülmedi" der — hükmü `dedektor_dustu`/`olculemedi`
# taşır ve alarm katmanı onu adıyla duyurur (check_integrity_and_alarm).
_DEDEKTOR_BOS: dict[str, dict] = {
    "production":   {"starved": [], "waiting": [], "total": 0},
    "conservation": {"plans": 0, "unexplained": 0, "rows": []},
    "determinism":  {},
    "coherence":    {"stale": [], "total": 0},
    "monotonicity": {"regressions": [], "amnestied": [], "tracked": 0},
    "ownership":    {"lost": []},
    "parity":       {"rows": [], "n_cycles": 0},
}


def integrity_report(persist: bool = False) -> dict:
    """YEDİ dedektörü tek çağrıda topla (teşhis paneli + öz-değerlendirme buradan okur).
    7. desen (parity/makullük) 2026-07-21'de eklendi: ilk altısı bileşen bazlıdır ve 'doğru
    parçalar, yanlış sistem sonucu' sınıfını göremez — motorun evrenin %18'inde karar verdiği
    hata tam olarak o sınıftandı.

    DEĞERLEME SIRASI SÖZLEŞMESİ (C21, 2026-08-02): `parity_report()` persist'li ÜÇLÜDEN
    (determinism/monotonicity/ownership) ÖNCE değerlenir. Eski hâlde parity sözlük literalinde EN
    SON duruyordu; Python sözlük değerlerini soldan sağa değerlediği için üçlü TABANINI DİSKE
    YAZDIKTAN sonra parity çağrılıyordu. parity_report korumasız fırlatma yüzeyleri taşır
    (store okumaları, `_lg.validate_live`, `_rc.report()`, `_sv.report()`); biri fırlarsa
    `check_integrity_and_alarm` hiçbir alarm üretmeden düşer, `integrity_alarmed.json` yazılmaz,
    ama YENİ TABAN çoktan yazılmıştır — o turun gerilemesi bir sonraki turda prev==cur olduğu için
    KALICI olarak kaybolur. Bu, persist kapısının kendi gerekçesinin (bkz. determinism_report
    docstring'i) istisna yolunda birebir tekrarıydı.

    DEDEKTÖR-BAŞINA YALITIM: düşen bir dedektör diğerlerini GÖTÜRMEZ; `{"ok": False,
    "dedektor_dustu": True, "error": ...}` döner ve alarm katmanı bunu adıyla duyurur. Yalıtımın
    iskeleti (`_DEDEKTOR_BOS`) şart: tüketiciler alt alanları köşeli parantezle indeksliyor
    (bu dosyada :1086+, mutation.py:311-313, pano app.js:3677-3690) — iskeletsiz bir hata sözlüğü
    yalıtımı çağıranda KeyError'a çevirirdi, yani hiç yalıtmamış olurdu.

    TEK OKUMA (v181, 2026-08-03): olay defteri turun BAŞINDA bir kez okunur ve dedektörler onu
    paylaşır (bkz. `_olay_satirlari` üstündeki gerekçe). Dedektör imzaları ve çağrı biçimi
    DEĞİŞMEDİ — paylaşım iplik-yerel bağlamdan akar, çünkü C21 sözleşmesi dedektörleri argümansız
    saplamalarla sınıyor."""
    def _tut(ad: str, fn) -> dict:
        try:
            return fn()
        except Exception as e:
            from . import obs
            obs.warn("integrity_detector_failed", detector=ad, error=f"{type(e).__name__}: {e}",
                     detail="bu dedektör BU TURDA hüküm veremedi — diğerleri koştu; "
                            "ölçülemeyen hüküm 'temiz' sayılmaz")
            return {**_DEDEKTOR_BOS.get(ad, {}), "ok": False, "dedektor_dustu": True,
                    "olculemedi": True, "error": f"{type(e).__name__}: {e}"}

    try:
        _ham = store.read_jsonl("events.jsonl")
    except Exception as e:
        # PAYLAŞILAN OKUMANIN ARIZASI YEDİ DEDEKTÖRÜ BİRDEN DÜŞÜREMEZ (C21 yalıtımı burada da
        # geçerli): okuma düşerse `None` bırakılır ve her dedektör bugüne kadarki gibi KENDİ
        # okumasını yapar — o zaman düşen dedektör tek başına düşer. Hız kaybı, yalıtım kaybından
        # ucuzdur. Sessiz de kalmaz: "yavaş yola düşüldü" ölçülebilir bir olgudur.
        _ham = None
        from . import obs
        obs.warn("integrity_shared_events_read_failed", error=f"{type(e).__name__}: {e}",
                 detail="dedektörler kendi okumasına düştü — hüküm aynı, tur yalnızca yavaş")
    _PAYLASIM.olaylar = _ham
    try:
        _par = _tut("parity", parity_report)  # ÖNCE — persist'li üçlü tabanı yazmadan ÖNCE düşsün
        # Anahtar SIRASI korunur (pano ve öz-değerlendirme bu sırayla basar); değişen yalnız
        # DEĞERLEME sırasıdır — `_par` yukarıda hesaplandı.
        return {"production": _tut("production", production_report),
                "conservation": _tut("conservation", conservation_report),
                "determinism": _tut("determinism", lambda: determinism_report(persist=persist)),
                "coherence": _tut("coherence", coherence_report),
                "monotonicity": _tut("monotonicity", lambda: monotonicity_report(persist=persist)),
                "ownership": _tut("ownership", lambda: ownership_report(persist=persist)),
                "parity": _par}
    finally:
        # TUR BİTTİ, KUTU BOŞALIR: paylaşılan liste bu turun fotoğrafıdır. Bırakılsaydı bir sonraki
        # BAĞIMSIZ `parity_report()` çağrısı, yaşı beyansız eski bir defteri okurdu.
        _PAYLASIM.olaylar = None


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


# =============================================================================================
# ALARM BÜTÇESİ (WP-P/P2, 2026-08-01) — "kaç alarm ürettik" sorusunun EEMUA 191 merceği.
# ---------------------------------------------------------------------------------------------
# NİYE VAR: bu depoda alarm ÜRETİMİ ölçülüyordu (her jeton bir satır), alarm YÜKÜ hiç ölçülmüyordu.
# Klinik ve kontrol-odası kanıtının ortak bulgusu şu: bir operatörü kör eden şey tek bir kaçırılmış
# alarm değil, bakılamayacak kadar çok alarmdır. EEMUA 191 bu yüzden bir BÜTÇE tanımlar — üretim
# hızının kendisi bir ölçüttür.
#
# SEVİYE EŞLEMESİ BEYANLIDIR VE EKSİKTİR (uydurma yasağı):
# `obs._emit` ÜÇ seviye basar — "info", "warn", "alarm". EEMUA'nın üç önceliğiyle birebir örtüşmez:
#   warn  → low         (bir insanın gün içinde bakması beklenen; karar yolunu durdurmaz)
#   alarm → high        (bildirim zincirine giren sınıf: NOTIFY_TOKENS + 6 sa susturma penceresi)
#   emergency → ÜRETİCİSİ YOK. Bu seviyeyi basan tek satır kod yok. Sayacı 0 yazmak "ölçtük, hiç
#   acil alarm çıkmadı" demek olurdu; gerçek ise "bu sistem acil sınıfını HİÇ ÜRETEMİYOR". İkisi
#   aynı şey değil — alan None kalır ve gerekçesi `emergency_neden` ile BİRLİKTE taşınır.
# `info` bütçeye GİRMEZ: bir alarm değil, bir kayıt satırıdır. Bütçeye katılsaydı gürültünün
# kendisi bütçeyi doldurur ve ölçüt anlamını yitirirdi.
SEVIYE_EEMUA = {"warn": "low", "alarm": "high"}
EEMUA_HEDEF_YUZDE = {"low": 80, "high": 15, "emergency": 5}   # EEMUA 191 öncelik dağılımı hedefi

ALARM_PENCERE_S = 24 * 3600           # bütçe penceresi — "son 24 saat"
ALARM_TEPE_PENCERE_S = 10 * 60        # tepe ölçümünün kayan penceresi
ALARM_TEPE_TAVAN = 10                 # EEMUA 191: kabul edilebilir tepe ≤10 alarm / 10 dk
ALARM_DURAN_TAVAN = 10                # EEMUA 191: aynı anda DURAN alarm ≤10

# ---- RESTART-PATLAMASI MUAFİYETİ (küçük-kuyruk turu, 2026-08-02) -----------------------------
# BU SAYILAR ÖLÇÜLDÜ, SEÇİLMEDİ. Canlı defter (A1, /opt/meridian/state/events.jsonl, 31.040 satır;
# 24 saatlik bütçe penceresinde 459 warn+alarm, damgasız 0, bozuk 0):
#   * ham 10 dk tepesi          = 18   (tavan 10 → AŞIM)   pencere başı 2026-08-02T16:48:03Z
#   * tepe penceresinin 18 satırının 15'i, 16:52:11Z restart'ının +4s..+85s aralığında
#   * restart pencereleri içi yoğunluk 8,9 satır/10dk · dışı 2,85 satır/10dk → 3,1×
#   * restart penceresi HARİÇ tepe = 5 (muafiyet 3/5/10/15 dk'nın DÖRDÜNDE de aynı 5 çıkıyor;
#     kalan tepe restart'sız bir pencerede, 02:57:31Z)
#   * YALNIZ restart pencerelerinde görülen jetonlar (dışarıda SIFIR kez): warmup_coverage_short
#     (22), hermes_brain_unavailable (7), hermes_bg_proposal_rejected (7), io_latency_high (4),
#     hermes_brain_failed (4), hermes_brain_empty (2) — açılış sınıfı, süregelen arıza değil.
# HÜKÜM: tepe GERÇEK ve restart kaynaklı → muafiyet EKLENDİ.
# PENCERE NEDEN 5 DK: ölçülen patlama kütlesi restart+85 sn'de bitiyor ve 3 dk'lık muafiyet zaten
# tabanı geri veriyor; 5 dk ölçülen kuyruğun ~3,5 katı bir emniyet payıdır AMA tepe penceresinin
# (10 dk) YARISINI muaf tutmaz — yani restart'tan 5-10 dk SONRA süren gerçek bir alarm fırtınası
# hâlâ sayılır ve tavanı deler. Daha geniş bir pencere seçmek, korumak istediğimiz şeyi de körleştirirdi.
ALARM_RESTART_MUAFIYET_S = 5 * 60
# Restart'ın ÖLÇÜLEN sinyali. `scheduler._rehydrate()` her süreç doğumunda BİR kez `info` seviyesinde
# yazar (scheduler.py:96) ve seviyesi `info` olduğu için bütçenin kendi sayacına ZATEN girmez.
# EŞLEŞME KANITI (aynı canlı defter, aynı 24 saat): 11 `scheduler_state_rehydrated` damgası vs
# systemd journal'ındaki 11 "Started meridian.service" damgası — 11/11, fark 0..3 sn.
# NEDEN BU, `scheduler_status.json`ın `started_at`i DEĞİL: `started_at` YALNIZ o an koşan sürecin
# doğumunu taşır (24 saatlik pencerede 11 restart'ın 10'u görünmez); defterdeki jeton pencerenin
# TAMAMINI kapsar. Uydurma sinyal yok — ikisi de zaten yazılan, ölçülmüş kayıtlar.
ALARM_RESTART_JETONU = "scheduler_state_rehydrated"

_ALARM_CACHE: dict = {}
ALARM_TTL_S = 30.0


def _alarm_tepe(damgalar: list[float]) -> tuple[int, str | None]:
    """En yoğun `ALARM_TEPE_PENCERE_S` penceresindeki alarm sayısı + o pencerenin başlangıcı.

    Kayan pencere, O(n): damgalar artan sırada gelir; sol kenar pencereden düşeni atar."""
    if not damgalar:
        return 0, None
    en, en_i, sol = 0, 0, 0
    for sag in range(len(damgalar)):
        while damgalar[sag] - damgalar[sol] > ALARM_TEPE_PENCERE_S:
            sol += 1
        if sag - sol + 1 > en:
            en, en_i = sag - sol + 1, sol
    return en, dt.datetime.fromtimestamp(damgalar[en_i], dt.timezone.utc).isoformat(
        timespec="seconds")


def alarm_budget() -> dict:
    """Son 24 saatin alarm bütçesi: EEMUA dağılımı + 10 dk tepe + duran alarm sayısı.

    PENCERE TARİH TABANLIDIR, satır limitli DEĞİL (`events_since` — K1 dersi: satır limiti
    `hotstate_down` selinde pencereyi 16 saate düşürmüştü). Yani sayılar bir ALT SINIR değil,
    defterin tamamı üzerinden ölçülmüş gerçek sayılardır.

    DAMGASIZ SATIR AYRI SAYILIR: `events_since` ts'siz satırı pencerede TUTAR (ölçülemeyeni yok
    saymamak için) ama bir zaman noktasına oturtulamayan satır tepe hesabına giremez. 24 saatlik
    sayıma katmak "bu satır bu pencerede oldu" iddiası olurdu — ölçüm yokken bir iddia."""
    olaylar = events_since(1)
    simdi = _now()
    sinir = simdi - ALARM_PENCERE_S
    dagilim = {"low": 0, "high": 0}
    damgalar: list[float] = []
    restartlar: list[float] = []
    damgasiz = 0
    for e in olaylar:
        ts = e.get("ts")
        if str(e.get("event") or "") == ALARM_RESTART_JETONU and ts:
            # Restart damgası AYRI toplanır ve bütçe sayacına GİRMEZ (seviyesi zaten `info`).
            try:
                _tr = dt.datetime.fromisoformat(str(ts)).timestamp()
            except (TypeError, ValueError):  # sessiz-yutma: bozuk damgalı restart satırı muafiyet üretemez — muafiyetsiz saymak DAHA SIKI tarafta hata yapmaktır, maskeleme yönünde değil
                _tr = None
            if _tr is not None and _tr >= sinir - ALARM_RESTART_MUAFIYET_S:
                restartlar.append(_tr)
        oncelik = SEVIYE_EEMUA.get(str(e.get("level") or ""))
        if oncelik is None:                     # info — bütçeye girmez (bkz. blok başlığı)
            continue
        if not ts:
            damgasiz += 1
            continue
        try:
            t = dt.datetime.fromisoformat(str(ts)).timestamp()
        except (TypeError, ValueError):  # sessiz-yutma: bozuk damga SAYIYA GİRMEZ ama kaybolmaz — `damgasiz` sayacında dürüstçe görünür
            damgasiz += 1
            continue
        if t < sinir:
            continue
        dagilim[oncelik] += 1
        damgalar.append(t)
    damgalar.sort()
    restartlar.sort()
    # TEPE İKİ KEZ ÖLÇÜLÜR. `tepe_ham_10dk` muafiyetsiz gerçektir ve HER ZAMAN taşınır — muafiyetin
    # sakladığı sayı görünür kalmadan "sessiz maskeleme yasağı" bir slogan olurdu. Tavanla kıyaslanan
    # (`asim.tepe`) ise muafiyetli değerdir: restart'ın kendi açılış gürültüsü operatörü uyandırmaz.
    tepe_ham, tepe_ham_basi = _alarm_tepe(damgalar)
    muaf = [t for t in damgalar
            if any(r <= t <= r + ALARM_RESTART_MUAFIYET_S for r in restartlar)]
    kalan = [t for t in damgalar if not any(r <= t <= r + ALARM_RESTART_MUAFIYET_S for r in restartlar)]
    tepe, tepe_basi = _alarm_tepe(kalan)
    muafiyet_uygulandi = bool(muaf) and tepe != tepe_ham

    duran = store.read_json(ALARMED_FILE, [])
    duran_adlar = sorted(str(x) for x in duran) if isinstance(duran, list) else []
    n_duran = len(duran_adlar)

    toplam = dagilim["low"] + dagilim["high"]
    # YÜZDE PAYDASI ÖLÇÜLENDİR: emergency üretilemediği için payda low+high'tır ve bu payda
    # `yuzde_beyan` ile birlikte taşınır — %85/%15 okuyan biri bunu 80/15/5 hedefiyle
    # kıyaslarken paydanın eksik olduğunu BİLMEK zorunda.
    yuzde = ({"low": round(100 * dagilim["low"] / toplam, 1),
              "high": round(100 * dagilim["high"] / toplam, 1),
              "emergency": None} if toplam else {"low": None, "high": None, "emergency": None})
    asim = {"tepe": tepe > ALARM_TEPE_TAVAN, "duran": n_duran > ALARM_DURAN_TAVAN}
    return {
        "pencere_s": ALARM_PENCERE_S,
        "dagilim": {**dagilim, "emergency": None},
        "toplam": toplam,
        "yuzde": yuzde,
        "hedef_yuzde": dict(EEMUA_HEDEF_YUZDE),
        "tepe_10dk": tepe, "tepe_basi": tepe_basi, "tavan_10dk": ALARM_TEPE_TAVAN,
        # ---- RESTART MUAFİYETİNİN BEYANI (sessiz maskeleme yasağı) ----
        "tepe_ham_10dk": tepe_ham, "tepe_ham_basi": tepe_ham_basi,
        "tepe_muafiyet_s": ALARM_RESTART_MUAFIYET_S,
        "tepe_restart_n": len(restartlar),
        "tepe_muaf_satir": len(muaf),
        "tepe_muafiyet_uygulandi": muafiyet_uygulandi,
        "tepe_beyan": (
            f"tepe: {tepe} (restart-muafiyetli) — ham {tepe_ham}; "
            f"{len(restartlar)} restart × {ALARM_RESTART_MUAFIYET_S // 60} dk penceresinde "
            f"{len(muaf)} satır tepe SAYACINDAN düşüldü (24 saatlik dağılımda AYNEN duruyorlar). "
            f"Restart sinyali: `{ALARM_RESTART_JETONU}` olayı."
            if muafiyet_uygulandi else
            (f"tepe: {tepe} (muafiyet uygulanmadı — pencerede {len(restartlar)} restart var ama "
             f"tepe sayısını değiştirmedi; ham {tepe_ham})"
             if restartlar else
             f"tepe: {tepe} (muafiyet uygulanmadı — pencerede `{ALARM_RESTART_JETONU}` damgası YOK, "
             f"yani restart ölçülemedi; sayı HAM)")),
        "duran": n_duran, "duran_adlar": duran_adlar[:8], "tavan_duran": ALARM_DURAN_TAVAN,
        "damgasiz": damgasiz,
        "asim": asim, "asim_var": bool(asim["tepe"] or asim["duran"]),
        "eslemem": dict(SEVIYE_EEMUA),
        "emergency_neden": ("obs.py'de 'emergency' seviyesini basan kod YOK — sayaç 0 değil None. "
                            "0 yazmak 'ölçtük, acil alarm çıkmadı' demek olurdu; gerçek şu ki bu "
                            "sistem acil sınıfını üretemiyor."),
        "yuzde_beyan": ("payda YALNIZ low+high — emergency üretilemediği için 80/15/5 hedefinin "
                        "üçüncü dilimi bu sistemde ÖLÇÜLEMEZ, sıfır değil."),
        "duran_beyan": ("duran alarm = `watchdog_alarmed.json` — penceresini aşmış ve HÂLÂ aşmakta "
                        "olan mekanizmalar. Toparlanan mekanizma listeden düşer."),
    }


def alarm_budget_cached() -> tuple[dict, float]:
    """Panonun okuduğu alarm bütçesi + kaç saniye önce hesaplandığı.

    `integrity_report_cached` ile AYNI desen ve aynı gerekçe: `/api/diagnostics` 20 saniyede bir
    yoklanıyor ve bu hesap 27 bin satırlık olay defterini baştan sona okuyor. TTL bayatlığı
    SINIRLAR, `age` onu GÖRÜNÜR yapar — pano taze gibi göstermez."""
    import time as _t
    from . import config as _cfg
    # ÖNBELLEK ANAHTARI `config.STATE` İÇERİR ve bu bir ayrıntı değil: ölçümler kum havuzu
    # kopyasında koşuyor (config.STATE yönlendirmesi). Anahtarsız bir süreç-içi önbellek, kum
    # havuzuna geçen bir çağrıya CANLI defterin sayılarını döndürürdü — ölçüm turlarının en
    # sinsi kirlenme yolu, üstelik sessiz. Yön değişince önbellek kendiliğinden ıskalar.
    anahtar = str(getattr(_cfg, "STATE", ""))
    now = _t.monotonic()
    hit = _ALARM_CACHE.get(anahtar)
    if hit is not None:
        rep, at = hit
        if (now - at) < ALARM_TTL_S:
            return rep, round(now - at, 1)
    rep = alarm_budget()
    _ALARM_CACHE.clear()          # tek girdi yeter; havuz anahtarları birikip sızıntı yapmasın
    _ALARM_CACHE[anahtar] = (rep, now)
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
    # TABAN SAHİPLİĞİ (C21 düzeltmesi, 2026-08-02): burası CANLI state'te tabanı ilerleten TEK
    # yoldur, ama "tek sahip" cümlesi mutlak biçimde YANLIŞTI — `mutation.py:310` da
    # `integrity_report(persist=True)` çağırır. Aradaki fark yönlendirmedir, çağrı değil:
    # mutation.py `_LIVE_STATE` koruması ve `_state_dir` ile GEÇİCİ bir kopyaya yazar
    # (mutation.py:54-80, :609-635), yani canlı tabana dokunmaz.
    # DOĞRU CÜMLE: canlı tabanın tek yazarı burasıdır — `persist=True` çağrısının tek sahibi DEĞİL.
    rep = integrity_report(persist=True)
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
    # DÜŞEN DEDEKTÖR ADIYLA DUYURULUR (C21): yalıtım tek başına sessizlik üretmemeli — "ölçemedim"
    # de bir hükümdür ve operatöre gitmelidir. `determinism` DIŞARIDA: onun kendi dalı (aşağıda)
    # `olculemedi`yi zaten alarmlar; buradan ikinci kez duyurmak aynı olguyu iki kanaldan anlatırdı.
    for _ad, _dr in rep.items():
        if _ad == "determinism" or not isinstance(_dr, dict) or not _dr.get("dedektor_dustu"):
            continue
        tok = f"detector_failed:{_ad}"
        now.add(tok)
        if tok not in prev:
            obs.alarm("MECHANISM_STALE",
                      f"BÜTÜNLÜK DEDEKTÖRÜ DÜŞTÜ: {_ad} hüküm veremedi — {_dr.get('error')}",
                      kind="detector_failed", detector=_ad)
    # `.get(...)` KÖŞELİ PARANTEZ YERİNE (C21): düşen bir dedektörün iskeleti alanı taşısa bile
    # tüketici tarafını indeksleme kazasına açık bırakmak, yalıtımı burada geri kırardı.
    for s in rep["production"].get("starved") or []:
        tok = f"starved:{s['name']}"
        now.add(tok)
        if tok not in prev:
            obs.alarm("MECHANISM_STALE", f"mekanizma ÜRETMİYOR: {s['name']} — {s['note']} (0 çıktı)",
                      mechanism=s["name"], kind="starved")
    if rep["conservation"].get("unexplained"):
        tok = "conservation"
        now.add(tok)
        if tok not in prev:
            obs.alarm("MECHANISM_STALE",
                      f"KORUNUM İHLALİ: {rep['conservation']['unexplained']} plan kayıtsız kayboldu",
                      kind="conservation")
    if not rep["determinism"].get("ok"):
        # ÖLÇÜLEMEDİ ≠ İHLAL (C22): bar dizini okunamadığında (ya da dedektör düştüğünde) hüküm
        # YOKTUR. Onu "SESSİZ BAR MUTASYONU" diye adlandırmak uydurma olurdu; jeton da AYRIDIR,
        # böylece ölçüm geri geldiğinde GERÇEK bir mutasyon kendi jetonuyla yeniden alarmlanır.
        _olcum_yok = bool(rep["determinism"].get("olculemedi"))
        tok = "determinism_unmeasured" if _olcum_yok else "determinism"
        now.add(tok)
        if tok not in prev:
            obs.alarm("DATA_QUALITY",
                      (f"BAR DETERMİNİZMİ ÖLÇÜLEMEDİ: {rep['determinism'].get('detail')}"
                       if _olcum_yok else
                       f"SESSİZ BAR MUTASYONU: {rep['determinism'].get('detail')}"),
                      kind="determinism", olculemedi=_olcum_yok)
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
    for st in rep["coherence"].get("stale") or []:             # #4 bayat türev (eski veriyle konuşan kalibrasyon)
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


def monotonicity_report(persist: bool = False, olaylar: list[dict] | None = None) -> dict:
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
        # SERMAYE BEYANI DA İLERİ-ONLY'DİR (D4, 2026-08-04 vakası). Kayıtlar deftere yalnız
        # EKLENİR; sayı ya da kayıt-başına mutlak ofset toplamı düşüyorsa bir beyan SİLİNMİŞTİR.
        # Canlıda bu kayıp ÜÇ GÜN sonra üç kırık `recompute` kimliği olarak göründü ve teşhis
        # maliyeti bir kök-neden dosyası oldu; tabana bağlanınca aynı olay TEK döngüde bir
        # gerileme satırıdır. Ölçü `broker.beyan_olcusu`dan gelir — yazım kapısıyla (loop
        # `_save_broker`) AYNI ölçü, ikinci bir uygulama değil.
        from .broker import beyan_olcusu as _beyan_olcusu
        _b = _beyan_olcusu(pf)
        cur["sermaye_reset_n"] = _b["n"]
        cur["sermaye_ofset_abs"] = _b["abs_ofset"]
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
            # OLAY DEFTERİ PAYLAŞILAN OKUMADAN SAYILIR (v181) — ve sayı TAM DEFTERİNDİR, pencerenin
            # DEĞİL: bu sayaç bir uzunluk gerilemesi arıyor, tabanı da tam defterle yazılmış.
            # Paylaşılan liste `store.read_jsonl("events.jsonl")`in kendisidir (limitsiz), yani
            # `len()` bit-bit aynı sayıyı verir; pencerelenmiş bir liste gelseydi HER TUR sahte
            # gerileme üretirdi. Bu yüzden paylaşım ham satırlarla yapılır, süzülmüşle değil.
            cur[key] = (len(_olay_satirlari(olaylar=olaylar)) if f == "events.jsonl"
                        else len(store.read_jsonl(f)))
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


# =============================================================================================
# #8 KORUMA — "elimde pozisyon var; BROKER'DA canlı bir stop'u var mı?" (v209, 2026-08-07)
# =============================================================================================
# VAKA (canlı A1, ölçüm 2026-08-07): broker'da 5 açık pozisyon, açık emir SIFIR — beşi de
# korumasız. `state/portfolio.json` dört pozisyon için stop BEYAN EDİYORDU (NUE 257,4033 ·
# EMR 152,4839 · BKNG 191,5372 · AMGN 389,4209); broker'da hiçbirinin karşılığı yoktu. Kök neden
# ölçüldü: bracket TIF'i emrin TAMAMINA (giriş + iki koruma bacağına) uygulanır ve E1 yasası
# (o gün `broker.ENTRY_TIF = "day"`, kart EXE-2026-001) TIF'i GTC'den DAY'e çekerken yalnız GİRİŞ
# bacağının bayat-tetik sorununu gerekçelendirmişti. → AYNI GÜN DÜZELTİLDİ: E1-v2 ile TIF GTC'ye
# döndü ve `day` beyaz-listeden çıkarıldı (kart revizyonu EXE-2026-001-R1); bayat tetik artık
# günlük `cancel_open_entries()` kadansıyla kesiliyor. Bu bekçi yine de gerekli — yasa yalnız
# BUNDAN SONRA gönderilen bracket'ları bağlar, ve "koruma var mı" sorusu TIF'ten bağımsızdır.
# Sonuç, olay defterinde saniyesiyle duruyor:
# giriş 2026-08-06 13:32-13:33Z'de doldu, koruma bacakları AYNI GÜN 20:00:16 / 20:01:34 /
# 20:02:06 / 20:02:31Z'de (kapanış 20:00Z) `expired` + OCO kardeşi `canceled` oldu.
#
# NEDEN HİÇBİR DEDEKTÖR GÖRMEDİ — bu bölümün var olma sebebi:
#   * `loop.reconcile_broker_state` ADET sapmasını ölçüyor (o gece 4 MIRROR_DRIFT alarmı bastı) ve
#     KORUMA'yı hiç sormuyordu: dört alarm ötüyordu ama hiçbiri "bu pozisyonlar çıplak" demiyordu.
#   * Aynı fonksiyonun trailing-stop senkronu (1.2c) canlı OLMAYAN stop bacağını `continue` ile
#     SESSİZCE atlıyor — koruma bacağına dokunan tek kod, bacağın YOK olduğunu fark etmiyor.
#   * `alpaca._naked()` yalnız DAR vakayı bilir ("kapatma düştü, bacak iptal edilmişti").
# Yani soru hiç sorulmamıştı. Bu dedektör onu sorar ve HÜKÜM VERİR.
#
# SAHİPLİK KANITI BACAKTA DEĞİL PARENT'TA (alpaca.py:411 dersi): koruma bacaklarının
# `client_order_id`si Alpaca üretimidir, `is_engine_order` onlarda HER ZAMAN False döner. "Canlı
# stop var mı" sorusu bu yüzden önek süzgeciyle SORULAMAZ — süzseydik her pozisyon çıplak görünür,
# dedektör de kurt masalı anlatırdı. Önek yalnız POZİSYONUN kime ait olduğunu ayırmakta kullanılır.
KORUMA_SEV = "sev-1"                 # P1: bu bir RİSK kalemidir, gözlemlenebilirlik değil
KORUMA_PAYDA_BEYANI = "korumasız / toplam MOTOR pozisyonu (motor-dışı pozisyonlar AYRI sayılır)"
_KORUMA_TIPLERI = ("stop", "stop_limit", "trailing_stop")   # koruyucu emir tipleri
_KORUMA_TOL = 1e-6                   # kesirli hisse yuvarlamasını eler, gerçek açığı elemez
KORUMA_EMIR_TAVANI = 200             # `close_engine_position` ile AYNI tavan (tek okuma disiplini)
# MANDAL SÜREÇ-İÇİDİR, DİSKE YAZILMAZ. Gerekçesi obs.py:101-104'ün `_SUPPRESS_LOGGED` kaydıyla
# BİREBİR aynı: diske yazsaydık ikinci bir defter yüzeyi doğardı — üstelik yazanı da okuyanı da bu
# dosya olan, yani `parity:artifact_unread`in tanımına giren bir yüzey. Süreç yeniden başlarsa
# korumasız pozisyon başına BİR fazla alarm satırı düşer; bu, satır SELİNDEN (288/gün) iyidir ve
# KAYBEDİLEN bir alarmdan kat kat iyidir.
_KORUMA_ALARMED: set = set()


def _koruma_duz(ords: list) -> list:
    """Emirleri DÜZLEŞTİR: üst düzey emirler + `nested=True`nin parent altına astığı bacaklar.

    `nested=True` ZORUNLU (aynı gerekçe `alpaca.orders` docstring'inde yazılı): düz listede bracket
    üç ayrı satıra bölünür ve `legs` boş gelir; nested'da ise DOLMUŞ bir parent'ın canlı koruma
    bacakları YALNIZ `legs` altında görünür. Yalnız üst düzeye bakan bir dedektör, korumanın
    varlığını tam da bracket doldurduktan sonra — yani korumanın ÖNEM KAZANDIĞI anda — kaçırırdı."""
    out = []
    for o in (ords or []):
        if not isinstance(o, dict):
            continue
        out.append(o)
        for leg in (o.get("legs") or []):
            if isinstance(leg, dict):
                out.append(leg)
    return out


def _koruma_adet(v) -> float:
    """Adet alanı → mutlak float. Okunamayan adet 0'dır ve bu FAIL-CLOSED yöndür: koruma kapsaması
    BÜYÜMEZ (`alpaca._filled_qty` ile aynı yasa) — ölçülemeyen bir stop, koruyan bir stop değildir."""
    try:
        return abs(float(v or 0.0))
    except (TypeError, ValueError):  # sessiz-yutma: biçimsiz tek alan raporun `not_okunan` sayacında GÖRÜNÜR; 0 dönmek korumayı azaltır, uydurmaz
        return 0.0


def koruma_report() -> dict:
    """#8 — HER açık broker pozisyonu için broker'da CANLI koruyucu stop var mı?

    SÖZLEŞME (dördü de bilinçli):
      1. `ok` DÖNER. Hüküm vermeyen bir dedektör bakanı hiçbir şey öğrenmeden geçirir
         (`conservation_report`ın 2026-07-22'de öğrendiği ders, bu dosyanın :518'i).
      2. PAYDA BEYANLI: `korumasiz / toplam` + `payda_beyani` metni. Paydasız bir sayı ("3 korumasız")
         okuyucuya risk oranını söylemez.
      3. BROKER OKUNAMAZSA `ok=None` + `neden` — **0 DEĞİL**. "0 korumasız" ile "ölçemedim" aynı şey
         değildir ve burada bu ayrım HAYATİDİR: `alpaca.positions()/orders()` arıza hâlinde de []
         döner (A1 sözleşmesi), yani boş listeye bakıp "hiç pozisyon yok, her şey yolunda" demek
         tam olarak arızayı temizlik diye raporlamak olurdu.
      4. MOTOR-DIŞI POZİSYONLAR AYRI SAYILIR: operatörün kendi NVDA'sı motorun sorumluluğu DEĞİLDİR
         (A3 sahiplik sınırı) ama GÖRÜNMEZ de olmamalıdır — `ok` hükmünü etkilemez, kendi sayacıyla
         raporlanır.

    KISMİ KAPSAMA KORUMASIZDIR: canlı stopların toplam adedi pozisyon adedinin ALTINDAysa satır
    `korumali=False` + `kismi=True` ile sayılır. "Yarısı korunuyor" bir güvenlik hâli değil, ölçülmüş
    bir açıktır; yukarı yuvarlamak dedektörü yalancı yapardı.

    SALT OKUMA: bu fonksiyon broker'a YALNIZ GET atar (`positions`, `orders`). Emir gönderme/iptal
    bu dosyanın yetkisinde DEĞİLDİR — bekçi haber verir, düzeltmez (modül başlığı)."""
    out = {"ok": None, "olculemedi": True, "neden": "", "kapsam_disi": False,
           "korumasiz": None, "toplam": None, "payda_beyani": KORUMA_PAYDA_BEYANI,
           "korumasiz_semboller": [], "rows": [],
           "motor_disi": None, "motor_disi_korumasiz": None, "motor_disi_semboller": [],
           "emir_tavani_dolu": False, "sev": KORUMA_SEV}
    from . import config as _cfg
    if getattr(_cfg, "BROKER", "internal") != "alpaca_paper":
        # KAPSAM DIŞI ≠ ÖLÇÜLEMEDİ: ayna hiç yokken "broker'daki stop" sorusunun REFERANSI yoktur
        # (iç motorun stop'unu simülatörün kendisi uygular). Alarm katmanı bu dalda SUSAR — ama
        # `ok` yine None'dır, çünkü "koruma var" hükmü de verilmiş değildir.
        return {**out, "kapsam_disi": True,
                "neden": f"broker={getattr(_cfg, 'BROKER', '?')} — aynada pozisyon yok, "
                         f"broker-tarafı koruma sorusunun referansı yok"}
    from .adapters import alpaca
    if not alpaca.paper_available():
        return {**out, "neden": "Alpaca kimliği/erişimi yok (paper_available()=False) — broker'daki "
                                "koruma ÖLÇÜLEMEDİ ('korumasız 0' DEĞİL)"}
    apos = alpaca.positions()
    if not alpaca.transport()["ok"]:
        # A1: [] burada "pozisyon yok" DEĞİL, ARIZA. Bu dalın olmaması, tam da broker düştüğünde
        # dedektörün "0 pozisyon, 0 korumasız, temiz" demesi anlamına gelirdi.
        return {**out, "neden": "pozisyon listesi okunamadı: "
                                + (alpaca.transport().get("error") or "alpaca transport down")[:160]}
    ords = alpaca.orders(status="all", limit=KORUMA_EMIR_TAVANI, nested=True)
    if not alpaca.transport()["ok"]:
        return {**out, "neden": "emir listesi okunamadı: "
                                + (alpaca.transport().get("error") or "alpaca transport down")[:160]}
    # TAVAN DOLDUYSA SAHİPLİK KANITI EKSİK OLABİLİR — sessiz kalmaz, satırla beyan edilir: dolmuş
    # bir motor emri tavanın dışında kaldıysa pozisyon 'motor-dışı' görünür ve YANLIŞ payda üretir.
    out["emir_tavani_dolu"] = len(ords or []) >= KORUMA_EMIR_TAVANI
    duz = _koruma_duz(ords)

    # SAHİPLİK: kanıt "bir P- emri var" değil "bir P- emri DOLDU"dur (close_engine_position ile
    # AYNI yasa — iki yerde iki farklı sahiplik tanımı, bu deponun kovaladığı kusurun kendisi olurdu).
    motor_semboller = {str(o.get("symbol")) for o in duz
                       if alpaca.is_engine_order(o)
                       and (alpaca._filled_qty(o) > 0
                            or str(o.get("status", "")).lower() in ("filled", "partially_filled"))}

    canli = set(alpaca._LIVE_ORDER_STATES)   # TEK SÖZLÜK: canlı emir durumlarını burada ikinci kez
                                             # tanımlamak, iki tanımın kayması demek olurdu
    korumasiz, motor_disi_korumasiz, rows = 0, 0, []
    for p in (apos or []):
        sym = str(p.get("symbol") or "")
        if not sym:
            continue
        adet = _koruma_adet(p.get("qty"))
        yon = str(p.get("side") or "long").lower()
        # UZUN pozisyonu SATIŞ stop'u korur, KISA pozisyonu ALIŞ stop'u. Bugün motor yalnız uzun
        # açıyor; yönü sabit yazsaydık ileride bir kısa pozisyon KORUNUYOR görünürdü (yanlış yönde
        # bir stop, korumasızlıktan beterdir: koruma sanılır).
        koruyan_yon = "buy" if yon == "short" else "sell"
        kapsanan, emir_ids = 0.0, []
        for o in duz:
            if str(o.get("symbol")) != sym:
                continue
            if str(o.get("side", "")).lower() != koruyan_yon:
                continue
            if str(o.get("type", "")).lower() not in _KORUMA_TIPLERI:
                continue
            if str(o.get("status", "")).lower() not in canli:
                continue
            kapsanan += _koruma_adet(o.get("qty")) - _koruma_adet(o.get("filled_qty"))
            # YALNIZ BROKER `id`si: `client_order_id` bunun EŞ ADI DEĞİL, BAŞKA bir kimliktir
            # (biri broker'ın, diğeri bizim) ve koruma bacaklarında zaten Alpaca üretimi bir
            # UUID'dir. "Biri yoksa öbürü" yazmak iki kimliği tek alana yığmak olurdu —
            # `test_parity_v56::no_undeclared_field_alias` tam bu sınıfı kovalıyor.
            emir_ids.append(str(o.get("id") or "?")[:36])
        korumali = bool(adet > 0 and kapsanan + _KORUMA_TOL >= adet)
        motor = sym in motor_semboller
        row = {"ticker": sym, "adet": adet, "yon": yon, "motor": motor,
               "korumali": korumali, "kapsanan": round(kapsanan, 6),
               "kismi": bool(not korumali and kapsanan > 0), "stop_emirleri": emir_ids,
               "neden": ("" if korumali else
                         ("broker'da CANLI koruyucu stop YOK" if kapsanan <= 0 else
                          f"stop yalnız {kapsanan:g}/{adet:g} adedi kapsıyor"))}
        rows.append(row)
        if not korumali:
            if motor:
                korumasiz += 1
            else:
                motor_disi_korumasiz += 1
    motor_rows = [r for r in rows if r["motor"]]
    disi = [r["ticker"] for r in rows if not r["motor"]]
    return {**out, "ok": korumasiz == 0, "olculemedi": False, "neden": "",
            "korumasiz": korumasiz, "toplam": len(motor_rows),
            "korumasiz_semboller": sorted(r["ticker"] for r in motor_rows if not r["korumali"]),
            "rows": rows, "motor_disi": len(disi),
            "motor_disi_korumasiz": motor_disi_korumasiz, "motor_disi_semboller": sorted(disi)}


def check_koruma_and_alarm() -> dict:
    """#8'in alarm geçişi — korumasız pozisyon başına BİR kez, sev-1. Raporu DÖNDÜRÜR (test + çağıran).

    JETON SEÇİMİ BEYANLI VE EKSİK: `obs.NOTIFY_TOKENS` yalnız `obs.py`deki `ALARM_*` sabitlerinden
    TÜRETİLİR (obs.py:98) — listede olmayan yeni bir jeton yazılır ama operatörün telefonuna HİÇ
    ULAŞMAZ. Bu tur `obs.py` yazım kapsamı dışında olduğu için mevcut ve teslim edilen en yakın
    sınıf kullanılır: `MIRROR_DRIFT` ("ayna kitabın söylediği şey değil") — `loop._mirror_exit_sync`
    çıplak pencereyi ZATEN bu jetonla anlatıyor, yani sınıf birliği de korunuyor.
    BEDELİ ÖLÇÜLÜ: jeton başına 6 saatlik susturma penceresi (obs._NOTIFY_MIN_GAP_S) ADET SAPMASI
    alarmlarıyla PAYLAŞILIR — gürültülü bir mutabakat gecesi bu alarmın TESLİMATINI bastırabilir
    (defter satırı ve pano yine yazılır). Ayrı bir `NAKED_POSITION` jetonu OPERATÖR KARARIDIR ve
    `obs.py`ye bir satır ekler; bu tur ölçüldü ve raporlandı, uygulanmadı.

    `kind="korumasiz_pozisyon"` + `sev` alanları satırda taşınır: gelen kutusu ve pano bu iki alanla
    ayırt eder — jeton paylaşılsa da OLGU karışmaz."""
    from . import obs
    rep = koruma_report()
    if rep.get("kapsam_disi"):
        # Ayna kapalı: alarm YOK (referansı olmayan bir soruyu her poll'da alarmlamak, EEMUA
        # bütçesini bir yapılandırma hâliyle doldurmak olurdu). Mandal da temizlenir ki ayna
        # yeniden açıldığında ilk korumasızlık YENİDEN alarmlansın.
        _KORUMA_ALARMED.clear()
        return rep
    simdi = set()
    if rep.get("ok") is None:
        # ÖLÇÜLEMEDİ DE BİR HÜKÜMDÜR (YASA 4) — ve 'temiz' DEĞİLDİR. Kendi jetonu var: ölçüm geri
        # geldiğinde GERÇEK bir korumasızlık kendi jetonuyla yeniden alarmlanabilsin.
        tok = "koruma_olculemedi"
        simdi.add(tok)
        if tok not in _KORUMA_ALARMED:
            obs.alarm(obs.ALARM_MIRROR_DRIFT,
                      f"KORUMA ÖLÇÜLEMEDİ: broker okunamadı — {rep.get('neden')} "
                      f"(bu 'korumasız 0' DEĞİL: açık pozisyonların koruma durumu BİLİNMİYOR)",
                      kind="koruma_olculemedi", sev=KORUMA_SEV, olculemedi=True)
    else:
        for r in rep.get("rows") or []:
            if r.get("korumali"):
                continue
            tok = ("korumasiz:" if r.get("motor") else "korumasiz_disi:") + r["ticker"]
            simdi.add(tok)
            if tok in _KORUMA_ALARMED:
                continue
            if r.get("motor"):
                obs.alarm(obs.ALARM_MIRROR_DRIFT,
                          f"KORUMASIZ POZİSYON: {r['ticker']} {r['adet']:g} adet açık, broker'da "
                          f"canlı koruyucu stop YOK — {r['neden']} "
                          f"({rep['korumasiz']}/{rep['toplam']} motor pozisyonu korumasız)",
                          kind="korumasiz_pozisyon", sev=KORUMA_SEV, ticker=r["ticker"],
                          adet=r["adet"], kapsanan=r["kapsanan"], kismi=r["kismi"],
                          korumasiz=rep["korumasiz"], toplam=rep["toplam"],
                          payda_beyani=rep["payda_beyani"])
            else:
                # MOTOR-DIŞI: `ok` hükmüne GİRMEZ (A3 — motor sahibi olmadığı pozisyonu koruyamaz,
                # koruma emri göndermek operatörün işi) ama GÖRÜNÜR olur; seviye WARN, çünkü bu
                # motorun kendi riski değildir ve operatörün alarm bütçesini sev-1 ile yemez.
                obs.warn("korumasiz_motor_disi_pozisyon", ticker=r["ticker"], adet=r["adet"],
                         kapsanan=r["kapsanan"], kind="korumasiz_pozisyon",
                         detail="motor-DIŞI pozisyonun broker'da canlı stop'u yok — motorun "
                                "sorumluluğu DEĞİL (A3 sahiplik sınırı), yalnız görünürlük")
    # MANDAL: düzelen jeton düşer, yeniden bozulursa YENİDEN alarmlanır (integrity_alarmed deseni).
    _KORUMA_ALARMED.clear()
    _KORUMA_ALARMED.update(simdi)
    return rep
