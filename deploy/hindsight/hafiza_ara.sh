#!/usr/bin/env bash
# hafiza_ara.sh — A1 sarmalayıcısı: EDG-067 taban indeksinde anlamsal arama (TSK-167 dilim-1).
#
# NEDEN SARMALAYICI. Çıplak çağrı üç uzun sabiti (venv yorumcusu, taban dosyası, bge-m3 snapshot
# yolu) HER seferinde elle yazdırırdı ve o üçü BİRLİKTE değişir — biri unutulduğunda arama sessizce
# başka bir modelle ya da bayat bir indeksle koşar, hata VERMEZ. Sabitler tek yerde durur.
#
# KURULUM (Rol-1, A1'de elle — bu betik kendini kurmaz):
#     ln -sfn /opt/meridian/deploy/hindsight/hafiza_ara.sh ~/bin/hafiza_ara.sh
# `~/bin/hafiza_sor.sh` (Hindsight recall) emsali. Symlink olması ŞART DEĞİL ama TERCİHTİR:
# dağıtım depoyu tazelediğinde sarmalayıcı da tazelenir; kopya olsaydı sessizce ayrışırdı.
#
# MODEL YOLU BU DOSYADA SABİTTİR VE BU BİR AYRIŞMA YÜZEYİDİR — beyan ediliyor: aynı snapshot
# yolu A1'deki taban derleme betiğinde (kos_taban.sh) ve haftalık tazeleme biriminde de yazılı.
# Model dizini bir gün değişirse ÜÇÜ BİRDEN değişmeli; yoksa arama ile indeks farklı vektör
# uzaylarında koşar ve sonuçlar sessizce anlamsızlaşır. Tek kaynağa indirmek A1 tarafında bir
# ortam dosyası ister — bu turun dosya sahipliğinde DEĞİL, açık kalem olarak raporlandı.
#
# OMP_NUM_THREADS=2: kos_taban.sh emsali. A1 4 OCPU'dur ve ONNX oturumu varsayılanda hepsini
# alır; arama etkileşimli koşar, yani gece işleriyle (sprint, geri dolum) aynı anda tetiklenebilir.
#
# ÇIKIŞ KODU: `exec` ile CLI'ın kendi kodu (0 sonuç / 1 girdi-uzantı arızası / 2 kullanım)
# DEĞİŞMEDEN dışarı çıkar — kabuk araya kendi kodunu koymaz.
#
# KULLANIM: hafiza_ara.sh [-k 5] [--dosya docs/] [--json] "<soru>"
set -euo pipefail

export OMP_NUM_THREADS=2

exec /opt/hindsight/venv/bin/python \
  /opt/meridian/research/olcumler/edg067_hindsight_faz1/hafiza_ara.py \
  --db /opt/hindsight/edg067/taban.sqlite \
  --model-dir /opt/hindsight/hf-cache/hub/models--BAAI--bge-m3/snapshots/5617a9f61b028005a4858fdac845db406aefb181 \
  "$@"
