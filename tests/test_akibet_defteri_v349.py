"""ÖNERİ AKIBET DEFTERİ — `ops/akibet.py` — v349 (2026-08-31), bölüm A-D (bölüm E T2'nindir)

NEDEN VAR. Plan: docs/superpowers/plans/2026-08-31-akibet-defteri.md; karar kaydı: ROADMAP §7
"AKIBET DEFTERİ TASARIM KARARLARI". Dört kaynaktan doğan önerilerin doğum→karar→sonuç zinciri
hiçbir yerde tutulmuyordu; sef her brifingde aynı "N yeni öneri"yi tekrarlıyordu çünkü karara
bağlanmış bir önerinin bunu SÖYLEYECEK hiçbir yeri yoktu.

EMSAL: `ops/filo.py` + `tests/test_filo_araci_v348.py` — desen BİREBİR izlenir: saf-kurucu + tek
alt-süreç noktası (`filo._ssh_kos`/`filo._kos`, ÖDÜNÇ alınır — akibet.py kendi `subprocess.run`
çağrısı YAPMAZ; R1 düzeltmesinde kendi `_uzak_kos` kopyası kaldırılıp doğrudan `filo._ssh_kos`
çağrılmaya başlandı — Kü3), kimlik CLI>env>sabit (`filo`den ithal), `--komut-yaz` (BASAR/KOŞMAZ),
ssh nişancı deseni (gerçek ssh testte HİÇ çağrılmaz, davranış ÖLÇÜLÜR).

R1 DÜZELTME TURU (inceleme 2026-08-31, task-1-review.md) bu dosyaya eklenen/değişen testler:
K1 (okunamayan/boş defter ayrımı) · Ö1 (`sonuc` satırlarının `listele`de görünmesi) · Ö2 (AKB id
tahsisinin flock içine alınması, `oneri_ekleme_komutu`) · Ö3 (`--komut-yaz` BASAR yarısının
`karar`/`sonuc` dallarında da ölçülmesi) · Ö4 (ONERI_KAYNAKLARI/KARAR_VERENLER ayrımı) · Ö5
(gerçek zaman kıyası) · Ö6 (naive damga + `main`'in dar hata yakalaması).

ÇİFT NİŞANCI SINIFI (bu dosyaya özgü):
  · `_nisanci`       — filo'nun İZ BIRAKAN basit betiği: "ssh hiç çağrılmadı" negatifini ölçer.
  · `_gercek_nisanci` — GERÇEK bir `sh -c` çalıştıran Python betiği: canlı `/opt/meridian/...`
    yolunu tmp_path altında bir dosyaya METİN-DEĞİŞİMİYLE yönlendirip komutu GERÇEKTEN koşar.
    Böylece `flock`+`printf`+`tail` zincirinin ÇİFT `shlex.quote` kaçışı ŞEKLİ değil DAVRANIŞI
    ölçülür — sahte-yeşil riski (yalnız dize arayan bir çivi) burada yoktur.
"""
from __future__ import annotations

import ast
import json
import os
import pathlib
import shutil
import subprocess
import sys
import types

import pytest

KOK = pathlib.Path(__file__).resolve().parent.parent
BETIK = KOK / "ops/akibet.py"

from tests.conftest import betikten_modul_yukle  # noqa: E402


def _yukle():
    assert BETIK.exists(), f"{BETIK} YOK"
    return betikten_modul_yukle(BETIK, "akibet")


def _cli(*bayrak: str, ort: dict | None = None) -> subprocess.CompletedProcess:
    """GİRİŞ NOKTASI: betiğin KENDİSİ (`main([...])` değil) — argparse sys.argv'yi görmüyorsa
    (v348'in `--uygula` sessiz-yok-sayma vakası) bu çağrı yakalar."""
    return subprocess.run([sys.executable, str(BETIK), *bayrak],
                          capture_output=True, text=True,
                          env={**os.environ, **(ort or {})})


def _ithaller(agac) -> set[str]:
    adlar = set()
    for d in ast.walk(agac):
        if isinstance(d, ast.Import):
            adlar.update(a.name.split(".")[0] for a in d.names)
        elif isinstance(d, ast.ImportFrom) and d.module and d.level == 0:
            adlar.add(d.module.split(".")[0])
        elif isinstance(d, ast.ImportFrom) and d.level:
            adlar.add("<göreli>")
    return adlar


def _nisanci(tmp_path) -> tuple[dict, pathlib.Path]:
    """PATH'e GERÇEK bir `ssh` betiği koyar (mock değil, ayrı süreç). Çağrılırsa iz bırakır."""
    kutu = tmp_path / "bin"
    kutu.mkdir()
    iz = tmp_path / "ssh-cagrildi.iz"
    sh = kutu / "ssh"
    sh.write_text(f'#!/bin/sh\nprintf "%s\\n" "$*" >> {iz}\nexit 0\n', encoding="utf-8")
    sh.chmod(0o755)
    return {"PATH": str(kutu)}, iz


def _satir_yaz(yol: pathlib.Path, satirlar: list[dict]) -> None:
    yol.write_text("\n".join(json.dumps(s, ensure_ascii=False, sort_keys=True)
                             for s in satirlar) + ("\n" if satirlar else ""), encoding="utf-8")


def _flock_yolu(tmp_path) -> str:
    """`flock` (util-linux) geliştirme makinesinde (macOS/Darwin) YOKTUR — A1 Ubuntu'da vardır.
    GERÇEK kilitleme semantiğine güveniyoruz (GNU coreutils, test edilmiş bir dış araç); burada
    ölçülmek istenen KENDİ `shlex.quote` kaçışımız ve printf/tail zinciridir. `flock` PATH'te
    VARSA GERÇEĞİ kullanılır (daha sadık); YOKSA kilit dosyasını atlayıp geri kalan argümanı
    çalıştıran bir SAPLAMA PATH'e eklenir — davranış ölçümü ETKİLENMEZ, yalnız gerçek kilitleme
    KAPSAM DIŞI kalır (zaten tek-süreçli bir testte anlamlı bir kilit çekişmesi YOKTUR)."""
    if shutil.which("flock"):
        return os.environ["PATH"]
    kutu = tmp_path / "flock-saplama"
    kutu.mkdir(exist_ok=True)
    saplama = kutu / "flock"
    saplama.write_text('#!/bin/sh\nshift\nexec "$@"\n', encoding="utf-8")
    saplama.chmod(0o755)
    return f"{kutu}:{os.environ['PATH']}"


_GUARD_ISARET = "@@GERCEK-SSH-YAKALANDI-BEKLENMEYEN-COAGRI@@"


@pytest.fixture(autouse=True)
def _sistemik_ssh_kilidi(monkeypatch, tmp_path_factory):
    """SİSTEMİK KİLİT (Y1, R2 yeniden-inceleme 2026-08-31 — güvenlik olayının tekrarını KAPATIR).

    R1 raporundaki olay ("test_d18" `ort=` vermeyi unuttu → GERÇEK A1'e yazdı) ve R2'nin bulduğu
    aynı sınıf boşluk (`test_j3b`) tek tek yamalarla kapatıldı, ama "tekil çağrıları yamamak"
    yeterli DEĞİL — bir SONRAKİ test aynı hatayı yeniden yapabilir. Bu yüzden bu dosyadaki HER
    TEK test (autouse), PATH'in EN BAŞINA gerçek `/usr/bin/ssh`i HER ZAMAN gölgeleyen bir sahte
    `ssh` betiği eklenmiş ortamda koşar — bir test `ort=` vermeyi UNUTSA BİLE artık GERÇEK ssh'a
    hiçbir yol YOKTUR.

    Kendi `ort={"PATH": ...}`ını veren testler (`_nisanci`/`_gercek_nisanci` ile) bu korumanın
    YERİNE kendi sahte-ssh'larını geçirir — bu KASITLI ve ZARARSIZ: `_cli`de `**ort`,
    `**os.environ`dan SONRA birleştiği için testin KENDİ (doğru, amaca özel) PATH'i kullanılır;
    çakışma değil devirdir.

    Beklenmeyen bir çağrı YAKALANIRSA sessizce "başarılı" TAKLİT ETMEZ: `_GUARD_ISARET` ile
    işaretli bir satırı hem STDERR'e basar hem bir iz dosyasına yazar, rc=113 ile döner — kaçak
    GÖRÜNÜR olsun, hiçbir test onu farketmeden "yeşil" geçmesin (rc=0 dönseydi bazı testler
    bunu gerçek bir başarı sanabilirdi).

    `monkeypatch.undo()` BURADA ASLA ÇAĞRILMAZ (CLAUDE.md: autouse fixture'ları da geri alırdı) —
    `monkeypatch` fixture'ının KENDİ otomatik (per-test) teardown'ına güvenilir."""
    kutu = tmp_path_factory.mktemp("sistemik-ssh-kilidi")
    iz = kutu / "GERCEK_SSH_YAKALANDI.iz"
    sh = kutu / "ssh"
    sh.write_text(
        "#!/bin/sh\n"
        f'echo "{_GUARD_ISARET}: $*" >&2\n'
        f'printf "%s\\n" "$*" >> {iz}\n'
        "exit 113\n",
        encoding="utf-8")
    sh.chmod(0o755)
    monkeypatch.setenv("PATH", f"{kutu}{os.pathsep}{os.environ.get('PATH', '')}")


# ═══════════════════════════════════════════════════════════════════════════
#  A. KOMUT-SATIRI SÖZLEŞMESİ + YAPISAL
# ═══════════════════════════════════════════════════════════════════════════

def test_a1_YARDIM_DORT_ALT_KOMUTU_ADIYLA_GOSTERIR():
    r = _cli("--help")
    assert r.returncode == 0, f"--help düştü: {r.returncode}\n{r.stderr}"
    for komut in ("listele", "oneri", "karar", "sonuc"):
        assert komut in r.stdout, f"`{komut}` --help metninde YOK:\n{r.stdout}"


def test_a2_CIKIS_KODLARI_YARDIMDA_BEYANLI():
    r = _cli("--help")
    metin = r.stdout.replace(" = ", "=").replace(" =", "=")
    for beyan in ("0", "1", "2"):
        assert f"{beyan}=" in metin, f"çıkış kodu {beyan} --help'te beyan edilmiyor:\n{metin}"


def test_a3_TANIMSIZ_ALT_KOMUT_KULLANIM_HATASI_2():
    r = _cli("boyle-bir-komut-yok")
    assert r.returncode == 2, f"beklenen 2, gelen {r.returncode}\n{r.stdout}{r.stderr}"


@pytest.mark.parametrize("komut", ["listele", "oneri", "karar", "sonuc"])
def test_a4_HER_ALT_KOMUTUN_KENDI_YARDIMI_VAR(komut):
    r = _cli(komut, "--help")
    assert r.returncode == 0, f"{komut} --help düştü:\n{r.stderr}"
    assert len(r.stdout.strip()) > 40, f"{komut} --help boş sayılır:\n{r.stdout}"


def test_a5_GECERSIZ_KARAR_DEGERI_KULLANIM_HATASI_2(tmp_path):
    """`karar` pozisyonel argümanı `choices=` ile sınırlı — argparse KENDİSİ rc=2 verir.

    GÜVENLİK (R1 sonrası eklendi — bkz. test_d18 GÜVENLİK notu): bir `choices=` gevşemesi bu
    testi SESSİZCE gerçek ssh'a düşürebilir (tam da d18'in mutasyon turunda GERÇEKTEN olduğu
    gibi, gerçek A1'e yazdı). `_nisanci` savunma-derinliği için burada da zorunlu."""
    ort, iz = _nisanci(tmp_path)
    r = _cli("karar", "N00001", "boyle-bir-karar-yok", "--gerekce", "x" * 25,
             "--veren", "operator", ort=ort)
    assert not iz.exists(), f"argparse reddetmedi, ssh'a ulaşıldı: {iz.read_text(encoding='utf-8')!r}"
    assert r.returncode == 2, f"beklenen 2, gelen {r.returncode}\n{r.stdout}{r.stderr}"


def test_a6_GECERSIZ_KAYNAK_KULLANIM_HATASI_2(tmp_path):
    """GÜVENLİK: bkz. test_a5 — `--kaynak choices=` gevşemesi gerçek ssh'a sızabilir, `_nisanci`
    savunma-derinliği burada da zorunlu."""
    ort, iz = _nisanci(tmp_path)
    r = _cli("oneri", "bir öneri metni", "--kaynak", "boyle-bir-kaynak-yok", ort=ort)
    assert not iz.exists(), f"argparse reddetmedi, ssh'a ulaşıldı: {iz.read_text(encoding='utf-8')!r}"
    assert r.returncode == 2, f"beklenen 2, gelen {r.returncode}\n{r.stdout}{r.stderr}"


def test_a7_MERIDIAN_ITHAL_EDILMEZ():
    """`meridian` ithal edilseydi `meridian.obs` erişilebilir olurdu — bu araç pytest DIŞINDA,
    operatörün elinde koşar: canlı YEREL deftere yazardı (CLAUDE.md §2, 3 vaka 2026-08-30)."""
    agac = ast.parse(BETIK.read_text(encoding="utf-8"))
    ith = _ithaller(agac)
    assert "meridian" not in ith, f"meridian ithal ediliyor: {sorted(ith)}"
    assert "<göreli>" not in ith, f"göreli ithal var (paket bağı): {sorted(ith)}"


def test_a8_YALNIZ_STDLIB_VE_FILO():
    agac = ast.parse(BETIK.read_text(encoding="utf-8"))
    izinli = set(sys.stdlib_module_names) | {"filo"}
    disarda = _ithaller(agac) - izinli
    assert not disarda, f"stdlib/filo dışı ithal: {sorted(disarda)}"


def test_a9_KENDI_ALT_SURECI_YOK_FILO_ODUNC_ALINIR():
    """akibet.py `subprocess`u KENDİSİ ithal ETMEZ — tek alt-süreç noktası `filo._ssh_kos`
    (o da içeride `filo._kos`u çağırır) — üçüncü bir alt-süreç noktası tek-kaynak yasasını ihlal
    ederdi. R1 düzeltmesi (Kü3): eskiden akibet.py kendi `_uzak_kos` KOPYASINI taşıyordu (yalnız
    `filo._kos`a erişiyordu); şimdi `filo._ssh_kos`u DOĞRUDAN çağırıyor — kopya YOK."""
    agac = ast.parse(BETIK.read_text(encoding="utf-8"))
    assert "subprocess" not in _ithaller(agac), (
        "akibet.py kendi subprocess'ini ithal ediyor — filo._kos ÖDÜNÇ alınmalıydı")
    kaynak = BETIK.read_text(encoding="utf-8")
    assert "filo._ssh_kos(" in kaynak, "filo._ssh_kos hiç çağrılmıyor — alt-süreç nereden koşuyor?"
    assert "def _uzak_kos(" not in kaynak, (
        "akibet.py hâlâ kendi ssh-kos KOPYASINI taşıyor — filo._ssh_kos'un DOĞRUDAN çağrılması "
        "gerekiyordu (Kü3 düzeltmesi, inceleme 2026-08-31)")


def test_a10_SYS_PATH_INSERT_VE_IMPORT_FILO_DESENI():
    """Brief'in bağlayıcı deseni: `sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))`
    + `import filo` — ops/ paket olmadığı için göreli import yerine bu."""
    kaynak = BETIK.read_text(encoding="utf-8")
    assert "sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))" in kaynak, kaynak
    assert "import filo" in kaynak, kaynak


# ═══════════════════════════════════════════════════════════════════════════
#  B. `akibet_turet` — SAF ÇEKİRDEK
# ═══════════════════════════════════════════════════════════════════════════

def _n(id_, ts, oneri="bir gözlem") -> dict:
    return {"ts": ts, "id": id_, "hafta": "2026-W35", "alan": "x", "gozlem": "g",
            "oneri": oneri, "beklenen_etki": "e", "onerilen_olcum": "o"}


def _akb_dogum(id_, ts, kaynak="rol1", oneri="bir fikir") -> dict:
    return {"ts": ts, "olay": "oneri", "oneri_id": id_, "kaynak": kaynak, "oneri": oneri}


def _karar_satiri(id_, ts, karar="uygulandi", veren="operator", gerekce="x" * 25) -> dict:
    return {"ts": ts, "olay": "karar", "oneri_id": id_, "karar": karar, "karar_veren": veren,
            "gerekce": gerekce}


def test_b1_BOS_DEFTER_HERKES_ACIK():
    mod = _yukle()
    t = mod.akibet_turet([_n("N00001", "2026-08-01T00:00:00+00:00")], [],
                        "2026-08-31T00:00:00+00:00")
    assert [a["oneri_id"] for a in t["acik"]] == ["N00001"]
    assert t["sayilar"] == {"acik": 1, "uygulandi": 0, "reddedildi": 0, "ertelendi": 0}
    assert t["kararlar"] == []
    assert t["olculemeyen"] == []


def test_b2_YAS_TAM_GUN_DOGUMDAN_SIMDIYE():
    mod = _yukle()
    t = mod.akibet_turet([_n("N00001", "2026-08-01T00:00:00+00:00")], [],
                        "2026-08-31T12:00:00+00:00")
    assert t["acik"][0]["yas_gun"] == 30, t["acik"][0]


def test_b3_KARAR_ALAN_ONERI_ACIKTAN_DUSER():
    """AÇIK türetimi: karar alınca düşer — bu, akibet_turet'in EN ÖNEMLİ davranışı."""
    mod = _yukle()
    t = mod.akibet_turet(
        [_n("N00001", "2026-08-01T00:00:00+00:00"), _n("N00002", "2026-08-05T00:00:00+00:00")],
        [_karar_satiri("N00001", "2026-08-10T00:00:00+00:00", karar="uygulandi")],
        "2026-08-31T00:00:00+00:00")
    acik_id = [a["oneri_id"] for a in t["acik"]]
    assert acik_id == ["N00002"], acik_id
    assert t["sayilar"]["acik"] == 1
    assert t["sayilar"]["uygulandi"] == 1


@pytest.mark.parametrize("karar", ["uygulandi", "reddedildi", "ertelendi"])
def test_b4_HER_UC_KARAR_TIPI_DE_ACIKTAN_DUSURUR_AMA_SAYILIR(karar):
    """`ertelendi` AÇIK SAYILMAZ ama `sayilar`da görünür (plan md, BAĞLAYICI)."""
    mod = _yukle()
    t = mod.akibet_turet(
        [_n("N00001", "2026-08-01T00:00:00+00:00")],
        [_karar_satiri("N00001", "2026-08-10T00:00:00+00:00", karar=karar)],
        "2026-08-31T00:00:00+00:00")
    assert t["acik"] == [], f"{karar} açıkta KALDI: {t['acik']}"
    assert t["sayilar"][karar] == 1, t["sayilar"]
    assert t["sayilar"]["acik"] == 0


