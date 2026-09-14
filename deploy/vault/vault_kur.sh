#!/usr/bin/env bash
# =================================================================================================
# vault_kur.sh — A1'de Vault'u KURAR ve bootstrap eder (TSK-064 Faz-2). DEPODA versiyonlanır.
# =================================================================================================
# KİM KOŞAR: Rol-1, bakım penceresinde, `sudo` ile. OTOMATİK ÇAĞRILMAZ — hiçbir timer, hiçbir
# playbook bu betiği tetiklemez. Ajan bu betiği YAZAR, KOŞTURMAZ (CLAUDE.md §3).
#
# KULLANIM:
#   sudo ./vault_kur.sh --kuru        → hiçbir şey değiştirmez; her adımın NE YAPACAĞINI basar
#   sudo ./vault_kur.sh --uygula      → kurar (her adım idempotent: ikinci koşum no-op'tur)
#   sudo ./vault_kur.sh --uygula --kok-iptal
#                                     → kurulumun sonunda KÖK JETONU İPTAL eder (tasarım §6.2)
#
# `--kuru` ile `--uygula` BİRLİKTE VERİLEMEZ (çıkış 2): biri SORAR, öteki YAPAR ve sessiz bir
# öncelik kuralı operatöre "kurdum" dedirtip hiçbir şey kurmazdı (ölçülmüş ops aracı sınıfı).
# BAYRAKSIZ koşum da çıkış 2'dir: bu betik kip SEÇTİRİR, varsayılan seçmez.
#
# ─────────────────────────────────────────────────────────────────────────────────────────────
# SIR DİSİPLİNİ — BU BETİĞİN EN SERT KURALI
# ─────────────────────────────────────────────────────────────────────────────────────────────
#   · Hiçbir sır DEĞERİ terminale, journal'a, argv'ye ya da bir kabuk DEĞİŞKENİNE girmez.
#   · `operator init` çıktısı BORUYLA python'a akar; python iki dosyayı yazar ve HİÇBİR ŞEY
#     basmaz. Değer kabukta hiç görünmez.
#   · `role-id`/`secret-id`/`admin token` `-field=` ile doğrudan DOSYAYA yönlendirilir; dosya
#     izni `umask 377` ile yaratıldığı ANDA 0400'dür (önce 0644 yaratıp sonra chmod etmek, bir
#     yarış penceresi açardı).
#   · `set -x` YOKTUR ve eklenmemelidir.
#   · Her adımın KANITI sır OLMAYAN alanlardır: `vault status` çıktısı, politika adları, dosya
#     izinleri. "Kurdum" demek yetmez; ne kurulduğu ÖLÇÜLÜR.
#
# ─────────────────────────────────────────────────────────────────────────────────────────────
# SAPMA — /etc/vault DİZİN İZNİ 0750 root:vault (planın 0700 root'undan)
# ─────────────────────────────────────────────────────────────────────────────────────────────
# ÖLÇÜLMÜŞ GEREKLİLİK: `vault.service` User=vault koşar ve süreç KENDİ yapılandırmasını
# (`/etc/vault/vault.hcl`) açar. 0700 root bir dizinde `vault` kullanıcısı dizine GİREMEZ ve
# servis "no such file or directory" ile açılmaz. Çözüm dizini gevşetmek DEĞİL, tam olarak
# gereken kadar açmaktır:
#     /etc/vault            0750 root:vault   → vault kullanıcısı GİREBİLİR, listeleyebilir
#     /etc/vault/vault.hcl  0640 root:vault   → okuyabilir (sır DEĞİL, yapılandırma)
#     ÖTEKİ HER DOSYA       0400 root:root    → vault kullanıcısı OKUYAMAZ
# Yani unseal anahtarı, kök jetonu ve AppRole secret-id'si `vault` kullanıcısına da KAPALIDIR;
# onları yalnız root okur (ve `vault.service`in ExecStartPost'u `+` önekiyle root koşar).
#
# ─────────────────────────────────────────────────────────────────────────────────────────────
# CANARY REÇETESİ (kurulumdan SONRA, Rol-1; tasarım §6.4 — bu betiğin İŞİ DEĞİL, kanıtı)
# ─────────────────────────────────────────────────────────────────────────────────────────────
#   1. Vault'a GERÇEK değer koy (vault_sir_koy.sh), eski dosyaya SAHTE bir değer yaz
#   2. systemctl start vault-agent  → dosya GERÇEK değere dönmeli
#   3. tüketiciyi restart et → 200 (yani dosyayı GERÇEKTEN Agent yazıyor)
#   4. /proc/<pid>/environ içinde sır adı grep → 0 beklenir
#   5. vault status → Sealed=false ; systemctl show meridian -p LoadCredential
set -euo pipefail

