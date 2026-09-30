"""v606 — EXE-2026-012 ALETİ: KILL#1 canlı çapasının TUR İÇİ ATIF kaydı (TSK-020 UYGULA-9 Faz C, A dilimi, 2026-09-30).

KART-ÖNCE: kart `research/cards/EXE-2026-012-kill1-canli-capa.yaml` 2e00cf2d'de ön-kayıtlı; bu dosya ve aletin kodu
ondan SONRA yazıldı ve kartın `olcum_plani` ALET maddelerini BİREBİR çiviler. Kartın eşik/kill/hüküm alanlarına bu
dosya dokunmaz; hüküm betiği (research/olcumler/exe012_kill1_canli/, PK-1/PK-2/NK/PK-3 uçtan uca) B dilimidir.

HER BÖLÜM BİR ALET MADDESİ:
  A (1) X = `DONGU_SURESI`ne işlenen değerin KENDİSİ — tek ölçüm, iki görünüm; ikinci kronometre YOK. Sahte saatle
        değer EŞİTLİĞİ (yaklaşık değil) + kartın "tanık eşi" (defter X'lerinin kova sayımı = histogramın processed
        sayımı; Prometheus tanığının süreç-içi karşılığı).
  B (2) Z = planli dal gövdesinin süresi, olaydaki semboller üzerinden TOPLANIR, AYNI saatle; silahlı dal ve
        plansız sembol Z'ye GİRMEZ; olaylar arası sıfırlanır; hata dalı gövdeye dahildir.
  C (3) Evren: `processed` + `error` kaydedilir, `skipped` (seans/pencere/HALT) KAYDEDİLMEZ; alanlar sıralı ve
        yuvarlamasız; kayıt X ölçüldükten SONRA eklenir (X'e GİRMEZ — sahte saatle kanıt); istisna yolunda da.
  D (4) Toplu yazım: seans kapısında dönen ilk olayda ya da seans değişince, X ölçümünün DIŞINDA; satır süreç
        başlangıç damgasını + pid'i taşır; yazım düşerse kayıp adıyla uyarıya düşer, tampon sınırsız büyümez.
  E (5) Kapatma bayrağı (`MERIDIAN_TUR_ATIF`, varsayılan AÇIK): kapalıyken kayıt/defter YOK ve sıcak yolun bütün
        çıktıları (defterler, sayaçlar, dönüş, histogram sayımları) açık hâlle BAYT-EŞİT.
  F     Yasa 6 + kartın OTOMATİK KAPI YASAĞI: motor/ops defteri OKUMAZ (yalnız yazar); okuyucusuzluk
        `codelaw.DECLARED_SINKS`te beyanlı ve graf onu DOĞRULUYOR.
  G     Bedel (kart beyanli_sinirlar (4), ADIM-0c `alet_olay_basi_maliyeti_us`): PK bileşimli düzenekte ölçülür ve
        basılır (`-s` ile görünür); tavanlar şişme bekçisidir, kanıt değil.
TUR 2 (düzeltme turu 1, 2026-09-30 — inceleme I-1, M-2/M-3/M-4 + Rol-1 kararı "kapanışta boşaltma"):
  H     I-1: kayıt yolunun arızası turu DÜŞÜREMEZ — temiz tur temiz döner, `except` kolunun kendi istisnası
        maskelenmez; kayıp adıyla (yalnız tür adı) uyarıya düşer, `last_error`a dokunulmaz.
  K     Kapanışta boşaltma (`api._lifespan` kapanış kolu): yalnız `_autostart`ın tüketiciyi KAYDETTİĞİ yaşam
        döngüsünde; boş tampon satır yazmaz; takas + yazım kilit altında (barfeed iş parçacığı kapanışta durmaz);
        kapanış çağrısının arızası kapanışı bozmaz; `bosaltma: kapanis`.
  E1'e M-3 (bayrak kapalıyken `_handle_symbol`da saat okuması/sayaç YOK) ve C6'ya M-4 (alan sırası tek kaynak)
  eklendi.

BAĞIMLILIK BEYANI (inceleme M-6, ertelendi): v217'nin sahne yardımcıları (`_kapilar_olculebilir`, `_plan`, `_bar`,
`RTH`, `SEANS`, `PLAN_GUNU`) bilerek içe aktarılır — kopya ikinci kaynak olurdu; v217 bu adları değiştirirse bu dosya
toplama hatasıyla GÖRÜNÜR biçimde düşer.

Bu dosya `state/`e yalnız `sandbox_state` üzerinden dokunur, ağa çıkmaz. Numara v606: ana checkout + beş worktree'de
boş (ölçüldü 2026-09-30; v604 G3b, v605 TSK-259).
"""
from __future__ import annotations

import ast
import bisect
import datetime as dt
import json
import os
import pathlib
import random
import re
import statistics
import threading
import time

import pytest

from fastapi.testclient import TestClient

from meridian import api, barclock as bc, barfeed as bf, codelaw, gecikme, intraday_cycle as ic, \
    intraday_shadow as ish, marketstream as mk, store
from meridian.adapters import alpaca
from tests.test_golge_planli_kol_v217 import PLAN_GUNU, RTH, SEANS, _bar, _kapilar_olculebilir, _plan

KOK = pathlib.Path(__file__).resolve().parent.parent
KART = KOK / "research" / "cards" / "EXE-2026-012-kill1-canli-capa.yaml"
UTC = dt.timezone.utc
GECE = dt.datetime(2026, 7, 23, 3, 0, 0, tzinfo=UTC)              # 23:00 ET önceki gün — seans dışı
PENCERE_ONCESI = dt.datetime(2026, 7, 23, 13, 35, 0, tzinfo=UTC)   # 09:35 ET — RTH açık, sabah penceresi KAPALI
KAPANIS_SONRASI = dt.datetime(2026, 7, 23, 21, 0, 0, tzinfo=UTC)   # 17:00 ET — AYNI ET günü, seans kapalı
ERTESI_RTH = dt.datetime(2026, 7, 24, 14, 46, 30, tzinfo=UTC)      # ertesi seans 10:46:30 ET


@pytest.fixture(autouse=True)
def _temiz():
    """Tüketici tekil, saat ve tekilleştirme modül-genelidir — testler arasına sızmasın (v217 deseni)."""
    ic._CONSUMER = None
    ic.reset_plans_cache()
    ish.reset_dedup()
    yield
    bc.reset_clock()
    ic._CONSUMER = None
    ic.reset_plans_cache()
    ish.reset_dedup()


# ---- yardımcılar -------------------------------------------------------------------------------------------------

class _Saat:
    """Yalnız `ilerle` ile ilerleyen sahte saat: aradaki her `_saat()` okuması AYNI anı verir → süre DETERMİNİSTİK,
    tam olarak testin enjekte ettiği gecikmenin toplamıdır (float toplamı; değerler ikili kesirli seçildi)."""

    def __init__(self, t: float = 1000.0):
        self.t = t

    def __call__(self) -> float:
        return self.t

    def ilerle(self, s: float) -> None:
        self.t += s


