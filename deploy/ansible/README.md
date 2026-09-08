# `deploy/ansible/` — Meridian A1 Ansible rolü (`meridian_a1`)

TSK-176 Faz A0. Spec: `docs/TASARIM-ALTYAPI-KOD-2026-09-08.md` §2/§3/§4/§5/§8. Uygulama planı:
`docs/superpowers/plans/2026-09-08-ansible-a0.md`. A1'in VM-içi durumunu (paketler, systemd
birimleri/timer'ları/drop-in'leri, polkit, sır DOSYALARININ varlık/izin denetimi, hermes
config'i, kum havuzları) repodaki `deploy/oracle-a1/`, `deploy/hindsight/`, `deploy/apisix/`,
`deploy/hermes/` kaynaklarından TEK KAYNAKLA yakınsatır. `dagit.sh`'a A0'da DOKUNMAZ.

**Kim koşar:** `ansible-playbook` A1'e karşı yalnız **Rol-1** tarafından koşulur
(CLAUDE.md §2/§9 — yan oturum/ajan dağıtım/canlı komut koşmaz). Ajanlar bu dizinde yalnız
`--syntax-check` ve `ansible-lint` koşabilir (A1'e ssh YOK).

## Ops sözleşmesi — komut satırı (repo kökünden)

```sh
# Kuru koşum (hiçbir şeyi değiştirmez; "temiz" hükmü yalnız check-mode destekleyen modüller
# içindir — command/shell ATLANIR, bkz. site.yml pre_tasks beyanı ve TASARIM §2.1).
ansible-playbook -i deploy/ansible/inventory.ini deploy/ansible/site.yml --check --diff

# Gerçek koşum (aynı komut --check'siz).
ansible-playbook -i deploy/ansible/inventory.ini deploy/ansible/site.yml

# Sözdizimi çivisi (ajan da koşabilir; A1'e bağlanmaz).
ansible-playbook --syntax-check -i deploy/ansible/inventory.ini deploy/ansible/site.yml

# Lint (production profili; ajan da koşabilir; A1'e bağlanmaz). Profil/istisna kaynağı: repo
# kökündeki `.ansible-lint` (CWD'den yukarı arandığı için config BURADA durur — deploy/ansible/
# içinde DEĞİL; bkz. o dosyadaki gerekçe).
ansible-lint deploy/ansible

# Yapılandırmanın GERÇEKTEN yüklendiğini gör (boş çıktı ya da `CONFIG_FILE() = None` = ayarların
# hiçbiri yürürlükte değil demektir).
ansible-config dump --only-changed
```

**Komutlar depo KÖKÜNDEN çağrılır ve bu bir zorunluluktur:** ansible yapılandırmayı
`ANSIBLE_CONFIG` → `./ansible.cfg` (CWD) → `~/.ansible.cfg` → `/etc/ansible/ansible.cfg`
sırasıyla arar; **playbook'un yanındaki dosyaya BAKMAZ**. Bu yüzden `ansible.cfg` depo
**kökündedir** (`.ansible-lint` ile aynı gerekçe). Ölçüldü (2026-09-08): dosya `deploy/ansible/`
altındayken `ansible-config dump --only-changed` → `CONFIG_FILE() = None`, yani
`host_key_checking`/`interpreter_python`/`pipelining` ayarlarının hiçbiri yürürlükte değildi.
Başka bir dizinden koşacaksanız `ANSIBLE_CONFIG=<depo>/ansible.cfg` verin.

## Bağımlılık

`ansible-core` + `ansible-lint` dev-grubunda (`pyproject.toml` `[dependency-groups].dev`,
`uv add --group dev --no-sync "ansible-core>=2.17,<2.19" "ansible-lint>=24"`). Rol-1 dev-grubunu
`uv sync` ile projeye kurar; çiviler ikiliyi **önce `.venv/bin`de** (yani pyproject/uv.lock'un
PİNLEDİĞİ sürüm), sonra PATH'te arar — salt PATH araması her zaman ayrı kurulmuş bir `uv tool`
kopyasını ölçerdi ve iki kaynak sessizce ayrışırdı. Worktree'lerde `.venv` yoktur: orada ikili
`~/.local/bin`ten gelir ve **A1'e KOŞULMAZ**, yalnız `--syntax-check`/`ansible-lint` için kullanılır.

## Kapılar (CLAUDE.md §2/§9 ile aynı)

- `ansible-playbook` A1'e karşı **yalnız Rol-1**; ajan/yan oturum ne koşar ne "hazır" der.
- Uzun ömürlü birimler (`meridian.service`, `meridian-barsarchive.service`,
  `hindsight-api.service`, `hindsight-cp.service`, `apisix.service`, `apisix-etcd.service`,
  `meridian-litestream.service`) için `state: restarted`/`state: started` YASAK — yalnız
  `enabled: true` + `daemon_reload` (handler). Restart kararı bakım penceresi/dagit'e aittir.
  `tests/test_ansible_a0_v451.py` bunu YAML'ı PARSE EDEREK ve `loop`/`with_*` ifadelerini
  `defaults/main.yml`ten ÇÖZEREK ölçer — metin araması `name: "{{ item }}"` biçimindeki şablonlu
  adları görmüyordu (yasak, rolün kendi deyimiyle sessizce delinebiliyordu; TUR 2 K6/K11).
- Sır DEĞERİ bu rolde YOK: sır dosyaları yalnız `stat`+`assert` ile denetlenir (`no_log: true`);
  üretim koşumlarında `-v` üstü YASAK (sır süzgeci ilkesi — yalnız beyaz-liste adlar basılır).
- Rol kaynağı = repodaki dosyanın kendisi (`ansible.builtin.copy`, `.j2` YOK — tek kaynak, aynı
  bayt). Birim listesi ELLE yazılmaz: `roles/meridian_a1/defaults/main.yml` içindeki
  `birim_kaynaklari` glob'ları `deploy/`'dan türetilir; `tests/test_ansible_a0_v451.py` bu
  glob'ların `deploy/` altındaki HER `*.service`/`*.timer` dosyasını kapsadığını (bilinen ölü
  dosyalar hariç) ölçer. Çiviler kaynağın YANINDA **hedefi** de ölçer (`dest` ifadeleri gerçek
  glob kümesi üzerinde render edilip beklenen `/etc/systemd/system/…` yollarıyla kıyaslanır) ve
  `with_fileglob` dışındaki her `src:`in diskte var olduğunu doğrular — plan hedefi "kopyalanan
  dosya kümesi == deploy/ altındaki birim kümesi" idi, bugüne dek yalnız kaynak yarısı çiviliydi.

