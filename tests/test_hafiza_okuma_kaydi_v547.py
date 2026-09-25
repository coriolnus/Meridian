"""tests/test_hafiza_okuma_kaydi_v547.py — TSK-222: EDG-2026-103'ün ölçüm aletleri (ADIM-0 (b)/(d)).

NUMARA: `ls tests | grep _v547` boş (2026-09-25, Rol-1 brief'i ve bu ağaçta yeniden ölçüldü).

NE ÖLÇÜLÜR — üç alet, dört bölüm:
  A. `deploy/hindsight/sayfa_oku.sh` — A1 `~/bin`deki sürümsüz betiğin depoya alınmış hâli.
     DAVRANIŞ AYNI: çıktı biçimi, argümanlar, çıkış kodları birebir (CLAUDE.md §0 adım 5 ve §2 bu
     betiğe atıf yapıyor). Beklenen çıktılar A1 kopyasının kendi `print` biçimlerinden yazıldı;
     eski↔yeni bayt-bayt kıyası bir kez rapora konuldu (TSK-222 raporu §1).
  B. `deploy/hindsight/hafiza_sor.sh` — aynısı, recall tarafı.
  C. OKUMA KAYDI — iki betiğin tek eklemesi: her çağrı `HAFIZA_OKUMA_KAYDI` dosyasına TEK JSON
     satırı ekler. Kartın kill-list'i: yer tutucu/hata gövdesi OKUNDU sayılmaz (ayırt edilir),
     sır/kimlik değeri kayda düşerse akış KAPANIR. Kayıt yazılamazsa okuma YİNE çıkar ve bu
     stderr'e SÖYLENİR (Yasa 4).
  D. `ops/karar_envanteri.py` — kartın SAYAÇ-0'ı (D). Sentetik git geçmişi + ROADMAP + günlük +
     kart parçasıyla D'nin ve atıf türlerinin DOĞRU sayıldığı ölçülür; token fonksiyonu
     `kart_benzer.normalize_tokens`tan İTHAL edilir (kimlik eşitliğiyle, kopya değil).

SAHTE SUNUCU: betikler Hindsight'a `127.0.0.1:<port>` üzerinden gider; port ve anahtar dosyası
ortamdan ezilebilir (`HAFIZA_PORT`, `HAFIZA_ANAHTAR_DOSYASI`) — ana bilgisayar SABİT loopback'tir,
yani anahtar makineden hiçbir yapılandırmayla çıkamaz. Testteki anahtar SAHTEDİR ve ayırt edici bir
dizgedir; sır süzgeci çivisi onu kayıtta, stdout'ta ve stderr'de arar.

GERÇEK DEPOYA DOKUNULMAZ: envanter testleri `tmp_path` altında kendi git deposunu kurar ve aracı
`--repo` ile oraya yöneltir (her git çağrısında `cwd=` sentetik depodur).
"""
from __future__ import annotations

import hashlib
import http.server
import json
import os
import pathlib
import re
import shutil
import socket
import subprocess
import sys
import threading

import pytest

from tests.conftest import betikten_modul_yukle

KOK = pathlib.Path(__file__).resolve().parents[1]
SAYFA_OKU = KOK / "deploy" / "hindsight" / "sayfa_oku.sh"
HAFIZA_SOR = KOK / "deploy" / "hindsight" / "hafiza_sor.sh"
KAYIT_MODULU = KOK / "deploy" / "hindsight" / "hafiza_okuma_kaydi.py"
ENVANTER = KOK / "ops" / "karar_envanteri.py"
KART_BENZER = KOK / "ops" / "kart_benzer.py"

SAHTE_ANAHTAR = "TEST-ANAHTARI-sahte-degil-gercek-7Qx9Zk"
ALANLAR = ("v", "ts", "betik", "kip", "kimlik", "ad", "tazeleme", "bank", "butce", "http",
           "bayt", "sha256", "durum", "sonuc_n", "sure_s", "hata", "etiket")
TABAN_YOL = "/v1/default/banks/meridian-arsiv/mental-models"

SAYFALAR = [
    {"id": "mm-hedef", "name": "meridian-hedef-sapma", "content": "# Hedef\nSapma raporu gövdesi.",
     "last_refreshed_at": "2026-09-20T10:00:00+00:00", "bank_id": "meridian-arsiv"},
    {"id": "mm-pk", "name": "pk-pit-civisi", "version": 3, "content": "PK içerik",
     "last_refreshed_at": "2026-09-21T11:00:00+00:00"},
]
RECALL_YANIT = {"results": [
    {"document_id": "doc-1", "type": "world", "occurred_start": "2026-09-01",
     "scores": {"final": 0.9}, "text": "metin\nbir"},
    {"document_id": "doc-2", "type": "experience", "mentioned_at": "2026-09-02",
     "scores": {"rerank": 0.5}, "text": "iki"},
]}
SORU = "okuma kaydına metni yazılmaması gereken soru xyzzy"


def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


# ------------------------------------------------------------------------------------------------
# SAHTE HINDSIGHT
# ------------------------------------------------------------------------------------------------