class _AdimliSaat:
    """Her okumada `adim` kadar ilerleyen sahte saat: bir süre, iki okuma ARASINDAKİ okuma sayısını taşır — ikinci
    bir kronometre (fazladan okuma çifti) değeri görünür biçimde DEĞİŞTİRİR."""

    def __init__(self, t: float = 5000.0, adim: float = 0.0009765625):
        self.t, self.adim = t, adim

    def __call__(self) -> float:
        simdi = self.t
        self.t += self.adim
        return simdi


def _gozlem_casusu(monkeypatch) -> list:
    """`DONGU_SURESI.gozlemle`e verilen (saniye, etiket) çiftlerini AYNEN yakalar (sonra özgününü çağırır)."""
    yakalanan: list = []
    ozgun = ic.DONGU_SURESI.gozlemle

    def casus(saniye, etiket_degeri=None):
        yakalanan.append((saniye, etiket_degeri))
        ozgun(saniye, etiket_degeri)

    monkeypatch.setattr(ic.DONGU_SURESI, "gozlemle", casus)
    return yakalanan


def _pk_kur(monkeypatch, *, planli_n: int = 3) -> str:
    """Kartın PK bileşimi (v217 gibi ≥ 5 sembol/olay): silahlı (MSFT) + `planli_n` planli (T0…) + plansız pozisyon
    (POS) + ilgi dışı (ZZZ) — hepsinin barı tetiği keser. Dönüş: olayın `syms` alanı."""
    bc.set_clock(lambda: RTH)
    poz = {"plan_id": "P-ESKI", "ticker": "POS", "side": "long", "entry": 100.0, "stop": 95.0,
           "trail_stop": 95.0, "target": 130.0, "qty": 10, "r_per_share": 5.0,
           "risk_dollars": 50.0, "size_r": 1.0, "ts_open": "2026-07-20"}
    _kapilar_olculebilir(armed=[_plan("MSFT", 50.0)], positions={"POS": poz})
    for i in range(planli_n):
        store.append_jsonl("trade_plans.jsonl", _plan(f"T{i}", 100.0))
    monkeypatch.setattr(ic.hotstate, "read_bars", lambda tk, n: [_bar(o=50.0, h=200.0, c=150.0)])
    return ",".join(["MSFT", *(f"T{i}" for i in range(planli_n)), "POS", "ZZZ"])


def _defter() -> list[dict]:
    return store.read_jsonl(ic.ATIF_DEFTERI)


# =================================================================================================================
# A — (1) X = DONGU_SURESI'ne işlenen değerin KENDİSİ
# =================================================================================================================

def test_A1_X_DONGU_SURESINE_islenen_degerin_KENDISI_ikinci_kronometre_YOK(sandbox_state, monkeypatch):
    syms = _pk_kur(monkeypatch)
    monkeypatch.setattr(gecikme, "_saat", _AdimliSaat())
    casus = _gozlem_casusu(monkeypatch)
    t = ic.consumer()
    for _ in range(3):
        t.on_barfeed_event({"syms": syms})
    assert [e for _, e in casus] == ["processed"] * 3, "kurgu geçersiz: olaylar işlenmedi"
    kayitlar = t._atif_olaylar
    assert len(kayitlar) == 3
    for (x_hist, _), kayit in zip(casus, kayitlar):
        assert kayit[0] == "processed"
        # EŞİTLİK, yaklaşıklık değil: aynı float nesnesinin iki görünümü. Ayrı bir kronometre (fazladan okuma çifti)
        # adımlı saatte en az iki adım fark ederdi.
        assert kayit[1] == x_hist, f"defter X'i ({kayit[1]!r}) histograma işlenen değerden ({x_hist!r}) farklı"


def test_A2_TANIK_ESI_defter_X_kova_sayimi_DONGU_SURESI_processed_ile_ESIT(sandbox_state, monkeypatch):
    """Kart PK 'TANIK EŞİ': defterdeki X'ler `DONGU_SURESI.kovalar` üzerinde bisect_left (le) kuralıyla binlenir;
    kova başına sayım histogramın AYNI aralıktaki processed sayım farkına eşit olmalı (gerçek saat)."""
    syms = _pk_kur(monkeypatch)
    once = ic.DONGU_SURESI.anlik()["processed"]["kova_sayilari"]
    t = ic.consumer()
    for _ in range(40):
        t.on_barfeed_event({"syms": syms})
    sonra = ic.DONGU_SURESI.anlik()["processed"]["kova_sayilari"]
    bc.set_clock(lambda: KAPANIS_SONRASI)
    t.on_barfeed_event({"syms": syms})                     # seans kapısı → toplu yazım
    satirlar = _defter()
    assert len(satirlar) == 1 and satirlar[0]["n"] == 40
    i_x = satirlar[0]["alanlar"].index("x_s")
    defter_kova = [0] * (len(ic.DONGU_SURESI.kovalar) + 1)
    for olay in satirlar[0]["olaylar"]:
        assert olay[0] == "processed"
        defter_kova[bisect.bisect_left(ic.DONGU_SURESI.kovalar, olay[i_x])] += 1
    assert defter_kova == [b - a for a, b in zip(once, sonra)], "tanık eşi tutmadı: defter ≠ histogram"


# =================================================================================================================
# B — (2) Z = planli dal gövdesi, semboller üzerinden toplam, AYNI saat
# =================================================================================================================

def _z_sahnesi(monkeypatch, saat: _Saat, *, planli_gecikme: float, silahli_gecikme: float = 0.5,
               planli_satir_dondur: bool = True) -> str:
    """Silahlı dalın (`intraday_shadow.record`) ve planli dalın (`planli_satir`) süresini sahte saatle ENJEKTE eder."""
    syms = _pk_kur(monkeypatch, planli_n=2)
    monkeypatch.setattr(gecikme, "_saat", saat)

    def silahli(plan, bar, as_of):
        saat.ilerle(silahli_gecikme)
        return None

    def planli(plan, bar, as_of):
        saat.ilerle(planli_gecikme)
        if not planli_satir_dondur:
            return None                                    # tekilleştirme dönüşü: dala girildi, yazım yok
        return {"plan_id": plan["id"], "ticker": plan["ticker"], "date": SEANS, "kol": ish.KOL_PLANLI,
                "status": "would_submit", "qty": 1, "sim_price": 100.0}

    monkeypatch.setattr(ish, "record", silahli)
    monkeypatch.setattr(ish, "planli_satir", planli)
    return syms


def test_B1_Z_YALNIZ_planli_dal_semboller_uzerinden_TOPLANIR_silahli_dal_GIRMEZ(sandbox_state, monkeypatch):
    saat = _Saat()
    syms = _z_sahnesi(monkeypatch, saat, planli_gecikme=0.25)
    casus = _gozlem_casusu(monkeypatch)
    t = ic.consumer()
    t.on_barfeed_event({"syms": syms})
    (x_hist, etiket), = casus
    assert etiket == "processed" and x_hist == 1.0, f"kurgu: X = 0,5 silahlı + 2×0,25 planli beklenirdi, {x_hist}"
    (sonuc, x, z, _ofset, giris, yazim), = t._atif_olaylar
    assert z == 0.5, f"Z yalnız iki planli dal gövdesi olmalı (2×0,25), ölçülen {z} — silahlı dal ya da dal dışı süre sızdı"
    assert (sonuc, x, giris, yazim) == ("processed", 1.0, 2, 2)
    assert ic.health()["shadow_planli_written"] == 2, "sıcak yolun planli sayacı değişti"
    assert len(store.read_jsonl(ish.PLANLI_ORDERS_FILE)) == 2


