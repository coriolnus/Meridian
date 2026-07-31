"""test_sadelestirme_v123.py — MİMARİ SADELEŞTİRME + KANIT-HIZI turu (2026-07-30).

Dört kalemin KİLİTLERİ:
  ① 4a gözlemi TÜM planları izler — ama yetki farkı (eod_armed) ve 4b gölge nüfusu DEĞİŞMEDİ
  ② 2.4 gölge-varyant portföyleri — kanun ÇAĞRILIR, ship yolu YOK, k_variants satırda
  ③ prescreen bileşik adaylar — doğrulama düğme düzeyinde, k_probes ADAY sayısı
  ④ redis/intraday kopukluk ekleri — NOGROUP onarımı, yalnız-yazılır katmanın kapanışı, ölü şema

CANLI STATE'E YAZAN TEST YOK: hepsi `sandbox_state` içinde ya da `write=False` ile koşar.
"""
import ast
import datetime as dt
import inspect
import pathlib

import pytest

from meridian import barclock as bc, barsarchive as ba, hotstate, intraday_cycle as ic, \
    loop, prescreen, shadow_variants as sv, store

ROOT = pathlib.Path(__file__).resolve().parent.parent
UTC = dt.timezone.utc
RTH = dt.datetime(2026, 7, 23, 14, 46, 30, tzinfo=UTC)      # 10:46:30 ET (RTH açık)


@pytest.fixture(autouse=True)
def _reset():
    ic._CONSUMER = None
    ic.reset_plans_cache()
    yield
    bc.reset_clock()
    ic._CONSUMER = None
    ic.reset_plans_cache()


def _bar(t, h, c):
    return {"t": t, "o": c, "h": h, "l": c, "c": c, "v": 100}


def _plan(tk, trig, pid=None, date="2026-07-22"):
    return {"id": pid or f"P-{date}-{tk}", "date": date, "ticker": tk, "entry_trigger": trig,
            "stop": trig * 0.95, "profit_target": trig * 1.1, "size_r": 1.0}


# ============================ ① 4a gözlemi TÜM planlara =========================================
def test_silahsiz_plan_da_izlenir_ve_karar_satiri_yazilir(sandbox_state, monkeypatch):
    """TURUN ASIL KAZANCI: silahlı plan YOK, açık pozisyon YOK — eski davranışta izlenen 0 ticker
    ve 0 satır olurdu (canlıda tam olarak bu vardı: 10 plan / 0 silahlı)."""
    bc.set_clock(lambda: RTH)
    store.write_json("portfolio.json", {"positions": {}, "armed": [], "last_date": "2026-07-22"})
    store.append_jsonl("trade_plans.jsonl", _plan("AAPL", 100.0))
    monkeypatch.setattr(ic.hotstate, "read_bars",
                        lambda tk, n: [_bar("2026-07-23T14:45:00Z", 101.0, 100.5)])
    ic.consumer().on_barfeed_event({"syms": "AAPL"})
    rows = store.read_jsonl("intraday_decisions.jsonl")
    assert len(rows) == 1, "silahsız plan izlenmedi — turun ① kalemi işlemiyor"
    r = rows[0]
    assert r["fired"] is True and r["entry_trigger"] == 100.0
    assert ic.consumer().watched == 1 and ic.consumer().watched_planned == 1


def test_eod_armed_ETIKETI_ANLAMINI_KORUR_ve_plan_source_ayirir(sandbox_state, monkeypatch):
    """YETKİ FARKI KAYBOLMADI: `eod_armed` HÂLÂ 'portfolio.json.armed içinde mi' demektir.
    Bu alanın anlamı kayarsa, defteri okuyan her ölçüm silahsız planları silahlı sanar."""
    bc.set_clock(lambda: RTH)
    store.write_json("portfolio.json", {"positions": {}, "armed": [_plan("MSFT", 50.0)],
                                        "last_date": "2026-07-22"})
    for p in (_plan("AAPL", 100.0), _plan("MSFT", 50.0)):
        store.append_jsonl("trade_plans.jsonl", p)
    monkeypatch.setattr(ic.hotstate, "read_bars",
                        lambda tk, n: [_bar("2026-07-23T14:45:00Z", 999.0, 998.0)])
    ic.consumer().on_barfeed_event({"syms": "AAPL,MSFT"})
    by = {r["ticker"]: r for r in store.read_jsonl("intraday_decisions.jsonl")}
    assert by["MSFT"]["eod_armed"] is True and by["MSFT"]["plan_source"] == "armed"
    assert by["AAPL"]["eod_armed"] is False and by["AAPL"]["plan_source"] == "planned"
    assert by["AAPL"]["plan_id"] == "P-2026-07-22-AAPL"
    # NÜFUS AYRIMI health()'te GÖRÜNÜR: api `decisions.fired` toplamını bölmeden okuyor; ayrım
    # üretici tarafında sayılmazsa panodaki sayı sessizce anlam değiştirirdi.
    h = ic.health()
    assert h["decisions_armed"] == 1 and h["decisions_planned"] == 1


