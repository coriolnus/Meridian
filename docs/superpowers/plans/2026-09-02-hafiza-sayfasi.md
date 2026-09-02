# TSK-091 — Hafıza Sayfası (pano'da Hindsight'ın tam yüzeyi) Uygulama Planı

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development
> (recommended) or superpowers:executing-plans to implement this plan task-by-task.
> Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Pano'ya Hindsight'ın (loopback 8888) salt-okunur tam yüzeyini ekleyen AYRI bir
"Hafıza" sayfası — Kapı sayfası (TSK-090) deseninin birebir eşi.

**Architecture:** api.py'a v361 desenli SALT-OKUNUR vekil (`/api/hindsight` toplu ucu +
iki dar liste/detay ucu; sır dosyadan, gövdeye asla; ölçülemezlik 200+`neden`); UI'da
`yuzeyler/hafiza/` (uctipleri.ts + HafizaYuzey.tsx) ve üç kayıt noktası (Yuzey.tsx,
alanlar.ts, komutlar.ts). Tarayıcı 8888/9999'a ASLA gitmez.

**Tech Stack:** FastAPI (mevcut api.py), urllib (KAPI deseni), React/TS (mevcut pano),
vitest yok — `npm run kontrol` (tsc) + build.

**Spec:** ROADMAP.md `[TSK-091]` What bloğu (operatör talimatı 2026-09-01) + bu plandaki
ölçümler. Ayrıca desen kaynağı: `meridian/api.py::api_gateway` (v361) ve
`ui/src/pano/yuzeyler/kapi/`.

## Ölçülmüş gerçekler (2026-09-02, plan bunlara yaslanır — tahmin değil)

- Hindsight canlı: `hindsight-api.service`, `127.0.0.1:8888`; `GET /health` → 200 (anahtarsız).
- `/v1/*` KİMLİKLİ: `Authorization: Bearer <HINDSIGHT_API_TENANT_API_KEY>` → 200;
  `X-API-Key` → 401. Anahtar `/opt/hindsight/.env` (0600, ubuntu) içinde
  `HINDSIGHT_API_TENANT_API_KEY=` satırında. (ROADMAP'teki "auth varsayılan YOK" endişesi
  bayat — extension kurulu ve zorluyor.)
- Bugünkü bank'ler: `meridian-arsiv`, `smoke-067`. Bot bank'leri HENÜZ YOK — sayfa bunu
  dürüstçe çizer ("bank yok" ≠ "ölçülemedi").