def test_B2_Z_olaylar_arasi_SIFIRLANIR_tekillestirme_donusu_giris_sayar_yazim_saymaz(sandbox_state, monkeypatch):
    saat = _Saat()
    syms = _z_sahnesi(monkeypatch, saat, planli_gecikme=0.25)
    t = ic.consumer()
    t.on_barfeed_event({"syms": syms})
    monkeypatch.setattr(ish, "planli_satir", lambda plan, bar, as_of: (saat.ilerle(0.125), None)[1])
    t.on_barfeed_event({"syms": syms})
    ilk, ikinci = t._atif_olaylar
    assert ilk[2:] == (0.5, ilk[3], 2, 2)
    assert ikinci[2] == 0.25, f"ikinci olayın Z'si birinciyi taşıyor ya da yanlış: {ikinci[2]}"
    assert (ikinci[4], ikinci[5]) == (2, 0), "tekilleştirme dönüşü: dala girildi (2), satır yazılmadı (0)"


def test_B3_planli_dal_HATASI_gövdeye_dahil_tur_DUSMEZ(sandbox_state, monkeypatch):
    saat = _Saat()
    syms = _z_sahnesi(monkeypatch, saat, planli_gecikme=0.25)
    uyarilar = []
    monkeypatch.setattr(ic.obs, "warn", lambda olay, **kw: (saat.ilerle(0.0625), uyarilar.append(olay)))

    def patlayan(plan, bar, as_of):
        saat.ilerle(0.25)
        raise RuntimeError("v606 bilerek")

    monkeypatch.setattr(ish, "planli_satir", patlayan)
    t = ic.consumer()
    t.on_barfeed_event({"syms": syms})
    (sonuc, _x, z, _o, giris, yazim), = t._atif_olaylar
    assert uyarilar == ["intraday_shadow_planli_failed"] * 2, "planli dal hata sözleşmesi değişti"
    assert sonuc == "processed" and (giris, yazim) == (2, 0)
    assert z == 2 * (0.25 + 0.0625), f"Z dal gövdesini (hata dalı dahil) kapsamalı: {z}"


def test_B4_NK_sekli_planli_kol_KAPALI_giris_var_Z_sifir(sandbox_state, monkeypatch):
    """Kart NK: `PLANLI_ENABLED=False` → dal erken döner; Z yalnız kronometre (sahte saatte TAM sıfır)."""
    syms = _pk_kur(monkeypatch, planli_n=2)
    saat = _Saat()
    monkeypatch.setattr(gecikme, "_saat", saat)
    monkeypatch.setattr(ish, "record", lambda plan, bar, as_of: None)
    monkeypatch.setattr(ish, "PLANLI_ENABLED", False)
    t = ic.consumer()
    t.on_barfeed_event({"syms": syms})
    (sonuc, _x, z, _o, giris, yazim), = t._atif_olaylar
    assert (sonuc, z, giris, yazim) == ("processed", 0.0, 2, 0)
    assert store.read_jsonl(ish.PLANLI_ORDERS_FILE) == []


# =================================================================================================================
# C — (3) evren, alanlar, kayıt X'e GİRMEZ
# =================================================================================================================

def test_C1_skipped_KAYDEDILMEZ_seans_pencere_halt(sandbox_state, monkeypatch):
    store.write_json("portfolio.json", {"positions": {}, "armed": []})
    t = ic.consumer()
    for an in (GECE, PENCERE_ONCESI):
        bc.set_clock(lambda an=an: an)
        t.on_barfeed_event({"syms": "AAPL"})
    bc.set_clock(lambda: RTH)
    monkeypatch.setattr(ic._health, "halted", lambda: True)
    t.on_barfeed_event({"syms": "AAPL"})
    assert (t.skipped["session"], t.skipped["pencere"], t.skipped["halt"]) == (1, 1, 1), "kurgu geçersiz"
    assert t._atif_olaylar == [], f"skipped olay kaydedildi: {t._atif_olaylar}"
    monkeypatch.setattr(ic._health, "halted", lambda: False)
    t.on_barfeed_event({"syms": ""})
    assert [k[0] for k in t._atif_olaylar] == ["processed"]


def test_C2_hata_olayi_KAYDEDILIR_outcome_error(sandbox_state, monkeypatch):
    saat = _Saat()
    monkeypatch.setattr(gecikme, "_saat", saat)
    monkeypatch.setattr(ic.obs, "warn", lambda olay, **kw: None)

    def patla(self, fields):
        saat.ilerle(0.375)
        raise RuntimeError("v606")

    monkeypatch.setattr(ic.IntradayConsumer, "_handle", patla)
    t = ic.consumer()
    assert t.on_barfeed_event({"syms": "AAPL"}) is None
    (sonuc, x, z, _o, giris, yazim), = t._atif_olaylar
    assert (sonuc, x, z, giris, yazim) == ("error", 0.375, 0.0, 0, 0)


def test_C3_istisna_yolunda_da_KAYIT_ve_ozgun_istisna_AYNEN(sandbox_state, monkeypatch):
    """v585 B6 sözleşmesi korunur: `except` dalının kendisi yükseltirse istisna AYNEN geçer; kayıt yine düşer."""
    ozgun = OSError("kanal düştü")

    def kanal(olay, **kw):
        raise ozgun

    def patla(self, fields):
        raise RuntimeError("v606")

    monkeypatch.setattr(ic.obs, "warn", kanal)
    monkeypatch.setattr(ic.IntradayConsumer, "_handle", patla)
    t = ic.consumer()
    with pytest.raises(OSError) as yakalanan:
        t.on_barfeed_event({"syms": "AAPL"})
    assert yakalanan.value is ozgun
    assert [k[0] for k in t._atif_olaylar] == ["error"]


def test_C4_kayit_X_ölcumune_GIRMEZ(sandbox_state, monkeypatch):
    """Kart (3) + beyanli_sinirlar (4): kayıt X ölçüldükten SONRA eklenir. Kaydın kendisine 1 s enjekte edilir; ne
    histograma işlenen X ne defterdeki X onu taşımaz."""
    store.write_json("portfolio.json", {"positions": {}, "armed": []})
    bc.set_clock(lambda: RTH)
    saat = _Saat()
    monkeypatch.setattr(gecikme, "_saat", saat)
    ozgun = ic.IntradayConsumer._atif_kaydet

    def pahali_kayit(self, *a, **kw):
        saat.ilerle(1.0)
        return ozgun(self, *a, **kw)

    monkeypatch.setattr(ic.IntradayConsumer, "_atif_kaydet", pahali_kayit)
    monkeypatch.setattr(ic.IntradayConsumer, "_pencere_gonderim",
                        lambda self, pf: saat.ilerle(0.25))          # işlenen turun içindeki bilinen süre
    casus = _gozlem_casusu(monkeypatch)
    t = ic.consumer()
    t.on_barfeed_event({"syms": ""})
    t.on_barfeed_event({"syms": ""})
    assert [x for x, _ in casus] == [0.25, 0.25], f"kayıt maliyeti X'e sızdı: {casus}"
    assert [k[1] for k in t._atif_olaylar] == [0.25, 0.25]