def test_b5_AKB_DOGUM_SATIRI_ACIGA_GIRER():
    mod = _yukle()
    t = mod.akibet_turet([], [_akb_dogum("AKB-0001", "2026-08-20T00:00:00+00:00",
                                        kaynak="operator", oneri="bir fikir")],
                        "2026-08-31T00:00:00+00:00")
    assert len(t["acik"]) == 1
    a = t["acik"][0]
    assert a["oneri_id"] == "AKB-0001" and a["kaynak"] == "operator" and a["ozet"] == "bir fikir"
    assert a["yas_gun"] == 11


def test_b6_SON_KARAR_GECERLI_DUZELTME_YENI_SATIRDIR():
    """Aynı oneri_id için SON karar satırı geçerlidir (plan: düzeltme = yeni satır, silme yok)."""
    mod = _yukle()
    t = mod.akibet_turet(
        [_n("N00001", "2026-08-01T00:00:00+00:00")],
        [_karar_satiri("N00001", "2026-08-05T00:00:00+00:00", karar="ertelendi"),
         _karar_satiri("N00001", "2026-08-10T00:00:00+00:00", karar="uygulandi")],
        "2026-08-31T00:00:00+00:00")
    assert t["sayilar"] == {"acik": 0, "uygulandi": 1, "reddedildi": 0, "ertelendi": 0}, t["sayilar"]
    assert len(t["kararlar"]) == 2, "TÜM tarihçe korunmalı, yalnız SON karar sayılır"


def test_b7_KARARLAR_TS_SIRALI_TUM_TARIHCE():
    mod = _yukle()
    t = mod.akibet_turet(
        [], [_karar_satiri("N00001", "2026-08-10T00:00:00+00:00"),
             _karar_satiri("N00002", "2026-08-05T00:00:00+00:00"),
             _karar_satiri("N00003", "2026-08-20T00:00:00+00:00")],
        "2026-08-31T00:00:00+00:00")
    assert [k["oneri_id"] for k in t["kararlar"]] == ["N00002", "N00001", "N00003"]


def test_b8_BOZUK_SATIR_DUSURULMEZ_OLCULEMEYENE_SAYILIR():
    """v347 emsali: bozuk satır sessizce `continue` ile YOK OLMAZ, POZİSYONU sayılır."""
    mod = _yukle()
    t = mod.akibet_turet(
        [_n("N00001", "2026-08-01T00:00:00+00:00"), {}, {"id": "N00002"}],  # 2,3: eksik alan
        [_akb_dogum("AKB-0001", "2026-08-05T00:00:00+00:00"),
         {"ts": "2026-08-01T00:00:00+00:00"},          # 2: olay yok
         {"ts": "2026-08-01T00:00:00+00:00", "olay": "bilinmez-olay"},  # 3: geçersiz olay
         {"ts": "2026-08-01T00:00:00+00:00", "olay": "karar"},          # 4: oneri_id yok
         {"ts": "2026-08-01T00:00:00+00:00", "olay": "karar", "oneri_id": "x",
          "karar": "boyle-bir-karar-yok"}],            # 5: geçersiz karar değeri
        "2026-08-31T00:00:00+00:00")
    assert t["olculemeyen"] == [2, 3, 2, 3, 4, 5], t["olculemeyen"]
    assert len(t["acik"]) == 2, "iyi satırlar bozuk satırlar YÜZÜNDEN kaybolmamalı"


def test_b9_TS_AYRISTIRILAMAYAN_DOGUM_YAS_NONE_UYDURULMAZ():
    """UYDURMA YASAĞI: ölçülemeyen yaş `None`dur, 0 DEĞİL."""
    mod = _yukle()
    t = mod.akibet_turet([_n("N00001", "böyle-bir-tarih-yok")], [],
                        "2026-08-31T00:00:00+00:00")
    assert t["acik"][0]["yas_gun"] is None, t["acik"][0]


def test_b10_SIMDI_TS_AYRISTIRILAMAZSA_HATA():
    mod = _yukle()
    with pytest.raises(ValueError):
        mod.akibet_turet([], [], "böyle-bir-tarih-yok")


def test_b11_SONUC_OLAYI_YUZEYE_CIKMAZ_AMA_GECERLI_SAYILIR():
    """`olay=sonuc` dönüşte YOKTUR (brief şeması sabit: acik/kararlar/sayilar/olculemeyen) ama
    geçerli bir satırdır — bozuk sayılıp `olculemeyen`e DÜŞMEMELİDİR."""
    mod = _yukle()
    t = mod.akibet_turet(
        [_n("N00001", "2026-08-01T00:00:00+00:00")],
        [_karar_satiri("N00001", "2026-08-05T00:00:00+00:00"),
         {"ts": "2026-08-06T00:00:00+00:00", "olay": "sonuc", "oneri_id": "N00001",
          "ozet": "yapıldı"}],
        "2026-08-31T00:00:00+00:00")
    assert t["olculemeyen"] == [], t["olculemeyen"]
    assert "sonuc" not in json.dumps(t)  # dönüşte sonuç izi YOK


def test_b12_BOZUK_SONUC_SATIRI_OLCULEMEYENE_SAYILIR():
    mod = _yukle()
    t = mod.akibet_turet([], [{"ts": "2026-08-06T00:00:00+00:00", "olay": "sonuc"}],
                        "2026-08-31T00:00:00+00:00")
    assert t["olculemeyen"] == [1], t["olculemeyen"]


def test_b13_ACIK_AZALAN_YAS_SIRASINDA():
    mod = _yukle()
    t = mod.akibet_turet(
        [_n("N00001", "2026-08-20T00:00:00+00:00"), _n("N00002", "2026-08-01T00:00:00+00:00"),
         _n("N00003", "2026-08-10T00:00:00+00:00")],
        [], "2026-08-31T00:00:00+00:00")
    assert [a["oneri_id"] for a in t["acik"]] == ["N00002", "N00003", "N00001"]


def test_b14_PROPOSALS_KAYNAGI_HERMES_REFLECT_SABIT():
    mod = _yukle()
    t = mod.akibet_turet([_n("N00001", "2026-08-01T00:00:00+00:00")], [],
                        "2026-08-31T00:00:00+00:00")
    assert t["acik"][0]["kaynak"] == "hermes_reflect"


def test_b15_SON_KARAR_GERCEK_ZAMANLA_SECILIR_DIZGE_SIRASI_DEGIL():
    """Ö5: iki farklı UTC-ofsetli karar aynı öneri için — DİZGE karşılaştırması YANLIŞ "son"u
    seçerdi. A = 2026-08-10T21:00:00+00:00 (gerçek 21:00 UTC, DAHA GEÇ).
    B = 2026-08-10T23:00:00+03:00 (gerçek 20:00 UTC, DAHA ERKEN — ama '23' rakamı '21'den BÜYÜK
    olduğu için DİZGE karşılaştırmasında B, A'dan SONRA görünürdü). Doğru "son karar" A'dır
    (uygulandi); eski dizge-kıyaslı kod B'yi (reddedildi) "son" sayardı."""
    mod = _yukle()
    t = mod.akibet_turet(
        [_n("N00001", "2026-08-01T00:00:00+00:00")],
        [_karar_satiri("N00001", "2026-08-10T21:00:00+00:00", karar="uygulandi"),
         _karar_satiri("N00001", "2026-08-10T23:00:00+03:00", karar="reddedildi")],
        "2026-08-31T00:00:00+00:00")
    assert t["sayilar"]["uygulandi"] == 1, t["sayilar"]
    assert t["sayilar"]["reddedildi"] == 0, t["sayilar"]


def test_b16_NAIVE_DAMGA_UTC_SAYILIR_COKMEZ():
    """Ö6: ofsetsiz (naive) ama geçerli ISO-8601 damga eskiden `_ts_ayristir`den NAIVE bir
    `datetime` dönerdi — offset-aware `simdi` ile fark alınırken `TypeError` fırlatırdı (ve bu,
    `main`'in eskiden var olan geniş `except (ValueError, TypeError)` yakalayıcısı yüzünden
    "kullanım hatası" gibi YANLIŞ etiketlenirdi). Artık naive damga UTC SAYILIR, çökmez."""
    mod = _yukle()
    t = mod.akibet_turet([_n("N00001", "2026-08-01T00:00:00")], [],
                        "2026-08-31T00:00:00+00:00")
    assert t["acik"][0]["yas_gun"] == 30, t["acik"][0]


def test_b17_BOZUK_TS_KARAR_ASLA_SON_KARARI_ELE_GECIREMEZ():
    """Y2 (yeniden-inceleme 2026-08-31): `_ts_sira_anahtari`nin kutbu — ayrıştırılamayan `ts`
    EN ESKİ sayılır, GEÇERLİ damgalı hiçbir kararı `son_karar` yarışında ASLA ele geçiremez.
    Bozuk-ts satır `kararlar`dan DÜŞÜRÜLMEZ (bkz. `_ts_sira_anahtari` docstring'indeki KARAR
    notu — doğum satırları için zaten kurulu `test_b9` emsaliyle tutarlı), yalnız sıralama
    gücünü kaybeder. İKİ giriş SIRASI da denenir: giriş sırasına bağımlı bir davranış, sırf
    "şu an kazandı" diye yanlışlıkla yeşil kalan bir çiviyi gizlerdi."""
    mod = _yukle()
    # Sıra 1: bozuk-ts ÖNCE (en kötü durum — eski kutupla bozuk satır ÖNCE gelip son_karar'ı
    # tutar, GERÇEK damgalı satır SONRA gelip onu YENEMEZDİ; bkz. eski `>=` mantığı).
    t1 = mod.akibet_turet(
        [_n("N00001", "2026-08-01T00:00:00+00:00")],
        [_karar_satiri("N00001", "boyle-bir-tarih-yok", karar="reddedildi"),
         _karar_satiri("N00001", "2026-08-10T00:00:00+00:00", karar="uygulandi")],
        "2026-08-31T00:00:00+00:00")
    assert t1["sayilar"]["uygulandi"] == 1, t1["sayilar"]
    assert t1["sayilar"]["reddedildi"] == 0, t1["sayilar"]
    # Sıra 2: bozuk-ts SONRA — eski (bozuk) kutupla bu sıra da bozuk-ts'in `(True, min)` anahtarı
    # her zaman kazandığından AYNI yanlış sonucu (reddedildi) verirdi.
    t2 = mod.akibet_turet(
        [_n("N00001", "2026-08-01T00:00:00+00:00")],
        [_karar_satiri("N00001", "2026-08-10T00:00:00+00:00", karar="uygulandi"),
         _karar_satiri("N00001", "boyle-bir-tarih-yok", karar="reddedildi")],
        "2026-08-31T00:00:00+00:00")
    assert t2["sayilar"]["uygulandi"] == 1, t2["sayilar"]
    assert t2["sayilar"]["reddedildi"] == 0, t2["sayilar"]


def test_b18_BOZUK_TS_SONUC_SIRALAMADA_EN_BASA_DUSER():
    """Y2 devamı: aynı kutup `sonuclar()`ın sıralamasını da (`_ts_sira_anahtari` üzerinden)
    etkiliyor — bozuk-ts bir `sonuc` satırı, geçerli damgalı bir sonuçtan ÖNCE (en eski
    sayılarak) sıralanmalı, SONRA (en yeni sayılarak) DEĞİL."""
    mod = _yukle()
    defter = [
        {"ts": "2026-08-20T00:00:00+00:00", "olay": "sonuc", "oneri_id": "N00001", "ozet": "yeni"},
        {"ts": "boyle-bir-tarih-yok", "olay": "sonuc", "oneri_id": "N00002", "ozet": "bozuk-ts"},
    ]
    s = mod.sonuclar(defter)
    assert [x["oneri_id"] for x in s] == ["N00002", "N00001"], s


# ═══════════════════════════════════════════════════════════════════════════
#  C. UZAK ŞABLONLAR — okuma_komutu / ekleme_komutu / sayaç / gerekçe
# ═══════════════════════════════════════════════════════════════════════════

def test_c1_OKUMA_KOMUTU_SUDOSUZ_SALT_OKUMA_IKI_DOSYA():
    mod = _yukle()
    k = mod.okuma_komutu()
    assert "sudo" not in k
    assert mod.PROPOSALS in k and mod.DEFTER in k
    assert mod.FETCH_AYRAC in k
    assert "grep -q" not in k, "journalctl tuzağıyla AYNI sınıf: borulanan bir komut kesilebilir"


def _sentetik_fetch(mod, proposals_icerik: str, proposals_durum: str,
                    defter_icerik: str, defter_durum: str) -> str:
    """`okuma_komutu`nun GERÇEK çıktı biçimini taklit eden sentetik metin — `_ayir`i ssh'sız
    ölçmek için. `durum` ∈ {"ok","yok","hata"}."""
    def blok(icerik: str, isaret: str, durum: str) -> str:
        if durum == "yok":
            return f"{isaret} YOK\n"
        rc = "0" if durum == "ok" else "1"
        return f"{icerik}\n{isaret} rc={rc}\n"
    return (blok(proposals_icerik, mod.PROPOSALS_ISARET, proposals_durum) + mod.FETCH_AYRAC +
           "\n" + blok(defter_icerik, mod.DEFTER_ISARET, defter_durum))


def test_c2_AYIR_HER_DOSYAYI_KENDI_ISARETIYLE_AYRISTIRIR_OK():
    """K1 düzeltmesi: `_ayir` artık `dict` döner ({"proposals_metin","proposals_durum",
    "defter_metin","defter_durum"}) — durum bilgisi TAŞIR, eski `tuple[str,str]` şekli DEĞİL."""
    mod = _yukle()
    metin = _sentetik_fetch(mod, "satir-a\nsatir-b\n", "ok", "satir-c\n", "ok")
    a = mod._ayir(metin)
    assert a["proposals_metin"] == "satir-a\nsatir-b\n", a
    assert a["proposals_durum"] == "ok", a
    assert a["defter_metin"] == "satir-c\n", a
    assert a["defter_durum"] == "ok", a


def test_c2b_AYIR_DOSYA_YOK_ISARETI_BOS_METIN_YOK_DURUMU():
    """Dosya HİÇ YOKSA (meşru — henüz hiç karar yazılmamış) içerik boş, durum 'yok'tur ('hata'
    DEĞİL): bu, K1'in ayırt etmesi gereken İKİ meşru-boş sınıftan biridir."""
    mod = _yukle()
    metin = _sentetik_fetch(mod, "", "yok", "", "yok")
    a = mod._ayir(metin)
    assert a["proposals_metin"] == "" and a["proposals_durum"] == "yok", a
    assert a["defter_metin"] == "" and a["defter_durum"] == "yok", a


def test_c2c_AYIR_RC_SIFIR_DEGILSE_HATA_DURUMU():
    """K1 KRİTİK bulgusu: dosya VAR ama `cat` başarısız olduysa (izin/bozukluk) durum 'hata'dır —
    'yok' (meşru boş) İLE KARIŞTIRILMAZ."""
    mod = _yukle()
    metin = _sentetik_fetch(mod, "", "hata", "bir-satir", "ok")
    a = mod._ayir(metin)
    assert a["proposals_durum"] == "hata", a
    assert a["defter_durum"] == "ok", a


def test_c2d_AYIR_ISARET_SATIRI_HIC_YOKSA_HATA_SAYILIR():
    """Ölçülmemiş bir uzak çıktı biçimi (işaret satırı kayıp) YEŞİL SAYILMAZ — doğrulanamayan
    bir okuma başarılı sayılamaz (uydurma yasağı)."""
    mod = _yukle()
    a = mod._ayir("hiç işaretsiz düz metin")
    assert a["proposals_durum"] == "hata", a


def test_c2e_FETCH_HUKMU_HATA_VARSA_KIRMIZI_ADIYLA_SOYLER():
    """K1 KRİTİK bulgusunun kapanışı: `_fetch_hukmu` bir dosya 'hata' durumundaysa KIRMIZI döner
    ve HANGİ dosya olduğunu adıyla söyler — 'sıfır' ile 'bilmiyorum' burada nihayet ayrılır."""
    mod = _yukle()
    ok, neden = mod._fetch_hukmu({"proposals_durum": "ok", "defter_durum": "hata"})
    assert ok is False
    assert "defter" in neden and "ÖLÇÜLEMEDİ" in neden.upper(), neden
    ok2, _ = mod._fetch_hukmu({"proposals_durum": "yok", "defter_durum": "yok"})
    assert ok2 is True, "meşru boş defter YANLIŞLIKLA kırmızı sayıldı"
    ok3, _ = mod._fetch_hukmu({"proposals_durum": "ok", "defter_durum": "ok"})
    assert ok3 is True


def test_c3_JSONL_SATIRLARI_BOZUK_SATIRI_BOS_SOZLUKLE_KORUR():
    mod = _yukle()
    satirlar = mod._jsonl_satirlari('{"a": 1}\nboyle-bir-json-yok\n\n{"b": 2}\n')
    assert satirlar == [{"a": 1}, {}, {"b": 2}], satirlar


def test_c4_EKLEME_KOMUTU_FLOCK_PRINTF_TAIL_TASIR():
    mod = _yukle()
    k = mod.ekleme_komutu({"ts": "2026-08-31T00:00:00+00:00", "olay": "oneri"})
    assert k.startswith("flock "), k
    assert mod.KILIT in k, k
    assert "printf" in k and "tail -1" in k, k
    assert mod.DEFTER in k, k


def test_c5_EKLEME_KOMUTU_ENJEKSIYON_METNI_SH_CROKMEDEN_AYRISTIRIR(tmp_path):
    """v348 enjeksiyon çivisi sınıfı: içinde `'` VE `"; DROP` taşıyan bir metin, `sh -c`nin
    sarmalını BÖLMEMELİ. Gerçek `sh -c` altında koşulur (flock saplaması: bkz. `_flock_yolu`)."""
    mod = _yukle()
    defter = tmp_path / "d.jsonl"
    kilit = tmp_path / "d.jsonl.lock"
    satir = {"ts": "2026-08-31T00:00:00+00:00", "olay": "oneri", "oneri_id": "AKB-0001",
             "kaynak": "operator", "oneri": "operatörün fikri; \"; DROP TABLE x; -- ' enjeksiyon"}
    komut = mod.ekleme_komutu(satir).replace(mod.KILIT, str(kilit)).replace(mod.DEFTER, str(defter))
    r = subprocess.run(["sh", "-c", komut], capture_output=True, text=True,
                       env={**os.environ, "PATH": _flock_yolu(tmp_path)})
    assert r.returncode == 0, f"zincir düştü:\n{komut}\nstderr={r.stderr}"
    beklenen = json.dumps(satir, ensure_ascii=False, sort_keys=True)
    assert defter.read_text(encoding="utf-8") == beklenen + "\n", defter.read_text(encoding="utf-8")


