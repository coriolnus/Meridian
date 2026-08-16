#!/usr/bin/env bash
# ci_duman.sh — CI DUMAN KAPISI (2026-08-15).
#
# NEDEN VAR. Tam suite 4 çekirdekte ~50 dk sürer ve canlı-benzeri `state/` + lokal hermes-agent +
# doğrudan ağ varsayar (ölçüm ve küme sınıflandırması: docs/MODUL-ENVANTERI-2026-08-15.md §5).
# CI'ın 15 dk sınırı bu paketi HİÇ bitirememişti — her koşu zaman aşımıyla iptal oluyordu, yani
# fiilen kapı yoktu. Bu betik CI'ın gerçekten BİTİREBİLECEĞİ, state-bağımsız duman kapısıdır.
#
# BU TAM SUITE DEĞİLDİR VE ONUN YERİNE GEÇMEZ (CLAUDE.md kural 6: tam suite Rol-1'de tek-otoriter).
# Yerel hızlı kapı ops/kapilar.sh'tır; bu betik onun CI ikizidir — farkları: bayt-derleme taban
# kontrolü eklidir ve pytest kapsamı daha geniştir (CI'ın dakikaları vardır, operatörün saniyeleri).
#
# SIRA ucuzdan pahalıya; AMA İLK KIRMIZI KOŞUMU DURDURMAZ. Dört kapının HEPSİ koşar, hepsinin
# hükmü ekranda görünür ve kırmızılar sonda TEK bir `exit 1`e toplanır. Bu BİLİNÇLİ: bir turda
# tüm kapıların durumu bir kerede görülsün — kısa devre yapan bir kapı, ikinci kırmızıyı bir
# sonraki koşuma erteler ve turu gereksiz yere ikiye böler. Sıra yine de ucuzdan pahalıyadır,
# çünkü ucuz kapının hükmü saniyeler içinde ekrana düşer (bekleme değil, okuma sırası).
#   [1] compileall   (~5 sn)   — beyan edilen Python tabanında (>=3.11) SÖZDİZİMİ. CI, venv'i
#                                bilerek 3.11'e sabitler: 3.12+'da geçerli olup 3.11'de patlayan
#                                sözdizimi (PEP 701 f-string vakası, 2026-08-15) burada yakalanır.
#                                O vaka test TOPLAMASINI kesiyordu — tek satır, sıfır koşan test.
#   [2] lint-imports (~2 sn)   — 5 mimari sözleşme (pyproject [tool.importlinter]).
#   [3] uv audit     (~2 sn)   — tedarik zinciri. Gerçek bir açık bulunursa KIRMIZI: dağıtım da
#                                PR de bekler. Alt-komut bu uv sürümünde YOKSA sonuç KIRMIZI değil
#                                ÖLÇÜLEMEDİ'dir ve ekranda öyle görünür (aşağıdaki bloğa bak).
#   [4] pytest duman (~2-4 dk) — state-bağımsız çekirdek: anayasa property paketi (kapilar [3]
#                                ile aynı 6 dosya) + modül-yasası audit ailesi + bounds/seed
#                                çivileri + son regresyon sitesi. Ölçüldü (2026-08-15, 4 çekirdek):
#                                390 test · ~1 dk 50 sn · 0 kırmızı.
#
# LİSTE ELLE VE DAR TUTULUR — yavaşlayan kapı, atlanan kapıdır (kapilar.sh dersi). Dosya eklerken
# iki şart: (a) taze klonda state'siz geçtiği kanıtlı, (b) toplam süre < 5 dk kalmalı.
set -uo pipefail
cd "$(dirname "$0")/.."

UV="${UV:-uv}"
KIRMIZI=0

baslik() { printf '\n=== %s ===\n' "$1"; }

baslik "[1/4] compileall — beyan edilen Python tabanında sözdizimi"
if "$UV" run python -m compileall -q meridian tests; then
  echo "  ✓ 96 modül + test ağacı tabanda derleniyor"
else
  echo "!! SÖZDİZİMİ TABAN İHLALİ — requires-python tabanında derlenmeyen dosya var."
  echo "   (3.12+'da geçerli olabilir; taahhüt >=3.11'dir. 2026-08-15 f-string vakasına bak.)"
  KIRMIZI=1
