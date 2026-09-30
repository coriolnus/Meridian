# Konuşan Bot Filosu — Parça 1b G3b: Bot Ağ Geçidinin Sırları — Uygulama Planı

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bot ağ geçidinin (`meridian-botlar.service`) ve Telegram dinleyicisinin (`meridian-telegram.service`) ihtiyaç duyduğu sırları kasadan besleyen, döndüren ve ilk kez tohumlayan depo tarafını kurmak. Değerlere hiçbir aşamada Rol-1 ya da ajan dokunmaz.

**Architecture:** Mevcut rotasyon aracı `deploy/oracle-a1/sir_rotasyon.sh` tablo güdümlüdür. Satırı `_kopyalar()` tablosuna ve envanter aynasına (`deploy/sir_envanteri.yaml`) girmemiş bir sır için hiçbir yol yoktur. Bu dilim beş şey ekler:
- iki yeni sır ailesi: `API_SERVER_KEY` ve `BOT_KEY_<AD>` sohbet kopyaları;
- mevcut kiracı anahtarının üç sohbet kopyası;
- iki birimin credential drop-in'i;
- etkin olmayan birimi başlatmayan koşullu yeniden başlatma;
- tablodan türeyen, değersiz tohumlama kipi.

İlk kasa değeri ve canlı adımlar RUNBOOK'ta, Rol-1'de ya da operatörde kalır.

