"""research/olcumler/edg086_pano_sohbet/sayim.py — EDG-2026-086 pano sohbeti KALİTE SAYACI.

NE ÖLÇER. Kart `research/cards/EDG-2026-086-pano-sohbet-kalite.yaml`nin `olcum_plani`
maddelerinin BEŞİNİ, `state/sohbet.jsonl` defterinden:
  1. UYDURMA — cevaptaki her sayı/kimlik/yol/sembol atfı, O SATIRIN araç çıktılarından çıkarılmış
     literal atıf kümesinde (ya da OPERATÖRÜN KENDİ MESAJINDA) geçiyor mu.
  2. ARAÇ DİSİPLİNİ — şema-dışı çağrı sayısı + "metin olarak araç çağrısı" (EDG-2026-074 sınıfı).
  3. GECİKME — mesaj→cevap süresinin p50/p95'i, araç turu sayısıyla kırılımlı (tanı).
  4. KOTA — gün başı sohbet çağrı sayısının tepesi/ortalaması, dolu pencere payı, düşen zincir.
  5. ÖNERİ — `approvals.jsonl`de `kaynak=sohbet` satırlarının onay/ret/bekleme dağılımı (tanı).

BETİK HÜKÜM VERMEZ (CLAUDE.md §5: "Ölçüm kartına hüküm: Rol-1"). Eşikler karttan OKUNUR ve rapora
SAYI olarak yazılır; hiçbir çıktıda "geçti/kaldı" yoktur. Pencere dolmadan (kartın `n_alt_mesaj`
eşiği ∧ seans alt sınırı ∧ GERÇEKTEN ÖLÇÜLEN satır sayısı) markdown başlığı "HÜKÜM YOK
(betimleyici ara-rapor)"dur.

PAYDA ARAÇ ÇIKTISI + OPERATÖR MESAJIDIR. Kartın kill-list'i "uydurma sayımı araç çıktısını değil
CEVABI TEK BAŞINA okursa ölçüm geçersiz" der; payda cevabı tek başına okumaz. Mesajın paydaya
girmesi (çekişmeli inceleme, 2026-09-08) bir gevşetme DEĞİLDİR: operatör "T00842 planı ne durumda?"
diye sorduğunda modelin cevabında T00842'yi tekrarlaması MODELİN ÜRETTİĞİ bir değer değil,
KULLANICININ girdisinin yankısıdır — uydurma sayılsaydı oran hak etmeden YÜKSELİR ve donuk 0,05
eşiği sahte bir hüküm üretirdi. Yankının kendi büyüklüğü `mesaj_kaynakli` ile ADIYLA raporlanır.

SATIRLAR ÜÇ KOVAYA AYRILIR (tur-1'de üçü tek şekle katlanmıştı ve ikisi ölçüm dışındaydı):
  * SİSTEM METNİ (`sistem_metni_n`) — cevabı DÖNGÜ yazdı: kota kapısı, zincir düşmesi (`llm_dustu`),
    tur tavanı, `mesgul`. Ölçüm DIŞI; o cümlelerdeki hiçbir dizge modelin iddiası değildir. Aksi
    hâlde "kota dolu (120/120)" cümlesi iki uydurma üretirdi — ölçüm artefaktı.
  * BOŞ PAYDA (`bos_payda_n`) — MODEL konuştu ama hiçbir araç veri OKUMADI. Kartın hipotez (a)
    maddesinin kanonik arıza vakası: cevaptaki her atıf dayanaksızdır ve UYDURMA SAYILIR. Tur-1 bu
    satırları sistem şablonlarıyla aynı kovaya atıp ölçüm dışında bırakıyordu — en saf uydurma
    sınıfı ölçülmüyordu ve yanlılık eşiği GEÇME yönündeydi (EXE-2026-006 sınıfı).
  * NORMAL — en az bir başarılı araç çağrısı var.
Sınıf tavanı aşılan (`cikti_atif_kesildi`) SINIFLAR o satırda ölçülmez, SATIR ölçülür: `sayi` taşan
bir veri cevabında `kimlik`/`yol`/`sembol` paydaları tamdır. Satırın tamamını elemek, en çok sayı
taşıyan (yani uydurma riski en yüksek) cevapları seçerek elerdi.

TEK ÇIKARICI (tek-kaynak yasası). Cevap tarafı `meridian.sohbet.cikti_atiflari` ile çıkarılır —
defteri YAZAN tarafla AYNI fonksiyon; ikinci bir çıkarıcı yazılsaydı "uydurma" sayısı sınıf
tanımlarının farkını ölçerdi. Aynı gerekçeyle araç adı listesi `BEYAZ_LISTE`den, öneri kimliği
ayrımı `oneri_kimligi_mi`den, ölçülemeyen sembol kovası `belirsiz_semboller`den, SİSTEM ŞABLONU
İMZALARI `_kota_cevabi`nin KENDİ çıktısından, eşikler KARTIN KENDİSİNDEN gelir.

`state/`E YAZMAZ, `obs`A YAZMAZ. Defter `--defter` ile verilen DOSYA YOLUNDAN okunur (`store`
üzerinden değil), yani `config.STATE`e hiç dokunulmaz. Çivi:
`tests/test_edg086_sayim_v450.py` komut satırı çivisi (tmp_path'te koşar, `state/` doğmadığını
ölçer). Ağa ÇIKMAZ.

UYDURMA YASAĞI. Ölçülemeyen her değer `None` + `neden`dir, `0` DEĞİL: iki noktadan az örneklemde
gecikme yüzdelikleri, onay defteri verilmemişken öneri sayıları, hiç çağrı yokken araç oranı,
KARTTA EŞİK ANAHTARI YOKKEN pencere ve kota kapıları. "BELİRSİZ" sınıfı da buradan doğar: `%12` /
`yüzde 12` / `YÜZDE 12` / `12 %` (üç boşluğa kadar) türetilmiş bir orandır, `1,103` Türkçe
ondalık virgülü ile binlik ayracını ayırt edemediğimiz bir biçimdir, `1.000.000` binlik noktalıdır,
`MU`/`CI`/`T` evrenle kesişen ama gündelik Türkçeden ayrılamayan KISA sembol adaylarıdır, `DAL`/
`HAL`/`TER` ise aynı satırda BAĞLAM ÇAPASI (`$` · fiyat biçimi · "sembol" · satırın kaynak
künyesi) taşımayan üç harfli adaylardır — hiçbiri sayı/sembol sınıfına GİRMEZ ve uydurma
SAYILMAZ, `belirsiz` olarak ayrı sayılır. Körlüğün büyüklüğü `belirsiz_pay` ile basılır
(bedel yasası: kazanç ölçülüp bedel ölçülmezse körlüğün belirtisi hiçbir şeydir).

ÇAPA YASAĞI: bu dosyada `dosya.py` + iki nokta + satır numarası biçiminde atıf yoktur; `research/`
altındaki bir betiğe nokta'lı sembol çapası da yazılmaz (codelaw'ın sembol taraması yalnız
`meridian`/`tests`/`ops` köklerini çözer, buradaki bir çapa sessizce çürürdü).

KOMUT SATIRI (ops sözleşmesi KOMUT SATIRIdır, `main()` değil):

    .venv/bin/python research/olcumler/edg086_pano_sohbet/sayim.py \\
        --defter state/sohbet.jsonl \\
        --cikti research/olcumler/edg086_pano_sohbet/sonuc_2026-09-20.json \\
        --markdown research/olcumler/edg086_pano_sohbet/sonuc_2026-09-20.md \\
        [--onaylar state/approvals.jsonl] [--kart research/cards/EDG-2026-086-….yaml] \\
        [--baslangic 2026-09-08T00:00Z]
"""
from __future__ import annotations

