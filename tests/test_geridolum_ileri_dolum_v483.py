"""TSK-188 — İLERİ dolum çivileri: tick arşivi 2026-09-03'te durdu, İKİ kök neden (ölçüm
2026-09-13, A1 journal + defter sayımı; sürücü `deploy/oracle-a1/geridolum.py`).

KÖK NEDEN 1 — "taze-boş" gün o koşumda BİR DAHA denenmiyordu: atlanan günler bir SET'ti.
Tek koşum (PID 306299) 09-05→09-10 günlerce sürdü; her yeni iş günü 00:0xZ'de bir kez denendi,
IEX pcap ~09:20Z'de yayımlandığı için "boş döndü" cevabı geldi, gün sete girdi ve o koşum onu
bir daha AÇMADI. Kalıcı kayıt yok (gecilen.jsonl'de değil) — yani gün "atlanmış" da sayılmadı,
sadece kayboldu. Çivi: süre dolunca (TAZE_YENIDEN_SN) aynı koşumda YENİDEN denenir.

KÖK NEDEN 2 — 120 GB tavanı İLERİ günleri de kesiyordu: tavan kontrolü gün SEÇİMİNDEN önceydi
ve koşum gün seçmeden çıkıyordu ("TAVAN … çıkılıyor"). Operatörün 09-12 kararı "geri dolum
dursun" idi; ileri (T-1) dolumun durması o kararın İSTENMEYEN yan etkisiydi. Çivi: tavan yalnız
GERİ günleri keser; ileri günler yalnız DISK_PAYI_BAYT kapısına tabidir.

TUR 2 (Rol-1 kararı 2026-09-14) — "İLERİ GÜN" TANIMI ÖLÇÜM DEĞİL SABİTTİR: ilk sürüm sınırı
"defterin en büyük günü" diye ÖLÇÜYORDU; T-1 işlendiği an tepe oraya taşınıyor ve arada kalan
09-04..T-2 "geri" sayılıp tavanla kesiliyordu — koşum ne kadar sürerse sürsün boşluğun yalnız
en yeni ISCI günü doluyordu. Yeni sözleşme: `ILERI_PENCERE_BASI = 2026-09-04` (son arşiv günü
09-03 + 1) ve `ileri_gun(g) = g >= ILERI_PENCERE_BASI`; defter tanımın girdisi DEĞİLDİR.
Bu dosyanın iki çivisi (`…TUM_eksik_gunler…`, `…KESINTILI_kosumda…`) tam olarak eski ÖLÇÜM
tanımını ısırır — ikisi de o tanımla KIRMIZI olur.

TEZGAH TEK KAYNAKTAN: modül (`gd`) ve sahte süreç sınıfı v377 çivisinden İTHAL edilir
(test_geridolum_dayaniklilik_v377). Kopyalansaydı iki tezgah sessizce ayrışırdı — ve bu dosya
"yeşil" derken v377'nin ölçtüğü sürücüden BAŞKA bir şeyi ölçüyor olurdu. Gerçek /opt/veri, ağ,
obs ve saat YOK: KOK tmp_path, Popen sahte, saat sahte.

TEZGAHIN v377'DEN FARKI (ikisi de bilerek): (a) sahte işçi SÜRE harcar — "altı saat sonra"
ancak ilerleyen bir saatle ölçülebilir; (b) başarılı işçi manifest.jsonl'e yazar (canlıda pilot
yazar) — defter ilerlemezse koşum hiç bitmez ve `done` kümesi hiç büyümezdi. `sonraki_gunler`
stub'ı `done` kümesini GERÇEKTEN süzer: bu dosyanın ölçtüğü şey tam olarak main'in o kümeye ne
koyduğudur (v377'nin stub'ı sabit tur listesi döndürür, done'a bakmaz).
"""
from __future__ import annotations

import collections
import datetime as dt
import inspect
import json

import pytest

from tests.test_geridolum_dayaniklilik_v377 import _SahteSurec, gd

_Tezgah = collections.namedtuple("_Tezgah", "olaylar gorulen_done saat kok")

TAVAN_USTU = 121 * 1000**3      # TAVAN_BAYT (120 GB) üstü — kapı "aşıldı" tarafında ölçülür


