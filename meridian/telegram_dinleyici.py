"""telegram_dinleyici.py — konuşan bot filosunun Telegram kanalı: operatörün mesajını alır, doğru bota
yönlendirir, cevabı aynı sohbete YANIT olarak geri verir (spec 2026-09-29 §3.5, operatör kararı K3).

NE YAPAR. `getUpdates` uzun yoklamasıyla (`guncellemeleri_al`) gelen her güncellemeyi `isle` işler:
`yonlendir` önce yetkiyi sınar, sonra hedef botu seçer — `@ad` öneki (`@Bekci:`/`@KARNE,`/`@bekçi`
biçimleri dahil; Türkçe harf `kadro.ad_katla` ile katlanır) → o bot; bir bot cevabına (`💬 @ad · <oturum>`
ilk satırı; çok parçalı cevabın her parçası ve ara bildirim de bu satırı taşır) yanıt → aynı bot; bir rapora
yanıt (ilk satır kadrodaki bir aktif botun imzasıyla başlar,
`kadro.imzadan_bot`) → o bot; hiçbiri yoksa `@sef`. Cevap `bota_sor(bot, metin, kanal, oturum)` ile
alınır ve `💬 @ad · <oturum>` imzasıyla gönderilir.

YANIT BAĞLAMI (Tur 3, son inceleme I-1). (a) Operatörün mesajı bir YANITSA, yanıtlanan metin bota
`<<<VERI:yanitlanan_mesaj>>> … <<<VERI-SON:yanitlanan_mesaj>>>` çitiyle, operatörün sözlerinden ÖNCE
gider — "bu kalem ne?" hangi kalemi sorduğunu ancak alıntıyla bilir. Çit ve jeton etkisizleştirmesi
`skill_gorus_llm._veri_bloku`dan İTHAL edilir (tek kaynak; `sohbet` de oradan alır). Alıntı Telegram
mesajıdır, yani en çok 4096 karakter — ayrıca kırpılmaz. (b) Oturum kimliği: bot cevabına yanıtta
cevabın imza satırındaki oturum SÜRER (Telegram `reply_to_message`ı yalnız BİR düzey iç içe verir,
zincir yürünemez — durum cevabın kendisinde taşınır); rapora yanıt `tg-<bot>-r<rapor mesajı>`,
yanıtsız mesaj `tg-<bot>-<YYYYAAGG>`. (c) KOMUT İSTİSNASI (Tur 2, Görev 1 incelemesi I-1): operatörün
sözleri `bot_kanal.komut_oneki` ile bir komutsa (`hatırla:` · `unut:` · `onayla:` · `geri al:`) çit KURULMAZ — çit
öne konsaydı `bota_sor` öneki göremez ve not MODELE giderdi; `hatırla` yanıtı nota yanıtlanan mesajın ilk İÇERİK
satırını kaynak etiketi olarak ekler, gövdesiz `unut:` yanıtı aynı satırı sorgu yapar (`_komut_giden`; tek kural
`bot_kanal.alinti_icerik_satiri` — sohbet imzası ve araçsız-veri uyarısı içerik sayılmaz).

HİZMET (Parça 1b G4 Görev 3). `python -m meridian.telegram_dinleyici` → `main()` → `dongu(bota_sor=bot_kanal.bota_sor)`
— üretim `bota_sor`u (gerçek taşıyıcı + hafıza). Birim `deploy/oracle-a1/meridian-telegram.service` (A0 rolü kopyalar,
ETKİN ETMEZ; credential drop-in'i G3b sır dilimine ertelendi — birim şerhi). Çivi: tests/test_telegram_birimi_v602.py.

DEĞİŞMEZLER.
  * YALNIZ OPERATÖR (Tur 3, I-3): mesaj yalnız `chat.type == "private"` VE
    `from.id == chat.id == TELEGRAM_CHAT_ID` ise kabul edilir — özel sohbette sohbet kimliği KULLANICI
    kimliğidir, yani "yalnız operatör" sözü yapısaldır. Grup/kanal (kimlik eşleşse bile) ve başka
    gönderen YABANCIDIR: CEVAP VERİLMEZ, kadro bile okunmaz; ret SAYILIR (`bot_yabanci_mesaj`) ve
    olayda sohbet kimliği HAM değil sha256'nın ilk 12 hanesiyle durur. `dongu`, pozitif tamsayı
    olmayan bir `TELEGRAM_CHAT_ID` ile (negatif = grup/kanal) HİÇ BAŞLAMAZ.
  * TEK TESLİMAT YOLU: varsayılan gönderici `notify.yanitla`dır — `send` ile aynı Telegram yolu ve
    aynı `scrub`; bu modül dışarıya kendi başına METİN göndermez. `getUpdates` çağrısı bir GELEN
    okumadır: gövdesi yalnız ofset/bekleme taşır.
  * JETON LOG'A DÜŞMEZ: yoklama hatası olayı yalnız istisnanın SINIF adını ve (HTTP hatasında)
    durum KODUNU taşır — `e.url`/`e.filename`/`e.msg`/`str(e)` jetonlu URL taşıyabilir, basılmaz; bot
    hatası da operatöre sınıf adıyla söylenir. Jeton her turda `secrets.get` ile YENİDEN okunur
    (pano değiştirirse yeniden başlatma gerekmez; süreç-içi önbellek TTL'i kadar gecikme olabilir).
  * SESSİZ HATA YOK: `bota_sor` düşerse operatöre "şu an cevap veremiyor" yanıtı gider VE
    `bot_sohbet_hatasi` olayı yazılır; döngü ölmez. Pasif/bilinmeyen bota yazılan mesaj da
    cevapsız kalmaz (ne olduğu söylenir).
  * EN-ÇOK-BİR-KEZ + GERİ ÇEKİLME (Tur 2): ofset güncelleme işlenmeden ÖNCE ilerler ve yazılır;
    tek bir güncellemenin hatası (`telegram_isle_hatasi`) ya da ofset yazım hatası döngüyü
    düşürmez. Yoklama hatası `None` döner ve `dongu` 1, 2, 4, … 60 sn geri çekilir — ağ/jeton
    arızasında API'yi dövüp olay defterini şişiren sıcak döngü yok. Ayrıntı `dongu` docstring'inde.
  * İLK KOŞUM BİRİKİMİ YENİDEN OYNATMAZ (G4 Görev 3, Rol-1 kararı 5): `telegram_ofset.json` YOKSA ilk yoklama
    BLOKLAMAZ (`timeout: 0` — yalnız ZATEN birikmiş olanı alır; uzun yoklama operatörün ilk TAZE mesajını da
    "birikmiş" sayıp yutardı) ve dönen güncellemeler İŞLENMEZ: en yüksek `update_id + 1` yazılır, olay
    `telegram_ilk_ofset` (atlanan sayısı + yeni ofset). Sayfa dolu gelirse (`GUNCELLEME_SAYFASI`) birikim sürüyor
    olabilir — atlama bir tur daha sürer. Gerekçe: ofset 0 ile Telegram 24 saatlik birikimi yeniden verir; dinleyici ilk
    açılışında günlerce önceki soruları (ve pano kurulumundaki `merhaba`yı) cevaplardı. Dosya VARSA bugünkü davranış.
  * CEVAP 4096'YA BÖLÜNÜR (plan Review Focus 3): `sendMessage` metin tavanı `TELEGRAM_TAVANI`. Bölme `notify.scrub`'DAN
    SONRA yapılır — sınırı ortadan kesen bir anahtar iki yarım hâlinde desenden kaçmasın, scrub'ın UZATTIĞI metin
    (`://u:p@` → `://***:***@`) tavanı sonradan aşmasın (`yanitla`nın parça başına scrub'ı scrub'lı metinde
    büyümez). İMZA HER PARÇADA (Tur 2, Rol-1 kararı — yönlendirme doğruluğu > sadelik): her parçanın ilk satırı sohbet
    imzasıdır, çok parçalıda sonunda `PARCA_EKI` (` (i/n)`); `_SOHBET_IMZA` (imza sabitleriyle birlikte `bot_kanal`dan
    ithal) eki tanır ve oturumu eksiz yakalar, yani operatör HANGİ parçaya yanıt verirse versin aynı bot + aynı
    oturum. Tek parça bugünkü biçimde (eksiz). Tavan imza
    satırını ve eki SAYAR. `reply_to` YALNIZ ilk parçada. Ayrıntı `imzali_parcalar`, `parcala`.
    Teslim edilemeyen parça SESSİZ değildir (`telegram_parca_teslim_hatasi`: bot, parça no/toplam, sınıf) ve kalan
    parçalar YİNE denenir.
  * ARA BİLDİRİM CEVAPTAN SONRA ASLA GİTMEZ (Review Focus 4): `bota_sor` `ARA_BILDIRIM_ESIGI_S` içinde dönmezse
    enjekte `bildir` ile BİR kez ara bildirim gider — 1. satır sohbet imzası (eksiz; ona yanıt da aynı bota ve oturuma
    gider), 2. satır `ARA_BILDIRIM`; operatörün mesajına yanıt olarak. Ayrıntı `_AraBildirim`.
    `bildir` `gonder`den AYRIDIR: tek teslimat yolu yine `notify.yanitla`dır, ama "cevap" ile "bekleme işareti"
    ayrı sayılır (v592'nin `gidenler[0]` sözleşmesi cevabı gösterir).
  * YASA 6: `telegram_ofset.json`in yazarı ve okuyucusu `dongu`nun kendisidir (süreç yeniden
    başladığında işlenmiş güncelleme ikinci kez cevaplanmasın diye KALICI); aynı modül olduğu için
    statik graf dış okuyucu göremez — beyanı `codelaw.DECLARED_SINKS`te gerekçesiyle durur.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import threading
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone

from . import bot_kanal, kadro as _kadro, notify, obs, secrets, store
# KOMUT TESPİTİ, YANIT ÇİTİNİN ADI, KAYNAK ETİKETİ, ALINTININ İÇERİK SATIRI ve SOHBET İMZASI (üretici sabitleri +
# tanıyıcı) İTHAL EDİLİR, KOPYALANMAZ — sahibi `bot_kanal` (bota_sor'un dağıtımı ve dönüş kaydı da onları kullanır;
# G4 Görev 1 Tur 3: dönüş kaydı yanıt çitini hafızaya yazmadan çözer; G4 kalıntıları M-2/M-3, 2026-10-01: hatırla
# etiketi, dönüş kaydı ve gövdesiz `unut:` sorgusu TEK içerik-satırı kuralından geçer — imza, araçsız-veri uyarısı ve
# ara bildirim satırı içerik sayılmaz; imza deseni ve `ARA_BILDIRIM` bu yüzden `bot_kanal`a taşındı).
from .bot_kanal import (ALINTI_CIT_ADI, ARA_BILDIRIM, OTURUM_AYRACI, PARCA_EKI, SOHBET_IMZA, _SOHBET_IMZA,
                        alinti_icerik_satiri, kaynak_etiketi, komut_oneki)
# ÇİT GRAMERİ İTHAL EDİLİR, KOPYALANMAZ — sahibi `skill_gorus_llm` (`sohbet` de oradan alır).
from .skill_gorus_llm import _veri_bloku

VARSAYILAN_BOT = "sef"
OFSET_DOSYASI = "telegram_ofset.json"
_ONEK = re.compile(r"^@([A-Za-zÇĞİÖŞÜçğıöşü_]+)[:,]?\s*(.*)$", re.S)
_POZITIF_TAMSAYI = re.compile(r"[1-9]\d*")
#: Telegram `sendMessage` metin tavanı (Bot API: "1-4096 characters"). Sayım UTF-16 KOD BİRİMİYLE yapılır: Telegram'ın
#: karakteri kod noktası mı UTF-16 birimi mi saydığı ÖLÇÜLMEDİ (2026-09-30) — BMP dışı karakteri (emoji) iki saymak
#: güvenli taraftır: en kötü hâlde gereksiz bir bölme, hiçbir hâlde "message is too long" reddi.
TELEGRAM_TAVANI = 4096
#: Bir `getUpdates` yoklamasının en çok getirdiği güncelleme (Bot API `limit`, 1–100). Gövdede AÇIK gönderilir ki ilk
#: koşumun "sayfa dolu → birikim sürüyor olabilir" kararı sunucunun varsayılanına değil bu sayıya bağlı olsun.
GUNCELLEME_SAYFASI = 100
#: Uzun yoklamanın sunucu tarafı bekleme süresi (sn). İlk koşum yoklaması 0 ile (bloklamadan) yapılır — `dongu`.
UZUN_YOKLAMA_S = 50
#: `bota_sor` bu kadar saniyede dönmezse operatöre bir kez ara bildirim gider (Rol-1 kararı 4, G4): 1. satır sohbet
#: imzası (EKSİZ), 2. satır `ARA_BILDIRIM` (metni `bot_kanal`dan ithal — içerik kuralı onu atlar, G4 kalıntıları Tur 2)
#: — imza sayesinde ona verilen yanıt da aynı bota ve oturuma gider (Tur 2).
ARA_BILDIRIM_ESIGI_S = 8


@dataclass(frozen=True)
class Yonlendirme:
    bot: str | None
    metin: str
    neden: str


def yonlendir(mesaj: dict, yetkili_sohbet: str, kadro=None) -> Yonlendirme:
    """Mesajın hedef botunu seçer. `neden` ∈ onek · imza · sohbet_imza · varsayilan · yabanci ·
    bos · pasif_bot · bilinmeyen_bot. YETKİ sınaması HER ŞEYDEN önce gelir: özel sohbet VE
    gönderen = sohbet = yetkili kimlik (grup kimliği eşleşse bile grup yabancıdır)."""
    sohbet, gonderen = mesaj.get("chat") or {}, mesaj.get("from") or {}
    if not (sohbet.get("type") == "private"
            and str(gonderen.get("id")) == str(sohbet.get("id")) == str(yetkili_sohbet)):
        return Yonlendirme(None, "", "yabanci")
    metin = (mesaj.get("text") or "").strip()
    if not metin:
        return Yonlendirme(None, "", "bos")
    k = kadro if kadro is not None else _kadro.kadro_yukle()
    m = _ONEK.match(metin)
    if m:
        b = _kadro.bot_bul(m.group(1), k)
        if b is None:
            return Yonlendirme(None, metin, "bilinmeyen_bot")
        return Yonlendirme(b.ad, m.group(2).strip(), "onek" if b.durum == "aktif" else "pasif_bot")
    yanit = ((mesaj.get("reply_to_message") or {}).get("text") or "")
    ilk = yanit.split("\n", 1)[0].strip()
    s = _SOHBET_IMZA.match(ilk)
    if s and (b := _kadro.bot_bul(s.group(1), k)) and b.durum == "aktif":
        return Yonlendirme(b.ad, metin, "sohbet_imza")
    if (b := _kadro.imzadan_bot(yanit, k)) is not None:
        return Yonlendirme(b.ad, metin, "imza")
    return Yonlendirme(VARSAYILAN_BOT, metin, "varsayilan")


def oturum_kimligi(bot: str, mesaj: dict, bugun: str) -> str:
    """AYNI botun cevabına yanıtsa o cevabın imza satırındaki oturum SÜRER; başka yanıtsa
    `tg-<bot>-r<reply_to_message_id>`; yanıt değilse `tg-<bot>-<bugun>`. Başka botun oturumu
    devralınmaz (imzadaki bot ve oturum öneki `bot` ile eşleşmeli)."""
    yanitlanan = mesaj.get("reply_to_message") or {}
    ilk = (yanitlanan.get("text") or "").split("\n", 1)[0].strip()
    s = _SOHBET_IMZA.match(ilk)
    if s and s.group(1) == bot and s.group(2) and s.group(2).startswith(f"tg-{bot}-"):
        return s.group(2)
    r = yanitlanan.get("message_id")
    return f"tg-{bot}-r{r}" if r is not None else f"tg-{bot}-{bugun}"


def _bota_giden(mesaj: dict, metin: str) -> str:
    """Yanıtsa: yanıtlanan metin VERİ çitinde, ardından operatörün sözleri; değilse sözlerin kendisi."""
    alinti = (mesaj.get("reply_to_message") or {}).get("text") or ""
    if not alinti.strip():
        return metin
    return f"{_veri_bloku(ALINTI_CIT_ADI, alinti)}\n{metin}"


def _komut_giden(mesaj: dict, metin: str, komut: tuple[str, str]) -> str:
    """Komut bota ÇİTSİZ çıplak söz olarak gider (çit öne konsaydı `bota_sor` öneki göremez, not MODELE
    giderdi — Tur 2, inceleme I-1). Yanıt kipinde iki deterministik ek, İKİSİ DE yanıtlanan mesajın ilk İÇERİK
    satırından (`bot_kanal.alinti_icerik_satiri` — TEK KURAL, G4 kalıntıları M-2/M-3: boş satır, sohbet imzası ve
    araçsız-veri uyarısı atlanır; scrub SONRA ≤`KAYNAK_ETIKETI_TAVANI`):
      * `hatırla` + DOLU gövde (Rol-1 kararı) → nota kaynak etiketi ` (yanıt: <içerik satırı>)` — biçim
        `bot_kanal.kaynak_etiketi`nde (tek kaynak; dönüş kaydı da onu kullanır).
      * `unut` + BOŞ gövde (G4 Görev 2, Rol-1 kararı 5) → içerik satırı SORGU olur: `unut: <satır>`. "Bunu unut"
        demenin yolu.
    Dolu gövdeli `unut`, gövdesiz `hatırla` (bota_sor "neyi?" diye sorsun), `onayla`/`geri al` ve içeriksiz alıntı
    (yalnız imza/uyarı) OLDUĞU GİBİ gider — sorgu da etiket de uydurulmaz."""
    ad, govde = komut
    alinti = ((mesaj.get("reply_to_message") or {}).get("text") or "").strip()
    if not alinti:
        return metin
    if ad == "hatirla" and govde:
        etiket = kaynak_etiketi(alinti)
        return f"{metin} {etiket}" if etiket else metin
    if ad == "unut" and not govde:
        sorgu = alinti_icerik_satiri(alinti)
        return f"{metin.rstrip()} {sorgu}" if sorgu else metin
    return metin


def _sha(x) -> str:
    return hashlib.sha256(str(x).encode()).hexdigest()[:12]


def _kod_birimi(c: str) -> int:
    """Bir kod noktasının UTF-16 kod birimi sayısı: BMP dışı (U+FFFF üstü — emoji vb.) iki, diğerleri bir."""
    return 2 if ord(c) > 0xFFFF else 1


def utf16_uzunluk(metin: str) -> int:
    """UTF-16 kod birimi sayısı. `encode("utf-16")` KULLANILMAZ: eşsiz vekil (surrogate) taşıyan bir model cevabı
    `UnicodeEncodeError` ile bölmeyi — dolayısıyla cevabı — düşürürdü."""
    return sum(_kod_birimi(c) for c in metin)


def _karakterle_kes(satir: str, sinir: int) -> tuple[str, str]:
    """`satir`ı ilk `sinir` UTF-16 birimi SIĞAN kod noktasından keser: (baş, kalan). Python `str` dilimi bir kod
    noktasını bölemez — emoji iki yarıya ayrılmaz. En az bir kod noktası alınır (ilerleme garantisi)."""
    uz = 0
    for i, c in enumerate(satir):
        if uz + _kod_birimi(c) > sinir:
            k = max(i, 1)
            return satir[:k], satir[k:]
        uz += _kod_birimi(c)
    return satir, ""


def parcala(metin: str, *, ilk_butce: int, butce: int = TELEGRAM_TAVANI) -> list[str]:
    """`metin`i her biri tavana sığan parçalara böler; ilk parçanın bütçesi `ilk_butce`, sonrakilerin `butce`
    (`imzali_parcalar` ikisini de imza satırı + ek kadar kısaltır — her parça imzalıdır). Satır SINIRINDA böler
    (parça sınırındaki satır sonu düşer — yalnız satır sınırında bölünen
    metinde `"\\n".join(parcalar) == metin`); tek başına bütçeyi aşan satır kod noktası sınırında kesilir
    (`_karakterle_kes`; o kesimde ayraç yoktur). Uzunluk `utf16_uzunluk` ile.
    Boş/yalnız boşluk parça ÜRETİLMEZ (boş gövdeli bir `(i/n)` mesajı gürültüdür) — ilk parça hariç: boş cevabın da
    tek mesajı vardır.
    Boş `metin` → `[""]` (bugünkü tek mesaj)."""
    parcalar: list[str] = []
    cari: str | None = None
    cari_uz = 0
    for satir in metin.split("\n"):
        while True:
            sinir = max(2, ilk_butce if not parcalar else butce)
            ek = satir if cari is None else "\n" + satir
            ek_uz = utf16_uzunluk(ek)
            if cari_uz + ek_uz <= sinir:
                cari, cari_uz = (ek if cari is None else cari + ek), cari_uz + ek_uz
                break
            if cari is not None:
                parcalar.append(cari)
                cari, cari_uz = None, 0
                continue
            bas, satir = _karakterle_kes(satir, sinir)
            parcalar.append(bas)
    if cari is not None:
        parcalar.append(cari)
    return parcalar[:1] + [p for p in parcalar[1:] if p.strip()]


def imzali_parcalar(imza: str, govde: str) -> list[str]:
    """`govde`yi HER BİRİ ilk satırında `imza` taşıyan mesajlara böler (Tur 2, Rol-1 kararı: yönlendirme doğruluğu >
    sadelik). Tek parça: `"<imza>\n<gövde>"` — bugünkü biçim, EKSİZ. Çok parça: imza satırının sonuna `PARCA_EKI`.
    TAVAN imza satırını ve eki SAYAR: bütçe en uzun ek (` (n/n)`) için ayrılır; ekin hane sayısı parça sayısıyla büyür,
    bu yüzden bölme hane sayısı sabitlenene dek yinelenir (bütçe yalnız küçülür → parça sayısı yalnız büyür → sonlanır)."""
    butce = TELEGRAM_TAVANI - utf16_uzunluk(imza) - 1
    parcalar = parcala(govde, ilk_butce=butce, butce=butce)
    if len(parcalar) == 1:
        return [f"{imza}\n{parcalar[0]}"]
    toplam = len(parcalar)
    while True:
        ek_butce = butce - utf16_uzunluk(PARCA_EKI.format(no=toplam, toplam=toplam))
        parcalar = parcala(govde, ilk_butce=ek_butce, butce=ek_butce)
        if len(str(len(parcalar))) <= len(str(toplam)):
            break
        toplam = len(parcalar)
    toplam = len(parcalar)
    return [f"{imza}{PARCA_EKI.format(no=no, toplam=toplam)}\n{parca}" for no, parca in enumerate(parcalar, 1)]


def _parcali_gonder(gonder, bot: str, imza: str, cevap: str, reply_to) -> None:
    """Cevabı ÖNCE scrub'lar, SONRA böler (modül başlığı, CEVAP 4096'YA BÖLÜNÜR); her parça imzalıdır
    (`imzali_parcalar`), `reply_to` YALNIZ ilk parçada. Parça başına teslim hatası olay olur ve kalan parçalar yine
    denenir."""
    mesajlar = imzali_parcalar(imza, notify.scrub(cevap))
    toplam = len(mesajlar)
    for no, metin in enumerate(mesajlar, 1):
        hedef = reply_to if no == 1 else None
        try:
            teslim = gonder(metin, hedef)
        except Exception as e:  # sinyalli: olay (bot, parça no/toplam, yalnız sınıf adı); kalan parçalar YİNE denenir
            obs.warn("telegram_parca_teslim_hatasi", bot=bot, parca=no, toplam=toplam, sinif=type(e).__name__)
            continue
        if not teslim:
            obs.warn("telegram_parca_teslim_hatasi", bot=bot, parca=no, toplam=toplam, sinif="teslim_edilemedi")


class _AraBildirim:
    """`bota_sor` uzun sürerse BİR kez "<imza>\n<`ARA_BILDIRIM`>" — ve cevaptan SONRA ASLA (plan Review Focus 4).

    ÜÇ KATMAN, üçü de gerekli: (1) `kapat()` cevap gönderiminden ÖNCE kilit altında `_kapandi` bayrağını kurar — iplik
    beklemeyi bitirmiş ama iptal ona yetişmemişse (`Timer.cancel` koşmakta olan işlevi durdurmaz) işlev kilidi alınca
    bayrağı görür ve SUSAR; (2) işlev koşarken `kapat()` kilidi bekler — ara bildirim o anda gidiyorsa cevaptan ÖNCE
    tamamlanır (ters sıra "cevap geldi, sonra düşünüyor…" demekti). BEDEL: en kötü hâlde cevap, uçuştaki bildirim
    gönderimi bitene dek gecikir — ve bu süre `notify._post`un zaman aşımıyla SINIRLI DEĞİLDİR (G4 dal sonu M-6; karar
    T3 M-5 durur, yalnız sayı düzeltildi): zaman aşımı soket İŞLEMİ başınadır (bağlanma, el sıkışma, her okuma; duvar
    saati değil) ve DNS çözümlemesini (`getaddrinfo`) HİÇ kapsamaz — `getaddrinfo` yavaşlatma BENZETİMİYLE ölçüldü
    (2026-10-01, yerel CPython 3.12.7; gerçek çözümleyici DEĞİL): `getaddrinfo` 1,5 s geciktirilince 0,3 s zaman aşımlı
    istek 1,52 s bekledi. Çözümleme payının tavanı çözümleyicinin kendi zaman aşımlarıdır (glibc resolv.conf
    varsayılanı ad sunucusu başına 5 s × 2 deneme); A1 çözümleyicisi ölçülmedi — G3c; (3) `cancel()` bekleyen ipliği
    bırakır — cevap geldikten sonra eşik dolana dek boşuna yaşamaz. `_gitti` ikinci ateşlemeyi susturur (BİR kez).
    İplik `daemon`: süreç çıkışını tutmaz. Zamanlayıcı enjekte edilir (`threading.Timer` imzası: `(sure, islev)` + `daemon` · `start` · `cancel`)."""

    def __init__(self, bildir, bot: str, metin: str, reply_to, esik_s: float, zamanlayici) -> None:
        self._bildir, self._bot, self._metin, self._reply_to = bildir, bot, metin, reply_to
        self._kilit = threading.Lock()
        self._kapandi = False
        self._gitti = False
        self._zamanlayici = zamanlayici(esik_s, self._ates)
        self._zamanlayici.daemon = True
        self._zamanlayici.start()

    def _ates(self) -> None:
        with self._kilit:
            if self._kapandi or self._gitti:
                return
            self._gitti = True
            try:
                teslim = self._bildir(self._metin, self._reply_to)
            except Exception as e:  # sinyalli: olay (yalnız sınıf adı); ara bildirim düşse de cevap yolu sürer
                obs.warn("telegram_ara_bildirim_hatasi", bot=self._bot, sinif=type(e).__name__)
                return
            if not teslim:
                obs.warn("telegram_ara_bildirim_hatasi", bot=self._bot, sinif="teslim_edilemedi")

    def kapat(self) -> None:
        with self._kilit:
            self._kapandi = True
        self._zamanlayici.cancel()


def _ara_bildirim_kur(bildir, bot: str, imza: str, reply_to, zamanlayici) -> _AraBildirim | None:
    """`bildir` yoksa ara bildirim yok. Metin: 1. satır sohbet imzası (EKSİZ — ona yanıt aynı bota ve oturuma gider),
    2. satır `ARA_BILDIRIM`. Zamanlayıcı kurulamazsa (ör. iplik açılamadı) olay + ara bildirimsiz devam — bekleme
    işareti cevabın önünü kesmez."""
    if bildir is None:
        return None
    try:
        return _AraBildirim(bildir, bot, f"{imza}\n{ARA_BILDIRIM}", reply_to, ARA_BILDIRIM_ESIGI_S, zamanlayici)
    except Exception as e:  # sinyalli: olay (yalnız sınıf adı); soru ara bildirimsiz sorulur
        obs.warn("telegram_ara_bildirim_hatasi", bot=bot, sinif=type(e).__name__, kurulamadi=True)
        return None


def isle(guncelleme: dict, *, yetkili_sohbet: str, bota_sor, gonder, bildir=None, kadro=None,
         bugun: str | None = None, _zamanlayici=threading.Timer) -> str:
    """Tek güncellemeyi işler ve yönlendirme nedenini döner. `bota_sor(bot, metin, kanal, oturum)
    -> str`, `gonder(metin, reply_to) -> bool` enjekte edilir (test ve hizmet aynı gövdeyi koşar).
    `bildir(metin, reply_to) -> bool` verilirse `bota_sor` `ARA_BILDIRIM_ESIGI_S`i aşınca bir kez ara bildirim
    gider (`_AraBildirim`; `None` = ara bildirim yok). Cevap `_parcali_gonder` ile tavana bölünür."""
    mesaj = guncelleme.get("message") or {}
    y = yonlendir(mesaj, yetkili_sohbet, kadro)
    mid = mesaj.get("message_id")
    if y.neden == "yabanci":
        obs.warn("bot_yabanci_mesaj", sohbet_sha=_sha((mesaj.get("chat") or {}).get("id")))
        return y.neden
    if y.neden == "bos":
        return y.neden
    k = kadro if kadro is not None else _kadro.kadro_yukle()
    if y.neden == "bilinmeyen_bot":
        aktif = ", ".join("@" + b.ad for b in _kadro.aktif_botlar(k))
        gonder(f"Tanınmayan bot. Aktif botlar: {aktif}", mid)
        return y.neden
    if y.neden == "pasif_bot":
        b = _kadro.bot_bul(y.bot, k)
        gonder(f"@{y.bot} henüz aktif değil (dalga {b.dalga}).", mid)
        return y.neden
    gun = bugun or datetime.now(timezone.utc).strftime("%Y%m%d")
    oturum = oturum_kimligi(y.bot, mesaj, gun)
    imza = f"{SOHBET_IMZA.format(ad=y.bot)}{OTURUM_AYRACI}{oturum}"
    # Komut tespiti ÇİT KURULMADAN ÖNCE, operatörün kendi sözleri üzerinde (Tur 2, I-1).
    komut = komut_oneki(y.metin)
    giden = _komut_giden(mesaj, y.metin, komut) if komut else _bota_giden(mesaj, y.metin)
    ara = _ara_bildirim_kur(bildir, y.bot, imza, mid, _zamanlayici)
    try:
        cevap = bota_sor(y.bot, giden, "telegram", oturum)
    except Exception as e:  # sinyalli: aşağıda olay + operatöre sınıf adıyla cevap; döngü ölmez
        hata = e
    else:
        hata = None
    finally:
        # CEVAPTAN (ya da hata cevabından) ÖNCE: bu satırdan sonra ara bildirim ASLA gitmez (`_AraBildirim`).
        if ara is not None:
            ara.kapat()
    if hata is not None:
        obs.warn("bot_sohbet_hatasi", bot=y.bot, sinif=type(hata).__name__)
        gonder(f"{imza}\n@{y.bot} şu an cevap veremiyor ({type(hata).__name__}). Kayda geçti.", mid)
        return y.neden
    _parcali_gonder(gonder, y.bot, imza, cevap, mid)
    return y.neden


def _cagir_varsayilan(url: str, govde: dict, zaman_asimi: float) -> dict:
    r = urllib.request.Request(url, data=json.dumps(govde).encode(),
                               headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(r, timeout=zaman_asimi) as y:
        return json.load(y)


def guncellemeleri_al(jeton: str, ofset: int, bekleme_s: int = UZUN_YOKLAMA_S, _cagir=None) -> list[dict] | None:
    """`getUpdates` uzun yoklaması. DÖNÜŞ İKİ ANLAMLIDIR ve karışmaz: liste (boş olabilir) =
    yoklama BAŞARILI; `None` = HATA (istisna ya da gövdede `ok: false`). Ayrım `dongu`nun geri
    çekilmesinin girdisidir — hata boş tur sayılsaydı döngü beklemeden API'yi dövüp olay defterini
    şişirirdi (Tur 2, I-1). Hata SESSİZ değildir (`telegram_yoklama_hatasi`): yalnız istisnanın SINIF
    adı ya da Telegram hata KODU taşınır — istisna metni ve `description` jetonlu URL'yi
    taşıyabildiği için basılmaz."""
    cagir = _cagir or _cagir_varsayilan
    try:
        d = cagir(f"https://api.telegram.org/bot{jeton}/getUpdates",
                  {"offset": ofset, "timeout": bekleme_s, "limit": GUNCELLEME_SAYFASI,
                   "allowed_updates": ["message"]}, bekleme_s + 10)
    except urllib.error.HTTPError as e:  # sinyalli: sınıf + HTTP KODU; e.url/e.filename/e.msg/str(e) jetonlu URL taşır, BASILMAZ
        obs.warn("telegram_yoklama_hatasi", sinif=type(e).__name__, error_code=getattr(e, "code", None))
        return None
    except Exception as e:  # sinyalli: jetonsuz olay (yalnız sınıf adı), None → dongu geri çekilir
        obs.warn("telegram_yoklama_hatasi", sinif=type(e).__name__)
        return None
    if not (isinstance(d, dict) and d.get("ok")):
        obs.warn("telegram_yoklama_hatasi", sinif="ok_false",
                 error_code=d.get("error_code") if isinstance(d, dict) else None)
        return None
    return list(d.get("result") or [])


#: Art arda yoklama hatasında bekleme tavanı (sn). Dizi 1, 2, 4, … 60 — `2**n` üssü tavana ulaşınca
#: büyümeyi bırakır (günlerce süren kesintide dev tamsayı üretilmesin).
GERI_CEKILME_TAVANI_S = 60


def _bekleme_s(ardisik_hata: int) -> int:
    return min(GERI_CEKILME_TAVANI_S, 2 ** min(ardisik_hata, 6))


def _ofset_yaz(ofset: int) -> None:
    try:
        store.write_json(OFSET_DOSYASI, {"ofset": ofset, "ts": time.time()})
    except Exception as e:  # sinyalli: ofset bellekte ilerler; döngü düşmez (bedel `dongu` docstring'inde)
        obs.warn("telegram_ofset_yazim_hatasi", sinif=type(e).__name__)


def _ilk_kosum_atla(guncellemeler: list, ofset: int) -> int:
    """İlk koşum sayfasını İŞLEMEDEN geçer: yeni ofset = en yüksek `update_id + 1` (hiç kimlik yoksa ofset aynen),
    KALICI yazılır ve `telegram_ilk_ofset` olayı atlanan sayısını taşır (içerik değil — yalnız sayı)."""
    kimlikler = [g["update_id"] for g in guncellemeler
                 if isinstance(g, dict) and isinstance(g.get("update_id"), int) and not isinstance(g["update_id"], bool)]
    yeni = max([ofset, *(k + 1 for k in kimlikler)])
    _ofset_yaz(yeni)
    obs.warn("telegram_ilk_ofset", atlanan=len(guncellemeler), ofset=yeni)
    return yeni


def dongu(*, bota_sor, tur_sayisi: int | None = None, _cagir=None, gonder=None, bildir=None,
          _uyku=time.sleep, _zamanlayici=threading.Timer) -> None:
    """Hizmet döngüsü: yokla → her güncelleme için ofseti ilerlet + KALICI yaz → işle.
    `tur_sayisi` None ise sonsuz. Jeton/sohbet yapılandırılmamışsa sessiz no-op DEĞİL, çıkış
    (`SystemExit`). `gonder` ve `bildir` (ara bildirim) verilmezse ikisi de `notify.yanitla`.

    İLK KOŞUM (G4 Görev 3): `OFSET_DOSYASI` yoksa (okunamıyorsa da — `store.read_json` olayla varsayılana düşer)
    yoklama `timeout: 0` ile yapılır ve dönen sayfa `_ilk_kosum_atla` ile İŞLENMEDEN geçilir; sayfa
    `GUNCELLEME_SAYFASI` kadar doluysa atlama bir tur daha sürer, eksik sayfa (boş dahil) ilk koşumu bitirir. Yoklama
    hatası ilk koşumu bitirmez. Gerekçe modül başlığında (İLK KOŞUM BİRİKİMİ YENİDEN OYNATMAZ).

    TESLİM POLİTİKASI — EN-ÇOK-BİR-KEZ (Tur 2, I-2; Rol-1 kararı 2026-09-29). Ofset güncelleme
    İŞLENMEDEN ÖNCE ilerletilir ve diske yazılır; işleme hatası (`telegram_isle_hatasi`, yalnız sınıf
    adı) döngüyü düşürmez ve ofseti geri almaz. Gerekçe: düşen güncelleme zaten kayda geçti (ve bot
    hatası operatöre cevapla bildirildi); yeniden oynatmak operatöre ÇİFT cevap + boşa LLM kotası
    demek, zehirli bir güncellemeyse de sonsuz çökme döngüsü. `update_id`siz güncelleme aynı olayla
    atlanır. Ofset diske yazılamazsa (`telegram_ofset_yazim_hatasi`) bellekte ilerlemeye devam eder;
    bedeli: o süreçte yeniden başlatmada son yazılabilen ofsetten sonrası bir kez tekrar gelebilir.

    GERİ ÇEKİLME (Tur 2, I-1): art arda her yoklama hatasında `_uyku(min(60, 2**n))` — 1, 2, 4, …
    60 sn; bir başarılı tur sayacı sıfırlar. Bu bekleme bir hizmet döngüsünün hata frenidir, kendi
    kendini canlı tutan bir yoklayıcı değildir; `_uyku` testte enjekte edilir.

    JETON HER TUR YENİDEN OKUNUR (Tur 3, I-2): jeton boşalırsa `telegram_jeton_yok` olayı + aynı geri
    çekilme — süreç düşmez. `TELEGRAM_CHAT_ID` pozitif tamsayı değilse döngü HİÇ başlamaz (I-3)."""
    jeton, yetkili = secrets.get("TELEGRAM_BOT_TOKEN"), secrets.get("TELEGRAM_CHAT_ID")
    if not (jeton and yetkili):
        raise SystemExit("telegram_dinleyici: TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID yapılandırılmamış")
    yetkili = str(yetkili).strip()
    if not _POZITIF_TAMSAYI.fullmatch(yetkili):
        # Değer BASILMAZ (operatör kimliği). Negatif kimlik grup/kanaldır: grubun HER üyesi operatör olurdu.
        raise SystemExit("telegram_dinleyici: TELEGRAM_CHAT_ID birebir (özel) sohbet kimliği olmalı — "
                         "pozitif tamsayı; grup/kanal kimliği her üyeyi operatör yapardı. Başlatılmadı.")
    gonder = gonder or (lambda t, r: notify.yanitla(t, reply_to=r))
    bildir = bildir or (lambda t, r: notify.yanitla(t, reply_to=r))
    kayit = store.read_json(OFSET_DOSYASI, None)
    ilk_kosum = kayit is None
    ofset = 0 if ilk_kosum else int((kayit or {}).get("ofset") or 0)
    tur, ardisik_hata = 0, 0
    while tur_sayisi is None or tur < tur_sayisi:
        tur += 1
        jeton = secrets.get("TELEGRAM_BOT_TOKEN")     # HER TUR: pano jetonu değiştirirse yeniden başlatma gerekmez
        if not jeton:
            obs.warn("telegram_jeton_yok")
            _uyku(_bekleme_s(ardisik_hata))
            ardisik_hata += 1
            continue
        guncellemeler = guncellemeleri_al(jeton, ofset, bekleme_s=0 if ilk_kosum else UZUN_YOKLAMA_S,
                                          _cagir=_cagir)
        if guncellemeler is None:
            _uyku(_bekleme_s(ardisik_hata))
            ardisik_hata += 1
            continue
        ardisik_hata = 0
        if ilk_kosum:
            ofset = _ilk_kosum_atla(guncellemeler, ofset)
            ilk_kosum = len(guncellemeler) >= GUNCELLEME_SAYFASI
            continue
        for g in guncellemeler:
            try:
                ofset = int(g["update_id"]) + 1
            except (KeyError, TypeError, ValueError) as e:  # sinyalli: kimliksiz güncelleme atlanır, döngü sürer
                obs.warn("telegram_isle_hatasi", sinif=type(e).__name__, update_id_yok=True)
                continue
            _ofset_yaz(ofset)
            try:
                isle(g, yetkili_sohbet=yetkili, bota_sor=bota_sor, gonder=gonder, bildir=bildir,
                     _zamanlayici=_zamanlayici)
            except Exception as e:  # sinyalli: en-çok-bir-kez — olay (yalnız sınıf adı), ofset geri alınmaz
                obs.warn("telegram_isle_hatasi", sinif=type(e).__name__)


def main(argv: list[str] | None = None) -> int:
    """`python -m meridian.telegram_dinleyici` — `meridian-telegram.service`in giriş noktası: üretim `bota_sor`u
    (`bot_kanal.bota_sor` — gerçek taşıyıcı + hafıza) ile `dongu`. Argüman ALMAZ (bilinmeyen argüman → argparse çıkışı
    2). Sır yoksa `dongu`nun `SystemExit`i aynen yükselir (sessiz no-op yok); `dongu` sonsuzdur, dönüş yalnız
    sözleşme içindir."""
    argparse.ArgumentParser(prog="python -m meridian.telegram_dinleyici",
                            description="Konuşan bot filosunun Telegram dinleyicisi (getUpdates uzun yoklaması)."
                            ).parse_args(argv)
    dongu(bota_sor=bot_kanal.bota_sor)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
