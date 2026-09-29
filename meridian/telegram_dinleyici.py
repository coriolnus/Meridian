"""telegram_dinleyici.py — konuşan bot filosunun Telegram kanalı: operatörün mesajını alır, doğru bota
yönlendirir, cevabı aynı sohbete YANIT olarak geri verir (spec 2026-09-29 §3.5, operatör kararı K3).

NE YAPAR. `getUpdates` uzun yoklamasıyla (`guncellemeleri_al`) gelen her güncellemeyi `isle` işler:
`yonlendir` önce sohbet kimliğini sınar, sonra hedef botu seçer — `@ad` öneki (`@Bekci:`/`@KARNE,`
biçimleri dahil) → o bot; bir bot cevabına (`💬 @ad` ilk satırı) yanıt → aynı bot; bir rapora yanıt
(ilk satır kadrodaki bir aktif botun imzasıyla başlar, `kadro.imzadan_bot`) → o bot; hiçbiri yoksa
`@sef`. Cevap `bota_sor(bot, metin, kanal, oturum)` ile alınır ve `💬 @ad` imzasıyla gönderilir.
Oturum kimliği yanıt zincirine bağlıdır (`tg-<bot>-r<yanıtlanan mesaj>`), zincir yoksa güne
(`tg-<bot>-<YYYYAAGG>`). `dongu` bir ürün hizmet döngüsüdür; systemd birimi Parça 2 dağıtımında
gelir — bu modülde `main()` YOK.

DEĞİŞMEZLER.
  * YALNIZ YETKİLİ SOHBET: `TELEGRAM_CHAT_ID` dışındaki sohbete CEVAP VERİLMEZ, kadro bile
    okunmaz; ret SAYILIR (`bot_yabanci_mesaj` olayı) ve olayda sohbet kimliği HAM değil, sha256'nın
    ilk 12 hanesiyle durur (yabancının kimliği deftere düşmez, tekrarı yine sayılabilir).
  * TEK TESLİMAT YOLU: varsayılan gönderici `notify.yanitla`dır — `send` ile aynı Telegram yolu ve
    aynı `scrub`; bu modül dışarıya kendi başına METİN göndermez. `getUpdates` çağrısı bir GELEN
    okumadır: gövdesi yalnız ofset/bekleme taşır.
  * JETON LOG'A DÜŞMEZ: yoklama hatası olayı yalnız istisnanın SINIF adını taşır (URL jetonu içerir,
    istisna metni ona dokunabilir); bot hatası da operatöre sınıf adıyla söylenir.
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
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone

from . import kadro as _kadro, notify, obs, secrets, store

SOHBET_IMZA = "💬 @{ad}"
VARSAYILAN_BOT = "sef"
OFSET_DOSYASI = "telegram_ofset.json"
_ONEK = re.compile(r"^@([A-Za-zÇĞİÖŞÜçğıöşü_]+)[:,]?\s*(.*)$", re.S)
_SOHBET_IMZA = re.compile(r"^💬 @([a-z_]+)\s*$")


@dataclass(frozen=True)
class Yonlendirme:
    bot: str | None
    metin: str
    neden: str


def yonlendir(mesaj: dict, yetkili_sohbet: str, kadro=None) -> Yonlendirme:
    """Mesajın hedef botunu seçer. `neden` ∈ onek · imza · sohbet_imza · varsayilan · yabanci ·
    bos · pasif_bot · bilinmeyen_bot. Sohbet kimliği sınaması HER ŞEYDEN önce gelir."""
    if str((mesaj.get("chat") or {}).get("id")) != str(yetkili_sohbet):
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
    """Yanıt zinciri varsa `tg-<bot>-r<reply_to_message_id>`, yoksa `tg-<bot>-<bugun>`."""
    r = (mesaj.get("reply_to_message") or {}).get("message_id")
    return f"tg-{bot}-r{r}" if r is not None else f"tg-{bot}-{bugun}"


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
    try:
        cevap = bota_sor(y.bot, y.metin, "telegram", oturum_kimligi(y.bot, mesaj, gun))
    except Exception as e:  # sinyalli: operatöre sınıf adıyla cevap + olay; döngü ölmez
        obs.warn("bot_sohbet_hatasi", bot=y.bot, sinif=type(e).__name__)
        gonder(f"{SOHBET_IMZA.format(ad=y.bot)}\n@{y.bot} şu an cevap veremiyor "
               f"({type(e).__name__}). Kayda geçti.", mid)
        return y.neden
    gonder(f"{SOHBET_IMZA.format(ad=y.bot)}\n{cevap}", mid)
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
    kendini canlı tutan bir yoklayıcı değildir; `_uyku` testte enjekte edilir."""
    jeton, yetkili = secrets.get("TELEGRAM_BOT_TOKEN"), secrets.get("TELEGRAM_CHAT_ID")
    if not (jeton and yetkili):
        raise SystemExit("telegram_dinleyici: TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID yapılandırılmamış")
    gonder = gonder or (lambda t, r: notify.yanitla(t, reply_to=r))
    ofset = int((store.read_json(OFSET_DOSYASI, {}) or {}).get("ofset") or 0)
    tur, ardisik_hata = 0, 0
    while tur_sayisi is None or tur < tur_sayisi:
        tur += 1
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
