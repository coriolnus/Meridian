#!/usr/bin/env python3
"""bekci_tarama.py — SÜREGELEN ve DURAN durumların deterministik tespiti. Model YOK, tahmin YOK.

NEDEN VAR (brifingle gelen ÖLÇÜM, A1, 2026-08-30 — bu makinede DOĞRULANAMADI, aşağıya bak).
Son 3 günün 1645 olayının 1580'i `info` seviyesinde. Şu zinciri bulmak ALTI elle ölçüm aldı ve
her halkası saatlik olarak deftere düşüyordu:

    duvar=1 → warmup 40 adayın 0'ını geçiriyor → `taze_hipotez` kalıcı 0
            → sprint yalnız 7 günlük zaman aşımıyla ateşliyor, LİYAKATLE hiç ateşlemiyor

`warmup_merdiven_kilitli.ardisik` canlıda 93'e çıkmış bir sayaçtır ve HİÇBİR KOD ONU OKUMAZ.
Bu, kural yazılamayan sınıftır: bir watchdog kuralı arızayı ÖNCEDEN bilmeyi gerektirir, bu
katmanın işi ise "bu N turdur aynı ve kimse bakmadı" diyebilmektir.

KANIT KÜNYESİ — ÖLÇÜLEN, ÇIKARILAN ve DOĞRULANAMAYAN (denetim bulgusu 9, 2026-08-30).
Bu dosyanın kuralları üç ayrı kaynaktan geldi ve karıştırılmaları yasak:
  · ÖLÇÜLEN (bu makinede, salt okuma): yerel `state/events.jsonl` üzerindeki her sayı —
    kapı kalibrasyonu, `medyan=0` sıklığı, mesaj biçimli olay adlarının çoğalması.
  · ÇIKARILAN (yayımcı KAYNAK KODU okunarak): alan adları ve `sebep` biçimleri
    (`meridian/sprint.py` → `sprint_cadence_skip`, `meridian/hermes.py` →
    `warmup_merdiven_kilitli`). Alanların VAR OLDUĞU kesindir; DEĞERLERİ değil.
  · DOĞRULANAMAYAN: kuralın canlı defterdeki DAVRANIŞI. Yerel defterin son 3 gününde 5 satır
    var ve `sprint_cadence_skip` / `warmup_merdiven_kilitli` / `ardisik` yerelde HİÇ YOK.
    Yani "canlıda şöyle olur" cümlelerinin hepsi ÇIKARIMDIR, gözlem DEĞİL. İlk canlı koşum bir
    DOĞRULAMA turudur, bir teslimat turu değil.

TESPİT NEDEN BURADA, MODELDE DEĞİL. Listeyi model üretirse bir arıza UYDURABİLİR. Ayrım
mimaridir: bu dosya ÖLÇER, model (ayrı bir katman) yalnız SIRALAR. Model düşerse ham liste yine
gider. Bu dosyada ne bir model çağrısı ne bir teslimat kanalı vardır — çivisi de var.

ASIL TUZAK: `sprint_cadence_skip` 3 günde 845 kez düştü ve "alarm" diye raporlanacaktı. `sebep`
ölçülünce 554'ü `saat_dilimi_disinda` (pencere dışı — NORMAL), 95'i `zaten_kosuyor` (NORMAL)
çıktı; yalnız 191 `tetik_yok(gun=N<7, taze=0<5)` kaydı DURUM sinyaliydi. SIKLIK TEK BAŞINA ARIZA
DEĞİLDİR. Ayrım YAPISALDIR (isim listesi çürür): bkz. `_imza` — bir alanın DEĞERİ değil,
ZAMAN İÇİNDEKİ ŞEKLİ hüküm verir.

KİMLİK ≠ DEĞER (denetim bulgusu 1). Kalem adı bir KİMLİKTİR ve gün geçtikçe değişmemelidir;
ölçüm DEĞERDİR ve değişebilir. Canlı `sebep` ikisini tek dizede taşıyor:
`tetik_yok(gun=4<7, taze=0<5)`. `gun` her arttığında ad değişir ve AYNI takılı durum her gün
sıfırdan bildirilirdi — Global Constraint'in ("aynı takılı durumu her gün tekrar etme") tam
ihlali. `_kalip` ölçülen değeri addan çıkarır (`gun=<N><7`), ham dize kanıta gider. Eşik (`<7`)
KORUNUR, çünkü eşiğin değişmesi GERÇEKTEN başka bir durumdur.

BU ARAÇ YAZMAZ. Kuru koşum onun TEK kipidir; `--uygula` gibi bir bayrak BİLEREK yoktur.
Yalnız `state/events.jsonl` OKUNUR. Söz artık MEKANİK: `test_TESPIT_KATMANI_HICBIR_BAYT_YAZMAZ`
yazma kipli `open`, `obs.`/`store.`, `meridian` ithali ve dosya sistemi çağrılarını tarar
(okuma serbest). Sözün çivisiz kaldığı sürümde bu oturumda ÜÇ AJAN canlı yerel deftere yazdı.
KAPSAMI TAM DEĞİL, BEYAN EDİLİR: desen TEK SATIRLIK çağrıya hapsedilmiştir, yani çok satıra
yayılmış `open(`, DEĞİŞKEN kipli `open(p, kip)` ve `os.open(p, os.O_WRONLY)` KAÇAR. Üç kaçak da
çiviyle ölçülüdür (biri kapanırsa çivi kırmızı olur ve bu cümle güncellenmek zorunda kalır).
Ölçülen gerçek olay sınıfı (`obs.log` eklenmesi) `obs.` koluyla zaten kapalıdır.

DAL DENETİMİ DÜZELTME DALGASI (2026-08-30) — üç kural bu turda değişti, üçü de ÖLÇÜMLE:
  · HÜKÜM KENDİ AÇIKLIĞININ KANITINA BAĞLIDIR. `_sifirlanan_alanlar` en geniş (60 gün)
    pencerede koşup 3 günlük TAKILI hükmünü bağlıyordu; haftalık tabanla sıfırlanan
    `sprint_cadence_skip.gecen_gun` bu yüzden hiç KERTİK olamıyor ve dalın var oluş gerekçesi
    olan grup `oynak` diye eleniyordu. Artık kanıt hükmün penceresinden toplanır.
  · HÜKÜM KURULAMADI = TOPLU KALEM — AMA GEÇMİŞİ OLAN KALEM TOPLANMAZ. Gerçek yerel defterde
    üretim açıklığında ölçüldü: `0 TAKILI · 1 DURAN · 73 ÖLÇÜLEMEDİ`, 73/73 `kadans_olculemedi`;
    kararlı durumda her gün ~10-16 arıza-olmayan satır. İlke KORUNDU (ölçülemeyen iyi huylu bir
    sıfır değildir, model onu susturamaz), TESLİMAT BİÇİMİ değişti: neden başına TEK kalem, tekil
    hüküm `olculemedi_ayrinti`de. İKİNCİ DALGA BUNUN BEDELİNİ ÖLÇTÜ ve düzeltti: ilk toplama,
    DURAN'dan göçen durmuş işleri de yığına katıyor ve onları KALICI OLARAK görünmez kılıyordu
    (20 günde göç eden 7 olayın 7'si bir daha anılmadı). Artık daha önce ADIYLA bildirilmiş
    kalem yığına girmez — bkz. `_hukumsuzleri_topla`nın `bilinen` parametresi.
  · MANDALIN DEĞERİ KİMLİĞE GİRMEZ. Pencere içinde kıpırdamış bir alan durağanlığın kanıtı
    olamaz; ölçüldü ki 3 günde bir dönen iyi huylu bir bayrak kalemi 21 günde 8 kez andırıyordu.

ARAÇ TAMLIK İDDİA ETMEZ (`ops/olcum.py` fix round 4 dersi). Her cevabın yanında kendi kapsamını
BEYAN EDER ve elediği grupları ADIYLA sayar — görünmeyen bir eleme denetlenemez.

NOT (`ops/olcum.py` ile aynı gerekçe): `from __future__ import annotations` BİLEREK yok; bu
betik testlerde `sys.modules`e kayıt olmadan yükleniyor ve ertelenmiş tip ipuçları o yükleme
biçiminde dataclass iç kodunu düşürüyor.
"""

import argparse
import dataclasses
import datetime as dt
import json
import pathlib
import re
import statistics
import sys

KOK = pathlib.Path(__file__).resolve().parent.parent

# Varsayılan defter yolu SAF `pathlib` ile kurulur — uygulama paketinden BİLEREK import yok:
# bu katman ölçüm yaparken üretim modüllerini yan etkileriyle birlikte yüklememelidir.
VARSAYILAN_DEFTER = KOK / "state" / "events.jsonl"

# ZARF ALANLARI — kaydın YÜKÜ değil, taşıyıcısı. `level` BİLEREK dışarıda: seviye yayımcının
# ŞİDDET HÜKMÜDÜR, ölçülen durumun kendisi değil; `info`dan `warn`a yükselen satır aynı arızanın
# daha yüksek sesle söylenmesidir. Görülen seviyeler kanıtta raporlanır.
ZARF_ALANLARI = frozenset({"ts", "event", "level", "sebep"})

# Yayımcının KENDİ kesintisizlik hükmünü taşıyan sayaç. Bugün canlıda yalnız
# `warmup_merdiven_kilitli` taşıyor, ama tespit ALAN VARLIĞINA bakar, olay ADINA değil.
SAYAC_ALANI = "ardisik"

# ZAMANI ÇÖZÜLEMEYEN KUSURLAR — PENCEREYE BAĞLANAMAZ (ikinci dalga, 2026-08-30).
# "Hüküm kendi açıklığının kanıtına bağlıdır" ilkesinin İKİNCİ örneği: `_oku` kusurları pencere
# süzgecinden ÖNCE kaydediyordu, yani DOSYANIN TAMAMINDAN. 2024 tarihli bozuk bir satır, 3 ve 60
# günlük pencerelerin İKİSİNİN DE dışındayken kalem olarak raporlanıyor, aynı mesajın kapsam
# satırı ise "bu pencerenin DIŞI görülmedi" diyordu. Kusur `kusur:` ailesindedir, yani bilerek
# toplanmaz ve 168 saatte bir yeniden anılır — tek bir eski bozuk bayt, sonsuza dek haftalık bir
# satır demekti.
# ONARIM DÜRÜST OLMAK ZORUNDA: bazı kusurların zamanı TANIMI GEREĞİ çözülemez (bozuk bayt,
# ayrıştırılamayan satır, damgası olmayan/çözülemeyen satır). Onları ATMAK, ölçülemeyeni sıfır
# saymak olurdu. Bu yüzden kural İKİYE ayrılır: zamanı ÇÖZÜLEBİLEN kusur pencereye BAĞLANIR,
# çözülemeyen kusur raporlanır ama DOSYA GENELİ olduğunu ADIYLA söyler (kalemde ve kapsamda).
PENCEREYE_BAGLANAMAYAN_KUSURLAR = frozenset({
    "bozuk_bayt", "ayristirilamayan_satir", "zaman_damgasi_yok",
    "zaman_damgasi_ayristirilamadi"})

