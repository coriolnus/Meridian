"""test_read_jsonl_kuyruk_v410.py — TSK-137a, 2026-09-04: `store.read_jsonl(limit=)` SONDAN kuyruk
okuma (seek-from-end) + `/api/alerts` kısa sunucu önbelleği.

BAĞLAM (`docs/TASARIM-DEFTER-ROTASYONU-2026-09-04.md` §3(c)/§4 adım-1, brief
`.superpowers/sdd/2026-09-04-tsk137a/brief.md`): `store.read_jsonl` dosya-yolu dalında `limit`
verildiğinde bile dosyanın TAMAMI okunup `rows[-limit:]` ile kırpılıyordu (events.jsonl A1'de
26,5 MB; üç sık okuyucu — `notify.inbox` /api/alerts 15 sn, `analytics._hayalet_suzulen_n` /api/hermes
30 sn, `hermes.bg_on_eleme_karnesi` — her çağrıda tam ayrıştırma yapıyordu). Emsal:
`api._son_dongu_olaydan` (byte-seek + kademeli büyüyen blok + mtime önbelleği).

BU DOSYA ÜÇ SÖZLEŞMEYİ ÇİVİLER:
  D1 `store.read_jsonl(name, limit=N)` dosya-yolu dalı, TAM OKUMANIN test-içi BAĞIMSIZ naif
     referansıyla (`_naif_oku` — store.py'den KOPYA DEĞİL, testin kendi ayrıştırıcısı) sentetik
     defterlerde (küçük/büyük, limit </> satır sayısı, son satır \\n'siz, boş dosya, bozuk satır)
     BİREBİR eşittir.
  D2 Bedel ölçümü: yerel `state/events.jsonl` (9 MB, "yerel" etiketiyle) üzerinde limit=4000 ve
     limit=15000 için kuyruk okumanın TAM OKUMADAN AZ bayt okuduğu ölçülür (sayı iddiası yok —
     yalnız "az okur" ölçülür, mutlak bir ms/bayt eşiğine çivi atılmaz: donanıma göre değişir).
  D3 `/api/alerts` sunucu önbelleği: TestClient + `sandbox_state` ile hit/miş, `events.jsonl`
     mtime'ı değişince MISS.

MUTASYON DOĞRULAMASI (bu oturumda elle yapıldı, kalıcı test DEĞİL — CLAUDE.md §6 "çivi yeşili
kanıt değildir"): (1) `_read_jsonl_kuyruk`daki `f.readline()` (ilk yarım satırı atma) adımı
kaldırılınca `test_kuyruk_ilk_kismi_satiri_ATMAZSA_hayalet_satir_uretir` KIRMIZI oldu; (2)
`meridian/api.py`deki `ALERTS_TTL_S` 0'a çekilince `test_alerts_ikinci_cagri_onbellekten_gelir`
KIRMIZI oldu. İkisi de doğrulandıktan sonra geri alındı (pyc silindi)."""
from __future__ import annotations

import json
import random
import shutil
import statistics
import time as _time
from pathlib import Path

import pytest

from meridian import store

REPO = Path(__file__).resolve().parent.parent


# ================================================================================================
# YARDIMCILAR
# ================================================================================================

def _naif_oku(path: Path, limit: int | None = None) -> list:
    """TAM OKUMANIN BAĞIMSIZ referansı — `store.py`den kopya DEĞİL, testin KENDİ ayrıştırıcısı
    (brief D1: "test içinde bağımsız naif okuma"). Amaç: store'daki bir regresyon iki tarafı da
    aynı yanlış cevaba GÖTÜRMESİN — referans store'un uygulama detaylarını bilmez, yalnız eski
    sözleşmeyi (satır satır oku, bozuğu atla, sonda kırp) uygular."""
    if not path.exists():
        return []
    rows = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows[-limit:] if limit else rows


def _defter_yaz(dizin: Path, ad: str, satirlar: list, sonda_yeni_satir: bool = True) -> Path:
    """`satirlar`daki her öğeyi bir satır yapar: dict ise `json.dumps`, str ise OLDUĞU GİBİ
    (bozuk satır enjeksiyonu için)."""
    p = dizin / ad
    parcalar = []
    for s in satirlar:
        parcalar.append(json.dumps(s) if isinstance(s, dict) else str(s))
    icerik = "\n".join(parcalar)
    if sonda_yeni_satir and parcalar:
        icerik += "\n"
    p.write_text(icerik)
    return p


