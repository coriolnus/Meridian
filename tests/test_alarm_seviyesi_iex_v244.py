"""test_alarm_seviyesi_iex_v244.py — v244 KALEM 3: alarm kutusunun %68'i IEX seyrekliğini ölçüyordu.

KANIT: docs/TESHIS-ALARM-GURULTUSU-IEX-SEYREKLIGI-2026-08-14.md.
Seans-içi akış IEX'tir (`marketstream.FEED`); IEX ABD hacminin küçük bir payını basar ve orta
ölçekli bir isimde bazı dakikalarda HİÇ IEX baskısı olmaz. "Seansın her dakikasında bu sembolden
bir baskı olmalı" beklentisi KONSOLİDE (SIP) besleme kalitesindedir. Ayırt edici ölçüm: geçmiş
`tur="sembol"` alarm havuzundan (n=1717) sabit tohumla 15 rastgele alarm çekildi ve her biri iki
beslemeye soruldu → SEYREKLİK 15 · GERÇEK-KESİNTİ 0 (IEX'te 1 bar, konsolidede 4-10).
Maliyet: günde 408 olay = warn/error kutusunun ~%68'i; para riski taşıyan
`korumasiz_motor_disi_pozisyon` günde 13 — en önemli alarm, en gürültülüsünün 1/31'i kadar görünür.

BU DOSYA ÇİVİLER:
  K2 — `tur="sembol"` BİLGİ seviyesinde (`obs.log`), `tur="akis"` HÂLÂ `warn`
  K1 — olayın künyesinde etkin besleme var ve SABİT KODLU DEĞİL (`marketstream.FEED`)
  KORUNAN — aynı boşluk iki kez basılmaz · olay ADI/alanları aynı (veri kaybı yok) ·
            `gap_scan`ın kendi hükümleri (takvim_yok / seans_disi / arsiv_yok) değişmedi

NEDEN SEVİYE İŞE YARIYOR (varsayım değil, kaynakta yazılı): `watchdog.SEVIYE_EEMUA` yalnız
`warn`/`alarm` sayar — "`info` bütçeye GİRMEZ: bir alarm değil, bir kayıt satırıdır". Yani bu
değişiklik EEMUA alarm yükünü gerçekten düşürür, satırı gizlemez.
"""
from __future__ import annotations

import datetime as dt
import inspect

import pytest

from meridian import barsarchive, scheduler, watchdog

NY_ACIK = dt.datetime(2026, 7, 30, 14, 30, tzinfo=dt.timezone.utc)   # 09:30 ET (yaz), Perşembe


def _akis(baslangic, dakika, semboller=("AAA", "BBB"), atla=()):
    """Sentetik akış (v147'nin yardımcısıyla aynı sözleşme): `atla` = (sembol|None, ilk_dk, son_dk);
    sembol None ise O DAKİKALARDA HİÇBİR sembol bar üretmez (gerçek akış kesintisi)."""
    rows = []
    for i in range(dakika):
        t = (baslangic + dt.timedelta(minutes=i)).isoformat().replace("+00:00", "Z")
        for s in semboller:
            if any((sem is None or sem == s) and a <= i <= b for sem, a, b in atla):
                continue
            rows.append((s, t))
    return rows


@pytest.fixture
def kanca(monkeypatch):
    """GERÇEK `gap_scan` + sentetik satırlar: rapor uydurulmuyor, ÖLÇÜLÜYOR. Rapor HER İKİ türü de
    taşır (akis + sembol) — ayrımın testi tek raporda yan yana durmalı, yoksa "biri warn biri log"
    iddiası iki ayrı kurulumun yan etkisi olabilirdi.

    `obs.log` ve `obs.warn` AYRI listelere yazılır: bu testin ölçtüğü şey olayın VARLIĞI değil,
    SEVİYESİDİR."""
    rapor = barsarchive.gap_scan(as_of=NY_ACIK + dt.timedelta(minutes=62),
                                 rows=_akis(NY_ACIK, 62, atla=[(None, 20, 27), ("AAA", 40, 45)]))
    assert {b["tur"] for b in rapor["bosluklar"]} == {"akis", "sembol"}, "fikstür iki türü kurmadı"
    monkeypatch.setattr(barsarchive, "gap_scan", lambda *a, **k: rapor)
    monkeypatch.setattr(scheduler.store, "write_json", lambda *a, **k: None)
    import meridian.obs as obs
    bilgi, uyari = [], []
    monkeypatch.setattr(obs, "log", lambda ev, **kw: bilgi.append((ev, kw)))
    monkeypatch.setattr(obs, "warn", lambda ev, **kw: uyari.append((ev, kw)))
    for k in ("intraday_gap", "intraday_gap_seen"):
        scheduler._state.pop(k, None)
    yield bilgi, uyari, rapor
    for k in ("intraday_gap", "intraday_gap_seen"):
        scheduler._state.pop(k, None)


