"""test_dalga2_motor_v222.py — DALGA-2 AJAN A (motor): E2 iç-motor totolojisi (K4) + E2 kilitsiz
oku-değiştir-yaz (K8) + SB-1 boyut makbuzu (K5).

Kaynak triyaj: docs/SABAH-TRIYAJI-2026-08-09.md kalem 4/8/5; SB-1 tasarımı
docs/BAYAT-SERMAYE-KOK-2026-08-07.md §8 (B1).

KALEM 4 — İÇ-MOTOR TOTOLOJİSİ. İç motorun "dolum vs resmî açılış" bps'i, dolum fiyatı açılıştan
  SABİT slippage ile türetildiği için (broker.fill_entry: base_fill = açılış×(1+slip)), tanımı
  gereği slippage_bps sabitini geri üretir — bir ÖLÇÜM değil totolojidir. Yazar (loop) satıra
  None + beyan bırakır; özet (analytics) o beyanı surface eder ve aynanın "tavan gevşetilebilir"
  HÜKMÜNÜ n_dolan < BAND_MIN_N iken SUSTURUR (UYDURMA YASAĞI: az örnekten hüküm uydurulmaz).

KALEM 8 — E2 KİLİTSİZ RMW. `_entry_exec_write` (append), `_entry_exec_trim` ve
  `_patch_entry_slippage` (oku-değiştir-yaz) aynı `file_lock(ENTRY_LEDGER)` altına alındı;
  os.replace ATOMİKLİK verir ama oku-değiştir-yaz'ı serialize etmez → kilit kayıp-güncellemeyi
  kapatır. Kontrol testi kilitsiz pencerenin GERÇEK olduğunu, fix testi kilidin kapattığını gösterir.

KALEM 5 — SB-1 BOYUT MAKBUZU. `mirror_submit_armed` plan başına 5 alanlı makbuz yazar
  (eq_kaynak · eq_now · peak · size_mult · kitap_rev); `_save_broker`ın 14. sahiplenilen anahtarı
  (`size_law`) olarak restart'ı atlatır.

Hiçbir test canlı state'e yazmaz (`sandbox_state`).
"""
from __future__ import annotations

import ast
import inspect
import textwrap
import threading
import time

import pytest

from meridian import analytics as an
from meridian import broker as BR
from meridian import config, health, loop, store
from meridian.adapters import alpaca
from meridian.broker import PaperBroker, derisk_mult


@pytest.fixture(autouse=True)
def _saat_sifirla():
    """Pencere-yasası (EXE-009) testleri saati donduruyor — sızıntıya karşı her testte sıfırla."""
    yield
    from meridian import barclock as _bc
    _bc.reset_clock()


# =================================================================================================
# KALEM 4 — İÇ-MOTOR TOTOLOJİSİ (None + beyan; ayna hükmü n<20'de susar)
# =================================================================================================
def test_k4_ic_motor_acilis_bps_TOTOLOJIKtir(sandbox_state):
    """DAVRANIŞSAL KANIT: iç motorun dolumu açılıştan sabit slippage ile türer, yani açılışa göre
    bps ölçmek slippage_bps sabitini GERİ ÜRETİR. `slippage_bps=5` iken bps = 5,0 — bu bir ölçüm
    değil totolojidir (canlıda ~5,04; fark modellenmiş likidite etkisinden)."""
    b = PaperBroker(equity=100_000.0, slippage_bps=5.0, commission_per_share=0.0)
    plan = {"id": "P-1", "ticker": "AAA", "entry_trigger": 100.0, "stop": 95.0,
            "profit_target": 115.0, "size_r": 1.0}
    pos = b.fill_entry(plan, next_open=100.0, ts="2026-08-01", equity=100_000.0)   # adv=None → sabit slip
    assert pos is not None
    # açılışa (100.0) göre dolumun bps'i = slippage_bps. Tam da bu sayı deftere yazılırdı (totoloji).
    assert BR.bps_delta(pos.entry, 100.0) == pytest.approx(5.0, abs=1e-6)


