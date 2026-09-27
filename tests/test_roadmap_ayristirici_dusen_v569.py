"""v569 · ROADMAP AYRIŞTIRICISI `|` SATIRINI SAYMADAN DÜŞÜRMEZ (TSK-235, 2026-09-27).

ÖLÇÜLEN ARIZA. `api._roadmap_ayristir` bir bölümün `|` satırlarını bloklara ayırır ve her bloğu
ayraç (`|---|`) satırlarına göre tablolara böler (`_tablolari_kur` → `_bitir`). Üç yol satırı HİÇBİR
kovaya yazmadan düşürüyordu — `sayim.tablo_atlanan_n` 0 derken satır kayıptı:

  1. **İlk başlık+ayraç çiftinden ÖNCEKİ satırlar.** Bölünmüş bir tablonun alt parçası (araya düz
     metin girmiş) ardından yalnız boş satırla YENİ bir tablo gelirse parça yeni tablonun başlığının
     üstünde kalır ve atılır. TSK-231 uygulayıcısının K4 bulgusu; v337 F/G ayakları (TSK-232) bunu
     yalnız §2 tahtası için ham sayımla yakalıyordu — öteki bölümler ve pano kördü.
  2. **Bloğun ilk satırı ayraçsa** kayıt `satir_n: 1` diyor, ayraçtan sonraki başlıksız satırlar
     sonraki tablonun başlığına kadar (sonraki tablo yoksa bloğun SONUNA kadar) düşüyordu.
  3. **Belgenin ilk `##` başlığından ÖNCE** (ve önsöz maddesi yokken) gelen tablo bütünüyle düşüyordu:
     satırı bağlayacak bölüm yoktu ve önsöz yalnız madde için açılıyordu.

Yan kusur (kayıp değil, ÇİFT sayım): art arda iki ayraç satırında ikinci ayraç yeni bir tablo
açıyor ve BİRİNCİ ayraç o tablonun "başlık" satırı oluyordu — tek satır iki yerde sayılıyordu.

ÖLÇÜM (2026-09-27, düzeltmeden ÖNCE): bugünkü `ROADMAP.md`de bu yollardan düşen satır 0 (327 tablo
biçimli satır = 26 tablo × başlık+ayraç + 275 tablo satırı; `tablo_atlanan_n` 0) ve 2026-07-31'den
beri örneklenen 129 sürümde de 0 — kusur GİZLİYDİ, veri kaybı yaşanmadı. Bu yüzden gerçek belge
çivileri düzeltmeden önce de yeşildi; ısırdıklarını enjeksiyonlu pozitif kontrol gösterir.

SÖZLEŞME (bu dosyanın çivilediği): ayrıştırıcıya giren tablo biçimli her `|` satırı (kod çiti
dışında, `|` ile başlayıp `|` ile biten, en az iki boru) TAM OLARAK BİR yere düşer — bir tablonun
başlığı, ayracı ya da satırı; ya da nedeniyle `tablo_atlanan`. `sayim.tablo_atlanan_n` (pano
`tabloAtlananN`) bu kayıtları sayar; süzgeçli sayım (`api._roadmap_say`) aynı sayıyı verir.

MUHASEBE AYRIŞTIRICIDAN BAĞIMSIZ YÜRÜR: ham sayım `api._ROADMAP_TABLO_SATIRI`/`_ROADMAP_BASLIK`
ithal ETMEZ (ortak körlük olmasın — v337 F ayağının emsali); aynı markdown kuralının ikinci okumasıdır.
"""
import itertools
import pathlib
import re
from collections import Counter

from meridian import api, config

#: Başlık deseni — ayrıştırıcıdan bağımsız ikinci okuma (bkz. modül şerhi).
_HAM_BASLIK = re.compile(r"^(#{1,6})\s+(.*)$")
_ONSOZ_BASLIGI = "(başlıksız önsöz)"


