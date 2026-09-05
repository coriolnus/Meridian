"""research/olcumler/edg079_replay_pit_denetimi/olcum.py — EDG-2026-079 ÖLÇÜM aracı
(TSK-156 dilim-2 (a), TSK-066 girdisi, 2026-09-05).

NE ÖLÇER. Kart `research/cards/EDG-2026-079-replay-defteri-pit-uyelik-denetimi.yaml`nin hipotezi:
tohum/replay defterindeki (`state/meridian.db` trades, 901 satır — 885 `replay_seed` + 16
`live_paper`) işlemlerin küçük bir payı işlem AÇILIŞ tarihinde S&P 500 üyesi OLMAYAN sembollerde
gerçekleşti mi (survivorship sızıntısı, K1) ve `REPLAY_UNIVERSE`ün (248) küçük bir payı
2022-01-01'de üye DEĞİL miydi (geç katılan, K2). Paylar kartın eşiklerini aşarsa replay hükümleri
survivorship şerhi ister ve TSK-066 evren yeniden kurulumu `as_of(t)`yi ZORUNLU tüketici yapar.

ROL: ÖLÇÜM ajanı. AĞA ÇIKMAZ (yalnız verilen dosyalar okunur), karta DOKUNMAZ, `meridian/*.py`ye
DOKUNMAZ, canlı state'e YAZMAZ. Eşikler (`esikler.k1_gecti`/`k2_gecti`) kartın `esikler:`
alanından ÇALIŞMA ANINDA okunur (`esikleri_karttan_oku`, edg071/edg075 emsali) — eşik METNİ
serbest-düzyazı olduğu için `esik_bandlarini_ayristir` onu bant listesine çevirir; SAYI KODA
KOPYALANMAZ (0,02/0,10 gibi literaller bu dosyada YAZILI DEĞİLDİR, yalnız kartta).

GİRDİLER (--olc bunları OKUR, yazmaz):
  --trades <json>        state/meridian.db trades salt-okunur dökümü (`{"rows": [...]}` ya da
                         doğrudan liste — ikisi de kabul edilir).
  --guncel-liste <json>  güncel S&P 500 üyelik listesi (liste[str]).
  --girdi-html <html>    "Historical components of the S&P 500" değişiklik tablosunun ham HTML'i
                         (Rol-1 dışarıdan verir — `research/olcumler/edg075_sp500_tarihsel/ham/`
                         .gitignore'lu, bu ajan turunda worktree'de YOK).
  --kart <yaml>          varsayılan EDG-2026-079 kartı.
  --t-evren <ISO>        K2 `as_of` tarihi (kart örneği: 2022-01-01).

ADIM-0 FİZİBİLİTE (`adim0`): üç girdinin sha256'sı DONUK kayıtla eşit mi — `trades`/`guncel-liste`
kendi dizinlerindeki `SHA256.txt`ye (coreutils `sha256sum` biçimi) karşı, HTML kartın
`girdi_kimligi.degisiklik_tablosu` DÜZYAZISINDAKİ 64-hex'e karşı (`kart_html_sha_oku`). Üçü de
eşleşmezse `gecerli=False` ve K1/K2/pozitif_kontrol bu turda KOŞMAZ — `sonuc.json` YİNE üretilir
(Yasa 6), ilgili alanlar `None` + `adim_0.neden` (UYDURMA YOK: 'koşulmadı' ile 'koştu, geçti'
KARIŞMAZ, edg075/076 `adim0` emsali).

TABLO AYRIŞTIRMA + `as_of`: KOPYALANMADI. `research/olcumler/edg075_sp500_tarihsel/olcum.py`
modülü `sys.path` ile İÇE AKTARILIR (`_edg075_yukle`) ve `tabloyu_ayristir`/`as_of` ORADAN
kullanılır — iki kopya sessizce ayrışmasın (tek-kaynak yasası). Modül adı ("olcum") bu depoda
JENERİKTİR (onlarca ölçüm dizini aynı dosya adını taşır); yükleyici `sys.modules`teki olası
YANLIŞ önbelleği kendi dosya yoluyla doğrular.

NORMALİZASYON + RENAME (kart `girdi_kimligi.rename_defteri`): ticker `.`→`-` + upper
(`_normalize_ticker`). `meridian.adapters.constituents.SEMBOL_YENIDEN_ADLANDIRMA` (tuple of
{eski, yeni, tarih}) — TEK KAYNAK SINIRI (o modülün kendi başlığı): "Historical components" tablosu
ÜYELİK olaylarını taşır, şirket S&P 500'de KALIRKEN sembol değiştirmesini (EQR→VMRK 2026-08-18)
satır olarak TAŞIMAZ. Bu yüzden `guncel_uyeler` bugünkü adla (VMRK) kurulur ve tabloda BU olay için
satır YOKTUR — `as_of(t)` t < 2026-08-18 için hâlâ VMRK'yi üye SAYAR, EQR'yi HİÇ döndürmez. Kaynak
sınırının düzeltmesi `islem_uye_mi`dedir: `uye_mi = (ticker ∈ as_of(t)) or (rename ile yeni ad ∈
as_of(t) and t < rename tarihi)` — yani ticker="EQR", t="2026-06-01" için doğrudan üyelik YANLIŞ
(False) çıkar ama rename dalı "VMRK" ∈ as_of(t)'yi bulur ve t rename tarihinden ÖNCE olduğu için
üye SAYILIR. AÇIK KALEM: brief bu defteri `meridian.adapters.data.SEMBOL_YENIDEN_ADLANDIRMA` diye
andı; gerçek konum ÖLÇÜLDÜ — `meridian/adapters/constituents.py` (grep: `data.py`da bu ad HİÇ
geçmiyor). `REPLAY_UNIVERSE` (K2) brief'in dediği gibi GERÇEKTEN `meridian.adapters.data`da —
yalnız rename defterinin modül adı brief'te yanlış yazılmış, betik GERÇEK konumdan okur (Rol-1'e
rapor edilir, karta DOKUNULMADI).

K1 (`k1_hesapla`): her işlem için `uye_mi` (yukarıdaki formül). Tohum (`kaynak == "replay_seed"`)
ve canlı (GERİ KALAN HER kaynak, kartta "16 live_paper") AYRI raporlanır — hüküm YALNIZ tohum
üstünden (kart `kill_list`), canlı BİLGİ. Ölçülemeyen (ticker boş / `ts_open` ayrışmıyor)
`olculemedi_n`de sayılır, PAYA GİRMEZ. `as_of_onbellek` ÇAĞIRAN tarafından tutulan bir sözlüktür —
901 işlem × `as_of` yerine tarih başına BİR KEZ kurulur (kart `olcum_plani` performans notu).

K2 (`k2_hesapla`): verilen evren (varsayılan `meridian.adapters.data.REPLAY_UNIVERSE`; test kendi
sentetiğini VERİR — kart notu) için `as_of(t_evren)`de üye OLMAYANLARIN payı `q`. `ikinci_kesit`
(kart: 2024-01-01) K DEĞİL, bilgi amaçlı ikinci kesit.

POZİTİF KONTROL (`pozitif_kontrol`, YOL-TUTARLI — kart `pozitif_kontrol`): üç sentetik işlem AYNI
`islem_uye_mi` fonksiyonuyla — (a) FERG 2026-07-01 → sızıntı (gerçek giriş 2026-08-05'ten ÖNCE),
(b) FERG 2026-08-10 → üye (giriş SONRASI), (c) EQR 2026-06-01 → üye (rename eşlemesi). `tuttu`
üçü de beklenen gibiyse.

DİSİPLİN: UYDURMA YASAĞI (ölçülemeyen `None` + neden — ticker/ts_open ayrışamadığında, eşik bandı
kartta yoksa ValueError, sha kaydı yoksa `gecerli=False`). YASA 4 (sessiz-yutma işaretli +
gerekçe). YASA 6 (okuyucu: `sonuc.json` → Rol-1 karta + K defterine işler; kart/ROADMAP/günlük bu
betik tarafından YAZILMAZ — CLAUDE.md §3/§5, ajan karta dokunmaz)."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import importlib
import json
import pathlib
import re
import statistics
import sys

import yaml

from meridian.adapters.data import REPLAY_UNIVERSE
from meridian.adapters.constituents import SEMBOL_YENIDEN_ADLANDIRMA

KOK = pathlib.Path(__file__).resolve().parents[3]
SANDBOX = pathlib.Path(__file__).resolve().parent
KART_YOLU = KOK / "research" / "cards" / "EDG-2026-079-replay-defteri-pit-uyelik-denetimi.yaml"
EDG075_DIR = KOK / "research" / "olcumler" / "edg075_sp500_tarihsel"
IKINCI_KESIT_TARIHI = "2024-01-01"          # kart `olcum_plani` — K DEĞİL, bilgi amaçlı ikinci kesit

# kart `pozitif_kontrol`: üç sentetik vaka, birebir
_PK_VAKALAR: tuple[dict, ...] = (
    {"ad": "FERG_giris_oncesi_sizinti", "ticker": "FERG", "ts_open": "2026-07-01", "beklenen": False},
    {"ad": "FERG_giris_sonrasi_uye", "ticker": "FERG", "ts_open": "2026-08-10", "beklenen": True},
    {"ad": "EQR_rename_ile_uye", "ticker": "EQR", "ts_open": "2026-06-01", "beklenen": True},
)


# ======================================================================================
# edg075 olcum.py'yi sys.path ile İÇE AKTAR — KOPYALAMA DEĞİL (tek-kaynak yasası)
# ======================================================================================

def _edg075_yukle():
    """`research/olcumler/edg075_sp500_tarihsel/olcum.py`yi `sys.path` ile içe aktarır. Modül adı
    ("olcum") bu depoda JENERİKTİR — onlarca ölçüm dizini aynı dosya adını taşır — bu yüzden
    `sys.modules`'taki olası YANLIŞ önbellek bu betiğin KENDİ dosya yoluyla doğrulanır; eşleşmezse
    (başka bir "olcum" önbellekte kalmışsa) YENİDEN yüklenir. Ad çakışması sessizce yanlış modülü
    döndürmesin diye bu koruma VAR."""
    dizin = str(EDG075_DIR)
    if dizin not in sys.path:
        sys.path.insert(0, dizin)
    beklenen = str(EDG075_DIR / "olcum.py")
    mevcut = sys.modules.get("olcum")
    if mevcut is not None and getattr(mevcut, "__file__", None) == beklenen:
        return mevcut
    sys.modules.pop("olcum", None)
    return importlib.import_module("olcum")


_edg075 = _edg075_yukle()
tabloyu_ayristir = _edg075.tabloyu_ayristir
as_of = _edg075.as_of


# ======================================================================================
# KART OKUMA — eşikler ÇALIŞMA ANINDA okunur, koda kopyalanmaz (edg071/edg075 emsali)
# ======================================================================================

def esikleri_karttan_oku(kart_yolu: pathlib.Path = KART_YOLU) -> dict:
    kart = yaml.safe_load(pathlib.Path(kart_yolu).read_text(encoding="utf-8"))
    if not isinstance(kart, dict):
        raise ValueError(f"kart sözlük değil: {kart_yolu}")
    esikler = kart.get("esikler")
    if not isinstance(esikler, dict):
        raise ValueError(f"kart 'esikler' alanı yok/sözlük değil: {kart_yolu}")
    for anahtar in ("k1_gecti", "k2_gecti"):
        if anahtar not in esikler:
            raise ValueError(f"kart eşiği '{anahtar}' bulunamadı ({kart_yolu}) — betik eşiği UYDURAMAZ")
    return {"k1_gecti": str(esikler["k1_gecti"]), "k2_gecti": str(esikler["k2_gecti"]),
           "kart_id": kart.get("card_id"), "kart_yolu": str(kart_yolu)}


def kart_yukle(kart_yolu: pathlib.Path) -> dict:
    """Kart YAML'ının TAMAMI (`esikleri_karttan_oku` yalnız `esikler:` alanını döner) —
    `girdi_kimligi.degisiklik_tablosu` (html sha) buradan okunur."""
    kart = yaml.safe_load(pathlib.Path(kart_yolu).read_text(encoding="utf-8"))
    if not isinstance(kart, dict):
        raise ValueError(f"kart sözlük değil: {kart_yolu}")
    return kart


_ESIK_BANDI_DESENI_SABLONU = (
    r"(?:(?P<alt>[\d,]+)\s*<\s*)?\b{degisken}\b\s*(?P<op>≤|<=|>|<)\s*(?P<esik>[\d,]+)\s*→\s*(?P<etiket>.+?)\s*$"
)


def esik_bandlarini_ayristir(metin: str, degisken: str) -> list[dict]:
    """Kartın 'p ≤ 0,02 → \\'x\\'; 0,02 < p ≤ 0,10 → \\'y\\'; p > 0,10 → \\'z\\'' biçimindeki
    TEK SATIR eşik düzyazısını `[{alt, op, esik, etiket}, ...]` bant listesine ayrıştırır (`;` ile
    bölünür). SAYI (0,02/0,10) koda YAZILMAZ — kart neyi yazarsa o okunur (eşik donuk kalır, karta
    dokunmadan DEĞİŞMEZ). UYDURMA YASAĞI: bir bent kalıba uymuyorsa ValueError (varsayılan bant
    UYDURULMAZ) — kartın serbest-metin alanı bu betiğin BEKLEDİĞİ dilbilgisiyle yazılmalı."""
    bantlar: list[dict] = []
    desen = re.compile(_ESIK_BANDI_DESENI_SABLONU.format(degisken=re.escape(degisken)))
    for parca in metin.split(";"):
        parca = parca.strip()
        if not parca:
            continue
        m = desen.search(parca)
        if not m:
            raise ValueError(f"kart eşik metni beklenen kalıba uymuyor ('{degisken}' bandı): {parca!r}")
        etiket = m.group("etiket").strip()
        if len(etiket) >= 2 and etiket[0] == etiket[-1] == "'":
            etiket = etiket[1:-1]
        alt = float(m.group("alt").replace(",", ".")) if m.group("alt") else None
        esik = float(m.group("esik").replace(",", "."))
        bantlar.append({"alt": alt, "op": m.group("op"), "esik": esik, "etiket": etiket})
    if not bantlar:
        raise ValueError(f"kart eşik metninde '{degisken}' için bant bulunamadı: {metin!r}")
    return bantlar


def hukum_sinifi_sec(deger: float, bantlar: list[dict]) -> str:
    """`deger`i (p ya da q) `esik_bandlarini_ayristir` çıktısındaki bantlara göre sınıflandırır —
    İLK uyan bandın `etiket`ini döner. Hiçbir bant uymazsa ValueError (UYDURMA YASAĞI: bantlar
    donuk kart metninden geldiği için bu, kart YA DA kod arasında bir tutarsızlığı GÖSTERİR,
    sessizce bir varsayılana düşülmez)."""
    for b in bantlar:
        if b["alt"] is not None and not (b["alt"] < deger):
            continue
        op, esik = b["op"], b["esik"]
        if op in ("≤", "<=") and deger <= esik:
            return b["etiket"]
        if op == "<" and deger < esik:
            return b["etiket"]
        if op == ">" and deger > esik:
            return b["etiket"]
    raise ValueError(f"değer {deger} hiçbir banda uymadı: {bantlar}")


# ======================================================================================
# ADIM-0 FİZİBİLİTE — sha256 üçlü doğrulama
# ======================================================================================

def sha256_dosya(yol: pathlib.Path) -> str:
    return hashlib.sha256(pathlib.Path(yol).read_bytes()).hexdigest()


def sha256_defteri_oku(dizin: pathlib.Path) -> dict[str, str]:
    """`SHA256.txt` (coreutils `sha256sum` çıktısı: '<sha>␠␠<dosya_adı>') içeriğini
    `{dosya_adı: sha}` sözlüğüne çevirir. Dosya yoksa BOŞ sözlük (UYDURMA YOK — çağıran bunu
    'beklenen sha yok' diye okur, adım-0 bu girdiyi geçersiz sayar)."""
    yol = pathlib.Path(dizin) / "SHA256.txt"
    if not yol.exists():
        return {}
    defter: dict[str, str] = {}
    for satir in yol.read_text(encoding="utf-8").splitlines():
        parcalar = satir.split(None, 1)
        if len(parcalar) == 2:
            defter[parcalar[1].strip()] = parcalar[0].strip()
    return defter


_HEX64_DESENI = re.compile(r"\b([0-9a-f]{64})\b")


def kart_html_sha_oku(kart: dict) -> str | None:
    """Kartın `girdi_kimligi.degisiklik_tablosu` DÜZYAZISINDAN 64-hex sha256'yı çıkarır (bu alan
    elle bakımlı serbest metin, sha AYRI bir yapılandırılmış alana KONMADI). Bulunamazsa None
    (UYDURMA YOK — adım-0 bunu 'html sha kartta yok' diye sayar)."""
    metin = ((kart.get("girdi_kimligi") or {}).get("degisiklik_tablosu")) or ""
    m = _HEX64_DESENI.search(str(metin))
    return m.group(1) if m else None


def adim0(trades_yolu: pathlib.Path, guncel_liste_yolu: pathlib.Path, html_yolu: pathlib.Path,
         kart: dict) -> dict:
    """Kart `adim_0_fizibilite`: üç girdinin sha256'sı DONUK kayıtla eşit mi. `trades`/`guncel-
    liste` KENDİ dizinlerindeki `SHA256.txt`ye karşı, HTML kartın `girdi_kimligi.
    degisiklik_tablosu` metnindeki 64-hex'e karşı. Üçü de eşitse `gecerli=True`; değilse `olc()`
    bu bayrağı okuyup K1/K2/pozitif_kontrol'ü KOŞTURMAZ — sonuç YİNE üretilir (Yasa 6), yalnız
    ilgili alanlar `None` + `neden` (UYDURMA YOK: 'koşulmadı' ile 'koştu, geçti' KARIŞMAZ)."""
    trades_yolu = pathlib.Path(trades_yolu)
    guncel_liste_yolu = pathlib.Path(guncel_liste_yolu)
    html_yolu = pathlib.Path(html_yolu)

    trades_sha = sha256_dosya(trades_yolu)
    guncel_sha = sha256_dosya(guncel_liste_yolu)
    html_sha = sha256_dosya(html_yolu)

    beklenen_trades = sha256_defteri_oku(trades_yolu.parent).get(trades_yolu.name)
    beklenen_guncel = sha256_defteri_oku(guncel_liste_yolu.parent).get(guncel_liste_yolu.name)
    beklenen_html = kart_html_sha_oku(kart)

    trades_ok = beklenen_trades is not None and trades_sha == beklenen_trades
    guncel_ok = beklenen_guncel is not None and guncel_sha == beklenen_guncel
    html_ok = beklenen_html is not None and html_sha == beklenen_html

    nedenler: list[str] = []
    if not trades_ok:
        nedenler.append(f"trades sha uyuşmuyor: beklenen={beklenen_trades} hesaplanan={trades_sha}")
    if not guncel_ok:
        nedenler.append(f"güncel liste sha uyuşmuyor: beklenen={beklenen_guncel} hesaplanan={guncel_sha}")
    if not html_ok:
        nedenler.append(f"html sha uyuşmuyor: beklenen={beklenen_html} hesaplanan={html_sha}")

    gecerli = trades_ok and guncel_ok and html_ok
    return {
        "trades_sha256": trades_sha, "guncel_liste_sha256": guncel_sha, "html_sha256": html_sha,
        "trades_sha256_beklenen": beklenen_trades, "guncel_liste_sha256_beklenen": beklenen_guncel,
        "html_sha256_beklenen": beklenen_html,
        "trades_sha_esit_mi": trades_ok, "guncel_liste_sha_esit_mi": guncel_ok, "html_sha_esit_mi": html_ok,
        "gecerli": gecerli, "neden": None if gecerli else "; ".join(nedenler),
    }


# ======================================================================================
# NORMALİZASYON + ÜYELİK (rename eşlemesi dahil)
# ======================================================================================

def _normalize_ticker(v) -> str | None:
    """'.'→'-' + upper (`BRK.B`→`BRK-B`); boş/None → None (UYDURMA YOK: boş sembol hakkında
    üyelik hükmü verilmez, çağıran 'olculemedi' sayar)."""
    if v is None:
        return None
    s = str(v).strip().upper().replace(".", "-")
    return s or None


def _ts_open_tarihi(v) -> str | None:
    """`ts_open` hücresini ISO tarihe indirger (ilk 10 karakter — saat/damga varsa atılır).
    Ayrıştırılamazsa None (YASA 4: sessiz atlama değil — çağıran 'olculemedi' kovasına yazar)."""
    if not v:
        return None
    s = str(v).strip()[:10]
    try:
        return dt.date.fromisoformat(s).isoformat()
    except ValueError:  # sessiz-yutma: ts_open ISO'ya uymuyor — çağıran 'olculemedi' kovasına yazar, uydurma yok
        return None


def islem_uye_mi(ticker_ham, ts_open_ham, degisiklikler: list[dict], guncel_uyeler: set[str],
                 rename_defteri, as_of_onbellek: dict) -> tuple[bool | None, str | None]:
    """Kart `girdi_kimligi`: `uye_mi = (ticker ∈ as_of(ts_open)) or (rename ile yeni ad ∈
    as_of(ts_open) and ts_open < rename tarihi)`. `as_of_onbellek` ÇAĞIRAN tarafından tutulan bir
    sözlüktür (tarih → üye kümesi) — aynı gün 901 işlemde TEKRAR KURULMAZ (kart `olcum_plani`
    performans notu). Ölçülemeyen (ticker boş / `ts_open` ayrışmıyor) `(None, neden)` döner — PAYA
    GİRMEZ (çağıran `k1_hesapla` bunu 'olculemedi' sayar, uydurma yok)."""
    ticker = _normalize_ticker(ticker_ham)
    if not ticker:
        return None, "ticker boş/ayrıştırılamadı"
    tarih = _ts_open_tarihi(ts_open_ham)
    if tarih is None:
        return None, "ts_open yok/ayrışmıyor"
    if tarih not in as_of_onbellek:
        as_of_onbellek[tarih] = as_of(degisiklikler, guncel_uyeler, tarih)
    uyeler = as_of_onbellek[tarih]
    if ticker in uyeler:
        return True, None
    for rn in rename_defteri:
        if rn.get("eski") == ticker and tarih < str(rn.get("tarih", "")):
            if rn.get("yeni") in uyeler:
                return True, None
    return False, None


def _medyan(degerler: list[float]) -> float | None:
    return statistics.median(degerler) if degerler else None


# ======================================================================================
# K1 — işlem düzeyi sızıntı (tohum/canlı AYRI)
# ======================================================================================

def k1_hesapla(trades: list[dict], degisiklikler: list[dict], guncel_uyeler: set[str],
              rename_defteri, bantlar: list[dict], as_of_onbellek: dict | None = None) -> dict:
    """Kart `olcum_plani` K1: her işlem için `uye_mi` (`islem_uye_mi`). Tohum (`kaynak ==
    "replay_seed"`) ve canlı (GERİ KALAN her kaynak — kartta '16 live_paper') AYRI raporlanır;
    hüküm YALNIZ tohum üstünden (kart `kill_list`), canlı BİLGİ. `olculemedi` (ticker boş/`ts_open`
    ayrışmıyor) `olculemedi_n`de sayılır, PAYA GİRMEZ (UYDURMA YASAĞI: 'ölçülemedi' ile 'üye
    değil' AYNI piksele düşmez). `n == 0` ise `p`/`hukum_sinifi` None (bölme UYDURULMAZ)."""
    as_of_onbellek = {} if as_of_onbellek is None else as_of_onbellek
    kayitlar: dict[str, list[dict]] = {"tohum": [], "canli": []}
    olculemedi_n = {"tohum": 0, "canli": 0}
    for t in trades:
        grup = "tohum" if t.get("kaynak") == "replay_seed" else "canli"
        uye_mi, _neden = islem_uye_mi(t.get("ticker"), t.get("ts_open"), degisiklikler,
                                      guncel_uyeler, rename_defteri, as_of_onbellek)
        if uye_mi is None:
            olculemedi_n[grup] += 1
            continue
        kayitlar[grup].append({**t, "uye_mi": uye_mi})

    sonuc: dict[str, dict] = {}
    for grup, satirlar in kayitlar.items():
        n = len(satirlar)
        sizanlar = [s for s in satirlar if not s["uye_mi"]]
        n_sizinti = len(sizanlar)
        n_uye = n - n_sizinti
        p = (n_sizinti / n) if n else None
        r_sizan = [s["r_multiple"] for s in sizanlar if isinstance(s.get("r_multiple"), (int, float))]
        r_kalan = [s["r_multiple"] for s in satirlar
                  if s["uye_mi"] and isinstance(s.get("r_multiple"), (int, float))]
        sonuc[grup] = {
            "n": n, "n_uye": n_uye, "n_sizinti": n_sizinti, "p": p,
            "olculemedi_n": olculemedi_n[grup],
            "sizanlar": [{"seq": s.get("seq"), "id": s.get("id"), "ticker": s.get("ticker"),
                         "ts_open": s.get("ts_open"), "r_multiple": s.get("r_multiple")}
                        for s in sizanlar],
            "r_medyan_sizan": _medyan(r_sizan), "r_medyan_kalan": _medyan(r_kalan),
            "hukum_sinifi": hukum_sinifi_sec(p, bantlar) if p is not None else None,
        }
    return sonuc


# ======================================================================================
# K2 — evren düzeyi geç-katılan payı
# ======================================================================================

def k2_hesapla(evren: list[str], degisiklikler: list[dict], guncel_uyeler: set[str], t_evren: str,
              bantlar: list[dict], ikinci_kesit: str = IKINCI_KESIT_TARIHI,
              as_of_onbellek: dict | None = None) -> dict:
    """Kart `olcum_plani` K2: verilen evren (varsayılan `meridian.adapters.data.REPLAY_UNIVERSE`;
    test kendi sentetik evrenini VERİR — kart notu 'REPLAY yerine verilen sentetik evren listesi')
    için `as_of(t_evren)`de üye OLMAYANLARIN payı `q`. `ikinci_kesit` (kart: 2024-01-01) K DEĞİL,
    bilgi amaçlı ikinci kesit — eşiğe TABİ değildir."""
    as_of_onbellek = {} if as_of_onbellek is None else as_of_onbellek
    evren_norm = sorted({t for t in (_normalize_ticker(e) for e in evren) if t})

    def _kesit(tarih: str) -> dict:
        if tarih not in as_of_onbellek:
            as_of_onbellek[tarih] = as_of(degisiklikler, guncel_uyeler, tarih)
        uyeler = as_of_onbellek[tarih]
        uye_olmayan = [t for t in evren_norm if t not in uyeler]
        n = len(evren_norm)
        q = (len(uye_olmayan) / n) if n else None
        return {"tarih": tarih, "uye_olmayanlar": uye_olmayan, "n_uye_olmayan": len(uye_olmayan), "q": q}

    ana = _kesit(t_evren)
    bilgi = _kesit(ikinci_kesit)
    return {
        "t_evren": t_evren, "n_evren": len(evren_norm),
        "uye_olmayanlar": ana["uye_olmayanlar"], "n_uye_olmayan": ana["n_uye_olmayan"], "q": ana["q"],
        "hukum_sinifi": hukum_sinifi_sec(ana["q"], bantlar) if ana["q"] is not None else None,
        "ikinci_kesit": bilgi,
    }


# ======================================================================================
# POZİTİF KONTROL — YOL-TUTARLI, AYNI `islem_uye_mi` fonksiyonu
# ======================================================================================

def pozitif_kontrol(degisiklikler: list[dict], guncel_uyeler: set[str], rename_defteri,
                    as_of_onbellek: dict | None = None, vakalar: tuple[dict, ...] = _PK_VAKALAR) -> dict:
    """Kart `pozitif_kontrol`: üç sentetik işlem AYNI `islem_uye_mi` fonksiyonuyla — (a) FERG
    2026-07-01 → sızıntı (gerçek giriş 2026-08-05'ten ÖNCE), (b) FERG 2026-08-10 → üye (giriş
    SONRASI), (c) EQR 2026-06-01 → üye (rename eşlemesi, `SEMBOL_YENIDEN_ADLANDIRMA`). `tuttu`
    üçü de beklenen gibiyse."""
    as_of_onbellek = {} if as_of_onbellek is None else as_of_onbellek
    detay = []
    for v in vakalar:
        uye_mi, neden = islem_uye_mi(v["ticker"], v["ts_open"], degisiklikler, guncel_uyeler,
                                     rename_defteri, as_of_onbellek)
        detay.append({**v, "olculen": uye_mi, "neden": neden, "tuttu": uye_mi == v["beklenen"]})
    return {"detay": detay, "tuttu": all(d["tuttu"] for d in detay)}


# ======================================================================================
# --olc: TAM ÖLÇÜM (ağ YOK — yalnız verilen dosyalar)
# ======================================================================================

def olc(trades_yolu, guncel_liste_yolu, html_yolu, kart_yolu: pathlib.Path = KART_YOLU,
       t_evren: str = "2022-01-01", evren: list[str] | None = None) -> dict:
    """TAM ÖLÇÜM. `evren=None` ise K2 gerçek `meridian.adapters.data.REPLAY_UNIVERSE`yi kullanır;
    testler kendi sentetik listesini VERİR. `adim0().gecerli` False İSE K1/K2/pozitif_kontrol
    KOŞMAZ (üç alan `None`), sonuç YİNE üretilir (Yasa 6)."""
    trades_yolu = pathlib.Path(trades_yolu)
    guncel_liste_yolu = pathlib.Path(guncel_liste_yolu)
    html_yolu = pathlib.Path(html_yolu)
    kart_yolu = pathlib.Path(kart_yolu)

    kart = kart_yukle(kart_yolu)
    esikler = esikleri_karttan_oku(kart_yolu)
    k1_bantlari = esik_bandlarini_ayristir(esikler["k1_gecti"], "p")
    k2_bantlari = esik_bandlarini_ayristir(esikler["k2_gecti"], "q")

    a0 = adim0(trades_yolu, guncel_liste_yolu, html_yolu, kart)

    girdi_kimligi = {
        "trades_yolu": str(trades_yolu), "guncel_liste_yolu": str(guncel_liste_yolu),
        "html_yolu": str(html_yolu),
        "trades_sha256": a0["trades_sha256"], "guncel_liste_sha256": a0["guncel_liste_sha256"],
        "html_sha256": a0["html_sha256"],
    }

    if a0["gecerli"]:
        guncel_ham = json.loads(guncel_liste_yolu.read_text(encoding="utf-8"))
        guncel_set = {t for t in (_normalize_ticker(g) for g in guncel_ham) if t}

        trades_ham = json.loads(trades_yolu.read_text(encoding="utf-8"))
        satirlar = trades_ham["rows"] if isinstance(trades_ham, dict) and "rows" in trades_ham else trades_ham

        html = html_yolu.read_text(encoding="utf-8")
        degisiklikler, tablo_meta = tabloyu_ayristir(html)
        as_of_onbellek: dict[str, set] = {}
        rename_defteri = list(SEMBOL_YENIDEN_ADLANDIRMA)

        k1 = k1_hesapla(satirlar, degisiklikler, guncel_set, rename_defteri, k1_bantlari, as_of_onbellek)
        kullanilan_evren = list(evren) if evren is not None else list(REPLAY_UNIVERSE)
        k2 = k2_hesapla(kullanilan_evren, degisiklikler, guncel_set, t_evren, k2_bantlari,
                        ikinci_kesit=IKINCI_KESIT_TARIHI, as_of_onbellek=as_of_onbellek)
        pk = pozitif_kontrol(degisiklikler, guncel_set, rename_defteri, as_of_onbellek=as_of_onbellek)
        k1_tohum, k1_canli = k1["tohum"], k1["canli"]
    else:
        tablo_meta = None
        k1_tohum = k1_canli = k2 = pk = None

    return {
        "kart": esikler["kart_id"],
        "olcum_zamani": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "girdi_kimligi": girdi_kimligi,
        "adim_0": a0,
        "tablo_meta": tablo_meta,
        "k1_tohum": k1_tohum,
        "k1_canli": k1_canli,
        "k2": k2,
        "pozitif_kontrol": pk,
        "esikler": {"k1_gecti": esikler["k1_gecti"], "k2_gecti": esikler["k2_gecti"]},
        "beyan": ("Bu betik yalnız ÖLÇER; hüküm Rol-1'de, AYNI turda karta + K defterine işlenir "
                 "(CLAUDE.md §3/§5). meridian/*.py bu turda DEĞİŞTİRİLMEDİ, ağa ÇIKILMADI (yalnız "
                 "--girdi-html'den okundu)."),
    }


# ======================================================================================
# CLI
# ======================================================================================

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="EDG-2026-079 replay/tohum defteri PIT üyelik denetimi (ağsız — yalnız verilen dosyalar)")
    ap.add_argument("--olc", action="store_true", help="ölçümü koşar (AĞ YOK)")
    ap.add_argument("--trades", required=True, help="trades JSON yolu (kendi dizinindeki SHA256.txt ile doğrulanır)")
    ap.add_argument("--guncel-liste", required=True, dest="guncel_liste",
                    help="güncel S&P 500 üyelik JSON'u (liste[str])")
    ap.add_argument("--girdi-html", required=True, dest="girdi_html",
                    help="değişiklik tablosu ham HTML yolu (kartın 64-hex sha'sına karşı doğrulanır)")
    ap.add_argument("--kart", default=str(KART_YOLU), help="kart yolu (varsayılan EDG-2026-079)")
    ap.add_argument("--cikti", default=str(SANDBOX / "sonuc.json"), help="sonuc.json çıktı yolu")
    ap.add_argument("--t-evren", default="2022-01-01", dest="t_evren", help="K2 as_of tarihi (kart örneği 2022-01-01)")
    a = ap.parse_args(argv)

    if not a.olc:
        ap.error("--olc verilmeli")

    sonuc = olc(a.trades, a.guncel_liste, a.girdi_html, kart_yolu=a.kart, t_evren=a.t_evren)
    cikti = json.dumps(sonuc, ensure_ascii=False, indent=2, sort_keys=True, default=str)
    pathlib.Path(a.cikti).write_text(cikti + "\n", encoding="utf-8")
    print(f"yazıldı: {a.cikti}")
    print(cikti)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
