#!/usr/bin/env bash
# dagit.sh — Meridian dağıtımının İNCE SARMALAYICISI. EMEKLİ OLACAK (TSK-176 Faz A1, 2026-09-08).
#
# BU BETİK ARTIK KAPI TAŞIMIYOR. Dağıtımın on yedi kapısı — [0a] [0b] [0c] [0d] [1] [1b] [1c]
# [F9] [F10] [2] [3] [4] [5] [5a] [5c] [5b] [B] — `deploy/ansible/dagit.yml` playbook'una TAŞINDI
# (Task 2, 2026-09-08). Listelerin (dosya-dışlama sınıfları, [F9] çiftleri, [5a] uçları, birim
# adayları) TEK KAYNAĞI `deploy/ansible/vars/dagit_vars.yml`dir; kapı gövdelerinin tek kaynağı
# `ops/state_fark_hukmu.py`, `ops/artefakt_tazelik.py`, `deploy/oracle-a1/dogrulama_anahtar.py`,
# `deploy/oracle-a1/kod_tazelik.sh` dosyalarıdır. Buradaki kopyalar SİLİNDİ — iki kaynak sessizce
# ayrışır (tek-kaynak yasası) ve ayrışan taraf her zaman okunmayan taraftır.
#
# NEDEN BİR SÜRÜM DAHA YAŞIYOR (K1 geçiş kararı): operatörün ve belgelerin parmak hafızası
# `./dagit.sh`tır; kapılar taşınırken çağrı adresini de aynı turda değiştirmek, ilk gerçek
# playbook dağıtımının arıza yüzeyini iki katına çıkarırdı. Sarmalayıcı yalnız YÖNLENDİRİR:
# kendi kapısı, kendi listesi, kendi ölçümü YOKTUR. Bir sürüm sonra SİLİNİR ve komut satırı
# `ansible-playbook`a döner (Task 4 / ROADMAP TSK-176 A1).
#
# Kullanım (repo kökünden ya da başka bir dizinden — fark etmez, aşağıya bak):
#   ./dagit.sh                       → kuru koşum (playbook `--check --diff`)
#   ./dagit.sh --dry-run             → aynısı, açık yazılmış hâli
#   ./dagit.sh --uygula              → gerçek dağıtım (aynı playbook, `--check`siz)
#   ./dagit.sh --uygula --kirli-gec  → + `-e kirli_gec=true` (kirli ağaç BEYANLI istisnası)
# Bilinmeyen bayrak → kullanım basılır ve ÇIKIŞ 2 (sessizce "kuru koşum" varsayılmaz: yanlış
# yazılmış bir `--uygla`nın kuru koşuma düşmesi, operatöre dağıttığını sandırırdı).
# Kip bayrağı (`--dry-run` / `--uygula`) EN FAZLA BİR KEZ verilir; ikincisi de ÇIKIŞ 2'dir.
# "Son bayrak kazanır" davranışı `./dagit.sh --dry-run --uygula`yı UYARISIZ gerçek dağıtıma
# çevirirdi (ters sıra ise kuru koşuma): aynı komut satırı, iki farklı dünya. Belirsizlik
# burada canlıya YAZMA yönüne çözülüyordu — tek başına `--kirli-gec`i reddetme gerekçesinin
# aynısı, pahalı yönde (inceleme bulgusu B1, 2026-09-08).
#
# CWD'YE BAKMAZ: dağıtılan ağaç HER ZAMAN ana checkout'tur (`$HOME/AI-Trading`), bu betiğin
# çağrıldığı dizin değil (CLAUDE.md §9, vaka 2026-08-26 — "ağacım temiz" bir güvence DEĞİLDİR).
# Playbook aynı kuralı `repo_kok_yerel` ile taşır ve ana-checkout kapısını [0a]'da kendisi ölçer;
# başka bir checkout'tan dağıtım BEYANLIDIR (`-e worktree_gec=true`) ve [B] beyanına yazılır.
#
# SÜRÜM TERFİSİ SÖZLEŞMESİ (WP5-B; bu başlık tek kaynak — RUNBOOK üreticisi kapsamına 2026-08-23
# K4 kararıyla alındı): canlıya yeni sürüm YALNIZ bu yoldan çıkar; `git push` dağıtım DEĞİLDİR
# (cloud görünürlüğü). Dağıtılan tepe playbook'un [0a] kapısında donar ve [B] beyanına yazılır.
# GERİ ALMA: önceki commit'e dönüp (`git checkout <sha>`) aynı akışı koşmak — state'e dokunulmaz;
# versiyonlu state kopyası ([1b]) yalnız hükümle yapıldığından goal/bounds geri-alması da aynı
# kapıdan geçer.
set -euo pipefail

