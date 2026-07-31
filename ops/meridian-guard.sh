#!/bin/bash
# meridian-guard.sh — hermes-agent pre_tool_call KORUMA HOOK'u (Meridian, 2026-07-20).
#
# Kapı yasasını HARNESS düzeyinde ZORLAR: ajanı yalnız-öneri diye prompt'la sınırlamak ricadır; bu hook
# mekanizmadır. Ajanın terminal/dosya araçlarıyla Meridian'ın KORUNAN yüzeylerine dokunmasını SERT bloklar:
#   • state/ altına YAZMA (portfolio, strategy.yaml, goal.yaml, bounds.yaml — Hermes'e değişmez)
#   • secrets.json / API anahtarları
#   • MERIDIAN_MODE / MERIDIAN_I_ACCEPT_RISK / autonomy_level (gerçek-para kapıları — yalnız operatör)
#   • alpaca emir gönderimi / close_all / submit_bracket (canlı emir yetkisi)
#
# Girdi: stdin'de JSON {tool_name, tool_input:{command|path|file_path|content}, ...}.
# Çıktı: izin → {} ; blok → {"decision":"block","action":"block","reason":..,"message":..} (iki şema da).
# Parse edilemezse fail-open (boş {}) — ajanı büsbütün kilitlemeyiz; asıl savunma desen eşleşmesidir.

payload="$(cat -)"

# İki tarama yüzeyi:
#  scan  = komut + hedef yol + içerik → her zaman tehlikeli desenler (mode/secrets/emir) için
#  tgt   = komut + hedef yol (İÇERİK HARİÇ) → korunan durum DOSYASI hedefi için (içerik yanlış-pozitifi olmasın)
scan="$(printf '%s' "$payload" | jq -r '
  [.tool_input.command // empty, .tool_input.path // empty,
   .tool_input.file_path // empty, .tool_input.content // empty] | join("\n")' 2>/dev/null)"
tgt="$(printf '%s' "$payload" | jq -r '
  [.tool_input.command // empty, .tool_input.path // empty,
   .tool_input.file_path // empty] | join("\n")' 2>/dev/null)"

# jq başarısızsa ham payload üstünden tara (denylist yine çalışsın)
[ -z "$scan" ] && scan="$payload"
[ -z "$tgt" ] && tgt="$payload"

block() {
  printf '{"decision":"block","action":"block","reason":%s,"message":%s}\n' \
    "$(jq -Rn --arg m "$1" '$m')" "$(jq -Rn --arg m "$1" '$m')"
  exit 0
}

# 1) gerçek-para / özerklik kapıları — hiçbir koşulda ajan eline geçmez
printf '%s' "$scan" | grep -qiE 'MERIDIAN_(MODE|I_ACCEPT_RISK)|autonomy_level' && \
  block "Meridian koruması: gerçek-para/özerklik kapıları yalnız operatöre aittir."

# 2) sırlar
printf '%s' "$scan" | grep -qiE 'secrets\.json|ALPACA_[A-Z_]*KEY|ANTHROPIC_API_KEY|GEMINI_API_KEY|HERMES_API_KEY' && \
  block "Meridian koruması: sırlara (secrets.json / API anahtarları) erişim engellendi."

# 3) canlı emir yüzeyi
printf '%s' "$scan" | grep -qiE 'close_all|submit_bracket|submit_plan|/v2/orders|alpaca.*(submit|order|close)' && \
  block "Meridian koruması: canlı emir gönderimi/iptali yalnız döngünün yetkisidir."

# 4) korunan durum dosyalarına dokunma. write_file/patch = doğrudan yazma (verb gerekmez); terminal'de
#    okuma bile MCP'ye yönlendirilir (ajan state'e shell'lememeli — salt-okuma için meridian_* araçları var).
# KİLİT ANAHTARLARI ve YETKİ TAŞIYAN DOSYALAR da listede (2026-07-22, yetki denetimi bulgusu F1):
#   * HALT / LEARN_HALT — operatörün kill switch'i. Ajan `rm -f state/HALT` yazabiliyordu ve hook
#     buna İZİN veriyordu; yani durdurulmuş bir motoru kendi kendine yeniden başlatabilirdi.
#   * llm_calibration.json — `analytics.llm_promoted()` bu dosyadaki `promoted` boole'sini okur ve
#     `loop._llm_veto_filter` LLM'in TEK canlı yetkisini ona bağlar. Ajan dosyaya `{"promoted":true}`
#     yazarak 30-çift/0.3R kalibrasyon kuralını atlayıp o yetkiyi KENDİNE verebiliyordu.
#   * skills_registry.json — korunan beceri kaydı.
printf '%s' "$tgt" | grep -qiE 'state/(portfolio|strategy|goal|bounds|secrets|llm_calibration|skills_registry)|state/(HALT|LEARN_HALT)|(^|/)(goal|bounds|strategy)\.yaml|(^|/)secrets\.json' && \
  block "Meridian koruması: korunan durum dosyalarına erişim engellendi (okuma için MCP araçlarını kullan; goal/bounds Hermes'e değişmezdir; HALT/kalibrasyon yetki taşır)."

# aksi halde izin
printf '{}\n'
