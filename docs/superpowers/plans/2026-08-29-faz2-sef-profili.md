# Faz 2 — `@sef` profili: uygulama planı

> **Ajan işçiler için:** ZORUNLU ALT-SKILL: bu planı görev görev uygulamak için
> superpowers:subagent-driven-development (önerilen) ya da superpowers:executing-plans kullan.
> Adımlar onay kutusu (`- [ ]`) biçimindedir.

**Hedef:** Roster'ın İLK Hermes profilini kurmak — üç teslimat kaynağını tek, öncelikli bir
brifinge indiren `@sef`. Repo tarafı eksiksiz; canlıda hiçbir şey yaratılmaz/etkinleştirilmez.

**Mimari:** `ops/sef_brifingi.py` bir KOŞUM KOŞUMUDUR (harness): iki `ozet_kur()` fonksiyonunu
ve `self_review.json`u okur, tek bir prompt kurar, `sef` profilini `HERMES_HOME` ile TEK ATIŞLIK
çağırır, dönen sıralamayı `notify.send` ile teslim eder. LLM düşerse HAM birleşik brifing yine
gider — alarm teslimatı bir modele BAĞLANMAZ.

**Teknoloji:** Hermes Agent v0.19.0 profile distribution (`distribution.yaml`) · systemd
`meridian-brifing.service` · `meridian.notify` · OpenRouter `nvidia/nemotron-3-super-120b-a12b:free`.

**Spec:** `docs/superpowers/specs/2026-08-27-bot-roster-design.md` (§2 roller · §3 fazlar ·
§9 güvenlik duruşu · §9.4 üç çivi).

---

## Neden `@sef` — hüküm ve gerekçesi

Spec §3: *"Faz 2 — İLK profil. Faz 1'de iş akışı kanıtlanmış olan. **Tek.**"*

**`@nobet` değerlendirildi ve ölçümle elendi.** Ayırt edici yarısı (talep üzerine KONUŞMA)
Hermes gateway + **ikinci bir Telegram bot token'ı** ister (spec §7, açıkça Faz 2'ye ertelenmiş
soru) — token bir sırdır, ajan yaratmaz. LLM'siz yarısı Faz 1'de zaten var ve saf Python; ona
profil giydirmek hiçbir şey EKLEMEZ.

**`@karne` Faz 3'e bırakıldı**, zayıf olduğu için değil: Faz 1 planının kendisi bu turun işini
adıyla `@sef`e vermiş — *"Birleştirme `@sef`in işidir ve Faz 2'ye aittir"*
(`docs/superpowers/plans/2026-08-27-faz1-bot-roster.md`, "Spec'ten SAPMA" bölümü). O cümleyi
gerekçesiz değiştirmek tutarsızlık olurdu.

