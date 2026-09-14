# Vault dalga-2 — tasarım (TSK-064 Faz-2 devamı; operatör kararı 2026-09-14 17:47Z: HEPSİ)

**Kapsam (operatör):** dalga-1'in 7 sırrına ek olarak kalan bütün sırlar kasaya: OpenRouter anahtarı (14 kopya → tek kaynak),
bot anahtarları (BOT_KEY_BEKCI/KARNE/SEF/MERIDIAN), APISIX yönetim anahtarı (kasada var; docker env dosyasına da Agent yazar),
PANO_GIRIS_PAROLA, Hindsight kontrol paneli (HINDSIGHT_CP_ACCESS_KEY, HINDSIGHT_CP_DATAPLANE_API_KEY). Kabul edilen bedeller:
Agent (root) yazma yüzeyi `/opt/hindsight`, `/opt/apisix`, `/home/ubuntu/.hermes` ile genişler; docker tüketicileri
rotasyonda yeniden başlatılır. Kaynak: `docs/degerlendirme/VAULT-DALGA2-ONERI-2026-09-14.md`, `deploy/sir_envanteri.yaml`.

## 1. Ölçülen kısıtlar (tasarımı belirleyen)
- Vault Agent `template` bloğunda dosya SAHİBİ/GRUBU parametresi YOK (yalnız `perms`; resmî belge 2026-09-14). Agent root
  koştuğu için render edilen dosya root:root olur. Docker env dosyalarını docker daemon (root) okur → sorun yok; hermes profil
  `.env` dosyalarını `ubuntu` okur → render sonrası `exec { command = ["chown", "ubuntu:ubuntu", "<yol>"] }` (kabuksuz, sabit
  argüman listesi; Agent'ın tek ek yetkisi bu — tasarım §6.3 "Agent tüketiciyi yeniden başlatmaz" ilkesi KORUNUR: chown restart
  değildir).
- KV-v2 statik sırlar `template_config { static_secret_render_interval = "1m" }` ile yeniden render edilir (varsayılan 5 dk);
  rotasyon penceresinde bekleme bu süreyle sınırlanır.
