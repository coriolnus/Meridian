# Meridian → Oracle Cloud Always Free Ampere A1 (aarch64) taşıma kılavuzu

**Uygunluk özeti:** Mac'in zaten `arm64` (Apple Silicon), A1 `aarch64 Linux` — **aynı mimari ailesi**. Meridian saf
Python + uv (build adımı yok), hermes-agent bir Python venv paketi. **Mimari engel yok.** Tüm bağımlılıkların
aarch64 Linux wheel'i var (`uv sync` derleme yapmaz). systemd, macOS'ta auto-restart'ı bloklayan launchd/TCC
sorununu temiz çözer.

## ⚠️ Dürüst performans beklentisi (önce oku)
A1'e taşımak **aramaları hızlandırmaz** — Apple Silicon çekirdeği Ampere A1 çekirdeğinden **daha hızlı** ve Mac'te
daha çok çekirdek var. Walk-forward reflection A1'de **yerelden yavaş** koşar. Taşımanın gerçek kazancı:
- **7/24 çalışır**, senin masaüstünü yavaşlatmaz (bugünkü yavaşlığın ana kaynağı buydu: 250-evren reflection
  Mac'in çekirdeklerini dolduruyordu).
- **systemd auto-restart** (çöküş/reboot sonrası kendiliğinden geri gelir).
- Ücretsiz.

**Çekirdek ayarı (2026-07-30 sunucuda ÖLÇÜLDÜ, `nproc=4`):** paralel sonda havuzu **AÇIK**
(`MERIDIAN_PARALLEL_PROBES=1`, yerel prod ile aynı). Havuz kendini sınırlar —
`reflect._havuz_tavani()` → `max(1, min(4, cpu_count-2))` → 4 çekirdekte **2 işçi**, geriye
sunucu+ajan için 2 çekirdek kalır; işçiler doğuştan `nice(15)` (2026-08-03: iki işçi 2 saat
%99,9 CPU'yla pano API'sini boğdu — canlı vaka; taban 2→1'e indi, ≤3 çekirdekte tavan ezilmesin). `MERIDIAN_SEARCH_MAX_MIN=60` duruyor: Ampere çekirdeği Apple
Silicon'dan yavaş, aramalar yine uzun sürer. *(Eski "2 OCPU → havuzu KAPAT" notu geçersiz.)*

---

## Bölüm A — Oracle konsolu (instance ZATEN VAR)

> **TEYİTLİ SUNUCU KÜNYESİ (ssh ile doğrulandı, 2026-07-30)**
> | alan | değer |
> |---|---|
> | public IP | `130.61.126.87` |
> | kullanıcı | `ubuntu` |
> | ssh anahtarı | `~/Documents/OCI/ssh-key-2026-07-21.key` (0600, yerelde mevcut) |
> | şekil | VM.Standard.A1.Flex — **4 OCPU** / 12 GB (`nproc=4`) |
> | imaj | Ubuntu **24.04.4 LTS** aarch64 |
> | disk | 42 GB boş |
> | durum | `rsync` + `curl` KURULU · `redis` YOK · `/opt/meridian` YOK (temiz kurulum) |
>
> Bağlan: `ssh -i ~/Documents/OCI/ssh-key-2026-07-21.key ubuntu@130.61.126.87`

Aşağıdaki adımlar **yalnız instance'ı yeniden kurman gerekirse** geçerlidir.

1. **A1 instance oluştur:** Oracle Cloud → Compute → Instances → Create.
   - Shape: **VM.Standard.A1.Flex**, 2 OCPU / 12 GB (Always Free sınırı: toplam 4 OCPU/24 GB).
   - Image: **Canonical Ubuntu 24.04 Minimal (aarch64)** — 22.04'e tercih edildi (daha yeni LTS
     2029'a dek destek, çekirdek 6.8 ARM için daha olgun, yerel Python 3.12 projenin `>=3.11`'ini
     ve Mac'i birebir karşılıyor; Minimal + uv mükemmel eşleşme — sistem python-dev/build-essential
     gerekmez, hepsi hazır aarch64 wheel).
   - Boot volume: 50 GB yeter (state ~85 MB).
   - **SSH anahtarı ekle** (kendi public key'in) — parola değil.
   - **Minimal önyükleme pürüzü:** Minimal imajda rsync/curl önyüklü GELMEZ. İlk transferden önce
     bir kez: `ssh ubuntu@<A1-IP> 'sudo apt-get update && sudo apt-get install -y rsync curl'`
     (ya da rsync yerine `tar | ssh` — tar/ssh hep var).
2. **Ağ (Oracle iki katmanlı bloklar):**
   - VCN Security List: SSH (22) zaten açık. Panoyu 0.0.0.0'a **AÇMA**.
   - **Önerilen:** portu hiç açma; panoya **SSH tünel** ile eriş (aşağıda).
3. Instance açılınca **public IP**'yi not et ve bağlan: `ssh ubuntu@<A1-IP>`

## Bölüm B — taşıma: TEK KOMUT

```bash
# YEREL (Mac), repo kökünden. Anahtar default'u ~/Documents/OCI/ssh-key-2026-07-21.key;
# başka anahtar için:  -i <yol>
bash deploy/oracle-a1/cutover.sh 130.61.126.87
```

`cutover.sh` şu **sırayı** yürütür (sıra kritik, gerekçeleri betiğin içinde):

| # | adım | neden bu sırada |
|---|---|---|
| 1 | ön kontrol: IP, ssh, uzakta `rsync`/`curl`, `/opt/meridian` | eksik araçla yarıda kalmasın |
| 2 | **YEREL durdurma**: `stop_worker` (süreç grubu) + `barsarchive-run.sh stop` + keepalive | **rsync'ten ÖNCE** — koşan worker state'e yazarken alınan kopya yarım defterle gider |
| 3 | rsync: önce repo (`--exclude .venv .git state`), sonra `state/` ayrıca | durmuş süreçten tutarlı görüntü; sırlar uzakta 0600'e sabitlenir |
| 4 | uzakta `deploy.sh` | uv sync + redis + systemd birimleri + **tohum kapısı** |
| 5 | `MERIDIAN_DASH_TOKEN`: `.dash.env` yoksa üret (`openssl rand -hex 24`) + dolu/0600 doğrula + restart | token'sız canlıya çıkmayı önler; dolu dosyaya DOKUNMAZ (habersiz rotasyon yasak) |
| 6 | doğrulama tablosu + **çift-emir uyarısı** | |

**keepalive neden özel ele alınıyor:** `ops/keepalive.sh` pidfile silinince kendini kapatır ama
**60 sn'ye kadar** yaşar (uyku turu) — o süre içinde worker'ı **diriltir**. Betik önce PID'i
(komut kimliğiyle doğrulayarak) öldürür, sonra pidfile'ı siler. `caffeinate`'e dokunulmaz.

> **DÜZELTİLEN HATA (aynı sınıfın iki kuşağı — "sessiz sıfır-etkili adım"):** (1) eski B.3
> adımındaki `sed` deseni `DEĞİŞTİR-uzun-rastgele-token` idi, oysa placeholder
> `CHANGEME-long-random-ascii-token` — desen eşleşmeyince `sed` **sessizce 0 dönüyor**, servis
> bilinen bir placeholder token'la canlıya çıkıyordu. (2) Düzeltme `CHANGEME` grep'ine bağlanmıştı;
> H3 tur-2 (2026-08-02) placeholder'ı birimden tamamen çıkarınca `cutover.sh`'ın o adımı da
> `deploy.sh`'ın bekçisi de **sessiz no-op**'a düştü — taze kurulum TOKEN'SIZ kalırdı. İki betik
> artık desen değil **dosyanın kendisini** ölçer: `/opt/meridian/.dash.env` yok/boşsa üretilir,
> doluysa DOKUNULMAZ (habersiz rotasyon yasak) ve sonuç (dolu + 0600) doğrulanır.

<details><summary>Elle yol (cutover.sh koşmuyorsa)</summary>

```bash
# 0) (YEREL) ÖNCE durdur — yoksa tutarsız state kopyalarsın
source ops/stop-worker.sh && stop_worker
./ops/barsarchive-run.sh stop
kill "$(cat state/keepalive.pid)" 2>/dev/null; rm -f state/keepalive.pid

# 1) (YEREL) repo + state (.venv HARİÇ — A1'de yeniden kurulacak)
K=~/Documents/OCI/ssh-key-2026-07-21.key
ssh -i $K ubuntu@130.61.126.87 'sudo mkdir -p /opt/meridian && sudo chown ubuntu:ubuntu /opt/meridian'
rsync -az --delete --exclude .venv --exclude '.git' --exclude state -e "ssh -i $K" \
  ./ ubuntu@130.61.126.87:/opt/meridian/          # --delete-excluded ASLA: state'i silerdi
rsync -az -e "ssh -i $K" ./state/ ubuntu@130.61.126.87:/opt/meridian/state/

# 2) (A1) kurulum
ssh -i $K ubuntu@130.61.126.87 'cd /opt/meridian && bash deploy/oracle-a1/deploy.sh'

# 3) (A1) TOKEN — birimde DEĞİL, 0600 dosyada (H3 tur-1'den beri; eski `sed CHANGEME` adımı ÖLDÜ)
ssh -i $K ubuntu@130.61.126.87 '
  printf "MERIDIAN_DASH_TOKEN=%s\n" "$(openssl rand -hex 24)" | sudo tee /opt/meridian/.dash.env >/dev/null
  sudo chown ubuntu:ubuntu /opt/meridian/.dash.env && sudo chmod 600 /opt/meridian/.dash.env
  sudo systemctl daemon-reload && sudo systemctl restart meridian'
```
`meridian.service` bu dosyayı `EnvironmentFile=-/opt/meridian/.dash.env` ile okur. Birim dosyası
0644'tür (herkes okur) — sır oraya YAZILMAZ. `.dash.env` `dagit.sh` rsync'inden bilerek dışlanmıştır
(2026-08-01 vakası: `--delete` A1'deki dosyayı silmişti).
</details>

## Bölüm B2 — A1'deki birimler (üçü de `deploy.sh` tarafından kurulur+enable edilir)

| birim | ne yapar | not |
|---|---|---|
| `meridian.service` | worker + pano (uvicorn, 127.0.0.1:8080) | `Restart=always`; token birimde DEĞİL → `/opt/meridian/.dash.env` (0600) |
| `meridian-barsarchive.service` | `mrd:bars:*` → `state/bars_intraday/` | **AYRI birim**: worker restart'ı bar akışını kesmesin (yereldeki serve.sh/`stop_worker` ayrıklığının karşılığı) |
| `meridian-backup.timer` → `.service` | günlük `state/` tar.gz, 7 gün saklama | 23:30 UTC (kapanış sonrası), `Persistent=true` |
| `redis-server` (apt) | sıcak durum + bar ring'i | **ŞART**, opsiyonel değil — `hotstate.py`/`barsarchive.py` buna bağlı. Ubuntu default'u yalnız `127.0.0.1` dinler, **değiştirme** |

**Redis yoksa arşivci ÖLMEZ, sessizce boşa döner:** `poll()` `None` döner, `run()` `idle_s` uyuyup
yeniden dener (`barsarchive.py::BarsArchiver.poll` / `barsarchive.py::BarsArchiver.run`). Yani `is-active` **bar yazdığını kanıtlamaz** — ölçüsü
`--ozet` (aşağıda).

## Bölüm B3 — H3 tur-2 systemd sertleştirme: **uygulama prosedürü** (bakım penceresi)

Tur-1 (2026-07-31) maruziyeti **9.2 UNSAFE → 6.3 MEDIUM** yapmıştı ve seti ayrı bir drop-in'den
(`sertlestirme.conf`) uyguluyordu. Tur-2 seti **birim dosyalarının içindedir** ve üç birimi kapsar:
`meridian` · `meridian-barsarchive` · `meridian-backup`. `meridian-fail-notify` **bilerek dışarıda**
(gerekçe o dosyanın içinde: kendi arızasını tanım gereği yutar, sertleştirme hatası görünmez olurdu).

> **BEKLENEN SKOR — TAHMİN, ÖLÇÜM DEĞİL.** Yeni kalemler (`CapabilityBoundingSet=` ·
> `SystemCallFilter=@system-service` + `SystemCallArchitectures=native` · `RestrictNamespaces` ·
> `ProtectHostname`) `systemd-analyze security`'nin en ağır kalemlerini kapatır; **6.3'ten 2,5–3,8
> bandına** düşmesi beklenir (ROADMAP hedefi <4). Bu bir tahmindir — **gerçek sayı adım 6'da
> ölçülür ve ROADMAP'e ÖLÇÜLEN değer yazılır.** Tahmin tutmazsa hüküm ölçümündür.

### Ön koşullar
- Çalışma ağacı temiz (`dagit.sh` kapısı), depodaki birimler A1'e taşınmış olmalı
  (`dagit.sh` rsync'i `/opt/meridian/deploy/oracle-a1/` altına bırakır; **birimleri `/etc`'e
  KURMAZ** — kurulum bu bölümün işidir).
- Piyasa **kapalı** olmalı: adım 3 iki servisi de durdurur.

```bash
K=~/.ssh/oci-a1.key ; A1=ubuntu@130.61.126.87
```

### 1) GERİ-ALMA YEDEĞİ ÖNCE (bu adım atlanırsa prosedür başlamaz)
```bash
ssh -i $K $A1 'set -e
  D=/etc/systemd/system/h3-tur1-yedek-$(date -u +%Y%m%dT%H%M)
  sudo mkdir -p $D
  sudo cp -a /etc/systemd/system/meridian.service \
             /etc/systemd/system/meridian-barsarchive.service \
             /etc/systemd/system/meridian-backup.service $D/
  sudo cp -a /etc/systemd/system/meridian.service.d $D/meridian.service.d 2>/dev/null || true
  sudo cp -a /etc/systemd/system/meridian-barsarchive.service.d $D/meridian-barsarchive.service.d 2>/dev/null || true
  echo "YEDEK: $D" ; sudo ls -R $D'
```
Çıktıdaki `YEDEK:` yolunu **not al** — adım 7 (geri alma) ona ihtiyaç duyar.

### 2) Kopyala + tur-1 drop-in'ini SÖK
```bash
ssh -i $K $A1 'set -e
  # (a) yeni birimler
  sudo install -m 644 /opt/meridian/deploy/oracle-a1/meridian.service             /etc/systemd/system/
  sudo install -m 644 /opt/meridian/deploy/oracle-a1/meridian-barsarchive.service /etc/systemd/system/
  sudo install -m 644 /opt/meridian/deploy/oracle-a1/meridian-backup.service      /etc/systemd/system/
  sudo install -m 644 /opt/meridian/deploy/oracle-a1/meridian-backup.timer        /etc/systemd/system/
  # (b) tur-1 drop-in EMEKLİ — iki kaynak kalırsa yürürlükteki ayar okunamaz olur
  sudo rm -f /etc/systemd/system/meridian.service.d/sertlestirme.conf \
             /etc/systemd/system/meridian-barsarchive.service.d/sertlestirme.conf
  sudo rmdir /etc/systemd/system/meridian.service.d \
             /etc/systemd/system/meridian-barsarchive.service.d 2>/dev/null || true
  # (c) TOKEN KAPISI — .dash.env yerinde mi? (yoksa pano tokensız açılır)
  sudo test -s /opt/meridian/.dash.env && echo "  ✓ .dash.env var" || echo "  !! .dash.env YOK — Bölüm B adım 3"
  # (c2) AJAN DİZİNİ KAPISI — `~/.hermes` ReadWritePaths içinde `-` önekiyle YAZILIDIR (installer
  #      düşmüş olabilir, Bölüm D). Dizin yoksa yol SESSİZCE atlanır ve ajan yazımları tur-1
  #      kırıklığında kalır; birim yine de açılır. Burada GÖRÜNÜR yapılır:
  test -d /home/ubuntu/.hermes && echo "  ✓ ~/.hermes var — yazma yolu açılacak" \
    || echo "  !! ~/.hermes YOK — ajan yazımları kapalı kalır (Bölüm D: installer düşmüş)"
  sudo systemctl daemon-reload
  # (d) tek kaynak kanıtı: çıktıda YALNIZ .service dosyası görünmeli, drop-in görünmemeli
  sudo systemd-analyze cat-config systemd/system/meridian.service | grep -E "^# /|sertlestirme"'
```

### 3) Yeniden başlat
```bash
ssh -i $K $A1 'sudo systemctl restart meridian meridian-barsarchive && sleep 12
  systemctl is-active meridian meridian-barsarchive | tr "\n" " "; echo'
```

### 4) DOĞRULAMA — yürürlükteki direktifler (yorum değil, systemd'nin okuduğu değer)
```bash
ssh -i $K $A1 'for u in meridian meridian-barsarchive meridian-backup; do echo "--- $u"; \
  systemctl show $u -p NoNewPrivileges -p ProtectSystem -p ProtectHome -p ReadWritePaths \
    -p CapabilityBoundingSet -p RestrictAddressFamilies -p SystemCallFilter -p RestrictNamespaces \
    | cut -c1-160; done'
```
`ReadWritePaths` **meridian'da `/home/ubuntu/.hermes` içermeli** (tur-1'de yoktu — sessiz kırıklık).

### 5) DOĞRULAMA — üç duman testi
```bash
# (a) healthz  · 200=taze, 503=BAYAT ama süreç canlı (çöküş sonrası ~10dk normal)
ssh -i $K $A1 'curl -s -o /dev/null -w "healthz: %{http_code}\n" http://127.0.0.1:8080/healthz'

# (b) HERMES YAZMA PROBU — ~/.hermes gerçekten yazılabilir mi? (tur-1'in sessiz kırıklığının ölçüsü)
#     Aynı ad alanıyla geçici bir birim koşar; CANLI sürece dokunmaz.
ssh -i $K $A1 'sudo systemd-run --uid=ubuntu --pipe --wait --collect \
  -p NoNewPrivileges=true -p ProtectSystem=strict -p ProtectHome=read-only \
  -p ReadWritePaths="/opt/meridian /home/ubuntu/.cache /home/ubuntu/.hermes" \
  -p SystemCallArchitectures=native -p SystemCallFilter=@system-service \
  /bin/sh -c "touch /home/ubuntu/.hermes/.rw-probe && rm -f /home/ubuntu/.hermes/.rw-probe \
              && echo HERMES-RW-OK || echo HERMES-RW-KIRIK ; \
              (touch /home/ubuntu/.h3-negatif-kontrol 2>/dev/null && echo PROTECTHOME-KIRIK \
              || echo PROTECTHOME-OK)"'
#     BEKLENEN İKİ SATIR:  HERMES-RW-OK  +  PROTECTHOME-OK
#     (ikinci satır POZİTİF DEĞİL NEGATİF kontroldür: ev dizininin geri kalanı hâlâ salt-okunur)

# (c) TİCK AKIŞI — "is-active" ilerlemeyi kanıtlamaz (asılı-tick vakası, 2026-07-30).
#     scheduler_status.updated TAZELENİYOR mu: iki ölçüm arasında damga DEĞİŞMELİ.
ssh -i $K $A1 'cd /opt/meridian && export PATH=$HOME/.local/bin:$PATH
  for i in 1 2; do uv run --frozen --no-dev python -c "from meridian import store; \
    print(store.read_json(\"scheduler_status.json\",{}).get(\"updated\"))"; sleep 90; done'

# (d) BAR AKIŞI — arşivcinin ölçüsü `is-active` DEĞİL, satır sayısıdır (Redis düşse de aktif görünür)
ssh -i $K $A1 'cd /opt/meridian && export PATH=$HOME/.local/bin:$PATH
  uv run --frozen --no-dev python -m meridian.barsarchive --ozet --gun 2'
```

### 6) YEDEK BİRİMİ ELLE TETİKLE + skorları ÖLÇ
`meridian-backup.service`in `OnFailure=`i yoktur: sertleştirme onu kırarsa **kimse haber almaz**.
Bu adım pazarlığa açık değildir.
```bash
ssh -i $K $A1 'sudo systemctl start meridian-backup.service
  systemctl show meridian-backup.service -p ExecMainStatus -p Result | tr "\n" " "; echo
  ls -lh /home/ubuntu/backups/ | tail -3
  echo "--- maruziyet skorları (tur-1: 6.3) ---"
  for u in meridian meridian-barsarchive meridian-backup; do \
    printf "%-28s " $u; systemd-analyze security $u 2>/dev/null | tail -1; done'
```
Ölçülen üç sayıyı **ROADMAP §3 WP-H/H3 satırına yaz** (tahmini değil, ölçüleni).

### 7) GERİ ALMA (herhangi bir adım düşerse — tek blok)
```bash
ssh -i $K $A1 'set -e
  D=<adım-1de-not-edilen-YEDEK-yolu>
  sudo cp -a $D/meridian.service $D/meridian-barsarchive.service $D/meridian-backup.service \
             /etc/systemd/system/
  [ -d $D/meridian.service.d ] && sudo cp -a $D/meridian.service.d /etc/systemd/system/
  [ -d $D/meridian-barsarchive.service.d ] && sudo cp -a $D/meridian-barsarchive.service.d /etc/systemd/system/
  sudo systemctl daemon-reload
  sudo systemctl restart meridian meridian-barsarchive
  sleep 10; systemctl is-active meridian meridian-barsarchive | tr "\n" " "; echo'
```
**Kısmi geri alma da geçerlidir:** tek suçlu direktif biliniyorsa (adım 8'in çıktısı) yalnız o satırı
birim dosyasından çıkarmak yeter — bütün seti geri almak gerekmez.

### 8) İLK 24 SAAT — seccomp nöbeti (ATLANMAZ)
`SystemCallFilter=@system-service` bir çağrıyı keserse süreç **SIGSYS ile ölür** (bu bilinçli: EPERM
seçilseydi engel sıradan bir `OSError`a dönüşür ve bu depodaki `except OSError: pass` blokları onu
sessizce yutardı). Arıza **açılışta değil, o kod yoluna ilk girildiğinde** gelir — adım 3-6'daki
doğrulama onu yakalayamaz. Bu yüzden 24 saat izlenir:
```bash
# (a) SIGSYS ile ölüm oldu mu — üç birim için
ssh -i $K $A1 'journalctl -u meridian -u meridian-barsarchive -u meridian-backup --since "-24h" \
  | grep -Ei "SIGSYS|seccomp|status=31|Failed to set up mount namespacing|Read-only file system" | tail -30'
# (b) çekirdek denetim tarafı: hangi syscall numarası kesildi
ssh -i $K $A1 'sudo journalctl -k --since "-24h" | grep -i seccomp | tail -20'
# (c) restart çırpınması var mı (arşivcide OnFailure yok — tek görünür iz budur)
ssh -i $K $A1 'systemctl show meridian-barsarchive -p NRestarts; systemctl show meridian -p NRestarts'
# (d) ajan yazımları geri geldi mi (tur-1'de sessizce durmuştu)
ssh -i $K $A1 'cd /opt/meridian && grep -cE "agent_skills_synced|agent_integrations_synced" state/events.jsonl'
```
**Bir SIGSYS görülürse:** filtreyi kaldırma — **log moduna al.** İlgili birimde
`SystemCallFilter=@system-service` satırını geçici olarak şununla değiştir:
```
SystemCallLog=@clock @cpu-emulation @debug @module @mount @obsolete @privileged @raw-io @reboot @swap
```
Bu, `@system-service`in **dışladıklarından** hangisinin gerçekten çağrıldığını journal'a yazar ve
süreci **öldürmez**. (`SystemCallLog=@system-service` yanlıştır: *listelenen* çağrıları loglar, yani
izin verilen her çağrıyı — kullanılamaz gürültü.) Suçlu belirlenince ya o çağrı filtreye
`SystemCallFilter=@system-service <çağrı>` diye eklenir ya da kalemi dışarıda bırakma gerekçesi
birim dosyasına yazılır.

### Bilinen yan etki: `PrivateTmp` ve `/tmp/prescreen-*`
`hermes_composite.py::spawn_pending` ön-eleme alt süreçlerini `/tmp/prescreen-<id>` altında koşturur.
`PrivateTmp=true` bunu **kırmaz** (özel ad alanı yazılabilir) ama SSH kabuğundan o dizin **görünmez**.
Bakmak için:
```bash
ssh -i $K $A1 'sudo ls -d /tmp/systemd-private-*-meridian.service-*/tmp/prescreen-* 2>/dev/null | tail'
```

## Bölüm B4 — H10 aşama-1: **Litestream sürekli çoğaltma** (bakım penceresi)

H9'dan beri karar defteri `state/meridian.db`de (WAL). Yedek zinciri iki halkalı: gecelik tar
(23:32 UTC, 7 gün) + Mac-pull (30 gün). **Ölçülen kusur RPO'dur:** iki tar arasındaki her şey VM
kaybında kayıptır — en kötü hâlde bir tam işlem günü. Litestream bu aralığı **saniyelere** indirir.

> ### ⚠ DÜRÜST SINIR — BU AŞAMA **MEDYA ARIZASINI KAPSAMAZ**
> A1'de **ikinci fiziksel disk YOK.** Ölçüm (2026-08-02, salt-okuma keşif): `lsblk` → tek `sda`
> (46,6G) · `sda1` = `/` (45,6G, %10 dolu, **40G boş**) · `sda15` `/boot/efi` · `sda16` `/boot`.
> Yani `/home/ubuntu/replica` ile `/opt/meridian/state` **aynı blok cihazdadır**. Disk arızası
> ikisini birden götürür. Bu aşamanın kapsadığı: **mantıksal bozulma / yanlış migrasyon / yanlış
> silme / yarım yazım** → dakika hassasiyetli geri sarma; artı Mac'e çekilen replica kopyası.
> **Medya + bölge koruması AŞAMA-2'dir** (OCI Object Storage S3-uyumlu bucket; anahtar
> **OPERATÖRDE**, ROADMAP H10). `litestream.yml`de aşama-2'ye geçerken **yalnız `replica:` bloğu**
> değişecek şekilde yazıldı.

> ### ⚠ LİTESTREAM CANLI DEFTERE **YAZAR** (salt-okuma yeterli DEĞİL — ölçüldü, varsayılmadı)
> v0.5.15 kaynağı: `db.go:1075` `PRAGMA journal_mode=wal` · `db.go:1083/1089`
> `CREATE TABLE IF NOT EXISTS _litestream_seq` + `_litestream_lock` · `db.go:1544` her senkronda
> `INSERT ... ON CONFLICT` · `db.go:2627` `PRAGMA wal_checkpoint`. Yani **ilk `start`, canlı
> defterin ŞEMASINA iki tablo ekler** — prosedürün geri alınması en zor adımı budur ve bu yüzden
> `litestream_kur.sh` bayraksız koşumda **başlatmaz**.
> Güvenli taraf (bu da ölçüldü): DB dosyası yoksa litestream onu **yaratmaz**
> (`db.go:1030` "Exit if no database file exists") → `MERIDIAN_DB=off` acil anahtarı güvende.

**Dosyalar:** `deploy/oracle-a1/litestream.yml` (yapılandırma + tüm tasarım gerekçeleri) ·
`deploy/oracle-a1/meridian-litestream.service` (H3 tur-2 sertleştirme seti) ·
`deploy/oracle-a1/litestream_kur.sh` (sürüm-sabitli + sha256 kapılı, **idempotent**).
**`deploy.sh` bu birimi KURMAZ** — kurulum bir bakım penceresi kalemidir.

### Ön koşullar
- Çalışma ağacı temiz + depo A1'e taşınmış (`dagit.sh` kapısı).
- Bakım penceresi: worker'ın durması **şart değil** (birim `Requires=` taşımaz) ama ilk start
  seans dışında yapılır — checkpoint'ler yazarlarla kilit yarışına girer.
- `sudo` parolasız (betik `/usr/local/bin` + `/etc` + `/var/lib` altına yazar).

### 1) GERİ-ALMA YEDEĞİ ÖNCE (bu adım atlanırsa prosedür başlamaz)
```bash
K=~/.ssh/oci-a1.key; A1=ubuntu@130.61.126.87
# Defterin çevrimiçi tutarlı kopyası (yedek biriminin kullandığı yolun aynısı) — geri dönüş noktası
ssh -i $K $A1 'export PATH=$HOME/.local/bin:$PATH; cd /opt/meridian && \
  uv run --frozen --no-dev python -c "from meridian import storage; storage.backup_to(\"/home/ubuntu/backups/meridian.db.h10-oncesi\")" && \
  ls -la /home/ubuntu/backups/meridian.db.h10-oncesi'
```

### 2) Kurulum (idempotent; indirmeyi sha256 kapısı korur)
```bash
ssh -i $K $A1 'cd /opt/meridian && ./deploy/oracle-a1/litestream_kur.sh'
# Beklenen: sha256 EŞLEŞTİ · /usr/local/bin/litestream kuruldu · dizinler 0750 ubuntu:ubuntu
#           · /etc/litestream.yml + birim kuruldu · databases kuru doğrulaması geçti · ENABLE, BAŞLATILMADI
```
**Sürüm yükseltmede:** `litestream_kur.sh` içindeki `LS_SURUM` **ve** `LS_SHA256` birlikte
güncellenir; sha256 yayıncının `checksums.txt`inden okunur. Betik onu internetten **tazelemez**
(tazeleseydi kapı, "indirdiğimi indirdiğimle doğruladım" totolojisine dönerdi).

### 3) BAŞLATMA (ayrı karar — şemaya iki tablo eklenir)
```bash
ssh -i $K $A1 'sudo systemctl start meridian-litestream && sleep 5 && systemctl is-active meridian-litestream'
```

### 4) DOĞRULAMA — yürürlükteki direktifler (yorum değil, systemd'nin okuduğu değer)
```bash
ssh -i $K $A1 'systemd-analyze cat-config systemd/system/meridian-litestream.service | grep -E "ReadWritePaths|ProtectSystem|SystemCallFilter|CapabilityBoundingSet"'
ssh -i $K $A1 'systemd-analyze security meridian-litestream | tail -3'
```
> **BEKLENEN SKOR — TAHMİN, ÖLÇÜM DEĞİL.** Birim H3 tur-2 setinin **birebir aynısını** taşıyor
> (üç birimle ortak direktifler testle çivili) ve `ReadWritePaths`i **daha dar** (yalnız
> `state` + iki hedef dizin, `uv` ağacı yok) → **aynı sınıfa, 2,5–3,8 bandına** düşmesi beklenir.
> Bu bir tahmindir; **gerçek sayı bu adımda ölçülür ve ROADMAP'e ÖLÇÜLEN değer yazılır.**

### 5) DOĞRULAMA — duman testleri
```bash
# (a) journal: açılış hatası / SIGSYS var mı
ssh -i $K $A1 'journalctl -u meridian-litestream -n 40 --no-pager'

# (b) çoğaltma GERÇEKTEN yazıyor mu — "is-active" bunu KANITLAMAZ (barsarchive dersi)
ssh -i $K $A1 'find /home/ubuntu/replica -type f | wc -l; find /home/ubuntu/replica -type f -printf "%T@ %p\n" | sort -n | tail -3'

# (c) REPLICA YAŞI — BU BİRİMİN GERÇEK ÖLÇÜSÜ. İki ölçüm arasında en yeni dosyanın damgası
#     DEĞİŞMELİ (defterde yazım varken). Değişmiyorsa çoğaltma sessizce durmuştur.
ssh -i $K $A1 'date -u; find /home/ubuntu/replica -type f -newermt "-5 minutes" | wc -l'

# (d) litestream'in kendi görüşü
ssh -i $K $A1 'litestream databases -config /etc/litestream.yml; litestream ltx -config /etc/litestream.yml /opt/meridian/state/meridian.db 2>&1 | tail -5'

# (e) BEKLENEN YAN ETKİ — iki yeni tablo görünecek (arıza DEĞİL, yukarıdaki uyarı)
ssh -i $K $A1 'cd /opt/meridian && sqlite3 state/meridian.db "SELECT name FROM sqlite_master WHERE type=\"table\" ORDER BY 1;" 2>/dev/null || echo "(sqlite3 yok — uv run --frozen --no-dev python -c ile bak)"'

# (f) DEFTER HÂLÂ İLERLİYOR MU (çoğaltma yazarları bloklamadı mı)
ssh -i $K $A1 'curl -s localhost:8080/healthz | head -c 200; echo'
```

### 6) RESTORE TATBİKATI — **H7 ritüeline eklenen adım** (çeyreklik)
Tatbikat yapılmamış bir yedek, yedek değildir. H7 ritüeli bugüne dek **tar arşivini** tatbik
ediyordu; H10'dan sonra **replica'dan geri yükleme** de her turda ölçülür.
> **TATBİKAT BEYANI GÜNCELLENDİ (2026-08-02, tar kapsam daraltması):** H7'nin "64/64 JSON sağlam"
> restore'u `state/sprint` alt-ağacını İÇEREN bir arşiv üzerinde yapılmıştı. `meridian-backup.service`
> artık `--exclude=state/sprint` taşıyor → bundan sonraki tar tatbikatları sprint alt-ağacını arşivde
> **aramaz**; yokluğu arıza değil, beyanlı kapsamdır (gerekçe + kayıp beyanı birim dosyasının tepe
> yorumunda). `bars/`, `bars_intraday/`, `intraday_bars/` kapsamda KALIR ve tatbikatta doğrulanır.
```bash
# CANLI DEFTERE DOKUNMAZ: -o ile AYRI dosyaya yazılır, -integrity-check ile SQLite'a doğrulatılır.
ssh -i $K $A1 'litestream restore -config /etc/litestream.yml \
    -o /tmp/tatbikat-meridian.db -integrity-check full /opt/meridian/state/meridian.db && \
  ls -la /tmp/tatbikat-meridian.db'

# SAYILAR CANLIYLA TUTUYOR MU (H7'nin "64/64 JSON sağlam" adımının SQLite karşılığı)
ssh -i $K $A1 'cd /opt/meridian && uv run --frozen --no-dev python -c "
import sqlite3
for yol in (\"state/meridian.db\", \"/tmp/tatbikat-meridian.db\"):
    c = sqlite3.connect(yol)
    print(yol, {t: c.execute(f\"SELECT COUNT(*) FROM {t}\").fetchone()[0] for t in (\"trades\",\"trade_plans\",\"scoreboard\")})
    c.close()"'

# GERİ SARMA TATBİKATI (mantıksal bozulma senaryosu): 1 saat öncesine
ssh -i $K $A1 'litestream restore -config /etc/litestream.yml -timestamp "$(date -u -d "-1 hour" +%Y-%m-%dT%H:%M:%SZ)" \
    -o /tmp/tatbikat-1saat-once.db /opt/meridian/state/meridian.db && ls -la /tmp/tatbikat-1saat-once.db'

# TEMİZLİK
ssh -i $K $A1 'rm -f /tmp/tatbikat-meridian.db /tmp/tatbikat-1saat-once.db'
```
**Mac'teki kopyadan geri yükleme** (VM tamamen gitmişse): `ops/pull-a1-backups.sh` replica bacağı
`~/AI-Trading/backups/a1-replica/` altına çeker. Mac'te litestream kuruluysa:
```bash
litestream restore -o /tmp/kurtarilan.db "file://$HOME/AI-Trading/backups/a1-replica/meridian.db"
```
Not: Mac kopyası A1'in **üst kümesidir** (silme yok) — `restore` noktayı TXID/zaman damgasına göre
seçer, fazlalık eski snapshot yalnız daha eskiye sarma imkânıdır.

### 7) İLK 24 SAAT — seccomp nöbeti (ATLANMAZ)
Bu birimde **`OnFailure=` YOK** ve `Restart=always` var (gerekçe birim dosyasında: fail-notify
gövdesi sabit metinle "meridian.service FAILED" der; buraya bağlamak yanlış alarm üretirdi).
Yani bir `SystemCallFilter` kesmesi **sessiz çoğaltma kaybıdır** — kayıp ancak restore gerektiğinde
görülür.
```bash
ssh -i $K $A1 'journalctl -u meridian-litestream --since "24 hours ago" | grep -Ei "SIGSYS|Main process exited|Scheduled restart" | tail -20'
ssh -i $K $A1 'systemctl show meridian-litestream -p NRestarts'
# ÖLÇÜ: NRestarts artmamalı VE replica'daki en yeni dosya damgası ilerlemeli (adım 5c).
```
SIGSYS görülürse: filtreyi kaldırma, **log moduna al** — reçete Bölüm B3'ün sonundadır
(`SystemCallLog=@clock @cpu-emulation @debug @module @mount @obsolete @privileged @raw-io @reboot @swap`).

### 8) GERİ ALMA (tek blok)
```bash
ssh -i $K $A1 'set -x
  sudo systemctl disable --now meridian-litestream
  sudo rm -f /etc/systemd/system/meridian-litestream.service /etc/litestream.yml
  sudo systemctl daemon-reload
  # replica + meta dizinleri: VERİ TAŞIRLAR. Silmek geri-alma DEĞİL, temizliktir — ayrı karar:
  #   sudo rm -rf /home/ubuntu/replica /var/lib/litestream
  # ikili de kalabilir (koşmayan bir ikili zarar vermez): sudo rm -f /usr/local/bin/litestream
'
```
**`_litestream_seq` / `_litestream_lock` tabloları:** geri almada **bırakılır**. Zararsızdırlar
(Meridian'ın hiçbir kodu tablo envanteri saymaz — tarama: `sqlite_master` yalnız
`tests/test_denetim_defter_v159.py::test_c4_sema_migrasyon_transaction_ININ_ICINDE_kurulur`de, sandbox'ta ve negatif iddia). Düşürülecekse **worker
DURMUŞKEN** yapılır (CLAUDE.md §5: canlı worker koşarken state'e yazma):
```bash
# BAKIM PENCERESİ — worker durmuş olmalı
ssh -i $K $A1 'sudo systemctl stop meridian && cd /opt/meridian && uv run --frozen --no-dev python -c "
import sqlite3; c=sqlite3.connect(\"state/meridian.db\")
c.execute(\"DROP TABLE IF EXISTS _litestream_seq\"); c.execute(\"DROP TABLE IF EXISTS _litestream_lock\")
c.commit(); c.close(); print(\"düşürüldü\")" && sudo systemctl start meridian'
```

### 9) ÜÇÜNCÜ KOPYA — **bar arşivi** için seçenek tablosu (KARAR OPERATÖRE; bu tablo VERİDİR)
**Neden gündemde:** WP-U operasyonel bulgusu — mevcut Massive planı artık yalnız ~son 2 ayı
veriyor, dolayısıyla **2004'e giden yerel bar arşivi yeniden-üretilemez KALINTIdır; kaybı kalıcı
kayıptır** (ROADMAP WP-U). Litestream **yalnız `meridian.db`yi** çoğaltır — bar arşivi SQLite'ta
değil, CSV/JSONL dosyalarındadır ve bu turun kapsamı DIŞINDADIR.

**Ölçülen boyutlar (A1, 2026-08-02):** `state/` **617M** → `bars/` **59M** (260 CSV) ·
`bars_intraday/` 43M · `intraday_bars/` 40M · `sprint/` **438M** (4 kum-havuzu × ~110M) ·
`meridian.db` 1,3M. Gecelik tar.gz **~112M/gün**; A1'de 7 gün (421M), Mac'te 30 gün.
**Kritik okuma:** günlük tar'ın hacmini **yeniden-üretilebilir sprint kum-havuzları** domine
ediyor; yeri doldurulamaz olan bars ise toplamın **onda biri**.
**Ek ölçüm (2026-08-02, aynı keşif):** `tar -cz --exclude=state/sprint -C /opt/meridian state | wc -c`
= **40.497.179 bayt (~40,5M)** — satır 5'in "~15M" tahmini YANLIŞTI, ölçülen budur (kalan hacmi
bars 59M + iki seans-içi arşiv 83M taşıyor). Kum havuzlarının kendisi de ayrıca küçülüyor:
`sprint.SKIP_COPY`ye iki seans-içi arşiv eklendi — **ÖLÇÜLDÜ (2026-08-02 22:04, sandbox
20260802-220408): 30 MB/kum-havuzu** (~27M türetimi doğrulandı; dökümde bars_intraday/
intraday_bars/çıplak meridian.db yok; kalan hacim events.jsonl 10M + dashboard.log 5M + cf 4M).
Kararlı durum 4 dizin × ~30M ≈ 120M'ye yakınsar (eski ~110M'likler budandıkça).

| # | Seçenek | Neyi kapsar | Tazelik | Yer/bant | Ön koşul | Not |
|---|---|---|---|---|---|---|
| 0 | **BUGÜNKÜ TABAN** (değişiklik yok) | bars **zaten** gecelik tar'ın içinde → A1 + Mac = **2 kopya** | 1 gün | 112M/gün × 30 | — | "üçüncü kopya" gerçekten ÜÇÜNCÜdür; ikinci kopya zaten var |
| 1 | **Mac-pull'a ayrı `bars` bacağı** (rsync delta, `--delete` yok) | `state/bars` (59M) | çekim kadansı | ilk 59M, sonra delta (~KB) | yok — `ops/pull-a1-backups.sh`'a bir bacak | En ucuzu; ama Mac ile tar aynı makinede → yine **2. kopya**, 3. değil |
| 2 | **OCI Object Storage bucket** (aşama-2) | `meridian.db` (litestream) **+** bars (rclone/aws-cli) | dakikalar / günlük | Always-Free 20G; 59M+ | **anahtar OPERATÖRDE** | Tek seçenek ki hem **off-box** hem **off-media**; H10 aşama-2 ile aynı anahtarı kullanır |
| 3 | **Harici disk / ikinci makine** (Mac dışı) | seçilen ne varsa | elle / haftalık | disk maliyeti | operatör fiziksel erişim | Gerçek 3. kopya; otomasyonu yok, ritüele bağlı |
| 4 | **Bağımsız bulut** (B2 / S3 / rsync.net) | bars + db | günlük | ~1$/ay altı | hesap + anahtar | Oracle hesabı kapanma riskini de kapsar (seçenek 2 kapsamaz) |
| 5 | **tar kapsamını daralt** (`sprint/` hariç) + sıklığı artır | tar'ı 112,5M → **40,5M'e** indirir (ÖLÇÜLDÜ; eski ~15M tahmini yanlıştı) | günden saatlere inebilir | çok ucuz | ~~birim düzenlemesi~~ **UYGULANDI repo'da (2026-08-02):** `--exclude=state/sprint` + çift-yönlü çivi (`test_h3_tur2_v174::test_backup_kapsami_sprint_haric_bars_dahil`); **CANLIDA (2026-08-02 ~20:50 UTC penceresi):** kuruldu + iki kez elle test-ateşlendi; ölçülen tar **40.593.530 bayt** (sprint 0 üye · bars 261 · db.yedek 1). İlk ateşleme H9'dan beri sessiz düşen python bacağını da yakaladı (`\"` kaçışı → SyntaxError; `sys.argv` biçimiyle düzeltildi, artık `.yedek` GERÇEKTEN doğuyor — ayrıntı birim yorumu + günlük) | Kopya SAYISINI artırmaz ama 1–4'ün hepsini ucuzlatır. **Sıklık artışı BİLEREK yapılmadı:** defterin dakika-RPO'sunu litestream zaten taşıyor, bars günde bir değişiyor — ölçülebilir faydası şimdilik yok, operatör isterse artık ucuz |

**Bu turun hükmü (2026-08-02 güncellemesi):** üçüncü-kopya seçimi HÂLÂ yapılmadı — 1–4 operatör
kalemidir. Satır 5'in repo yarısı bu turda kapandı (kapsam daraltması + kum-havuzu küçültmesi,
ölçümleriyle); "kum-havuzu birikimi ayrı bir bulgudur" notu da kapandı — birikim SINIRLIYMIŞ
(SANDBOX_KEEP=3, kararlı durum 4 dizin), 2026-08-02 sabahındaki 4×5dk damgalarının kökü C15
damga-ezme kusuruydu (154 kadans başlangıcı ölçüldü; düzeltme aynı gün canlıya indi, ayrıntı
MERIDIAN_ENGINEERING_LOG.md).

## Bölüm C — sırlar (asla repo'da/git'te taşınMAZ)
`state/secrets.json` git-ignored. İki yol:
- **Panodan yeniden gir** (en temiz): Ayarlar sayfasından FMP/Alpaca/Gemini anahtarlarını tekrar gir.
- **Elle kopyala:** `scp state/secrets.json ubuntu@<A1-IP>:/opt/meridian/state/` sonra `chmod 600`.
- **FMP anahtarını rotasyonla** (sohbette bir kez ifşa olmuştu) — taşımadan önce iyi fırsat.

## Bölüm D — hermes-agent beyni
`deploy.sh` ikili yoksa **resmi installer'ı otomatik koşar**
(`https://hermes-agent.nousresearch.com/install.sh`, aarch64 Linux) ve `hermes --version` ile
doğrular. Kurulum düşerse **kurulum durmaz** — açık uyarı basar ve devam eder.

Meridian ikiliyi şurada arar (`hermes.py:_hermes_bin()`): `HERMES_LOCAL_BIN` → `PATH` →
`~/.hermes/bin/hermes` → `~/.local/bin/hermes`. `meridian.service`'in `PATH`'i
`/home/ubuntu/.local/bin`'i zaten içerir.

**Beyin zincirinin A1'deki gerçeği:** claude (kimliksiz → atlanıyor) → **nous** → **gemini**.
`state/secrets.json`'da **`NOUS_API_KEY` YOK** → nous bacağı **ancak yerel ikiliyle** çalışır.
Yani installer düşerse zincirde pratikte yalnız **gemini** (`GEMINI_API_KEY`) kalır.
- **Alternatif (ikilisiz):** Ayarlar'dan `NOUS_ENDPOINT=<portal-url>` → uzak Nous Portal.
- Ajan hiç yoksa Meridian **deterministik öneriye** düşer — döngü/kapı/işlem çalışmaya devam eder.

## Bölüm E — panoya erişim (güvenli)
```bash
# SSH tünel — port'u internete açmadan panoyu yerelde aç
ssh -i ~/Documents/OCI/ssh-key-2026-07-21.key -L 8080:127.0.0.1:8080 ubuntu@130.61.126.87
# tarayıcı: http://localhost:8080   (token gerekmez, tünel yerel-origin)
```

## Doğrulama (A1'de)

### 1. Anında (cutover.sh bunları zaten basar)
```bash
systemctl is-active redis-server meridian meridian-barsarchive
systemctl list-timers 'meridian-*'   # meridian-backup.timer sırada mı
redis-cli ping                       # PONG
curl -s localhost:8080/healthz       # 200=taze · 503=BAYAT ama süreç canlı (/healthz `api.py::healthz`de VAR)
curl -s localhost:8080/api/today     # 200 + JSON
journalctl -u meridian -f            # canlı log
# tam suite A1'de KOŞULMAZ (TSK-230): pytest DEV grubundadır ve A1'e kurulmaz (A0 `--no-dev`);
# kurmak bir sonraki dağıtımda "VENV DEĞİŞTİ" üretir. Test hükmü yerelde, Rol-1'dedir (CLAUDE.md §6).
```
Reboot testi: `sudo reboot` → tekrar SSH → `systemctl is-active meridian` **active** olmalı
(launchd'nin Mac'te yapamadığı şey).

### 2. TAŞIMA SONRASI — bir seans + bir hafta içinde ölçülecekler
Bunlar "servis ayakta mı" değil, **taşımanın işe yarayıp yaramadığı** ölçüleridir. `is-active`
yeşilken bunların hepsi ölü olabilir; o yüzden ayrı liste.

| # | ne beklenir | nasıl ölçülür | taşıma anındaki taban |
|---|---|---|---|
| a | `validation_ledger`'a **`pencere_id:"R1"`** damgalı satır AKMAYA başlar | TSK-020 Kademe C göçünden (D6-2) SONRA defter DB'dedir, dosyası `.migrated` adıyla DONAR — `grep` orada sessizce bayat sayar. Salt-okur DB sorgusu: `uv run --frozen --no-dev python -c "import sqlite3; c=sqlite3.connect('file:state/meridian.db?mode=ro', uri=True); print(c.execute('SELECT COUNT(*) FROM validation_ledger WHERE json_extract(extra_json, ?) = ?', ('\$.pencere_id', 'R1')).fetchone()[0])"` — göçten ÖNCE tablo yoktur ve sorgu `no such table` ile DÜŞER (sessiz 0 değil); o zaman `grep -c '"pencere_id": *"R1"' state/validation_ledger.jsonl` | **0** (204 satırın hepsi `pencere_id=null`; R1 bugün, 2026-07-30 açıldı) |
| b | **PBO tabanı birikmeye** başlar (PBO YALNIZ `pencere_id==R1` satırlarını sayar) | `uv run --frozen --no-dev python -c "from meridian import validation,store,dataset; d=store.read_jsonl('validation_ledger.jsonl',limit=validation.LEDGER_CAP); print(validation.pbo_cscv([r for r in d if r.get('pencere_id')==dataset.ROTATION_ID]))"` → `durum` `olculemedi`→`olculdu` | `olculemedi` (aday yok) |
| c | `hotstate_down` **çırpınması A1'de yeniden ölçülür** — Redis artık *aynı makinede* (yerelde bu tek olay olay defterinin %91'ini yiyordu) | `grep -c hotstate_down state/events.jsonl` (7 gün sonra tekrar) | yerel taban: **15.860/hafta** |
| d | `events.jsonl`'da **scheduler'ın nous kadansı** görünür | `grep -E 'nous_eval\|haftalik' state/events.jsonl \| tail` | henüz yok — kadans **restart'la** iner |
| e | bar arşivi gerçekten yazıyor (yalnız `is-active` YETMEZ) | `uv run --frozen --no-dev python -m meridian.barsarchive --ozet --gun 5` | `satir` artıyor olmalı |
| f | günlük yedek düştü mü | `ls -la /home/ubuntu/backups/` | ilk atış: kurulumdan sonraki 23:30 UTC |