def test_uc_damga_sozlesmesi_AYNEN_korunur(sandbox_state, monkeypatch):
    """3 DAMGA (decision_as_of / bar_t / close_ts) ve as_of >= close_ts denetlenebilirliği."""
    bc.set_clock(lambda: RTH)
    store.write_json("portfolio.json", {"positions": {}, "armed": [], "last_date": "2026-07-22"})
    store.append_jsonl("trade_plans.jsonl", _plan("AAPL", 100.0))
    monkeypatch.setattr(ic.hotstate, "read_bars",
                        lambda tk, n: [_bar("2026-07-23T14:45:00Z", 101.0, 100.5)])
    ic.consumer().on_barfeed_event({"syms": "AAPL"})
    r = store.read_jsonl("intraday_decisions.jsonl")[0]
    for alan in ("decision_as_of", "bar_t", "close_ts"):
        assert r[alan], f"3-damga sözleşmesi bozuldu: {alan} yok"
    assert dt.datetime.fromisoformat(r["decision_as_of"]) >= dt.datetime.fromisoformat(r["close_ts"])


def test_4b_golge_YALNIZ_silahli_planda_calisir(sandbox_state, monkeypatch):
    """Gölge nüfusu bilerek DARALTILDI: silahsız plan EOD'de hiç dolmaz → `vs_eod` eşleştirmesi
    her satırda unpaired'e düşer ve friksiyon ölçümü sulanırdı."""
    bc.set_clock(lambda: RTH)
    store.write_json("portfolio.json", {"positions": {}, "armed": [], "last_date": "2026-07-22"})
    store.append_jsonl("trade_plans.jsonl", _plan("AAPL", 100.0))
    monkeypatch.setattr(ic.hotstate, "read_bars",
                        lambda tk, n: [_bar("2026-07-23T14:45:00Z", 999.0, 998.0)])
    cagrildi = []
    from meridian import intraday_shadow
    monkeypatch.setattr(intraday_shadow, "record", lambda *a, **k: cagrildi.append(a) or {})
    ic.consumer().on_barfeed_event({"syms": "AAPL"})
    assert store.read_jsonl("intraday_decisions.jsonl")[0]["fired"] is True
    assert cagrildi == [], "gölge SİLAHSIZ planda çalıştı — vs_eod nüfusu kirlenir"


def test_plan_onbellegi_mtime_ile_TAZELENIR(sandbox_state, monkeypatch):
    """Önbellek anahtarı (tarih, mtime): EOD turu defteri tazelediğinde kendiliğinden düşer.
    Zaman aşımına dayanan bir önbellek, yeni planları bir pencere boyunca GÖRMEZDİ."""
    pf = {"positions": {}, "armed": [], "last_date": "2026-07-22"}
    store.write_json("portfolio.json", pf)
    store.append_jsonl("trade_plans.jsonl", _plan("AAPL", 100.0))
    c = ic.consumer()
    assert set(c._planned(pf)) == {"AAPL"}
    store.append_jsonl("trade_plans.jsonl", _plan("MSFT", 50.0))
    assert set(c._planned(pf)) == {"AAPL", "MSFT"}, "mtime değişti ama önbellek düşmedi"


def test_plan_defteri_yoksa_gozlem_ESKI_davranisina_duser(sandbox_state):
    """Fail-soft: plan defteri okunamazsa ölçüm DARALIR, DURMAZ (istisna sızmaz)."""
    pf = {"positions": {}, "armed": [], "last_date": "2026-07-22"}
    assert ic.consumer()._planned(pf) == {}
    assert ic.consumer()._planned({"positions": {}, "armed": []}) == {}   # last_date yok → çapa yok