def _rastgele_satirlar(n: int, rng: random.Random, dolgu: int = 60) -> list:
    return [{"i": i, "ts": f"2026-09-04T00:{i % 60:02d}:00Z", "level": "info",
             "msg": "".join(rng.choice("abcdefgh0123456789") for _ in range(dolgu))}
            for i in range(n)]


def _sabit_boyutlu_defter(dizin: Path, ad: str, hedef_bayt: int, dolgu: int = 100) -> Path:
    """SABİT satır uzunluklu (indeks sıfır-dolgulu) bir defter — toplam bayt İSTENEN hedefe
    DETERMİNİST olarak yaklaşır (satır boyu değişmez, tahmine gerek kalmaz). Eşik-aşımı testinde
    dosya boyutunu belirli bir ARALIĞA (`_KUYRUK_TABAN`in 1-2 katı) oturtmak için kullanılır."""
    ornek = json.dumps({"i": f"{0:07d}", "msg": "x" * dolgu})
    satir_uzunlugu = len(ornek) + 1
    n = max(1, hedef_bayt // satir_uzunlugu)
    satirlar = [{"i": f"{i:07d}", "msg": "x" * dolgu} for i in range(n)]
    return _defter_yaz(dizin, ad, satirlar)


# ================================================================================================
# D1 — EŞİTLİK: sentetik defterler, `store.read_jsonl` (yeni) == `_naif_oku` (eski referans)
# ================================================================================================

def test_bos_dosya(sandbox_state):
    p = _defter_yaz(sandbox_state, "olay.jsonl", [])
    assert store.read_jsonl("olay.jsonl", limit=50) == []
    assert store.read_jsonl("olay.jsonl", limit=50) == _naif_oku(p, limit=50)


def test_dosya_yok(sandbox_state):
    assert store.read_jsonl("hic_olusmamis.jsonl", limit=50) == []


def test_kucuk_dosya_limit_satir_sayisindan_BUYUK(sandbox_state):
    """Küçük dosya + büyük `limit` → kuyruk yolu hemen eşiğe takılıp TAM OKUMAYA düşmeli
    (dosya kuyruk bloğundan küçük); sonuç naif referansla eşit ve dosyadaki TÜM satırları taşır."""
    rng = random.Random(1)
    satirlar = _rastgele_satirlar(5, rng)
    p = _defter_yaz(sandbox_state, "olay.jsonl", satirlar)
    for limit in (1, 4, 5, 100, 4000):
        assert store.read_jsonl("olay.jsonl", limit=limit) == _naif_oku(p, limit=limit)


def test_kucuk_dosya_limit_satir_sayisindan_KUCUK(sandbox_state):
    rng = random.Random(2)
    satirlar = _rastgele_satirlar(9, rng)
    p = _defter_yaz(sandbox_state, "olay.jsonl", satirlar)
    for limit in (1, 3, 8):
        yeni = store.read_jsonl("olay.jsonl", limit=limit)
        assert yeni == _naif_oku(p, limit=limit)
        assert [r["i"] for r in yeni] == list(range(9 - limit, 9))


def test_son_satir_yeni_satirsiz(sandbox_state):
    rng = random.Random(3)
    satirlar = _rastgele_satirlar(12, rng)
    p = _defter_yaz(sandbox_state, "olay.jsonl", satirlar, sonda_yeni_satir=False)
    for limit in (1, 5, 12, 50):
        assert store.read_jsonl("olay.jsonl", limit=limit) == _naif_oku(p, limit=limit)


def test_bos_satirlar_karisik(sandbox_state):
    """Boş (yalnız boşluk) satırlar sessizce atlanır — ne bozuk sayılır ne satır sayılır,
    eski davranışla aynı (§ `_naif_oku`/`_read_jsonl_govde` ikisi de `if not line: continue`)."""
    rng = random.Random(4)
    ham = _rastgele_satirlar(10, rng)
    karisik: list = []
    for i, s in enumerate(ham):
        karisik.append(s)
        if i % 3 == 0:
            karisik.append("   ")
    p = _defter_yaz(sandbox_state, "olay.jsonl", karisik)
    for limit in (2, 7, 100):
        assert store.read_jsonl("olay.jsonl", limit=limit) == _naif_oku(p, limit=limit)


def test_bozuk_satir_karisik_kucuk_dosya(sandbox_state):
    rng = random.Random(5)
    ham = _rastgele_satirlar(15, rng)
    karisik: list = []
    for i, s in enumerate(ham):
        if i % 4 == 1:
            karisik.append("{bu gecerli json degil")
        karisik.append(s)
    p = _defter_yaz(sandbox_state, "olay.jsonl", karisik)
    for limit in (1, 6, 15, 40):
        assert store.read_jsonl("olay.jsonl", limit=limit) == _naif_oku(p, limit=limit)


def test_buyuk_dosya_TEK_BLOKTA_kuyruk_yolu_gercekten_calisir(sandbox_state):
    """Dosya kuyruk bloğundan (256 KB) belirgin büyük ve `limit` ilk blokla karşılanabilir
    ölçekte: `_read_jsonl_kuyruk` None DÖNMEMELİ (gerçekten hızlı yoldan geçmeli, sessizce
    TAM OKUMAYA düşmemeli) — aksi hâlde bu test kuyruk kodunu hiç EGZERSİZ ETMEZ."""
    rng = random.Random(6)
    satirlar = _rastgele_satirlar(7000, rng, dolgu=60)   # ~700 KB
    p = _defter_yaz(sandbox_state, "olay.jsonl", satirlar)
    assert p.stat().st_size > 512_000, "kurulum varsayımı bozuldu: dosya beklenenden küçük"
    limit = 500
    dogrudan = store._read_jsonl_kuyruk(p, "olay.jsonl", limit)
    assert dogrudan is not None, "kuyruk yolu ilk blokta yeterli satırı toplayamadı — eşik/blok varsayımı ölç"
    assert dogrudan == _naif_oku(p, limit=limit)
    assert store.read_jsonl("olay.jsonl", limit=limit) == _naif_oku(p, limit=limit)


def test_buyuk_dosya_BUYUME_ile_kuyruk_yolu_calisir(sandbox_state):
    """`limit` ilk bloğa sığmayacak kadar büyük ama dosyanın YARISINI aşmayan bir blokla
    karşılanabiliyor: `_read_jsonl_kuyruk` en az iki deneme sonra (blok 4 kat büyüyerek)
    None DEĞİL bir sonuç dönmeli — büyüme dalı da egzersiz edilsin diye."""
    rng = random.Random(7)
    satirlar = _rastgele_satirlar(50_000, rng, dolgu=60)   # ~5 MB
    p = _defter_yaz(sandbox_state, "olay.jsonl", satirlar)
    assert p.stat().st_size > 4_000_000, "kurulum varsayımı bozuldu: dosya beklenenden küçük"
    limit = 3000    # ilk blok (~256 KB) tek başına yetmez, ikinci blok (~1 MB) yeter
    dogrudan = store._read_jsonl_kuyruk(p, "olay.jsonl", limit)
    assert dogrudan is not None, "büyüme dalı hiç tetiklenmedi — sentetik boyut varsayımı ölç"
    assert dogrudan == _naif_oku(p, limit=limit)
    assert store.read_jsonl("olay.jsonl", limit=limit) == _naif_oku(p, limit=limit)


def test_buyuk_limit_esik_asimi_TAM_OKUMAYA_duser(sandbox_state):
    """Dosya `_KUYRUK_TABAN`in 1-2 katı büyüklükte (SABİT satır boyu, deterministik) — bu aralıkta
    İLK (yoklama) bloğu bile dosyanın YARISINDAN büyük sayılır (`_KUYRUK_TAM_OKUMA_ORANI`), yani
    `_read_jsonl_kuyruk` DAHA İLK denemeden ÖNCE eşiğe takılıp None dönmeli — `read_jsonl` TAM
    OKUMAYA düşer, sonuç yine de naif referansla eşit kalır (D2'nin beyanlı eşiği D1'in eşitliğini
    BOZMAZ)."""
    hedef_bayt = int(store._KUYRUK_TABAN * 1.3)   # (KUYRUK_TABAN, 2*KUYRUK_TABAN] aralığında
    p = _sabit_boyutlu_defter(sandbox_state, "olay.jsonl", hedef_bayt)
    boyut = p.stat().st_size
    assert store._KUYRUK_TABAN < boyut <= 2 * store._KUYRUK_TABAN, \
        f"kurulum varsayımı bozuldu: boyut={boyut}"
    limit = 999999   # dosyadaki satır sayısından kesinlikle büyük — asla tek blokla karşılanamaz
    dogrudan = store._read_jsonl_kuyruk(p, "olay.jsonl", limit)
    assert dogrudan is None, "bu senaryoda (İLK denemeden önce) TAM OKUMAYA düşmesi bekleniyordu"
    assert store.read_jsonl("olay.jsonl", limit=limit) == _naif_oku(p, limit=limit)


@pytest.mark.parametrize("tohum", list(range(20)))
def test_rastgele_sentetik_defterler_esitlik(sandbox_state, tohum):
    """Brief D1: "rastgele üretilmiş sentetik defterlerde (küçük/büyük, limit </> satır sayısı,
    son satır \\n'siz, boş dosya, bozuk satır) yeni == eski". Sabit tohumla YİRMİ farklı rastgele
    defter/limit kombinasyonu — determinist (CI'de her koşuda aynı defterler)."""
    rng = random.Random(1000 + tohum)
    n = rng.choice([0, 1, 3, 30, 800, 9000])
    satirlar = _rastgele_satirlar(n, rng, dolgu=rng.choice([10, 60, 200]))
    # rastgele bozuk satır enjeksiyonu
    if satirlar and rng.random() < 0.5:
        pos = rng.randrange(len(satirlar) + 1)
        satirlar = satirlar[:pos] + ["{bozuk satir " + str(tohum)] + satirlar[pos:]
    sonda_yeni_satir = rng.random() < 0.85
    p = _defter_yaz(sandbox_state, f"olay_{tohum}.jsonl", satirlar, sonda_yeni_satir=sonda_yeni_satir)
    for limit in sorted({0, 1, max(n, 1), n + 50, max(n // 2, 1)}):
        assert store.read_jsonl(f"olay_{tohum}.jsonl", limit=limit) == _naif_oku(p, limit=limit), \
            f"tohum={tohum} n={n} limit={limit}"


def test_negatif_limit_eski_davranisla_esit(sandbox_state):
    """fix-r1 Bulgu 1: eski geçiş `if limit:` negatif `limit`i de (truthy) kuyruk yoluna sokuyordu.
    `_read_jsonl_kuyruk` içindeki `len(rows) >= limit` negatif `limit` için İLK yoklama bloğunda
    HER ZAMAN doğrudur (`0 >= -5`) — döndürülen `rows[-limit:]` yalnız o (256 KB'lık) blok
    üzerinden hesaplanır; eski (doğru) davranış `rows[-limit:]`i TÜM dosya üzerinden hesaplardı.

    BÜYÜK dosya (kuyruk tabanı 256 KB'ı AŞAN) ŞART: küçük dosyada yoklama bloğu zaten dosyanın
    TAMAMINI kapsar, iki hesaplama tesadüfen eşit çıkar ve regresyon gizlenir (nitekim
    `test_rastgele_sentetik_defterler_esitlik` negatif limit denemez ve bunu yakalamaz)."""
    rng = random.Random(42)
    satirlar = _rastgele_satirlar(9000, rng, dolgu=60)   # ~700 KB — _KUYRUK_TABAN'ı (256 KB) aşar
    p = _defter_yaz(sandbox_state, "olay.jsonl", satirlar)
    assert p.stat().st_size > store._KUYRUK_TABAN, \
        "kurulum varsayımı bozuldu: dosya kuyruk tabanını aşmıyor"
    n = len(satirlar)
    for limit in (-1, -5, -(n // 2)):
        assert store.read_jsonl("olay.jsonl", limit=limit) == _naif_oku(p, limit=limit), \
            f"limit={limit}"


# ================================================================================================
# D1 (mutasyon hedefi) — ilk kısmi satırı ATMA adımının GERÇEKTEN gerekli olduğunun kanıtı
# ================================================================================================

def test_kuyruk_ilk_kismi_satiri_ATMAZSA_hayalet_satir_uretir(sandbox_state):
    """DETERMİNİST İNŞA: kuyruk bloğunun ilk (yarım) satırı atılmazsa, blok tam da bir "çöp
    öneki + geçerli JSON sayı son eki" (`999...9`) sınırına denk gelen bir dosyada, o son ek
    KENDİ BAŞINA geçerli bir JSON tamsayısı olarak ayrıştırılır — dosyanın gerçekte TEK bir
    geçerli satırı bile olmayan bu "junk" satırından HAYALET bir satır doğar.

    Kurulum: `junk_line = "z"*PADLEN + "9"*DIGLEN` (PADLEN = kuyruk taban bloğu, DIGLEN geniş bir
    tolerans penceresi) dosyanın TEK satırıdır ve TAM OKUMADA da bozuk sayılır (baştaki 'z'ler
    yüzünden) — yani dosyada `limit` kadar GEÇERLİ satır ASLA yoktur, `_read_jsonl_kuyruk` doğru
    çalışıyorsa HER blok denemesinde None dönmeli (çağıran TAM OKUMAYA düşer, 0 satır bulur).

    `f.readline()` (ilk yarım satırı atma) KALDIRILIRSA: ilk blok denemesinde seek noktası
    DIGLEN penceresinin içine düşer, atılmayan "ilk satır" `9`ların bir soneki olur — KENDİ
    BAŞINA geçerli bir JSON tamsayısıdır ve `rows`a hayalet bir satır olarak eklenir. Bu testte
    `limit`, tam olarak "gerçek satır sayısı (0) + 1" seçildiği için hayalet satır olmadan asla
    `len(rows) >= limit` sağlanamaz — mutasyon (`f.readline()` satırının kaldırılması) bu testi
    KIRMIZI yapar (elle doğrulandı, bu oturumda; store.py'deki gerçek kod DEĞİŞMEDİ)."""
    blok = store._KUYRUK_TABAN
    oran = store._KUYRUK_TAM_OKUMA_ORANI
    padlen = blok
    diglen = blok // 3
    junk = ("z" * padlen) + ("9" * diglen)
    junk_bytes = len(junk) + 1   # + "\n"

    # seek hedefi: DIGLEN penceresinin ORTASI — geniş tolerans, kesin aritmetiğe gerek yok
    s_hedef = padlen + diglen // 2
    suffix_bayt_hedef = s_hedef + blok - junk_bytes
    assert suffix_bayt_hedef > 0, "kurulum varsayımı bozuldu"

    # sabit boyutlu, GEÇERLİ JSON satırlarından oluşan bir kuyruk (dosyanın YEGÂNE geçerli
    # satırları burada yaşar) — toplam bayt suffix_bayt_hedef'e YAKLAŞIK eşit (DIGLEN toleransı
    # bayt-hassas hizalamayı GEREKSİZ kılıyor)
    satir_sablonu = json.dumps({"i": 0, "dolgu": "x" * 80})
    satir_uzunlugu = len(satir_sablonu) + 1
    suffix_sayisi = max(1, suffix_bayt_hedef // satir_uzunlugu)
    suffix = [json.dumps({"i": i, "dolgu": "x" * 80}) for i in range(suffix_sayisi)]

    p = sandbox_state / "olay.jsonl"
    p.write_text(junk + "\n" + "\n".join(suffix) + "\n")
    boyut = p.stat().st_size
    s_gercek = boyut - blok

    # KURULUM VARSAYIMLARI — ölçülür, uydurulmaz: eşik aşılmadı (kuyruk yolu denenir) VE seek
    # noktası gerçekten DIGLEN penceresinin içinde (junk satırının 'z' kısmına DEĞİL).
    assert blok < boyut and blok < boyut * oran, "eşik varsayımı tutmadı — dosya boyutunu ayarla"
    assert padlen <= s_gercek < padlen + diglen, \
        f"seek noktası ({s_gercek}) DIGLEN penceresinin ({padlen}-{padlen + diglen}) dışında"

    limit = suffix_sayisi + 1   # dosyada GERÇEKTEN bu kadar geçerli satır YOK (junk hiç sayılmaz)

    # DOĞRU DAVRANIŞ (bugünkü kod, `f.readline()` YERİNDE): junk satırı hiçbir blokta geçerli bir
    # satır üretmez (ne 'z' önekinden ne '9' sonekinden — sonek her zaman ATILIR), dosyanın toplam
    # geçerli satır sayısı `suffix_sayisi` = limit-1 < limit — HİÇBİR blok `limit`e ulaşamaz.
    sonuc = store._read_jsonl_kuyruk(p, "olay.jsonl", limit)
    assert sonuc is None, (
        "kuyruk okuma None DÖNMELİYDİ (dosyada limit kadar geçerli satır yok) ama bir sonuç "
        "üretti — ilk kısmi satırı atma adımı çalışmıyor olabilir (bkz. bu testin docstring'i)")


# ================================================================================================
# D2 — BEDEL ÖLÇÜMÜ: yerel events.jsonl (9 MB) üzerinde bayt + ms (n=5 medyan)
# ================================================================================================

def _acma_sarmalayici(sayac: dict):
    """`open()`ı bayt sayan bir sürümle DEĞİŞTİRİR — yalnız `.read()`/`.readline()` üzerinden
    (kuyruk yolunun kullandığı API'ler; tam okuma `for line in f:` KULLANIR ve bu satırı
    KAPSAMAZ — tam okumanın bayt maliyeti bu yüzden AYRI ve YAPISAL olarak `dosya boyutu`dur,
    aşağıdaki testte öyle ölçülür)."""
    orig_open = open

    def _acan(*a, **kw):
        f = orig_open(*a, **kw)
        _oread, _oreadline = f.read, f.readline

        def _read(*ra, **rkw):
            v = _oread(*ra, **rkw)
            sayac["bayt"] += len(v) if isinstance(v, (bytes, bytearray)) else len(v.encode("utf-8", "replace"))
            return v

        def _readline(*ra, **rkw):
            v = _oreadline(*ra, **rkw)
            sayac["bayt"] += len(v) if isinstance(v, (bytes, bytearray)) else len(v.encode("utf-8", "replace"))
            return v

        f.read, f.readline = _read, _readline
        return f
    return _acan


def test_bedel_kuyruk_okuma_tam_okumadan_AZ_bayt_okur(sandbox_state, monkeypatch):
    """D2 — yerel `state/events.jsonl` (9 MB, "yerel" etiketiyle) kopyalanır (canlı state'e
    dokunulmaz); limit=4000 ve limit=15000 için kuyruk okumanın GERÇEKTEN AZ bayt okuduğu
    ölçülür. SAYI İDDİASI YOK: yalnız `kuyruk_bayt < tam_bayt` — mutlak bir yüzdeye çivi
    atılmaz (donanım/dosya içeriğine göre değişir, brief D2)."""
    kaynak = REPO / "state" / "events.jsonl"
    if not kaynak.exists():
        pytest.skip("yerel state/events.jsonl yok — D2 bedel ölçümü ATLANDI (ölçülemedi, uydurulmadı)")
    hedef = sandbox_state / "events.jsonl"
    shutil.copy2(kaynak, hedef)
    tam_bayt = hedef.stat().st_size   # tam okuma dosyanın TAMAMINI baştan sona okur — YAPISAL üst sınır

    sonuclar = {}
    for limit in (4000, 15000):
        sayac = {"bayt": 0}
        monkeypatch.setattr(store, "open", _acma_sarmalayici(sayac), raising=False)
        try:
            satirlar = store.read_jsonl("events.jsonl", limit=limit)
        finally:
            monkeypatch.delattr(store, "open", raising=False)
        sonuclar[limit] = (sayac["bayt"], len(satirlar))
        print(f"D2 BAYT limit={limit}: kuyruk={sayac['bayt']} tam={tam_bayt} "
              f"oran={sayac['bayt'] / tam_bayt:.1%}")
        assert sayac["bayt"] > 0, "sayaç hiç tetiklenmedi — sarmalama çalışmıyor olabilir"
        assert sayac["bayt"] < tam_bayt, \
            f"limit={limit}: kuyruk okuma {sayac['bayt']} bayt okudu, tam dosya {tam_bayt} bayt — kazanç YOK"

    # rapor için: iki limit değerinin de gerçekten `limit` (ya da dosyadaki tüm satırlar) kadar
    # satır döndürdüğünü doğrula — bayt tasarrufu SESSİZ bir eksik-okumadan gelmiyor
    for limit, (bayt, n) in sonuclar.items():
        assert n == limit, f"limit={limit} ama {n} satır döndü"


def test_bedel_kuyruk_okuma_ms_medyan(sandbox_state):
    """D2 — süre (ms, n=5 medyan): yerel events.jsonl üzerinde limit=4000/15000 için
    `store.read_jsonl` süresi, TAM OKUMANIN (`_naif_oku`) süresinden büyük ölçüde SAPMAZ —
    sıkı bir SLA iddia edilmez (I/O gürültülüdür), yalnız kuyruk yolunun makul olduğu ölçülür."""
    kaynak = REPO / "state" / "events.jsonl"
    if not kaynak.exists():
        pytest.skip("yerel state/events.jsonl yok — D2 ms ölçümü ATLANDI (ölçülemedi, uydurulmadı)")
    hedef = sandbox_state / "events.jsonl"
    shutil.copy2(kaynak, hedef)

    def _medyan_ms(fn, n=5):
        sureler = []
        for _ in range(n):
            t0 = _time.perf_counter()
            fn()
            sureler.append((_time.perf_counter() - t0) * 1000.0)
        return statistics.median(sureler)

    for limit in (4000, 15000):
        eski_ms = _medyan_ms(lambda: _naif_oku(hedef, limit=limit))
        yeni_ms = _medyan_ms(lambda: store.read_jsonl("events.jsonl", limit=limit))
        print(f"D2 MS limit={limit}: eski(tam,naif)={eski_ms:.2f} ms yeni(kuyruk)={yeni_ms:.2f} ms")
        # rapora taşınacak ham sayı — burada sadece "makul" sınırı çiviliyoruz (aşırı yavaşlama yok)
        assert yeni_ms < eski_ms * 3.0 + 5.0, \
            f"limit={limit}: kuyruk {yeni_ms:.2f} ms, tam okuma {eski_ms:.2f} ms — beklenenden çok yavaş"


# ================================================================================================
# D3 — `/api/alerts` sunucu önbelleği: hit/miss + mtime anahtarı
# ================================================================================================

def test_alerts_ikinci_cagri_onbellekten_gelir(sandbox_state):
    from fastapi.testclient import TestClient
    from meridian import api
    c = TestClient(api.app)
    r1 = c.get("/api/alerts")
    assert r1.status_code == 200, r1.text
    assert r1.json()["onbellekten"] is False, "ilk çağrı MISS olmalıydı (kutu boş)"
    r2 = c.get("/api/alerts")
    assert r2.status_code == 200, r2.text
    assert r2.json()["onbellekten"] is True, "ikinci çağrı (aynı TTL penceresinde) HIT olmalıydı"
    # içerik (onbellekten alanı hariç) AYNI kalmalı — önbellek FARKLI bir cevap üretmemeli
    j1, j2 = dict(r1.json()), dict(r2.json())
    del j1["onbellekten"], j2["onbellekten"]
    assert j1 == j2


def test_alerts_mtime_degisince_MISS(sandbox_state):
    from fastapi.testclient import TestClient
    from meridian import api
    c = TestClient(api.app)
    r1 = c.get("/api/alerts")
    assert r1.json()["onbellekten"] is False
    r2 = c.get("/api/alerts")
    assert r2.json()["onbellekten"] is True, "önce HIT bekleniyordu (kontrol)"
    # events.jsonl'ı DEĞİŞTİR (mtime ilerler) — TTL dolmasa bile önbellek bayat sayılmalı
    store.append_jsonl("events.jsonl", {"ts": "2026-09-04T00:00:00Z", "level": "info",
                                        "event": "sentetik_olay"})
    r3 = c.get("/api/alerts")
    assert r3.status_code == 200, r3.text
    assert r3.json()["onbellekten"] is False, \
        "events.jsonl mtime'ı değişti ama önbellek HÂLÂ eski cevabı servis etti"


def test_alerts_TTL_dolunca_MISS(sandbox_state, monkeypatch):
    from fastapi.testclient import TestClient
    from meridian import api
    monkeypatch.setattr(api, "ALERTS_TTL_S", 0.05)
    c = TestClient(api.app)
    assert c.get("/api/alerts").json()["onbellekten"] is False
    _time.sleep(0.08)
    assert c.get("/api/alerts").json()["onbellekten"] is False, \
        "TTL süresi doldu ama önbellek HÂLÂ HIT diyor"