## Geri dönüş
Mac'teki kurulum olduğu gibi duruyor (cutover repoyu/state'i **kopyalar, silmez**); A1 sorun
çıkarırsa yerelde `./serve.sh` ile devam.

**İki kopya AYNI ANDA canlı işlem yapMAMALI** — aynı Alpaca hesabına **çift emir** gider, pozisyon
boyutu ikiye katlanır, iç defter–broker mutabakatı bozulur (`MIRROR_DRIFT`). Sıra şu:
```bash
# 1) ÖNCE A1'i durdur
ssh -i ~/Documents/OCI/ssh-key-2026-07-21.key ubuntu@130.61.126.87 \
  'sudo systemctl stop meridian meridian-barsarchive'
# 2) SONRA yerelde başlat
./serve.sh
```
Not: A1'de biriken `state/` yerele geri dönmez — geri dönüşte yereldeki state **taşıma anındaki**
hâlidir. Aradaki öğrenmeyi korumak istiyorsan önce `rsync` ile A1'den geri çek.

## Opsiyonel devre kesici: WS kopuşunda girişleri iptal et (K1, 2026-07-30)

`MERIDIAN_WS_DISCONNECT_CANCEL_ENTRIES=1`

**Ne yapar:** `mirror_stream` WebSocket bağlantısı koptuğunda DOLMAMIŞ giriş emirlerini iptal eder
(`_maybe_cancel_entries`). Dolu pozisyonların koruyucu bacaklarına **asla dokunmaz** — çıplak
pozisyon yasağı bu bayrakla da geçerlidir.

