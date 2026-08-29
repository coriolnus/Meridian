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
    assert mod == "deny", (
        f"{profil.name}: approvals.cron_mode = {mod!r} — `deny` olmalı. Başka her değerde "
        "başsız (TTY'siz) cron oturumu tehlikeli bir komutu KENDİ ONAYLAR: onay isteyecek "
        "kimse yoktur, yani 'sor' pratikte 'geç' demektir")


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
    assert str(man.get("name")) == profil.name, (
        f"manifest `name: {man.get('name')!r}` ile dizin adı {profil.name!r} ayrışıyor — "
        "`hermes profile install` profili MANİFESTTEKİ adla kurar, yani canlıda dizinden "
        "başka adlı bir profil doğar ve `HERMES_HOME` onu bulamaz")


# ---------------------------------------------------------------------------
# DÜZELTME DALGASI (2026-08-29) — inceleme sonrası eklenen çiviler.
#
# Hepsinin ortak dersi: bir duruşu YAZMAK onu YÜRÜRLÜĞE KOYMAZ. Aşağıdakilerin
# dördü, config'te doğru görünen ama Hermes'in HİÇ OKUMADIĞI ya da başsız koşumda
# SESSİZCE DÜŞEN anahtarları yakalar. Ölçümler YEREL Hermes v0.18.2 kaynağında
# yapıldı (canlı v0.19.0 — sürüm farkı beyan edilir, gizlenmez).
# ---------------------------------------------------------------------------

MODEL_ANAHTARI = "nvidia/nemotron-3-super-120b-a12b:free"

# Botun ELİNDEN ALINAN araç takımları. İnceleme dört geri-alınamaz sınıf ölçtü ve
# dördü de ARAÇ ister: silme + süreç öldürme (terminal), kimlik okuyup dışarı taşıma
# (file + terminal + web), kendi guard'ını/config'ini üstüne yazma (file).
YASAK_TAKIMLAR = ["terminal", "file", "code_execution", "browser", "web"]


@pytest.mark.parametrize("profil", _profiller(), ids=lambda p: p.name)
def test_MODEL_BLOGU_ESLEME_ve_max_tokens_ICINDE(profil):
    """ÖLÇÜLDÜ (`agent/agent_init.py`, v0.18.2): `max_tokens` MODEL EŞLEMESİNİN İÇİNDEN
    okunur (`_model_cfg.get("max_tokens")`) ve okuma `isinstance(_model_cfg, dict)`
    kapısının ARDINDADIR. Yani `model:` düz bir dize olursa bütçe SESSİZCE YOK SAYILIR:
    dosya 8.000 der, koşum modelin kendi varsayılanını kullanır ve kimse fark etmez.
    """
    cfg = yaml.safe_load((profil / "config.yaml").read_text(encoding="utf-8")) or {}
    model = cfg.get("model")
    assert isinstance(model, dict), (
        f"{profil.name}: `model` düz dize — bu biçimde `max_tokens` HİÇ OKUNMAZ, "
        f"bütçe beyanı sessizce ölü kalır (bulunan: {model!r})")
    assert model.get("provider"), f"{profil.name}: `model.provider` yok — sağlayıcı seçilemez"
    assert model.get("default"), f"{profil.name}: `model.default` yok — model seçilemez"
    assert isinstance(model.get("max_tokens"), int), (
        f"{profil.name}: `max_tokens` model eşlemesinin İÇİNDE ve tamsayı olmalı — "
        f"kökte duran bir kopya okunmaz (bulunan: {model.get('max_tokens')!r})")


@pytest.mark.parametrize("profil", _profiller(), ids=lambda p: p.name)
def test_TIMEOUT_HERMESIN_OKUDUGU_YERDE(profil):
    """ÖLÇÜLDÜ (`hermes_cli/timeouts.py::get_provider_request_timeout`): istek zaman aşımı
    NE kökten NE model eşlemesinden okunur. Okuma sırası
    `providers.<saglayici>.models.<model>.timeout_seconds` → `providers.<saglayici>.
    request_timeout_seconds`. Kökteki bir `timeout:` anahtarı hiçbir şey yapmaz; onu
    yazmak, olmayan bir korumaya güvenmektir.
    """
    cfg = yaml.safe_load((profil / "config.yaml").read_text(encoding="utf-8")) or {}
    assert "timeout" not in cfg, (
        f"{profil.name}: kökte `timeout` var — Hermes burayı OKUMAZ, anahtar ölü yatar")
    saglayici = ((cfg.get("model") or {}).get("provider"))
    p_cfg = ((cfg.get("providers") or {}).get(saglayici) or {})
    model_ust = ((p_cfg.get("models") or {}).get(MODEL_ANAHTARI) or {})
    deger = model_ust.get("timeout_seconds") or p_cfg.get("request_timeout_seconds")
    assert isinstance(deger, (int, float)) and deger > 0, (
        f"{profil.name}: `providers.{saglayici}` altında zaman aşımı yok — model asılırsa "
        f"koşum sağlayıcı varsayılanında bekler (bulunan: {deger!r})")


