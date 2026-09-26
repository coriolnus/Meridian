"""test_ogrenme_canlilik_v555.py — TSK-204: "ÖĞRENME DURDU" alarmı özgün tasarımına ve yansıma kapısına hizalanır.

KUSUR (ölçüldü A1, Rol-1, 2026-09-25): `watchdog._learning_liveness` YALNIZ `hypotheses.jsonl`in en taze
`ts`ini 7 günle kıyaslıyordu. Yansıma (`hermes_runtime._run`) ise `n − last_reflect_at ≥ reflection_every`
∧ canlı-rejim ufku (`_horizon_ok`) sağlanınca koşar; kapanış akışı ~1/2 gün iken yansıma ~10 günde bir →
alarm YAPISAL olarak her gün öter (canlıda kapı 1/5 iken 35,1 gün "DURDU"). Özgün tasarım (2026-09-02,
Hindsight recall meridian-arsiv): "son 7 günde yeni hipotez + dolgulanan görüş; ikisi de 0 ise stalled" —
uygulama görüş kolunu hiç almamıştı.

YENİ TETİK (Rol-1 kararı, 2026-09-25) — alarm YALNIZ iki hâlde:
  (A) VADE DOLDU AMA YANSIMA YOK — kapı `hermes_runtime.yansima_kapisi()`ten okunur (tek kaynak; bekleme
      döngüsü aynı `_yansima_vadesi` yüklemiyle ateşler) ve vade 7 günden uzun sürüyor. Vadenin başladığı
      an = vadeyi dolduran kapanışın damgası; ölçülemezse en taze hipotez yaşı VEKİLdir (beyan söyler).
  (B) TAM SESSİZLİK — son 7 günde NE yeni hipotez NE görüş dolgusu (`plan_atif.jsonl`, `backfill=true`).
Aksi hâlde `ok: True` ve beyan BİLGİ taşır (kapı ilerlemesi, hipotez yaşı, görüş dolgusu, son ısınma).
Ölçülemeyen kol None + neden; ölçülemezlik 'taze' DEMEZ.

SAAT ÇİVİLİDİR: `watchdog._now` monkeypatch'lenir. `hermes_runtime._state`/`_thread` her testte tazelenir
(komşu testlerin `_record` artığı `last_reflect_at`ı kirletmesin).
"""
from __future__ import annotations

import calendar
import datetime as dt
import inspect

import pytest

from meridian import config, hermes_runtime, obs, store, watchdog

# 2026-09-25T22:00:00Z — Rol-1'in canlı ölçüm anı (gün ortası değil ama hiçbir hesap gün sınırına bakmaz).
T0 = float(calendar.timegm((2026, 9, 25, 22, 0, 0, 0, 0, 0)))
GUN_S = 86400.0
CANLI_REJIM = "trend_up"          # duraklatılmış rejim (chop) DEĞİL — kapı tartışmasına bulaşmasın


@pytest.fixture
def saat(monkeypatch):
    """`watchdog._now` çivili; testler `saat.t`yi taban alır."""
    class _Saat:
        t = T0
    s = _Saat()
    monkeypatch.setattr(watchdog, "_now", lambda: s.t)
    return s


@pytest.fixture
def alarmlar(monkeypatch):
    """`obs.alarm` çağrılarını dict olarak yakalar (jeton + mesaj + alanlar)."""
    kayit: list[dict] = []
    monkeypatch.setattr(obs, "alarm",
                        lambda tok, msg, **kw: kayit.append({"tok": tok, "msg": msg, **kw}))
    return kayit


@pytest.fixture(autouse=True)
def _temiz(monkeypatch):
    """Mandal ve hermes süreç-içi durumu testler arası TAŞINMASIN. `_state` taze bir kopyayla değişir:
    komşu bir testin `_record`u `last_reflect_at`ı bellekte bırakabilir ve kapı tabanı disk yerine
    ondan okunurdu (status() ile aynı taban kuralı: süreç-içi değilse {**_state, **disk})."""
    watchdog._LIVENESS_ALARMED.clear()
    monkeypatch.setattr(hermes_runtime, "_state", {"reflections": 0, "last_reflect_at": None})
    monkeypatch.setattr(hermes_runtime, "_thread", None)
    yield
    watchdog._LIVENESS_ALARMED.clear()


def _iso(t: float) -> str:
    return dt.datetime.fromtimestamp(t, dt.timezone.utc).isoformat(timespec="seconds")


