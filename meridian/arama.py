"""EDG-067 taban indeksinin PANO OKUYUCUSU — ince alt-süreç sarmalayıcısı (TSK-167 dilim-2).

NE OLDUĞU. Dilim-1'de A1'e kurulan arama CLI'ı (`research/olcumler/edg067_hindsight_faz1/
hafiza_ara.py` → `deploy/hindsight/hafiza_ara.sh`) bugün yalnız kabuktan koşuyor. Bu modül onu
panoya BİR OKUYUCU olarak bağlar: argümanları kelepçeler, çıktıyı süzer, kırpar ve şeklini
`GET /api/arama`ın döndürdüğü zarfa çevirir. İNDEKSİ KURMAZ, TAZELEMEZ, YAZMAZ — indeks haftalık
bir A1 timer'ının ürünüdür ve buradan görünmez.

NE VAAT ETMEZ (CLI başlığındaki okuma talimatının aynısı). Ölçülen taban: dosya-isabet@3 %55,6 ·
bölüm-isabet@3 %27,8 (n=36, EDG-067 hükmü 2026-09-06). Yani çıktı bir CEVAP değil bir ADAY
LİSTESİdir. Eşik yoktur, sıralama saf mesafedir: boş liste "hafızada bu yok" DEMEK DEĞİLDİR.

SALT OKUMA — VE TEK YAZAN YÜZEY BU MODÜLDE DEĞİL. `ara` hiçbir `state/` dosyasına yazmaz; arıza
bilgisi bile `neden` alanıyla ÇAĞIRANA taşınır ve olay künyesini uç yazar (`api.api_arama`).
İkinci bir yazan yüzey açmamak bilinçlidir: bu modülün Yasa 6 sözleşmesi "yazmaz"dır ve o cümle
çivilidir; burada bir `obs.warn` bile o cümleyi "çoğunlukla yazmaz"a çevirirdi.

SIR DIŞLAMA İKİ KATMANLIDIR. (a) YAPISAL: korpus `manifest_uret.py`nin git-HEAD beyaz listesidir
(günlük · ROADMAP §7 kesiti · kartlar · docs), `state/secrets.json` ve `.env` versiyonlanmadığı
için indekse GİREMEZ. (b) SAVUNMA DERİNLİĞİ: dönen her satırın yolu `KORPUS_ONEKLERI` ile süzülür
— küme dışı satır DÜŞÜRÜLÜR ve sayısı `korpus_disi_n` ile BEYAN EDİLİR (sessizce yutulmaz);
ayrıca giden her dizge `notify.scrub`tan geçer.

KOTA YOK, AMA BEDEL SIFIR DEĞİL. Bu yüzey hiçbir model çağırmaz (LLM kotasına dokunmaz), o yüzden
bir çağrı sayacı TUTULMAZ. Ama her sorgu A1'in 4 OCPU'sunda yeni bir ONNX oturumu açar; karşılığı
bir sayaç değil bir KİLİTtir (`_ARAMA_KILIDI`): aynı anda tek arama, ikinci istek süreç DOĞURMADAN
`mesgul` döner. Gün içi çağrı sayısı olay defterinden SAYILIR — ikinci bir sayaç dosyası
tek-kaynak yasasını kırardı.
"""
from __future__ import annotations

import json
import os
import subprocess
import threading
import time

from . import config, notify

#: Betik yolunun ORTAM DEĞİŞKENİ. Ad `SOHBET_HAFIZA_ARA` olarak KORUNUR: yol çözümü buraya
#: devredildiğinde (K2, 2026-09-08) `sohbet._hafiza_betigi` bu fonksiyona bağlandı ve o yüzeyin
#: çivisi (v440) bu adı monkeypatch'liyor — adı değiştirmek o çiviyi sessizce körleştirirdi.
BETIK_ENV = "SOHBET_HAFIZA_ARA"

#: İNDEKSE GİREN KORPUSUN ÖNEKLERİ — `manifest_uret.py`nin git-HEAD beyaz listesinin bu yüzeydeki
#: karşılığı. `ROADMAP.md%237` bir KESİT kimliğidir (ROADMAP §7 bölümü), dosya adı değil; ham
#: `ROADMAP.md` indekste YOKTUR ve önek olarak da kabul edilmez. Çivi: manifest kaynağıyla
#: ayrışma ölçülür.
KORPUS_ONEKLERI: tuple[str, ...] = ("docs/", "research/cards/",
                                    "MERIDIAN_ENGINEERING_LOG.md", "ROADMAP.md%237")

