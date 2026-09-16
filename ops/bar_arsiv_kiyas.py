#!/usr/bin/env python3
# bar_arsiv_kiyas.py — EDG-2026-100 K1: bar arşivindeki (parquet) her parçayı, canlı motorun
# BUGÜN kullandığı CSV(sanitize) okuma yoluyla DEĞER-EŞDEĞERLİK açısından kıyaslar. SALT OKUR:
# state/ ve gözlem defterine tek bayt yazmaz; ürettiği tek şey rapor dizinindeki iki artefakttır.
# Koşum: .venv/bin/python ops/bar_arsiv_kiyas.py --kuru
"""ops/bar_arsiv_kiyas.py — BAR ARŞİVİ ↔ CANLI CSV OKUMA YOLU EŞDEĞERLİK ÖLÇÜMÜ (K1)
(kart: research/cards/EDG-2026-100-bar-arsivi-canli-okuma-esdegerlik.yaml; tasarım:
docs/TASARIM-BARS-PARQUET-DUCKDB-2026-09-06.md, üçüncü adım "canlı yol").

NEDEN VAR. Arşiv 2026-09-13'ten beri canlıdır ama canlı motor barları hâlâ CSV'den okur. Arşivin
canlı yola girebilmesinin ÖN ŞARTI, iki yakanın aynı çerçeveyi vermesidir — ve bu bir VARSAYIM
değil, her arşiv tazelemesinden sonra yeniden ölçülen bir SAYIDIR (kartın "ayrışma çivisi"
gerekçesi). Bu araç o sayıyı üretir. HÜKÜM VERMEZ: kartın eşiklerini okur, ölçülen değeri
eşiğin yanına yazar, tetiklenen kill-list kalemlerini listeler; "GEÇTİ/KALDI" cümlesini Rol-1
kurar.

KIYASIN İKİ YAKASI VE İKİSİNİN DE TEK KAYNAĞI.
  * ARŞİV YAKASI — parquet, DuckDB ile okunur. pyarrow bu venv'de YOKTUR (ölçüldü 2026-09-16:
    `import pyarrow` ModuleNotFoundError; arşiv yazıcısı da aynı sebeple DuckDB kullanır), yani
    okuma yolu yazma yoluyla aynı motordadır. Yol, yerleşim ve manifest anahtarı
    `bar_arsivle.hedef_yolu` ile TÜRETİLİR, burada yeniden yazılmaz.
  * CANLI YAKA — `pd.read_csv(..., parse_dates=["date"])` + `data.sanitize_bars`, yani
    `meridian/dataset.py`nin önbellekten yüklerken kullandığı desenin ta kendisi. Onarım kuralı
    KOPYALANMAZ, ÇAĞRILIR: kopyalansaydı `sanitize_bars` bir gün bir satırı başka türlü
    onardığında bu araç "eşit" derken canlı motor başka bir çerçeve görürdü — ölçümün ölçtüğü
    şeyin ta kendisi sessizce yalan olurdu.

BU ARAÇ OBS'A YAZMAZ — SINIRIYLA BİRLİKTE (ölçüldü 2026-09-16, ve bu bir BEYANDIR, temenni
değil). Aracın kendi metninde `obs` ithali YOKTUR ve gözlem defterine tek satır atmaz; kıyas
fonksiyonu tamamen saftır. SINIR ŞUDUR: canlı yakayı okumak `sanitize_bars` çağırmak demektir ve
o fonksiyon, hayalet-seans/karantina satırı DÜŞÜRDÜĞÜNDE kendi TEMBEL ithaliyle bir uyarı olayı
atar — olay `config.STATE` altındaki defterlere düşer. Yani bu araç yazmaz, ONARIM KAPISI yazar.
Kardeş `ops/bar_arsivle.py` aynı kapıdan geçer ve A1'de haftalık koşar, yani bu yeni bir yüzey
DEĞİLDİR. Defteri tamamen kapalı tutmak isteyen koşum, kökü ayırır ve veri dizinlerini AÇIKÇA
verir (`config.ROOT` bu değişkenden türer):
    MERIDIAN_ROOT=/tmp/edg100-kok python ops/bar_arsiv_kiyas.py --rapor \
        --kaynak-dizin state/bars --arsiv-dizin state/barlar --rapor-dizin <yol>

KAPSAMIN KAYNAĞI MANİFESTTİR, DİZİN TARAMASI DEĞİL. "Kaç parça vardı" sorusunun cevabı arşivin
kendi defterindedir. Manifest yoksa ya da beyan ettiği yerleşim tanınmıyorsa ÖLÇÜM DURUR
(çıkış 2) ve HİÇBİR artefakt yazılmaz: dizini tarayıp kapsamı çıkarsamak, bilinmeyen bir sayıyı
bilir gibi göstermek olurdu (uydurma yasağı). Bayat manifest ölçümü DURDURMAZ — sayı üretilir,
tazelik eşiği raporda DÜŞER ve hükmü Rol-1 verir.

KIYAS TEK FONKSİYONDADIR (`kiyasla`) VE SAFTIR: dosya açmaz, `meridian` ithal etmez, durum
tutmaz. Kartın kill-list kalemi "kıyas fonksiyonu obs/state'e yazıyor → ölçüm geçersiz" tam da
bunu korur. Dört eksen, dördü de ayrı ayrı raporlanır — satır sayısı · sütun kümesi VE SIRASI ·
dtype · hücre değeri. Float karşılaştırması BİT EŞİTLİĞİDİR: yakınlık ölçen bir kıyas (toleranslı
karşılaştırma) burada YASAKTIR, çünkü ölçülen şey "yakın mı" değil "aynı mı"dır; `-0.0` ile
`0.0` bu yüzden FARKLIDIR. Tek istisna NaN'dır: NaN ↔ NaN EŞİT sayılır (kartın kendi tanımı),
NaN ↔ sayı FARKLIDIR.

SATIR SAYILARI TUTMUYORSA DEĞER EKSENİ ÖLÇÜLMEZ ve bu raporda ADIYLA durur (`deger_olculdu`):
hizalanmamış iki çerçevede hücre kıyaslamak uydurma bir fark (ya da uydurma bir eşitlik)
üretirdi. "Ölçemedim" ile "fark yok" aynı piksele düşmez.

ÖLÇÜLEMEYEN PARÇA "FARKLI" DEĞİLDİR. CSV'si ya da parquet'i okunamayan parça kendi kovasında
sayılır, oranın PAYDASINA girmez ve nedeni raporda yazılıdır; kart bu kovaya ayrı bir eşik
koymuştur (kapsam eşiği).

OKUYUCUSU KİM (Yasa 6 — okuyucusuz yazım yok). İki artefakt, ikisinin de adı konmuş okuyucusu:
  * `sonuc_100_<damga>.json` → EDG-2026-100 kartının K defteri ve Rol-1'in K1 hükmü; sayılar
    oradan kartın `esikler` bloğuyla karşılaştırılır.
  * `fark_<damga>.jsonl` → aynı hükmün KÖK NEDEN tarafı: kart "fark kaynağı (sanitize/onarım/
    dtype) bulunmadan arşiv canlı yola giremez" der ve bu dosya o kaynağı parça parça gösterir.
Bu araç `ops/` altındadır; `meridian` kökünü tarayan statik artefakt grafı buraya BAKMAZ, yani
beyan (DECLARED_SINKS) gerekmez — okuyucu yine de burada ADIYLA yazılıdır.

BU DİLİM K1'DİR. Kartın K2'si (canlı gölge kıyası, 7 seans) ve `data.load_many` arşiv bayrağı
BU ARAÇTA YOKTUR: onlar canlı davranışa dokunur ve ayrı dilim + ayrı onaydır. Kartın K2
eşikleri raporda "ölçülmedi" kovasında ADIYLA durur — kapsamda olmayan bir eşik, geçmiş bir
eşik gibi okunmamalı.

KURU VARSAYILAN DEĞİLDİR (kardeş `ops/bar_arsivle.py`den bilinçli FARK). O araç ARŞİVE yazar ve
varsayılanı KURUdur; bu araç yalnız RAPOR dizinine yazar ve raporsuz bir ölçüm koşumu, ölçümü
hiç koşmamakla aynı kapıya çıkardı. `--kuru` ölçer ve BASAR, dosya yazmaz; `--rapor` açıkça
yazar. İkisi birlikte verilirse çıkış 2 — çelişen kip bayrağı sessizce bir tarafa düşmez.

KULLANIM:
    python ops/bar_arsiv_kiyas.py --kuru
    python ops/bar_arsiv_kiyas.py --rapor --sembol AAPL --sembol MSFT
    python ops/bar_arsiv_kiyas.py --kaynak-dizin /yol/bars --arsiv-dizin /yol/barlar

ÇIKIŞ KODU: 0 = ölçüm tamam · 2 = ÖLÇÜLEMEDİ (kullanım çelişkisi · kart okunamadı · manifest
           yok/bozuk · yerleşim tanınmıyor · kapsam boş) · 1 = araç hatası.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import sys

import duckdb
import numpy as np
import pandas as pd
import yaml

# ops/ altından doğrudan koşulduğunda `meridian` paketi ve kardeş `ops` modülleri bulunabilsin
# (kardeş betiklerin taşıdığı bootstrap satırının aynısı). Kök BU dosyadan türetilir: worktree'de
# koşan bir kopya ana checkout'un motorunu yüklemesin (ölçülmüş worktree tuzağı, 2026-09-13).
REPO = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from meridian import config as _config                       # noqa: E402
from meridian.adapters.data import sanitize_bars             # noqa: E402
from ops import bar_arsivle                                  # noqa: E402
from ops import olay_sorgu                                   # noqa: E402

#: Araç sürümü rapora yazılır: hangi sözleşmeyle ölçüldüğü sonuç dosyasından okunabilsin.
ARAC_ADI = "ops/bar_arsiv_kiyas.py"
ARAC_SURUMU = "2026-09-16.1"

#: EŞİKLERİN TEK KAYNAĞI KARTTIR — kodda donuk eşik sözlüğü YOKTUR (kardeş ölçüm betiği
#: `research/olcumler/edg094_r_yeniden/olc.py` ile aynı desen). Modül GLOBALİdİR ve fonksiyonlar
#: onu çağrı anında okur: çivi kartın bir KOPYASINI göstererek eşiğin gerçekten dosyadan geldiğini
#: ölçebilsin (donuk kopya sessizce ayrışırdı — tek-kaynak yasası).
KART_DIZINI = REPO / "research" / "cards"
VARSAYILAN_KART = "EDG-2026-100"

#: Rapor dizini varsayılanı. Depo köküne GÖRELİ türetilir ki worktree'de koşan bir kopya ana
#: checkout'un ölçüm dizinine yazmasın.
VARSAYILAN_RAPOR_DIZINI = REPO / "research" / "olcumler" / "edg100_bar_arsiv" / "olcum"

#: HÜKÜM BU ARAÇTA YAZILMAZ. Metin sonuç dosyasına aynen düşer ki "araç hüküm vermedi" ile
#: "alan unutuldu" ayırt edilebilsin.
HUKUM_YOK = "YOK — hüküm ROL-1'indir (kart EDG-2026-100, K1)"

#: FARK EKSENLERİ — sıra ANLAMLIDIR: kaba eksenden (satır) ince eksene (hücre) doğru okunur.
TUR_SATIR = "satir_sayisi"
TUR_SUTUN = "sutun"
TUR_DTYPE = "dtype"
TUR_DEGER = "deger"
TURLER = (TUR_SATIR, TUR_SUTUN, TUR_DTYPE, TUR_DEGER)

#: `fark_<damga>.jsonl`a PARÇA BAŞINA yazılan örnek satır tavanı (kartın ölçüm adımı: "ilk ≤5").
PARCA_FARK_TAVANI = 5
#: Kıyas fonksiyonunun topladığı DETAY satırı tavanı. SAYIM tavandan ETKİLENMEZ (tam sayılır);
#: kesilen yalnız örneklerdir ve kesilme `kesildi` alanıyla SÖYLENİR — bedel yasası: neyin
#: kaybedildiği de raporda durur.
KIYAS_DETAY_TAVANI = 50

#: KART EŞİKLERİNİN K1 AYAĞI: (kart alanı, yön, rapordaki ölçülen değerin adı).
K1_ESIK_HARITASI = (
    ("esitlik_orani_alt", ">=", "esitlik_orani"),
    ("olculemeyen_ust_oran", "<=", "olculemeyen_oran"),
    ("manifest_tazelik_gun_ust", "<=", "manifest_yas_gun"),
)
#: Kartın K2 (canlı gölge kıyası) eşikleri — bu araçta ÖLÇÜLMEZ, ama ADIYLA raporlanır.
K2_ESIKLERI = {
    "golge_kiyas_seans": "K2 — canlı gölge kıyası (7 seans) bu koşumun kapsamı DIŞINDA",
    "golge_fark_ust": "K2 — canlı gölge kıyası fark defteri bu koşumun kapsamı DIŞINDA",
}

#: `float` bit kalıbını okumak için kullanılan tamsayı görünümleri (itemsize → tip).
_BIT_GORUNUMU = {2: np.uint16, 4: np.uint32, 8: np.uint64}


# ---------------------------------------------------------------------------------------------
# Kıyas — SAF (dosya yok, meridian yok, durum yok)
# ---------------------------------------------------------------------------------------------

def _bos_mu(v) -> bool:
    """Tek bir hücre "yok" mu (NaN · None · NaT · pandas NA)? Dizi/çerçeve gelirse `pandas`
    dizi döndürür ve `bool()` patlar — hücre kıyası dışında çağrılmaz, ama sınır yazılı olsun."""
    try:
        return bool(pd.isna(v))
    except (TypeError, ValueError):  # sessiz-yutma: skaler olmayan (dizi/liste) hücre için "yok" hükmü kurulamaz; DOLU sayılır ve ayrım değer ekseninde ölçülür, sinyal kaybolmaz
        return False


def _elemanca_esit(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Eleman başına `==` — KIYAS KURULAMAZSA hepsi FARKLI sayılır (sessiz "eşit" değil).

    Yön bilinçlidir: kıyası kuramamak bir bilgisizliktir ve bu araçta bilgisizliğin güvenli
    tarafı "fark var" demektir — ters yön, ölçülmemiş bir eşitliği rapora eşitlik diye yazardı."""
    try:
        r = a == b
    except (TypeError, ValueError):  # sessiz-yutma: kıyaslanamayan tip çifti (ör. dizge ↔ tarih) EŞİT SAYILMAZ; fark olarak raporlanır ve hücre değerleri fark satırında GÖRÜNÜR
        return np.zeros(len(a), dtype=bool)
    if np.isscalar(r) or getattr(r, "shape", None) != a.shape:
        return np.zeros(len(a), dtype=bool)
    return np.asarray(r, dtype=bool)


