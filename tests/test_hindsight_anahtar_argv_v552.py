"""tests/test_hindsight_anahtar_argv_v552.py — TSK-064 (argv dilimi): Hindsight kiracı anahtarı süreç argv'sinde DURMAZ.

NUMARA: `ls tests | grep _v552` boş (2026-09-25 18:13Z; ana checkout + dört worktree tarandı —
v551 `tsk224-edg104`, v553 `tsk225-edg085-yazim` ağacında; v552 yalnız bu dosya).

SORUN (ROADMAP TSK-064 notu 2026-09-25 09:11Z): `deploy/hindsight/sayfa_oku.sh` ve
`deploy/hindsight/hafiza_sor.sh` anahtarı `KEY=$(cat …)` ile okuyup gömülü Python'a KONUMSAL
ARGÜMAN veriyordu. Anahtar böylece Python sürecinin argv'sinde durur — recall boyunca (~38 sn) aynı
makinedeki her kullanıcı `ps` / `/proc/<pid>/cmdline` ile görebilirdi.
KARAR (Rol-1, 2026-09-25): bash anahtarı OKUMAZ; gömülü Python `HAFIZA_ANAHTAR_DOSYASI` (varsayılan
`/opt/hindsight/.key`) yolundaki dosyayı KENDİSİ okur. Anahtar ortama da konmaz: `/proc/<pid>/environ`
aynı kullanıcıya açıktır.

NE ÖLÇÜLÜR:
  E1 DİNAMİK argv — sahte sunucu istek ANINDA (istemci yanıt beklerken) `ps -A -ww -o pid,ppid,args`
     alır: anahtar bu pytest sürecinin hiçbir TORUNUNUN (betiğin bash'i, gömülü Python, varsa başka alt
     süreç) argv'sinde yok. POZİTİF KONTROL aynı görüntüde: istemcinin BASE argümanı (`127.0.0.1:<port>`)
     VAR — yani ps istemci sürecini gerçekten gördü ("görmedi" ≠ "yok"). Torunlarla sınırlama
     bilinçlidir: başka worktree'de ESKİ betikle koşan v547 aynı sahte anahtarı argv'ye koyar.
  E2 DİNAMİK ortam — aynı an, torunların ortamları (macOS `ps -E`, Linux `/proc/<pid>/environ`).
     Pozitif kontrol `HAFIZA_BETIK=` — bu değişken YALNIZ Python istemcisinin ortamına konur.
  E3 STATİK — bash tarafı anahtarın İÇERİĞİNİ okumaz ve yolunu bile ellemez; `python3 -` satırında
     anahtar yok; anahtar okuma bloğu iki betikte bayt-aynı (tek-kaynak yasası: iki kopya kaçınılmaz,
     çünkü okuma kayıt modülüne BAĞLANAMAZ — modül bulunamasa da okuma çıkmalı, v547 C10).
  E4 anahtar dosyası yok / okunamaz (0000) → çıkış 1, stdout boş, İSTEK YOK, okuma kaydı YOK; stderr
     yolu adlandırır, traceback basmaz (v547 A7'nin iki betik × iki kip ikizi).
  E5 sondaki CR/LF'ler kırpılır, BAŞKA hiçbir şey kırpılmaz — ölçüt sunucunun gördüğü Authorization
     başlığıdır. (Tur 1 eski `$(cat …)` gibi yalnız LF kırpıyordu; Tur 2'de CR de — Rol-1 kararı.)
  TUR 2 (Rol-1 kararı 2026-09-25: anahtarın bir çıktı kanalına düşmesi AYNI sınıf):
  E7 anahtarı taşıyan istisna zorlanır (ortadaki CR → başlık ValueError'ı, mesajda anahtarın bayt-repr'i)
     → stdout, stderr ve okuma kaydında anahtar YOK, `<anahtar>` işareti VAR, traceback yok.
  E8 yakalanmamış istisna → tek satır `Tür: arındırılmış mesaj`, çıkış 1 (eskisi gibi), stdout boş.
  E9 STATİK — gömülü Python'da istisna metni yalnız `arindir(...)` üzerinden basılır.

v547'nin A/B/C davranış çivileri (stdout baytları, çıkış kodları, okuma kaydı, C8 sızıntı taraması)
değişmeden geçmek ZORUNDADIR. Bu dosya onların fikstür ve yardımcılarını İTHAL eder (kopya değil);
v547'ye eklenen tek şey sahte sunucudaki `istek_kancasi` alanıdır.
"""
from __future__ import annotations

