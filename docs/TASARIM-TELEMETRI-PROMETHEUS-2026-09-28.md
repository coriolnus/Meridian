# TASARIM — Gecikme telemetrisi: Prometheus + Grafana (TSK-020 UYGULA-9)

Durum: **TASLAK — operatör onayı bekliyor** (sıra: ölçüm ✔ → bu belge → onay → kod). Yazan: Rol-1, 2026-09-28 09:0xZ.
Operatör talebi (2026-09-28, sohbet): "prometheus'u da paralelde yapamaz mısın" → Kademe C ile paralel. ROADMAP satırı: "gecikme telemetrisi —
Prometheus+Grafana (pano-SQLite alternatifi elendi); kill-kriteri yeniden çapalama AYRI KART ister."
Envanter: `…/scratchpad/tsk020-9-envanter.md` (salt-okur ajan) + A1 ölçümü (Rol-1, salt-okur, 2026-09-28 08:54Z ve 09:0xZ).
hafıza: memory `hindsight-aktif-kullanim` (CP UI yalnız 127.0.0.1 + ssh tüneli emsali), `vault-sir-yonetimi-karari`, `loadcredential-kanali`; benzer telemetri kararı yok.

---

## 1. Ölçüm

**A1 kaynak:** 4 çekirdek · RAM 24 GB (19,8 GB boş) · yük 0,05 · `/` 45G %55 (21G boş; `/var/lib/docker` burada) · `/opt/veri` 147G %82 (26G boş).
**Portlar:** DOLU 9090 (APISIX kontrol) ve 9091 (APISIX prometheus eklentisi) — Prometheus'un varsayılanı ÇAKIŞIR. BOŞ: 3000, 9092, 9093, 9095, 9100, 9101.
**Docker:** kullanımda (apisix-kapi `apache/apisix:3.18.0-debian`, apisix-etcd, hindsight-cp) — 3 imaj 1,03 GB.
**Kurulu değil:** prometheus, node_exporter, grafana.

**Bugün var olan gecikme verisi:**

| Kaynak | Ne | Bugün kim okuyor |
|---|---|---|
| APISIX `:9091` (ÖLÇÜLDÜ) | `apisix_http_latency` histogramı — 13 rota × {request, upstream, apisix}; `apisix_llm_latency` + token dağılımları | HİÇ KİMSE — `meridian/api.py::_kapi_metrik_ayristir` yalnız `apisix_http_status` sayaçlarını alır |
| Meridian `:8080/metrics` (ÖLÇÜLDÜ) | 14 gauge (up, heartbeat yaşı, halted, equity, açık pozisyon, …) — **gecikme YOK** | dış kazıyıcı yok |
| `store.io_stats` | atomik yazım p50/p95 (süreç belleği) | `/api/diagnostics` → pano IO çipi |
| `agent_telemetry` | LLM çağrı `sure_ms` (defter) | `/api/hermes` |
| **Karar döngüsü süresi (KILL#1)** | **CANLIDA ÖLÇÜLMÜYOR** — yalnız v217 sentetik testi; kart EXE-2026-003 "p95 döngü enstrümanı yok" diye itiraf ediyor | — |
| Broker/emir gecikmesi · API'nin kendi istek süresi | BULUNAMADI (APISIX `request` tipi dışarıdan kapsar) | — |

Karar döngüsü (`meridian/intraday_cycle.py::IntradayConsumer`) `/metrics`i sunan uvicorn süreciyle AYNI süreçte koşar (`api._autostart` kaydı) — süreç-içi histogram doğrudan yayınlanabilir.

## 2. Hedef ve sınır

**Amaç:** gecikmeyi ZAMAN SERİSİ olarak görmek (bugün yalnız anlık kesitler var) — özellikle (1) karar döngüsü süresi, (2) geçit/API ve LLM
gecikmesi, (3) makine baskısı (CPU/RAM/disk — `/opt/veri` %82).
**Sınır (bağlayıcı):**
- Telemetri GÖZLEMDİR, karar yüzeyi DEĞİL: hiçbir kapı/kill kararı Prometheus'tan okumaz. KILL#1'in canlı ölçümle yeniden çapalanması (EXE-2026-003,
  EDG-2026-019/078 aynı yöntemi paylaşır) AYRI KART ister — bu kalem yalnız ALETİ kurar, veri biriktirir.
- **İkinci alarm kanalı YOK:** Alertmanager kurulmaz; alarmlar tek kanalda kalır (`obs` → notify/bekçi). Grafana uyarıları kapalı.
- Her şey 127.0.0.1'e bağlanır; dışarı açılan port yok. Grafana'ya erişim ssh tüneliyle (hindsight-cp emsali).

## 3. Tasarım

**T1 — Bileşenler (Docker, pinli imaj + digest).** Prometheus `127.0.0.1:9095` · node_exporter `127.0.0.1:9100` · Grafana `127.0.0.1:3000`.
Emsal: `deploy/apisix/apisix.service` (docker `--network host`, pinli sürüm, `MemoryMax`, `Restart=on-failure`). Gerekçe: A1'de docker zaten
işletimde; resmi arm64 imajları; yükseltme = etiket değişikliği. Alternatif (native ikili + sha256, Vault deseni) §5'te.
Bellek tavanları: Prometheus 512M · Grafana 256M · node_exporter 64M.

**T2 — Veri saklama (disk tavanı zorunlu).** TSDB `/` altında (21G boş; `/opt/veri` %82 ve DISK_ESIK alarmı var) — `--storage.tsdb.retention.time=30d`
ve `--storage.tsdb.retention.size=2GB` (hangisi önce dolarsa). Kazıma aralığı 30 s. Beklenen hacim: ~3 hedef, birkaç bin seri → 30 günde yüzlerce MB.

**T3 — Kazıma hedefleri.** (a) APISIX `:9091/apisix/prometheus/metrics` — geçit ve LLM gecikmesi, SIFIR yeni kod; (b) meridian `:8080/metrics` — yerel istek
tam seti alır (mevcut gizlilik sınırı korunur, yetkisiz uzak istek yalnız canlılık görür); (c) node_exporter.

**T4 — Motor aleti (Faz B, küçük motor değişikliği).** `/metrics`'e SIFIR BAĞIMLILIKLA (mevcut elle yazılmış ifade deseni; `prometheus_client`
EKLENMEZ — tedarik zinciri kapısı `[0b]` yüzeyi büyümesin) histogramlar: karar döngüsü turu (`on_barfeed_event` sarmalı), gün döngüsü faz süreleri
(P1…P5), atomik yazım (mevcut `io_stats` verisinin histogram hali). Süreç-içi sabit kovalar; yeniden başlatmada sıfırlanır (Prometheus `rate`/
`histogram_quantile` bunu tolere eder). Çiviler: ifade biçimi (kova monotonluğu, `_count`/`_sum` tutarlılığı), sarmanın döngü davranışını
değiştirmemesi (istisna yolu dahil), gizlilik sınırı (uzak yetkisiz istek histogram ALMAZ).

