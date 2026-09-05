"""test_trade_id_carpisma_v417.py — TSK-150(a), 2026-09-05: trades `id` çarpışmasına İLERİ
YÖNLÜ koruma.

KEŞİF (A1 salt-okunur, 2026-09-05): canlı `state/trades.jsonl` 901 satırda 16 çift ÇARPIŞAN
`id` taşıyor — tohum (seq 92–117, 2023 tarihli) ile canlı (seq 886–901, 2026-08-07…09-02)
aynı `T%05d` etiketini paylaşıyor. KÖK: `broker.PaperBroker` sınıfının `_id` sayacı sayacı kapanışta
`f"T{self._id:05d}"` üretir; `loop._load_broker` bunu `portfolio.json["last_id"]`den yükler;
tohum 95→885 işleme GENİŞLETİLİRKEN (tam `run.replay_seed()` yoluyla DEĞİL) `last_id` 95'te
KALDI — canlı döngü T00096'dan devam edip zaten yazılmış seed id'leriyle çarpıştı.
`storage.py::_COLS[TRADES]` beyanı: gerçek anahtar `seq`dir, `id` bir İNSAN ETİKETİDİR (UNIQUE
kısıtı YOK) — bu yüzden ÇARPIŞMA sayısal zarar üretmedi (tüketiciler trades'i id ile
anahtarlamıyor), ama insan-okur etiketler (recompute sapan raporu, ledgerstamp örnekleri)
belirsizleşti. 16 mevcut çiftin yeniden numaralanması OPERATÖR kararıdır — BU DİLİM onları
DOKUNMAZ, yalnız BUNDAN SONRAKİ çarpışmaları engeller.

RULING (Rol-1, TSK-150 brief) İKİ KAPI, TEK KAYNAK (`loop._max_trade_num`):
  D1 — `loop._persist_trade`: YAZIM ANI çarpışma reddi. Üretilen `trade["id"]` defterde ZATEN
       varsa sayaç defterin GERÇEK maksimumunun bir üstüne sıçrar, `PaperBroker` örneğinin `_id` sayacı (verilmişse)
       aynı değere yükseltilir (sonraki kapanışlar tekrar çarpışmasın) ve `obs.warn(
       "trade_id_carpismasi", eski=..., yeni=..., sebep="last_id sayacı defterin gerisinde")`
       basılır — sessiz değil (Yasa 4).
  D2 — `loop._load_broker`: YÜKLEME ANI sayaç düzeltmesi. `last_id` defterin GERÇEK
       maksimumundan KÜÇÜKSE (kökün TAM eşleşmesi: genişleyen tohum ama donmuş `last_id`)
       yükseltilir + AYNI warn. Sayaç defterden İLERİDEYSE (normal durum) DOKUNULMAZ.

BU DOSYA DÖRT DURUMU ÇİVİLER + BİR AST TARİPWIRE:
  (1) D1 — kapanışta üretilen id defterde varsa: T00097'YE DEVAM EDİLMEZ, defter maksimumu+1
      (T00887 gibi) alınır + warn.
  (2) D2 — `_load_broker`de `last_id` defter maksimumunun altındaysa yükseltilir + warn.
  (3) Çarpışma YOKSA (sayaç zaten defterden ileride) HİÇBİR uyarı basılmaz, sayaç normal ilerler
      — hem yazım hem yükleme yolunda.
  (4) AST TRİPWIRE: `meridian/` içinde trades'i (ya da başka bir satır listesini) bracket-
      subscript `{t["id"]: t for t in ...}` biçiminde anahtarlayan kod YOK (bugün 0 — bu test
      0'ı KORUR; `meridian.topviews` içindeki yerel `plan_by_id` sözlüğü `.get("id")` kullanır, bu ŞEKİL DEĞİL, dokunulmaz).

MUTASYON (bu oturumda ELLE doğrulandı, kalıcı test DEĞİL — CLAUDE.md §6 "çivi yeşili kanıt
değildir"): `loop._persist_trade` içindeki `if any(r.get("id") == trade.get("id") ...)` bloğu
geçici olarak `if False and ...` yapılınca `test_D1_kapanista_carpisma_defter_maksimumuna_siçrar`
KIRMIZI oldu (id `T00096` olarak kaldı, defterde ikinci bir `T00096` yazıldı); yama geri
alınıp `meridian/__pycache__/loop.*.pyc` silindikten sonra tekrar YEŞİL doğrulandı.

HİÇBİR TEST CANLI STATE'E YAZMAZ: hepsi `sandbox_state` üzerinden koşar (D4 hariç — o saf statik
kaynak taraması, hiçbir I/O yapmaz).
"""
from __future__ import annotations

