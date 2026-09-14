"""EDG-2026-093 · ANA ÖLÇÜM Parti-1 — BAR VERİSİ KURULUMU (Alpaca IEX günlük barlar).

Kart: research/cards/EDG-2026-093-midcap-pit-kohort-sagkalan-ust-sinir.yaml
Selef: adim0b_kapsama.py (EKSEN B kapsama SONDASI — bar SAYAR, bar YAZMAZ). Bu betik onun
halefi değil TAMAMLAYICISIDIR: aynı isim kümesini alır ve barları DİSKE yazar.

BU BETİK NE YAPAR: kohort defterinden pencere içindeki isim kümesini çıkarır, her isim için
Alpaca IEX günlük barlarını sorar ve CANLI BAR ARŞİVİNİN ŞEMASIYLA `<cikti>/bars/<ad>.csv`
yazar; her ismin sonucunu (satır sayısı, ilk/son bar, sha256, hata/neden) bir manifeste işler.
NE YAPMAZ: sinyal ölçmez, eşik yorumlamaz, HÜKÜM YAZMAZ (CLAUDE.md §3 — hüküm Rol-1'in);
repo/state'e yazmaz; barı TEMİZLEMEZ (takvim kapısı/bütünlük dışlaması Parti-2'nin işidir ve
canlı boru hattının KENDİ fonksiyonlarıyla yapılır — burada ikinci bir uygulama yazmak, aynı
yasanın iki kopyasını doğururdu).

NEDEN CANLI ŞEMA (ölçüldü 2026-09-14). Parti-2 ölçüm boru hattı bu dosyaları
`meridian/adapters/data.py` içindeki `sanitize_bars` / `measurement_bars` / `integrity_safe_start`
üçlüsünden geçirecek (emsal: research/olcumler/wp2_olcum/ortak.py `load_bars`). O yol
`pd.read_csv(..., parse_dates=["date"])` ile okur ve kolon adlarına göre çalışır; dosya adı da
motorun `_cache_path` kuralıyla üretilir. Bu yüzden:
  * kolon şeması `data.py` içindeki `COLS` sabitinden TÜRETİLİR (kopyalanmaz — ortak.py
    `bar_kolonlari`; türetme düşerse beyanlı tabana düşülür ve bu kayda ADIYLA yazılır),
  * dosya adı ortak.py `bar_dosya_adi` ile üretilir (`MOG-A` → `mog-a.csv`, canlı arşivle AYNI).

PIT GİRDİSİ DONUKTUR — ÜZERİNE YAZMA YOK. Var olan bir bar dosyası varsayılan olarak YENİDEN
ÇEKİLMEZ. `--yeniden-cek` ile yeniden çekilirse içerik diskteki sha ile KIYASLANIR: aynıysa
yazım YOK, farklıysa yeni içerik `<ad>__<damga>.csv` YAN DOSYASINA yazılır ve özgün dosya
DOKUNULMADAN kalır. Gerekçe: bir ölçüm girdisi koşumlar arasında sessizce değişirse kartın
dondurduğu şey ölür (vaka EDG-2026-059, üç kez) — ayrışma SESSİZ değil, DOSYA olarak görünür.

YASALAR VE SINIRLAR
  * `meridian.obs` İTHAL EDİLMEZ. Tek `meridian` teması `meridian.adapters.alpaca` ve o da
    YALNIZ `--alpaca != 0` dalında, TEMBEL ithalle (CLAUDE.md §2).
  * UYDURMA YASAĞI — ölçülemeyen her alan None + `neden`. "Soruldu, satır yok" (0) ile
    "sorulamadı" (None) AYRI şeylerdir; `alpaca.daily_bars` sözleşmesi de aynen budur.
  * `time.sleep` YALNIZ hız-sınırı aralığıdır (isimler arası tek atım), YOKLAMA DÖNGÜSÜ DEĞİL —
    CLAUDE.md §7'nin yasakladığı şey bir KOŞULUN beklenmesidir; burada beklenen koşul yoktur,
    çağrı temposu vardır ve tur sayısı isim sayısıyla SINIRLIDIR.
  * SOĞUMA ÖLÇÜLÜR VE (sınıra kadar) SIFIRLANIR — gövde ortak.py'de, gerekçesi orada yazılı.
    Tek sembolün HTTP 400'ü 298 ismi ölçülemez yapmıştı (A1 olayı 2026-09-14).
  * PENCERE KARTTAN OKUNUR: kohort penceresinin başı kartın `veri_penceresi` alanından türetilir
    (koda gömülmez). Bar çekim penceresi AYRIDIR ve daha ERKEN başlar (`--baslangic`): 21 günlük
    medyan hacim, rvol20 ve momentum özellikleri pencerenin İLK gününde de tanımlı olmalıdır,
    yani en az ~12 ay ısınma gerekir. İki tarihin karıştırılması ölçümün ilk aylarını sessizce
    yarım özellikle bırakırdı.

KOMUT SATIRI (sözleşme burasıdır, `main()` değil — CLAUDE.md §1):
    python research/olcumler/edg093_midcap_pit/veri_bar.py --repo <kök> --cikti <dizin>
    ssh a1 '/opt/meridian/.venv/bin/python - --repo /opt/meridian --ortak <ortak.py> \\
            --cikti <dizin> --alpaca -1' < veri_bar.py            # STDIN KİPİ (deploy YOK)
    … --yalniz-eksik <onceki_bars_manifest.json>       # yalnız eksik/hatalı isimleri çeker
Çıkış kodu: 0 = manifest yazıldı · 2 = kullanım hatası (eksik/bozuk girdi, ortak.py yok,
kohort sha uyuşmazlığı).
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import io
import json
import pathlib
import sys
import time

# A1'de dosya deploy edilmeden `ssh a1 'python - --repo … --cikti …' < betik` ile koşabilsin:
# `python -` kipinde `__file__` TANIMLIDIR ve "<stdin>" değerini taşır — kip onun DEĞERİNDEN
# ölçülür (v480 vakası). Stdin kipinde VARSAYILAN YOL YOKTUR: `--repo`/`--cikti` ZORUNLU.
STDIN_KIPI = globals().get("__file__") in (None, "<stdin>")
SANDBOX = pathlib.Path.cwd() if STDIN_KIPI else pathlib.Path(__file__).resolve().parent
# `parents[2]` SIĞ BİR DİZİNDE PATLAR ve patlama argparse KURULURKEN olur — yani `--help` bile
# IndexError verir (v480'in tam olarak ölçtüğü arıza sınıfı). Betik A1'de `/tmp/edg093` gibi sığ
# bir dizine kopyalanıp DOSYA kipinde koşacağı için bu yol gerçektir: derinlik yetmiyorsa
# varsayılan YOKTUR ve `--repo` zorunlu olur (sessiz yanlış kök yerine açık kullanım hatası).
_REPO_VARSAYILAN = (None if (STDIN_KIPI or len(SANDBOX.parents) < 3)
                    else SANDBOX.parents[2])

_ARGS = argparse.ArgumentParser(
    description="EDG-2026-093 ANA ÖLÇÜM Parti-1 — Alpaca IEX bar çekimi (hüküm YOK)")
_ARGS.add_argument("--repo", type=pathlib.Path, default=_REPO_VARSAYILAN,
                   help="depo kökü (A1: /opt/meridian; stdin kipinde ZORUNLU)")
_ARGS.add_argument("--cikti", type=pathlib.Path, default=None,
                   help="bars/ ve bars_manifest_<damga>.json'un yazılacağı DİZİN "
                        "(stdin kipinde ZORUNLU — cwd'ye sessizce yazılmaz)")
_ARGS.add_argument("--ortak", type=pathlib.Path, default=None,
                   help="ortak.py'nin AÇIK yolu; verilmezse dosya kipinde betiğin yanına, sonra "
                        "<repo>/research/olcumler/edg093_midcap_pit/ortak.py yoluna bakılır")
_ARGS.add_argument("--kohort", type=pathlib.Path, default=None,
                   help="as-of üyelik csv'si (date,tickers). Varsayılan: "
                        "<repo>/research/pit_universe/sp400_uyelik_tarihi.csv")
_ARGS.add_argument("--kart", type=pathlib.Path, default=None,
                   help="kart yaml'i (kohort penceresinin başı buradan okunur)")
_ARGS.add_argument("--kohort-baslangic", default=None, dest="kohort_baslangic",
                   help="kohort penceresinin başı; VERİLMEZSE karttan (`veri_penceresi`) okunur. "
                        "Kart okunamazsa koşum DURUR — sessiz varsayılan yok")
_ARGS.add_argument("--baslangic", default="2019-06-01",
                   help="BAR çekim penceresinin başı (kohort penceresi DEĞİL). Varsayılan "
                        "2019-06-01: kart penceresinin (2020-07-27) ilk gününde 21g medyan hacim / "
                        "rvol20 / momentum tanımlı olsun diye ≥12 ay ısınma")
_ARGS.add_argument("--bugun", default=None, help="pencere sonu (varsayılan: bugün, UTC)")
_ARGS.add_argument("--bekleme-sn", type=float, default=0.6, dest="bekleme_sn",
                   help="isimler ARASI hız-sınırı aralığı, saniye (varsayılan 0.6; yoklama değil)")
_ARGS.add_argument("--alpaca", type=int, default=0,
                   help="kaç isim çekilecek: 0 = ÇAĞRI YOK (kuru koşum, manifest 'çağrılmadı'), "
                        "N>0 = ilk N isim (alfabetik), -1 = TAMAMI")
_ARGS.add_argument("--yalniz-eksik", type=pathlib.Path, default=None, dest="yalniz_eksik",
                   help="önceki bars_manifest_<damga>.json: YALNIZ o manifestte OLMAYAN ya da "
                        "dosyası yazılmamış/hatalı isimler çekilir. Önceki kaydın kohort sha'sı "
                        "bu koşumunkiyle eşit değilse koşum DURUR")
_ARGS.add_argument("--yeniden-cek", action="store_true", dest="yeniden_cek",
                   help="var olan bar dosyası için de çağrı atılır ve içerik diskteki sha ile "
                        "KIYASLANIR (fark varsa YAN DOSYA yazılır; üzerine yazma YOK)")
ARGV = _ARGS.parse_args()
if ARGV.repo is None:
    _ARGS.error("stdin kipinde --repo zorunlu (A1: --repo /opt/meridian)")
if STDIN_KIPI and ARGV.cikti is None:
    _ARGS.error("stdin kipinde --cikti zorunlu (cwd'ye sessizce yazılmaz)")

REPO = ARGV.repo.resolve()
CIKTI_DIZIN = (ARGV.cikti if ARGV.cikti is not None else SANDBOX).resolve()
KOHORT = (ARGV.kohort if ARGV.kohort is not None
          else REPO / "research" / "pit_universe" / "sp400_uyelik_tarihi.csv")
KART = (ARGV.kart if ARGV.kart is not None
        else REPO / "research" / "cards"
        / "EDG-2026-093-midcap-pit-kohort-sagkalan-ust-sinir.yaml")

sys.path.insert(0, str(REPO))          # `meridian` YALNIZ çekim dalında, --repo kökünden çözülür


def _ortak_yukle():
    """`ortak.py`yi üç adaydan ilk bulunanla yükler ve KİMLİĞİNİ doğrular (bu depoda ikinci bir
    `ortak.py` daha var — yanlışı sessizce yüklenirse betik başka bir ölçümün sözleşmesiyle
    koşardı)."""
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

#: Manifest kaydının TEK KAYNAK alan listesi — hem yazım hem önceki manifestten hedef seçimi
#: bunu kullanır. İkinci bir kopya, şema büyüdüğünde sessizce eksik okurdu.
KAYIT_ALANLARI = ("sembol", "alpaca_anahtar", "dosya", "satir_n", "ilk_bar", "son_bar",
                  "tekrarli_tarih_n", "sha256", "durum", "hata", "neden", "yan_dosya",
                  "soguma_aktif", "soguma_yazildi", "soguma_olculemedi_neden")

#: Bir ismin "eksik" sayıldığı durumlar — `--yalniz-eksik` hedefini BU küme belirler.
#: "ölçülmüş sıfır" (satır_n == 0, uç soruldu ve satır yok) EKSİK DEĞİLDİR: yeniden sormak
#: ölçülmüş bir gerçeği ölçülmemiş sanmak olurdu (uydurma yasağının tersi yönü).
EKSIK_DURUMLAR = frozenset({"olculemedi", "cagrilmadi", "yan_dosya"})


def _bos_kayit(sembol: str) -> dict:
    return {"sembol": sembol, "alpaca_anahtar": ortak.alpaca_anahtari(sembol), "dosya": None,
            "satir_n": None, "ilk_bar": None, "son_bar": None, "tekrarli_tarih_n": None,
            "sha256": None, "durum": None, "hata": None, "neden": None, "yan_dosya": None,
            "soguma_aktif": None, "soguma_yazildi": None, "soguma_olculemedi_neden": None}


def csv_metni(kolonlar: list[str], barlar: list[dict]) -> str:
    """Bar listesinden CANLI ARŞİV ŞEMASIYLA csv metni. Satırlar tarihe göre ARTAN.

    Eksik alan BOŞ hücre olur (pandas NaN okur) — sıfır YAZILMAZ: "alan yok" ile "değer sıfır"
    aynı piksele düşerse Parti-2 hacim sıfırını gerçek sanardı (uydurma yasağı).
    TEKRARLI TARİH DÜŞÜRÜLMEZ: yinelenen tarihin son satırını tutmak `sanitize_bars`ın KENDİ
    kuralıdır ve burada ikinci kez yazılmaz (aynı yasanın iki kopyası ayrışır); sayısı kayda
    `tekrarli_tarih_n` olarak düşer."""
    tampon = io.StringIO()
    y = csv.writer(tampon, lineterminator="\n")
    y.writerow(kolonlar)
    for b in sorted(barlar, key=lambda x: ortak.bar_tarihi(x) or ""):
        y.writerow(["" if b.get(k) is None else b.get(k) for k in kolonlar])
    return tampon.getvalue()


def cekim(semboller: list[str], hedef_n: int, bekleme_sn: float, baslangic: str, bugun: str,
          kolonlar: list[str], bars_dizin: pathlib.Path, damga: str,
          mevcut_atla: bool) -> tuple[dict, dict]:
    """(sembol → manifest kaydı, soğuma özeti). İsim BAŞINA tek çağrı: hem hız-sınırı aralığı hem
    de sembol BAŞINA hata ayrımı ancak böyle mümkün (toplu çağrıda bir patlama tüm kümeyi
    ölçülemez yapardı)."""
    if hedef_n == 0 or not semboller:
        return {}, ortak.soguma_bos_ozet(
            "çekim çağrılmadı (--alpaca 0 ya da hedef sembol kalmadı) — "
            "meridian.adapters.alpaca İTHAL BİLE EDİLMEDİ")
    from meridian.adapters import alpaca as _alp      # TEMBEL: kuru koşumda hiç ithal edilmez
    yuzey = ortak.soguma_yuzeyi(_alp)
    hedef = semboller if hedef_n < 0 else semboller[:hedef_n]
    out: dict = {}
    sifirlama_n, ardisik_olculemeyen, sifirlama_durdu = 0, 0, False
    for i, s in enumerate(hedef):
        kayit = _bos_kayit(s)
        anahtar = kayit["alpaca_anahtar"]
        hedef_csv = bars_dizin / f"{ortak.bar_dosya_adi(s)}.csv"
        if mevcut_atla and hedef_csv.exists():
            kayit.update({"dosya": hedef_csv.name, "durum": "atlandi_mevcut",
                          "sha256": ortak.sha256(hedef_csv),
                          "satir_n": _satir_say(hedef_csv),
                          "neden": "bar dosyası ZATEN VAR — yeniden ÇEKİLMEDİ (PIT girdisi "
                                   "donuk; yeniden çekmek için --yeniden-cek)"})
            out[s] = kayit
            continue
        if i and bekleme_sn > 0:
            time.sleep(bekleme_sn)      # hız-sınırı ARALIĞI; tur sayısı isim sayısıyla sınırlı
        if yuzey["olculdu"]:
            if ardisik_olculemeyen < ortak.ARDISIK_OLCULEMEYEN_UST_SINIRI:
                sifirlama_n += 1 if ortak.soguma_sifirla(yuzey) else 0
            else:
                sifirlama_durdu = True
            soguk_once = bool(yuzey["oku"](yuzey["anahtar"]))
        else:
            soguk_once = None
        hata, cevap = None, None
        try:
            cevap = _alp.daily_bars([anahtar], start=baslangic, end=bugun)
        except Exception as e:  # sessiz-yutma DEĞİL: hata sınıfı+metni kayda düşer, sayı UYDURULMAZ
            hata = f"{type(e).__name__}: {e}"[:200]
        soguk_sonra = bool(yuzey["oku"](yuzey["anahtar"])) if yuzey["olculdu"] else None
        kayit.update({"soguma_aktif": soguk_once,
                      "soguma_yazildi": (bool(soguk_sonra) and not soguk_once)
                                        if yuzey["olculdu"] else None,
                      "soguma_olculemedi_neden": yuzey["neden"]})
        if hata is not None:
            kayit.update({"durum": "olculemedi", "hata": hata,
                          "neden": "Alpaca çağrısı hata verdi — bar ÇEKİLEMEDİ (yokluk KANITI "
                                   "değil)"})
            out[s] = kayit
            ardisik_olculemeyen += 1
            continue
        if cevap is None:
            kayit.update({"durum": "olculemedi",
                          "neden": ("veri ucu SOĞUMADA — istek ATILMADI (süreç-içi soğuma "
                                    "penceresi açık, sıfırlama üst sınırda durdu); ÇEKİLEMEDİ, "
                                    "'veri yok' DEĞİL")
                          if soguk_once else
                          ("daily_bars None döndü (istek atılamadı/patladı) — ÇEKİLEMEDİ; "
                           "'soruldu, satır yok' ile aynı şey DEĞİL")})
            out[s] = kayit
            ardisik_olculemeyen += 1
            continue
        barlar = [b for b in (cevap.get(anahtar) or []) if ortak.bar_tarihi(b)]
        tarihler = sorted(ortak.bar_tarihi(b) for b in barlar)
        kayit.update({"satir_n": len(barlar),
                      "ilk_bar": tarihler[0] if tarihler else None,
                      "son_bar": tarihler[-1] if tarihler else None,
                      "tekrarli_tarih_n": len(tarihler) - len(set(tarihler))})
        if barlar:
            kayit.update(_yaz(hedef_csv, csv_metni(kolonlar, barlar), damga))
        else:
            # BAŞLIK-ONLY DOSYA YAZILMAZ: barsız bir bar dosyası, Parti-2'de "veri var ama boş"
            # gibi okunur ve ölçülmüş sıfırı bir dosya varlığına çevirirdi. Sıfır MANİFESTTE yazılı.
            kayit.update({"durum": "bos",
                          "neden": "Alpaca cevabı bu sembol için satır taşımıyor (SORULDU — "
                                   "ölçülmüş sıfır, bilinmiyor DEĞİL); DOSYA YAZILMADI"})
        out[s] = kayit
        ardisik_olculemeyen = 0
    return out, {"yuzey_olculdu": yuzey["olculdu"], "anahtar": yuzey["anahtar"],
                 "sifirlama_n": sifirlama_n,
                 "ust_sinir": ortak.ARDISIK_OLCULEMEYEN_UST_SINIRI,
                 "sifirlama_durdu": sifirlama_durdu, "neden": yuzey["neden"],
                 "gerekce": "soğuma SÜREÇ-İÇİdir (canlı worker AYRI süreç, etkilenmez); çekim "
                            "her çağrıdan önce ölçer ve sıfırlar ki tek sembolün arızası tüm "
                            "kümeyi ölçülemez yapmasın. Sıfırlama üst sınırda DURUR."}


def _satir_say(yol: pathlib.Path):
    """Var olan bir bar csv'sinin VERİ satırı sayısı; okunamazsa None + (çağıran nedenini yazar)."""
    try:
        with open(yol, encoding="utf-8") as f:
            return max(sum(1 for _ in f) - 1, 0)
    except OSError:
        # sessiz-yutma DEĞİL: dosya okunamadı — sayı UYDURULMAZ, None döner ve kayıtta öyle görünür
        return None


