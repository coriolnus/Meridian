# Konuşan bot filosu — Parça 1a: kanal çekirdeği (`bota_sor`) + "şimdi çalıştır" (`is_iste`) Uygulama Planı

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Spec §3.5'in ortak giriş noktası `bota_sor` (kadro/kanal doğrulama, bot başına günlük kota, deterministik `hatırla:`/`unut:`, konuşma defteri, takılabilir taşıyıcı) ve §3.6 `is_iste` (kadrodan türeyen iş listesi, 15 dk tavanı, systemd `.path` birimleri) — DAĞITIMSIZ, taşıyıcı mimarisinden bağımsız.

**Architecture:** `meridian/bot_kanal.py` saf çekirdek; ağ/hafıza bağımlılıkları `Tasiyici` ve `Hafiza` protokolleriyle enjekte edilir. Varsayılan taşıyıcı `HermesTasiyici` (Hermes api_server, `/p/<bot>/v1/chat/completions`, `X-Hermes-Session-Id`, anahtar `secrets.credential_oku("API_SERVER_KEY")`); Parça 0 (a)/(b) KALIRSA yedek taşıyıcı (pano sohbet motoru) aynı protokole takılır, çekirdek değişmez. Gerçek Hindsight hafıza yazıcısı Parça 0 (e)/(f) ölçümünü bekler — bu planda `Hafiza` verilmezse `hatırla:` açıkça "henüz bağlı değil" der. `meridian/is_istek.py` istek dosyasını yazar; `deploy/oracle-a1/meridian-istek-<bot>.path` (`PathChanged=`) aynı `.service`i başlatır (dosya silinmez → yeniden tetikleme döngüsü yok; oneshot çalışırken ikinci başlatma aynı işe katılır).

**Tech Stack:** Python 3 stdlib (`urllib`, `dataclasses`, `hashlib`, `typing.Protocol`), mevcut `meridian.kadro`, `meridian.store`, `meridian.obs`, `meridian.notify.scrub`, `meridian.secrets`; systemd `.path`; Ansible A0 rol listeleri.

**Spec:** `docs/superpowers/specs/2026-09-29-konusan-bot-filosu-design.md` (§0 K2-B, §3.4 hatırla/unut, §3.5 bot_kanal, §3.6, §3.7, §4)

## Global Constraints

