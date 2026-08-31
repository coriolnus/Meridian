"""test_hotstate_gorunurluk_v294.py — ÇIRPINMA SAYACI SÜREÇLER ARASI OKUNABİLİR Mİ?

FİŞ 3/6 (ORTA): `coverage_ariza.hotstate.surec_ici_sayac = null`, beyan "health().
reassert_suppressed okunmadı". Ölçülen kök: `hotstate.health()` SÜREÇ-İÇİ bir sözlük döndürür;
sayacı ARTIRAN süreç (worker: marketstream/barfeed iplikleri) ile onu OKUYACAK süreç (pano —
docker-compose'da `state`i SALT-OKUNUR bağlayan ayrı bir servis; ayrıca `meridian-barsarchive`
üçüncü bir birim) AYNI süreç değildir. Sözlük süreç sınırını geçmez.

BU DOSYANIN ÇİVİLEDİĞİ İDDİA — iki yarım, ikisi de zorunlu:
  (1) GÖRÜNÜRLÜK: sayaç BAŞKA BİR SÜREÇTE artırıldığında BU süreçten okunabiliyor. Çivi taklit
      etmez: gerçek bir `subprocess` açar, sayacı orada artırır, süreci kapatır ve okumayı
      buradan yapar. Yalıtılmış bir modül-yeniden-yüklemesi bu iddiayı KANITLAMAZ.
  (2) DÜRÜSTLÜK: okunamadığında `None` + NEDEN taşır. SESSİZ 0 YASAK — "ölçtük, sıfır çırpınma"
      ile "ölçemedik" AYRI hâllerdir. Bu yarım, canlı defterin kendi kanıtıyla zorunlu:
      yerel `state/events.jsonl`daki 15.865 `hotstate_down` satırının 15.863'ü `suppressed`
      alanını HİÇ TAŞIMIYOR (alan, DOWN_REASSERT_S kısıtlamasından önce yoktu). O satırları
      "suppressed=0" diye toplamak, ölçülmemiş bir pencereyi "çırpınma yok" diye rapor etmektir.

TASARIM KARARI DA ÇİVİLENİR: görev iki yol öneriyordu — (a) YENİ kalıcı artefakt, (b) watchdog
Redis'e kendi sorsun. İkisi de reddedildi, gerekçe `test_hotstate_hala_kalici_defter_yazmiyor`
ve `test_watchdog_redise_kendisi_sormuyor` docstring'lerinde. Seçilen yol: sayaç ZATEN VAR OLAN
kalıcı yüzeye (`state/events.jsonl`, yazan `obs`, okuyan `watchdog`) süreç kimliğiyle basılır.
"""
from __future__ import annotations

import ast
import json
import os
import subprocess
import sys
import datetime as _dt
from pathlib import Path

import pytest

from meridian import hotstate as hs
from meridian import watchdog as wd

REPO = Path(__file__).resolve().parent.parent
HOTSTATE_SRC = REPO / "meridian" / "hotstate.py"
WATCHDOG_SRC = REPO / "meridian" / "watchdog.py"


@pytest.fixture(autouse=True)
def _saglik_defteri_yalitildi():
    """`hotstate._HEALTH` modül-globaldir ve conftest onu sıfırlamaz; bu dosya sayaç değerleri
    üzerine hüküm verdiği için komşu testten devralınan bir artık ölçümü yalanlardı."""
    onceki = dict(hs._HEALTH)
    onceki_emit = hs._LAST_DOWN_EMIT
    hs._HEALTH.clear()
    hs._HEALTH.update(ok=None, reads=0, writes=0, fails=0, last_error="", at=None, down_since=None)
    yield
    hs._HEALTH.clear()
    hs._HEALTH.update(onceki)
    hs._LAST_DOWN_EMIT = onceki_emit


