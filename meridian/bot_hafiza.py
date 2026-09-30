"""bot_hafiza.py — konuşan bot filosunun Hindsight hafıza YAZICISI: `bot_kanal.Hafiza` protokolünün gerçek uygulaması
(spec docs/superpowers/specs/2026-09-29-konusan-bot-filosu-design.md §3.4; plan 2026-09-29 Parça 1b-ön Görev 2).

NE YAPAR. `bota_sor`un DETERMİNİSTİK `hatırla:` / `unut:` dalları ve sohbet dönüşü kaydı bu sınıfı çağırır (model
çağırmaz):
  * `yaz`     → retain `POST /v1/default/banks/bot-<ad>/memories` (senkron, `async: false`); etiketleri çağıran verir.
  * `donus_yaz` → AYNI uca retain, `async: true` (Parça 1b G4 Görev 1): Hindsight çıkarımı arka planda koşar ve uç
    hemen `success` + `operation_id` döner (A1 OpenAPI `RetainRequest`/`RetainResponse`, 2026-09-30) — dönüş kaydı
    cevabı çıkarım süresince bekletmez; kendi KISA zaman aşımı `DONUS_ZAMAN_ASIMI_S` (async kabul gecikmesi G3c'de
    ölçülür). İçerik `"Operatör: <mesaj>\\n@<bot>: <cevap>"`; her parça ÖNCE `notify.scrub`,
    SONRA `DONUS_TAVANI`; bağlam `DONUS_BAGLAMI`, `metadata.kaynak` `DONUS_KAYNAGI`. Spec §3.4 (2026-09-30
    düzeltmesi): Hermes `auto_retain` KAPALI — sohbet dönüşünü hafızaya YALNIZ bu yol yazar.
  * `unut`    → önce recall `POST …/memories/recall` (`budget: low`), sonra sonuç SIRASIYLA (upstream'in kendi
    sıralaması = recall skoru) en fazla `UNUT_TAVANI` bellek için `PATCH …/memories/{id}`
    `{"state": "invalidated", "reason": "operatör unut: <ifade> (<ISO>)"}`. Emekliye ayrılan `(id, kesit)`
    listesi döner; `bota_sor` operatöre hangi metinleri unuttuğunu söyler.
  * `geri_al` → `PATCH …/memories/{id}` `{"state": "valid"}` (bu parçada API fonksiyonu, komut değil).
  * `ara`     → SALT-OKUR recall (Parça 1b G1 Görev 2; MCP araç sunucusunun `bot_hafizasi_ara` aracı): TEK
    `POST …/memories/recall`, bellek durumu DEĞİŞMEZ; `[(tarih, metin), …]` en fazla `k` öğe, upstream sırasıyla.

ÇAĞIRANLAR. `bota_sor` `hafiza` verilmezse bu sınıfı ÜRETİM varsayılanı olarak kurar (Parça 1b G4 Görev 1);
`mcp_server`in `--bot` kipindeki `bot_hafizasi_ara` aracı `ara`yı çağırır. `bota_sor`u üretimde çağıran bir süreç
henüz YOK (Telegram `main()` G4 Görev 3'te gelir; canlı açılış G3b sırlarından sonradır).

DEĞİŞMEZLER.
  * `ara` SALT-OKURDUR: recall dışında hiçbir istek atmaz (çivi v596 — tek çağrı, PATCH/DELETE yok). Tarih
    alanı ölçülmüş okuyucunun (`deploy/hindsight/hafiza_sor.sh`) sırasıyla okunur, yoksa "(tarih yok)" —
    uydurulmaz; öğe nesne değilse "sonuç yok" SAYILMAZ, `RuntimeError`.
  * KALICI SİLME YOK: yalnız `state` alanı değişir (`invalidated` recall'dan düşürür, arşive taşır, `valid` ile
    geri döner — ölçüldü, A1 openapi 2026-09-29). Kaynakta silme yöntemi yoktur (çivi v596).
  * TAVAN: tek `unut` en fazla `UNUT_TAVANI` bellek emekliye ayırır; ilk `UNUT_TAVANI` sonucun kimliklerinden biri
    bile tanınmazsa (yok / URL yoluna uygun değil) HİÇBİR PATCH atılmaz — yarım iş sessiz kalırdı.
  * TANIMADIĞINI "BOŞ" SAYMAZ: recall zarfı ölçülmüş okuyucu (`deploy/hindsight/hafiza_sor.sh`) kadar toleranslıdır
    (liste ya da `items`/`results`/`memories`/`data`), ama hiçbiri tutmazsa `RuntimeError` — "eşleşme yok" demek
    ölçülmemiş bir iddia olurdu. Retain cevabında `success` okunamazsa da "yazıldı" UYDURULMAZ.
  * KISMİ HATA GÖRÜNÜR: bir PATCH düşerse istisna, o âna dek emekliye ayrılanları `unutulanlar` özniteliğinde
    taşır (`bota_sor` onları operatöre söyler — geri alabilsin diye).
  * SIR: kiracı anahtarı HER çağrıda `secrets.credential_oku(secrets.HAFIZA_KRED_ADI)` ile okunur (LoadCredential
    kanalı); yoksa istek HİÇ atılmaz. Anahtar yalnız `Authorization` başlığındadır; HTTP hatası yalnız DURUM KODUYLA,
    ağ/başlık hatası yalnız SINIF ADIYLA `RuntimeError`a çevrilir, zincir bastırılır — `http.client`in geçersiz
    başlık hatası başlık DEĞERİNİ (anahtarı) mesajına yazar. Recall kesitleri ÖNCE `notify.scrub`, SONRA tavan.
  * ZAMAN AŞIMI ZORUNLU: sonlu ve > 0 olmayan değer kurucuda `ValueError` (`bot_kanal.HermesTasiyici` emsali);
    asılı bir Hindsight Telegram döngüsünü de asardı.
  * GİRDİ URL YOLUNA GİRER: bot adı `kadro.AD_DESENI`, bellek kimliği `_KIMLIK_DESENI` ile HTTP'den ÖNCE doğrulanır.
  * HATA NEDENİ YAPISALDIR: bu sınıfın attığı her `RuntimeError` KAPALI küme bir `neden` özniteliği taşır
    (`HATA_NEDENLERI` + `http_<kod>`), raise ANINDA sınıfından işaretlenir — mesaj metni hiçbir yerde ayrıştırılmaz.
    Olay alanına çeviren TEK yer `hata_nedeni`dir (işaretsiz ya da küme dışı → `beklenmeyen`); `bot_kanal`in
    `bot_hafiza_*` olayları onu çağırır. Bu modül `obs` ithal ETMEZ (üreteç `ops/sohbet_profili_uret.py` onu
    pytest dışında yükler; ithal zinciri canlı deftere ulaşmamalı — çivi v599).

TEK KAYNAK. Taban ve kiracı anahtarı adı `secrets`ten gelir (`api` takma ad verir). `BANKA_KOKU` ve
`UNUT_RECALL_MAX_TOKENS` `api`nin ölçülmüş sabitlerinin KOPYASIDIR — bu modül `api`yi (FastAPI uygulaması)
ithal etmez; ayrışma çivisi v596 `test_api_kopyalariyla_ayrismaz`.

YASA 6. Bu modül dosya yazmaz; yazdığı tek yer Hindsight bankasıdır (okuyucuları: sohbet profillerinin Hermes
`auto_recall`u — `deploy/hermes/sohbet/profiles/*/hindsight/config.json`, `ara`/`bot_hafizasi_ara`, `unut` recall'u).
Emekliye ayrılan kimliklerin yerel kaydı `bot_kanal` defter satırının `unutulan_idler` alanıdır.
"""
from __future__ import annotations

