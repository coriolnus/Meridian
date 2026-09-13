# EDG-2026-085 Senaryo-A — icra-anı IEX quote kaydı (tick pilotu) Uygulama Planı

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Motorun mevcut TEK Alpaca data bağlantısına, bayrakla açılan ve emir penceresiyle sınırlı bir `quotes` aboneliği ekleyerek her canlı kâğıt dolumunun anındaki bid/ask'ı ayrı bir JSONL'e kaydetmek ve bu kayıttan kartın dört eksenini (kayıp oranı · bant-içi tutarlılık · disk · CPU/worker) hesaplayan çevrimdışı rapor aracını yazmak.

**Architecture:** Üç motor parçası + bir araştırma aracı. (1) `meridian/quotecapture.py` (YENİ): halka tamponu (sembol başına son 90 sn quote), emir pencereleri (coid → başlangıç/dolum/kapanış), günlük JSONL yazıcı (kayıt + ham; dosya adları `edg085_` önekli), abone kümesi (pozisyonlar ∪ bekleyen emirler, ≤30, öncelikli) ve sağlık anlık görüntüsü. (2) `meridian/marketstream.py`: oturum içinde bayrak açıksa bir eşlik görevi `quotes` subscribe/unsubscribe mesajlarını AYNI soketten gönderir; gelen `T=="q"` çerçeveleri quotecapture'a yönlendirilir; `b` yolu ve hotstate değişmez. (3) `meridian/mirror_stream.py`: `apply` her trade_updates olayını quotecapture'a iletir (new/accepted → pencere aç; fill → dolum işareti + 30 sn kuyruk; canceled/expired/rejected → kapat). (4) `research/olcumler/edg085_icra_ani_quote/rapor.py`: kayıt + E2 defteri + `meridian.db trades` + `bars_intraday` + `taban.jsonl` → dolum başına satır, K ölçüleri, üç PK, fizibilite deltası. Bayrak VARSAYILAN KAPALI (`MERIDIAN_QUOTE_CAPTURE=0`): kod 09-14 dağıtımıyla canlıya iner, pilot 2026-09-21'de bayrakla açılır (kart `adim_0_kaydi_2026_09_13`).

**Tech Stack:** Python 3.12, asyncio + `websockets` (mevcut `streamhealth.run_stream` sürücüsü), Alpaca data WS (`quotes` kanalı, `T:"q"` mesajı: `S, bp, bs, ap, as, bx, ax, c, t, z`), JSONL, pytest (`sandbox_state`), DuckDB/sqlite3 (rapor aracı okuma), mevcut `store`/`obs`/`codelaw` sözleşmeleri.

**Spec:** `research/cards/EDG-2026-085-icra-ani-quote-kaydi-senaryo-a.yaml` (hipotez, K=2, eşikler, kill-list, üç PK, ADIM-0 kayıtları 09-07 + 09-13). Ad çakışması uyarısı: `docs/TASARIM-13-INTRADAY-DOLUM-SOZLESMESI-2026-08-23.md` §3'teki "A1/A2/A3" DAKİKA-BARI aşamalarıdır; bu planın "Senaryo-A"sı canlı quote eksenidir (kart üst yorumu). Bu plan kartın sözleşmesini KODA çevirir; eşik/pencere/kill tanımı karttan alınır, burada DEĞİŞTİRİLMEZ.

## Global Constraints

- **Kill#2 (mimari):** iex hesap başına TEK data bağlantısı; `quotes` aboneliği MEVCUT `MarketStreamListener` soketine `{"action":"subscribe","quotes":[...]}` / `{"action":"unsubscribe","quotes":[...]}` mesajıyla eklenir/çıkarılır. İkinci soket, ikinci dinleyici, ikinci `websockets.connect` YASAK.
- **Kill#4 (disk yolu):** kayıt canlı `state/` içine ya da E2/trades defterine YAZILMAZ. Kayıt dizini YALNIZ `MERIDIAN_EDG085_KAYIT_DIZIN` ortam değişkeninden gelir (A1: `/opt/veri/olcum/edg085/kayit`); değişken boşsa hiçbir dosya yazılmaz. Testler `sandbox_state` + `tmp_path` ile koşar ve `state/` altına tek bayt yazılmadığını ölçer.
- **Kill#3 (sessiz düşürme yok):** her motor dolumu için bir `tur:"dolum"` işaret satırı yazılır — quote yakalanmamışsa `kayip_nedeni` dolu (`abone_degil` · `tavan_asimi` · `pencere_yok` · `sembol_sessiz` · `baglanti_yok`). Rapor aracı eşlenemeyen dolumu ADIYLA sayar.
- **Look-ahead disiplini (marketstream başlığı):** `q` çerçeveleri mrd:price/mrd:bars'a ASLA yazılmaz; `hotstate.ingest_bars` yalnız `b` ile çağrılır (mevcut çivi `test_batched_array_only_b_bars_ingested` korunur).
- **Yapısal sınır (v84 `test_structural_no_order_or_disk_paths`):** `marketstream.py` kaynağında `write_json/write_jsonl/append_jsonl/write_text/httpx/submit_plan/...` GEÇMEZ — dosya yazımı quotecapture'da yaşar.
- **Bayrak:** `MERIDIAN_QUOTE_CAPTURE` varsayılan `"0"`. Kapalıyken: abonelik mesajı gönderilmez, `q` çerçeveleri yok sayılır (bugünkü davranış bit-özdeş), mirror kancası erken döner, sağlık `{"aktif": false}` der.
- **Tavan:** abone kümesi ≤ 30 sembol (t/q kanal tavanı). Öncelik: açık pozisyon > `P-` önekli (motor girişi) bekleyen emir > diğer bekleyen emir. Tavan aşımı sayılır ve düşen sembolün dolumu `tavan_asimi` ile işaretlenir.
- **Pencere (kart):** kayıt = [gönderim, dolum] ± 30 sn. Gönderim öncesi 30 sn HALKA tamponundan (`faz:"halka_geri"`), gönderim→dolum sürekli (`faz:"pencere"`), dolum sonrası 30 sn (`faz:"dolum_sonrasi"`). Sürekli kayıt tavanı 1.800 sn (pencere kapanır, `kayip_nedeni:"pencere_tavani"` işareti; abonelik sürer). Bracket bacağı (uuid coid) dolumları için pencere yoktur: halka_geri + dolum_sonrasi.
- **Yasa 4:** hiçbir sinyalsiz `except`; dosya yazımı düşerse `obs.warn("quote_capture_yazim_dustu", ...)` (dakikada en çok bir kez, sayaç sağlıkta).
- **Yasa 6:** kayıt dosyaları tarihli addır → `codelaw.DECLARED_SINK_PATTERNS`e yapısal beyan (`sinif`, `gerekce`, `sinanamaz` alanları; okuyucu `research/.../rapor.py` — motor dışı, statik graf görmez). `tests/test_codelaw_kor_nokta_v214.py` donmuş tabanı değişirse AYNI commit'te güncellenir ve gerekçesi yazılır.
- **Çapa yasası:** `dosya.py:SATIR` biçimi YASAK (tests/ dahil); sembol çapası `modul.py::ad`.
- **PIT'e dokunulmaz;** `pitlaw` kayıtlarına yeni kapı yüzeyi eklenmez (bu iş karar yüzeyi değildir).
- **Test kimlikleri:** `tests/test_quote_capture_v465.py` (motor üçlüsü), `tests/test_edg085_rapor_v466.py` (rapor aracı). Numara kimliktir; çakışma varsa az-çapalı taraf taşınır.
- **Koşum:** `.venv/bin/python -m pytest <dosya> -p no:cacheprovider` seri; `-n`/`-q` verilmez. Her çivi için en az bir mutasyon kanıtı (kaynak yedeği `cp`, geri alım kopyadan + sha256; `git checkout --` ASLA).
- **Uydurma yasağı:** ölçülemeyen alan `None` + neden (satırda `..._neden`).
- **Alpaca `q` şeması (ölçülmüş, Alpaca docs v2 stream):** `{"T":"q","S":"AAPL","bx":"V","bp":..,"bs":..,"ax":"V","ap":..,"as":..,"c":["R"],"t":"2026-09-14T13:46:01.208Z","z":"C"}`; `bs/as` lot sayısıdır (×100 hisse), `t` RFC3339 nanosaniye olabilir (`Z` ile biter) — parse tolere eder (ilk 26 karakter + `Z`).