# ------------------------------------------------------------------------------------------------
# ZAMAN FİKSTÜRÜ — SABİT DAMGA YASAK (2026-08-26'da ölçülerek öğrenildi)
# ------------------------------------------------------------------------------------------------
# Bu dosya `"2026-08-25T10:00:00+00:00"` gibi SABİT damgalar kullanıyordu ve
# `watchdog.events_since` penceresini ŞİMDİDEN geriye hesaplar:
#     since = now(utc) - timedelta(days=gun);  satır ancak ts >= since ise pencereye girer
# Yani fikstür, gerçek saat 2026-08-26T10:00 UTC'yi geçtiği AN pencereden düştü ve üç test
# birden kırmızıya döndü — kodda hiçbir değişiklik olmadan. Saatli bir bombaydı.
#
# TAM OLARAK BU SINIF DEPODA ADI KONMUŞ: scheduler.py'nin "DÖRDÜNCÜ KAPI" şerhi diyor ki
# "test paketi 18:00-21:00 arası yeşil, 22:00'den sonra kırmızıydı: SAAT BAĞIMLI bir suite,
# geçtiğinde HİÇBİR ŞEY KANITLAMAZ." Bir fikstür damgası, ölçülen şeyin parçası değilse,
# ölçüm ânına GÖRE üretilmelidir.
def _damga(dakika_once: int = 60) -> str:
    """Pencere içinde kalması GARANTİ bir damga. Testler `gun=1` penceresi kullanıyor;
    60 dakika öncesi her saatte güvenle içeridedir."""
    return (_dt.datetime.now(_dt.timezone.utc)
            - _dt.timedelta(minutes=dakika_once)).isoformat(timespec="seconds")


def _satir(rapor: dict, ad: str) -> dict | None:
    """`parity_report()` satırlarından adı verileni bul (yoksa None)."""
    for r in rapor["rows"]:
        if r["check"] == ad:
            return r
    return None


# ============ 1) GÖRÜNÜRLÜK: GERÇEK İKİNCİ SÜREÇ ============
_COCUK = r"""
import os, pathlib, sys
sys.path.insert(0, {repo!r})
from meridian import config
config.STATE = pathlib.Path({state!r})
config.HISTORY = config.STATE / "history"
config.BARS = config.STATE / "bars"
from meridian import hotstate as hs
hs.DOWN_REASSERT_S = 0            # yeniden-basım kısıtını kaldır: bastırılan sayaç HEMEN yayınlansın
hs._note_down(ConnectionError("civi: taklit kopus"))   # KENAR  → hotstate_down basılır
hs._note_down(ConnectionError("civi: taklit kopus"))   # SÜREGELEN → bastırılan 1, yeniden basılır
print("PID=%d" % os.getpid())
"""


def test_sayac_baska_bir_surecte_yazilip_bu_surecte_okunuyor(sandbox_state):
    """ASIL ÇİVİ. Sayaç AYRI BİR İŞLETİM SİSTEMİ SÜRECİNDE artırılır, o süreç ölür, okuma BURADA
    yapılır. `hotstate.health()` bu süreçte hâlâ boştur (ok=None) — yani okunan sayı süreç-içi
    sözlükten GELEMEZ; geldiyse süreç sınırı gerçekten aşılmış demektir."""
    betik = _COCUK.format(repo=str(REPO), state=str(sandbox_state))
    p = subprocess.run([sys.executable, "-c", betik], capture_output=True, text=True, timeout=180)
    assert p.returncode == 0, f"çocuk süreç düştü:\n{p.stdout}\n{p.stderr}"
    cocuk_pid = int([s for s in p.stdout.split() if s.startswith("PID=")][0].split("=")[1])
    assert cocuk_pid != os.getpid(), "çocuk süreç ayrışmadı — çivi süreç sınırını ölçmüyor"

    rap = wd.hotstate_health_report()

    assert rap["surec_ici"]["bastirilan"] is None, \
        "bu süreç hotstate'e hiç dokunmadı; süreç-içi sayaç ÖLÇÜLMEMİŞ sayılmalı"
    assert rap["defter"]["bastirilan"] == 1, "başka sürecin bastırdığı kopuş bu süreçten okunamadı"
    assert rap["defter"]["surecler"] == {str(cocuk_pid): 2}, \
        "olaylar süreç kimliğine bağlanamıyor — 'tek süreç çırpındı' ile 'elli süreç yeniden başladı' ayrılamaz"
    assert rap["defter"]["down_basimi"] == 2
    assert rap["capraz_surec"] is True


