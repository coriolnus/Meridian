"""telegram_dinleyici.py — konuşan bot filosunun Telegram kanalı: operatörün mesajını alır, doğru bota
yönlendirir, cevabı aynı sohbete YANIT olarak geri verir (spec 2026-09-29 §3.5, operatör kararı K3).

NE YAPAR. `getUpdates` uzun yoklamasıyla (`guncellemeleri_al`) gelen her güncellemeyi `isle` işler:
`yonlendir` önce yetkiyi sınar, sonra hedef botu seçer — `@ad` öneki (`@Bekci:`/`@KARNE,`/`@bekçi`
biçimleri dahil; Türkçe harf `kadro.ad_katla` ile katlanır) → o bot; bir bot cevabına (`💬 @ad · <oturum>`
ilk satırı) yanıt → aynı bot; bir rapora yanıt (ilk satır kadrodaki bir aktif botun imzasıyla başlar,
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
öne konsaydı `bota_sor` öneki göremez ve not MODELE giderdi; `hatırla` yanıtı nota yanıtlanan ilk satırı kaynak
etiketi olarak ekler, gövdesiz `unut:` yanıtı yanıtlanan mesajın ilk İÇERİK satırını sorgu yapar
(`_komut_giden`). `dongu` bir ürün hizmet döngüsüdür; systemd birimi Parça 2 dağıtımında gelir — bu modülde
`main()` YOK.

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
  * YASA 6: `telegram_ofset.json`in yazarı ve okuyucusu `dongu`nun kendisidir (süreç yeniden
    başladığında işlenmiş güncelleme ikinci kez cevaplanmasın diye KALICI); aynı modül olduğu için
    statik graf dış okuyucu göremez — beyanı `codelaw.DECLARED_SINKS`te gerekçesiyle durur.
"""
from __future__ import annotations

import hashlib
import json
import re
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone

from . import kadro as _kadro, notify, obs, secrets, store
# KOMUT TESPİTİ, YANIT ÇİTİNİN ADI, KAYNAK ETİKETİ ve ALINTI İLK SATIRI İTHAL EDİLİR, KOPYALANMAZ — sahibi `bot_kanal`
# (bota_sor'un dağıtımı ve dönüş kaydı da onları kullanır; G4 Görev 1 Tur 3: dönüş kaydı yanıt çitini hafızaya
# yazmadan çözer; G4 Görev 2: gövdesiz `unut:` sorgusu aynı ilk-satır kuralından geçer).
from .bot_kanal import ALINTI_CIT_ADI, alinti_ilk_satiri, kaynak_etiketi, komut_oneki
# ÇİT GRAMERİ İTHAL EDİLİR, KOPYALANMAZ — sahibi `skill_gorus_llm` (`sohbet` de oradan alır).
from .skill_gorus_llm import _veri_bloku

SOHBET_IMZA = "💬 @{ad}"
#: Cevap imza satırı `💬 @<bot> · <oturum>` — yanıt zincirinin oturumu cevabın KENDİSİNDE taşınır.
OTURUM_AYRACI = " · "
VARSAYILAN_BOT = "sef"
OFSET_DOSYASI = "telegram_ofset.json"
_ONEK = re.compile(r"^@([A-Za-zÇĞİÖŞÜçğıöşü_]+)[:,]?\s*(.*)$", re.S)
#: Bot adı [a-z_] — kadro bunu ZORLAR (`kadro.AD_DESENI`). Oturum `tg-<ad>-r<N>` ya da `tg-<ad>-<YYYYAAGG>`.
_SOHBET_IMZA = re.compile(r"^💬 @([a-z_]+)(?: · (tg-[a-z_]+-r?\d+))?\s*$")
_POZITIF_TAMSAYI = re.compile(r"[1-9]\d*")


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


def _alinti_icerik_satiri(alinti: str) -> str:
    """Yanıtlanan mesajın ilk İÇERİK satırı: bot cevabının imza satırı (`💬 @ad · <oturum>`) içerik değildir, atlanır;
    boş satırlar atlanır. Satır `bot_kanal.alinti_ilk_satiri`ndan geçer (scrub SONRA tavan). İçerik yoksa `""`."""
    satirlar = [s.strip() for s in alinti.split("\n")]
    if satirlar and _SOHBET_IMZA.match(satirlar[0]):
        satirlar = satirlar[1:]
    ilk = next((s for s in satirlar if s), "")
    return alinti_ilk_satiri(ilk) if ilk else ""


def _komut_giden(mesaj: dict, metin: str, komut: tuple[str, str]) -> str:
    """Komut bota ÇİTSİZ çıplak söz olarak gider (çit öne konsaydı `bota_sor` öneki göremez, not MODELE
    giderdi — Tur 2, inceleme I-1). Yanıt kipinde iki deterministik ek:
      * `hatırla` + DOLU gövde (Rol-1 kararı) → nota kaynak etiketi ` (yanıt: <yanıtlanan mesajın ilk satırı>)` —
        biçim, scrub ve tavan `bot_kanal.kaynak_etiketi`nde (tek kaynak; dönüş kaydı da onu kullanır).
      * `unut` + BOŞ gövde (G4 Görev 2, Rol-1 kararı 5) → yanıtlanan mesajın ilk İÇERİK satırı (`_alinti_icerik_satiri`:
        bot imzası atlanır, scrub SONRA ≤`KAYNAK_ETIKETI_TAVANI`) SORGU olur: `unut: <satır>`. "Bunu unut" demenin yolu.
    Dolu gövdeli `unut`, gövdesiz `hatırla` (bota_sor "neyi?" diye sorsun), `onayla`/`geri al` ve içeriksiz alıntı
    OLDUĞU GİBİ gider — sorgu uydurulmaz."""
    ad, govde = komut
    alinti = ((mesaj.get("reply_to_message") or {}).get("text") or "").strip()
    if not alinti:
        return metin
    if ad == "hatirla" and govde:
        return f"{metin} {kaynak_etiketi(alinti)}"
    if ad == "unut" and not govde:
        sorgu = _alinti_icerik_satiri(alinti)
        return f"{metin.rstrip()} {sorgu}" if sorgu else metin
    return metin


