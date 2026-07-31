#!/usr/bin/env bash
# bakim_h9.sh — H9 SQLite canlı geçişi + H3 sertleştirme + yedek-unit düzeltmesi + token rotasyonu
# TEK BAKIM PENCERESİ. Ajan runbook'u (12 adım) + Rol-1 eklemeleri. Her adım doğrulamalı;
# migrasyon paritesi tutmazsa TOPTAN geri alınır ve servisler DOSYA arka ucuyla yeniden başlar.
# Kullanım: ./bakim_h9.sh          (uçtan uca; ~10-20 dk)
set -uo pipefail
KEY="$HOME/.ssh/oci-a1.key"; IP="130.61.126.87"; REPO="$HOME/AI-Trading"
SSH=(ssh -i "$KEY" -o ConnectTimeout=15 ubuntu@"$IP")
RSYNC_EXC=(--exclude '.venv' --exclude '.git' --exclude 'state' --exclude 'backups' --exclude 'scratchpad' --exclude '__pycache__' --exclude '.claude')
die(){ echo "!! $*"; exit 1; }

echo "=== [0] yerel kapılar ==="
cd "$REPO"
[[ -z "$(git status --porcelain)" ]] || die "çalışma ağacı kirli — önce commit"
echo "  ✓ ağaç temiz · dağıtılacak: $(git rev-parse --short HEAD)"

echo "=== [1] ledgerstamp (SIRA BAĞLAYICI — migrasyondan önce, mtime kanıtı) ==="
"${SSH[@]}" 'export PATH="$HOME/.local/bin:$PATH"; cd /opt/meridian && uv run python -m meridian.ledgerstamp --uygula 2>&1 | tail -3' || die "ledgerstamp"

echo "=== [2] kod rsync (dry-run özeti + gerçek) ==="
rsync -azin --delete "${RSYNC_EXC[@]}" -e "ssh -i $KEY" "$REPO"/ ubuntu@"$IP":/opt/meridian/ | head -25
rsync -az  --delete "${RSYNC_EXC[@]}" -e "ssh -i $KEY" "$REPO"/ ubuntu@"$IP":/opt/meridian/ || die "rsync"
"${SSH[@]}" 'export PATH="$HOME/.local/bin:$PATH"; cd /opt/meridian && uv sync --frozen --extra dev -q && echo "  ✓ uv sync"' || die "uv sync"

echo "=== [3] DB henüz pasif mi? ==="
"${SSH[@]}" 'export PATH="$HOME/.local/bin:$PATH"; cd /opt/meridian && uv run python -m meridian.dbmigrate --durum 2>&1 | head -4'

echo "=== [4] BAKIM PENCERESİ: durdur + keepalive ==="
"${SSH[@]}" 'sudo systemctl stop meridian meridian-barsarchive && rm -f /opt/meridian/state/keepalive.pid && echo "  ✓ durdu"' || die "stop"

echo "=== [5] soğuk yedek (durmuşken → tutarlı) ==="
"${SSH[@]}" 'tar -czf /home/ubuntu/backups/state-premigration-$(date -u +%Y%m%dT%H%M).tar.gz -C /opt/meridian state && ls -lh /home/ubuntu/backups/ | tail -2' || die "soğuk yedek"

echo "=== [6] MİGRASYON: kuru → uygula → durum ==="
"${SSH[@]}" 'export PATH="$HOME/.local/bin:$PATH"; cd /opt/meridian && uv run python -m meridian.dbmigrate 2>&1 | tail -10'
if ! "${SSH[@]}" 'export PATH="$HOME/.local/bin:$PATH"; cd /opt/meridian && uv run python -m meridian.dbmigrate --uygula 2>&1 | tail -10'; then
  echo "!! MİGRASYON BAŞARISIZ — parite korumalı geri alma devrede; servisler DOSYA arka ucuyla başlatılıyor"
  "${SSH[@]}" 'sudo systemctl start meridian meridian-barsarchive'
  die "dbmigrate --uygula (kaynak dosyalar yerinde; incele: dbmigrate --durum)"
fi
"${SSH[@]}" 'export PATH="$HOME/.local/bin:$PATH"; cd /opt/meridian && uv run python -m meridian.dbmigrate --durum 2>&1 | tail -8'