def _farkli_maske(sa: pd.Series, sb: pd.Series) -> np.ndarray:
    """Bir sütunun hücre bazında FARKLI olduğu konumlar (konumsal; indeks dikkate ALINMAZ).

    Aynı float dtype'ta kıyas BİT kalıbı üzerinden yapılır — kartın "float bit-eşit" tanımı
    budur ve `==` bunu vermez (`-0.0 == 0.0` TRUE'dur). NaN bit kalıbı taşıyıcıdan taşıyıcıya
    değişebildiği için "yok" hücreleri bit kıyasının ÜSTÜNE yazılır: iki yaka da boşsa EŞİT,
    biri boşsa FARKLI."""
    a = np.ascontiguousarray(sa.to_numpy())
    b = np.ascontiguousarray(sb.to_numpy())
    bos_a = np.asarray(pd.isna(sa), dtype=bool)
    bos_b = np.asarray(pd.isna(sb), dtype=bool)
    if a.dtype == b.dtype and a.dtype.kind == "f" and a.dtype.itemsize in _BIT_GORUNUMU:
        gorunum = _BIT_GORUNUMU[a.dtype.itemsize]
        ayni = a.view(gorunum) == b.view(gorunum)
    else:
        ayni = _elemanca_esit(a, b)
    return ~np.where(bos_a | bos_b, bos_a & bos_b, ayni)