# ============================ ② 2.4 gölge-varyant portföyleri ====================================
def test_varyantlar_TEK_SOZLUKTE_ve_bounds_ile_uyumlu():
    """Tanım tek yerde; her düğme bounds SÖZLEŞMESİNDE ve aralık içinde. Uydurma düğme adı sessizce
    'etkisiz varyant' olarak görünürdü — en sinsi hata sınıfı."""
    from meridian import config
    # 3-5. Üst sınır KEYFİ DEĞİL — her kol `k_variants` paydasını büyütür, yani diğerlerinin
    # çoklu-karşılaştırma cezasını artırır. Sınırı yükseltmek bilinçli bir karar olmalı, sessiz bir
    # birikim değil (2026-07-30'da tam bu gerekçeyle üç karar-özdeş kol ÇIKARILDI).
    assert 3 <= len(sv.VARIANTS) <= 5, "ROADMAP 2.4: 3-5 varyant (k_variants paydası bedellidir)"
    assert sv.validate_knobs(config.bounds()) == []
    assert sv.VARIANTS["V5"]["knobs"] == {}, "kontrol kolu olmadan 'fark' bir sayı değil izlenimdir"


def test_tanimsiz_dugme_SESSIZ_KALMAZ():
    bozuk = {"min_rvvol": {"min": 0, "max": 2}}          # yazım hatası: gerçek ad entry.min_rvol
    hatalar = sv.validate_knobs(bozuk)
    assert hatalar and all("hata" in h for h in hatalar)
    assert any("TANIMSIZ" in h["hata"] for h in hatalar)


def test_kanun_CAGRILIR_kopyalanmaz():
    """YAPISAL (AST): modül üretimin kapı/tarama fonksiyonlarını ÇAĞIRIR ve İKİNCİ bir kapı yasası
    yazmaz. Kopya bir kapı, defterin zamanla stratejiyi değil KENDİNİ ölçmesi demekti (4b dersi)."""
    src = (ROOT / "meridian" / "shadow_variants.py").read_text()
    for cagri in ("strategy.scan_all(", "guard.classify_gate(", "earnings.in_blackout(",
                  "derisk_mult(", "max_positions_at("):
        assert cagri in src, f"üretim fonksiyonu çağrılmıyor: {cagri}"
    # tarama dilimi reçetesi DIŞARIDAN gelir (tail_of) — burada yeniden yazılmamalı
    assert ".tail(" not in src, "tarama dilimi reçetesi kopyalanmış — pencere kayması riski"
    assert "_gate_eval" not in src, "kapı hükmü yeniden yazılmış"