**Varsayılan KAPALI ve bu bilinçli.** Bayrak bugüne kadar hiçbir dağıtımda (serve.sh, launchd
plist, `meridian.service`, docker-compose) set edilmiyordu ve hiçbir runbook onu anmıyordu — yani
özellik vardı, "ne zaman açılır" bilgisi hiçbir yerde YOKTU. Kopukluk özelliğin kendisi değil, bu
sessizlikti.

**NE ZAMAN 1 YAPILIR:**
- Emir akışı **canlı paraya** geçtiğinde (L1+). Kağıt modda kapalı kalması doğrudur: iptal
  edilmeyen bir kağıt emrin maliyeti yok, ama ölçümü bozar.
- Kopuş süresi bir barı aşabiliyorsa: WS kopukken tetiklenen bir giriş emri, iç defterin
  görmediği bir dolum üretebilir → `MIRROR_DRIFT` alarmı ve mutabakat farkı.
- Ağın kararsız olduğu bir sunucuda (kopuş/toparlanma döngüsü sık) — kopuş sıklığını
  `state/events.jsonl`'daki `*_down` olaylarından ölç, tahminle karar verme.

**NE ZAMAN 0 BIRAKILIR:**
- L0 kağıt modunda (bugünkü durum): gölge/kağıt ölçümlerin kesintiye uğramaması yeğlenir.
- Kopuşlar saniyeler mertebesindeyse: iptal etmek, bir sonraki barda yeniden girmek anlamına gelir
  ve friksiyonu ölçüme sokar.