def _gosterim(v):
    """Bir hücreyi JSON'a yazılabilir hâle getirir. NaN ve NaT metne çevrilir: `None` yazmak
    "boş" ile "sayı değil" ayrımını silerdi ve fark satırı okunamaz olurdu."""
    if v is None:
        return None
    if isinstance(v, float):
        return "NaN" if v != v else float(v)
    if isinstance(v, np.integer):
        return int(v)
    if isinstance(v, np.bool_):
        return bool(v)
    if _bos_mu(v):
        return f"BOS<{type(v).__name__}>"
    if isinstance(v, (pd.Timestamp, dt.datetime, dt.date)):
        return str(v)
    try:
        json.dumps(v)
        return v
    except TypeError:  # sessiz-yutma: JSON'a çevrilemeyen tip kaybedilmez, `repr` ile METİN olarak rapora girer; kaybolan yalnız makine-okunurluktur ve bu fark satırı insan içindir
        return repr(v)


def kiyasla(df_a: pd.DataFrame, df_b: pd.DataFrame, *,
            tavan: int = KIYAS_DETAY_TAVANI) -> dict:
    """ARŞİV (`df_a`) ↔ CANLI CSV (`df_b`) çerçevelerinin DÖRT EKSENDE kıyası. SAF fonksiyon.

    Döner: `esit` (dört eksen de tutuyor mu) · `farklar` (detay satırları, `tavan`a kadar) ·
    `sayim` (eksen başına TAM sayı; değer ekseninde farklı HÜCRE sayısı) · `deger_olculdu`
    (satır sayıları tutmadığında değer ekseni ölçülmez) · `kesildi` (detay kesildi mi).

    Eksen sırası kabadan inceye: satır sayısı → sütun kümesi/sırası → dtype → hücre."""
    farklar: list[dict] = []
    sayim = {t: 0 for t in TURLER}

    def _ekle(kayit: dict) -> None:
        if len(farklar) < max(int(tavan), 0):
            farklar.append(kayit)

    na, nb = len(df_a), len(df_b)
    if na != nb:
        sayim[TUR_SATIR] = 1
        _ekle({"tur": TUR_SATIR, "arsiv": na, "csv": nb})

    sut_a, sut_b = list(df_a.columns), list(df_b.columns)
    if sut_a != sut_b:
        ortak_a = [c for c in sut_a if c in set(sut_b)]
        ortak_b = [c for c in sut_b if c in set(sut_a)]
        sayim[TUR_SUTUN] = 1
        _ekle({"tur": TUR_SUTUN, "arsiv": sut_a, "csv": sut_b,
               "yalniz_arsiv": [c for c in sut_a if c not in set(sut_b)],
               "yalniz_csv": [c for c in sut_b if c not in set(sut_a)],
               "sira_farkli": ortak_a != ortak_b})

    ortak = [c for c in sut_a if c in set(sut_b)]
    for sutun in ortak:
        ta, tb = str(df_a[sutun].dtype), str(df_b[sutun].dtype)
        if ta != tb:
            sayim[TUR_DTYPE] += 1
            _ekle({"tur": TUR_DTYPE, "sutun": sutun, "arsiv": ta, "csv": tb})

    deger_olculdu = na == nb
    if deger_olculdu:
        for sutun in ortak:
            maske = _farkli_maske(df_a[sutun], df_b[sutun])
            n = int(maske.sum())
            if not n:
                continue
            sayim[TUR_DEGER] += n
            for i in np.flatnonzero(maske):
                _ekle({"tur": TUR_DEGER, "sutun": sutun, "satir": int(i),
                       "arsiv": _gosterim(df_a[sutun].iat[int(i)]),
                       "csv": _gosterim(df_b[sutun].iat[int(i)])})

    return {"esit": not any(sayim.values()),
            "farklar": farklar,
            "sayim": sayim,
            "deger_olculdu": deger_olculdu,
            "kesildi": sum(sayim.values()) > len(farklar),
            "satir": {"arsiv": na, "csv": nb}}