def _yaz(hedef: pathlib.Path, icerik: str, damga: str) -> dict:
    """Bar csv'sini yazar — ÜZERİNE YAZMADAN. Dönen sözlük manifest kaydına birleştirilir.

    ÜÇ HÂL: (1) dosya yok → yazılır; (2) dosya var ve içerik AYNI → yazım YOK ("degismedi");
    (3) dosya var ve içerik FARKLI → `<ad>__<damga>.csv` yan dosyası yazılır, özgün dosya
    DOKUNULMAZ ("yan_dosya"). Üçüncü hâl bir ARIZA DEĞİL bir SİNYALDİR: aynı pencere için uç iki
    farklı seri verdi ve bu, kartın dondurduğu girdinin sessizce değişmesinden ÇOK daha iyidir."""
    yeni_sha = ortak.sha256_metin(icerik)
    if not hedef.exists():
        hedef.parent.mkdir(parents=True, exist_ok=True)
        hedef.write_text(icerik, encoding="utf-8")
        return {"dosya": hedef.name, "sha256": yeni_sha, "durum": "yazildi", "neden": None}
    mevcut_sha = ortak.sha256(hedef)
    if mevcut_sha == yeni_sha:
        return {"dosya": hedef.name, "sha256": mevcut_sha, "durum": "degismedi",
                "neden": "içerik diskteki dosyayla BİREBİR aynı — yazım yapılmadı"}
    yan = hedef.with_name(f"{hedef.stem}__{damga}{hedef.suffix}")
    yan.write_text(icerik, encoding="utf-8")
    return {"dosya": hedef.name, "sha256": mevcut_sha, "durum": "yan_dosya",
            "yan_dosya": yan.name,
            "neden": f"AYRIŞMA: yeni içerik diskteki dosyadan FARKLI (disk={mevcut_sha[:12]} "
                     f"yeni={yeni_sha[:12]}). Üzerine YAZILMADI — yeni seri yan dosyaya yazıldı; "
                     f"hangisinin geçerli olduğu Rol-1'in hükmüdür."}