**Tech Stack:** bash 3.2 uyumlu kabuk (yerel çiviler macOS'ta koşar), gömülü `yardimci.py` (stdlib), YAML envanter, Vault Agent şablonları (`ops/vault_politika_uret.py` üretir), Ansible A0 rolü, pytest çivileri (v447/v520/v491/v521/v522/v557/v561/v439/v485/v601/v602 + yeni v604).

**Spec:** `docs/superpowers/specs/2026-09-29-konusan-bot-filosu-design.md` (§3.2, §3.4) · G3 planı `docs/superpowers/plans/2026-09-30-konusan-filo-parca1b-g3-bot-agi-gecidi.md` (Architecture + G3c listesi) · sır sınıfları `docs/TASARIM-SIR-YOL1-2026-09-03.md` §1/§2.

**Operatör kararları (2026-09-30 16:1xZ, AskUserQuestion):**
- **K-G3b-1 = birlikte yenile.** `--kapi-bot <ad>` bir botun kapı anahtarını değiştirdiğinde apisix, rapor ve sohbet kopyaları aynı turda yazılır.
- **K-G3b-2 = araç oluştursun.** `--tohumla-sohbet` yoksa oluşturur, varsa dokunmaz; değer ekrana, argv'ye ya da log'a düşmez.
- **K-G3b-3 = Rol-1 dener, engellenirse operatöre tek komut.** Vault'a ilk değer ve A1 tohumlaması bu kurala tabidir.
- **Sıra:** G4 main'e birleştikten SONRA. Telegram birimi ve v602 ancak o zaman main'de olur.

## Ölçülmüş zemin (2026-09-30 18:0x–18:2xZ; harita `scratchpad/g3b-harita.md` + A1 salt-okur)

- **DÜZELTME — `API_SERVER_KEY` profil kapsamlıdır.** A1 Hermes v0.19 kaynağında ölçüldü:
  - `gateway/platforms/api_server.py::_expected_api_key`: `/p/<profil>/…` isteği anahtarı `get_secret("API_SERVER_KEY")` ile o PROFİLİN kapsamından alır.
  - `agent/secret_scope.py::get_secret`: çoklu kipte kapsam yetkilidir, `os.environ`a düşmez.
  - Anahtar yoksa ya da <16 karakterse istek 401 (fail-closed) alır.
  - `meridian/bot_kanal.py::HermesTasiyici` her soruyu `/p/<bot>/v1/chat/completions`a gönderir.
  - Sonuç: G3 planındaki "`API_SERVER_KEY` yalnız kökün `.env`inde" tasarımı üç botu da 401'e düşürürdü. Anahtar TEK sırdır; DÖRT kopyası vardır: kök `.env` (dinleyici açılışı, `connect()` anahtarsız açmaz) ve üç sohbet profil `.env`i. Değer aynıdır; `HermesTasiyici` tek credential okur.
- **Hermes uçları.** `GET /health` kimlik doğrulamasızdır: `{"status":"ok"}` döner ve hazırlık yoklamasında kullanılır. `GET /health/detailed` ve `GET /v1/models` Bearer ister; yeni/eski anahtar kanıtında kullanılır. Varsayılan dinleyici `127.0.0.1:8642`.
- **A1 bugün:**
  - `/etc/meridian/bot_key_{bekci,karne,sef}`: VAR, root:root 0400, 48 bayt.
  - `/etc/hindsight/creds/HINDSIGHT_API_TENANT_API_KEY`: VAR, root:root 0400, 64 bayt.
  - `/etc/meridian/api_server_key`: YOK (yeni sır).
  - `/home/ubuntu/.hermes-botlar/`: YOK. G3'ün A0 görevleri canlıda henüz koşmadı; dağıtım #88 + site.yml kurar.
  - `meridian-botlar.service`, `meridian-telegram.service`: birim dosyası YOK, `inactive`.
  - Alan adları (değer değil): global `~/.hermes/.env` = `GEMINI_API_KEY OPENROUTER_API_KEY`; rapor profilleri = `OPENROUTER_API_KEY BOT_KEY_<AD>`. `API_SERVER_KEY` ve `HINDSIGHT_API_KEY` hiçbir mevcut hermes `.env`inde yok, dolayısıyla beyan-dışı tarama gürültü üretmez.
  - `ubuntu` grubu gid 1001.
- **Rotasyon aracı** (`sir_rotasyon.sh`, 3579 satır):
  - `_yaz_satir env` hedef dosya yoksa o satırda `die` eder. Önceki satırlar ve kasa zaten yazılmış olur: yarıda kalmış rotasyon.
  - `_yeniden_baslat` koşulsuz `systemctl restart` yapar.
  - `_sirala` `_BIRIM_SIRASI`nda olmayan birimi SESSİZCE düşürür.
  - `.env` oluşturan bir yardımcı işlem yok. Araçta `install -m 600 -o ubuntu` dosya deseni de yok.
  - `_dizin_hazirla` yoksa root sahipli dizin açar; hermes evinde yanlış olur.
- **`BOT_KEY_<AD>`** bugün hiçbir rotasyon satırında yok. Envanterdeki "rotasyon kanalıyla beslenir" beyanı ileriye dönüktü. Rapor profil `.env`i elle dolduruldu. APISIX `$env://` çözümünü yalnız açılışta yapar; `ExecReload` yok, restart gerekir.
- **Telegram birimi:** jeton ve sohbet kimliği `secrets.get` zincirinden gelir (`state/secrets.json`); yeni kanal gerekmez. `HermesTasiyici` `API_SERVER_KEY`i yalnız `credential_oku` ile okur. `bot_hafiza` `HINDSIGHT_API_TENANT_API_KEY`i `credential_oku` ile okur. Pano (`meridian.service`) `bota_sor` çağırmaz; pano birimine credential gerekmez.
- **A0:** `.hermes-botlar` kök/profil dizinleri `tasks/dizinler.yml`de 0700 ubuntu olarak kurulur. `.env`e A0 dokunmaz (v601 çivisi). `/etc/meridian` ve `/etc/hindsight/creds` dizinlerini A0 kurar, dosyaları Vault Agent render eder.
- **Hafıza:** A1 recall (18:2xZ, k=4) doğrudan benzer kayıt vermedi. Memory `hermes-v019-sohbet-yetenekleri` (çoklu kipte sırlar profil `.env`i) bu düzeltmeyle tutarlı.

## Global Constraints

- **Sır değeri hiçbir yerde görünmez.** argv, stdout/stderr, log, commit, test çıktısı, rapor dahil. Değer yalnız aracın 0700 işlik dizinindeki 0600 dosyalar ve STDIN üzerinden taşınır (mevcut desen: `py cikar … "$ISLIK/ref_<sır>"`, `vault kv put … value=-`). v447 B3/B4/D5 ve v557 `_sizinti` çivileri yeşil kalır.
- **Kabuk bash 3.2 uyumlu olmalı.** `${VAR^^}`, `mapfile`, `declare -A`, `readarray` YOK; büyük harf `tr a-z A-Z` ile yapılır. `set -e` altında `systemctl is-active` yalnız `if`/`||` içinde çağrılır (inactive = çıkış 3).
- **Tek-kaynak yasası.**
  - Bot listesi `deploy/ansible/roles/meridian_a1/defaults/main.yml::sohbet_profil_adlari` ve `deploy/hermes/sohbet/profiles/*` dizinleridir. Kabuk kopyası kaçınılmazsa v604'te iki yönlü eşitlik çivisi yazılır.
  - Tohumlamanın alan kümesi `_kopyalar()` tablosundan TÜRETİLİR. İkinci bir alan listesi yazılmaz.
  - Envanter `rotasyon_kopyalari` betik tablosunun aynasıdır (v447 A1/A2, v520 A3 sıra dahil).
- **Bot sayısından bağımsız tasarım (operatör 2026-09-30: kadroda 21 bot — 3 canlı + dalga 1/2/3).** Bot başına her tablo satırı ve eşleme TEK bot listesinden döngüyle türetilir. Kabukta tek liste sabiti `_SOHBET_BOTLARI` bulunur; v604 C3 onu `sohbet_profil_adlari` ve `deploy/hermes/kadro.yaml` içindeki `durum: aktif` botlarla iki yönlü eşitler. Envanter `rotasyon_kopyalari` aynası bot başına satır isterse iki yol var: satırları üreteç yazar (`--kontrol` çivisiyle) ya da ayna şemasına bot şablonu girer. v447 A1/A2 ve v520 A3'ü en az bozanı seçilir; uygulayıcı ölçer ve gerekçesini rapora yazar. Yeni bot = listeye bir ad + APISIX tüketicisi + kasa girdisi. Elle yazılan satır sayısı bot sayısıyla BÜYÜMEZ. Kasa girdisi (`vault_kv.bot_key_<ad>`) sır başına tek girdidir; bu doğal olarak bot başınadır.
- **Üretilmiş dosyalar elle düzenlenmez.** `deploy/vault/agent.hcl` ve `deploy/vault/policies/meridian-agent.hcl` yalnız `python ops/vault_politika_uret.py --uygula` ile üretilir. `docs/RUNBOOK.md` üretilmiştir: ajan ona DOKUNMAZ, Rol-1 birleştirmede yeniden üretir. `deploy/oracle-a1/RUNBOOK.md` elle yazılır.
- **Birimler etkinleştirilmez.** Botlar ve Telegram `etkin_birimler`e girmez; canlıda etkinleştirme G3c'dedir.
- **Yasa 4:** sinyalsiz `except`/`|| true` yasaktır; kaçış `# sessiz-yutma: <≥20 karakter gerekçe>` ile açıkça işaretlenir. **Yasa 6:** her yeni çıktı satırının okuyucusu (operatör reçetesi ya da çivi) vardır.
- **Kabuktaki çapa kuralı:** `.sh` ve `.py` şerhlerinde `dosya:NNN` satır çapası yok (v382); sembol çapası kullanılır.
- **Ajan kuralları.** Ajan A1'e ssh yapmaz ve sır içerebilecek dosya açmaz (`.env`, `state/secrets.json`, `backups/`, `/etc/...` kopyaları). pytest yalnız kendi worktree'sinde ve SERİ koşar: `env -u PYTHONDONTWRITEBYTECODE /Users/erdemozturk/AI-Trading/.venv/bin/python -m pytest …`, cwd = worktree. Test hükmü üçlüdür: grep boş + "N passed" + `PYTEST_EXIT`. Dosya yerinden kaldırılmaz (bisect yok). `git checkout --` ile geri alma yok; mutasyon geri alımı yedek kopyadan yapılır.

## Review Focus

1. **Etkin olmayan birim** (`inactive`, `failed`, yüklü değil) rotasyonda BAŞLATILMAZ.
   - Kuru raporda ve gerçek koşumda `ATLANDI (etkin değil: <durum>)` satırı basılır.
   - O birim için credential denetimi (`/run/credentials/<birim>`) ve hazırlık yoklaması istenmez; bu yüzden `olcum_yok` çıkış 2 OLMAZ.
   - Etkin birim ise restart + credential + hazırlık denetiminden geçer.
2. **Hedef `.env` yokken hiçbir yazım yapılmaz.** Alt komutun herhangi bir `env`/`dosya` kopya hedefi yoksa rotasyon, kasaya put, yedek, üretim ve ilk satır yazımı dahil HİÇBİR yazım yapmadan önce durur. Mesaj eksik yolları adlandırır ve `--tohumla-sohbet` önerir. Bugünkü "önceki satırlar yazıldı, sonra die" yarım hali kalmaz.
3. **`--kapi-bot bekci` yalnız bekçiyi değiştirir.** Yalnız `BOT_KEY_BEKCI` satırları değişir; öteki iki botun bütün kopyaları bayt-eşit kalır. Geçersiz ad kasaya ve dosyaya dokunmadan reddedilir: `meridian`, boş, `BEKCI`, `bekci/../sef`, `sef bekci`, eksik argüman, bilinmeyen bot.
4. **`--tohumla-sohbet` kuralları:**
   - Var olan dosyanın içeriğine, mtime'ına, modu ve sahibine dokunmaz. O dosyada eksik alan varsa ADIYLA raporlar ama yazmaz.
   - Yok olan dosyayı 0600 ubuntu:ubuntu olarak yazar. Alan kümesi yalnız tablonun o yola yazan satırlarıdır.
   - Herhangi bir referans (render hedefi) yoksa ya da boşsa HİÇBİR dosya yazmadan durur.
   - Hedef dizin yoksa durur; A0'nun işidir, araç dizin açmaz.
   - Değer çıktıda yoktur. İkinci koşum hiçbir şey yazmaz (idempotent).
5. **`API_SERVER_KEY`in dört kopyası AYNI değeri taşır.** Kök ve üç profil kopyası tek alt komutla birlikte döner. `HINDSIGHT_API_TENANT_API_KEY`in üç sohbet kopyası `--tenant` ile birlikte döner. Kopyalar arasında ayrışma kalırsa `--envanter` ve `--esitle` bunu yakalar: tablo güdümlü eşitlik yeni satırları da kapsar.

---

### Task 1: Rotasyon aracının güvenlik altyapısı (sırsız)

Yeni sır eklemeden önce aracı iki tehlikeye karşı kapatır:
- etkin olmayan birimi başlatmak ya da sessizce düşürmek;
- yarıda kalmış rotasyon.

Bu görev tablo satırı EKLEMEZ. Mevcut 24 satır aynen kalır.

**Files:**
- Modify: `deploy/oracle-a1/sir_rotasyon.sh` (`_BIRIM_SIRASI`, `_yeniden_baslat`, `_kuru_rapor`, `_hazir_uc`, yeni ön-denetim fonksiyonu ve çağrı noktaları)
- Modify: `tests/test_sir_rotasyon_v447.py` (`SIM_SYSTEMCTL` `is-active` modeli; varsayılan davranış MEVCUT birimler için "etkin")
- Create: `tests/test_bot_agi_sirlari_v604.py` (G3b çivileri — bu görevde Bölüm A)

**Interfaces:**
- Produces:
  - `_KOSULLU_BIRIMLER="meridian-botlar.service meridian-telegram.service"`: yalnız etkinse yeniden başlatılan birimler.
  - `_BIRIM_SIRASI` sonuna `meridian-botlar.service meridian-telegram.service`. Telegram `After=meridian-botlar.service` taşıdığı için sıra bu.
  - `_hedef_on_denetim <alt>`: alt komutun bütün kopya hedeflerini `sudo test -f` ile sınar. Eksik varsa her eksik yolu bir satırda adlandırır ve `die "… hedef dosya YOK — önce: sudo ./sir_rotasyon.sh --tohumla-sohbet"` eder. Tüm yollar varsa sessiz geçer.
  - `SIM_SYSTEMCTL` `is-active <birim>`: `.sahte/etkin_birimler` dosyası varsa içindeki birimler etkin; dosya yoksa `_KOSULLU_BIRIMLER` dışındaki her birim etkin, koşullu birimler `inactive` (A1 gerçeği).
- Consumes: mevcut `_yeniden_baslat`, `_kredensiyel_denetle`, `_hazir_bekle`, `_birimler`, `_kuru_rapor`, `vault_rotasyon`, `esitle` ve her alt komut fonksiyonunun yazım sırası.

- [ ] **Step 1: Failing çiviler (v604 Bölüm A).** Sahte ortam `tests/test_sir_rotasyon_v447.py::_sahte_ortam` ve koşum yardımcılarıyla (ithal et, kopyalama) şunları yaz:
  - `test_A1_birim_sirasi_kosullu_birimleri_tasir`: `_BIRIM_SIRASI` iki birimi içerir, botlar telegram'dan önce.
  - `test_A2_etkin_olmayan_kosullu_birim_baslatilmaz`: `_yeniden_baslat` doğrudan sınanabiliyorsa onunla sına, değilse Task 2 sonrasına ertele ve A2'yi Task 2'de yaz. Sahte `systemctl.log` koşullu birim için `restart` İÇERMEZ; stdout `ATLANDI (etkin değil: inactive)` içerir; çıkış kodu 0.
  - `test_A3_etkin_kosullu_birim_restart_ve_credential_denetimi`: `.sahte/etkin_birimler` ile etkin → `restart` log'da, credential denetimi istenir.
  - `test_A4_failed_durumu_adiyla_basilir`: sahte `is-active` `failed` → satırda `failed` geçer.
  - `test_A5_on_denetim_eksik_hedefte_HICBIR_yazim_yok`: mevcut bir alt komutun (`--tenant`) env hedefi sahte ortamda silinir. Koşum ≠0 döner. Sahte `vault` log'unda `kv put` YOK, yedek dizini oluşmamış, öteki hedeflerin sha256'sı değişmemiş, stderr eksik yolu ADIYLA ve `--tohumla-sohbet` önerisini içerir.
  - `test_A6_on_denetim_vault_kipinde_de_puttan_once`: `--tenant --vault` aynı iddialarla.
  - `test_A7_kuru_rapor_kosullu_birimi_bildirir`: `--tenant --kuru` çıktısı koşullu birimlerin "yalnız etkinse" notunu taşır (bedel yasası: atlanacağı ÖNCEDEN görünür).
  Çalıştır: `env -u PYTHONDONTWRITEBYTECODE …/python -m pytest tests/test_bot_agi_sirlari_v604.py -k "A1 or A5 or A6" > …log 2>&1; echo PYTEST_EXIT=$?` → **Expected:** FAIL (A1: birimler listede yok; A5/A6: bugün kasa put'u ya da ilk satır yazılıyor).
- [ ] **Step 2: Uygula.**
  - `_KOSULLU_BIRIMLER` ve `_BIRIM_SIRASI` eklemesini yap.
  - `_yeniden_baslat` içinde koşullu birim için `sudo systemctl is-active --quiet "$b"` denetle. Etkin değilse `sudo systemctl is-active "$b" || true` çıktısıyla (işaretli `# sessiz-yutma:` şerhi) durumu al, `ATLANDI (etkin değil: <durum>)` bas ve birimi restart, credential ve hazırlık kümelerinden çıkar.
  - `_negatif_restart_kurtarma` ve `_yeniden_baslat_sessiz` koşullu birimlere hiç dokunmuyorsa bunu çiviyle göster.
  - `_hedef_on_denetim`i her alt komutun ilk YAZIM işleminden önce çağır: `_yedek_al`, `_uret`, `vault_rotasyon`un put'u. En az dokunan tek noktayı ölç, ama bütün yazım yollarını kapsadığını çiviyle göster.
  - `esitle`nin mevcut "kopya YOK" durdurması korunur.
  - `_hazir_uc` botlar için `http://127.0.0.1:8642/health` (Hermes kimlik doğrulamasız sağlık ucu, ölçüldü). Telegram'ın ucu YOK; mevcut "hazırlık yoklaması YOK" güvenlik ağı kalır.
  - Başlık `# KULLANIM` bloğuna koşullu birim davranışını tek satırla ekle.
- [ ] **Step 3: Doğrula.** v604 Bölüm A + `tests/test_sir_rotasyon_v447.py tests/test_sir_referans_hizasi_v520.py tests/test_vault_dalga2_v491.py tests/test_vault_dalga1_baglama_v521.py tests/test_rotasyon_operator_mesajlari_v522.py tests/test_sir_uret_v557.py tests/test_sir_kasa_surum_v561.py tests/test_cp_*v556*.py` (adları `ls tests | grep -E "v55[6-9]|v53[8]"` ile ölç, uydurma) → **Expected:** hepsi PASS. v557, v561, v556 restart pinleri DEĞİŞMEZ: koşullu birimler sahte ortamda etkin değil.
- [ ] **Step 4: Mutasyonla ısır.** Her mutasyonu yedek kopyadan geri al (`cp` + sha256):
  - (M1) `is-active` denetimini kaldır → A2 kırmızı.
  - (M2) ön-denetimi put'tan sonraya taşı → A6 kırmızı.
  - (M3) `_BIRIM_SIRASI`ndan telegram'ı çıkar → A1 kırmızı.
  - (M4) `ATLANDI` satırını sil → A2 kırmızı.
- [ ] **Step 5: Commit.** `git add deploy/oracle-a1/sir_rotasyon.sh tests/test_sir_rotasyon_v447.py tests/test_bot_agi_sirlari_v604.py` → mesaj `G3b Task 1: rotasyon aracı koşullu birim (yalnız etkinse restart, ATLANDI satırı) + yazım öncesi hedef ön-denetimi (yarım rotasyon yok) + botlar /health hazırlık ucu; v604 A`.

### Task 2: `API_SERVER_KEY` zinciri + kiracı anahtarının sohbet kopyaları + credential drop-in'leri

Bu görev tek düğümdür; parçalanırsa ara commit'ler kırmızı olur. Birbirini zorlayan çiviler:
- v485 F2: envanter girdisi ile drop-in aynı commit'te olmalı.
- v447 P6: drop-in çiftleri ile `_kredensiyeller` tablosu birlikte değişmeli.
- v521 A3: tablodaki her sır kasaya bağlı olmalı.
- v491 A5: bağlı girdinin kopya kümesi tabloyla birebir olmalı.

**Files:**
- Modify: `docs/TASARIM-SIR-YOL1-2026-09-03.md` (§1 tablosuna iki satır, ÖNCE bu dosya — envanter başlığındaki sıra kuralı; "ÖLÇÜM GÜNCELLEMESİ" maddesi `D11` biçiminde, profil kapsamı ölçümü kaynaklı)
- Modify: `deploy/sir_envanteri.yaml`:
  - `dosyalar` +2: `~/.hermes-botlar/.env` (`API_SERVER_KEY`) ve `~/.hermes-botlar/profiles/<bekci,karne,sef>/.env` (`API_SERVER_KEY`, `HINDSIGHT_API_KEY`, `BOT_KEY_<AD>`), sınıf C, mod/sahip hedef beyanı `600`/`ubuntu`.
  - `vault_kv` yeni `api_server_key` girdisi: `vault_yolu: secret/meridian/api_server_key`, `hedef: /etc/meridian/api_server_key`, `mod: "0400"`, `sahip: root`, `rotasyon_siri: API_SERVER_KEY`, tek satır `tuketici` "LoadCredential" + `meridian-telegram.service` + dört `.env` kopyası.
  - `hindsight_cp_dataplane_api_key.kopya_kaynaklari` +3 sohbet env_satiri.
  - `rotasyon_kopyalari.kopyalar` aynası.
  - `olcum` notu.
- Modify: `deploy/oracle-a1/sir_rotasyon.sh`:
  - `_kopyalar`: yeni alt komut `api-sunucu`. İLK satır referans `dosya /etc/meridian/api_server_key`, ardından dört `env` satırı (kök + 3 profil, alan `API_SERVER_KEY`). `tenant` bloğuna üç sohbet `env` satırı (alan `HINDSIGHT_API_KEY`), mevcut referans satırından SONRA bitişik.
  - `_sir_birimleri`: `API_SERVER_KEY) echo "meridian-botlar.service meridian-telegram.service"`; `HINDSIGHT_API_TENANT_API_KEY` dalına iki koşullu birim.
  - `_kredensiyeller`: `tenant meridian-botlar.service HINDSIGHT_API_TENANT_API_KEY`, `tenant meridian-telegram.service HINDSIGHT_API_TENANT_API_KEY`, `api-sunucu meridian-telegram.service API_SERVER_KEY`.
  - `_taranan_dosyalar`: dört `.env`.
  - `_uret_sinifi`: `api-sunucu) hex` (tenant emsali; Hermes ≥16 kr ister, hex 64 kr).
  - `_deger_kaynagi_beyani`: `api-sunucu`.
  - Yeni `api_sunucu()` fonksiyonu (`tenant()` emsali; kanıt: botlar ETKİNSE `/health/detailed` yeni anahtarla 200 + eski anahtarla 401 `curl -K` 0600 cfg ile; etkin değilse `KANIT: ölçülemedi — meridian-botlar.service etkin değil (<durum>)` satırı ve çıkış 0).
  - Arg ayrıştırma, `KURU_ONERILIR`, `--esitle`/`--vault`/`--uret` metinleri ve dispatch güncellenir. Başlık KULLANIM'a `#   sudo ./sir_rotasyon.sh --api-sunucu …` satırı eklenir.
- Create: `deploy/oracle-a1/meridian-botlar.service.d/54-hafiza-credential.conf`. İçerik `deploy/oracle-a1/meridian.service.d/54-hafiza-credential.conf` ile AYNI çift ve aynı başlık şerhi deseni.
- Create: `deploy/oracle-a1/meridian-telegram.service.d/54-hafiza-credential.conf` (aynı çift) ve `deploy/oracle-a1/meridian-telegram.service.d/55-api-sunucu-credential.conf` (`LoadCredential=API_SERVER_KEY:/etc/meridian/api_server_key`).
- Modify: `deploy/oracle-a1/meridian-botlar.service`, `deploy/oracle-a1/meridian-telegram.service`: "CREDENTIAL BUGÜN YOK / G3b'ye ertelendi" şerhleri kanal açıklamasıyla değişir. Botlar `API_SERVER_KEY`i credential'dan DEĞİL `.env`den okur; bunun gerekçesi Hermes profil kapsamıdır.
- Modify: `deploy/ansible/roles/meridian_a1/defaults/main.yml`: `dropin_dizinleri` + `dropin_kaynaklari` iki birim. `izin_denetimli_sir_dosyalari`/`zorunlu_sir_dosyalari` DEĞİŞMEZ (Ruling G3b-R4).
- Regenerate: `deploy/vault/agent.hcl`, `deploy/vault/policies/meridian-agent.hcl` via `.venv/bin/python ops/vault_politika_uret.py --uygula`. Önce betiğin `meridian` ithal etmediğini `grep -n "^import\|^from" ops/vault_politika_uret.py` ile ölç; ithal ediyorsa KOŞMA, Rol-1'e bildir.
- Modify (test pinleri; sayıları UYDURMA, uygulamadan sonra say ve şerhe tarih + gerekçe yaz):
  - `tests/test_sir_rotasyon_v447.py`: `KOPYA_SAYISI`, `test_A0` alt kümesi, `test_A5` dosya sayısı, `test_E1` tenant tek-kopya çivisi. `test_E1`in adı ve iddiası yeni gerçeğe göre yeniden yazılır: referans tek, kopyalar dört. Ayrıca `_sahte_ortam` tohum dünyası: dört yeni `.env` + `etc/meridian/api_server_key` sahnede var. Kaldırıldıklarında ön-denetim çivisi (Task 1 A5) zaten öter.
  - `tests/test_sir_credential_v439.py` E0.
  - `tests/test_vault_dalga2_v491.py`: `AGENT_SABLON_SAYISI`; yeni `SOHBET_ENV_KOPYALARI` pini `HERMES_ENV_KOPYALARI` emsaliyle.
  - `tests/test_vault_dalga1_baglama_v521.py`: `BAGLI_TAM_KUME` + `API_SERVER_KEY`.
  - `tests/test_rotasyon_operator_mesajlari_v522.py`, `tests/test_sir_uret_v557.py`, `tests/test_sir_kasa_surum_v561.py`: alt komut kümeleri + `api-sunucu`; v561 `TENANT_BIRIMLER` geri alma metni birim listesi.
  - `tests/test_bot_agi_gecidi_v601.py` ve `tests/test_telegram_birimi_v602.py`: erteleme çivileri ÇEVRİLİR. Yeni ad `test_credential_G3b_drop_in_ciftleri`. İddia tam liste eşitliğidir: botlar = tek hafıza çifti, telegram = hafıza + api-sunucu. Kimlik adları `secrets.HAFIZA_KRED_ADI` ve envanter `hedef`ten türetilir; `credential_denetcisi_*` pozitif kontrolleri KALIR.
- Test: `tests/test_bot_agi_sirlari_v604.py` Bölüm B.

**Interfaces:**
- Consumes: Task 1 `_KOSULLU_BIRIMLER`, `_hedef_on_denetim`, `SIM_SYSTEMCTL is-active`.
- Produces: `_kopyalar` alt komutu `api-sunucu` (satırlar: referans `dosya /etc/meridian/api_server_key` + 4 env); tenant sohbet satırları; Task 3 ve 4'ün tüketeceği tablo biçimi. Tohumlama bu satırlardan türer: `/home/ubuntu/.hermes-botlar/` altına yazan her `env` satırı + sırrının referans satırı.

- [ ] **Step 1: Failing çiviler (v604 Bölüm B).**
  - `test_B1_API_SERVER_KEY_dort_kopya_ayni_sir`: `--kopyalar` çıktısında `API_SERVER_KEY`in referansı `dosya /etc/meridian/api_server_key` ve tam dört `env` satırı var (kök + `sohbet_profil_adlari`ndan türeyen üç profil). Liste YAML'dan okunur, kabuğa ikinci liste yazılmaz.
  - `test_B2_tenant_sohbet_kopyalari`: tenant bloğu üç sohbet `HINDSIGHT_API_KEY` satırı taşır, referans ilk.
  - `test_B3_api_sunucu_sahte_ortamda_doner`: `--api-sunucu --uret` (ya da emsalin istediği kip) sahte ortamda dört kopyayı AYNI yeni değerle yazar (sha256 eşit, eskiden farklı). Kök `.env`deki başka alanlar bayt-eşit kalır. Çıktıda değer yok (işlikteki değer dosyasının içeriği stdout/stderr'de aranır). Botlar etkin değil → `KANIT: ölçülemedi` satırı, çıkış 0.
  - `test_B4_api_sunucu_etkin_botlarda_kanit_ister`: `.sahte/etkin_birimler` ile → sahte curl'e `/health/detailed` iki çağrı (yeni/eski).
  - `test_B5_tenant_sohbet_kopyalarini_birlikte_dondurur`: `--tenant` sonrası üç sohbet `HINDSIGHT_API_KEY` = creds dosyasının yeni değeri.
  - `test_B6_telegram_ve_botlar_tenant_restart_yalniz_etkinse`: A2/A3'ün tenant yolu üzerinden tekrarı.
  - `test_B7_drop_in_icerigi_emsalle_ayni`: botlar/telegram `54-hafiza-credential.conf` `LoadCredential` satırı `meridian.service.d/54-hafiza-credential.conf` ile AYNI.
  - `test_B8_botlar_birimi_API_SERVER_KEY_credential_TASIMAZ`: gerekçe profil kapsamı; yanlış kanal kapanır.
  Çalıştır → **Expected:** FAIL.
- [ ] **Step 2: Uygula.** Önce spec §1 tablosu, sonra envanter (sıra kuralı). Ardından betik tablosu, haritalar, fonksiyon, drop-in'ler, A0 listeleri, üretilmiş HCL. En son pinleri SAYARAK güncelle.
- [ ] **Step 3: Doğrula.**
  - v604 A+B.
  - Task 1 Step 3 kümesi + `tests/test_sir_credential_v439.py tests/test_vault_faz2_v485.py tests/test_bot_agi_gecidi_v601.py tests/test_telegram_birimi_v602.py tests/test_ansible_a0_v451.py tests/test_birim_sertlestirme*v553*.py tests/test_telemetri_altyapi_v584.py tests/test_sir_denetimi*v565*.py`. Adları `ls tests | grep` ile ölç.
  - Tarama çivileri: `tests/test_codelaw*.py`, `tests/test_capa*v382*.py`, `tests/test_dagit_f9_beyan_v266.py`, `tests/test_ansible_dagit_v452.py`, `tests/test_filo*v348*.py`.
  - **Expected:** PASS. `ops/vault_politika_uret.py --kontrol` çıkış 0.
- [ ] **Step 4: Mutasyonla ısır.**
  - (M1) Bir profil kopyasını tablodan sil → B1 + v447 A1 kırmızı.
  - (M2) Botlar birimine `API_SERVER_KEY` LoadCredential ekle → B8 kırmızı.
  - (M3) `_kredensiyeller`den telegram api-sunucu satırını sil → v447 P6 kırmızı.
  - (M4) envanter `api_server_key.tuketici`den "LoadCredential" kelimesini çıkar → v485 F2 kırmızı.
  - (M5) kopyalardan birine farklı değer yazan bir hata sok (ör. `sadece_sir` süzgecini boz) → B3 kırmızı.
- [ ] **Step 5: Commit.** Açık yollarla `git add` → mesaj `G3b Task 2: API_SERVER_KEY (kasa + 4 kopya: kök + 3 sohbet profili — Hermes profil kapsamı ölçümü) + --api-sunucu, tenant sohbet kopyaları, botlar/telegram credential drop-in'leri, A0 drop-in listeleri, agent.hcl/politika üretildi; v604 B + pinler`.

### Task 3: `--kapi-bot <ad>` — bir botun kapı anahtarı tüm kopyalarıyla birlikte döner

**Files:**
- Modify: `deploy/oracle-a1/sir_rotasyon.sh`:
  - Arg ayrıştırma `--kapi-bot <ad>`. İki jeton; `for _a in "$@"` yerine gereken en az değişiklikle ön-geçiş ya da `while/shift`. Mevcut bütün bayrak davranışı çivilerle aynı kalır.
  - İç alt adı `kapi-bot-<ad>` (Ruling G3b-R2).
  - `_kopyalar`: her bot için bitişik blok. Referans `dosya /etc/meridian/bot_key_<ad>`, ardından `env /opt/apisix/.env-apisix BOT_KEY_<AD>`, `env /home/ubuntu/.hermes/profiles/<ad>/.env BOT_KEY_<AD>`, `env /home/ubuntu/.hermes-botlar/profiles/<ad>/.env BOT_KEY_<AD>`.
  - `_sir_birimleri BOT_KEY_<AD>`: `apisix.service meridian-botlar.service`. Motor `BOT_KEY_<AD>` kullanmaz, meridian.service yeniden başlamaz. Rapor botları timer'lı oneshot'tur ve `.env`i her koşuda okur.
  - `_uret_sinifi kapi-bot-*`: `b64`, `kapi` emsali; mevcut değerler 48 kr.
  - Alt komut fonksiyonları.
  - Kanıt: `kapi()` emsali — kapı ucunda yeni anahtar 200, eski 401. Botlar etkinse ek olarak botlar `/health`.
  - Başlık KULLANIM `#   sudo ./sir_rotasyon.sh --kapi-bot <bekci|karne|sef> …`.
- Modify: `deploy/sir_envanteri.yaml`: `bot_key_<ad>` üç girdisi.
  - `rotasyon_siri: BOT_KEY_<AD>`.
  - `kaynak` → render hedefi `dosya /etc/meridian/bot_key_<ad>` (emsal `hindsight_cp_access_key`, 2026-09-26).
  - `kopya_kaynaklari` = `.env-apisix` + rapor `.env` + sohbet `.env`.
  - `tuketici` metni gerçeğe çekilir: "ROTASYON KANALIYLA beslenir" artık DOĞRU.
  - `rotasyon_kopyalari` aynası.
- Modify: pinler — v447 `KOPYA_SAYISI`/A0, v521 `BAGLI_TAM_KUME` + üç `BOT_KEY_<AD>`, v522/v557/v561 alt komut kümeleri (üç yeni iç alt ad), v491 (A5 yeşil kalır; yeni `SOHBET_ENV_KOPYALARI` pini BOT_KEY sohbet kopyalarını da kapsar).
- Test: v604 Bölüm C.

**Interfaces:**
- Consumes: Task 1 koşullu birim + ön-denetim; Task 2 tablo/sahne düzeni.
- Produces: `--kapi-bot <ad>` CLI; iç alt adlar `kapi-bot-bekci|kapi-bot-karne|kapi-bot-sef`; tohumlamanın `BOT_KEY_<AD>` sohbet satırları.

- [ ] **Step 1: Failing çiviler (v604 Bölüm C).**
  - `test_C1_kapi_bot_yalniz_kendi_botunu_dondurur`: `--kapi-bot bekci --uret` → `BOT_KEY_BEKCI` dört kopyası aynı yeni değer. `BOT_KEY_KARNE`/`BOT_KEY_SEF` satırları ve dosyaları bayt-eşit (sha256), `.env-apisix`in öteki satırları bayt-eşit. Değer çıktıda yok.
  - `test_C2_gecersiz_bot_adi_hicbir_sey_yazmadan_reddedilir`: parametreli `["", "meridian", "BEKCI", "bekci/../sef", "sef bekci", "yok", "--kuru"]` + argümansız `--kapi-bot`. Çıkış ≠0, sahte vault/systemctl/yedek dokunulmamış, bütün hedeflerin sha256'sı aynı.
  - `test_C3_bot_listesi_tek_kaynaktan`: kabuktaki bot kümesi == `sohbet_profil_adlari` == `deploy/hermes/sohbet/profiles/*` dizinleri. Kabuk listesi yoksa ve tablo satırlarından türüyorsa bu çivi tablo satırlarının bot kümesini sınar.
  - `test_C4_kapi_bot_apisix_restart_botlar_yalniz_etkinse`: restart log'unda `apisix.service` var, `meridian.service` YOK. Botlar etkin değilse ATLANDI.
  - `test_C5_BOT_KEY_baglari_tabloyla_birebir`: envanter `bot_key_<ad>` `kaynak ∪ kopya_kaynaklari` == tablo satırları. v491 A5 bunu kapsıyorsa C5, A5'e işaret eden pozitif kontrol olarak kalır.
  Çalıştır → **Expected:** FAIL.
- [ ] **Step 2: Uygula** (yukarıdaki dosyalar).
- [ ] **Step 3: Doğrula.** Task 2 Step 3 kümesi + v604 A–C → **Expected:** PASS.
- [ ] **Step 4: Mutasyonla ısır.**
  - (M1) Bir botun sohbet satırını başka botun `.env`ine yönelt → C1 + A5 kırmızı.
  - (M2) ad doğrulamasını gevşet (`*` kabul) → C2 kırmızı.
  - (M3) `_sir_birimleri BOT_KEY_*`e `meridian.service` ekle → C4 kırmızı.
- [ ] **Step 5: Commit.** Mesaj `G3b Task 3: --kapi-bot <ad> (operatör K-G3b-1: apisix + rapor + sohbet kopyaları birlikte; iç alt ad kapi-bot-<ad>, bot listesi tek kaynak), bot_key_<ad> rotasyon bağı (referans render hedefi); v604 C + pinler`.

### Task 4: `--tohumla-sohbet` — tablodan türeyen, değersiz, idempotent ilk yazım

**Files:**
- Modify: `deploy/oracle-a1/sir_rotasyon.sh`:
  - Yeni `tohumla_sohbet()`.
  - Yeni yardımcı işlem `tohumla-env` (gömülü `yardimci.py`): `<hedef> <mod> <sahip> <grup>`, ardından `<alan> <değer-dosyası>` çiftleri.
  - Arg ayrıştırma `--tohumla-sohbet` (+ `--kuru` desteği, `KURU_ONERILIR`).
  - Başlık KULLANIM satırı + "sıra" uyarısı: tohumlama site.yml'den SONRA, ilk rotasyondan ÖNCE.
- Test: v604 Bölüm D.

**Interfaces:**
- Consumes: Task 2–3 tablo satırları. Hedef kümesi = `/home/ubuntu/.hermes-botlar/` altına yazan `env` satırları; değer kaynağı = her sırrın tablodaki referans satırı (`py cikar` deseni, `esitle()` emsali).
- Produces: `sudo ./sir_rotasyon.sh --tohumla-sohbet [--kuru]`.

Davranış (Review Focus 4):
1. Root kapısı + işlik (mevcut).
2. Hedefleri ve alan kümelerini TABLODAN türet (yol → alanlar).
3. Her hedefin dizini `sudo test -d`. Biri yoksa HİÇBİR şey yazmadan dur: "dizin YOK: <yol> — önce A0 site.yml".
4. Her gerekli sırrın referansını işliğe çıkar. Biri yok ya da boşsa hiçbir şey yazmadan dur: "referans YOK: <yol> — önce Vault'a değer + Agent render (RUNBOOK)". Değer basılmaz.
5. `--kuru`: her hedef için `VAR (alanlar tam | eksik: A, B)` ya da `YOK — yazılacak alanlar: …`, her referans için `VAR/YOK`; sıfır yazım, çıkış 0.
6. Gerçek koşum:
   - YOK olan hedef `tohumla-env` ile yazılır: 0600, sahip `ubuntu`, grup `ubuntu`, `KEY=değer` satırları, `_atomik_yaz` (aynı dizinde mkstemp + chmod + chown + `os.replace`).
   - VAR olan hedefe dokunulmaz; eksik alan varsa ADIYLA raporlanır.
   - Sonda özet: `yazıldı N · dokunulmadı M · eksik alanlı K`.
   - Eksik alanlı dosya varsa çıkış 3; operatör reçetesi o durumda elle inceleme ister.
7. Restart YOK: birimler etkin değil, tohumlama G3c'den önce.
8. `tohumla-env` yardımcısı hedef VARSA yazmayı reddeder: `O_EXCL`/`os.link` ya da `os.replace` öncesi yeniden `exists` denetimi ile yarış kapanır; ikinci savunma katmanıdır.

- [ ] **Step 1: Failing çiviler (v604 Bölüm D).**
  - `test_D1_yok_olan_dosyalar_0600_ubuntu_ile_yazilir`: sahte ortamda sohbet `.env`ler yok, referanslar var. Dört dosya oluşur, alan kümeleri tablodan türeyen küme ile birebir, değerler referanslarla eşit. Mod/sahip çağrısı sahte chown/`os.stat` ile ölçülür; çivi makinesinde ubuntu yoksa mevcut işaretli emsale uy.
  - `test_D2_var_olan_dosyaya_dokunulmaz`: bir dosya önceden var ve farklı içerikte. sha256, mtime_ns, mod aynı kalır; çıktı `dokunulmadı`.
  - `test_D3_var_olan_dosyada_eksik_alan_raporlanir_yazilmaz`: çıkış 3, alan adı çıktıda, dosya bayt-eşit.
  - `test_D4_referans_yoksa_hicbir_dosya_yazilmaz`: `etc/meridian/api_server_key` sahneden kaldırılır. Çıkış ≠0, hiçbir sohbet `.env`i oluşmamış, mesaj yolu adlandırır.
  - `test_D5_dizin_yoksa_durur`.
  - `test_D6_ikinci_kosum_hicbir_sey_yazmaz`: sha256 + mtime.
  - `test_D7_deger_hicbir_ciktida_yok`: stdout, stderr ve sahte komut log'larında (argv) referans değerleri aranır.
  - `test_D8_kuru_sifir_yazim`.
  - `test_D9_alan_kumesi_tablodan_turetilir`: tabloya sahte bir sohbet satırı ekleyen geçici betik kopyası (worktree dışı, `tmp_path`) → tohumlama o alanı da yazar. İkinci liste olmadığının kanıtı.
  - `test_D10_tohumla_env_yardimcisi_var_olan_hedefi_reddeder`: yardımcıyı doğrudan çağır.
  Çalıştır → **Expected:** FAIL.
- [ ] **Step 2: Uygula.**
- [ ] **Step 3: Doğrula.** Task 3 Step 3 kümesi + v604 A–D → **Expected:** PASS.
- [ ] **Step 4: Mutasyonla ısır.**
  - (M1) "VAR ise dokunma" dalını kaldır → D2 kırmızı.
  - (M2) referans denetimini yazımdan sonraya taşı → D4 kırmızı.
  - (M3) mod 0644 → D1 kırmızı.
  - (M4) alan kümesini sabit listeye çevir → D9 kırmızı.
  - (M5) değeri argv ile geçir → D7 kırmızı.
- [ ] **Step 5: Commit.** Mesaj `G3b Task 4: --tohumla-sohbet (operatör K-G3b-2: tablodan türeyen alan kümesi, yoksa 0600 ubuntu yaz, varsa dokunma + eksik alanı söyle, referans/dizin yoksa hiç yazma, değer çıktıya düşmez); v604 D`.

### Task 5: Canlı reçete (elle RUNBOOK) + bağlam belgeleri

**Files:**
- Modify: `deploy/oracle-a1/RUNBOOK.md` (ELLE yazılı; `docs/RUNBOOK.md` DEĞİL). Yeni bölüm "Bot ağ geçidi sırları (G3b)", telemetri/Grafana bölümü emsaliyle. Sıra ve her adımın DEĞER BASMAYAN doğrulaması:
  1. Dağıtım (Rol-1) + `ansible-playbook … site.yml`. Kurulanlar: `.hermes-botlar` dizinleri, drop-in'ler, botlar/telegram birim dosyaları (etkin değil). Doğrulama `stat` + `systemctl is-enabled` → `disabled`.
  2. Vault politikası: `vault policy write meridian-agent deploy/vault/policies/meridian-agent.hcl` (admin jetonu; Rol-1 dener, engellenirse operatör).
  3. İlk değer (değer görünmez, boru): `openssl rand -hex 32 | tr -d '\n' | vault kv put secret/meridian/api_server_key value=-`. Doğrulama `vault kv metadata get` sürüm 1 (değer yok).
  4. `agent.hcl` kurulumu + `systemctl restart vault-agent` → doğrulama `sudo stat -c '%U:%G %a %s' /etc/meridian/api_server_key` (root:root 400 64).
  5. `sudo ./sir_rotasyon.sh --tohumla-sohbet --kuru`, ardından gerçek koşum. Doğrulama: `stat` 600 ubuntu + alan ADLARI (`grep -o '^[A-Z_]*='`).
  6. Ancak bundan sonra rotasyon alt komutları. Tohumlamadan önce `--tenant` koşulursa ön-denetim durdurur (Task 1).
  7. G3c test-ateşlemesi (G3 planı listesi).
  Geri alma: yeni `.env`leri `sudo mv` ile yedek dizinine taşı (silme yok); drop-in'ler etkin olmayan birimde zararsız.
- ~~G3 planı G3c satırı~~ — Rol-1 2026-09-30 18:4xZ ekledi (G3c 4b, G4 dal sonu I-1 ile birlikte); bu görevde YAPILMAZ.

- [ ] **Step 1:** RUNBOOK bölümünü yaz. Her komut ssh sarmalı ya da "A1'de" başlıklı olur, değer basan komut içermez.
- [ ] **Step 2:** Doğrula: `tests/test_uiux_s1b_v154.py` (üretilmiş RUNBOOK bekçisi) kırmızıysa bu beklenen durumdur. Başlık değişti; `docs/RUNBOOK.md`i Rol-1 üretir. Raporda "v154 kırmızı — Rol-1 `ops/runbook_uret.py` üretecek" diye beyan et, ajan düzeltmeye kalkmaz. Öteki kapsam: Task 4 kümesi → PASS.
- [ ] **Step 3: Commit.** Mesaj `G3b Task 5: canlı reçete (deploy/oracle-a1/RUNBOOK.md — site.yml → politika → ilk değer boruyla → agent render → tohumla → rotasyon; değersiz doğrulamalar) + G3c profil-kapsamı kontrol satırı`.

## Rol-1 kararları (Ruling)

- **G3b-R1 — `API_SERVER_KEY` dört kopya, tek sır.** Ölçüm: Hermes profil kapsamı ve fail-closed davranışı. Bot başına ayrı anahtar reddedildi: `HermesTasiyici` tek credential okur ve bütün botlar aynı süreçte koşar, ayrı anahtar yalıtım getirmez. Yanlışsa bedeli dört satırın bota bölünmesidir; veri kaybı yok.
- **G3b-R2 — `--kapi-bot` iç modeli: bot başına iç alt ad `kapi-bot-<ad>`.** Tablo güdümlü makine (`_birimler`, `_alt_sirlari`, `_yedek_al`, `_kuru_rapor`, `_envanter_esitlik`) süzgeçsiz doğru çalışır. Tek alt komut + bot süzgeci üç ayrı fonksiyona süzgeç ister; unutulan bir süzgeç üç botun anahtarını birden döndürür. Bedeli üç ince fonksiyon ve v557 ad kuralı uyumudur.
- **G3b-R3 — `bot_key_<ad>` referansı render hedefi** (`/etc/meridian/bot_key_<ad>`, emsal `hindsight_cp_access_key`). Bedel: `vault_sir_koy.sh` bot anahtarlarını `.env-apisix`ten tohumlayamaz. Kasa 2026-09-14'ten beri dolu, render hedefleri ölçüldü; betik yeniden koşulmaz.
- **G3b-R4 — `api_server_key` A0 izin denetimi listesine GİRMEZ.** Birimler etkin değil; render kanıtı RUNBOOK adım 4'te `stat` ile. Listeye eklemek v584 F1'in rotasyon-dışı küme bağını zorlar. Bedeli, dosya izni kayarsa A0'nun uyarmamasıdır; `_kredensiyel_denetle` birim etkinleşince zaten ölçer.
- **G3b-R5 — `api-sunucu` üretim sınıfı `hex` (64 kr).** Hermes ≥16 kr ve yer tutucu olmayan değer ister (`has_usable_secret`); tenant emsali.
- **G3b-R6 — İlk kasa değeri araçla değil RUNBOOK borusuyla konur** (grafana emsali). Araca "ilk kurulum" istisnası eklemek güvenlik aracında dallanma demektir; ön-denetim değişmezi ("hedef yoksa hiç yazma") istisnasız kalır.