# ---- EŞİKLER: BEYAN EDİLMİŞ, ÖLÇÜLMÜŞ DEĞİL ----------------------------------------------------
# CLAUDE.md madde 3: eşik sonradan değişmez. Hiçbiri canlı deftere BAKILARAK ayarlanmadı (yerel
# kopya bayat; canlıya karşı ayarlamak ölçümü ölçülene uydurmak olurdu). `tara()` hepsini
# sonuçla birlikte döner ki okuyucu hükmü kendi eşiğiyle yeniden kurabilsin.
TAKILI_MIN_TEKRAR = 5       # 5'ten az özdeş kayıtta "takılı" ile "kısa iyi huylu seri" ayrılamaz
TAKILI_MIN_SURE_SAAT = 1.0  # konu SÜREGELEN durumdur; saniyelik yeniden-deneme döngüsü değil
SERBEST_AKAN_ORAN = 0.9     # benzersiz/toplam bu oranı aşan alan SAAT sayılır (bkz. `_imza`)

# DURAN KENDİ PENCERESİNİ KULLANIR (denetim bulgusu 4). İki sınıf AYRI SORU sorar:
# TAKILI "şu an takılı mı" der — yakın pencere doğrudur. DURAN "bir ritim durdu mu" der ve
# ritmi KURMAK için örnek ister. `gun=3` varsayılanında `DURAN_MIN_ORNEK=5`, kadansı ~18
# saatten uzun HER İŞİ yapısal olarak hükümsüz kılıyordu: gecelik yedekleme, günlük özet,
# haftalık bakım — yani bir bekçinin en değerli "durdu" sinyalleri hiç erişilemezdi.
# AÇIKLIK ARİTMETİKLE SEÇİLDİ, yuvarlak sayıyla değil. Bir kadansın DURDUĞUNU söylemek iki şey
# ister: ritmi kuracak kadar örnek (`DURAN_MIN_ORNEK`=5) VE gürültü tabanını aşacak kadar
# sessizlik (`DURAN_KAT`=3 × kadans). Haftalık bir iş için bu 5×7 + 3×7 = 56 gün eder; 45 gün
# örnekleri toplar ama sessizliğe yer bırakmaz (ölçüldü: 45'te haftalık çivi kırmızı kaldı).
# 60 gün: günlük iş rahatça, HAFTALIK iş sınırın üstünde girer. AYLIK iş HÂLÂ ERİŞİLEMEZ
# (5×30 + 3×30 = 240 gün) — beyan edilmiş kör nokta, bkz. `_duran_tara` (b).
DURAN_VARSAYILAN_GUN = 60
DURAN_MIN_ORNEK = 5         # 5 kayıt = 4 aralık; daha azından "düzenli ritim" ÇIKARILAMAZ
DURAN_KAT = 3.0             # sessizlik, olağan aralığın bu katını AŞMALI
DURAN_DUZENLILIK_TAVANI = 10.0   # en uzun/medyan; aşan seri RİTİM değil, serpintidir
DURAN_GOZLEM_KAT = 3.0      # sessizlik, olayın gözlenmiş ömrünün bu katını aşarsa hüküm YOK

# Elenen grupların KAÇ TANESİNİN ADI kapsama yazılacağı. Sayı görünürdür ama denetlenebilir
# olan ADdır (denetim bulgusu 10): "37 grup elendi" cümlesi, yanlış eleneni gizler.
ELENEN_ORNEK_TAVANI = 8

# ---- HÜKÜM KURULAMADI: TOPLU TESLİMAT (dal denetimi H2, 2026-08-30) -----------------------------
# İKİ AYRI "ölçülemedi" VARDIR ve bu tur onları AYIRIYOR:
#   (a) ÖLÇÜM ZİNCİRİ KIRIĞI — `bozuk_bayt`, `ayristirilamayan_satir`, `olay_alani_yok`,
#       `zaman_damgasi_*`, `defter_yok`, `zaman_ekseni_yok`, `pencere_bos`. Aracın KENDİ arızası;
#       adedi KUSUR sayısıyla büyür, nadirdir ve tek tek onarılabilir. TEKİL kalır.
#   (b) HÜKÜM KURULAMADI — `kadans_olculemedi`, `donuk_alan_yok`. Defter sağlamdır; kural o
#       gruba/olaya hüküm veremiyordur. Adedi DEFTERDEKİ OLAY ADI SAYISIYLA büyür: yerel
#       defterde 177 olaydan 74'ü hükme uygun, 73'ü ölçülemedi. Kalem başına satır basmak, bu
#       sınıfı kalıcı bir günlük gürültü kaynağına çevirir — üstelik modelin SUSTURAMADIĞI
#       sınıfta, yani operatörün kapatamayacağı yerde.
# (b) SINIFI NEDEN BAŞINA TEK KALEME İNER. Sınıf `olculemedi`de KALIR (model yine susturamaz);
# değişen yalnız kaç SATIR ürettiğidir.
HUKUM_KURULAMADI_NEDENLERI = ("kadans_olculemedi", "donuk_alan_yok")

# `donuk_alan_yok` HACMİ ÖLÇÜLMEDİ — BEYAN: yerel defterde üretim açıklığında 0 kalem üretti
# (15 günlük kaydırma probunun HER gününde 0). Aynı mekanizmaya alınması ŞEKİL benzerliğinden
# gelen bir ÇIKARIMDIR, gözlem değil: ikisi de "defter sağlam, kural hüküm veremedi" der ve
# ikisinin de adedi olay/grup sayısıyla büyür.

# `key=<sayı>` — ÖLÇÜLEN tarafı normalleştiren TEK desen. Karşılaştırmanın sağ tarafı (`<7`)
# KASITLI olarak dokunulmadan kalır: eşiğin değişmesi gerçekten başka bir durumdur.
# Bu bir olay-listesi DEĞİL, bir BİÇİM kuralıdır ve deponun `sebep=f"...(gun={g}<{X})"`
# konvansiyonunu izleyen HER olayda çalışır.
_KALIP_DESENI = re.compile(r"([A-Za-z_]\w*\s*=\s*)-?\d+(?:[.,]\d+)?")


@dataclasses.dataclass(frozen=True)
class Kayit:
    """Ayrıştırılmış tek defter satırı. `ham_ts` defterdeki DİZEnin kendisidir (rapor ona döner,
    yeniden biçimlendirilmiş bir zaman UYDURMA sayılır); `an` yalnız aritmetik içindir."""
    satir: int
    ham_ts: str
    an: dt.datetime
    olay: str
    seviye: str
    sebep_ham: object
    sebep: object
    yuk: dict


def _kalip(metin):
    """`key=<sayı>` biçimindeki ÖLÇÜLEN değeri `<N>` ile değiştirir; başka hiçbir şeye dokunmaz.

    NEDEN (denetim bulgusu 1): `tetik_yok(gun=4<7, taze=0<5)` → `tetik_yok(gun=<N><7, taze=<N><5)`.
    Kalem adı KİMLİKTİR; içinde ölçüm taşırsa `gun` her arttığında aynı takılı durum yeni bir
    kalem olur ve tekrar bastırma HİÇ ateşlenemez.

    NEDEN SADECE BU BİÇİM — ölçülerek daraltıldı. Bütün sayıları silen bir kural `http_502` ile
    `http_503`ü ya da `strategy_version 4` ile `3`ü birleştirirdi; bunlar AYRI durumlardır.
    Atama konumundaki sayı ise tanımı gereği o anki ÖLÇÜMDÜR. Yerel defterde (27.887 satır)
    `key=<sayı>` taşıyan tek bir `sebep` YOK — bu biçim canlıya özgüdür, yani kural burada
    ÇIKARIMLA (yayımcı kaynağı) kuruldu ve sentetik defterle çivilendi.

    GÖREMEDİĞİ (ölçüldü, yerel defter): DEĞER TAŞIYAN MESAJ BİÇİMLİ OLAY ADLARI. Örnek —
    `BROKER_REJECT Alpaca reddi: NSC — stop price must be greater than current price` ile aynı
    cümlenin `RTX`lisi ayrı kalemler olarak kalır; `MECHANISM_STALE ... 0.5 sa` ile `0.6 sa` da
    öyle. Değişen parça çoğu zaman SAYI DEĞİL (sembol, hata metni), yani sayısal normalleştirme
    onları zaten toplayamaz; toplamak varlık düzeyinde kümeleme ister ve bu, tespit katmanının
    işi değildir. Bulgu KAYBOLMAZ, TEKRARLAR."""
    if not isinstance(metin, str):
        return metin
    return _KALIP_DESENI.sub(r"\1<N>", metin)


def _kanonik(deger):
    """Alan değerini KARŞILAŞTIRILABİLİR ve hash'lenebilir hâle getirir. Liste/sözlük değerler
    sıralı JSON'a çevrilir — yoksa aynı içerik farklı sırayla "değişmiş" görünürdü."""
    if deger is None or isinstance(deger, (str, int, float, bool)):
        return deger
    try:
        return json.dumps(deger, sort_keys=True, ensure_ascii=False)
    except (TypeError, ValueError):  # sessiz-yutma: JSON'a dönmeyen değer `repr` ile TEMSİL EDİLİR; bilgi kaybolmaz, karşılaştırma yine yapılır ve alan hiçbir sayaçtan düşmez
        return repr(deger)


def _an_coz(ham):
    """ISO-8601 → zaman dilimli `datetime`. Saat dilimi YOKSA UTC varsayılır (defterin tamamı UTC
    yazıyor); varsayım BEYAN EDİLİR çünkü sessiz bir varsayım saatlik kaymayı gizlerdi."""
    if not isinstance(ham, str) or not ham:
        return None
    try:
        an = dt.datetime.fromisoformat(ham)
    except ValueError:  # sessiz-yutma: çözülemeyen damga ÇAĞIRAN tarafından `zaman_damgasi_ayristirilamadi` olarak KAYDA GEÇER — None dönmek onu kaybetmez, sınıflandırmaya yollar
        return None
    return an if an.tzinfo is not None else an.replace(tzinfo=dt.timezone.utc)


def _sayisal(deger):
    """Sayaç adayı mı? `bool` BİLEREK dışarıda: `False→True` bir SAYAÇ artışı değil, bir DURUM
    geçişidir ve `_imza` onu ayrı bir sınıf (`gecis`) olarak ele alır."""
    return isinstance(deger, (int, float)) and not isinstance(deger, bool)


