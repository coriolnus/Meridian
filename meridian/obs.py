"""obs.py — yapılandırılmış JSON olay kaydı + bildirim zincirinin anahtarlandığı ALARM_ jetonları.

NE YAPAR. Sessiz ajan izlenmeyen ajandır: kayda değer her olay TEK JSON satırı olarak stdout'a
basılır (systemd/launchd yakalar) VE `state/events.jsonl`a aynalanır. Üç seviye: `log`/`warn`/
`alarm`; `alarm(token, message)` jetonu satırın METNİNE koyar (düz alt-dize filtresi yakalasın)
ve `_maybe_notify` ile operatöre iter.

JETONLAR (gerçek adlar): ALARM_HEARTBEAT_STALE, ALARM_ROLLBACK, ALARM_CIRCUIT_BREAKER,
ALARM_DATA_QUALITY, ALARM_HALT ("HALT_ACTIVE"), ALARM_MIRROR_DRIFT, ALARM_BROKER_REJECT,
ALARM_TRAIL_DESYNC, ALARM_MECHANISM_STALE, ALARM_ARMING_READY, ALARM_AUTHORITY
("AUTHORITY_CHANGE"), ALARM_GOAL_FAILURE, ALARM_NAKED_POSITION, ALARM_ONAYLI_PLAN_GONDERILMEDI.
NOTIFY_TOKENS el listesi DEĞİL TÜRETMEdir: her ALARM_ sabiti kendiliğinden bildirim
kapsamındadır — elle bakımlı liste tam da en kritik alarmları sessizce dışarıda bırakarak
eskimişti; bilerek susacak jeton açık bir çıkarma ister (bugün yok).

TESLİM ZİNCİRİ (eski "GCP Cloud Monitoring tüketir" beyanı YANLIŞLANDI — o tüketici bu kurulumda
var olamaz): (1) `_maybe_notify` → `notify.send` (jeton başına 6 sa susturma; bastırma pencere
başına BİR satırla kayda geçer, kanal yokken/teslim düşünce `notify_undelivered.json` sayacı
artar), (2) `notify.inbox` yerel gelen kutusu, (3) `watchdog.parity_report` teslim sayaçları.
"Alarm yazıldı" ile "alarm ULAŞTI" ayrı şeylerdir; ikincisini yalnız ACK kanıtlar.

İMZA-MANDALI: çözülmemiş ama DEĞİŞMEMİŞ bilinen durumun aynı imzalı tekrarları (MANDAL_IMZALAR:
MIRROR_DRIFT adet-sapması, DATA_QUALITY bar-kaynak uyuşmazlığı) satır üretmez,
`state/alarm_mandal.json`da SAYILIR; imzanın herhangi bir alanı değişir ya da serbest penceresi
aşılıp durum geri gelirse yeniden alarmlanır. Sermaye-sınıfı jetonlar mandallanmaz; mandal
arızası alarmı asla yutmaz (fail-open). Okur/yazar: `state/events.jsonl` (+`recent` ile okur),
`notify_sent.json`, `notify_undelivered.json`, `alarm_mandal.json`."""
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
# KALİBRASYON YETKİ DEĞİŞİMİ 'BENİ UYANDIR' SINIFIDIR (operatör kararı): bir danışmanın
# yetkisi EŞİK DOLUNCA KENDİLİĞİNDEN açılır ve pano bunu yalnız DUYURUR — yani operatör onay vermez,
# haberdar edilir. Haberin kendisi obs.log seviyesinde kalsaydı yetki devri olay defterinin içinde
# sıradan bir satır olurdu ve kimse bakmadan geçerdi. Kayıp da kazanım kadar yüksek sesli olmalı:
# yetkinin GERİ ALINMASI, sessizce alınırsa "danışman hâlâ konuşuyor" sanılır.
ALARM_AUTHORITY = "AUTHORITY_CHANGE"       # bir mekanizmanın yetkisi açıldı/geri alındı
# SÖZLEŞMENİN BAŞARISIZLIK HÜKMÜ. goal.yaml `failure_below` hükmünü ("30g getiri bu
# eşiğin altına düşerse deney BAŞARISIZ") tanımlandığından beri hiçbir kod ölçmüyordu:
# score.py hedef tarafını (target_return_30d/max_drawdown/min_sharpe) composite'e katıyor, failure
# tarafını asla okumuyordu. Deney başarısız olsa bunu söyleyecek tek satır kod yoktu. Bu kendi
# sınıfıdır: DATA_QUALITY "veri bozuk" der, MECHANISM_STALE "mekanizma üretmiyor" der — ikisi de
# "mekanizma çalıştı ve sonuç sözleşmenin başarısızlık eşiğinin altında" demez.
ALARM_GOAL_FAILURE = "GOAL_FAILURE"        # realized_30d < goal.failure_below — sözleşme hükmü
# KORUMASIZ POZİSYON KENDİ JETONUNU HAK EDER (N1 — operatör kararı; v209'da ölçülüp
# ertelenmişti). `watchdog.check_koruma_and_alarm` v209'da MIRROR_DRIFT jetonunu ÖDÜNÇ alıyordu
# çünkü o tur `obs.py` yazım kapsamı dışındaydı ve listede olmayan bir jeton yazılıp operatöre HİÇ
# ulaşmazdı (NOTIFY_TOKENS türetmesi, aşağıda). Ödüncün BEDELİ o gün ölçülmüş ve docstring'e
# yazılmıştı: `_maybe_notify` susturma penceresi JETON BAŞINADIR (6 sa), yani gürültülü bir
# mutabakat gecesinde ADET SAPMASI alarmları pencereyi doldurup KORUMASIZ POZİSYON alarmının
# TESLİMATINI bastırabiliyordu. İki olgu ayrı: "ayna kitabın söylediği adette değil" bir MUHASEBE
# sapmasıdır, "pozisyonun broker'da canlı stop'u yok" bir SERMAYE riskidir (sev-1) ve birincisi
# ikincisini susturamaz. Teslim zinciri DEĞİŞMEZ — jeton buraya eklendiği an NOTIFY_TOKENS onu
# kendiliğinden kapsar (el listesi yok); kanalın kendisi operatör yapılandırmasıdır.
ALARM_NAKED_POSITION = "NAKED_POSITION"    # açık pozisyonun broker'da canlı koruyucu stop'u YOK
# ONAYLI PLAN GÖNDERİLMEDİ — KENDİ JETONU (P-2026-08-07-VLO vakası). Aday
# alternatif MIRROR_DRIFT'in yeni bir `drift_sinifi` değeriydi ve ÜÇ ölçülmüş gerekçeyle REDDEDİLDİ:
# (1) N1 emsali birebir — `_maybe_notify` susturma penceresi JETON BAŞINADIR (6 sa): gürültülü bir
#     mutabakat gecesinde adet-sapması MIRROR_DRIFT'leri pencereyi doldurur ve "operatörün onayladığı
#     emir broker'a HİÇ gitmedi" alarmının TESLİMATINI bastırırdı — bu sınıf tam da operatörün
#     "büyük fiyasko" dediği sınıftır, muhasebe gürültüsünün arkasında bekleyemez.
# (2) C9 yasası ("iki teşhis aynı isimle sayılırsa ikisi de okunamaz"): split_brain BELİRTİ adıdır
#     (sebep bilinmiyor), bu jeton SEBEBİ BİLİNEN ve EYLEMİ BELLİ bir alt sınıftır (onay verildi,
#     iç motor doldu, gönderim hiç olmadı → gönderim yolunu onar / elle emirle).
# (3) Teslim zinciri değişmez: NOTIFY_TOKENS her ALARM_ sabitinden TÜRETİLİR (aşağıda) — jeton
#     eklendiği an bildirim kapsamındadır, el listesi eskimez. Üretici: watchdog (İŞ-3b bekçisi);
#     reconcile'ın MIRROR_DRIFT/split_brain alarmı AYNEN kalır (o genel belirtiyi anlatmaya devam eder).
ALARM_ONAYLI_PLAN_GONDERILMEDI = "ONAYLI_PLAN_GONDERILMEDI"

