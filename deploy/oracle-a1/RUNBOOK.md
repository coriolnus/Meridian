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

# 3) (A1) TOKEN — desen meridian.service'ten BİREBİR
ssh -i $K ubuntu@130.61.126.87 '
  sudo sed -i "s/CHANGEME-long-random-ascii-token/$(openssl rand -hex 24)/" /etc/systemd/system/meridian.service
  sudo systemctl daemon-reload && sudo systemctl restart meridian'
```
</details>

## Bölüm B2 — A1'deki birimler (üçü de `deploy.sh` tarafından kurulur+enable edilir)

| birim | ne yapar | not |
|---|---|---|
| `meridian.service` | worker + pano (uvicorn, 127.0.0.1:8080) | `Restart=always`; token burada |
| `meridian-barsarchive.service` | `mrd:bars:*` → `state/bars_intraday/` | **AYRI birim**: worker restart'ı bar akışını kesmesin (yereldeki serve.sh/`stop_worker` ayrıklığının karşılığı) |
| `meridian-backup.timer` → `.service` | günlük `state/` tar.gz, 7 gün saklama | 23:30 UTC (kapanış sonrası), `Persistent=true` |
| `redis-server` (apt) | sıcak durum + bar ring'i | **ŞART**, opsiyonel değil — `hotstate.py`/`barsarchive.py` buna bağlı. Ubuntu default'u yalnız `127.0.0.1` dinler, **değiştirme** |

**Redis yoksa arşivci ÖLMEZ, sessizce boşa döner:** `poll()` `None` döner, `run()` `idle_s` uyuyup
yeniden dener (`barsarchive.py:343/413`). Yani `is-active` **bar yazdığını kanıtlamaz** — ölçüsü
`--ozet` (aşağıda).

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
