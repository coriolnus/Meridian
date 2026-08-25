"""KRİZ KOLLARI — GERİ ALINAMAZ İCRANIN ARAYÜZ KAPILARI · v297 (2026-08-25)

NEDEN STATİK ÇİVİ. Bu dört kol (HALT · Cancel-Open · Flatten · Halt-Learning) canlı
sisteme yazar ve üçü GERİ ALINAMAZ. Davranışları bir tarayıcı testiyle ölçmek en doğrusu
olurdu; o düzenek bu depoda yok. Ama korunması gereken şeylerin ÇOĞU kaynaktan
okunabilir: iki adımın varlığı, jeton kapısı, ve "200 = oldu" varsayımının kurulmamış
olması. Ölçülebileni ölçmemek, ölçülemediği için değil bakılmadığı için kaçırmaktır.

KORUNAN DÖRT ŞEY, hepsi bir arıza sınıfının karşılığı:
  (a) KOLUN EVİ SABİT — üst bar, yönlendirilen içeriğin DIŞINDA. Eski panoda şerhi var:
      "HALT'ın SABİT bir evi olmak zorunda (kas hafızası)". Sayfa değişince yeniden
      monte edilen bir kol, acil anda aranan koldur.
  (b) TEK TIKLA GÖNDERİM YOK — her kol iki adımlı. "Listeyi temizle" refleksiyle
      basılabilecek bir düğme, geri alınamaz icranın en kötü eşleşmesidir.
  (c) FLATTEN JETONSUZ GÖNDERİLEMEZ — ucun kendi sözleşmesi (`alpaca.CLOSE_ALL_CONFIRM`)
      arayüzde de bir kapıdır; jeton yazılmadan son düğme kilitli.
  (d) "HTTP 200 = OLDU" KURULMAZ — bu ailede `cancel_open` ve `close_all` adaptör
      arızasını 200 İÇİNDE `{ok: false}` olarak taşıyor. Hüküm gövdeden alan alan okunur.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

KOK = Path(__file__).resolve().parent.parent
KABUK = KOK / "ui" / "src" / "pano" / "kabuk"

pytestmark = pytest.mark.skipif(not KABUK.is_dir(), reason="ui/ yok — pano kaynağı bu ağaçta değil")


def _oku(ad: str) -> str:
    p = KABUK / ad
    assert p.exists(), f"{ad} yok — kriz kolları kaldırılmış ya da taşınmış olabilir"
    return p.read_text(encoding="utf-8")


def _soy(metin: str) -> str:
    """Yorumları at. Bu depoda aynı ölçüm hatası üç kez yapıldı: bir kuralın YORUMDA
    geçmesi onun UYGULANDIĞI anlamına gelmiyor."""
    metin = re.sub(r"/\*.*?\*/", "", metin, flags=re.S)
    metin = re.sub(r"^\s*//.*$", "", metin, flags=re.M)
    return re.sub(r"\{/\*.*?\*/\}", "", metin, flags=re.S)


def test_a_kolun_evi_UST_BARDA_ve_sayfadan_bagimsiz():
    """Kol tetikleyicisi `Ustbar`da monte olmalı — yönlendirilen gövdenin içinde DEĞİL."""
    ust = _soy(_oku("Ustbar.tsx"))
    # SÖZCÜK SINIRI ŞART — mutasyon sondası bunu ÖLÇTÜ ve ilk sürüm KAÇIRDI:
    # `"KrizKollari" in ust` testi `KrizKollariYOK` yazıldığında da GEÇİYORDU (alt dizge).
    # JSX etiketinin KENDİSİ aranıyor: import edilip kullanılmayan bir bileşen monte değildir.
    assert re.search(r"<KrizKollari\b", ust), (
        "üst bar kriz kollarını monte etmiyor — kol bir yüzeyin içine düşmüş olabilir. "
        "Eski panonun şerhi: HALT'ın SABİT bir evi olmak ZORUNDA (kas hafızası).")
    yuzeyler = KOK / "ui" / "src" / "pano" / "yuzeyler"
    if yuzeyler.is_dir():
        sizanlar = [p.relative_to(KOK).as_posix() for p in yuzeyler.rglob("*.tsx")
                    if "KrizKollari" in _soy(p.read_text(encoding="utf-8"))]
        assert not sizanlar, (
            f"kriz kolları bir YÜZEYİN içinde de monte edilmiş: {sizanlar} — iki ev, iki kas "
            "hafızası demektir ve acil anda hangisinin canlı olduğu bilinmez.")


def test_b_hicbir_kol_TEK_TIKLA_gonderilmiyor():
    """İki adım: birinci tık NİYET alır, ikinci tık gönderir."""
    s = _soy(_oku("KrizKollari.tsx"))
    assert "setAsama" in s and "Asama" in s, (
        "kolların aşama durumu yok — tek tıkla gönderim kurulmuş olabilir. "
        "İki adım bu ailede bir üslup değil bir kapıdır.")
    # Gönderim yolu aşamaya BAĞLI olmalı: "hazir" aşamasında gönderen bir dal olmamalı.
    assert '"hazir"' in s, "aşama sözlüğünde başlangıç hâli (`hazir`) yok — akış izlenemiyor"


def test_c_flatten_JETONSUZ_gonderilemez():
    """Son düğme jeton doğru yazılana kadar kilitli olmalı."""
    s = _soy(_oku("FlattenKapisi.tsx"))
    assert "jetonTamam" in s, "Flatten'ın jeton kapısı yok"
    m = re.search(r"const\s+jetonTamam\s*=\s*([^;]+);", s)
    assert m, "jeton karşılaştırması okunamadı — kapı kaynaktan doğrulanamıyor"
    assert "FLATTEN_JETON" in m.group(1), (
        "jeton, ucun kendi sabitiyle (`FLATTEN_JETON`) karşılaştırılmıyor — arayüzde ikinci "
        "bir jeton tanımı, uç sözleşmesi değişince SESSİZCE ayrışır")
    # Gönder düğmesi `!jetonTamam` iken devre dışı olmalı.
    assert re.search(r"disabled=\{[^}]*!jetonTamam", s), (
        "Flatten'ın gönder düğmesi jeton yokken KİLİTLİ DEĞİL — kapı görünüyor ama tutmuyor")


def test_d_HTTP_200_basari_sayilmiyor():
    """`{ok: false}` ve `dry_run` 200 içinde gelebilir; hüküm gövdeden okunmalı."""
    s = _soy(_oku("krizUclari.ts"))
    assert "kolSonucu" in s, "sonuç okuyucu (`kolSonucu`) yok — hüküm nereden veriliyor?"
    # SAYIYLA ÖLÇÜLÜYOR, VARLIKLA DEĞİL — mutasyon sondası ilk sürümü ÇÜRÜTTÜ: tek bir
    # başarısızlık dalını silmek "var" iddiasını bozmuyordu, çünkü ötekiler duruyordu.
    # TABAN BUGÜNÜN ÖLÇÜMÜ (7), tahmini bir alt sınır DEĞİL — ve bu ayrım mutasyon sondasıyla
    # kazanıldı: taban 3 iken yedi daldan birini silmek çiviyi HİÇ düşürmüyordu, yani çivi
    # "hiç dal yok" hâlini yakalıyor ama GERİLEMEYİ kaçırıyordu. Cırcır mantığı: dal EKLEMEK
    # serbest (sayı artar, çivi geçer), dal SİLMEK gerekçe ister (sayı düşer, çivi düşer).
    # SÖZCÜK SINIRI: `basarili: falseXYZ` gibi bir kalıntı dal SAYILMAMALI (mutasyon
    # sondası bu tuzağı da ölçtü — düz `count` bozulmuş bir dalı sağlam sayıyordu).
    dal = len(re.findall(r"basarili:\s*false\b", s))
    assert dal >= 7, (
        f"sonuç okuyucusunda yalnız {dal} BAŞARISIZ dalı var (taban 7) — bir kolun arıza yolu "
        "silinmiş olabilir ve o kolda 200 dönen her yanıt başarı sayılır. Bu ailede "
        "`cancel_open`/`close_all` adaptör arızasını 200 İÇİNDE taşıyor.")
    assert "dry_run" in s, (
        "`dry_run` okunmuyor — jetonlu çağrıya kuru-koşu yanıtı dönerse (jeton uca ulaşmadıysa) "
        "hiçbir şey kapanmamıştır ve bu BAŞARI sayılamaz")


def test_e_geri_alma_yolu_ayni_yerde():
    """Çekilen kolun geri alınması aynı yüzeyde olmalı — HALT bir karardır, çıkmaz sokak değil."""
    s = _soy(_oku("KrizKollari.tsx")) + _soy(_oku("krizUclari.ts"))
    assert "/api/resume" in s, (
        "geri alma ucu (`/api/resume`) arayüzde yok — operatör durdurduğu sistemi aynı yerden "
        "devam ettiremiyor demektir")
