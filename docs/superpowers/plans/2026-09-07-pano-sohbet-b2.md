# TSK-012 dalga-B — B2 UI uygulama planı (Ajan yüzeyinde sohbet + öneri kartları + kota + ⌘K devri)

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:subagent-driven-development.

**Goal:** Yeni panoda (`ui/`, React/TSX) Ajan yüzeyinin KİLİTLİ yazma şeridini `/api/sohbet` ile açmak; sohbet geçmişi, kaynak atıfları, kota
göstergesi, sohbet önerilerinin onay kuyruğunda görünmesi ve ⌘K paletinin sohbet girişine odaklanması.
**Spec:** `docs/superpowers/specs/2026-09-07-pano-sohbet-design.md` §1-§2, §4 B2 (operatör onayı 19:1xZ). **Backend (canlı, dağıtım #27):**
`POST /api/sohbet {mesaj, oturum?}` → `{cevap, kaynaklar[], turlar[], model, sure_s, jeton_giris, jeton_cikis, kota_bugun, oneri_id?, llm_dustu?}` ·
`GET /api/sohbet?oturum=&n=` → geçmiş + künye + kota · `GET /api/sohbet/kota` → `{bugun|null, kalan, tavan, neden}` · `GET /api/approvals` (pending,
`kaynak:"sohbet"` satırları `tur/hedef/gerekce/durum`) · `POST /api/approvals/{id}` (mevcut karar ucu). Kesin alan adları için `meridian/api.py::api_sohbet`,
`api_sohbet_gecmis`, `api_sohbet_kota` ve `meridian/sohbet.py` okunur (ÖLÇ, varsayma). Kart: `research/cards/EDG-2026-086-pano-sohbet-kalite.yaml`.

## Global Constraints
- `ui/` tek yer; `meridian/` DOKUNULMAZ (backend değişikliği gerekirse rapora "eksik uç" yaz, kendin ekleme). Build ÇALIŞTIRMA (`npm run build`
  Rol-1'in — dagit 5c mtime kapısı); `npm run typecheck`/`tsc --noEmit` ve varsa lint serbest. Test altyapısı ÖLÇ (`ui/package.json`; vitest yoksa
  saf-mantık dosyaları için `node --test` ile küçük çiviler yazılabilir; UI bileşen testi zorlanmaz — raporda beyan).
- Mevcut gramer: `veri.ts::apiGet` (okuma), `gonder.ts::apiPost` (yazma; hata ayrımı), `Ajan.tsx` "iki muhatap, iki kaynak" iskeleti + `SohbetHatti` /
  `YazmaSeridi` (KİLİT nedeni şerhte — kilit AÇILIR ve şerh GÜNCELLENİR: artık `/api/sohbet` var), `OnayKuyrugu.tsx` (öneri kartları buraya; `kaynak:"sohbet"`
  satırları mevcut onay/ret düğmeleriyle), `kabuk/search-dialog.tsx` + `komutlar.ts` (⌘K → "Ajan'a sor" komutu sohbet girişine odaklanır; kanonik adres).
- Jetonlar: renk/aralık yalnız `--color-*` rol jetonları (tokens.json / jetonlar.css); ham hex YASAK (v153 Ç3 sınıfı; `ui/` için v208/v407 çivileri).
- Uydurma yasağı UI'da da: `kota_bugun=null` → "ölçülemedi" yaz, 0 gösterme; `llm_dustu` → "model yok" durumu görünür; boş kaynaklar listesi → "kaynak
  atfı yok" etiketi (kartın uydurma sayımı için görünür sinyal).
- `alarm_ack` önerisi GLOBAL etkilidir (bekleyen tüm alarmları kapatır) — kartta bunu yazan uyarı metni (B1 kaygısı).
- Çapa yasağı (`dosya.tsx:NNN`), sır yok, git yok, alt ajan yok.

## Task 1 — Sohbet paneli (`ui/src/pano/yuzeyler/Ajan.tsx` + gerekirse `ui/src/pano/yuzeyler/ajan/*`)
- Yazma şeridi açılır: metin alanı + gönder; gönderimde `apiPost("/api/sohbet", {mesaj, oturum})`; oturum kimliği `localStorage` (`meridian.sohbet.oturum`),
  yoksa üretilir. Yanıt kartı: cevap metni, `kaynaklar` (araç adı · anahtar) rozetleri, `model` künyesi, `sure_s`, `oneri_id` varsa "öneri onay kuyruğunda"
  bağlantısı (OnayKuyrugu'na rota). `llm_dustu`/`kota dolu` durumları ayrı görsel durum (hata değil, beyan).
- Geçmiş: açılışta `apiGet("/api/sohbet?oturum=…&n=50")`; kronolojik; yeniden yükle düğmesi.
- Kota rozeti: `GET /api/sohbet/kota` → "bugün N/120 · kalan K" ya da "ölçülemedi (neden)".
- Şerhteki KİLİT gerekçesi güncellenir (tarihçe korunur: "2026-09-07 dalga-B ile açıldı").
## Task 2 — Öneri kartları (`OnayKuyrugu.tsx`) + ⌘K devri (`komutlar.ts`, `search-dialog.tsx`)
- `kaynak:"sohbet"` bekleyen satırlar OnayKuyrugu'nda ayrı grup "Sohbet önerileri": tur (plan_onayi/alarm_ack/not), hedef, gerekçe, oturum;
  onay/ret mevcut `POST /api/approvals/{id}` akışıyla (yeni uç yok); `alarm_ack` için global-etki uyarısı; `not` için "icra yok" etiketi.
- ⌘K: "Ajan'a sor…" komutu → Ajan yüzeyine gider ve sohbet girişine odaklanır; komut paletinde serbest metin girildiyse sohbet girişine taşınır.
## Çiviler
- `npm run typecheck` (ya da `tsc --noEmit`) temiz; varsa vitest: `ui/src/pano/yuzeyler/ajan/*.test.ts` — saf mantık: oturum kimliği üretimi, kota metni
  (null→ölçülemedi), yanıt→kart eşlemesi, öneri türü→uyarı metni. Kırmızı-önce.
## Rapor
`.superpowers/sdd/2026-09-07-sohbet-b1/b2-report.md`; dönüş: durum / dosyalar / typecheck+test özeti / eksik uç listesi / kaygılar.
