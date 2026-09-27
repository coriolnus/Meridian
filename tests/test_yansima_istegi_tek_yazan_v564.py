"""test_yansima_istegi_tek_yazan_v564.py — TSK-233: öğrenme durumunun TEK yazanı; pano "düşün" düğmesi yansımayı
öğrenme sürecine DEVREDER.

BULGU (TSK-229 kaygı-1; inceleme + Rol-1 kod okumasıyla doğruladı, 2026-09-26): `api.api_hermes_reflect` →
`hermes_runtime.reflect_now()` PANO sürecinde (`meridian.service`) iş parçacığı açıp `hermes.reflect_once()` koşuyordu ve
`_persist` ile `hermes_status.json`un TAMAMINI o sürecin boş `_state`inden yazıyordu. Öğrenme döngüsü AYRI süreçtir
(`meridian-learn`). Sonuç: (1) `last_reflect_at` None yazılır → öğrenme sürecinin sonraki restart'ında `_restored_baseline`
defter ucuna düşer (TSK-227'nin kapattığı sıfırlama başka yoldan); `bg_reflect_by_regime` ve `kalp` silinir; (2)
`_reflect_lock` süreç-başı → iki süreç AYNI ANDA iki yansıma koşabilir; (3) ağır walk-forward pano sürecinde koşar (Ö-50).

KARAR (Rol-1, 2026-09-26; emsal: 2026-09-05 start/stop düğmelerinin `meridian-learn`e devri — `api._ogrenme_kumanda`):
  * PANO UCU yansımayı KOŞMAZ, durum dosyasına YAZMAZ: istek dosyası bırakır (`hermes_runtime.YANSIMA_ISTEGI_FILE`, atomik
    `store.write_json`) + `hermes_yansima_istegi` olayı. Bekleyen istek ya da süren yansıma → "busy". Öğrenme döngüsü poll
    etmiyorsa (kalp bayat — eşik `KALP_PAY × poll_seconds`, `_kalp_canliligi`in TEK kuralı) AÇIK ret, istek BIRAKILMAZ.
  * ÖĞRENME DÖNGÜSÜ poll'unda isteği görür, KENDİ `_reflect_lock`u altında elle yansıma gövdesini (`arka_plan=False`)
    koşar, isteği siler, alınış olayını gecikmeyle yazar. Kilit doluysa istek BEKLER (kaybolmaz).
  * Ufuk-kapısı atlama notu korunur: pano yanıtında VE öğrenme tarafındaki yansıma kaydında.

İKİ ROL, İKİ FİKSTÜR: `pano` → bu süreçte döngü YOK (`_thread` None), `_state` import-anı hâli; öğrenme sürecinin diske
yazdığı durum sahnelenir. `ogrenme` → bekleme döngüsü (`_run`) GERÇEKTEN koşar (gerçek `_persist`, sahte yansıma; tur sayısı
v560'ın adımlı durdurucusuyla). Öğrenme tarafındaki istekler GERÇEK pano ucuyla bırakılır — sözleşmenin iki ucu aynı
çivide buluşur, istek biçimi testte ikinci kez yazılmaz (tek kaynak).
"""
from __future__ import annotations

import ast
import datetime as dt
import pathlib
import threading
import types

import pytest

from meridian import api, codelaw, config, health, hermes, store, watchdog
from meridian import hermes_runtime as hr
from tests.test_bg_taban_geri_yukleme_v562 import _ilk_state
from tests.test_yansima_taban_v560 import TABAN, CANLI, _AdimliDurdurucu, _birikmis, _canli, _defter_n, _every

POLL = 300                                   # canlı `HERMES_POLL_SECONDS` varsayılanı (learn_run)
OLAY_ISTEK = "hermes_yansima_istegi"
OLAY_ALINDI = "hermes_yansima_istegi_alindi"
API_PY = pathlib.Path(api.__file__)

# Pano sürecinin DOKUNAMAYACAĞI semboller: yansımayı koşanlar ve `hermes_status.json`u yazanlar. `start`/`stop` bilerek
# listede YOK — süreç-içi kip (`MERIDIAN_AUTOSTART_HERMES=1`, yerel geliştirme) döngünün kendisini API sürecinde kurar ve
# o kipte döngü o süreçte TEK yazandır; yasak, döngüsü BAŞKA süreçte olan panonun yansıma/durum yazımıdır.
YASAKLI = frozenset({"reflect_now", "reflect_once", "_persist", "_record", "_elle_yansima_govdesi",
                     "_yansima_istegini_isle", "_kalp_vur", "_run"})
