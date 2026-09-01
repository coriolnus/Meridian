"""mukerrerlik.py — YANSIMA MÜKERRERLİK KAPISI: bir öneri DOĞMADAN önce akıbet defterine bak.

SORUN (ölçüldü 2026-09-01, ilk akıbet karar turu): 22 önerinin ~%45'i BELLEK YOKLUĞU israfıydı —
daha önce doğmuş bir öneriyi yeniden doğuran, zaten var olanı isteyen ya da çözülmüş bir kalemi
yeniden isteyen satırlar. Kök neden tek: öneri üretilirken akıbet defterine HİÇ BAKILMIYORDU.
Reddedilmiş bir fikir, reddedildiğini söyleyecek hiçbir yer olmadığı için ertesi tur yeniden
doğuyordu. Başarı ölçüsü DONUK ve plana yazılı: israf %45 → ≤%10 (sonraki karar turunda ölçülür).

NE YAPAR: `mukerrer_mi(metin)` → `{"mukerrer", "eslesen_id", "benzerlik", "neden"}`. Modül HİÇBİR
ŞEYİ BASTIRMAZ — hüküm verir; bastırma kararı çağıranındır (`nous_eval._mukerrer_ele`).

FAIL-OPEN, BEYANLA. Defter okunamıyorsa hüküm `None`dur ve bastırma YOKTUR. Ölçülemeyen bir
benzerlikle öneri bastırmak, sahte bir hüküm vermek olurdu; uydurma yasağı burada "sıfır yazma,
bilmiyorum yaz" biçimini alır. Aynı disiplin üç ölçülemez hâlin HEPSİNDE geçerlidir: defter
okunamadı · defter boş (karşılaştırma kümesi yok) · metin jetonsuz.

KARŞILAŞTIRMA KÜMESİ İKİ KAYNAKTAN GELİR (Rol-1 hükmü 2026-09-01) — ve bu bir genişletme değil,
kapsamın DÜZELTİLMESİDİR: ölçülen israfın ANA sınıfı hermes'in KENDİ eski önerilerini yeniden
üretmesiydi, ama o önerilerin doğum metinleri akıbet defterinde YAŞAMAZ.
  · `oneri_akibet.jsonl` (`KAYNAK_DEFTER`) — rol1/operatör doğumları + TÜM kaynakların karar
    satırları. Kimlik uzayı `AKB-####`.
  · `improvement_proposals.jsonl` (`KAYNAK_DOGUM`) — N-serisi (hermes) doğum kayıtları; adı
    `nous_eval.PROPOSALS_FILE`den TÜRETİLİR, kopyalanmaz. Kimlik uzayı `N#####`.
İki kimlik uzayı olduğu için eşleşme raporu `eslesen_kaynak` etiketi taşır: etiketsiz bir id
hangi deftere bakılacağını söylemez ve denetim yolu kırılır.

AÇIK + KARARLI ÖNERİLERİN TAMAMI kümededir. Reddedilmiş bir fikri kümeden çıkarmak, "reddedildi"
bilgisini kullanmamak demekti — oysa israfın ölçülen bir başka biçimi tam olarak reddedilmiş
fikrin yeniden doğmasıdır. Kimliği OLMAYAN satır kümeye GİRMEZ (her iki kaynakta da): kimliksiz
eşleşme denetlenemez bir bastırma üretirdi (obs satırı "neye benzedi" sorusunu cevaplayamazdı) ve
`ops/akibet.py::akibet_turet` de kimliksiz satırı `olculemeyen` sayar — aynı disiplin, aynı yön.

KISMİ KÖRLÜK TAM KÖRLÜK DEĞİLDİR: bir kaynak okunamazsa öteki kümeye girmeye DEVAM eder, hüküm
okunabilenle verilir ve okunamayan kaynak `olculemeyen`de ADIYLA durur (çağıran loglar). Hüküm
`None` YALNIZ hiçbir kaynak okunamadığında ya da metin jetonsuz olduğunda verilir.

SIRA TAŞIYICIDIR: kapı `nous_eval._oneri_kaydet`ten ÖNCE koşar. Sonra koşsaydı her öneri kendi
yeni doğum satırıyla 1.0 benzerlik yakalar ve sistem HİÇBİR öneri üretemezdi — çivili
(`test_kapi_KOPRUDEN_ve_DEFTER_YAZIMINDAN_once_kosar_AST` + davranış kardeşi).

OKUR: yukarıdaki iki defter — YALNIZ OKUR.
YAZAR: hiçbir defter; yalnız hükmünü döner (olay satırını çağıran basar).
"""
from __future__ import annotations

