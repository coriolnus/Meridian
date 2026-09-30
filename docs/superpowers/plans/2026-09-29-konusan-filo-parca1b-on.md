# Konuşan bot filosu — Parça 1b-ön: araçsız-veri uyarısı + gerçek hafıza yazıcısı (dağıtımsız) Uygulama Planı

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Parça 0'ın iki bulgusunu mimariden bağımsız biçimde kapatmak: (1) araçsız bot veri uydurur → `bota_sor` gerçek araç çağrı sayısını ölçer ve araçsız veri cevabına deterministik uyarı ekler; (2) `hatırla:`/`unut:` gerçek Hindsight yazıcısına bağlanır (unut = geri alınabilir `state: invalidated`).

**Architecture:** `TasiyiciSonuc.arac_cagrilari` zaten var; `HermesTasiyici` onu Hermes oturum mesajlarından (bu turun `tool_calls`ları) doldurur. `bota_sor` uyarıyı taşıyıcıdan bağımsız uygular (yedek taşıyıcı da aynı alanı doldurur). Yeni `meridian/bot_hafiza.py` `HindsightHafiza` sınıfı `Hafiza` protokolünü (yaz + yeni `unut`) Hindsight HTTP API'siyle uygular. Hiçbir canlı yol bunları çağırmaz (Parça 1b kablolaması operatörün K-1 kararından sonra).

**Tech Stack:** Python 3 stdlib (`urllib`, `json`, `re`), mevcut `meridian.bot_kanal`, `meridian.secrets`, `meridian.notify.scrub`, `meridian.obs`.

**Spec:** `docs/superpowers/specs/2026-09-29-konusan-bot-filosu-design.md` (§3.4 hafıza, §3.5, §4, §5) + Parça 0 raporu `docs/superpowers/specs/2026-09-29-konusan-bot-filosu-parca0-olcum.md` (EN AĞIR BULGU, (f)).

