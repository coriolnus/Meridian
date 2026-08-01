"""olcum_araclari.py — ÖLÇÜM ŞABLONLARININ ORTAK YARDIMCILARI (WP-M, 2026-08-01).

NEDEN VAR — KIYAS KİRLENMESİ (EAP'nin yan bulgusu, kart-adayı). Olay-çalışması ölçümlerinde
"olayın getirisi" tek başına bir bulgu değildir; taban (aynı gün evrenin geri kalanı) ondan
çıkarılır. EAP ölçümünde bu tabanın KENDİSİ kirliydi: olay penceresinin içindeki bir günde
evrenin %64-74'ü de KENDİ olay penceresindeydi. Yani "olay - evren medyanı" farkı, olayı olayla
kıyaslıyordu ve fark sistematik olarak SIKIŞIYORDU. Hiçbir test kırılmaz, hiçbir istisna atılmaz;
yalnız her etki olduğundan küçük görünür — bu deponun en sevmediği hata sınıfı ("hata değil,
miktar değişimi").

NE YAPAR. `temiz_taban` tabandan olay-penceresi-İÇİ satırları düşürür ve KAÇ TANESİNİ düşürdüğünü
raporlar. Kirlilik oranı çıktının birinci sınıf alanıdır: temizlenmiş bir taban "temiz" diye
sunulup ne kadar kirli olduğu söylenmezse, okuyucu düzeltmenin büyüklüğünü göremez.

NE YAPMAZ — GEÇMİŞE DÖNÜK DÜZELTME YOK. Bu modül İLERİYE dönük bir standarttır. Bugün
`research/`de duran ölçüm betikleri TARİHE aittir ve kendi kartlarının hükmünü taşırlar; onları
bu fonksiyonla yeniden yazmak, hükümleri sessizce değiştirmek olurdu. Kullanım kuralı
`docs/olcum_standartlari.md`de yazılıdır.

SAF YAPRAK: hiçbir `meridian` modülünü import etmez, hiçbir dosyaya yazmaz, ağa çıkmaz. Ölçüm
şablonlarının bir kum havuzundan da çağırabilmesi için böyle.
"""
from __future__ import annotations

import datetime as _dt

# Gün birimi ADIYLA raporlanır — çıkarım yapılır ama gizlenmez. "±5 gün" bir takvim penceresi mi
# yoksa 5 BAR mı, ölçümün hükmünü değiştirir (T+1 ritim kusurunun sınıfı: "zaman varsayımı kodda
# örtük"). Fonksiyon girdiden hangisini gördüğünü çıkarır ve çıktıda söyler.
BIRIM_TAKVIM = "takvim gunu"
BIRIM_SIRA = "sira/bar indeksi"


def _gun_ordinali(g) -> tuple[int, str]:
    """(sıra_numarası, birim). ISO metin / date / datetime → takvim ordinali; int → sıra indeksi.

    TİP KARIŞIMI HATA VERİR, SESSİZCE ÇEVRİLMEZ: aynı seride hem `2026-01-05` hem `12` varsa
    pencere aritmetiği iki farklı birimi toplar ve sonuç HİÇBİR YERDE yanlış görünmez. Bu
    fonksiyonun var oluş sebebi tam olarak o sınıftır."""
    if isinstance(g, bool):
        raise TypeError(f"gün olarak bool geldi: {g!r}")
    if isinstance(g, int):
        return int(g), BIRIM_SIRA
    if isinstance(g, _dt.datetime):
        return g.date().toordinal(), BIRIM_TAKVIM
    if isinstance(g, _dt.date):
        return g.toordinal(), BIRIM_TAKVIM
    if isinstance(g, str):
        return _dt.date.fromisoformat(g[:10]).toordinal(), BIRIM_TAKVIM
    raise TypeError(f"çözülemeyen gün tipi: {type(g).__name__} ({g!r})")


