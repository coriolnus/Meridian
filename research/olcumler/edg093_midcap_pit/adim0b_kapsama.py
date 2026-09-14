"""EDG-2026-093 · ADIM-0 (adim_0_fizibilite) EKSEN B — Alpaca IEX BAR KAPSAMA sondası.

Kart: research/cards/EDG-2026-093-midcap-pit-kohort-sagkalan-ust-sinir.yaml
Emsal/desen: research/olcumler/edg070_pit_midcap/adim0_kapsama.py (eksen E; stdin kipi çivisi
tests/test_edg070_adim0_stdin_kipi_v480.py). O dosya İTHAL EDİLMEZ — argparse'ı modül seviyesinde
koşar ve ithal etmek çağıranın argv'siyle bir koşum tetiklerdi.

ORTAK GÖVDE ARTIK BU DOSYADA DEĞİL (2026-09-14, ANA ÖLÇÜM Parti-1). Kohort okuma, pencere/çıkış
hesabı, sembol anahtarı, sha256 ve soğuma yüzeyi `ortak.py`ye taşındı ve buradan İTHAL edilir;
kopyaları SİLİNDİ. Gerekçe: ana ölçümün veri betikleri (veri_bar.py, veri_edgar.py) AYNI
sözleşmeleri okuyor — üç kopya zamanla ayrışırdı (CLAUDE.md §4 tek-kaynak yasası). `ortak.py`
argparse KURMAZ ve modül düzeyinde G/Ç yapmaz, bu yüzden ithal edilebilir.

ORTAK NEREDEN BULUNUR (sıra): `--ortak <yol>` · dosya kipinde bu betiğin YANI · `<repo>/research/
olcumler/edg093_midcap_pit/ortak.py`. Hiçbiri yoksa KULLANIM HATASI (çıkış 2) — sessiz bir yerel
kopyaya düşmek tam olarak yasaklanan şeydir. A1 stdin kipinde `--ortak` ile açık yol verilir.

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
  * SEMBOL NORMALİZASYONU — TUR-2'DE ÖLÇÜLDÜ VE DEĞİŞTİ (2026-09-14). Tur-1 bu dönüşümü
    "ölçülmedi" diye UYGULAMAMIŞTI; ölçülen bedeli 298 isim oldu (aşağı bkz.). Bugün ölçülen:
    `alpaca.daily_bars` sembole YALNIZ `upper().strip()` uygular (nokta/tire dönüşümü YOK) →
    çağıranın yazdığı biçim sağlayıcıya AYNEN gider; motorun kanonik sembolü NOKTA taşır
    (`data._cache_path` şerhi: `BRK.B` diske `brk-b.csv` yazılır) ve sp500 üyelik defteri de
    NOKTA yazar (BRK.B, BF.B) — sp400 kohort defteri ise TİRE (MOG-A). İki defter, iki yazım.
    KURAL (dar): yalnız TEK harflik sınıf son eki (`^[A-Z]+-[A-Z]$`) Alpaca anahtarında noktaya
    çevrilir; `AA`, `MP`, iki harflik son ek DOKUNULMAZ. Kaynak listesi kayda da yazılır
    (`sozlesmeler.sembol_normalizasyonu.sembol_bicimi_kaynagi`).
  * ADAPTER SOĞUMASI ÖLÇÜLÜR VE SIFIRLANIR (tur-2). ÖLÇÜLEN ARIZA: `MOG-A` isteği uçtan HTTP 400
    aldı (A1 olayı 2026-09-14 14:27:02Z `alpaca_data_failed status=400`); `alpaca._data_fail`
    SÜREÇ-İÇİ soğuma penceresi açtı (`_DATA_FAIL_AT`/`_DATA_COOLDOWN`, `DATA_FAIL_COOLDOWN_S`
    300 sn) ve `daily_bars` sonraki HER çağrıda İSTEK ATMADAN None döndü → 298 isim ölçülemedi.
    Bu sonda artık her çağrıdan ÖNCE soğuma durumunu ADAPTERDEN ÖLÇER (`_data_cooled`) ve
    `bars:<feed>` kaydını siler; ölçüm harita kaydına `soguma_aktif`/`soguma_yazildi` olarak
    yazılır — "veri yok" ile "uç soğuk" böylece KARIŞMAZ. Sıfırlama sınırsız DEĞİL: üst üste
    `ARDISIK_OLCULEMEYEN_UST_SINIRI` kadar ölçülemeyen gelirse DURUR (gerçekten düşmüş bir ucu
    661 kez dövmek `alpaca._data_fail`ın kendi gerekçesine aykırıdır — bedel yasası).
  * YENİDEN SONDA VE BİRLEŞTİRME (`--yalniz-olculemeyen`, tur-2): önceki haritadaki `bar_n is
    None` isimleri YALNIZ onları sondalar ve sonucu önceki haritayla birleştirir. ÖNCEKİ ÖLÇÜLMÜŞ
    KAYITLAR AYNEN KORUNUR (yeniden sorulmazlar); özet ve yanlılık tabanı BİRLEŞİK harita
    üzerinden yeniden hesaplanır. KAPI: önceki kaydın `girdi.kohort_csv_sha256`si bu koşumun
    csv'siyle eşit değilse koşum DURUR (iki farklı evren tek haritada karıştırılmaz).

KOMUT SATIRI (sözleşme burasıdır, `main()` değil — CLAUDE.md §1):
    python research/olcumler/edg093_midcap_pit/adim0b_kapsama.py --cikti <dizin> [--kohort <csv>]
    ssh a1 '/opt/meridian/.venv/bin/python - --repo /opt/meridian --cikti <dizin> \\
            --ortak <ortak.py yolu> --kohort <csv> --alpaca-sonda -1' < adim0b_kapsama.py
    … --alpaca-sonda -1 --yalniz-olculemeyen <onceki_kapsama_haritasi.json>   # YENİDEN SONDA
Çıkış kodu: 0 = harita yazıldı · 2 = kullanım hatası (eksik/bozuk girdi, kohort sha uyuşmazlığı,
ortak.py bulunamadı).
"""
from __future__ import annotations

