#!/usr/bin/env bash
# haftalik_mutasyon.sh — HAFTALIK MUTASYON TESTİ (WP-H/H5, 2026-07-31).
#
# NE ÖLÇER. Kapsam ("bu satır koşuldu mu") ile SINAMA ("bu satır DEĞİŞSE test kırılır mı") aynı şey
# değildir. Bu depoda 1300+ test var ve hepsi yeşil — ama yeşil bir suite, ölçmediği bir davranış
# hakkında hiçbir şey KANITLAMAZ. Mutasyon testi tam olarak o farkı ölçer: kaynağa küçük bir kusur
# enjekte eder ve suite'in onu yakalayıp yakalamadığına bakar. HAYATTA KALAN bir mutant, "burada
# testlerin görmediği bir davranış var" demektir — yani bu depoda uydurma riskinin adresi.
#
# NEDEN YALNIZ ÜÇ DOSYA (pyproject `[tool.mutmut] only_mutate`): para yolunun karar çekirdeği.
#   broker.py — pozisyon/risk/de-risk rampası    guard.py — parametre sınırları
#   score.py  — skor=para yasası
# Tüm repoyu mutasyona uğratmak günler sürer ve sinyali seyreltirdi. Kapsam genişletme kararı
# Rol-1'indir; genişletirken bu betiğe DOKUNULMAZ, yalnız pyproject'teki liste büyür.
#
# NEDEN HAFTALIK VE ELLE: koşum SAATLER sürer (her mutant için suite'in ilgili kesiti yeniden
# koşar). Bir kadansa bağlamak, gecelik pencereyi tek başına yerdi. Bakım ritüelinde koşulur.
#
# KULLANIM:
#   ./ops/haftalik_mutasyon.sh --kontrol   # HIZLI öz-test: mutmut yapılandırmayı GÖRÜYOR mu?
#   ./ops/haftalik_mutasyon.sh --kisa      # KISA doğrulama: tek dosya + dar test seçimi, DAKİKALAR
#   ./ops/haftalik_mutasyon.sh             # TAM koşum (SAATLER) → docs/mutasyon/<tarih>.md
set -euo pipefail
cd "$(dirname "$0")/.."

TARIH="$(date +%F)"
CIKTI_DIZIN="docs/mutasyon"
CIKTI="${CIKTI_DIZIN}/${TARIH}.md"
UV="${UV:-uv}"
KOK="$(pwd)"
# Kısa doğrulamanın kapsamı: GERÇEK hedeflerden EN KÜÇÜĞÜ + onun kendi denetim testi. Yapay bir
# oyuncak modül seçilmedi — kısa mod, tam koşumun küçültülmüş hâli olmalı, benzeri değil.
KISA_DOSYA="${KISA_DOSYA:-meridian/score.py}"
KISA_TEST="${KISA_TEST:-tests/test_score_audit_v40.py}"

