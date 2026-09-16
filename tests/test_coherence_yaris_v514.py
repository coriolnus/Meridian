"""test_coherence_yaris_v514.py — TSK-203: bayatlık denetimi SIRA YARIŞI.

ÖLÇÜLEN ARIZA (A1 SQLite entity_meta damgaları, 2026-09-16 akşamı):

  · 20:34:17Z  `trades.jsonl` yazıldı (bir işlem kapandı)
  · 20:34:59Z  `MECHANISM_STALE BAYAT TÜREV: equity_curve.json kaynağından 23.9 sa geride (eşik 1.0 sa)`
  · 20:34:59,29Z `equity_curve.json` yazıldı — alarmdan 0,29 saniye SONRA

Eğrinin o günkü noktası defterde VARDI; eğri bayat DEĞİLDİ, denetim iki yazımın ARASINA düştü.
`watchdog.coherence_report` bayrağı `türev < kaynak − eşik` koşuluyla kaldırıyordu: eşik kaynak ile
türev ARASINDAKİ farka uygulanıyor, kaynağın NE ZAMAN güncellendiğine uygulanmıyordu. Kaynakla
türevin yazımı arasına düşen HER yoklama — 42 saniyelik bir aralıkta bile — sahte alarm üretirdi.

ROL-1 KARARI (TSK-203 tur 2): koşula ikinci şart — `şimdi − kaynak > COHERENCE_GRACE_S`. Yani
"kaynak güncellemesinin üzerinden bir döngü payı geçti VE türev kendi kadans eşiğinden fazla
geride" → bayrak. Bekleme türevin eşiği DEĞİL, döngü payıdır: tur 1'de beklemeye eşik konmuştu ve
haftalık türevler (eşik 9 gün + 1 sa, kaynakları her gün ilerler) KALICI olarak kör kalıyordu (K7).
"Şimdi" modülün saat desenidir (`watchdog._now`); bu dosya onu çiviler, gerçek saate bağlı DEĞİLDİR.

ÇİVİLER:
  K1  YARIŞ — kaynak az önce yazıldı (şimdi − kaynak ≤ pay), türev geride → bayrak YOK
  K1b ÇOK KAYNAKLI türevde bekleme EN YENİ kaynaktan ölçülür
  K2  GERÇEK BAYATLIK — kaynak paydan eski, türev eşikten fazla geride → bayrak VAR
  K3  TÜREV YETİŞTİ — türev kaynaktan yeni → bayrak YOK (regresyon)
  K4  HAFTALIK TÜREV — yarış şartı aynı payla; bayrak TSK-191 kadans eşiği aşılınca
  K5  RAPOR ALANLARI — `behind_h`/`esik_h` eski formülle AYNI değeri taşır; yoklama anı sızmaz
  K6  VAKA YENİDEN ÜRETİMİ — 2026-09-16 zaman çizelgesi → bayrak YOK; aynı çizelgede türev
      gerçekten yazılmasaydı alarm TAM O sayılarla (23.9 / 1.0) kalkardı
  K7  HAFTALIK TÜREV KÖR KALMAZ — kaynağı her gün ilerleyen haftalık türev kadansını aşınca
      bayrak VAR (tur 1 tasarımının kaybını kapatan çivi)
"""
from __future__ import annotations

import datetime as dt
import os

import pytest

from meridian import config, store, watchdog


def _epoch(iso: str) -> float:
    """ISO-8601 UTC → epoch saniyesi (çizelge okunur kalsın diye sayılar ISO ile yazılır)."""
    return dt.datetime.fromisoformat(iso).replace(tzinfo=dt.timezone.utc).timestamp()


SIMDI = _epoch("2026-09-16T20:34:59")          # vaka yoklama anı; tüm çiviler bu saate çivilenir
SAAT = 3600.0
GUN = 24 * SAAT
PAY = watchdog.COHERENCE_GRACE_S                 # bekleme süresi — kaynağından okunur, sayılmaz
HAFTALIK = ("arming_report.json", "self_review.json")


@pytest.fixture
def saat(sandbox_state, monkeypatch):
    """`watchdog._now` çivilenir; çivi `saat.t = …` ile yoklama anını oynatır."""
    class _Saat:
        t = SIMDI
    s = _Saat()
    monkeypatch.setattr(watchdog, "_now", lambda: s.t)
    return s


