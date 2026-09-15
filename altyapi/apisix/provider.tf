# TSK-176 T1 — sağlayıcı yapılandırması: BOŞ, ve bu bilinçlidir.
#
# Değerler ORTAMDAN gelir (APISIX_ENDPOINT / APISIX_APIKEY) ve ortamı `altyapi/altyapi.sh` doldurur:
# anahtar `ops/apisix_uygula.py` ile AYNI kanal sırasından okunur ve HİÇBİR çıktıya yazılmaz.
# HCL'e yazılsaydı sır (ya da en iyi hâlde canlı adres) versiyonlanmış bir dosyaya girerdi —
# `deploy/apisix/routes.yaml` başlığındaki "SIR YOK" kuralının aynısı, bir katman aşağıda.
# Çivi: tests/test_apisix_tf_uret_v502.py test_e (bu dosyada anahtar/adres alanı ARANMAZ, YOKLUĞU
# ölçülür).
provider "apisix" {}
