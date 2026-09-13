"""test_defter_ozeti_retain_v464.py — TSK-168: günlük defter özeti RETAIN akışı (EDG-2026-089).

NUMARA ÖLÇÜLDÜ (2026-09-13): ana checkout ve `.claude/worktrees/*` altında en büyük vNNN 463
(`test_yetim_damga_beyani_v463.py`); v464 İKİ ağaçta da BOŞTU. Numara bir KİMLİKTİR — çakışmada
az-çapalı taraf taşınır (CLAUDE.md §2).

NE ÖLÇÜLÜR. `ops/defter_ozeti_retain.py` kartın (EDG-2026-089) `pozitif_kontrol (1)` sentetik
şartını ve `olcum_plani`nın ilk iki maddesini KURAR:
  (a) SENTETİK PK — sahte kökten üretilen belgede BİLİNEN beş sayı kaynak yollarıyla VAR ve
      deftere sokulan sahte ANAHTAR DİZİSİ belgede YOK (sır süzgeci; kill#3).
  (b) `--kuru` HİÇBİR HTTP çağrısı yapmaz (ağ casusu) — belge stdout'a basılır.
  (c) `--uygula` önce `GET …/documents/{id}` (404) sonra `POST …/memories`; gövde upstream
      şemasına uyar (`document_id`, `async: true`, `content` ≤ tavan) → çıkış 0 + obs olayı.
  (d) AYNI GÜN İKİNCİ `--uygula` → GET 200 → POST YOK, çıkış 2 (idempotens; hata değil).
  (e) Anahtar hiçbir kanalda yoksa çıkış 1 + ADIYLA hata; anahtar DEĞERİ hiçbir çıktıda yok.
  (f) Kaynak taraması: betik model/ajan istemcisi İTHAL ETMEZ (kill#2) ve süzgeci çağırır.
  (g) Dağıtım yüzeyi: birim + timer + drop-in dosyaları, A0 rolü envanteri, rotasyon oneshot
      tablosu, sır envanteri tüketici notu.
  (h) AYRIŞMA ÇİVİSİ: betiğin taban URL'i / credential kimliği pano vekilininkiyle EŞİT.

GİRİŞ NOKTASI İKİ YÜZLÜDÜR ve ikisi de ölçülür (CLAUDE.md §1: "ops betiklerinin sözleşmesi KOMUT
SATIRIdır, `main()` değil" — 18 çivi yeşilken `--uygula` sessizce yok sayılmıştı). Ağ gerektiren
bacaklar süreç İÇİNDE `main([...])` ile koşar (urlopen casusu ancak orada kurulabilir); ağ
gerektirmeyen bacaklar AYRICA gerçek komut satırıyla alt süreçte koşulur.

ALT SÜREÇ CANLI `state/`E YAZMAZ: `--kok` bayrağı `config.STATE`i verilen ağacın altına çevirir,
yani alt sürecin obs/store yazımları `tmp_path` altında kalır — ajan turunun `state/` yazım yasağı
yapısal olarak korunur, sözle değil."""
from __future__ import annotations

import ast
import json
import os
import pathlib
import subprocess
import sys
import urllib.error
import urllib.request

import pytest

from tests.conftest import betikten_modul_yukle  # noqa: E402

KOK = pathlib.Path(__file__).resolve().parent.parent
BETIK = KOK / "ops" / "defter_ozeti_retain.py"
DEPLOY = KOK / "deploy" / "oracle-a1"
BIRIM_ADI = "meridian-defter-ozeti-retain"
TABAN = "http://127.0.0.1:8888"

GUN = "2026-09-12"
#: Deftere BİLEREK sokulan sahte anahtar. Süzgeç YALNIZ `secrets.ALLOWED` adlarının DEĞERLERİNİ
#: maskeler, o yüzden bu dizge sandbox'taki `state/secrets.json`a GERÇEK bir adla yazılır —
#: ölçülen şey süzgecin kendi yolu olsun, taklidi değil.
SAHTE_ANAHTAR = "sk-or-v1-" + "9f3c" * 10
#: Sahte TENANT anahtarı — `secrets.ALLOWED` DIŞINDA bir addır (pano vekilinin ölçtüğü gerçek:
#: `HINDSIGHT_API_*` motorun sır deposunda yaşamaz), o yüzden ortam basamağından verilir ve
#: süzgeç onu maskelemez. Çiviler onun HİÇBİR URL'e/olaya girmediğini ölçer.
TENANT_ANAHTAR = "tenant-" + "a1b2" * 8
#: Yasak ithal kümesi (kill#2). Belge bir MODEL çıktısı olursa kart GEÇERSİZDİR; yasağı ithal
#: düzeyinde ölçmek, "çağrı var mı" aramasının kaçıracağı dolaylı kullanımı da kapatır.
YASAK_ITHALLER = ("hermes", "hermes_composite", "skill_gorus_llm", "reflect", "nous_eval",
                  "anthropic", "openai", "httpx", "requests")


# =================================================================================================
# ORTAK ZEMİN
# =================================================================================================

@pytest.fixture(autouse=True)
def _ag_kapali(monkeypatch):
    """Bu dosyadaki HİÇBİR test gerçek ağa çıkmaz. Kapı `urllib.request.urlopen`tadır çünkü
    betiğin tek dış-çağrı boğazı odur; casus kurmayan bir test canlı 8888'e giderdi."""
    def _yasak(*a, **k):
        raise AssertionError("test ağa çıktı — urlopen çağrıldı")
    monkeypatch.setattr(urllib.request, "urlopen", _yasak)