def _yaz(ad: str, t: float) -> None:
    """`ad` artefaktını sandbox state'e yazıp damgasını `t`ye çeker; damga dedektörün okuduğu
    yoldan (`store.mtime`) geri okunur — fikstür dedektörü GERÇEKTEN beslemiyorsa çivi yanlış
    sebeple yeşil olurdu."""
    yol = config.STATE / ad
    yol.write_text('{"id": "x"}\n' if ad.endswith(".jsonl") else "{}")
    os.utime(yol, (t, t))
    assert store.mtime(ad) == pytest.approx(t, abs=1e-3), f"{ad} damgası dedektöre ulaşmıyor"


def _kurgu(art: str, kaynak_t: float, turev_t: float) -> None:
    """`art` türevini `turev_t`de, BEYAN EDİLMİŞ kaynaklarının hepsini `kaynak_t`de damgalar.
    Kaynak listesi `DERIVED_SOURCES`ten okunur — test kendi kopyasını tutmaz."""
    for src in watchdog.DERIVED_SOURCES[art]:
        _yaz(src, kaynak_t)
    _yaz(art, turev_t)


def _satir(art: str) -> dict | None:
    """`art` için `coherence_report` bayat satırı (yoksa None)."""
    for s in watchdog.coherence_report()["stale"]:
        if s["artifact"] == art:
            return s
    return None


GUNLUK = "near_miss.json"                        # DERIVED_MECHANISM'da kaydı YOK → eşik = pay


def test_K0_pay_bir_saattir_ve_haftalik_esik_paydan_genis():
    """Çivilerin kurgusu iki ölçeğin AYRI olmasına dayanır: pay (bekleme) ile haftalık eşik
    (bayrak). İkisi çakışırsa K4/K7 hangi şartı ölçtüğünü söyleyemez."""
    assert PAY == 3600
    for art in HAFTALIK:
        assert watchdog._coherence_esik_s(art) > 2 * GUN, f"{art} eşiği paya yakın"


# --------------------------------------------------------------------------------------------
# K1 — YARIŞ: kaynak az önce yazıldı → bayrak YOK
# --------------------------------------------------------------------------------------------
@pytest.mark.parametrize("gecen_s", [0.0, 42.0, "pay-1", "pay"])
def test_K1_YARIS_kaynak_az_once_yazildi_turev_geride_BAYRAK_YOK(saat, gecen_s):
    """Kaynak yoklamadan `gecen_s` önce ilerledi, türev kaynaktan 2 sa geride (eşiği aşmış).
    Üretici aynı döngüde türevi yazmak ÜZERE — pay dolmadan hüküm verilmez. Sınır (`= pay`) da
    bekleme penceresinin İÇİNDEDİR (şart kesin büyüktür)."""
    assert GUNLUK not in watchdog.DERIVED_MECHANISM
    gecen = {"pay-1": PAY - 1, "pay": PAY}.get(gecen_s, gecen_s)
    kaynak_t = SIMDI - gecen
    _kurgu(GUNLUK, kaynak_t, kaynak_t - 2 * SAAT)
    assert _satir(GUNLUK) is None, \
        f"kaynak {gecen} sn önce yazıldı ve bayrak kalktı — sıra yarışı geri geldi"


def test_K1b_cok_kaynakli_turevde_bekleme_EN_YENI_kaynaktan_olculur(saat):
    """`score_calibration.json` iki defterden beslenir. cf iki gün önce, trades 42 sn önce
    ilerledi; türev üç gün eski. Bekleme EN YENİ kaynaktan ölçülür: trades'in yazımına üretici
    henüz yetişemedi → bayrak YOK. En eski kaynağa bakan bir şart yarışı yeniden açardı."""
    art = "score_calibration.json"
    assert watchdog.DERIVED_SOURCES[art] == ["counterfactuals.jsonl", "trades.jsonl"]
    _yaz("counterfactuals.jsonl", SIMDI - 2 * GUN)
    _yaz("trades.jsonl", SIMDI - 42)
    _yaz(art, SIMDI - 3 * GUN)
    assert _satir(art) is None


# --------------------------------------------------------------------------------------------
# K2 — GERÇEK BAYATLIK: kaynak paydan eski → bayrak VAR
# --------------------------------------------------------------------------------------------
@pytest.mark.parametrize("fazla_s", [1.0, 60.0, GUN])
def test_K2_GERCEK_BAYATLIK_kaynak_paydan_eski_turev_geride_BAYRAK_VAR(saat, fazla_s):
    """Kaynak pay + `fazla_s` önce ilerledi, türev hâlâ 2 sa geride: üreticiye bir döngü
    verildi ve yetişmedi — bu gerçek bayatlıktır. Yarış onarımı dedektörü KÖRLEŞTİRMEZ."""
    kaynak_t = SIMDI - PAY - fazla_s
    _kurgu(GUNLUK, kaynak_t, kaynak_t - 2 * SAAT)
    s = _satir(GUNLUK)
    assert s is not None, "kaynak paydan eski, türev geride ve bayrak KALKMADI — dedektör kör"
    assert s["behind_h"] == 2.0 and s["esik_h"] == 1.0, s


