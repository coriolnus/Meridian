"""v585 — TSK-020 UYGULA-9 Faz B: motor gecikme histogramları (sıfır bağımlılık) `/metrics`'e + Grafana panelleri
(2026-09-28).

TASARIM (bağlayıcı, operatör ONAYLI 2026-09-28): `docs/TASARIM-TELEMETRI-PROMETHEUS-2026-09-28.md` — T4 (süreç-içi sabit
kovalı histogram, `prometheus_client` YOK), T3(b) (meridian `/metrics` yerel istek tam seti alır; gizlilik sınırı
korunur), T7 (aynı kaynağın iki görünümü, kopya değil), §2 (telemetri GÖZLEMDİR — hiçbir kapı/kill kararı bu
histogramlardan okumaz; KILL#1 canlı çapası ayrı kart, Faz C).

NE ÖLÇÜLÜR — her bölüm bir iddia:
  A. İfade biçimi: `# HELP`/`# TYPE histogram` tek kez; `_bucket{le=…}` BİRİKİMLİ ve monoton; `le="+Inf"` = `_count`;
     `_sum` gözlemlerin toplamı; `le` "küçük-eşit"tir (sınırdaki gözlem o kovadadır); kurucu geçersiz tanımı REDDEDER;
     sonlu-olmayan/negatif gözlem kaydedilmez ama SAYILIR ve görünür; bilinmeyen etiket değeri `other`a düşer
     (kardinalite beyanlı küme + 1 ile sınırlı).
  B. Sarma davranış değiştirmez: `gecikme.sure_olc` normal ve istisna yolunda süreyi kaydeder, istisnayı AYNEN
     (aynı nesne) yükseltir; `IntradayConsumer.on_barfeed_event` dönüşü/sayaçları/yutma sözleşmesi aynı, sonuç etiketi
     (processed/skipped/error) doğru; `skills.pipeline_run` defter satırı ve istisna yolu aynı, faz etiketi sınırlı;
     `store._record_io` io_stats ile AYNI ölçümü histograma da işler.
  C. Gizlilik sınırı: yerel istek histogramları görür; uzak+yetkisiz ve vekilli+yetkisiz istek GÖRMEZ.
  D. Tek kaynak: pano sorgularındaki `meridian_*` adları `/metrics`in gerçekten yayınladığı seri adlarının alt
     kümesidir; motorda tanımlı her histogram yayınlanır; IO kovası store'un uyarı eşiğini TAŞIR (türetilmiş); faz
     etiket kümesi `skills.PIPELINES`tir; `gecikme` saf yapraktır (meridian içe aktarmaz).
  E. Eşzamanlılık: iki iş parçacığı aynı histograma yazar, sayım kaybolmaz; durum yalnız KİLİT ALTINDA okunur/yazılır.
  F. Bedel (Bedel yasası): sarmanın tur başına ek süresi ve `/metrics` gövde büyümesi ÖLÇÜLÜR ve basılır
     (`-s` ile görünür); tavanlar bloat/regresyon bekçisidir, kanıt değil.

BİLİNEN SINIR (dürüst beyan): CPython 3.12 GIL'i altında `kova[i] += 1` deseni kilitsiz de sayım kaybetmeyebilir —
E1 davranışsal korunumu gösterir ama kilit kaldırma mutasyonunu kendi başına ISIRMAYABİLİR; kilidin varlığını ısıran
çivi E2'dir (deterministik kayıtlı kilit). Bu dosya `state/`e yalnız `sandbox_state` üzerinden dokunur, ağa çıkmaz.

Numara v585: `ls tests | grep v585` boş (2026-09-28, brief).
"""
from __future__ import annotations

import ast
import datetime as dt
import json
import math
import pathlib
import re
import statistics
import sys
import threading
import time

import pytest

from meridian import api, barclock as bc, gecikme, intraday_cycle as ic, skills, store
from tests.test_metrics_vekil_v365 import _req

KOK = pathlib.Path(__file__).resolve().parent.parent
MERIDIAN = KOK / "meridian"
PANO = KOK / "deploy" / "telemetri" / "grafana" / "panolar" / "meridian-gecikme.json"
UTC = dt.timezone.utc
RTH = dt.datetime(2026, 7, 23, 14, 46, 30, tzinfo=UTC)          # 10:46:30 ET — RTH ve sabah penceresi açık
GECE = dt.datetime(2026, 7, 23, 3, 0, 0, tzinfo=UTC)             # 23:00 ET — seans dışı


