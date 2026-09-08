"""test_arama_api_v459.py — TSK-167 dilim-2 / Task 1: `meridian/arama.py` + `GET /api/arama`.

TAŞINDI v455 → v459, 2026-09-08 (vNNN çakışması, mikro tur): dosya `test_arama_api_v455.py` olarak
doğdu ve o anda v455 boştu; main dalında sonradan v455 `test_soul_denetimi_rota_v455` tarafından,
v456/v457 gölge pilot tarafından, v458 roadmap arşiv sayımı tarafından ALINDI. Kimlik çakışan
tarafta az çapa vardı (bu dosya henüz merge edilmemişti) — CLAUDE.md'nin "çakışmada az-çapalı
taraf taşınır" kuralı gereği taşınan BU dosya oldu, ad çakışan üçü DEĞİL. Numara YENİDEN ölçüldü:
`ls tests | grep -oE 'v[0-9]+' | sort -t v -k2 -n | tail -1` main'de v458 veriyordu, v459 boştu.

NE ÇİVİLENİR (plan `docs/superpowers/plans/2026-09-08-tsk167-dilim2.md`, Çivi 1-16 + mikro tur
Çivi 17-19 — bağımsız inceleme, 2026-09-08, ısırmayan 3 mutasyon):
auth · boş soru 400 (süreç doğmadan) · `k` kelepçesi argv'den ÖLÇÜLÜR · `--dosya` beyaz listesi ·
argv sözleşmesi (`shell=False`, soru AYRI öğe) · betik yokken 200 + `sonuclar: None` (K1) ·
rc 1/2/3 ÜÇ AYRI `neden` (sözleşme CLI başlığından TÜRETİLİR, kopyalanmaz) · zaman aşımı ·
`scrub` · korpus dışı yol düşürülür ve SAYILIR · kesit tavanı + bedel beyanı · bozuk stdout ·
`obs.log("arama_sorgu")` künyesi (SORU METNİ YAZILMAZ) · eşzamanlılık kilidi · Yasa 6 ·
`sohbet._hafiza_betigi` → `arama.betik_yolu` devri (K2) · SINIRDA (600 karakter) scrub-önce/
kırpma-sonra sırası (Çivi 17) · kos-SONRASI istisnada kilit `finally` ile serbest kalır (Çivi 18)
· GERÇEK `_kos_varsayilan` zaman aşımında alt süreci GERÇEKTEN öldürür (Çivi 19).

GERÇEK CLI KOŞMAZ. A1'deki `hafiza_ara.sh` ONNX oturumu açar ve yerelde sqlite-vec yoktur
(`hafiza_ara.py` başlığı: "KOŞUM YERİ A1"). Bu dosyanın TAMAMI sahte bir `kos` çağrılabiliriyle
koşar — yani hiçbir alt süreç doğmaz, hiçbir model yüklenmez ve testler makineden bağımsızdır.
Çivi 17-19 İSTİSNADIR (mikro tur): `_kos_varsayilan`ı GERÇEK koşturur ama argv ARAMA CLI'sı
DEĞİLDİR — yalnız `time.sleep` çalıştıran sentetik bir kabuk betiğidir, ONNX/sqlite-vec gerekmez.
"""
from __future__ import annotations

import re
import subprocess
import textwrap
import threading
import time

import pytest
from fastapi.testclient import TestClient

from meridian import api, arama, codelaw, obs, secrets as secrets_mod, sohbet, store

CLI_YOLU = "research/olcumler/edg067_hindsight_faz1/hafiza_ara.py"


# =================================================================================================
# 0) SAHTE ALT SÜREÇ — bu dosyanın TEK dış dünya vekili
# =================================================================================================
class _Sonuc:
    """`subprocess.CompletedProcess`un bu yüzeyde OKUNAN üç alanı."""

    def __init__(self, returncode: int, stdout: str, stderr: str):
        self.returncode, self.stdout, self.stderr = returncode, stdout, stderr


class SahteKos:
    """Çağrıları KAYDEDEN sahte alt süreç. `cagrilar` argv listelerini AYNEN taşır — "süreç
    doğmadı" iddiası bir sayıdan ölçülür, docstring'den değil."""

    def __init__(self, rc: int = 0, stdout: str = "[]", stderr: str = "", patlat=None):
        self.rc, self.stdout, self.stderr, self.patlat = rc, stdout, stderr, patlat
        self.cagrilar: list[tuple[list[str], float]] = []

    def __call__(self, argv, zaman_asimi):
        self.cagrilar.append((list(argv), zaman_asimi))
        if self.patlat is not None:
            raise self.patlat
        return _Sonuc(self.rc, self.stdout, self.stderr)

    @property
    def n(self) -> int:
        return len(self.cagrilar)

    @property
    def son_argv(self) -> list[str]:
        assert self.cagrilar, "alt süreç HİÇ çağrılmadı"
        return self.cagrilar[-1][0]


