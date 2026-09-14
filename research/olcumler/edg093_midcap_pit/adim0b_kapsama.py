"""EDG-2026-093 · ADIM-0 (adim_0_fizibilite) EKSEN B — Alpaca IEX BAR KAPSAMA sondası.

Kart: research/cards/EDG-2026-093-midcap-pit-kohort-sagkalan-ust-sinir.yaml
Emsal/desen: research/olcumler/edg070_pit_midcap/adim0_kapsama.py (eksen E; stdin kipi çivisi
tests/test_edg070_adim0_stdin_kipi_v480.py). O dosya İTHAL EDİLMEZ — argparse'ı modül seviyesinde
koşar ve ithal etmek çağıranın argv'siyle bir koşum tetiklerdi; ortak mantık burada küçük saf
fonksiyonlar olarak YENİDEN yazılmıştır (kopya değil, aynı sözleşmenin ikinci uygulaması).

BU BETİK NE YAPAR: kohort csv'sinden (as-of üyelik defteri) pencere içindeki İSİM KÜMESİNİ ve
ÇIKIŞ GÜNLERİNİ çıkarır, istenirse (`--alpaca-sonda`) her isim için Alpaca IEX günlük barlarını
sorar ve isim başına ilk/son bar + bar sayısı + bar-geçmişi (yıl) haritasını yazar.
NE YAPMAZ: sinyal ölçmez, EŞİK YORUMLAMAZ, HÜKÜM YAZMAZ. Hüküm Rol-1'indir (CLAUDE.md §3).

YASALAR VE SINIRLAR
  * repo/state'e HİÇBİR YAZIM YOK — kohort csv ve kart SALT-OKUNUR açılır; tek yazım `--cikti`
    dizinindeki `kapsama_haritasi_<damga>.json`dır (Yasa 6: okuyucusu kayıtta ADIYLA yazılıdır).
  * `meridian.obs` İTHAL EDİLMEZ. Tek `meridian` teması `meridian.adapters.alpaca` ve o da YALNIZ
    `--alpaca-sonda != 0` dalında, TEMBEL ithalle (CLAUDE.md §2: pytest dışı koşum obs'a ulaşırsa
    canlı yerel deftere yazar).
  * UYDURMA YASAĞI — ölçülemeyen her alan None + `*_neden`. "Soruldu, satır yok" (0) ile
    "sorulamadı" (None) AYRI şeylerdir; `alpaca.daily_bars` sözleşmesi de aynen budur
    (None = istek atılamadı/patladı, {} = soruldu ama satır yok).
  * EŞİKLER KARTTAN OKUNUR (tek-kaynak yasası) — burada yeniden yazılmaz; kart okunamazsa
    eşik None + neden olur ve kıyas satırı DÜŞER, koşum düşmez.
  * `time.sleep` YALNIZ hız-sınırı aralığıdır (isimler arası tek atım), YOKLAMA DÖNGÜSÜ DEĞİL —
    CLAUDE.md §7'nin yasakladığı şey bir koşulun beklenmesidir; burada beklenen bir koşul yoktur,
    çağrı temposu vardır ve tur sayısı isim sayısıyla SINIRLIDIR.

ÖLÇÜLEN SÖZLEŞMELER (varsayılmadı — 2026-09-14, bu turda ölçüldü; kayda da yazılır):
  * KOHORT CSV SATIR ANLAMI: başlık `date,tickers`; satırlar artan tarihli; bir satır KENDİSİNDEN
    SONRAKİ satıra kadar geçerlidir → as_of(t) = tarihi t'den küçük-eşit olan SON satır. Kaynak:
    research/qc_dogrulama/pit_araliklari_uret.py (ölçüm şerhi: 2.718 satır, ardışık 2.717 çiftin
    2.024'ü BİREBİR aynı küme → dosya "her gün" defteri değil, adım fonksiyonu örneklemesi) ve
    research/olcumler/edg070_pit_midcap/adim0_kapsama.py (aynı okuma). Dosya sonrası TAŞINMAZ.
  * ALPACA ÇAĞRI BİÇİMİ: `alpaca.daily_bars(semboller, start=..., end=...)` — timeframe 1Day,
    feed iex, adjustment split ve sort asc çağrının KENDİ içindedir (fonksiyon gövdesinde ölçüldü),
    çağıran bunları GEÇMEZ; EDG-070 eksen E de aynen böyle çağırır. Dönen yapı {TICKER: [bar,…]},
    bar anahtarı "date" (ham API alanı "t" şemaya girmez — `alpaca._to_bar`).
  * SEMBOL NORMALİZASYONU: EDG-070 emsali sembole HİÇBİR dönüşüm uygulamaz (ölçüldü: o dosyada
    replace/translate/re.sub yok); tek normalizasyon `daily_bars`ın kendi `upper().strip()`idir.
    Aynısı uygulanır. `BRK.B`↔`BRK-B` sınıfı nokta/tire dönüşümü ÖLÇÜLMEDİ → UYGULANMAZ ve kayda
    None + neden olarak yazılır; nokta taşıyan semboller ayrıca listelenir ki eşleşmeyen isim
    "kapsanmıyor" diye okunmadan önce bu sınıf görülebilsin.

KOMUT SATIRI (sözleşme burasıdır, `main()` değil — CLAUDE.md §1):
    python research/olcumler/edg093_midcap_pit/adim0b_kapsama.py --cikti <dizin> [--kohort <csv>]
    ssh a1 '/opt/meridian/.venv/bin/python - --repo /opt/meridian --cikti <dizin> \\
            --kohort <csv> --alpaca-sonda -1' < adim0b_kapsama.py     # STDIN KİPİ (deploy YOK)
Çıkış kodu: 0 = harita yazıldı · 2 = kullanım hatası (eksik/bozuk girdi).
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import pathlib
import re
import sys
import time

# A1'de dosya deploy edilmeden `ssh a1 'python - --repo … --cikti …' < betik` ile koşabilsin:
# `python -` kipinde `__file__` TANIMLIDIR ve "<stdin>" değerini taşır — kip onun DEĞERİNDEN
# ölçülür (v480 vakası: `"__file__" in globals()` sınaması stdin'i dosya sanıyordu). Stdin kipinde
# VARSAYILAN YOL YOKTUR: cwd'nin "üç üstü" anlamsızdır ve /opt/meridian'ın iki üstü olduğu için
# `parents[2]` argparse KURULURKEN IndexError verirdi (aynı vaka) — `--repo`/`--cikti` ZORUNLU.
STDIN_KIPI = globals().get("__file__") in (None, "<stdin>")
SANDBOX = pathlib.Path.cwd() if STDIN_KIPI else pathlib.Path(__file__).resolve().parent
_REPO_VARSAYILAN = None if STDIN_KIPI else SANDBOX.parents[2]

_ARGS = argparse.ArgumentParser(
    description="EDG-2026-093 ADIM-0 EKSEN B — Alpaca IEX bar kapsama sondası (salt-okur; hüküm YOK)")
_ARGS.add_argument("--repo", type=pathlib.Path, default=_REPO_VARSAYILAN,
                   help="depo kökü (A1: /opt/meridian; dosya kipinde varsayılan bu dosyanın üç üstü; "
                        "stdin kipinde ZORUNLU)")
_ARGS.add_argument("--cikti", type=pathlib.Path, default=None,
                   help="kapsama_haritasi_<damga>.json'un yazılacağı DİZİN (dosya kipinde varsayılan "
                        "bu klasör; stdin kipinde ZORUNLU — cwd'ye sessizce yazılmaz)")
_ARGS.add_argument("--kohort", type=pathlib.Path, default=None,
                   help="as-of üyelik csv'si (date,tickers). Varsayılan: "
                        "<repo>/research/pit_universe/sp400_uyelik_tarihi.csv")
_ARGS.add_argument("--alpaca-sonda", type=int, default=0, dest="alpaca_sonda",
                   help="kaç isim için Alpaca IEX bar sorulacak: 0 = ÇAĞRI YOK (harita 'ölçülmedi'), "
                        "N>0 = ilk N isim (alfabetik), -1 = TAMAMI")
_ARGS.add_argument("--bekleme-sn", type=float, default=0.35, dest="bekleme_sn",
                   help="isimler ARASI hız-sınırı aralığı, saniye (varsayılan 0.35; yoklama değil)")
_ARGS.add_argument("--baslangic", default="2020-07-27",
                   help="pencere başlangıcı (karttan: veri_penceresi; varsayılan 2020-07-27)")
_ARGS.add_argument("--bugun", default=None, help="pencere sonu (varsayılan: bugün, UTC)")
ARGV = _ARGS.parse_args()
if ARGV.repo is None:
    _ARGS.error("stdin kipinde --repo zorunlu (A1: --repo /opt/meridian)")
if STDIN_KIPI and ARGV.cikti is None:
    _ARGS.error("stdin kipinde --cikti zorunlu (cwd'ye sessizce yazılmaz)")

REPO = ARGV.repo.resolve()
CIKTI_DIZIN = (ARGV.cikti if ARGV.cikti is not None else SANDBOX).resolve()
KOHORT = (ARGV.kohort if ARGV.kohort is not None
          else REPO / "research" / "pit_universe" / "sp400_uyelik_tarihi.csv")
KART = REPO / "research" / "cards" / "EDG-2026-093-midcap-pit-kohort-sagkalan-ust-sinir.yaml"

sys.path.insert(0, str(REPO))          # `meridian` YALNIZ sonda dalında, --repo kökünden çözülür
csv.field_size_limit(10 ** 9)

# ---- BEYANLI SABİTLER (kart DIŞI; kayıtta da yazılırlar) --------------------------------
ISLEM_GUNU_YIL = 252.0        # bar sayısı → yıl dönüşümü (EDG-070 eksen E ile AYNI sabit)
BARSIZ_TOLERANS_GUN = 7       # "çıkış gününe kadar barı yok" toleransı, TAKVİM günü
ALPACA_BASLANGIC = "2020-07-01"   # sondanın bar penceresi başı (kart penceresinden ~4 hafta önce)
KOHORT_BASLIK = ("date", "tickers")


def _kullanim_hatasi(mesaj: str) -> None:
    """Kullanım hatası = çıkış 2 (argparse ile AYNI kod). Sessiz düşme yok: neden stderr'e yazılır."""
    print(f"KULLANIM HATASI: {mesaj}", file=sys.stderr)
    raise SystemExit(2)