import argparse
import datetime as dt
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
# `parents[2]` SIĞ BİR DİZİNDE PATLAR ve patlama argparse KURULURKEN olur — `--help` bile
# IndexError verir (v480'in ölçtüğü arıza sınıfının DOSYA-KİPİ eşi, 2026-09-14). Derinlik
# yetmiyorsa varsayılan YOKTUR ve `--repo` zorunlu olur.
_REPO_VARSAYILAN = (None if (STDIN_KIPI or len(SANDBOX.parents) < 3)
                    else SANDBOX.parents[2])

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
_ARGS.add_argument("--ortak", type=pathlib.Path, default=None,
                   help="ortak.py'nin AÇIK yolu (stdin kipinde betiğin yanı bilinmez). Verilmezse "
                        "dosya kipinde bu betiğin yanına, sonra <repo>/research/olcumler/"
                        "edg093_midcap_pit/ortak.py yoluna bakılır; bulunmazsa çıkış 2")
_ARGS.add_argument("--alpaca-sonda", type=int, default=0, dest="alpaca_sonda",
                   help="kaç isim için Alpaca IEX bar sorulacak: 0 = ÇAĞRI YOK (harita 'ölçülmedi'), "
                        "N>0 = ilk N isim (alfabetik), -1 = TAMAMI")
_ARGS.add_argument("--yalniz-olculemeyen", type=pathlib.Path, default=None,
                   dest="yalniz_olculemeyen",
                   help="önceki kapsama_haritasi_<damga>.json: YALNIZ bar_n'i None olan semboller "
                        "yeniden sondalanır, sonuç önceki haritayla BİRLEŞTİRİLİR. Önceki kaydın "
                        "kohort csv sha256'sı bu koşumunkiyle eşit değilse koşum DURUR")
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


def _ortak_yukle():
    """`ortak.py`yi ÜÇ ADAYDAN ilk bulunanla yükler ve kimliğini DOĞRULAR.

    Neden kimlik doğrulaması: `ortak` çok genel bir modül adıdır ve bu depoda BAŞKA bir
    `research/olcumler/wp2_olcum/ortak.py` de vardır. Yanlış `ortak` sessizce yüklenirse bu betik
    başka bir ölçümün sözleşmesiyle koşardı — ölçüm bağlamı tuzağının ta kendisi. Bu yüzden dizin
    `sys.path`in BAŞINA konur ve yüklenen modülün `__file__`i beklenen yolla KIYASLANIR."""
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
                  f"(beklenen={aday} yüklenen={yuklenen}) — başka bir ölçümün ortak modülü "
                  f"gölgeledi", file=sys.stderr)
            raise SystemExit(2)
        return _o
    print("KULLANIM HATASI: ortak.py bulunamadı — bakılan yollar: "
          + ", ".join(str(a) for a in adaylar)
          + " (stdin kipinde `--ortak <yol>` verin)", file=sys.stderr)
    raise SystemExit(2)