- Env dosyaları KARIŞIKTIR (sır + yapılandırma). Envanterde DEĞER tutulmaz (tek kural) → Agent bütün dosyayı üretemez.
  KARAR: **sır-yalnız yan dosya**: Agent `<dosya>.vault` dosyasına YALNIZ sır satırlarını yazar (`ALAN=değer`), tüketici iki
  kaynağı birlikte okur (docker: ikinci `--env-file`; systemd: ikinci `EnvironmentFile=`); asıl dosyadaki sır satırları
  iki-kanal döneminden sonra AYRI adımda kaldırılır (Faz-1 deseni). hermes profil `.env` dosyaları yalnız sır taşıyorsa
  (A1'de ÖLÇÜLÜR) bütün dosya render edilir, taşımıyorsa aynı yan-dosya deseni + hermes env_loader'ın ikinci dosya desteği
  ölçülür (yoksa: bot birimlerine `EnvironmentFile=` ile yan dosya).
- Türetilmiş değer: `OPENROUTER_AUTH = "Bearer <anahtar>"` — şablonda önek sabit, değer kasadan (`{{ with secret }}` içinde
  birleştirme); envanter satırı `onek: "Bearer "` taşır.

## 2. Envanter (tek kaynak) genişlemesi — `deploy/sir_envanteri.yaml`
- `vault_kv` += 8 girdi (dosya-başına, dalga-1 deseni, hedef `/etc/meridian/<ad>` 0400 root, tüketici: `vault_dosyalar`
  şablonları): `openrouter_api_key`, `bot_key_bekci`, `bot_key_karne`, `bot_key_sef`, `bot_key_meridian`, `pano_giris_parola`,
  `hindsight_cp_access_key`, `hindsight_cp_dataplane_api_key`. (`apisix_admin_key` zaten var.)
- YENİ blok `vault_dosyalar`: her yan dosya için `yol` (ör. `/opt/apisix/.env-apisix.vault`), `mod`, `sahip` (`root` | `ubuntu`
  → exec chown), `tuketici`, `yeniden_baslat` (rotasyon aracının koşacağı komut adı; docker/systemd), `satirlar`: liste
  `{alan, sir, onek?}` — `sir` `vault_kv.ad`e referans (çivi: dangling referans yok). Dalga-2 dosyaları: `.env-apisix.vault`
  (OPENROUTER_API_KEY, OPENROUTER_AUTH[önek Bearer], APISIX_ADMIN_KEY, PANO_GIRIS_PAROLA, BOT_KEY_×4), `/opt/hindsight/.env.vault`
  (6 REFLECT/CONSOLIDATION alanı — hepsi `openrouter_api_key`), `/opt/hindsight/.env-cp.vault` (2), hermes ×4 (`BOT_KEY_<AD>`,
  `OPENROUTER_API_KEY`; sahip ubuntu).
- `rotasyon_kopyalari` bloğu KALIR (sir_rotasyon.sh `--esitle` eski kanal için); yeni `--vault` kipi kasayı kaynak sayar.

## 3. Üretici (`ops/vault_politika_uret.py`)
- `agent.hcl`: mevcut tek-değer şablonlarına ek `vault_dosyalar` için template blokları (`contents` = satır satır
  `ALAN={{ with secret "…" }}{{ .Data.data.value }}{{ end }}`; önekli alanlar için `ALAN=Bearer {{ … }}`), `perms`, sahip
  ubuntu ise `exec` chown; `template_config` 1m. `policies/meridian-agent.hcl`: okuma yolları (8 yeni). `meridian-admin.hcl`
  değişmez (secret/data/meridian/*).
- `vault-agent.service` `ReadWritePaths` ÜRETİLMEZ (birim dosyası elle) ama çivi envanter hedef dizinlerinden türetilen
  kümeyle birebir eşitliği ölçer (v485 E-serisi genişler): `/etc/meridian /etc/hindsight/creds /opt/apisix /opt/hindsight
  /home/ubuntu/.hermes/profiles/... /home/ubuntu/.hermes`.

## 4. Taşıma (`deploy/vault/vault_sir_koy.sh`) ve rotasyon (`deploy/oracle-a1/sir_rotasyon.sh --vault`)
- sir_koy: `vault_kv` girdisi `kaynak: {tur: env_satiri, dosya, alan}` taşıyabilir → değer o dosyanın `^ALAN=` satırının
  sağından (tırnak kırpılır, `Bearer ` öneki soyulur) STDIN ile `kv put`; sha256 doğrulama aynen. Değer hiçbir değişkene
  alınmaz (boru). Aynı sır birden çok dosyada varsa İLK kaynak alınır, diğerleriyle sha EŞİTLİĞİ ölçülür (ayrışma → durur:
  14 kopya gerçekten aynı mı — bu, rotasyonun eksik bıraktığı kopyayı bulur).
- sir_rotasyon `--vault --openrouter`: yeni değeri stdin'den kasaya `kv put` → `.vault` dosyalarının render edilmesini
  ölçer (sha değişimi, en çok 90 s) → `yeniden_baslat` listesini koşar (docker apisix, hindsight-cp; hindsight-api; hermes
  oneshot'ları restart gerektirmez) → kapı chat 200 + Hindsight 2/2 kanıtları (mevcut) → eski kanal kopyalarını `--esitle`
  ile eşitler (iki-kanal dönemi boyunca).

## 5. Uygulama sırası (A1, Rol-1, bakım penceresi) ve geri alım
1. Repo tarafı (Opus): envanter + üretici + sir_koy + rotasyon + birim ReadWritePaths + tüketici drop-in'leri (docker
   birimlerine ikinci `--env-file`; hindsight-api ikinci `EnvironmentFile=`) + çiviler.
2. A1: `vault_sir_koy.sh --kuru/--uygula` (8 sır; kopya eşitliği raporu) → agent.hcl/policy dağıtımı (kur betiği adım 3/8)
   → `systemctl restart vault-agent` → `.vault` dosyaları render (sha kanıtı, sahip/mod) → tüketici drop-in'leri →
   docker/hindsight restart (20:05Z sonrası) → canary: her dosya için sahte değer → render geri → tüketici 200.
3. İki-kanal dönemi (≥2 gece): asıl dosyalardaki sır satırları KALIR. Sonra AYRI adım: sır satırlarını asıl dosyalardan
   kaldır (yedekli), envanter `kanal_bugun` güncelle.
Geri alım: `systemctl stop vault-agent` + drop-in'lerin kaldırılması; asıl dosyalar dokunulmamış olduğu için tüketiciler
eski kanalla devam eder (tasarım §6.4).

## 6. Çiviler (v491)
Envanter: her `vault_dosyalar.satirlar.sir` `vault_kv`de var; değer yok; sahip ∈ {root, ubuntu}; yol mutlak. Üretici: 8 yeni
policy yolu; template blokları satır sayısı = envanter satır sayısı; önekli alan `Bearer ` ile; ubuntu sahipli dosyada exec
chown var, root sahiplide YOK; `template_config` 1m; üretilen dosyalar deterministik. Birim: ReadWritePaths kümesi envanter
dizinleriyle birebir. sir_koy: env_satiri kaynağı boru ile, `$(cat` yok, kopya sha eşitliği kapısı (sentetik iki dosya ayrışınca
durur). Rotasyon: `--vault` kipi render bekleme sınırlı, restart listesi envanterden. Mutasyonlar: referans kontrolü, önek,
chown, kopya-eşitliği kapısı.