@pytest.fixture
def betik():
    assert BETIK.exists(), f"{BETIK} YOK"
    return betikten_modul_yukle(BETIK, "defter_ozeti_retain")


def _sahte_kok(tmp_path, gun: str = GUN) -> pathlib.Path:
    """Bilinen sayılarla dolu SAHTE kök. `sandbox_state` zaten `config.STATE`i `tmp_path/state`e
    çevirdiği için kök `tmp_path`tir ve betiğe `--kok tmp_path` verilir: iki yol AYNI dizini
    gösterir, yani çivi betiğin kendi `--kok` çözümünü de ölçer."""
    from meridian import store

    (tmp_path / "state").mkdir(exist_ok=True)
    (tmp_path / "research" / "cards").mkdir(parents=True, exist_ok=True)

    store.write_json("dagitim.json", {"deployed_sha": "405607cabc1234",
                                      "dagitildi_utc": f"{gun}T20:11:04Z", "dagitan_host": "mac"})
    # Üç işlem satırı: İKİSİ o gün kapandı (R +1,5 / −1,0), biri ÖNCEKİ gün (gün süzgeci ölçülsün).
    for satir in (
        {"id": "T1", "ticker": "AAA", "ts_close": f"{gun}T20:00:00Z", "r_multiple": 1.5},
        {"id": "T2", "ticker": "BBB", "ts_close": f"{gun}T20:05:00Z", "r_multiple": -1.0},
        {"id": "T3", "ticker": "CCC", "ts_close": "2026-09-11T20:05:00Z", "r_multiple": 4.0},
    ):
        store.append_jsonl("trades.jsonl", satir)
    store.write_json("portfolio.json", {"positions": {"DDD": {}, "EEE": {}, "FFF": {}},
                                        "last_date": gun})
    # İki alarm: biri jetonlu (`alarm` alanı), biri YALNIZ `event` metniyle — ve o metin sahte
    # anahtarı TAŞIR, yani süzgeç çalışmazsa dizge belgeye ÇIKAR.
    for satir in (
        {"ts": f"{gun}T18:00:00Z", "level": "alarm", "event": "DATA_QUALITY bar yok",
         "alarm": "DATA_QUALITY", "message": "bar yok"},
        {"ts": f"{gun}T19:00:00Z", "level": "alarm",
         "event": f"UPSTREAM_401 anahtar={SAHTE_ANAHTAR}"},
        {"ts": "2026-09-11T19:00:00Z", "level": "alarm", "event": "ESKI_GUN", "alarm": "ESKI_GUN"},
        {"ts": f"{gun}T19:30:00Z", "level": "info", "event": "gun_ici_bilgi"},
    ):
        store.append_jsonl("events.jsonl", satir)
    for satir in (
        {"date": gun, "motor": "ayna", "karar": "submitted", "fill": 101.25, "plan_id": "P1"},
        {"date": gun, "motor": "ic", "karar": "submitted", "plan_id": "P2"},
        {"date": "2026-09-11", "motor": "ayna", "karar": "rejected", "plan_id": "P0"},
    ):
        store.append_jsonl("entry_execution.jsonl", satir)
    (tmp_path / "research" / "cards" / "EDG-2026-999-sahte.yaml").write_text(
        "card_id: EDG-2026-999\n"
        f"status: measured   # {gun} Rol-1 — SENTETİK HÜKÜM: sahte kart bugünkü hükmü taşır\n"
        "thesis: Sentetik kart — yalnız çivi için.\n",
        encoding="utf-8")
    return tmp_path


@pytest.fixture
def kok(tmp_path, sandbox_state, monkeypatch):
    """Sahte kök + sandbox sır deposu + sahte tenant anahtarı (ortam basamağı).

    `secrets.clear_cache()` ŞART: `secrets.get` 300 sn'lik süreç-içi önbellek tutar ve komşu bir
    testin okuduğu değer bu testin süzgecini SESSİZCE boşa çıkarırdı."""
    from meridian import secrets
    yol = _sahte_kok(tmp_path)
    sir = sandbox_state / "secrets.json"
    sir.write_text(json.dumps({"HERMES_API_KEY": SAHTE_ANAHTAR}), encoding="utf-8")
    os.chmod(sir, 0o600)
    monkeypatch.setenv("HINDSIGHT_API_TENANT_API_KEY", TENANT_ANAHTAR)
    secrets.clear_cache()
    yield yol
    secrets.clear_cache()


@pytest.fixture
def bos_kok(tmp_path, sandbox_state):
    """Hiçbir defteri OLMAYAN kök — 'ölçülemedi' dalının zemini."""
    (tmp_path / "research" / "cards").mkdir(parents=True, exist_ok=True)
    return tmp_path


class _Cevap:
    """`urlopen` bağlam yöneticisinin ölçülen yüzeyi: `status` + `read()`."""

    def __init__(self, status: int, govde: bytes = b"{}"):
        self.status, self._govde = status, govde

    def read(self) -> bytes:
        return self._govde

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def _yok_404(url: str) -> urllib.error.HTTPError:
    """GERÇEK davranış: `urlopen` 404'ü DÖNDÜRMEZ, `HTTPError` FIRLATIR. Sahte bir 404 `_Cevap`ı
    dönmek, betiğin hiç koşmayacağı bir dalı ölçerdi."""
    return urllib.error.HTTPError(url, 404, "Not Found", {}, None)