def test_c6_SONRAKI_AKB_ID_BOS_DEFTERDE_0001():
    mod = _yukle()
    assert mod.sonraki_akb_id([]) == "AKB-0001"


def test_c7_SONRAKI_AKB_ID_EN_BUYUK_ARTI_BIR_CAKISMASIZ():
    """AKB sayaç çakışmasızlığı: ara boşluk (gap) olsa bile max+1 alınır, count+1 DEĞİL."""
    mod = _yukle()
    defter = [_akb_dogum("AKB-0005", "2026-08-01T00:00:00+00:00"),
              _karar_satiri("AKB-0002", "2026-08-02T00:00:00+00:00")]
    assert mod.sonraki_akb_id(defter) == "AKB-0006"


def test_c8_SONRAKI_AKB_ID_KARAR_SATIRINDAKI_ID_YI_DE_TARAR():
    """Bozuk bir defterde doğum satırı kaybolsa bile (yalnız karar/sonuç hayatta kaldıysa)
    numara GERİYE gitmez."""
    mod = _yukle()
    defter = [{"ts": "x", "olay": "karar", "oneri_id": "AKB-0009", "karar": "uygulandi"}]
    assert mod.sonraki_akb_id(defter) == "AKB-0010"


def test_c9_GEREKCE_GECERLI_ESIK_TAM_SINIRDA():
    mod = _yukle()
    assert mod.gerekce_gecerli_mi("x" * mod.GEREKCE_ASGARI) is True
    assert mod.gerekce_gecerli_mi("x" * (mod.GEREKCE_ASGARI - 1)) is False
    assert mod.gerekce_gecerli_mi("   ") is False
    assert mod.gerekce_gecerli_mi(None) is False


def test_c10_YAZIM_DOGRULANDI_ESLESMEDE_YESIL_ESLESMEZSE_KIRMIZI():
    mod = _yukle()
    satir = {"ts": "2026-08-31T00:00:00+00:00", "olay": "oneri"}
    beklenen = json.dumps(satir, ensure_ascii=False, sort_keys=True)
    ok, neden = mod.yazim_dogrulandi(beklenen + "\n", satir)
    assert ok is True, neden
    ok2, neden2 = mod.yazim_dogrulandi("baska-bir-satir\n", satir)
    assert ok2 is False, "eşleşmeyen tail çıktısı YEŞİL sayıldı"
    assert "DOĞRULANAMADI" in neden2.upper(), neden2


def test_c11_GERCEK_FLOCK_PRINTF_TAIL_ZINCIRI_DOSYAYA_GERCEKTEN_EKLER(tmp_path):
    """ŞEKİL DEĞİL DAVRANIŞ: `ekleme_komutu`nun ürettiği dizge, GERÇEK bir `sh -c` altında,
    canlı yola İŞARET EDEN metin tmp_path'e yönlendirilerek koşulur. `flock`/`printf`/`tail`
    zincirinin KENDİSİ ölçülür — yalnız alt-dizge arayan bir çivinin YAKALAYAMAYACAĞI bir
    sınıf hata (örn. tek `shlex.quote`, ya da `>` yerine `>>`) burada YAKALANIR.
    """
    mod = _yukle()
    defter = tmp_path / "oneri_akibet.jsonl"
    kilit = tmp_path / "oneri_akibet.jsonl.lock"
    satir = {"ts": "2026-08-31T00:00:00+00:00", "olay": "oneri", "oneri_id": "AKB-0001",
             "kaynak": "operator", "oneri": "operatörün kesme işaretli fikri: \"it's\" ve '; DROP"}
    # KİLİT ÖNCE değiştirilir: KILIT metni DEFTER'i ÖNEK olarak içerir (`KILIT == DEFTER+".lock"`)
    # — ters sırada DEFTER değişimi KILIT'in içine de sızar (bu testte tesadüfen aynı sonucu
    # verirdi, ama sıra BURADA açıkça doğru olan yönde: en UZUN eşleşen dize önce).
    komut = (mod.ekleme_komutu(satir)
            .replace(mod.KILIT, str(kilit)).replace(mod.DEFTER, str(defter)))
    r = subprocess.run(["sh", "-c", komut], capture_output=True, text=True,
                       env={**os.environ, "PATH": _flock_yolu(tmp_path)})
    assert r.returncode == 0, f"zincir düştü:\n{komut}\nstderr={r.stderr}"
    beklenen = json.dumps(satir, ensure_ascii=False, sort_keys=True)
    assert defter.read_text(encoding="utf-8") == beklenen + "\n", (
        f"dosyaya YAZILAN, beklenenle eşleşmiyor:\n{defter.read_text(encoding='utf-8')!r}")
    assert r.stdout.strip() == beklenen, (
        f"`tail -1` geri-okuması yazılanla eşleşmiyor:\n{r.stdout!r}")


def test_c12_GERCEK_ZINCIR_IKINCI_EKLEME_APPEND_EDER_UZERINE_YAZMAZ(tmp_path):
    mod = _yukle()
    defter = tmp_path / "oneri_akibet.jsonl"
    kilit = tmp_path / "oneri_akibet.jsonl.lock"
    ort = {**os.environ, "PATH": _flock_yolu(tmp_path)}
    for i in range(2):
        satir = {"ts": f"2026-08-3{i}T00:00:00+00:00", "olay": "oneri", "oneri_id": f"AKB-000{i}"}
        komut = (mod.ekleme_komutu(satir)
                .replace(mod.KILIT, str(kilit)).replace(mod.DEFTER, str(defter)))
        r = subprocess.run(["sh", "-c", komut], capture_output=True, text=True, env=ort)
        assert r.returncode == 0, r.stderr
    satirlar = defter.read_text(encoding="utf-8").splitlines()
    assert len(satirlar) == 2, satirlar
    assert json.loads(satirlar[0])["oneri_id"] == "AKB-0000"
    assert json.loads(satirlar[1])["oneri_id"] == "AKB-0001"


# ── Ö2 düzeltmesi: `oneri_ekleme_komutu` — AKB id tahsisi flock İÇİNDE, TEK ssh çağrısı ────────

def _oneri_komut_calistir(mod, tmp_path, kaynak: str, metin: str, ts: str,
                          on_defter_satirlari: list[dict] = ()) -> subprocess.CompletedProcess:
    """`oneri_ekleme_komutu`nun ürettiği dizgeyi GERÇEK `sh -c` altında (flock saplamalı) koşturur;
    `on_defter_satirlari` verilirse defter ÖNCEDEN o satırlarla doldurulur (id çakışmasızlığını
    ölçmek için)."""
    defter = tmp_path / "d.jsonl"
    kilit = tmp_path / "d.jsonl.lock"
    if on_defter_satirlari:
        _satir_yaz(defter, list(on_defter_satirlari))
    komut = (mod.oneri_ekleme_komutu(kaynak, metin, ts)
            .replace(mod.KILIT, str(kilit)).replace(mod.DEFTER, str(defter)))
    ort = {**os.environ, "PATH": _flock_yolu(tmp_path)}
    r = subprocess.run(["sh", "-c", komut], capture_output=True, text=True, env=ort)
    r.defter_yolu = defter  # type: ignore[attr-defined]
    return r


def test_c13_ONERI_EKLEME_KOMUTU_FLOCK_VE_PYTHON3_TASIR():
    mod = _yukle()
    k = mod.oneri_ekleme_komutu("operator", "bir fikir", "2026-08-31T00:00:00+00:00")
    assert k.startswith("flock "), k
    assert mod.KILIT in k, k
    assert "python3 -c" in k, k


def test_c14_ONERI_EKLEME_KOMUTU_GERCEKTEN_KOSAR_BOS_DEFTERDE_AKB0001(tmp_path):
    """ŞEKİL DEĞİL DAVRANIŞ: id ÖNCEDEN bilinmez, REMOTE (burada gerçek yerel `sh -c`) tarafından
    hesaplanır. Boş/yok defterde ilk id `AKB-0001`dir."""
    mod = _yukle()
    r = _oneri_komut_calistir(mod, tmp_path, "operator", "bir fikir",
                              "2026-08-31T00:00:00+00:00")
    assert r.returncode == 0, f"zincir düştü:\n{r.stdout}\n{r.stderr}"
    ok, neden, atanan_id = mod.oneri_yazim_dogrulandi(r.stdout, "operator", "bir fikir")
    assert ok is True, neden
    assert atanan_id == "AKB-0001", atanan_id
    satirlar = r.defter_yolu.read_text(encoding="utf-8").splitlines()
    assert len(satirlar) == 1
    row = json.loads(satirlar[0])
    assert row == {"ts": "2026-08-31T00:00:00+00:00", "olay": "oneri", "oneri_id": "AKB-0001",
                   "kaynak": "operator", "oneri": "bir fikir"}, row


def test_c15_ONERI_EKLEME_KOMUTU_DOLU_DEFTERDE_MAX_ARTI_BIR(tmp_path):
    """AKB sayaç çakışmasızlığı REMOTE tarafta da: `sonraki_akb_id` ile AYNI algoritma (max+1,
    gap'ler doğru ele alınır) — çapraz-çivi."""
    mod = _yukle()
    mevcut = [_akb_dogum("AKB-0005", "2026-08-01T00:00:00+00:00"),
              _karar_satiri("AKB-0002", "2026-08-02T00:00:00+00:00")]
    r = _oneri_komut_calistir(mod, tmp_path, "rol1", "ikinci fikir",
                              "2026-08-31T00:00:00+00:00", on_defter_satirlari=mevcut)
    assert r.returncode == 0, r.stderr
    ok, neden, atanan_id = mod.oneri_yazim_dogrulandi(r.stdout, "rol1", "ikinci fikir")
    assert ok is True, neden
    beklenen = mod.sonraki_akb_id(mevcut)
    assert atanan_id == beklenen == "AKB-0006", (atanan_id, beklenen)


def test_c16_ONERI_EKLEME_KOMUTU_ARDISIK_IKI_KOSUM_CAKISMAZ(tmp_path):
    """Ö2'nin asıl konusu: id hesaplaması artık AYNI flock kapsamında — ardışık iki koşum farklı
    id üretir (eski akışta da doğruydu; burada TEK ssh çağrısıyla, okuma-yazma arası pencere
    olmadan doğrulanır)."""
    mod = _yukle()
    defter = tmp_path / "d.jsonl"
    kilit = tmp_path / "d.jsonl.lock"
    ort = {**os.environ, "PATH": _flock_yolu(tmp_path)}
    idler = []
    for i in range(3):
        komut = (mod.oneri_ekleme_komutu("operator", f"fikir-{i}", "2026-08-31T00:00:00+00:00")
                .replace(mod.KILIT, str(kilit)).replace(mod.DEFTER, str(defter)))
        r = subprocess.run(["sh", "-c", komut], capture_output=True, text=True, env=ort)
        assert r.returncode == 0, r.stderr
        _, _, atanan_id = mod.oneri_yazim_dogrulandi(r.stdout, "operator", f"fikir-{i}")
        idler.append(atanan_id)
    assert idler == ["AKB-0001", "AKB-0002", "AKB-0003"], idler


def test_c17_ONERI_EKLEME_KOMUTU_KESME_ISARETLI_VE_ENJEKSIYON_METNI_BOZULMADAN_YAZILIR(tmp_path):
    """Kullanıcı metni ham Python kaynağına KARIŞMAZ — `json.dumps`/`json.loads` ile tek parça
    taşınır. v348 enjeksiyon çivisi sınıfı: `'` VE `"; DROP` içeren metin."""
    mod = _yukle()
    metin = "operatörün fikri: \"it's\" bir enjeksiyon denemesi '; DROP TABLE x; --"
    r = _oneri_komut_calistir(mod, tmp_path, "operator", metin, "2026-08-31T00:00:00+00:00")
    assert r.returncode == 0, f"zincir düştü:\n{r.stdout}\n{r.stderr}"
    row = json.loads(r.defter_yolu.read_text(encoding="utf-8").splitlines()[-1])
    assert row["oneri"] == metin, row


def test_c18_ONERI_YAZIM_DOGRULANDI_ALAN_UYUSMAZLIGINDA_KIRMIZI():
    mod = _yukle()
    satir = json.dumps({"ts": "x", "olay": "oneri", "oneri_id": "AKB-0001",
                        "kaynak": "operator", "oneri": "bir fikir"})
    ok, neden, atanan = mod.oneri_yazim_dogrulandi(satir, "operator", "bir fikir")
    assert ok is True and atanan == "AKB-0001", neden
    ok2, neden2, atanan2 = mod.oneri_yazim_dogrulandi(satir, "rol1", "bir fikir")  # kaynak UYUŞMUYOR
    assert ok2 is False and atanan2 is None, neden2
    assert "DOĞRULANAMADI" in neden2.upper(), neden2
    ok3, _, _ = mod.oneri_yazim_dogrulandi("boyle-bir-json-yok", "operator", "bir fikir")
    assert ok3 is False
    kotu_id = json.dumps({"ts": "x", "olay": "oneri", "oneri_id": "boyle-bir-id-degil",
                          "kaynak": "operator", "oneri": "bir fikir"})
    ok4, _, atanan4 = mod.oneri_yazim_dogrulandi(kotu_id, "operator", "bir fikir")
    assert ok4 is False and atanan4 is None


def test_c19_DEFTER_VE_TUREV_KOMUT_YAZ_ICIN_NONE_GUARDI_TASIR():
    """Y7 (yeniden-inceleme 2026-08-31): `_defter_ve_turev`, `_listele`/`_oneri` ile SİMETRİK
    olarak `filo._ssh_kos`un `None` dönüşünü (`--komut-yaz` sözleşmesi) karşılamalı. Bugün
    `_karar`/`_sonuc` `komut_yaz` dalında ÖNCE döndüğü için bu yol ULAŞILMAZ, ama asimetri
    LATENTTİ: `_listele`/`_oneri` guard'ı taşırken burası taşımıyordu — sıralama değişse çıplak
    `TypeError` ile çökerdi (ve R1 tam da bunu yakalayacak geniş `except`i haklı olarak
    kaldırmıştı). Doğrudan çağrı ile ölçülür — `komut_yaz=True` olduğu için `filo._ssh_kos` HİÇ
    subprocess çalıştırmaz (yalnız basar), gerçek/sahte ssh'a hiç gerek yok."""
    mod = _yukle()
    a = types.SimpleNamespace(host=None, anahtar=None, komut_yaz=True)
    rc, turev = mod._defter_ve_turev(a)
    assert turev is None, turev
    assert rc == 0, rc


# ═══════════════════════════════════════════════════════════════════════════
#  D. ALT-KOMUTLAR UÇTAN UCA + SSH NİŞANCISI
# ═══════════════════════════════════════════════════════════════════════════

def _gercek_nisanci(tmp_path, mod) -> tuple[dict, pathlib.Path, pathlib.Path]:
    """PATH'e GERÇEK bir `ssh` betiği koyar — uzak komut STRINGİNİ alıp GERÇEKTEN `sh -c` ile
    koşar (mock DEĞİL, ayrı bir Python süreci). Canlı `/opt/meridian/state/...` yolları, komut
    METNİNDE düz-metin değişimiyle tmp_path altındaki dosyalara yönlendirilir — bu güvenlidir
    çünkü bu yollar shlex-özel karakter TAŞIMAZ (shlex.quote onları DEĞİŞTİRMEDEN bırakır).
    `flock` yoksa (macOS geliştirme makinesi) saplama PATH'e eklenir (`_flock_yolu`).
    Sonuç: CLI'ın GERÇEKTEN ürettiği komut GERÇEKTEN koşar — gerçek A1'e ASLA gidilmez, gerçek
    `ssh` ikilisi HİÇ çağrılmaz (`ssh` adındaki bu şey bir Python betiğidir)."""
    kutu = tmp_path / "bin"
    kutu.mkdir()
    proposals = tmp_path / "improvement_proposals.jsonl"
    defter = tmp_path / "oneri_akibet.jsonl"
    kilit = tmp_path / "oneri_akibet.jsonl.lock"
    flock_path = _flock_yolu(tmp_path)
    sh = kutu / "ssh"
    program = f"""#!{sys.executable}
import os, subprocess, sys
komut = sys.argv[-1]
komut = komut.replace({mod.KILIT!r}, {str(kilit)!r})
komut = komut.replace({mod.DEFTER!r}, {str(defter)!r})
komut = komut.replace({mod.PROPOSALS!r}, {str(proposals)!r})
ort = dict(os.environ)
ort["PATH"] = {flock_path!r}
p = subprocess.run(["sh", "-c", komut], capture_output=True, text=True, env=ort)
sys.stdout.write(p.stdout)
sys.stderr.write(p.stderr)
sys.exit(p.returncode)
"""
    sh.write_text(program, encoding="utf-8")
    sh.chmod(0o755)
    return {"PATH": str(kutu)}, proposals, defter


def test_d1_LISTELE_BOS_DEFTERDE_ACIK_ONERI_YOK_VE_AKIBET_SIFIR(tmp_path):
    mod = _yukle()
    ort, _, _ = _gercek_nisanci(tmp_path, mod)
    r = _cli("listele", ort=ort)
    assert r.returncode == 0, f"{r.returncode}\n{r.stdout}\n{r.stderr}"
    assert "(açık öneri yok)" in r.stdout, r.stdout
    assert "AKIBET: 0 açık" in r.stdout, r.stdout


def test_d2_LISTELE_PROPOSALS_ACIK_ONERIYI_YASIYLA_LISTELER(tmp_path):
    mod = _yukle()
    ort, proposals, _ = _gercek_nisanci(tmp_path, mod)
    _satir_yaz(proposals, [_n("N00001", "2026-08-01T00:00:00+00:00", oneri="şey yap")])
    r = _cli("listele", ort=ort)
    assert r.returncode == 0, f"{r.stdout}\n{r.stderr}"
    assert "N00001" in r.stdout and "şey yap" in r.stdout, r.stdout
    assert "AKIBET: 1 açık" in r.stdout, r.stdout


def test_d3_LISTELE_KARARLI_ONERI_ACIKTAN_DUSER_UCTAN_UCA(tmp_path):
    mod = _yukle()
    ort, proposals, defter = _gercek_nisanci(tmp_path, mod)
    _satir_yaz(proposals, [_n("N00001", "2026-08-01T00:00:00+00:00")])
    _satir_yaz(defter, [_karar_satiri("N00001", "2026-08-10T00:00:00+00:00", karar="uygulandi")])
    r = _cli("listele", ort=ort)
    assert r.returncode == 0, r.stderr
    assert "AKIBET: 0 açık" in r.stdout, r.stdout
    assert "uygulandi" in r.stdout, "son 5 karar listede yok:\n" + r.stdout


