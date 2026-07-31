#!/usr/bin/env bash
# deploy/monitoring.sh — GCP log-based alert policies for the ALARM_ tokens.
#
# ==============================================================================================
# BAYAT YOL UYARISI (K1, 2026-07-30) — BU KANONİK DAĞITIM DEĞİL
# ==============================================================================================
# Bu betik `gcloud` + `resource.type="gce_instance"` varsayar. Meridian'ın FİİLİ işletimi bu
# değil: yerelde ops/keepalive.sh (state/keepalive.pid), hedef sunucu ise Oracle A1
# (deploy/oracle-a1/meridian.service + systemd). Yani GCP tüketicisi bu kurulumda var OLAMAZ.
#
# NEDEN SİLİNMEDİ: obs.py'nin docstring'i jetonların "Cloud Monitoring log-based metrics fire"
# için basıldığını söylüyordu ve bu betik o beyanın tek dayanağıydı. Betiği silmek beyanı
# havada bırakırdı; onun yerine ikisi de gerçeğe çekildi — obs.py artık GERÇEK tüketicisini
# (notify + notify.inbox) beyan ediyor, bu betik de "GCP'ye dönülürse buradan devam" notu.
#
# DAHA ÖNEMLİ KUSUR ONARILDI: filtre listesi ELLE bakımlıydı ve 11 jetondan yalnız 3'ünü
# tanıyordu (HEARTBEAT_STALE, ROLLBACK, CIRCUIT_BREAKER). obs.py'nin kendi saydığı DATA_QUALITY
# bile yoktu; sonradan eklenen yedi jeton (HALT_ACTIVE, MIRROR_DRIFT, BROKER_REJECT,
# TRAIL_DESYNC, MECHANISM_STALE, ARMING_READY, AUTHORITY_CHANGE) ve K1'de eklenen GOAL_FAILURE
# hiç yoktu. Bu, obs.NOTIFY_TOKENS'ın 2026-07-26'da çözdüğü hatanın BİREBİR aynısıydı: elle
# liste, yeni jeton eklendikçe SESSİZCE eskir. Çözüm de aynı: TÜRETME.
# Jetonlar artık obs.py'den okunur — yeni bir ALARM_ sabiti bu filtreye kendiliğinden girer.
# ==============================================================================================
set -euo pipefail
: "${PROJECT_ID:?set PROJECT_ID}"
: "${ALERT_EMAIL:?set ALERT_EMAIL for the notification channel}"

# Jeton listesi TEK KAYNAKTAN: meridian/obs.py. Elle kopyalanmaz.
PY="${PY:-.venv/bin/python}"
TOKENS=$("$PY" -c 'from meridian import obs; print(" ".join(sorted(obs.NOTIFY_TOKENS)))')
if [ -z "${TOKENS}" ]; then
  echo "HATA: obs.NOTIFY_TOKENS boş okundu — filtre üretilmedi (elle listeye DÜŞMEYİN)." >&2
  exit 1
fi
echo "obs.py'den türetilen jetonlar: ${TOKENS}"

echo "Creating email notification channel for ${ALERT_EMAIL}…"
CH=$(gcloud beta monitoring channels create \
  --display-name "Meridian ops" --type email \
  --channel-labels="email_address=${ALERT_EMAIL}" \
  --format="value(name)")

# Her jeton ham metin olarak log satırında görünür (obs.alarm jetonu mesaja gömer), bu yüzden
# düz substring filtresi eşleşir.
OR_FILTER=""
for t in ${TOKENS}; do
  [ -n "${OR_FILTER}" ] && OR_FILTER="${OR_FILTER} OR "
  OR_FILTER="${OR_FILTER}textPayload:\"${t}\""
done

echo "Log-based metrikleri şu filtrelerle kurun:"
cat <<EOF
  # Nabız ölümü ayrı bir metrik olarak kalır (en sık kurulan tek-jeton politikası):
  gcloud logging metrics create meridian_stale --description="stale heartbeat" \\
    --log-filter='resource.type="gce_instance" AND textPayload:"HEARTBEAT_STALE"'

  # TÜM alarm jetonları (obs.NOTIFY_TOKENS'tan türetildi — elle güncellenmez):
  gcloud logging metrics create meridian_alarms --description="all ALARM_ tokens" \\
    --log-filter='resource.type="gce_instance" AND (${OR_FILTER})'

# then: gcloud alpha monitoring policies create ... --notification-channels=${CH}
EOF
echo "Channel: ${CH}"