def _casus(monkeypatch, cevaplar: dict[str, object]) -> list[dict]:
    """`urlopen` casusu: çağrıları KAYDEDER, `"<YÖNTEM> <url parçası>"` desenine göre hazır cevap
    döner (değer bir istisnaysa FIRLATIR). Karşılığı olmayan çağrı sessizce geçmez — düşer."""
    kayit: list[dict] = []

    def _sahte(istek, timeout=None):
        kayit.append({"yontem": istek.get_method(), "url": istek.full_url,
                      "basliklar": dict(istek.headers), "govde": istek.data, "timeout": timeout})
        anahtar = f"{istek.get_method()} {istek.full_url}"
        for desen, cevap in cevaplar.items():
            if desen in anahtar:
                if isinstance(cevap, Exception):
                    raise cevap
                if callable(cevap):
                    raise cevap(istek.full_url)
                return cevap
        raise AssertionError(f"casusta karşılığı olmayan çağrı: {anahtar}")

    monkeypatch.setattr(urllib.request, "urlopen", _sahte)
    return kayit


def _ortam_kredensiyelsiz() -> dict:
    """Alt süreç ortamı: systemd credential kanalı KAPALI (yerelde kurulu olsaydı GERÇEK anahtar
    okunurdu — `sandbox_state`in kendi gerekçesinin alt-süreç karşılığı)."""
    ort = {k: v for k, v in os.environ.items() if k != "CREDENTIALS_DIRECTORY"}
    ort.pop("HINDSIGHT_API_TENANT_API_KEY", None)
    return ort


def _cli(*bayrak: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(BETIK), *bayrak],
                          capture_output=True, text=True, cwd=str(KOK),
                          env=_ortam_kredensiyelsiz())


# =================================================================================================
# (a) SENTETİK POZİTİF KONTROL — bilinen beş sayı VAR, sahte anahtar YOK
# =================================================================================================

def test_a1_belge_BILINEN_BES_SAYIYI_kaynak_yoluyla_TASIR(betik, kok):
    """Kartın PK(1)'i: sahte defterden üretilen belge beş bilinen sayıyı ve HER birinin kaynak
    yolunu taşır. Kaynak yolu olmayan bir sayı, defterden okunduğu KANITLANAMAYAN bir sayıdır."""
    metin = betik.belge_uret(GUN, kok)
    for beklenen in ("405607c",                 # (1) dağıtım sha, ilk 7
                     "kapanan işlem 2",         # (2) o gün kapanan işlem
                     "+0.50",                   # (3) toplam R = +1,5 − 1,0
                     "açık pozisyon 3",         # (4) portfolio positions
                     "dolum 1"):                # (5) EXE-011 dönüşüm
        assert beklenen in metin, f"{beklenen!r} belgede YOK:\n{metin}"
    for yol in ("state/dagitim.json", "state/trades.jsonl", "state/portfolio.json",
                "state/events.jsonl", "state/entry_execution.jsonl"):
        assert yol in metin, f"kaynak yolu {yol} belgede YOK:\n{metin}"
    assert metin.startswith(f"# Meridian günlük defter özeti — {GUN}")
    assert metin.rstrip().endswith("(EDG-2026-089, TSK-168).")


def test_a2_SAHTE_ANAHTAR_belgeye_SIZMAZ(betik, kok):
    """kill#3: süzgeç atlanırsa akış KAPATILIR. Defterdeki alarm metni anahtarı taşıyor —
    belge onu taşımamalı."""
    metin = betik.belge_uret(GUN, kok)
    assert SAHTE_ANAHTAR not in metin, "sahte anahtar belgeye SIZDI (sır süzgeci atlandı)"
    assert "***" in metin, "maskeleme izi YOK — süzgeç hiç çalışmamış olabilir"


def test_a3_o_GUN_hukum_alan_kart_listelenir_otekiler_DEGIL(betik, kok):
    """Kart hükmü satırı kartların KENDİ `status` yorumundan gelir (kart endeksi üreticisi ithal
    edilir, kopyalanmaz); günü taşımayan kart listeye GİRMEZ."""
    (kok / "research" / "cards" / "EDG-2026-998-eski.yaml").write_text(
        "card_id: EDG-2026-998\nstatus: measured   # 2026-01-01 Rol-1 — ESKİ hüküm\n"
        "thesis: Eski kart.\n", encoding="utf-8")
    metin = betik.belge_uret(GUN, kok)
    assert "EDG-2026-999" in metin
    assert "EDG-2026-998" not in metin, "günü taşımayan kart listeye girdi"
    assert "research/cards/EDG-2026-999-sahte.yaml" in metin


def test_a4_OLCULEMEYEN_alan_None_ve_NEDEN_ile_yazilir(betik, bos_kok):
    """UYDURMA YASAĞI: boş bir kökte sayı SIFIRA düşmez, `None` + neden yazılır. Sıfır ile
    'bilmiyorum' aynı şey değildir."""
    metin = betik.belge_uret(GUN, bos_kok)
    assert "None" in metin, f"ölçülemeyen alan None ile yazılmadı:\n{metin}"
    assert "state/dagitim.json" in metin
    assert metin.rstrip().endswith("(EDG-2026-089, TSK-168).")


