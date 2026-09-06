"""test_tek_kaynak_refetch_ve_equity_v432.py — TSK-172 + TSK-173(a) (2026-09-06).

TSK-172 — `refetch_max` / `DENSE_ATTEMPTS` TEK KAYNAK (doğrulama C3): literal `8` dört yerde
yaşıyordu (`meridian/scheduler.py::DENSE_ATTEMPTS`, `meridian/api.py`'nin teşhis yükündeki
`"refetch_max": 8` literali, `meridian/web/app.js`'te `|| 8` ×2 + `?? 8` + sabit "8 adımlı" metni).
Davranış AYNI kalır (tavan hâlâ 8) — kaynak tekilleşir: `scheduler.DENSE_ATTEMPTS` TEK gerçek,
gerisi ondan TÜRER. Alan hiç gelmezse (varsayımsal — canlıda API her zaman değer gönderir) `|| 8`/
`?? 8` ile UYDURULMAZ, `null` kalır ve gösterge "—"/"(tavan ölçülemedi)" der (v295/9090 deseniyle
aynı: `mx = pl.refetch_max != null && Number.isFinite(...) ? Number(pl.refetch_max) : null`).

TSK-173(a) — 'yanıt VAR ama equity YOK' sessiz 100k (doğrulama C17, recall 2026-09-05 önerisi):
`meridian/loop.py::mirror_submit_armed` ayna gönderim yolunda `acct` sözlüğü GELDİĞİ hâlde
`equity` alanı yoksa ya da float'a çevrilemiyorsa eski kod `else START_EQUITY` ile SESSİZCE
100.000$'a düşüyordu. 'ULAŞILAMADI ≠ 100k' ilkesi (2026-07-21 denetimi, `acct is None ∧ transport
ok False` dalı) zaten kapalıydı; bu dosya AYNI ilkenin ikinci dalını kapatır: yanıt bir SÖZLÜK ama
`equity` okunamıyor. Muamele AYNI: `obs.alarm(obs.ALARM_BROKER_REJECT, ...)` + `_MirrorUnreachable`
(planlar SİLAHLI kalır, bu turda gönderim yok). `START_EQUITY`ye düşüş YALNIZ tarihsel/backtest
yollarında kalır — loop'un ayna gönderim yolunda ARTIK YOK.

FİKSTÜR EMSALİ: `tests/test_kovab_icra_v161.py::paper` (aynı desen — sahte Alpaca kimliği + donuk
saat, gönderim MEKANİĞİ değil equity okuma DALI ölçülüyor) ve
`test_c8_endpoint_refuses_on_halt_and_on_unreachable_mirror` (ulaşılamama emsali — bu dosyanın (a)
ve (b) çivileri onun equity-okunamaz ikizidir).

HİÇBİR TEST CANLI STATE'E YAZMAZ: `sandbox_state` ile izole; `obs.alarm` sandbox'ın
`state/events.jsonl`ına yazar, gerçek deftere değil.
"""
from __future__ import annotations

import datetime as _dt
import inspect
import pathlib
import re

import pytest

from meridian import barclock as _bc
from meridian import config, loop, obs, scheduler, store
from meridian.adapters import alpaca

KOK = pathlib.Path(__file__).resolve().parents[1]
WEB = KOK / "meridian" / "web"
API_PY = KOK / "meridian" / "api.py"

FAKE_KEY = "PKV432FAKEKEY7788990011"
FAKE_SECRET = "SKV432FAKESECRET2233445566778899"


# =================================================================================================
# TSK-172 — refetch_max / DENSE_ATTEMPTS TEK KAYNAK
# =================================================================================================

def test_c_scheduler_dense_attempts_degeri_korunur():
    """(c) Davranış DEĞİŞMEDİ: tavan hâlâ 8 — yalnız kaynak tekilleşti."""
    assert scheduler.DENSE_ATTEMPTS == 8


def test_a_api_kaynaginda_refetch_max_literali_YOK_dense_attempts_kullanilir():
    """(a) `api.py`nin kaynak METNİNDE `"refetch_max": 8` literali YOK ve `DENSE_ATTEMPTS`
    geçiyor — teşhis yükü artık `scheduler.DENSE_ATTEMPTS`ten türer, ikinci bir `8` taşımaz."""
    src = API_PY.read_text()
    assert '"refetch_max": 8' not in src, "eski literal hâlâ kaynakta duruyor — tekilleşme yarım"
    assert "DENSE_ATTEMPTS" in src, "api.py artık scheduler.DENSE_ATTEMPTS'i KULLANMIYOR"
    assert "_sched_mod.DENSE_ATTEMPTS" in src, "refetch_max alanı DENSE_ATTEMPTS'ten TÜREMİYOR"