VAULT_SURUM="${VAULT_SURUM:-2.1.0}"

# ─────────────────────────────────────────────────────────────────────────────────────────────
# TEDARİK KAPISI — NÖBETÇİ DEĞER (uydurma yasağı)
# ─────────────────────────────────────────────────────────────────────────────────────────────
# Bu sha ÖLÇÜLMEDİ: ajan ağa çıkmaz ve bir sha256 TAHMİN EDİLEMEZ. Nöbetçi değerde duran bu
# sabit, betiği kurulumdan ÖNCE durdurur — yani sürümsüz/doğrulanmamış bir ikili canlıya
# GİREMEZ. Emsal: `deploy/ansible/roles/meridian_a1/defaults/main.yml::uv_installer_sha256`
# (o da nöbetçi değerde doğdu, Rol-1 ölçüp doldurdu).
# DOLDURMA REÇETESİ (Rol-1, A1):
#   curl -fsSL https://releases.hashicorp.com/vault/${VAULT_SURUM}/vault_${VAULT_SURUM}_SHA256SUMS \
#     | grep linux_arm64
# Çıkan sha bu satıra yazılır ve ROADMAP TSK-064 notuna (sürüm + sha) düşülür.
# ÖLÇÜLDÜ 2026-09-14 (Rol-1, A1): releases.hashicorp.com/vault/2.1.0/vault_2.1.0_SHA256SUMS → linux_arm64 satırı;
#   A1'de `sha256sum -c` OK, `vault version` "Vault v2.1.0 (cb6a54fa…)". Sürüm değişirse bu satır ve üstteki VAULT_SURUM birlikte.
VAULT_ZIP_SHA256="${VAULT_ZIP_SHA256:-319b3eb7b0c2ad218453f5d1af5c23cac81a024db3a07ccd2494ecd31f2090c3}"

VAULT_ZIP="${VAULT_ZIP:-/tmp/vault_${VAULT_SURUM}_linux_arm64.zip}"
VAULT_BIN="${VAULT_BIN:-/usr/local/bin/vault}"
ETC=/etc/vault
DEPO=/opt/vault/data
BETIK_DIZIN=/opt/vault/bin
KAYNAK_DIZIN="$(cd "$(dirname "$0")" && pwd)"
POLITIKA_DIZIN="$KAYNAK_DIZIN/policies"
export VAULT_ADDR="${VAULT_ADDR:-http://127.0.0.1:8200}"

KIP=""
KOK_IPTAL=0

die() { echo "!! $*" >&2; exit 1; }
adim() { echo; echo "== $*"; }
oldu() { echo "   ✓ $*"; }
kuru() { echo "   (kuru) $*"; }

# Kip ayrımını TEK yerde yapan sarmalayıcı: `--kuru` hiçbir şey yazmaz, komutu BASAR.
yap() {
  if [ "$KIP" = "kuru" ]; then kuru "$*"; return 0; fi
  "$@"
}

# =================================================================================================
# 0) KİP AYRIŞTIRMA
# =================================================================================================
for arg in "$@"; do
  case "$arg" in
    --kuru)      [ -n "$KIP" ] && die "çelişen kip bayrağı"; KIP=kuru ;;
    --uygula)    [ -n "$KIP" ] && die "çelişen kip bayrağı"; KIP=uygula ;;
    --kok-iptal) KOK_IPTAL=1 ;;
    *)           die "bilinmeyen argüman: $arg (--kuru | --uygula [--kok-iptal])" ;;
  esac
