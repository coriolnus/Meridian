# Konuşan bot filosu — Kadro listesi + Telegram dinleyicisi (kod, dağıtımsız) Uygulama Planı

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Spec §3.1 kadro listesini (21 bot, tek kaynak) ve §3.5 Telegram dinleyicisinin yönlendirme/yetki/yanıt çekirdeğini, bot sunucusundan bağımsız (enjekte edilen `bota_sor` ile) yazıp testlemek.

**Architecture:** `deploy/hermes/kadro.yaml` tek kaynak; `meridian/kadro.py` yükler + doğrular + sorgular. `meridian/telegram_dinleyici.py` saf yönlendirme (`yonlendir`), tek güncelleme işleyici (`isle`, bağımlılıklar enjekte), uzun yoklama (`guncellemeleri_al`) ve döngü (`dongu`); cevap `meridian/notify.py`deki TEK teslimat yolundan (`yanitla`, `scrub` korunur). Systemd birimi ve dağıtım BU PLANDA YOK (Parça 1 `bota_sor`u gelince).

**Tech Stack:** Python 3 stdlib (`urllib`, `dataclasses`, `hashlib`), PyYAML (depoda var), pytest (`.venv/bin/python -m pytest`).

**Spec:** `docs/superpowers/specs/2026-09-29-konusan-bot-filosu-design.md` (§0 K3/K6/K7, §2.2, §3.1, §3.5, §4, §7)

## Global Constraints

- Kadro 21 bot, adlar: sef bekci karne kod karar ayna olay kacan veri butce yol nobet denetci civici devir derleyici olcum tasarimci yabanci piyasa hipotez.
- Durumlar DONUK: `aktif` · `sirada` · `kilitli`; dalgalar: `canli` · `1` · `2` · `3` · `kilitli`; hafıza: `kendi` · `hepsi` (yalnız `sef` `hepsi` — K6).
- `aktif` botlar ↔ `deploy/hermes/profiles/*` dizinleri BİREBİR (tek-kaynak yasası).
- `gunluk_tavan` Parça 0 ölçümü gelene dek `null` + `gunluk_tavan_neden` (uydurma yasağı).
- Telegram: YALNIZ `secrets.get("TELEGRAM_CHAT_ID")` sohbeti; yabancı mesaja CEVAP YOK, `obs.warn("bot_yabanci_mesaj", …)` ile SAYILIR, ham sohbet kimliği log'a yazılmaz (sha256 ilk 12).
- Sır: bot jetonu yalnız URL yolunda (Telegram API zorunluluğu, `notify.send` emsali); log/olay/istisna metnine düşmez.
- Yasa 4: her `except` işaretli (`# sessiz-yutma: <≥20 karakter gerekçe>`) ya da sinyalli. Yasa 6: `state/telegram_ofset.json` okuyucusu dinleyicinin kendisi (beyan modül başlığında).
- Test adlarında `FAILED`/`ERROR` jetonu yok; yeni test numaraları v591 (kadro), v592 (telegram).
- Kod yorumlarında `dosya.py:NNN` çapası yok (sembol çapası).

## Review Focus

1. Kadrodaki bir `aktif` bot profili silinir/yeniden adlandırılırsa yönlendirme sessizce yanlış bota gider → v591 kadro↔profil eşitliği çivisi (Görev 1).
2. `@Bekci:` / `@bekci,` / `@BEKCI` gibi büyük harf ve noktalama varyantları tanınmazsa operatör "bilinmeyen bot" alır → Görev 2 `yonlendir` testleri varyantları kapsar.
3. Rapor başlığı ileride değişirse (ör. `@sef` HAM → sıralı başlık) rapora yanıt yönlendirmesi kırılır → v591 imza↔`BASLIK` önek çivisi (Görev 1).
4. `bota_sor` istisna fırlatırsa operatör sessizlik görür → Görev 2 `isle` hata yolu testi (cevap + `bot_sohbet_hatasi` olayı).
5. Telegram yoklaması ağ hatası verirse döngü ölmemeli ve jeton log'a düşmemeli → Görev 2 `guncellemeleri_al` hata testi (boş liste + jetonsuz olay).

---

### Task 1: Kadro listesi (`deploy/hermes/kadro.yaml` + `meridian/kadro.py`)

**Files:**
- Create: `deploy/hermes/kadro.yaml`
- Create: `meridian/kadro.py`
- Test: `tests/test_kadro_v591.py`