def test_hicbir_YAZIM_yolu_yok_defter_haric():
    """SIFIR YETKİ (yapısal, AST): store yazım çağrılarının tek hedefi `LEDGER` sabitidir ve KODDA
    (belgede değil) hiçbir canlı defter adı geçmez. Metin taraması yerine AST: gerekçe yazan bir
    yorumun içindeki 'portfolio.json' bir yazım DEĞİLDİR ve testi düşürmemeli."""
    tree = ast.parse((ROOT / "meridian" / "shadow_variants.py").read_text())
    YAZIM = ("append_jsonl", "write_json", "write_jsonl", "merge_dated_jsonl",
             "update_json", "update_jsonl")
    hedefler = [n.args[0] for n in ast.walk(tree)
                if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                and n.func.attr in YAZIM and n.args]
    assert hedefler, "hiç yazım yok — defter nasıl doluyor?"
    for h in hedefler:
        assert isinstance(h, ast.Name) and h.id == "LEDGER", \
            f"yazım hedefi LEDGER değil: {ast.dump(h)[:60]}"
    # KODDAKİ dizeler (docstring/yorum hariç): canlı defter adı geçmemeli
    kod_dizeleri = {n.value for n in ast.walk(tree)
                    if isinstance(n, ast.Constant) and isinstance(n.value, str)}
    for d in kod_dizeleri:
        assert not d.endswith((".json", ".jsonl", ".yaml")) or d == sv.LEDGER, \
            f"kodda başka bir artefakt adı var: {d}"
    # ÇAĞRILAN AD listesi (yine AST): dolum/kalıcılık yolları hiç çağrılmamalı. Docstring bu adlardan
    # söz edebilir (etmeli — neden çağrılmadığını yazıyor); yasak olan ÇAĞRIDIR.
    cagrilan = {n.func.attr for n in ast.walk(tree)
                if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)}
    cagrilan |= {n.func.id for n in ast.walk(tree)
                 if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
    for yasak in ("fill_entry", "_save_broker", "write_heartbeat", "record"):
        assert yasak not in cagrilan, f"gölge katmanı canlı yolu çağırıyor: {yasak}"


def test_satir_k_variants_paydasini_ve_ayrismayi_TASIR(sandbox_state, monkeypatch):
    """`k_probes` kardeşi: 'en iyi varyant' seçimi ÇOKLU KARŞILAŞTIRMADIR; paydayı satıra yazmayan
    defter kazananın-lanetini görünmez kılar."""
    rows = _kosu(monkeypatch, write=False)
    assert len(rows) == len(sv.VARIANTS)
    for r in rows:
        assert r["k_variants"] == len(sv.VARIANTS)
        assert r["authority"] == "paper_only"
        for alan in ("only_variant", "only_live", "shared_n", "gates_applied", "gates_skipped",
                     "book_as_of", "decision_as_of", "flow_n", "verdicts"):
            assert alan in r, f"satırda {alan} yok"
    assert store.read_jsonl(sv.LEDGER) == [], "write=False iken deftere yazıldı"


def test_varyant_KARARI_AYRISABILIR_ve_kontrol_kolu_canliyla_ayni(sandbox_state, monkeypatch):
    """Ölçümün asıl iddiası: aynı akış + farklı düğme = FARKLI karar. Kontrol kolu (V5) canlı
    parametrelerin ta kendisidir; V1 (min_rvol 1.5) düşük-rvol adayı ELEMELİ."""
    rows = {r["variant"]: r for r in _kosu(monkeypatch, write=False, rvol=0.4)}
    assert rows["V5"]["signal_n"] == 1, "kontrol kolu adayı görmedi — kurgu bozuk"
    assert rows["V1"]["signal_n"] == 0, "min_rvol 1.5 rvol=0.4 adayını elemedi"
    assert rows["V4"]["signal_n"] == 0, "V4 takasının rvol tabanı işlemiyor"


def test_V_SETI_BUTUNLUGU_ve_payda_OTOMATIK(sandbox_state, monkeypatch):
    """ÇİVİ ①: set TAM OLARAK V1/V2/V4/V5'tir ve `k_variants` paydası ELLE DEĞİL `len(VARIANTS)`ten
    türer. V3/V6/V7 2026-07-30'da ÇIKARILDI (karar-özdeş kollardı); sabit bir sayaç olsaydı çıkarma
    paydayı küçültmez ve çoklu-karşılaştırma cezası sessizce FAZLA hesaplanmaya devam ederdi."""
    from meridian import ledgers
    assert set(sv.VARIANTS) == {"V1", "V2", "V4", "V5"}, \
        "V-seti değişti — çıkarılan kollar geri geldiyse gerekçe/çivi de güncellenmeli"
    rows = {r["variant"]: r for r in _kosu(monkeypatch, write=False)}
    assert set(rows) == {"V1", "V2", "V4", "V5"}
    for vid, r in rows.items():
        # PAYDA OTOMATİK: 4'e sabitlenmiş değil, tanımlı kol sayısından türer.
        assert r["k_variants"] == len(sv.VARIANTS) == 4
        # ALAN BÜTÜNLÜĞÜ: defter SÖZLEŞMESİNİN zorunlu alanları her kolda tam.
        for alan in ledgers.CONTRACTS["shadow_variants.jsonl"].required:
            assert alan in r, f"{vid} satırında zorunlu alan yok: {alan}"
    # Çıkarılan kolların ARTIĞI kalmamalı: satırda ölü bir ölçüm-sınırı alanı taşımak, sınırın
    # HÂLÂ geçerli olduğu izlenimi verirdi (taşıyıcısı olmayan şema alanı çürür).
    assert "v1_note" not in rows["V5"], "ölü v1_note alanı satırda kalmış"


def test_cikis_dugmeleri_v1_GIRIS_yolunda_GERCEKTEN_okunmaz():
    """ÇİVİ ②: ELEME GEREKÇESİNİ DOĞRULAR — iddia değil ölçüm. V3/V6/V7 "v1'de karar-özdeşti" diye
    çıkarıldı; bu YAPISAL bir iddiadır ve çürütülebilir olmalı. Biri `early_kill_pivot`i ya da
    `scale_out`u `scan_all`/`classify_gate` yoluna bağlarsa gerekçe DÜŞER ve kollar v1'de gerçekten
    ayrışmaya başlar — o gün bu test patlar ve eleme kararı yeniden gözden geçirilir."""
    def _okundugu_fonksiyonlar(dosya, dugme):
        tree = ast.parse((ROOT / "meridian" / dosya).read_text())
        return {fn.name for fn in ast.walk(tree)
                if isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef))
                for n in ast.walk(fn)
                if isinstance(n, ast.Constant) and n.value == dugme}

    def _cagiranlar(dosya, ad):
        tree = ast.parse((ROOT / "meridian" / dosya).read_text())
        return {fn.name for fn in ast.walk(tree)
                if isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef))
                for n in ast.walk(fn)
                if isinstance(n, ast.Call)
                and getattr(n.func, "id", getattr(n.func, "attr", None)) == ad}

    # early_kill_pivot: YALNIZ çıkış fonksiyonunda okunur, o da YALNIZ yaşam-döngüsünden çağrılır.
    assert _okundugu_fonksiyonlar("strategy.py", "exit.early_kill_pivot") == {"early_kill_pivot_exit"}
    assert _cagiranlar("strategy.py", "early_kill_pivot_exit") == {"manage_position"}
    # scale_out: giriş yolunun İKİ dosyasında da HİÇ geçmez (yalnız broker.scale_out = FILL ömrü).
    for dosya in ("strategy.py", "guard.py"):
        for dugme in ("exit.scale_out_frac", "exit.scale_out_r"):
            assert not _okundugu_fonksiyonlar(dosya, dugme), \
                f"{dugme} artık {dosya} yolunda okunuyor — ELEME GEREKÇESİ düştü, kararı gözden geçir"
    assert _okundugu_fonksiyonlar("broker.py", "exit.scale_out_frac") == {"scale_out"}
    # ...ve gölge katmanı bu düğmelerin hiçbirini KENDİ kararında okumuyor.
    for dugme in sv.LIFECYCLE_KNOBS_V2:
        assert not _okundugu_fonksiyonlar("shadow_variants.py", dugme)