import argparse
import datetime as dt
import difflib
import functools
import json
import pathlib
import re
import statistics
import sys

import yaml

SANDBOX = pathlib.Path(__file__).resolve().parent
KOK = SANDBOX.parents[2]
# BETİK DOĞRUDAN KOŞULUR (`python research/.../sayim.py`), yani `sys.path[0]` bu dizindir ve depo
# kökü yoldA DEĞİLDİR. Operatörün koşacağı BİÇİMDE çalışması için kök yola eklenir — "18 çivi
# yeşilken aracın kendisi koşmuyordu" vakasının sınıfı.
if str(KOK) not in sys.path:
    sys.path.insert(0, str(KOK))

from meridian import sohbet as _sohbet                                          # noqa: E402
from meridian.sohbet import (ATIF_SINIFLARI, BEYAZ_LISTE, CAGRI_KIND,  # noqa: E402
                             belirsiz_semboller, cikti_atiflari, oneri_kimligi_mi)

VARSAYILAN_KART = KOK / "research" / "cards" / "EDG-2026-086-pano-sohbet-kalite.yaml"

#: Seans alt sınırı. Kartın `esikler` bloğunda MAKİNE OKUNUR bir alanı YOKTUR (ölçüldü: yalnız
#: `n_alt_mesaj` var, seans sayısı `veri_penceresi` DÜZ METNİNDE yaşıyor). Sessiz bir kopya yerine
#: BAĞLI bir kopya: çivi kart metninde "10 seans" ifadesini arar, kart değişirse öter.
SEANS_ALT = 10

#: ÖLÇÜLEMEYEN SAYI BİÇİMLERİ ("belirsiz"). Beşi de cevapta GEÇER ama araç çıktısında literal
#: aranamaz: yüzde (üç yazımıyla) türetilmiş bir orandır; `1,103` Türkçe ondalık virgülü ile binlik
#: ayracını ayırt edemediğimiz bir dizgedir; `1.000.000` binlik noktalıdır ve tur-1'de ne `sayi` ne
#: `belirsiz`di — hem paydadan hem "ölçülemeyen" kovasından SESSİZCE düşüyordu.
#: BİR NOKTA GRUBU YETMEZ (`{2,}`): `1.103` ASCII araç çıktısında ONDALIKTIR ve `sayi` sınıfına
#: girer; onu da binlik saymak `belirsiz ∩ sayi ≠ ∅` yapardı (çift sayım).
#: `SAYI_RE` bu bağlamları KENDİSİ eler — iki küme AYRIKTIR ve ayrıklık çividedir (v450).
#: BOŞLUK TAVANI ÜÇTÜR VE `SAYI_RE`NİNKİYLE AYNIDIR (yeniden inceleme, 2026-09-08): tur-2'de
#: `YÜZDE 12`, `yüzde  12` ve `12  %` hem bu kovadan hem "ölçülemeyen" beyanından SESSİZCE düşüp
#: doğrudan uydurma adayı oluyordu. Tavan iki tarafta AYNI olmak ZORUNDADIR — biri diğerinden
#: geniş olsaydı aynı karakter aralığı hem `sayi` hem `belirsiz` sayılırdı (çift sayım). Dört ve
#: daha fazla boşluk ölçülmemiş bir KALINTIdır ve o hâlde değer `sayi`dır, `belirsiz` DEĞİL.
BELIRSIZ_RE = re.compile(r"%\s{0,3}\d+(?:[.,]\d+)?"
                         r"|\d+(?:[.,]\d+)?\s{0,3}%"
                         r"|(?:[Yy]üzde|YÜZDE)\s{1,3}\d+(?:[.,]\d+)?"
                         r"|\d{1,3}(?:\.\d{3}){2,}"
                         r"|\d+,\d+")

#: Onay defterindeki karar sözlüğü. `api`nin defter taramasıyla AYNI iki değer; bu betik `api`yi
#: (FastAPI uygulamasını) ithal EDEMEZ, o yüzden sözlük burada donuk ve dar tutulur.
KARAR_DEGERLERI = ("approve", "reject")


# ======================================================================================
# SİSTEM METNİ — cevabı MODEL değil DÖNGÜ yazdı
# ======================================================================================
def _ortak_blok(a, b) -> str:
    """İki dizgenin EN UZUN ORTAK bloğu. Aynı şablonun iki AYRI değişken değerle üretilmiş hâli
    verildiğinde geriye tam olarak şablonun DEĞİŞMEZ gövdesi kalır."""
    a, b = str(a or ""), str(b or "")
    if not a or not b:
        return ""
    e = difflib.SequenceMatcher(None, a, b, autojunk=False).find_longest_match(0, len(a),
                                                                              0, len(b))
    return a[e.a:e.a + e.size].strip()


@functools.lru_cache(maxsize=1)
def _sistem_imzalari() -> tuple[str, ...]:
    """Döngünün kendi yazdığı cevapların DEĞİŞMEZ PARÇALARI — `meridian.sohbet`ten TÜRETİLİR.

    ÖNEK YETMİYORDU (yeniden inceleme, 2026-09-08). Kota şablonunda değişken kısım DOKUZUNCU
    karakterde başlar, yani `split("(")[0]` en fazla "kota dolu" üretebilirdi; ayraç bir gün daha
    erkene kayarsa önek "kota" gibi AŞIRI GENİŞ bir dizgeye düşer, çivi yeşil kalır ama "kota
    durumu şöyle…" diye başlayan GERÇEK bir model cevabı sistem metni sayılıp ölçüm dışına
    atılırdı — `n_satir` sessizce düşerdi (ve pencerenin üçüncü koşulu tam da `n_satir`dır).

    İMZA İKİ SAHTE ÇAĞRININ FARKINDAN DOĞAR: aynı şablon iki AYRI değişken değerle üretilir ve en
    uzun ortak blok alınır. Elle yazılmış bir kopya değildir — şablon metni değişirse imza da
    değişir (tek-kaynak yasası). `mesgul` bir SABİTTİR, imzası kendisidir."""
    return tuple(x for x in (
        _ortak_blok(_sohbet._kota_cevabi({"bugun": 1, "tavan": 0, "neden": None}),
                    _sohbet._kota_cevabi({"bugun": 4321, "tavan": 99, "neden": None})),
        _ortak_blok(_sohbet._kota_cevabi({"bugun": None, "tavan": 0, "neden": "a"}),
                    _sohbet._kota_cevabi({"bugun": None, "tavan": 0, "neden": "bbbb"})),
        str(_sohbet.MESGUL_CEVABI).strip(),
    ) if x)