def test_k4_ic_fill_yazimi_None_beyan_ve_limit_bacagi_kalir():
    """AST ÇİVİSİ: iç-motor 'fill' E2 yazımı `fill_vs_resmi_acilis_bps`i SABİT None basar (totolojik
    bps HESAPLANIP yazılmaz), yanında beyan taşır, ve `fill_vs_limit_bps`i (limit-bacağı, E1 grid'in
    ölçtüğü ayrı bacak) KORUR."""
    tree = ast.parse(inspect.getsource(loop))
    hedef = None
    for node in ast.walk(tree):
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                and node.func.id == "_entry_exec_write" and node.args
                and isinstance(node.args[0], ast.Dict)):
            kv = {k.value: v for k, v in zip(node.args[0].keys, node.args[0].values)
                  if isinstance(k, ast.Constant)}
            if isinstance(kv.get("karar"), ast.Constant) and kv["karar"].value == "fill":
                hedef = kv
    assert hedef is not None, "iç-motor 'fill' E2 yazımı bulunamadı"
    assert isinstance(hedef["fill_vs_resmi_acilis_bps"], ast.Constant) \
        and hedef["fill_vs_resmi_acilis_bps"].value is None, \
        "iç-motor açılış bps'i hâlâ hesaplanıp yazılıyor — totoloji kapanmadı"
    assert "fill_vs_resmi_acilis_beyan" in hedef, "None yazıldı ama beyan yok (UYDURMA YASAĞI: neden şart)"
    assert isinstance(hedef["fill_vs_limit_bps"], ast.Call), \
        "limit-bacağı bps'i de düşürülmüş — E1 grid'inin ölçtüğü bacak kaybolmamalı"


def test_k4_beyan_sabiti_olculemedi_der():
    beyan = loop.IC_ACILIS_TOTOLOJI_BEYAN
    assert isinstance(beyan, str) and len(beyan) >= 20
    assert "ÖLÇÜLEMEDİ" in beyan and "slippage" in beyan.lower()


def test_k4_ozet_ic_bps_None_ve_beyani_surface_eder(sandbox_state):
    """Özet: iç motorun açılış bps'i None'lardan oluşur → ort None + n_olculemeyen (0 basmaz), ve
    satırdaki beyan surface edilir (analytics loop'u import etmeden, satırdan okuyarak)."""
    for i in range(3):
        store.append_jsonl(loop.ENTRY_LEDGER, {
            "date": "2026-08-09", "plan_id": f"P{i}", "ticker": "A", "motor": "ic", "karar": "fill",
            "fill": 100.4, "fill_vs_resmi_acilis_bps": None,
            "fill_vs_resmi_acilis_beyan": loop.IC_ACILIS_TOTOLOJI_BEYAN,
            "fill_vs_limit_bps": -9.9})
    s = an.entry_execution_summary(days=None)
    icb = s["ic_motor"]["fill_vs_resmi_acilis_bps"]
    assert icb["ort"] is None and icb["n"] == 0 and icb["n_olculemeyen"] == 3, \
        "totolojik bps 0 olarak toplandı — ölçülemeyen None düşmedi"
    assert s["ic_motor"]["fill_vs_resmi_acilis_beyan"] == loop.IC_ACILIS_TOTOLOJI_BEYAN


def test_k4_ayna_yorumu_n_altinda_hukmu_SUSTURUR(sandbox_state):
    """n_dolan < BAND_MIN_N: 'gevşetilebilir' HÜKMÜ basılmaz (canlı vaka n=4'te basıyordu)."""
    for i in range(4):                       # < BAND_MIN_N (20)
        store.append_jsonl(loop.ENTRY_LEDGER, {
            "date": "2026-08-09", "plan_id": f"A{i}", "ticker": "A", "motor": "ayna",
            "karar": "submitted", "fill": 100.4, "fill_vs_limit_bps": -271.0})
    yorum = an.entry_execution_summary(days=None)["ayna"]["dolum"]["yorum"]
    assert "gevşet" not in yorum, "n<20'de 'gevşetilebilir' hükmü hâlâ basılıyor (UYDURMA YASAĞI)"
    assert "HÜKÜM YOK" in yorum and str(an.BAND_MIN_N) in yorum