# ============ 2) DÜRÜSTLÜK: ÖLÇÜLEMEYEN None + NEDEN ============
def test_hic_kayit_yokken_sifir_degil_none_ve_neden_doner(sandbox_state):
    """Boş defter + hotstate'e hiç dokunmamış süreç: HER İKİ yarım da None ve HER İKİSİ de NEDEN
    taşır. 0 dönmek "ölçtük, çırpınma yok" demek olurdu — bu süreç hiçbir şey ölçmedi."""
    rap = wd.hotstate_health_report()

    assert rap["surec_ici"]["bastirilan"] is None
    assert len(rap["surec_ici"]["bastirilan_neden"] or "") >= 20
    assert rap["defter"]["bastirilan"] is None
    assert len(rap["defter"]["bastirilan_neden"] or "") >= 20
    assert rap["defter"]["surecler"] is None
    assert len(rap["defter"]["surecler_neden"] or "") >= 20
    assert rap["capraz_surec"] is False


def test_alan_tasimayan_satirlar_sifir_diye_toplanmaz(sandbox_state):
    """CANLI KANIT ÇİVİSİ: yerel defterdeki 15.863 `hotstate_down` satırı `suppressed` alanını
    taşımıyor. Alan yoksa sayaç ÖLÇÜLMEMİŞTİR — `sum(get('suppressed', 0))` yazan bir okuyucu
    tam da bu satırlarda "0 çırpınma" raporlar. Alan-taşımayan satır sayısı GÖRÜNÜR kalmalı."""
    alansiz = [{"ts": _damga(60), "level": "warn", "event": "hotstate_down",
                "error": "TimeoutError: Timeout reading from socket"} for _ in range(7)]

    rap = wd.hotstate_health_report(olaylar=alansiz)

    assert rap["defter"]["olay"] == 7, "olay sayımı ayrı bir ölçüdür ve kaybolmamalı"
    assert rap["defter"]["bastirilan"] is None, "alansız satırlar sessizce 0 sayıldı — SESSİZ 0 YASAK"
    assert rap["defter"]["alansiz_satir"] == 7
    assert "suppressed" in (rap["defter"]["bastirilan_neden"] or "")


def test_karisik_defterde_toplam_alt_sinir_olarak_isaretlenir(sandbox_state):
    """Bir kısmı alanı taşıyor, bir kısmı taşımıyor: toplam DÖNER ama ALT SINIR olduğu beyan
    edilir. Beyansız bir toplam, eksik pencereyi tam sanmaktır."""
    karisik = [
        {"ts": _damga(60), "event": "hotstate_down", "error": "x"},
        {"ts": _damga(59), "event": "hotstate_down", "error": "x",
         "suppressed": 4, "pid": 999, "down_emits": 2, "suppressed_total": 4},
    ]

    rap = wd.hotstate_health_report(olaylar=karisik)

    assert rap["defter"]["bastirilan"] == 4
    assert rap["defter"]["alt_sinir"] is True
    assert rap["defter"]["alansiz_satir"] == 1


def test_surec_ici_sayac_bu_surecte_olculdugunde_okunur(sandbox_state):
    """Üçüncü hâl: bu süreç hotstate'i GERÇEKTEN kullandıysa (ok artık None değil) ve hiç
    bastırma olmadıysa cevap ÖLÇÜLMÜŞ 0'dır — None değil. Üç hâl birbirine karışmamalı."""
    hs._HEALTH.update(ok=True)
    assert wd.hotstate_health_report()["surec_ici"]["bastirilan"] == 0

    hs._LAST_DOWN_EMIT = 0.0
    hs._note_down(ConnectionError("çivi: kenar"))        # ok False'a düşer, olay basılır
    hs._note_down(ConnectionError("çivi: süregelen"))    # bastırılan 1 (yeniden-basım penceresi dolu değil)
    rap = wd.hotstate_health_report()
    assert rap["surec_ici"]["bastirilan"] == 1
    assert rap["surec_ici"]["bastirilan_neden"] is None
    assert rap["surec_ici"]["down_basimi"] == 1
    assert rap["surec_ici"]["pid"] == os.getpid()


