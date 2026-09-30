# Konuşan bot filosu — Parça 1b G3: bot ağ geçidi (ayrı Hermes kökü + systemd birimi) — Uygulama Planı

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `meridian-botlar.service` tek bir Hermes ağ geçidini ayrı bir kökte (`/home/ubuntu/.hermes-botlar`) çok profilli kipte koşturur; `sef`/`bekci`/`karne` sohbet profilleri `/p/<ad>/` altında, yalnız Meridian MCP araçlarıyla, 127.0.0.1:8642'de sunulur. Bu plan DEPO tarafını (üreteç, kök profil, birim, A0 rolü, ölçüm sayacı) kurar; canlı kurulum ve test-ateşleme Rol-1'in kontrol listesidir (son bölüm). Birim ETKİN EDİLMEZ — etkinleştirme ayrı değişiklik (A0 kuralı).

**Architecture (A1 Hermes v0.19.0 kaynağından ölçüldü, 2026-09-30):**
- `HERMES_HOME` `~/.hermes` DIŞINI gösterirse o dizin köktür (`hermes_constants.get_default_hermes_root`); çoklu kip varsayılan profil + `<kök>/profiles/*` hepsini sunar (`hermes_cli/profiles.py::profiles_to_serve`); dinleyiciyi VARSAYILAN profil tutar.
- Sırlar çoklu kipte PROFİL `.env`inden okunur, `os.environ`a düşmez (`agent/secret_scope.py::get_secret`; global küme yalnız HERMES_HOME/PATH/… ) → `BOT_KEY_<AD>` + `HINDSIGHT_API_KEY` her sohbet profilinin `.env`inde, `API_SERVER_KEY` kökün `.env`inde. Besleme: rotasyon aracı kasadan (rapor profilleri emsali).
- İkincil profil `config.yaml`ı `platforms.api_server.enabled: false` taşımak ZORUNDA — aksi hâlde süreç ortamındaki anahtar ikincil profilde dinleyici açmaya zorlar (`gateway/config.py::_apply_env_overrides` şerhi; `MultiplexConfigError`).
- MCP alt süreç ortamı SÜZÜLÜR (`tools/mcp_tool.py::_build_safe_env`: PATH/HOME/USER/LANG/LC_ALL/TERM/SHELL/TMPDIR + `XDG_*` + config `env:`) → `CREDENTIALS_DIRECTORY` geçmez; `bot_hafizasi_ara` Hindsight anahtarını `secrets.credential_oku` ile okur → sohbet profilinin MCP `env:`ine birimin sabit credential yolu `/run/credentials/meridian-botlar.service` yazılır; birimde `LoadCredential=HINDSIGHT_API_TENANT_API_KEY:/etc/hindsight/creds/HINDSIGHT_API_TENANT_API_KEY`.
- `HERMES_WRITE_SAFE_ROOT` SÜREÇ başına okunur (`agent/file_safety.py`, `os.getenv`) → tek ağ geçidinde bot başına kum havuzu İMKÂNSIZ; BEYANLI sapma: ortak `/opt/meridian/var/bots/sohbet` (dosya/terminal takımları zaten kapalı — ikinci katman).
- İstek dökümü kapatılamaz (`agent/agent_init.py` şerhi, `logs_dir` koşulsuz) → profil `logs/` 0700 + yaş temizliği (Rol-1 listesi).

**Tech Stack:** Python stdlib + PyYAML; systemd; Ansible A0 rolü (`deploy/ansible/roles/meridian_a1/`); mevcut `ops/sohbet_profili_uret.py` (G2).

**Spec:** `docs/superpowers/specs/2026-09-29-konusan-bot-filosu-design.md` §3.3–§3.4 · G2 planı "Sonra" bölümü (ölçümler) · depo haritası (Rol-1 oturumu 2026-09-30).

