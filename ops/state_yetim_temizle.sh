#!/usr/bin/env bash
# state_yetim_temizle.sh — `state/` içindeki YEDEK ARTIKLARINI `backups/state/`e TAŞIR (silmez).
#
# NEDEN VAR (MAKULLÜK bulgusu 1, 2026-08-07). `yeniden_hesap:orphan_state_files` canlıda 7 dosya
# sayıyordu ve ALTISI bizim artığımızdı: `dagit.sh` versiyonlu state kopyasının yedeğini
# `state/` İÇİNE yazıyordu (yani dedektörün taradığı dizine), bir de bakım penceresindeki bir
# `sed` iki dosya bırakmıştı. Kaynak `dagit.sh`ta onarıldı (yedek artık `backups/state/`e gider);
# bu betik ONARIMDAN ÖNCE DOĞMUŞ artıkları toplar.
#
# TAŞIR, SİLMEZ. Bu dosyalar GERİ DÖNÜŞ KOPYALARIDIR: `goal.yaml.bak-202608021652`, canlı motorun
# o dağıtımdan önceki yazılı yasasıdır. Silmek, geri dönüş yolunu kesmek olurdu. Taşımak dedektörü
# susturmaya YETER (tarama `state/` dizinine bakar) ve kanıtı korur.
#
# YALNIZ YEDEK SONEKLİ DOSYALAR — CANLI ARTEFAKT ASLA. Desen listesi ÖLÇÜLDÜ, uydurulmadı: canlıda
# görülen artıkların tamamı bu üç sonektendir. Özellikle `auth.json` bu betikle TAŞINMAZ: dedektör
# onu da orphan sayıyor ama o bir yedek değil, panonun CANLI kimlik dosyasıdır (kararı: kod
# tarafında beyan — `codelaw.DECLARED_SINKS`). Taşınsaydı operatör panosuna giremezdi.
#
# KURU KOŞU VARSAYILAN. Argümansız çağrı hiçbir şeye dokunmaz; yalnız ne yapılacağını yazar.
#
# KULLANIM
#   bash ops/state_yetim_temizle.sh                 # A1'e SSH, kuru koşu (varsayılan)
#   bash ops/state_yetim_temizle.sh --uygula        # A1'de TAŞI (bakım penceresinde)
#   bash ops/state_yetim_temizle.sh --yerel <kök>   # SSH yok: verilen kökte çalış (test/host-içi)
#
# CANLI WORKER: bu betik defterlere YAZMAZ, yalnız yedek dosyalarını YENİDEN ADLANDIRIR. Yine de
# bakım penceresinde koşulması istenir — bir yedeği okurken taşımak (nadir de olsa) yarış üretir.
set -euo pipefail

KEY="${MERIDIAN_A1_KEY:-$HOME/.ssh/oci-a1.key}"
IP="${MERIDIAN_A1_IP:-130.61.126.87}"
UZAK_KOK="${MERIDIAN_A1_DIR:-/opt/meridian}"

UYGULA=0
MOD="uzak"
KOK="$UZAK_KOK"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --uygula) UYGULA=1; shift ;;
    --yerel)  MOD="yerel"; KOK="${2:?--yerel bir kök dizin ister}"; shift 2 ;;
    *) echo "!! bilinmeyen argüman: $1"; exit 2 ;;
  esac
done

# TEK KOMUT YÜZEYİ: aynı gövde hem SSH'ın ötesinde hem yerelde koşsun — iki kopya gövde zamanla
# ayrışır (bu depoda adı konmuş hata sınıfı: aynı yasanın iki uygulaması).
_kos() {
  if [[ "$MOD" == "uzak" ]]; then
    ssh -i "$KEY" -o ConnectTimeout=15 "ubuntu@$IP" "$1"
  else
    bash -c "$1"
  fi
}

STATE="$KOK/state"
YEDEK="$KOK/backups/state"
# Desenler ÖLÇÜLDÜ (canlı liste 2026-08-07): dagit damgası (`*.bak-<damga>`), elle `sed` yedeği
# (`*.sedbak`), tarihli tek yedek (`*.bak`). TEK TIRNAK ŞART: tırnaksız desen, betiğin koştuğu
# dizinde eşleşen bir dosya varsa KABUK tarafından genişletilir ve find hiç görmez.
DESEN="-name '*.bak-*' -o -name '*.sedbak' -o -name '*.bak'"
BUL="find '$STATE' -maxdepth 1 -type f \\( $DESEN \\) 2>/dev/null"

echo "=== state yetim temizliği · mod=$MOD · kök=$KOK · $([[ $UYGULA == 1 ]] && echo UYGULA || echo 'KURU KOŞU') ==="

