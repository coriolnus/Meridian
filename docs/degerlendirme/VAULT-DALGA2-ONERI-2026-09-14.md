# Vault dalga-2 kapsam ÖNERİSİ — operatör kararı için (Rol-1, 2026-09-14 13:1xZ)

**Durum:** Faz-2 dalga-1 CANLI (2026-09-14 10:19Z): 7 sır Vault'ta, Agent `/etc/meridian/*` ve `/etc/hindsight/creds/*` dosyalarını
0400 root:root render ediyor; canary geçti; kök jetonu iptal, yönetim `admin.token` (orphan, TTL 720h, yenileme 2026-10-14 öncesi).
Bu belge **karar istemez, seçenek sunar**: dalga-2'nin kapsamı ve sırası operatörün (hafıza `vault-sir-yonetimi-karari`).
Kaynak: `deploy/sir_envanteri.yaml` (yalnız DEĞİŞKEN ADLARI; değer hiçbir yerde basılmadı).

## Vault DIŞINDA kalan sırlar (envanter, ad bazında)

| Dosya (A1) | Tüketici | Sır adları | Kopya sorunu |
|---|---|---|---|
| `/opt/hindsight/.env` | hindsight-api.service | `HINDSIGHT_API_{REFLECT,CONSOLIDATION}_LLM_{1,2,3}_API_KEY` (6, OpenRouter) | 09-08 rotasyonu 14 kopyadan 6'sı burada |
| `/opt/apisix/.env-apisix` | apisix (docker `$env://`) + `ops/apisix_uygula.py` | `OPENROUTER_API_KEY`, `OPENROUTER_AUTH`, `APISIX_ADMIN_KEY`, `PANO_GIRIS_PAROLA`, `BOT_KEY_{BEKCI,KARNE,SEF,MERIDIAN}` (8) | `APISIX_ADMIN_KEY` dalga-1'de zaten Vault'ta (`/etc/meridian/apisix_admin_key`) — İKİ kanal |
| `~/.hermes/profiles/{bekci,karne,sef}/.env` + `~/.hermes/.env` | hermes bot oneshot'ları | `BOT_KEY_<AD>`, `OPENROUTER_API_KEY` (3+1 kopya) | TSK-138 kök nedeni: global kopya 09-08'de atlandı (401 'User not found') |
| `/opt/hindsight/.env-cp` | hindsight-cp (docker) | `HINDSIGHT_CP_ACCESS_KEY`, `HINDSIGHT_CP_DATAPLANE_API_KEY` (2) | — |
| `/opt/meridian/.dash.env` | meridian.service (eski kanal) | `MERIDIAN_DASH_TOKEN` | dalga-1'de `dash_token` credential kanalı canlı; bu dosya eski kanal — kaldırılabilir mi ölçülmeli |
| `state/secrets.json` | motor (Telegram/Alpaca/FMP) | hafıza `kimlik-deposu-secrets-json` | envanterde ayrı sınıf; Faz-1 kapsamı dışıydı |

## Seçenekler (bağımsız; her biri tek başına uygulanabilir)

**2a — OpenRouter anahtarları TEK kaynağa (en yüksek kazanç):** `secret/meridian/openrouter_api_key` (+ `openrouter_auth`) → Agent
şablonuyla `.env-apisix`, `/opt/hindsight/.env` (6 alan) ve hermes `.env` dosyaları render edilir. Rotasyon = kasaya bir kez `kv put`
+ Agent render + tüketici restart penceresi (`sir_rotasyon.sh --esitle` kalır, ama 14 kopya yerine 1 kaynak). BEDEL: Agent
`ReadWritePaths` `/opt/hindsight`, `/opt/apisix`, `/home/ubuntu/.hermes` ile genişler (root Agent'ın yazma yüzeyi büyür — tasarım
§6.3 sapmasının bedeli artar); docker tüketicileri env dosyasını yalnız konteyner (yeniden) başlayınca okur → rotasyon = restart.

**2b — Bot ve APISIX yönetim anahtarları:** `BOT_KEY_*` (4) + `APISIX_ADMIN_KEY` tek kanal (Vault) — `.env-apisix`ten `$env://`
çözümü için dosya yine gerekir (APISIX ortamdan okur); kazanç: iki kanal → bir kanal (dalga-1'deki `apisix_admin_key` kopyası kalkar).
BEDEL: 2a ile aynı yazma yüzeyi; `PANO_GIRIS_PAROLA` insan parolası — Vault'a girmesi kişisel karar.

**2c — hindsight-cp (2 sır):** küçük; docker restart bedeli; 2a ile birlikte anlamlı.

**2d — `.dash.env` eski kanalın KALDIRILMASI (kapsam daraltma, kazanç: kopya azalır):** `meridian/api.py::_read_dash_token`
credential'ı ÖNCE okuyor (2026-09-07); dosya kaldırılınca davranış değişmez mi → ölçüm (grep + canary) sonra sil. Vault işi değil, hijyen.

**2e — `state/secrets.json` (Telegram/Alpaca/FMP):** en hassas sınıf; Agent → dosya render deseni burada da işler ama motor bu dosyayı
JSON olarak okur (şablon JSON üretir). Ayrı dalga (3) — operatör kararı olmadan önerilmez.

## Rol-1 önerisi (sıra)
1. **2a** (OpenRouter tek kaynak) + **2c**; yazma yüzeyi genişlemesi kabul ediliyorsa. Ölçüm: rotasyon tatbikatı — kasaya yeni anahtar,
   Agent render, tüketici restart, `sir_rotasyon.sh` kuru koşumu 14/14 EŞİT, kapı chat 200, Hindsight 2/2.
2. **2d** hijyen (Vault'suz).
3. **2b** sonra; **2e** ayrı karar.

## Operatörden istenen üç cevap
1. Root Agent'ın yazma yüzeyi `/opt/hindsight`, `/opt/apisix`, `/home/ubuntu/.hermes` ile genişlesin mi? (evet/hayır)
2. Docker tüketicilerinin (apisix, hindsight-cp) rotasyonda yeniden başlatılması kabul mü? (pencere: 20:05Z sonrası)
3. `PANO_GIRIS_PAROLA` Vault'a girsin mi, yoksa envanterde "insan parolası, Vault dışı" beyanıyla mı kalsın?