def _satir(dosya="docs/RUNBOOK-YOK.md", bolum="## §1", metin="gövde", mesafe=0.25,
           blob_sha="abc123") -> dict:
    """`taban_indeks.py::en_yakin`in döndürdüğü satır şekli (plan: dosya · bolum · metin ·
    blob_sha · mesafe)."""
    return {"dosya": dosya, "bolum": bolum, "metin": metin, "mesafe": mesafe,
            "blob_sha": blob_sha}


def _json(satirlar) -> str:
    import json
    return json.dumps(satirlar, ensure_ascii=False)


@pytest.fixture
def betik(tmp_path, monkeypatch):
    """VAR OLAN bir betik yolu — `os.path.exists` kapısı geçsin diye. İçeriği hiç KOŞULMAZ."""
    yol = tmp_path / "hafiza_ara.sh"
    yol.write_text("#!/usr/bin/env bash\nexit 0\n")
    monkeypatch.setenv(arama.BETIK_ENV, str(yol))
    return yol


@pytest.fixture
def istemci(sandbox_state, monkeypatch) -> TestClient:
    monkeypatch.setattr(api, "DASH_TOKEN", None)
    return TestClient(api.app)


@pytest.fixture
def kos(monkeypatch):
    """Varsayılan alt süreç çalıştırıcısını sahtesiyle değiştirir — UÇ üzerinden koşan çiviler
    `kos=` argümanını geçiremez, çözüm modül genelindedir (çağrı anında okunur)."""
    sahte = SahteKos()
    monkeypatch.setattr(arama, "_kos_varsayilan", sahte)
    return sahte


def _arama_olaylari() -> list[dict]:
    return [o for o in store.read_jsonl("events.jsonl") if o.get("event") == "arama_sorgu"]


# =================================================================================================
# 1) ÇİVİ 1 — AUTH ZORUNLU (yetkisiz GET beyaz listesine EKLENMEZ; v21 p1c ayrıca ölçer)
# =================================================================================================
def test_civi1_auth_zorunlu(sandbox_state, monkeypatch):
    monkeypatch.setattr(api, "DASH_TOKEN", "gizli-jeton-degeri")
    c = TestClient(api.app)
    assert c.get("/api/arama", params={"soru": "kota nedir"}).status_code == 401


def test_civi1b_uc_yetkisiz_get_beyaz_listesinde_DEGIL():
    """Rota tablosunda `/api/arama` YETKİLİ görünmeli — `_auth` çağrısı kaynaktan ölçülür."""
    import inspect
    assert "_auth(request)" in inspect.getsource(api.api_arama)


# =================================================================================================
# 2) ÇİVİ 2 — BOŞ SORU 400 VE SÜREÇ DOĞMAZ
# =================================================================================================
@pytest.mark.parametrize("params", [{"soru": ""}, {"soru": "   "}, {}])
def test_civi2_bos_soru_400_ve_surec_dogmaz(istemci, betik, kos, params):
    r = istemci.get("/api/arama", params=params)
    assert r.status_code == 400, r.text
    assert kos.n == 0, f"boş soruda alt süreç doğdu: {kos.cagrilar}"


def test_civi2b_ara_bos_soruda_ValueError(betik, kos):
    with pytest.raises(ValueError):
        arama.ara("   ", kos=kos)
    assert kos.n == 0


# =================================================================================================
# 3) ÇİVİ 3 — `k` KELEPÇESİ ARGV'DEN ÖLÇÜLÜR
# =================================================================================================
@pytest.mark.parametrize("verilen,beklenen", [("0", "1"), ("-1", "1"), ("999", "20"), ("7", "7")])
def test_civi3_k_kelepcesi_argvde_gorunur(istemci, betik, kos, verilen, beklenen):
    r = istemci.get("/api/arama", params={"soru": "kota", "k": verilen})
    assert r.status_code == 200, r.text
    argv = kos.son_argv
    assert "-k" in argv and argv[argv.index("-k") + 1] == beklenen, argv


def test_civi3b_sayi_olmayan_k_400_ve_surec_dogmaz(istemci, betik, kos):
    r = istemci.get("/api/arama", params={"soru": "kota", "k": "beş"})
    assert r.status_code == 400, r.text
    assert kos.n == 0


@pytest.mark.parametrize("verilen,beklenen", [(0, "1"), (-1, "1"), (999, "20"), (7, "7")])
def test_civi3bb_ara_DOGRUDAN_cagrildiginda_da_kelepcelenir(betik, kos, sandbox_state,
                                                            verilen, beklenen):
    """UÇTAN GEÇEN ÇİVİ YETMEZ (mutasyon bulgusu, 2026-09-08): uçtaki kelepçe kaldırılmadan
    `ara` içindekini bozmak hiçbir çiviyi kırmıyordu — yani o kelepçe ÖLÇÜLMÜYORDU."""
    arama.ara("kota", k=verilen, kos=kos)
    argv = kos.son_argv
    assert argv[argv.index("-k") + 1] == beklenen, argv


def test_civi3c_k_tavani_yirmi():
    """K6 hükmü: sohbetle ORTAK sabit (tek kaynak) — pano 5/10 sunar, tavan burada durur."""
    assert arama.K_TAVANI == 20