# ANA CHECKOUT — LİTERAL, TÜRETİLMEZ (çivi: tests/test_ansible_dagit_v452.py B12).
REPO="$HOME/AI-Trading"
PLAYBOOK="deploy/ansible/dagit.yml"
ENVANTER="deploy/ansible/inventory.ini"
# Yorumlayıcı da proje ortamından: sistem python'unda ansible YOKTUR ve "koşamıyorum" ile
# "kapı kırmızı" birbirine karışır (CLAUDE.md §6'nın `.venv/bin/python` kuralıyla aynı sınıf).
ANSIBLE="$REPO/.venv/bin/ansible-playbook"

_kullanim() {
  echo "Kullanım: ./dagit.sh [--dry-run]              → kuru koşum ($PLAYBOOK --check --diff)"
  echo "          ./dagit.sh --uygula                 → gerçek dağıtım"
  echo "          ./dagit.sh --uygula --kirli-gec     → + -e kirli_gec=true"
  echo "          (--kirli-gec tek başına verilmez: hangi modda koşacağı belirsiz kalır)"
  echo "          (kip bayrağı EN FAZLA bir kez: --dry-run/--uygula birlikte ya da iki kez YOK)"
}

MOD=""
KIRLI_GEC=false
_KIP_ILK=""   # İLK kip bayrağının METNİ — hata mesajı operatörün yazdığı bayrağı anmalı.

# KİP BAYRAĞI KAPISI (inceleme bulgusu B1, 2026-09-08): ikinci bir kip bayrağı komut satırını
# belirsiz yapar. Eski döngü MOD'u üzerine yazıyordu, yani SON bayrak kazanıyordu: sıraya bağlı
# olarak aynı çağrı bir kez kuru koşum, bir kez GERÇEK DAĞITIM oluyordu ve hiçbir uyarı yoktu.
_kip_kapisi() {
  if [[ -n "$_KIP_ILK" ]]; then
    echo "!! Kip bayrağı EN FAZLA bir kez verilir: '$_KIP_ILK' seçiliyken '$1' geldi."
    echo "   'Son bayrak kazanır' YOK — hangi modda koşacağı belirsiz kalır."
    _kullanim
    exit 2
  fi
  _KIP_ILK="$1"
}

for _arg in "$@"; do
  case "$_arg" in
    --dry-run) _kip_kapisi "$_arg"; MOD="dry" ;;
    --uygula)  _kip_kapisi "$_arg"; MOD="uygula" ;;
    --kirli-gec) KIRLI_GEC=true ;;
    *)
      echo "!! Bilinmeyen bayrak: $_arg"
      _kullanim
      exit 2
      ;;
  esac
done
if [[ -z "$MOD" && "$KIRLI_GEC" == true ]]; then
  echo "!! --kirli-gec yalnız --uygula ya da --dry-run ile birlikte verilir."
  _kullanim
  exit 2
fi
# Bayraksız çağrı = kuru koşum. Eski betiğin davranışı BİREBİR korunur (docs/RUNBOOK.md ve
# operatör alışkanlığı `./dagit.sh`i "göster, dokunma" diye tanır); değişen tek şey kuru koşumu
# artık playbook'un `--check`inin yapmasıdır.
[[ -z "$MOD" ]] && MOD="dry"

echo "=== dagit.sh EMEKLİ OLACAK — deploy/ansible/dagit.yml'e yönlendiriyor; bir sürüm sonra silinir ==="
echo "  kapılar, listeler ve gövdeler playbook'ta; bu betik yalnız çağrıyı kurar."

if [[ ! -x "$ANSIBLE" ]]; then
  echo "!! DURDU: ansible-playbook yok ($ANSIBLE) — kur: uv sync --group dev"
  echo "   Koleksiyon da gerekir: ansible-galaxy collection install -r deploy/ansible/requirements.yml"
  exit 1
fi

KOMUT=("$ANSIBLE" -i "$ENVANTER" "$PLAYBOOK")
[[ "$MOD" == "dry" ]] && KOMUT+=(--check)
KOMUT+=(--diff)
[[ "$KIRLI_GEC" == true ]] && KOMUT+=(-e kirli_gec=true)

cd "$REPO"
echo "  ${KOMUT[*]}"
# ÇIKIŞ KODU AYNEN DÖNER: `set -e` altında son komutun kodu betiğin kodudur. Playbook'un hükmünü
# yeniden yorumlayan bir katman (özet basıp 0 dönen bir sarmalayıcı) kapıları sessizce açardı.
"${KOMUT[@]}"
