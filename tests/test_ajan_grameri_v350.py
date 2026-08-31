"""AJAN YÜZEYİNİN GRAMERİ — SAF ÇEKİRDEK DAVRANIŞI · v350 (2026-08-31)

NUMARA TAŞIMASI. v348 olarak doğdu, aynı gün v350'ye taşındı: v348 `test_filo_araci_v348.py`nin
kimliğiydi (vNNN çakışmasında az-çapalı taraf taşınır — vaka v331×2, 2026-08-30).

NE ÖLÇÜLÜYOR. Ajan yüzeyi bu turda mesajlaşma gramerine taşındı ve görünüm kararlarının
tamamı (`hangi muhatap seçili` · `hangi sekme açık` · `kim bugün aktif` · `oturumlar hangi
sırada akıyor` · `süzgeç neyi geçiriyor`) TEK bir saf modüle çekildi:
`ui/src/pano/yuzeyler/ajan/gramer.ts`. Bu çivi o modülün DAVRANIŞINI koşar.

NEDEN KAYNAK METNİ DEĞİL, KOŞUM. v347'nin kendi dersi (inceleme B4): `assert "<kimlik>" in
kaynak` biçimindeki bir çivi, ifadeyi bozan ama kimliği koruyan bir mutasyonda ISIRMAZ.
Buradaki iddiaların hepsi `esbuild` + `node` ile gerçekten çağrılıyor — emsal
`test_pano_palet_v152` ve v347'nin `_js_cekirdek`i, aynı beyanlı atlama disipliniyle:
araç yoksa test GEÇMİŞ sayılmaz, ATLANIR.

TEK KAYNAK, İKİ KOŞUCU. İddia gövdesi `tests/civiler/gramer_civileri.mjs`te ve suite ile
elden koşum AYNI dosyayı çalıştırır:
    node tests/civiler/gramer_civileri.mjs
Çivileri Python'a KOPYALAMADIK — kopyalasaydık aynı sözleşmenin iki nüshası sessizce
ayrışırdı (tek-kaynak yasası). Bedeli beyanlıdır: pytest bu iddiaları TEK test olarak görür,
tek tek değil. Karşılığında bir SAYI NÖBETÇİSİ (`test_civi_sayisi_TABANI`) ve bir POZİTİF
KONTROL (`test_civi_kosucusu_KIRMIZIYA_donebiliyor`) var; ikisi olmadan "N çivi geçti"
cümlesi vakumda doğru olabilirdi.

DİKİŞ DE BURADA (yeniden-inceleme Ö-1b, 2026-08-31). Koşucunun son bölümü (`[7] dikiş`)
`gramer.ts`in DIŞINA çıkar: `ui/src/pano/alanlar.ts`i ayrıca paketleyip `bolumBasligi`i
node'da çağırır ve `Ustbar.tsx`in kayda sorduğunu metinle tutar. Gerekçe: saf bir
fonksiyonun doğru olması ÇAĞRILDIĞINI kanıtlamaz — `Ustbar`ı eski `bolumler.find(...)`
hâline döndürmek derleniyor ve bu tur öncesinde tüm suite yeşil kalıyordu.

v347 T2j/T2k'DEN DEVRALINAN KISIM. Orada `filoOku.ts::aktifAnahtar` çivileniyordu; o
fonksiyon bu turda EMEKLİ oldu ve yerini `gramer.ts::muhatapSec` aldı. İkisi DAVRANIŞÇA DENK
DEĞİL, bu yüzden assert'ler taşınmadı, YENİDEN YAZILDI:
  · eski sürüm bayat seçimde sessizce İLK AJANA düşüyordu,
  · yenisi KANALA düşüyor, istenen adı `bulunamayan` ile EKRANA taşıyor ve ayrıca
    "liste hiç okunamadı" hâlini `listeOlculemedi` ile ayırıyor (inceleme Ö-2).
Karşılıkları: `[5] muhatap seçimi` bölümündeki beş çivi.
"""
from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

KOK = Path(__file__).resolve().parents[1]
UI = KOK / "ui"
ESBUILD = UI / "node_modules/.bin/esbuild"
GIRIS = "src/pano/yuzeyler/ajan/gramer.ts"
KOSUCU = KOK / "tests/civiler/gramer_civileri.mjs"