## Bilinen ölü/silinmeli dosyalar (bu rolün kaynağı DEĞİL)

- `deploy/litestream.service`, `deploy/litestream.yml` (üst dizin) — eski tasarım
  (`User=meridian`), canlı A1 `deploy/oracle-a1/meridian-litestream.service` +
  `deploy/oracle-a1/litestream.yml` kullanıyor (A0 envanteri, Tek-Kaynak Riski #3).
- `deploy/meridian.service` (üst dizin) — eski GCP/docker-compose birimi (`Type=oneshot`,
  `docker compose up`); canlı A1 `deploy/oracle-a1/meridian.service` (native uv/uvicorn)
  kullanıyor. Task 1 sırasında ayrıca tespit edildi (planın envanterinde adı geçmiyordu);
  aynı gerekçeyle role kaynağı DEĞİL ve silinmesi önerilir.
- İkisi de `tests/test_ansible_a0_v451.py`'de adıyla dışlanır (glob-kapsama çivisi bunlarsız
  hesaplanır); silme kararı Rol-1'e aittir, bu tur silmedi (git yok, dosya-taşıma da yapılmadı).

## Task 2 (görev dosyaları) — koşumdan ÖNCE bilinmesi gerekenler

Rol dokuz görev dosyasını sırayla koşar (`roles/meridian_a1/tasks/main.yml`):
`paketler → dizinler → venv → birimler → sir_denetimi → dropinler → polkit → hermes → saglik`.
Sıra sözleşmedir ve `tests/test_ansible_a0_v451.py` ile çivilidir:

- **venv birimlerden ÖNCE** — birimlerin `ExecStart`'ı `.venv/bin/python`a bakar; venv'siz enable
  edilen birim ilk atışta 203/EXEC ile düşerdi.
- **sır denetimi drop-in'lerden ÖNCE** — kopyalanacak drop-in'lerin beşi `LoadCredential=` taşır
  ve dosyaların kendi başlıkları şunu yazar: *"LoadCredential= kaynak dosyası YOKSA systemd birimi
  BAŞLATMAZ."* Yani sırsız bir hosta bu drop-in'leri kurmak, `meridian.service`i (ve
  `hindsight-api`yi) başlatılamaz hâle getirmektir. Denetim orada DURDURUR: birim dosyaları
  kurulmuştur, credential kanalı ise kaynağı doğrulanmadan AÇILMAZ.
- **sağlık EN SONDA** — "kurulu != çalışır" hükmü (koşullu kapı, aşağıya bakın).

### KAPI-0 — `uv_surum` + installer sha256 ölçülmeden playbook koşmaz