# ---- OKUMA: İKİ GEÇİŞ, AKIŞLA ------------------------------------------------------------------
# NEDEN İKİ GEÇİŞ (denetim bulgusu 10): ilk sürüm `read_text().splitlines()` ile TÜM defteri
# belleğe alıyor, sonra pencere DIŞINDAKİ kayıtların yükünü de tutuyordu (~40-60 MB bugün,
# canlıda ~200k satır/yıl büyüyor). Pencereyi kurmak için "şu an"ı bilmek, "şu an"ı bilmek için
# defteri görmek gerekir — bu yüzden 1. geçiş YALNIZ en son damgayı arar ve HİÇBİR yük tutmaz;
# 2. geçiş yalnız pencere içindeki kaydı somutlaştırır. Maliyet O(pencere)ye iner.
# Dosya SIRALI VARSAYILMAZ: iki geçiş de tüm dosyayı gezer, yani sıra dışı kayıt kaçmaz.

def _satirlar(defter):
    """Defteri satır satır, BAYT olarak akıtır: `(satir_no, metin | None)`. `None`, satırın
    UTF-8 olarak çözülemediği anlamına gelir.

    `errors="replace"` KULLANILMIYOR (denetim bulgusu 10): bozuk bir baytı sessizce U+FFFD'ye
    çevirmek, satırın yine ayrışmasına ve YANLIŞ bir değerin hiçbir kusur kaydı bırakmadan
    ölçüme girmesine yol açardı — `except` içermediği için YASA-4 çivisinin bile göremeyeceği
    bir sessiz yutma."""
    with defter.open("rb") as f:
        for satir_no, ham in enumerate(f, start=1):
            try:
                yield satir_no, ham.decode("utf-8")
            except UnicodeDecodeError:  # sessiz-yutma: çağıran bunu `bozuk_bayt` kusuru olarak KAYDEDER; burada None dönmek bilgiyi kaybetmez, sınıflandırmaya yollar
                yield satir_no, None


def _son_zaman(defter):
    """1. GEÇİŞ — defterdeki EN SON çözülebilir zaman damgası. Hiçbir yük tutulmaz."""
    en_son = None
    for _, satir in _satirlar(defter):
        if not satir or not satir.strip():
            continue
        try:
            kayit = json.loads(satir)
        except (json.JSONDecodeError, ValueError):  # sessiz-yutma: bozuk satır 2. GEÇİŞTE kusur olarak kayda geçer; burada yalnız zaman ekseni aranıyor, atlamak hiçbir bilgiyi kaybetmez
            continue
        if not isinstance(kayit, dict):
            continue
        an = _an_coz(kayit.get("ts"))
        if an is not None and (en_son is None or an > en_son):
            en_son = an
    return en_son


def _oku(defter, baslangic, bitis):
    """2. GEÇİŞ — yalnız `[baslangic, bitis]` aralığındaki kayıtları somutlaştırır.

    Dört liste/sayaç döner: kayıtlar · kusurlar · okunan satır · (boş satır, pencere dışı).
    Ölçülemeyen satır SESSİZCE ATLANMAZ; atlansaydı "0 bulgu" cümlesi defterin okunamayan
    kısmını da kapsıyormuş gibi okunurdu (deponun `olcum-baglami-tuzagi` dersi)."""
    kayitlar, kusurlar = [], []
    okunan = bos = pencere_disi = 0
    for satir_no, satir in _satirlar(defter):
        okunan += 1
        if satir is None:
            kusurlar.append(("bozuk_bayt", None, satir_no, None, "<UTF-8 olarak çözülemedi>"))
            continue
        if not satir.strip():
            bos += 1        # boş satır bir KAYIT DEĞİLDİR; kusur da değildir — ayrı sayılır
            continue
        try:
            kayit = json.loads(satir)
        except (json.JSONDecodeError, ValueError):  # sessiz-yutma: satır kusur listesine ADIYLA girer ve raporda görünür — burada yakalamak taramayı ayakta tutar, bilgiyi yutmaz
            kayit = None
        if not isinstance(kayit, dict):
            kusurlar.append(("ayristirilamayan_satir", None, satir_no, None, satir[:160]))
            continue
        olay = kayit.get("event")
        ham_ts = kayit.get("ts")
        if not isinstance(olay, str) or not olay:
            # ZAMANI ÇÖZÜLEBİLEN TEK KUSUR SINIFI: pencereye BAĞLANIR (yukarıdaki gerekçe).
            kusur_an = _an_coz(ham_ts)
            if kusur_an is not None and not (baslangic <= kusur_an <= bitis):
                pencere_disi += 1
                continue
            kusurlar.append(("olay_alani_yok", None, satir_no,
                             ham_ts if isinstance(ham_ts, str) else None, satir[:160]))
            continue
        if ham_ts is None:
            kusurlar.append(("zaman_damgasi_yok", olay, satir_no, None, satir[:160]))
            continue
        an = _an_coz(ham_ts)
        if an is None:
            kusurlar.append(("zaman_damgasi_ayristirilamadi", olay, satir_no, None, satir[:160]))
            continue
        if not (baslangic <= an <= bitis):
            pencere_disi += 1       # yükü TUTULMAZ — yalnız sayılır
            continue
        sebep_ham = _kanonik(kayit.get("sebep"))
        kayitlar.append(Kayit(
            satir=satir_no, ham_ts=ham_ts, an=an, olay=olay,
            seviye=str(kayit.get("level") or ""),
            sebep_ham=sebep_ham, sebep=_kalip(sebep_ham),
            yuk={a: d for a, d in kayit.items() if a not in ZARF_ALANLARI}))
    return kayitlar, kusurlar, okunan, bos, pencere_disi


def _sifirlanan_alanlar(kayitlar):
    """OLAY DÜZEYİNDE sıfırlanan sayısal alanların adları: `{olay: {alan, ...}}`.

    NEDEN OLAY DÜZEYİNDE, GRUP DÜZEYİNDE DEĞİL: sayaç SİSTEMİN malıdır, onu o an raporlayan
    dalın değil. `gecen_gun` sıfırlanması sprint GERÇEKTEN koştuğunda olur; o an olay ya hiç
    basılmaz ya başka bir `sebep`le basılır. Sıfırlanmayı yalnız grubun içinde arasaydık,
    ilerleme kanıtı komşu dalda kalır ve göremezdik.

    HÜKÜMDEKİ ROLÜ: sıfırlanan sayaç İLERLEME kanıtıdır (sistem tur atıyor) → o alan artık
    "kertik" sayılmaz, dünyanın hareketi sayılır. Sıfırlanmayan sayaç ise SÜRE kanıtıdır.

    HANGİ PENCEREDEN ÇAĞRILIR — DAL DENETİMİ H1'İN ONARIMI (2026-08-30). Bu küme, bağladığı
    hükmün KENDİ penceresinden toplanmalıdır ve `tara()` onu artık TAKILI penceresiyle çağırır.
    Önceki hâl EN GENİŞ pencereyi (60 gün) kullanıyor ama 3 GÜNLÜK hükmü bağlıyordu; bedeli
    ölçülmüş bir vakadır: `sprint_cadence_skip.gecen_gun` haftalık taban tetiğiyle en geç 7 günde
    bir sıfırlanır, yani 60 günde ~8 sıfırlama görülür ve alan KALICI olarak "ilerleme" sayılır.
    Sonuç: alan hiç KERTİK olamaz, 3 günlük pencerede 3-4 değer alır, grup `oynak` diye elenir —
    ve dalın var oluş gerekçesi olan sinyal (*"sprint yalnız zaman aşımıyla ateşliyor, LİYAKATLE
    hiç ateşlemiyor"*) tespit katmanına HİÇ GÖRÜNMEZ. Bir hüküm, göremediği bir pencereden gelen
    kanıtla beraat ettirilemez.

    BEDELİ, AÇIKÇA: dar pencere sıfırlamayı KAÇIRABİLİR (yanlış pozitif yönü — iyi huylu bir dal
    takılı görünür). Asimetri bunu haklı kılar ve `_imza`nın residüel notu bu bedeli zaten
    beyan ediyor: yanlış pozitifin bedeli bir mesaj, yanlış negatifin bedeli görülmeyen arızadır.
    OLAY DÜZEYİ KORUNDU: sıfırlama komşu DALDA görünür (`kota_yenileme[yenilendi]` vakası)."""
    seri = {}
    for k in sorted(kayitlar, key=lambda k: (k.olay, k.an, k.satir)):
        for ad, deger in k.yuk.items():
            if _sayisal(deger):
                seri.setdefault((k.olay, ad), []).append(deger)
    sifirlanan = {}
    for (olay, ad), degerler in seri.items():
        if any(b < a for a, b in zip(degerler, degerler[1:])):
            sifirlanan.setdefault(olay, set()).add(ad)
    return sifirlanan


