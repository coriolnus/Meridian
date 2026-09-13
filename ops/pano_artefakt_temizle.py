#!/usr/bin/env python3
"""ops/pano_artefakt_temizle.py — pano derlemesinin ÖLÜ artefaktlarını budar (TSK-185).

NEDEN VAR — ÖLÇÜLDÜ (2026-09-13). `ui/vite.config.ts` `emptyOutDir: false` taşır ve TAŞIMAK
ZORUNDA: çıktı klasörü `meridian/web/` ve Vite'ın varsayılanı o klasörü TEMİZLER — yani el yazımı
`index.html`, `app.js`, `tokens.json` ve `fonts/` her derlemede silinirdi. Bayrağın bedeli şudur:
her derleme `pano-assets/` altına yeni bir içerik-hash'li js + css bırakır ve ESKİSİNİ SİLMEZ.
Ölçüm günü depoda 5 js + 4 css git-İZLİYDİ; manifest ve `pano.html` bunların yalnız birer tanesini
işaret ediyordu. Kalan 4 js + 3 css (~8,4 MB) rsync ile canlıya gidiyor ve orada SUNULAMIYOR
bile — `meridian/api.py::pano_varlik` manifestte olmayan her adı 404'ler. Yani: okuyucusu olmayan
artefakt (YASA 6) + dağıtım yüzeyinde ölü bayt.

NEDEN `emptyOutDir: true` DEĞİL: o bayrak sorunu çözmez, büyütür — pano temizlenmez, PANONUN
KOMŞULARI silinir (yukarıdaki el yazımı dosyalar). Bu araç, dizinin TAMAMINI süpürmek yerine
DERLEMENİN KENDİ BEYANINI okur ve yalnız beyan dışı kalan hash'li adları düşürür.

REFERANS KÜMESİ İKİ KAYNAĞIN BİRLEŞİMİDİR, kesişimi değil:
  1. `pano-assets/manifest.json` — Vite'ın beyanı; `api.py`nin sunum kapısı da bunu okur.
  2. `meridian/web/pano.html`    — sayfanın GERÇEKTEN yüklediği adlar.
İkisi bir derleme kayabilir (elle kopyalama, yarım rsync). Kesişim alınsaydı sayfanın yüklediği
bir dosya silinebilirdi; birleşim en kötü hâlde bir derleme fazla dosya tutar. Yanlış tarafta
kalmanın bedeli asimetriktir: fazla dosya MB'dır, eksik dosya ÖLÜ SAYFADIR.

FAIL-CLOSED: zemin güvenilmezse HİÇBİR ŞEY silinmez (çıkış 2). Zemin yoksa saymak şudur —
manifest yok · manifest bozuk · manifest boş beyan · manifestin/HTML'in andığı bir dosya diskte
yok · hedef dizin yok. Boş bir referans kümesiyle çalışmak, dizindeki HER ŞEYİ ölü saymak
demektir; bu aracın yapabileceği en pahalı hata odur.

GIT KULLANILMAZ, DOSYA SİSTEMİ SİLİNİR (`git rm` DEĞİL). Araç derleme zincirinin içinden koşar
(`npm run build`) ve o an hangi konumda olunduğu bilinmez — CLAUDE.md §8: ajan/yan oturum git
komutu koşmaz. İzli dosyanın silinmesini Rol-1 `git add -u` ile yakalar.

KOMUT SATIRI SÖZLEŞMESİ (ops sözleşmesi `main()` değil KOMUT SATIRIdır, vaka 2026-08-30):

    python3 ops/pano_artefakt_temizle.py [--kuru | --uygula] [--dizin D] [--manifest M] [--html H]

Kip VARSAYILAN KURUdur: bayrak unutulduğunda silinen dosya olamaz. İki kip birden verilirse
kullanım hatasıdır (`dagit.sh`ın çelişen-kip kapısıyla aynı disiplin) — sessizce bir taraf
seçilmez.

Çıkış kodu HÜKÜMDÜR:
    0  TAMAM        listelendi (kuru) ya da silindi (uygula) — silinecek şey olmaması da 0'dır
    1  EKSİK SİLME  en az bir ölü dosya silinemedi (adı stderr'de); kalanlar yine silindi
    2  ZEMİN YOK    referans kümesine güvenilemez ya da kullanım hatası → HİÇBİR SİLME

OKUYUCU (YASA 6): `ui/package.json` `build` zincirinin son adımı · `tests/
test_pano_artefakt_temizlik_v478.py` · operatör (elle bakım). Araç hiçbir artefakt ÜRETMEZ;
yalnız stdout'a rapor yazar ve dosya siler.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import pathlib
import re
import sys

#: İÇERİK-HASH'Lİ AD: son tire segmenti ≥8 karakter ve TİRE İÇERMEZ (`pano-B0709Zmr.js`).
#: `ops/etkilenen_testler.sh::_hashli` aynı soruyu kabuk tarafında sorar ve desen oradan
#: İTHAL EDİLEMEZ (bash ↔ python). İki desen BİLEREK aynı dar biçimdedir ve ikisi de aynı
#: ölçülmüş tuzaktan kaçınır: segmente tire sokulursa `elle-birakilmis-dosya.js` gibi EL YAZIMI
#: adlar hash sayılır. Ayrışma riski burada tek yönlü ve ucuzdur: bu desen daralırsa ölü dosya
#: KALIR (v478 A1 kırmızı olur), genişlerse el yazımı dosya aday olur — o yüzden genişletmeden
#: önce v478'in B4 çivisi okunur.
#: BİLİNEN SINIR, BEYANLA (ölçüldü 2026-09-13): desen UZANTIYI tek parça ister, yani
#: `pano-B0709Zmr.js.map` gibi ÇİFT uzantılı bir kaynak haritası aday SAYILMAZ ve budanmaz.
#: Bugün böyle bir dosya üretilmiyor (`build.sourcemap` kapalı — `ui/vite.config.ts`); açılırsa
#: ölü haritalar birikir. Sınır bu yönde BİLİNÇLİ: desen genişletmenin riski (el yazımı dosyayı
#: silmek) birikmenin bedelinden büyüktür — genişletmeden önce v478 B4 okunur.
HASH_DESENI = re.compile(r"-[A-Za-z0-9_]{8,}\.[A-Za-z0-9]+$")

#: `pano.html` içindeki varlık referansları: `/pano-assets/<ad>` (script src, link href,
#: modulepreload). Dizin adı DESENE GÖMÜLÜ DEĞİL — `--dizin` başka bir ad taşıyabilir; bu yüzden
#: yakalanan şey yalnız SON SEGMENTTİR ve karşılaştırma ad üzerinden yapılır.
HTML_REFERANS_DESENI = re.compile(r"/pano-assets/([A-Za-z0-9_.\-]+)")

VARSAYILAN_DIZIN = "meridian/web/pano-assets"
VARSAYILAN_MANIFEST = "meridian/web/pano-assets/manifest.json"
VARSAYILAN_HTML = "meridian/web/pano.html"


class ZeminYok(Exception):
    """Referans kümesine güvenilemez — çağıran çıkış 2 ile döner ve HİÇBİR ŞEY silmez."""


@dataclasses.dataclass(frozen=True)
class Olcum:
    """Tek bir ölçümün tamamı. `olu` DIŞINDAKİ alanlar raporun dürüstlüğü içindir: yalnız
    silinecekleri döndürmek, korunanı ve atlananı GÖRÜNMEZ kılardı (bedel yasası — neyin
    kaybolmadığı da ölçülür)."""

    referans: frozenset[str]
    mevcut: frozenset[str]
    olu: list[str]
    korunan: list[str]
    atlanan: list[str]
    eksik: list[str]
    bayt: int


def hashli(ad: str) -> bool:
    """Ad içerik-hash'li mi? Yalnız hash'li adlar SİLME ADAYIDIR; `manifest.json` ve dizine
    bilerek konmuş el yazımı dosyalar aday kümesinin DIŞINDADIR."""
    return bool(HASH_DESENI.search(ad))


def manifest_referanslari(ham: object) -> set[str]:
    """Vite manifestinin beyan ettiği varlık ADLARI (son segment).

    `meridian/api.py::_pano_varliklari` ile AYNI alanları gezer (`file` + `css`) ve bir tane daha
    ekler: `assets` (font/ikon gibi varlıklar). Sunum kapısından GENİŞ olması bilinçlidir — bu
    taraf SİLER, o taraf sunar: silme kararı daha geniş bir koruma kümesiyle verilir."""
    adlar: set[str] = set()
    if not isinstance(ham, dict):
        raise ZeminYok("manifest bir JSON nesnesi değil")
    for girdi in ham.values():
        if not isinstance(girdi, dict):
            continue
        dosya = girdi.get("file")
        if isinstance(dosya, str):
            adlar.add(dosya.rsplit("/", 1)[-1])
        for anahtar in ("css", "assets"):
            for yol in girdi.get(anahtar) or ():
                if isinstance(yol, str):
                    adlar.add(yol.rsplit("/", 1)[-1])
    return adlar


def html_referanslari(metin: str) -> set[str]:
    """Sayfanın GERÇEKTEN yüklediği varlık adları."""
    return set(HTML_REFERANS_DESENI.findall(metin))


def _manifest_oku(manifest: pathlib.Path) -> set[str]:
    """Manifesti okur ve beyan kümesini döndürür. Boş beyan ZEMİN YOKtur: `api.py` orada dürüst
    bir 404 yazabilir (sunulmaz), ama burada aynı boşluk "her şeyi sil" anlamına gelirdi."""
    if not manifest.is_file():
        raise ZeminYok(f"manifest yok: {manifest} (derleme koşmamış — `cd ui && npm run build`)")
    try:
        ham = json.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        raise ZeminYok(f"manifest okunamadı/bozuk: {manifest} ({e})") from e
    adlar = manifest_referanslari(ham)
    if not adlar:
        raise ZeminYok(f"manifest BOŞ beyan taşıyor: {manifest} — boş referans kümesiyle silmek "
                       f"dizini süpürmektir")
    return adlar


def olcum(dizin: pathlib.Path, manifest: pathlib.Path, html: pathlib.Path) -> Olcum:
    """Ölçümün tamamı; hiçbir dosyaya DOKUNMAZ (saf okuma). `ZeminYok` fırlatırsa çağıran
    çıkış 2 ile döner."""
    if not dizin.is_dir():
        raise ZeminYok(f"varlık dizini yok: {dizin}")

    referans = _manifest_oku(manifest)
    if html.is_file():
        referans |= html_referanslari(html.read_text(encoding="utf-8"))
    # `pano.html` YOKSA zemin yine de yeterlidir: manifest tek başına derlemenin beyanıdır ve
    # HTML bir sonraki adımda yazılır (Vite önce varlıkları, sonra sayfayı üretir). Eksikliği
    # ADIYLA basmak çağıranın işi değil — silme kararı manifestten güvenle verilebilir.

    mevcut = {p.name for p in dizin.iterdir() if p.is_file()}
    adaylar = {ad for ad in mevcut if hashli(ad)}
    olu = sorted(adaylar - referans)
    # EKSİK ÖLÇÜLÜR, BURADA HÜKÜM VERİLMEZ (ayrım bilinçli): ölçüm dürüst kalır ve çivi iki yönü
    # de AYNI nesneden okuyabilir; "eksik varsa silme" kararı `main`in fail-closed dalıdır.
    # Ölçümün kendisi istisna fırlatsaydı, ayrışma çivisi eksikliği bir assert ile değil bir
    # traceback ile bildirirdi — kırmızının sebebi okunmaz olurdu.
    return Olcum(
        referans=frozenset(referans),
        mevcut=frozenset(mevcut),
        olu=olu,
        korunan=sorted(adaylar & referans),
        atlanan=sorted(mevcut - adaylar),
        eksik=sorted(referans - mevcut),
        bayt=sum((dizin / ad).stat().st_size for ad in olu),
    )


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dizin", default=VARSAYILAN_DIZIN, help=f"varlık dizini ({VARSAYILAN_DIZIN})")
    ap.add_argument("--manifest", default=VARSAYILAN_MANIFEST,
                    help=f"Vite manifesti ({VARSAYILAN_MANIFEST})")
    ap.add_argument("--html", default=VARSAYILAN_HTML,
                    help=f"sayfanın kendisi ({VARSAYILAN_HTML}); ikinci referans kaynağı")
    ap.add_argument("--kuru", action="store_true", help="yalnız LİSTELE (VARSAYILAN)")
    ap.add_argument("--uygula", action="store_true", help="ölü artefaktları SİL")
    args = ap.parse_args(argv)

    if args.kuru and args.uygula:
        print("HATA: --kuru ve --uygula birlikte verilemez — kip TEK olmalı (hiçbir şey "
              "silinmedi)", file=sys.stderr)
        return 2

    dizin = pathlib.Path(args.dizin)
    html = pathlib.Path(args.html)
    if not html.is_file():
        # ÖLÇÜM BOŞLUĞU ADIYLA BASILIR (uydurma yasağı): referans kümesi bu koşumda tek
        # kaynaklıdır. Silmeyi durdurmaz — manifest derlemenin kendi beyanıdır ve sayfa yoksa
        # onun yüklediği bir dosya da yoktur — ama "iki kaynağı da okudum" DENMEZ.
        print(f"NOT: sayfa yok ({html}) — referans YALNIZ manifestten okundu")
    try:
        o = olcum(dizin, pathlib.Path(args.manifest), html)
    except ZeminYok as e:
        print(f"ZEMİN YOK: {e} · SİLME YAPILMADI", file=sys.stderr)
        return 2

    if o.eksik:
        # FAIL-CLOSED. Manifest/HTML diskteki gerçeği tarif etmiyorsa referans kümesine
        # güvenilemez (yarım derleme, elle kurcalanmış dizin). Bilgi eksikken silmek, doğru
        # bilgi yokken karar vermektir.
        print("ZEMİN YOK: referans var ama DOSYA YOK: " + ", ".join(o.eksik)
              + " · SİLME YAPILMADI (onarım: cd ui && npm run build)", file=sys.stderr)
        print("ZEMİN YOK — eksik referans: " + ", ".join(o.eksik))
        return 2

    for ad in o.korunan:
        print(f"KORUNDU {ad}")
    for ad in o.atlanan:
        print(f"ATLANDI {ad} (hash'siz — araç tanımaz)")

    rc = 0
    for ad in o.olu:
        yol = dizin / ad
        bayt = yol.stat().st_size
        if args.uygula:
            try:
                yol.unlink()
            except OSError as e:
                print(f"SİLİNEMEDİ {ad}: {e}", file=sys.stderr)
                rc = 1
                continue
            print(f"SİLİNDİ {ad} ({bayt} bayt)")
        else:
            print(f"SİLİNECEK {ad} ({bayt} bayt)")

    kip = "UYGULA (silindi)" if args.uygula else "KURU (silme yok)"
    print(f"TOPLAM {len(o.olu)} dosya / {o.bayt} bayt · korunan {len(o.korunan)} · "
          f"atlanan {len(o.atlanan)} · mod: {kip}")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
