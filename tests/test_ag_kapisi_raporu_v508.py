"""test_ag_kapisi_raporu_v508.py — TSK-193: dış-ağ kapısının oturum-sonu RAPORU + kapıya takılıp
geri çekilme uykusunda süre yakan dört testin yamasının çivileri.

vNNN KİMLİK KAYDI: v507 → v508 taşındı 2026-09-16, çakışma: TSK-192 ondalıklı hacim çivisi
(tests/test_bar_ondalikli_hacim_v507.py). İlk seçim v507'ydi (bu worktree'de o an geçmiyordu);
çakışan dilim başka dalda commit'li ve incelemedeydi, az-çapalı taraf olarak bu dosya taşındı.

VAKA (Rol-1 cProfile, 2026-09-16). `tests/conftest.py` "DIŞ AĞ TESTLERE KAPALI" kapısı dış
bağlantıyı DENEMEDEN `DisAgErisimiKapali` ile düşürüyor (doğru). Ama
`scheduler.advance_once → earnings.refresh → data.nasdaq_earnings_window → data._get_json` yolu
her düşen bağlantıyı `except Exception` ile yakalayıp 3 deneme × üstel geri çekilme uykusu yapıyor
ve bunu GÜN BAŞINA tekrarlıyor. Test YEŞİL geçtiği için kapının "yamalanmamış yol gürültülü
görünsün" hedefi o yolda tutmuyordu. Dört test, tek başına seri koşumda (bu worktree, ÖNCE):
audit_fixes 267 s · v136 seans-başına 198 s · regime_patch 134 s · v136 bar-gelmese 67 s.

ÇİVİLER
  (a) dış adrese bağlanma denemesi süreç-içi sayacı artırır ve rapor metni tetikleyen testin
      KİMLİĞİNİ taşır;
  (b) loopback / AF_UNIX sayacı ARTIRMAZ (kapının konusu makine DIŞI trafik);
  (c) xdist kolu: işçinin `workeroutput`u kontrolcüde birleşir ve terminal özetine basılır;
  (d) dört test artık earnings adaptörüne girmez — SÜRE DEĞİL ÇAĞRI SAYISI ölçülür
      (`data._get_json`u sayan, anında düşen saplama). Süreye bağlı çivi bilerek yok: yük altında
      flake üretir.

MUTASYON KANITI bu dosyada KOŞMAZ; teslim raporunda durur (CLAUDE.md §6).
"""
from __future__ import annotations

import importlib
import socket
import tempfile
import os

import pytest

from tests import conftest as _kapi
from tests.conftest import DisAgErisimiKapali
# (d) regime_patch testinin fikstürü; modül özniteliği olarak içeri alınınca bu dosyada da görünür.
from tests.test_regime_patch import seeded_sandbox  # noqa: F401


# ---- (a) DIŞ ADRES: SAYAÇ ARTAR, RAPOR KİMLİĞİ TAŞIR -----------------------------------------------
# Hedef RFC 5737 TEST-NET-3: kapı bozuk olsa bile yönlendirilmez, paket gerçek bir makineye gitmez.
@pytest.mark.parametrize("yontem", ["connect", "connect_ex"])
def test_dis_adres_sayaci_artirir_ve_rapor_test_kimligini_tasir(request, yontem):
    kimlik = request.node.nodeid
    onceki = _kapi._AG_KAPISI_TETIK.get(kimlik, 0)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        with pytest.raises(DisAgErisimiKapali):
            getattr(s, yontem)(("203.0.113.7", 80))
        assert _kapi._AG_KAPISI_TETIK.get(kimlik, 0) == onceki + 1
        metin = "\n".join(_kapi.ag_kapisi_rapor_satirlari(dict(_kapi._AG_KAPISI_TETIK)))
        assert "DIŞ AĞ KAPISI" in metin and "yamalanmamış yol" in metin
        assert kimlik in metin
    finally:
        s.close()
        # Bu çivi kapıyı BİLEREK tetikler; kendi girdisini silmezse oturum raporunda sahte bir
        # "yamalanmamış yol" bulgusu olarak görünürdü.
        _kapi._AG_KAPISI_TETIK.pop(kimlik, None)


def test_bos_sayac_rapor_uretmez():
    assert _kapi.ag_kapisi_rapor_satirlari({}) == []