---

## Dosya yapısı

| Dosya | Sorumluluk |
|---|---|
| `meridian/quotecapture.py` (YENİ) | halka tamponu · pencereler · abone kümesi · JSONL yazıcı (kayıt + ham) · sağlık anlık görüntüsü · bayrak/dizin okuma |
| `meridian/marketstream.py` (DEĞİŞİR) | `q` çerçevesi yönlendirme, `quotes` abonelik eşlik görevi, `subscription` mesajından abone sayısı, sağlıkta `quote_capture` bloğu, docstring güncellemesi |
| `meridian/mirror_stream.py` (DEĞİŞİR) | `OrderStateMachine.apply` → `quotecapture.olay(event, order)` kancası (kilit DIŞINDA, `_persist`ten sonra) |
| `meridian/codelaw.py` (DEĞİŞİR) | `DECLARED_SINK_PATTERNS["edg085 kayit"]` beyanı |
| `tests/test_quote_capture_v465.py` (YENİ) | A) quotecapture birim · B) marketstream q yolu · C) mirror kancası · D) yapısal sınırlar · E) mutasyon |
| `research/olcumler/edg085_icra_ani_quote/rapor.py` (YENİ) | KOMUT SATIRI aracı: kayıt + defterler → `sonuc_<gün>.json` + `rapor_<gün>.md`; PK-1 sentetik, PK-3 bar çaprazı; fizibilite deltası |
| `tests/test_edg085_rapor_v466.py` (YENİ) | rapor aracı çivileri (tmp dizin, sahte kayıt/defterler) |
| `deploy/oracle-a1/meridian.service.d/55-edg085-quote.conf` (YENİ) | `Environment=MERIDIAN_QUOTE_CAPTURE=0` + `Environment=MERIDIAN_EDG085_KAYIT_DIZIN=/opt/veri/olcum/edg085/kayit` (ansible drop-in glob'u otomatik alır) |

Arayüz sözleşmesi (Task 1 üretir, Task 2–4 tüketir):

```python
# meridian/quotecapture.py — kamu yüzeyi
AKTIF_ENV = "MERIDIAN_QUOTE_CAPTURE"          # "1" → aktif; varsayılan "0"
DIZIN_ENV = "MERIDIAN_EDG085_KAYIT_DIZIN"     # boş/yok → dosya yazımı yok (aktifse bir kez warn)
HALKA_S = 90            # halka tamponu derinliği (sn)
PAY_S = 30              # pencere payı (kart: ±30 sn)
PENCERE_TAVAN_S = 1800  # sürekli kayıt tavanı (sn)
ABONE_TAVAN = 30        # t/q kanal tavanı
MOTOR_COID_ONEKI = "P-" # alpaca.ENGINE_COID_PREFIX ile AYNI değer — ithal edilir, kopyalanmaz

def aktif() -> bool
def get() -> "QuoteCapture"                      # süreç-içi tekil (test fixture sıfırlar: quotecapture._KAYIT = None)
class QuoteCapture:
    def __init__(self, dizin: str | None, simdi=None)   # simdi: () -> datetime (UTC) — test enjeksiyonu
    def istenen_abonelik(self) -> list[str]     # pozisyonlar ∪ bekleyen emir sembolleri, öncelikli, ≤ ABONE_TAVAN
    def q_geldi(self, m: dict) -> None          # marketstream'den; halkaya ekle, açık pencere varsa kayıt + ham
    def olay(self, event: str, order: dict) -> None   # mirror_stream'den (trade_updates olayı + order sözlüğü)
    def abonelik_degisti(self) -> "asyncio.Event"     # marketstream eşlik görevi bekler
    def snapshot(self) -> dict                  # {"aktif","dizin","abone_n","abone","pencere_acik","satir_bugun","ham_bugun","son_q_at","yazim_hata_n","tavan_asimi_n"}
```

Kayıt satırı (`edg085_<gün>.jsonl`, gün = `alindi` UTC — `edg085_` öneki tur-2 Rol-1 kararı: codelaw `_joined_glob` literal parçayı korur, anahtar `*/edg085_*.jsonl`a daralır; inceleme K1):

```json
{"tur":"quote","alindi":"2026-09-14T13:46:01Z","ts":"2026-09-14T13:46:01.208Z","sembol":"AAPL","coid":"P-2026-09-14-AAPL-1","faz":"pencere","bid":231.12,"ask":231.15,"bid_lot":3,"ask_lot":5,"bx":"V","ax":"V","kosul":["R"]}
{"tur":"dolum","alindi":"...","sembol":"AAPL","coid":"P-...","yon":"buy","dolum_ts":"...","dolum_fiyat":231.14,"quote_n_pencere":57,"son_quote":{"ts":"...","bid":231.12,"ask":231.15},"kayip_nedeni":null}
{"tur":"pencere","alindi":"...","sembol":"AAPL","coid":"P-...","olay":"ac|kapat","neden":"new|fill+30s|canceled|expired|rejected|pencere_tavani"}
```

Ham satırı (`edg085_ham_<gün>.jsonl`): gelen `q` mesajı sözlüğü `json.dumps(m, separators=(",",":"))` ile OLDUĞU GİBİ (süzgeç/halka öncesi), yalnız kayıt aktifken (o sembol için açık pencere ya da dolum-sonrası kuyruk varken) — PK-2'nin ikinci kaynağı.

---

### Task 1: `meridian/quotecapture.py` — halka, pencere, abone kümesi, yazıcı

**Files:**
- Create: `meridian/quotecapture.py`
- Test: `tests/test_quote_capture_v465.py` (A bölümü)

**Interfaces:**
- Consumes: `store.read_json("portfolio.json")` (pozisyon anahtarları), `store.read_json("mirror_orders.json")` (açılışta bekleyen emir tohumu; anahtar coid → `{status, symbol, side}`; PENDING/TERMINAL sözlüğü `mirror_stream.PENDING`/`TERMINAL` İTHAL edilir, kopyalanmaz — döngüsel import yoksa; varsa `mirror_stream` içindeki kümeler `quotecapture`'a taşınır ve mirror oradan ithal eder), `adapters.alpaca.ENGINE_COID_PREFIX`, `obs.warn`.
- Produces: yukarıdaki kamu yüzeyi.

- [ ] **Step 1: Kırmızı çiviler (A bölümü)** — `tests/test_quote_capture_v465.py`:

```python
"""test_quote_capture_v465.py — EDG-2026-085 Senaryo-A: icra-anı quote kaydı (halka · pencere · abone · yazıcı ·
marketstream q yolu · mirror kancası). Kart: research/cards/EDG-2026-085-icra-ani-quote-kaydi-senaryo-a.yaml."""
import asyncio, datetime as dt, json, pathlib
import pytest
from meridian import quotecapture as qc

class Saat:
    def __init__(self, t0="2026-09-14T13:45:00Z"):
        self.t = dt.datetime.fromisoformat(t0.replace("Z", "+00:00"))
    def __call__(self): return self.t
    def ilerle(self, s): self.t += dt.timedelta(seconds=s)

def _q(sembol, bid, ask, ts):
    return {"T": "q", "S": sembol, "bp": bid, "bs": 2, "ap": ask, "as": 3, "bx": "V", "ax": "V", "c": ["R"], "t": ts, "z": "C"}

def _emir(coid, sembol, side="buy", event="new", **ek):
    return event, {"client_order_id": coid, "symbol": sembol, "side": side, "status": ek.pop("status", event), **ek}

@pytest.fixture
def kayit(tmp_path, sandbox_state, monkeypatch):
    monkeypatch.setenv(qc.AKTIF_ENV, "1")
    d = tmp_path / "kayit"
    monkeypatch.setenv(qc.DIZIN_ENV, str(d))
    qc._KAYIT = None
    saat = Saat()
    k = qc.QuoteCapture(str(d), simdi=saat)
    yield k, d, saat
    qc._KAYIT = None

def _satirlar(d, ad):
    p = d / ad
    return [json.loads(s) for s in p.read_text().splitlines()] if p.exists() else []

def test_A1_pencere_disi_quote_YAZILMAZ_halkada_tutulur(kayit):
    k, d, saat = kayit
    k.q_geldi(_q("AAPL", 100.0, 100.1, "2026-09-14T13:45:00.100Z"))
    assert _satirlar(d, "2026-09-14.jsonl") == []
    assert k.snapshot()["satir_bugun"] == 0 and k.snapshot()["son_q_at"] is not None

def test_A2_new_olayi_pencere_acar_halka_geri_30sn_dokulur(kayit):
    k, d, saat = kayit
    for i in range(6):                       # 13:44:10 .. 13:44:60 → yalnız son 30 sn halka_geri'ye girer
        saat.t = Saat("2026-09-14T13:44:10Z").t + dt.timedelta(seconds=10 * i)
        k.q_geldi(_q("AAPL", 100 + i, 100.1 + i, saat.t.isoformat().replace("+00:00", "Z")))
    saat.t = Saat("2026-09-14T13:45:05Z").t
    k.olay(*_emir("P-2026-09-14-AAPL-1", "AAPL"))
    rows = _satirlar(d, "2026-09-14.jsonl")
    geri = [r for r in rows if r["tur"] == "quote" and r["faz"] == "halka_geri"]
    assert [r["bid"] for r in geri] == [103, 104, 105], "yalnız son 30 sn (≥13:44:35) dökülmeli"
    assert any(r["tur"] == "pencere" and r["olay"] == "ac" and r["neden"] == "new" for r in rows)

def test_A3_pencere_icinde_quote_kayit_ve_HAM_yazilir(kayit):
    k, d, saat = kayit
    k.olay(*_emir("P-1", "AAPL"))
    saat.ilerle(2)
    m = _q("AAPL", 100.0, 100.2, "2026-09-14T13:45:02.000Z")
    k.q_geldi(m)
    rows = [r for r in _satirlar(d, "2026-09-14.jsonl") if r["tur"] == "quote"]
    assert rows[-1]["faz"] == "pencere" and rows[-1]["coid"] == "P-1" and rows[-1]["ask"] == 100.2
    ham = _satirlar(d, "ham_2026-09-14.jsonl")
    assert ham == [m], "ham çerçeve OLDUĞU GİBİ (süzgeçsiz) yazılmalı"

def test_A4_fill_dolum_isareti_ve_30sn_kuyruk_sonra_kapanis(kayit):
    k, d, saat = kayit
    k.olay(*_emir("P-1", "AAPL"))
    saat.ilerle(5); k.q_geldi(_q("AAPL", 100.0, 100.2, "2026-09-14T13:45:05.000Z"))
    saat.ilerle(1)
    k.olay(*_emir("P-1", "AAPL", event="fill", status="filled", filled_avg_price="100.15", filled_at="2026-09-14T13:45:06.4Z"))
    saat.ilerle(10); k.q_geldi(_q("AAPL", 100.1, 100.3, "2026-09-14T13:45:16.000Z"))   # dolum_sonrasi
    saat.ilerle(25); k.q_geldi(_q("AAPL", 100.2, 100.4, "2026-09-14T13:45:41.000Z"))   # +35 sn → kapanmış, yazılmaz
    rows = _satirlar(d, "2026-09-14.jsonl")
    dolum = [r for r in rows if r["tur"] == "dolum"][0]
    assert dolum["coid"] == "P-1" and dolum["dolum_fiyat"] == 100.15 and dolum["quote_n_pencere"] == 1
    assert dolum["kayip_nedeni"] is None and dolum["son_quote"]["ask"] == 100.2
    fazlar = [r["faz"] for r in rows if r["tur"] == "quote"]
    assert fazlar == ["pencere", "dolum_sonrasi"]
    assert [r for r in rows if r["tur"] == "pencere" and r["olay"] == "kapat"][-1]["neden"] == "fill+30s"

def test_A5_quote_suz_dolum_kayip_nedeni_SEMBOL_SESSIZ(kayit):
    k, d, saat = kayit
    k.olay(*_emir("P-1", "AAPL"))
    saat.ilerle(3)
    k.olay(*_emir("P-1", "AAPL", event="fill", status="filled", filled_avg_price="100.15"))
    dolum = [r for r in _satirlar(d, "2026-09-14.jsonl") if r["tur"] == "dolum"][0]
    assert dolum["quote_n_pencere"] == 0 and dolum["kayip_nedeni"] == "sembol_sessiz"

def test_A6_abone_degil_dolum_isareti(kayit, monkeypatch):
    k, d, saat = kayit
    # NVDA motor-dışı: pozisyon değil, bekleyen emir değil → abone kümesinde yok
    k.olay(*_emir("6f0c-uuid", "NVDA", event="fill", status="filled", filled_avg_price="10"))
    dolum = [r for r in _satirlar(d, "2026-09-14.jsonl") if r["tur"] == "dolum"][0]
    assert dolum["kayip_nedeni"] == "abone_degil"

def test_A7_bracket_bacagi_uuid_coid_halka_geri_ve_dolum_sonrasi(kayit):
    k, d, saat = kayit
    k.olay(*_emir("P-1", "AAPL"))                       # sembol abone kümesine girer
    saat.ilerle(1); k.q_geldi(_q("AAPL", 99.0, 99.1, "2026-09-14T13:45:01.000Z"))
    saat.ilerle(1)
    k.olay(*_emir("P-1", "AAPL", event="fill", status="filled", filled_avg_price="99.05"))
    saat.ilerle(3600)                                    # bir saat sonra stop bacağı dolar
    k.q_geldi(_q("AAPL", 95.0, 95.1, "2026-09-14T14:45:00.000Z"))   # halkada
    saat.ilerle(1)
    k.olay(*_emir("e1a2-uuid", "AAPL", side="sell", event="fill", status="filled", filled_avg_price="95.02"))
    rows = _satirlar(d, "2026-09-14.jsonl")
    cikis = [r for r in rows if r["tur"] == "dolum" and r["coid"] == "e1a2-uuid"][0]
    assert cikis["quote_n_pencere"] == 1 and cikis["kayip_nedeni"] is None
    assert [r["faz"] for r in rows if r["tur"] == "quote" and r["coid"] == "e1a2-uuid"] == ["halka_geri"]

def test_A8_pencere_tavani_1800sn_kapatir_ve_isaretler(kayit):
    k, d, saat = kayit
    k.olay(*_emir("P-1", "AAPL"))
    saat.ilerle(qc.PENCERE_TAVAN_S + 1)
    k.q_geldi(_q("AAPL", 100.0, 100.1, "2026-09-14T14:15:01.000Z"))
    rows = _satirlar(d, "2026-09-14.jsonl")
    assert [r for r in rows if r["tur"] == "pencere" and r["olay"] == "kapat"][-1]["neden"] == "pencere_tavani"
    assert not [r for r in rows if r["tur"] == "quote" and r["faz"] == "pencere"]

def test_A9_abone_kumesi_oncelik_ve_tavan(kayit, monkeypatch):
    from meridian import store
    k, d, saat = kayit
    store.write_json("portfolio.json", {"positions": {f"POS{i}": {} for i in range(20)}})
    for i in range(15):
        k.olay(*_emir(f"P-{i}", f"GIR{i}"))
    for i in range(5):
        k.olay(*_emir(f"uuid-{i}", f"DIG{i}", event="accepted"))
    ab = k.istenen_abonelik()
    assert len(ab) == qc.ABONE_TAVAN and ab[:20] == [f"POS{i}" for i in range(20)]
    assert ab[20:] == [f"GIR{i}" for i in range(10)] and k.snapshot()["tavan_asimi_n"] == 10
    k.olay(*_emir("P-14", "GIR14", event="fill", status="filled", filled_avg_price="1"))
    assert [r for r in _satirlar(d, "2026-09-14.jsonl") if r["tur"] == "dolum"][-1]["kayip_nedeni"] == "tavan_asimi"

def test_A10_terminal_olay_sembolu_kumeden_dusurur_ve_event_set_eder(kayit):
    k, d, saat = kayit
    k.olay(*_emir("P-1", "AAPL"))
    assert "AAPL" in k.istenen_abonelik() and k.abonelik_degisti().is_set()
    k.abonelik_degisti().clear()
    k.olay(*_emir("P-1", "AAPL", event="canceled", status="canceled"))
    assert "AAPL" not in k.istenen_abonelik() and k.abonelik_degisti().is_set()
    assert [r for r in _satirlar(d, "2026-09-14.jsonl") if r["tur"] == "pencere"][-1]["neden"] == "canceled"

def test_A11_dizin_yoksa_yazim_yok_ve_BIR_kez_warn(sandbox_state, monkeypatch):
    monkeypatch.setenv(qc.AKTIF_ENV, "1"); monkeypatch.delenv(qc.DIZIN_ENV, raising=False)
    uyarilar = []
    monkeypatch.setattr(qc.obs, "warn", lambda ev, **f: uyarilar.append(ev))
    k = qc.QuoteCapture(None, simdi=Saat())
    k.olay(*_emir("P-1", "AAPL")); k.q_geldi(_q("AAPL", 1, 1.1, "2026-09-14T13:45:01.000Z"))
    assert uyarilar.count("quote_capture_dizin_yok") == 1 and k.snapshot()["dizin"] is None

def test_A12_yazim_dusunce_WARN_ve_sayac(kayit, monkeypatch):
    k, d, saat = kayit
    uyarilar = []
    monkeypatch.setattr(qc.obs, "warn", lambda ev, **f: uyarilar.append((ev, f)))
    d.mkdir(exist_ok=True); (d / "2026-09-14.jsonl").mkdir()          # dosya yerine DİZİN → açılamaz
    k.olay(*_emir("P-1", "AAPL"))
    assert uyarilar and uyarilar[0][0] == "quote_capture_yazim_dustu" and k.snapshot()["yazim_hata_n"] >= 1

def test_A13_STATE_altina_tek_bayt_yazilmaz(kayit, sandbox_state):
    from meridian import store
    k, d, saat = kayit
    once = sorted(p.name for p in pathlib.Path(store.STATE_DIR).rglob("*")) if hasattr(store, "STATE_DIR") else None
    k.olay(*_emir("P-1", "AAPL")); k.q_geldi(_q("AAPL", 1, 1.1, "2026-09-14T13:45:01.000Z"))
    k.olay(*_emir("P-1", "AAPL", event="fill", status="filled", filled_avg_price="1"))
    sonra = sorted(p.name for p in pathlib.Path(store.STATE_DIR).rglob("*")) if hasattr(store, "STATE_DIR") else None
    assert once == sonra, "quotecapture state/ altına yazdı"
```

`store.STATE_DIR` adı yoksa `store`'un sandbox kök yolunu veren sembolü ÖLÇ (`grep -n "def _path\|STATE\b" meridian/store.py`) ve testte onu kullan; uydurma.

- [ ] **Step 2: Koş, KIRMIZI gör** — `.venv/bin/python -m pytest tests/test_quote_capture_v465.py -p no:cacheprovider -k test_A` → `ModuleNotFoundError: meridian.quotecapture`.

- [ ] **Step 3: Modülü yaz** — asgari, sözleşmeye birebir:

```python
"""quotecapture.py — EDG-2026-085 Senaryo-A: icra-anı IEX quote kaydı (halka · pencere · abone · yazıcı).

NE YAPAR: marketstream'in TEK data soketine bayrakla eklenen `quotes` aboneliğinden gelen `q` çerçevelerini
sembol başına HALKA tamponunda (son HALKA_S sn) tutar; mirror_stream'den gelen emir olaylarıyla pencere açar
(new/accepted → sürekli kayıt; fill → dolum işareti + PAY_S sn kuyruk; terminal → kapat) ve YALNIZ pencere
içindeki quote'ları günlük JSONL'e yazar (`<gün>.jsonl`), ham çerçeveyi ayrı dosyaya (`ham_<gün>.jsonl`,
PK-2 ikinci kaynak). Abone kümesi: açık pozisyonlar ∪ bekleyen emir sembolleri, ≤ ABONE_TAVAN, öncelikli.

DEĞİŞMEZLER: kayıt dizini YALNIZ MERIDIAN_EDG085_KAYIT_DIZIN'den (kill#4: state/ ve defterlere ASLA);
hiçbir sinyalsiz except (Yasa 4: yazım arızası quote_capture_yazim_dustu, dakikada bir); her motor dolumu
işaret satırı alır — quote yoksa kayip_nedeni dolu (kill#3); q çerçevesi hotstate'e ASLA gitmez (look-ahead).
Bayrak MERIDIAN_QUOTE_CAPTURE varsayılan "0" — kapalıyken bu modül hiçbir şey yapmaz (bit-özdeş davranış).
OKUR: portfolio.json (pozisyonlar), mirror_orders.json (açılış tohumu) — store üzerinden, salt-okur.
YAZAR: yalnız kayıt dizinine. OKUYUCU: research/olcumler/edg085_icra_ani_quote/rapor.py (Rol-1, salt-okur);
codelaw.DECLARED_SINK_PATTERNS "edg085 kayit" beyanı.
"""
```

Uygulama notları (implementer ölçer, uydurmaz):
- Halka: `collections.deque` sembol başına; eleman `(alindi_dt, satir_dict)`; `q_geldi` eskileri (`alindi < simdi - HALKA_S`) atar.
- Pencereler: `self._pencereler: dict[coid, {"sembol","yon","baslangic","dolum_ts","kapanis","faz"}]`; `olay()`:
  - `event in ("new","accepted","pending_new")` ve coid `MOTOR_COID_ONEKI` ile başlıyorsa → pencere aç (`faz="pencere"`), halka_geri dök (`alindi >= simdi - PAY_S`), `tur:"pencere" olay:"ac"` satırı; sembolü bekleyenlere ekle; `abonelik_degisti().set()`.
  - `event in ("fill",)` (partial_fill: dolum işareti YAZMA, `quote_n` say — kısmi dolum sürerken tek işaret son fill'de): pencere varsa → `dolum_ts` (`order.filled_at` varsa o, yoksa `simdi`), `faz="dolum_sonrasi"`, `kapanis = dolum_ts + PAY_S`; pencere yoksa (bracket bacağı) → halka_geri dök + `dolum_sonrasi` kuyruğu için geçici pencere (aynı yapı, `baslangic=None`). Dolum işareti: `quote_n_pencere` = o coid için yazılan quote satırı sayısı (halka_geri dahil), `son_quote` = dolumdan önceki son quote (halkadan), `kayip_nedeni`: sembol abone kümesinde değilse `abone_degil`; tavan düşürdüyse `tavan_asimi`; abonede ama hiç quote yoksa `sembol_sessiz`; marketstream canlı değilse (`_baglanti_ok` bayrağı — Task 2 set eder) `baglanti_yok`; yoksa `None`.
  - `event in ("canceled","expired","rejected","replaced","done_for_day")` → pencere kapat (`neden=event`), bekleyenlerden düş, `abonelik_degisti().set()`.
  - `held`/`pending_cancel`/diğer → bekleyen kümesine dokunma (bilinmeyen olay yok sayılır ama `snapshot()["bilinmeyen_olay_n"]` sayar — sessiz değil).
- `q_geldi`: `m["S"]` yoksa dön; halkaya ekle; sembolün açık penceresi varsa (faz pencere ya da dolum_sonrasi ve `simdi <= kapanis`) → quote satırı + ham satırı; `simdi > kapanis` → pencereyi kapat (`fill+30s`), yazma; `faz=="pencere"` ve `simdi - baslangic > PENCERE_TAVAN_S` → kapat (`pencere_tavani`), yazma.
- Dosya yazımı: `open(yol, "a", encoding="utf-8")` her satırda (düşük hacim; kilit gerekmez — tek yazar süreç); `os.makedirs(dizin, exist_ok=True)` bir kez; `OSError` → `obs.warn("quote_capture_yazim_dustu", error=..., yol=...)` en çok 60 sn'de bir, `yazim_hata_n += 1`.
- `istenen_abonelik()`: `store.read_json("portfolio.json", {}).get("positions", {})` anahtarları (sırayla) + `P-` bekleyenler + diğer bekleyenler; tekilleştir; `[:ABONE_TAVAN]`; düşenler `self._tavan_disi` kümesine (dolum işareti için), `tavan_asimi_n` = düşen sayısı.
- Açılış tohumu: `__init__` içinde `store.read_json("mirror_orders.json", {}).get("orders", {})` → status PENDING olanlar bekleyenlere (mirror'ın `PENDING` kümesi ithal). Test: A14 (implementer yazar): tohumlu dosya ile `istenen_abonelik` bekleyen sembolü içerir.
- Zaman: `simdi` enjekte edilebilir (`simdi=None → lambda: dt.datetime.now(dt.timezone.utc)`); satır `alindi` ISO saniye, `Z`.
- Tekil: `_KAYIT: QuoteCapture | None`; `get()` env'den kurar (`aktif()` False ise yine nesne döner ama `olay/q_geldi` no-op — Task 2/3 çağıranlar `aktif()` ile kapıyı geçer; çift kapı bilinçli: modül kendi kendini de korur).

- [ ] **Step 4: Koş, YEŞİL gör** — `-k test_A` hepsi geçer; `tests/test_codelaw_v59.py` (Yasa 4 tarayıcısı) yeşil.

- [ ] **Step 5: Mutasyon kanıtı** — (a) `halka_geri` dökümündeki `PAY_S` süzgecini kaldır → A2 kırmızı; (b) dolum işaretindeki `kayip_nedeni` hesabını `None`'a sabitle → A5/A6/A9 kırmızı; (c) `PENCERE_TAVAN_S` kontrolünü kaldır → A8 kırmızı. Her mutasyon kopyadan geri alınır, sha256 eşitliği raporlanır.

- [ ] **Step 6: Commit** — `git add meridian/quotecapture.py tests/test_quote_capture_v465.py && git commit -m "quotecapture: EDG-085 Senaryo-A halka/pencere/abone/yazıcı (v465 A)"`

---

### Task 2: marketstream — `quotes` aboneliği (eşlik görevi) + `q` yönlendirme + sağlık

**Files:**
- Modify: `meridian/marketstream.py` (`MarketStreamListener.session`, `snapshot`, `health`, modül docstring)
- Modify: `meridian/codelaw.py` (`DECLARED_SINK_PATTERNS`)
- Modify (gerekirse): `tests/test_codelaw_kor_nokta_v214.py` donmuş taban
- Test: `tests/test_quote_capture_v465.py` (B + D bölümleri)

**Interfaces:**
- Consumes: `quotecapture.aktif()`, `quotecapture.get()`, `.istenen_abonelik()`, `.abonelik_degisti()`, `.q_geldi(m)`, `.snapshot()`.
- Produces: soket üzerinden `{"action":"subscribe","quotes":[...]}` / `{"action":"unsubscribe","quotes":[...]}`; sağlıkta `"quote_capture": {...}`; `quotecapture.get()._baglanti_ok` bayrağı (mark_alive/kopuşta).

- [ ] **Step 1: Kırmızı çiviler (B/D)**:

```python
from meridian import marketstream as mk
from tests.test_marketstream_v84 import FakeWS   # ithal: sahte soket TEK kaynak (kopyalanmaz)

class KuyrukluWS(FakeWS):
    """Eşlik görevi test edilebilsin diye çerçeveler asyncio kuyruğundan gelir; test aralara olay sokar."""
    def __init__(self):
        super().__init__([]); self.kuyruk = asyncio.Queue()
    def __aiter__(self):
        async def _gen():
            while True:
                f = await self.kuyruk.get()
                if f is None: return
                yield f
        return _gen()

@pytest.fixture(autouse=True)
def _sifirla():
    mk._LISTENER = None; mk._TASK = None; mk.STATE = None; qc._KAYIT = None
    yield
    mk._LISTENER = None; mk._TASK = None; mk.STATE = None; qc._KAYIT = None

def test_B1_bayrak_KAPALI_bit_ozdes_abonelik_yalniz_bars(sandbox_state, monkeypatch):
    monkeypatch.setenv(qc.AKTIF_ENV, "0")
    lis = mk.MarketStreamListener(); ws = FakeWS([json.dumps({"T": "q", "S": "AAPL", "bp": 1, "ap": 1.1})])
    monkeypatch.setattr(mk.hotstate, "ingest_bars", lambda b: 0)
    asyncio.run(lis.session(ws, lambda: None))
    assert all("quotes" not in json.loads(s) for s in ws.sent)
    assert lis.snapshot()["quote_capture"] == {"aktif": False}

def test_B2_bayrak_ACIK_new_olayi_subscribe_quotes_gonderir_sonra_unsubscribe(kayit, monkeypatch):
    k, d, saat = kayit
    monkeypatch.setattr(qc, "get", lambda: k)
    monkeypatch.setattr(mk.hotstate, "ingest_bars", lambda b: 0)
    lis = mk.MarketStreamListener(); ws = KuyrukluWS()
    async def senaryo():
        gorev = asyncio.ensure_future(lis.session(ws, lambda: None))
        await ws.kuyruk.put(json.dumps({"T": "success", "msg": "authenticated"}))
        await asyncio.sleep(0.05)
        k.olay("new", {"client_order_id": "P-1", "symbol": "AAPL", "side": "buy", "status": "new"})
        await asyncio.sleep(0.05)
        await ws.kuyruk.put(json.dumps([{"T": "q", "S": "AAPL", "bp": 1.0, "ap": 1.1, "bs": 1, "as": 1, "t": "2026-09-14T13:45:01.000Z"}]))
        await asyncio.sleep(0.05)
        k.olay("canceled", {"client_order_id": "P-1", "symbol": "AAPL", "status": "canceled"})
        await asyncio.sleep(0.05)
        await ws.kuyruk.put(None); await gorev
    asyncio.run(senaryo())
    gond = [json.loads(s) for s in ws.sent]
    assert {"action": "subscribe", "quotes": ["AAPL"]} in gond
    assert {"action": "unsubscribe", "quotes": ["AAPL"]} in gond
    assert gond.index({"action": "subscribe", "quotes": ["AAPL"]}) > 1, "auth + bars aboneliğinden SONRA"
    assert _satirlar(d, "2026-09-14.jsonl") and k.snapshot()["son_q_at"]

def test_B3_q_cercevesi_hotstate_e_GITMEZ(kayit, monkeypatch):
    k, d, saat = kayit
    monkeypatch.setattr(qc, "get", lambda: k)
    got = []
    monkeypatch.setattr(mk.hotstate, "ingest_bars", lambda b: (got.append(b), 0)[1])
    lis = mk.MarketStreamListener()
    ws = FakeWS([json.dumps([{"T": "q", "S": "AAPL", "bp": 1, "ap": 1.1, "t": "2026-09-14T13:45:01Z"},
                             {"T": "b", "S": "AAPL", "o": 1, "h": 1, "l": 1, "c": 1, "t": "2026-09-14T13:45:00Z"}])])
    asyncio.run(lis.session(ws, lambda: None))
    assert got == [{"AAPL": {"o": 1, "h": 1, "l": 1, "c": 1, "v": 0, "vw": None, "n": None, "t": "2026-09-14T13:45:00Z"}}]

def test_B4_subscription_mesaji_quotes_sayisini_sagliga_yazar(kayit, monkeypatch):
    k, d, saat = kayit
    monkeypatch.setattr(qc, "get", lambda: k); monkeypatch.setattr(mk.hotstate, "ingest_bars", lambda b: 0)
    lis = mk.MarketStreamListener()
    ws = FakeWS([json.dumps([{"T": "subscription", "bars": ["AAPL"], "quotes": ["AAPL", "MSFT"]}])])
    asyncio.run(lis.session(ws, lambda: None))
    assert lis.snapshot()["quote_capture"]["soket_abone_n"] == 2

def test_B5_health_hic_kosmamis_quote_capture_aktif_false():
    assert mk.health()["quote_capture"] == {"aktif": False}

def test_D1_marketstream_yapisal_sinir_korunur():
    import inspect
    src = inspect.getsource(mk)
    for f in ("write_json", "write_jsonl", "append_jsonl", "write_text", "open("):
        assert f not in src

def test_D2_codelaw_desen_beyani_var():
    from meridian import codelaw
    k = [a for a in codelaw.DECLARED_SINK_PATTERNS if "edg085" in a]
    assert len(k) == 1 and {"sinif", "gerekce", "sinanamaz"} <= set(codelaw.DECLARED_SINK_PATTERNS[k[0]])
```

- [ ] **Step 2: Kırmızı gör** — B2/B4/B5/D2 kırmızı (B1/B3/D1 bugün de geçer; onlar davranış-koruma çivileridir ve mutasyon adımında ısırdıkları gösterilir).

- [ ] **Step 3: Uygula**:
  - `session()`: auth + bars gönderiminden sonra
    ```python
    eslik = None
    if quotecapture.aktif():
        eslik = asyncio.ensure_future(self._q_abonelik(ws))
    try:
        async for raw in ws: ...
    finally:
        if eslik is not None:
            eslik.cancel()
    ```
  - `_q_abonelik(ws)`: `k = quotecapture.get(); guncel: set[str] = set()`; döngü: `istenen = set(k.istenen_abonelik())`; `ekle = sorted(istenen - guncel)`, `cikar = sorted(guncel - istenen)`; boş değilse `await ws.send(json.dumps({"action":"subscribe","quotes": ekle}))` / `unsubscribe`; `guncel = istenen`; `self.state.q_abone_n = len(guncel)`; sonra `ev = k.abonelik_degisti(); ev.clear()` ve `await asyncio.wait_for(ev.wait(), timeout=30)` (`asyncio.TimeoutError` → periyodik uzlaştırma, sessiz-yutma işaretli gerekçe: zaman aşımı beklenen yoldur, uzlaştırma turudur). `self._stop.is_set()` → çık. `ws.send` istisnası → `obs.warn("marketstream_q_abonelik_dustu", error=...)` ve çık (oturum zaten kopuyor; `run_stream` yeniden bağlar ve yeni oturum yeni eşlik görevi kurar; `guncel` sıfırdan başlar — soket değiştiği için doğru).
  - Mesaj döngüsü: `elif T == "q": if quotecapture.aktif(): quotecapture.get().q_geldi(m)`; `T == "subscription"` → `self.state.q_soket_abone_n = len(m.get("quotes") or [])`.
  - `mark_alive` sarmalı: `quotecapture.get()._baglanti_ok = True` (aktifse); `run_stream` kopuş yolunda ayarlanamaz (ortak sürücü) → `snapshot()` içinde `alive` False iken quotecapture'a `_baglanti_ok=False` yaz (dolum işaretinde `baglanti_yok` için yeterli: dolum anında `alive` bayrağı okunur — `quotecapture.get().baglanti_kaynagi = lambda: self._alive`; implementer en basit doğru yolu seçer ve raporda söyler).
  - `snapshot()`: `"quote_capture": ({**k.snapshot(), "soket_abone_n": self.state.q_soket_abone_n} if aktif else {"aktif": False})`; `health()` hiç-koşmamış dalı `"quote_capture": {"aktif": False}`.
  - Docstring: "abonelik YALNIZ bars" cümlesi → "abonelik `bars` (+ bayrakla, pencere-süreli `quotes` — quotecapture; `q` mrd:price/mrd:bars'a ASLA yazılmaz, ayrı dosyaya gider)"; "diske hiçbir şey yazmaz" → "bu modül diske yazmaz; `q` yolu quotecapture'a devreder (o yazar, kayıt dizini state/ dışı)".
  - `codelaw.DECLARED_SINK_PATTERNS["edg085 kayit/<gün>.jsonl + ham_<gün>.jsonl"]` = `{"sinif": "dis_okuyucu_arastirma", "gerekce": "... yazan quotecapture (MERIDIAN_EDG085_KAYIT_DIZIN, state/ DIŞI); okuyucu research/olcumler/edg085_icra_ani_quote/rapor.py (Rol-1 salt-okur, statik graf motor dışını görmez); kart EDG-2026-085 penceresi 20 seans; pilot bitince dosya yazımı bayrakla KAPANIR (kill#8) ...", "sinanamaz": "okuyucu motor dışı bir araçtır; declared_claims çağrı analizi onu göremez — DEVİR ŞARTI: kart hükmü inince bayrak kapatılır ve bu satır kartın hüküm kaydına atıfla KALIR ya da kaldırılır (Rol-1)"}`. Anahtarın `_joined_glob` ile eşleşme kuralını ÖLÇ (bararchive emsali `intraday_bars/*.jsonl` anahtarı nasıl türetiliyor — `grep -n "_joined_glob" meridian/codelaw.py`) ve anahtarı o kurala göre yaz; eşleşmeyen anahtar `orphan_patterns` ihlalidir (v214/v59 kırmızı yapar — bu da doğru davranıştır, yanlış anahtar sessiz kalmaz).

- [ ] **Step 4: Yeşil** — v465 tamamı + `tests/test_marketstream_v84.py` + `tests/test_api_marketstream_wiring_v84.py` + `tests/test_codelaw_v59.py` + `tests/test_codelaw_kor_nokta_v214.py` (taban değişirse güncelle + gerekçe) + `tests/test_hotstate_bars_v84.py`.

- [ ] **Step 5: Mutasyon** — (a) `T == "q"` dalını sil → B2 kırmızı (satır yazılmaz); (b) `quotecapture.aktif()` kapısını `True`'ya sabitle → B1 kırmızı; (c) `q`yu da `batch`e sok → B3 kırmızı; (d) codelaw beyanını sil → D2 kırmızı.

- [ ] **Step 6: Commit** — `git add meridian/marketstream.py meridian/codelaw.py tests/test_quote_capture_v465.py [tests/test_codelaw_kor_nokta_v214.py] && git commit -m "marketstream: bayrakla quotes aboneliği (tek soket, eşlik görevi) + q→quotecapture; codelaw desen beyanı (v465 B/D)"`

---

### Task 3: mirror_stream kancası

**Files:**
- Modify: `meridian/mirror_stream.py` (`OrderStateMachine.apply`)
- Test: `tests/test_quote_capture_v465.py` (C bölümü)

**Interfaces:**
- Consumes: `quotecapture.aktif()`, `quotecapture.get().olay(event, order)`.
- Produces: her trade_updates olayı (mükerrer/bayat süzgecinden GEÇENLER) quotecapture'a iletilir; mükerrer olay iletilmez (mirror'ın v68 tekrar yasası korunur).

- [ ] **Step 1: Kırmızı çiviler (C)**:

```python
from meridian import mirror_stream as ms

def test_C1_apply_olayi_quotecapture_a_iletir(kayit, monkeypatch, sandbox_state):
    k, d, saat = kayit
    monkeypatch.setattr(qc, "get", lambda: k)
    sm = ms.OrderStateMachine()          # sınıf adını ÖLÇ (grep -n "^class " meridian/mirror_stream.py)
    sm.apply("new", {"client_order_id": "P-1", "symbol": "AAPL", "side": "buy", "status": "new", "filled_qty": "0"})
    assert "AAPL" in k.istenen_abonelik()

def test_C2_mukerrer_olay_ILETILMEZ(kayit, monkeypatch, sandbox_state):
    k, d, saat = kayit
    monkeypatch.setattr(qc, "get", lambda: k)
    sayac = []
    monkeypatch.setattr(k, "olay", lambda e, o: sayac.append(e))
    sm = ms.OrderStateMachine()
    o = {"client_order_id": "P-1", "symbol": "AAPL", "side": "buy", "status": "new", "filled_qty": "0"}
    sm.apply("new", o); sm.apply("new", dict(o))
    assert sayac == ["new"]

def test_C3_bayrak_KAPALI_kanca_erken_doner(monkeypatch, sandbox_state):
    monkeypatch.setenv(qc.AKTIF_ENV, "0"); qc._KAYIT = None
    cagri = []
    monkeypatch.setattr(qc, "get", lambda: (cagri.append(1), None)[1])
    ms.OrderStateMachine().apply("new", {"client_order_id": "P-1", "symbol": "AAPL", "status": "new"})
    assert cagri == [], "bayrak kapalıyken quotecapture.get() bile çağrılmamalı"
```

- [ ] **Step 2: Kırmızı gör.**
- [ ] **Step 3: Uygula** — `apply` içinde `self._persist()` ve kilit bloğu bittikten sonra, `lvl` hesabından ÖNCE:
  ```python
  if quotecapture.aktif():          # EDG-085: icra-anı quote penceresi (bayrak kapalıyken sıfır maliyet)
      quotecapture.get().olay(event, order)
  ```
  Mükerrer/bayat `return` dalları kancadan ÖNCE olduğu için iletilmez. İthalat `from . import quotecapture` modül üstünde; döngüsel import ölçülür (`quotecapture` → `mirror_stream.PENDING` ithal ediyorsa döngü OLUR → kümeleri `quotecapture`'a taşı, `mirror_stream` oradan ithal etsin; ya da `quotecapture` içinde geç ithal). Raporda hangisi seçildi, neden.
- [ ] **Step 4: Yeşil** — v465 C + `tests/test_mirror_stream_audit_v33.py` + `tests/test_mirror_health_v68.py` + `tests/test_mirror_endpoint_v72.py`.
- [ ] **Step 5: Mutasyon** — kancayı sil → C1 kırmızı; kancayı `return`'lerin ÜSTÜNE taşı → C2 kırmızı.
- [ ] **Step 6: Commit** — `git commit -m "mirror_stream: trade_updates olayı → quotecapture kancası (v465 C)"`

---

### Task 4: rapor aracı — `research/olcumler/edg085_icra_ani_quote/rapor.py`

**Files:**
- Create: `research/olcumler/edg085_icra_ani_quote/rapor.py`
- Create: `research/olcumler/edg085_icra_ani_quote/README.md` (koşum reçetesi; A1'de ssh salt-okur)
- Test: `tests/test_edg085_rapor_v466.py`

**Interfaces:**
- Consumes: kayıt dizini (`<gün>.jsonl`, `ham_<gün>.jsonl`), `entry_execution.jsonl` (E2: `plan_id, ticker, ts, fill, karar`), `meridian.db` `trades` (`plan_id`, `entry`, `extra_json.alpaca_fill_price`, `extra_json.dolum_ts`; sqlite3 salt-okur `?mode=ro`), `state/bars_intraday/<gün>.jsonl` (`ticker, t, o, h, l, c` — şemayı `barsarchive.py` başlığından ÖLÇ), `taban.jsonl` (`cpu_kaynak=="cgroup"` satırları), kart eşikleri (SABİT olarak karttan AYNEN: 0.30 · 0.95 · 50 MB · 5 pp · 50 ms · n 30/10 seans).
- Produces: `sonuc_<bitis>.json` + `rapor_<bitis>.md` (`--cikti-dizin`); çıkış 0 rapor yazıldı / 2 PK düştü (sayı yayılmaz) / 1 hata.

**KOMUT SATIRI sözleşmesi** (`ops/` yasası: `main()` değil, argv):
```
python -m research.olcumler.edg085_icra_ani_quote.rapor --kayit-dizin D --state-dizin S --baslangic 2026-09-21 --bitis 2026-10-17
    [--taban T.jsonl] [--pilot-taban P.jsonl] [--cikti-dizin C] [--pk-sentetik] [--tick 0.01]
```

- [ ] **Step 1: Kırmızı çiviler** — `tests/test_edg085_rapor_v466.py`: sahte kayıt (3 gün, 4 dolum: 1 bant-içi, 1 bant-dışı, 1 quote'suz `sembol_sessiz`, 1 bracket çıkışı), sahte E2 + sqlite `trades` (şema: `storage._COLS` adlarını ÖLÇ ve yalnız gereken kolonlarla küçük tablo kur), sahte `bars_intraday` (PK-3 için pencere dakikası barı), sahte taban (cgroup satırları) ve pilot taban:
  - R1 dolum satırları: `n_dolum=4`, `kayip_orani=0.25` (1/4), neden dağılımı `{"sembol_sessiz":1}`.
  - R2 bant-içi: payda quote'lu dolumlar (3), `bant_ici_oran=2/3` (±1 tick), yön-farkındalı yakınlık tanı sütunu (long→ask farkı bps) dolu.
  - R3 PK-1 sentetik (`--pk-sentetik`): araç kendi ürettiği sabit desenle kayıp 0 / bant-içi 1.0 / pencere dışı 0 → `pk1: "gecti"`; mutasyonla (pencere sınırı bozulunca) `kaldi` ve çıkış 2.
  - R4 PK-3 bar çaprazı: pencere içi min(ask)/max(bid) aynı dakikanın `[l,h]` bandında → `gecti`; bar dışına çıkarılınca `kaldi`.
  - R5 fizibilite: disk = kayıt+ham bayt / seans; cpu delta = medyan(pilot cgroup) − medyan(taban cgroup); healthz p95 delta; eski (cpu_kaynak'sız) taban satırları ELENİR ve sayısı raporda; `cpu_taban_n_gecerli` alanı.
  - R6 örneklem kapısı: `n_dolum < 30 ∨ seans < 10` → `hukum: None` + `neden`, betimleyici sayılar yine yazılır.
  - R7 eşlenemeyen dolum (E2'de olmayan coid) `eslenemeyen` listesinde ADIYLA; sessiz düşmez.
  - R8 salt-okur: state dizinine yazmadığı ölçülür (dizin ağacı önce/sonra).
  - R9 `sonuc.json` alanları: `pencere`, `n_dolum`, `n_seans`, `kayip_orani`, `kayip_nedenleri`, `bant_ici_oran`, `bant_ici_n`, `tani_yon_farkindali_bps` (medyan + p90), `tani_sembol_saat` (açılış 13:30–14:00Z ayrı), `disk_mb_gun`, `cpu_delta_pp`, `healthz_p95_delta_ms`, `pk`: `{sentetik, bar_capraz, gercek: "elle — Rol-1"}`, `esikler` (karttan), `hukum` (`None` ya da `{kayip: gecti|kaldi, tutarlilik: gecti|kaldi, fizibilite: gecti|kaldi}`), `uretim_utc`, `girdi_sha256` (kayıt dosyaları).
- [ ] **Step 2: Kırmızı gör.**
- [ ] **Step 3: Uygula** — saf Python (json/sqlite3/statistics), DuckDB gerekmez; bootstrap yok (kart bant-içi oran + kayıp oranı için CI istemiyor; EDG-069'dan farklı). Tick: `--tick` varsayılan 0.01 (fiyat ≥1 USD; alt-dolar tick 0.0001 — sembol fiyatı <1 ise otomatik).
- [ ] **Step 4: Yeşil** — v466 + `tests/test_ops_komut_satiri_*` sınıfı çiviler research/ altını kapsıyorsa (ÖLÇ: `grep -rn "research/olcumler" tests/*.py | head`).
- [ ] **Step 5: Mutasyon** — ±1 tick payını kaldır → R2 kırmızı; eşlenemeyen dolumu sessizce düşür → R7 kırmızı; eski taban satırlarını elemeyi kaldır → R5 kırmızı.
- [ ] **Step 6: Commit** — `git commit -m "EDG-085 rapor aracı: dolum başına satır, K ölçüleri, PK-1/PK-3, fizibilite deltası (v466)"`

---

### Task 5: dağıtım artefaktı + kart notu (Rol-1 ile birlikte)

**Files:**
- Create: `deploy/oracle-a1/meridian.service.d/55-edg085-quote.conf`
- Modify: `research/olcumler/edg085_icra_ani_quote/README.md` (pilot açma reçetesi: drop-in'de `MERIDIAN_QUOTE_CAPTURE=1` → A0 rolü `site.yml` → `systemctl restart meridian` → `/api/diagnostics` `marketstream.quote_capture.aktif=true` doğrulaması; kapatma tersi)

- [ ] **Step 1:** drop-in:
  ```ini
  # 55-edg085-quote.conf — EDG-2026-085 Senaryo-A icra-anı quote kaydı (pilot bayrağı; kart adim_0_kaydi_2026_09_13).
  # VARSAYILAN KAPALI: kod 2026-09-14 dağıtımıyla iner, pilot en erken 2026-09-21 (CPU tabanı 5 seans) — Rol-1 açar.
  # Kayıt dizini /opt/veri (repo/state DIŞI; dagit --delete'ten korunur; kill#4). Dizin yoksa quotecapture kendisi kurar.
  [Service]
  Environment=MERIDIAN_QUOTE_CAPTURE=0
  Environment=MERIDIAN_EDG085_KAYIT_DIZIN=/opt/veri/olcum/edg085/kayit
  ```
- [ ] **Step 2:** `tests/test_ansible_*` / `tests/test_dropin_*` sınıfı çiviler drop-in listesini sayıyorsa (ÖLÇ: `grep -rln "meridian.service.d" tests/`) güncelle.
- [ ] **Step 3: Commit** — `git commit -m "EDG-085: meridian drop-in (pilot bayrağı KAPALI + kayıt dizini) + README reçetesi"`

---

## Rol-1 kapanışı (plan dışı, implementer YAPMAZ)
Tek Sonnet inceleme (task reviewer + dal sonu) → merge → tam suite (`-n 4`, arka plan, üçlü hüküm) → push → dağıtım 2026-09-14 akşam 20:05Z sonrası (bayrak KAPALI) → `/api/diagnostics` `quote_capture.aktif=false` doğrulaması → kart notu → 2026-09-21 pilot açılışı (5 geçerli CPU taban seansı şartıyla; eksikse ertelenir ve karta yazılır).

## Self-review (Rol-1, 2026-09-13)
- Kapsam: kartın olcum_plani 7 maddesi → T1 (pencere/satır), T4 (kayıp/tutarlılık/disk/CPU/tanı); kill#2 (T2 tek soket), kill#3 (T1 işaret satırı + T4 R7), kill#4 (T1 dizin sözleşmesi + A13), kill#5 (rapor 'IEX temsiliyeti' satırı: hüküm metnine karttan aynen), kill#7 (T4 çıkış 2), kill#8 (README kapatma reçetesi). ADIM-0 (4) ham defter T1.
- Yer tutucu taraması: sınıf adı `OrderStateMachine` ve `store.STATE_DIR` ÖLÇ notuyla işaretli — implementer ölçer; başka TBD yok.
- Tip tutarlılığı: `olay(event, order)`, `q_geldi(m)`, `istenen_abonelik()`, `abonelik_degisti()`, `snapshot()` adları T1→T2→T3'te aynı.

## Tur-2 (2026-09-13, inceleme sonrası Rol-1 kararları)
- Kayıt dosya adları `edg085_<gün>.jsonl` / `edg085_ham_<gün>.jsonl` (codelaw anahtarı `*/edg085_*.jsonl`; kart dosya adını sabitlemez — plan kararı).
- `quotecapture._dizin_env`: göreli değer → `quote_capture_dizin_goreli` uyarısı + yazım devre dışı (kill#4 çalışma-anı savunması).
- `_baglanti_ok` varsayılanı False; `baglanti(bool)` metodu; ilk `mark_alive`e kadar quote'suz dolum `baglanti_yok`.
- Eşlik görevi iptali `await asyncio.gather(eslik, return_exceptions=True)` ile beklenir.
- Kabul edilen kalıntılar (DÜŞÜK): `q_soket_abone_n` bayraktan bağımsız sayılır; tırnaklı env değerinde artık tırnak (notify, ayrı kalem); `kapsam.txt` biçimi (scratch).
