#!/usr/bin/env bash
# tick_watchdog.sh — ASILI-TİCK bekçisinin GÖVDESİ (küçük-kuyruk turu, 2026-08-02).
#
# ================================ NEDEN AYRI DOSYA ============================================
# Bu mantık 2026-07-31'de birim dosyasının `ExecStart=/bin/bash -c '...'` satırının İÇİNE
# yazılmıştı ve ÖLÜYDÜ. Kanıt (A1, salt-okuma ölçüm 2026-08-02 19:46 UTC):
#     journalctl -u meridian-tick-watchdog.service
#     Aug 02 19:32:34 (bash)[10835]: meridian-tick-watchdog.service:
#         Referenced but unset environment variable evaluates to an empty string: YAS
#     Aug 02 19:32:34 bash[10835]: [tick-watchdog] ilerleme var (s)
# `(s)` yazması `(${YAS}s)`nin boş genişlemesidir: systemd, ExecStart satırındaki `$YAS`/`${YAS}`
# dizgelerini bash'e VERMEDEN ÖNCE kendi ortam sözlüğünden ikame eder; sözlükte yoktur, boş dizge
# koyar. Bash'in gördüğü karşılaştırma `[ "" -gt 10800 ]` olur, "integer expression expected" ile
# düşer ve akış HER ZAMAN else dalına gider. Yani bekçi kurulduğu günden beri HİÇBİR restart
# yapamazdı — 45 dk mı 3 sa mı tartışması bu kusurun yanında ikincildir.
# SINIF: "birim dosyasında kabuk-sözdizimi varsayımı" — fail-notify'ın çok-satır-Python vakası
# (2026-07-30) ve `Environment=` satır-sonu yorumu vakasının (2026-08-02) ÜÇÜNCÜ kuşağı. Kalıcı
# ders bu üçünden çıkar: systemd birimi bir kabuk betiği DEĞİLDİR; mantık ayrı bir dosyada yaşar,
# birim yalnız o dosyayı çağırır. Bu dosya kabuk tarafından okunur, `$` ikamesi bash'indir.
#
# ============================== EŞİK: 45 DK (KALICI) ==========================================
# ÖNCEKİ DEĞER 10800 sn idi ve birim açıklamasında "3sa-GECICI(ilk-tam-tick; sabah 45dk-normale
# döner)" yazıyordu. "Sabah" 2026-07-31'di; etiket 2026-08-02'ye kadar durdu. Artık KALICI 2700.
# ÖLÇÜM (A1 canlı olay defteri + systemd journal, 2026-08-02, salt-okuma):
#   * NORMAL İŞLEYİŞ: son 24 saatte poll işaretlerinin (finviz_unavailable · candidate_review_backlog
#     · sprint_cadence_*) 513 damgası — medyan aralık 300 sn, p95 301 sn, MAKSİMUM 302 sn (5,0 dk).
#     45 dk bunun 8,9 KATIDIR. Yanlış alarm payı geniş.
#   * KURUCU VAKA: 2026-07-30 21:14→22:27 UTC asılı-tick — ölçülen sessizlik 73,1 dk. 45 dk bunu
#     YAKALAR; eski 10800 sn (3 sa) YAKALAMAZDI. Yani "geçici" gevşetme, bekçiyi tam da onu var
#     eden vakaya karşı kör bırakmıştı.
#   * İKİ EK İLERLEMESİZ PENCERE (aynı ölçüm, systemd'de restart YOK — süreç ayaktaydı):
#     2026-07-31 00:16:16→01:56:32 = 100,3 dk ve 2026-07-31 20:12:58→21:37:32 = 84,6 dk.
#     İKİSİ DE AYNI kod bölgesinde: `earnings_refreshed` olayından `arming_measured` olayına.
#     Bunlar "yavaş ama çalışan kadans" DEĞİL, tekrar eden bir takılmadır (kök neden ayrı tur —
#     günlükteki `earnings.refresh` ağ-nondeterminizmi kalemiyle aynı bölge). 45 dk'lık kapı bu
#     pencerelerde ateşlenir ve bu DOĞRUDUR: kadans damgaları ilerlememiştir, restart sonrası
#     sonraki poll onları yeniden koşar.
#
# ============================ NABIZ SÖZLEŞMESİ (v186, 2026-08-04) =============================
# Uzun süpürmeler (bar yükleme/onarım, sip düzeltmesi, hacim kalibrasyonu, kazanç takvimi, tarama)
# artık YİNELEME BAŞINA bir İLERLEME NABZI atar ve nabız bu betiğin okuduğu damgayı tazeler
# (`meridian/scheduler.py` → İLERLEME NABZI bloğu; nabız = `_persist()`, yeni bir biçim yok).
# NEDENİ: 2026-08-03 20:00→23:30 UTC'de bu bekçi meşru-uzun bir EOD döngüsünü ÜÇ kez öldürdü —
# döngü asılı değildi, damga yalnız döngü SONUNDA yazılıyordu. HÜKÜM: eşik YÜKSELTİLMEZ, NABIZ
# EKLENİR. Gerçekten tek bir çağrıda asılan bir döngü hiçbir yinelemeyi bitiremez, nabız atmaz ve
# aşağıdaki 2700 sn eşiği onu ESKİSİ GİBİ yakalar.
#
# ========================= SEANS FARKINDALIĞI: ÖLÇÜLDÜ, GEREKSİZ ==============================
# Brief'in sorusu: hafta sonu tick yok — 45 dk sahte alarm üretir mi? ÖLÇÜM: HAYIR, ve bu yüzden
# takvim/mcal bağı EKLENMEDİ (gereksiz bir bağımlılık uydurmak çözüm değildir).
#   * Ölçülen 24 saatin TAMAMI seans dışıdır (2026-08-02 Pazar) ve maksimum poll aralığı yine
#     302 sn çıktı.
#   * MEKANİZMA (koda karşı doğrulandı): `scheduler.advance_once()` seans dışında "güncel" dalına
#     düşer ve o dal `_persist()` çağırır (`scheduler.advance_once`) — yani `scheduler_status.updated`
#     seanstan BAĞIMSIZ olarak her poll'de (300 sn) tazelenir. `_run()`un istisna dalı da
#     `updated` yazar (`scheduler._run`). Seans dışı olmak damganın DURMASI demek değildir.
#   * CANLI KANIT: 2026-08-02 19:46:50Z ölçüm anı · scheduler_status.updated = 19:45:59Z → yaş 51 sn.
#
# ============================ YAS (YENİDEN-BAŞLATMA-SONRASI) ==================================
# Yeniden başlatmadan hemen sonra `scheduler_status.json` HÂLÂ eski `updated`ı taşır (yeni süreç
# onu saniyeler içinde tazeler, ama "saniyeler" > 0). Zamanlayıcı o aralığa denk gelirse taze
# doğmuş bir süreci bayat sanıp yeniden başlatır — ve bu KENDİNİ BESLEYEN bir restart döngüsüdür.
# Bu yüzden servisin systemd'den okunan AYAKTA KALMA SÜRESİ eşiğin altındaysa hüküm VERİLMEZ.
# Sinyal uydurma değil ölçülmüştür: `ActiveEnterTimestamp` = 2026-08-02 19:05:18 UTC, aynı anın
# journal satırı "Started meridian.service" = 19:05:18 — birebir.
set -uo pipefail

