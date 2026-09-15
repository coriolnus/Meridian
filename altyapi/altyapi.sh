#!/usr/bin/env bash
# altyapi/altyapi.sh — A1'de Terraform sarmalayıcısı (TSK-176 T1). ROOT ile koşar:
#   sudo ./altyapi/altyapi.sh <komut>
#
#   init         terraform init (sağlayıcı pini versions.tf'te, kilit dosyası depodan)
#   import-uret  import.tf'yi routes.yaml'dan yeniden üret (ops/apisix_tf_uret.py) + güncellik kontrolü
#   plan         ilk turda `-generate-config-out=uretilen.tf` (import edilen kaynakların HCL'i),
#                uretilen.tf zaten varsa düz plan
#   denetle      terraform plan -detailed-exitcode (0 drift yok · 2 drift · 1 hata) —
#                `ops/apisix_uygula.py --denetle` ikizi; iki denetçinin aynı hükmü vermesi kanıttır
#
# APPLY ALT KOMUTU YOK (Rol-1 ruling 2026-09-15): yerel state YALNIZ import/plan içindir; ilk
# apply'ın ön koşulu T2'nin uzak arka ucudur (backend.tf şerhi). Çivi: v502 test_d alt komut
# kümesini TAM ölçer — buraya `apply)` eklenirse çivi kırılır.
#
# SIR SÖZLEŞMESİ. Admin anahtarı `ops/apisix_uygula.py` ile AYNI sırada okunur: önce credential
# dosyası (0400 root, TSK-064 Faz-1C kanalı), bulunamazsa apisix konteynerinin `--env-file`ı
# (yedek — o satır kapının kendi config çözümü için orada YAŞAMAYA devam eder). DEĞER yalnız
# ortam değişkenine girer: hiçbir echo/log/argv onu görmez. Okunan KANALIN ADI stderr'e yazılır
# (`ops/apisix_uygula.py::kanal_bildir` emsali, çivi v476): "araç hangi kanaldan okudu" sorusunun
# cevabı bildirilmezse kanal göçü ölçülemez.
set -euo pipefail

KOK="$(cd "$(dirname "$0")/.." && pwd)"
DIZIN="$KOK/altyapi/apisix"
KRED=/etc/meridian/apisix_admin_key
ENVF=/opt/apisix/.env-apisix

# Üretici PyYAML ister; A1'de pinli bağımlılıklar meridian venv'indedir. Sistem python3'e düşüş
# AÇIK VE İŞARETLİDİR (fallback bir özür değil, beyan edilmiş bir yoldur): venv yoksa betik yine
# koşar, PyYAML de yoksa python'un kendi ImportError'u ile GÜRÜLTÜLÜ düşer — sessiz yutma yok.
PY="${PY:-/opt/meridian/.venv/bin/python}"
[ -x "$PY" ] || PY=python3

# Uç adres ortamdan geçersiz kılınabilir (tünel/port değişikliği); varsayılan A1-içi Admin API.
export APISIX_ENDPOINT="${APISIX_ENDPOINT:-http://127.0.0.1:9180}"

if [ -r "$KRED" ]; then
  APISIX_APIKEY="$(tr -d '\n' < "$KRED")"
  echo "kanal: credential dosyası ($KRED)" >&2
elif [ -r "$ENVF" ]; then
  APISIX_APIKEY="$(sed -n 's/^APISIX_ADMIN_KEY=//p' "$ENVF" | head -1 | tr -d '\n')"
  echo "kanal: .env-apisix yedeği ($ENVF)" >&2
else
  echo "anahtar kanalı YOK ($KRED / $ENVF) — okunabilir bir kanal olmadan terraform koşmaz" >&2
  exit 2
fi

# BOŞ ANAHTAR = ARIZA, varsayılan değil (2026-09-07 sınıfı: credential dosyası 1 baytlık boş
# satırdı ve tüketici "anahtarım var" sanıp 401 yedi). Fail-closed.
if [ -z "$APISIX_APIKEY" ]; then
  echo "anahtar BOŞ — kanal okundu ama değer yok (2026-09-07 sınıfı)" >&2
  exit 2
fi
export APISIX_APIKEY

cd "$DIZIN"
case "${1:-}" in
  init)
    terraform init -input=false
    ;;
  import-uret)
    "$PY" "$KOK/ops/apisix_tf_uret.py" --cikti "$DIZIN/import.tf"
    "$PY" "$KOK/ops/apisix_tf_uret.py" --kontrol
    ;;
  plan)
    if [ ! -f uretilen.tf ] && [ ! -f kaynaklar.tf ]; then
      # İLK ÜRETİM: import blokları GEÇİCİ olarak provider satırı taşır (Terraform kısıtı, ops/apisix_tf_uret.py şerhi);
      # üretim biter bitmez import.tf normale (provider'sız, depo hâli) döndürülür — kalıcı fark bırakılmaz.
      "$PY" "$KOK/ops/apisix_tf_uret.py" --cikti "$DIZIN/import.tf" --uretim
      terraform plan -input=false -generate-config-out=uretilen.tf; rc=$?
      "$PY" "$KOK/ops/apisix_tf_uret.py" --cikti "$DIZIN/import.tf"
      exit $rc
    else
      terraform plan -input=false
    fi ;;
  denetle)
    terraform plan -input=false -detailed-exitcode
    ;;
  *)
    echo "kullanım: altyapi.sh {init|import-uret|plan|denetle}" >&2
    exit 64
    ;;
esac
