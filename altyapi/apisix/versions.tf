# TSK-176 T1 — sürüm pinleri (tasarım §1.2; plan Tech Stack).
#
# İKİ PİN, İKİ AYRI GEREKÇE — ikisi de "=" ile TAM, ">=" ile değil:
#   · Terraform 1.16.2 (BUSL 1.1; lisans beyanı ROADMAP TSK-176 Ref'te): ikilinin sürümü A0
#     rolünde apt pini ile (`terraform_surumu`) kurulur. Buradaki `required_version` o pinin
#     AYNASIDIR: A1'de başka bir sürüm belirirse terraform ÇALIŞMAYI REDDEDER — sessiz sürüm
#     kaymasının state'e dokunmadan durduğu yer.
#   · Sağlayıcı `rework-space-com/apisix` 1.8.1 (MPL-2.0) TOPLULUK sağlayıcısıdır (bedel beyanı,
#     tasarım §6): bakımı bize ait değil. Pin + `.terraform.lock.hcl` (depoda) o riski "bir gün
#     kendiliğinden değişir"den "bir commit ile değişir"e indirir.
terraform {
  required_version = "= 1.16.2"
  required_providers {
    apisix = {
      source  = "rework-space-com/apisix"
      version = "= 1.8.1"
    }
  }
}
