#!/usr/bin/env bash
# =================================================================================================
# dash_token_credential.sh — EMEKLİ (2026-09-26, TSK-064): MEZAR TAŞI, hiçbir iş yapmaz
# =================================================================================================
# HER ÇAĞRI (argümansız eski DURUM dahil, her bayrak) tek bir açıklama basar ve ÇIKIŞ 2 ile döner:
# hiçbir dosya okumaz ya da yazmaz, sudo/systemctl/curl çağırmaz. Gövde yalnız bash yerleşikleridir
# (set · printf · exit) — çivi: tests/test_dash_token_betigi_v559.py.
#
# YERİNE NE:
#   rotasyon → sudo deploy/oracle-a1/sir_rotasyon.sh --dash --vault --uret   (önce --kuru ile)
#              Değer betik İÇİNDE üretilir, hiçbir yere basılmaz, ÖNCE kasaya yazılır; render ölçümü,
#              yeni/eski jeton kanıtı ve sürümlü geri alma o betiktedir.
#   kanal    → Vault Agent render'ı → /etc/meridian/dash_token → meridian.service LoadCredential
#              (meridian.service.d/50-dash-credential.conf).
#   kurulum  → drop-in'leri A0 rolü kurar (deploy/ansible/roles/meridian_a1/tasks/dropinler.yml).
#   durum    → sudo deploy/oracle-a1/sir_rotasyon.sh --envanter  +  systemctl show meridian -p LoadCredential
#
# NEDEN EMEKLİ: geçiş bitti. LoadCredential canlıda (TSK-049, 2026-09-01), ortam kanalını
# 51-dash-env-kaldir.conf kapattı, `.dash.env` A1'de 2026-09-14'te silindi ve kaynak dosyayı artık
# Vault Agent yazar. Bu düzende eski --faz1 ve --faz2 `.dash.env` yok diye düşüyordu; --geri-al ise
# ZARARLIYDI: tek kanalı (50 drop-in'i) kaldırıp pano jetonunu boşa düşürürken "ortam kanalı
# yürürlükte" diyordu (model ölçümü + kod okuması, 46120fb4 — A1'de koşulmadı).
#
# NEDEN SİLİNMEDİ: tarihsel belgeler ve mühendislik günlüğünden RUNBOOK'a alıntılanan bir pano jetonu
# kurtarma yönergesi bu yolu gösteriyor. Dosya yerinde kalınca o yönergeyi izleyen operatör "dosya yok"
# yerine doğru yolu bulur.
#
# TARİHÇE (değer yok): 2026-08-03'te doğdu (WP-H/H3 tur-3). Argümansız mod kanalların durumunu (dosya
# izinleri, drop-in'ler, LoadCredential, servis) gösterirdi; --faz1 jetonu döndürür, credential
# kaynağını ve `.dash.env`i aynı değere çeker, 50 drop-in'ini kurup yeni jetonla /api/hermes 200'ü
# ölçerdi; --faz2 ortam kanalına sahte değer koyup gerçek credential'la farksal ölçüm yapar, geçerse
# 51'i kurardı; --geri-al iki drop-in'i kaldırırdı. Farksal kanal ölçümü deseni sir_credential_gecis.sh'te
# genelleştirilmiş hâliyle yaşar; eski gövde git geçmişindedir (son hâli 8ccbbb15).
set -euo pipefail

MESAJ="EMEKLİ (2026-09-26, TSK-064): pano jetonu rotasyonu artık \`sudo deploy/oracle-a1/sir_rotasyon.sh --dash --vault --uret\` (önce \`--kuru\`); kanal Vault Agent render'ı → \`/etc/meridian/dash_token\` (LoadCredential)"

printf '%s\n' "$MESAJ" >&2
exit 2
