# ÜRETİLDİ — ELLE DÜZENLEME YAPMA.
# Kaynak : deploy/sir_envanteri.yaml (vault_kv + vault_dosyalar blokları)
# Üreten : ops/vault_politika_uret.py — deterministik, damgasız (her koşu aynı bayt)
# Tazelik: python ops/vault_politika_uret.py --kontrol   (çıkış 1 = bayat)
#
# Bu dosyayı düzenlersen bir sonraki üretim değişikliği siler. Değişmesi gereken şey
# envanterdir: yeni bir sır oraya girer, bu dosya yeniden üretilir.


# Yalnız okuma. Liste `vault_kv`den TÜRER ve envanterin SIRASINI korur —
# düzyazıya gömülü bir sayım (kaç sır) dalga-2'de sessizce yalan olurdu.

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

# openrouter_api_key → /etc/meridian/openrouter_api_key
path "secret/data/meridian/openrouter_api_key" {
  capabilities = ["read"]
}

# bot_key_bekci → /etc/meridian/bot_key_bekci
path "secret/data/meridian/bot_key_bekci" {
  capabilities = ["read"]
}

# bot_key_karne → /etc/meridian/bot_key_karne
path "secret/data/meridian/bot_key_karne" {
  capabilities = ["read"]
}

# bot_key_sef → /etc/meridian/bot_key_sef
path "secret/data/meridian/bot_key_sef" {
  capabilities = ["read"]
}

# bot_key_meridian → /etc/meridian/bot_key_meridian
path "secret/data/meridian/bot_key_meridian" {
  capabilities = ["read"]
}

# pano_giris_parola → /etc/meridian/pano_giris_parola
path "secret/data/meridian/pano_giris_parola" {
  capabilities = ["read"]
}

# hindsight_cp_access_key → /etc/meridian/hindsight_cp_access_key
path "secret/data/meridian/hindsight_cp_access_key" {
  capabilities = ["read"]
}

# hindsight_cp_dataplane_api_key → /etc/meridian/hindsight_cp_dataplane_api_key
path "secret/data/meridian/hindsight_cp_dataplane_api_key" {
  capabilities = ["read"]
}