@pytest.fixture
def sunucu():
    durum = {
        "sayfalar": [dict(s) for s in SAYFALAR],
        "kod": {"liste": 200, "tekil": 200, "recall": 200},
        "recall_yanit": json.loads(json.dumps(RECALL_YANIT)),
        "govdeler": {},
        "istekler": [],
        # İstek ANINDA (istemci süreci yanıtı beklerken) çağrılır; v552 (TSK-064) bu anda `ps`
        # görüntüsü alıp anahtarın hiçbir sürecin argv'sinde/ortamında olmadığını ölçer.
        "istek_kancasi": None,
    }

    class _Isleyici(http.server.BaseHTTPRequestHandler):
        def log_message(self, *a):  # sahte sunucu erişim satırlarını test çıktısına basmasın
            return

        def _gonder(self, kod, nesne):
            govde = json.dumps(nesne, ensure_ascii=False).encode("utf-8")
            durum["govdeler"][self.path] = govde
            self.send_response(kod)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(govde)))
            self.end_headers()
            self.wfile.write(govde)

        def _yetkili(self):
            return self.headers.get("Authorization") == "Bearer " + SAHTE_ANAHTAR

        def do_GET(self):
            durum["istekler"].append(("GET", self.path, self.headers.get("Authorization"), None))
            if durum["istek_kancasi"] is not None:
                durum["istek_kancasi"]()
            if not self._yetkili():
                return self._gonder(401, {"detail": "yetkisiz"})
            if self.path == TABAN_YOL:
                kod = durum["kod"]["liste"]
                return self._gonder(kod, {"items": durum["sayfalar"]} if kod == 200 else {"detail": "x"})
            if self.path.startswith(TABAN_YOL + "/"):
                kod = durum["kod"]["tekil"]
                if kod != 200:
                    return self._gonder(kod, {"detail": "x"})
                sid = self.path[len(TABAN_YOL) + 1:]
                s = next((x for x in durum["sayfalar"] if x["id"] == sid), None)
                return self._gonder(200 if s else 404, s or {"detail": "yok"})
            return self._gonder(404, {"detail": "yol yok"})

        def do_POST(self):
            n = int(self.headers.get("Content-Length") or 0)
            govde = self.rfile.read(n)
            durum["istekler"].append(("POST", self.path, self.headers.get("Authorization"), govde))
            if durum["istek_kancasi"] is not None:
                durum["istek_kancasi"]()
            if not self._yetkili():
                return self._gonder(401, {"detail": "yetkisiz"})
            if self.path.endswith("/memories/recall"):
                kod = durum["kod"]["recall"]
                return self._gonder(kod, durum["recall_yanit"] if kod == 200 else {"detail": "x"})
            return self._gonder(404, {"detail": "yol yok"})

    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _Isleyici)
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    durum["port"] = srv.server_address[1]
    try:
        yield durum
    finally:
        srv.shutdown()
        srv.server_close()


def _kapali_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def _ortam(tmp_path, port, kayit=None, **ek):
    anahtar = tmp_path / "anahtar"
    anahtar.write_text(SAHTE_ANAHTAR + "\n", encoding="utf-8")
    ortam = {k: v for k, v in os.environ.items() if not k.startswith("HAFIZA_")}
    ortam.update({
        "PATH": f"{pathlib.Path(sys.executable).parent}:/usr/bin:/bin",
        "HAFIZA_PORT": str(port),
        "HAFIZA_ANAHTAR_DOSYASI": str(anahtar),
        "HAFIZA_OKUMA_KAYDI": str(kayit if kayit is not None else tmp_path / "okuma.jsonl"),
    })
    ortam.update({k: str(v) for k, v in ek.items()})
    return ortam


def _kos(betik, *argv, ortam, dogrudan=False):
    komut = [str(betik), *argv] if dogrudan else ["/bin/bash", str(betik), *argv]
    return subprocess.run(komut, capture_output=True, text=True, env=ortam, timeout=120)


def _kayitlar(yol: pathlib.Path) -> list[dict]:
    if not yol.exists():
        return []
    return [json.loads(s) for s in yol.read_text(encoding="utf-8").splitlines() if s.strip()]


def _liste_beklenen(sayfalar) -> str:
    satirlar = [f"# zihin modelleri: {len(sayfalar)}"]
    for m in sayfalar:
        surum = m.get("version", m.get("current_version", "?"))
        satirlar.append(f"- {m['id']} · {m['name']} · v{surum} · {m.get('last_refreshed_at') or ''}")
    return "\n".join(satirlar) + "\n"


def _sayfa_beklenen(m) -> str:
    return (f"# {m['name']} · id={m['id']} · v{m.get('version', '?')} · "
            f"tazeleme={m.get('last_refreshed_at') or ''}\n{m['content']}\n")


# ================================================================================================
# A — sayfa_oku.sh DAVRANIŞI (A1 kopyasıyla birebir)
# ================================================================================================

def test_A1_liste_ciktisi_birebir(sunucu, tmp_path):
    r = _kos(SAYFA_OKU, ortam=_ortam(tmp_path, sunucu["port"]))
    assert r.returncode == 0, r.stderr
    assert r.stdout == _liste_beklenen(SAYFALAR)


def test_A2_sayfa_ada_gore_ciktisi_birebir(sunucu, tmp_path):
    r = _kos(SAYFA_OKU, "meridian-hedef-sapma", ortam=_ortam(tmp_path, sunucu["port"]))
    assert r.returncode == 0, r.stderr
    assert r.stdout == _sayfa_beklenen(SAYFALAR[0])


def test_A3_sayfa_id_ile_de_bulunur_ve_surum_basilir(sunucu, tmp_path):
    r = _kos(SAYFA_OKU, "mm-pk", ortam=_ortam(tmp_path, sunucu["port"]))
    assert r.returncode == 0, r.stderr
    assert r.stdout == _sayfa_beklenen(SAYFALAR[1])
    assert r.stdout.startswith("# pk-pit-civisi · id=mm-pk · v3 ·")


def test_A4_bulunamadi_cikis_2(sunucu, tmp_path):
    r = _kos(SAYFA_OKU, "yok-sayfa", ortam=_ortam(tmp_path, sunucu["port"]))
    assert r.returncode == 2
    assert r.stdout == "BULUNAMADI: yok-sayfa\n"


def test_A5_bos_icerik_alan_adlarini_basar(sunucu, tmp_path):
    bos = {"id": "mm-bos", "name": "bos-sayfa", "content": "", "last_refreshed_at": None}
    sunucu["sayfalar"].append(bos)
    r = _kos(SAYFA_OKU, "bos-sayfa", ortam=_ortam(tmp_path, sunucu["port"]))
    assert r.returncode == 0, r.stderr
    assert r.stdout == ("# bos-sayfa · id=mm-bos · v? · tazeleme=\n"
                        "(içerik boş) alanlar: id, name, content, last_refreshed_at\n")


def test_A6_http_500_cikis_1_stdout_bos(sunucu, tmp_path):
    sunucu["kod"]["liste"] = 500
    r = _kos(SAYFA_OKU, "meridian-hedef-sapma", ortam=_ortam(tmp_path, sunucu["port"]))
    assert r.returncode == 1
    assert r.stdout == ""
    assert "HTTPError" in r.stderr