ortak = _ortak_yukle()

# ---- ORTAK GÖVDEDEN İTHAL (kopya YOK — CLAUDE.md §4 tek-kaynak yasası) ------------------
_kullanim_hatasi = ortak.kullanim_hatasi
sha256 = ortak.sha256
kohort_oku = ortak.kohort_oku
pencere_satirlari = ortak.pencere_satirlari
isim_kumesi_ve_cikislar = ortak.isim_kumesi_ve_cikislar
alpaca_anahtari = ortak.alpaca_anahtari
_bar_tarihi = ortak.bar_tarihi
_soguma_yuzeyi = ortak.soguma_yuzeyi
_soguma_sifirla = ortak.soguma_sifirla
ARDISIK_OLCULEMEYEN_UST_SINIRI = ortak.ARDISIK_OLCULEMEYEN_UST_SINIRI
SEMBOL_BICIMI_KAYNAGI = ortak.SEMBOL_BICIMI_KAYNAGI
SOGUMA_ALANLARI = ortak.SOGUMA_ALANLARI

# ---- BEYANLI SABİTLER (kart DIŞI; bu sondaya ÖZGÜ; kayıtta da yazılırlar) ---------------
ISLEM_GUNU_YIL = 252.0        # bar sayısı → yıl dönüşümü (EDG-070 eksen E ile AYNI sabit)
BARSIZ_TOLERANS_GUN = 7       # "çıkış gününe kadar barı yok" toleransı, TAKVİM günü
ALPACA_BASLANGIC = "2020-07-01"   # sondanın bar penceresi başı (kart penceresinden ~4 hafta önce)