def test_k4_ayna_yorumu_esikte_hukmu_verir(sandbox_state):
    """n_dolan >= BAND_MIN_N: yeterli örneklem → hüküm cümlesi geri gelir."""
    for i in range(an.BAND_MIN_N):
        store.append_jsonl(loop.ENTRY_LEDGER, {
            "date": "2026-08-09", "plan_id": f"A{i}", "ticker": "A", "motor": "ayna",
            "karar": "submitted", "fill": 100.4, "fill_vs_limit_bps": -30.0})
    yorum = an.entry_execution_summary(days=None)["ayna"]["dolum"]["yorum"]
    assert "gevşetilebilir" in yorum, "eşikte hüküm cümlesi verilmiyor"


# =================================================================================================
# KALEM 8 — E2 KİLİTSİZ OKU-DEĞİŞTİR-YAZ (file_lock ile kapatıldı)
# =================================================================================================
def _rmw_under_lock(func) -> bool:
    """func kaynağında read_jsonl VE write_jsonl, `with … file_lock(ENTRY_LEDGER)` bloğunun
    İÇİNDE mi? (kilit satırının VARLIĞI yetmez — RMW onun KAPSAMINDA olmalı)."""
    tree = ast.parse(textwrap.dedent(inspect.getsource(func)))
    for w in ast.walk(tree):
        if not isinstance(w, ast.With):
            continue
        kilitli = any(
            isinstance(it.context_expr, ast.Call)
            and isinstance(it.context_expr.func, ast.Attribute)
            and it.context_expr.func.attr == "file_lock"
            and any(isinstance(a, ast.Name) and a.id == "ENTRY_LEDGER"
                    for a in it.context_expr.args)
            for it in w.items)
        if not kilitli:
            continue
        calls = {n.func.attr for n in ast.walk(w)
                 if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)}
        if "read_jsonl" in calls and "write_jsonl" in calls:
            return True
    return False


def test_k8_patch_ve_trim_rmw_file_lock_altinda():
    assert _rmw_under_lock(loop._patch_entry_slippage), \
        "_patch_entry_slippage oku-değiştir-yaz'ı file_lock(ENTRY_LEDGER) kapsamında değil"
    assert _rmw_under_lock(loop._entry_exec_trim), \
        "_entry_exec_trim oku-değiştir-yaz'ı file_lock(ENTRY_LEDGER) kapsamında değil"


def test_k8_append_ve_yaniltici_atomik_yorumu():
    src_w = inspect.getsource(loop._entry_exec_write)
    assert "file_lock(ENTRY_LEDGER)" in src_w, "append aynı kilidi paylaşmıyor — RMW ile serialize olmaz"
    src_p = inspect.getsource(loop._patch_entry_slippage)
    assert "atomik (mkstemp + os.replace)" not in src_p, \
        "yanıltıcı 'atomik' yorumu duruyor — os.replace oku-değiştir-yaz'ı serialize ETMEZ"
    assert "serialize" in src_p.lower() or "kayıp-güncelleme" in src_p, \
        "farkın (atomiklik ≠ kayıp-güncelleme koruması) yazılı olması gerekiyor"


def test_k8_kilitsiz_rmw_kayip_update_KANITI(sandbox_state):
    """KONTROL (kırmızı sınıf, deterministik): kilitsiz oku-değiştir-yaz penceresi araya düşen bir
    append'i EZER. Kilidin kapattığı sınıfın GERÇEK olduğunu thread'siz gösterir."""
    assert not store.db_backed(loop.ENTRY_LEDGER), "defter DB arka ucunda — kontrol dosya dalına dair"
    store.append_jsonl(loop.ENTRY_LEDGER, {"id": "A", "motor": "ayna"})
    store.append_jsonl(loop.ENTRY_LEDGER, {"id": "B", "motor": "ayna"})
    rows = store.read_jsonl(loop.ENTRY_LEDGER)                            # 1) RMW okur → [A, B]
    store.append_jsonl(loop.ENTRY_LEDGER, {"id": "C", "motor": "ayna"})  # 2) araya append → disk [A,B,C]
    rows.append({"id": "B2", "motor": "ayna"})
    store.write_jsonl(loop.ENTRY_LEDGER, rows)                           # 3) bayat görünüm geri yazılır
    ids = [r.get("id") for r in store.read_jsonl(loop.ENTRY_LEDGER)]
    assert ids == ["A", "B", "B2"] and "C" not in ids, \
        "kilitsiz RMW C'yi kaybetmedi — kontrol geçersiz (kayıp-güncelleme sınıfı gösterilemedi)"