# ---- ÖZ-TEST: yapılandırma GERÇEKTEN okunuyor mu? ----------------------------------------------
# Bu adım koşumdan ÖNCE gelir ve bir sigortadır. mutmut 3'te `paths_to_mutate`/`tests_dir`
# anahtarları DEPRECATED'dır; yanlış anahtarla yazılmış bir yapılandırma SESSİZCE yok sayılır ve
# mutmut TÜM repoyu mutasyona uğratmaya başlar (saatler → günler, ve kimse nedenini anlamaz).
# Yapılandırmanın GÖRÜLDÜĞÜNÜ iddia etmek yetmez — ölçülür.
oz_test() {
  echo "=== öz-test: mutmut yapılandırmayı görüyor mu? ==="
  "$UV" run python - <<'PY'
import sys
from mutmut.configuration import Config

c = Config.get()
kaynak = [str(p) for p in c.source_paths]
sadece = list(c.only_mutate)
testler = list(c.pytest_add_cli_args_test_selection)
print(f"  source_paths                       : {kaynak}")
print(f"  only_mutate                        : {sadece}")
print(f"  pytest_add_cli_args_test_selection : {testler}")

beklenen = {"meridian/broker.py", "meridian/guard.py", "meridian/score.py"}
hata = []
if kaynak != ["meridian"]:
    hata.append(f"source_paths beklenen ['meridian'] değil: {kaynak} — paket EKSİK kopyalanırsa "
                f"her test import hatasıyla ölür ve skor sahte %100 çıkar")
if set(sadece) != beklenen:
    hata.append(f"only_mutate beklenen {sorted(beklenen)} değil: {sadece}")
# Test seçimi: 'tests' ile BAŞLAMALI; kalanı yalnız --deselect çiftleri olabilir (ortam-duyarlı
# dışlamalar, pyproject'te gerekçeli). Birebir-eşitlik kapısı 2026-08-01'de meşru dışlamayı
# kırmızıya boyadı — kapı artık biçimi ölçer, listeyi ezberlemez.
if not testler or testler[0] != "tests":
    hata.append(f"test seçimi 'tests' ile başlamıyor: {testler}")
else:
    kalan = testler[1:]
    while kalan:
        if kalan[0] != "--deselect" or len(kalan) < 2 or not kalan[1].startswith("tests/"):
            hata.append(f"test seçiminde --deselect çifti dışında öğe: {kalan}")
            break
        kalan = kalan[2:]

# DURUM FİKSTÜRÜ KAPISI (H5 kırığı, 2026-08-01). mutmut testleri `mutants/` içinden koşturur;
# `config.ROOT` orada `mutants/`e çözülür ve `mutants/state/` yoksa HER test FileNotFoundError ile
# ölür — istatistik toplanamaz. Kopyayı mutmut'un kendi `also_copy` kancası yapar; bu kapı o
# satırın DURDUĞUNU ve kaynağın gerçekten var olduğunu ölçer (ikisi de olmadan koşum baştan ölü).
from pathlib import Path
kopya = [str(p) for p in c.also_copy]
if "state" not in kopya:
    hata.append(f"also_copy içinde 'state' YOK: {kopya} — mutants/state kurulmaz, her test "
                f"`required config missing: .../mutants/state/goal.yaml` ile ölür")
for gerekli in ("state/goal.yaml", "state/bounds.yaml"):
    if not Path(gerekli).exists():
        hata.append(f"{gerekli} YOK — kopyalanacak fikstürün kaynağı eksik")

# Kapının KENDİSİNİ sına: filtre gerçekten kapsam dışını eliyor mu?
if c.should_mutate("meridian/api.py"):
    hata.append("api.py mutasyon kapsamında görünüyor — only_mutate filtresi UYGULANMIYOR")
if not c.should_mutate("meridian/broker.py"):
    hata.append("broker.py mutasyon kapsamı DIŞINDA görünüyor — filtre fazla dar")

if hata:
    print("\n!! YAPILANDIRMA KAPISI KIRMIZI:")
    for h in hata:
        print(f"   - {h}")
    sys.exit(1)
print("  ✓ yapılandırma okundu ve kapsam DOĞRULANDI (3 dosya, tests/ seçimi)")
PY
}

