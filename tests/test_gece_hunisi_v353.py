"""test_gece_hunisi_v353.py — "GECE NE BULDU" HUNİSİNİN SAF ÇEKİRDEĞİ (2026-08-31).

ÖLÇÜLEN ARIZA: operatör panonun huni kartını "hiç tarama olmadı" diye okudu. Gerçek: döngü
koşmuş, 0 aday bulmuştu. Üç kusur üst üste binmişti ve ÜÇÜ DE bir React bileşeninin içinde
yaşıyordu:

  (a) İlk basamağın ETİKETİ "Taranan aday"dı ama bağlandığı alan eleme SONRASI `candidates`ti —
      huninin AĞZI hiç çizilmiyordu.
  (b) Aday 0 iken dipnot "ilk basamak yazılı değil" diyordu. Yazılıydı (0). Gerçek sebep
      "payda 0, oran hesaplanamaz"dı; iki AYRI olgu tek cümleye indirilmişti.
  (c) Eleme ÖNCESİ evren büyüklüğü hiçbir yere kaydedilmiyordu (motor tarafı — `loop.daily_cycle`
      artık `taranan`/`taranan_neden` yazıyor, çivileri `test_loop_gaps_v48`; uca ulaşması
      `test_wp2d_pano_beyani_v246` §5b).

NEDEN AYRI DOSYA VE NEDEN NODE: kusurların üçü de haftalarca sessiz kaldı çünkü bileşen
içindeki türetmeye ancak `assert "<metin>" in kaynak` biçiminde bakılabiliyordu ve o çivi,
ifadeyi bozan ama adı koruyan mutasyonda ISIRMAZ (v347 incelemesinin B4 dersi). Türetme bu
turda `ui/src/pano/yuzeyler/kanban/gece.ts` + `huni_cekirdek.ts` içine SAF olarak taşındı ve
`tests/civiler/gece_hunisi_civileri.mjs` onu node'da ÇAĞIRIYOR. Bu dosya o koşucuyu suite'e
bağlar — koşucu bağlanmasaydı okuyucusuz bir artefakt olurdu (YASA 6).

HİÇBİR TEST CANLI STATE'E YAZMAZ: burada state'e hiç dokunulmuyor, yalnız `ui/` kaynağı
paketlenip node'da değerlendiriliyor.
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
GIRIS = "src/pano/yuzeyler/kanban/gece.ts"
CEKIRDEK = "src/pano/yuzeyler/kanban/huni_cekirdek.ts"
KOSUCU = KOK / "tests/civiler/gece_hunisi_civileri.mjs"

pytestmark = pytest.mark.skipif(not (UI / "src").exists(), reason="ui/ yok — pano kaynağı bu ağaçta değil")


def _node() -> str:
    n = shutil.which("node")
    if n is None or not ESBUILD.exists():
        pytest.skip("node ya da esbuild yok — saf çekirdek DAVRANIŞI ölçülemedi (GEÇTİ DEĞİL)")
    return n


def _kos(*ek: str) -> subprocess.CompletedProcess[str]:
    """`gece.ts`i paketleyip çivi koşucusunu çalıştırır.

    Paketleme BURADA yapılıyor (v350 deseni): `esbuild` düşerse bunu ÇİVİNİN kendi hatası
    olarak görelim, koşucunun içinde sessizce yutulup 'çivi kırmızı' diye okunmasın."""
    node = _node()
    with tempfile.TemporaryDirectory() as d:
        paket = Path(d) / "gece.mjs"
        yap = subprocess.run(
            [str(ESBUILD), GIRIS, "--bundle", "--format=esm", "--platform=node", f"--outfile={paket}"],
            cwd=UI, capture_output=True, text=True)
        assert yap.returncode == 0, f"esbuild düştü:\n{yap.stderr}"
        return subprocess.run([node, str(KOSUCU), str(paket), *ek], capture_output=True, text=True)


def test_KOSUCU_dosyasi_YERINDE():
    assert KOSUCU.exists(), f"çivi koşucusu yok: {KOSUCU} — huninin türetmesi ölçüsüz kaldı"


def test_civi_kosucusu_KIRMIZIYA_donebiliyor():
    """POZİTİF KONTROL (v152 disiplini). Koşucu bilerek yanlış bir iddiayla çağrılır ve
    SIFIRDAN FARKLI çıkmak ZORUNDADIR — yoksa aşağıdaki yeşil vakumda doğru olurdu."""
    r = _kos("--kendini-sina")
    assert r.returncode != 0, (
        "çivi koşucusu bilerek YANLIŞ bir iddiayı geçirdi — düzenek kırık.\n"
        f"stdout:\n{r.stdout}\nstderr:\n{r.stderr}")


def test_HUNI_civileri_gecti():
    r = _kos()
    assert r.returncode == 0, (
        "gece hunisi çivileri KIRMIZI — hangi iddianın düştüğü aşağıda:\n"
        f"{r.stdout}\n{r.stderr}")
    assert "çivi GEÇTİ" in r.stdout, "koşucu özet satırını basmadı — çıktı kesilmiş olabilir"


def test_civi_sayisi_TABANI():
    """SAYI NÖBETÇİSİ: koşucudan iddia silmek testi yeşil bırakır (0 iddia da 0 ile çıkar).
    Sayı ÖLÇÜLDÜ (2026-08-31: 17); taban bilerek altında — eklemek serbest, toptan silmek değil."""
    r = _kos()
    m = re.search(r"TOPLAM (\d+) çivi GEÇTİ", r.stdout)
    assert m is not None, f"çivi sayısı okunamadı — özet biçimi değişmiş olabilir:\n{r.stdout}"
    n = int(m.group(1))
    assert n >= 16, f"çivi sayısı {n}'e düştü (2026-08-31 ölçümü: 17) — iddialar sessizce silinmiş"


# =================================================================================================
# KAPSAM BEYANI — hangi saf fonksiyon çivili, hangisi DEĞİL
# =================================================================================================
CIVISIZ_BEYAN: dict[str, str] = {
    "huniTabani": "dolaylı çivili: `geceModeli`nin ürettiği her oran bu kuralla bölünüyor "
                  "([3] bölümü paydayı dört ayrı hâlde ölçüyor) ve `Huni` şeridi de aynı "
                  "çağrıyı yapıyor — ayrı bir doğrudan iddia aynı kuralı iki kez ölçerdi",
    "tabanNedeni": "dolaylı çivili: dipnot metinleri ([2] bölümü) bu fonksiyonun üç hâlinin "
                   "TAMAMINI ekrandaki hâliyle ölçüyor — kusurun yaşadığı katman orası",
}


def test_SAF_FONKSIYON_KAPSAMI_beyanli():
    """"Hepsi ölçülüyor" cümlesi ancak SAYILARAK kurulabilir (v350 deseni)."""
    kaynak = (UI / GIRIS).read_text(encoding="utf-8") + (UI / CEKIRDEK).read_text(encoding="utf-8")
    fonksiyonlar = set(re.findall(r"^export function (\w+)", kaynak, re.M))
    assert len(fonksiyonlar) >= 4, f"ayrıştırıcı yalnız {len(fonksiyonlar)} dışa aktarım gördü — desen bayat"
    govde = KOSUCU.read_text(encoding="utf-8")
    civisiz = sorted(f for f in fonksiyonlar if f"G.{f}(" not in govde and f not in CIVISIZ_BEYAN)
    assert not civisiz, (
        f"{len(civisiz)} saf fonksiyon hiç ÇAĞRILMIYOR: {civisiz}\n"
        "Ya koşucuya çivi ekle, ya `CIVISIZ_BEYAN`a gerekçesiyle yaz.")
    bos = [f for f, neden in CIVISIZ_BEYAN.items() if len(neden) < 20]
    assert not bos, f"beyan gerekçesiz: {bos} (≥20 karakter şart)"
    olu = [f for f in CIVISIZ_BEYAN if f not in fonksiyonlar]
    assert not olu, f"beyan edilen fonksiyon kaynakta YOK — beyan bayatlamış: {olu}"


# =================================================================================================
# ÇEKİRDEK REACT'SİZ KALIR — yoksa node'da çağrılamaz ve bu dosya SESSİZCE atlanır
# =================================================================================================
def test_CEKIRDEK_React_ithal_ETMIYOR():
    """Bu çivinin tamamı `gece.ts`in node'da paketlenebilmesine dayanıyor. Bir gün oraya
    `@/components/...` ya da `react` ithali girerse esbuild takma adı çözemez ve bütün
    ölçüm 'skip'e düşerdi — yani sessizce körleşirdik."""
    for yol in (GIRIS, CEKIRDEK):
        s = (UI / yol).read_text(encoding="utf-8")
        kod = re.sub(r"/\*.*?\*/", "", s, flags=re.S)
        ithal = re.findall(r'^import\s+(?!type\b)[^;]*?from\s+"([^"]+)"', kod, re.M)
        kirli = [m for m in ithal if m.startswith("@/") or m == "react" or m.endswith(".tsx")]
        assert not kirli, (
            f"{yol} saf değil, çalışma-zamanı ithali var: {kirli} — node'da paketlenemez "
            "ve bu dosyadaki bütün çiviler sessizce atlanır")
