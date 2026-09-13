"""v478 — `ops/pano_artefakt_temizle.py` çivileri: pano derlemesinin ÖLÜ artefakt birikimi
(TSK-185, 2026-09-13).

NUMARA SEÇİMİ: `ls tests | grep -c v478` = 0 ile ölçüldü (2026-09-13); en yakın komşu v477
(`test_e2_seyrelme_kovasi_v477.py`). Çakışma yok.

ÖLÇÜLEN ARIZA (TSK-012 UI implementer, 2026-09-13). `ui/vite.config.ts` `emptyOutDir: false`
taşır ve TAŞIMAK ZORUNDA: çıktı klasörü `meridian/web/` ve varsayılan davranış oradaki EL YAZIMI
dosyaların (index.html, app.js, tokens.json, fonts/) tamamını silerdi. Bedeli şu: her derleme
`pano-assets/` altına yeni içerik-hash'li bir js + css bırakır ve ESKİSİNİ SİLMEZ. Ölçüm günü
depoda 5 js + 4 css izliydi; manifest ve `pano.html` bunların YALNIZ birer tanesini işaret
ediyordu — kalan 4 js + 3 css (~8,4 MB) git-izli, dağıtımla canlıya giden ve HİÇBİR okuyucusu
olmayan bayttı. `meridian/api.py::pano_varlik` manifestte olmayan adı zaten 404'ler, yani bu
dosyalar canlıda SUNULAMAZ bile: okunmayan artefakt (YASA 6) + dağıtım yüzeyi şişmesi.

NEDEN ÇİVİ, NEDEN "BİR KEZ SİL" DEĞİL: silme tek seferlik bir olaydır, birikim ise HER derlemede
yeniden doğar. Bu dosyanın A bölümü bu yüzden DEPONUN KENDİSİNİ ölçer (tmp fikstürü değil):
`pano-assets/` altındaki hash'li dosya kümesi, manifest + `pano.html` referans kümesinden
AYRIŞIRSA kırmızı. Ayrışmanın iki yönü de arızadır — fazlalık ölü bayttır, eksiklik ölü sayfadır.

NEYİ ÇİVİLER (sınıf sınıf):
  A. AYRIŞMA (depo gerçeği)  — hash'li artefakt kümesi == referans kümesi; ne fazla ne eksik.
  B. KOMUT SATIRI SÖZLEŞMESİ — varsayılan KURU (1 bayt silinmez) · `--uygula` siler ·
     referanslıya ASLA dokunulmaz · hash'siz dosya (manifest.json, el yazımı) dokunulmaz ·
     `pano.html`in referansı manifest bayat olsa bile KORUR · çıkış 0/1/2 sözleşmesi ·
     çelişen kip çifti kullanım hatası · idempotent.
  C. ZEMİN YOKSA SİLME YOK      — manifest yok/bozuk/boş ya da beyan ettiği dosya diskte yok →
     çıkış 2 ve HİÇBİR silme (fail-closed: güvenilmeyen referans kümesiyle silmek, canlı sayfayı
     öldürmenin en sessiz yoludur).
  D. ZİNCİR                     — `ui/package.json` `build` betiğinin SON adımı temizliktir ve
     verdiği yollar gerçekten çözülür; `vite.config.ts` `emptyOutDir` HÂLÂ `false`.

`meridian.obs`A DOKUNULMAZ: araç saf dosya sistemi + json'dur, hiçbir motor modülü ithal etmez —
bu yüzden çiviler `subprocess` ile GERÇEK komut satırını koşar (ops sözleşmesi `main()` değil
KOMUT SATIRIdır, vaka 2026-08-30). Tek istisna, silme hatasının çıkış kodunu ölçen çivi: oraya
gerçek bir dosya-sistemi arızası üretmek platforma bağlı olurdu, `main([...])` gerçek argv
listesiyle çağrılır ve yalnız `unlink` yamalanır (sapma ADIYLA yazılıdır).
"""

from __future__ import annotations

import json
import pathlib
import subprocess
import sys

import pytest