#: Birleştirmede ÖNCEKİ kayıttan devralınan alanlar. Liste TEK KAYNAK: hem okuma hem devralma
#: bunu kullanır — ikinci bir kopya, şema büyüdüğünde sessizce eksik devralırdı.
OLCUM_ALANLARI = ("bar_n", "ilk_bar", "son_bar", "bar_gecmisi_yil", "hata", "neden")


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
# 2. Kohort defteri — as-of okuma: GÖVDE `ortak.py`DE (yukarıda ithal edildi)
# 3. Alpaca IEX sondası — YALNIZ --alpaca-sonda != 0 ile (ağ çağrısı)
# =========================================================================================
def alpaca_sondasi(semboller: list[str], sonda_n: int, bekleme_sn: float,
                   bugun: str) -> tuple[dict, dict]:
    """(sembol → ölçüm kaydı, soğuma özeti). İsim BAŞINA tek çağrı: hem hız-sınırı aralığı hem de
    sembol BAŞINA hata ayrımı ancak böyle mümkün (toplu çağrıda bir patlama tüm kümeyi None
    yapardı). Her çağrıdan ÖNCE soğuma ölçülür ve (sınıra kadar) sıfırlanır."""
    if sonda_n == 0 or not semboller:
        return {}, ortak.soguma_bos_ozet(
            "sonda çağrılmadı (--alpaca-sonda 0 ya da hedef sembol kalmadı) — "
            "meridian.adapters.alpaca İTHAL BİLE EDİLMEDİ")
    from meridian.adapters import alpaca as _alp      # TEMBEL: kuru koşumda hiç ithal edilmez
    yuzey = _soguma_yuzeyi(_alp)
    hedef = semboller if sonda_n < 0 else semboller[:sonda_n]
    out: dict = {}
    sifirlama_n, ardisik_olculemeyen, sifirlama_durdu = 0, 0, False
    for i, s in enumerate(hedef):
        if i and bekleme_sn > 0:
            time.sleep(bekleme_sn)      # hız-sınırı ARALIĞI; tur sayısı isim sayısıyla sınırlı
        anahtar = alpaca_anahtari(s)
        if yuzey["olculdu"]:
            if ardisik_olculemeyen < ARDISIK_OLCULEMEYEN_UST_SINIRI:
                sifirlama_n += 1 if _soguma_sifirla(yuzey) else 0
            else:
                sifirlama_durdu = True
            soguk_once = bool(yuzey["oku"](yuzey["anahtar"]))
        else:
            soguk_once = None
        hata, cevap = None, None
        try:
            cevap = _alp.daily_bars([anahtar], start=ALPACA_BASLANGIC, end=bugun)
        except Exception as e:  # sessiz-yutma DEĞİL: hata sınıfı+metni kayda düşer, sayı UYDURULMAZ
            hata = f"{type(e).__name__}: {e}"[:200]
        soguk_sonra = bool(yuzey["oku"](yuzey["anahtar"])) if yuzey["olculdu"] else None
        soguma = {"soguma_aktif": soguk_once,
                  "soguma_yazildi": (bool(soguk_sonra) and not soguk_once)
                                    if yuzey["olculdu"] else None,
                  "soguma_olculemedi_neden": yuzey["neden"]}
        bos = {"bar_n": None, "ilk_bar": None, "son_bar": None, "bar_gecmisi_yil": None}
        if hata is not None:
            out[s] = {**bos, "hata": hata,
                      "neden": "Alpaca çağrısı hata verdi — kapsama ÖLÇÜLEMEDİ (yokluk KANITI "
                               "değil)", **soguma}
            ardisik_olculemeyen += 1
            continue
        if cevap is None:
            out[s] = {**bos, "hata": None,
                      "neden": ("veri ucu SOĞUMADA — istek ATILMADI (süreç-içi soğuma penceresi "
                                "açık, sıfırlama üst sınırda durdu); ÖLÇÜLEMEDİ, 'veri yok' DEĞİL")
                      if soguk_once else
                      ("daily_bars None döndü (istek atılamadı/patladı) — ÖLÇÜLEMEDİ; "
                       "'soruldu, satır yok' ile aynı şey DEĞİL"), **soguma}
            ardisik_olculemeyen += 1
            continue
        barlar = [b for b in (cevap.get(anahtar) or []) if _bar_tarihi(b)]
        tarihler = sorted(_bar_tarihi(b) for b in barlar)
        out[s] = {"bar_n": len(barlar),
                  "ilk_bar": tarihler[0] if tarihler else None,
                  "son_bar": tarihler[-1] if tarihler else None,
                  "bar_gecmisi_yil": len(barlar) / ISLEM_GUNU_YIL,
                  "hata": None,
                  "neden": None if barlar else "Alpaca cevabı bu sembol için satır taşımıyor "
                                               "(SORULDU — ölçülmüş sıfır, bilinmiyor değil)",
                  **soguma}
        ardisik_olculemeyen = 0
    return out, {"yuzey_olculdu": yuzey["olculdu"], "anahtar": yuzey["anahtar"],
                 "sifirlama_n": sifirlama_n, "ust_sinir": ARDISIK_OLCULEMEYEN_UST_SINIRI,
                 "sifirlama_durdu": sifirlama_durdu, "neden": yuzey["neden"],
                 "gerekce": "soğuma SÜREÇ-İÇİdir (canlı worker AYRI süreç, etkilenmez); sonda "
                            "her çağrıdan önce ölçer ve sıfırlar ki tek sembolün arızası tüm "
                            "kümeyi ölçülemez yapmasın. Sıfırlama üst sınırda DURUR."}


