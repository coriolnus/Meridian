"""research/olcumler/edg092_sp400_uyelik/olc.py — EDG-2026-092 ÖLÇÜM aracı (2026-09-14).

NE ÖLÇER. Kart `research/cards/EDG-2026-092-sp400-uyelik-tarihcesi-ucretsiz-kaynak-fizibilite.yaml`
hipotezi: S&P MidCap 400 üyelik DEĞİŞİKLİKLERİ ücretsiz kamu kaynağından (Wikipedia "List of S&P 400
companies" değişiklik tablosu, oldid ile dondurulmuş HAM WİKİTEXT) 2020-07-27 → bugün penceresinde
PIT-doğru yeniden kurulabilir mi. K=1 (bilinen olay kapsaması) + dört pozitif kontrol.

ROL: ÖLÇÜM ajanı. Bu modül HÜKÜM VERMEZ (`hukum: "YOK — Rol-1"`), KARTA DOKUNMAZ, `meridian/*.py`ye
DOKUNMAZ, `meridian`i İTHAL ETMEZ (canlı yerel deftere yazma riski — CLAUDE.md §2), canlı `state/`e
YAZMAZ. Eşikler kartın `esikler:` alanından ÇALIŞMA ANINDA okunur (`esikleri_karttan_oku`), koda
KOPYALANMAZ; veri penceresinin başlangıcı da kartın `veri_penceresi` metninden TÜRETİLİR
(`pencere_baslangici_karttan`) — tek-kaynak yasası.

EDG-075/076 BETİĞİNİN WİKİTEXT-GİRDİLİ KARDEŞİ, KOPYASI DEĞİL. `research/olcumler/
edg075_sp500_tarihsel/olcum.py` HTML (pandas `read_html`) okur; bu kart ham WİKİTEXT dondurdu
(Wikimedia python-httpx'i 403 ile kesiyor — hafıza `wikipedia-cekim-httpx-403`; `action=raw` curl ile
alındı). Bu yüzden YALNIZ tablo-okuma katmanı burada yeniden yazıldı; K1 eşleştirmesi, `as_of` geri
sarma, tarih/sembol normalizasyonu, iş-günü toleransı, gelecek-olay negatif kontrolü ve kart iç
tutarlılığı EDG-075 modülünden İTHAL edilir (`ORTAK`) — tek-kaynak yasası; ayrışma çivisi
`tests/test_edg092_sp400_olcum_v484.py::test_ortak_yardimcilar_edg075ten_ithal_kopya_degil`.

WİKİTABLO AYRIŞTIRICI (bu modülün asıl yeni yüzeyi):
  * Tablo `id`ye ÇİVİLENMEZ, BAŞLIK SÜTUNLARINDAN tanınır (Rol-1 notu 2026-09-14: S&P 400 sayfasında
    `id="changes"` var, başka sayfalarda yok; başlık "Date" ya da "Effective Date" olabilir). Sütun
    eşleştirmesi EDG-075'in `_kolon_bul` alt-dizge desenini AYNEN kullanır (ithal).
  * `rowspan`/`colspan` HEM başlıkta HEM veri satırlarında açılır: iki satırlı başlık
    (Date · Added{Ticker,Security} · Removed{Ticker,Security} · Reason) düz sütun adlarına indirgenir
    ("Added_Ticker" …), `| rowspan=2 | June 30, 2016` biçimindeki tarih hücresi ALT SATIRA DEVREDİLİR
    — devretmeyen bir ayrıştırıcı o satırların tarihini "çözülemedi" sayar (Rol-1 ön ayrıştırıcısı
    544 satırın 36'sında tam bunu gördü).
  * Hücre bölme DERİNLİK DUYARLIDIR: `||` ayıracı yalnız `[[…]]` ve `{{…}}` DIŞINDA bölünür
    (`{{cite web |url=…}}` şablonundaki `|` hücre sınırı DEĞİLDİR).
  * Hücre nitelikleri (`rowspan=2 |`, `style="…" |`) yalnız SOL parça nitelik-biçimindeyse ayrılır.
  * `<ref>…</ref>` / `<ref … />` metinden ÇIKARILIR ama içindeki `url=…` adresleri satırın
    `urller` alanında SAKLANIR (kaynaksız satır sayısı ölçülebilsin diye — kart adım_0 notu).
  * `[[Ad|Görünen]]` → "Görünen", `[[Ad]]` → "Ad", `'''kalın'''` sadeleşir.
  * HAYALET SATIR (tarih/eklenen/çıkan/neden'in HEPSİ boş) atılır; yalnız-eklenen ya da yalnız-çıkan
    satır GERÇEK VERİDİR, tutulur (EDG-075 hayalet-satır süzgeciyle aynı kural).

ÖLÇÜLENLER:
  ADIM-0  tablo var mı · sütunlar · satır n · pencere satırı n ≥ kart `pencere_satir_alt` ·
          tarihi çözülemeyen satırlar ADIYLA (uydurma yok) · `--beklenen-sha` · kart iç tutarlılığı.
  K1      kartın `bilinen_olaylar`ı: tabloda satır var ∧ |tarih farkı| ≤ 1 İŞ GÜNÜ ∧ yön doğru.
          `kart_beyan_n != olculen_n` AYRIŞMA olarak işaretlenir, hiçbir taraf ZORLANMAZ (EDG-076).
  PK-1    `gelecek_olaylar` tabloda yürürlük satırı taşımamalı ∧ `as_of(bugün)` yönle tutarlı olmalı.
  PK-2    `rename_vakalari` RAPORU: vaka tarihindeki tablo satırları + kart notunda geçen sembollerin
          `as_of` davranışı. Kartta `eski`/`yeni` ALANI YOKTUR (yalnız düzyazı `not`) — bu yüzden
          eski/yeni AYRIMI YAPILMAZ (`eski_yeni_ayrimi: None` + neden), semboller nottan AÇIK bir
          regexle çıkarılır ve kaynağı yazılır. Mekanik kapı: vaka tarihinde, eklenen VE çıkan'ın
          İKİSİ de not sembolü olan ve gerekçesi YENİDEN-ADLANDIRMA sözlüğüne uyan bir satır
          OLMAMALI (yeniden adlandırma üyelik değişikliği olarak kitaplanmamalı).
  PK-3    `as_of(bugün)` ∩ bağımsız güncel liste (SPDR MDY holdings xlsx) / |liste| ≥ kart eşiği.
          TAUTOLOJİ BEYANI: `as_of` güncel listeden GERİYE sararak kurulur; listeden SONRA tabloda
          değişiklik yoksa kesişim 1,0 ÇIKAR — bu bir kanıt değil, TOHUMUN KENDİSİDİR. Beyan
          `pk3.tautoloji`de yazılır; yanına BİLGİ TAŞIYAN tanı konur: `as_of(pencere başı)` üye
          sayısı — S&P 400 her zaman 400 üyelidir, sapma tabloda EKSİK/EŞLEŞMEMİŞ satır demektir.
  PK-4    YOL TUTARLILIĞI: AYNI ayrıştırıcı + AYNI K1 fonksiyonu, EDG-076'nın S&P 500 ham wikitext'i
          ve doğrulanmış 28 olayıyla koşar; EDG-076 hükmü 28/28 idi.

KILL-LIST #5 (kart): PK'lerden biri DÜŞERSE hiçbir kapsama sayısı YAYILMAZ —
`yayin_engeli.engel=True`, `k1_kapsama_yayinlanabilir=None` ve markdown rapor kapsama oranını
BASMAZ. Koşmamış (girdisi verilmemiş) PK "düşmüş" SAYILMAZ, `kosmayan_pkler`de ADIYLA raporlanır
(uydurma yasağı: "bilinmiyor" ile "geçti" aynı şey değildir).

AĞ: yalnız `cek()` fonksiyonu HTTP yapar ve bu ajan turunda HİÇ ÇAĞRILMADI (CLAUDE.md ajan kuralı).
Girdi her zaman diskten (`--girdi`), kimliği oldid + sha256.

YASA 4 (sessiz yutma yok): her yakalayıcı `# sessiz-yutma:` gerekçesiyle işaretli.
YASA 6 (okuyucusuz yazım yok): `sonuc_<damga>.json` + `rapor_<damga>.md` → okuyucusu Rol-1'dir
(hükmü AYNI turda karta + K defterine işler, CLAUDE.md §5).
UYDURMA YASAĞI: ölçülemeyen her değer `None` + neden.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import pathlib
import re
import sys
import xml.etree.ElementTree as ET
import zipfile

import yaml

SANDBOX = pathlib.Path(__file__).resolve().parent
KOK = SANDBOX.parents[2]
KART_YOLU = KOK / "research" / "cards" / "EDG-2026-092-sp400-uyelik-tarihcesi-ucretsiz-kaynak-fizibilite.yaml"
EDG075_YOLU = KOK / "research" / "olcumler" / "edg075_sp500_tarihsel" / "olcum.py"

WIKI_TITLE = "List_of_S%26P_400_companies"
WIKI_RAW = f"https://en.wikipedia.org/w/index.php?title={WIKI_TITLE}&action=raw"


# `sys.path` eki ZORUNLU ve BİLİNÇLİ (eski şerh "sys.path KİRLETİLMEZ" diyordu; o kural burada
# ARTIK GEÇERLİ DEĞİL ve sessizce bırakılması bir sürüklenme olurdu). Bu betik DOĞRUDAN koşulur,
# o zaman `sys.path[0]` BU dizindir ve `ops.` ön eki editable-install `.pth`i üzerinden BAŞKA BİR
# CHECKOUT'a düşer (worktree'den `ModuleNotFoundError`, ana checkout'ta sessizce ORANIN kopyası).
# Emsal: research/olcumler/edg042_kosum_*/pencere_altbant.py.
if str(KOK) not in sys.path:
    sys.path.insert(0, str(KOK))
from ops.sasi_yukleyici import kaynaktan_yukle                                    # noqa: E402


def _ortak_yukle():
    """EDG-075/076 ölçüm betiğini DOSYA YOLUNDAN yükler. `research/` bir paket değildir; yolu
    `KOK`tan türetiriz. Tek-kaynak yasası: K1/as_of/tarih/sembol yardımcıları BURADA YENİDEN
    YAZILMAZ, ORADAN gelir.

    KAYNAKTAN DERLENİR (v334 §C, düzeltme 2026-09-14). Ham `spec.loader.exec_module` yolu
    `__pycache__`e bakar ve zaman damgalı pyc'nin geçerlilik kontrolü YALNIZ (tam-saniye mtime,
    bayt boyutu) çiftidir — EDG-075 betiğinde boyutu değiştirmeyen bir düzenleme aynı saniyede
    kalırsa BAYAT bytecode koşar. Bedeli burada özellikle ağırdır: yukarıdaki satırın gerekçesi
    "tek kopya" iken, ithal edilen yardımcılar sessizce ESKİ bir sürümden gelirdi ve ayrışma tam
    da engellemek istenen yerde doğardı. Gerekçe + ölçüm: `ops/sasi_yukleyici.py` başlığı ·
    kapı: tests/test_bayat_bytecode_v334.py §C.

    `sys_modules_kaydet=True` eski `sys.modules.setdefault(...)`ın YERİNİ tutar: kayıt exec'ten
    ÖNCE yapılır (betiğin kendi adını çözebilmesi için). TEK FARK, anahtar zaten doluysa
    `setdefault` eskiyi korurdu, bu yol yenisini yazar — ve yenisi, döndürülen modülün TA
    KENDİSİDİR, yani kayıt ile dönen nesne artık AYRIŞAMAZ."""
    return kaynaktan_yukle(EDG075_YOLU, "edg075_olcum", sys_modules_kaydet=True)


ORTAK = _ortak_yukle()

# Yeniden-adlandırma sözlüğü — PK-2'nin mekanik kapısı ve tarama listesi bu SABİTTEN türer
# (iki ayrı yerde tekrar edilmez).
RENAME_SOZLUGU = re.compile(
    r"renam|name change|changed its name|ticker (?:change|symbol change)|rebrand|adını|ad değişik",
    re.IGNORECASE)
# Kartın rename notlarındaki İKİ MAKİNE-OKUNUR İŞARET (kartın kendi yazımı, uydurma değil):
#   `X↑ Y↓` = o tarihte tabloda BEKLENEN satır · `X→Y` = üyelik değişikliği SAYILMAMASI gereken çift.
SATIR_BEKLENTI_RE = re.compile(r"([A-Z][A-Z0-9.\-]{0,5})\s*↑\s*[,;]?\s*([A-Z][A-Z0-9.\-]{0,5})\s*↓")
RENAME_OK_RE = re.compile(r"([A-Z][A-Z0-9.\-]{0,5})\s*(?:→|->)\s*([A-Z][A-Z0-9.\-]{0,5})")
# Kart `not` düzyazısından sembol çıkarma deseni — AÇIK ve dar: 1-5 büyük harf, isteğe bağlı
# `.X`/`-X` sınıf eki. Türetme olduğu `sembol_kaynagi` alanında YAZILI (uydurma yasağı).
NOT_SEMBOL_RE = re.compile(r"\b([A-Z]{1,5}(?:[.-][A-Z])?)\b")
# Düzyazıda geçen ama ticker OLMAYAN büyük-harf kısaltmalar — beyanlı dışlama listesi.
NOT_SEMBOL_HARIC = {"S", "P", "SP", "MIDCAP", "DEGIL", "DEĞİL", "SEC", "ETF", "USD", "LLC", "INC",
                    "CEO", "US", "NYSE", "CUSIP", "PIT", "EDG", "TSK", "K", "PK"}

ESIK_ANAHTARLARI = ("bilinen_olay_kapsama_alt", "bilinen_olay_n_alt", "pencere_satir_alt",
                    "guncel_liste_kesisim_alt")


def damga() -> str:
    """UTC damga — TAHMİN EDİLMEZ, ölçülür (hafıza `saat-etiketi-olculur`)."""
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")


# ======================================================================================
# EŞİKLER VE PENCERE — KARTTAN (kod kopyalamaz)
# ======================================================================================

def esikleri_karttan_al(kart: dict) -> dict:
    esikler = kart.get("esikler") if isinstance(kart, dict) else None
    if not isinstance(esikler, dict):
        raise ValueError("kart 'esikler' alanı yok/sözlük değil — betik eşiği UYDURAMAZ")
    eksik = [a for a in ESIK_ANAHTARLARI if a not in esikler]
    if eksik:
        raise ValueError(f"kart eşiği bulunamadı: {', '.join(eksik)} — betik eşiği UYDURAMAZ")
    out = {a: float(esikler[a]) for a in ESIK_ANAHTARLARI}
    out["kart_id"] = kart.get("card_id")
    return out


def esikleri_karttan_oku(kart_yolu: pathlib.Path = KART_YOLU) -> dict:
    kart = kart_yukle(kart_yolu)
    out = esikleri_karttan_al(kart)
    out["kart_yolu"] = str(kart_yolu)
    return out


def kart_yukle(kart_yolu: pathlib.Path) -> dict:
    kart = yaml.safe_load(pathlib.Path(kart_yolu).read_text(encoding="utf-8"))
    if not isinstance(kart, dict):
        raise ValueError(f"kart sözlük değil: {kart_yolu}")
    return kart


def pencere_baslangici_karttan(kart: dict) -> str:
    """Pencere başlangıcı kartın `veri_penceresi` METNİNDEN türetilir (ilk ISO tarih) — koda
    kopyalanmaz. Metinde ISO tarih yoksa ValueError (UYDURMA YOK)."""
    metin = str((kart or {}).get("veri_penceresi") or "")
    m = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", metin)
    if not m:
        raise ValueError("kart 'veri_penceresi' metninde ISO tarih yok — pencere UYDURULAMAZ")
    return m.group(1)


# ======================================================================================
# WİKİTEXT — DERİNLİK DUYARLI HÜCRE BÖLME
# ======================================================================================

def derinlik_bol(metin: str, ayirac: str) -> list[str]:
    """`metin`i `ayirac`la böler ama `[[…]]` ve `{{…}}` İÇİNDE bölmez — `{{cite web |url=…}}`
    şablonundaki `|` hücre sınırı DEĞİLDİR."""
    parcalar: list[str] = []
    tampon: list[str] = []
    link = tmpl = 0
    i = 0
    n = len(metin)
    while i < n:
        if metin.startswith("[[", i):
            link += 1; tampon.append("[["); i += 2; continue
        if metin.startswith("]]", i):
            link = max(0, link - 1); tampon.append("]]"); i += 2; continue
        if metin.startswith("{{", i):
            tmpl += 1; tampon.append("{{"); i += 2; continue
        if metin.startswith("}}", i):
            tmpl = max(0, tmpl - 1); tampon.append("}}"); i += 2; continue
        if link == 0 and tmpl == 0 and metin.startswith(ayirac, i):
            parcalar.append("".join(tampon)); tampon = []; i += len(ayirac); continue
        tampon.append(metin[i]); i += 1
    parcalar.append("".join(tampon))
    return parcalar


NITELIK_RE = re.compile(r"^[A-Za-z0-9_\-\s=\"':;%.,#()]*$")


def nitelik_ayir(hucre: str) -> tuple[str, str]:
    """`rowspan=2 | June 30, 2016` → ("rowspan=2 ", " June 30, 2016"). Sol parça nitelik BİÇİMİNDE
    değilse hücrenin TAMAMI içeriktir (metinde geçen `|` içeriği bölmez)."""
    parcalar = derinlik_bol(hucre, "|")
    if len(parcalar) < 2:
        return "", hucre
    sol = parcalar[0]
    if NITELIK_RE.match(sol) and "[" not in sol and "{" not in sol and "<" not in sol:
        return sol, "|".join(parcalar[1:])
    return "", hucre


SPAN_RE = re.compile(r"\b(rowspan|colspan)\s*=\s*\"?(\d+)\"?", re.IGNORECASE)


def _span(nitelikler: str, ad: str) -> int:
    for anahtar, deger in SPAN_RE.findall(nitelikler or ""):
        if anahtar.lower() == ad:
            return max(1, int(deger))
    return 1


# ======================================================================================
# WİKİTEXT — TABLO BLOKLARI VE GRİD (rowspan/colspan açılır)
# ======================================================================================

def wikitablo_bloklari(wikitext: str) -> list[list[str]]:
    """Her `{|` … `|}` bloğunun SATIR LİSTESİNİ döndürür (iç içe tabloda derinlik sayılır)."""
    bloklar: list[list[str]] = []
    yigin: list[list[str]] = []
    for satir in wikitext.split("\n"):
        s = satir.lstrip()
        if s.startswith("{|"):
            yigin.append([])
            continue
        if s.startswith("|}") and yigin:
            bitti = yigin.pop()
            if yigin:
                yigin[-1].append(satir)
            bloklar.append(bitti)
            continue
        if yigin:
            yigin[-1].append(satir)
    while yigin:                       # kapanmamış tablo — içeriği KAYBEDİLMEZ, blok olarak alınır
        bloklar.append(yigin.pop())
    return bloklar


def blok_hucreleri(satirlar: list[str]) -> list[list[dict]]:
    """Blok satırlarını HAM hücre satırlarına çevirir. Her hücre: {ham, nitelikler, rowspan,
    colspan, baslik}. `|` ile başlamayan satır ÖNCEKİ hücrenin DEVAMIDIR (çok satırlı `<ref>`)."""
    satir_listesi: list[list[dict]] = []
    acik: list[dict] | None = None
    for ham_satir in satirlar:
        s = ham_satir.rstrip("\n")
        duz = s.lstrip()
        if duz.startswith("|-"):
            acik = []
            satir_listesi.append(acik)
            continue
        if duz.startswith("|+"):       # tablo başlığı (caption) — hücre değil
            continue
        if duz.startswith("!") or duz.startswith("|"):
            if acik is None:
                acik = []
                satir_listesi.append(acik)
            baslik = duz.startswith("!")
            govde = duz[1:]
            parcalar = []
            if baslik:
                for p in derinlik_bol(govde, "!!"):
                    parcalar.extend(derinlik_bol(p, "||"))
            else:
                parcalar = derinlik_bol(govde, "||")
            for p in parcalar:
                nitelikler, icerik = nitelik_ayir(p)
                acik.append({"ham": icerik, "nitelikler": nitelikler, "baslik": baslik,
                             "rowspan": _span(nitelikler, "rowspan"),
                             "colspan": _span(nitelikler, "colspan")})
            continue
        if acik:                       # devam satırı — son hücreye eklenir (çok satırlı ref/metin)
            acik[-1]["ham"] = acik[-1]["ham"] + "\n" + s
    return [r for r in satir_listesi if r]


def grid_ac(satir_listesi: list[list[dict]]) -> list[list[dict]]:
    """rowspan/colspan'i açar: her çıktı satırı SÜTUN SAYISI kadar hücre taşır; `rowspan`lı hücre
    alt satır(lar)a DEVREDİLİR (tarih hücresi devralma — modül başlığı)."""
    grid: list[list[dict]] = []
    bekleyen: dict[int, list] = {}          # sütun → [kalan_satir, hucre]
    for satir in satir_listesi:
        cikti: list[dict] = []
        ci = 0
        idx = 0
        while True:
            while ci in bekleyen and bekleyen[ci][0] > 0:
                cikti.append(bekleyen[ci][1])
                bekleyen[ci][0] -= 1
                if bekleyen[ci][0] == 0:
                    del bekleyen[ci]
                ci += 1
            if idx >= len(satir):
                break
            hucre = satir[idx]
            idx += 1
            for _ in range(hucre["colspan"]):
                cikti.append(hucre)
                if hucre["rowspan"] > 1:
                    bekleyen[ci] = [hucre["rowspan"] - 1, hucre]
                ci += 1
        grid.append(cikti)
    return grid


def kolon_adlari(baslik_grid: list[list[dict]]) -> list[str]:
    """İki (ya da bir) satırlık başlık grid'ini DÜZ sütun adlarına indirger: aynı hücre rowspan'la
    tekrar ediyorsa ad TEK KEZ yazılır → "Date", "Added_Ticker", …"""
    if not baslik_grid:
        return []
    genislik = max(len(r) for r in baslik_grid)
    adlar: list[str] = []
    for j in range(genislik):
        parcalar: list[str] = []
        for satir in baslik_grid:
            if j < len(satir):
                ad = wiki_sadele(satir[j]["ham"]).strip()
                if ad and (not parcalar or parcalar[-1] != ad):
                    parcalar.append(ad)
        adlar.append("_".join(parcalar).replace(" ", "_"))
    return adlar


# ======================================================================================
# WİKİ METNİ SADELEŞTİRME
# ======================================================================================

REF_RE = re.compile(r"<ref\b[^>]*/>|<ref\b[^>]*>[\s\S]*?</ref>", re.IGNORECASE)
URL_RE = re.compile(r"\|\s*url\s*=\s*([^\s|}\]]+)", re.IGNORECASE)
LINK_RE = re.compile(r"\[\[([^\]|]+)(?:\|([^\]]*))?\]\]")
TMPL_RE = re.compile(r"\{\{[^{}]*\}\}")


def ref_ayikla(ham: str) -> tuple[str, list[str]]:
    """`<ref>…</ref>` bloklarını metinden ÇIKARIR, içlerindeki `url=…` adreslerini DÖNDÜRÜR
    (kaynaksız satır sayısı ölçülebilsin — sessizce atmak Yasa 4 ihlali olurdu)."""
    urller: list[str] = []
    for ref in REF_RE.findall(ham or ""):
        urller.extend(URL_RE.findall(ref))
    return REF_RE.sub("", ham or ""), urller


def wiki_sadele(ham: str) -> str:
    """`[[Ad|Görünen]]`→"Görünen", `[[Ad]]`→"Ad", `<ref>` yok, şablon yok, `'''kalın'''` yok."""
    s, _ = ref_ayikla(ham or "")
    s = LINK_RE.sub(lambda m: (m.group(2) if m.group(2) is not None else m.group(1)), s)
    onceki = None
    while onceki != s:                  # iç içe şablonlar dıştan içe temizlenir
        onceki = s
        s = TMPL_RE.sub("", s)
    s = re.sub(r"<[^>]+>", "", s)
    s = s.replace("'''", "").replace("''", "").replace("&nbsp;", " ").replace("\xa0", " ")
    s = re.sub(r"\s+", " ", s)
    return s.strip()


# ======================================================================================
# HEDEF TABLO VE SATIRLAR
# ======================================================================================

def hedef_tablo_bul(wikitext: str):
    """Değişiklik-günlüğü ŞEMASINA (tarih + en az bir yön sütunu) uyan İLK wikitabloyu döndürür.
    `id`ye ÇİVİLENMEZ — sütun eşleştirmesi EDG-075'in `_kolon_bul`u ile yapılır (ithal)."""
    bloklar = wikitablo_bloklari(wikitext)
    tum_kolonlar = []
    for i, blok in enumerate(bloklar):
        satirlar = blok_hucreleri(blok)
        if not satirlar:
            tum_kolonlar.append([])
            continue
        grid = grid_ac(satirlar)
        baslik_grid = []
        veri_grid = []
        for satir in grid:
            if satir and all(h["baslik"] for h in satir) and not veri_grid:
                baslik_grid.append(satir)
            else:
                veri_grid.append(satir)
        kolonlar = kolon_adlari(baslik_grid)
        tum_kolonlar.append(kolonlar)
        dcol = ORTAK._kolon_bul(kolonlar, "date")
        acol_ticker = ORTAK._kolon_bul(kolonlar, "added", "ticker")
        rcol_ticker = ORTAK._kolon_bul(kolonlar, "removed", "ticker")
        acol_any = acol_ticker or ORTAK._kolon_bul(kolonlar, "added")
        rcol_any = rcol_ticker or ORTAK._kolon_bul(kolonlar, "removed")
        if dcol and (acol_any or rcol_any):
            meta = {
                "tablo_index": i, "n_tablo": len(bloklar), "kolonlar": kolonlar,
                "eslenen": {
                    "tarih": dcol, "eklenen_ticker": acol_any,
                    "eklenen_ad": ORTAK._kolon_bul(kolonlar, "added", haric="ticker") if acol_ticker else None,
                    "cikan_ticker": rcol_any,
                    "cikan_ad": ORTAK._kolon_bul(kolonlar, "removed", haric="ticker") if rcol_ticker else None,
                    "neden": ORTAK._kolon_bul(kolonlar, "reason"),
                },
            }
            return i, kolonlar, veri_grid, meta
    return None, [], [], {"tablo_index": None, "n_tablo": len(bloklar), "kolonlar_tum": tum_kolonlar}