done
[ -n "$KIP" ] || { echo "KULLANIM: $0 --kuru | --uygula [--kok-iptal]" >&2; exit 2; }

# =================================================================================================
# 1) İKİLİ — sha256 PİNİ DOĞRULANIR, SONRA kurulur
# =================================================================================================
# KURU KOŞUM EKSİKLERİ ÖLDÜRMEZ, RAPORLAR. Bir kuru koşumun işi "neyin eksik olduğunu
# göstermek"tir; ilk eksikte ölen bir kuru koşum operatöre yalnız BİR eksiği söyler ve geri
# kalanını gizler (ölçüm boşluğu, kapı değil). `--uygula` kipinde AYNI koşullar DURDURUR.
#
# ZIP AÇICI — İKİ YOL, İKİSİ DE ADIYLA (A1 ilk kurulumunda ÖLÇÜLEN eksik, 2026-09-14 09:0xZ).
# `unzip` A1'de KURULU DEĞİLDİ ve bu adım tam da sha256'sı doğrulanmış zip'i açacağı yerde
# düştü; Rol-1 apt ile kurup elle ilerledi. Düzeltme ÇİFTTİR ve iki parçası AYRI sorunu çözer:
#   (a) A0 rolü paket listesine `unzip` girdi (roles/meridian_a1/defaults/main.yml::apt_paketleri)
#       → bir dahaki TEMİZ kurulumda eksik DOĞMAZ;
#   (b) bu betik stdlib'e düşer (python3 zipfile) → kasa kurulumu bir BAKIM PENCERESİNDE koşar
#       ve orada "önce apt-get install" demek pencereyi uzatır. python3 A1'de zaten var
#       (meridian venv'i onunla kuruluyor).
# Yalnız (a) yapılsaydı rolü koşmamış bir makinede aynı arıza tekrarlardı; yalnız (b) yapılsaydı
# A1 kalıcı olarak fallback yolunda kalır ve eksik HİÇ görünmezdi.
# ÜÇÜNCÜ, SESSİZ BİR YOL YOKTUR: ikisi de yoksa `--uygula` DURUR, `--kuru` eksiği RAPORLAR.
# Kapı: tests/test_vault_faz2_v485.py §I9-I12 (kuru çıktısı · gerçek zip · mutasyon).
_acici() {
  if command -v unzip >/dev/null 2>&1; then echo "unzip"
  elif command -v python3 >/dev/null 2>&1; then echo "python3-zipfile"
  else echo "YOK"; fi
}

# Fallback tek satırı. TIRNAKLAMASI ÇİVİLİ: I11 bu satırı kaynaktan SÖKÜP gerçek bir zip'le
# koşar — bozuk bir tırnaklama aksi hâlde ancak bakım penceresinde, zip elde dururken görünürdü.
_ac_zip() {
  python3 -c 'import sys, zipfile; zipfile.ZipFile(sys.argv[1]).extractall(sys.argv[2])' "$1" "$2"
}

adim "1) vault ikilisi (sürüm $VAULT_SURUM)"
ACICI="$(_acici)"
if [ "$VAULT_ZIP_SHA256" = "OLCULMEDI" ]; then
  RECETE="curl -fsSL https://releases.hashicorp.com/vault/${VAULT_SURUM}/vault_${VAULT_SURUM}_SHA256SUMS | grep linux_arm64"
  if [ "$KIP" = "kuru" ]; then
    kuru "TEDARİK KAPISI AÇIK DEĞİL: VAULT_ZIP_SHA256 nöbetçi değerde — --uygula burada DURUR"
    kuru "reçete: $RECETE"
  else
    die "tedarik kapısı: VAULT_ZIP_SHA256 nöbetçi değerde.
     Reçete: $RECETE
     Değeri bu betiğe (ya da ortama) yazıp yeniden koş. Doğrulanmamış ikili KURULMAZ."
  fi