@pytest.fixture(autouse=True)
def _tuketici_ve_saat_sifirla():
    """`set_clock` modül-geneli; tüketici tekil — ikisi de testler arasına sızmasın (v88 deseni)."""
    ic._CONSUMER = None
    yield
    bc.reset_clock()
    ic._CONSUMER = None


# ---- yardımcılar ------------------------------------------------------------------------------------------------

_SATIR = re.compile(r'^(?P<ad>[a-zA-Z_:][a-zA-Z0-9_:]*)(?:\{(?P<etiketler>[^}]*)\})? (?P<deger>\S+)$')


def _ayristir(metin: str) -> dict:
    """Prometheus metin ifadesini {aile: {"help": [...], "type": [...], "ornekler": [(ad, {etiket: değer}, değer)]}}
    biçimine ayırır. Tanınmayan örnek satırı çiviyi KIRMIZI yapar (ayrıştırıcı sessizce atlamaz)."""
    aileler: dict = {}
    for satir in metin.splitlines():
        if not satir.strip():
            continue
        if satir.startswith("# HELP ") or satir.startswith("# TYPE "):
            _, tur, ad, *geri = satir.split(" ", 3)
            aileler.setdefault(ad, {"help": [], "type": [], "ornekler": []})[tur.lower()].append(
                geri[0] if geri else "")
            continue
        if satir.startswith("#"):
            continue
        m = _SATIR.match(satir)
        assert m, f"ayrıştırılamayan örnek satırı: {satir!r}"
        ad = m["ad"]
        etiketler = dict(re.findall(r'([a-zA-Z_][a-zA-Z0-9_]*)="([^"]*)"', m["etiketler"] or ""))
        aile = re.sub(r"_(bucket|sum|count)$", "", ad)
        aileler.setdefault(aile, {"help": [], "type": [], "ornekler": []})["ornekler"].append(
            (ad, etiketler, float(m["deger"])))
    return aileler


def _seri(aile: dict, sonek: str, **etiket) -> list[tuple[dict, float]]:
    """Bir ailenin `_bucket`/`_sum`/`_count` örnekleri, verilen etiketlere uyanlar (le hariç eşleşme)."""
    out = []
    for ad, et, deger in aile["ornekler"]:
        if not ad.endswith(sonek):
            continue
        if all(et.get(k) == v for k, v in etiket.items()):
            out.append((et, deger))
    return out


def _sayi(h: "gecikme.Histogram", etiket_degeri=None) -> int:
    """Histogramın bir serisinin gözlem sayısı (yoksa 0)."""
    return h.anlik().get(etiket_degeri, {}).get("sayi", 0)


def _toplam(h: "gecikme.Histogram", etiket_degeri=None) -> float:
    """Histogramın bir serisinin süre toplamı (yoksa 0.0)."""
    return h.anlik().get(etiket_degeri, {}).get("toplam", 0.0)


def _sahte_saat(monkeypatch, degerler: list[float]) -> None:
    """`gecikme._saat`i sırayla verilen değerleri döndüren sahte saatle değiştirir (deterministik süre)."""
    it = iter(degerler)
    monkeypatch.setattr(gecikme, "_saat", lambda: next(it))


def _yerel_metrics() -> str:
    """Yerel (127.0.0.1, XFF'siz) istekle `/metrics` gövdesi — tam set."""
    return api.metrics(_req("127.0.0.1"))


# =================================================================================================================
# A — ifade biçimi
# =================================================================================================================

def test_A1_HELP_ve_TYPE_histogram_TEK_kez_ve_aile_bitisik():
    h = gecikme.Histogram("v585_a1_seconds", "a1 test", kovalar=(0.1, 1.0))
    h.gozlemle(0.05)
    metin = h.ifade()
    aile = _ayristir(metin)["v585_a1_seconds"]
    assert aile["type"] == ["histogram"], aile["type"]
    assert aile["help"] == ["a1 test"], aile["help"]
    satirlar = [s for s in metin.splitlines() if s]
    assert satirlar[0].startswith("# HELP v585_a1_seconds ") and satirlar[1] == "# TYPE v585_a1_seconds histogram"
    assert all(s.startswith("v585_a1_seconds_") for s in satirlar[2:]), "aile satırları bitişik değil"


