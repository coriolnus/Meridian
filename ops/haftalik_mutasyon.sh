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
#   ./ops/haftalik_mutasyon.sh             # TAM koşum (SAATLER) → docs/mutasyon/<tarih>.md
set -euo pipefail
cd "$(dirname "$0")/.."

TARIH="$(date +%F)"
CIKTI_DIZIN="docs/mutasyon"
CIKTI="${CIKTI_DIZIN}/${TARIH}.md"
UV="${UV:-uv}"

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
if testler != ["tests"]:
    hata.append(f"test seçimi beklenen ['tests'] değil: {testler}")

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

if [[ "${1:-}" == "--kontrol" ]]; then
  oz_test
  echo ">> öz-test TAMAM. Tam koşum için argümansız çalıştır (SAATLER sürer)."
  exit 0
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