DURUM_DOSYASI="${MERIDIAN_TICK_DURUM:-/opt/meridian/state/scheduler_status.json}"
BIRIM="${MERIDIAN_TICK_BIRIM:-meridian.service}"
# Monotonik "şimdi"nin KAYNAK YOLU. Üretimde her zaman /proc/uptime'dır; ayrı bir değişken olması
# YAS lütuf dalının bir sınama düzeneğinde de koşabilmesi içindir (geliştirme makinesi Linux
# değildir ve /proc yoktur). Bu bir DAVRANIŞ anahtarı değil bir YOL anahtarıdır — `MERIDIAN_TICK_DURUM`
# ile aynı sınıf. Dal, ölçülemeyen bir kaynakta sessizce atlanır (aşağıdaki `-n` kapıları).
MONO_KAYNAK="${MERIDIAN_TICK_MONO_KAYNAK:-/proc/uptime}"
BAYAT_VARSAYILAN=2700            # 45 dk — KALICI (yukarıdaki ölçüm)
YAS_LUTUF_VARSAYILAN=300         # restart sonrası hüküm verilmeyen pencere (5 dk)

BAYAT_S="${MERIDIAN_TICK_BAYAT_S:-$BAYAT_VARSAYILAN}"
YAS_LUTUF_S="${MERIDIAN_TICK_YAS_LUTUF_S:-$YAS_LUTUF_VARSAYILAN}"