def test_A7_anahtar_dosyasi_yoksa_cikis_1_ve_istek_gitmez(sunucu, tmp_path):
    ortam = _ortam(tmp_path, sunucu["port"])
    ortam["HAFIZA_ANAHTAR_DOSYASI"] = str(tmp_path / "yok.key")
    r = _kos(SAYFA_OKU, ortam=ortam)
    assert r.returncode == 1
    assert r.stdout == ""
    assert sunucu["istekler"] == []


def test_A8_port_sayi_degilse_cikis_1_ve_istek_gitmez(sunucu, tmp_path):
    """Ana bilgisayar SABİT loopback'tir; port ezmesi URL'ye taşınan bir enjeksiyon olamaz
    (`8888@baska.host` biçimi ana bilgisayarı değiştirirdi)."""
    for betik, argv in ((SAYFA_OKU, ()), (HAFIZA_SOR, (SORU,))):
        ortam = _ortam(tmp_path, f"{sunucu['port']}@baska.ornek")
        r = _kos(betik, *argv, ortam=ortam)
        assert r.returncode == 1, (betik.name, r.stdout, r.stderr)
        assert "HAFIZA_PORT" in r.stderr
        assert r.stdout == ""
    assert sunucu["istekler"] == []


def test_A9_betikler_calistirilabilir_ve_sembolik_bagla_calisir(sunucu, tmp_path):
    """Operatörün koştuğu BİÇİM: A1'de `~/bin/sayfa_oku.sh` depodaki dosyaya sembolik bağdır ve
    doğrudan çağrılır (`bash` önekiyle değil)."""
    kutu = tmp_path / "bin"
    kutu.mkdir()
    for betik in (SAYFA_OKU, HAFIZA_SOR):
        assert os.access(betik, os.X_OK), f"{betik.name} çalıştırılabilir değil"
        (kutu / betik.name).symlink_to(betik)
    kayit = tmp_path / "okuma.jsonl"
    ortam = _ortam(tmp_path, sunucu["port"], kayit=kayit)
    r1 = _kos(kutu / "sayfa_oku.sh", "meridian-hedef-sapma", ortam=ortam, dogrudan=True)
    r2 = _kos(kutu / "hafiza_sor.sh", SORU, ortam=ortam, dogrudan=True)
    assert r1.returncode == 0 and r2.returncode == 0, (r1.stderr, r2.stderr)
    assert r1.stdout == _sayfa_beklenen(SAYFALAR[0])
    assert [k["betik"] for k in _kayitlar(kayit)] == ["sayfa_oku", "hafiza_sor"], \
        "sembolik bağ üzerinden çağrıda kayıt modülü bulunamadı"


# ================================================================================================
# B — hafiza_sor.sh DAVRANIŞI
# ================================================================================================

RECALL_DESENI = re.compile(
    r"\A# recall · bank=meridian-arsiv · butce=mid · k=5 · \d+\.\d s · sonuç 2\n"
    r"\n\[1\] doc-1 · world · 2026-09-01 · skor=0\.9\n    metin bir\n"
    r"\n\[2\] doc-2 · experience · 2026-09-02 · skor=0\.5\n    iki\n\Z")


def test_B1_recall_ciktisi_birebir(sunucu, tmp_path):
    r = _kos(HAFIZA_SOR, SORU, ortam=_ortam(tmp_path, sunucu["port"]))
    assert r.returncode == 0, r.stderr
    assert RECALL_DESENI.match(r.stdout), r.stdout


def test_B2_k_ve_bank_ve_butce_argumanlari(sunucu, tmp_path):
    r = _kos(HAFIZA_SOR, SORU, "1", "baska-bank", "low", ortam=_ortam(tmp_path, sunucu["port"]))
    assert r.returncode == 0, r.stderr
    assert r.stdout.startswith("# recall · bank=baska-bank · butce=low · k=1 · ")
    assert "[1] doc-1" in r.stdout and "[2]" not in r.stdout
    yontem, yol, yetki, govde = sunucu["istekler"][-1]
    assert (yontem, yol) == ("POST", "/v1/default/banks/baska-bank/memories/recall")
    assert yetki == "Bearer " + SAHTE_ANAHTAR
    assert json.loads(govde) == {"query": SORU, "budget": "low"}


def test_B3_soru_yoksa_cikis_1(sunucu, tmp_path):
    r = _kos(HAFIZA_SOR, ortam=_ortam(tmp_path, sunucu["port"]))
    assert r.returncode == 1
    assert "soru gerekli" in r.stderr
    assert sunucu["istekler"] == []


def test_B4_http_hatasi_cikis_2_ve_recall_hatasi_satiri(sunucu, tmp_path):
    sunucu["kod"]["recall"] = 500
    r = _kos(HAFIZA_SOR, SORU, ortam=_ortam(tmp_path, sunucu["port"]))
    assert r.returncode == 2
    assert r.stdout == "RECALL HATASI: HTTPError: HTTP Error 500: Internal Server Error\n"


# ================================================================================================
# C — OKUMA KAYDI
# ================================================================================================

def test_C1_sayfa_okumasi_tek_satir_tum_alanlar(sunucu, tmp_path):
    kayit = tmp_path / "okuma.jsonl"
    r = _kos(SAYFA_OKU, "meridian-hedef-sapma", ortam=_ortam(tmp_path, sunucu["port"], kayit))
    assert r.returncode == 0, r.stderr
    satirlar = _kayitlar(kayit)
    assert len(satirlar) == 1
    k = satirlar[0]
    assert tuple(sorted(k)) == tuple(sorted(ALANLAR)), sorted(k)
    icerik = SAYFALAR[0]["content"].encode("utf-8")
    assert k["v"] == 1
    assert re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ", k["ts"]), k["ts"]
    assert (k["betik"], k["kip"], k["kimlik"], k["ad"]) == (
        "sayfa_oku", "sayfa", "mm-hedef", "meridian-hedef-sapma")
    assert k["tazeleme"] == SAYFALAR[0]["last_refreshed_at"]
    assert (k["http"], k["bayt"], k["sha256"]) == (200, len(icerik), _sha(icerik))
    assert k["durum"] == "gercek"
    assert isinstance(k["sure_s"], float) and 0 <= k["sure_s"] < 60
    assert (k["bank"], k["butce"], k["sonuc_n"], k["hata"], k["etiket"]) == (None,) * 5


