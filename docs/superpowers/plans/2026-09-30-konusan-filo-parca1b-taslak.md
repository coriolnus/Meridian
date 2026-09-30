# Konuşan bot filosu — Parça 1b TASLAK plan (K-1 kararı bekliyor)

> **Durum:** TASLAK (Rol-1, 2026-09-30 gece). writing-plans biçimindeki tam plan (adım adım kod + test) K-1 kararından SONRA bu taslaktan
> üretilir; bu belge sabah kararı hızlandırmak için görevleri, bağımlılıkları ve kabul ölçütlerini sabitler.
> **Spec:** `docs/superpowers/specs/2026-09-29-konusan-bot-filosu-design.md` · **Parça 0:** `…/2026-09-29-konusan-bot-filosu-parca0-olcum.md`
> (EN AĞIR BULGU + tarihli not) · **Hazır olan (main ee4da617, dağıtımsız):** kadro (v591), Telegram çekirdeği (v592), `bota_sor` + araçsız-veri
> uyarısı (v593), `is_iste` + `.path` (v594), `HindsightHafiza` (v596), test ortam-sızıntı bekçisi (v595).

## Karar kapısı K-1 (operatör) — bu planın yolu buna bağlı
- **(i) önerilen:** Hermes venv'ine `hermes-agent[mcp]` ekstrası (`mcp==1.26.0`, `starlette==1.3.1`) + canlı varsayılan profil
  `~/.hermes/config.yaml` `mcp_servers.meridian`ına `enabled: false` (depo `deploy/hermes/config.yaml` ile AYNI değişiklik, tek kaynak) →
  öğrenme/bileşik ön-eleme/pano 'düşün' yollarının davranışı DEĞİŞMEZ; bot sohbet profilleri Meridian MCP'yi kendi izin listesiyle açar.
- (ii) kur ve varsayılan profilin de kullanmasına izin ver (ayrı ölçüm kartı gerekir).
- (iii) kurma → taşıyıcı pano sohbet motoru (`sohbet.py`) olur; Görev 2–4 Hermes yerine `SohbetTasiyici` ile yeniden yazılır.
Aşağısı (i) içindir.

## Görevler (sıra; her biri kendi TDD + görev incelemesi; sonda son Opus incelemesi, tam suite, push)

**G0 — A1 kurulum (Rol-1/operatör; sınıflandırıcı engellerse tek komut reçetesi).** Hermes venv `uv pip install 'mcp==1.26.0' 'starlette==1.3.1'`;
`~/.hermes/config.yaml` meridian `enabled: false`. KABUL: `tools.mcp_tool._MCP_AVAILABLE=True`; varsayılan profil koşumunda MCP bağlanmıyor
(INFO günlüğü); deneme v3 (bekçi ikizi, izin listesi `meridian`) → (b) GEÇER: oturumda en az bir gerçek `role: tool` sonucu + cevap araç verisine
dayanıyor (POZİTİF KONTROL); (e) bankada ham araç JSON'u yok; hafızadan geri çağırma sohbet SOUL bölümüyle ölçülür.

**G1 — Meridian araç sunucusu, bot başı alt küme (`meridian/mcp_server.py`).** `sohbet.py` okuma araçları TEK KAYNAKTAN (ithal), `oneri_yaz`
(aynı `approvals.jsonl` yolu, `kaynak` = bot adı), `is_iste` (`is_istek.is_iste`, `kanal` bilinmiyorsa `None` + neden — uydurma yok),
`bot_hafizasi_ara` (yalnız `hafiza: hepsi`); `--bot <ad>` argümanı `kadro.araclar`a göre `tools/list` süzer, `tools/call` dışarıdakini reddeder;
çıktılar VERİ çiti + `scrub` + boyut tavanı. KABUL: alt küme iki yönlü çivili; dışarıdaki araç çağrısı reddedilir; çit sızmaz.

**(2026-09-30 06:3xZ v3 notu: K-1 uygulandı, (b) GEÇTİ; `-z` yolu hafızaya YAZABİLİYOR → ikiz profil ZORUNLU; ücretsiz model ~5 dk asılabiliyor → G2 config'ine kapı `request_timeout_seconds` + yedek model zinciri, G3 birimine `TimeoutStopSec`/`KillMode`, G4 Telegram'a ara bildirim.)**