def _yuk(metin: str) -> dict:
    return api._roadmap_ayristir(metin, yol="sanal.md", bayt=len(metin.encode()),
                                 mtime=None, tam=True)


def _gez(bolum: dict):
    yield bolum
    for alt in bolum["alt_bolumler"]:
        yield from _gez(alt)


def _tablo_bicimli(satir: str) -> bool:
    k = satir.strip()
    return k.startswith("|") and k.endswith("|") and k.count("|") >= 2


def _ham_boru(metin: str) -> dict:
    """HAM SAYIM: başlık satır no (ilk `##`+ başlıktan önce `None`) → o başlığın altındaki tablo
    biçimli satır numaraları, sırayla. Kod çiti içi atlanır; `#` (seviye 1) başlık bölüm değiştirmez
    (ayrıştırıcıdaki belge-içi ayraç kuralı)."""
    sonuc: dict = {}
    cit = False
    anahtar = None
    for i, l in enumerate(metin.split("\n"), 1):
        if l.lstrip().startswith("```"):
            cit = not cit
            continue
        if cit:
            continue
        hb = _HAM_BASLIK.match(l)
        if hb:
            if len(hb.group(1)) >= 2:
                anahtar = i
            continue
        if _tablo_bicimli(l):
            sonuc.setdefault(anahtar, []).append(i)
    return sonuc


def _ayristirilan(yuk: dict) -> dict:
    """Ayrıştırıcı çıktısı: başlık satır no (önsöz → `None`) → (tablolar, atlanan kayıtları)."""
    sonuc: dict = {}
    for kok in yuk["bolumler"]:
        for b in _gez(kok):
            anahtar = None if b.get("ham_baslik") == _ONSOZ_BASLIGI else b["satir"]
            t, a = sonuc.setdefault(anahtar, ([], []))
            t.extend(b["tablolar"])
            a.extend(b.get("tablo_atlanan") or [])
    return sonuc


def _muhasebe(metin: str) -> dict:
    """Ham `|` satırı ↔ ayrıştırıcının her kovası, SATIR SATIR.

    Ayrıştırıcı ayraç satırının numarasını taşımaz; ayraç, tablo başlığının bloktaki ardılıdır ve
    blok boş satırları taşımadığı için ham listede de başlığın HEMEN ardılıdır. `tablo_atlanan`
    kaydı `satir` + `satir_n` taşır: aynı bölümün ham listesinde `satir`dan başlayan ardışık
    `satir_n` satır. `kayip`: hiçbir kovaya düşmeyen satır. `fazla`: iki kovaya birden düşen ya da
    ham listede karşılığı olmayan satır."""
    yuk = _yuk(metin)
    ham = _ham_boru(metin)
    ayr = _ayristirilan(yuk)
    kayip, fazla = {}, {}
    ham_n = kovali_n = 0
    for anahtar in set(ham) | set(ayr):
        nolar = ham.get(anahtar, [])
        konum = {n: k for k, n in enumerate(nolar)}
        kaplanan: Counter = Counter()
        tablolar, atlanan = ayr.get(anahtar, ([], []))
        for t in tablolar:
            kaplanan[t["satir"]] += 1
            k = konum.get(t["satir"])
            if k is not None and k + 1 < len(nolar):
                kaplanan[nolar[k + 1]] += 1
            for r in t["satirlar"]:
                kaplanan[r["satir"]] += 1
            kovali_n += 2 + t["satir_n"]
        for a in atlanan:
            k = konum.get(a["satir"])
            if k is None:
                kaplanan[a["satir"]] += 2          # ham listede yok → fazla
                continue
            for n in nolar[k:k + a["satir_n"]]:
                kaplanan[n] += 1
            kovali_n += a["satir_n"]
        ham_n += len(nolar)
        eksik = [n for n in nolar if kaplanan[n] == 0]
        cift = sorted(n for n, c in kaplanan.items() if c > 1 or n not in konum)
        if eksik:
            kayip[anahtar] = eksik
        if cift:
            fazla[anahtar] = cift
    return {"yuk": yuk, "kayip": kayip, "fazla": fazla, "ham_n": ham_n, "kovali_n": kovali_n}