def test_b_appjs_refetch_max_uydurma_default_YOK():
    """(b) `app.js` metninde `refetch_max || 8`, `refetch_max ?? 8`, `8 adımlı` YOK — eski üç
    uydurma-varsayılan deseni (iki `|| 8`, bir `?? 8`) ve sabit "8 adımlı" metni kaldırıldı."""
    app = (WEB / "app.js").read_text()
    assert "refetch_max || 8" not in app, "app.js hâlâ `|| 8` ile tavanı UYDURUYOR"
    assert "refetch_max ?? 8" not in app, "app.js hâlâ `?? 8` ile tavanı UYDURUYOR"
    assert "8 adımlı" not in app, "sabit '8 adımlı' metni hâlâ kaynakta — değerden TÜREMİYOR"
    # POZİTİF KONTROL: null-güvenli türetim GERÇEKTEN var, dosya boşuna basitleştirilmedi.
    assert "_sabirMax" in app and "tavan ölçülemedi" in app


def test_e_appjs_refetch_max_null_koruma_her_yerde():
    """(e) TSK-172 fix turu 1 (Rol-1 inceleme bulgusu): `Number.isFinite(Number(pl.refetch_max))`
    deseni `app.js`'te KAÇ yerde geçerse geçsin, HER birinin hemen önünde
    `pl.refetch_max != null &&` koruması vardır. `Number(null)` 0 olduğundan koruma yoksa
    `refetch_max: null` geldiğinde tavan 0 SANILIR ("0 deneme", oran Infinity) — doğru desen
    dosyada zaten (9090 civarı) örnektir, diğer geçişler ona hizalanır."""
    app = (WEB / "app.js").read_text()
    desen = re.compile(r"Number\.isFinite\(Number\(pl\.refetch_max\)\)")
    bulunanlar = list(desen.finditer(app))
    assert bulunanlar, "refetch_max isFinite deseni app.js'te YOK — dosya değişti mi?"
    for m in bulunanlar:
        onceki = app[max(0, m.start() - 40):m.start()]
        assert "pl.refetch_max != null &&" in onceki, (
            f"konum {m.start()} korumasız: Number(null)==0 olduğundan tavan 0 SANILIR — "
            "önüne `pl.refetch_max != null &&` eklenmeli"
        )


def test_d_api_diagnostics_refetch_max_scheduler_ile_ESIT(sandbox_state, monkeypatch):
    """(d) api'nin ürettiği plan yükünde `refetch_max` == `scheduler.DENSE_ATTEMPTS` —
    `/api/diagnostics` gerçekten bu alanı `_sched_mod.DENSE_ATTEMPTS`ten okuyor (ölçülebilir yol
    VAR: `test_defter_kaynak_damgasi_v140.py::client` fikstürünün aynısı)."""
    from fastapi.testclient import TestClient

    from meridian import api
    monkeypatch.setattr(api, "DASH_TOKEN", "")
    client = TestClient(api.app)
    yuk = client.get("/api/diagnostics?taze=1").json()
    assert yuk["pipeline"]["refetch_max"] == scheduler.DENSE_ATTEMPTS == 8


# =================================================================================================
# TSK-173(a) — 'yanıt var ama equity yok' sessiz 100k KAPATILDI
# =================================================================================================

@pytest.fixture
def mirror_ortami(sandbox_state, monkeypatch):
    """`mirror_submit_armed`ı çağrılabilir kılar: sahte Alpaca kimliği + saat pencere İÇİNE
    donar (emsal: `tests/test_kovab_icra_v161.py::paper`) — bu dosyanın çivileri gönderim
    MEKANİĞİNİ değil equity-okuma DALINI ölçer, pencerenin kendisini değil."""
    from meridian import secrets as secrets_mod
    monkeypatch.setenv("ALPACA_PAPER_KEY", FAKE_KEY)
    monkeypatch.setenv("ALPACA_PAPER_SECRET", FAKE_SECRET)
    monkeypatch.delenv("MERIDIAN_GCP_PROJECT", raising=False)
    secrets_mod.clear_cache()
    monkeypatch.setattr(config, "BROKER", "alpaca_paper")
    alpaca._note(True)
    _bc.set_clock(lambda: _dt.datetime(2026, 9, 3, 14, 0, tzinfo=_dt.timezone.utc))
    yield sandbox_state
    _bc.reset_clock()
    secrets_mod.clear_cache()
    alpaca._note(True)


def _broker_reject_olaylari():
    return [e for e in store.read_jsonl("events.jsonl")
            if obs.ALARM_BROKER_REJECT in str(e.get("event"))]


