# ÜRETİLDİ — ELLE DÜZENLEME YAPMA.
# Kaynak : deploy/sir_envanteri.yaml (vault_kv bloğu)
# Üreten : ops/vault_politika_uret.py — deterministik, damgasız (her koşu aynı bayt)
# Tazelik: python ops/vault_politika_uret.py --kontrol   (çıkış 1 = bayat)
#
# Bu dosyayı düzenlersen bir sonraki üretim değişikliği siler. Değişmesi gereken şey
# envanterdir: yeni bir sır oraya girer, bu dosya yeniden üretilir.


# Kasa adresi — deploy/vault/vault.hcl listener'ı ile TEK KAYNAK.
vault {
  address = "http://127.0.0.1:8200"
}

# Sıfırıncı sır (tasarım §6.3): role_id sır DEĞİL, secret_id 0400 root:root.
auto_auth {
  method "approle" {
    mount_path = "auth/approle"
    config = {
      role_id_file_path                   = "/etc/vault/agent.role-id"
      secret_id_file_path                 = "/etc/vault/agent.secret-id"
      remove_secret_id_file_after_reading = false
    }
  }
}

# dash_token — tüketici: meridian.service (LoadCredential=dash_token)
template {
  contents    = "{{ with secret \"secret/data/meridian/dash_token\" }}{{ .Data.data.value }}{{ end }}"
  destination = "/etc/meridian/dash_token"
  perms       = 0400
  error_on_missing_key = true
}

# nous_api_key — tüketici: meridian.service (LoadCredential=NOUS_API_KEY)
template {
  contents    = "{{ with secret \"secret/data/meridian/nous_api_key\" }}{{ .Data.data.value }}{{ end }}"
  destination = "/etc/meridian/nous_api_key"
  perms       = 0400
  error_on_missing_key = true
}

# kapi_apikey — tüketici: meridian.service (LoadCredential=KAPI_APIKEY)
template {
  contents    = "{{ with secret \"secret/data/meridian/kapi_apikey\" }}{{ .Data.data.value }}{{ end }}"
  destination = "/etc/meridian/kapi_apikey"
  perms       = 0400
  error_on_missing_key = true
}

# apisix_admin_key — tüketici: ops/apisix_uygula.py (operatör eliyle koşan ops aracı; birim DEĞİL, restart yok)
template {
  contents    = "{{ with secret \"secret/data/meridian/apisix_admin_key\" }}{{ .Data.data.value }}{{ end }}"
  destination = "/etc/meridian/apisix_admin_key"
  perms       = 0400
  error_on_missing_key = true
}

# HINDSIGHT_API_DATABASE_URL — tüketici: hindsight-api.service (LoadCredential=HINDSIGHT_API_DATABASE_URL)
template {
  contents    = "{{ with secret \"secret/data/meridian/HINDSIGHT_API_DATABASE_URL\" }}{{ .Data.data.value }}{{ end }}"
  destination = "/etc/hindsight/creds/HINDSIGHT_API_DATABASE_URL"
  perms       = 0400
  error_on_missing_key = true
}

# HINDSIGHT_API_LLM_API_KEY — tüketici: hindsight-api.service (LoadCredential=HINDSIGHT_API_LLM_API_KEY)
template {
  contents    = "{{ with secret \"secret/data/meridian/HINDSIGHT_API_LLM_API_KEY\" }}{{ .Data.data.value }}{{ end }}"
  destination = "/etc/hindsight/creds/HINDSIGHT_API_LLM_API_KEY"
  perms       = 0400
  error_on_missing_key = true
}

# HINDSIGHT_API_TENANT_API_KEY — tüketici: hindsight-api.service · meridian.service · meridian-defter-ozeti-retain (LoadCredential=HINDSIGHT_API_TENANT_API_KEY — AYNI dosya)
template {
  contents    = "{{ with secret \"secret/data/meridian/HINDSIGHT_API_TENANT_API_KEY\" }}{{ .Data.data.value }}{{ end }}"
  destination = "/etc/hindsight/creds/HINDSIGHT_API_TENANT_API_KEY"
  perms       = 0400
  error_on_missing_key = true
}