def test_C2_liste_kaydi_ham_govdeyi_olcer(sunucu, tmp_path):
    kayit = tmp_path / "okuma.jsonl"
    _kos(SAYFA_OKU, ortam=_ortam(tmp_path, sunucu["port"], kayit))
    (k,) = _kayitlar(kayit)
    ham = sunucu["govdeler"][TABAN_YOL]
    assert (k["kip"], k["kimlik"], k["sonuc_n"], k["durum"]) == ("liste", None, 2, "gercek")
    assert (k["http"], k["bayt"], k["sha256"]) == (200, len(ham), _sha(ham))


def test_C3_recall_kaydi_soru_metnini_yazmaz_ozetini_yazar(sunucu, tmp_path):
    kayit = tmp_path / "okuma.jsonl"
    _kos(HAFIZA_SOR, SORU, ortam=_ortam(tmp_path, sunucu["port"], kayit))
    (k,) = _kayitlar(kayit)
    ham = sunucu["govdeler"]["/v1/default/banks/meridian-arsiv/memories/recall"]
    assert k["kimlik"] == "sha256:" + _sha(SORU.encode("utf-8"))
    assert (k["betik"], k["kip"], k["bank"], k["butce"]) == ("hafiza_sor", "recall", "meridian-arsiv", "mid")
    assert (k["http"], k["bayt"], k["sha256"], k["sonuc_n"], k["durum"]) == (
        200, len(ham), _sha(ham), 2, "gercek")
    ham_metin = kayit.read_text(encoding="utf-8")
    assert SORU not in ham_metin and "xyzzy" not in ham_metin


def test_C4_her_cagri_bir_satir_ekler(sunucu, tmp_path):
    kayit = tmp_path / "okuma.jsonl"
    ortam = _ortam(tmp_path, sunucu["port"], kayit)
    _kos(SAYFA_OKU, ortam=ortam)
    _kos(SAYFA_OKU, "mm-pk", ortam=ortam)
    _kos(HAFIZA_SOR, SORU, ortam=ortam)
    assert [(k["betik"], k["kip"]) for k in _kayitlar(kayit)] == [
        ("sayfa_oku", "liste"), ("sayfa_oku", "sayfa"), ("hafiza_sor", "recall")]


@pytest.mark.parametrize("icerik,tazeleme", [
    ("Generating content...", "2026-09-20T10:00:00+00:00"),
    ("Generating content…\n", "2026-09-20T10:00:00+00:00"),
    ("Gerçek görünen içerik", None),
])
def test_C5_yer_tutucu_okundu_sayilmaz(sunucu, tmp_path, icerik, tazeleme):
    sunucu["sayfalar"].append({"id": "mm-yt", "name": "yt", "content": icerik,
                               "last_refreshed_at": tazeleme})
    kayit = tmp_path / "okuma.jsonl"
    r = _kos(SAYFA_OKU, "yt", ortam=_ortam(tmp_path, sunucu["port"], kayit))
    assert r.returncode == 0
    (k,) = _kayitlar(kayit)
    assert k["durum"] == "yer_tutucu", k
    assert k["sha256"] == _sha(icerik.encode("utf-8"))


def test_C6_bos_bulunamadi_ve_hata_siniflari(sunucu, tmp_path):
    kayit = tmp_path / "okuma.jsonl"
    ortam = _ortam(tmp_path, sunucu["port"], kayit)
    sunucu["sayfalar"].append({"id": "mm-bos", "name": "bos", "content": "",
                               "last_refreshed_at": None})
    _kos(SAYFA_OKU, "bos", ortam=ortam)
    _kos(SAYFA_OKU, "yok-sayfa", ortam=ortam)
    sunucu["kod"]["tekil"] = 503
    _kos(SAYFA_OKU, "meridian-hedef-sapma", ortam=ortam)
    sunucu["kod"]["recall"] = 500
    _kos(HAFIZA_SOR, SORU, ortam=ortam)
    kapali = _ortam(tmp_path, _kapali_port(), kayit)
    rk = _kos(HAFIZA_SOR, SORU, ortam=kapali)
    assert rk.returncode == 2 and rk.stdout.startswith("RECALL HATASI: URLError: ")
    bos, yok, hata_sayfa, hata_recall, baglanti = _kayitlar(kayit)
    assert (bos["durum"], bos["bayt"], bos["kimlik"]) == ("bos", 0, "mm-bos")
    assert (yok["durum"], yok["http"]) == ("bulunamadi", 200)
    assert yok["kimlik"] == "sha256:" + _sha(b"yok-sayfa")
    assert (hata_sayfa["durum"], hata_sayfa["http"], hata_sayfa["hata"], hata_sayfa["kimlik"]) == (
        "hata", 503, "HTTPError", "mm-hedef")
    assert (hata_recall["durum"], hata_recall["http"], hata_recall["hata"]) == ("hata", 500, "HTTPError")
    assert (baglanti["durum"], baglanti["http"], baglanti["hata"]) == ("hata", None, "URLError")


def test_C7_kayit_dizini_yoksa_okuma_yine_cikar_ve_stderr_soyler(sunucu, tmp_path):
    kayit = tmp_path / "olmayan" / "dizin" / "okuma.jsonl"
    ortam = _ortam(tmp_path, sunucu["port"], kayit)
    r1 = _kos(SAYFA_OKU, "meridian-hedef-sapma", ortam=ortam)
    r2 = _kos(HAFIZA_SOR, SORU, ortam=ortam)
    assert (r1.returncode, r2.returncode) == (0, 0)
    assert r1.stdout == _sayfa_beklenen(SAYFALAR[0])
    assert RECALL_DESENI.match(r2.stdout), r2.stdout
    for r in (r1, r2):
        assert "UYARI: okuma kaydı yazılamadı" in r.stderr and str(kayit) in r.stderr, r.stderr
    assert not kayit.parent.exists(), "betik kayıt dizinini KENDİSİ yaratmamalı (kurulum Rol-1'in)"


