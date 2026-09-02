"""TSK-107 + TSK-087 dayanıklılık çivileri — F9 "ayrık artefakt" dosyalarının repo kaynağı.

TSK-107 (vaka 2026-09-02 07:08Z): kesik inen gz, ~8 dk ayrıştırma CPU'sundan SONRA gzip
`EOFError` ile patladı; birim failed'a düştü ve arıza YANLIŞ ADLA (gzip iç hatası gibi)
göründü. Çivi: indirme BİTTİKTEN sonra boyut kıyası → `KesikIndirme` + yarım gz silinir;
önbellek kapısı AYNI yardımcıyı kullanır (tek-kaynak yasası); beklenen bilinmiyorsa kıyas
YAPILMAZ ve bir kez not düşülür (uydurma yasağı).

TSK-087: `geridolum.py` ISCI=2 işçiden biri rc≠0 verince koşum ANINDA KIRMIZI'ya düşüyordu —
öteki işçinin bitmiş işi yarıda kalıyor, saatlik timer'a kadar bekleniyordu. Çivi: çöken gün
AYNI koşumda BİR kez yeniden denenir (öteki işçi sürerken); ikinci çöküşte yine KIRMIZI, ve
bedel yasası özeti her koşumda çıkar ("N düştü / M 2. denemede geçti / K kaldı"). Kalıcı ve
geçici arıza sınıfı ayrımı YALNIZ mesajdadır — sınıf rc'den ölçülemez, karar ona bağlanmaz.

Ölçülen dosyalar (canlıda /opt/veri/ altında ayrık yaşarlar; kurulum Rol-1'de):
  research/olcumler/edg066_tick_arsiv/pilot.py
  deploy/oracle-a1/geridolum.py
Gerçek ağ, gerçek /opt/veri ve obs YOK: `urlopen` ve `subprocess.Popen` sahtelenir, KOK tmp_path.
"""
from __future__ import annotations

import importlib.util
import json
import pathlib
import re

import pytest

DEPO = pathlib.Path(__file__).resolve().parents[1]
PILOT_YOL = DEPO / "research" / "olcumler" / "edg066_tick_arsiv" / "pilot.py"
GERIDOLUM_YOL = DEPO / "deploy" / "oracle-a1" / "geridolum.py"


def _yukle(ad: str, yol: pathlib.Path):
    """F9 ayrık artefaktları paket değildir — dosya yolundan yüklenir. Modül yüklemesi dosya
    AÇMAZ (ölçüldü 2026-09-02: /opt/veri sabitleri yalnız Path nesnesi üretir), bu yüzden
    import yan etkisizdir; tembelleştirme gerekmedi."""
    spec = importlib.util.spec_from_file_location(ad, yol)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


pilot = _yukle("edg066_pilot_v377", PILOT_YOL)
gd = _yukle("edg066_geridolum_v377", GERIDOLUM_YOL)


# ------------------------------------------------------------------ TSK-107: indir()

class _SahteCevap:
    """urlopen bağlam yöneticisinin okuma bacağı — parça parça verir, ağa çıkmaz."""

    def __init__(self, govde: bytes):
        self._govde, self._poz = govde, 0

    def read(self, n: int = -1) -> bytes:
        if n is None or n < 0:
            n = len(self._govde) - self._poz
        parca = self._govde[self._poz:self._poz + n]
        self._poz += len(parca)
        return parca

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


@pytest.fixture
def sahte_ag(monkeypatch):
    """urlopen'ı sahteler ve ÇAĞRI defterini döndürür — önbellek kapısı çivisi onu okur."""
    cagri: list[str] = []

    def kur(govde: bytes) -> list[str]:
        def urlopen(url, timeout=None):
            cagri.append(url)
            return _SahteCevap(govde)

        monkeypatch.setattr(pilot.urllib.request, "urlopen", urlopen)
        return cagri

    return kur


def test_kesik_inen_dosya_KesikIndirme_atar_ve_yarim_dosyayi_siler(tmp_path, sahte_ag):
    sahte_ag(b"x" * 10)                       # HIST 100 bayt dedi, 10 geldi
    hedef = tmp_path / "2020-09-15.pcap.gz"
    with pytest.raises(pilot.KesikIndirme) as exc:
        pilot.indir("http://ornek/ham.gz", hedef, 100)
    mesaj = str(exc.value)
    assert re.fullmatch(r"KIRMIZI: kesik indirme \S+ \d+/\d+ bayt", mesaj), mesaj
    assert "2020-09-15.pcap.gz 10/100 bayt" in mesaj, mesaj
    assert not hedef.exists(), "yarım gz önbellekte kaldı — sonraki tur yine EOFError'a yürür"


