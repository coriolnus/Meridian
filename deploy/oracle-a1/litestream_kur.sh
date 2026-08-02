#!/usr/bin/env bash
# litestream_kur.sh — Litestream'i A1'e SÜRÜM-SABİTLİ + SHA256-KAPILI kurar (WP-H / H10 aşama-1).
#
# NEREDE KOŞAR: **A1'de**, /opt/meridian içinden. Mac'ten değil (ikili aarch64-Linux'tur).
# NE ZAMAN KOŞAR: bakım penceresinde, RUNBOOK "Bölüm B4" prosedürünün adımı olarak. Bu betiği bir
# AJAN KOŞMAZ — canlı defterin şemasına dokunan ilk `start`ı operatör açar (aşağıda `--baslat`).
#
# İDEMPOTENT: iki kez koşmak hiçbir şeyi bozmaz. Doğru sürüm zaten kuruluysa indirme ATLANIR;
# yapılandırma/birim dosyaları AYNIYSA "değişmedi" der ve dokunmaz; `enable` zaten etkinse geçer.
#
# ==================================================================================================
# TEDARİK-ZİNCİRİ KAPISI (H2 ruhu — `uv audit` neyse bu da o)
# ==================================================================================================
# Bu betik depo dışından bir İKİLİ indiriyor: Python paketlerine uyguladığımız kapıyı ona
# uygulaMAMAK, kapıyı en zayıf halkadan delmek olurdu. Üç kilit:
#   1. SÜRÜM SABİT (`LS_SURUM`) — "latest" YASAK. `latest`, dünkü denetimden geçmemiş bir ikiliyi
#      yarınki koşumda sessizce canlıya sokar.
#   2. SHA256 SABİT (`LS_SHA256`) — yayıncının `checksums.txt`inden 2026-08-02'de alındı. İndirme
#      ile eşleşmezse betik DURUR ve dosyayı SİLER; "belki ağ bozdu" diye tekrar denemez.
#   3. MİMARİ KAPISI — `uname -m` aarch64 değilse durur (yanlış ikili "çalışmıyor" diye değil,
#      "exec format error" diye ölürdü ve bunu birim journal'ında aramak saatler yerdi).
# SHA256 YENİLEME (sürüm yükseltirken): yayıncının checksums dosyasından okunur —
#   curl -sSL https://github.com/benbjohnson/litestream/releases/download/v<SÜRÜM>/checksums.txt
# Sabit ELLE güncellenir ve turun commit'ine girer; betik onu İNTERNETTEN TAZELEMEZ (tazeleseydi
# kapı kapı olmaktan çıkar, "indirdiğimi indirdiğimle doğruladım" totolojisine dönerdi).
set -euo pipefail

LS_SURUM="0.5.15"
LS_SHA256="2b7d6c6b8cfefab545e632bf8a77b5d1e1a95ff9fd0d2754a67c8a046391125c"
LS_ARSIV="litestream-${LS_SURUM}-linux-arm64.tar.gz"
LS_URL="https://github.com/benbjohnson/litestream/releases/download/v${LS_SURUM}/${LS_ARSIV}"

REPO="${MERIDIAN_REPO:-/opt/meridian}"
IKILI="/usr/local/bin/litestream"
YAPILANDIRMA="/etc/litestream.yml"
BIRIM="/etc/systemd/system/meridian-litestream.service"
REPLICA_DIR="/home/ubuntu/replica"
META_DIR="/var/lib/litestream"
SAHIP="ubuntu:ubuntu"

BASLAT=0
for a in "$@"; do
  case "$a" in
    --baslat) BASLAT=1 ;;
    -h|--yardim|--help)
      echo "kullanım: $0 [--baslat]"
      echo "  (bayraksız) : ikili+yapılandırma+birim kurulur ve ENABLE edilir — BAŞLATILMAZ"
      echo "  --baslat    : ayrıca 'systemctl start meridian-litestream' koşar"
      exit 0 ;;
    *) echo "!! bilinmeyen argüman: $a (bkz. --yardim)"; exit 2 ;;
  esac
done

adim() { printf '\n== %s\n' "$*"; }
die()  { printf '!! %s\n' "$*" >&2; exit 1; }

