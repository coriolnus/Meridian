# TASARIM — Altyapı-kod: Terraform ve Ansible Meridian'da hangi bileşenlerin yerine geçebilir? (TSK-176)

**Tarih:** 2026-09-08 · **Rol-1 sentezi (H1)** · **Kod YOK — operatör kararı bekler (§8)** · **Operatör soruları (2026-09-08 00:xx–01:xx local):**
"otomasyon tarafımız için terraform mantıklı mı" → "developer.hashicorp.com/terraform/docs dokümanlarını detaylı inceleyip daha fazla nasıl
kullanılabilir değerlendir, sistemin birçok bileşeni var" → "aynı şeyi ansible için de yap (docs.ansible.com)" → "terraform ve ansible sistem
içindeki hangi bileşenleri replace edebilir, detaylı incele, sadece dagit.sh için değil".

**Yöntem:** 4 Terraform + 3 Ansible salt-okunur araştırma ajanı (resmi dokümanlar WebFetch ile; okunamayan sayfalar "doğrulanmadı" listesinde),
Rol-1'in doğrudan okumaları (import blokları, ephemeral kaynaklar, APISIX Terraform sağlayıcısı deposu), depodaki TÜM operasyon mekanizmalarının
envanteri (1 ajan: dagit.sh, serve.sh, deploy/*, ops/* altyapı betikleri, CI, günlük/ROADMAP elle-adım grep'i). Uydurma yasağı: ölçülmeyen
şey "ölçülemedi"; eğitim bilgisi "doğrulanmadı" damgalı (§Ek-B).

---

## 0. Hüküm (özet)

| Katman | Araç | Yerine geçtiği şey | Kalan |
|---|---|---|---|
| Bulut kaynakları (A1 VM, /opt/veri blok hacmi, nesne deposu, NSG/güvenlik listesi, IAM; ileride Vault KMS/IAM) | **Terraform, import-first** | Oracle konsolundan elle yapılan her şey + ölü `deploy/gcp_provision.sh`'ın OCI eşdeğeri | VM-içi hiçbir şey |
| **APISIX kapı yapılandırması** (rota, upstream, tüketici anahtarı, eklenti, TLS) | **Terraform `apisix` sağlayıcısı** (rework-space-com, APISIX 3.15 test) | `ops/apisix_uygula.py` + `apisix_ssl_yukle.py` (kendi yazdığımız "PUT + drift denetimi") | `deploy/apisix/routes.yaml` HCL'e döner; drift = `plan -detailed-exitcode` |
| **Vault (Faz-2) YAPILANDIRMASI** (mount, policy, AppRole, KV) | **Terraform `vault` sağlayıcısı** + ephemeral kaynaklar | (henüz yok) | Vault'un KURULUMU Ansible rolü |
| VM-içi durum: paketler, systemd birimleri/timer'lar/drop-in'ler, polkit, unattended-upgrades, venv'ler, docker konteynerleri (APISIX/etcd/Hindsight-CP), litestream, model önbelleği, bot kum havuzları, sır dosyaları 0400 | **Ansible rolü (tek host)** | `deploy/oracle-a1/deploy.sh` (694 satır), dagit `[1c]` "yalnız raporla" duruşu + elle `install` (bu gece 4 birim + 3 drop-in), `litestream_kur.sh`'ın sha kapısı (`get_url checksum`), `docker run --rm` ExecStart'ları (`docker_container`), hermes config "üzerine yazma+yedekle" (`copy backup`) | **Postgres kurulumu** (repoda hiç yok — ölçüldü, ilk kez kod hâline gelir) |
| Uygulama dağıtımı (kod) | **dagit.sh KALIR, içi Ansible'a devredilir** | `[2]` rsync → `synchronize`, `[3]` uv sync → `command creates/changed_when`, `[4]` bakım penceresi → `systemd` + `block/rescue`, `[5]` healthz → `uri until/retries` | Kapılar: temiz ağaç, uv audit, lint-imports, dev-grubu, [1b] versiyonlu state farkı, F9/F10, [5a-5c], [B] dağıtım kaydı, RUNBOOK zinciri |
| İlk önyükleme (boş VM) | **cloud-init user-data** (yalnız köprü: ssh anahtarı, python3, ubuntu+NOPASSWD, blok hacim mount) | RUNBOOK Bölüm A/B elle adımları | Sonrası Ansible |
| Bot profilleri (`hermes profile install`), sır DEĞERİ üretimi/rotasyonu | **ELLE (operatör kararı, tasarım gereği)** | — | Faz-2 Vault Agent template ile dağıtım |

**Tek cümle:** Terraform üç şeyin yerine geçer (bulut kaynakları, APISIX yapılandırması, Vault yapılandırması); Ansible `deploy.sh`'ın ve
dagit'in "kurulum" gövdesinin yerine geçer; Meridian'ın disiplin kapıları ikisine de taşınmaz, dagit.sh'ın sarmalayıcı olarak kalmasıyla korunur.

---

## 1. Terraform — dokümandan ne öğrendik, Meridian'a ne düşer

### 1.1 Dil ve state (developer.hashicorp.com/terraform/language, /state, /backend, /import, /resources/ephemeral, /checks, /tests)
- **Import blokları** (`import { to = …; id = … }` + `terraform plan -generate-config-out`): mevcut A1 kaynakları YENİDEN YARATILMADAN yönetime alınır;
  `for_each` desteklemez. Always-Free Ampere kapasitesi kıt → import-first zorunlu; ilk plan `-refresh-only` ve dikkatli diff ile (üretilen config
  gerçek durumdan sapıyorsa `apply` instance'ı değiştirebilir).
- **State = yeni bir sır deposu**: açık metin JSON; `sensitive = true` yalnız CLI çıktısını gizler. Kural: sır taşıyan hiçbir değer `data` kaynağıyla
  okunmaz; **ephemeral kaynak / write-only argüman** (state ve plan dosyasına hiç yazılmaz) — Faz-2 Vault için tam karşılık.
- **Backend**: local KESİNLİKLE değil (tek makine kilidi, "team/production için önerilmez"; Rol-1 tek-otorite ilkesiyle çakışır). İki seçenek:
  (A) HCP Terraform ücretsiz katman (500 kaynak; uzak state + kilit + run geçmişi; bedel: bir SaaS hesabı daha) · (B) OCI Object Storage'ın
  S3-uyumlu ucu (`backend "s3"` + `endpoints.s3`, `use_path_style`, `use_lockfile`) — resmi belge "best effort", kilidin OCI'de çalıştığı
  DOĞRULANMADI, üretim öncesi sandbox testi şart; ayrıca OCI "Customer Secret Key" gerektirir (Oracle tarafı, doğrulanmadı).
- **check blokları** uyarıdır, apply'ı DURDURMAZ → healthz/servis kapısı olarak Meridian'ın GO/NO_GO sertliğine denk değil; sert kapı için
  `terraform test` (`.tftest.hcl`, mock provider) + harici sağlık betiği. `terraform test` hükmü için pytest'teki "üçlü hüküm"ün ayrı bir
  karşılığı tanımlanmalı (yeni kural, otomatik dahil sayılmaz).
- **moved/removed**: kaynak adı değişince state kaybı yerine açık kayıt; kaynağı elle yönetime bırakırken `removed { lifecycle { destroy=false } }`;
  asla elle `state rm`. CLI **workspaces kullanılmasın** (HashiCorp'un kendi uyarısı: sistem ayrıştırması için değil).
- **`-refresh-only`** periyodik drift taraması olabilir ama refresh'in state'te değiştirdiği alanlar (dinamik IP vb.) Bedel yasasıyla okunmalı.
- **functions**: `templatefile` (birim/rota şablonları), `yamlencode` (profil config), `filesha256` (içerik-adresli tetikleme — §5 kart-blob ilkesiyle aynı desen).

### 1.2 Sağlayıcılar — Meridian bileşeni eşlemesi
| Sağlayıcı | Meridian karşılığı | Uyum | Not |
|---|---|---|---|
| `oracle/oci` | `oci_core_instance` (A1, import), `oci_core_volume` + attachment (/opt/veri), `oci_objectstorage_bucket` (aylık kopya), `oci_core_network_security_group`/security list, `oci_identity_*` (dynamic group/policy; Vault KMS istenirse `oci_kms_*`), instance `metadata.user_data` = cloud-init | **Yerine geçer** (konsol adımları) | Kimlik: A1 üzerinden **Instance Principal** ile çalıştır — statik API anahtarı hiç üretilmez (Rol-1 zaten A1'de ssh ile); OCID'ler sır değil ama versiyonsuz `.tfvars`. Always-Free şekil `VM.Standard.A1.Flex`; kapasite hatası = yaratma yok. |
| `apisix` (rework-space-com/terraform-provider-apisix; kaynaklar: route, upstream, consumer, consumer_group, service, ssl_certificate, global_rule, plugin_config, plugin_metadata, stream_route, secret; `APISIX_ENDPOINT`/`APISIX_API_KEY`) | `deploy/apisix/routes.yaml` + `ops/apisix_uygula.py` (idempotent PUT + EKSİK/AYRIK/BEYANSIZ drift) + `apisix_ssl_yukle.py` | **Yerine geçer** (Rol-1 hükmü: bizim betiğimiz zaten "terraform apply" taklidi) | Topluluk sağlayıcısı (39 commit; bakım riski beyanlı — sürüm pinlenir, plan çıktısı Rol-1 okur). Admin anahtarı `ephemeral`/env, state'e girmez (kaynaklar anahtar taşımaz; tüketici key-auth anahtarı state'e GİRER → ephemeral/write-only ile ya da tüketici anahtarını Vault'ta tutup `secret` kaynağıyla). |
| `hashicorp/vault` | Faz-2: `vault_mount` (kv-v2), `vault_policy` (meridian-motor/hindsight-api/apisix/hermes-<profil> — `secrets.ALLOWED`'dan üretilir, tek kaynak), `vault_auth_backend` approle + `vault_approle_auth_backend_role`, `vault_kv_secret_v2` (ephemeral/write-only ile) | **Yerine geçer** (Vault yapılandırması elle yapılacaktı) | Vault'un kurulumu/init/unseal Terraform'un işi değil (Ansible rolü + `vault operator init` elle, unseal anahtarı 0400). |
| `cyrilgdn/postgresql` | Hindsight DB rolü/veritabanı/yetkileri | Yanına gelir | Kurulum (apt) Ansible; şema Hindsight'ın kendi göçü. Küçük kazanım; ilk turda atlanabilir. |
| `kreuzwerker/docker` | APISIX/etcd/Hindsight-CP konteynerleri | **Uygun değil** (Ansible `community.docker` daha uygun: aynı makine, systemd birimleriyle iç içe) | İki aracın aynı konteyneri yönetmesi tek-kaynak ihlali. |
| `integrations/github` | repo ayarları, dal koruması, Actions sırları | Yanına gelir (isteğe bağlı) | CI'de yalnız plan (HCP VCS entegrasyonu tercih; OCI Workload Identity/OIDC doğrulanmadı). |
| `hashicorp/cloudinit`, `tls`, `random`, `http`, `local`, `null`/`terraform_data` + provisioner'lar | user-data derleme; self-signed (kullanmıyoruz: loopback HTTP); rastgele jeton (ephemeral `random_password`) | provisioner'lar "son çare" (resmi uyarı) — Ansible varken kullanılmaz | — |
| CDKTF | — | **Kullanılmaz** (resmi: 10 Aralık 2025 itibarıyla deprecated) | Düz HCL, tek kök modül. |
| Stacks | — | **Kullanılmaz** (GA ama 500 deployment ölçeği için) | — |

### 1.3 Operasyon modeli (resmi "adoption phases": Meridian = Adopt fazı; Collaborate/Scale/Govern araçları atlanır)
- Yeni `altyapi.sh` (dagit'in YANINA, içine değil): `terraform plan` (Rol-1/ajan salt-okunur) → Rol-1 diff okur → `apply` yalnız Rol-1, dagit §9
  reçetesinin aynısıyla (temiz ağaç, plan çıktısı kayıt, canlı VM'e dokunan kaynaksa bakım penceresi, doğrulama, dağıtım kaydına altyapı satırı).
  CLAUDE.md §2 tablosuna `terraform apply/destroy/state mv|rm` → "Rol-1 miyim?" satırı; ajanlara `plan/show/state list` beyaz listesi (git emsali).
- Drift: A1'de timer ile `terraform plan -detailed-exitcode`; çıkış 2 → bildirim sınıfı "altyapı drift" (push politikası).
- Lisans: BSL 1.1 — iç kullanım (üçüncü tarafa Terraform servisi satılmıyor) serbest görünüyor; FAQ tam metni okunamadı (§Ek-B) → ilk kurulumdan
  önce Rol-1 okur. OpenTofu (MPL) teknik olarak aynı HCL'i koşar — yedek yol.

---

## 2. Ansible — dokümandan ne öğrendik, Meridian'a ne düşer

### 2.1 Çekirdek (docs.ansible.com getting_started / inventory / playbook / vault / roles / config)
- Tek control node (Mac, Rol-1) → tek managed node (A1). Envanter: `deploy/ansible/inventory.ini` tek host (`ansible_host=130.61.126.87`,
  `ansible_user=ubuntu`, anahtar yolu) — "A1'e komut ssh sarmalı" kuralı TEK kaynaktan türer; her koşumda `--limit a1` (tek host olsa da disiplin;
  memory canliya-giden-komut-ssh-sarmali'nın Ansible karşılığı). Dinamik envanter gereksiz (Terraform gelirse `cloud.terraform` eklentisiyle türetilir).
- **Idempotency** modülün işi; `command/shell` idempotent DEĞİL → `creates`/`removes`/`changed_when` şart (uv sync, model indirme).
- **Check mode (`--check --diff`) yalancı-yeşil üretir**: (a) `register` sonucuna bağlı koşullar check modda değerlendirilmez, (b) `command/shell`
  hiç çalışmaz (doğrulanmadı ama bilinen), (c) `check_mode_markers` maskeleyebilir → "dry-run temiz" hükmü yalnız check-mode destekleyen modüller
  için verilir; Meridian'ın "çivi yeşili kanıt değildir" ilkesiyle aynı sınıf. `synchronize`'ın check-mode davranışı doğrulanmadı — ilk kullanımda ölçülür.
- **become**: parolasız sudo var; iki imtiyazsız kullanıcı arası become'da modül dosyası dünya-okunur olabilir → `pipelining = True` (`requiretty`
  Ubuntu 24.04 varsayılanı doğrulanmadı → `sudo -l` ile ölçülür).
- **ansible-vault**: git-taraflı at-rest şifreleme — Meridian'ın ".env asla commit'lenmez" politikasıyla gerilimli; sır DEĞERİ Faz-2'ye kadar A1'de
  elle üretilmeye devam eder; Ansible sırrı yalnız TAŞIR (`copy content=… mode=0400 owner=root no_log=true`) — ve `no_log` `-vvv`'yi etkilemez →
  üretim koşumlarında `-v` üstü YASAK (sır süzgeci ilkesi). Faz-2'de `community.hashi_vault` lookup (AppRole parametreleri doğrulanmadı).
- **ansible-pull ÖNERİLMEZ** (Rol-1 onaylı adım adım dağıtım disiplinini atlar). **cron modülü KULLANILMAZ** (timer SSoT, tek-kaynak).
- Hata yönetimi `block/rescue/always`: boş `rescue`/`ignore_errors` = Yasa 4 sessiz yutma — gerekçeli olmadan yasak.

### 2.2 Modül eşlemesi (ansible.builtin / ansible.posix / community.docker / community.postgresql / community.general / oracle.oci)
| Bileşen | Modül | Bedel/tuzak |
|---|---|---|
| systemd birimleri + timer + drop-in + polkit + unattended-upgrades | `template`/`copy` + `file` + `systemd_service` (daemon_reload, enabled, state) + handler | Handler yoksa her koşuda restart; template = üretilmiş dosya (hedefte elle düzenlenmez) |
| Paketler (postgresql, docker, redis, rsync…) + docker apt deposu | `apt`, `apt_repository`/`deb822_repository` | A1 apt allowlist (`deploy.sh`) aynen |
| venv'ler + `uv sync` | `pip` (venv) + `command uv sync creates/changed_when` | uv modülü yok; `changed_when` olmadan gürültü |
| Hindsight Postgres (ilk kez kodda) | `apt` + `community.postgresql.postgresql_db/user/privs` (`no_log`) | Parola task'ında `no_log` zorunlu |
| APISIX/etcd/Hindsight-CP konteynerleri | `community.docker.docker_image` + `docker_container` (`comparisons`) | Bugünkü ham `docker run --rm` ExecStart'tan daha sağlam; `comparisons` yoksa gereksiz yeniden yaratma |
| Sır dosyaları /etc/meridian, /etc/hindsight/creds | `file` (0700 dizin) + `copy` (0400 root, `no_log`) | Değer kaynağı: Faz-2'ye kadar elle/A1-içi; sonra hashi_vault |
| litestream (sürüm-sabit ikili + sha) | `get_url checksum=sha256:…` + `template` + `systemd_service` | `litestream_kur.sh`'ın elle yazdığı kapının native karşılığı |
| hermes config/SOUL (üzerine yazma, yedekle) | `copy backup=yes` | deploy.sh'ın 15 satırının yerine |
| /opt/veri blok hacmi | `ansible.posix.mount` (+ fstab) | Cihaz OCI tarafında (Terraform); mount Ansible; modül bu turda okunmadı |
| healthz / bakım penceresi | `uri until/retries/status_code`, `wait_for`, `systemd_service stop/start` | Belgedeki 720×5 s örneği kopyalanmaz (SLA'ya göre) |
| `.env`/`.dash.env` | `template` ile TÜM dosya (lineinfile/blockinfile YASAK — idempotency kırılır) | Faz-1 sonrası .env yalnız ayar taşıyor |
| OCI kaynakları | `oracle.oci` koleksiyonu (docs.ansible.com dışı; state'siz idempotency iddiası doğrulanmadı) | Bulut katmanı için Terraform tercih (import/drift/plan) |
| ufw/timezone | `community.general.ufw`, `timezone` | A1'de ufw kullanımı ölçülmedi |

### 2.3 Test ve operasyon
`ansible-lint` + `--check --diff` + idempotency testi (ikinci koşum `changed=0`) çivi olarak; Molecule (Docker sahnesi) Apple Silicon/aarch64 uyumu
doğrulanmadı → Meridian'da Molecule yerine A1'in kendisinde `--check` + gerçek koşum (tek host) ve pytest çivileri (birim dosyaları/şablonlar için
mevcut v-çivi ailesi). `ansible.cfg`: `host_key_checking=True`, pipelining, mutlak yol/`ANSIBLE_CONFIG` (cwd tuzağı — memory bash-cwd-kalici).

---

## 3. Bileşen × araç matrisi — "yerine geçer / yanına gelir / kalır" (envanter ajanı + Rol-1 hükmü)

| Mekanizma (dosya) | Bugün | Terraform | Ansible | Hüküm |
|---|---|---|---|---|
| `deploy/oracle-a1/deploy.sh` (apt, uv, birimler `sudo cp`+enable, kum havuzları, token, hermes config) | elle ssh, idempotent | — | **YERİNE GEÇER** (rol: packages/venv/units/timers/sandbox/hermes-config) | Ansible rolü deploy.sh'ı emekli eder |
| dagit `[1c]` birim ayrıklığı (yalnız rapor) + elle `install` | elle | — | **YERİNE GEÇER** (template+systemd+handler: raporlamak yerine kurar) | F9/[1c] duruşu "kur ama bakım penceresinde" olur |
| dagit `[2] rsync` `[3] uv sync` `[4] pencere` `[5] healthz` | dagit | — | **İÇİ DEVREDİLİR** (`synchronize` exclude listesi RSYNC_EXC'den TÜRETİLİR — tek kaynak; `state/`, `backups/`, `.env*` silinmesin) | dagit sarmalayıcı kalır |
| dagit `[0a-0d]` (git temiz, uv audit, lint-imports, dev-grubu), `[1b]` state farkı, F9/F10, `[5a-5c]`, `[B]` kayıt, RUNBOOK zinciri | dagit | — | **KALIR** (Meridian'a özgü politika/kapı; `pre_tasks` ile sarılabilir ama yeniden yazılmaz) | dagit.sh'ın var oluş sebebi |
| `cutover.sh` (Mac→A1 tek seferlik taşıma) | tek seferlik | — | Yanına gelir (playbook'a çevrilebilir) | Düşük öncelik |
| `bakim_h9.sh` (tarihî tek seferlik migrasyon) | bitti | — | — | Arşiv |
| systemd birimleri/timer'lar/polkit/`52meridian-unattended-upgrades`/`sertlestirme.conf` (emekli) | elle kurulum | — | **YERİNE GEÇER** | — |
| `dash_token_credential.sh`, `sir_credential_gecis.sh`, `h3_tur2_sertlestir.sh` (fazlı, farksal ölçümlü geçişler) | elle | — | Yanına gelir (dosya yerleştirme trivial; kanıt+geri-alım mantığı `block/rescue`+`uri` ile yeniden yazılır) | Geçişler BİTTİ (Faz-1B/1A canlı); betikler geri-alım için kalır; Faz-2 Vault Agent template sonrası emekli |
| `litestream_kur.sh` | elle | — | **YERİNE GEÇER (daha iyi)** (`get_url checksum`) | — |
| `apisix.service`/`apisix-etcd.service` (ham `docker run`) + `hindsight-cp.service` | birim | — | **YERİNE GEÇER** (`docker_container`; birim yine Ansible yazar) | Karar: konteyner ExecStart'ta mı, docker_container'da mı — tek kaynak |
| `deploy/apisix/config.yaml` + `routes.yaml` + `ops/apisix_uygula.py` + `apisix_ssl_yukle.py` | elle `--uygula/--denetle` | **YERİNE GEÇER** (apisix sağlayıcısı: route/upstream/consumer/plugin/ssl; drift = plan) | Yanına gelir (`uri` döngüsü — gereksiz) | `routes.yaml` → HCL; `apisix_uygula.py` emekli (denetim testleri `terraform plan -detailed-exitcode`'a taşınır) |
| `hindsight-api.service` (+ sarmalayıcı, drop-in) · `hindsight-yedek` · `hindsight-taban-tazele` | elle kurulum | — | **YERİNE GEÇER** (birim dağıtımı); pipeline/pg_dump mantığı betik kalır | — |
| **Postgres kurulumu** (repoda YOK) | A1'de elle (ölçülemedi) | — | **İLK KEZ KODA GİRER** (`apt` + `postgresql_*`) | DR için kritik boşluk |
| hermes profilleri (`hermes profile install`) | elle, bilinçli | — | Teknik olarak uygun, **ELLE KALIR** (CLAUDE.md: yeni ajan kimliği operatör kararı) | — |
| `meridian-backup`, `litestream.yml`, `aylik_bucket_kopya.py`+birim, `ops/pull-a1-backups.sh` (Mac launchd) | timer/elle | bucket: **Terraform** (`oci_objectstorage_bucket` import) | birimler: **YERİNE GEÇER**; Mac launchd: kalır | — |
| `deploy/gcp_provision.sh`, `connect.sh`, `monitoring.sh`, `install_hermes.sh`, `push_secret.sh`, `state_backup/restore.sh` (GCS), `Caddyfile` | **ÖLÜ GCP yolu** (kanonik değil; Caddy A1'de koşmuyor) | (GCP'de olsaydı Terraform'un en saf örneği) | — | Emekli et/`deploy/legacy/`'ye taşı (tek-kaynak: iki TLS-ingress tasarımı — Caddy vs APISIX 9443 — netleşmeli) |
| `.github/workflows/ci.yml` (duman testi) | CI | github sağlayıcısı (repo ayarları) — isteğe bağlı | — | CD yok, kalır |
| `serve.sh`, `ops/kapilar.sh` | yerel/gate | — | — | Kalır |
| Bulut: A1 instance, blok hacim, bucket, NSG, IAM; ileride Vault KMS | konsol (elle), RUNBOOK'ta hacim adımı YOK | **YERİNE GEÇER (import)** | `oracle.oci` mümkün ama tercih değil | Belge boşluğu (hacim) Terraform ile kapanır |
| Vault (Faz-2) kurulum / yapılandırma | (henüz yok) | yapılandırma: **Terraform vault sağlayıcısı** | kurulum: **Ansible rolü** (`get_url checksum`, birim, unseal betiği) | Sır değerleri: ephemeral/write-only; unseal anahtarı elle 0400 |

---

## 4. Meridian'a özgü kapılar — neden hiçbir araca taşınmaz, nasıl korunur
1. **Rol-1 tekelciliği + temiz ağaç** (`[0a]`): araçlar "kim koşturuyor" bilmez → sarmalayıcı (dagit/altyapi.sh) `git status --porcelain` + rol beyanı.
2. **Tedarik-zinciri kapıları** (`uv audit`, `lint-imports`, dev-grubu taraması): depoya özgü; `command`+`failed_when` ile sarılır, yeniden yazılmaz.
3. **`[1b]` versiyonlu state farkı** (goal/bounds canlıda elle değişmiş mi): iki yönlü SSoT hükmü; Ansible template diff'i tek yönlü → `assert/fail` ile.
4. **F10 enabled+inactive anomalisi**: Ansible bunu SESSİZCE düzeltir (enabled → start) — Meridian bilerek DURDURUR → playbook'ta `state` verilmez, önce `service_facts`+`assert`.
5. **`[5a-5c]` doğrulama üçlüsü** (token'lı gövde, kod-tazelik ≥ kaynak-mtime, artefakt tazeliği): `stat`+`assert` ile taşınabilir ama özel mantık.
6. **`[B]` dağıtım kaydı** (`state/dagitim.json`: sha, kirli-geç, sandbox-eski-kod): playbook sonu `template` ile üretilebilir; şema korunur.
7. **Farksal ölçüm** (sahte değer eski kanala, gerçek yeni kanaldan): stok modül yok; Faz-2 sonrası gereksizleşir (tek kanal: Vault Agent).
8. **Sır süzgeci** (yalnız beyaz-liste adlar basılır): Ansible'da `no_log` + `-v` tavanı; Terraform'da ephemeral + state backend şifreli + Instance Principal.
**Yol:** "hepsini taşı" değil, **"aracı dagit'in içine çağır"** — kapılar bash'te, kurulum/dağıtım gövdesi Ansible'da, bulut/kapı/Vault yapılandırması Terraform'da.

---

## 5. Önerilen mimari ve fazlar (kart-önce değil — altyapı; ROADMAP kalemleri + operatör sıra onayı)
| Faz | Ne | Yerine geçtiği | Boyut | Ön-koşul |
|---|---|---|---|---|
| **A0** | `deploy/ansible/` iskeleti: inventory (tek host), ansible.cfg, rol `meridian_a1` (packages · venv · units/timers/drop-ins/polkit · sandbox · hermes-config · litestream · docker-konteynerler · secrets-copy · healthcheck); `ansible-lint`; pytest çivisi: rolün ürettiği birim dosyaları == `deploy/` kaynakları (tek kaynak — `.j2` YOK, `copy` ile aynı dosya) | `deploy.sh`, dagit `[1c]` elle install, `litestream_kur.sh`, ham `docker run` | M | Ansible kurulumu (Mac `pipx`), A1'de python3 var; `--check` yalancı-yeşil beyanı |
| **A1** | dagit.sh `[2]-[5]` gövdesi → `ansible-playbook … --tags dagit` çağrısı (kapılar bash'te kalır; RSYNC_EXC → synchronize exclude tek kaynaktan üretilir; `[B]` kayıt aynen) | dagit'in içi | S-M | A0 |
| **A2** | Postgres kurulumu + Hindsight venv/birimleri role girer; **DR tatbikatı**: boş VM (yerel VM/lima ya da ikinci A1 kapasite varsa) → cloud-init köprü → rol → yedekten `meridian.db`+creds geri yükleme → healthz | Repoda olmayan Postgres adımı; RUNBOOK elle adımları | M | A0; yedek geri-yükleme reçetesi |
| **T1** | Terraform `altyapi/apisix/`: `routes.yaml` → HCL (route/upstream/consumer/plugin/ssl), `apisix` sağlayıcısı pinli; `terraform plan -detailed-exitcode` = drift denetimi; `apisix_uygula.py` emekli (testleri taşınır) | `ops/apisix_uygula.py`, `apisix_ssl_yukle.py` | S-M | Sağlayıcı bakım riski beyanı; admin anahtarı env/ephemeral |
| **T2** | Terraform `altyapi/oci/`: import (instance, volume+attachment, bucket, NSG/security list, IAM); backend kararı (HCP ücretsiz vs OCI S3 — kilit testi); Instance Principal; `altyapi.sh` (plan/apply reçetesi) + CLAUDE.md §2 satırı; drift timer | Konsol adımları; RUNBOOK hacim boşluğu | M | Lisans/OpenTofu kararı; state backend testi |
| **T3** | Faz-2 Vault: kurulum Ansible rolü (pinli ikili+sha, birim, oto-unseal betiği) + Terraform `vault` sağlayıcısı (mount/policy/AppRole/KV, policy'ler `secrets.ALLOWED`'dan üretilir) + Vault Agent template → LoadCredential dosyaları; sırlar ephemeral | Elle Vault yapılandırması; `sir_credential_gecis.sh` (geri-alım için kalır) | M-L | TSK-064 §6; T2 (IAM/NSG) |
| **T4** (isteğe bağlı) | `github` sağlayıcısı: dal koruması, Actions sırları | elle repo ayarları | S | — |
Sıra önerisi: A0 → T1 → A1 → A2 (DR) → T2 → T3 → T4. Gerekçe: A0/T1 hemen ölçülebilir kazanç (elle kurulum + kapı yapılandırması), T2
bedeli en yüksek belirsizlik (state backend, kapasite), T3 Vault'a bağlı.

---

## 6. Bedel / riskler (Bedel yasası)
- **Check-mode yalancı yeşil** (Ansible) ve **check bloğu uyarı** (Terraform): "dry-run temiz" hükmü ancak destekleyen modüller için; gerçek doğrulama healthz/uri + dağıtım kaydı.
- **Sır yüzeyi büyür**: Terraform state (ephemeral + şifreli backend + Instance Principal), Ansible log (`no_log`, `-v` tavanı, pipelining). Sır DEĞERİ ilkesi aynen.
- **Tek kaynak ayrışması**: aynı şeyi iki araç yönetirse (docker konteyneri: birim ExecStart vs docker_container; rota: routes.yaml vs HCL; birim dosyası: deploy/ vs .j2) sessiz ayrışma → her bileşenin TEK yöneticisi olur, çivi ile.
- **Topluluk sağlayıcısı** (apisix): bakım/uyum riski; sürüm pinlenir, plan çıktısı okunur; alternatif `ops/apisix_uygula.py` geri-alım için bir sürüm daha kalır.
- **OCI S3-uyumlu backend kilidi doğrulanmadı**; HCP ücretsiz katman = yeni hesap/SaaS bağımlılığı.
- **Otomasyon/sınıflandırıcı**: tek komutlu, opak-betiksiz, argümanı açık çağrılar (bugünkü dagit tecrübesi) — Ansible/Terraform komutları da böyle yazılır.
- **Öğrenme bedeli**: HCL + YAML + iki aracın hata biçimleri; tek kişilik takım + Rol-1 ajanları için CLAUDE.md §2 kapı satırları şart.
- **Molecule aarch64** doğrulanmadı → yerel sahne yok, test A1'de (`--check` + gerçek koşum) ve pytest çivileri.

---

## 7. Ölçülemeyen / doğrulanmayan (dürüst liste; §Ek-B ayrıntı)
Postgres'in A1'e nasıl kurulduğu (repoda yok); A1'de kaç OCI kaynağı var (konsol erişimi yok); OCI S3-uyumlu backend + `use_lockfile`;
OCI Customer Secret Key; Workload Identity/OIDC; BSL FAQ tam metni; `synchronize`/`command` check-mode davranışı; `community.hashi_vault`
AppRole parametreleri; `ansible.posix.mount`; Molecule/aarch64; Ubuntu 24.04 `requiretty`; apisix sağlayıcısının son commit tarihi.

## 8. Operatör kararları
1. **Yön:** Ansible dagit'in İÇİNE (öneri) mi, yerine mi? 2. **APISIX** yapılandırması Terraform'a geçsin mi (apisix_uygula.py emekli)? 3. **State
backend:** HCP Terraform ücretsiz (yeni hesap) mi, OCI S3-uyumlu (kilit testi) mi? 4. **Sıra:** A0 → T1 → A1 → A2 → T2 → T3 (öneri) — hangi
adıma kadar onay? 5. **Ölü GCP yolu** (`deploy/gcp_*`, Caddyfile) `deploy/legacy/`'ye taşınsın mı?

## Ek-A — Kaynaklar (okunanlar)
developer.hashicorp.com/terraform: /docs, /language/import, /language/resources/ephemeral, /language/state, /language/backend/s3|local,
/language/checks, /language/tests, /language/moved, /language/block/removed, /cli/workspaces, /cli/commands/plan, /language/values/variables,
/intro/phases, /intro/vs/chef-puppet, /cdktf (deprecation), /language/stacks, hcp docs (ücretsiz katman). registry/github: rework-space-com/
terraform-provider-apisix (docs/resources listesi). docs.ansible.com: getting_started, inventory_guide, playbook_guide (checkmode, privilege_
escalation, error_handling, strategies, reuse_roles), vault_guide, collections_guide, cli/ansible-pull, dev_guide/testing, reference_appendices/
logging; modül sayfaları: systemd_service, apt, pip, copy/template/file, synchronize, uri, wait_for, docker_container/image, postgresql_db/user/
privs, ufw, lineinfile/blockinfile, command/shell, cron, get_url. Depo: envanter ajanı raporu (dagit.sh, deploy/*, ops/*, ci.yml, günlük/ROADMAP).

## Ek-B — Doğrulanmadı / okunamadı (ajan beyanları, birleştirilmiş)
OCI S3-uyumlu backend "best effort" + `use_lockfile` OCI'de test edilmedi · OCI Customer Secret Key gereksinimi (Oracle belgesi) · Workload
Identity Federation/OIDC (403) · BSL 1.1 FAQ tam metni (JS) · HCP drift detection ücretsiz katmanda mı · apisix sağlayıcısı son commit/bakım ·
`command/shell` check-mode'da atlanması (modül sayfası okunmadı) · `synchronize` check-mode · `ansible.builtin.systemd` alias ilişkisi (429) ·
`community.hashi_vault` AppRole parametreleri (403/429) · `ansible.posix.mount` · `oracle.oci` modül parametreleri · Molecule aarch64 · Ubuntu
24.04 sudoers `requiretty` · ansible.cfg `[ssh_connection]` tam metni (429) · ansible-lint kurulum/CI (429) · `-i "host,"` sözdizimi ·
`ANSIBLE_VAULT_PASSWORD_FILE` · playbooks_best_practices.html 404 → tips_tricks/sample_setup.html.

## Ek-C — Sağlayıcı araştırmasının ek bulguları (4. ajan; registry SPA olduğundan GitHub ham dokümanlardan okundu)
- `oci_core_instance`: zorunlu `availability_domain/compartment_id/shape`, A1.Flex için `shape_config{ocpus,memory_in_gbs}`, `metadata.user_data` (base64
  cloud-init) — Terraform yalnız TAŞIYICI; force-replacement tetikleyen alan değişikliklerinden (AD, source_details — GitHub issue kaynaklı, doğrulanmadı)
  KAÇINILIR (`lifecycle.prevent_destroy`). "Out of host capacity" retry döngüleri topluluk kaynaklı, resmi belgede yok.
- NSG: kurallar ayrı kaynaktır (`oci_core_network_security_group_security_rule`), import kuralları otomatik getirmez → kural sayısı kadar import.
- Bucket import biçimi `n/{namespace}/b/{bucket}`; hacim `size_in_gbs` birebir eşlenmezse plan resize gösterir.
- `hashicorp/local` `local_file` varsayılan `file_permission` "0777" — sır dosyası yazımında açıkça "0600/0400" verilmezse dünya-okunur; bu yüzden
  sır dosyalarını Terraform DEĞİL Ansible (`copy mode=0400 no_log`) yazar (Rol-1 hükmü).
- `github_actions_secret` state'te düz metin — kullanılırsa uzak/şifreli backend zorunlu; T4 isteğe bağlı.
- `terraform_data` (1.4+) `null_resource`'un resmi halefi; provisioner yalnız son çare.
- Vault: OCI için resmi "Vault kurulum" Terraform modülü YOK (AWS/Azure/GCP var) → kurulum Ansible rolü; **terminoloji**: resmi "auto-unseal" harici
  KMS/HSM/Transit ister; bizim "anahtar dosyası A1'de" kararı Shamir unseal'ın betikle OTOMASYONUDUR (K6b) — belgelerde bu ayrım korunur.
- Sağlayıcı ajanı docker konteynerleri ve Postgres rolleri için Terraform önerdi; Rol-1 hükmü Ansible (aynı makine, birim/konteyner tek yöneticide;
  tek-kaynak) — iki araç aynı nesneyi yönetmez. `vault_generic_secret` yerine `vault_kv_secret_v2` (+ ephemeral) kullanılır.