def _muhasebe_mesaji(m: dict, metin: str) -> str:
    satirlar = metin.split("\n")
    parca = [f"ham tablo biçimli satır {m['ham_n']} ↔ kovalı {m['kovali_n']}"]
    for ad, kume in (("KAYIP", m["kayip"]), ("FAZLA", m["fazla"])):
        for anahtar, nolar in sorted(kume.items(), key=lambda x: (x[0] is not None, x[0] or 0)):
            bas = satirlar[anahtar - 1][:70] if anahtar else "(ilk başlıktan önce)"
            parca.append(f"  · {ad} [{bas}]: " + ", ".join(
                f"{n}:{satirlar[n - 1].strip()[:50]}" for n in nolar[:12]))
    return "\n".join(parca)


def _atlanan_toplami(yuk: dict) -> int:
    return sum(len(b.get("tablo_atlanan") or [])
               for kok in yuk["bolumler"] for b in _gez(kok))


def _bolum(yuk: dict) -> dict:
    return yuk["bolumler"][0]


# =================================================================================================
# GERÇEK BELGE
# =================================================================================================

def test_gercek_roadmap_boru_muhasebesi_kayip_sifir():
    """Bugünkü `ROADMAP.md`nin her tablo biçimli satırı TAM OLARAK bir kovada; sayım eşit."""
    metin = (pathlib.Path(config.ROOT) / "ROADMAP.md").read_text(encoding="utf-8")
    m = _muhasebe(metin)
    assert m["ham_n"] >= 100, f"ham sayım körleşmiş olabilir: {m['ham_n']} satır"
    assert not m["kayip"] and not m["fazla"], _muhasebe_mesaji(m, metin)
    assert m["ham_n"] == m["kovali_n"], _muhasebe_mesaji(m, metin)


def test_gercek_roadmap_sayac_agacla_ve_suzgecli_sayimla_esit():
    metin = (pathlib.Path(config.ROOT) / "ROADMAP.md").read_text(encoding="utf-8")
    yuk = _yuk(metin)
    n = _atlanan_toplami(yuk)
    assert yuk["sayim"]["tablo_atlanan_n"] == n
    assert api._roadmap_say(yuk["bolumler"])["tablo_atlanan_n"] == n


def test_gercek_roadmap_enjekte_yetim_satir_sayilarak_atlanir():
    """YOL-TUTARLI POZİTİF KONTROL: bugünkü belgede bu sınıftan satır YOK (ölçüldü 2026-09-27),
    dolayısıyla yukarıdaki iki çivi düzeltmeden önce de yeşildi. Gerçek belgenin bir tablosunun
    başlığının HEMEN üstüne (bellekteki kopyaya, dosyaya DEĞİL) bir `|` satırı enjekte edilir:
    satır sayılarak `tablo_atlanan`a düşmeli, tablolar değişmemeli, muhasebe tam kalmalı."""
    metin = (pathlib.Path(config.ROOT) / "ROADMAP.md").read_text(encoding="utf-8")
    satirlar = metin.split("\n")
    once = _yuk(metin)

    def _blok_basi(no: int) -> bool:          # başlığın üstündeki ilk dolu satır `|` değil
        k = no - 2
        while k >= 0 and not satirlar[k].strip():
            k -= 1
        return k < 0 or not _tablo_bicimli(satirlar[k])

    hedef = next(t["satir"] for kok in once["bolumler"] for b in _gez(kok)
                 for t in b["tablolar"] if _blok_basi(t["satir"]))
    enjekte = "\n".join(satirlar[:hedef - 1] + ["| enjekte | yetim satır |"] + satirlar[hedef - 1:])
    m = _muhasebe(enjekte)
    assert not m["kayip"] and not m["fazla"], _muhasebe_mesaji(m, enjekte)
    sonra = m["yuk"]["sayim"]
    assert sonra["tablo_atlanan_n"] == once["sayim"]["tablo_atlanan_n"] + 1
    assert (sonra["tablo_n"], sonra["tablo_satir_n"]) == (once["sayim"]["tablo_n"],
                                                           once["sayim"]["tablo_satir_n"])
    yeni = [a for kok in m["yuk"]["bolumler"] for b in _gez(kok)
            for a in b.get("tablo_atlanan") or [] if a["satir"] == hedef]
    assert [a["satir_n"] for a in yeni] == [1], yeni