#: `k` üst sınırı — sohbet aracıyla ORTAK sayı (K6 hükmü, 2026-09-08). Pano kutusu 5/10 sunar;
#: tavan burada durur ki uç, kutunun dışından gelen bir `k=999` ile A1'i sıralamaya boğmasın.
K_TAVANI = 20
K_VARSAYILAN = 5

#: Satır başına dönen metin kesitinin tavanı (karakter). SEÇİLDİ, ÖLÇÜLMEDİ (K4 hükmü): CLI'ın
#: `--json` kolu chunk'ı KESMEDEN verir (pencere 1500 karakter) ve 20 satırlık bir yanıtta bu 30
#: KB'lık bir gövde demekti. Kırpma GÖRÜNÜRDÜR — her satır `kesit_kirpildi` + `metin_uzunluk`
#: taşır (bedel yasası: ne kaybettiğini de ölç).
ARAMA_KESIT_TAVANI = 600

#: Alt sürecin süre tavanı (saniye). SEÇİLDİ, ÖLÇÜLMEDİ (K4): sohbet aracının 180'i etkileşimli
#: bir pano kutusu için fazla, ve SOĞUK AÇILIŞ HİÇ ÖLÇÜLMEDİ (her istek yeni bir ONNX oturumu
#: kurar; ölçülen p50 616 ms SICAK süreçtendir). İlk gerçek A1 sorgusundan sonra ölçülmüş değerle
#: DEĞİŞTİRİLİR — o adım planın Görev 3'üdür.
ARAMA_ZAMAN_ASIMI_S = 60

#: CLI'ın SIFIR OLMAYAN çıkış kodlarının reçeteleri. TEK KAYNAK CLI BAŞLIĞIDIR ("ÇIKIŞ KODU
#: SÖZLEŞMESİ" bloğu); burası ÜÇÜNCÜ kopyadır (ikincisi sarmalayıcı kabuğun şerhi) ve kaçınılmaz:
#: pano operatörü stderr'i görmez, gördüğü tek şey `neden` metnidir ve "yolu düzelt" ile "indeksi
#: modelle yeniden kur" AYRI reçetelerdir. Ayrışma çivilidir — kod kümesi CLI başlığından TÜRETİLİP
#: bu sözlükle karşılaştırılır (kardeş çivi v446 CLI ile kabuğu birlikte ölçer).
RC_NEDENLERI: dict[int, str] = {
    1: "girdi/uzantı arızası — betiğin yolunu ve sqlite-vec kurulumunu doğrula",
    2: "kullanım hatası — argüman sözleşmesi tutmadı",
    3: "model/şema ayrışması — indeksi modelle YENİDEN kur",
}

#: Kilit başkasındayken dönen `neden` (tek kaynak: uç, pano ve çivi hep bunu okur).
MESGUL_NEDENI = ("meşgul — başka bir arama koşuyor. O bitince tekrar sor: alt süreç "
                 "BAŞLATILMADI, indeks okunmadı.")

#: CLI'ın `--json` kolunda künyeyi STDERR'e bastığı satırın öneki (stdout o zaman SAF JSON'dur).
KUNYE_ONEKI = "# indeks: "

#: Künye satırının alan ayıracı — CLI'ın tablo ayıracıyla aynı dizi.
KUNYE_AYIRACI = " · "

#: AYNI ANDA TEK ARAMA. Kilit PARK ETMEZ (`acquire(blocking=False)`) — sohbet kilidinin ölçülmüş
#: gerekçesi birebir geçerli: uç gövdeyi `run_in_threadpool`e verir, bekleyen her istek paylaşılan
#: anyio havuzundan bir jeton tutar ve yığılma `api.py`deki senkron rotaları susturur.
#: BEDEL BEYANI (bedel yasası): KAZANILAN — A1'de aynı anda iki ONNX oturumu açılmaz (4 OCPU'da
#: ikinci oturum birinciyi de yavaşlatırdı) ve cevap ANINDA döner. KAYBEDİLEN — ikinci sorgu
#: sıraya GİRMEZ, REDDEDİLİR: operatör onu elle tekrarlar (`MESGUL_NEDENI` bunu adıyla söyler).
_ARAMA_KILIDI = threading.Lock()