import os
import pathlib
import re
import subprocess
import sys

import pytest

from tests.test_hafiza_okuma_kaydi_v547 import (  # noqa: F401 — `sunucu` fikstürü ithalle kaydolur
    HAFIZA_SOR,
    SAHTE_ANAHTAR,
    SAYFA_OKU,
    SORU,
    _kos,
    _ortam,
    sunucu,
)

VARSAYILAN_ANAHTAR_YOLU = "/opt/hindsight/.key"
ANAHTAR_BLOK_BASI = "# >>> anahtar"
ANAHTAR_BLOK_SONU = "# <<< anahtar"

CAGRILAR = [
    pytest.param(SAYFA_OKU, (), id="sayfa_oku-liste"),
    pytest.param(SAYFA_OKU, ("meridian-hedef-sapma",), id="sayfa_oku-sayfa"),
    pytest.param(HAFIZA_SOR, (SORU,), id="hafiza_sor"),
]
BETIKLER = [
    pytest.param(SAYFA_OKU, (), id="sayfa_oku"),
    pytest.param(HAFIZA_SOR, (SORU,), id="hafiza_sor"),
]
#: yetki reddinde (401) betiğin çıkış kodu — v547 A6/B4'ün pinlediği sözleşme
RET_KODU = {SAYFA_OKU: 1, HAFIZA_SOR: 2}


def _ps(*secenek: str) -> tuple[int, str, str]:
    r = subprocess.run(["ps", *secenek], capture_output=True, text=True, timeout=30)
    return r.returncode, r.stdout, r.stderr


def _surec_tablosu(*ek: str) -> tuple[int, dict[str, tuple[str, str]], str]:
    """`ps -A [ek] -ww -o pid=,ppid=,args=` → (kod, {pid: (ppid, args)}, stderr)."""
    kod, cikti, hata = _ps("-A", *ek, "-ww", "-o", "pid=,ppid=,args=")
    tablo = {}
    for satir in cikti.splitlines():
        parca = satir.split(None, 2)
        if len(parca) >= 2:
            tablo[parca[0]] = (parca[1], parca[2] if len(parca) > 2 else "")
    return kod, tablo, hata


def _torunlar(tablo: dict[str, tuple[str, str]]) -> list[str]:
    """Bu pytest sürecinin (kanca sunucu ipliğinde, aynı süreçte koşar) TÜM torunları: betiğin bash'i,
    gömülü Python istemcisi ve varsa başka her alt süreç. KAPSAM BİLİNÇLİ DAR: aynı makinede başka
    worktree'lerde v547 koşabilir ve ESKİ betik aynı sahte anahtarı KENDİ argv'sine koyar — tüm süreç
    tablosuna bakmak yabancı koşumdan sahte kırmızı üretirdi (bu turda eşzamanlı üç worktree ölçüldü)."""
    cocuklar: dict[str, list[str]] = {}
    for pid, (ppid, _) in tablo.items():
        cocuklar.setdefault(ppid, []).append(pid)
    sira = [str(os.getpid())]
    for pid in sira:  # liste gezilirken büyür: genişlik-önce gezinti, bekleme döngüsü değil
        sira.extend(c for c in cocuklar.get(pid, []) if c not in sira)
    return sira[1:]


def _torun_argvleri() -> tuple[int, list[str], str]:
    kod, tablo, hata = _surec_tablosu()
    return kod, [tablo[p][1] for p in _torunlar(tablo)], hata