class _ZamanliSurec(_SahteSurec):
    """v377'nin sahte süreci + iki canlı yan etki: süre geçer, başarı deftere düşer.

    Süre `saat` listesinde taşınır (sahte monotonic); manifest yazımı canlıda pilotundur —
    burada sahtelenmesi, sürücünün "işlenmiş" kümesini deftere sorduğunu ölçmek içindir."""

    def __init__(self, gun: str, rc: int, cikti: str, olaylar: list[str],
                 saat: list[float], is_sn: float, tick_kok) -> None:
        super().__init__(gun, rc, cikti, olaylar)
        self._saat, self._is_sn, self._tick_kok = saat, is_sn, tick_kok

    def communicate(self):
        self._saat[0] += self._is_sn
        if self.returncode == 0:
            with (self._tick_kok / "manifest.jsonl").open("a") as f:
                f.write(json.dumps({"gun": self.gun}) + "\n")
        return super().communicate()


@pytest.fixture
def ileri_tezgah(tmp_path, monkeypatch):
    """`plan` gün → [(rc, çıktı), …]; `havuz` sürücünün seçebileceği günler (yeniden → eski)."""

    def kur(plan: dict[str, list[tuple[int, str]]], havuz: list[str], *,
            manifest: tuple[str, ...] = (), tick: int = 0, bos: int = 10 ** 12,
            is_sn: float = 0.0) -> _Tezgah:
        tick_kok = tmp_path / "tick"
        tick_kok.mkdir(parents=True, exist_ok=True)
        (tmp_path / "pilot.py").write_text("# sahte pilot\n")
        (tmp_path / "kapsam.txt").write_text("AAPL\n")
        if manifest:
            (tick_kok / "manifest.jsonl").write_text(
                "".join(json.dumps({"gun": g}) + "\n" for g in manifest))
        monkeypatch.setattr(gd, "KOK", tmp_path)
        monkeypatch.setattr(gd, "PILOT", tmp_path / "pilot.py")
        monkeypatch.setattr(gd, "KAPSAM", tmp_path / "kapsam.txt")
        monkeypatch.setattr(gd, "PY", tmp_path / "python")
        monkeypatch.setattr(gd, "tick_bayt", lambda: tick)
        monkeypatch.setattr(gd, "bos_bayt", lambda: bos)
        saat = [0.0]
        monkeypatch.setattr(gd, "_simdi_sn", lambda: saat[0])
        olaylar: list[str] = []
        gorulen_done: list[list[str]] = []

        def sonraki(n: int, done: set[str]) -> list[str]:
            gorulen_done.append(sorted(done))
            return [g for g in havuz if g not in done][:n]

        monkeypatch.setattr(gd, "sonraki_gunler", sonraki)

        def popen(argv, **kw):
            g = argv[argv.index("--gun") + 1]
            olaylar.append(f"baslat:{g}")
            rc, cikti = plan[g].pop(0)
            return _ZamanliSurec(g, rc, cikti, olaylar, saat, is_sn, tick_kok)

        monkeypatch.setattr(gd.subprocess, "Popen", popen)
        return _Tezgah(olaylar, gorulen_done, saat, tmp_path)

    return kur


def _dun() -> str:
    """Taze-boş dalı YAŞ ölçer (TAZE_GUN): gün bugüne göre seçilmeli, sabit yazılamaz."""
    return (dt.date.today() - dt.timedelta(days=1)).isoformat()


# ------------------------------------------------- KÖK NEDEN 1: taze-boş yeniden deneme

def test_taze_bos_gun_SURE_DOLUNCA_ayni_kosumda_yeniden_denenir(ileri_tezgah, capsys):
    g = _dun()
    t = ileri_tezgah(
        plan={g: [(1, f"KIRMIZI: HIST API {g} için boş döndü (HTTP 404)\n"),
                  (0, f"OZET gun={g} mesaj=9\n")]},
        havuz=[g], is_sn=gd.TAZE_YENIDEN_SN + 60)
    assert gd.main() == 0
    cikti = capsys.readouterr().out
    assert t.olaylar.count(f"baslat:{g}") == 2, t.olaylar
    assert "taze-boş" in cikti, cikti
    assert "PENCERE-TAMAM" in cikti, cikti
    assert t.gorulen_done[1] == [], t.gorulen_done   # süre dolmuş gün done'dan ÇIKAR