@pytest.mark.parametrize("profil", _profiller(), ids=lambda p: p.name)
def test_BASSIZ_KOSUM_ONAY_ANAHTARI_ACIK(profil):
    """§9.4/1'İN EKSİK YARISI — kancanın kaydolmasının GEREK ŞARTI (yeter şartı DEĞİL).

    ADI DEĞİŞTİ (denetim 2026-08-30). Eski ad `…GERCEKTEN_KAYDOLUR` idi ve bu bir söz veriyordu:
    çivi kaydın GERÇEKLEŞTİĞİNİ ölçmüyor, YALNIZ bir config anahtarının `true` olduğunu ölçüyor.
    Kayıt ÜÇ şarta birden bağlı ve çivi yalnız birini görüyor:
      (1) `hooks_auto_accept: true` — BURADA ölçülen (ya da `--accept-hooks` bayrağı; çağrı
          tarafındaki yarısı `test_CAGRI_ACCEPT_HOOKS_TASIR`ta),
      (2) `_prepare_agent_startup`in `_AGENT_COMMANDS` kapısından geçmek — `-z` bugün geçiyor
          (ÖLÇÜLDÜ, yerel Hermes v0.18.2 kaynağı; canlı v0.19.0, sürüm farkı beyan edilir),
      (3) kancanın canlıda GERÇEKTEN ateşlenmesi — CANLIDA HİÇ ÖLÇÜLMEDİ; `deploy.sh` bunu
          operatöre "DOĞRULANMADI (1)" diye ADIYLA basıyor.
    Adı taşıyabildiği kadarını taşıyan bir çivi, taşıyamadığını iddia eden bir çividen iyidir.

    ÖLÇÜLDÜ (satıcının KENDİ testi `test_no_tty_no_flag_skips_registration`,
    `tests/agent/test_shell_hooks_consent.py`): TTY YOKKEN ve onay kanallarının HİÇBİRİ
    açık değilken `register_from_config(...)` `[]` döndürür — kanca SESSİZCE KAYDOLMAZ.
    Varsayılan da kapalı (`hermes_cli/config.py`, `hooks_auto_accept: False`).
    """
    cfg = yaml.safe_load((profil / "config.yaml").read_text(encoding="utf-8")) or {}
    assert cfg.get("hooks_auto_accept") is True, (
        f"{profil.name}: `hooks_auto_accept: true` YOK — başsız koşumda guard kancası "
        "SESSİZCE kaydolmaz ve profil korumasız koşar")


@pytest.mark.parametrize("profil", _profiller(), ids=lambda p: p.name)
def test_GUARD_KANCASI_DOGRU_ARACLARA_BAGLI(profil):
    """Çivi 1 yalnız `command` dizesine bakarsa, `matcher: sadece_okuma` yazan bir profil
    YEŞİL geçer ve kanca hiç ateşlenmez. Kancanın kapsadığı araç adları da ölçülür."""
    cfg = yaml.safe_load((profil / "config.yaml").read_text(encoding="utf-8")) or {}
    kancalar = ((cfg.get("hooks") or {}).get("pre_tool_call")) or []
    guard = [k for k in kancalar if isinstance(k, dict)
             and str(k.get("command", "")).endswith("meridian-guard.sh")]
    assert guard, f"{profil.name}: `meridian-guard.sh` KOMUT OLARAK çağrılmıyor"
    matcher = str(guard[0].get("matcher") or "")
    eksik = [a for a in ("terminal", "write_file", "patch", "edit", "apply_patch")
             if a not in matcher]
    assert not eksik, (
        f"{profil.name}: guard matcher'ı şu araçları KAPSAMIYOR: {eksik} — kanca yazılı "
        f"ama o araçlar çağrıldığında ateşlenmez (matcher: {matcher!r})")


@pytest.mark.parametrize("profil", _profiller(), ids=lambda p: p.name)
def test_TEHLIKELI_ARAC_TAKIMLARI_KAPALI(profil):
    """SAVUNMANIN EN YÜKSEK KALDIRAÇLI KATMANI: deny listesi bir KABUĞU polislemeye
    çalışır; bu satır kabuğu HİÇ VERMEZ. `@sef` girdilerini hazır hesaplanmış alır ve
    yalnız metin üretir — araca ihtiyacı yoktur.

    ÖLÇÜLDÜ (`hermes_cli/tools_config.py`): `agent.disabled_toolsets` çözümlemenin EN
    SONUNDA uygulanır ve üstündeki her şeyi geçersiz kılar. Deny listesi KALIR (derinlemesine
    savunma); araçları daraltmak yasakları gevşetme ruhsatı değildir.

    BU ÇİVİNİN ÖLÇMEDİĞİ ŞEY, ADIYLA (denetim 2026-08-30): burada YALNIZ beş dizgenin YAML
    listesinde DURDUĞU ölçülür. Adların GERÇEK toolset anahtarı olup olmadığını ölçmez — bir
    yazım hatası (`termial`) ya da üst akım yeniden adlandırması takımı sessizce geri açar ve bu
    çivi adını taşıdığı arızanın İÇİNDEN yeşil geçer. O yarıyı kardeş çivi
    `test_KAPALI_TAKIM_ADLARI_GERCEK_TOOLSET_ANAHTARIDIR` ölçer — ve o çivi Hermes KAYNAĞINA
    ulaşamadığı makinede ATLANIR, sessizce geçmez.
    """
    cfg = yaml.safe_load((profil / "config.yaml").read_text(encoding="utf-8")) or {}
    kapali = [str(t) for t in ((cfg.get("agent") or {}).get("disabled_toolsets") or [])]
    eksik = [t for t in YASAK_TAKIMLAR if t not in kapali]
    assert not eksik, (
        f"{profil.name}: şu araç takımları KAPATILMAMIŞ: {eksik} — bot silme, kimlik "
        f"okuyup dışarı taşıma ve kendi guard'ını üstüne yazma yeteneğini korur "
        f"(mevcut: {kapali})")


