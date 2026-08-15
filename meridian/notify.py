"""notify.py — operatöre kısa mesaj itme (Telegram / genel webhook) + yerel alarm gelen kutusu; yalnız stdlib.

NE YAPAR. `send(text)` yapılandırılmış kanallara iletir; kanal yoksa güvenli no-op'tur — her
yerden çağrılabilir. Alarm sınıflarına bağlıdır: devre-kesici, rollback, HALT, yeni plan.
`inbox()` ACK'lenmemiş alarmları `events.jsonl`dan imzaya göre gruplar: gelen kutusu ikinci bir
defter DEĞİL bir GÖRÜNÜMDÜR — tek kaynak olaylardır, burada yalnız "nereye kadar okudum"
(`alerts_ack.json`) durur ve ACK hiçbir alarmı silmez, yalnız "gördüm" der. `_signature` aynı
kusurun tekrarını tek satıra toplar (anahtar varsa ticker ile İNCELTİR, mesaj yedeğinde bilinen
ticker'ı normalize eder — kaba birleşme de yanlış bölme de ölçülüp düzeltilmiş iki ayrı hataydı).

DEĞİŞMEZLER. Sır disiplini: `scrub()` giden metinden BİLİNEN sır değerlerini (secrets.ALLOWED)
siler — bu modül dışarıya veri gönderen TEK yoldur ve "asla sır göndermez" iddiasının uygulaması
tam budur (iddia bir dönem docstring'de vardı, uygulaması yoktu). Teslimat başarısızlığı sessiz
kalmaz (`notify_delivery_failed`): "telefonuma bildirim gelmedi" ile "zaten alarm yoktu" ayırt
edilebilmelidir. "Operatöre ulaştı" ile "operatör GÖRDÜ" ayrı şeylerdir; ikincisini yalnız ACK
kanıtlar. Kapıyı geçen plan (`new_plan`) alarm değil BİLGİ sınıfıdır — obs alarm zinciri onu
asla itmez, tetiği üretim döngüsüdür.

GİRİŞLER: `configured()`, `send()`, `inbox()`, `scrub()`, `breaker`/`rollback`/`halted`/
`new_plan`. Yapılandırma (env ya da sır deposu): TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID ve/veya
MERIDIAN_WEBHOOK_URL. Okur: `events.jsonl`; yazar: yalnız ağ kanalları (dosyaya yazmaz;
`alerts_ack.json`u yazan pano ucudur)."""
from __future__ import annotations
import json
import urllib.request

from . import secrets


def _post(url: str, payload: dict, timeout: float = 8.0) -> bool:
    try:
        req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                     headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=timeout)
        return True
    except Exception:  # sessiz-yutma: ağ/sağlayıcı hatası bu yolun NORMAL hâli; çağıran boş sonuç üzerinden yedek kaynağa düşer ve kaynak seçimi ayrıca kaydedilir
        return False


def configured() -> bool:
    return bool((secrets.get("TELEGRAM_BOT_TOKEN") and secrets.get("TELEGRAM_CHAT_ID"))
                or secrets.get("MERIDIAN_WEBHOOK_URL"))


# --------------------------------------------------------------------------------------------
# YEREL GELEN KUTUSU (2026-07-26) — uzak kanal yokken alarmın KAYBOLMAMASI için.
#
# NEDEN YENİ BİR DEFTER YOK: `events.jsonl` her alarmı zaten ts + level="alarm" + alarm=<jeton> +
# message ile taşıyor (obs.alarm) ve dış okuyucuları var. Alarm metnini ikinci bir deftere
# KOPYALAMAK üçüncü bir şema yüzeyi, bir budama sorunu ve iki kaynağın sessizce ayrışması demekti.
# Gelen kutusu bir GÖRÜNÜM'dür: tek kaynak olaylardır, burada yalnız "nereye kadar okudum" durur.
# ACK yalnız bir zaman damgasıdır — hiçbir alarmı SİLMEZ, yalnız "bunları gördüm" der.
ACK_FILE = "alerts_ack.json"