## Global Constraints
- Birim `etkin_birimler`e EKLENMEZ (A0 kuralı: uzun ömürlü birim ayrı değişiklikle etkin); `birim_adaylari` (dagit bakım penceresi, v452 A3b DONUK) DEĞİŞMEZ.
- `LoadCredential=` YALNIZ drop-in'de (`deploy/oracle-a1/meridian-botlar.service.d/*.conf`) — depo kuralı (v447 `_dropin_kredensiyelleri`).
- Birim `ExecStart`ında sır adı sınıfında değişken genişlemesi YOK (v554).
- Sertleştirme filo ortak seti (v174 `ORTAK_SET`) + `ReadWritePaths=/opt/meridian -/home/ubuntu/.hermes-botlar` (v553 B: `HERMES_HOME` yolu kapsanır); `/opt/meridian` MCP yazımları için (approvals.jsonl, .locks, events.jsonl, istek/).
- `KillMode=mixed` + `TimeoutStopSec=30` (Parça 0 v3: ağ geçidi SIGTERM'i yok saydı → SIGKILL gerekti; learn'ün `control-group` gerekçesi — hermes CLI alt süreçleri — burada yok: ağ geçidinin çocukları MCP stdio süreçleridir ve ana süreçle ölür). Değer G3c'de ölçülür.
- Üreteç tek kaynak: MCP girdisi kökten (`deploy/hermes/config.yaml`), duruş rapor profilinden (G2); yeni sabitler üreteçte.
- Test numarası v601 (v600 TSK-257'ye ayrıldı). Test adlarında FAILED/ERROR yok; yorumlarda `dosya.py:NNN` yok; Yasa 4/6.

## Review Focus
1. Kök (varsayılan) profil `/p/` öneksiz isteğe cevap verirse araçsız model UYDURUR (Parça 0) → kök profilin araç listesi boş VE SOUL'u "bu uç kullanılmaz" der; `bota_sor` yalnız `/p/<ad>/` kullanır (çivi).
2. İkincil profilde `platforms.api_server.enabled: false` yoksa ağ geçidi açılışta düşer → üç profilde çivili.
3. MCP `env:`indeki credential yolu birim adıyla ayrışırsa `bot_hafizasi_ara` sessizce "credential yok" döner → yol birim adından TÜRETİLİR ve çivi birim dosyasının adıyla kıyaslar.
4. Birim kopyalanır ama `etkin_birimler`de değildir → dagit [1c] "kurulmamış birim" kapısı: site.yml dağıtımdan ÖNCE koşmalı (Rol-1 listesi).
5. EDG-2026-086 sayımı bot önerilerini pano sohbeti önerileriyle karıştırmamalı → `oturum` `mcp:` önekli satırlar ayrı sayılır.

---

### Task 1: Üreteç — ikincil profil api_server kapalı, MCP credential yolu, kök profil, metin düzeltmeleri

**Files:** Modify `ops/sohbet_profili_uret.py`, `tests/test_sohbet_profili_uret_v599.py`; Create (ÜRETİLİR) `deploy/hermes/sohbet/config.yaml`, `deploy/hermes/sohbet/SOUL.md`; yeniden üret `deploy/hermes/sohbet/profiles/*`.

**Interfaces:** Produces: sabitler `BOT_BIRIMI = "meridian-botlar.service"`, `BOT_KUM_HAVUZU = "/opt/meridian/var/bots/sohbet"`, `KOK_DIZIN = "/home/ubuntu/.hermes-botlar"`; `uret()` çıktısına iki kök dosya (`deploy/hermes/sohbet/config.yaml`, `deploy/hermes/sohbet/SOUL.md`).

- [ ] **Step 1: Başarısız testler (v599'a ekle):**
  - her profil: `c["platforms"]["api_server"]["enabled"] is False`.
  - her profil: `c["mcp_servers"]["meridian"]["env"]["CREDENTIALS_DIRECTORY"] == f"/run/credentials/{u.BOT_BIRIMI}"` ve `env`in geri kalanı kökle eşit (mevcut çivi `m["env"] == kok["env"]` → `{k: v for k, v in m["env"].items() if k != "CREDENTIALS_DIRECTORY"} == kok["env"]`).
  - `(KOK / "deploy/oracle-a1" / u.BOT_BIRIMI).is_file()` — Task 2 sonrası yeşil olur; Task 1'de `pytest.mark.xfail(strict=True, reason="Task 2 birimi")` İLE yazılır ve Task 2 xfail'i kaldırır.
  - her profil manifesti: `HERMES_WRITE_SAFE_ROOT.default == u.BOT_KUM_HAVUZU`; `HINDSIGHT_API_KEY` açıklaması "credential" DEMEZ, ".env" der.
  - kök config: `gateway.multiplex_profiles is True`; `platform_toolsets == {"api_server": []}`; `agent.disabled_toolsets ⊇ YASAK_TAKIMLAR`; `mcp_servers` YOK ya da `meridian.enabled is False`; guard kancası + `hooks_auto_accept` + `approvals.deny` sef rapor profiliyle aynı (duruş mirası kaynağı: `deploy/hermes/profiles/sef/config.yaml`); `memory` YOK (kök hafızasız).
  - kök SOUL: "Bu uç doğrudan kullanılmaz" cümlesini ve `/p/<bot>/` yönlendirmesini taşır; araç/hafıza vaadi yok.
  - `--kontrol` kök dosyaları da kapsar (bayat kök → 1).
- [ ] **Step 2: Kırmızı** — `.venv/bin/python -m pytest tests/test_sohbet_profili_uret_v599.py -p no:cacheprovider`
- [ ] **Step 3: Uygula** — üreteçte `_config`e `platforms` + `env` eki; `_dagitim` metinleri; `_kok_config()` ve `_kok_soul()` (sabit metin: "Bu, Meridian bot ağ geçidinin kök profilidir. Bu uç doğrudan kullanılmaz; her soru `/p/<bot>/` önekiyle bir bota gider. Buraya gelen her mesaja yalnız şunu yaz: Bu kök profil; lütfen bir bot seçin."); `uret()` kök dosyaları ekler. Sonra `--yaz`, `--kontrol` 0.
- [ ] **Step 4: Yeşil** · **Step 5: Mutasyon** (api_server satırını kaldır; env ekini kaldır; kök `platform_toolsets`e `meridian` ekle; kök SOUL cümlesini sil — her biri kırmızı) · **Step 6: Kapsam** — v599 + v593 + v266 + v329 + v334 + v382 + v571/v572 (üretilmiş kök dosyalar tarama çivilerinde).

### Task 2: Birim + drop-in + A0 rolü

**Files:** Create `deploy/oracle-a1/meridian-botlar.service`, `deploy/oracle-a1/meridian-botlar.service.d/54-hafiza-credential.conf`; Modify `deploy/ansible/roles/meridian_a1/defaults/main.yml` (`dropin_dizinleri`, `dropin_kaynaklari`, yeni `sohbet_kok_dizini` + dizin görevleri), `deploy/ansible/roles/meridian_a1/tasks/dizinler.yml` (`/opt/meridian/var/bots/sohbet` 0700 ubuntu; `/home/ubuntu/.hermes-botlar` 0700 ubuntu + `profiles/` + `profiles/<ad>/` + `profiles/<ad>/hindsight` — döngü AYRI liste, `bot_adlari` DEĞİL), `deploy/ansible/roles/meridian_a1/tasks/hermes.yml` (sohbet kök + profil DOSYA kopyası: `deploy/hermes/sohbet/{config.yaml,SOUL.md}` → kök, `profiles/<ad>/{SOUL.md,config.yaml,distribution.yaml,hindsight/config.json}` → profil; `mode 0600`, `backup: true`; `.env` ASLA kopyalanmaz), `tests/test_ansible_a0_v451.py` (`UZUN_OMURLU_BIRIMLER` += `meridian-botlar.service`), `tests/test_h3_tur2_v174.py` (`SERTLESTIRILEN` += birim), `tests/test_sohbet_profili_uret_v599.py` (xfail kaldır); Test `tests/test_bot_agi_gecidi_v601.py`.

- [ ] **Step 1: Başarısız testler (v601):** birim `Type=simple`, `User=ubuntu`, `Environment=HERMES_HOME=/home/ubuntu/.hermes-botlar`, `Environment=HERMES_WRITE_SAFE_ROOT=/opt/meridian/var/bots/sohbet`, `ExecStart=/home/ubuntu/.local/bin/hermes gateway --accept-hooks run` (A1'de ölçüldü 2026-09-30: `~/.local/bin/hermes` ubuntu sahipli sarmalayıcı; `--accept-hooks` `gateway` alt ayrıştırıcısının bayrağıdır ve `run`dan ÖNCE gelir — `hooks_auto_accept: true` config'te de var, bayrak ikinci katman; Hermes'in `~/.hermes-botlar` dışına — ör. `~/.cache` — yazıp yazmadığı G3c'de `ProtectHome=read-only` altında ölçülür, yazıyorsa `-/home/ubuntu/.cache` eklenir), `KillMode=mixed`, `TimeoutStopSec=30`, `Restart=on-failure`, `[Install]` VAR (`WantedBy=multi-user.target` — uzun ömürlü; enable ayrı değişiklik); `ReadWritePaths` her iki yolu kapsar; drop-in `LoadCredential=HINDSIGHT_API_TENANT_API_KEY:/etc/hindsight/creds/HINDSIGHT_API_TENANT_API_KEY`; `etkin_birimler`de YOK; `birim_adaylari` değişmedi; A0 hermes görevleri `.env` kopyalamaz (görev gövdesinde `.env` yok); üreteç `BOT_BIRIMI` == birim dosya adı; üreteç `KOK_DIZIN` == birim `HERMES_HOME`; üreteç `BOT_KUM_HAVUZU` == birim `HERMES_WRITE_SAFE_ROOT` == A0 dizin görevi yolu.
- [ ] **Step 2–6:** kırmızı → uygula → yeşil → mutasyon (KillMode'u sil; RWP'den kökü düşür; drop-in'i sil; üreteç sabitini değiştir — her biri kırmızı) → kapsam: v601 + v599 + v451 + v452 + v553 + v554 + v563 + v174 + v447 (`ROTASYON_DISI_KREDENSIYELLER` gerekirse — drop-in yeni bir `LoadCredential` çifti ekler; P6/P6b rotasyon tablosu ya da gerekçeli beyan ister: tenant anahtarı bugün hangi alt komutla döner, ölç) + v329 + codelaw.

### Task 3: EDG-2026-086 sayımı bot önerilerini ayırır + CI duman

**Files:** Modify `research/olcumler/edg086_pano_sohbet/sayim.py` (`oneri_olc`), `research/olcumler/edg086_pano_sohbet/README.md`, `tests/test_edg086_sayim_v450.py`, `ops/ci_duman.sh` ([4/4] listesine `tests/test_sohbet_profili_uret_v599.py` — taze klonda state'siz geçtiği ÖLÇÜLÜR: `git clone` + `uv run pytest` o dosya; geçmiyorsa ekleme ve raporla).

- [ ] **Step 1: Başarısız test:** `oturum` `mcp:` ile başlayan öneri satırı pano öneri sayısına GİRMEZ; ayrı `oneri_bot` alanında sayılır; `oturum` alanı olmayan eski satırlar pano sayılır (geriye uyum). Kart eşiği/kill-list'e DOKUNULMAZ (sayım bir TANI alanıdır — kart `olcum_plani` "öneri: tanı").
- [ ] **Step 2–6:** kırmızı → uygula → yeşil → mutasyon (önek süzgecini kaldır → kırmızı) → kapsam v450 + codelaw.

---

## Rol-1 canlı kontrol listesi (G3c — ajan DEĞİL; sırası bağlayıcı)
1. Sır: `API_SERVER_KEY` (≥16 karakter) kasaya + `deploy/sir_envanteri.yaml` `vault_kv` (emsal `grafana_admin_parola` commit 5004544d) + `python ops/vault_politika_uret.py --uygula` + v491/v485 — AYRI dilim (Task 4 adayı; sır dosyaları sınıflandırıcıda engellenebilir → operatör).
2. `.env` tohumlama: `~/.hermes-botlar/.env` (`API_SERVER_KEY`), `~/.hermes-botlar/profiles/<ad>/.env` (`BOT_KEY_<AD>`, `HINDSIGHT_API_KEY`) — 0600 ubuntu; rotasyon aracının `_kopyalar()` tablosuna yeni satırlar + `deploy/sir_envanteri.yaml` `rotasyon_kopyalari` + v447 `KOPYA_SAYISI` + v520/v491 pinleri (AYRI dilim). İlk değer operatör/rotasyon aracıyla; Rol-1 sır DEĞERİ görmez/yazmaz.
3. site.yml (A0) → birim /etc'de, dizinler + profil dosyaları kökte; SONRA dagit (aksi [1c] durdurur).
4. `sudo systemctl start meridian-botlar` (enable DEĞİL) → ölç: `/health` 200; `/p/bekci/v1/toolsets` yalnız meridian; `/v1/chat/completions` öneksiz → kök profil reddi; `/p/sef/…` bir soru → oturumda `role: tool` (gerçek araç sonucu); `bot_hafizasi_ara` sef'ten → credential bulundu (hata YOK); karne'den → izinli değil; guard kancası ve `approvals.deny` profil başına uygulanıyor mu (bir `terminal` isteği reddedilir); `logs/request_dump_*` dizin izni; `systemctl stop` süresi (< `TimeoutStopSec`, SIGKILL yok); MCP çocukları durdurmada ölüyor mu (`ps`).
5. EDG-2026-086 ayrımı canlıda; `is_iste` `.path` birimleri etkin değilse sohbet profillerinde `is_iste` vaadi → operatöre karar (SOUL satırı `is_iste` kadroda olduğu için var).
6. Hepsi yeşilse: `etkin_birimler`e AYRI değişiklik + dağıtım; ölçüm kartı EDG-2026-107 (G5) AYNI gün ADIM-0.
