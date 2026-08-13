#!/usr/bin/env bash
# deploy.sh — Meridian'ı Oracle Cloud Always Free Ampere A1 (aarch64 Ubuntu) üzerine kurar.
# A1 ÜZERİNDE, repo /opt/meridian'a kopyalandıktan SONRA çalıştır. Idempotent: tekrar koşulabilir.
#
#   ssh ubuntu@<A1-IP>
#   sudo mkdir -p /opt/meridian && sudo chown ubuntu:ubuntu /opt/meridian
#   # (yerelden) rsync -az --exclude .venv ./ ubuntu@<A1-IP>:/opt/meridian/
#   cd /opt/meridian && bash deploy/oracle-a1/deploy.sh
#
# Not: normalde bu betiği ELLE koşman gerekmez — yereldeki cutover.sh (aynı dizinde) durdurma +
# rsync + bu betik + token + doğrulama sırasını tek komutta yürütür.
set -euo pipefail
cd "$(dirname "$0")/../.."   # repo kökü (/opt/meridian)
REPO="$(pwd)"
echo "== Meridian A1 kurulumu · $REPO =="

# 1) sistem paketleri
#    redis-server ŞART, opsiyonel değil: meridian/hotstate.py sıcak durumu (heartbeat, mrd:bars ring)
#    Redis'te tutar ve meridian/barsarchive.py o ring'i okuyup diske arşivler. Redis yoksa arşivci
#    her turda "REDIS YOK" deyip boşa döner, dakikalık barlar TEMELLİ kaybolur.
#    Ubuntu paketi VARSAYILAN OLARAK yalnız 127.0.0.1 dinler (/etc/redis/redis.conf → `bind 127.0.0.1
#    -::1`). BU AYARA DOKUNMA: A1'in public IP'sinde parolasız Redis açmak anlamına gelir.
if command -v apt-get >/dev/null; then
  sudo apt-get update -qq
  sudo apt-get install -y -qq curl ca-certificates rsync redis-server >/dev/null
  sudo systemctl enable --now redis-server
  echo "-- redis: $(redis-cli ping 2>&1 | head -1)   (dinlenen adres: $(redis-cli CONFIG GET bind 2>/dev/null | tail -1))"
fi

# 2) uv (aarch64 Linux) — Meridian venv'i uv.lock'tan bire bir kurulur (derleme yok, hepsi wheel)
if ! command -v uv >/dev/null 2>&1; then
  echo "-- uv kuruluyor"
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
fi
export PATH="$HOME/.local/bin:$PATH"
echo "uv: $(uv --version)"

# 3) Meridian bağımlılıkları (uv.lock → tekrarlanabilir; aarch64 wheel'leri)
echo "-- uv sync (bağımlılıklar)"
uv sync --frozen 2>/dev/null || uv sync
uv run python -c "import meridian.api, pandas, numpy, fastapi; print('meridian import OK')"

# 4) state/ var mı? (yoksa uyar — operatör yerelden rsync'lemeli)
if [ ! -f state/portfolio.json ] && [ ! -s state/meridian.db ]; then
  echo "!! state/portfolio.json (ya da state/meridian.db) yok — yereldeki state/ dizinini rsync'le:"
  echo "   rsync -az ./state/ ubuntu@<A1-IP>:/opt/meridian/state/"
fi
# sırlar 0600 (rsync -a izinleri taşır ama garanti altına al; dosya yoksa atla — SESSİZ DEĞİL)
for f in state/secrets.json state/auth.json; do
  if [ -f "$f" ]; then chmod 600 "$f"; echo "-- izin 0600: $f"; else echo "-- $f YOK (panodan girilecek)"; fi
done