def _imza(grup, sifirlanan):
    """Grubun alanlarını ZAMAN İÇİNDEKİ ŞEKİLLERİNE göre BEŞ sınıfa ayırır.

    Hüküm alanın DEĞERİNDEN değil, ŞEKLİNDEN çıkar — iyi huylu/takılı ayrımını yapısal kılan
    şey budur (elle yazılmış bir "iyi huylu sebepler" listesi bakımı unutulan ikinci bir
    gerçektir ve çürür):

      DONUK   — hiç değişmemiş. Durağanlığın kanıtı; `deger` bundan kurulur.
      GEÇİŞ   — TAM BİR KEZ değişip donmuş (mandal). Dünya bir kez kıpırdadı ve DURDU; bu,
                takılılığı çürütmez, pekiştirir. Son değeri `kanit`e girer, `deger`e GİRMEZ
                (dal denetimi M4 — aşağıda).
      KERTİK  — sayısal, zamanla hiç azalmayan, olay düzeyinde de SIFIRLANMAYAN sayaç.
                SÜRE kanıtıdır; `deger`e GİRMEZ (her tur artar, girseydi tekrar bastırma her
                gün bozulurdu), `kanit`e girer.
      SERBEST — neredeyse her kayıtta farklı: bir SAAT (yaş/süre/sıra). Durağanlık lehine de
                aleyhine de tanıklık edemez, hükümden ÇEKİLİR ve çekildiği kanıtta YAZAR.
      OYNAK   — geri kalan her şey. DÜNYANIN HAREKETİDİR: tek bir oynak alan grubu takılı
                olmaktan çıkarır.

    KERTİK NEDEN AYRI BİR SINIF (denetim bulgusu 2 — ASIL ONARIM). İlk sürüm yalnız `ardisik`i
    tanıyor, aynı semantiğe sahip `gecen_gun`ü "dünyanın hareketi" sayıp grubu ÖLDÜRÜYORDU.
    Aynı alan bir vakada ayırt edici, öbüründe kör ediciydi. Bedeli ölçülmüş bir vakadır:
    `sprint_cadence_skip[mesgul:canli_arama]` — yayımcının kendi yorumuyla *"4+ gün boyunca HER
    döngüde tekrar etti"* — `gecen_gun` yürüdüğü için iyi huylu sayılıp eleniyordu. `@bekci`nin
    var olma sebebi olan takılı durum, tespit katmanına GÖRÜNMÜYORDU. Bu depoda bayatlık sayacı
    bir kaza değil KONVANSİYONdur (`ardisik`, `gecen_gun`, `yas_sa`); artık hepsi aynı sınıfta.

    RESIDÜEL YANLIŞ POZİTİF SINIFI — KAPATILMADI, BEYAN EDİLDİ. Tekdüze artış TEK BAŞINA iyi
    huyluyu takılıdan AYIRMAZ: `saat_dilimi_disinda` (gerçekten iyi huylu) da `gecen_gun`
    yürütür. Sıfırlanma denetimi bu ayrımı SAĞLIKLI sistemde yapar (sprint koşar → sayaç
    sıfırlanır → grup iyi huylu okunur), ama sistem GERÇEKTEN takılıyken iki grup da takılı
    görünür. O hâlde ikisi de AYNI arızanın iki görüntüsüdür — yani bedel bir YALAN değil bir
    TEKRARdır. Asimetri bunu haklı kılar: yanlış pozitifin bedeli bir mesaj, yanlış negatifin
    bedeli kimsenin görmediği bir arızadır. Sıralama katmanı ve operatör hüküm verir.

    BU SINIFIN İKİNCİ YÖNÜ — GÜRÜLTÜ ÜRETEN YÖN (dal denetimi M4, ÖLÇÜLDÜ 2026-08-30). Beyan
    eskiden yalnız SİNYAL ÖLDÜREN yönü (kör nokta (c): iki kez dönen bayrak grubu öldürür)
    anlatıyordu; öteki yön ölçülmemişti bile. 25 günlük sentetik defter, günlük kaydırma, 3
    günde bir dönen İYİ HUYLU bir bayrak: kalem hiçbir gün elenmedi, ama `deger`i 21 günde 7 kez
    değiştirdi — yani operatöre 21 günde 8 bildirim (hedeflenen kadans: 3). Kök neden `oynak`
    değil, MANDALIN DEĞERİNİN durağanlık kimliğine girmesiydi: pencere İÇİNDE kıpırdamış bir
    alan, tanımı gereği durağanlığa tanıklık edemez. `deger` artık YALNIZ DONUK alanlardan
    kurulur; mandal `kanit.mandal_alanlar`da durur ve kalemin kendisi TAKILI kalmaya devam eder.
      · KAPATILMAYAN YARI, İKİ YÖNLÜ BEYAN: (i) periyodu PENCEREDEN UZUN bir bayrak, bu
        açıklıkta gerçekten iki farklı durumdur ve yeniden anılması DOĞRUDUR — hükmü kendi
        açıklığının kanıtına bağlama ilkesi burada da geçerli, bu bir kusur değil bir SINIRDIR.
        (ii) GERÇEK bir mandal (bir kez dönüp donan bayrak) artık ertesi gün "DEĞİŞTİ" diye
        anılmaz; en geç yeniden-anma aralığında (168 sa) "HÂLÂ SÜRÜYOR" satırıyla gider. Bu bir
        YANLIŞ NEGATİF yönüdür ve bilerek ödendi: kalem zaten HER taramada listede durur, yani
        kaybolan bilgi değil, bir bildirimin gecikmesidir."""
    n = len(grup)
    sifir = sifirlanan.get(grup[0].olay, set())
    alanlar = {}
    for k in grup:
        for ad, deger in k.yuk.items():
            alanlar.setdefault(ad, []).append(_kanonik(deger))

    donuk, gecis, kertik, serbest, oynak = {}, {}, {}, [], []
    for ad, dizi in sorted(alanlar.items()):
        if len(dizi) != n:
            # ALAN HER KAYITTA YOK: varlığın kendisi bir durum değişimidir.
            oynak.append(ad)
            continue
        benzersiz = set(dizi)
        if len(benzersiz) == 1:
            donuk[ad] = dizi[0]
            continue
        gecis_sayisi = sum(1 for a, b in zip(dizi, dizi[1:]) if a != b)
        artan = (all(_sayisal(d) for d in dizi)
                 and all(b >= a for a, b in zip(dizi, dizi[1:]))
                 and ad not in sifir)
        if artan:
            kertik[ad] = {"ilk": dizi[0], "son": dizi[-1], "artis": dizi[-1] - dizi[0]}
        elif gecis_sayisi == 1:
            gecis[ad] = dizi[-1]
        elif len(benzersiz) >= min(SERBEST_AKAN_ORAN * n, n - 1):
            # KÜÇÜK n TOLERANSI (denetim bulgusu 10): salt oranla n=9'da 8 farklı değer
            # 0,889 < 0,9 kalır ve yuvarlanmış bir saat (0.11, 0.11, 0.12, …) OYNAK sayılıp
            # gerçek takılı grubu sessizce öldürürdü. `n-1` kolu bu bandı kapatır.
            serbest.append(ad)
        else:
            oynak.append(ad)
    return donuk, gecis, kertik, serbest, oynak


def _sayac(grup):
    """Grubun SON kaydındaki bayatlık sayacı (yoksa None).

    SON, AZAMİ DEĞİL: sayacı basan kod onu kilit dışındaki her dalda sıfırlar, yani son değer
    "şu an kesintisiz kaç tur" demektir. Azami, pencerede bir kez 93'e çıkıp sonra temizlenmiş
    bir durumu HÂLÂ takılı diye raporlardı."""
    son = grup[-1].yuk.get(SAYAC_ALANI)
    return int(son) if _sayisal(son) else None


def _kalem(ad, deger, ilk, son, kanit, kimlik=None):
    """Arayüzün TEK kurucusu — Görev 2 bu ALTI alana bağlanıyor; ikinci bir kurucu ikinci bir
    şekil demektir ve sessizce ayrışır.

    `kimlik` — BASTIRMANIN ANAHTARI (dal denetimi M6, 2026-08-30). `ad` OKUNUR bir etikettir ve
    hüküm değişince değişir (`X` → `X (kadans_olculemedi)`); ÖLÇÜLDÜ ki gerçek yerel defterde 14
    günde DURAN'dan düşen 7 olayın 7'si de `kadans_olculemedi`ye göçtü — yani göç bir uç durum
    değil, DURMUŞ bir işin bu defterdeki NORMAL son durağıdır. Anahtar `ad`dan kurulunca aynı
    olgu göçte ikinci kez "YENİ" diye duyuruluyordu. `kimlik` TARAMA AİLESİNİ taşır
    (`durum:` = takılı tarayıcısı · `kadans:` = duran tarayıcısı · `kusur:` · `toplu:`), sınıf
    adını DEĞİL: aynı olay adının aynı taramada hem `takili` hem `duran` görünebilmesi ÖLÇÜLMÜŞ
    bir vakadır ve iki aileyi ayıran şey o ön ektir."""
    return {"ad": ad, "deger": deger, "ilk_gorulme": ilk, "son_gorulme": son, "kanit": kanit,
            "kimlik": ad if kimlik is None else kimlik}


def _grup_adi(olay, sebep):
    """Kalem adı sebebi TAŞIMAK ZORUNDA: aynı olayın iki sebebi iki AYRI durumdur ve tekrar
    bastırma ada göre anahtarlanır. Sebep burada zaten `_kalip`ten geçmiş KİMLİKTİR."""
    return olay if sebep is None else f"{olay}[{sebep}]"