def test_A2_kovalar_BIRIKIMLI_monoton_Inf_esittir_count_sum_tutarli():
    h = gecikme.Histogram("v585_a2_seconds", "a2", kovalar=(0.001, 0.01, 0.1, 1.0))
    gozlemler = [0.0005, 0.002, 0.002, 0.05, 0.5, 3.0, 7.25]
    for g in gozlemler:
        h.gozlemle(g)
    aile = _ayristir(h.ifade())["v585_a2_seconds"]
    kovalar = _seri(aile, "_bucket")
    les = [et["le"] for et, _ in kovalar]
    assert les == ["0.001", "0.01", "0.1", "1.0", "+Inf"], les
    sayilar = [d for _, d in kovalar]
    assert sayilar == [1, 3, 4, 5, 7], f"birikimli değil: {sayilar}"
    assert all(a <= b for a, b in zip(sayilar, sayilar[1:])), "kova sayıları monoton değil"
    (_, sayi), = _seri(aile, "_count")
    (_, toplam), = _seri(aile, "_sum")
    assert sayilar[-1] == sayi == len(gozlemler), "le=+Inf ≠ _count"
    assert math.isclose(toplam, sum(gozlemler), rel_tol=1e-12), (toplam, sum(gozlemler))


def test_A3_le_KUCUK_ESIT_sinirdaki_gozlem_O_kovada():
    h = gecikme.Histogram("v585_a3_seconds", "a3", kovalar=(0.05, 0.1))
    h.gozlemle(0.05)
    kovalar = dict((et["le"], d) for et, d in _seri(_ayristir(h.ifade())["v585_a3_seconds"], "_bucket"))
    assert kovalar["0.05"] == 1, f"sınırdaki gözlem le=0.05 kovasına düşmedi (≤ semantiği): {kovalar}"


@pytest.mark.parametrize("kw, beklenen", [
    ({"ad": "v585 bosluk", "kovalar": (1.0,)}, "ad"),
    ({"ad": "v585_ok_seconds", "kovalar": ()}, "kova"),
    ({"ad": "v585_ok_seconds", "kovalar": (1.0, 1.0)}, "kova"),
    ({"ad": "v585_ok_seconds", "kovalar": (2.0, 1.0)}, "kova"),
    ({"ad": "v585_ok_seconds", "kovalar": (0.0, 1.0)}, "kova"),
    ({"ad": "v585_ok_seconds", "kovalar": (1.0, float("inf"))}, "kova"),
    ({"ad": "v585_ok_seconds", "kovalar": (1.0,), "etiket": "le", "etiket_degerleri": ("a",)}, "etiket"),
    ({"ad": "v585_ok_seconds", "kovalar": (1.0,), "etiket": "x", "etiket_degerleri": ('a"b',)}, "etiket"),
    ({"ad": "v585_ok_seconds", "kovalar": (1.0,), "etiket": "x", "etiket_degerleri": ()}, "etiket"),
])
def test_A4_kurucu_GECERSIZ_tanimi_REDDEDER(kw, beklenen):
    ad = kw.pop("ad")
    with pytest.raises(ValueError, match=beklenen):
        gecikme.Histogram(ad, "a4", **kw)


def test_A5_sonlu_olmayan_ve_negatif_gozlem_KAYDEDILMEZ_ama_SAYILIR_ve_GORUNUR():
    h = gecikme.Histogram("v585_a5_seconds", "a5", kovalar=(1.0,))
    for kotu in (float("nan"), float("inf"), -0.001, None, True):
        h.gozlemle(kotu)
    assert _sayi(h) == 0 and _toplam(h) == 0.0, "geçersiz gözlem seriye girdi (sum NaN/negatif kirlenir)"
    assert h.reddedilen == 5, h.reddedilen
    assert "# NOTE v585_a5_seconds reddedilen_gozlem 5" in h.ifade(), "reddedilen gözlem görünmez"
    h.gozlemle(0.5)
    assert _sayi(h) == 1