def sistem_metni_mi(satir: dict) -> bool:
    """Cevabı DÖNGÜ mü yazdı? İki kanıt sınıfı, ikisi de defterdeki alanlardan okunur:

    YAPISAL — `llm_dustu` (zincirin hiçbir ayağı cevap vermedi), `mesgul` (kilit başkasındaydı),
    `model is None` ya da hiç tur yok (kota kapısı mesajın başında kapandı), SON TURDA YAPISAL
    ÇAĞRI VAR (döngü `tool_calls` boşalınca kırılır; son tur doluysa tur tavanı doldu demektir).

    METİNSEL — zincir ayağı kotada durduğunda tur listesi doludur ve son tur çağrısızdır; o hâli
    yapısal olarak ayırt edemeyiz, cevapta `_sistem_imzalari`nın DEĞİŞMEZ parçası aranır."""
    if satir.get("llm_dustu") or satir.get("mesgul") or satir.get("model") is None:
        return True
    turlar = [t for t in (satir.get("turlar") or []) if isinstance(t, dict)]
    if not turlar:
        return True
    if int(turlar[-1].get("tool_calls") or 0) > 0:
        return True
    cevap = str(satir.get("cevap") or "")
    return any(imza in cevap for imza in _sistem_imzalari())


# ======================================================================================
# DEFTER OKUMA
# ======================================================================================
def defter_oku(yol) -> tuple[list[dict], int]:
    """(sözlük satırlar, BOZUK satır sayısı). Bozuk satır sessizce atlanmaz — sayılır ve rapora
    girer (Yasa 4): ayrıştırılamayan bir satır ölçümün GÖREMEDİĞİ bir mesajdır."""
    yol = pathlib.Path(yol)
    if not yol.exists():
        raise FileNotFoundError(f"defter bulunamadı: {yol}")
    satirlar: list[dict] = []
    bozuk = 0
    for ham in yol.read_text(encoding="utf-8").splitlines():
        ham = ham.strip()
        if not ham:
            continue
        try:
            r = json.loads(ham)
        except ValueError:
            # sessiz-yutma: bozuk JSON satırı ÖLÇÜM SONUCUDUR (defter kirliliği), çökme değil —
            # sayılır ve `n_bozuk_satir` ile rapora girer; ikinci bir kanal yok
            bozuk += 1
            continue
        if isinstance(r, dict):
            satirlar.append(r)
        else:
            bozuk += 1
    return satirlar, bozuk


def damga_ayristir(x) -> dt.datetime | None:
    """ISO damgayı UTC'ye normalize eder; ayrıştırılamazsa `None`.

    `Z` EKİ ELLE ÇEVRİLİR: `fromisoformat` 3.12'de `Z`yi kabul eder ama bu betik daha eski bir
    yorumlayıcıyla da koşabilir ve sessiz bir `ValueError` tüm satırları elerdi. Ofissiz damga
    UTC sayılır — defterin kendi damgası her zaman ofislidir, ofissiz olan yalnız operatörün
    elle yazdığı `--baslangic` olabilir."""
    metin = str(x or "").strip()
    if not metin:
        return None
    if metin.endswith(("Z", "z")):
        metin = metin[:-1] + "+00:00"
    try:
        d = dt.datetime.fromisoformat(metin)
    except ValueError:
        # sessiz-yutma: ayrıştırılamayan damga ÖLÇÜM SONUCUDUR, çökme değil — `None` dönüşü
        # sinyaldir ve çağıran onu `n_bozuk_ts` ile SAYIP rapora yazar (ikinci bir kanal yok)
        return None
    return d if d.tzinfo else d.replace(tzinfo=dt.timezone.utc)


def pencereye_al(satirlar: list[dict], baslangic: str | None) -> tuple[list[dict], int, int]:
    """(pencere içindeki satırlar, dışarıda kalan sayısı, AYRIŞTIRILAMAYAN ts sayısı).

    KARŞILAŞTIRMA AYRIŞTIRILMIŞ DAMGA ÜZERİNDEDİR, DİZGE ÜZERİNDE DEĞİL (çekişmeli inceleme,
    2026-09-08). Defterin `ts`i `+00:00` ofsetli yazılır, planın komut satırı örneği ise `Z` ekli:
    düz dizge kıyasında `'2026-09-08T00:00:00+00:00' >= '2026-09-08T00:00Z'` YANLIŞTIR (':' < 'Z')
    ve operatör planın YAZDIĞI komutu koşarsa o günün TÜM satırları sessizce pencere dışına
    düşerdi — "ölçüm bağlamı tuzağı" sınıfı sessiz yanlış sayı."""
    if not baslangic:
        return list(satirlar), 0, sum(1 for r in satirlar if damga_ayristir(r.get("ts")) is None)
    esik = damga_ayristir(baslangic)
    if esik is None:
        raise ValueError(f"--baslangic ayrıştırılamadı: {baslangic!r} — ISO damga bekleniyor "
                         "(örn. 2026-09-08T00:00Z). Sessizce boş pencere üretmek yerine durdum.")
    iceride, bozuk_ts, disarida = [], 0, 0
    for r in satirlar:
        d = damga_ayristir(r.get("ts"))
        if d is None:
            bozuk_ts += 1
        elif d >= esik:
            iceride.append(r)
        else:
            disarida += 1
    return iceride, disarida, bozuk_ts


