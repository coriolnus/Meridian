"""EDG-2026-093 · ORTAK SAF FONKSİYONLAR — kohort okuma, sembol anahtarı, manifest, kaynak türetme.

Kart: research/cards/EDG-2026-093-midcap-pit-kohort-sagkalan-ust-sinir.yaml

NE İÇİN VAR. ADIM-0 EKSEN B sondası (adim0b_kapsama.py) ile ANA ÖLÇÜMÜN veri kurulumu
(veri_bar.py, veri_edgar.py) AYNI sözleşmeleri okur: kohort csv'sinin as-of satır anlamı,
pencere isim kümesi + çıkış günleri, sınıf-hisse sembolünün Alpaca anahtarı, sha256, manifest
yazımı, adapter soğuma yüzeyi. Bu sözleşmelerin ÜÇ kopyası zamanla ayrışırdı — bu deponun tekrar
eden "aynı gerçeğin iki kopyası sessizce ayrışır" sınıfı (CLAUDE.md §4 tek-kaynak yasası). Gövde
burada TEK yaşar; üç betik de buradan ithal eder.

NE YAPMAZ — ve bu bir sınır değil, SÖZLEŞMEDİR:
  * `meridian` İTHAL ETMEZ (obs'a hiçbir yol yok; pytest dışı koşum canlı yerel deftere yazamaz).
  * argparse KURMAZ, modül düzeyinde HİÇBİR G/Ç yapmaz — ithal etmek bir koşum tetiklemez
    (adim0b'nin ithal edilememe nedeni tam da bunun tersiydi).
  * HÜKÜM VERMEZ, eşik YORUMLAMAZ. Hüküm Rol-1'indir (CLAUDE.md §3, §5).
  * Ağa ÇIKMAZ. Tek dış dünya teması dosya okumaktır.

KAYNAK TÜRETME — ÇALIŞTIRMADAN (`kaynaktan_sabit` / `kaynaktan_desen`). Bu dosyanın ihtiyaç
duyduğu birkaç sabit (bar csv kolonları, EDGAR şeması, hisse-adedi etiket kümesi, SEC nezaket
politikası, elle-eşleme karar grameri) BAŞKA dosyalarda yaşıyor ve oraların sahibi biziz değiliz.
Kopyalamak yerine KAYNAK METİNDEN ayrıştırılırlar: `ast.parse` + `ast.literal_eval`. Üç kazanç:
  (1) tek-kaynak — üretici dosya değişince türetilen değer de değişir;
  (2) yan etki YOK — hedef dosya ÇALIŞTIRILMAZ (extract.py ve download.py modül düzeyinde dosya
      okur/ağa çıkar; ithal etmek bir çekim başlatırdı);
  (3) bayat bytecode BAĞIŞIKLIĞI — `ast.parse` kaynağı okur, `__pycache__`e hiç bakmaz
      (v334 sınıfı; ham exec_module da zaten yasak).
Türetilemeyen değer UYDURULMAZ: her türetici `(deger, neden)` döndürür ve `deger` None ise `neden`
ADIYLA kayda düşer. Çağıran beyanlı bir tabana düşerse bunu kayda YAZAR.

ÖLÇÜLEN SÖZLEŞMELER (bu turda, 2026-09-14 — varsayılmadı):
  * KOHORT CSV: başlık `date,tickers`; satırlar artan tarihli; bir satır KENDİSİNDEN SONRAKİ
    satıra kadar geçerlidir → as_of(t) = tarihi t'den küçük-eşit olan SON satır. (Kaynak:
    research/qc_dogrulama/pit_araliklari_uret.py ölçüm şerhi + EDG-070 eksen E aynı okuma.)
  * BAR DOSYA ADI: canlı bar arşivi sembolü küçültür ve noktayı tireye çevirir (motorun
    `_cache_path` kuralı; `BRK.B` diske `brk-b.csv` yazılır). Kohort defteri sınıf hissesini
    zaten TİRE ile yazdığından (`MOG-A`) iki kural AYNI dosya adında buluşur: `mog-a.csv`.
    Bu tesadüf DEĞİL, aynı kuralın iki ucudur ve `bar_dosya_adi` ikisini tek yerde birleştirir.
  * ALPACA ÇAĞRI BİÇİMİ: `daily_bars` sembole YALNIZ `upper().strip()` uygular — nokta/tire
    dönüşümü YOKTUR, yani çağıranın yazdığı biçim sağlayıcıya AYNEN gider. Tire biçimi uçtan
    HTTP 400 alır (A1 olayı 2026-09-14 14:27:02Z) ve süreç-içi soğuma penceresi açar.
"""
from __future__ import annotations

import ast
import csv
import datetime as dt
import hashlib
import json
import pathlib
import re
import sys