# ---------------------------------------------------------------------------------------------
# Kart (eşiklerin tek kaynağı)
# ---------------------------------------------------------------------------------------------

def kart_yolu(kart_no: str) -> pathlib.Path | None:
    """Kart dosyası — `KART_DIZINI` çağrı anında okunur (gerekçe o sabitin şerhinde). Birden
    çok aday varsa hüküm KURULMAZ: hangi kartın eşiğiyle ölçüldüğü belirsiz bir rapor, eşiksiz
    bir rapordan daha kötüdür (yanlış kesinlik)."""
    adaylar = sorted(pathlib.Path(KART_DIZINI).glob(f"{kart_no}-*.yaml"))
    return adaylar[0] if len(adaylar) == 1 else None


def kart_esikleri(kart_no: str) -> tuple[dict | None, str | None]:
    """(eşikler, gerekçe). Eşikler okunamazsa `(None, neden)` — ölçüm o zaman DURUR."""
    yol = kart_yolu(kart_no)
    if yol is None:
        return None, (f"kart bulunamadı ya da ikircikli: {kart_no} ({KART_DIZINI}) — eşikler "
                      "KODDA YOKTUR ve uydurulmaz")
    try:
        govde = yaml.safe_load(yol.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError) as e:  # sessiz-yutma: kart okunamıyorsa eşik bilinmiyor demektir ve eşiksiz sayı basmak hükmü uydurmaya davettir; neden ÇAĞIRANA döner ve stderr'e basılır
        return None, f"kart okunamadı ({yol}): {type(e).__name__}: {e}"
    esikler = govde.get("esikler")
    if not isinstance(esikler, dict) or not esikler:
        return None, f"kartta `esikler` bloğu yok ya da boş: {yol}"
    return esikler, None