# =================================================================================================
# SENTETİK — her sınıf ayrı
# =================================================================================================
_BAS = "# T\n## §9 SINAMA\n"


def _satir_no(metin: str, parca: str) -> int:
    return next(i for i, l in enumerate(metin.split("\n"), 1) if parca in l)


def test_ayrac_oncesi_boru_satiri_atlanana_duser_ve_sayilir():
    """Sınıf 1'in en yalın hâli: başlık+ayraç çiftinin ÜSTÜNDE başka bir `|` satırı."""
    metin = _BAS + "| yetim | satır |\n| h1 | h2 |\n|---|---|\n| a | b |\n"
    m = _muhasebe(metin)
    assert not m["kayip"] and not m["fazla"], _muhasebe_mesaji(m, metin)
    b = _bolum(m["yuk"])
    assert [t["basliklar"] for t in b["tablolar"]] == [["h1", "h2"]]
    assert [r["hucreler"] for r in b["tablolar"][0]["satirlar"]] == [["a", "b"]]
    at = b["tablo_atlanan"]
    assert [(a["satir"], a["satir_n"]) for a in at] == [(_satir_no(metin, "yetim"), 1)]
    assert at[0]["neden"].strip()
    assert m["yuk"]["sayim"]["tablo_atlanan_n"] == 1


def test_bolunmus_tablo_ardindan_yeni_baslik_parca_atlanana_duser():
    """K4 bulgusunun kendisi (v337 G ikinci ayağının sentetiği): not satırıyla bölünen parça,
    ardından boş satır ve yeni bir tablo. Parça (iki satır) sayılarak `tablo_atlanan`a düşer."""
    metin = (_BAS + "| id | ad |\n|---|---|\n| T1 | bir |\n"
             "Not: araya düşen düzyazı.\n"
             "| T2 | iki |\n| T3 | üç |\n\n"
             "| id | ad |\n|---|---|\n| T4 | dört |\n")
    m = _muhasebe(metin)
    assert not m["kayip"] and not m["fazla"], _muhasebe_mesaji(m, metin)
    b = _bolum(m["yuk"])
    assert [[r["hucreler"][0] for r in t["satirlar"]] for t in b["tablolar"]] == [["T1"], ["T4"]]
    assert [(a["satir"], a["satir_n"]) for a in b["tablo_atlanan"]] == [(_satir_no(metin, "T2"), 2)]
    assert m["yuk"]["sayim"]["tablo_atlanan_n"] == 1


def test_ayrac_ilk_satir_basliksiz_parca_tamami_sayilir():
    """Sınıf 2: başlık satırı metinle ayrılmış; ikinci blok ayraçla başlıyor. Ayraç + altındaki
    başlıksız satırlar TEK kayıt ve `satir_n` hepsini kapsar (eski hâl: 1)."""
    metin = (_BAS + "| h1 | h2 |\nara metin\n|---|---|\n| a | b |\n| c | d |\n")
    m = _muhasebe(metin)
    assert not m["kayip"] and not m["fazla"], _muhasebe_mesaji(m, metin)
    b = _bolum(m["yuk"])
    assert b["tablolar"] == []
    assert [(a["satir"], a["satir_n"]) for a in b["tablo_atlanan"]] == [
        (_satir_no(metin, "h1"), 1), (_satir_no(metin, "---"), 3)]