# =================================================================================================
# 0. KULLANIM HATASI — çıkış 2, sessiz düşme YOK
# =================================================================================================
def kullanim_hatasi(mesaj: str) -> None:
    """Kullanım hatası = çıkış 2 (argparse ile AYNI kod). Neden stderr'e ADIYLA yazılır: sessizce
    yanlış girdiyle ölçmektense koşum durur."""
    print(f"KULLANIM HATASI: {mesaj}", file=sys.stderr)
    raise SystemExit(2)


def sha256(p: pathlib.Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for blok in iter(lambda: f.read(1 << 20), b""):
            h.update(blok)
    return h.hexdigest()


def sha256_metin(metin: str) -> str:
    """Diske yazılmadan ÖNCE içeriğin sha'sı — üzerine-yazma kapısı bunu diskteki sha ile kıyaslar
    (dosya yazılıp sonra kıyaslanırsa donuk PIT girdisi çoktan ezilmiş olurdu)."""
    return hashlib.sha256(metin.encode("utf-8")).hexdigest()


def damga_uret() -> str:
    """UTC damgası `YYYYAAGGTHHMMSSZ`. Saat TAHMİNLE değil saatten okunur (hafıza: saat-etiketi
    ölçülür — etiketler bir gecede iki kez şişmişti)."""
    return dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")


# =================================================================================================
# 1. KAYNAK TÜRETME — hedef dosya ÇALIŞTIRILMADAN (AST)
# =================================================================================================
def _ust_duzey_atamalar(yol: pathlib.Path):
    """(ad → değer düğümü) üst-düzey atamalar. Hedef dosya ÇALIŞTIRILMAZ."""
    agac = ast.parse(yol.read_text(encoding="utf-8"), str(yol))
    out: dict[str, ast.expr] = {}
    for dugum in agac.body:
        if isinstance(dugum, ast.Assign):
            for hedef in dugum.targets:
                if isinstance(hedef, ast.Name):
                    out[hedef.id] = dugum.value
        elif isinstance(dugum, ast.AnnAssign) and isinstance(dugum.target, ast.Name) \
                and dugum.value is not None:
            out[dugum.target.id] = dugum.value
    return out


def kaynaktan_sabit(yol: pathlib.Path, ad: str):
    """`(deger, neden)` — `<ad> = <literal>` atamasını kaynak METİNDEN türetir.

    UYDURMA YASAĞI: dosya yoksa/ayrıştırılamıyorsa/atama literal değilse `deger` None döner ve
    `neden` ne olduğunu ADIYLA söyler. Çağıran beyanlı tabana düşerse bunu kayda yazmakla
    yükümlüdür — "türetildi" ile "beyan edildi" AYNI piksele düşmemelidir."""
    try:
        atamalar = _ust_duzey_atamalar(pathlib.Path(yol))
    except (OSError, SyntaxError, ValueError) as e:
        # sessiz-yutma DEĞİL: kaynak okunamadı/ayrıştırılamadı — neden ADIYLA döner, sayı uydurulmaz
        return None, f"kaynak okunamadı/ayrıştırılamadı ({type(e).__name__}: {e}): {yol}"
    if ad not in atamalar:
        return None, f"üst-düzey `{ad}` ataması bulunamadı: {yol}"
    try:
        return ast.literal_eval(atamalar[ad]), None
    except (ValueError, SyntaxError, TypeError) as e:
        # sessiz-yutma DEĞİL: atama literal değil (çağrı/isim); türetilemedi ve bu kayda düşer
        return None, f"`{ad}` ataması literal değil ({type(e).__name__}): {yol}"


def kaynaktan_desen(yol: pathlib.Path, ad: str):
    """`(desen_metni, neden)` — `<ad> = re.compile(r"…")` atamasının DESEN METNİ.

    `literal_eval` bir `re.compile` çağrısını çözemez (çağrıdır, literal değil); aranan şey zaten
    derlenmiş nesne değil, GRAMERİN KENDİSİDİR."""
    try:
        atamalar = _ust_duzey_atamalar(pathlib.Path(yol))
    except (OSError, SyntaxError, ValueError) as e:
        # sessiz-yutma DEĞİL: kaynak okunamadı — neden ADIYLA döner ve çağıran beyanlı tabana düşer
        return None, f"kaynak okunamadı/ayrıştırılamadı ({type(e).__name__}: {e}): {yol}"
    dugum = atamalar.get(ad)
    if dugum is None:
        return None, f"üst-düzey `{ad}` ataması bulunamadı: {yol}"
    if not (isinstance(dugum, ast.Call) and dugum.args):
        return None, f"`{ad}` bir `re.compile(...)` çağrısı değil: {yol}"
    try:
        return ast.literal_eval(dugum.args[0]), None
    except (ValueError, SyntaxError, TypeError) as e:
        # sessiz-yutma DEĞİL: desen metni literal değil (birleştirilmiş/değişkenden) — türetilemedi
        return None, f"`{ad}` deseninin ilk argümanı literal değil ({type(e).__name__}): {yol}"


# =================================================================================================
# 2. KOHORT DEFTERİ — as-of okuma
# =================================================================================================
KOHORT_BASLIK = ("date", "tickers")

csv.field_size_limit(10 ** 9)          # bir as-of satırı 661 sembol taşıyabilir


def kohort_oku(yol: pathlib.Path) -> list[tuple[dt.date, frozenset]]:
    """(tarih, sembol kümesi) satırları, artan tarihte. Başlık ve sıra SÖZLEŞMEDİR: bozuksa
    kullanım hatası — sessizce yanlış kohort ölçmektense koşum durur."""
    try:
        with open(yol, newline="", encoding="utf-8") as f:
            r = csv.reader(f)
            baslik = next(r, None)
            if baslik is None or tuple(x.strip() for x in baslik[:2]) != KOHORT_BASLIK:
                kullanim_hatasi(f"kohort csv başlığı 'date,tickers' olmalı, görülen: {baslik!r} ({yol})")
            satirlar = [(dt.date.fromisoformat(a[0].strip()),
                         frozenset(t.strip() for t in a[1].split(",") if t.strip()))
                        for a in r if a and a[0].strip()]
    except OSError as e:  # sessiz-yutma DEĞİL: dosya yoksa/okunamıyorsa kullanım hatası olarak ADIYLA çıkar
        kullanim_hatasi(f"kohort csv okunamadı ({type(e).__name__}): {yol}")
    except ValueError as e:  # sessiz-yutma DEĞİL: bozuk tarih alanı sessizce atlanmaz, koşum durur
        kullanim_hatasi(f"kohort csv tarih alanı bozuk ({type(e).__name__}: {e}): {yol}")
    if not satirlar:
        kullanim_hatasi(f"kohort csv boş: {yol}")
    for i in range(len(satirlar) - 1):
        if satirlar[i][0] >= satirlar[i + 1][0]:
            kullanim_hatasi(f"kohort csv tarihleri artan değil: {satirlar[i][0]} → {satirlar[i+1][0]}")
    return satirlar


def pencere_satirlari(satirlar, baslangic: dt.date, bugun: dt.date):
    """Pencerede ETKİN as-of satırları. Pencere başından ÖNCEKİ son satır bir ÇAPAdır: as-of
    okumasında o satır pencere başında hâlâ yürürlüktedir, tarihi pencereye KIRPILIR."""
    capa = [x for x in satirlar if x[0] <= baslangic]
    etkin = [(baslangic, capa[-1][1])] if capa else []
    etkin.extend((d, k) for d, k in satirlar if baslangic < d <= bugun)
    return etkin, bool(capa)


def isim_kumesi_ve_cikislar(etkin):
    """Pencerede en az bir gün listede olan HER sembol (birleşim) → çıkış günü.

    ÇIKIŞ GÜNÜ = sembolün listede SON göründüğü satırın ERTESİ as-of değişimi (yani ilk kez
    üye OLMADIĞI as-of tarihi). Pencere sonunda hâlâ listedeyse çıkış YOKTUR (None) — dosya
    sonrası TAŞINMAZ (uydurma yasağı)."""
    son_gorulme: dict[str, int] = {}
    for i, (_, k) in enumerate(etkin):
        for s in k:
            son_gorulme[s] = i
    son_i = len(etkin) - 1
    return {s: (etkin[i + 1][0].isoformat() if i < son_i else None)
            for s, i in son_gorulme.items()}


#: Kart penceresinin başlangıcını kartın KENDİ `veri_penceresi` alanından çeker. Kart YAML'i
#: PyYAML'siz okunur (stdlib'de kalmak A1 stdin kipinin şartı); desen alanın ilk ISO tarihini alır.
_KART_PENCERE_DESENI = re.compile(r"^veri_penceresi:\s*\"?(\d{4}-\d{2}-\d{2})", re.M)


def kart_pencere_baslangici(kart: pathlib.Path):
    """`(iso_tarih, neden)` — kohort penceresinin başı KARTTAN okunur, koda GÖMÜLMEZ (tek-kaynak).
    Okunamazsa None + neden döner ve çağıran kullanım hatası verir: sessiz varsayılan, kartın
    penceresiyle ölçümün penceresini ayrıştırırdı."""
    try:
        metin = pathlib.Path(kart).read_text(encoding="utf-8")
    except OSError as e:
        # sessiz-yutma DEĞİL: kart okunamadı — neden ADIYLA döner, tarih UYDURULMAZ
        return None, f"kart okunamadı ({type(e).__name__}): {kart}"
    m = _KART_PENCERE_DESENI.search(metin)
    if m is None:
        return None, f"kartın `veri_penceresi` alanında ISO tarih bulunamadı: {kart}"
    return m.group(1), None


# =================================================================================================
# 3. SEMBOL BİÇİMİ — kohort defteri ↔ Alpaca ucu ↔ bar arşivi dosya adı
# =================================================================================================
#: Sınıf-hisse sembolü deseni — BİLEREK DAR: yalnız TEK harflik sınıf son eki (`MOG-A`, `BRK-B`).
#: `TST-AB` (iki harf) ve `AA`/`MP` (tire yok) bu desene GİRMEZ ve dönüştürülmez.
SINIF_HISSE_DESENI = re.compile(r"^[A-Z]+-[A-Z]$")

#: Dönüşümün KAYNAĞI — uydurma yasağı: kayıt kuralı değil, kuralın NEREDEN ölçüldüğünü de taşır.
SEMBOL_BICIMI_KAYNAGI = [
    "meridian/adapters/alpaca.py `daily_bars` — sembole YALNIZ upper().strip() uygular; nokta/tire "
    "dönüşümü YOKTUR, yani çağıranın yazdığı biçim sağlayıcıya AYNEN gider (ölçüldü 2026-09-14).",
    "meridian/adapters/data.py `_cache_path` — motorun kanonik sembolü NOKTA taşır ve bar arşivi "
    "dosya adında küçültüp noktayı TİREYE çevirir (`BRK.B` → `brk-b.csv`).",
    "research/pit_universe/sp500_uyelik_tarihi.csv NOKTA yazar (BRK.B, BF.B); bu kartın kohort "
    "defteri sp400_uyelik_tarihi.csv ise TİRE yazar (MOG-A) — dönüşüm tam bu ayrımı kapatır.",
    "A1 koşum olayı 2026-09-14 14:27:02Z — `MOG-A` isteği alpaca_data_failed status=400 aldı, "
    "yani TİRE biçimi uçta REDDEDİLDİ (ADIM-0 EKSEN B tur-1'in ölçülen arızası: 298 isim).",
]


def alpaca_anahtari(sembol: str) -> str:
    """Kohort sembolü → Alpaca veri ucu anahtarı. Dönüşüm YALNIZ tek harflik sınıf son ekinde:
    `MOG-A` → `MOG.A`, `BRK-B` → `BRK.B`. `AA`/`MP`/`TST-AB` DOKUNULMAZ. Kural TEK yerde yaşar —
    hem çağrı hem kayıt alanı (`alpaca_anahtar`) bunu çağırır (tek-kaynak yasası)."""
    s = str(sembol).upper().strip()
    return s.replace("-", ".") if SINIF_HISSE_DESENI.match(s) else s


def bar_dosya_adi(sembol: str) -> str:
    """Kohort sembolü → bar csv dosya adı (uzantısız), CANLI ARŞİVİN KENDİ KURALIYLA.

    Motorun kuralı `_cache_path`te ölçüldü: `ticker.lower().replace(".", "-")`. Burada girdi
    Alpaca anahtarıdır, yani kural iki adımda uygulanır ve `MOG-A` → `MOG.A` → `mog-a` verir.
    İkinci bir adlandırma şeması YAZILMAZ: Parti-2 bu dosyaları canlı boru hattının (sanitize /
    measurement / integrity) beklediği adla bulmalıdır."""
    return alpaca_anahtari(sembol).lower().replace(".", "-")


def bar_tarihi(bar: dict):
    """Bar şemamızın tarih alanı "date"tir (ölçüldü: `_to_bar` onu üretir). "t" HAM API alanıdır ve
    şemaya girmez; ikinci okuma yalnız ham satırın sızdığı hâller için durur."""
    if not isinstance(bar, dict):
        return None
    d = bar.get("date") or bar.get("t")
    return str(d)[:10] if d else None


#: Bar csv'sinin kolon şeması. TEK KAYNAK canlı arşivin kendi `COLS` sabitidir — kopyalanmaz,
#: `kaynaktan_sabit` ile türetilir (`bar_kolonlari`). Bu liste yalnız türetme DÜŞERSE kullanılan
#: BEYANLI tabandır ve o hâl kayda `bar_kolonlari_kaynagi` ile ADIYLA yazılır.
BAR_KOLONLARI_BEYAN = ["date", "open", "high", "low", "close", "volume"]


def bar_kolonlari(repo: pathlib.Path):
    """`(kolonlar, kaynak, neden)` — canlı bar arşivinin kolon şeması.

    Türetme hedefi `meridian/adapters/data.py` içindeki `COLS`. Türetilemezse beyanlı tabana
    düşülür ve NEDEN kayda yazılır: "türetildi" ile "beyan edildi" karışmamalıdır (ölçüm bağlamı
    tuzağı — yanlış kaynak sessizce sahte sayı verir)."""
    yol = pathlib.Path(repo) / "meridian" / "adapters" / "data.py"
    deger, neden = kaynaktan_sabit(yol, "COLS")
    if isinstance(deger, list) and deger:
        return list(deger), f"türetildi: meridian/adapters/data.py `COLS` ({yol})", None
    return list(BAR_KOLONLARI_BEYAN), "BEYANLI TABAN (türetme düştü)", neden


# =================================================================================================
# 4. ADAPTER SOĞUMASI — ölçülür ve (sınıra kadar) sıfırlanır
# =================================================================================================
#: Ardışık kaç ÖLÇÜLEMEYEN sonucundan sonra soğuma sıfırlaması DURUR. Sıfırlamanın bedeli budur:
#: gerçekten düşmüş bir uç sınırsız sıfırlamayla yüzlerce kez dövülürdü ve bu, soğumanın VAROLUŞ
#: gerekçesine (adapterin kendi şerhi) aykırı olurdu. Sınır aşılınca kayıtlar "uç SOĞUMADA" der.
ARDISIK_OLCULEMEYEN_UST_SINIRI = 25

SOGUMA_ALANLARI = ("soguma_aktif", "soguma_yazildi", "soguma_olculemedi_neden")


def soguma_yuzeyi(alp) -> dict:
    """Adapterin soğuma yüzeyini ÖLÇER (varsayılmaz): `DATA_FEED` · `_data_cooled` ·
    `_DATA_FAIL_AT` · `_DATA_COOLDOWN`. Biri yoksa yüzey ölçülemedi sayılır ve bu, kayda
    `soguma_olculemedi_neden` olarak ADIYLA düşer — koşum düşmez, körlük BEYAN edilir."""
    parcalar = {"DATA_FEED": getattr(alp, "DATA_FEED", None),
                "_data_cooled": getattr(alp, "_data_cooled", None),
                "_DATA_FAIL_AT": getattr(alp, "_DATA_FAIL_AT", None),
                "_DATA_COOLDOWN": getattr(alp, "_DATA_COOLDOWN", None)}
    eksik = sorted(ad for ad, v in parcalar.items() if v is None)
    if eksik:
        return {"olculdu": False, "anahtar": None, "oku": None, "fail_at": None, "cooldown": None,
                "neden": "adapterde soğuma yüzeyi ölçülemedi, eksik: " + ", ".join(eksik)}
    return {"olculdu": True, "anahtar": "bars:%s" % parcalar["DATA_FEED"],
            "oku": parcalar["_data_cooled"], "fail_at": parcalar["_DATA_FAIL_AT"],
            "cooldown": parcalar["_DATA_COOLDOWN"], "neden": None}


def soguma_sifirla(yuzey: dict) -> bool:
    """`bars:<feed>` soğuma kaydını BU SÜREÇTE siler; gerçekten bir kayıt sildiyse True.

    GEREKÇE (şerh zorunlu, CLAUDE.md §2): soğuma modül-düzeyi sözlüklerde yaşar, yani SÜREÇ
    İÇİdir — bu araştırma betiği ayrı bir süreçtir ve canlı worker'ın soğumasına DOKUNMAZ.
    Tek bir sembolün 400'ü 298 ismi ölçülemez yapmıştı (ölçülen arıza 2026-09-14); doğru davranış
    "bu sembol düştü" ile "uç düştü"yü AYIRMAKTIR. Sınırsız sıfırlama da yanlış olurdu —
    `ARDISIK_OLCULEMEYEN_UST_SINIRI` bedeli kapatır."""
    silindi = yuzey["fail_at"].pop(yuzey["anahtar"], None) is not None
    yuzey["cooldown"].pop(yuzey["anahtar"], None)
    return silindi


def soguma_bos_ozet(neden: str) -> dict:
    """Sonda hiç çağrılmadığında soğuma özeti — ŞEMA KOŞUMLAR ARASI SABİT kalır (alan yoksa
    okuyucu "ölçüldü ve sıfır" ile "hiç ölçülmedi"yi ayıramazdı)."""
    return {"yuzey_olculdu": None, "anahtar": None, "sifirlama_n": 0,
            "ust_sinir": ARDISIK_OLCULEMEYEN_UST_SINIRI, "sifirlama_durdu": False,
            "neden": neden}


# =================================================================================================
# 5. EDGAR ŞEMASI — hisse-adedi etiketleri, 16 kolon, dönem türü
# =================================================================================================
#: Hisse-adedi etiket kümesinin BEYANLI tabanı. TEK KAYNAK research/edgar_facts/betikler/extract.py
#: içindeki `SHARE_TAGS`tir ve `hisse_etiketleri` onu kaynak METİNDEN türetir; bu liste yalnız
#: türetme düşerse kullanılır ve o hâl kayda ADIYLA yazılır. Çivi ikisinin EŞİTLİĞİNİ ölçer —
#: kopya kaçınılmazsa türetme + ayrışma çivisi (CLAUDE.md §4 tek-kaynak yasası).
HISSE_ETIKETLERI_BEYAN = (
    ("dei", "EntityCommonStockSharesOutstanding"),
    ("us-gaap", "CommonStockSharesOutstanding"),
    ("us-gaap", "CommonStockSharesIssued"),
    ("us-gaap", "WeightedAverageNumberOfSharesOutstandingBasic"),
    ("us-gaap", "WeightedAverageNumberOfDilutedSharesOutstanding"),
    ("us-gaap", "WeightedAverageNumberOfShareOutstandingBasicAndDiluted"),
)

#: Hisse-adedi etiketlerinin İKİ SEMANTİĞİ (README'nin "iki farklı semantik, karıştırma" uyarısı):
#: ANLIK SAYIM (bilanço/kapak tarihine ait adet) ve DÖNEM ORTALAMASI (EPS paydası). Ayrım etiket
#: ADINDAN türetilir — ikinci bir liste tutmak, etiket kümesi büyüdüğünde sessizce eksik kalırdı.
WAVG_ONEKI = "WeightedAverage"


def etiket_semantigi(tag: str) -> str:
    """`anlik` | `wavg` — etiket adından TÜRETİLİR, ikinci bir listeden okunmaz."""
    return "wavg" if str(tag).startswith(WAVG_ONEKI) else "anlik"


def hisse_etiketleri(repo: pathlib.Path):
    """`(etiketler, kaynak, neden)` — hisse-adedi etiket kümesi.

    Türetme hedefi research/edgar_facts/betikler/extract.py içindeki `SHARE_TAGS`. O dosya
    İTHAL EDİLEMEZ gibi davranılır ve edilmez: modül düzeyinde `cikmap.json` okur ve çalışma
    dizinine kilitlidir — ithal etmek çağıranın dizininde bir çekim/okuma tetiklerdi. Kaynak
    METİN ayrıştırılır; aynı kümedir, ikinci bir uygulama değil."""
    yol = pathlib.Path(repo) / "research" / "edgar_facts" / "betikler" / "extract.py"
    deger, neden = kaynaktan_sabit(yol, "SHARE_TAGS")
    if isinstance(deger, list) and deger:
        return ([tuple(x) for x in deger],
                f"türetildi: research/edgar_facts/betikler/extract.py `SHARE_TAGS` ({yol})", None)
    return list(HISSE_ETIKETLERI_BEYAN), "BEYANLI TABAN (türetme düştü)", neden


#: EDGAR PIT serisinin 16 kolonu. TEK KAYNAK research/edgar_facts/betikler/finalize.py `COLS`
#: (extract.py'nin 14 kolonuna `donem_gun` + `donem_turu` ekleyen nihai şema); bu liste beyanlı
#: tabandır ve README'nin yazdığı şemayla birebir aynıdır.
EDGAR_KOLONLARI_BEYAN = ["symbol", "cik", "taxonomy", "tag", "unit", "start", "end", "filed",
                         "val", "form", "fy", "fp", "donem_gun", "donem_turu", "accn", "frame"]


def edgar_kolonlari(repo: pathlib.Path):
    """`(kolonlar, kaynak, neden)` — nihai 16 kolonluk EDGAR şeması, finalize.py'den türetilir."""
    yol = pathlib.Path(repo) / "research" / "edgar_facts" / "betikler" / "finalize.py"
    deger, neden = kaynaktan_sabit(yol, "COLS")
    if isinstance(deger, list) and len(deger) == len(EDGAR_KOLONLARI_BEYAN):
        return (list(deger),
                f"türetildi: research/edgar_facts/betikler/finalize.py `COLS` ({yol})", None)
    return list(EDGAR_KOLONLARI_BEYAN), "BEYANLI TABAN (türetme düştü)", neden


#: `donem_turu` eşik merdiveni — finalize.py'nin KENDİ merdiveni. Kaynak bir FONKSİYON gövdesidir,
#: literal değil; bu yüzden türetme burada değil ÇİVİDE yapılır (çivi finalize.py'yi ayrıştırıp
#: bu demetle eşitliğini ölçer — ayrışma çivisi). Sıra ANLAMLIDIR: ilk eşiği geçen kazanır.
DONEM_TURU_MERDIVENI = ((45, "diger"), (135, "ceyrek"), (225, "yarim"), (315, "9ay"),
                        (400, "yillik"))
DONEM_TURU_ANLIK = "anlik"          # `start` yok → bilanço/kapak sayımı
DONEM_TURU_DIGER = "diger"          # merdivenin üstü


def donem_turu(gun):
    """Dönem uzunluğu (takvim günü) → dönem türü. `gun` None ise `anlik` (start alanı boş)."""
    if gun is None:
        return DONEM_TURU_ANLIK
    for esik, ad in DONEM_TURU_MERDIVENI:
        if gun <= esik:
            return ad
    return DONEM_TURU_DIGER


def donem_gun(start, end):
    """(end - start) takvim günü; biri yoksa None (uydurma yasağı: 0 ile "bilinmiyor" AYRI)."""
    if not start or not end:
        return None
    try:
        return (dt.date.fromisoformat(str(end)[:10]) - dt.date.fromisoformat(str(start)[:10])).days
    except ValueError:
        # sessiz-yutma DEĞİL: kaynak tarihi bozuk — satır DÜŞMEZ, dönem uzunluğu ÖLÇÜLEMEDİ (None)
        return None


# =================================================================================================
# 6. SEC NEZAKET POLİTİKASI — download.py'nin disiplininden türetilir
# =================================================================================================
#: SEC fair-access: kimlik bildiren User-Agent ZORUNLU, istek arası gecikme. Beyanlı taban;
#: gerçek kaynak research/edgar_facts/betikler/download.py (`UA`, `DELAY`, `TPL`).
SEC_UA_BEYAN = "Meridian Research oztrkerdem@gmail.com"
SEC_BEKLEME_BEYAN = 0.15
SEC_COMPANYFACTS_TPL_BEYAN = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json"
#: `company_tickers.json` URL'i download.py'de YOKTUR (o betik dosyayı hazır bulur); tek kaynak
#: research/edgar_facts/kaynak.json `url_sablonlari.ticker_cik_haritasi` alanıdır.
SEC_TICKERS_URL_BEYAN = "https://www.sec.gov/files/company_tickers.json"


def sec_politikasi(repo: pathlib.Path) -> dict:
    """SEC çekim politikası: UA · istek arası gecikme · companyfacts URL şablonu · tickers URL.

    Her alan KAYNAĞIYLA birlikte döner. `download.py` bir ÇEKİM BETİĞİDİR ve modül düzeyinde
    `cikmap.json` okuyup ağa çıkar — ithal EDİLMEZ, kaynak metni ayrıştırılır."""
    dl = pathlib.Path(repo) / "research" / "edgar_facts" / "betikler" / "download.py"
    kaynak_json = pathlib.Path(repo) / "research" / "edgar_facts" / "kaynak.json"
    ua, ua_neden = kaynaktan_sabit(dl, "UA")
    bekleme, bekleme_neden = kaynaktan_sabit(dl, "DELAY")
    tpl, tpl_neden = kaynaktan_sabit(dl, "TPL")
    tickers_url, tickers_neden = None, None
    try:
        ham = json.loads(kaynak_json.read_text(encoding="utf-8"))
        tickers_url = ((ham.get("url_sablonlari") or {}).get("ticker_cik_haritasi")) or None
        if tickers_url is None:
            tickers_neden = f"`url_sablonlari.ticker_cik_haritasi` alanı yok: {kaynak_json}"
    except (OSError, ValueError) as e:
        # sessiz-yutma DEĞİL: kaynak kaydı okunamadı — neden ADIYLA döner, URL beyanlı tabana düşer
        tickers_neden = f"kaynak.json okunamadı ({type(e).__name__}): {kaynak_json}"
    return {
        "user_agent": ua if isinstance(ua, str) and ua else SEC_UA_BEYAN,
        "user_agent_kaynak": ("türetildi: research/edgar_facts/betikler/download.py `UA`"
                              if isinstance(ua, str) and ua else "BEYANLI TABAN"),
        "user_agent_neden": ua_neden,
        "bekleme_sn": float(bekleme) if isinstance(bekleme, (int, float)) else SEC_BEKLEME_BEYAN,
        "bekleme_sn_kaynak": ("türetildi: research/edgar_facts/betikler/download.py `DELAY`"
                              if isinstance(bekleme, (int, float)) else "BEYANLI TABAN"),
        "bekleme_sn_neden": bekleme_neden,
        "companyfacts_tpl": tpl if isinstance(tpl, str) and tpl else SEC_COMPANYFACTS_TPL_BEYAN,
        "companyfacts_tpl_kaynak": ("türetildi: research/edgar_facts/betikler/download.py `TPL`"
                                    if isinstance(tpl, str) and tpl else "BEYANLI TABAN"),
        "companyfacts_tpl_neden": tpl_neden,
        "tickers_url": tickers_url or SEC_TICKERS_URL_BEYAN,
        "tickers_url_kaynak": ("türetildi: research/edgar_facts/kaynak.json "
                               "`url_sablonlari.ticker_cik_haritasi`"
                               if tickers_url else "BEYANLI TABAN"),
        "tickers_url_neden": tickers_neden,
        "fair_use": "SEC EDGAR fair-access: kimlik bildiren User-Agent (ad + e-posta) ZORUNLU, "
                    "otomatik erişimde 10 istek/sn üst sınırı. Bu çekim SIRALI ve tek bağlantılı.",
    }


# =================================================================================================
# 7. ELLE EŞLEME KARARLARI — `esle:`/`cift:` çiftleri
# =================================================================================================
#: Karar grameri BEYANLI tabanı. TEK KAYNAK kohort üreticisinin kendi `KARAR_CIFT_RE` deseni
#: (research/olcumler/edg093_midcap_pit/kohort.py) — o dosya bu yaml'i ÜRETİR, gramerin sahibi odur.
KARAR_CIFT_DESENI_BEYAN = r"(?:esle|cift):[A-Z0-9.\-]{1,8}->[A-Z0-9.\-]{1,8}"

#: `esle` ile `cift` AYNI ŞEY DEĞİLDİR ve bu ayrım kayda taşınır:
#:   esle:<eski>-><yeni>  → YENİDEN ADLANDIRMA KİMLİĞİ: aynı ihraççı, aynı CIK beklenir.
#:   cift:<cikan>-><giren> → ANOTASYON: iki yarım satır aynı endeks olayının iki kitaplamasıdır
#:                           (tipik olarak spin-off) — İKİ AYRI İHRAÇÇI olabilir ve genelde öyledir.
#: Bu yüzden `cift`ten türetilen bir CIK eşlemesi "kanıtlanmış kimlik" DEĞİLDİR; kayıt onu ADIYLA
#: ayırır ve hükmü Rol-1'e bırakır (uydurma yasağı: "eşleşti" ile "aynı şirket" ayrı iddialardır).
KARAR_KIMLIK_KANITI = {"esle": "yeniden_adlandirma", "cift": "anotasyon_cift"}


def karar_ciftleri(esleme_yaml: pathlib.Path, desen_metni: str | None = None):
    """`(ciftler, neden)` — yaml'deki `karar:` satırlarından `(jeton, sol, sag)` üçlüleri.

    PyYAML'e BAĞLANILMAZ (stdlib'de kalmak A1 stdin kipinin şartı): aranan şey `karar:` alanının
    DEĞERİDİR ve gramer zaten tek satırlık bir jetondur. Dosya okunamazsa `ciftler` boş döner ve
    `neden` ADIYLA yazılır — sessizce "eşleme kararı yok" denmez."""
    gramer = desen_metni or KARAR_CIFT_DESENI_BEYAN
    try:
        metin = pathlib.Path(esleme_yaml).read_text(encoding="utf-8")
    except OSError as e:
        # sessiz-yutma DEĞİL: eşleme dosyası okunamadı — neden ADIYLA döner, karar UYDURULMAZ
        return [], f"elle eşleme yaml okunamadı ({type(e).__name__}): {esleme_yaml}"
    satir_deseni = re.compile(r"^\s*karar:\s*(" + gramer + r")\s*$", re.M)
    jeton_deseni = re.compile(r"^(esle|cift):([A-Z0-9.\-]{1,8})->([A-Z0-9.\-]{1,8})$")
    out, gorulen = [], set()
    for m in satir_deseni.finditer(metin):
        j = jeton_deseni.match(m.group(1))
        if j is None:
            continue    # gramer eşleşti ama jeton çözülemedi — bu satır atlanır, sayım aşağıda
        ucdu = (j.group(1), j.group(2), j.group(3))
        if ucdu not in gorulen:
            gorulen.add(ucdu)
            out.append(ucdu)
    return out, None


def esleme_komsulari(ciftler):
    """`sembol → [(diger_ad, jeton), …]` — bir sembolün karar çiftlerindeki KARŞI adı.

    Yön ÖNEMSİZDİR (çift iki yarım satırı bağlar): hem sol hem sağ komşu olarak kaydedilir."""
    out: dict[str, list] = {}
    for jeton, sol, sag in ciftler:
        out.setdefault(sol, []).append((sag, jeton))
        out.setdefault(sag, []).append((sol, jeton))
    return out


# =================================================================================================
# 8. MANİFEST YAZIMI
# =================================================================================================
def manifest_yaz(cikti_dizin: pathlib.Path, ad: str, govde: dict) -> pathlib.Path:
    """`<cikti_dizin>/<ad>` dosyasına JSON yazar ve YOLU döndürür.

    YASA 6: `govde` içinde `okuyan` alanı ZORUNLUDUR — okuyucusu adıyla yazılmamış bir artefakt
    üretilmemişten farksızdır. Alan yoksa kullanım hatası verilir; "sonra ekleriz" tam olarak
    okunmayan artefaktın doğuş biçimidir."""
    if not isinstance(govde, dict) or not govde.get("okuyan"):
        kullanim_hatasi(f"manifest gövdesinde `okuyan` alanı YOK (Yasa 6): {ad}")
    d = pathlib.Path(cikti_dizin)
    d.mkdir(parents=True, exist_ok=True)
    hedef = d / ad
    hedef.write_text(json.dumps(govde, ensure_ascii=False, indent=1, sort_keys=False) + "\n",
                     encoding="utf-8")
    return hedef


def onceki_manifest_oku(yol: pathlib.Path, anahtar: str = "kayitlar"):
    """`(kayitlar, damga, neden)` — önceki manifest; okunamazsa hepsi None + neden (koşum düşmez,
    çağıran karar verir)."""
    try:
        ham = json.loads(pathlib.Path(yol).read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        # sessiz-yutma DEĞİL: önceki manifest okunamadı — neden ADIYLA döner ve çağıran durur
        return None, None, f"önceki manifest okunamadı ({type(e).__name__}): {yol}"
    kayitlar = ham.get(anahtar)
    if not isinstance(kayitlar, list):
        return None, None, f"önceki manifestte `{anahtar}` listesi yok: {yol}"
    return ({str(r.get("sembol") or ""): r for r in kayitlar if isinstance(r, dict) and r.get("sembol")},
            ham.get("damga_utc"), None)
