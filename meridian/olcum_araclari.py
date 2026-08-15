"""olcum_araclari.py — ölçüm şablonlarının ORTAK YARDIMCILARI: temiz taban, blok bootstrap, küçültme, damga.

ARAÇLAR (hepsi İLERİYE dönük standart, hiçbiri hüküm vermez):
  * `temiz_taban`        — olay-penceresi DIŞI havuz tabanı + kirlilik oranı
  * `olay_disi_kiyas`    — GÜN BAZINDA temiz evren tabanı + taban-fazlası
  * `blok_bootstrap_ci`  — örtüşen-blok (moving block) güven aralığı (BOOTSTRAP_TOHUM/BOOTSTRAP_N)
  * `eb_kucult`          — empirik-Bayes/James-Stein küçültme (SE tabanlı; EB_MIN_HUCRE altı yok)
  * `kod_surumu_damgasi` — rapor hangi kod hâliyle üretildi (git HEAD + SURUM/ARAC_SURUMLERI)

NEDEN VAR — KIYAS KİRLENMESİ. Olay-çalışması ölçümlerinde "olayın getirisi" tek başına bulgu
değildir; taban (aynı gün evrenin geri kalanı) ondan çıkarılır. Ölçülen vaka: tabanın KENDİSİ
kirliydi — olay penceresi içindeki bir günde evrenin %64-74'ü de kendi olay penceresindeydi, yani
"olay − evren medyanı" farkı olayı olayla kıyaslıyor ve sistematik SIKIŞIYORDU. Test kırılmaz,
istisna atılmaz; her etki olduğundan küçük görünür ("hata değil, miktar değişimi" sınıfı).
`temiz_taban` olay-penceresi-İÇİ satırları düşürür ve KAÇINI düşürdüğünü birinci sınıf alan olarak
raporlar. Gün birimi (takvim günü mü, bar indeksi mi) çıkarımla bulunur ama GİZLENMEZ; tip karışımı
sessizce çevrilmez, hata verir.

DEĞİŞMEZLER: GEÇMİŞE DÖNÜK DÜZELTME YOK — `research/`deki tarihi betikler kendi kartlarının hükmünü
taşır, buradaki araçlarla yeniden yazılmaz; bir aracın eklenmesi eski hiçbir kart hükmünü
geçersizleştirmez, tazelemek yeni ön-kayıt kartı ister (kural `docs/olcum_standartlari.md`).
Ölçülemeyen uydurulmaz: eşik altı girdide lo/hi None + neden.

SAF YAPRAK: hiçbir `meridian` modülünü import etmez, hiçbir dosyaya yazmaz, ağa çıkmaz (kum
havuzundan da çağrılabilsin diye). TEK BEYANLI İSTİSNA: `kod_surumu_damgasi` YALNIZ-OKUMA bir
`git` alt süreci koşar (yazmaz; git yoksa None + neden döner).
"""
from __future__ import annotations

import datetime as _dt

# ARAÇ SÜRÜM LİSTESİ — raporlara damga olarak basılır (`kod_surumu_damgasi`). NEDEN: "bu rapor
# hangi ölçüm aracıyla üretildi?" sorusunun cevabı bugüne kadar hiçbir raporun İÇİNDE yazmıyordu;
# bir aracın davranışı değiştiğinde eski raporlar sessizce YENİ aracın davranışıyla okunuyordu.
# Sürüm ARTAR: bir aracın çıktısı/matematiği değişirse buradaki sürümü de değişir (aynı sürüm
# adıyla iki farklı davranış, damgayı damga olmaktan çıkarır).
SURUM = "2026-08-02"
ARAC_SURUMLERI = {
    "temiz_taban": "1.0",
    "olay_disi_kiyas": "1.0",
    "blok_bootstrap_ci": "1.0",
    "eb_kucult": "1.0",
}

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


def _olaylari_ordinalle(olay_gunleri) -> tuple[dict, set, int]:
    """{kimlik: [gün]} → ({kimlik: [ordinal, ...]}, görülen birimler, toplam olay sayısı).

    TEK TANIM, İKİ TÜKETİCİ (`temiz_taban` ve `olay_disi_kiyas`). İkinci bir yerde olay ordinali
    kurmak, aynı olay listesinden iki farklı kirlilik tanımı üretebilirdi ve fark ancak iki çıktıyı
    yan yana koyan biri tarafından görülürdü — bu deponun `_ic_hucreleri` dersi."""
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
    return olaylar, birimler, n_olay


def _birim_kontrolu(birimler: set):
    """Karışık gün birimi ÖLÜMCÜLDÜR — sessizce toplanamaz (bkz. `_gun_ordinali`)."""
    if len(birimler) > 1:
        raise ValueError(f"gün birimi KARIŞIK ({sorted(birimler)}) — takvim tarihi ile sıra "
                         f"indeksi aynı seride toplanamaz; pencere aritmetiği iki farklı birimi "
                         f"toplar ve sonuç hiçbir yerde yanlış görünmez")


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
    olaylar, birimler, n_olay = _olaylari_ordinalle(olay_gunleri)

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

    _birim_kontrolu(birimler)

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