# ============ 3) YAYIN: OLAY SÜREÇ KİMLİĞİ TAŞIR ============
def test_hotstate_down_olayi_surec_kimligi_ve_kumulatif_sayac_tasir(sandbox_state):
    """Sayacın süreç sınırını geçtiği TEK yer bu olaydır; kimliksiz bir sayı toplanamaz.
    `down_emits` ayrıca zorunlu: pencere içinde 1 satır görmek "bir kez koptu" DEĞİL, "bu
    pencerede bir kez YAZILDI" demektir — süreç kaç kenar bastığını kendi taşımalı."""
    hs._LAST_DOWN_EMIT = 0.0
    hs._note_down(ConnectionError("çivi: kenar"))

    satirlar = [json.loads(s) for s in
                (sandbox_state / "events.jsonl").read_text().splitlines() if s.strip()]
    olay = [e for e in satirlar if e.get("event") == "hotstate_down"][-1]

    assert olay["pid"] == os.getpid()
    assert olay["down_emits"] == 1
    assert olay["suppressed_total"] == 0
    assert "***" not in olay["error"], "hata metni maskeleme kuralına takılmamalı (url ayrı alan)"


# ============ 4) YASA 6: OKUYUCU AYNI TURDA BAĞLI ============
def test_parity_satiri_capraz_surec_sayacini_tasiyor(sandbox_state):
    """`hotstate_sustained_down` satırı bugüne dek yalnız OLAY SAYISI ve son hatayı yazıyordu.
    Sensörün okuyucusu bu satırdır: sayaç satıra girmezse ölçüm yine okunmadan kalırdı."""
    olaylar = [{"ts": _damga(60), "level": "warn", "event": "hotstate_down",
                "error": "ResponseError: UNBLOCKED the stream key no longer exists",
                "suppressed": 3, "pid": 4242, "down_emits": 9, "suppressed_total": 3}]

    r = _satir(wd.parity_report(olaylar=olaylar), "hotstate_sustained_down")

    assert r is not None and r["ok"] is False
    assert "4242" in r["detail"], "satır hangi sürecin çırpındığını söylemiyor"
    assert "3" in r["detail"]


# ============ 4b) FİŞİN KENDİ ALANI: SENSÖR TÜKETİCİYE BAĞLANDI ============
# Sensör 2026-08-26'da yazıldı ama fişi DOĞURAN alan (`coverage_ariza.hotstate.surec_ici_sayac`)
# `analytics.coverage_breakage_counters` içinde SABİT `None` kalmıştı — yanında "OKUNMADI" beyanıyla.
# Yani ölçüm vardı, okuyanı yoktu ve fiş her koşuda aynı cümleyle yeniden doğuyordu (akıbet kalemi
# N00016). Bu blok kabloyu çiviler: fiş alanı artık `watchdog.hotstate_health_report`tan gelir.
def _hs_olay(dk, **ek):
    """Pencere içinde bir `hotstate_down` satırı — alanlar isteğe bağlı (alansız satır da geçerli
    bir hâldir ve tam da bu yüzden ayrı sayılır)."""
    return {"ts": _damga(dk), "level": "warn", "event": "hotstate_down",
            "error": "ConnectionError: civi", **ek}