import http.client
import json
import math
import re
import urllib.error
import urllib.request
from datetime import datetime, timezone

from . import kadro as _kadro, notify, secrets

#: Her HTTP çağrısının zaman aşımı (sn) — spec §3.4 `HINDSIGHT_TIMEOUT=10` (Parça 0 (c): küçük bankada recall
#: low 4,2 s). `api.HAFIZA_ZAMAN_ASIMI_S` (2 s) pano vekilinin AYRI sözleşmesidir; bu değer ondan türemez.
#: SENKRON retain'in süresi ÖLÇÜLMEDİ (retain LLM çıkarımı koşar) — Parça 1b kablolamasından önce ölçülür.
HAFIZA_ZAMAN_ASIMI_S = 10.0
#: `donus_yaz`in AYRI ve KISA zaman aşımı (sn; soket İŞLEMİ başına) — Rol-1 kararı 2026-09-30 (G4 Görev 1 Tur 2, K-1).
#: Dönüş kaydı operatörün cevabıyla aynı turda SENKRON koşar (`hafiza_durumu` aynı defter satırında kalsın diye arka
#: plana alınmadı); `async: true` kabulü sağlıklı Hindsight'ta anında döner, ASILI Hindsight'ta cevap soket işlemi
#: başına en fazla bu kadar gecikir. `HAFIZA_ZAMAN_ASIMI_S` DEĞİŞMEZ (v599 onu Hermes profil yapılandırmasına bağlar;
#: `yaz`/`unut`/`ara`/`geri_al` onu kullanır). Async kabul gecikmesi G3c'de ölçülür — bu değer ölçüm değil tavandır.
DONUS_ZAMAN_ASIMI_S = 3.0
#: Tek `unut` en fazla bu kadar belleği emekliye ayırır (plan Review Focus 2: belirsiz ifade → alakasız bellek).
UNUT_TAVANI = 3
#: Hindsight banka kökü — `api._HAFIZA_BANK_KOKU` kopyası (ayrışma çivisi v596).
BANKA_KOKU = "/v1/default/banks"
#: Recall `max_tokens` — upstream'in KENDİ varsayılanı (openapi v0.9.2 `RecallRequest`; `api.HAFIZA_RECALL_TOKEN_TAVANI`
#: şerhi). Açık gönderilir ki upstream varsayılanı sessizce değişirse davranış değişmesin; daha küçüğü ölçülmemiş bir
#: eşik olurdu. Kopya — ayrışma çivisi v596.
UNUT_RECALL_MAX_TOKENS = 4096
#: Recall bütçesi — spec §3.4 `HINDSIGHT_BUDGET=low`.
UNUT_RECALL_BUTCESI = "low"
#: Operatöre gösterilen kesit tavanı (karakter; plan arayüzü `metin_kesiti≤80`).
KESIT_TAVANI = 80
#: `ara` sonucunun metin tavanı (karakter) — ölçülmüş okuyucu `deploy/hindsight/hafiza_sor.sh` sonuç başına 600
#: karakter basar. Modele giden toplam ayrıca araç çıktısı tavanından geçer (MCP: sohbetin çit + kesit gövdesi).
ARA_KESIT_TAVANI = 600
#: `ara` tarih alanları, ölçülmüş okuyucunun okuma sırasıyla (olay anı, yoksa anılma anı).
_ARA_TARIH_ALANLARI = ("occurred_start", "mentioned_at")
#: Retain `context` ve `metadata` — plan 2026-09-29 Görev 2 (DONUK).
NOT_BAGLAMI = "operatör notu"
NOT_KAYNAGI = "operator"
#: Sohbet dönüşü kaydı (`donus_yaz`) — plan 2026-09-30 G4 Görev 1, Rol-1 kararı (DONUK). Tavan karakter cinsinden,
#: parça başına (operatör mesajı ve bot cevabı AYRI AYRI); tam metnin yerel kaydı `bot_kanal` defteridir.
DONUS_TAVANI = 2000
DONUS_BAGLAMI = "sohbet dönüşü"
DONUS_KAYNAGI = "bot_kanal"
#: Hata `neden`inin KAPALI kümesi (+ `http_<kod>`, `_HTTP_NEDENI`). `bot_hafiza_*` olaylarının tek sözlüğü.
HATA_NEDENLERI = ("anahtar_yok", "ag", "zaman_asimi", "bicim", "beklenmeyen")
_HTTP_NEDENI = re.compile(r"http_[1-5][0-9]{2}")
#: Ölçülen recall zarfları (`deploy/hindsight/hafiza_sor.sh` okuyucusuyla aynı sıra).
_RECALL_ZARFLARI = ("items", "results", "memories", "data")
#: Bellek kimliği URL YOLUNA girer: upstream UUID üretir (openapi örneği `123e4567-e89b-…`); `/`, `..`, `?`, `#`
#: yolu başka bir uca taşırdı. Desene uymayan kimlikte istek ATILMAZ.
_KIMLIK_DESENI = re.compile(r"[A-Za-z0-9_-]{1,128}")
_ANAHTAR_YOK = "hindsight kiracı anahtarı credential yok"