def test_tam_inen_dosya_gecer(tmp_path, sahte_ag):
    sahte_ag(b"x" * 100)
    hedef = tmp_path / "2020-09-15.pcap.gz"
    pilot.indir("http://ornek/ham.gz", hedef, 100)
    assert hedef.stat().st_size == 100


@pytest.mark.parametrize("beklenen", [None, 0])
def test_beklenen_bilinmiyorsa_kiyas_atlanir_ve_bir_kez_not_dusulur(
        beklenen, tmp_path, sahte_ag, capsys):
    """Uydurma yasağı: bilinmeyen boyutla kıyas UYDURULMAZ — atlanır ve GÖRÜNÜR olur (Yasa 6)."""
    sahte_ag(b"x" * 7)
    hedef = tmp_path / "2020-09-15.pcap.gz"
    pilot.indir("http://ornek/ham.gz", hedef, beklenen)
    cikti = capsys.readouterr().out
    assert hedef.exists() and hedef.stat().st_size == 7
    assert cikti.count("boyut kıyası atlandı") == 1, cikti


def test_onbellek_kapisi_tam_dosyada_ag_bacagina_hic_gitmez(tmp_path, sahte_ag):
    cagri = sahte_ag(b"x" * 100)
    hedef = tmp_path / "2020-09-15.pcap.gz"
    hedef.write_bytes(b"y" * 100)
    pilot.indir("http://ornek/ham.gz", hedef, 100)
    assert cagri == [], "önbellek kapısı düştü — iki boyut kıyası sessizce ayrıştı"


def test_onbellekteki_kesik_dosya_yeniden_indirilir(tmp_path, sahte_ag):
    cagri = sahte_ag(b"x" * 100)
    hedef = tmp_path / "2020-09-15.pcap.gz"
    hedef.write_bytes(b"y" * 10)              # önceki turdan kalan yarım gz
    pilot.indir("http://ornek/ham.gz", hedef, 100)
    assert len(cagri) == 1 and hedef.read_bytes() == b"x" * 100


# ------------------------------------------------------- TSK-087: işçi çökmesi dayanıklılığı

class _SahteSurec:
    """subprocess.Popen yerine: rc ve çıktı önceden planlanır, olay defteri sıra tutar."""

    def __init__(self, gun: str, rc: int, cikti: str, olaylar: list[str]):
        self.gun, self.returncode, self._cikti, self._olaylar = gun, rc, cikti, olaylar

    def communicate(self):
        self._olaylar.append(f"topla:{self.gun}")
        return self._cikti, None


@pytest.fixture
def gd_tezgah(tmp_path, monkeypatch):
    """geridolum.py'yi tmp KOK'a ve sahte Popen'a bağlar: gerçek /opt/veri, ağ, obs YOK."""

    def kur(plan: dict[str, list[tuple[int, str]]], turlar: list[list[str]]):
        (tmp_path / "tick").mkdir(parents=True, exist_ok=True)
        (tmp_path / "pilot.py").write_text("# sahte pilot\n")
        (tmp_path / "kapsam.txt").write_text("AAPL\n")
        monkeypatch.setattr(gd, "KOK", tmp_path)
        monkeypatch.setattr(gd, "PILOT", tmp_path / "pilot.py")
        monkeypatch.setattr(gd, "KAPSAM", tmp_path / "kapsam.txt")
        monkeypatch.setattr(gd, "PY", tmp_path / "python")
        monkeypatch.setattr(gd, "tick_bayt", lambda: 0)
        monkeypatch.setattr(gd, "bos_bayt", lambda: 10 ** 12)
        kalan_turlar = [list(t) for t in turlar]
        monkeypatch.setattr(gd, "sonraki_gunler", lambda n, done: kalan_turlar.pop(0))
        olaylar: list[str] = []

        def popen(argv, **kw):
            g = argv[argv.index("--gun") + 1]
            olaylar.append(f"baslat:{g}")
            rc, cikti = plan[g].pop(0)
            return _SahteSurec(g, rc, cikti, olaylar)

        monkeypatch.setattr(gd.subprocess, "Popen", popen)
        return olaylar, tmp_path

    return kur