def _hyps(saat, yaslar_sa: list[float]) -> None:
    """Hipotezleri verilen YARATILMA yaşlarıyla (saat) yaz — `ts` kayıt damgası (memory.record)."""
    store.write_jsonl("hypotheses.jsonl",
                      [{"variable": f"v{i}", "status": "proposed", "ts": _iso(saat.t - a * 3600)}
                       for i, a in enumerate(yaslar_sa)])


def _gorus(saat, yaslar_sa: list[float], *, backfill: bool = True) -> None:
    """`plan_atif.jsonl` satırları (sözleşme alanlarının tamamı) — `ts` damga anı, `backfill` dolgu işareti."""
    store.write_jsonl("plan_atif.jsonl", [
        {"ts": _iso(saat.t - a * 3600), "plan_id": f"P{i}", "ticker": "AAA", "plan_date": "2026-03-02",
         "kind": "backfill" if backfill else "review", "model": "m", "model_olculemedi": None,
         "model_kaynagi": "cevap_veren", "model_istenen": "m", "iz_id": None, "backfill": backfill}
        for i, a in enumerate(yaslar_sa)])


def _kapi(saat, yeni_gun_once: list, *, taban: int = 10, isinma: dict | None = None) -> None:
    """Kapıyı kur: `taban` kadar ESKİ kapanış (son yansımadan önce) + verilen yaşlarda (gün) YENİ
    kapanışlar, canlı rejimde. `None` yaş = damgasız kapanış (ts_close/ts_open yok).
    `hermes_status.json` `last_reflect_at = taban` — bekleme döngüsünün kalıcı tabanı."""
    eski = [{"id": f"E{i}", "regime": CANLI_REJIM, "r_multiple": 0.1,
             "ts_close": _iso(saat.t - (200 + i) * GUN_S)} for i in range(taban)]
    yeni = []
    for i, g in enumerate(yeni_gun_once):
        satir = {"id": f"Y{i}", "regime": CANLI_REJIM, "r_multiple": 0.1}
        if g is not None:
            satir["ts_close"] = _iso(saat.t - g * GUN_S)
        yeni.append(satir)
    store.write_jsonl("trades.jsonl", eski + yeni)
    store.write_json("regime.json", {"regime": CANLI_REJIM})
    durum = {"last_reflect_at": taban}
    if isinma is not None:
        durum["last_warmup"] = isinma
    store.write_json("hermes_status.json", durum)


def _ogrenme_alarmlari(alarmlar: list[dict]) -> list[dict]:
    return [a for a in alarmlar if a["tok"] == "MECHANISM_STALE" and a.get("kind") == "learning_stalled"]


# =================================================================================================
# (1) CANLI VAKA — kapı 1/5, hipotez 35 gün eski, görüş dolgusu son 7 günde VAR → alarm YOK
# =================================================================================================
def test_1_kapi_bekliyor_gorus_dolgusu_var_ALARM_YOK(sandbox_state, saat, alarmlar):
    """Bugünkü canlı hâl: yansıma kapısı TASARIM GEREĞİ bekliyor (1/5), görüş dolgusu işliyor. Eski
    kod bunu 35,1 gündür "DURDU" diye çalıyordu; yeni tetikte (A) yok (vade dolmadı), (B) yok (dolgu var)."""
    _kapi(saat, [3.0], isinma={"at": _iso(saat.t - 2 * 3600), "evaluated": 10, "cleared": 0})
    _hyps(saat, [35.1 * 24, 40 * 24])
    _gorus(saat, [5, 30, 70])
    lr = watchdog._learning_liveness()
    assert lr["ok"] is True and lr["stalled"] is False, lr
    # BEYAN BİLGİ TAŞIR: kapı ilerlemesi, hipotez yaşı, görüş dolgusu, son ısınma.
    assert "1/5" in lr["beyan"], lr["beyan"]
    assert lr["kapi"]["vade_doldu"] is False and lr["kapi"]["ilerleme"] == "1/5"
    assert lr["hipotez_7g"] == 0 and lr["age_h"] == pytest.approx(35.1 * 24, abs=0.1)
    assert lr["gorus_dolgusu_7g"] == 3
    assert lr["son_isinma"]["evaluated"] == 10 and lr["son_isinma"]["cleared"] == 0
    assert "ısınma" in lr["beyan"] and "görüş dolgusu" in lr["beyan"]
    watchdog.check_liveness_and_alarm()
    assert _ogrenme_alarmlari(alarmlar) == []


