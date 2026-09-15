# TSK-176 T1 (Rol-1 ruling 2026-09-15) — YEREL state, YALNIZ import/plan aşaması için.
#
# BU PLANDA `terraform apply` YOKTUR: `altyapi/altyapi.sh` bir `apply` alt komutu TAŞIMAZ
# (çivi: tests/test_apisix_tf_uret_v502.py test_d). İlk apply'ın ön koşulu T2'dir — OCI Object
# Storage S3-uyumlu arka ucu ve `terraform init -migrate-state`; Customer Secret Key operatördedir.
# Tasarım §1.1'in "üretimde local kesinlikle değil" hükmü GEÇERLİDİR; buradaki istisna bootstrap
# (import + plan) penceresidir ve apply'ın yokluğuyla sınırlanmıştır.
#
# YOL NEDEN `/opt/veri/...`: dağıtım (`dagit`) `/opt/meridian/` ağacını `rsync --delete` ile
# eşitler — state dosyası o ağacın İÇİNDE dursaydı ilk dağıtımda SESSİZCE SİLİNİRDİ ve terraform
# canlı kaynakları "yok" sayardı. Ağacın dışında duran state dağıtımdan etkilenmez.
terraform {
  backend "local" {
    path = "/opt/veri/altyapi/apisix/terraform.tfstate"
  }
}