def _signature(ev: dict) -> str:
    """Aynı kusurun tekrarını TEK satırda topla: jeton + onu doğuran mekanizma. Rakamlar tekilliği
    şişirdiği için (ör. '23 plan kayıtsız kayboldu' → '# plan...') mesajda normalize edilir.

    TICKER İKİ YÖNE BİRDEN ÇALIŞIR (2026-07-26) — ve eskiden ikisinde de yanlış tarafta duruyordu:
      * KABA BİRLEŞME: anahtar alanı VARKEN `kind` gibi geniş bir anahtar farklı olayları tek gruba
        çökertiyordu — "SESSİZ BAR MUTASYONU: AAPL 07-20" ile ":TSLA 07-24" ikisi de `kind=determinism`
        olduğu için TEK satıra düşüyor, iki ayrı sembolün bozulması bir sayaç olarak okunuyordu.
        Çözüm: anahtar bulunduysa ticker ile İNCELT (determinism·AAPL ≠ determinism·TSLA).
      * YANLIŞ BÖLME: anahtar alanı OLMAYAN alarmlar mesaj yedeğine düşüyor ve oradaki ticker varyansı
        AYNI kusuru çok satıra bölüyordu — "Alpaca reddi: AAPL — insufficient buying power" ile
        ":TSLA — ..." iki ayrı grup oluyordu. Çözüm: mesaj yedeğinde BİLİNEN ticker'ı `§` ile sil.
    Bu yüzden ticker anahtar listesine TEK BAŞINA GİRMEZ: girseydi ikinci senaryodaki tek kusur yine
    ticker başına bölünürdü. Ve normalizasyon yalnız BİLİNEN ticker'a uygulanır — genel bir BÜYÜK-HARF
    kuralı Türkçe vurgu sözcüklerini ("SESSİZ", "CANLI", "MAKULLÜK") sembol sanıp mesajı boşaltırdı."""
    import re
    key = next((str(ev[k]) for k in ("mechanism", "check", "artifact", "field", "kind")
                if ev.get(k)), "")
    tic = str(ev.get("ticker") or "")
    if key:
        if tic:
            key = f"{key}·{tic}"
    else:
        msg = str(ev.get("message") or "")
        if tic:
            msg = msg.replace(tic, "§")
        key = re.sub(r"\d+", "#", msg)[:80]
    return f"{ev.get('alarm')}·{key}"


EVENT_WINDOW = 4000     # gelen kutusunun okuduğu olay penceresi (satır)


def inbox(limit: int = 60) -> dict:
    """ACK'lenmemiş alarmları imzaya göre gruplanmış olarak döndür — panonun ve bekçinin tükettiği
    görünüm. Uzak kanal bağlı olsa da olmasa da çalışır: 'operatöre ulaştı' ile 'operatör GÖRDÜ'
    ayrı şeylerdir ve ikincisini yalnız ACK kanıtlar."""
    from . import obs, store
    ack = (store.read_json(ACK_FILE, {}) or {}).get("ack_ts") or ""
    evs = store.read_jsonl("events.jsonl", limit=EVENT_WINDOW)
    groups: dict = {}
    for ev in evs:
        if ev.get("level") != "alarm" or ev.get("alarm") not in obs.NOTIFY_TOKENS:
            continue
        if ack and str(ev.get("ts") or "") <= ack:
            continue
        sig = _signature(ev)
        g = groups.setdefault(sig, {"token": ev.get("alarm"), "n": 0, "first_ts": ev.get("ts"),
                                    "last_ts": ev.get("ts"), "message": ev.get("message")})
        g["n"] += 1
        g["last_ts"] = ev.get("ts")
        # GRUBUN METNİ SON MESAJDIR (2026-07-26): imza aynı olsa da mesaj DEĞİŞİR (ör. "%18 kapsama"
        # → "%41 kapsama"). İlk mesajı göstermek operatöre penceredeki EN ESKİ hâli okutuyordu ve
        # durum düzelirken de kötüleşirken de aynı satır duruyordu. Grup bir SAYAÇ + bir DURUM
        # taşır; durum en taze gözlemdir.
        g["message"] = ev.get("message")
    rows = sorted(groups.values(), key=lambda g: str(g["last_ts"]), reverse=True)[:limit]
    # PENCERE KESTİ Mİ — ÖLÇÜM, TAHMİN DEĞİL. Okunan en eski satır ACK sınırından DAHA YENİYSE,
    # sınırla o satır arasındaki alarmlar bu görünüme hiç girmemiştir: "0 bekliyor" ile "0 GÖRDÜM"
    # ayrı şeyler ve ikincisi burada kanıtlanamaz. ACK hiç yoksa karşılaştıracak sınır da yoktur →
    # `None` (ölçülmedi); `False` demek ölçmediğimiz bir temizliği iddia etmek olurdu.
    _oldest = str((evs[0].get("ts") if evs else "") or "")
    _trunc = (_oldest > ack) if (ack and _oldest) else None
    return {"ack_ts": ack or None, "pending": sum(g["n"] for g in groups.values()),
            "groups": rows, "channel_configured": configured(),
            "window_truncated": _trunc, "window_lines": EVENT_WINDOW,
            "window_oldest_ts": _oldest or None}