# =================================================================================================
# 4) ÇİVİ 4 — `--dosya` BEYAZ LİSTESİ
# =================================================================================================
@pytest.mark.parametrize("onek", ["state/", "/etc/", "../", ".env", "state/secrets.json",
                                  "docs/../state/", "ROADMAP.md"])
def test_civi4_korpus_disi_onek_400_ve_surec_dogmaz(istemci, betik, kos, onek):
    r = istemci.get("/api/arama", params={"soru": "kota", "dosya": onek})
    assert r.status_code == 400, f"{onek!r} kabul edildi: {r.text}"
    assert kos.n == 0


@pytest.mark.parametrize("onek", ["docs/", "docs/superpowers/", "research/cards/",
                                  "MERIDIAN_ENGINEERING_LOG.md", "ROADMAP.md%237"])
def test_civi4b_korpus_onekleri_gecer_ve_argvde_durur(istemci, betik, kos, onek):
    r = istemci.get("/api/arama", params={"soru": "kota", "dosya": onek})
    assert r.status_code == 200, r.text
    argv = kos.son_argv
    assert "--dosya" in argv and argv[argv.index("--dosya") + 1] == onek, argv


def test_civi4c_onek_kumesi_manifest_korpusuyla_ayrismaz():
    """Beyaz liste, indekse GİREN korpusun kendisidir (`manifest_uret.py`): günlük · ROADMAP §7
    kesiti · kartlar · docs. Ayrışırsa uç ya meşru sonucu düşürür ya korpus dışını geçirir."""
    from pathlib import Path
    from meridian import config
    kaynak = (Path(config.ROOT) / "research" / "olcumler" / "edg067_hindsight_faz1"
              / "manifest_uret.py").read_text(encoding="utf-8")
    for onek in ("MERIDIAN_ENGINEERING_LOG.md", "ROADMAP.md%237", "research/cards/", "docs/"):
        assert onek in kaynak, f"{onek!r} manifest korpusunda ölçülemedi"
    assert set(arama.KORPUS_ONEKLERI) == {"docs/", "research/cards/",
                                          "MERIDIAN_ENGINEERING_LOG.md", "ROADMAP.md%237"}


# =================================================================================================
# 5) ÇİVİ 5 — ARGV SÖZLEŞMESİ (`shell=False`, soru AYRI öğe)
# =================================================================================================
def test_civi5_argv_json_ve_k_tasir_soru_ayri_ogedir(istemci, betik, kos):
    soru = "kota tavanı; rm -rf / $(whoami) `id`"
    r = istemci.get("/api/arama", params={"soru": soru, "k": "3"})
    assert r.status_code == 200, r.text
    argv = kos.son_argv
    assert argv[0] == str(betik)
    assert "--json" in argv
    assert argv[-1] == soru, "soru argv'nin SON ve AYRI öğesi değil"
    assert not any(a is not soru and (";" in a or "$(" in a) for a in argv[:-1]), argv


def test_civi5b_kabuk_enjeksiyonu_yuzeyi_YOK():
    """`shell=True` yok, `shell=` parametresi HİÇ yok: çalıştırıcının KODU ölçülür.

    DOCSTRING SÜZÜLÜR, ÖLÇÜM KODA İNER: ilk yazımda `inspect.getsource` şerhi de kapsıyordu ve
    "shell=False (varsayılan)" cümlesi çiviyi kırdı — yani çivi kodu değil düzyazıyı ölçüyordu."""
    import ast
    import inspect
    src = inspect.getsource(arama._kos_varsayilan)
    fn = ast.parse(textwrap.dedent(src)).body[0]
    govde = "\n".join(ast.unparse(d) for d in fn.body
                      if not (isinstance(d, ast.Expr) and isinstance(d.value, ast.Constant)))
    assert "shell" not in govde, f"kabuk parametresi kodda geçmemeli: {govde}"
    assert "subprocess.run(" in govde


def test_civi5c_zaman_asimi_argvle_birlikte_gecer(istemci, betik, kos):
    istemci.get("/api/arama", params={"soru": "kota"})
    _, zaman = kos.cagrilar[-1]
    assert zaman == arama.ARAMA_ZAMAN_ASIMI_S == 60


# =================================================================================================
# 6) ÇİVİ 6 — BETİK YOKKEN 200 + `sonuclar: None` (K1: 200 + neden, 503 DEĞİL)
# =================================================================================================
def test_civi6_betik_yoksa_200_ve_olculemedi(istemci, tmp_path, monkeypatch, kos):
    monkeypatch.setenv(arama.BETIK_ENV, str(tmp_path / "yok.sh"))
    r = istemci.get("/api/arama", params={"soru": "kota"})
    assert r.status_code == 200, r.text
    g = r.json()
    assert g["sonuclar"] is None and g["n"] is None
    assert "ölçülemedi" in (g["neden"] or ""), g["neden"]
    assert kos.n == 0


def test_civi6b_bos_sonuc_olculemedi_DEGIL(istemci, betik, kos):
    """"0 satır" bir BULGUdur: `sonuclar: []` + `neden: None`. İkisini katlamak uydurmadır."""
    kos.stdout = "[]"
    g = istemci.get("/api/arama", params={"soru": "kota"}).json()
    assert g["sonuclar"] == [] and g["n"] == 0 and g["neden"] is None