def test_v2_YE_KADAR_CIKIS_DUGMELI_KOL_EKLENEMEZ():
    """ÇİVİ ③: KURAL — `LIFECYCLE_KNOBS_V2` düğmesi taşıyan kol v1 setine ALINAMAZ. Böyle bir kol
    kontrol koluyla karar-özdeş olur: defterine yazdığı ayrışma sıfırı bir ÖLÇÜM değil KURGUDUR ve
    'etkisi yok' diye okunmaya açıktır; üstelik `k_variants` paydasını bedavaya şişirir. Kural sözlü
    bir konvansiyon olarak bırakılmadı — ihlali BURADA patlar."""
    assert sv.LIFECYCLE_KNOBS_V2, "kısıt listesi boşalmış — kural sessizce etkisizleşti"
    for vid, spec in sv.VARIANTS.items():
        ihlal = set(spec["knobs"]) & sv.LIFECYCLE_KNOBS_V2
        assert not ihlal, (f"{vid} v2-öncesi yasak düğme taşıyor: {sorted(ihlal)} — bu kol v1'de "
                          "KARAR-ÖZDEŞ olur, ölçüm kazancı sıfır, payda bedeli gerçek")
    # ELEME GEREKÇESİ KAYNAKTA YAZILI KALMALI: gerekçesiz bir çıkarma, yarın sessizce geri alınır.
    src = (ROOT / "meridian" / "shadow_variants.py").read_text()
    assert "ÇIKARILDI 2026-07-30" in src, "eleme kaydı kaynaktan silinmiş"
    for kol in ("V3", "V6", "V7"):
        assert kol in src, f"{kol} çıkarıldı ama gerekçe kaydında adı geçmiyor"
    assert "KARAR-ÖZDEŞ" in src and "v2" in src, "elemenin NEDENİ kaynakta yazılı değil"
    # Ölü not makinesi geride bırakılmadı (taşıyıcısı yok; kalırsa "sınır hâlâ var" izlenimi verir).
    assert "V1_EXIT_KNOB_NOTE" not in src and '"note"' not in src


def test_tek_varyantin_arizasi_digerlerini_REHIN_ALMAZ(sandbox_state, monkeypatch):
    cagri = {"n": 0}

    def patlak(vid, spec, *a, **k):
        cagri["n"] += 1
        if vid == "V2":
            raise RuntimeError("kurgu arıza")
        return {"variant": vid, "label": spec["label"], "knobs": {}, "signal_n": 0,
                "would_arm_n": 0, "verdicts": {}, "would_arm": [], "detail": [],
                "detail_truncated": 0, "scan_failed": [], "scan_failed_n": 0}
    monkeypatch.setattr(sv, "_decide_variant", patlak)
    rows = _kosu(monkeypatch, write=False)
    assert cagri["n"] == len(sv.VARIANTS)
    assert len(rows) == len(sv.VARIANTS) - 1
    assert "V2" not in {r["variant"] for r in rows}


def test_bos_defter_SAHTE_bir_her_sey_yolunda_gostermez():
    metin = sv.render_summary([])
    assert "BOŞ" in metin and "shadow_variants" in metin
    assert sv.summarize([])["rows"] == 0


def test_ozet_CLI_tuketicisi_calisir(sandbox_state, capsys):
    """YASA 6: `--ozet` gerçek bir tüketicidir (defteri okur, derler, yazar)."""
    assert sv.main(["--varyantlar"]) == 0
    assert "k_variants=" in capsys.readouterr().out
    assert sv.main(["--ozet"]) == 0
    assert "BOŞ" in capsys.readouterr().out


