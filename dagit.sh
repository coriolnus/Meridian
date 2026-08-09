#!/usr/bin/env bash
# dagit.sh — Meridian GENEL dağıtım betiği (WP-H/H2 kapılı). Tek-seferlik gece betiklerinin
# (dagitim_gece*.sh) yerine standart yol: her dağıtım BU sırayla geçer.
#   [0] uv audit (tedarik-zinciri kapısı — kırmızıysa DAĞITIM YOK)
#   [0c] lint-imports (mimari sözleşmeler — WP-H/H4; kırmızıysa DAĞITIM YOK)
#   [0d] import taraması (dev-grubu daraltması hâlâ güvenli mi — WP-H; kırmızıysa DAĞITIM YOK)
#   [1] rsync DRY-RUN (ne değişecek göster; yarım-iş/mtime tuzağına karşı GÖZLE onay)
#   [1b] versiyonlu state farkı (goal.yaml + bounds.yaml canlı↔repo; kuru koşumda YALNIZ diff)
#   [2] rsync (state/backups/.venv/.git HARİÇ)
#   [3] uv sync --frozen (dev grubu HARİÇ — [0d]'nin hükmüne dayanır)
#   [4] bakım penceresi: durdur → versiyonlu state kopyası ([1b] KOPYALA dediyse) → başlat
#   [5] doğrulama: servisler active + healthz 200 + son olay yaşı
# Kullanım: ./dagit.sh            → dry-run'a kadar gider, ONAY İSTER
#           ./dagit.sh --uygula   → tam dağıtım
set -euo pipefail
KEY="$HOME/.ssh/oci-a1.key"; IP="130.61.126.87"; REPO="$HOME/AI-Trading"
SSH=(ssh -i "$KEY" -o ConnectTimeout=15 ubuntu@"$IP")
RSYNC_EXC=(--exclude '.venv' --exclude '.git' --exclude 'state' --exclude 'backups' --exclude 'scratchpad' --exclude '__pycache__' --exclude '.claude' --exclude '.hypothesis' --exclude 'mutants' --exclude '.pytest_cache' --exclude '.env' --exclude '.dash.env' --exclude '.agents' --exclude '.codex' --exclude '.github' --exclude 'skills-lock.json' --exclude '.impeccable' --exclude '.import_linter_cache' --exclude 'research/olcumler/*/seanslar.json' --exclude 'research/olcumler/*/run.stderr.log' --exclude 'research/olcumler/*/state')  # + ÖLÇÜM HAM ÇIKTILARI (2026-08-10, ROADMAP §2 madde-1): .gitignore rsync'i ETKİLEMEZ — ham seans dökümü/betik-state/stderr yeniden-üretilebilir (olcum*.py deterministik), canlıda okuyucusu yok; özet sonuc.json + olcum*.py TAŞINIR  # + HARNESS ARTEFAKTLARI (2026-08-06): worktree-oturum kalıntıları dagit'i dry-run'da boğdu  # + ARAÇ ÖNBELLEKLERİ (2026-08-07): .impeccable/hook.cache.json (kökte VE meridian/web/ altında) ile .import_linter_cache/ kuru koşumda göründü — 306ab56'nın hükmü bunları kapsamıyordu. İkisi de araç katmanı: canlıda karşılığı yok, hiçbir test okumuyor, ama tool-layer sızıntısı aynı sınıf.  # SIR SINIFI (2026-08-01 vakası): rsync --delete A1-yerel .dash.env'i SİLDİ — sırlar dağıtıma binmez, kanal push_secret.sh

echo "=== [0a/5] git temiz-ağaç kapısı ==="
cd "$REPO"
if [[ -n "$(git status --porcelain)" ]]; then
  if [[ "${2:-}" == "--kirli-gec" || "${1:-}" == "--kirli-gec" ]]; then
    echo "  ⚠ KİRLİ AĞAÇLA dağıtım (bilinçli --kirli-gec)"; git status --short | head -10
  else
    echo "!! Çalışma ağacı KİRLİ — önce commit'le (yarım-iş canlıya gitmesin)."
    echo "   Bilinçli istisna için: ./dagit.sh --uygula --kirli-gec"; git status --short | head -15; exit 1
  fi
fi
echo "  ✓ dağıtılacak commit: $(git rev-parse --short HEAD) — $(git log -1 --format=%s | head -c 60)"

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
rsync -azin --delete "${RSYNC_EXC[@]}" -e "ssh -i $KEY" "$REPO"/ ubuntu@"$IP":/opt/meridian/ | head -40
echo "--- (yukarısı ilk 40 satır; boşsa fark yok) ---"

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
"${SSH[@]}" 'sudo systemctl stop meridian meridian-barsarchive && echo "  ✓ durdu"'

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

"${SSH[@]}" 'sudo systemctl daemon-reload && sudo systemctl start meridian meridian-barsarchive && sleep 8 && systemctl is-active meridian meridian-barsarchive | tr "\n" " "; echo'

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
echo "=== DAĞITIM TAMAM ==="