def tabloyu_ayristir(wikitext: str) -> tuple[list[dict], dict]:
    """(degisiklikler, meta). Satır şeması EDG-075 ile AYNI (`tarih`, `tarih_ham`, `eklenen`,
    `cikan`, `neden`) + bu kaynağa özgü `eklenen_ad`/`cikan_ad`/`urller`/`satir_no`."""
    idx, kolonlar, veri_grid, meta = hedef_tablo_bul(wikitext)
    if idx is None:
        return [], meta
    e = meta["eslenen"]

    def _al(satir: list[dict], ad: str | None) -> str:
        if not ad or ad not in kolonlar:
            return ""
        j = kolonlar.index(ad)
        return satir[j]["ham"] if j < len(satir) else ""

    rows: list[dict] = []
    hayalet = 0
    for no, satir in enumerate(veri_grid):
        tarih_ham = wiki_sadele(_al(satir, e["tarih"]))
        eklenen = ORTAK._tick(wiki_sadele(_al(satir, e["eklenen_ticker"]))) if e["eklenen_ticker"] else None
        cikan = ORTAK._tick(wiki_sadele(_al(satir, e["cikan_ticker"]))) if e["cikan_ticker"] else None
        neden_ham = _al(satir, e["neden"])
        _, urller = ref_ayikla(neden_ham)
        for ad in (e["tarih"], e["eklenen_ticker"], e["cikan_ticker"], e["eklenen_ad"], e["cikan_ad"]):
            urller.extend(ref_ayikla(_al(satir, ad))[1])
        neden = wiki_sadele(neden_ham)
        if not (tarih_ham or eklenen or cikan or neden):
            hayalet += 1
            continue
        rows.append({
            "tarih": ORTAK._tarihi_isoya_cevir(tarih_ham), "tarih_ham": tarih_ham,
            "eklenen": eklenen, "cikan": cikan, "neden": neden or None,
            "eklenen_ad": wiki_sadele(_al(satir, e["eklenen_ad"])) or None,
            "cikan_ad": wiki_sadele(_al(satir, e["cikan_ad"])) or None,
            "urller": sorted(set(urller)), "satir_no": no,
        })
    meta["satir_n_ham"] = len(veri_grid)
    meta["hayalet_atlanan_n"] = hayalet
    meta["satir_n_gecerli"] = len(rows)
    meta["tarih_cozulemeyen_n"] = sum(1 for r in rows if r["tarih"] is None)
    meta["kaynaksiz_satir_n"] = sum(1 for r in rows if not r["urller"])
    return rows, meta