# =================================================================================================
# 7) ÇİVİ 7 — rc AYRIMI (sözleşme CLI BAŞLIĞINDAN TÜRETİLİR)
# =================================================================================================
def _cli_cikis_kodlari() -> dict[int, str]:
    """CLI'ın "ÇIKIŞ KODU SÖZLEŞMESİ" bloğundaki SIFIR OLMAYAN kodlar — tek kaynak orasıdır."""
    from pathlib import Path
    from meridian import config
    metin = (Path(config.ROOT) / CLI_YOLU).read_text(encoding="utf-8")
    blok = metin.split("ÇIKIŞ KODU SÖZLEŞMESİ", 1)[1].split("KULLANIM", 1)[0]
    return {int(m.group(1)): m.group(2).strip()
            for m in re.finditer(r"^\s{4}([1-9]) — (.+)$", blok, re.M)}


def test_civi7_rc_sozlesmesi_CLI_BASLIGINDAN_turetilir():
    kodlar = _cli_cikis_kodlari()
    assert kodlar, "CLI'ın çıkış kodu sözleşmesi okunamadı — çapa kaydı"
    assert set(arama.RC_NEDENLERI) == set(kodlar), (
        f"sarmalayıcı kodları CLI ile ayrıştı: {set(arama.RC_NEDENLERI) ^ set(kodlar)}")


@pytest.mark.parametrize("rc", [1, 2, 3])
def test_civi7b_rc_ayri_neden_uretir(istemci, betik, kos, rc):
    kos.rc, kos.stderr = rc, "stderr metni"
    g = istemci.get("/api/arama", params={"soru": "kota"}).json()
    assert g["sonuclar"] is None and g["n"] is None
    assert str(rc) in (g["neden"] or ""), g["neden"]
    assert arama.RC_NEDENLERI[rc] in g["neden"], g["neden"]


def test_civi7c_uc_neden_metni_BIRBIRINDEN_ayrik(istemci, betik, kos):
    nedenler = set()
    for rc in (1, 2, 3):
        kos.rc = rc
        nedenler.add(istemci.get("/api/arama", params={"soru": "k"}).json()["neden"])
    assert len(nedenler) == 3, nedenler


# =================================================================================================
# 8) ÇİVİ 8 — ZAMAN AŞIMI (süre ADIYLA yazılır)
# =================================================================================================
def test_civi8_zaman_asimi_sureyi_adiyla_yazar(istemci, betik, monkeypatch):
    patlayan = SahteKos(patlat=subprocess.TimeoutExpired(cmd=["x"], timeout=60))
    monkeypatch.setattr(arama, "_kos_varsayilan", patlayan)
    g = istemci.get("/api/arama", params={"soru": "kota"}).json()
    assert g["sonuclar"] is None
    assert "ölçülemedi" in g["neden"] and "60" in g["neden"], g["neden"]


def test_civi8b_alt_surec_hic_kosamazsa_olculemedi(istemci, betik, monkeypatch):
    patlayan = SahteKos(patlat=OSError("Exec format error"))
    monkeypatch.setattr(arama, "_kos_varsayilan", patlayan)
    g = istemci.get("/api/arama", params={"soru": "kota"}).json()
    assert g["sonuclar"] is None and "ölçülemedi" in g["neden"]


# =================================================================================================
# 9) ÇİVİ 9 — SIR: giden her dizge `notify.scrub`tan geçer
# =================================================================================================
def test_civi9_sir_govdeye_sizmaz(istemci, betik, kos, monkeypatch):
    sir = "SIRDEGERI-1234567890"
    monkeypatch.setattr(secrets_mod, "ALLOWED", ("TELEGRAM_BOT_TOKEN",))
    monkeypatch.setattr(secrets_mod, "get", lambda ad, *a, **kw: sir)
    kos.stdout = _json([_satir(metin=f"gövde {sir} devam", bolum=f"## {sir}")])
    ham = istemci.get("/api/arama", params={"soru": "kota"}).text
    assert sir not in ham, "sır yanıt gövdesinde"
    assert "***" in ham


# =================================================================================================
# 10) ÇİVİ 10 — KORPUS DIŞI YOL DÜŞÜRÜLÜR VE SAYILIR
# =================================================================================================
def test_civi10_korpus_disi_satir_dusurulur_ve_beyan_edilir(istemci, betik, kos):
    kos.stdout = _json([_satir(dosya="state/secrets.json", metin="ALPACA_KEY=xyz"),
                        _satir(dosya="docs/RUNBOOK-YOK.md")])
    r = istemci.get("/api/arama", params={"soru": "kota"})
    g, ham = r.json(), r.text
    assert g["korpus_disi_n"] == 1
    assert g["n"] == 1 and g["sonuclar"][0]["dosya"] == "docs/RUNBOOK-YOK.md"
    assert "secrets.json" not in ham, "korpus dışı yol gövdede"