# ================================ K2 — SEVİYE ===================================================
def test_k2_sembol_boslugu_BILGI_seviyesine_indi(kanca):
    """ASIL KAZANÇ: örneklemde susturulacak GERÇEK kesinti yok (15/15 seyreklik). Satır defterde
    kalır, alarm kutusunda değil."""
    bilgi, uyari, _ = kanca
    scheduler._intraday_gap_check()
    sembol = [kw for ev, kw in bilgi if ev == "intraday_gap_detected"]
    assert len(sembol) == 1 and sembol[0]["tur"] == "sembol" and sembol[0]["sembol"] == "AAA"
    assert not [kw for ev, kw in uyari
                if ev == "intraday_gap_detected" and kw["tur"] == "sembol"], \
        "sembol-boşluğu hâlâ warn basıyor — kutunun %68'i geri geldi"


def test_k2_akis_boslugu_HALA_WARN(kanca):
    """KARŞI-ÇİVİ (bu turun en önemli satırı): bütün sembollerde EŞ-ANLI susma gerçek soket/besleme
    kesintisidir ve nadir gerçek kesinti K2'den SONRA bu kanalda görünmeye devam eder. Susturulsaydı
    gürültüyle birlikte sinyali de kaybederdik."""
    bilgi, uyari, _ = kanca
    scheduler._intraday_gap_check()
    akis = [kw for ev, kw in uyari if ev == "intraday_gap_detected"]
    assert len(akis) == 1 and akis[0]["tur"] == "akis"
    assert akis[0]["eksik_dk"] == 8 and akis[0]["aralik"] == "14:50-14:57Z"
    assert not [kw for ev, kw in bilgi
                if ev == "intraday_gap_detected" and kw["tur"] == "akis"]


def test_k2_info_EEMUA_butcesine_girmez():
    """SEVİYENİN ANLAMI KAYNAKTA KİLİTLİ: `info` bir alarm değil kayıt satırıdır ve alarm yüküne
    girmez. Bu eşleme değişirse K2 kazancı sessizce buharlaşırdı."""
    assert set(watchdog.SEVIYE_EEMUA) == {"warn", "alarm"}, "info alarm bütçesine sokulmuş"


# ================================ K1 — BESLEME KÜNYESİ ==========================================
def test_k1_kunye_her_iki_turde_de_var(kanca):
    bilgi, uyari, _ = kanca
    scheduler._intraday_gap_check()
    hepsi = [kw for ev, kw in bilgi + uyari if ev == "intraday_gap_detected"]
    assert len(hepsi) == 2
    for kw in hepsi:
        assert "feed" in kw, "olay hangi beslemeyi ölçtüğünü söylemiyor"


def test_k1_kunye_marketstreamden_gelir_SABIT_KODLU_DEGIL(kanca, monkeypatch):
    """SIP'e geçildiği gün künye kendiliğinden doğruyu söylemeli. "iex" yazsaydık künyenin kendisi
    ilk gün bayatlar ve tam da düzeltmeye çalıştığımız yanlış-zemin sınıfını üretirdi."""
    from meridian import marketstream
    monkeypatch.setattr(marketstream, "FEED", "sip")
    bilgi, uyari, _ = kanca
    scheduler._intraday_gap_check()
    assert {kw["feed"] for ev, kw in bilgi + uyari if ev == "intraday_gap_detected"} == {"sip"}


def test_k1_kunye_olculemezse_UYDURULMAZ(kanca, monkeypatch):
    """UYDURMA YASAĞI: besleme okunamazsa ad None kalır ve NEDEN olayda taşınır — "iex" varsayımı
    yazmak, ölçülmemiş bir künyeyi ölçülmüş gibi göstermek olurdu."""
    monkeypatch.setattr(scheduler, "_akis_beslemesi", lambda: (None, "ImportError: sinama"))
    bilgi, uyari, _ = kanca
    scheduler._intraday_gap_check()
    for ev, kw in bilgi + uyari:
        if ev == "intraday_gap_detected":
            assert kw["feed"] is None and kw["feed_neden"] == "ImportError: sinama"


def test_k1_kunye_olcumu_kontrolu_DUSUREMEZ(kanca, monkeypatch):
    """Bir ETİKET uğruna boşluk taraması ÖLMEZ: akış katmanı okunamazsa `_akis_beslemesi`
    (None, neden) döner ve tarama aynen koşar. YASA 4'ün kapattığı sınıf tam budur — kontrolün
    kendisi bir süs alanı yüzünden kaybolamaz."""
    from meridian import marketstream
    monkeypatch.delattr(marketstream, "FEED")          # akış katmanı sözleşmesini kaybetti
    ad, neden = scheduler._akis_beslemesi()
    assert ad is None and "AttributeError" in neden
    bilgi, uyari, _ = kanca
    scheduler._intraday_gap_check()                    # ve tarama YİNE de hüküm basar
    assert len([1 for ev, _ in bilgi + uyari if ev == "intraday_gap_detected"]) == 2