def test_C8_anahtar_ve_url_hicbir_yola_sizmaz(sunucu, tmp_path):
    kayit = tmp_path / "okuma.jsonl"
    ortam = _ortam(tmp_path, sunucu["port"], kayit)
    cagrilar = [(SAYFA_OKU, ()), (SAYFA_OKU, ("meridian-hedef-sapma",)), (SAYFA_OKU, ("yok",)),
                (HAFIZA_SOR, (SORU,))]
    ciktilar = [_kos(b, *a, ortam=ortam) for b, a in cagrilar]
    sunucu["kod"].update(liste=500, tekil=500, recall=401)
    ciktilar += [_kos(b, *a, ortam=ortam) for b, a in cagrilar]
    kapali = _ortam(tmp_path, _kapali_port(), kayit)
    ciktilar += [_kos(b, *a, ortam=kapali) for b, a in cagrilar]
    yanlis = tmp_path / "yanlis.key"
    yanlis.write_text("baska-" + SAHTE_ANAHTAR, encoding="utf-8")
    yetkisiz = dict(ortam, HAFIZA_ANAHTAR_DOSYASI=str(yanlis))
    sunucu["kod"].update(liste=200, tekil=200, recall=200)
    ciktilar += [_kos(b, *a, ortam=yetkisiz) for b, a in cagrilar]
    ham = kayit.read_text(encoding="utf-8")
    assert len(_kayitlar(kayit)) == 16
    for metin in [ham] + [r.stdout for r in ciktilar] + [r.stderr for r in ciktilar]:
        assert SAHTE_ANAHTAR not in metin
    assert "Bearer" not in ham and "http://" not in ham and "127.0.0.1" not in ham
    assert "401" in {str(k["http"]) for k in _kayitlar(kayit)}


def test_C9_etiket_yalniz_bicimli_deger_yazilir(sunucu, tmp_path):
    kayit = tmp_path / "okuma.jsonl"
    r1 = _kos(SAYFA_OKU, "mm-pk", ortam=_ortam(tmp_path, sunucu["port"], kayit,
                                               HAFIZA_OKUMA_ETIKET="pk"))
    r2 = _kos(SAYFA_OKU, "mm-pk", ortam=_ortam(tmp_path, sunucu["port"], kayit,
                                               HAFIZA_OKUMA_ETIKET="PK deneme; sil"))
    assert r1.returncode == r2.returncode == 0
    iyi, kotu = _kayitlar(kayit)
    assert iyi["etiket"] == "pk"
    assert kotu["etiket"] == "gecersiz"
    assert "PK deneme" not in kayit.read_text(encoding="utf-8")
    assert "UYARI" in r2.stderr and "HAFIZA_OKUMA_ETIKET" in r2.stderr


def test_C10_kayit_modulu_yoksa_okuma_kayitsiz_surer_ve_soyler(sunucu, tmp_path):
    """Betik ~/bin'e sembolik bağ yerine KOPYA olarak kurulursa modülü yanında bulamaz: okuma
    yine çıkar, bunun kaydedilmediği stderr'e yazılır (sessiz körlük yok)."""
    tek = tmp_path / "tek"
    tek.mkdir()
    for betik in (SAYFA_OKU, HAFIZA_SOR):
        shutil.copy2(betik, tek / betik.name)
    kayit = tmp_path / "okuma.jsonl"
    ortam = _ortam(tmp_path, sunucu["port"], kayit)
    r1 = _kos(tek / "sayfa_oku.sh", "meridian-hedef-sapma", ortam=ortam)
    r2 = _kos(tek / "hafiza_sor.sh", SORU, ortam=ortam)
    assert (r1.returncode, r2.returncode) == (0, 0)
    assert r1.stdout == _sayfa_beklenen(SAYFALAR[0])
    for r in (r1, r2):
        assert "UYARI: okuma kaydı modülü yüklenemedi" in r.stderr, r.stderr
    assert not kayit.exists()


def test_C13_cikti_borusu_erken_kapansa_da_okuma_kaydedilir(sunucu, tmp_path):
    """Rol-1 çıktıyı `| head` ile kısaltabilir. Gövde boru + stdio tamponunu aşınca (sayfalar 8-12 bin
    karakter) `print` EPIPE ile düşer; kayıt yazdırmadan SONRA olsaydı okuma kayıttan sessizce
    kaybolurdu. Kayıt, çıktı basılmadan ÖNCE yazılır (çıktı biçimi ve çıkış kodu değişmez)."""
    sunucu["sayfalar"].append({"id": "mm-buyuk", "name": "buyuk", "content": "satır\n" * 60000,
                               "last_refreshed_at": "2026-09-20T10:00:00+00:00"})
    sunucu["recall_yanit"] = {"results": [{"document_id": f"d{i}", "type": "world",
                                           "text": "x" * 600} for i in range(300)]}
    kayit = tmp_path / "okuma.jsonl"
    ortam = _ortam(tmp_path, sunucu["port"], kayit)
    for betik, argv in ((SAYFA_OKU, ["buyuk"]), (SAYFA_OKU, []), (HAFIZA_SOR, [SORU, "300"])):
        subprocess.run(["/bin/bash", "-c", '"$0" "$@" | head -1', str(betik), *argv],
                       capture_output=True, text=True, env=ortam, timeout=120)
    assert [(k["kip"], k["durum"]) for k in _kayitlar(kayit)] == [
        ("sayfa", "gercek"), ("liste", "gercek"), ("recall", "gercek")]


def test_C11_kayit_yazimi_TEK_modulde_yasar():
    """Tek-kaynak: iki betik kaydı AYNI modülle yazar; betiklerin kendisinde ikinci bir yazar
    (dosya açan kod) ya da ikinci bir yer tutucu tanımı yoktur."""
    for betik in (SAYFA_OKU, HAFIZA_SOR):
        metin = betik.read_text(encoding="utf-8")
        assert "import hafiza_okuma_kaydi" in metin, betik.name
        assert not re.search(r"(?<![\w.])open\(", metin), \
            f"{betik.name} kendi dosyasını açıyor (ikinci yazar)"
        assert "Generating" not in metin, f"{betik.name} yer tutucu tanımını kopyalıyor"
    mod = betikten_modul_yukle(KAYIT_MODULU, ad="hafiza_okuma_kaydi_v547")
    assert mod.VARSAYILAN_YOL == "/opt/veri/olcum/edg103/okuma.jsonl"
    assert mod.ALANLAR == ALANLAR


