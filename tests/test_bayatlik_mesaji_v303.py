"""BAYATLIK MESAJI ARIZANIN BÜYÜKLÜĞÜNÜ GİZLEMEZ · v303

VAKA (2026-08-25). Alarm metni şuydu:

    "mekanizma gecikti: hermes_poll — 0.5 sa (pencere 0.5 sa)"

İki sayı AYNI görünüyor ve metin bir bekçi arızası gibi okunuyor. Ölçüldü — iki ayrı kusur:

  (1) YUVARLAMA. `round(gap/3600, 1)` hem 1810 sn'yi hem 1800 sn'lik pencereyi "0.5" yapar.
      Kıl payı bir aşım ile saatlerce süren bir aşım aynı satırı üretir.
  (2) DAHA KÖTÜSÜ — SAYI SESSİZLİĞİN UZUNLUĞU DEĞİL. `check_and_alarm` 300 sn'lik scheduler
      poll'unda koşar ve histerezis mandalı (`if ad in alarmed: continue`) tekrarı keser.
      Yani kaydedilen gap HER ZAMAN İLK TESPİT anındaki gap'tir → (1800, 2100] → 0,5 veya 0,6.
      Sessizlik 30 dk da sürse 15,2 sa da sürse deftere "0.5" yazılır.
      ÖLÇÜLDÜ: 134 kaydın 113'ü (%84) 0,5 ya da 0,6. Gerçek sessizlikler 2,1-2,8 sa,
      bir vakada 15,2 sa. Metin arızayı küçük gösteriyordu ve teşhis ÜÇ KEZ yanlış yöne gitti.

BU ÇİVİNİN KORUDUĞU ŞEY: (a) iki sayı ayırt edilebilir kalsın, (b) rakamın "ilk tespit" değeri
olduğu YAZILI olsun, (c) sessizlik BİTTİĞİNDE gerçek uzunluğu ölçülüp kaydedilsin — yoksa
"gerçekte ne kadar sustu" sorusu geriye dönük ÖLÇÜLEMEZ kalır.
"""
from __future__ import annotations

import time

from meridian import obs as _obs, store, watchdog


def _beat_kur(monkeypatch, ad: str, yas_sn: float):
    """`ad` mekanizması `yas_sn` saniye önce nabız atmış gibi davransın."""
    monkeypatch.setattr(watchdog, "EXPECTED", {ad: 1800})
    monkeypatch.setattr(watchdog, "_beats", lambda: {ad: time.time() - yas_sn}, raising=False)


def test_rapor_saniye_ve_asim_tasiyor(sandbox_state, monkeypatch):
    """Yuvarlanmış saat TEK BAŞINA yeterli değil: ham saniye ve AŞIM da satırda olmalı."""
    store.write_json("mechanism_beats.json", {"deneme": time.time() - 1810})
    monkeypatch.setattr(watchdog, "EXPECTED", {"deneme": 1800})
    rep = watchdog.report()
    assert rep["stale"], f"1810 sn'lik boşluk bayat sayılmadı: {rep}"
    x = rep["stale"][0]
    assert "gap_s" in x and "asim_s" in x, f"satır ham saniye/aşım taşımıyor: {sorted(x)}"
    assert 1805 <= x["gap_s"] <= 1830, f"gap_s yanlış: {x['gap_s']}"
    assert 5 <= x["asim_s"] <= 30, f"aşım yanlış: {x['asim_s']}"


def test_alarm_metni_IKI_AYNI_SAYI_basmaz(sandbox_state, monkeypatch):
    """Kıl payı aşımda metin '0.5 sa (pencere 0.5 sa)' üretmemeli."""
    store.write_json("mechanism_beats.json", {"deneme": time.time() - 1810})
    monkeypatch.setattr(watchdog, "EXPECTED", {"deneme": 1800})
    yakalanan = []
    monkeypatch.setattr(_obs, "alarm",
                        lambda ad, detay, **k: yakalanan.append((ad, detay, k)))
    watchdog.check_and_alarm()
    assert yakalanan, "alarm hiç basılmadı"
    _ad, detay, _k = yakalanan[0]
    assert "0.5 sa (pencere 0.5 sa)" not in detay, (
        f"metin hâlâ iki aynı sayı basıyor — kusur duruyor: {detay}")
    assert "aşım" in detay or "asim" in detay, f"aşım metinde yok: {detay}"