def test_C5_alanlar_SIRALI_ofset_AYNI_saatten(sandbox_state, monkeypatch):
    """Ofset = olayın X ölçümünün başladığı an − süreç saat tabanı (`_SUREC_SAAT0`), AYNI saatle (`gecikme._saat`):
    olaylar arası süre ofsete girer, X'e girmez. (Yuvarlamasızlık: A1 bellek↔histogram, D1 defter↔bellek.)"""
    assert ic.ATIF_ALANLARI == ("outcome", "x_s", "z_s", "ofset_s", "planli_giris", "planli_yazim")
    store.write_json("portfolio.json", {"positions": {}, "armed": []})
    bc.set_clock(lambda: RTH)
    saat = _Saat(t=1000.0)
    monkeypatch.setattr(gecikme, "_saat", saat)
    monkeypatch.setattr(ic, "_SUREC_SAAT0", 900.0)
    monkeypatch.setattr(ic.IntradayConsumer, "_pencere_gonderim", lambda self, pf: saat.ilerle(0.25))
    t = ic.consumer()
    t.on_barfeed_event({"syms": ""})
    saat.ilerle(59.5)
    t.on_barfeed_event({"syms": ""})
    ilk, ikinci = t._atif_olaylar
    assert ilk[3] == 100.0, f"ofset = olay başlangıcı − süreç saat tabanı olmalı: {ilk[3]}"
    assert ikinci[3] == 159.75 and (ilk[1], ikinci[1]) == (0.25, 0.25)


def test_C6_alan_sirasi_TEK_KAYNAK_ATIF_ALANLARI(sandbox_state, monkeypatch):
    """İnceleme M-4 (tek-kaynak yasası): kaydın alan sırası `ATIF_ALANLARI`dan TÜRER — kayıt kurucusu yalnız ADLA
    doldurulur, satırdaki `alanlar` başlığı ile değerler ada göre eşleşir; konumsal bir demet ikinci kaynak olamaz."""
    saat = _Saat()
    syms = _z_sahnesi(monkeypatch, saat, planli_gecikme=0.25)
    casus = _gozlem_casusu(monkeypatch)
    t = ic.consumer()
    t.on_barfeed_event({"syms": syms})
    k = t._atif_olaylar[0]
    assert k._fields == ic.ATIF_ALANLARI
    assert (k.outcome, k.x_s, k.z_s, k.planli_giris, k.planli_yazim) == ("processed", casus[0][0], 0.5, 2, 2)
    bc.set_clock(lambda: KAPANIS_SONRASI)
    t.on_barfeed_event({"syms": syms})
    satir = _defter()[0]
    olay = dict(zip(satir["alanlar"], satir["olaylar"][0]))
    assert (olay["outcome"], olay["x_s"], olay["z_s"], olay["planli_giris"], olay["planli_yazim"]) == \
        ("processed", casus[0][0], 0.5, 2, 2), f"satır başlığı ile değer konumu ayrıştı: {olay}"
    agac = ast.parse((KOK / "meridian" / "intraday_cycle.py").read_text(encoding="utf-8"))
    fn = next(d for d in ast.walk(agac) if isinstance(d, ast.FunctionDef) and d.name == "_atif_kaydet")
    kurucular = [d for d in ast.walk(fn) if isinstance(d, ast.Call) and ast.unparse(d.func) == "AtifOlay"]
    assert len(kurucular) == 1 and not kurucular[0].args, "kayıt kurucusu konumsal argüman almamalı (yalnız ad)"
    assert {kw.arg for kw in kurucular[0].keywords} == set(ic.ATIF_ALANLARI)
    eklemeler = [d for d in ast.walk(fn) if isinstance(d, ast.Call) and ast.unparse(d.func).endswith(".append")]
    assert all(not isinstance(a, ast.Tuple) for d in eklemeler for a in d.args), "tampona konumsal demet ekleniyor"


# =================================================================================================================
# D — (4) seans başına TOPLU yazım, X ölçümünün DIŞINDA; süreç damgası
# =================================================================================================================

def test_D1_seans_kapisinda_TEK_satir_alanlar_ve_surec_damgasi(sandbox_state, monkeypatch):
    syms = _pk_kur(monkeypatch)
    monkeypatch.setattr(ic, "_SUREC_BASLANGIC", "2026-07-23T12:00:00.123456+00:00")
    t = ic.consumer()
    for _ in range(3):
        t.on_barfeed_event({"syms": syms})
    bellek = [list(k) for k in t._atif_olaylar]
    assert _defter() == [], "seans bitmeden yazım olmamalı (toplu yazım)"
    bc.set_clock(lambda: KAPANIS_SONRASI)
    t.on_barfeed_event({"syms": syms})
    t.on_barfeed_event({"syms": syms})                     # ikinci kapı-önü olay: tampon boş → ikinci satır YOK
    satirlar = _defter()
    assert len(satirlar) == 1, f"seans başına TEK satır olmalı: {len(satirlar)}"
    s = satirlar[0]
    assert s["kart"] == "EXE-2026-012" and s["seans"] == SEANS and s["bosaltma"] == "seans_kapandi"
    assert ic.ATIF_BOSALTMA == ("seans_kapandi", "seans_degisti", "kapanis"), "bosaltma değer sözlüğü (B okuyucusu)"
    assert s["surec_baslangic"] == "2026-07-23T12:00:00.123456+00:00" and s["pid"] == os.getpid()
    assert s["alanlar"] == list(ic.ATIF_ALANLARI) and s["n"] == 3
    assert s["olaylar"] == bellek, "defter bellekten farklı — yuvarlama/dönüşüm var"
    assert t._atif_olaylar == []
    assert (sandbox_state / ic.ATIF_DEFTERI).exists(), "defter state/ altında değil"


def test_D2_toplu_yazim_X_olcumunun_DISINDA_seans_kapisinda(sandbox_state, monkeypatch):
    store.write_json("portfolio.json", {"positions": {}, "armed": []})
    bc.set_clock(lambda: RTH)
    saat = _Saat()
    monkeypatch.setattr(gecikme, "_saat", saat)
    ozgun = store.append_jsonl

    def yavas_defter(ad, satir):
        if ad == ic.ATIF_DEFTERI:
            saat.ilerle(2.0)
        return ozgun(ad, satir)

    monkeypatch.setattr(ic.store, "append_jsonl", yavas_defter)
    casus = _gozlem_casusu(monkeypatch)
    t = ic.consumer()
    t.on_barfeed_event({"syms": ""})
    bc.set_clock(lambda: KAPANIS_SONRASI)
    t.on_barfeed_event({"syms": ""})
    assert casus == [(0.0, "processed"), (0.0, "skipped")], f"toplu yazım bir turun ölçümüne girdi: {casus}"
    assert len(_defter()) == 1