## Global Constraints
- Uydurma yasağı: araç sayısı ÖLÇÜLEMİYORSA `None` (0 değil); `None` ile `0` ayrı dallardır.
- Uyarı metinleri DONUK: `UYARI_ARACSIZ = "⚠️ Bu cevap hiçbir araç çağrısına dayanmıyor — içindeki veri doğrulanmadı."` · `UYARI_OLCULEMEDI = "⚠️ Bu cevabın araç kullanımı doğrulanamadı."`
- "Veri içeriyor" DETERMİNİSTİK: cevapta rakam ya da `%` ya da (katlanmış küçük harfle) `kaynak`/`source`/`.json`/`.jsonl` geçiyor.
- Defter satırı yeni alanlar: `arac_siz_veri: bool`, `arac_olculemedi: bool` (mevcut alanlar korunur).
- Hindsight: taban `http://127.0.0.1:8888/v1/default`, banka `bot-<ad>`, anahtar `secrets.credential_oku(<kiracı anahtarı adı>)` — ad TEK KAYNAKTAN (bugün `meridian/api.py::HAFIZA_KRED_ADI`; `bot_hafiza` onu `api`'yi içe aktarmadan kullanabilsin diye tek kaynak `meridian/secrets.py`ye taşınır, `api.HAFIZA_KRED_ADI` o kaynağa takma ad olur — v439 bölüm I eşitlik çivisi yeşil kalmalı). Taban URL için aynı desen (`api.HAFIZA_TABAN_URL`).
- Her HTTP çağrısı zaman aşımlı (`HAFIZA_ZAMAN_ASIMI_S = 10`), sonlu > 0 doğrulamalı (`HermesTasiyici` emsali). Anahtar yalnız `Authorization` başlığında; istisna metninde yalnız sınıf + HTTP kodu.
- Kalıcı silme YOK: `unut` yalnız `PATCH …/memories/{id}` `{"state": "invalidated", "reason": ...}`; en fazla `UNUT_TAVANI = 3` bellek, recall skoruna göre; geri alma `{"state": "valid"}` (bu planda API fonksiyonu olarak, komut değil).
- Test numaraları: v596 (bot_hafiza), v593'e ek testler (uyarı). Test adlarında FAILED/ERROR yok; yorumlarda `dosya.py:NNN` yok; Yasa 4/6.

## Review Focus
1. Hermes oturum mesajlarında önceki turların `tool_calls`ı sayılırsa uyarı yanlış yere susar → yalnız SON kullanıcı mesajından sonraki asistan/araç mesajları sayılır (Görev 1 testi: geçmişte araç var, bu turda yok → uyarı VAR).
2. `unut` belirsiz bir ifadeyle alakasız belleği emekliye ayırır → tavan 3 + operatöre hangi metinleri unuttuğunu kısa listeyle söyler + her PATCH `reason` taşır (Görev 2 testi).
3. Hindsight erişilemezse `hatırla`/`unut` operatöre sessiz kalmamalı → "YAZILAMADI"/"UNUTULAMADI" + olay (mevcut `bota_sor` dalları) — Görev 2'de gerçek sınıfla testli.
4. Uyarı çift eklenmesin (cevap zaten uyarıyla başlıyorsa) ve defterdeki `cevap` uyarıyı içersin (operatörün gördüğü metin).
5. `credential_oku` `None` dönerse `HindsightHafiza` açıkça "anahtar yok" hatası verir (değer basmadan).

---

### Task 1: Araçsız-veri uyarısı (`meridian/bot_kanal.py`)

**Files:** Modify `meridian/bot_kanal.py` · Test `tests/test_bot_kanal_v593.py` (ek testler)

**Interfaces:**
- Produces: `UYARI_ARACSIZ`, `UYARI_OLCULEMEDI`, `def veri_iceriyor(metin: str) -> bool`; `HermesTasiyici.sor` artık `arac_cagrilari`ı doldurur (ölçülemezse `None`); `bota_sor` uyarı mantığı; defter `arac_siz_veri`, `arac_olculemedi`.

- [ ] **Step 1: Başarısız testler** (v593'e):

```python
@pytest.mark.parametrize("cevap,beklenen", [
    ("Rejim neutral, bütçe %100", True), ("kaynak: risk/state.json", True), ("Bugün 3 kalem var", True),
    ("Merhaba, nasıl yardımcı olabilirim?", False), ("", False)])
def test_veri_iceriyor(cevap, beklenen):
    assert bk.veri_iceriyor(cevap) is beklenen


class SayacliTasiyici(SahteTasiyici):
    def __init__(self, metin, arac):
        super().__init__(metin); self.arac = arac
    def sor(self, bot, mesaj, oturum):
        self.cagrilar.append((bot, mesaj, oturum))
        return bk.TasiyiciSonuc(self.metin, arac_cagrilari=self.arac, model_cagrilari=1)


def test_aracsiz_veri_uyarisi_ve_defter(sandbox_state):
    c = bk.bota_sor("bekci", "rejim?", "telegram", "o", tasiyici=SayacliTasiyici("Rejim neutral, bütçe %100", 0), simdi=SIMDI)
    assert c.startswith(bk.UYARI_ARACSIZ) and "Rejim neutral" in c
    s = _defter()[-1]
    assert s["arac_siz_veri"] is True and s["cevap"].startswith(bk.UYARI_ARACSIZ)


def test_aracli_veri_uyarisiz(sandbox_state):
    c = bk.bota_sor("bekci", "rejim?", "telegram", "o", tasiyici=SayacliTasiyici("Rejim neutral", 2), simdi=SIMDI)
    assert not c.startswith("⚠️") and _defter()[-1]["arac_siz_veri"] is False


def test_verisiz_aracsiz_cevap_uyarisiz(sandbox_state):
    c = bk.bota_sor("sef", "selam", "pano", "o", tasiyici=SayacliTasiyici("Merhaba!", 0), simdi=SIMDI)
    assert c == "Merhaba!"


def test_arac_sayisi_olculemediyse_ayri_uyari(sandbox_state):
    c = bk.bota_sor("karne", "getiri?", "pano", "o", tasiyici=SayacliTasiyici("Getiri %2", None), simdi=SIMDI)
    assert c.startswith(bk.UYARI_OLCULEMEDI) and _defter()[-1]["arac_olculemedi"] is True


def test_uyari_cift_eklenmez(sandbox_state):
    c = bk.bota_sor("bekci", "x", "pano", "o", tasiyici=SayacliTasiyici(bk.UYARI_ARACSIZ + "\n3 kalem", 0), simdi=SIMDI)
    assert c.count(bk.UYARI_ARACSIZ) == 1


def test_hermes_tasiyici_bu_turun_arac_cagrilarini_sayar():
    oturum_mesajlari = {"data": [
        {"role": "user", "content": "eski"}, {"role": "assistant", "tool_calls": [{"function": {"name": "a"}}]},
        {"role": "tool", "content": "x"}, {"role": "assistant", "content": "eski cevap"},
        {"role": "user", "content": "yeni"}, {"role": "assistant", "content": "yeni cevap"}]}
    def cagir(url, govde, basliklar, zaman_asimi):
        if url.endswith("/chat/completions"):
            return {"choices": [{"message": {"content": "yeni cevap"}}]}
        assert url.endswith("/p/bekci/api/sessions/o-1/messages") and govde is None
        return oturum_mesajlari
    s = bk.HermesTasiyici(_cagir=cagir, _anahtar=lambda: "K" * 32).sor("bekci", "yeni", "o-1")
    assert s.arac_cagrilari == 0


def test_hermes_tasiyici_oturum_okunamazsa_none():
    def cagir(url, govde, basliklar, zaman_asimi):
        if url.endswith("/chat/completions"):
            return {"choices": [{"message": {"content": "c"}}]}
        raise OSError("okunamadı")
    assert bk.HermesTasiyici(_cagir=cagir, _anahtar=lambda: "K" * 32).sor("bekci", "m", "o").arac_cagrilari is None
```

- [ ] **Step 2: Kırmızıyı gör** — `.venv/bin/python -m pytest tests/test_bot_kanal_v593.py -p no:cacheprovider` · Expected: yeni testler `AttributeError`/assert ile düşer.
- [ ] **Step 3: Uygula** — `_cagir` imzası GET için `govde=None` kabul eder (`urllib` GET); `HermesTasiyici.sor` sohbet çağrısından sonra `GET {taban}/p/{bot}/api/sessions/{oturum}/messages`; SON `role == "user"` mesajından sonraki mesajlarda `tool_calls` öğelerini sayar; GET istisnası → `arac_cagrilari=None` + `obs.warn("bot_arac_sayimi_olculemedi", bot=..., sinif=...)`. `bota_sor` başarı dalında: `n = sonuc.arac_cagrilari`; `n is None` → `UYARI_OLCULEMEDI` öneki, `arac_olculemedi=True`; `n == 0 and veri_iceriyor(metin)` → `UYARI_ARACSIZ` öneki, `arac_siz_veri=True`; önek zaten varsa eklenmez; önek + `"\n"` + metin döner ve deftere yazılır.
- [ ] **Step 4: Yeşil** — aynı komut · Expected: tümü PASS.
- [ ] **Step 5: Mutasyon** — (i) sayımı bütün mesajlar üzerinden yap → `…bu_turun…` kırmızı; (ii) `None`'u 0 say → `…olculemediyse…` kırmızı; (iii) `veri_iceriyor`dan `%` dalını çıkar → parametrik kırmızı; (iv) çift-önek korumasını kaldır → kırmızı.
- [ ] **Step 6: Kapsam** — v593 + v592 + v591 + codelaw dosyaları + v391 + v571 (seri, üçlü hüküm).

---

### Task 2: `meridian/bot_hafiza.py` — Hindsight hafıza yazıcısı

**Files:** Create `meridian/bot_hafiza.py` · Modify `meridian/secrets.py` (kiracı anahtarı adı + taban URL TEK KAYNAK), `meridian/api.py` (takma ad), `meridian/bot_kanal.py` (`Hafiza` protokolüne `unut`, `unut:` dalı gerçek çağrı) · Test `tests/test_bot_hafiza_v596.py`, `tests/test_bot_kanal_v593.py` (unut dalı)

**Interfaces:**
- Consumes: `bot_kanal.Hafiza`, `bot_kanal.komut_oneki`, `secrets.credential_oku`
- Produces: `class HindsightHafiza: __init__(self, taban_url=<tek kaynak>, zaman_asimi_s=10.0, _cagir=None, _anahtar=None)`; `yaz(bot, metin, etiketler) -> bool`; `unut(bot, ifade) -> list[tuple[str, str]]` (emekliye ayrılan `(id, metin_kesiti≤80)`); `geri_al(bot, memory_id) -> bool`; `UNUT_TAVANI = 3`; `Hafiza` protokolü `unut(bot, ifade) -> list[tuple[str, str]]` ile genişler.

- [ ] **Step 1: Başarısız testler** — `tests/test_bot_hafiza_v596.py` (sahte `_cagir` ile istek biçimi): `yaz` → `POST /v1/default/banks/bot-bekci/memories`, gövde `{"items": [{"content": metin, "timestamp": <ISO UTC>, "context": "operatör notu", "tags": [...], "metadata": {"kaynak": "operator"}}], "async": False}`, başlık yalnız `Authorization: Bearer`; `unut` → önce `POST …/memories/recall` (`{"query": ifade, "budget": "low", "max_tokens": ...}`), sonuçtan en fazla 3 `id` için `PATCH …/memories/{id}` `{"state": "invalidated", "reason": "operatör unut: <ifade> (<ISO>)"}`, dönüş kesitleri; recall boş → `[]` ve PATCH YOK; `geri_al` → `{"state": "valid"}`; HTTPError → `RuntimeError("hindsight HTTP <kod>")` (anahtar/URL yok); anahtar `None` → `RuntimeError("hindsight kiracı anahtarı credential yok")`; zaman aşımı sonlu > 0 doğrulaması. v593: `unut:` dalı `hafiza.unut` çağırır; liste doluysa "Unuttum (geri alınabilir): 1) … 2) …", boşsa "Eşleşen bir not bulamadım; hiçbir şey unutulmadı."; `hafiza.unut` istisnası → "UNUTULAMADI" + olay; `hafiza=None` → mevcut "bağlı değil" dalı. v439: `api.HAFIZA_KRED_ADI is secrets.<yeni ad>` (ya da eşit) çivisi.
- [ ] **Step 2: Kırmızı** · **Step 3: Uygula** (recall cevabının biçimini `hafiza_sor.sh`/`api._hafiza_*` okuyucularından ölç — `results`/`memories` anahtarı, `id`, `text` alanları; uydurma) · **Step 4: Yeşil** · **Step 5: Mutasyon** (tavanı kaldır → 4. PATCH kırmızı; `state` değerini `"deleted"` yap → kırmızı; recall boşken PATCH at → kırmızı; anahtarı hata metnine koy → kırmızı) · **Step 6: Kapsam** — v596 + v593 + v592 + v439 (I bölümü) + api hafıza testleri (`grep -l "HAFIZA_KRED_ADI\|_hafiza_" tests/test_*.py`) + codelaw + v391 + v571 + v334 + v382.