from ops import pano_artefakt_temizle as arac

REPO = pathlib.Path(__file__).resolve().parents[1]
ARAC_YOLU = REPO / "ops" / "pano_artefakt_temizle.py"
WEB = REPO / "meridian" / "web"
DIZIN = WEB / "pano-assets"
MANIFEST = DIZIN / "manifest.json"
HTML = WEB / "pano.html"
UI = REPO / "ui"


def _kos(*argv: str, cwd: pathlib.Path | None = None) -> subprocess.CompletedProcess:
    """Aracı GERÇEK komut satırıyla koşar. `sys.executable` pytest'in yorumlayıcısıdır
    (`.venv/bin/python`) — sistem python'u seçilseydi "koşamıyorum" ile "kırmızı" karışırdı."""
    return subprocess.run([sys.executable, str(ARAC_YOLU), *argv],
                          capture_output=True, text=True, cwd=str(cwd or REPO))


# =================================================================================================
# A — AYRIŞMA ÇİVİSİ: DEPONUN KENDİSİ
# =================================================================================================

def test_A1_depodaki_hashli_artefakt_kumesi_REFERANS_kumesiyle_AYNI():
    """Tek iddia, iki yön. FAZLALIK: manifest/`pano.html` işaret etmiyorsa o dosya ölü bayttır
    (canlıda 404, depoda MB). EKSİKLİK: referans var ama dosya yoksa pano canlıda ölü açılır.

    ONARIM tek satırdır ve çıktıda yazılıdır: `cd ui && npm run build` (zincirin son adımı
    temizliği koşar) ya da doğrudan aracın `--uygula` kipi."""
    if not MANIFEST.is_file():
        pytest.fail("`pano-assets/manifest.json` YOK — derleme hiç koşmamış; kapı ÖLÇÜLEMEDİ. "
                    "Bu bir 'geçti' değildir: onarım `cd ui && npm run build`.")
    o = arac.olcum(DIZIN, MANIFEST, HTML)
    assert o.olu == [], (
        f"ÖLÜ ARTEFAKT ({len(o.olu)} dosya / {o.bayt} bayt) depoda izli ve dağıtımla canlıya "
        f"gidiyor — hiçbiri manifestte ya da pano.html'de anılmıyor (api.py onları 404'ler):\n  "
        + "\n  ".join(o.olu)
        + "\nOnarım: .venv/bin/python ops/pano_artefakt_temizle.py --uygula")
    assert o.eksik == [], (
        f"REFERANS VAR, DOSYA YOK ({o.eksik}) — pano canlıda ölü açılır (kabuk gelir, uygulama "
        f"hiç gelmez). Onarım: cd ui && npm run build")


def test_A2_referans_kumesi_BOS_DEGIL_pozitif_kontrol():
    """A1'in pozitif kontrolü. Referans çıkarımı sessizce boşalırsa (manifest şeması değişir,
    `pano.html` başka bir yoldan yüklenir) A1 HER ŞEYİ ölü sayardı ve o kırmızı doğru sebeple
    olmazdı; buradaki alt sınır o sessiz boşalmayı ayrı bir cümleyle yakalar."""
    o = arac.olcum(DIZIN, MANIFEST, HTML)
    assert len(o.referans) >= 2, (
        f"referans kümesi {sorted(o.referans)} — en az bir js (giriş) ve bir css beklenir; "
        f"çıkarım bozulduysa A1'in 'ölü' listesi UYDURMADIR")
    assert any(a.endswith(".js") for a in o.referans), "referans kümesinde js YOK"
    assert any(a.endswith(".css") for a in o.referans), "referans kümesinde css YOK"


# =================================================================================================
# Sentetik zemin — B ve C bölümlerinin fikstürü
# =================================================================================================