- Kanallar DONUK: `telegram` · `pano` · `claude`. Yalnız `kadro.aktif_botlar()` botlarına soru gider; `sirada`/`kilitli` → `ValueError`.
- `bota_sor(bot, mesaj, kanal, oturum) -> str` imzası Telegram dinleyicisinin beklediğidir (değişmez); ek anahtar kelimeler yalnız enjeksiyon için (`tasiyici=`, `hafiza=`, `simdi=`, `kadro=`).
- Kota: `kadro.gunluk_tavan` `None` ise TAVAN YOK ama sayılır (uydurma yasağı — sayı Parça 0 (g)'den); doluysa bot "bugünlük kotam doldu (n/n)" der, taşıyıcı ÇAĞRILMAZ, defter satırı yazılır.
- `hatırla:` / `unut:` önekleri (büyük/küçük harf ve `hatirla`/`unut` Türkçe-katlamalı) MODELE GİTMEZ; deterministik işlenir. Kalıcı silme YOK.
- Defter `state/bot_sohbet.jsonl` — her satır `notify.scrub`'dan geçmiş `mesaj`/`cevap` (cevap ≤4000 karakter, kesilirse `kesildi: true`); Yasa 6 okuyucusu beyanlı (codelaw `DECLARED_SINKS` emsali: `telegram_ofset.json`).
- Sır: `API_SERVER_KEY` yalnız `Authorization` başlığında; argv/log/olay/istisna metnine düşmez; istisnalarda yalnız sınıf adı + HTTP kodu.
- `is_iste` işi yalnız kadrodaki `zamanli_is` taşıyan botlar için (bugün sef→meridian-brifing, bekci→meridian-bekci, karne→meridian-karne); takma ad `brifing`→`sef`. Aynı bot için 15 dk (`IS_TAVAN_S = 900`) içinde ikinci istek REDDEDİLİR (sonraki uygun zamanla).
- Yeni `.path` birimleri A0 rolünde YALNIZ KOPYALANIR (`birim_kaynaklari`), `etkin_birimler`e EKLENMEZ (Vault/Grafana emsali: "rol kopyalar → elle test-ateşle → AYRI değişiklikle etkin").
- Test numaraları: v593 (bot_kanal), v594 (is_istek). Test adlarında `FAILED`/`ERROR` yok; yorumlarda `dosya.py:NNN` çapası yok; her `except` işaretli ya da sinyalli (Yasa 4).

## Review Focus

1. Taşıyıcı asılırsa (api_server cevap vermez) Telegram döngüsü de asılır → `HermesTasiyici` zaman aşımı ZORUNLU ve testli; aşımda istisna (dinleyici `bot_sohbet_hatasi` yolu yakalar), defter satırı `tur: hata`.
2. Aynı saniyede iki `is_iste` (iki kanal) → ikisi de "kabul" alırsa iş iki kez koşar → istek defteri tek-yazar kilidi/atomik kontrol (Görev 2 testi).
3. `hatırla:` gövdesi boşsa ya da yalnız boşluksa → modele gitmez, "neyi hatırlayayım?" döner.
4. Defter yazımı düşerse (disk dolu, salt-okur) cevap yine operatöre dönmeli → yazım hatası sinyalli olay, cevap kaybolmaz.
5. Kota sayımı UTC günü mü yerel gün mü → UTC (`simdi` enjekte), gün dönümü testi.

---

### Task 1: `meridian/bot_kanal.py` — ortak giriş noktası

**Files:**
- Create: `meridian/bot_kanal.py`
- Modify: `meridian/codelaw.py` (`DECLARED_SINKS["bot_sohbet.jsonl"]` — gerekçe: "okuyucu @ayna/@butce/pano + EDG ölçüm kartı; Parça 1 dağıtımında okuyucu kodu gelir")
- Modify: `tests/test_codelaw_kor_nokta_v214.py` (`SINK_TABANI` satırı — `telegram_ofset.json` emsali)
- Test: `tests/test_bot_kanal_v593.py`

**Interfaces:**
- Consumes: `kadro.bot_bul`, `kadro.aktif_botlar`, `kadro.ad_katla`, `Bot.gunluk_tavan`; `store.append_jsonl`, `store.read_jsonl`; `notify.scrub`; `obs.warn`; `secrets.credential_oku`
- Produces:
  - `KANALLAR = ("telegram", "pano", "claude")`, `DEFTER = "bot_sohbet.jsonl"`, `CEVAP_TAVANI = 4000`
  - `@dataclass(frozen=True) class TasiyiciSonuc: metin: str; arac_cagrilari: int | None = None; model_cagrilari: int | None = None`
  - `class Tasiyici(Protocol): def sor(self, bot: str, mesaj: str, oturum: str) -> TasiyiciSonuc: ...`
  - `class Hafiza(Protocol): def yaz(self, bot: str, metin: str, etiketler: tuple[str, ...]) -> bool: ...`
  - `class HermesTasiyici: def __init__(self, taban_url: str = "http://127.0.0.1:8642", zaman_asimi_s: float = 300.0, _cagir=None, _anahtar=None)`; `sor(...)` → `POST {taban}/p/{bot}/v1/chat/completions`, gövde `{"model": "hermes-agent", "messages": [{"role": "user", "content": mesaj}]}`, başlıklar `Authorization: Bearer <anahtar>`, `X-Hermes-Session-Id: <oturum>`; anahtar yoksa `RuntimeError("API_SERVER_KEY credential yok")` (değer içermez)
  - `def bota_sor(bot: str, mesaj: str, kanal: str, oturum: str, *, tasiyici: Tasiyici | None = None, hafiza: Hafiza | None = None, simdi=None, kadro=None) -> str`
  - `def gunluk_sayim(bot: str, gun: str) -> int` (UTC `YYYY-MM-DD`, defterden, `tur == "sohbet"` satırları)

- [ ] **Step 1: Başarısız testleri yaz** — `tests/test_bot_kanal_v593.py` (tümü `sandbox_state` ile; taşıyıcı ve hafıza SAHTE sınıflar):

```python
"""v593 — konuşan filo kanal çekirdeği bota_sor (spec 2026-09-29 §3.4-§3.7): doğrulama, kota, hatırla/unut, defter, taşıyıcı."""
import datetime as dt
import json

import pytest

from meridian import bot_kanal as bk, kadro, obs, store

SIMDI = dt.datetime(2026, 9, 29, 12, 0, tzinfo=dt.timezone.utc)


class SahteTasiyici:
    def __init__(self, metin="cevap", hata=None):
        self.cagrilar, self.metin, self.hata = [], metin, hata

    def sor(self, bot, mesaj, oturum):
        self.cagrilar.append((bot, mesaj, oturum))
        if self.hata:
            raise self.hata
        return bk.TasiyiciSonuc(self.metin, arac_cagrilari=2, model_cagrilari=3)


class SahteHafiza:
    def __init__(self, sonuc=True):
        self.yazilanlar, self.sonuc = [], sonuc

    def yaz(self, bot, metin, etiketler):
        self.yazilanlar.append((bot, metin, etiketler))
        return self.sonuc


def _defter():
    return store.read_jsonl(bk.DEFTER)


def test_normal_soru_tasiyiciya_gider_ve_deftere_yazilir(sandbox_state):
    t = SahteTasiyici("rejim risk-on")
    assert bk.bota_sor("bekci", "durum?", "telegram", "tg-bekci-1", tasiyici=t, simdi=SIMDI) == "rejim risk-on"
    assert t.cagrilar == [("bekci", "durum?", "tg-bekci-1")]
    s = _defter()[-1]
    assert (s["bot"], s["kanal"], s["oturum"], s["tur"]) == ("bekci", "telegram", "tg-bekci-1", "sohbet")
    assert s["arac_cagrilari"] == 2 and s["model_cagrilari"] == 3 and s["kota_bugun"] == 1


@pytest.mark.parametrize("bot,kanal", [("kod", "telegram"), ("yok", "pano"), ("bekci", "faks")])
def test_gecersiz_bot_ya_da_kanal_reddedilir(sandbox_state, bot, kanal):
    with pytest.raises(ValueError):
        bk.bota_sor(bot, "x", kanal, "o", tasiyici=SahteTasiyici(), simdi=SIMDI)


def test_kota_doluysa_tasiyici_cagrilmaz(sandbox_state):
    k = tuple(kadro.Bot(**{**b.__dict__, "gunluk_tavan": 1, "gunluk_tavan_neden": None})
              if b.ad == "karne" else b for b in kadro.kadro_yukle())
    t = SahteTasiyici()
    bk.bota_sor("karne", "1", "pano", "o", tasiyici=t, simdi=SIMDI, kadro=k)
    cevap = bk.bota_sor("karne", "2", "pano", "o", tasiyici=t, simdi=SIMDI, kadro=k)
    assert "kotam doldu" in cevap and "(1/1)" in cevap and len(t.cagrilar) == 1
    assert _defter()[-1]["tur"] == "kota_doldu"


def test_kota_gun_donumunde_sifirlanir(sandbox_state):
    k = tuple(kadro.Bot(**{**b.__dict__, "gunluk_tavan": 1, "gunluk_tavan_neden": None})
              if b.ad == "karne" else b for b in kadro.kadro_yukle())
    t = SahteTasiyici()
    bk.bota_sor("karne", "1", "pano", "o", tasiyici=t, simdi=SIMDI, kadro=k)
    ertesi = SIMDI + dt.timedelta(days=1)
    assert bk.bota_sor("karne", "2", "pano", "o", tasiyici=t, simdi=ertesi, kadro=k) == "cevap"


def test_tavan_none_sayilir_ama_sinirlamaz(sandbox_state):
    t = SahteTasiyici()
    for i in range(5):
        bk.bota_sor("sef", str(i), "pano", "o", tasiyici=t, simdi=SIMDI)
    assert len(t.cagrilar) == 5 and bk.gunluk_sayim("sef", "2026-09-29") == 5


@pytest.mark.parametrize("onek", ["hatırla:", "HATIRLA:", "hatirla :", "Hatırla:"])
def test_hatirla_modele_gitmez_hafizaya_yazilir(sandbox_state, onek):
    t, h = SahteTasiyici(), SahteHafiza()
    cevap = bk.bota_sor("sef", f"{onek} cuma toplantısı iptal", "telegram", "o", tasiyici=t, hafiza=h, simdi=SIMDI)
    assert t.cagrilar == [] and h.yazilanlar[0][:2] == ("sef", "cuma toplantısı iptal")
    assert "sabit_not" in h.yazilanlar[0][2] and "kanal:telegram" in h.yazilanlar[0][2]
    assert "Not aldım" in cevap and _defter()[-1]["tur"] == "hatirla"


def test_hatirla_bos_govde_sorar(sandbox_state):
    h = SahteHafiza()
    assert "neyi" in bk.bota_sor("sef", "hatırla:   ", "pano", "o", tasiyici=SahteTasiyici(), hafiza=h, simdi=SIMDI)
    assert h.yazilanlar == []


def test_hatirla_hafiza_bagli_degilse_acik_soyler(sandbox_state):
    cevap = bk.bota_sor("sef", "hatırla: x", "pano", "o", tasiyici=SahteTasiyici(), simdi=SIMDI)
    assert "henüz bağlı değil" in cevap
    assert any(e.get("event") == "bot_hafiza_bagli_degil" for e in obs.recent(20))


def test_unut_henuz_hazir_degil_ve_sinyalli(sandbox_state):
    t = SahteTasiyici()
    cevap = bk.bota_sor("bekci", "unut: eski not", "telegram", "o", tasiyici=t, simdi=SIMDI)
    assert t.cagrilar == [] and "henüz hazır değil" in cevap
    assert _defter()[-1]["tur"] == "unut"


def test_tasiyici_hatasi_defterde_ve_yukari_firlar(sandbox_state):
    with pytest.raises(TimeoutError):
        bk.bota_sor("bekci", "x", "telegram", "o", tasiyici=SahteTasiyici(hata=TimeoutError("zaman")), simdi=SIMDI)
    s = _defter()[-1]
    assert s["tur"] == "hata" and s["hata"] == "TimeoutError"


def test_defter_scrub_ve_cevap_tavani(sandbox_state):
    anahtar = "sk-or-v1-" + "a" * 64
    bk.bota_sor("sef", f"anahtarım {anahtar}", "pano", "o", tasiyici=SahteTasiyici("y" * 5000), simdi=SIMDI)
    s = _defter()[-1]
    assert anahtar not in json.dumps(s) and len(s["cevap"]) == bk.CEVAP_TAVANI and s["kesildi"] is True


def test_defter_yazim_hatasi_cevabi_dusurmez(sandbox_state, monkeypatch):
    def patla(*a, **k):
        raise OSError("disk dolu")
    monkeypatch.setattr(bk.store, "append_jsonl", patla)
    assert bk.bota_sor("sef", "x", "pano", "o", tasiyici=SahteTasiyici("tamam"), simdi=SIMDI) == "tamam"
    assert any(e.get("event") == "bot_defter_yazim_hatasi" for e in obs.recent(20))


def test_hermes_tasiyici_istek_bicimi_ve_jetonsuz_hata():
    gorulen = {}

    def cagir(url, govde, basliklar, zaman_asimi):
        gorulen.update(url=url, govde=govde, basliklar=basliklar, zaman_asimi=zaman_asimi)
        return {"choices": [{"message": {"content": "tamam"}}]}

    t = bk.HermesTasiyici(_cagir=cagir, _anahtar=lambda: "K" * 32, zaman_asimi_s=7)
    assert t.sor("karne", "soru", "tg-karne-1").metin == "tamam"
    assert gorulen["url"] == "http://127.0.0.1:8642/p/karne/v1/chat/completions"
    assert gorulen["basliklar"]["X-Hermes-Session-Id"] == "tg-karne-1" and gorulen["zaman_asimi"] == 7
    assert gorulen["govde"]["messages"] == [{"role": "user", "content": "soru"}]
    with pytest.raises(RuntimeError) as e:
        bk.HermesTasiyici(_cagir=cagir, _anahtar=lambda: None).sor("karne", "x", "o")
    assert "K" * 8 not in str(e.value)
```

- [ ] **Step 2: Kırmızıyı gör** — Run: `.venv/bin/python -m pytest tests/test_bot_kanal_v593.py -p no:cacheprovider` · Expected: `ModuleNotFoundError: meridian.bot_kanal`.

- [ ] **Step 3: Uygula** — `meridian/bot_kanal.py`: modül başlığı (ne yapar, değişmezler, Yasa 6 okuyucu beyanı, spec atfı). Davranış sırası `bota_sor` içinde: (1) kanal ∈ `KANALLAR` değilse `ValueError`; (2) `kadro.bot_bul(bot, k)` yoksa ya da `durum != "aktif"` ise `ValueError`; (3) `mesaj.strip()`'in katlanmış öneki (`kadro.ad_katla` ile `hatirla` / `unut`, ardından isteğe bağlı boşluk ve `:`) → deterministik dal: `hatirla` boş gövde → "Neyi hatırlayayım? `hatırla: <not>` biçiminde yaz."; `hafiza is None` → `obs.warn("bot_hafiza_bagli_degil", bot=...)` + "Hafızam henüz bağlı değil (Parça 0 ölçümü bekleniyor); not ALINMADI."; aksi hâlde `hafiza.yaz(bot, govde, ("sabit_not", f"bot:{bot}", f"kanal:{kanal}"))` → True ise "Not aldım: …", False ise "Not YAZILAMADI (hafıza hatası), kayda geçti." + olay; `unut` → "`unut` henüz hazır değil — hafızadan geri alma yöntemi ölçülüyor (Parça 0 f); hiçbir şey silinmedi." + `obs.warn("bot_unut_hazir_degil", bot=...)`. Her dal defter satırı (`tur`: `hatirla`/`unut`). (4) kota: `gun = simdi.strftime("%Y-%m-%d")` (UTC; `simdi` yoksa `datetime.now(timezone.utc)`), `n = gunluk_sayim(bot, gun)`; `tavan` doluysa ve `n >= tavan` → `f"@{bot} bugünlük kotam doldu ({n}/{tavan}); yarın (UTC) yeniden."` + defter `tur: kota_doldu`; (5) `tasiyici = tasiyici or HermesTasiyici()`; `t0` ölç; `sor` istisnası → defter `tur: hata, hata: <sınıf adı>` + yeniden fırlat; (6) başarı → defter `tur: sohbet` (+ `sure_s`, `arac_cagrilari`, `model_cagrilari`, `kota_bugun: n+1`) ve metni döndür. Defter yazımı `_defter_yaz(satir)` içinde: `store.append_jsonl` istisnası → `obs.warn("bot_defter_yazim_hatasi", sinif=...)` (sinyalli; cevap düşmez). `mesaj`/`cevap` `notify.scrub`'dan geçer; `cevap` `CEVAP_TAVANI`'na kesilir, `kesildi` alanı her satırda. `HermesTasiyici._cagir_varsayilan(url, govde, basliklar, zaman_asimi)` `urllib` ile POST + `json.load`; `HTTPError` → `RuntimeError(f"api_server HTTP {e.code}")` (yalnız kod; `e.url`/`str(e)` YOK); anahtar `_anahtar or (lambda: secrets.credential_oku("API_SERVER_KEY"))`.

- [ ] **Step 4: codelaw beyanı** — `meridian/codelaw.py` `DECLARED_SINKS`e `bot_sohbet.jsonl` satırı (mevcut `telegram_ofset.json` satırının biçimiyle, gerekçe Global Constraints'teki metin) + `tests/test_codelaw_kor_nokta_v214.py` `SINK_TABANI`.

- [ ] **Step 5: Yeşili gör** — Run: `.venv/bin/python -m pytest tests/test_bot_kanal_v593.py tests/test_codelaw_kor_nokta_v214.py -p no:cacheprovider` · Expected: tümü PASS.

- [ ] **Step 6: Mutasyonla ısırt** (yedekten geri al, sha256 eşit): (i) kanal kontrolünü sil → parametrik test kırmızı; (ii) kota karşılaştırmasını `>`e çevir → kota testi kırmızı; (iii) `hatırla` dalını kaldır (modele gitsin) → hatırla testleri kırmızı; (iv) defter satırında `scrub`'ı kaldır → scrub testi kırmızı; (v) `_defter_yaz` istisnasını yakalama → yazım hatası testi kırmızı; (vi) `HTTPError` mesajına `str(e)` ekle → (Görev 1'e bir jeton-sızıntı testi ekle: `_cagir` URL'de anahtar taşıyan `HTTPError` fırlatır, `RuntimeError` metninde anahtar yok).

- [ ] **Step 7: Kapsam** (SERİ, ön planda) — v593 + v592 + v591 + codelaw dosyaları (`grep -l codelaw tests/test_*.py`) + v391 + v571 · Expected: üçlü hüküm yeşil.

- [ ] **Step 8: Commit** (Rol-1) — `git add meridian/bot_kanal.py meridian/codelaw.py tests/test_codelaw_kor_nokta_v214.py tests/test_bot_kanal_v593.py`

---

### Task 2: `meridian/is_istek.py` + `.path` birimleri — "şimdi çalıştır"

**Files:**
- Create: `meridian/is_istek.py`
- Create: `deploy/oracle-a1/meridian-istek-sef.path`, `deploy/oracle-a1/meridian-istek-bekci.path`, `deploy/oracle-a1/meridian-istek-karne.path`
- Modify: `deploy/ansible/roles/meridian_a1/defaults/main.yml` (`birim_kaynaklari`ne üç `.path` — `etkin_birimler`e DEĞİL; şerh: "rol yalnız kopyalar; Parça 1 dağıtımında elle test-ateşle → ayrı değişiklikle etkin")
- Modify: `meridian/codelaw.py` + `tests/test_codelaw_kor_nokta_v214.py` (`istek/*.istek` ve `is_istek_defteri.jsonl` beyanları — okuyucu: systemd `.path` birimi / `is_iste` tavan kontrolü)
- Test: `tests/test_is_istek_v594.py`

**Interfaces:**
- Consumes: `kadro.aktif_botlar`, `kadro.bot_bul`, `kadro.ad_katla`; `store`; `obs`; `config.STATE`
- Produces:
  - `IS_TAVAN_S = 900`, `ISTEK_DIZINI = "istek"`, `DEFTER = "is_istek_defteri.jsonl"`, `TAKMA_ADLAR = {"brifing": "sef"}`
  - `@dataclass(frozen=True) class IsSonuc: kabul: bool; bot: str | None; birim: str | None; neden: str; sonraki_uygun: str | None`
  - `def is_listesi(kadro=None) -> dict[str, str]` — `{bot: zamanli_is}` yalnız `aktif` ve `zamanli_is` dolu botlar
  - `def is_iste(ad: str, kanal: str, *, simdi=None, kadro=None) -> IsSonuc` — `neden` ∈ `kabul · bilinmeyen_is · tavan`

- [ ] **Step 1: Başarısız testleri yaz** — `tests/test_is_istek_v594.py`:

```python
"""v594 — 'şimdi çalıştır' (spec 2026-09-29 §3.6): kadrodan türeyen iş listesi, 15 dk tavanı, istek dosyası, .path birimleri."""
import datetime as dt
import json
import re

import pytest
import yaml

from meridian import config, is_istek as ii, kadro

ROOT = config.ROOT
SIMDI = dt.datetime(2026, 9, 29, 12, 0, tzinfo=dt.timezone.utc)


def test_is_listesi_kadrodan_turer():
    assert ii.is_listesi() == {"sef": "meridian-brifing", "bekci": "meridian-bekci", "karne": "meridian-karne"}


@pytest.mark.parametrize("ad,bot", [("karne", "karne"), ("BEKÇİ", "bekci"), ("brifing", "sef"), ("şef", "sef")])
def test_kabul_istek_dosyasini_yazar(sandbox_state, ad, bot):
    s = ii.is_iste(ad, "telegram", simdi=SIMDI)
    assert (s.kabul, s.bot, s.neden) == (True, bot, "kabul")
    govde = json.loads((config.STATE / ii.ISTEK_DIZINI / f"{bot}.istek").read_text())
    assert govde["kanal"] == "telegram" and govde["ts"].startswith("2026-09-29T12:00")


def test_bilinmeyen_ve_zamanli_isi_olmayan_bot(sandbox_state):
    assert ii.is_iste("yokboyle", "pano", simdi=SIMDI).neden == "bilinmeyen_is"
    assert ii.is_iste("kod", "pano", simdi=SIMDI).neden == "bilinmeyen_is"


def test_tavan_15_dakika(sandbox_state):
    assert ii.is_iste("karne", "pano", simdi=SIMDI).kabul
    s = ii.is_iste("karne", "telegram", simdi=SIMDI + dt.timedelta(minutes=14))
    assert (s.kabul, s.neden) == (False, "tavan") and s.sonraki_uygun.startswith("2026-09-29T12:15")
    assert ii.is_iste("karne", "telegram", simdi=SIMDI + dt.timedelta(minutes=15)).kabul


def test_tavan_bot_basina(sandbox_state):
    assert ii.is_iste("karne", "pano", simdi=SIMDI).kabul
    assert ii.is_iste("bekci", "pano", simdi=SIMDI).kabul


def test_red_istek_dosyasina_dokunmaz(sandbox_state):
    ii.is_iste("karne", "pano", simdi=SIMDI)
    p = config.STATE / ii.ISTEK_DIZINI / "karne.istek"
    once = p.read_text()
    ii.is_iste("karne", "pano", simdi=SIMDI + dt.timedelta(minutes=1))
    assert p.read_text() == once


@pytest.mark.parametrize("bot,birim", [("sef", "meridian-brifing"), ("bekci", "meridian-bekci"), ("karne", "meridian-karne")])
def test_path_birimi_dogru_servisi_ve_dosyayi_izler(bot, birim):
    metin = (ROOT / "deploy/oracle-a1" / f"meridian-istek-{bot}.path").read_text(encoding="utf-8")
    assert re.search(rf"^PathChanged=/opt/meridian/state/istek/{bot}\.istek$", metin, re.M)
    assert re.search(rf"^Unit={birim}\.service$", metin, re.M)
    assert "PathExists=" not in metin  # dosya silinmediği için PathExists sonsuz yeniden tetikler
    assert (ROOT / "deploy/oracle-a1" / f"{birim}.service").is_file()


def test_path_birimleri_kopyalanir_ama_etkin_degil():
    d = yaml.safe_load((ROOT / "deploy/ansible/roles/meridian_a1/defaults/main.yml").read_text(encoding="utf-8"))
    kaynaklar = json.dumps(d.get("birim_kaynaklari"))
    etkin = json.dumps(d.get("etkin_birimler"))
    for bot in ("sef", "bekci", "karne"):
        assert f"meridian-istek-{bot}.path" in kaynaklar and f"meridian-istek-{bot}.path" not in etkin


def test_her_zamanli_is_icin_path_birimi_var():
    for bot in ii.is_listesi():
        assert (ROOT / "deploy/oracle-a1" / f"meridian-istek-{bot}.path").is_file(), bot
```

- [ ] **Step 2: Kırmızıyı gör** — Run: `.venv/bin/python -m pytest tests/test_is_istek_v594.py -p no:cacheprovider` · Expected: `ModuleNotFoundError: meridian.is_istek`.

- [ ] **Step 3: Uygula** — `meridian/is_istek.py`: `is_iste`: `hedef = TAKMA_ADLAR.get(kadro.ad_katla(ad), kadro.ad_katla(ad))`; `is_listesi()`'de yoksa `bilinmeyen_is`; tavan: `is_istek_defteri.jsonl`de o bot için son `kabul` satırının `ts`i + `IS_TAVAN_S` > `simdi` ise `tavan` (sonraki uygun ISO); kabul → `config.STATE/istek/<bot>.istek` dosyasına ATOMİK yaz (geçici dosya + `os.replace`; dizin yoksa `0o750` ile kur) gövde `{"bot", "kanal", "ts"}`, sonra defter satırı; tavan kontrolü + yazım SÜREÇLER ARASI kilit altında: `fcntl.flock` ile `config.STATE/istek/.kilit` (LOCK_EX) — `store.file_lock` KULLANILMAZ, o süreç-içidir (memory: karne yazım güvenliği) ve istekler iki ayrı süreçten (Telegram dinleyicisi, pano API) gelir (Review Focus 2). Test: `multiprocessing` ile iki süreç aynı anda `is_iste("karne")` → tam bir `kabul`, bir `tavan`. `.path` birimleri (üçü aynı şablon, `<bot>`/`<birim>` değişir):

```ini
# meridian-istek-<bot>.path — konuşan filo "şimdi çalıştır" (spec 2026-09-29 §3.6).
# is_iste() state/istek/<bot>.istek dosyasını her kabul edilen istekte YENİDEN YAZAR → PathChanged
# (kapanışta) <birim>.service'i başlatır. PathExists KULLANILMAZ: dosya silinmez, PathExists servis
# bittikçe yeniden tetiklerdi. Oneshot koşarken gelen ikinci tetik aynı işe katılır (çift koşum yok).
# A0 rolü YALNIZ KOPYALAR; etkinleştirme Parça 1 dağıtımında elle test-ateşlemeden sonra.
[Unit]
Description=Meridian konuşan filo — @<bot> iş isteği izleyicisi

[Path]
PathChanged=/opt/meridian/state/istek/<bot>.istek
Unit=<birim>.service

[Install]
WantedBy=paths.target
```

- [ ] **Step 4: A0 listesi + codelaw beyanları** — `birim_kaynaklari`ne üç `.path` (mevcut girdilerin biçimiyle; `etkin_birimler`e dokunma); codelaw `DECLARED_SINKS` + v214. Ardından A0/birim çivilerini bul ve koş: `grep -l "birim_kaynaklari\|etkin_birimler" tests/test_*.py` (v553 dahil) — yeni `.path` türü mevcut çivilerin bir varsayımını kırıyorsa (ör. her birim `.service`/`.timer`), ölç ve en küçük doğru değişikliği yap, rapora ruling olarak yaz.

- [ ] **Step 5: Yeşili gör** — Run: `.venv/bin/python -m pytest tests/test_is_istek_v594.py tests/test_codelaw_kor_nokta_v214.py $(grep -l "birim_kaynaklari\|etkin_birimler" tests/test_*.py) -p no:cacheprovider` · Expected: tümü PASS.

- [ ] **Step 6: Mutasyonla ısırt**: (i) `IS_TAVAN_S` kontrolünü kaldır → tavan testi kırmızı; (ii) bir `.path`te `PathChanged`→`PathExists` → birim testi kırmızı; (iii) `birim_kaynaklari`nden bir `.path`i sil → kopya testi kırmızı; (iv) `TAKMA_ADLAR`ı boşalt → `brifing` testi kırmızı; (v) red dalında dosyayı yeniden yaz → `test_red_istek_dosyasina_dokunmaz` kırmızı.

- [ ] **Step 7: Kapsam** (SERİ) — v594 + v593 + v592 + v591 + codelaw + A0/birim çivileri + tarama çivileri (v334 · v266 · v98 · v382 · v571 · v154) · Expected: üçlü hüküm yeşil.

- [ ] **Step 8: Commit** (Rol-1) — `git add meridian/is_istek.py deploy/oracle-a1/meridian-istek-*.path deploy/ansible/roles/meridian_a1/defaults/main.yml meridian/codelaw.py tests/test_codelaw_kor_nokta_v214.py tests/test_is_istek_v594.py` (+ Step 4'te değişen çivi dosyaları, açık yollarla).
