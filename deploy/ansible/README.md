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
