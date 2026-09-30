# Konuşan bot filosu — Parça 1b G4: kanal kablolaması — Uygulama Planı

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `bota_sor` üretimde gerçek taşıyıcı ve hafızayla çalışır, her sohbet dönüşünü scrub'lı ve etiketli olarak hafızaya kendisi yazar, `unut:` iki adımlı ve geri alınabilir olur; Telegram dinleyicisi `main()` + birim (ETKİN DEĞİL) + 4096 bölme + ara bildirim kazanır; pano sohbeti `mcp:` önekli oturumu reddeder. Canlı açılış YOK (G3b sırları + G3c test-ateşleme sonrası).

**Architecture:** Depo haritası (Rol-1 oturumu 2026-09-30, main 66706ec9) ölçtü: üretimde `bota_sor` çağıran kod YOK; Telegram `main()`/birim YOK; normal sohbet dönüşü hafızaya yazılmıyor (`hafiza` varsayılanı `None`); `unut:` tek adım, `geri_al` bağsız; Telegram'da 4096 bölme ve ara bildirim yok; `POST /api/sohbet` `oturum`u serbest alır. Spec §3.4 (2026-09-30 düzeltmesi): Hermes `auto_retain` KAPALI, dönüşü YALNIZ `bota_sor` scrub'lı yazar. Hindsight retain `async: true` arka planda işler ve hemen `success` + `operation_id` döner (A1 OpenAPI `RetainRequest`/`RetainResponse`, 2026-09-30 ölçüldü) → dönüş kaydı cevabı geciktirmez.

**Tech Stack:** Python stdlib; `meridian.bot_kanal`, `meridian.bot_hafiza`, `meridian.telegram_dinleyici`, `meridian.notify`, `meridian.sohbet`, `meridian.api`; systemd.

**Spec:** `docs/superpowers/specs/2026-09-29-konusan-bot-filosu-design.md` §3.4–§3.5, §4 · taslak `docs/superpowers/plans/2026-09-30-konusan-filo-parca1b-taslak.md` G4 (a)–(e) · G2/G3 dal sonu ertelemeleri (M-1 unut iki adım, M-4 kanal etiketi + 10 s hafızasız beyanı, M-5 bütçe ↔ taşıyıcı çapraz çivisi; G3 T3 M2 `mcp:` reddi).

## Global Constraints
- Sır/anahtar ASLA argv/log/deftere; `notify.scrub` hem deftere hem hafızaya hem MODELE giden mesaja uygulanır (Rol-1 hükmü: operatörün yapıştırdığı sır dış modele gitmesin).
- Hafıza yazımı başarısız olursa CEVAP DÜŞMEZ; defter `hafiza_durumu` alanı doğruyu söyler (yazildi/yazilamadi/atlandi); olay `bot_hafiza_*` kapalı-küme `neden` taşır.
- Hafızaya yazan taraflar yalnız: dönüş kaydı (`bota_sor`, bağlam "sohbet dönüşü", kaynak "bot_kanal") + `hatırla:` (bağlam "operatör notu", kaynak "operator" — bugünkü gövde AYNEN). Kalıcı silme YOK (`unut` = invalidated, `geri al` = valid).
- `komut_oneki` komut tespitinin TEK kaynağı kalır (v593 AST çivisi).
- Test numaraları mevcut dosyalar (v592/v593/v596/v450) + yeni v602 (Telegram birimi/ana) — çakışmayı `ls tests/*v602*` ile ölç. Test adlarında FAILED/ERROR yok; yorumlarda `dosya.py:NNN` yok; Yasa 4/6; pytest `env -u PYTHONDONTWRITEBYTECODE`.
- Yeni durum dosyası → `codelaw.DECLARED_SINKS` + v214 `SINK_TABANI`.
- Telegram birimi `etkin_birimler`e EKLENMEZ; credential drop-in'i G3b sır dilimine (API_SERVER_KEY) ertelenir — v601 emsaliyle erteleme çivisi.
- Dal `meridian/`e dokunur → tam suite + KILL#1 Rol-1'de; ayrıca birim ekler → depo tarayıcıları (memory `motor-disi-dal-tam-suite`).

## Review Focus
1. Hafıza yazımı 10 s zaman aşımına düşerse Telegram cevabı gecikmemeli/düşmemeli (`async: true` + cevaptan bağımsız hata yolu).
2. `unut:` ilk adımı HİÇBİR şeyi değiştirmemeli (yalnız aday listesi); süresi geçen/yabancı kısa kod reddedilir; başka botun adayını onaylamak mümkün olmamalı.
3. 4096 bölme: imza yalnız ilk parçada, `reply_to` yalnız ilk parçada; parça sınırı çok baytlı karakteri bölmez; teslimat hatası sessiz kalmaz.
4. Ara bildirim yalnız cevap gecikince gider (eşik) ve cevap geldikten sonra ASLA gitmez (yarış).
5. Pano `mcp:` reddi yalnız `oturum` BAŞINDA `mcp:` (strip + harf duyarlı, EDG-086 `startswith` ile aynı); `pano-mcp:x` geçer.