import re
import unicodedata

from . import store

#: DEFTERİN TABAN ADI — `store` bunu `config.STATE` altında çözer. `ops/akibet.py` aynı defteri
#: A1'deki MUTLAK yolla tanır ve `meridian`i İTHAL EDEMEZ (obs'a ulaşır, canlı deftere yazardı):
#: kopya kaçınılmazdır, bu yüzden ayrışma ÇİVİLİDİR (test_yansima_mukerrerlik_v352).
DEFTER = "oneri_akibet.jsonl"

# EŞİK BİR KARARDIR, BİR AYAR DEĞİL. 0.6 ilk karar turundaki (2026-09-01) mükerrer çiftleri
# yakalayacak kadar gevşek, "aynı alan hakkında farklı istek" çiftlerini geçirecek kadar sıkı
# seçildi; ÖLÇÜMLE ayarlanacak (yeni eşik = yeni kart, eşik sonradan değişmez yasası). Tek sayı,
# tek yer: ikinci bir eşik sabiti doğduğu gün iki gerçek doğar.
ESIK = 0.6

#: Bastırma olayı — çağıran basar (Yasa 6: obs'un okuyucusu var).
OLAY_BASTIRILDI = "reflect_mukerrer_bastirildi"
#: Ölçülemedi olayı — körlük SESSİZ kalmaz; fail-open bir muafiyet değil, KAYDA GEÇEN bir hâldir.
OLAY_OLCULEMEDI = "reflect_mukerrer_olculemedi"
#: `nous_eval` kalite kapısının düşme-neden anahtarı (koşu kaydı → pano).
DUSME_NEDENI = "mukerrer"

#: KAYNAK ETİKETLERİ. İki defter İKİ AYRI kimlik uzayı kullanır (`AKB-####` · `N#####`); etiketsiz
#: bir `eslesen_id` hangi deftere bakılacağını söylemez ve denetim yolu kırılır.
KAYNAK_DEFTER = "defter"    # oneri_akibet.jsonl — rol1/operatör doğumları + tüm karar satırları
KAYNAK_DOGUM = "dogum"      # improvement_proposals.jsonl — N-serisi (hermes) doğum kayıtları

NEDEN_DEFTER_BOS = ("her iki kaynak da boş — karşılaştırma kümesi YOK, benzerlik ölçülmedi "
                    "(sıfır ile 'bilmiyorum' aynı şey değildir)")
NEDEN_METIN_YOK = "öneri metni jetonsuz (boş ya da yalnız noktalama) — benzerlik ölçülemez"

#: TÜRKÇE'NİN NFKD'YE TESLİM OLMAYAN HARFİ. `ş`/`ğ`/`ü`/`ö`/`ç`/`İ` ayrıştırılıp birleşen
#: işaretleri atılınca ASCII karşılığına düşer; `ı` (noktasız i) AYRIŞMAZ ve jeton süzgecinde
#: SESSİZCE SİLİNİRDİ — "sayıları" beklenen `sayilari` yerine `sayar` olurdu. Açık eşleme.
_TR = str.maketrans({"ı": "i", "I": "i"})

#: JETONLAYICI. Önce SAYI (ondalıklı hâliyle BÜTÜN), sonra harf/rakam dizisi. Sıra taşıyıcıdır:
#: düz bir noktalama-silici `0.6`yı `0` ve `6` diye ikiye bölerdi ve "eşiği 0.6 yap" ile
#: "eşiği 0.9 yap" %80 benzer görünürdü — sayıyı korumak, TAM korumak demektir.
_JETON = re.compile(r"\d+(?:[.,]\d+)+|[a-z0-9]+")