def test_D3_seans_DEGISINCE_eski_seans_yazilir_X_disinda(sandbox_state, monkeypatch):
    store.write_json("portfolio.json", {"positions": {}, "armed": []})
    bc.set_clock(lambda: RTH)
    saat = _Saat()
    monkeypatch.setattr(gecikme, "_saat", saat)
    ozgun = store.append_jsonl

    def yavas_defter(ad, satir):
        if ad == ic.ATIF_DEFTERI:
            saat.ilerle(2.0)
        return ozgun(ad, satir)

    monkeypatch.setattr(ic.store, "append_jsonl", yavas_defter)
    casus = _gozlem_casusu(monkeypatch)
    t = ic.consumer()
    t.on_barfeed_event({"syms": ""})
    t.on_barfeed_event({"syms": ""})
    bc.set_clock(lambda: ERTESI_RTH)                       # kapanış sonrası olay GELMEDİ; ertesi seansın ilk olayı
    t.on_barfeed_event({"syms": ""})
    satirlar = _defter()
    assert [(s["seans"], s["n"], s["bosaltma"]) for s in satirlar] == [(SEANS, 2, "seans_degisti")]
    assert [x for x, _ in casus] == [0.0, 0.0, 0.0], f"seans değişimi yazımı ölçülen tura girdi: {casus}"
    assert t._atif_seans == "2026-07-24" and len(t._atif_olaylar) == 1


def test_D4_yazim_DUSERSE_kayip_ADIYLA_uyari_tampon_BOSALIR_tur_DUSMEZ(sandbox_state, monkeypatch):
    store.write_json("portfolio.json", {"positions": {}, "armed": []})
    bc.set_clock(lambda: RTH)
    ozgun = store.append_jsonl

    def bozuk_defter(ad, satir):
        if ad == ic.ATIF_DEFTERI:
            raise OSError("v606 disk")
        return ozgun(ad, satir)

    monkeypatch.setattr(ic.store, "append_jsonl", bozuk_defter)
    uyarilar = []
    monkeypatch.setattr(ic.obs, "warn", lambda olay, **kw: uyarilar.append((olay, kw)))
    t = ic.consumer()
    t.on_barfeed_event({"syms": ""})
    t.on_barfeed_event({"syms": ""})
    bc.set_clock(lambda: KAPANIS_SONRASI)
    assert t.on_barfeed_event({"syms": ""}) is None
    t.on_barfeed_event({"syms": ""})                       # tampon boş → ikinci deneme/uyarı YOK (sel yok)
    assert [o for o, _ in uyarilar] == ["exe012_defter_yazim_dustu"]
    kw = uyarilar[0][1]
    assert kw["seans"] == SEANS and kw["n"] == 2 and "v606 disk" in kw["error"]
    assert t._atif_olaylar == [] and t.last_error == "", "alet arızası sıcak yolun hata alanına sızdı"


def test_D5_surec_baslangic_damgasi_UTC_ISO_ve_ice_aktarimdan_once():
    damga = dt.datetime.fromisoformat(ic._SUREC_BASLANGIC)
    assert damga.tzinfo is not None and damga.utcoffset() == dt.timedelta(0)
    assert damga <= dt.datetime.now(UTC)
    assert isinstance(ic._SUREC_SAAT0, float)


# =================================================================================================================
# E — (5) kapatma bayrağı
# =================================================================================================================

def _senaryo(sandbox_state, monkeypatch, *, acik: bool) -> dict:
    """Aynı olay dizisi (PK bileşimi, tekilleştirme dönüşleri, kapanış sonrası olay) — sıcak yolun bütün çıktıları."""
    for ad in (ic.DECISIONS_FILE, ish.ORDERS_FILE, ish.PLANLI_ORDERS_FILE, "trade_plans.jsonl", ic.ATIF_DEFTERI):
        (sandbox_state / ad).unlink(missing_ok=True)
    ic._CONSUMER = None
    ic.reset_plans_cache()
    ish.reset_dedup()
    monkeypatch.setattr(ic, "ATIF_ENABLED", acik)
    syms = _pk_kur(monkeypatch)
    okuma = [0]
    gercek = time.perf_counter

    def sayan_saat():
        okuma[0] += 1
        return gercek()

    monkeypatch.setattr(gecikme, "_saat", sayan_saat)
    once = {e: s["sayi"] for e, s in ic.DONGU_SURESI.anlik().items()}
    t = ic.consumer()
    donusler = [t.on_barfeed_event({"syms": syms}) for _ in range(3)]
    bc.set_clock(lambda: KAPANIS_SONRASI)
    donusler.append(t.on_barfeed_event({"syms": syms}))
    sonra = {e: s["sayi"] for e, s in ic.DONGU_SURESI.anlik().items()}
    oku = lambda ad: (sandbox_state / ad).read_bytes() if (sandbox_state / ad).exists() else None  # noqa: E731
    return {"donusler": donusler, "health": ic.health(),
            "sayim": {e: sonra[e] - once.get(e, 0) for e in sonra},
            "defterler": {ad: oku(ad) for ad in (ic.DECISIONS_FILE, ish.ORDERS_FILE, ish.PLANLI_ORDERS_FILE)},
            "atif_defteri": oku(ic.ATIF_DEFTERI), "tampon": list(t._atif_olaylar),
            "birikim": (t._atif_z, t._atif_giris, t._atif_yazim), "saat_okuma": okuma[0]}


def test_E1_bayrak_KAPALIYKEN_kayit_ve_defter_YOK_sicak_yol_BAYT_ESIT(sandbox_state, monkeypatch):
    kapali = _senaryo(sandbox_state, monkeypatch, acik=False)
    acik = _senaryo(sandbox_state, monkeypatch, acik=True)
    assert kapali["atif_defteri"] is None and kapali["tampon"] == [], "bayrak kapalıyken alet kaydetti/yazdı"
    assert acik["atif_defteri"] is not None, "kurgu geçersiz: açık hâlde de defter yok"
    assert all(v is not None for v in acik["defterler"].values()), "kurgu: üç sıcak yol defteri de yazılmalı"
    assert kapali["defterler"] == acik["defterler"], "alet sıcak yolun defterlerini değiştirdi"
    assert kapali["health"] == acik["health"], "alet sıcak yolun sayaçlarını değiştirdi"
    assert kapali["donusler"] == acik["donusler"] == [None] * 4
    assert kapali["sayim"] == acik["sayim"] and acik["sayim"]["processed"] == 3
    # M-3 (inceleme): kapalıyken `_handle_symbol`un planli dalında da saat OKUNMAZ, sayaç DEĞİŞMEZ — yalnız olay
    # turunun kendi iki okuması (giriş/çıkış) × 4 olay kalır. Açıkta planli girişler ek okuma yapar (kurgu kanıtı).
    assert kapali["birikim"] == (0.0, 0, 0), f"bayrak kapalıyken planli dal birikimi değişti: {kapali['birikim']}"
    assert kapali["saat_okuma"] == 2 * 4, f"bayrak kapalıyken fazladan saat okuması: {kapali['saat_okuma']}"
    # (açıkta birikimler her olayın başında sıfırlanır — son olay kapanış-sonrası skipped olduğu için (0.0, 0, 0)
    # görünür; kurgu kanıtı fazladan saat okumasıdır: 3 olay × 3 planli giriş × 2 okuma)
    assert acik["saat_okuma"] == 2 * 4 + 3 * 3 * 2, f"kurgu geçersiz: açıkta planli dal okuması {acik['saat_okuma']}"