# ======================================================================================
# 1) UYDURMA — payda ARAÇ ÇIKTISININ atıf kümesi + OPERATÖRÜN MESAJI
# ======================================================================================
def kesilen_siniflar(satir: dict) -> tuple[set[str], int]:
    """(PAYDASI EKSİK sınıflar, BEKLENMEDİK TİPTE beyan taşıyan tur sayısı).

    Eski tekil `True` biçimi DÖRT sınıfın hepsini eksik sayar — "payda tam" varsaymak sahte
    uydurma üretirdi. BEKLENMEDİK TİP DE AYNI YASAYA TABİDİR (yeniden inceleme, 2026-09-08):
    dizge/sayı/sözlük bir beyan sessizce YOK SAYILSAYDI o satır "paydası tam" muamelesi görürdü
    ve fonksiyonun kendi gerekçesi ihlal edilirdi. Fail-closed: dört sınıf da eksik sayılır ve
    sayısı ADIYLA raporlanır (`atif_beyani_bozuk_n` → `olculemeyen`)."""
    eksik: set[str] = set()
    bozuk = 0
    for tur in (satir.get("turlar") or []):
        if not isinstance(tur, dict):
            continue
        beyan = tur.get("cikti_atif_kesildi")
        if beyan is None:
            continue
        if beyan is True:
            eksik.update(ATIF_SINIFLARI)
        elif isinstance(beyan, (list, tuple)):
            eksik.update(str(x) for x in beyan)
        elif beyan is False:
            continue                       # eski biçimin "kesilmedi" hâli — payda TAM, beyan var
        else:
            bozuk += 1
            eksik.update(ATIF_SINIFLARI)
    return eksik, bozuk


def satir_paydasi(satir: dict) -> tuple[dict[str, set[str]], bool]:
    """(sınıf başına payda kümesi, HİÇ ARAÇ ÇIKTISI VAR MIYDI).

    PAYDA İKİ KAYNAKTAN BİRLEŞİR: turların `cikti_atiflari` kümeleri (araç ÇIKTISI) ve operatörün
    KENDİ mesajı. İkincisi kill-list'i ihlal etmez — payda hâlâ "cevabı tek başına" okumuyor."""
    birlesim: dict[str, set[str]] = {s: set() for s in ATIF_SINIFLARI}
    bulundu = False
    for tur in (satir.get("turlar") or []):
        if not isinstance(tur, dict):
            continue
        atiflar = tur.get("cikti_atiflari")
        if not isinstance(atiflar, dict):
            continue
        bulundu = True
        for sinif in ATIF_SINIFLARI:
            birlesim[sinif].update(atiflar.get(sinif) or ())
    return birlesim, bulundu


def kaynak_capasi(satir: dict) -> str:
    """Satırın KAYNAK künyelerinin düz metni — sembol sınıfının EK BAĞLAM ÇAPASI.

    Model bir sembolü gerçekten sorgulamışsa (`{"arac": "bar_sorgu", "anahtar": "HAL 2026-09"}`)
    cevaptaki düz yazımını da sembol saymak DOĞRUdur. ÇAPA PAYDA DEĞİLDİR: sembolü sınıfa sokar,
    "araç çıktısında geçiyor mu" sorusunu cevaplamaz — o soru `satir_paydasi`nındır."""
    parcalar = []
    for k in (satir.get("kaynaklar") or []):
        if isinstance(k, dict):
            parcalar.append(f"{k.get('arac') or ''} {k.get('anahtar') or ''}")
        else:
            parcalar.append(str(k))
    return " ".join(parcalar)


def satir_uydurmasi(satir: dict) -> dict:
    """Bir satırın uydurma muhasebesi: sınıf başına payda/uydurma + belirsiz + örnekler.

    CEVAP TARAFI BAĞLAM ÇAPASI İSTER, PAYDA İSTEMEZ (`capa_gerek`; gerekçesi çıkarıcının kendi
    docstring'inde): cevap Türkçe düzyazıdır ve `DAL`/`HAL`/`TER` orada gündelik kelimelerdir."""
    if sistem_metni_mi(satir):
        return {"olculdu": False, "kova": "sistem_metni"}

    arac_kumesi, arac_vardi = satir_paydasi(satir)
    mesaj_kumesi = cikti_atiflari(str(satir.get("mesaj") or ""))
    eksik_sinif, beyan_bozuk = kesilen_siniflar(satir)
    capa = kaynak_capasi(satir)
    cevap = str(satir.get("cevap") or "")
    cevap_atiflari = cikti_atiflari(cevap, capa_gerek=True, ek_capa=capa)

    sinif: dict[str, dict[str, int]] = {}
    ornekler: list[dict] = []
    mesaj_kaynakli: dict[str, int] = {}
    for ad in ATIF_SINIFLARI:
        if ad in eksik_sinif:
            # PAYDA EKSİK: bu SINIF ölçülmez (satırın kalan sınıfları ölçülür).
            continue
        adaylar = cevap_atiflari.get(ad) or []
        aractan = arac_kumesi[ad]
        mesajdan = set(mesaj_kumesi.get(ad) or ())
        eksik = [a for a in adaylar if a not in aractan and a not in mesajdan]
        yankı = sum(1 for a in adaylar if a not in aractan and a in mesajdan)
        sinif[ad] = {"payda": len(adaylar), "uydurma": len(eksik)}
        if yankı:
            mesaj_kaynakli[ad] = yankı
        for a in eksik:
            ornekler.append({"ts": satir.get("ts"), "oturum": satir.get("oturum"),
                             "sinif": ad, "atif": a})
    belirsiz = (set(m.group(0) for m in BELIRSIZ_RE.finditer(cevap))
                | set(belirsiz_semboller(cevap, capa_gerek=True, ek_capa=capa)))
    return {"olculdu": True, "kova": ("normal" if arac_vardi else "bos_payda"),
            "sinif": sinif, "ornekler": ornekler, "belirsiz": len(belirsiz),
            "mesaj_kaynakli": mesaj_kaynakli, "kesilen": sorted(eksik_sinif),
            "beyan_bozuk": beyan_bozuk}