def test_ayrac_ilk_satir_ardindan_tablo_gelince_parca_sonraki_basliga_kadar():
    metin = (_BAS + "ara metin\n|---|---|\n| a | b |\n| h1 | h2 |\n|---|---|\n| e | f |\n")
    m = _muhasebe(metin)
    assert not m["kayip"] and not m["fazla"], _muhasebe_mesaji(m, metin)
    b = _bolum(m["yuk"])
    assert [[r["hucreler"][0] for r in t["satirlar"]] for t in b["tablolar"]] == [["e"]]
    assert [(a["satir"], a["satir_n"]) for a in b["tablo_atlanan"]] == [
        (_satir_no(metin, "---"), 2)]


def test_ardisik_iki_ayrac_cift_sayilmaz():
    """Yan kusur: ikinci ayraç tablo AÇMAZ (üstünde başlık yok, ayraç var); satır değildir,
    sayılarak `tablo_atlanan`a düşer. Tablonun satırları tabloda kalır."""
    metin = _BAS + "| h1 | h2 |\n|---|---|\n|:-:|:-:|\n| a | b |\n"
    m = _muhasebe(metin)
    assert not m["kayip"] and not m["fazla"], _muhasebe_mesaji(m, metin)
    b = _bolum(m["yuk"])
    assert [t["basliklar"] for t in b["tablolar"]] == [["h1", "h2"]]
    assert [r["hucreler"] for r in b["tablolar"][0]["satirlar"]] == [["a", "b"]]
    assert [(a["satir"], a["satir_n"]) for a in b["tablo_atlanan"]] == [(_satir_no(metin, ":-:"), 1)]


def test_ilk_basliktan_once_tablo_onsoze_duser():
    """Sınıf 3: `##` başlığından önce tablo. Önsöz bölümü madde için olduğu gibi tablo için de açılır."""
    metin = "# T\n\n| h1 | h2 |\n|---|---|\n| a | b |\n\n## §1 BÖLÜM\n- madde\n"
    m = _muhasebe(metin)
    assert not m["kayip"] and not m["fazla"], _muhasebe_mesaji(m, metin)
    onsoz = m["yuk"]["bolumler"][0]
    assert onsoz["ham_baslik"] == _ONSOZ_BASLIGI
    assert [r["hucreler"] for r in onsoz["tablolar"][0]["satirlar"]] == [["a", "b"]]
    assert m["yuk"]["sayim"]["tablo_satir_n"] == 1


# ---- DEĞİŞMEYENLER (bedel yasası: düzeltme normal tabloya dokunmuyor) ---------------------------

def test_normal_tablo_degismez():
    metin = _BAS + "| h1 | h2 |\n|---|---|\n| a | b |\n\n| c | d |\n| e | f |\n"
    m = _muhasebe(metin)
    assert not m["kayip"] and not m["fazla"], _muhasebe_mesaji(m, metin)
    b = _bolum(m["yuk"])
    assert [r["hucreler"][0] for r in b["tablolar"][0]["satirlar"]] == ["a", "c", "e"]
    assert "tablo_atlanan" not in b and m["yuk"]["sayim"]["tablo_atlanan_n"] == 0


def test_iki_ardisik_tablo_degismez():
    """Arada metin yok: ikinci tablonun başlığı birincinin son satırı DEĞİL, kendi başlığıdır."""
    metin = _BAS + "| h1 | h2 |\n|---|---|\n| a | b |\n| c | d |\n| k1 | k2 |\n|---|---|\n| e | f |\n"
    m = _muhasebe(metin)
    assert not m["kayip"] and not m["fazla"], _muhasebe_mesaji(m, metin)
    b = _bolum(m["yuk"])
    assert [(t["basliklar"], [r["hucreler"][0] for r in t["satirlar"]]) for t in b["tablolar"]] == [
        (["h1", "h2"], ["a", "c"]), (["k1", "k2"], ["e"])]
    assert "tablo_atlanan" not in b