# BEYAN ZORUNLU: eşik varsayılandan SAPTIYSA her koşuda journal'a yazılır. "Geçici" bir gevşetmenin
# iki gün sonra hâlâ yürürlükte olduğunu kimsenin fark etmemesi bu turun kapattığı kusurdur —
# beyan, gevşetmeyi sessiz olmaktan çıkarır.
if [ "$BAYAT_S" != "$BAYAT_VARSAYILAN" ]; then
  echo "[tick-watchdog] BEYAN: eşik ENV ile gevşetildi/sıkıldı — MERIDIAN_TICK_BAYAT_S=${BAYAT_S}s (kalıcı varsayılan ${BAYAT_VARSAYILAN}s). Bu satır her koşuda basılır."
fi
if [ "$YAS_LUTUF_S" != "$YAS_LUTUF_VARSAYILAN" ]; then
  echo "[tick-watchdog] BEYAN: YAS lütuf penceresi ENV ile değiştirildi — MERIDIAN_TICK_YAS_LUTUF_S=${YAS_LUTUF_S}s (varsayılan ${YAS_LUTUF_VARSAYILAN}s)."
fi

# ---- (1) YAS LÜTFU: birim az önce mi doğdu? --------------------------------------------------
UPTIME_S="$(systemctl show "$BIRIM" --property=ActiveEnterTimestampMonotonic --value 2>/dev/null || echo "")"
SIMDI_MONO="$(awk '{printf "%d", $1 * 1000000}' "$MONO_KAYNAK" 2>/dev/null || echo "")"
if [ -n "$UPTIME_S" ] && [ -n "$SIMDI_MONO" ] && [ "$UPTIME_S" != "0" ]; then
  AYAKTA=$(( (SIMDI_MONO - UPTIME_S) / 1000000 ))
  if [ "$AYAKTA" -ge 0 ] && [ "$AYAKTA" -lt "$YAS_LUTUF_S" ]; then
    echo "[tick-watchdog] YAS lütfu: ${BIRIM} ${AYAKTA}s önce başladı (< ${YAS_LUTUF_S}s) — hüküm VERİLMEDİ"
    exit 0
  fi
fi

# ---- (2) DAMGANIN YAŞI ------------------------------------------------------------------------
# ÖLÇÜLEMEYEN None'dır, 0 DEĞİLDİR (uydurma yasağı). Dosya yoksa/bozuksa "0 saniye bayat" demek
# sistemin sağlıklı olduğunu İDDİA etmek olurdu; eski gömülü sürüm tam bunu yapıyordu
# (`|| echo 0`). Burada ölçülemeyen hâl AYRI bir dal ve restart TETİKLEMEZ (bekçinin kendi
# arızası, izlenen sürecin arızası değil) ama journal'da sessiz de kalmaz.
#
# OKUMA SÖZLEŞMESİ (TSK-265 dilim 1, 2026-10-02). Durum dosyasını ubuntu süreçleri yazar; birim
# 2026-10-02'ye dek ROOT koşuyordu, artık `User=ubuntu` koşar — okuma bir yetki sınırını GEÇMEZ.
# Arıza şekli yine de sözleşmelidir, çünkü bekçinin bekçisi yoktur:
#   * `python3 -I` — PYTHONPATH/PYTHONHOME/kullanıcı site-packages ve çalışma dizini yorumlayıcının
#     ithal yoluna GİRMEZ (betik heredoc'tan koşar; ithal edilen tek şey stdlib).
#   * `O_NONBLOCK` — yolun yerinde bir FIFO dursaydı düz `open()` bir yazar gelene dek SONSUZA
#     asılırdı: timer'ın oneshot'u hiç bitmez, sonraki tetikler kuyrukta kalır, bekçi SUSAR.
#     Bloklamasız açılış anında döner; ardından `fstat` düzenli dosya değilse ÖLÇÜLEMEDİ.
#   * `O_NOFOLLOW` — son bileşen bir bağsa izlenmez (ELOOP → ÖLÇÜLEMEDİ). Üretici dosyayı atomik
#     tmp+replace ile DÜZENLİ dosya olarak yazar (`store.write_json`); bağ beklenen bir hâl değildir.
# ÖLÇÜLEMEDİ'NİN NEDENİ stdout'tan gelir ve journal satırına girer. Eski hâlde neden stderr'e
# basılıp `2>/dev/null` ile atılıyordu — FIFO, eksik dosya ve bozuk JSON journal'da AYNI satırdı.
# stderr artık bastırılmaz: yorumlayıcının kendi arızası (ör. bilinmeyen bayrak) journal'a düşer.
YAS="$(python3 -I - "$DURUM_DOSYASI" <<'PY'
import datetime as dt, json, os, stat, sys
try:
    fd = os.open(sys.argv[1], os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW)
    with os.fdopen(fd, "rb") as f:
        kip = os.fstat(f.fileno()).st_mode
        if not stat.S_ISREG(kip):
            raise ValueError(f"duzenli dosya degil ({stat.filemode(kip)})")
        d = json.loads(f.read())
    t = dt.datetime.fromisoformat(str(d["updated"]))
    if t.tzinfo is None:
        t = t.replace(tzinfo=dt.timezone.utc)
    print(int((dt.datetime.now(dt.timezone.utc) - t).total_seconds()))