def _torun_ortamlari() -> tuple[int, list[str], str]:
    """Torun süreçlerin ortamları — argv HARİÇ (argv E1'in işi; E2 argv'yi de sayarsa eski kodda
    'ortamda' diye yanlış kırmızı verirdi — ölçüldü 2026-09-25). Linux: `/proc/<pid>/environ`.
    macOS: `ps -E` satırı 'argv + ortam'dır; aynı pid'in ortamsız satırı önekten düşülür."""
    if sys.platform == "darwin":
        k1, argvli, h1 = _surec_tablosu()
        k2, ortamli, h2 = _surec_tablosu("-E")
        parcalar = []
        for pid in _torunlar(ortamli):
            kalan = ortamli[pid][1]
            argv = argvli.get(pid, ("", None))[1]
            # pid iki görüntüde eşleşmezse (arada doğmuş süreç) satırın TAMAMI sayılır: bu yön
            # yalnız fazladan kırmızı üretebilir, sızıntıyı gizleyemez.
            parcalar.append(kalan[len(argv):] if argv is not None and kalan.startswith(argv) else kalan)
        return (k1 or k2), parcalar, h1 + h2
    kod, tablo, hata = _surec_tablosu()
    parcalar = []
    for pid in _torunlar(tablo):
        try:
            ham = pathlib.Path(f"/proc/{pid}/environ").read_bytes()
        except OSError:  # sessiz-yutma: ölçüm anında çıkmış torun (ör. ps'in kendisi) okunamaz; istemcinin görüldüğü pozitif kontrolle AYRICA ölçülür
            continue
        parcalar.append(ham.replace(b"\0", b"\n").decode("utf-8", "replace"))
    return kod, parcalar, hata


def _bolumler(betik: pathlib.Path) -> tuple[list[str], str, str]:
    """(bash kod satırları [tam-satır yorumlar hariç], `python3 -` çağrı satırı, gömülü Python)."""
    satirlar = betik.read_text(encoding="utf-8").splitlines()
    cagri = [i for i, s in enumerate(satirlar) if re.search(r"\bpython3\s+-\s", s)]
    assert len(cagri) == 1, (betik.name, cagri)
    i = cagri[0]
    assert satirlar[i].rstrip().endswith("<<'PY'"), satirlar[i]
    son = satirlar.index("PY", i + 1)
    bash = [s for s in satirlar[: i + 1] if not s.lstrip().startswith("#")]
    return bash, satirlar[i], "\n".join(satirlar[i + 1: son])


# ================================================================================================
# E1/E2 — DİNAMİK: istek anında süreç tablosu
# ================================================================================================

@pytest.mark.parametrize("betik,argv", CAGRILAR)
def test_E1_anahtar_hicbir_surecin_argvsinde_yok(sunucu, tmp_path, betik, argv):
    goruntuler: list[tuple[int, list[str], str]] = []
    sunucu["istek_kancasi"] = lambda: goruntuler.append(_torun_argvleri())
    r = _kos(betik, *argv, ortam=_ortam(tmp_path, sunucu["port"]))
    assert r.returncode == 0, r.stderr
    assert goruntuler, "sunucuya istek gelmedi — süreç tablosu ölçülemedi"
    for kod, argvler, hata in goruntuler:
        # Mesajlar süreç tablosunu basmaz (`assert x in metin` pytest'te tüm metni döker); yalnız
        # anahtarı içeren argv(ler) basılır.
        assert kod == 0, hata[-300:]
        gordu = any(f"127.0.0.1:{sunucu['port']}" in a for a in argvler)
        assert gordu, "POZİTİF KONTROL düştü: ps istemcinin argv'sini görmedi — 'anahtar yok' hükmü verilemez"
        sizan = [a[:300] for a in argvler if SAHTE_ANAHTAR in a]
        assert not sizan, f"anahtar süreç argv'sinde: {sizan}"


@pytest.mark.parametrize("betik,argv", CAGRILAR)
def test_E2_anahtar_hicbir_surecin_ortaminda_yok(sunucu, tmp_path, betik, argv):
    if sys.platform != "darwin" and not pathlib.Path("/proc/self/environ").exists():
        pytest.skip("süreç ortamını okuma yolu yok (ne macOS `ps -E` ne `/proc`) — ölçülemez")
    goruntuler: list[tuple[int, list[str], str]] = []
    sunucu["istek_kancasi"] = lambda: goruntuler.append(_torun_ortamlari())
    r = _kos(betik, *argv, ortam=_ortam(tmp_path, sunucu["port"]))
    assert r.returncode == 0, r.stderr
    assert goruntuler, "sunucuya istek gelmedi — süreç ortamı ölçülemedi"
    for kod, ortamlar, hata in goruntuler:
        # Ortam metni ASLA mesaja girmez: koşturan kabuğun gerçek jetonlarını taşır (ölçüldü
        # 2026-09-25 — ilk sürümün `assert … not in cikti` kırmızısı tüm ortamı pytest çıktısına
        # döktü). Sızıntıda yalnız anahtarı taşıyan DEĞİŞKENİN ADI basılır.
        assert kod == 0, hata[-300:]
        cikti = "\n".join(ortamlar)
        gordu = "HAFIZA_BETIK=" in cikti
        assert gordu, "POZİTİF KONTROL düştü: Python istemcisinin ortamı görülmedi — 'anahtar yok' hükmü verilemez"
        tasiyan = sorted(set(re.findall(r"(\w+)=\S*" + re.escape(SAHTE_ANAHTAR), cikti)))
        sizdi = SAHTE_ANAHTAR in cikti
        assert not sizdi, f"anahtar bir sürecin ORTAMINDA — değişken(ler): {tasiyan or '?'}"