# 5) hermes-agent (ajan beyni). Saf Python paketi → aarch64 Linux'a kurulabilir.
#    meridian/hermes.py:_hermes_bin() sırası: HERMES_LOCAL_BIN → PATH → ~/.hermes/bin/hermes →
#    ~/.local/bin/hermes. Resmi installer bunlardan birine kurar; meridian.service'in PATH'i
#    /home/ubuntu/.local/bin'i zaten içeriyor.
#    KURULUM BAŞARISIZSA YIKMIYORUZ: Meridian ajan yoksa deterministik öneriye düşer — döngü/kapı/
#    işlem çalışmaya devam eder (RUNBOOK Bölüm D). Ama sessizce geçmiyoruz (YASA 4).
HERMES_BIN=""
for c in "$(command -v hermes || true)" "$HOME/.hermes/bin/hermes" "$HOME/.local/bin/hermes"; do
  if [ -n "$c" ] && [ -x "$c" ]; then HERMES_BIN="$c"; break; fi
done
if [ -n "$HERMES_BIN" ]; then
  echo "-- hermes zaten kurulu: $HERMES_BIN"
else
  echo "-- hermes-agent yok → resmi installer koşuluyor (aarch64 Linux destekli)"
  if curl -fsSL https://hermes-agent.nousresearch.com/install.sh | sh; then
    export PATH="$HOME/.local/bin:$HOME/.hermes/bin:$PATH"
    for c in "$(command -v hermes || true)" "$HOME/.hermes/bin/hermes" "$HOME/.local/bin/hermes"; do
      if [ -n "$c" ] && [ -x "$c" ]; then HERMES_BIN="$c"; break; fi
    done
  else
    echo "!! HERMES KURULUMU BAŞARISIZ — kurulum durdurulmuyor, ama beyin zinciri EKSİK koşacak."
    echo "   Etki: nous bacağı ikili olmadan çalışmaz (state/secrets.json'da NOUS_API_KEY de YOK)."
    echo "   Kalan yol: gemini bacağı (GEMINI_API_KEY) veya Ayarlar'dan NOUS_ENDPOINT=<portal-url>."
    echo "   Hiçbiri yoksa Meridian deterministik öneriye düşer (döngü durmaz)."
  fi
fi
if [ -n "$HERMES_BIN" ]; then
  # DOĞRULAMA: ikilinin varlığı çalıştığını kanıtlamaz (yarım kurulum/venv kırığı olabilir).
  if "$HERMES_BIN" --version 2>&1 | head -1; then :; else
    echo "!! $HERMES_BIN çalışmıyor (--version başarısız) — beyin zinciri nous bacağı DEVRE DIŞI sayılmalı"
  fi
fi