def uydurma_olc(satirlar: list[dict]) -> dict:
    sinif_toplam = {s: {"payda": 0, "uydurma": 0} for s in ATIF_SINIFLARI}
    payda = uydurma = belirsiz = n_satir = 0
    sistem_metni = bos_payda = beyan_bozuk = 0
    kesilen_sayaci: dict[str, int] = {}
    mesaj_kaynakli: dict[str, int] = {}
    ornekler: list[dict] = []
    for satir in satirlar:
        sonuc = satir_uydurmasi(satir)
        if not sonuc["olculdu"]:
            sistem_metni += 1
            continue
        n_satir += 1
        bos_payda += 1 if sonuc["kova"] == "bos_payda" else 0
        beyan_bozuk += 1 if sonuc["beyan_bozuk"] else 0
        belirsiz += sonuc["belirsiz"]
        ornekler.extend(sonuc["ornekler"])
        for ad in sonuc["kesilen"]:
            kesilen_sayaci[ad] = kesilen_sayaci.get(ad, 0) + 1
        for ad, n in sonuc["mesaj_kaynakli"].items():
            mesaj_kaynakli[ad] = mesaj_kaynakli.get(ad, 0) + n
        for ad, v in sonuc["sinif"].items():
            sinif_toplam[ad]["payda"] += v["payda"]
            sinif_toplam[ad]["uydurma"] += v["uydurma"]
            payda += v["payda"]
            uydurma += v["uydurma"]
    for ad, v in sinif_toplam.items():
        # SIFIR PAYDA "ÖLÇTÜK, TEMİZ" DEMEK DEĞİLDİR: sınıfa hiç bakılamamış olabilir (Türkçe
        # ondalık virgülü sayı sınıfını çökertir, kısa adaylar sembolü). Neden ADIYLA durur.
        v["neden"] = (None if v["payda"] else
                      f"`{ad}` sınıfında hiç atıf çıkmadı — bu sınıf ÖLÇÜLMEDİ, temiz DEĞİL")
    olculebilir = payda + belirsiz
    return {
        "n_satir": n_satir, "payda": payda, "uydurma": uydurma, "belirsiz": belirsiz,
        "belirsiz_pay": ((belirsiz / olculebilir) if olculebilir else None),
        "belirsiz_pay_neden": (None if olculebilir else
                               "cevaplarda hiç atıf ya da belirsiz biçim çıkmadı — pay ÖLÇÜLEMEDİ"),
        "oran": (uydurma / payda) if payda else None,
        "oran_neden": None if payda else "cevaplarda hiç atıf çıkmadı — payda 0, oran ÖLÇÜLEMEDİ",
        "sinif_kirilimi": sinif_toplam,
        "sistem_metni_n": sistem_metni, "bos_payda_n": bos_payda,
        "atif_kesilen_sinif": kesilen_sayaci,
        "atif_beyani_bozuk_n": beyan_bozuk,
        "mesaj_kaynakli": sum(mesaj_kaynakli.values()),
        "mesaj_kaynakli_kirilimi": mesaj_kaynakli,
        "ornekler": ornekler[:20],
    }


# ======================================================================================
# 2) ARAÇ DİSİPLİNİ — şema-dışı + metin-araç (EDG-2026-074 sınıfı)
# ======================================================================================
def metin_arac_mi(satir: dict) -> bool:
    """Cevap metninde beyaz listedeki bir araç adı `ad(` biçiminde geçiyor VE cevabı üreten turda
    hiç yapısal çağrı yok. Cevabı üreten tur SONUNCUSUDUR: döngü `tool_calls` boşalınca kırılır."""
    turlar = satir.get("turlar") or []
    if not turlar or not isinstance(turlar[-1], dict):
        return False
    if int(turlar[-1].get("tool_calls") or 0) != 0:
        return False
    cevap = str(satir.get("cevap") or "")
    return any(f"{ad}(" in cevap for ad in BEYAZ_LISTE)


def arac_olc(satirlar: list[dict]) -> dict:
    """PAYDA ÇAĞRIDIR (çekişmeli inceleme, 2026-09-08). Kart hipotezi (b) "araç ÇAĞRILARININ
    ≥%90'ı şemaya uyar" der ve eşik `arac_sema_disi_ust: 0.10` o birimdedir.

    Tur-1 paydayı TUR saymıştı ve `sohbet_dongusu` cevabı üreten çağrısız turu da listeye eklediği
    için payda gerçek çağrı sayısının ~2 katıydı: aynı sentetik defterde tur paydası 0,0526,
    çağrı paydası 0,1053 — donuk 0,10 eşiğinin İKİ YANI. Ayrıca `sema_disi` ÇAĞRI, `tur_n` TUR
    saydığı için oran 1'i AŞABİLİYORDU (tek turda 3 şema-dışı çağrı + cevap turu → 1,5).

    METİN-ARAÇ TURU ÇAĞRI ÜRETMEZ: kart onu şema-dışıyla aynı orana koyduğu için paydaya KENDİSİ
    eklenir; böylece oran tanım gereği ≤1 kalır. Tur paydalı hâli TANI olarak durur."""
    tur_n = sema_disi_n = metin_arac_n = cagri_n = 0
    for satir in satirlar:
        turlar = [t for t in (satir.get("turlar") or []) if isinstance(t, dict)]
        tur_n += len(turlar)
        sema_disi_n += sum(int(t.get("sema_disi") or 0) for t in turlar)
        cagri_n += sum(int(t.get("tool_calls") or 0) for t in turlar)
        metin_arac_n += 1 if metin_arac_mi(satir) else 0
    payda = cagri_n + metin_arac_n
    return {
        "tur_n": tur_n, "sema_disi_n": sema_disi_n, "metin_arac_n": metin_arac_n,
        "toplam_tool_calls": cagri_n,
        "oran": ((sema_disi_n + metin_arac_n) / payda) if payda else None,
        "oran_paydasi": "çağrı paydalı (kart hipotezi (b) ile aynı birim)",
        "oran_neden": (None if payda else
                       "hiç araç çağrısı ve metin-araç turu yok — oran ÖLÇÜLEMEDİ"),
        "tur_paydali_oran": ((sema_disi_n + metin_arac_n) / tur_n) if tur_n else None,
    }


# ======================================================================================
# 3) GECİKME
# ======================================================================================
def _yuzdelik(veri: list[float], k: int) -> float:
    return statistics.quantiles(veri, n=100, method="inclusive")[k - 1]


def gecikme_olc(satirlar: list[dict]) -> dict:
    sureler: list[float] = []
    sure_yok = 0
    kirilim: dict[str, list[float]] = {}
    for satir in satirlar:
        s = satir.get("sure_s")
        if s is None:
            sure_yok += 1
            continue
        sureler.append(float(s))
        anahtar = str(len([t for t in (satir.get("turlar") or []) if isinstance(t, dict)]))
        kirilim.setdefault(anahtar, []).append(float(s))
    if len(sureler) < 2:
        return {"p50_s": None, "p95_s": None, "n": len(sureler), "sure_yok_n": sure_yok,
                "tur_kirilimi": {}, "neden": (f"yüzdelik için en az 2 ölçüm gerekir, {len(sureler)}"
                                              " var — p50/p95 ÖLÇÜLEMEDİ")}
    sureler.sort()
    return {
        "p50_s": _yuzdelik(sureler, 50), "p95_s": _yuzdelik(sureler, 95),
        "n": len(sureler), "sure_yok_n": sure_yok, "neden": None,
        "tur_kirilimi": {k: {"n": len(v),
                             "p50_s": (_yuzdelik(sorted(v), 50) if len(v) >= 2 else None)}
                         for k, v in sorted(kirilim.items())},
    }