def test_A6_etiket_kumesi_SINIRLI_bilinmeyen_other_a_duser_ve_ONCEDEN_kurulur():
    h = gecikme.Histogram("v585_a6_seconds", "a6", kovalar=(1.0,), etiket="yol", etiket_degerleri=("x", "y"))
    ilk = _ayristir(h.ifade())["v585_a6_seconds"]
    # ÖNCEDEN KURULUM: beyanlı değerler sıfır sayımla baştan yayınlanır — ilk gözlem `increase()`te kaybolmasın.
    assert {et["yol"] for et, _ in _seri(ilk, "_count")} == {"x", "y"}
    for i in range(50):
        h.gozlemle(0.1, f"kullanici-girdisi-{i}")
    h.gozlemle(0.1, None)
    h.gozlemle(0.1, "x")
    aile = _ayristir(h.ifade())["v585_a6_seconds"]
    degerler = {et["yol"] for et, _ in _seri(aile, "_count")}
    assert degerler == {"x", "y", gecikme.DIGER}, f"kardinalite sınırı delindi: {sorted(degerler)[:8]}…"
    assert _sayi(h, gecikme.DIGER) == 51 and _sayi(h, "x") == 1 and _sayi(h, "y") == 0


# =================================================================================================================
# B — sarma davranış değiştirmez
# =================================================================================================================

def test_B1_sure_olc_NORMAL_yolda_sureyi_kaydeder(monkeypatch):
    h = gecikme.Histogram("v585_b1_seconds", "b1", kovalar=(1.0,))
    _sahte_saat(monkeypatch, [100.0, 100.25])
    with gecikme.sure_olc(h) as olcum:
        sonuc = "govde"
    assert sonuc == "govde" and olcum is not None
    assert _sayi(h) == 1 and _toplam(h) == 0.25


def test_B2_sure_olc_ISTISNA_yolunda_KAYDEDER_ve_ISTISNA_AYNEN_yukselir(monkeypatch):
    h = gecikme.Histogram("v585_b2_seconds", "b2", kovalar=(1.0,), etiket="s", etiket_degerleri=("ok", "hata"))
    _sahte_saat(monkeypatch, [5.0, 5.5])
    ozgun = KeyError("ozgun")
    with pytest.raises(KeyError) as yakalanan:
        with gecikme.sure_olc(h, "hata"):
            raise ozgun
    assert yakalanan.value is ozgun, "istisna değişti/sarıldı — aynen yükselmeli"
    assert _sayi(h, "hata") == 1 and _toplam(h, "hata") == 0.5, "istisna yolunda süre kaydedilmedi"


def test_B3_on_barfeed_event_SEANS_DISI_skipped_ve_davranis_AYNI(sandbox_state):
    bc.set_clock(lambda: GECE)
    t = ic.consumer()
    once = _sayi(ic.DONGU_SURESI, "skipped")
    donus = t.on_barfeed_event({"syms": "AAPL"})
    assert donus is None
    assert t.skipped["session"] == 1 and t.events_handled == 0, "seans kapısının davranışı değişti"
    assert _sayi(ic.DONGU_SURESI, "skipped") == once + 1


def test_B4_on_barfeed_event_ISLENEN_olay_processed(sandbox_state):
    bc.set_clock(lambda: RTH)
    store.write_json("portfolio.json", {"positions": {}, "armed": []})
    t = ic.consumer()
    once = _sayi(ic.DONGU_SURESI, "processed")
    assert t.on_barfeed_event({"syms": ""}) is None
    assert t.events_handled == 1, "RTH+pencere olayı işlenmedi — test kurgusu geçersiz"
    assert _sayi(ic.DONGU_SURESI, "processed") == once + 1


def test_B5_on_barfeed_event_HATA_yutulur_kaydedilir_ve_error(sandbox_state, monkeypatch):
    uyarilar = []
    monkeypatch.setattr(ic.obs, "warn", lambda olay, **kw: uyarilar.append((olay, kw)))

    def patla(self, fields):
        raise RuntimeError("v585 bilerek")

    monkeypatch.setattr(ic.IntradayConsumer, "_handle", patla)
    t = ic.consumer()
    once = _sayi(ic.DONGU_SURESI, "error")
    assert t.on_barfeed_event({"syms": "AAPL"}) is None, "yutma sözleşmesi değişti"
    assert t.last_error == "RuntimeError: v585 bilerek"
    assert [o for o, _ in uyarilar] == ["intraday_event_failed"]
    assert _sayi(ic.DONGU_SURESI, "error") == once + 1