def _hermes_toolset_anahtarlari() -> tuple[set[str] | None, str]:
    """`(anahtar kümesi, kaynak açıklaması)`. Küme `None` = KAYNAĞA ULAŞILAMADI (uydurma yasağı).

    Hermes bu deponun `.venv`ine KURULU DEĞİL (ölçüldü: `importlib.util.find_spec("hermes_cli")`
    `None`), o yüzden anahtar kümesi ithal edilerek okunamaz. Kalan tek dürüst yol KAYNAK
    AĞACINI bulup `CONFIGURABLE_TOOLSETS` literalini AST ile okumaktır. Bulunamazsa `None`
    döner ve çağıran ATLAR — "bulamadım" ile "hepsi geçerli" aynı şey değildir.
    """
    import ast
    import os as _os
    adaylar = []
    if _os.environ.get("HERMES_SRC"):
        adaylar.append(pathlib.Path(_os.environ["HERMES_SRC"]))
    adaylar.append(pathlib.Path.home() / ".hermes" / "hermes-agent")
    for kok in adaylar:
        dosya = kok / "hermes_cli" / "tools_config.py"
        if not dosya.is_file():
            continue
        try:
            agac = ast.parse(dosya.read_text(encoding="utf-8"))
        except Exception as e:
            return None, f"{dosya} ayrıştırılamadı: {e!r}"
        for dugum in agac.body:
            if not isinstance(dugum, ast.Assign):
                continue
            if not any(isinstance(h, ast.Name) and h.id == "CONFIGURABLE_TOOLSETS"
                       for h in dugum.targets):
                continue
            try:
                kayitlar = ast.literal_eval(dugum.value)
            except Exception as e:
                return None, f"CONFIGURABLE_TOOLSETS literal okunamadı: {e!r}"
            return {str(k[0]) for k in kayitlar if k}, str(dosya)
        return None, f"{dosya} içinde CONFIGURABLE_TOOLSETS bulunamadı (üst akım yeniden adlandırmış olabilir)"
    return None, ("Hermes kaynak ağacı bulunamadı (HERMES_SRC ya da ~/.hermes/hermes-agent) — "
                  "anahtar kümesi ÖLÇÜLEMEDİ")


@pytest.mark.parametrize("profil", _profiller(), ids=lambda p: p.name)
def test_KAPALI_TAKIM_ADLARI_GERCEK_TOOLSET_ANAHTARIDIR(profil):
    """Kardeş çivinin ÖLÇEMEDİĞİ yarı: adlar GERÇEKTEN toolset anahtarı mı?

    NEDEN AYRI VE NEDEN ATLANABİLİR. `disabled_toolsets` bir KARA LİSTEDİR ve eşleşmeyen bir ad
    SESSİZCE yok sayılır: `termial` yazan bir profil "terminal kapalı" görünür, koşum terminali
    AÇIK koşar ve dizge sayan çivi yeşil kalır. Bunu ölçmenin tek dürüst yolu üst akımın kendi
    anahtar kümesine bakmaktır — ama Hermes bu deponun bağımlılığı DEĞİL. Kaynağa ulaşılamayan
    bir makinede çivi ATLAR ve NEDENİNİ söyler; sessizce yeşile dönüp kapsamadığı bir şeyi
    kapsıyormuş gibi yapmaz (UYDURMA YASAĞI).

    SÜRÜM BEYANI: yerel kaynak v0.18.2, canlı v0.19.0. Üst akım bir anahtarı yeniden adlandırırsa
    bu çivi YEREL sürüme göre yeşil kalıp canlıda yanılabilir — o yüzden koşum, hükmün kaynağını
    (dosya yolu) hata metnine yazar.
    """
    anahtarlar, kaynak = _hermes_toolset_anahtarlari()
    if anahtarlar is None:
        pytest.skip(f"toolset anahtar kümesi ÖLÇÜLEMEDİ — {kaynak}. Bu çivi ATLANDI: kardeş "
                    "çivi (`test_TEHLIKELI_ARAC_TAKIMLARI_KAPALI`) yalnız DİZGE varlığını "
                    "ölçer, bir yazım hatası bu koşumda YAKALANMAZ")
    cfg = yaml.safe_load((profil / "config.yaml").read_text(encoding="utf-8")) or {}
    kapali = [str(t) for t in ((cfg.get("agent") or {}).get("disabled_toolsets") or [])]
    taninmayan = [t for t in kapali if t not in anahtarlar]
    assert not taninmayan, (
        f"{profil.name}: `disabled_toolsets` GERÇEK bir toolset anahtarı OLMAYAN ad(lar) "
        f"taşıyor: {taninmayan} — eşleşmeyen ad SESSİZCE yok sayılır, yani o takım AÇIK koşar "
        f"ve dizge sayan çivi yeşil kalır (anahtar kümesi kaynağı: {kaynak})")


