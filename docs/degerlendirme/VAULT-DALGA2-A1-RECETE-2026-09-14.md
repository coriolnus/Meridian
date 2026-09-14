# Vault dalga-2 — A1 uygulama reçetesi (2026-09-14; kaynak: Opus tur-2 raporu + Sonnet inceleme bulgusu 2)

Kim koşar: adım 1 (dağıtım) ve adım 2 (sır yazımı) OPERATÖR (sınıflandırıcı Rol-1'i bu iki komutta engelliyor, 2026-09-13/14 ölçüldü); kalan adımlar Rol-1 (ssh, salt-okur/servis). Sır DEĞERİ hiçbir terminale basılmaz (yalnız ad/sha).

## A1 UYGULAMA REÇETESİ — TUR-2 FARKI + ADIM-BAŞI GERİ ALIM (inceleme bulgusu 2)

Tur-1 reçetesi (rapor_vault_dalga2.md § "A1 UYGULAMA REÇETESİ") **AYNEN GEÇERLİ**; iki şey değişti:

- **Adım 2 (`vault_sir_koy.sh`)**: artık **12** yola `kv put` yapar, 15'e değil. Üç takma ad için
  çıktıda `✓ TAKMA AD <ad> → <birincil> … EŞİT` satırı beklenir. `✗ TAKMA AD … AYRIŞTI` çıkarsa
  **DUR**: bugün aynı sanılan iki değer aynı değildir ve hangisinin doğru olduğu betikten bilinemez.
- **Adım 4 (render kanıtı)**: `/etc/meridian/openrouter_api_key`,
  `/etc/meridian/bot_key_meridian`, `/etc/meridian/hindsight_cp_dataplane_api_key` dosyaları
  **ARTIK HİÇ DOĞMAZ** — `stat` listesinden çıkarılmalıdır. Onların yerine birincillerin dalga-1
  dosyaları (`/etc/hindsight/creds/HINDSIGHT_API_LLM_API_KEY`, `/etc/meridian/kapi_apikey`,
  `/etc/hindsight/creds/HINDSIGHT_API_TENANT_API_KEY`) render kanıtıdır ve zaten kuruludur.
- **Adım 10 (`--vault` rotasyonu)**: `--openrouter --vault` artık `secret/meridian/HINDSIGHT_API_LLM_API_KEY`
  yoluna yazar ve render kanıtı `/etc/hindsight/creds/HINDSIGHT_API_LLM_API_KEY`tir. Kuru koşum
  bunu `TAKMA AD: openrouter_api_key → HINDSIGHT_API_LLM_API_KEY` satırıyla ADIYLA basar.

**ADIM-BAŞI GERİ ALIM ÇAPRAZ REFERANSLARI** (incelemenin G merceği bulgusu):

| Adım | Ne yapar | Geri alım (o adıma özel) | Nereden okunur |
|---|---|---|---|
| 0 | `tick-watchdog.timer` durdurulur | `sudo systemctl start meridian-tick-watchdog.timer` (adım 11) | kalıcı kayıt `bakim-penceresi-tick-watchdog` |
| 1 | `./dagit.sh` (Rol-1) | önceki HEAD'e dağıtım; `state/dagitim.json::deployed_sha` önceki sürümü söyler | kalıcı kayıt `a1-git-yok-dagitim-sha` |
| 2 | `vault_sir_koy.sh --uygula` | **geri alım GEREKMEZ**: betik KAYNAK DOSYALARA DOKUNMAZ, yalnız kasaya kopya koyar | `vault_sir_koy.sh` başlığı "GERİ ALIM" bloğu |
| 3 | `agent.hcl` + politika kurulumu | `/etc/vault/agent.hcl`in yedeğini geri koy + `vault policy write` eski dosyayla | üretilmiş dosya → depodaki önceki sürüm |
| 4 | `systemctl restart vault-agent` | `sudo systemctl stop vault-agent` — render duran dosyalar OLDUĞU GİBİ kalır, tüketici eski kanalda | tasarım §6.4 |
| 5 | üç drop-in kurulur | `rm /etc/systemd/system/<birim>.d/*-vault-yan-dosya.conf` + `daemon-reload` | drop-in dosyalarının kendi "GERİ ALIM" bölümleri |
| 6 | `restart apisix hindsight-api hindsight-cp` | adım 5 geri alındıktan SONRA aynı restart — eski kanal geri gelir | — |
| 7 | kanıt (curl/envanter) | okuma; geri alımı YOK | — |
| 8 | canary (sahte değer) | satırı yedekten geri koy (canary'nin kendi son adımı) | reçete adım 8 |
| 9 | hermes `env_loader` ölçümü | sahte değeri geri al; birim başlatma gerekmez | reçete adım 9 |
| 10 | `sir_rotasyon.sh --vault` | betiğin kendi `$YEDEK` dizini (`/root/sir-yedek-<ts>-<alt>`) + eski yolla `--<alt> --esitle` | `sir_rotasyon.sh` yedek bloğu |
| 11 | timer geri açılır | — (adım 0'ın kapanışı) | — |

**KRİTİK SIRA (değişmedi):** render kanıtı → drop-in kurulumu → restart. apisix `--env-file` HARD
bağımlılıktır; `/opt/apisix/.env-apisix.vault` yokken drop-in kurulursa kapı AÇILMAZ.

## Kaygılar (Rol-1'e)

1. **`ops/apisix_uygula.py` ve APISIX `admin` anahtarı kapsam DIŞI kaldı (tur-1'den devam).**
   `apisix_admin_key` bir yan dosya satırı (`APISIX_ADMIN_KEY`) taşıyor ama `rotasyon_siri`
   ALAMIYOR: dalga-1 girdisi ve v485 E1 onların alan kümesini BİREBİR donduruyor. Sonuç:
   `--apisix-admin --vault` bugün "kasaya BAĞLI sırrı YOK" der. Aynı sınıf bot anahtarları / pano
   parolası / CP erişim anahtarı için de geçerli (onların rotasyon alt komutu HİÇ yok). Bu turda
   BİLEREK açılmadı — dalga-1 şema donukluğunu gevşetmek AYRI bir karardır.
2. **`--kapi --vault` artık motoru VE kapıyı birlikte yeniden başlatır.** `bot_key_meridian`
   takma adı `kapi_apikey` yoluna çözüldüğü için restart listesi `_sir_birimleri KAPI_APIKEY`
   (meridian.service) ∪ `apisix.service` olur. Tur-1'de kapı bu listede DEĞİLDİ (yan dosya ada
   göre aranıyordu) — yani bu bir düzeltmedir, ama bakım penceresinin bedeli büyüdü: iki birim,
   iki kesinti. Çivi T9 bunu ölçüyor; pencere planlanırken bilinmeli.
3. **Takma ad eşitlik kapısı `--kuru`da ÖLÇÜLEMEZ** ve bu beyanlı: kuru koşum kasaya HİÇ
   dokunmaz (v485 J3 / v491 D3 çivileri bunu zorluyor), yani "takma adın kaynağı kasadaki birincil
   değerle aynı mı" sorusu ancak `--uygula`da cevaplanır. Operatör kuru koşumdan "her şey hazır"
   sonucu ÇIKARMAMALI; kuru çıktı bunu satır satır söylüyor.
4. **`kopya_kaynaklari` kapısı takma adlar için hâlâ koşuyor** (kaldırılmadı): takma adın kendi
   kopya kümesi (ör. OpenRouter'ın 12 kopyası) taşımadan ÖNCE yine sha ile ölçülüyor. Yani iki
   kapı üst üste: önce "bu değerin kopyaları kendi aralarında aynı mı", sonra "bu değer kasadaki
   birinciliyle aynı mı". Bu bilinçli — ikisi AYRI sorulardır.
5. **Tur-1'in "RUNBOOK tazelik çivisi yok" iddiası ÇÜRÜK çıktı** (yukarıda). Bu, tur-1 raporunun
   ve incelemenin AYNI hatayı bağımsız olarak tekrarladığı bir vakadır (iki göz aynı kör noktaya
   baktı) — kalıcı hafızaya değebilir: "çivi yok" iddiası ancak kapsam koşumunun KIRMIZI
   vermemesiyle değil, çiviyi ARAYAN bir grep'le yazılır.
6. **A1'de ölçülecekler DEĞİŞMEDİ** (tur-1 kaygı 3/5): `ProtectHome=read-only` + hermes yazma
   deliği, hermes `env_loader`ın ikinci dosya desteği, `CAP_CHOWN`. Yerelde ölçülemez.
7. **Tam suite koşulmadı** (ajan yetkisi yok). Kapsam kuyruğu brief'in listesi + tur-1'in eklediği
   iki dosya (v451, v439) + v154/v209. `tests/test_uiux_s1b_v154.py` bu turda KRİTİK çıktı ve
   kuyruğa girmesi iyi olmuş — brief'in kuyruk listesi doğruydu.