def test_not_bloklu_tablo_degismez_ve_icindeki_not_parcayi_sayar():
    """Tablonun ALTINDAKİ not bloğu (düz metin + alıntı) tabloyu bozmaz; tablonun İÇİNE yazılan not
    alttaki satırları eski sınıfla ('ayraç yok') sayılı olarak atlatır — sessiz değil."""
    alt = _BAS + "| h1 | h2 |\n|---|---|\n| a | b |\n| c | d |\nNot: tablo altı.\n> alıntı notu\n"
    m = _muhasebe(alt)
    assert not m["kayip"] and not m["fazla"], _muhasebe_mesaji(m, alt)
    b = _bolum(m["yuk"])
    assert b["tablolar"][0]["satir_n"] == 2 and "tablo_atlanan" not in b

    ic = _BAS + "| h1 | h2 |\n|---|---|\n| a | b |\n> not tablonun içinde\n| c | d |\n| e | f |\n"
    m = _muhasebe(ic)
    assert not m["kayip"] and not m["fazla"], _muhasebe_mesaji(m, ic)
    b = _bolum(m["yuk"])
    assert b["tablolar"][0]["satir_n"] == 1
    assert [(a["satir"], a["satir_n"]) for a in b["tablo_atlanan"]] == [(_satir_no(ic, "| c |"), 2)]


# ---- SAYAÇ ---------------------------------------------------------------------------------------

def test_sayac_yeni_siniflari_sayar_suzgecli_sayim_ayni():
    """`sayim.tablo_atlanan_n` = ağaçtaki kayıt sayısı = `_roadmap_say` (pano `?bolum=` yolu).
    Bu belgede kayıtların ÜÇÜ yeni sınıftır (ayraç öncesi · ayraç-ilk parça · ardışık ayraç)."""
    metin = (_BAS + "| yetim | satır |\n| h1 | h2 |\n|---|---|\n| a | b |\n"
             "ara metin\n|---|---|\n| c | d |\n"
             "ara metin\n| k1 | k2 |\n|---|---|\n|---|---|\n| e | f |\n")
    yuk = _yuk(metin)
    assert _atlanan_toplami(yuk) == 3
    assert yuk["sayim"]["tablo_atlanan_n"] == 3
    assert api._roadmap_say(yuk["bolumler"])["tablo_atlanan_n"] == 3


# ---- SINIF ÇİVİSİ: küçük belgelerin TAMAMI --------------------------------------------------------
_SEMBOL = {"R": "| r{i} | x |", "A": "|---|---|", "T": "düz metin {i}", "B": "", "H": "### alt {i}"}


def test_sinif_civisi_kucuk_belgelerin_tamaminda_kayip_ve_cift_yok():
    """Beş satır türünün (tablo satırı · ayraç · düz metin · boş · alt başlık) 1–5 uzunluktaki her
    dizilimi, `##` başlıklı ve başlıksız (önsöz) iki önekle. Tek bir örneği düzeltip sınıfı açık
    bırakmak bu deponun ölçülmüş hatasıdır; burada sınıfın küçük evreni TAMAMEN taranır."""
    kotu = []
    for onek in ("# T\n## §9 S\n", "# T\n"):
        for uz in range(1, 6):
            for dizi in itertools.product("RATBH", repeat=uz):
                metin = onek + "\n".join(_SEMBOL[s].format(i=i) for i, s in enumerate(dizi)) + "\n"
                m = _muhasebe(metin)
                if m["kayip"] or m["fazla"] or m["ham_n"] != m["kovali_n"]:
                    kotu.append((onek.count("#") > 1, "".join(dizi), m["kayip"], m["fazla"]))
                elif m["yuk"]["sayim"]["tablo_atlanan_n"] != _atlanan_toplami(m["yuk"]):
                    kotu.append((onek.count("#") > 1, "".join(dizi), "sayaç", None))
    assert not kotu, f"{len(kotu)} dizilimde kayıp/çift/sayaç: " + "; ".join(map(str, kotu[:15]))