def test_d4_LISTELE_SSH_OLCUM_HATASINDA_KIRMIZI(tmp_path):
    """ssh RC != 0 ise `listele` KIRMIZI döner, sessizce boş defter SAYMAZ."""
    kutu = tmp_path / "bin"
    kutu.mkdir()
    sh = kutu / "ssh"
    sh.write_text("#!/bin/sh\necho 'baglanti koptu' >&2\nexit 255\n", encoding="utf-8")
    sh.chmod(0o755)
    r = _cli("listele", ort={"PATH": str(kutu)})
    assert r.returncode == 1, f"{r.returncode}\n{r.stdout}\n{r.stderr}"
    assert "ÖLÇÜLEMEDİ" in r.stderr, r.stderr


def test_d5_ONERI_ID_SAYACI_ARDISIK_KOSUMLARDA_CAKISMAZ(tmp_path):
    mod = _yukle()
    ort, _, defter = _gercek_nisanci(tmp_path, mod)
    r1 = _cli("oneri", "birinci fikir", "--kaynak", "operator", ort=ort)
    assert r1.returncode == 0, f"{r1.stdout}\n{r1.stderr}"
    assert "AKB-0001" in r1.stdout, r1.stdout
    r2 = _cli("oneri", "ikinci fikir", "--kaynak", "rol1", ort=ort)
    assert r2.returncode == 0, f"{r2.stdout}\n{r2.stderr}"
    assert "AKB-0002" in r2.stdout, r2.stdout
    satirlar = [json.loads(s) for s in defter.read_text(encoding="utf-8").splitlines()]
    assert [s["oneri_id"] for s in satirlar] == ["AKB-0001", "AKB-0002"]
    assert satirlar[0]["kaynak"] == "operator" and satirlar[1]["kaynak"] == "rol1"


def test_d6_ONERI_KESME_ISARETLI_METIN_UCTAN_UCA_BOZULMADAN_YAZILIR(tmp_path):
    mod = _yukle()
    ort, _, defter = _gercek_nisanci(tmp_path, mod)
    metin = "operatörün fikri: \"it's\" bir enjeksiyon denemesi '; DROP TABLE x; --"
    r = _cli("oneri", metin, "--kaynak", "operator", ort=ort)
    assert r.returncode == 0, f"{r.stdout}\n{r.stderr}"
    satirlar = [json.loads(s) for s in defter.read_text(encoding="utf-8").splitlines()]
    assert satirlar[0]["oneri"] == metin, satirlar


def test_d7_KARAR_ACIK_ONERIYE_YAZILIR_VE_ACIKTAN_DUSURUR(tmp_path):
    mod = _yukle()
    ort, proposals, defter = _gercek_nisanci(tmp_path, mod)
    _satir_yaz(proposals, [_n("N00001", "2026-08-01T00:00:00+00:00")])
    r = _cli("karar", "N00001", "uygulandi", "--gerekce", "x" * 25, "--veren", "operator",
             ort=ort)
    assert r.returncode == 0, f"{r.stdout}\n{r.stderr}"
    satirlar = [json.loads(s) for s in defter.read_text(encoding="utf-8").splitlines()]
    assert satirlar[-1] == {"ts": satirlar[-1]["ts"], "olay": "karar", "oneri_id": "N00001",
                            "karar": "uygulandi", "karar_veren": "operator",
                            "gerekce": "x" * 25}
    r2 = _cli("listele", ort=ort)
    assert "AKIBET: 0 açık" in r2.stdout, r2.stdout


def test_d8_KARAR_KISA_GEREKCEDE_KIRMIZI_SSH_HIC_CAGRILMAZ(tmp_path):
    ort, iz = _nisanci(tmp_path)
    r = _cli("karar", "N00001", "uygulandi", "--gerekce", "kısa", "--veren", "operator", ort=ort)
    assert r.returncode == 1, f"{r.returncode}\n{r.stdout}\n{r.stderr}"
    assert not iz.exists(), "kısa gerekçe ssh'a KADAR gitti"
    assert "gerekçe" in r.stderr.lower(), r.stderr


def test_d9_KARAR_VAR_OLMAYAN_ID_YE_YAZILMAZ(tmp_path):
    mod = _yukle()
    ort, proposals, defter = _gercek_nisanci(tmp_path, mod)
    _satir_yaz(proposals, [_n("N00001", "2026-08-01T00:00:00+00:00")])
    r = _cli("karar", "N09999", "uygulandi", "--gerekce", "x" * 25, "--veren", "operator",
             ort=ort)
    assert r.returncode == 1, f"{r.stdout}\n{r.stderr}"
    assert "HİÇ doğmamış" in r.stderr, r.stderr
    assert defter.read_text(encoding="utf-8") == "" if defter.exists() else True


def test_d10_KARAR_ZATEN_KAPALI_ONERIYE_ZORLASIZ_KIRMIZI_ZORLA_ILE_GECER(tmp_path):
    mod = _yukle()
    ort, proposals, defter = _gercek_nisanci(tmp_path, mod)
    _satir_yaz(proposals, [_n("N00001", "2026-08-01T00:00:00+00:00")])
    r1 = _cli("karar", "N00001", "reddedildi", "--gerekce", "x" * 25, "--veren", "operator",
              ort=ort)
    assert r1.returncode == 0, f"{r1.stdout}\n{r1.stderr}"

    r2 = _cli("karar", "N00001", "uygulandi", "--gerekce", "y" * 25, "--veren", "rol1", ort=ort)
    assert r2.returncode == 1, "zaten kapalı öneriye --zorla'sız karar YAZILDI"
    assert "ZATEN kapalı" in r2.stderr, r2.stderr
    assert len(defter.read_text(encoding="utf-8").splitlines()) == 1, "ikinci satır YAZILMAMALI"

    r3 = _cli("karar", "N00001", "uygulandi", "--gerekce", "y" * 25, "--veren", "rol1",
              "--zorla", ort=ort)
    assert r3.returncode == 0, f"{r3.stdout}\n{r3.stderr}"
    assert "UYARI" in r3.stdout, r3.stdout
    satirlar = [json.loads(s) for s in defter.read_text(encoding="utf-8").splitlines()]
    assert len(satirlar) == 2 and satirlar[-1]["karar"] == "uygulandi", satirlar


def test_d11_SONUC_KARARSIZ_ONERIYE_YAZILMAZ(tmp_path):
    mod = _yukle()
    ort, proposals, defter = _gercek_nisanci(tmp_path, mod)
    _satir_yaz(proposals, [_n("N00001", "2026-08-01T00:00:00+00:00")])
    r = _cli("sonuc", "N00001", "--ozet", "yapıldı", ort=ort)
    assert r.returncode == 1, f"{r.stdout}\n{r.stderr}"
    assert "karardan ÖNCE" in r.stderr, r.stderr


def test_d12_SONUC_KARARLI_ONERIYE_YAZILIR(tmp_path):
    mod = _yukle()
    ort, proposals, defter = _gercek_nisanci(tmp_path, mod)
    _satir_yaz(proposals, [_n("N00001", "2026-08-01T00:00:00+00:00")])
    r1 = _cli("karar", "N00001", "uygulandi", "--gerekce", "x" * 25, "--veren", "operator",
              ort=ort)
    assert r1.returncode == 0, r1.stderr
    r2 = _cli("sonuc", "N00001", "--ozet", "yapıldı", "--ref", "commit:abc123", ort=ort)
    assert r2.returncode == 0, f"{r2.stdout}\n{r2.stderr}"
    satirlar = [json.loads(s) for s in defter.read_text(encoding="utf-8").splitlines()]
    sonuc_satiri = satirlar[-1]
    assert sonuc_satiri["olay"] == "sonuc" and sonuc_satiri["ozet"] == "yapıldı"
    assert sonuc_satiri["ref"] == "commit:abc123"


def test_d13_SONUC_REF_VERILMEZSE_ALAN_HIC_YAZILMAZ(tmp_path):
    mod = _yukle()
    ort, proposals, defter = _gercek_nisanci(tmp_path, mod)
    _satir_yaz(proposals, [_n("N00001", "2026-08-01T00:00:00+00:00")])
    _cli("karar", "N00001", "uygulandi", "--gerekce", "x" * 25, "--veren", "operator", ort=ort)
    r = _cli("sonuc", "N00001", "--ozet", "yapıldı", ort=ort)
    assert r.returncode == 0, r.stderr
    satirlar = [json.loads(s) for s in defter.read_text(encoding="utf-8").splitlines()]
    assert "ref" not in satirlar[-1], satirlar[-1]


def test_d15_LISTELE_DEFTER_OKUNAMAZSA_KIRMIZI_VE_AKB_SIFIRLANMAZ(tmp_path):
    """K1 (KRİTİK, inceleme 2026-08-31): okunamayan defter ile BOŞ defter AYNI şey DEĞİLDİR.
    Eskiden ikisi de sessizce boş metne düşüyordu (`2>/dev/null; ...; true`) — okunamayan bir
    defter "0 açık, sayaç 0'dan başlar" YANILSAMASI verirdi (uydurma yasağı ihlali: ölçüm YOKSA
    sıfır SAYILMAZ). Artık `_dosya_blogu`nun `rc=$?` işareti bunu YAKALAR: `listele` KIRMIZI
    döner, ÖLÇÜLEMEDİ der — sessizce "0 açık" BASMAZ."""
    if os.geteuid() == 0:
        pytest.skip("root için chmod 0o000 okumayı engellemez — bu ortamda ölçülemez")
    mod = _yukle()
    ort, _, defter = _gercek_nisanci(tmp_path, mod)
    defter.write_text('{"ts": "x"}\n', encoding="utf-8")
    defter.chmod(0o000)
    try:
        r = _cli("listele", ort=ort)
    finally:
        defter.chmod(0o644)  # tmp_path temizliği izin hatasıyla patlamasın
    assert r.returncode == 1, f"okunamayan defter YEŞİL geçti:\n{r.stdout}\n{r.stderr}"
    assert "ÖLÇÜLEMEDİ" in r.stderr, r.stderr
    assert "açık" not in r.stdout, (
        f"okunamayan defter BOŞ defterle karıştırılmış olabilir (AKB sayacı uydurulmuş):\n"
        f"{r.stdout}")
    # Y5 düzeltmesi (yeniden-inceleme 2026-08-31): ÖLÇÜLMÜŞ uzak stderr (`cat`ın KENDİ hata
    # metni, örn. "Permission denied") atılmamalı — operatör "ÖLÇÜLEMEDİ" görüp NEDENİNİ de
    # görebilmeli. `_gercek_nisanci` gerçek `cat`ı gerçekten koşturuyor, bu yüzden gerçek OS
    # hata metnini bekleyebiliriz.
    assert "denied" in r.stderr.lower() or "izin" in r.stderr.lower(), (
        f"ÖLÇÜLEMEDİ mesajı basılıyor ama ÖLÇÜLMÜŞ uzak stderr nedeni (Permission denied) "
        f"görünmüyor:\n{r.stderr}")


def test_d16_ONERI_DEFTER_OKUNAMAZSA_AKB_0001E_SIFIRLANMAZ_KIRMIZI(tmp_path):
    """K1 devamı, coordinator'ın açıkça istediği mutasyon: `oneri` de aynı kritik sınıfı taşır —
    id hesaplaması artık uzak `python3` betiğinin İÇİNDE (Ö2), ve o betik defteri `open(...)` ile
    okur; `except FileNotFoundError` YALNIZ dosya YOKLUĞUNU yutar — chmod 0o000'lı bir defter
    `PermissionError` fırlatır, betik ÇÖKER, `flock ... sh -c` zinciri RC≠0 döner. Sessizce boş
    sayılıp AKB-0001 ÜRETİLMEZ — CLI KIRMIZI döner."""
    if os.geteuid() == 0:
        pytest.skip("root için chmod 0o000 okumayı engellemez — bu ortamda ölçülemez")
    mod = _yukle()
    ort, _, defter = _gercek_nisanci(tmp_path, mod)
    defter.write_text('{"ts": "x"}\n', encoding="utf-8")
    defter.chmod(0o000)
    try:
        r = _cli("oneri", "bir fikir", "--kaynak", "operator", ort=ort)
    finally:
        defter.chmod(0o644)
    assert r.returncode == 1, f"okunamayan defterde oneri YEŞİL geçti:\n{r.stdout}\n{r.stderr}"
    assert "AKB-0001" not in r.stdout, (
        f"okunamayan defter BOŞ sayılıp AKB-0001 üretildi (uydurma yasağı ihlali):\n{r.stdout}")


def test_d16b_ONERI_OKUMA_ISTISNASI_DAR_YAKALANIR_YAZMAYA_SIZMAZ(tmp_path):
    """K1 devamı — d16 KENDİSİ (chmod 0o000) bu mutasyonu YAKALAMAZ: dosya hem okuma hem yazma
    izni kaybettiğinden, `except FileNotFoundError`ın YERİNE geniş bir `except Exception`
    konsa bile betiğin SONUNDAKİ geri-okuma adımı AYNI izin hatasıyla YİNE çöker — CLI yine
    KIRMIZI görünür, mutasyon sahte-yeşil kalırdı. Bu yüzden burada dosya YALNIZ YAZMAYA açık
    bırakılır (chmod 0o200): orijinal kod ilk `open(...).read()`de PermissionError'ı
    YAKALAMADAN (yalnız FileNotFoundError yakalanır) çöker VE APPEND'E HİÇ ULAŞMAZ — disk hâlâ
    ÖNCEKİ hâlindedir. Geniş bir `except` konsaydı ilk okuma sessizce boş sayılır, AKB-0001
    hesaplanır ve APPEND GERÇEKTEN ÇALIŞIRDI (append yazma izni ister, okuma değil) — disk
    kirlenirdi, CLI yine "kırmızı" görünse bile (son geri-okuma adımı ayrıca çöktüğü için)."""
    if os.geteuid() == 0:
        pytest.skip("root için chmod 0o200 okumayı engellemez — bu ortamda ölçülemez")
    mod = _yukle()
    ort, _, defter = _gercek_nisanci(tmp_path, mod)
    onceki_icerik = '{"ts": "x", "olay": "oneri", "oneri_id": "AKB-0007", "kaynak": "rol1", "oneri": "eski"}\n'
    defter.write_text(onceki_icerik, encoding="utf-8")
    defter.chmod(0o200)  # yalnız YAZILABİLİR — okuma izni YOK
    try:
        r = _cli("oneri", "bir fikir", "--kaynak", "operator", ort=ort)
        defter.chmod(0o644)
        sonraki_icerik = defter.read_text(encoding="utf-8")
    finally:
        defter.chmod(0o644)
    assert r.returncode == 1, f"okunamayan (yalnız-yazılabilir) defterde oneri YEŞİL geçti:\n{r.stdout}\n{r.stderr}"
    assert sonraki_icerik == onceki_icerik, (
        f"CLI kırmızı döndü AMA disk DEĞİŞMİŞ — okuma istisnası sessizce yutulup APPEND yine de "
        f"çalışmış olabilir (dar `except FileNotFoundError` genişletilmiş olabilir):\n"
        f"öncesi={onceki_icerik!r}\nsonrası={sonraki_icerik!r}")


def test_d17_LISTELE_SONUC_SATIRLARINI_GOSTERIR(tmp_path):
    """Ö1 (ÖNEMLİ, Yasa-6 bulgusu): `olay=sonuc` satırları deftere yazılıyordu ama HİÇBİR
    okuyucusu yoktu (`akibet_turet` bilinçli olarak yüzeye çıkarmıyor — bkz. `sonuclar`
    docstring'i). `listele` artık son sonuçları asgari biçimde gösterir — yeni bir alt komut
    YOK, `listele`nin var olan çıktısına ekleniyor.

    Y3 düzeltmesi (yeniden-inceleme 2026-08-31): eski hâli yalnız `ozet`i arıyordu, `ref`
    ALANINI hiç ölçmüyordu — `ref_parcasi` satırını silen bir mutasyon suite'i YEŞİL bırakırdı."""
    mod = _yukle()
    ort, proposals, defter = _gercek_nisanci(tmp_path, mod)
    _satir_yaz(proposals, [_n("N00001", "2026-08-01T00:00:00+00:00")])
    _satir_yaz(defter, [
        _karar_satiri("N00001", "2026-08-10T00:00:00+00:00", karar="uygulandi"),
        {"ts": "2026-08-15T00:00:00+00:00", "olay": "sonuc", "oneri_id": "N00001",
         "ozet": "beklenenden iyi çıktı", "ref": "PR-7"},
    ])
    r = _cli("listele", ort=ort)
    assert r.returncode == 0, r.stderr
    assert "N00001" in r.stdout and "beklenenden iyi çıktı" in r.stdout, (
        f"sonuç satırı listele çıktısında okunamıyor (Yasa-6 ihlali sürüyor):\n{r.stdout}")
    assert "PR-7" in r.stdout, (
        f"sonuç satırının `ref` alanı listele çıktısında okunamıyor (Y3, Yasa-6 yarım ölçüm):"
        f"\n{r.stdout}")


def test_d17b_LISTELE_SONUC_EKSIK_ALAN_OLCULEMEDI_BASAR_NONE_DEGIL(tmp_path):
    """Y4 (yeniden-inceleme 2026-08-31): `sonuclar()` yalnız `oneri_id`yi zorunlu tutar —
    `ozet`/`ts` eksik bir `sonuc` satırı süzgeçten geçer. Açık tablosu (Kü4) `None` yerine
    "ÖLÇÜLEMEDİ" basıyordu ama "son sonuçlar" bloğu bunu TEKRARLAMAMIŞTI — literal `None`
    metni basılırdı (aynı fonksiyonda iki farklı sözleşme, Kü4'ün ta kendisi)."""
    mod = _yukle()
    ort, proposals, defter = _gercek_nisanci(tmp_path, mod)
    _satir_yaz(proposals, [_n("N00001", "2026-08-01T00:00:00+00:00")])
    _satir_yaz(defter, [
        _karar_satiri("N00001", "2026-08-10T00:00:00+00:00", karar="uygulandi"),
        {"ts": "2026-08-15T00:00:00+00:00", "olay": "sonuc", "oneri_id": "N00001"},  # ozet YOK
    ])
    r = _cli("listele", ort=ort)
    assert r.returncode == 0, r.stderr
    assert "ÖLÇÜLEMEDİ" in r.stdout, (
        f"eksik `ozet` alanı için ÖLÇÜLEMEDİ basılmıyor:\n{r.stdout}")
    assert "None" not in r.stdout, (
        f"eksik alan literal 'None' olarak basılmış (Kü4 tekrar etti, Y4):\n{r.stdout}")