import ast
import pathlib

from meridian import config, ledgerstamp, loop, store
from meridian.broker import PaperBroker

MERIDIAN_DIR = pathlib.Path(config.__file__).resolve().parent
REPO = MERIDIAN_DIR.parent

CARPISMA_OLAYI = "trade_id_carpismasi"


def _uyarilar() -> list[dict]:
    return [e for e in store.read_jsonl("events.jsonl") if e.get("event") == CARPISMA_OLAYI]


def _plan(tid="P1", ticker="AAA", trigger=100.0, stop=95.0, target=115.0, size_r=1.0) -> dict:
    return {"id": tid, "ticker": ticker, "entry_trigger": trigger, "stop": stop,
            "profit_target": target, "size_r": size_r}


def _seed_satir(tid: str, ticker: str, ts_close: str) -> dict:
    """Defterde ZATEN duran (tohum ya da eski canlı) bir satırın minimal şekli — yalnız `id`
    çarpışma/maksimum hesabı için gereken alanları taşır, dedup anahtarıyla (plan_id|ticker,
    ts_close, exit_reason, exit) test edilen YENİ kapanışla KASITLI ÇAKIŞMAZ."""
    return {"id": tid, "ticker": ticker, "ts_close": ts_close, "exit_reason": "stop", "exit": 50.0}


def _acik_pozisyon_kapat(broker_id: int, ts_open="2026-08-07", ts_close="2026-08-10") -> tuple:
    """Sayacı `broker_id`ye sabitlenmiş bir broker açar, TEK pozisyon doldurur ve kapatır —
    dönen `(broker, row)` `close_position`in KENDİ ürettiği id ile (sayaç+1) test edilebilir."""
    b = PaperBroker(equity=100_000, slippage_bps=0, commission_per_share=0.0)
    b._id = broker_id
    b.fill_entry(_plan(), next_open=100.0, ts=ts_open, equity=100_000)
    row = b.close_position("AAA", raw_exit=110.0, reason="target", ts=ts_close)
    return b, row


# =================================================================================================
# (1) D1 — YAZIM ANI: kapanışta üretilen id defterde varsa, defter maksimumu+1'e sıçrar
# =================================================================================================
def test_D1_kapanista_carpisma_defter_maksimumuna_siçrar(sandbox_state):
    # Defter ZATEN T00096 (çarpışacak) ve T00886 (GERÇEK maksimum) taşıyor — KEŞİF'teki şekli
    # taklit eder: sayaç geride, ama defterin en büyük numarası çarpışan id'den ÇOK daha yüksek.
    store.append_jsonl(ledgerstamp.LEDGER, _seed_satir("T00096", "SEED1", "2023-01-05"))
    store.append_jsonl(ledgerstamp.LEDGER, _seed_satir("T00886", "SEED2", "2026-08-06"))

    b, row = _acik_pozisyon_kapat(broker_id=95)
    assert row["id"] == "T00096", "ön koşul: sayaç düzeltmeden ÖNCE üretilen id ZATEN çarpışıyor"

    loop._persist_trade(row, broker=b)

    assert row["id"] == "T00887", "T00097'ye DEVAM EDİLMEDİ — defter maksimumu (886) + 1"
    assert b._id == 887, "broker sayacı ileri alınmalı, yoksa BİR SONRAKİ kapanış tekrar çarpışır"

    yazili_idler = [r["id"] for r in store.read_jsonl(ledgerstamp.LEDGER)]
    assert yazili_idler.count("T00887") == 1
    assert "T00097" not in yazili_idler, "çarpışan aday id defterde YOK olmalı"

    uyari = _uyarilar()
    assert len(uyari) == 1, "sessiz yutma YOK — Yasa 4"
    assert uyari[0]["eski"] == "T00096" and uyari[0]["yeni"] == "T00887"
    assert uyari[0]["sebep"] == "last_id sayacı defterin gerisinde"


# =================================================================================================
# (2) D2 — YÜKLEME ANI: `last_id` defter maksimumunun altındaysa yükseltilir
# =================================================================================================
def test_D2_load_broker_sayaci_defter_maksimumuna_yukseltir(sandbox_state):
    store.append_jsonl(ledgerstamp.LEDGER, _seed_satir("T00885", "SEED", "2026-08-06"))
    pf = {"cash": 100_000.0, "realized_pnl": 0.0, "last_id": 95, "positions": {}, "armed": [],
          "pending_exits": {}, "last_date": "2026-08-06", "day_start_equity": 100_000.0,
          loop.MIRROR_EXIT_KEY: {}}
    store.write_json(loop.PORTFOLIO, pf)

    b, meta = loop._load_broker()

    assert b._id == 885, "last_id (95) defter maksimumuna (885) YÜKSELTİLDİ"
    uyari = _uyarilar()
    assert len(uyari) == 1
    assert uyari[0]["eski"] == "T00095" and uyari[0]["yeni"] == "T00885"
    assert uyari[0]["sebep"] == "last_id sayacı defterin gerisinde"