# ==================================================================================================
# OLAY-DIŞI KIYAS — `temiz_taban`ın GÜN BAZLI ikizi
# ==================================================================================================
# NEDEN AYRI BİR FONKSİYON. `temiz_taban` tek bir HAVUZ döndürür: "olay penceresine değmemiş tüm
# satırlar". Ders #3 ise tabanı AYNI GÜNÜN evreninde ister — çünkü havuz tabanı, olay günlerinin
# piyasa-genelinde nasıl bir gün olduğunu (rejim, volatilite, endeks hareketi) düzeltmez. İki taban
# iki farklı soruya cevaptır ve ikisi de gereklidir:
#   * havuz tabanı → "bu kurulum genel olarak evrenden farklı mı?"
#   * gün tabanı   → "olay günü, O GÜNÜN evreninden farklı mı?" (olay-çalışması sorusu)
# `temiz_taban` KIRILMADI: imzası, alanları ve sayıları bit-bit aynı kaldı. Bu, ek bir parametre
# yerine yeni bir yardımcı olarak indi — çünkü dönüş SÖZLEŞMESİ farklı (satır listesi değil, gün ×
# taban tablosu) ve mevcut okuyucuya opsiyonel bir alan eklemek, aynı ada iki şekil yüklerdi.
#
# SIKIŞMA ÖLÇÜSÜ RAPORUN İÇİNDE. Fonksiyon aynı hedefleri BİR DE kirli tabanla (o günün TÜM
# satırları, olay-pencereli olanlar dahil) kıyaslar ve farkı `sikisma` olarak yazar. EAP'nin yan
# bulgusunun tamamı buydu: kimse yanlış bir sayı görmüyordu, herkes DOĞRU ama SIKIŞMIŞ bir sayı
# görüyordu. Düzeltmenin büyüklüğü raporda durmazsa, okuyucu düzeltmenin gerekli olup olmadığını
# değerlendiremez.
_OZETLER = ("medyan", "ortalama")


def _medyan(vals: list) -> float:
    s = sorted(vals)
    n = len(s)
    orta = n // 2
    return float(s[orta]) if n % 2 else (float(s[orta - 1]) + float(s[orta])) / 2.0


def _ozetle(vals: list, ozet: str) -> float:
    return _medyan(vals) if ozet == "medyan" else (sum(float(v) for v in vals) / len(vals))