**T5 — Sır.** Grafana yönetici parolası: Vault'ta yeni kayıt (`deploy/sir_envanteri.yaml` tek kaynak → `ops/vault_politika_uret.py`), Vault Agent
şablonu `/etc/meridian/grafana_admin_password` (0400), birim `LoadCredential=` → konteynere salt-okur bağlanır, Grafana `GF_SECURITY_ADMIN_PASSWORD__FILE`
ile DOSYADAN okur (argv/ortam değerine düşmez). Anonim erişim kapalı, kayıt kapalı. Parola üretimi Rol-1/operatör adımıdır (değer hiçbir çıktıya basılmaz).

**T6 — Dağıtım.** `deploy/telemetri/` altında birimler + Prometheus yapılandırması + Grafana sağlayıcı (datasource + 1 pano JSON'u) dosyaları;
`deploy/ansible/roles/meridian_a1/defaults/main.yml` tek-kaynak listelerine (`birim_kaynaklari`, `dropin_*`, `zorunlu_sir_dosyalari`) eklenir —
v451/v553/v554/v558 çivileri yeni birimleri KENDİLİĞİNDEN kapsar. Kurulum `site.yml` (A0 rolü; dagit kurmaz — memory `dagit-dropin-kurmaz-a0-rolu-kurar`);
Vault emsaliyle birimler ilk gün `etkin_birimler`e GİRMEZ: kopyala → parolayı koy → elle başlat + test-ateşle (CLAUDE.md §9) → sonra etkinleştir.

**T7 — Tek-kaynak beyanı.** Gecikme ZAMAN SERİSİNİN kanonik yüzeyi Grafana; pano ANLIK durumu göstermeye devam eder (`/api/diagnostics` IO çipi,
`/api/hermes` LLM p50/p95 — aynı kaynağın iki görünümü, kopya değil). Pano'ya "geçmiş için Grafana" bağlantısı/metni YOK (tünelle açılır) — beyan
RUNBOOK'ta. `/api/gateway` gecikme okumaz (bilinçli; Grafana okur).

## 4. Fazlar

- **Faz A — altyapı, motor kodu YOK:** T1+T2+T3(a,c)+T5+T6. APISIX gecikmesi ve makine baskısı ilk günden görünür. Motor suite'i gerektirmez (deploy/ + test).
- **Faz B — motor aleti:** T4 + T3(b). Motor değişikliği → tam suite + KILL#1 seri + dağıtım.
- **Faz C — (bu kalem DEĞİL):** ≥2 hafta veri birikince KILL#1 canlı çapası için yeni kart (EXE-2026-003 ardılı) — Rol-1 açar, operatör kararı.

## 5. Bedel yasası — ne kaybediyoruz / alternatifler

(a) Üç yeni süreç (loopback) — saldırı yüzeyi ve bakım (imaj yükseltmeleri). (b) Disk ≤2 GB (`/`) + imajlar ~0,5 GB. (c) RAM ≤~0,8 GB tavanlı.
(d) İki yüzey gecikme gösterir (T7 beyanıyla). (e) Faz B'de `/metrics` gövdesi büyür (kazıma 30 s'de bir, yerel).
**Alternatif — native ikili (Vault deseni):** docker bağımlılığı yok, bellek biraz daha az; ama sha256'lı indirici + sürüm takibi üç ikili için elle.
Öneri docker (T1), çünkü A1'de docker zaten zorunlu (APISIX).
**Elenen:** Alertmanager (ikinci alarm kanalı), `prometheus_client` (bağımlılık), Grafana'yı APISIX üzerinden dışarı açmak (kimlik yüzeyi).

## 6. Operatöre sorulacaklar

1. Tasarım onayı (T1–T7, fazlar A→B; C ayrı kart).
2. Kurulum biçimi: docker (öneri) mi, native ikili mi?
3. Grafana'ya erişim: yalnız ssh tüneli (öneri) — dışarıdan erişim istenirse ayrı karar.