**Açtıktan sonra doğrula:** `journalctl -u meridian | grep -i cancel_entries` ve panodaki
"başarısız/iptal edilen emir" satırı — iptalin GERÇEKTEN çalıştığı görülmeden bayrak güvenilmez.

---

## Telemetri (Grafana) erişimi — TSK-020 UYGULA-9 Faz A (2026-09-28)

**Ne:** Prometheus (`127.0.0.1:9095`) + node_exporter (`127.0.0.1:9100`) + Grafana (`127.0.0.1:3000`); üçü de
docker, imajlar etiket + dizin özetiyle pinli. Tasarım: `docs/TASARIM-TELEMETRI-PROMETHEUS-2026-09-28.md`
(operatör onayı 2026-09-28: Faz A→B, docker, yalnız ssh tüneli). Hiçbir port dışarı açık DEĞİL. Birimler, drop-in
ve yapılandırma `deploy/telemetri/` altında; A0 rolü (`site.yml`) kopyalar, ETKİNLEŞTİRMEZ ve BAŞLATMAZ.

**Tek-kaynak beyanı (tasarım T7):** gecikmenin GEÇMİŞİ (zaman serisi) Grafana'dadır; ANLIK durum panoda kalır
(`/api/diagnostics` IO çipi, `/api/hermes` LLM p50/p95 — aynı kaynağın iki görünümü, kopya değil). Panoda Grafana
bağlantısı YOK (tünelle açılır); `/api/gateway` gecikme OKUMAZ (bilinçli — Grafana okur). Alarm TEK kanaldadır
(`obs` → notify/bekçi): Alertmanager kurulmadı, Grafana uyarıları kapalı — Grafana'da görülen bir eşik aşımı
alarm DEĞİLDİR. Hiçbir kapı/kill kararı Prometheus'tan okumaz; KILL#1'in canlı çapası ayrı karttır (Faz C).

