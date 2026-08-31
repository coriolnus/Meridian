# Hindsight — Derin Teknik İnceleme (A1 / Meridian bağlamı)

**Tarih:** 2026-08-31 · **Rol:** ajan (git yok, kurulum yok, salt okuma + bu dosyanın yazımı)
**Yöntem:** yalnız resmî docs (`hindsight.vectorize.io`), GitHub deposu, PyPI ve HuggingFace metadata'sı okundu.
Her iddianın yanında kaynağı var. Ölçemediğim her şey **ÖLÇÜLEMEDİ** olarak işaretli — tahmin yazılmadı.

**İncelenen sürüm:** Hindsight **0.9.2** (yayın 2026-08-25), MIT lisans, pre-1.0.
Kaynak: <https://pypi.org/pypi/hindsight-api/json> · <https://github.com/vectorize-io/hindsight/releases>

> **Uyarı — bu belgedeki sayıların sınıfı.** Docs'tan gelen sayılar kaynaklıdır. Model ağırlık
> boyutları `config.json`'dan **türetilmiş** hesaplardır (yöntem §4.4'te açık). A1'in **şu anki**
> RAM kullanımı ölçülmedi — §6.4'teki hüküm bir *karar kuralıdır*, ölçüm değil.

---

## 1. MİMARİ

### 1.1 Bileşenler (üç servis)