def _takili_tara(pencere, sifirlanan):
    """TAKILI sınıfı + hükmü kurulamayan gruplar + ADIYLA sayılan elemeler.

    İKİ YOL, biri ötekini ezer:
      (a) SAYAÇ YOLU — grup `ardisik` taşıyorsa YAYIMCININ hükmü üstündür: o sayaç kilit
          dışındaki her dalda sıfırlandığı için "kesintisiz" bilgisi zaten kaynakta verilmiştir
          ve pencere sınırından da SAĞ ÇIKAR (bizim tekrar sayımız yalnız bir alt sınırdır).
      (b) TÜRETİLMİŞ YOL — sayaç yoksa tekrar, süre ve durağanlık defterden çıkarılır.

    HÜKMÜ KURULAMAYAN GRUP SESSİZCE DÜŞMEZ: eşikleri geçmiş ama tek bir durağan alanı olmayan
    grup için "değeri değişmiyor" BOŞ BİR DOĞRUdur. Takılı saymak durağanlığı UYDURMAK, sessizce
    atmak ölçülemeyeni sıfır saymak olurdu — `olculemedi`ye düşer.

    BU SINIFIN KÖR NOKTALARI — dördü de gerçek, dördü de kapatılmadı (denetim bulgusu 7;
    `_duran_tara` bunları sayarken burada hiç yoktu, ve tek taraflı dürüstlük dürüstlük
    değildir):
      (a) SABİT YÜKLÜ SAĞLIKLI NABIZ → YANLIŞ POZİTİF. Saatlik `disk_ok{esik:90}` gibi sabit
          bir yapılandırma alanı basan sağlam bir kalp atışı tekrar eşiğini ve süre tabanını
          geçer, hiçbir alanı oynamaz ve TAKILI diye raporlanır. Kural "aynı şeyi söylüyor" ile
          "bozuk" arasındaki farkı GÖREMEZ; bu ayrım defterde değil, olayın anlamındadır.
      (b) KERTİK RESIDÜELİ — bkz. `_imza`. Sistem gerçekten takılıyken iyi huylu bir dal da
          takılı görünür (aynı arızanın ikinci görüntüsü).
      (c) İKİDEN ÇOK KEZ DÖNEN BİR BAYRAK grubu öldürür. Mandal (tek geçiş) artık tolere
          ediliyor, ama iki kez dönen bir boolean OYNAK'tır ve 191 kayıtlık bir sinyali
          eleyebilir. Tolerans BİLEREK 1 geçişte tutuldu: daha fazlası "dünya hareket ediyor"
          ile "gürültü" arasındaki ayrımı ölçülemez kılar.
      (d) TEK KAYITLIK SAYAÇ GRUBU. n=1 iken her alan zorunlu olarak donuktur; alan
          sınıflandırması hiçbir şey ölçmez, o yüzden `deger` UYDURULMAZ — `None` + neden döner.
    """
    gruplar = {}
    for k in pencere:
        gruplar.setdefault((k.olay, k.sebep), []).append(k)

    takili, olculemez = [], []
    esik_alti, oynak_deger = [], []

    for (olay, sebep), grup in sorted(gruplar.items(), key=lambda x: (x[0][0], str(x[0][1]))):
        grup.sort(key=lambda k: (k.an, k.satir))
        n = len(grup)
        sure_saat = (grup[-1].an - grup[0].an).total_seconds() / 3600.0
        donuk, gecis, kertik, serbest, oynak = _imza(grup, sifirlanan)
        sayac = _sayac(grup)
        ad = _grup_adi(olay, sebep)
        ham_ornek = sorted({str(k.sebep_ham) for k in grup if k.sebep_ham is not None})
        ortak = {
            "olay": olay, "sebep": sebep, "tekrar": n, "sure_saat": round(sure_saat, 3),
            "seviyeler": sorted({k.seviye for k in grup if k.seviye}),
            "sebep_ham_ornekleri": ham_ornek[:3],
            "sebep_ham_benzersiz": len(ham_ornek),
            "serbest_akan_alanlar": serbest,
            "kertik_alanlar": kertik, "mandal_alanlar": gecis,
            "ilk_satir": grup[0].satir, "son_satir": grup[-1].satir,
        }
        # `deger` YALNIZ DONUK ALANLARDAN (dal denetimi M4 — gerekçe ve ölçüm `_imza`da):
        # pencere içinde kıpırdamış bir alan durağanlığın kimliği olamaz. Mandal `kanit`te.
        kimlik = f"durum:{ad}"
        deger = dict(donuk) if n > 1 else None
        if n == 1:
            ortak["deger_olculemedi"] = ("tek kayıt — her alan zorunlu olarak donuk görünür, "
                                         "alan sınıflandırması hiçbir şey ölçmez")

        if sayac is not None:
            if sayac < TAKILI_MIN_TEKRAR:
                esik_alti.append(ad)
                continue
            azami = max((int(k.yuk[SAYAC_ALANI]) for k in grup if _sayisal(k.yuk.get(SAYAC_ALANI))),
                        default=sayac)
            takili.append(_kalem(ad, deger, grup[0].ham_ts, grup[-1].ham_ts,
                                 {**ortak, "kaynak": "ardisik", "kaynak_alani": SAYAC_ALANI,
                                  "ardisik_son": sayac, "ardisik_azami": azami,
                                  "oynak_alanlar": oynak,
                                  "not": ("kesintisizlik hükmü YAYIMCININ sayacından gelir; "
                                          "sayaç kilit dışındaki her dalda sıfırlanır")},
                                 kimlik=kimlik))
            continue

        if n < TAKILI_MIN_TEKRAR or sure_saat < TAKILI_MIN_SURE_SAAT:
            esik_alti.append(ad)
            continue
        if oynak:
            # İYİ HUYLU TEKRAR — ve elemesi GÖRÜNÜR: adı kapsama yazılır. Görünmez bir eleme,
            # elle yazılmış bir yoksayma listesinden daha tehlikelidir; denetlenemez bile.
            oynak_deger.append(ad)
            continue
        if not deger:
            olculemez.append(_kalem(
                f"{ad} (donuk_alan_yok)", None, grup[0].ham_ts, grup[-1].ham_ts,
                {**ortak, "neden": "donuk_alan_yok", "adet": n,
                 # `hepsi_mandal` AYRI BİR ALT NEDENDİR (dal denetimi M4): mandal artık `deger`e
                 # girmediği için, YALNIZ mandal taşıyan bir grup buraya düşer. Onu
                 # `hepsi_serbest_akan` kovasına atmak, yeni açılan bu yolu GÖRÜNMEZ kılardı.
                 "alt_neden": ("hepsi_mandal" if (gecis and not serbest and not kertik)
                               else "hepsi_serbest_akan" if (serbest or kertik or gecis)
                               else "yuk_yok"),
                 "aciklama": ("tekrar eşiklerini geçti ama durağanlığa tanıklık edebilecek tek "
                              "bir DONUK alan taşımıyor — durağanlık UYDURULAMAZ, hüküm "
                              "kurulmadı")},
                kimlik=kimlik))
            continue
        takili.append(_kalem(ad, deger, grup[0].ham_ts, grup[-1].ham_ts,
                             {**ortak, "kaynak": "turetilmis", "oynak_alanlar": oynak},
                             kimlik=kimlik))

    takili.sort(key=lambda x: (-x["kanit"].get("ardisik_son", x["kanit"]["tekrar"]), x["ad"]))
    return takili, olculemez, {
        "grup_sayisi": len(gruplar), "takili_grup": len(takili),
        "esik_alti_grup": len(esik_alti), "oynak_deger_grup": len(oynak_deger),
        "esik_alti_ornek": sorted(esik_alti)[:ELENEN_ORNEK_TAVANI],
        "oynak_deger_ornek": sorted(oynak_deger)[:ELENEN_ORNEK_TAVANI]}


def _duran_tara(pencere, simdi):
    """DURAN sınıfı: geçmişte DÜZENLİ tekrarlayan bir olay ARTIK GELMİYOR.

    KURAL, DEFTERİN KENDİ ŞEKLİNDEN — beklenen olayların elle yazılmış bir listesinden DEĞİL
    (öyle bir liste, tam da yokluğu görülmesi gereken yeni olayı içermezdi):

      1. Pencerede ≥ `DURAN_MIN_ORNEK` kayıt (5 kayıt = 4 aralık; azından ritim çıkarılamaz).
      2. OLAĞAN ARALIK = aralıkların MEDYANI. Ortalama DEĞİL: tek bir uzun boşluk, kendisiyle
         karşılaştırılacak tabanı şişirir ve aranan duruşu görünmez kılar.
      3. Seri DÜZENLİ: en uzun / medyan ≤ `DURAN_DUZENLILIK_TAVANI` — düzensiz bir serpintinin
         medyanı seriyi temsil etmez.
      3b. Sessizlik ≤ `DURAN_GOZLEM_KAT` × olayın gözlenmiş ömrü. Bu bir KANIT kuralıdır, ritim
         kuralı değil: 29 saniye gözlenmiş bir olayın 52 saatlik suskunluğu hakkında dürüst tek
         cevap "bilmiyorum"dur. 3. madde bunu YAKALAYAMAZ çünkü düzgün aralıklı bir patlama
         KUSURSUZ DÜZENLİDİR (ölçüldü: 3. madde tek başına konunca patlama çivisi kırmızı kaldı).
      4. Sessilik > `DURAN_KAT` × medyan.
      5. VE sessizlik > olayın KENDİ geçmişindeki en uzun boşluk: kendi geçmişinde 36 saatlik
         boşlukları olan bir olay için 16 saatlik suskunluk NORMALDİR.

    PENCERE: bu sınıf `DURAN_VARSAYILAN_GUN` günlük KENDİ penceresini kullanır, `gun`u değil —
    gerekçe `DURAN_VARSAYILAN_GUN` sabitinin başında.

    BU KURALIN GÖREMEDİKLERİ — beşi de gerçek, beşi de kapatılmadı:
      (a) PENCEREDEN ÖNCE DURMUŞ OLAY. Pencerede sıfır kaydı vardır; bir pencere taraması
          "çoktan durdu" ile "hiç var olmadı"yı AYIRT EDEMEZ. Sınıfın en büyük kör noktası;
          beklenen-olaylar kaydı olmadan kapanmaz, o kayıt da planın yasakladığı elle liste olur.
      (b) PENCEREDEN UZUN KADANS. 60 günlük pencere günlük (60 örnek) ve haftalık (8 örnek) işi
          görür; AYLIK bir iş 5 örneğe ulaşamaz (2 örnek) ve hükümsüzdür.
          BU SATIR BİR KEZ BAYATLADI (dal denetimi M1, 2026-08-30): sabit 45'ten 60'a çıkarken
          beyan 45'te kaldı ve AYNI DOSYA iki paragraf yukarıda 45'in NEDEN reddedildiğini
          anlatıyordu. Hiçbir çivi ölçmediği için sessizce çürüdü; artık
          `test_DURAN_KOR_NOKTA_BEYANI_SABITTEN_TURETILIR` sayıları `DURAN_VARSAYILAN_GUN`den
          türetip burada arıyor.
      (c) DEFTERİN TAMAMEN DURMASI. `simdi` defterin son kaydıdır; yazar tamamen ölürse saat de
          donar ve HİÇBİR ŞEY durmuş görünmez. Tam arıza, bu kuralın göremediği arızadır.
      (d) 5. madde MUHAFAZAKÂRDIR: geçmişinde tek bir büyük boşluk olan olay kendi çıtasını
          yükseltir — yanlış negatif üretir.
      (e) BULGU GEÇİCİDİR — ve bu ÖLÇÜLDÜ, çıkarılmadı. 3b maddesi ve kayan pencere yüzünden bir
          "durdu" bulgusu sonsuza dek raporlanmaz: sessizlik gözlem ömrünün 3 katını aşınca kalem
          `olculemedi`ye, örnekler pencereden düşünce `ornek_kitligi`ne geçer. GERÇEK YEREL
          DEFTERDE (`simdi` 14 gün geriye kaydırılarak, 2026-08-30): DURAN listesinden düşen 7
          olayın 7'si de `kadans_olculemedi`ye göçtü, hiçbiri "düzeldi" diye düşmedi. Yani göç
          bir uç durum DEĞİL, durmuş bir işin bu defterdeki NORMAL son durağıdır. Operatör "hâlâ
          duruyor mu?" sorusunu bu araca SÜRESİZ soramaz — 60 günlük pencere bandı ilk sürüme
          göre çok genişletti ama KALDIRMADI. Göçün İKİNCİ zararı (aynı olgunun iki kez "YENİ"
          diye duyurulması) `kimlik` ile kapatıldı; BU zarar (unutma) AÇIK KALDI ve beklenen-olay
          kaydı olmadan kapanmaz.
    """
    olaylar = {}
    for k in pencere:
        olaylar.setdefault(k.olay, []).append(k)

    duran, olculemez = [], []
    ornek_kitligi = []
    for olay, grup in sorted(olaylar.items()):
        grup.sort(key=lambda k: (k.an, k.satir))
        if len(grup) < DURAN_MIN_ORNEK:
            ornek_kitligi.append(olay)
            continue
        araliklar = [(b.an - a.an).total_seconds() / 3600.0 for a, b in zip(grup, grup[1:])]
        medyan = statistics.median(araliklar)
        en_uzun = max(araliklar)
        sessizlik = (simdi - grup[-1].an).total_seconds() / 3600.0
        gozlem = (grup[-1].an - grup[0].an).total_seconds() / 3600.0
        duzensizlik = None if medyan <= 0 else en_uzun / medyan
        if medyan <= 0 or duzensizlik > DURAN_DUZENLILIK_TAVANI \
                or sessizlik > DURAN_GOZLEM_KAT * gozlem:
            # RİTMİ ya da KANITI OLMAYAN SERİ: hüküm KURULMAZ, ama SESSİZCE DE DÜŞMEZ.
            olculemez.append(_kalem(
                f"{olay} (kadans_olculemedi)", None, grup[0].ham_ts, grup[-1].ham_ts,
                kimlik=f"kadans:{olay}", kanit={
                 "neden": "kadans_olculemedi", "adet": len(grup), "olay": olay,
                 "alt_neden": ("medyan_aralik_sifir" if medyan <= 0
                               else "duzensiz_ritim" if duzensizlik > DURAN_DUZENLILIK_TAVANI
                               else "gozlem_suresi_yetersiz"),
                 "medyan_aralik_saat": round(medyan, 6),
                 "en_uzun_aralik_saat": round(en_uzun, 3),
                 "duzensizlik": None if duzensizlik is None else round(duzensizlik, 1),
                 "tavan": DURAN_DUZENLILIK_TAVANI,
                 "gozlem_suresi_saat": round(gozlem, 3),
                 "sessizlik_saat": round(sessizlik, 3), "gozlem_kat": DURAN_GOZLEM_KAT,
                 "aciklama": ("sessizliğin karşılaştırılacağı GÜVENİLİR bir ritim YOK — seri ya "
                              "patlama hâlinde basılıyor ya da olay, suskunluğuna kıyasla çok "
                              "kısa bir süre gözlenmiş")}))
            continue
        if sessizlik <= DURAN_KAT * medyan or sessizlik <= en_uzun:
            continue
        duran.append(_kalem(
            olay,
            # `deger` SINIF-KARARLI KİMLİKTİR, ölçüm DEĞİLDİR (denetim bulgusu 3). İlk sürüm
            # buraya `ornek` ve `medyan` koyuyordu; ikisi de pencere kaydıkça değişir, yani
            # `deger` HER TARAMADA farklı olur ve "yalnız DEĞERİ değişince tekrar söyle" kuralı
            # bu sınıf için hiç ateşlenemezdi — `takili` tarafında özenle kaçınılan hatanın
            # birebir aynısı. Ölçümler `kanit`e taşındı.
            {"durum": "sessiz"},
            grup[0].ham_ts, grup[-1].ham_ts,
            {"olay": olay, "neden": "duran", "ornek": len(grup),
             "sessizlik_saat": round(sessizlik, 3),
             "olagan_aralik_saat": round(medyan, 3),
             "medyan_aralik_saat": round(medyan, 3),
             "en_uzun_gecmis_aralik_saat": round(en_uzun, 3),
             "duzensizlik": round(duzensizlik, 1), "tavan": DURAN_DUZENLILIK_TAVANI,
             "gozlem_suresi_saat": round(gozlem, 3), "gozlem_kat": DURAN_GOZLEM_KAT,
             "kat": DURAN_KAT, "son_satir": grup[-1].satir,
             "not": ("sessizlik hem olağan aralığın {:.0f} katını hem de olayın KENDİ en uzun "
                     "boşluğunu aştı").format(DURAN_KAT)},
            kimlik=f"kadans:{olay}"))
    duran.sort(key=lambda x: (-x["kanit"]["sessizlik_saat"], x["ad"]))
    return duran, olculemez, {
        "olay_sayisi": len(olaylar), "duran_ornek_kitligi": len(ornek_kitligi),
        "duran_ornek_kitligi_ornek": sorted(ornek_kitligi)[:ELENEN_ORNEK_TAVANI]}