def _pencere(pencere) -> tuple[int, int]:
    """(once, sonra) — ikisi de POZİTİF genişlik. `pencere=5` ⇒ (5, 5); `(1, 10)` ⇒ (1, 10).

    `(-1, 10)` gibi işaretli yazımlar da kabul edilir ve mutlak değere alınır: olay-çalışması
    yazınında pencere `[-1, +10]` diye yazılır, ölçüm şablonunun o gösterimi elle çevirmek zorunda
    kalması gereksiz bir hata kapısıdır."""
    if isinstance(pencere, (list, tuple)):
        if len(pencere) != 2:
            raise ValueError(f"pencere iki elemanlı olmalı, {len(pencere)} geldi")
        once, sonra = pencere
    else:
        once = sonra = pencere
    once, sonra = abs(int(once)), abs(int(sonra))
    return once, sonra


def _satirlar(getiriler):
    """Girdi normalleştirme → (kimlik, gün, değer) üçlüleri.

    Kabul edilen üç şekil (ölçüm şablonlarında bugün üçü de görülüyor):
      * {kimlik: {gün: değer}}              — sembol × gün matrisi
      * [(kimlik, gün, değer), ...]         — uzun biçim
      * [{"kimlik":…, "gun":…, "deger":…}]  — sözlük satırları (eşanlamlılar: sembol/ticker,
                                              tarih/date/day, getiri/ret/value)
    """
    if isinstance(getiriler, dict):
        for kimlik, seri in getiriler.items():
            if not isinstance(seri, dict):
                raise TypeError(f"{kimlik!r} için {{gün: değer}} sözlüğü bekleniyordu, "
                                f"{type(seri).__name__} geldi")
            for gun, deger in seri.items():
                yield kimlik, gun, deger
        return
    for satir in getiriler:
        if isinstance(satir, dict):
            kimlik = _ilk(satir, ("kimlik", "sembol", "ticker", "symbol"))
            gun = _ilk(satir, ("gun", "tarih", "date", "day"))
            deger = _ilk(satir, ("deger", "getiri", "ret", "value", "r"))
            yield kimlik, gun, deger
        else:
            kimlik, gun, deger = satir
            yield kimlik, gun, deger


def _ilk(d: dict, adlar: tuple):
    for a in adlar:
        if a in d:
            return d[a]
    raise KeyError(f"satırda {adlar} adlarından hiçbiri yok: {sorted(d)}")


