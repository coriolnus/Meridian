"""is_istek.py — konuşan filonun "şimdi çalıştır" yolu: `is_iste(ad, kanal, *, cagiran=None) -> IsSonuc`
(spec docs/superpowers/specs/2026-09-29-konusan-bot-filosu-design.md §0 K2-B, §3.6, §4).

NE YAPAR. Operatör bir kanaldan (Telegram dinleyicisi, pano, Claude uygulaması) bir botun zamanlı işini
HEMEN koşturmak ister. Bu modül işi kendisi BAŞLATMAZ ve sohbete systemctl/sudo yetkisi AÇMAZ: kabul
edilen istek `state/istek/<bot>.istek` dosyasını yeniden yazar, dosyayı izleyen systemd `.path` birimi
(`deploy/oracle-a1/meridian-istek-<bot>.path`, `PathChanged=`) aynı `.service`i başlatır. Oneshot
koşarken gelen ikinci başlatma aynı işe katılır → çift koşum yok.

DONUK LİSTE KADRODAN TÜRER. İş listesi `kadro.yaml`in `aktif` ve `zamanli_is`i dolu satırlarıdır
(`is_listesi`); elle ikinci bir liste YOK. İstek adı `kadro.ad_katla` ile katlanır ("BEKÇİ" → bekci),
sonra `TAKMA_ADLAR`dan geçer (spec §3.6 işi `brifing` diye adlandırır, onu koşan bot `sef`tir). Dosya
adı bot adıdır ve bot adı kadroda `[a-z_]+` ile ZORLANIR (`kadro.AD_DESENI`) — istek adından yol
enjeksiyonu yapısal olarak imkânsız: listede olmayan ad dosya yoluna hiç ulaşmaz.

15 DK TAVANI (§4 "operatörün Telegram hesabı ele geçer" savunması). Bot başına son KABUL satırının
`ts`i + `IS_TAVAN_S` şimdiden büyükse istek `tavan` ile reddedilir ve `sonraki_uygun` döner. Tavanın
hafızası `state/is_istek_defteri.jsonl`dir; deftere YALNIZ kabuller yazılır (red çağırana döner,
çağıran onu kendi kanalında söyler — bot_kanal defteri ya da pano cevabı).

SÜREÇLER ARASI KİLİT. İstekler iki ayrı süreçten gelir (Telegram dinleyicisi servisi, pano API'si);
tavan denetimi ile yazım `state/istek/.kilit` üzerinde `fcntl.flock(LOCK_EX)` altında TEK işlemdir.
Kilit kurulamazsa istisna YUKARI çıkar (fail-closed): kilitsiz bir yarış iki kabul ve çift koşum
demektir. `store.file_lock`a düşülmez — o da flock kullanır ama flock kurulamazsa süreç-İÇİ kilide
DÜŞER (uyararak); bu yüzeyde süreç-içi kilit hiçbir şey korumaz.

DEĞİŞMEZLER.
  * GEÇERSİZ GİRDİ SESSİZ VARSAYILANA DÜŞMEZ: `bot_kanal.KANALLAR` dışı kanal ve saat dilimsiz
    `simdi` → `ValueError`, hiçbir bayt yazılmaz (bot_kanal değişmeziyle aynı).
  * KANAL UYDURULMAZ, KİMLİKSİZ İSTEK YOK (Parça 1b G1 Görev 2). Kanalı BİLMEYEN çağıran (MCP araç
    sunucusu: Hermes hangi kanaldan konuştuğunu söylemez) `kanal=None` verir ve `cagiran` kimliğini
    (`mcp:<bot>`) ZORUNLU taşır; istek dosyasında ve defterde `kanal: null` + `cagiran` durur. `kanal`
    verilince doğrulama aynen işler — `cagiran` bilinmeyen bir kanalı aklamaz. `cagiran` verildiyse boş
    olmayan bir dizge olmalı; `kanal=None` + `cagiran` yok/boş → `ValueError`, hiçbir bayt yazılmaz.
    Tavan bot başınadır, kanal başına değil: kanalsız istek Telegram kabulünü görür.
  * SIRA: istek dosyası (atomik, `store.write_text`: tmp + fsync + os.replace) ÖNCE, defter satırı
    SONRA. Defter yazımı düşerse iş zaten tetiklenmiştir: sonuç `kabul` döner (gerçeği söyler) ve
    `is_istek_defter_yazim_hatasi` olayı yazılır — o istekten sonraki 15 dk tavansız kalır ve bu
    sessiz değildir.
  * İstek dizini yoksa `0o750` ile kurulur (umask düşürebilir; hiçbir zaman genişletmez).

YASA 6 — OKUYUCU BEYANI. `is_istek_defteri.jsonl`in okuyucusu bu modülün `_son_kabul`üdür (tavan) —
aynı modül, statik graf dış tüketiciyi göremez. `istek/*.istek` dosyasının tüketicisi bir modül değil
systemd'dir (`PathChanged=` değişikliği izler, içeriği okumaz; içerik bir denetim izidir ve defterde de
vardır). İkisi de `codelaw.DECLARED_SINKS`te gerekçesiyle; ikincisi yazarı grafta görünmediği için
`codelaw.UNVERIFIABLE_SINKS` borç defterinde de durur.
"""
from __future__ import annotations

import contextlib
import datetime as dt
import fcntl
import json
import os
from dataclasses import dataclass

from . import bot_kanal, config, kadro as _kadro, obs, store

