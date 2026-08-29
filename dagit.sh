#!/usr/bin/env bash
# dagit.sh — Meridian GENEL dağıtım betiği (WP-H/H2 kapılı). Tek-seferlik gece betiklerinin
# (dagitim_gece*.sh) yerine standart yol: her dağıtım BU sırayla geçer.
#   [0] uv audit (tedarik-zinciri kapısı — kırmızıysa DAĞITIM YOK)
#   [0c] lint-imports (mimari sözleşmeler — WP-H/H4; kırmızıysa DAĞITIM YOK)
#   [0d] import taraması (dev-grubu daraltması hâlâ güvenli mi — WP-H; kırmızıysa DAĞITIM YOK)
#   [1] rsync DRY-RUN (ne değişecek göster; yarım-iş/mtime tuzağına karşı GÖZLE onay)
#   [1b] versiyonlu state farkı (goal.yaml + bounds.yaml canlı↔repo; kuru koşumda YALNIZ diff)
#   [F9] dagit-kapsamı-dışı canlı artefaktlar (sprint@ birimi · polkit kuralı · SOUL.md ·
#        hermes config.yaml · tick-watchdog service+timer · litestream.yml · aylık-bucket-kopya
#        service+timer · brifing service+timer · @sef profili: distribution.yaml+config.yaml+SOUL.md):
#        içerik kapısı — sürüklenmeyi RAPORLAR, engellemez
#   [2] rsync (state/backups/.venv/.git HARİÇ)
#   [3] uv sync --frozen (dev grubu HARİÇ — [0d]'nin hükmüne dayanır)
#   [4] bakım penceresi: durdur → versiyonlu state kopyası ([1b] KOPYALA dediyse) → başlat
#   [5] doğrulama: servisler active + healthz 200 + son olay yaşı
#   [B] dağıtım-beyanı: canlıya state/dagitim.json (deployed_sha + damga — P0-b, ortamlar-arası #2)
# Kullanım: ./dagit.sh            → dry-run'a kadar gider, ONAY İSTER
#           ./dagit.sh --uygula   → tam dağıtım
#
# SÜRÜM TERFİSİ SÖZLEŞMESİ (WP5-B; bu başlık tek kaynak — RUNBOOK üreticisi kapsamına alınması
# ayrı karar [B-RUNBOOK-KAPSAM]): canlıya yeni sürüm YALNIZ bu betikle çıkar; `git push` dağıtım
# DEĞİLDİR (cloud görünürlüğü). Dağıtılan tepe [0a]'da DAGIT_SHA olarak donar ve [B] beyanına
# yazılır. GERİ ALMA: önceki commit'e dönüp (`git checkout <sha>`) aynı akışı koşmak — state'e
# dokunulmaz; [1b] kopyası yalnız onayla yapıldığından goal/bounds geri-alması da aynı kapıdan.
# ÖLÇÜM 2026-08-23: git-izli state YALNIZ goal.yaml+bounds.yaml (`git ls-files state/`) — ayrı bir
# "versiyonlu-state adımı" bilerek YOK, [1b] kapsıyor.
set -euo pipefail
KEY="$HOME/.ssh/oci-a1.key"; IP="130.61.126.87"; REPO="$HOME/AI-Trading"
SSH=(ssh -i "$KEY" -o ConnectTimeout=15 ubuntu@"$IP")
RSYNC_EXC=(--exclude '.venv' --exclude '.git' --exclude 'state' --exclude 'backups' --exclude '/var' --exclude 'scratchpad' --exclude 'scratch-*' --exclude '.superpowers' --exclude '__pycache__' --exclude '.claude' --exclude '.hypothesis' --exclude 'mutants' --exclude '.pytest_cache' --exclude '.env' --exclude '.dash.env' --exclude '.agents' --exclude '.codex' --exclude '.github' --exclude 'skills-lock.json' --exclude '.impeccable' --exclude '.import_linter_cache' --exclude 'research/olcumler/*/seanslar.json' --exclude 'research/olcumler/*/run.stderr.log' --exclude 'research/olcumler/*/state' --exclude 'node_modules' --exclude 'ui/node_modules' --exclude '/ui')  # + DERLEME SINIFI (2026-08-24, shadcn pilotu): `npm install` on binlerce dosya yazar ve rsync onları .gitignore'a BAKMADAN taşır — `scratch-panov2` vakasının aynısı, iki mekanizma AYRI. Canlıya giden ARTEFAKT'tır (`meridian/web/pilot-*`), kaynak DEĞİL: `/ui` altındaki TSX/config canlıda okuyucusuzdur (YASA 6). `/ui` ANKORLU — `meridian/web/ui/` gibi bir alt yol yanlışlıkla düşmesin.  # + ÖLÇÜM HAM ÇIKTILARI (2026-08-10, ROADMAP §2 madde-1): .gitignore rsync'i ETKİLEMEZ — ham seans dökümü/betik-state/stderr yeniden-üretilebilir (olcum*.py deterministik), canlıda okuyucusu yok; özet sonuc.json + olcum*.py TAŞINIR  # + HARNESS ARTEFAKTLARI (2026-08-06): worktree-oturum kalıntıları dagit'i dry-run'da boğdu  # + ARAÇ ÖNBELLEKLERİ (2026-08-07): .impeccable/hook.cache.json (kökte VE meridian/web/ altında) ile .import_linter_cache/ kuru koşumda göründü — 306ab56'nın hükmü bunları kapsamıyordu. İkisi de araç katmanı: canlıda karşılığı yok, hiçbir test okumuyor, ama tool-layer sızıntısı aynı sınıf.  # SIR SINIFI (2026-08-01 vakası): rsync --delete A1-yerel .dash.env'i SİLDİ — sırlar dağıtıma binmez, kanal push_secret.sh  # + SCRATCH SINIFI (2026-08-24 vakası): `scratch-panov2/` kuru koşumda 5 girdiyle CANLIYA GİDİYORDU. Yerelde .gitignore'lu ama RSYNC GITIGNORE OKUMAZ, yalnız bu listeyi okur — iki mekanizma ayrı ve birini kapatmak ötekini kapatmaz. `scratchpad` zaten listedeydi; `scratch-*` globu sınıfı kapatır.  # + BOT KUM HAVUZU SINIFI (2026-08-29): `/var` — botların TEK yazılabilir dizini (`var/bots/<ad>`, spec §9.3 safe-root). Depoda YOK, canlıda VAR: dışlanmasaydı `--delete` her dağıtımda botun biriktirdiği her şeyi SİLERDİ — `state`/`backups` ile BİREBİR aynı sınıf (canlı-sahipli, repo-sahipli değil). ANKORLU (`/var`, `/ui` gibi): ileride bir `ui/src/var/` doğarsa onu sessizce dağıtım dışı bırakmasın.

echo "=== [0a/5] git temiz-ağaç kapısı ==="
cd "$REPO"
KIRLI_GEC=false   # dağıtım-beyanına ([B]) yazılır: true = istisna GERÇEKTEN kullanıldı (bayrak
                  # temiz ağaçla verilmişse istisna işlememiştir ve beyan false kalır)