# ================================================================================================
# E3 — STATİK: bash anahtara dokunmaz, Python dosyayı kendisi okur
# ================================================================================================

@pytest.mark.parametrize("betik", [SAYFA_OKU, HAFIZA_SOR], ids=["sayfa_oku", "hafiza_sor"])
def test_E3_bash_anahtari_okumaz_python_cagrisinda_anahtar_yok(betik):
    bash, cagri, _ = _bolumler(betik)
    arguman = cagri.split("python3", 1)[1].split("<<", 1)[0]
    assert not re.search(r"KEY|ANAHTAR", arguman, re.IGNORECASE), \
        f"{betik.name}: `python3 -` argümanlarında anahtar: {arguman!r}"
    kod = "\n".join(bash)
    yasak = {
        "komut ikamesiyle dosya okuma": r"\$\(\s*(cat\b|<)",
        "ters tırnak komut ikamesi": r"`",
        "read/mapfile/readarray": r"\b(read|mapfile|readarray)\b",
        "KEY değişkeni": r"\bKEY\s*=",
        "anahtar yolu ezmesi (yol yalnız Python'da)": r"HAFIZA_ANAHTAR_DOSYASI",
        "anahtar varsayılan yolu (yol yalnız Python'da)": re.escape(VARSAYILAN_ANAHTAR_YOLU),
    }
    bulunan = {ad: re.findall(desen, kod) for ad, desen in yasak.items() if re.search(desen, kod)}
    assert not bulunan, f"{betik.name} bash tarafı anahtara dokunuyor: {bulunan}"


def test_E3b_anahtar_okuma_blogu_iki_betikte_bayt_ayni_ve_yol_sozlesmesi():
    bloklar = []
    for betik in (SAYFA_OKU, HAFIZA_SOR):
        _, _, py = _bolumler(betik)
        assert py.count(ANAHTAR_BLOK_BASI) == 1 and py.count(ANAHTAR_BLOK_SONU) == 1, betik.name
        blok = py[py.index(ANAHTAR_BLOK_BASI): py.index(ANAHTAR_BLOK_SONU)]
        assert (f'os.environ.get("HAFIZA_ANAHTAR_DOSYASI") or "{VARSAYILAN_ANAHTAR_YOLU}"'
                in blok), f"{betik.name}: ezme adı ya da varsayılan yol değişti"
        # anahtar okuması argv ayrıştırmasından ÖNCE: eski sıra (bash `cat`, sonra Python) korunur —
        # anahtar yokken `k` gibi bir argüman hatası öne geçmez.
        assert py.index(ANAHTAR_BLOK_BASI) < py.index("sys.argv"), betik.name
        bloklar.append(blok)
    assert bloklar[0] == bloklar[1], "anahtar okuma bloğu iki betikte AYRIŞTI (tek-kaynak)"


# ================================================================================================
# E4 — anahtar okunamazsa: çıkış 1, istek yok, kayıt yok (v547 A7 ikizi)
# ================================================================================================