### Erişim (ssh tüneli)

```bash
ssh -i ~/.ssh/oci-a1.key -N -L 3000:127.0.0.1:3000 ubuntu@130.61.126.87
# tarayıcı: http://localhost:3000 — kullanıcı `admin`; Prometheus arayüzü gerekirse ek olarak -L 9095:127.0.0.1:9095
```

Parola A1'de `/etc/meridian/grafana_admin_parola`dadır (0400 root, Vault Agent render eder). Onu görmek
operatörün KENDİ terminalindedir (`ssh … 'sudo cat /etc/meridian/grafana_admin_parola'`); hiçbir ajan ya da
Claude oturumu çıktısına basılmaz.

### İlk kurulum (Rol-1; sıra sözleşmedir)

**0. Önkoşul + kimlik doğrulaması.** Dilim main'de ve `dagit` ile A1'de (yeni `policies/meridian-agent.hcl` ve
`agent.hcl` `/opt/meridian/deploy/vault/` altına gelir). İmajları önceden çek (ilk `start` çekimi beklemesin) ve
konteyner kullanıcı kimliklerini ÖLÇ — `defaults/main.yml` `telemetri_*_uid/gid` imaj yapılandırmasından
okundu (prometheus `nobody`, grafana `472`), passwd'den ölçülmedi:

