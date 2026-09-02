# Sır Yönetimi Kademeli YOL-1 — Hazırlık Belgesi (TSK-064)

**Tarih:** 2026-09-03 gece (Rol-1, operatör gece yetkisi; canlıya DOKUNULMADI — belge + envanter).
**Emsal:** TSK-049 / `deploy/oracle-a1/dash_token_credential.sh` (pano token'ı: rotasyon + `LoadCredential`
faz-1 canlı, faz-2 uygulama-şartlı). **Üst kayıt:** ROADMAP §4 mimari madde 7 (BEKLEMEDE-7: OpenBao/unseal
adımı operatörde — bu belge o adımı GEREKTİRMEZ, ondan önceki basamaktır).

## 1. Envanter (2026-09-03 21:5x UTC, A1; yalnız DEĞİŞKEN ADLARI okundu — değerler hiçbir terminale basılmadı)

| Dosya | mod / sahip | Değişken | Sır mı? | Tüketici | Kanal bugün |
|---|---|---|---|---|---|
| `/opt/meridian/.env` | 600 / ubuntu | MERIDIAN_DASH_TOKEN | SIR (tekrar: `.dash.env`) | meridian.service | EnvironmentFile (+ LoadCredential faz-1 paralel) |
| | | NOUS_API_KEY | SIR | meridian.service (Nous istemcisi) | EnvironmentFile |
| | | KAPI_APIKEY | SIR (kapı tüketici anahtarı `motor_meridian`) | meridian.service | EnvironmentFile |
| | | NOUS_MODEL · NOUS_ENDPOINT · MERIDIAN_FMP_BASE | yapılandırma | meridian.service | EnvironmentFile |
| `/opt/meridian/.dash.env` | 600 / ubuntu | MERIDIAN_DASH_TOKEN | SIR | meridian.service | EnvironmentFile (faz-2'de kapanacak) |
| `/opt/hindsight/.env` | 600 / ubuntu | HINDSIGHT_API_DATABASE_URL (parola gömülü) | SIR | hindsight-api.service | EnvironmentFile |
| | | HINDSIGHT_API_LLM_API_KEY | SIR | hindsight-api.service | EnvironmentFile |
| | | HINDSIGHT_API_TENANT_API_KEY | SIR | hindsight-api.service · (pano vekili `meridian/api.py` dosyayı okur) | EnvironmentFile + dosya okuma |
| | | diğer 29 (LLM/embedder/reranker/DB havuzu/…) | yapılandırma | hindsight-api.service | EnvironmentFile |
| `/opt/hindsight/.env-cp` | 600 / root | HINDSIGHT_CP_ACCESS_KEY · HINDSIGHT_CP_DATAPLANE_API_KEY | SIR | hindsight-cp.service (docker) | docker env-file |
| `/opt/apisix/.env-apisix` | **640** / root | APISIX_ADMIN_KEY · OPENROUTER_API_KEY · OPENROUTER_AUTH · PANO_GIRIS_PAROLA · BOT_KEY_{BEKCI,KARNE,SEF,MERIDIAN} | SIR ×8 | apisix.service (docker, `$env://` çözümü) · `ops/apisix_uygula.py` (admin anahtarı) | EnvironmentFile → docker run env |
| `~/.hermes/profiles/<bekci,karne,sef>/.env` | (ölçülmedi) | BOT_KEY_<AD> | SIR | hermes bot birimleri (timer'lı oneshot) | HERMES_HOME/.env (hermes env_loader) |

**Bulgu-1 (hemen):** `.env-apisix` 640 — grup okuyabilir; diğer sır dosyaları 600. Tek satır: `chmod 600`
(docker `EnvironmentFile`'ı root okur, grup gerekmez). Sabah penceresinde, F9 beyanıyla.
**Bulgu-2:** MERIDIAN_DASH_TOKEN iki dosyada (motor `.env` + `.dash.env`) — tek-kaynak ihlali; faz-2'de
`.dash.env` kapanınca motor `.env`'deki kopya da kalkmalı (TSK-049 faz-2 şartı: uygulama tarafı).
**Bulgu-3:** hindsight TENANT_API_KEY'i pano vekili DOSYADAN okuyor (`meridian/api.py::_env_anahtari`);
LoadCredential'a geçince vekilin okuma yolu `$CREDENTIALS_DIRECTORY`ye taşınmalı (kod değişikliği, tam suite).

## 2. Sınıflandırma ve hedef kanal

| Sınıf | Bugün | YOL-1 hedefi | Not |
|---|---|---|---|
| A · systemd-doğal süreçler (meridian, hindsight-api) | EnvironmentFile | **LoadCredential** (sır ortama girmez; `$CREDENTIALS_DIRECTORY/<ad>`) | emsal hazır; uygulama tarafı: `os.environ[...]` → credential dosyası okuyucu (tek yardımcı, iki serviste) |
| B · docker-sarmalı süreçler (apisix, hindsight-cp) | EnvironmentFile → `docker run -e` | LoadCredential + ExecStart sarmalayıcı (`$CREDENTIALS_DIRECTORY`den okuyup `--env` verir; ortamda yine görünür ama HOST birimi ortamına girmez) | docker'ın kendi secret'ı swarm ister — YOK; yarım kazanım, dürüstçe beyan |
| C · hermes profil `.env` | HERMES_HOME/.env | DEĞİŞMEZ (hermes env_loader sözleşmesi; TSK-105 ölçümü) | OpenBao (BEKLEMEDE-7) gelince yeniden |
| D · yapılandırma (sır değil) | EnvironmentFile | KALIR | sır/ayar ayrımı dosya düzeyinde: sır dosyası ayrı, ayar dosyası ayrı (hindsight `.env` 32 → 3 + 29) |

## 3. Fazlar (her faz kendi canary'si ve geri-alımıyla; hiçbiri bu belgeyle uygulanmaz)

1. **Faz-0 (sabah, 5 dk, risksiz):** `.env-apisix` 600; envanter bu belgeye çivilenir (test: dosya
   adları + değişken adları listesi repo beyanıyla eşleşir — `deploy/sir_envanteri.yaml` üretilir,
   F9 kapısı içerik yerine AD listesi kıyaslar; değer asla).
2. **Faz-1A (hindsight-api):** `HINDSIGHT_API_{DATABASE_URL,LLM_API_KEY,TENANT_API_KEY}` →
   `/etc/hindsight/creds/<ad>` (0600 root) + `LoadCredential=` ×3; hindsight-api upstream kodu
   env okur → sarmalayıcı `ExecStart` credential'ları ortama koyar (B sınıfı yarım kazanım) YA DA
   `HINDSIGHT_API_*` için upstream `_FILE` desteği ölçülür (varsa tam kazanım). Ölçüm önce.
   Vekil (`api.py`) TENANT anahtarını credential dosyasından okur (kod + v375 çivisi + tam suite).
3. **Faz-1B (meridian):** NOUS_API_KEY + KAPI_APIKEY → LoadCredential; `nous.py`/`_nous_headers()`
   okuma yolu credential-önce, env-yedek (geçiş penceresi), sonra env kapanır (TSK-049 faz-2 deseni).
4. **Faz-1C (apisix/cp):** sarmalayıcı ExecStart; `$env://` çözümü aynen; `ops/apisix_uygula.py`
   admin anahtarını credential dosyasından okur.
5. **Faz-2:** BEKLEMEDE-7 (OpenBao/unseal) — operatörde; bu belgenin kapsamı dışı.

## 4. Kapılar / bedel
- Her faz: rotasyon + kanal geçişi AYNI pencerede (TSK-049 hükmü: eski kanal geçerliyken yeni
  kanal ölçülemez). Canary: `systemctl show <birim> -p LoadCredential` + servis açılıyor + iş
  yapıyor (health/ilk istek) + `/proc/<pid>/environ`da sır YOK (grep -c 0).
- Bedel: docker sınıfında sır konteyner ortamında kalır — beyanlı; tam kapanış OpenBao'yla.
- Sır DEĞERİ hiçbir aşamada terminale/loga basılmaz (2026-09-02 DATABASE_URL vakası: süzgeç
  kara-liste değil beyaz-liste — hafıza kaydı).

## 5. Sonraki adım (operatör kararı)
Faz-0 sabah penceresinde (chmod + envanter çivisi); Faz-1A/1B tek dalga (motor + hindsight kodu, tam
suite, dağıtım penceresi). Onay: ROADMAP TSK-064 status notu.