@pytest.mark.parametrize("profil", _profiller(), ids=lambda p: p.name)
def test_CALISMAK_ICIN_GEREKEN_ANAHTAR_BEYAN_EDILIR(profil):
    """Profil KENDİ `HERMES_HOME`udur, yani KENDİ `.env`ini okur — ana profilin anahtarı
    ona GEÇMEZ. Anahtar yoksa LLM her koşumda düşer, Görev 2'nin ham-brifing düşüş yolu
    bunu MASKELER ve sistem çalışıyor görünür: bot hiç düşünmeden teslimat yapar.
    Sessiz bozulma budur — gürültülü arıza değil.
    """
    man = yaml.safe_load((profil / "distribution.yaml").read_text(encoding="utf-8")) or {}
    adlar = {str(e.get("name")) for e in (man.get("env_requires") or [])
             if isinstance(e, dict)}
    assert "OPENROUTER_API_KEY" in adlar, (
        f"{profil.name}: `OPENROUTER_API_KEY` beyan edilmemiş — profil sessizce ham "
        f"brifinge düşer ve bu bir arıza gibi GÖRÜNMEZ (beyan edilenler: {sorted(adlar)})")


def test_SOUL_SESSIZ_JETONUNU_CIPLAK_YAZAR():
    """Tüketici `cevap.strip().upper() == "SESSIZ"` karşılaştırıyor (Görev 2). SOUL jetonu
    backtick içinde gösterirse model de backtick'le yazar, eşleşme düşer ve ham brifing
    gider — yani botun ASIL işi olan SUSMA iptal olur. Arıza sessiz değil, tam tersi."""
    soul = (PROFIL_KOKU / "sef" / "SOUL.md").read_text(encoding="utf-8")
    assert "SESSIZ" in soul, "SESSIZ sözleşmesi SOUL'dan düşmüş"
    assert "`SESSIZ`" not in soul, (
        "SOUL `SESSIZ` jetonunu backtick içinde gösteriyor — model onu backtick'le yazar "
        "ve tüketicinin çıplak karşılaştırması düşer")


def test_SOUL_MEKANIZMANIN_VERMEDIGI_YETENEGI_VAAT_ETMEZ():
    """ÖLÇÜLDÜ (`agent/agent_init.py`): hafıza VARSAYILAN OLARAK KAPALI
    (`_memory_enabled = False`, ancak `memory.memory_enabled` ile açılır) ve deposu
    `HERMES_HOME/memories/` altına yazar (`tools/memory_tool.py`) — yani safe-root'un
    DIŞINA. Ajana "hafızan var" demek, dünü göremeyen bir modele dünü UYDURMA daveti
    çıkarır; iki satır yukarıdaki "Sayı uydurma" kuralıyla doğrudan çelişir."""
    soul = (PROFIL_KOKU / "sef" / "SOUL.md").read_text(encoding="utf-8")
    assert "Hafızan var" not in soul, (
        "SOUL hâlâ hafıza vaat ediyor — mekanizma bunu vermiyor, model dünü uydurur")


def test_DAGITIM_BOTUN_TEK_YAZILABILIR_DIZININI_SILMEZ():
    """ÖLÇÜLDÜ: `dagit.sh` `rsync --delete` ile dağıtıyor. Safe-root `/opt/meridian/var/...`
    depoda YOK; dışlanmazsa HER dağıtım botun biriktirdiği her şeyi SİLER — yani §9.3'ün
    "her bot kendi artefaktının tek yazarı" sözleşmesinin taşıyıcısı yok olur. Depo bu
    sınıfı zaten tanıyor: `state/` ve `backups/` tam bu yüzden dışlama listesinde."""
    dagit = (KOK / "dagit.sh").read_text(encoding="utf-8")
    exc = dagit.split("RSYNC_EXC=", 1)[1].split("\n", 1)[0] if "RSYNC_EXC=" in dagit else ""
    assert "--exclude '/var'" in exc, (
        "`/var` RSYNC_EXC'te YOK — her `dagit.sh --uygula` botun tek yazılabilir dizinini "
        "SİLER ve bot her gün sıfırdan başlar. ANKORLU biçim şart (`/var`, `/ui` gibi): "
        "ankorsuz `var` ileride doğacak bir `ui/src/var/` yolunu da sessizce dağıtım dışı "
        "bırakırdı")