# =================================================================================================
# (3) Çarpışma YOKSA: hiçbir uyarı basılmaz, sayaç NORMAL ilerler (yazım + yükleme)
# =================================================================================================
def test_D3_carpisma_yoksa_sessiz_ve_sayac_dogal_ilerler(sandbox_state):
    # (a) YAZIM: sayaç zaten defterdeki en büyük numaranın (50) ÇOK ilerisinde (200) — kendi
    # doğal id'sini (T00201) korur.
    store.append_jsonl(ledgerstamp.LEDGER, _seed_satir("T00050", "ZZZ", "2023-01-05"))
    b, row = _acik_pozisyon_kapat(broker_id=200)
    assert row["id"] == "T00201"
    loop._persist_trade(row, broker=b)
    assert row["id"] == "T00201", "çarpışma yok — id DEĞİŞMEZ"
    assert b._id == 201
    assert _uyarilar() == [], "çarpışma yokken warn basılmamalı"

    # (b) YÜKLEME: `last_id` (300) defterin GERÇEK maksimumundan (201, (a)'da yazılan) İLERİDE —
    # `_load_broker` dokunmaz, warn basmaz.
    pf = {"cash": 100_000.0, "realized_pnl": 0.0, "last_id": 300, "positions": {}, "armed": [],
          "pending_exits": {}, "last_date": "2026-08-06", "day_start_equity": 100_000.0,
          loop.MIRROR_EXIT_KEY: {}}
    store.write_json(loop.PORTFOLIO, pf)
    b2, _meta2 = loop._load_broker()
    assert b2._id == 300, "sayaç defterden ileride — DOKUNULMAZ"
    assert _uyarilar() == []


# =================================================================================================
# (4) AST TRİPWIRE — trades (ya da başka bir satır listesi) bracket-subscript `id` ile
#     anahtarlanmıyor: bugün 0, bu test 0'ı korur.
# =================================================================================================
def _py_kaynaklari():
    """meridian/ altındaki her üretim modülü: (mutlak yol, AST)."""
    for p in sorted(MERIDIAN_DIR.rglob("*.py")):
        src = p.read_text(errors="ignore")
        yield p, ast.parse(src, filename=str(p))


def _id_ile_anahtarlanan_dictcomp(tree: ast.AST) -> list[ast.DictComp]:
    """`{X["id"]: X for X in ...}` ŞEKLİNDEKİ dict-comprehension'ları bulur — bir satır
    listesini id ile anahtarlamanın TEHLİKELİ biçimi budur: `id` gerçek anahtar DEĞİLDİR
    (`storage.py::_COLS[TRADES]` beyanı, gerçek anahtar `seq`) ve bugünkü 16 çarpışan çiftten
    biri bu şekilde okunursa dict aynı anahtarı SESSİZCE üzerine yazar. `meridian.topviews` içindeki yerel `plan_by_id` sözlüğü
    gibi meşru kullanımlar `.get("id")` ÇAĞRISI kullanır — bu ayrı bir AST şeklidir (`ast.Call`,
    `ast.Subscript` DEĞİL) ve burada KASITLI olarak eşleşmez."""
    hits = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.DictComp) or not node.generators:
            continue
        target = node.generators[0].target
        key, val = node.key, node.value
        if not isinstance(target, ast.Name):
            continue
        if not (isinstance(key, ast.Subscript) and isinstance(key.value, ast.Name)
                and key.value.id == target.id):
            continue
        sl = key.slice
        if not (isinstance(sl, ast.Constant) and sl.value == "id"):
            continue
        if not (isinstance(val, ast.Name) and val.id == target.id):
            continue
        hits.append(node)
    return hits


def test_D4_ast_tripwire_trades_id_ile_anahtarlanmiyor():
    ihlaller = []
    for yol, tree in _py_kaynaklari():
        for node in _id_ile_anahtarlanan_dictcomp(tree):
            ihlaller.append(f"{yol.relative_to(REPO)}:{node.lineno}")
    assert ihlaller == [], (
        f"bir satır listesini bracket-subscript {{X['id']: X}} ile anahtarlayan kod bulundu: "
        f"{ihlaller} — id gerçek anahtar DEĞİLDİR (storage.py::_COLS[TRADES]), 16 çarpışan çift "
        f"böyle bir okumada SESSİZCE tek satıra düşer")