def test_a5_belge_TAVANI_asilmaz_ve_kesme_BEYANLI(betik, kok):
    """≤4.000 karakter sözleşmesi. Kesme SESSİZ olamaz (bedel yasası): kesilen karakter sayısı
    belgeye yazılır ve son satır (kaynak beyanı) HAYATTA kalır.

    TAVANI AŞTIRAN GİRDİ GERÇEKÇİ: bir gün otuz kart birden hüküm alırsa (eleme turu) kart bölümü
    tek başına tavanı aşar — sentetik bir 'çok uzun tek satır' değil, bu akışın kendi yükü."""
    _kartlari_cogalt(kok)
    metin = betik.belge_uret(GUN, kok)
    assert len(metin) <= betik.BELGE_TAVANI, len(metin)
    assert "KESİLDİ" in metin, "tavan aşıldı ama kesme beyan edilmedi"
    assert metin.rstrip().endswith("(EDG-2026-089, TSK-168).")


# =================================================================================================
# (b) `--kuru` — HTTP YOK
# =================================================================================================

def test_b1_kuru_HICBIR_HTTP_CAGRISI_yapmaz(betik, kok, capsys):
    """`--kuru` belgeyi basar ve DURUR. Ağ casusu autouse fixture'dadır: bir çağrı olsaydı
    AssertionError uçardı."""
    rc = betik.main(["--kuru", "--gun", GUN, "--kok", str(kok)])
    assert rc == 0
    cikti = capsys.readouterr().out
    assert f"# Meridian günlük defter özeti — {GUN}" in cikti
    assert SAHTE_ANAHTAR not in cikti


def test_b2_kuru_GERCEK_KOMUT_SATIRINDAN_da_kosar(kok):
    """Giriş noktası `main()` DEĞİL komut satırıdır: argparse `--kuru`yu görmüyorsa bu çivi
    yakalar (CLAUDE.md §1 vakası)."""
    r = _cli("--kuru", "--gun", GUN, "--kok", str(kok))
    assert r.returncode == 0, r.stdout + r.stderr
    assert f"# Meridian günlük defter özeti — {GUN}" in r.stdout
    assert SAHTE_ANAHTAR not in r.stdout + r.stderr


def test_b3_kuru_OBS_OLAYI_yazmaz(betik, kok, sandbox_state):
    """`--kuru` bir ÖLÇÜM koşumudur; defter yazsaydı operatörün kuru koşumu K1 sayımını şişirirdi
    (ajanın pytest-dışı state yazımı dersinin bu betikteki karşılığı)."""
    defter = sandbox_state / "events.jsonl"
    once = defter.read_text(encoding="utf-8") if defter.exists() else ""
    betik.main(["--kuru", "--gun", GUN, "--kok", str(kok)])
    sonra = defter.read_text(encoding="utf-8") if defter.exists() else ""
    assert betik.OLAY not in sonra[len(once):], "kuru koşum deftere yazdı"


# =================================================================================================
# (c) `--uygula` — GET(404) → POST
# =================================================================================================

def test_c1_uygula_ONCE_GET_sonra_POST_yapar_ve_govde_SEMAYA_uyar(betik, kok, monkeypatch):
    kayit = _casus(monkeypatch, {
        f"GET {TABAN}/v1/default/banks/meridian-arsiv/documents/": _yok_404,
        f"POST {TABAN}/v1/default/banks/meridian-arsiv/memories":
            _Cevap(200, json.dumps({"success": True, "items_count": 1,
                                    "operation_ids": ["op-1"]}).encode()),
    })
    rc = betik.main(["--uygula", "--gun", GUN, "--kok", str(kok)])
    assert rc == 0, rc
    assert [k["yontem"] for k in kayit] == ["GET", "POST"], kayit
    assert kayit[0]["url"].endswith(f"/documents/meridian-gunluk-ozet-{GUN}")
    govde = json.loads(kayit[1]["govde"].decode())
    assert govde["async"] is True
    assert len(govde["items"]) == 1
    item = govde["items"][0]
    assert item["document_id"] == f"meridian-gunluk-ozet-{GUN}"
    assert item["timestamp"].startswith(GUN)
    assert item["tags"] == ["meridian", "gunluk-ozet"]
    assert item["context"]
    assert item["metadata"]["kaynak"] == "ops/defter_ozeti_retain.py"
    assert len(item["metadata"]["blob_sha"]) == 64
    assert 0 < len(item["content"]) <= betik.BELGE_TAVANI


def test_c2_uygula_KIMLIGI_BASLIKTA_tasir_URLde_DEGIL(betik, kok, monkeypatch):
    """Sır URL'e/query'ye ASLA girmez — `Authorization` başlığı tek taşıyıcıdır."""
    kayit = _casus(monkeypatch, {f"GET {TABAN}": _yok_404,
                                 f"POST {TABAN}": _Cevap(200, b'{"success": true}')})
    betik.main(["--uygula", "--gun", GUN, "--kok", str(kok)])
    for cagri in kayit:
        basliklar = {k.lower(): v for k, v in cagri["basliklar"].items()}
        assert basliklar.get("authorization", "") == f"Bearer {TENANT_ANAHTAR}"
        assert TENANT_ANAHTAR not in cagri["url"], "sır URL'e girdi"
        assert SAHTE_ANAHTAR not in cagri["url"]


