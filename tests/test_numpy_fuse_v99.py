"""test_numpy_fuse_v99.py — numpy/NaN'ın API'den çıkmasını KALICI olarak imkânsız kılan sigorta.

tests/test_api_contract.py bir VAKAYI çiviliyor: OOS kapısının ürettiği `passes` bir `numpy.bool_`tü,
/api/hermes onu serileştiremedi ve uç HTTP 500 verdi. O vaka kaynağında düzeltildi — ama SINIF açık
kaldı: uçların dönüşleri canlı hesaplanır, yani yarın eklenecek her yeni alan aynı tuzağa yeniden
düşebilir ve yine yalnız BAŞARISIZ dalda görünür (geçen dal gerçek `bool` üretiyordu, hata tam da bu
yüzden saklanmıştı). Bu dosya vakayı değil SINIFI kapatan iki mekanizmayı ölçer:

  1. `store.sanitize` — tek yasa: np tipleri yerliye, SONLU OLMAYAN float None'a.
  2. `meridian.api._NativeRoute` — her uç dönüşünü o yasadan geçiren rota sınıfı.

İkinci başlık NaN'dır ve numpy'den bağımsız bir 500 kaynağıdır: Starlette `JSONResponse` gövdeyi
`allow_nan=False` ile dump eder, yani tek bir NaN ucun tamamını düşürür; dosyaya yazılırsa da
tarayıcının `JSON.parse`ı reddeder.
"""
from __future__ import annotations

import json

import numpy as np
import pytest
from fastapi import FastAPI
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient

from meridian import store
from meridian.api import app, _NativeRoute


# ---------------- 1) YASA: store.sanitize ----------------
def test_sanitize_numpy_scalars_become_native_types():
    """`type(...) is ...` KASITLIDIR, `isinstance` değil: `np.float64` Python `float`ın ALT SINIFIDIR,
    yani `isinstance(np.float64(0.5), float)` sanitize hiçbir şey yapmasa DA True döner — o test
    yeşil yanar ve hiçbir şey kanıtlamaz. Tam tip kimliği, dönüşümün gerçekten olduğunu ölçer."""
    out = store.sanitize({"b": np.bool_(True), "i": np.int64(7), "f": np.float64(0.5)})
    assert type(out["b"]) is bool and out["b"] is True
    assert type(out["i"]) is int and out["i"] == 7
    assert type(out["f"]) is float and out["f"] == 0.5
    json.dumps(out)                                    # sözleşmenin kendisi: serileşebilir


def test_sanitize_ndarray_becomes_a_native_list():
    out = store.sanitize(np.array([1.5, 2.5]))
    assert type(out) is list
    assert [type(v) for v in out] == [float, float]
    assert out == [1.5, 2.5]


def test_sanitize_recurses_through_nested_dicts_and_lists():
    """Sızıntı üst düzeyde değil, GÖMÜLÜ bir alanda olur (canlıdaki vaka SEARCH_PROGRESS'in içindeydi)."""
    payload = {"probes": [{"passes": np.bool_(False), "oos": np.float64(0.21)},
                          {"folds": (np.int64(30), np.float64(0.1))}],
               "grid": np.array([[1, 2], [3, 4]])}
    out = store.sanitize(payload)
    json.dumps(out)
    assert type(out["probes"][0]["passes"]) is bool
    assert type(out["probes"][0]["oos"]) is float
    assert type(out["probes"][1]["folds"]) is list       # tuple → list (JSON'da tuple yok)
    assert [type(v) for v in out["probes"][1]["folds"]] == [int, float]
    assert out["grid"] == [[1, 2], [3, 4]]


@pytest.mark.parametrize("deger", [np.nan, np.inf, -np.inf,
                                   np.float64("nan"), np.float64("inf"),
                                   float("nan"), float("inf"), float("-inf")])
