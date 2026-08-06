"""test_nous_boru_v192.py — NOUS ÖNERİ BORUSU: ÜÇ ŞEKİL, ÜÇ YOL (2026-08-06).

OPERATÖR ŞİKÂYETİ: "nous her hafta öneri üretiyor, sonra hiçbir şey olmuyor."

ÖLÇÜM (canlı defter, 2026-W32 — `improvement_proposals.jsonl`): üç öneri kabul edildi, ÜÇÜ DE
`sekil="tasarim"`, ÜÇÜNÜN DE `kuyruk="yol_yok"`. Kalite kapısı çalıştı, defter yazıldı, pano
gösterdi — ve sonra HİÇBİR ŞEY olmadı. Katman C yalnız `parametre` şeklini taşıyordu; kalan iki
şekilde "yol yok" bir DURUM etiketi değil bir ÇIKMAZ SOKAKTI: öneri hiçbir kuyruğa girmiyor,
hiçbir olay üretmiyor, operatörün önüne bir iş kalemi olarak ÇIKMIYORdu (`skill_revisions.json`
dersi: sessiz bir kuyruk, kuyruk değil çöplüktür).

BORU ÜÇ SINIFI DA BİR YOLA BAĞLAR — ve üçü AYRI kalır:
  (a) parametre         → hermes composite kuyruğu (YENİ YOL AÇILMADI: mevcut `koprule`/
                          `_kuyruga_yaz` köprüsü; kapı hakem, H4 bütçesi içinde, elle ağırlık YOK).
                          Boru burada YALNIZ sonucu okur — ikinci bir enqueue aynı öneriyi iki
                          ölçüm sırasına sokar ve bütçeyi iki kez harcardı.
  (b) tasarim           → FİŞ: `nous_fisler.json` + `nous_oneri_fisi` olayı + pano rozeti.
                          Otomatik UYGULAMA yolu YOK (ve olmamalı) — görünür operatör kalemi VAR.
  (c) cekirdek_hakkinda → sade `nous_oneri_red_anayasal` olayı. `CekirdekIhlali` FIRLATILMAZ ve
                          ALARM BASILMAZ: o istisna köprünün YANLIŞ YÖNLENDİRMESİNİN (bir kod
                          hatasının) işaretidir; burada sistem DOĞRU çalışıyor, sınıf kapalı.
                          Anayasanın normal işleyişini alarm diye raporlamak, aynı turda kapatılan
                          alarm-yorgunluğu kusurunun ta kendisi olurdu.

HİÇBİR TEST LLM ÇAĞIRMAZ (`text=` enjekte edilir) ve HİÇBİR TEST CANLI STATE'E YAZMAZ.
"""
from __future__ import annotations

import ast
import json
import pathlib

import pytest

from meridian import nous_eval, obs, store

SRC = pathlib.Path("meridian")

_KNOB_A = "stop_loss_atr_mult"      # GERÇEK bounds düğmesi (min 0.8 · max 4.0 · step 0.1)
_KNOB_B = "exit.time_stop_days"     # min 3 · max 40 · step 1
# BİLEŞİK EN AZ İKİ DÜĞME TAŞIR (guard.composite_shape_reasons): tek düğme "bileşik değil, normal
# hipotez yolu" reddine düşer. Fikstür o yasaya UYAR — gevşetmez.


def _tohumla(st):
    for f in ("bounds.yaml", "goal.yaml"):
        p = st / f
        if not p.exists():
            p.write_text(pathlib.Path("state").joinpath(f).read_text())
    return st


def _oneri(**ek) -> dict:
    o = {"alan": "kar_selalesi",
         "gozlem": "kar_selalesi bölümünde net_r -0.0421 iken sinyal_mfe_r 0.9648",
         "oneri": "çıkış eşiğini sıkılaştır",
         "beklenen_etki": "net_r +0.10 yönünde",
         "onerilen_olcum": "profit_waterfall geri_verilen_r yeniden ölçülür",
         "oncelik": "yuksek", "sekil": "tasarim",
         "kanit_atifi": ["net_r", "sinyal_mfe_r"]}
    o.update(ek)
    return o


@pytest.fixture
def olaylar(monkeypatch):
    kayit: list[dict] = []
    monkeypatch.setattr(obs, "log", lambda ev, **kw: kayit.append({"ev": ev, **kw}) or {})
    return kayit


@pytest.fixture
def alarmlar(monkeypatch):
    kayit: list[tuple] = []
    monkeypatch.setattr(obs, "alarm", lambda tok, msg, **kw: kayit.append((tok, msg)) or {})
    return kayit