# ---------------------------------------------------------------------------
# GÖREV 3 — DURUŞUN ZAMANLANMIŞ KOŞUMDAKİ YÜZEYİ.
#
# Yukarıdaki çivilerin hepsi REPO tarafındaki BEYANI ölçer. Beyan, etkileşimli
# koşumu kapsar; systemd'nin başlattığı koşumu KAPSAMAZ — ölçüldü: `env_requires`
# `.env` YAZMAZ, yalnız `.env.template` üretir ve `.env` kullanıcı-sahiplidir.
# Aşağıdaki üç çivi o boşluğun kapağıdır: birim ne veriyor, ve kum havuzunu KİM
# yaratıyor.
# ---------------------------------------------------------------------------

BIRIM = KOK / "deploy/oracle-a1/meridian-brifing.service"
DEPLOY_SH = KOK / "deploy/oracle-a1/deploy.sh"
BOT_KUM_HAVUZU = "/opt/meridian/var/bots/sef"


def _birim_ortam_satirlari(anahtar: str) -> list[str]:
    """Birimin `Environment=` satırlarından `anahtar` geçenler (yorum satırları HARİÇ).

    Yorumlar ELENİR çünkü bu dosya kendi kararlarını uzun uzun anlatıyor ve anahtarın adı
    gerekçe metninde de geçiyor — yorumu sayan bir çivi, satır dosyadan DÜŞTÜKTEN sonra bile
    yeşil kalırdı (ölçtüğünü sandığı şeyi ölçmeyen çivi sınıfı)."""
    return [ln.strip() for ln in BIRIM.read_text(encoding="utf-8").splitlines()
            if ln.strip().startswith("Environment=") and anahtar in ln]


def test_SAFE_ROOT_BIRIMDE_DE_BAGLANIR():
    """§9.4/3, İKİNCİ yüzey — ve ZAMANLANMIŞ koşumu BAĞLAYAN yüzey budur.

    ÖLÇÜLDÜ: `env_requires` `.env` YAZMAZ, yalnız `.env.template` üretir; `.env` kullanıcı-sahibi
    olduğu için dağıtım ona hiç dokunamaz. Yani manifest beyanı ETKİLEŞİMLİ koşumu kapsar,
    systemd'nin başlattığı koşumu KAPSAMAZ. Birim değeri vermezse bot SINIRSIZ yazar
    (`agent/file_safety.py`, `if safe_roots:` — değişken tanımsızsa hiçbir kısıt uygulanmaz).
    """
    satirlar = _birim_ortam_satirlari("HERMES_WRITE_SAFE_ROOT")
    assert satirlar, (
        "birim `HERMES_WRITE_SAFE_ROOT` vermiyor — zamanlanmış koşumda bot SINIRSIZ yazar "
        "(değişken tanımsızsa hiçbir yazma kısıtı uygulanmaz; manifest beyanı yalnız "
        "ETKİLEŞİMLİ koşumu kapsar, `.env` yazılmadığı için)")
    assert all(ln.endswith(BOT_KUM_HAVUZU) for ln in satirlar), (
        f"safe-root botun kendi dizini değil: {satirlar} — beklenen {BOT_KUM_HAVUZU}")


def test_BIRIM_HERMES_HOME_SEF_PROFILINI_GOSTERIR():
    """Birim `HERMES_HOME` vermezse profil HİÇ çağrılmaz — ve arıza SESSİZDİR.

    ÖLÇÜLDÜ (`ops/sef_brifingi.py`, `_profil_evini_dogrula`): harness ortamdan gelen evi
    doğruluyor ve `sef` profili değilse çağrıyı REDDEDİYOR. Bu doğru davranış, ama bedeli var:
    birim değeri vermezse (ya da yanlış verirse) her koşum ham brifinge düşer, teslimat
    çalışmaya DEVAM eder ve dışarıdan hiçbir şey bozulmuş görünmez. Yani bu satırın yokluğu
    sıralama katmanını KALICI olarak kapatır — gürültüsüzce.

    Değer profil DİZİNİNİ gösterir, `~/.hermes`i değil: harness dizin adının `sef` olmasını
    şart koşuyor, çünkü §9.4 duruşunun tamamı (guard kancası · `cron_mode: deny` · deny
    listesi · kapalı araç takımları) O dizinin `config.yaml`ındadır, ana profilinkinde değil.
    """
    satirlar = _birim_ortam_satirlari("HERMES_HOME")
    assert satirlar, (
        "birim `HERMES_HOME` vermiyor — harness ev doğrulamasında düşer ve her koşum sessizce "
        "HAM brifinge iner; sıralama katmanı kalıcı olarak kapanır ve bu bir arıza gibi "
        "GÖRÜNMEZ")
    assert all(ln.endswith("/.hermes/profiles/sef") for ln in satirlar), (
        f"`HERMES_HOME` `sef` profil dizinini göstermiyor: {satirlar} — harness `sef` olmayan "
        "bir evi REDDEDER (bilinmeyen ajan kimliği çağrılmaz), yani yanlış değer de ham "
        "brifing demektir")