def test_civi10b_korpus_ici_koşumda_sayi_sifir(istemci, betik, kos):
    kos.stdout = _json([_satir(dosya="research/cards/EDG-2026-067.yaml")])
    g = istemci.get("/api/arama", params={"soru": "kota"}).json()
    assert g["korpus_disi_n"] == 0 and g["n"] == 1


# =================================================================================================
# 11) ÇİVİ 11 — KESİT TAVANI + BEDEL BEYANI
# =================================================================================================
def test_civi11_kesit_tavani_ve_bedel_beyani(istemci, betik, kos):
    kos.stdout = _json([_satir(metin="x" * 5000)])
    s = istemci.get("/api/arama", params={"soru": "kota"}).json()["sonuclar"][0]
    assert len(s["kesit"]) <= arama.ARAMA_KESIT_TAVANI == 600
    assert s["kesit_kirpildi"] is True
    assert s["metin_uzunluk"] == 5000


def test_civi11b_tavanin_altinda_kirpma_YOK(istemci, betik, kos):
    kos.stdout = _json([_satir(metin="kısa gövde")])
    s = istemci.get("/api/arama", params={"soru": "kota"}).json()["sonuclar"][0]
    assert s["kesit"] == "kısa gövde" and s["kesit_kirpildi"] is False
    assert s["metin_uzunluk"] == len("kısa gövde")


def test_civi11c_mesafe_HAM_doner(istemci, betik, kos):
    """Recall.tsx'in ölçülmüş gerekçesi: ham skor yuvarlanmaz."""
    kos.stdout = _json([_satir(mesafe=0.123456789)])
    s = istemci.get("/api/arama", params={"soru": "kota"}).json()["sonuclar"][0]
    assert s["mesafe"] == 0.123456789
    assert s["blob_sha"] == "abc123"


# =================================================================================================
# 12) ÇİVİ 12 — BOZUK STDOUT + YASA 4
# =================================================================================================
def test_civi12_bozuk_stdout_olculemedi(istemci, betik, kos):
    kos.stdout = "bu JSON değil {"
    g = istemci.get("/api/arama", params={"soru": "kota"}).json()
    assert g["sonuclar"] is None and g["n"] is None
    assert "ölçülemedi" in g["neden"], g["neden"]


def test_civi12b_liste_olmayan_json_olculemedi(istemci, betik, kos):
    kos.stdout = '{"sonuclar": []}'
    g = istemci.get("/api/arama", params={"soru": "kota"}).json()
    assert g["sonuclar"] is None and "ölçülemedi" in g["neden"]


def test_civi12c_yasa4_arama_modulunde_isaretsiz_yakalayici_YOK():
    ihlaller = [h for h in codelaw.silent_handlers("meridian")
                if h["file"].endswith("arama.py")]
    assert ihlaller == [], ihlaller


# =================================================================================================
# 13) ÇİVİ 13 — `obs.log("arama_sorgu")` KÜNYESİ; SORU METNİ YAZILMAZ
# =================================================================================================
def test_civi13_kunye_yazilir_soru_metni_YAZILMAZ(istemci, betik, kos):
    kos.stdout = _json([_satir()])
    soru = "kota tavanı nedir"
    istemci.get("/api/arama", params={"soru": soru, "k": "3"})
    olaylar = _arama_olaylari()
    assert len(olaylar) == 1, olaylar
    o = olaylar[0]
    assert o["k"] == 3 and o["n"] == 1 and o["soru_uzunluk"] == len(soru)
    assert o["neden"] is None and o["mesgul"] is False and o["korpus_disi_n"] == 0
    assert isinstance(o["sure_s"], (int, float))
    import json as _j
    assert soru not in _j.dumps(o, ensure_ascii=False), "soru METNİ olay defterine düştü"


def test_civi13b_olculemedi_de_kunye_yazar(istemci, betik, kos):
    kos.rc = 1
    istemci.get("/api/arama", params={"soru": "kota"})
    olaylar = _arama_olaylari()
    assert len(olaylar) == 1 and olaylar[0]["neden"] and olaylar[0]["n"] is None


def test_civi13c_kunye_gunluk_sayacin_TEK_kaynagi():
    """K5: ikinci bir sayaç DOSYASI tutulmaz — gün içi çağrı sayısı olay defterinden sayılır."""
    import inspect
    src = inspect.getsource(api.api_arama) + inspect.getsource(arama)
    assert "kota_durumu" not in src, "kota sayacı emsali bu uçta UYGULANMAZ (K5)"
    for yazan in ("append_jsonl", "write_json", "write_jsonl", "write_text", "update_json"):
        assert f"store.{yazan}" not in src, f"arama yüzeyi state'e yazıyor: {yazan}"


# =================================================================================================
# 14) ÇİVİ 14 — EŞZAMANLILIK: kilit tutulurken İKİNCİ SÜREÇ DOĞMAZ
# =================================================================================================
def test_civi14_kilit_tutulurken_mesgul_doner_ve_surec_dogmaz(betik, kos, sandbox_state):
    arama._ARAMA_KILIDI.acquire()
    try:
        g = arama.ara("kota", kos=kos)
    finally:
        arama._ARAMA_KILIDI.release()
    assert g["mesgul"] is True
    assert g["sonuclar"] is None and g["n"] is None and g["neden"], g
    assert kos.n == 0, "meşgulken alt süreç doğdu"