`@sef`in dört dayanağı:
1. **İş akışı Faz 1'de kanıtlandı.** Bugün ÜÇ teslimat yolu var — alarm digest · öneri brifingi ·
   `selfreview.weekly()` (scheduler'da asılı, kendi `notify.send`ini çağırıyor) — ve üçü de
   AYRI, önceliksiz mesaj olarak geliyor.
2. **Spec'in ADINI KOYDUĞU iki ASIL KISITA vuruyor** (§5): *operatör dikkati* ve *okunmayan çıktı
   riski*. Öteki roller üretim ekler; `@sef` okunabilirlik ekler.
3. **Sahip olduğu artefakt gerçek, okuyucusu beyanlı** (§2 değişmez şartı).
4. **İşlem riski sıfır** — hiçbir emir yüzeyine dokunmaz.

## Ölçülmüş zemin (bu plan bunların üstüne kurulu; hiçbiri varsayım değil)

| ölçüm | değer | kaynak |
|---|---|---|
| canlı Hermes | v0.19.0 | `~/.local/bin/hermes --version`, A1 |
| canlı profil sayısı | **0** (`~/.hermes/profiles/` yok) | A1 |
| profil = | bağımsız `HERMES_HOME` dizini | `hermes_cli/profiles.py:4` |
| tek-atışlık çağrı | `hermes -z PROMPT` | `hermes --help` |
| dağıtım kurulumu | `hermes profile install <yerel dizin>`, kökte `distribution.yaml` | `hermes profile install --help` |
| `.env` | KULLANICI-SAHİPLİ, dağıtım ASLA dokunmaz | `profile_distribution.py` güncelleme semantiği |
| `env_requires` | `.env` YAZMAZ — yalnız `.env.template` üretir | `profile_distribution.py:337` |
| `HERMES_WRITE_SAFE_ROOT` | ORTAM değişkeni; **tanımsızsa HİÇBİR kısıt yok** (`if safe_roots:`) | `agent/file_safety.py:148` |
| guard kancası | canlı `~/.hermes/config.yaml`de etkin, profile OTOMATİK GEÇMEZ | spec §9.0 |
| `approvals.cron_mode` | kod varsayılanı ZATEN `deny` | `tools/approval.py:2506` |
| özet/rapor çağrı bütçesi | Super · `max_tokens` 8.000 · `timeout` 120 sn | `docs/OLCUM-MODEL-BUTCESI-2026-08-27.md` §6 |
| iki betiğin şekli | `ozet_kur()` yan etkisiz hesap + `main()` gönderim | `ops/*.py` |

## Global Constraints

- **Teslimat YALNIZ `meridian.notify.send`** (§9.1). İkinci bir giden yol açılmaz.
- **LLM teslimatın ÖNKOŞULU DEĞİLDİR.** Model düşerse/zaman aşarsa ham birleşik brifing gider.
  Alarmların bir modele bağlanması, alarmın var oluş sebebini iptal eder.
- **Boşken SESSİZ.** Karar döndürmeyen zamanlanmış iş bildirim spam'idir (spec §8).
- **Her profil `pre_tool_call → meridian-guard.sh` TAŞIR** (§9.4/1) — korumasız profil doğamaz.
- **`approvals.cron_mode: deny`** (§9.4/2).
- **`HERMES_WRITE_SAFE_ROOT` kendi dizinine kısıtlı** (§9.4/3), İKİ yüzeyde birden.
- Canlıda profil YARATILMAZ, birim ETKİNLEŞTİRİLMEZ. Operatöre TEK komut bırakılır.
- Ajanlar git komutu koşmaz (CLAUDE.md madde 8); tam suite yalnız Rol-1'de (madde 6).
- **Satır çapası yazma.** `dosya.py:123` çürür. Bu turda ölçüldü: çapa taşıyan bir dosyada
  satır eklemek/çıkarmak BAŞKA bir çapayı sessizce kırar.

## Dosya yapısı

| dosya | sorumluluğu |
|---|---|
| `deploy/hermes/profiles/sef/distribution.yaml` | **YENİ.** Dağıtım manifesti; `env_requires` safe-root'u BEYAN eder. |
| `deploy/hermes/profiles/sef/config.yaml` | **YENİ.** Guard kancası + `approvals` duruşu + model. §9.4/1-2'nin repo tarafı. |
| `deploy/hermes/profiles/sef/SOUL.md` | **YENİ.** `@sef`in kalıcı brifingi: ne sıralar, neyi susturur, neyi ASLA yapmaz. |
| `ops/sef_brifingi.py` | **YENİ.** Koşum koşumu: topla → profili çağır → teslim et; LLM düşerse ham brifing. |
| `deploy/oracle-a1/meridian-brifing.service` | Değişir: ExecStart iki betik yerine `sef_brifingi.py`. |
| `deploy/oracle-a1/deploy.sh` | Değişir: profil dizini kurulumu (operatörün tek komutu). |
| `dagit.sh` | Değişir: `F9_LISTE`ye üç profil dosyası. |
| `deploy/hermes/config.yaml` | Değişir: `cron_mode` şerhindeki fazla iddia düzeltilir. |
| `tests/test_bot_profil_durusu_v329.py` | **YENİ.** §9.4'ün üç çivisi, hepsi REPO tarafında. |
| `tests/test_sef_brifingi_v330.py` | **YENİ.** Birleştirme · sessizlik · LLM düşüş yolu · damga. |

---

## Görev 1: Profil dağıtımı ve §9.4'ün üç çivisi

**Dosyalar:**
- Oluştur: `deploy/hermes/profiles/sef/distribution.yaml`
- Oluştur: `deploy/hermes/profiles/sef/config.yaml`
- Oluştur: `deploy/hermes/profiles/sef/SOUL.md`
- Oluştur: `tests/test_bot_profil_durusu_v329.py`
- Değiştir: `deploy/hermes/config.yaml` (yalnız `cron_mode` şerhi)

**Arayüzler:**
- Üretir: `PROFIL_KOKU = "deploy/hermes/profiles"` dizin sözleşmesi — Görev 3 kurulum adımını
  buradan okur; ileride her yeni bot bu şablona düşer.
- Üretir: safe-root yolu `/opt/meridian/var/bots/sef` — Görev 3 birimin `Environment=` satırına
  BİREBİR bunu yazar.

- [ ] **Adım 1: Çiviyi yaz (kırmızı doğmalı — henüz hiç profil yok)**

```python
# tests/test_bot_profil_durusu_v329.py
"""Her bot profili güvenlik duruşunu REPO TARAFINDA taşır — canlıya varmadan ölçülür.

Spec §9.4 üç çivi ister. Üçü de burada, ve üçü de `~/.hermes/profiles/` DEĞİL
`deploy/hermes/profiles/` üstünde ölçülür: canlıyı okuyan bir çivi, dosya canlıya VARDIKTAN
sonra bağırır — oysa korumasız bir profilin doğmaması gerekiyordu.
"""
from __future__ import annotations

import pathlib

import pytest
import yaml

KOK = pathlib.Path(__file__).resolve().parent.parent
PROFIL_KOKU = KOK / "deploy" / "hermes" / "profiles"

GEREKLI_DENY = ["*dagit.sh*", "*git push*", "*git commit*", "*systemctl*", "*serve.sh*"]


def _profiller() -> list[pathlib.Path]:
    if not PROFIL_KOKU.is_dir():
        return []
    return sorted(p for p in PROFIL_KOKU.iterdir() if (p / "distribution.yaml").is_file())


def test_EN_AZ_BIR_PROFIL_VAR():
    """Kapsam boşsa üstteki çiviler VACUOUSLY yeşil olurdu — sıfır profil, sıfır ihlal."""
    assert _profiller(), (
        f"{PROFIL_KOKU} altında `distribution.yaml` taşıyan profil YOK — aşağıdaki duruş "
        "çivileri hiçbir şey ölçmüyor demektir")


@pytest.mark.parametrize("profil", _profiller(), ids=lambda p: p.name)
def test_PROFIL_GUARD_KANCASINI_TASIR(profil):
    """§9.4/1. `--clone` kancayı taşır, SIFIRDAN kurulan profil KORUMASIZ doğar (spec §9.0'ın
    en önemli bulgusu). Bot çoğaltmak, kancasız ajan sayısını çoğaltma riskidir."""
    cfg = yaml.safe_load((profil / "config.yaml").read_text(encoding="utf-8")) or {}
    kancalar = ((cfg.get("hooks") or {}).get("pre_tool_call")) or []
    komutlar = [str(k.get("command", "")) for k in kancalar if isinstance(k, dict)]
    assert any("meridian-guard.sh" in c for c in komutlar), (
        f"{profil.name}: `pre_tool_call → meridian-guard.sh` YOK — profil korumasız doğar")


@pytest.mark.parametrize("profil", _profiller(), ids=lambda p: p.name)
def test_CRON_MODE_DENY_DISINDA_OLAMAZ(profil):
    """§9.4/2. Başsız cron oturumu tehlikeli komutu ONAYLAYAMAZ."""
    cfg = yaml.safe_load((profil / "config.yaml").read_text(encoding="utf-8")) or {}
    mod = str(((cfg.get("approvals") or {}).get("cron_mode") or "")).strip().lower()
    assert mod == "deny", f"{profil.name}: approvals.cron_mode = {mod!r} — `deny` olmalı"


@pytest.mark.parametrize("profil", _profiller(), ids=lambda p: p.name)
def test_DENY_LISTESI_TAM_VE_IKI_YANDAN_SARILI(profil):
    """Ana profilin listesi profillere OTOMATİK GEÇMEZ. Ve her desen iki yandan sarılı olmalı:
    ön-eke çakılı bir desenin altından `cd /opt/meridian && git push` geçer (2026-08-29 ölçümü)."""
    cfg = yaml.safe_load((profil / "config.yaml").read_text(encoding="utf-8")) or {}
    deny = [str(d) for d in ((cfg.get("approvals") or {}).get("deny") or [])]
    eksik = [d for d in GEREKLI_DENY if d not in deny]
    assert not eksik, f"{profil.name}: deny listesinde eksik desen(ler): {eksik} · mevcut: {deny}"
    sarilmamis = [d for d in deny if not (d.startswith("*") and d.endswith("*"))]
    assert not sarilmamis, (
        f"{profil.name}: iki yandan sarılmamış desen(ler): {sarilmamis} — mutlak yol, "
        "`cd /x && <komut>` ve baştaki boşluk bu yasağın altından geçer")


@pytest.mark.parametrize("profil", _profiller(), ids=lambda p: p.name)
def test_SAFE_ROOT_BEYAN_EDILIR_ve_KENDI_DIZINIDIR(profil):
    """§9.4/3, BİRİNCİ yüzey (manifest beyanı).

    ÖLÇÜLDÜ (`agent/file_safety.py`, `if safe_roots:`): değişken TANIMSIZSA hiçbir yazma kısıtı
    UYGULANMAZ — yalnız kimlik yolları bloklu kalır. Yani beyan süs değil TAŞIYICIDIR. Ve
    `env_requires` `.env` YAZMAZ, `.env.template` üretir: bu yüzden İKİNCİ yüzey (systemd
    `Environment=`) ayrı çividir ve zamanlanmış koşumu O bağlar.
    """
    man = yaml.safe_load((profil / "distribution.yaml").read_text(encoding="utf-8")) or {}
    gerekli = {str(e.get("name")): e for e in (man.get("env_requires") or [])
               if isinstance(e, dict)}
    e = gerekli.get("HERMES_WRITE_SAFE_ROOT")
    assert e is not None, (
        f"{profil.name}: `HERMES_WRITE_SAFE_ROOT` manifestte BEYAN EDİLMEMİŞ — tanımsız "
        "değişken = SINIRSIZ yazma yetkisi")
    assert e.get("required") is True, f"{profil.name}: safe-root `required: true` olmalı"
    varsayilan = str(e.get("default") or "")
    assert varsayilan.endswith(f"/bots/{profil.name}"), (
        f"{profil.name}: safe-root varsayılanı kendi dizini olmalı, bulunan: {varsayilan!r}")


@pytest.mark.parametrize("profil", _profiller(), ids=lambda p: p.name)
def test_MANIFEST_HERMES_SURUMUNU_SARTA_BAGLAR(profil):
    """Canlıda ölçülen sürüm v0.19.0. Manifest bir taban beyan etmezse, dağıtım eski bir
    kurulumda sessizce yarım kurulur."""
    man = yaml.safe_load((profil / "distribution.yaml").read_text(encoding="utf-8")) or {}
    assert str(man.get("hermes_requires") or "").startswith(">="), (
        f"{profil.name}: `hermes_requires` yok ya da taban beyan etmiyor")
    assert str(man.get("name")) == profil.name, "manifest adı dizin adıyla ayrışıyor"
```

- [ ] **Adım 2: Çiviyi koş, KIRMIZI gördüğünü doğrula**

Koş: `.venv/bin/python -m pytest tests/test_bot_profil_durusu_v329.py -v`
Beklenen: `test_EN_AZ_BIR_PROFIL_VAR` FAIL — "distribution.yaml taşıyan profil YOK".
(Öteki çiviler parametrize kapsamı boş olduğu için TOPLANMAZ; bu yüzden birinci çivi var.)

- [ ] **Adım 3: Manifesti yaz**

```yaml
# deploy/hermes/profiles/sef/distribution.yaml
# @sef — dikkat bütçesi. Üç teslimat kaynağını TEK öncelikli brifinge indirir.
#
# KURULUM (operatörün TEK komutu, canlıda):
#     hermes profile install /opt/meridian/deploy/hermes/profiles/sef
# Kurulum bu depoda YAPILMAZ ve dağıtım betiği de YAPMAZ: profil yaratmak canlıda yeni bir
# ajan kimliği doğurur ve bu operatör kararıdır (CLAUDE.md madde 5).
name: sef
version: 0.1.0
description: >-
  Meridian dikkat bütçesi. Alarm yığınını, iyileştirme önerilerini ve haftalık öz-değerlendirmeyi
  okur; operatöre TEK, öncelikli brifing yazar. Hiçbir şey önemli değilse SUSAR.
hermes_requires: ">=0.19.0"
author: "Meridian / Rol-1"
license: "özel — bu depoya ait"

env_requires:
  - name: HERMES_WRITE_SAFE_ROOT
    description: >-
      Bu botun yazabileceği TEK dizin. ÖLÇÜLDÜ (agent/file_safety.py): değişken TANIMSIZSA
      hiçbir yazma kısıtı uygulanmaz — beyan etmemek, sınırsız yetki vermektir. Zamanlanmış
      koşumda değeri systemd birimi verir; bu satır ETKİLEŞİMLİ koşum içindir.
    required: true
    default: "/opt/meridian/var/bots/sef"

distribution_owned:
  - SOUL.md
  - config.yaml
```

- [ ] **Adım 4: Profil yapılandırmasını yaz**

```yaml
# deploy/hermes/profiles/sef/config.yaml
# @sef profilinin güvenlik duruşu. ANA PROFİLDEN MİRAS ALINMAZ (spec §9.0'ın en önemli
# bulgusu): `hermes profile create --clone` taşır, sıfırdan/dağıtımdan kurulan profil
# KORUMASIZ doğar. Bu dosya o boşluğun kapağıdır ve tests/test_bot_profil_durusu_v329.py
# onu repo tarafında çiviler — canlıya VARMADAN.
hooks:
  pre_tool_call:
    - matcher: terminal|write_file|patch|edit|apply_patch
      command: /opt/meridian/ops/meridian-guard.sh
      timeout: 10

approvals:
  mode: smart
  # Kod varsayılanı ZATEN `deny` (tools/approval.py) — bu satır bir DELİK KAPATMAZ, bir BEYANDIR:
  # varsayılan bir gün değişirse bizim duruşumuz değişmez.
  cron_mode: deny
  deny:                      # fnmatch TÜM DİZGEYİ eşler; iki yandan sarılı olmayan desen delinir
    - "*dagit.sh*"
    - "*git push*"
    - "*git commit*"
    - "*systemctl*"
    - "*serve.sh*"

# ÖLÇÜLMÜŞ BÜTÇE — docs/OLCUM-MODEL-BUTCESI-2026-08-27.md §6, "özet/rapor" satırı.
# Super, Ultra'dan 5 kat hızlı (130,8 vs 25,8 tok/sn) ve bu çağrı bir özet/sıralamadır:
# 8.000 token ≈ 61 sn, 120 sn zaman aşımında bol pay var. Ultra bu bütçede zaman aşımına
# düşerdi — ölçümün "sert sonuç" bölümü tam bu tuzağı anlatıyor.
model: nvidia/nemotron-3-super-120b-a12b:free
max_tokens: 8000
timeout: 120
```

- [ ] **Adım 5: SOUL.md yaz**

```markdown
<!-- deploy/hermes/profiles/sef/SOUL.md -->
# @sef — dikkat bütçesi

Sen Meridian'ın şefisin. İşin ÜRETMEK değil, üretilmiş olanı OKUNUR kılmak.

Bu sistemin ölçülmüş hastalığı üretmemek değil, ürettiğini okumamaktır: 310 teslim edilmemiş
alarm ve 16 okunmamış iyileştirme önerisi biriktiği ölçüldü. Sen o yığının önünde duruyorsun.

## Sana ne verilir
Üç kaynak, hazır hesaplanmış olarak: (1) alarm yığını özeti, (2) yeni iyileştirme önerileri,
(3) haftalık öz-değerlendirmenin son hâli — bu üçüncüsü BAĞLAMDIR, kendi teslimatı ayrıdır.

## Senden ne istenir
TEK bir brifing. En çok üç kalem. Her kalem için: NE oldu · NEDEN önemli · operatör NE YAPMALI.

## Kurallar
- **Susmayı bil.** Hiçbir kalem operatörün bugün bir şey yapmasını gerektirmiyorsa, `SESSIZ` yaz
  ve dur. Bildirim spam'i dikkat bütçesini yakar; bu senin koruman gereken şeydir.
- **Sayı uydurma.** Verilmeyen bir sayıyı yazma. Ölçülmemişse "ölçülmedi" de.
- **Tekrar etme.** Hafızan var. Dün söylediğin ve değişmemiş bir şeyi yeniden yazma; değiştiyse
  NE değiştiğini yaz.
- **Sıralaman gerekçeli olsun.** "Önemli" bir gerekçe değildir. Neyin bozulduğunu ya da neyin
  kaçırıldığını söyle.
- **Karar verme, kararı GÖRÜNÜR KIL.** Emir gönderme, eşik değiştirme, dosya yazma senin işin
  değil — bunlar zaten mekanizmayla engelli.

## Biçim
Düz metin, Telegram'da okunacak. Başlık yok, madde işareti kullan, 1200 karakteri aşma.
Hiçbir şey yoksa yalnız şu tek kelime: `SESSIZ`
```

- [ ] **Adım 6: `cron_mode` şerhindeki fazla iddiayı düzelt**

`deploy/hermes/config.yaml` içindeki `cron_mode: deny` yorumu şu an "pazarlığa kapalı" diyor ve
satırın taşımadığı bir ağırlık ima ediyor. Ölçüldü: `tools/approval.py` varsayılanı ZATEN `deny`.
Şerh, satırın bir DELİK KAPATMADIĞINI ama bir BEYAN olduğunu söyleyecek şekilde yeniden yazılır.

- [ ] **Adım 7: Çivileri koş, YEŞİL gör**

Koş: `.venv/bin/python -m pytest tests/test_bot_profil_durusu_v329.py tests/test_hermes_config_durusu_v326.py -v`
Beklenen: hepsi PASS.

---

## Görev 2: `@sef`in iş akışı — birleşik brifing ve LLM'siz düşüş yolu

**Dosyalar:**
- Oluştur: `ops/sef_brifingi.py`
- Oluştur: `tests/test_sef_brifingi_v330.py`

**Arayüzler:**
- Tüketir: `ops.alarm_backlog_digest.ozet_kur()` ve `ops.oneri_brifingi.ozet_kur()` — ikisi de
  yan etkisiz, `{"mesaj": str|None, ...}` ya da `{"hata": str}` döndürür.
- Üretir: `sef_brifingi.topla() -> dict` · `sef_brifingi.sirala(ham: dict) -> tuple[str, str]`
  (metin, kaynak) burada `kaynak ∈ {"llm", "ham"}` · `main(argv) -> int`.
- Üretir: damgalama SORUMLULUĞU KAYNAKTA KALIR — `@sef` her iki kaynağın kendi `main()`ini
  ÇAĞIRMAZ, ama teslimattan sonra ikisinin damga fonksiyonlarını çağırır. İdempotens kaynak
  başına korunur.

- [ ] **Adım 1: Çiviyi yaz**

```python
# tests/test_sef_brifingi_v330.py
"""`@sef` üç kaynağı TEK brifinge indirir — ve LLM düşerse teslimat DÜŞMEZ.

EN ÖNEMLİ ÇİVİ SONUNCUSUDUR. Bir alarm teslimatını bir modele bağlamak, alarmın var oluş
sebebini iptal eder: model yavaşladığı gün alarm da susar. LLM SIRALAMA katmanıdır, TESLİMAT
katmanı değil.
"""
from __future__ import annotations

import importlib

import pytest


@pytest.fixture
def sef():
    m = importlib.import_module("ops.sef_brifingi")
    return importlib.reload(m)


def test_IKI_KAYNAK_DA_BOSSA_SESSIZ(sef, monkeypatch):
    monkeypatch.setattr(sef, "_alarm_ozeti", lambda: {"mesaj": None, "yeni": 0})
    monkeypatch.setattr(sef, "_oneri_ozeti", lambda: {"mesaj": None, "yeni": 0})
    monkeypatch.setattr(sef, "_self_review", lambda: {})
    ham = sef.topla()
    assert ham["bos"] is True, f"iki kaynak da boşken brifing kurulmamalı: {ham!r}"


def test_LLM_DUSERSE_HAM_BRIFING_YINE_GIDER(sef, monkeypatch):
    """Zaman aşımı, boş cevap, sıfırdan farklı çıkış kodu — üçü de teslimatı DÜŞÜRMEZ."""
    monkeypatch.setattr(sef, "_alarm_ozeti", lambda: {"mesaj": "5 yeni MECHANISM_STALE", "yeni": 5})
    monkeypatch.setattr(sef, "_oneri_ozeti", lambda: {"mesaj": None, "yeni": 0})
    monkeypatch.setattr(sef, "_self_review", lambda: {})

    def _patla(_prompt):
        raise TimeoutError("profil 120 sn'de cevap vermedi")

    monkeypatch.setattr(sef, "_profili_cagir", _patla)
    metin, kaynak = sef.sirala(sef.topla())
    assert kaynak == "ham", "LLM düştüğünde ham brifinge düşülmedi"
    assert "MECHANISM_STALE" in metin, f"ham brifing içeriği kaybolmuş: {metin!r}"


def test_LLM_SESSIZ_DERSE_HICBIR_SEY_GONDERILMEZ(sef, monkeypatch):
    monkeypatch.setattr(sef, "_alarm_ozeti", lambda: {"mesaj": "1 yeni MIRROR_DRIFT", "yeni": 1})
    monkeypatch.setattr(sef, "_oneri_ozeti", lambda: {"mesaj": None, "yeni": 0})
    monkeypatch.setattr(sef, "_self_review", lambda: {})
    monkeypatch.setattr(sef, "_profili_cagir", lambda _p: "SESSIZ")
    metin, kaynak = sef.sirala(sef.topla())
    assert metin is None and kaynak == "llm", (
        "`SESSIZ` hükmü teslimatı durdurmadı — dikkat bütçesi botun ASIL işidir")


def test_SELF_REVIEW_BAGLAMDIR_TESLIMATI_DEVRALMAZ(sef, monkeypatch):
    """Haftalık öz-değerlendirme `scheduler.py`de asılı ve KENDİ `notify.send`ini çağırıyor.
    `@sef` onu BAĞLAM olarak okur; kadansını devralmak çalışan bir davranışı değiştirirdi."""
    monkeypatch.setattr(sef, "_alarm_ozeti", lambda: {"mesaj": "x", "yeni": 1})
    monkeypatch.setattr(sef, "_oneri_ozeti", lambda: {"mesaj": None, "yeni": 0})
    monkeypatch.setattr(sef, "_self_review", lambda: {"week": {"ships": 0}})
    ham = sef.topla()
    assert "self_review" in ham["baglam"], "öz-değerlendirme bağlama girmedi"
    assert "self_review" not in str(ham["teslim_edilecek"]), (
        "öz-değerlendirme TESLİMAT listesine girmiş — kadansı devralınmamalı")


def test_KURU_KOSUM_VARSAYILAN_HICBIR_BAYT_YAZMAZ(sef, monkeypatch, capsys):
    gonderildi = []
    monkeypatch.setattr(sef.notify, "send", lambda *a, **k: gonderildi.append(a))
    monkeypatch.setattr(sef, "_alarm_ozeti", lambda: {"mesaj": "x", "yeni": 1})
    monkeypatch.setattr(sef, "_oneri_ozeti", lambda: {"mesaj": None, "yeni": 0})
    monkeypatch.setattr(sef, "_self_review", lambda: {})
    monkeypatch.setattr(sef, "_profili_cagir", lambda _p: "- x oldu")
    rc = sef.main([])
    assert rc == 0 and not gonderildi, "kuru koşum gönderim yaptı"
    assert "KURU" in capsys.readouterr().out.upper()
```

- [ ] **Adım 2: Çiviyi koş, KIRMIZI gör**

Koş: `.venv/bin/python -m pytest tests/test_sef_brifingi_v330.py -v`
Beklenen: `ModuleNotFoundError: No module named 'ops.sef_brifingi'`.

- [ ] **Adım 3: `ops/sef_brifingi.py` yaz**

Şekil `ops/alarm_backlog_digest.py`den BİREBİR alınır (kuru-koşum varsayılan · boşken sessiz ·
teslimden sonra damga · teslim düşerse damga BASILMAZ). Kritik parçalar:

```python
def _profili_cagir(prompt: str) -> str:
    """`sef` profilini TEK ATIŞLIK çağırır ve ham metnini döndürür.

    Profil = bağımsız HERMES_HOME dizini (hermes_cli/profiles.py). `-z` tek-atışlık prompt
    bayrağıdır. `check=True` YOK: çıkış kodunu çağıran yorumlar, çünkü LLM'in düşmesi
    teslimatı düşürmez (`sirala`nın ham dalı).
    """
    ev = dict(os.environ, HERMES_HOME=HERMES_PROFIL_HOME)
    r = subprocess.run([HERMES_BIN, "-z", prompt], capture_output=True, text=True,
                       timeout=PROFIL_TIMEOUT_S, env=ev)
    if r.returncode != 0:
        raise RuntimeError(f"profil çıkış kodu {r.returncode}: {r.stderr[-400:]}")
    return r.stdout.strip()


def sirala(ham: dict) -> tuple[str | None, str]:
    """(metin, kaynak) döndürür. kaynak: 'llm' = bot sıraladı · 'ham' = bot düştü, ham gitti.

    DÜŞÜŞ YOLU BİR KONFOR DEĞİL SÖZLEŞMEDİR: bir alarm teslimatını modele bağlamak, model
    yavaşladığı gün alarmı da susturur. Model SIRALAMA katmanıdır, TESLİMAT katmanı değil.
    """
    if ham["bos"]:
        return None, "ham"
    try:
        cevap = _profili_cagir(_prompt_kur(ham))
    except Exception as e:   # sessiz-yutma DEĞİL: aşağıda obs.log ile ADIYLA kayda geçer
        obs.log("sef_brifingi_llm_dustu", hata=repr(e)[:300])
        return _ham_metin(ham), "ham"
    if not cevap:
        obs.log("sef_brifingi_llm_bos", ham_uzunluk=len(_ham_metin(ham)))
        return _ham_metin(ham), "ham"
    if cevap.strip().upper() == "SESSIZ":
        return None, "llm"
    return cevap, "llm"
```

- [ ] **Adım 4: Çivileri koş, YEŞİL gör**

Koş: `.venv/bin/python -m pytest tests/test_sef_brifingi_v330.py tests/test_brifing_kadansi_v327.py -v`

---

## Görev 3: Kadans devri, kurulum ve F9 kaydı

**Dosyalar:**
- Değiştir: `deploy/oracle-a1/meridian-brifing.service`
- Değiştir: `deploy/oracle-a1/deploy.sh`
- Değiştir: `dagit.sh` (`F9_LISTE` + başlık)
- Değiştir: `tests/test_brifing_kadansi_v327.py`
- Değiştir: `tests/test_bot_profil_durusu_v329.py` (safe-root'un İKİNCİ yüzeyi)

- [ ] **Adım 1: İkinci yüzey çivisini yaz (kırmızı doğmalı)**

```python
def test_SAFE_ROOT_BIRIMDE_DE_BAGLANIR():
    """§9.4/3, İKİNCİ yüzey — ve ZAMANLANMIŞ koşumu BAĞLAYAN yüzey budur.

    ÖLÇÜLDÜ: `env_requires` `.env` YAZMAZ, yalnız `.env.template` üretir; `.env` kullanıcı-sahibi
    olduğu için dağıtım ona hiç dokunamaz. Yani manifest beyanı ETKİLEŞİMLİ koşumu kapsar,
    systemd'nin başlattığı koşumu KAPSAMAZ. Birim değeri vermezse bot SINIRSIZ yazar.
    """
    metin = (KOK / "deploy/oracle-a1/meridian-brifing.service").read_text(encoding="utf-8")
    satirlar = [ln.strip() for ln in metin.splitlines()
                if ln.strip().startswith("Environment=") and "HERMES_WRITE_SAFE_ROOT" in ln]
    assert satirlar, (
        "birim `HERMES_WRITE_SAFE_ROOT` vermiyor — zamanlanmış koşumda bot SINIRSIZ yazar "
        "(agent/file_safety.py: değişken tanımsızsa hiçbir kısıt uygulanmaz)")
    assert all("/bots/sef" in ln for ln in satirlar), \
        f"safe-root botun kendi dizini değil: {satirlar}"
```

- [ ] **Adım 2: Birimi güncelle**

ExecStart iki betiği çağıran sarmalayıcıdan `sef_brifingi.py --uygula`ya geçer. SARMALAYICININ
İKİ ŞARTI KORUNUR (ilk düşse ikincisi koşar · herhangi biri düşerse birim `failed`) — artık tek
betik var, yani `-` öneksiz düz `ExecStart` yeter ve bu SADELEŞMEDİR, gevşeme değil.
`Environment=HERMES_WRITE_SAFE_ROOT=/opt/meridian/var/bots/sef` eklenir; `ReadWritePaths`e
o dizin `/opt/meridian` altında olduğu için EK SATIR GEREKMEZ (ölçülerek yazılır, varsayılmaz).

- [ ] **Adım 3: `deploy.sh` profil dizinini kurar, profili KURMAZ**

`deploy/hermes/profiles/` rsync ile zaten canlıya gidiyor (dagit dışlama listesinde yok — koşumdan
ÖNCE `grep` ile doğrula). Betik yalnız `var/bots/sef` dizinini yaratır ve operatöre TEK komutu
basar. `hermes profile install` ÇALIŞTIRILMAZ: profil yaratmak canlıda yeni bir ajan kimliği
doğurur.

- [ ] **Adım 4: `F9_LISTE`ye üç profil dosyası**

```
deploy/hermes/profiles/sef/distribution.yaml|/home/ubuntu/.hermes/profiles/sef/distribution.yaml
deploy/hermes/profiles/sef/config.yaml|/home/ubuntu/.hermes/profiles/sef/config.yaml
deploy/hermes/profiles/sef/SOUL.md|/home/ubuntu/.hermes/profiles/sef/SOUL.md
```

`test_f9_LISTESININ_TAMAMI_deploy_sh_BASLIGINDA_ADLANDIRILIR` bu üç adı `deploy.sh` başlığında
da ZORUNLU kılar — çivi kendiliğinden kırmızı doğar, başlık güncellenerek yeşile alınır.

- [ ] **Adım 5: Kapsam koşumu**

Koş: `.venv/bin/python -m pytest tests/test_sef_brifingi_v330.py tests/test_bot_profil_durusu_v329.py tests/test_brifing_kadansi_v327.py tests/test_dagit_f9_beyan_v266.py tests/test_h3_tur2_v174.py tests/test_kucuk_kuyruk_v179.py -v`

- [ ] **Adım 6: RUNBOOK'u yeniden üret** (`deploy.sh` ve `dagit.sh` başlıkları değişti)

Koş: `.venv/bin/python ops/runbook_uret.py`

---

## Bu planın KAPSAMADIKLARI — açıkça

1. **Canlıda profil yaratmak / birimi etkinleştirmek.** Operatöre iki komut kalır ve ikisi de
   `deploy.sh` çıktısında basılır.
2. **Konuşan bot.** Spec §7 bu soruyu açıkça Faz 2'ye erteledi ve İKİNCİ bir Telegram bot
   token'ı gerektiriyor (aynı token'a iki dinleyici çakışır). Token bir sırdır.
3. **Kalan altı rol.** Spec §3: *"Faz 3 — kalan roster, her biri kanıtlandıkça."* İş akışı
   kanıtlanmamış altı SOUL.md yazmak YASA 6'nın (okuyucusuz yazım yok) ihlalidir.
4. **`selfreview.weekly()` kadansını devralmak.** Çalışan, dağıtılmış davranış; `@sef` onu
   BAĞLAM olarak okur.
