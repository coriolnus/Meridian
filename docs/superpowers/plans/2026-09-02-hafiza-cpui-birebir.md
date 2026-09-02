# TSK-108 — Hafıza Sayfası CP-UI Birebirleştirmesi Uygulama Planı

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development
> (recommended) or superpowers:executing-plans to implement this plan task-by-task.
> Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Pano'daki Hafıza sayfasını Hindsight Control Plane'in (v0.9.2) gerçek bilgi
mimarisine birebirleştirmek — operatör kararı 2026-09-02: "CP UI'ı inceleyip birebir taşı"
(orijinal talimat 2026-09-01: "hindsight-dashboard bizim kendi UI'ımıza birebir ayrı bir
sayfa olarak aktarılmalı" — v1 bunu dar yorumlamıştı, operatör düzeltti).

**Architecture:** Mevcut `/api/hindsight` vekili GENİŞLER (yeni salt-okunur uçlar + recall
POST'u "sorgu sınıfı" olarak vekillenir); `HafizaYuzey` dört-bölüm düzeninden CP'nin
bank-kapsamlı KENAR ÇUBUĞU + görünüm-anahtarı düzenine geçer. Kod taşınmaz — Next/i18n/CP
bileşenleri bizim Vite+React yığınımıza AKTARILMAZ; taşınan şey bilgi mimarisi, görünüm
başına içerik ve etkileşim sözleşmesi. Etiketler Türkçe.

**Tech Stack:** Mevcut pano yığını (Vite+React+shadcn) · FastAPI vekil (v361 deseni) ·
Upstream referans: github.com/vectorize-io/hindsight tag v0.9.2, `hindsight-control-plane/src/`.

**Spec:** Bu plan + ölçülen CP yapısı (aşağıda). Upstream dosyaları implementer için
BAĞLAYICI referanstır: her görünümün alan/etkileşim listesi oradan OKUNUR, tahmin edilmez.

## Ölçülen CP yapısı (2026-09-02, v0.9.2 kaynağından — plan bunlara yaslanır)

- İki sayfa: `dashboard` (bank listesi/genel) + `banks/[bankId]?view=<id>` (asıl yüzey).
- Kenar çubuğu (sidebar.tsx, sıra aynen): `home` (Ana Sayfa, Home ikonu) · `data`
  (Bellekler, Database) · `knowledge` (Bilgi Tabanı, Network) · `recall` (Recall, Search) ·
  `reflect` (Reflect, Sparkles) · `documents` (Belgeler, FileText) · `entities`
  (Varlıklar, Users) · `profile` (Yapılandırma, Settings). Görünüm `?view=` ile değişir.
- Görünüm bileşenleri (components/): home-view (bank-stats + freshness + next-refresh
  içerir) · data-view (bellek listesi + fact-type filtresi + memory-detail-panel/modal +
  edit/invalidate diyalogları) · knowledge-base-view · entities-view (+graph) ·
  documents-view (+chunk modal) · mental-models-view (+detail/diagnostics) ·
  llm-requests-view · audit-logs-view · bank-operations-view · bank-config-view ·
  memory-defense-section · observation-history-view · search-debug-view · constellation
  (graf görseli) · llm-health-dialog.
- CP'nin kendi girişi var (access key) — BİZDE YOK: pano oturumu tek kimlik katmanı.
- CP api route'ları 1:1 dataplane vekilidir — bizim `/api/hindsight` genişlemesinin
  yol haritası CP'nin `src/app/api/` ağacıdır (aynı uçlar, bizim adlandırmayla).

## Kapsam kararı (ruling, defterde)

- **Faz-1 (bu plan):** TÜM salt-okunur görünümler + `recall` oyun alanı (POST ama sorgu
  sınıfı — durum değiştirmez, vekilde `POST /api/hindsight/recall` olarak açılır ve
  SALT-OKUNUR sözleşmenin beyanlı istisnasıdır; gövde: bank+query+limit, süzülmüş geçiş).
- **Faz-1 DIŞI (görünür-devre-dışı çizilir, gizlenmez):** yazan her şey — bellek
  düzenleme/geçersizleme, config PATCH, reflect tetikleme, consolidate/recover, document
  reprocess, webhook CRUD. Bu düğmeler CP'deki yerlerinde DURUR ama devre-dışı + "yazma
  yolu Faz-2 (operatör kararı bekler)" rozetiyle — birebirlik görünümde korunur,
  yazma-vekili kararı ayrı kaleme (TSK-109 adayı) kalır.
- Graflar (constellation/entities-graph): Faz-1'de veri uçları vekillenir, çizim mevcut
  yığınla sade SVG/canvas (CP'nin kütüphanesi taşınmaz); "birebir"lik düzen ve bilgi
  düzeyindedir, piksel değil.

## Global Constraints

- Sır/ölçülemezlik/zaman-aşımı sözleşmeleri v361/v375 emsalleriyle AYNEN (200+neden,
  `_kapi_maskele`, ≤2 sn üst çağrı).
- Vekil uçları CP'nin api ağacından TÜRETİLİR; her yeni uç v375 dosyasına çivi ekler
  (kırmızı-önce). Alan adları upstream'den ölçülür — v375'in "fixture=gerçek gövde" dersi
  bağlayıcı (analojiyle gövde uydurmak YASAK; ölçülemeyen şekil sentetik etiketiyle ayrılır).
- UI: alanlar.ts `memory` kaydı yeni bölüm yapısına göre GÜNCELLENİR (bölüm kimlikleri
  `hafiza-*` kalır, yeni görünümler eklenir); komutlar.ts derin-bağları genişler.
- Ajan kuralları: git yok · seri kapsam-pytest · npm kontrol/build serbest · tam suite Rol-1.
- Push: api.py'a dokunan turda tam suite hükmü.

## Görevler

### Task 1: Vekil genişlemesi (api.py) — TDD
**Files:** Modify `meridian/api.py` (HAFIZA bloğu) · Test `tests/test_hafiza_yuzeyi_v375.py`
**Yeni uçlar** (hepsi `_auth` kapılı, 200+neden; upstream yolu CP api ağacındaki eşi):
`/api/hindsight/ozet` (banks+stats+timeseries — mevcut toplu uç genişler) ·
`/liste` (mevcut; fact_type/scope filtreleri eklenir) · `/detay` (mevcut; history eklenir) ·
`/varliklar` + `/varlik-graf` · `/belgeler` + `/belge-parcalari` · `/zihin-modelleri` (+detay/tarihçe) ·
`/bilgi-tabani` (tree+search+page) · `/gozlemler` (+scopes) · `/llm-istekleri` (+stats) ·
`/denetim` (+stats) · `/islemler` (operations) · `/yapilandirma` (GET config) ·
`POST /recall` (beyanlı sorgu-sınıfı istisna).
- [ ] Her uç için kırmızı-önce çivi (env-yok/sır-sızmaz/akış/parametre-kırpma kalıpları
  v375'teki mevcut kalıplarla) → asgari kod → yeşil → mutasyon turu.
- [ ] Kapsam serisi: v375 + v361.

### Task 2: UI yeniden kurulumu — kenar çubuğu + görünümler (1/2: iskelet + home/data/documents)
**Files:** Rework `ui/src/pano/yuzeyler/hafiza/` (HafizaYuzey → kabuk: bank seçici üstte,
CP sıralı kenar çubuğu solda, `?view=` yerine yerel state; uctipleri.ts yeni uçlarla) ·
Modify `alanlar.ts`/`komutlar.ts`.
- [ ] Kabuk + home (stats/freshness) + data (liste+filtre+detay paneli) + documents
  (+chunk çekmecesi); her görünümün alan listesi upstream bileşeninden okunarak.
- [ ] Faz-1-dışı düğmeler görünür-devre-dışı rozetiyle.
- [ ] `npm run kontrol` + build.

### Task 3: UI görünümler (2/2: knowledge/recall/entities/mental-models/operasyon-denetim-llm/config)
- [ ] Kalan görünümler; recall oyun alanı (sorgu kutusu + sonuç listesi, POST /recall).
- [ ] Entities graf sade çizim; memory-defense bölümü audit görünümünde CP'deki yerinde.
- [ ] kontrol + build; bundle adı rapora.

### Task 4 (Rol-1): dal-sonu
- [ ] Tam suite (donmuş ağaç, üçlü) · ROADMAP hizası · commit zinciri + push · dağıtım
  penceresi + canlı doğrulama (operatörle) · eski bundle temizliği.