def test_civi14b_kilit_serbest_kalinca_calisir(betik, kos, sandbox_state):
    kos.stdout = _json([_satir()])
    g = arama.ara("kota", kos=kos)
    assert g["mesgul"] is False and g["n"] == 1
    assert not arama._ARAMA_KILIDI.locked(), "kilit bırakılmadı"


def test_civi14c_arizada_da_kilit_birakilir(betik, sandbox_state):
    patlayan = SahteKos(patlat=OSError("boom"))
    arama.ara("kota", kos=patlayan)
    assert not arama._ARAMA_KILIDI.locked()


def test_civi14d_ikinci_iplik_mesgule_duser(betik, sandbox_state):
    """Gerçek iki iplik: birincisi kilitteyken ikincisi süreç DOĞURMADAN döner."""
    girdi, birak = threading.Event(), threading.Event()

    def yavas_kos(argv, zaman_asimi):
        girdi.set()
        birak.wait(5)
        return _Sonuc(0, "[]", "")

    ikinci: dict = {}
    t = threading.Thread(target=lambda: ikinci.update(arama.ara("a", kos=yavas_kos)))
    t.start()
    assert girdi.wait(5), "birinci iplik alt sürece giremedi"
    sayac = SahteKos()
    g = arama.ara("b", kos=sayac)
    birak.set()
    t.join(5)
    assert g["mesgul"] is True and sayac.n == 0
    assert ikinci["mesgul"] is False


# =================================================================================================
# 15) ÇİVİ 15 — YASA 6: SALT OKUMA
# =================================================================================================
def test_civi15_ara_HICBIR_dosya_yazmaz(betik, kos, sandbox_state, monkeypatch):
    yazilan: set[str] = set()
    for ad in ("append_jsonl", "write_json", "write_jsonl", "write_text", "update_json",
               "update_jsonl", "merge_dated_jsonl"):
        monkeypatch.setattr(store, ad, lambda name, *a, **kw: yazilan.add(name))
    kos.stdout = _json([_satir()])
    arama.ara("kota", kos=kos)
    assert yazilan == set(), f"`arama.ara` state'e yazdı: {yazilan}"


def test_civi15b_uc_yalniz_olay_kunyesini_yazar(istemci, betik, kos, monkeypatch):
    yazilan: set[str] = set()
    gercek = store.append_jsonl
    monkeypatch.setattr(store, "append_jsonl",
                        lambda name, row: (yazilan.add(name), gercek(name, row))[1])
    for ad in ("write_json", "write_jsonl", "write_text", "update_json", "update_jsonl"):
        monkeypatch.setattr(store, ad, lambda name, *a, **kw: yazilan.add(name))
    kos.stdout = _json([_satir()])
    istemci.get("/api/arama", params={"soru": "kota"})
    assert yazilan <= {obs._EVENTS}, f"yeni defter doğdu: {yazilan - {obs._EVENTS}}"


def test_civi15c_olay_kunyesinin_okuyucusu_MEVCUT():
    """Beyanlı muafiyet (`DECLARED_SINKS`) GEREKMEZ: `events.jsonl`ın okuyucusu `api.py`de."""
    assert obs._EVENTS not in set(getattr(codelaw, "DECLARED_SINKS", ()) or ())
    import inspect
    assert obs._EVENTS in inspect.getsource(api)


# =================================================================================================
# 16) ÇİVİ 16 — DEVİR (K2): tek kaynak `arama.betik_yolu`
# =================================================================================================
def test_civi16_sohbet_ve_arama_AYNI_yolu_doner(tmp_path, monkeypatch):
    monkeypatch.setenv(arama.BETIK_ENV, str(tmp_path / "x.sh"))
    assert sohbet._hafiza_betigi() == arama.betik_yolu() == str(tmp_path / "x.sh")


def test_civi16b_env_adi_KORUNUR():
    """v440 `SOHBET_HAFIZA_ARA`yı monkeypatch'liyor — ad değişirse o çivi sessizce körleşirdi."""
    assert arama.BETIK_ENV == "SOHBET_HAFIZA_ARA"


def test_civi16c_sohbet_kendi_cozucusunu_TUTMAZ():
    import inspect
    src = inspect.getsource(sohbet._hafiza_betigi)
    assert "arama" in src and "betik_yolu" in src
    assert "hafiza_ara.sh" not in src, "ikinci çözücü kaldı — sessiz ayrışma yüzeyi"


def test_civi16d_varsayilan_yol_depo_kurulumunu_gosterir(monkeypatch):
    from meridian import config
    monkeypatch.delenv(arama.BETIK_ENV, raising=False)
    assert arama.betik_yolu() == str(config.ROOT / "deploy" / "hindsight" / "hafiza_ara.sh")


# =================================================================================================
# 17) ZARF ŞEKLİ — Task 2 (UI) bu alanları okur; ikinci bir şekil ikinci bir gerçek olurdu
# =================================================================================================
ZARF_ALANLARI = ("sonuclar", "kunye", "n", "korpus_disi_n", "sure_s", "mesgul", "neden")
SATIR_ALANLARI = ("dosya", "bolum", "mesafe", "blob_sha", "kesit", "kesit_kirpildi",
                  "metin_uzunluk")


