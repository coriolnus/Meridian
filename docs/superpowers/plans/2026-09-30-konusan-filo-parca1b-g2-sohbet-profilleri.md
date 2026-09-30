# Konuşan bot filosu — Parça 1b G2: sohbet profilleri üreteci — Uygulama Planı

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `ops/sohbet_profili_uret.py` her `aktif` bot için rapor profilinden (`deploy/hermes/profiles/<ad>/`) bir SOHBET profili TÜRETİR ve `deploy/hermes/sohbet/profiles/<ad>/` altına yazar; `--kontrol` kipi üretilmiş ≡ depo ayrışmasını yakalar; duruş (guard kancası, onay, kapalı takımlar) rapor profilinden miras alınır ve çivilenir.

**Architecture:** Rapor profili DEĞİŞMEZ ve hafızasız kalır (Parça 0 v3: `-z` yolu hafızaya YAZABİLİYOR → ikiz zorunlu). Sohbet profilleri AYRI bir Hermes kökünde yaşayacak: A1 ölçümü 2026-09-30 07:1xZ (Hermes v0.19.0 `hermes_constants.get_default_hermes_root` + `hermes_cli.profiles.profiles_to_serve`) — `HERMES_HOME` `~/.hermes` DIŞINI gösterirse O dizin köktür, profiller `<kök>/profiles/` altındadır ve `gateway.multiplex_profiles: true` kökün varsayılan profilini + `profiles/` altındaki HER geçerli profili `/p/<ad>/` önekiyle sunar; her turun sırları o profilin `.env`inden kurulan kapsamla okunur (`gateway/run.py::_profile_runtime_scope`). Yani bot ağ geçidi (G3) canlı varsayılan profili (`~/.hermes`) ve rapor profillerini GÖRMEZ. Depodaki karşılık: `deploy/hermes/sohbet/profiles/<ad>/` (G3 kökün kendi `config.yaml`ını `deploy/hermes/sohbet/config.yaml` olarak ekler). Bu dizin `deploy/hermes/profiles/` DIŞINDADIR, çünkü v329'un profil çivileri "bir profil = bir systemd birimi + harness" varsayar (sessizlik sınıfı harness'ten ölçülür) ve sohbet profilinin birimi çoklu ağ geçididir; sohbet profillerinin duruşu v599 ile, v329'un aynı yasak listesi İTHAL edilerek çivilenir.

**Tech Stack:** Python 3 stdlib + PyYAML (depoda var); `meridian.kadro` (`aktif_botlar`, `Bot.araclar`, `Bot.hafiza`); `tests/test_bot_profil_durusu_v329.py::YASAK_TAKIMLAR`.

**Spec:** `docs/superpowers/specs/2026-09-29-konusan-bot-filosu-design.md` §3.3–§3.4 · Parça 0 raporu (v3 notu) · taslak `docs/superpowers/plans/2026-09-30-konusan-filo-parca1b-taslak.md` G2.