def esik_hukmu(deger, esik, yon: str) -> bool | None:
    """Tek eşik karşılaştırması. Ölçülemeyen değer `None` döner — `False` döndürmek "ölçtük,
    kaldı" demek olurdu (uydurma yasağı)."""
    if deger is None or esik is None:
        return None
    return deger >= esik if yon == ">=" else deger <= esik


# ---------------------------------------------------------------------------------------------
# Çerçeve okuma — iki yaka
# ---------------------------------------------------------------------------------------------

def arsiv_cercevesi(con: duckdb.DuckDBPyConnection, yol: pathlib.Path) -> pd.DataFrame:
    """Parquet parçası → pandas çerçevesi. Sütun SIRASI dosyadan gelir (`SELECT *`): sıra da
    şemanın parçasıdır ve burada yeniden sıralamak, ölçülecek farkı ölçümün kendisi silerdi."""
    return con.execute(
        f"SELECT * FROM read_parquet({olay_sorgu.sql_metni(yol)})").df()


def canli_cerceve(yol: pathlib.Path, sembol: str) -> pd.DataFrame:
    """CSV → canlı motorun bugün gördüğü çerçeve. Desen `meridian/dataset.py`nin önbellek
    okuma yolundan gelir; onarım kuralı ithal edilir, kopyalanmaz (gerekçe modül başlığında)."""
    ham = pd.read_csv(yol, parse_dates=["date"])
    temiz, _rapor = sanitize_bars(ham, sembol)
    return temiz.reset_index(drop=True)


def parca_dilimi(temiz: pd.DataFrame, bolum: str, parca: str | None) -> pd.DataFrame:
    """Canlı çerçevenin BU PARÇAYA düşen dilimi. Bölüm anahtarı `bar_arsivle.parca_seri` ile
    türetilir — yazıcı hangi satırı hangi dosyaya koyduysa kıyas da aynı kuralla böler."""
    if bolum == bar_arsivle.BOLUM_SEMBOL:
        return temiz
    anahtar = bar_arsivle.parca_seri(temiz, bolum)
    return temiz.loc[anahtar == parca].reset_index(drop=True)