# =================================================================================================
# ÜÇ SINIFIN YÖNLENDİRMESİ
# =================================================================================================
def test_uc_sinif_UC_AYRI_yola_gider(sandbox_state, olaylar, alarmlar):
    _tohumla(sandbox_state)
    kabul = [
        _oneri(alan="a", sekil="parametre", parametreler={_KNOB_A: 2.0, _KNOB_B: 10},
               kuyruk="evet", kuyruk_id="C00001"),
        _oneri(alan="b", sekil="tasarim", oneri="karne üreticisine avg_r alanını bas"),
        _oneri(alan="c", sekil="cekirdek_hakkinda",
               oneri="guard'daki dsr_hard eşiğini gevşet"),
    ]
    out = nous_eval.boru(kabul, hafta="2026-W32")
    ozet = out["ozet"]
    assert ozet["n"] == 3
    assert ozet[nous_eval.YOL_KUYRUK] == 1
    assert ozet[nous_eval.YOL_FIS] == 1
    assert ozet[nous_eval.YOL_RED] == 1
    yollar = {k["alan"]: k["yol"] for k in out["kalemler"]}
    assert yollar == {"a": nous_eval.YOL_KUYRUK, "b": nous_eval.YOL_FIS, "c": nous_eval.YOL_RED}


def test_tasarim_FISLENIR_defter_ve_olay(sandbox_state, olaylar):
    _tohumla(sandbox_state)
    kabul = [_oneri(id="N00007", alan="sonuc_hukmu.tavan_durumu.durum",
                    oneri="v3 karne satırına backtest_full.avg_r alanını bas")]
    nous_eval.boru(kabul, hafta="2026-W32")
    doc = store.read_json(nous_eval.FISLER_FILE, {})
    assert doc["n"] == 1
    f = doc["fisler"][0]
    assert f["anahtar"] == "N00007" and f["durum"] == "fislendi"
    assert f["hafta"] == "2026-W32" and f["oncelik"] == "yuksek"
    assert "avg_r" in f["oneri"]
    ev = [e for e in olaylar if e["ev"] == nous_eval.OLAY_FIS]
    assert len(ev) == 1 and ev[0]["anahtar"] == "N00007"
    assert "otomatik uygulama yolu YOK" in ev[0]["detail"]


def test_fis_TEKILDIR_ikinci_kosum_ikinci_fis_uretmez(sandbox_state, olaylar):
    _tohumla(sandbox_state)
    for _ in range(3):
        nous_eval.boru([_oneri(id="N00007")], hafta="2026-W32")
    doc = store.read_json(nous_eval.FISLER_FILE, {})
    assert doc["n"] == 1, "aynı öneri her koşuda yeni fiş üretiyor — kuyruk çöplüğe dönerdi"


def test_id_yokken_fis_anahtari_HAFTA_ALAN_olur(sandbox_state):
    """`yaz=False` kuru koşumda öneri kimliği henüz doğmamıştır; anahtarsız fiş her koşuda yeniden
    doğardı (tekilleştirme anahtar üzerinden çalışır)."""
    _tohumla(sandbox_state)
    out = nous_eval.boru([_oneri(alan="hotstate")], hafta="2026-W32")
    assert out["kalemler"][0]["anahtar"] == "2026-W32:hotstate"


# =================================================================================================
# KATMAN D — RED, İSTİSNASIZ VE ALARMSIZ
# =================================================================================================
def test_cekirdek_onerisi_SADE_olayla_reddedilir(sandbox_state, olaylar, alarmlar):
    """Katman D'nin sözü korunur (kuyruk yolu yapısal kapalı) AMA normal işleyişi alarm üretmez."""
    _tohumla(sandbox_state)
    out = nous_eval.boru([_oneri(alan="guard", sekil="cekirdek_hakkinda",
                                 oneri="min_sample eşiğini düşür")], hafta="2026-W32")
    assert out["ozet"][nous_eval.YOL_RED] == 1
    ev = [e for e in olaylar if e["ev"] == nous_eval.OLAY_RED_ANAYASAL]
    assert len(ev) == 1
    assert "ASLA" in ev[0]["detail"] and "Katman D" in ev[0]["detail"]
    assert ev[0]["cekirdek_isaretleri"], "hangi çekirdek imzasının yakaladığı yazılmamış"
    assert alarmlar == [], "anayasanın NORMAL işleyişi alarm üretti — alarm yorgunluğu"


def test_cekirdek_onerisi_FIS_defterine_GIRMEZ(sandbox_state, olaylar):
    """Otomatik-uygulama borusu bu sınıfa ASLA dokunmaz — fiş kuyruğu bir iş kalemidir."""
    _tohumla(sandbox_state)
    nous_eval.boru([_oneri(alan="guard", sekil="cekirdek_hakkinda",
                           oneri="risk zarfı vetosunu kaldır")], hafta="2026-W32")
    assert store.read_json(nous_eval.FISLER_FILE, None) is None


