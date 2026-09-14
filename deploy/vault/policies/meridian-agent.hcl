# ÜRETİLDİ — ELLE DÜZENLEME YAPMA.
# Kaynak : deploy/sir_envanteri.yaml (vault_kv bloğu)
# Üreten : ops/vault_politika_uret.py — deterministik, damgasız (her koşu aynı bayt)
# Tazelik: python ops/vault_politika_uret.py --kontrol   (çıkış 1 = bayat)
#
# Bu dosyayı düzenlersen bir sonraki üretim değişikliği siler. Değişmesi gereken şey
# envanterdir: yeni bir sır oraya girer, bu dosya yeniden üretilir.


# Dalga-1: yedi tek-değer sırrı, yalnız okuma. Liste envanterin SIRASINI korur.

# dash_token → /etc/meridian/dash_token
path "secret/data/meridian/dash_token" {
  capabilities = ["read"]
}

# nous_api_key → /etc/meridian/nous_api_key
path "secret/data/meridian/nous_api_key" {
  capabilities = ["read"]
}

# kapi_apikey → /etc/meridian/kapi_apikey
path "secret/data/meridian/kapi_apikey" {
  capabilities = ["read"]
}

# apisix_admin_key → /etc/meridian/apisix_admin_key
path "secret/data/meridian/apisix_admin_key" {
  capabilities = ["read"]
}

# HINDSIGHT_API_DATABASE_URL → /etc/hindsight/creds/HINDSIGHT_API_DATABASE_URL
path "secret/data/meridian/HINDSIGHT_API_DATABASE_URL" {
  capabilities = ["read"]
}

# HINDSIGHT_API_LLM_API_KEY → /etc/hindsight/creds/HINDSIGHT_API_LLM_API_KEY
path "secret/data/meridian/HINDSIGHT_API_LLM_API_KEY" {
  capabilities = ["read"]
}

# HINDSIGHT_API_TENANT_API_KEY → /etc/hindsight/creds/HINDSIGHT_API_TENANT_API_KEY
path "secret/data/meridian/HINDSIGHT_API_TENANT_API_KEY" {
  capabilities = ["read"]
}