def onceki_harita_oku(yol: pathlib.Path, kohort_sha: str) -> dict:
    """Önceki kapsama haritası + KOHORT KAPISI. Sha eşit değilse koşum DURUR: iki farklı evren
    tek haritada birleştirilirse "aynı kohortun kapsaması" iddiası sessizce yalan olurdu."""
    try:
        ham = json.loads(yol.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:  # sessiz-yutma DEĞİL: neden ADIYLA çıkar, koşum durur
        _kullanim_hatasi(f"--yalniz-olculemeyen dosyası okunamadı ({type(e).__name__}): {yol}")
    onceki_sha = (ham.get("girdi") or {}).get("kohort_csv_sha256")
    if onceki_sha != kohort_sha:
        _kullanim_hatasi(
            "önceki haritanın kohort_csv_sha256'sı bu koşumunkiyle EŞİT DEĞİL — birleştirme iki "
            f"farklı evreni tek haritada karıştırırdı. önceki={onceki_sha} şimdi={kohort_sha} "
            f"dosya={yol}")
    harita = ham.get("harita")
    if not isinstance(harita, list) or not harita:
        _kullanim_hatasi(f"--yalniz-olculemeyen dosyasında 'harita' listesi yok ya da boş: {yol}")
    kayitlar: dict = {}
    for r in harita:
        if not isinstance(r, dict):
            continue
        s = str(r.get("sembol") or "").strip()
        if s:
            kayitlar[s] = {a: r.get(a) for a in OLCUM_ALANLARI + SOGUMA_ALANLARI}
    if not kayitlar:
        _kullanim_hatasi(f"--yalniz-olculemeyen dosyasında sembol taşıyan kayıt yok: {yol}")
    return {"yol": str(yol), "damga": ham.get("damga_utc"), "kayitlar": kayitlar}


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

    kohort_sha = sha256(KOHORT)
    sonda_n = int(ARGV.alpaca_sonda or 0)
    onceki = None
    if ARGV.yalniz_olculemeyen is not None:
        if sonda_n == 0:
            _kullanim_hatasi("--yalniz-olculemeyen ile --alpaca-sonda 0 birlikte anlamsız: "
                             "yeniden sonda ÇAĞRISIZ yapılamaz, harita yalnız yeniden yazılırdı "
                             "(örn. --alpaca-sonda -1 verin)")
        onceki = onceki_harita_oku(ARGV.yalniz_olculemeyen, kohort_sha)
        hedef_isimler = [s for s in isimler
                         if (onceki["kayitlar"].get(s) or {}).get("bar_n") is None
                         and s in onceki["kayitlar"]]
    else:
        hedef_isimler = isimler

    kayitlar, soguma_ozeti = alpaca_sondasi(hedef_isimler, sonda_n, float(ARGV.bekleme_sn),
                                            bugun.isoformat())
    sorulan = len(kayitlar)

    damga = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    onceki_kayitlar = onceki["kayitlar"] if onceki else {}
    devralinan = 0
    harita = []
    for s in isimler:
        k = kayitlar.get(s)
        olcum_damgasi = damga
        if k is None and s in onceki_kayitlar:
            k = dict(onceki_kayitlar[s])          # ÖNCEKİ ÖLÇÜM AYNEN KORUNUR (ezilmez)
            olcum_damgasi = onceki["damga"]
            devralinan += 1
        elif k is None:
            k = {"bar_n": None, "ilk_bar": None, "son_bar": None, "bar_gecmisi_yil": None,
                 "hata": None,
                 "neden": "ölçülmedi — Alpaca sondası bu isim için çağrılmadı (--alpaca-sonda)"}
            olcum_damgasi = None
        for alan in SOGUMA_ALANLARI:
            k.setdefault(alan, None)              # şema koşumlar arası SABİT kalır
        harita.append({"sembol": s, "alpaca_anahtar": alpaca_anahtari(s),
                       "cikis_gunu": cikis[s], "olcum_damgasi": olcum_damgasi, **k})

    harita_kayitlari = {r["sembol"]: r for r in harita}
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
        "soguma": soguma_ozeti,
        # BİRLEŞİK harita üzerinden: devralınan kayıtlar da paya/paydaya girer, yoksa yeniden
        # sonda turu tabanı sessizce yalnız yeni ölçümlerle hesaplardı (tek-kaynak yasası).
        "yanlilik_gostergesi_tabani": barsiz_cikis_payi(harita_kayitlari, cikis),
    }

    if onceki is not None:
        onceki_semboller = set(onceki["kayitlar"])
        birlesim = {
            "onceki_json": onceki["yol"],
            "onceki_damga": onceki["damga"],
            "onceki_harita_n": len(onceki_semboller),
            "yeniden_sondalanan_n": len(hedef_isimler),
            "yeniden_sondalanan_semboller": hedef_isimler,
            "oncekinden_devralinan_n": devralinan,
            "oncekinde_olup_bu_pencerede_olmayan": sorted(onceki_semboller - set(isimler)),
            "bu_pencerede_olup_oncekinde_olmayan": sorted(set(isimler) - onceki_semboller),
            "kohort_csv_sha256_kapisi": "EŞİT — kapı geçildi (eşit olmasaydı koşum dururdu)",
            "kural": "önceki ÖLÇÜLMÜŞ kayıtlar (bar_n not None) AYNEN korunur ve YENİDEN "
                     "SORULMAZ; yalnız bar_n None olanlar sondalanır; özet ve yanlılık tabanı "
                     "BİRLEŞİK harita üzerinden yeniden hesaplanır.",
        }
        birlesim_kaynagi = [onceki["damga"], damga]
        birlesim_neden = None
    else:
        birlesim, birlesim_kaynagi = None, [damga]
        birlesim_neden = ("--yalniz-olculemeyen verilmedi: harita TEK koşumdan doğdu, "
                          "devralınan kayıt YOK")

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
        "birlesim_kaynagi": birlesim_kaynagi,
        "birlesim": birlesim,
        "birlesim_neden": birlesim_neden,
        "girdi": {
            "repo": str(REPO),
            "kohort_csv": str(KOHORT),
            "kohort_csv_sha256": kohort_sha,
            "kohort_satir_n": len(satirlar),
            "kart_yaml": str(KART),
            "kart_sha256": sha256(KART) if KART.exists() else None,
            "kart_sha256_neden": None if KART.exists() else f"kart bu ağaçta yok: {KART}",
            # ORTAK GÖVDE PROVENANSI: hangi `ortak.py` yüklendi ve içeriği neydi. Kopya silindiği
            # için sözleşme artık BU dosyada değil; kaydın onu adıyla taşıması gerekir.
            "ortak_py": str(pathlib.Path(ortak.__file__).resolve()),
            "ortak_py_sha256": sha256(pathlib.Path(ortak.__file__).resolve()),
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
                "uygulanan": "upper().strip() + sınıf-hisse tire→nokta dönüşümü",
                "kaynak": "alpaca.daily_bars içindeki upper/strip DIŞINDA dönüşüm yok; sınıf-hisse "
                          "kuralı ortak.py'de, tek yerde (`alpaca_anahtari`) yaşar ve bu betik "
                          "onu İTHAL eder (kopya YOK).",
                "nokta_tire_donusumu": "kohort defterindeki TEK harflik sınıf son eki (desen "
                                       "^[A-Z]+-[A-Z]$, örn. MOG-A / BRK-B) Alpaca anahtarında "
                                       "NOKTAYA çevrilir (MOG.A / BRK.B). Başka HİÇBİR sembole "
                                       "dokunulmaz: AA, MP ve iki harflik son ek (TST-AB) aynen "
                                       "kalır.",
                "nokta_tire_donusumu_neden": None,
                "sembol_bicimi_kaynagi": SEMBOL_BICIMI_KAYNAGI,
                "sinif_hisse_donusumu": {s: alpaca_anahtari(s) for s in isimler
                                         if alpaca_anahtari(s) != s},
                "nokta_tasiyan_semboller": [s for s in isimler if "." in s or "-" in s],
            },
            "soguma_yonetimi": {
                "olcum": "her sembol çağrısından ÖNCE `alpaca._data_cooled('bars:<feed>')` "
                         "okunur; sonuç kayda `soguma_aktif` olarak yazılır. Çağrıdan SONRA "
                         "yeniden okunur: soğuma bu çağrıyla AÇILDIYSA `soguma_yazildi` true — "
                         "yani ucu soğutan sembol ADIYLA görünür.",
                "sifirlama": "ölçümden hemen önce `bars:<feed>` soğuma kaydı bu SÜREÇTE silinir "
                             "(soğuma modül-düzeyi sözlüktedir, canlı worker AYRI süreçtir ve "
                             "etkilenmez). Tur-1'de tek bir 400, 298 ismi ölçülemez yapmıştı.",
                "ust_sinir": ARDISIK_OLCULEMEYEN_UST_SINIRI,
                "bedel": "sınırsız sıfırlama gerçekten düşmüş bir ucu isim sayısı kadar döverdi "
                         "(adapterin soğuma gerekçesine aykırı); üst üste ust_sinir kadar "
                         "ölçülemeyen gelirse sıfırlama DURUR ve kayıtlar 'uç SOĞUMADA' der.",
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