def test_loop_kancasi_VAR_ve_korumali():
    """Kanca minimaldir, try/except + obs.warn ile sarılıdır ve P3'ün DIŞINDA durur."""
    src = inspect.getsource(loop.daily_cycle)
    assert "shadow_variants" in src, "loop'ta gölge-varyant kancası yok"
    i = src.index("shadow_variants as _sv")
    assert "try:" in src[max(0, i - 400):i], "kanca try ile sarılmamış"
    assert "shadow_variants_failed" in src, "arıza obs.warn ile görünür kılınmıyor"
    # kanca dilim reçetesini PAYLAŞIR (iki kopya değil)
    assert src.count("_scan_tail(") == 2 and "def _scan_tail" in inspect.getsource(loop)


def test_scan_tail_TEK_TANIM_ve_nedensel():
    src = inspect.getsource(loop._scan_tail)
    assert ".loc[:d]" in src and f".tail(SCAN_TAIL_BARS)" in src
    assert loop.SCAN_TAIL_BARS == 340, "tarama penceresi sessizce değişti"


def _kosu(monkeypatch, *, write=False, rvol=2.5):
    """Tek adaylı sahte akış — `scan_all` MONKEYPATCH'lenir (bar üretmeden kapı yolu sürülür).
    `min_rvol`/`min_volume_ratio` etkisi gerçek strategy filtresiyle taklit edilir ki varyantın
    düğmesi GERÇEKTEN okunsun."""
    from meridian import config

    class _Sig:
        ticker, setup, score = "AAPL", "breakout_vcp", 75
        entry_trigger, stop, profit_target, r_per_share, size_r = 100.0, 95.0, 112.5, 5.0, 1.0
        rvol20, mom_12_1, rmom = rvol, None, None

    def fake_scan_all(tail, params, rs, ticker="?"):
        floor = float(params.get("entry.min_rvol", 0.0) or 0.0)
        if floor > 0 and rvol < floor:
            return {}
        # stop çarpanı geometriyi değiştirir → V2 kolunda stop farkı görünür olsun
        s = _Sig()
        s.stop = 100.0 - float(params.get("stop_loss_atr_mult", 2.0)) * 2.5
        s.r_per_share = 100.0 - s.stop
        return {"breakout_vcp": s}

    monkeypatch.setattr(sv.strategy, "scan_all", fake_scan_all)
    monkeypatch.setattr(sv.earnings, "in_blackout", lambda t, d: False)
    monkeypatch.setattr(sv.earnings, "known", lambda t: True)
    goal = config.goal()
    return sv.record_cycle(
        "2026-07-28", ["AAPL"],
        tail_of=lambda t: None, rs_of=lambda t: 80, sector_of=lambda t: "Tech",
        max_corr_of=lambda t: 0.1,
        eff={"entry.min_rvol": 0.0, "stop_loss_atr_mult": 2.0, "exit.breakeven_r": 1.0,
             "exit.scale_out_frac": 0.0, "exit.scale_out_r": 2.0, "entry.min_volume_ratio": 1.5},
        regime={"regime": "trend_up", "exposure_budget_pct": 60}, goal=goal,
        limits=goal["limits"], bounds=config.bounds(), version=3,
        book={"positions": {}, "equity": 100000.0, "peak_equity": 100000.0},
        live_armed=[], write=write)


# ============================ ③ prescreen bileşik adaylar ========================================
@pytest.mark.parametrize("ham,beklenen", [
    ("a=1;b=2", [{"a": 1, "b": 2}]),
    ("a=1|b=2", [{"a": 1}, {"b": 2}]),
    ("stop_loss_atr_mult=3.0;exit.breakeven_r=0.0",
     [{"stop_loss_atr_mult": 3.0, "exit.breakeven_r": 0.0}]),
    (" a=1 ; b=true |", [{"a": 1, "b": True}]),
])
def test_bilesik_ayristirma(ham, beklenen):
    assert prescreen.parse_composite(ham) == beklenen


@pytest.mark.parametrize("bozuk", ["", "a", "a=1;b", "=1", "a=1;a=2", "|"])
def test_bicimsiz_bilesik_SESSIZCE_ATLANMAZ_patlar(bozuk):
    """Sessiz atlama: kullanıcı üç aday verdiğini sanır, ikisi ölçülür ve k_probes de düşer —
    hem eksik ölçüm hem gevşemiş çıta, ikisi de görünmeden."""
    with pytest.raises(ValueError):
        prescreen.parse_composite(bozuk)