def betik_yolu() -> str:
    """Arama sarmalayıcısının yolu (`SOHBET_HAFIZA_ARA`, varsayılan depo kurulumu).

    TEK ÇÖZÜCÜ (K2 hükmü): `sohbet._hafiza_betigi` buraya DEVREDİLDİ. İki çözücü, env adı ya da
    varsayılan yol değiştiği gün sessizce ayrışırdı — sohbet aracı bir betiği, pano ucu başkasını
    koşardı ve ikisi de "çalışıyor" derdi."""
    return (os.environ.get(BETIK_ENV)
            or str(config.ROOT / "deploy" / "hindsight" / "hafiza_ara.sh"))


def k_kelepcele(ham) -> int:
    """İstemciden gelen `k`yı 1..`K_TAVANI` aralığına çeker.

    AYRIŞTIRILAMAYAN DEĞER SESSİZCE VARSAYILANA OTURMAZ, `ValueError` FIRLATIR: kardeş hafıza
    uçlarında bozuk sayı beyanlı bir varsayılana düşer çünkü orada parametre İSTEĞE BAĞLI bir
    sayfalama sınırıdır; burada `k` operatörün SEÇTİĞİ şeydir ve "10 istedim, 5 geldi" sessiz bir
    yalan olurdu. Uç bunu 400'e çevirir."""
    return max(1, min(int(str(ham).strip()), K_TAVANI))


def dosya_onegi_gecerli(onek: str) -> bool:
    """`--dosya` süzgeci korpusun İÇİNDE mi? (Beyaz liste `KORPUS_ONEKLERI`.)

    `..` ve mutlak yol AYRICA reddedilir: `docs/../state/` öneki beyaz listeyi geçer ama korpusun
    dışına işaret eder. Süzgeç istemci tarafındadır (CLI'ın vec0 sorgusu yola göre daraltamaz),
    yani buradan geçen her önek A1'de bir dizge karşılaştırmasıdır — dizin gezintisi yüzeyi
    DOĞMAZ, ama beyaz listenin kendisi de o varsayıma yaslanmaz."""
    onek = str(onek)
    if not onek or ".." in onek or onek.startswith("/"):
        return False
    return onek.startswith(KORPUS_ONEKLERI)


def kunye_coz(stderr) -> dict | None:
    """CLI'ın stderr'e bastığı indeks künyesi → sözlük. Satır yoksa `None`.

    BOŞ SÖZLÜK DÖNMEZ: "künye okunamadı" ile "künye boş" aynı şey değildir ve pano ikisini ayrı
    çizer. `None` DİZGESİ DE DEĞERE ÇEVRİLMEZ: CLI eksik alanı bilerek `None` basar (uydurma
    yasağı), yani o dizgeyi olduğu gibi taşımak eksikliği bir değere dönüştürürdü."""
    for satir in str(stderr or "").splitlines():
        if not satir.startswith(KUNYE_ONEKI):
            continue
        alanlar: dict = {}
        for parca in satir[len(KUNYE_ONEKI):].split(KUNYE_AYIRACI):
            ad, ayirac, deger = parca.partition("=")
            if not ayirac:
                continue
            deger = deger.strip()
            alanlar[ad.strip()] = None if deger == "None" else deger
        return alanlar or None
    return None


def _zarf(*, sonuclar=None, kunye=None, korpus_disi_n: int = 0, sure_s: float = 0.0,
          mesgul: bool = False, neden: str | None = None) -> dict:
    """Ucun döndürdüğü TEK şekil — her dalda AYNI alanlar.

    `n` SONUÇLARDAN TÜRETİLİR, ayrıca taşınmaz: iki sayı bir gün ayrışırdı. `sonuclar is None`
    dalında `n` de `None`dır — "ölçemedim" ile "0 satır buldum" aynı alandan okunamaz."""
    return {"sonuclar": sonuclar,
            "kunye": kunye,
            "n": (None if sonuclar is None else len(sonuclar)),
            "korpus_disi_n": korpus_disi_n,
            "sure_s": round(float(sure_s), 3),
            "mesgul": mesgul,
            "neden": neden}