# also mirror events to state/events.jsonl so the dashboard/tests can read them without a log scraper
_EVENTS = "events.jsonl"


def _emit(level: str, event: str, fields: dict) -> dict:
    """Olayı TEK JSON satırı olarak kurar, stdout'a basar (systemd/launchd yakalar) VE
    `state/events.jsonl`a aynalar; kaydın kendisini döner. Aynalama düşerse olay yine
    stdout'a basılmıştır — kayıt denemesi çağıranı düşüremez."""
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
    """Kaydı JSON'a çevrilebilir hâle getirir: olduğu gibi dump edilebiliyorsa dokunmaz, aksi
    hâlde yalnız serileştirilemeyen alanları `str()`e çevirir — tek kötü alan olayı düşürmesin."""
    try:
        json.dumps(o)
        return o
    except TypeError:  # sessiz-yutma: yardımcı G/Ç yolu; çağıran yokluğu zaten yedek değerle karşılıyor ve asıl okuma hatası store katmanında bir kez uyarılıyor
        return {k: (v if _ok(v) else str(v)) for k, v in o.items()}


def _ok(v):
    """Tek bir değer JSON'a serileştirilebiliyor mu? (`_san` alan süzgecinin ölçüsü.)"""
    try:
        json.dumps(v)
        return True
    except TypeError:  # sessiz-yutma: yardımcı G/Ç yolu; çağıran yokluğu zaten yedek değerle karşılıyor ve asıl okuma hatası store katmanında bir kez uyarılıyor
        return False