def test_DEPLOY_SH_BOT_KUM_HAVUZUNU_YARATIR():
    """Kum havuzunu BİRİNİN yaratması gerekir — ve artık rsync yaratmıyor.

    ÖLÇÜLDÜ: `dagit.sh` `RSYNC_EXC`e ankorlu `/var` dışlaması girdi (kardeş çivi
    `test_DAGITIM_BOTUN_TEK_YAZILABILIR_DIZININI_SILMEZ` onu koruyor) ve `.gitignore` `/var/`
    taşıyor. İkisi birlikte şu anlama gelir: `deploy/hermes/profiles/` canlıya rsync ile
    gider ama `var/bots/sef` GİTMEZ. Dizin yoksa safe-root VAR OLMAYAN bir yolu gösterir ve
    ilk yazma denemesi düşer — üstelik zamanlanmış koşumda, kimse bakmıyorken.

    Emsal biçim: `mkdir -p /home/ubuntu/backups` (yedek timer'ı ilk atışta hedefi hazır bulsun
    diye deploy.sh yaratıyor). Aynı sınıf, aynı çare.
    """
    d = DEPLOY_SH.read_text(encoding="utf-8")
    satirlar = [ln for ln in d.splitlines() if not ln.lstrip().startswith("#")]
    yaratim = [ln for ln in satirlar if "mkdir -p" in ln and BOT_KUM_HAVUZU in ln]
    assert yaratim, (
        f"deploy.sh `{BOT_KUM_HAVUZU}` dizinini YARATMIYOR — rsync artık `/var`ı taşımıyor, "
        "yani bu dizini kimse yaratmıyor: safe-root var olmayan bir yolu gösterir ve botun "
        "ilk yazma denemesi zamanlanmış koşumda düşer")
    izin = [ln for ln in satirlar if "chmod" in ln and BOT_KUM_HAVUZU in ln]
    assert izin, (
        f"deploy.sh `{BOT_KUM_HAVUZU}` dizininin İZNİNİ sabitlemiyor — umask'a bırakılan bir "
        "kum havuzu, botun tek yazılabilir dizinini makineye göre değişen bir izinle açar "
        "(`.dash.env` 0600 sabitlemesiyle aynı sınıf)")


def test_BRIFING_BIRIMI_ANA_PROFILE_YAZAMAZ():
    """Birim `~/.hermes`in TAMAMINA değil, YALNIZ kendi profil dizinine yazabilir.

    NEDEN. `HERMES_WRITE_SAFE_ROOT` AJANIN ARAÇLARINI bağlar; systemd `ReadWritePaths` ise
    SÜRECİ. İki AYRI katmandır ve biri ötekinin yerine geçmez. `ReadWritePaths` bütün
    `~/.hermes`i açsaydı bu birim ANA profilin `config.yaml`ına — yani her öteki hermes
    çağrısının guard duruşuna, `hooks_auto_accept` dahil — ve `~/.hermes/.env`e (model
    anahtarları) YAZABİLİRDİ. Safe-root katmanında kapattığımız kendi-silahsızlandırma
    sınıfının bir katman aşağıda yeniden açılması olurdu.

    ÇİVİ SIKILDI (denetim 2026-08-30). Eski hâli YALNIZ tam `/home/ubuntu/.hermes`i reddediyordu
    ve docstring'i `~/.hermes/profiles/` yazılmasını AÇIKÇA MEŞRU sayıyordu — oysa o hâlde `@sef`
    BAŞKA BİR BOTUN `config.yaml`ını (yani onun guard duruşunu) ve `.env`ini ezebilirdi. Aynı
    kendini-silahsızlandırma sınıfı, bir dizin yukarıda. "Ana profil dosyaları" bir hedef değil;
    hedef ŞUDUR: bu birim YALNIZ KENDİ profil dizinine yazabilir. Genel kural, ad listesi değil:
    `~/.hermes` altındaki her yazılabilir yol `<profil>/sef`in ta kendisi ya da ALTI olmalı.
    """
    import posixpath
    metin = (KOK / "deploy/oracle-a1/meridian-brifing.service").read_text(encoding="utf-8")
    yollar = [p.lstrip("-")
              for ln in metin.splitlines() if ln.strip().startswith("ReadWritePaths=")
              for p in ln.split("=", 1)[1].split()]
    hermes_yollari = [p for p in yollar if "/.hermes" in p]
    assert hermes_yollari, (
        "birim hermes evine hiç yazamıyor — `ProtectHome=read-only` altında ajanın kendi "
        "oturum durumu EROFS alır ve harness her gün sessizce ham brifinge düşer")
    kendi_evi = "/home/ubuntu/.hermes/profiles/sef"
    cok_genis = [p for p in hermes_yollari
                 if posixpath.normpath(p) != kendi_evi
                 and not posixpath.normpath(p).startswith(kendi_evi + "/")]
    assert not cok_genis, (
        f"birim `~/.hermes` altında KENDİ profil dizininin dışına yazabiliyor ({cok_genis}) — "
        f"beklenen yalnız {kendi_evi} (ya da altı). `~/.hermes` ANA profilin config.yaml'ını "
        "(guard duruşu) ve .env'ini (model anahtarları) taşır; `~/.hermes/profiles` ise BAŞKA "
        "BOTLARIN config.yaml'larını — ikisi de aynı kendini-silahsızlandırma sınıfıdır")