`defaults/main.yml`'deki `uv_surum` ve `uv_installer_sha256` **`OLCULECEK`** nöbetçi değeriyle
doğar; `venv.yml`'in ilk görevi ikisinde de DURUR. Ölçüp yazmak **Rol-1'in işidir**:

```sh
ssh -i ~/.ssh/oci-a1.key ubuntu@130.61.126.87 'uv --version'
# çıktıdaki sürümü defaults/main.yml → uv_surum satırına yaz, sonra o sürümün installer'ını ölç:
curl -fsSL https://astral.sh/uv/<sürüm>/install.sh | shasum -a 256
# özeti defaults/main.yml → uv_installer_sha256 satırına yaz
```

Sürüm pini bilinçli: sürümsüz installer URL'si her koşumda başka bir uv kurabilirdi (A0
envanteri Bulgu 5 — tedarik-zinciri kapısı yok). sha256 + `force: true` + kök-dışı yazılamayan
`dest` üçlüsü de bilinçli ve ÖLÇÜLMÜŞ bir davranışa dayanır: `get_url` checksum'suz ve
`force: false` iken dest varsa koşullu GET atar ve **304 dönerse diskteki dosyayı korur**
(ansible-core 2.18.19 `modules/get_url.py`) — installer `/tmp`e tahmin edilebilir adla inseydi,
önceden konmuş bir dosya `ubuntu` olarak çalıştırılabilirdi.

### Kadans kapısı (brifing/bekçi/karne) — deploy.sh'tan DAVRANIŞ FARKI

Kapı `systemctl is-enabled <birim>.timer` ile ölçülür (`service_facts` timer'ları vermeyebilir)
ve **timer `enabled` DEĞİLSE birim dosyası kopyalanmaz, timer enable edilmez**; her atlanan birim
için "DOKUNULMADI: neden" satırı basılır. Devretmek için:

```sh
ansible-playbook -i deploy/ansible/inventory.ini deploy/ansible/site.yml -e brifing_devri=true
```

**Desteklenen TEK biçim budur.** Kapıyı kapalı tutmak için bayrak **verilmez** — `-e
brifing_devri=false` YAZMAYIN. Gerekçe ölçüldü (2026-09-08): `-e` ile gelen değer ansible'da
DİZGEdir ve boş olmayan her dizge truthy'dir; süzgeçsiz bir `when` ifadesinde `false` dizgesi
kapıyı **AÇARDI**, yani operatör kapıyı kapalı tutmak için yazdığı komutla tam tersini yapardı.
Rol artık her kullanımda `| bool` taşır (v451 çivisi bunu ve kapının YÖNÜNÜ senaryo tablosuyla
ölçer), ama bayrağı hiç vermemek yine de en açık yoldur.

Bu, planın Global Constraints satırının birebir uygulanmasıdır ve `deploy.sh` 6c-e'den **farklıdır**:
deploy.sh kadans KAPALIYKEN dosyayı kopyalıyor (zararsız — koşan bir şey yok), yalnız kadans
AÇIKken ve yürürlükteki `ExecStart` repodakinden farklıyken dokunmuyordu. A0'ın kapısı daha
dardır: kadans kapalıyken dosya da kurulmaz. **Sonucu:** taze bir A1'de brifing/bekçi/karne birim
dosyaları `-e brifing_devri=true` verilmeden kurulmaz. Karar Rol-1'indir (A0 kuru koşumunda
"DOKUNULMADI" satırları bunu ADIYLA gösterir).

### Bu rolün YAPMADIKLARI (bilinçli sınırlar)

- **Hiçbir uzun ömürlü servisi başlatmaz/restart etmez.** Yalnız `enabled: true` + `daemon-reload`
  handler'ı. `state` verilmez — F10 (enabled+inactive) anomalisi bilerek DURDURULUR (TASARIM §4.4).
- **hermes ikilisini KURMAZ** (`deploy.sh` 5'in sürüm/sha kapısız boru-hattı A0'a geçmedi):
  ölçer, yoksa reçete basar. Bot profilleri (`hermes profile install`) de ROL DIŞIDIR.
- **Hiçbir sır ÜRETMEZ/OKUMAZ.** `deploy.sh` 7'nin `.dash.env` token üretimi A0'a geçmedi;
  sır dosyaları yalnız `stat` (checksum KAPALI — içerik okunmaz) + `assert` ile denetlenir ve
  eksikse playbook DURUR, hangi betiğin koşulacağını söyler.
- **Postgres kurulumu YOK** (A2 fazı), **docker konteyner tanımı YOK** (birim dosyalarının işi).
- `deploy.sh` 15'in koşulsuz `restart meridian meridian-barsarchive` adımı ve `--replay` tohumu
  A0'a GEÇMEDİ (bakım penceresi + state kararı).