@pytest.mark.parametrize("kip", ["yok", "izinsiz"])
@pytest.mark.parametrize("betik,argv", BETIKLER)
def test_E4_anahtar_okunamazsa_cikis_1_istek_ve_kayit_yok(sunucu, tmp_path, betik, argv, kip):
    ortam = _ortam(tmp_path, sunucu["port"])
    yol = tmp_path / f"{kip}.key"
    if kip == "izinsiz":
        if os.geteuid() == 0:
            pytest.skip("root 0000 iznini aşar — 'okunamaz' dalı bu kullanıcıyla ölçülemez")
        yol.write_text(SAHTE_ANAHTAR + "\n", encoding="utf-8")
        yol.chmod(0)
    ortam["HAFIZA_ANAHTAR_DOSYASI"] = str(yol)
    try:
        r = _kos(betik, *argv, ortam=ortam)
    finally:
        if yol.exists():
            yol.chmod(0o600)
    assert r.returncode == 1, (r.stdout, r.stderr)
    assert r.stdout == ""
    assert sunucu["istekler"] == [], "anahtar okunamadığı hâlde istek gitti"
    assert not pathlib.Path(ortam["HAFIZA_OKUMA_KAYDI"]).exists(), "anahtarsız çağrı okuma kaydı yazdı"
    assert str(yol) in r.stderr, f"stderr okunamayan dosyayı adlandırmıyor: {r.stderr!r}"
    assert "Traceback" not in r.stderr, r.stderr
    assert SAHTE_ANAHTAR not in r.stderr


# ================================================================================================
# E5 — Bearer başlığı: sondaki CR/LF'ler düşer, başka hiçbir şey düşmez
# ================================================================================================

@pytest.mark.parametrize("icerik,yetki_ok", [
    pytest.param(SAHTE_ANAHTAR, True, id="satir_sonu_yok"),
    pytest.param(SAHTE_ANAHTAR + "\n", True, id="tek_satir_sonu"),
    pytest.param(SAHTE_ANAHTAR + "\n\n\n", True, id="coklu_satir_sonu"),
    # TUR 2 (Rol-1 kararı): sondaki CR de kırpılır. Eskiden (`$(cat …)` ve Tur 1) CR anahtarda kalır,
    # `Bearer KEY\r` başlığı http.client'ta ValueError'la düşer ve mesaj ANAHTARI taşırdı.
    pytest.param(SAHTE_ANAHTAR + "\r\n", True, id="crlf"),
    pytest.param(SAHTE_ANAHTAR + "\r", True, id="yalniz_cr"),
    pytest.param(SAHTE_ANAHTAR + "\r\n\r\n", True, id="coklu_crlf"),
    # Kırpma YALNIZ sondaki CR/LF'dir: baştaki boşluk anahtarın parçası kalır → sunucu reddeder.
    # `.strip()` gibi geniş bir kırpma bu davranışı sessizce değiştirirdi.
    pytest.param(" " + SAHTE_ANAHTAR + "\n", False, id="bastaki_bosluk_korunur"),
])
@pytest.mark.parametrize("betik,argv", BETIKLER)
def test_E5_bearer_basligi_yalniz_sondaki_crlf_kirpilir(sunucu, tmp_path, betik, argv, icerik, yetki_ok):
    ortam = _ortam(tmp_path, sunucu["port"])
    yol = tmp_path / "e5.key"
    yol.write_bytes(icerik.encode("utf-8"))
    ortam["HAFIZA_ANAHTAR_DOSYASI"] = str(yol)
    r = _kos(betik, *argv, ortam=ortam)
    assert sunucu["istekler"], f"istek gitmedi: {r.stderr[-400:]}"
    beklenen = "Bearer " + icerik.rstrip("\r\n")
    assert [i[2] for i in sunucu["istekler"]] == [beklenen] * len(sunucu["istekler"])
    assert r.returncode == (0 if yetki_ok else RET_KODU[betik]), (r.stdout, r.stderr)


# ================================================================================================
# E7/E8/E9 — TUR 2: anahtar DEĞERİ hiçbir çıktı kanalına basılmaz; ham traceback yok
# ================================================================================================

#: Başlıkta YASAK bir karakter (ORTADAKİ CR — sondaki kırpılır) → http.client
#: `ValueError: Invalid header value b'Bearer …'` fırlatır ve mesaj anahtarı bayt-repr biçiminde
#: (`…7Qx9Zk\\rZ`) TAŞIR. Tur 1'de bu mesaj sayfa_oku'da traceback'le stderr'e, hafiza_sor'da
#: `RECALL HATASI` satırıyla STDOUT'a düşüyordu (ölçüldü 2026-09-25, eski `$(cat)` kodunda da aynı).
GECERSIZ_BASLIKLI = SAHTE_ANAHTAR + "\rZ\n"
#: UZUN anahtar: `RECALL HATASI` mesajı 200 karakterde kesilir. Kesim arındırmadan ÖNCE olsaydı anahtar
#: yarıda kalır, `replace` tam anahtarı bulamaz ve ilk ~170 karakteri basılırdı — sıra bu kipte ölçülür.
GECERSIZ_BASLIKLI_UZUN = SAHTE_ANAHTAR * 8 + "\rZ\n"


