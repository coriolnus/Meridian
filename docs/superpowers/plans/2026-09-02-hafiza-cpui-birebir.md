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

## Operatör görsel turu (2026-09-02 akşam, dağıtım sonrası) — beş bulgu → T5/T6

Bulgular (operatör): ① küresel nav'da Hafıza alt bölümleri + yüzey-içi kenar çubuğu = çift nav;
alt sekmeler YALNIZ uygulama UI'ında olmalı; ayrıca "Belgeler" rafı "Hafıza" + "Karar belgeleri"
taşıyor — ad çakışması, konsolide edilmeli · ② "Hafızaya giren kayıtlar" grafiği CP'de sürekli
(recharts), bizde merdiven çubuk · ③/④ constellation yok; varlık grafı (çember yerleşimi)
orijinaliyle ilgisiz · ⑤ Bank Configuration CP'de form (alanlar görünür), bizde yalnız sayaç +
salt-okunur dökum — "konfigürasyon yapacak yer bile yok".

Ölçüm (Rol-1): CP api ağacında constellation yolu YOK — `constellation.tsx` + `graph-data.ts`
mevcut uçlardan istemci tarafında kurar; CP grafikleri `recharts ^3.5`; bizim `ui/package.json`
`recharts ^3.8` zaten var → yeni vekil ucu / bağımlılık gerekmez. Raf: `alanlar.ts` "Belgeler"
yüzeyinin `hafiza` bölümü ("Hangi dersler biriktirildi?") eski dersler kategorisi.

Rulings: R20 küresel nav'da Hafıza TEK girdi (yüzey `altBolumNav: "yuzey-ici"` beyanı), yüzey-içi
kenar çubuğu kalır; komut paleti/derin bağlar bölüm kayıtlarını kullanmaya devam eder ·
R21 KESİN (operatör 2026-09-02 ~19:05: "raftakilerin içeriklerini mevcut yeni sayfa ile duplike
olmayacak şekilde konsolide et — redirect ya da ikisini tek yerde vermek değil"): "Belgeler" rafı
yüzeyi KALKAR; dersler (`/api/memory` = state/lessons.md damıtımı, Hindsight korpusunda yok) →
Hafıza ▸ Bilgi Tabanı "Meridian dersleri" alt sekmesi (mantık taşınır); karar arşivi
(`/api/karar-belgeleri` = docs/KARAR-*/HUKUM-*, Hindsight'a ingest edilmiş → çift) → Hafıza ▸
Belgeler listesine yol/ad eşlemesiyle birleşir (tür rozeti + süzgeç, eşleşmeyen dürüst); yönlendirme
yok, raf dizini silinir, parite çivileri gerekçeli hizalanır ·
R22 ana sayfa grafiği CP'nin recharts tipi/kova çözünürlüğü/pencere eşlemesiyle birebir ·
R23 constellation EVET (operatör: "bayağı başarılı"), canvas + kendi kuvvet yerleşimi, kütüphane
yok; varlık grafı aynı yerleşime geçer; CP `graph-data.ts` veri kuralı ölçülüp taşınır ·
R24 Bank Configuration CP formu birebir, alanlar değerleriyle DEVRE-DIŞI + tek rozet; Meridian
sayaçları ayrı alt sekme ("Sayaçlar") — yazma yolu Faz-2 kararı operatörde.

### Task 5: nav konsolidasyonu + raf adları + ana sayfa grafiği + bank config formu (UI)
**Files:** `ui/src/pano/alanlar.ts`, `ui/src/pano/sistem/nav-main.tsx` (ölçülür), `ui/src/pano/yuzeyler/hafiza/{HafizaYuzey,AnaSayfa,Yapilandirma,uctipleri,parcalar}`
- [ ] R20 · R21 · R22 · R24; kontrol+build; v288/v323/v324/v314/v373 + parite mutasyonu.

### Task 6: constellation — ÖLÇÜLDÜ (Rol-1, CP kaynağı ebad4782)
CP `constellation.tsx` (1.642 satır, canvas; kuvvet simülasyonu YOK — deterministik yerleşim: id-hash
halkası ya da `clusterKeyFn` ile küme merkezleri etrafında yarı-saydam "blob" + etiket; nokta yarıçapı
bağ sayısından, ısı rengi `sqrt(lc/maxLinkCount)`; çizim tavanı 6.000 bağ; hover kartı metin sarma
[`@chenglou/pretext` — bizde canvas fillText + elle sarma]). Veri: `client.getGraph({bank_id,
limit: GRAPH_NODE_CAP=200})` = dataplane **`GET /banks/{id}/graph`** (BELLEK grafı; params type ·
limit [default 1000] · q · tags · tags_match; cytoscape-biçimi `{data:{id,label,color,type}}` /
`{data:{source,target,weight,linkType,entityName}}`), ana sayfada fact-type kümeli; tam graf Bellekler
görünümünde. T1 yalnız `/entities/graph`ı vekilledi (varlık grafı) — bellek grafı vekili YOK.
**T6-A (api.py, TDD):** `GET /api/hindsight/bellek-graf` → upstream `/graph` (type/limit/q/tags/tags_match
süzülmüş geçiş, `_HAFIZA_UC_TAVANI` ölçülür, zarf aynen) + v375 çivileri kırmızı-önce + mutasyon.
**T6-B (UI):** `takimyildizi.tsx` canvas bileşeni (CP yerleşim kuralları), ana sayfada 200-düğüm
kümeli özet, Bellekler görünümünde tam graf sekmesi; varlık grafı (`graf.tsx`) aynı bileşene geçer
(çember yerleşimi emekli). Sıra: T5 → T6-A → T6-B (aynı dizin + eşzamanlı pytest yasağı).

### Task 7 (Rol-1): T4 tekrarı — tam suite gerekmez (yalnız UI) → etkilenen küme + dağıtım penceresi + görsel tur → DONE.
