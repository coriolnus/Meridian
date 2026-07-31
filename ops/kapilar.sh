#!/usr/bin/env bash
# kapilar.sh — MERIDIAN KAPI ZİNCİRİ (WP-H/H4, 2026-07-31).
#
# NEDEN TEK BETİK. Bu depoda üç ayrı kapı var ve üçü de ayrı ayrı çalıştırılabiliyordu — yani
# pratikte hiçbiri düzenli çalışmıyordu. "Kapı var" ile "kapıdan geçildi" arasındaki fark, bu
# deponun tekrar eden kusur sınıfıdır (fail-notify birimi kurulmuştu ama hiç ateşlenmemişti).
# Tek çağrı, sabit sıra, ilk kırmızıda DUR.
#
# SIRA GEREKÇELİ, keyfi değil — ucuzdan pahalıya VE dıştan içe:
#   [1] lint-imports  (~2 sn)  — mimari sözleşmeler. En ucuz ve en yapısal: bir yukarı-yön
#                                bağımlılık doğduysa altındaki hiçbir ölçüm güvenilir değildir.
#   [2] uv audit      (~1 sn)  — tedarik zinciri. Kırmızıysa koşturduğumuz kodun kim olduğunu
#                                bilmiyoruz demektir; test yeşilliği bunu telafi etmez.
#   [3] pytest kapsamı(~30 sn) — anayasa yasalarının property paketi + doğrudan komşuları.
#
# BU TAM SUITE DEĞİLDİR VE ONUN YERİNE GEÇMEZ. Tam suite turda BİR kez, Rol-1'de, tek-otoriter
# koşar (CLAUDE.md §6). Bu betik "dağıtımdan önce hızlı sağlık" kapısıdır — geçmesi dağıtım için
# GEREK şarttır, YETER şart değildir.
#
# KULLANIM: ./ops/kapilar.sh          → üç kapı, ilk kırmızıda exit 1
#           ./ops/kapilar.sh --hizli  → pytest kapsamını atla (yalnız [1]+[2]; ~3 sn)
set -uo pipefail
cd "$(dirname "$0")/.."

UV="${UV:-uv}"
HIZLI="${1:-}"
KIRMIZI=0

baslik() { printf '\n=== %s ===\n' "$1"; }

baslik "[1/3] lint-imports — mimari sözleşmeler"
if "$UV" run lint-imports; then
  echo "  ✓ sözleşmeler KORUNDU"
else
  echo "!! MİMARİ SÖZLEŞME KIRILDI — yeni bir yukarı-yön bağımlılık ya da döngü doğdu."
  echo "   Sözleşmeler ve istisna gerekçeleri: pyproject.toml [tool.importlinter]"
  echo "   İstisna EKLEMEK bir çözüm DEĞİL bir borç kaydıdır; ekliyorsan gerekçeyi yanına yaz."
  KIRMIZI=1
fi

baslik "[2/3] uv audit — tedarik zinciri"
if "$UV" audit --preview-features audit-command; then
  echo "  ✓ bilinen açık YOK"
else
  echo "!! TEDARİK ZİNCİRİ KIRMIZI — bağımlılıkta bilinen açık var. Dağıtım YOK."
  KIRMIZI=1
fi

if [[ "$HIZLI" == "--hizli" ]]; then
  baslik "[3/3] pytest kapsamı — ATLANDI (--hizli)"
  echo "  ⚠ anayasa property paketi KOŞULMADI: bu koşum dağıtım kapısı SAYILMAZ."
else
  baslik "[3/3] pytest kapsamı — anayasa property paketi + doğrudan komşular"
  # Dosya listesi ELLE ve DAR tutulur: bu kapının değeri HIZINDA. Genişletme isteği geldiğinde
  # doğru cevap genelde "tam suite'i Rol-1'de koş"tur — yavaşlayan bir kapı, atlanan bir kapıdır.
  if "$UV" run pytest -q \
      tests/test_anayasa_hypothesis_v143.py \
      tests/test_warmup_tavani_v143.py \
      tests/test_storage_v142.py \
      tests/test_storage_eszamanlilik_v142.py \
      tests/test_defter_kaynak_damgasi_v140.py \
      tests/test_bars_integrity_v141.py; then
    echo "  ✓ anayasa kapsamı YEŞİL"
  else
    echo "!! ANAYASA KAPSAMI KIRMIZI — bir yasa ihlal edildi. Tam grep ile bak:"
    echo "   uv run pytest -q tests/ 2>&1 | grep -E 'FAILED|ERROR'"
    KIRMIZI=1
  fi
fi

echo
if [[ "$KIRMIZI" -ne 0 ]]; then
  echo "=== KAPI ZİNCİRİ KIRMIZI — geçilmedi ==="
  exit 1
fi
echo "=== KAPI ZİNCİRİ YEŞİL (tam suite'in YERİNE GEÇMEZ) ==="