def _kusurlari_topla(kusurlar):
    """Ölçülemeyen satırları (neden, olay) çiftine göre TOPLAR. 800 bozuk satır 800 kalem
    üretseydi liste okunmaz olurdu; ama sayı ve satır aralığı KAYBOLMAZ."""
    kovalar = {}
    for neden, olay, satir_no, ham_ts, ornek in kusurlar:
        kova = kovalar.setdefault((neden, olay), {"adet": 0, "ilk_satir": satir_no,
                                                  "son_satir": satir_no, "ilk_ts": ham_ts,
                                                  "son_ts": ham_ts, "ornek": ornek})
        kova["adet"] += 1
        kova["ilk_satir"] = min(kova["ilk_satir"], satir_no)
        kova["son_satir"] = max(kova["son_satir"], satir_no)
        if ham_ts:
            kova["ilk_ts"] = kova["ilk_ts"] or ham_ts
            kova["son_ts"] = ham_ts
    return [_kalem(
        neden if olay is None else f"{olay} ({neden})",
        None,                              # UYDURMA YASAĞI: ölçülemeyenin DEĞERİ None'dır
        kova["ilk_ts"], kova["son_ts"],    # zaman okunamadıysa None kalır — SAHTE ZAMAN YOK
        {"neden": neden, "olay": olay, "adet": kova["adet"],
         "ilk_satir": kova["ilk_satir"], "son_satir": kova["son_satir"],
         "ornek_satir": kova["ornek"],
         # KAPSAM KALEMİN İÇİNDE YAZAR: zamanı çözülemeyen kusur pencereye bağlanamaz ve
         # okuyucu bunu kalemden öğrenmeli — kapsam satırının "bu pencerenin DIŞI görülmedi"
         # cümlesi bu sınıf için YANLIŞTIR.
         "pencere": ("dosyanin_tamami" if neden in PENCEREYE_BAGLANAMAYAN_KUSURLAR
                     else "pencere_ici"),
         "pencere_notu": (
             "zamanı ÇÖZÜLEMEDİĞİ için pencereye bağlanamadı — bu kalem DOSYANIN TAMAMINDAN "
             "gelir, pencere beyanının istisnasıdır"
             if neden in PENCEREYE_BAGLANAMAYAN_KUSURLAR
             else "zamanı çözüldü ve pencere içinde")},
        # ÖLÇÜM ZİNCİRİ KIRIĞI KENDİ AİLESİDİR: aynı adı taşıyan bir `durum:`/`kadans:` hükmüyle
        # tek anahtara düşerse, bozuk bir satır bir arıza hükmünü sessizce bastırırdı.
        kimlik=f"kusur:{neden}|{olay}")
        for (neden, olay), kova in sorted(kovalar.items(), key=lambda x: (x[0][0], str(x[0][1])))]


def _buyukluk_bandi(adet: int) -> str:
    """Kalem sayısını İKİLİK BÜYÜKLÜK BANDINA indirger — bir kimlik parçası olarak.

    NEDEN BANT, TAM SAYI DEĞİL (ÖLÇÜLDÜ, gerçek yerel defter, `simdi` 14 gün geriye
    kaydırılarak, 2026-08-30): `kadans_olculemedi` kalem sayısı 65→73 yürüdü ve TAM SAYI olarak
    14 günlük geçişin 6'sında (%43) değişti. Kimliğe ham sayı koymak, sıfır gerçek bulgu taşıyan
    bir sınıf için haftada ~3 "DEĞİŞTİ" bildirimi demekti. AYNI ölçümde ikilik bant 14 geçişin
    HİÇBİRİNDE değişmedi.

    NEDEN İKİLİK — YENİ BİR EŞİK UYDURULMADI. Bant, ayarlanmış bir kesim değil sayının kendi
    gösteriminden gelen bir özelliktir: "sayı İKİYE KATLANDI mı / YARILANDI mı". Bir insanın
    triyajında bilgi taşıyan tek sayı değişimi budur; "71 mi 73 mü" eyleme çevrilemez.

    BEDELİ ÖLÇÜLDÜ ve İLK BEYAN YANLIŞTI. İlk hâl *"ölçülen aralık (65-73) bugün sınırdan
    uzaktır"* diyordu; prob 14 günden 30 güne uzatılınca seri `-28g`den `-22g`ye kadar TAM 63'te
    (bandın son değeri), `-21g`den `-17g`ye kadar TAM 64'te (bir sonraki bandın ilk değeri)
    durdu — yani seri, ilk probun 7 gün ötesinde ON İKİ GÜN boyunca bant kenarında oturuyordu ve
    tek bir kalemin düşmesi bandı çevirirdi. Bandın duyarlılığı değişimin BÜYÜKLÜĞÜNE değil
    KONUMUNA bağlıdır: kenarda +1'e ateşler, bandın ortasında +9'a ateşlemez. Yön iyi huyludur
    (fazladan bir mesaj), ama beyanın kendisi ölçüme UYMAK zorundadır — bu dosyanın ilk turda
    `_duran_tara`da kapattığı sınıfın (beyan kendi dosyasına karşı bayat) aynısıdır.
    KONUM DUYARLILIĞINI ALT-NEDEN BAŞINA BANT KISMEN TELAFİ EDER: bir alt sınıf kenarda
    değilken öteki olabilir, yani tek bir bandın körlüğü sınıfın tamamını körleştirmez."""
    if adet <= 0:
        return "0 kalem"
    alt = 1 << (adet.bit_length() - 1)
    return f"{alt}-{alt * 2 - 1} kalem"