# ======================================================================================
# ADIM-0
# ======================================================================================

def adim0(wikitext: str, girdi_kimligi: dict, kart: dict, bugun: str | None = None,
          beklenen_sha: str | None = None) -> dict:
    """Kart `adim_0_fizibilite` (1)(2) + `--beklenen-sha` + kart iç tutarlılığı. `gecerli=False`
    ise K1/PK'ler KOŞMAZ (EDG-076 deseni) — sonuç YİNE yazılır (Yasa 6)."""
    bugun = bugun or dt.date.today().isoformat()
    esikler = esikleri_karttan_al(kart)
    baslangic = pencere_baslangici_karttan(kart)
    degisiklikler, meta = tabloyu_ayristir(wikitext)
    tablo_var = meta.get("tablo_index") is not None
    pencere = ORTAK.pencereye_kirp(degisiklikler, baslangic=baslangic, bitis=bugun) if tablo_var else []
    cozulemeyen = [{"satir_no": r["satir_no"], "tarih_ham": r["tarih_ham"], "eklenen": r["eklenen"],
                    "cikan": r["cikan"]} for r in degisiklikler if r["tarih"] is None]

    sha_hesaplanan = hashlib.sha256(wikitext.encode("utf-8")).hexdigest()
    sha_esit = None if beklenen_sha is None else (sha_hesaplanan == beklenen_sha)
    tutarlilik = ORTAK.kart_ic_tutarliligi(kart, bugun)

    nedenler: list[str] = []
    if not tablo_var:
        nedenler.append("değişiklik tablosu bulunamadı (başlık sütunları eşleşmedi)")
    if sha_esit is False:
        nedenler.append(f"--beklenen-sha uyuşmuyor: beklenen={beklenen_sha} hesaplanan={sha_hesaplanan}")
    if not tutarlilik["gecerli"]:
        nedenler.extend(tutarlilik["ihlaller"])

    gecerli = bool(tablo_var and sha_esit is not False and tutarlilik["gecerli"])
    yeterli = len(pencere) >= esikler["pencere_satir_alt"]
    return {
        "tablo_bulundu": tablo_var, "tablo_meta": meta,
        "pencere_baslangici": baslangic, "bugun": bugun,
        "satir_n_gecerli": meta.get("satir_n_gecerli", 0),
        "pencere_satir_n": len(pencere),
        "pencere_satir_alt": esikler["pencere_satir_alt"],
        "pencere_satir_yeterli": yeterli,
        "askiya_veri_kapisi": (not yeterli),   # kart kill-list: kill DEĞİL, askıya
        "tarih_cozulemeyen_n": len(cozulemeyen), "tarih_cozulemeyen_satirlar": cozulemeyen,
        "kaynaksiz_satir_n": meta.get("kaynaksiz_satir_n"),
        "sha_beklenen": beklenen_sha, "sha_hesaplanan": sha_hesaplanan, "sha_esit_mi": sha_esit,
        "kart_ic_tutarli": tutarlilik["gecerli"], "kart_ic_ihlaller": tutarlilik["ihlaller"],
        "girdi_kimligi": girdi_kimligi,
        "gecerli": gecerli, "neden": None if gecerli else "; ".join(nedenler),
    }