def test_d18_KARAR_VEREN_GECERSIZ_DEGERDE_ARGPARSE_REDDEDER(tmp_path):
    """Ö4: `KARAR_VERENLER` `ONERI_KAYNAKLARI`dan AYRI adlandırıldı (eskiden tek `ROLLER` sabiti
    ikisini de taşıyordu) — argparse `choices` HÂLÂ bağımsız uygulanıyor mu, geçersiz bir
    `--veren` argparse kullanım hatası (rc=2) ile reddediliyor mu diye ölçer.

    GÜVENLİK: `_nisanci` ile PATH'e sahte bir `ssh` konur — argparse GEÇERLİ kodda `_karar`a hiç
    ULAŞMADAN reddeder (ssh hiç çağrılmaz), ama bu YALITIM KENDİSİ TEST EDİLEN ŞEYDİR: `choices=`
    kaldırılmış bir mutasyonda (Ö4 mutasyon turu, 2026-08-31) tam olarak BU test PATH sahtesi
    OLMADAN GERÇEK `ssh`i `ubuntu@130.61.126.87`ye ÇAĞIRDI ve gerçek A1 üretim defterine
    (`/opt/meridian/state/oneri_akibet.jsonl`) sahte bir `karar` satırı YAZDI (oneri_id=N00001,
    karar_veren="boyle-bir-rol-yok", gerekce=25×'x') — operatöre AYRICA bildirildi. Artık HER
    CLI çağrısı, argparse'ın kendisi güvenilir olsa BİLE, gerçek ssh'a asla ULAŞAMAYACAK şekilde
    sahte PATH'le sarılır (savunma-derinliği, `_nisanci` iz bırakır — sessizce gerçek ssh'a
    kaymışsa `iz.exists()` bunu YAKALAR)."""
    ort, iz = _nisanci(tmp_path)
    r = _cli("karar", "N00001", "uygulandi", "--gerekce", "x" * 25, "--veren", "boyle-bir-rol-yok",
              ort=ort)
    assert not iz.exists(), (
        f"argparse geçersiz --veren'i REDDETMEDİ, ssh'a ULAŞILDI (gerçek ortamda bu GERÇEK A1'e "
        f"giderdi!): {iz.read_text(encoding='utf-8') if iz.exists() else ''!r}")
    assert r.returncode == 2, f"{r.returncode}\n{r.stdout}\n{r.stderr}"


def test_d14_ONERI_YAZIM_DOGRULANAMAZSA_CLI_KIRMIZI(tmp_path):
    """Uzak zincir RC=0 dönse bile geri okunan satır BAŞKA bir şeyse (sahte başarı sınıfı) CLI
    KIRMIZI döner. Nişancı GERİ OKUMAYI sahtekarlıkla DEĞİŞTİRİR: gerçek `python3 -c` zincirini
    koşturur (dosyaya GERÇEKTEN doğru satır yazılır) ama STDOUT'u sahte bir satırla DEĞİŞTİRİR —
    Ö2 sonrası `oneri` artık `tail -1` DEĞİL, uzak scriptin KENDİ `sys.stdout.buffer` yazımını
    kullanır; nişancı bunu `"python3 -c"` işaretiyle yakalar."""
    mod = _yukle()
    kutu = tmp_path / "bin"
    kutu.mkdir()
    defter = tmp_path / "d.jsonl"
    kilit = tmp_path / "d.jsonl.lock"
    proposals = tmp_path / "p.jsonl"
    flock_path = _flock_yolu(tmp_path)
    sh = kutu / "ssh"
    program = f"""#!{sys.executable}
import os, subprocess, sys
komut = sys.argv[-1]
komut = komut.replace({mod.KILIT!r}, {str(kilit)!r}).replace({mod.DEFTER!r}, {str(defter)!r})
komut = komut.replace({mod.PROPOSALS!r}, {str(proposals)!r})
ort = dict(os.environ); ort["PATH"] = {flock_path!r}
p = subprocess.run(["sh", "-c", komut], capture_output=True, text=True, env=ort)
if "python3 -c" in komut:
    sys.stdout.write("baska-bir-satir-sahte-basari\\n")
else:
    sys.stdout.write(p.stdout)
sys.stderr.write(p.stderr)
sys.exit(p.returncode)
"""
    sh.write_text(program, encoding="utf-8")
    sh.chmod(0o755)
    r = _cli("oneri", "bir fikir", "--kaynak", "operator", ort={"PATH": str(kutu)})
    assert r.returncode == 1, f"sahte geri-okuma YEŞİL geçti:\n{r.stdout}\n{r.stderr}"
    assert "DOĞRULANAMADI" in r.stderr.upper(), r.stderr
    # dosyaya GERÇEKTEN doğru satır yazıldı (zincirin kendisi sağlam) — yalnız GERİ OKUMA sahte
    assert json.loads(defter.read_text(encoding="utf-8").splitlines()[-1])["oneri"] == "bir fikir"


def test_d14b_KARAR_YAZIM_DOGRULANAMAZSA_CLI_KIRMIZI_VE_STDERR(tmp_path):
    """`karar`/`sonuc` HÂLÂ `tail -1` kullanır (Ö2 yalnız `oneri`yi değiştirdi) — aynı sahte-tail
    sınıfı orada da ölçülür, VE Kü6 düzeltmesi: hata mesajı STDOUT DEĞİL STDERR'e gider."""
    mod = _yukle()
    kutu = tmp_path / "bin"
    kutu.mkdir()
    defter = tmp_path / "d.jsonl"
    kilit = tmp_path / "d.jsonl.lock"
    proposals = tmp_path / "p.jsonl"
    _satir_yaz(proposals, [_n("N00001", "2026-08-01T00:00:00+00:00")])
    flock_path = _flock_yolu(tmp_path)
    sh = kutu / "ssh"
    program = f"""#!{sys.executable}
import os, subprocess, sys
komut = sys.argv[-1]
komut = komut.replace({mod.KILIT!r}, {str(kilit)!r}).replace({mod.DEFTER!r}, {str(defter)!r})
komut = komut.replace({mod.PROPOSALS!r}, {str(proposals)!r})
ort = dict(os.environ); ort["PATH"] = {flock_path!r}
p = subprocess.run(["sh", "-c", komut], capture_output=True, text=True, env=ort)
if "tail -1" in komut:
    sys.stdout.write("baska-bir-satir-sahte-basari\\n")
else:
    sys.stdout.write(p.stdout)
sys.stderr.write(p.stderr)
sys.exit(p.returncode)
"""
    sh.write_text(program, encoding="utf-8")
    sh.chmod(0o755)
    r = _cli("karar", "N00001", "uygulandi", "--gerekce", "x" * 25, "--veren", "operator",
             ort={"PATH": str(kutu)})
    assert r.returncode == 1, f"sahte tail çıktısı YEŞİL geçti:\n{r.stdout}\n{r.stderr}"
    assert "DOĞRULANAMADI" in r.stderr.upper(), (
        f"hata mesajı STDERR'de değil (Kü6 düzeltmesi):\n{r.stderr!r}")
    assert "DOĞRULANAMADI" not in r.stdout.upper(), (
        f"hata mesajı hâlâ STDOUT'a sızıyor:\n{r.stdout!r}")


# ── j. --komut-yaz HİÇBİR DALDAN ssh çalıştırmaz (v348 sözleşmesi) ──────────

@pytest.mark.parametrize("bayrak", [
    ("listele", "--komut-yaz"),
    ("oneri", "bir fikir", "--kaynak", "operator", "--komut-yaz"),
    ("karar", "N00001", "uygulandi", "--gerekce", "x" * 25, "--veren", "operator", "--komut-yaz"),
    ("karar", "N00001", "uygulandi", "--gerekce", "x" * 25, "--veren", "operator", "--zorla",
     "--komut-yaz"),
    ("sonuc", "N00001", "--ozet", "yapıldı", "--komut-yaz"),
    ("sonuc", "N00001", "--ozet", "yapıldı", "--ref", "x", "--komut-yaz"),
])
def test_j1_KOMUT_YAZ_HICBIR_DALDAN_SSH_CAGIRMAZ(tmp_path, bayrak):
    ort, iz = _nisanci(tmp_path)
    r = _cli(*bayrak, ort=ort)
    assert r.returncode == 0, f"{bayrak} rc={r.returncode}\n{r.stdout}\n{r.stderr}"
    assert not iz.exists(), f"{bayrak} GERÇEKTEN ssh çalıştırdı: {iz.read_text(encoding='utf-8')!r}"


def test_j2_POZITIF_KONTROL_NISANCI_GERCEKTEN_OTER(tmp_path):
    """Nişancı ötmüyorsa j1 BOŞ bir çividir. Önce ötebildiğini göster."""
    ort, iz = _nisanci(tmp_path)
    r = _cli("listele", ort=ort)
    assert iz.exists(), (
        f"nişancı ötmedi: `listele` ssh'ı hiç çalıştırmadı ya da PATH'ten çözmedi\n"
        f"rc={r.returncode}\n{r.stdout}\n{r.stderr}")


def test_j3_ONERI_KOMUT_YAZ_GERCEK_ATOMIK_ZINCIRI_BASAR_YER_TUTUCU_YOK(tmp_path):
    """Ö2 sonrası `oneri --komut-yaz` artık YER TUTUCU id basmaz (eski "AKB-????" tasarımı
    emekli oldu) — id hesaplaması komutun KENDİSİNE (uzak `python3 -c` betiği, `flock` içinde)
    taşındı; basılan şey GERÇEK, doğrudan koşulabilir zincirdir.

    GÜVENLİK: `_nisanci` savunma-derinliği için burada da eklendi — `--komut-yaz`ın kendisi
    (`filo._ssh_kos`) korusa da, bu test SADECE o mekanizmayı SINAMAK için var; ikinci bağımsız
    bir kilit (PATH'te sahte ssh) tek hata noktasını YOK eder (bkz. test_d18 GÜVENLİK notu)."""
    ort, iz = _nisanci(tmp_path)
    r = _cli("oneri", "bir fikir", "--kaynak", "operator", "--komut-yaz", ort=ort)
    assert not iz.exists(), f"--komut-yaz GERÇEK ssh'a ulaştı: {iz.read_text(encoding='utf-8')!r}"
    assert r.returncode == 0, r.stderr
    assert "AKB-????" not in r.stdout, r.stdout
    assert "YER TUTUCU" not in r.stdout.upper(), r.stdout
    # basılan komut TEK satır DEĞİL — uzak python3 betiği çok satırlı kaynak taşır ve bu, tek
    # tırnaklı bir kabuk dizgesi içinde GERÇEK satır-sonlarıyla katıştırılır (POSIX'te geçerli:
    # tek tırnak içinde satır sonu harfiyen korunur, operatör tüm bloğu olduğu gibi yapıştırabilir).
    # bu yüzden ölçüt "ilk satır ssh ile başlar" + "içerik TÜM çıktıda geçer"dir, "SON satır" değil.
    ilk_satir = r.stdout.strip().splitlines()[0]
    assert ilk_satir.startswith("ssh "), r.stdout
    assert "flock" in r.stdout, r.stdout
    assert "python3 -c" in r.stdout, r.stdout
    assert "bir fikir" in r.stdout, r.stdout


def test_j3b_ONERI_KOMUT_YAZ_CIKTISI_GERCEKTEN_TEK_KOMUT_OLARAK_YAPISTIRILABILIR(tmp_path, tmp_path_factory):
    """test_j3'ün varsayımını (çok satırlı basılan metin, tek tırnak içindeki gerçek satır
    sonlarıyla, YİNE DE tek bir POSIX komutudur) KANITLAR: basılan TAM metni olduğu gibi bir
    `sh -c`ye besleyip nişancının TAM OLARAK BİR kez ve doğru argüman SAYISIYLA (`ssh -i <anahtar>
    <host> <uzak-komut>` → 4 argüman) çağrıldığını ölçer. Bu olmasaydı operatör kopyala-yapıştır
    yaptığında komut sessizce ikiye bölünüp YARIM koşabilirdi — ölçülmeden varsayılmayacak tam
    da bu sınıftan bir risk.

    GÜVENLİK (Y1, R2 yeniden-inceleme 2026-08-31): bu testin İLK `_cli` çağrısı `ort=` VERMEDEN
    yazılmıştı — `--komut-yaz`ın erken-dönüşü koruyordu ama bu tam da GÜVENLİK OLAYININ (R1
    raporu) AYNI SINIFI: `--komut-yaz` bir mutasyonda kaldırılırsa bu çağrı GERÇEK ssh'a, GERÇEK
    A1'e, GERÇEK bir `oneri` (append-only, silinemeyen bir AKB-#### doğum satırı) yazardı. Artık
    `_nisanci` ile sarılı — ikinci `_cli` çağrısının (aşağıda) kullandığı `tmp_path/"bin"`la
    ÇAKIŞMAMASI için AYRI bir `tmp_path_factory.mktemp(...)` dizini kullanılıyor."""
    ort, guard_iz = _nisanci(tmp_path_factory.mktemp("j3b_ilk_cagri_guard"))
    r = _cli("oneri", "bir fikir", "--kaynak", "operator", "--komut-yaz", ort=ort)
    assert not guard_iz.exists(), (
        f"--komut-yaz GERÇEK ssh'a ulaştı: {guard_iz.read_text(encoding='utf-8')!r}")
    assert r.returncode == 0, r.stderr
    basilan = r.stdout  # TAM çıktı — satırlara bölmeden, olduğu gibi
    kutu = tmp_path / "bin"
    kutu.mkdir()
    iz = tmp_path / "ssh-cagrildi.iz"
    sh = kutu / "ssh"
    sh.write_text(f'#!/bin/sh\nprintf "%s\\n" "$#" >> {iz}\nexit 0\n', encoding="utf-8")
    sh.chmod(0o755)
    # PATH'in ÖNÜNE eklenir, YERİNE DEĞİL: `sh`nin kendisi de PATH'ten çözülür, sadece
    # fake `ssh` gerçek ssh'ın ÖNÜNE geçmeli.
    p = subprocess.run(["sh", "-c", basilan], capture_output=True, text=True,
                        env={**os.environ, "PATH": f"{kutu}{os.pathsep}{os.environ.get('PATH', '')}"})
    assert p.returncode == 0, f"yapıştırılan komut sh içinde patladı:\n{p.stdout}\n{p.stderr}"
    assert iz.exists(), (
        f"yapıştırılan komut ssh'ı hiç çağırmadı (kabuk sessizce başka bir şey yaptı)\n"
        f"basılan:\n{basilan}")
    cagrilar = iz.read_text(encoding="utf-8").splitlines()
    assert cagrilar == ["4"], (
        f"ssh TAM OLARAK BİR kez ve 4 argümanla (-i, anahtar, host, uzak-komut) çağrılmalıydı, "
        f"gözlenen çağrı(lar): {cagrilar!r}\nbasılan:\n{basilan}")


def test_j1b_KOMUT_YAZ_ICERIK_KARAR_VE_SONUC_ALANLARINI_DOGRU_TASIR(tmp_path_factory):
    """Ö3: eski j1 yalnız rc==0 VE ssh-çağrılmadı ölçer — incelemenin bulduğu hayatta-kalan
    mutasyon (komut_yaz dalında `satir` içeriği bozulsa/sabitlense bile j1 YEŞİL kalırdı,
    çünkü içerik hiç okunmuyordu) burada BASILAN komutun GERÇEKTEN doğru alanları taşıdığını
    ölçerek ölür. `ilk baştaki satır` yerine TÜM çıktıda arıyoruz: `ekleme_komutu` tek satır
    üretir ama bu ayrım testin varsayımı olmamalı — üretilen komutun BİÇİMİ değil İÇERİĞİ konu."""
    ort, iz = _nisanci(tmp_path_factory.mktemp("j1b_karar"))
    r = _cli("karar", "N00042", "reddedildi", "--gerekce", "x" * 30, "--veren", "rol1",
              "--komut-yaz", ort=ort)
    assert r.returncode == 0, r.stderr
    assert not iz.exists()
    ilk_satir = r.stdout.strip().splitlines()[0]
    assert ilk_satir.startswith("ssh "), r.stdout
    assert "N00042" in r.stdout, r.stdout
    assert "reddedildi" in r.stdout, r.stdout
    assert "rol1" in r.stdout, r.stdout
    assert "x" * 30 in r.stdout, r.stdout

    ort2, iz2 = _nisanci(tmp_path_factory.mktemp("j1b_sonuc"))
    r2 = _cli("sonuc", "N00042", "--ozet", "gözlenen etki büyük", "--ref", "PR-9",
               "--komut-yaz", ort=ort2)
    assert r2.returncode == 0, r2.stderr
    assert not iz2.exists()
    ilk_satir2 = r2.stdout.strip().splitlines()[0]
    assert ilk_satir2.startswith("ssh "), r2.stdout
    assert "N00042" in r2.stdout, r2.stdout
    assert "gözlenen etki büyük" in r2.stdout, r2.stdout
    assert "PR-9" in r2.stdout, r2.stdout


def test_j4_HOST_VE_ANAHTAR_CLI_DAN_GECERSIZ_KILINIR(tmp_path):
    """GÜVENLİK: `_nisanci` savunma-derinliği (bkz. test_j3 GÜVENLİK notu, test_d18 olayı)."""
    ort, iz = _nisanci(tmp_path)
    r = _cli("listele", "--komut-yaz", "--host", "ubuntu@10.0.0.9", "--anahtar", "/tmp/k.key",
              ort=ort)
    assert not iz.exists(), f"--komut-yaz GERÇEK ssh'a ulaştı: {iz.read_text(encoding='utf-8')!r}"
    assert r.returncode == 0, r.stderr
    assert "ubuntu@10.0.0.9" in r.stdout and "/tmp/k.key" in r.stdout, r.stdout


def test_j5_ENV_KIMLIK_UC_KATMANLI(tmp_path):
    """GÜVENLİK: `_nisanci` savunma-derinliği (bkz. test_j3 GÜVENLİK notu, test_d18 olayı) —
    env değişkenleri zaten host'u sahte bir IP'ye çeviriyordu, PATH kilidi İKİNCİ bağımsız katman."""
    mod = _yukle()
    nisanci_ort, iz = _nisanci(tmp_path)
    ort = {**nisanci_ort, mod.filo.ENV_KULLANICI: "root", mod.filo.ENV_IP: "10.1.2.3",
           mod.filo.ENV_ANAHTAR: "/tmp/env.key"}
    r = _cli("listele", "--komut-yaz", ort=ort)
    assert not iz.exists(), f"--komut-yaz GERÇEK ssh'a ulaştı: {iz.read_text(encoding='utf-8')!r}"
    assert r.returncode == 0, r.stderr
    assert "root@10.1.2.3" in r.stdout and "/tmp/env.key" in r.stdout, r.stdout