def temiz_taban(getiriler, olay_gunleri, pencere) -> dict:
    """OLAY-PENCERESİ-DIŞI taban serisi + kirlilik oranı raporu.

    Parametreler
    ------------
    getiriler   : taban serisinin ham satırları — `_satirlar`ın kabul ettiği üç şekilden biri.
    olay_gunleri: {kimlik: [olay günü, ...]}. Listede olmayan bir kimlik KİRLETİLMEMİŞ sayılır ve
                  bu çıktıda `n_olaysiz_kimlik` ile GÖRÜNÜR — "olay listesi eksik" ile "o sembolde
                  olay yok" aynı şey değildir ve ikisini ayırmak okuyucunun hakkıdır.
    pencere     : `5` ya da `(once, sonra)`. Birim, GÜNLERİN KENDİ birimidir (takvim tarihi
                  verirsen takvim günü, bar indeksi verirsen bar) ve çıktıda `gun_birimi` ile
                  adıyla söylenir.

    Dönüş
    -----
    {"taban": [(kimlik, gün, değer), ...],     # olay-penceresi DIŞI satırlar (giriş sırası korunur)
     "degerler": [değer, ...],                 # aynı satırların yalnız değerleri (kolay tüketim)
     "n_toplam", "n_temiz", "n_kirli", "n_cozulemeyen",
     "kirlilik_orani",                         # n_kirli / n_toplam — n_toplam=0 ise None
     "pencere", "gun_birimi", "n_kimlik", "n_olay", "n_olaysiz_kimlik",
     "beyan", "uyari"}

    İKİ DÜRÜSTLÜK KURALI:
      (1) HİÇ SATIR YOKSA `kirlilik_orani` **None**'dır, 0.0 DEĞİL. Ölçülmemiş bir temizlik "temiz"
          diye raporlanamaz (UYDURMA YASAĞI).
      (2) GÜNÜ ÇÖZÜLEMEYEN satır sessizce düşmez: `n_cozulemeyen` sayılır ve `uyari` metnine
          girer. Sessiz düşürme, tam olarak bu modülün önlemek için var olduğu şeydir (YASA 4).
    """
    once, sonra = _pencere(pencere)

    # olay günlerini ordinale çevir (kimlik başına sıralı liste)
    olaylar: dict = {}
    birimler: set = set()
    n_olay = 0
    for kimlik, gunler in (olay_gunleri or {}).items():
        ords = []
        for g in gunler or ():
            o, b = _gun_ordinali(g)
            birimler.add(b)
            ords.append(o)
        olaylar[kimlik] = sorted(ords)
        n_olay += len(ords)

    taban, degerler = [], []
    n_toplam = n_kirli = n_cozulemeyen = 0
    gorulen_kimlik: set = set()
    olaysiz: set = set()
    for kimlik, gun, deger in _satirlar(getiriler):
        n_toplam += 1
        gorulen_kimlik.add(kimlik)
        try:
            o, b = _gun_ordinali(gun)
        except (TypeError, ValueError):  # sessiz-yutma: günü çözülemeyen satır SAYILIR (n_cozulemeyen) ve `uyari` metnine girer — kayıp görünür, üstelik bu modül saf yaprak olduğu için obs kanalı yok
            n_cozulemeyen += 1
            continue
        birimler.add(b)
        kimlik_olaylari = olaylar.get(kimlik)
        if kimlik_olaylari is None:
            olaysiz.add(kimlik)
            kimlik_olaylari = ()
        if any(-once <= (o - oe) <= sonra for oe in kimlik_olaylari):
            n_kirli += 1
            continue
        taban.append((kimlik, gun, deger))
        degerler.append(deger)

    if len(birimler) > 1:
        raise ValueError(f"gün birimi KARIŞIK ({sorted(birimler)}) — takvim tarihi ile sıra "
                         f"indeksi aynı seride toplanamaz; pencere aritmetiği iki farklı birimi "
                         f"toplar ve sonuç hiçbir yerde yanlış görünmez")

    n_temiz = len(taban)
    olculebilir = n_toplam - n_cozulemeyen
    kirlilik = round(n_kirli / olculebilir, 4) if olculebilir else None
    uyarilar = []
    if n_cozulemeyen:
        uyarilar.append(f"{n_cozulemeyen} satırın günü çözülemedi ve tabandan düştü "
                        f"(kirlilik oranının paydası {olculebilir})")
    if kirlilik is not None and kirlilik >= 0.5:
        uyarilar.append(f"taban satırlarının %{kirlilik * 100:.0f}'i olay penceresi İÇİNDEYDİ — "
                        f"temizlenmemiş bir kıyas bu ölçümde etkiyi ciddi biçimde SIKIŞTIRIRDI")
    if olculebilir and n_temiz == 0:
        uyarilar.append("TEMİZ SATIR KALMADI — bu pencerede olay-dışı taban YOK; kıyas kurulamaz")

    return {
        "taban": taban, "degerler": degerler,
        "n_toplam": n_toplam, "n_temiz": n_temiz, "n_kirli": n_kirli,
        "n_cozulemeyen": n_cozulemeyen, "n_olculebilir": olculebilir,
        "kirlilik_orani": kirlilik,
        "pencere": {"once": once, "sonra": sonra},
        "gun_birimi": (next(iter(birimler)) if len(birimler) == 1 else None),
        "n_kimlik": len(gorulen_kimlik), "n_olay": n_olay,
        "n_olaysiz_kimlik": len(olaysiz),
        "beyan": ("taban = olay-penceresi DIŞI satırlar. Pencere kapsayıcıdır: olay gününün "
                  "kendisi ve [gün−once, gün+sonra] aralığının tamamı KİRLİ sayılır. Olay listesi "
                  "boş olan kimliklerin satırları temiz sayılır (n_olaysiz_kimlik ile görünür). "
                  "kirlilik_orani = n_kirli / n_olculebilir; hiç ölçülebilir satır yoksa None "
                  "(0.0 değil — ölçülmemiş temizlik 'temiz' diye raporlanamaz)"),
        "uyari": (" · ".join(uyarilar) if uyarilar else None),
    }