# ======================================================================================
# K1
# ======================================================================================

def olay_kumesi(kart: dict) -> tuple[list[dict], int, list[dict]]:
    """K1 olayları KARTTAN (EDG-075 `k1_olaylari_ve_beyan` — İTHAL). İki yerel ek, ikisi de
    EŞLEŞTİRME MANTIĞINA DOKUNMAZ:

      (a) `yon_kaynak`: EDG-092 kartı kaynağı `url`/`neden` alanında taşır (EDG-076 `kaynak`
          yerine); ithal fonksiyon bu alanı None bırakır, burada YALNIZ O ALAN doldurulur.
      (b) SEMBOL NORMALİZASYONU: tablo tarafındaki semboller `ORTAK._tick` ile normalleşir
          ("MOG.A" → "MOG-A"); kart tarafı ham literal kalırsa nokta taşıyan HER sembol sessizce
          "bulunamadı" sayılır (ilk koşumda MOG.A tam da böyle düştü, 2026-09-14). İki taraf AYNI
          fonksiyonla normalleşir — tek kaynak; değişen semboller `normalizasyon`da RAPORLANIR.
    """
    olaylar, beyan_n = ORTAK.k1_olaylari_ve_beyan(kart)
    ham = kart.get("bilinen_olaylar") if isinstance(kart, dict) else None
    if isinstance(ham, list) and len(ham) == len(olaylar):
        for o, h in zip(olaylar, ham):
            if o.get("yon_kaynak") is None:
                o["yon_kaynak"] = h.get("url") or h.get("neden")
    normalizasyon: list[dict] = []
    for o in olaylar:
        kart_literali = o["sembol"]
        o["sembol"] = ORTAK._tick(kart_literali) or kart_literali
        if o["sembol"] != kart_literali:
            normalizasyon.append({"kart_literali": kart_literali, "normal": o["sembol"],
                                  "kural": "ORTAK._tick — tablo tarafıyla AYNI fonksiyon"})
    return olaylar, beyan_n, normalizasyon


def k1_kapsama(degisiklikler: list[dict], olaylar: list[dict], kart_beyan_n: int,
               tolerans_gun: int = 1) -> dict:
    """EDG-075 `k1_bilinen_olaylar` (İTHAL) + kapsama oranı + kart-beyan AYRIŞMA bayrağı."""
    ham = ORTAK.k1_bilinen_olaylar(degisiklikler, olaylar, tolerans_gun=tolerans_gun,
                                   kart_beyan_n=kart_beyan_n)
    n = ham["olculen_n"]
    ham["kapsama_orani"] = (ham["n_tam_gecti"] / n) if n else None
    ham["kapsama_orani_neden"] = None if n else "olay kümesi boş — oran ölçülemez"
    ham["beyan_ayrismasi"] = bool(kart_beyan_n != n)
    ham["farkli_yururluk_tarihi_n"] = len({o["tarih"] for o in olaylar})
    return ham


# ======================================================================================
# PK-1 — GELECEK OLAYLAR
# ======================================================================================

def pk1_gelecek_olaylar(degisiklikler: list[dict], kart: dict, guncel_uyeler: list[str] | None,
                        bugun: str, tolerans_gun: int = 1) -> dict:
    """EDG-075 `k1n_gelecek_olaylar` (İTHAL) + `tuttu` (hepsi geçti mi)."""
    out = ORTAK.k1n_gelecek_olaylar(degisiklikler, kart, guncel_uyeler, bugun, tolerans_gun)
    out["tuttu"] = bool(out.get("calisti") and out.get("n") and out["n_gecti"] == out["n"])
    return out


# ======================================================================================
# PK-2 — RENAME RAPORU
# ======================================================================================

def _not_sembolleri(metin: str) -> list[str]:
    bulunan = []
    for s in NOT_SEMBOL_RE.findall(metin or ""):
        t = ORTAK._tick(s)
        if t and t not in NOT_SEMBOL_HARIC and t not in bulunan:
            bulunan.append(t)
    return bulunan


