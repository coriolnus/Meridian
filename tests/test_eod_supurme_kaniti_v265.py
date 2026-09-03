"""v265 — DAVRANIŞSAL EOD SÜPÜRME KANITI BEKÇİSİ (WP2 · denetim A4 kapanış çivisi).

ÖLÇÜLEN BOŞLUK ("DAVRANIŞSAL EOD KANITI HÂLÂ KAYITSIZ" — ROADMAP.md §8 ARŞİV → "SB-2
drift_sinifi · davranışsal EOD süpürme kanıtı" satırı, H6 ✅ KAPANDI 2026-08-22 v265; TSK-083,
2026-09-03: satır çapası ROADMAP :503 çürümüştü, sembole çevrildi): v220+v221 fixli süpürücü
GERÇEK EOD süpürmelerinde koşuyor — canlı ölçüm (research/olcumler/wp2_eod_supurme_2026-08-22):
son 10 işlenen seansın 10'unda `mirror_stale_entries_cancelled` olayı var (20:31-20:50 UTC),
10'unda da cancelled=0 / kept=3-4 (koruma sınıfı DOKUNULMADI; `mirror_cancel_sinif_dokumu`
10/10). Yani DAVRANIŞ var, KAYIT/HÜKÜM yüzeyi yoktu: hiçbir bekçi "bu seansın süpürme kanıtı
defterde mi" sorusunu sormuyordu — kanıt bir gün kaybolsa (süpürme sessizce koşmasa) kimse
duymayacaktı. A4'ün istediği kayıt: "süpürme koştu ve N emri süpürdü" hükmünün OKUNAN bir
yüzeyde durması.

SÖZLEŞME (bu dosya çiviler):
  * `watchdog.eod_supurme_report()` → {kosdu, n, son_tarih, olculemedi_neden, ...}:
    - kosdu=True  ⟺ kitabın işlediği SON seansın günlük-kadans süpürme olayı defterde;
    - kosdu=False ⟺ kitap seansı işledi ama o seansın süpürme kanıtı YOK (İHLAL);
    - kosdu=None  ⟺ ölçülemedi (defter okunamadı) YA DA hüküm referanssız (kitap hiç
      seans işlememiş / kapsam dışı) — ikisi AYRI: ilki `olculemedi_neden` taşır ve ALARMDIR,
      ikincisi taşımaz ve bilgidir.
    - n = son süpürme seansında iptal edilen emir sayısı; ölçülemeyen/olmayan n=None ≠ 0 (v196).
  * Olay adları motorun/adaptörün KENDİ sabitlerinden okunur; watchdog'daki yedekler
    (`EOD_SUPURME_OLAY_YEDEK`/`EOD_SUPURME_DOKUM_YEDEK`) kaynakla AYNI kalmak zorundadır
    (drift çivisi burada — `_kapsama_penceresi` deseninin ikizi).
  * `check_eod_supurme_and_alarm()` — İHLAL/ÖLÇÜLEMEDİ başına BİR alarm (mandal,
    `MECHANISM_STALE`); toparlanınca mandal düşer; kapsam-dışı/bilgi hâlleri alarm ÜRETMEZ.
  * YASA 6 okuyucu: `check_and_alarm` zinciri bu bekçiyi KENDİ try'ında çağırır (AST çivisi —
    metin değil; api/pano bağlama işi BAŞKA ajanda, okuyucu bu zincirdir).
"""
from __future__ import annotations

import ast
import json
import pathlib

import pytest

from meridian import config, store, watchdog

SRC = pathlib.Path(__file__).resolve().parents[1]

KADANS_OLAY = "mirror_stale_entries_cancelled"
DOKUM_OLAY = "mirror_cancel_sinif_dokumu"


# ---- yardımcılar ---------------------------------------------------------------------------

def _defter_yaz(state, ad: str, satirlar: list[dict]) -> None:
    """Sandbox state'e ham jsonl yaz — store yazıcılarını değil dosyayı kullanır ki test,
    okunan biçimi (obs._emit'in diske koyduğu satır) birebir taklit etsin."""
    (state / ad).write_text("".join(json.dumps(r) + "\n" for r in satirlar))


def _kadans(date: str, ts: str, cancelled: int = 0, kept: int = 3, foreign: int = 0) -> dict:
    return {"ts": ts, "level": "info", "event": KADANS_OLAY, "gate": "gunluk_kadans",
            "date": date, "cancelled": cancelled, "kept": kept, "foreign": foreign}


@pytest.fixture
def ayna(sandbox_state, monkeypatch):
    """BROKER=alpaca_paper + temiz mandal. Mandal süreç-içi küme: testler arası sızmasın."""
    monkeypatch.setattr(config, "BROKER", "alpaca_paper", raising=False)
    monkeypatch.setattr(watchdog, "_EOD_SUPURME_ALARMED", set())
    return sandbox_state