# ==================================================================================================
# [0] ÖN KOŞULLAR — yanlış makinede yarım kurulum bırakmaktansa hiç başlamamak
# ==================================================================================================
adim "[0] ön koşullar"
MIMARI="$(uname -m)"
[ "$MIMARI" = "aarch64" ] || die "mimari $MIMARI — bu betik aarch64 (Oracle A1) içindir; sabitlenen arşiv linux-arm64"
[ "$(uname -s)" = "Linux" ] || die "işletim sistemi $(uname -s) — bu betik A1'de (Linux) koşar, Mac'te DEĞİL"
[ -d "$REPO/deploy/oracle-a1" ] || die "$REPO/deploy/oracle-a1 yok — depo A1'e taşınmamış (dagit/rsync önce)"
[ -f "$REPO/deploy/oracle-a1/litestream.yml" ] || die "kaynak yapılandırma yok: $REPO/deploy/oracle-a1/litestream.yml"
[ -f "$REPO/deploy/oracle-a1/meridian-litestream.service" ] || die "kaynak birim yok: $REPO/deploy/oracle-a1/meridian-litestream.service"
command -v sha256sum >/dev/null || die "sha256sum yok — doğrulama kapısı olmadan kurulum YAPILMAZ"
command -v curl >/dev/null || die "curl yok"
sudo -n true 2>/dev/null || die "parolasız sudo yok — betik /usr/local/bin ve /etc altına yazar"
echo "   ✓ aarch64 Linux · depo $REPO · sudo hazır"

# DEFTER UYARISI (bilgi, kapı değil): DB yoksa litestream onu YARATMAZ (db.go:1030) — ama kurulumun
# hedefsiz olduğunu operatör bilmeli.
if [ -s "$REPO/state/meridian.db" ]; then
  echo "   ✓ defter yerinde: $(stat -c '%s bayt · %y' "$REPO/state/meridian.db")"
else
  echo "   ⚠ $REPO/state/meridian.db YOK ya da boş — litestream onu YARATMAZ, boşta bekler (MERIDIAN_DB=off mu?)"
fi

# ==================================================================================================
# [1] İKİLİ — sürüm-sabitli indirme + sha256 kapısı (İDEMPOTENT)
# ==================================================================================================
adim "[1] litestream ikilisi (sabit sürüm $LS_SURUM)"
KURULU_SURUM=""
if [ -x "$IKILI" ]; then
  KURULU_SURUM="$("$IKILI" version 2>/dev/null || true)"
fi
if printf '%s' "$KURULU_SURUM" | grep -qF "$LS_SURUM"; then
  echo "   ✓ zaten kurulu: $KURULU_SURUM — indirme ATLANDI (idempotent)"
else
  [ -n "$KURULU_SURUM" ] && echo "   · kurulu sürüm: '$KURULU_SURUM' → sabitlenen $LS_SURUM ile değiştirilecek"
  TMP="$(mktemp -d)"
  # `trap`: sha256 tutmazsa da, indirme yarıda kalırsa da geçici dizin ARKADA KALMAZ. İndirilen
  # ikili doğrulanana kadar /usr/local/bin'e YAKLAŞMAZ.
  trap 'rm -rf "$TMP"' EXIT
  echo "   · indiriliyor: $LS_URL"
  curl -fsSL --max-time 300 -o "$TMP/$LS_ARSIV" "$LS_URL" || die "indirme başarısız: $LS_URL"

  echo "   · sha256 doğrulanıyor"
  printf '%s  %s\n' "$LS_SHA256" "$TMP/$LS_ARSIV" > "$TMP/beklenen.sha256"
  if sha256sum -c "$TMP/beklenen.sha256" >/dev/null 2>&1; then
    echo "   ✓ sha256 EŞLEŞTİ ($LS_SHA256)"
  else
    GERCEK="$(sha256sum "$TMP/$LS_ARSIV" | cut -d' ' -f1)"
    rm -f "$TMP/$LS_ARSIV"
    die "SHA256 TUTMADI — arşiv SİLİNDİ. beklenen=$LS_SHA256 gerçek=$GERCEK (tekrar denenmez: bu bir ağ hatası değil, tedarik-zinciri sinyalidir)"
  fi

  tar -xzf "$TMP/$LS_ARSIV" -C "$TMP" || die "arşiv açılamadı"
  [ -f "$TMP/litestream" ] || die "arşivde 'litestream' ikilisi yok — yayın düzeni değişmiş, sabitler gözden geçirilmeli"
  sudo install -o root -g root -m 0755 "$TMP/litestream" "$IKILI" || die "install $IKILI"
  rm -rf "$TMP"; trap - EXIT
  echo "   ✓ kuruldu: $IKILI → $("$IKILI" version 2>&1 | head -1)"
fi

# ==================================================================================================
# [2] DİZİNLER — birimin ReadWritePaths'i bunları ŞART koşar (`-` öneki YOK: yoklarsa birim açılmaz)
# ==================================================================================================
adim "[2] replica + meta dizinleri"
for d in "$REPLICA_DIR" "$META_DIR"; do
  sudo mkdir -p "$d"
  sudo chown "$SAHIP" "$d"
  sudo chmod 750 "$d"
  echo "   ✓ $d ($(stat -c '%U:%G %a' "$d"))"