fi
if [ -x "$VAULT_BIN" ] && "$VAULT_BIN" version 2>/dev/null | grep -q "$VAULT_SURUM"; then
  oldu "ikili zaten kurulu ve sürüm eşleşiyor (idempotent)"
elif [ "$KIP" = "kuru" ]; then
  kuru "sha256 doğrula + aç ($ACICI) + install → $VAULT_BIN   (zip: $VAULT_ZIP$([ -f "$VAULT_ZIP" ] || echo ' — YOK'))"
  if [ "$ACICI" = "YOK" ]; then
    kuru "EKSİK: ne unzip ne python3 var — zip AÇILAMAZ, --uygula burada DURUR"
    kuru "reçete: sudo apt-get install -y unzip"
  fi
else
  [ -f "$VAULT_ZIP" ] || die "zip bulunamadı: $VAULT_ZIP (önce indir, sonra bu betiği koş)"
  echo "${VAULT_ZIP_SHA256}  ${VAULT_ZIP}" | sha256sum -c - >/dev/null \
    || die "sha256 UYUŞMADI — ikili kurulmadı ($VAULT_ZIP)"
  oldu "sha256 pini doğrulandı"
  rm -rf /tmp/vault_unzip
  mkdir -p /tmp/vault_unzip
  case "$ACICI" in
    unzip)           unzip -o -q "$VAULT_ZIP" -d /tmp/vault_unzip ;;
    python3-zipfile) _ac_zip "$VAULT_ZIP" /tmp/vault_unzip ;;
    *) die "zip AÇILAMIYOR: ne unzip ne python3 var. Reçete: sudo apt-get install -y unzip" ;;
  esac
  oldu "zip açıldı ($ACICI)"
  install -o root -g root -m 0755 /tmp/vault_unzip/vault "$VAULT_BIN"
  oldu "ikili kuruldu: $VAULT_BIN"
fi

# =================================================================================================
# 2) KULLANICI + DİZİNLER  (izin gerekçeleri başlıktaki SAPMA bloğunda)
# =================================================================================================
adim "2) kullanıcı ve dizinler"
if id -u vault >/dev/null 2>&1; then
  oldu "vault kullanıcısı zaten var"
else
  yap useradd --system --home-dir "$DEPO" --shell /usr/sbin/nologin vault
  oldu "vault sistem kullanıcısı (nologin)"
fi
yap install -d -o vault -g vault -m 0700 "$DEPO"
yap install -d -o root  -g root  -m 0755 "$BETIK_DIZIN"
yap install -d -o root  -g vault -m 0750 "$ETC"
oldu "dizinler: $DEPO (0700 vault) · $BETIK_DIZIN (0755 root) · $ETC (0750 root:vault)"

# =================================================================================================
# 3) YAPILANDIRMA + BETİK + BİRİMLER (depodan; A0 rolü kurmadıysa)
# =================================================================================================
adim "3) yapılandırma, betik ve birimler"
yap install -o root -g vault -m 0640 "$KAYNAK_DIZIN/vault.hcl"  "$ETC/vault.hcl"
yap install -o root -g vault -m 0640 "$KAYNAK_DIZIN/agent.hcl"  "$ETC/agent.hcl"
yap install -o root -g root  -m 0750 "$KAYNAK_DIZIN/vault_unseal.sh" "$BETIK_DIZIN/vault_unseal.sh"
for birim in vault.service vault-unseal.service vault-agent.service \
             vault-sagligi.service vault-sagligi.timer; do
  yap install -o root -g root -m 0644 "$KAYNAK_DIZIN/$birim" "/etc/systemd/system/$birim"
done
yap systemctl daemon-reload
oldu "yapılandırma + 5 birim yerinde"

# =================================================================================================
# 4) SERVİSİ AÇ
# =================================================================================================
adim "4) vault servisini aç"
yap systemctl enable --now vault
if [ "$KIP" != "kuru" ]; then
  "$VAULT_BIN" status || true      # çıkış kodu 2 = mühürlü; bu adımda BEKLENEN hâl