YAZIM_CAGRILARI = frozenset({"write_json", "update_json", "write_jsonl", "append_jsonl", "write_text"})


def _iso(saniye_once: float = 0.0) -> str:
    return (dt.datetime.now(dt.timezone.utc) - dt.timedelta(seconds=saniye_once)).isoformat(timespec="seconds")


def _olaylar(ad: str) -> list[dict]:
    return [e for e in store.read_jsonl("events.jsonl") if e.get("event") == ad]


def _istek():
    return store.read_json(hr.YANSIMA_ISTEGI_FILE, None)


def _durum_ham() -> bytes:
    return (config.STATE / hr.STATUS_FILE).read_bytes()


def _canli_ogrenme_diski(*, kalp_yasi_s: float = 5.0, n_canli: int | None = None) -> None:
    """Öğrenme sürecinin (başka süreç) diske yazmış olduğu hâl: canlı taban, arka plan tabanı, kalp, poll aralığı.
    Canlı sayaç `every - 2` → ufuk DOLMADI (elle tetikleme bunu bilerek atlar ve NOT düşer)."""
    every = _every()
    n_canli = every - 2 if n_canli is None else n_canli
    store.write_jsonl("trades.jsonl", _birikmis() + [_canli(i) for i in range(n_canli)])
    store.write_json("regime.json", {"regime": CANLI})
    store.write_json(hr.STATUS_FILE, {"last_reflect_at": TABAN, "bg_reflect_by_regime": {"trend_down": TABAN},
                                      "kalp": _iso(kalp_yasi_s), "last_poll": _iso(kalp_yasi_s),
                                      "poll_seconds": POLL, "reflections": 7})


class _EsZamanliIplik:
    """`threading.Thread` yerine: hedef AYNI iş parçacığında koşar — eski `reflect_now` yolu geri konursa sahte
    yansıma çağrısı çivinin içinde, belirlenimci biçimde görünür (mutasyon M1)."""

    def __init__(self, target=None, name=None, daemon=None, **_k):
        self._hedef = target

    def start(self) -> None:
        self._hedef()


def _ortak_sahteler(monkeypatch, cagrilar: list) -> None:
    """İki rolde de sahte olan DIŞ yüzeyler: yansımanın kendisi, beyin ölçümleri, öz-onarım eşitlemeleri, nabız."""
    monkeypatch.setattr(hr, "_brain", lambda: "deterministic")
    monkeypatch.setattr(hr, "_brain_availability", lambda: {})
    monkeypatch.setattr(hr, "_brain_chain", lambda: {})
    monkeypatch.setattr(hermes, "SEARCH_PROGRESS", {})             # süreç belleği: komşu testin artığı taşınmasın
    monkeypatch.setattr(hermes, "sync_agent_skills", lambda: {})
    monkeypatch.setattr(hermes, "config_ensure_integrations", lambda: {})
    monkeypatch.setattr(watchdog, "beat", lambda _ad: None)
    # İplik açan eski yol geri konursa sahte yansıma çivinin İÇİNDE koşsun (belirlenimci) ve iplik sızmasın.
    monkeypatch.setattr(hr, "threading", types.SimpleNamespace(Thread=_EsZamanliIplik, Lock=threading.Lock))

    def _sahte_yansima(target_regime="auto", *, background=False):
        cagrilar.append({"rejim": target_regime, "arka_plan": background, "defter": _defter_n()})
        return {"status": "rejected_by_backtest", "hypothesis": {"variable": "exit.trail_atr_mult"}}

    monkeypatch.setattr(hermes, "reflect_once", _sahte_yansima)


@pytest.fixture
def pano(sandbox_state, monkeypatch):
    """PANO SÜRECİ → `(bas, cagrilar)`: `bas()` gerçek `/api/hermes/reflect` ucunu çağırır (kimlik kapısı sahte)."""
    monkeypatch.setattr(hr, "_state", _ilk_state())
    monkeypatch.setattr(hr, "_thread", None)                        # döngü BU süreçte değil (meridian.service)
    monkeypatch.setattr(api, "_auth", lambda _r: None)
    cagrilar: list[dict] = []
    _ortak_sahteler(monkeypatch, cagrilar)

    def bas() -> dict:
        return api.api_hermes_reflect(types.SimpleNamespace())

    return bas, cagrilar