```bash
ssh -i ~/.ssh/oci-a1.key ubuntu@130.61.126.87 'sudo docker pull prom/node-exporter:v1.12.1@sha256:1b4e4438faca4dd7e001dd445d161a4a2091b0fededa84093b3a8dfeae1f1be0'
ssh -i ~/.ssh/oci-a1.key ubuntu@130.61.126.87 'sudo docker pull prom/prometheus:v3.15.0@sha256:efd719c99d83b060d9daefdcf00360461adf279f45ef5391f8d111892118753e'
ssh -i ~/.ssh/oci-a1.key ubuntu@130.61.126.87 'sudo docker pull grafana/grafana:13.2.2@sha256:ac461fb352abc50da10a51c7d02462e9c05488f11f53f14b3ad79a8145f638a0'
ssh -i ~/.ssh/oci-a1.key ubuntu@130.61.126.87 'sudo docker run --rm --entrypoint id prom/prometheus:v3.15.0@sha256:efd719c99d83b060d9daefdcf00360461adf279f45ef5391f8d111892118753e'
# beklenen: uid=65534(nobody) gid=65534(nogroup)
ssh -i ~/.ssh/oci-a1.key ubuntu@130.61.126.87 'sudo docker run --rm --entrypoint id grafana/grafana:13.2.2@sha256:ac461fb352abc50da10a51c7d02462e9c05488f11f53f14b3ad79a8145f638a0'
# beklenen: uid=472(grafana) gid=0(root)
```

Farklı çıkarsa DUR: `defaults/main.yml` telemetri kimlikleri + `meridian-grafana.service.d/50-grafana-credential.conf`
`install -o/-g` aynı değişiklikte düzeltilir (v584 C3/D3 ikisini kıyaslar).

**1. A0 rolü** — birimler, drop-in, yapılandırma ve veri dizinleri (`/var/lib/meridian-telemetri/{prometheus,grafana}`)
kurulur; hiçbir telemetri birimi etkinleştirilmez ya da başlatılmaz:

```bash
ansible-playbook -i deploy/ansible/inventory.ini deploy/ansible/site.yml --check --diff
ansible-playbook -i deploy/ansible/inventory.ini deploy/ansible/site.yml
```

Bilinen check-kipi sınırı: yeni `meridian-grafana.service.d` dizini ilk `--check`te henüz yoktur ve "Drop-in
dosyaları" görevi o öğe için `Destination directory … does not exist` ile düşer (ansible copy modülü check kipinde
dizin yaratmaz; gerçek koşumda dizin görevi önce koşar). Temiz bir kuru koşum isteniyorsa önce
`ssh … 'sudo install -d -m 0755 /etc/systemd/system/meridian-grafana.service.d'`. Telemetri yapılandırma kopyası bu
sınıfa girmez (hedefi `/` ile biter; check kipi "yaratılacak" der).

Bu ilk koşumda parola henüz kasada olmadığı için sır denetiminin İZİN-DENETİMLİ kapısı
`İZİN DENETİMİ ATLANDI (dosya YOK): /etc/meridian/grafana_admin_parola` satırını basar — beklenen hâl, playbook durmaz.
Adım 2'den sonraki her `site.yml` koşumu dosyayı root:root 0400 olarak denetler ve farklıysa DURUR
(`defaults/main.yml::izin_denetimli_sir_dosyalari`; rotasyon dışı ≠ denetim dışı).

**2. Parola kasaya** — yeni bir sırdır (`vault_sir_koy.sh` mevcut dosyaları taşır, bunu DEĞİL). Değer yalnız
borudan akar; hiçbir değişkene, argümana ya da çıktıya girmez. Politika ÖNCE (yoksa Agent yeni yolu okuyamaz),
değer İKİNCİ, Agent yapılandırması SON:

```bash
ssh -i ~/.ssh/oci-a1.key ubuntu@130.61.126.87 'sudo bash -s' <<'KASA'
set -euo pipefail
export VAULT_ADDR=http://127.0.0.1:8200
trap 'rm -f /root/.vault-token' EXIT
/usr/local/bin/vault login -no-print - < /etc/vault/admin.token >/dev/null
/usr/local/bin/vault policy write meridian-agent /opt/meridian/deploy/vault/policies/meridian-agent.hcl
openssl rand -hex 24 | tr -d '\n' | /usr/local/bin/vault kv put secret/meridian/grafana_admin_parola value=- >/dev/null
install -o root -g vault -m 0640 /opt/meridian/deploy/vault/agent.hcl /etc/vault/agent.hcl
systemctl restart vault-agent
KASA
ssh -i ~/.ssh/oci-a1.key ubuntu@130.61.126.87 'sudo stat -c "%a %U %s" /etc/meridian/grafana_admin_parola'
# beklenen: 400 root 48   (yalnız izin/sahip/boyut — değer değil)
```

Agent yeniden başlaması tüketicileri yeniden başlatmaz (her hedef aynı değerle yeniden render edilir).

**3. Elle başlat + test-ateşle** (CLAUDE.md §9 "kurulu ≠ çalışır"; her birim AYRI komut):

```bash
ssh -i ~/.ssh/oci-a1.key ubuntu@130.61.126.87 'sudo systemctl start meridian-node-exporter'
ssh -i ~/.ssh/oci-a1.key ubuntu@130.61.126.87 'sudo systemctl start meridian-prometheus'
ssh -i ~/.ssh/oci-a1.key ubuntu@130.61.126.87 'sudo systemctl start meridian-grafana'
```

**4. Doğrulama** (her satırın beklenen çıktısı yanında):

```bash
ssh -i ~/.ssh/oci-a1.key ubuntu@130.61.126.87 'systemctl is-active meridian-node-exporter meridian-prometheus meridian-grafana'
# active ×3
ssh -i ~/.ssh/oci-a1.key ubuntu@130.61.126.87 'curl -s 127.0.0.1:9095/-/ready'
# Prometheus Server is Ready.
ssh -i ~/.ssh/oci-a1.key ubuntu@130.61.126.87 'curl -s 127.0.0.1:9095/api/v1/targets | jq -r ".data.activeTargets[] | [.labels.job, .health, .lastError] | @tsv"'
# apisix up · meridian up · node up (lastError boş)
ssh -i ~/.ssh/oci-a1.key ubuntu@130.61.126.87 'curl -s 127.0.0.1:9095/api/v1/status/runtimeinfo | jq -r .data.storageRetention'
# 30d or 2GiB
ssh -i ~/.ssh/oci-a1.key ubuntu@130.61.126.87 'sudo ss -ltnp | grep -E ":(9095|9100|3000) "'
# üçü de 127.0.0.1:<port> — 0.0.0.0 ya da [::] GÖRÜNMEMELİ
ssh -i ~/.ssh/oci-a1.key ubuntu@130.61.126.87 'curl -s 127.0.0.1:3000/api/health; curl -s -o /dev/null -w " anonim=%{http_code}\n" 127.0.0.1:3000/api/org'
# "database": "ok" … anonim=401
ssh -i ~/.ssh/oci-a1.key ubuntu@130.61.126.87 'sudo docker inspect -f "{{.Name}} bellek={{.HostConfig.Memory}} kullanici={{.Config.User}}" meridian-node-exporter meridian-prometheus meridian-grafana'
# bellek 67108864 / 536870912 / 536870912 ; kullanıcı nobody / nobody / 472
ssh -i ~/.ssh/oci-a1.key ubuntu@130.61.126.87 'sudo stat -c "%a %u" /run/meridian-grafana/grafana_admin_parola'
# 400 472
```

Tünelle giriş yapılıp "Meridian — gecikme telemetrisi" panosunun altı paneli veri gösterdiği görülür (geçit p50/p95
rota başına, LLM p50/p95, CPU, RAM, `/` + `/opt/veri` doluluğu). Ardından test-ateşleme:
`ssh … 'sudo systemctl restart meridian-grafana'` → sağlık satırı yeniden.

**5. Etkinleştirme** — test-ateşleme temiz geçtikten sonra, AYRI bir değişiklikle: üç birim
`defaults/main.yml::etkin_birimler`e (ve `tests/test_ansible_a0_v451.py` `UZUN_OMURLU_BIRIMLER` kümesine — rol
onları asla yeniden başlatmasın) → commit → `site.yml`. O güne kadar birimler reboot'ta AÇILMAZ.

### Yapılandırma değişikliği · imaj yükseltme

Depoda düzenle → `site.yml` (kopyalar, restart ETMEZ) → `ssh … 'sudo systemctl restart meridian-prometheus'` (ya da
`meridian-grafana`). Panolar arayüzden değiştirilemez (`allowUiUpdates: false`); kaynak
`deploy/telemetri/grafana/panolar/`dır. İmaj yükseltmesi birimdeki `etiket@sha256:` değerinin değişmesidir: özet iki
kaynaktan ölçülür (Docker Hub tag API `digest` + registry `Docker-Content-Digest` başlığı) ve eşit olmalıdır;
`latest` yasak (v584).