def olay_disi_kiyas(getiriler, olay_gunleri, pencere, hedefler=None,
                    ozet: str = "medyan", min_taban: int = 5) -> dict:
    """GÜN BAZINDA olay-penceresi-dışı evren tabanı + her hedef satırın TABAN-FAZLASI.

    Parametreler
    ------------
    getiriler   : EVREN satırları (`_satirlar`ın üç şeklinden biri). Taban BURADAN kurulur.
    olay_gunleri: {kimlik: [olay günü, ...]} — `temiz_taban`daki sözleşmenin aynısı.
    pencere     : `5` ya da `(once, sonra)`. Birim GİRDİNİN birimidir (`gun_birimi` ile raporlanır).
    hedefler    : kıyaslanacak satırlar. VARSAYILAN (None) = evrenin KİRLİ satırları, yani
                  olay-penceresi İÇİ satırlar — olay-çalışmasının doğal hedefi. Açıkça verilirse
                  hedefler evrenin içinde olmak zorunda DEĞİLDİR (ör. yalnız olay GÜNÜ satırları).
    ozet        : "medyan" (varsayılan) | "ortalama". Medyan varsayılandır çünkü günlük kesitte tek
                  bir kuyruk sembolü ortalamayı taşıyabilir. Tanınmayan değer `ValueError`dır.
    min_taban   : bir günün tabanının SAYILMASI için gereken en az temiz satır. Altında kalan gün
                  ATLANIR ve `n_taban_yok` ile GÖRÜNÜR — 2 sembolle kurulmuş bir "evren medyanı",
                  kirli bir tabandan daha kötüdür (Ders #4'ün son cümlesi).

    Dönüş (hepsi birinci sınıf alan)
    --------------------------------
    {"kiyaslar": [{"kimlik","gun","deger","taban","fazla","kirli_taban","n_taban"}, ...],
     "fazlalar": [...], "fazla_ozeti": {"n","ortalama","medyan"} | None,
     "gun_tabani": {gün: {"n_temiz","n_kirli","kirlilik_orani","taban","kirli_taban"}},
     "sikisma": {"temiz","kirli","fark","aciklama"} | None,
     "n_hedef","n_kiyaslanan","n_taban_yok","n_gun","n_cozulemeyen","n_deger_cozulemeyen",
     "kirlilik_orani","pencere","gun_birimi","ozet","min_taban","beyan","uyari"}

    DÖRT DÜRÜSTLÜK KURALI:
      (1) KENDİ SATIRI KENDİ TABANINDA OLAMAZ: hedefin kimliği o günün tabanından düşürülür. Aksi
          hâlde ölçüm kendini kendine kıyaslar ve etkiyi 1/N kadar SİSTEMATİK olarak küçültür.
      (2) TABANI OLMAYAN HEDEF ATILMAZ, SAYILIR (`n_taban_yok`) — sessizce düşen hedef, seçim
          yanlılığıdır: tabanı zayıf günler tipik olarak İNCE GÜNLERDİR ve rastgele değildir.
      (3) `kirlilik_orani` hiç ölçülebilir satır yoksa **None**'dır (0.0 değil).
      (4) `sikisma` yalnız BİLGİDİR: kirli taban asla hükme girmez, yalnız temizliğin ne kadar
          fark ettirdiğini gösterir.
    """
    if ozet not in _OZETLER:
        raise ValueError(f"ozet {ozet!r} tanınmıyor — {_OZETLER} bekleniyor "
                         f"(sessiz varsayılan seçmek, ölçütü ölçümden sonra seçmek olurdu)")
    min_taban = max(1, int(min_taban))   # 0 taban "boş listenin medyanı"dır; sayı değil, çökmedir
    once, sonra = _pencere(pencere)
    olaylar, birimler, n_olay = _olaylari_ordinalle(olay_gunleri)

    def _kirli_mi(kimlik, o) -> bool:
        return any(-once <= (o - oe) <= sonra for oe in olaylar.get(kimlik) or ())

    # ---- 1) evreni gün gün sınıflandır ----------------------------------------------------------
    gunler: dict = {}                       # ordinal → {"temiz": [(kimlik, v)], "kirli": [...]}
    gun_gosterim: dict = {}                 # ordinal → ilk görülen gün gösterimi (rapor anahtarı)
    n_toplam = n_kirli = n_cozulemeyen = n_deger = 0
    for kimlik, gun, deger in _satirlar(getiriler):
        n_toplam += 1
        try:
            o, b = _gun_ordinali(gun)
            v = float(deger)
        except (TypeError, ValueError):  # sessiz-yutma: günü ya da değeri çözülemeyen satır SAYILIR (n_cozulemeyen) ve `uyari` metnine girer — bu modül saf yaprak, obs kanalı yok
            n_cozulemeyen += 1
            continue
        birimler.add(b)
        gun_gosterim.setdefault(o, gun)
        kova = gunler.setdefault(o, {"temiz": [], "kirli": []})
        if _kirli_mi(kimlik, o):
            n_kirli += 1
            kova["kirli"].append((kimlik, v))
        else:
            kova["temiz"].append((kimlik, v))
    _birim_kontrolu(birimler)

    # ---- 2) hedefler ---------------------------------------------------------------------------
    if hedefler is None:
        hedef_satirlari = [(kimlik, gun_gosterim[o], v, o)
                           for o, kova in gunler.items() for kimlik, v in kova["kirli"]]
        hedef_kaynagi = "varsayılan: evrenin olay-penceresi İÇİ satırları"
    else:
        hedef_satirlari = []
        for kimlik, gun, deger in _satirlar(hedefler):
            try:
                o, b = _gun_ordinali(gun)
                v = float(deger)
            except (TypeError, ValueError):  # sessiz-yutma: çözülemeyen HEDEF satırı n_deger_cozulemeyen'e yazılır ve uyarıya girer — atılan hedef görünmez kalamaz
                n_deger += 1
                continue
            birimler.add(b)
            hedef_satirlari.append((kimlik, gun, v, o))
        _birim_kontrolu(birimler)
        hedef_kaynagi = "açıkça verildi (hedefler parametresi)"

    # ---- 3) kıyas ------------------------------------------------------------------------------
    kiyaslar, fazlalar, kirli_fazlalar = [], [], []
    n_taban_yok = 0
    tabani_zayif_gunler: set = set()
    for kimlik, gun, v, o in hedef_satirlari:
        kova = gunler.get(o) or {"temiz": [], "kirli": []}
        temiz_v = [x for k, x in kova["temiz"] if k != kimlik]          # KURAL (1): kendini dışla
        if len(temiz_v) < min_taban:
            n_taban_yok += 1
            tabani_zayif_gunler.add(o)
            continue
        taban = _ozetle(temiz_v, ozet)
        tum_v = temiz_v + [x for k, x in kova["kirli"] if k != kimlik]  # KİRLİ ikiz (yalnız bilgi)
        kirli_taban = _ozetle(tum_v, ozet) if tum_v else None
        kiyaslar.append({"kimlik": kimlik, "gun": gun, "deger": v, "taban": taban,
                         "fazla": v - taban, "n_taban": len(temiz_v),
                         "kirli_taban": kirli_taban,
                         "kirli_fazla": (None if kirli_taban is None else v - kirli_taban)})
        fazlalar.append(v - taban)
        if kirli_taban is not None:
            kirli_fazlalar.append(v - kirli_taban)

    # ---- 4) rapor ------------------------------------------------------------------------------
    gun_tabani = {}
    for o, kova in gunler.items():
        nt, nk = len(kova["temiz"]), len(kova["kirli"])
        gun_tabani[str(gun_gosterim[o])] = {
            "n_temiz": nt, "n_kirli": nk,
            "kirlilik_orani": (round(nk / (nt + nk), 4) if (nt + nk) else None),
            "taban": (_ozetle([x for _, x in kova["temiz"]], ozet) if nt else None),
            "kirli_taban": (_ozetle([x for _, x in kova["temiz"] + kova["kirli"]], ozet)
                            if (nt + nk) else None),
        }

    olculebilir = n_toplam - n_cozulemeyen
    kirlilik = round(n_kirli / olculebilir, 4) if olculebilir else None
    fazla_ozeti = ({"n": len(fazlalar), "ortalama": sum(fazlalar) / len(fazlalar),
                    "medyan": _medyan(fazlalar)} if fazlalar else None)
    sikisma = None
    if fazlalar and len(kirli_fazlalar) == len(fazlalar):
        t, k = _ozetle(fazlalar, ozet), _ozetle(kirli_fazlalar, ozet)
        sikisma = {"temiz": t, "kirli": k, "fark": t - k,
                   "aciklama": ("kirli taban aynı hedefleri OLAYLA kıyaslar; `fark` temizliğin "
                                "etkiyi ne kadar açtığını gösterir (pozitif = kirli ölçüm etkiyi "
                                "SIKIŞTIRIYORDU). YALNIZ BİLGİ — hükme girmez")}

    uyarilar = []
    if n_cozulemeyen:
        uyarilar.append(f"{n_cozulemeyen} evren satırının günü/değeri çözülemedi ve tabana girmedi")
    if n_deger:
        uyarilar.append(f"{n_deger} hedef satırının günü/değeri çözülemedi ve kıyasa girmedi")
    if n_taban_yok:
        uyarilar.append(f"{n_taban_yok} hedef, min_taban={min_taban} şartını karşılamayan "
                        f"{len(tabani_zayif_gunler)} günde kaldığı için kıyaslanamadı — bu günler "
                        f"RASTGELE değildir (ince günler sistematik olarak seçilir)")
    if kirlilik is not None and kirlilik >= 0.5:
        uyarilar.append(f"evren satırlarının %{kirlilik * 100:.0f}'i olay penceresi İÇİNDEYDİ — "
                        f"temizlenmemiş bir gün-tabanı bu ölçümde etkiyi ciddi biçimde SIKIŞTIRIRDI")
    if hedef_satirlari and not kiyaslar:
        uyarilar.append("HİÇBİR HEDEF KIYASLANAMADI — bu pencerede gün-bazlı temiz taban YOK")

    return {
        "kiyaslar": kiyaslar, "fazlalar": fazlalar, "fazla_ozeti": fazla_ozeti,
        "gun_tabani": gun_tabani, "sikisma": sikisma,
        "n_hedef": len(hedef_satirlari), "n_kiyaslanan": len(kiyaslar),
        "n_taban_yok": n_taban_yok, "n_gun": len(gunler),
        "n_toplam": n_toplam, "n_kirli": n_kirli, "n_cozulemeyen": n_cozulemeyen,
        "n_deger_cozulemeyen": n_deger, "n_olculebilir": olculebilir,
        "kirlilik_orani": kirlilik, "n_olay": n_olay,
        "pencere": {"once": once, "sonra": sonra},
        "gun_birimi": (next(iter(birimler)) if len(birimler) == 1 else None),
        "ozet": ozet, "min_taban": min_taban, "hedef_kaynagi": hedef_kaynagi,
        "beyan": ("taban = AYNI GÜNÜN olay-penceresi DIŞI satırları, hedefin KENDİ kimliği "
                  "düşürülmüş hâliyle. Pencere kapsayıcıdır (olay gününün kendisi de kirli). "
                  "min_taban altındaki günler kıyasa girmez ve n_taban_yok ile sayılır. "
                  "kirli_taban/sikisma YALNIZ BİLGİDİR — hüküm temiz tabandan okunur."),
        "uyari": (" · ".join(uyarilar) if uyarilar else None),
    }