# =================================================================================================
# (1) PANO UCU yansıma KOŞMAZ, durum dosyasına YAZMAZ; istek dosyası + olay BIRAKIR; ufuk notu yanıtta
# =================================================================================================
def test_1_pano_ucu_yansima_KOSMAZ_durum_dosyasina_YAZMAZ_istek_ve_olay_BIRAKIR(pano):
    bas, cagrilar = pano
    _canli_ogrenme_diski()
    once = _durum_ham()
    out = bas()
    assert out["status"] == "queued", out
    assert cagrilar == [], f"pano süreci yansıma koştu: {cagrilar}"
    assert _durum_ham() == once, "pano süreci hermes_status.json'a YAZDI — öğrenme sürecinin kaydını ezdi"
    ist = _istek()
    assert isinstance(ist, dict) and ist.get("istek_id") and ist.get("istek_at") and ist.get("kaynak"), ist
    olay = _olaylar(OLAY_ISTEK)
    assert len(olay) == 1 and olay[0].get("istek_id") == ist["istek_id"] and olay[0].get("kaynak") == ist["kaynak"]
    # Ufuk-kapısı atlama notu KORUNUR (eski `reflect_now` yanıtıyla aynı metin): hem yanıtta hem istekte.
    assert out["horizon_ready"] is False and "ufuk kapısı" in out["detail"], out
    assert ist.get("ufuk_hazir") is False and "ufuk kapısı" in str(ist.get("ufuk_notu")), ist


# =================================================================================================
# (2) İKİNCİ İSTEK → MEŞGUL; bekleyen istek ezilmez, ikinci olay yazılmaz
# =================================================================================================
def test_2_bekleyen_istek_varken_ikinci_istek_MESGUL_istek_EZILMEZ(pano):
    bas, cagrilar = pano
    _canli_ogrenme_diski()
    assert bas()["status"] == "queued"
    ilk = _istek()
    out = bas()
    assert out["status"] == "busy" and out.get("neden") == "bekleyen_istek", out
    assert _istek() == ilk, "bekleyen istek ikinci tıklamayla ezildi"
    assert len(_olaylar(OLAY_ISTEK)) == 1
    assert cagrilar == []


# =================================================================================================
# (3) KALP BAYAT → AÇIK RET, istek BIRAKILMAZ (ölü kuyruk yok); hiç kayıt yoksa da ret
# =================================================================================================
def test_3_kalp_bayat_ACIK_RET_istek_BIRAKILMAZ(pano):
    bas, cagrilar = pano
    _canli_ogrenme_diski(kalp_yasi_s=hr.KALP_PAY * POLL + 60)       # eşiğin 60 sn ötesi
    once = _durum_ham()
    out = bas()
    assert out["status"] == "unavailable", out
    assert "öğrenme birimi çalışmıyor" in out["detail"] and "istek alınmadı" in out["detail"], out
    assert "eşik" in out["detail"], "ret, eşiği (KALP_PAY × poll) söylemiyor — neden okunmaz"
    assert _istek() is None, "ölü kuyruk: poll etmeyen döngüye istek bırakıldı"
    assert _olaylar(OLAY_ISTEK) == [] and cagrilar == []
    assert _durum_ham() == once


def test_3b_hic_durum_kaydi_yok_ACIK_RET(pano):
    bas, _cagrilar = pano
    store.write_jsonl("trades.jsonl", _birikmis())
    out = bas()
    assert out["status"] == "unavailable" and "istek alınmadı" in out["detail"], out
    assert _istek() is None and not (config.STATE / hr.STATUS_FILE).exists()


# =================================================================================================
# (4) BAŞKA SÜREÇTE YANSIMA SÜRÜYOR → MEŞGUL (kalp uzun aramada bayatlar, arama ilerlemesi tazedir)
# =================================================================================================
def test_4_ogrenme_surecinde_arama_suruyor_MESGUL_ve_status_reflecting(pano):
    bas, cagrilar = pano
    _canli_ogrenme_diski(kalp_yasi_s=hr.KALP_PAY * POLL + 600)      # uzun yansıma: poll dönmüyor
    store.write_json(hermes.SEARCH_PROGRESS_FILE, {"running": True, "phase": "probing", "i": 3, "total": 12,
                                                   "updated_at": _iso(30)})
    out = bas()
    assert out["status"] == "busy" and out.get("neden") == "yansima_suruyor", out
    assert _istek() is None and cagrilar == []
    # Panonun "düşünüyor…" göstergesi de AYNI olgudan okunur: süreç-dışında `reflecting` artık yalnız bu
    # sürecin kilidi değil (o, yansıma buradan taşındığından beri hep False'tu).
    st = hr.status()
    assert st["reflecting"] is True and st["active"] is True, (st["reflecting"], st["active"])