def test_c3_uygula_OBS_OLAYINI_yazar(betik, kok, monkeypatch, sandbox_state):
    """Yasa 6: olayın okuyucusu EDG-089 K1 sayımı + bekçi brifinginin jenerik `durum:` yolu."""
    _casus(monkeypatch, {f"GET {TABAN}": _yok_404,
                         f"POST {TABAN}": _Cevap(
                             200, json.dumps({"operation_ids": ["op-7"]}).encode())})
    betik.main(["--uygula", "--gun", GUN, "--kok", str(kok)])
    satirlar = [json.loads(s) for s in
                (sandbox_state / "events.jsonl").read_text(encoding="utf-8").splitlines()
                if s.strip()]
    olay = [s for s in satirlar if s.get("event") == betik.OLAY]
    assert olay, satirlar
    son = olay[-1]
    assert son["sonuc"] == "retain"
    assert son["gun"] == GUN
    assert son["document_id"] == f"meridian-gunluk-ozet-{GUN}"
    assert son["items"] == 1
    assert son["karakter"] > 0
    assert TENANT_ANAHTAR not in json.dumps(son), "anahtar DEĞERİ olaya sızdı"
    assert SAHTE_ANAHTAR not in json.dumps(son)


def _kartlari_cogalt(kok, n: int = 30) -> None:
    """Tavanı AŞTIRAN gerçekçi yük: bir eleme turunda otuz kart birden hüküm alır."""
    for i in range(n):
        (kok / "research" / "cards" / f"EDG-2026-{800 + i}-toplu.yaml").write_text(
            f"card_id: EDG-2026-{800 + i}\n"
            f"status: measured   # {GUN} Rol-1 — TOPLU ELEME HÜKMÜ: " + "h" * 150 + "\n"
            "thesis: Toplu eleme turu kartı.\n", encoding="utf-8")


def test_c5_TAVANI_ASAN_belge_de_TAVAN_ALTINDA_POSTlanir(betik, kok, monkeypatch):
    """Tavan bir BELGE ÜRETİCİ süsü değil, GÖNDERİLEN gövdenin sözleşmesidir. (c1) küçük bir
    belgeyle koşar ve orada tavan iddiası BOŞTUR (mutasyonla ölçüldü: tavanı kaldırmak (c1)'i
    kırmıyordu) — bu çivi aynı iddiayı tavanın GERÇEKTEN bağladığı yükte kurar."""
    _kartlari_cogalt(kok)
    kayit = _casus(monkeypatch, {f"GET {TABAN}": _yok_404,
                                 f"POST {TABAN}": _Cevap(200, b'{"success": true}')})
    assert betik.main(["--uygula", "--gun", GUN, "--kok", str(kok)]) == 0
    item = json.loads(kayit[1]["govde"].decode())["items"][0]
    assert len(item["content"]) <= betik.BELGE_TAVANI, len(item["content"])
    assert "KESİLDİ" in item["content"]
    # `blob_sha` GÖNDERİLEN metnin sha'sıdır — kesilmeden ÖNCEKİ metnin değil; ayrışsaydı bankadaki
    # belge ile damgası birbirini doğrulayamazdı.
    import hashlib
    assert item["metadata"]["blob_sha"] == hashlib.sha256(
        item["content"].encode("utf-8")).hexdigest()


def test_c4_POST_HATASI_SESSIZ_DEGIL_cikis_1(betik, kok, monkeypatch, capsys):
    """Yasa 4: retain düşerse çıkış 1 ve sebep ADIYLA stderr'e — sessiz 0 dönmek 'bugün retain
    edildi' yalanı olurdu ve K1 sayımı o yalanı ölçemez."""
    _casus(monkeypatch, {f"GET {TABAN}": _yok_404,
                         f"POST {TABAN}": OSError("bağlantı reddedildi")})
    rc = betik.main(["--uygula", "--gun", GUN, "--kok", str(kok)])
    assert rc == 1
    assert "bağlantı reddedildi" in capsys.readouterr().err


# =================================================================================================
# (d) İDEMPOTENS — aynı gün ikinci koşum
# =================================================================================================

def test_d1_ayni_gun_IKINCI_kosum_POST_YAPMAZ_cikis_2(betik, kok, monkeypatch):
    kayit = _casus(monkeypatch, {
        f"GET {TABAN}": _Cevap(200, json.dumps(
            {"document_id": f"meridian-gunluk-ozet-{GUN}"}).encode()),
        f"POST {TABAN}": _Cevap(200, b"{}"),
    })
    rc = betik.main(["--uygula", "--gun", GUN, "--kok", str(kok)])
    assert rc == 2, rc
    assert [k["yontem"] for k in kayit] == ["GET"], f"idempotens kapısı POST'u durdurmadı: {kayit}"


def test_d2_zaten_var_OLAYI_SONUC_alaniyla_ayrilir(betik, kok, monkeypatch, sandbox_state):
    """'retain edildi' ile 'zaten vardı' AYRI sonuç sınıfıdır — K1 kadansı ikisini karıştırırsa
    dolmayan bir gün dolmuş görünür."""
    _casus(monkeypatch, {f"GET {TABAN}": _Cevap(200, b"{}")})
    betik.main(["--uygula", "--gun", GUN, "--kok", str(kok)])
    satirlar = [json.loads(s) for s in
                (sandbox_state / "events.jsonl").read_text(encoding="utf-8").splitlines()
                if s.strip()]
    olay = [s for s in satirlar if s.get("event") == betik.OLAY][-1]
    assert olay["sonuc"] == "zaten_var"


