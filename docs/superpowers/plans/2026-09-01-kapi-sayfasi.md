# TSK-090 Kapı Sayfası v1 — Uygulama Planı

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:subagent-driven-development.

**Goal:** Pano'ya salt-okunur "Kapı" sayfası — APISIX'in rotaları, LLM zincirleri, sağlığı ve
metrikleri; tarayıcı 9180/9091'e asla gitmez, her şey `api.py` vekilinden gelir.

**Architecture:** `meridian/api.py`'ye tek GET ucu `/api/gateway` (Admin API + prometheus'u
sunucu-tarafında okur, admin anahtarı yanıta asla girmez); `ui/src/pano/yuzeyler/kapi/` yeni
yüzey mevcut tasarım diliyle; sidebar + route kaydı; `npm run build` artefaktı.

**Spec:** ROADMAP.md `[TSK-090]` What/Why blokları (operatör talimatı verbatim orada).

## Global Constraints
- Sır sızmaz: admin anahtarı (X-API-KEY) YALNIZ sunucu-tarafı istekte; yanıt gövdesinde,
  logda, hata mesajında ASLA. Rotalardaki `"$env://..."` literal referansları sır DEĞİLDİR
  ve olduğu gibi gösterilir (tasarım: "sırlar $ENV referansı olarak, değer asla").
- Uydurma yasağı: ölçülemeyen alan `None` + `neden` (örn. yerel makinede 9180 yok →
  `{"olculemedi": "admin_api_erisilemez"}` sınıfı alanlar; sıfır uydurulmaz).
- Pano token sözleşmesi: uç, diğer uçlarla aynı `x-meridian-token` doğrulamasından geçer.
- Vekil zaman aşımı kısa (≤2 sn/istek): kapı düşükken pano asılı kalmaz.
- Yasa 4/6 ve mevcut api.py idiomları (v287 `/api/infra` bloğu emsal — oku, taklit et).
- UI: mevcut yüzey idiomu (`SistemSagligiYuzey.tsx` emsal); yeni bağımlılık YOK.

---

### Task 1: `/api/gateway` motor ucu

**Files:** Modify `meridian/api.py` (v287 `/api/infra` bloğunun yakınına yeni blok) ·
Test: `tests/test_kapi_yuzeyi_v361.py` (yeni)

**Produces (yanıt şeması — UI bunu tüketir):**
```json
{
  "saglik": {"admin_api": true, "prometheus": true, "neden": null},
  "rotalar": [{
    "id": "llm-danisma", "uri": "/llm/v1/chat/completions",
    "zincir": [{"ad": "birincil-nemotron", "model": "nvidia/…:free", "oncelik": 10}],
    "fallback_tetikleri": ["http_429", "http_5xx"],
    "temizlenen_basliklar": ["Authorization", "X-Forwarded-For", "X-Real-IP"]
  }],
  "metrikler": {"kaynak_ok": true, "rota_basina": {"llm-danisma": {"istek_n": 12,
      "durum_kirilimi": {"200": 10, "429": 2}}}, "neden": null},
  "fazlar": {"faz1_llm": "canli", "faz2_fmp": "bekliyor", "faz3_ingress": "bekliyor",
             "faz4_filo": "bekliyor"}
}
```

**Kaynaklar (sunucu-tarafı):** Admin `GET http://127.0.0.1:9180/apisix/admin/routes`
(anahtar `/opt/apisix/.env-apisix` içindeki `APISIX_ADMIN_KEY=` satırından; dosya yoksa
`saglik.admin_api=false`, `neden` dolu) · `GET http://127.0.0.1:9091/apisix/prometheus/metrics`
(satır süzme: `apisix_http_status{...route="<id>"...} <n>` sayaçları toplanır; parse edilemeyen
satır sessiz atlanmaz — sayısı `metrikler.atlanan_satir` alanına).

**Adımlar (TDD):** her davranış için önce kırmızı test:
1. token'sız istek → 401.
2. Admin/prometheus erişilemez (monkeypatch'li urlopen hata) → 200 + `saglik.*=false` +
   `neden` dolu; İSTİSNA YUTULMAZ, sınıflanır (Yasa 4 işareti gerekmeden — sinyal yanıtta).
3. Sahte admin yanıtı (routes listesi bizim `routes.yaml` şeklinde) → `rotalar` şeması birebir;
   `auth.header.Authorization` alanı "$env://OPENROUTER_AUTH" literal'i olarak geçer.
4. SIZINTI ÇİVİSİ: sahte admin anahtarı test değeri yanıt JSON'unda HİÇBİR yerde geçmez.
5. Sahte prometheus metni → `rota_basina` doğru toplanır; bozuk satır `atlanan_satir`e sayılır.
6. Zaman aşımı parametresi ≤2 sn (çağrı imzasında assert).
Commit: `git add meridian/api.py tests/test_kapi_yuzeyi_v361.py`.

### Task 2: Kapı yüzeyi (UI)

**Files:** Create `ui/src/pano/yuzeyler/kapi/KapiYuzey.tsx` · Modify
`ui/src/navigation/sidebar/sidebar-items.ts` (yeni girdi: id `gateway`, url
`/dashboard/gateway`, ad "Kapı") · Modify route kaydı (infrastructure sayfasının kayıt
deseni neredeyse — `App.tsx`/`Yuzey.tsx` — aynısını uygula) · Build: `cd ui && npm run build`.

**Consumes:** Task 1 şeması, `apiGet<T>("/api/gateway")` (`ui/src/pano/veri.ts`).

**Bölümler (v1, salt-okunur):**
1. Sağlık şeridi: admin/prometheus rozetleri + `neden` görünür (ölçülemedi ≠ sağlıklı).
2. LLM rotaları: rota kartı — zincir sırası (öncelik desc), model adları, fallback tetikleri,
   temizlenen başlıklar; "kaynağı repo'da aç" bağı `deploy/apisix/routes.yaml`e işaret eder
   (metin/href, düzenleme yok).
3. Metrikler: rota-başına istek + durum-kodu kırılımı (kaynak_ok=false ise boş-durum bileşeni).
4. Fazlar: 2/3/4 "bekliyor" rozetleri (sabit metin DEĞİL — Task 1 `fazlar` alanından).
Boş/ölçülemedi durumları üç-durum ayrık (dolu/boş/ölçülemedi) — TSK-086 emsali.

**Adımlar:** yüzeyi yaz → sidebar+route kaydı → `npm run build` temiz → görsel doğrulama
Rol-1'de (ben yaparım, ajan değil) → commit (`git add ui/... meridian/web/pano-assets/...
meridian/web/pano.html` — build artefaktı canlıya giden şeydir).

### Task 3 (Rol-1, ajan değil): suite + dağıtım + canlı doğrulama
Hedefli koşumlar → tam suite → push → rsync → restart (operatör) → canlıda `/api/gateway`
200 + pano sayfası ekran doğrulaması → ROADMAP/TSK-090 status + günlük.
