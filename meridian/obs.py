"""obs.py — structured JSON logging + the ALARM_ tokens the notification chain keys on.

A silent agent is an unmonitored agent (§9). Every notable event emits ONE JSON line to stdout
(captured by systemd/launchd) AND a mirrored row in `state/events.jsonl`.

JETONLARIN GERÇEK TÜKETİCİSİ (K1, 2026-07-30 düzeltmesi): bu docstring eskiden jetonların "Cloud
Monitoring log-based metrics fire" için basıldığını söylüyordu. O beyan bayattı ve yanlış güven
üretiyordu: deploy/monitoring.sh gcloud/gce_instance'a bağlıdır, fiilî işletim ise yerel
keepalive + Oracle A1 systemd — yani GCP tüketicisi bu kurulumda var OLAMAZ. Üstelik o betiğin
filtresi 11 jetondan yalnız 3'ünü tanıyordu.
BUGÜNÜN GERÇEK ZİNCİRİ, sırayla:
  1. `_maybe_notify` → `notify.send` (Telegram/webhook; jeton başına 6 sa susturma penceresi),
  2. `notify.inbox` → panonun YEREL alarm gelen kutusu (ACK'lenmemiş olanları imzaya göre gruplar),
  3. `watchdog.parity_report` → teslim edilemeyen alarm sayacı (`notify_undelivered.json`).
Kanal yapılandırılmamışsa 1 sessiz no-op olur; 2 ve 3 yine çalışır — "alarm yazıldı" ile "alarm
ULAŞTI" ayrı şeylerdir ve ikincisini yalnız ACK kanıtlar.
deploy/monitoring.sh yaşamaya devam ediyor (GCP'ye dönülürse) ama artık filtresini bu dosyadaki
NOTIFY_TOKENS'tan TÜRETİYOR — elle liste, yeni jeton eklendikçe sessizce eskiyordu."""
from __future__ import annotations
import datetime as dt
import json
import sys

# Tokens matched by deploy/monitoring.sh log filters. Keep these strings stable.
ALARM_HEARTBEAT_STALE = "HEARTBEAT_STALE"
ALARM_ROLLBACK = "ROLLBACK"
ALARM_CIRCUIT_BREAKER = "CIRCUIT_BREAKER"
ALARM_DATA_QUALITY = "DATA_QUALITY"
ALARM_HALT = "HALT_ACTIVE"
ALARM_MIRROR_DRIFT = "MIRROR_DRIFT"        # internal sim fill vs actual Alpaca fill diverged beyond tolerance
ALARM_BROKER_REJECT = "BROKER_REJECT"      # Alpaca rejected an order the internal book would have executed
ALARM_TRAIL_DESYNC = "TRAIL_DESYNC"        # trailing-stop PATCH reddedildi — iç HWM ile broker stopu ayrıştı
ALARM_MECHANISM_STALE = "MECHANISM_STALE"  # bir mekanizma üretmiyor/bayatladı (bütünlük dedektörleri)
ALARM_ARMING_READY = "ARMING_READY"        # silahlanma eşiği karşılandı — operatör kararı bekleniyor
# KALİBRASYON YETKİ DEĞİŞİMİ 'BENİ UYANDIR' SINIFIDIR (operatör kararı 2026-07-27): bir danışmanın
# yetkisi EŞİK DOLUNCA KENDİLİĞİNDEN açılır ve pano bunu yalnız DUYURUR — yani operatör onay vermez,
# haberdar edilir. Haberin kendisi obs.log seviyesinde kalsaydı yetki devri olay defterinin içinde
# sıradan bir satır olurdu ve kimse bakmadan geçerdi. Kayıp da kazanım kadar yüksek sesli olmalı:
# yetkinin GERİ ALINMASI, sessizce alınırsa "danışman hâlâ konuşuyor" sanılır.
ALARM_AUTHORITY = "AUTHORITY_CHANGE"       # bir mekanizmanın yetkisi açıldı/geri alındı
# SÖZLEŞMENİN BAŞARISIZLIK HÜKMÜ (K1, 2026-07-30). goal.yaml `failure_below` hükmünü ("30g getiri bu
# eşiğin altına düşerse deney BAŞARISIZ") tanımlandığı 2026-07-14'ten beri hiçbir kod ölçmüyordu:
# score.py hedef tarafını (target_return_30d/max_drawdown/min_sharpe) composite'e katıyor, failure
# tarafını asla okumuyordu. Deney başarısız olsa bunu söyleyecek tek satır kod yoktu. Bu kendi
# sınıfıdır: DATA_QUALITY "veri bozuk" der, MECHANISM_STALE "mekanizma üretmiyor" der — ikisi de
# "mekanizma çalıştı ve sonuç sözleşmenin başarısızlık eşiğinin altında" demez.
ALARM_GOAL_FAILURE = "GOAL_FAILURE"        # realized_30d < goal.failure_below — sözleşme hükmü