# =================================================================================================
# (e) ANAHTAR YOKSA — çıkış 1, ADIYLA, DEĞERSİZ
# =================================================================================================

def test_e1_anahtar_yoksa_cikis_1_ve_AD_stderrde(betik, bos_kok, capsys, monkeypatch):
    """Sessiz düşüş YOK: anahtarsız bir POST 401 alıp 'retain denendi' gibi görünürdü."""
    from meridian import secrets
    monkeypatch.delenv(secrets.CREDENTIAL_DIZIN_ENV, raising=False)
    monkeypatch.delenv(betik.KRED_ADI, raising=False)
    secrets.clear_cache()
    try:
        rc = betik.main(["--uygula", "--gun", GUN, "--kok", str(bos_kok)])
    finally:
        secrets.clear_cache()
    assert rc == 1
    hata = capsys.readouterr().err
    assert betik.KRED_ADI in hata, hata


def test_e2_anahtarsiz_KOMUT_SATIRI_da_1_doner_ve_DEGER_basmaz(bos_kok):
    """Aynı sözleşme gerçek komut satırında. `--uygula` ağ gerektirmeden burada durur (anahtar
    çözümü İLK adımdır), o yüzden alt süreçte güvenle ölçülür."""
    r = _cli("--uygula", "--gun", GUN, "--kok", str(bos_kok))
    assert r.returncode == 1, r.stdout + r.stderr
    assert "HINDSIGHT_API_TENANT_API_KEY" in r.stderr
    assert TENANT_ANAHTAR not in r.stdout + r.stderr
    assert SAHTE_ANAHTAR not in r.stdout + r.stderr


def test_e3_CIKIS_KODLARI_SABIT_ve_AYRI(betik):
    """Üç sınıf üç sayıdır: 0 retain · 2 zaten var (hata DEĞİL) · 1 hata."""
    assert (betik.CIKIS_RETAIN, betik.CIKIS_ZATEN_VAR, betik.CIKIS_HATA) == (0, 2, 1)


def test_e4_KIP_BAYRAGI_TEK_olmali_ve_BAYRAKSIZ_kosum_RETAIN_ETMEZ(betik, kok, capsys):
    """MUTASYONLA BULUNDU (bu turda): `--uygula` bayrağını sessizce yok sayan bir sürüm 29 çivinin
    HİÇBİRİNİ kırmıyordu — çünkü kip kapısı kaldırıldığında bayraksız koşum "varsayılan olarak"
    retain yoluna düşüyordu ve hiçbir çivi o yolu sormuyordu. Bu tam olarak CLAUDE.md §1'in
    vakasıdır ("18 çivi yeşilken `--uygula` sessizce yok sayılıyordu"), o yüzden kapı ADIYLA
    ölçülür: kip bayrağı YOKSA ya da İKİSİ BİRDEN varsa çıkış 1 ve HİÇBİR ağ çağrısı yok
    (autouse ağ casusu bir çağrıda düşerdi)."""
    assert betik.main(["--gun", GUN, "--kok", str(kok)]) == 1
    assert "kip bayrağı TEK olmalı" in capsys.readouterr().err
    assert betik.main(["--kuru", "--uygula", "--gun", GUN, "--kok", str(kok)]) == 1


# =================================================================================================
# (f) KAYNAK TARAMASI — model yok, süzgeç var
# =================================================================================================

def _ithal_adlari(yol: pathlib.Path) -> set[str]:
    """Betiğin İTHAL ettiği modül adları (AST ile — düzyazı bir yasak kelimeyi taşısa bile
    ithal ölçümü yanılmaz; tersi de geçerli: gizlenmiş bir ithal düzyazıya bakarak kaçmaz)."""
    adlar: set[str] = set()
    for dugum in ast.walk(ast.parse(yol.read_text(encoding="utf-8"))):
        if isinstance(dugum, ast.Import):
            adlar.update(a.name for a in dugum.names)
        elif isinstance(dugum, ast.ImportFrom):
            adlar.add(dugum.module or "")
            adlar.update(f"{dugum.module or ''}.{a.name}" for a in dugum.names)
    return {a.split(".")[-1] for a in adlar} | adlar


def test_f1_betik_MODEL_veya_AJAN_istemcisi_ITHAL_ETMEZ():
    """kill#2: özet belgeyi bir model üretirse kart GEÇERSİZDİR. Yasak İTHALDE ölçülür — çağrı
    aramak, ithal edilmiş bir istemcinin dolaylı kullanımını kaçırırdı."""
    adlar = _ithal_adlari(BETIK)
    kesisim = adlar & set(YASAK_ITHALLER)
    assert not kesisim, f"betik yasak yüzeyi ithal ediyor: {sorted(kesisim)}"
    assert "urllib.request" in adlar or "request" in adlar, \
        "pozitif kontrol: ithal tarayıcı hiçbir şey görmüyor"


def test_f2_betik_SIR_SUZGECINI_cagirir(kod_govdesi):
    """Belgenin TAMAMI süzgeçten geçer; çağrının varlığı kaynakta ölçülür (davranış (a2)'de)."""
    metin = kod_govdesi(BETIK)
    assert "notify.scrub" in metin, "sır süzgeci çağrısı YOK (kill#3 yüzeyi açık)"


# =================================================================================================
# (g) DAĞITIM YÜZEYİ
# =================================================================================================

