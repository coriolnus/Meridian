#!/usr/bin/env bash
# ================================================================================================
# ETKİLENEN TEST SEÇİCİSİ — "tam suite" her commit'in aracı DEĞİLDİR
# ------------------------------------------------------------------------------------------------
# NEDEN VAR — ÖLÇÜLMÜŞ İSRAF (2026-08-26, operatör kalemi): kenar çubuğu ikonu `size-4`ten
# `size-5`e çekildi (bir Tailwind sınıfı) ve tam suite koşuldu.
#     tam suite                 7183 test   28:13
#     gerçekten etkilenen küme   149 test    0:18.7      ← 90 kat
# Değişiklik dört dosyaydı; o yolları okuyan test dosyası SEKİZ taneydi.
#
# KURALIN KAYNAĞI: CLAUDE.md madde 6 "tam suite yalnız Rol-1'de TEK-OTORİTER" der — "HER
# COMMIT'te" DEMEZ. Kuralı sıkılaştırmak disiplin değil israftır.
#
# ------------------------------------------------------------------------------------------------
# SINIR — BU BETİĞİN NE ZAMAN KÖR OLDUĞU (en önemli paragraf):
#   Diff `meridian/**/*.py` dosyasına dokunuyorsa BU SEÇİCİ YETMEZ ve betik tam suite İSTER.
#   Sebep yapısal: orada etki IMPORT GRAFİĞİNDEN yayılır. `sprint.py` değişince onu import eden
#   `scheduler.py`yi import eden bir testi kırabilir — ve o testin dosyasında "sprint.py" DİZESİ
#   HİÇ GEÇMEZ. "Hangi test bu yolu anıyor" mantığı o durumda yapısal olarak kördür.
#   Varlık/UI/doküman değişikliğinde ise mantık SAĞLAMDIR: bu depodaki çiviler yolları AÇIKÇA
#   okur (kaynak-tarayıcı testler, `pathlib` + `read_text`), yani anmak = bağımlılık.
#
# AŞIRI-KAPSAMA GÜVENLİ, EKSİK-KAPSAMA DEĞİL: şüphede geniş davranılır (tam yol + taban ad +
# uzantısız ad + üst dizin adı). Fazladan koşan test saniye yakar; kaçan test sessiz gerileme
# dağıtır. Bu asimetri bilinçlidir.
#
# KULLANIM:
#   ops/etkilenen_testler.sh                      # çalışma ağacı (commit'lenmemiş) değişiklikleri
#   ops/etkilenen_testler.sh --commit HEAD        # tek commit
#   ops/etkilenen_testler.sh --yollar a/b.tsx c/d.json   # açık yol listesi (test edilebilirlik)
# Çıkış kodu: 0 = seçici küme yeterli · 1 = TAM SUITE gerekli · 2 = eşleşme yok (karar okuyucuda)
# Çivi: tests/test_etkilenen_testler_v322.py
# ================================================================================================
set -uo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO"

# TAŞINABİLİRLİK: `mapfile` bash 4+ yapısıdır ve macOS'un /bin/bash'ı 3.2'dir. Bu depo hem
# geliştirme Mac'inde hem A1'de (bash 5) koşuyor; betik ikisinde de çalışmak zorunda. İlk sürüm
# `mapfile` kullandı ve macOS'ta "command not found" + `unbound variable` zinciriyle düştü —
# ÇİVİ YAKALADI (v322). Aşağıdaki okuyucu iki sürümde de aynı işi yapar.
_satirlari_oku() {            # kullanım: _satirlari_oku DIZI_ADI < <(komut)
  local _ad="$1" _s; eval "$_ad=()"
  while IFS= read -r _s; do
    [[ -n "$_s" ]] && eval "$_ad+=(\"\$_s\")"
  done
}

MOD="agac"; YOLLAR=()
case "${1:-}" in
  --yollar) shift; YOLLAR=("$@"); MOD="acik" ;;
  --commit) MOD="commit"; REV="${2:-HEAD}" ;;
  "") : ;;
  *) echo "bilinmeyen argüman: $1" >&2; exit 64 ;;
esac

if [[ "$MOD" == "agac" ]]; then
  _satirlari_oku YOLLAR < <(git diff --name-only HEAD; git ls-files --others --exclude-standard)
elif [[ "$MOD" == "commit" ]]; then
  _satirlari_oku YOLLAR < <(git show --name-only --format="" "$REV")
fi
# Boş satırları at.
TEMIZ=(); for y in ${YOLLAR[@]+"${YOLLAR[@]}"}; do [[ -n "$y" ]] && TEMIZ+=("$y"); done
YOLLAR=(${TEMIZ[@]+"${TEMIZ[@]}"})