def test_j6_SISTEMIK_KILIT_PATHTEKI_SSH_GERCEGI_GOLGELER():
    """Y1 sistemik kilidinin (`_sistemik_ssh_kilidi`, autouse) KENDİSİNİ, `ops/akibet.py`'nin
    doğruluğundan TAMAMEN BAĞIMSIZ olarak sınar — bu test `_cli`/`ort=`/akibet.py'ye HİÇ
    dokunmaz. Bu dosyadaki HER test otomatik olarak PATH'in başına sahte bir `ssh` almış
    ortamda koştuğu için, `subprocess.run(["ssh", ...])` GERÇEK `/usr/bin/ssh`e DEĞİL bu sahte
    betiğe düşer — `akibet.py`'nin KENDİ `--komut-yaz`/`_ssh_kos` mantığı ne kadar bozulursa
    bozulsun (bkz. R1 güvenlik olayı, Y1 mutasyon turu) bu İKİNCİ, BAĞIMSIZ katman ayakta kalır.
    `rc=113` ve `_GUARD_ISARET`, gerçek `ssh` İLE karıştırılamayacak belirgin bir imzadır."""
    p = subprocess.run(["ssh", "-i", "/tmp/boyle-bir-anahtar-yok.key", "ubuntu@130.61.126.87",
                        "echo test"], capture_output=True, text=True)
    assert p.returncode == 113, (
        f"sahte-ssh devrede DEĞİL — gerçek ssh'a ULAŞILMIŞ OLABİLİR: rc={p.returncode}\n"
        f"stdout={p.stdout!r}\nstderr={p.stderr!r}")
    assert _GUARD_ISARET in p.stderr, p.stderr


# ═══════════════════════════════════════════════════════════════════════════
#  E. `ops/oneri_brifingi.py` SÜZGECİ — akıbet defteri brifinge girer (T2)
# ═══════════════════════════════════════════════════════════════════════════
#
# NE ÖLÇÜLÜR. `ozet_kur()` artık akıbet defterini YEREL dosyadan okur (A1'de bu betik defterin
# yanında koşar — ssh YOK) ve `akibet_turet` ile birleştirir. Üç blok: yeni · karara bağlanan ·
# açık yaş satırı. ASIL DAVRANIŞ: karara bağlanmış bir öneri "yeni" listesine BİR DAHA GİRMEZ —
# bu betiğin var oluş sebebindeki kusur tam olarak buydu.
#
# BU BÖLÜM `ops/akibet.py`YE DOKUNMAZ (T1'in sözleşmesi donuk): yalnız onun SAF çekirdeğini
# tüketen tarafı ölçer. Dosyanın autouse `_sistemik_ssh_kilidi` fikstürü burada da geçerlidir —
# yani bu bölümdeki hiçbir test gerçek ssh'a ULAŞAMAZ (ve `test_e12` bunu ayrıca ölçer).

from datetime import datetime, timedelta, timezone  # noqa: E402

BRIFING_BETIK = KOK / "ops/oneri_brifingi.py"

#: Mesaj blokları işaretleriyle ayrışır (operatör metninde başlık yok — tek mesaj zarfı).
_BLOK_ISARETLERI = ("⚠", "🧠", "✅", "📌")


def _brifing():
    assert BRIFING_BETIK.exists(), f"{BRIFING_BETIK} YOK"
    return betikten_modul_yukle(BRIFING_BETIK, "oneri_brifingi")


def _bloklar(mesaj: str) -> dict:
    """Mesajı işaretine göre bloklara ayırır — bir çivi "hangi blokta" sorusunu SORABİLSİN diye.
    Aynı işaretli iki blok (iki ayrı ⚠) BİRLEŞTİRİLİR, biri ötekini SİLMEZ."""
    out: dict = {}
    aktif = None
    for satir in mesaj.splitlines():
        if satir[:1] in _BLOK_ISARETLERI:
            aktif = satir[:1]
            out[aktif] = (out[aktif] + "\n" + satir) if aktif in out else satir
        elif aktif is not None:
            out[aktif] += "\n" + satir
    return out


def _gun_once(n: int) -> str:
    """`n` tam gün önceki UTC damgası — yaş satırı GERÇEK bir sayı üzerinden ölçülsün diye
    (sabit bir tarih yazmak, testi takvimle birlikte çürütürdü)."""
    return (datetime.now(timezone.utc) - timedelta(days=n, hours=1)).isoformat(timespec="seconds")


def _oneri_satiri(id_: str, ts: str, alan: str = "x", oneri: str = "bir iyileştirme") -> dict:
    return {"ts": ts, "id": id_, "alan": alan, "oneri": oneri}


def _defter_yaz(sandbox_state, satirlar: list[dict]) -> pathlib.Path:
    """Akıbet defterini SANDBOX `state/` altına yazar — bu okuma `config.STATE`e bağlıdır, yani
    testler CANLI `/opt/meridian/state/oneri_akibet.jsonl`e ASLA bakmaz."""
    yol = pathlib.Path(sandbox_state) / "oneri_akibet.jsonl"
    _satir_yaz(yol, satirlar)
    return yol


def _karar(oneri_id: str, karar: str = "uygulandi", ts: str | None = None,
           veren: str = "rol1", gerekce: str = "ölçüldü ve tek turda uygulandı, kapanış commit'i") -> dict:
    return {"ts": ts or _gun_once(0), "olay": "karar", "oneri_id": oneri_id, "karar": karar,
            "gerekce": gerekce, "karar_veren": veren}


def test_e1_KARARA_BAGLANAN_ONERI_YENI_SAYILMAZ(sandbox_state):
    """ASIL ÇİVİ. Karara bağlanmış bir öneri `yeni` listesine BİR DAHA GİRMEZ.

    KAPATILAN ARIZA (bu dalganın var oluş sebebi): `improvement_proposals.jsonl` yalnız DOĞUMU
    taşır. Damga da yalnız "en son ne zamana kadar bildirdim"i taşır. İkisi birlikte "bu öneri
    karara bağlandı" bilgisini TAŞIYAMAZ — o yüzden bir öneri karara bağlansa bile, damga
    ilerlemediği sürece her brifingde yeniden "yeni öneri" diye sayılırdı.

    Ölçüm iki taraflıdır: karara bağlanan `yeni` SAYIsından düşer VE "yeni öneriler" bloğunda
    ADIYLA GÖRÜNMEZ (yalnız sayının düşmesi, kimliği listede bırakan bir kusuru kaçırırdı)."""
    mod = _brifing()
    from meridian import store
    store.write_jsonl("improvement_proposals.jsonl", [
        _oneri_satiri("N00017", _gun_once(9), "coverage.hotstate", "watchdog sayacını dışa aç"),
        _oneri_satiri("N00018", _gun_once(3), "risk.kapi", "ikinci kapıyı ölç"),
    ])
    _defter_yaz(sandbox_state, [_karar("N00017")])

    o = mod.ozet_kur()
    assert o["yeni"] == 1, (
        f"karara bağlanmış öneri hâlâ 'yeni' sayılıyor: {o['yeni']} — sef her brifingde aynı "
        f"öneriyi tekrarlar ({o['mesaj']!r})")
    yeni_blok = _bloklar(o["mesaj"])["🧠"]
    assert "N00018" in yeni_blok, f"açık öneri yeni bloğundan düştü: {yeni_blok!r}"
    assert "N00017" not in yeni_blok, (
        f"karara bağlanan öneri 'yeni öneriler' bloğunda ADIYLA duruyor: {yeni_blok!r}")


def test_e2_KARARA_BAGLANAN_KENDI_BLOGUNDA_CUMLEYLE_GORUNUR(sandbox_state):
    """Kaybolmaz, YER DEĞİŞTİRİR: karara bağlanan öneri kendi bloğunda birer cümleyle görünür.
    Yalnız 'yeni'den düşürmek, operatöre kararın gerçekleştiğini HİÇ söylemezdi."""
    mod = _brifing()
    from meridian import store
    store.write_jsonl("improvement_proposals.jsonl", [
        _oneri_satiri("N00017", _gun_once(9)),
        _oneri_satiri("N00018", _gun_once(3)),
    ])
    _defter_yaz(sandbox_state, [
        _karar("N00017", "reddedildi", veren="operator",
               gerekce="ölçüm kartı yok, hipotez kanıtsız kaldı"),
    ])

    o = mod.ozet_kur()
    karar_blok = _bloklar(o["mesaj"])["✅"]
    assert "N00017" in karar_blok and "reddedildi" in karar_blok, karar_blok
    assert "operatör" in karar_blok, f"kararı VEREN taraf operatör diliyle yazılmadı: {karar_blok!r}"
    assert "ölçüm kartı yok" in karar_blok, f"gerekçe cümleye girmedi: {karar_blok!r}"


def test_e3_YAS_SATIRI_MESAJ_URETILEN_HER_TURDA_VE_YASI_GERCEKTEN_OLCER(sandbox_state):
    """Yaş satırı TEK KOMPAKT satırdır, en eski önce, ve yaş GERÇEKTEN hesaplanır.

    Yaş sırası `akibet_turet`ten geldiği gibi korunur — burada ikinci bir sıralama kuralı
    yazılsaydı ikisi zamanla ayrışırdı (tek-kaynak yasası)."""
    mod = _brifing()
    from meridian import store
    store.write_jsonl("improvement_proposals.jsonl", [
        _oneri_satiri("N00012", _gun_once(9)),
        _oneri_satiri("N00005", _gun_once(21)),
    ])
    _defter_yaz(sandbox_state, [])

    o = mod.ozet_kur()
    yas = _bloklar(o["mesaj"])["📌"]
    assert yas.startswith("📌 2 açık:"), f"açık sayısı satırın başında yok: {yas!r}"
    assert "N00005 21g" in yas and "N00012 9g" in yas, f"yaşlar ölçülmedi: {yas!r}"
    assert yas.index("N00005") < yas.index("N00012"), (
        f"yaş sırası azalan değil (en eski önce olmalı): {yas!r}")
    assert "\n" not in yas, f"yaş satırı TEK satır olmalı: {yas!r}"
    assert o["acik_sayi"] == 2, o


def test_e4_DEFTER_YOKSA_HERKES_ACIK_BU_OLCULEMEDI_DEGILDIR(sandbox_state):
    """Henüz hiç karar yazılmamışsa defter DOSYASI yoktur — bu ÖLÇÜLMÜŞ AÇIKLIKTIR.

    Sıfır ile 'bilmiyorum' burada ayrılır: dosyanın yokluğu bir arıza değil bir DURUMDUR ve
    doğru cevabı "herkes açık"tır. Ölçülemedi sayılsaydı sistem, kendi normal ilk gününü bir
    arıza gibi raporlardı."""
    mod = _brifing()
    from meridian import store
    store.write_jsonl("improvement_proposals.jsonl", [
        _oneri_satiri("N00012", _gun_once(9)),
        _oneri_satiri("N00005", _gun_once(21)),
    ])
    assert not (pathlib.Path(sandbox_state) / "oneri_akibet.jsonl").exists()

    o = mod.ozet_kur()
    assert o["akibet_olculemedi"] is None, o["akibet_olculemedi"]
    assert o["acik_sayi"] == 2, f"defter yokken herkes açık sayılmadı: {o}"
    assert "ölçülemedi" not in _bloklar(o["mesaj"]).get("📌", ""), o["mesaj"]
    assert "📌 2 açık:" in o["mesaj"], o["mesaj"]


@pytest.mark.skipif(hasattr(os, "geteuid") and os.geteuid() == 0,
                    reason="root izinleri yok sayar — okunamayan dosya kurgulanamaz")
def test_e5_DEFTER_OKUNAMIYORSA_OLCULEMEDI_VE_DUSTUGUNU_SOYLER(sandbox_state):
    """DOSYA VAR AMA OKUNAMIYORSA bu SIFIR DEĞİL BİLMİYORUM'dur — ve eski davranışa
    (karara bağlananlar ayıklanmamış HAM SAYIM) düşülür ama SESSİZCE DEĞİL.

    Bu ayrım `test_e4`ün ikizidir ve ikisi birlikte ölçülmelidir: tek bir "defter boş" dalı,
    bir izin hatasını 'hiç karar verilmemiş' diye okurdu."""
    mod = _brifing()
    from meridian import store
    store.write_jsonl("improvement_proposals.jsonl", [_oneri_satiri("N00017", _gun_once(3))])
    yol = _defter_yaz(sandbox_state, [_karar("N00017")])
    yol.chmod(0o000)
    try:
        o = mod.ozet_kur()
    finally:
        yol.chmod(0o600)

    assert o["akibet_olculemedi"], f"okunamayan defter ölçülemedi sayılmadı: {o}"
    assert o["acik_sayi"] is None, f"okunamayan defterden açık sayısı UYDURULDU: {o}"
    assert "akıbet ölçülemedi — ham sayım: 1" in o["hata"], (
        f"eski davranışa SESSİZCE düşüldü — düştüğünü söyleyen cümle yok: {o!r}")
    assert o["yeni"] == 1, (
        f"karar ayıklanamazken ham sayım da düştü: {o} — sayı beyan edilmeliydi")
    assert not o["mesaj"], (
        f"beyan DÜŞEBİLİR kanaldan (mesaj) gidiyor: {o['mesaj']!r} — R1/Ö1: ölçüm zincirinin "
        "kırıldığının beyanı modelin susturabileceği kanaldan gidemez")
    assert "📌" not in o["hata"], (
        f"açık listesi çıkarılamazken yine de basıldı: {o['hata']!r}")


def test_e6_BOZUK_SATIR_SESSIZCE_ATILMAZ_BEYAN_EDILIR(sandbox_state):
    """BEDEL YASASI: akıbet katmanının kazancı (açık/karar ayrımı) ölçülüyorsa BEDELİ de
    ölçülür. Çözülemeyen bir defter satırı açık sayısını ve yaşları EKSİK bırakır; bu eksiklik
    operatöre söylenmezse körlüğün belirtisi hiçbir şeydir."""
    mod = _brifing()
    from meridian import store
    store.write_jsonl("improvement_proposals.jsonl", [_oneri_satiri("N00017", _gun_once(3))])
    yol = pathlib.Path(sandbox_state) / "oneri_akibet.jsonl"
    yol.write_text('{"ts": "2026-08-30T10:00:00+00:00", "olay": "sonuc", "oneri_id": "N00001",\n'
                   '{bu satır JSON değil}\n', encoding="utf-8")

    o = mod.ozet_kur()
    assert o["akibet_olculemedi"] is None, (
        f"bozuk SATIR, okunamayan DOSYA ile karıştırıldı: {o} — dosya okunabildi")
    assert "satır çözülemedi" in o["mesaj"], (
        f"çözülemeyen satırlar sessizce atıldı: {o['mesaj']!r}")


def test_e7_KARARA_BAGLANAN_SON_DAMGADAN_BERI_SUZULUR(sandbox_state):
    """Karar bloğu SON DAMGADAN BERİ yazılanları taşır — defterin tüm tarihçesini değil.
    Aksi hâlde bir yıl önceki karar her gün yeniden 'karara bağlandı' diye bildirilirdi."""
    mod = _brifing()
    from meridian import store
    store.write_jsonl("improvement_proposals.jsonl", [_oneri_satiri("N00020", _gun_once(1))])
    store.write_json(mod.DAMGA_DOSYA, {mod.DAMGA: {"ts": _gun_once(5), "son_ts": _gun_once(5)}})
    _defter_yaz(sandbox_state, [
        _karar("N00001", ts=_gun_once(30), gerekce="çok eski karar, damgadan çok önce yazıldı"),
        _karar("N00002", ts=_gun_once(2), gerekce="damgadan sonra yazılmış taze karar kaydı"),
    ])

    o = mod.ozet_kur()
    karar_blok = _bloklar(o["mesaj"])["✅"]
    assert "N00002" in karar_blok, f"damgadan sonraki karar bildirilmedi: {karar_blok!r}"
    assert "N00001" not in karar_blok, (
        f"damgadan ÖNCEKİ karar yeniden bildirildi: {karar_blok!r} — her gün tekrarlanırdı")


def test_e8_DAMGA_SOZLESMESI_DEGISMEDI_KARAR_TS_SI_DAMGAYI_ILERLETMEZ(monkeypatch, sandbox_state):
    """DAMGA SÖZLEŞMESİ DEĞİŞMEZ (plan, BAĞLAYICI): damga hâlâ TEK bir `son_ts`tir ve YALNIZ
    öneri satırlarından ilerler.

    NEDEN ÇİVİ. Karar satırının ts'si damgayı ilerletseydi (cazip bir "tekrarı önleme" çözümü),
    bir karar satırı, kendisinden ESKİ ts'li ama SONRA yazılmış bir öneriyi damganın gerisinde
    bırakıp KALICI olarak görünmez yapardı — dosyanın kendi docstring'inde adı konmuş 'wedge'
    sınıfı. Damgaya ikinci bir anahtar eklemek de yasaktır: iki damga, 'hangi kaynak nereye
    kadar bildirildi' sorusunu ölçülemez hâle getirir."""
    mod = _brifing()
    from meridian import store
    oneri_ts = _gun_once(4)
    store.write_jsonl("improvement_proposals.jsonl", [_oneri_satiri("N00030", oneri_ts)])
    _defter_yaz(sandbox_state, [
        _karar("N00031", ts=_gun_once(0), gerekce="bugün verilmiş karar, önerilerden çok taze"),
    ])
    monkeypatch.setattr(mod.notify, "configured", lambda: True)
    monkeypatch.setattr(mod.notify, "send", lambda _t: True)

    assert mod.main(["--uygula"]) == 0
    damga = (store.read_json(mod.DAMGA_DOSYA, {}) or {})[mod.DAMGA]
    assert set(damga) == {"ts", "son_ts", "kapsanan"}, (
        f"damga sözleşmesine anahtar eklendi/çıkarıldı: {damga!r}")
    assert damga["son_ts"] == oneri_ts, (
        f"damga karar satırının ts'siyle ilerledi: {damga['son_ts']!r} != {oneri_ts!r} — "
        "sonradan yazılan eski-ts'li öneri kalıcı olarak görünmez olurdu")


def test_e9_YOL_SABITI_TEK_KAYNAKTAN_TURER(sandbox_state):
    """Defterin adı `ops/akibet.py::DEFTER`den TÜRETİLİR; ikinci bir yol sabiti YAZILMAZ.

    İKİNCİ YARI TÜRETİMİN GEÇERLİLİK ŞARTIDIR: bu betik dosyayı `config.STATE` altında ADIYLA
    okur, yani türetim ancak defter `state/` dizinindeyken doğrudur. akibet.py yolu bir gün
    başka bir dizine taşırsa bu okuma SESSİZCE yanlış (var olmayan) dosyaya bakar ve her gün
    'herkes açık' der — çivi o gün öter."""
    mod = _brifing()
    akibet = _yukle()
    assert mod.AKIBET_DEFTER == pathlib.Path(akibet.DEFTER).name, (
        f"{mod.AKIBET_DEFTER!r} != {pathlib.Path(akibet.DEFTER).name!r}")
    assert pathlib.Path(akibet.DEFTER).parent.name == "state", (
        f"akıbet defteri artık `state/` altında değil ({akibet.DEFTER!r}) — `oneri_brifingi.py` "
        "onu `config.STATE` altında ADIYLA arıyor, yani sessizce YANLIŞ dosyaya bakardı")
    kaynak = BRIFING_BETIK.read_text(encoding="utf-8")
    assert akibet.DEFTER not in kaynak, (
        "mutlak defter yolu `oneri_brifingi.py`ye KOPYALANMIŞ — iki kopya sessizce ayrışır")


