# Konuşan bot filosu — tasarım (TSK-010 + bot kadrosu dalga 1–2)

**Durum:** tasarım ONAYLI (operatör 2026-09-29 12:4xZ "onaylıyorum"), kod yok · **Yazan:** Rol-1 · **Tarih:** 2026-09-29
**Kaynak belgeler:** `docs/superpowers/specs/2026-08-27-bot-roster-design.md` (21 bot, §7 "konuşan bot" açık sorusu) ·
`docs/superpowers/specs/2026-09-07-pano-sohbet-design.md` (pano sohbeti, güvenlik değişmezleri) ·
`docs/DEGERLENDIRME-HAFIZA-ADAYLARI-2026-08-31.md` (hafıza katmanı: "önce kart") · 21 botun rol tablosu: oturum
`f323a729` satır 41220, 2026-08-26T21:22Z (bu belgenin §2.2'sine taşındı — artık TEK KAYNAK burası).
**Hafıza kontrolü (karar öncesi):** Hindsight recall 2026-09-29 12:07Z — "konuşan bot 09-06'da ertelendi, gerekçe aynı
jetona iki dinleyici" (bugün dinleyen YOK, ölçüldü) · `ops/kart_benzer.py` → yalnız EDG-2026-086 (hükümsüz; sohbet hiç
kullanılmadı), KALDI/NO-GO benzeri yok · memory: [[hindsight-aktif-kullanim]], [[llm-cagri-kotasi]], [[birim-sertlestirme-yeni-yazim-yolu]].

## 0. Operatör kararları (2026-09-29, sırayla)

| # | Soru | Karar |
|---|---|---|
| K1 | Botlar nereden kullanılsın? | ÜÇ KANAL: Telegram · pano · Claude uygulaması (burası) |
| K2 | Bot ne yapabilsin? | **B** — okur, cevaplar, onay kuyruğuna öneri yazar, rapor işlerini hemen çalıştırır; ayar DEĞİŞTİRMEZ |
| K3 | Telegram biçimi | **A** — tek sohbet, MEVCUT bot; `@ad` öneki ya da rapora "yanıtla" |
| K4 | Mimari | Her bot KENDİ Hermes profiliyle konuşur, komut çalıştırma yetkisi YAPISAL olarak kapalı (operatör önerisi) |
| K5 | Uzun hafıza | EVET — her botun kendi hafızası |
| K6 | Hafıza paylaşımı | **B** — `@sef` hepsini okur, diğerleri yalnız kendininkini |
| K7 | Kadro | Hedef 21 bot; **dalga 1 + dalga 2 bu yapımda**, dalga 3 sırada, `@hipotez` kilitli. TSK-061'in "önce ≥1 bot değer kanıtı" kapısı operatör kararıyla KALKTI |

## 1. Amaç ve başarı tanımı

**Sorun (ölçüldü 2026-09-29 11:4xZ, A1):** üç bot (`@sef` 22:00Z, `@bekci` 10:00Z, `@karne` Cmt 16:00Z) yalnız TEK YÖNLÜ zamanlı rapor
yolluyor (14 günde 28/28/4 koşum). Telegram botunu DİNLEYEN hiçbir kod/süreç yok (`getUpdates`/webhook grep boş). Pano sohbeti
(TSK-012 dalga-B) 2026-09-13'ten beri canlı ama HİÇ kullanılmadı (`state/sohbet.jsonl` yok, `approvals.jsonl`de sohbet satırı 0).
Üç botun Hermes `memories/` dizini boş.

**Başarı:** operatör 13 bottan herhangi birine üç kanaldan soru sorar; bot kendi kimliği ve rolünün araçlarıyla, kaynak atfıyla
cevaplar; önerileri onay kuyruğuna düşer; rapor işlerini isteyince koşturur; sohbette dünü hatırlar ama bugünü yalnız araçtan
okur. Hiçbir kanal botlara komut/dosya/ağ yetkisi açmaz.

## 2. Kapsam

