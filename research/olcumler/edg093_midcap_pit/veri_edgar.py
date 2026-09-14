"""EDG-2026-093 · ANA ÖLÇÜM Parti-1 — EDGAR HİSSE SAYISI KURULUMU (PIT, `filed` korunur).

Kart: research/cards/EDG-2026-093-midcap-pit-kohort-sagkalan-ust-sinir.yaml
Emsal ve TEK KAYNAK: research/edgar_facts/ (README PIT semantiği; betikler/build_cikmap.py,
download.py, extract.py, finalize.py). O betikler ÇALIŞMA DİZİNİNE KİLİTLİDİR (modül düzeyinde
`cikmap.json` okur, mutlak `OUT` yoluna yazar, ağa çıkar) — İTHAL EDİLMEZLER; sözleşmeleri
(etiket kümesi, şema, UA/nezaket, dönem türü merdiveni) ortak.py tarafından KAYNAK METİNDEN
türetilir ve türetilemeyen her alan beyanlı tabana düşüp kayda ADIYLA yazılır.

NEDEN YENİ BİR ÇEKİM. research/edgar_facts/ evreni `REPLAY_UNIVERSE` + `RETIRED_SYMBOLS`tir
(259 sembol, S&P 500 ağırlıklı). Bu kartın kohortu S&P 400 PIT defteridir (661 isim) ve ÖLÇÜLDÜ
(2026-09-14): mevcut haritayla örtüşen sembol sayısı 11. Yani hisse sayısı serisi bu kohort için
YENİDEN çekilmelidir; turnover ölçüsü (medyan21(hacim) / as_of_shares(t)) onsuz tanımsızdır.

PIT — SIFIR TOLERANS (CLAUDE.md §4). `end` DEĞERİN AİT OLDUĞU tarihtir, `filed` DEĞERİN BİLİNİR
OLDUĞU ilk gündür. Ölçüm `filed`i kullanır. Bu betik:
  * `filed` alanını HER satırda KORUR ve `end` ile hiçbir filtre UYGULAMAZ,
  * `filed`i BOŞ olan satırı REDDEDER (PIT'te kullanılamaz; kaç satır düştüğü kayda yazılır),
  * satırları ne düzeltir ne birleştirir — kaynaktaki yeniden beyan ve düzeltmeler GERÇEK
    olaylardır ve silinmez (README'nin Alphabet örneği: aynı `end`, iki `filed`, iki değer).

CIK EŞLEMESİ — SIRA SABİTTİR VE KAYDA YAZILIR:
  (1) research/edgar_facts/cik_haritasi.json (zaten ölçülmüş eşlemeler),
  (2) SEC `company_tickers.json` (bir kez indirilir, sha ile kayda bağlanır),
  (3) research/pit_universe/sp400_elle_esleme.yaml karar çiftlerinin DİĞER ADI,
  (4) hiçbiri çözmezse sembol EŞLEŞMEYEN listesine yazılır — CIK UYDURULMAZ (delist/rename
      beklenen bir sonuçtur, boşluk sayıyla teslim edilir).
(3) İKİ JETONU AYIRIR ve bu ayrım hükmü taşır: `esle:<eski>-><yeni>` bir YENİDEN ADLANDIRMA
KİMLİĞİDİR (aynı ihraççı, aynı CIK beklenir); `cift:<cikan>-><giren>` bir ANOTASYONDUR — iki
yarım satır aynı endeks olayının iki kitaplamasıdır ve tipik olarak İKİ AYRI İHRAÇÇIDIR
(spin-off). `cift`ten türetilen eşleme bu yüzden "kanıtlanmış kimlik" DEĞİLDİR: kayıt onu
`kimlik_kaniti: anotasyon_cift` ile ayırır, ayrıca listeler ve hükmü Rol-1'e bırakır.

AĞ DİSİPLİNİ (download.py'nin disiplini, kaynağından türetilir): SIRALI, tek bağlantı, kimlik
bildiren User-Agent, istek arası gecikme, `Accept-Encoding: gzip`, ham JSON gzip'lenip
`<cikti>/edgar/raw/` altına yazılır ve sha256'sı manifeste işlenir; VAR OLAN DOSYA YENİDEN
İNDİRİLMEZ. Atılan HER istek — atılmadan ÖNCE — `<cikti>/edgar/istek_defteri.jsonl` dosyasına
düşer: "ağa çıkılmadı" iddiası böylece VARSAYIM değil ÖLÇÜM olur.

YASALAR VE SINIRLAR
  * `meridian` HİÇ İTHAL EDİLMEZ (bu betiğin hiçbir dalında motor yolu yoktur).
  * `--sec 0` → HİÇBİR istek atılmaz; yalnız eşleme raporu (+ diskte hazır dosya varsa çıkarım).
  * UYDURMA YASAĞI — ölçülemeyen her alan None + neden.
  * HÜKÜM YOK; eşik yorumlanmaz.

KOMUT SATIRI (sözleşme burasıdır, `main()` değil — CLAUDE.md §1):
    python research/olcumler/edg093_midcap_pit/veri_edgar.py --repo <kök> --cikti <dizin> --sec 0
    ssh a1 '/opt/meridian/.venv/bin/python - --repo /opt/meridian --ortak <ortak.py> \\
            --cikti <dizin> --sec 1' < veri_edgar.py              # STDIN KİPİ (deploy YOK)
Çıkış kodu: 0 = kayıt yazıldı · 2 = kullanım hatası (eksik/bozuk girdi, ortak.py yok).
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import gzip
import hashlib
import io
import json
import pathlib
import sys
import time
import urllib.error
import urllib.request

STDIN_KIPI = globals().get("__file__") in (None, "<stdin>")
SANDBOX = pathlib.Path.cwd() if STDIN_KIPI else pathlib.Path(__file__).resolve().parent
# `parents[2]` SIĞ BİR DİZİNDE PATLAR ve patlama argparse KURULURKEN olur (v480 arıza sınıfı):
# betik A1'de sığ bir dizine kopyalanıp DOSYA kipinde koşabilir. Derinlik yetmiyorsa varsayılan
# YOKTUR ve `--repo` zorunlu olur — sessiz yanlış kök yerine açık kullanım hatası.
_REPO_VARSAYILAN = (None if (STDIN_KIPI or len(SANDBOX.parents) < 3)
                    else SANDBOX.parents[2])

_ARGS = argparse.ArgumentParser(
    description="EDG-2026-093 ANA ÖLÇÜM Parti-1 — EDGAR hisse sayısı çekimi (PIT; hüküm YOK)")
_ARGS.add_argument("--repo", type=pathlib.Path, default=_REPO_VARSAYILAN,
                   help="depo kökü (A1: /opt/meridian; stdin kipinde ZORUNLU)")
_ARGS.add_argument("--cikti", type=pathlib.Path, default=None,
                   help="edgar/ alt ağacının yazılacağı DİZİN (stdin kipinde ZORUNLU)")
_ARGS.add_argument("--ortak", type=pathlib.Path, default=None,
                   help="ortak.py'nin AÇIK yolu (stdin kipinde betiğin yanı bilinmez)")
_ARGS.add_argument("--kohort", type=pathlib.Path, default=None,
                   help="as-of üyelik csv'si; varsayılan "
                        "<repo>/research/pit_universe/sp400_uyelik_tarihi.csv")
_ARGS.add_argument("--kart", type=pathlib.Path, default=None, help="kart yaml'i (pencere kaynağı)")
_ARGS.add_argument("--esleme", type=pathlib.Path, default=None,
                   help="elle eşleme yaml'i; varsayılan "
                        "<repo>/research/pit_universe/sp400_elle_esleme.yaml")
_ARGS.add_argument("--kohort-baslangic", default=None, dest="kohort_baslangic",
                   help="kohort penceresinin başı; verilmezse karttan okunur")
_ARGS.add_argument("--bugun", default=None, help="pencere sonu (varsayılan: bugün, UTC)")
_ARGS.add_argument("--sec", type=int, default=0,
                   help="0 = AĞA ÇIKMA (yalnız eşleme raporu + diskte hazır olanın çıkarımı), "
                        "1 = company_tickers + companyfacts indir")
_ARGS.add_argument("--bekleme-sn", type=float, default=None, dest="bekleme_sn",
                   help="istekler ARASI gecikme; verilmezse download.py `DELAY` değerinden "
                        "türetilir (SEC fair-access; yoklama döngüsü DEĞİL)")
_ARGS.add_argument("--company-tickers", type=pathlib.Path, default=None, dest="company_tickers",
                   help="hazır company_tickers.json yolu; verilmezse <cikti>/edgar/ altındaki "
                        "kopya kullanılır (yoksa ve --sec 1 ise indirilir)")
ARGV = _ARGS.parse_args()
if ARGV.repo is None:
    _ARGS.error("stdin kipinde --repo zorunlu (A1: --repo /opt/meridian)")
if STDIN_KIPI and ARGV.cikti is None:
    _ARGS.error("stdin kipinde --cikti zorunlu (cwd'ye sessizce yazılmaz)")

REPO = ARGV.repo.resolve()
CIKTI_DIZIN = (ARGV.cikti if ARGV.cikti is not None else SANDBOX).resolve()
KOHORT = (ARGV.kohort if ARGV.kohort is not None
          else REPO / "research" / "pit_universe" / "sp400_uyelik_tarihi.csv")
ESLEME = (ARGV.esleme if ARGV.esleme is not None
          else REPO / "research" / "pit_universe" / "sp400_elle_esleme.yaml")
KART = (ARGV.kart if ARGV.kart is not None
        else REPO / "research" / "cards"
        / "EDG-2026-093-midcap-pit-kohort-sagkalan-ust-sinir.yaml")
EDGAR_DIZIN = CIKTI_DIZIN / "edgar"
RAW_DIZIN = EDGAR_DIZIN / "raw"
ISTEK_DEFTERI = EDGAR_DIZIN / "istek_defteri.jsonl"


def _ortak_yukle():
    """`ortak.py`yi üç adaydan ilk bulunanla yükler ve KİMLİĞİNİ doğrular (bu depoda ikinci bir
    `ortak.py` daha var — yanlışı sessizce yüklenirse başka bir ölçümün sözleşmesi koşardı)."""
    adaylar = []
    if ARGV.ortak is not None:
        adaylar.append(pathlib.Path(ARGV.ortak))
    if not STDIN_KIPI:
        adaylar.append(SANDBOX / "ortak.py")
    adaylar.append(REPO / "research" / "olcumler" / "edg093_midcap_pit" / "ortak.py")
    for aday in adaylar:
        aday = aday.resolve()
        if not aday.is_file():
            continue
        sys.path.insert(0, str(aday.parent))
        import ortak as _o
        yuklenen = pathlib.Path(getattr(_o, "__file__", "") or "").resolve()
        if yuklenen != aday:
            print(f"KULLANIM HATASI: yüklenen `ortak` beklenen dosya DEĞİL "
                  f"(beklenen={aday} yüklenen={yuklenen})", file=sys.stderr)
            raise SystemExit(2)
        return _o
    print("KULLANIM HATASI: ortak.py bulunamadı — bakılan yollar: "
          + ", ".join(str(a) for a in adaylar) + " (stdin kipinde `--ortak <yol>` verin)",
          file=sys.stderr)
    raise SystemExit(2)


ortak = _ortak_yukle()

#: CIK eşleme kaynaklarının SIRASI — liste TEK KAYNAK: hem çözüm hem kayıt bunu yazar.
ESLEME_SIRASI = ("edgar_facts_cik_haritasi", "sec_company_tickers", "elle_esleme_cifti")


# =================================================================================================
# 1. AĞ — download.py'nin disiplini, her istek DEFTERE düşer
# =================================================================================================
def _ssl_baglami():
    """SEC bağlantısı için SSL bağlamı. `certifi` varsa onun CA paketi kullanılır (download.py
    aynısını yapar: sistem CA yolu boş olabiliyor); yoksa yorumlayıcının varsayılanı."""
    import ssl
    try:
        import certifi
    except ImportError as e:
        # sessiz-yutma DEĞİL: certifi yok — varsayılan bağlamla devam edilir ve bu KAYDA yazılır
        return ssl.create_default_context(), f"certifi YOK ({e}) — varsayılan CA paketi"
    return ssl.create_default_context(cafile=certifi.where()), "certifi CA paketi"


def _istek_defterine_yaz(kayit: dict) -> None:
    """Atılacak isteği — ATILMADAN ÖNCE — deftere yazar.

    YASA 6 OKUYUCU: `kaynak_sp400.json` bu dosyayı adıyla anar ve istek sayısını ondan alır;
    çiviler de "--sec 0'da ağa çıkılmadı" iddiasını BU dosyanın yokluğuyla ölçer. Sayılan şeyin
    kendisini üretmek, "ölçtüm" ile "varsaydım" arasındaki farktır."""
    ISTEK_DEFTERI.parent.mkdir(parents=True, exist_ok=True)
    with open(ISTEK_DEFTERI, "a", encoding="utf-8") as f:
        f.write(json.dumps(kayit, ensure_ascii=False) + "\n")


def indir(url: str, politika: dict, baglam, amac: str) -> tuple[bytes | None, dict]:
    """(gövde, kayıt) — tek bir SEC isteği. Hata SESSİZ DEĞİL: kayda HTTP kodu/istisna yazılır."""
    kayit = {"url": url, "amac": amac,
             "istek_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
    _istek_defterine_yaz(dict(kayit))          # ÖNCE defter, SONRA istek
    istek = urllib.request.Request(url, headers={"User-Agent": politika["user_agent"],
                                                 "Accept-Encoding": "gzip"})
    try:
        with urllib.request.urlopen(istek, timeout=90, context=baglam) as cevap:
            govde = cevap.read()
            if cevap.headers.get("Content-Encoding") == "gzip":
                govde = gzip.decompress(govde)
            kayit |= {"http": cevap.status, "bytes": len(govde),
                      "sha256": hashlib.sha256(govde).hexdigest()}
            return govde, kayit
    except urllib.error.HTTPError as e:  # sessiz-yutma DEĞİL: HTTP kodu kayda ADIYLA düşer
        kayit |= {"http": e.code, "bytes": 0, "sha256": None, "hata": str(e)}
    except Exception as e:  # sessiz-yutma DEĞİL: ağ/SSL arızası kayda düşer, koşum devam eder
        kayit |= {"http": None, "bytes": 0, "sha256": None, "hata": f"{type(e).__name__}: {e}"}
    return None, kayit


# =================================================================================================
# 2. CIK EŞLEMESİ
# =================================================================================================
def edgar_facts_haritasi(repo: pathlib.Path):
    """`(sembol → (cik, baslik), neden)` — mevcut ölçülmüş harita."""
    yol = repo / "research" / "edgar_facts" / "cik_haritasi.json"
    try:
        ham = json.loads(yol.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        # sessiz-yutma DEĞİL: mevcut harita okunamadı — kaynak (1) DÜŞER ve neden kayda yazılır
        return {}, f"cik_haritasi.json okunamadı ({type(e).__name__}): {yol}"
    out = {}
    for r in (ham.get("eslesen") or []):
        s = str(r.get("symbol") or "").upper().strip()
        if s and r.get("cik") is not None:
            out.setdefault(s, (int(r["cik"]), r.get("title")))
    return out, None


def company_tickers_haritasi(yol: pathlib.Path):
    """`(sembol → (cik, baslik), neden)` — SEC `company_tickers.json` biçimi
    `{"0": {"cik_str": …, "ticker": …, "title": …}, …}` (build_cikmap.py aynı okumayı yapar)."""
    try:
        ham = json.loads(pathlib.Path(yol).read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        # sessiz-yutma DEĞİL: dosya yok/bozuk — kaynak (2) DÜŞER ve neden kayda yazılır
        return {}, f"company_tickers.json okunamadı ({type(e).__name__}): {yol}"
    out = {}
    for r in (ham.values() if isinstance(ham, dict) else ham):
        if not isinstance(r, dict):
            continue
        t = str(r.get("ticker") or "").upper().strip()
        if t and r.get("cik_str") is not None:
            out.setdefault(t, (int(r["cik_str"]), r.get("title")))
    return out, None


def cik_esle(isimler, kaynak1: dict, kaynak2: dict, komsular: dict):
    """(eslesen, eslesmeyen, cift_turetilen) — eşleme SIRASI `ESLEME_SIRASI`dır.

    Bir sembol hiçbir kaynakta çözülmezse CIK UYDURULMAZ; `eslesmeyen` listesine nedeniyle yazılır
    (S&P 400'de delist/birleşme sık, boşluk sayıyla teslim edilir)."""
    eslesen, eslesmeyen, cift_turetilen = [], [], []
    for s in isimler:
        for kaynak_adi, harita in (("edgar_facts_cik_haritasi", kaynak1),
                                   ("sec_company_tickers", kaynak2)):
            vurus = harita.get(s)
            if vurus:
                eslesen.append({"symbol": s, "cik": vurus[0], "title": vurus[1], "rol": "sp400",
                                "cik_kaynak": kaynak_adi, "kimlik_kaniti": "dogrudan_ticker",
                                "uyari": None})
                break
        else:
            cozuldu = False
            for diger, jeton in komsular.get(s, []):
                vurus = kaynak1.get(diger) or kaynak2.get(diger)
                if not vurus:
                    continue
                kanit = ortak.KARAR_KIMLIK_KANITI.get(jeton, jeton)
                uyari = None if jeton == "esle" else (
                    "cift kararı bir ANOTASYONDUR (iki yarım satır, aynı endeks olayı) — aynı "
                    "ihraççı olduğu KANITLANMADI; bu eşleme Rol-1'in hükmüne bırakılır")
                kayit = {"symbol": s, "cik": vurus[0], "title": vurus[1], "rol": "sp400",
                         "cik_kaynak": f"elle_esleme_cifti:{jeton}:{s}->{diger}",
                         "kimlik_kaniti": kanit, "uyari": uyari}
                eslesen.append(kayit)
                if jeton != "esle":
                    cift_turetilen.append(kayit)
                cozuldu = True
                break
            if not cozuldu:
                eslesmeyen.append({"symbol": s, "rol": "sp400",
                                   "neden": "hiçbir kaynakta çözülemedi (sıra: "
                                            + " → ".join(ESLEME_SIRASI) + ")"})
    return eslesen, eslesmeyen, cift_turetilen


# =================================================================================================
# 3. ÇIKARIM — companyfacts → PIT hisse-adedi satırları
# =================================================================================================
def satirlari_cek(facts: dict, etiketler):
    """extract.py'nin çıkarım kuralıyla AYNI satırlar: etiket kümesi × birim × giriş, aynı
    tekilleştirme anahtarı ((tag, unit, start, end, val, filed, accn, form)) ve aynı sıralama.

    `filed` BOŞ satır REDDEDİLİR (PIT'te kullanılamaz — `filed` değerin BİLİNİR olduğu gündür;
    o gün yoksa satır hiçbir as-of soruya cevap veremez). Kaç satırın bu yüzden düştüğü SAYILIR
    ve kayda yazılır: sessizce süzülen satır, ölçülmemiş bir boşluk olurdu."""
    gorulen, satirlar, filed_bos = set(), [], 0
    for tax, tag in etiketler:
        dugum = ((facts.get(tax) or {}).get(tag) or {})
        for unit, girisler in (dugum.get("units") or {}).items():
            for e in (girisler or []):
                if not isinstance(e, dict):
                    continue
                anahtar = (tag, unit, e.get("start"), e.get("end"), e.get("val"),
                           e.get("filed"), e.get("accn"), e.get("form"))
                if anahtar in gorulen:
                    continue
                gorulen.add(anahtar)
                if not e.get("filed"):
                    filed_bos += 1
                    continue                    # PIT KAPISI — `end` ile ikame EDİLMEZ
                start = e.get("start") or ""
                gun = ortak.donem_gun(start, e.get("end"))
                satirlar.append({"taxonomy": tax, "tag": tag, "unit": unit, "start": start,
                                 "end": e.get("end"), "filed": e.get("filed"), "val": e.get("val"),
                                 "form": e.get("form"), "fy": e.get("fy"), "fp": e.get("fp"),
                                 "donem_gun": "" if gun is None else gun,
                                 "donem_turu": ortak.donem_turu(gun),
                                 "accn": e.get("accn"), "frame": e.get("frame") or ""})
    satirlar.sort(key=lambda r: (r["tag"], str(r["end"] or ""), str(r["filed"] or "")))
    return satirlar, filed_bos


def csv_gz_yaz(hedef: pathlib.Path, kolonlar, satirlar) -> dict:
    """Satırları 16 kolonluk şemayla gzip'li CSV'ye yazar; sha'ları döndürür.

    `mtime=0`: gzip başlığına zaman damgası GİRMEZ, yani aynı içerik aynı sha'yı verir — bir
    ölçüm girdisinin kimliği içeriğinden gelmelidir, yazıldığı saatten değil."""
    tampon = io.StringIO()
    y = csv.writer(tampon, lineterminator="\n")
    y.writerow(kolonlar)
    for r in satirlar:
        y.writerow(["" if r.get(k) is None else r.get(k) for k in kolonlar])
    duz = tampon.getvalue().encode("utf-8")
    hedef.parent.mkdir(parents=True, exist_ok=True)
    hedef.write_bytes(gzip.compress(duz, compresslevel=6, mtime=0))
    return {"dosya": hedef.name, "satir_n": len(satirlar),
            "duz_bayt": len(duz), "duz_sha256": hashlib.sha256(duz).hexdigest(),
            "gz_bayt": hedef.stat().st_size, "gz_sha256": ortak.sha256(hedef)}


def main() -> int:
    bugun_s = ARGV.bugun or dt.datetime.now(dt.timezone.utc).date().isoformat()
    try:
        bugun = dt.date.fromisoformat(bugun_s)
    except ValueError as e:  # sessiz-yutma DEĞİL: bozuk tarih kullanım hatasıdır
        ortak.kullanim_hatasi(f"--bugun ISO tarih olmalı ({e})")
    if ARGV.kohort_baslangic is not None:
        baslangic_s, pencere_kaynak, pencere_neden = ARGV.kohort_baslangic, "--kohort-baslangic", None
    else:
        baslangic_s, pencere_neden = ortak.kart_pencere_baslangici(KART)
        pencere_kaynak = f"karttan türetildi: {KART} `veri_penceresi`"
        if baslangic_s is None:
            ortak.kullanim_hatasi(
                f"kohort penceresinin başı karttan okunamadı ({pencere_neden}) — sessiz varsayılan "
                f"YOK; `--kohort-baslangic <YYYY-AA-GG>` ile açık verin")
    try:
        baslangic = dt.date.fromisoformat(baslangic_s)
    except ValueError as e:  # sessiz-yutma DEĞİL: kart/bayrak tarihi bozuksa koşum durur
        ortak.kullanim_hatasi(f"kohort penceresi başı ISO tarih olmalı ({e}): {baslangic_s!r}")

    satirlar = ortak.kohort_oku(KOHORT)
    etkin, capa_var = ortak.pencere_satirlari(satirlar, baslangic, bugun)
    if not etkin:
        ortak.kullanim_hatasi(f"pencerede ({baslangic} → {bugun}) as-of satırı yok: {KOHORT}")
    cikis = ortak.isim_kumesi_ve_cikislar(etkin)
    isimler = sorted(cikis)

    politika = ortak.sec_politikasi(REPO)
    bekleme = float(ARGV.bekleme_sn) if ARGV.bekleme_sn is not None else politika["bekleme_sn"]
    baglam, ca_kaynak = _ssl_baglami()
    etiketler, etiket_kaynak, etiket_neden = ortak.hisse_etiketleri(REPO)
    kolonlar, kolon_kaynak, kolon_neden = ortak.edgar_kolonlari(REPO)
    damga = ortak.damga_uret()
    EDGAR_DIZIN.mkdir(parents=True, exist_ok=True)

    # ---- (a) CIK EŞLEMESİ ---------------------------------------------------------------
    kaynak1, kaynak1_neden = edgar_facts_haritasi(REPO)
    tickers_yol = (ARGV.company_tickers if ARGV.company_tickers is not None
                   else EDGAR_DIZIN / "company_tickers.json")
    tickers_kayit = {"yol": str(tickers_yol), "indirildi": False, "sha256": None, "neden": None}
    if not pathlib.Path(tickers_yol).exists():
        if int(ARGV.sec or 0) == 1:
            govde, istek = indir(politika["tickers_url"], politika, baglam, "company_tickers")
            tickers_kayit["istek"] = istek
            if govde is not None:
                pathlib.Path(tickers_yol).write_bytes(govde)
                tickers_kayit.update({"indirildi": True, "sha256": istek.get("sha256")})
            else:
                tickers_kayit["neden"] = ("company_tickers.json İNDİRİLEMEDİ — kaynak (2) DÜŞTÜ; "
                                          "eşleşmeyen listesi bu yüzden ŞİŞMİŞ olabilir")
        else:
            tickers_kayit["neden"] = ("--sec 0: ağa çıkılmadı ve diskte kopya YOK — kaynak (2) "
                                      "atlandı (eşleşmeyen listesi ŞİŞER, bu bir ölçüm değil)")
    else:
        tickers_kayit["sha256"] = ortak.sha256(pathlib.Path(tickers_yol))
        tickers_kayit["neden"] = "diskteki kopya kullanıldı (yeniden indirilmedi)"
    kaynak2, kaynak2_neden = ({}, tickers_kayit["neden"]) if not pathlib.Path(tickers_yol).exists() \
        else company_tickers_haritasi(tickers_yol)

    desen_metni, desen_neden = ortak.kaynaktan_desen(
        REPO / "research" / "olcumler" / "edg093_midcap_pit" / "kohort.py", "KARAR_CIFT_RE")
    ciftler, cift_neden = ortak.karar_ciftleri(ESLEME, desen_metni)
    komsular = ortak.esleme_komsulari(ciftler)
    eslesen, eslesmeyen, cift_turetilen = cik_esle(isimler, kaynak1, kaynak2, komsular)

    by_cik: dict[int, list[str]] = {}
    for r in eslesen:
        by_cik.setdefault(int(r["cik"]), []).append(r["symbol"])
    harita_json = {
        "eslesen": eslesen, "eslesmeyen": eslesmeyen,
        "paylasilan_cik": {str(c): s for c, s in by_cik.items() if len(s) > 1},
        "esleme_sirasi": list(ESLEME_SIRASI),
        "kaynak_nedenleri": {"edgar_facts_cik_haritasi": kaynak1_neden,
                             "sec_company_tickers": kaynak2_neden,
                             "elle_esleme_cifti": cift_neden,
                             "karar_grameri": desen_neden},
        "okuyan": "bu betiğin (b) çekim ve (c) çıkarım adımları + Rol-1 (eşleşmeyen sınıfının "
                  "hükmü); ayrıca kaynak_sp400.json bu dosyayı adıyla anar.",
    }
    ortak.manifest_yaz(EDGAR_DIZIN, "cik_haritasi_sp400.json", harita_json)

    # ---- (b) COMPANYFACTS ÇEKİMİ --------------------------------------------------------
    indirme_manifesti, toplam_bayt, istek_n = [], 0, 0
    for i, (cik, semboller) in enumerate(sorted(by_cik.items())):
        url = politika["companyfacts_tpl"].format(cik=cik)
        hedef = RAW_DIZIN / f"CIK{cik:010d}.json.gz"
        kayit = {"cik": cik, "symbols": sorted(semboller), "url": url, "dosya": hedef.name}
        if hedef.exists():
            ham = _gz_oku(hedef)
            kayit |= {"http": 200, "bytes": (len(ham) if ham is not None else None),
                      "sha256": (hashlib.sha256(ham).hexdigest() if ham is not None else None),
                      "not": "diskteki dosya (bu koşumda yeniden indirilmedi)",
                      "indirme_utc": dt.datetime.fromtimestamp(
                          hedef.stat().st_mtime, dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
            if ham is None:
                kayit["hata"] = "diskteki gzip AÇILAMADI — bu CIK çıkarımda ATLANIR"
            indirme_manifesti.append(kayit)
            continue
        if int(ARGV.sec or 0) != 1:
            kayit |= {"http": None, "bytes": 0, "sha256": None,
                      "neden": "--sec 0: indirilmedi (ağa çıkılmadı) — ÇEKİLMEDİ, 'veri yok' DEĞİL"}
            indirme_manifesti.append(kayit)
            continue
        if istek_n:
            time.sleep(bekleme)     # SEC fair-access ARALIĞI; tur sayısı CIK sayısıyla sınırlı
        govde, istek = indir(url, politika, baglam, f"companyfacts CIK{cik:010d}")
        istek_n += 1
        kayit |= {k: v for k, v in istek.items() if k not in ("url", "amac")}
        if govde is not None:
            RAW_DIZIN.mkdir(parents=True, exist_ok=True)
            hedef.write_bytes(gzip.compress(govde, compresslevel=6, mtime=0))
            toplam_bayt += len(govde)
        indirme_manifesti.append(kayit)

    # ---- (c) ÇIKARIM --------------------------------------------------------------------
    cik_sembolleri = {int(r["cik"]): [] for r in eslesen}
    for r in eslesen:
        cik_sembolleri[int(r["cik"])].append(r["symbol"])
    tum_satirlar, kapsam, eksik_dosya, bos_facts, filed_bos_toplam = [], {}, [], [], 0
    for cik, semboller in sorted(cik_sembolleri.items()):
        yol = RAW_DIZIN / f"CIK{cik:010d}.json.gz"
        ham = _gz_oku(yol) if yol.exists() else None
        if ham is None:
            eksik_dosya.append({"cik": cik, "symbols": sorted(semboller),
                                "neden": ("ham dosya YOK (çekilmedi ya da indirilemedi)"
                                          if not yol.exists() else "gzip/JSON açılamadı")})
            continue
        try:
            facts = (json.loads(ham).get("facts") or {})
        except ValueError as e:
            # sessiz-yutma DEĞİL: bozuk JSON kayda ADIYLA düşer, diğer CIK'ler etkilenmez
            eksik_dosya.append({"cik": cik, "symbols": sorted(semboller),
                                "neden": f"JSON ayrıştırılamadı ({type(e).__name__}: {e})"})
            continue
        if not facts:
            bos_facts.append({"cik": cik, "symbols": sorted(semboller),
                              "neden": "companyfacts `facts` boş (yabancı ihraççı / yalnız 'ffd')"})
            continue
        satir, filed_bos = satirlari_cek(facts, etiketler)
        filed_bos_toplam += filed_bos * max(len(semboller), 1)
        for sym in sorted(semboller):
            k = kapsam.setdefault(sym, {"symbol": sym, "cik": cik, "satir_n": 0, "shares_dei_n": 0,
                                        "shares_anlik_n": 0, "shares_wavg_n": 0,
                                        "shares_dei_end_min": None, "shares_dei_end_max": None,
                                        "filed_min": None, "filed_max": None})
            for r in satir:
                tum_satirlar.append({"symbol": sym, "cik": cik, **r})
                k["satir_n"] += 1
                k["shares_%s_n" % ortak.etiket_semantigi(r["tag"])] += 1
                if r["taxonomy"] == "dei":
                    k["shares_dei_n"] += 1
                    k["shares_dei_end_min"] = _min(k["shares_dei_end_min"], r["end"])
                    k["shares_dei_end_max"] = _max(k["shares_dei_end_max"], r["end"])
                k["filed_min"] = _min(k["filed_min"], r["filed"])
                k["filed_max"] = _max(k["filed_max"], r["filed"])
    tum_satirlar.sort(key=lambda r: (r["symbol"], r["tag"], str(r["end"] or ""),
                                     str(r["filed"] or "")))
    seri = csv_gz_yaz(EDGAR_DIZIN / "shares_outstanding_sp400.csv.gz", kolonlar, tum_satirlar)

    kapsam_kolonlari = ["symbol", "cik", "satir_n", "shares_dei_n", "shares_anlik_n",
                        "shares_wavg_n", "shares_dei_end_min", "shares_dei_end_max",
                        "filed_min", "filed_max"]
    kapsam_yolu = EDGAR_DIZIN / "sembol_kapsam_sp400.csv"
    with open(kapsam_yolu, "w", newline="", encoding="utf-8") as f:
        y = csv.DictWriter(f, kapsam_kolonlari)
        y.writeheader()
        for sym in sorted(kapsam):
            y.writerow({k: ("" if kapsam[sym].get(k) is None else kapsam[sym][k])
                        for k in kapsam_kolonlari})

    kaynak = {
        "kart": "EDG-2026-093",
        "asama": "ANA ÖLÇÜM Parti-1 — EDGAR hisse sayısı kurulumu (ölçüm DEĞİL, veri)",
        "hukum": "YOK — Rol-1",
        "okuyan": "(1) Rol-1: eşleşmeyen sınıfı ve cift-türetilen eşlemelerin hükmü; (2) Parti-2 "
                  "ölçüm boru hattı: as_of_shares(t) serisini shares_outstanding_sp400.csv.gz'den "
                  "`filed <= t` ile okur (Yasa 6 beyanı).",
        "yazim_beyani": "YAZILAN HER ŞEY --cikti/edgar altındadır. repo/state'e yazım YOK; kohort, "
                        "kart, elle eşleme ve edgar_facts SALT-OKUNUR açıldı; meridian İTHAL "
                        "EDİLMEDİ.",
        "damga_utc": damga,
        "uretici": "research/olcumler/edg093_midcap_pit/veri_edgar.py",
        "pit_beyani": {
            "kural": "`filed` = değerin BİLİNİR olduğu ilk gün; ölçüm `filed <= t` kullanır. "
                     "`end` yalnız dönem etiketidir ve BU BETİKTE HİÇBİR FİLTREDE kullanılmaz.",
            "filed_bos_reddedilen_satir_n": filed_bos_toplam,
            "end_ile_filtre": False,
            "satir_duzeltmesi": "YOK — yeniden beyan ve düzeltmeler GERÇEK olaylardır, silinmedi.",
        },
        "girdi": {
            "repo": str(REPO), "kohort_csv": str(KOHORT),
            "kohort_csv_sha256": ortak.sha256(KOHORT), "kohort_satir_n": len(satirlar),
            "elle_esleme_yaml": str(ESLEME),
            "elle_esleme_sha256": ortak.sha256(ESLEME) if ESLEME.exists() else None,
            "kart_yaml": str(KART),
            "kart_sha256": ortak.sha256(KART) if KART.exists() else None,
            "ortak_py": str(pathlib.Path(ortak.__file__).resolve()),
            "ortak_py_sha256": ortak.sha256(pathlib.Path(ortak.__file__).resolve()),
        },
        "pencere": {"baslangic": baslangic.isoformat(), "baslangic_kaynak": pencere_kaynak,
                    "baslangic_neden": pencere_neden, "bugun": bugun.isoformat(),
                    "etkin_as_of_satir_n": len(etkin),
                    "pencere_oncesi_capa_satiri_var_mi": capa_var},
        "sozlesmeler": {
            "etiket_kumesi": [list(x) for x in etiketler],
            "etiket_kumesi_kaynak": etiket_kaynak, "etiket_kumesi_neden": etiket_neden,
            "kolonlar": kolonlar, "kolonlar_kaynak": kolon_kaynak, "kolonlar_neden": kolon_neden,
            "istek_politikasi": politika, "ca_kaynak": ca_kaynak,
            "bekleme_sn": bekleme,
            "istek_defteri": str(ISTEK_DEFTERI),
            "istek_defteri_notu": "atılan HER istek ATILMADAN ÖNCE buraya düşer; '--sec 0'da ağa "
                                  "çıkılmadı' iddiası bu dosyanın YOKLUĞUYLA ölçülür.",
            "karar_jetonlari": {"esle": "YENİDEN ADLANDIRMA KİMLİĞİ — aynı ihraççı",
                                "cift": "ANOTASYON — iki yarım satır, aynı endeks olayı; AYNI "
                                        "İHRAÇÇI OLDUĞU KANITLANMADI"},
        },
        "esleme": {
            "isim_n": len(isimler), "eslesen_n": len(eslesen), "eslesmeyen_n": len(eslesmeyen),
            "benzersiz_cik_n": len(by_cik),
            "paylasilan_cik_n": sum(1 for s in by_cik.values() if len(s) > 1),
            "kaynak_dagilimi": _say([r["cik_kaynak"].split(":")[0] for r in eslesen]),
            "cift_turetilen_n": len(cift_turetilen),
            "cift_turetilen": cift_turetilen,
            "eslesmeyen": eslesmeyen,
            "karar_cifti_n": len(ciftler),
        },
        "cekim": {
            "sec": int(ARGV.sec or 0), "atilan_istek_n": istek_n,
            "company_tickers": tickers_kayit,
            "indirilen_bayt": toplam_bayt,
            "diskte_hazir_n": sum(1 for m in indirme_manifesti if m.get("not")),
            "basarisiz_n": sum(1 for m in indirme_manifesti if m.get("hata")),
            "cekilmeyen_n": sum(1 for m in indirme_manifesti if m.get("neden")),
            "manifest": indirme_manifesti,
        },
        "seri": seri,
        "kapsam": {
            "dosya": kapsam_yolu.name, "sembol_n": len(kapsam),
            "eksik_dosya": eksik_dosya, "bos_facts": bos_facts,
            "kapsanmayan_sembol_n": len(isimler) - len(kapsam),
        },
    }
    hedef = ortak.manifest_yaz(EDGAR_DIZIN, "kaynak_sp400.json", kaynak)
    print(f"YAZILDI: {hedef}")
    print(f"isim_n={len(isimler)} eşleşen={len(eslesen)} eşleşmeyen={len(eslesmeyen)} "
          f"cift_türetilen={len(cift_turetilen)} istek={istek_n} satır={seri['satir_n']} "
          f"kapsanan_sembol={len(kapsam)} filed_boş_red={filed_bos_toplam}")
    print("HÜKÜM YOK — bu bir VERİ kurulumudur; hüküm Rol-1'in (karta + K defterine).")
    return 0


def _gz_oku(yol: pathlib.Path):
    """Gzip'li ham JSON baytları; açılamazsa None (çağıran nedeni kayda yazar)."""
    try:
        return gzip.decompress(pathlib.Path(yol).read_bytes())
    except (OSError, ValueError, EOFError):
        # sessiz-yutma DEĞİL: bozuk/yarım gzip — None döner ve çağıran kaydı ADIYLA düşer
        return None


def _min(a, b):
    return b if a is None else (a if b is None else min(a, b))


def _max(a, b):
    return b if a is None else (a if b is None else max(a, b))


def _say(degerler):
    out: dict[str, int] = {}
    for d in degerler:
        out[d] = out.get(d, 0) + 1
    return out


raise SystemExit(main())