if [[ -n "$(git status --porcelain)" ]]; then
  if [[ "${2:-}" == "--kirli-gec" || "${1:-}" == "--kirli-gec" ]]; then
    echo "  ⚠ KİRLİ AĞAÇLA dağıtım (bilinçli --kirli-gec)"; git status --short | head -10
    KIRLI_GEC=true
  else
    echo "!! Çalışma ağacı KİRLİ — önce commit'le (yarım-iş canlıya gitmesin)."
    echo "   Bilinçli istisna için: ./dagit.sh --uygula --kirli-gec"; git status --short | head -15; exit 1
  fi
fi
echo "  ✓ dağıtılacak commit: $(git rev-parse --short HEAD) — $(git log -1 --format=%s | head -c 60)"
# BEYAN İÇİN BURADA DONDURULUR ([B] adımında değil): 660dc10 dersi — paralel oturum trafiği ana
# checkout'u dağıtım SIRASINDA taşıyabilir; beyan "dağıtımın kapılardan geçtiği andaki tepe"yi
# söylemeli, betiğin bittiği andakini değil.
DAGIT_SHA="$(git rev-parse HEAD)"

echo "=== [0b/5] uv audit (tedarik-zinciri kapısı) ==="
uv audit --preview-features audit-command || { echo "!! AUDIT KIRMIZI — dağıtım İPTAL"; exit 1; }

# [0c] MİMARİ SÖZLEŞMELER (WP-H/H4, 2026-07-31). Neden DAĞITIM kapısı: bu sözleşmelerin ihlali
# derleme hatası vermez, test kırmazsa görünmez ve canlıya SESSİZCE gider. En pahalı hâli döngüsel
# import'tur — süreç AÇILIRKEN patlar, yani arıza dağıtımdan dakikalar sonra, bakım penceresi
# kapandıktan sonra ortaya çıkar. 2 saniyelik bir kapı, o gecenin tamamını kurtarır.
# `uv run` KULLANILIR (çıplak `lint-imports` değil): dev bağımlılığı yalnız proje ortamındadır ve
# çıplak çağrı, aracın kurulu OLMADIĞI bir kabukta "command not found" ile — yani kapı hiç
# koşmadan — geçilmiş sayılırdı.
echo "=== [0c/5] lint-imports (mimari sözleşme kapısı) ==="
uv run lint-imports || {
  echo "!! MİMARİ SÖZLEŞME KIRILDI — dağıtım İPTAL."
  echo "   Sözleşmeler: pyproject.toml [tool.importlinter]. İstisna eklemek bir borç kaydıdır."
  exit 1
}

# [0d] DEV-DARALTMASI HÂLÂ GÜVENLİ Mİ? (WP-H, 2026-08-03). Adım [3] A1'e dev grubunu KURMAZ.
# Bu daraltmanın tek dayanağı "çalışma yolunda sıfır dev-import" iddiasıydı ve o iddia bir kez,
# elle, KAYITSIZ ölçülmüştü. Yarın `meridian/` içine bir `import hypothesis` girerse daraltma
# canlıyı SESSİZCE düşürür — üstelik testler YEŞİL kalır (yerelde paket KURULUDUR), arıza yalnız
# A1'de, süreç açılırken, bakım penceresi kapandıktan sonra görünür. Tam olarak [0c]'nin kapattığı
# sınıf, başka bir kapıdan. Ölçüm ucuz (~1 sn) ve HÜKMÜ makine verir.
# ÇIKIŞ KODU SÖZLEŞMESİ: 0 = daraltma güvenli · 1 = dev paketi çalışma yolunda · 2 = ölçülemedi.
# 2 de ENGELDİR: ölçülemeyen daraltma 'güvenli' sayılmaz (fail-closed — bu depodaki genel yasa).
echo "=== [0d/5] import taraması (dev-grubu daraltma kapısı) ==="
uv run python ops/import_tarama.py --sessiz || {
  echo "!! DEV-DARALTMASI ARTIK GÜVENLİ DEĞİL — dağıtım İPTAL."
  echo "   Tam rapor: uv run python ops/import_tarama.py"
  echo "   Ya import'u çalışma yolundan çıkar, ya paketi ANA bağımlılığa taşı (ikisi de bilinçli)."
  exit 1
}

echo "=== [1/5] rsync DRY-RUN ==="
# SIGPIPE SINIFI (2026-08-12 vakası): eski hali `rsync … | head -40` idi — liste 40 satırı AŞINCA
# head boruyu erken kapatır, rsync SIGPIPE/rc-20 ile ölür ve `set -o pipefail` dağıtımı [1]'de
# sessizce düşürür. Kusur ancak tarihin en uzun transfer listesinde göründü (v237 turu: 81 ölçüm
# artefaktı + kartlar). Tampon dosya rsync'in GERÇEK çıkış kodunu korur; head canlı boruya değil
# dosyaya bakar — gerçek rsync hataları (23/24/12…) eskisi gibi dağıtımı durdurur.
DRY_TMP="$(mktemp)"
rsync -azin --delete "${RSYNC_EXC[@]}" -e "ssh -i $KEY" "$REPO"/ ubuntu@"$IP":/opt/meridian/ > "$DRY_TMP"
head -40 "$DRY_TMP"
_dry_n="$(wc -l < "$DRY_TMP" | tr -d ' ')"
rm -f "$DRY_TMP"
echo "--- (yukarısı ilk 40 satır; toplam $_dry_n satır; boşsa fark yok) ---"