def test_sanitize_non_finite_floats_become_none(deger):
    """NaN/±Inf JSON'da YOKTUR. `allow_nan=False` ile dump eden her tüketici (Starlette, tarayıcı)
    onları görünce patlar. Ayrıca NaN 'ölçülemedi' demektir; ölçülmeyenin dürüst temsili None'dır —
    0.0'a çevirmek okura ölçülmemiş bir değeri ölçülmüş gibi gösterirdi (UYDURMA YASAĞI)."""
    out = store.sanitize({"x": deger})
    assert out["x"] is None
    json.dumps(out, allow_nan=False)       # üretim tüketicisinin AYNI katılığıyla


def test_sanitize_keeps_finite_floats_and_passes_other_types_through():
    """Sigorta fazla kesmemeli: sonlu sayılar, str/None/bool aynen geçer — yoksa NaN'a karşı
    korurken gerçek veriyi yok eden bir 'düzeltme' olurdu."""
    out = store.sanitize({"f": 1.25, "nf": np.float64(-3.5), "s": "metin",
                          "n": None, "t": True, "fa": False, "i": 42})
    assert out == {"f": 1.25, "nf": -3.5, "s": "metin",
                   "n": None, "t": True, "fa": False, "i": 42}
    assert out["n"] is None and out["t"] is True and out["fa"] is False
    assert type(out["t"]) is bool and type(out["i"]) is int


# ---------------- 2) SİGORTA GERÇEKTEN TAKILI MI (üretim app'i) ----------------
def test_production_app_uses_the_native_route_class():
    assert app.router.route_class is _NativeRoute, (
        "rota sınıfı atanmamış — uçların canlı-hesap dönüşleri korumasız")


def test_every_api_route_endpoint_is_actually_wrapped():
    """`route_class` ATAMASI tek başına yetmez: `add_api_route` sınıfı KAYIT ANINDA okur, yani
    atama ilk `@app.get`ten sonra yapılsaydı erken rotalar sessizce korumasız kalırdı ve yukarıdaki
    test yine geçerdi. Kanıt, her uç fonksiyonunun sarılmış olmasıdır (`functools.wraps` →
    `__wrapped__`). Statik/HTML rotaları da sarılıdır; ayrım gerekmez (sanitize onlara dokunmaz)."""
    api_routes = [r for r in app.routes if isinstance(r, APIRoute)]
    assert len(api_routes) >= 40, "rota sayımı bozuldu — test artık hiçbir şeyi korumuyor olabilir"
    sarilmamis = [r.path for r in api_routes if not hasattr(r.endpoint, "__wrapped__")]
    assert not sarilmamis, f"sigortasız uç: {sarilmamis}"


def test_wrapping_preserves_the_original_signature_for_dependency_injection():
    """Sarıcı `*a, **k` alır; FastAPI'nin `request: Request` gibi parametreleri hâlâ çözebilmesi
    YALNIZCA `inspect.signature`ın `__wrapped__`i izlemesi sayesindedir. Bu bir SÜRÜM DAVRANIŞIDIR
    (fastapi 0.139.0) — değişirse sigorta değil, tüm API sessizce bozulur; burada çakılı."""
    r = next(x for x in app.routes if isinstance(x, APIRoute) and x.path == "/api/summary")
    assert r.dependant.request_param_name == "request"
    yol = next(x for x in app.routes
               if isinstance(x, APIRoute) and x.path == "/api/trade/{trade_id}")
    assert [p.name for p in yol.dependant.path_params] == ["trade_id"]


# ---------------- 3) İŞLEVSEL: sigorta uçtan uca ne yapıyor ----------------
# ÜRETİM APP'İNE TEST ROTASI EKLENMEZ: `app` modül düzeyinde tekildir, eklenen rota süreç boyunca
# kalır ve sonraki testlerin rota sayımı/yetki taramalarını kirletirdi. Sigorta SINIF olarak
# paylaşıldığı için yerel bir app onu birebir aynı şekilde koşturur.
def _mini_app() -> FastAPI:
    mini = FastAPI()
    mini.router.route_class = _NativeRoute

    @mini.get("/sync")
    def _sync():
        return {"passes": np.bool_(False), "oos": np.float64(0.21),
                "folds": np.array([1.5, 2.5]), "olcum": np.nan}

    @mini.get("/async")
    async def _async():
        return {"passes": np.bool_(True), "oos": np.float64(0.40),
                "folds": np.array([3.5, 4.5]), "olcum": float("nan")}

    return mini