def test_E2_bayrak_ORTAMDAN_okunur_varsayilan_ACIK_intraday_shadow_deseni():
    kaynak = (KOK / "meridian" / "intraday_cycle.py").read_text(encoding="utf-8")
    atamalar = [d for d in ast.parse(kaynak).body
                if isinstance(d, ast.Assign) and any(getattr(h, "id", "") == "ATIF_ENABLED" for h in d.targets)]
    assert len(atamalar) == 1, "ATIF_ENABLED modül düzeyinde TEK kez atanmalı"
    assert ast.unparse(atamalar[0].value) == "os.environ.get('MERIDIAN_TUR_ATIF', '1') != '0'"
    assert ic.ATIF_ENABLED is (os.environ.get("MERIDIAN_TUR_ATIF", "1") != "0")


# =================================================================================================================
# F — Yasa 6 + OTOMATİK KAPI YASAĞI
# =================================================================================================================

def test_F1_motor_defteri_OKUMAZ_yalniz_yazar_OTOMATIK_KAPI_YOK():
    """Kart kill_list: 'hiçbir motor kodu R'yi, bu kartın defterini ya da Prometheus'u okuyup kolu kapatamaz/açamaz;
    kodda böyle bir mandal bulunursa ölçüm GEÇERSİZ'. Graf defterin TEK yazarını gösterir, okuyucusunu göstermez."""
    g = codelaw.artifact_graph()
    bilgi = g["artifacts"].get(ic.ATIF_DEFTERI)
    assert bilgi is not None, "defter grafta çözülmüyor — yazım biçimi değişmiş olabilir"
    assert bilgi["writers"] == ["intraday_cycle.py"] and bilgi["unread"] is True, bilgi
    assert ic.ATIF_DEFTERI in g["declared_sinks"] and ic.ATIF_DEFTERI not in g["violations"]
    iddia = next(c for c in codelaw.declared_claims() if c["artifact"] == ic.ATIF_DEFTERI)
    assert iddia["stale_claim"] is False and iddia["external_accessors"] == {}, iddia
    # Ad ve sabit, yazar ile beyan dışında hiçbir üretim kaynağında GEÇMEZ (okuma yolu kurulamaz). Sabit adı SÖZCÜK
    # sınırıyla aranır: `hermes.PLAN_ATIF_DEFTERI` başka bir defterdir (ölçüldü 2026-09-30, ilk koşum).
    sabit = re.compile(r"\bATIF_DEFTERI\b")
    for yol in sorted((KOK / "meridian").rglob("*.py")) + sorted((KOK / "ops").rglob("*.py")):
        if yol.name in ("intraday_cycle.py", "codelaw.py"):
            continue
        metin = yol.read_text(encoding="utf-8")
        assert ic.ATIF_DEFTERI not in metin and not sabit.search(metin), f"{yol} defteri anıyor"
    # Yazarın kendisi de defteri yalnız YAZAR (AST — şerh/docstring anmaları sayılmaz): sabit tanımı + TEK
    # `store.append_jsonl(ATIF_DEFTERI, …)` çağrısı; başka hiçbir kod kullanımı (okuma, ad türetme) yok.
    agac = ast.parse((KOK / "meridian" / "intraday_cycle.py").read_text(encoding="utf-8"))
    adlar = [d for d in ast.walk(agac) if isinstance(d, ast.Name) and d.id == "ATIF_DEFTERI"]
    yazimlar = [d for d in ast.walk(agac) if isinstance(d, ast.Call) and ast.unparse(d.func) == "store.append_jsonl"
                and d.args and isinstance(d.args[0], ast.Name) and d.args[0].id == "ATIF_DEFTERI"]
    assert len(yazimlar) == 1 and len(adlar) == 2, (
        f"intraday_cycle defteri yazım dışında kullanıyor: {len(adlar)} ad, {len(yazimlar)} yazım (2/1 beklenir)")


def test_F2_beyan_OKUYUCUYU_ve_DEVIR_SARTINI_adlandirir():
    gerekce = codelaw.DECLARED_SINKS[ic.ATIF_DEFTERI]
    for parca in ("EXE-2026-012", "research/olcumler/exe012_kill1_canli", "OTOMATİK KAPI", "DEVİR ŞARTI",
                  "kapanis", "27 MB", "yarım satır"):
        assert parca in gerekce, f"beyan '{parca}' parçasını taşımıyor"


def test_F3_kod_KARTA_bagli_kart_ALET_maddesini_tasiyor():
    kart = KART.read_text(encoding="utf-8")
    assert "card_id: EXE-2026-012" in kart and ic.ATIF_KART == "EXE-2026-012"
    for parca in ("ikinci kronometre YASAK", "gecikme._saat", "skipped kaydedilmez", "süreç başlangıç damgasını"):
        assert parca in kart, f"kartın ALET metni '{parca}' içermiyor — kod neye bağlı?"


# =================================================================================================================
# H — (Tur 2, I-1) kayıt yolunun arızası turu DÜŞÜREMEZ
# =================================================================================================================

def test_H1_kayit_ARIZASI_temiz_turu_temiz_dondurur_adiyla_uyari(sandbox_state, monkeypatch):
    store.write_json("portfolio.json", {"positions": {}, "armed": []})
    bc.set_clock(lambda: RTH)
    uyarilar = []
    monkeypatch.setattr(ic.obs, "warn", lambda olay, **kw: uyarilar.append((olay, kw)))

    def patlayan_kayit(self, *a, **kw):
        raise RuntimeError("v606 kayıt gizli-değer-xyz")

    monkeypatch.setattr(ic.IntradayConsumer, "_atif_kaydet", patlayan_kayit)
    t = ic.consumer()
    assert t.on_barfeed_event({"syms": ""}) is None, "kayıt arızası temiz turu istisnaya çevirdi"
    assert t.events_handled == 1 and t.last_error == "", "alet arızası sıcak yolun sayaç/hata alanına sızdı"
    assert [o for o, _ in uyarilar] == ["exe012_atif_kayit_dustu"]
    kw = uyarilar[0][1]
    assert kw["tur"] == "RuntimeError", kw
    assert "gizli-değer-xyz" not in json.dumps(kw, ensure_ascii=False), "uyarı istisnanın DEĞERİNİ taşıyor (yalnız tür)"


def test_H2_except_kolunun_ISTISNASI_kayit_arizasiyla_MASKELENMEZ(sandbox_state, monkeypatch):
    """v585 B6 / C3 sözleşmesinin üstüne: `except` kolu yükseltir + kayıt da patlar + kayıp uyarısı da patlar →
    yine ÖZGÜN istisna (aynı nesne) yükselir."""
    ozgun = OSError("kanal düştü")

    def kanal(olay, **kw):
        if olay == "intraday_event_failed":
            raise ozgun
        raise OSError("ikinci kanal arızası — özgünün yerine geçmemeli")

    def patla(self, fields):
        raise RuntimeError("v606")

    def patlayan_kayit(self, *a, **kw):
        raise RuntimeError("v606 kayıt")

    monkeypatch.setattr(ic.obs, "warn", kanal)
    monkeypatch.setattr(ic.IntradayConsumer, "_handle", patla)
    monkeypatch.setattr(ic.IntradayConsumer, "_atif_kaydet", patlayan_kayit)
    with pytest.raises(OSError) as yakalanan:
        ic.consumer().on_barfeed_event({"syms": "AAPL"})
    assert yakalanan.value is ozgun, f"turun kendi istisnası maskelendi: {yakalanan.value!r}"