def pk2_rename_raporu(degisiklikler: list[dict], kart: dict, guncel_uyeler: list[str] | None,
                      bugun: str, tolerans_gun: int = 1) -> dict:
    """Kart `rename_vakalari` RAPORU + mekanik kapı.

    Kart bu vakalarda `eski`/`yeni` ALANI TAŞIMAZ (yalnız düzyazı `not`) — o yüzden hiçbir sembol
    "eski"/"yeni" diye ETİKETLENMEZ (`eski_yeni_ayrimi: None`), yalnız kartın KENDİ yazdığı iki
    işaret makine tarafından okunur, ikisi de AÇIK regexle ve kaynağı beyan edilerek:
      * `X↑ Y↓`  (kartın "tablo satırı …" ifadesi)  → o tarihte BEKLENEN satır,
      * `X→Y`    (kartın yeniden-adlandırma çifti)  → üyelik değişikliği SAYILMAMASI gereken çift.

    MEKANİK KAPI (`tuttu`), vaka bazında:
      (i)  `↑↓` ile yazılı satır tabloda O TARİHTE (±`tolerans_gun` iş günü) GERÇEKTEN var mı,
      (ii) `→` ile yazılı yeniden-adlandırma çiftinin HİÇBİR ucu o tarihte eklenen/çıkan olarak
           KİTAPLANMAMIŞ mı (yani rename bir üyelik değişikliği gibi yazılmamış mı).
    Kart bir vakada o işareti taşımıyorsa ilgili ölçüt `None` kalır ve vakayı DÜŞÜRMEZ (uydurma
    yasağı: ölçülemeyen şey "kaldı" sayılmaz).

    GEREKÇE METNİ TEK BAŞINA KAPI DEĞİLDİR (ölçülmüş yanlış-pozitif, 2026-09-14): 2024-10-01
    satırı ENSG↑/SWN↓ GERÇEK bir üyelik değişikliğidir, ama gerekçesinde birleşik şirketin adının
    değiştiği ANLATILIR — "gerekçede rename geçiyor" kuralı bu satırı yanlışlıkla ihlal saymıştı.
    O tarama artık KAPI değil RAPORDUR (`yeniden_adlandirma_gerekceli_satirlar`, kaynak sınıfı
    ölçümü — Rol-1 okur)."""
    vakalar = kart.get("rename_vakalari") if isinstance(kart, dict) else None
    if not isinstance(vakalar, list) or not vakalar:
        return {"calisti": False, "neden": "kartta rename_vakalari yok", "tuttu": None}
    if guncel_uyeler is None:
        return {"calisti": False, "neden": "güncel liste sağlanmadı — as_of hesaplanamaz", "tuttu": None}
    gu = {ORTAK._tick(s) for s in guncel_uyeler if ORTAK._tick(s)}
    a_bugun = ORTAK.as_of(degisiklikler, gu, bugun)

    detay = []
    olculen_olcut = 0
    dusen_olcut = 0
    for vaka in vakalar:
        tarih = vaka.get("tarih")
        notu = vaka.get("not") or ""
        semboller = _not_sembolleri(notu)
        satirlar = [r for r in degisiklikler
                    if r["tarih"] and tarih and ORTAK._is_gunu_farki_icinde(r["tarih"], tarih, tolerans_gun)]
        satirdaki = {r["eklenen"] for r in satirlar if r["eklenen"]} | {r["cikan"] for r in satirlar if r["cikan"]}
        a_tarih = ORTAK.as_of(degisiklikler, gu, tarih) if tarih else set()

        m_satir = SATIR_BEKLENTI_RE.search(notu)
        beklenen_satir = None
        beklenen_satir_var = None
        if m_satir:
            beklenen_satir = {"eklenen": ORTAK._tick(m_satir.group(1)), "cikan": ORTAK._tick(m_satir.group(2))}
            beklenen_satir_var = any(r["eklenen"] == beklenen_satir["eklenen"]
                                     and r["cikan"] == beklenen_satir["cikan"] for r in satirlar)
            olculen_olcut += 1
            if beklenen_satir_var is False:
                dusen_olcut += 1

        m_ok = RENAME_OK_RE.search(notu)
        rename_cifti = None
        rename_kitaplandi = None
        if m_ok:
            rename_cifti = {"eski": ORTAK._tick(m_ok.group(1)), "yeni": ORTAK._tick(m_ok.group(2))}
            rename_kitaplandi = bool({rename_cifti["eski"], rename_cifti["yeni"]} & satirdaki)
            olculen_olcut += 1
            if rename_kitaplandi:
                dusen_olcut += 1

        detay.append({
            "tarih": tarih, "kart_notu": notu,
            "sembol_kaynagi": ("kartın KENDİ işaretleri okundu: `X↑ Y↓` beklenen satır, `X→Y` "
                               "yeniden-adlandırma çifti; serbest semboller regexle — kartta "
                               "eski/yeni ALANI YOK, Rol-1 doğrular (uydurma yasağı)"),
            "eski_yeni_ayrimi": None,
            "eski_yeni_ayrimi_neden": ("kartta `eski`/`yeni` alanı yok; `→` işareti varsa çift "
                                       "`rename_cifti`de yönüyle raporlanır, yoksa None"),
            "beklenen_satir": beklenen_satir, "beklenen_satir_var": beklenen_satir_var,
            "rename_cifti": rename_cifti,
            "rename_degisiklik_olarak_kitaplandi": rename_kitaplandi,
            "rename_cifti_as_of": (None if not rename_cifti else {
                "eski_as_of_tarih_uye_mi": rename_cifti["eski"] in a_tarih,
                "yeni_as_of_tarih_uye_mi": rename_cifti["yeni"] in a_tarih,
                "eski_as_of_bugun_uye_mi": rename_cifti["eski"] in a_bugun,
                "yeni_as_of_bugun_uye_mi": rename_cifti["yeni"] in a_bugun,
            }),
            "not_sembolleri": [
                {"sembol": s, "satirda_var_mi": s in satirdaki,
                 "as_of_tarih_uye_mi": (s in a_tarih) if tarih else None,
                 "as_of_bugun_uye_mi": s in a_bugun}
                for s in semboller
            ],
            "tablodaki_satirlar": [
                {"tarih": r["tarih"], "eklenen": r["eklenen"], "cikan": r["cikan"], "neden": r["neden"]}
                for r in satirlar
            ],
            "gecti": (beklenen_satir_var is not False) and (rename_kitaplandi is not True),
        })

    taranan = [{"tarih": r["tarih"], "eklenen": r["eklenen"], "cikan": r["cikan"], "neden": r["neden"]}
               for r in degisiklikler if RENAME_SOZLUGU.search(r["neden"] or "")]
    return {"calisti": True, "detay": detay,
            "olculen_olcut_n": olculen_olcut, "dusen_olcut_n": dusen_olcut,
            "yeniden_adlandirma_gerekceli_satirlar": taranan,
            "yeniden_adlandirma_gerekceli_n": len(taranan),
            "gerekce_taramasi_kapi_mi": False,
            "gerekce_taramasi_notu": ("gerekçe metni KAPI DEĞİL — 2024-10-01 satırı (ENSG↑/SWN↓) "
                                      "gerçek değişiklik olduğu hâlde gerekçesinde rename anlatılıyor; "
                                      "bu tarama kaynak sınıfı RAPORUdur"),
            "tuttu": (None if olculen_olcut == 0 else dusen_olcut == 0),
            "neden": (None if olculen_olcut else
                      "kart notlarında `X↑ Y↓` / `X→Y` işareti yok — mekanik ölçüt kurulamadı")}


# ======================================================================================
# PK-3 — GÜNCEL LİSTE (SPDR MDY holdings, stdlib zipfile)
# ======================================================================================

XL_NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
TICKER_RE = re.compile(r"^[A-Z][A-Z0-9]{0,4}([.-][A-Z])?$")


def mdy_tickerlari(xlsx_yolu: pathlib.Path) -> tuple[list[str], dict]:
    """SPDR MDY holdings xlsx → ticker listesi. `openpyxl` venv'de YOK (ölçüldü 2026-09-14), bu
    yüzden stdlib `zipfile` + `xml.etree`. BEYANLI DIŞLAMA: ticker biçimine (`TICKER_RE`) uymayan
    satırlar (nakit/ETF artığı, ör. `CASH_USD`) hisse DEĞİLDİR ve `haric_tutulan`da ADIYLA
    raporlanır — sessizce atılmaz (Yasa 4 ruhu)."""
    z = zipfile.ZipFile(pathlib.Path(xlsx_yolu))
    adlar = set(z.namelist())
    havuz: list[str] = []
    if "xl/sharedStrings.xml" in adlar:
        kok = ET.fromstring(z.read("xl/sharedStrings.xml"))
        havuz = ["".join(t.text or "" for t in si.iter(XL_NS + "t")) for si in kok]
    sayfa_adi = next((a for a in sorted(adlar) if a.startswith("xl/worksheets/sheet")), None)
    if sayfa_adi is None:
        raise ValueError(f"xlsx içinde çalışma sayfası yok: {xlsx_yolu}")
    sayfa = ET.fromstring(z.read(sayfa_adi))

    satirlar: list[tuple[int, dict]] = []
    for r in sayfa.iter(XL_NS + "row"):
        hucreler: dict[str, str | None] = {}
        for c in r.iter(XL_NS + "c"):
            ref = c.get("r") or ""
            tip = c.get("t")
            v = c.find(XL_NS + "v")
            if tip == "s" and v is not None and v.text is not None:
                metin = havuz[int(v.text)] if int(v.text) < len(havuz) else None
            elif tip == "inlineStr":
                i_s = c.find(XL_NS + "is")
                metin = "".join(t.text or "" for t in i_s.iter(XL_NS + "t")) if i_s is not None else None
            else:
                metin = v.text if v is not None else None
            hucreler["".join(ch for ch in ref if ch.isalpha())] = metin
        satirlar.append((int(r.get("r") or 0), hucreler))

    as_of = next((v for _, h in satirlar for v in h.values()
                  if isinstance(v, str) and v.strip().lower().startswith("as of")), None)
    baslik_no = None
    ticker_kolon = None
    for no, h in satirlar:
        for kolon, v in h.items():
            if isinstance(v, str) and v.strip().lower() == "ticker":
                baslik_no, ticker_kolon = no, kolon
                break
        if baslik_no is not None:
            break
    if ticker_kolon is None:
        raise ValueError(f"xlsx'te 'Ticker' başlık sütunu bulunamadı: {xlsx_yolu}")

    ham: list[str] = []
    for no, h in satirlar:
        if no <= baslik_no:
            continue
        v = h.get(ticker_kolon)
        if isinstance(v, str) and v.strip():
            ham.append(v.strip().upper())
    tutulan = [t for t in ham if TICKER_RE.match(t)]
    haric = [t for t in ham if not TICKER_RE.match(t)]
    meta = {
        "yol": str(xlsx_yolu), "as_of": as_of, "baslik_satiri": baslik_no,
        "ticker_kolonu": ticker_kolon, "ham_satir_n": len(ham), "tutulan_n": len(tutulan),
        "haric_tutulan": haric,
        "haric_gerekcesi": ("ticker biçimine uymayan satırlar hisse değildir (nakit/ETF artığı) — "
                            f"desen {TICKER_RE.pattern}; beyanla dışarıda, kart PK-3 notu"),
        "okuyucu": "stdlib zipfile+xml.etree (openpyxl venv'de YOK, ölçüldü 2026-09-14)",
    }
    return [ORTAK._tick(t) for t in tutulan], meta