def log(event: str, **fields) -> dict:
    """Ordinary structured event."""
    return _emit("info", event, fields)


def warn(event: str, **fields) -> dict:
    """Uyarı seviyesinde yapılandırılmış olay — alarm DEĞİLDİR: bildirim zincirini tetiklemez."""
    return _emit("warn", event, fields)


# BİLDİRİLECEK JETONLAR — EL LİSTESİ DEĞİL, TÜRETME.
# DENETİM "beni uyandır" sınıfının ÜÇÜNÜ listede bulamamıştı: HALT (motor
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
    """Kritik alarm sınıfları paneli açmadan operatöre ulaşır (Telegram/webhook; yapılandırılmamışsa
    sessiz no-op). Token başına 6 saatlik sessizlik penceresi; bildirim hatası alarmı ASLA düşürmez."""
    if token not in NOTIFY_TOKENS:
        return
    try:
        import time
        from . import store, notify
        if not notify.configured():
            # KANAL YOKSA ALARM HİÇBİR YERE GİTMEZ — ve bu sessizce olurdu (ölçülmüş bulgu:
            # canlı defterde 23 MECHANISM_STALE alarmı vardı, hiçbiri operatöre ulaşmamıştı).
            # "Alarm yazıldı" ile "alarm ULAŞTI" ayrı şeylerdir; teslim edilemeyen alarm sayılır ve
            # makullük dedektöründe görünür. Log'a satır BASILMAZ — alarm zaten yazıldı, ikinci
            # satır yalnız gürültü olurdu.
            try:
                def _bump(d):
                    """Teslim edilemeyen alarm sayacını yerinde artırır (jeton + `_toplam`) ve
                    `store.update_json` sözleşmesi gereği True döner."""
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
            # ÜÇÜNCÜ SESSİZ DELİK: kanal BAĞLIYKEN bile 6 saatlik pencere mesajı
            # düşürüyordu ve bunun hiçbir izi yoktu — "susturuldu" ile "hiç alarm yoktu" yine
            # ayırt edilemiyordu. Alarmın kendisi deftere zaten yazılıyor; burada susturmanın
            # KENDİSİ kayda geçer, böylece "telefonuma gelmedi" sorusunun cevabı defterde durur.
            #
            # PENCERE BAŞINA TEK SATIR (ikinci düzeltme): bu kayıt HER bastırmada
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
        else:
            # DÖRDÜNCÜ SESSİZ DELİK: kanal BAĞLIYKEN teslimatın BAŞARISIZ olması
            # hiçbir sayaca girmiyordu. `notify_undelivered.json`ı besleyen tek yol yukarıdaki
            # "kanal YOK" dalıydı; yani "kanal yok" ölçülüyor, "kanal var ama cevap vermiyor"
            # ölçülmüyordu. Sonuç: `parity_report`ın `alarm_delivery` satırı yığın ACK ile
            # soğurulduğunda yeşil, `notify_channel` satırı `configured()` True olduğu için
            # KOŞULSUZ yeşil — iki satır da yeşilken operatöre tek bir alarm ulaşmamış olabilirdi.
            # Bu, modülün kuruluş ayrımının ("alarm yazıldı ≠ alarm ULAŞTI") tam da adını koyduğu
            # vakada kırılmasıydı. `notify.py` bu düşüşte `notify_delivery_failed` uyarısı basıyor
            # ama ÜRETİM tarafında okuyucusu yok (YASA 6) — sayaç okuyucusu olan yüzeydir.
            #
            # `_teslim_hatasi` AYRI SAYAÇ: `_toplam` ikisini birden taşır (kalıntı hesabı bozulmaz),
            # ama "kanal yokken biriken yığın" ile "kanal bağlıyken düşen teslimat" AYRI olgulardır
            # ve `alarm_delivery` metni ikisini karıştırmamalıdır. Alt çizgiyle başlar: jeton
            # listesini basan yüzeyler (`watchdog.parity_report`) `_` önekli anahtarları eler.
            #
            # `notify_sent.json` YAZILMAZ (mevcut davranış korunur): susturma penceresi yalnız
            # GERÇEKTEN gönderilmiş bir mesajla kurulur, yoksa başarısız bir deneme kanalı
            # 6 saat susturur ve alarm kaybolur.
            def _bump_fail(d):
                """Kanal BAĞLIYKEN düşen teslimatı sayar: jeton + `_toplam` + ayrı
                `_teslim_hatasi` sayacı; `store.update_json` sözleşmesi gereği True döner."""
                # store.update_json SÖZLEŞMESİ: belgeyi YERİNDE değiştir ve True dön (yeni sözlük
                # döndürmek sessizce hiçbir şey yazmaz — yukarıdaki kardeş dalın dersi).
                d[token] = int(d.get(token, 0)) + 1
                d["_toplam"] = int(d.get("_toplam", 0)) + 1
                d["_teslim_hatasi"] = int(d.get("_teslim_hatasi", 0)) + 1
                return True

            store.update_json("notify_undelivered.json", _bump_fail, {})
    except Exception:  # sessiz-yutma: obs alarmı/kaydı bu noktada ZATEN yazıldı; ikincil bildirim kanalının (Telegram/webhook) düşmesi alarmı asla düşüremez
        pass