# --------------------------------------------------------------------------------------------
# K3 — TÜREV YETİŞTİ → bayrak YOK
# --------------------------------------------------------------------------------------------
@pytest.mark.parametrize("kaynak_once_s", [42.0, 3 * GUN])
def test_K3_turev_kaynaktan_YENI_BAYRAK_YOK(saat, kaynak_once_s):
    """Türev kaynaktan sonra yazıldıysa kaynağın ne kadar eski olduğu önemsizdir: türev onu
    görmüştür. İkinci şart birinci şartın YERİNE geçmez, ona EKLENİR."""
    kaynak_t = SIMDI - kaynak_once_s
    _kurgu(GUNLUK, kaynak_t, kaynak_t + 1)
    assert _satir(GUNLUK) is None


# --------------------------------------------------------------------------------------------
# K4 — HAFTALIK TÜREV: aynı pay, TSK-191 eşiği
# --------------------------------------------------------------------------------------------
@pytest.mark.parametrize("gecen_s", [42.0, "pay"])
@pytest.mark.parametrize("art", HAFTALIK)
def test_K4a_haftalik_turev_YARIS_kaynak_az_once_BAYRAK_YOK(saat, art, gecen_s):
    """Haftalık türev kadansını AŞMIŞ geride (eşik + 1 gün), ama kaynak paydan kısa süre önce
    ilerledi: yarış şartı günlük türevle AYNI payla uygulanır."""
    esik = watchdog._coherence_esik_s(art)
    kaynak_t = SIMDI - {"pay": PAY}.get(gecen_s, gecen_s)
    _kurgu(art, kaynak_t, kaynak_t - esik - GUN)
    assert _satir(art) is None


@pytest.mark.parametrize("art", HAFTALIK)
def test_K4b_haftalik_turev_kaynak_PAYDAN_eski_esik_asilmis_BAYRAK_VAR(saat, art):
    """Aynı türev, kaynak paydan 60 sn fazla önce ilerlemiş: bekleme doldu, türev kadansını
    aştı → bayrak; `esik_h` TSK-191 türetmesinin kendisidir (test sabit saymaz)."""
    esik = watchdog._coherence_esik_s(art)
    kaynak_t = SIMDI - PAY - 60
    _kurgu(art, kaynak_t, kaynak_t - esik - GUN)
    s = _satir(art)
    assert s is not None, f"{art} kadans+pay aşıldı, bekleme doldu ve bayrak KALKMADI"
    assert s["esik_h"] == round(esik / 3600, 1)
    assert s["behind_h"] == round((esik + GUN) / 3600, 1)


@pytest.mark.parametrize("art", HAFTALIK)
def test_K4c_haftalik_turev_KADANSININ_icinde_bekleme_dolmus_olsa_da_BAYRAK_YOK(saat, art):
    """Pay yalnız BEKLEMEdir, bayrak eşiğinin yerine geçmez: kaynak dün ilerledi (bekleme çoktan
    doldu), türev 6 gün geride — haftalık kadansın içinde, normal çalışma (TSK-191)."""
    kaynak_t = SIMDI - GUN
    _kurgu(art, kaynak_t, kaynak_t - 6 * GUN)
    assert _satir(art) is None


# --------------------------------------------------------------------------------------------
# K5 — RAPOR ALANLARI DEĞİŞMEZ
# --------------------------------------------------------------------------------------------
@pytest.mark.parametrize("art,geride_s", [(GUNLUK, 10 * SAAT), ("arming_report.json", 10 * GUN)])
def test_K5_rapor_alanlari_ESKI_formulle_ayni_ve_yoklama_ani_SIZMAZ(saat, art, geride_s):
    """Tüketiciler (alarm satırı, v505, TSK-102) `behind_h` = kaynak − türev ve `esik_h` = eşik
    okur. Yeni şart yalnız HÜKMÜ değiştirir: satırın anahtarları ve değerleri eski formülle
    birebir aynıdır ve yoklama anı değişince (bir gün sonra) satır DEĞİŞMEZ."""
    esik = watchdog._coherence_esik_s(art)
    kaynak_t = SIMDI - PAY - 60
    _kurgu(art, kaynak_t, kaynak_t - geride_s)
    beklenen = {"artifact": art, "behind_h": round(geride_s / 3600, 1),
                "esik_h": round(esik / 3600, 1)}
    ilk = _satir(art)
    assert ilk == beklenen, ilk
    saat.t = SIMDI + GUN
    assert _satir(art) == beklenen, "yoklama anı rapor alanlarına sızdı"