def jetonla(metin: str | None) -> frozenset[str]:
    """Metni karşılaştırılabilir jeton kümesine çevirir: büyük harf, noktalama ve TÜRKÇE AKSAN
    yutulur; SAYI ondalığıyla birlikte korunur.

    Aksan yutulması bir kolaylık değil kapının işlevidir: "eşiği" ile "esigi" iki ayrı fikir
    sayılsaydı, kapı mükerrerin en sık biçimini (aynı isteğin aksansız yeniden yazımı) kaçırırdı.
    """
    if not metin:
        return frozenset()
    duz = unicodedata.normalize("NFKD", str(metin)).translate(_TR).lower()
    duz = "".join(c for c in duz if not unicodedata.combining(c))
    return frozenset(_JETON.findall(duz))


def benzerlik(a: frozenset[str], b: frozenset[str]) -> float:
    """İki jeton kümesinin Jaccard benzerliği. Kümelerden biri boşsa 0.0 — çağıran o hâli ZATEN
    'ölçülemedi' diye ayırmıştır (buraya boş küme yalnız defter satırından gelebilir)."""
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _dogum_defteri() -> str:
    """N-serisi doğum defterinin adı — `nous_eval.PROPOSALS_FILE`den TÜRETİLİR, kopyalanmaz.

    GECİKMELİ İTHAL ZORUNLU: `nous_eval` bu modülü ÜST DÜZEYDE ithal eder (kapıyı o çağırır);
    buradan üst düzeyde ona dönmek karşılıklı bir ithal döngüsü olurdu. İkinci bir literal ise
    tek-kaynak ihlali olurdu: defteri YAZAN sabit ile kapının OKUDUĞU ad sessizce ayrışabilirdi
    ve kapı bir gün var olmayan bir dosyaya bakıp hiçbir şey bastırmazdı."""
    from . import nous_eval
    return nous_eval.PROPOSALS_FILE


#: KAYNAK KAYDI — (etiket, defter adını veren çağrı, satırdaki KİMLİK alanı). Metin alanı ikisinde
#: de `oneri`dir (ölçüldü: `ops/akibet.py` doğum satırı ve `nous_eval._oneri_kaydet` satırı aynı adı
#: kullanıyor). Yeni bir kaynak eklendiği gün BURAYA eklenir; tarama tek yerden türer.
_KAYNAKLAR = ((KAYNAK_DEFTER, lambda: DEFTER, "oneri_id"),
              (KAYNAK_DOGUM, _dogum_defteri, "id"))


def _adaylar() -> tuple[list[tuple[str, str, frozenset[str]]], dict[str, str], int]:
    """→ ([(kimlik, kaynak, jetonlar)...], {kaynak: ölçülemedi_nedeni}, okunabilen_kaynak_sayısı)

    KISMİ KÖRLÜK TAM KÖRLÜK DEĞİLDİR: bir kaynak okunamazsa öteki kümeye GİRMEYE DEVAM EDER ve
    okunamayan kaynak ADIYLA `olculemeyen`e yazılır. Okunabilen kaynak SAYISI ayrıca döner çünkü
    "hepsi okundu ama hepsi boş" (meşru hâl, hüküm verilebilir) ile "hiçbiri okunamadı"
    (ölçülemedi, fail-open) aynı boş listeye çöker — ayrımı sayı taşır.

    Kimliği ya da metni olmayan satır kümeye GİRMEZ (modül docstring'i: denetlenemez bastırma
    üretirdi) ve bu kural İKİ kaynakta da aynıdır — asimetri kapının bir yarısını denetlenemez
    bırakırdı."""
    out: list[tuple[str, str, frozenset[str]]] = []
    olculemeyen: dict[str, str] = {}
    okunan = 0
    for kaynak, ad_ver, kimlik_alani in _KAYNAKLAR:
        ad = ad_ver()
        try:
            satirlar = store.read_jsonl(ad)
        except OSError as e:
            # sessiz-yutma: kaynak okunamadığında hüküm UYDURULMAZ — istisna mesajı `olculemeyen`
            # kaydına ADIYLA taşınır, çağıran onu loglar ve öteki kaynakla devam edilir; yutulan
            # bilgi yok, yalnız bu kaynak karşılaştırmadan düşer.
            olculemeyen[kaynak] = (f"{ad} okunamadı ({type(e).__name__}: {e}) — bu kaynak "
                                   f"karşılaştırmaya GİRMEDİ")
            continue
        okunan += 1
        for r in satirlar:
            if not isinstance(r, dict):
                continue
            kimlik = str(r.get(kimlik_alani) or "").strip()
            jet = jetonla(r.get("oneri"))
            if kimlik and jet:
                out.append((kimlik, kaynak, jet))
    return out, olculemeyen, okunan


