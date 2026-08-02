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
`reflect.py:1049` → `workers = max(2, min(4, cpu_count-2))` → 4 çekirdekte **2 işçi**, geriye
sunucu+ajan için 2 çekirdek kalır. `MERIDIAN_SEARCH_MAX_MIN=60` duruyor: Ampere çekirdeği Apple
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
| 5 | `MERIDIAN_DASH_TOKEN` üretimi (`openssl rand -hex 24`) + restart | placeholder token'la canlıya çıkmayı önler |
| 6 | doğrulama tablosu + **çift-emir uyarısı** | |

**keepalive neden özel ele alınıyor:** `ops/keepalive.sh` pidfile silinince kendini kapatır ama
**60 sn'ye kadar** yaşar (uyku turu) — o süre içinde worker'ı **diriltir**. Betik önce PID'i
(komut kimliğiyle doğrulayarak) öldürür, sonra pidfile'ı siler. `caffeinate`'e dokunulmaz.

> **DÜZELTİLEN HATA (bu tur):** eski B.3 adımındaki `sed` deseni `DEĞİŞTİR-uzun-rastgele-token`
> idi, oysa `meridian.service`'teki placeholder `CHANGEME-long-random-ascii-token`. Desen
> eşleşmediği için `sed` **sessizce 0 dönüyor**, servis bilinen bir placeholder token'la canlıya
> çıkıyordu. `cutover.sh` artık doğru deseni kullanır **ve değişimin gerçekten olduğunu doğrular**.

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
yeniden dener (`barsarchive.py:343/413`). Yani `is-active` **bar yazdığını kanıtlamaz** — ölçüsü
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
  # (c) TOKEN KAPISI — .dash.env yerinde mi? (yoksa pano token'sız açılır)
  sudo test -s /opt/meridian/.dash.env && echo "  ✓ .dash.env var" || echo "  !! .dash.env YOK — Bölüm B adım 3"
  # (c2) AJAN DİZİNİ KAPISI — `~/.hermes` ReadWritePaths'te `-` önekiyle YAZILIDIR (installer
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
  for i in 1 2; do uv run python -c "from meridian import store; \
    print(store.read_json(\"scheduler_status.json\",{}).get(\"updated\"))"; sleep 90; done'

# (d) BAR AKIŞI — arşivcinin ölçüsü `is-active` DEĞİL, satır sayısıdır (Redis düşse de aktif görünür)
ssh -i $K $A1 'cd /opt/meridian && export PATH=$HOME/.local/bin:$PATH
  uv run python -m meridian.barsarchive --ozet --gun 2'
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
`hermes_composite.py:330` ön-eleme alt süreçlerini `/tmp/prescreen-<id>` altında koşturur.
`PrivateTmp=true` bunu **kırmaz** (özel ad alanı yazılabilir) ama SSH kabuğundan o dizin **görünmez**.
Bakmak için:
```bash
ssh -i $K $A1 'sudo ls -d /tmp/systemd-private-*-meridian.service-*/tmp/prescreen-* 2>/dev/null | tail'
```

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
curl -s localhost:8080/healthz       # 200=taze · 503=BAYAT ama süreç canlı (/healthz api.py:478'de VAR)
curl -s localhost:8080/api/today     # 200 + JSON
journalctl -u meridian -f            # canlı log
uv run python -m pytest -q           # tüm testler yeşil (aarch64'te de geçmeli)
```
Reboot testi: `sudo reboot` → tekrar SSH → `systemctl is-active meridian` **active** olmalı
(launchd'nin Mac'te yapamadığı şey).

### 2. TAŞIMA SONRASI — bir seans + bir hafta içinde ölçülecekler
Bunlar "servis ayakta mı" değil, **taşımanın işe yarayıp yaramadığı** ölçüleridir. `is-active`
yeşilken bunların hepsi ölü olabilir; o yüzden ayrı liste.

| # | ne beklenir | nasıl ölçülür | taşıma anındaki taban |
|---|---|---|---|
| a | `validation_ledger`'a **`pencere_id:"R1"`** damgalı satır AKMAYA başlar | `grep -c '"pencere_id": *"R1"' state/validation_ledger.jsonl` | **0** (204 satırın hepsi `pencere_id=null`; R1 bugün, 2026-07-30 açıldı) |
| b | **PBO tabanı birikmeye** başlar (PBO YALNIZ `pencere_id==R1` satırlarını sayar) | `uv run python -c "from meridian import validation,store,dataset; d=store.read_jsonl('validation_ledger.jsonl',limit=validation.LEDGER_CAP); print(validation.pbo_cscv([r for r in d if r.get('pencere_id')==dataset.ROTATION_ID]))"` → `durum` `olculemedi`→`olculdu` | `olculemedi` (aday yok) |
| c | `hotstate_down` **çırpınması A1'de yeniden ölçülür** — Redis artık *aynı makinede* (yerelde bu tek olay olay defterinin %91'ini yiyordu) | `grep -c hotstate_down state/events.jsonl` (7 gün sonra tekrar) | yerel taban: **15.860/hafta** |
| d | `events.jsonl`'da **scheduler'ın nous kadansı** görünür | `grep -E 'nous_eval\|haftalik' state/events.jsonl \| tail` | henüz yok — kadans **restart'la** iner |
| e | bar arşivi gerçekten yazıyor (yalnız `is-active` YETMEZ) | `uv run python -m meridian.barsarchive --ozet --gun 5` | `satir` artıyor olmalı |
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