def test_B6_on_barfeed_event_uyari_kanali_duserse_ISTISNA_AYNEN_yukselir_sure_yine_kaydedilir(
        sandbox_state, monkeypatch):
    ozgun = OSError("kanal düştü")

    def kanal(olay, **kw):
        raise ozgun

    def patla(self, fields):
        raise RuntimeError("v585")

    monkeypatch.setattr(ic.obs, "warn", kanal)
    monkeypatch.setattr(ic.IntradayConsumer, "_handle", patla)
    once = _sayi(ic.DONGU_SURESI, "error")
    with pytest.raises(OSError) as yakalanan:
        ic.consumer().on_barfeed_event({"syms": "AAPL"})
    assert yakalanan.value is ozgun
    assert _sayi(ic.DONGU_SURESI, "error") == once + 1


def test_B7_pipeline_run_NORMAL_ve_ISTISNA_yolu_AYNI_faz_etiketi_SINIRLI(sandbox_state, monkeypatch):
    h = skills.BORU_HATTI_SURESI
    _sahte_saat(monkeypatch, [10.0, 17.5, 20.0, 21.0, 30.0, 30.5])
    once_p1, once_p2, once_diger = _sayi(h, "P1_REGIME"), _sayi(h, "P2_SCREEN"), _sayi(h, gecikme.DIGER)
    toplam_p1 = _toplam(h, "P1_REGIME")
    with skills.pipeline_run("P1_REGIME", artifact="state/regime.json") as run:
        run_id = run["run_id"]
    ozgun = ValueError("faz düştü")
    with pytest.raises(ValueError) as yakalanan:
        with skills.pipeline_run("P2_SCREEN"):
            raise ozgun
    assert yakalanan.value is ozgun, "pipeline_run istisnayı değiştirdi"
    with skills.pipeline_run("P9_BILINMEYEN"):
        pass
    satirlar = store.read_jsonl(skills.RUNS)
    assert [s["status"] for s in satirlar[-3:]] == ["ok", "error", "ok"], "defter sözleşmesi değişti"
    assert satirlar[-3]["run_id"] == run_id and satirlar[-2]["error"] == "ValueError: faz düştü"
    assert _sayi(h, "P1_REGIME") == once_p1 + 1 and math.isclose(_toplam(h, "P1_REGIME") - toplam_p1, 7.5)
    assert _sayi(h, "P2_SCREEN") == once_p2 + 1, "istisna yolunda faz süresi kaydedilmedi"
    assert _sayi(h, gecikme.DIGER) == once_diger + 1, "bilinmeyen boru hattı adı `other`a düşmedi"
    assert set(h.anlik()) <= set(skills.PIPELINES) | {gecikme.DIGER}


def test_B8_record_io_AYNI_olcumu_histograma_isler(sandbox_state):
    h = store.YAZIM_SURESI
    once_n, once_t, once_w = _sayi(h), _toplam(h), store.io_stats()["writes"]
    store.write_json("v585_io.json", {"a": 1})
    assert store.io_stats()["writes"] == once_w + 1
    assert _sayi(h) == once_n + 1, "atomik yazım histograma işlenmedi"
    son_ms = store._IO["recent"][-1]
    assert math.isclose(_toplam(h) - once_t, son_ms / 1000.0, rel_tol=1e-9), "iki görünüm AYNI ölçüm değil"


# =================================================================================================================
# C — gizlilik sınırı
# =================================================================================================================

def test_C1_YEREL_istek_histogramlari_GORUR(sandbox_state):
    metin = _yerel_metrics()
    tipler = re.findall(r"^# TYPE (\S+) histogram$", metin, flags=re.M)
    assert set(tipler) == {h.ad for h in api._gecikme_histogramlari()}, tipler
    assert "_bucket{" in metin
    # Aynı aile İKİ kez yayınlanırsa Prometheus kazımanın TAMAMINI reddeder (ikinci TYPE satırı / yinelenen örnek) —
    # gauge'lar dahil hedef "down" olur. Küme eşitliği yinelemeyi göremez; sayım görür.
    butun = re.findall(r"^# TYPE (\S+) ", metin, flags=re.M)
    assert len(butun) == len(set(butun)), f"yinelenen metrik ailesi: {sorted(a for a in butun if butun.count(a) > 1)}"