# 6) systemd birimleri (yerli, docker yok)
echo "-- systemd birimleri"
sudo cp deploy/oracle-a1/meridian.service            /etc/systemd/system/meridian.service
sudo cp deploy/oracle-a1/meridian-barsarchive.service /etc/systemd/system/meridian-barsarchive.service
sudo cp deploy/oracle-a1/meridian-backup.service     /etc/systemd/system/meridian-backup.service
sudo cp deploy/oracle-a1/meridian-backup.timer       /etc/systemd/system/meridian-backup.timer
# OnFailure hedefi: meridian.service ölürse operatöre haber verir. enable EDİLMEZ (oneshot,
# yalnız OnFailure tetikler). Kanal kurulu değilse birim no-op'tur ve nedenini journal'a yazar.
sudo cp deploy/oracle-a1/meridian-fail-notify.service /etc/systemd/system/meridian-fail-notify.service
# ASILI-TİCK BEKÇİSİ (2026-08-02 küçük-kuyruk turu — BU ADIM EKSİKTİ).
# Bekçi 2026-07-31'de CANLIDA elle kurulmuştu ve depoda hiç yoktu; dolayısıyla bu betik onu
# KURMUYORDU. Sonucu: taze bir kurulum ya da `cutover.sh` (adım 4 bu betiği çağırır) panoyu
# asılı-tick korumasız canlıya çıkarırdı — "canlılık != ilerleme" vakası (2026-07-30 21:14→22:27,
# ölçülen sessizlik 73,1 dk) hiçbir bekçiye çarpmadan tekrarlanabilirdi.
sudo cp deploy/oracle-a1/meridian-tick-watchdog.service /etc/systemd/system/meridian-tick-watchdog.service
sudo cp deploy/oracle-a1/meridian-tick-watchdog.timer   /etc/systemd/system/meridian-tick-watchdog.timer
# SPRINT ŞABLON BİRİMİ (v241, 2026-08-13 — tick-watchdog'un AYNI DERSİ, bu kez baştan uygulandı).
# Öğrenme sprinti 2026-08-13'e dek worker'ın çocuğu olarak doğuyordu (`sprint.py` Popen) ve systemd
# varsayılan `KillMode=control-group` yüzünden HER `systemctl restart meridian` onu biçiyordu —
# o gün üç sprint tam bu şekilde öldü (41, 113 ve 1 adımda; üçünün de tetiği bir restart'tı).
# Kendi birimi olduğu için artık worker'ın cgroup'unda DEĞİL; birim dosyasında `PartOf`/`BindsTo`/
# `After=meridian.service` BİLEREK YOK. `enable` EDİLMEZ (şablon + `[Install]` yok): örnekleri
# `sprint.start()` sid ile tetikler. Kurulmazsa sistem bozulmaz — kod `sprint_systemd_yok` olayıyla
# eski Popen yoluna GÖRÜNÜR şekilde düşer (`kosum_yolu` damgası), ama o yolda sorun geri gelir.
sudo cp deploy/oracle-a1/meridian-sprint@.service       /etc/systemd/system/meridian-sprint@.service
# POLKIT KURALI (v241, 2026-08-13 — CANLI ÖLÇÜMÜN sonucu): worker `NoNewPrivileges=true` altında
# koştuğu için `sudo` (setuid) root'a yükselemiyor ve sprint birimini tetikleyemiyordu. Bu kural
# yalnız `ubuntu` kullanıcısına, yalnız `meridian-sprint@*` birimleri için manage-units izni verir —
# `NoNewPrivileges=no` tavizini VERMEDEN (H3 koruma kalemi yerinde kalır). Eşlik eden satır:
# meridian.service `Environment=MERIDIAN_SPRINT_SYSTEMCTL=/usr/bin/systemctl` (tetiği sudo'suz yapar).
sudo cp deploy/oracle-a1/50-meridian-sprint.rules       /etc/polkit-1/rules.d/50-meridian-sprint.rules
sudo systemctl restart polkit
# HERMES BRİFİNGİ (SOUL.md) — v242, 2026-08-13. tick-watchdog ve polkit ile AYNI SINIF: dosya
# CANLIDA elle kurulmuştu ve depoda YOKTU, yani taze bir kurulum beyni brifingsiz açardı (ya da
# eski bir kopya elde kalırdı). Brifing ölçülebilir davranış üretir: 2026-08-13'te içindeki
# "araç çağrısı … yok" satırı ÇIKTI BİÇİMİNE daraltıldı çünkü bir üstteki maddenin ("skill'in
# SKILL.md'sini oku") tek uygulama yolunu yasaklıyordu — ölçüm: 1.113 oturumda %1,1 skill aracı
# çağrısı (docs/DENETIM-SKILL-CAGRI-IZI-2026-08-13.md). ÜZERİNE YAZMAZ: varsa yedeklenir.
if [ -f deploy/hermes/SOUL.md ]; then
  mkdir -p "$HOME/.hermes"
  [ -f "$HOME/.hermes/SOUL.md" ] && cp "$HOME/.hermes/SOUL.md" "$HOME/.hermes/SOUL.md.bak-$(date -u +%Y%m%d%H%M)"
  cp deploy/hermes/SOUL.md "$HOME/.hermes/SOUL.md"
  echo "-- hermes brifingi kuruldu: ~/.hermes/SOUL.md"