def test_taze_bos_gun_SURE_DOLMADAN_yeniden_DENENMEZ(ileri_tezgah, capsys):
    """Karşı yön: bekleme olmasaydı sürücü aynı günü dakikalar içinde döngüye sokardı."""
    g = _dun()
    t = ileri_tezgah(
        plan={g: [(1, f"KIRMIZI: HIST API {g} için boş döndü (HTTP 404)\n"),
                  (0, f"OZET gun={g}\n")]},
        havuz=[g], is_sn=gd.TAZE_YENIDEN_SN - 60)
    assert gd.main() == 0
    cikti = capsys.readouterr().out
    assert t.olaylar.count(f"baslat:{g}") == 1, t.olaylar
    assert t.gorulen_done[1] == [g], t.gorulen_done  # süre dolmamış gün done'DA
    assert "PENCERE-TAMAM" in cikti, cikti


def test_taze_bekleyen_SINIRI_esitte_yeniden_dener():
    """Sınır AÇIK yazılır: `simdi - ts < TAZE_YENIDEN_SN` → eşitlikte gün SERBESTTİR."""
    atlanan = {"2026-09-12": 100.0, "2026-09-11": 100.0}
    assert gd.taze_bekleyen(atlanan, 100.0) == {"2026-09-12", "2026-09-11"}
    assert gd.taze_bekleyen(atlanan, 100.0 + gd.TAZE_YENIDEN_SN - 1) == {"2026-09-12",
                                                                        "2026-09-11"}
    assert gd.taze_bekleyen(atlanan, 100.0 + gd.TAZE_YENIDEN_SN) == set()
    assert gd.taze_bekleyen({}, 10 ** 9) == set()


def test_kalici_defter_davranisi_DEGISMEDI_eski_bos_gun_beklemez(ileri_tezgah, capsys):
    """Yaşı TAZE_GUN'den büyük boş gün gecilen.jsonl'e yazılır ve bekleme kuyruğuna GİRMEZ —
    kalıcı atlama ile koşum-içi bekleme iki AYRI sınıftır (v377 o dalı ayrıca ölçer).

    AYRIMI ÖLÇEN KURULUM: saat bekleme süresinin ÖTESİNE atlar. Gün bekleme kuyruğunda olsaydı
    ikinci turda yeniden denenirdi; kalıcı defterde olduğu için denenmez."""
    eski = "2019-06-03"
    t = ileri_tezgah(
        plan={eski: [(1, f"KIRMIZI: HIST API {eski} için boş döndü (HTTP 404)\n"),
                     (0, "OZET\n")]},
        havuz=[eski], is_sn=gd.TAZE_YENIDEN_SN + 60)
    assert gd.main() == 0
    satirlar = (t.kok / "tick" / "gecilen.jsonl").read_text().splitlines()
    assert len(satirlar) == 1 and json.loads(satirlar[0])["gun"] == eski
    assert t.olaylar.count(f"baslat:{eski}") == 1, t.olaylar
    assert t.gorulen_done[1] == [eski], t.gorulen_done      # kalıcı defterden geldi


# ------------------------------------------------------- KÖK NEDEN 2: tavan yalnız GERİYE

PENCERE_ONCESI = "2026-09-03"       # son arşiv günü — GERİ pencerenin tepesi
PENCERE_BASI = "2026-09-04"         # ILERI_PENCERE_BASI — CANLI pencerenin ilk günü
# 09-04..09-11 iş günleri, yeniden → eskiye (09-05/09-06 hafta sonu). ELLE yazılır: gerçek
# `sonraki_gunler` T-1'e bağlıdır ve bu çivi yarın başka bir şey ölçerdi.
ILERI_BOSLUK = ["2026-09-11", "2026-09-10", "2026-09-09", "2026-09-08", "2026-09-07",
                "2026-09-04"]
GERI_KUYRUK = ["2026-09-02", "2026-09-01"]