# =================================================================================================
# [1b] VERSİYONLU STATE DOSYALARI — canlı ↔ repo farkı (2026-08-02)
# =================================================================================================
# NEDEN VAR — CANLI VAKA, sınıf: "doğru dışlama, yanlış kapsam". `state/` rsync'ten HARİÇTİR ve bu
# DOĞRUDUR (canlı defter dağıtımla ezilemez). Ama `state/` altında iki dosya defter değil
# YAPILANDIRMADIR ve c783442'den beri VERSİYONDADIR: `goal.yaml` + `bounds.yaml`. Dışlama onları da
# kapsayınca repo ile canlı SESSİZCE ayrıştı:
#   2026-08-01'de `entry.w_turnover` bounds'a indi (kart EDG-2026-016, hüküm SUCCESS) — A1'e HİÇ
#   GİTMEDİ. Makine o düğmeyi canlıda HİÇ ÖRNEKLEMEDİ. "Sıfır örnekleme"nin İKİNCİ kök nedeni
#   budur; birincisi (emekli `spy_sma_gate` satırının arama uzayını işgal etmesi) aynı gün bulundu.
#   İkisi birbirinin aynası: biri hükümsüz bir ekseni örnekletiyordu, diğeri gerçek bir ekseni hiç
#   doğurmuyordu. Bir dağıtım betiğinin taşıdığını sandığı ama taşımadığı şey, taşımadığını bildiği
#   şeyden tehlikelidir.
#
# YASA — İKİ DALLI, ÇÜNKÜ SSoT TEK YÖNLÜ DEĞİL: repo bu iki dosyanın kaynağıdır, AMA canlı taraf
# elle değiştirilmiş olabilir (operatör kalemi) ve o değişiklik SESSİZCE EZİLEMEZ.
#   * canlıda REPO-DIŞI anahtar YOK  → fark repo'nun ilerlemesidir → bakım penceresinde kopyala.
#   * canlıda REPO-DIŞI anahtar VAR  → KOPYALAMA. Kırmızı uyarı bas, hükmü operatöre bırak.
# AYRIM ANAHTAR DÜZEYİNDE, HAM SATIR DÜZEYİNDE DEĞİL: bu dosyalar yorum ağırlıklıdır (mezar taşları,
# kanıt blokları) ve repo tarafında bir yorumun yeniden yazılması `diff`te "canlıda olup repoda
# olmayan satır" gibi görünür. Satır bazlı bir kapı her yorum düzenlemesinde ENGEL derdi, yani hiç
# kopyalamazdı — kapı olmayan bir kapı. Anahtar/değer bazlı hüküm, "canlıda elle eklenmiş bir
# düğme" ile "repoda yeniden yazılmış bir yorum"u ayırt eder.
#
# DOSYA LİSTESİ GİT'TEN TÜRETİLİR, elle yazılmaz: yarın üçüncü bir state dosyası versiyona alınırsa
# bu adım onu kendiliğinden kapsar. Elle liste, tam da bu turda kapatılan kopukluğun kendisiydi.
echo "=== [1b/5] versiyonlu state farkı (canlı ↔ repo) ==="
STATE_TMP="$(mktemp -d)"; trap 'rm -rf "$STATE_TMP"' EXIT
STATE_VERSIYONLU="$(git ls-files state/ | sed 's|^state/||')"
STATE_KOPYALA=""; STATE_ENGEL=""     # bash 3.2: boş DİZİ + `set -u` patlar → boşluklu dizge
# HÜKÜM SÜRECİNİN KENDİSİ DÜŞERSE (uv/python yok, ortam bozuk) SONUÇ "fark yok" DEĞİLDİR: ölçüm
# yapılamadı demektir ve ölçülemeyen hüküm 'temiz' sayılmaz — fail-closed, operatöre.
_HUKUM_DUSTU="      hüküm süreci DÜŞTÜ (uv run python) — ölçülemedi, fail-closed
HUKUM=ENGEL"
# AÇIK `if` — `[[ … ]] && echo` DEĞİL: `set -e` altında koşul YANLIŞ olduğunda liste 1 döner ve o
# ifade betiğin SON komutu hâline geldiği gün dağıtım sessizce burada biter. Dağıtım betiğinde
# "bugün çalışıyor ama bir satır eklenince susar" sınıfına yer yok.
if [[ -z "${STATE_VERSIYONLU// /}" ]]; then
  echo "  (versiyonlu state dosyası yok — adım boş geçildi)"
fi
for _sf in $STATE_VERSIYONLU; do
  if ! "${SSH[@]}" "cat /opt/meridian/state/$_sf" > "$STATE_TMP/$_sf" 2>/dev/null; then
    # Dosya canlıda YOKSA/okunamıyorsa uygulama zaten açılamaz (`config.goal()` FileNotFoundError
    # atar) — bu bir dağıtım farkı değil bir ARIZA. Kopyalayıp üstünü örtmek, arızayı görünmez
    # kılardı; hüküm operatörün.
    echo "  ⚠ $_sf: CANLIDA OKUNAMADI — kopyalama YOK (arıza sınıfı, dağıtım farkı değil)"
    STATE_ENGEL="$STATE_ENGEL $_sf"; continue
  fi
  if cmp -s "$STATE_TMP/$_sf" "$REPO/state/$_sf"; then
    echo "  ✓ $_sf: canlı ile repo BİREBİR"; continue
  fi
  echo "  --- $_sf: FARK VAR (diff canlı→repo, ilk 30 satır) ---"
  diff -u "$STATE_TMP/$_sf" "$REPO/state/$_sf" | head -30 || true
  # ANAHTAR DÜZEYİ HÜKÜM. Yaprak yollara düzleştirilir (bounds: `entry.min_score.min`; goal:
  # `execution_v2.limit_pct_cap`) — iç içe blokları da kapsar. Son satır makine-okunur HÜKÜM'dür.
  _hukum="$(uv run python - "$STATE_TMP/$_sf" "$REPO/state/$_sf" <<'PY'
import sys, yaml


def duz(d, on=""):
    """Yaprak yollara düzleştir — iç içe blok (goal.execution_v2) da anahtar düzeyinde kıyaslansın."""
    out = {}
    if isinstance(d, dict):
        for k, v in d.items():
            yol = f"{on}{k}"
            if isinstance(v, dict):
                out.update(duz(v, yol + "."))
            else:
                out[yol] = v
    return out


try:
    canli = duz(yaml.safe_load(open(sys.argv[1], encoding="utf-8")) or {})
    repo = duz(yaml.safe_load(open(sys.argv[2], encoding="utf-8")) or {})
except Exception as e:
    # AYRIŞTIRILAMAYAN DOSYA "fark yok" DEĞİLDİR: hüküm verilemedi → ENGEL (fail-closed).
    print(f"      YAML okunamadı: {type(e).__name__}: {e}")
    print("HUKUM=ENGEL")
    raise SystemExit(0)

canli_fazla = sorted(set(canli) - set(repo))          # canlıda VAR, repoda YOK → elle değişiklik
repo_yeni = sorted(set(repo) - set(canli))            # repoda VAR, canlıda YOK → w_turnover sınıfı
deger = sorted(k for k in set(canli) & set(repo) if canli[k] != repo[k])
if repo_yeni:
    print(f"      repoda YENİ (canlı hiç görmedi): {', '.join(repo_yeni[:12])}"
          + (f" (+{len(repo_yeni) - 12})" if len(repo_yeni) > 12 else ""))
if deger:
    print(f"      DEĞER farkı: " + ", ".join(f"{k}: canlı={canli[k]!r} repo={repo[k]!r}"
                                             for k in deger[:8])
          + (f" (+{len(deger) - 8})" if len(deger) > 8 else ""))
if not (repo_yeni or deger or canli_fazla):
    print("      anahtar/değer düzeyinde fark YOK — ayrım yalnız yorum/biçim")
if canli_fazla:
    print(f"      CANLIDA REPO-DIŞI ANAHTAR: {', '.join(canli_fazla[:12])}"
          + (f" (+{len(canli_fazla) - 12})" if len(canli_fazla) > 12 else ""))
    print("HUKUM=ENGEL")
else:
    print("HUKUM=KOPYALA")
PY
)" || _hukum="$_HUKUM_DUSTU"
  echo "$_hukum" | grep -v '^HUKUM=' || true
  if [[ "$(echo "$_hukum" | grep '^HUKUM=' | tail -1)" == "HUKUM=KOPYALA" ]]; then
    echo "      → KOPYALANACAK (bakım penceresinde, durdurma sonrası/başlatma öncesi)"
    STATE_KOPYALA="$STATE_KOPYALA $_sf"
  else
    echo "      !! KOPYALANMAYACAK — canlı taraf elle değiştirilmiş görünüyor. HÜKÜM OPERATÖRÜN:"
    echo "         canlı satırı kasıtlıysa önce repoya al; değilse elle eşitle. Sessizce EZİLMEZ."
    STATE_ENGEL="$STATE_ENGEL $_sf"
  fi
done
if [[ -n "${STATE_ENGEL// /}" ]]; then
  echo "  ⚠ operatöre bırakılan:$STATE_ENGEL"
fi