# ======================================================================================
# 4) KOTA
# ======================================================================================
def kota_olc(satirlar: list[dict], tavan) -> dict:
    """`tavan` `None` ise DOLU PENCERE ÖLÇÜLEMEZ. Tur-1'de eksik eşik `or 0`la 0'a düşüyordu ve
    `bugun >= 0` her satırda doğru olduğu için `dolu_pencere_pay` 1,0 oluyordu — fail-open."""
    gunluk: dict[str, int] = {}
    olculemeyen = dolu = llm_dustu = 0
    for satir in satirlar:
        if satir.get("llm_dustu"):
            llm_dustu += 1
        bugun = satir.get("kota_bugun")
        if bugun is None:
            olculemeyen += 1
            continue
        if tavan is not None and int(bugun) >= int(tavan):
            dolu += 1
        gun = str(satir.get("ts") or "")[:10]
        gunluk[gun] = max(gunluk.get(gun, 0), int(bugun))
    tepeler = sorted(gunluk.values())
    n = len(satirlar)
    return {
        "gun_basi_max": (max(tepeler) if tepeler else None),
        "gun_basi_ort": (statistics.fmean(tepeler) if tepeler else None),
        "gun_n": len(gunluk),
        "dolu_pencere_n": (dolu if tavan is not None else None),
        "dolu_pencere_pay": ((dolu / n) if n else None) if tavan is not None else None,
        "dolu_pencere_neden": (None if tavan is not None else
                               "kartta `kota_gunluk_tavan` yok — dolu pencere ÖLÇÜLEMEDİ"),
        "llm_dustu_n": llm_dustu,
        "olculemeyen_n": olculemeyen,
        "neden": (None if tepeler else "hiçbir satırda `kota_bugun` ölçülmemiş — kota ÖLÇÜLEMEDİ"),
    }


# ======================================================================================
# 5) ÖNERİ — approvals.jsonl (tanı)
# ======================================================================================
def oneri_olc(yol, baslangic: str | None) -> dict:
    bos = {"n": None, "onaylanan": None, "reddedilen": None, "bekleyen": None}
    if yol is None:
        return {**bos, "neden": "onay defteri verilmedi (`--onaylar`) ve defterin yanında "
                                "`approvals.jsonl` yok — öneri sayımı ÖLÇÜLEMEDİ"}
    yol = pathlib.Path(yol)
    if not yol.exists():
        return {**bos, "neden": f"onay defteri bulunamadı: {yol} — öneri sayımı ÖLÇÜLEMEDİ"}
    satirlar, _ = defter_oku(yol)
    kararlar: dict[str, str] = {}
    oneriler: list[dict] = []
    for r in satirlar:
        kimlik = str(r.get("id") or "")
        karar = r.get("decision")
        if isinstance(karar, str) and karar.strip().lower() in KARAR_DEGERLERI:
            kararlar[kimlik] = karar.strip().lower()      # dosya sırası = zaman sırası, son kazanır
        elif r.get("kaynak") == CAGRI_KIND and oneri_kimligi_mi(kimlik):
            oneriler.append(r)
    if baslangic:
        oneriler, _, _ = pencereye_al(oneriler, baslangic)
    onaylanan = sum(1 for r in oneriler if kararlar.get(str(r.get("id"))) == "approve")
    reddedilen = sum(1 for r in oneriler if kararlar.get(str(r.get("id"))) == "reject")
    return {"n": len(oneriler), "onaylanan": onaylanan, "reddedilen": reddedilen,
            "bekleyen": len(oneriler) - onaylanan - reddedilen, "neden": None}


# ======================================================================================
# 6) MODEL KIRILIMI — zincir hangi künyeye düştü, o künye ne yaptı
# ======================================================================================
def model_kirilimi(satirlar: list[dict]) -> dict:
    kovalar: dict[str, list[dict]] = {}
    for satir in satirlar:
        kovalar.setdefault(str(satir.get("model") or "(olculemedi)"), []).append(satir)
    cikti = {}
    for kunye, kume in sorted(kovalar.items()):
        u = uydurma_olc(kume)
        a = arac_olc(kume)
        cikti[kunye] = {"n": len(kume), "uydurma_oran": u["oran"],
                        "uydurma_payda": u["payda"], "sema_disi_oran": a["oran"],
                        "tur_n": a["tur_n"]}
    return cikti


# ======================================================================================
# KOŞUM
# ======================================================================================
def _esik(esikler: dict, ad: str):
    """Eşiği KARTTAN okur; anahtar yoksa `None` (uydurma yasağı: eksik eşik 0 DEĞİLDİR)."""
    deger = esikler.get(ad)
    return None if deger is None else int(deger)