def test_ileri_gun_SABIT_pencere_basindan_itibaredir_ve_deftere_BAKMAZ():
    """Sınır KAPSAYICI ve deftersizdir: 09-04 ileri, 09-03 (son arşiv günü) değil.

    İmza da sözleşmenin parçası: defter argümanı KALKTI — iki kaynak (sabit + defter) olsaydı
    biri sessizce ötekinden ayrışırdı (tek-kaynak yasası)."""
    assert gd.ileri_gun(PENCERE_BASI) is True
    assert gd.ileri_gun(PENCERE_ONCESI) is False
    assert gd.ileri_gun("2026-09-14") is True
    assert gd.ileri_gun("2020-01-02") is False
    assert set(inspect.signature(gd.ileri_gun).parameters) == {"g"}


def test_tavan_dolu_iken_PENCERE_BASINA_kadar_TUM_eksik_gunler_islenir(ileri_tezgah, capsys):
    """Boşluğun TAMAMI dolar — ISCI=2'şer, döngü boyunca; 09-03 ve öncesi işlenmez.

    ESKİ ÖLÇÜM TANIMINI ISIRAN ÇİVİ: "ileri = defterin en büyük gününden yeni" olsaydı ilk tur
    09-11/09-10'u işler, defterin tepesi 09-11'e taşınır ve kalan dört gün GERİ sayılıp tavanla
    kesilirdi — boşluk asla kapanmazdı."""
    t = ileri_tezgah(
        plan={g: [(0, f"OZET gun={g}\n")] for g in ILERI_BOSLUK + GERI_KUYRUK},
        havuz=ILERI_BOSLUK + [PENCERE_ONCESI] + GERI_KUYRUK,
        manifest=(PENCERE_ONCESI,), tick=TAVAN_USTU)
    assert gd.main() == 0
    cikti = capsys.readouterr().out
    baslatilan = [o for o in t.olaylar if o.startswith("baslat:")]
    assert baslatilan == [f"baslat:{g}" for g in ILERI_BOSLUK], t.olaylar
    assert not any(g in t.olaylar for g in
                   [f"baslat:{x}" for x in GERI_KUYRUK + [PENCERE_ONCESI]]), t.olaylar
    # 6 gün / ISCI=2 = 3 iş turu + geri kuyrukta kesilen 4. tur
    assert len(t.gorulen_done) == len(ILERI_BOSLUK) // gd.ISCI + 1, t.gorulen_done
    assert "TAVAN: 121.0 GB >= 120 GB — çıkılıyor" in cikti, cikti


def test_KESINTILI_kosumda_defterin_tepesi_ILERI_tanimini_KAYDIRMAZ(ileri_tezgah, capsys):
    """Kesinti simülasyonu: defterde yalnız 09-11 var, 09-04..09-10 EKSİK (koşum kesildi).

    Eski ÖLÇÜM tanımında 09-10 ve 09-04 "defterin en büyük gününden eski"dir ve tavan ikisini
    de keserdi; sabit tanımda ikisi de CANLI penceredir ve dolar. 09-03 yine geri kalır."""
    t = ileri_tezgah(
        plan={"2026-09-10": [(0, "OZET gun=2026-09-10\n")],
              PENCERE_BASI: [(0, f"OZET gun={PENCERE_BASI}\n")]},
        havuz=["2026-09-10", PENCERE_BASI, PENCERE_ONCESI],
        manifest=("2026-09-11",), tick=TAVAN_USTU)
    assert gd.main() == 0
    cikti = capsys.readouterr().out
    assert t.olaylar.count("baslat:2026-09-10") == 1, t.olaylar
    assert t.olaylar.count(f"baslat:{PENCERE_BASI}") == 1, t.olaylar
    assert f"baslat:{PENCERE_ONCESI}" not in t.olaylar, t.olaylar
    assert "TAVAN aşıldı: yalnız ileri günler dolduruluyor" in cikti, cikti