# ---------------------------------------------------------------------------
# OPERATÖRÜN REÇETESİ — İKİ BELGE, TEK REÇETE (denetim 2026-08-30)
#
# Reçete iki yerde duruyordu ve AYRIŞMIŞTI: manifest üç adım sayıyor ama TIMER'DAN HİÇ SÖZ
# ETMİYORDU; `deploy.sh` başka üç adım sayıyor ve üstüne "manifestle BİREBİR aynıdır" diye
# YANLIŞ bir olgu beyan ediyordu. Numara kayması kozmetik DEĞİL: manifesti okuyan operatör
# kurar, anahtarı doldurur ve KADANSI HİÇ AÇMAZ — sonuç sessizliktir ve "boşken sessiz"
# davranışından ayırt edilemez. Tam da bu dalın her yerde kapattığı sınıf, operatörün okuduğu
# tarafta açık kalmıştı.
# ---------------------------------------------------------------------------

SEF_MANIFEST = PROFIL_KOKU / "sef" / "distribution.yaml"

# Reçetenin ÜÇ EYLEMİ — her biri iki belgede de GEÇMEK ZORUNDA. Dizgeler komutun kendisidir,
# anlatısı değil: bir belge adımı düzyazıya gömerse çivi kırmızıya döner.
RECETE_EYLEMLERI = (
    "hermes profile install",
    "sudo systemctl enable --now meridian-brifing.timer",
)

# Var OLMAYAN komutlar. ÖLÇÜLDÜ (yerel Hermes v0.18.2, `hermes_cli/subcommands/profile.py`
# `build_profile_parser` — canlı v0.19.0, sürüm farkı beyan edilir): profil alt komutları
# list · use · create · delete · describe · show · alias · rename · export · import · install ·
# update · info. `env` YOKTUR — belgelenen komut çalıştırılamaz ve operatör "en sessiz adımı"
# hiç yapamaz.
OLMAYAN_KOMUTLAR = ("hermes profile env",)


def _recete_belgeleri() -> dict:
    return {"distribution.yaml": SEF_MANIFEST.read_text(encoding="utf-8"),
            "deploy.sh": DEPLOY_SH.read_text(encoding="utf-8")}


@pytest.mark.parametrize("eylem", RECETE_EYLEMLERI)
def test_RECETENIN_HER_EYLEMI_IKI_BELGEDE_DE_GECER(eylem):
    """İki belge TEK reçete anlatmalı. Adımın birinde olup ötekinde olmaması, o adımın
    atlanması demektir — ve atlanan adım hep operatörün okumadığı belgede kalır."""
    eksik = [ad for ad, metin in _recete_belgeleri().items() if eylem not in metin]
    assert not eksik, (
        f"reçete eylemi `{eylem}` şu belge(ler)de YOK: {eksik} — iki yerde tutulan bir reçete "
        "birini bayatlatmaktır ve bayatlayan taraf hep operatörün okuduğu taraf olur")


@pytest.mark.parametrize("komut", OLMAYAN_KOMUTLAR)
def test_OLMAYAN_HERMES_KOMUTU_BELGELENMEZ(komut):
    """Var olmayan bir komutla belgelenen adım, YAPILMAYAN adımdır. Ve bu adım tam da
    "anahtarsız profil sessizce ham brifinge düşer" arızasının kapağıydı."""
    gecen = [ad for ad, metin in _recete_belgeleri().items() if komut in metin]
    assert not gecen, (
        f"`{komut}` şu belge(ler)de yazılı: {gecen} — bu alt komut Hermes'te YOK "
        "(ölçüm: v0.18.2 `build_profile_parser`; list/use/create/delete/describe/show/alias/"
        "rename/export/import/install/update/info). Operatör komutu koşar, hata alır ve "
        "adımı atlar")


def test_KURULU_PROFILDEKI_ENV_SABLONU_UST_AKIMLA_AYNI_ADLA_ANILIR():
    """ÖLÇÜLDÜ (`hermes_cli/profile_distribution.py`, v0.18.2): `install` kaynak ağaçtaki
    `.env.template`i hedefe **`.env.EXAMPLE`** adıyla yazar (`ENV_EXAMPLE_FILENAME`), ve
    manifest bir şablon taşımıyorsa onu `env_requires`ten yine `.env.EXAMPLE` adıyla ÜRETİR.
    Belgelerimiz kurulu profilde `.env.template` aratıyordu — operatör aradığı dosyayı bulamaz
    ve "şablon yok" diye adımı atlar."""
    for ad, metin in _recete_belgeleri().items():
        assert ".env.template" not in metin, (
            f"{ad}: KURULU profilde `.env.template` aranıyor — üst akım oraya `.env.EXAMPLE` "
            "yazar; operatör aradığı dosyayı bulamaz")