fi

baslik "[2/4] lint-imports — mimari sözleşmeler"
if "$UV" run lint-imports; then
  echo "  ✓ sözleşmeler KORUNDU"
else
  echo "!! MİMARİ SÖZLEŞME KIRILDI — pyproject.toml [tool.importlinter]'a bak."
  KIRMIZI=1
fi

baslik "[3/4] uv audit — tedarik zinciri"
# ARAÇ YOKLUĞU İHLAL DEĞİLDİR — AMA SESSİZ YEŞİL DE DEĞİLDİR.
# Bu ortamdaki uv (0.8.17) `audit` alt-komutunu TANIMIYOR. Eski hâlde adım bu yüzden KALICI
# kırmızıydı: kapı her koşuda exit 1 veriyor, ama kırmızının ANLAMI ("bağımlılıkta bilinen açık
# var") ile GERÇEĞİ ("ölçen araç yok") ayrışıyordu. Sürekli kırmızı bir kapı, bakılmayan kapıdır —
# ve ölçülemeyen bir şeyi ihlal saymak UYDURMA YASAĞInın ihlalidir. Ayrım bir YOKLAMAYLA yapılır:
# alt-komut yoksa hüküm ÖLÇÜLEMEDİ'dir, KIRMIZI sayılmaz; alt-komut VARSA ve gerçek bir açık
# bulursa KIRMIZI sayılır. Ölçülemedi sessizce yeşile de yazılmaz: ekranda ADIYLA görünür, yoksa
# "denetlendi" ile "denetlenemedi" bir daha ayırt edilemezdi.
if "$UV" audit --help >/dev/null 2>&1; then
  if "$UV" audit --preview-features audit-command; then
    echo "  ✓ bilinen açık YOK"
  else
    echo "!! TEDARİK ZİNCİRİ KIRMIZI — bağımlılıkta bilinen açık var. Dağıtım da PR de bekler."
    KIRMIZI=1
  fi
else
  echo "  ? ÖLÇÜLEMEDİ (araç yok): bu uv sürümü '$UV audit' alt-komutunu tanımıyor."
  echo "    Sürüm: $("$UV" --version 2>/dev/null || echo 'okunamadı')"
  echo "    Tedarik zinciri bu koşumda DENETLENMEDİ — yeşil DEĞİL, ölçüsüz. uv yükseltilince"
  echo "    yoklama kendiliğinden geçer ve adım gerçek hüküm vermeye başlar."
fi

baslik "[4/4] pytest duman — state-bağımsız çekirdek (tam suite DEĞİL)"
if "$UV" run pytest -q \
    tests/test_anayasa_hypothesis_v143.py \
    tests/test_warmup_tavani_v143.py \
    tests/test_storage_v142.py \
    tests/test_storage_eszamanlilik_v142.py \
    tests/test_defter_kaynak_damgasi_v140.py \
    tests/test_bars_integrity_v141.py \
    tests/test_backtest_audit_v23.py \
    tests/test_config_audit_v25.py \
    tests/test_guard_audit_v27.py \
    tests/test_memory_audit_v32.py \
    tests/test_oos_pipeline_audit_v36.py \
    tests/test_probgate_audit_v35.py \
    tests/test_regime_audit_v37.py \
    tests/test_rollback_audit_v38.py \
    tests/test_score_audit_v40.py \
    tests/test_store_strategy_audit_v46.py \
    tests/test_gate_statistics_v74.py \
    tests/test_turnover_kablolama_v149.py \
    tests/test_wp2d_pano_beyani_v246.py \
    tests/test_firsat_yuzeyleri_v200.py; then
  echo "  ✓ duman kapsamı YEŞİL"
else
  echo "!! DUMAN KAPSAMI KIRMIZI — tam grep ile bak: pytest çıktısında FAILED|ERROR ara."
  KIRMIZI=1
fi

echo
if [[ "$KIRMIZI" -ne 0 ]]; then
  echo "=== CI DUMAN KAPISI KIRMIZI ==="
  exit 1
fi
echo "=== CI DUMAN KAPISI YEŞİL (tam suite'in YERİNE GEÇMEZ — Rol-1, CLAUDE.md kural 6) ==="