CANLI_JS = "pano-AAAAAAAA.js"
CANLI_CSS = "pano-BBBBBBBB.css"
OLU_JS = "pano-CCCCCCCC.js"
OLU_CSS = "pano-DDDDDDDD.css"
EL_YAZIMI = "elle-kopya.js"           # hash'siz: son segment 5 karakter (< 8) → aday DEĞİL
#: İKİNCİ el yazımı dosya, BAŞKA bir sebeple hash'siz: son segment ≥8 karakter ama TİRE TAŞIYOR.
#: Mutasyon ölçümünün (M4, 2026-09-13) doğurduğu fikstür — desen tireye izin verecek şekilde
#: genişletilirse bu ad hash SAYILIR ve silinir; `elle-kopya.js` tek başına o mutasyonu GÖRMÜYORDU
#: (kısa segment her iki desende de eleniyor). Aynı tuzak `ops/etkilenen_testler.sh::_hashli`da
#: da ölçülmüştü: tireli segment `OLMAYAN-DOSYA-xyzzy.md`yi hash saydırmıştı.
EL_YAZIMI_TIRELI = "elle-birakilmis-kopya.js"


@pytest.fixture
def zemin(tmp_path):
    """İki canlı (manifest + html referanslı), iki ölü, bir hash'siz el yazımı dosya.
    Dönüş: (dizin, manifest, html)."""
    d = tmp_path / "web" / "pano-assets"
    d.mkdir(parents=True)
    (d / CANLI_JS).write_text("canli js" * 10, encoding="utf-8")
    (d / CANLI_CSS).write_text("canli css" * 10, encoding="utf-8")
    (d / OLU_JS).write_text("olu js" * 100, encoding="utf-8")
    (d / OLU_CSS).write_text("olu css" * 100, encoding="utf-8")
    (d / EL_YAZIMI).write_text("el yazimi", encoding="utf-8")
    (d / EL_YAZIMI_TIRELI).write_text("el yazimi, tireli", encoding="utf-8")
    man = d / "manifest.json"
    man.write_text(json.dumps({"pano.html": {"file": f"pano-assets/{CANLI_JS}",
                                             "name": "pano", "isEntry": True,
                                             "css": [f"pano-assets/{CANLI_CSS}"]}}),
                   encoding="utf-8")
    html = d.parent / "pano.html"
    html.write_text(
        f'<script type="module" src="/pano-assets/{CANLI_JS}"></script>\n'
        f'<link rel="stylesheet" href="/pano-assets/{CANLI_CSS}">\n', encoding="utf-8")
    return d, man, html


def _adlar(d: pathlib.Path) -> set[str]:
    return {p.name for p in d.iterdir()}


def _argv(d: pathlib.Path, man: pathlib.Path, html: pathlib.Path) -> list[str]:
    return ["--dizin", str(d), "--manifest", str(man), "--html", str(html)]


# =================================================================================================
# B — KOMUT SATIRI SÖZLEŞMESİ
# =================================================================================================

def test_B1_VARSAYILAN_KURU_tek_bayt_silmez_ama_OLUYU_listeler(zemin):
    """Varsayılan kip KURUdur — bayrak unutulduğunda silinen dosya olamaz. Kuru koşum yine de
    ADLARI basar: "temiz" ile "çıktı yok" aynı görünmesin (pytest `-qq` dersinin kardeşi)."""
    d, man, html = zemin
    onceki = _adlar(d)
    r = _kos(*_argv(d, man, html))
    assert r.returncode == 0, f"kuru koşum 0 dönmedi: rc={r.returncode}\n{r.stdout}\n{r.stderr}"
    assert _adlar(d) == onceki, f"KURU koşum dosya sildi: {onceki - _adlar(d)}"
    assert OLU_JS in r.stdout and OLU_CSS in r.stdout, f"ölü adlar listelenmiyor:\n{r.stdout}"
    assert "KURU" in r.stdout.upper(), f"kip çıktıda yazılı değil:\n{r.stdout}"


def test_B2_KURU_bayragi_ACIKCA_verilince_de_silmez(zemin):
    d, man, html = zemin
    onceki = _adlar(d)
    r = _kos("--kuru", *_argv(d, man, html))
    assert r.returncode == 0
    assert _adlar(d) == onceki