# [1c] SİSTEM BİRİMİ AYRIKLIĞI (2026-08-14, YAŞANMIŞ VAKA). rsync `/opt/meridian/`e yazar; systemd'nin
# OKUDUĞU dosya `/etc/systemd/system/`dedir ve dagit onu KURMAZ. O gece `deploy/oracle-a1/meridian.service`e
# `Environment=MERIDIAN_AGENT_RPD=600` eklendi, suite geçti, dağıtım "TAMAM" dedi — ve ayar ETKİSİZ kaldı;
# arıza yalnızca worker'ın `/proc/<pid>/environ`ına elle bakılınca görüldü. Sessiz etkisizlik, yanlış
# ayardan beterdir: operatör değişikliğin yürürlükte olduğunu SANIR.
#
# NEDEN KURMUYOR, YALNIZ SÖYLÜYOR: birim kurmak `sudo` + `daemon-reload` + RESTART demektir; restart
# bakım penceresinin konusudur ve [4]'ün hükmüne aittir. Kapı burada bir KARAR vermez, GÖRÜNÜRLÜK üretir.
#
# AYRIM YÖNERGE DÜZEYİNDE ([1b]'nin dersi): bu dosyalar yorum ağırlıklıdır (mezar taşları, kanıt
# blokları). Ham `diff` her yorum düzenlemesinde bağırırdı, yani kimse bakmaz olurdu. Karşılaştırma
# YALNIZ yönerge satırlarında (`Anahtar=değer`); yorum farkı sessiz nottur.
echo "=== [1c/5] sistem birimi ayrıklığı (repo ↔ /etc) ==="
BIRIM_AYRIK=""
_yonergeler() { grep -E '^[A-Za-z][A-Za-z0-9]*=' "$1" 2>/dev/null | sed 's/[[:space:]]*$//' | sort; }
for _bs in "$REPO"/deploy/oracle-a1/*.service; do
  [[ -e "$_bs" ]] || continue
  _ad="$(basename "$_bs")"
  _canli_tmp="$(mktemp)"
  if ! "${SSH[@]}" "cat /etc/systemd/system/$_ad" > "$_canli_tmp" 2>/dev/null; then
    echo "  ⚠ $_ad: /etc/systemd/system'de YOK (hiç kurulmamış)"
    BIRIM_AYRIK="$BIRIM_AYRIK $_ad"; rm -f "$_canli_tmp"; continue
  fi
  if diff <(_yonergeler "$_bs") <(_yonergeler "$_canli_tmp") > /dev/null 2>&1; then
    # yorum farkı önemsizdir ama SESSİZ de kalmaz — "aynı" derken neyi kastettiğimiz yazılı olsun
    if diff -q "$_bs" "$_canli_tmp" > /dev/null 2>&1; then echo "  ✓ $_ad: birebir"
    else echo "  ✓ $_ad: YÖNERGELER aynı (yalnız yorum farkı)"; fi
  else
    echo "  ⚠ $_ad: YÖNERGE FARKI — repodaki değişiklik ETKİSİZ:"
    diff <(_yonergeler "$_canli_tmp") <(_yonergeler "$_bs") | grep -E '^[<>]' | sed 's/^/      /'
    BIRIM_AYRIK="$BIRIM_AYRIK $_ad"
  fi
  rm -f "$_canli_tmp"
done
if [[ -n "$BIRIM_AYRIK" ]]; then
  echo "  ——————————————————————————————————————————————————————————————"
  echo "  BU DEĞİŞİKLİKLER YÜRÜRLÜKTE DEĞİL. Kurmak OPERATÖR/BAKIM işidir:"
  for _ad in $BIRIM_AYRIK; do
    echo "    ssh ubuntu@$IP 'sudo cp -p /etc/systemd/system/$_ad /etc/systemd/system/$_ad.bak-\$(date -u +%Y%m%dT%H%M%SZ) && sudo install -m 0644 /opt/meridian/deploy/oracle-a1/$_ad /etc/systemd/system/$_ad && sudo systemctl daemon-reload'"
  done
  echo "  Ardından ilgili servis RESTART ister (bakım penceresi) ve etki"
  echo "  /proc/<MainPID>/environ üzerinden DOĞRULANMALIDIR — 'kurdum' ≠ 'yürürlükte'."
  echo "  ——————————————————————————————————————————————————————————————"
fi

# =================================================================================================
# [F9] DAGİT-KAPSAMI-DIŞI CANLI ARTEFAKTLAR — içerik kapısı (denetim §F9 2026-08-13; kablo 2026-08-23)
# =================================================================================================
# AŞAĞIDAKİ ARTEFAKTLAR rsync kapsamının DIŞINDA yaşar ve ELLE kurulur (deploy/oracle-a1/
# deploy.sh). SAYI BURADA YAZILI DEĞİL, `F9_LISTE`DE SAYILIR — düzyazıya gömülü bir sayım
# (eskiden "DÖRT ARTEFAKT" yazıyordu, liste 11'e çıkmıştı) tam da bu kapının kapatmak için var
# olduğu sürüklenmenin belgeye vurmuş hâlidir. TEK KAYNAK `F9_LISTE`; bu liste onun okunur özeti:
#   * meridian-sprint@.service  → /etc/systemd/system/     (v241 — sprint'in kendi cgroup birimi)
#   * 50-meridian-sprint.rules  → /etc/polkit-1/rules.d/   (v241 — NoNewPrivileges altında tetik izni)
#   * deploy/hermes/SOUL.md     → ~ubuntu/.hermes/SOUL.md  (v242 — hermes brifingi)
#   * deploy/hermes/config.yaml → ~ubuntu/.hermes/config.yaml  (v326 — ajan güvenlik duruşu:
#     approvals/deny + guard kancası + skills.external_dirs)
#   * meridian-tick-watchdog.service + .timer → /etc/systemd/system/  (asılı-tick bekçisi)
#   * litestream.yml → /etc/litestream.yml (kurulum litestream_kur.sh — 2026-08-23 eklendi)
#   * meridian-aylik-bucket-kopya.service + .timer → /etc/systemd/system/  (E-kod [4] 2026-08-23:
#     aylık bar-arşivi bucket kopyası; kurulumu birim başlığında)
#   * meridian-brifing.service + .timer → /etc/systemd/system/  (v327 — alarm yığını + öneri
#     brifingi kadansı; boşken sessiz, arızada `failed`)
#   * @sef profili: distribution.yaml + config.yaml + SOUL.md → ~ubuntu/.hermes/profiles/sef/
#     (Faz 2 — bot roster'ın ilk Hermes profili). BURADA BİR İNCELİK VAR: rsync depo tarafını
#     (`deploy/hermes/profiles/sef/`) canlıya TAŞIR, ama F9'un kıyasladığı şey o değil KURULU
#     KOPYAdır — profil canlıya `hermes profile install` ile varır ve o komut operatörün
#     kararıdır (yeni bir ajan kimliği doğurur). Yani "repoda güncel" ile "botun okuduğu dosya
#     güncel" AYRI iki gerçektir; kapının ölçtüğü ikincisidir.
# Bu, OB-2'yi doğuran "kurulu ≠ çalışır" sınıfıdır: repo ilerler, canlı kopya yerinde sayar ve
# hiçbir kapı bağırmazdı — denetim ölçtü: dagit'te bu dosyalara sıfır atıf vardı. [1c] yalnız
# *.service YÖNERGELERİNİ kıyaslar; bu kapı LİSTEDEKİ HER dosyanın TAM İÇERİĞİNİ kıyaslar
# (timer/polkit/brifing/yapılandırma [1c]'nin tür kapsamının dışındadır, yorum-düzeyi
# sürüklenme de burada görünür).
#
# KAPI RAPORLAR, ENGELLEMEZ — BİLİNÇLİ: bu artefaktlar dagit'in kopyalama kapsamında DEĞİL;
# ayrıklıkta dağıtımı durdurmak, elle-kurulum akışını (bakım penceresi + daemon-reload + doğrulama)
# dagit'e kilitlerdi. Kapının işi sürüklenmeyi GÖRÜNÜR yapmaktır; hüküm operatörün. Karşılaştırma
# [1b]'nin idiomuyla (`ssh cat | cmp` — karşılaştırma tek yerde, iki tarafta ayrı sha aracı
# aranmaz); "içerik-sha kapısı" sınıf adıdır, ölçü bayt-özdeşliktir (sha eşitliğinden güçlü).
echo "=== [F9] dagit-kapsamı-dışı canlı artefaktlar (içerik kapısı) ==="
F9_AYRIK=""; F9_OLCULEMEDI=""     # bash 3.2: boş DİZİ + `set -u` patlar → boşluklu dizge ([1b] gibi)
F9_LISTE="
deploy/oracle-a1/meridian-sprint@.service|/etc/systemd/system/meridian-sprint@.service
deploy/oracle-a1/50-meridian-sprint.rules|/etc/polkit-1/rules.d/50-meridian-sprint.rules
deploy/hermes/SOUL.md|/home/ubuntu/.hermes/SOUL.md
deploy/hermes/config.yaml|/home/ubuntu/.hermes/config.yaml
deploy/oracle-a1/meridian-tick-watchdog.service|/etc/systemd/system/meridian-tick-watchdog.service
deploy/oracle-a1/meridian-tick-watchdog.timer|/etc/systemd/system/meridian-tick-watchdog.timer
deploy/oracle-a1/litestream.yml|/etc/litestream.yml
deploy/oracle-a1/meridian-aylik-bucket-kopya.service|/etc/systemd/system/meridian-aylik-bucket-kopya.service
deploy/oracle-a1/meridian-aylik-bucket-kopya.timer|/etc/systemd/system/meridian-aylik-bucket-kopya.timer
deploy/oracle-a1/meridian-brifing.service|/etc/systemd/system/meridian-brifing.service
deploy/oracle-a1/meridian-brifing.timer|/etc/systemd/system/meridian-brifing.timer
deploy/hermes/profiles/sef/distribution.yaml|/home/ubuntu/.hermes/profiles/sef/distribution.yaml
deploy/hermes/profiles/sef/config.yaml|/home/ubuntu/.hermes/profiles/sef/config.yaml
deploy/hermes/profiles/sef/SOUL.md|/home/ubuntu/.hermes/profiles/sef/SOUL.md"
for _cift in $F9_LISTE; do
  _f9_repo="${_cift%%|*}"; _f9_canli="${_cift##*|}"; _f9_ad="$(basename "$_f9_repo")"
  if [[ ! -f "$REPO/$_f9_repo" ]]; then
    # Repo tarafı yoksa kıyas zemini yok — bu bir sürüklenme hükmü değil, LİSTENİN bayatlamasıdır.
    echo "  ⚠ $_f9_ad: ölçülemedi — REPODA YOK ($_f9_repo); kapı listesi bayat, listeyi güncelle"
    F9_OLCULEMEDI="$F9_OLCULEMEDI $_f9_ad"; continue
  fi
  _f9_tmp="$(mktemp)"
  # Önce düz cat; düşerse `sudo -n cat` (polkit rules.d dizini çoğu kurulumda root-dışına kapalıdır;
  # -n: parola sorusu ssh altında asılı kalmasın — NOPASSWD yoksa dal temiz düşer, aşağıda ayrışır).
  if ! "${SSH[@]}" "cat $_f9_canli" > "$_f9_tmp" 2>/dev/null && \
     ! "${SSH[@]}" "sudo -n cat $_f9_canli" > "$_f9_tmp" 2>/dev/null; then
    # ÖLÇÜLEMEYEN ne "aynı"dır ne "ayrık" (uydurma yasağı) — ama nedeni AYRIŞTIRILIR: yok mu,
    # okunamıyor mu? İkisi farklı iş kalemidir (kurulum vs. erişim/sudo arızası).
    if "${SSH[@]}" "sudo -n test -e $_f9_canli" 2>/dev/null; then
      echo "  ⚠ $_f9_ad: ölçülemedi — canlıda VAR ama OKUNAMADI (izin/sudo); elle bak: $_f9_canli"
    else
      echo "  ⚠ $_f9_ad: ölçülemedi — canlıda DOSYA YOK ($_f9_canli); hiç kurulmamış olabilir," \
           "kurulum elle: deploy/oracle-a1/deploy.sh"
    fi
    F9_OLCULEMEDI="$F9_OLCULEMEDI $_f9_ad"; rm -f "$_f9_tmp"; continue
  fi
  if cmp -s "$_f9_tmp" "$REPO/$_f9_repo"; then
    echo "  ✓ $_f9_ad: canlı ile repo BİREBİR"
  else
    echo "  ⚠ $_f9_ad: AYRIK — repodaki hâli canlıda DEĞİL (rsync bu dosyayı TAŞIMAZ; elle kurulum ister)"
    diff -u "$_f9_tmp" "$REPO/$_f9_repo" | head -12 || true
    F9_AYRIK="$F9_AYRIK $_f9_ad"
  fi
  rm -f "$_f9_tmp"
done
if [[ -n "${F9_AYRIK// /}" ]]; then
  echo "  ——————————————————————————————————————————————————————————————"
  echo "  [F9] AYRIK ARTEFAKT VAR:$F9_AYRIK"
  echo "  dagit bunları TAŞIMAZ; kurulum elle + bakım penceresi (deploy/oracle-a1/deploy.sh"
  echo "  ilgili adımları; birimler daemon-reload ister). Dağıtım ENGELLENMEDİ — özet sonda tekrarlanır."
  echo "  ——————————————————————————————————————————————————————————————"
fi

if [[ "${1:-}" != "--uygula" ]]; then
  # KURU KOŞUMDA YALNIZ DIFF: yukarıdaki blok hiçbir şey yazmadı (tek yazımı $STATE_TMP'ye okuma).
  # Kopyalama --uygula'ya ve BAKIM PENCERESİNE bağlıdır — koşan bir worker'ın altından yapılandırma
  # değiştirmek, dağıtımın kendisinden daha sinsi bir yarış üretirdi.
  echo ">> KURU KOŞUM BİTTİ. Tam dağıtım için: ./dagit.sh --uygula"; exit 0
fi

echo "=== [2/5] rsync ==="
rsync -az --delete "${RSYNC_EXC[@]}" -e "ssh -i $KEY" "$REPO"/ ubuntu@"$IP":/opt/meridian/
echo "  ✓"

# [3] DEV GRUBU A1'E KURULMAZ (karar 2026-08-01, ölçümü 2026-08-03'te kalıcılaştı): çalışma
# yolunda sıfır dev-import — hüküm [0d]'de HER DAĞITIMDA yeniden ölçülür, burada yalnız uygulanır.
# Kaldırılan 17 dağıtım (geçişli): pytest, hypothesis, import-linter+grimp, mutmut+libcst+textual…
# Kazanç yalnız disk değil DENETİM YÜZEYİ: [0b] `uv audit` kapısı artık yalnız A1'de GERÇEKTEN
# koşan koda ait CVE'lerle dağıtım bloklayabilir; bir test aracının CVE'si canlı dağıtımı durduramaz.
#
# BAYRAK KOŞUM ANINDA ÖLÇÜLÜR, VARSAYILMAZ. `--no-default-groups` semantik olarak daha dayanıklıdır:
# `--no-dev` YALNIZ `dev` grubunu eler, yani `tool.uv.default-groups` yarın ikinci bir grupla
# büyürse o grup A1'e SESSİZCE sızar (daraltma sanılan yerde daraltma olmaz). Ama o bayrağın
# A1'deki uv sürümünde VAR OLDUĞU buradan görülemez ve olmayan bir bayrak dağıtımı bakım
# penceresinin ortasında düşürürdü. Yardım çıktısına SORULUR; yoksa `--no-dev`e düşülür — bugün
# ikisi de ÖLÇÜLEN aynı 17 paketi kaldırıyor (ops/import_tarama.py), yani düşüş bedava.
SYNC_BAYRAK="--no-dev"
if "${SSH[@]}" 'export PATH="$HOME/.local/bin:$PATH"; uv sync --help 2>/dev/null | grep -q -- "--no-default-groups"'; then
  SYNC_BAYRAK="--no-default-groups"
fi
echo "=== [3/5] uv sync --frozen $SYNC_BAYRAK (dev grubu HARİÇ) ==="
"${SSH[@]}" "export PATH=\"\$HOME/.local/bin:\$PATH\"; cd /opt/meridian && uv sync --frozen $SYNC_BAYRAK -q && echo '  ✓'"

echo "=== [4/5] bakım penceresi ==="
# `meridian-learn` 2026-08-24'te LİSTEYE GİRDİ. Birim 2026-08-17'de doğdu ve bu betikte `learn`
# kelimesi HİÇ geçmiyordu — bilinçli dışlama değil UNUTMA. Bedeli ölçüldü: 12:30Z dağıtımı
# ısınma telemetrisini diske indirdi ama süreç 00:34:40'tan beri eski bytecode'u koşuyordu
# (11 sa 19 dk), ve doğrulama "active" dediği için kimse görmedi.
# RESTART UCUZ, ÖLÇÜLDÜ: sonda önbelleği diske yazılıyor (`reflect.PROBE_DISK_FILE`), döngü
# 300 sn'de bir uyanıyor, birim `Restart=always`. Kaybedilen en fazla o anki turun taze hesabı.
"${SSH[@]}" 'sudo systemctl stop meridian meridian-barsarchive meridian-learn && echo "  ✓ durdu"'

# VERSİYONLU STATE KOPYASI — DURDURMA SONRASI, BAŞLATMA ÖNCESİ (2026-08-02). Yer bilinçli:
#   * durdurmadan ÖNCE olsaydı, koşan worker yapılandırmayı okurken altından değişirdi (yarı-okuma
#     + `config.goal()` lru_cache'i eski değerle donmuş süreç = iki gerçek aynı anda).
#   * başlatmadan SONRA olsaydı yeni süreç ESKİ yapılandırmayla açılır, dosya sonradan değişir ve
#     etkisi bir sonraki restart'a kadar GÖRÜNMEZDİ — tam olarak bu adımın kapattığı sessizlik.
# Hüküm [1b]'de verildi; burada yalnız UYGULANIR (karar ile icra ayrı yerlerde durur).
#
# YEDEK NEREYE YAZILIR — `backups/state/`, `state/` DEĞİL (2026-08-07, MAKULLÜK bulgusu 1).
# Buradaki `cp` yedeği `state/$_sf.bak-$_damga` diye, yani DEDEKTÖRÜN TARADIĞI DİZİNİN İÇİNE
# yazıyordu. Sonucu ölçüldü: `yeniden_hesap:orphan_state_files` canlıda 7 dosya sayıyordu ve
# altısı bu satırın (ve bir bakım-penceresi `sed`inin) artığıydı — her dağıtım kartı bir satır
# daha kalabalıklaştırıyor, gerçek bir "üretilip tüketilmeyen kanıt" bulgusu o gürültüde
# kayboluyordu. Dedektörün desenini gevşetmek YANLIŞ onarım olurdu (bekçiyi kör etmek); doğru
# onarım artığın KAYNAĞINI taşımaktır — yedek hâlâ alınır, yalnız yeri değişir.
# `backups/` rsync'ten HARİÇTİR (satır 18): yedekler dağıtımla ne ezilir ne silinir, ve A1'de kalır.
# GERİ DÖNÜŞ YOLU AYNEN DURUYOR — yalnız adresi değişti:
#   ssh … "cp -p /opt/meridian/backups/state/goal.yaml.bak-<damga> /opt/meridian/state/goal.yaml"
if [[ -n "${STATE_KOPYALA// /}" ]]; then
  _damga="$(date -u +%Y%m%d%H%M)"
  _yedek_dizin="/opt/meridian/backups/state"
  "${SSH[@]}" "mkdir -p $_yedek_dizin"
  for _sf in $STATE_KOPYALA; do
    # GERİ ALINABİLİRLİK ÖNCE: birim migrasyonunun (adım 6) dersi — üstüne yazmadan önce yedekle.
    "${SSH[@]}" "cp -p /opt/meridian/state/$_sf $_yedek_dizin/$_sf.bak-$_damga"
    scp -q -i "$KEY" "$REPO/state/$_sf" ubuntu@"$IP":/opt/meridian/state/"$_sf"
    # KOPYALANDIĞI DOĞRULANIR, VARSAYILMAZ: uzak dosya yerel dosyayla BAYT-ÖZDEŞ mi? (`cmp` ile —
    # iki tarafta farklı md5 araçları aramaya gerek yok, karşılaştırma tek yerde yapılır.)
    if "${SSH[@]}" "cat /opt/meridian/state/$_sf" | cmp -s - "$REPO/state/$_sf"; then
      echo "  ✓ state/$_sf CANLIYA KOPYALANDI (yedek: backups/state/$_sf.bak-$_damga) — bayt-özdeş doğrulandı"
    else
      echo "  !! state/$_sf kopyalandı AMA doğrulanamadı — yedek: backups/state/$_sf.bak-$_damga"
      echo "     DAĞITIM DURDU (servisler DURMUŞ hâlde): yapılandırma belirsizken başlatmak, hangi"
      echo "     yasayla koştuğu bilinmeyen bir motor demektir. Yedeği geri koy ya da elle eşitle:"
      echo "     ssh ubuntu@$IP \"cp -p $_yedek_dizin/$_sf.bak-$_damga /opt/meridian/state/$_sf\""
      exit 1
    fi
  done
else
  echo "  · versiyonlu state kopyası YOK (fark yok ya da [1b] operatöre bıraktı)"
fi

"${SSH[@]}" 'sudo systemctl daemon-reload && sudo systemctl start meridian meridian-barsarchive meridian-learn && sleep 8 && systemctl is-active meridian meridian-barsarchive meridian-learn | tr "\n" " "; echo'

echo "=== [5/5] doğrulama ==="
"${SSH[@]}" 'curl -s -o /dev/null -w "healthz: %{http_code}\n" http://127.0.0.1:8080/healthz;
  tail -1 /opt/meridian/state/events.jsonl | head -c 200; echo'

# ARTIK BEKÇİSİ (2026-08-07). Bu betiğin yedeği artık `state/` dışına düşüyor — ama `state/`e
# yedek bırakan TEK yol bu değildi: canlıda `earnings.csv.sedbak` ve `earnings.csv.<damga>.bak`
# bir bakım penceresindeki elle `sed`den kalmıştı. Onların kaynağı bir betik değil bir ALIŞKANLIK,
# yani kodla kapatılamaz — GÖRÜNÜR kılınabilir. Burada yalnız SORULUR (salt okuma, hiçbir şey
# taşınmaz): pencere kapanırken artık varsa operatör onu aynı oturumda görür, bir hafta sonra
# makullük kartında değil.
echo "--- state/ artık kontrolü (salt okuma) ---"
_ARTIK="$("${SSH[@]}" "find /opt/meridian/state -maxdepth 1 -type f \\( -name '*.bak-*' -o -name '*.sedbak' -o -name '*.bak' \\) 2>/dev/null | sed 's|.*/||' | sort" || true)"
if [[ -z "${_ARTIK// /}" ]]; then
  echo "  ✓ state/ temiz — yedek artığı yok"