def _simdi_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _hata(mesaj: str, neden: str) -> RuntimeError:
    """Yapısal `neden` taşıyan `RuntimeError` (sınıf adı olaylarda `RuntimeError` kalır). `mesaj` sabit metindir —
    içerik, URL ya da anahtar TAŞIMAZ."""
    hata = RuntimeError(mesaj)
    hata.neden = neden
    return hata


def _ag_nedeni(e: BaseException) -> str:
    """`urlopen`/okuma istisnasının SINIFINDAN neden: soket zaman aşımı (okurken `TimeoutError`, bağlanırken urllib'in
    `URLError(reason=TimeoutError)` sarmalı) `zaman_asimi`; diğer `OSError`/`HTTPException` (bağlantı reddi, sıfırlama,
    yarım cevap) `ag`; `ValueError` (geçersiz başlık/URL — istemci tarafı) `beklenmeyen`."""
    if isinstance(e, TimeoutError) or isinstance(getattr(e, "reason", None), TimeoutError):
        return "zaman_asimi"
    if isinstance(e, (OSError, http.client.HTTPException)):
        return "ag"
    return "beklenmeyen"


def hata_nedeni(e: BaseException) -> str:
    """`bot_hafiza_*` olaylarının `neden` alanı — TÜRETİMİN TEK YERİ. İstisnanın yapısal `neden` özniteliği KAPALI
    kümedeyse (`HATA_NEDENLERI` ya da `http_<3 hane>`) o; işaretsiz ya da küme dışıysa `beklenmeyen`. `str(e)`
    OKUNMAZ: mesaj metninden türetmek, metni değişen bir hatayı sessizce yanlış sınıfa düşürürdü."""
    neden = getattr(e, "neden", None)
    if isinstance(neden, str) and (neden in HATA_NEDENLERI or _HTTP_NEDENI.fullmatch(neden)):
        return neden
    return "beklenmeyen"