def test_4b_bayat_arama_bayragi_MESGUL_SAYILMAZ(pano):
    """SIGKILL'de `running=True` diskte DONAR (learn_run docstring'i). Donmuş bayrak düğmeyi sonsuza dek 'meşgul'e
    kilitlemez — tazelik ölçüsü kalbin payıdır; döngü de ölüyse açık ret."""
    bas, _cagrilar = pano
    _canli_ogrenme_diski(kalp_yasi_s=hr.KALP_PAY * POLL + 600)
    store.write_json(hermes.SEARCH_PROGRESS_FILE, {"running": True, "phase": "probing",
                                                   "updated_at": _iso(hr.KALP_PAY * POLL + 600)})
    out = bas()
    assert out["status"] == "unavailable", out
    assert hr.status()["reflecting"] is False


# =================================================================================================
# (5) SÜREÇ-İÇİ KİP (yerel geliştirme): döngü bu süreçte → kilit yetkili
# =================================================================================================
def test_5_surec_ici_kipte_kilit_doluyken_MESGUL_bosken_istek_BIRAKILIR(pano, monkeypatch):
    bas, cagrilar = pano
    store.write_jsonl("trades.jsonl", _birikmis())
    monkeypatch.setattr(hr, "_thread", types.SimpleNamespace(is_alive=lambda: True))
    hr._state.update(last_reflect_at=TABAN, poll_seconds=POLL)
    assert hr._reflect_lock.acquire(blocking=False)
    try:
        out = bas()
        assert out["status"] == "busy" and out.get("neden") == "yansima_suruyor", out
        assert _istek() is None
    finally:
        hr._reflect_lock.release()
    assert bas()["status"] == "queued"
    assert cagrilar == []


# =================================================================================================
# (6) SINIF ÇİVİSİ — api.py yansıma koşturan / durum dosyası yazan sembole DOKUNMAZ; istek dosyasının okuyucusu var
# =================================================================================================
def _yasakli_erisimler(kaynak: str) -> list[str]:
    """`kaynak` içinde YASAKLI sembole her erişim (çağrı, öznitelik referansı, içe aktarma) ve `hermes_status.json`a
    her `store` yazımı. Metin araması DEĞİL, AST: docstring/şerhteki anma ihlal sayılmaz, `getattr` dışı her
    erişim görünür."""
    bulgu: list[str] = []
    for n in ast.walk(ast.parse(kaynak)):
        if isinstance(n, ast.Attribute) and n.attr in YASAKLI:
            bulgu.append(f"{n.lineno}: .{n.attr}")
        elif isinstance(n, ast.Name) and n.id in YASAKLI:
            bulgu.append(f"{n.lineno}: {n.id}")
        elif isinstance(n, ast.ImportFrom):
            bulgu += [f"{n.lineno}: import {a.name}" for a in n.names if a.name in YASAKLI]
        elif isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr in YAZIM_CAGRILARI \
                and n.args:
            hedef = n.args[0]
            if (isinstance(hedef, ast.Constant) and hedef.value == hr.STATUS_FILE) or \
                    (isinstance(hedef, ast.Attribute) and hedef.attr == "STATUS_FILE"
                     and isinstance(hedef.value, ast.Name) and hedef.value.id == "hermes_runtime"):
                bulgu.append(f"{n.lineno}: {n.func.attr}({ast.unparse(hedef)})")
    return bulgu


def test_6_SINIF_api_py_yansima_kosturan_ya_da_durum_yazan_sembole_DOKUNMAZ():
    """Pano süreci öğrenme durumunun yazarı DEĞİLDİR. `reflect_now` bugün CLI/süreç-içi yol olarak yaşar ama pano ucu
    onu çağıramaz — yarın biri "hızlı yol" diye geri koyarsa bu çivi öter (M1)."""
    # POZİTİF KONTROL: tarayıcı üç ihlal biçimini de GÖRÜYOR (yoksa boş bulgu bir şey kanıtlamaz).
    ornek = ("from .hermes_runtime import reflect_now\n"
             "def f():\n    hermes_runtime.reflect_now()\n    store.write_json(hermes_runtime.STATUS_FILE, {})\n"
             "    store.write_json('hermes_status.json', {})\n")
    assert len(_yasakli_erisimler(ornek)) == 4, _yasakli_erisimler(ornek)
    assert _yasakli_erisimler("def f():\n    '''reflect_now anılır ama çağrılmaz'''\n") == []
    bulgu = _yasakli_erisimler(API_PY.read_text(encoding="utf-8"))
    assert bulgu == [], f"api.py pano sürecinde yansıma koşturuyor ya da durum dosyasına yazıyor: {bulgu}"