def pk3_guncel_liste(degisiklikler: list[dict], guncel_uyeler: list[str] | None, esik: float,
                     bugun: str, pencere_baslangici: str | None = None) -> dict:
    """`as_of(bugün)` ∩ güncel liste / |liste| ≥ esik.

    TAUTOLOJİ BEYANI: `as_of` TOHUM olarak GÜNCEL LİSTEYİ alır ve geriye sarar; listeden SONRA
    tabloda hiç değişiklik yoksa kesişim 1,0 ÇIKAR — bu bir doğrulama değil, tohumun kendisidir.
    `tautoloji.liste_sonrasi_degisiklik_n` bunu SAYIYLA gösterir. Yanına BİLGİ TAŞIYAN tanı konur:
    `as_of(pencere başı)` üye sayısı — S&P 400 daima 400 üyelidir, sapma tabloda eşleşmemiş
    (yalnız-giren / yalnız-çıkan) satır demektir. Tanının EŞİĞİ YOKTUR (kart eşik tanımlamadı)."""
    if guncel_uyeler is None:
        return {"calisti": False, "neden": "güncel liste sağlanmadı (--guncel-liste)", "tuttu": None}
    gu = {ORTAK._tick(s) for s in guncel_uyeler if ORTAK._tick(s)}
    a_bugun = ORTAK.as_of(degisiklikler, gu, bugun)
    kesisim = a_bugun & gu
    oran = (len(kesisim) / len(gu)) if gu else None
    tarihli = [r["tarih"] for r in degisiklikler if r["tarih"]]
    taban = pencere_baslangici or (min(tarihli) if tarihli else bugun)
    return {
        "calisti": True, "bugun": bugun, "esik": esik,
        "guncel_liste_n": len(gu), "as_of_bugun_n": len(a_bugun), "kesisim_n": len(kesisim),
        "kesisim_orani": oran,
        "sapan_listede_var_as_ofta_yok": sorted(gu - a_bugun),
        "sapan_as_ofta_var_listede_yok": sorted(a_bugun - gu),
        "tuttu": bool(oran is not None and oran >= esik),
        "tautoloji": {
            "liste_sonrasi_degisiklik_n": sum(1 for t in tarihli if t > bugun),
            "beyan": ("as_of TOHUM olarak güncel listeyi alıp geriye sarar; `liste_sonrasi_"
                      "degisiklik_n` 0 ise kesişim 1,0 İNŞAAT GEREĞİ çıkar ve bağımsız bilgi "
                      "TAŞIMAZ — hüküm bu sayıya değil, yanındaki tanıya bakmalı"),
        },
        "tani": {
            "as_of_pencere_basi_tarih": taban,
            "as_of_pencere_basi_n": len(ORTAK.as_of(degisiklikler, gu, taban)),
            "yalniz_giren_satir_n": sum(1 for r in degisiklikler if r["eklenen"] and not r["cikan"]),
            "yalniz_cikan_satir_n": sum(1 for r in degisiklikler if r["cikan"] and not r["eklenen"]),
            "pencere_ici_eslesmemis_satirlar": [
                {"tarih": r["tarih"], "eklenen": r["eklenen"], "cikan": r["cikan"], "neden": r["neden"]}
                for r in degisiklikler
                if r["tarih"] and r["tarih"] >= taban and bool(r["eklenen"]) != bool(r["cikan"])],
            "not": ("S&P 400 daima 400 üyelidir: as_of(pencere başı) 400'den sapıyorsa tabloda "
                    "eşleşmemiş satır vardır. EŞİK YOK — kart tanımlamadı, bu TANIdır (hüküm Rol-1)"),
        },
    }


# ======================================================================================
# PK-4 — YOL TUTARLILIĞI (aynı ayrıştırıcı + aynı K1, EDG-076 sayfası)
# ======================================================================================

def pk4_yol_tutarli(pk_wikitext: str, pk_kart: dict, pencere_baslangici: str, bugun: str,
                    tolerans_gun: int = 1) -> dict:
    """AYNI `tabloyu_ayristir` + AYNI `k1_kapsama`, EDG-076'nın S&P 500 ham wikitext'i ve
    doğrulanmış olay kümesiyle. EDG-076 hükmü 28/28 idi — kod yolu bunu YENİDEN ÜRETMELİ."""
    degisiklikler, meta = tabloyu_ayristir(pk_wikitext)
    if meta.get("tablo_index") is None:
        return {"calisti": False, "neden": "PK sayfasında değişiklik tablosu bulunamadı", "tuttu": False}
    olaylar, beyan_n, normalizasyon = olay_kumesi(pk_kart)
    if not olaylar:
        return {"calisti": False, "neden": "PK kartında bilinen_olaylar yok", "tuttu": None}
    pencere = ORTAK.pencereye_kirp(degisiklikler, baslangic=pencere_baslangici, bitis=bugun)
    k1 = k1_kapsama(pencere, olaylar, kart_beyan_n=beyan_n, tolerans_gun=tolerans_gun)
    return {"calisti": True, "tablo_meta": {k: v for k, v in meta.items() if k != "kolonlar_tum"},
            "sembol_normalizasyonu": normalizasyon,
            "pencere_satir_n": len(pencere), "n": k1["olculen_n"], "n_tam_gecti": k1["n_tam_gecti"],
            "kapsama_orani": k1["kapsama_orani"], "detay": k1["detay"],
            "tuttu": bool(k1["olculen_n"] and k1["n_tam_gecti"] == k1["olculen_n"])}


# ======================================================================================
# TAM ÖLÇÜM
# ======================================================================================

def olc(wikitext: str, kart: dict, girdi_kimligi: dict, guncel_uyeler: list[str] | None,
        bugun: str | None = None, beklenen_sha: str | None = None, pk4: dict | None = None,
        mdy_meta: dict | None = None, pk_kimligi: dict | None = None) -> dict:
    """ADIM-0 → K1 → PK-1/2/3 (+ dışarıdan verilen PK-4) → yayın engeli. ADIM-0 geçersizse
    K1/PK'ler KOŞMAZ ve `None` yazılır (EDG-076 deseni), sonuç YİNE üretilir (Yasa 6)."""
    bugun = bugun or dt.date.today().isoformat()
    esikler = esikleri_karttan_al(kart)
    a0 = adim0(wikitext, girdi_kimligi, kart, bugun=bugun, beklenen_sha=beklenen_sha)
    degisiklikler, _ = tabloyu_ayristir(wikitext)
    olaylar, beyan_n, sembol_normalizasyonu = olay_kumesi(kart)

    if a0["gecerli"]:
        pencere = ORTAK.pencereye_kirp(degisiklikler, baslangic=a0["pencere_baslangici"], bitis=bugun)
        k1 = k1_kapsama(pencere, olaylar, kart_beyan_n=beyan_n)
        k1["olay_n_alt"] = esikler["bilinen_olay_n_alt"]
        k1["olay_n_yeterli"] = k1["olculen_n"] >= esikler["bilinen_olay_n_alt"]
        k1["kapsama_alt"] = esikler["bilinen_olay_kapsama_alt"]
        k1["sembol_normalizasyonu"] = sembol_normalizasyonu
        k1["esik_ustunde_mi"] = (None if k1["kapsama_orani"] is None
                                 else k1["kapsama_orani"] >= esikler["bilinen_olay_kapsama_alt"])
        pk1 = pk1_gelecek_olaylar(degisiklikler, kart, guncel_uyeler, bugun)
        pk2 = pk2_rename_raporu(degisiklikler, kart, guncel_uyeler, bugun)
        pk3 = pk3_guncel_liste(degisiklikler, guncel_uyeler, esikler["guncel_liste_kesisim_alt"],
                               bugun, pencere_baslangici=a0["pencere_baslangici"])
    else:
        k1 = pk1 = pk2 = pk3 = None

    dusenler: list[str] = []
    kosmayanlar: list[str] = []
    for ad, pk in (("PK-1 gelecek-olay", pk1), ("PK-2 rename", pk2), ("PK-3 güncel-liste", pk3),
                   ("PK-4 yol-tutarlılık", pk4)):
        if pk is None:
            kosmayanlar.append(f"{ad}: ADIM-0 geçersiz ya da girdi verilmedi")
        elif pk.get("tuttu") is False:
            dusenler.append(f"{ad} DÜŞTÜ: {pk.get('neden') or 'ölçüm detayına bak'}")
        elif pk.get("tuttu") is None:
            kosmayanlar.append(f"{ad}: {pk.get('neden') or 'koşmadı'}")

    engel = bool(dusenler)
    return {
        "kart": esikler.get("kart_id"), "damga": damga(),
        "olcum_zamani": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "bugun": bugun, "girdi_kimligi": girdi_kimligi, "pk_girdi_kimligi": pk_kimligi,
        "guncel_liste_meta": mdy_meta,
        "adim0": a0, "k1": k1, "pk1": pk1, "pk2": pk2, "pk3": pk3, "pk4": pk4,
        "esikler": esikler,
        "yayin_engeli": {
            "engel": engel,
            "neden": dusenler,
            "kural": "kart kill_list #5 — PK'lerden biri düşerse hiçbir kapsama sayısı YAYILMAZ",
        },
        "kosmayan_pkler": kosmayanlar,
        "k1_kapsama_yayinlanabilir": (None if (engel or k1 is None) else k1["kapsama_orani"]),
        "hukum": "YOK — Rol-1",
        "beyan": ("Bu betik yalnız ÖLÇER. Hüküm Rol-1'de, AYNI turda karta + K defterine işlenir "
                  "(CLAUDE.md §3/§5). meridian/*.py bu turda DEĞİŞTİRİLMEDİ; ağa çıkılmadı "
                  "(`cek()` hiç çağrılmadı), canlı state'e yazılmadı."),
    }