def test_beynin_PARAMETRE_etiketi_cekirdegi_ORTEMEZ(sandbox_state, olaylar, alarmlar):
    """Şekil BORUDA DA yeniden türetilir: model çekirdek önerisini "parametre" diye etiketlerse
    boru onu kuyruk sayacına yazar ve sayaç YALAN söylerdi (koprule'ün aynı dersi)."""
    _tohumla(sandbox_state)
    o = _oneri(alan="probgate", sekil="parametre", parametreler={_KNOB_A: 2.0, _KNOB_B: 10},
               oneri="dsr_hard eşiğini 0.1'e çek")
    out = nous_eval.boru([o], hafta="2026-W32")
    assert out["ozet"][nous_eval.YOL_RED] == 1 and out["ozet"][nous_eval.YOL_KUYRUK] == 0
    assert o["sekil"] == "cekirdek_hakkinda"                # etiket EZİLDİ
    assert [e for e in olaylar if e["ev"] == nous_eval.OLAY_RED_ANAYASAL]


def test_boru_KUYRUGA_YAZMAZ_yapisal(sandbox_state):
    """`hermes_composite.enqueue` bu modülde HÂLÂ yalnız `_kuyruga_yaz` içinde çağrılır. Boru,
    kuyruk yoluna ikinci bir kapı AÇMAZ — Katman D'nin yapısal çivisi bu tekliğe dayanıyor."""
    tree = ast.parse((SRC / "nous_eval.py").read_text())
    sahipler = []
    for fn in [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]:
        for n in ast.walk(fn):
            if (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                    and n.func.attr == "enqueue"):
                sahipler.append(fn.name)
    assert sahipler == ["_kuyruga_yaz"], f"enqueue çağrısı yayıldı: {sahipler}"


# =================================================================================================
# (a) BOUNDS-İÇİ DÜĞME GERÇEKTEN HERMES KUYRUĞUNA DÜŞER (uçtan uca, LLM'siz)
# =================================================================================================
def test_bounds_ici_dugme_HERMES_KUYRUGUNA_duser(sandbox_state, olaylar):
    """Uçtan uca: haftalık koşu → köprü → composite_queue satırı → boru sayacı. Ağırlık ELLE
    YAZILMAZ; kuyruğa girmek onay değil ÖLÇÜM SIRASIdır (kapı + operatör hâlâ hakemdir)."""
    _tohumla(sandbox_state)
    tel = {"hafta": "2026-W32", "bolum_adlari": ["kar_selalesi"],
           "bolumler": {"kar_selalesi": {"n": 95, "genel": {"net_r": -0.0421,
                                                            "sinyal_mfe_r": 0.9648}}},
           "bounds_dugmeleri": [_KNOB_A, _KNOB_B]}
    metin = json.dumps({"oneriler": [
        {"alan": "kar_selalesi",
         "gozlem": "kar_selalesi net_r -0.0421 ve sinyal_mfe_r 0.9648 — stop mesafesi dar",
         "oneri": "stop_loss_atr_mult 2.0 ve exit.time_stop_days 10 demetini ölç",
         "beklenen_etki": "net_r +0.05", "onerilen_olcum": "prescreen yoklaması",
         "oncelik": "orta", "sekil": "parametre", "parametreler": {_KNOB_A: 2.0, _KNOB_B: 10}}]},
        ensure_ascii=False)
    out = nous_eval.haftalik_degerlendirme(telemetri=tel, text=metin, hafta="2026-W32")
    assert out["kosu"]["boru"][nous_eval.YOL_KUYRUK] == 1
    kuyruk = store.read_jsonl("composite_queue.jsonl")
    assert len(kuyruk) == 1 and kuyruk[0]["source"] == "nous_eval"
    assert kuyruk[0]["composite"] == {_KNOB_A: 2.0, _KNOB_B: 10}
    assert kuyruk[0]["status"] == "pending"                # ONAY DEĞİL, ölçüm sırası
    assert out["kabul"][0]["yol"] == nous_eval.YOL_KUYRUK


