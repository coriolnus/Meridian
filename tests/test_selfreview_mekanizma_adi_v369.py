"""v369 — HAFTALIK RAPORUN `watchdog_incidents` SATIRLARINDA MEKANİZMA ADI BOŞLUĞU (2026-09-02).

CANLI ÖLÇÜM: `selfreview.build()` MECHANISM_STALE olaylarından yalnız `e.get("mechanism")` okuyordu;
üreticilerin çoğu o alanı GÖNDERMİYOR (21 olayın 19'unda yok). Sonuç: rapor `{"mechanism": null}`
satırları basıyor, operatör hangi mekanizmanın öksürdüğünü RAPORDA göremiyordu — "8 bekçi olayı"
diyen dikkat satırı, hangi 8 olduğunu söyleyemiyordu.

ÜRETİCİ İMZALARI TEK DEĞİL, DÖRT SINIF (hepsi `obs.alarm("MECHANISM_STALE", msg, **fields)`;
alanlar olay sözlüğünün TEPESİNE düşer — `obs._emit`):
  1. `mechanism=` var                       — watchdog.py::check_and_alarm (gap_h/gap_s/asim_s ile),
                                              watchdog.py::check_integrity_and_alarm (kind="starved" ile)
  2. `kind=` + `detector=`, mechanism YOK   — watchdog.py::check_integrity_and_alarm (kind="detector_failed", detector=<ad>)
  3. `kind=` + `artifact=`/`check=`          — watchdog.py::check_integrity_and_alarm (kind="parity", check, artifact;
                                              kind="coherence", artifact de aynı fonksiyonda)
  4. tanınan alan YOK (yalnız mesaj)        — `loop._reconcile_gunu_atlandi` (alan adı `mekanizma=`,
                                              TÜRKÇE — tüketicinin beklediği `mechanism` DEĞİL;
                                              ÜRETİCİ 2026-09-03'te TSK-101 ile düzeltildi, geçmiş
                                              defter satırları bu şekilde KALIR),
                                              `watchdog.py::check_liveness_and_alarm` (kind var ama
                                              bu sınıfın saf hâli: hiçbir tanınan alan yok).
                                              ÇAPA SEMBOLE ÇEVRİLDİ (2026-09-03, TSK-030 adım-3):
                                              `watchdog.py:3736-3754` [çapa-mezar-taşı] yazıyordu ve BU TURUN
                                              `watchdog.py`ye eklediği 4 satır onu kaydırdı —
                                              satır çapasının çürüme biçimi tam olarak budur.

ÇİVİLENEN İDDİA (uygulama değil): `_olay_mekanizma(e)` bir DÜŞÜŞ SIRASI uygular —
mechanism → kind(+detector|artifact) → artifact → message[:60] → None. Son basamak ÖNEMLİDİR:
ad ÖLÇÜLEMEDİĞİNDE None döner, İCAT EDİLMEZ (uydurma yasağı). Ve rapor satırı bu yardımcıyı
GERÇEKTEN çağırır (entegrasyon çivisi) — yalnız yardımcının kendisi doğru olsa sorun kapanmazdı.

`gap_h` bilerek çıplak kalır: sınıfların çoğunda o alan YOKTUR ve None kalması DOĞRUDUR (dürüst
boşluk). Bu dosya `gap_h`'ı doldurmaya ÇALIŞMAZ.
"""
from __future__ import annotations

import datetime as dt

from meridian import selfreview, store


# =================================================================================================
# A) DÜŞÜŞ SIRASI — sınıf başına bir GERÇEK imza
# =================================================================================================
def test_mechanism_dolu_ise_dogrudan_doner_ve_dusus_ORADA_durur():
    """Sınıf 1 (watchdog.py::check_integrity_and_alarm imzası): `mechanism` VE `kind` birlikte gelir. Düşüş sırası ilk
    basamakta durmazsa "starved" gibi bir SINIF ADI, mekanizma adının yerine geçerdi."""
    e = {"alarm": "MECHANISM_STALE", "message": "mekanizma ÜRETMİYOR: cf_advance — (0 çıktı)",
         "mechanism": "cf_advance", "kind": "starved"}
    assert selfreview._olay_mekanizma(e) == "cf_advance"