def test_6b_istek_dosyasinin_TEK_yazari_pano_OKUYUCUSU_ogrenme_dongusu():
    """Yasa 6 + tek-yazan: istek dosyasını yalnız pano ucu (api.py) yazar, öğrenme tarafı (hermes_runtime.py) okur.
    Beyan (`DECLARED_SINKS`) GEREKMEZ — okuyucu grafta görünür; muafiyet kapatılabilen yerde kullanılmaz."""
    g = codelaw.artifact_graph()["artifacts"].get(hr.YANSIMA_ISTEGI_FILE) or {}
    assert g.get("writers") == ["api.py"], g
    assert "hermes_runtime.py" in g.get("external_readers", []) and g.get("unread") is False, g
    assert hr.YANSIMA_ISTEGI_FILE not in codelaw.DECLARED_SINKS


# =================================================================================================
# ÖĞRENME SÜRECİ — bekleme döngüsü isteği alır
# =================================================================================================
@pytest.fixture
def ogrenme(sandbox_state, monkeypatch):
    """ÖĞRENME SÜRECİ → `(bas, kos, cagrilar)`. `kos(adimlar)` bekleme döngüsünü GERÇEKTEN koşar (gerçek `_persist`);
    `bas()` isteği GERÇEK pano ucuyla bırakır (o an diskte öğrenme sürecinin taze kalbi durur)."""
    monkeypatch.setattr(hr, "_state", _ilk_state())
    monkeypatch.setattr(hr, "_thread", None)
    monkeypatch.setattr(hr, "_acilis_senkron_calisti", True)        # açılış senkronu alt süreç koşturur — konu değil
    monkeypatch.setattr(api, "_auth", lambda _r: None)
    monkeypatch.setattr(health, "halted", lambda: False)
    monkeypatch.setattr(health, "stale", lambda *_a, **_k: False)
    monkeypatch.setattr(health, "learn_halted", lambda: False)
    monkeypatch.setenv("MERIDIAN_BG_REFLECT", "0")                  # arka plan ve ısınma dalı bu çivinin konusu değil
    monkeypatch.setenv("MERIDIAN_WARMUP_SPRINTS", "0")
    cagrilar: list[dict] = []
    _ortak_sahteler(monkeypatch, cagrilar)

    def bas() -> dict:
        out = api.api_hermes_reflect(types.SimpleNamespace())
        assert out["status"] == "queued", out
        return _istek()

    def kos(adimlar=()):
        monkeypatch.setattr(hr, "_stop", _AdimliDurdurucu(adimlar))
        hr._run(poll_seconds=POLL)
        assert not str(hr._state.get("last_result") or "").startswith("error"), hr._state.get("last_result")

    return bas, kos, cagrilar


# =================================================================================================
# (7) İSTEK ALINIR → TEK elle yansıma (`arka_plan=False`), canlı taban ilerler, istek silinir, alınış olayı + not
# =================================================================================================
def test_7_ogrenme_istegi_ALIR_elle_yansima_canli_taban_ILERLER_istek_SILINIR(ogrenme):
    bas, kos, cagrilar = ogrenme
    _canli_ogrenme_diski()
    n = _defter_n()
    ist = bas()
    kos()
    assert cagrilar == [{"rejim": "auto", "arka_plan": False, "defter": n}], cagrilar
    assert hr._state["last_reflect_at"] == n, "elle yansıma canlı geri sayımı taşımadı (davranış birebir değil)"
    assert _istek() is None, "işlenen istek silinmedi — bir sonraki poll aynı isteği yeniden koşar"
    olay = _olaylar(OLAY_ALINDI)
    assert len(olay) == 1, olay
    assert olay[0]["istek_id"] == ist["istek_id"] and olay[0]["istek_at"] == ist["istek_at"]
    assert olay[0]["kaynak"] == ist["kaynak"]
    assert isinstance(olay[0].get("gecikme_s"), (int, float)) and olay[0]["gecikme_s"] >= 0, olay[0]
    # Ufuk notu öğrenme tarafındaki YANSIMA KAYDINDA da korunur (olay + kalıcı durum).
    assert "ufuk kapısı" in str(olay[0].get("ufuk_notu")), olay[0]
    kayit = store.read_json(hr.STATUS_FILE, {}).get("son_elle_istek") or {}
    assert kayit.get("durum") == "bitti" and kayit.get("istek_id") == ist["istek_id"], kayit
    assert kayit.get("sonuc") == "rejected_by_backtest" and "ufuk kapısı" in str(kayit.get("ufuk_notu")), kayit
    # Öğrenme sürecinin kendi yazımı arka plan tabanını ve kalbi TAŞIYOR (pano ezmesi yok).
    disk = store.read_json(hr.STATUS_FILE, {})
    assert disk.get("bg_reflect_by_regime") == {"trend_down": TABAN} and disk.get("kalp"), disk