def test_haftalik_kosunun_SONUNDA_boru_otomatik_isler(sandbox_state, olaylar):
    """Boru elle tetiklenmez: haftalık kadansın sonunda kendiliğinden koşar ve koşu kaydına yazılır."""
    _tohumla(sandbox_state)
    tel = {"hafta": "2026-W32", "bolum_adlari": ["hotstate"],
           "bolumler": {"hotstate": {"hotstate_down": 7873}}, "bounds_dugmeleri": [_KNOB_A]}
    metin = json.dumps({"oneriler": [
        {"alan": "hotstate", "gozlem": "hotstate_down sayacı 7873 — sıcak katman kesintili",
         "oneri": "redis yeniden bağlanma stratejisini belgelendir",
         "beklenen_etki": "kesinti süresi düşer", "onerilen_olcum": "hotstate_down sayacı",
         "oncelik": "orta", "sekil": "tasarim"}]}, ensure_ascii=False)
    out = nous_eval.haftalik_degerlendirme(telemetri=tel, text=metin, hafta="2026-W32")
    assert out["kosu"]["boru"][nous_eval.YOL_FIS] == 1
    kosu = store.read_json(nous_eval.RUNS_FILE, {})["haftalar"]["2026-W32"]
    assert kosu["boru"][nous_eval.YOL_FIS] == 1              # koşu kaydında KALICI
    doc = store.read_json(nous_eval.FISLER_FILE, {})
    assert doc["n"] == 1 and doc["fisler"][0]["id"] == "N00001"   # defter kimliği fişe geçti


def test_kuru_kosumda_fis_defteri_YAZILMAZ(sandbox_state, olaylar):
    _tohumla(sandbox_state)
    nous_eval.boru([_oneri()], hafta="2026-W32", yaz=False)
    assert store.read_json(nous_eval.FISLER_FILE, None) is None
    assert [e for e in olaylar if e["ev"] == nous_eval.OLAY_FIS][0]["yazildi"] is False


# =================================================================================================
# TÜKETİCİLER (YASA 6): uç + pano
# =================================================================================================
def test_api_fis_kuyrugunu_SERVIS_eder(sandbox_state, olaylar):
    from meridian import api
    _tohumla(sandbox_state)
    assert api._nous_fisler()["durum"] == "defter_yok"       # "fiş yok" ile "defter yok" AYRI
    nous_eval.boru([_oneri(id="N00003")], hafta="2026-W32")
    d = api._nous_fisler()
    assert d["durum"] == "dolu" and d["n"] == 1 and d["n_acik"] == 1
    assert d["anahtarlar"] == ["N00003"]


def test_fis_defterinin_DIS_okuyucusu_var(sandbox_state):
    """`codelaw.artifact_graph`: kendi yazdığını kendi okuyan modül tüketici sayılmaz."""
    from meridian import codelaw
    g = codelaw.artifact_graph()["artifacts"].get(nous_eval.FISLER_FILE)
    assert g and g["external_readers"], f"{nous_eval.FISLER_FILE} okuyucusuz (YASA 6)"
    assert g["unread"] is False


def test_cli_boru_defterdeki_ESKI_onerileri_yonlendirir(sandbox_state, olaylar, monkeypatch, capsys):
    """Boru v192'de doğdu; ondan ÖNCE kabul edilmiş satırlar (canlı 2026-W32'nin üç `tasarim`
    önerisi) hiçbir yola bağlanmamıştı. Tek-atışlık `--boru` onları taşır — LLM ÇAĞIRMADAN."""
    _tohumla(sandbox_state)
    store.append_jsonl(nous_eval.PROPOSALS_FILE,
                       {"ts": "2026-08-04T00:28:00+00:00", "id": "N00002", "hafta": "2026-W32",
                        "alan": "hotstate", "gozlem": "hotstate_down 7873",
                        "oneri": "redis yeniden bağlanma stratejisini belgele",
                        "beklenen_etki": "kesinti düşer", "onerilen_olcum": "hotstate_down",
                        "oncelik": "orta", "sekil": "tasarim", "kanit_atifi": ["hotstate_down"],
                        "kuyruk": "yol_yok"})
    monkeypatch.setattr("sys.argv", ["nous_eval", "--boru"])
    assert nous_eval._cli() == 0
    cikti = json.loads(capsys.readouterr().out)
    assert cikti["hafta"] == "2026-W32" and cikti["ozet"][nous_eval.YOL_FIS] == 1
    assert store.read_json(nous_eval.FISLER_FILE, {})["fisler"][0]["anahtar"] == "N00002"


def test_pano_fis_rozetini_CIZER(sandbox_state):
    appjs = (pathlib.Path("meridian") / "web" / "app.js").read_text()
    kod = "\n".join(l for l in appjs.splitlines() if not l.lstrip().startswith("//"))
    assert "ml.nous_fisler" in kod, "pano fiş kuyruğunu okumuyor"
    assert "FİŞLENDİ" in kod, "fiş rozeti yok — operatör görünürlüğü kurulmadı"
    assert "KATMAN D" in kod, "çekirdek sınıfı panoda kuyruk gibi görünüyor"
    assert "yol_yok" not in kod, "çıkmaz sokak etiketi hâlâ çiziliyor"