except Exception as e:
    print(f"OLCULEMEDI {type(e).__name__}: {str(e)[:160]}".replace("\n", " "))
    sys.exit(3)
PY
)"

case "$YAS" in
  ''|*[!0-9-]*)
    echo "[tick-watchdog] ÖLÇÜLEMEDİ: ${DURUM_DOSYASI} okunamadı/ayrıştırılamadı (${YAS:-neden yok: yorumlayıcı çıktı vermedi}) — hüküm VERİLMEDİ (restart YOK). Bekçinin kendi arızası izlenen sürecin arızası sayılmaz."
    exit 0 ;;
esac

# ---- (3) HÜKÜM --------------------------------------------------------------------------------
# RESTART YETKİSİ POLKIT'TEDİR (TSK-265 dilim 1): birim `User=ubuntu` koşar; `systemctl restart`
# DBus'tan geçer ve /etc/polkit-1/rules.d/52-meridian-tick-watchdog.rules onu YALNIZ bu birim +
# bu fiil için verir. `--no-ask-password`: ajansız bir oturumda yetki sorusu sorulmaz, ret ANINDA
# döner. RET SESSİZ BAŞARI DEĞİLDİR: systemctl'in kendi gerekçesi adlı satırla basılır ve betik
# sıfırdan farklı çıkar → birim `failed` → `OnFailure=meridian-fail-notify.service` bildirimi.
# İKİ ARIZA, İKİ AD (düzeltme turu 1, inceleme M1): systemctl'in iletisi polkit reddini taşıyorsa
# (Access denied · Interactive authentication required · Not authorized) YETKİ — çıkış 4, kuralın yeri
# söylenir; taşımıyorsa birim başlatılamamıştır (ExecStart düştü vb.) — İŞ arızası, çıkış 5, polkit
# SUÇLANMAZ (yanlış teşhis operatörü yanlış yeri onarmaya gönderirdi).
# BAŞARIDA da çıktı basılır (M2, bedel yasası): yakalama eskiden journal'a düşen uyarıları ("unit file
# changed on disk" = /etc depodan ayrışmış) sessizce atmamalı.
if [ "$YAS" -gt "$BAYAT_S" ]; then
  echo "[tick-watchdog] durum ${YAS}s bayat (eşik ${BAYAT_S}s) -> ${BIRIM} yeniden başlatılıyor"
  RESTART_CIKTI="$(systemctl --no-ask-password restart "$BIRIM" 2>&1)"
  RESTART_RC=$?
  if [ "$RESTART_RC" -ne 0 ]; then
    case "$RESTART_CIKTI" in
      *"Access denied"*|*"Interactive authentication required"*|*"ot authorized"*)
        echo "[tick-watchdog] RESTART BAŞARISIZ (YETKİ): systemctl restart ${BIRIM} çıkış ${RESTART_RC} — ${RESTART_CIKTI}. Bekçi User=ubuntu koşar; yetki /etc/polkit-1/rules.d/52-meridian-tick-watchdog.rules kuralındadır (kurulum: site.yml). Bayat süreç YENİDEN BAŞLATILMADI." >&2
        exit 4 ;;
      *)
        echo "[tick-watchdog] RESTART BAŞARISIZ (İŞ): systemctl restart ${BIRIM} çıkış ${RESTART_RC} — ${RESTART_CIKTI:-çıktı yok}. Yetki reddi DEĞİL (polkit iletisi yok): birim yeniden başlatılamadı — teşhis: journalctl -u ${BIRIM} -n 100." >&2
        exit 5 ;;
    esac
  fi
  if [ -n "$RESTART_CIKTI" ]; then
    echo "[tick-watchdog] systemctl çıktısı (başarıda): ${RESTART_CIKTI}"
  fi
  echo "[tick-watchdog] ${BIRIM} yeniden başlatıldı"
else
  echo "[tick-watchdog] ilerleme var (${YAS}s / eşik ${BAYAT_S}s)"
fi