def _kesit(metin, tavan: int = KESIT_TAVANI) -> str:
    """Tek satırlık kesit: ÖNCE scrub (tavan bir anahtarı ortadan bölüp desenin dışına itmesin), sonra boşluk
    katlama, sonra `tavan` (varsayılan `KESIT_TAVANI`; `ara` kendi tavanını verir). Metin yoksa bunu SÖYLER —
    boş kesit uydurulmaz."""
    if not isinstance(metin, str) or not metin.strip():
        return "(metin yok)"
    tek = " ".join(notify.scrub(metin).split())
    return tek if len(tek) <= tavan else tek[:tavan - 1] + "…"


def _tarih(kayit: dict) -> str:
    """Belleğin tarihi, `_ARA_TARIH_ALANLARI` sırasıyla; hiçbiri dolu bir dizge değilse bunu SÖYLER (uydurulmaz)."""
    for alan in _ARA_TARIH_ALANLARI:
        deger = kayit.get(alan)
        if isinstance(deger, str) and deger.strip():
            return deger.strip()
    return "(tarih yok)"


def _recall_dizisi(veri) -> list:
    """Recall cevabından sonuç dizisi; zarf tanınmazsa `RuntimeError` (içerik basılmaz)."""
    if isinstance(veri, list):
        return veri
    if isinstance(veri, dict):
        for alan in _RECALL_ZARFLARI:
            if isinstance(veri.get(alan), list):
                return veri[alan]
    raise _hata("hindsight recall zarfı tanınmadı", "bicim")


