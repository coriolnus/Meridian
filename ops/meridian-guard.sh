#!/bin/bash
# meridian-guard.sh — hermes-agent pre_tool_call KORUMA HOOK'u (Meridian, 2026-07-20).
#
# Kapı yasasını HARNESS düzeyinde ZORLAR: ajanı yalnız-öneri diye prompt'la sınırlamak ricadır; bu hook
# mekanizmadır. Ajanın terminal/dosya araçlarıyla Meridian'ın KORUNAN yüzeylerine dokunmasını SERT bloklar:
#   • state/ altına YAZMA — TÜMÜ (2026-08-30'da GERÇEKTEN tümü oldu; bkz. aşağıdaki şerh)
#   • secrets.json / API anahtarları
#   • MERIDIAN_MODE / MERIDIAN_I_ACCEPT_RISK / autonomy_level (gerçek-para kapıları — yalnız operatör)
#   • alpaca emir gönderimi / close_all / submit_bracket (canlı emir yetkisi)
#
# Girdi: stdin'de JSON {tool_name, tool_input:{command|path|file_path|content}, ...}.
# Çıktı: izin → {} ; blok → {"decision":"block","action":"block","reason":..,"message":..} (iki şema da).
# Parse edilemezse fail-open (boş {}) — ajanı büsbütün kilitlemeyiz; asıl savunma desen eşleşmesidir.
#
# BAŞLIĞIN İDDİASI ile GERÇEK KAPSAM 2026-08-30'a KADAR AYRIŞIKTI, ve bu şerh o günün kaydıdır.
# Üstteki ilk madde "state/ altına YAZMA" diyordu; hedef deseni ise YALNIZ ADI SAYILAN yedi
# aileyi blokluyordu. ÖLÇÜM: `state/` altında 87 dosya, 24'ü üretim kodunca yazılıyor ve
# korumasız kalanlar arasında `trades.jsonl` (İŞLEM DEFTERİ), `equity_curve.json`,
# `scoreboard.json` (`update_scoreboard` KİLİTSİZ), `trade_plans.jsonl`, `notify_undelivered.json`
# vardı. Tutarsızlık tek cümlede: `portfolio.json` KORUMALI, `trades.jsonl` DEĞİL — ikisi aynı
# sınıf kanıttır. Kendi başlığında yazan ama tutulmayan bir söz, olmayan bir kapıdan DAHA
# KÖTÜDÜR: okuyan onu okur ve korunduğunu sanır.
# HÜKÜM: kapsamı GENİŞLET, başlığı indirme. İki ölçüme dayanır.
#   (a) ÜRETİMİ KIRMAZ: o 24 dosyanın hepsi Meridian'ın KENDİ Python kodundan yazılır ve o
#       yazımlar `pre_tool_call`a HİÇ uğramaz — bu kanca yalnız AJANIN araçlarını görür.
#   (b) ARIZA ASİMETRİSİ: fazla bloklamak ajana GÖRÜNÜR bir ret verir (mesaj MCP'yi adıyla
#       söyler, geri alınabilir); az bloklamak operatöre sunulan kanıtı SESSİZCE tahrif eder.
# NASIL, kör değil keskin: `tool_name` artık ÇIKARILIYOR (şerhte hep yazılıydı, hiç okunmuyordu —
# okuma/yazma ayıramamanın kökü buydu). Yapısal yazma araçları `state/` altına HİÇ yazamaz;
# `terminal` için YALNIZ YAZMA ŞEKLİ bloklanır (`>` `>>` `tee` `sed -i` `rm/mv/cp/truncate/dd`),
# `cat`/`grep`/`jq` SERBEST kalır. Adı sayılan ailelerin TÜM-ERİŞİM bloğu aynen DURUR.
# Çiviler: tests/test_authority_boundaries_v77.py, C3-b bölümü (dördü de kancayı GERÇEKTEN koşturur).

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

