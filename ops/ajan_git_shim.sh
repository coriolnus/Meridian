#!/bin/sh
# ops/ajan_git_shim.sh — TSK-050: git mutasyon kapısının MEKANİK v1'i (B-AJAN-GIT).
#
# NE KAPATIR — yalnız HİÇBİR oturumda meşru olmayan iki sınıf:
#   * `git stash` (her alt biçimi) — gece 2 ajan stash koşup hayalet dizini süpürdü (vaka
#     2026-08-26 sınıfı; CLAUDE.md §2: stash okuma DEĞİLDİR).
#   * `git add -A` / `git add --all` / `git add .` — vaka a94d425 ("Hiçbir zaman"); "." yalnız
#     TAM jeton olarak yakalanır, `git add ./dosya` meşrudur.
# BAŞKA HİÇBİR ŞEYİ KAPATMAZ: commit/push/checkout ayrımı oturum kimliği ister ve ortamdan
# ÖLÇÜLEMEZ (spike 2026-09-01: Rol-1 Bash'i ile ajan Bash'i AYNI işaretleri taşıyor —
# CLAUDE_CODE_CHILD_SESSION=1 + AI_AGENT=..._agent ikisinde de; ayrım bilgi-tabanlı olurdu,
# o genişleme AYRI karar). Sözleşme kapısı (CLAUDE.md §2/§3) aynen yürürlükte — bu shim onun
# yerine değil, dalgınlığa karşı mekanik bariyer.
#
# KİMİ ETKİLER: yalnız CLAUDECODE=1 ortamları (Claude Code oturumları — Rol-1 dahil, ki bu
# İYİ: iki yasak evrenseldir). Operatörün kendi terminali CLAUDECODE taşımaz → shim saydam
# exec ile gerçek git'e devreder, sıfır davranış farkı.
# KAÇIŞ (bilinçli eylem, dalgınlık değil): MERIDIAN_GIT_BYPASS=1 ile geç.
# KURULUM: cp ops/ajan_git_shim.sh ~/.local/bin/git && chmod +x ~/.local/bin/git
#   (~/.local/bin PATH'in BAŞINDA — ölçüldü 2026-09-01). Yerel-makine koruması; dagit rsync'i
#   bunu A1'e dosya olarak taşır ama KURMAZ (A1'de ajan oturumu yok, zararsız).
# TEST KANCASI: MERIDIAN_GERCEK_GIT — testler sahte git enjekte eder; boşsa bilinen konumlar.

gercek_git() {
    if [ -n "$MERIDIAN_GERCEK_GIT" ]; then exec "$MERIDIAN_GERCEK_GIT" "$@"; fi
    for g in /opt/homebrew/bin/git /usr/bin/git /usr/local/bin/git; do
        if [ -x "$g" ]; then exec "$g" "$@"; fi
    done
    echo "ajan_git_shim: gerçek git bulunamadı (bilinen konumlar boş)" >&2
    exit 127
}

# Claude oturumu değilse ya da bilinçli kaçış: saydam geçiş.
if [ "$CLAUDECODE" != "1" ] || [ "$MERIDIAN_GIT_BYPASS" = "1" ]; then gercek_git "$@"; fi

# İlk alt-komutu bul (git'in global bayraklarını -c/-C/--git-dir vb. atlayarak; değer alan
# bayrağın değeri de atlanır). Alt-komut bulunamazsa (yalnız bayrak/versiyon) saydam geçiş.
altkomut=""
beklenen_deger=0
for arg in "$@"; do
    if [ "$beklenen_deger" = "1" ]; then beklenen_deger=0; continue; fi
    case "$arg" in
        -c|-C|--git-dir|--work-tree|--namespace|--exec-path) beklenen_deger=1 ;;
        -*) ;;   # değer taşımayan/eşittirli global bayrak — atla
        *) altkomut="$arg"; break ;;
    esac
done

if [ "$altkomut" = "stash" ]; then
    echo "ajan_git_shim RED: 'git stash' hiçbir Meridian oturumunda meşru değil (CLAUDE.md §2;" \
         "vaka 2026-08-26 — stash okuma DEĞİLDİR). Bilinçli kaçış: MERIDIAN_GIT_BYPASS=1." >&2
    exit 86
fi

if [ "$altkomut" = "add" ]; then
    add_gorunudu=0
    for arg in "$@"; do
        if [ "$add_gorunudu" = "0" ]; then
            [ "$arg" = "add" ] && add_gorunudu=1
            continue
        fi
        case "$arg" in
            -A|--all|.)
                echo "ajan_git_shim RED: 'git add $arg' yasak (vaka a94d425 — ajanın yarım işi" \
                     "commit'e karışır). Açık yollarla add kullan. Kaçış: MERIDIAN_GIT_BYPASS=1." >&2
                exit 86 ;;
        esac
    done
fi

gercek_git "$@"