# ======================================================================================
# MARKDOWN RAPOR (okuyucu: Rol-1 — Yasa 6)
# ======================================================================================

def _bayrak(deger) -> str:
    return {True: "EVET", False: "HAYIR", None: "ÖLÇÜLEMEDİ"}.get(deger, str(deger))


def rapor_markdown(sonuc: dict) -> str:
    a0 = sonuc["adim0"]
    sat: list[str] = []
    sat.append(f"# EDG-2026-092 ölçüm raporu — {sonuc['damga']}")
    sat.append("")
    sat.append(f"- Kart: `{sonuc['kart']}` · hüküm: **{sonuc['hukum']}** (bu belge hüküm TAŞIMAZ)")
    sat.append(f"- Girdi: `{sonuc['girdi_kimligi'].get('yol')}` sha256 `{a0['sha_hesaplanan']}`")
    if sonuc.get("pk_girdi_kimligi"):
        sat.append(f"- PK-4 girdisi: `{sonuc['pk_girdi_kimligi'].get('yol')}` "
                   f"sha256 `{sonuc['pk_girdi_kimligi'].get('sha256')}`")
    if sonuc.get("guncel_liste_meta"):
        g = sonuc["guncel_liste_meta"]
        sat.append(f"- Güncel liste: `{g.get('yol')}` ({g.get('as_of')}) "
                   f"{g.get('tutulan_n')} hisse, hariç: {g.get('haric_tutulan')}")
    sat.append(f"- Ölçüm günü (`--bugun`): {sonuc['bugun']} · pencere başı: {a0['pencere_baslangici']}")
    sat.append("")

    sat.append("## ADIM-0")
    sat.append("")
    sat.append("| Ölçüt | Değer |")
    sat.append("|---|---|")
    sat.append(f"| Tablo bulundu (başlık sütunlarından) | {_bayrak(a0['tablo_bulundu'])} |")
    sat.append(f"| Eşleşen sütunlar | `{a0['tablo_meta'].get('eslenen')}` |")
    sat.append(f"| Geçerli satır | {a0['satir_n_gecerli']} |")
    sat.append(f"| Pencere satırı ({a0['pencere_baslangici']}+) | {a0['pencere_satir_n']} "
               f"(eşik {a0['pencere_satir_alt']:.0f} → {_bayrak(a0['pencere_satir_yeterli'])}) |")
    sat.append(f"| Tarihi çözülemeyen satır | {a0['tarih_cozulemeyen_n']} |")
    sat.append(f"| Kaynak (ref url) taşımayan satır | {a0['kaynaksiz_satir_n']} |")
    sat.append(f"| `--beklenen-sha` eşit mi | {_bayrak(a0['sha_esit_mi'])} |")
    sat.append(f"| Kart iç tutarlılığı | {_bayrak(a0['kart_ic_tutarli'])} |")
    sat.append(f"| ADIM-0 geçerli | {_bayrak(a0['gecerli'])} {('— ' + a0['neden']) if a0['neden'] else ''} |")
    sat.append("")
    if a0["tarih_cozulemeyen_satirlar"]:
        sat.append("### Tarihi çözülemeyen satırlar (ADIYLA — uydurma yok)")
        sat.append("")
        sat.append("| satır | ham tarih | eklenen | çıkan |")
        sat.append("|---|---|---|---|")
        for r in a0["tarih_cozulemeyen_satirlar"]:
            sat.append(f"| {r['satir_no']} | `{r['tarih_ham']}` | {r['eklenen']} | {r['cikan']} |")
        sat.append("")

    engel = sonuc["yayin_engeli"]
    sat.append("## K1 — bilinen olay kapsaması")
    sat.append("")
    if sonuc["k1"] is None:
        sat.append(f"KOŞMADI — ADIM-0 geçersiz: {a0['neden']}")
    elif engel["engel"]:
        sat.append("**YAYIN ENGELİ** — kart kill_list #5: pozitif kontrollerden biri düştü, "
                   "kapsama sayısı bu raporda YAYILMAZ.")
        for n in engel["neden"]:
            sat.append(f"- {n}")
        sat.append("")
        sat.append("Olay olay tablo yine aşağıdadır (Rol-1 okur); ORAN bilinçli olarak yazılmadı.")
    else:
        k1 = sonuc["k1"]
        sat.append(f"KAPSAMA ORANI: **{k1['n_tam_gecti']}/{k1['olculen_n']} = "
                   f"{k1['kapsama_orani']:.4f}** (kart eşiği {k1['kapsama_alt']:.2f} → "
                   f"{_bayrak(k1['esik_ustunde_mi'])})")
        sat.append("")
        sat.append(f"- olay n {k1['olculen_n']} ≥ eşik {k1['olay_n_alt']:.0f}: "
                   f"{_bayrak(k1['olay_n_yeterli'])} · farklı yürürlük tarihi: "
                   f"{k1['farkli_yururluk_tarihi_n']}")
        sat.append(f"- kart beyan n {k1['kart_beyan_n']} vs ölçülen n {k1['olculen_n']} → "
                   f"ayrışma: {_bayrak(k1['beyan_ayrismasi'])}")
        if k1.get("sembol_normalizasyonu"):
            sat.append(f"- sembol normalizasyonu (kart literali → tablo biçimi): "
                       f"{[(n['kart_literali'], n['normal']) for n in k1['sembol_normalizasyonu']]}")
    sat.append("")
    if sonuc["k1"]:
        sat.append("| sembol | beklenen yön | beklenen tarih | bulunan tarih | satır var | ±1 iş günü | yön doğru |")
        sat.append("|---|---|---|---|---|---|---|")
        for d in sonuc["k1"]["detay"]:
            sat.append(f"| {d['sembol']} | {d['beklenen_yon']} | {d['beklenen_tarih']} | "
                       f"{d['bulunan_tarih']} | {_bayrak(d['satir_var'])} | "
                       f"{_bayrak(d['tarih_tolerans_icinde'])} | {_bayrak(d['yon_dogru'])} |")
        sat.append("")

    sat.append("## Pozitif kontroller")
    sat.append("")
    sat.append("| PK | tuttu | özet |")
    sat.append("|---|---|---|")
    pk1, pk2, pk3, pk4 = sonuc["pk1"], sonuc["pk2"], sonuc["pk3"], sonuc["pk4"]
    if pk1:
        sat.append(f"| PK-1 gelecek olay | {_bayrak(pk1.get('tuttu'))} | "
                   f"{pk1.get('n_gecti')}/{pk1.get('n')} olgu beklendiği gibi |")
    if pk2:
        sat.append(f"| PK-2 rename | {_bayrak(pk2.get('tuttu'))} | "
                   f"{len(pk2.get('detay') or [])} vaka raporlandı · rename gerekçeli satır: "
                   f"{pk2.get('yeniden_adlandirma_gerekceli_n')} |")
    if pk3:
        oran = pk3.get("kesisim_orani")
        sat.append(f"| PK-3 güncel liste | {_bayrak(pk3.get('tuttu'))} | "
                   f"{pk3.get('kesisim_n')}/{pk3.get('guncel_liste_n')} = "
                   f"{oran:.4f} (eşik {pk3.get('esik')}) |" if oran is not None else
                   f"| PK-3 güncel liste | {_bayrak(pk3.get('tuttu'))} | ölçülemedi |")
    if pk4:
        sat.append(f"| PK-4 yol tutarlılığı | {_bayrak(pk4.get('tuttu'))} | "
                   f"{pk4.get('n_tam_gecti')}/{pk4.get('n')} (EDG-076 hükmü 28/28) |")
    sat.append("")
    if sonuc["kosmayan_pkler"]:
        sat.append("KOŞMAYAN pozitif kontroller (geçti SAYILMAZ — uydurma yasağı):")
        for n in sonuc["kosmayan_pkler"]:
            sat.append(f"- {n}")
        sat.append("")
    if pk3:
        t = pk3["tautoloji"]
        sat.append(f"> PK-3 TAUTOLOJİ BEYANI: listeden sonraki değişiklik sayısı "
                   f"{t['liste_sonrasi_degisiklik_n']}. {t['beyan']}")
        sat.append(f"> TANI: as_of({pk3['tani']['as_of_pencere_basi_tarih']}) üye sayısı "
                   f"{pk3['tani']['as_of_pencere_basi_n']} · yalnız-giren satır "
                   f"{pk3['tani']['yalniz_giren_satir_n']} · yalnız-çıkan satır "
                   f"{pk3['tani']['yalniz_cikan_satir_n']}. {pk3['tani']['not']}")
        sat.append("")
        eslesmemis = pk3["tani"].get("pencere_ici_eslesmemis_satirlar") or []
        if eslesmemis:
            sat.append(f"### Pencere içi EŞLEŞMEMİŞ satırlar ({len(eslesmemis)}) — as_of kaymasının kaynağı")
            sat.append("")
            sat.append("| tarih | eklenen | çıkan | gerekçe |")
            sat.append("|---|---|---|---|")
            for r in eslesmemis:
                sat.append(f"| {r['tarih']} | {r['eklenen']} | {r['cikan']} | {(r['neden'] or '')[:110]} |")
            sat.append("")
    if pk2 and pk2.get("detay"):
        sat.append("### PK-2 rename vakaları (RAPOR — eski/yeni ayrımı YAPILMADI, kartta alan yok)")
        sat.append("")
        for v in pk2["detay"]:
            sat.append(f"- **{v['tarih']}** (geçti: {_bayrak(v['gecti'])}) — tablo satırları: "
                       f"{[(r['eklenen'], r['cikan']) for r in v['tablodaki_satirlar']]}")
            sat.append(f"  - kartın `X↑ Y↓` beklentisi: {v['beklenen_satir']} → tabloda var: "
                       f"{_bayrak(v['beklenen_satir_var'])}")
            sat.append(f"  - kartın `X→Y` yeniden-adlandırma çifti: {v['rename_cifti']} → "
                       f"üyelik değişikliği olarak kitaplandı: "
                       f"{_bayrak(v['rename_degisiklik_olarak_kitaplandi'])}")
            if v["rename_cifti_as_of"]:
                sat.append(f"  - as_of: {v['rename_cifti_as_of']}")
            for s in v["not_sembolleri"]:
                sat.append(f"  - `{s['sembol']}` satırda: {_bayrak(s['satirda_var_mi'])} · "
                           f"as_of({v['tarih']}) üye: {_bayrak(s['as_of_tarih_uye_mi'])} · "
                           f"as_of(bugün) üye: {_bayrak(s['as_of_bugun_uye_mi'])}")
        sat.append("")
        sat.append(f"> PK-2 gerekçe taraması KAPI DEĞİLDİR (rapor): "
                   f"{pk2['yeniden_adlandirma_gerekceli_n']} satırın gerekçesinde yeniden "
                   f"adlandırma geçiyor. {pk2['gerekce_taramasi_notu']}")
        sat.append("")
    sat.append("---")
    sat.append(sonuc["beyan"])
    return "\n".join(sat) + "\n"