def test_g1_birim_timer_ve_dropin_dosyalari_VAR():
    assert (DEPLOY / f"{BIRIM_ADI}.service").exists()
    assert (DEPLOY / f"{BIRIM_ADI}.timer").exists()
    assert (DEPLOY / f"{BIRIM_ADI}.service.d" / "54-hafiza-credential.conf").exists()


def test_g2_birim_ONESHOT_ve_ExecStart_betigi_gosterir():
    metin = (DEPLOY / f"{BIRIM_ADI}.service").read_text(encoding="utf-8")
    assert "Type=oneshot" in metin
    assert "User=ubuntu" in metin
    assert "WorkingDirectory=/opt/meridian" in metin
    assert ("ExecStart=/opt/meridian/.venv/bin/python "
            "/opt/meridian/ops/defter_ozeti_retain.py --uygula") in metin
    assert "TimeoutStartSec=300" in metin
    # BÖLÜM BAŞLIĞI ölçülür, METİN değil: gerekçe şerhi `[Install]`i ADIYLA anlatır (ve anlatmalı —
    # yokluğun gerekçesi yazılmazsa bir sonraki okuyucu onu eksik sanıp ekler). Düz alt-dizge
    # araması o şerhi ihlal sanardı; systemd'nin gördüğü şey SATIR BAŞINDAKİ bölüm başlığıdır.
    assert not [s for s in metin.splitlines() if s.strip() == "[Install]"], \
        "tetik YALNIZ timer olmalı (v327 dersi)"


def test_g3_sertlestirme_satirlari_BRIFING_ile_AYNI():
    """Sertleştirme kümesi filoda BİREBİRdir; bir satırın eksikliği sessiz bir maruziyettir.
    Küme REFERANS BİRİMDEN türetilir, elle yazılmaz — kopya listesi ayrışırdı."""
    referans = (DEPLOY / "meridian-brifing.service").read_text(encoding="utf-8")
    yeni = (DEPLOY / f"{BIRIM_ADI}.service").read_text(encoding="utf-8")
    onekler = ("NoNewPrivileges", "CapabilityBoundingSet", "ProtectSystem", "ProtectHome",
               "PrivateTmp", "ProtectKernelTunables", "ProtectKernelModules", "ProtectKernelLogs",
               "ProtectClock", "ProtectControlGroups", "ProtectHostname", "RestrictNamespaces",
               "RestrictSUIDSGID", "RestrictRealtime", "LockPersonality",
               "RestrictAddressFamilies", "SystemCallArchitectures", "SystemCallFilter")
    beklenen = [s.strip() for s in referans.splitlines()
                if s.strip().split("=")[0] in onekler]
    assert len(beklenen) == len(onekler), beklenen
    for satir in beklenen:
        if satir.startswith("RestrictAddressFamilies"):
            continue           # ağ ailesi kümesi aşağıda AYRICA ölçülür (bu birim de ağa çıkar)
        assert satir in yeni, f"sertleştirme satırı EKSİK/AYRIK: {satir}"
    assert "RestrictAddressFamilies=AF_INET AF_INET6 AF_UNIX" in yeni


def test_g4_timer_2130_UTC_ve_PERSISTENT():
    metin = (DEPLOY / f"{BIRIM_ADI}.timer").read_text(encoding="utf-8")
    assert "OnCalendar=*-*-* 21:30:00 UTC" in metin
    assert "Persistent=true" in metin
    assert "RandomizedDelaySec=120" in metin
    assert "WantedBy=timers.target" in metin


def test_g5_dropin_LOADCREDENTIAL_kaynagi_MOTOR_dropiniyle_AYNI():
    """Kimlik = sır ADI; kaynak dosya hindsight creds dizinindeki TEK kopyadır (aynı kaynak, çok
    tüketici — systemd `LoadCredential`ı birim başına okur)."""
    yeni = (DEPLOY / f"{BIRIM_ADI}.service.d" / "54-hafiza-credential.conf").read_text(
        encoding="utf-8")
    referans = (DEPLOY / "meridian.service.d" / "54-hafiza-credential.conf").read_text(
        encoding="utf-8")
    satir = ("LoadCredential=HINDSIGHT_API_TENANT_API_KEY:"
             "/etc/hindsight/creds/HINDSIGHT_API_TENANT_API_KEY")
    assert satir in referans, "referans drop-in değişmiş — iki taraf ayrıştı"
    assert satir in yeni


def test_g6_A0_ROLU_dropin_dizinini_ve_KAYNAGINI_tasir():
    """Rol envanteri iki listedir ve v451 Çivi 2 ikisini gerçek ağaçla EŞİTLER; yeni drop-in
    dizini ikisine de girmezse ya kopyalanmaz ya boş dizin doğar."""
    import yaml
    defaults = yaml.safe_load(
        (KOK / "deploy/ansible/roles/meridian_a1/defaults/main.yml").read_text(encoding="utf-8"))
    assert f"{BIRIM_ADI}.service.d" in defaults["dropin_dizinleri"]
    assert any(f"{BIRIM_ADI}.service.d" in d for d in defaults["dropin_kaynaklari"])