def test_alarm_metni_ILK_TESPIT_oldugunu_SOYLUYOR(sandbox_state, monkeypatch):
    """UYDURMA YASAĞI sınıfı: rakam sessizliğin uzunluğu DEĞİL; metin bunu itiraf etmeli."""
    store.write_json("mechanism_beats.json", {"deneme": time.time() - 5400})
    monkeypatch.setattr(watchdog, "EXPECTED", {"deneme": 1800})
    yakalanan = []
    monkeypatch.setattr(_obs, "alarm",
                        lambda ad, detay, **k: yakalanan.append(detay))
    watchdog.check_and_alarm()
    assert yakalanan, "alarm hiç basılmadı"
    d = yakalanan[0]
    # `.lower()` KULLANILMAZ: Python Türkçe "İ"yi "i̇" (i + birleşen nokta) yapar ve düz bir
    # alt-dize araması sessizce tutmaz. Metin zaten sabit; olduğu gibi aranır.
    assert "İLK TESPİT" in d, (
        f"metin rakamın ilk-tespit değeri olduğunu söylemiyor — sessizlik SÜRÜYOR olabilir: {d}")
    assert "mechanism_recovered" in d, "gerçek uzunluğun nerede olduğu metinde yazmıyor"
    # Mutasyonla yakalandı: uyarı cümlesi silinince çivi susuyordu. Metnin ASIL işi bu —
    # okuyucuya "gördüğün sayı bitmiş bir olayın ölçüsü DEĞİL" demek.
    assert "sürüyor" in d, f"sessizliğin SÜRÜYOR olabileceği söylenmiyor: {d}"


def test_sessizlik_bitince_GERCEK_uzunluk_olculuyor(sandbox_state, monkeypatch):
    """(c) ayağı: mandal yüzünden 'ne kadar sustu' kaybolmasın. Toparlanmada olay + süre."""
    monkeypatch.setattr(watchdog, "EXPECTED", {"deneme": 1800})
    # 1) bayat: ilk tespit
    store.write_json("mechanism_beats.json", {"deneme": time.time() - 5400})
    monkeypatch.setattr(_obs, "alarm", lambda *a, **k: None)
    watchdog.check_and_alarm()
    assert "deneme" in store.read_json("watchdog_alarmed.json", {}), (
        "bayatlığın BAŞLANGICI hiçbir yere yazılmadı — gerçek uzunluk bir daha ölçülemez")
    # 2) toparlanma: nabız geldi
    kayit = []
    monkeypatch.setattr(_obs, "log", lambda ad, **k: kayit.append((ad, k)))
    store.write_json("mechanism_beats.json", {"deneme": time.time()})
    watchdog.check_and_alarm()
    olay = [k for ad, k in kayit if ad == "mechanism_recovered"]
    assert olay, f"toparlanma kaydedilmedi: {[a for a, _ in kayit]}"
    sess = olay[0].get("sessizlik_s")
    assert sess is not None and sess >= 5400, (
        f"ölçülen sessizlik gerçeğin altında ({sess}) — ilk tespit gap'i eklenmemiş olabilir")
    assert "deneme" not in store.read_json("watchdog_alarmed.json", {}), (
        "toparlanan mekanizma bayat-başlangıç defterinden silinmedi (sızıntı)")


def test_BOZUK_mandal_dosyasi_bekciyi_DUSURMEZ(sandbox_state, monkeypatch):
    """Bekçi bir HİJYEN aracıdır, karar kaynağı değil: bozuk bir mandal dosyası yüzünden istisna
    atmak, tam da var olma sebebini (haber vermek) kaybettirir — üstelik çağıran scheduler
    poll'unu da yanında götürür (`_gunluk_oku` docstring'indeki aynı yasa).

    VAKA: v303 damgası mandal dosyasına taşınınca değerlerin SÖZLÜK olduğu varsayıldı. Tam
    suite'te `store.read_json` her dosya için `{"last_date": "..."}` döndüren bir testte
    `'str' object has no attribute 'get'` ile patladı ve scheduler turunu götürdü."""
    monkeypatch.setattr(watchdog, "EXPECTED", {"deneme": 1800})
    store.write_json("mechanism_beats.json", {"deneme": time.time() - 5400})
    monkeypatch.setattr(_obs, "alarm", lambda *a, **k: None)
    monkeypatch.setattr(_obs, "log", lambda *a, **k: None)
    for bozuk in ({"deneme": "yabanci-dize"}, {"deneme": None}, {"deneme": 42},
                  ["deneme"], "hepten-bozuk", {"baska_dosya": "alakasiz"}):
        store.write_json("watchdog_alarmed.json", bozuk)
        watchdog.check_and_alarm()          # istisna ATMAMALI
    # ve bozuk şekilden sonra dosya SAĞLAM şekle dönmüş olmalı
    son = store.read_json("watchdog_alarmed.json", None)
    assert isinstance(son, dict), f"mandal dosyası sözlüğe dönmedi: {type(son)}"
    assert all(isinstance(v, dict) for v in son.values()), f"bozuk değer kaldı: {son}"