@pytest.fixture
def alarmlar(monkeypatch):
    """obs.alarm çağrılarını yakala — bekçi felsefesi gereği tek gözlenebilir çıktı budur."""
    from meridian import obs
    kayit: list[dict] = []
    def _yakala(token, message, **fields):
        kayit.append({"token": token, "message": message, **fields})
        return {"token": token}
    monkeypatch.setattr(obs, "alarm", _yakala)
    return kayit


# ---- drift çivileri: olay adları motor/adaptör sabitleriyle AYNI ----------------------------

def test_yedek_olay_adi_motor_sabitiyle_ayni():
    from meridian import loop
    assert watchdog.EOD_SUPURME_OLAY_YEDEK == loop.EV_STALE_ENTRIES_CANCELLED
    assert watchdog.EOD_SUPURME_OLAY_YEDEK == KADANS_OLAY


def test_yedek_dokum_adi_adaptor_sabitiyle_ayni():
    from meridian.adapters import alpaca
    assert watchdog.EOD_SUPURME_DOKUM_YEDEK == alpaca.EV_SUPURME_SINIFLARI
    assert watchdog.EOD_SUPURME_DOKUM_YEDEK == DOKUM_OLAY


# ---- rapor: dört hâl -----------------------------------------------------------------------

def test_kapsam_disi_baska_broker(sandbox_state, monkeypatch):
    monkeypatch.setattr(config, "BROKER", "internal", raising=False)
    rep = watchdog.eod_supurme_report()
    assert rep["kapsam_disi"] is True
    assert rep["kosdu"] is None
    assert rep["olculemedi_neden"] is None          # kapsam dışı ≠ ölçülemedi


def test_kanit_var_kosdu(ayna):
    _defter_yaz(ayna, "events.jsonl", [
        _kadans("2026-08-20", "2026-08-20T20:34:06+00:00", cancelled=0, kept=3, foreign=6),
        _kadans("2026-08-21", "2026-08-21T20:31:58+00:00", cancelled=2, kept=3, foreign=4),
    ])
    store.write_json("portfolio.json", {"last_date": "2026-08-21"})
    rep = watchdog.eod_supurme_report()
    assert rep["kosdu"] is True
    assert rep["n"] == 2                            # "süpürme koştu ve N emri süpürdü" — N burada
    assert rep["son_tarih"] == "2026-08-21"
    assert rep["kept"] == 3 and rep["foreign"] == 4
    assert rep["kitap_seansi"] == "2026-08-21"
    assert rep["seans_gerisinde"] is False
    assert rep["olculemedi_neden"] is None


def test_koruma_dokumu_tasinir(ayna):
    """A4'ün kalbi: süpürücü koruma sınıfıyla karşılaştı ve DOKUNMADI — döküm olayı rapora düşer."""
    _defter_yaz(ayna, "events.jsonl", [
        _kadans("2026-08-21", "2026-08-21T20:31:58+00:00"),
        {"ts": "2026-08-21T20:31:58+00:00", "level": "info", "event": DOKUM_OLAY,
         "giris": 0, "koruma": 3, "yabanci": 4, "cancelled": 0},
    ])
    store.write_json("portfolio.json", {"last_date": "2026-08-21"})
    rep = watchdog.eod_supurme_report()
    assert rep["koruma_dokumu"] is not None
    assert rep["koruma_dokumu"]["koruma"] == 3
    assert rep["koruma_dokumu"]["cancelled"] == 0


def test_kanit_bayat_ihlal(ayna):
    """Kitap yeni seansı işledi, son süpürme kanıtı ESKİ seanstan → İHLAL."""
    _defter_yaz(ayna, "events.jsonl",
                [_kadans("2026-08-19", "2026-08-19T20:32:56+00:00")])
    store.write_json("portfolio.json", {"last_date": "2026-08-21"})
    rep = watchdog.eod_supurme_report()
    assert rep["kosdu"] is False
    assert rep["seans_gerisinde"] is True
    assert rep["son_tarih"] == "2026-08-19"
    assert rep["kitap_seansi"] == "2026-08-21"


def test_hic_kanit_yok_ihlal_ve_n_None(ayna):
    """Defter okunuyor ama tek süpürme olayı yok; kitap seans işlemiş → İHLAL. v196: n=None ≠ 0."""
    _defter_yaz(ayna, "events.jsonl", [])
    store.write_json("portfolio.json", {"last_date": "2026-08-21"})
    rep = watchdog.eod_supurme_report()
    assert rep["kosdu"] is False
    assert rep["n"] is None                          # 0 DEĞİL: süpürülen sayı ölçülmedi
    assert rep["son_tarih"] is None