def test_PROFIL_GUNCELLEME_CONFIGI_KORUDUGU_BELGELENIR():
    """ÖLÇÜLDÜ (v0.18.2 `build_profile_parser`, `profile update` açıklaması): `config.yaml` is
    preserved unless `--force-config`. Yani REPODAKİ bir duruş değişikliği (guard kancası,
    kapalı takımlar) `hermes profile update sef` ile canlı profile GİTMEZ. Hiçbir belge bunu
    söylemiyordu; söylemeyen belge, yapılmayan adım üretir."""
    metin = SEF_MANIFEST.read_text(encoding="utf-8")
    assert "--force-config" in metin, (
        "manifest `hermes profile update`in config.yaml'ı VARSAYILAN OLARAK KORUDUĞUNU "
        "söylemiyor — repodaki duruş değişikliği canlı profile sessizce ULAŞMAZ")


def test_deploy_sh_PROFIL_YOLUNU_BIRIMLE_KARSILASTIRIR():
    """AYNI OLGUNUN İKİ KAYNAĞI (denetim 2026-08-30). Profil yolu iki yerde yaşıyor: `deploy.sh`
    onu ÖLÇEREK türetir (çağıran kullanıcının ev dizini), birim ise SABİT yazar — systemd `$HOME`
    ikamesi yapamaz, başka çare yok. İkisi ayrıştığında arıza SESSİZDİR: betik "profil kurulu ✓"
    der, birim başka bir dizini gösterir, harness onu reddeder ve brifing sonsuza dek ham gider.
    Çare kaynağı teke indirmek DEĞİL (mümkün değil), İKİSİNİ KARŞILAŞTIRMAKTIR."""
    # KOD SATIRLARI ÖLÇÜLÜR, DÜZYAZI DEĞİL: bu betik kendi kararlarını uzun uzun anlatıyor ve
    # aradığımız dizgeler GEREKÇE metninde de geçiyor. Yorumu sayan bir çivi, satır dosyadan
    # DÜŞTÜKTEN sonra bile yeşil kalırdı (kardeş çivilerin `_birim_ortam_satirlari` dersi).
    kod = [ln for ln in DEPLOY_SH.read_text(encoding="utf-8").splitlines()
           if not ln.lstrip().startswith("#")]
    okuma = [ln for ln in kod if "Environment=HERMES_HOME=" in ln and "meridian-brifing.service" in ln]
    assert okuma, (
        "deploy.sh birimin HERMES_HOME satırını HİÇ OKUMUYOR — iki kaynak karşılaştırılmadan "
        "ayrışabilir ve ayrışma sessizdir")
    # `echo` HARİÇ: iki değişkeni birlikte BASAN satır, onları KARŞILAŞTIRAN satır değildir —
    # kıyas kaldırılıp yalnız mesaj kalsa çivi yeşil kalırdı (mutasyonla ölçüldü).
    kiyas = [ln for ln in kod if "$SEF_BIRIM_HOME" in ln and "$SEF_PROFIL" in ln
             and not ln.lstrip().startswith("echo")]
    assert kiyas, "okunan birim yolu ölçülen yolla KARŞILAŞTIRILMIYOR — okuma tek başına hüküm değil"
    assert any("AYRIŞIYOR" in ln for ln in kod), "deploy.sh ayrışmayı operatöre BASMIYOR"


def test_deploy_sh_PROFIL_YOLUNU_SUDO_ALTINDA_DA_OLCER():
    """`$HOME` bu betikte GÜVENİLİR DEĞİL: başlıktaki reçete `sudo` içeriyor ve betik
    `sudo bash deploy/...` ile koşulabilir — o hâlde `$HOME=/root` olur, KURULU profil
    "KURULU DEĞİL" raporlanır ve `.env` uyarısı HİÇ ateşlenmez. Kum havuzunun sahipliği bir üstte
    `stat` ile ÖLÇÜLÜYOR; aynı disiplin buraya da (denetim 2026-08-30)."""
    kod = [ln for ln in DEPLOY_SH.read_text(encoding="utf-8").splitlines()
           if not ln.lstrip().startswith("#") and not ln.lstrip().startswith("echo")]
    atama = [ln for ln in kod if ln.lstrip().startswith(("SEF_EV=", "SEF_PROFIL="))]
    assert atama, "deploy.sh profil yolunu hiç türetmiyor — çivi hedefini kaybetti"
    assert any("SUDO_USER" in ln for ln in atama), (
        f"deploy.sh profil yolunu `$HOME`dan varsayıyor ({atama!r}) — `sudo bash` altında "
        "`/root` çıkar, KURULU profil 'KURULU DEĞİL' raporlanır ve `.env` uyarısı hiç "
        "ateşlenmez; gerçek çağıran `SUDO_USER`dır")