# ARAÇ SINIFI (2026-08-30): `tool_name` şerhte hep yazılıydı ama HİÇ ÇIKARILMIYORDU — bu yüzden
# kanca okuma ile yazmayı ayıramıyor ve `state/` kapsamı ad-ad genişletilmek zorunda kalıyordu.
tool="$(printf '%s' "$payload" | jq -r '.tool_name // empty' 2>/dev/null)"
if [ -z "$tool" ]; then
  # tool_name yoksa GİRDİ ANAHTARLARINDAN çıkar (mevcut çiviler onu göndermiyor, gerçek payload'da
  # da eksik olabilir). İkisi de yoksa YAZMA varsay: sınıflandıramadığımızda tehlikeli olanı
  # varsaymak sınıflandırmayı fail-CLOSED yapar. Genel parse fail-OPEN'ı BOZMAZ — o aynen durur.
  if printf '%s' "$payload" | jq -e '.tool_input.command' >/dev/null 2>&1; then
    tool="terminal"
  else
    tool="write_file"
  fi
fi

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

# 5) state/ VARSAYILAN-RET — YAZMA ŞEKLİ (2026-08-30 denetimi).
# ÖLÇÜLEN BOŞLUK: `state/` altında 87 dosya var, yukarıdaki desen 7 ad ailesini kapsıyordu ve
# 24 KORUMASIZ dosya üretim kodunca yazılıyordu — aralarında `trades.jsonl` (İŞLEM DEFTERİ),
# `equity_curve.json`, `scoreboard.json` (kilitsiz), `trade_plans.jsonl`, `notify_undelivered.json`.
# `portfolio.json` korumalıyken `trades.jsonl`in korumasız olması bir hüküm değil bir EKSİKTİ:
# ikisi aynı sınıf kanıttır ve kancanın kendi başlığı zaten "state/ altına YAZMA" diyordu.
# ÜRETİMİ KIRMAZ, ölçüldü: o 24 dosyanın hepsi Meridian'ın KENDİ Python kodundan yazılıyor ve o
# yazımlar `pre_tool_call`a hiç uğramaz — kanca YALNIZ ajanın araçlarını görür.
# OKUMA SERBEST KALIR: yalnız YAZMA ŞEKLİ bloklanır. Adı sayılan aileler (yukarısı) tüm-erişim
# bloklu KALIR; bu katman onların dışındaki state dosyalarını yazmaya karşı kapatır.
if printf '%s' "$tgt" | grep -qiE '(^|[^A-Za-z0-9_./-])state/'; then
  # VAKA TERSİNE ÇEVRİLDİ (kendi doğrulamamda bulundu): yazma araçlarını SAYIP gerisini serbest
  # bırakmak, YARIN EKLENECEK bir aracı sessizce serbest bırakmaktır — `disabled_toolsets`in
  # kara-liste zaafının aynısı. Burada BELİRSİZLİK BLOKLAR: yalnız KABUK sınıfı ad ad sayılır
  # (hedefi ancak komut şeklinden anlaşılan tek sınıf odur), geri kalan HER ŞEY yazma sayılır.
  # Kanca zaten yalnız config'teki matcher'ın saydığı araçlar için çağrılır; bilinmeyen bir ad
  # görmek "matcher genişletildi ama kanca güncellenmedi" demektir ve bunun SESSİZ kalmaması
  # gerekir — ret mesajı durumu adıyla söyler.
  case "$tool" in
    terminal|bash|shell|sh|run_command|run_terminal_cmd|execute_command)
      printf '%s' "$tgt" | grep -qE '>>?[[:space:]]*[^|&;]*state/|[|][[:space:]]*tee[[:space:]]+[^|&;]*state/|sed[[:space:]]+-i|(^|[^A-Za-z0-9_-])(rm|mv|cp|truncate|dd|install|chmod|chown)([[:space:]]+-[^[:space:]]+)*[[:space:]]+[^|&;]*state/' && \
        block "Meridian koruması: state/ altına kabuktan YAZMA/SİLME ajana kapalıdır — defterler operatöre sunulan kanıttır (okuma serbest)."
      ;;
    *)
      block "Meridian koruması: state/ altına YAZMA ajana kapalıdır — defterler ve karne operatöre sunulan kanıttır (okuma için meridian_* MCP araçları). Araç sınıfı '"'"'$tool'"'"' KABUK olarak tanınmadı; matcher genişletildiyse bu kanca da güncellenmelidir." ;;
  esac
fi

# aksi halde izin
printf '{}\n'