def test_a_equity_alani_yok_ALARM_ve_100k_YOK(mirror_ortami, monkeypatch):
    """(a) `alpaca.account` → `{"cash": "1"}` (equity YOK) ⇒ ALARM_BROKER_REJECT olayı events'te,
    `_MirrorUnreachable` sınıfı davranış (planlar silahlı kalır, gönderim yok), 100k ile
    boyutlandırılmış plan YOK."""
    gonderilen: list = []
    monkeypatch.setattr(alpaca, "account", lambda: {"cash": "1"})
    monkeypatch.setattr(alpaca, "submit_plan",
                        lambda *a, **k: gonderilen.append(1) or {"ok": True})
    meta = {"armed": [{"id": "P-1", "ticker": "T0", "entry_trigger": 10.0}],
            "peak_equity": 100_000.0}

    out = loop.mirror_submit_armed(meta, "2026-09-03", eq_now=100_000.0, halted=False)

    assert out["ok"] is False and out.get("unreachable") is True
    assert out["equity"] is None, "equity okunamazken SESSİZCE bir sayıya (100k) düştü"
    assert gonderilen == [], "equity okunamazken hayali sermaye (100k) üzerinden emir gitti"
    assert len(meta["armed"]) == 1, "ret planı silahlı kümeden düşürdü"
    olaylar = _broker_reject_olaylari()
    assert olaylar, "equity okunamama bir ALARM_BROKER_REJECT olayı ÜRETMEDİ"
    assert olaylar[-1].get("keys") == ["cash"], olaylar[-1]


def test_b_equity_float_cevrilemiyor_ALARM_ve_100k_YOK(mirror_ortami, monkeypatch):
    """(b) `alpaca.account` → `{"equity": "abc"}` ⇒ aynı muamele (alan VAR ama sayıya çevrilemiyor)."""
    gonderilen: list = []
    monkeypatch.setattr(alpaca, "account", lambda: {"equity": "abc"})
    monkeypatch.setattr(alpaca, "submit_plan",
                        lambda *a, **k: gonderilen.append(1) or {"ok": True})
    meta = {"armed": [{"id": "P-1", "ticker": "T0", "entry_trigger": 10.0}],
            "peak_equity": 100_000.0}

    out = loop.mirror_submit_armed(meta, "2026-09-03", eq_now=100_000.0, halted=False)

    assert out["ok"] is False and out.get("unreachable") is True
    assert out["equity"] is None, "equity 'abc'ten SESSİZCE bir sayıya (100k) düştü"
    assert gonderilen == [], "equity okunamazken hayali sermaye (100k) üzerinden emir gitti"
    assert len(meta["armed"]) == 1, "ret planı silahlı kümeden düşürdü"
    olaylar = _broker_reject_olaylari()
    assert olaylar, "equity okunamama (float hatası) bir ALARM_BROKER_REJECT olayı ÜRETMEDİ"
    assert olaylar[-1].get("keys") == ["equity"], olaylar[-1]


def test_c_equity_normal_POZITIF_KONTROL(mirror_ortami, monkeypatch):
    """(c) `alpaca.account` → `{"equity": "50000"}` ⇒ NORMAL yol (regresyon) — okunabilir bir
    equity gönderimi engellemez, alarm ÜRETİLMEZ. Pozitif kontrol: (a)/(b) 'bulamadığı için değil,
    gerçekten equity kırık olduğu için' kırmızı."""
    gonderilen: list = []
    monkeypatch.setattr(alpaca, "account", lambda: {"equity": "50000"})
    monkeypatch.setattr(alpaca, "submit_plan",
                        lambda *a, **k: gonderilen.append(1) or {"ok": True, "qty": 1,
                                                                 "law": {"limit": 10.1,
                                                                         "mode": "stop_limit",
                                                                         "tif": "day"}})
    meta = {"armed": [{"id": "P-1", "ticker": "T0", "entry_trigger": 10.0}],
            "peak_equity": 100_000.0}

    out = loop.mirror_submit_armed(meta, "2026-09-03", eq_now=100_000.0, halted=False)

    assert out["ok"] is True, out
    assert out["equity"] == pytest.approx(50_000.0)
    assert gonderilen == [1], "okunabilir equity ile gönderim GİTMEDİ"
    assert not _broker_reject_olaylari(), "normal yolda gereksiz BROKER_REJECT alarmı"


def test_loop_kaynaginda_ulasilamadi_esittir_100k_degil_ilkesi_iki_dal_tasir():
    """Yapısal çivi: yorum bloğu ('ULAŞILAMADI ≠ 100k') artık İKİ dalı da anlatıyor ve eski
    `else START_EQUITY` düşümü ayna gönderim yolundan KALKMIŞ (emsal:
    `tests/test_alpaca_audit_v16.py::test_a1_unreachable_broker_keeps_plans_armed`'ın kaynak-metni
    deseni)."""
    src = inspect.getsource(loop.mirror_submit_armed)
    assert src.count("ULAŞILAMADI") >= 2, "TSK-173a dalı yorum-anlatıya EKLENMEDİ"
    assert 'else START_EQUITY' not in src, "eski sessiz 100k düşümü hâlâ kodda duruyor"
    assert "_MirrorUnreachable" in src