# ==================================================================================================
# 2B — BLOK-BOOTSTRAP CI STANDARDI
# ==================================================================================================
# NEDEN BLOK, NEDEN IID DEĞİL. Zaman serisi gözlemleri bağımsız DEĞİLDİR: getiriler kümelenir
# (volatilite kümelenmesi), kayıplar seri hâlinde gelir, aynı rejimdeki günler birlikte hareket
# eder. IID yeniden örnekleme bu bağımlılığı KIRAR ve ortalamanın örnekleme dağılımını olduğundan
# DAR gösterir — yani aralık, ölçülmemiş bir kesinlik yazar. Bu tek yönlü bir hatadır: IID daima
# "daha anlamlı" görünür, hiçbir zaman daha az. Bu yüzden IID bir tercih değil, bir HATA SINIFIDIR.
#
# DEPODAKİ CANLI KANIT (analytics, n=95): işlem başına ortalama $ için IID aralık
# [−116,86, −0,00] sıfırı KIL PAYI dışarıda bırakıyordu ("kaybettiğimiz kanıtlandı"), blok aralığı
# [−137,75, +14,53] ise sıfırı İÇERİYOR ("n=95'te henüz kanıtlanmadı"). Aynı defter, iki hüküm.
#
# BU FONKSİYON MEVCUT HESAPLARI DEĞİŞTİRMEZ. `analytics._blok_bootstrap_ci` (dolar beklentisi,
# CIRCULAR blok, blok=5 İŞLEM) ve `score.tail_risk` kendi eksenlerinde çalışmaya AYNEN devam eder;
# oradaki sayılar yayımlanmış hükümlerin tabanıdır ve bu turda tek hanesi bile oynatılmadı. Buradaki
# araç İLERİYE dönük ölçüm şablonları içindir (kart ölçümleri, getiri serileri).
#
# MOVING BLOCK vs CIRCULAR — BEYANLI FARK. Burada ÖRTÜŞEN (moving) blok kullanılır: bloklar
# [0, n−L] aralığındaki her başlangıçtan seçilir, dizi SARILMAZ. Bunun bilinen bedeli, uçlardaki
# gözlemlerin biraz daha AZ örneklenmesidir (ilk/son L−1 gözlem daha az blokta görünür) ve bu,
# aralığı bir miktar daraltabilir. Sarmalı (circular) varyant bu dengesizliği giderir ama serinin
# sonunu başına DİKER — trend taşıyan bir seride olmayan bir devamlılık uydurur. Getiri serilerinde
# moving block yazının varsayılanıdır; seçim burada YAZILIDIR, çıktıda `yontem` alanında da durur.
BOOTSTRAP_TOHUM = 11        # sabit tohum: aynı seri aynı aralığı verir (tekrarlanabilirlik şartı)
BOOTSTRAP_N = 2000          # varsayılan replikasyon. %2,5/%97,5 yüzdelikleri için yeterli; ölçüm
                            # şablonları binlerce seri koştuğunda maliyet lineer büyür.
BOOTSTRAP_MIN_N = 2         # altında ortalamanın dağılımı KURULAMAZ → lo/hi None + neden


def _blok_uzunlugu(n: int) -> int:
    """n^(1/3) kuralı — blok uzunluğunun standart pratik seçimi (bağımlılık ufku ile örnek sayısı
    arasındaki ödünleşme). Kural ADIYLA raporlanır; "blok neden 6?" sorusu tahminle cevaplanmasın."""
    return max(1, min(n, int(round(n ** (1.0 / 3.0)))))