### 2.1 İçeride / dışarıda
İÇERİDE: kadro listesi (tek kaynak) · Meridian araç sunucusu genişlemesi · Hermes bot sunucusu (api_server) · bot başına Hindsight
bankası · kanal katmanı (Telegram dinleyicisi, pano bot seçici + hafıza görünümü, Claude uygulaması filo sunucusu) · "iş iste" ·
kota sayacı · ölçüm kartı · 10 yeni bot profili (dalga 1: 4, dalga 2: 6).
DIŞARIDA: Hermes'in kendi Telegram gateway'i (Hermes ajanının yetkileri Telegram'a açılmaz) · botların depoya/state'e yazması ·
ayar değiştirme (K2-C reddedildi) · zamanlı raporlara hafıza · dalga 3 · TSK-018 (olay-tetikli zamanlama).

### 2.2 Kadro (21 bot — tasarım anının kaydı)
(2026-09-29 14:5xZ Rol-1 notu: kadronun TEK KAYNAĞI artık `deploy/hermes/kadro.yaml`dır — rol, dalga, durum, araç seti, imza,
hafıza kipi orada yaşar ve `tests/test_kadro_v591.py` çivilidir. Bu tablo tasarım anının kaydıdır; ayrışırsa kadro.yaml kazanır.)
| Bot | Rol | Girdi | Dalga |
|---|---|---|---|
| `@sef` | Konuştuğun tek yüzey; diğer botların çıktısını kısar | diğer botların çıktısı | canlı |
| `@bekci` | Sessizce bozulanı bulur ve kışkırtır | mekanizma tazeliği + bant dışı hayati bulgu | canlı |
| `@karne` | Deney `goal.yaml`a karşı kazanıyor mu | `goal.yaml` + getiri eğrisi + işlemler | canlı |
| `@kod` | Bu kod/karar neden böyle | kaynak + kök-neden şerhleri + git + karar belgeleri + dersler (arşiv bankası) | 1 |
| `@karar` | Sende bekleyen her şey + yaşları | onay kuyruğu + OPERATOR kalemleri + dağıtılmamış commit'ler | 1 |
| `@ayna` | Botların/skill'lerin kendi sicili — kalibrasyon | `agent_calls` + izler + bu tasarımın sohbet defteri | 1 |
| `@olay` | Olayın zaman çizgisi ve kapanış takibi | alarm → sonrası (olay arşivi) | 1 |
| `@kacan` | Ne olmadı ve neye mal oldu | `counterfactuals.jsonl` + `intraday_decisions.jsonl` | 2 |
| `@veri` | Dış dünya (fiyat/broker/takvim) sağlam mı | bar bütünlüğü + broker görüşü + takvim | 2 |
| `@butce` | Kota, harcama, israf | `fmp_usage` + sağlayıcı kotaları + §3.7 sayacı | 2 |
| `@yol` | İş takibi: yakala · önceliklendir · öldür | ROADMAP | 2 |
| `@nobet` | Alarmın İLK ayrıştırması (sonrası `@olay`da) | beyanlı alarmlar | 2 |
| `@denetci` | Neyi iddia ediyoruz, hâlâ doğru mu | belgeler + şerhler | 2 |
| `@civici` · `@devir` · `@derleyici` · `@olcum` · `@tasarimci` · `@yabanci` · `@piyasa` | (roster tablosu) | — | 3 (sırada) |
| `@hipotez` | Öğrenme motorunu besler | ret örüntüleri + arama uzayı | KİLİTLİ (EDG-2026-058) |

`@nobet`in 2026-09-06 elenme gerekçesi ("ikinci Telegram jetonu gerekir") bu tasarımla ortadan kalktı; ayırt edici yarısı (talep
üzerine konuşma) HER botun ortak özelliği olduğundan rolü "ilk ayrıştırma"ya daraltıldı.

## 3. Mimari

```
 Telegram (tek bot)          Pano (bot seçmeli sohbet)          Claude uygulaması (Mac)
       │                              │                                   │
 meridian-telegram.service     /api/sohbet (+bot alanı)           ops/filo_mcp.py (stdio MCP)
 (getUpdates; YALNIZ operatör         │                           SSH tüneli + pano jetonu
  sohbeti; @ad / rapor imzası)        │                                   │
       └───────────────┬──────────────┴───────────────────────────────────┘
                       ▼
          meridian/bot_kanal.py :: bota_sor(bot, mesaj, kanal, oturum)
          (kadro doğrulama · kota · hatırla/unut · bot_sohbet.jsonl defteri)
                       │  HTTP 127.0.0.1:8642, API_SERVER_KEY (Vault → LoadCredential)
                       ▼
          meridian-botlar.service = `hermes gateway run` (api_server, multiplex_profiles)
            /p/<bot>/v1/chat/completions  +  X-Hermes-Session-Id
            profil: SOUL.md (zamanlı raporla AYNI) · platform_toolsets.api_server = [meridian araçları] (İZİN LİSTESİ)
                    · disabled_toolsets (bugünkü 13 takım, YASAK LİSTESİ) · hafıza sağlayıcı = hindsight, banka bot-<ad>
                       │ stdio MCP
                       ▼
          meridian/mcp_server.py (genişler) — okuma araçları (sohbet.py'den TEK KAYNAK) · oneri_yaz · is_iste · bot_hafizasi_ara (yalnız @sef)
```

### 3.1 Kadro listesi — `deploy/hermes/kadro.yaml` (TEK KAYNAK)
Satır başına: `ad`, `rol`, `dalga` (canli|1|2|3|kilitli), `durum` (aktif|sirada|kilitli), `araclar` (araç sunucusu alt kümesi),
`zamanli_is` (birim adı ya da `null`), `imza` (rapor başlığının ÖNEKİ; `ops/*_brifingi.py` `BASLIK` sabiti bununla BAŞLAR — çivi; önek çünkü `@sef` başlığı kip ekini taşır, 2026-09-29 Task 1 incelemesi), `hafiza`
(`kendi`|`hepsi`), `gunluk_tavan` (Parça 0 ölçümünden). Türetilenler: Telegram yönlendirmesi, Hindsight bankaları, pano seçicisi,
profil `platform_toolsets`, filo sunucusu `bota_sor` enum'u. Çivi: `aktif` satırlar ↔ `deploy/hermes/profiles/*` birebir; `sirada`
satırlar profil taşımaz.

### 3.2 Meridian araç sunucusu (`meridian/mcp_server.py` genişler)
- Okuma araçları `meridian/sohbet.py` `ARACLAR` fonksiyonlarından İTHAL edilir (kopya yok): `pano_ozeti · plan_oku · pozisyon_oku ·
  alarm_oku · olay_sorgu · bar_sorgu · hafiza_ara · kart_oku · gunluk_ara` + mevcut 6 getter. Çıktı `<<<VERI:ad>>>` çiti +
  `notify.scrub` + boyut tavanı (sohbet.py değişmezleri aynen).
- `oneri_yaz` — sohbet.py'deki donuk `ONERI_TURLERI` (`plan_onayi`, `alarm_ack`, `not`) ve AYNI `approvals.jsonl` yolu; ikinci
  onay yolu AÇILMAZ; `kaynak` alanı bot adını taşır.
- `is_iste(is)` — §3.6.
- `bot_hafizasi_ara(bot, soru)` — yalnız `hafiza: hepsi` botlara (bugün `@sef`) listelenir; `bot-*` bankalarında SALT-OKUR recall.
- Bot başına araç seti: sunucu çağıran profili kimliğinden bilir (profil başına ayrı `mcp_servers` girdisi, `--bot <ad>` argümanı);
  kadro.yaml'daki `araclar` dışındaki araç `tools/list`te GÖRÜNMEZ ve `tools/call`da reddedilir (iki kat).

### 3.3 Hermes bot sunucusu
- Hermes v0.19.0 (A1'de ölçüldü): `gateway/platforms/api_server.py` — varsayılan `127.0.0.1:8642`, `API_SERVER_KEY` zorunlu;
  `gateway.multiplex_profiles` açıkken tek dinleyici, profillere `/p/<profil>/` öneki; oturum sürekliliği `X-Hermes-Session-Id`.
- Birim `meridian-botlar.service` (A0 rolü `site.yml` kurar — [[dagit-dropin-kurmaz-a0-rolu-kurar]]): `User=ubuntu`, sertleştirilmiş,
  anahtar `LoadCredential` ile (değer argv/ortam dosyası/log'a düşmez), yalnız loopback.
- Profil "sohbet kipi" config bloğu: `platform_toolsets.api_server` = yalnız Meridian araç sunucusu (İZİN LİSTESİ — Hermes
  `hermes_cli/config.py` `platform_toolsets`; ölçüm: v0.19'da var, resolve_toolset listede olmayanı yüklemez); mevcut
  `agent.disabled_toolsets` (13 takım) YERİNDE KALIR. Depodaki "beyaz liste yok" şerhi (`deploy/hermes/profiles/*/config.yaml`)
  v0.19 ölçümüyle güncellenir.
- Zamanlı rapor yolu (`hermes -z`, `ops/*_brifingi.py`) DEĞİŞMEZ.

### 3.4 Hafıza
- Sağlayıcı: Hermes `plugins/memory/hindsight` (profil-kapsamlı `$HERMES_HOME/hindsight/config.json`; `HINDSIGHT_BANK_ID`,
  `HINDSIGHT_API_URL`, `HINDSIGHT_BUDGET=low`, `HINDSIGHT_TIMEOUT=10`). Hedef A1'deki MEVCUT self-host Hindsight sunucusudur;
  sağlayıcının hangi kipinin (`cloud` + `HINDSIGHT_API_URL` / `local`) ona bağlandığı Parça 0'da ölçülür — Hermes'in GÖMÜLÜ
  daemon'u AÇILMAZ (ikinci bir hafıza süreci ve ikinci bir depo olurdu). Kiracı anahtarı bot sunucusuna yalnız `LoadCredential`
  ile (TSK-064 kanalı: `/etc/hindsight/creds/`), argv/ortam dosyası/log'a düşmez. Banka `bot-<ad>`; mühendislik arşivi
  (`meridian-arsiv`) ayrı kalır, botlara yalnız `hafiza_ara` ile SALT-OKUR.
- Ne yazılır: sohbet dönüşü (operatör mesajı + botun nihai cevabı), etiket `bot`, `kanal`, tarih. Ham araç çıktısı YAZILMAZ;
  kayıt öncesi `notify.scrub`.
- Kim yazar: bot kendi kararıyla YAZAMAZ (sağlayıcının retain aracı izin listesinde yok); yazan yalnız (a) sağlayıcının otomatik
  dönüş kaydı, (b) kanal katmanının DETERMİNİSTİK `hatırla: …` işleyicisi (etiket `sabit_not`, kaynak operatör). `unut: …` →
  geri alınabilir "unutuldu" işareti; kalıcı silme YOK.
- Uydurma koruması: SOUL sohbet bölümü — hafızadan gelen her cümle TARİHLİ atıfla söylenir; BUGÜNÜN durumu hakkında hafızadan hüküm
  verilmez (bugün yalnız araçtan). Hafıza 10 s'de gelmezse bot hafızasız cevaplar ve bunu SÖYLER.
- Zamanlı raporlar HAFIZASIZ (2026-08-31 değerlendirmesi §7: "ne değişti" harness damgasıyla ÖLÇÜLÜR, hatırlanmaz). Uygulama:
  sağlayıcı yalnız api_server platformunda açılır; platform-kapsamlı açma mümkün değilse (Parça 0 ölçer) sohbet için ikiz profil
  `<ad>-sohbet`, `SOUL.md` sembolik bağla TEK KAYNAK.
- Görünürlük: pano Bilgi Tabanı'nda bot başına hafıza listesi + unut düğmesi.

### 3.5 Kanal katmanı
- **Ortak çekirdek `meridian/bot_kanal.py`:** `bota_sor(bot, mesaj, kanal, oturum) -> Cevap` — kadro doğrulama, kota, hatırla/unut,
  api_server çağrısı, `state/bot_sohbet.jsonl` defteri (ts, bot, kanal, oturum, mesaj_sha, cevap_uzunluk, sure_s, arac_cagrilari,
  hafiza_durumu, oneri_id, kota_bugun, hata). Yasa 6 okuyucuları: `@ayna`, `@butce`, pano, ölçüm kartı.
- **Telegram — `meridian/telegram_dinleyici.py` + `meridian-telegram.service`:** `getUpdates` uzun yoklama (webhook YOK → dışarıya
  yeni giriş YOK); ofset kalıcı; yalnız `TELEGRAM_CHAT_ID` sohbeti — diğerleri reddedilir ve `bot_yabanci_mesaj` olayı olarak
  SAYILIR. Yönlendirme: `@ad` öneki → o bot; rapora yanıt → yanıtlanan mesajın ilk satırı `kadro.imza` ile eşleşir → o bot;
  ikisi de yoksa `@sef`. Cevap aynı sohbete, `reply_to_message_id` ile — `notify.py`ye yanıt parametresi (tek teslimat yolu,
  `scrub` korunur).
- **Pano:** `/api/sohbet` isteğine `bot` alanı: yoksa/`genel` → mevcut `sohbet.py` döngüsü (EDG-2026-086 kartı ona bağlı, dokunulmaz);
  kadrodaki bot → `bota_sor`. UI: `Ajan.tsx` sohbet paneline kadrodan türeyen seçici.
- **Claude uygulaması — TSK-010 `ops/filo_mcp.py`:** Mac'te stdio MCP; araçlar `bota_sor`, `is_iste`, `filo_durum` (`ops/filo.py`
  okuma fonksiyonları). A1'e SSH tüneli üzerinden pano API'si; pano jetonu `.dash.env`den süreç içinde okunur (argv yok). Bot
  sunucusu anahtarı Mac'e GELMEZ. Kayıt: depo kökü `.mcp.json`.

### 3.6 "İş iste"
`is_iste(ad)` → `state/istek/<bot>.istek` (bot, kanal, ts; 2026-09-29 Parça 1a: iş adı = kadrodaki `zamanli_is` taşıyan botun adı, takma ad `brifing`→`sef` — liste `kadro.yaml`dan türer) → systemd `.path` birimi aynı `.service`i başlatır (sohbete systemctl/sudo
yetkisi AÇILMAZ; oneshot çalışırken ikinci başlatma aynı işe katılır → çift koşum yok). Liste (donuk): `karne` → meridian-karne ·
`bekci` → meridian-bekci · `brifing` → meridian-brifing. Aynı iş için 15 dk tavanı `is_iste` içinde (istek defterinden). Yazan
birimin `ReadWritePaths`ine `state/istek` eklenir + A0 dizin görevi ([[birim-sertlestirme-yeni-yazim-yolu]], v553).

### 3.7 Kota
Filo-çapında LLM sayacı BUGÜN YOK (TSK-014 keşfi 2026-09-03). Parça 0 bugünkü günlük kullanımı ölçer (kaynak: APISIX kapı erişim
kaydı; ölçülemezse `None` + neden). `bot_kanal` her dönüşü + Hermes'in dönüş başına model çağrı sayısını deftere yazar;
`kadro.gunluk_tavan` aşılınca bot "bugünlük kotam doldu" der (sessiz değil). Tavan sayıları Parça 0 ölçümünden yazılır —
UYDURULMAZ. `@butce` ve pano bot başına sayacı okur.

## 4. Güvenlik

| Tehdit | Savunma |
|---|---|
| Telegram'dan yabancı mesaj | yalnız `TELEGRAM_CHAT_ID`; red SAYILIR (`bot_yabanci_mesaj`) |
| Operatörün Telegram hesabı ele geçer | K2-C yok: ayar değiştirilemez; öneri onayı yalnız pano; `is_iste` donuk liste + 15 dk tavan. KALAN RİSK (beyanlı): okuma araçlarıyla kâğıt-işlem verisi okunabilir |
| Bot komut/dosya/ağ aracına erişir | izin listesi (`platform_toolsets`) + yasak listesi (`disabled_toolsets`) + araç sunucusunda bot-başı alt küme; Parça 0'da YAPISAL kanıt (araç `tools/list`te yok) |
| Veriye gömülü talimat | VERİ çiti + `scrub` (sohbet.py değişmezleri); hafızaya ham araç çıktısı girmez |
| Hafıza zehirlenmesi | bot yazamaz; tarihli atıf; bugün-hükmü yasağı; kart kill maddesi; operatör görür/unutur |
| Sır sızıntısı | API anahtarı LoadCredential; pano jetonu süreç içi; hiçbir değer argv/log/URL parametresinde değil |
| Kota tüketimi | bot başına günlük tavan + sayaç |

## 5. Ölçüm kartı (Parça 0'da yazılır, hafıza AÇILMADAN önce)
Yeni kart (EDG sınıfı, `ops/kart_benzer.py` → selef EDG-2026-086). Ölçer: bot başına soru sayısı, cevap süresi, öneri→onay oranı,
hafıza atıflarının doğrulanabilirliği (tarih + kaynak dönüşü var mı), araçsız "bugün" iddiaları. **Kill (sıfır tolerans):**
hafızadan BUGÜN hakkında hüküm → o botun hafızası kapanır. Eşikler ADIM-0'da gerçek veriden ölçülür ([[kill-esigi-adim0da-olculur]]);
`@ayna` bu kartın okuyucusudur.

## 6. Parçalar ve sıra
| # | Parça | Bitti tanımı |
|---|---|---|
| 0 | **Deneme** (yalnız `@bekci`) | (a) izin listesi YAPISAL: `terminal/file/web` araçları istekte YOK (`/v1/capabilities` ya da koşu olayları); (b) ücretsiz zincirle araç çağrısı api_server üzerinden çalışıyor; (c) boş bankada recall süresi; (d) hafıza platform-kapsamlı mı; (e) sağlayıcının otomatik kaydı araç çıktısı içeriyor mu; (f) Hindsight "unut" ucu; (g) bugünkü günlük LLM kullanımı; (h) bot sunucusu RAM. Biri tutmazsa DUR → operatör |
| 1 | Çekirdek | kadro.yaml + araç sunucusu + bot sunucusu birimi + hafıza + `bot_kanal` + is_iste + kota; üç canlı bot sohbet kipinde |
| 2 | Telegram | dinleyici + yönlendirme + yanıt; yabancı red sayacı |
| 3 | Pano | bot seçici + bot hafıza görünümü |
| 4 | Claude uygulaması | TSK-010 `ops/filo_mcp.py` + `.mcp.json` |
| 5 | Dalga 1 | `@kod @karar @ayna @olay` profilleri (SOUL + araç seti + testler) |
| 6 | Dalga 2 | `@kacan @veri @butce @yol @nobet @denetci` |

Her parça kendi uygulama planını alır (tek dev plan değil): Parça 0 bir ÖLÇÜMDÜR ve bulguları Parça 1 planının girdisidir
(ör. §3.4 platform-kapsamlı hafıza mı ikiz profil mi). Her parça: Opus uygulayıcı (worktree, TDD, mutasyon) → Sonnet 5.5
inceleme → birleştirme → motor dokunduysa tam suite → push → CI (SHA ile) → dağıtım (A0 bloğu gerekiyorsa `site.yml` dahil).
Parça 0'ın A1 adımları (deneme birimi, anahtar) Rol-1'dedir — ajan A1'e dokunmaz ([[ajana-a1-verisi-rol1-ceker]]).

## 7. Test
Parça başına TDD; sabit çiviler: kadro ↔ profil eşitliği · `imza` ↔ `BASLIK` eşitliği · izin listesi yalnız Meridian araçları ·
yasak listesi adları gerçek toolset anahtarı (mevcut kardeş çivi) · "yalnız operatör" (yabancı chat_id → cevap YOK + sayaç) ·
bot-başı araç alt kümesi (`tools/list` + `tools/call` reddi) · `oneri_yaz` ikinci onay yolu açmaz · `is_iste` donuk liste + tavan ·
hafıza: ham araç çıktısı kaydedilmez · sır: argv'de değer yok (v554 deseni). Her çivi mutasyonla ısırmalı; test adında
`FAILED`/`ERROR` jetonu yok.

## 8. ROADMAP etkisi
TSK-010 → ACTIVE (bu belge) · TSK-061 → kapı operatör kararıyla kalktı (K7), dalga 1–2 bu programda, dalga 3 GATED(sırada) ·
parçalar ayrı TSK kalemleri (PRG-12) · TSK-018 değişmez.