def sha256(p: pathlib.Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for blok in iter(lambda: f.read(1 << 20), b""):
            h.update(blok)
    return h.hexdigest()


# =========================================================================================
# 1. Kart eşikleri — TEK KAYNAK karttır; koda gömülmez
# =========================================================================================
#: Kart YAML'i yalnız iki skaler için okunur. PyYAML'e BAĞLANILMAZ (bu betik stdlib'de kalır ve
#: A1'de yorumlayıcı seçiminden bağımsız koşar); desen `esikler:` bloğundaki iki adı hedefler.
_ESIK_DESENLERI = {
    "kapsanan_isim_alt": re.compile(r"^\s{2,}kapsanan_isim_alt:\s*([0-9]+(?:\.[0-9]+)?)\b", re.M),
    "ortalama_bar_gecmisi_yil_alt": re.compile(
        r"^\s{2,}ortalama_bar_gecmisi_yil_alt:\s*([0-9]+(?:\.[0-9]+)?)\b", re.M),
}


def kart_esikleri(kart: pathlib.Path) -> dict:
    """Kart eşikleri + hangi eşiğin NEDEN okunamadığı. Kart yoksa/okunamazsa koşum DÜŞMEZ:
    kıyas satırı None'a düşer (eşik yorumu zaten bu betiğin işi değil — hüküm Rol-1'in)."""
    out: dict = {"kaynak": str(kart), "hukum": "YOK — kıyas satırı; hüküm Rol-1'in"}
    try:
        metin = kart.read_text(encoding="utf-8")
    except OSError as e:  # sessiz-yutma DEĞİL: neden ADIYLA kayda düşer, sayı UYDURULMAZ (None)
        for ad in _ESIK_DESENLERI:
            out[ad] = None
            out[f"{ad}_neden"] = f"kart okunamadı ({type(e).__name__}): {kart}"
        return out
    for ad, desen in _ESIK_DESENLERI.items():
        m = desen.search(metin)
        if m is None:
            out[ad] = None
            out[f"{ad}_neden"] = f"kartın esikler bloğunda '{ad}' bulunamadı"
            continue
        deger = float(m.group(1))
        out[ad] = int(deger) if deger.is_integer() else deger
        out[f"{ad}_neden"] = None
    return out


# =========================================================================================
# 2. Kohort defteri — as-of okuma (satır anlamı yukarıda ÖLÇÜLDÜ)
# =========================================================================================
def kohort_oku(yol: pathlib.Path) -> list[tuple[dt.date, frozenset]]:
    """(tarih, sembol kümesi) satırları, artan tarihte. Başlık ve sıra SÖZLEŞMEDİR: bozuksa
    kullanım hatası — sessizce yanlış kohort ölçmektense koşum durur."""
    try:
        with open(yol, newline="", encoding="utf-8") as f:
            r = csv.reader(f)
            baslik = next(r, None)
            if baslik is None or tuple(x.strip() for x in baslik[:2]) != KOHORT_BASLIK:
                _kullanim_hatasi(f"kohort csv başlığı 'date,tickers' olmalı, görülen: {baslik!r} ({yol})")
            satirlar = [(dt.date.fromisoformat(a[0].strip()),
                         frozenset(t.strip() for t in a[1].split(",") if t.strip()))
                        for a in r if a and a[0].strip()]
    except OSError as e:  # sessiz-yutma DEĞİL: dosya yoksa/okunamıyorsa kullanım hatası olarak ADIYLA çıkar
        _kullanim_hatasi(f"kohort csv okunamadı ({type(e).__name__}): {yol}")
    except ValueError as e:  # sessiz-yutma DEĞİL: bozuk tarih alanı sessizce atlanmaz, koşum durur
        _kullanim_hatasi(f"kohort csv tarih alanı bozuk ({type(e).__name__}: {e}): {yol}")
    if not satirlar:
        _kullanim_hatasi(f"kohort csv boş: {yol}")
    for i in range(len(satirlar) - 1):
        if satirlar[i][0] >= satirlar[i + 1][0]:
            _kullanim_hatasi(f"kohort csv tarihleri artan değil: {satirlar[i][0]} → {satirlar[i+1][0]}")
    return satirlar


def pencere_satirlari(satirlar, baslangic: dt.date, bugun: dt.date):
    """Pencerede ETKİN as-of satırları. Pencere başından ÖNCEKİ son satır bir ÇAPAdır: as-of
    okumasında o satır pencere başında hâlâ yürürlüktedir, tarihi pencereye KIRPILIR."""
    capa = [x for x in satirlar if x[0] <= baslangic]
    etkin = [(baslangic, capa[-1][1])] if capa else []
    etkin.extend((d, k) for d, k in satirlar if baslangic < d <= bugun)
    return etkin, bool(capa)


def isim_kumesi_ve_cikislar(etkin):
    """Pencerede en az bir gün listede olan HER sembol (birleşim) + çıkış günleri.

    ÇIKIŞ GÜNÜ = sembolün listede SON göründüğü satırın ERTESİ as-of değişimi (yani ilk kez
    üye OLMADIĞI as-of tarihi). Pencere sonunda hâlâ listedeyse çıkış YOKTUR (None) — dosya
    sonrası TAŞINMAZ (uydurma yasağı)."""
    son_gorulme: dict[str, int] = {}
    for i, (_, k) in enumerate(etkin):
        for s in k:
            son_gorulme[s] = i
    son_i = len(etkin) - 1
    return ({s: (etkin[i + 1][0].isoformat() if i < son_i else None)
             for s, i in son_gorulme.items()})


# =========================================================================================
# 3. Alpaca IEX sondası — YALNIZ --alpaca-sonda != 0 ile (ağ çağrısı)
# =========================================================================================
def _bar_tarihi(bar: dict):
    """Bizim bar şemamızın tarih alanı "date"tir (ölçüldü: `alpaca._to_bar` onu üretir). "t" ham
    API alanıdır ve şemaya girmez; ikinci okuma yalnız ham satırın sızdığı hâller için durur."""
    if not isinstance(bar, dict):
        return None
    d = bar.get("date") or bar.get("t")
    return str(d)[:10] if d else None


def alpaca_sondasi(semboller: list[str], sonda_n: int, bekleme_sn: float, bugun: str) -> dict:
    """Sembol → ölçüm kaydı. İsim BAŞINA tek çağrı: hem hız-sınırı aralığı hem de sembol BAŞINA
    hata ayrımı ancak böyle mümkün (toplu çağrıda bir patlama tüm kümeyi None yapardı)."""
    if sonda_n == 0:
        return {}
    from meridian.adapters import alpaca as _alp      # TEMBEL: kuru koşumda hiç ithal edilmez
    hedef = semboller if sonda_n < 0 else semboller[:sonda_n]
    out: dict = {}
    for i, s in enumerate(hedef):
        if i and bekleme_sn > 0:
            time.sleep(bekleme_sn)      # hız-sınırı ARALIĞI; tur sayısı isim sayısıyla sınırlı
        anahtar = s.upper().strip()
        try:
            cevap = _alp.daily_bars([s], start=ALPACA_BASLANGIC, end=bugun)
        except Exception as e:  # sessiz-yutma DEĞİL: hata sınıfı+metni kayda düşer, sayı UYDURULMAZ
            out[s] = {"bar_n": None, "ilk_bar": None, "son_bar": None, "bar_gecmisi_yil": None,
                      "hata": f"{type(e).__name__}: {e}"[:200],
                      "neden": "Alpaca çağrısı hata verdi — kapsama ÖLÇÜLEMEDİ (yokluk KANITI değil)"}
            continue
        if cevap is None:
            out[s] = {"bar_n": None, "ilk_bar": None, "son_bar": None, "bar_gecmisi_yil": None,
                      "hata": None,
                      "neden": "daily_bars None döndü (istek atılamadı/patladı ya da veri ucu "
                               "soğumada) — ÖLÇÜLEMEDİ; 'soruldu, satır yok' ile aynı şey DEĞİL"}
            continue
        barlar = [b for b in (cevap.get(anahtar) or []) if _bar_tarihi(b)]
        tarihler = sorted(_bar_tarihi(b) for b in barlar)
        out[s] = {"bar_n": len(barlar),
                  "ilk_bar": tarihler[0] if tarihler else None,
                  "son_bar": tarihler[-1] if tarihler else None,
                  "bar_gecmisi_yil": len(barlar) / ISLEM_GUNU_YIL,
                  "hata": None,
                  "neden": None if barlar else "Alpaca cevabı bu sembol için satır taşımıyor "
                                               "(SORULDU — ölçülmüş sıfır, bilinmiyor değil)"}
    return out


# =========================================================================================
# 4. Yanlılık göstergesinin TABANI — barsız çıkan isim payı
# =========================================================================================
BARSIZ_TANIMI = (f"çıkan bir isim ŞU HÂLDE barsızdır: bar YOK (bar_n == 0) YA DA "
                 f"son_bar < çıkış_günü − {BARSIZ_TOLERANS_GUN} takvim günü. Ölçülemeyen isim "
                 f"(bar_n None: hata/çağrılmadı) paya da paydaya da GİRMEZ, ayrıca sayılır.")


def barsiz_cikis_payi(kayitlar: dict, cikis: dict, tolerans_gun: int = BARSIZ_TOLERANS_GUN) -> dict:
    barsiz, barli, olculemeyen = [], [], []
    for s, gun in sorted(cikis.items()):
        if not gun:
            continue
        k = kayitlar.get(s)
        if k is None or k.get("bar_n") is None:
            olculemeyen.append(s)
            continue
        esik = dt.date.fromisoformat(gun) - dt.timedelta(days=tolerans_gun)
        son = k.get("son_bar")
        (barsiz if (k["bar_n"] == 0 or not son or dt.date.fromisoformat(son) < esik)
         else barli).append(s)
    payda = len(barsiz) + len(barli)
    return {"tanim": BARSIZ_TANIMI, "tolerans_gun": tolerans_gun,
            "cikan_n": sum(1 for g in cikis.values() if g),
            "barsiz_n": len(barsiz), "barli_n": len(barli), "olculemeyen_n": len(olculemeyen),
            "barsiz_semboller": barsiz, "olculemeyen_semboller": olculemeyen,
            "barsiz_cikis_payi": (len(barsiz) / payda) if payda else None,
            "barsiz_cikis_payi_neden": None if payda else
            "ölçülebilir çıkan isim yok (sonda koşulmadı ya da hepsi ölçülemedi)"}


# =========================================================================================
# 5. Koşum
# =========================================================================================
def main() -> int:
    try:
        baslangic = dt.date.fromisoformat(ARGV.baslangic)
    except ValueError as e:  # sessiz-yutma DEĞİL: bozuk tarih kullanım hatasıdır, varsayılana DÜŞÜLMEZ
        _kullanim_hatasi(f"--baslangic ISO tarih olmalı ({e})")
    bugun_s = ARGV.bugun or dt.datetime.now(dt.timezone.utc).date().isoformat()
    try:
        bugun = dt.date.fromisoformat(bugun_s)
    except ValueError as e:  # sessiz-yutma DEĞİL: aynı sınıf — sessiz varsayılan yok
        _kullanim_hatasi(f"--bugun ISO tarih olmalı ({e})")
    if bugun < baslangic:
        _kullanim_hatasi(f"--bugun ({bugun}) --baslangic'tan ({baslangic}) önce olamaz")

    satirlar = kohort_oku(KOHORT)
    etkin, capa_var = pencere_satirlari(satirlar, baslangic, bugun)
    if not etkin:
        _kullanim_hatasi(f"pencerede ({baslangic} → {bugun}) hiç as-of satırı yok: {KOHORT}")
    cikis = isim_kumesi_ve_cikislar(etkin)
    isimler = sorted(cikis)

    sonda_n = int(ARGV.alpaca_sonda or 0)
    kayitlar = alpaca_sondasi(isimler, sonda_n, float(ARGV.bekleme_sn), bugun.isoformat())
    sorulan = len(kayitlar)

    harita = []
    for s in isimler:
        k = kayitlar.get(s) or {
            "bar_n": None, "ilk_bar": None, "son_bar": None, "bar_gecmisi_yil": None, "hata": None,
            "neden": "ölçülmedi — Alpaca sondası bu isim için çağrılmadı (--alpaca-sonda)"}
        harita.append({"sembol": s, "alpaca_anahtar": s.upper().strip(),
                       "cikis_gunu": cikis[s], **k})

    kapsanan = [r for r in harita if (r["bar_n"] or 0) > 0]
    yillar = [r["bar_gecmisi_yil"] for r in kapsanan]
    esik = kart_esikleri(KART)
    ort_yil = (sum(yillar) / len(yillar)) if yillar else None

    ozet = {
        "isim_n": len(isimler),
        "cikan_isim_n": sum(1 for g in cikis.values() if g),
        "sonda_cagrildi": sonda_n != 0,
        "sonda_n": sorulan,
        "orneklem_mi": (sorulan < len(isimler)) if sonda_n != 0 else None,
        "kapsanan_n": len(kapsanan) if sonda_n != 0 else None,
        "kapsanan_n_neden": None if sonda_n != 0 else
        "--alpaca-sonda 0 (kuru koşum; ağ çağrısı YOK) — kapsama ÖLÇÜLMEDİ",
        "ortalama_bar_gecmisi_yil": ort_yil,
        "ortalama_bar_gecmisi_yil_neden": None if ort_yil is not None else
        "kapsanan isim yok (sonda koşulmadı ya da hiçbir isim bar döndürmedi)",
        "olculemeyen_n": sum(1 for r in harita if r["bar_n"] is None),
        "esik_kiyasi": {
            **esik,
            "kapsanan_n_esigi_gecti_mi": (None if (sonda_n == 0 or esik["kapsanan_isim_alt"] is None)
                                          else len(kapsanan) >= esik["kapsanan_isim_alt"]),
            "ortalama_yil_esigi_gecti_mi": (
                None if (ort_yil is None or esik["ortalama_bar_gecmisi_yil_alt"] is None)
                else ort_yil >= esik["ortalama_bar_gecmisi_yil_alt"]),
        },
        "yanlilik_gostergesi_tabani": barsiz_cikis_payi(kayitlar, cikis),
    }

    damga = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    rapor = {
        "kart": "EDG-2026-093",
        "eksen": "adim_0_fizibilite EKSEN B — bar kapsaması (EDG-070 eksen E halefi)",
        "hukum": "YOK — Rol-1",
        "okuyan": "Rol-1: hüküm AYNI turda karta + K defterine işlenir (CLAUDE.md §5). "
                  "Bu dosya o okumanın TEK girdisidir; başka tüketicisi yoktur (Yasa 6 beyanı).",
        "yazim_beyani": "TEK YAZIM bu JSON'dur. repo/state'e yazım YOK; kohort csv ve kart "
                        "SALT-OKUNUR açıldı; meridian.obs İTHAL EDİLMEDİ.",
        "damga_utc": damga,
        "uretici": "research/olcumler/edg093_midcap_pit/adim0b_kapsama.py",
        "girdi": {
            "repo": str(REPO),
            "kohort_csv": str(KOHORT),
            "kohort_csv_sha256": sha256(KOHORT),
            "kohort_satir_n": len(satirlar),
            "kart_yaml": str(KART),
            "kart_sha256": sha256(KART) if KART.exists() else None,
            "kart_sha256_neden": None if KART.exists() else f"kart bu ağaçta yok: {KART}",
        },
        "pencere": {
            "baslangic": baslangic.isoformat(), "bugun": bugun.isoformat(),
            "etkin_as_of_satir_n": len(etkin),
            "pencere_oncesi_capa_satiri_var_mi": capa_var,
            "capa_notu": "pencere başından önceki son satır as-of okumasında hâlâ yürürlüktedir; "
                         "yoksa kohort pencerenin ilk satırından başlar ve bu BEYAN edilir",
        },
        "sozlesmeler": {
            "as_of_okumasi": "as_of(t) = tarihi t'den küçük-eşit olan SON satır; bir satır "
                             "kendisinden sonraki satıra kadar geçerlidir. Dosya sonrası TAŞINMAZ. "
                             "Kaynak: research/qc_dogrulama/pit_araliklari_uret.py ölçüm şerhi + "
                             "research/olcumler/edg070_pit_midcap/adim0_kapsama.py aynı okuma.",
            "cikis_gunu_tanimi": "sembolün SON göründüğü satırın ERTESİ as-of değişimi; pencere "
                                 "sonunda hâlâ üye ise çıkış YOK (None).",
            "alpaca_cagri_bicimi": "alpaca.daily_bars([sembol], start=%s, end=<bugün>) — isim "
                                   "BAŞINA tek çağrı. timeframe=1Day · feed=iex · adjustment=split "
                                   "· sort=asc çağrının KENDİ içindedir (ölçüldü), çağıran "
                                   "geçmez. Dönen yapı {TICKER: [bar,…]}; bar tarih alanı 'date'."
                                   % ALPACA_BASLANGIC,
            "sembol_normalizasyonu": {
                "uygulanan": "upper().strip()",
                "kaynak": "EDG-070 adim0_kapsama.py sembole HİÇBİR dönüşüm uygulamıyor (ölçüldü); "
                          "tek normalizasyon alpaca.daily_bars içindeki upper/strip — aynısı.",
                "nokta_tire_donusumu": None,
                "nokta_tire_donusumu_neden": "BRK.B↔BRK-B sınıfı dönüşümün Alpaca ucundaki doğru "
                                             "yönü bu turda ÖLÇÜLMEDİ; uydurulmadı. Nokta taşıyan "
                                             "isimler aşağıda listelidir — bar dönmezse önce bu "
                                             "sınıf sorgulanır, 'kapsanmıyor' diye okunmaz.",
                "nokta_tasiyan_semboller": [s for s in isimler if "." in s or "-" in s],
            },
            "barsiz_cikis_tanimi": BARSIZ_TANIMI,
            "bar_gecmisi_yil_donusumu": f"bar_n / {ISLEM_GUNU_YIL} (EDG-070 eksen E ile AYNI sabit)",
            "bekleme": {"bekleme_sn": float(ARGV.bekleme_sn),
                        "not": "isimler ARASI hız-sınırı aralığı; yoklama döngüsü DEĞİL "
                               "(beklenen bir koşul yok, tur sayısı isim sayısıyla sınırlı)"},
        },
        "harita": harita,
        "ozet": ozet,
    }

    CIKTI_DIZIN.mkdir(parents=True, exist_ok=True)
    hedef = CIKTI_DIZIN / f"kapsama_haritasi_{damga}.json"
    hedef.write_text(json.dumps(rapor, ensure_ascii=False, indent=1, sort_keys=False) + "\n",
                     encoding="utf-8")
    print(f"YAZILDI: {hedef}")
    print(f"isim_n={ozet['isim_n']} çıkan={ozet['cikan_isim_n']} sonda_n={ozet['sonda_n']} "
          f"kapsanan_n={ozet['kapsanan_n']} ort_yıl={ozet['ortalama_bar_gecmisi_yil']} "
          f"barsız_pay={ozet['yanlilik_gostergesi_tabani']['barsiz_cikis_payi']}")
    print("HÜKÜM YOK — eşik kıyası bir kıyas satırıdır; hüküm Rol-1'in (karta + K defterine).")
    return 0


raise SystemExit(main())