- **Enable ettiği birimlerin YAPILANDIRMA dosyalarını taşımaz** ve bu bir kapsam boşluğudur —
  beyanlı, sessiz değil. `dagit.sh::F9_LISTE` (canlıya giden repo dosyalarının tek kaynağı) ile
  rol kapsamı arasındaki fark `defaults/main.yml::f9_rol_disi` listesinde ADIYLA durur ve
  `tests/test_ansible_a0_v451.py::test_f9_beyani_rol_kapsami_ve_beyanli_istisnalarla_ortusur`
  ikisinin TAM EŞİT olduğunu ölçer (yeni bir F9 dosyası ya role girer ya listeye — sessiz üçüncü
  yol yok). Bugünkü liste ve **etkisi**:
  - `deploy/apisix/config.yaml` → `/opt/apisix/config.yaml`: `apisix.service` bu dosyayı
    bind-mount eder. Rol `apisix.service`i **enable eder ama config'i kurmaz** — taze bir A1'de
    birim ilk atışta düşer. (Config ayrıca `/opt/apisix/.env-apisix` sırrına dayanır: F9-DIŞI.)
  - `deploy/oracle-a1/litestream.yml` → `/etc/litestream.yml`: `meridian-litestream.service`
    `-config /etc/litestream.yml` ile koşar; kurulumu bugün `litestream_kur.sh`ın işidir.
  - `deploy/oracle-a1/geridolum.py` → `/opt/veri/geridolum.py` (+ `research/olcumler/
    edg066_tick_arsiv/{pilot.py,kapsam.txt}` → `/opt/veri/`): `meridian-geridolum.timer` enable
    edilir, işçi betikleri taşınmaz.
  - `deploy/hermes/profiles/{sef,bekci,karne}/*` (9 dosya): profil kurulumu `hermes profile
    install` iledir ve yeni ajan kimliği **operatör kararıdır** — rol yalnız varlıklarını raporlar.

  **AÇIK KALEM (A1 fazı, Rol-1):** ilk üç kalem sırsız ve git-izlidir, yani role `copy` ile
  eklenebilir; bu tur eklemedi çünkü karar canlı A1'de neyin zaten kurulu olduğunu ölçmeyi
  gerektirir (ajan A1'e ssh yapmaz) ve rolün kapsamını "birim + drop-in + polkit"ten
  "yapılandırma"ya genişletmek plan kapsamı dışıdır.
- **ÖN-KOŞUL: `/opt/meridian` repo ağacını TAŞIMAZ, VAR OLMASINI VARSAYAR.** Bu depoyu hedefe
  koymak bugüne dek `dagit.sh`ın rsync'idir; rol onun YERİNE geçmez. Dört görev doğrudan
  `repo_kok`a bağlıdır: `venv.yml` (`uv sync --frozen` `chdir={{ repo_kok }}` ve import
  doğrulaması `{{ repo_kok }}/.venv/bin/python`), `birimler.yml` (`{{ repo_kok }}/deploy/
  oracle-a1/tick_watchdog.sh` `state: file` — dosya yoksa görev DÜŞER) ve `dizinler.yml`
  (`{{ repo_kok }}/var/bots/*`). Taze/soğuk bir A1'de — rolün ilan ettiği birincil senaryo —
  bu playbook TEK BAŞINA YETMEZ: önce A2/DR reçetesiyle repo ağacı hedefe konmalı, sonra bu rol
  koşulmalı; aksi halde yukarıdaki dört görev ilk atışta düşer. Aynı beyanlı-boşluk sözleşmesi
  geçerlidir (`defaults/main.yml::f9_rol_disi` gerekçesiyle aynı ilke): boşluk yasak değildir,
  SESSİZ olması yasaktır.

### Sağlık hükmü — KOŞULLU kapı

`saglik.yml` sonda: önce `systemctl is-active meridian.service` **okunur**, sonra hüküm verilir —
`meridian.service` **active** assert'i + `healthz` 200 (5 deneme × 3 sn). Timer'lar için yalnız
RAPOR (kapalı kadans arıza değildir). Kapı fail-closed'dır: nabız 900 sn'den eskiyse healthz 503
döner ("bayat ama süreç canlı") ve playbook DÜŞER.

**Kapı iki durumda ATLANIR ve atlandığını ADIYLA basar** (sessiz atlama = körlük):

1. `-e beklenen_aktif=false` — soğuk kurulum / bakım penceresi. Gerekçe: rol hiçbir uzun ömürlü
   servisi **başlatmaz** (`state` verilmez, F10 kararı), dolayısıyla taze bir A1'de yakınsama
   tamamen başarılıyken bile koşulsuz bir `active` şartı playbook'u kırmızı yapardı ve rolün bunu
   düzeltmesi kısıtı gereği imkânsızdı. Görmezden gelinen kapı, kapı değildir. Semantik:
   *"servis çalışması bekleniyorsa sağlıklı da olmalı."*
2. `--check --diff` (kuru koşum) — `command`/`shell` check-mode'da ATLANIR ve register'da
   `stdout` hiç doğmaz; ona dayanan bir assert boş dizgeyle karşılaşıp **hiç ölçülmemiş bir şey
   hakkında** arıza beyan ederdi (eski hâlde kuru koşum HER ZAMAN kırmızı bitiyordu).

**`uv sync` uyarısı:** venv değiştiğinde (`changed`) rol "VENV DEĞİŞTİ — koşan meridian/
barsarchive süreçleri eski kodla; restart bakım penceresine ait" satırını basar. Rol restart
ETMEZ: `deploy.sh` 15'in koşulsuz restart'ı A0'a bilerek geçmedi, o hâlde riskin okunur bir
çıktısı olmak zorundadır (Yasa 6).

---

# `dagit.yml` — dağıtım playbook'u (TSK-176 Faz A1)

`site.yml` A1'in **VM-içi durumunu** yakınsatır (paketler, birimler, drop-in'ler). `dagit.yml`
bundan ayrı bir iştir: **kodu canlıya taşır** — yani `dagit.sh`ın kapılarını, davranış birebir,
Ansible'a taşır. Plan: `docs/superpowers/plans/2026-09-08-ansible-a1-dagit.md`.