def test_mechanism_bos_ise_dususe_devam_eder():
    """"Dolu" olan kazanır: boş dize bir ad DEĞİLDİR — varlığı düşüşü durdurursa satır yine boş çıkar."""
    e = {"mechanism": "", "kind": "coherence", "artifact": "score_calibration.json"}
    assert selfreview._olay_mekanizma(e) == "coherence:score_calibration.json"


def test_kind_ve_detector_birlesir():
    """Sınıf 2 (watchdog.py::check_integrity_and_alarm): mechanism YOK, ad `detector`da. Yalnız "detector_failed" demek
    HANGİ dedektörün düştüğünü gizler."""
    e = {"alarm": "MECHANISM_STALE",
         "message": "BÜTÜNLÜK DEDEKTÖRÜ DÜŞTÜ: determinism hüküm veremedi — KeyError",
         "kind": "detector_failed", "detector": "determinism"}
    assert selfreview._olay_mekanizma(e) == "detector_failed:determinism"


def test_kind_ve_artifact_birlesir():
    """Sınıf 3 (watchdog.py::check_integrity_and_alarm): kind="coherence", artifact=<defter adı>."""
    e = {"alarm": "MECHANISM_STALE", "message": "BAYAT TÜREV: plans.json kaynağından 30 sa geride",
         "kind": "coherence", "artifact": "plans.json"}
    assert selfreview._olay_mekanizma(e) == "coherence:plans.json"


def test_detector_artifactten_ONCE_gelir():
    """Sıra sabittir: ikisi birden varsa `detector` kazanır — iki farklı tur iki farklı ad basarsa
    rapor satırları kıyaslanamaz hâle gelir."""
    e = {"kind": "detector_failed", "detector": "determinism", "artifact": "plans.json"}
    assert selfreview._olay_mekanizma(e) == "detector_failed:determinism"


def test_ciplak_kind_de_gecerli_bir_addir():
    """Sınıf 3'ün ikinci hâli (watchdog.py::check_integrity_and_alarm): kind="parity" + `check` — `check` tanınan bir alan
    DEĞİL, ama çıplak `kind` yine de mesaj önekinden iyi bir addır."""
    e = {"alarm": "MECHANISM_STALE", "message": "MAKULLÜK: universe_coverage — ATLANDI",
         "kind": "parity", "check": "universe_coverage"}
    assert selfreview._olay_mekanizma(e) == "parity"


def test_kindsiz_artifact_tek_basina_doner():
    """`artifact` bağımsız bir basamaktır: kind düşmüş olsa bile okunmayan artefaktın ADI vardır."""
    e = {"alarm": "MECHANISM_STALE", "artifact": "massive_crosscheck.json"}
    assert selfreview._olay_mekanizma(e) == "massive_crosscheck.json"


def test_yalniz_mesaj_60_karakterde_kirpilir():
    """Sınıf 4 — GEÇMİŞ DEFTER satırı (alan adı `mekanizma`, TÜRKÇE; tüketici onu TANIMAZ). Ad
    yerine mesajın öneki geçer: uydurma değildir, olayın kendi metnidir. Kırpma İŞARETLİdir —
    kesik bir satır tam sanılırsa operatör yanlış okur.

    ÜRETİCİ DÜZELTİLDİ (2026-09-03, TSK-101): bu şekli yazan iki üretici
    (`loop._reconcile_gunu_atlandi`, `skill_gorus.kuyruk_kadansi`) artık `mechanism=` basar. ÇİVİ KALIR ve
    fikstür de Türkçe alanla kalır: defterde YAZILI geçmiş satırlar bu şekildedir ve pencereli
    tüketiciler onları okumaya devam eder — düşüşün bu basamağı geçmişin okunabilirliğidir."""
    mesaj = "mutabakat 3 işlem günüdür koşmuyor — pozisyon sapması ÖLÇÜLMÜYOR ve bu satır uzundur"
    assert len(mesaj) > 60, "fikstür mesajı 60'tan kısa — çivi kırpmayı ölçmüyor"
    e = {"alarm": "MECHANISM_STALE", "message": mesaj,
         "mekanizma": "broker_reconcile", "gun": 3}
    assert selfreview._olay_mekanizma(e) == mesaj[:60] + "…"