**Interfaces:**
- Produces:
  - `@dataclass(frozen=True) class Bot: ad: str; rol: str; dalga: str; durum: str; araclar: tuple[str, ...]; zamanli_is: str | None; imza: str | None; hafiza: str; gunluk_tavan: int | None; gunluk_tavan_neden: str | None`
  - `KADRO_YOLU: Path` (= `config.ROOT / "deploy/hermes/kadro.yaml"`)
  - `DURUMLAR = ("aktif", "sirada", "kilitli")`, `DALGALAR = ("canli", "1", "2", "3", "kilitli")`, `HAFIZA_KIPLERI = ("kendi", "hepsi")`
  - `PLANLI_ARACLAR = ("is_iste", "bot_hafizasi_ara")` (Parça 1'de yazılacak araçlar — bilinçli beyan)
  - `def kadro_yukle(yol: Path | None = None) -> tuple[Bot, ...]` — doğrulama hatasında `ValueError` (mesaj hatalı alanı ve botu adlandırır)
  - `def bot_bul(ad: str, kadro: tuple[Bot, ...] | None = None) -> Bot | None` (büyük/küçük harf duyarsız)
  - `def aktif_botlar(kadro: tuple[Bot, ...] | None = None) -> tuple[Bot, ...]`
  - `def imzadan_bot(metin: str, kadro: tuple[Bot, ...] | None = None) -> Bot | None` — metnin İLK satırı bir `aktif` botun `imza`sıyla başlıyorsa o bot

- [ ] **Step 1: Başarısız testleri yaz** — `tests/test_kadro_v591.py`:

```python
"""v591 — konuşan filo kadro listesi (spec 2026-09-29 §2.2/§3.1): tek kaynak + doğrulama + sorgu."""
import re
from pathlib import Path

import pytest
import yaml

from meridian import config, kadro

ROOT = config.ROOT
BEKLENEN_21 = {"sef", "bekci", "karne", "kod", "karar", "ayna", "olay", "kacan", "veri", "butce", "yol",
               "nobet", "denetci", "civici", "devir", "derleyici", "olcum", "tasarimci", "yabanci", "piyasa",
               "hipotez"}


def _yaz(tmp_path, botlar):
    p = tmp_path / "kadro.yaml"
    p.write_text(yaml.safe_dump({"botlar": botlar}, allow_unicode=True), encoding="utf-8")
    return p


def _gecerli(ad="sef", **k):
    b = {"ad": ad, "rol": "r", "dalga": "canli", "durum": "aktif", "araclar": ["pano_ozeti"],
         "zamanli_is": None, "imza": None, "hafiza": "kendi", "gunluk_tavan": None,
         "gunluk_tavan_neden": "olculmedi"}
    b.update(k)
    return b


def test_kadro_21_bot_ve_adlar_birebir():
    assert {b.ad for b in kadro.kadro_yukle()} == BEKLENEN_21


def test_aktif_botlar_profil_dizinleriyle_birebir():
    profiller = {p.name for p in (ROOT / "deploy/hermes/profiles").iterdir() if p.is_dir()}
    assert {b.ad for b in kadro.aktif_botlar()} == profiller


def test_dalgalar_operator_kararina_esit():
    k = kadro.kadro_yukle()
    dalga = lambda d: {b.ad for b in k if b.dalga == d}
    assert dalga("canli") == {"sef", "bekci", "karne"}
    assert dalga("1") == {"kod", "karar", "ayna", "olay"}
    assert dalga("2") == {"kacan", "veri", "butce", "yol", "nobet", "denetci"}
    assert dalga("kilitli") == {"hipotez"}
    assert len(dalga("3")) == 7


def test_hepsi_hafizasi_yalniz_sef():
    assert {b.ad for b in kadro.kadro_yukle() if b.hafiza == "hepsi"} == {"sef"}


def test_imza_rapor_basligi_onekidir():
    for b in kadro.aktif_botlar():
        if b.zamanli_is is None:
            continue
        betik = {"sef": "ops/sef_brifingi.py", "bekci": "ops/bekci_brifingi.py",
                 "karne": "ops/karne_brifingi.py"}[b.ad]
        m = re.search(r'^BASLIK = "(.+)"$', (ROOT / betik).read_text(encoding="utf-8"), re.M)
        assert m and m.group(1).startswith(b.imza), (b.ad, b.imza)


def test_zamanli_is_birimi_depoda_var():
    for b in kadro.aktif_botlar():
        if b.zamanli_is:
            assert (ROOT / "deploy/oracle-a1" / f"{b.zamanli_is}.service").is_file(), b.zamanli_is


def test_araclar_bilinen_kumede():
    from meridian import mcp_server, sohbet
    bilinen = set(sohbet.ARACLAR) | {t["name"] for t in mcp_server.TOOLS} | set(kadro.PLANLI_ARACLAR)
    for b in kadro.kadro_yukle():
        assert set(b.araclar) <= bilinen, (b.ad, set(b.araclar) - bilinen)


def test_gunluk_tavan_olculmeden_null_ve_nedenli():
    for b in kadro.kadro_yukle():
        assert b.gunluk_tavan is None and b.gunluk_tavan_neden, b.ad


def test_imzadan_bot_rapor_ilk_satiri():
    assert kadro.imzadan_bot("🔭 Meridian bekçi\n3 kalem").ad == "bekci"
    assert kadro.imzadan_bot("🧭 Meridian brifing — HAM (sıralama katmanı devrede değil)\n…").ad == "sef"
    assert kadro.imzadan_bot("📊 Meridian karne\nGEÇTİ").ad == "karne"
    assert kadro.imzadan_bot("başka bir mesaj\n🔭 Meridian bekçi") is None
    assert kadro.imzadan_bot("") is None


def test_bot_bul_harf_duyarsiz():
    assert kadro.bot_bul("BEKCI").ad == "bekci"
    assert kadro.bot_bul("yok") is None


@pytest.mark.parametrize("bozuk,alan", [
    ({"durum": "belki"}, "durum"),
    ({"dalga": "9"}, "dalga"),
    ({"hafiza": "ortak"}, "hafiza"),
    ({"araclar": []}, "araclar"),
])
def test_dogrulama_hatali_alani_adlandirir(tmp_path, bozuk, alan):
    with pytest.raises(ValueError, match=alan):
        kadro.kadro_yukle(_yaz(tmp_path, [_gecerli(**bozuk)]))


def test_dogrulama_tekrarlanan_ad(tmp_path):
    with pytest.raises(ValueError, match="tekrar"):
        kadro.kadro_yukle(_yaz(tmp_path, [_gecerli(), _gecerli()]))


def test_dogrulama_null_tavan_nedensiz(tmp_path):
    with pytest.raises(ValueError, match="gunluk_tavan_neden"):
        kadro.kadro_yukle(_yaz(tmp_path, [_gecerli(gunluk_tavan_neden=None)]))
```

- [ ] **Step 2: Kırmızıyı gör**

Run: `.venv/bin/python -m pytest tests/test_kadro_v591.py -p no:cacheprovider`
Expected: toplama hatası `ModuleNotFoundError: meridian.kadro` (ya da `ImportError`).

- [ ] **Step 3: `deploy/hermes/kadro.yaml` yaz** — 21 satır, spec §2.2 tablosundaki rol metinleriyle. Aktif üçlü tam alanlı:

```yaml
# deploy/hermes/kadro.yaml — konuşan bot filosu KADRO LİSTESİ (TEK KAYNAK, spec 2026-09-29 §3.1).
# Okuyucu: meridian/kadro.py (Telegram yönlendirmesi; ileride pano seçicisi, bot sunucusu, filo MCP).
# Çivi: tests/test_kadro_v591.py. `aktif` satırlar deploy/hermes/profiles/* ile birebir.
botlar:
  - ad: sef
    rol: "Konuştuğun tek yüzey; diğer botların çıktısını tek brifinge indirir"
    dalga: canli
    durum: aktif
    araclar: [pano_ozeti, alarm_oku, gunluk_ara, kart_oku, hafiza_ara, oneri_yaz, is_iste, bot_hafizasi_ara]
    zamanli_is: meridian-brifing
    imza: "🧭 Meridian brifing"
    hafiza: hepsi
    gunluk_tavan: null
    gunluk_tavan_neden: "Parça 0 (g) günlük çağrı ölçümü bekliyor — uydurma yasağı"
  - ad: bekci
    rol: "Sessizce bozulanı bulur ve kışkırtır"
    dalga: canli
    durum: aktif
    araclar: [pano_ozeti, alarm_oku, olay_sorgu, gunluk_ara, is_iste]
    zamanli_is: meridian-bekci
    imza: "🔭 Meridian bekçi"
    hafiza: kendi
    gunluk_tavan: null
    gunluk_tavan_neden: "Parça 0 (g) günlük çağrı ölçümü bekliyor — uydurma yasağı"
  - ad: karne
    rol: "Deney goal.yaml'a karşı kazanıyor mu sorusunu cevaplar"
    dalga: canli
    durum: aktif
    araclar: [pano_ozeti, pozisyon_oku, plan_oku, kart_oku, meridian_selfreview, is_iste]
    zamanli_is: meridian-karne
    imza: "📊 Meridian karne"
    hafiza: kendi
    gunluk_tavan: null
    gunluk_tavan_neden: "Parça 0 (g) günlük çağrı ölçümü bekliyor — uydurma yasağı"
```
Kalan 18 satır aynı şemayla, `durum: sirada` (dalga 1/2/3) ya da `durum: kilitli` (hipotez, `dalga: kilitli`), `araclar: []`, `zamanli_is: null`, `imza: null`, `hafiza: kendi`, aynı `gunluk_tavan*` çifti; `rol` metinleri spec §2.2'den (dalga 3 rolleri: civici "Yanlış gideni bir daha imkânsız kılan kuralı önerir" · devir "Oturumlar ve Mac↔A1 arası süreklilik" · derleyici "Tekrarlanan prosedürü skill'e ya da koda çevirmeyi önerir" · olcum "Tipli ölçüm API'si ve eksik enstrümantasyon avcısı" · tasarimci "Parametre değil yapısal öneri kanalı" · yabanci "Panoya ilk kez gören biri gibi bakar" · piyasa "Rejim dedektörünün göremediği makro bağlam"; hipotez "Öğrenme motorunu besler (ret örüntüleri + arama uzayı)").

- [ ] **Step 4: `meridian/kadro.py` yaz**

```python
"""kadro.py — konuşan bot filosunun KADRO LİSTESİNİ (`deploy/hermes/kadro.yaml`) yükler, doğrular, sorgular.

TEK KAYNAK (spec docs/superpowers/specs/2026-09-29-konusan-bot-filosu-design.md §3.1): bot adı, durumu,
araç alt kümesi, rapor imzası ve hafıza kipi YALNIZ o dosyada yaşar; Telegram yönlendirmesi, pano seçicisi,
bot sunucusu ve filo MCP'si buradan türetir. Doğrulama gevşek değildir: bilinmeyen durum/dalga/hafıza,
tekrarlanan ad, aracı olmayan aktif bot, nedensiz boş tavan → `ValueError` (sessiz varsayılan YOK).
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from . import config

KADRO_YOLU = config.ROOT / "deploy/hermes/kadro.yaml"
DURUMLAR = ("aktif", "sirada", "kilitli")
DALGALAR = ("canli", "1", "2", "3", "kilitli")
HAFIZA_KIPLERI = ("kendi", "hepsi")
#: Parça 1'de araç sunucusuna eklenecek araçlar — kadro bugünden adlandırır, çivi bilinen kümeye katar.
PLANLI_ARACLAR = ("is_iste", "bot_hafizasi_ara")


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
    ad = str(ham.get("ad") or "").strip().lower()
    if not ad:
        raise ValueError("kadro: 'ad' alanı boş bir satır var")
    for alan, izinli in (("durum", DURUMLAR), ("dalga", DALGALAR), ("hafiza", HAFIZA_KIPLERI)):
        if str(ham.get(alan)) not in izinli:
            raise ValueError(f"kadro: @{ad} '{alan}'={ham.get(alan)!r} izinli değil {izinli}")
    araclar = tuple(ham.get("araclar") or ())
    if ham["durum"] == "aktif" and not araclar:
        raise ValueError(f"kadro: aktif @{ad} için 'araclar' boş olamaz")
    tavan = ham.get("gunluk_tavan")
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


def bot_bul(ad: str, kadro: tuple[Bot, ...] | None = None) -> Bot | None:
    hedef = (ad or "").strip().lower()
    return next((b for b in (kadro if kadro is not None else kadro_yukle()) if b.ad == hedef), None)


def aktif_botlar(kadro: tuple[Bot, ...] | None = None) -> tuple[Bot, ...]:
    return tuple(b for b in (kadro if kadro is not None else kadro_yukle()) if b.durum == "aktif")


def imzadan_bot(metin: str, kadro: tuple[Bot, ...] | None = None) -> Bot | None:
    ilk = (metin or "").split("\n", 1)[0].strip()
    if not ilk:
        return None
    return next((b for b in aktif_botlar(kadro) if b.imza and ilk.startswith(b.imza)), None)
```

- [ ] **Step 5: Yeşili gör**

Run: `.venv/bin/python -m pytest tests/test_kadro_v591.py -p no:cacheprovider`
Expected: tümü PASS (`N passed`, `PYTEST_EXIT=0`).

- [ ] **Step 6: Mutasyonla ısırt** (yedek KOPYADAN geri al, `sha256` eşit; `git checkout --` YOK): (i) kadro.yaml'dan `sef`i sil → 21-bot ve profil eşitliği çivileri kırmızı; (ii) `bekci` imzasını `"🔭 Meridian bekci"` yap → imza↔BASLIK kırmızı; (iii) `_bot`taki `hafiza` doğrulamasını kaldır → `test_dogrulama_hatali_alani_adlandirir[hafiza]` kırmızı; (iv) `imzadan_bot`ta `split("\n",1)[0]` yerine tüm metni ara → "başka bir mesaj" testi kırmızı. Her mutasyondan sonra geri al + yeşili yeniden gör.

- [ ] **Step 7: Commit**

```bash
git add deploy/hermes/kadro.yaml meridian/kadro.py tests/test_kadro_v591.py
git commit -m "Konusan filo: kadro listesi (21 bot, tek kaynak) + meridian/kadro.py dogrulama/sorgu; v591"
```

---

### Task 2: Telegram dinleyicisi çekirdeği + `notify.yanitla`

**Files:**
- Create: `meridian/telegram_dinleyici.py`
- Modify: `meridian/notify.py` (`send`in Telegram dalı `_telegram_gonder`e çıkarılır; yeni `yanitla`)
- Test: `tests/test_telegram_dinleyici_v592.py`

**Interfaces:**
- Consumes: `kadro.bot_bul`, `kadro.aktif_botlar`, `kadro.imzadan_bot`, `Bot` (Görev 1)
- Produces:
  - `notify.yanitla(text: str, reply_to: int | None = None) -> bool` — yalnız Telegram, `scrub`lı, başarısızlık `notify_delivery_failed` olayı
  - `SOHBET_IMZA = "💬 @{ad}"` ; `VARSAYILAN_BOT = "sef"`
  - `@dataclass(frozen=True) class Yonlendirme: bot: str | None; metin: str; neden: str` — neden ∈ `onek · imza · sohbet_imza · varsayilan · yabanci · bos · pasif_bot · bilinmeyen_bot`
  - `def yonlendir(mesaj: dict, yetkili_sohbet: str, kadro=None) -> Yonlendirme`
  - `def oturum_kimligi(bot: str, mesaj: dict, bugun: str) -> str` — yanıtsa `tg-<bot>-r<reply_to_message_id>`, değilse `tg-<bot>-<bugun>`
  - `def isle(guncelleme: dict, *, yetkili_sohbet: str, bota_sor, gonder, kadro=None, bugun: str | None = None) -> str` — `bota_sor(bot, metin, kanal, oturum) -> str`, `gonder(metin, reply_to) -> bool`; döner: yönlendirme nedeni
  - `def guncellemeleri_al(jeton: str, ofset: int, bekleme_s: int = 50, _cagir=None) -> list[dict]`
  - `def dongu(*, bota_sor, tur_sayisi: int | None = None, _cagir=None, gonder=None) -> None` — ofset `store` üzerinden `telegram_ofset.json`

- [ ] **Step 1: Başarısız testleri yaz** — `tests/test_telegram_dinleyici_v592.py`:

```python
"""v592 — Telegram dinleyicisi çekirdeği (spec 2026-09-29 §3.5, K3): yetki, yönlendirme, yanıt, yoklama."""
import hashlib

import pytest

from meridian import kadro, notify, obs, telegram_dinleyici as td

YETKILI = "4242"


def _m(metin, sohbet=YETKILI, yanit=None, mid=7):
    m = {"message_id": mid, "chat": {"id": int(sohbet)}, "text": metin}
    if yanit is not None:
        m["reply_to_message"] = {"message_id": 99, "text": yanit}
    return m


@pytest.mark.parametrize("metin,bot,neden,govde", [
    ("@bekci şu an takılı ne var?", "bekci", "onek", "şu an takılı ne var?"),
    ("@Bekci: durum?", "bekci", "onek", "durum?"),
    ("@KARNE, bu hafta?", "karne", "onek", "bu hafta?"),
    ("merhaba", "sef", "varsayilan", "merhaba"),
])
def test_yonlendir_onek_ve_varsayilan(metin, bot, neden, govde):
    y = td.yonlendir(_m(metin), YETKILI)
    assert (y.bot, y.neden, y.metin) == (bot, neden, govde)


def test_yonlendir_rapor_imzasina_yanit():
    y = td.yonlendir(_m("bu kalem ne?", yanit="🔭 Meridian bekçi\n1. TAKILI x"), YETKILI)
    assert (y.bot, y.neden) == ("bekci", "imza")


def test_yonlendir_bot_cevabina_yanit_ayni_bota():
    y = td.yonlendir(_m("devam et", yanit="💬 @karne\nGEÇTİ"), YETKILI)
    assert (y.bot, y.neden) == ("karne", "sohbet_imza")


def test_yonlendir_onek_yanittan_once_gelir():
    y = td.yonlendir(_m("@karne bak", yanit="🔭 Meridian bekçi\n…"), YETKILI)
    assert y.bot == "karne"


def test_yonlendir_yabanci_sohbet():
    assert td.yonlendir(_m("@bekci selam", sohbet="5550123987"), YETKILI).neden == "yabanci"


def test_yonlendir_pasif_ve_bilinmeyen_bot():
    assert td.yonlendir(_m("@kod neden?"), YETKILI).neden == "pasif_bot"
    assert td.yonlendir(_m("@yokboyle selam"), YETKILI).neden == "bilinmeyen_bot"
    assert td.yonlendir(_m("   "), YETKILI).neden == "bos"


def test_oturum_kimligi():
    assert td.oturum_kimligi("bekci", _m("x", yanit="🔭 Meridian bekçi"), "20260929") == "tg-bekci-r99"
    assert td.oturum_kimligi("sef", _m("x"), "20260929") == "tg-sef-20260929"


def _isle(metin, sohbet=YETKILI, yanit=None, cevap="tamam", hata=None):
    cagrilar, gidenler = [], []

    def bota_sor(bot, m, kanal, oturum):
        cagrilar.append((bot, m, kanal, oturum))
        if hata:
            raise hata
        return cevap

    neden = td.isle({"update_id": 1, "message": _m(metin, sohbet, yanit)}, yetkili_sohbet=YETKILI,
                    bota_sor=bota_sor, gonder=lambda t, r: gidenler.append((t, r)) or True, bugun="20260929")
    return neden, cagrilar, gidenler


def test_isle_normal_cevap_imzali_ve_yanitli(sandbox_state):
    neden, cagrilar, gidenler = _isle("@bekci durum?")
    assert neden == "onek"
    assert cagrilar == [("bekci", "durum?", "telegram", "tg-bekci-20260929")]
    assert gidenler[0][0].startswith("💬 @bekci\n") and gidenler[0][1] == 7


def test_isle_yabanci_cevapsiz_ve_sayilir(sandbox_state):
    neden, cagrilar, gidenler = _isle("@bekci selam", sohbet="5550123987")
    assert (neden, cagrilar, gidenler) == ("yabanci", [], [])
    olay = [e for e in obs.recent(20) if e.get("event") == "bot_yabanci_mesaj"]
    assert olay and olay[-1].get("sohbet_sha") == hashlib.sha256(b"5550123987").hexdigest()[:12]
    assert "5550123987" not in str(olay[-1])


def test_isle_bota_sor_hatasi_sessiz_degil(sandbox_state):
    neden, _, gidenler = _isle("@karne?", hata=TimeoutError("zaman aşımı"))
    assert "cevap veremiyor" in gidenler[0][0] and "TimeoutError" in gidenler[0][0]
    assert any(e.get("event") == "bot_sohbet_hatasi" for e in obs.recent(20))


def test_isle_pasif_bot_bilgilendirir(sandbox_state):
    neden, cagrilar, gidenler = _isle("@kod neden?")
    assert neden == "pasif_bot" and cagrilar == [] and "henüz aktif değil" in gidenler[0][0]


def test_guncellemeleri_al_basari_ve_hata(sandbox_state):
    def iyi(url, govde, zaman_asimi):
        assert url.endswith("/getUpdates") and govde["offset"] == 5 and govde["timeout"] == 50
        return {"ok": True, "result": [{"update_id": 5}]}

    def kotu(url, govde, zaman_asimi):
        raise OSError("ağ yok")

    assert td.guncellemeleri_al("JETONDEGERI123", 5, _cagir=iyi) == [{"update_id": 5}]
    assert td.guncellemeleri_al("JETONDEGERI123", 5, _cagir=kotu) == []
    olay = [e for e in obs.recent(20) if e.get("event") == "telegram_yoklama_hatasi"]
    assert olay and "JETONDEGERI123" not in str(olay[-1])


def test_dongu_ofseti_ilerletir_ve_kalici(sandbox_state, monkeypatch):
    monkeypatch.setattr(td.secrets, "get", lambda ad: {"TELEGRAM_BOT_TOKEN": "J" * 20,
                                                        "TELEGRAM_CHAT_ID": YETKILI}.get(ad))
    turlar = iter([[{"update_id": 10, "message": _m("merhaba")}], []])
    td.dongu(bota_sor=lambda *a: "ok", tur_sayisi=2, _cagir=lambda u, g, z: {"ok": True, "result": next(turlar)},
             gonder=lambda t, r: True)
    from meridian import store
    assert store.read_json("telegram_ofset.json", {}).get("ofset") == 11


def test_yanitla_reply_ve_scrub(monkeypatch):
    giden = {}
    monkeypatch.setattr(notify.secrets, "get", lambda ad: {"TELEGRAM_BOT_TOKEN": "T" * 20,
                                                            "TELEGRAM_CHAT_ID": YETKILI}.get(ad))
    monkeypatch.setattr(notify, "_post", lambda url, payload, timeout=8.0: giden.update(payload) or True)
    assert notify.yanitla("sk-or-v1-" + "a" * 40 + " selam", reply_to=7) is True
    assert giden["reply_to_message_id"] == 7 and "a" * 40 not in giden["text"]


def test_send_davranisi_degismedi(monkeypatch):
    giden = {}
    monkeypatch.setattr(notify.secrets, "get", lambda ad: {"TELEGRAM_BOT_TOKEN": "T" * 20,
                                                            "TELEGRAM_CHAT_ID": YETKILI}.get(ad))
    monkeypatch.setattr(notify, "_post", lambda url, payload, timeout=8.0: giden.update(payload) or True)
    assert notify.send("x") is True and "reply_to_message_id" not in giden
```

- [ ] **Step 2: Kırmızıyı gör**

Run: `.venv/bin/python -m pytest tests/test_telegram_dinleyici_v592.py -p no:cacheprovider`
Expected: `ModuleNotFoundError: meridian.telegram_dinleyici`.
Not: `sk-or-v1-…` desenini `notify.scrub`un gerçekten maskelediğini `meridian/notify.py` `_SIR_DESENLERI`nden doğrula; maskelemiyorsa testte `_SIR_DESENLERI`in kapsadığı bir desen kullan ve bunu rapora yaz (testi scrub'a uydur, scrub'ı genişletme — kapsam dışı).

- [ ] **Step 3: `notify.py`de tek teslimat yolu** — `send`in Telegram dalını `_telegram_gonder(text: str, reply_to: int | None = None) -> bool | None` yardımcısına çıkar (`None` = kanal yapılandırılmamış); `payload`a `reply_to` varsa `"reply_to_message_id": reply_to` eklenir. `send` davranışı birebir korunur (webhook dalı ve `notify_delivery_failed` kaydı dahil). Yeni:

```python
def yanitla(text: str, reply_to: int | None = None) -> bool:
    """Operatörün Telegram mesajına YANIT olarak gönderir (konuşan filo, spec 2026-09-29 §3.5).
    `send` ile AYNI teslimat yolu ve AYNI `scrub`; webhook'a gitmez (yanıt yalnız Telegram sohbetine anlamlı).
    Başarısızlık `send` gibi kayda geçer."""
    text = scrub(text)
    r = _telegram_gonder(text, reply_to)
    if r is False:
        try:
            from . import obs
            obs.warn("notify_delivery_failed", channels="telegram", delivered=False, yanit=True)
        except Exception:  # sessiz-yutma: kayıt kanalının kendisi düştü — ikinci kanal yok, çağıran düşürülmez
            pass
    return bool(r)
```

- [ ] **Step 4: `meridian/telegram_dinleyici.py` yaz** — modül başlığı: ne yapar, değişmezler (yalnız yetkili sohbet; yabancıya cevap yok + sha'lı sayım; cevap tek teslimat yolu; jeton log'a düşmez; Yasa 6 okuyucu beyanı: `telegram_ofset.json`in okuyucusu `dongu`nun kendisi). Gövde:

```python
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
    r = (mesaj.get("reply_to_message") or {}).get("message_id")
    return f"tg-{bot}-r{r}" if r is not None else f"tg-{bot}-{bugun}"


def _sha(x) -> str:
    return hashlib.sha256(str(x).encode()).hexdigest()[:12]


def isle(guncelleme: dict, *, yetkili_sohbet: str, bota_sor, gonder, kadro=None,
         bugun: str | None = None) -> str:
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


def guncellemeleri_al(jeton: str, ofset: int, bekleme_s: int = 50, _cagir=None) -> list[dict]:
    cagir = _cagir or _cagir_varsayilan
    try:
        d = cagir(f"https://api.telegram.org/bot{jeton}/getUpdates",
                  {"offset": ofset, "timeout": bekleme_s, "allowed_updates": ["message"]}, bekleme_s + 10)
    except Exception as e:  # sinyalli: jetonsuz olay, boş tur; döngü bir sonraki turda yeniden dener
        obs.warn("telegram_yoklama_hatasi", sinif=type(e).__name__)
        return []
    return list(d.get("result") or []) if isinstance(d, dict) and d.get("ok") else []


def dongu(*, bota_sor, tur_sayisi: int | None = None, _cagir=None, gonder=None) -> None:
    jeton, yetkili = secrets.get("TELEGRAM_BOT_TOKEN"), secrets.get("TELEGRAM_CHAT_ID")
    if not (jeton and yetkili):
        raise SystemExit("telegram_dinleyici: TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID yapılandırılmamış")
    gonder = gonder or (lambda t, r: notify.yanitla(t, reply_to=r))
    ofset = int((store.read_json(OFSET_DOSYASI, {}) or {}).get("ofset") or 0)
    tur = 0
    while tur_sayisi is None or tur < tur_sayisi:
        tur += 1
        for g in guncellemeleri_al(jeton, ofset, _cagir=_cagir):
            isle(g, yetkili_sohbet=yetkili, bota_sor=bota_sor, gonder=gonder)
            ofset = int(g["update_id"]) + 1
            store.write_json(OFSET_DOSYASI, {"ofset": ofset, "ts": time.time()})
```
(`dongu` bir ürün hizmet döngüsüdür — systemd birimi Parça 2 dağıtımında gelir; bu planda KOŞTURULMAZ. `main()` YOK.)

- [ ] **Step 5: Yeşili gör**

Run: `.venv/bin/python -m pytest tests/test_telegram_dinleyici_v592.py tests/test_kadro_v591.py -p no:cacheprovider`
Expected: tümü PASS.

- [ ] **Step 6: Mutasyonla ısırt** (yedekten geri al, sha256 eşit): (i) `yonlendir`deki sohbet kimliği kontrolünü kaldır → yabancı testleri kırmızı; (ii) `isle`de `except` gövdesinden `gonder` çağrısını sil → hata testi kırmızı; (iii) `_sha` yerine ham kimliği yaz → "5550123987 not in" kırmızı; (iv) `_telegram_gonder`de `reply_to_message_id` eklemesini sil → `test_yanitla_reply_ve_scrub` kırmızı; (v) önek regex'inden `[:,]?` kaldır → `@Bekci:` testi kırmızı.

- [ ] **Step 7: Kapsam + tarama çivileri (SERİ, ön planda)**

Run: `.venv/bin/python -m pytest tests/test_telegram_dinleyici_v592.py tests/test_kadro_v591.py $(grep -l "notify\.send\|notify\._post\|notify\.scrub\|notify\.configured" tests/test_*.py) tests/test_capa_metin_dedektoru_v391.py tests/test_capa_pydisi_hedef_v571.py -p no:cacheprovider`
Ayrıca `codelaw` (Yasa 4/6) çivisi: `grep -l "codelaw" tests/test_*.py` ile bulunan dosyalar.
Expected: üçlü hüküm yeşil (FAILED|ERROR grep boş · `N passed` · `PYTEST_EXIT=0`). (2026-09-29 ölçümü: bu grep 21 dosya seçer — kesme YOK.)

- [ ] **Step 8: Commit**

```bash
git add meridian/telegram_dinleyici.py meridian/notify.py tests/test_telegram_dinleyici_v592.py
git commit -m "Konusan filo: Telegram dinleyici cekirdegi (yetki, @ad/imza yonlendirme, yanit, yoklama) + notify.yanitla tek teslimat yolu; v592"
```
