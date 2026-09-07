"""PANO SOHBETİ — SAF ÇEKİRDEK DAVRANIŞI + UÇ SÖZLEŞMESİ · v443 (TSK-012 dalga-B, B2)

NUMARA. v443 SERBESTTİ (2026-09-07 ölçümü: `tests/` altında en yüksek kimlik v442, `v443`/`v444`
depoda hiç geçmiyor). vNNN bir KİMLİKTİR; çakışmada az-çapalı taraf taşınır.

NE ÖLÇÜLÜYOR. Dalga-B'nin UI yarısı (B2) `/api/sohbet` gövdelerini okuyup ekrana cümle kuruyor ve
`sohbet_onerisi` satırlarını onay kuyruğuna bağlıyor. Bu hükümlerin tamamı React'siz iki saf modüle
çekildi ve burada GERÇEKTEN koşuluyor:
    ui/src/pano/yuzeyler/ajan/sohbet.ts          (geçmiş · kota · yanıt durumu · oturum · ⌘K devri)
    ui/src/pano/yuzeyler/kuyruk/sohbetOnerisi.ts (donuk öneri sözlüğü · kimlik biçimi · uyarılar)
artı DİKİŞ: `kuyruk/onaylar.ts::kuyrugaCevir` ve `kuyruk/onayEylem.ts::onayHedefi` bu sözlüğü
gerçekten çağırıyor mu (saf bir fonksiyonun doğru olması ÇAĞRILDIĞINI kanıtlamaz — v350 dersi).

NEDEN KAYNAK METNİ DEĞİL, KOŞUM. `assert "<kimlik>" in kaynak` biçimindeki bir çivi, ifadeyi bozan
ama adı koruyan mutasyonda ISIRMAZ (v347 incelemesi B4). İddialar `esbuild` + `node` ile çağrılıyor;
araç yoksa test GEÇMİŞ sayılmaz, ATLANIR (v350 ile aynı beyanlı atlama disiplini).

TEK KAYNAK, İKİ KOŞUCU. İddia gövdesi `tests/civiler/sohbet_civileri.mjs`te; suite ile elden koşum
AYNI dosyayı çalıştırır:
    node tests/civiler/sohbet_civileri.mjs
Kopyalamadık — kopyalasaydık aynı sözleşmenin iki nüshası sessizce ayrışırdı. Bedeli beyanlıdır:
pytest bu iddiaları TEK test olarak görür. Karşılığında bir SAYI NÖBETÇİSİ ve bir POZİTİF KONTROL var.

AYRICA: DONUK SÖZLÜĞÜN İKİ TARAFI. `sohbetOnerisi.ts` öneri türlerinin ve kimlik biçiminin bir
KOPYASINI taşıyor (pano Python'u import edemez). Kopya kaçınılmazsa ayrışma çivilenir (tek-kaynak
yasası, CLAUDE.md §4) — `test_DONUK_SOZLUK_iki_tarafta_AYNI` tam olarak budur.
"""
from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import pytest

KOK = Path(__file__).resolve().parents[1]
UI = KOK / "ui"
ESBUILD = UI / "node_modules/.bin/esbuild"
KOSUCU = KOK / "tests/civiler/sohbet_civileri.mjs"
SAF_MODULLER = (
    "src/pano/yuzeyler/ajan/sohbet.ts",
    "src/pano/yuzeyler/kuyruk/sohbetOnerisi.ts",
)

pytestmark = pytest.mark.skipif(not (UI / "src").exists(), reason="ui/ yok — pano kaynağı bu ağaçta değil")


def _node() -> str:
    n = shutil.which("node")
    if n is None or not ESBUILD.exists():
        pytest.skip("node ya da esbuild yok — saf çekirdek DAVRANIŞI ölçülemedi (GEÇTİ DEĞİL)")
    return n