def _sha(x) -> str:
    return hashlib.sha256(str(x).encode()).hexdigest()[:12]


def isle(guncelleme: dict, *, yetkili_sohbet: str, bota_sor, gonder, kadro=None,
         bugun: str | None = None) -> str:
    """Tek güncellemeyi işler ve yönlendirme nedenini döner. `bota_sor(bot, metin, kanal, oturum)
    -> str`, `gonder(metin, reply_to) -> bool` enjekte edilir (test ve hizmet aynı gövdeyi koşar)."""
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
    try:
        cevap = bota_sor(y.bot, giden, "telegram", oturum)
    except Exception as e:  # sinyalli: operatöre sınıf adıyla cevap + olay; döngü ölmez
        obs.warn("bot_sohbet_hatasi", bot=y.bot, sinif=type(e).__name__)
        gonder(f"{imza}\n@{y.bot} şu an cevap veremiyor ({type(e).__name__}). Kayda geçti.", mid)
        return y.neden
    gonder(f"{imza}\n{cevap}", mid)
    return y.neden


def _cagir_varsayilan(url: str, govde: dict, zaman_asimi: float) -> dict:
    r = urllib.request.Request(url, data=json.dumps(govde).encode(),
                               headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(r, timeout=zaman_asimi) as y:
        return json.load(y)


def guncellemeleri_al(jeton: str, ofset: int, bekleme_s: int = 50, _cagir=None) -> list[dict] | None:
    """`getUpdates` uzun yoklaması. DÖNÜŞ İKİ ANLAMLIDIR ve karışmaz: liste (boş olabilir) =
    yoklama BAŞARILI; `None` = HATA (istisna ya da gövdede `ok: false`). Ayrım `dongu`nun geri
    çekilmesinin girdisidir — hata boş tur sayılsaydı döngü beklemeden API'yi dövüp olay defterini
    şişirirdi (Tur 2, I-1). Hata SESSİZ değildir (`telegram_yoklama_hatasi`): yalnız istisnanın SINIF
    adı ya da Telegram hata KODU taşınır — istisna metni ve `description` jetonlu URL'yi
    taşıyabildiği için basılmaz."""
    cagir = _cagir or _cagir_varsayilan
    try:
        d = cagir(f"https://api.telegram.org/bot{jeton}/getUpdates",
                  {"offset": ofset, "timeout": bekleme_s, "allowed_updates": ["message"]}, bekleme_s + 10)
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


def dongu(*, bota_sor, tur_sayisi: int | None = None, _cagir=None, gonder=None,
          _uyku=time.sleep) -> None:
    """Hizmet döngüsü: yokla → her güncelleme için ofseti ilerlet + KALICI yaz → işle.
    `tur_sayisi` None ise sonsuz. Jeton/sohbet yapılandırılmamışsa sessiz no-op DEĞİL, çıkış
    (`SystemExit`).

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
    ofset = int((store.read_json(OFSET_DOSYASI, {}) or {}).get("ofset") or 0)
    tur, ardisik_hata = 0, 0
    while tur_sayisi is None or tur < tur_sayisi:
        tur += 1
        jeton = secrets.get("TELEGRAM_BOT_TOKEN")     # HER TUR: pano jetonu değiştirirse yeniden başlatma gerekmez
        if not jeton:
            obs.warn("telegram_jeton_yok")
            _uyku(_bekleme_s(ardisik_hata))
            ardisik_hata += 1
            continue
        guncellemeler = guncellemeleri_al(jeton, ofset, _cagir=_cagir)
        if guncellemeler is None:
            _uyku(_bekleme_s(ardisik_hata))
            ardisik_hata += 1
            continue
        ardisik_hata = 0
        for g in guncellemeler:
            try:
                ofset = int(g["update_id"]) + 1
            except (KeyError, TypeError, ValueError) as e:  # sinyalli: kimliksiz güncelleme atlanır, döngü sürer
                obs.warn("telegram_isle_hatasi", sinif=type(e).__name__, update_id_yok=True)
                continue
            try:
                store.write_json(OFSET_DOSYASI, {"ofset": ofset, "ts": time.time()})
            except Exception as e:  # sinyalli: ofset bellekte ilerler; döngü düşmez (bedel docstring'de)
                obs.warn("telegram_ofset_yazim_hatasi", sinif=type(e).__name__)
            try:
                isle(g, yetkili_sohbet=yetkili, bota_sor=bota_sor, gonder=gonder)
            except Exception as e:  # sinyalli: en-çok-bir-kez — olay (yalnız sınıf adı), ofset geri alınmaz
                obs.warn("telegram_isle_hatasi", sinif=type(e).__name__)