# ---------------------------------------------------------------------------------------------
# Kapsam — manifestten
# ---------------------------------------------------------------------------------------------

def parcalar(manifest: dict, bolum: str, semboller: list[str] | None) -> list[tuple[str, str | None]]:
    """(sembol, parça) çiftleri — KAPSAMIN KAYNAĞI manifesttir, dizin taraması değil."""
    suzgec = {s.upper() for s in semboller} if semboller else None
    out: list[tuple[str, str | None]] = []
    for sembol, govde in sorted((manifest.get("semboller") or {}).items()):
        if suzgec is not None and sembol.upper() not in suzgec:
            continue
        if bolum == bar_arsivle.BOLUM_SEMBOL:
            out.append((sembol, None))
        else:
            out.extend((sembol, p) for p in sorted(govde or {}))
    return out


def manifest_yas_gun(manifest: dict, simdi: dt.datetime | None = None) -> float | None:
    """Manifest üretim damgasının yaşı (gün). Damga yoksa/ayrıştırılamazsa `None` — "0 gün"
    yazmak, bilinmeyen bir tazeliği taze göstermek olurdu."""
    damga = ((manifest.get("uretim") or {}).get("utc") or "").strip()
    if not damga:
        return None
    try:
        an = dt.datetime.fromisoformat(damga)
    except ValueError:  # sessiz-yutma: ayrıştırılamayan damga hakkında tazelik hükmü kurulamaz; None döner ve eşik `gecti: null` olur (ölçülemeyen ile "geçti" ayrı kalır)
        return None
    if an.tzinfo is None:
        an = an.replace(tzinfo=dt.timezone.utc)
    return ((simdi or dt.datetime.now(dt.timezone.utc)) - an).total_seconds() / 86400.0


# ---------------------------------------------------------------------------------------------
# Ölçüm
# ---------------------------------------------------------------------------------------------

def olc(kaynak: pathlib.Path, arsiv: pathlib.Path, manifest: dict, bolum: str,
        semboller: list[str] | None) -> dict:
    """Bütün parçaları kıyaslar; (sayım, oranlar, fark satırları, ölçülemeyenler) döner.
    HİÇBİR DOSYA YAZMAZ — yazım çağıranın (raporla) işidir."""
    kume = parcalar(manifest, bolum, semboller)
    sayim = {"esit": 0, "farkli": 0, "olculemeyen": 0}
    tur_sayilari = {t: 0 for t in TURLER}
    fark_satirlari: list[dict] = []
    olculemeyenler: list[dict] = []
    hucre_farki = 0
    deger_ekseni_olculmeyen = 0

    con = duckdb.connect()
    try:
        for sembol, parca in kume:
            p_yol = bar_arsivle.hedef_yolu(arsiv, bolum, sembol, parca)
            c_yol = kaynak / bar_arsivle.sembol_dosya_adi(sembol)
            neden = None
            if not p_yol.is_file():
                neden = "parquet yok"
            elif not c_yol.is_file():
                neden = "CSV yok"
            if neden is None:
                try:
                    df_a = arsiv_cercevesi(con, p_yol)
                    df_b = parca_dilimi(canli_cerceve(c_yol, sembol), bolum, parca)
                except (duckdb.Error, OSError, ValueError, KeyError) as e:  # sessiz-yutma: okunamayan tek parça bütün ölçümü düşürmez; parça ÖLÇÜLEMEYEN kovasına NEDENİYLE yazılır ve kartın kapsam eşiği onu görür
                    neden = f"{type(e).__name__}: {e}"
            if neden is not None:
                sayim["olculemeyen"] += 1
                olculemeyenler.append({"sembol": sembol, "parca": parca, "neden": neden})
                continue

            rapor = kiyasla(df_a, df_b)
            if rapor["esit"]:
                sayim["esit"] += 1
                continue
            sayim["farkli"] += 1
            hucre_farki += rapor["sayim"][TUR_DEGER]
            if not rapor["deger_olculdu"]:
                deger_ekseni_olculmeyen += 1
            for t in TURLER:
                if rapor["sayim"][t]:
                    tur_sayilari[t] += 1
            for kayit in rapor["farklar"][:PARCA_FARK_TAVANI]:
                fark_satirlari.append({"sembol": sembol, "parca": parca, **kayit})
            if rapor["kesildi"] or len(rapor["farklar"]) > PARCA_FARK_TAVANI:
                fark_satirlari.append({"sembol": sembol, "parca": parca, "tur": None,
                                       "kesildi": True, "sayim": rapor["sayim"],
                                       "not": "örnek satırlar kesildi; SAYIM tamdır"})
    finally:
        con.close()

    olculen = sayim["esit"] + sayim["farkli"]
    toplam = olculen + sayim["olculemeyen"]
    return {
        "kume": kume,
        "sayim": sayim,
        "tur_sayilari": tur_sayilari,
        "deger_hucre_farki": hucre_farki,
        "deger_ekseni_olculmeyen_parca": deger_ekseni_olculmeyen,
        "fark_satirlari": fark_satirlari,
        "olculemeyenler": olculemeyenler,
        "esitlik_orani": (sayim["esit"] / olculen) if olculen else None,
        "olculemeyen_oran": (sayim["olculemeyen"] / toplam) if toplam else None,
        "olculen": olculen,
        "toplam": toplam,
    }