def test_normalize_iki_bicimi_TEK_ic_bicime_indirir_ve_anahtar_deterministik():
    tek = prescreen._normalize([("a", 1)])
    assert tek == [{"key": "a", "knobs": {"a": 1}, "bilesik": False}]
    b1 = prescreen._normalize([{"b": 2, "a": 1}])[0]
    b2 = prescreen._normalize([{"a": 1, "b": 2}])[0]
    assert b1["key"] == b2["key"] == "a=1;b=2", "anahtar sıraya bağlı — aynı aday iki kez ölçülürdü"
    assert b1["bilesik"] is True


def test_bilesikte_DUGME_DUZEYI_bounds_reddi_ve_hangi_dugme(sandbox_state, tmp_path, monkeypatch):
    """Bileşik olmak bounds dışına çıkma ruhsatı değildir; hangi düğme yüzünden reddedildiği taşınır."""
    from meridian import config
    rapor = prescreen.run([{"entry.min_score": 80, "exit.breakeven_r": 99.0}],
                          tmp_path / "wd", config.STATE, log=lambda *a: None)
    assert rapor.get("hata") == "guard_hepsini_reddetti"
    red = rapor["reddedilen"][0]
    assert red["bilesik"] is True and red["yeni"] is None
    assert [d["knob"] for d in red["dugme_redleri"]] == ["exit.breakeven_r"]
    assert red["knobs"] == {"entry.min_score": 80, "exit.breakeven_r": 99.0}


def test_CLI_iki_bayraktan_en_az_biri_zorunlu_ve_ikisi_BIRLIKTE_mesru(monkeypatch):
    """`--candidates` artık zorunlu değil ama ikisi de yoksa ölçülecek şey YOKTUR → argparse hatası.
    İkisi birlikte verilirse TEK koşuda ölçülür (aynı incumbent, aynı k_probes paydası)."""
    with pytest.raises(SystemExit):
        prescreen.main(["--workdir", "/tmp/yok"])
    gorulen = {}

    def fake_run(a, w, l, resume=False):
        gorulen["adaylar"] = a
        return {}
    monkeypatch.setattr(prescreen, "run", fake_run)
    prescreen.main(["--workdir", "/tmp/yok", "--candidates", "a=1", "--composite", "b=2;c=3"])
    assert gorulen["adaylar"] == [("a", 1), {"b": 2, "c": 3}]


def test_bilesik_k_probes_ADAY_sayisidir_dugme_sayisi_degil():
    """Bir bileşik aday kapıya BİR yoklama gönderir. Düğme başına saymak cezayı sahte şişirirdi."""
    src = inspect.getsource(prescreen.run)
    assert "k_probes = len(gecerli)" in src
    assert "n_bilesik" in src, "rapor bileşik sayısını beyan etmiyor"


# ============================ ④ redis/intraday kopukluk ekleri ===================================
def test_NOGROUP_onarimi_grup_kaydini_duser_ve_SAYAR(sandbox_state):
    """TTL'li anahtarda grup ölümü: `_ensure_group` erken dönüyordu ve akış süreç yeniden
    başlatılana kadar arşivlenmiyordu. Onarım sessiz DEĞİL — sayaç + uyarı."""
    a = ba.BarsArchiver()
    a._groups.update({"mrd:bars:AAPL", "mrd:bars:MSFT"})
    a._drained.update({"mrd:bars:AAPL", "mrd:bars:MSFT"})
    err = Exception("NOGROUP No such key 'mrd:bars:AAPL' or consumer group 'archive'")
    hit = a._forget_nogroup(err, ["mrd:bars:AAPL", "mrd:bars:MSFT"])
    assert hit == ["mrd:bars:AAPL"], "hata metninden anahtar çözülemedi"
    assert "mrd:bars:AAPL" not in a._groups and "mrd:bars:AAPL" not in a._drained
    assert "mrd:bars:MSFT" in a._groups, "ilgisiz akışın grubu boşuna düşürüldü"
    assert a.group_resets == 1 and a.snapshot()["group_resets"] == 1


def test_NOGROUP_anahtar_cozulemezse_MUHAFAZAKAR_davranir(sandbox_state):
    """Anahtar adı metinde yoksa tüm canlı akışlar unutulur: gereksiz XGROUP CREATE bedava,
    kaçırılmış onarım ise sessiz veri kaybıdır."""
    a = ba.BarsArchiver()
    a._groups.update({"mrd:bars:AAPL", "mrd:bars:MSFT"})
    hit = a._forget_nogroup(Exception("NOGROUP"), ["mrd:bars:AAPL", "mrd:bars:MSFT"])
    assert sorted(hit) == ["mrd:bars:AAPL", "mrd:bars:MSFT"] and a._groups == set()


