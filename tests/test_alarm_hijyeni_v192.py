"""test_alarm_hijyeni_v192.py — MEKANİZMA-GECİKME ALARMININ İKİ HİJYEN KAPISI (2026-08-06).

CANLI KANIT (Rol-1, 24 saatlik alarm dağılımı): 130 alarmın ~112'si TEK cümleydi —
    MECHANISM_STALE  mekanizma gecikti: hermes_poll — 0.5-0.7 sa (pencere 0.5 sa)
Yanında 7× warmup_sprint (8,0-8,1 sa) ve 10× "sunucu ölü→keepalive". Yani operatörün telefonuna
düşen sinyalin ~%86'sı tek bir mekanizmanın pencere sınırındaki SALINIMIYDI; gerçek olan tek olay
(1× ROLLBACK v4→v3) o selin içinde kayboldu. ROADMAP WP-P'nin EEMUA 191 bütçesi ≤10 alarm/gün der.

İKİ AYRI KUSUR ÖLÇÜLDÜ, İKİSİ DE BURADA ÇİVİLENİR:

  (a) ASKIDA ≠ GECİKMİŞ. `hermes_poll` nabzı, hermes zinciri kota soğumasındayken (v188'in yazdığı
      `brain_cooldown.json`) ya da kimlik havuzu tükenmişken (`_pool_exhausted`) seyrekleşir:
      mekanizma ölü değil, sistemin KENDİ beyanıyla beklemeye alınmıştır. Emsal aynı dosyada:
      `production_report` kapı meta-kalibrasyonunu `askida` kovasına ayırır (WP-M). Askıda mekanizma
      `ok` da SAYILMAZ — panoda adıyla ve nedeniyle görünür, yalnız ALARM üretmez.
      FAIL-CLOSED: sonda düşerse askıda SAYILMAZ (alarm basılır) ve düşüş `obs.warn`a yazılır —
      "ölçemedim"i "meşru bekleme" saymak bekçinin var olma sebebini silerdi.

  (b) HİSTEREZİS + GÜNLÜK TEKİLLEŞTİRME. Mandal yalnız "şu an bayat olanlar"ı tutuyordu; pencere
      sınırında salınan mekanizma her toparlanışta mandaldan düşüp her yeniden aşımda YENİ alarm
      yazıyordu (çırpınma). Kural: aynı mekanizma, aynı UTC günü, en fazla `GUNLUK_ALARM_TAVANI`.
      Bastırılan satır SESSİZ DEĞİL: `watchdog_alarm_gunluk.json` sayacına yazılır ve `report()`
      onu dışarı verir — bastırma kayda geçmezse bekçi kendi körlüğünü hijyen sanardı.

SAAT ÇİVİLİDİR: gün sınırı testi gerçek duvar saatine bağlansaydı UTC 23:5x'te kırmızıya dönerdi
(2026-08-03 tarih-bağımlı fikstür dersi). `watchdog._now` monkeypatch'lenir; store'un kendi kilit
saati hiç değişmez.
"""
from __future__ import annotations

import calendar

import pytest

from meridian import obs, store, watchdog


# 2026-08-06T12:00:00Z — gün ortası: ileri/geri 6 saatlik oynatma gün sınırını kazara geçmez.
T0 = float(calendar.timegm((2026, 8, 6, 12, 0, 0, 0, 0, 0)))
GUN = 24 * 3600.0


@pytest.fixture
def saat(monkeypatch):
    """`watchdog._now` çivili; testler `saat.ileri(sn)` ile zamanı taşır."""
    class _Saat:
        def __init__(self) -> None:
            self.t = T0

        def ileri(self, saniye: float) -> None:
            self.t += float(saniye)

    s = _Saat()
    monkeypatch.setattr(watchdog, "_now", lambda: s.t)
    return s


@pytest.fixture
def alarmlar(monkeypatch):
    kayit: list[tuple[str, str | None]] = []
    monkeypatch.setattr(obs, "alarm",
                        lambda tok, msg, **kw: kayit.append((tok, kw.get("mechanism"))))
    return kayit


def _bayatla(saat, ad: str, yas_s: float) -> None:
    """Mekanizmanın nabzını `yas_s` saniye geriye koy (yalnız o mekanizma; diğerleri 'never')."""
    beats = store.read_json(watchdog.BEATS_FILE, {}) or {}
    beats[ad] = saat.t - yas_s
    store.write_json(watchdog.BEATS_FILE, beats)


def _tazele(saat, ad: str) -> None:
    beats = store.read_json(watchdog.BEATS_FILE, {}) or {}
    beats[ad] = saat.t
    store.write_json(watchdog.BEATS_FILE, beats)