**G2 — Sohbet profilleri üreteci (`ops/sohbet_profili_uret.py`).** Rapor profili (`deploy/hermes/profiles/<ad>/`) DEĞİŞMEZ; üreteç `<ad>-sohbet`
ikizini TÜRETİR: SOUL = rapor SOUL'u + donuk "## Sohbet kipi" bölümü (hafızan var; hafızadan söylenen her şey TARİHLİ; BUGÜN hakkında yalnız
araçla konuş; aracın yoksa "bilmiyorum" de, asla sonuç yazma), config = rapor config + `mcp_servers.meridian --bot <ad>` + `platform_toolsets.api_server:
[meridian]` + `memory.provider: hindsight` (`local_external`, banka `bot-<ad>`, `memory_mode: context`, `recall_budget: low`, `timeout: 10`) +
istek dökümü kapalı (Hermes anahtarı ölçülür). `--kontrol` kipi (RUNBOOK emsali) + çivi: üretilmiş ≡ depo. Neden ikiz: (d) `-z` yolunun hafızadan
OKUYUP okumadığı ölçülmedi; rapor profili hafızasız kalmalı (2026-08-31 değerlendirmesi). KABUL: `-z` rapor koşumu hafızasız (ölçüm), sohbet
profili hafızalı.

**G3 — Bot sunucusu birimi (`deploy/oracle-a1/meridian-botlar.service` + A0).** `hermes gateway run` multiplex (yalnız sohbet profilleri),
127.0.0.1:8642, `API_SERVER_KEY` ve Hindsight kiracı anahtarı `LoadCredential` (yeni sır → `deploy/sir_envanteri.yaml` + Vault), BOT_KEY'ler
profil `.env`inden (Hermes kapsamı), sertleştirme + `ReadWritePaths` (v553 sınıfı). A0 `birim_kaynaklari` + (ayrı değişiklikle) `etkin_birimler`.
KABUL: ELLE test-ateşleme (CLAUDE.md §9): `/health` 200, `/p/<bot>/v1/toolsets` yalnız meridian, bir soru → gerçek araç sonucu.

**G4 — Kanal kablolaması.** (a) `bota_sor` üretim varsayılanları `HermesTasiyici()` + `HindsightHafiza()`; (b) araçsız-veri turunu hafızaya
`arac_siz_veri` etiketiyle bota_sor KENDİSİ yazar (Hermes otomatik kaydı uyarısız cevabı saklıyor — son inceleme M-2); (c) `unut:` İKİ ADIM:
ilk mesaj adayları listeler + "onayla: unut <kısa kod>" ister; Telegram yanıtında alıntı metni sorgu olur (son inceleme M-1); operatöre
`geri al: <kısa kod>` komutu; (d) `bot_hafiza_*_hatasi` olaylarına kapalı-küme `neden`; PATCH hatasında denenen id'ler deftere;
(e) `meridian-telegram.service` + `main()` (ReadWritePaths `state/`, credential'lar, 4096 bölme, ilk koşum ofseti, canlı `TELEGRAM_CHAT_ID`
pozitif mi ölçümü, pano getUpdates kurulum talimatı güncellemesi). KABUL: Telegram'dan `@bekci durum?` → gerçek araçlı cevap; rapora yanıt →
doğru bot + alıntı bağlamı; `hatırla:`/`unut:` iki yönlü; yabancı sohbet sessiz + sayaç.

**G5 — Ölçüm kartı EDG-2026-107 (Rol-1, ilk canlı günden ADIM-0 ile).** Metrikler: soru/bot, süre, öneri→onay, `arac_olculemedi` oranı (kendi
eşiği), `arac_siz_veri is True` satırları (sıfır tolerans adayı yalnız rakam/yüzde/kaynak/sembol — ADIM-0 yanlış-pozitif oranıyla),
`veri_isareti is None ∧ arac=0` örneklemesi (kaçan nitel uydurma), hafızadan BUGÜN hükmü (kill). Pozitif kontrol: bilinen olgu → tarihli geri çağrı.

**G6 — Dağıtım + test-ateşleme listesi.** `.path` 8 maddelik liste (`.superpowers/sdd/2026-09-29-konusan-filo-parca1a-kanal-cekirdegi/task-2-review.md`),
`.path` etkinleştirmesi zamanlayıcı durumuna bağlı (brifing_devri kararı), dagit drift kapısının `.path`i görmesi, Vault `agent.hcl` yorum farkı
(`vault_kur.sh`), retain gecikmesi ölçümü.

## Sonra
Parça 3 (pano bot seçici + hafıza görünümü), Parça 4 (TSK-010 filo MCP, Mac), Dalga 1 profilleri (TSK-061) — her biri bu çekirdeğin üstüne.