| Servis | Port | Rol | Kaynak |
|---|---|---|---|
| **API** | 8888 | "The core memory engine. Handles all memory operations: Retain, Recall, Reflect". Durumsuz; durum Postgres'te. Arka plan görevlerini kendi içinde işleyebilir. | [services](https://hindsight.vectorize.io/developer/services) |
| **Worker** | 8889 (metrics) | "Dedicated task processor for background operations". API ile **aynı paket ve imaj**, farklı giriş noktası. Birden çok örnek koşabilir. | [services](https://hindsight.vectorize.io/developer/services) |
| **Control Plane** | 9999 | "Web UI for managing and exploring your memory banks". Next.js. | [services](https://hindsight.vectorize.io/developer/services) · [installation](https://hindsight.vectorize.io/developer/installation) |

Ayrı worker **zorunlu değildir** — API kendi içinde işler. Ayırmak istenirse:

```
hindsight-api                              # API
hindsight-worker --worker-id worker-1      # ayrı worker
HINDSIGHT_API_WORKER_ENABLED=false hindsight-api   # API'nin iç işlemesini kapat
```
Kaynak: [services](https://hindsight.vectorize.io/developer/services)

**Görev brokerı ayrı bir kuyruk değil, Postgres'tir:** workerlar "poll for pending tasks" —
"eliminating direct process-to-process coupling" ([services](https://hindsight.vectorize.io/developer/services)).
→ **Meridian için iyi haber: Redis/RabbitMQ gibi yeni bir filo üyesi gerekmiyor.**

Üretimde `HINDSIGHT_API_WORKER_ID` sabitlenmeli: "Set a stable `HINDSIGHT_API_WORKER_ID` in
production" ([installation](https://hindsight.vectorize.io/developer/installation)).

### 1.2 Hafıza modeli (dört tip)

- **World facts** — nesnel bilgi ("water freezes at 0°C")
- **Experiences** — ajanın kendi eylemleri ("I encountered this error")
- **Observations** — kanıta bağlı, mükerrersizleştirilmiş inançlar
- **Mental models** — sentezlenmiş, kendini güncelleyen anlayış

Kaynak: [README](https://github.com/vectorize-io/hindsight) · [overview](https://hindsight.vectorize.io/)

### 1.3 API yüzeyi (tam yollar)

Kimlik doğrulama: **Bearer token**, `authorization` başlığı.
Kaynak: [api-reference](https://hindsight.vectorize.io/api-reference)

| İşlem | Metot + yol |
|---|---|
| Retain | `POST /v1/default/banks/{bank_id}/memories` <br> *(retain sayfası ayrıca `POST /v1/default/banks/{bank_id}/memories/retain` gösteriyor — **iki yol belgede tutarsız**, §8.8)* |
| Recall | `POST /v1/default/banks/{bank_id}/memories/recall` |
| Reflect | `POST /v1/default/banks/{bank_id}/reflect` |
| Dry-run çıkarım | `POST /v1/default/banks/{bank_id}/memories/dry-run-extract` |
| Bellek listesi / tekil | `GET .../memories/list` · `GET .../memories/{memory_id}` |
| Bellek düzeltme | `PATCH .../memories/{memory_id}` |
| Bank CRUD | `GET /v1/default/banks` · `PUT|PATCH|DELETE /v1/default/banks/{bank_id}` |
| Bank config | `GET|PATCH /v1/default/banks/{bank_id}/config` |
| Direktifler | `POST|GET /v1/default/banks/{bank_id}/directives` · `DELETE .../directives/{id}` |
| Operasyonlar | `GET .../operations` · `GET|DELETE .../operations/{operation_id}` |
| Dokümanlar | `GET|PATCH|DELETE .../documents[/{document_id}]` |
| Sağlık | `GET /health` · `GET /health/ready` · `GET /health/live` |
| Sürüm / metrik | `GET /version` · `GET /metrics` |

Kaynak: [api-reference](https://hindsight.vectorize.io/api-reference) · [api/retain](https://hindsight.vectorize.io/developer/api/retain) · [api/memory-banks](https://hindsight.vectorize.io/developer/api/memory-banks) · [monitoring](https://hindsight.vectorize.io/developer/monitoring)

`/v1/default/...` içindeki `default` **tenant** adıdır; çok-kiracılık `TenantExtension` ile
özelleştirilir ([extensions](https://hindsight.vectorize.io/developer/extensions)).

### 1.4 Retain istek gövdesi (tam)

```json
{
  "items": [{
    "content": "string (required)",
    "context": "string (optional)",
    "timestamp": "ISO 8601 | 'unset' | null",
    "metadata": { "key": "value" },
    "document_id": "string (optional)",
    "update_mode": "replace | append",
    "entities": [{ "text": "string", "type": "string" }],
    "resolve_entities": true,
    "tags": ["string"],
    "document_tags": ["string"],
    "observation_scopes": "combined | shared | per_tag | all_combinations | [custom]"
  }],
  "async": false,
  "operation_id": "UUID (opsiyonel, güvenli yeniden deneme için)"
}
```
Yanıt (senkron): `success`, `bank_id`, `items_count`, `async`, `usage{input_tokens, output_tokens, total_tokens}`.
Asenkron: `operation_id` döner.
Kaynak: [api/retain](https://hindsight.vectorize.io/developer/api/retain)

### 1.5 Recall istek alanları

`query` (zorunlu, **max 500 token**), `types` (`world|experience|observation`),
`prefer_observations`, `budget` (`low|mid|high`), `max_tokens` (varsayılan 4096),
`query_timestamp`, `temporal_window{start,end}`, `tags` + `tags_match`
(`any|any_strict|all|all_strict|exact`), `tag_groups`, `include{chunks,source_facts,entities}`,
`trace`, `min_scores{semantic,keyword,reranker,final}`.
Kaynak: [api/recall](https://hindsight.vectorize.io/developer/api/recall)

### 1.6 Reflect istek alanları

`query` (zorunlu), `budget`, `max_tokens` (varsayılan 4096), **`response_schema`** (JSON Schema ile
yapılandırılmış çıktı), `tags`/`tags_match`/`tag_groups`, `include{facts,tool_calls}`.
Yanıt: `text` (markdown), `structured_output`, `based_on` (kullanılan kaynaklar), `usage`, `trace`.
Kaynak: [api/reflect](https://hindsight.vectorize.io/developer/api/reflect)

### 1.7 Recall iç mimarisi (TEMPR)

Dört strateji **paralel** koşar, sonra **RRF** ile birleşir, sonra **cross-encoder** yeniden sıralar:

1. **Semantic** — anlam eşleşmesi
2. **Keyword/BM25** — "five pluggable BM25 backends" (native, vchord, pg_textsearch, pgroonga, pg_search)
3. **Graph traversal** — varlıklar arası bağ; sinyaller arasında **"Causal link weight"** var
4. **Temporal** — zaman ifadesini pencereye çevirir; adayları **recency'ye göre değil semantic
   relevance'a göre** seçer ve "spreading selection across the window's range"

Füzyon: `score(d) = Σ 1/(k+rank_i(d))`, **k=60**. Sonra top **300** aday cross-encoder'a girer.
Budget: `low`=100 aday, `mid`=300 (varsayılan), `high`=1000.
Kaynak: [retrieval](https://hindsight.vectorize.io/developer/retrieval)

**Recall LLM çağırmaz** — docs recall sırasında LLM çağrısından söz etmiyor; retrieval yalnız
embedding + BM25 + graph + cross-encoder kullanıyor ([retrieval](https://hindsight.vectorize.io/developer/retrieval)).
*(Bu bir yokluk gözlemidir; docs açıkça "recall LLM çağırmaz" cümlesini kurmuyor — §9'da açık soru.)*

### 1.8 MCP ucu

API sunucusuna **gömülü**, ayrı süreç değil; HTTP/SSE. `/mcp` altında mount edilir.
- Tek-bank modu (önerilen): `http://localhost:8888/mcp/{bank_id}/` → **27 araç**
- Çok-bank modu: `http://localhost:8888/mcp/` → **30 araç**

"By default, the endpoint is open" — açık; etkinleştirilince `Authorization` başlığı.

```
claude mcp add --transport http hindsight http://localhost:8888/mcp \
  --header "Authorization: Bearer your-secret-key" \
  --header "X-Bank-Id: my-bank"
```
Kaynak: [mcp-server](https://hindsight.vectorize.io/developer/mcp-server)

---

## 2. NATIVE (pip) KURULUM YOLU

### 2.1 Paket ağacı — kritik bulgu

`hindsight-api` **meta-pakettir**: tek bağımlılığı `hindsight-api-slim[all]==0.9.2`.
Gerçek kod `hindsight-api-slim`'de. Her ikisi de **saf Python** (`py3-none-any.whl`) — yani
Hindsight'ın kendisinde mimari-bağımlı derleme yok. ARM riski Hindsight'ta değil,
**alt bağımlılıklarındadır**.

- `hindsight_api_slim-0.9.2-py3-none-any.whl` — **1.606.165 bayt** (~1,6 MB)
- `hindsight_api_slim-0.9.2.tar.gz` — 1.405.555 bayt
- `requires_python`: **>=3.11**

Kaynak: <https://pypi.org/pypi/hindsight-api/json> · <https://pypi.org/pypi/hindsight-api-slim/json>

### 2.2 Extra'lar — ağırlığın nerede olduğu

| Extra | İçerdiği ağır paketler |
|---|---|
| `local-ml` | **torch >=2.6.0** (`sys_platform != "win32"`), **sentence-transformers >=5.0.0**, transformers >=5.5.0, huggingface-hub |
| `local-onnx` | **onnxruntime >=1.17.0**, transformers >=5.5.0, huggingface-hub — **torch YOK** |
| `local-llm` | huggingface-hub (llama.cpp yolu) |
| `embedded-db` | `pg0-embedded` |
| `oracle` | Oracle sürücüsü |
| `all` | yukarıdakilerin hepsi (torch dâhil) |

Kaynak: <https://pypi.org/pypi/hindsight-api-slim/json>

> **Bu tablo tasarımın kilit taşıdır.** `pip install hindsight-api` = `[all]` = **torch çeker**.
> `pip install "hindsight-api-slim[local-onnx]"` = torch'suz, ONNX'li, tam lokal.
> Bizim istediğimiz profil ikincisidir (§4, §6.4).

### 2.3 Docker'sız koşum resmî destekli mi — EVET

Docs "Bare Metal (pip)" yolunu tüm platformlar için **destekli** listeliyor (tek istisna Intel Mac):

| Platform | Docker | Bare Metal (pip) | Embedded DB |
|---|---|---|---|
| **Linux (x86_64, ARM64)** | ✅ | ✅ | ✅ |
| macOS (Apple Silicon/arm64) | ✅ | ✅ | ✅ |
| macOS (Intel/x86_64) | ✅ | ⚠️ slim only | ✅ |
| Windows (x86_64) | ✅ | ✅ | ✅ |

Kaynak: [installation](https://hindsight.vectorize.io/developer/installation)

**Linux ARM64 için bare-metal pip açıkça ✅.** Bu, A1 için resmî bir destek beyanıdır.

### 2.4 Koşum ve CLI

```bash
# gömülü DB ile (geliştirme)
export HINDSIGHT_API_LLM_PROVIDER=groq
export HINDSIGHT_API_LLM_API_KEY=gsk_xxxx
hindsight-api          # ~/.hindsight/data/ altında DB, port 8888

# harici Postgres ile (üretim)
export HINDSIGHT_API_DATABASE_URL=postgresql://user:pass@localhost:5432/hindsight
hindsight-api
```
CLI bayrakları: `--port 9000`, `--host 127.0.0.1`, `--workers 4`, `--log-level debug`.
Kaynak: [installation](https://hindsight.vectorize.io/developer/installation)

`--host 127.0.0.1` → **localhost-bind resmî olarak destekli** (§6.2).

### 2.5 Şema yönetimi / migration

- `HINDSIGHT_API_RUN_MIGRATIONS_ON_STARTUP` — **varsayılan `true`**: şemayı Hindsight kendi kurar.
- `HINDSIGHT_API_MIGRATION_DATABASE_URL` — migration için ayrı (doğrudan) bağlantı.
- `HINDSIGHT_API_DATABASE_SCHEMA` — varsayılan `public`.
- Elle: `hindsight-admin run-db-migration` (belirli tenant şemasını hedefleyebilir).

Kaynak: [configuration](https://hindsight.vectorize.io/developer/configuration) · [admin-cli](https://hindsight.vectorize.io/developer/admin-cli)

→ **Şemayı biz kurmuyoruz; Hindsight kuruyor.** Postgres kullanıcısına ilk açılışta DDL yetkisi gerekir.

### 2.6 Sağlık ucu

- `GET /health/live` — I/O'suz; `{"status":"alive","version":"0.4.0","uptime_seconds":812.4}`
- `GET /health/ready` ve `GET /health` — DB bağlantısı alır, `SELECT 1` koşar; 200 / 503.
  Yanıt `db_acquire_ms` ve `db_pool_waiting` içerir.

Docs'un uyarısı aynen: **"Never point a liveness probe at a dependency check. A liveness failure
means 'restart this process.'"**
Kaynak: [monitoring](https://hindsight.vectorize.io/developer/monitoring)

→ systemd/bekçi tarafında: **restart tetikleyicisi `/health/live`**, trafik/alarm göstergesi `/health/ready`.

### 2.7 Yapılandırma dosyası

Sunucu tarafı yapılandırma **env değişkeni** ile (`.env` dosyaları da destekleniyor —
[admin-cli](https://hindsight.vectorize.io/developer/admin-cli)).
İstemci/CLI tarafında `~/.hindsight/config`:
```
api_url = "<server url>"
api_key = "<api key>"
```
`chmod 600`. Kaynak: [skills/hindsight-self-hosted/SKILL.md](https://github.com/vectorize-io/hindsight/blob/main/skills/hindsight-self-hosted/SKILL.md)

---

## 3. POSTGRES

### 3.1 Sürüm gereksinimi — belgede ÇELİŞKİ var

| Sayfa | İddia |
|---|---|
| [installation](https://hindsight.vectorize.io/developer/installation) | "PostgreSQL: Version 14 or later" |
| [storage](https://hindsight.vectorize.io/developer/storage) | "PostgreSQL 15 or later" ve "pgvector 0.5.0 or later" |
| [external-pg compose](https://github.com/vectorize-io/hindsight/tree/main/docker/docker-compose/external-pg) | varsayılan imaj `pgvector/pgvector:pg18` |

**Hüküm: en yüksek beyanı taban al → PG 17 veya 18.** Compose varsayılanının 18 olması, projenin
18'i fiilen koştuğunun kanıtı. (§9 açık soru: hangi sayfa güncel?)

### 3.2 Vektör eklentisi

`HINDSIGHT_API_VECTOR_EXTENSION` ∈ `pgvector` (varsayılan) | `vchord` | `pgvectorscale` | `scann`.
İndeks: "pgvector extension with **HNSW indexes**".
Kaynak: [configuration](https://hindsight.vectorize.io/developer/configuration) · [storage](https://hindsight.vectorize.io/developer/storage)

Ayrıca per-bank indeks bakımı:
`HINDSIGHT_API_VECTOR_INDEX_MIN_ROWS` (varsayılan `0`),
`HINDSIGHT_API_VECTOR_INDEX_MAINTENANCE_MIN_INTERVAL_SECONDS` (varsayılan `900`).
Onarım: `hindsight-admin repair-bank` — "Verify and repair a bank's per-(bank, fact_type) vector
index coverage" ([admin-cli](https://hindsight.vectorize.io/developer/admin-cli)).

### 3.3 Ubuntu ARM64'te pgvector — VAR

`packages.ubuntu.com` bağlantıyı reddetti (ÖLÇÜLEMEDİ), Debian'dan doğrulandı:

| Debian sürümü | Paket | Versiyon | Mimariler |
|---|---|---|---|
| trixie | `postgresql-17-pgvector` | 0.8.0-1 | amd64, **arm64**, ppc64el, riscv64, s390x |
| forky / sid | `postgresql-18-pgvector` | 0.8.6-1 | amd64, **arm64**, loong64, ppc64el, riscv64, s390x … |

Kaynak: <https://packages.debian.org/search?keywords=pgvector>

Ayrıca **apt.postgresql.org (PGDG) arm64'ü resmen kapsıyor** — HUAWEI Cloud bir arm64 derleme
makinesi bağışladı, paketler amd64 ile aynı hızda üretiliyor.
Kaynak: <https://www.postgresql.org/about/news/arm64-on-aptpostgresqlorg-2033/>

→ **A1'de `apt install postgresql-17 postgresql-17-pgvector` PGDG deposundan çalışmalı.**
(Ubuntu'nun kendi deposunda değil PGDG'de aramak gerekir — §9 açık soru: A1'in Ubuntu sürümü ÖLÇÜLEMEDİ.)

### 3.4 Bağlanma biçimi (DSN) ve havuz

```
HINDSIGHT_API_DATABASE_URL=postgresql://user:pass@localhost:5432/hindsight
HINDSIGHT_API_READ_DATABASE_URL=...        # okuma replikası (opsiyonel)
HINDSIGHT_API_DATABASE_BACKEND=postgresql  # veya oracle
```
Havuz varsayılanları — **A1 için kritik**:
`DB_POOL_MIN_SIZE=5`, **`DB_POOL_MAX_SIZE=100`**, `DB_COMMAND_TIMEOUT=60`,
`DB_ACQUIRE_TIMEOUT=30`, `DB_STATEMENT_TIMEOUT=600`.
Kaynak: [configuration](https://hindsight.vectorize.io/developer/configuration)

> **Uyarı:** `DB_POOL_MAX_SIZE=100` varsayılanı, Postgres'in varsayılan `max_connections=100`'ünü
> tek başına tüketir. A1'de bu **düşürülmeli** (§6.4, kurulum planı adım 7).

### 3.5 Gömülü pg0 — üretimde YASAK

"By default, Hindsight uses pg0 — an embedded PostgreSQL that runs locally on your machine.
This is convenient for development but **not recommended for production**."
Kaynak: [installation](https://hindsight.vectorize.io/developer/installation)

pg0 tek binary: PostgreSQL sunucusu + pgvector önkurulu + otomatik başlatma ([storage](https://hindsight.vectorize.io/developer/storage)).
→ **A1'de pg0 kullanılmayacak. Native Postgres.** Bu, operatörün "genel sisteme katkı sağlayacak
bileşen native kurulur" tercihiyle **docs'un kendi üretim tavsiyesinin çakıştığı** noktadır — ikisi aynı yönü gösteriyor.

### 3.6 Depolama felsefesi

"Hindsight does not abstract storage behind a generic interface." — Postgres birinci sınıf
bağımlılıktır, değiştirilebilir bir sürücü değil. Vektör + tam metin + ilişkisel + JSON + graf
sorguları hepsi Postgres'in içinde.
Kaynak: [storage](https://hindsight.vectorize.io/developer/storage)

Şema tabloları, partitioning ve disk boyutlandırma rehberi **docs'ta yok** — ÖLÇÜLEMEDİ (§9).

---

## 4. EMBEDDING / RERANK — TAMAMEN LOKAL TUTMA

Bu bölüm operatörün "dışarı giden TEK şey LLM sorguları" kısıtının teknik karşılığıdır.

### 4.1 Sağlayıcı seçenekleri (tam liste)

```
HINDSIGHT_API_EMBEDDINGS_PROVIDER ∈
  local | onnx | tei | openai | openai-codex | openrouter | requesty |
  cohere | google | zeroentropy | litellm | litellm-sdk     (varsayılan: local)

HINDSIGHT_API_RERANKER_PROVIDER ∈
  local | tei | cohere | openrouter | zeroentropy | siliconflow | alibaba |
  google | flashrank | litellm | litellm-sdk | jina-mlx | rrf   (varsayılan: local)
```
Kaynak: [configuration](https://hindsight.vectorize.io/developer/configuration)

**Her ikisinin de varsayılanı zaten lokaldir** — embedding/rerank için hiçbir şey dışarı gitmez.
Bunu bozmamak için tek yapmamız gereken: `openai`/`cohere`/`openrouter` sağlayıcılarını **seçmemek**.

### 4.2 İki lokal yol: `local` (torch) vs `onnx` (torch'suz)

| | `local` | `onnx` |
|---|---|---|
| Çalışma zamanı | PyTorch + sentence-transformers | onnxruntime |
| Varsayılan model | `BAAI/bge-small-en-v1.5` (384 boyut, ~130 MB) | **`intfloat/multilingual-e5-small`** |
| Dil | **İngilizce-only** | **100+ dil** |
| Extra | `local-ml` | `local-onnx` |

`onnx` yolu için docs: "Set `HINDSIGHT_API_EMBEDDINGS_PROVIDER=onnx` for in-process CPU inference
without sidecars".
Kaynak: [models](https://hindsight.vectorize.io/developer/models) · [configuration](https://hindsight.vectorize.io/developer/configuration)

ONNX ayarları (varsayılanlarıyla):
`ONNX_MODEL_ID=intfloat/multilingual-e5-small`, `ONNX_QUERY_PREFIX=query:`,
`ONNX_PASSAGE_PREFIX=passage:`, `ONNX_POOLING=mean`, `ONNX_NORMALIZE=true`,
ayrıca `ONNX_MODEL_PATH`, `ONNX_TOKENIZER_NAME_OR_PATH`, `ONNX_DIMENSIONS`.
Kaynak: [configuration](https://hindsight.vectorize.io/developer/configuration)

> **Bu incelemenin en değerli tek bulgusu:** ONNX yolunun **varsayılan modeli zaten çok dillidir.**
> Yani Meridian'ın Türkçe arşivi için doğru yapılandırma, aynı zamanda torch'suz ve en hafif olan
> yapılandırmadır. Üç kısıt (Türkçe · ARM · düşük RAM) tek seçimle birden karşılanıyor.

### 4.3 TÜRKÇE — sessiz kalite çöküşü riski

Docs açıkça yazıyor:
- **"The default embedding model (`BAAI/bge-small-en-v1.5`) is English-only."**
- **"The default reranker (`cross-encoder/ms-marco-MiniLM-L-6-v2`) is English-only."**

Önerilen çok dilli embedding modelleri:

| Model | Dil |
|---|---|
| `BAAI/bge-m3` | 100+ — "Best overall multilingual performance" |
| `intfloat/multilingual-e5-large` | 100+ |
| `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` | 50+ |

Önerilen çok dilli reranker: `BAAI/bge-reranker-v2-m3`
(`HINDSIGHT_API_RERANKER_LOCAL_MODEL=BAAI/bge-reranker-v2-m3`).

BM25 arka uçları / çok dillilik:

| Backend | Çok dilli? |
|---|---|
| `native` | "European languages only" — `TEXT_SEARCH_EXTENSION_NATIVE_LANGUAGE` ile ayarlanır |
| `vchord` | Çok dilli (`llmlingua2` tokenizer) |
| `pg_textsearch` | İngilizce-only |
| `pgroonga` | **"Yes — out of the box"** (TokenBigram polyglot tokenizer) |
| `pg_search` | Çok dilli (ParadeDB) |

Kaynak: [multilingual](https://hindsight.vectorize.io/developer/multilingual)

**Meridian hükmü:** Türkçe mühendislik günlüğü varsayılan ayarlarla indekslenirse arama sessizce
bozulur — hata vermez, sadece kötü sonuç döner (Bedel yasasının tam vakası). Yapılandırma zorunlu.
Postgres `native` BM25 için Türkçe sözlük stok PG'de **yoktur** (§9 açık soru) — bu yüzden
`native` + `english` ile başlayıp kalibre etmek, ya da `pgroonga`ya geçmek gerekir.

> **EK 2026-08-31 akşam (operatör sayfayı işaret etti — yeniden okundu):** sayfanın `native`
> beyanı "European languages only"dir ve Türkçe'yi adıyla anmaz; §9'daki açık soru ("stok PG'de
> `turkish` ts-config var mı?") kurulum gününde TEK komutla kapanır: `psql -c '\dF turkish'`.
> VARSA `.env`'e `HINDSIGHT_API_TEXT_SEARCH_EXTENSION_NATIVE_LANGUAGE=turkish` yazılır (adım 7'ye
> koşullu satır eklendi); YOKSA pgroonga değerlendirilir (§8.9 arm64 belirsizliği hâlâ geçerli).
> Türkçe recall kartının kill-listesi bu ayar ölçülmeden koşulan kıyası zaten geçersiz sayar.

### 4.4 Model ayak izleri — türetilmiş hesap

> **Yöntem (uydurma değil, türetme):** HuggingFace `config.json` dosyalarındaki gerçek boyutlardan
> parametre sayısı hesaplandı; fp32 için ×4 bayt alındı. Docs bu sayıları vermiyor.

**`intfloat/multilingual-e5-small`** — `hidden_size=384`, `num_hidden_layers=12`,
`intermediate_size=1536`, `vocab_size=250037`, `max_position_embeddings=512`, `model_type=bert`
([config.json](https://huggingface.co/intfloat/multilingual-e5-small/raw/main/config.json))
- Gömme matrisi: 250.037 × 384 ≈ **96,0M** (parametrelerin %82'si tokenizer sözlüğünde!)
- 12 katman ≈ 21,3M · toplam ≈ **~118M parametre** → **fp32 ≈ 470 MB**, int8 ONNX ≈ ~120 MB

**`BAAI/bge-m3`** — `hidden_size=1024`, `num_hidden_layers=24`, `intermediate_size=4096`,
`vocab_size=250002`, `max_position_embeddings=8194`, `model_type=xlm-roberta`
([config.json](https://huggingface.co/BAAI/bge-m3/raw/main/config.json))
- Gömme: 250.002 × 1024 ≈ 256,0M · pozisyon: 8194 × 1024 ≈ 8,4M · 24 katman ≈ 302,3M
- Toplam ≈ **~567M parametre** → **fp32 ≈ 2,27 GB**

**`BAAI/bge-reranker-v2-m3`** — aynı XLM-R-large gövdesi → **fp32 ≈ 2,27 GB** (türetildi, config
ayrıca çekilmedi — ÖLÇÜLEMEDİ, ama mimari aynı olduğu için mertebe güvenilir)

**Docs'un verdiği ayak izleri:** bge-small ~130 MB, MiniLM cross-encoder ~85–90 MB
([models](https://hindsight.vectorize.io/developer/models) · [installation](https://hindsight.vectorize.io/developer/installation)).

**FlashRank modelleri** (ONNX, CPU):

| Model | Boyut |
|---|---|
| `ms-marco-TinyBERT-L-2-v2` | ~4 MB (varsayılan) |
| `ms-marco-MiniLM-L-12-v2` | ~34 MB (Hindsight'ın flashrank varsayılanı) |
| **`ms-marco-MultiBERT-L-12`** | **~150 MB — 100+ dil** |

Kaynak: <https://pypi.org/project/FlashRank/> · <https://github.com/PrithivirajDamodaran/FlashRank>
Çok dilli model dosyası ONNX olarak dağıtılıyor: `flashrank-MultiBERT-L12_Q.onnx` (`_Q` = kuantize).

### 4.5 `flashrank` ve `rrf` — torch'suz rerank yolu

Docs, `flashrank`i "a fast CPU-based reranking" olarak tanımlıyor ve **ONNX Runtime** kullandığını
söylüyor. Ayarları:

| Değişken | Varsayılan |
|---|---|
| `HINDSIGHT_API_RERANKER_FLASHRANK_MODEL` | `ms-marco-MiniLM-L-12-v2` |
| `HINDSIGHT_API_RERANKER_FLASHRANK_CACHE_DIR` | sistem varsayılanı |
| `HINDSIGHT_API_RERANKER_FLASHRANK_CPU_MEM_ARENA` | `false` |
| `HINDSIGHT_API_RERANKER_FLASHRANK_BATCH_SIZE` | `32` |

`CPU_MEM_ARENA`: "ONNX pre-allocates a memory arena that never shrinks" — tepe belleği tahsis
hızına karşı takas eder. **A1'de `false` kalmalı** (varsayılan zaten doğru).

`rrf` sağlayıcısı: **"no reranking, keep the fusion order rather than fail"** — "makes recall fail
open: results come back in the order the retrieval stages produced, exactly as if no reranker were
configured, instead of the request failing." Failover zincirinin sonuna konur.
Kaynak: [configuration](https://hindsight.vectorize.io/developer/configuration)

> **Rerank'ı tamamen kapatan bir `none`/`enabled=false` anahtarı YOK.** Ama `rrf` fiilen o işi
> görür ve **failover zinciri sonuna konarak** rerank arızasında recall'un çökmesini engeller.
> A1 için doğru dizilim: `RERANKER_PROVIDER=flashrank`, `RERANKER_1_PROVIDER=rrf`.

### 4.6 ARM64 çalışma zamanı doğrulaması

| Bileşen | aarch64 durumu | Kaynak |
|---|---|---|
| `hindsight-api` / `-slim` | Saf Python (`py3-none-any`) — mimariden bağımsız | [PyPI](https://pypi.org/pypi/hindsight-api-slim/json) |
| **`onnxruntime`** | **VAR** — `onnxruntime-1.29.0-cp{311,312,313,314}-manylinux_2_28_aarch64.whl`, ~20,8 MB (2026-08-17) | <https://pypi.org/project/onnxruntime/#files> |
| `torch` | Linux aarch64 CPU wheel'leri v1.8.0'dan beri resmî; 2.6'da aarch64 PyPI wheel'i **CPU-only** | <https://pytorch.org/blog/vllm-and-pytorch-work-together-to-improve-the-developer-experience-on-aarch64/> · <https://github.com/pytorch/pytorch/issues/160162> |
| `postgresql-N-pgvector` | **VAR** (arm64) — Debian trixie/forky + PGDG apt | <https://packages.debian.org/search?keywords=pgvector> · <https://www.postgresql.org/about/news/arm64-on-aptpostgresqlorg-2033/> |
| Docker imajı | **VAR** — full ~3,7 GB (ARM64), slim ~500 MB | [installation](https://hindsight.vectorize.io/developer/installation) |
| `pgroonga` arm64 apt | **ÖLÇÜLEMEDİ** — Groonga PPA'sının arm64 ürettiği doğrulanamadı | §9 |

**Sonuç: seçtiğimiz ONNX yolunda ARM'da çalışmayan bileşen YOK.** torch da çalışır ama gereksizdir.

### 4.7 Embedding'i lokalde tutmanın resmî yolu — özet reçete

```bash
HINDSIGHT_API_EMBEDDINGS_PROVIDER=onnx                      # varsayılan model zaten çok dilli
HINDSIGHT_API_RERANKER_PROVIDER=flashrank
HINDSIGHT_API_RERANKER_FLASHRANK_MODEL=ms-marco-MultiBERT-L-12   # Türkçe için
HINDSIGHT_API_RERANKER_1_PROVIDER=rrf                       # fail-open emniyet supabı
```
Hiçbir embedding/rerank çağrısı ağ üstünden gitmez. Modeller ilk açılışta HuggingFace'ten
**bir kez** indirilir ("downloaded from HuggingFace on first run" — [models](https://hindsight.vectorize.io/developer/models));
kapalı ağda `ONNX_MODEL_PATH` / `FLASHRANK_CACHE_DIR` ile önden yerleştirilebilir.

---

## 5. LLM YAPILANDIRMASI

### 5.1 Hangi işlemler LLM çağırır

| İşlem | LLM? | Not |
|---|---|---|
| **retain** | **EVET** | İçerik parçalanır, her parça olgu çıkarımı için LLM'e gider |
| **recall** | Hayır (docs LLM'den söz etmiyor) | embedding + BM25 + graf + cross-encoder |
| **reflect** | **EVET** | "agentic reasoning loop", sentezlenmiş yanıt |
| **consolidation** | **EVET** | retain sonrası arka planda, otomatik |
| **mental model rebuild** | **EVET** (arka planda) | okuma "is a database read. No retrieval, no synthesis, **no LLM call**, no waiting" |
| **knowledge page refresh** | EVET (consolidation üzerinden) | |

Kaynak: [api/retain](https://hindsight.vectorize.io/developer/api/retain) · [retrieval](https://hindsight.vectorize.io/developer/retrieval) · [api/reflect](https://hindsight.vectorize.io/developer/api/reflect) · [observations](https://hindsight.vectorize.io/developer/observations) · [mental-models](https://hindsight.vectorize.io/developer/mental-models)

### 5.2 OpenRouter'a bağlama

Docs'un OpenAI-uyumlu uç reçetesi aynen:

> "Hindsight works with any provider that exposes an OpenAI-compatible API. Set
> `HINDSIGHT_API_LLM_PROVIDER=openai` and point `HINDSIGHT_API_LLM_BASE_URL` at the endpoint that
> serves `/chat/completions` — for most providers that is the URL ending in `/v1`, **not** the
> account or resource root."

Kaynak: [models](https://hindsight.vectorize.io/developer/models)

OpenRouter ayrıca **birinci sınıf sağlayıcı olarak da listeli**: "OpenRouter (`openrouter`)",
"OpenAI-compatible gateway" ([models](https://hindsight.vectorize.io/developer/models)).

> **DİKKAT — doğrulanamayan ayrıntı:** Docs'ta **OpenRouter'a özel işlenmiş bir örnek yok**;
> base URL dizesi belgede geçmiyor. İlk okumada bir özetleyici bana `https://openrouter.io/api/v1`
> verdi; ikinci, hedefli okumada docs'ta böyle bir dize **bulunmadığı** doğrulandı. Bu yüzden
> base URL'i bu rapora **yazmıyorum** — kurulumda OpenRouter'ın kendi dokümanından alınacak (§9).
> (Uydurma yasağı: ölçemediğim dizeyi yazmam.)

İki seçenek var, ikisi de meşru:
- `PROVIDER=openrouter` + `API_KEY` (yerleşik sağlayıcı yolu)
- `PROVIDER=openai` + `BASE_URL=<openrouter /v1 ucu>` + `API_KEY` (genel OpenAI-uyumlu yol)

### 5.3 İşlem başına model seçimi — VAR

Her işlem (`retain`, `reflect`, `consolidation`) için ayrı sağlayıcı/model/anahtar/base_url:

```bash
HINDSIGHT_API_RETAIN_LLM_PROVIDER=...      HINDSIGHT_API_RETAIN_LLM_MODEL=...
HINDSIGHT_API_REFLECT_LLM_PROVIDER=...     HINDSIGHT_API_REFLECT_LLM_MODEL=...
HINDSIGHT_API_CONSOLIDATION_LLM_MODEL=...
# her biri için ayrıca: _LLM_API_KEY, _LLM_BASE_URL, _LLM_MAX_CONCURRENT, _LLM_TIMEOUT
```
Sıcaklık varsayılanları: `RETAIN=0.1`, `REFLECT=0.9`, `CONSOLIDATION=0.0`.
Kaynak: [configuration](https://hindsight.vectorize.io/developer/configuration) · [models](https://hindsight.vectorize.io/developer/models)

→ **Meridian için doğrudan kullanışlı:** ucuz/hızlı model retain+consolidation'a (hacim burada),
güçlü model reflect'e. Maliyet kontrolü tek env değişkeni.

Çoklu LLM stratejisi de var: `HINDSIGHT_API_LLM_<n>_PROVIDER/MODEL/API_KEY` +
`HINDSIGHT_API_LLM_STRATEGY` (`failover` | `round-robin`).

### 5.4 Model seçim kısıtı — 65.000 çıktı tokenı

Docs: retain için modeller **"at least 65,000 output tokens"** taşımalı; düşünen modellerde
akıl yürütme tokenları aynı tavandan yenir. `HINDSIGHT_API_REFLECT_MAX_COMPLETION_TOKENS` sert
maliyet tavanı koyar.
Kaynak: [models](https://hindsight.vectorize.io/developer/models)

> **OpenRouter model seçiminde bu bir eleme kriteridir** — küçük çıktı tavanlı ucuz modeller
> retain'i güvenilmez kılar.

### 5.5 Diğer LLM anahtarları

`LLM_MAX_CONCURRENT=32` (varsayılan — **A1'de düşürülmeli**), `LLM_TIMEOUT=120`,
`LLM_MAX_RETRIES=3`, `LLM_STRICT_SCHEMA=false` (+ retain/reflect/consolidation başına),
`LLM_PROMPT_CACHE_ENABLED=true`, `LLM_EXTRA_BODY` (JSON — sağlayıcıya özel parametreler),
`LLM_DEFAULT_HEADERS` (proxy/tracing başlıkları — OpenRouter'ın `HTTP-Referer`/`X-Title`
başlıkları buradan verilir), `LLM_REASONING_EFFORT`, `LLM_SEND_BANK_AS_USER=false`.
Ayrıca yerleşik **llama.cpp**: `LLAMACPP_MODEL_PATH`, `LLAMACPP_CONTEXT_SIZE=8192` (tam yerel LLM
istenirse — bizim senaryoda gerekmiyor).
Kaynak: [configuration](https://hindsight.vectorize.io/developer/configuration)

### 5.6 Retain başına token maliyeti

Docs **sayı vermiyor** — "Token consumption depends on content size and extraction complexity."
Ama senkron retain yanıtı **gerçek `usage`** döndürür → maliyet ölçülebilir, tahmin gerekmez.
Asenkron retain, sağlayıcı Batch API'lerini kullanabilir: **"~50%"** tasarruf, 24 saate kadar
işleme penceresi (OpenAI, Groq, Gemini).
Kaynak: [api/retain](https://hindsight.vectorize.io/developer/api/retain)

> OpenRouter'ın Batch API desteği **ÖLÇÜLEMEDİ** (§9) — %50 tasarruf bizim yolumuzda geçerli olmayabilir.

---

## 6. OPERASYON

### 6.1 Yedekleme

`hindsight-admin` (aynı `pip install hindsight-api` ile gelir, doğrudan Postgres'e bağlanır,
yalnız PostgreSQL):

| Komut | İş |
|---|---|
| `backup` | "Create a backup of all Hindsight data to a zip file" |
| `restore` | Arşivden geri yükleme (veri kaybı uyarısıyla) |
| `export-bank` / `import-bank` | Bank bazında taşınabilir ZIP; import **yeniden gömme** yapar |
| `run-db-migration` | Şema göçü |
| `repair-bank` | Vektör indeks kapsamı onarımı |
| `worker-status` | İşlenen görevler, worker bazında |
| `decommission-worker(s)` | Görevleri `processing`'den `pending`'e geri bırak |

Kaynak: [admin-cli](https://hindsight.vectorize.io/developer/admin-cli)

Ayrıca HTTP üzerinden bank export/import: `POST .../document-transfer/export` (asenkron,
`operation_id` döner) ve `POST .../document-transfer?on_conflict=replace` (multipart).
**"Both operations preserve facts without re-extraction"** — yani LLM maliyeti olmadan taşınır.
Kaynak: [api/memory-banks](https://hindsight.vectorize.io/developer/api/memory-banks)

> **Meridian notu:** Postgres native olduğu için mevcut `litestream`/pg yedek disiplinimiz
> Hindsight verisini de kapsayabilir — ayrı yedek hattı kurmaya gerek yok. `hindsight-admin backup`
> ikinci, mantıksal katman olarak eklenir.

### 6.2 Auth ve bind

- API: **Bearer token**, `authorization` başlığı ([api-reference](https://hindsight.vectorize.io/api-reference)).
- MCP ucu **varsayılan olarak AÇIKTIR**: "By default, the endpoint is open" ([mcp-server](https://hindsight.vectorize.io/developer/mcp-server)).
- CLI/istemci tarafı: `~/.hindsight/config` (`api_url`, `api_key`, `chmod 600`).
- API anahtarları bank bazında kısıtlanabilir (Cloud dokümanı; self-hosted karşılığı ÖLÇÜLEMEDİ — §9).
- Bind: `hindsight-api --host 127.0.0.1` ([installation](https://hindsight.vectorize.io/developer/installation)).
- İleri auth (JWT/OAuth/çok-kiracı): `TenantExtension` ([extensions](https://hindsight.vectorize.io/developer/extensions)).
- Control Plane erişim anahtarı henüz **açık issue**: [#1148](https://github.com/vectorize-io/hindsight/issues/1148).

> **Hüküm: A1'de 8888/9999 kesinlikle `127.0.0.1`'e bağlanmalı.** MCP'nin varsayılan açıklığı ve
> CP'nin auth'unun henüz issue aşamasında olması, dışa açık bind'ı kabul edilemez kılar.

### 6.3 Gözlemlenebilirlik

- **Prometheus:** `GET /metrics` (API 8888, worker 8889). Metrikler: işlem süresi/sayısı, retain
  doküman sayısı, LLM çağrısı ve token, HTTP istekleri, DB havuz istatistikleri.
- **OpenTelemetry:** `HINDSIGHT_API_OTEL_TRACES_ENABLED=true`,
  `HINDSIGHT_API_OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318`; GenAI semantic conventions
  v1.37+, W3C trace context.
- **Log:** `--log-level debug`.

Kaynak: [monitoring](https://hindsight.vectorize.io/developer/monitoring) · [installation](https://hindsight.vectorize.io/developer/installation)

→ Meridian'ın mevcut bekçi/alarm hattı `/metrics`i doğrudan tüketebilir; **Yasa 6 (okuyucusuz
yazım yok)** açısından: metrik ucu üretiliyorsa okuyanı da bağlanmalı, yoksa açmayalım.

### 6.4 KAYNAK AYAK İZİ — iki senaryolu RAM hükmü

**Docs'un resmî tablosu** ([installation](https://hindsight.vectorize.io/developer/installation)):

| Bileşen | Asgari RAM | Önerilen | Not |
|---|---|---|---|
| API — full imaj | 1,5 GB | 2 GB | "Loads local BGE embedder (~130 MB) and MiniLM cross-encoder (~90 MB)" |
| API — slim imaj | 512 MB | 1 GB | Gömülü model yok |
| Control Plane | 128 MB | 256 MB | "Next.js process, lightweight" |
| Worker (ayrılırsa) | API ile aynı | API ile aynı | "Workers load the same models as the API" |
| PostgreSQL | 512 MB | 1 GB+ | "Scales with the number of memories and indexes" |

CPU: **"2 vCPUs on CPU-only is fine for development and basic workloads."** Üretimde lokal rerank
GPU'dan faydalanır (A1'de GPU yok — flashrank/ONNX seçimi bu yüzden de doğru).

**ÇELİŞKİ:** FAQ farklı bir sayı veriyor — "Python 3.11+, **4GB RAM minimum (8GB recommended for
production)**, LLM API key … or local LLM setup" ([faq](https://hindsight.vectorize.io/faq)).
Bu bileşen-başı değil **yığın-toplamı** bir beyandır; ikisi çelişmiyor olabilir ama docs bunu
belirtmiyor (§9). **Tutumlu davranıp FAQ'ın 8 GB "önerilen" rakamını üst sınır olarak alıyorum.**

#### Senaryo A — ONNX/çok dilli yığın (önerdiğim)

| Kalem | Tahmini RSS | Dayanak |
|---|---|---|
| Hindsight API süreci (Python+FastAPI+asyncpg) | ~0,3–0,4 GB | docs slim asgarisi 512 MB |
| ONNX embedder `multilingual-e5-small` fp32 + arena | ~0,6–0,8 GB | 470 MB ağırlık (§4.4) + oturum |
| flashrank `MultiBERT-L12_Q` (kuantize ONNX) | ~0,2–0,3 GB | 150 MB ağırlık (§4.4) |
| **Hindsight API toplam** | **~1,2–1,8 GB** | docs full-imaj bandıyla (1,5–2 GB) uyumlu |
| Postgres (native, mütevazı bank) | ~0,5–1,0 GB | docs tablosu |
| Control Plane (opsiyonel) | ~0,15–0,25 GB | docs tablosu |
| **A senaryosu toplam ek yük** | **~2,0–3,0 GB** (CP'siz ~1,8–2,8 GB) | |

#### Senaryo B — torch + `bge-m3` + `bge-reranker-v2-m3`

| Kalem | Tahmini RSS |
|---|---|
| `bge-m3` fp32 | ~2,3 GB (§4.4 türetme) |
| `bge-reranker-v2-m3` fp32 | ~2,3 GB (§4.4 türetme) |
| torch çalışma zamanı + Python | ~0,6–0,9 GB |
| **Hindsight API toplam** | **~5,2–5,5 GB** |
| Postgres + CP | ~0,7–1,25 GB |
| **B senaryosu toplam ek yük** | **~6,0–6,8 GB** |

#### Hüküm: 12 GB'de başla — 24'e çıkma

**A1'in ŞU ANKİ kullanımı ÖLÇÜLEMEDİ** (ajanım; A1'e ssh atmadım). Bu yüzden hüküm bir *karar
kuralı* olarak yazılıyor, sayı olarak değil:

> **Karar kuralı:** A1'de `free -g` ile ölçülen **available** bellek ≥ **5 GB** ise Senaryo A
> 12 GB'de rahat sığar (2–3 GB ek yük + ~2 GB emniyet payı). 3–5 GB arasıysa Control Plane'i
> kapatarak ve `DB_POOL_MAX_SIZE`i düşürerek sığar ama pay dardır. < 3 GB ise 24 GB'ye çıkılır.

**Önerim: 12 GB'de başla.** Gerekçe üç adımlı:
1. Senaryo A'nın ek yükü **~2–3 GB** — mevcut Meridian yığını (worker + learn + redis + litestream
   + üç bot) 12 GB'lik bir makinede tipik olarak bu payı bırakır.
2. **24 GB'yi tek başına gerekçelendiren bileşen Senaryo B'nin `bge-m3` + `bge-reranker-v2-m3`
   çiftidir: ~4,6 GB sadece model ağırlığı** (§4.4). Bu iki modeli seçmediğimiz sürece 24 GB'nin
   teknik gerekçesi yoktur.
3. Yükseltme **geri dönüşü olan** bir karardır ve ölçüm ucuzdur: `/metrics` + `free` ile bir hafta
   izlenip karar verilebilir. Ölçmeden yükseltmek, bedeli ölçmeden kazanç almaktır.

**24'e çıkma tetikleyicisi (önden yazılı, sonradan gevşetilmez):** (a) `multilingual-e5-small`
Türkçe recall kalitesi ön-kayıtlı bir ölçüm kartının eşiğini geçemezse ve `bge-m3`'e geçiş
gerekirse; **veya** (b) A1'de OOM-killer Hindsight'ı ya da Meridian worker'ını bir kez bile
öldürürse.

**A1 tarafında koşulacak ölçüm (Rol-1):**
```bash
ssh -i ~/.ssh/oci-a1.key ubuntu@130.61.126.87 'free -g; nproc; lsb_release -ds; python3 -V'
```

> **REVİZYON 2026-08-31 (aynı gün, hüküm yazıldıktan sonra):** Operatör A1'i **24 GB'ye çıkardı**
> (reboot 13:24, kanıt turu yeşil — yükseltme bu rapordan bağımsız operatör kararıydı). Yukarıdaki
> karar kuralı ve "12'de başla" önerisi TARİHÎ KAYIT olarak duruyor; fiili durumun sonuçları:
> (1) Senaryo B (`bge-m3` + `bge-reranker-v2-m3`) artık **gün-1'den teknik olarak masada** — ama
> sıra değişmez: önce Senaryo A, Türkçe recall kartı eşiği geçemezse B'ye geçilir (bedel artık RAM
> değil yalnız kurulum+yeniden-gömme). (2) systemd `MemoryMax` çiti 3G→**8G** (aşağıda, adım 8) —
> Senaryo B tavanının (~5,5 GB API) üstünde, Meridian yığınına ≥16 GB bırakır. (3) CPU türevli
> sınırlar DEĞİŞMEZ: `LLM_MAX_CONCURRENT=6` ve `DB_POOL_MAX_SIZE=10` çekirdek/bağlantı kısıtıdır,
> RAM'den bağımsız (§6.4 CPU bölümü).

#### CPU (4 çekirdek) ayarı

Varsayılan `HINDSIGHT_API_LLM_MAX_CONCURRENT=32` 4 çekirdek için **fazla**; retain LLM-bağımlı
olduğu için ağ eşzamanlılığıdır ama her yanıtın ardından CPU'da embedding/rerank işi doğar.
`DB_POOL_MAX_SIZE=100` de Postgres'in varsayılan `max_connections=100`'ünü tek başına tüketir.
İkisi de düşürülmeli (kurulum planı adım 7).

Docs'un gecikme rakamları ([performance](https://hindsight.vectorize.io/developer/performance)):
recall **100–600 ms** (CPU'da darboğaz yeniden sıralayıcı), reflect **800–3000 ms**,
retain/batch **500–2000 ms**, vektör arama **10–50 ms** (100K+ olguda),
uçtan uca reflect **600–2600 ms**. Bunlar A1 sınıfı bir makinede değil, belirtilmemiş bir referans
donanımda ölçülmüş — **A1'de doğrulanmalı** (§9).

### 6.5 Çok-bank yönetimi

Banklar tam izole: **"Banks are completely isolated from each other with no data leakage"**
([faq](https://hindsight.vectorize.io/faq)). İki desen: kullanıcı/konu başına ayrı bank, ya da tek
bank + tag'ler. Tag eşleşme modları (`any_strict`, `all_strict`, `exact` …) çok-kiracı izolasyonu
için kullanılıyor ([best-practices](https://hindsight.vectorize.io/best-practices)).

Bank config alanları ([api/memory-banks](https://hindsight.vectorize.io/developer/api/memory-banks)):

| Alan | İş |
|---|---|
| `retain_mission` | "Steers fact extraction focus without replacing logic" |
| `retain_extraction_mode` | `concise` (varsayılan) / `verbose` / `custom` |
| `reflect_mission` | Reflect için birinci-şahıs zemin |
| `disposition_skepticism` | 1–5 (1 güvenen … 5 şüpheci) |
| `disposition_literalism` | 1–5 |
| `disposition_empathy` | 1–5 |
| `entity_labels` | Varlık sınıflandırması için kontrollü sözlük |
| `recall_budget_function` | `fixed` / `adaptive` |
| `memory_defense` | Bank başına güvenlik politikası |

**Direktifler** ayrı bir kaynak: reflect sırasında uygulanan **sert kurallar** —
"strict enforcement" (disposition ise "soft influence on reasoning").

---

## 7. MERİDİAN AMAÇLARI — ÖZELLİK EŞLEMESİ

| Bizim amacımız | Karşılık gelen özellik | Kaynak |
|---|---|---|
| **Arşiv araması** | `recall` + TEMPR dört strateji (semantic/BM25/graph/temporal); `document_id` ile doküman kimliği; `tags`/`tag_groups` ile daraltma; `include.source_facts` + `trace` ile kanıt zinciri | [retrieval](https://hindsight.vectorize.io/developer/retrieval) · [api/recall](https://hindsight.vectorize.io/developer/api/recall) |
| **Ajan-B sohbet bağlamı** | `retain` (`context` alanı) + `reflect` (`reflect_mission`, direktifler, disposition) + **MCP ucu** ile Claude Code'a doğrudan bağlanma | [mcp-server](https://hindsight.vectorize.io/developer/mcp-server) · [api/memory-banks](https://hindsight.vectorize.io/developer/api/memory-banks) |
| **Nedensel sorgu** | Graph traversal sinyalleri arasında **"Causal link weight"**; docs'un örneği birebir: "Why did Alice leave?" | [retrieval](https://hindsight.vectorize.io/developer/retrieval) |
| **Zamansal sorgu** | Temporal strateji + `query_timestamp` + `temporal_window{start,end}`; retain'de çift zaman ekseni: "when it happened" / "when you learned it" | [retrieval](https://hindsight.vectorize.io/developer/retrieval) · [retain](https://hindsight.vectorize.io/developer/retain) |
| **Mükerrer-önleme** | Üç katman: (1) `document_id` upsert — "old content and memories are deleted before reprocessing"; (2) `operation_id` ile güvenli yeniden deneme; (3) observation **near-duplicate reconciliation** (varsayılan açık) | [api/retain](https://hindsight.vectorize.io/developer/api/retain) · [observations](https://hindsight.vectorize.io/developer/observations) |

### 7.1 Tasarımda öngörmediğimiz DEĞERLİ yetenekler — İŞARETLİ

**① Knowledge Pages + `hindsight fs` — en büyük sürpriz.**
Bank kendisi hakkında "living documents" yazıyor: her sayfa tek bir soruyu cevaplıyor ve
"rewrites itself as the bank learns more". Kritik cümle: **"projected onto disk as ordinary
markdown files"** ve CLI `hindsight fs` "mirrors banks to local markdown folders".
Sayfalar ham sohbetten değil **observation'lardan** üretiliyor ve "never reads other pages, so
pages can't cite each other into a feedback loop".
→ *Meridian karşılığı:* `MERIDIAN_ENGINEERING_LOG.md` sınıfı belgelerin **kendini güncelleyen**
bir versiyonu. Ama dikkat: bu bir **türetilmiş** artefakttır — §4 Tek-kaynak yasası gereği SSoT
olarak kullanılamaz, yalnız türetme olarak. ([knowledge-pages](https://hindsight.vectorize.io/developer/knowledge-pages))

**② Mental Models — LLM'siz sabit cevap.**
"a standing answer to a question about a bank"; okuma **"is a database read. No retrieval, no
synthesis, no LLM call, no waiting."** Yeniden inşa yalnız kapsamına giren yeni bellek geldiğinde
tetikleniyor.
→ *Meridian karşılığı:* "şu an X konusundaki duruşumuz ne?" gibi tekrar tekrar sorulan sorular
sıfır LLM maliyetiyle cevaplanır. ([mental-models](https://hindsight.vectorize.io/developer/mental-models))

**③ Direktifler — yasaların makineye taşınması.**
Reflect sırasında uygulanan sert kurallar, `POST .../directives` ile yönetiliyor.
→ *Meridian karşılığı:* CLAUDE.md §4 Yasaları bank direktifi olarak kodlanabilir; reflect çıktısı
yasaya aykırı öneri üretemez. **Ama** bu zorlanma katmanı `codelaw` kadar sert değildir — CLAUDE.md'nin
"zorlanma katmanı dürüstçe etiketlidir" kuralı gereği **"LLM-zorlamalı"** diye etiketlenmeli.

**④ `dry-run-extract` ucu.**
`POST .../memories/dry-run-extract` — çıkarımı bankı kirletmeden dener.
→ *Meridian karşılığı:* prompt/model ayarını **ön-kayıtlı kart** disipliniyle, üretim bankına
yazmadan kalibre etme yolu. Ölçüm kartı yazarken bu uç kill-list'i ucuzlatır. ([api-reference](https://hindsight.vectorize.io/api-reference))

**⑤ `reflect` + `response_schema`.**
JSON Schema verilince `structured_output` dönüyor → reflect **program tarafından** tüketilebilir,
metin ayrıştırmaya gerek yok. ([api/reflect](https://hindsight.vectorize.io/developer/api/reflect))

**⑥ Observation'ın çelişki davranışı — kayıt disiplinimizle aynı felsefe.**
Çelişki geldiğinde üzerine yazmıyor, **"reconciles the contradiction by capturing the evolution"**;
sonuç "captures the full journey". Her observation destekleyen belleklere **alıntılarla** referans
veriyor, "proof count" tutuyor.
→ Bu, Meridian'ın "künyeli kural + vaka arşivi" disiplininin motor içindeki karşılığıdır.
([observations](https://hindsight.vectorize.io/developer/observations))

**⑦ Bank export/import — LLM maliyetsiz taşıma.**
"Both operations preserve facts without re-extraction" → bank'ı yeniden çıkarım maliyeti ödemeden
taşıyabiliriz. Ama `import-bank` (admin CLI yolu) **yeniden gömme** yapar — embedding modeli
değiştirirsek maliyet burada. ([api/memory-banks](https://hindsight.vectorize.io/developer/api/memory-banks) · [admin-cli](https://hindsight.vectorize.io/developer/admin-cli))

**⑧ Memory Defense — 45 desenli sır/PII temizliği.**
Dokuz kategori: AI/LLM sağlayıcı anahtarları, bulut kimlik bilgileri, kaynak kontrol tokenları,
ödeme sağlayıcı sırları, DB bağlantı dizeleri, özel anahtarlar/JWT, PII biçimleri…
Her eşleşme `[REDACTED:type]` ile değiştiriliyor. **Bank başına opt-in, varsayılan KAPALI.**
→ Bu bir yetenek **ve** bir risk (§8.5). ([memory-defense](https://hindsight.vectorize.io/developer/memory-defense))

---

## 8. RİSKLER

### 8.1 ⚠️ YÜKSEK — Türkçe içerikte sessiz kalite çöküşü
Varsayılan embedder **ve** varsayılan reranker İngilizce-only (docs'un kendi ifadesi, §4.3).
Meridian arşivi Türkçe. Yanlış yapılandırmada sistem **hata vermez**, sadece kötü sonuç döner.
Bu tam olarak CLAUDE.md'nin "körlüğün belirtisi hiçbir şeydir" vakasıdır.
**Azaltma:** `EMBEDDINGS_PROVIDER=onnx` (varsayılan modeli çok dilli) + flashrank `MultiBERT-L-12`.
**Ve:** kurulumdan sonra Türkçe recall kalitesi **ön-kayıtlı bir kartla** ölçülmeli — yoksa
"çalışıyor" diyemeyiz.

### 8.2 ⚠️ YÜKSEK — pre-1.0, haftalık sürüm, belgelenmiş kırıcı değişiklik
v0.8.5 (22 Tem) → v0.9.2 (25 Ağu) arası **beş sürüm**; 1–2 haftada bir. Sürüm notlarında kırıcı
değişiklikler açık: v0.9.0 "deprecate bank name as narrator; steer speaker via context",
v0.8.6 "require explicit semantic link thresholds".
22.000+ yıldız, 2.730 commit, 68 açık issue, 28 açık PR.
Kaynak: <https://github.com/vectorize-io/hindsight/releases> · [README](https://github.com/vectorize-io/hindsight)
**Azaltma:** sürümü **çivile** (`hindsight-api-slim==0.9.2`), `latest` etiketi kullanma; yükseltmeyi
ayrı bir tur işi yap, `hindsight-admin backup` sonrası.

### 8.3 🟡 ORTA — `hindsight-api` meta-paketi torch çeker
`pip install hindsight-api` = `[all]` = torch + sentence-transformers. A1'de bu ~2–3 GB disk ve
gereksiz RAM demektir. Doğru hedef **`hindsight-api-slim[local-onnx]`**.
**Azaltma:** kurulum komutunu §10'daki gibi yaz; kurulumdan sonra `pip list | grep -i torch` boş
olmalı — bu bir **çividir**, kontrol edilmeli.

### 8.4 🟡 ORTA — rerank kapatılamıyor, ve varsayılanı torch'lu
`RERANKER_PROVIDER` için `none`/`off` yok; varsayılan `local` (torch). Yanlış bırakılırsa
`local-onnx` kurulumunda **çalışma zamanı hatası** verir (torch yok).
**Azaltma:** `flashrank` + failover zincirinin sonunda `rrf` (fail-open). Bu ikisi birlikte hem
torch'suz hem arızaya dayanıklı.

### 8.5 🟡 ORTA — Memory Defense varsayılan KAPALI
Meridian log/artefakt içeriğini retain edeceksek `.env`, API anahtarı, DSN sızma yüzeyi gerçektir.
Üstelik **"Existing memories are not retroactively scanned when you add or change a policy"** —
politikayı sonradan açmak eskiyi temizlemez.
**Azaltma:** bank'ı **ilk günden** `memory_defense` politikasıyla oluştur. Sonradan açmak geç kalır.

### 8.6 🟡 ORTA — MCP ucu varsayılan açık + CP auth'u issue aşamasında
"By default, the endpoint is open" ([mcp-server](https://hindsight.vectorize.io/developer/mcp-server));
CP erişim anahtarı [#1148](https://github.com/vectorize-io/hindsight/issues/1148) hâlâ açık issue.
**Azaltma:** 8888 ve 9999 **yalnız `127.0.0.1`**; dışarıdan erişim gerekirse ssh tüneli.
Bunu systemd biriminde `--host 127.0.0.1` ile çivile, güvenlik grubuna güvenme.

### 8.7 🟢 DÜŞÜK — Lisans ve telemetri: TEMİZ
**MIT**, self-hosted'da kısıt yok. Vectorize'ın kendi beyanı aynen:
**"Hindsight is MIT licensed with no usage limits, no telemetry, and no restrictions. Run it in
production on your own infrastructure at no cost."**
Kaynak: <https://vectorize.io/pricing> · [README](https://github.com/vectorize-io/hindsight) (LICENSE: MIT)
Ayrıca [configuration](https://hindsight.vectorize.io/developer/configuration) sayfasında telemetri
env değişkeni **yok** ve [monitoring](https://hindsight.vectorize.io/developer/monitoring) sayfası
yalnız *bizim* topladığımız metrikleri (Prometheus/OTel) anlatıyor — dışa veri gönderimi geçmiyor.
**Ancak:** bu bir *beyan* + *yokluk gözlemi*dir; kaynak kodda telefon-eve araması yapılmadı
(ÖLÇÜLEMEDİ — §9). Kurulumdan sonra `/metrics` dışı giden bağlantı bir kez izlenmeli.
**Not:** modeller ilk açılışta **HuggingFace'ten indirilir** — bu bir telemetri değil ama
"dışarı giden tek şey LLM" kısıtının teknik istisnasıdır (bir kerelik, `HF_ENDPOINT` ile
yönlendirilebilir, önden yerleştirilebilir).

### 8.8 🟢 DÜŞÜK — Docs iç tutarsızlıkları
Üç tane ölçüldü: (a) PG **14+** vs **15+** (§3.1); (b) RAM **1,5–2 GB** (bileşen tablosu) vs
**4 GB min / 8 GB önerilen** (FAQ) (§6.4); (c) retain yolu `.../memories` vs `.../memories/retain`
(§1.3). Hiçbiri engelleyici değil ama **kurulumda ölçülerek çözülmeli**, belgeye güvenilerek değil.

### 8.9 🟢 DÜŞÜK — `pgroonga` ARM64 apt durumu doğrulanamadı
Türkçe BM25 için `pgroonga`ya geçmek istersek arm64 paketi ÖLÇÜLEMEDİ (§9).
**Azaltma:** `native` + PG'nin kendi sözlüğüyle başla (pgroonga'ya bağımlı olma); gerekirse
`vchord`/`pg_search` alternatiflerini değerlendir.

### 8.10 🟢 DÜŞÜK — toplu arşiv yükleme yolu ince
Docs'ta **toplu arşiv API'si yok**; CLI'da `hindsight memory retain-files my-bank docs/` var ama
desteklenen biçimler (PDF/Markdown) belirtilmemiş ([api/documents](https://hindsight.vectorize.io/developer/api/documents)).
İlk geri-dolumda `docs/` (~100+ dosya) yüklenirken bu yol ölçülmeli; gerekirse `items[]` toplu
`async: true` retain ile kendi betiğimiz yazılır.

---

## 9. AÇIK SORULAR (docs'un cevaplamadıkları)

1. **OpenRouter base URL dizesi** — docs'ta OpenRouter'a işlenmiş örnek yok; `/v1` ile biten uç
   OpenRouter'ın kendi dokümanından alınacak. (§5.2)
2. **PG asgari sürümü gerçekte kaç?** 14 mü 15 mi — iki sayfa çelişiyor; compose 18 kullanıyor. (§3.1)
3. **RAM asgarisi gerçekte kaç?** Bileşen tablosu (1,5–2 GB) ile FAQ (4 GB min / 8 GB önerilen)
   aynı şeyi mi ölçüyor? (§6.4)
4. **Retain'in kanonik HTTP yolu** — `.../memories` mi `.../memories/retain` mi? (§1.3)
5. **Recall gerçekten hiç LLM çağırmıyor mu?** Docs bunu açıkça *söylemiyor*, sadece *anmıyor*.
   Maliyet modelimiz buna dayanıyor — `/metrics`teki LLM çağrı sayacıyla doğrulanmalı. (§1.7, §5.1)
6. **OpenRouter Batch API destekliyor mu?** Asenkron retain'in "~%50" tasarrufu bizde geçerli mi? (§5.6)
7. **`hindsight-api-slim[local-onnx]` flashrank'i içeriyor mu**, yoksa `pip install flashrank`
   ayrı mı gerekiyor? PyPI extra listesinde flashrank görünmedi. (§4.5, §10 adım 5)
8. **`pgroonga` arm64 apt paketi var mı?** (§8.9)
9. **Postgres şema/tablo yapısı, partitioning, disk boyutlandırma** — docs'ta yok. Bank başına
   1 GB olgu ne kadar disk tutar, bilinmiyor. (§3.6)
10. **A1'in Ubuntu sürümü ve Python sürümü** — `>=3.11` şartını karşılıyor mu? Ubuntu 22.04
    stok Python 3.10'dur; 24.04 3.12'dir. ÖLÇÜLEMEDİ. (§6.4'teki ssh komutu bunu çözer)
11. **A1'in şu anki boş RAM'i** — 12/24 GB hükmünün tek eksik girdisi. (§6.4)
12. **Self-hosted'da bank-kısıtlı API anahtarı var mı?** Bu özellik Cloud dokümanında görüldü;
    self-hosted karşılığı doğrulanmadı. (§6.2)
13. **Kaynak kodda telefon-eve var mı?** Beyan temiz ama kod okunmadı. (§8.7)
14. **`performance` sayfasındaki gecikmeler hangi donanımda ölçüldü?** A1 (4 çekirdek ARM, GPU yok)
    için geçerli değil; yeniden ölçülmeli. (§6.4)

---

## 10. A1 İÇİN SOMUT KURULUM PLANI TASLAĞI

> Bu bir **taslaktır** — hiçbir komut koşulmadı. Dağıtım kararı ve icrası **Rol-1**'indir.

### 10.0 Önce: hangi yol? — üç seçeneğin kıyası

**(a) Resmî best-practice yolu.** Docs dört yolu şöyle etiketliyor
([installation](https://hindsight.vectorize.io/developer/installation)):

| Yol | Docs'un ifadesi |
|---|---|
| Docker | "Best for: Quick start, development, small deployments" |
| Kubernetes/Helm | **"Best for: Production deployments, auto-scaling, cloud environments"** |
| Bare Metal (pip) | "Best for: Running Hindsight as a standalone service on a host machine" |
| Embedded Python | "Best for: Using Hindsight programmatically … without running a separate server process" |

README ayrıca Docker'ı "**(Recommended)**" diye işaretliyor — ama bağlamı *en hızlı başlangıç*tır
([README](https://github.com/vectorize-io/hindsight)).
**Dürüst okuma: docs'un "üretim" etiketi Kubernetes'e gidiyor** — A1'de tek düğüm için anlamsız.
Tek-host için docs iki yolu da destekli sunuyor; **hiçbirini üretim için kötülemiyor.**
Kötülediği tek şey **gömülü pg0**'dır ("not recommended for production").
→ Yani resmî best-practice'in A1'e düşen kısmı tek bir cümledir: **harici, gerçek Postgres kullan.**

**(b) Bizim karma tercihimizle uyarlanmış yol.**
Karma **resmî olarak desteklidir**: depoda `docker/docker-compose/external-pg` senaryosu var ve
`HINDSIGHT_API_DATABASE_URL` hem Docker'da hem pip'te aynı şekilde çalışıyor
([external-pg](https://github.com/vectorize-io/hindsight/tree/main/docker/docker-compose/external-pg)).
Yani "hindsight konteynerde + Postgres native" meşru bir kurulumdur.

**(c) Önerim: native pip (venv) + native Postgres. Tek paragraf gerekçe:**
Kararı duygusal değil **teknik** bir gerçek belirliyor: **hiçbir hazır Docker imajı bizim istediğimiz
profili taşımıyor.** Full imaj (~3,7 GB ARM64) torch'lu lokal modelleri **bundle ediyor** — bizim
kullanmayacağımız ~2 GB'lık bir yük; slim imaj (~500 MB) ise lokal model **hiç içermiyor**, "requires
external services" diyor — yani embedding'i dışarı çıkarmamızı ister ki bu operatörün "dışarı giden
tek şey LLM" kısıtını **ihlal eder** ([installation](https://hindsight.vectorize.io/developer/installation)).
Aradaki ONNX profili (torch'suz + tam lokal) yalnız `pip install "hindsight-api-slim[local-onnx]"`
ile elde edilebiliyor. Buna Docker'ın A1'e getireceği filo bedeli ekleniyor — A1'de docker **bugün
yok**: daemon'ın kendisi yeni bir filo üyesi olur (systemd birimi, ~200–300 MB RAM, imaj katmanları
için disk, ayrı güvenlik güncelleme hattı, yedeklenecek yeni bir volume kavramı) ve bunların hiçbiri
karşılığında bize bir yetenek vermiyor, çünkü zaten tek servis + tek Postgres koşuyoruz. Postgres'i
native tutmak ayrıca operatörün asıl amacına hizmet ediyor: **birinci sınıf servis olarak kurulan pg,
ileride Meridian'ın başka bileşenlerince de kullanılabilir** ve mevcut yedek/yükseltme disiplinimize
(litestream dâhil) doğrudan girer — konteyner volume'una hapsedilmiş bir pg bunu yapamaz.
**Docker'a dönme tetikleyicisi:** ikiden fazla Hindsight süreci (ayrı worker'lar) koşurmaya
başlarsak ya da sürüm yükseltmelerinde geri-alma (rollback) elle çözülemeyecek kadar sıklaşırsa.

**Kıyas tablosu (operatörün istediği eksenler):**

| Eksen | Native pip + native pg | Docker + native pg | Docker + konteyner pg |
|---|---|---|---|
| İstenen ONNX profili | ✅ tam (`[local-onnx]`) | ⚠️ full imaj torch taşır | ⚠️ aynı |
| Yedekleme | ✅ mevcut pg disiplinine girer | ✅ pg native, aynı | ❌ volume ayrı hat |
| Yükseltme / rollback | 🟡 venv + pin | ✅ imaj etiketi | ✅ imaj etiketi |
| Başka tüketicinin pg'ye erişimi | ✅ doğrudan | ✅ doğrudan | ❌ konteyner içi |
| Filo bedeli | ✅ yeni daemon yok | ❌ dockerd + containerd | ❌ aynı |
| ARM desteği | ✅ (docs ✅, wheel'ler doğrulandı) | ✅ (~3,7 GB imaj) | ✅ |

### 10.1 Adım adım

**Adım 0 — ön ölçüm (Rol-1, A1'de):**
```bash
ssh -i ~/.ssh/oci-a1.key ubuntu@130.61.126.87 \
  'free -g; nproc; lsb_release -ds; python3 -V; systemctl list-units --type=service --state=running | head -30'
```
→ §6.4 karar kuralını burada uygula (available ≥ 5 GB mi?) ve Python'un ≥3.11 olduğunu doğrula.

**Adım 1 — Postgres native (PGDG deposundan, arm64):**
```bash
# PGDG deposu (arm64 destekli — postgresql.org duyurusu, §3.3)
sudo apt install -y postgresql-common
sudo /usr/share/postgresql-common/pgdg/apt.postgresql.org.sh
sudo apt install -y postgresql-17 postgresql-17-pgvector
```
Sürüm hükmü: docs 14+/15+ diye çelişiyor, compose 18 kullanıyor → **17 güvenli orta yol** (§3.1).

**Adım 2 — pgvector ve rol:**
```sql
CREATE ROLE hindsight LOGIN PASSWORD '<sır>';
CREATE DATABASE hindsight OWNER hindsight;
\c hindsight
CREATE EXTENSION IF NOT EXISTS vector;
```
`hindsight` rolü şemayı **kendisi kuracak** (migration on startup, §2.5) → DDL yetkisi gerekli.
Sır `.env`e; **versiyonlanmaz** (CLAUDE.md §1).

**Adım 3 — Postgres'i A1 boyutuna ayarla:**
`max_connections`, `shared_buffers` mevcut yüke göre. Hindsight'ın havuzu (adım 7) buna göre
kısılacak. `postgresql.conf` değişikliği **ölçülerek**, varsayılana güvenilerek değil.

**Adım 4 — Python venv (Python ≥3.11):**
```bash
python3 -m venv /opt/hindsight/venv
/opt/hindsight/venv/bin/pip install --upgrade pip
```

**Adım 5 — Hindsight, torch'suz, sürüm çivili:**
```bash
/opt/hindsight/venv/bin/pip install "hindsight-api-slim[local-onnx]==0.9.2"
```
**Çivi (mutlaka kontrol et):** `pip list | grep -iE 'torch|sentence-transformers'` **BOŞ olmalı.**
Boş değilse yanlış extra kurulmuştur (§8.3).
Ayrıca flashrank gerekiyorsa: `pip install flashrank` (§9 madde 7 — önce kontrol et, körlemesine kurma).

**Adım 6 — model önbelleğini önden doldur (opsiyonel ama önerilir):**
İlk `recall`da HuggingFace'ten indirme olur. Kapalı/yavaş ağ riskini almamak için modelleri
önden indir ve `HINDSIGHT_API_EMBEDDINGS_ONNX_MODEL_PATH` / `..._FLASHRANK_CACHE_DIR` ile göster.

**Adım 7 — yapılandırma (`/opt/hindsight/.env`, `chmod 600`):**
```bash
# --- veritabanı ---
HINDSIGHT_API_DATABASE_URL=postgresql://hindsight:<sır>@127.0.0.1:5432/hindsight
HINDSIGHT_API_RUN_MIGRATIONS_ON_STARTUP=true
HINDSIGHT_API_DB_POOL_MIN_SIZE=2
HINDSIGHT_API_DB_POOL_MAX_SIZE=10          # varsayılan 100 — A1 için fazla (§3.4)

# --- LLM: dışarı giden TEK trafik ---
HINDSIGHT_API_LLM_PROVIDER=openrouter       # ya da openai + BASE_URL (§5.2)
HINDSIGHT_API_LLM_API_KEY=<sır>
HINDSIGHT_API_LLM_MODEL=<≥65k çıktı tokenlı model — §5.4>
HINDSIGHT_API_LLM_MAX_CONCURRENT=6          # varsayılan 32 — 4 çekirdek için fazla (§6.4)
HINDSIGHT_API_REFLECT_MAX_COMPLETION_TOKENS=<maliyet tavanı>

# --- embedding: TAM LOKAL, çok dilli, torch'suz ---
HINDSIGHT_API_EMBEDDINGS_PROVIDER=onnx
# ONNX varsayılan modeli zaten intfloat/multilingual-e5-small (§4.2)

# --- BM25 dil ayarı: kurulum günü psql -c '\dF turkish' VARSA aç (§4.3 EK) ---
HINDSIGHT_API_TEXT_SEARCH_EXTENSION_NATIVE_LANGUAGE=turkish

# --- rerank: TAM LOKAL, çok dilli, ONNX + fail-open ---
HINDSIGHT_API_RERANKER_PROVIDER=flashrank
HINDSIGHT_API_RERANKER_FLASHRANK_MODEL=ms-marco-MultiBERT-L-12
HINDSIGHT_API_RERANKER_FLASHRANK_CPU_MEM_ARENA=false
HINDSIGHT_API_RERANKER_1_PROVIDER=rrf       # zincir sonu emniyet supabı (§4.5)

# --- worker kimliği ---
HINDSIGHT_API_WORKER_ID=a1-worker-1          # docs: üretimde sabitle (§1.1)
```

**Adım 8 — systemd birimi eskizi:**
```ini
[Unit]
Description=Hindsight agent memory API
After=network-online.target postgresql.service
Requires=postgresql.service

[Service]
Type=simple
User=hindsight
EnvironmentFile=/opt/hindsight/.env
ExecStart=/opt/hindsight/venv/bin/hindsight-api --host 127.0.0.1 --port 8888
Restart=on-failure
RestartSec=5
# kaynak çiti — A1'i koru (REVİZE 2026-08-31: 24 GB sonrası 3G→8G, §6.4 revizyon notu)
MemoryMax=8G
CPUQuota=200%
# sertleştirme
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/hindsight

[Install]
WantedBy=multi-user.target
```
`MemoryMax=8G` (revize 2026-08-31, 24 GB sonrası): Senaryo A tavanının (~1,8 GB) da Senaryo B
tavanının (~5,5 GB) da üstünde — model değişiminde birim dosyasına dokunmak gerekmez — ama A1'i
OOM'dan korumaya devam eder: Hindsight şişerse **Meridian worker'ı değil Hindsight** ölür ve
Meridian yığınına ≥16 GB kalır. Bu bilinçli bir tercih.
**Ve CLAUDE.md §9 gereği:** birim kurulduğu gün **elle test-ateşlenir** — "kurulu" ≠ "çalışır".

**Adım 9 — ilk bank + smoke test:**
```bash
# 1) sağlık — üçlü
curl -s localhost:8888/health/live
curl -s localhost:8888/health/ready
curl -s localhost:8888/version

# 2) bank oluştur — memory_defense İLK GÜNDEN açık (§8.5: sonradan geriye dönük taramıyor)
curl -X PUT localhost:8888/v1/default/banks/meridian-arsiv \
  -H "Content-Type: application/json" \
  -d '{"memory_defense": {...politika...}, "retain_mission": "..."}'

# 3) Türkçe retain
curl -X POST localhost:8888/v1/default/banks/meridian-arsiv/memories \
  -H "Content-Type: application/json" \
  -d '{"items":[{"content":"<Türkçe test metni>","document_id":"smoke-001"}]}'
#    -> yanıtta usage.total_tokens gelmeli (maliyet ölçülebilir, §5.6)

# 4) Türkçe recall — asıl sınav
curl -X POST localhost:8888/v1/default/banks/meridian-arsiv/memories/recall \
  -H "Content-Type: application/json" \
  -d '{"query":"<Türkçe soru>","trace":true,"include":{"source_facts":true}}'

# 5) mükerrer-önleme çivisi: aynı document_id ile tekrar retain, olgu sayısı ARTMAMALI
# 6) metrik ucu
curl -s localhost:8888/metrics | head
```

**Adım 10 — mutasyon çivisi (CLAUDE.md §6: "çivi yeşili kanıt değildir"):**
Smoke test yeşil olunca, yanlış sebeple yeşil olmadığını göster:
- `EMBEDDINGS_PROVIDER`i bilerek `local`a çevir → torch yok, **patlamalı**. Patlamıyorsa `[all]`
  kurulmuş demektir (§8.3 çivisi).
- `RERANKER_PROVIDER`i bozuk bir değere çevir → `rrf` failover'ı devreye girip recall **çalışmaya
  devam etmeli** (fail-open doğrulaması, §4.5).
- Türkçe recall'u bir de İngilizce-only modelle koş, sonuçları kıyasla → çok dilli seçimin
  gerçekten fark yarattığını **ölç** (yoksa §8.1 azaltması kanıtsızdır).

**Adım 11 — yedek hattına bağla:**
Postgres native olduğu için mevcut disipline girer. Üstüne mantıksal katman:
`hindsight-admin backup` → zip. Yükseltme öncesi **zorunlu**.

---

## 11. ÖZET HÜKÜM

Hindsight, Meridian'ın dört amacının (arşiv araması · Ajan-B bağlamı · nedensel/zamansal sorgu ·
mükerrer-önleme) **dördüne de** doğrudan karşılık gelen özellikler taşıyor ve MIT lisanslı,
telemetrisiz, ARM64'te resmen destekli. Kısıtlarımızla (tam lokal, yalnız LLM dışarı, aarch64,
4 çekirdek, 12 GB) **uyumludur** — ama **varsayılan yapılandırmayla değil.** Varsayılanlar
İngilizce-only ve torch'ludur; doğru kurulum, `onnx` embedding + `flashrank` rerank + native
Postgres üçlüsüdür ve bu üçlü aynı anda hem en hafif hem çok dilli hem torch'suz olandır.
En büyük risk teknik değil **sessizlik** riskidir: Türkçe içerikte yanlış model hata vermez,
sadece kötü cevap verir. Bu yüzden kurulum, ön-kayıtlı bir ölçüm kartı olmadan "bitti" sayılamaz.