def _sogumasiz(monkeypatch):
    """hermes askıda-sondasını 'bekleme yok' konumuna çiviler (varsayılan sandbox hâli zaten budur;
    test niyeti açıkça yazılsın diye ayrı yardımcı)."""
    monkeypatch.setattr(watchdog, "_hermes_askida", lambda: None)


# =================================================================================================
# (a) ASKIDA-FARKINDALIK
# =================================================================================================
def test_hermes_kota_sogumasinda_gecikti_alarmi_BASILMAZ(sandbox_state, saat, alarmlar, monkeypatch):
    """Canlı vakanın ta kendisi: hermes_poll penceresini aşmış ama beyin soğumada → askıda."""
    monkeypatch.setattr(watchdog, "_hermes_askida",
                        lambda: {"neden": "kota_sogumasi", "kalan_s": 1800.0,
                                 "detay": "beyin soğumada: gemini — 30.0 dk kaldı (rate_limit)"})
    _bayatla(saat, "hermes_poll", 0.7 * 3600)          # canlı defterdeki gap (pencere 0,5 sa)
    rep = watchdog.report()
    assert "hermes_poll" not in {x["name"] for x in rep["stale"]}
    askida = {x["name"]: x for x in rep["askida"]}
    assert "hermes_poll" in askida
    assert askida["hermes_poll"]["neden"] == "kota_sogumasi"
    assert askida["hermes_poll"]["gap_h"] == 0.7 and askida["hermes_poll"]["expected_h"] == 0.5

    watchdog.check_and_alarm()
    watchdog.check_and_alarm()
    assert alarmlar == []                                        # tek satır bile yazılmadı
    # SESSİZ DEĞİL: askıda sayacı defterde.
    doc = store.read_json(watchdog.ALARM_GUNLUK_FILE, {})
    assert doc["mekanizmalar"]["hermes_poll"]["askida"] == 2
    assert doc["mekanizmalar"]["hermes_poll"]["son_askida_neden"] == "kota_sogumasi"


def test_askida_mekanizma_OK_SAYILMAZ(sandbox_state, saat, monkeypatch):
    """Askıda 'iyi' değildir. `ok` sayacına katılırsa pano beklemeyi sağlık diye gösterir."""
    monkeypatch.setattr(watchdog, "_hermes_askida",
                        lambda: {"neden": "havuz_tukendi", "kalan_s": None, "detay": "kimlik yok"})
    _tazele(saat, "scheduler_poll")
    _bayatla(saat, "hermes_poll", 0.7 * 3600)
    rep = watchdog.report()
    assert rep["ok"] == 1                                        # yalnız scheduler_poll
    assert "hermes_poll" not in rep["never"] and "hermes_poll" not in {x["name"] for x in rep["stale"]}


def test_sogumadan_cikinca_gecikme_alarmi_YENIDEN_calisir(sandbox_state, saat, alarmlar, monkeypatch):
    """Askıda kapısı gerçek arızayı ÖRTMEZ: bekleme bitince aynı bayatlık normal yola döner."""
    askida = {"v": {"neden": "kota_sogumasi", "kalan_s": 60.0, "detay": "soğumada"}}
    monkeypatch.setattr(watchdog, "_hermes_askida", lambda: askida["v"])
    _bayatla(saat, "hermes_poll", 0.7 * 3600)
    watchdog.check_and_alarm()
    assert alarmlar == []
    askida["v"] = None                                            # soğuma bitti, nabız hâlâ yok
    watchdog.check_and_alarm()
    assert alarmlar == [("MECHANISM_STALE", "hermes_poll")]


def test_sonda_DUSERSE_askida_sayilmaz_ve_sessiz_kalmaz(sandbox_state, saat, alarmlar, monkeypatch):
    """FAIL-CLOSED + YASA 4: ölçülemeyen bekleme alarmı bastırmaz, üstelik düşüş kayda geçer."""
    def _patlat():
        raise RuntimeError("brain_cooldown.json okunamadı")

    uyarilar: list[dict] = []
    monkeypatch.setattr(watchdog, "_hermes_askida", _patlat)
    monkeypatch.setattr(obs, "warn", lambda ev, **kw: uyarilar.append({"ev": ev, **kw}))
    _bayatla(saat, "hermes_poll", 0.7 * 3600)
    rep = watchdog.report()
    assert "hermes_poll" in {x["name"] for x in rep["stale"]} and rep["askida"] == []
    watchdog.check_and_alarm()
    assert alarmlar == [("MECHANISM_STALE", "hermes_poll")]
    assert any(u["ev"] == "watchdog_askida_probe_failed" for u in uyarilar)


