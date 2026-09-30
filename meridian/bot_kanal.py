"""bot_kanal.py — konuşan bot filosunun ORTAK GİRİŞ NOKTASI: `bota_sor(bot, mesaj, kanal, oturum) -> str`
(spec docs/superpowers/specs/2026-09-29-konusan-bot-filosu-design.md §3.4, §3.5, §3.7, §4).

NE YAPAR. Üç kanal (Telegram dinleyicisi, pano, Claude uygulaması) bir bota soruyu YALNIZ buradan
sorar. Sıra DONUKTUR: (1) kanal `KANALLAR` içinde mi; (2) bot kadroda VE `aktif` mi
(`kadro.bot_bul`); (3) `hatırla:` / `unut:` öneki mi — öyleyse MODELE GİTMEZ, deterministik işlenir;
(4) bot başına UTC günlük kota (kadro satırının `gunluk_tavan` alanı; `None` = tavan yok ama SAYILIR);
(5) taşıyıcı çağrısı (`Tasiyici` protokolü; varsayılan `HermesTasiyici` = Hermes api_server);
(6) araçsız-veri uyarısı (aşağıda); (7) her dönüş `state/bot_sohbet.jsonl` defterine bir satır.

DEĞİŞMEZLER.
  * GEÇERSİZ GİRDİ SESSİZ VARSAYILANA DÜŞMEZ: bilinmeyen kanal, kadroda olmayan ya da `aktif`
    olmayan bot → `ValueError`. Saat dilimsiz `simdi` de `ValueError` — kota günü UTC'dir ve
    dilimsiz bir an yerel saat sanılıp günü sessizce kaydırırdı.
  * `hatırla:` / `unut:` (Türkçe harf katlamalı, büyük/küçük harf duyarsız — `kadro.ad_katla`)
    modele GİTMEZ. `hatırla` gövdesi `notify.scrub`'dan geçip `Hafiza.yaz`a gider (etiket
    `sabit_not`, `bot:<ad>`, `kanal:<kanal>`); hafıza bağlı değilse bunu AÇIKÇA söyler ve
    `bot_hafiza_bagli_degil` olayı yazar. `unut` gövdesi de `notify.scrub`'dan geçip `Hafiza.unut`a gider:
    en fazla birkaç bellek GERİ ALINABİLİR biçimde emekliye ayrılır (gerçek uygulama `bot_hafiza.HindsightHafiza`,
    Parça 0 (f) ölçümü: `state: invalidated`) ve operatöre hangi metinlerin unutulduğu kısa listeyle söylenir;
    eşleşme yoksa bu da söylenir. Gövdesiz komut hafızaya GİTMEZ ("neyi?" diye sorulur) — boş sorgu rastgele
    bellek döndürürdü. Hafıza istisnası "YAZILAMADI"/"UNUTULAMADI" + olay olur, sohbet hatasına dönmez; kısmi
    `unut` hatasında o âna dek unutulanlar (`unutulanlar` özniteliği) yine söylenir. Kalıcı silme bu modülde YOK.
    Tespitin TEK kaynağı `komut_oneki`dir; Telegram dinleyicisi de onu çağırır (yanıt kipinde
    komut, VERİ çitinin arkasında kaybolmasın diye çit kurulmadan ÖNCE — Tur 2, inceleme I-1).
  * KOTA SESSİZ DEĞİL: tavan doluysa bot "bugünlük kotam doldu (n/tavan)" der, taşıyıcı ÇAĞRILMAZ,
    defter `tur: kota_doldu` satırı alır. Sayım defterin `tur == "sohbet"` satırlarından
    (`gunluk_sayim`); tavan sayısı Parça 0 (g) ölçümünden gelir — burada UYDURULMAZ.
  * TAŞIYICI HATASI YUTULMAZ: defter `tur: hata` + sınıf adı, istisna YUKARI fırlar (Telegram
    dinleyicisi `bot_sohbet_hatasi` yolunda yakalar ve operatöre sınıf adıyla söyler).
  * DEFTER YAZIMI CEVABI DÜŞÜRMEZ: `store.append_jsonl` düşerse `bot_defter_yazim_hatasi` olayı
    (sinyalli) — operatörün cevabı yine döner.
  * SIR DEFTERE/İSTİSNAYA DÜŞMEZ: defterdeki `mesaj`/`cevap` `notify.scrub`'dan ÖNCE geçer, SONRA
    `cevap` `CEVAP_TAVANI`na kesilir (ters sıra yarım kesilmiş bir anahtarı desenin dışına itip
    sızdırırdı); `kesildi` alanı her satırda. `API_SERVER_KEY` yalnız `Authorization` başlığındadır;
    HTTP hatası yalnız DURUM KODUYLA `RuntimeError`a çevrilir, zincir bastırılır (`from None`).
  * ARAÇSIZ VERİ İŞARETLENİR, MODELE GÜVENİLMEZ (Parça 0 EN AĞIR BULGU, 2026-09-29: araç katmanı bağlı
    olmayan bot bir araç çağrısı VE sonucunu uydurup gerçek veri gibi sundu; oturumda `tool_calls` yoktu).
    Taşıyıcı bu turun GERÇEK araç SONUCU sayısını (hizalı oturum dökümünden) `TasiyiciSonuc.arac_cagrilari`na
    koyar; sayı 0 iken cevap veri taşıyorsa (`veri_isareti`, defter `veri_isareti` alanı hangi işaretin
    eşleştiğini yazar) `UYARI_ARACSIZ` öneki + defter `arac_siz_veri: true`; sayı ÖLÇÜLEMEDİYSE
    (`None`) `UYARI_OLCULEMEDI` öneki + `arac_olculemedi: true` ve `arac_siz_veri: None` (0 ile "bilmiyorum"
    aynı şey değildir — uydurma yasağı). Önek cevap zaten onunla başlıyorsa eklenmez; defterdeki `cevap`
    operatörün gördüğü (önekli) metindir. Uyarı taşıyıcıdan BAĞIMSIZ burada uygulanır.

YASA 6 — OKUYUCU BEYANI. `bot_sohbet.jsonl`in bugünkü tek okuyucusu bu modülün kendi
`gunluk_sayim`idir (kota); aynı modül olduğu için statik graf dış tüketiciyi göremez. Planlı
okuyucular (@ayna, @butce, pano bot sayacı, EDG ölçüm kartı) Parça 1 dağıtımında gelir — beyan
`codelaw.DECLARED_SINKS`te gerekçesiyle durur.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol

from . import kadro as _kadro, notify, obs, secrets, store

KANALLAR = ("telegram", "pano", "claude")
DEFTER = "bot_sohbet.jsonl"
CEVAP_TAVANI = 4000
#: Komut öneki: ilk kelime (yalnız harf) + isteğe bağlı boşluk + `:`. Kelime `kadro.ad_katla` ile
#: katlanıp `hatirla` / `unut` ile kıyaslanır — GÖVDE katlanmaz (not operatörün yazdığı gibi kalır).
_KOMUT = re.compile(r"^([^\W\d_]+)\s*:(.*)$", re.S)
#: Deterministik komutlar (katlanmış ad). Tespit YALNIZ `komut_oneki`de.
KOMUTLAR = ("hatirla", "unut")
_HATIRLA_BOS = "Neyi hatırlayayım? `hatırla: <not>` biçiminde yaz."
_HAFIZA_BAGLI_DEGIL = "Hafızam henüz bağlı değil (Parça 0 ölçümü bekleniyor); not ALINMADI."
_HAFIZA_YAZILAMADI = "Not YAZILAMADI (hafıza hatası), kayda geçti."
_UNUT_BOS = "Neyi unutayım? `unut: <ifade>` biçiminde yaz."
_UNUT_BAGLI_DEGIL = "Hafızam henüz bağlı değil; hiçbir şey unutulmadı."
_UNUT_ESLESME_YOK = "Eşleşen bir not bulamadım; hiçbir şey unutulmadı."
#: "hiçbir şey unutulmadı" DENMEZ: zaman aşımına uğrayan bir PATCH sunucuda yine de uygulanmış olabilir.
_UNUTULAMADI = "UNUTULAMADI (hafıza hatası), kayda geçti."
#: Araçsız-veri uyarıları — DONUK (plan 2026-09-29 Parça 1b-ön): ölçüm kartı ve operatör bu metinleri tanır.
UYARI_ARACSIZ = "⚠️ Bu cevap hiçbir araç çağrısına dayanmıyor — içindeki veri doğrulanmadı."
UYARI_OLCULEMEDI = "⚠️ Bu cevabın araç kullanımı doğrulanamadı."
#: "Veri içeriyor" DETERMİNİSTİK (`veri_isareti`; ilk eşleşen işaret, bu sırayla): rakam · `%` · katlanmış metinde
#: kaynak jetonu (`.json`, `.jsonl`yi kapsar) · alan sözlüğü (kelime başında kök öneki) · büyük harfli sembol
#: (`SEMBOL_DISI` hariç).
_RAKAM = re.compile(r"\d")
_VERI_JETONLARI = ("kaynak", "source", ".json")
#: Alan sözlüğü — Rol-1 kararları 2026-09-30 (inceleme I-3 genişletme; Tur 3 kök öneki; Tur 4 `getiri`/`hisset`).
#: Katlanmış (`kadro.ad_katla`) metinde KELİME BAŞINDA KÖK ÖNEKİ eşleşir: Türkçe eklemeli — tam-kelime kuralı 10
#: çekimli alan cümlesinin 1'ini yakalıyordu. Kökler ≥4 harf. DÜŞENLER: `kar` (karar/karne/kardeş çakışması),
#: `getiri` ("getirmek" fiili: depo Türkçe belgelerinde `getiri*` isabetlerinin 41/137'si; getiri iddiaları rakam
#: ya da `%` taşır, onlar ayrı işarettir). BİLİNEN GÜRÜLTÜ (ölçüldü, bilerek bırakıldı): `zarar` → "zararlı",
#: `plan`/`stop` → İngilizce "plane"/"planner"/"stopped", `hisse` → "hissediyorum"/"hissederim" (`hissed` öneki
#: "hissedar"la ortak). Yanlış pozitif yalnız bir uyarı satırıdır; defter `veri_isareti` alanından ölçülür ve kart
#: `sozluk:*` isabetlerini inceleme sınıfı sayar (Rol-1).
VERI_SOZLUGU = ("rejim", "maruziyet", "pozisyon", "stop", "alarm", "emir", "zarar", "butce",
                "sinyal", "plan", "fiyat", "hisse", "portfoy", "dolum", "tetik")
_SOZLUK_DESENI = re.compile(r"\b(" + "|".join(VERI_SOZLUGU) + r")\w*")
#: Kök önekine takılan ama açıkça veri OLMAYAN katlanmış TAM kelimeler — yalnız ÖLÇÜLMÜŞ çakışmalar: `emirhan`
#: (Rol-1, özel ad), `zararsiz` (SOUL'da "nedeni zararsız görünüyor" = masum). Ayrışma çivisi: v593 SOUL taraması.
SOZLUK_DISI = frozenset({"emirhan", "zararsiz"})
#: Kök önekine takılan ama açıkça veri olmayan kelimelerin ÖNEKLERİ (Rol-1 Tur 4): `hisset` = "hissetmek" fiili
#: (hissettirdi, hissetmek, hissettim). `hissed` BİLEREK YOK: "hissedar" (hissedar) ve "hisseler" veri kalır.
SOZLUK_DISI_ONEK = ("hisset",)
_SEMBOL_DESENI = re.compile(r"\b[A-Z]{2,5}\b")
#: Sembol SAYILMAYAN büyük harfli jetonlar: Rol-1 listesi + kendi SOUL/uyarı metinlerimizde ÖLÇÜLEN vurgu
#: kelimeleri (2026-09-30; `deploy/hermes/**/SOUL*.md` — ayrışma çivisi v593 SOUL taraması). BEDEL: `GO`,
#: `OOS`, `KALDI`, `GECTI` gibi hüküm kelimeleri bu işarete takılmaz.
SEMBOL_DISI = frozenset({
    "OK", "UTC", "API", "JSON", "PDF", "AI", "TL", "USD",
    "ANLAM", "ANMAK", "ARIZA", "ARTIK", "AYNI", "AZ", "BU", "CAGRI", "DURAN", "EN", "GECTI", "GO", "HAFTA",
    "HAZIR", "HER", "IZI", "KALDI", "KALEM", "KEZ", "KIL", "MCP", "NE", "NEDEN", "OKUMA", "OOS", "SADE", "SANA",
    "SATIR", "SIRA", "SKILL", "SON", "SONRA", "TEK", "VERI", "YA", "YAZMA", "YOK", "ZORLA",
})
#: Oturum kimliği oturum dökümü GET'inde URL YOLUNA girer (bot adıyla aynı sınıf): `/`, `..`, `?`, `#`
#: yolu başka bir uca taşırdı. Desene uymayan kimlikte GET ATILMAZ, sayım ölçülemedi (`None`) olur.
_OTURUM_DESENI = re.compile(r"[A-Za-z0-9_-]{1,128}")


@dataclass(frozen=True)
class TasiyiciSonuc:
    metin: str
    arac_cagrilari: int | None = None
    model_cagrilari: int | None = None


class Tasiyici(Protocol):
    def sor(self, bot: str, mesaj: str, oturum: str) -> TasiyiciSonuc: ...


class SayimOlculemedi(ValueError):
    """Bu turun araç sonucu sayısı ölçülemedi — kendi denetimlerimizin kapalı-küme `neden`i (`oturum_kimligi` ·
    `bicim` · `tur_hizasiz`). İçerik, URL ya da anahtar TAŞIMAZ."""

    def __init__(self, neden: str):
        super().__init__(neden)
        self.neden = neden


class Hafiza(Protocol):
    def yaz(self, bot: str, metin: str, etiketler: tuple[str, ...]) -> bool: ...

    def unut(self, bot: str, ifade: str) -> list[tuple[str, str]]:
        """Geri alınabilir unutma; emekliye ayrılan `(bellek_id, metin_kesiti)` listesi (boş = eşleşme yok)."""
        ...


class HermesTasiyici:
    """Hermes api_server (v0.19.0, A1 kaynağında ölçüldü): `POST {taban}/p/<bot>/v1/chat/completions`,
    `Authorization: Bearer <API_SERVER_KEY>`, oturum sürekliliği `X-Hermes-Session-Id`. Anahtar HER
    çağrıda `secrets.credential_oku` ile okunur (LoadCredential kanalı; argv/ortam/log'a düşmez) —
    yoksa istek HİÇ atılmaz. Zaman aşımı ZORUNLUDUR: asılı bir api_server Telegram döngüsünü de
    asardı — kurucu sonlu ve > 0 olmayan değeri (`None`, 0, negatif, inf, nan, bool, dizge) `ValueError`
    ile REDDEDER; `urlopen(timeout=None)` soketi sonsuz bloklardı (Tur 3, son inceleme I-1). Sınır soket
    İŞLEMİ başınadır, duvar saati değil (park: son inceleme M-4). `arac_cagrilari` sohbet çağrısından SONRA
    `GET {taban}/p/<bot>/api/sessions/<oturum>/messages` dökümünden ölçülür (`_bu_turun_arac_sonuclari`: hizalı
    döküm, dönen araç SONUÇLARI; AYNI zaman aşımı ve anahtar hijyeni); okunamaz, hizasız ya da biçimi tanınmazsa
    `None` + `bot_arac_sayimi_olculemedi` olayı (`sinif` + kapalı-küme `neden`) — sohbet cevabı düşmez.
    `model_cagrilari` bu yolda ÖLÇÜLMÜYOR (`None`): api_server cevabının bu sayıyı taşıyıp taşımadığı
    Parça 0 (b)/(g) ölçümünü bekler (uydurma yasağı)."""

    def __init__(self, taban_url: str = "http://127.0.0.1:8642", zaman_asimi_s: float = 300.0,
                 _cagir=None, _anahtar=None):
        # bool bir int alt sınıfıdır: `True` 1 sn diye sessizce okunmasın (kadro `gunluk_tavan` emsali).
        if (isinstance(zaman_asimi_s, bool) or not isinstance(zaman_asimi_s, (int, float))
                or not math.isfinite(zaman_asimi_s) or zaman_asimi_s <= 0):
            raise ValueError(f"HermesTasiyici: zaman_asimi_s sonlu ve > 0 olmalı, gelen {zaman_asimi_s!r} — "
                             "sınırsız çağrı Telegram döngüsünü süresiz kilitler")
        self.taban_url = taban_url.rstrip("/")
        self.zaman_asimi_s = zaman_asimi_s
        self._cagir = _cagir or self._cagir_varsayilan
        self._anahtar = _anahtar or (lambda: secrets.credential_oku("API_SERVER_KEY"))

    @staticmethod
    def _cagir_varsayilan(url: str, govde: dict | None, basliklar: dict, zaman_asimi: float) -> dict:
        """`govde` varsa JSON POST (sohbet), `None` ise gövdesiz GET (oturum dökümü)."""
        if govde is None:
            istek = urllib.request.Request(url, method="GET", headers=dict(basliklar))
        else:
            istek = urllib.request.Request(url, data=json.dumps(govde).encode(), method="POST",
                                           headers={"Content-Type": "application/json", **basliklar})
        try:
            with urllib.request.urlopen(istek, timeout=zaman_asimi) as y:
                return json.load(y)
        except urllib.error.HTTPError as e:  # sinyalli: yalnız HTTP KODU yukarı gider; e.url/e.msg/str(e) BASILMAZ, zincir bastırılır
            hata = RuntimeError(f"api_server HTTP {e.code}")
            hata.http_kod = e.code  # sayım olayının `neden`i için (M-2) — tamsayı; URL/mesaj/anahtar taşımaz
            raise hata from None

    def sor(self, bot: str, mesaj: str, oturum: str) -> TasiyiciSonuc:
        if not _kadro.AD_DESENI.fullmatch(bot or ""):
            raise ValueError("HermesTasiyici: bot adı [a-z_] olmalı (URL yoluna girer)")
        anahtar = self._anahtar()
        if not anahtar:
            raise RuntimeError("API_SERVER_KEY credential yok")
        d = self._cagir(f"{self.taban_url}/p/{bot}/v1/chat/completions",
                        {"model": "hermes-agent", "messages": [{"role": "user", "content": mesaj}]},
                        {"Authorization": f"Bearer {anahtar}", "X-Hermes-Session-Id": oturum},
                        self.zaman_asimi_s)
        try:
            metin = d["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as e:  # sinyalli: biçim hatası sınıf adıyla yukarı; gövde basılmaz
            raise RuntimeError(f"api_server cevabı beklenmeyen biçimde ({type(e).__name__})") from None
        if not isinstance(metin, str):
            raise RuntimeError("api_server cevabında metin yok")
        return TasiyiciSonuc(metin, arac_cagrilari=self._arac_sayisi(bot, oturum, anahtar, metin))

    def _arac_sayisi(self, bot: str, oturum: str, anahtar: str, cevap: str) -> int | None:
        """Bu turun GERÇEK araç SONUCU sayısı (hizalı Hermes oturum dökümü); ölçülemezse `None` — 0 UYDURULMAZ."""
        try:
            if not _OTURUM_DESENI.fullmatch(oturum or ""):
                raise SayimOlculemedi("oturum_kimligi")
            d = self._cagir(f"{self.taban_url}/p/{bot}/api/sessions/{oturum}/messages", None,
                            {"Authorization": f"Bearer {anahtar}"}, self.zaman_asimi_s)
            return _bu_turun_arac_sonuclari(d, cevap)
        except Exception as e:  # sinyalli: olay (sınıf adı + kapalı-küme neden) + None → bota_sor UYARI_OLCULEMEDI ekler; sohbet cevabı düşmez
            obs.warn("bot_arac_sayimi_olculemedi", bot=bot, sinif=type(e).__name__, neden=_olculemedi_nedeni(e))
            return None


def _olculemedi_nedeni(e: Exception) -> str:
    """`bot_arac_sayimi_olculemedi` olayının `neden`i (inceleme M-2) — KAPALI küme, `str(e)` kullanılmaz:
    `oturum_kimligi` · `bicim` · `tur_hizasiz` (kendi denetimlerimiz, `SayimOlculemedi`) · `http_<kod>` ·
    `ag` (bağlantı/zaman aşımı, `OSError` ailesi) · `bicim` (JSON çözülemedi, `ValueError`) · `beklenmeyen`."""
    if isinstance(e, SayimOlculemedi):
        return e.neden
    kod = getattr(e, "http_kod", None)
    if isinstance(kod, int) and not isinstance(kod, bool):
        return f"http_{kod}"
    if isinstance(e, OSError):
        return "ag"
    if isinstance(e, ValueError):
        return "bicim"
    return "beklenmeyen"


def _bu_turun_arac_sonuclari(dokum, cevap: str) -> int:
    """Hermes oturum dökümünden (`{"data": [{"role", "content", "tool_calls"}, ...]}`) BU turun araç SONUCU sayısı.

    HİZA (inceleme I-1): döküm ancak SON mesajı `role == "assistant"` ve içeriği az önce alınan sohbet cevabına
    (`.strip()` sonrası) EŞİTSE bu turundur; değilse (bu tur henüz yazılmamış, sayfalanmış ya da devrilmiş oturum)
    `tur_hizasiz`. Hizasız döküm sayılsaydı önceki turun araç sonuçları bu turun araçsız cevabını SESSİZCE
    susturabilirdi (plan Review Focus 1).
    SAYIM (inceleme I-2): SON `role == "user"` mesajından sonraki `role == "tool"` mesajları — DÖNEN sonuçlar.
    `tool_calls` öğeleri (denemeler) SAYILMAZ: yanıtsız bir yapılandırılmış çağrı uyarıyı susturamaz.
    BİLİNEN SINIR: HATA dönen bir araç da sonuç sayılır (sayım içeriğe bakmaz) — ölçüm kartı kill-list'i bu
    sınırı yazar; "`arac_siz_veri` sıfır" her cevabın başarılı bir araca dayandığı anlamına GELMEZ.
    Biçim tanınmazsa ya da tur bulunamazsa `SayimOlculemedi` (içerik basılmaz) — çağıran `None`a çevirir."""
    mesajlar = dokum.get("data") if isinstance(dokum, dict) else None
    if not isinstance(mesajlar, list) or not mesajlar or not all(isinstance(m, dict) for m in mesajlar):
        raise SayimOlculemedi("bicim")
    son = mesajlar[-1]
    icerik = son.get("content")
    if son.get("role") != "assistant" or not isinstance(icerik, str) or icerik.strip() != cevap.strip():
        raise SayimOlculemedi("tur_hizasiz")
    son_kullanici = max((i for i, m in enumerate(mesajlar) if m.get("role") == "user"), default=None)
    if son_kullanici is None:
        raise SayimOlculemedi("bicim")
    return sum(1 for m in mesajlar[son_kullanici + 1:] if m.get("role") == "tool")


def veri_isareti(metin: str) -> str | None:
    """Cevabın veri taşıdığını gösteren İLK işaret — DETERMİNİSTİK, modele sorulmaz. Sıra: `"rakam"` · `"yuzde"` ·
    `"kaynak"` (katlanmış metinde `kaynak`/`source`/`.json`) · `"sozluk:<kök>"` (`VERI_SOZLUGU`, kelime başında
    kök öneki; `SOZLUK_DISI` kelimeleri ve `SOZLUK_DISI_ONEK` önekli kelimeler atlanır; metindeki ilk eşleşme) ·
    `"sembol:<X>"` (özgün metinde `[A-Z]{2,5}`, `SEMBOL_DISI` hariç) · `None`.
    Bilerek geniş: yanlış pozitif yalnız bir uyarı satırıdır ve defterin `veri_isareti` alanından ÖLÇÜLÜR;
    yanlış negatif operatöre doğrulanmamış veri demektir."""
    metin = metin or ""
    if _RAKAM.search(metin):
        return "rakam"
    if "%" in metin:
        return "yuzde"
    katli = _kadro.ad_katla(metin)
    if any(j in katli for j in _VERI_JETONLARI):
        return "kaynak"
    for kelime in _SOZLUK_DESENI.finditer(katli):
        if kelime.group(0) not in SOZLUK_DISI and not kelime.group(0).startswith(SOZLUK_DISI_ONEK):
            return f"sozluk:{kelime.group(1)}"
    for sembol in _SEMBOL_DESENI.findall(metin):
        if sembol not in SEMBOL_DISI:
            return f"sembol:{sembol}"
    return None


def veri_iceriyor(metin: str) -> bool:
    """`veri_isareti(metin) is not None` (brief arayüzü)."""
    return veri_isareti(metin) is not None


def _onekle(metin: str, onek: str | None) -> str:
    """`onek + "\\n" + metin`; önek yoksa ya da cevap zaten onunla başlıyorsa metin olduğu gibi."""
    if onek is None or metin.startswith(onek):
        return metin
    return f"{onek}\n{metin}"


def _utc(simdi: datetime | None) -> datetime:
    if simdi is None:
        return datetime.now(timezone.utc)
    if simdi.tzinfo is None:
        raise ValueError("bota_sor: `simdi` saat dilimli olmalı (kota günü UTC)")
    return simdi.astimezone(timezone.utc)


def gunluk_sayim(bot: str, gun: str) -> int:
    """`bot`un `gun` (UTC `YYYY-MM-DD`) içindeki `tur == "sohbet"` defter satırı sayısı. Defterin
    TAMAMI okunur: kuyruk okuması (`limit`) yoğun bir günde eksik sayıp kotayı sessizce aşardı."""
    return sum(1 for s in store.read_jsonl(DEFTER)
               if s.get("bot") == bot and s.get("tur") == "sohbet" and str(s.get("ts", "")).startswith(gun))


def _defter_yaz(satir: dict) -> None:
    try:
        store.append_jsonl(DEFTER, satir)
    except Exception as e:  # sinyalli: olay + cevap düşmez — defter kaybı görünür, operatörün cevabı kaybolmaz
        obs.warn("bot_defter_yazim_hatasi", bot=satir.get("bot"), tur=satir.get("tur"), sinif=type(e).__name__)


def _satir(an: datetime, bot: str, kanal: str, oturum: str, tur: str, mesaj: str,
           cevap: str | None, **ek) -> dict:
    temiz_mesaj = notify.scrub(mesaj)
    temiz_cevap = notify.scrub(cevap) if cevap is not None else None
    return {
        "ts": an.isoformat(timespec="seconds"), "bot": bot, "kanal": kanal, "oturum": oturum, "tur": tur,
        "mesaj": temiz_mesaj, "mesaj_sha": hashlib.sha256(temiz_mesaj.encode()).hexdigest()[:16],
        "cevap": temiz_cevap[:CEVAP_TAVANI] if temiz_cevap is not None else None,
        "cevap_uzunluk": len(cevap) if cevap is not None else None,
        "kesildi": temiz_cevap is not None and len(temiz_cevap) > CEVAP_TAVANI,
        **ek,
    }


def komut_oneki(metin: str) -> tuple[str, str] | None:
    """`hatırla:` / `unut:` komut TESPİTİNİN TEK KAYNAĞI: `("hatirla" | "unut", gövde)` ya da `None`.

    Hem `bota_sor` (dağıtım) hem Telegram dinleyicisi (`telegram_dinleyici.isle`, VERİ çiti
    kurulmadan ÖNCE operatörün kendi sözleri üzerinde) BUNU çağırır — iki ayrı regex ayrışır ve bir
    girdi bir yerde komut, öbüründe soru sayılır (Tur 2, inceleme I-1). Önek metnin BAŞINDA aranır;
    çit burada AYRIŞTIRILMAZ: sahte bir çit, alıntılanan veriden komut enjekte etmenin kapısı olurdu."""
    m = _KOMUT.match((metin or "").strip())
    if not m:
        return None
    ad = _kadro.ad_katla(m.group(1))
    return (ad, m.group(2).strip()) if ad in KOMUTLAR else None


def _komut(bot: str, mesaj: str, kanal: str, oturum: str, an: datetime, hafiza: Hafiza | None) -> str | None:
    """`hatırla:` / `unut:` dalı. Komut değilse `None` (soru modele gider)."""
    komut = komut_oneki(mesaj)
    if komut is None:
        return None
    ad, govde = komut
    if ad == "unut":
        return _unut(bot, mesaj, govde, kanal, oturum, an, hafiza)
    if not govde:
        cevap, durum = _HATIRLA_BOS, "bos_govde"
    elif hafiza is None:
        obs.warn("bot_hafiza_bagli_degil", bot=bot, kanal=kanal)
        cevap, durum = _HAFIZA_BAGLI_DEGIL, "bagli_degil"
    else:
        temiz = notify.scrub(govde)
        try:
            yazildi = bool(hafiza.yaz(bot, temiz, ("sabit_not", f"bot:{bot}", f"kanal:{kanal}")))
        except Exception as e:  # sinyalli: olay + "YAZILAMADI" cevabı; hafıza istisnası sohbet hatasına dönmez
            obs.warn("bot_hafiza_yazim_hatasi", bot=bot, sinif=type(e).__name__)
            yazildi = False
        if yazildi:
            cevap, durum = f"Not aldım: {temiz}", "yazildi"
        else:
            obs.warn("bot_hafiza_yazilamadi", bot=bot, kanal=kanal)
            cevap, durum = _HAFIZA_YAZILAMADI, "yazilamadi"
    _defter_yaz(_satir(an, bot, kanal, oturum, "hatirla", mesaj, cevap, hafiza_durumu=durum))
    return cevap


def _unutulan_listesi(unutulanlar) -> str:
    """`1) kesit 2) kesit` — kesit hafızadan gelir, operatöre gitmeden ÖNCE `notify.scrub`'dan geçer."""
    return " ".join(f"{i}) {notify.scrub(kesit)}" for i, (_, kesit) in enumerate(unutulanlar, 1))


def _unut(bot: str, mesaj: str, govde: str, kanal: str, oturum: str, an: datetime, hafiza: Hafiza | None) -> str:
    """`unut:` dalı — geri alınabilir unutma. Defter satırı `unutulan_idler` taşır (geri almanın yerel kaydı)."""
    unutulanlar: list = []
    if not govde:
        cevap, durum = _UNUT_BOS, "bos_govde"
    elif hafiza is None:
        obs.warn("bot_hafiza_bagli_degil", bot=bot, kanal=kanal)
        cevap, durum = _UNUT_BAGLI_DEGIL, "bagli_degil"
    else:
        try:
            unutulanlar = list(hafiza.unut(bot, notify.scrub(govde)))
        except Exception as e:  # sinyalli: olay + "UNUTULAMADI" cevabı; kısmi unutulanlar operatöre söylenir, sohbet hatasına dönmez
            obs.warn("bot_hafiza_unut_hatasi", bot=bot, kanal=kanal, sinif=type(e).__name__)
            unutulanlar = list(getattr(e, "unutulanlar", None) or [])
            cevap, durum = _UNUTULAMADI, "unutulamadi"
            if unutulanlar:
                cevap += f" Yine de unutulanlar (geri alınabilir): {_unutulan_listesi(unutulanlar)}"
        else:
            if unutulanlar:
                cevap, durum = f"Unuttum (geri alınabilir): {_unutulan_listesi(unutulanlar)}", "unutuldu"
            else:
                cevap, durum = _UNUT_ESLESME_YOK, "eslesme_yok"
    _defter_yaz(_satir(an, bot, kanal, oturum, "unut", mesaj, cevap, hafiza_durumu=durum,
                       unutulan_idler=[kimlik for kimlik, _ in unutulanlar]))
    return cevap


def bota_sor(bot: str, mesaj: str, kanal: str, oturum: str, *, tasiyici: Tasiyici | None = None,
             hafiza: Hafiza | None = None, simdi=None, kadro=None) -> str:
    """Kanal → bot → komut → kota → taşıyıcı → defter (modül başlığındaki DONUK sıra)."""
    if kanal not in KANALLAR:
        raise ValueError(f"bota_sor: kanal {kanal!r} izinli değil {KANALLAR}")
    b = _kadro.bot_bul(bot, kadro)
    if b is None or b.durum != "aktif":
        raise ValueError(f"bota_sor: {bot!r} kadroda aktif bir bot değil")
    an = _utc(simdi)
    komut_cevabi = _komut(b.ad, mesaj, kanal, oturum, an, hafiza)
    if komut_cevabi is not None:
        return komut_cevabi
    n = gunluk_sayim(b.ad, an.strftime("%Y-%m-%d"))
    if b.gunluk_tavan is not None and n >= b.gunluk_tavan:
        cevap = f"@{b.ad} bugünlük kotam doldu ({n}/{b.gunluk_tavan}); yarın (UTC) yeniden."
        _defter_yaz(_satir(an, b.ad, kanal, oturum, "kota_doldu", mesaj, cevap, kota_bugun=n))
        return cevap
    tasiyici = tasiyici or HermesTasiyici()
    t0 = time.monotonic()
    try:
        sonuc = tasiyici.sor(b.ad, mesaj, oturum)
    except Exception as e:  # sinyalli: defter `tur: hata` + sınıf adı, istisna YUKARI fırlar
        _defter_yaz(_satir(an, b.ad, kanal, oturum, "hata", mesaj, None, hata=type(e).__name__,
                           sure_s=round(time.monotonic() - t0, 3), kota_bugun=n))
        raise
    arac = sonuc.arac_cagrilari
    arac_olculemedi = arac is None
    # Sayı ölçülemediyse "araçsız veri mi" de BİLİNMEZ: False yazmak "temiz" demek olurdu (uydurma yasağı).
    isaret = veri_isareti(sonuc.metin)
    arac_siz_veri = None if arac_olculemedi else (arac == 0 and isaret is not None)
    cevap = _onekle(sonuc.metin, UYARI_OLCULEMEDI if arac_olculemedi else UYARI_ARACSIZ if arac_siz_veri else None)
    _defter_yaz(_satir(an, b.ad, kanal, oturum, "sohbet", mesaj, cevap,
                       sure_s=round(time.monotonic() - t0, 3), arac_cagrilari=arac,
                       arac_siz_veri=arac_siz_veri, arac_olculemedi=arac_olculemedi, veri_isareti=isaret,
                       model_cagrilari=sonuc.model_cagrilari, kota_bugun=n + 1))
    return cevap