**Geçiş süresince İKİ YOL yan yana durur (K1):** `dagit.sh` hâlâ koşabilir ve aynı dört gövdeyi
(`ops/state_fark_hukmu.py`, `ops/artefakt_tazelik.py`, `deploy/oracle-a1/dogrulama_anahtar.py`,
`deploy/oracle-a1/kod_tazelik.sh`) çağırır. **İlk gerçek dağıtım operatör gözetimindedir.**

## Koleksiyon bağımlılığı (koşumdan ÖNCE, bir kez)

`dagit.yml` `[1]`/`[2]` adımlarında `ansible.posix.synchronize` kullanır; bu modül `ansible-core`
ile **gelmez** ve kurulu değilken `--syntax-check` bile düşer.

```sh
ansible-galaxy collection install -r deploy/ansible/requirements.yml
```

Koleksiyon **kullanıcı düzeyine** kurulur (`~/.ansible/collections`) — depoya yazmaz, dolayısıyla
dagit'in temiz-ağaç/mtime kapılarını tetiklemez. Sürüm `requirements.yml`de **tam** pinlidir;
`tests/test_ansible_dagit_v452.py` B11a pinin tam sürüm olduğunu, B11b de kurulu sürümün pinle
aynı olduğunu ölçer. Bu makinede ölçülen tuzak (2026-09-08): çıplak komut
`CERTIFICATE_VERIFY_FAILED` ile düşerse `SSL_CERT_FILE`ı venv'in certifi'sine verin (komutun
tamamı `requirements.yml` başlığında).

## Ops sözleşmesi — komut satırı (repo kökünden)

```sh
# Kuru koşum. dagit.sh'ın `./dagit.sh` (bayraksız) hâlinin karşılığı.
ansible-playbook -i deploy/ansible/inventory.ini deploy/ansible/dagit.yml --check --diff

# Gerçek dağıtım (aynı komut --check'siz). dagit.sh'ın `--uygula` hâli.
ansible-playbook -i deploy/ansible/inventory.ini deploy/ansible/dagit.yml

# Kirli ağaçla BEYANLI istisna — dagit.sh'ın `--kirli-gec` bayrağı.
ansible-playbook -i deploy/ansible/inventory.ini deploy/ansible/dagit.yml -e kirli_gec=true

# Başka bir checkout'u dağıtmak (BEYANLI): worktree ise ikinci bayrak da ZORUNLU.
ansible-playbook -i deploy/ansible/inventory.ini deploy/ansible/dagit.yml \
  -e repo_kok_yerel=/yol/checkout -e worktree_gec=true

# Kapı envanteri (A1'e BAĞLANMAZ — ajan da koşabilir).
ansible-playbook --list-tasks -i deploy/ansible/inventory.ini deploy/ansible/dagit.yml
ansible-playbook --syntax-check -i deploy/ansible/inventory.ini deploy/ansible/dagit.yml
ansible-lint deploy/ansible/dagit.yml
```

## Kapılar — liste DÜŞMEZ