def test_C12_modul_yer_tutucu_siniflamasi_dogrudan():
    mod = betikten_modul_yukle(KAYIT_MODULU, ad="hafiza_okuma_kaydi_v547b")
    t = "2026-09-20T10:00:00+00:00"
    assert mod.sayfa_durumu("Gerçek metin", t) == "gercek"
    assert mod.sayfa_durumu("", t) == "bos"
    assert mod.sayfa_durumu("   \n", None) == "bos"
    assert mod.sayfa_durumu("generating CONTENT", t) == "yer_tutucu"
    assert mod.sayfa_durumu("Generating content... ama devamı var", t) == "gercek"
    assert mod.sayfa_durumu("Gerçek metin", "") == "yer_tutucu"


# ================================================================================================
# D — KARAR ENVANTERİ (ops/karar_envanteri.py)
# ================================================================================================

ROADMAP_SENTETIK = """# ROADMAP
## §2 TAHTA
**[TSK-901] Deneme kalemi bir** — status: DONE(2026-09-20·abc1234) · born: 2026-09-10 · owner: rol1 · size: S · trigger: —
  What: (2026-09-20 KAPANDI — hafıza: recall 3 sonuç, doğrudan kayıt yok) eski not (2026-09-12 açıldı; hafıza: memory `eski-not-burada`).
  Why: gerekçe.
  Ref: PRG-06
**[TSK-902] Deneme kalemi iki** — status: DROPPED(2026-09-21·ölçüm: gereksiz) · born: 2026-09-10 · owner: rol1 · size: S · trigger: —
  What: (2026-09-21 düştü — hafıza: benzer kayıt yok) ayrıntı.
**[TSK-903] Pencere dışı kalem** — status: DONE(2026-09-10·def5678) · born: 2026-09-01 · owner: rol1 · size: S · trigger: —
  What: (2026-09-10 KAPANDI) x.
**[TSK-904] Aktif kalem** — status: ACTIVE · born: 2026-09-01 · owner: rol1 · size: S · trigger: —
  What: (2026-09-22 ölçüm notu — sayaç 3/5; hafıza: recall 2 sonuç) aktif.
**[TSK-912] Destekli kalem** — status: ACTIVE · born: 2026-09-22 · owner: rol1 · size: S · trigger: —
  What: (2026-09-22 11:0xZ HAFIZA ATFI [CLAUDE.md §2 kapısı, geç — karar 10:0xZ'de atıfsız]: ornek-dort-not emsali) (2026-09-22 ÖLÇÜM [Rol-1] — Kaynak: hafıza: benzer kayıt yok (recall 10:0xZ)) açıklama.
**[TSK-913] Notta karar** — status: GATED · born: 2026-09-20 · owner: rol1 · size: S · trigger: —
  What: (2026-09-23 OPERATÖR KARARI: bekleyecek — hafıza: memory `ornek-iki-not`) (2026-09-20 açıldı) açıklama.
## §6 KANIT/KARTLAR
- **[EDG-2026-901] ornek-kart** — status: DONE(2026-09-22·KALDI) · owner: rol1 · size: S · trigger: —
## §7 KARAR GÜNLÜĞÜ
"""

GUNLUK_SENTETIK = """# Günlük
### 2026-09-17 akşam (Rol-1) — pencere öncesi
- **OPERATÖR KARARI:** pencere dışı karar.
### 2026-09-19 sabah (Rol-1) — deneme oturumu
- **OPERATÖR KARARI:** zaman aşımı 30 s kalır (hafıza: memory `ornek-hafiza-notu`).
- sıradan bir satır, karar içermez.
- **Suite #5:** 100 passed — üçlü hüküm: yeşil.
- **HÜKÜM:** yük-flake, tekrar koşulmadı.
### 3. EDG-2026-901 HÜKMÜ — KALDI (2026-09-22 10:00Z)
Karar paragrafı; kaynak: zihin modeli meridian-hedef-sapma v?.
### 2026-09-26 — pencere sonrası
- **OPERATÖR KARARI:** pencere sonrası.
"""

KART_SENTETIK = """# EDG-2026-901 — örnek kart
# HAFIZA KONTROLÜ (2026-09-18 09:0xZ, ön-kayıttan önce): A1 `hafiza_sor.sh` recall ("örnek soru") → kayıt yok;
# `ops/kart_benzer.py --hipotez "örnek"` → benzer yok.
card_id: EDG-2026-901
status: measured
family: ornek
on_kayit: 2026-09-18
hipotez: >
  örnek hipotez metni
hukum_2026_09_22: >
  KALDI — eşik tutmadı (kaynak: memory ornek-not-bir).
hukum_A: >
  tarihsiz eski hüküm.
"""

SIR_BENZERI = "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0"

COMMITLER = [  # (committer tarihi, mesaj)
    ("2026-09-17T23:59:59+00:00", "TSK-905 KARAR: pencere öncesi"),
    ("2026-09-18T00:00:00+00:00", "TSK-906 → ACTIVE: yeni iş açıldı"),
    ("2026-09-20T12:00:00+03:00", "ROADMAP: TSK-901 KAPANDI"),
    ("2026-09-22T08:00:00+00:00", "EDG-901 HÜKÜM: KALDI"),
    ("2026-09-23T10:00:00+00:00", "TSK-907: kod dilimi, çivi v999"),
    ("2026-09-23T11:00:00+00:00", "Günlük §5: operatör kararı işlendi"),
    ("2026-09-24T23:59:59+00:00", "CLAUDE.md §6: kural değişti\n\nkaynak: recall 'x kuralı'"),
    ("2026-09-25T00:00:00+00:00", "TSK-908 DROPPED: gereksiz"),
    ("2026-09-21T02:00:00+03:00", "TSK-909 Rol-1 ruling: pay reddedildi\n\nhafıza: TSK-196 kök neden sınıflaması"),
    ("2026-09-23T12:00:00+00:00", f"TSK-910 KARAR: anahtar {SIR_BENZERI} döndü"),
    # Kuralın BİÇİMİNİ alıntılayan karar atıf DEĞİLDİR (kuru koşumda EDG-089 hükmü böyle sahte
    # 'sayfa' sayıldı, 2026-09-25): tırnak/backtick içindeki "kaynak: …" biçim alıntısıdır.
    ("2026-09-23T13:00:00+00:00", "TSK-911 KARAR: hiçbir karara `kaynak: zihin modeli <ad> v<n>` "
                                  "ya da 'kaynak: recall' atfı yazılmadı"),
    # Atıf karar metninde değil, AYNI GÜN aynı kalemin ROADMAP notunda (Rol-1'in 2026-09-24'ten beri
    # yazdığı yer): not işaretsizdir → karar DOĞURMAZ, yalnız bu karara DESTEK olarak eklenir.
    ("2026-09-22T09:00:00+00:00", "TSK-912 → ACTIVE: yeni kalem"),
    # İşaretsiz commit aynı gün aynı kimlikli karara destek olur (gövdesindeki atıf sayılır).
    ("2026-09-18T05:00:00+00:00", "TSK-906: kod dilimi\n\nhafıza: memory `ornek-uc-not`"),
]