# also mirror events to state/events.jsonl so the dashboard/tests can read them without a log scraper
_EVENTS = "events.jsonl"


def _emit(level: str, event: str, fields: dict) -> dict:
    rec = {"ts": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
           "level": level, "event": event, **fields}
    line = json.dumps(_san(rec), ensure_ascii=False)
    print(line, file=sys.stdout, flush=True)
    try:
        from . import store
        store.append_jsonl(_EVENTS, rec)
    except Exception:  # sessiz-yutma: kayıt kanalının kendisi düştü — ikinci bir kanal yok; kayıt denemesi çağıranı düşüremez
        pass
    return rec


def _san(o):
    try:
        json.dumps(o)
        return o
    except TypeError:  # sessiz-yutma: yardımcı G/Ç yolu; çağıran yokluğu zaten yedek değerle karşılıyor ve asıl okuma hatası store katmanında bir kez uyarılıyor
        return {k: (v if _ok(v) else str(v)) for k, v in o.items()}


def _ok(v):
    try:
        json.dumps(v)
        return True
    except TypeError:  # sessiz-yutma: yardımcı G/Ç yolu; çağıran yokluğu zaten yedek değerle karşılıyor ve asıl okuma hatası store katmanında bir kez uyarılıyor
        return False


def log(event: str, **fields) -> dict:
    """Ordinary structured event."""
    return _emit("info", event, fields)


def warn(event: str, **fields) -> dict:
    return _emit("warn", event, fields)


# BİLDİRİLECEK JETONLAR — EL LİSTESİ DEĞİL, TÜRETME (2026-07-26).
# DENETİM turu 20 (2026-07-21) "beni uyandır" sınıfının ÜÇÜNÜ listede bulamamıştı: HALT (motor
# durdu), ROLLBACK (canlı strateji geri alındı), HEARTBEAT_STALE (döngü ölmüş). Sebep tek tek
# unutkanlık değil YAPIYDI: liste elle bakımlıydı ve yeni bir ALARM_ sabiti eklemek onu sessizce
# ESKİTİYORDU — en kritik alarmlar tam da bu yolla dışarıda kalmıştı.
# KURAL: her ALARM_ sabiti bildirilir. Bir jeton BİLEREK sessiz kalacaksa bu bir KARAR olmalı ve
# burada açık bir çıkarma ile yazılmalı; şu an böyle bir jeton yok (bkz. test_o1b).
NOTIFY_TOKENS = {v for k, v in list(globals().items())
                 if k.startswith("ALARM_") and isinstance(v, str)}
_NOTIFY_MIN_GAP_S = 6 * 3600     # token başına en fazla 6 saatte bir mesaj — kanal spam'e dönmesin
# Hangi SUSTURMA PENCERESİ için zaten kayıt düşüldü: {token: pencere_baslangici}. Süreç-içi bir
# kayıttır ve öyle kalmalı — diske yazsaydı susturmanın kaydı ikinci bir defter yüzeyi doğururdu.
# Süreç yeniden başlarsa pencere başına bir fazla satır düşer; bu, satır SELİNDEN iyidir.
_SUPPRESS_LOGGED: dict[str, float] = {}