# ---- İMZA-MANDALI: tekrar-eden BİLİNEN durum → DURUM, yalnız DEĞİŞİM → alarm ----
# ÖLÇÜLEN GÜRÜLTÜ: aynı (ticker, local_qty, alpaca_qty, drift_sinifi) içerikli MIRROR_DRIFT
# adet-sapması HER GÜN ×4 (NUE/EMR/BKNG/AMGN `olculemedi` — kök bilinen: makbuzsuz
# boyut) ve aynı (ticker, date, source, dev_pct) içerikli DATA_QUALITY bar-kaynak
# uyuşmazlığı (MNST %50) her gün yeniden alarmlanıyordu. Çözülmemiş ama DEĞİŞMEMİŞ bir durumu
# her gün yeniden anlatmak alarm-yorgunluğudur (EEMUA); susup yok saymak ise yasak.
# KURAL (dikiş defteri `bar_source_seams.json` + bastırma-sayacı emsali): imza İLK görüşte
# alarmlanır; AYNI imza tekrarları SAYILIR ama satır üretmez; imzanın HERHANGİ bir alanı değişirse
# (adet/sınıf/sapma) bu YENİ bir imzadır ve ANINDA alarmlanır; imza `MANDAL_SERBEST_S` boyunca hiç
# görünmezse durum ÇÖZÜLMÜŞ sayılır ve yeniden belirmesi YENİDEN alarmlanır (`mandal_yeniden`).
# GÖRÜNÜRLÜK (YASA-4 + YASA-6): ilk alarm satırı `tekrar_mandali` alanıyla "tekrarlar sayaçta"
# der; sayaç `state/alarm_mandal.json`ta durur ve DIŞ okuyucusu `watchdog.parity_report`un
# `alarm_mandal` satırıdır (→ /api/diagnostics → pano) — bastırılan hiçbir tekrar görünmez olmaz.
# SINIR: teslim katmanına (aşağıdaki `_maybe_notify` 6 sa penceresi) DOKUNULMAZ; sermaye-sınıfı
# jetonlar (NAKED_POSITION, ONAYLI_PLAN_GONDERILMEDI, …) bu sözlükte YOKTUR ve eklenmesi karar
# ister (test_gelen_kutusu_mandal çivisi). Alarm SEVİYESİ ve eşikleri değişmez — yalnız kadans.
MANDAL_FILE = "alarm_mandal.json"
MANDAL_SERBEST_S = 4 * 24 * 3600   # 96 sa: hafta sonu (Cu→Pzt = 72 sa) + pay; altı "aktif durum"
# jeton → {ayrac: hangi alan mandalı AÇAR, alanlar: imzayı kuran alanlar, yalniz/haric: ayraç süzgeci}
# `ayrac` alanı OLMAYAN satır mandallanmaz (eski/başka yayıcılar bugünkü gibi akar — fail-open).
MANDAL_IMZALAR: dict[str, dict] = {
    # adet/durum sapmaları imzayla tam anlatılır → mandallanabilir. `icra` ve `koruma_dolumu`
    # HARİÇ: ikisi de dolum-BAŞINA olaydır (her vaka yeni bir gerçek; imza tuple'ı fiyat/bacak
    # taşımaz, aynı görünen iki vaka AYRI olabilir) — onları mandallamak yeni olayı yutardı.
    "MIRROR_DRIFT": {"ayrac": "drift_sinifi", "haric": ("icra", "koruma_dolumu"),
                     "alanlar": ("ticker", "local_qty", "alpaca_qty", "drift_sinifi")},
    # yalnız bar-kaynak uyuşmazlığı (adapters.data._massive_crosscheck). Diğer tüm DATA_QUALITY
    # yayıcıları (determinism/monotonicity/ownership/parity/…) `kind` süzgecine takılmaz→akar.
    "DATA_QUALITY": {"ayrac": "kind", "yalniz": ("bar_kaynak_uyusmazligi",),
                     "alanlar": ("ticker", "date", "source", "dev_pct")},
}