def test_kitap_hic_seans_islememis_bilgi(ayna):
    """Hüküm referanssız (kitap boş): alarm değil bilgi — kosdu=None, olculemedi_neden YOK."""
    _defter_yaz(ayna, "events.jsonl", [])
    rep = watchdog.eod_supurme_report()
    assert rep["kosdu"] is None
    assert rep["olculemedi_neden"] is None
    assert rep["beklenir"] is False


def test_defter_okunamadi_olculemedi(ayna, monkeypatch):
    def _patla(name, limit=None):
        raise OSError("disk okunamadı")
    monkeypatch.setattr(watchdog.store, "read_jsonl", _patla)
    rep = watchdog.eod_supurme_report()
    assert rep["kosdu"] is None
    assert rep["olculemedi_neden"]                   # ölçülemedi BEYANLI
    assert rep["n"] is None


# ---- alarm geçişi: mandal + üç hâlin ayrımı -------------------------------------------------

def test_ihlal_tek_alarm_mandal(ayna, alarmlar):
    _defter_yaz(ayna, "events.jsonl",
                [_kadans("2026-08-19", "2026-08-19T20:32:56+00:00")])
    store.write_json("portfolio.json", {"last_date": "2026-08-21"})
    watchdog.check_eod_supurme_and_alarm()
    watchdog.check_eod_supurme_and_alarm()           # aynı ihlal İKİNCİ kez anlatılmaz
    assert len(alarmlar) == 1
    assert alarmlar[0]["token"] == "MECHANISM_STALE"
    assert alarmlar[0]["kind"] == "eod_supurme_kaniti"


def test_toparlaninca_mandal_duser(ayna, alarmlar):
    _defter_yaz(ayna, "events.jsonl",
                [_kadans("2026-08-19", "2026-08-19T20:32:56+00:00")])
    store.write_json("portfolio.json", {"last_date": "2026-08-21"})
    watchdog.check_eod_supurme_and_alarm()
    assert len(alarmlar) == 1
    # süpürme kanıtı geldi → temiz; sonra YENİ seansta yine kayıp → YENİ alarm
    _defter_yaz(ayna, "events.jsonl",
                [_kadans("2026-08-21", "2026-08-21T20:31:58+00:00")])
    watchdog.check_eod_supurme_and_alarm()
    assert len(alarmlar) == 1                        # temiz hâl alarm üretmez, mandalı düşürür
    store.write_json("portfolio.json", {"last_date": "2026-08-24"})
    watchdog.check_eod_supurme_and_alarm()
    assert len(alarmlar) == 2                        # yeni seansın kaybı yeni olgudur


def test_olculemedi_alarmi_beyanli(ayna, alarmlar, monkeypatch):
    def _patla(name, limit=None):
        raise OSError("disk okunamadı")
    monkeypatch.setattr(watchdog.store, "read_jsonl", _patla)
    watchdog.check_eod_supurme_and_alarm()
    assert len(alarmlar) == 1
    assert alarmlar[0].get("olculemedi") is True


def test_kapsam_disi_ve_bilgi_alarm_uretmez(ayna, alarmlar, monkeypatch):
    _defter_yaz(ayna, "events.jsonl", [])            # kitap yok → bilgi hâli
    watchdog.check_eod_supurme_and_alarm()
    monkeypatch.setattr(config, "BROKER", "internal", raising=False)
    watchdog.check_eod_supurme_and_alarm()           # kapsam dışı hâli
    assert alarmlar == []


# ---- YASA 6: okuyucu zinciri (AST çivisi — metin çivisi değil) ------------------------------

def test_zincir_check_and_alarm_kendi_tryinda_cagirir():
    agac = ast.parse((SRC / "meridian" / "watchdog.py").read_text(encoding="utf-8"))
    fn = next(n for n in agac.body
              if isinstance(n, ast.FunctionDef) and n.name == "check_and_alarm")
    hedefli_try = None
    for tr in (n for n in ast.walk(fn) if isinstance(n, ast.Try)):
        adlar = {c.func.id if isinstance(c.func, ast.Name) else getattr(c.func, "attr", None)
                 for c in ast.walk(tr) if isinstance(c, ast.Call)
                 if isinstance(c.func, (ast.Name, ast.Attribute))}
        if "check_eod_supurme_and_alarm" in adlar:
            hedefli_try = tr
            break
    assert hedefli_try is not None, (
        "check_and_alarm zinciri check_eod_supurme_and_alarm'ı çağırmıyor — rapor OKUYUCUSUZ "
        "(YASA 6): bekçi yazılmış ama zincire bağlanmamış")
    # yalıtım: kendi try'ı Exception yakalar (akranlarının deseni — biri düşünce zincir düşmez)
    assert any(isinstance(h.type, ast.Name) and h.type.id == "Exception"
               for h in hedefli_try.handlers)