# ---- (b) MAKİNE İÇİ TRAFİK SAYILMAZ --------------------------------------------------------------
def test_loopback_ve_af_unix_sayaci_artirmaz(request):
    kimlik = request.node.nodeid
    dinleyici = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    istemci = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        dinleyici.bind(("127.0.0.1", 0))
        dinleyici.listen(1)
        istemci.connect(dinleyici.getsockname())
        assert istemci.connect_ex(dinleyici.getsockname()) != -1   # errno döner, ATMAZ
    finally:
        istemci.close()
        dinleyici.close()
    # AF_UNIX: var olmayan kısa bir yol — gerçek connect'e ulaştığını çekirdeğin OSError'ı kanıtlar
    # (kapı atsaydı DisAgErisimiKapali olurdu, OSError DEĞİL).
    yol = os.path.join(tempfile.gettempdir(), f"v508-yok-{os.getpid()}.sock")
    u = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        with pytest.raises(OSError):
            u.connect(yol)
    finally:
        u.close()
    assert kimlik not in _kapi._AG_KAPISI_TETIK


# ---- (c) XDIST KOLU: İŞÇİ ÇIKTISI KONTROLCÜDE BİRLEŞİR VE BASILIR -----------------------------------
def test_xdist_isci_ciktisi_birlesir_ve_terminal_ozetine_basilir(monkeypatch):
    monkeypatch.setattr(_kapi, "_AG_KAPISI_ISCILERDEN", {})
    monkeypatch.setattr(_kapi, "_AG_KAPISI_TETIK", {})

    class _Dugum:
        workeroutput = {"ag_kapisi_tetik": {"tests/test_x.py::test_y": 6}}

    _kapi.pytest_testnodedown(_Dugum(), None)
    _kapi.pytest_testnodedown(_Dugum(), None)      # iki işçi aynı kimliği raporlarsa TOPLANIR

    class _Terminal:
        def __init__(self):
            self.satirlar = []

        def write_sep(self, sep, baslik):
            self.satirlar.append(baslik)

        def write_line(self, satir):
            self.satirlar.append(satir)

    class _Yapilandirma:
        pass

    t = _Terminal()
    _kapi.pytest_terminal_summary(t, 0, _Yapilandirma())
    metin = "\n".join(t.satirlar)
    assert "DIŞ AĞ KAPISI 1 test tarafından tetiklendi" in metin
    assert "12" in metin and "tests/test_x.py::test_y" in metin


# ---- (d) DÖRT TEST EARNINGS ADAPTÖRÜNE GİRMEZ (çağrı sayısı, süre değil) ----------------------------
_DORT_TEST = [
    ("test_audit_fixes", "test_scheduler_refetches_once_per_session_not_per_poll", ("sandbox_state",)),
    ("test_regime_patch", "test_scheduler_flag_survives_publish_lag", ("seeded_sandbox", "monkeypatch")),
    ("test_ogrenme_otomasyonu_v136", "test_kadans_seans_basina_BIR_kez_kosar", ("sandbox_state", "monkeypatch")),
    ("test_ogrenme_otomasyonu_v136", "test_kadans_bar_GELMESE_DE_kosar", ("sandbox_state", "monkeypatch")),
]


@pytest.mark.parametrize("modul,ad,fiksturler", _DORT_TEST, ids=[a for _, a, _ in _DORT_TEST])
def test_dort_test_earnings_adaptorune_girmez(request, monkeypatch, modul, ad, fiksturler):
    from meridian import scheduler
    from meridian.adapters import data
    cagrilar = []

    def _sayan_get_json(url, timeout, attempts=3):
        cagrilar.append(url)
        # ANINDA düşer: yama geri alınırsa (mutasyon) çivi uyku merdivenine girmeden kırmızı olur.
        raise data.FetchError("v508-sayac", 0)

    monkeypatch.setattr(data, "_get_json", _sayan_get_json)
    # Kazanç bloğunun kapısı hafta/gün damgasıdır; önceki bir testten kalmış damga bloğu atlatıp
    # çiviyi YANLIŞ SEBEPLE yeşil yapardı — deterministik olsun diye damgalar kaldırılır.
    for anahtar in ("earnings_week", "earnings_gaveup_day", "earnings_attempts"):
        monkeypatch.delitem(scheduler._state, anahtar, raising=False)
    fn = getattr(importlib.import_module(f"tests.{modul}"), ad)
    fn(*[request.getfixturevalue(f) for f in fiksturler])
    assert cagrilar == [], f"{ad} earnings ağ yoluna girdi: {len(cagrilar)} _get_json çağrısı"
    # KAPSAMIN DÜRÜST SINIRI: "kapı bu testte HİÇ tetiklenmez" iddia EDİLMEZ. Yeni rapor aynı dört
    # testte İKİNCİ bir yamasız yol buldu (2026-09-16): `scheduler._y4_collect → shortinterest.fetch`
    # test başına 1 deneme, geri çekilme uykusu YOK (yamalı dört test bu dosyada 0,06-0,85 s). Bu dilimin
    # kapsamı earnings yoludur; o yol teslim raporunda açık kalem olarak durur.