# =================================================================================================
# (8) ÇİFT YANSIMA YOK — tek istek; işlendiği süreç YENİDEN BAŞLASA da → TEK yansıma
# =================================================================================================
def test_8_tek_istek_yeniden_baslatmada_da_TEK_yansima(ogrenme, monkeypatch):
    """Silinmeyen istek, yeni süreçte (taze bellek — `son_elle_istek` yok) AYNI yansımayı yeniden koşar: günlük
    dağıtım restart'ı her seferinde bir elle yansıma üretirdi. Süreç A bir poll, süreç B iki poll koşar."""
    bas, kos, cagrilar = ogrenme
    _canli_ogrenme_diski()
    bas()
    kos()                                                            # süreç A: istek alınır, yansıma koşar
    monkeypatch.setattr(hr, "_state", _ilk_state())                  # süreç B: yeniden başlatma (taze bellek)
    kos([lambda: None])
    assert len(cagrilar) == 1, f"tek istek birden çok yansıma koşturdu: {cagrilar}"
    assert len(_olaylar(OLAY_ALINDI)) == 1


# =================================================================================================
# (9) KİLİT DOLUYKEN İSTEK BEKLER — kaybolmaz, kilit boşalınca alınır
# =================================================================================================
def test_9_kilit_doluyken_istek_BEKLER_kaybolmaz_bosalinca_ALINIR(ogrenme):
    bas, kos, cagrilar = ogrenme
    _canli_ogrenme_diski()
    ist = bas()
    goruldu: list[dict] = []

    def _tur1_sonu():
        goruldu.append({"istek": _istek(), "cagri": len(cagrilar), "olay": len(_olaylar(OLAY_ALINDI))})
        hr._reflect_lock.release()

    assert hr._reflect_lock.acquire(blocking=False)                  # başka bir yansıma kilidi tutuyor
    try:
        kos([_tur1_sonu])
    finally:
        if hr._reflect_lock.locked() and not goruldu:
            hr._reflect_lock.release()
    assert goruldu == [{"istek": ist, "cagri": 0, "olay": 0}], goruldu
    assert len(cagrilar) == 1 and cagrilar[0]["arka_plan"] is False, cagrilar
    assert _istek() is None and len(_olaylar(OLAY_ALINDI)) == 1


# =================================================================================================
# (10) SİLİNEMEYEN İSTEK aynı süreçte YENİDEN KOŞMAZ (kimlikle tanınır); ölü kuyruk sessiz değil
# =================================================================================================
def test_10_silinemeyen_istek_ayni_surecte_YENIDEN_KOSMAZ(ogrenme, monkeypatch):
    """Silme düşerse (izin/disk) kalan istek her poll'da yeni bir yansıma olurdu — CPU ve LLM bütçesi sonsuz döngüde.
    Kimlik (`istek_id`) `son_elle_istek` ile eşleşince ikinci yansıma koşmaz. Silme burada sahte olarak DÜŞÜRÜLÜR."""
    bas, kos, cagrilar = ogrenme
    _canli_ogrenme_diski()
    ist = bas()
    silme_denemesi: list[int] = []
    monkeypatch.setattr(hr, "_yansima_istegini_sil", lambda: silme_denemesi.append(1))
    kos([lambda: None, lambda: None])                                # üç poll
    assert len(cagrilar) == 1, f"silinemeyen istek yeniden koştu: {cagrilar}"
    assert _istek() == ist, "sahte düşen silme dosyayı silmiş olamaz — sahne kurulmadı"
    assert len(silme_denemesi) >= 3, "kalan istek için silme yeniden denenmiyor"