def _kos_varsayilan(argv: list[str], zaman_asimi: float):
    """Alt süreci koşar. `shell=False` (varsayılan) ve argümanlar LİSTEdir — soru argv'nin ayrı
    bir öğesi olarak geçer, yani kabuk enjeksiyonu yüzeyi HİÇ DOĞMAZ. Zaman aşımında
    `subprocess.run` çocuğu ÖLDÜRÜR ve `TimeoutExpired` fırlatır."""
    return subprocess.run(argv, capture_output=True, text=True, timeout=zaman_asimi)


def _temiz(deger) -> str:
    """Giden her dizge `notify.scrub`tan geçer — savunma derinliği: yapısal olarak korpusa hiçbir
    sır giremez, ama tek katmanlı bir savunma savunma DEĞİLDİR."""
    return notify.scrub(str(deger if deger is not None else ""))


def _bicimle(satir: dict) -> dict:
    """Bir sonuç satırı → pano satırı. Kırpma GÖRÜNÜRDÜR.

    SCRUB ÖNCE, KIRPMA SONRA: ters sırada, tavana denk gelen bir sır YARIM kalır ve yarım sır
    `scrub` tarafından TANINMAZ — yani kırpma bir sızıntı yolu olurdu. `metin_uzunluk` da
    scrub'lanmış metnin uzunluğudur; iki farklı metni ölçüp tek alanda göstermek "kaç karakter
    kırpıldı" sorusunu bulandırırdı. Değişmez: `kesit_kirpildi` ⟺ `metin_uzunluk` > tavan."""
    metin = _temiz(satir.get("metin"))
    return {"dosya": _temiz(satir.get("dosya")),
            "bolum": _temiz(satir.get("bolum")),
            "mesafe": satir.get("mesafe"),
            "blob_sha": _temiz(satir.get("blob_sha")),
            "kesit": metin[:ARAMA_KESIT_TAVANI],
            "kesit_kirpildi": len(metin) > ARAMA_KESIT_TAVANI,
            "metin_uzunluk": len(metin)}


def _korpus_ici(dosya: str) -> bool:
    return ".." not in dosya and str(dosya).startswith(KORPUS_ONEKLERI)


def _suz(ham: list) -> tuple[list[dict], int]:
    """(korpus içi satırlar, DÜŞÜRÜLEN sayısı). Düşen satır SAYILIR — sessizce yutulmuş bir
    süzgeç, süzgeç olmayan bir süzgeçten ayırt edilemezdi."""
    icerde, disarda = [], 0
    for satir in ham:
        if not isinstance(satir, dict) or not _korpus_ici(str(satir.get("dosya") or "")):
            disarda += 1
            continue
        icerde.append(_bicimle(satir))
    return icerde, disarda