BEKLENEN = {  # (tarih, kimlik) → atıf türleri
    ("2026-09-18", "TSK-906"): ["memory"],
    ("2026-09-18", "EDG-2026-901"): ["kart_benzer", "recall"],
    ("2026-09-19", None, "OPERATÖR KARARI"): ["memory"],
    ("2026-09-19", None, "HÜKÜM"): [],
    ("2026-09-20", "TSK-901"): ["recall"],
    ("2026-09-20", "TSK-909"): ["diger"],
    ("2026-09-21", "TSK-902"): ["bos_beyan"],
    ("2026-09-22", "EDG-2026-901"): ["memory", "sayfa"],
    ("2026-09-23", "TSK-910"): [],
    ("2026-09-23", "TSK-911"): [],
    ("2026-09-22", "TSK-912"): ["memory", "recall"],
    ("2026-09-23", "TSK-913"): ["memory"],
    ("2026-09-24", None, "CLAUDE.md"): ["recall"],
}


def _git(depo, *args, tarih=None):
    ortam = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    ortam.update({"GIT_AUTHOR_NAME": "Sahne", "GIT_AUTHOR_EMAIL": "sahne@ornek.gecersiz",
                  "GIT_COMMITTER_NAME": "Sahne", "GIT_COMMITTER_EMAIL": "sahne@ornek.gecersiz"})
    if tarih:
        ortam.update({"GIT_AUTHOR_DATE": tarih, "GIT_COMMITTER_DATE": tarih})
    return subprocess.run(["git", *args], cwd=str(depo), env=ortam, capture_output=True,
                          text=True, check=True, timeout=120)


@pytest.fixture
def sentetik_depo(tmp_path):
    depo = tmp_path / "depo"
    (depo / "research" / "cards").mkdir(parents=True)
    _git(depo, "init", "-q", "-b", "main")
    (depo / "ROADMAP.md").write_text(ROADMAP_SENTETIK, encoding="utf-8")
    (depo / "MERIDIAN_ENGINEERING_LOG.md").write_text(GUNLUK_SENTETIK, encoding="utf-8")
    (depo / "research" / "cards" / "EDG-2026-901-ornek-kart.yaml").write_text(
        KART_SENTETIK, encoding="utf-8")
    for i, (tarih, mesaj) in enumerate(COMMITLER):
        (depo / f"dosya{i}.txt").write_text(str(i), encoding="utf-8")
        _git(depo, "add", f"dosya{i}.txt")
        _git(depo, "commit", "-q", "-m", mesaj, tarih=tarih)
    return depo


def _envanter(depo, *ek, baslangic="2026-09-18", bitis="2026-09-24", cwd=None):
    return subprocess.run(
        [sys.executable, str(ENVANTER), "--repo", str(depo), "--baslangic", baslangic,
         "--bitis", bitis, *ek], capture_output=True, text=True, timeout=120,
        cwd=str(cwd or depo))


def _envanter_json(depo, tmp_path):
    cikti = tmp_path / "envanter.json"
    r = _envanter(depo, "--cikti", str(cikti))
    assert r.returncode == 0, r.stderr
    return json.loads(cikti.read_text(encoding="utf-8")), r


def _anahtar(k):
    if k["kimlik"] is None:
        for ipucu in ("OPERATÖR KARARI", "HÜKÜM", "CLAUDE.md"):
            if ipucu in k["baslik"]:
                return (k["tarih"], None, ipucu)
    return (k["tarih"], k["kimlik"])


def test_D1_sentetik_depoda_D_ve_atif_turleri_dogru(sentetik_depo, tmp_path):
    veri, r = _envanter_json(sentetik_depo, tmp_path)
    bulunan = {_anahtar(k): k["atif_turleri"] for k in veri["kararlar"]}
    assert bulunan == BEKLENEN
    assert veri["D"] == 13
    assert veri["atif_dagilimi"] == {"atifli": 10, "yok": 3, "sayfa": 1, "recall": 4, "memory": 5,
                                    "kart_benzer": 1, "bos_beyan": 1, "diger": 1}
    for k in veri["kararlar"]:
        assert k["atif_var"] is bool(k["atif_turleri"])
    assert veri["pencere"] == {"baslangic": "2026-09-18", "bitis": "2026-09-24", "saat_dilimi": "UTC"}
    assert r.stdout.strip().startswith("D=13 · atıflı 10 · yok 3")


def test_D2_ayni_gun_ayni_kimlik_kaynaklari_birlestirir(sentetik_depo, tmp_path):
    veri, _ = _envanter_json(sentetik_depo, tmp_path)
    (k,) = [k for k in veri["kararlar"] if (k["tarih"], k["kimlik"]) == ("2026-09-22", "EDG-2026-901")]
    assert sorted(x["tur"] for x in k["kaynaklar"]) == ["git", "gunluk", "kart", "roadmap"]
    (t,) = [k for k in veri["kararlar"] if k["kimlik"] == "TSK-901"]
    assert {x["tur"] for x in t["kaynaklar"]} == {"git", "roadmap"}
    assert veri["kaynak_kayit_sayilari"] == {"git": 8, "roadmap": 5, "kart": 2, "gunluk": 3}