- Kullanılacak uçlar (openapi.json'dan ölçüldü): `GET /health` · `GET /version` ·
  `GET /v1/default/banks` · `GET /v1/default/banks/{id}/stats` ·
  `GET /v1/default/banks/{id}/memories/list` · `GET /v1/default/banks/{id}/memories/{mid}` ·
  `GET /v1/default/banks/{id}/audit-logs` + `/audit-logs/stats` ·
  `GET /v1/default/banks/{id}/llm-requests` + `/llm-requests/stats`.
- ÇAKIŞMA (ruling, defterde): ROADMAP `/api/memory/*` yazar ama `api.py:~1889`da
  `GET /api/memory` ZATEN VAR (lessons.md ucu, Belgeler yüzeyi okur). Vekil öneki
  **`/api/hindsight`** olur; işin iniş commit'inde ROADMAP What satırındaki yol adı da
  düzeltilir (tek-kaynak).
- Bölüm kimlikleri KÜRESEL (`alanlar.ts` sözleşmesi) ve çıplak `hafiza` kimliği Belgeler'de
  dolu → bu sayfanın bölümleri `hafiza-` önekli bileşik kimlikler alır (aşağıda).

## Global Constraints

- Sır sözleşmesi (v361 emsali AYNEN): tenant anahtarı yalnız giden isteğin başlığında yaşar;
  gövdeye, `neden`e, loga GİRMEZ; `_kapi_maskele` ikinci hat olarak yeniden kullanılır.
- Ölçülemezlik NORMAL HÂL: dev makinesinde 8888 yok → 500 DEĞİL, 200 + bölüm-başına
  `saglik/neden` alanları; `None` ≠ `0`.
- Her upstream çağrı zaman aşımı ≤2.0 sn (`KAPI_ZAMAN_ASIMI_S` emsali; sabit ayrı tanımlanır).
- Vekil SALT-OKUNUR: yalnız GET; PATCH/DELETE/POST upstream'e ASLA taşınmaz. Curation
  DÜZENLEMESİ v1-DIŞI (CP UI tünelli araç onun yeri; sayfa okur-gösterir).
- Yasa 4 (sinyalsiz yutma yok) · Yasa 6 (her alanın okuyucusu sayfada) · uydurma yasağı ·
  bedel yasası. TDD zorunlu; testler SERİ; vNNN çakışma kontrolü.
- Ajanlar: git yok, tam suite yok, pytest dışı koşum yok, `monkeypatch.undo()` yok.

---

### Task 1: api.py `/api/hindsight` vekili (motor) — TDD

**Files:**
- Modify: `meridian/api.py` (v361 KAPI bloğunun hemen ardına yeni blok: "HAFIZA YÜZEYİ")
- Test: `tests/test_hafiza_yuzeyi_vNNN.py` (`ls tests/ | grep -o "v[0-9]*" | sort -V | tail`
  ile bir SONRAKİ boş numarayı al; v371 TSK-106'ya gitmiş olabilir)

**Interfaces (Produces — Task 2 bunlara yaslanır):**
- `GET /api/hindsight` → `{saglik: {erisilebilir: bool, surum: str|null, neden: str|null},
  bankalar: [{bank_id, stats: {...}|null, stats_neden: str|null}], bankalar_neden: str|null,
  kota: {bank_id → {llm_stats: {...}|null, neden: str|null}},
  operasyon: {bank_id → {audit_stats: {...}|null, neden: str|null}}}`
- `GET /api/hindsight/liste?bank=<id>&limit=<1..200>&offset=<n>` →
  `{ogeler: [...], neden: str|null}` (upstream `memories/list` gövdesi süzülmeden ama
  anahtar-maskeli geçer; `limit` sunucuda 200'e KIRPILIR)
- `GET /api/hindsight/detay?bank=<id>&kimlik=<mid>` → `{oge: {...}|null, neden: str|null}`
- Hepsi `_auth` kapılı (mevcut pano oturumu), hepsi 200-her-zaman.

**Sabitler (koda birebir):**
```python
HAFIZA_TABAN_URL = "http://127.0.0.1:8888"
HAFIZA_ENV_DOSYASI = "/opt/hindsight/.env"          # 0600, F9 dışı; testler monkeypatch'ler
HAFIZA_ANAHTAR_ONEKI = "HINDSIGHT_API_TENANT_API_KEY="
HAFIZA_ZAMAN_ASIMI_S = 2.0
HAFIZA_LISTE_TAVANI = 200
```

**Anahtar okuma + GET yardımcıları:** `_kapi_admin_anahtari` / `_kapi_getir` DESENİ
kopyalanmaz — İKİ yardımcı parametrikleştirilerek YENİDEN KULLANILIR (tek-kaynak):
`_kapi_admin_anahtari`'nın gövdesi `(dosya, onek)` parametreli `_env_anahtari(dosya, onek)`
yardımcısına çıkarılır; eski imza `_env_anahtari(KAPI_ENV_DOSYASI, KAPI_ANAHTAR_ONEKI)`
çağıran bir sarmalayıcı olarak KALIR (mevcut v361 çivileri kırılmaz). `_kapi_getir` zaten
parametrik — aynen kullanılır (`Authorization: Bearer …` başlığıyla).

- [ ] **Step 1: Kırmızı testler.** Asgari vakalar (hepsi `TestClient` + monkeypatch;
      upstream'i `_kapi_getir`i monkeypatch'leyerek taklit et — gerçek 8888 YOK):
      `test_env_yokken_200_ve_neden_dolu` · `test_anahtar_govdeye_sizamaz` (sahte anahtarı
      cevap gövdesinin tamamında ara — bulunursa kırmızı) · `test_bankalar_ve_stats_akisi` ·
      `test_liste_limit_tavani_kirpar` (limit=9999 → upstream'e ≤200 gitti) ·
      `test_detay_olcum_yoklugu_null_neden` · `test_yalniz_get_yontemleri` (POST → 405) ·
      `test_auth_kapisi` (çerezsiz → 401). Koş, hepsinin KIRMIZI olduğunu gör.
- [ ] **Step 2: `_env_anahtari` çıkarımı + eski sarmalayıcı; v361 çivilerini SERİ koş
      (`tests/test_kapi_yuzeyi_v361.py`) — yeşil kalmalı.**
- [ ] **Step 3: Üç ucu yaz (asgari).** v361 bloğunun yorum sözleşmesi (sır üç sızıntı yolu,
      ölçülemezlik, zaman aşımı) yeni blokta Hindsight adlarıyla tekrarlanmaz — kısa yorum
      v361 bloğuna ATIF verir ("sözleşme aynı, kaynak: KAPI YÜZEYİ bloğu").
- [ ] **Step 4: Kapsam testlerini SERİ koş; yeşil.** `-q` verme.
- [ ] **Step 5: Rapor** (commit YOK — git Rol-1'in).

### Task 2: UI — `yuzeyler/hafiza/` + üç kayıt

**Files:**
- Create: `ui/src/pano/yuzeyler/hafiza/uctipleri.ts` (alan adları Task 1 api.py'ı OKUYARAK;
  sembol çapaları, satır numarası değil)
- Create: `ui/src/pano/yuzeyler/hafiza/HafizaYuzey.tsx`
- Modify: `ui/src/pano/Yuzey.tsx` (`memory: HafizaYuzey` — anahtar `memory`; `hafiza` bölüm
  kimliğiyle karışmasın diye yüzey anahtarında da İngilizce emsal [gateway] izlenir)
- Modify: `ui/src/pano/alanlar.ts` (Kapı kaydının HEMEN ARDINA; şablon alanı
  "(şablonda karşılığı yok — Meridian'a özgü)")
- Modify: `ui/src/pano/komutlar.ts` (arama anahtarları)

**Interfaces (Consumes):** Task 1'in üç ucu, birebir alan adlarıyla.

**alanlar.ts kaydı (koda birebir; ikonlar lucide'den, dosyadaki mevcut import desenine ekle):**
```ts
  memory: {
    sablon: "(şablonda karşılığı yok — Meridian'a özgü)",
    baslik: "Hafıza",
    soru: "Botların biriktirdiği bellek ne durumda, kim ne öğreniyor?",
    ikon: Brain,
    grup: "Panolar",
    bolumler: [
      { kimlik: "hafiza-bankalar",  baslik: "Bank'ler",          soru: "Hangi bank'ler var, kaç bellek taşıyorlar?", ikon: Landmark },
      { kimlik: "hafiza-bellekler", baslik: "Bellek listesi",    soru: "Ne hatırlanıyor, kaynağı ne?", ikon: BookOpen },
      { kimlik: "hafiza-operasyon", baslik: "Operasyon",         soru: "Retain/consolidation akıyor mu, ne başarısız?", ikon: Activity },
      { kimlik: "hafiza-kota",      baslik: "LLM kotası",        soru: "Hafıza motoru ana modelden ne kadar çağrı yaktı?", ikon: Gauge },
    ],
  },
```
(Memory Defense olayları ayrı bölüm DEĞİL: ölçülen API'de ayrı ucu yok; audit-logs
akışının içinde etiketli satır olarak `hafiza-operasyon` bölümünde çizilir. Bu bedel
beyanı HafizaYuzey.tsx başlık yorumuna yazılır.)

- [ ] **Step 1: uctipleri.ts** — üç gövde tipi; her alan `x?: T` / `x: T | null` ayrımı
      kapi/uctipleri.ts'in gerekçe yorumuyla (oraya ATIF, kopya değil).
- [ ] **Step 2: HafizaYuzey.tsx** — KapiYuzey.tsx iskeleti emsal: tek `useEffect` +
      15 sn yoklama YOK (Kapı 15 sn yoklamıyorsa aynı kadans; KapiYuzey'in gerçek kadansını
      OKU ve aynısını uygula), dört bölüm `bolum-hafiza-*` çapalarıyla; üç-durum ayrık çizim
      (ölçüldü-boş / ölçülemedi-neden / dolu); bank seçici + liste sayfalama
      (`/api/hindsight/liste` limit/offset), satıra tıkla → detay çekmecesi
      (`/api/hindsight/detay`).
- [ ] **Step 3: Yuzey.tsx + komutlar.ts kayıtları.** komutlar.ts:
      `memory: ["hafiza", "hindsight", "bellek", "bank", "retain", "consolidation", "recall"]`.
- [ ] **Step 4: `cd ui && npm run kontrol && npm run build`** — ikisi de temiz; build
      çıktısındaki yeni hash'li dosyayı rapora yaz (git işlemi YOK).
- [ ] **Step 5: Rapor.**

### Task 3 (Rol-1, ajan değil): dal-sonu

- [ ] Tam suite (arka plan, `-n 4`, donmuş ağaç, üçlü hüküm) — motor değişti.
- [ ] ROADMAP TSK-091 What'taki `/api/memory/*` → `/api/hindsight/*` düzeltmesi + v351.
- [ ] Tek commit zinciri + push; dağıtım ayrı karar (dagit reçetesi).
- [ ] Dağıtım sonrası A1'de canlı doğrulama: pano üzerinden sayfa + `neden` alanlarının
      gerçek 8888'le dolu/boş halleri; tarayıcı doğrulaması operatöre bırakılmaz.