def ara(soru: str, k: int = K_VARSAYILAN, dosya: str | None = None, *,
        kos=None, simdi=None) -> dict:
    """Taban indeksinde bir soru → `_zarf` şekli. Alt süreç ÇAĞRILABİLİR ENJEKTE EDİLİR.

    `kos(argv, zaman_asimi)` çiviler tarafından sahtelenir — bu sayede testler gerçek bir ONNX
    oturumu açmaz (yerelde sqlite-vec zaten yoktur; CLI'ın kendi başlığı "KOŞUM YERİ A1" diyor).
    Varsayılan çözüm ÇAĞRI ANINDA yapılır (`_kos_varsayilan` modül genelinden okunur) ki uçtan
    geçen çiviler de sahteyi yerleştirebilsin.

    `simdi()` SÜRE SAATİDİR (varsayılan `time.monotonic`), damga değil: bu yüzey hiçbir deftere
    satır yazmaz, yani ölçtüğü tek zaman GEÇEN SÜREdir.

    BOŞ SORU `ValueError`: aranacak bir şey yokken A1'de bir ONNX oturumu açmak bedeli olan bir
    hiçliktir. Kilidin hâli bu kararı değiştirmez, o yüzden kapı kilidin DIŞINDADIR (sohbetin
    boş-mesaj kapısıyla aynı gerekçe).

    KELEPÇE TEK YERDE (`k_kelepcele`): uç aynı fonksiyonu ÖNCEDEN çağırır — ama bunun sebebi
    ikinci bir kelepçe değil, sayı olmayan `k`yı alt süreç DOĞMADAN 400'e çevirmektir. İlk yazımda
    burada `max(1, min(...))` ikinci bir kopyaydı ve mutasyon turu onu ÖLÇÜLEMEZ buldu (uçtan
    geçen çivi uçtaki kelepçeyi görüyordu, buradakini değil) — kopya kaldırıldı."""
    soru = str(soru or "").strip()
    if not soru:
        raise ValueError("boş soru — aranacak bir şey yok")
    k = k_kelepcele(k)
    if dosya is not None and dosya != "" and not dosya_onegi_gecerli(dosya):
        raise ValueError(f"korpus dışı dosya öneki: {dosya!r} — "
                         f"beyaz liste: {', '.join(KORPUS_ONEKLERI)}")
    saat = simdi or time.monotonic
    if not _ARAMA_KILIDI.acquire(blocking=False):
        return _zarf(neden=MESGUL_NEDENI, mesgul=True)
    try:
        return _ara_kilitliyken(soru, k, dosya or None, kos or _kos_varsayilan, saat)
    finally:
        _ARAMA_KILIDI.release()


def _ara_kilitliyken(soru: str, k: int, dosya: str | None, kos, saat) -> dict:
    """`ara`nın gövdesi — `_ARAMA_KILIDI` TUTULURKEN koşar (tek çağıran oradadır).

    AYRI FONKSİYON, ÇÜNKÜ KİLİT SÖZLEŞMENİN PARÇASI (sohbetin aynı ayrımı): gövdeyi doğrudan
    çağıran ikinci bir yol açılsaydı serileştirme sessizce kaybolurdu."""
    t0 = saat()
    yol = betik_yolu()
    if not os.path.exists(yol):
        return _zarf(sure_s=saat() - t0,
                     neden=f"ölçülemedi: arama betiği bulunamadı ({yol}) — bu makinede taban "
                           "indeksi kurulu değil; 'kayıt yok' SONUCU DEĞİLDİR")
    argv = [yol, "--json", "-k", str(k)]
    if dosya:
        argv += ["--dosya", dosya]
    argv.append(soru)
    try:
        r = kos(argv, ARAMA_ZAMAN_ASIMI_S)
    except subprocess.TimeoutExpired as e:
        return _zarf(sure_s=saat() - t0,
                     neden=f"ölçülemedi: zaman aşımı "
                           f"({getattr(e, 'timeout', None) or ARAMA_ZAMAN_ASIMI_S:g} s) — "
                           "alt süreç öldürüldü, indeks okunmadı")
    except Exception as e:
        return _zarf(sure_s=saat() - t0,
                     neden=f"ölçülemedi: alt süreç koşamadı ({type(e).__name__}: {e})")
    kunye = kunye_coz(getattr(r, "stderr", ""))
    rc = int(getattr(r, "returncode", 1))
    if rc != 0:
        return _zarf(kunye=kunye, sure_s=saat() - t0,
                     neden=f"ölçülemedi: betik rc={rc} — "
                           f"{RC_NEDENLERI.get(rc, 'bilinmeyen çıkış kodu')}"
                           f"\n{_temiz(getattr(r, 'stderr', ''))[:500]}")
    try:
        ham = json.loads(getattr(r, "stdout", "") or "")
    except (ValueError, TypeError) as e:
        return _zarf(kunye=kunye, sure_s=saat() - t0,
                     neden=f"ölçülemedi: betik çıktısı JSON değil ({type(e).__name__}: {e})")
    if not isinstance(ham, list):
        return _zarf(kunye=kunye, sure_s=saat() - t0,
                     neden=f"ölçülemedi: betik çıktısı liste değil ({type(ham).__name__}) — "
                           "sözleşme `--json` kolunda HAM SONUÇ LİSTESİdir")
    sonuclar, korpus_disi_n = _suz(ham)
    return _zarf(sonuclar=sonuclar, kunye=kunye, korpus_disi_n=korpus_disi_n,
                 sure_s=saat() - t0)