def esik_raporu(esikler: dict, olcum: dict, yas_gun: float | None) -> tuple[dict, dict, list[str]]:
    """(K1 eşik tablosu, K2 ölçülmeyenler, tetiklenen kill-list kalemleri). Kill-list metni
    KARTTAN gelir — burada yeniden yazılmaz, yalnız TETİKLENEN eşiğin adı taşınır."""
    olculen_degerler = {"esitlik_orani": olcum["esitlik_orani"],
                        "olculemeyen_oran": olcum["olculemeyen_oran"],
                        "manifest_yas_gun": yas_gun}
    tablo: dict[str, dict] = {}
    tetik: list[str] = []
    for ad, yon, deger_adi in K1_ESIK_HARITASI:
        esik = esikler.get(ad)
        deger = olculen_degerler[deger_adi]
        gecti = esik_hukmu(deger, esik, yon)
        tablo[ad] = {"deger": deger, "esik": esik, "yon": yon,
                     "n": olcum["olculen"] if deger_adi == "esitlik_orani" else olcum["toplam"],
                     "gecti": gecti}
        if gecti is False:
            tetik.append(ad)
    k2 = {ad: {"esik": esikler.get(ad), "neden": neden} for ad, neden in K2_ESIKLERI.items()}
    return tablo, k2, tetik


# ---------------------------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------------------------

def _ayristirici() -> argparse.ArgumentParser:
    a = argparse.ArgumentParser(
        prog=ARAC_ADI,
        description="Bar arşivindeki parquet parçalarını canlı CSV(sanitize) okuma yoluyla "
                    "kıyaslar (EDG-2026-100 K1). Salt okur; hüküm basmaz, sayı basar.",
        epilog="Eşikler research/cards/EDG-2026-100-*.yaml dosyasından okunur.",
    )
    a.add_argument("--kaynak-dizin", type=pathlib.Path, default=None, dest="kaynak_dizin",
                   help="CSV önbellek dizini (varsayılan: config.BARS = state/bars)")
    a.add_argument("--arsiv-dizin", type=pathlib.Path, default=None, dest="arsiv_dizin",
                   help="parquet arşiv dizini (varsayılan: config.STATE/barlar)")
    a.add_argument("--sembol", action="append", default=None,
                   help="yalnız bu sembol(ler) — birden çok kez verilebilir")
    a.add_argument("--rapor-dizin", type=pathlib.Path, default=None, dest="rapor_dizin",
                   help=f"rapor dizini (varsayılan: {VARSAYILAN_RAPOR_DIZINI})")
    a.add_argument("--kart", default=VARSAYILAN_KART, help="eşiklerin okunacağı kart numarası")
    a.add_argument("--kuru", action="store_true",
                   help="ölç ve BAS, dosya YAZMA")
    a.add_argument("--rapor", action="store_true",
                   help="rapor dosyalarını YAZ (varsayılan kip)")
    return a


def _damga(simdi: dt.datetime | None = None) -> str:
    return (simdi or dt.datetime.now(dt.timezone.utc)).strftime("%Y%m%dT%H%M%SZ")