def test_fis_alani_defter_yarimini_GERCEK_sayilarla_tasiyor(sandbox_state):
    """ASIL ÇİVİ. Fişin alanı artık sabit değil: başka süreçlerin bastırdığı kopuşlar, kenar
    basımları ve süreç kimlikleri `coverage_ariza.hotstate` altında GÖRÜNÜR. Sayılar sensörün
    (`watchdog.hotstate_health_report`) hükmüyle BİREBİR aynı olmalı — iki kopya sessizce ayrışır."""
    from meridian import analytics, store
    olaylar = [_hs_olay(60, suppressed=3, pid=4242, down_emits=5, suppressed_total=3),
               _hs_olay(59, suppressed=1, pid=4242, down_emits=6, suppressed_total=4),
               _hs_olay(58)]
    store.write_jsonl("events.jsonl", olaylar)

    hs_blok = analytics.coverage_breakage_counters(days=1)["hotstate"]
    sensor = wd.hotstate_health_report(1)

    assert hs_blok["defter"] == sensor["defter"], "fiş alanı sensörün defterinden AYRIŞMIŞ"
    assert hs_blok["defter"]["bastirilan"] == 4, "süreçler arası sayaç fişe ULAŞMIYOR"
    assert hs_blok["defter"]["alt_sinir"] is True, "alansız satır varken toplam alt-sınır DEĞİL"
    assert hs_blok["defter"]["surecler"] == {"4242": 2}
    assert hs_blok["defter"]["down_basimi"] == 6
    assert hs_blok["hotstate_down"] == 3, "olay sayımı kayboldu/ayrıştı"
    assert hs_blok["capraz_surec"] is True


def test_fis_alani_surec_ici_yarimda_SIFIR_BASMAZ(sandbox_state):
    """DÜRÜSTLÜK YARIMI KORUNDU. Bu süreç hotstate'e dokunmadı (pano süreci de dokunmaz): süreç-içi
    sayaç None KALIR ve NEDENİ alanla birlikte taşınır. Sensörü bağlamak, "0 çırpınma" basmak için
    bir bahane DEĞİLDİR — kablonun kendisi bu yasayı gevşetemez."""
    from meridian import analytics, store
    store.write_jsonl("events.jsonl", [_hs_olay(60, suppressed=2, pid=4242, down_emits=1)])

    hs_blok = analytics.coverage_breakage_counters(days=1)["hotstate"]

    assert hs_blok["surec_ici_sayac"] is None, "ölçülmemiş süreç-içi sayaç SIFIR basıldı"
    assert len(hs_blok["surec_ici_neden"] or "") >= 20, "None NEDENSİZ — 'yok' ile 'ölçemedik' karışır"
    assert str(os.getpid()) in hs_blok["surec_ici_neden"], "neden hangi süreçte ölçülemediğini demiyor"


def test_fis_alani_surec_ici_yarimi_OLCULDUGUNDE_gercekten_okur(sandbox_state):
    """Üçüncü hâl fişe de ulaşır: sayacı ARTIRAN sürecin kendisi bu paketi üretirse alan artık
    None değil ÖLÇÜLMÜŞ bir sayıdır. Aksi hâlde kablo yalnız bir yarımı taşıyor olurdu."""
    from meridian import analytics
    hs._HEALTH.update(ok=True)
    hs._LAST_DOWN_EMIT = 0.0
    hs._note_down(ConnectionError("çivi: kenar"))
    hs._note_down(ConnectionError("çivi: süregelen"))

    hs_blok = analytics.coverage_breakage_counters(days=1)["hotstate"]

    assert hs_blok["surec_ici_sayac"] == 1
    assert hs_blok["surec_ici_neden"] is None, "ölçülmüş bir sayı NEDEN taşıyor — hâller karışmış"


def test_fis_beyani_artik_OKUNMADI_demiyor(sandbox_state):
    """BEYAN BAYATLAMA KAPISI. Eski beyan "`health().reassert_suppressed` OKUNMADI" diyordu;
    sensör bağlandıktan sonra bu cümle bir YALANdır ve okuyucuyu var olmayan bir boşluğa
    yönlendirir. Beyan iki yarımı da ADIYLA anmalı."""
    from meridian import analytics
    beyan = analytics.coverage_breakage_counters(days=1)["hotstate"]["beyan"]

    assert "OKUNMADI" not in beyan, "beyan sensör bağlandıktan sonra da 'okunmadı' diyor"
    assert "hotstate_health_report" in beyan, "beyan tek kaynağı adıyla söylemiyor"