## Global Constraints
- Rapor profili dosyalarına (`deploy/hermes/profiles/**`) YAZILMAZ; üreteç yalnız `deploy/hermes/sohbet/profiles/**` yazar.
- Tek kaynak: duruş anahtarları (`hooks`, `hooks_auto_accept`, `approvals`, `agent.disabled_toolsets`, `model`, `providers.kapi`) rapor profilinin `config.yaml`ından OKUNUR; Meridian MCP girdisi (`command`, `args`, `env`, `tools`) `deploy/hermes/config.yaml` `mcp_servers.meridian`dan OKUNUR (`enabled` → `true`, `args` + `["--bot", ad]`). Sohbet sabitleri (zaman aşımı, yeniden deneme, Hindsight ayarları, SOUL bölümü) üretecin modül sabitleridir — başka yerde yazılmaz.
- Üretilmiş her dosyanın başında (YAML/MD yorum; JSON'da `_uretildi` alanı) "ÜRETİLMİŞ — elle düzenlenmez; üreteç `ops/sohbet_profili_uret.py`" beyanı.
- Sır dosyaya YAZILMAZ: `hindsight/config.json`da `api_key` alanı YOK (değer G3'te `HINDSIGHT_API_KEY` ortamından); profil `.env` üretilmez.
- Çıktı deterministiktir (iki koşum bayt-özdeş; sözlük sırası sabit, zaman damgası YOK).
- Üreteç `meridian.obs`'a ULAŞMAZ (pytest-dışı koşumu canlı yerel deftere yazmasın); yalnız dosya üretir, stdout'a özet basar.
- Zaman aşımı Hermes'in OKUDUĞU yerde: `providers.custom.request_timeout_seconds` (+ geri dönüş evi `providers.openrouter.request_timeout_seconds`) — kökte `timeout` YOK (v329 emsali). Değer `SOHBET_ISTEK_ZAMAN_ASIMI_SN = 60`, `agent.api_max_retries = SOHBET_API_DENEME = 2` (Hermes v0.19 `agent/agent_init.py` varsayılanı 3; Parça 0 v3'te ücretsiz model çağrı başına ~5 dk asıldı ≈ 3 deneme × 120 s; 2 × 60 s en kötü ~2 dk — G4 Telegram ara bildirimi bu süreyi karşılar).
- Test numarası v599 (v598 TSK-214 brief'ine ayrıldı). Test adlarında FAILED/ERROR yok; yorumlarda `dosya.py:NNN` yok; Yasa 4/6.
- SOUL'a eklenen bölümde ev-dizini yolu yok (v266) ve yeni BÜYÜK HARF jetonu yok (v593 `SEMBOL_DISI` sözleşmesi; `SESSIZ` zaten var).

## Review Focus
1. Rapor profilinde duruş değişirse (ör. yeni kapalı takım) sohbet profili bayat kalır → `--kontrol` ≠ 0 olmalı (v599 çivisi + dağıtım öncesi kapı G6'da).
2. Kadroda `aktif`ten çıkan bot → sohbet profili "fazla" raporlanmalı (üreteç SİLMEZ; `--kontrol` ≠ 0 + ad).
3. SOUL bölümü botun kadroda OLMAYAN aracını vaat ederse (ör. `oneri_yaz` yokken "öneri yaz") model yeteneği uydurur → satır yalnız araç kadrodaysa.
4. Alarm sınıfı SOUL'un (bekçi) tek başına `SESSIZ` şablon satırı sohbette de uygulanırsa bot soruya "SESSIZ" der → sohbet bölümü bunu açıkça geçersiz kılar (cümle içinde, tek başına satır YOK).
5. `platform_toolsets` geçersiz/eksik ad Hermes'te sessizce varsayılan takıma düşebilir → tam eşitlik `{"api_server": ["meridian"]}` çivisi.

---

### Task 1: Üreteç + üretilmiş üç profil + v599

**Files:** Create `ops/sohbet_profili_uret.py`, `deploy/hermes/sohbet/profiles/{sef,bekci,karne}/{SOUL.md,config.yaml,distribution.yaml,hindsight/config.json}` (ÜRETİLİR, elle yazılmaz), `tests/test_sohbet_profili_uret_v599.py`

**Interfaces:**
- Consumes: `meridian.kadro.aktif_botlar(kadro: tuple[Bot, ...] | None = None) -> tuple[Bot, ...]`, `kadro.kadro_yukle(yol)`, `Bot.ad`, `Bot.araclar`, `Bot.hafiza` (`Bot` donuk dataclass; `DURUMLAR = ("aktif", "sirada", "kilitli")`). `kadro=None` iken üreteç kadroyu `kok / "deploy/hermes/kadro.yaml"`dan okur (tmp kökte test edilebilsin).
- Produces: `uret(kok: Path = REPO, kadro=None) -> dict[str, bytes]` (göreli yol → içerik; YAZMAZ) · `yaz(kok: Path = REPO, kadro=None) -> list[str]` (yazılan göreli yollar) · `kontrol(kok: Path = REPO, kadro=None) -> list[str]` (ayrışan/eksik/fazla dosya açıklamaları; boş = güncel) · `main(argv) -> int` (`--yaz` → 0; `--kontrol` → 0 güncel / 1 bayat, ayrışanlar stdout'a; ikisi birden ya da hiçbiri → 2) · sabitler `SOHBET_ISTEK_ZAMAN_ASIMI_SN`, `SOHBET_API_DENEME`, `SOHBET_KOK = "deploy/hermes/sohbet/profiles"`, `SOHBET_BOLUMU_BASLIGI = "## Sohbet kipi"`.

**Üretim kuralları (profil başına, `ad` = kadro adı, rapor evi `R = deploy/hermes/profiles/<ad>`):**
- `config.yaml` = `yaml.safe_load(R/config.yaml)` üzerine: `mcp_servers = {"meridian": {**kök_meridian_girdisi, "enabled": True, "args": kök_args + ["--bot", ad]}}` · `platform_toolsets = {"api_server": ["meridian"]}` · `memory = {"provider": "hindsight"}` · `agent.api_max_retries = SOHBET_API_DENEME` · `providers.custom.request_timeout_seconds` ve `providers.openrouter.request_timeout_seconds` = `SOHBET_ISTEK_ZAMAN_ASIMI_SN`. Diğer her anahtar AYNEN (duruş mirası). Yazım `yaml.safe_dump(..., allow_unicode=True, sort_keys=False)` + başlık yorumu.
- `hindsight/config.json` = `{"_uretildi": "...", "mode": "local_external", "api_url": "http://127.0.0.1:8888", "bank_id": f"bot-{ad}", "recall_budget": "low", "memory_mode": "context", "auto_recall": true, "auto_retain": true, "retain_tags": f"bot:{ad},kaynak:sohbet", "retain_source": ad, "retain_async": false, "timeout": 10}` (Parça 0 v3'te ölçülerek çalışan anahtar kümesi; `memory_mode: context` → modele hafıza ARACI açılmaz).
- `SOUL.md` = `R/SOUL.md` metni (rstrip) + `"\n\n"` + sohbet bölümü. Bölüm metni (sabit; `{…}` satırları koşullu):
  ```
  ## Sohbet kipi

  Bu bölüm yukarıdaki rapor talimatlarından önce gelir. Burada zamanlanmış bir rapor yazmıyorsun: operatörün sorusuna cevap veriyorsun.

  - Bugünün durumu hakkında yalnız araçlarından gelen veriyle konuş. Araç çağırmadan hiçbir sayı, yüzde, sembol ya da kaynak yazma.
  - Aracın yoksa ya da araç cevap vermediyse bilmediğini söyle ve nedenini yaz. Araç sonucu uydurma; çağırmadığın bir aracın adını anma.
  - Geçmiş konuşmalarından notlar bağlam olarak gelebilir. Oradan aktardığın her şeyin tarihini ver ve onu bugün için hüküm sayma.
  - Ayar değiştiremez, komut çalıştıramazsın.
  {oneri_yaz ∈ araclar} - Bir değişiklik gerekiyorsa oneri_yaz aracıyla öneri yaz; onayı operatör verir.
  {is_iste ∈ araclar} - Bir raporun yeniden üretilmesi gerekiyorsa is_iste aracıyla iste; işi Meridian koşar.
  {bot_hafizasi_ara ∈ araclar ve hafiza == "hepsi"} - Başka bir botun geçmiş konuşmalarına bot_hafizasi_ara aracıyla bakabilirsin; oradan aktardığın her şeyin hangi bota ve hangi tarihe ait olduğunu yaz.
  - Bu kipte SESSIZ yazmazsın: her soruya cevap verirsin.
  - Kısa yaz; birkaç paragrafı geçme.
  ```
- `distribution.yaml` = `{name: ad, version: "0.1.0", description: "<ad> sohbet profili — ÜRETİLMİŞ (rapor profilinden türetildi)", hermes_requires: <R manifestindeki değer>, env_requires: [R manifestinin `BOT_KEY_<AD>` girdisi AYNEN, {name: HINDSIGHT_API_KEY, required: true, description: "Hindsight kiracı anahtarı; değer G3 biriminin credential'ından, dosyaya yazılmaz"}], distribution_owned: [SOUL.md, config.yaml, hindsight/config.json]}`.

- [ ] **Step 1: Başarısız testler** (`tests/test_sohbet_profili_uret_v599.py`; üreteç `importlib` ile `ops/` yolundan yüklenir — depodaki ops testlerinin emsaline bak: `grep -l "spec_from_file_location" tests/test_*uret*.py`):

```python
import json, pathlib, subprocess, sys, yaml, pytest
KOK = pathlib.Path(__file__).resolve().parent.parent
from tests.test_bot_profil_durusu_v329 import YASAK_TAKIMLAR

def _ur():
    import importlib.util
    s = importlib.util.spec_from_file_location("sohbet_profili_uret", KOK / "ops/sohbet_profili_uret.py")
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m

def _aktifler():
    from meridian import kadro
    return list(kadro.aktif_botlar())

def _cfg(ad):  return yaml.safe_load((KOK / f"deploy/hermes/sohbet/profiles/{ad}/config.yaml").read_text(encoding="utf-8"))
def _rap(ad):  return yaml.safe_load((KOK / f"deploy/hermes/profiles/{ad}/config.yaml").read_text(encoding="utf-8"))

def test_depo_guncel_kontrol_bos():
    assert _ur().kontrol() == []

def test_komut_satiri_kontrol_sifir_doner():
    r = subprocess.run([sys.executable, "ops/sohbet_profili_uret.py", "--kontrol"], cwd=KOK, capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr

def test_bayat_dosya_yakalanir(tmp_path):
    import shutil
    shutil.copytree(KOK / "deploy", tmp_path / "deploy")
    hedef = tmp_path / "deploy/hermes/sohbet/profiles/bekci/config.yaml"
    hedef.write_text(hedef.read_text(encoding="utf-8") + "\n# el ile\n", encoding="utf-8")
    ayrisan = _ur().kontrol(kok=tmp_path)
    assert any("bekci/config.yaml" in a for a in ayrisan)

def test_uretim_deterministik():
    u = _ur(); assert u.uret() == u.uret()

@pytest.mark.parametrize("bot", _aktifler(), ids=lambda b: b.ad)
def test_durus_rapor_profilinden_miras(bot):
    c, r = _cfg(bot.ad), _rap(bot.ad)
    for anahtar in ("hooks", "hooks_auto_accept", "approvals", "model"):
        assert c.get(anahtar) == r.get(anahtar), anahtar
    assert c["agent"]["disabled_toolsets"] == r["agent"]["disabled_toolsets"]
    assert set(YASAK_TAKIMLAR) <= set(c["agent"]["disabled_toolsets"])
    assert c["providers"]["kapi"] == r["providers"]["kapi"]

@pytest.mark.parametrize("bot", _aktifler(), ids=lambda b: b.ad)
def test_platform_izin_listesi_yalniz_meridian(bot):
    assert _cfg(bot.ad)["platform_toolsets"] == {"api_server": ["meridian"]}

@pytest.mark.parametrize("bot", _aktifler(), ids=lambda b: b.ad)
def test_mcp_girdisi_tek_kaynaktan_ve_bot_argumani(bot):
    kok = yaml.safe_load((KOK / "deploy/hermes/config.yaml").read_text(encoding="utf-8"))["mcp_servers"]["meridian"]
    m = _cfg(bot.ad)["mcp_servers"]["meridian"]
    assert m["enabled"] is True and m["args"] == kok["args"] + ["--bot", bot.ad]
    for a in ("command", "env", "tools"):
        assert m[a] == kok[a]

@pytest.mark.parametrize("bot", _aktifler(), ids=lambda b: b.ad)
def test_hafiza_saglayicisi_banka_ve_sirsiz(bot):
    assert _cfg(bot.ad)["memory"] == {"provider": "hindsight"}
    h = json.loads((KOK / f"deploy/hermes/sohbet/profiles/{bot.ad}/hindsight/config.json").read_text(encoding="utf-8"))
    assert h["bank_id"] == f"bot-{bot.ad}" and h["memory_mode"] == "context" and h["mode"] == "local_external"
    assert "api_key" not in h

@pytest.mark.parametrize("bot", _aktifler(), ids=lambda b: b.ad)
def test_zaman_asimi_hermesin_okudugu_yerde(bot):
    u, c = _ur(), _cfg(bot.ad)
    assert c["providers"]["custom"]["request_timeout_seconds"] == u.SOHBET_ISTEK_ZAMAN_ASIMI_SN
    assert c["agent"]["api_max_retries"] == u.SOHBET_API_DENEME and "timeout" not in c

@pytest.mark.parametrize("bot", _aktifler(), ids=lambda b: b.ad)
def test_soul_rapor_soulu_ile_baslar_bolum_tek(bot):
    s = (KOK / f"deploy/hermes/sohbet/profiles/{bot.ad}/SOUL.md").read_text(encoding="utf-8")
    r = (KOK / f"deploy/hermes/profiles/{bot.ad}/SOUL.md").read_text(encoding="utf-8").rstrip()
    assert s.startswith(r) and s.count("## Sohbet kipi") == 1
    bolum = s.split("## Sohbet kipi", 1)[1]
    assert not [ln for ln in bolum.splitlines() if ln.strip() == "SESSIZ"]

@pytest.mark.parametrize("bot", _aktifler(), ids=lambda b: b.ad)
def test_soul_yalniz_kadrodaki_araci_vaat_eder(bot):
    bolum = (KOK / f"deploy/hermes/sohbet/profiles/{bot.ad}/SOUL.md").read_text(encoding="utf-8").split("## Sohbet kipi", 1)[1]
    for arac in ("oneri_yaz", "is_iste", "bot_hafizasi_ara"):
        beklenen = arac in bot.araclar and (arac != "bot_hafizasi_ara" or bot.hafiza == "hepsi")
        assert (arac in bolum) is beklenen, arac

def test_aktif_olmayan_bot_icin_profil_yok_ve_fazla_raporlanir(tmp_path):
    import shutil, dataclasses
    shutil.copytree(KOK / "deploy", tmp_path / "deploy")
    from meridian import kadro
    kd = tuple(dataclasses.replace(b, durum="sirada") if b.ad == "karne" else b for b in kadro.kadro_yukle())
    u = _ur()
    assert not any("/karne/" in y for y in u.uret(kok=tmp_path, kadro=kd))
    assert any("karne" in a and "fazla" in a for a in u.kontrol(kok=tmp_path, kadro=kd))

def test_rapor_profillerine_dokunulmaz(tmp_path):
    import shutil, hashlib
    shutil.copytree(KOK / "deploy", tmp_path / "deploy")
    iz = lambda: {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in (tmp_path / "deploy/hermes/profiles").rglob("*") if p.is_file()}
    once = iz(); _ur().yaz(kok=tmp_path); assert iz() == once
```
(`sirada` = `DURUMLAR`ın aktif olmayan değeri; `aktif_botlar` bu satırı düşürür.)

- [ ] **Step 2: Kırmızı** — `.venv/bin/python -m pytest tests/test_sohbet_profili_uret_v599.py -p no:cacheprovider` (üreteç yok → toplama/ithal hatası; beklenen).
- [ ] **Step 3: Uygula** — üreteci yaz; `python ops/sohbet_profili_uret.py --yaz` ile üç profili ÜRET (bu koşum `meridian.obs`'a ulaşmaz — Global Constraints; ulaşıyorsa DUR ve raporla). Üretilmiş dosyaları elle düzeltme; hata üreteçte düzeltilir ve yeniden üretilir.
- [ ] **Step 4: Yeşil** — aynı komut; üçlü hüküm.
- [ ] **Step 5: Mutasyon** (her biri yedekten geri alınır, sha256 kıyası): `--bot` ekini kaldır → `test_mcp_girdisi…` kırmızı · `hooks` kopyasını atla → `test_durus…` kırmızı · `bank_id` `bot-` öneksiz → `test_hafiza…` kırmızı · `oneri_yaz` satırını koşulsuz yaz → `test_soul_yalniz…` kırmızı · `--kontrol` fazla profili saymasın → `test_aktif_olmayan…` kırmızı · zaman aşımını kökte `timeout` olarak yaz → `test_zaman_asimi…` kırmızı · `api_key` alanını JSON'a ekle → `test_hafiza…` kırmızı.
- [ ] **Step 6: Kapsam** (seri, üçlü hüküm): v599 + v329 + v266 (`test_dagit_f9_beyan_v266.py`, SOUL ev-dizini taraması `deploy/hermes/**/SOUL.md`yi kapsar) + v593 (SOUL büyük harf jetonları) + v591 + v326 + v571 + v572 + codelaw + v334 + v382.

---

## Sonra (G3'e devreden açık ölçümler — bu planın kapsamı DIŞI)
- Bot kökü `~/.hermes-botlar` (A1) + `deploy/hermes/sohbet/config.yaml` (varsayılan profil: `gateway.multiplex_profiles: true`, api_server 127.0.0.1:8642, hiçbir araç takımı yok) + profillerin köke kurulumu (`hermes profile install` mı A0 kopya görevi mi — ölçülür).
- **ÖLÇÜLEMEDİ (2026-09-30 07:2xZ, sınıflandırıcı engeli — operatör ya da ayrı onay):** (a) çoklu kipte `API_SERVER_KEY`/`HINDSIGHT_API_KEY` gibi "global" sırların `os.environ`dan okunup okunmadığı (`agent/secret_scope.py` `_is_global_env`) — LoadCredential → ortam yolunun işleyip işlemediği buna bağlı; (b) `request_dump_*.json` yazımının koşulu (`agent/agent_runtime_helpers.py`) — kapatılabilir mi, yoksa dizin izni/temizliğiyle mi sınırlanır.
- Birim: `TimeoutStopSec` + `KillMode=mixed` (v3: ağ geçidi SIGTERM'i yok saydı), `ReadWritePaths` ⊇ `state/approvals.jsonl`, `state/.locks`, `state/events.jsonl` (G1 Task 1 raporu), `/opt/meridian/var/bots/<ad>`.