echo "--- [1/4] ÖNCESİ: state/ içindeki yedek artıkları ---"
_ONCE="$(_kos "$BUL | sed 's|.*/||' | sort" || true)"
_N_ONCE="$(printf '%s\n' "$_ONCE" | grep -c . || true)"
if [[ "$_N_ONCE" == "0" ]]; then
  echo "  · yedek artığı YOK — taşınacak dosya yok"
else
  _kos "$BUL -exec ls -l {} + 2>/dev/null" | sed 's/^/  /' || true
  echo "  toplam: $_N_ONCE dosya"
fi

# ÖLÇÜLEMEDİ ≠ TEMİZ (UYDURMA YASAĞI): dedektör koşamazsa sayı UYDURULMAZ, sebebi yazılır.
_DEDEKTOR="cd '$KOK' && uv run python -c \"
import json
from meridian import recompute
r = [x for x in recompute.report()['rows'] if x['check'] == 'orphan_state_files']
print(json.dumps(r[0] if r else {'hata': 'orphan_state_files satırı YOK'}, ensure_ascii=False))
\""
# KÖK GERÇEKTEN BİR MERIDIAN CHECKOUT'U MU? Değilse dedektör ADIMI ATLANIR — `uv run` boş bir
# dizinde ortam kurmaya kalkar (ağ + saniyeler) ve çıktısı zaten "modül yok"tan ibaret olurdu.
# Atlama SESSİZ DEĞİL: aşağıda adıyla yazılır, "temiz" ile karıştırılamaz.
_DEDEKTOR_VAR=1
if ! _kos "test -d '$KOK/meridian'" >/dev/null 2>&1; then _DEDEKTOR_VAR=0; fi
_dedektor_yaz() {
  if [[ "$_DEDEKTOR_VAR" != "1" ]]; then
    echo "  · dedektör ADIMI ATLANDI: '$KOK' bir Meridian checkout'u değil (yalnız state temizliği ölçüldü)"
    return 0
  fi
  _kos "$_DEDEKTOR" 2>&1 | sed 's/^/  /' || echo "  !! dedektör ÖLÇÜLEMEDİ (uv/meridian koşmadı) — sayı uydurulmaz"
}
echo "--- [2/4] dedektör (ÖNCE) ---"
_dedektor_yaz

if [[ "$UYGULA" != "1" ]]; then
  echo "--- [3/4] TAŞIMA: kuru koşu, hiçbir şey yapılmadı ---"
  if [[ "$_N_ONCE" != "0" ]]; then
    printf '%s\n' "$_ONCE" | while IFS= read -r _f; do
      [[ -n "$_f" ]] && echo "  mv $STATE/$_f  →  $YEDEK/$_f"
    done
  fi
  echo "--- [4/4] SONRASI: kuru koşuda ölçülmez (taşıma olmadı) ---"
  echo ">> KURU KOŞU BİTTİ. Uygulamak için: bash ops/state_yetim_temizle.sh --uygula"
  exit 0
fi

echo "--- [3/4] TAŞIMA (mv — kopya DEĞİL, silme DEĞİL) ---"
if [[ "$_N_ONCE" == "0" ]]; then
  echo "  · taşınacak dosya yok"
else
  # `mkdir -p` + `mv -n`: aynı adlı bir yedek zaten oradaysa ÜSTÜNE YAZILMAZ. Bir geri-dönüş
  # kopyasını başka bir geri-dönüş kopyasıyla ezmek, temizliğin veri kaybına dönüştüğü andır.
  _kos "mkdir -p '$YEDEK' && $BUL -exec mv -n {} '$YEDEK'/ \\; && echo '  ✓ taşındı'"
fi

echo "--- [4/4] SONRASI ---"
_SONRA="$(_kos "$BUL | sed 's|.*/||' | sort" || true)"
if [[ "$(printf '%s\n' "$_SONRA" | grep -c . || true)" == "0" ]]; then
  echo "  ✓ state/ içinde yedek artığı KALMADI"
else
  echo "  !! HÂLÂ DURAN dosyalar (taşınamadı — hedefte aynı ad olabilir):"
  printf '%s\n' "$_SONRA" | sed 's/^/    /'
fi
echo "  yedek dizini içeriği:"
_kos "ls -l '$YEDEK' 2>/dev/null" | sed 's/^/    /' || echo "    (okunamadı)"

echo "--- dedektör (SONRA) — sayı DÜŞTÜ mü? ---"
_dedektor_yaz
echo "=== BİTTİ. Not: kalan orphan varsa (ör. auth.json) o AYRI bir haldir — beyan/karar işi. ==="