@pytest.mark.parametrize("istemci, basliklar", [
    ("198.51.100.9", {}),                                   # uzak + yetkisiz
    ("127.0.0.1", {"X-Forwarded-For": "203.0.113.7"}),      # vekilli (kapı arkası) + yetkisiz
])
def test_C2_UZAK_ya_da_VEKILLI_yetkisiz_istek_histogram_GORMEZ(sandbox_state, istemci, basliklar):
    from meridian import auth
    auth.set_password("v585-test-parolasi")        # parolasız kum havuzunda `_auth` no-op'tur (v365 ölçümü)
    metin = api.metrics(_req(istemci, basliklar))
    assert "meridian_up" in metin, "canlılık üçlüsü de gitti — test kurgusu geçersiz"
    assert "histogram" not in metin and "_bucket" not in metin and "_seconds_sum" not in metin, \
        "gizlilik sınırı delindi: yetkisiz uzak istek histogram gördü"


# =================================================================================================================
# D — tek kaynak
# =================================================================================================================

def _pano_ifadeleri() -> list[str]:
    pano = json.loads(PANO.read_text(encoding="utf-8"))
    return [h.get("expr", "") for p in pano["panels"] for h in p.get("targets", [])]


def test_D1_pano_meridian_adlari_YAYINLANAN_seri_adlarinin_ALT_KUMESI(sandbox_state):
    yayinlanan = {ad for aile in _ayristir(_yerel_metrics()).values() for ad, _, _ in aile["ornekler"]}
    panodaki = {m for e in _pano_ifadeleri() for m in re.findall(r"\bmeridian_[a-zA-Z0-9_]+", e)}
    assert len(panodaki) >= 4, f"panoda Faz B sorgusu yok: {panodaki}"
    eksik = panodaki - yayinlanan
    assert not eksik, f"pano /metrics'in YAYINLAMADIĞI adları sorguluyor: {sorted(eksik)}"


def test_D2_pano_brief_panellerini_TASIR():
    ifadeler = _pano_ifadeleri()

    def var(*parcalar: str) -> bool:
        return any(all(p in e for p in parcalar) for e in ifadeler)

    for q in ("0.5", "0.95", "0.99"):
        assert var(f"histogram_quantile({q}", "rate(meridian_intraday_cycle_seconds_bucket",
                   'outcome="processed"'), f"karar döngüsü p{q} (işlenen olaylar) paneli yok"
    assert var("meridian_pipeline_run_seconds_sum", "meridian_pipeline_run_seconds_count", "by (pipeline)"), \
        "faz süresi paneli yok"
    assert var("histogram_quantile(0.95", "rate(meridian_store_write_seconds_bucket"), "IO p95 paneli yok"


def _histogram_kurulumlari() -> dict[str, str]:
    """meridian/ altında `gecikme.Histogram("<ad>", …)` kurulumları → {ad: dosya}. `gecikme.py`nin kendisi hariç."""
    out = {}
    for yol in sorted(MERIDIAN.rglob("*.py")):
        if yol.name == "gecikme.py":
            continue
        for d in ast.walk(ast.parse(yol.read_text(encoding="utf-8"))):
            if (isinstance(d, ast.Call) and isinstance(d.func, ast.Attribute) and d.func.attr == "Histogram"
                    and isinstance(d.func.value, ast.Name) and d.func.value.id == "gecikme"):
                assert d.args and isinstance(d.args[0], ast.Constant), f"{yol.name}: histogram adı literal değil"
                out[d.args[0].value] = yol.name
    return out


def test_D3_motorda_TANIMLI_her_histogram_YAYINLANIR(sandbox_state):
    tanimli = _histogram_kurulumlari()
    assert len(tanimli) >= 3, f"tarayıcı boş gördü (canlı taban): {tanimli}"
    yayinlanan = set(re.findall(r"^# TYPE (\S+) histogram$", _yerel_metrics(), flags=re.M))
    assert set(tanimli) == yayinlanan, f"tanımlı ama yayınlanmayan: {set(tanimli) - yayinlanan}; " \
                                       f"yayınlanan ama taranmayan: {yayinlanan - set(tanimli)}"