# =================================================================================================
# (2) (A) VADE DOLDU AMA YANSIMA YOK
# =================================================================================================
def test_2_vade_8_gundur_dolu_yansima_yok_ALARM_A(sandbox_state, saat, alarmlar):
    """Kapı 5/5 + ufuk ≥30 gün (canlı rejimde) 8 gün önce doldu, o günden beri yansıma yok (taban
    ilerlemedi) ve 8 gündür hipotez yok. Görüş dolgusu VAR — yani alarmı (B) değil (A) çalar."""
    _kapi(saat, [68, 50, 30, 20, 8])
    _hyps(saat, [8 * 24])
    _gorus(saat, [10])
    lr = watchdog._learning_liveness()
    assert lr["stalled"] is True and lr["ok"] is False, lr
    assert lr["ayak"] == ["A"], lr["ayak"]
    assert lr["kapi"]["vade_doldu"] is True and lr["kapi"]["ilerleme"] == "5/5"
    assert lr["kapi"]["vade_kaynagi"] == "kapanis_damgasi"
    assert lr["kapi"]["vade_yas_h"] == pytest.approx(8 * 24, abs=0.1)
    assert "DURDU" in lr["beyan"] and "5/5" in lr["beyan"]
    watchdog.check_liveness_and_alarm()
    ogr = _ogrenme_alarmlari(alarmlar)
    assert len(ogr) == 1 and not ogr[0].get("olculemedi")
    watchdog.check_liveness_and_alarm()                 # hâl sürüyor → mandal susturur
    assert len(_ogrenme_alarmlari(alarmlar)) == 1


def test_2b_vade_baslangici_olculemez_HIPOTEZ_YASI_VEKIL(sandbox_state, saat):
    """Vadeyi dolduran kapanış damgasız (ts_close/ts_open yok) → vadenin başladığı an ÖLÇÜLEMEZ; en
    taze hipotez yaşı VEKİL olur ve beyan bunu SÖYLER (8 gün > 7 → alarm)."""
    _kapi(saat, [68, 50, 30, 20, None])
    _hyps(saat, [8 * 24])
    _gorus(saat, [10])
    lr = watchdog._learning_liveness()
    assert lr["kapi"]["vade_doldu"] is True
    assert lr["kapi"]["vade_kaynagi"] == "hipotez_yasi_vekil"
    assert lr["stalled"] is True and lr["ayak"] == ["A"]
    assert "vekil" in lr["beyan"]


def test_2c_vade_yeni_doldu_hipotez_eski_ALARM_YOK(sandbox_state, saat, alarmlar):
    """Vade DÜN doldu (yansıma bir sonraki poll'da ya da şu an koşan 1-3 saatlik aramada) — hipotez
    35 gün eski olsa da bu bir durma DEĞİL. Vekil yalnız vade anı ölçülemezse devreye girer; ölçülen
    vade anı varken hipotez yaşı (A)'ya sızarsa her normal yansıma bir yanlış alarm üretirdi."""
    _kapi(saat, [68, 50, 30, 20, 1])
    _hyps(saat, [35.1 * 24])
    _gorus(saat, [10])
    lr = watchdog._learning_liveness()
    assert lr["kapi"]["vade_doldu"] is True and lr["kapi"]["vade_kaynagi"] == "kapanis_damgasi"
    assert lr["ok"] is True and lr["stalled"] is False, lr
    watchdog.check_liveness_and_alarm()
    assert _ogrenme_alarmlari(alarmlar) == []


# =================================================================================================
# (3) (B) TAM SESSİZLİK
# =================================================================================================
def test_3_kapi_bekliyor_8_gundur_ne_hipotez_ne_gorus_ALARM_B(sandbox_state, saat, alarmlar):
    """Kapı 1/5 (vade yok) ama son 7 günde ne yeni hipotez ne görüş dolgusu → 02 Eylül tasarımı: durdu."""
    _kapi(saat, [3.0])
    _hyps(saat, [8 * 24])
    _gorus(saat, [9 * 24])                              # dolgu var ama pencere DIŞINDA
    lr = watchdog._learning_liveness()
    assert lr["stalled"] is True and lr["ok"] is False, lr
    assert lr["ayak"] == ["B"]
    assert lr["hipotez_7g"] == 0 and lr["gorus_dolgusu_7g"] == 0
    assert "DURDU" in lr["beyan"]
    watchdog.check_liveness_and_alarm()
    assert len(_ogrenme_alarmlari(alarmlar)) == 1