def _mandal_yakala(token: str, fields: dict) -> dict | None:
    """İmza mandalda mı? None → normal yayın (ve uygunsa `tekrar_mandali` işareti fields'a
    eklenmiş olur); dict → BASTIRILDI (satır yazılmaz, sayaç arttı — dönen kayıt teşhis içindir)."""
    cfg = MANDAL_IMZALAR.get(token)
    if not cfg:
        return None
    ayrac = fields.get(cfg["ayrac"])
    if ayrac is None:
        return None
    if cfg.get("yalniz") and ayrac not in cfg["yalniz"]:
        return None
    if cfg.get("haric") and ayrac in cfg["haric"]:
        return None
    if not fields.get("ticker"):
        return None                       # kimliksiz satır mandallanamaz — olduğu gibi akar
    import time
    from . import store
    imza = token + "|" + "|".join(f"{k}={fields.get(k)}" for k in cfg["alanlar"])
    now = time.time()
    now_iso = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    karar: dict = {}

    def _mut(doc: dict) -> bool:
        """Mandal defterini yerinde günceller: imza serbest penceresi içinde ZATEN varsa tekrarı
        sayar (bastırma kararı), yoksa/eskimişse yeni satır açar (yayın kararı). Kararı dış
        `karar` sözlüğüne yazar, 2× serbest penceresinden eski imzaları süpürür ve True döner."""
        row = doc.get(imza)
        if isinstance(row, dict) and (now - float(row.get("son_ts") or 0)) < MANDAL_SERBEST_S:
            # BİLİNEN-AKTİF DURUM: satır yok, sayaç var (bastırılan SAYILIR ve görünür).
            row["n"] = int(row.get("n") or 0) + 1
            row["bastirilan"] = int(row.get("bastirilan") or 0) + 1
            row["son_ts"] = now
            row["son"] = now_iso
            karar.update(bastir=True, kayit=dict(row))
        else:
            yeniden = isinstance(row, dict)   # serbest penceresini aşmış ESKİ imza yeniden belirdi
            doc[imza] = {"token": token, "ilk": (row or {}).get("ilk") or now_iso, "son": now_iso,
                         "son_ts": now, "n": int((row or {}).get("n") or 0) + 1,
                         "bastirilan": int((row or {}).get("bastirilan") or 0),
                         "yeniden": yeniden}
            karar.update(bastir=False, yeniden=yeniden)
            # SÜPRÜNTÜ: 2× serbest penceresinden eski imzalar düşer — defter okunur kalır; düşen
            # imzanın yeniden belirmesi zaten YENİ imza muamelesi görür (ilk görüşte alarm).
            for k in [k for k, v in doc.items()
                      if isinstance(v, dict) and (now - float(v.get("son_ts") or 0)) > 2 * MANDAL_SERBEST_S]:
                doc.pop(k, None)
        return True

    store.update_json(MANDAL_FILE, _mut, {})
    if karar.get("bastir"):
        return {"ts": now_iso, "level": "alarm",
                "event": f"{token} {str(fields.get('message') or '')[:160]}",
                "mandal_bastirildi": True, "imza": imza, **karar["kayit"]}
    fields["tekrar_mandali"] = "state/" + MANDAL_FILE
    if karar.get("yeniden"):
        fields["mandal_yeniden"] = True    # sessiz kalmış durum GERİ geldi — bu bilgi satırda taşınır
    return None


def alarm(token: str, message: str, **fields) -> dict:
    """Emit an alarm line whose text CONTAINS the token monitoring.sh searches for."""
    fields["alarm"] = token
    fields["message"] = message
    try:
        _m = _mandal_yakala(token, fields)
    except Exception:  # sessiz-yutma: mandal makinesinin arızası alarmı ASLA yutamaz — fail-open, satır normal yoldan basılır
        _m = None
    if _m is not None:
        return _m                          # bilinen-aktif durum: satır yok, sayaç state/alarm_mandal.json'ta
    _maybe_notify(token, message)
    # the raw token appears in the printed line so a plain substring filter matches
    return _emit("alarm", f"{token} {message}", fields)


def recent(limit: int = 50) -> list[dict]:
    """Son `limit` olayı `state/events.jsonl`dan okur (pano ve testlerin log kazıyıcısız okuma yolu)."""
    from . import store
    return store.read_jsonl(_EVENTS, limit=limit)