def test_D4_IO_kovasi_store_UYARI_ESIGINI_tasir_TURETILMIS():
    assert store.IO_P95_UYARI_MS / 1000.0 in store.YAZIM_SURESI.kovalar, \
        "io_latency_high eşiği bir kova sınırı değil — eşik üstü payı histogramdan KESİN okunamaz"


def test_D5_faz_etiket_kumesi_skills_PIPELINES():
    assert skills.BORU_HATTI_SURESI.etiket == "pipeline"
    assert skills.BORU_HATTI_SURESI.etiket_degerleri == tuple(skills.PIPELINES)


def test_D6_gecikme_SAF_YAPRAK_meridian_ice_aktarmaz():
    agac = ast.parse((MERIDIAN / "gecikme.py").read_text(encoding="utf-8"))
    ihlal = []
    for d in ast.walk(agac):
        if isinstance(d, ast.ImportFrom) and (d.level or (d.module or "").startswith("meridian")):
            ihlal.append(ast.unparse(d))
        if isinstance(d, ast.Import) and any(a.name.startswith("meridian") for a in d.names):
            ihlal.append(ast.unparse(d))
    assert not ihlal, f"gecikme saf yaprak değil (store/obs döngüsüne girer): {ihlal}"
    assert any(isinstance(d, (ast.Import, ast.ImportFrom)) for d in ast.walk(agac)), "tarayıcı boş gördü"


def test_D7_etiket_degerleri_KULLANICI_girdisinden_TUREMEZ_intraday_sonuclari_sabit():
    assert ic.DONGU_SURESI.etiket == "outcome"
    assert ic.DONGU_SURESI.etiket_degerleri == ("processed", "skipped", "error")
    assert store.YAZIM_SURESI.etiket is None


# =================================================================================================================
# E — eşzamanlılık
# =================================================================================================================

def test_E1_iki_is_parcacigi_ayni_histograma_yazar_SAYIM_KAYBOLMAZ():
    h = gecikme.Histogram("v585_e1_seconds", "e1", kovalar=(0.1, 1.0), etiket="k", etiket_degerleri=("a",))
    n = 50_000
    engel = threading.Barrier(2)

    def yaz():
        engel.wait()
        for _ in range(n):
            h.gozlemle(0.5, "a")

    eski = sys.getswitchinterval()
    sys.setswitchinterval(1e-6)          # iş parçacığı geçişini sıklaştır — yarış penceresi açılsın
    try:
        isler = [threading.Thread(target=yaz) for _ in range(2)]
        for t in isler:
            t.start()
        for t in isler:
            t.join()
    finally:
        sys.setswitchinterval(eski)
    s = h.anlik()["a"]
    assert s["sayi"] == 2 * n and s["toplam"] == 0.5 * 2 * n, s
    kovalar = dict((et["le"], d) for et, d in _seri(_ayristir(h.ifade())["v585_e1_seconds"], "_bucket", k="a"))
    assert kovalar == {"0.1": 0, "1.0": 2 * n, "+Inf": 2 * n}, kovalar


class _KayitliKilit:
    """Kilit taklidi: tutulup tutulmadığını kaydeder (deterministik kilit disiplini çivisi)."""

    def __init__(self):
        self.tutuluyor = False
        self.giris = 0

    def __enter__(self):
        assert not self.tutuluyor, "kilit yeniden girildi"
        self.tutuluyor = True
        self.giris += 1
        return self

    def __exit__(self, *a):
        self.tutuluyor = False
        return False


def test_E2_durum_YALNIZ_KILIT_ALTINDA_okunur_ve_yazilir():
    h = gecikme.Histogram("v585_e2_seconds", "e2", kovalar=(1.0,), etiket="k", etiket_degerleri=("a",))
    kilit = _KayitliKilit()

    class _Bekci(dict):
        def _kontrol(self):
            assert kilit.tutuluyor, "histogram durumu KİLİTSİZ erişildi"

        def __getitem__(self, k):
            self._kontrol()
            return super().__getitem__(k)

        def get(self, k, d=None):
            self._kontrol()
            return super().get(k, d)

        def __setitem__(self, k, v):
            self._kontrol()
            super().__setitem__(k, v)

        def items(self):
            self._kontrol()
            return super().items()

        def __contains__(self, k):
            self._kontrol()
            return super().__contains__(k)

    h._kilit = kilit
    h._seriler = _Bekci(h._seriler)
    h.gozlemle(0.5, "a")
    h.gozlemle(0.5, "yeni")
    h.gozlemle(float("nan"))
    h.anlik()
    h.ifade()
    assert kilit.giris >= 5 and not kilit.tutuluyor