def test_e10_OPERATOR_SOZCUKLERI_AKIBET_SABITLERINI_KAPSAR():
    """Türkçe karşılıklar ÖLÇÜLEMEZ, yazılır — ama kaynak sabitlere KARŞI denetlenir.
    Yeni bir karar değeri (`ops/akibet.py::KARARLAR`) eklenip burası unutulursa brifing ham
    kimliği basmaya başlar ve bunu kimse görmez: ayrışma çivisi (tek-kaynak yasası)."""
    mod = _brifing()
    akibet = _yukle()
    eksik = [k for k in akibet.KARARLAR if k not in mod.KARAR_SOZCUKLERI]
    assert not eksik, f"karar değerlerinin operatör karşılığı yok: {eksik}"
    eksik_veren = [v for v in akibet.KARAR_VERENLER if v not in mod.VEREN_SOZCUKLERI]
    assert not eksik_veren, f"karar verenlerin operatör karşılığı yok: {eksik_veren}"


def test_e11_AKIBET_BLOKLARI_IC_AYRINTI_TASIMAZ(sandbox_state):
    """v323 ARAYÜZ DİLİ: operatörün okuduğu cümlede backtick'li alan adı, dosya adı ya da ham
    ASCII kimlik (`uygulandi`) olmaz — bunlar geliştiricinin kendine yazdığı kelimelerdir.

    KURGU R2/Y2 İLE GENİŞLETİLDİ: karara bağlanan önerinin DOĞUM satırı da yazılıyor, yoksa
    Kü3'ün açtığı yeni metin yüzeyi (`konu: …`) hiç basılmaz ve çivi onun ALTINDAN geçerdi —
    ölçtüğünü sandığı şeyi ölçmeyen çivi sınıfı. Yüzeyin GERÇEKTEN denetlendiği, `konu`nun
    varlığı ayrıca iddia edilerek çivilenir."""
    mod = _brifing()
    from meridian import store
    store.write_jsonl("improvement_proposals.jsonl", [_oneri_satiri("N00040", _gun_once(2))])
    _defter_yaz(sandbox_state, [
        {"ts": _gun_once(4), "olay": "oneri", "oneri_id": "AKB-0007", "kaynak": "operator",
         "oneri": "kapanış turunda ikinci bir bakış"},
        _karar("AKB-0007", "ertelendi", veren="operator",
               gerekce="kart açılana kadar bekliyor, ölçüm penceresi kapalı"),
    ])

    bloklar = _bloklar(mod.ozet_kur()["mesaj"])
    assert "konu: kapanış turunda ikinci bir bakış" in bloklar["✅"], (
        f"kurgu hatası: konu yüzeyi hiç basılmadı, çivi onu DENETLEYEMEZ: {bloklar['✅']!r}")
    for isaret in ("✅", "📌"):
        metin = bloklar[isaret]
        assert "`" not in metin, f"{isaret} bloğunda backtick: {metin!r}"
        assert ".jsonl" not in metin, f"{isaret} bloğunda dosya adı: {metin!r}"
        assert "oneri_id" not in metin, f"{isaret} bloğunda alan adı: {metin!r}"
        assert "None" not in metin, f"{isaret} bloğunda Python literali: {metin!r}"
    assert "ertelendi" in bloklar["✅"], bloklar["✅"]


@pytest.mark.skipif(hasattr(os, "geteuid") and os.geteuid() == 0,
                    reason="root izinleri yok sayar — okunamayan dosya kurgulanamaz")
def test_e11b_OLCULEMEDI_CUMLESI_IKI_KATMANLI(sandbox_state):
    """R1/Kü1 — v323'ün İKİ KATMANLI sözleşmesi ölçülemedi beyanında da geçerlidir.

    Eskiden ham istisna dizgesi (`PermissionError: … /opt/meridian/state/oneri_akibet.jsonl`)
    cümlenin ORTASINDAYDI: operatörün okuduğu birincil metne mutlak yol ve Python sınıf adı
    sızıyordu. Ayrım `Teşhis:` etiketiyle yapılır — ÖNCESİ insan cümlesidir (iç ayrıntı YOK),
    SONRASI beyan edilmiş teknik katmandır. Teşhis KALDIRILMAZ (teşhis edilemez beyan beyan
    değildir), yalnız yeri değişir."""
    mod = _brifing()
    from meridian import store
    store.write_jsonl("improvement_proposals.jsonl", [_oneri_satiri("N00042", _gun_once(2))])
    yol = _defter_yaz(sandbox_state, [_karar("N00043")])
    yol.chmod(0o000)
    try:
        o = mod.ozet_kur()
    finally:
        yol.chmod(0o600)

    assert "Teşhis:" in o["hata"], f"teknik katman etiketlenmemiş: {o['hata']!r}"
    insan, teknik = o["hata"].split("Teşhis:", 1)
    for desen in ("`", ".jsonl", "Error", "/opt/", "None"):
        assert desen not in insan, (
            f"insan cümlesinde iç ayrıntı ({desen!r}): {insan!r} — yeri `Teşhis:` katmanıdır")
    assert teknik.strip(), f"teşhis düşürülmüş — teşhis edilemez beyan beyan değildir: {o['hata']!r}"


def test_e12_OZET_KUR_SSH_CAGIRMAZ_YEREL_DOSYADAN_OKUR(monkeypatch, sandbox_state):
    """A1'de bu betik defterin YANINDA koşar: okuma YEREL dosyadandır, ssh GEREKMEZ.

    ÖLÇÜM DAVRANIŞSALDIR, metin araması değil: `akibet`in TEK alt-süreç noktası (`filo._kos`)
    patlayıcıyla değiştirilir. `ozet_kur()` yine de çalışıyorsa o yoldan HİÇ geçilmemiştir."""
    mod = _brifing()
    from meridian import store
    store.write_jsonl("improvement_proposals.jsonl", [_oneri_satiri("N00050", _gun_once(2))])
    _defter_yaz(sandbox_state, [_karar("N00051", gerekce="yerel okumanın ssh'sız olduğunu ölç")])

    def _patla(*a, **k):
        raise AssertionError("ozet_kur alt-süreç/ssh yoluna girdi — A1'de yerel dosya okunmalı")

    monkeypatch.setattr(mod._akibet.filo, "_kos", _patla)
    o = mod.ozet_kur()
    assert o["acik_sayi"] == 1, o


def test_e13_SEF_GOVDESI_DEGISMEDEN_UC_BLOGU_TASIR(monkeypatch, sandbox_state):
    """SÜZGEÇ SEF'İN GÖVDESİNE DOKUNMAZ: `@sef` kaynağın `mesaj`ını OLDUĞU GİBİ taşır, o yüzden
    akıbet blokları harness'ta hiçbir değişiklik olmadan brifinge girer.

    Bu çivi iki yönlüdür: (a) sef gövdesi akıbet defterini TANIMAZ (ikinci bir okuyucu = ikinci
    bir gerçek), (b) buna rağmen üç blok da ham brifing metninde GÖRÜNÜR. Blokları `mesaj`
    dışında bir anahtara koyan bir uygulama (a)'yı korur ama (b)'yi sessizce kaybederdi."""
    # `reload` DEĞİL `import_module` (R1/Kü7): kardeş çivi (`test_sef_brifingi_v330.py::
    # kaynak_modulleri`) da öyle yapar. `reload` modül gövdesini suite ortasında yeniden koşturur
    # (`HERMES_PROFIL_HOME`/`YAZMA_KOKU` env'den yeniden hesaplanır) — bu çivinin ölçtüğü şeye
    # hiçbir katkısı olmayan bir yan etki yüzeyi.
    import importlib
    sef = importlib.import_module("ops.sef_brifingi")
    from meridian import store
    store.write_jsonl("improvement_proposals.jsonl", [_oneri_satiri("N00060", _gun_once(6))])
    _defter_yaz(sandbox_state, [
        _karar("N00061", gerekce="dalga kapandı, çivi ve kayıt aynı commit'te"),
    ])
    monkeypatch.setattr(sef, "_alarm_ozeti", lambda: {"toplam": 0, "yeni": 0, "mesaj": ""})
    monkeypatch.setattr(sef, "_self_review", lambda: {})
    monkeypatch.setattr(sef, "_son_brifing", lambda: "")

    metin = sef._ham_metin(sef.topla())
    assert "N00060" in metin, f"yeni öneri bloğu brifinge girmedi: {metin!r}"
    assert "N00061" in metin, f"karara bağlanan bloğu brifinge girmedi: {metin!r}"
    assert "📌 1 açık:" in metin, f"açık yaş satırı brifinge girmedi: {metin!r}"
    assert "akibet" not in (KOK / "ops/sef_brifingi.py").read_text(encoding="utf-8"), (
        "`@sef` akıbet defterini KENDİSİ tanımaya başlamış — ikinci okuyucu ikinci gerçektir; "
        "kaynağın `ozet_kur()`u tek yüzeydir")


def test_e14_BOS_DEFTERDE_YENI_YOKKEN_YINE_SESSIZ(sandbox_state):
    """SESSİZLİK ŞARTI PAZARLIĞA KAPALI (v327): açık öneri VARLIĞI tek başına mesaj DOĞURMAZ.
    Yaş satırı bir bağlam bloğudur, teslimat sebebi değil — aksi hâlde günlük kadans, karar
    döndürmeyen bir bildirime dönüşürdü."""
    mod = _brifing()
    from meridian import store
    ts = _gun_once(3)
    store.write_jsonl("improvement_proposals.jsonl", [_oneri_satiri("N00070", ts)])
    store.write_json(mod.DAMGA_DOSYA, {mod.DAMGA: {"ts": ts, "son_ts": ts}})
    _defter_yaz(sandbox_state, [])

    o = mod.ozet_kur()
    assert o["yeni"] == 0 and not o["mesaj"], f"açık öneri tek başına mesaj doğurdu: {o!r}"
    assert o["acik_sayi"] == 1, o
    assert "1 açık" in o["not"], f"sessiz turda açık sayısı kayda geçmedi: {o['not']!r}"


def test_e15_OPERATOR_BICIMINDE_KOSUM_AKIBETI_BASAR(tmp_path):
    """ARAÇ, OPERATÖRÜN KOŞACAĞI BİÇİMDE BİR KEZ GERÇEKTEN KOŞTURULUR (18-çivi vakası: her şey
    yeşilken `--uygula` sessizce yok sayılıyordu).

    Betik AYRI BİR SÜREÇTE, `.venv/bin/python ops/oneri_brifingi.py` biçiminde koşar — yani
    modülün kendi `sys.path` bootstrap'ı ve `from ops import akibet` ithali de ÖLÇÜLÜR (pytest
    içinden yükleme bu iki riski GÖRMEZ). `MERIDIAN_ROOT` tmp'ye çevrilir: koşum CANLI yerel
    `state/`e (ve `obs` defterine) TEK BAYT yazamaz — CLAUDE.md §2'nin "davranış görmek istiyorsan
    sandbox'lı çivi yaz" reçetesi.

    Varsayılan dal KURU KOŞUMDUR: hiçbir şey gönderilmez, hiçbir damga basılmaz."""
    kok = tmp_path / "kok"
    (kok / "state").mkdir(parents=True)
    _satir_yaz(kok / "state" / "improvement_proposals.jsonl",
               [_oneri_satiri("N00080", _gun_once(5))])
    _satir_yaz(kok / "state" / "oneri_akibet.jsonl",
               [_karar("N00081", gerekce="operatör biçiminde koşum için gerçek karar satırı")])

    r = subprocess.run([sys.executable, str(BRIFING_BETIK)], capture_output=True, text=True,
                       env={**os.environ, "MERIDIAN_ROOT": str(kok)})
    assert r.returncode == 0, f"kuru koşum düştü: rc={r.returncode}\n{r.stdout}\n{r.stderr}"
    assert "akıbet: 1 açık" in r.stdout, (
        f"operatörün gördüğü satırda akıbet durumu YOK: {r.stdout!r}")
    assert "📌 1 açık: N00080" in r.stdout, f"yaş satırı basılmadı: {r.stdout!r}"
    assert "N00081" in r.stdout, f"karara bağlanan bloğu basılmadı: {r.stdout!r}"
    assert "KURU KOŞU" in r.stdout, f"varsayılan dal kuru koşum değil: {r.stdout!r}"
    assert not (kok / "state" / "oneri_brifingi_damga.json").exists(), (
        "kuru koşum damga bastı — 'ne gönderilecekti' diye bakan tek bir koşum, o günün yığınını "
        "kalıcı olarak görünmez yapardı")


# ── R1 düzeltme turu (inceleme: task-2-review.md) — Ö1 · Ö2 · Ö3 · Kü1-Kü7 ──────────────────

@pytest.mark.skipif(hasattr(os, "geteuid") and os.geteuid() == 0,
                    reason="root izinleri yok sayar — okunamayan dosya kurgulanamaz")
def test_e16_YENI_YOKKEN_OKUNAMAYAN_DEFTER_YINE_BEYAN_EDILIR(sandbox_state):
    """R1/Ö1 (ikinci yarı) — HİÇ ÇİVİLENMEMİŞ DAL: `yeni == 0` + okunamayan defter.

    Eski uygulamada mesaj YALNIZ ⚠ satırından doğuyordu; yani tek bir izin hatası günlük kadansı
    süresiz "her gün mesaj"a çeviriyor VE `@sef`in `bos` hesabını bozuyordu (`mesaj` doluydu ama
    ölçüm zinciri kırıktı). Şimdi bu dal `hata` ile döner: `@sef` onu `olculemeyen`e koyar —
    `bos` hesabı DOĞRU sebeple bozulur (ölçülemeyen kaynak) ve kaynak DAMGALANMAZ."""
    mod = _brifing()
    from meridian import store
    ts = _gun_once(3)
    store.write_jsonl("improvement_proposals.jsonl", [_oneri_satiri("N00090", ts)])
    store.write_json(mod.DAMGA_DOSYA, {mod.DAMGA: {"ts": ts, "son_ts": ts}})   # her şey bildirilmiş
    yol = _defter_yaz(sandbox_state, [_karar("N00090")])
    yol.chmod(0o000)
    try:
        o = mod.ozet_kur()
    finally:
        yol.chmod(0o600)

    assert o["hata"], f"yeni yokken arıza SESSİZLİĞE dönüştü: {o!r}"
    assert "akıbet ölçülemedi — ham sayım: 0" in o["hata"], o["hata"]
    assert not o["mesaj"], f"düşebilir kanal yine dolduruldu: {o['mesaj']!r}"
    assert o["acik_sayi"] is None and o["yeni"] == 0, o


@pytest.mark.skipif(hasattr(os, "geteuid") and os.geteuid() == 0,
                    reason="root izinleri yok sayar — okunamayan dosya kurgulanamaz")
def test_e17_OLCULEMEDI_BEYANI_SEFIN_DUSMEYEN_KANALINDAN_GIDER(monkeypatch, sandbox_state):
    """R1/Ö1 ASIL ÇİVİSİ — beyan `@sef`in ZORUNLU (düşmeyen) parçasına girer.

    `@sef`in iki kanalı EŞİT DEĞİL: `teslim_edilecek` zarf taşmasında düşebilir ve LLM dalında
    metni MODEL yazar (SOUL kalem tavanı 3) — yani "akıbet ölçülemedi" satırı özetlenip yok
    olabilirdi ve operatör katmanın ÖLÜ olduğunu HİÇ öğrenmezdi. `olculemeyen` kanalı ise
    `_ham_parcalari`da zorunlu parçadır, kapsam satırında ÖLÇÜLEMEDİ olarak görünür ve prompt'ta
    modele "bunları SUSTURAMAZSIN" denir.

    Dördü de burada ölçülür — ve BEŞİNCİSİ: ölçülemeyen kaynak DAMGALANMAZ (yani öneri listesi
    kaybolmaz, ertesi turda yeniden bildirilir). Sağlam kaynağın (alarm) yine teslim edilmesi de
    ayrıca çivilenir: bir arızayı iki arızaya çevirmek yok."""
    import importlib
    sef = importlib.import_module("ops.sef_brifingi")
    from meridian import store
    store.write_jsonl("improvement_proposals.jsonl", [_oneri_satiri("N00091", _gun_once(2))])
    yol = _defter_yaz(sandbox_state, [_karar("N00091")])
    monkeypatch.setattr(sef, "_alarm_ozeti",
                        lambda: {"toplam": 5, "yeni": 5, "mesaj": "🔔 5 alarm birikti"})
    monkeypatch.setattr(sef, "_self_review", lambda: {})
    monkeypatch.setattr(sef, "_son_brifing", lambda: "")
    yol.chmod(0o000)
    try:
        ham = sef.topla()
        kapsam = sef._kapsam_satiri(ham)
        zorunlu, kaynaklar = sef._ham_parcalari(ham)
        prompt = sef._prompt_kur(ham)
    finally:
        yol.chmod(0o600)

    assert [k["kaynak"] for k in ham["olculemeyen"]] == ["oneri"], (
        f"beyan ÖLÇÜLEMEYEN kanalına girmedi: {ham!r}")
    assert "akıbet ölçülemedi — ham sayım: 1" in ham["olculemeyen"][0]["neden"], ham["olculemeyen"]
    assert [k["kaynak"] for k in ham["teslim_edilecek"]] == ["alarm"], (
        f"sağlam kaynak düştü ya da öneri damgalanabilir sayıldı: {ham['teslim_edilecek']!r}")
    assert any("akıbet ölçülemedi" in p for p in zorunlu), (
        f"beyan ZORUNLU parçada değil — zarf taşmasında düşebilir: {zorunlu!r}")
    assert "ÖLÇÜLEMEDİ" in kapsam, f"kapsam satırı arızayı taşımıyor: {kapsam!r}"
    assert "SUSTURAMAZSIN" in prompt and "akıbet ölçülemedi" in prompt, (
        "prompt modele beyanı susturamayacağını söylemiyor")


