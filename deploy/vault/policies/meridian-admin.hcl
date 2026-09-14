# ÜRETİLDİ — ELLE DÜZENLEME YAPMA.
# Kaynak : deploy/sir_envanteri.yaml (vault_kv + vault_dosyalar blokları)
# Üreten : ops/vault_politika_uret.py — deterministik, damgasız (her koşu aynı bayt)
# Tazelik: python ops/vault_politika_uret.py --kontrol   (çıkış 1 = bayat)
#
# Bu dosyayı düzenlersen bir sonraki üretim değişikliği siler. Değişmesi gereken şey
# envanterdir: yeni bir sır oraya girer, bu dosya yeniden üretilir.


# Yönetim politikası — kök jetonun YERİNE geçer (kök iptal edilir).

# sır DEĞERLERİ: koy/oku/güncelle/sil (vault_sir_koy.sh bu yolu kullanır)
path "secret/data/meridian/*" {
  capabilities = ["create", "read", "update", "delete"]
}

# KV-v2 meta: sürüm listesi ve kalıcı silme AYRI yoldur (data/ ile karıştırmak 'sildim ama duruyor' üretir)
path "secret/metadata/meridian/*" {
  capabilities = ["read", "list", "delete"]
}

# mühür durumu — operatörün `vault status` çağrısı
path "sys/health" {
  capabilities = ["read"]
}

# Agent'ın secret-id'sini ELLE yenileme yolu (secret_id_ttl=0, kendiliğinden dönmez)
path "auth/approle/role/agent/secret-id" {
  capabilities = ["update"]
}