def _hukumsuzleri_topla(kalemler, bilinen=frozenset()):
    """HÜKÜM KURULAMADI kalemlerini NEDEN BAŞINA TEK kaleme indirir — AMA GEÇMİŞİ OLANI DEĞİL.

    `(teslim_edilecek, ayrinti)` döner. Gerekçenin tamamı `HUKUM_KURULAMADI_NEDENLERI`nin yanında.

    GEÇMİŞİ OLAN KALEM TOPLANMAZ (`bilinen`) — İKİNCİ DALGANIN ASIL ONARIMI, 2026-08-30.
    İlk toplama turu "KAYIP YOKTUR: tekil hüküm `ayrinti`ye gider" diyordu; bu CLI ve çiviler
    için doğru, TESLİMAT KANALI için YANLIŞTI. ÖLÇÜLDÜ (gerçek yerel defter, 20 gün): DURAN'dan
    düşen 7 olayın 7'si de `kadans_olculemedi`ye göçtü ve toplamadan SONRA hiçbiri bir daha
    ANILMADI — oysa toplamadan ÖNCE her biri 168 saatte bir ADIYLA "hâlâ sürüyor" satırı
    alıyordu. Yani sessizlik, tam da bu botun var oluş sebebi olan sınıfın (durmuş bir iş,
    kimse bakmadı) körleşmesiyle satın alınmıştı. Üstelik göç, DURMUŞ bir işin bu defterdeki
    NORMAL yoludur: bir iş durur, sessizliği gözlem ömrünün 3 katını aşar ve ölçülemez olur —
    "durmuş"tan DAHA KÖTÜ bir hâl, daha az değil.

    KAYIT YENİ BİR MEKANİZMA DEĞİL: `bilinen`, harness'in KENDİ damga defterinin anahtarlarıdır —
    yani bu araç bir kalemi DAHA ÖNCE ADIYLA bildirmişse, o kalem tanımı gereği sistemin
    yinelemesini beklediği bir olaydır. Elle yazılmış bir "beklenen olaylar" listesi YOKTUR
    (planın yasağı korunur); kayıt teslimatın kendi geçmişidir. YIĞINI TOPLA, GEÇMİŞİ OLANI TUT.

    ÖLÇÜLEN BEDEL: 15 günlük teslimat simülasyonunda 20 → 28 satır (mesajlı gün yine 4/15), yani
    haftada ~4 satır. Karşılığında göç eden 7 olayın 7'si haftalık ADLI satırını geri aldı.

    `bilinen` YALNIZ PAKETLEMEYİ etkiler: `takili`, `duran`, `olculemedi_ayrinti` ve HER SAYI
    onunla da onsuz da BİREBİR AYNIDIR (çivili). Tespit deterministik kalır.

    `deger` = TOPLAM BANT + ALT-NEDEN BAŞINA BANT (denetim: ilk hâlin çözünürlüğü yetmiyordu).
    İlk hâl `alt_nedenler`i yalnız KÜME olarak taşıyordu; `kadans_olculemedi`nin alfabesi ÜÇ
    elemanlı ve KAPALI olduğu için küme DOYMUŞTU — kimlik tek bir bite inmişti ve ölçüldü ki
    `gozlem_suresi_yetersiz`in 1 → 8 (sekiz kat) yürümesi TEK BİR BİLDİRİM üretmedi. Alt-neden
    başına bant o kapıyı açar ve ham sayıya dönmez: ölçüldü (30 geçiş, terfi açıkken) ham sayı
    3, alt-neden bantları 3, toplam bant 1 kez değişti — ham sayının terfisiz hâli 10'du."""
    toplanacak, gecen, ayrinti = {}, [], []
    for k in kalemler:
        neden = (k.get("kanit") or {}).get("neden")
        if neden not in HUKUM_KURULAMADI_NEDENLERI:
            gecen.append(k)
            continue
        ayrinti.append(k)
        if k.get("kimlik") in bilinen:
            # ADIYLA BİLDİRİLMİŞTİ: yığına karışmaz, kendi satırını korur.
            gecen.append(k)
            continue
        toplanacak.setdefault(neden, []).append(k)

    for neden, uyeler in sorted(toplanacak.items()):
        alt = {}
        for u in uyeler:
            a = (u.get("kanit") or {}).get("alt_neden") or "belirtilmedi"
            alt[a] = alt.get(a, 0) + 1
        # ÖRNEKLER EN SON GÖRÜLENDEN SEÇİLİR, ALFABETİK DEĞİL (denetim: 73 addan alfabetik ilk 8
        # günlerce BİREBİR sabit kaldı ve göç eden 6 durmuş işten 0'ını içeriyordu — yani
        # örnekleme, yapısal olarak SINIFA YENİ GİRENİ gösteremiyordu). "En son ne zaman
        # görüldü" durumsuz, deterministik ve bilgi taşıyan tek sıralamadır: sınıfa en yeni
        # düşen, en son susan olaydır. ÖLÇÜLDÜ: alfabetik liste 30 geçişte 1, en-taze liste 8
        # kez değişti ve son günün başında gerçek sinyal (`yerel_donmus_defter`) duruyordu.
        taze = sorted(uyeler, key=lambda u: (u.get("son_gorulme") or ""), reverse=True)
        adlar = [str((u.get("kanit") or {}).get("olay") or u["ad"]) for u in taze]
        ilkler = [u["ilk_gorulme"] for u in uyeler if u["ilk_gorulme"]]
        sonlar = [u["son_gorulme"] for u in uyeler if u["son_gorulme"]]
        gecen.append(_kalem(
            f"{neden} (toplu)",
            {"buyukluk": _buyukluk_bandi(len(uyeler)),
             "alt_nedenler": {a: _buyukluk_bandi(s) for a, s in sorted(alt.items())}},
            min(ilkler) if ilkler else None, max(sonlar) if sonlar else None,
            {"neden": neden, "toplu": True, "olay_sayisi": len(uyeler), "adet": len(uyeler),
             "alt_neden_sayimi": dict(sorted(alt.items())),
             "ornekler": adlar[:ELENEN_ORNEK_TAVANI], "ornek_tavani": ELENEN_ORNEK_TAVANI,
             "ornek_secimi": "en_son_gorulen",
             "aciklama": ("bu sınıf HÜKÜM KURULAMADI der, 'arıza yok' DEMEZ. Kalem başına satır "
                          "BASILMAZ: kararlı bir ölçülemezlik sınıfı sessizliği her gün bozamaz. "
                          "DAHA ÖNCE ADIYLA BİLDİRİLMİŞ kalemler bu yığına GİRMEZ, kendi "
                          "satırlarını korur; tam liste "
                          "`uv run python ops/bekci_tarama.py --json`")},
            kimlik=f"toplu:{neden}"))
    return gecen, ayrinti


def _bos_kapsam(yol, gun, duran_gun):
    """Ölçülemeyen alanlar `None`dır, `0` DEĞİL (denetim bulgusu 8).

    İlk sürüm zaman ekseni kurulamadığında altı alanı LİTERAL SIFIR döndürüyor, `kapsam_beyani`
    de onları ölçülmüş bir cümle gibi basıyordu: *"0 (olay, sebep) grubu: 0 eşik altı, 0 değeri
    oynadığı için elendi"*. Bu, dosyanın kendi yasakladığı sahte sıfırın birebir örneğiydi —
    üstelik aracın EN ÇOK güvenilmesi gereken cümlesinde."""
    return {"defter": str(yol), "gun": gun, "duran_gun": duran_gun,
            "okunan_satir": 0, "bos_satir": 0,
            "pencere_ici": None, "duran_pencere_ici": None, "pencere_disi": None,
            "pencere_ilk": None, "pencere_son": None, "simdi_kaynagi": None,
            "grup_sayisi": None, "takili_grup": None, "olay_sayisi": None,
            "esik_alti_grup": None, "oynak_deger_grup": None, "duran_ornek_kitligi": None,
            "esik_alti_ornek": [], "oynak_deger_ornek": [], "duran_ornek_kitligi_ornek": [],
            "hukumsuz_toplu": {}, "hukumsuz_adiyla": None, "kusur_dosya_geneli": None,
            "esikler": esikler()}


def esikler():
    """Tüm eşikler TEK yerden — hem hüküm hem beyan buradan okur (poka-yoke)."""
    return {"takili_min_tekrar": TAKILI_MIN_TEKRAR,
            "takili_min_sure_saat": TAKILI_MIN_SURE_SAAT,
            "serbest_akan_oran": SERBEST_AKAN_ORAN,
            "duran_min_ornek": DURAN_MIN_ORNEK, "duran_kat": DURAN_KAT,
            "duran_duzenlilik_tavani": DURAN_DUZENLILIK_TAVANI,
            "duran_gozlem_kat": DURAN_GOZLEM_KAT}


def tara(gun: int = 3, *, duran_gun=None, defter=None, simdi=None, bilinen=None) -> dict:
    """Defteri tarar; `{"takili": [...], "duran": [...], "olculemedi": [...], "kapsam": {...}}`.

    Her kalem `{"ad", "deger", "ilk_gorulme", "son_gorulme", "kanit"}` taşır (Görev 2 sözleşmesi).
    `kapsam` sözleşmenin ÜSTÜNE eklenir ve her cevapla birlikte gider: üç boş liste tek başına
    "arıza yok" DEĞİL, "BU kapsamda bulunamadı" demektir.

    `gun` TAKILI penceresidir. DURAN kendi (daha uzun) penceresini kullanır — `duran_gun`,
    varsayılanı `DURAN_VARSAYILAN_GUN`; iki sınıf ayrı soru sorar, ayrı açıklık ister.
    `simdi` verilmezse defterin SON kaydı "şu an" sayılır (bkz. `_duran_tara` kör noktaları).

    `bilinen` — ÇAĞIRANIN DAHA ÖNCE ADIYLA BİLDİRDİĞİ kalem kimlikleri (harness'in damga
    defterinin anahtarları). YALNIZ `olculemedi` sınıfının PAKETLENMESİNİ etkiler: bu kümedeki
    bir kimlik toplu kaleme girmez, kendi satırını korur (gerekçe ve ölçüm
    `_hukumsuzleri_topla`da). `takili`, `duran`, `olculemedi_ayrinti` ve HER SAYI `bilinen`den
    BAĞIMSIZDIR — tespit deterministik kalır ve bu çivilidir.
    """
    yol = pathlib.Path(defter) if defter is not None else VARSAYILAN_DEFTER
    d_gun = DURAN_VARSAYILAN_GUN if duran_gun is None else int(duran_gun)
    kapsam = _bos_kapsam(yol, gun, d_gun)

    if not yol.is_file():
        # DEFTER YOK, ÜÇ BOŞ LİSTE DEĞİL. Boş liste "arıza yok" diye okunur; varsayılan deftere
        # sessizce düşmek de aynı yalanın başka hâlidir.
        return {"takili": [], "duran": [],
                "olculemedi": [_kalem("defter_yok", None, None, None,
                                      {"neden": "defter_yok", "adet": 0, "defter": str(yol),
                                       "aciklama": ("okunacak defter YOK — bu bir 'arıza yok' "
                                                    "bulgusu DEĞİLDİR, ölçüm hiç yapılamadı")})],
                "olculemedi_ayrinti": [], "kapsam": kapsam}

    an_simdi = (_an_coz(simdi) if isinstance(simdi, str) else simdi) if simdi is not None \
        else _son_zaman(yol)
    if an_simdi is None:
        # Zaman ekseni yok: satırları saymak için yine de bir geçiş yapılır, ama pencere
        # kurulamadığı için İKİ SINIF DA ölçülemez ve kapsamın ölçülmemiş alanları None kalır.
        _, kusurlar, okunan, bos, _ = _oku(yol, dt.datetime.max.replace(tzinfo=dt.timezone.utc),
                                           dt.datetime.max.replace(tzinfo=dt.timezone.utc))
        kapsam["okunan_satir"], kapsam["bos_satir"] = okunan, bos
        olculemedi = _kusurlari_topla(kusurlar)
        olculemedi.append(_kalem(
            "zaman_ekseni_yok", None, None, None,
            {"neden": "zaman_ekseni_yok", "adet": okunan,
             "aciklama": ("hiçbir kaydın zamanı çözülemedi — pencere kurulamadı, iki sınıf da "
                          "ölçülemedi; boş liste 'temiz' demek DEĞİLDİR")}))
        return {"takili": [], "duran": [], "olculemedi": olculemedi,
                "olculemedi_ayrinti": [], "kapsam": kapsam}

    kapsam["simdi_kaynagi"] = "cagiran" if simdi is not None else "defterin_son_kaydi"
    genis_baslangic = an_simdi - dt.timedelta(days=max(gun, d_gun))
    tum, kusurlar, okunan, bos, pencere_disi = _oku(yol, genis_baslangic, an_simdi)
    kapsam.update(okunan_satir=okunan, bos_satir=bos, pencere_disi=pencere_disi)

    takili_baslangic = an_simdi - dt.timedelta(days=gun)
    duran_baslangic = an_simdi - dt.timedelta(days=d_gun)
    takili_pencere = [k for k in tum if k.an >= takili_baslangic]
    duran_pencere = [k for k in tum if k.an >= duran_baslangic]
    kapsam.update(pencere_ici=len(takili_pencere), duran_pencere_ici=len(duran_pencere),
                  pencere_ilk=takili_baslangic.isoformat(), pencere_son=an_simdi.isoformat(),
                  duran_pencere_ilk=duran_baslangic.isoformat())

    olculemedi = _kusurlari_topla(kusurlar)
    if len(tum) < DURAN_MIN_ORNEK and pencere_disi > len(tum):
        # PENCERE ÖLÇÜLEMEYECEK KADAR BOŞ, AMA DEFTER DOLU (denetim bulgusu 8). Tek bir ileri
        # tarihli kayıt (`ts: "2099-…"`, saat kayması, elle düzenleme) `simdi`yi öne iter;
        # pencerede yalnız O kayıt kalır ve üç liste de sessizce boş döner. YENİ EŞİK
        # UYDURULMADI: ölçüt, zaten beyan edilmiş `DURAN_MIN_ORNEK`tir — en geniş pencere ritim
        # kuracak kadar kayıt taşımıyorsa ve defterin ÇOĞU dışarıda kalmışsa, "şu an"
        # referansının kendisi şüphelidir. `defter_yok` için konan dürüstlük kapısı buraya da
        # konur: dolu bir defter "temiz" diye okunamaz.
        olculemedi.append(_kalem(
            "pencere_bos", None, None, None,
            {"neden": "pencere_bos", "adet": okunan, "defter": str(yol),
             "pencere_ilk": duran_baslangic.isoformat(), "pencere_son": an_simdi.isoformat(),
             "pencere_ici": len(tum), "pencere_disi": pencere_disi,
             "aciklama": ("defter DOLU ama en geniş pencerede ölçüm yapılacak kadar kayıt YOK — "
                          "büyük olasılıkla ileri tarihli bir damga 'şu an'ı öne itti. Boş "
                          "liste 'arıza yok' DEĞİL")}))

    # KANIT, HÜKMÜN KENDİ PENCERESİNDEN (dal denetimi H1 — gerekçe `_sifirlanan_alanlar`da).
    # Eskiden `tum` (en geniş pencere) veriliyordu ve 3 günlük TAKILI hükmünü bağlıyordu.
    sifirlanan = _sifirlanan_alanlar(takili_pencere)
    takili, takili_olculemez, t_sayac = _takili_tara(takili_pencere, sifirlanan)
    duran, duran_olculemez, d_sayac = _duran_tara(duran_pencere, an_simdi)
    kapsam.update(t_sayac)
    kapsam.update(d_sayac)

    olculemedi.extend(takili_olculemez)
    olculemedi.extend(duran_olculemez)
    olculemedi, ayrinti = _hukumsuzleri_topla(
        olculemedi, frozenset(bilinen or ()))
    olculemedi.sort(key=lambda x: (-x["kanit"].get("adet", 0), x["ad"]))
    ayrinti.sort(key=lambda x: (-x["kanit"].get("adet", 0), x["ad"]))
    kapsam["hukumsuz_toplu"] = {k["kanit"]["neden"]: k["kanit"]["olay_sayisi"]
                                for k in olculemedi if k["kanit"].get("toplu")}
    # ADIYLA GEÇENLER AYRICA SAYILIR: toplu sayı ile teslim listesi arasındaki farkı gizlemek,
    # toplamanın kendi dürüstlük iddiasını (görünmez eleme yoktur) delerdi.
    # ZAMANI ÇÖZÜLEMEYEN KUSUR SATIRLARI PENCERE BEYANININ İSTİSNASIDIR — sayısı beyanda geçer.
    kapsam["kusur_dosya_geneli"] = sum(
        k["kanit"].get("adet", 0) for k in olculemedi
        if k["kanit"].get("pencere") == "dosyanin_tamami")
    kapsam["hukumsuz_adiyla"] = sum(
        1 for k in olculemedi
        if not k["kanit"].get("toplu")
        and k["kanit"].get("neden") in HUKUM_KURULAMADI_NEDENLERI)
    return {"takili": takili, "duran": duran, "olculemedi": olculemedi,
            "olculemedi_ayrinti": ayrinti, "kapsam": kapsam}