def test_B3_UYGULA_OLUYU_siler_CANLIYA_dokunmaz(zemin):
    """Silme ve koruma TEK koşumda ölçülür: ikisini ayrı çivilere bölmek, 'sildi ama yanlışını
    sildi' hâlini iki yeşil test arasından geçirirdi."""
    d, man, html = zemin
    olu_bayt = (d / OLU_JS).stat().st_size + (d / OLU_CSS).stat().st_size
    r = _kos("--uygula", *_argv(d, man, html))
    assert r.returncode == 0, f"rc={r.returncode}\n{r.stdout}\n{r.stderr}"
    kalan = _adlar(d)
    assert OLU_JS not in kalan and OLU_CSS not in kalan, f"ölü dosya SİLİNMEDİ: {kalan}"
    assert {CANLI_JS, CANLI_CSS, "manifest.json", EL_YAZIMI, EL_YAZIMI_TIRELI} <= kalan, (
        f"referanslı/hash'siz dosya SİLİNDİ — canlı sayfa ölür: kalan={kalan}")
    assert str(olu_bayt) in r.stdout, (
        f"toplam bayt raporda YOK ({olu_bayt} bekleniyordu) — kazanç ölçülmeden bildirilemez:\n"
        f"{r.stdout}")


def test_B4_HASHSIZ_dosyaya_ASLA_dokunulmaz(zemin):
    """`manifest.json` ve el yazımı dosyalar aday KÜMESİNİN DIŞINDADIR: araç yalnız içerik-hash'li
    adları tanır. Aksi hâlde dizine bilerek konmuş bir dosya ilk derlemede buharlaşırdı."""
    d, man, html = zemin
    r = _kos("--uygula", *_argv(d, man, html))
    assert r.returncode == 0
    assert (d / EL_YAZIMI).is_file(), "hash'siz el yazımı dosya silindi (kısa segment)"
    assert (d / EL_YAZIMI_TIRELI).is_file(), (
        "TİRELİ el yazımı dosya silindi — hash deseni genişlemiş; dizine bilerek konan dosya "
        "ilk derlemede buharlaşır")
    assert (d / "manifest.json").is_file(), "manifest silindi"
    for ad in (EL_YAZIMI, EL_YAZIMI_TIRELI):
        assert ad in r.stdout, f"atlanan dosya raporda anılmıyor ({ad}):\n{r.stdout}"


def test_B5_PANO_HTML_referansi_manifest_ANMASA_DA_korur(zemin):
    """İki kaynak, İKİSİ DE bağlayıcı. `pano.html` manifestten bir derleme geride kalabilir
    (elle kopyalama, yarım rsync); o hâlde sayfanın YÜKLEDİĞİ dosyayı silmek canlıyı öldürür.
    Referans kümesi bu yüzden BİRLEŞİMDİR, kesişim değil."""
    d, man, html = zemin
    html.write_text(f'<script src="/pano-assets/{OLU_JS}"></script>', encoding="utf-8")
    r = _kos("--uygula", *_argv(d, man, html))
    assert r.returncode == 0, f"rc={r.returncode}\n{r.stderr}"
    assert (d / OLU_JS).is_file(), "pano.html'in YÜKLEDİĞİ dosya silindi — sayfa canlıda ölür"
    assert not (d / OLU_CSS).is_file(), "gerçekten ölü olan css silinmedi (çivi kendini kandırdı)"


def test_B6_IDEMPOTENT_ikinci_kosum_hicbir_sey_silmez(zemin):
    d, man, html = zemin
    _kos("--uygula", *_argv(d, man, html))
    onceki = _adlar(d)
    r = _kos("--uygula", *_argv(d, man, html))
    assert r.returncode == 0
    assert _adlar(d) == onceki, "ikinci koşum dosya sildi — küme yakınsamıyor"
    assert "TOPLAM 0 dosya" in r.stdout, f"ikinci koşumun özeti sıfırı ADIYLA demiyor:\n{r.stdout}"


