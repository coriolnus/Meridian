# =================================================================================================
# vault.hcl — HashiCorp Vault sunucu yapılandırması (TSK-064 Faz-2, A1 Oracle Ampere)
# =================================================================================================
# HEDEF: /etc/vault/vault.hcl (0640 root:vault). Kurulumu deploy/vault/vault_kur.sh yapar; bu
# dosya DEPODA yaşar ve canlıya elle kopyalanır ([F9] içerik kapısı onu her dağıtımda kıyaslar).
#
# BU DOSYADA SIR YOKTUR ve olmayacaktır: unseal anahtarı, kök jetonu ve AppRole secret-id AYRI
# dosyalardadır (0400 root:root). Bir yapılandırma dosyasının okunabilir olması gerekir; bir sır
# dosyasının olmaması. İkisini aynı dosyaya koymak, ikisinin de iznini yanlış yapardı.
#
# NEDEN DOSYA DEPOSU (tasarım §6.1): A1 tek makinedir, HA yoktur. Aynı sınıf karar `state/`in
# SQLite+WAL'inde de verildi. Yedek `backups/` sınıfına girer (günlük tar+sha) ve dağıtıma
# BİNMEZ — rsync `backups`ı zaten dışlıyor.

# -------------------------------------------------------------------------------------------------
# DİNLEME — YALNIZ LOOPBACK. Bu satır bu dosyanın en yüksek bahisli satırıdır.
# -------------------------------------------------------------------------------------------------
# `0.0.0.0` YASAK (tasarım §6.1). A1'in genel IP'sinde dinleyen bir sır kasası, bütün Faz-1
# kazanımını (sır ortama girmesin) tek satırda geri alırdı. Kurulum günü `ss -ltnp` ile ÖLÇÜLÜR;
# çivi: tests/test_vault_faz2_v485.py bölüm A.
#
# TLS YOK ve bu bir KARARDIR, unutulmuş bir varsayılan değil (tasarım §6.1, bedel beyanlı):
# pano da TLS'siz loopback dinler (MERIDIAN_BIND_HOST zorlaması) ve self-signed bir CA'yı her
# tüketiciye dağıtmak YENİ bir yüzeydir. BEDEL: aynı makinedeki başka bir yerel süreç trafiği
# görebilir. A1 tek kullanıcı (ubuntu) + servisler ProtectSystem=strict → kabul edildi.
listener "tcp" {
  address     = "127.0.0.1:8200"
  tls_disable = true
}

# -------------------------------------------------------------------------------------------------
# DEPOLAMA — tek düğüm, dosya arka ucu
# -------------------------------------------------------------------------------------------------
# Dizin 0700 vault:vault. `vault.service` ReadWritePaths'te YALNIZ bu yol vardır: kasa süreci
# makinede başka hiçbir yere yazamaz.
storage "file" {
  path = "/opt/vault/data"
}

# -------------------------------------------------------------------------------------------------
# API adresi — Agent ve bekçi bu adresi kullanır (tek kaynak: yukarıdaki listener)
# -------------------------------------------------------------------------------------------------
api_addr = "http://127.0.0.1:8200"

# UI KAPALI: bir tarayıcı yüzeyi bu kurulumda hiçbir şey kazandırmaz (operatör kasaya ssh ile
# ulaşır) ama saldırı yüzeyi ekler.
ui = false

# mlock AÇIK (disable_mlock yazılmaz = varsayılan false): Vault bellek sayfalarını diske
# takas ettirmez. Bunun bedeli `vault.service`teki TEK yetenektir (AmbientCapabilities=
# CAP_IPC_LOCK) ve birim dosyasında gerekçesiyle yazılıdır.

# -------------------------------------------------------------------------------------------------
# KURTARMA KÖKÜ — `generate-root` JETONSUZ (ölçülen arıza, A1 2026-09-14 10:1xZ, Rol-1)
# -------------------------------------------------------------------------------------------------
# Vault 2.0'dan beri `sys/generate-root/*` VARSAYILAN OLARAK kimlik doğrulaması ister
# (CVE-2026-5807: jetonsuz bir yerel süreç tek "devam eden işlem" yuvasını işgal edip meşru
# operatörü engelleyebiliyordu — DoS). Bu kurulumda o kapının kapalı kalması kasanın TEK kurtarma
# yolunu kapatır: kök jetonu iptal edildikten (vault_kur.sh adım 11) sonra yönetici jetonu
# kaybolur/süresi dolarsa unseal anahtarı tek başına HİÇBİR şey açamaz ve kasa yeniden KURULMAK
# zorunda kalır (ölçüldü: kök iptali ÇOCUK yönetici jetonunu da götürdü, generate-root 403 döndü).
# KARAR: yalnız "generate-root" ailesi jetonsuz açılır — "rekey" ve "generate-operation-token"
# KAPALI kalır. BEDEL: aynı makinedeki yerel bir süreç generate-root yuvasını meşgul edebilir
# (DoS); dinleyici yalnız loopback (yukarıda) ve tamamlamak için 0400 root unseal anahtarı
# gerekir → kabul edildi. Çivi: tests/test_vault_faz2_v485.py §A5 (liste TAM OLARAK bu tek aile).
enable_unauthenticated_access = ["generate-root"]
