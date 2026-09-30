# Konuşan bot filosu — Parça 1b G3b: bot ağ geçidinin sırları — TASLAK (Rol-1, 2026-09-30)

> **OPERATÖR KARARLARI ALINDI (2026-09-30 16:1xZ, AskUserQuestion):** K-G3b-1 = **(a) birlikte yenile** — rotasyon aracına `--kapi-bot <ad>`
> alt komutu; bir botun kapı anahtarı yenilenince rapor (`~/.hermes/profiles/<ad>/.env`) ve sohbet (`~/.hermes-botlar/profiles/<ad>/.env`) kopyaları
> aynı turda yazılır. K-G3b-2 = **(a) araç oluştursun** — `--tohumla-sohbet` kipi (dosya yoksa 0600 ubuntu oluşturup kasadan yazar, varsa dokunmaz;
> değer argv/log/ekrana düşmez). K-G3b-3 = **Rol-1 dener, engellenirse operatöre tek komut** — Vault'a yeni sır koyma ve A1'de tohumlama; Rol-1 sır
> DEĞERİ görmez/yazmaz. Sıra: G4 birleştikten SONRA (Telegram biriminin credential drop-in'i de bu dilimde — v602 erteleme çivisi).

> Depoya `docs/superpowers/plans/2026-09-30-konusan-filo-parca1b-g3b-sirlar.md` olarak girecek. Yazım/uygulama yalnız DEPO (envanter, üreteçler,
> rotasyon aracı, drop-in, çiviler); canlı sır değeri Rol-1 görmez/yazmaz — tohumlama operatörde ya da rotasyon aracının kendi kipinde.

## Ölçülmüş zemin (G3 Architecture + depo haritası)
- Çoklu kipte sırlar profil `.env`inden (`agent/secret_scope.py`) → `~/.hermes-botlar/.env` (`API_SERVER_KEY`), `~/.hermes-botlar/profiles/<ad>/.env`
  (`BOT_KEY_<AD>`, `HINDSIGHT_API_KEY`). Rapor profilleri emsali: `.env`ler rotasyon aracıyla kasadan yazılır; Hermes `.env.vault` okumaz.
- `sir_rotasyon.sh` `_yaz_satir`: hedef dosya ÖNCEDEN VAR olmalı (`sudo test -f`), `^<alan>=` satırı TAM 1 kez; `koru koru` mod/sahip korur.
- `BOT_KEY_<AD>`: `vault_kv.bot_key_<ad>` `rotasyon_siri: null` (hiçbir alt komut döndürmüyor); `kopya_kaynaklari` taşıma-kıyas kapısı (`vault_sir_koy.sh`) içindir.
- Tenant: `--tenant` alt komutu; `_kredensiyeller` `tenant meridian.service HINDSIGHT_API_TENANT_API_KEY`; restart `_sir_birimleri`/`_BIRIM_SIRASI`.
- `API_SERVER_KEY` envanterde YOK; tüketicileri: bot ağ geçidi (kök `.env`) + `meridian/bot_kanal.py::HermesTasiyici` (`credential_oku("API_SERVER_KEY")` → pano/Telegram birimlerine `LoadCredential`, G4).
- Emsal yeni sır: `grafana_admin_parola` (commit 5004544d) — `vault_kv` + `agent.hcl`/`policies/meridian-agent.hcl` üretimi (`ops/vault_politika_uret.py --uygula`) + v491 `AGENT_SABLON_SAYISI` + v447 `ROTASYON_DISI_KREDENSIYELLER` + `izin_denetimli_sir_dosyalari` + deploy.sh başlığı + RUNBOOK.

## Görevler
- **Task 1 — Envanter + Vault şablonu (API_SERVER_KEY):** `deploy/sir_envanteri.yaml` `vault_kv.api_server_key` (hedef `/etc/meridian/api_server_key`, 0400 root) + `dosyalar` satırları (üç sohbet `.env` + kök `.env`, sınıf C; spec `docs/TASARIM-SIR-YOL1-2026-09-03.md` §1 tablosu + v439 E0 sayıları) + üreteç (`vault_politika_uret.py --uygula`) + v485/v491/v439. Değer YOK.
- **Task 2 — Rotasyon aracı:** `_kopyalar()` yeni satırlar: `tenant HINDSIGHT_API_TENANT_API_KEY env /home/ubuntu/.hermes-botlar/profiles/<ad>/.env HINDSIGHT_API_KEY koru koru -` ×3;
  `api_sunucu API_SERVER_KEY env /home/ubuntu/.hermes-botlar/.env API_SERVER_KEY koru koru -` (yeni alt komut `--api-sunucu`: kasaya yeni rastgele değer → render → kopya → birimler; ÜRETİM tanımı `_uret_sinifi`);
  BOT_KEY_<AD> sohbet kopyası: bugün rapor profiline de rotasyon yok → **KARAR K-G3b-1 = (a):** `--kapi-bot <ad>` alt komutu açılır ve rapor+sohbet `.env` birlikte döner (APISIX tüketici anahtarı `/opt/apisix/.env-apisix` kaynaklı — kapı yeniden yükleme sırası ölçülür).
  `_kredensiyeller` += `tenant meridian-botlar.service HINDSIGHT_API_TENANT_API_KEY`; `_sir_birimleri`/`_BIRIM_SIRASI` += `meridian-botlar.service` **yalnız aktifse** (`systemctl try-restart` — duran geçidi başlatmaz) + çivi; `_taranan_dosyalar` += dört `.env`.
  Envanter `rotasyon_kopyalari` aynası (v447 iki yönlü) + `KOPYA_SAYISI` + v520 `HERMES_SATIRLARI` + v491 `HERMES_ENV_KOPYALARI`.
- **Task 3 — Drop-in:** `deploy/oracle-a1/meridian-botlar.service.d/54-hafiza-credential.conf` (`LoadCredential=HINDSIGHT_API_TENANT_API_KEY:/etc/hindsight/creds/HINDSIGHT_API_TENANT_API_KEY`) + A0 `dropin_dizinleri`/`dropin_kaynaklari` + v601 erteleme çivisini çevir (credential VAR) + v447 P6 yeşil.
- **Task 4 — Tohumlama kipi:** `.env` dosyaları yokken rotasyon aracı yazamaz (`test -f`). **KARAR K-G3b-2 = (a):** `sir_rotasyon.sh --tohumla-sohbet`: dosya YOKSA 0600 ubuntu boş dosya + alan satırlarını kasadan yazar, VARSA dokunmaz (idempotent); değer argv/log'a düşmez.

## Canlı (Rol-1/operatör; G3c'den ÖNCE)
1. `vault_politika_uret.py --uygula` çıktısı + A1 Vault'a politika/şablon (admin jetonu — operatör) → `/etc/meridian/api_server_key` render kanıtı (değer basmadan: sahip/mod/uzunluk ≥16).
2. site.yml (drop-in + dizinler) → `sir_rotasyon.sh --tohumla-sohbet` (operatör) → `.env` sahip/mod/alan-varlık kanıtı (değer basmadan).
3. G3c test-ateşleme (plan G3 kontrol listesi).
