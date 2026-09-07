#!/usr/bin/env bash
# EDG-2026-085 ADIM-0 (3) — PİLOT ÖNCESİ TABAN ÖRNEKLEMİ (A1, seans içi, 5 dk'da bir; meridian-edg085-taban.timer).
# Ne ölçer: motor sürecinin CPU payı (10 sn pencere, tek çekirdek yüzdesi), /healthz gecikmesi (5 istek → p50/maks),
# load1, state/ ve state/bars bayt, /opt/meridian boş disk. Çıktı: /opt/veri/olcum/edg085/taban.jsonl (repo DIŞI —
# dagit rsync --delete repo-dışı research/ çıktısını siler; /opt/veri dokunulmaz). Okuyucu (Yasa 6): kartın fizibilite-2
# eşiği (cpu_payi_delta_ust_pp=5, healthz_p95_delta_ms_ust=50) bu dosyadan türetilir; hüküm Rol-1'in.
# Uydurma yasağı: ölçülemeyen alan null + neden. Sır yok, argv'de değer yok.
set -u
CIKTI_DIZIN=/opt/veri/olcum/edg085
CIKTI=$CIKTI_DIZIN/taban.jsonl
mkdir -p "$CIKTI_DIZIN" 2>/dev/null || true
TS=$(date -u +%FT%TZ)
PID=$(systemctl show -p MainPID --value meridian.service 2>/dev/null || echo 0)
CLK=$(getconf CLK_TCK 2>/dev/null || echo 100)
NCPU=$(nproc 2>/dev/null || echo 0)
cpu_pct=null; cpu_neden=null
if [ -n "$PID" ] && [ "$PID" != "0" ] && [ -r "/proc/$PID/stat" ]; then
  t0=$(awk '{print $14+$15}' "/proc/$PID/stat"); sleep 10
  if [ -r "/proc/$PID/stat" ]; then
    t1=$(awk '{print $14+$15}' "/proc/$PID/stat")
    cpu_pct=$(awk -v a="$t0" -v b="$t1" -v c="$CLK" 'BEGIN{printf "%.2f", (b-a)/c/10*100}')
  else cpu_neden='"süreç 10 sn içinde kayboldu"'; fi
else cpu_neden='"MainPID yok ya da /proc okunamadı (worker durmuş olabilir)"'; fi
# healthz gecikmesi (saniye → ms), 5 istek
lat=()
for i in 1 2 3 4 5; do
  v=$(curl -s -o /dev/null -m 5 -w "%{time_total}" http://127.0.0.1:8080/healthz 2>/dev/null || echo "")
  [ -n "$v" ] && lat+=("$v")
done
if [ "${#lat[@]}" -ge 3 ]; then
  sorted=$(printf "%s\n" "${lat[@]}" | sort -g)
  p50=$(echo "$sorted" | awk 'NR==3{printf "%.1f", $1*1000}')
  mx=$(echo "$sorted" | tail -1 | awk '{printf "%.1f", $1*1000}')
  h_n=${#lat[@]}
else p50=null; mx=null; h_n=${#lat[@]}; fi
load1=$(awk '{print $1}' /proc/loadavg 2>/dev/null || echo null)
state_b=$(du -sb /opt/meridian/state 2>/dev/null | cut -f1 || echo null)
bars_b=$(du -sb /opt/meridian/state/bars 2>/dev/null | cut -f1 || echo null)
bos_b=$(df -B1 --output=avail /opt/meridian 2>/dev/null | tail -1 | tr -d ' ' || echo null)
printf '{"ts":"%s","pid":%s,"ncpu":%s,"cpu_pct_tek_cekirdek":%s,"cpu_neden":%s,"healthz_p50_ms":%s,"healthz_max_ms":%s,"healthz_n":%s,"load1":%s,"state_bayt":%s,"bars_bayt":%s,"bos_disk_bayt":%s}\n' \
  "$TS" "${PID:-0}" "${NCPU:-0}" "$cpu_pct" "$cpu_neden" "$p50" "$mx" "$h_n" "${load1:-null}" "${state_b:-null}" "${bars_b:-null}" "${bos_b:-null}" >> "$CIKTI"