def test_k8_entry_exec_write_kilit_altinda_serialize_olur_ve_ezilmez(sandbox_state):
    """FIX (davranışsal): E2 kilidi tutulurken `_entry_exec_write` BLOKLAR; kilit sahibi bir
    oku-değiştir-yaz yaparken araya giremez, kilit bırakılınca yazımı defterin ÜSTÜNE ekler —
    ne kilit sahibinin RMW'si ne appender'ın satırı kaybolur."""
    store.append_jsonl(loop.ENTRY_LEDGER, {"id": "base", "motor": "ayna"})
    lk = store.file_lock(loop.ENTRY_LEDGER)
    lk.acquire()                                  # ana iplik kilidi tutar (RMW ortasını taklit)
    done = threading.Event()

    def _appender():
        loop._entry_exec_write({"id": "yeni", "motor": "ayna"})   # AYNI kilidi ister → bloklanır
        done.set()

    t = threading.Thread(target=_appender)
    t.start()
    try:
        time.sleep(0.2)
        ara = [r.get("id") for r in store.read_jsonl(loop.ENTRY_LEDGER)]
        assert "yeni" not in ara and not done.is_set(), \
            "append kilit tutulurken yazdı — serialize edilmedi"
        rows = store.read_jsonl(loop.ENTRY_LEDGER)          # kilit sahibinin RMW'si
        rows.append({"id": "patch", "motor": "ayna"})
        store.write_jsonl(loop.ENTRY_LEDGER, rows)          # reentrant: aynı kilit
    finally:
        lk.release()
    t.join(timeout=3.0)
    assert not t.is_alive() and done.is_set(), "kilit bırakıldıktan sonra appender tamamlanmadı"
    ids = {r.get("id") for r in store.read_jsonl(loop.ENTRY_LEDGER)}
    assert ids == {"base", "patch", "yeni"}, f"kayıp-güncelleme: {ids}"


def test_k8_patch_entry_slippage_hala_iki_bps_yazar(sandbox_state):
    """Regresyon: kilit sarımı DAVRANIŞI değiştirmez — patch yine iki bps yazar ve idempotenttir."""
    store.append_jsonl(loop.ENTRY_LEDGER, {
        "date": "2026-08-09", "plan_id": "P-1", "ticker": "AAA", "motor": "ayna",
        "entry_trigger": 100.0, "limit": 100.5, "karar": "submitted", "fill": None,
        "fill_vs_resmi_acilis_bps": None, "fill_vs_limit_bps": None})
    orders = {"P-1": {"status": "filled", "filled_avg_price": "100.40", "filled_qty": "50"}}
    rap = loop._patch_entry_slippage(orders, {"AAA": 100.0}, "2026-08-09")
    assert rap == {"eslesen": 1, "yazilan": 1, "acilis_yok": 0,
                   "kismi_tazelenen": 0}   # B5a (v234): kısmi-tazeleme sayacı sözleşmeye girdi
    row = store.read_jsonl(loop.ENTRY_LEDGER)[0]
    assert row["fill"] == 100.4 and row["fill_vs_resmi_acilis_bps"] == pytest.approx(40.0, abs=0.01)
    assert loop._patch_entry_slippage(orders, {"AAA": 100.0}, "2026-08-10")["yazilan"] == 0


# =================================================================================================
# KALEM 5 — SB-1 BOYUT MAKBUZU (5 alan; _save_broker'ın 14. anahtarı)
# =================================================================================================
@pytest.fixture
def ayna(sandbox_state, monkeypatch):
    """`alpaca_paper` arka ucu + sahte, hiçbir şey göndermeyen submit_plan.

    Saat pencere İÇİNE donar (EXE-009+K2): gönderim artık sabah tetik penceresine bağlı; bu
    dosyanın çivileri MAKBUZ mekaniğini ölçer, pencereyi değil — koşum saatinden bağımsız kalır."""
    from meridian import barclock as _bc
    import datetime as _dt
    _bc.set_clock(lambda: _dt.datetime(2026, 7, 23, 14, 0, tzinfo=_dt.timezone.utc))
    monkeypatch.setattr(config, "BROKER", "alpaca_paper")
    monkeypatch.setattr(alpaca, "paper_available", lambda: True)
    monkeypatch.setattr(alpaca, "account", lambda: {"equity": "100000"})
    monkeypatch.setattr(
        alpaca, "submit_plan",
        lambda pl, eq, size_mult=1.0, atr=None, ref_price=None:
        {"ok": True, "qty": 5, "law": {"limit": 10.1, "mode": "stop_limit", "tif": "gtc"}})
    yield sandbox_state
    _bc.reset_clock()