def test_kisa_mesaj_kirpilmadan_doner():
    """60'tan kısa mesaj olduğu gibi döner — sahte bir "…" mesajı kesikmiş gibi gösterirdi."""
    e = {"alarm": "MECHANISM_STALE", "message": "ÖĞRENME DURDU"}
    assert selfreview._olay_mekanizma(e) == "ÖĞRENME DURDU"


def test_hicbir_alan_yoksa_None():
    """UYDURMA YASAĞI: ad ölçülemediğinde None döner. "bilinmeyen"/"?" gibi bir yer tutucu, boş
    olduğu ANLAŞILAMAYAN bir satır üretirdi."""
    assert selfreview._olay_mekanizma({}) is None
    assert selfreview._olay_mekanizma({"alarm": "MECHANISM_STALE", "ts": "2026-09-02T00:00:00+00:00"}) is None


# =================================================================================================
# B) ENTEGRASYON — rapor satırı yardımcıyı GERÇEKTEN çağırıyor mu?
# =================================================================================================
def test_rapor_satiri_mechanismsiz_olayda_da_ad_tasir(sandbox_state):
    """Yardımcının doğru olması YETMEZ: `build()` onu çağırmazsa canlı rapor yine `null` basar.
    Fikstür, canlıdaki baskın sınıfı (mechanism YOK, kind+detector VAR) haftalık pencereye koyar."""
    simdi = dt.datetime.now(dt.timezone.utc)
    store.append_jsonl("events.jsonl", {
        "ts": (simdi - dt.timedelta(days=2)).isoformat(timespec="seconds"), "level": "alarm",
        "event": "MECHANISM_STALE BÜTÜNLÜK DEDEKTÖRÜ DÜŞTÜ: determinism",
        "alarm": "MECHANISM_STALE",
        "message": "BÜTÜNLÜK DEDEKTÖRÜ DÜŞTÜ: determinism hüküm veremedi — KeyError",
        "kind": "detector_failed", "detector": "determinism"})
    rows = selfreview.build()["week"]["watchdog_incidents"]
    assert len(rows) == 1, rows
    assert rows[0]["mechanism"] == "detector_failed:determinism", \
        "rapor satırı hâlâ ham `mechanism` alanını okuyor — düşüş sırası build()'e bağlanmamış"
    # `gap_h` bu sınıfta YOKTUR ve None kalması dürüst boşluktur (uydurulmaz).
    # ZARF BÜYÜDÜ (2026-09-03, TSK-102): satır `sure_h`/`sure_kaynak` de taşır. `gap_h`ın
    # KORUNMASI bu çivinin asıl iddiasıdır — yeni alanlar onun YERİNE geçmez, YANINA gelir.
    assert rows[0]["gap_h"] is None, rows[0]
    assert set(rows[0]) == {"mechanism", "gap_h", "sure_h", "sure_kaynak"}, rows[0]
    # detector_failed olayında hiçbir süre alanı yok → ölçülemeyen süre uydurulmaz
    assert rows[0]["sure_h"] is None and rows[0]["sure_kaynak"] is None, rows[0]


def test_rapor_mechanismli_olayda_ham_adi_KORUR(sandbox_state):
    """Karşı yön: düşüş sırası eklenirken sınıf 1'in doğru davranışı bozulmamalı — gap_h da taşınır."""
    simdi = dt.datetime.now(dt.timezone.utc)
    store.append_jsonl("events.jsonl", {
        "ts": (simdi - dt.timedelta(days=1)).isoformat(timespec="seconds"), "level": "alarm",
        "event": "MECHANISM_STALE mekanizma gecikti: cf_advance",
        "alarm": "MECHANISM_STALE", "message": "mekanizma gecikti: cf_advance — nabız sessiz",
        "mechanism": "cf_advance", "gap_h": 31.5, "gap_s": 113400, "asim_s": 3600})
    rows = selfreview.build()["week"]["watchdog_incidents"]
    # `sure_h`/`sure_kaynak` 2026-09-03'te (TSK-102) eklendi; sınıf 1'de kaynak `gap_h`tır.
    assert len(rows) == 1 and rows[0] == {"mechanism": "cf_advance", "gap_h": 31.5,
                                          "sure_h": 31.5, "sure_kaynak": "gap_h"}, rows