def test_fis_sayaci_KENDI_hesaplamiyor_sensorden_okuyor():
    """TEK-KAYNAK YASASI, statik. Aynı sayının ikinci bir hesabı sessizce ayrışır: `analytics`
    `hotstate_down` satırlarını kendi süzüp `suppressed` toplamaya BAŞLARSA sensörün "alansız satır
    0 DEĞİLDİR" yasası o kopyada yaşamaz ve fiş yine sessiz bir 0 rapor ederdi."""
    kaynak = REPO / "meridian" / "analytics.py"
    agac = ast.parse(kaynak.read_text())
    fn = next(n for n in ast.walk(agac)
              if isinstance(n, ast.FunctionDef) and n.name == "coverage_breakage_counters")
    cagrilar = {n.func.attr for n in ast.walk(fn)
                if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)}
    assert "hotstate_health_report" in cagrilar, \
        "fiş alanı sensörü çağırmıyor — sayaç ikinci kez hesaplanıyor olabilir"


# ============ 5) REDDEDİLEN İKİ YOL — YAPISAL OLARAK KAPALI ============
def test_hotstate_hala_kalici_defter_yazmiyor(sandbox_state):
    """SEÇENEK (a) 'YENİ ARTEFAKT' NEDEN REDDEDİLDİ: `hotstate` yalnız UÇUCU Redis tutar ve bu
    sınır depoda İKİ ayrı testle (v83, v84) zaten çivilenmiş. `store.write_json` ile yeni bir
    `state/hotstate_health.json` yazmak o iki çiviyi kırardı — ve `codelaw.artifact_graph`
    okuyucusuz gördüğü an kapı düşerdi. Sınır burada ÜÇÜNCÜ kez çivilenir ki bu turun
    kararı sonraki turda sessizce geri alınmasın."""
    yasak = {"write_json", "write_jsonl", "append_jsonl", "update_json", "write_text", "write_bytes"}
    agac = ast.parse(HOTSTATE_SRC.read_text())
    isabet = [n.func.attr for n in ast.walk(agac)
              if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr in yasak]
    assert not isabet, f"hotstate kalıcı defter yazıyor: {isabet}"


def test_watchdog_redise_kendisi_sormuyor(sandbox_state):
    """SEÇENEK (b) 'WATCHDOG REDIS'E SORSUN' NEDEN REDDEDİLDİ: ölçülen büyüklük "Redis kaç kez
    ERİŞİLEMEDİ"dir. Erişilemeyen bir servise bunu sormak tanım gereği imkânsızdır (soru tam da
    cevabın alınamadığı anlarda sorulur), erişilebildiği anda da Redis o anların hafızasını
    tutmaz. Üstelik `hotstate` DEĞİŞMEZ-1 Redis'i UÇUCU ilan eder: denetim sayacını oraya koymak
    kalıcı bir iddiayı uçucu bir depoya bağlardı. Sensör bu yüzden bağlantı KURMAZ — bekçi
    raporu ağ hatasıyla düşemez."""
    agac = ast.parse(WATCHDOG_SRC.read_text())
    fn = next(n for n in ast.walk(agac)
              if isinstance(n, ast.FunctionDef) and n.name == "hotstate_health_report")
    cagrilar = {n.func.attr for n in ast.walk(fn)
                if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)}
    for redis_yolu in ("available", "_redis", "_blocking_redis", "ping", "read_bars", "barfeed_pending"):
        assert redis_yolu not in cagrilar, \
            f"sensör Redis'e uzanıyor ({redis_yolu}) — bekçi gözlemdir, ağ bağımlılığı taşıyamaz"