| Kapı | Ne sorar | Düşürür mü |
|---|---|---|
| `[0a]` | dağıtım kaynağı **ana checkout** mu; çalışma ağacı temiz mi; **dağıtılan tepe (`DAGIT_SHA`) burada donar** | evet (`-e worktree_gec=true` / `-e kirli_gec=true` ile beyanlı geçilir) |
| `[0b]` | `uv audit` — tedarik zinciri | evet |
| `[0c]` | `uv run lint-imports` — mimari sözleşmeler | evet |
| `[0d]` | `ops/import_tarama.py` — dev-daraltması hâlâ güvenli mi | evet (rc 2 = ölçülemedi de ENGEL) |
| `[5c]` | pano artefaktı kaynağından taze mi (`ops/artefakt_tazelik.py`) | rc 1 evet (kuru koşumda UYARI) · **rc 2 = ölçülemedi, sürer** |
| `[1]` | rsync kuru koşum — ne değişecek, ne SİLİNECEK | hayır (rapor) |
| `[1b]` | versiyonlu state farkı; hüküm `ops/state_fark_hukmu.py` | hayır (KOPYALA/ENGEL) |
| `[1c]` | repo birimi ↔ `/etc/systemd/system` yönerge farkı | **evet** — çare `site.yml`; kadans birimlerinin (brifing/bekçi/karne) hiç kurulmamış olması RAPOR |
| `[F9]` | rsync kapsamı DIŞINDAKİ 39 artefaktın içerik kıyası | hayır (görünürlük) |
| `[F10]` | `enabled + inactive` anomalisi | evet (override bayrağı YOK) |
| `[2]` | rsync `--delete` (28 dışlama sınıfı) | — |
| `[3]` | `uv sync --frozen` (dev grubu HARİÇ) | evet |
| `[4]` | bakım penceresi: durdur → state kopyası → başlat (`block`/`rescue`) | evet, reçeteyle |
| `[5]` | healthz (200 · 503 = bayat nabız) + son olay satırı | **hayır (rapor)** — hüküm `[5a]`/`[5b]`de |
| `[5a]` | doğrulama-token anahtar kontrolü (uç gövdesi doğru mu) | evet · **token yoksa fail-open** |
| `[5b]` | kod-tazelik değişmezi ("active" ≠ "yeni kodu koşuyor") | evet — beyan YAZILMAZ |
| `[B]` | `state/dagitim.json` beyanı (5 alan, bayt-özdeş doğrulanır) | hayır (yazılamazsa yüksek sesle) |

Çivi: `tests/test_ansible_dagit_v452.py` bölüm B — B1 her etiketi bir görev **adında** arar,
B9 `[4]` stop/start kapılarının **yönünü** Jinja ile çözerek altı senaryoda ölçer.

## Check-mode'da ne ÖLÇÜLÜR, ne ÖLÇÜLMEZ

`command`/`shell`/`script` görevleri check-mode'da **atlanır**. Bu yüzden kapılar ikiye ayrılır:

* **Kuru koşumda da GERÇEKTEN ölçülenler** (`check_mode: false`, hepsi salt okuma):
  `[0a]` `[0b]` `[0c]` `[0d]` `[1]` `[1b]` `[1c]` `[F9]` `[F10]`. dagit.sh'ın kuru koşumu da
  bunları koşuyordu; playbook'un kuru koşumu ondan zayıf olamaz.
* **`[5c]` kuru koşumda ÖLÇÜLÜR ama DURDURMAZ.** dagit.sh'ın kuru koşumu `[5c]`yi hiç koşmuyordu
  (kuru koşum `exit 0` ile biter, `[5c]` bloğu dağıtımın sonundadır) — bu playbook onu Play 1'e
  aldığı için kuru koşumda da ölçer. Bayat artefakt kuru koşumda **uyarı** basar (`cd ui &&
  npm run build`), dağıtımı yalnız **gerçek** koşumda durdurur. Gerekçe: `[5c]` kuru koşumu
  düşürseydi `[1]`/`[1b]`/`[1c]`/`[F9]`/`[F10]` — A1 hakkında sorulan her şey — hiç ölçülmezdi.
* **Atlananlar, her biri "ÖLÇÜLMEDİ" diye ADIYLA raporlar:** `[3]` `[4]` `[5]` `[5a]` `[5b]` `[B]`.
  Atlanan kapı bir sağlık hükmü DEĞİLDİR — soru cevapsız kalmıştır. Çivi: v452 B14 (`when: not
  ansible_check_mode` taşıyan HER kapının aynı etiketli bir "ÖLÇÜLMEDİ" karşılığı vardır).

`[2]` rsync check-mode'da kendiliğinden `--dry-run` ile koşar (canlıya yazmaz). `[4]` penceresinin
modülleri (`systemd_service`, `copy`) check-mode'da hiçbir şeyi değiştirmez.