IS_TAVAN_S = 900
ISTEK_DIZINI = "istek"
DEFTER = "is_istek_defteri.jsonl"
#: Katlanmış istek adı → bot adı. Spec §3.6 listesi işi `brifing` diye adlandırır; bot adları kadrodan.
TAKMA_ADLAR = {"brifing": "sef"}
#: Süreçler arası kilit dosyası (`state/istek/` altında). Nokta önekli: `.path` birimlerinin izlediği
#: `<bot>.istek` adlarıyla çakışamaz.
KILIT = ".kilit"
DIZIN_KIPI = 0o750
KILIT_KIPI = 0o640


@dataclass(frozen=True)
class IsSonuc:
    kabul: bool
    bot: str | None
    birim: str | None
    neden: str
    sonraki_uygun: str | None


def is_listesi(kadro: tuple[_kadro.Bot, ...] | None = None) -> dict[str, str]:
    """`{bot: zamanli_is}` — yalnız `aktif` VE `zamanli_is`i dolu botlar (kadrodan türer, donuk liste)."""
    return {b.ad: b.zamanli_is for b in _kadro.aktif_botlar(kadro) if b.zamanli_is}


def _an(simdi: dt.datetime | None) -> dt.datetime:
    an = simdi if simdi is not None else dt.datetime.now(dt.timezone.utc)
    if an.tzinfo is None:
        raise ValueError("is_iste: 'simdi' saat dilimli olmalı — dilimsiz an yerel saat sanılıp "
                         "tavanı sessizce kaydırırdı")
    return an.astimezone(dt.timezone.utc)


@contextlib.contextmanager
def _kilit():
    """`state/istek/.kilit` üzerinde süreçler arası `flock(LOCK_EX)`; tanıtıcı kapanınca kilit düşer."""
    dizin = config.STATE / ISTEK_DIZINI
    dizin.mkdir(mode=DIZIN_KIPI, parents=True, exist_ok=True)
    fd = os.open(dizin / KILIT, os.O_RDWR | os.O_CREAT, KILIT_KIPI)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield
    finally:
        os.close(fd)


def _son_kabul(bot: str) -> dt.datetime | None:
    """Defterde `bot` için EN GEÇ kabul anı (yoksa `None`). Yazan yalnız bu modüldür ve `ts`i hep
    dilimli ISO yazar; çözülemeyen `ts` dış hasardır — satır SAYILMAZ ama sessiz de geçmez."""
    son: dt.datetime | None = None
    for satir in store.read_jsonl(DEFTER):
        if not isinstance(satir, dict) or satir.get("bot") != bot or satir.get("neden") != "kabul":
            continue
        try:
            ts = dt.datetime.fromisoformat(str(satir.get("ts")))
            if ts.tzinfo is None:
                raise ValueError("dilimsiz ts")
        except ValueError as e:
            obs.warn("is_istek_defter_bozuk_ts", bot=bot, ts=str(satir.get("ts"))[:40],
                     sinif=type(e).__name__, detail="satır tavan hesabına katılmadı")
            continue
        if son is None or ts > son:
            son = ts
    return son


def is_iste(ad: str, kanal: str | None, *, simdi: dt.datetime | None = None,
            kadro: tuple[_kadro.Bot, ...] | None = None, cagiran: str | None = None) -> IsSonuc:
    """Bir botun zamanlı işini şimdi koşturma isteği. `neden` ∈ `kabul · bilinmeyen_is · tavan`.
    `kanal=None` yalnız `cagiran` kimliğiyle (modül başlığı, DEĞİŞMEZLER)."""
    if cagiran is not None and (not isinstance(cagiran, str) or not cagiran.strip()):
        raise ValueError(f"is_iste: 'cagiran' boş olmayan bir dizge olmalı, gelen {type(cagiran).__name__}")
    if kanal is None:
        if cagiran is None:
            raise ValueError("is_iste: kanal bilinmiyorsa 'cagiran' zorunlu — kimliksiz istek denetim izi "
                             "bırakmaz, kanal da uydurulmaz")
    elif kanal not in bot_kanal.KANALLAR:
        raise ValueError(f"is_iste: bilinmeyen kanal {kanal!r} (izinli: {bot_kanal.KANALLAR})")
    cagiran = cagiran.strip() if cagiran is not None else None
    an = _an(simdi)
    katli = _kadro.ad_katla(ad)
    hedef = TAKMA_ADLAR.get(katli, katli)
    birim = is_listesi(kadro).get(hedef)
    if birim is None:
        return IsSonuc(kabul=False, bot=None, birim=None, neden="bilinmeyen_is", sonraki_uygun=None)
    with _kilit():
        son = _son_kabul(hedef)
        if son is not None:
            sonraki = son + dt.timedelta(seconds=IS_TAVAN_S)
            if an < sonraki:
                return IsSonuc(kabul=False, bot=hedef, birim=birim, neden="tavan",
                               sonraki_uygun=sonraki.isoformat(timespec="seconds"))
        ts = an.isoformat(timespec="seconds")
        store.write_text(f"{ISTEK_DIZINI}/{hedef}.istek",
                         json.dumps({"bot": hedef, "kanal": kanal, "ts": ts}, ensure_ascii=False))
        try:
            store.append_jsonl(DEFTER, {"ts": ts, "bot": hedef, "birim": birim, "kanal": kanal,
                                        "cagiran": cagiran, "neden": "kabul"})
        except OSError as e:
            obs.warn("is_istek_defter_yazim_hatasi", bot=hedef, birim=birim, sinif=type(e).__name__,
                     detail="iş tetiklendi ama kabul deftere düşmedi — bu istekten sonraki 15 dk tavansız")
    return IsSonuc(kabul=True, bot=hedef, birim=birim, neden="kabul", sonraki_uygun=None)