def kapsam_beyani(sonuc: dict) -> str:
    """Kapsam cümlesini SONUCUN KENDİSİNDEN üretir — elle yazılmış sabit bir cümleden değil.
    Poka-yoke: pencere ya da eşikler değişince bu cümle KENDİLİĞİNDEN değişir. Ayrı tutulsaydı
    biri güncellenip öteki unutulurdu ("mekanizma düzeltildi, İDDİA eski kaldı")."""
    k = sonuc.get("kapsam") or {}
    if not k.get("okunan_satir"):
        return (f"{k.get('defter', '?')} OKUNAMADI ya da BOŞ — sonuç GEÇERSİZ; "
                f"boşluğu 'arıza yok' diye OKUMA")

    def s(alan):
        """Ölçülmemiş alan `?` basar, `0` DEĞİL — sahte sıfır beyanın içine giremez."""
        d = k.get(alan)
        return "?" if d is None else d

    return (f"{k['defter']} · {k['okunan_satir']} satır · takılı penceresi son {k['gun']} gün "
            f"({s('pencere_ici')} kayıt), duran penceresi son {k['duran_gun']} gün "
            f"({s('duran_pencere_ici')} kayıt) · "
            f"pencere sonu {k['pencere_son']} ('şu an' kaynağı: {s('simdi_kaynagi')}), "
            f"dışarıda kalan {s('pencere_disi')} kayıt · "
            f"{s('grup_sayisi')} (olay, sebep) grubu: {s('takili_grup')} takılı, "
            f"{s('esik_alti_grup')} eşik altı, {s('oynak_deger_grup')} değeri oynadığı için "
            f"elendi (örnekler: {k.get('oynak_deger_ornek') or '—'}) · "
            f"{s('olay_sayisi')} olaydan {s('duran_ornek_kitligi')} tanesi örnek kıtlığından "
            f"hükümsüz (örnekler: {k.get('duran_ornek_kitligi_ornek') or '—'}) · "
            # HÜKÜM KURULAMADI SINIFI SAYIYLA BEYAN EDİLİR: teslimatta tek satıra indi, ama
            # KAÇ olayı kapsadığı kapsam cümlesinden düşerse toplama bir SUSTURMAYA dönerdi.
            f"hüküm kurulamadı (toplu): {k.get('hukumsuz_toplu') or '—'}, "
            f"ayrıca {s('hukumsuz_adiyla')} tanesi ADIYLA · "
            f"eşikler {k['esikler']} — BU KAPSAMIN DIŞI GÖRÜLMEDİ (TEK İSTİSNA: zamanı "
            f"çözülemeyen {s('kusur_dosya_geneli')} kusur satırı DOSYANIN TAMAMINDAN gelir, "
            f"pencereye bağlanamaz); boş liste 'arıza yok' değil 'BU KAPSAMDA bulunamadı' "
            f"demektir")


def _bas(sonuc: dict) -> None:
    # AYRINTI CLI'DA BASILIR: teslimat listesi toplu kaleme indi (dal denetimi H2), ama
    # operatörün "hangi olaylar?" sorusunun cevabı BİR KOMUT ötede olmalı — mesajdaki toplu
    # kalem zaten bu betiği işaret ediyor.
    for baslik, anahtar in (("TAKILI (süregelen)", "takili"),
                            ("DURAN (artık gelmiyor)", "duran"),
                            ("ÖLÇÜLEMEDİ (sıfır DEĞİL)", "olculemedi"),
                            ("ÖLÇÜLEMEDİ — TEKİL HÜKÜM (teslimatta TOPLU gider)",
                             "olculemedi_ayrinti")):
        kalemler = sonuc.get(anahtar) or []
        print(f"\n## {baslik} — {len(kalemler)} kalem")
        for kalem in kalemler:
            print(f"- {kalem['ad']}")
            print(f"    deger : {kalem['deger']}")
            print(f"    aralik: {kalem['ilk_gorulme']} → {kalem['son_gorulme']}")
            print(f"    kanit : {kalem['kanit']}")


def _pozitif(metin):
    sayi = int(metin)
    if sayi <= 0:
        raise argparse.ArgumentTypeError("gün sayısı POZİTİF olmalı — sıfır/negatif pencere "
                                         "sessizce boş sonuç üretirdi")
    return sayi


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--gun", type=_pozitif, default=3,
                    help="TAKILI penceresi, gün (varsayılan 3)")
    ap.add_argument("--duran-gun", type=_pozitif, default=None,
                    help=f"DURAN penceresi, gün (varsayılan {DURAN_VARSAYILAN_GUN})")
    ap.add_argument("--defter", default=None, help=f"defter yolu (varsayılan {VARSAYILAN_DEFTER})")
    ap.add_argument("--json", action="store_true", help="ham sonucu JSON olarak bas")
    args = ap.parse_args(argv)

    sonuc = tara(args.gun, duran_gun=args.duran_gun, defter=args.defter)
    if args.json:
        print(json.dumps(sonuc, ensure_ascii=False, indent=2, default=str))
    else:
        _bas(sonuc)
    if not (sonuc["takili"] or sonuc["duran"]):
        print("\nTAKILI/DURAN BULGU YOK — bu 'sistem sağlıklı' DEMEK DEĞİLDİR. Üç şeyden biri "
              "olabilir: (1) gerçekten temiz; (2) durum pencerenin DIŞINDA kaldı ya da "
              "penceresinden uzun bir kadansa sahip; (3) olay bu deftere hiç basılmıyor.")
    # HER koşumda, bulgu olsun olmasın: önce NEREYE bakıldı, sonra orada NE ölçülemedi.
    print(f"\n# taranan kapsam: {kapsam_beyani(sonuc)}")
    print(f"# ölçülemedi: {len(sonuc['olculemedi'])} teslim kalemi / "
          f"{len(sonuc.get('olculemedi_ayrinti') or [])} tekil hüküm "
          f"(ayrıştırılamayan/alansız satır ve hükmü kurulamayan grup — SIFIR SAYILMADI)")
    # ÇIKIŞ KODU: 0 = ölçüm YAPILDI (bulgu olsun olmasın), 2 = ölçüm YAPILAMADI.
    # "Bulgu yok" bir HATA DEĞİLDİR (denetim bulgusu 10): ilk sürüm boş sonuçta 1 dönüyordu ve
    # bunu koşturacak bir birim, sağlıklı her günü BAŞARISIZ koşum olarak raporlardı — bekçinin
    # kendisi gürültü kaynağı olurdu.
    olcum_yok = {"defter_yok", "zaman_ekseni_yok", "pencere_bos"}
    if any(k["kanit"]["neden"] in olcum_yok for k in sonuc["olculemedi"]):
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