def calistir(*, defter, cikti=None, markdown=None, onaylar=None, kart=None,
             baslangic=None) -> dict:
    """Sayımı koşar ve sonuç sözlüğünü döner. `cikti`/`markdown` yalnız `ana`nın yazdığı yollardır;
    burada dosya YAZILMAZ (çağıran çivi saf sonucu okuyabilsin diye)."""
    defter = pathlib.Path(defter)
    kart_yolu = pathlib.Path(kart or VARSAYILAN_KART)
    kart_verisi = yaml.safe_load(kart_yolu.read_text(encoding="utf-8")) or {}
    esikler = dict(kart_verisi.get("esikler") or {})

    ham, bozuk = defter_oku(defter)
    satirlar, pencere_disi, bozuk_ts = pencereye_al(ham, baslangic)

    if onaylar is None:
        yan = defter.parent / "approvals.jsonl"
        onaylar = yan if yan.exists() else None

    oturumlar = {str(r.get("oturum") or "") for r in satirlar}
    n_mesaj, n_seans = len(satirlar), len(oturumlar)
    uydurma = uydurma_olc(satirlar)
    kota_tavani = _esik(esikler, "kota_gunluk_tavan")
    kota = kota_olc(satirlar, kota_tavani)

    n_alt = _esik(esikler, "n_alt_mesaj")
    if n_alt is None:
        pencere_doldu, pencere_neden = None, ("kartta `n_alt_mesaj` eşiği YOK — pencere kapısı "
                                              "ÖLÇÜLEMEDİ (eksik eşik 0 sayılsaydı kapı sessizce "
                                              "AÇILIRDI)")
    else:
        # ÜÇÜNCÜ KOŞUL ÖLÇÜLEN SATIR SAYISIDIR: 100 mesajın 90'ı sistem metniyse oran bir avuç
        # satıra dayanır ve "HÜKÜM YOK" başlığı hak etmeden düşerdi.
        pencere_doldu = bool(n_mesaj >= n_alt and n_seans >= SEANS_ALT
                             and uydurma["n_satir"] >= n_alt)
        pencere_neden = None

    olculemeyen: list[str] = []
    if uydurma["sistem_metni_n"]:
        olculemeyen.append(f"sistem_metni: {uydurma['sistem_metni_n']} satırın cevabını DÖNGÜ "
                           "yazdı (kota kapısı · zincir düşmesi · tur tavanı · meşgul) — o "
                           "cümlelerdeki dizgeler modelin iddiası değildir, uydurma ölçülmedi")
    if uydurma["atif_kesilen_sinif"]:
        dokum = ", ".join(f"{k}×{v}" for k, v in sorted(uydurma["atif_kesilen_sinif"].items()))
        olculemeyen.append(f"atif_kesildi: sınıf tavanı aşılan satırlar ({dokum}) — o SINIFLARIN "
                           "paydası EKSİK, yalnız o sınıflar ölçülmedi")
    if bozuk_ts:
        # GEREKÇE DALA BAĞLIDIR (yeniden inceleme, 2026-09-08). `--baslangic` verilmediğinde
        # pencere süzgeci HİÇ koşmaz ve satırların TAMAMI ölçüme girer; koşulsuz "dışarıda
        # bırakıldı" cümlesi hüküm turunda Rol-1'e paydayı hak etmeden KÜÇÜLTTÜRÜRDÜ.
        olculemeyen.append(
            f"bozuk_ts: {bozuk_ts} satırın `ts` alanı ayrıştırılamadı — pencere içinde mi "
            "dışında mı olduğu ÖLÇÜLEMEDİ, satırlar dışarıda bırakıldı"
            if baslangic else
            f"bozuk_ts: {bozuk_ts} satırın `ts` alanı ayrıştırılamadı — `--baslangic` "
            "verilmediği için pencere süzgeci HİÇ uygulanmadı ve satırlar ölçüme DAHİL edildi")
    if uydurma["atif_beyani_bozuk_n"]:
        olculemeyen.append(f"atif_beyani_bozuk: {uydurma['atif_beyani_bozuk_n']} turda "
                           "`cikti_atif_kesildi` beklenmedik tipte — o satırların DÖRT sınıfı da "
                           "eksik paydalı sayıldı (payda TAM varsaymak sahte uydurma üretirdi)")
    if kota["olculemeyen_n"]:
        olculemeyen.append(f"kota_bugun_yok: {kota['olculemeyen_n']} satırda kota sayacı "
                           "ölçülememiş (telemetri halkası bugünün içinde dolmuş)")
    if pencere_neden:
        olculemeyen.append(f"n_alt_mesaj: {pencere_neden}")
    if kota["dolu_pencere_neden"]:
        olculemeyen.append(f"kota_gunluk_tavan: {kota['dolu_pencere_neden']}")
    return {
        "olcum_zamani": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "kart": str(kart_verisi.get("card_id") or ""),
        "girdi": {"defter": str(defter), "onaylar": (str(onaylar) if onaylar else None),
                  "kart_yolu": str(kart_yolu), "baslangic": baslangic,
                  "n_ham_satir": len(ham), "n_pencere_disi": pencere_disi,
                  "n_bozuk_satir": bozuk, "n_bozuk_ts": bozuk_ts},
        "esikler": esikler,
        "n_mesaj": n_mesaj, "n_seans": n_seans,
        "pencere_doldu": pencere_doldu, "pencere_neden": pencere_neden,
        "seans_alt": SEANS_ALT,
        "uydurma": uydurma,
        "arac": arac_olc(satirlar),
        "gecikme": gecikme_olc(satirlar),
        "kota": kota,
        "oneri": oneri_olc(onaylar, baslangic),
        "model_kirilimi": model_kirilimi(satirlar),
        "olculemeyen": olculemeyen,
        "beyan": ("Bu betik SAYAR, HÜKÜM VERMEZ — eşikler kart EDG-2026-086'dan okunur ve rapora "
                  "yalnız SAYI olarak yazılır; hükmü Rol-1 aynı turda karta + K defterine işler. "
                  "Payda ARAÇ ÇIKTISI + OPERATÖRÜN MESAJIDIR (cevap tek başına okunmaz). Cevabını "
                  "DÖNGÜNÜN yazdığı satırlar (kota · zincir düşmesi · tur tavanı · meşgul) ölçüm "
                  "DIŞINDA tutulur; modelin konuşup hiç veri OKUMADIĞI satırlar BOŞ PAYDAYLA "
                  "ölçülür. Ölçülemeyen her değer None + neden'dir; `%12`, `yüzde 12`, `1,103`, "
                  "`1.000.000` ve `MU`/`T` gibi kısa sembol adayları 'belirsiz' sayılır, uydurma "
                  "SAYILMAZ."),
    }


# ======================================================================================
# MARKDOWN RAPOR
# ======================================================================================
def _sayi(x, basamak=4) -> str:
    if x is None:
        return "None"
    if isinstance(x, float):
        return f"{x:.{basamak}f}"
    return str(x)


def _esik_hucresi(esikler: dict, ad: str) -> str:
    return "ÖLÇÜLEMEDİ (kartta anahtar yok)" if esikler.get(ad) is None else str(esikler[ad])