else
  echo "$_ARTIK" | sed 's/^/  · /'
  echo "  ⚠ yedek artığı VAR → orphan_state_files dedektörü bunları sayar."
  echo "    Temizlik (TAŞIR, silmez): bash ops/state_yetim_temizle.sh   # kuru koşu; sonra --uygula"
fi

# [F9 ÖZETİ] DAĞITIM ÖZETİNE TAŞINIR: kapı [F9] kuru-koşum tarafında koştu ve bulgusunu orada
# bastı; burada bir kez daha yazılır ki "DAĞITIM TAMAM" satırını okuyan göz onu kaçırmasın —
# raporlanan ama görülmeyen sürüklenme, hiç raporlanmamış gibidir.
if [[ -n "${F9_AYRIK// /}" || -n "${F9_OLCULEMEDI// /}" ]]; then
  echo "--- [F9] dagit-kapsamı-dışı artefakt özeti ---"
  if [[ -n "${F9_AYRIK// /}" ]];      then echo "  ⚠ AYRIK (repo ≠ canlı):$F9_AYRIK"; fi
  if [[ -n "${F9_OLCULEMEDI// /}" ]]; then echo "  ⚠ ölçülemedi:$F9_OLCULEMEDI"; fi
  echo "  Kurulum elle + bakım penceresi: deploy/oracle-a1/deploy.sh (dagit bu dosyaları taşımaz)."