def test_NOGROUP_disi_hata_onarim_TETIKLEMEZ(sandbox_state):
    a = ba.BarsArchiver()
    a._groups.add("mrd:bars:AAPL")
    assert a._forget_nogroup(TimeoutError("timed out"), ["mrd:bars:AAPL"]) == []
    assert a._groups == {"mrd:bars:AAPL"} and a.group_resets == 0


def test_yalniz_yazilir_katman_KAPALI_ve_geri_acma_yolu_yazili():
    """mrd:price + mrd:pos KARARI: loop'taki iki yazım noktası devre dışı; hotstate fonksiyonları
    SİLİNMEDİ (tüketici gelince kanca tek satır)."""
    src = (ROOT / "meridian" / "loop.py").read_text()
    tree = ast.parse(src)
    cagrilar = {n.func.attr for n in ast.walk(tree)
                if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)}
    assert "set_prices" not in cagrilar, "mrd:price yazımı hâlâ CANLI"
    assert "cache_positions" not in cagrilar, "mrd:pos yazımı hâlâ CANLI"
    assert "GERİ AÇMA" in src, "geri açma yolu yazılı değil"
    assert callable(hotstate.set_prices) and callable(hotstate.cache_positions)
    assert callable(hotstate.get_price) and callable(hotstate.get_positions)


def test_kapatma_SESSIZ_degil_ama_tur_basina_log_selini_de_dokmez(sandbox_state):
    """Süreç başına BİR kez: statik bir olgu için günlük olay yazmak obs defterini şişirirdi."""
    loop._HOTSTATE_OFF_LOGGED.clear()
    try:
        loop._hotstate_off_once("mrd:pos", "_save_broker", "get_positions")
        loop._hotstate_off_once("mrd:pos", "_save_broker", "get_positions")
        olaylar = [e for e in store.read_jsonl("events.jsonl")
                   if e.get("event") == "hotstate_write_disabled"]
        assert len(olaylar) == 1, f"tekrar bastırılmadı: {len(olaylar)}"
    finally:
        loop._HOTSTATE_OFF_LOGGED.clear()


def test_mrd_ord_OLU_SEMA_beyani_temizlendi():
    """Ölü şema beyanı yalnız fazlalık değildir: sonraki okuyucuyu 'emirler zaten sıcak katmanda'
    diye yanlış yönlendirir."""
    src = (ROOT / "meridian" / "hotstate.py").read_text()
    # ŞEMA SATIRLARI: "  mrd:xxx  → ..." biçimli beyan satırları. Kaldırma GEREKÇESİ metinde
    # `mrd:ord`dan söz edebilir (etmeli); yasak olan onu bir ŞEMA SATIRI olarak listelemektir.
    sema = [l.strip() for l in src.splitlines() if l.strip().startswith("mrd:") and "→" in l]
    assert sema, "şema beyanı hiç yok — tarama yanlış yere bakıyor"
    assert not any(l.startswith("mrd:ord") for l in sema), \
        f"mrd:ord hâlâ şema satırı olarak beyan ediliyor: {sema}"
    assert 'PREFIX + "ord"' not in src, "beyan kaldırıldı ama yazan/okuyan bir kod eklenmiş"


def test_barsarchive_runner_OPS_katmaninda():
    """Koşmayan bir arşivci 'sonra toplarız' demez: Redis ring'i ~2 seans tutar."""
    p = ROOT / "ops" / "barsarchive-run.sh"
    assert p.exists(), "ops girişi yok — modül yine elle terminal açmaya bağlı"
    s = p.read_text()
    for komut in ("start)", "stop)", "status)", "once)"):
        assert komut in s
    assert "nohup" in s and "launchctl" not in s.replace("launchctl-siz", "")
    assert "meridian.barsarchive" in s
    # serve.sh'ye DOKUNMAZ: adı gerekçede geçebilir, ama ÇALIŞTIRILMAZ / source EDİLMEZ.
    kod = [l for l in s.splitlines() if not l.strip().startswith("#")]
    assert not any("serve.sh" in l for l in kod), "runner serve.sh'yi çağırıyor"
    assert "stop-worker" not in s, "runner canlı worker süreç grubuna dokunuyor"
    assert not (ROOT / "serve.sh").read_text().count("barsarchive"), \
        "serve.sh'ye barsarchive eklenmiş — bu turun sözü serve.sh'ye dokunmamaktı"
    import os
    assert os.access(p, os.X_OK), "çalıştırma izni yok"