def test_zarf_alanlari_her_dalda_AYNI(istemci, betik, kos):
    kos.stdout = _json([_satir()])
    dolu = istemci.get("/api/arama", params={"soru": "kota"}).json()
    kos.rc = 1
    ariza = istemci.get("/api/arama", params={"soru": "kota"}).json()
    for govde in (dolu, ariza):
        assert set(ZARF_ALANLARI) <= set(govde), set(ZARF_ALANLARI) - set(govde)
    assert set(SATIR_ALANLARI) == set(dolu["sonuclar"][0])


def test_kunye_stderrden_cozulur(istemci, betik, kos):
    """`--json` modunda künye STDERR'e gider (CLI: "stdout O ZAMAN saf JSON'dur")."""
    kos.stderr = ("# indeks: uretim_ts=2026-09-06T23:00:00Z · head_commit=ac824e1 · "
                  "chunk_sayisi=3582 · dosya_sayisi=None\n")
    kos.stdout = _json([_satir()])
    k = istemci.get("/api/arama", params={"soru": "kota"}).json()["kunye"]
    assert k["head_commit"] == "ac824e1" and k["chunk_sayisi"] == "3582"
    assert k["dosya_sayisi"] is None, "'None' dizgesi bir DEĞER değildir (uydurma yasağı)"


def test_kunye_yoksa_None_bos_sozluk_DEGIL(istemci, betik, kos):
    kos.stderr = ""
    assert istemci.get("/api/arama", params={"soru": "kota"}).json()["kunye"] is None


# =================================================================================================
# 18) ÇİVİ 17 — SCRUB ÖNCE, KIRPMA SONRA: sınırda YARIM sır sızmaz
#
# Bağımsız inceleme (TSK-167 dilim-2 Task 1, 2026-09-08) bunu MUTASYONLA ölçtü: sırayı tersine
# çevirince (önce kırp, sonra scrub) mevcut 67 çivinin HİÇBİRİ kırılmadı — `test_civi9` kısa bir
# metinle (tavanın ALTINDA) çalışıyor, `test_civi11` uzun metinle ama SIR OLMADAN. İkisini
# birleştiren — sırrın TAM 600 karakter sınırını AŞAN bir noktada durduğu — örnek yoktu.
# =================================================================================================
def test_civi17_sinirda_YARIM_sir_KIRPMADAN_ONCE_scrublanir_ve_sizmaz(istemci, betik, kos,
                                                                       monkeypatch):
    """Sır [590:611) aralığında durur — 600 karakter sınırının TAM ORTASINDAN geçer. Sıra
    DOĞRUYSA (`_temiz` önce) sır `***`e döner ve kırpma bu maskeden SONRAKİ karakterlerde olur;
    sıra TERS olsaydı `metin[:600]` sırrın yalnız ilk 10 karakterini (`SIRDEGERI-`) keser ve o
    yarım dizge `notify.scrub`a hiç ULAŞMADAN kesitte kalır (kırmızıyı elle doğrulanan tam bu
    örnekle üretiyoruz)."""
    sir = "SIRDEGERI-1234567890"
    monkeypatch.setattr(secrets_mod, "ALLOWED", ("TELEGRAM_BOT_TOKEN",))
    monkeypatch.setattr(secrets_mod, "get", lambda ad, *a, **kw: sir)
    metin = "x" * 590 + sir + "y" * 50
    kos.stdout = _json([_satir(metin=metin)])
    ham = istemci.get("/api/arama", params={"soru": "kota"}).text
    assert sir not in ham, "tam sır gövdede"
    assert "SIRDEGERI" not in ham, f"sırrın YARIM bir parçası kesitte sızdı: {ham[:700]!r}"
    assert "***" in ham


def test_civi17b_temiz_KIRPILMADAN_ONCEKI_TAM_uzunlugu_gorur(istemci, betik, kos, monkeypatch):
    """Yapısal ikinci bakış (davranışsaldan bağımsız): `notify.scrub`a giden dizgenin uzunluğu
    CASUSLANIR. Kırpma ÖNCE olsaydı `_temiz` en fazla 600 karakter görürdü — burada 900 karakterlik
    bir gövde geçiyoruz ve TAM uzunluğun scrub'a ULAŞTIĞINI ölçüyoruz."""
    uzunluklar: list[int] = []
    gercek_temiz = arama._temiz

    def casus(deger):
        uzunluklar.append(len(str(deger if deger is not None else "")))
        return gercek_temiz(deger)

    monkeypatch.setattr(arama, "_temiz", casus)
    kos.stdout = _json([_satir(metin="z" * 900)])
    istemci.get("/api/arama", params={"soru": "kota"})
    assert uzunluklar and max(uzunluklar) >= 900, (
        f"scrub'a giden metin ÖNCEDEN kırpılmış görünüyor: {uzunluklar}")