done
# DÜRÜST SINIR — TEK DİSK: replica, çoğaltılan defterle AYNI blok cihazdadır (A1'de ikinci disk YOK).
echo "   ⚠ aynı disk: $(df -h --output=source,avail "$REPLICA_DIR" | tail -1 | tr -s ' ') boş — medya arızası KAPSAM DIŞI (aşama-2 bucket)"

# ==================================================================================================
# [3] YAPILANDIRMA + BİRİM — değişmediyse DOKUNULMAZ (idempotent + gürültüsüz)
# ==================================================================================================
adim "[3] /etc/litestream.yml + systemd birimi"
kur_dosya() {  # $1=kaynak $2=hedef $3=mod
  if [ -f "$2" ] && cmp -s "$1" "$2"; then
    echo "   · $2 AYNI — dokunulmadı"
    return 1
  fi
  sudo install -o root -g root -m "$3" "$1" "$2"
  echo "   ✓ $2 güncellendi"
  return 0
}
YENIDEN_YUKLE=0
kur_dosya "$REPO/deploy/oracle-a1/litestream.yml" "$YAPILANDIRMA" 0644 || true
kur_dosya "$REPO/deploy/oracle-a1/meridian-litestream.service" "$BIRIM" 0644 && YENIDEN_YUKLE=1 || true

# YAPILANDIRMA KURU DOĞRULAMASI: `databases` YALNIZ config'i ayrıştırır ve DB nesnelerini kurar —
# hiçbir DB AÇMAZ (cmd/litestream/databases.go: NewDBFromConfig, Open YOK). Yani bu satır canlı
# deftere DOKUNMAZ; bozuk YAML'ı `start`tan ÖNCE yakalar.
adim "[3b] yapılandırma kuru doğrulaması (DB AÇILMAZ)"
"$IKILI" databases -config "$YAPILANDIRMA" || die "yapılandırma ayrıştırılamadı — $YAPILANDIRMA"

# ==================================================================================================
# [4] systemd — daemon-reload + enable (BAŞLATMA AYRI KARARDIR)
# ==================================================================================================
adim "[4] systemd"
if [ "$YENIDEN_YUKLE" = "1" ]; then
  sudo systemctl daemon-reload && echo "   ✓ daemon-reload"
else
  # Birim değişmedi ama ilk kurulumda da buraya düşebiliriz (aynı içerik, zaten kurulu) — reload
  # ucuz ve zararsız; ATLAMAK, "kurdum ama systemd görmedi" sınıfını açık bırakırdı.
  sudo systemctl daemon-reload && echo "   ✓ daemon-reload (birim değişmemişti, yine de yapıldı)"
fi
# `systemctl enable` idempotenttir ve zaten etkinken de 0 döner — o yüzden DURUM ÖNCE OKUNUR.
# (Çıkış kodunu "yapıldı mı" sanmak, betiği her koşuda "✓ enable" diye yalan söyletirdi.)
if [ "$(systemctl is-enabled meridian-litestream 2>/dev/null || true)" = "enabled" ]; then
  echo "   · enable zaten yapılmış"
else
  sudo systemctl enable meridian-litestream >/dev/null && echo "   ✓ enable"
fi

if [ "$BASLAT" = "1" ]; then
  adim "[5] BAŞLATMA (--baslat verildi)"
  # ⚠ İLK START GERİ ALINMASI EN ZOR ADIMDIR: litestream canlı deftere `_litestream_seq` +
  # `_litestream_lock` tablolarını EKLER (db.go:1083/1089). Geri alma RUNBOOK B4 adım 8'de.
  sudo systemctl start meridian-litestream
  sleep 5
  systemctl is-active --quiet meridian-litestream \
    && echo "   ✓ aktif — ama 'aktif' ÇOĞALTIYOR demek DEĞİLDİR; ölçüsü replica dosyalarının yaşıdır (RUNBOOK B4/5c)" \
    || die "birim aktif değil — journalctl -u meridian-litestream -n 50"
else
  adim "[5] BAŞLATILMADI (bilinçli)"
  echo "   İlk start canlı defterin ŞEMASINA iki tablo ekler. Operatör kalemi:"
  echo "     sudo systemctl start meridian-litestream"
  echo "   ya da bu betiği --baslat ile tekrar koş."
fi

adim "BİTTİ"
echo "sonraki: RUNBOOK 'Bölüm B4' adım 5 (doğrulama) + adım 6 (restore tatbikatı)"
