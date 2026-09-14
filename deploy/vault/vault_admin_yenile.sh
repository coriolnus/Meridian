#!/usr/bin/env bash
# =================================================================================================
# vault_admin_yenile.sh — YÖNETİCİ jetonunu (PERİYODİK) yeniler (TSK-064 Faz-2, tur-4). A1'de koşar;
# DEPODA versiyonlanır. HEDEF: /opt/vault/bin/vault_admin_yenile.sh (0750 root:root).
# =================================================================================================
# NEDEN VAR — ÖLÇÜLDÜ (2026-09-14 15:1xZ, Rol-1): kök jetonu iptal edildikten sonra kasanın TEK
# yönetim kimliği /etc/vault/admin.token'dır. `-ttl=720h` ile yaratılan bir jeton `token renew` ile
# en fazla SİSTEM AZAMİ TTL'sine (varsayılan 768 sa, YARATILIŞTAN itibaren) uzatılır: aylık bir
# yenileme onu kurtarmaz, 32. gün ölür ve kasa yönetimsiz kalır (kurtarma yolu yalnız generate-root).
# PERİYODİK jeton (`vault_kur.sh` adım 10: `-period=720h`) her yenilemede periyodu BAŞTAN alır —
# süresiz yaşar, yeter ki periyot dolmadan yenilensin. Bu betik o yenilemedir; tetik haftalık
# (`vault-admin-yenile.timer`; periyot 30 gün → 4× emniyet payı), düşerse fail-notify alarmı.
#
# SIR DİSİPLİNİ (vault_unseal.sh ile AYNI): jeton DEĞERİ argv'ye ve ortama GİRMEZ — `login -no-print -`
# stdin'den okur; `set -x` YOK; hiçbir `echo`/`printf` sır basmaz (yalnız TTL/period SAYILARI basılır);
# oturum yardımcısı (`$HOME/.vault-token`, 0600) çıkışta SİLİNİR (trap) — kalıcı yönetici oturumu
# sonraki her root kabuğunu yönetici yapardı.
#
# ÇIKIŞ KODLARI (HÜKÜM): 0 yenilendi (ttl ölçüldü ve basıldı) · 1 oturum/yenileme düştü ya da jeton
# yenilenebilir DEĞİL/periyotsuz (adıyla) · 2 jeton dosyası yok/boş.
set -euo pipefail

JETON_DOSYASI=${VAULT_ADMIN_TOKEN_FILE:-/etc/vault/admin.token}
VAULT_IKILI=${VAULT_BIN:-/usr/local/bin/vault}
export VAULT_ADDR=${VAULT_ADDR:-http://127.0.0.1:8200}

_bas() { echo "[vault-admin-yenile] $*"; }

[ -s "$JETON_DOSYASI" ] || { _bas "yönetici jetonu dosyası yok/boş: $JETON_DOSYASI"; exit 2; }
trap 'rm -f "${HOME:-/root}/.vault-token"' EXIT

"$VAULT_IKILI" login -no-print - < "$JETON_DOSYASI" >/dev/null \
  || { _bas "yönetici jetonuyla oturum açılamadı — jeton SÜRESİ DOLMUŞ ya da iptal olabilir (kurtarma: generate-root, vault.hcl KURTARMA KÖKÜ)"; exit 1; }

# ÖNCE ÖLÇ: yenilenebilir mi, periyotlu mu. Periyotsuz bir jeton (eski `-ttl` kurulumu) burada ADIYLA
# yakalanır — "yeniledim" demek yetmez, 32. günde yine ölürdü.
BILGI="$("$VAULT_IKILI" token lookup -format=json | tr -d ' \n' || true)"
case "$BILGI" in
  *'"renewable":true'*) ;;
  *) _bas "jeton YENİLENEBİLİR DEĞİL — yenileme anlamsız (adım 10 -period ile yeniden yaratılmalı)"; exit 1 ;;
esac
case "$BILGI" in
  *'"period":0'*|*'"period":"0'*) _bas "jeton PERİYOTSUZ (eski -ttl kurulumu) — renew azami TTL'de ölür; adım 10 -period ile yeniden yarat"; exit 1 ;;
esac

"$VAULT_IKILI" token renew >/dev/null 2>&1 \
  || { _bas "token renew BAŞARISIZ"; exit 1; }

# HÜKÜM ÖLÇÜMDEN: yenileme sonrası ttl (saniye) ve period basılır — sır değil, sayıdır.
SONRA="$("$VAULT_IKILI" token lookup -format=json | tr -d ' \n' || true)"
TTL="$(printf '%s' "$SONRA" | sed -n 's/.*"ttl":\([0-9]*\).*/\1/p')"
PERIOD="$(printf '%s' "$SONRA" | sed -n 's/.*"period":"\{0,1\}\([0-9hms]*\).*/\1/p')"
_bas "yenilendi — ttl_sn=${TTL:-olculemedi} period=${PERIOD:-olculemedi}"
exit 0