## `dagit.sh`a göre BEYANLI farklar (ölçüldü 2026-09-08)

1. **`[5c]`nin yeri.** dagit.sh'ta `[5a]` ile `[5b]` arasında, yani dağıtımdan **sonra** koşar;
   burada yerel kapılara alındı. Ölçüm ve onarım (`cd ui && npm run build`) zaten yereldir;
   erken koşmak bayat artefaktı rsync'ten önce yakalar. Çıkış kodu sözleşmesi aynen korunur.
2. **`[3]` bayrağı.** dagit.sh koşum anında `uv sync --help`e sorup `--no-default-groups`a
   yükselir; playbook A0 defaults'undaki taban bayrağı (`uv_sync_bayrak`, `--no-dev`) kullanır —
   ikisi de ÖLÇÜLEN aynı 17 paketi kaldırıyor. Yükseltme Rol-1'in kararıdır, sondanın değil.
3. **`[B]` yazımı.** `copy: content:` **kullanılmaz** (v451 Çivi 3a `deploy/ansible/` altındaki
   her YAML'da modül argümanı `content:`i yasaklar, `.j2` de yasaktır). Yazım dagit.sh'ın kendi
   iki adımıyla yapılır: `tee <tmp>` + `mv <tmp> <hedef>` (atomiklik korunur), sonra `slurp` ile
   bayt-özdeşlik doğrulanır. JSON `to_json` ile kurulur: alan adları ve sırası dagit.sh'ın
   `printf` şablonuyla aynıdır (B7); tek fark `sandbox_eski_kod` dizisinde 2+ öğe varken
   ayraçtan sonra bir boşluk olmasıdır (`["a", "b"]` ↔ `["a","b"]`) — okuyucular JSON ayrıştırır,
   anlam aynıdır.
4. **`[F10]`/`[4]` ölçümü `service_facts` ile DEĞİL `systemctl` ile yapılır.** Ölçüldü (modül
   kaynağı okundu): `service_facts` systemd toplayıcısı `state`i `running` / `stopped` diye iki
   kovaya indirir ve `inactive` · `activating` · `deactivating` ayrımını **kaybeder**. dagit.sh'ın
   ölçütü tam olarak `is-active == inactive` (ve `[4]`ünki `!= inactive`) olduğu için fact'lerle
   yazılsaydı `[4]`ün durdurma kümesi güvensiz yönde daralırdı.
5. **`[1b]` hüküm süreci düşerse** dagit.sh her dosya için `ENGEL` varsayıyordu; playbook aynı
   sonucu `block`/`rescue` ile üretir (tüm farklı dosyalar ENGEL) ve nedeni ADIYLA basar.
6. **`[1c]` artık DURDURUR** (plan Architecture kararı; dagit.sh yalnız raporluyordu). İki koldan
   yalnız biri düşürür: **yönerge farkı** durdurur (2026-08-14 "sessiz etkisizlik" vakası),
   **kadans birimlerinin** (brifing/bekçi/karne) hiç kurulmamış olması RAPORdur — A0 rolü onları
   `brifing_devri: false` iken BİLEREK kurmaz ve durduran bir kapı, çaresi kendisinde olmayan bir
   kapı olurdu. `fail_msg` hangi `Anahtar=değer` satırlarının ayrık olduğunu **listeler**
   (dagit.sh `diff | grep '^[<>]'` ile aynı bilgi) ve kadans kaçışını adıyla yazar
   (`site.yml … -e brifing_devri=true`).
7. **Kuru koşumda `[5c]` ÖLÇÜLÜR** (yukarıdaki check-mode bölümü): dagit.sh'ın kuru koşumu onu hiç
   koşmuyordu. Kazanç: bayat artefakt kuru koşumda GÖRÜNÜR. Bedel ölçüldü ve ödenmedi: kuru
   koşumda kapı DÜŞÜRMEZ, yalnız uyarır.
8. **Dağıtım kaynağı `~/AI-Trading`** (dagit.sh `REPO="$HOME/AI-Trading"` ile birebir), playbook'un
   bulunduğu ağaç DEĞİL. `[0a]` bunu bir kapıyla ölçer: bu playbook'un durduğu git ağacı ana
   checkout değilse dağıtım DURUR; bilinçli istisna `-e worktree_gec=true` ve o istisna `[B]`
   beyanına **altıncı alan** olarak yazılır (`worktree_gec`). Gerekçe CLAUDE.md §9: "dagit.sh
   NEREDEN çağrılırsa çağrılsın ana checkout'un O ANKİ HEAD'ini iter, senin ağacını değil;
   'ağacım temiz' bir güvence DEĞİLDİR" (vaka 2026-08-26). Bayrağın adı DAR, anlamı GENİŞtir:
   `-e repo_kok_yerel=<worktree OLMAYAN başka checkout>` ile koşulduğunda da istenir ve beyana
   `true` yazılır — okunuşu "ana checkout DIŞINDAN dağıtıldı"dır, "worktree'den" değil. Ad
   değişikliği beyan sözleşmesini (`worktree_gec` alanı, v452 B7/B12) etkiler: Rol-1 kalemi.
9. **`[5]` healthz bir KAPI DEĞİLDİR** — dagit.sh gibi yalnız RAPOR eder (`status_code: [200, 503]`,
   `retries` YOK). 503 = "nabız bayat, süreç canlı" belgeli hâlidir ve ADIYLA basılır; hüküm
   `[5a]`/`[5b]`dedir. Kapı olsaydı, 503 döndüren bir turda `[5a]`/`[5b]`/`[B]` hiç koşmaz ve yeni
   kod canlıdayken `state/dagitim.json` eski sha'da kalırdı — `[B]`nin var olma sebebi olan
   ortamlar-arası kıyas tam da o turda kör kalırdı. **Sınır BEYANLI** (ölçüldü, sentetik `uri`
   koşumu 2026-09-08): 200/503 DIŞINDAKİ bir kod ya da bağlantı hatası `uri` sözleşmesi gereği
   play'i DÜŞÜRÜR (`[5a]`/`[5b]`/`[B]` koşmaz); dagit.sh bileşik ssh komutunu `; echo` ile
   bitirdiği için hiçbir kodda durmuyordu. Tam birebirlik `failed_when: false` isterdi — o
   YASAK (Yasa 4), bu yüzden fark ödeniyor ve burada yazılı.
10. **`[B]` beyanı ALTI alan yazar**: dagit.sh'ın beş alanı (ad ve SIRA aynı) + `worktree_gec`
   (madde 8). Geçiş süresince dagit.sh beş alan yazmayı sürdürür; okuyucular (meridian/api.py
   `dagitim`, pano Gözetim satırı) JSON ayrıştırır ve bilmedikleri alanı görmezden gelir.
11. **`[F9]` ayrık dosyada `diff -u … | head -12` GÖVDESİ BASILMAZ** — playbook yalnız ayrık
   YOLLARI listeler. Bilinçli: `[F9]` listesi `config.yaml`/`SOUL.md` sınıfı dosyalar taşır ve
   satır gövdesi sır sızdırabilir (`slurp` içeriği zaten kontrolcüde, basmak ayrı bir karardır).
   BEDEL ÖDENDİ ve yazıldı: operatör "hangi dosya ayrık"ı görür, "nerede ayrık"ı görmez —
   `diff` elle koşulur. Gövdenin sızdırmayan bir özetiyle (bayt sayısı / hangi taraf yeni)
   değiştirilmesi Rol-1 kalemidir.

> Bu liste ile davranış arasındaki bağ ÖLÇÜLÜR: her maddenin playbook'ta bir `# BEYANLI-FARK n`
> şerhi vardır ve kıyas İKİ YÖNLÜDÜR (v452 `test_B18_…`) — listeden madde düşerse de, playbook'a
> şerhli bir sapma eklenip listeye yazılmazsa da çivi kırılır. Sayı vererek sunulan eksik bir
> liste, okuyucuya "başka fark yok" hükmünü verdirir.

## Sır

`.dash.env` token'ı **hiçbir Ansible değişkenine girmez**: `[5a]` betiği `.dash.env`i A1'in kendi
içinde okur (`--env-dosya` varsayılanı) ve yalnız `VAR|<yol>|<anahtar>` / `YOK|…` hükmü döner. Uç
gövdeleri de süreç içinde ayrıştırılır. Token'ı `slurp` + `no_log` ile kontrolcüye taşımak bu
güvenceden **zayıf** olurdu (sır ağdan geçer ve belleğe girer) — bu yüzden taşınmıyor.

**Token'ı `ubuntu` okur, root DEĞİL.** `[5a]` ve `[5b]` `script:` görevleri `become: false` taşır
(dagit.sh ikisini de `ssh ubuntu@…` ile koşturuyordu): `.dash.env` `ubuntu`nun 0600 dosyasıdır ve
`/proc/<pid>` okuması da root gerektirmez. Play 2 `become: true` olduğu için bu satır olmasaydı
iki betik sessizce ROOT koşardı — en az yetki burada bir tercih değil, birebirliğin parçasıdır.
Çivi: v452 B15 (her `script:` görevinde `become: false`).