def _kos(*ek: str) -> subprocess.CompletedProcess[str]:
    """Çivi koşucusunu çalıştırır. Paketlemeyi koşucu KENDİ yapıyor (dört ayrı giriş
    noktası paketliyor: iki saf modül + iki dikiş modülü); burada yapıp geçirmek,
    dördünü de ayrı ayrı yönetmek demek olurdu."""
    return subprocess.run([_node(), str(KOSUCU), *ek], capture_output=True, text=True, cwd=str(KOK))


def test_KOSUCU_dosyasi_YERINDE():
    """Çivi gövdesi depoda DURUYOR mu — `.gitignore`lı bir dizine kaçarsa ölçülmüş ama
    KORUNMAMIŞ olurdu (v350'nin aynı nöbetçisi)."""
    assert KOSUCU.exists(), f"çivi koşucusu yok: {KOSUCU} — sohbet grameri ölçüsüz kaldı"


def test_civi_kosucusu_KIRMIZIYA_donebiliyor():
    """POZİTİF KONTROL (v152 disiplini): koşucu bilerek yanlış bir iddiayla çağrılır ve
    SIFIRDAN FARKLI çıkmak ZORUNDADIR."""
    r = _kos("--kendini-sina")
    assert r.returncode != 0, (
        "çivi koşucusu bilerek YANLIŞ bir iddiayı geçirdi — düzenek kırık, aşağıdaki yeşil "
        f"hiçbir şey kanıtlamaz.\nstdout:\n{r.stdout}\nstderr:\n{r.stderr}")


def test_SOHBET_civileri_gecti():
    """ASIL ÇİVİ: B2'nin saf hükümleri + kuyruk dikişi node'da koşuluyor."""
    r = _kos()
    assert r.returncode == 0, (
        "pano sohbeti çivileri KIRMIZI — hangi iddianın düştüğü aşağıda:\n"
        f"{r.stdout}\n{r.stderr}")
    assert "çivi GEÇTİ" in r.stdout, "koşucu özet satırını basmadı — çıktı kesilmiş olabilir"


def test_civi_sayisi_TABANI():
    """SAYI NÖBETÇİSİ: koşucudan çivi silmek testi yeşil bırakır (0 iddia da 0 ile çıkar).
    Sayı ÖLÇÜLDÜ (2026-09-08 düzeltme turu 1: 49, K-1/K-2 çivileriyle 42'den yükseldi) ve
    taban bilerek altında — çivi eklemek serbest, toptan silmek değil."""
    r = _kos()
    m = re.search(r"TOPLAM (\d+) çivi GEÇTİ", r.stdout)
    assert m is not None, f"çivi sayısı okunamadı — özet biçimi değişmiş olabilir:\n{r.stdout}"
    n = int(m.group(1))
    assert n >= 40, f"çivi sayısı {n}'e düştü (2026-09-08 ölçümü: 49) — iddialar sessizce silinmiş"


# =================================================================================================
# KAPSAM BEYANI — hangi saf dışa aktarım çivili, hangisi DEĞİL
# -------------------------------------------------------------------------------------------------
# "Hepsi ölçülüyor" cümlesi ancak SAYILARAK kurulabilir (v350'nin aynı nöbetçisi). Beyan boş
# kalırsa çivisiz bir sözleşme sessizce bayatlar (YASA 6 kuzeni).
CIVISIZ_BEYAN: dict[str, str] = {
    # (bugün boş — iki modülün tüm dışa aktarımları koşucuda çağrılıyor)
}


