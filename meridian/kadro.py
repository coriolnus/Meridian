"""kadro.py — konuşan bot filosunun KADRO LİSTESİNİ (`deploy/hermes/kadro.yaml`) yükler, doğrular, sorgular.

TEK KAYNAK (spec docs/superpowers/specs/2026-09-29-konusan-bot-filosu-design.md §3.1): bot adı, durumu,
araç alt kümesi, rapor imzası ve hafıza kipi YALNIZ o dosyada yaşar; Telegram yönlendirmesi, pano seçicisi,
bot sunucusu ve filo MCP'si buradan türetir. Doğrulama gevşek değildir: bilinmeyen durum/dalga/hafıza,
tekrarlanan ad, aracı olmayan aktif bot, nedensiz boş tavan → `ValueError` (sessiz varsayılan YOK).
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import yaml

from . import config

KADRO_YOLU = config.ROOT / "deploy/hermes/kadro.yaml"
DURUMLAR = ("aktif", "sirada", "kilitli")
DALGALAR = ("canli", "1", "2", "3", "kilitli")
HAFIZA_KIPLERI = ("kendi", "hepsi")
#: Sohbet kaydının DIŞINDAKİ araç sunucusu araçları — `mcp_server` bunları `--bot` kipinde sunar (Parça 1b G1);
#: çivi v597 kayıtla eşitliği, v591 bilinen kümeyi ölçer.
PLANLI_ARACLAR = ("is_iste", "bot_hafizasi_ara")
#: Bot adının izinli biçimi. Telegram yönlendirme desenleri (`bot_kanal` modülündeki sohbet imzası
#: tanıyıcısı `_SOHBET_IMZA` ve `telegram_dinleyici` modülündeki `_ONEK`) ve oturum kimliği biçimi
#: (`tg-<ad>-…`) adın bu kümede olduğunu varsayar; kadro varsayımı ZORLAR — rakamlı ya da Türkçe harfli
#: bir ad, o botun cevabına yanıtı sessizce varsayılan bota düşürürdü.
AD_DESENI = re.compile(r"[a-z_]+")
#: Türkçe harf katlaması — operatör "@bekçi"/"@ŞEF" yazar, kadro adı ASCII'dir. BÜYÜK harfler de
#: DOĞRUDAN ASCII küçüğe iner: "İ".lower() Python'da "i" + BİRLEŞTİRİCİ NOKTA (U+0307) verir, yani
#: `.lower()`dan ÖNCE katlanmazsa "@DENETCİ" hiçbir adla eşleşmez.
_TR_KATLAMA = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosucgiosu")


@dataclass(frozen=True)
class Bot:
    ad: str
    rol: str
    dalga: str
    durum: str
    araclar: tuple[str, ...]
    zamanli_is: str | None
    imza: str | None
    hafiza: str
    gunluk_tavan: int | None
    gunluk_tavan_neden: str | None


def _bot(ham: dict) -> Bot:
    if not isinstance(ham, dict):
        raise ValueError(f"kadro: satır bir eşleme değil: {ham!r}")
    ad = str(ham.get("ad") or "").strip().lower()
    if not ad:
        raise ValueError("kadro: 'ad' alanı boş bir satır var")
    if not AD_DESENI.fullmatch(ad):
        raise ValueError(f"kadro: 'ad'={ad!r} yalnız [a-z_] olabilir — Telegram yönlendirme "
                         "desenleri ve oturum kimliği bu varsayıma dayanır")
    for alan, izinli in (("durum", DURUMLAR), ("dalga", DALGALAR), ("hafiza", HAFIZA_KIPLERI)):
        if str(ham.get(alan)) not in izinli:
            raise ValueError(f"kadro: @{ad} '{alan}'={ham.get(alan)!r} izinli değil {izinli}")
    ham_araclar = ham.get("araclar") or []
    # Dizge bir liste DEĞİLDİR: `araclar: pano_ozeti` tuple()'a girse harf harf araç adı olurdu.
    if not isinstance(ham_araclar, (list, tuple)) or not all(isinstance(a, str) for a in ham_araclar):
        raise ValueError(f"kadro: @{ad} 'araclar' dizge listesi olmalı, gelen {ham_araclar!r}")
    araclar = tuple(ham_araclar)
    if ham["durum"] == "aktif" and not araclar:
        raise ValueError(f"kadro: aktif @{ad} için 'araclar' boş olamaz")
    tavan = ham.get("gunluk_tavan")
    # bool bir int alt sınıfıdır — `gunluk_tavan: true` tavan 1 diye sessizce okunmasın.
    if tavan is not None and (isinstance(tavan, bool) or not isinstance(tavan, int)):
        raise ValueError(f"kadro: @{ad} 'gunluk_tavan' tamsayı ya da null olmalı, gelen {tavan!r}")
    neden = ham.get("gunluk_tavan_neden")
    if tavan is None and not neden:
        raise ValueError(f"kadro: @{ad} 'gunluk_tavan' boşken 'gunluk_tavan_neden' zorunlu")
    return Bot(ad=ad, rol=str(ham.get("rol") or ""), dalga=str(ham["dalga"]), durum=str(ham["durum"]),
               araclar=araclar, zamanli_is=ham.get("zamanli_is"), imza=ham.get("imza"),
               hafiza=str(ham["hafiza"]), gunluk_tavan=tavan, gunluk_tavan_neden=neden)


def kadro_yukle(yol: Path | None = None) -> tuple[Bot, ...]:
    veri = yaml.safe_load(Path(yol or KADRO_YOLU).read_text(encoding="utf-8")) or {}
    botlar = tuple(_bot(h) for h in (veri.get("botlar") or ()))
    goruldu: set[str] = set()
    for b in botlar:
        if b.ad in goruldu:
            raise ValueError(f"kadro: @{b.ad} tekrar ediyor")
        goruldu.add(b.ad)
    return botlar


def ad_katla(ad: str) -> str:
    """Operatörün yazdığı bot adını kadro biçimine indirir: Türkçe harf katlaması (`İ` dahil,
    `.lower()`dan ÖNCE) + küçük harf. Tek katlama noktası budur — yönlendirme ve sorgu buradan geçer."""
    return (ad or "").strip().translate(_TR_KATLAMA).lower()


def bot_bul(ad: str, kadro: tuple[Bot, ...] | None = None) -> Bot | None:
    hedef = ad_katla(ad)
    return next((b for b in (kadro if kadro is not None else kadro_yukle()) if b.ad == hedef), None)


def aktif_botlar(kadro: tuple[Bot, ...] | None = None) -> tuple[Bot, ...]:
    return tuple(b for b in (kadro if kadro is not None else kadro_yukle()) if b.durum == "aktif")


def imzadan_bot(metin: str, kadro: tuple[Bot, ...] | None = None) -> Bot | None:
    ilk = (metin or "").split("\n", 1)[0].strip()
    if not ilk:
        return None
    return next((b for b in aktif_botlar(kadro) if b.imza and ilk.startswith(b.imza)), None)