---

### Task 1: `bota_sor` üretim kablolaması + dönüş kaydı + dışa giden scrub + bütçe çivisi

**Files:** Modify `meridian/bot_kanal.py`, `meridian/bot_hafiza.py`, `tests/test_bot_kanal_v593.py`, `tests/test_bot_hafiza_v596.py`.

**Interfaces:** Produces: `HindsightHafiza.donus_yaz(bot, mesaj, cevap, etiketler) -> bool` (retain `async: true`, bağlam "sohbet dönüşü", `metadata.kaynak` "bot_kanal", içerik `"Operatör: <mesaj>\n@<bot>: <cevap>"` her biri scrub + `DONUS_TAVANI = 2000` karakter); `Hafiza` protokolüne `donus_yaz`; `bota_sor(..., hafiza=None)` → üretim varsayılanı `HindsightHafiza()` (test sahteleri açık verir); defter `sohbet` satırına `hafiza_durumu` ∈ `yazildi | yazilamadi | atlandi`; etiketler `bot:<ad>`, `kanal:<kanal>`, `sohbet_donusu`, ve `arac_siz_veri is True` ise `arac_siz_veri`, `arac_olculemedi` ise `arac_olculemedi`; modele giden mesaj `notify.scrub(mesaj)`.
- [ ] Testler (RED): dönüş kaydı çağrılır ve etiketler/bağlam doğru; hafıza istisnası cevabı düşürmez ve `hafiza_durumu == "yazilamadi"` + `bot_hafiza_donus_hatasi` olayı (`neden` kapalı küme — Task 2 ile ortak yardımcı); kota dolu/hata turunda dönüş YAZILMAZ (`atlandi`); modele giden metin scrub'lı (sahte taşıyıcı gördüğü metni kaydeder; sır biçimli değer maskeli); `hatırla:` gövdesi değişmedi (v596 pinli gövde); çapraz çivi: `HermesTasiyici` varsayılan zaman aşımı ≥ `SOHBET_API_DENEME × SOHBET_ISTEK_ZAMAN_ASIMI_SN` (`ops/sohbet_profili_uret.py` sabitleri `tests.conftest.betikten_modul_yukle` ile).
- [ ] "henüz bağlı değil" çivileri yeni gerçeğe çevrilir: `hafiza` verilmezse gerçek sınıf; anahtar yoksa `yazilamadi` (sessiz değil). `_HAFIZA_BAGLI_DEGIL` kolu kaldırılıyorsa v593 emeklilik çivisi emsaliyle (`test_hazir_degil_dali_emekli`).
- [ ] Mutasyon: scrub'ı modele giden yoldan kaldır; `async` false yap (gövde çivisi); hata yolunda cevabı düşür; etiket `arac_siz_veri` koşulunu ters çevir — her biri kırmızı.

### Task 2: `unut:` iki adım + `onayla: unut <kod>` + `geri al: <kod>` + yapısal `neden`

**Files:** Modify `meridian/bot_kanal.py` (`_KOMUT`/`KOMUTLAR`/`komut_oneki`/`_komut`/`_unut`), `meridian/bot_hafiza.py` (`unut` → `unut_adaylari(bot, ifade) -> list[(id, kesit)]` salt-okur + `unut_uygula(bot, idler, ifade)`; PATCH hatasında istisna `denenen` + `kalan` taşır; ağ/HTTP/biçim hatalarına `neden` özniteliği), `meridian/codelaw.py` (`DECLARED_SINKS` yeni `bot_unut_bekleyen.json`), `meridian/telegram_dinleyici.py` (`_komut_giden`: `unut:` yanıtta alıntı metni sorgu olur — gövde boşsa), testler v593/v596/v592/v214.

**Interfaces:** `komut_oneki` iki kelimeli komutları tanır (`geri al`, ad_katla ile `geri_al`); `KOMUTLAR = ("hatirla", "unut", "onayla", "geri_al")`; bekleyen aday kaydı `state/bot_unut_bekleyen.json` `{kod: {bot, idler, ifade, ts, son}}` — kod 6 hex, ömür 15 dk, yazım `store` atomik + kilit; `onayla: unut <kod>` yalnız AYNI bot ve süresi dolmamış kod; uygulanınca kayıt `uygulandi` işaretlenir (silinmez) ve `geri al: <kod>` o idleri `valid` yapar; olay `neden` kapalı küme: `anahtar_yok | http_<kod> | ag | zaman_asimi | bicim | kimlik | beklenmeyen`.
- [ ] Testler: ilk adım PATCH atmaz (casus); kod yabancı bot/süresi dolmuş/bilinmiyorsa ret + olay; onay PATCH ≤3; kısmi hata `denenen`/`kalan` deftere; `geri al` valid PATCH; Telegram yanıtında `unut:` gövdesiz → alıntı ilk satırı sorgu; `komut_oneki` tablosu genişler, AST çivisi yeşil kalır; v214 `SINK_TABANI`.
- [ ] Mutasyon: ilk adımda PATCH; bot eşitliği kontrolünü kaldır; süre kontrolünü kaldır; `neden` türetimini sabitle — her biri kırmızı.