def test_3b_canli_inceleme_gorusu_DOLGU_SAYILMAZ(sandbox_state, saat):
    """Görüş kolu DOLGUYU sayar (`backfill=true`): karar-anı inceleme görüşü (`backfill=false`) bir
    dolgu değildir — sayılsaydı 02 Eylül tasarımının "dolgulanan görüş" kolu sessizce genişlerdi."""
    _kapi(saat, [3.0])
    _hyps(saat, [8 * 24])
    _gorus(saat, [5, 10], backfill=False)
    lr = watchdog._learning_liveness()
    assert lr["gorus_dolgusu_7g"] == 0
    assert lr["stalled"] is True and lr["ayak"] == ["B"]


# =================================================================================================
# (4) GÖRÜŞ KAYNAĞI OKUNAMIYOR → ÖLÇÜLEMEDİ, 'taze' DEMEZ
# =================================================================================================
def _plan_atif_okunamaz(monkeypatch):
    gercek = store.read_jsonl

    def _oku(name, *a, **k):
        if name == "plan_atif.jsonl":
            raise OSError("disk okunamadı")
        return gercek(name, *a, **k)
    monkeypatch.setattr(store, "read_jsonl", _oku)


def test_4_gorus_kaynagi_okunamiyor_OLCULEMEDI(sandbox_state, saat, alarmlar, monkeypatch):
    """Hipotez 35 gün eski, kapı 1/5, görüş defteri okunamıyor → (B) hükümsüz: ok None + neden.
    'taze'/'ilerliyor' DEMEZ; alarm geçişi kendi ÖLÇÜLEMEDİ jetonuyla duyurur (durma alarmı değil)."""
    _kapi(saat, [3.0])
    _hyps(saat, [35.1 * 24])
    _plan_atif_okunamaz(monkeypatch)
    lr = watchdog._learning_liveness()
    assert lr["ok"] is None and lr["olculemedi"] is True, lr
    assert lr["stalled"] is False
    assert lr["gorus_dolgusu_7g"] is None and lr["gorus_neden"]
    assert lr["neden"] and "ÖLÇÜLEMEDİ" in lr["beyan"]
    assert "ilerliyor" not in lr["beyan"] and "taze" not in lr["beyan"].replace("'taze' DEMEZ", "")
    watchdog.check_liveness_and_alarm()
    ogr = _ogrenme_alarmlari(alarmlar)
    assert len(ogr) == 1 and ogr[0].get("olculemedi") is True


def test_4b_gorus_okunamiyor_ama_hipotez_taze_OK(sandbox_state, saat, monkeypatch):
    """Üç değerli mantık: taze hipotez (B)'yi TEK BAŞINA yanlışlar — görüş kolu ölçülemese de hüküm
    verilebilir. Ölçülemeyen kol yine None + neden taşır (gizlenmez)."""
    _kapi(saat, [3.0])
    _hyps(saat, [48])
    _plan_atif_okunamaz(monkeypatch)
    lr = watchdog._learning_liveness()
    assert lr["ok"] is True and lr["stalled"] is False, lr
    assert lr["gorus_dolgusu_7g"] is None and lr["gorus_neden"]


# =================================================================================================
# (5) HİÇ HİPOTEZ YOK → 'starved' ayrımı korunur
# =================================================================================================
def test_5_hic_hipotez_yok_STARVED_korunur(sandbox_state, saat, alarmlar):
    """Hiç hipotez yok = 'durdu' DEĞİL (hiç başlamadı; production 'starved' der) — vade dolu olsa bile."""
    _kapi(saat, [68, 50, 30, 20, 8])
    store.write_jsonl("hypotheses.jsonl", [])
    lr = watchdog._learning_liveness()
    assert lr["stalled"] is False and lr["n"] == 0 and "hiç başlamadı" in lr["beyan"]
    watchdog.check_liveness_and_alarm()
    assert _ogrenme_alarmlari(alarmlar) == []