def test_D2b_isaretsiz_kayit_yalniz_DESTEK_olur_karar_dogurmaz(sentetik_depo, tmp_path):
    veri, _ = _envanter_json(sentetik_depo, tmp_path)
    kimlikler = {k["kimlik"] for k in veri["kararlar"]}
    assert "TSK-904" not in kimlikler, "işaretsiz ROADMAP notu tek başına karar doğurdu"
    (t912,) = [k for k in veri["kararlar"] if k["kimlik"] == "TSK-912"]
    destekler = [x for x in t912["kaynaklar"] if x.get("destek")]
    assert [x["tur"] for x in destekler] == ["roadmap", "roadmap"]
    assert "benzer" not in t912["konu_tokenleri"], "destek metni konu tokenlarına karıştı"
    (t906,) = [k for k in veri["kararlar"] if k["kimlik"] == "TSK-906"]
    assert [x["tur"] for x in t906["kaynaklar"] if x.get("destek")] == ["git"]
    assert veri["destek_eklenen"] == 4


def test_D3_pencere_sinirlari_UTC_ve_haric_siniflar(sentetik_depo, tmp_path):
    veri, _ = _envanter_json(sentetik_depo, tmp_path)
    kimlikler = {k["kimlik"] for k in veri["kararlar"]}
    assert "TSK-905" not in kimlikler and "TSK-908" not in kimlikler, "pencere sınırı taşıyor"
    assert "TSK-903" not in kimlikler and "TSK-904" not in kimlikler
    assert "TSK-907" not in kimlikler, "işaretsiz kod commit'i karar sayıldı"
    (t909,) = [k for k in veri["kararlar"] if k["kimlik"] == "TSK-909"]
    assert t909["tarih"] == "2026-09-20", "+03:00 commit UTC'ye çevrilmedi"
    basliklar = " ".join(k["baslik"] for k in veri["kararlar"])
    assert "Günlük §5" not in basliklar, "günlük commit'i ikinci kez sayıldı"
    assert "üçlü hüküm" not in basliklar and "Suite #5" not in basliklar
    assert "pencere dışı" not in basliklar and "pencere sonrası" not in basliklar


def test_D4_tarihsiz_kart_hukmu_uydurulmaz_sayilir(sentetik_depo, tmp_path):
    veri, _ = _envanter_json(sentetik_depo, tmp_path)
    assert veri["tarihsiz_atlanan"] == {"kart": 1}
    assert all(k["tarih"] for k in veri["kararlar"])


def test_D5_konu_tokenleri_kart_benzer_ile_ve_sir_benzeri_atilir(sentetik_depo, tmp_path):
    kb = betikten_modul_yukle(KART_BENZER, ad="kart_benzer_v547")
    veri, _ = _envanter_json(sentetik_depo, tmp_path)
    (t,) = [k for k in veri["kararlar"] if k["kimlik"] == "TSK-910"]
    (mesaj,) = [m for _t, m in COMMITLER if m.startswith("TSK-910")]
    beklenen = sorted(kb.normalize_tokens(mesaj) - {SIR_BENZERI})
    assert t["konu_tokenleri"] == beklenen
    assert SIR_BENZERI not in json.dumps(veri, ensure_ascii=False)
    assert veri["sir_benzeri_atilan"] >= 1


def test_D6_kart_benzer_fonksiyonu_ITHAL_kopya_yok():
    kaynak = ENVANTER.read_text(encoding="utf-8")
    assert re.search(r"^(from kart_benzer import|import kart_benzer)", kaynak, re.M), \
        "kart_benzer ithal edilmiyor"
    assert not re.search(r"^def (normalize_tokens|skorla)\b", kaynak, re.M), "fonksiyon KOPYALANMIŞ"
    r = subprocess.run(
        [sys.executable, "-B", "-c",
         "import sys; sys.path.insert(0, sys.argv[1]); import karar_envanteri as k, kart_benzer as b; "
         "print(k.normalize_tokens is b.normalize_tokens)", str(KOK / "ops")],
        capture_output=True, text=True, timeout=60, cwd=str(KOK))
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip() == "True"


def test_D7_meridian_ithal_edilmez(sentetik_depo):
    kaynak = ENVANTER.read_text(encoding="utf-8")
    assert not re.search(r"^\s*(import meridian|from meridian)", kaynak, re.M)
    r = subprocess.run(
        [sys.executable, "-X", "importtime", str(ENVANTER), "--repo", str(sentetik_depo),
         "--baslangic", "2026-09-18", "--bitis", "2026-09-24"],
        capture_output=True, text=True, timeout=120, cwd=str(sentetik_depo))
    assert r.returncode == 0, r.stderr
    yuklenen = {s.split("|")[-1].strip() for s in r.stderr.splitlines() if "import time:" in s}
    assert not [m for m in yuklenen if m == "meridian" or m.startswith("meridian.")]
    assert json.loads(r.stdout)["D"] == 13, "--cikti yokken stdout JSON olmalı"


@pytest.mark.parametrize("bas,bit", [("2026-09-31", "2026-10-01"), ("2026-09-24", "2026-09-18"),
                                     ("dün", "2026-09-24")])
def test_D8_gecersiz_pencere_cikis_2(sentetik_depo, bas, bit):
    """Çıkış 2 TEK BAŞINA kanıt değil: Python eksik betikte de 2 döner (kırmızı turda bu çivi o
    yüzden sahte-yeşildi) — aracın KENDİ hata satırı aranır."""
    r = _envanter(sentetik_depo, baslangic=bas, bitis=bit)
    assert r.returncode == 2, (r.stdout, r.stderr)
    assert r.stdout == ""
    assert "HATA: pencere" in r.stderr, r.stderr


def test_D9_kaynak_okunamazsa_eksik_D_basilmaz(sentetik_depo):
    (sentetik_depo / "MERIDIAN_ENGINEERING_LOG.md").unlink()
    r = _envanter(sentetik_depo)
    assert r.returncode == 1
    assert r.stdout == ""
    assert "MERIDIAN_ENGINEERING_LOG.md" in r.stderr


def test_D10_girdi_kunyesi_icerik_adresli(sentetik_depo, tmp_path):
    veri, _ = _envanter_json(sentetik_depo, tmp_path)
    head = _git(sentetik_depo, "rev-parse", "HEAD").stdout.strip()
    assert veri["girdi"]["head"] == head
    icerik = ROADMAP_SENTETIK.encode("utf-8")
    blob = hashlib.sha1(b"blob %d\0" % len(icerik) + icerik).hexdigest()
    assert veri["girdi"]["dosyalar"]["ROADMAP.md"] == blob
    assert veri["girdi"]["kart_sayisi"] == 1