# ---- KISA DOĞRULAMA: mutmut UÇTAN UCA koşuyor mu? (H5 kırığının kanıt kapısı, 2026-08-01) -------
# NE KANITLAR: mutant üretimi + `mutants/state` fikstürü + İSTATİSTİK TOPLAMA + mutant başına test
# koşumu zincirinin TAMAMI çalışıyor ve mutantlar GERÇEKTEN öldürülüyor. Kırık tam da bu zincirin
# ortasındaydı (istatistik toplanamıyordu) ve "yapılandırma görülüyor" öz-testi onu YAKALAYAMAZDI.
#
# NEDEN AYRI BİR ÇALIŞMA DİZİNİ: tam koşumun test seçimi `tests/` (yani TÜM suite) — istatistik
# toplama o seçimi bir kez baştan sona koşar ve kısa doğrulama olmaktan çıkar. mutmut yapılandırmayı
# YALNIZ cwd'deki pyproject.toml'dan okur (env/CLI ile daraltılamaz — mutmut/configuration.py), o
# yüzden daraltma ancak ayrı bir çalışma dizininde mümkün. Depo pyproject'i ASLA elden geçirilmez:
# ritüelin ortasında gerçek yapılandırmayı geçici olarak değiştirmek, koşum yarıda kalırsa depoyu
# bozuk bırakırdı. Kaynak ağaçları KOPYALANMAZ, SEMBOLİK BAĞ verilir (kopya maliyeti sıfır; mutmut
# zaten kendi `mutants/` kopyasını çıkarır ve mutasyon YALNIZ o kopyaya yazılır).
kisa_dogrulama() {
  # DEĞİŞKEN GLOBAL, `local` DEĞİL: EXIT tuzağı fonksiyon DÖNDÜKTEN sonra koşar ve yerel değişken o
  # anda yok olmuş olur — `set -u` altında temizlik "unbound variable" ile ölürdü (ilk koşumda oldu).
  KISA_WS="$(mktemp -d "${TMPDIR:-/tmp}/meridian-mutasyon-kisa.XXXXXX")"
  trap 'rm -rf "${KISA_WS:-}"' EXIT
  local ws="$KISA_WS"
  echo "=== kısa doğrulama: ${KISA_DOSYA} × ${KISA_TEST} (çalışma dizini: $ws) ==="
  ln -s "$KOK/meridian" "$ws/meridian"
  ln -s "$KOK/tests"    "$ws/tests"
  ln -s "$KOK/state"    "$ws/state"
  "$KOK/.venv/bin/python" - "$ws" "$KISA_DOSYA" "$KISA_TEST" <<'PY'
import sys, pathlib
ws, dosya, test = sys.argv[1], sys.argv[2], sys.argv[3]
metin = pathlib.Path("pyproject.toml").read_text()
# GERÇEK pyproject'ten TÜRETİLİR (kopyalanır + tek bölüm daraltılır): pytest ini ayarları, markerlar
# ve bağımlılık bölümleri birebir aynı kalsın — kısa mod tam koşumun küçültülmüşü olmalı.
bas = metin.index("[tool.mutmut]")
son = metin.find("\n[", bas + 1)
son = len(metin) if son == -1 else son
dar = (f"[tool.mutmut]\nsource_paths = [\"meridian\"]\nonly_mutate = [\"{dosya}\"]\n"
       f"pytest_add_cli_args_test_selection = [\"{test}\"]\nalso_copy = [\"state\"]\n"
       f"timeout_multiplier = 5.0\ntimeout_constant = 10.0\n")
pathlib.Path(ws, "pyproject.toml").write_text(metin[:bas] + dar + metin[son:])
print(f"  daraltılmış yapılandırma yazıldı: only_mutate={dosya} · test={test}")
PY
  local kod=0
  ( cd "$ws" && "$KOK/.venv/bin/mutmut" run ) || kod=$?
  echo "  mutmut run çıkış kodu: $kod (0'dan farklı = hayatta kalan mutant VAR — arıza değil)"
  # FİKSTÜR KAPISI: kırığın kendisi. Dosya yoksa istatistik toplama baştan ölürdü.
  if [[ ! -f "$ws/mutants/state/goal.yaml" ]]; then
    echo "!! KISA DOĞRULAMA KIRMIZI: mutants/state/goal.yaml kurulmadı (also_copy işlemedi)"; return 1
  fi
  echo "  ✓ fikstür kuruldu: mutants/state/goal.yaml"
  # HÜKÜM SAYIDAN OKUNUR, EKRANDAN DEĞİL. `mutmut results` YALNIZ hayatta kalanları listeler
  # (killed satırları bilerek basmaz) — ilk denemede bu yüzden "hiç öldürülmedi" sanıldı, oysa 266
  # mutant ölmüştü. Makine-okunur kaynak `export-cicd-stats`in yazdığı JSON'dur.
  # KOMUT ADI `export-cicd-stats` (tire), fonksiyon adı `export_cicd_stats` DEĞİL — click alt
  # çizgiyi tireye çevirir. İlk denemede alt çizgiyle çağrıldı, komut sessizce bulunamadı ve kapı
  # "sonuç üretilmedi" dedi: çıktıyı /dev/null'a atan bir çağrı, kendi yazım hatasını da yutar.
  ( cd "$ws" && "$KOK/.venv/bin/mutmut" export-cicd-stats ) || {
    echo "!! KISA DOĞRULAMA KIRMIZI: export-cicd-stats çalışmadı (mutmut sürümü/komut adı değişmiş olabilir)"
    return 1
  }
  "$KOK/.venv/bin/python" - "$ws" <<'PY' || return 1
import json, pathlib, sys
p = pathlib.Path(sys.argv[1], "mutants", "mutmut-cicd-stats.json")
if not p.exists():
    print("!! KISA DOĞRULAMA KIRMIZI: mutmut-cicd-stats.json yok — koşum sonuç ÜRETMEDİ")
    raise SystemExit(1)
d = json.loads(p.read_text())
print(f"  mutant: toplam={d.get('total')} · öldürülen={d.get('killed')} · hayatta={d.get('survived')} "
      f"· testsiz={d.get('no_tests')} · zaman aşımı={d.get('timeout')}")
# İKİ KOŞUL BİRDEN: mutant ÜRETİLDİ (total>0) VE testler onları GERÇEKTEN öldürebiliyor (killed>0).
# killed=0, "suite bu dosyayı hiç sınamıyor" ile "testler hiç koşmadı"yı aynı yüzle gösterir — ve
# H5'in kırığı tam olarak ikincisiydi. Hayatta kalan mutant sayısı bir ARIZA değil, ölçüm sonucudur.
if not d.get("total"):
    print("!! KISA DOĞRULAMA KIRMIZI: hiç mutant üretilmedi (only_mutate/source_paths eşleşmiyor)")
    raise SystemExit(1)
if not d.get("killed"):
    print("!! KISA DOĞRULAMA KIRMIZI: hiç mutant ÖLDÜRÜLMEDİ — istatistik/test zinciri koşmuyor "
          "(fikstür kırığının imzası: her test aynı hatayla ölürse hiçbir mutant ölmez)")
    raise SystemExit(1)
PY
  echo ">> KISA DOĞRULAMA YEŞİL: üretim → fikstür → istatistik → mutant koşumu zinciri çalışıyor."
}