def markdown_uret(sonuc: dict) -> str:
    e = sonuc["esikler"]
    u, a, g, k, o = (sonuc["uydurma"], sonuc["arac"], sonuc["gecikme"], sonuc["kota"],
                     sonuc["oneri"])
    satirlar = ["# EDG-2026-086 — pano sohbeti kalite sayımı", ""]
    if sonuc["pencere_doldu"] is not True:
        satirlar += ["## HÜKÜM YOK (betimleyici ara-rapor)", "",
                     (sonuc["pencere_neden"] or
                      (f"Pencere DOLMADI: n_mesaj={sonuc['n_mesaj']} (alt sınır "
                       f"{_esik_hucresi(e, 'n_alt_mesaj')}) · n_seans={sonuc['n_seans']} (alt "
                       f"sınır {sonuc['seans_alt']}) · ölçülen satır={u['n_satir']} (alt sınır "
                       f"{_esik_hucresi(e, 'n_alt_mesaj')})."))
                     + " Kartın `veri_penceresi` maddesi dolmadan hiçbir sayı eşikle "
                       "karşılaştırılmaz.", ""]
    satirlar += [f"Ölçüm zamanı: {sonuc['olcum_zamani']}",
                 f"Defter: `{sonuc['girdi']['defter']}`  ·  Kart: `{sonuc['girdi']['kart_yolu']}`",
                 f"Pencere başlangıcı: {sonuc['girdi']['baslangic'] or '—'}  ·  ham satır: "
                 f"{sonuc['girdi']['n_ham_satir']}  ·  pencere dışı: "
                 f"{sonuc['girdi']['n_pencere_disi']}  ·  bozuk satır: "
                 f"{sonuc['girdi']['n_bozuk_satir']}  ·  bozuk damga: "
                 f"{sonuc['girdi']['n_bozuk_ts']}", "",
                 "| Ölçü | Ölçülen | Kart eşiği |", "|---|---|---|",
                 f"| uydurma oranı | {_sayi(u['oran'])} | "
                 f"{_esik_hucresi(e, 'uydurma_orani_ust')} |",
                 f"| ölçülemeyen biçim payı (belirsiz) | {_sayi(u['belirsiz_pay'])} | — |",
                 f"| araç şema-dışı oranı ({a['oran_paydasi']}) | {_sayi(a['oran'])} | "
                 f"{_esik_hucresi(e, 'arac_sema_disi_ust')} |",
                 f"| gecikme p50 (s) | {_sayi(g['p50_s'], 3)} | "
                 f"{_esik_hucresi(e, 'gecikme_p50_s_ust')} |",
                 f"| gün başı kota tepesi | {_sayi(k['gun_basi_max'], 1)} | "
                 f"{_esik_hucresi(e, 'kota_gunluk_tavan')} |",
                 f"| mesaj sayısı | {sonuc['n_mesaj']} | {_esik_hucresi(e, 'n_alt_mesaj')} |",
                 f"| ölçülen satır sayısı | {u['n_satir']} | "
                 f"{_esik_hucresi(e, 'n_alt_mesaj')} |",
                 f"| seans sayısı | {sonuc['n_seans']} | {sonuc['seans_alt']} |", "",
                 "## Uydurma kırılımı", "",
                 f"payda={u['payda']} · uydurma={u['uydurma']} · belirsiz={u['belirsiz']} "
                 f"(pay {_sayi(u['belirsiz_pay'])}) · ölçülen satır={u['n_satir']} · "
                 f"sistem metni={u['sistem_metni_n']} · boş paydalı satır={u['bos_payda_n']} · "
                 f"mesaj yankısı={u['mesaj_kaynakli']}", "",
                 "| Sınıf | Payda | Uydurma | Mesaj yankısı | Payda notu |", "|---|---|---|---|---|"]
    for sinif in ATIF_SINIFLARI:
        v = u["sinif_kirilimi"][sinif]
        satirlar.append(f"| {sinif} | {v['payda']} | {v['uydurma']} | "
                        f"{u['mesaj_kaynakli_kirilimi'].get(sinif, 0)} | {v['neden'] or '—'} |")
    satirlar += ["", "## Araç disiplini · gecikme · kota · öneri", "",
                 f"- araç: tur={a['tur_n']} · çağrı={a['toplam_tool_calls']} · "
                 f"şema-dışı={a['sema_disi_n']} · metin-araç={a['metin_arac_n']} · "
                 f"tur paydalı oran (tanı)={_sayi(a['tur_paydali_oran'])}"
                 + (f" · neden: {a['oran_neden']}" if a["oran_neden"] else ""),
                 f"- gecikme: p50={_sayi(g['p50_s'], 3)} · p95={_sayi(g['p95_s'], 3)} · "
                 f"n={g['n']} · süresi yok={g['sure_yok_n']}"
                 + (f" · neden: {g['neden']}" if g["neden"] else ""),
                 f"- kota: gün tepesi={_sayi(k['gun_basi_max'], 1)} · "
                 f"gün ortalaması={_sayi(k['gun_basi_ort'], 2)} · "
                 f"dolu pencere payı={_sayi(k['dolu_pencere_pay'])} · "
                 f"zincir düştü={k['llm_dustu_n']}"
                 + (f" · neden: {k['dolu_pencere_neden']}" if k["dolu_pencere_neden"] else ""),
                 f"- öneri (tanı): n={_sayi(o['n'])} · onaylanan={_sayi(o['onaylanan'])} · "
                 f"reddedilen={_sayi(o['reddedilen'])} · bekleyen={_sayi(o['bekleyen'])}"
                 + (f" · neden: {o['neden']}" if o["neden"] else ""), "",
                 "## Model kırılımı", "", "| Künye | n | uydurma oranı | şema-dışı oranı |",
                 "|---|---|---|---|"]
    for kunye, v in sonuc["model_kirilimi"].items():
        satirlar.append(f"| {kunye} | {v['n']} | {_sayi(v['uydurma_oran'])} | "
                        f"{_sayi(v['sema_disi_oran'])} |")
    if sonuc["olculemeyen"]:
        satirlar += ["", "## Ölçülemeyen (uydurma yasağı — None + neden)"]
        satirlar += [f"- {x}" for x in sonuc["olculemeyen"]]
    if u["ornekler"]:
        satirlar += ["", "## Uydurma örnekleri (en çok 20 — elle PK'nin girdisi)", "",
                     "| ts | oturum | sınıf | atıf |", "|---|---|---|---|"]
        satirlar += [f"| {x['ts']} | {x['oturum']} | {x['sinif']} | `{x['atif']}` |"
                     for x in u["ornekler"]]
    satirlar += ["", "---", "", sonuc["beyan"]]
    return "\n".join(satirlar) + "\n"


# ======================================================================================
# CLI
# ======================================================================================
def ana(argv=None) -> int:
    ap = argparse.ArgumentParser(description="EDG-2026-086 pano sohbeti kalite sayacı")
    ap.add_argument("--defter", required=True, help="state/sohbet.jsonl yolu (SALT OKUNUR)")
    ap.add_argument("--cikti", required=True, help="JSON sonuç yolu")
    ap.add_argument("--markdown", default=None, help="isteğe bağlı markdown rapor yolu")
    ap.add_argument("--onaylar", default=None,
                    help="approvals.jsonl yolu; verilmezse defterin yanındaki dosya aranır")
    ap.add_argument("--kart", default=str(VARSAYILAN_KART), help="eşiklerin okunduğu kart")
    ap.add_argument("--baslangic", default=None,
                    help="ISO damga (Z ya da +00:00); bu andan ÖNCEKİ satırlar pencere dışıdır")
    ns = ap.parse_args(argv)

    sonuc = calistir(defter=ns.defter, onaylar=ns.onaylar, kart=ns.kart, baslangic=ns.baslangic)

    cikti_yolu = pathlib.Path(ns.cikti)
    cikti_yolu.parent.mkdir(parents=True, exist_ok=True)
    cikti_yolu.write_text(json.dumps(sonuc, indent=2, sort_keys=True, ensure_ascii=False),
                          encoding="utf-8")
    if ns.markdown:
        md_yolu = pathlib.Path(ns.markdown)
        md_yolu.parent.mkdir(parents=True, exist_ok=True)
        md_yolu.write_text(markdown_uret(sonuc), encoding="utf-8")

    u = sonuc["uydurma"]
    # PENCERE DIŞI SAYISI TERMİNALE BASILIR: operatör damga biçimi yüzünden pencereyi kaybettiyse
    # bunu raporun içinde değil, komutu koştuğu anda görmelidir (sessiz sıfır rapor sınıfı).
    print(f"yazildi: {cikti_yolu} — n_mesaj={sonuc['n_mesaj']} n_seans={sonuc['n_seans']} "
          f"pencere_disi={sonuc['girdi']['n_pencere_disi']} "
          f"olculen={u['n_satir']} pencere_doldu={sonuc['pencere_doldu']} payda={u['payda']} "
          f"uydurma={u['uydurma']} belirsiz={u['belirsiz']} oran={_sayi(u['oran'])} "
          f"metin_arac={sonuc['arac']['metin_arac_n']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(ana())