fi

# =================================================================================================
# [B] DAĞITIM-BEYANI (P0-b — docs/ENVANTER-DEGER-ESITLIGI-2026-08-22.md §4.2). Ortamlar-arası #2
# ("repo-ağacı ↔ canlı-ağacı hangi tepede?") bugüne dek dedektörün YAPISAL kör noktasıydı: süreç-içi
# hiçbir kıyas iki ortamı aynı anda göremez. Kapısı bu beyandır: dagit her başarılı dağıtımın
# =================================================================================================
# [5c] ARTEFAKT TAZELİĞİ — derleme adımı [5b]'nin varsayımını KIRAR
# =================================================================================================
# [5b] "dağıtılan dosya = kaynak" varsayar ve Python için bu DOĞRU. Ama shadcn göçüyle araya bir
# DERLEME girdi: canlıya giden `meridian/web/pano*` artefaktı, `ui/` altındaki kaynaktan ÜRETİLİR.
# Kaynak değişip `npm run build` koşmazsa canlı sessizce bayat kalır ve [5b] bunu GÖREMEZ — o
# Python mtime'ına bakar, artefaktı hiç tanımaz. Bu, `meridian-learn`de yaşadığımız SESSİZ
# ETKİSİZLİĞİN aynısıdır: doğru bir cümle, anlamsız bir güvence.
#
# DEĞİŞMEZ:  mtime(meridian/web/pano.html)  >=  en yeni mtime(ui/ altındaki kaynak)
#
# YERELDE ölçülür (dağıtımdan ÖNCE), çünkü onarım da yerel: `cd ui && npm run build`. Canlıda
# ölçmenin anlamı yok — orada kaynak zaten yok (rsync `/ui`yi dışlıyor).
# ~~JETON KÖPRÜSÜ AYRICA ÖLÇÜLÜR: `ops/jeton_css_uret.py --kontrol`~~ — 2026-08-25'te DÜŞTÜ.
# Köprü `ui/src/jetonlar.css`i üretiyordu ve o dosyayı yalnız pilotun `stil.css`i okuyordu.
# studio-admin göçüyle jeton katmanı ŞABLONUNKİ oldu (`src/tema.css`); `jetonlar.css`in artık
# HİÇ okuyucusu yok. Okuyucusu olmayan bir dosyanın tazeliğini ölçmek, doğru bir cümleyle
# anlamsız bir güvence vermektir — tam da [5b]'nin düzelttiği hata sınıfı (YASA 6).
# Betik ve üretim yolu DURUYOR (silinmedi): göç sırasında bir rol jetonuna geri dönmek
# gerekirse köprü yerinde. Geri açılacaksa ÖNCE bir okuyucusu olmalı.
_ART="$REPO/meridian/web/pano.html"
if [ -d "$REPO/ui" ]; then
  echo "=== [5c/5] artefakt tazeliği (pano) ==="
  if [ ! -f "$_ART" ]; then
    echo "  ATLANDI pano artefaktı yok (henüz derlenmedi) — kapı ölçülemedi, dağıtım sürüyor"
  else
    _art_m=$(stat -f %m "$_ART" 2>/dev/null || stat -c %Y "$_ART")
    _kay_m=$(find "$REPO/ui" -type f \( -name '*.ts' -o -name '*.tsx' -o -name '*.css' -o -name '*.html' -o -name '*.json' \) \
             -not -path '*/node_modules/*' -exec stat -f %m {} \; 2>/dev/null | sort -rn | head -1)
    [ -z "$_kay_m" ] && _kay_m=$(find "$REPO/ui" -type f \( -name '*.ts' -o -name '*.tsx' -o -name '*.css' -o -name '*.html' -o -name '*.json' \) \
             -not -path '*/node_modules/*' -printf '%T@\n' 2>/dev/null | cut -d. -f1 | sort -rn | head -1)
    if [ -n "$_kay_m" ] && [ "$_art_m" -lt "$_kay_m" ]; then
      echo "  IHLAL artefakt BAYAT: pano.html $_art_m < ui/ kaynak $_kay_m"
      echo "  onarım: cd ui && npm run build   (sonra dagit'i tekrar koş — rsync idempotent)"
      exit 1
    fi
    echo "  TAMAM artefakt kaynağından taze"
  fi