# ======================================================================================
# --cek (AĞ — bu ajan turunda ÇAĞRILMADI)
# ======================================================================================

def cek(oldid: int | None = None, hedef: pathlib.Path | None = None) -> dict:
    """Ham WİKİTEXT'i `action=raw` + `oldid` ile SABİTLEYEREK çeker. Wikimedia python-httpx'i
    robot politikasıyla 403'ler (hafıza `wikipedia-cekim-httpx-403`) — bu yüzden `urllib` ve açık
    bir User-Agent kullanılır. BU AJAN TURUNDA ÇAĞRILMADI (ağ yasak); Rol-1 için yazılıdır."""
    import urllib.request
    url = WIKI_RAW + (f"&oldid={oldid}" if oldid else "")
    istek = urllib.request.Request(url, headers={"User-Agent": "Meridian/1.0 (research; contact repo owner)"})
    with urllib.request.urlopen(istek, timeout=30) as cevap:      # noqa: S310 — sabit https adres
        govde = cevap.read().decode("utf-8")
    sha = hashlib.sha256(govde.encode("utf-8")).hexdigest()
    yol = pathlib.Path(hedef) if hedef else (SANDBOX / "ham" / f"sp400_oldid_{oldid or 'guncel'}.wiki")
    yol.parent.mkdir(parents=True, exist_ok=True)
    yol.write_text(govde, encoding="utf-8")
    return {"ok": True, "oldid": oldid, "sha256": sha, "yol": str(yol)}


# ======================================================================================
# CLI
# ======================================================================================

def _kimlik(yol: pathlib.Path, metin: str) -> dict:
    m = re.search(r"oldid[_-](\d+)", yol.name)
    return {"yol": str(yol), "oldid": int(m.group(1)) if m else None,
            "sha256": hashlib.sha256(metin.encode("utf-8")).hexdigest()}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="EDG-2026-092 — S&P MidCap 400 üyelik tarihçesi ücretsiz kaynak fizibilitesi "
                    "(ham wikitext girdili; ölçer, hüküm vermez)")
    ap.add_argument("--girdi", required=True, help="ham S&P 400 wikitext yolu (oldid ile dondurulmuş)")
    ap.add_argument("--beklenen-sha", default=None, help="girdinin beklenen sha256'sı — uyuşmazsa çıkış 2")
    ap.add_argument("--kart", default=str(KART_YOLU), help="EDG-2026-092 kart yolu (eşikler ORADAN)")
    ap.add_argument("--guncel-liste", default=None, help="PK-3: SPDR MDY holdings .xlsx")
    ap.add_argument("--bugun", default=None, help="ölçüm günü (ISO) — varsayılan bugün")
    ap.add_argument("--cikti-dizin", default=str(SANDBOX), help="sonuc_<damga>.json + rapor_<damga>.md dizini")
    ap.add_argument("--pk-sp500", default=None, help="PK-4: EDG-076'nın S&P 500 ham wikitext'i")
    ap.add_argument("--pk-kart", default=None, help="PK-4: EDG-2026-076 kart yolu")
    ap.add_argument("--cek", type=int, nargs="?", const=0, default=None,
                    help="AĞ: verilen oldid'i çeker (Rol-1; ölçüm ajanı ÇAĞIRMAZ)")
    a = ap.parse_args(argv)

    if a.cek is not None:
        print(json.dumps(cek(a.cek or None), ensure_ascii=False, indent=2))
        return 0

    girdi_yolu = pathlib.Path(a.girdi)
    if not girdi_yolu.exists():
        print(f"girdi yok: {girdi_yolu}", file=sys.stderr)
        return 1
    wikitext = girdi_yolu.read_text(encoding="utf-8")
    try:
        kart = kart_yukle(pathlib.Path(a.kart))
        esikleri_karttan_al(kart)
        pencere_baslangici_karttan(kart)
    except (OSError, ValueError) as e:  # sessiz-yutma: kart okunamıyor/eşik yoksa ÖLÇÜM YAPILAMAZ — sözleşme hatası olarak çıkış 2 ile ADIYLA bildirilir, varsayılan eşik UYDURULMAZ
        print(f"kart sözleşmesi okunamadı: {e}", file=sys.stderr)
        return 2

    guncel_uyeler = None
    mdy_meta = None
    if a.guncel_liste:
        guncel_uyeler, mdy_meta = mdy_tickerlari(pathlib.Path(a.guncel_liste))

    pk4 = None
    pk_kimligi = None
    if a.pk_sp500 and a.pk_kart:
        pk_yolu = pathlib.Path(a.pk_sp500)
        pk_metin = pk_yolu.read_text(encoding="utf-8")
        pk_kart = kart_yukle(pathlib.Path(a.pk_kart))
        pk4 = pk4_yol_tutarli(pk_metin, pk_kart,
                              pencere_baslangici=ORTAK.PENCERE_BASLANGIC,
                              bugun=a.bugun or dt.date.today().isoformat())
        pk_kimligi = _kimlik(pk_yolu, pk_metin)
        pk_kimligi["kart"] = pk_kart.get("card_id")
    elif a.pk_sp500 or a.pk_kart:
        print("--pk-sp500 ve --pk-kart BİRLİKTE verilmeli", file=sys.stderr)
        return 2

    sonuc = olc(wikitext, kart, _kimlik(girdi_yolu, wikitext), guncel_uyeler,
                bugun=a.bugun, beklenen_sha=a.beklenen_sha, pk4=pk4, mdy_meta=mdy_meta,
                pk_kimligi=pk_kimligi)

    cikti_dizin = pathlib.Path(a.cikti_dizin)
    cikti_dizin.mkdir(parents=True, exist_ok=True)
    d = sonuc["damga"]
    (cikti_dizin / f"sonuc_{d}.json").write_text(
        json.dumps(sonuc, ensure_ascii=False, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8")
    (cikti_dizin / f"rapor_{d}.md").write_text(rapor_markdown(sonuc), encoding="utf-8")
    print(f"yazıldı: {cikti_dizin / f'sonuc_{d}.json'}")
    print(f"yazıldı: {cikti_dizin / f'rapor_{d}.md'}")
    if sonuc["adim0"]["gecerli"] is False:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
