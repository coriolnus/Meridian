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
# ========================= SEANS FARKINDALIĞI: ÖLÇÜLDÜ, GEREKSİZ ==============================
# Brief'in sorusu: hafta sonu tick yok — 45 dk sahte alarm üretir mi? ÖLÇÜM: HAYIR, ve bu yüzden
# takvim/mcal bağı EKLENMEDİ (gereksiz bir bağımlılık uydurmak çözüm değildir).
#   * Ölçülen 24 saatin TAMAMI seans dışıdır (2026-08-02 Pazar) ve maksimum poll aralığı yine
#     302 sn çıktı.
#   * MEKANİZMA (koda karşı doğrulandı): `scheduler.advance_once()` seans dışında "güncel" dalına
#     düşer ve o dal `_persist()` çağırır (scheduler.py:976) — yani `scheduler_status.updated`
#     seanstan BAĞIMSIZ olarak her poll'de (300 sn) tazelenir. `_run()`un istisna dalı da
#     `updated` yazar (scheduler.py:1051). Seans dışı olmak damganın DURMASI demek değildir.
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
YAS="$(python3 - "$DURUM_DOSYASI" <<'PY' 2>/dev/null
import datetime as dt, json, sys
try:
    with open(sys.argv[1]) as f:
        d = json.load(f)
    t = dt.datetime.fromisoformat(str(d["updated"]))
    if t.tzinfo is None:
        t = t.replace(tzinfo=dt.timezone.utc)
    print(int((dt.datetime.now(dt.timezone.utc) - t).total_seconds()))
except Exception as e:
    print(f"OLCULEMEDI {type(e).__name__}", file=sys.stderr)
    sys.exit(3)
PY
)"

case "$YAS" in
  ''|*[!0-9-]*)
    echo "[tick-watchdog] ÖLÇÜLEMEDİ: ${DURUM_DOSYASI} okunamadı/ayrıştırılamadı — hüküm VERİLMEDİ (restart YOK). Bekçinin kendi arızası izlenen sürecin arızası sayılmaz."
    exit 0 ;;
esac

# ---- (3) HÜKÜM --------------------------------------------------------------------------------
if [ "$YAS" -gt "$BAYAT_S" ]; then
  echo "[tick-watchdog] durum ${YAS}s bayat (eşik ${BAYAT_S}s) -> ${BIRIM} yeniden başlatılıyor"
  systemctl restart "$BIRIM"
else
  echo "[tick-watchdog] ilerleme var (${YAS}s / eşik ${BAYAT_S}s)"
fi