def test_DISA_AKTARIM_KAPSAMI_beyanli():
    govde = KOSUCU.read_text(encoding="utf-8")
    fonksiyonlar: set[str] = set()
    for yol in SAF_MODULLER:
        kaynak = (UI / yol).read_text(encoding="utf-8")
        fonksiyonlar |= set(re.findall(r"^export function (\w+)", kaynak, re.M))
    assert len(fonksiyonlar) >= 20, (
        f"ayrıştırıcı yalnız {len(fonksiyonlar)} dışa aktarım gördü — desen bayat olabilir")
    civisiz = sorted(
        f for f in fonksiyonlar
        if f"S.{f}(" not in govde and f"O.{f}(" not in govde and f not in CIVISIZ_BEYAN)
    assert not civisiz, (
        f"{len(civisiz)} saf fonksiyon hiç ÇAĞRILMIYOR: {civisiz}\n"
        "Ya koşucuya çivi ekle, ya `CIVISIZ_BEYAN`a gerekçesiyle yaz.")
    bos = [f for f, neden in CIVISIZ_BEYAN.items() if len(neden) < 20]
    assert not bos, f"beyan gerekçesiz: {bos} (≥20 karakter şart)"
    olu = [f for f in CIVISIZ_BEYAN if f not in fonksiyonlar]
    assert not olu, f"beyan edilen fonksiyon kaynakta YOK — beyan bayatlamış: {olu}"


# =================================================================================================
# DONUK SÖZLÜĞÜN İKİ TARAFI — kopya kaçınılmaz, AYRIŞMA ÇİVİLİ
# -------------------------------------------------------------------------------------------------
# `meridian/sohbet.py` öneri türlerini ve kimlik biçimini DONUK tutuyor; pano bunları Python'dan
# import EDEMEZ (tarayıcıda koşuyor). Bu yüzden kopya var ve kopyanın bedeli burada ödeniyor:
# türlerden biri backend'de değişirse, panonun uyarı metinleri sessizce YANLIŞ tür için çizilirdi.
def test_DONUK_SOZLUK_iki_tarafta_AYNI():
    from meridian.sohbet import ONERI_TURLERI

    kaynak = (UI / "src/pano/yuzeyler/kuyruk/sohbetOnerisi.ts").read_text(encoding="utf-8")
    m = re.search(r"export const SOHBET_ONERI_TURLERI = \[(.*?)\] as const;", kaynak, re.S)
    assert m is not None, "pano tarafındaki donuk sözlük bulunamadı — biçim değişmiş olabilir"
    panodakiler = tuple(re.findall(r'"([a-z_]+)"', m.group(1)))
    assert panodakiler == tuple(ONERI_TURLERI), (
        f"öneri türleri AYRIŞTI — motor: {tuple(ONERI_TURLERI)} · pano: {panodakiler}. "
        "Pano bu sözlüğe göre uyarı metni ve geri-alınabilirlik hükmü çiziyor; ayrışma, yanlış "
        "türe yanlış cümle yazdırır (`alarm_ack`in GLOBAL etkisi gibi).")


def test_ONERI_KIMLIK_BICIMI_iki_tarafta_AYNI():
    """Kimlik deseni de kopya: pano `SO-…` kimliğini TANIYAMAZSA karar yolu "önek yok"
    gerekçesiyle KAPANIR (`onayEylem.ts` sohbet dalı ondan ÖNCE duruyor)."""
    from meridian.sohbet import oneri_kimligi, oneri_kimligi_mi

    ornek = oneri_kimligi("20260907T193000Z", 1)
    assert oneri_kimligi_mi(ornek), "motorun kendi ürettiği kimliği kendi tanımıyor — B1 kusuru"
    kaynak = (UI / "src/pano/yuzeyler/kuyruk/sohbetOnerisi.ts").read_text(encoding="utf-8")
    m = re.search(r"const KIMLIK_DESENI = /(.+?)/;", kaynak)
    assert m is not None, "pano tarafındaki kimlik deseni bulunamadı — biçim değişmiş olabilir"
    panodaki = re.compile(m.group(1))
    assert panodaki.match(ornek), (
        f"pano deseni motorun ürettiği kimliği TANIMIYOR: {ornek!r} vs /{m.group(1)}/ — "
        "sohbet önerisi onay kuyruğunda karara bağlanamaz hâle gelir")
    assert not panodaki.match("SO:20260907T193000Z-1"), (
        "desen iki nokta taşıyan kimliği kabul ediyor — `api_approve` kimliği ilk `:`ten böler, "
        "yani böyle bir kimlik tanınmaz bir öneke düşerdi")
