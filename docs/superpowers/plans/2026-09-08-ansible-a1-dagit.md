# TSK-176 Faz A1 — `deploy/ansible/dagit.yml`: dağıtım playbook'u dagit.sh'ın YERİNE (K1) — uygulama planı

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:subagent-driven-development. Steps use checkbox syntax.
> **Sevk kararı (Rol-1, 2026-09-08 02:2xZ):** plan hazır; implementer OPERATÖR SABAH GÖZETİMİNDE sevk edilir — dokuz test dosyası dagit.sh iç
> yapısına çivili (v266 F9, v172, v367, v451, v286, v154, v204, v326, v329) ve ilk playbook dağıtımı izlenerek yapılmalı (K1: geçiş süresince iki yol).

**Goal:** `./dagit.sh --dry-run|--uygula`nın [0a][0b][0c][0d][1][1b][1c][F9][F10][2][3][4][5][5a][5c][5b][B] kapı ve adımlarını, davranış birebir,
`deploy/ansible/dagit.yml` playbook'una taşımak; dagit.sh BİR sürüm ince sarmalayıcı kalır, sonra silinir. Kapılar `pre_tasks`/`assert`/`block-rescue`;
listeler (rsync dışlama, F9 çiftleri, doğrulama uçları, birim adayları) TEK KAYNAK `deploy/ansible/vars/dagit_vars.yml` — dagit.sh sarmalayıcı bu
listeleri okumaz; onları okuyan testler yeni kaynağa taşınır.
**Spec:** docs/TASARIM-ALTYAPI-KOD-2026-09-08.md §2, §4 (Meridian kapıları hiçbir araca taşınmaz — burada playbook'a TAŞINIR ama düşmez), §5 A1, §8 K1.
**Emsal:** `dagit.sh` (844 satır; kapı gövdeleri ve gerekçeleri ORADA — implementer her kapının yorumunu okur ve göreve `name:` olarak taşır), A0 rolü
`deploy/ansible/roles/meridian_a1` (defaults `uv_sync_bayrak`, `etkin_birimler`; kadans kapısı deseni; check-mode beyanı), `tests/test_ansible_a0_v451.py`
(YAML parse çivileri, `_dongu_ogeleri`, Jinja senaryo tablosu).

**Architecture:** iki play. **Play 1 — YEREL KAPILAR** (`hosts: localhost`, `connection: local`, `gather_facts: false`): [0a] temiz ağaç (`git status
--porcelain` boş; `-e kirli_gec=true` ile beyanlı geçiş → `kirli_gec_kullanildi`), `dagit_sha` (`git rev-parse HEAD`), [0b] `uv audit`, [0c] `uv run
lint-imports`, [0d] `uv run python ops/import_tarama.py --sessiz`, [5c] pano artefakt tazeliği (Mac `stat -f %m` / Linux `stat -c %Y` — `ops/artefakt_tazelik.py`
YENİ küçük betik, dagit.sh'taki iki-platform gövdesi taşınır) — hepsi `check_mode: false` (`--check`te de ÖLÇÜLÜR; salt okuma), `changed_when: false`,
`failed_when` açık. **Play 2 — A1** (`hosts: meridian`, `become: true`): [1] `synchronize` `--dry-run` + `--itemize-changes` → `*deleting` satırları
raporda (SIGPIPE sınıfı: çıktı dosyaya, `head` YOK); [1b] versiyonlu state farkı: `git ls-files state/` → `slurp` canlı → fark varsa `ops/state_fark_hukmu.py`
(YENİ: dagit.sh'taki gömülü YAML düzleştirme+hüküm python'u DOSYAYA taşınır; dagit.sh sarmalayıcı döneminde de onu çağırır — tek kaynak) → `KOPYALA|ENGEL|OPERATÖR`;
[1c] birim ayrıklığı: A0 rolü yakınsar → burada ASSERT (repo birim == /etc; değilse "önce `ansible-playbook deploy/ansible/site.yml`" ile DUR); [F9]
`f9_ciftleri` (vars) `slurp`+`stat` içerik kıyası → AYRIK/ölçülemedi listesi (rapor + özet, dagit gibi düşürmez); [F10] `service_facts` → enabled+inactive
anomali → assert; [2] `synchronize --delete` (`rsync_disla` vars'tan); [3] `command uv sync --frozen {{ uv_sync_bayrak }}` (A0 defaults ile aynı değişken —
`vars_files`); [4] BAKIM PENCERESİ `block`: `birim_adaylari` (meridian, meridian-barsarchive, meridian-learn) için `is-enabled`/`is-active` ölç →
yalnız aktif olanlara `stopped`, [1b] KOPYALA kararı varsa `backups/state/<sf>.bak-<damga>` + `copy` + `slurp` bayt kıyası (uyuşmazsa `fail` — servisler
DURMUŞ hâlde, reçete basılır), `daemon_reload`, yalnız enabled olanlara `started`, 8 s sonra `is-active`; `rescue`: reçete + `fail` (sessiz değil);
[5] healthz `uri` + son olay satırı; [5a] `script: deploy/oracle-a1/dogrulama_anahtar.py` (YENİ: dagit'teki gömülü python + uç listesi `dogrulama_uclari`
vars'tan; "OLCULEMEDI token yok" fail-open beyanlı; YOK → `fail`, beyan yazılmaz); state/ artık kontrolü (rapor); [5b] `script: deploy/oracle-a1/kod_tazelik.sh`
(YENİ: dagit'teki gömülü uzak betik dosyaya; IHLAL → `fail`, BEKLENEN → `sandbox_eski_kod` listesi); [B] beyan: `copy content=` JSON (`deployed_sha`,
`dagitildi_utc` (localhost'ta `date -u` fact), `dagitan_host`, `kirli_gec_kullanildi`, `sandbox_eski_kod`) → `state/dagitim.json` + `slurp` bayt kıyası.
Check-mode: Play 1 kapıları koşar; Play 2'de `synchronize` kuru koşum yapar, `command`/`script` görevleri ATLANIR ve `debug` "check-mode'da ÖLÇÜLMEDİ" der
(A0 K4 deseni). **dagit.sh (sarmalayıcı, bir sürüm):** `--dry-run` → `ansible-playbook deploy/ansible/dagit.yml --check --diff`; `--uygula` → aynı komut
`--check`siz; `--kirli-gec` → `-e kirli_gec=true`; başta "dagit.sh EMEKLİ OLACAK — playbook'a yönlendiriyor" satırı; gövdesindeki eski kapılar SİLİNİR.

**Tech Stack:** ansible-core 2.18 (dev grubu), `ansible.posix.synchronize` (KOLEKSİYON: `ansible-galaxy collection install ansible.posix` → `deploy/ansible/requirements.yml`
+ README + v452 çivisi "koleksiyon kurulu"), pytest çivileri (YAML parse), `deploy/ansible/vars/dagit_vars.yml`.

## Global Constraints
- Kapı listesi DÜŞMEZ: [0a][0b][0c][0d][1][1b][1c][F9][F10][2][3][4][5][5a][5c][5b][B] — v452 çivisi her kapının `name:`ini playbook'ta bulur (etiket `[0a]` … `[B]` görev adında).
- Tek kaynak: `rsync_disla`, `f9_ciftleri`, `dogrulama_uclari`, `birim_adaylari`, `state_versiyonlu` (git ls-files'tan türer) YALNIZ `deploy/ansible/vars/dagit_vars.yml`de;
  dagit.sh'tan silinir; okuyan testler (v266, v172, v367, v286, v154, v204, v326, v329, v451 F9 çivisi) yeni kaynağa taşınır — her taşıma bir çivi olarak kalır, silinmez.
- Restart/stop yalnız `birim_adaylari` (TSK-092 semantiği: yalnız aktif olan durur, yalnız enabled olan başlar); hindsight/apisix/litestream/timer'lara DOKUNULMAZ.
- `ignore_errors`/`failed_when: false` YASAK; `block/rescue` reçete + `fail`. Sır değeri hiçbir çıktıda (token `.dash.env`den `slurp` + `no_log`).
- Gömülü çok-satır python/bash YOK (A0 kuralı + 2026-07-30 IndentationError vakası): `ops/state_fark_hukmu.py`, `ops/artefakt_tazelik.py`, `deploy/oracle-a1/dogrulama_anahtar.py`,
  `deploy/oracle-a1/kod_tazelik.sh` DOSYA; dagit.sh sarmalayıcı döneminde aynı dosyaları çağırır (tek kaynak, eski gövde silinir).
- Test numaraları SABİT: v452 (`tests/test_ansible_dagit_v452.py`). Taşınan çiviler kendi dosyalarında kalır (numara kimliktir).
- Çapa yasağı; `-q` yok; seri pytest; git yok; dağıtım yok; A1'e ssh YOK — playbook A1'e karşı yalnız Rol-1 (`--check --diff` → gerçek dağıtım operatör gözetiminde).

---

### Task 1 — Tek-kaynak listeleri + üç betik (implementer)
**Files:** Create `deploy/ansible/vars/dagit_vars.yml` (`rsync_disla` (dagit.sh RSYNC_EXC'ten BİREBİR — 27+1 öğe), `f9_ciftleri` (repo|canlı, 34+ çift), `dogrulama_uclari`
(3 uç: yol/anahtar/tip), `birim_adaylari`), `ops/state_fark_hukmu.py` (argv: canlı yol, repo yol → stdout `HUKUM=KOPYALA|ENGEL|OPERATOR` + gerekçe satırları; dagit.sh'taki
gömülü python birebir), `ops/artefakt_tazelik.py` (`--repo <kök>` → çıkış 0 taze / 1 bayat / 2 ölçülemedi; iki platform stat), `deploy/oracle-a1/dogrulama_anahtar.py`
(A1'de python3; uç listesi argv/JSON; çıkış 0/1; "OLCULEMEDI token yok" özel), `deploy/oracle-a1/kod_tazelik.sh` (dagit'teki uzak gövde; çıkış 0 / IHLAL 1; BEKLENEN satırları) ·
Modify `dagit.sh` (bu dört gövde dosyaları ÇAĞIRIR; listeleri vars'tan `yq`/python ile okumaz — sarmalayıcıya kadar kendi listesini tutar AMA v452 eşitlik çivisi ikisini kıyaslar) ·
Test `tests/test_ansible_dagit_v452.py` (bölüm A).
- [ ] Çivi A1: `rsync_disla` == dagit.sh `RSYNC_EXC` öğeleri (sıra bağımsız, küme eşit); A2: `f9_ciftleri` == dagit.sh `F9_LISTE`; A3: `dogrulama_uclari` == dagit.sh `DOGRULAMA_UCLARI`;
      A4: dört betik komut satırından koşar (tmp sahne: state farkı KOPYALA/ENGEL/OPERATOR üç dal; artefakt taze/bayat; dogrulama_anahtar sahte gövde VAR/YOK; kod_tazelik sahte
      systemctl şimi IHLAL/BEKLENEN) · mutasyon her betikte ≥1.
- [ ] Uygulama · rapor.

### Task 2 — `deploy/ansible/dagit.yml` + `requirements.yml` + README (implementer, Task 1 sonrası)
**Files:** Create `deploy/ansible/dagit.yml`, `deploy/ansible/requirements.yml` (ansible.posix pinli), Modify `deploy/ansible/README.md` (dağıtım komutları; check-mode beyanı; ilk
dağıtım operatör gözetiminde), Test v452 bölüm B.
- [ ] Çivi B1: her kapı etiketi `[0a]…[B]` bir görev adında; B2: Play 1 kapıları `check_mode: false` + `changed_when: false`; B3: `birim_adaylari` dışında hiçbir `systemd_service`
      `state: stopped|started|restarted` yok (A0 çivisi deseni, şablon çözerek); B4: [4] `block` + `rescue` (`fail` içerir, reçete metni `backups/state` ve `systemctl start` anar);
      B5: [1b] hükmü `ops/state_fark_hukmu.py` çağrısından geliyor (gömülü python YOK — regex); B6: [5a]/[5b] `script:` dosyaları Task 1'dekiler; B7: [B] beyan alanları dagit.sh
      `printf` şablonuyla aynı beş alan; B8: `synchronize` `rsync_opts` `rsync_disla`dan türer ve `delete: true`; B9: Jinja senaryo tablosu — [4] stop/start `when` ifadeleri
      (aktif→stop, inactive→stop yok; enabled→start, disabled→start yok); B10: `--syntax-check` + `ansible-lint` temiz; B11: `ansible.posix` kurulu (`ansible-galaxy collection list`).
- [ ] Uygulama · rapor (A1'e KOŞULMADI beyanı).

### Task 3 — dagit.sh sarmalayıcı + test taşımaları (implementer, Task 2 sonrası)
**Files:** Modify `dagit.sh` (gövde → 3 komut + banner; `--kirli-gec` → `-e`), dokuz test dosyası (F9/RSYNC_EXC/bölüm başlığı okuyanlar → `dagit_vars.yml`/`dagit.yml` okur;
her taşıma aynı iddiayı korur; taşıma kaydı dosya başlığına), `docs/RUNBOOK.md` DEĞİL (üretilmiş; Rol-1), CLAUDE.md §1/§2 dagit satırları (Rol-1 — rapora öneri).
- [ ] Çivi C1: dagit.sh gövdesinde `rsync `, `uv audit`, `lint-imports` KALMADI (sarmalayıcı); C2: dokuz test dosyası yeşil; C3: `./dagit.sh --dry-run` → `ansible-playbook … --check --diff` çağırır (bash şimi ile ölçülür).
- [ ] Uygulama · rapor.

### Task 4 — Rol-1: merge → tam suite → `./dagit.sh --dry-run` (= playbook `--check --diff`) A1'e → **ilk gerçek dağıtım OPERATÖR GÖZETİMİNDE** (bakım penceresi) → RUNBOOK/CLAUDE.md
→ bir sürüm sonra dagit.sh silinir (ROADMAP TSK-176 A1 DONE).