class HindsightHafiza:
    """`bot_kanal.Hafiza` — Hindsight HTTP API'si (A1 self-host, `bot-<ad>` bankası). Ayrıntı modül başlığında."""

    def __init__(self, taban_url: str = secrets.HAFIZA_TABAN_URL, zaman_asimi_s: float = HAFIZA_ZAMAN_ASIMI_S,
                 _cagir=None, _anahtar=None):
        # bool bir int alt sınıfıdır: `True` 1 sn diye sessizce okunmasın (`bot_kanal.HermesTasiyici` emsali).
        if (isinstance(zaman_asimi_s, bool) or not isinstance(zaman_asimi_s, (int, float))
                or not math.isfinite(zaman_asimi_s) or zaman_asimi_s <= 0):
            raise ValueError(f"HindsightHafiza: zaman_asimi_s sonlu ve > 0 olmalı, gelen {zaman_asimi_s!r} — "
                             "sınırsız çağrı Telegram döngüsünü süresiz kilitler")
        self.taban_url = taban_url.rstrip("/")
        self.zaman_asimi_s = zaman_asimi_s
        self._cagir = _cagir or self._cagir_varsayilan
        self._anahtar = _anahtar or (lambda: secrets.credential_oku(secrets.HAFIZA_KRED_ADI))

    @staticmethod
    def _cagir_varsayilan(yontem: str, url: str, govde: dict | None, basliklar: dict, zaman_asimi: float):
        """JSON istek (`govde` varsa `Content-Type: application/json`); cevap JSON çözülür, boş gövde `None`."""
        veri = None if govde is None else json.dumps(govde, ensure_ascii=False).encode("utf-8")
        tum = dict(basliklar) if veri is None else {"Content-Type": "application/json", **basliklar}
        istek = urllib.request.Request(url, data=veri, method=yontem, headers=tum)
        try:
            with urllib.request.urlopen(istek, timeout=zaman_asimi) as y:
                ham = y.read()
        except urllib.error.HTTPError as e:  # sinyalli: yalnız HTTP KODU yukarı gider; e.url/e.msg/str(e) BASILMAZ, zincir bastırılır
            hata = _hata(f"hindsight HTTP {e.code}", f"http_{e.code}")
            hata.http_kod = e.code
            raise hata from None
        except (OSError, ValueError, http.client.HTTPException) as e:  # sinyalli: ağ/zaman aşımı/geçersiz başlık/yarım cevap — yalnız SINIF adı; mesaj anahtarı taşıyabilir
            raise _hata(f"hindsight {type(e).__name__}", _ag_nedeni(e)) from None
        if not ham.strip():
            return None
        try:
            return json.loads(ham)
        except ValueError:  # sinyalli: biçim hatası sabit metinle yukarı; gövde basılmaz
            raise _hata("hindsight cevabı JSON değil", "bicim") from None

    # ---- iç boğaz -------------------------------------------------------------------------------------------

    def _banka_yolu(self, bot: str) -> str:
        if not isinstance(bot, str) or not _kadro.AD_DESENI.fullmatch(bot):
            raise ValueError("HindsightHafiza: bot adı [a-z_] olmalı (banka kimliği URL yoluna girer)")
        return f"{self.taban_url}{BANKA_KOKU}/bot-{bot}"

    def _anahtar_al(self) -> str:
        anahtar = self._anahtar()
        if not anahtar:
            raise _hata(_ANAHTAR_YOK, "anahtar_yok")
        return anahtar

    def _istek(self, yontem: str, url: str, govde: dict, anahtar: str, zaman_asimi: float | None = None):
        """`zaman_asimi` verilmezse kurucunun `zaman_asimi_s`i; yalnız `donus_yaz` `DONUS_ZAMAN_ASIMI_S` verir."""
        return self._cagir(yontem, url, govde, {"Authorization": f"Bearer {anahtar}"},
                           self.zaman_asimi_s if zaman_asimi is None else zaman_asimi)

    def _recall(self, banka: str, ifade: str, anahtar: str) -> list:
        """TEK recall gövdesi (`unut` ve `ara`): `budget` + upstream'in kendi `max_tokens` varsayılanı; zarf
        tanınmazsa `RuntimeError`."""
        cevap = self._istek("POST", f"{banka}/memories/recall",
                            {"query": ifade, "budget": UNUT_RECALL_BUTCESI, "max_tokens": UNUT_RECALL_MAX_TOKENS},
                            anahtar)
        return _recall_dizisi(cevap)

    @staticmethod
    def _kimlik(memory_id) -> str:
        if not isinstance(memory_id, str) or not _KIMLIK_DESENI.fullmatch(memory_id):
            raise ValueError("HindsightHafiza: bellek kimliği [A-Za-z0-9_-] olmalı (URL yoluna girer)")
        return memory_id

    # ---- Hafiza protokolü -----------------------------------------------------------------------------------

    def _retain(self, banka: str, oge: dict, asenkron: bool, anahtar: str, zaman_asimi: float | None = None) -> bool:
        """TEK retain çağrısı (`yaz` ve `donus_yaz`): `success` alanı okunamazsa "yazıldı" UYDURULMAZ (`bicim`)."""
        cevap = self._istek("POST", f"{banka}/memories", {"items": [oge], "async": asenkron}, anahtar, zaman_asimi)
        if not isinstance(cevap, dict) or not isinstance(cevap.get("success"), bool):
            raise _hata("hindsight retain cevabı tanınmadı (success alanı yok)", "bicim")
        return cevap["success"]

    def yaz(self, bot: str, metin: str, etiketler: tuple[str, ...]) -> bool:
        """Senkron retain; `success` alanı `True` ise `True`, `False` ise `False`; okunamazsa `RuntimeError`."""
        banka = self._banka_yolu(bot)
        anahtar = self._anahtar_al()
        oge = {"content": metin, "timestamp": _simdi_iso(), "context": NOT_BAGLAMI, "tags": list(etiketler),
               "metadata": {"kaynak": NOT_KAYNAGI}}
        return self._retain(banka, oge, False, anahtar)

    def donus_yaz(self, bot: str, mesaj: str, cevap: str, etiketler: tuple[str, ...]) -> bool:
        """Sohbet dönüşü kaydı: `async: true` retain (modül başlığı). İçerik parçaları ÖNCE scrub SONRA `DONUS_TAVANI`
        (ters sırada tavan bir anahtarı ortadan böler ve yarısı desenin dışında kalıp kalıcı bankaya sızar). Dönüş
        `yaz` ile aynı sözleşme: `success`; okunamazsa `RuntimeError` (`bicim`). Zaman aşımı `DONUS_ZAMAN_ASIMI_S`
        (kurucunun `zaman_asimi_s`i DEĞİL — cevabı bekleten yol kısa tutulur)."""
        banka = self._banka_yolu(bot)
        anahtar = self._anahtar_al()
        icerik = (f"Operatör: {notify.scrub(mesaj)[:DONUS_TAVANI]}\n"
                  f"@{bot}: {notify.scrub(cevap)[:DONUS_TAVANI]}")
        oge = {"content": icerik, "timestamp": _simdi_iso(), "context": DONUS_BAGLAMI, "tags": list(etiketler),
               "metadata": {"kaynak": DONUS_KAYNAGI}}
        return self._retain(banka, oge, True, anahtar, DONUS_ZAMAN_ASIMI_S)

    def unut(self, bot: str, ifade: str) -> list[tuple[str, str]]:
        """Recall + en fazla `UNUT_TAVANI` bellek için geri alınabilir `invalidated`. Dönüş `[(id, kesit), …]`."""
        banka = self._banka_yolu(bot)
        ifade = ifade.strip() if isinstance(ifade, str) else ""
        if not ifade:
            raise ValueError("HindsightHafiza.unut: boş ifade — recall en yakın rastgele bellekleri döndürür")
        anahtar = self._anahtar_al()
        secilen = []
        for kayit in self._recall(banka, ifade, anahtar)[:UNUT_TAVANI]:
            kimlik = kayit.get("id") if isinstance(kayit, dict) else None
            if not isinstance(kimlik, str) or not _KIMLIK_DESENI.fullmatch(kimlik):
                raise _hata("hindsight recall sonucunda bellek kimliği tanınmadı — hiçbir şey unutulmadı", "bicim")
            secilen.append((kimlik, _kesit(kayit.get("text"))))
        neden = f"operatör unut: {ifade} ({_simdi_iso()})"
        unutulanlar: list[tuple[str, str]] = []
        for kimlik, kesit in secilen:
            try:
                self._istek("PATCH", f"{banka}/memories/{kimlik}", {"state": "invalidated", "reason": neden}, anahtar)
            except Exception as e:  # sinyalli: istisna YUKARI fırlar; o âna dek emekliye ayrılanları taşır (operatör geri alabilsin)
                e.unutulanlar = list(unutulanlar)
                raise
            unutulanlar.append((kimlik, kesit))
        return unutulanlar

    def ara(self, bot: str, soru: str, k: int = 5) -> list[tuple[str, str]]:
        """SALT-OKUR recall: TEK POST, bellek durumu DEĞİŞMEZ. Dönüş `[(tarih, metin), …]` en fazla `k` öğe,
        upstream sırasıyla; metin ÖNCE scrub SONRA `ARA_KESIT_TAVANI`. Boş soru / geçersiz `k` HTTP'den ÖNCE
        `ValueError`; nesne olmayan sonuç öğesi `RuntimeError` ("sonuç yok" sayılmaz)."""
        banka = self._banka_yolu(bot)
        soru = soru.strip() if isinstance(soru, str) else ""
        if not soru:
            raise ValueError("HindsightHafiza.ara: boş soru — recall en yakın rastgele bellekleri döndürür")
        # bool bir int alt sınıfıdır: `True` 1 diye sessizce okunmasın.
        if isinstance(k, bool) or not isinstance(k, int) or k < 1:
            raise ValueError(f"HindsightHafiza.ara: k pozitif tamsayı olmalı, gelen {k!r}")
        anahtar = self._anahtar_al()
        sonuc: list[tuple[str, str]] = []
        for kayit in self._recall(banka, soru, anahtar)[:k]:
            if not isinstance(kayit, dict):
                raise _hata("hindsight recall sonucu tanınmadı (öğe bir nesne değil)", "bicim")
            sonuc.append((_tarih(kayit), _kesit(kayit.get("text"), ARA_KESIT_TAVANI)))
        return sonuc

    def geri_al(self, bot: str, memory_id: str) -> bool:
        """`unut`un tersi: `state: valid` (bellek recall'a döner). Başarıda `True`; hata `RuntimeError`."""
        banka = self._banka_yolu(bot)
        kimlik = self._kimlik(memory_id)
        anahtar = self._anahtar_al()
        self._istek("PATCH", f"{banka}/memories/{kimlik}", {"state": "valid"}, anahtar)
        return True