# =================================================================================================
# 19) ÇİVİ 18 — KOS SONRASI İSTİSNADA KİLİT `finally` İLE SERBEST KALIR
#
# İnceleme: `test_civi14c` yalnız `kos()` çağrısını patlatıyor ve `_ara_kilitliyken`'in KENDİ
# `except Exception`ı onu zaten yakalıyor — `ara()`nin `try` bloğu hiçbir zaman gerçekten istisna
# GÖRMÜYOR, `finally`nin asıl işlevi hiç TETİKLENMİYOR. Burada kos() BAŞARILI olduktan SONRA, ama
# `_ara_kilitliyken`'in kendi try/except'i DIŞINDA kalan bir noktayı (`_suz`) patlatıyoruz.
# =================================================================================================
def _patlayan_suz(ham):
    raise RuntimeError("suz patladi — kos SONRASI istisna")


def test_civi18_kos_sonrasi_istisnada_kilit_finally_ile_serbest_kalir(betik, kos, sandbox_state,
                                                                       monkeypatch):
    """TAZE KİLİT: paylaşılan `_ARAMA_KILIDI` bu mutasyonun KENDİSİ tarafından kalıcı kilitli
    bırakılabilir — bu testin (ve komşularının) sonucu bir ÖNCEKİ testin durumuna bağlı KALMASIN
    diye modül genelindeki kilidin YERİNE taze bir `Lock()` takılır."""
    monkeypatch.setattr(arama, "_ARAMA_KILIDI", threading.Lock())
    kos.stdout = _json([_satir()])
    monkeypatch.setattr(arama, "_suz", _patlayan_suz)
    with pytest.raises(RuntimeError):
        arama.ara("kota", kos=kos)
    assert not arama._ARAMA_KILIDI.locked(), "kos SONRASI istisnada kilit bırakılmadı"


def test_civi18b_finally_OLMASA_ikinci_cagri_SURESIZ_mesgul_kalirdi(betik, sandbox_state,
                                                                     monkeypatch):
    """Uçtan görünen sonuç: kilit gerçekten kurtarılmazsa yeniden başlatmadan düzelmeyen bir
    `mesgul: true` üretir. Burada `_suz`ü GERİ ALIRKEN `monkeypatch.undo()` KULLANILMAZ (autouse
    fikstürleri de geri alırdı) — orijinal fonksiyon açıkça `setattr` ile YENİDEN takılır. TAZE
    KİLİT gerekçesi `test_civi18` ile aynı."""
    monkeypatch.setattr(arama, "_ARAMA_KILIDI", threading.Lock())
    orijinal_suz = arama._suz
    monkeypatch.setattr(arama, "_suz", _patlayan_suz)
    kos1 = SahteKos(stdout=_json([_satir()]))
    with pytest.raises(RuntimeError):
        arama.ara("kota", kos=kos1)
    monkeypatch.setattr(arama, "_suz", orijinal_suz)
    kos2 = SahteKos(stdout=_json([_satir()]))
    g = arama.ara("kota", kos=kos2)
    assert g["mesgul"] is False and kos2.n == 1, (
        "finally olmasaydı ikinci çağrı SÜRESİZ meşgul kalırdı (yeniden başlatmadan düzelmez)")


# =================================================================================================
# 20) ÇİVİ 19 — GERÇEK `_kos_varsayilan`: zaman aşımında alt süreç GERÇEKTEN öldürülür
#
# İnceleme: `_kos_varsayilan`ın GERÇEK davranışı hiçbir çivide koşmuyordu — `test_civi5c` yalnız
# SAHTEye geçen `zaman_asimi` değerini ölçüyor, gerçek `subprocess.run` çağrısının `timeout=`
# argümanını FİİLEN aldığını değil. `kos=` HİÇ verilmez (`ara()` varsayılan çözücüyü kullanır);
# betik GERÇEKTEN uyuyan bir kabuk betiğidir — ARAMA CLI'sı DEĞİL, sqlite-vec/ONNX gerekmez.
# =================================================================================================
def test_civi19_gercek_alt_surec_zaman_asiminda_oldurulur_ve_neden_sureyi_yazar(
        tmp_path, sandbox_state, monkeypatch):
    uyuyan = tmp_path / "uyuyan.sh"
    # exec: gerçek `hafiza_ara.sh` gibi PID DEVRALIR — kill çocuğun kendisini öldürür, artık süreç
    # bırakmaz (inceleme, "process group gerekir mi" sorusunun ölçülmüş cevabı).
    uyuyan.write_text("#!/usr/bin/env bash\nexec sleep 5\n")
    uyuyan.chmod(0o755)
    monkeypatch.setenv(arama.BETIK_ENV, str(uyuyan))
    monkeypatch.setattr(arama, "ARAMA_ZAMAN_ASIMI_S", 0.3)
    t0 = time.monotonic()
    g = arama.ara("kota")
    gecen = time.monotonic() - t0
    assert gecen < 3.0, f"alt süreç zaman aşımında GERÇEKTEN öldürülmedi, {gecen:.2f}s bekledi"
    assert g["sonuclar"] is None and g["n"] is None
    assert "ölçülemedi" in g["neden"] and "0.3" in g["neden"], g["neden"]