if [[ "${1:-}" == "--kontrol" ]]; then
  oz_test
  echo ">> öz-test TAMAM. Tam koşum için argümansız çalıştır (SAATLER sürer)."
  exit 0
fi

if [[ "${1:-}" == "--kisa" ]]; then
  oz_test
  kisa_dogrulama
  exit $?
fi

oz_test

mkdir -p "$CIKTI_DIZIN"
echo "=== mutasyon koşumu başlıyor — SAATLER sürebilir (çıktı: $CIKTI) ==="
BASLANGIC="$(date -u +%FT%TZ)"

# `mutmut run` hayatta kalan mutant varsa SIFIRDAN FARKLI döner. Bu bir ARIZA DEĞİL, ÖLÇÜM
# SONUCUdur — betik onu yutmaz ama üstüne de düşmez: rapor her hâlükârda yazılır, çıkış kodu
# raporun sonunda dürüstçe taşınır.
set +e
"$UV" run mutmut run 2>&1 | tee "${CIKTI_DIZIN}/.${TARIH}.ham.log"
KOSUM_KODU=${PIPESTATUS[0]}
set -e
# MUTMUT'UN SESSİZ YALANI (2026-08-01, ikinci kırık): temiz-koşum/istatistik toplama düşse bile
# `mutmut run` exit 0 verebiliyor ("failed to collect stats. runner returned 1" yalnız stdout'ta).
# Çıkış kodunu ham logdaki arıza imzasından DÜZELTİYORUZ — skor üretmeyen koşum başarı sayılamaz.
if grep -q "failed to collect stats" "${CIKTI_DIZIN}/.${TARIH}.ham.log"; then
  echo "!! istatistik toplanamadı — koşum BAŞARISIZ sayılıyor (mutmut exit 0 dese bile)"
  KOSUM_KODU=1
fi

BITIS="$(date -u +%FT%TZ)"

# ---- RAPOR ------------------------------------------------------------------------------------
# `mutmut results` hayatta kalan mutantları ADIYLA listeler. Skor tek başına bir sayıdır; DEĞERLİ
# olan listedir — her satır "testlerin görmediği bir davranış" adresidir ve bir sonraki turun
# test borcu listesidir.
{
  echo "# Mutasyon koşumu — ${TARIH}"
  echo
  echo "- başlangıç: \`${BASLANGIC}\`  ·  bitiş: \`${BITIS}\`"
  echo "- kapsam: \`meridian/broker.py\`, \`meridian/guard.py\`, \`meridian/score.py\` (pyproject \`[tool.mutmut] only_mutate\`)"
  echo "- test seçimi: \`tests/\`"
  echo "- \`mutmut run\` çıkış kodu: \`${KOSUM_KODU}\` (0'dan farklı = hayatta kalan mutant VAR; arıza değil, ölçüm)"
  echo
  echo "## Skor"
  echo
  echo '```'
  "$UV" run mutmut results 2>&1 | tail -60 || echo "(mutmut results okunamadı — ham log: .${TARIH}.ham.log)"
  echo '```'
  echo
  echo "## Hayatta kalan mutantlar (test borcu)"
  echo
  echo "Her satır, suite'in ÖLÇMEDİĞİ bir davranıştır. Hüküm Rol-1'in: ya davranışı sınayan bir test"
  echo "yazılır, ya da mutantın EŞDEĞER olduğu (davranışı gerçekten değiştirmediği) gerekçesiyle kayda"
  echo "geçilir. Sessizce bırakmak, kapsamı sınama sanmaktır."
  echo
  echo '```'
  "$UV" run mutmut browse --help >/dev/null 2>&1 && \
    echo "(ayrıntılı gezinti: \`uv run mutmut browse\` — bu betik etkileşimli TUI açmaz)"
  "$UV" run mutmut results 2>&1 | grep -iE "survived|hayatta" | head -80 || echo "(hayatta kalan mutant listesi boş ya da okunamadı)"
  echo '```'
} > "$CIKTI"

echo "=== rapor yazıldı: $CIKTI ==="
exit "$KOSUM_KODU"