fi
# ÇALIŞTIRMA BİTİ: rsync tabanlı dağıtım (dagit.sh / push_code_a1.sh) izinleri her zaman
# taşımayabilir; `Type=oneshot` bir ExecStart çalıştırılamazsa birim 203/EXEC ile düşer ve bekçi
# SESSİZCE ölür. Her koşuda garanti altına alınır (`.dash.env` izin sabitlemesiyle aynı sınıf).
sudo chmod +x deploy/oracle-a1/tick_watchdog.sh
# PANO TOKEN'I — BİRİMDE DEĞİL, 0600'lük /opt/meridian/.dash.env'te (H3 tur-1/2):
# meridian.service onu `EnvironmentFile=-/opt/meridian/.dash.env` ile okur; birim dosyası 0644'tür,
# sır oraya YAZILMAZ. Dosya SUNUCUDA üretilir, dağıtımla TAŞINMAZ (dagit.sh rsync'i .dash.env'i
# bilerek dışlar — 2026-08-01 vakası: --delete A1'dekini silmişti). Eski `grep CHANGEME` bekçisi
# ÖLDÜ: H3 tur-2 placeholder'ı birimden çıkarınca desen-bağımlı bekçi SESSİZ NO-OP oldu ve taze
# kurulum token'sız kalırdı — o yüzden desen değil DOSYANIN KENDİSİ ölçülür. İDEMPOTENT: dolu
# dosyaya DOKUNULMAZ; üzerine yazmak operatörün canlı token'ını habersiz döndürmek olurdu.
if [ ! -s /opt/meridian/.dash.env ]; then
  echo "-- pano token'ı üretiliyor → /opt/meridian/.dash.env (openssl rand -hex 24)"
  printf 'MERIDIAN_DASH_TOKEN=%s\n' "$(openssl rand -hex 24)" | sudo tee /opt/meridian/.dash.env >/dev/null
else
  echo "-- /opt/meridian/.dash.env zaten dolu — DOKUNULMADI (mevcut token korunuyor)"
fi
# izinler her koşuda garanti altına alınır (yukarıdaki secrets/auth chmod'larıyla aynı sınıf;
# içeriğe dokunmaz)
sudo chown ubuntu:ubuntu /opt/meridian/.dash.env
sudo chmod 600 /opt/meridian/.dash.env
# DOĞRULAMA (sed-vakası dersi: adımın gerçekleştiğini dosya söyler): dolu + 0600, değilse DUR —
# token'sız devam etmek panoyu parolasız canlıya çıkarmak olurdu
DASH_IZIN="$(stat -c '%a' /opt/meridian/.dash.env 2>/dev/null || echo YOK)"
if [ ! -s /opt/meridian/.dash.env ] || [ "$DASH_IZIN" != "600" ]; then
  echo "!! /opt/meridian/.dash.env DOĞRULANAMADI (izin=$DASH_IZIN) — pano token'sız kalırdı"
  exit 1
fi
echo "-- pano token'ı: /opt/meridian/.dash.env dolu + 0600 ✓"
mkdir -p /home/ubuntu/backups     # yedek hedefi — timer ilk atışta var olmalı
sudo systemctl daemon-reload
sudo systemctl enable meridian meridian-barsarchive
sudo systemctl enable --now meridian-backup.timer   # timer şimdi başlar; service'i o tetikler
sudo systemctl enable --now meridian-tick-watchdog.timer

# BEKÇİ KURULUM DOĞRULAMASI — "kurulu != çalışır" (fail-notify dersi, 2026-07-30: birim iki gün
# kuruluydu ve ilk test-ateşlemede IndentationError verdi). Burada ÜÇ ayrı gerçek ölçülür ve
# hiçbiri diğerinin yerine geçmez: (a) ExecStart hedefi gerçekten ÇALIŞTIRILABİLİR mi, (b) timer
# gerçekten AKTİF mi, (c) betik bir kez KOŞTURULDUĞUNDA beklenen satırı basıyor mu.
# (c) BİLEREK VAR: eski gömülü sürüm systemd `$` ikamesi yüzünden hiçbir zaman restart edemiyordu
# ve bunu YALNIZ çıktısına bakınca ("[tick-watchdog] ilerleme var (s)" — boş `${YAS}`) anlaşılıyordu.
# Desen değil DURUM ölçülür: hüküm satırı yaşı SAYIYLA basmalı.
if [ ! -x /opt/meridian/deploy/oracle-a1/tick_watchdog.sh ]; then
  echo "!! tick-watchdog betiği çalıştırılabilir değil — bekçi 203/EXEC ile sessizce ölürdü"; exit 1