def test_k5_makbuz_bes_alan_eq_now_dali(ayna):
    meta = {"armed": [{"id": "P-1", "ticker": "T0", "entry_trigger": 10.0}],
            "peak_equity": 100_000.0, "entry_law": {"P-1": {"atr": 1.25, "ref_price": 9.5}}}
    out = loop.mirror_submit_armed(meta, "2026-08-02", eq_now=95_000.0, halted=False, source="loop")
    assert out["ok"] is True and out["submitted"] == 1
    mk = meta["size_law"]["P-1"]
    # ALTI ALAN (2026-08-22, Ö-53): `eq_ayna` BİLİNÇLİ eklendi. Makbuz bugüne dek yalnız KİTABIN
    # sermayesini yazıyordu, oysa `submit_plan`e AYNANIN tabanı (`acct["equity"]`) gidiyor — yani
    # aynanın FİİLEN boyutlandığı sayı hiç kayıtlı değildi ve yedi pozisyondaki adet sapması
    # kayıttan açıklanamıyordu. Tam-küme iddiası KORUNUYOR (alan sızması hâlâ kırar); genişletme
    # bu satırı bilerek değiştirmeyi gerektirdi — kapının amacı tam olarak bu.
    # YEDİ ALAN (2026-08-22, Ö-53/B). Makbuz ÜÇ tabanı da taşır: kitabınki · broker'ınki ·
    # FİİLEN KULLANILAN. Üçüncüsü olmadan guard'ın bağlayıp bağlamadığı kayıttan çıkarılamaz.
    # Tam-küme iddiası KORUNUYOR (alan sızması hâlâ kırar).
    assert set(mk) == {"eq_kaynak", "eq_now", "eq_broker", "eq_ayna",
                       "peak", "size_mult", "kitap_rev"}, f"makbuz 7 alanla yazılmadı: {sorted(mk)}"
    assert mk["eq_broker"] == 100_000.0, "eq_broker broker hesabının tabanını taşımıyor"
    # B: ayna KİTABIN tabanıyla boyutlanır. Fikstürde kitap (95.000) broker'dan (100.000) DÜŞÜK,
    # yani guard BAĞLAMAZ ve kullanılan taban kitabınkidir.
    assert mk["eq_ayna"] == 95_000.0 == mk["eq_now"], \
        "kitap tabanı broker'dan düşükken ayna yine de broker'ınkiyle boyutlanmış — B uygulanmamış"
    assert mk["eq_kaynak"] == "eq_now"
    assert mk["eq_now"] == 95_000.0 and mk["peak"] == 100_000.0
    assert mk["size_mult"] == round(derisk_mult(95_000.0, 100_000.0), 4)   # 0,6 — %5 düşüşün çarpanı
    assert isinstance(mk["kitap_rev"], int)


def test_k5_broker_tavani_BAGLAYINCA(ayna, monkeypatch):
    """GUARD (Ö-53/B): kitap equity'si broker'ınkini AŞARSA emir broker'ın parasını aşardı.
    O hâlde kullanılan taban BROKER'ınki olur ve makbuz bunu GÖSTERİR — `eq_ayna != eq_now`
    tam olarak "guard bağladı" demektir ve `ayna_taban` sapma sınıfı da yalnız o an konuşur.
    Ölçüldü (2026-08-22): kitap tabanı broker'ınkini +%6,5'e kadar aşabiliyor."""
    monkeypatch.setattr(alpaca, "account", lambda: {"equity": "90000"})   # broker DÜŞÜK
    meta = {"armed": [{"id": "P-G", "ticker": "T9", "entry_trigger": 10.0}],
            "peak_equity": 100_000.0}
    out = loop.mirror_submit_armed(meta, "2026-08-02", eq_now=95_000.0, halted=False)
    assert out["ok"] is True
    mk = meta["size_law"]["P-G"]
    assert mk["eq_now"] == 95_000.0 and mk["eq_broker"] == 90_000.0
    assert mk["eq_ayna"] == 90_000.0, \
        "kitap broker'dan YÜKSEKKEN tavan bağlamamış — emir broker'ın parasını aşardı"