### Parola döndürme (Grafana değeri YALNIZ ilk açılışta okur)

Kasadaki değeri değiştirmek yönetici hesabını DEĞİŞTİRMEZ (Grafana `GF_SECURITY_ADMIN_PASSWORD` değerini yalnız
veritabanı ilk kurulurken hesaba yazar). `sir_rotasyon.sh` bu sırrı bu yüzden TAŞIMAZ (v447
`ROTASYON_DISI_KREDENSIYELLER`). Sıra: adım 2'nin `openssl rand … | vault kv put …` satırı (login + trap ile) →
Agent ≤1 dk içinde render eder (`stat -c %y` ile mtime) → hesabı dosyadan güncelle (değer stdin'den):

```bash
ssh -i ~/.ssh/oci-a1.key ubuntu@130.61.126.87 'sudo sh -c "docker exec -i meridian-grafana grafana cli admin reset-admin-password --password-from-stdin < /etc/meridian/grafana_admin_parola"'
```

ÖLÇÜLMEDİ: `--password-from-stdin` Grafana 13.2.2 CLI kaynağında var; A1'de ilk döndürmede doğrulanır.

### Geri alma · bedel

Durdurmak: üç birim için ayrı ayrı `ssh … 'sudo systemctl stop <birim>'`. Veri `/var/lib/meridian-telemetri`
altında kalır; silmek operatör kararıdır. Bedel (tasarım §5): üç loopback süreç; disk ≤2GB TSDB + imajlar (`/`
üstünde; `docker images` ile ölçülür); RAM tavanı (konteyner `--memory`) meridian-prometheus 512M +
meridian-node-exporter 64M + meridian-grafana 512M = 1088M — Grafana 256M'den 512M'e canlı ölçümle çıktı
(2026-09-28: ilk açılış göçü ~324 MB → OOM; kararlı 222,5 MiB / 256 MiB); node_exporter ev sahibinin
dünyaya-okunur dosyalarını görebilir (0400/0600 sır dosyalarını göremez).

---

## Docker konteyner bellek tavanı — TSK-247 (2026-09-28)

**Ne:** `apisix`, `apisix-etcd` ve `hindsight-cp` birimlerindeki `MemoryMax=` YALNIZ `docker run` istemcisini
sınırlıyordu; konteyner dockerd'nin cgroup'unda koşar. Rol-1 A1 ölçümü (2026-09-28): `docker inspect`
`HostConfig.Memory` = 0 → üç konteynerin tavanı makinenin tamamıydı (23,41 GiB). Düzeltme: `docker run`a
`--memory=<MemoryMax ile aynı>` — apisix-kapi 512m · apisix-etcd 256m · hindsight-cp 512m (aynı ölçümde kullanım
89 / 13 / 43 MiB). Telemetri birimleri bu biçimi zaten taşıyordu. Eşitliği tüm docker birimlerinde (drop-in'le
birleşik hâl dahil) `tests/test_konteyner_bellek_tavani_v587.py` ölçer; apisix'in `50-vault-yan-dosya.conf` drop-in'i
ExecStart'ı yeniden yazdığı için bayrak orada da vardır.

**CPU eşi (TSK-247(b), 2026-09-28):** `CPUQuota=` de yalnız istemciyi sınırlar. Rol-1 A1 ölçümü: `hindsight-cp`
`CPUQuotaPerSecUSec` = 1s (istemci), `docker inspect` `NanoCpus` = 0 → konteyner CPU'su sınırsızdı. Düzeltme:
`hindsight-cp` `docker run`ına `--cpus=<CPUQuota/100>` (100% → 1 çekirdek). CPU kotası YALNIZ bu birimde var; kota
beyan eden her docker biriminde eşitliği v587 E bölümü ölçer. Aynı restart'la yürürlüğe girer.

**Yürürlük RESTART ister:** bayrak konteyner AÇILIRKEN uygulanır. `site.yml` dosyaları kopyalar ve `daemon-reload`
yapar, hiçbir birimi yeniden başlatmaz. Restart BAKIM PENCERESİNDE yapılır: APISIX yeniden başlarken kapının bütün
yüzeyi (LLM egress `9080`, FMP rotası, pano girişi `9443`) birkaç saniye kesilir. `dagit` `[F9]` içerik aynası
`site.yml` koşana dek bu üç birimi ayrık raporlar (engellemez).

**1. A0 rolü** — birimler ve apisix drop-in'i kopyalanır:

```bash
ansible-playbook -i deploy/ansible/inventory.ini deploy/ansible/site.yml --check --diff
ansible-playbook -i deploy/ansible/inventory.ini deploy/ansible/site.yml
```

Beklenen fark: `apisix.service`, `apisix-etcd.service`, `hindsight-cp.service` ve
`apisix.service.d/50-vault-yan-dosya.conf` içinde yalnız `--memory=…` satırı ve şerhi; `hindsight-cp.service`te ek
olarak `--cpus=…` satırı ve şerhi. Başka dosya değişiyorsa DUR.

**2. Yeniden başlat** — tek komut, sıra etcd önce:

```bash
ssh -i ~/.ssh/oci-a1.key ubuntu@130.61.126.87 'sudo systemctl restart apisix-etcd apisix hindsight-cp'
```

`apisix.service` `Requires=` + `After=apisix-etcd.service` taşır: systemd tek işlemde önce etcd'yi, sonra apisix'i
açar. etcd'nin restart'ı apisix'i zaten yeniden başlatır — iki ayrı komut kapıyı İKİ kez keserdi.

**3. Doğrulama** (her satırın beklenen çıktısı altında):

```bash
ssh -i ~/.ssh/oci-a1.key ubuntu@130.61.126.87 'systemctl is-active apisix-etcd apisix hindsight-cp'
# active ×3
ssh -i ~/.ssh/oci-a1.key ubuntu@130.61.126.87 'sudo docker inspect -f "{{.Name}} {{.HostConfig.Memory}}" apisix-etcd apisix-kapi hindsight-cp'
# beklenen: /apisix-etcd 268435456 · /apisix-kapi 536870912 · /hindsight-cp 536870912
ssh -i ~/.ssh/oci-a1.key ubuntu@130.61.126.87 'sudo docker stats --no-stream --format "{{.Name}} {{.MemUsage}}" apisix-etcd apisix-kapi hindsight-cp'
# tavan sütunu 256MiB / 512MiB / 512MiB — "23.41GiB" GÖRÜNMEMELİ
ssh -i ~/.ssh/oci-a1.key ubuntu@130.61.126.87 'sudo docker inspect -f "{{.Name}} {{.HostConfig.NanoCpus}}" hindsight-cp'
# beklenen: /hindsight-cp 1000000000   (0: CPU tavanı konteynere inmemiş)
ssh -i ~/.ssh/oci-a1.key ubuntu@130.61.126.87 'curl -s 127.0.0.1:2379/health; curl -s -o /dev/null -w " kapi=%{http_code}\n" 127.0.0.1:9080/healthz'
# {"health":"true"…} kapi=200   (502: kapı açık ama pano kapalı · 000: kapı açılmadı)
```

Son satırın kapı yarısı ÖLÇÜLMEDİ: `/healthz` isteği `pano-ingress` rotasının `/*` eşleşmesiyle panoya gider (depodaki
`routes.yaml` okuması). Farklı bir kod dönerse hüküm ilk iki satırdır. `inspect` `0` gösterirse düzeltme konteynere
inmemiştir: birim kopyalandı ama restart yapılmadı ya da KOŞAN komut eski — `systemctl cat apisix` birleşik hâli
(drop-in dahil) gösterir.

**Tavan aşılırsa** çekirdek konteyneri öldürür (`docker events`: `oom` → `die 137`) ve `Restart=on-failure` birimi
yeniden açar. Tavan ÖLÇEREK yükseltilir (Grafana emsali: memcg dosya önbelleğini de sayar); değer birimde, apisix
drop-in'inde, bu cetvelde ve v587'de birlikte değişir. CPU tavanı öldürmez, KISAR (throttle); `--cpus` değeri
birimin `CPUQuota=`su ve bu cetvelin `NanoCpus` satırıyla birlikte değişir. **Geri alma:** `--memory` (ve/veya
`--cpus`) satırı kaldırılır → `site.yml` → aynı restart.

## TSK-064 iki-kanal kapanışı — kiracı anahtarı ve hindsight-cp yalnız Vault kanalından (2026-09-29)

Hindsight kiracı anahtarının ve CP ortamının ESKİ kopyaları kapanır: `/opt/hindsight/.key` (0600 ubuntu — tek
okuyucusu Rol-1 hafıza araçlarıydı) ve `/opt/hindsight/.env-cp` (0600 root — hindsight-cp temel biriminin
`EnvironmentFile=`ı). Değerlerin tek kaynağı kasadır (Vault Agent render hedefleri, 0400 root). **Dosyaların
kaldırılması KODUN işi değildir — bu bölümün 4–5. adımları operatör komutudur.** Gerekçe ve kararlar:
`deploy/hindsight/hindsight-cp.service.d/51-env-cp-kaldir.conf` şerhi · `deploy/sir_envanteri.yaml`
`rotasyon_kopyalari.emekli_kopyalar` · `deploy/hindsight/sayfa_oku.sh` başlığı. Çivi: `tests/test_iki_kanal_kapanisi_v590.py`.

**Ne, A1'e nasıl gider:**

| Parça | Yol | Nasıl |
|---|---|---|
| Hafıza araçları (`hafiza_sor.sh`, `sayfa_oku.sh`) — anahtarı `sudo -n cat /etc/hindsight/creds/HINDSIGHT_API_TENANT_API_KEY` borusundan okur | `/opt/meridian/deploy/hindsight/` | `dagit` (rsync). `~/bin/*.sh` bu dosyalara SEMBOLİK BAĞDIR (2026-09-25, dağıtım #67) — restart gerekmez |
| Rotasyon tablosu + envanter (`.key`/`.env-cp` satırları emekli) | `/opt/meridian/deploy/oracle-a1/sir_rotasyon.sh` · `/opt/meridian/deploy/sir_envanteri.yaml` | `dagit` (rsync) |
| hindsight-cp drop-in `51-env-cp-kaldir.conf` (boş `EnvironmentFile=` + ZORUNLU `.env-cp.vault`) | `/etc/systemd/system/hindsight-cp.service.d/` | A0 rolü (`site.yml` → `dropinler.yml`); `dagit` drop-in KURMAZ |

Bedel: araçlar ubuntu'nun PAROLASIZ sudo'suna dayanır (bugün var; yeni yetki açılmadı). sudo parola isterse
araç BEKLEMEZ (`-n`): çıkış 1 ve stderr'de tek satır `HAFIZA ANAHTARI OKUNAMADI: … sudo: a password is required`.

**Sıra sözleşmedir:** 0 dağıtım → 1 A0 rolü → 2 restart → 3 doğrulama → 4 yedek → 5 kaldırma → 6 son doğrulama.
Doğrulama düşerse 4–5 YAPILMAZ.

**0. Kod A1'de** (`dagit` Rol-1'in normal reçetesiyle; ardından):

```bash
ssh -i ~/.ssh/oci-a1.key ubuntu@130.61.126.87 'readlink -f ~/bin/hafiza_sor.sh ~/bin/sayfa_oku.sh; grep -c "\"sudo\", \"-n\", \"cat\"" /opt/meridian/deploy/hindsight/hafiza_sor.sh /opt/meridian/deploy/hindsight/sayfa_oku.sh'
# /opt/meridian/deploy/hindsight/hafiza_sor.sh · /opt/meridian/deploy/hindsight/sayfa_oku.sh · her dosyada 1
```

**1. A0 rolü** — drop-in kopyalanır, `daemon-reload` yapılır, birim yeniden BAŞLATILMAZ:

```bash
ansible-playbook -i deploy/ansible/inventory.ini deploy/ansible/site.yml --check --diff
ansible-playbook -i deploy/ansible/inventory.ini deploy/ansible/site.yml
```

Beklenen fark: yeni dosya `hindsight-cp.service.d/51-env-cp-kaldir.conf` ve `50-vault-yan-dosya.conf`un YALNIZ
şerh satırları (2026-09-29 güncelleme notu). Başka dosya değişiyorsa DUR.

**2. Restart** (bakım penceresi; CP yalnız ssh tüneliyle erişilen yönetim arayüzüdür, motoru etkilemez):

```bash
ssh -i ~/.ssh/oci-a1.key ubuntu@130.61.126.87 'sudo systemctl restart hindsight-cp; systemctl is-active hindsight-cp'
# active   (failed + "Failed to load environment files" → .env-cp.vault YOK: kasa/Agent'a bak, GERİ ALMA'ya geç)
```

**3. Doğrulama — kaldırmadan ÖNCE** (her satırın beklenen çıktısı altında):

```bash
ssh -i ~/.ssh/oci-a1.key ubuntu@130.61.126.87 'systemctl show -p EnvironmentFiles hindsight-cp'
# EnvironmentFiles=/opt/hindsight/.env-cp.vault (ignore_errors=no)   — TEK satır; .env-cp GÖRÜNMEMELİ
# (özellik adı systemd D-Bus adıdır, A1'de ÖLÇÜLMEDİ: boş dönerse `systemctl cat hindsight-cp | grep EnvironmentFile`
#  → temel satır, 50'nin `-` satırı, 51'in boş satırı ve 51'in tiresiz .env-cp.vault satırı sırayla görünmeli)
ssh -i ~/.ssh/oci-a1.key ubuntu@130.61.126.87 'sudo sh -c '\''printf "{\"key\":\"%s\"}" "$(cat /etc/meridian/hindsight_cp_access_key)"'\'' | curl -s -o /dev/null -w "%{http_code}\n" -H "Content-Type: application/json" --data-binary @- http://127.0.0.1:9999/api/auth/login'
# 200   (kasadaki CP anahtarı; değer borudan akar, argv'ye/terminale GİRMEZ — printf kabuk yerleşiğidir)
ssh -i ~/.ssh/oci-a1.key ubuntu@130.61.126.87 'printf "{\"key\":\"yanlis\"}" | curl -s -o /dev/null -w "%{http_code}\n" -H "Content-Type: application/json" --data-binary @- http://127.0.0.1:9999/api/auth/login'
# 401   (kilit yürürlükte — iki ayak birlikte: yanlış anahtar da 200 dönseydi ilk satır hiçbir şey ölçmezdi; 503 = konteynerde anahtar YOK)
ssh -i ~/.ssh/oci-a1.key ubuntu@130.61.126.87 'HAFIZA_OKUMA_ETIKET=ikikanal-dogrulama ~/bin/sayfa_oku.sh | head -2'
# "# zihin modelleri: N" + ilk sayfa satırı (çıkış 0; etiket okumayı EDG-2026-103 sayımından ayırır)
ssh -i ~/.ssh/oci-a1.key ubuntu@130.61.126.87 'HAFIZA_OKUMA_ETIKET=ikikanal-dogrulama ~/bin/hafiza_sor.sh "iki kanal kapanışı doğrulama" 1 | head -1'
# "# recall · bank=meridian-arsiv · … · sonuç N"   (RECALL HATASI / HAFIZA ANAHTARI OKUNAMADI → DUR)
```

**4. Yedek** — `sir_rotasyon.sh` yedek sözleşmesi üslubu: dizin 0700 root, dosyalar 0600 root, ad saniyeli UTC;
kıyas yalnız EŞİT/AYRI basar (değer ve hash BASILMAZ). Basılan `yedek dizini` satırını kaydet — geri almanın girdisidir:

```bash
ssh -i ~/.ssh/oci-a1.key ubuntu@130.61.126.87 'Y=/root/sir-yedek-$(date -u +%Y%m%dT%H%M%SZ)-ikikanal; sudo install -d -m 0700 -o root -g root "$Y" && sudo install -d -m 0700 -o root -g root "$Y/opt/hindsight" && for f in /opt/hindsight/.key /opt/hindsight/.env-cp; do sudo install -m 0600 -o root -g root "$f" "$Y$f" && { sudo cmp -s "$f" "$Y$f" && echo "yedek EŞİT: $f" || echo "yedek AYRI: $f — DUR"; }; done; echo "yedek dizini: $Y"'
# yedek EŞİT: /opt/hindsight/.key · yedek EŞİT: /opt/hindsight/.env-cp · yedek dizini: /root/sir-yedek-<UTC>-ikikanal
```

**5. Kaldırma** (OPERATÖR — yalnız 3. ve 4. adım temizse). Kaldırma `rm` DEĞİL, TAŞIMADIR: asıl dosyalar 4. adımın
yedek dizininde `orijinal/` alt dizinine gider (sahip/izinleriyle; kalıcı silme YOK). `Y`, 4. adımın bastığı
`yedek dizini` satırıdır; dizin yoksa (`sudo test -d` düşer) hiçbir şey taşınmaz:

```bash
ssh -i ~/.ssh/oci-a1.key ubuntu@130.61.126.87 'Y=/root/sir-yedek-<UTC>-ikikanal; sudo test -d "$Y" && sudo install -d -m 0700 -o root -g root "$Y/orijinal" && sudo mv /opt/hindsight/.key /opt/hindsight/.env-cp "$Y/orijinal/" && { ls -A /opt/hindsight | grep -E "^\.key$|^\.env-cp$" || echo "iki dosya da YOK"; }'
# iki dosya da YOK   (.env-cp.vault ve .env YERİNDE kalır; asıl dosyalar $Y/orijinal/ altında, 4. adımın kopyaları $Y/opt/hindsight/ altında)
```

**UYGULANDI 2026-09-29 11:32Z** (Rol-1, operatör "sen çalıştır"): `rm` yerine yedek dizinine TAŞIMA — asıl dosyalar
`/root/sir-yedek-20260929T113217Z-ikikanal/orijinal/` altında (root-only); kalıcı silme yok. 6. adım temiz:
hindsight-cp yalnız `.env-cp.vault` ile açıldı (CP girişi 200/401), iki araç çalışıyor, `--envanter` iki emekli kopya
için "→ YOK (kaldırılmış)". Aynı an ve dizin `deploy/sir_envanteri.yaml` `rotasyon_kopyalari.emekli_kopyalar`
kayıtlarında (`kaldirildi` · `yedek_dizini`) yaşar — ikisi ayrışırsa v590 D3 öter.

**6. Son doğrulama — kaldırmadan SONRA** (CP'nin eski dosya olmadan AÇILDIĞI burada kanıtlanır):

```bash
ssh -i ~/.ssh/oci-a1.key ubuntu@130.61.126.87 'sudo systemctl restart hindsight-cp; systemctl is-active hindsight-cp'
# active — ardından 3. adımın iki login satırını (200 · 401) ve iki araç satırını AYNEN yeniden koş
ssh -i ~/.ssh/oci-a1.key ubuntu@130.61.126.87 'cd /opt/meridian && sudo ./deploy/oracle-a1/sir_rotasyon.sh --envanter | grep -E "emekli kopya|EMEKLİ KOPYA|/opt/hindsight/\.env-cp \["'
# emekli kopya: /opt/hindsight/.key → YOK (kaldırılmış) · emekli kopya: /opt/hindsight/.env-cp → YOK (kaldırılmış)
# ("EMEKLİ KOPYA HÂLÂ VAR" ya da "BEYAN DIŞI KOPYA: /opt/hindsight/.env-cp [...]" satırı GÖRÜNMEMELİ)
```

**GERİ ALMA** (hangi adımda düştüyse o adımdan geriye):

- *2–3. adım düştü (dosyalar yerinde):* drop-in'i kaldır → `sudo rm /etc/systemd/system/hindsight-cp.service.d/51-env-cp-kaldir.conf && sudo systemctl daemon-reload && sudo systemctl restart hindsight-cp`. Temel birimin `.env-cp` satırı ve 50'nin opsiyonel yan dosya satırı geri gelir. Bir sonraki `site.yml` drop-in'i YENİDEN kurar: depodaki kapanış commit'i de geri alınmalıdır (Rol-1).
- *Araçlar düştü (sudo borusu):* dosyalar yerindeyse geçici çare `HAFIZA_ANAHTAR_DOSYASI=/opt/hindsight/.key ~/bin/hafiza_sor.sh …` (ezme arayüzü korunur); kalıcı çare depo geri alımı + `dagit`.
- *5. adımdan sonra:* dosyaları ESKİ sahip/izinleriyle geri koy, SONRA drop-in'i yukarıdaki gibi kaldır. Asıl dosyalar
  `$Y/orijinal/` altında sahip/izinleriyle durur → `sudo mv "$Y/orijinal/.key" "$Y/orijinal/.env-cp" /opt/hindsight/`;
  `orijinal/` yoksa 4. adımın kopyalarından:
  `sudo install -m 0600 -o ubuntu -g ubuntu $Y/opt/hindsight/.key /opt/hindsight/.key` ·
  `sudo install -m 0600 -o root -g root $Y/opt/hindsight/.env-cp /opt/hindsight/.env-cp`.
  Yedek alındığı andan beri bir rotasyon (`--tenant`/`--cp`) koştuysa geri konan dosyalar BAYATTIR: geri alınmış
  kodla `sudo ./deploy/oracle-a1/sir_rotasyon.sh --tenant --esitle` ve `--cp --esitle` eski kanalı kasadaki değere eşitler.

**Bilinen kalan (açık kalem, bu bölümün kapsamı dışı):** `research/olcumler/edg067_hindsight_faz1/kiyas_kos.py`
kullanım örneği `--key-file /opt/hindsight/.key` der. Kaldırmadan sonra aynı araç `--key-file <(sudo -n cat
/etc/hindsight/creds/HINDSIGHT_API_TENANT_API_KEY)` ile koşar (değer argv'ye girmez; `/dev/fd` yolu geçer).