def scrub(text: str) -> str:
    """Giden metinden BİLİNEN sır değerlerini temizle (denetim turu 19, 2026-07-21).

    Bu modül dışarıya veri gönderen TEK yol. Bir alarm metni bir gün bir hata dizgisini taşırsa
    (ör. 'HTTPStatusError ... ?apikey=…'), o anahtar Telegram'a/webhook'a gider — yani sır, kendi
    makinemizden ÇIKAR. 'Asla sır göndermez' iddiası docstring'de vardı, uygulaması yoktu."""
    out = str(text)
    for name in getattr(secrets, "ALLOWED", ()):
        try:
            v = secrets.get(name)
        except Exception:  # sessiz-yutma: ağ/sağlayıcı hatası bu yolun NORMAL hâli; çağıran boş sonuç üzerinden yedek kaynağa düşer ve kaynak seçimi ayrıca kaydedilir
            v = None
        if v and len(str(v)) >= 8:
            out = out.replace(str(v), "***")
    return out


def send(text: str) -> bool:
    """Deliver `text` to whichever channels are configured. Returns True if at least one succeeded.

    TESLİMAT BAŞARISIZLIĞI SESSİZ KALMAZ: yapılandırılmış bir kanal cevap vermezse bu KAYDA geçer —
    aksi halde 'telefonuma bildirim gelmedi' ile 'zaten alarm yoktu' ayırt edilemez (turu 19)."""
    text = scrub(text)
    ok, tried = False, []
    tok, chat = secrets.get("TELEGRAM_BOT_TOKEN"), secrets.get("TELEGRAM_CHAT_ID")
    if tok and chat:
        r = _post(f"https://api.telegram.org/bot{tok}/sendMessage",
                  {"chat_id": chat, "text": text, "disable_web_page_preview": True})
        ok, _ = (ok or r), tried.append(("telegram", r))
    hook = secrets.get("MERIDIAN_WEBHOOK_URL")
    if hook:
        r = _post(hook, {"text": text})
        ok, _ = (ok or r), tried.append(("webhook", r))
    failed = [n for n, r in tried if not r]
    if failed:
        try:
            from . import obs
            obs.warn("notify_delivery_failed", channels=",".join(failed), delivered=ok)
        except Exception:  # sessiz-yutma: kayıt kanalının kendisi düştü — ikinci bir kanal yok; kayıt denemesi çağıranı düşüremez
            pass
    return ok


# convenience wrappers keyed to the alarm classes (safe no-op if unconfigured)
def breaker(day_pnl_pct: float):
    return configured() and send(f"⚠️ Meridian devre kesici: günlük kayıp {day_pnl_pct:.2%} — yeni giriş durdu.")