def test_B7_CELISEN_KIP_CIFTI_kullanim_hatasi_ve_SILME_YOK(zemin):
    """`dagit.sh`ın kip kapısıyla aynı disiplin: çelişen çift sessizce bir tarafı seçmez."""
    d, man, html = zemin
    onceki = _adlar(d)
    r = _kos("--kuru", "--uygula", *_argv(d, man, html))
    assert r.returncode == 2, f"çelişen kip çifti rc 2 vermedi: {r.returncode}\n{r.stdout}"
    assert _adlar(d) == onceki, "çelişen kip çiftiyle dosya silindi"


def test_B9_PANO_HTML_YOKSA_olcum_bosluguni_ADIYLA_basar_ve_manifest_korur(zemin):
    """İkinci kaynak okunamadıysa araç "iki kaynağı da okudum" DEMEZ (uydurma yasağı). Silme
    durmaz — sayfa yoksa onun yüklediği bir dosya da yoktur — ama manifestin beyanı yine de
    dokunulmaz kalır."""
    d, man, html = zemin
    html.unlink()
    r = _kos("--uygula", *_argv(d, man, html))
    assert r.returncode == 0, f"rc={r.returncode}\n{r.stdout}\n{r.stderr}"
    assert "YALNIZ manifestten" in r.stdout, (
        f"ölçüm boşluğu (sayfa yok) sessizce geçildi:\n{r.stdout}")
    assert (d / CANLI_JS).is_file() and (d / CANLI_CSS).is_file(), "manifest referansı silindi"
    assert not (d / OLU_JS).is_file(), "ölü dosya silinmedi (sayfa yokluğu silmeyi durdurmamalı)"


def test_B8_SILME_BASARISIZSA_rc_1_ve_ad_stderrde(zemin, monkeypatch, capsys):
    """BEYANLI SAPMA (bu dosyanın tek `main()` çağrısı): gerçek bir silme arızası üretmek
    platforma bağlı olurdu (kök kullanıcı salt-okunur dizinde de siler). argv yine GERÇEK bir
    komut satırı listesidir; yalnız `unlink` yamalanır."""
    d, man, html = zemin

    def _patlat(self, *a, **k):
        raise OSError(13, "izin yok")

    monkeypatch.setattr(pathlib.Path, "unlink", _patlat)
    rc = arac.main(["--uygula", *_argv(d, man, html)])
    yakalanan = capsys.readouterr()
    assert rc == 1, f"silme hatası rc 1 vermedi: {rc}"
    assert OLU_JS in yakalanan.err, f"silinemeyen dosya adı stderr'de YOK:\n{yakalanan.err}"


# =================================================================================================
# C — ZEMİN YOKSA SİLME YOK (fail-closed)
# =================================================================================================

def test_C1_MANIFEST_YOKSA_rc_2_ve_SILME_YOK(zemin):
    d, man, html = zemin
    man.unlink()
    onceki = _adlar(d)
    r = _kos("--uygula", *_argv(d, man, html))
    assert r.returncode == 2, f"manifest yokken rc 2 beklenirdi: {r.returncode}\n{r.stdout}"
    assert _adlar(d) == onceki, "manifest yokken dosya silindi — referans kümesi UYDURULDU"


def test_C2_MANIFEST_BOZUKSA_rc_2_ve_SILME_YOK(zemin):
    """Yarım yazılmış manifest JSON değildir. Onu 'boş küme' saymak, dizindeki HER ŞEYİ ölü
    saymak demektir — bu aracın yapabileceği en pahalı hata."""
    d, man, html = zemin
    man.write_text('{"pano.html": {"file": ', encoding="utf-8")
    onceki = _adlar(d)
    r = _kos("--uygula", *_argv(d, man, html))
    assert r.returncode == 2
    assert _adlar(d) == onceki


def test_C3_MANIFEST_BOS_BEYANSA_rc_2_ve_SILME_YOK(zemin):
    """Sözdizimi geçerli ama beyan boş (`{}`): yine zemin yoktur. Boş kümeyle silmek, dizini
    süpürmektir."""
    d, man, html = zemin
    man.write_text("{}", encoding="utf-8")
    onceki = _adlar(d)
    r = _kos("--uygula", *_argv(d, man, html))
    assert r.returncode == 2
    assert _adlar(d) == onceki