# ================================ KORUNAN DAVRANIŞ ==============================================
def test_korunan_ayni_bosluk_iki_kez_basilmaz(kanca):
    """İmza defteri (gün|tür|sembol|başlangıç) DEĞİŞMEDİ: pencere (60 dk) iki poll'ü fazlasıyla
    kapsar, yani aynı boşluk her poll'de yeniden görünür ve tek kez basılmalıdır."""
    bilgi, uyari, _ = kanca
    scheduler._intraday_gap_check()
    scheduler._intraday_gap_check()
    n = len([1 for ev, _ in bilgi + uyari if ev == "intraday_gap_detected"])
    assert n == 2, f"tekrar-bastırma bozuldu — her poll'de yeniden basılıyor (n={n})"


def test_korunan_olay_adi_ve_alanlari_ayni(kanca):
    """VERİ KAYBI YOK: olay ADI ve alan kümesi bugünkü sözleşmeyle aynı; `feed` YANINA eklendi."""
    bilgi, uyari, _ = kanca
    scheduler._intraday_gap_check()
    for ev, kw in bilgi + uyari:
        assert ev == "intraday_gap_detected"
        assert {"tur", "sembol", "gun", "aralik", "eksik_dk", "beklenen", "gelen",
                "pencere_dk", "detail"} <= set(kw)


def test_korunan_durum_kopyasi_ve_pano_alani_ayni(kanca):
    """`_state["intraday_gap"]` gövdesi DEĞİŞMEDİ — panonun (`/api/diagnostics` → `_gapRows`)
    okuduğu yüzey bu turda hiç oynamadı."""
    _, _, rapor = kanca
    scheduler._intraday_gap_check()
    st = scheduler._state["intraday_gap"]
    assert st["bosluk_sayisi"] == rapor["bosluk_sayisi"] == 2 and st["yeni_uyari"] == 2
    assert set(st) == {"durum", "gun", "olculdu", "pencere", "sembol", "gelen_bar", "bozuk_satir",
                       "bosluk_sayisi", "esik", "bosluklar", "yeni_uyari"}
    src = inspect.getsource(scheduler._intraday_gap_check)
    assert "gorulen[-GAP_SEEN_MAX:]" in src, "imza defteri budaması kayboldu (sızıntı)"


@pytest.mark.parametrize("durum", ["takvim_yok", "seans_disi", "arsiv_yok"])
def test_korunan_gap_scan_hukumleri_degismedi(monkeypatch, durum):
    """`gap_scan`ın ÖLÇEMEDİĞİ hâllerde hüküm basılmaz (uydurma yasağı) ve durum kopyası minimal
    kalır. Bu tur seviyeye dokundu, hükümlere DEĞİL."""
    rapor = {"durum": durum, "gun": "2026-07-30", "olculdu": "2026-07-30T15:32:00+00:00",
             "seans": {"durum": durum, "takvim": "XNYS", "acilis": None, "kapanis": None,
                       "hata": "sinama" if durum == "takvim_yok" else None},
             "bosluklar": [{"tur": "sembol", "sembol": "AAA", "baslangic": "x", "bitis": "y",
                            "eksik_dk": 5, "beklenen": 1, "gelen": 0}]}
    monkeypatch.setattr(barsarchive, "gap_scan", lambda *a, **k: rapor)
    monkeypatch.setattr(scheduler.store, "write_json", lambda *a, **k: None)
    import meridian.obs as obs
    gorulen = []
    monkeypatch.setattr(obs, "log", lambda ev, **kw: gorulen.append(ev))
    monkeypatch.setattr(obs, "warn", lambda ev, **kw: gorulen.append(ev))
    monkeypatch.setattr(scheduler, "_GAP_CALENDAR_WARNED", True)   # süreç-başı uyarı bu testin işi değil
    for k in ("intraday_gap", "intraday_gap_seen"):
        scheduler._state.pop(k, None)
    try:
        scheduler._intraday_gap_check()
        assert "intraday_gap_detected" not in gorulen, "ölçülemeyen turda BOŞLUK HÜKMÜ basıldı"
        st = scheduler._state["intraday_gap"]
        assert st["durum"] == durum and "bosluklar" not in st
        assert ("seans" in st) is (durum == "takvim_yok")
    finally:
        for k in ("intraday_gap", "intraday_gap_seen"):
            scheduler._state.pop(k, None)