fi
sudo systemctl start meridian-tick-watchdog.service || true
TICK_CIKTI="$(journalctl -u meridian-tick-watchdog.service -n 20 --no-pager 2>/dev/null | grep -o '\[tick-watchdog\].*' | tail -1)"
TICK_TIMER="$(systemctl is-active meridian-tick-watchdog.timer 2>&1 || true)"
echo "-- tick-watchdog: timer=$TICK_TIMER · son satır: ${TICK_CIKTI:-(YOK)}"
if [ "$TICK_TIMER" != "active" ]; then
  echo "!! meridian-tick-watchdog.timer AKTİF DEĞİL — asılı-tick koruması yok"; exit 1
fi
case "$TICK_CIKTI" in
  *"ilerleme var ("[0-9]*|*"bayat"*|*"ÖLÇÜLEMEDİ"*|*"YAS lütfu"*) : ;;
  *) echo "!! tick-watchdog beklenen hüküm satırını basmadı (systemd \$ ikamesi sınıfı?) — çıktı: ${TICK_CIKTI:-(YOK)}"; exit 1 ;;
esac

# 7) tohum + başlat
#    KORUMA (serve.sh:16 ile BİREBİR): dolu bir state üzerine replay KOŞULMAZ. Eski sürüm bu kontrolü
#    taşımıyordu → rsync'lenmiş CANLI state'in üstüne 2022→bugün replay koşabiliyordu.
#    SQLite GEÇİŞİ SONRASI TUZAK KAPALI (WP-H/H9, 2026-07-31): migrasyon sonrası defter
#    `state/meridian.db` içindedir ve `state/trades.jsonl` `.migrated` ekiyle durur — tek başına
#    `-s state/trades.jsonl` kontrolü DOLU defteri BOŞ görüp CANLI defterin üstüne replay koşardı.
if [ ! -s state/trades.jsonl ] && [ ! -s state/meridian.db ]; then
  echo "-- TOHUM: state/trades.jsonl boş/yok ve state/meridian.db yok → geçmişten tohumlanıyor (2022 → bugün)"
  uv run python -m meridian.run --dry-run --replay 2022-01-01:"$(date +%F)" \
    || echo "   (tohum başarısız — canlı turlarla devam edilecek; sebebi yukarıdaki çıktıda)"
elif [ -s state/trades.jsonl ]; then
  echo "-- TOHUM ATLANDI: state/trades.jsonl dolu ($(wc -l < state/trades.jsonl) satır) — taşınan canlı state korunuyor"
else
  echo "-- TOHUM ATLANDI: defter SQLite'ta (state/meridian.db) — taşınan canlı state korunuyor"
  uv run python -m meridian.dbmigrate --durum || true
fi
sudo systemctl restart meridian meridian-barsarchive
sleep 8

# 8) doğrulama
echo "== durum =="
printf 'redis-cli ping        : %s\n' "$(redis-cli ping 2>&1 | head -1)"
for u in redis-server meridian meridian-barsarchive; do
  # is-active aktif değilken 3 döner; set -e altında betiği düşürmesin — durum ZATEN basılıyor (YASA 4)
  printf '%-22s: %s\n' "$u" "$(systemctl is-active "$u" 2>&1 || true)"
done
systemctl --no-pager status meridian | head -6 || true   # status aktif değilken 3 döner; üstteki is-active satırı gerçeği söylüyor
echo "-- zamanlayıcılar --"
systemctl list-timers --no-pager 'meridian-*' || true    # timer hiç yoksa boş liste + 1 döner; üstte enable edildi
curl -s -o /dev/null -w "healthz  : %{http_code}  (200=taze, 503=bayat ama süreç canlı)\n" http://127.0.0.1:8080/healthz || true
curl -s -o /dev/null -w "api/today: %{http_code}\n" http://127.0.0.1:8080/api/today || true
echo ""
echo "PANO: SSH tünel öner →  ssh -L 8080:127.0.0.1:8080 ubuntu@<A1-IP>  → tarayıcıda http://localhost:8080"
echo "loglar:  journalctl -u meridian -f   ·   journalctl -u meridian-barsarchive -f"