pytestmark = pytest.mark.skipif(not (UI / "src").exists(), reason="ui/ yok — pano kaynağı bu ağaçta değil")


def _node() -> str:
    n = shutil.which("node")
    if n is None or not ESBUILD.exists():
        pytest.skip("node ya da esbuild yok — saf çekirdek DAVRANIŞI ölçülemedi (GEÇTİ DEĞİL)")
    return n


def _kos(*ek: str) -> subprocess.CompletedProcess[str]:
    """`gramer.ts`i paketleyip çivi koşucusunu çalıştırır.

    Paketleme BURADA yapılıyor, koşucunun içinde değil: aynı paket iki teste de verilebilsin
    ve `esbuild` düşerse bunu ÇİVİNİN kendi hatası olarak görelim (koşucunun içinde sessizce
    yutulup 'çivi kırmızı' diye okunmasın)."""
    node = _node()
    with tempfile.TemporaryDirectory() as d:
        paket = Path(d) / "gramer.mjs"
        yap = subprocess.run(
            [str(ESBUILD), GIRIS, "--bundle", "--format=esm", "--platform=node", f"--outfile={paket}"],
            cwd=UI, capture_output=True, text=True)
        assert yap.returncode == 0, f"esbuild düştü:\n{yap.stderr}"
        return subprocess.run([node, str(KOSUCU), str(paket), *ek], capture_output=True, text=True)


def test_KOSUCU_dosyasi_YERINDE():
    """Çivi gövdesi depoda DURUYOR mu. Bu tur öncesinde iddialar `.superpowers/` altındaydı ve
    orası `.gitignore`da: ölçülmüş ama KORUNMAMIŞ, cloud klonunda hiç yok. Nöbetçi o hâle
    geri dönüşü yakalar."""
    assert KOSUCU.exists(), f"çivi koşucusu yok: {KOSUCU} — gramerin davranışı ölçüsüz kaldı"


def test_civi_kosucusu_KIRMIZIYA_donebiliyor():
    """POZİTİF KONTROL (v152 disiplini). Koşucu bilerek yanlış bir iddiayla çağrılır ve
    SIFIRDAN FARKLI çıkmak ZORUNDADIR. Bu olmadan aşağıdaki test, koşucu her koşulda 0
    dönse bile yeşil kalırdı — 'davranışı ölçtüm' cümlesi vakumda doğru olurdu."""
    r = _kos("--kendini-sina")
    assert r.returncode != 0, (
        "çivi koşucusu bilerek YANLIŞ bir iddiayı geçirdi — düzenek kırık, aşağıdaki yeşil "
        f"hiçbir şey kanıtlamaz.\nstdout:\n{r.stdout}\nstderr:\n{r.stderr}")


def test_GRAMER_civileri_gecti():
    """ASIL ÇİVİ: `gramer.ts`in tüm saf hükümleri node'da koşuluyor."""
    r = _kos()
    assert r.returncode == 0, (
        "ajan grameri çivileri KIRMIZI — hangi iddianın düştüğü aşağıda:\n"
        f"{r.stdout}\n{r.stderr}")
    assert "çivi GEÇTİ" in r.stdout, "koşucu özet satırını basmadı — çıktı kesilmiş olabilir"


def test_civi_sayisi_TABANI():
    """SAYI NÖBETÇİSİ. Koşucudan çivi silmek testi yeşil bırakır (0 iddia da 0 ile çıkar);
    bu taban o sessiz daralmayı yakalar. Sayı ÖLÇÜLDÜ (2026-08-31: 55 → yeniden-inceleme
    Ö-1b dikiş bölümüyle 59) ve taban bilerek altında: çivi eklemek serbest, toptan silmek
    değil."""
    r = _kos()
    m = re.search(r"TOPLAM (\d+) çivi GEÇTİ", r.stdout)
    assert m is not None, f"çivi sayısı okunamadı — özet biçimi değişmiş olabilir:\n{r.stdout}"
    n = int(m.group(1))
    assert n >= 54, f"çivi sayısı {n}'e düştü (2026-08-31 ölçümü: 59) — iddialar sessizce silinmiş"