# =================================================================================================
# TEK-KAYNAK — kapı hermes_runtime'ın KENDİ fonksiyonundan okunur, bekçi ikinci bir kapı yazmaz
# =================================================================================================
def test_TK1_bekci_kapiyi_yansima_kapisi_SEMBOLUNDEN_okur(sandbox_state, saat, monkeypatch):
    """`hermes_runtime.yansima_kapisi` sentetik bir hâl dönerse bekçinin hükmü ve beyanı ONU izler —
    bekçi kendi defter okumasıyla kapı hesaplasaydı (ikinci uygulama) bu test düşerdi."""
    _hyps(saat, [9 * 24])
    _gorus(saat, [10])
    sentetik = {"reflection_every": 7, "trades_since_last_reflection": 9, "trades_until_next": 0,
                "closed_trades": 30, "last_reflect_at": 21, "vade_doldu": True,
                "vade_ts": _iso(saat.t - 10 * GUN_S), "vade_ts_neden": None,
                "horizon": {"regime": CANLI_REJIM, "trades": 9, "trades_needed": 7, "span_days": 40,
                            "min_days": 30, "ready": True},
                "horizon_ready": True, "horizon_regime": CANLI_REJIM, "son_isinma": None}
    monkeypatch.setattr(hermes_runtime, "yansima_kapisi", lambda *a, **k: dict(sentetik))
    lr = watchdog._learning_liveness()
    assert lr["kapi"]["ilerleme"] == "9/7" and "9/7" in lr["beyan"]
    assert lr["stalled"] is True and lr["ayak"] == ["A"]
    assert lr["kapi"]["vade_yas_h"] == pytest.approx(240, abs=0.1)


def test_TK2_reflection_every_goaldan_gelir_SABIT_5_DEGIL(sandbox_state, saat, monkeypatch):
    """`reflection_every` goal.yaml'dan (hermes_runtime'ın okuduğu yer) gelir: 3'e çekilince 3 yeni
    kapanış vadeyi doldurur. Sabit 5 ya da başka bir kaynak okuyan bekçi "3/5" der ve susardı."""
    # goal sarmalayıcısı DEĞİL alttaki önbellek yamalanır: sandbox_state sökülürken sarmalayıcının
    # önbellek-temizleme kancasını çağırır ve yama o anda hâlâ yerindedir (fikstür sökümü monkeypatch
    # geri alımından ÖNCE koşar) — lambda o kancayı taşımazdı.
    gercek = config.goal()
    monkeypatch.setattr(config, "_goal_cached", lambda: {**gercek, "reflection_every": 3})
    _kapi(saat, [60, 30, 8])
    _hyps(saat, [8 * 24])
    _gorus(saat, [10])
    lr = watchdog._learning_liveness()
    assert lr["kapi"]["ilerleme"] == "3/3", lr["kapi"]
    assert lr["kapi"]["vade_doldu"] is True
    assert lr["stalled"] is True and lr["ayak"] == ["A"]


def test_TK3_dongu_ve_rapor_AYNI_yuklemi_kullanir():
    """Bekleme döngüsü yansımayı `_yansima_vadesi` ile ATEŞLER; `yansima_kapisi` (pano + bekçi) 'vade
    doldu'yu AYNI yüklemle söyler. Döngüde satır-içi ikinci bir koşul (`n - last_at >= every`) kalırsa
    iki tanım sessizce ayrışabilirdi. Bekçi gövdesi kapı hesabının hiçbir parçasını TAŞIMAZ."""
    run_src = inspect.getsource(hermes_runtime._run)
    assert "_yansima_vadesi(trades, last_at, every, live_reg)" in run_src
    assert "n - last_at >= every" not in run_src
    assert "_yansima_vadesi(" in inspect.getsource(hermes_runtime.yansima_kapisi)
    wd_src = "".join(inspect.getsource(f) for f in (watchdog._learning_liveness,
                                                     watchdog._yansima_ayagi,
                                                     watchdog._gorus_dolgusu_kolu))
    # ÇAĞRI/LİTERAL biçimleri aranır (docstring'deki ad anışları kod değildir).
    for yasak in ("_horizon_ok(", "_horizon_progress(", "_yansima_vadesi(", '"trades.jsonl"',
                  '"regime.json"', '"hermes_status.json"', "goal()"):
        assert yasak not in wd_src, f"bekçi kapıyı kendisi hesaplıyor: {yasak!r}"
    assert "_hr.yansima_kapisi()" in wd_src


def test_TK4_status_geri_sayimi_yansima_kapisi_ile_AYNI(sandbox_state, saat):
    """Pano geri sayımı (`status()`) ve bekçinin kapısı aynı hesaptan: alanlar birebir eşit."""
    _kapi(saat, [68, 50, 30])
    st = hermes_runtime.status()
    k = hermes_runtime.yansima_kapisi()
    for alan in ("reflection_every", "closed_trades", "trades_since_last_reflection",
                 "trades_until_next", "horizon", "horizon_ready", "horizon_regime"):
        assert st[alan] == k[alan], alan
    assert k["trades_since_last_reflection"] == 3 and k["vade_doldu"] is False