fi

# =================================================================================================
# 5) INIT — DEĞER KABUĞA HİÇ GİRMEZ
# =================================================================================================
# `operator init` çıktısı (unseal anahtarı + kök jetonu) BORUYLA python'a akar. Python iki
# dosyayı yazar ve hiçbir şey basmaz. Bir kabuk değişkenine alsaydık değer, betiğin geri kalanı
# boyunca ortamda yaşar ve bir `set -x`/hata mesajı onu ifşa edebilirdi.
adim "5) init (Shamir 1/1)"
if [ -s "$ETC/unseal.key" ]; then
  oldu "kasa zaten init edilmiş (unseal anahtarı yerinde) — init ATLANDI (idempotent)"
elif [ "$KIP" = "kuru" ]; then
  kuru "vault operator init -key-shares=1 -key-threshold=1 → $ETC/unseal.key + $ETC/root.token (0400)"
else
  umask 377
  "$VAULT_BIN" operator init -key-shares=1 -key-threshold=1 -format=json \
    | python3 -c '
import json, os, sys
veri = json.load(sys.stdin)
os.umask(0o377)
for yol, icerik in (("/etc/vault/unseal.key", veri["unseal_keys_b64"][0]),
                    ("/etc/vault/root.token", veri["root_token"])):
    with open(yol, "w", encoding="utf-8") as f:
        f.write(icerik)
    os.chmod(yol, 0o400)
    os.chown(yol, 0, 0)
'
  umask 022
  oldu "init tamam — $ETC/unseal.key ve $ETC/root.token yazıldı (0400 root:root, DEĞER BASILMADI)"
fi

# =================================================================================================
# 6) UNSEAL — aynı betik, tek kaynak
# =================================================================================================
adim "6) unseal"
yap "$BETIK_DIZIN/vault_unseal.sh"

# =================================================================================================
# 7) KÖK JETONUYLA OTURUM — değer stdin'den, argv'ye ve ortama GİRMEZ
# =================================================================================================
# `vault login -` jetonu STDIN'den okur; `-no-print` onu ekrana basmaz. Jeton, kabuğun token
# yardımcısına (root'un ev dizini, 0600) yazılır ve bu betiğin SONUNDA silinir.
adim "7) kök jetonuyla oturum"
yap sh -c "\"$VAULT_BIN\" login -no-print - < \"$ETC/root.token\""

# =================================================================================================
# 8) KV-v2 MONTAJI + POLİTİKALAR
# =================================================================================================
adim "8) kv-v2 montajı ve politikalar"
if [ "$KIP" = "kuru" ]; then
  kuru "vault secrets enable -path=secret kv-v2   (zaten varsa no-op)"
  kuru "vault policy write meridian-agent $POLITIKA_DIZIN/meridian-agent.hcl"
  kuru "vault policy write meridian-admin $POLITIKA_DIZIN/meridian-admin.hcl"
else
  "$VAULT_BIN" secrets list -format=json | grep -q '"secret/"' \
    || "$VAULT_BIN" secrets enable -path=secret kv-v2
  "$VAULT_BIN" policy write meridian-agent "$POLITIKA_DIZIN/meridian-agent.hcl"
  "$VAULT_BIN" policy write meridian-admin "$POLITIKA_DIZIN/meridian-admin.hcl"
  oldu "politikalar yazıldı: $("$VAULT_BIN" policy list | tr '\n' ' ')"
fi

# =================================================================================================
# 9) APPROLE — Agent'ın kimliği
# =================================================================================================
# `secret_id_ttl=0` + `secret_id_num_uses=0`: secret-id DÖNMEZ ve sınırsız kullanılır. Gerekçe
# tasarım §6.3: dönen bir secret-id, Agent'ı yeniden başlatan her bakım penceresini bir
# bootstrap işine çevirirdi. Rotasyon ELLEdir (admin politikasındaki secret-id yolu).
adim "9) approle"
if [ "$KIP" = "kuru" ]; then
  kuru "vault auth enable approle   (zaten varsa no-op)"
  kuru "vault write auth/approle/role/agent policies=meridian-agent secret_id_ttl=0 …"
  kuru "role-id → $ETC/agent.role-id (0400) · secret-id → $ETC/agent.secret-id (0400)"