# =================================================================================================
# KAPSAM BEYANI — hangi dışa aktarım çivili, hangisi DEĞİL
# -------------------------------------------------------------------------------------------------
# "Hepsi ölçülüyor" cümlesi ancak SAYILARAK kurulabilir. Bu test `gramer.ts`in dışa aktarım
# yüzeyini okur ve koşucuda hiç GEÇMEYEN bir fonksiyon kalmadığını doğrular; kalması gerekiyorsa
# gerekçesiyle beyan edilir (YASA 4 deseni: kaçış açık işaretle).
CIVISIZ_BEYAN: dict[str, str] = {
    # (bugün boş — beş fonksiyon inceleme Ö-7 ile kapsama alındı)
}


def test_DISA_AKTARIM_KAPSAMI_beyanli():
    kaynak = (UI / GIRIS).read_text(encoding="utf-8")
    fonksiyonlar = set(re.findall(r"^export function (\w+)", kaynak, re.M))
    assert len(fonksiyonlar) >= 12, f"ayrıştırıcı yalnız {len(fonksiyonlar)} dışa aktarım gördü — desen bayat"
    govde = KOSUCU.read_text(encoding="utf-8")
    civisiz = sorted(f for f in fonksiyonlar if f"G.{f}(" not in govde and f not in CIVISIZ_BEYAN)
    assert not civisiz, (
        f"{len(civisiz)} saf fonksiyon hiç ÇAĞRILMIYOR: {civisiz}\n"
        "Ya koşucuya çivi ekle, ya `CIVISIZ_BEYAN`a gerekçesiyle yaz — ölçüsüz bir sözleşme "
        "sessizce bayatlar (YASA 6 kuzeni).")
    bos = [f for f, neden in CIVISIZ_BEYAN.items() if len(neden) < 20]
    assert not bos, f"beyan gerekçesiz: {bos} (≥20 karakter şart)"
    olu = [f for f in CIVISIZ_BEYAN if f not in fonksiyonlar]
    assert not olu, f"beyan edilen fonksiyon kaynakta YOK — beyan bayatlamış: {olu}"


# =================================================================================================
# EMEKLİ EDİLEN DIŞA AKTARIMLAR GERİ SIZMASIN
# -------------------------------------------------------------------------------------------------
# `filoOku.ts`ten üç fonksiyon bu turda kaldırıldı (inceleme Ö-5): `aktifAnahtar` · `mesajSayisi`
# · `modeller`. Üçünün de tek çağıranı silinen `Filo.tsx::{FiloGovdesi, AjanKarti}`ydı. Yerlerini
# `gramer.ts` aldı ve İKİSİ DENK DEĞİL (`aktifAnahtar` → `muhatapSec`, docstring'e bak). Bu çivi
# eskilerinin geri sızmasını değil, YENİLERİNİN VARLIĞINI tutar: biri silinirse yukarıdaki kapsam
# testi zaten öter, ama eskisi geri eklenirse İKİ KAYNAK oluşur ve o sessizdir.
ESKI_ADLAR = ("aktifAnahtar", "mesajSayisi", "modeller")


def test_EMEKLI_ADLAR_geri_gelmedi():
    oku = (UI / "src/pano/yuzeyler/ajan/filoOku.ts").read_text(encoding="utf-8")
    kod = re.sub(r"/\*.*?\*/", "", oku, flags=re.S)
    geri = [a for a in ESKI_ADLAR if f"export function {a}" in kod]
    assert not geri, (
        f"emekli edilen dışa aktarım geri gelmiş: {geri} — aynı hükmün iki kaynağı oluşur ve "
        "ikisi sessizce ayrışır (tek-kaynak yasası). Yerleri `gramer.ts`te.")
    yeni = (UI / GIRIS).read_text(encoding="utf-8")
    for ad in ("muhatapSec", "mesajToplami", "penceredekiModeller"):
        assert f"export function {ad}" in yeni, (
            f"`{ad}` yok — emekli edilen ölçümün karşılığı da düşmüş, yani ölçüm BEYANSIZ kaybolmuş "
            "(bedel yasası)")