@pytest.mark.parametrize("icerik", [pytest.param(GECERSIZ_BASLIKLI, id="kisa"),
                                    pytest.param(GECERSIZ_BASLIKLI_UZUN, id="uzun")])
@pytest.mark.parametrize("betik,argv", BETIKLER)
def test_E7_anahtari_tasiyan_istisna_hicbir_kanala_anahtar_basmaz(sunucu, tmp_path, betik, argv, icerik):
    kayit = tmp_path / "okuma.jsonl"
    ortam = _ortam(tmp_path, sunucu["port"], kayit)
    yol = tmp_path / "e7.key"
    yol.write_bytes(icerik.encode("utf-8"))
    ortam["HAFIZA_ANAHTAR_DOSYASI"] = str(yol)
    r = _kos(betik, *argv, ortam=ortam)
    assert r.returncode == RET_KODU[betik], r.returncode
    assert sunucu["istekler"] == [], "istek başlık doğrulamasında düşmeliydi"
    kanallar = {"stdout": r.stdout, "stderr": r.stderr,
                "okuma_kaydi": kayit.read_text(encoding="utf-8") if kayit.exists() else ""}
    sizan = sorted(ad for ad, metin in kanallar.items() if SAHTE_ANAHTAR in metin)
    assert not sizan, f"anahtar şu kanal(lar)a sızdı: {sizan}"
    # pozitif kontrol: hata GERÇEKTEN basıldı ve anahtarın yeri işaretli (arındırma "hiç basmamak" değil)
    hata_kanali = r.stderr if betik is SAYFA_OKU else r.stdout
    assert "ValueError" in hata_kanali and "<anahtar>" in hata_kanali, (r.stdout, r.stderr)
    assert "Traceback" not in r.stderr


@pytest.mark.parametrize("betik,argv,hazirla,beklenen", [
    pytest.param(SAYFA_OKU, ("meridian-hedef-sapma",), "liste500",
                 "HTTPError: HTTP Error 500: Internal Server Error\n", id="sayfa_oku-http500"),
    pytest.param(HAFIZA_SOR, (SORU, "x"), None,
                 "ValueError: invalid literal for int() with base 10: 'x'\n", id="hafiza_sor-k-sayi-degil"),
])
def test_E8_yakalanmamis_istisna_tek_satir_traceback_yok_cikis_1(sunucu, tmp_path, betik, argv,
                                                                  hazirla, beklenen):
    """Yakalanmamış istisna ham traceback BASMAZ: `Tür: arındırılmış mesaj` tek satırı, çıkış kodu
    eskisi gibi 1, stdout boş. (Eskiden traceback — son satırı aynı bilgiyi taşıyordu.)"""
    if hazirla == "liste500":
        sunucu["kod"]["liste"] = 500
    r = _kos(betik, *argv, ortam=_ortam(tmp_path, sunucu["port"]))
    assert r.returncode == 1, (r.stdout, r.stderr)
    assert r.stdout == ""
    assert r.stderr == beklenen


@pytest.mark.parametrize("betik", [SAYFA_OKU, HAFIZA_SOR], ids=["sayfa_oku", "hafiza_sor"])
def test_E9_istisna_metni_yalniz_arindirilarak_basilir(betik):
    """STATİK tuzak: gömülü Python'da istisna metni (`str(e)`, `{e}`, `{e!r}`, `print(e…`) yalnız
    `arindir(...)` üzerinden basılır; ham traceback'i `sys.excepthook` keser (blokta, E3b bayt-aynı)."""
    _, _, py = _bolumler(betik)
    ham = re.findall(r"(?<!arindir\()\bstr\(e\)|\{e(?:[!:][^}]*)?\}|\bprint\(\s*e\b|\brepr\(e\)", py)
    assert not ham, f"{betik.name}: arındırılmadan basılan istisna metni: {ham}"
    assert "sys.excepthook" in py and "arindir(" in py, betik.name