# =================================================================================================================
# K — (Tur 2, Rol-1 kararı) işçinin düzgün kapanışında seans tamponu deftere iner
# =================================================================================================================

def _yasam_dongusu(monkeypatch, *, kaydeder: bool) -> None:
    """`TestClient(api.app)` yaşam döngüsünün `_autostart` kolları: `kaydeder` = intraday tüketicisi barfeed'e
    KAYDEDİLİR mi (canlı işçinin koşulu: piyasa akışı açık + Alpaca kâğıt anahtarı). Akış/barfeed/ayna başlatılmaz."""
    monkeypatch.setattr(alpaca, "paper_available", lambda: kaydeder)
    monkeypatch.setattr(api.secrets_mod, "present", lambda n: True)
    monkeypatch.setenv("MERIDIAN_MARKET_STREAM", "1")
    monkeypatch.setenv("MERIDIAN_MIRROR_STREAM", "0")
    monkeypatch.setenv("MERIDIAN_INTRADAY", "1")
    monkeypatch.setattr(mk, "start", lambda *a, **k: None)
    monkeypatch.setattr(bf, "start", lambda *a, **k: None)
    monkeypatch.setattr(bf, "_CONSUMER", None)


def _olaylar(t, n: int) -> None:
    bc.set_clock(lambda: RTH)
    store.write_json("portfolio.json", {"positions": {}, "armed": []})
    for _ in range(n):
        t.on_barfeed_event({"syms": ""})


def test_K1_kayitli_yasam_dongusu_KAPANISTA_tamponu_yazar(sandbox_state, monkeypatch):
    _yasam_dongusu(monkeypatch, kaydeder=True)
    with TestClient(api.app):
        t = ic.consumer()
        assert bf.consumer().callback == t.on_barfeed_event, "kurgu: tüketici bu yaşam döngüsünde kaydedilmedi"
        _olaylar(t, 3)
        assert _defter() == []
    satirlar = _defter()
    assert [(s["seans"], s["n"], s["bosaltma"]) for s in satirlar] == [(SEANS, 3, "kapanis")]
    assert t._atif_olaylar == []


def test_K2_kaydetmeyen_yasam_dongusu_KAPANISTA_hicbir_sey_yazmaz(sandbox_state, monkeypatch):
    """Sandbox'sız bir TestClient kapanışının sınıfı: yaşam döngüsü tüketici KAYDETMEDİ (anahtar yok) ama süreçteki
    tekil tüketicinin tamponu DOLU (önceki bir testten). Kapanış yolu onu yazsaydı, sandbox'sız bir koşumda gerçek yerel
    `state/`e düşerdi. İkinci kurgu: doğrudan `api._autostart()` çağıran bir testin bıraktığı kayıt referansı sonraki
    yaşam döngüsünün kapanışına TAŞINMAZ."""
    t = ic.consumer()
    _olaylar(t, 2)
    _yasam_dongusu(monkeypatch, kaydeder=False)
    with TestClient(api.app):
        pass
    assert _defter() == [] and not (sandbox_state / ic.ATIF_DEFTERI).exists(), "kaydetmeyen kapanış defter yazdı"
    assert len(t._atif_olaylar) == 2
    _yasam_dongusu(monkeypatch, kaydeder=True)
    api._autostart()                                       # yaşam döngüsü DIŞI kayıt (bayat referans adayı)
    _yasam_dongusu(monkeypatch, kaydeder=False)
    with TestClient(api.app):
        pass
    assert not (sandbox_state / ic.ATIF_DEFTERI).exists(), "önceki kaydın referansı sonraki kapanışa taşındı"


def test_K3_bos_tampon_SATIR_YAZMAZ(sandbox_state, monkeypatch):
    t = ic.consumer()
    t._atif_bosalt("kapanis")
    t._atif_bosalt("seans_kapandi")
    assert not (sandbox_state / ic.ATIF_DEFTERI).exists(), "boş tampon n:0 satırı yazdı"
    _yasam_dongusu(monkeypatch, kaydeder=True)
    with TestClient(api.app):
        pass
    assert not (sandbox_state / ic.ATIF_DEFTERI).exists(), "olaysız yaşam döngüsünün kapanışı satır yazdı"
    _olaylar(t, 2)
    t._atif_bosalt("kapanis")
    t._atif_bosalt("kapanis")
    assert [s["n"] for s in _defter()] == [2], "ikinci boşaltma boş satır üretti"


def test_K4_kapanis_ARIZASI_kapanisi_BOZMAZ(sandbox_state, monkeypatch):
    uyarilar = []

    def kanal(olay, **kw):
        uyarilar.append((olay, kw))
        if olay == "exe012_kapanis_bosaltma_dustu":
            raise OSError("uyarı kanalı da düştü")

    def patlayan(self):
        raise RuntimeError("v606 kapanış gizli-değer-xyz")

    _yasam_dongusu(monkeypatch, kaydeder=True)
    monkeypatch.setattr(api.obs, "warn", kanal)
    monkeypatch.setattr(ic.IntradayConsumer, "kapanista_bosalt", patlayan)
    with TestClient(api.app):
        _olaylar(ic.consumer(), 1)
    ad = [(o, kw) for o, kw in uyarilar if o == "exe012_kapanis_bosaltma_dustu"]
    assert len(ad) == 1 and ad[0][1]["tur"] == "RuntimeError"
    assert "gizli-değer-xyz" not in json.dumps(ad[0][1], ensure_ascii=False)


def _baska_is_parcacigi_alabilir(kilit) -> bool:
    """Kilit şu an TUTULUYOR mu? — başka bir iş parçacığından bloklamadan almayı dener (RLock sahipliği yeniden
    girişe izin verdiği için aynı iş parçacığından sınanamaz)."""
    sonuc = []

    def dene():
        ok = kilit.acquire(blocking=False)
        if ok:
            kilit.release()
        sonuc.append(ok)

    th = threading.Thread(target=dene)
    th.start()
    th.join()
    return sonuc[0]


def test_K5_tampon_takasi_ve_yazim_KILIT_ALTINDA(sandbox_state, monkeypatch):
    """İnceleme koşulu (a): kapanış boşaltması lifespan iş parçacığından gelir, barfeed daemon iş parçacığı DURMAZ.
    Tampona ekleme, seans değişimi/kapısı boşaltması ve kapanış boşaltması AYNI kilidi TUTARAK koşar."""
    store.write_json("portfolio.json", {"positions": {}, "armed": []})
    bc.set_clock(lambda: RTH)
    t = ic.consumer()
    ihlal = []

    class KontrolluListe(list):
        def append(self, x):
            if _baska_is_parcacigi_alabilir(t._atif_kilit):
                ihlal.append("tampona ekleme kilitsiz")
            super().append(x)

    ozgun = store.append_jsonl

    def kontrollu_defter(ad, satir):
        if ad == ic.ATIF_DEFTERI and _baska_is_parcacigi_alabilir(t._atif_kilit):
            ihlal.append("defter yazımı kilitsiz")
        return ozgun(ad, satir)

    monkeypatch.setattr(ic.store, "append_jsonl", kontrollu_defter)
    t._atif_olaylar = KontrolluListe()
    t.on_barfeed_event({"syms": ""})
    t._atif_bosalt("kapanis")                              # kapanış yolu
    t._atif_olaylar = KontrolluListe()
    t.on_barfeed_event({"syms": ""})
    bc.set_clock(lambda: ERTESI_RTH)
    t._atif_olaylar = KontrolluListe(t._atif_olaylar)
    t.on_barfeed_event({"syms": ""})                       # seans değişimi yolu
    assert ihlal == [], ihlal
    assert [s["bosaltma"] for s in _defter()] == ["kapanis", "seans_degisti"]