def blok_bootstrap_ci(seri, blok: int | None = None, n_ornek: int = BOOTSTRAP_N,
                      seviye: float = 0.95, tohum: int = BOOTSTRAP_TOHUM) -> dict:
    """ORTALAMANIN örtüşen-blok (moving block) bootstrap güven aralığı.

    NE ZAMAN ZORUNLU (ileriye dönük standart, `docs/olcum_standartlari.md` Ders #5).
    Seri ZAMAN SIRALIYSA ve gözlemler arasında otokorelasyon OLASIYSA — yani günlük/bar getirileri,
    işlem serileri, eşitlik eğrisi farkları, gün-bazlı taban-fazlası serileri — aralık BLOK
    bootstrap ile kurulur. IID bootstrap (`blok=1`) bu sınıfta YASAKTIR: bağımlılığı kırar,
    aralığı sistematik olarak daraltır ve hükmü tek yönde kaydırır. IID yalnız gözlemlerin
    gerçekten değiştirilebilir (exchangeable) olduğu kesitlerde meşrudur ve o zaman bile kartta
    "neden IID meşru" cümlesi yazılır.

    Parametreler
    ------------
    seri    : sayı dizisi, ZAMAN SIRASINDA. Sıra bu fonksiyonun tek bilgi kaynağıdır — karıştırılmış
              bir seri verilirse blok yapısı anlamsızdır ve fonksiyon bunu ANLAYAMAZ (beyan).
    blok    : blok uzunluğu. None → `n^(1/3)` kuralı (çıktıda `blok_kaynagi` ile söylenir).
              `blok=1` IID bootstrap'tır ve çıktıda `iid: True` + uyarı ile DAMGALANIR.
    n_ornek : replikasyon sayısı (varsayılan 2000).
    seviye  : güven seviyesi (0,95 → %2,5/%97,5 yüzdelikleri).
    tohum   : sabit tohum; aynı girdi aynı aralığı verir.

    Dönüş
    -----
    {"ort","lo","hi","seviye","n","blok","blok_kaynagi","B","iid","sifiri_disliyor",
     "n_cozulemeyen","tohum","yontem","beyan","neden","uyari"}

    ÖLÇÜLEMEDİĞİNDE UYDURMAZ: n < 2 ise `lo`/`hi` **None** ve `neden` doludur; `sifiri_disliyor` da
    None'dır (False DEĞİL — "sıfırı dışlamıyor" ölçülmüş bir cevaptır, ölçülememiş değil).
    """
    import numpy as np

    # `seri or ()` YAZILAMAZ: numpy dizisinde `bool(dizi)` ValueError atar ("truth value of an array
    # is ambiguous") ve ölçüm şablonlarının elindeki seri tipik olarak bir numpy dizisidir.
    ham = list(seri) if seri is not None else []
    vals, n_cozulemeyen = [], 0
    for v in ham:
        try:
            f = float(v)
        except (TypeError, ValueError):  # sessiz-yutma: sayıya çevrilemeyen gözlem SAYILIR (n_cozulemeyen) ve uyarıya girer — bir bootstrap'ta sessizce düşen gözlem, örneklem büyüklüğünü haber vermeden küçültür
            n_cozulemeyen += 1
            continue
        if f != f or f in (float("inf"), float("-inf")):   # NaN / sonsuz
            n_cozulemeyen += 1
            continue
        vals.append(f)

    n = len(vals)
    uyarilar = []
    if n_cozulemeyen:
        uyarilar.append(f"{n_cozulemeyen} gözlem sayı değildi (NaN/None/sonsuz) ve seriden düştü — "
                        f"aralık n={n} üzerinden kuruldu")
    if n < BOOTSTRAP_MIN_N:
        return {"ort": (vals[0] if n == 1 else None), "lo": None, "hi": None, "seviye": seviye,
                "n": n, "blok": None, "blok_kaynagi": None, "B": 0, "iid": None,
                "sifiri_disliyor": None, "n_cozulemeyen": n_cozulemeyen, "tohum": tohum,
                "yontem": "moving block bootstrap (koşulmadı)",
                "neden": f"n={n} < {BOOTSTRAP_MIN_N} — ortalamanın örnekleme dağılımı kurulamaz",
                "beyan": "aralık ÖLÇÜLEMEDİ; None bir sayı değildir ve 0 yerine geçmez",
                "uyari": (" · ".join(uyarilar) if uyarilar else None)}

    if blok is None:
        L, blok_kaynagi = _blok_uzunlugu(n), "n^(1/3) kuralı"
    else:
        L = max(1, min(int(blok), n))
        blok_kaynagi = ("verildi" if L == int(blok)
                        else f"verildi ({int(blok)}) ama n={n}'e kırpıldı")

    B = max(1, int(n_ornek))                         # 0 replikasyonun yüzdeliği YOKTUR
    x = np.asarray(vals, dtype=float)
    k = -(-n // L)                                   # ceil(n / L) blok, sonda kırpılır
    rng = np.random.default_rng(tohum)
    bas = rng.integers(0, n - L + 1, size=(B, k))                     # MOVING: sarma YOK
    idx = bas[:, :, None] + np.arange(L)[None, None, :]
    ort = x[idx].reshape(B, k * L)[:, :n].mean(axis=1)
    alt = (1.0 - seviye) / 2.0 * 100.0
    lo, hi = (float(q) for q in np.percentile(ort, [alt, 100.0 - alt]))

    if L == 1:
        uyarilar.append("blok=1 → BU BİR IID BOOTSTRAP'TIR. Zaman-sıralı bir seride aralığı "
                        "sistematik olarak DARALTIR; kartta 'gözlemler neden değiştirilebilir' "
                        "gerekçesi yazılmadan kullanılamaz (Ders #5)")
    if n < 4 * L:
        uyarilar.append(f"n={n}, blok={L} — seride yalnız ~{n / L:.1f} blok var; blok bootstrap'ın "
                        f"kendisi bu kadar az blokta gürültülüdür (aralık geniş ÇIKMAYABİLİR)")

    return {
        "ort": float(x.mean()), "lo": lo, "hi": hi, "seviye": seviye,
        "n": n, "blok": L, "blok_kaynagi": blok_kaynagi, "B": B, "iid": (L == 1),
        "sifiri_disliyor": bool(lo > 0 or hi < 0),
        "n_cozulemeyen": n_cozulemeyen, "tohum": tohum,
        "yontem": (f"moving (örtüşen) blok bootstrap · blok={L} ({blok_kaynagi}) · "
                   f"B={B} · tohum={tohum} · yüzdelik aralığı"),
        "neden": None,
        "beyan": ("Bloklar [0, n−L] aralığındaki başlangıçlardan seçilir ve dizi SARILMAZ; bunun "
                  "bilinen bedeli uçlardaki gözlemlerin biraz az örneklenmesidir. Serinin ZAMAN "
                  "SIRASINDA olduğu VARSAYILIR — karıştırılmış bir seride blok yapısı anlamsızdır "
                  "ve fonksiyon bunu anlayamaz. Aralık ORTALAMA içindir; medyan/oran için "
                  "yeniden türetilmelidir."),
        "uyari": (" · ".join(uyarilar) if uyarilar else None),
    }


# ==================================================================================================
# 2C — EMPİRİK-BAYES KÜÇÜLTME (SE tabanlı)
# ==================================================================================================
# NEDEN VAR — EN İYİ HÜCRE SEÇİM YANLILIĞI ("kazananın laneti"). Çok hücreli bir kart özeti (K
# grid'i: bileşen × ufuk, rejim × kurulum, eşik × pencere) hücrelerin HAM tahminlerini yazar ve
# okuyucu doğal olarak EN İYİSİNE bakar. Ama en iyi hücre, en büyük GERÇEK etkiye sahip hücre
# değildir: en büyük (gerçek etki + GÜRÜLTÜ) toplamına sahip hücredir. Yani ham en-iyi hücre
# SİSTEMATİK olarak yukarı yanlıdır ve yanlılık hücre sayısıyla büyür. Bu, K-cezasının kapıda
# çözdüğü sorunun ÖZET tarafındaki ikizidir: kapı "kaç yoklama yaptın?" diye sorar, küçültme
# "kazananın ne kadarı gürültüydü?" diye sorar.
#
# NE YAPAR. Her hücreyi kendi standart hatasıyla orantılı biçimde ORTAK ortalamaya çeker:
#     w_i = τ² / (τ² + SE_i²)   ·   küçültülmüş_i = w_i · x_i + (1 − w_i) · hedef
# τ² (hücreler arası GERÇEK yayılım) momentlerle tahmin edilir: gözlenen yayılım − ortalama gürültü.
# Negatif çıkarsa 0'a kıstırılır ve bu, "hücreler arasında ölçülebilir gerçek fark YOK" demektir →
# her hücre hedefe TAM küçültülür. Bu bir eksiklik değil, dürüst cevaptır.
#
# `analytics._empirical_bayes` İLE İLİŞKİSİ — BİLEREK AYRI. O fonksiyon {mean, n, sd} sözleşmesiyle
# çalışır, n-ağırlıklı bir taban kullanır ve YAYIMLANMIŞ sayıların (component_ic `eb` sütunu, pano)
# tabanıdır. Bu fonksiyon doğrudan SE ile çalışır (kart özetlerinin doğal para birimi: etki ± SE) ve
# hedefi düz ortalamadır. İkisini tek gövdeye indirgemek, yayımlanmış `eb_ic` sayılarını HABERSİZ
# oynatırdı — bu turda hiçbir yayımlanmış sayı oynatılmadı. İki uygulamanın FARKI yazılıdır; aynı
# adı taşımadıkları için de karışmazlar.
EB_MIN_HUCRE = 3            # altında hücreler-arası varyans TAHMİN EDİLEMEZ → küçültme yok + neden


def eb_kucult(etkiler, seler, min_hucre: int = EB_MIN_HUCRE) -> dict:
    """Empirik-Bayes (James-Stein) havuz-küçültmesi: {ad: etki} + {ad: SE} → küçültülmüş tahminler.

    Parametreler
    ------------
    etkiler : {ad: etki} sözlüğü ya da sayı listesi (liste verilirse adlar "0","1",… olur).
    seler   : {ad: standart hata} sözlüğü ya da `etkiler` ile AYNI SIRADA liste. SE'si olmayan /
              pozitif olmayan hücre KÜÇÜLTÜLEMEZ: atılmaz, `n_se_yok`/`n_se_gecersiz` ile SAYILIR
              ve ham hâliyle raporlanır (SE'siz bir hücreye ağırlık uydurmak, ölçülmemiş bir
              kesinlik yazmaktır).
    min_hucre: bu sayının altında küçültme YAPILMAZ ve `neden` doldurulur.

    Dönüş
    -----
    {"hucreler": {ad: {"ham","se","kucultulmus","agirlik","cekim"}},
     "n_hucre","kucultuldu","neden","tau2","hedef","ortalama_se2","yayilim",
     "en_iyi_ham": {"hucre","ham","kucultulmus","cekim"},
     "en_iyi_kucultulmus": {...}, "sira_degisti",
     "n_se_yok","n_se_gecersiz","n_cozulemeyen","yontem","beyan","uyari"}

    KULLANIM KURALI (ileriye dönük standart, Ders #6). Çok hücreli bir kart özetinde EN İYİ HÜCRE
    rapor ediliyorsa, ham değerinin YANINDA küçültülmüş değeri de yazılır. Küçültülmüş değer
    HÜKÜM VERMEZ ve eşiklere GİRMEZ: küçültme örneklem büyütmez, yalnız gürültüyü geri alır. Kart
    eşiği neyse odur — bu araç eşiği ne gevşetir ne sıkar (`analytics._empirical_bayes`in
    "verdict tabanlarına giremez" beyanının aynısı).
    """
    # ---- girdi normalleştirme ------------------------------------------------------------------
    # `x or ()` YAZILAMAZ (numpy dizisinde `bool(dizi)` ValueError atar) — `is None` ile bakılır.
    if isinstance(etkiler, dict):
        adlar = list(etkiler.keys())
        ham_x = [etkiler[a] for a in adlar]
    else:
        ham_x = list(etkiler) if etkiler is not None else []
        adlar = [str(i) for i in range(len(ham_x))]
    if isinstance(seler, dict):
        ham_se = [seler.get(a) for a in adlar]
    elif seler is None:
        ham_se = [None] * len(ham_x)
    else:
        ham_se = list(seler)
    if len(ham_se) != len(ham_x):
        raise ValueError(f"etki sayısı ({len(ham_x)}) ile SE sayısı ({len(ham_se)}) uyuşmuyor — "
                         f"hizası kaymış bir SE listesi, her hücreye BAŞKASININ belirsizliğini verir")

    hucreler: dict = {}
    kullanilabilir: list = []                 # (ad, x, se) — küçültülebilenler
    n_se_yok = n_se_gecersiz = n_cozulemeyen = 0
    for ad, x, se in zip(adlar, ham_x, ham_se):
        try:
            xf = float(x)
        except (TypeError, ValueError):  # sessiz-yutma: etkisi sayı olmayan hücre SAYILIR (n_cozulemeyen) ve uyarıya girer — özetten sessizce düşen hücre, K'yı haber vermeden küçültür
            n_cozulemeyen += 1
            continue
        if xf != xf:
            n_cozulemeyen += 1
            continue
        if se is None:
            n_se_yok += 1
            hucreler[ad] = {"ham": xf, "se": None, "kucultulmus": xf, "agirlik": 1.0, "cekim": 0.0,
                            "not": "SE yok — küçültülemedi (ham değer olduğu gibi durur)"}
            continue
        try:
            sef = float(se)
        except (TypeError, ValueError):  # sessiz-yutma: SE'si sayı olmayan hücre n_se_gecersiz'e yazılır ve ham hâliyle raporlanır — atılmaz
            sef = float("nan")
        if not (sef > 0) or sef != sef:
            n_se_gecersiz += 1
            hucreler[ad] = {"ham": xf, "se": (sef if sef == sef else None), "kucultulmus": xf,
                            "agirlik": 1.0, "cekim": 0.0,
                            "not": "SE pozitif değil — sonsuz kesinlik iddiası; küçültülemedi"}
            continue
        kullanilabilir.append((ad, xf, sef))

    uyarilar = []
    if n_cozulemeyen:
        uyarilar.append(f"{n_cozulemeyen} hücrenin etkisi sayı değildi ve özete girmedi")
    if n_se_yok:
        uyarilar.append(f"{n_se_yok} hücrenin SE'si YOK — ham hâlleriyle durdular, küçültülmediler")
    if n_se_gecersiz:
        uyarilar.append(f"{n_se_gecersiz} hücrenin SE'si pozitif değildi — küçültülmediler")

    k = len(kullanilabilir)
    if k < max(2, int(min_hucre)):
        return {
            "hucreler": hucreler, "n_hucre": k, "kucultuldu": False,
            "neden": (f"{k} küçültülebilir hücre < {min_hucre} — hücreler-arası varyans TAHMİN "
                      f"EDİLEMEZ (küçültme yapılmadı, uydurulmadı)"),
            "tau2": None, "hedef": None, "ortalama_se2": None, "yayilim": None,
            "en_iyi_ham": None, "en_iyi_kucultulmus": None, "sira_degisti": None,
            "n_se_yok": n_se_yok, "n_se_gecersiz": n_se_gecersiz, "n_cozulemeyen": n_cozulemeyen,
            "yontem": "empirik Bayes (momentler) — KOŞULMADI",
            "beyan": "küçültme yapılmadı; ham değerler olduğu gibi döndü",
            "uyari": (" · ".join(uyarilar + [f"küçültülebilir hücre sayısı {k}"]) or None),
        }

    xs = [x for _, x, _ in kullanilabilir]
    hedef = sum(xs) / k                                        # düz ortalama = küçültme HEDEFİ
    yayilim = sum((x - hedef) ** 2 for x in xs) / (k - 1)      # gözlenen hücreler-arası yayılım
    ort_se2 = sum(se ** 2 for _, _, se in kullanilabilir) / k  # ortalama gürültü varyansı
    tau2 = max(0.0, yayilim - ort_se2)                         # GERÇEK yayılım (0'a kıstırılmış)

    for ad, x, se in kullanilabilir:
        w = tau2 / (tau2 + se ** 2) if (tau2 + se ** 2) > 0 else 0.0
        km = w * x + (1.0 - w) * hedef
        hucreler[ad] = {"ham": x, "se": se, "kucultulmus": km, "agirlik": w, "cekim": x - km}

    def _en_iyi(anahtar: str):
        ad = max((a for a, _, _ in kullanilabilir), key=lambda a: hucreler[a][anahtar])
        h = hucreler[ad]
        return {"hucre": ad, "ham": h["ham"], "kucultulmus": h["kucultulmus"],
                "cekim": h["cekim"], "agirlik": h["agirlik"]}

    en_iyi_ham = _en_iyi("ham")
    en_iyi_kucuk = _en_iyi("kucultulmus")
    if tau2 == 0.0:
        uyarilar.append("τ²=0 — hücreler arasında ÖLÇÜLEBİLİR gerçek fark yok; her hücre ortak "
                        "ortalamaya TAM küçültüldü (eksiklik değil, dürüst cevap)")

    return {
        "hucreler": hucreler, "n_hucre": k, "kucultuldu": True, "neden": None,
        "tau2": tau2, "hedef": hedef, "ortalama_se2": ort_se2, "yayilim": yayilim,
        "en_iyi_ham": en_iyi_ham, "en_iyi_kucultulmus": en_iyi_kucuk,
        "sira_degisti": bool(en_iyi_ham["hucre"] != en_iyi_kucuk["hucre"]),
        "n_se_yok": n_se_yok, "n_se_gecersiz": n_se_gecersiz, "n_cozulemeyen": n_cozulemeyen,
        "yontem": ("empirik Bayes (momentler): w_i = τ²/(τ²+SE_i²); τ² = hücreler-arası yayılım − "
                   "ortalama SE², 0'a kıstırılmış; hedef = hücrelerin düz ortalaması"),
        "beyan": ("KÜÇÜLTÜLMÜŞ DEĞER HÜKÜM VERMEZ ve eşiklere GİRMEZ: küçültme örneklemi büyütmez, "
                  "yalnız kazananın gürültü payını geri alır. `en_iyi_ham` ile "
                  "`en_iyi_kucultulmus` FARKLI hücreler olabilir (`sira_degisti`) — bu, ham "
                  "sıralamanın gürültüye ne kadar borçlu olduğunun ölçüsüdür. Hücreler bağımsız "
                  "VARSAYILIR; aynı gözlemlerden türeyen hücrelerde (ör. aynı bileşenin 5/10/20 bar "
                  "ufukları) τ² bir miktar küçük, küçültme bir miktar güçlü olur."),
        "uyari": (" · ".join(uyarilar) if uyarilar else None),
    }


# ==================================================================================================
# KOD-SÜRÜMÜ DAMGASI
# ==================================================================================================
# NEDEN VAR. Bir ölçüm raporu okunurken sorulan ilk soru "bu sayı hangi kodla üretildi?"dir ve bu
# soru bugüne kadar hiçbir raporun İÇİNDE cevaplanmıyordu. Cevap dışarıda (dosya tarihi, oturum
# kaydı, hafıza) arandığında tahmine dönüşür; iki hafta sonra bir aracın davranışı değiştiğinde eski
# rapor SESSİZCE yeni davranışla okunur. Damga bunu kapatır: git HEAD + ölçüm-araçları sürüm listesi.
#
# KİRLİ AĞAÇ AYRI BİR ALANDIR. Çalışma ağacı kirliyken üretilen bir rapor, SHA'dan yeniden
# ÜRETİLEMEZ — SHA o anki kodu değil, o anki kodun ATASINI adlandırır. `kirli_agac: True` bu farkı
# raporun içinde söyler; damgayı "SHA yazdım demek ki tekrarlanabilir" diye okumayı engeller.
def kod_surumu_damgasi(kok=None, zaman_asimi: float = 10.0) -> dict:
    """Raporun kod kimliği: `git rev-parse HEAD` (varsa) + ölçüm araçlarının sürüm listesi.

    Dönüş: {"git_head","git_head_kisa","kirli_agac","git_neden","olcum_araclari_surum",
            "arac_surumleri","beyan"}.

    UYDURMA YASAĞI: git yoksa / depo değilse / komut başarısızsa `git_head` **None**'dır ve
    `git_neden` sebebi ADIYLA taşır. "bilinmiyor"un yerine boş dizgi ya da eski bir SHA konmaz.
    YAN ETKİSİZ: yalnız-okuma iki git komutu koşar; hiçbir şey yazmaz, ağa çıkmaz."""
    import pathlib
    import subprocess

    kok = pathlib.Path(kok) if kok else pathlib.Path(__file__).resolve().parent.parent
    head = kisa = kirli = neden = None

    def _git(*argv):
        return subprocess.run(["git", *argv], cwd=str(kok), capture_output=True, text=True,
                              timeout=zaman_asimi)
    try:
        r = _git("rev-parse", "HEAD")
        if r.returncode == 0 and r.stdout.strip():
            head = r.stdout.strip()
            kisa = head[:7]
        else:
            neden = f"git rev-parse HEAD başarısız (rc={r.returncode}): {(r.stderr or '').strip()[:120]}"
    except (OSError, ValueError, subprocess.SubprocessError) as e:
        neden = f"git çağrılamadı: {type(e).__name__}: {e}"

    if head is not None:
        try:
            r = _git("status", "--porcelain")
            if r.returncode == 0:
                kirli = bool(r.stdout.strip())
            else:
                neden = (f"HEAD okundu ama `git status` başarısız (rc={r.returncode}) — "
                         f"ağacın temiz olup olmadığı BİLİNMİYOR")
        except (OSError, ValueError, subprocess.SubprocessError) as e:
            neden = f"HEAD okundu ama `git status` çağrılamadı: {type(e).__name__}: {e}"

    return {
        "git_head": head, "git_head_kisa": kisa, "kirli_agac": kirli, "git_neden": neden,
        "olcum_araclari_surum": SURUM, "arac_surumleri": dict(ARAC_SURUMLERI),
        "beyan": ("git_head None ise ÖLÇÜLEMEDİ (neden alanında yazar) — boş dizgi ya da tahmin "
                  "yazılmaz. kirli_agac True ise rapor bu SHA'dan YENİDEN ÜRETİLEMEZ: SHA o anki "
                  "kodun değil atasının adıdır. arac_surumleri, raporun hangi ölçüm-aracı "
                  "davranışıyla üretildiğini söyler (araç değişirse sürümü de değişir)."),
    }