def mukerrer_mi(metin: str | None) -> dict:
    """→ {"mukerrer": bool|None, "eslesen_id": str|None, "eslesen_kaynak": str|None,
          "benzerlik": float|None, "neden": str|None, "olculemeyen": {kaynak: neden}}

    `mukerrer=None` ÖLÇÜLEMEDİ demektir — YALNIZ İKİ HÂLDE: hiçbir kaynak okunamadı, ya da metin
    jetonsuz. Çağıran bu hâlde BASTIRMAZ. `mukerrer=False` ölçülmüş bir hükümdür: `benzerlik`
    eşiğin ne kadar altında kalındığını söyler ve eşiğin ölçümle ayarlanabilmesinin tek girdisidir.

    `olculemeyen` KISMİ KÖRLÜĞÜ TAŞIR ve hükümden BAĞIMSIZDIR: bir kaynak okunamamışken öteki
    apaçık bir mükerrer gösterdiyse hüküm `True`dur (ölçülebilen bilgi çöpe atılmaz), ama
    okunamayan kaynak adıyla burada durur — çağıran onu loglar. Boş sözlük "her kaynak okundu"
    demektir; eksik taramaya dayanan sessiz bir "temiz" iddiası bu alan olmadan doğardı.

    HER KAYNAK OKUNDU AMA HEPSİ BOŞ → `False`, `benzerlik=None`: "hiç öneri yok" bir hükümdür,
    "0.0 benzedi" ise ölçülmemiş bir sayıyı ölçülmüş göstermek olurdu."""
    jet = jetonla(metin)
    if not jet:
        return {"mukerrer": None, "eslesen_id": None, "eslesen_kaynak": None, "benzerlik": None,
                "neden": NEDEN_METIN_YOK, "olculemeyen": {}}
    kume, olculemeyen, okunan = _adaylar()
    if not okunan:
        return {"mukerrer": None, "eslesen_id": None, "eslesen_kaynak": None, "benzerlik": None,
                "neden": " · ".join(olculemeyen[k] for k in sorted(olculemeyen)),
                "olculemeyen": olculemeyen}
    if not kume:
        return {"mukerrer": False, "eslesen_id": None, "eslesen_kaynak": None, "benzerlik": None,
                "neden": NEDEN_DEFTER_BOS, "olculemeyen": olculemeyen}
    # KAYNAK SIRASI DEĞİL BENZERLİK KARAR VERİR: sıraya göre seçen bir kapı daha UZAK bir
    # eşleşmeyi rapor eder ve operatör yanlış kaydı açardı.
    en_iyi_id, en_iyi_kaynak, en_iyi = None, None, 0.0
    for kimlik, kaynak, oteki in kume:
        b = benzerlik(jet, oteki)
        if b > en_iyi:
            en_iyi_id, en_iyi_kaynak, en_iyi = kimlik, kaynak, b
    if en_iyi >= ESIK:
        return {"mukerrer": True, "eslesen_id": en_iyi_id, "eslesen_kaynak": en_iyi_kaynak,
                "benzerlik": round(en_iyi, 4), "olculemeyen": olculemeyen,
                "neden": (f"{en_iyi_kaynak} kaynağındaki {en_iyi_id} ile benzerlik "
                          f"{round(en_iyi, 4)} ≥ eşik {ESIK}")}
    return {"mukerrer": False, "eslesen_id": None, "eslesen_kaynak": None,
            "benzerlik": round(en_iyi, 4), "neden": None, "olculemeyen": olculemeyen}