echo "=== [7] uygulamanın gözünden çapraz kontrol (restart ÖNCESİ) ==="
"${SSH[@]}" 'export PATH="$HOME/.local/bin:$PATH"; cd /opt/meridian && uv run python -c "
from meridian import store
print(\"trades:\", len(store.read_jsonl(\"trades.jsonl\")),
      \"cash:\", store.read_json(\"portfolio.json\",{}).get(\"cash\"),
      \"karne:\", store.read_json(\"scoreboard.json\",{}).get(\"current_version\"))"' || die "çapraz kontrol"

echo "=== [8] yedek unit düzeltmesi (tar exit<=1 toleransı + DB tutarlı-kopya) ==="
UNITS="$REPO/deploy/oracle-a1"
scp -q -i "$KEY" "$UNITS/meridian-backup.service" "$UNITS/sertlestirme.conf" ubuntu@"$IP":/tmp/ || die "unit scp"
"${SSH[@]}" 'sudo install -m 644 /tmp/meridian-backup.service /etc/systemd/system/meridian-backup.service && echo "  ✓ yedek unit kuruldu"' || die "yedek unit"

echo "=== [9] H3 sertleştirme drop-in'leri (başlamazsa OTOMATİK geri alınır) ==="
"${SSH[@]}" 'for u in meridian meridian-barsarchive; do sudo mkdir -p /etc/systemd/system/$u.service.d && sudo install -m 644 /tmp/sertlestirme.conf /etc/systemd/system/$u.service.d/sertlestirme.conf || exit 1; done && rm -f /tmp/meridian-backup.service /tmp/sertlestirme.conf && echo "  ✓ drop-in kuruldu"' || die "drop-in"

echo "=== [10] token rotasyonu (unit'ten sırrı çıkar → 0600 dosyaya) ==="
"${SSH[@]}" 'NT=$(openssl rand -hex 24) && printf "MERIDIAN_DASH_TOKEN=%s\n" "$NT" | sudo tee /opt/meridian/.dash.env >/dev/null && sudo chown ubuntu:ubuntu /opt/meridian/.dash.env && sudo chmod 600 /opt/meridian/.dash.env && sudo sed -i "/^Environment=MERIDIAN_DASH_TOKEN=/d" /etc/systemd/system/meridian.service && sudo grep -q "EnvironmentFile=-/opt/meridian/.dash.env" /etc/systemd/system/meridian.service || sudo sed -i "/^\[Service\]/a EnvironmentFile=-/opt/meridian/.dash.env" /etc/systemd/system/meridian.service; echo "  ✓ yeni token: /opt/meridian/.dash.env (0600) — panoya girişte gerekecek"' || die "token"

echo "=== [11] başlat + doğrula (sertleştirme başarısızsa geri al) ==="
if ! "${SSH[@]}" 'sudo systemctl daemon-reload && sudo systemctl start meridian meridian-barsarchive && sleep 10 && systemctl is-active --quiet meridian && systemctl is-active --quiet meridian-barsarchive'; then
  echo "  ⚠ başlamadı — sertleştirme drop-in'leri geri alınıyor"
  "${SSH[@]}" 'sudo rm -f /etc/systemd/system/meridian.service.d/sertlestirme.conf /etc/systemd/system/meridian-barsarchive.service.d/sertlestirme.conf && sudo systemctl daemon-reload && sudo systemctl start meridian meridian-barsarchive && sleep 8 && systemctl is-active meridian meridian-barsarchive'
  echo "  ⚠ SERTLEŞTİRME GERİ ALINDI (H3 yeniden denenecek); migrasyon etkilenmedi"
else
  echo "  ✓ servisler sertleştirilmiş halde ayakta"
fi

echo "=== [12] son doğrulama paketi ==="
"${SSH[@]}" 'export PATH="$HOME/.local/bin:$PATH"; cd /opt/meridian
curl -s -o /dev/null -w "healthz: %{http_code}\n" http://127.0.0.1:8080/healthz
uv run python -m meridian.dbmigrate --durum 2>&1 | grep -E "aktif|kaynak_digest|sema" | head -8
systemctl is-active meridian meridian-barsarchive meridian-tick-watchdog.timer | tr "\n" " "; echo
echo "--- maruziyet skorları (9.2 idi) ---"
systemd-analyze security meridian 2>/dev/null | tail -1
systemd-analyze security meridian-barsarchive 2>/dev/null | tail -1
echo "--- yedek unit provası ---"
sudo systemctl start meridian-backup.service && systemctl show meridian-backup.service -p ExecMainStatus -p Result | tr "\n" " "; echo'
echo "=== BAKIM PENCERESİ TAMAM ==="