def test_g7_ROTASYON_oneshot_tablosunda_birim_VAR():
    """P6 (v447) iki tabloyu drop-in kümesiyle EŞİTLER: satır eklenmezse P6 kırmızı olur. Satır
    ONESHOT tabloda durur — rotasyon penceresi timer'lı oneshot birimi yeniden BAŞLATMAZ."""
    metin = (DEPLOY / "sir_rotasyon.sh").read_text(encoding="utf-8")
    govde = metin.split("<<'ONESHOT_KRED_SON'\n", 1)[1].split("\nONESHOT_KRED_SON\n", 1)[0]
    satirlar = [s.split() for s in govde.splitlines() if s.strip()]
    beklenen = ["tenant", f"{BIRIM_ADI}.service", "HINDSIGHT_API_TENANT_API_KEY",
                "/etc/hindsight/creds/HINDSIGHT_API_TENANT_API_KEY"]
    assert beklenen in satirlar, satirlar


def test_g8_SIR_ENVANTERI_tuketici_notunu_tasir():
    """Envanterdeki tenant creds kopyası artık ÜÇ tüketicilidir; not olmadan rotasyon operatöre
    'bu birim neden yeniden başlamadı' sorusunun cevabını hiçbir yerde yazmazdı."""
    import yaml
    envanter = yaml.safe_load((KOK / "deploy/sir_envanteri.yaml").read_text(encoding="utf-8"))
    kopyalar = envanter["rotasyon_kopyalari"]["kopyalar"]
    creds = [k for k in kopyalar
             if k["yol"] == "/etc/hindsight/creds/HINDSIGHT_API_TENANT_API_KEY"]
    assert len(creds) == 1, creds
    assert BIRIM_ADI in creds[0]["tuketici"], creds[0]["tuketici"]


# =================================================================================================
# (h) AYRIŞMA ÇİVİSİ — taban URL / credential kimliği
# =================================================================================================

def test_h1_taban_url_ve_KRED_ADI_pano_vekiliyle_AYRISMAZ(betik):
    """Betik `meridian.api`yi İTHAL ETMEZ (oneshot bir birim FastAPI uygulamasını kurmamalı), o
    yüzden iki sabit KOPYADIR — kopya kaçınılmazsa ayrışma çivisi kurulur (tek-kaynak yasası)."""
    from meridian import api
    assert betik.TABAN_URL_VARSAYILAN == api.HAFIZA_TABAN_URL
    assert betik.KRED_ADI == api.HAFIZA_KRED_ADI


def test_g7_SuccessExitStatus_2_ve_timer_ETKIN_LISTEDE():
    """Rol-1 hükümleri 2026-09-13 (implementer kaygı 2/3): aynı gün ikinci tetik idempotens sonucudur,
    `failed` değil (`SuccessExitStatus=2`); kadans operatör (b) kararıyla AÇIK — timer `etkin_timerlar`da.
    Hangi üretim değişikliğinde kırılır: satır silinirse (gün-1 sahte failed) ya da timer listeden düşerse (K1 hiç dolmaz)."""
    birim = (DEPLOY / "meridian-defter-ozeti-retain.service").read_text(encoding="utf-8")
    assert "SuccessExitStatus=2" in birim
    defaults = (KOK / "deploy" / "ansible" / "roles" / "meridian_a1" / "defaults" / "main.yml").read_text(encoding="utf-8")
    blok = defaults[defaults.index("etkin_timerlar:"):]
    blok = blok[:blok.index("\n\n")]
    assert "meridian-defter-ozeti-retain.timer" in blok, "timer etkin listede değil — kadans açılmaz, K1 dolmaz"


def test_a4_TENANT_ANAHTARI_defterden_belgeye_ve_POST_govdesine_SIZMAZ(betik, kok, monkeypatch):
    """İnceleme ORTA-1 (2026-09-13): `notify.scrub` yalnız `secrets.ALLOWED` adlarını maskeler, tenant
    anahtarı o kümede DEĞİL — betiğin kendi `_maskele`si belgeye uygulanır. Defterdeki bir alarm
    metni anahtar DEĞERİNİ taşıyor; POST gövdesi onu taşımamalı (kill#3 sıfır tolerans).
    Hangi üretim değişikliğinde kırılır: `_maskele(belge, anahtar)` çağrısı kaldırılırsa."""
    # Alarm bölümü yalnız SINIF SAYAR (metin belgeye girmez) — sızıntı vektörü belgeye GİREN bir
    # alan olmalı: kartın `status` yorumu (hüküm ilk 160 karakter) belgeye aynen taşınır.
    (kok / "research" / "cards" / "EDG-2026-997-sizinti.yaml").write_text(
        f"card_id: EDG-2026-997\nstatus: measured   # {GUN} Rol-1 — hata metni: {TENANT_ANAHTAR}\n"
        "thesis: Sızıntı denemesi.\n", encoding="utf-8")
    kayit = _casus(monkeypatch, {
        f"GET {TABAN}/v1/default/banks/meridian-arsiv/documents/": _yok_404,
        f"POST {TABAN}/v1/default/banks/meridian-arsiv/memories":
            _Cevap(200, json.dumps({"success": True, "items_count": 1,
                                    "operation_ids": ["op-9"]}).encode()),
    })
    rc = betik.main(["--uygula", "--gun", GUN, "--kok", str(kok)])
    assert rc == 0, rc
    govde = kayit[1]["govde"].decode()
    assert "EDG-2026-997" in govde, "sahne belgeye girmedi — çivi hiçbir şey ölçmüyor (pozitif kontrol)"
    assert TENANT_ANAHTAR not in govde, "tenant anahtarı POST gövdesine SIZDI"