### Task 3: Telegram `main()` + birim (etkin değil) + 4096 bölme + ara bildirim + ilk ofset

**Files:** Modify `meridian/telegram_dinleyici.py` (`main(argv)` → `dongu(bota_sor=bot_kanal.bota_sor)`; `isle`: cevap `TELEGRAM_TAVANI = 4096` bölmesi — imza + `reply_to` yalnız ilk parçada, satır sınırında böl, tek satır tavanı aşarsa karakter sınırında; ara bildirim enjekte `bildir` + `ARA_BILDIRIM_ESIGI_S = 8` `threading.Timer`, cevap gelince iptal, yarışta cevap sonrası GÖNDERİLMEZ; ilk koşumda ofset dosyası yoksa birikmiş güncellemeleri ATLA — son `update_id + 1`, olay `telegram_ilk_ofset`), `meridian/web/app.js` (`TELEGRAM_CHAT_ID` talimatı: "dinleyici çalışırken tarayıcıdan getUpdates çağırmayın (409); yalnız özel sohbet kimliği — pozitif sayı"), Create `deploy/oracle-a1/meridian-telegram.service` (Type=simple, User=ubuntu, `ExecStart=/opt/meridian/.venv/bin/python -m meridian.telegram_dinleyici`, WorkingDirectory=/opt/meridian, `Restart=on-failure`, filo ortak sertleştirme, `ReadWritePaths=/opt/meridian`, `After=network-online.target meridian-botlar.service` yalnız sıralama), `tests/test_ansible_a0_v451.py` (`UZUN_OMURLU_BIRIMLER`), `tests/test_h3_tur2_v174.py` (`SERTLESTIRILEN`), Test `tests/test_telegram_birimi_v602.py` + v592 eklemeleri.
- [ ] Testler: bölme (4096 sınırı, çok baytlı karakter, imza yalnız ilk parça, `reply_to` yalnız ilk parça, parça teslimat hatası `telegram_parca_teslim_hatasi`); ara bildirim eşik altı GİTMEZ / eşik üstü BİR kez gider / cevap sonrası gitmez (sahte saat); ilk ofset atlama; `main` sır yoksa `SystemExit` (mevcut `dongu` davranışı); birim çivileri (v601 emsali: etkin değil, `LoadCredential` BUGÜN YOK — G3b erteleme çivisi, sertleştirme, v553/v554/v563 yeşil); `ops/filo.py` birimi bot SAYMAZ (v348 — `HERMES_HOME` yok).
- [ ] Mutasyon: imzayı her parçaya bas; timer iptalini kaldır; ilk ofset atlamasını kaldır; birime `LoadCredential` ekle — her biri kırmızı.

### Task 4: Pano `mcp:` oturum reddi

**Files:** Modify `meridian/sohbet.py` (`_sohbet_turu`: `oturum.strip()` `mcp:` ile başlıyorsa `ValueError`), `tests/` (sohbet testi + v450 hizası: `pano-mcp:yanki` geçer).
- [ ] Testler: `POST /api/sohbet` `oturum: "mcp:sef"` → 400 ve hiçbir satır yazılmaz; `" mcp:sef"` → 400; `"MCP:sef"` → geçer (sayım `startswith` harf duyarlı — hizalı); `pano-mcp:x` geçer. Önek sabiti tek kaynak: `research/olcumler/edg086_pano_sohbet/sayim.py::MCP_OTURUM_ONEKI` ile `meridian/mcp_server.py` literalini `meridian/sohbet.py`de TEK sabite topla (`MCP_OTURUM_ONEKI`), ikisi oradan okusun.
- [ ] Mutasyon: reddi kaldır → kırmızı.

---

## Sonra (G4 dışı)
- G3b sır dilimi (API_SERVER_KEY + `.env` tohumlama + credential drop-in'leri: botlar + telegram) — operatör kararları K-G3b-1/2.
- G3c + Telegram test-ateşleme (tek soru → gerçek araçlı cevap; rapora yanıt → doğru bot; hatırla/unut iki yönlü; yabancı sohbet sessiz; ara bildirim; 4096 bölme).
- G5 ölçüm kartı EDG-2026-107 (ADIM-0 ilk canlı gün).