def _maybe_notify(token: str, message: str) -> None:
    """v11 #1 — kritik alarm sınıfları paneli açmadan operatöre ulaşır (Telegram/webhook; yapılandırılmamışsa
    sessiz no-op). Token başına 6 saatlik sessizlik penceresi; bildirim hatası alarmı ASLA düşürmez."""
    if token not in NOTIFY_TOKENS:
        return
    try:
        import time
        from . import store, notify
        if not notify.configured():
            # KANAL YOKSA ALARM HİÇBİR YERE GİTMEZ — ve bu sessizce olurdu (2026-07-22 bulgusu:
            # canlı defterde 23 MECHANISM_STALE alarmı vardı, hiçbiri operatöre ulaşmamıştı).
            # "Alarm yazıldı" ile "alarm ULAŞTI" ayrı şeylerdir; teslim edilemeyen alarm sayılır ve
            # makullük dedektöründe görünür. Log'a satır BASILMAZ — alarm zaten yazıldı, ikinci
            # satır yalnız gürültü olurdu.
            try:
                def _bump(d):
                    # store.update_json SÖZLEŞMESİ: belgeyi YERİNDE değiştir ve True dön. Yeni bir
                    # sözlük döndürmek sessizce hiçbir şey yazmaz (ilk denememde tam bu oldu — dosya
                    # oluştu ama boş kaldı). Sözleşmeyi yanlış okumanın cezası yine SESSİZLİK.
                    d[token] = int(d.get(token, 0)) + 1
                    d["_toplam"] = int(d.get("_toplam", 0)) + 1
                    return True

                store.update_json("notify_undelivered.json", _bump, {})
            except Exception:  # sessiz-yutma: SON ÇARE — sayaç yazılamıyorsa bile alarmın kendisi zaten deftere yazıldı; burada çağıranı düşürmek alarmı kaybettirirdi
                pass
            return
        sent = store.read_json("notify_sent.json", {})
        _win = float(sent.get(token, 0))
        if time.time() - _win < _NOTIFY_MIN_GAP_S:
            # ÜÇÜNCÜ SESSİZ DELİK (2026-07-26): kanal BAĞLIYKEN bile 6 saatlik pencere mesajı
            # düşürüyordu ve bunun hiçbir izi yoktu — "susturuldu" ile "hiç alarm yoktu" yine
            # ayırt edilemiyordu. Alarmın kendisi deftere zaten yazılıyor; burada susturmanın
            # KENDİSİ kayda geçer, böylece "telefonuma gelmedi" sorusunun cevabı defterde durur.
            #
            # PENCERE BAŞINA TEK SATIR (2026-07-26, ikinci düzeltme): bu kayıt HER bastırmada
            # düşüyordu. Susturma penceresinin amacı 6 saatte bir mesaj; ama aynı pencerede 200 kez
            # alarm üreten bir dedektör 200 `notify_suppressed` satırı yazıyor ve olay defterini —
            # yani gelen kutusunun ve tüm makullük dedektörlerinin okuduğu kaynağı — boğuyordu.
            # Gürültüye karşı kurulan mekanizmanın kendisi gürültü üretemez. Anlatılacak olgu
            # "susturma AÇIK" (pencere başına bir kez), "her bastırma" değil.
            if _SUPPRESS_LOGGED.get(token) != _win:
                _SUPPRESS_LOGGED[token] = _win
                log("notify_suppressed", token=token, since_s=int(time.time() - _win),
                    window_s=_NOTIFY_MIN_GAP_S,
                    detail="bu pencerede yalnız BİR kez kaydedilir — sonraki bastırmalar sessizdir")
            return
        if notify.send(f"⚠️ {token}: {message}"):
            sent[token] = time.time()
            store.write_json("notify_sent.json", sent)
    except Exception:  # sessiz-yutma: obs alarmı/kaydı bu noktada ZATEN yazıldı; ikincil bildirim kanalının (Telegram/webhook) düşmesi alarmı asla düşüremez
        pass


def alarm(token: str, message: str, **fields) -> dict:
    """Emit an alarm line whose text CONTAINS the token monitoring.sh searches for."""
    fields["alarm"] = token
    fields["message"] = message
    _maybe_notify(token, message)
    # the raw token appears in the printed line so a plain substring filter matches
    return _emit("alarm", f"{token} {message}", fields)


def recent(limit: int = 50) -> list[dict]:
    from . import store
    return store.read_jsonl(_EVENTS, limit=limit)