# =================================================================================================================
# F — bedel (ölçülür ve basılır; tavanlar bloat bekçisi)
# =================================================================================================================

def test_F1_sarmanin_tur_basina_EK_SURESI_olculur():
    h = gecikme.Histogram("v585_f1_seconds", "f1", kovalar=ic.DONGU_SURESI.kovalar, etiket="outcome",
                          etiket_degerleri=("processed", "skipped", "error"))
    n = 20_000

    def bos():
        return None

    turlar = []
    for _ in range(7):
        t0 = time.perf_counter()
        for _ in range(n):
            bos()
        taban = time.perf_counter() - t0
        t0 = time.perf_counter()
        for _ in range(n):
            with gecikme.sure_olc(h, "error") as olcum:
                bos()
                olcum.etiket_degeri = "processed"
        sarili = time.perf_counter() - t0
        turlar.append((sarili - taban) / n)
    ek = statistics.median(turlar)
    print(f"\nBEDEL v585 F1: sure_olc tur başına ek süre medyan {ek * 1e6:.2f} µs "
          f"(7 tur × {n}; min {min(turlar) * 1e6:.2f} µs, maks {max(turlar) * 1e6:.2f} µs)")
    assert ek < 50e-6, f"sarma tur başına {ek * 1e6:.1f} µs ekliyor — beklenen µs mertebesi"


def test_F2_metrics_govdesi_ONCESI_SONRASI_olculur(sandbox_state):
    metin = _yerel_metrics()
    hist = gecikme.ifade(*api._gecikme_histogramlari())
    assert metin.endswith(hist), "histogram bölümü gövdenin sonunda değil — ölçüm kurgusu geçersiz"
    once, sonra = len(metin.encode()) - len(hist.encode()), len(metin.encode())
    satir = sum(1 for s in hist.splitlines() if s and not s.startswith("#"))
    print(f"\nBEDEL v585 F2: /metrics tam set gövdesi {once} B → {sonra} B (+{sonra - once} B, "
          f"{satir} örnek satırı, {len(api._gecikme_histogramlari())} histogram)")
    assert sonra - once < 64 * 1024, "histogram bölümü 64 KiB'ı aştı — kova/etiket şişmesi"


def test_F3_on_barfeed_event_YERINDE_sarma_EK_SURESI_olculur(sandbox_state):
    """Yerinde ölçüm: aynı kapı-önü (seans dışı) yol, sarmalı `on_barfeed_event` ile sarmasız `_handle` arasında
    serpiştirilmiş turlarla — fark sarmanın (sure_olc + sonuç etiketi + try) tur başına bedelidir."""
    bc.set_clock(lambda: GECE)
    t = ic.consumer()
    olay = {"syms": "AAPL"}
    n = 2_000
    farklar = []
    for tur in range(9):
        sira = (t._handle, t.on_barfeed_event) if tur % 2 == 0 else (t.on_barfeed_event, t._handle)
        sure = {}
        for fn in sira:
            t0 = time.perf_counter()
            for _ in range(n):
                fn(olay)
            sure[fn.__name__] = (time.perf_counter() - t0) / n
        farklar.append((sure["on_barfeed_event"] - sure["_handle"], sure["_handle"]))
    ek = statistics.median(f for f, _ in farklar)
    taban = statistics.median(b for _, b in farklar)
    print(f"\nBEDEL v585 F3: on_barfeed_event sarması yerinde ek süre medyan {ek * 1e6:.2f} µs/tur "
          f"(kapı-önü `_handle` tabanı {taban * 1e6:.2f} µs/tur; 9 serpiştirilmiş tur × {n})")
    assert t.skipped["session"] == 9 * 2 * n, "ölçülen yol kapı-önü yol değil — kurgu geçersiz"
    assert ek < 50e-6, f"sarma yerinde tur başına {ek * 1e6:.1f} µs ekliyor"