def test_yalniz_PENCERE_ONCESI_gunler_kalinca_tavan_kosumu_KESER(ileri_tezgah, capsys):
    """Tavanın ASIL işi duruyor: geri dolum penceresi (09-03 ve öncesi) kesilir, iş AÇILMAZ.

    Operatörün 09-12 kararı ("geri dolum dursun") burada yaşar — gevşetilen tek şey ileri
    penceredir."""
    t = ileri_tezgah(plan={PENCERE_ONCESI: [(0, "OZET\n")]},
                     havuz=[PENCERE_ONCESI] + GERI_KUYRUK, tick=TAVAN_USTU)
    assert gd.main() == 0
    cikti = capsys.readouterr().out
    assert t.olaylar == [], t.olaylar
    assert "TAVAN: 121.0 GB >= 120 GB — çıkılıyor" in cikti, cikti
    assert (t.kok / "tick" / "TAVAN-DOLDU").exists()


def test_tavan_dolu_iken_ILERI_gun_islenir_GERI_gun_ISLENMEZ(ileri_tezgah, capsys):
    t = ileri_tezgah(
        plan={PENCERE_BASI: [(0, f"OZET gun={PENCERE_BASI}\n")]},
        havuz=[PENCERE_BASI, "2026-09-02"], manifest=(PENCERE_ONCESI,), tick=TAVAN_USTU)
    assert gd.main() == 0
    cikti = capsys.readouterr().out
    assert t.olaylar.count(f"baslat:{PENCERE_BASI}") == 1, t.olaylar
    assert "baslat:2026-09-02" not in t.olaylar, t.olaylar
    assert "TAVAN aşıldı: yalnız ileri günler dolduruluyor" in cikti, cikti
    assert "TAVAN: 121.0 GB >= 120 GB — çıkılıyor" in cikti, cikti   # geri dal mesajı AYNEN
    assert (t.kok / "tick" / "TAVAN-DOLDU").exists()


def test_tavan_ASILMAMISKEN_ileri_ve_geri_gun_ESKI_SIRAYLA_islenir(ileri_tezgah, capsys):
    """Bit-özdeşlik dalı: tavan altındayken ayrım GÖRÜNMEZ — iki gün de, aynı sırayla."""
    t = ileri_tezgah(
        plan={PENCERE_BASI: [(0, "OZET\n")], "2026-09-02": [(0, "OZET\n")]},
        havuz=[PENCERE_BASI, "2026-09-02"], manifest=(PENCERE_ONCESI,))
    assert gd.main() == 0
    cikti = capsys.readouterr().out
    assert t.olaylar[:2] == [f"baslat:{PENCERE_BASI}", "baslat:2026-09-02"], t.olaylar
    assert "TAVAN" not in cikti, cikti
    assert not (t.kok / "tick" / "TAVAN-DOLDU").exists()


def test_ILERI_gunde_DISK_PAYI_kapisi_hala_KIRMIZI(ileri_tezgah, capsys):
    """Tavan gevşedi, disk payı GEVŞEMEDİ: ham gz geçicisi sığmıyorsa iş açılmaz (ENOSPC)."""
    t = ileri_tezgah(
        plan={PENCERE_BASI: [(0, "OZET\n")]}, havuz=[PENCERE_BASI],
        manifest=(PENCERE_ONCESI,), tick=TAVAN_USTU, bos=1 * 1000**3)
    assert gd.main() == 1
    cikti = capsys.readouterr().out
    assert t.olaylar == [], t.olaylar
    assert "KIRMIZI: disk payı" in cikti, cikti
    assert "TAVAN aşıldı: yalnız ileri günler dolduruluyor" in cikti, cikti


def test_operator_esikleri_DEGISMEDI():
    """Operatör kararı 09-12 (geri dolum durur): eşik kararı AYRI kalemdir, bu tur onu
    değiştirmez — sabitler çiviyle sabitlenir ki "biraz yükseltelim" sessizce olmasın.

    ILERI_PENCERE_BASI de buradadır: kayması boşluğun bir kısmını sessizce tavana geri verir
    (pencere başı bir OPERATÖR sınırıdır, bir ayar değil)."""
    assert gd.TAVAN_BAYT == 120 * 1000**3
    assert gd.TAZE_GUN == 5
    assert gd.ISCI == 2
    assert gd.TAZE_YENIDEN_SN == 6 * 3600
    assert gd.ILERI_PENCERE_BASI == dt.date(2026, 9, 4)