def main(argv: list[str] | None = None) -> int:
    args = _ayristirici().parse_args(argv)

    if args.kuru and args.rapor:
        print("HATA: `--kuru` ve `--rapor` birlikte verilemez — çelişen kip bayrağı sessizce "
              "bir tarafa düşmez. Birini seç.", file=sys.stderr)
        return 2
    yazilacak = not args.kuru

    esikler, kart_nedeni = kart_esikleri(args.kart)
    if esikler is None:
        print(f"ÖLÇÜLEMEDİ: {kart_nedeni}", file=sys.stderr)
        return 2

    kaynak = args.kaynak_dizin or pathlib.Path(_config.BARS)
    arsiv = args.arsiv_dizin or (pathlib.Path(_config.STATE)
                                 / bar_arsivle.VARSAYILAN_HEDEF_ALT)
    rapor_dizin = args.rapor_dizin or VARSAYILAN_RAPOR_DIZINI

    if not kaynak.is_dir():
        print(f"ÖLÇÜLEMEDİ: CSV kaynak dizini yok: {kaynak}", file=sys.stderr)
        return 2
    if not arsiv.is_dir():
        print(f"ÖLÇÜLEMEDİ: arşiv dizini yok: {arsiv} — önce `ops/bar_arsivle.py --uygula`.",
              file=sys.stderr)
        return 2

    manifest_yolu = bar_arsivle.manifest_yolu(arsiv)
    if not manifest_yolu.is_file():
        print(f"ÖLÇÜLEMEDİ: manifest yok ({manifest_yolu}). Kapsam arşivin KENDİ defterinden "
              "okunur; dizin tarayıp kapsam çıkarsamak uydurma olurdu.", file=sys.stderr)
        return 2
    try:
        manifest = bar_arsivle.manifest_oku(arsiv)
    except RuntimeError as e:
        print(f"ÖLÇÜLEMEDİ: {e}", file=sys.stderr)
        return 2

    beyan = manifest.get("bolum")
    bolum = bar_arsivle.manifest_bolumu(manifest)
    if bolum not in bar_arsivle.BOLUMLER:
        print(f"ÖLÇÜLEMEDİ: manifest tanınmayan bir yerleşim beyan ediyor: {bolum!r} "
              f"(bilinen: {', '.join(bar_arsivle.BOLUMLER)}). Yerleşim bilinmeden parça yolu "
              "türetilemez.", file=sys.stderr)
        return 2

    olcum = olc(kaynak, arsiv, manifest, bolum, args.sembol)
    if olcum["toplam"] == 0:
        print("ÖLÇÜLEMEDİ: kapsam BOŞ — manifestte (süzgeçten sonra) hiç parça yok.",
              file=sys.stderr)
        return 2

    yas = manifest_yas_gun(manifest)
    tablo, k2, tetik = esik_raporu(esikler, olcum, yas)
    uretim = manifest.get("uretim") or {}
    damga = _damga()
    fark_adi = f"fark_{damga}.jsonl"

    sonuc = {
        "kart": args.kart,
        "kosum": {"utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                  "arac": ARAC_ADI, "surum": ARAC_SURUMU, "kip": "rapor" if yazilacak else "kuru"},
        "kapsam": {"kaynak_dizin": str(kaynak), "arsiv_dizin": str(arsiv),
                   "sembol_suzgeci": list(args.sembol) if args.sembol else None,
                   "manifest_sembol": len(manifest.get("semboller") or {}),
                   "parca": olcum["toplam"], "olculen": olcum["olculen"]},
        "arsiv": {"manifest_sha256": bar_arsivle.sha256_dosya(manifest_yolu),
                  "damga_utc": uretim.get("utc"), "yazan_arac": uretim.get("arac"),
                  "yazan_surum": uretim.get("surum"), "bolum": bolum,
                  "bolum_beyani": "manifest" if beyan else "varsayılan (alan yok)",
                  "manifest_yas_gun": yas},
        "sayim": olcum["sayim"],
        "oran": {"esitlik_orani": olcum["esitlik_orani"],
                 "olculemeyen_oran": olcum["olculemeyen_oran"]},
        "tur_sayilari": olcum["tur_sayilari"],
        "deger_hucre_farki": olcum["deger_hucre_farki"],
        "deger_ekseni_olculmeyen_parca": olcum["deger_ekseni_olculmeyen_parca"],
        "olculemeyen_nedenleri": _neden_sayimi(olcum["olculemeyenler"]),
        "olculemeyen_ornekleri": olcum["olculemeyenler"][:20],
        "esikler": tablo,
        "k2_olculmedi": k2,
        "kill_list_tetik": tetik,
        "hukum": HUKUM_YOK,
        "fark_dosyasi": fark_adi,
    }

    if yazilacak:
        rapor_dizin.mkdir(parents=True, exist_ok=True)
        (rapor_dizin / fark_adi).write_text(
            "".join(json.dumps(s, ensure_ascii=False) + "\n" for s in olcum["fark_satirlari"]),
            encoding="utf-8")
        (rapor_dizin / f"sonuc_100_{damga}.json").write_text(
            json.dumps(sonuc, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8")

    print(json.dumps(sonuc, ensure_ascii=False, indent=2, sort_keys=True))
    if not yazilacak:
        print(f"KURU: hiçbir dosya yazılmadı ({len(olcum['fark_satirlari'])} fark satırı "
              "basılmadı) — yazmak için `--rapor`.", file=sys.stderr)
    return 0


def _neden_sayimi(olculemeyenler: list[dict]) -> dict:
    """Ölçülemeyen parçaların nedenlerinin sayımı — "kaç tanesini ölçemedim" sorusunun yanına
    "NİYE" cevabı. Sayı tek başına kapsamı anlatmaz."""
    out: dict[str, int] = {}
    for k in olculemeyenler:
        out[k["neden"]] = out.get(k["neden"], 0) + 1
    return dict(sorted(out.items()))


if __name__ == "__main__":
    sys.exit(main())