def test_e18_KARARDA_KIMLIK_YOKSA_KIMLIKSIZ_ONERI_SESSIZCE_DUSMEZ(sandbox_state):
    """R1/Ö2 — `None` kimlik `kapali` kümesine SIZAMAZ.

    `akibet_turet` bir karar satırını yalnız alanın VARLIĞINA bakarak kabul eder, DEĞERİNİ
    denetlemez: elle düzenlenmiş bir defterdeki `oneri_id: null` bir karar `kararlar`a girer.
    Küme `{None}` olursa, kimliği OLMAYAN her öneri satırı (`r.get("id")` → `None`) `yeni`den
    SESSİZCE düşerdi — hiçbir blokta görünmez, hiçbir uyarı basılmaz: kalıcı görünmezlik, tam da
    bu dosyanın "ts'siz satır sessizce düşürülmez" diye yasakladığı sınıf."""
    mod = _brifing()
    from meridian import store
    store.write_jsonl("improvement_proposals.jsonl", [
        {"ts": _gun_once(2), "alan": "kimliksiz.satir", "oneri": "id alanı olmadan üretilmiş"},
        _oneri_satiri("N00092", _gun_once(1)),
    ])
    _defter_yaz(sandbox_state, [
        {"ts": _gun_once(0), "olay": "karar", "oneri_id": None, "karar": "uygulandi",
         "gerekce": "elle düzenlenmiş defterde kimliği boş bırakılmış karar", "karar_veren": "rol1"},
    ])

    o = mod.ozet_kur()
    assert o["yeni"] == 2, (
        f"kimliksiz öneri satırı SESSİZCE düştü: {o!r} — bir bozuk karar satırı, kimliksiz TÜM "
        "önerileri görünmez yapardı")
    assert "kimliksiz.satir" in o["mesaj"], o["mesaj"]
    # R2/Y4: görünürlüğü kazanıp okunabilirliği kaybetmek yarım düzeltmedir. Python literali
    # (`None`) operatör metnine SIZMAZ — eksiklik ev diliyle söylenir (`e11b` aynı kelimeyi
    # ölçülemedi cümlesinde de yasaklıyor: tek disiplin, iki yüzey).
    assert "None" not in o["mesaj"], (
        f"kimliksiz satır operatöre Python literaliyle basıldı: {o['mesaj']!r}")
    assert "kimliği yazılmamış" in o["mesaj"], (
        f"eksik kimlik ev diliyle söylenmedi: {o['mesaj']!r}")


def test_e19_TS_SI_COZULEMEYEN_KARAR_KOSULSUZ_BILDIRILIR(sandbox_state):
    """R1/Ö3a — belgelenmiş dal, artık çivili.

    `_karar_bildirilecek_mi`nin ilk iki satırı silinirse, ts'si çözülemeyen bir karar
    `(False, datetime.min)` anahtarıyla damgayı ASLA geçemez ve HİÇBİR turda bildirilmez —
    docstring'in "kalıcı sessiz kayıp" dediği şeyin ta kendisi. Cümlede tarihin ölçülemediği de
    işaretlenmelidir (uydurma yasağı: bilinmeyen an 'bugün' sayılmaz)."""
    mod = _brifing()
    from meridian import store
    ts = _gun_once(1)
    store.write_jsonl("improvement_proposals.jsonl", [_oneri_satiri("N00093", ts)])
    store.write_json(mod.DAMGA_DOSYA, {mod.DAMGA: {"ts": ts, "son_ts": _gun_once(0)}})
    _defter_yaz(sandbox_state, [
        {"ts": "geçen hafta", "olay": "karar", "oneri_id": "N00094", "karar": "uygulandi",
         "gerekce": "damgası çözülemeyen ama gerçek olan bir karar satırı", "karar_veren": "rol1"},
    ])

    o = mod.ozet_kur()
    karar_blok = _bloklar(o["mesaj"])["✅"]
    assert "N00094" in karar_blok, (
        f"ts'si çözülemeyen karar hiçbir turda bildirilmiyor — kalıcı sessiz kayıp: {o!r}")
    assert "tarihi ölçülemedi" in karar_blok, (
        f"bilinmeyen an sessizce 'ölçülmüş' gibi sunuldu: {karar_blok!r}")


def test_e20_KAPALI_KUMESI_TUM_TARIHCEDEN_TURER(sandbox_state):
    """R1/Ö3b — `kapali`, SÜZÜLMÜŞ (damga sonrası) kararlardan değil TÜM tarihçeden türer.

    Kurgu şerhin gerekçesini birebir ölçer: ts ALANI OLMAYAN bir öneri (koşulsuz `yeni`ye girer,
    `acik`e HİÇ giremez çünkü yaşı hesaplanamaz) + damgadan ÇOK ÖNCE yazılmış bir karar. `kapali`
    süzülmüş listeden kurulsaydı bu öneri her turda "yeni" diye geri dönerdi — karara bağlanmış
    olduğu hâlde."""
    mod = _brifing()
    from meridian import store
    store.write_jsonl("improvement_proposals.jsonl", [
        {"id": "N00095", "alan": "ts_siz.satir", "oneri": "ts alanı olmayan öneri"},
    ])
    store.write_json(mod.DAMGA_DOSYA, {mod.DAMGA: {"ts": _gun_once(1), "son_ts": _gun_once(1)}})
    _defter_yaz(sandbox_state, [
        _karar("N00095", ts=_gun_once(40), gerekce="damgadan çok önce verilmiş gerçek karar"),
    ])

    o = mod.ozet_kur()
    assert o["yeni"] == 0, (
        f"eski karar taşıyan öneri 'yeni' diye geri döndü: {o!r} — `kapali` tarihçenin TAMAMINDAN "
        "türemeli, yalnız damga sonrasından değil")
    assert not o["mesaj"], f"bildirilecek bir şey yokken mesaj üretildi: {o['mesaj']!r}"


def test_e21_TAVAN_TASMASI_ILAN_EDILIR_VE_KARARDA_EN_YENILER_GOSTERILIR(sandbox_state):
    """R1/Kü2 + Kü5 — taşma dalları (canlıda 16 öneri var: `📌` taşması İLK koşumda işler).

    KARAR BLOĞUNDA TAŞMA EN ESKİLERİ DEĞİL EN YENİLERİ gösterir: liste artan gerçek zamanla
    sıralıdır, baştan kesmek "son teslimden beri" başlıklı bloğu en eski sekiz kalemle
    doldururdu. Düşen kalemler her iki blokta da SAYIYLA beyan edilir."""
    mod = _brifing()
    from meridian import store
    store.write_jsonl("improvement_proposals.jsonl",
                      [_oneri_satiri(f"N001{i:02d}", _gun_once(30 - i)) for i in range(9)])
    _defter_yaz(sandbox_state, [
        _karar(f"N002{i:02d}", ts=_gun_once(20 - i),
               gerekce=f"kapanış kaydı numara {i}, yeterince uzun bir gerekçe") for i in range(9)
    ])

    bloklar = _bloklar(mod.ozet_kur()["mesaj"])
    assert "… +1 daha" in bloklar["📌"], f"açık listesi taşması beyan edilmedi: {bloklar['📌']!r}"
    karar_blok = bloklar["✅"]
    assert "+1 karar daha gösterilmiyor" in karar_blok, (
        f"karar taşması beyan edilmedi: {karar_blok!r}")
    # R2/Y1: düşenlere "eski" DENMEZ — tarihi ölçülemeyen bir karar için bu ÖLÇÜLMEMİŞ bir
    # iddiadır (uydurma yasağının kenarı). Söylenen şey seçim ÖNCELİĞİDİR.
    assert "eski karar" not in karar_blok, (
        f"gösterilmeyen kararlar ölçülmemiş bir sıfatla ('eski') adlandırıldı: {karar_blok!r}")
    assert "N00208" in karar_blok, f"EN YENİ karar kesilip atıldı: {karar_blok!r}"
    assert "N00200" not in karar_blok, (
        f"taşmada EN ESKİ karar gösterildi — 'son teslimden beri' bloğu eskilerle doldu: "
        f"{karar_blok!r}")


def test_e22_KARAR_CUMLESI_ONERININ_KONUSUNU_TASIR(sandbox_state):
    """R1/Kü3 — "kaybolmaz, YER DEĞİŞTİRİR" iddiasının kenarı.

    İki brifing arasında DOĞUP karara bağlanan bir öneri `yeni` bloğuna hiç girmez; karar cümlesi
    konusunu taşımazsa operatöre yalnız bir KİMLİK ulaşır ve neyin kapandığı hiçbir yerde
    yazmaz. Konu metni İKİ doğum kaynağından da okunur (öneri defteri + akıbet defterinin doğum
    satırları)."""
    mod = _brifing()
    from meridian import store
    store.write_jsonl("improvement_proposals.jsonl", [
        _oneri_satiri("N00096", _gun_once(2), oneri="watchdog sayacını dışa aç"),
        _oneri_satiri("N00097", _gun_once(1)),
    ])
    _defter_yaz(sandbox_state, [
        {"ts": _gun_once(3), "olay": "oneri", "oneri_id": "AKB-0003", "kaynak": "operator",
         "oneri": "kapanış zilinde ikinci bir kontrol"},
        _karar("N00096", gerekce="ölçüldü ve tek turda uygulandı, kapanış commit'i"),
        _karar("AKB-0003", "reddedildi", gerekce="ölçüm penceresi bu çeyrekte açılmıyor"),
    ])

    karar_blok = _bloklar(mod.ozet_kur()["mesaj"])["✅"]
    assert "watchdog sayacını dışa aç" in karar_blok, (
        f"öneri defterinden doğan kalemin konusu taşınmadı: {karar_blok!r}")
    assert "kapanış zilinde ikinci bir kontrol" in karar_blok, (
        f"akıbet defterinden doğan kalemin konusu taşınmadı: {karar_blok!r}")


def test_e23_ERTELENEN_ONERI_HICBIR_YUZEYDEN_KAYBOLMAZ(sandbox_state):
    """R1/Kü4 — "sonra bakarız" denen öneri açık SAYILMAZ ve `yeni`de de yoktur; karar bloğunda
    ise yalnız damga ilerleyene kadar görünür. Başka hiçbir yüzeyi olmasaydı sistemin TAMAMINDAN
    kaybolurdu — tam da bu kadansın var oluş sebebi olan "unutulan öneri" sınıfı. Sayı
    `akibet_turet`in KENDİ sayacından okunur (yeniden hesaplanmaz).

    KURGU BİLEREK EN ZOR HÂLDİR: erteleme kararı damgadan ÇOK ÖNCE yazılmıştır, yani karar bloğu
    onu ARTIK göstermez. Yaş satırındaki kuyruk, o önerinin sistemdeki TEK yüzeyidir."""
    mod = _brifing()
    from meridian import store
    store.write_jsonl("improvement_proposals.jsonl", [
        _oneri_satiri("N00098", _gun_once(40)), _oneri_satiri("N00099", _gun_once(1)),
    ])
    store.write_json(mod.DAMGA_DOSYA, {mod.DAMGA: {"ts": _gun_once(5), "son_ts": _gun_once(5)}})
    _defter_yaz(sandbox_state, [
        _karar("N00098", "ertelendi", ts=_gun_once(30),
               gerekce="ölçüm kartı açılana kadar bekliyor, sonra bakılacak"),
    ])

    o = mod.ozet_kur()
    bloklar = _bloklar(o["mesaj"])
    assert "✅" not in bloklar, (
        f"kurgu hatası: erteleme kararı hâlâ karar bloğunda — testin ölçtüğü kenar bu değil: {o}")
    assert "1 ertelenmiş" in bloklar["📌"], (
        f"ertelenen öneri açık listesinden düştü ve HİÇBİR yüzeyde görünmüyor: {bloklar['📌']!r}")
    assert "N00098" not in bloklar.get("🧠", ""), bloklar
    assert o["acik_sayi"] == 1, o


def test_e24_OPS_ADLARI_STDLIB_MODULLERINI_GOLGELEMEZ():
    """R1/Kü6 — `from ops import akibet`, `ops/akibet.py`nin kendi bootstrap'ını (`sys.path`in
    BAŞINA `ops/` eklenir) CANLI brifing sürecine taşıdı. Bugün zararsız; ama `ops/`e stdlib
    adıyla bir dosya eklendiği gün (`types.py`, `json.py`, `queue.py`…) canlı `@sef` süreci onu
    gölgeler ve arıza, ithal zincirinin çok uzağında görünür. Ucuz kapı, kalıcı koruma."""
    adlar = {p.stem for p in (KOK / "ops").glob("*.py")}
    cakisan = sorted(adlar & set(sys.stdlib_module_names))
    assert not cakisan, (
        f"`ops/` altında stdlib adını gölgeleyen dosya(lar): {cakisan} — `ops/akibet.py` "
        "`sys.path`in BAŞINA `ops/`i ekliyor ve bu bootstrap artık canlı brifing sürecinde de "
        "koşuyor; bu dosyalar stdlib yerine ithal edilir")


@pytest.mark.skipif(hasattr(os, "geteuid") and os.geteuid() == 0,
                    reason="root izinleri yok sayar — okunamayan dosya kurgulanamaz")
def test_e25_OLCULEMEDIGINDE_BETIK_DE_GONDERMEZ_DAMGALAMAZ_VE_SIFIR_DONMEZ(monkeypatch,
                                                                           sandbox_state):
    """R1/Ö1'in İKİNCİ YÜZEYİ: betiğin KENDİ `main()`i `@sef` ile AYNI hükmü verir.

    Aynı durumda iki yüzeyin farklı davranması (biri susup öteki göndermesi) tek gerçeğin iki
    kopyası olurdu. Ölçüm zinciri kırıkken: gönderim YOK, damga YOK, çıkış kodu SIFIR DEĞİL —
    teslim edilemeyen bir kadans "başarılı" görünemez."""
    mod = _brifing()
    from meridian import store
    store.write_jsonl("improvement_proposals.jsonl", [_oneri_satiri("N00044", _gun_once(2))])
    yol = _defter_yaz(sandbox_state, [_karar("N00045")])
    gonderilen: list = []
    monkeypatch.setattr(mod.notify, "configured", lambda: True)
    monkeypatch.setattr(mod.notify, "send", lambda t: gonderilen.append(t) or True)
    yol.chmod(0o000)
    try:
        rc = mod.main(["--uygula"])
    finally:
        yol.chmod(0o600)

    assert rc != 0, "ölçüm zinciri kırıkken betik 0 döndü — arıza 'başarılı koşum' gibi görünür"
    assert not gonderilen, f"ölçülemeyen turda mesaj gönderildi: {gonderilen!r}"
    assert not (pathlib.Path(sandbox_state) / mod.DAMGA_DOSYA).exists(), (
        "ölçülemeyen tur damgalandı — öneri listesi bir daha hiç bildirilmezdi")


# ── R2 turu (yeniden-inceleme: task-2-rereview.md) — Y1 · Y2 · Y4 · Y5 ───────────────────────

def test_e26_TARIHI_OLCULEMEYEN_KARAR_TASMADA_DA_KESILMEZ(sandbox_state):
    """R2/Y1 — Kü2'nin taşma kesimi ile Ö3a'nın koşulsuz bildirim garantisi ÇELİŞİYORDU.

    `kararlar` artan gerçek zamanla sıralıdır ve tarihi çözülemeyenler EN BAŞTADIR. R1'in
    `[-8:]` kesimi, 8'den fazla karar olan HER turda o kalemleri kesilen tarafta bırakıyordu —
    yani Ö3a'nın "hiçbir turda görünmesin diye koşulsuz bildiriyoruz" garantisi taşmada sessizce
    kayboluyordu. Öncelik sırası iki kuralı birlikte tutar: önce tarihi ölçülemeyenler, kalan
    slotlar en yenilere.

    Kurgu: 9 geçerli + 1 tarihi çözülemeyen karar (tavan 8)."""
    mod = _brifing()
    from meridian import store
    store.write_jsonl("improvement_proposals.jsonl", [_oneri_satiri("N00300", _gun_once(1))])
    _defter_yaz(sandbox_state, [
        {"ts": "kim bilir ne zaman", "olay": "karar", "oneri_id": "N00399",
         "karar": "uygulandi", "gerekce": "tarihi çözülemeyen ama gerçek bir karar satırı",
         "karar_veren": "rol1"},
    ] + [
        _karar(f"N003{i:02d}", ts=_gun_once(20 - i),
               gerekce=f"kapanış kaydı numara {i}, yeterince uzun bir gerekçe") for i in range(9)
    ])

    karar_blok = _bloklar(mod.ozet_kur()["mesaj"])["✅"]
    assert "N00399" in karar_blok, (
        f"tarihi ölçülemeyen karar taşmada kesildi — Ö3a'nın garantisi taşma turlarında "
        f"KAYBOLUYOR: {karar_blok!r}")
    assert "tarihi ölçülemedi" in karar_blok, karar_blok
    assert "N00308" in karar_blok, f"en yeni karar da girmeliydi: {karar_blok!r}"
    # 10 karar, tavan 8 → 1 tarihi ölçülemeyen + 7 en yeni gösterilir, 2 en eski düşer.
    assert "+2 karar daha gösterilmiyor" in karar_blok, (
        f"gösterilmeyen sayısı yanlış/eksik beyan edildi: {karar_blok!r}")
    assert "N00300" not in karar_blok and "N00301" not in karar_blok, (
        f"tavan aşıldı — en eski kararlar da basıldı: {karar_blok!r}")


def test_e27_YIGIN_BOSALDIGINDA_ACIK_ONERI_YOK_DALI_GERCEKTEN_KOSAR(sandbox_state):
    """R2/Y5 — `_yas_satiri`nin "açık öneri yok" dalı ÖLÜ DEĞİLDİR.

    Kapı koşullu olduğu sürece (`if acik or ertelenen`) bu dal yalnız ertelenen kuyruğuyla
    birlikte doğabilirdi; kuyruksuz hâli hiçbir girdiyle erişilemezdi. Artık yaş satırı mesaj
    üretilen HER turda basılır — ve bu yalnız ölü kod temizliği değil: yığının BOŞALDIĞI gün
    (her şey karara bağlandı) operatör bunu görür, ki bu kadansın anlatabileceği en iyi haberdir.

    Kurgu: tek öneri, karara bağlanmış → `yeni` boş, karar bloğu dolu, açık YOK."""
    mod = _brifing()
    from meridian import store
    store.write_jsonl("improvement_proposals.jsonl", [_oneri_satiri("N00400", _gun_once(3))])
    _defter_yaz(sandbox_state, [
        _karar("N00400", gerekce="ölçüldü, uygulandı ve kapanış commit'i atıldı"),
    ])

    o = mod.ozet_kur()
    bloklar = _bloklar(o["mesaj"])
    assert "🧠" not in bloklar, f"karara bağlanan öneri 'yeni' bloğunda: {o['mesaj']!r}"
    assert bloklar["📌"] == "📌 açık öneri yok", (
        f"yığın boşaldığında bu SÖYLENMİYOR (ölü dal): {bloklar.get('📌')!r}")
    assert o["acik_sayi"] == 0, o