if [[ ${#YOLLAR[@]} -eq 0 ]]; then
  echo "DEĞİŞİKLİK YOK — koşulacak bir şey yok."; exit 0
fi

echo "=== değişen yollar (${#YOLLAR[@]}) ==="
printf '  %s\n' "${YOLLAR[@]}"

# ---- SINIR KAPISI: motor `.py`si değiştiyse seçici kördür (yukarıdaki SINIR paragrafı) --------
MOTOR=()
for y in "${YOLLAR[@]}"; do
  [[ "$y" == meridian/*.py || "$y" == meridian/**/*.py ]] && MOTOR+=("$y")
done
if [[ ${#MOTOR[@]} -gt 0 ]]; then
  echo
  echo "!! TAM SUITE GEREKLİ — motor kaynağı değişti:"
  printf '     %s\n' "${MOTOR[@]}"
  echo "   Sebep: etki IMPORT GRAFİĞİNDEN yayılır; bir testin bu dosyanın ADINI içermesi"
  echo "   gerekmez, dolayısıyla ad-eşleşmeli seçici burada YAPISAL OLARAK KÖRDÜR."
  echo "   Koş:  .venv/bin/python -m pytest"
  exit 1
fi

# ---- KÜRESEL ERİŞİM KAPISI (dogfood sırasında bulundu, 2026-08-26) -----------------------------
# Bu dosyalar `meridian/**/*.py` DEĞİL ama etkileri KÜRESEL — ve ikisi de yukarıdaki iki kapıdan
# sızıyordu:
#   · `tests/conftest.py` → 7 AUTOUSE fikstür, yani HER testte koşar. `meridian/` altında
#     olmadığı için motor kapısına takılmaz, ve adı testlerin çoğunda GEÇMEZ (fikstür adıyla
#     çağrılır, dosya adıyla değil) → ad-eşleşmeli seçici onu TAMAMEN ıskalar.
#   · `pyproject.toml` → `addopts`, her koşumun bayrakları.
# Bir autouse fikstürünü değiştirip "5 dosya koştum, temiz" demek, 7183 testin davranışını
# ölçmeden dağıtmaktır.
KURESEL=()
for y in "${YOLLAR[@]}"; do
  case "$y" in
    tests/conftest.py|*/conftest.py|pyproject.toml|pytest.ini|setup.cfg) KURESEL+=("$y") ;;
  esac
done
if [[ ${#KURESEL[@]} -gt 0 ]]; then
  echo
  echo "!! TAM SUITE GEREKLİ — küresel erişimli dosya değişti:"
  printf '     %s\n' "${KURESEL[@]}"
  echo "   Sebep: conftest autouse fikstürleri HER testte koşar, addopts HER koşumun bayrağıdır."
  echo "   Ad-eşleşmeli seçici bunları yapısal olarak göremez (testler fikstürü ADIYLA çağırır,"
  echo "   dosya adıyla değil)."
  echo "   Koş:  .venv/bin/python -m pytest"
  exit 1
fi

# ---- ARAMA JETONLARI: geniş davran (asimetri gerekçesi yukarıda) ------------------------------
# ÜST DİZİN JETONU YALNIZ HASH'Lİ ADLARDA — ve bu bir DARALTMA düzeltmesidir. İlk sürüm üst
# dizini KOŞULSUZ ekliyordu; `docs/bir-sey.md` için jeton `docs` oluyordu ve 387 test dosyasının
# 106'sı eşleşiyordu. "Aşırı-kapsama güvenlidir" ilkesi doğru ama o kadarı seçiciyi İŞE YARAMAZ
# kılar — 106 dosya koşmak tam suite'e yaklaşmaktır, yani aracın varlık sebebini yer.
# GERÇEK İHTİYAÇ DAR: içerik-hash'li varlıklar (`pano-DCZt1aC7.js`). Onların adı her derlemede
# değişir, dolayısıyla hiçbir test adı ANMAZ — testler DİZİNİ anar (`pano-assets`). Jeton bu
# yüzden yalnız ad hash'li göründüğünde eklenir.
_hashli() {   # `ad-XXXXXXXX.uzanti` — son segment ≥8 karakter ve TİRE İÇERMEZ
  # TİRE DIŞARIDA, ve bu bir düzeltmedir: ilk sürüm `[A-Za-z0-9_-]{8,}` yazdı, yani segment
  # tire içerebiliyordu ve `OLMAYAN-DOSYA-xyzzy.md` hash SAYILDI → üst dizin (`docs`) jeton
  # oldu → 106 dosya eşleşti. Vite hash'i (`pano-DCZt1aC7.js`) tek parçadır, tire içermez.
  [[ "$1" =~ -[A-Za-z0-9_]{8,}\.[A-Za-z0-9]+$ ]]
}
# UZANTI SOYMA YALNIZ MODÜL BENZERİ DOSYALARDA — ikinci daraltma düzeltmesi. Amaç dar: bir
# bileşen/modül testte uzantısız anılır (`MarkaIsareti`, `app-sidebar`). Ama `.html`/`.json`/
# `.css` dosyaları testlerde TAM ADIYLA okunur, ve onların uzantısız hâli felakete yol açıyor:
# `pano.html` → jeton `pano` → 203 dosya eşleşti (elle ölçülen gerçek küme SEKİZDİ).
# İki koşul birden: modül uzantısı VE ≥5 karakter (kısa ad = geniş eşleşme).
_modul_uzantisi() {
  case "$1" in *.ts|*.tsx|*.js|*.jsx|*.py) return 0 ;; *) return 1 ;; esac
}
JETON=()
for y in "${YOLLAR[@]}"; do
  taban="$(basename "$y")"
  JETON+=("$y" "$taban")
  govde="${taban%.*}"
  if _modul_uzantisi "$taban" && [[ ${#govde} -ge 5 ]]; then
    JETON+=("$govde")
  fi
  if _hashli "$taban"; then
    ust="$(basename "$(dirname "$y")")"
    [[ -n "$ust" && "$ust" != "." && "$ust" != "/" ]] && JETON+=("$ust")
  fi
  # DİZİN JETONU (EĞİK ÇİZGİLİ) — DÖRDÜNCÜ KÖRLÜĞÜN KAPATILMASI, canlı vakayla bulundu:
  # bu betiği `ops/` altına eklemek `test_uiux_s1b_v154`i kırdı. O test RUNBOOK'u üretip
  # "N ops betiği" sayısını doğruluyor — yani DİZİNİ sayıyor ve yeni dosyanın ADINI hiç
  # anmıyor. Sınıf genel: bir dizini sayan/tarayan test, o dizine eklenen HER dosyadan
  # etkilenir ama hiçbirinin adını içermez.
  # EĞİK ÇİZGİ ZORUNLU: çıplak `ops` bir kelime olarak her yerde geçer; `ops/` bir YOL'dur.
  # Ölçüldü: `ops/`→20, `meridian/web/`→27, `research/cards/`→8, `docs/`→51 test dosyası
  # (387 içinde). Bedel saniyeler; kaçırmanın bedeli sessiz bir gerilemenin dağıtılmasıdır.
  dizin="$(dirname "$y")"
  [[ -n "$dizin" && "$dizin" != "." ]] && JETON+=("$dizin/")
done
# Yinelenenleri ele.
_satirlari_oku JETON < <(printf '%s\n' "${JETON[@]}" | sort -u | grep -vE '^\.?$')

DESEN="$(printf '%s\n' "${JETON[@]}" | sed 's/[][\.*^$(){}?+|/]/\\&/g' | paste -sd'|' -)"
ETKI=()
_satirlari_oku ETKI < <(grep -rlE "$DESEN" tests/*.py 2>/dev/null | sort -u)

# Değişen test dosyalarının KENDİLERİ de kümeye girer (kendini sınamayan bir çivi eklemesi
# "yeşil" görünürdü — dosya adı başka testte geçmeyebilir).
for y in "${YOLLAR[@]}"; do
  [[ "$y" == tests/test_*.py && -f "$y" ]] && ETKI+=("$y")
done
_satirlari_oku ETKI < <(printf '%s\n' ${ETKI[@]+"${ETKI[@]}"} | grep -v '^$' | sort -u)

echo
if [[ ${#ETKI[@]} -eq 0 ]]; then
  # UYDURMA YASAĞI komşusu: "eşleşme yok" ile "koşacak test yok" AYNI ŞEY DEĞİLDİR.
  echo "EŞLEŞME YOK — bu yolları anan bir test dosyası bulunamadı."
  echo "  Bu, 'gerileme riski yok' DEMEK DEĞİLDİR: değişiklik hiç sınanmıyor da olabilir."
  echo "  Karar okuyucunun: ya kapsayan bir çivi yaz, ya tam suite koş."
  exit 2
fi

echo "=== etkilenen test dosyaları (${#ETKI[@]}) ==="
printf '  %s\n' "${ETKI[@]}"
echo
echo "Koş:"
echo "  .venv/bin/python -m pytest ${ETKI[*]}"
exit 0