def test_K6_eszamanli_kapanis_bosaltmasi_OLAY_KAYBETMEZ_CIFT_YAZMAZ(sandbox_state, monkeypatch):
    """Davranış kanıtı (GIL altında yarış penceresi dar — ısırma K5'tedir): barfeed benzeri iş parçacığı olay işlerken
    ana iş parçacığı tekrar tekrar kapanış boşaltması yapar; her olay TAM BİR KEZ deftere ya da tampona düşer."""
    store.write_json("portfolio.json", {"positions": {}, "armed": []})
    bc.set_clock(lambda: RTH)
    t = ic.consumer()
    n = 400

    def akis():
        for _ in range(n):
            t.on_barfeed_event({"syms": ""})

    th = threading.Thread(target=akis)
    th.start()
    for _ in range(3000):                                  # sabit sayıda eşzamanlı boşaltma denemesi (iş yükü)
        t._atif_bosalt("kapanis")
    th.join()
    t._atif_bosalt("kapanis")
    satirlar = _defter()
    assert all(s["n"] == len(s["olaylar"]) and s["n"] > 0 for s in satirlar)
    ofsetler = [o[satirlar[0]["alanlar"].index("ofset_s")] for s in satirlar for o in s["olaylar"]]
    assert len(ofsetler) == n and len(set(ofsetler)) == n, "olay kayboldu ya da çift yazıldı"


# =================================================================================================================
# G — bedel (kart beyanli_sinirlar (4); ADIM-0c alet_olay_basi_maliyeti_us, defter_satir_boyutu_kb)
# =================================================================================================================

def test_G1_alet_OLAY_BASI_maliyeti_ve_satir_boyutu_OLCULUR(sandbox_state, monkeypatch):
    syms = _pk_kur(monkeypatch, planli_n=3)
    t = ic.consumer()
    t.on_barfeed_event({"syms": syms})                     # ısınma (import, önbellek, ilk yazımlar)
    n = 300

    # (1) X DIŞI EK — `_atif_kaydet` doğrudan (sarmalayıcı tabanı çıkarılır)
    ozgun = ic.IntradayConsumer._atif_kaydet
    ham: list[int] = []

    def olcen(self, *a, **kw):
        t0 = time.perf_counter_ns()
        ozgun(self, *a, **kw)
        ham.append(time.perf_counter_ns() - t0)

    monkeypatch.setattr(ic.IntradayConsumer, "_atif_kaydet", olcen)
    for _ in range(n):
        t.on_barfeed_event({"syms": syms})
    bos = []
    for _ in range(n):
        t0 = time.perf_counter_ns()
        (lambda: None)()
        bos.append(time.perf_counter_ns() - t0)
    monkeypatch.setattr(ic.IntradayConsumer, "_atif_kaydet", ozgun)
    kayit_ns = statistics.median(ham) - statistics.median(bos)
    kayit_p95 = sorted(ham)[int(round(0.95 * (len(ham) - 1)))]

    # (2) TOPLAM EK — alet açık/kapalı serpiştirilmiş turlar, olay başına dış süre (gürültülü; bilgi amaçlı)
    farklar = []
    for tur in range(8):
        sure = {}
        for acik in ((False, True) if tur % 2 == 0 else (True, False)):
            monkeypatch.setattr(ic, "ATIF_ENABLED", acik)
            t0 = time.perf_counter_ns()
            for _ in range(100):
                t.on_barfeed_event({"syms": syms})
            sure[acik] = (time.perf_counter_ns() - t0) / 100
        farklar.append(sure[True] - sure[False])
    monkeypatch.setattr(ic, "ATIF_ENABLED", True)
    toplam_ns = statistics.median(farklar)

    # (3) TOPLU YAZIM — seans büyüklüğünde tampon (kart: ≈ 1.650 processed olay/seans KABA TÜRETME)
    rnd = random.Random(606)
    t._atif_olaylar = [("processed", rnd.uniform(0.0008, 0.02), 0.0, rnd.uniform(0.0, 30000.0), 0, 0)
                       for _ in range(1650)]
    t._atif_seans = SEANS
    (sandbox_state / ic.ATIF_DEFTERI).unlink(missing_ok=True)
    t0 = time.perf_counter_ns()
    t._atif_bosalt("seans_kapandi")
    yazim_ms = (time.perf_counter_ns() - t0) / 1e6
    satir_kb = (sandbox_state / ic.ATIF_DEFTERI).stat().st_size / 1024
    json.loads((sandbox_state / ic.ATIF_DEFTERI).read_text())

    # (4) X İÇİ EK — planli dal kronometresinin kalıbı (giriş başına iki saat okuması + iki toplama), yalıtık; boş
    # döngü tabanı çıkarılır. Kart (2) bu eki gerektirir: Z, dalın AYNI saatle ölçülen gövdesidir.
    kalip_n = 100_000
    z, g = 0.0, 0
    t0 = time.perf_counter_ns()
    for _ in range(kalip_n):
        ta = gecikme._saat()
        g += 1
        z += gecikme._saat() - ta
    kalip = time.perf_counter_ns() - t0
    t0 = time.perf_counter_ns()
    for _ in range(kalip_n):
        g += 1
    icerde_ns = (kalip - (time.perf_counter_ns() - t0)) / kalip_n
    # X dışı ekin payı: seans tarihi (ET dilim dönüşümü) olay başına bir kez hesaplanır
    t0 = time.perf_counter_ns()
    for _ in range(n):
        bc.session_date()
    seans_ns = (time.perf_counter_ns() - t0) / n

    print(f"\nBEDEL v606 G1 (PK bileşimi: {syms}; {n} olay):"
          f"\n  X DIŞI kayıt eki (`_atif_kaydet`): medyan {kayit_ns:.0f} ns/olay (ham p95 {kayit_p95} ns, "
          f"sarmalayıcı tabanı {statistics.median(bos):.0f} ns çıkarıldı; bunun ~{seans_ns:.0f} ns'si seans tarihi)"
          f"\n  X İÇİ planli dal kronometresi: ~{icerde_ns:.0f} ns / planli giriş (yalıtık kalıp, {kalip_n} tekrar)"
          f"\n  toplam alet eki (açık−kapalı, 8 serpiştirilmiş tur × 100 olay): medyan {toplam_ns:.0f} ns/olay "
          f"(turlar: {', '.join(f'{f:.0f}' for f in farklar)})"
          f"\n  seans toplu yazımı (1650 olay): {yazim_ms:.2f} ms, satır {satir_kb:.1f} KB")
    assert kayit_ns < 20_000, f"X dışı kayıt eki {kayit_ns:.0f} ns — beklenen µs altı/mertebesi (şişme bekçisi)"
    assert satir_kb < 1024, f"seans satırı {satir_kb:.0f} KB — şişme"
    assert yazim_ms < 1000