fi

# =================================================================================================
# [5b] KOD-TAZELİK DEĞİŞMEZİ — "active" ≠ "yeni kodu koşuyor"
# =================================================================================================
# ÖLÇÜLEN VAKA (2026-08-24). [5] doğrulaması "iki birim de active" dedi ve bu DOĞRUYDU; ama
# `meridian-learn` 00:34:40'tan beri koşuyordu ve en yeni kaynak 11:53:16'ydı. Yani doğru bir
# cümle, ANLAMSIZ bir güvence verdi: `active`, sürecin hangi kodu taşıdığı hakkında hiçbir şey
# söylemez. Yarı-etkili bir dağıtım "TAMAM" damgası aldı.
#
# DEĞİŞMEZ:  süreç başlangıcı  ≥  en yeni  /opt/meridian/meridian/**/*.py  mtime'ı
#
# KAPSAM ELLE SAYILMAZ, ExecStart'TAN TÜRETİLİR. Birim adlarını buraya yazsaydık yarın eklenen
# bir birim aynı sessizlikle unutulurdu — düzeltmek istediğimiz sınıfın ta kendisi. Kural:
# `running` durumda VE ExecStart'ı /opt/meridian altından python/uv koşan her birim. Bu sayede
# `meridian-litestream` (litestream ikilisi, Python değil) kendiliğinden DIŞARIDA kalır.
#
# NEDEN [B]'DEN ÖNCE: beyan `state/dagitim.json`a "bu sha canlıda" yazar. Süreçlerden biri eski
# kodu koşuyorsa o cümle YANLIŞTIR. Kapı önce düşerse dosya eski sha'da kalır — koşan sistemin
# GERÇEK hâli odur (operatör kararı 2026-08-24). Onarım: birimi döndür, betiği tekrar koş
# (rsync idempotent).
echo "=== [5b/5] kod-tazelik değişmezi (süreç ≥ kaynak) ==="
_tazelik="$("${SSH[@]}" '
  yeni=$(find /opt/meridian/meridian -name "*.py" -printf "%T@\n" 2>/dev/null | sort -rn | head -1)
  yeni_ad=$(find /opt/meridian/meridian -name "*.py" -printf "%T@ %p\n" 2>/dev/null | sort -rn | head -1 | cut -d" " -f2-)
  [ -z "$yeni" ] && { echo "OLCULEMEDI kaynak-mtime-okunamadi"; exit 0; }
  for u in $(systemctl list-units --type=service --state=running --no-legend --plain 2>/dev/null \
             | awk "{print \$1}" | grep "^meridian"); do
    es=$(systemctl show "$u" -p ExecStart --value 2>/dev/null)
    case "$es" in *"/opt/meridian"*python*|*"/opt/meridian"*|*uv*) ;; *) continue ;; esac
    case "$es" in *litestream*) continue ;; esac
    bas=$(systemctl show "$u" -p ExecMainStartTimestampMonotonic --value 2>/dev/null)
    bas_epoch=$(date -u -d "$(systemctl show "$u" -p ExecMainStartTimestamp --value)" +%s 2>/dev/null)
    [ -z "$bas_epoch" ] && { echo "OLCULEMEDI $u sureç-baslangici-okunamadi"; continue; }
    if [ "${bas_epoch%.*}" -lt "${yeni%.*}" ]; then
      yas=$(( ${yeni%.*} - ${bas_epoch%.*} ))
      echo "IHLAL $u $yas $yeni_ad"
    fi
  done')"