def test_sonda_YALNIZ_kendi_mekanizmasi_icin_kosar(sandbox_state, saat, monkeypatch):
    """Sonda listesi dışındaki bir mekanizma hermes soğumasından etkilenmez (kapsam sızıntısı yok)."""
    cagri: list[str] = []
    monkeypatch.setattr(watchdog, "_hermes_askida",
                        lambda: cagri.append("x") or {"neden": "kota_sogumasi", "detay": "d"})
    _bayatla(saat, "scheduler_poll", 3600)
    rep = watchdog.report()
    assert "scheduler_poll" in {x["name"] for x in rep["stale"]}
    assert cagri == []                                            # hiç çağrılmadı


def test_sonda_YALNIZ_bayatken_kosar(sandbox_state, saat, monkeypatch):
    """Pano her poll'da `report()` çağırır; pencere içindeyken kota dosyalarını okumak boşuna I/O."""
    cagri: list[str] = []
    monkeypatch.setattr(watchdog, "_hermes_askida", lambda: cagri.append("x") or None)
    _tazele(saat, "hermes_poll")
    watchdog.report()
    assert cagri == []
    _bayatla(saat, "hermes_poll", 0.7 * 3600)
    watchdog.report()
    assert cagri == ["x"]


def test_hermes_askida_sondasi_GERCEK_defteri_okur(sandbox_state, saat, monkeypatch):
    """Sonda saplanmadan: `brain_cooldown.json` gerçekten okunuyor mu (v188'in yazdığı yer)."""
    from meridian import hermes
    assert watchdog._hermes_askida() is None                      # boş defter → askıda yok
    hermes.brain_stand_down("agent", "pool_exhausted:gemini")
    sus = watchdog._hermes_askida()
    assert sus and sus["neden"] == "kota_sogumasi" and sus["kalan_s"] > 0
    assert "agent" in sus["detay"]
    hermes.brain_recovered("agent")
    assert watchdog._hermes_askida() is None


# =================================================================================================
# (b) HİSTEREZİS + GÜNLÜK TEKİLLEŞTİRME
# =================================================================================================
def test_esik_asimi_surerken_tekrar_YOK(sandbox_state, saat, alarmlar, monkeypatch):
    """Eski davranış korunur: mandal duruyorken aynı olgu ikinci kez anlatılmaz."""
    _sogumasiz(monkeypatch)
    _bayatla(saat, "scheduler_poll", 3600)
    for _ in range(5):
        watchdog.check_and_alarm()
    assert alarmlar.count(("MECHANISM_STALE", "scheduler_poll")) == 1


def test_cirpinma_ayni_gunde_TEK_alarm_uretir(sandbox_state, saat, alarmlar, monkeypatch):
    """CANLI KUSUR: toparlan→yeniden-aş döngüsü 112 satır yazıyordu. Gün tavanı 1'dir."""
    _sogumasiz(monkeypatch)
    for _ in range(12):                                    # 12 tam salınım (canlı desenin minyatürü)
        _bayatla(saat, "scheduler_poll", 3600)
        watchdog.check_and_alarm()
        _tazele(saat, "scheduler_poll")
        watchdog.check_and_alarm()
        saat.ileri(600)
    assert alarmlar.count(("MECHANISM_STALE", "scheduler_poll")) == watchdog.GUNLUK_ALARM_TAVANI == 1
    doc = store.read_json(watchdog.ALARM_GUNLUK_FILE, {})
    satir = doc["mekanizmalar"]["scheduler_poll"]
    assert satir["alarm"] == 1 and satir["bastirilan"] == 11      # bastırma SAYILDI, yutulmadı


def test_bastirma_sayaci_RAPORDA_gorunur(sandbox_state, saat, alarmlar, monkeypatch):
    """Bastırma panoya çıkmazsa hijyen ile körlük ayırt edilemez."""
    _sogumasiz(monkeypatch)
    for _ in range(3):
        _bayatla(saat, "scheduler_poll", 3600)
        watchdog.check_and_alarm()
        _tazele(saat, "scheduler_poll")
        watchdog.check_and_alarm()
    rep = watchdog.report()
    ozet = rep["bastirilan"]["mekanizmalar"]["scheduler_poll"]
    assert ozet["alarm"] == 1 and ozet["bastirilan"] == 2
    assert rep["bastirilan"]["gun"] == "2026-08-06"


