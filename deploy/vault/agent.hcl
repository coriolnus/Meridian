# ÜRETİLDİ — ELLE DÜZENLEME YAPMA.
# Kaynak : deploy/sir_envanteri.yaml (vault_kv + vault_dosyalar blokları)
# Üreten : ops/vault_politika_uret.py — deterministik, damgasız (her koşu aynı bayt)
# Tazelik: python ops/vault_politika_uret.py --kontrol   (çıkış 1 = bayat)
#
# Bu dosyayı düzenlersen bir sonraki üretim değişikliği siler. Değişmesi gereken şey
# envanterdir: yeni bir sır oraya girer, bu dosya yeniden üretilir.


# Kasa adresi — deploy/vault/vault.hcl listener'ı ile TEK KAYNAK.
vault {
  address = "http://127.0.0.1:8200"
}

# STATİK (KV-v2) sırların yeniden render aralığı. Varsayılan 5 dk'dır ve
# rotasyon penceresinde beklenen süre TAM OLARAK budur — değer TEK yerde
# yaşar, şerhte tekrarlanmaz (tekrarlanan bir süre kadans değişince yalan olur).
template_config {
  static_secret_render_interval = "1m"
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

# kapi_apikey — tüketici: meridian.service (LoadCredential=KAPI_APIKEY) · BİRİNCİL yol: takma ad bot_key_meridian buraya çözülür · sir_rotasyon.sh --vault render kanıtı
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

# HINDSIGHT_API_LLM_API_KEY — tüketici: hindsight-api.service (LoadCredential=HINDSIGHT_API_LLM_API_KEY) · BİRİNCİL yol: takma ad openrouter_api_key buraya çözülür · sir_rotasyon.sh --vault render kanıtı
template {
  contents    = "{{ with secret \"secret/data/meridian/HINDSIGHT_API_LLM_API_KEY\" }}{{ .Data.data.value }}{{ end }}"
  destination = "/etc/hindsight/creds/HINDSIGHT_API_LLM_API_KEY"
  perms       = 0400
  error_on_missing_key = true
}

# HINDSIGHT_API_TENANT_API_KEY — tüketici: hindsight-api.service · meridian.service · meridian-defter-ozeti-retain (LoadCredential=HINDSIGHT_API_TENANT_API_KEY — AYNI dosya) · BİRİNCİL yol: takma ad hindsight_cp_dataplane_api_key buraya çözülür · sir_rotasyon.sh --vault render kanıtı
template {
  contents    = "{{ with secret \"secret/data/meridian/HINDSIGHT_API_TENANT_API_KEY\" }}{{ .Data.data.value }}{{ end }}"
  destination = "/etc/hindsight/creds/HINDSIGHT_API_TENANT_API_KEY"
  perms       = 0400
  error_on_missing_key = true
}

# bot_key_bekci — tüketici: vault_dosyalar şablonu (/opt/apisix/.env-apisix.vault) · sir_rotasyon.sh --vault render kanıtı — hermes bekci profili ROTASYON KANALIYLA beslenir (yan dosya 2026-09-15'te kaldırıldı: hermes-agent .env.vault OKUMAZ)
template {
  contents    = "{{ with secret \"secret/data/meridian/bot_key_bekci\" }}{{ .Data.data.value }}{{ end }}"
  destination = "/etc/meridian/bot_key_bekci"
  perms       = 0400
  error_on_missing_key = true
}

# bot_key_karne — tüketici: vault_dosyalar şablonu (/opt/apisix/.env-apisix.vault) · sir_rotasyon.sh --vault render kanıtı — hermes karne profili ROTASYON KANALIYLA beslenir (yan dosya 2026-09-15'te kaldırıldı: hermes-agent .env.vault OKUMAZ)
template {
  contents    = "{{ with secret \"secret/data/meridian/bot_key_karne\" }}{{ .Data.data.value }}{{ end }}"
  destination = "/etc/meridian/bot_key_karne"
  perms       = 0400
  error_on_missing_key = true
}

# bot_key_sef — tüketici: vault_dosyalar şablonu (/opt/apisix/.env-apisix.vault) · sir_rotasyon.sh --vault render kanıtı — hermes sef profili ROTASYON KANALIYLA beslenir (yan dosya 2026-09-15'te kaldırıldı: hermes-agent .env.vault OKUMAZ)
template {
  contents    = "{{ with secret \"secret/data/meridian/bot_key_sef\" }}{{ .Data.data.value }}{{ end }}"
  destination = "/etc/meridian/bot_key_sef"
  perms       = 0400
  error_on_missing_key = true
}

# pano_giris_parola — tüketici: vault_dosyalar şablonu (/opt/apisix/.env-apisix.vault) · sir_rotasyon.sh --vault render kanıtı
template {
  contents    = "{{ with secret \"secret/data/meridian/pano_giris_parola\" }}{{ .Data.data.value }}{{ end }}"
  destination = "/etc/meridian/pano_giris_parola"
  perms       = 0400
  error_on_missing_key = true
}

# hindsight_cp_access_key — tüketici: vault_dosyalar şablonu (/opt/hindsight/.env-cp.vault) · sir_rotasyon.sh --vault render kanıtı
template {
  contents    = "{{ with secret \"secret/data/meridian/hindsight_cp_access_key\" }}{{ .Data.data.value }}{{ end }}"
  destination = "/etc/meridian/hindsight_cp_access_key"
  perms       = 0400
  error_on_missing_key = true
}

# /opt/apisix/.env-apisix.vault — tüketici: apisix.service (docker --env-file, ikinci dosya — drop-in 50-vault-yan-dosya.conf; root okur)
template {
  contents    = <<EOT
APISIX_ADMIN_KEY={{ with secret "secret/data/meridian/apisix_admin_key" }}{{ .Data.data.value }}{{ end }}
OPENROUTER_API_KEY={{ with secret "secret/data/meridian/HINDSIGHT_API_LLM_API_KEY" }}{{ .Data.data.value }}{{ end }}
OPENROUTER_AUTH=Bearer {{ with secret "secret/data/meridian/HINDSIGHT_API_LLM_API_KEY" }}{{ .Data.data.value }}{{ end }}
PANO_GIRIS_PAROLA={{ with secret "secret/data/meridian/pano_giris_parola" }}{{ .Data.data.value }}{{ end }}
BOT_KEY_BEKCI={{ with secret "secret/data/meridian/bot_key_bekci" }}{{ .Data.data.value }}{{ end }}
BOT_KEY_KARNE={{ with secret "secret/data/meridian/bot_key_karne" }}{{ .Data.data.value }}{{ end }}
BOT_KEY_SEF={{ with secret "secret/data/meridian/bot_key_sef" }}{{ .Data.data.value }}{{ end }}
BOT_KEY_MERIDIAN={{ with secret "secret/data/meridian/kapi_apikey" }}{{ .Data.data.value }}{{ end }}
EOT
  destination = "/opt/apisix/.env-apisix.vault"
  perms       = 0400
  error_on_missing_key = true
}

# /opt/hindsight/.env.vault — tüketici: hindsight-api.service (EnvironmentFile, ikinci dosya — drop-in 51-vault-yan-dosya.conf; systemd PID 1 olarak root okur)
template {
  contents    = <<EOT
HINDSIGHT_API_REFLECT_LLM_1_API_KEY={{ with secret "secret/data/meridian/HINDSIGHT_API_LLM_API_KEY" }}{{ .Data.data.value }}{{ end }}
HINDSIGHT_API_REFLECT_LLM_2_API_KEY={{ with secret "secret/data/meridian/HINDSIGHT_API_LLM_API_KEY" }}{{ .Data.data.value }}{{ end }}
HINDSIGHT_API_REFLECT_LLM_3_API_KEY={{ with secret "secret/data/meridian/HINDSIGHT_API_LLM_API_KEY" }}{{ .Data.data.value }}{{ end }}
HINDSIGHT_API_CONSOLIDATION_LLM_1_API_KEY={{ with secret "secret/data/meridian/HINDSIGHT_API_LLM_API_KEY" }}{{ .Data.data.value }}{{ end }}
HINDSIGHT_API_CONSOLIDATION_LLM_2_API_KEY={{ with secret "secret/data/meridian/HINDSIGHT_API_LLM_API_KEY" }}{{ .Data.data.value }}{{ end }}
HINDSIGHT_API_CONSOLIDATION_LLM_3_API_KEY={{ with secret "secret/data/meridian/HINDSIGHT_API_LLM_API_KEY" }}{{ .Data.data.value }}{{ end }}
EOT
  destination = "/opt/hindsight/.env.vault"
  perms       = 0400
  error_on_missing_key = true
}

# /opt/hindsight/.env-cp.vault — tüketici: hindsight-cp.service (EnvironmentFile → docker -e AD, değer ortamdan — argv'de yok; ikinci dosya — drop-in 50-vault-yan-dosya.conf; systemd PID 1 olarak root okur)
template {
  contents    = <<EOT
HINDSIGHT_CP_ACCESS_KEY={{ with secret "secret/data/meridian/hindsight_cp_access_key" }}{{ .Data.data.value }}{{ end }}
HINDSIGHT_CP_DATAPLANE_API_KEY={{ with secret "secret/data/meridian/HINDSIGHT_API_TENANT_API_KEY" }}{{ .Data.data.value }}{{ end }}
EOT
  destination = "/opt/hindsight/.env-cp.vault"
  perms       = 0400
  error_on_missing_key = true
}