else
  "$VAULT_BIN" auth list -format=json | grep -q '"approle/"' \
    || "$VAULT_BIN" auth enable approle
  "$VAULT_BIN" write auth/approle/role/agent \
      token_policies=meridian-agent \
      secret_id_ttl=0 secret_id_num_uses=0 \
      token_ttl=1h token_max_ttl=24h
  # DEĞERLER DOĞRUDAN DOSYAYA: `umask 377` dosyayı 0400 olarak YARATIR (önce 0644 yaratıp
  # sonra chmod etmek bir yarış penceresi açardı).
  ( umask 377; "$VAULT_BIN" read  -field=role_id   auth/approle/role/agent/role-id   > "$ETC/agent.role-id" )
  ( umask 377; "$VAULT_BIN" write -f -field=secret_id auth/approle/role/agent/secret-id > "$ETC/agent.secret-id" )
  chown root:root "$ETC/agent.role-id" "$ETC/agent.secret-id"
  oldu "approle kuruldu; bootstrap dosyaları: $(stat -c '%n %a %U:%G' "$ETC/agent.role-id" "$ETC/agent.secret-id" | tr '\n' ' ')"
fi

# =================================================================================================
# 10) YÖNETİCİ JETONU (kök jetonun yerine geçer)
# =================================================================================================
adim "10) yönetici jetonu"
if [ "$KIP" = "kuru" ]; then
  kuru "vault token create -policy=meridian-admin -ttl=720h → $ETC/admin.token (0400)"
elif [ -s "$ETC/admin.token" ]; then
  oldu "yönetici jetonu zaten var — YENİDEN ÜRETİLMEDİ (idempotent; yenilemek için dosyayı sil)"
else
  ( umask 377; "$VAULT_BIN" token create -policy=meridian-admin -ttl=720h -field=token > "$ETC/admin.token" )
  chown root:root "$ETC/admin.token"
  oldu "yönetici jetonu yazıldı (0400 root:root, DEĞER BASILMADI)"
fi

# =================================================================================================
# 11) KÖK JETONU İPTALİ — YALNIZ --kok-iptal ile
# =================================================================================================
# Bilerek AÇIK BAYRAK: kök jetonu iptal edildikten sonra geri getirilemez (yeniden init
# gerekirdi) ve bu kurulumun TEK geri alınamaz adımıdır. Varsayılan olarak koşsaydı, yarım
# kalmış bir kurulum operatörü kasadan kilitleyebilirdi.
adim "11) kök jetonu"
if [ "$KOK_IPTAL" != "1" ]; then
  oldu "ATLANDI — kök jetonu DURUYOR ($ETC/root.token). İptal için: $0 --uygula --kok-iptal"
elif [ "$KIP" = "kuru" ]; then
  kuru "vault token revoke -self  +  rm -f $ETC/root.token  (GERİ ALINAMAZ)"
else
  "$VAULT_BIN" token revoke -self
  rm -f "$ETC/root.token"
  oldu "kök jetonu İPTAL edildi ve dosyası silindi — yönetim artık $ETC/admin.token ile"
fi

# =================================================================================================
# 12) OTURUMU KAPAT + KANIT
# =================================================================================================
adim "12) kanıt (yalnız sır OLMAYAN alanlar)"
if [ "$KIP" = "kuru" ]; then
  kuru "rm -f ~/.vault-token ; vault status ; stat $ETC/*"
else
  rm -f "$HOME/.vault-token"
  "$VAULT_BIN" status || true
  stat -c '%n %a %U:%G' "$ETC"/* || true
  echo
  echo ">> SIRADAKİ: ./vault_sir_koy.sh --kuru   (dalga-1 sırlarını kasaya taşı)"
  echo ">> SONRA   : systemctl enable --now vault-agent  +  canary (başlıktaki reçete)"
fi
