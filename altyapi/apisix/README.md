# `altyapi/apisix/` — APISIX yapılandırmasının Terraform tarafı (TSK-176 T1)

Canlı APISIX kapısının rota / upstream / tüketici / tüketici-grubu yapılandırmasını **import-first**
yönetime alan dizin. Bu fazda amaç **apply değil, DENETİM**: kaynaklar import edilir, `terraform plan
-detailed-exitcode` bir **drift denetçisi** olur ve `ops/apisix_uygula.py` bir sürüm daha geri-alım
yolu olarak yaşar.

## Dosyalar

| Dosya | Ne | Kim üretir |
|---|---|---|
| `versions.tf` | Terraform ve sağlayıcı sürüm pinleri (`=`, tam sürüm) | elle |
| `provider.tf` | `provider "apisix" {}` — BOŞ; uç/anahtar ortamdan | elle |
| `backend.tf` | `backend "local"`, state ağacın DIŞINDA (`/opt/veri/...`) | elle |
| `import.tf` | `import { … }` blokları — kimlikler `deploy/apisix/routes.yaml`tan | **ÜRETİLMİŞ** (`ops/apisix_tf_uret.py`) |
| `uretilen.tf` | `terraform plan -generate-config-out` çıktısı (Task 3, A1'de doğar) | terraform |
| `.terraform.lock.hcl` | sağlayıcı kilit dosyası — depoya girer (tek kaynak) | terraform (Task 3) |

`import.tf` **elle düzenlenmez**: tek kaynak `deploy/apisix/routes.yaml`tır ve dosya ondan üretilir.
Bayatlığı iki yerden ölçülür: `ops/apisix_tf_uret.py --kontrol` (çıkış 0/1) ve
`tests/test_apisix_tf_uret_v502.py` test_b (depodaki metin == üreticinin çıktısı).

## Koşum (A1, root)

```
sudo ./altyapi/altyapi.sh init          # sağlayıcıyı indirir, kilit dosyasına uyar
sudo ./altyapi/altyapi.sh import-uret   # import.tf'yi routes.yaml'dan yeniden üretir + kontrol
sudo ./altyapi/altyapi.sh plan          # ilk turda uretilen.tf'yi doğurur
sudo ./altyapi/altyapi.sh denetle       # drift hükmü: 0 = drift yok · 2 = drift · 1 = hata
```

`apply` alt komutu **yoktur** (Rol-1 ruling 2026-09-15): yerel state yalnız import/plan içindir.
İlk `apply`ın ön koşulu T2'dir — OCI Object Storage S3-uyumlu arka ucu + `terraform init
-migrate-state` (Customer Secret Key operatörde). Drift görülürse hüküm Rol-1'in, düzeltme bugün
hâlâ `ops/apisix_uygula.py --uygula` ile yapılır.

## Sır

Admin anahtarı yalnız iki kanaldan okunur — `/etc/meridian/apisix_admin_key` (0400 root), yoksa
`/opt/apisix/.env-apisix` içindeki `APISIX_ADMIN_KEY` satırı — ve **yalnız ortam değişkenine**
girer: `altyapi.sh` okuduğu **kanalın adını** stderr'e yazar, değeri hiçbir yere yazmaz. HCL
dosyalarında anahtar da uç adresi de bulunmaz (çivi: `tests/test_apisix_tf_uret_v502.py` test_e).

## Sınır (bedel beyanı, tasarım §6)

Sağlayıcı bir **topluluk** sağlayıcısıdır (`rework-space-com/apisix`, MPL-2.0): bakımı bize ait
değil. Sürüm pinli, kilit dosyası depoda, plan çıktısı okunuyor ve geri-alım aracı duruyor.
Sağlayıcının **satır-içi `upstream` desteği DOĞRULANMADI** (kaynak belgeleri `upstream_id`/
`service_id` sunuyor); canlı rotalar satır-içi upstream taşıyor — bunu Task 3 ÖLÇER, sonucun
kararı (rotaları `apisix_upstream` kaynaklarına ayırmak canlı DEĞİŞİKLİK gerektirir) operatörün.