def rollback(frm: int, to: int, delta: float):
    return configured() and send(f"↩️ Meridian rollback: v{frm} → v{to} (skor {delta:+.3f}) otomatik geri alındı.")


def halted(on: bool):
    return configured() and send("🛑 Meridian DURDURULDU (HALT)." if on else "▶️ Meridian devam ediyor.")


# ---- BAĞLANMAMIŞ İKİ İTME: DURUMLARI AYRI, KARARLARI AYRI (K1, 2026-07-30) ------------------
# Denetim ikisini de "hiç tetiklenmiyor" diye buldu (AST ile doğrulandı: breaker 1, halted 2,
# rollback 1, send 6, inbox 3 çağrı — bu ikisi SIFIR). Ama sebepleri AYNI DEĞİL ve bu yüzden
# kararları da aynı olamaz. "İkisi de ölü" demek, birini yanlış yola bağlamaya davetiye olurdu.
def new_plan(ticker: str, verdict: str, rr, n: int = 1, date: str | None = None):
    """BAĞLANDI (3b, 2026-07-30) — tetiği `loop.daily_cycle`ın plan-silahlama dalıdır.

    Kapıyı geçen bir plan ALARM DEĞİLDİR (bilgi sınıfı), dolayısıyla `obs.alarm` → `_maybe_notify`
    yolu onu ASLA itmez: bu fonksiyonun bağlanacağı tek yer üretim döngüsüdür. K1 turunda loop.py
    başka bir ajanın yüzeyi olduğu için kablo bilinçli olarak kurulmamıştı (`K1-NOTU`); 3b turunda
    kuruldu ve loop'taki ham `notify.send` metni BUNUNLA DEĞİŞTİRİLDİ — iki metin bırakmak, aynı
    olguyu iki farklı biçimde anlatan iki kod yolu demekti (sözleşmesiz defter deseninin bildirim
    katmanındaki hâli).

    `n`: o turda silahlanan plan SAYISI (1'den büyükse örnek plan ticker'la verilir); `date`: tur
    tarihi. Kapı hükmü (`verdict`) metne GİRER çünkü GO ile REVIEW aynı bildirim değildir: REVIEW
    insan gözü isteyen bir plandır ve bunu bildirimden okumak gerekir."""
    bas = f"🔎 Yeni plan{f' ×{n}' if n and n > 1 else ''}"
    tarih = f" ({date})" if date else ""
    return configured() and send(f"{bas}{tarih}: {ticker} · kapı {verdict} · R:R {rr}. "
                                 f"Panoyu kontrol et.")


# ÇIKARILDI 2026-07-30 (temizlik turu): `data_quality(detail)` — veri kalitesi bildirim
# sarmalayıcısı. K1 turunda (aynı gün) kendi docstring'i zaten "EMEKLİ — bağlanması ÇİFT bildirim
# üretirdi; çağıran eklenmez" diyordu; bu tur beyanı fiiliyata geçirdi.
# ÇAĞIRAN TARAMASI (meridian/ + tests/): `notify.data_quality` için tek eşleşme tanımın kendisiydi.
# (`data_quality.json` eşleşmeleri AYRI bir artefakttır — loop.py yazar, api/intraday_shadow okur;
# bu fonksiyonla ilgisi yoktur.)
# YERİNE GEÇEN TEK KAPI: `obs.alarm(obs.ALARM_DATA_QUALITY, …)`. O çağrı `obs._maybe_notify`
# üzerinden ZATEN `notify.send` yapıyor ve jeton başına 6 saatlik susturma penceresi uyguluyor.
# Veri-kalitesi yolları (adapters/data.py bar kaynak uyuşmazlığı, scheduler.py seans atlama) o
# kanala bağlı — bu fonksiyonu ayrıca çağırmak aynı olguyu iki kez iter ve susturmayı ATLARDI.
# GERİ-AL: `return configured() and send(f"🧪 Meridian veri kalitesi uyarısı: {detail}")` — bu
# yorumun yerine. Ama önce yukarıdaki çift-bildirim gerekçesini çürütmek gerekir.
