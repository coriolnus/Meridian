# Sır Yönetimi Kademeli YOL-1 — Hazırlık Belgesi (TSK-064)

**Tarih:** 2026-09-03 gece (Rol-1, operatör gece yetkisi; canlıya DOKUNULMADI — belge + envanter).
**Emsal:** TSK-049 / `deploy/oracle-a1/dash_token_credential.sh` (pano token'ı: rotasyon + `LoadCredential`
faz-1 canlı, faz-2 uygulama-şartlı). **Üst kayıt:** ROADMAP §4 mimari madde 7 (BEKLEMEDE-7: OpenBao/unseal → 2026-09-07 KARARLI: HashiCorp Vault, §6
adımı operatörde — bu belge o adımı GEREKTİRMEZ, ondan önceki basamaktır).

## 1. Envanter (2026-09-03 21:5x UTC, A1; yalnız DEĞİŞKEN ADLARI okundu — değerler hiçbir terminale basılmadı)

| Dosya | mod / sahip | Değişken | Sır mı? | Tüketici | Kanal bugün |
|---|---|---|---|---|---|
| `/opt/meridian/.env` | 600 / ubuntu | NOUS_MODEL · NOUS_ENDPOINT · MERIDIAN_FMP_BASE | yapılandırma (sır kalmadı — ölçüldü 2026-09-08 10:5xZ) | meridian.service | EnvironmentFile |
| `/opt/meridian/.dash.env` | 600 / ubuntu | MERIDIAN_DASH_TOKEN | SIR | meridian.service | EnvironmentFile (faz-2'de kapanacak) |
| `/opt/hindsight/.env` | 600 / ubuntu | HINDSIGHT_API_REFLECT_LLM_1_API_KEY · HINDSIGHT_API_REFLECT_LLM_2_API_KEY · HINDSIGHT_API_REFLECT_LLM_3_API_KEY | SIR ×3 (hafıza failover zinciri, 2026-09-06'dan beri; her üye OPENROUTER anahtarının birebir kopyası) | hindsight-api.service | EnvironmentFile |
| | | HINDSIGHT_API_CONSOLIDATION_LLM_1_API_KEY · HINDSIGHT_API_CONSOLIDATION_LLM_2_API_KEY · HINDSIGHT_API_CONSOLIDATION_LLM_3_API_KEY | SIR ×3 (aynı zincirin konsolidasyon yüzeyi) | hindsight-api.service | EnvironmentFile |
| | | diğer 29 (LLM/embedder/reranker/DB havuzu/…) | yapılandırma | hindsight-api.service | EnvironmentFile |
| `/etc/hindsight/creds/<AD>` | 0400 / root | HINDSIGHT_API_DATABASE_URL · HINDSIGHT_API_LLM_API_KEY · HINDSIGHT_API_TENANT_API_KEY | SIR ×3 (dosyanın ADI değişkenin adıdır) | hindsight-api.service (LoadCredential + ExecStart sarmalayıcı) · meridian.service (pano vekili, yalnız TENANT) | LoadCredential |
| `/opt/hindsight/.env-cp` | 600 / root | HINDSIGHT_CP_ACCESS_KEY · HINDSIGHT_CP_DATAPLANE_API_KEY | SIR | hindsight-cp.service (docker) | docker env-file |
| `/opt/apisix/.env-apisix` | **640** / root | APISIX_ADMIN_KEY · OPENROUTER_API_KEY · OPENROUTER_AUTH · PANO_GIRIS_PAROLA · BOT_KEY_{BEKCI,KARNE,SEF,MERIDIAN} | SIR ×8 | apisix.service (docker, `$env://` çözümü) · `ops/apisix_uygula.py` (admin anahtarı) | EnvironmentFile → docker run env |
| `~/.hermes/profiles/<bekci,karne,sef>/.env` | (ölçülmedi) | BOT_KEY_<AD> · OPENROUTER_API_KEY | SIR | hermes bot birimleri (timer'lı oneshot) | HERMES_HOME/.env (hermes env_loader) |

**ÖLÇÜM GÜNCELLEMESİ — 2026-09-08 (A1, yalnız AD varlığı okundu; değer basılmadı).** Tablo
2026-09-03 ölçümüdür ve üç yerde EKSİLDİ/ARTTI. Satırlar tarihiyle birlikte düzeltildi, çünkü bu
tablo bir arşiv değil, `deploy/sir_envanteri.yaml` ile çivilenmiş TEK KAYNAKtır ve bayat bir tek
kaynak, ayrışma çivisini "her şey uyuşuyor" diye yeşil tutar:
1. **`/opt/hindsight/.env`den ÜÇ SIR ÇIKTI.** `HINDSIGHT_API_DATABASE_URL` ·
   `HINDSIGHT_API_LLM_API_KEY` · `HINDSIGHT_API_TENANT_API_KEY` bu dosyada ARTIK YOK (09:3xZ
   ölçümü: üçünün de satır sayısı 0); Faz-1A/`LoadCredential` geçişi 2026-09-07'de tamamlandı ve
   üçü yalnız `/etc/hindsight/creds/<AD>` kaynak dosyalarında + `/run/credentials` altında yaşıyor.
   Bu yüzden yeni bir dosya satırı açıldı — "nerede YOK" ile "nerede VAR" iki ayrı gerçektir.
2. **`/opt/hindsight/.env`e ALTI SIR GİRDİ.** Hafıza failover zincirinin üye anahtarları
   (EDG-2026-080/081, 2026-09-06). Zincir ÜYESİ ana anahtarı DEVRALMAZ: her üye kendi
   `_API_KEY` satırını okur ve altısı da OpenRouter anahtarının birebir kopyasıdır — yani
   rotasyon kapsamına GİRERLER (`deploy/oracle-a1/sir_rotasyon.sh --kopyalar`).
3. **hermes profillerine `OPENROUTER_API_KEY` eklendi** (ölçüm 2026-09-07 22:0xZ; `sir_envanteri.yaml`
   rotasyon bloğunda beyanlıydı, §1'de açık kalemdi).
4. **`/opt/meridian/.env`den ÜÇ SIR ÇIKTI.** `NOUS_API_KEY` · `KAPI_APIKEY` ·
   `MERIDIAN_DASH_TOKEN` bu dosyada ARTIK YOK — Rol-1 ölçümü, A1, 2026-09-08 10:0xZ ve 10:5xZ:
   üçünün de satır sayısı **0**, ve `_TOKEN|_API_KEY|_APIKEY|_SECRET|_PASSWORD|_PAROLA` sonek
   taramasında bu dosyada **hiçbir** sır adı bulunamadı (yalnız ADLAR okundu; değer basılmadı).
   Üçü yalnız kendi kanallarında yaşıyor: NOUS/KAPI `LoadCredential`
   (`/etc/meridian/{nous_api_key,kapi_apikey}`, Faz-1B 2026-09-07 gecesi tamamlandı),
   `MERIDIAN_DASH_TOKEN` ise `.dash.env` + `/etc/meridian/dash_token` (TSK-049 faz-1).
   Dosya satırı KALDI — dosya duruyor ve üç YAPILANDIRMA değişkeni taşıyor; "dosya yok" ile
   "dosyada sır yok" iki ayrı gerçektir ve faz-2'nin ayrımı ikincisine bakar.

**ÖLÇÜLMEYEN, DOLAYISIYLA DEĞİŞTİRİLMEYEN TEK SATIR (uydurma yasağı):** `diğer 29` ayar
sayısı 2026-09-03 ölçümüdür ve 2026-09-08'de YENİDEN SAYILMADI — yalnız sır ADLARININ varlığı
ölçüldü. (Bu paragrafın 2026-09-08 sabahki ikinci maddesi — `/opt/meridian/.env`in
`NOUS_API_KEY`/`KAPI_APIKEY` satırları — 10:5xZ'de ÖLÇÜLDÜ ve yukarıdaki 4. madde onun yerini
aldı: ölçülmüş bir gerçeği "ölçülmedi" diye beyan etmek, bayat tek kaynağın en sessiz hâliydi.)

**Bulgu-1 (hemen):** `.env-apisix` 640 — grup okuyabilir; diğer sır dosyaları 600. Tek satır: `chmod 600`
(docker `EnvironmentFile`'ı root okur, grup gerekmez). Sabah penceresinde, F9 beyanıyla.
**Bulgu-2 (KAPANDI — ölçüldü 2026-09-08 10:5xZ):** MERIDIAN_DASH_TOKEN 2026-09-03'te iki dosyadaydı
(motor `.env` + `.dash.env`) — tek-kaynak ihlali. Motor `.env`'deki kopya ARTIK YOK (satır sayısı 0),
yani bulgunun istediği şey olmuş durumda; `.dash.env` + `/etc/meridian/dash_token` ikilisi TSK-049
faz-2'nin kendi kalemidir ve bu bulguya değil ona bakar. NOT: motorun KENDİ sır deposu
(`state/secrets.json`) hâlâ bir `MERIDIAN_DASH_TOKEN` kopyası taşır — o kopya rotasyon tablosunda
BEYAN DIŞIDIR ve `sir_rotasyon.sh --envanter` onu her koşumda bağırır (beyanlı, kalıcı kayıt
2026-09-06: kimlikler `secrets.json`da yaşar).
**Bulgu-3:** hindsight TENANT_API_KEY'i pano vekili DOSYADAN okuyor (`meridian/api.py::_env_anahtari`);
LoadCredential'a geçince vekilin okuma yolu `$CREDENTIALS_DIRECTORY`ye taşınmalı (kod değişikliği, tam suite).

## 2. Sınıflandırma ve hedef kanal

| Sınıf | Bugün | YOL-1 hedefi | Not |
|---|---|---|---|
| A · systemd-doğal süreçler (meridian, hindsight-api) | EnvironmentFile | **LoadCredential** (sır ortama girmez; `$CREDENTIALS_DIRECTORY/<ad>`) | emsal hazır; uygulama tarafı: `os.environ[...]` → credential dosyası okuyucu (tek yardımcı, iki serviste) |
| B · docker-sarmalı süreçler (apisix, hindsight-cp) | EnvironmentFile → `docker run -e` | LoadCredential + ExecStart sarmalayıcı (`$CREDENTIALS_DIRECTORY`den okuyup `--env` verir; ortamda yine görünür ama HOST birimi ortamına girmez) | docker'ın kendi secret'ı swarm ister — YOK; yarım kazanım, dürüstçe beyan |
| C · hermes profil `.env` | HERMES_HOME/.env | DEĞİŞMEZ (hermes env_loader sözleşmesi; TSK-105 ölçümü) | Vault Agent template ile kapsanır (Faz-2, §6.3) — CLI kodu değişmez |
| D · yapılandırma (sır değil) | EnvironmentFile | KALIR | sır/ayar ayrımı dosya düzeyinde: sır dosyası ayrı, ayar dosyası ayrı (hindsight `.env` 32 → 3 + 29) |

## 3. Fazlar (her faz kendi canary'si ve geri-alımıyla; hiçbiri bu belgeyle uygulanmaz)

1. **Faz-0 (sabah, 5 dk, risksiz):** `.env-apisix` 600; envanter bu belgeye çivilenir (test: dosya
   adları + değişken adları listesi repo beyanıyla eşleşir — `deploy/sir_envanteri.yaml` üretilir,
   F9 kapısı içerik yerine AD listesi kıyaslar; değer asla).
2. **Faz-1A (hindsight-api):** `HINDSIGHT_API_{DATABASE_URL,LLM_API_KEY,TENANT_API_KEY}` →
   `/etc/hindsight/creds/<ad>` (0600 root) + `LoadCredential=` ×3; hindsight-api upstream kodu
   env okur → sarmalayıcı `ExecStart` credential'ları ortama koyar (B sınıfı yarım kazanım) YA DA
   `HINDSIGHT_API_*` için upstream `_FILE` desteği ölçülür (varsa tam kazanım). Ölçüm önce.
   Vekil (`api.py`) TENANT anahtarını credential dosyasından okur (kod + v375 çivisi + tam suite).
3. **Faz-1B (meridian):** NOUS_API_KEY + KAPI_APIKEY → LoadCredential; `meridian/hermes.py::_nous_headers()` (belgenin ilk sürümü `nous.py` demişti — dosya adı yanlıştı, 2026-09-07 düzeltildi)
   okuma yolu credential-önce, env-yedek (geçiş penceresi), sonra env kapanır (TSK-049 faz-2 deseni).
4. **Faz-1C (apisix/cp):** sarmalayıcı ExecStart; `$env://` çözümü aynen; `ops/apisix_uygula.py`
   admin anahtarını credential dosyasından okur.
5. **Faz-2:** ~~BEKLEMEDE-7 (OpenBao/unseal) — operatörde; bu belgenin kapsamı dışı.~~ **KARARLI 2026-09-07 (operatör K6/K6b): HashiCorp Vault, otomatik unseal, anahtar dosyası A1'de — bkz. §6 (Faz-2 eki).**

## 4. Kapılar / bedel
- Her faz: rotasyon + kanal geçişi AYNI pencerede (TSK-049 hükmü: eski kanal geçerliyken yeni
  kanal ölçülemez). Canary: `systemctl show <birim> -p LoadCredential` + servis açılıyor + iş
  yapıyor (health/ilk istek) + `/proc/<pid>/environ`da sır YOK (grep -c 0).
- Bedel: docker sınıfında sır konteyner ortamında kalır — beyanlı; tam kapanış Vault'la (Faz-2, §6).
- Sır DEĞERİ hiçbir aşamada terminale/loga basılmaz (2026-09-02 DATABASE_URL vakası: süzgeç
  kara-liste değil beyaz-liste — hafıza kaydı).

## 5. Sonraki adım (operatör kararı)
Faz-0 sabah penceresinde (chmod + envanter çivisi); Faz-1A/1B tek dalga (motor + hindsight kodu, tam
suite, dağıtım penceresi). Onay: ROADMAP TSK-064 status notu.

## 6. Faz-2 eki — HashiCorp Vault (2026-09-07, Rol-1; operatör kararı K6/K6b aynı gün 10:30/10:34Z)

**Karar (verbatim):** "Hashicorp Vault kullanmak istiyorum"; unseal "Otomatik: anahtar dosyası A1'de". OpenBao, OCI KMS oto-unseal ve
elle unseal seçilmedi. BEKLEMEDE-7 kapandı. Faz-0/1A/1B/1C AYNEN ve ÖNCE (tek dalga, gelecek hafta); Faz-2 ayrı dalga, kendi planıyla
(`docs/superpowers/plans/`), implementer brief'i birim dosyaları + ops betiği için, A1 kurulumu Rol-1. Girdi: salt-okunur ajan taraması
(2026-09-07 12:0xZ) + bu belgenin §1-§4'ü. Aşağıdaki hükümler Rol-1'indir; "ölçülür" yazan her madde kurulum günü ölçülmeden geçilmez.

### 6.1 Kurulum (A1, Ubuntu 24.04 aarch64)
- **İkili, pinli sürüm** (`releases.hashicorp.com/vault/<sürüm>/vault_<sürüm>_linux_arm64.zip` → `/usr/local/bin/vault`, sha256 kayıtlı).
  apt deposu seçilmedi: sessiz sürüm atlaması sınıfı risk (pytest-xdist pini, systemd sürüm kapısı emsali). Sürüm ve sha kurulum günü
  ROADMAP TSK-064 notuna yazılır. **Lisans kapısı:** indirilen sürümün LICENSE dosyası (BSL 1.1) kurulumdan ÖNCE okunur; "rekabet eden
  barındırılmış hizmet" yasağı bizim kullanımı (iç sır deposu) kapsamıyorsa geçilir — bu belge çıkarımı doğrulamış SAYILMAZ.
- **Depolama:** `storage "file" { path = "/opt/vault/data" }` — tek düğüm, HA yok (A1 tek makine; SQLite+WAL deseniyle aynı sınıf).
  Disk: kurulum günü `df -h /` ölçülür; yedek: `/opt/vault/data` litestream KAPSAMI DIŞI, günlük tar+sha ile `backups/` sınıfına
  (yedek de sır taşır: 0600, dağıtıma binmez — dagit `backups` zaten dışlıyor).
- **Dinleme:** `127.0.0.1:8200`, `tls_disable = true` (düz HTTP loopback). Gerekçe: pano da TLS'siz loopback (`MERIDIAN_BIND_HOST`
  zorlaması); self-signed CA'nın her tüketiciye dağıtımı yeni bir yüzey. Bedel beyanı: aynı makinede başka yerel süreç trafiği görebilir —
  A1 tek kullanıcı (ubuntu) + servisler `ProtectSystem=strict`; kabul. Dışa açılmaz (0.0.0.0 YASAK, `ss -ltnp` ile kurulum günü ölçülür).
- **Birim:** `vault.service` — meridian.service sertleştirme bloğu aynen (NoNewPrivileges, ProtectSystem=strict, CapabilityBoundingSet boş
  + `AmbientCapabilities=CAP_IPC_LOCK` yalnız mlock için, RestrictAddressFamilies=AF_INET AF_UNIX, SystemCallFilter=@system-service);
  `User=vault`, `ReadWritePaths=/opt/vault/data`.

### 6.2 init / unseal
- **Shamir 1/1**: tek payda, tek dosya — operatör "anahtar dosyası" (tekil) dedi; aynı dizinde 3 payda "dağıtık güvenlik" vermez, yalnız
  operasyon yükü ekler. Dosya: `/etc/vault/unseal.key`, **root:root 0400** (operatörün "0600" niyeti = yalnız sahip okur; 0400 daha dar,
  emsal `/etc/meridian/dash_token`). Kök jeton `/etc/vault/root.token` 0400 — yalnız bootstrap; politika/AppRole kurulunca İPTAL edilir,
  yerine dar bir yönetici jetonu (`vault token create -policy=meridian-admin`, TTL'li) — iptal ve yeni jeton ROADMAP notuna (değer değil).
- **Otomatik unseal:** `vault.service` içinde `ExecStartPost=/opt/vault/vault_unseal.sh` (API ayağa kalkana kadar bekler — `_servis_ayakta`
  deseni, `dash_token_credential.sh` şablonu — sonra `vault operator unseal $(cat /etc/vault/unseal.key)`; değer argv'ye DEĞİL stdin'e).
  Böylece crash/reboot sonrası her açılışta unseal kendiliğinden olur (`After=` tek başına sıralama verir, tetikleme vermez — ajan bulgusu).
  Ek: `vault-unseal.service` (oneshot) elle/timer tekrarı için; **bekçi**: `/v1/sys/health` 503 (sealed) → `VAULT_SEALED` alarm sınıfı
  (RUNBOOK üretici + korpus yeniden üretilir — üretilmiş-belge zinciri), ölçüm önce (kod Faz-2b).
- Birim kurulduğu gün ÜÇ birim de elle test-ateşlenir (§9: "kurulu ≠ çalışır"): `systemctl restart vault` → `vault status` `Sealed false`.

### 6.3 Tüketim — Vault Agent + template → dosya (Seçenek 2)
- Ayrı `vault-agent.service` (User=vault-agent, AppRole ile login; `auto_auth` + `template` blokları) DÜZ DOSYALAR üretir:
  `/etc/meridian/dash_token`, `/etc/hindsight/creds/<ad>`, `/opt/apisix/.env-apisix`, `~/.hermes/profiles/<ad>/.env`. Sınıf A/B/C
  okuma kodu DEĞİŞMEZ: LoadCredential kaynak dosyaları artık Agent'tan gelir (Faz-1A/1B yatırımı korunur), hermes CLI kendi `.env`ini
  okumaya devam eder (TSK-105 env_loader sözleşmesi bozulmaz). Render aralığı = rotasyon gecikmesi (dakika sınıfı; ölçülür, kabul).
- **Sıfırıncı sır (bootstrap):** Agent'ın AppRole `role_id` (sır değil) + `secret_id` `/etc/vault/agent.secret-id` root:root 0400,
  `secret_id_num_uses=0`, `secret_id_ttl=0` (dönmez; rotasyonu elle, `vault write -f auth/approle/role/agent/secret-id`). Beyan: aynı
  makinede iki kök-dosya (unseal.key + agent.secret-id) — operatörün "anahtar dosyası A1'de" kararıyla aynı güven sınıfı; response-wrapping
  eklenmez (tek makine, taşıma yok).
- **GCP Secret Manager — KANAL KAPANDI (IaC-K5, 2026-09-07), bu madde artık TARİHÇEDİR.** Bu belge 2026-09-03'te
  `meridian/secrets.py::_fetch`in bulut basamağının "Faz-2 canary geçene kadar KALIR"ını yazıyordu (iki kanal aynı anda canlı ilkesi) ve
  kapatmayı Faz-2c'ye erteliyordu. Operatör kararı o beklemeyi geçersiz kıldı: basamak SİLİNDİ ve `secrets.KAYNAKLAR` üç adımdır
  (credential → env → dosya). **Faz-2c'nin "eski kanalı kapat" adımı düştü**; kapatılacak bir kanal yok. `deploy/push_secret.sh` de
  SİLİNDİ — yerine gelecek yazıcı yine `deploy/vault_sir_koy.sh`tir (aynı `read -s` disiplini: değer argv/log'a girmez), ama artık
  "eski betik Faz-2c'ye kadar kalır" diye bir geçiş penceresi YOKTUR. Çivi: `tests/test_gcp_yolu_kaldirildi_v448.py`.
- Politikalar: tüketici başına ayrı policy (`meridian-motor`, `hindsight-api`, `apisix`, `hermes-<profil>`) — yalnız kendi yolunu okur;
  `ALLOWED` frozenset'i (secrets.py) Vault yol listesinin TEK kaynağı olur (tek-kaynak yasası: policy dosyaları ondan üretilir, çivi ile).

### 6.4 Geri alım, canary, kapılar
- **Geri alım:** `vault-agent` durdur → Agent'ın ürettiği dosyalar yerine elle son bilinen iyi kopya (Agent yazmadan önce alınan `.bak`,
  0400) → tüketiciler LoadCredential/.env ile aynen okur; `vault.service` durdurulsa bile tüketiciler etkilenmez (dosya kanalı). Bu, iki-kanal
  ilkesinin Faz-2 hâlidir: Vault kanalı EKLENİR, dosya kanalı zaten hedef biçimdir.
- **Canary (farksal ölçüm, `dash_token_credential.sh::faz2` deseni):** Vault'a gerçek değer, eski kaynağa sahte değer → tüketici
  200 veriyorsa dosyayı GERÇEKTEN Agent yazıyor; `/proc/<pid>/environ` grep 0; `vault status` Sealed false; `systemctl show <birim> -p
  LoadCredential`. **ESKİ AYAK ARTIK ENV/DOSYADIR** (IaC-K5, 2026-09-07): tasarım "GCP/env" diyordu, bulut ayağı silindi — farksal ölçümün
  karşı tarafı ortam değişkeni ya da `state/secrets.json`dur. Var olmayan bir kanala sahte değer koymaya çalışmak canary'yi tanımsız kılardı.
- **Kapılar:** lisans (6.1) · disk ölçümü · `ss -ltnp` yalnız 127.0.0.1 · üç birim elle test-ateşleme · tam suite (secrets.py policy
  üretimi + çivi) · dağıtım reçetesi (§9) — Agent'a bağlama adımı meridian/hindsight restart'ı ister, worker o an durur (seans dışı pencere).
- **Bedel yasası:** kazanç = merkezi kasa, rotasyon, denetim izi, bot profillerinin de kapsanması; bedel = iki yeni süreç (CPU/RAM ölçülür),
  iki kök-dosya, render gecikmesi, BSL lisansı. Beyanla kabul; ölçümler kurulum günü ROADMAP'e.
