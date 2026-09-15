"""VİTE PANODA "DURUM SÖZLÜĞÜ" YÜZEYİ — v504 (TSK-070 A2/A8 · tasarım §9.2/§9.3, 2026-09-15).

ÖLÇÜLEN BOŞLUK (keşif, 2026-09-15): `/api/diagnostics.durum_sozlugu` 2026-08-23'ten beri
servis ediliyordu ve okuyucusu YALNIZ eski `app.js`ti (`/eski`). Operatörün varsayılan yüzeyi
olan Vite panoda (`/`, `/pano`) sözlüğün HİÇBİR satırı görünmüyordu: yani kanonik kelime
üretiliyor, kimse okumuyordu (Yasa 6'nın ekran tarafı). A8 hükmü sözlüğü dokuz aileye
genişletti; bu dosya o satırların PANOYA çıktığını ve ORADA ikinci bir sözlük DOĞMADIĞINI
çivilir.

ÜÇ SINIF ÇİVİLENİR:

  1. YÜZEY GERÇEKTEN VAR VE KANONİK SATIRI BASAR — `durum_sozlugu.satirlar[]`in dört taşıyıcı
     alanı (`aile`, `kimlik`, `kelime`, `beyan`) kaynakta okunur. Bir bileşenin var olması onu
     ekrana çıkarmaz: durak kaydı (`alanlar.ts`) ve yüzey yönlendiricisi
     (`SistemSagligiYuzey.tsx`) AYRICA ölçülür — ikisinden biri eksikken dosya diskte durur,
     operatör hiçbir şey görmez ve bu SESSİZDİR (v288'in kapattığı sınıfın aynısı).

  2. UI HAM KELİME ÇEVİRMEZ (A8 hükmü, tek kaynak yasası) — kelime BACKEND'de üretilir
     (`PANO_KELIME`, `meridian/durum_sozlugu.py`). Panoda ikinci bir çeviri tablosu doğarsa iki sözlük
     sessizce ayrışır: bugün `app.js` tam olarak bunu yapıyor (satır-içi çeviriler) ve yeni
     yüzeyin varlık sebeplerinden biri o tekrarı YAPMAMAKTIR. Çivi ham üretici kodlarının
     dizge olarak geçmediğini ölçer.

  3. UYDURMA YASAĞININ EKRAN KARŞILIĞI — ölçülemeyen sayı `null`dır ve pano onu
     "ÖLÇÜLEMEDİ (0 DEĞİL)" diye basar. Boş hücre ile sıfır aynı görünürse intraday atlama
     ailesinin BÜTÜN değeri kaybolur (0 ile None arasındaki fark o ailenin tek konusudur).

KAYNAĞA BAKAR, TARAYICI AÇMAZ (repo deseni v154/v288/v460): Node/vitest koşulmaz, `npm run
build` bu çividen ÇAĞRILMAZ — build ayrı ve EN SON adımdır (dagit [5c] mtime kapısı).
Tip sözleşmesinin derleyici tarafı `cd ui && npx tsc -b` ile ayrıca ölçülür; bu dosya onun
yerine geçmez, alan ADLARININ uç sözleşmesiyle aynı olduğunu ölçer.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

KOK = Path(__file__).resolve().parent.parent
PANO = KOK / "ui" / "src" / "pano"
TSX = PANO / "yuzeyler" / "sistem" / "DurumSozlugu.tsx"
TIPLER = PANO / "yuzeyler" / "sistem" / "uctipleri.ts"
KAYIT = PANO / "alanlar.ts"
YONLENDIRICI = PANO / "yuzeyler" / "SistemSagligiYuzey.tsx"

pytestmark = pytest.mark.skipif(not KAYIT.exists(), reason="ui/ yok — pano kaynağı bu ağaçta değil")

# ÜRETİCİ TARAFININ HAM KODLARI — panoda GEÇMEMELİ. Kaynakları: watchdog rapor kovaları
# (`stale`/`never`), kilit kolu (`learning_halted`), kitap damga sınıfı
# (`damga_ilerledi_icerik_ayni`), intraday atlama anahtarı (`no_bars`), hermes atlama kodları
# (`lock_busy`, `bg_reflect`). Hepsinin kanonik kelimesi backend'de üretilir.
HAM_KELIMELER = (
    "stale",
    "never",
    "learning_halted",
    "damga_ilerledi_icerik_ayni",
    "no_bars",
    "lock_busy",
    "bg_reflect",
)


def _oku(yol: Path) -> str:
    assert yol.exists(), f"beklenen pano kaynağı YOK: {yol.relative_to(KOK).as_posix()}"
    return yol.read_text(encoding="utf-8")


def _soy(metin: str) -> str:
    """Yorumları at (v288'in `_soy`u ile aynı gerekçe, BU dosyada MUTASYONLA ölçüldü).

    İlk sürüm ham metne bakıyordu ve test_c bu dosyanın KENDİ ŞERHİNDEKİ "ÖLÇÜLEMEDİ
    (0 DEĞİL)" cümlesiyle yeşildi: kalıbı koddan silince çivi ötmedi. Bir kuralın YORUMDA
    geçmesi onun UYGULANDIĞI anlamına gelmez — ekranda çizilmeyen bir kalıp, yazılmamış
    kalıptır. `test_b` (ham kelime yasağı) BİLEREK ham metne bakar: orada yorum da dahil
    hiçbir yerde geçmemesi istenir, çünkü çeviri tablosu şerh diye başlar."""
    metin = re.sub(r"/\*.*?\*/", "", metin, flags=re.S)
    return re.sub(r"^\s*//.*$", "", metin, flags=re.M)


def test_a_yuzey_var_ve_kanonik_satiri_basar():
    """Yüzey `durum_sozlugu.satirlar[]`i okur ve satırın dört taşıyıcı alanını basar."""
    m = _soy(_oku(TSX))
    for alan in ("durum_sozlugu", ".satirlar", ".kelime", ".aile", ".beyan"):
        assert alan in m, (
            f"`DurumSozlugu.tsx` `{alan}` alanını hiç okumuyor — yüzey kanonik satırı basmıyor "
            "demektir (sözleşme: tasarım §9.1 satır şeması).")


def test_b_ui_ham_kelime_cevirmez():
    """İKİNCİ SÖZLÜK YASAĞI: kelime backend'de üretilir, pano yalnız basar."""
    m = _oku(TSX)
    for ham in HAM_KELIMELER:
        assert f'"{ham}"' not in m and f"'{ham}'" not in m, (
            f"ham kelime UI'da çevriliyor: {ham}. Kelime TEK KAYNAKTA üretilir "
            "(`PANO_KELIME`, `meridian/durum_sozlugu.py`); panodaki ikinci tablo sessizce ayrışır (A8 hükmü).")


def test_c_olculemedi_sifir_degil_kalibi():
    """Ölçülemeyen sayı `null`dır ve ekranda 0 diye OKUNAMAZ."""
    assert "ÖLÇÜLEMEDİ (0 DEĞİL)" in _soy(_oku(TSX)), (
        "uydurma yasağının ekran kalıbı KODDA yok — `n === null` boş hücreye düşerse sıfırdan "
        "ayırt edilemez (intraday atlama ailesinin bütün değeri bu ayrımdır). Şerhte geçmesi "
        "SAYILMAZ: çizilmeyen kalıp yazılmamış kalıptır.")


def test_d_tip_sozlesmesi_ve_durak():
    """Uç gövdesi TİPLİ ve bölüm KAYITLI — ikisi de olmadan yüzey ekrana çıkmaz.

    ALAN ADLARI `?:` İLE YAZILIR ve bu `uctipleri.ts`in kendi sözleşmesidir ("uçlar bir alanı
    ÖLÇEMEDİĞİNDE onu HİÇ YAZMIYOR"), bu yüzden çivi `satirlar:` dizgesini değil `satirlar` +
    isteğe bağlılık işaretini arar."""
    t = _oku(TIPLER)
    assert re.search(r"durum_sozlugu\??:\s*DurumSozluguGovdesi", t), (
        "`TeshisGovdesi` `durum_sozlugu` alanını taşımıyor — pano gövdeyi tipsiz okuyamaz.")
    for alan in ("satirlar", "kelime", "aile", "aileler"):
        assert re.search(rf"\b{alan}\??:", t), f"`uctipleri.ts` `{alan}` alanını tiplemiyor"

    a = _oku(KAYIT)
    assert "Durum sözlüğü" in a and "DurumSozlugu" in a, (
        "`alanlar.ts`te durak kaydı yok — kenar çubuğu ve ⌘K paleti bu bölüme bağ ÜRETMEZ.")
    assert 'kimlik: "durum-sozlugu"' in a, (
        "durak kimliği `durum-sozlugu` değil — derin bağ çapası (`bolum-durum-sozlugu`) "
        "v288 paritesinde bu kimliğe bağlı.")


def test_e_yuzey_yonlendiriciye_kayitli():
    """BİLEŞEN VAR ≠ EKRANDA VAR: yönlendirici onu çizmiyorsa dosya ölü bayttır."""
    y = _oku(YONLENDIRICI)
    assert 'from "./sistem/DurumSozlugu"' in y, "`SistemSagligiYuzey.tsx` yüzeyi import etmiyor"
    assert re.search(r"<DurumSozlugu\b", y), (
        "`DurumSozlugu` hiç çizilmiyor — kayıtlı durak boş bir çapaya kaydırırdı.")
    assert 'kimlik="durum-sozlugu"' in _oku(TSX), (
        "`BolumKart` çapası yok — derin bağ sayfayı açar ama bölüme kaydırmaz (v288 sınıfı).")


def test_f_eski_appjs_dokunulmadi():
    """İkincil UI (`/eski`) bu turda DOKUNULMAZ: F8 kartı yerinde kalır (v261/v271 yeşil)."""
    m = (KOK / "meridian" / "web" / "app.js").read_text(encoding="utf-8")
    assert "f8SozlukSatiri" in m and "bekciDurumlari" in m, (
        "eski panonun F8 kartı kaybolmuş — emekliliği AYRI bir kalem (EDG-089 penceresi sonrası).")