# --------------------------------------------------------------------------------------------
# K6 — VAKA YENİDEN ÜRETİMİ (2026-09-16)
# --------------------------------------------------------------------------------------------
KAYNAK_T = _epoch("2026-09-16T20:34:17")
ONCEKI_EGRI_T = _epoch("2026-09-15T20:40:00")    # bir önceki günlük eğri yazımı (bir gün önce)
EGRI_T = _epoch("2026-09-16T20:34:59") + 0.29    # alarmdan 0,29 sn SONRA


def test_K6_VAKA_2026_09_16_yoklama_iki_yazimin_ARASINDA_BAYRAK_YOK(saat):
    """Kaynak 20:34:17Z, yoklama 20:34:59Z, türev bir gün önce: eski koşul burada
    "23.9 sa geride (eşik 1.0 sa)" diye alarm verdi. Yeni koşulda bayrak YOK."""
    assert watchdog.DERIVED_SOURCES["equity_curve.json"] == ["trades.jsonl"]
    _kurgu("equity_curve.json", KAYNAK_T, ONCEKI_EGRI_T)
    assert _satir("equity_curve.json") is None, "2026-09-16 sıra yarışı hâlâ alarm üretiyor"


def test_K6b_VAKA_turev_0_29_sn_sonra_yazildi_temiz(saat):
    """Aynı çizelgenin devamı: eğri 20:34:59,29Z'de yazıldı; sonraki yoklamalarda türev
    kaynaktan yenidir — iki saat sonra da bayrak YOK."""
    _kurgu("equity_curve.json", KAYNAK_T, EGRI_T)
    saat.t = EGRI_T + 2 * SAAT
    assert _satir("equity_curve.json") is None


def test_K6c_VAKA_turev_HIC_yazilmasaydi_alarm_AYNI_SAYILARLA_kalkardi(saat):
    """Fikstürün vakanın kendisi olduğunun kanıtı: aynı çizelgede eğri yazılMAsaydı, bekleme
    dolduktan sonra (kaynak + pay + 1 sn) alarm canlıdaki sayılarla kalkar — 23.9 / 1.0."""
    _kurgu("equity_curve.json", KAYNAK_T, ONCEKI_EGRI_T)
    saat.t = KAYNAK_T + PAY + 1
    s = _satir("equity_curve.json")
    assert s == {"artifact": "equity_curve.json", "behind_h": 23.9, "esik_h": 1.0}, s


# --------------------------------------------------------------------------------------------
# K7 — HAFTALIK TÜREV KÖR KALMAZ
# --------------------------------------------------------------------------------------------
@pytest.mark.parametrize("art", HAFTALIK)
def test_K7_haftalik_turev_kaynagi_her_gun_ilerlerken_esigi_asinca_BAYRAK_VAR(saat, art):
    """TUR 1 TASARIMININ KAYBINI KAPATAN ÇİVİ (Rol-1 kararı, TSK-203 tur 2).

    Tur 1'de bekleme süresi türevin EŞİĞİYDİ (`şimdi − kaynak > eşik`). Haftalık türevlerde eşik
    9 gün + 1 sa'dir; kaynakları (cf/trades defterleri; self_review için günlük kalibrasyonlar)
    ise HER GÜN ilerler (TSK-191 şerhinin kendi ölçümü). Kaynak her gün ilerledikçe bekleme her
    gün baştan başlıyordu: türev 10 gün geride olsa da bayrak HİÇ kalkmıyordu — ve
    `self_review.json` için ikinci bekçi YOKTUR.

    Bekleme artık döngü payıdır: kaynak dün ilerledi (pay çoktan doldu), türev kaynaktan 10 gün
    geride (eşiği aştı) → bayrak VAR. Beklemeye eşik geri konursa bu çivi kırmızıya döner."""
    esik = watchdog._coherence_esik_s(art)
    kaynak_t = SIMDI - GUN                              # dün ilerledi (günlük kadans)
    _kurgu(art, kaynak_t, kaynak_t - 10 * GUN)          # türev 10 gün geride
    assert 10 * GUN > esik and SIMDI - kaynak_t < esik, "kurgu iki ölçeği ayırmıyor"
    s = _satir(art)
    assert s is not None, f"{art} kaynağı her gün ilerlerken kadansını aştı ve bayrak KALKMADI"
    assert s == {"artifact": art, "behind_h": 240.0, "esik_h": round(esik / 3600, 1)}, s