@pytest.mark.parametrize("yol", ["/sync", "/async"])
def test_endpoint_returning_numpy_and_nan_serializes_cleanly(yol):
    """Sigortasız hâlde bu uç HTTP 500 verirdi — /api/hermes'i öldüren şeyin birebir aynısı."""
    with TestClient(_mini_app()) as c:
        r = c.get(yol)
    assert r.status_code == 200, f"{yol} → {r.status_code}: {r.text[:300]}"
    # HAM METİN kontrolü: `json.loads` NaN'ı sessizce kabul eder, yani yalnız parse ederek bakmak
    # bozuk gövdeyi GÖREMEZ. Tarayıcının `JSON.parse`ı ise kabul etmez — ölçülen o katılık.
    assert "NaN" not in r.text and "Infinity" not in r.text, f"ham gövdede JSON-dışı değer: {r.text}"
    body = json.loads(r.text)
    assert type(body["passes"]) is bool
    assert type(body["oos"]) is float
    assert type(body["folds"]) is list and [type(v) for v in body["folds"]] == [float, float]
    assert body["olcum"] is None                    # ölçülemedi → None, uydurulmuş bir sayı değil


def test_mini_app_without_the_fuse_actually_fails_positive_control():
    """POZİTİF KONTROL: yukarıdaki 200'ler 'FastAPI zaten hallediyor' demek DEĞİL. Aynı uç, rota
    sınıfı OLMADAN kurulunca gerçekten düşmeli — yoksa test bir sigortayı değil, hiçbir şeyi ölçer."""
    ciplak = FastAPI()

    @ciplak.get("/ciplak")
    def _ciplak():
        return {"passes": np.bool_(False)}

    with TestClient(ciplak, raise_server_exceptions=False) as c:
        r = c.get("/ciplak")
    assert r.status_code == 500, f"numpy artık kendiliğinden serileşiyor olabilir → {r.status_code}"


# ---------------- 4) GERİLEME: üretim uçları hâlâ ayakta ----------------
@pytest.mark.parametrize("yol", ["/api/summary", "/healthz"])
def test_production_endpoints_still_answer_200_through_the_fuse(yol, sandbox_state):
    """Sigorta HER dönüşün arasına giriyor; gerçek uçların hâlâ çalıştığı ölçülmeden takılmış sayılmaz.
    NABIZ TOHUMLANIR: /healthz nabız BAYATSA (ya da hiç yoksa) bilinçli olarak 503 döner — taze
    sandbox'ta 503 sigortanın değil, boş state'in sonucudur; 200 iddiası ancak nabız varken anlamlıdır."""
    import datetime as _dt
    store.write_json("heartbeat.json",
                     {"ts": _dt.datetime.now(_dt.timezone.utc).isoformat(), "equity": 100000.0})
    with TestClient(app) as client:
        r = client.get(yol)
    assert r.status_code == 200, f"{yol} → {r.status_code}: {r.text[:300]}"
    assert "NaN" not in r.text and "Infinity" not in r.text


# ---------------- 5) GERİLEME: yazım yolu (aynı yasa, diğer uç) ----------------
def test_write_json_puts_null_not_nan_on_disk(sandbox_state):
    """Diskteki NaN sessiz bir bombadır: Python `json.loads` onu KABUL eder (yani bir python testi
    fark etmez), tarayıcının `JSON.parse`ı ETMEZ — pano dosyayı hiç okuyamaz. Ham metin ölçülür."""
    yol = store.write_json("fuse_probe.json", {"x": np.nan, "y": np.float64(1.5),
                                               "z": float("inf"), "b": np.bool_(True)})
    ham = yol.read_text()
    assert "NaN" not in ham and "Infinity" not in ham, f"diske JSON-dışı değer yazıldı: {ham}"
    assert json.loads(ham) == {"x": None, "y": 1.5, "z": None, "b": True}