def test_gun_donunce_yeni_alarm_MESRU(sandbox_state, saat, alarmlar, monkeypatch):
    """Tavan bir gündür. Ertesi gün hâlâ bayatsa operatör yeniden duyar (kalıcı sessizlik YOK)."""
    _sogumasiz(monkeypatch)
    _bayatla(saat, "scheduler_poll", 3600)
    watchdog.check_and_alarm()
    assert alarmlar.count(("MECHANISM_STALE", "scheduler_poll")) == 1
    saat.ileri(GUN)                                        # ertesi UTC günü
    _tazele(saat, "scheduler_poll")
    watchdog.check_and_alarm()                             # mandal düşer
    _bayatla(saat, "scheduler_poll", 3600)
    watchdog.check_and_alarm()
    assert alarmlar.count(("MECHANISM_STALE", "scheduler_poll")) == 2
    doc = store.read_json(watchdog.ALARM_GUNLUK_FILE, {})
    assert doc["gun"] == "2026-08-07"
    assert doc["mekanizmalar"]["scheduler_poll"]["alarm"] == 1    # dünün sayacı taşınmadı


def test_tavan_MEKANIZMA_BASINA(sandbox_state, saat, alarmlar, monkeypatch):
    """Bir mekanizmanın tavanı diğerini susturmaz — bütçe mekanizma başınadır, küresel değil."""
    _sogumasiz(monkeypatch)
    _bayatla(saat, "scheduler_poll", 3600)
    _bayatla(saat, "warmup_sprint", 9 * 3600)
    watchdog.check_and_alarm()
    assert {a[1] for a in alarmlar} == {"scheduler_poll", "warmup_sprint"}


@pytest.mark.parametrize("bozuk", [{"gun": "2026-08-06", "mekanizmalar": "BOZUK"},
                                   {"gun": "2026-08-06", "mekanizmalar": {"scheduler_poll": 7}},
                                   ["liste", "beklenmiyor"]])
def test_gunluk_defter_bozuksa_bekci_DUSMEZ(sandbox_state, saat, alarmlar, monkeypatch, bozuk):
    """Bekçi asla düşmez: sayaç bir HİJYEN aracıdır, karar kaynağı değil. Bozuk bir dosya yüzünden
    `check_and_alarm` istisna atsaydı çağıran scheduler poll'unu da yanında götürürdü."""
    _sogumasiz(monkeypatch)
    store.write_json(watchdog.ALARM_GUNLUK_FILE, bozuk)
    _bayatla(saat, "scheduler_poll", 3600)
    watchdog.check_and_alarm()
    assert alarmlar == [("MECHANISM_STALE", "scheduler_poll")]   # haber verme görevi aksamadı
    assert store.read_json(watchdog.ALARM_GUNLUK_FILE, {})["mekanizmalar"]["scheduler_poll"]["alarm"] == 1


# =================================================================================================
# PANO PARİTESİ — askıda kovası okuyucusuz kalmasın (YASA 6)
# =================================================================================================
def test_pano_ve_sessiz_hat_askidayi_OKUR(sandbox_state):
    from pathlib import Path
    kok = Path(__file__).resolve().parent.parent
    appjs = (kok / "meridian" / "web" / "app.js").read_text()
    apipy = (kok / "meridian" / "api.py").read_text()
    kod = "\n".join(l for l in appjs.splitlines() if not l.lstrip().startswith("//"))
    assert "wd.askida" in kod, "HUD rozeti askıda kovasını okumuyor — kova yazılıp okunmuyor"
    assert "askıda" in kod
    assert 'wd.get("askida")' in apipy and '"n_askida"' in apipy


def test_sessiz_hat_askidayi_SAPMA_saymaz(sandbox_state, saat, monkeypatch):
    """Meşru bekleme sessiz hattı kırmızıya boyarsa alarm-yorgunluğu yüzeyi değiştirmiş olur."""
    from meridian import api
    monkeypatch.setattr(watchdog, "_hermes_askida",
                        lambda: {"neden": "kota_sogumasi", "kalan_s": 900.0, "detay": "soğumada"})
    _tazele(saat, "scheduler_poll")
    _bayatla(saat, "hermes_poll", 0.7 * 3600)
    wd = watchdog.report()
    wd["never"] = []                                       # bu testin konusu askıda; 'never' ayrı hâl
    seg = {s["ad"]: s for s in api._sessiz_hat(wd, {})["segmentler"]}["bekçiler"]
    assert seg["n_sapma"] == 0 and seg["saglikli"] is True
    assert seg["n_askida"] == 1 and seg["askida"][0]["ad"] == "hermes_poll"
    assert seg["askida"][0]["neden"] == "kota_sogumasi"