def main() -> int:
    try:
        bar_baslangic = dt.date.fromisoformat(ARGV.baslangic)
    except ValueError as e:  # sessiz-yutma DEĞİL: bozuk tarih kullanım hatasıdır, varsayılana DÜŞÜLMEZ
        ortak.kullanim_hatasi(f"--baslangic ISO tarih olmalı ({e})")
    bugun_s = ARGV.bugun or dt.datetime.now(dt.timezone.utc).date().isoformat()
    try:
        bugun = dt.date.fromisoformat(bugun_s)
    except ValueError as e:  # sessiz-yutma DEĞİL: aynı sınıf — sessiz varsayılan yok
        ortak.kullanim_hatasi(f"--bugun ISO tarih olmalı ({e})")

    if ARGV.kohort_baslangic is not None:
        kohort_baslangic_s, kohort_kaynak, kohort_neden = ARGV.kohort_baslangic, "--kohort-baslangic", None
    else:
        kohort_baslangic_s, kohort_neden = ortak.kart_pencere_baslangici(KART)
        kohort_kaynak = f"karttan türetildi: {KART} `veri_penceresi`"
        if kohort_baslangic_s is None:
            ortak.kullanim_hatasi(
                f"kohort penceresinin başı karttan okunamadı ({kohort_neden}) — sessiz varsayılan "
                f"YOK; `--kohort-baslangic <YYYY-AA-GG>` ile açık verin")
    try:
        kohort_baslangic = dt.date.fromisoformat(kohort_baslangic_s)
    except ValueError as e:  # sessiz-yutma DEĞİL: kart/bayrak tarihi bozuksa koşum durur
        ortak.kullanim_hatasi(f"kohort penceresi başı ISO tarih olmalı ({e}): {kohort_baslangic_s!r}")
    if bugun < kohort_baslangic:
        ortak.kullanim_hatasi(f"--bugun ({bugun}) kohort penceresinin başından "
                              f"({kohort_baslangic}) önce olamaz")
    if bar_baslangic > kohort_baslangic:
        ortak.kullanim_hatasi(
            f"--baslangic ({bar_baslangic}) kohort penceresinin başından ({kohort_baslangic}) "
            f"SONRA olamaz: özellik ısınması pencerenin ÖNÜNDE olmalı, yoksa ölçümün ilk ayları "
            f"sessizce yarım özellikle koşar")

    satirlar = ortak.kohort_oku(KOHORT)
    etkin, capa_var = ortak.pencere_satirlari(satirlar, kohort_baslangic, bugun)
    if not etkin:
        ortak.kullanim_hatasi(f"pencerede ({kohort_baslangic} → {bugun}) as-of satırı yok: {KOHORT}")
    cikis = ortak.isim_kumesi_ve_cikislar(etkin)
    isimler = sorted(cikis)

    kohort_sha = ortak.sha256(KOHORT)
    kolonlar, kolon_kaynak, kolon_neden = ortak.bar_kolonlari(REPO)
    damga = ortak.damga_uret()
    bars_dizin = CIKTI_DIZIN / "bars"

    onceki, onceki_damga = None, None
    if ARGV.yalniz_eksik is not None:
        onceki, onceki_damga, neden = ortak.onceki_manifest_oku(ARGV.yalniz_eksik)
        if onceki is None:
            ortak.kullanim_hatasi(neden)
        onceki_sha = _onceki_kohort_sha(ARGV.yalniz_eksik)
        if onceki_sha != kohort_sha:
            ortak.kullanim_hatasi(
                "önceki manifestin kohort_csv_sha256'sı bu koşumunkiyle EŞİT DEĞİL — iki farklı "
                f"evren tek manifestte karışırdı. önceki={onceki_sha} şimdi={kohort_sha} "
                f"dosya={ARGV.yalniz_eksik}")
        hedef_isimler = [s for s in isimler
                         if (onceki.get(s) or {}).get("durum") in EKSIK_DURUMLAR
                         or s not in onceki]
    else:
        hedef_isimler = isimler

    kayitlar, soguma_ozeti = cekim(hedef_isimler, int(ARGV.alpaca or 0), float(ARGV.bekleme_sn),
                                   bar_baslangic.isoformat(), bugun.isoformat(), kolonlar,
                                   bars_dizin, damga, not ARGV.yeniden_cek)

    tum: list[dict] = []
    devralinan = 0
    for s in isimler:
        k = kayitlar.get(s)
        if k is None and onceki and s in onceki:
            k = {a: (onceki[s] or {}).get(a) for a in KAYIT_ALANLARI}
            k["sembol"] = s
            devralinan += 1
        elif k is None:
            k = _bos_kayit(s)
            k.update({"durum": "cagrilmadi",
                      "neden": "çekilmedi — bu isim için çağrı yapılmadı (--alpaca / --yalniz-eksik)"})
        k["cikis_gunu"] = cikis[s]
        tum.append(k)

    durumlar: dict[str, int] = {}
    for k in tum:
        durumlar[str(k.get("durum"))] = durumlar.get(str(k.get("durum")), 0) + 1
    yazilan = [k for k in tum if k.get("durum") in ("yazildi", "degismedi", "atlandi_mevcut")]
    ozet = {
        "isim_n": len(isimler),
        "cikan_isim_n": sum(1 for g in cikis.values() if g),
        "hedef_n": len(hedef_isimler),
        "cagrildi_mi": int(ARGV.alpaca or 0) != 0,
        "yazilan_n": sum(1 for k in tum if k.get("durum") == "yazildi"),
        "degismedi_n": sum(1 for k in tum if k.get("durum") == "degismedi"),
        "atlandi_mevcut_n": sum(1 for k in tum if k.get("durum") == "atlandi_mevcut"),
        "yan_dosya_n": sum(1 for k in tum if k.get("durum") == "yan_dosya"),
        "bos_n": sum(1 for k in tum if k.get("durum") == "bos"),
        "eksik_n": sum(1 for k in tum if k.get("durum") in EKSIK_DURUMLAR),
        "hatali_n": sum(1 for k in tum if k.get("hata")),
        "dosyali_n": len(yazilan),
        "bar_toplam": sum(int(k["satir_n"]) for k in tum if isinstance(k.get("satir_n"), int)),
        "barsiz_ama_sorulmus_n": sum(1 for k in tum if k.get("satir_n") == 0),
        "durum_dagilimi": durumlar,
        "oncekinden_devralinan_n": devralinan,
        "soguma": soguma_ozeti,
    }

    rapor = {
        "kart": "EDG-2026-093",
        "asama": "ANA ÖLÇÜM Parti-1 — BAR VERİSİ KURULUMU (ölçüm DEĞİL, veri)",
        "hukum": "YOK — Rol-1",
        "okuyan": "(1) Rol-1: kapsama/eksik listesi ve yeniden çekim kararı; (2) Parti-2 ölçüm "
                  "boru hattı: bars/ dizinini --bars-dir olarak alır ve bu manifestten hangi "
                  "sembolün gerçekten dosyası olduğunu öğrenir (Yasa 6 beyanı).",
        "yazim_beyani": "YAZILAN HER ŞEY --cikti altındadır: bars/<ad>.csv ve bu manifest. "
                        "repo/state'e yazım YOK; kohort csv ve kart SALT-OKUNUR açıldı; "
                        "meridian.obs İTHAL EDİLMEDİ.",
        "damga_utc": damga,
        "uretici": "research/olcumler/edg093_midcap_pit/veri_bar.py",
        "girdi": {
            "repo": str(REPO),
            "kohort_csv": str(KOHORT),
            "kohort_csv_sha256": kohort_sha,
            "kohort_satir_n": len(satirlar),
            "kart_yaml": str(KART),
            "kart_sha256": ortak.sha256(KART) if KART.exists() else None,
            "kart_sha256_neden": None if KART.exists() else f"kart bu ağaçta yok: {KART}",
            "ortak_py": str(pathlib.Path(ortak.__file__).resolve()),
            "ortak_py_sha256": ortak.sha256(pathlib.Path(ortak.__file__).resolve()),
            "onceki_manifest": str(ARGV.yalniz_eksik) if ARGV.yalniz_eksik else None,
            "onceki_manifest_damga": onceki_damga,
        },
        "pencere": {
            "kohort_baslangic": kohort_baslangic.isoformat(),
            "kohort_baslangic_kaynak": kohort_kaynak,
            "kohort_baslangic_neden": kohort_neden,
            "bar_baslangic": bar_baslangic.isoformat(),
            "bugun": bugun.isoformat(),
            "etkin_as_of_satir_n": len(etkin),
            "pencere_oncesi_capa_satiri_var_mi": capa_var,
            "isinma_notu": "bar penceresi kohort penceresinden ÖNCE başlar: 21g medyan hacim / "
                           "rvol20 / momentum kohort penceresinin İLK gününde de tanımlı olsun "
                           "diye (ısınma günü sayısı aşağıda ölçülü değil — takvim günüdür, "
                           "seans sayısı bar dosyalarından Parti-2'de ölçülür).",
        },
        "sozlesmeler": {
            "bar_csv_kolonlari": kolonlar,
            "bar_csv_kolonlari_kaynak": kolon_kaynak,
            "bar_csv_kolonlari_neden": kolon_neden,
            "bar_dosya_adi_kurali": "ortak.py `bar_dosya_adi` — Alpaca anahtarı küçültülür ve "
                                    "nokta TİREYE çevrilir (canlı arşivin `_cache_path` kuralı); "
                                    "MOG-A → MOG.A → mog-a.csv.",
            "uzerine_yazma": "YOK. Var olan dosya varsayılan olarak yeniden ÇEKİLMEZ; "
                             "--yeniden-cek ile çekilirse içerik sha ile kıyaslanır ve fark "
                             "varsa YAN DOSYA (<ad>__<damga>.csv) yazılır. PIT girdisi donuktur.",
            "alpaca_cagri_bicimi": "alpaca.daily_bars([sembol], start=%s, end=%s) — isim BAŞINA "
                                   "tek çağrı. timeframe=1Day · feed=iex · adjustment=split · "
                                   "sort=asc çağrının KENDİ içindedir (ölçüldü), çağıran geçmez. "
                                   "Dönen yapı {TICKER: [bar,…]}; bar tarih alanı 'date'."
                                   % (bar_baslangic.isoformat(), bugun.isoformat()),
            "sembol_normalizasyonu": {
                "uygulanan": "upper().strip() + sınıf-hisse tire→nokta dönüşümü",
                "sembol_bicimi_kaynagi": ortak.SEMBOL_BICIMI_KAYNAGI,
                "sinif_hisse_donusumu": {s: ortak.alpaca_anahtari(s) for s in isimler
                                         if ortak.alpaca_anahtari(s) != s},
            },
            "temizlik_beyani": "BU BETİK BARI TEMİZLEMEZ: takvim kapısı, hayalet seans düşürme, "
                               "bölünme-düzeltilmemiş satır karantinası ve bütünlük dışlaması "
                               "canlı boru hattının KENDİ fonksiyonlarındadır ve Parti-2 onları "
                               "çağırır. Burada ikinci bir uygulama yazmak aynı yasanın iki "
                               "kopyasını doğururdu (tek-kaynak yasası).",
            "bekleme": {"bekleme_sn": float(ARGV.bekleme_sn),
                        "not": "isimler ARASI hız-sınırı aralığı; yoklama döngüsü DEĞİL "
                               "(beklenen bir koşul yok, tur sayısı isim sayısıyla sınırlı)"},
        },
        "kayitlar": tum,
        "ozet": ozet,
    }

    hedef = ortak.manifest_yaz(CIKTI_DIZIN, f"bars_manifest_{damga}.json", rapor)
    print(f"YAZILDI: {hedef}")
    print(f"isim_n={ozet['isim_n']} hedef={ozet['hedef_n']} yazılan={ozet['yazilan_n']} "
          f"atlanan={ozet['atlandi_mevcut_n']} eksik={ozet['eksik_n']} hatalı={ozet['hatali_n']} "
          f"yan_dosya={ozet['yan_dosya_n']} bar_toplam={ozet['bar_toplam']}")
    print("HÜKÜM YOK — bu bir VERİ kurulumudur; hüküm Rol-1'in (karta + K defterine).")
    return 0


def _onceki_kohort_sha(yol: pathlib.Path):
    """Önceki manifestin kohort sha'sı; okunamazsa None (çağıran kapıyı kapatır)."""
    try:
        ham = json.loads(pathlib.Path(yol).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        # sessiz-yutma DEĞİL: dosya zaten `onceki_manifest_oku` ile okunmuş ve orada nedeni
        # yazılmıştı; burada None dönmek sha kapısını KAPATIR (eşitsizlik → koşum durur)
        return None
    return (ham.get("girdi") or {}).get("kohort_csv_sha256")


raise SystemExit(main())
