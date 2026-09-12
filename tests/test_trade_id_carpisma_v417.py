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

EK RULING (TSK-180, 2026-09-12) — D2'NİN YARIM KALAN YARISI: D2 sayacı yalnız BELLEKTE
yükseltiyordu. `_load_broker`ın üretimdeki TEK çağıranı `loop.daily_cycle`dır ve o, seans zaten
işlenmişse yüklemeden hemen sonra `{"status": "noop"}` ile ERKEN DÖNER — tur-sonu `_save_broker`
o tick'te hiç koşmaz. Sonuç canlıda ölçüldü: 09-08 15:44Z'den 09-12'ye kadar her ~5 dk AYNI
uyarı (`last_id`=901, defter azamisi T00909). Hüküm: yükseltme ANINDA `loop._last_id_kalicila`
ile kalıcı yazılır (aynı `store.update_json`/`file_lock(PORTFOLIO)` kapısı, YALNIZ `last_id`
alanı) ve uyarı `kalici_yazildi` hükmünü taşır.

BU DOSYA ALTI DURUMU ÇİVİLER + BİR AST TARİPWIRE:
  (1) D1 — kapanışta üretilen id defterde varsa: T00097'YE DEVAM EDİLMEZ, defter maksimumu+1
      (T00887 gibi) alınır + warn.
  (2) D2 — `_load_broker`de `last_id` defter maksimumunun altındaysa yükseltilir + warn.
  (3) Çarpışma YOKSA (sayaç zaten defterden ileride) HİÇBİR uyarı basılmaz, sayaç normal ilerler
      — hem yazım hem yükleme yolunda.
  (4) AST TRİPWIRE: `meridian/` içinde trades'i (ya da başka bir satır listesini) bracket-
      subscript `{t["id"]: t for t in ...}` biçiminde anahtarlayan kod YOK (bugün 0 — bu test
      0'ı KORUR; `meridian.topviews` içindeki yerel `plan_by_id` sözlüğü `.get("id")` kullanır, bu ŞEKİL DEĞİL, dokunulmaz).
  (5) D5 — TSK-180: yükseltme DİSKE iner (`kalici_yazildi: True`) ve kitabın `last_id` DIŞINDAKİ
      hiçbir alanına (yabancı `sermaye_resetleri` dahil) dokunulmaz.
  (6) D6 — TSK-180 VAKANIN KENDİSİ: ikinci yükleme SESSİZ — "her tick yeniden uyar" döngüsü biter.

MUTASYON (bu oturumda ELLE doğrulandı, kalıcı test DEĞİL — CLAUDE.md §6 "çivi yeşili kanıt
değildir"): `loop._persist_trade` içindeki `if any(r.get("id") == trade.get("id") ...)` bloğu
geçici olarak `if False and ...` yapılınca `test_D1_kapanista_carpisma_defter_maksimumuna_siçrar`
KIRMIZI oldu (id `T00096` olarak kaldı, defterde ikinci bir `T00096` yazıldı); yama geri
alınıp `meridian/__pycache__/loop.*.pyc` silindikten sonra tekrar YEŞİL doğrulandı.
MUTASYON (TSK-180, 2026-09-12, ELLE): (a) `_last_id_kalicila` içindeki `store.update_json(...)`
çağrısı `pass` ile değiştirilince D5 (`KeyError`/disk 901'de kaldı) VE D6 (`assert 2 == 1` —
ikinci uyarı, canlının tam semptomu) KIRMIZI oldu; (b) `_yama` içine `doc["cash"] = 0.0`
eklenince D5'in dar-yazım çivisi "dar yazım `cash` alanına DOKUNMAMALIYDI" ile KIRMIZI oldu.
Her iki yama YEDEK KOPYADAN geri alındı (sha256 eşit) ve `__pycache__` silinip yeniden YEŞİL
doğrulandı.

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


# =================================================================================================
# (5-6) TSK-180 — YÜKSELTİLEN SAYAÇ KALICI YAZILIR (uyarı her tick tekrarlamaz)
# =================================================================================================
# ÖLÇÜM (A1, 2026-09-12): 09-08 15:44Z'den beri her ~5 dk AYNI `trade_id_carpismasi` uyarısı
# basılıyordu — DB `portfolio.last_id` = 901, defterin gerçek azamisi T00909 (S5 yeniden
# tohumlaması). ÇAĞIRAN ZİNCİRİ ölçüldü: `_load_broker`ın ÜRETİMDEKİ TEK çağıranı
# `loop.daily_cycle`dır (`meridian/run.py`, `meridian/sprint_run.py`, `meridian/scheduler.py`
# onu çağırır); `daily_cycle` yüklemeden hemen sonra `meta["last_date"] == dstr` ise
# `{"status": "noop"}` ile ERKEN DÖNER ve tur-sonu yazımı `loop._save_broker` O TİCK'TE HİÇ
# KOŞMAZ. Yani D2 yükseltmesi yalnız BELLEKTE yaşıyor, disk 901'de kalıyor, bir sonraki tick
# aynı uyarıyı yeniden basıyordu (Yasa 4 gürültüsü: tekrar eden uyarı GERÇEK çarpışmayı gizler).
#
# HÜKÜM: yükseltme gerçekleştiği anda sayaç TEK yerde — `loop._last_id_kalicila` —
# `_save_broker` ile AYNI store kapısından (`store.update_json` → `file_lock(PORTFOLIO)`)
# kalıcı yazılır ve YALNIZ `last_id` alanına dokunulur. `_save_broker`ın kendisi burada
# ÇAĞRILAMAZ (ölçülmüş engel): yükseltme anında `b.positions` HENÜZ DOLDURULMAMIŞTIR ve
# `_save_broker` sahiplendiği 15 alanı yazdığı için kitabın açık pozisyonlarını BOŞ sözlükle
# ezerdi — dar yazım bir tercih değil, yapısal zorunluluk.
def _pf_defteri_geride(last_id: int) -> dict:
    """Canlının ölçülen şekli: kitap `last_id`de donmuş, defterde daha büyük T-numarası var.
    `sermaye_resetleri` KASITLI olarak eklenir — dar yazımın yabancı anahtarlara dokunmadığı
    (2026-08-04 vakasının sınıfı) aynı çivide ölçülür."""
    return {"cash": 100_000.0, "realized_pnl": 12.5, "last_id": last_id,
            "positions": {"AAA": {"plan_id": "P1", "ticker": "AAA", "side": "long",
                                  "entry": 100.0, "stop": 95.0, "trail_stop": 95.0,
                                  "target": 115.0, "qty": 10, "r_per_share": 5.0,
                                  "risk_dollars": 50.0, "size_r": 1.0,
                                  "ts_open": "2026-09-01"}},
            "armed": [], "pending_exits": {}, "last_date": "2026-09-12",
            "day_start_equity": 100_000.0, loop.MIRROR_EXIT_KEY: {},
            "sermaye_resetleri": [{"amount": 1.0, "date": "2026-08-01"}]}


def test_D5_yukseltilen_sayac_KALICI_yazilir_ve_kitap_kalanina_dokunmaz(sandbox_state):
    store.append_jsonl(ledgerstamp.LEDGER, _seed_satir("T00909", "SEED", "2026-09-02"))
    store.write_json(loop.PORTFOLIO, _pf_defteri_geride(901))

    b, _meta = loop._load_broker()

    assert b._id == 909, "ön koşul: D2 yükseltmesi BELLEKTE oldu"
    uyari = _uyarilar()
    assert len(uyari) == 1, "sessiz yutma YOK — Yasa 4"
    assert uyari[0]["kalici_yazildi"] is True, (
        "uyarı KALICILIK hükmünü taşımalı: 'yükselttim' ile 'yükselttim ve yazdım' aynı satırda "
        "ayırt edilemezse dört gün boyunca kimse farkı göremez")

    disk = store.read_json(loop.PORTFOLIO, {})
    assert disk["last_id"] == 909, "yükseltme DİSKE indi — aksi halde her tick yeniden uyarır"
    # DAR YAZIM: `last_id` DIŞINDA hiçbir alan değişmedi (sahiplenilen de, yabancı da).
    beklenen = _pf_defteri_geride(909)
    for alan in ("cash", "realized_pnl", "positions", "armed", "pending_exits", "last_date",
                 "day_start_equity", "sermaye_resetleri"):
        assert disk[alan] == beklenen[alan], f"dar yazım `{alan}` alanına DOKUNMAMALIYDI"


def test_D6_ikinci_yukleme_sessiz_her_tick_uyarisi_biter(sandbox_state):
    """VAKANIN KENDİSİ. `daily_cycle`ın noop dalı `_save_broker`ı hiç çağırmadığı için ikinci
    tick birinciyle AYNI defteri okur: kalıcılık olmazsa uyarı SONSUZA KADAR tekrarlar."""
    store.append_jsonl(ledgerstamp.LEDGER, _seed_satir("T00909", "SEED", "2026-09-02"))
    store.write_json(loop.PORTFOLIO, _pf_defteri_geride(901))

    b1, _ = loop._load_broker()                 # tick 1 — yükseltme + kalıcı yazım
    assert b1._id == 909
    assert len(_uyarilar()) == 1

    b2, _ = loop._load_broker()                 # tick 2 — AYNI defter, `_save_broker` koşmadı
    assert b2._id == 909, "sayaç diskten 909 olarak geldi"
    assert len(_uyarilar()) == 1, (
        "İKİNCİ uyarı basıldı — yükseltme kalıcı DEĞİL; canlıda bu, 09-08'den beri her ~5 dk "
        "tekrarlayan `trade_id_carpismasi` gürültüsünün ta kendisiydi")