def test_C4_BEYAN_EDILEN_DOSYA_DISKTE_YOKSA_rc_2_ve_SILME_YOK(zemin):
    """Manifest diskteki gerçeği tarif etmiyorsa referans kümesine güvenilemez: derleme yarım
    kalmış ya da dizin elle kurcalanmıştır. Bu hâlde silmek, doğru bilgi yokken karar vermektir."""
    d, man, html = zemin
    (d / CANLI_JS).unlink()
    onceki = _adlar(d)
    r = _kos("--uygula", *_argv(d, man, html))
    assert r.returncode == 2, f"eksik referansta rc 2 beklenirdi: {r.returncode}\n{r.stdout}"
    assert _adlar(d) == onceki, "eksik referans varken silme yapıldı"
    assert CANLI_JS in r.stdout + r.stderr, "eksik referansın adı raporlanmıyor"


def test_C5_DIZIN_YOKSA_rc_2(zemin, tmp_path):
    d, man, html = zemin
    r = _kos("--uygula", "--dizin", str(tmp_path / "olmayan"), "--manifest", str(man),
             "--html", str(html))
    assert r.returncode == 2, f"olmayan dizinde rc 2 beklenirdi: {r.returncode}\n{r.stdout}"


# =================================================================================================
# D — ZİNCİR: derlemenin SON adımı
# =================================================================================================

def _build_betigi() -> str:
    return json.loads((UI / "package.json").read_text(encoding="utf-8"))["scripts"]["build"]


def test_D1_npm_build_SON_adimi_temizliktir():
    """Sıra HÜKÜMDÜR: temizlik `vite build`ten SONRA koşmalı (önce koşsaydı yeni derlemenin
    henüz var olmayan çıktısını referanssız sayardı) ve zincirin SONUNDA durmalı — artefakt
    tazelik kapısı ([5c], `ops/artefakt_tazelik.py`) derlemeden sonraki her kaynak dokunuşunu
    bayatlık sayar."""
    b = _build_betigi()
    assert "vite build" in b, f"build zincirinde `vite build` yok: {b}"
    assert "pano_artefakt_temizle.py" in b, f"temizlik adımı build zincirinde YOK: {b}"
    assert b.index("pano_artefakt_temizle.py") > b.index("vite build"), (
        f"temizlik `vite build`ten ÖNCE koşuyor — yeni çıktıyı ölü sayar: {b}")
    assert "--uygula" in b, f"zincirdeki temizlik KURU kipte — hiçbir şey silinmez: {b}"


def test_D2_build_zincirindeki_YOLLAR_gercekten_cozulur():
    """Zincirdeki göreli yollar `ui/` içinden çözülür. Yanlış yazılmış bir yol derlemeyi
    kırmaz (python "dosya yok" der, npm zinciri düşer) ama sessizce de kalabilir — ölç."""
    b = _build_betigi()
    for jeton in b.replace("&&", " ").split():
        if jeton.startswith("../") or jeton.startswith("./"):
            assert (UI / jeton).exists(), f"build zincirindeki yol çözülmüyor: {jeton}"


def test_D3_vite_emptyOutDir_HALA_false():
    """Temizlik aracı `emptyOutDir: true` yapmanın YERİNE geçer, onu mümkün kılmaz: çıktı klasörü
    `meridian/web/` ve orada el yazımı index.html/app.js/tokens.json/fonts/ yaşıyor. Bayrak
    dönerse pano temizlenmez, PANONUN KOMŞULARI silinir."""
    metin = (UI / "vite.config.ts").read_text(encoding="utf-8")
    assert "emptyOutDir: false" in metin, (
        "vite `emptyOutDir` artık false değil — meridian/web'deki el yazımı dosyalar her "
        "derlemede silinir (bu aracın çözdüğü sorun DEĞİL, çok daha büyüğü)")
