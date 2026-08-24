"""PANO YÜZEY KAYDI ↔ EKRAN ÇAPASI PARİTESİ — v288 (2026-08-25)

NEDEN BU ÇİVİ VAR. Eski panoda aynı bilgi ÜÇ yerde birden yaşıyordu ve üçü elle
senkron tutuluyordu (`app.js::VIEWS`, `app.js::ALAN_BOLUMLERI`, `index.html`in
`.page`/`.alan-bolum` kapları). Biri kaydığında hata ÇIKMIYOR, bölüm sessizce
ÇİZİLMİYORDU — 2026-08-24'te `karar` alanı tam olarak böyle boş okundu.

Yeni pano bu hastalığı `pano/alanlar.ts`teki TEK kayıtla kapatmayı amaçladı. Ama
göç turunda hastalık YENİ BİR KILIKTA geri geldi: kayıt ile yüzey gövdelerini
farklı eller yazdı ve ikisi ayrıştı. Ölçüldü (2026-08-25, göç turu bitişi):

    · kayıtta olup ekranda ÇAPASI OLMAYAN 14 bölüm
      → `#/dashboard/academy/karne` gibi derin bağ sayfayı açar ama BÖLÜME KAYDIRMAZ;
        hata yok, sessiz bir "çalışmıyor gibi".
    · ekranda olup kayıtta OLMAYAN 9 bölüm
      → kenar çubuğunda hiç görünmezler; bölüm VAR ama gezinmede YOK.

İki yön de sessiz. Çivi ikisini de kapatıyor.

SÖZLEŞME: `alanlar.ts`teki her `kimlik` için kaynakta bir `bolum-<kimlik>` çapası
OLMAK ZORUNDA, ve kaynaktaki her `bolum-<X>` çapası kayıtta OLMAK ZORUNDA.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

KOK = Path(__file__).resolve().parent.parent
PANO = KOK / "ui" / "src" / "pano"
KAYIT = PANO / "alanlar.ts"
YUZEYLER = PANO / "yuzeyler"

pytestmark = pytest.mark.skipif(not KAYIT.exists(), reason="ui/ yok — pano kaynağı bu ağaçta değil")


def _soy(metin: str) -> str:
    """Yorumları ve dizge içindeki gürültüyü at.

    NEDEN: bu depoda aynı ölçüm hatası ÜÇ KEZ yapıldı — bir kuralın YORUMDA geçmesi
    onun KULLANILDIĞI anlamına gelmiyor. Çapayı bir açıklama satırında sayarsak,
    hiç çizilmeyen bir bölümü "var" diye okuruz.
    """
    metin = re.sub(r"/\*.*?\*/", "", metin, flags=re.S)
    metin = re.sub(r"^\s*//.*$", "", metin, flags=re.M)
    metin = re.sub(r"\{/\*.*?\*/\}", "", metin, flags=re.S)
    return metin


def _kayitli_bolumler() -> dict[str, str]:
    """`alanlar.ts` → {bölüm kimliği: içinde durduğu yüzey anahtarı}."""
    s = _soy(KAYIT.read_text(encoding="utf-8"))
    # Yüzey blokları: `  <anahtar>: {` … `bolumler: [ … ]`
    sonuc: dict[str, str] = {}
    for m in re.finditer(r'^\s{2}"?([a-z-]+)"?:\s*\{', s, re.M):
        anahtar = m.group(1)
        blok = s[m.end():]
        son = re.search(r'^\s{2}\},', blok, re.M)
        blok = blok[: son.start()] if son else blok
        for k in re.finditer(r'kimlik:\s*"([a-z0-9-]+)"', blok):
            sonuc[k.group(1)] = anahtar
    return sonuc


def _ekran_capalari() -> dict[str, set[str]]:
    """Kaynakta geçen bölüm çapaları → {kimlik: {dosya, …}}.

    İKİ YAZIM BİÇİMİ VAR VE İKİSİ DE OKUNMALI — bu, çivinin İLK sürümünde yapılmış
    ölçüm hatasıdır ve kaydı burada duruyor (2026-08-25, uzlaştırma turu):

      · DÜZ:      `id="bolum-market"`         → regex doğrudan görür
      · BİLEŞİK:  `id={`bolum-${kimlik}`}`    → regex GÖREMEZ

    Beş paylaşılan sarmalayıcı (ogrenme/ortak · sistem/parcalar · kuyruk/parcalar ·
    kimlik/parcalar · yetki/parcalar) ikinci biçimi kullanıyor ve kimliği ÇAĞRI
    YERİNDE `kimlik="market"` propuyla alıyor. İlk sürüm bunları göremediği için
    15 bölümü "çapası yok" diye bildirdi; 15'i de YALANCI POZİTİFTİ ve düzeltmesi
    kaynağa İKİNCİ bir `id` eklemek olurdu — aynı sayfada çift `id`, ve
    `getElementById` ilk bulduğuna kayardı. Yani yanlış ölçüm, gerçek bir kusur
    ÜRETECEKTİ. Ayrıştırıcı koda uyduruldu; kod ayrıştırıcıya değil.
    """
    sonuc: dict[str, set[str]] = {}
    for p in sorted(YUZEYLER.rglob("*.tsx")):
        metin = _soy(p.read_text(encoding="utf-8"))
        yol = p.relative_to(KOK).as_posix()
        for m in re.finditer(r'bolum-([a-z0-9-]+)', metin):
            sonuc.setdefault(m.group(1), set()).add(yol)
        # BİLEŞİK BİÇİM: dosya `bolum-${...}` yazıyorsa, o dosyadaki `kimlik="x"`
        # propları o çapanın gerçek değerleridir. Sarmalayıcının KENDİSİ prop
        # taşımaz (orada `kimlik` bir parametredir), çağıran dosya taşır — bu
        # yüzden iki tarafı da tarayıp birleştiriyoruz.
        for m in re.finditer(r'kimlik=\{?"([a-z0-9-]+)"\}?', metin):
            sonuc.setdefault(m.group(1), set()).add(yol)
    return sonuc


def test_kayit_bos_degil():
    """Ayrıştırıcı sessizce boş okursa aşağıdaki iki çivi TRIVIAL geçer — bu nöbetçi
    o hâli yakalar. (Bu depoda birebir bu tuzağa düşüldü: `ALAN_BOLUMLERI` tek satıra
    yazılmadığı için iki test `karar` alanını boş okuyor ve yeşil kalıyordu.)"""
    kayitli = _kayitli_bolumler()
    assert len(kayitli) >= 20, f"kayıt ayrıştırıcısı yalnız {len(kayitli)} bölüm gördü — ayrıştırıcı bayat"


def test_kayitli_her_bolumun_ekranda_capasi_VAR():
    """Kayıtta duran her bölüm derin bağla ULAŞILABİLİR olmalı."""
    kayitli = _kayitli_bolumler()
    capalar = _ekran_capalari()
    eksik = sorted(f"{k} (yüzey: {y})" for k, y in kayitli.items() if k not in capalar)
    assert not eksik, (
        f"kayıtta olup ekranda ÇAPASI OLMAYAN {len(eksik)} bölüm: {eksik}\n"
        "Kenar çubuğu bu bölümlere bağ veriyor ama tıklandığında sayfa açılır, bölüme "
        "KAYDIRMAZ — hata vermez, sessizce çalışmaz. Gövdeyi çizen bileşene "
        'id="bolum-<kimlik>" koy (GenelYuzey.tsx desenine bak).')


# ~~"EKRANDAKİ HER ÇAPA KAYITTA OLMALI"~~ — TERS YÖN ÇİVİ OLMAKTAN ÇIKARILDI (2026-08-25).
#
# İlk sürüm iki yönü de çiviliyordu. Ölçüm ters yönün bir KUSUR değil bir TASARIM
# TERCİHİ olduğunu gösterdi: ekranda `id="bolum-…"` taşıyan 14 blok daha var
# (makine · bilesenler · zamanlayici · kosular · takvim · cagrilar · sozlesme ·
# defter · oturum · eksikler · seviyeler · izinler · terfi · kapi) ve hepsini
# kaydetmek kenar çubuğunu 22 bölümden 36'ya çıkarırdı. Bir çapa "gezinme durağı"
# olmak zorunda değildir — sayfa içi bir bloğun kendi kimliği de olabilir.
#
# ASIL KUSUR SINIFI BAŞKAYDI ve aşağıda çivileniyor: aynı kimliğin İKİ kayda
# birden girmesi. `_kayitli_bolumler()` sözlüğü kimliği KÜRESEL tutuyor; iki yüzey
# aynı kimliği kaydederse biri ötekini SESSİZCE ezer ve bir bölüm gezinmeden düşer.
# Bu tur `defter` kimliğinde tam bu riskle karşılaşıldı (chat sekmesi + tasks defteri).


def test_kayitli_kimlikler_TEKİL():
    """Aynı bölüm kimliği iki yüzeyde birden kayıtlı OLAMAZ.

    Kayıt sözlüğü kimliği küresel tutuyor (`BOLUMUN_ALANI`), yani çakışan ikinci
    girdi birincisini sessizce ezer: bölüm kenar çubuğunda görünür ama derin bağı
    YANLIŞ yüzeye çözülür. Hata yok, yanlış varış.
    """
    s = _soy(KAYIT.read_text(encoding="utf-8"))
    hepsi = re.findall(r'kimlik:\s*"([a-z0-9-]+)"', s)
    tekrar = sorted({k for k in hepsi if hepsi.count(k) > 1})
    assert not tekrar, (
        f"aynı bölüm kimliği birden çok yüzeyde kayıtlı: {tekrar} — "
        "kimliklerden birini yeniden adlandır (kayıt sözlüğü kimliği KÜRESEL tutuyor)")