def test_bir_isci_ikinci_denemede_gecer_kosum_yesil(gd_tezgah, capsys):
    olaylar, _ = gd_tezgah(
        plan={"2020-01-03": [(1, "Traceback\nEOFError: Compressed file ended before the "
                                 "end-of-stream marker was reached\n"),
                             (0, "OZET gun=2020-01-03 mesaj=9\n")],
              "2020-01-02": [(0, "OZET gun=2020-01-02 mesaj=9\n")]},
        turlar=[["2020-01-03", "2020-01-02"], []])
    rc = gd.main()
    cikti = capsys.readouterr().out
    assert rc == 0, cikti
    assert olaylar.count("baslat:2020-01-03") == 2, olaylar
    assert "1 gün 1. denemede düştü" in cikti, cikti
    assert "1 gün 2. denemede geçti" in cikti, cikti
    assert "0 gün kaldı" in cikti, cikti


def test_iki_kez_dusen_gun_kosumu_kirmizi_birakir_ve_ozet_cikar(gd_tezgah, capsys):
    olaylar, _ = gd_tezgah(
        plan={"2020-01-03": [(1, "KIRMIZI: kesik indirme 2020-01-03.pcap.gz 12/34 bayt\n")] * 2,
              "2020-01-02": [(0, "OZET gun=2020-01-02\n")]},
        turlar=[["2020-01-03", "2020-01-02"]])
    rc = gd.main()
    cikti = capsys.readouterr().out
    assert rc == 1, cikti
    assert olaylar.count("baslat:2020-01-03") == 2, olaylar
    assert "1 gün 1. denemede düştü" in cikti and "1 gün kaldı" in cikti, cikti
    assert "kesik indirme" in cikti, cikti      # TSK-107 mesajı özette sınıflanır


def test_oteki_iscinin_isi_kesilmez_ve_yeniden_deneme_o_sururken_baslar(gd_tezgah, capsys):
    olaylar, _ = gd_tezgah(
        plan={"2020-01-03": [(1, "Traceback\nEOFError\n"), (0, "OZET\n")],
              "2020-01-02": [(0, "OZET gun=2020-01-02\n")]},
        turlar=[["2020-01-03", "2020-01-02"], []])
    assert gd.main() == 0
    cikti = capsys.readouterr().out
    assert "bitti: 2020-01-02" in cikti, "öteki işçinin bitmiş işi yutuldu: " + cikti
    yeniden = [i for i, o in enumerate(olaylar) if o == "baslat:2020-01-03"][1]
    assert yeniden < olaylar.index("topla:2020-01-02"), olaylar


def test_kalici_sinifta_da_bir_kez_yeniden_denenir_ayrim_yalniz_mesajda(gd_tezgah, capsys):
    """Sınıf rc'den ÖLÇÜLEMEZ: kalıcı görünen arıza da bir kez denenir; ayrım mesajdadır."""
    olaylar, _ = gd_tezgah(
        plan={"2020-01-03": [(1, "KeyError: 'sembol'\n"), (0, "OZET\n")],
              "2020-01-02": [(0, "OZET\n")]},
        turlar=[["2020-01-03", "2020-01-02"], []])
    assert gd.main() == 0
    cikti = capsys.readouterr().out
    assert olaylar.count("baslat:2020-01-03") == 2, olaylar
    assert "sınıf bilinmiyor" in cikti, cikti


def test_hist_bos_gun_yeniden_denenmez_gecilen_defteri_degismez(gd_tezgah, capsys):
    """Defter yazımı (gecilen.jsonl) TSK-087'de değişmedi: boş-gün çökme SAYILMAZ."""
    olaylar, kok = gd_tezgah(
        plan={"2019-06-03": [(1, "KIRMIZI: HIST API 2019-06-03 için boş döndü (HTTP 404)\n")],
              "2020-01-02": [(0, "OZET\n")]},
        turlar=[["2019-06-03", "2020-01-02"], []])
    assert gd.main() == 0
    satirlar = (kok / "tick" / "gecilen.jsonl").read_text().splitlines()
    assert len(satirlar) == 1 and json.loads(satirlar[0])["gun"] == "2019-06-03"
    assert olaylar.count("baslat:2019-06-03") == 1, "boş-gün yeniden denendi"