def test_k5_makbuz_nabiz_dali(ayna):
    """eq_now geçilmezse nabızdan okunur ve makbuz `eq_kaynak="nabiz"` der (BAYAT-SERMAYE AMGN bacağı)."""
    health.write_heartbeat(equity=99_000.0, last_bar="2026-08-01")
    meta = {"armed": [{"id": "P-2", "ticker": "T1", "entry_trigger": 10.0}], "peak_equity": 100_000.0}
    out = loop.mirror_submit_armed(meta, "2026-08-02", halted=False)     # eq_now GEÇİLMEZ
    assert out["ok"] is True
    mk = meta["size_law"]["P-2"]
    assert mk["eq_kaynak"] == "nabiz" and mk["eq_now"] == 99_000.0


def test_k5_makbuz_reddedilen_planda_da_yazilir(sandbox_state, monkeypatch):
    """Boyut TABANI gönderim sonucundan bağımsız kanıttır: reddedilen planın da makbuzu yazılır."""
    from meridian import barclock as _bc
    import datetime as _dt
    _bc.set_clock(lambda: _dt.datetime(2026, 7, 23, 14, 0, tzinfo=_dt.timezone.utc))  # pencere içi (EXE-009)
    monkeypatch.setattr(config, "BROKER", "alpaca_paper")
    monkeypatch.setattr(alpaca, "paper_available", lambda: True)
    monkeypatch.setattr(alpaca, "account", lambda: {"equity": "100000"})
    monkeypatch.setattr(alpaca, "submit_plan",
                        lambda *a, **k: {"ok": False, "detail": "insufficient buying power",
                                         "reachable": True})
    meta = {"armed": [{"id": "P-R", "ticker": "TR", "entry_trigger": 10.0}], "peak_equity": 100_000.0}
    loop.mirror_submit_armed(meta, "2026-08-02", eq_now=100_000.0, halted=False)
    assert "P-R" in meta.get("size_law", {}), "reddedilen planın boyut makbuzu yazılmadı"


def test_k5_save_broker_size_law_14uncu_anahtar_restarti_atlatir(sandbox_state):
    """`size_law` `_save_broker`ın SAHİPLENİLEN alanıdır → portfolio.json'a yazılır ve restart'ı
    atlatır (entry_law/MIRROR_EXIT_KEY ile aynı desen)."""
    assert '"size_law": meta.get("size_law"' in inspect.getsource(loop._save_broker)
    b = PaperBroker(100_000.0, 5, 0.0)
    meta = {"size_law": {"P-1": {"eq_kaynak": "eq_now", "eq_now": 100_000.0, "peak": 100_000.0,
                                 "size_mult": 1.0, "kitap_rev": 3}}}
    loop._save_broker(b, meta)
    doc = store.read_json("portfolio.json", {})
    assert doc["size_law"]["P-1"]["size_mult"] == 1.0
    assert set(doc["size_law"]["P-1"]) == {"eq_kaynak", "eq_now", "peak", "size_mult", "kitap_rev"}


def test_k5_yabanci_anahtar_makbuz_yazilirken_de_korunur(sandbox_state):
    """SAHİPLİK KAPISI (2026-08-04 vakasının çivisi): size_law eklendi ama YABANCI anahtar
    (sermaye_resetleri) yerinde yaşamaya devam eder — 14. anahtar beyaz listeyi ezmez."""
    store.write_json("portfolio.json", {"sermaye_resetleri": [{"id": "SR-1", "delta": 5.0}]})
    b = PaperBroker(100_000.0, 5, 0.0)
    loop._save_broker(b, {"size_law": {"P-1": {"eq_kaynak": "nabiz", "eq_now": 1.0, "peak": 1.0,
                                               "size_mult": 1.0, "kitap_rev": 0}}})
    doc = store.read_json("portfolio.json", {})
    assert doc["sermaye_resetleri"] == [{"id": "SR-1", "delta": 5.0}], "yabancı beyan anahtarı silindi"
    assert "P-1" in doc["size_law"]