if [ -z "$_tazelik" ]; then
  echo "  ✓ koşan tüm meridian birimleri dağıtılan kodu taşıyor"
else
  echo "$_tazelik" | while read -r _d _u _y _f; do
    if [ "$_d" = "IHLAL" ]; then
      echo "  ✗ $_u — süreç kaynaktan $(( _y / 60 )) dk ESKİ (en yeni: $_f)"
    else
      echo "  ⚠ ölçülemedi: $_u $_y"
    fi
  done
  if echo "$_tazelik" | grep -q "^IHLAL"; then
    echo "  ——————————————————————————————————————————————————————————————"
    echo "  DAĞITIM YARI-ETKİLİ: kod diskte, süreç eski. Beyan YAZILMADI —"
    echo "  \`state/dagitim.json\` koşan sistemin gerçek hâlini (eski sha) söylemeyi sürdürüyor."
    echo "  Onarım: sudo systemctl restart <birim>  →  ardından ./dagit.sh --uygula (rsync idempotent)"
    echo "  ——————————————————————————————————————————————————————————————"
    exit 1
  fi
fi

# SONUNDA canlıya `state/dagitim.json` yazar. OKUYUCUSU (YASA 6): envanter/denetim turlarının
# ortamlar-arası kıyası + "canlıda hangi sha koşuyor" sorusunu soran operatör (660dc10 dersinin
# kalıcılaşması: beyan, kapılardan geçen tepeyi [0a]'da dondurulmuş DAGIT_SHA'dan söyler).
#
# CANLI STATE'E YAZIM — BİLİNÇLİ İSTİSNA: "canlı worker koşarken state'e yazma" yasağının konusu
# worker'ın OKUDUĞU/YAZDIĞI defter ve yapılandırma dosyalarıdır; dağıtım anı zaten bakım anıdır ve
# `dagitim.json`u hiçbir canlı süreç okumaz/yazmaz (salt dağıtım kaydı — okuyucusu yukarıda).
# Yazım yine de ATOMİKTİR (tmp + mv): yarım JSON, ortamlar-arası kapıyı "ölçülemedi"ye değil
# YANLIŞ hükme götürürdü. Yazıldığı bayt-özdeş DOĞRULANIR ([1b] kopya disiplini, satır ~298).
echo "=== [B] dağıtım-beyanı (state/dagitim.json → canlı) ==="
_beyan_utc="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
_beyan_host="$(hostname)"
_beyan_tmp="$(mktemp)"
printf '{"deployed_sha": "%s", "dagitildi_utc": "%s", "dagitan_host": "%s", "kirli_gec_kullanildi": %s}\n' \
  "$DAGIT_SHA" "$_beyan_utc" "$_beyan_host" "$KIRLI_GEC" > "$_beyan_tmp"
sed 's/^/  /' "$_beyan_tmp"   # aynı beyan dağıtım çıktısına da basılır (yerel kopya dosyaya YAZILMAZ:
                              # repoda state dosyası biriktirmek [1b]'nin kapattığı ayrışmayı geri açar)
if "${SSH[@]}" "cat > /opt/meridian/state/.dagitim.json.tmp && mv /opt/meridian/state/.dagitim.json.tmp /opt/meridian/state/dagitim.json" < "$_beyan_tmp" \
   && "${SSH[@]}" "cat /opt/meridian/state/dagitim.json" | cmp -s - "$_beyan_tmp"; then
  echo "  ✓ beyan canlıya yazıldı — bayt-özdeş doğrulandı"
else
  # ENGEL DEĞİL — dağıtım bu noktada ZATEN tamam ([4] başlattı, [5] doğruladı); beyanın yazılamaması
  # dağıtımı geri almaz, yalnız ortamlar-arası kıyası BU TUR İÇİN kör bırakır. Sessiz de bırakılmaz.
  echo "  !! BEYAN YAZILAMADI/DOĞRULANAMADI — ortamlar-arası kıyas bu dağıtımı GÖREMEZ."
  echo "     Elle yaz (yukarıdaki JSON'la): ssh ubuntu@$IP 'cat > /opt/meridian/state/dagitim.json'"
fi
rm -f "$_beyan_tmp"
echo "=== DAĞITIM TAMAM ==="
