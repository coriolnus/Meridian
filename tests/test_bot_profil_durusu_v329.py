"""Her bot profili güvenlik duruşunu REPO TARAFINDA taşır — canlıya varmadan ölçülür.

Spec §9.4 üç çivi ister. Üçü de burada, ve üçü de `~/.hermes/profiles/` DEĞİL
`deploy/hermes/profiles/` üstünde ölçülür: canlıyı okuyan bir çivi, dosya canlıya VARDIKTAN
sonra bağırır — oysa korumasız bir profilin doğmaması gerekiyordu.
"""
from __future__ import annotations

import pathlib
import re

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


# SOUL ÇİVİLERİ PROFİL BAŞINA PARAMETRELENDİ (Faz 3a, 2026-08-30). Eskiden ikisi de yalnız
# `sef/SOUL.md`i okuyordu ve bu, tek profil varken görünmeyen bir boşluktu: roster'ın İKİNCİ
# profili eklendiğinde iki SÖZLEŞME çivisi onu KAPSAMIYORDU. ÖLÇÜLDÜ — `bekci/` eksik duruşla
# yaratıldığında yukarıdaki 11 parametreli çivi kırmızıya döndü, bu ikisi YEŞİL kaldı: yani
# yeni bir profil, jetonu backtick'le yazan ya da hafıza vaat eden bir SOUL ile sessizce
# doğabilirdi. Kapsam artık `_profiller()`den gelir, ad listesinden değil.
@pytest.mark.parametrize("profil", _profiller(), ids=lambda p: p.name)
def test_SOUL_SESSIZ_JETONUNU_CIPLAK_YAZAR(profil):
    """Tüketici jetonu NORMALİZE EDİP çıplak karşılaştırıyor (Görev 2). SOUL jetonu backtick
    içinde gösterirse model de backtick'le yazar; normalizasyon backtick'i soyuyor ama bu bir
    YEDEK, sözleşme değil — ve jetonu HİÇ taşımayan bir SOUL'da susma yeteneği tümden yoktur,
    yani botun ASIL işi olan SUSMA iptal olur. Arıza sessiz değil, tam tersi: her gün mesaj."""
    soul = (profil / "SOUL.md").read_text(encoding="utf-8")
    assert "SESSIZ" in soul, f"{profil.name}: SESSIZ sözleşmesi SOUL'dan düşmüş"
    assert "`SESSIZ`" not in soul, (
        f"{profil.name}: SOUL `SESSIZ` jetonunu backtick içinde gösteriyor — model onu "
        "backtick'le yazar ve tüketicinin çıplak karşılaştırması düşer")


@pytest.mark.parametrize("profil", _profiller(), ids=lambda p: p.name)
def test_SOUL_MEKANIZMANIN_VERMEDIGI_YETENEGI_VAAT_ETMEZ(profil):
    """ÖLÇÜLDÜ (`agent/agent_init.py`): hafıza VARSAYILAN OLARAK KAPALI
    (`_memory_enabled = False`, ancak `memory.memory_enabled` ile açılır) ve deposu
    `HERMES_HOME/memories/` altına yazar (`tools/memory_tool.py`) — yani safe-root'un
    DIŞINA. Ajana "hafızan var" demek, dünü göremeyen bir modele dünü UYDURMA daveti
    çıkarır; iki satır yukarıdaki "Sayı uydurma" kuralıyla doğrudan çelişir.

    `@bekci`de aynı yasak DAHA SERT bağlar: o botun bütün mesele si "bu N turdur aynı"dır ve
    hafızası olduğunu sanan bir model tam da o cümleyi UYDURUR. Tekrarı bastırmak harness'in
    damga dosyasının işidir, modelin değil."""
    soul = (profil / "SOUL.md").read_text(encoding="utf-8")
    assert "Hafızan var" not in soul, (
        f"{profil.name}: SOUL hâlâ hafıza vaat ediyor — mekanizma bunu vermiyor, model dünü "
        "uydurur")


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
# Aşağıdaki çiviler o boşluğun kapağıdır: birim ne veriyor, ve kum havuzunu KİM
# yaratıyor.
#
# KÜME TÜRETİLİR, YAZILMAZ (Faz 3, 2026-08-30). Bu bölümün çivileri bir tur önce
# `meridian-brifing.service` LİTERALİ üzerinde ölçüyordu. O gün doğruydu, bugün
# EKSİK olurdu: roster'ın ikinci profili (`@bekci`) KENDİ birimini aldı ve
# ikinci bir literal eklemek sınıfı KAPATMAZ — üçüncü bot geldiğinde çivi yine
# sessizce kör kalırdı (aynı ders: `_enjekte_edilen_soullar`, v266). Profil kümesi
# `_profiller()`ten, her profilin BİRİMİ de birim dosyalarının kendi
# `Environment=HERMES_HOME=` satırından TÜRETİLİR — yani "hangi birim hangi botu
# koşturuyor" sorusu ad kuralına DEĞİL ölçüme bağlıdır (filoda ad kuralı YOK:
# `@sef`in birimi `meridian-brifing`, `@bekci`nin birimi `meridian-bekci`).
# ---------------------------------------------------------------------------

DEPLOY_SH = KOK / "deploy/oracle-a1/deploy.sh"
BIRIM_KOKU = KOK / "deploy" / "oracle-a1"


def _kum_havuzu(profil: pathlib.Path) -> str:
    """Profilin kum havuzu — MANİFESTTEN okunur, testte yeniden YAZILMAZ.

    İkinci bir literal, manifest ile çivinin ayrışabileceği ikinci bir yer demektir; kardeş
    çivi (`test_SAFE_ROOT_BEYAN_EDILIR_ve_KENDI_DIZINIDIR`) zaten varsayılanın `/bots/<ad>`
    ile bittiğini ölçüyor, buradaki iş o TEK değeri taşımak."""
    man = yaml.safe_load((profil / "distribution.yaml").read_text(encoding="utf-8")) or {}
    for e in (man.get("env_requires") or []):
        if isinstance(e, dict) and str(e.get("name")) == "HERMES_WRITE_SAFE_ROOT":
            return str(e.get("default") or "")
    return ""


def _yonergeler(yol: pathlib.Path) -> list[str]:
    """Birim dosyasının YÖNERGE satırları (yorumlar HARİÇ).

    Yorumlar ELENİR çünkü bu dosyalar kendi kararlarını uzun uzun anlatıyor ve aranan
    anahtarların adı gerekçe metninde de geçiyor — yorumu sayan bir çivi, satır dosyadan
    DÜŞTÜKTEN sonra bile yeşil kalırdı (ölçtüğünü sandığı şeyi ölçmeyen çivi sınıfı)."""
    return [ln.strip() for ln in yol.read_text(encoding="utf-8").splitlines()
            if ln.strip() and not ln.strip().startswith(("#", ";"))]


def _profil_birimi(profil: pathlib.Path) -> pathlib.Path | None:
    """Bu profili koşturan `.service` — `Environment=HERMES_HOME=` ÖLÇÜLEREK bulunur.

    Ad kuralından TÜRETİLMEZ, çünkü filoda ad kuralı yoktur (`@sef` → `meridian-brifing`).
    Ölçülen bağ, harness'in gerçekten okuduğu bağdır: zamanlanmış koşumda profili SEÇEN şey
    tam olarak bu satırdır."""
    hedef = f"/.hermes/profiles/{profil.name}"
    for svc in sorted(BIRIM_KOKU.glob("*.service")):
        for ln in _yonergeler(svc):
            if ln.startswith("Environment=HERMES_HOME=") and ln.endswith(hedef):
                return svc
    return None


def _profil_timeri(profil: pathlib.Path) -> pathlib.Path | None:
    """Profilin biriminin YANINDAKİ `.timer` (aynı taban ad). Birim yoksa None."""
    svc = _profil_birimi(profil)
    if svc is None:
        return None
    t = svc.with_suffix(".timer")
    return t if t.is_file() else None


def _birim_ortam_satirlari(profil: pathlib.Path, anahtar: str) -> list[str]:
    """Profilin biriminden `anahtar` taşıyan `Environment=` satırları (yorumlar hariç)."""
    svc = _profil_birimi(profil)
    if svc is None:
        return []
    return [ln for ln in _yonergeler(svc)
            if ln.startswith("Environment=") and anahtar in ln]


def _deploy_kod() -> list[str]:
    """`deploy.sh`ın KOD satırları — yorum satırları elenir.

    Bu betik kendi kararlarını uzun uzun anlatıyor ve aradığımız dizgeler GEREKÇE metninde de
    geçiyor: yorumu sayan bir çivi, satır dosyadan DÜŞTÜKTEN sonra bile yeşil kalırdı."""
    return [ln for ln in DEPLOY_SH.read_text(encoding="utf-8").splitlines()
            if not ln.lstrip().startswith("#")]


def _atanan_degisken(satir: str) -> str | None:
    """`FOO="..."` satırından `FOO`. Değişken ADLARI ÇİVİYE YAZILMAZ, satırdan OKUNUR —
    `SEF_...` literalleri ikinci profilde ölçmeyi bırakır ve bunu kimse fark etmez."""
    m = re.match(r"\s*([A-Z][A-Z0-9_]*)=", satir)
    return m.group(1) if m else None


def _profil_yolu_atamasi(profil: pathlib.Path) -> list[str]:
    """`deploy.sh`ta profilin KURULU dizinini kuran ATAMA satır(lar)ı (yorum/echo hariç)."""
    iz = f"/.hermes/profiles/{profil.name}"
    return [ln for ln in _deploy_kod()
            if iz in ln and _atanan_degisken(ln) and not ln.lstrip().startswith("echo")]


def _f9_listesi() -> list[tuple[str, str]]:
    """`dagit.sh` `F9_LISTE`sindeki (repo yolu, canlı yol) çiftleri.

    STATİK DİZGE OLARAK ayrıştırılır ve bu bilinçlidir: liste kabukta döngüyle ÜRETİLSEYDİ
    kapsamayı ölçen çiviler (burası ve v266'daki başlık çivisi) neyi koruduklarını STATİK
    OLARAK göremezdi — kapının kendisi kör kalmasa da kapıyı koruyan çivi kör kalırdı."""
    metin = (KOK / "dagit.sh").read_text(encoding="utf-8")
    govde = metin.split('F9_LISTE="', 1)[1].split('"', 1)[0]
    return [(ln.split("|")[0].strip(), ln.split("|")[1].strip())
            for ln in govde.strip().splitlines() if "|" in ln]


@pytest.mark.parametrize("profil", _profiller(), ids=lambda p: p.name)
def test_HER_PROFILIN_KENDI_SYSTEMD_BIRIMI_VAR(profil):
    """Birimi olmayan profil, HİÇBİR KADANSTA KOŞMAYAN profildir — ve bu SESSİZDİR.

    Bu, `@sef` manifestindeki eksiğin ikizi (manifest timer'dan hiç söz etmiyordu): profil
    kurulur, `.env`i dolar, duruş çivileri yeşil kalır ve bot HİÇ konuşmaz. Sonuç "boşken
    sessiz" davranışından AYIRT EDİLEMEZ. Bağ ad kuralıyla DEĞİL ölçümle kurulur —
    `Environment=HERMES_HOME=` satırı harness'in gerçekten okuduğu bağdır.

    ÖNCELİK NOTU: bu çivi kırmızıysa aşağıdaki bütün birim çivileri de kırmızıdır; hepsi aynı
    kök nedeni gösterir (profilin sürücüsü yok), her biri ayrı bir eksiği değil."""
    assert _profil_birimi(profil) is not None, (
        f"{profil.name}: `deploy/oracle-a1/*.service` içinde `Environment=HERMES_HOME=` ile "
        f"`.hermes/profiles/{profil.name}` gösteren BİRİM YOK — profil kurulsa bile hiçbir "
        "kadansa asılı değildir ve sessizliği 'boşken sessiz'den ayırt edilemez")


@pytest.mark.parametrize("profil", _profiller(), ids=lambda p: p.name)
def test_SAFE_ROOT_BIRIMDE_DE_BAGLANIR(profil):
    """§9.4/3, İKİNCİ yüzey — ve ZAMANLANMIŞ koşumu BAĞLAYAN yüzey budur.

    ÖLÇÜLDÜ: `env_requires` `.env` YAZMAZ, yalnız `.env.template` üretir; `.env` kullanıcı-sahibi
    olduğu için dağıtım ona hiç dokunamaz. Yani manifest beyanı ETKİLEŞİMLİ koşumu kapsar,
    systemd'nin başlattığı koşumu KAPSAMAZ. Birim değeri vermezse bot SINIRSIZ yazar
    (`agent/file_safety.py`, `if safe_roots:` — değişken tanımsızsa hiçbir kısıt uygulanmaz).
    """
    kum = _kum_havuzu(profil)
    assert kum, f"{profil.name}: manifest safe-root varsayılanı beyan etmiyor — çivi ölçemez"
    satirlar = _birim_ortam_satirlari(profil, "HERMES_WRITE_SAFE_ROOT")
    assert satirlar, (
        f"{profil.name}: birim `HERMES_WRITE_SAFE_ROOT` vermiyor — zamanlanmış koşumda bot "
        "SINIRSIZ yazar (değişken tanımsızsa hiçbir yazma kısıtı uygulanmaz; manifest beyanı "
        "yalnız ETKİLEŞİMLİ koşumu kapsar, `.env` yazılmadığı için)")
    assert all(ln.endswith(kum) for ln in satirlar), (
        f"{profil.name}: safe-root botun kendi dizini değil: {satirlar} — manifest {kum!r} "
        "diyor. İki belge ayrışırsa bot manifestin vaat ettiği yerin DIŞINA yazar")


@pytest.mark.parametrize("profil", _profiller(), ids=lambda p: p.name)
def test_BIRIM_HERMES_HOME_KENDI_PROFILINI_GOSTERIR(profil):
    """Birim `HERMES_HOME` vermezse profil HİÇ çağrılmaz — ve arıza SESSİZDİR.

    ÖLÇÜLDÜ (`ops/sef_brifingi.py`, `_profil_evini_dogrula`): harness ortamdan gelen evi
    doğruluyor ve `sef` profili değilse çağrıyı REDDEDİYOR. Bu doğru davranış, ama bedeli var:
    birim değeri vermezse (ya da yanlış verirse) her koşum ham brifinge düşer, teslimat
    çalışmaya DEVAM eder ve dışarıdan hiçbir şey bozulmuş görünmez. Yani bu satırın yokluğu
    sıralama katmanını KALICI olarak kapatır — gürültüsüzce.

    Değer profil DİZİNİNİ gösterir, `~/.hermes`i değil: harness dizin adının profilin ADI
    olmasını şart koşuyor (`_profil_evini_dogrula`, `p.name != PROFIL_ADI` → RED), çünkü §9.4
    duruşunun tamamı (guard kancası · `cron_mode: deny` · deny listesi · kapalı araç takımları)
    O dizinin `config.yaml`ındadır, ana profilinkinde değil.
    """
    satirlar = _birim_ortam_satirlari(profil, "HERMES_HOME")
    assert satirlar, (
        f"{profil.name}: birim `HERMES_HOME` vermiyor — harness ev doğrulamasında düşer ve her "
        "koşum sessizce HAM brifinge iner; sıralama katmanı kalıcı olarak kapanır ve bu bir "
        "arıza gibi GÖRÜNMEZ")
    assert all(ln.endswith(f"/.hermes/profiles/{profil.name}") for ln in satirlar), (
        f"{profil.name}: `HERMES_HOME` kendi profil dizinini göstermiyor: {satirlar} — harness "
        f"`{profil.name}` olmayan bir evi REDDEDER (bilinmeyen ajan kimliği çağrılmaz), yani "
        "yanlış değer de ham brifing demektir")


@pytest.mark.parametrize("profil", _profiller(), ids=lambda p: p.name)
def test_PROFIL_BIRIMI_ARIZAYI_YUTMAZ(profil):
    """Birimin `ExecStart`ı DÜZ olmalı — `-` öneki çıkış kodunu YUTAR.

    ÖLÇÜLMÜŞ SÖZLEŞME (`@sef` emsali, birim başlığında yazılı): betik kanal yapılandırılmamışsa
    2, gönderim düşerse 1 döner ve systemd bunu `failed`e çevirir. `failed`in OKUYUCUSU VAR
    (`meridian/api.py` `/api/infra`, `ActiveState=failed` → "arizali" → panoda görünür). `-`
    önekiyle o zincir kopar: Telegram kırılır, teslimat HER GÜN sessizce düşer ve bunu haber
    verecek tek mekanizma zaten gönderemeyen işin TA KENDİSİDİR.

    Ayrıca TEK `ExecStart`: birden fazlası, `-` öneksizken ilk düşüşte DURUR — yani ikinci
    teslimat bir daha hiç koşmaz ve bu da sessizdir."""
    svc = _profil_birimi(profil)
    assert svc is not None, f"{profil.name}: birim yok (kardeş çivi kırmızıdır)"
    execler = [ln for ln in _yonergeler(svc) if ln.startswith("ExecStart")]
    assert len(execler) == 1, (
        f"{profil.name}: {svc.name} {len(execler)} adet ExecStart taşıyor — `-` öneksiz systemd "
        "ilk başarısızlıkta DURUR, yani sonrakiler sessizce hiç koşmaz")
    deger = execler[0].split("=", 1)[1].strip()
    assert not deger.startswith("-"), (
        f"{profil.name}: {svc.name} `ExecStart=-` (öneki `-`) — çıkış kodu YUTULUR, birim ASLA "
        "`failed` görmez ve teslimat kırıldığı gün panoda hiçbir şey kırmızıya dönmez")


@pytest.mark.parametrize("profil", _profiller(), ids=lambda p: p.name)
def test_PROFIL_BIRIMI_INSTALL_BOLUMU_TASIMAZ(profil):
    """Servis birimi `[Install]` TAŞIMAZ — tetiği YALNIZ kendi timer'ıdır.

    `[Install] WantedBy=multi-user.target` dururken `systemctl enable <birim>.service` SESSİZCE
    başarılı olur ve birime kimsenin istemediği bir AÇILIŞ KOŞUMU ekler: timer kadansının
    dışında, `Persistent=true` telafisiyle karışan ikinci bir tetik. Bölüm yokken aynı komut
    "no installation config" diye DÜŞER — operatör hatası sessiz davranış değişikliği değil,
    görünür bir hata olur.

    Bölüm BAŞLIĞI aranır, alt-dizge DEĞİL: dosyalar bölümün NEDEN olmadığını yorumda anlatıyor
    ve o yorum "[Install]" dizgesini İÇERİYOR (v327'nin `@sef` çivisinin aynı dersi)."""
    svc = _profil_birimi(profil)
    assert svc is not None, f"{profil.name}: birim yok (kardeş çivi kırmızıdır)"
    assert "[Install]" not in _yonergeler(svc), (
        f"{profil.name}: {svc.name} bir `[Install]` BÖLÜMÜ taşıyor — `systemctl enable "
        f"{svc.name}` sessizce geçer ve timer'dan bağımsız bir açılış koşumu ekler")


@pytest.mark.parametrize("profil", _profiller(), ids=lambda p: p.name)
def test_DEPLOY_SH_BOT_KUM_HAVUZUNU_YARATIR(profil):
    """Kum havuzunu BİRİNİN yaratması gerekir — ve artık rsync yaratmıyor.

    ÖLÇÜLDÜ: `dagit.sh` `RSYNC_EXC`e ankorlu `/var` dışlaması girdi (kardeş çivi
    `test_DAGITIM_BOTUN_TEK_YAZILABILIR_DIZININI_SILMEZ` onu koruyor) ve `.gitignore` `/var/`
    taşıyor. İkisi birlikte şu anlama gelir: `deploy/hermes/profiles/` canlıya rsync ile
    gider ama `var/bots/<ad>` GİTMEZ. Dizin yoksa safe-root VAR OLMAYAN bir yolu gösterir ve
    ilk yazma denemesi düşer — üstelik zamanlanmış koşumda, kimse bakmıyorken.

    Emsal biçim: `mkdir -p /home/ubuntu/backups` (yedek timer'ı ilk atışta hedefi hazır bulsun
    diye deploy.sh yaratıyor). Aynı sınıf, aynı çare.
    """
    kum = _kum_havuzu(profil)
    assert kum, f"{profil.name}: manifest safe-root varsayılanı beyan etmiyor — çivi ölçemez"
    satirlar = _deploy_kod()
    yaratim = [ln for ln in satirlar if "mkdir -p" in ln and kum in ln]
    assert yaratim, (
        f"{profil.name}: deploy.sh `{kum}` dizinini YARATMIYOR — rsync artık `/var`ı taşımıyor, "
        "yani bu dizini kimse yaratmıyor: safe-root var olmayan bir yolu gösterir ve botun "
        "ilk yazma denemesi zamanlanmış koşumda düşer")
    izin = [ln for ln in satirlar if "chmod" in ln and kum in ln]
    assert izin, (
        f"{profil.name}: deploy.sh `{kum}` dizininin İZNİNİ sabitlemiyor — umask'a bırakılan "
        "bir kum havuzu, botun tek yazılabilir dizinini makineye göre değişen bir izinle açar "
        "(`.dash.env` 0600 sabitlemesiyle aynı sınıf)")


@pytest.mark.parametrize("profil", _profiller(), ids=lambda p: p.name)
def test_PROFIL_BIRIMI_BASKA_PROFILE_YAZAMAZ(profil):
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
    `~/.hermes` altındaki her yazılabilir yol `<profil>/<ad>`in ta kendisi ya da ALTI olmalı.

    HÜKÜM İKİNCİ PROFİLDE DAHA SERT (Faz 3): iki bot varken "biraz geniş" bir yol artık teorik
    değil, KOMŞUNUN duruşuna açılan bir kapıdır. Bu yüzden çivi tek birimde değil, profil
    kümesinden TÜRETİLEN her birimde ölçülür.
    """
    import posixpath
    svc = _profil_birimi(profil)
    assert svc is not None, f"{profil.name}: birim yok (kardeş çivi kırmızıdır)"
    yollar = [p.lstrip("-")
              for ln in _yonergeler(svc) if ln.startswith("ReadWritePaths=")
              for p in ln.split("=", 1)[1].split()]
    hermes_yollari = [p for p in yollar if "/.hermes" in p]
    assert hermes_yollari, (
        f"{profil.name}: birim hermes evine hiç yazamıyor — `ProtectHome=read-only` altında "
        "ajanın kendi oturum durumu EROFS alır ve harness her gün sessizce ham brifinge düşer")
    kendi_evi = f"/home/ubuntu/.hermes/profiles/{profil.name}"
    cok_genis = [p for p in hermes_yollari
                 if posixpath.normpath(p) != kendi_evi
                 and not posixpath.normpath(p).startswith(kendi_evi + "/")]
    assert not cok_genis, (
        f"{profil.name}: birim `~/.hermes` altında KENDİ profil dizininin dışına yazabiliyor "
        f"({cok_genis}) — beklenen yalnız {kendi_evi} (ya da altı). `~/.hermes` ANA profilin "
        "config.yaml'ını (guard duruşu) ve .env'ini (model anahtarları) taşır; "
        "`~/.hermes/profiles` ise BAŞKA BOTLARIN config.yaml'larını — ikisi de aynı "
        "kendini-silahsızlandırma sınıfıdır")


# ---------------------------------------------------------------------------
# KADANS — HER BOT KENDİ TETİĞİNİ ALIR, VE İKİ MESAJ AYNI DAKİKAYA DÜŞMEZ (Faz 3)
#
# `@bekci` `meridian-brifing.service`e İKİNCİ bir `ExecStart` olarak BİNMEZ. Faz 1'in "iki
# teslimat, tek sarmalayıcı" dersi burada TERSİNE geçerlidir ve gerekçesi FARKLIDIR: o iki
# teslimat AYNI mesajı kuruyordu; `@sef` ve `@bekci` AYRI artefaktın sahibi ve AYRI mesaj
# kuruyor — biri düşerse öteki KOŞMALI. Aynı birimde iki `ExecStart`, `-` öneksizken ilkinin
# düşüşünde ikinciyi hiç koşturmazdı (kardeş çivi: test_PROFIL_BIRIMI_ARIZAYI_YUTMAZ).
# ---------------------------------------------------------------------------

def _sprint_penceresi() -> tuple[int, int]:
    """Öğrenme sprintinin gece penceresi — KAYNAKTAN okunur, çiviye YAZILMAZ.

    ÖLÇÜLDÜ (`meridian/sprint.py`): `SPRINT_HOURS` otomatik sprintin TEK saat kapısıdır
    (`should_run`: pencere dışıysa `sebep=saat_dilimi_disinda`). Sayıyı buraya kopyalamak,
    pencere kaydığı gün çivinin sessizce yanlış aralığı korumasıydı.

    KARŞILAŞTIRMANIN TABANI: `should_run` naive `dt.datetime.now()` kullanıyor, yani pencere
    SUNUCU YERELİDİR; bizim `OnCalendar`ımız ise AÇIKÇA UTC. ÇIKARIM, ÖLÇÜM DEĞİL: A1'in TZ'si
    bu oturumda ölçülemedi (ssh yok) — aşağıdaki hüküm "A1 UTC koşuyor" varsayımına bağlıdır ve
    bu satır o bağı gizlememek için burada."""
    import re as _re
    m = _re.search(r"^SPRINT_HOURS\s*=\s*\((\d+),\s*(\d+)\)",
                   (KOK / "meridian" / "sprint.py").read_text(encoding="utf-8"), _re.M)
    assert m, "`SPRINT_HOURS` kaynakta bulunamadı — çivi kendi ölçüm eksenini kaybetmiş"
    return int(m.group(1)), int(m.group(2))


def _oncalendar_saati(timer: pathlib.Path) -> tuple[int, int]:
    """Timer'ın `OnCalendar` saati — AÇIKÇA UTC yazılmış olmak ZORUNDA.

    Sunucu TZ'sine güvenen bir kadans, TZ değiştiği gün sessizce başka bir saate kayar
    (`meridian-brifing.timer` başlığındaki DST dersinin aynısı)."""
    import re as _re
    m = _re.search(r"^OnCalendar=\S+ (\d{2}):(\d{2}):(\d{2}) UTC\s*$",
                   timer.read_text(encoding="utf-8"), _re.M)
    assert m, (
        f"{timer.name}: `OnCalendar` açıkça UTC saatiyle yazılmamış — sunucu TZ'si değiştiği gün "
        "kadans sessizce kayar ve bunu hiçbir şey bildirmez")
    return int(m.group(1)), int(m.group(2))


@pytest.mark.parametrize("profil", _profiller(), ids=lambda p: p.name)
def test_HER_PROFILIN_KENDI_TIMERI_VAR(profil):
    """Her bot KENDİ timer'ını alır — biri düşerse öteki koşmalı.

    Paylaşılan tek bir tetik, iki botu TEK arıza noktasına bağlar: `@sef`in birimi `failed`
    olduğu gün `@bekci` de susardı ve sessizliği "bildirilecek yeni bir şey yok"tan ayırt
    edilemezdi — tam olarak bu roster'ın kapatmak için var olduğu sınıf."""
    svc = _profil_birimi(profil)
    assert svc is not None, f"{profil.name}: birim yok (kardeş çivi kırmızıdır)"
    t = _profil_timeri(profil)
    assert t is not None, (
        f"{profil.name}: {svc.name} birimi var ama YANINDA `.timer` YOK — birimin `[Install]`ı "
        "da olmadığı için (kardeş çivi) hiçbir şey onu tetiklemez: teslimat HİÇ başlamaz")


def test_IKI_BOT_MESAJI_AYNI_DAKIKAYA_DUSMEZ():
    """DİKKAT BÜTÇESİ BİR KAYNAKTIR — bu roster onu korumak için var.

    İki bot AYNI operatöre AYNI kanaldan yazıyor. Dakikalar arayla düşen iki mesaj, tek bir
    yığın gibi okunur ve ikincisi ilkinin gürültüsü olur; aralarına saat koymak, ikisinin de
    OKUNMA olasılığını artırır. Sayısal hüküm: en yakın iki tetik arasında EN AZ dört saat.
    Dört, 24 saati yedi profile bölmenin (≈3,4 sa) hemen üstündeki ilk tam sayıdır — yani
    roster dolduğunda bu kapı hâlâ sağlanabilir ama gevşek değildir.

    `RandomizedDelaySec` PAYI YEMEZ: filoda değeri 300 sn'dir (5 dk), dört saatin yanında
    ihmal edilebilir; kapı yine de ham `OnCalendar` üstünde ölçülür çünkü karar orada verilir."""
    saatler = {}
    for profil in _profiller():
        t = _profil_timeri(profil)
        if t is None:
            continue                       # kardeş çivi zaten kırmızı; burada ikinci kez bağırma
        sa, dk = _oncalendar_saati(t)
        saatler[profil.name] = sa * 60 + dk
    if len(saatler) < 2:
        pytest.skip("tek profil — ayrışma ölçülemez (kapsam beyanı: bu kapı iki bottan itibaren)")
    adlar = sorted(saatler, key=lambda a: saatler[a])
    for i, ad in enumerate(adlar):
        oteki = adlar[(i + 1) % len(adlar)]
        fark = (saatler[oteki] - saatler[ad]) % (24 * 60)
        assert fark >= 4 * 60, (
            f"`{ad}` ({saatler[ad] // 60:02d}:{saatler[ad] % 60:02d}Z) ile `{oteki}` "
            f"({saatler[oteki] // 60:02d}:{saatler[oteki] % 60:02d}Z) arası {fark} dk — iki bot "
            "operatörün önüne neredeyse aynı anda düşer ve ikincisi birincisinin gürültüsü olur")


def test_GECE_PENCERESINE_IKINCI_BIR_BOT_EKLENMEZ():
    """4 çekirdekli kutunun gece penceresinde ZATEN bir bot var — ikincisi oraya kaymaz.

    KAPI SAYIMDIR, AD LİSTESİ DEĞİL. `@sef` penceredeki tek sakindir ve ORADAN ÇIKAMAZ: içeriği
    SEANSA bağlıdır ve ABD kapanışı EST'de 21:00 UTC'dir, yani 22:00'den önceye çekilirse tetik
    EOD turundan önce ateşler (`meridian-brifing.timer` başlığındaki ölçüm). Bu bir muafiyet
    değil bir ZORUNLULUKTUR — ve tam da bu yüzden pencereye giren HER YENİ bot, kaçınılabilir
    bir yük kararıdır: `@bekci`nin pencereleri GÜN cinsindendir (gun=3 / duran_gun=60), yani
    seansla hiçbir bağı yok ve pencereden kaçınmak ona BEDAVAYA gelir.

    NE ÖLÇÜLDÜ, NE ÇIKARILDI: pencere `meridian/sprint.py` KAYNAĞINDAN okunuyor (ölçüm);
    o pencerenin UTC karşılığı A1'in TZ'sine bağlı ve TZ bu oturumda ölçülemedi (çıkarım —
    bkz. `_sprint_penceresi` notu).

    Sayı 1'e sabit: bu kapıyı 2'ye çıkarmak, üçüncü bir botun gece yüküne binmesini SESSİZ
    değil GÖRÜNÜR bir karar hâline getirir — çiviyi elle değiştirmek gerekir."""
    lo, hi = _sprint_penceresi()
    icerde = []
    for profil in _profiller():
        t = _profil_timeri(profil)
        if t is None:
            continue                       # kardeş çivi zaten kırmızı; burada ikinci kez bağırma
        sa, dk = _oncalendar_saati(t)
        if sa >= lo or sa < hi:
            icerde.append(f"{profil.name}@{sa:02d}:{dk:02d}Z")
    assert len(icerde) <= 1, (
        f"öğrenme sprintinin gece penceresi [{lo}:00, {hi}:00) içinde {len(icerde)} bot tetiği "
        f"var: {icerde}. 4 çekirdekli kutuda 4 işçilik antrenmanın üstüne ikinci bir ajan "
        "çağrısı bindirmek kaçınılabilir bir yüktür; seansa bağlı OLMAYAN bir botun penceresi "
        "gündüze alınır")


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

# KAPSAM BÜYÜDÜ (Faz 3): bu bölüm bir tur önce YALNIZ `@sef`in manifestini okuyordu. Çiviler
# tam olarak "manifest ile deploy.sh ayrışmasın" diye vardı ve iki profilden BİRİNİ ölçüyordu —
# yani `@bekci`nin reçetesi ikisinde farklı yazılsa hiçbir şey kırmızıya dönmezdi. Küme artık
# `_profiller()`ten TÜRETİLİR; ikinci bir literal eklemek üçüncü profilde aynı körlüğü doğururdu.

# HER PROFİLDE AYNI olan eylem(ler). Profile ÖZGÜ eylem (kendi timer'ını açan komut) buraya
# yazılmaz — MANİFESTTEN OKUNUR (`_kadans_komutu`), çünkü filoda birim ad kuralı yoktur.
ORTAK_RECETE_EYLEMLERI = ("hermes profile install",)

# Var OLMAYAN komutlar. ÖLÇÜLDÜ (yerel Hermes v0.18.2, `hermes_cli/subcommands/profile.py`
# `build_profile_parser` — canlı v0.19.0, sürüm farkı beyan edilir): profil alt komutları
# list · use · create · delete · describe · show · alias · rename · export · import · install ·
# update · info. `env` YOKTUR — belgelenen komut çalıştırılamaz ve operatör "en sessiz adımı"
# hiç yapamaz.
OLMAYAN_KOMUTLAR = ("hermes profile env",)

_KADANS_KALIBI = re.compile(r"sudo systemctl enable --now (meridian-[A-Za-z0-9@._-]+\.timer)")


def _manifest_metni(profil: pathlib.Path) -> str:
    return (profil / "distribution.yaml").read_text(encoding="utf-8")


def _kadans_komutu(profil: pathlib.Path) -> str | None:
    """Profilin kadansını AÇAN komut — MANİFESTTEN okunur, çiviye yazılmaz.

    Bu, reçetenin profile ÖZGÜ tek adımıdır ve tam da ilk turda ayrışan adımdır (manifest
    timer'dan hiç söz etmiyordu). Kaynak olarak MANİFEST seçildi çünkü operatörün izlediği
    belge odur; `deploy.sh` ona UYMAK zorundadır, tersi değil."""
    m = _KADANS_KALIBI.search(_manifest_metni(profil))
    return m.group(0) if m else None


def _recete_belgeleri(profil: pathlib.Path) -> dict:
    """İki belgenin TAM metni — "şu geçmemeli" çivileri için (yasak bir dizge NEREDE geçerse
    geçsin ölçülmeli; dar bir pencere onu gizlerdi)."""
    return {f"{profil.name}/distribution.yaml": _manifest_metni(profil),
            "deploy.sh": DEPLOY_SH.read_text(encoding="utf-8")}


_ADIM_ECHO = re.compile(r'^\s*echo\s+"\s*\d\)\s')


def _recete_adimlari(profil: pathlib.Path) -> dict:
    """OPERATÖRÜN REÇETE OLARAK OKUDUĞU metin — "şu geçmeli" çivileri için.

    NEDEN TAM METİN DEĞİL (mutasyonla ÖLÇÜLDÜ, 2026-08-30): reçetenin 3. adımı `deploy.sh`ın
    basılan reçetesinden SİLİNDİĞİNDE çivi YEŞİL KALIYORDU — çünkü aynı komut dosyanın BAŞKA
    yerlerinde de geçiyor (kadans kapısının kendi `enable` satırı ve kapalı-dal uyarısı). Yani
    çivi "operatör bu adımı okuyor mu" sorusunu değil "dizge dosyada var mı" sorusunu ölçüyordu;
    silinen adım, onu hiç okumayacağı bir satır yüzünden gizleniyordu.

    İKİ BELGEDE DE ÖLÇÜ "OPERATÖRÜN GÖRDÜĞÜ REÇETE"DİR:
      · manifest → dosyanın BAŞINDAKİ yorum bloğu (kurulum reçetesi orada yaşar; ilk yorum
        olmayan satırda biter),
      · deploy.sh → NUMARALI adım olarak BASILAN `echo` satırları (`echo "  N) ..."`).
    """
    manifest_bas = []
    for ln in _manifest_metni(profil).splitlines():
        if ln.strip() and not ln.lstrip().startswith("#"):
            break
        manifest_bas.append(ln)
    adimlar = [ln for ln in _deploy_kod() if _ADIM_ECHO.match(ln)]
    return {f"{profil.name}/distribution.yaml (kurulum bloğu)": "\n".join(manifest_bas),
            "deploy.sh (numaralı reçete adımları)": "\n".join(adimlar)}


def _recete_cift_listesi() -> list[tuple[pathlib.Path, str]]:
    """(profil, eylem) çiftleri — ortak eylemler + her profilin KENDİ kadans komutu."""
    ciftler = []
    for profil in _profiller():
        for eylem in ORTAK_RECETE_EYLEMLERI:
            ciftler.append((profil, eylem))
        kadans = _kadans_komutu(profil)
        if kadans:                 # yoksa ayrı çivi (test_MANIFEST_KENDI_KADANSINI_YAZAR) bağırır
            ciftler.append((profil, kadans))
    return ciftler


@pytest.mark.parametrize("profil", _profiller(), ids=lambda p: p.name)
def test_MANIFEST_KENDI_KADANSINI_YAZAR(profil):
    """Manifest kendi timer'ını AÇAN komutu YAZMAK ZORUNDA — ölçülen ilk ayrışma buydu.

    Manifest kurulumu ve `.env`i anlatıp KADANSTAN hiç söz etmezse, onu izleyen operatör
    profili kurar, anahtarı doldurur ve teslimatı HİÇ BAŞLATMAZ. Sonuç sessizliktir ve botun
    "boşken sessiz" davranışından AYIRT EDİLEMEZ — yani arıza kendi kılığına girer.

    Ayrıca bu çivi, aşağıdaki reçete karşılaştırmasının VACUOUS olmasını da engeller: komut
    manifestte yoksa türetilecek eylem de yoktur ve karşılaştırma sessizce hiçbir şey ölçmez."""
    assert _kadans_komutu(profil) is not None, (
        f"{profil.name}: manifest `sudo systemctl enable --now <birim>.timer` komutunu HİÇ "
        "yazmıyor — operatör kurar, anahtarı doldurur ve kadansı hiç açmaz; sessizlik 'boşken "
        "sessiz'den ayırt edilemez")


@pytest.mark.parametrize("profil", _profiller(), ids=lambda p: p.name)
def test_MANIFESTIN_ANDIGI_TIMER_GERCEKTEN_VAR(profil):
    """Manifestin adını verdiği timer DEPODA da olmalı — iki belge tek birimi anlatmalı.

    `@bekci`nin manifesti `meridian-bekci.timer`ı Görev 2'de ADIYLA sabitledi; birimin kendisi
    Görev 3'ün işiydi. Bu çivi o boşluğu kapatır: manifest var olmayan bir birimi işaret
    ederse operatörün üçüncü adımı `Failed to enable unit: No such file or directory` ile
    düşer ve kurulum tam da en sessiz noktasında yarım kalır."""
    kadans = _kadans_komutu(profil)
    if kadans is None:
        pytest.skip(f"{profil.name}: manifest kadans komutu yazmıyor — kardeş çivi kırmızı")
    ad = _KADANS_KALIBI.search(kadans).group(1)
    assert (BIRIM_KOKU / ad).is_file(), (
        f"{profil.name}: manifest `{ad}` diyor ama `deploy/oracle-a1/{ad}` YOK — operatörün "
        "üçüncü adımı 'No such file or directory' ile düşer")
    t = _profil_timeri(profil)
    assert t is not None and t.name == ad, (
        f"{profil.name}: manifest `{ad}` diyor, birimden türeyen timer ise "
        f"{t.name if t else '(yok)'} — manifest BAŞKA bir birimin kadansını açtırıyor ve o "
        "birim bu profili çağırmıyor: operatör 'açtım' der, bot hiç koşmaz")


@pytest.mark.parametrize("profil,eylem", _recete_cift_listesi(),
                         ids=lambda x: x if isinstance(x, str) else x.name)
def test_RECETENIN_HER_EYLEMI_IKI_BELGEDE_DE_GECER(profil, eylem):
    """İki belge TEK reçete anlatmalı. Adımın birinde olup ötekinde olmaması, o adımın
    atlanması demektir — ve atlanan adım hep operatörün okumadığı belgede kalır.

    ÖLÇÜ, DOSYANIN TAMAMI DEĞİL, OPERATÖRÜN REÇETE OLARAK OKUDUĞU BÖLÜMDÜR — gerekçesi ve o
    gerekçeyi doğuran mutasyon `_recete_adimlari`da yazılı."""
    eksik = [ad for ad, metin in _recete_adimlari(profil).items() if eylem not in metin]
    assert not eksik, (
        f"{profil.name}: reçete eylemi `{eylem}` şu belge(ler)de YOK: {eksik} — iki yerde "
        "tutulan bir reçete birini bayatlatmaktır ve bayatlayan taraf hep operatörün okuduğu "
        "taraf olur")


@pytest.mark.parametrize("profil", _profiller(), ids=lambda p: p.name)
@pytest.mark.parametrize("komut", OLMAYAN_KOMUTLAR)
def test_OLMAYAN_HERMES_KOMUTU_BELGELENMEZ(komut, profil):
    """Var olmayan bir komutla belgelenen adım, YAPILMAYAN adımdır. Ve bu adım tam da
    "anahtarsız profil sessizce ham brifinge düşer" arızasının kapağıydı."""
    gecen = [ad for ad, metin in _recete_belgeleri(profil).items() if komut in metin]
    assert not gecen, (
        f"`{komut}` şu belge(ler)de yazılı: {gecen} — bu alt komut Hermes'te YOK "
        "(ölçüm: v0.18.2 `build_profile_parser`; list/use/create/delete/describe/show/alias/"
        "rename/export/import/install/update/info). Operatör komutu koşar, hata alır ve "
        "adımı atlar")


@pytest.mark.parametrize("profil", _profiller(), ids=lambda p: p.name)
def test_KURULU_PROFILDEKI_ENV_SABLONU_UST_AKIMLA_AYNI_ADLA_ANILIR(profil):
    """ÖLÇÜLDÜ (`hermes_cli/profile_distribution.py`, v0.18.2): `install` kaynak ağaçtaki
    `.env.template`i hedefe **`.env.EXAMPLE`** adıyla yazar (`ENV_EXAMPLE_FILENAME`), ve
    manifest bir şablon taşımıyorsa onu `env_requires`ten yine `.env.EXAMPLE` adıyla ÜRETİR.
    Belgelerimiz kurulu profilde `.env.template` aratıyordu — operatör aradığı dosyayı bulamaz
    ve "şablon yok" diye adımı atlar."""
    for ad, metin in _recete_belgeleri(profil).items():
        assert ".env.template" not in metin, (
            f"{ad}: KURULU profilde `.env.template` aranıyor — üst akım oraya `.env.EXAMPLE` "
            "yazar; operatör aradığı dosyayı bulamaz")


@pytest.mark.parametrize("profil", _profiller(), ids=lambda p: p.name)
def test_PROFIL_GUNCELLEME_CONFIGI_KORUDUGU_BELGELENIR(profil):
    """ÖLÇÜLDÜ (v0.18.2 `build_profile_parser`, `profile update` açıklaması): `config.yaml` is
    preserved unless `--force-config`. Yani REPODAKİ bir duruş değişikliği (guard kancası,
    kapalı takımlar) düz `hermes profile update <ad>` ile canlı profile GİTMEZ. Hiçbir belge
    bunu söylemiyordu; söylemeyen belge, yapılmayan adım üretir."""
    assert "--force-config" in _manifest_metni(profil), (
        f"{profil.name}: manifest `hermes profile update`in config.yaml'ı VARSAYILAN OLARAK "
        "KORUDUĞUNU söylemiyor — repodaki duruş değişikliği canlı profile sessizce ULAŞMAZ")


@pytest.mark.parametrize("profil", _profiller(), ids=lambda p: p.name)
def test_deploy_sh_PROFIL_YOLUNU_BIRIMLE_KARSILASTIRIR(profil):
    """AYNI OLGUNUN İKİ KAYNAĞI (denetim 2026-08-30). Profil yolu iki yerde yaşıyor: `deploy.sh`
    onu ÖLÇEREK türetir (çağıran kullanıcının ev dizini), birim ise SABİT yazar — systemd `$HOME`
    ikamesi yapamaz, başka çare yok. İkisi ayrıştığında arıza SESSİZDİR: betik "profil kurulu ✓"
    der, birim başka bir dizini gösterir, harness onu reddeder ve brifing sonsuza dek ham gider.
    Çare kaynağı teke indirmek DEĞİL (mümkün değil), İKİSİNİ KARŞILAŞTIRMAKTIR."""
    svc = _profil_birimi(profil)
    assert svc is not None, f"{profil.name}: birim yok (kardeş çivi kırmızıdır)"
    # KOD SATIRLARI ÖLÇÜLÜR, DÜZYAZI DEĞİL: bu betik kendi kararlarını uzun uzun anlatıyor ve
    # aradığımız dizgeler GEREKÇE metninde de geçiyor. Yorumu sayan bir çivi, satır dosyadan
    # DÜŞTÜKTEN sonra bile yeşil kalırdı (kardeş çivilerin `_yonergeler` dersi).
    kod = _deploy_kod()
    okuma = [ln for ln in kod if "Environment=HERMES_HOME=" in ln and svc.name in ln]
    assert okuma, (
        f"{profil.name}: deploy.sh `{svc.name}` biriminin HERMES_HOME satırını HİÇ OKUMUYOR — "
        "iki kaynak karşılaştırılmadan ayrışabilir ve ayrışma sessizdir")
    # `echo` HARİÇ: iki değişkeni birlikte BASAN satır, onları KARŞILAŞTIRAN satır değildir —
    # kıyas kaldırılıp yalnız mesaj kalsa çivi yeşil kalırdı (mutasyonla ölçüldü).
    # DEĞİŞKEN ADI TÜRETİLİR, YAZILMAZ: `SEF_BIRIM_HOME` literali ikinci profilde ölçmeyi bırakır.
    birim_var = _atanan_degisken(okuma[0])
    olcum = _profil_yolu_atamasi(profil)
    assert olcum, (
        f"{profil.name}: deploy.sh `.hermes/profiles/{profil.name}` yolunu hiç TÜRETMİYOR — "
        "kıyasın bir yakası yok")
    olcum_var = _atanan_degisken(olcum[0])
    kiyas = [ln for ln in kod
             if birim_var and olcum_var
             and f"${birim_var}" in ln and f"${olcum_var}" in ln
             and not ln.lstrip().startswith("echo")]
    assert kiyas, (
        f"{profil.name}: okunan birim yolu (${birim_var}) ölçülen yolla (${olcum_var}) "
        "KARŞILAŞTIRILMIYOR — okuma tek başına hüküm değil")
    assert any("AYRIŞIYOR" in ln for ln in kod), "deploy.sh ayrışmayı operatöre BASMIYOR"


@pytest.mark.parametrize("profil", _profiller(), ids=lambda p: p.name)
def test_deploy_sh_PROFIL_YOLUNU_SUDO_ALTINDA_DA_OLCER(profil):
    """`$HOME` bu betikte GÜVENİLİR DEĞİL: başlıktaki reçete `sudo` içeriyor ve betik
    `sudo bash deploy/...` ile koşulabilir — o hâlde `$HOME=/root` olur, KURULU profil
    "KURULU DEĞİL" raporlanır ve `.env` uyarısı HİÇ ateşlenmez. Kum havuzunun sahipliği bir üstte
    `stat` ile ÖLÇÜLÜYOR; aynı disiplin buraya da (denetim 2026-08-30).

    ZİNCİR TÜRETİLEREK İZLENİR: profil yolunu kuran satır bulunur, o satırın İÇİNDEN referans
    verdiği ev değişkeni okunur ve O değişkenin ataması `SUDO_USER` taşımak zorundadır. Böylece
    çivi `SEF_EV` gibi bir ada bağlı kalmaz — ikinci profil kendi adını kullanabilir."""
    atama = _profil_yolu_atamasi(profil)
    assert atama, (
        f"{profil.name}: deploy.sh profil yolunu hiç türetmiyor — çivi hedefini kaybetti")
    kod = [ln for ln in _deploy_kod() if not ln.lstrip().startswith("echo")]
    zincir = list(atama)
    for ref in set(re.findall(r"\$\{?([A-Z][A-Z0-9_]*)", atama[0])):
        zincir += [ln for ln in kod if ln.lstrip().startswith(f"{ref}=")]
    assert any("SUDO_USER" in ln for ln in zincir), (
        f"{profil.name}: deploy.sh profil yolunu `$HOME`dan varsayıyor ({atama!r}) — `sudo bash` "
        "altında `/root` çıkar, KURULU profil 'KURULU DEĞİL' raporlanır ve `.env` uyarısı hiç "
        "ateşlenmez; gerçek çağıran `SUDO_USER`dır")


# ---------------------------------------------------------------------------
# KURULUM KAPILARI — HER PROFİLİN KENDİ TİMER'I İÇİN (Faz 3)
#
# v327 bu iki kapıyı `meridian-brifing` için ölçüyor. Aşağıdakiler AYNI iki kapıyı profil
# kümesinden TÜRETEREK ölçer: `cutover.sh` adım 4 `deploy.sh`i çağırıyor, yani "ilgisiz bir
# sebeple koşan dağıtım" GÜNDELİK bir olaydır ve her yeni bot onunla birlikte bir kadans
# AÇMA riski getirir. Kapı ikinci profilde kopyalanmazsa, yeni bot canlıda operatör kararı
# olmadan konuşmaya başlar.
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("profil", _profiller(), ids=lambda p: p.name)
def test_deploy_sh_PROFIL_KADANSINI_KOSULSUZ_ACMAZ(profil):
    """Dosya KURULUMU ile ETKİNLEŞTİRME AYRI EYLEMDİR — teslimat operatör kararıdır.

    Kardeş timer'lar (`meridian-backup`, `meridian-tick-watchdog`) sütun 0'da koşulsuz `enable
    --now` alır; bot timer'ları ALMAZ, çünkü onlar operatöre TELEGRAM MESAJI gönderir. Girinti
    ölçülür: `enable --now <timer>` geçen her satır bir `if` gövdesinin İÇİNDE olmalı."""
    t = _profil_timeri(profil)
    assert t is not None, f"{profil.name}: timer yok (kardeş çivi kırmızıdır)"
    satirlar = [ln for ln in _deploy_kod()
                if f"enable --now {t.name}" in ln and not ln.lstrip().startswith("echo")]
    assert satirlar, (
        f"{profil.name}: deploy.sh `{t.name}`ı hiç enable etmiyor — bir kez açıldıktan sonra "
        "kendini onaran davranış yok, sonraki dağıtımlar kadansı açık TUTMAZ")
    for ln in satirlar:
        assert ln.startswith((" ", "\t")), (
            f"{profil.name}: `{t.name}` KOŞULSUZ enable ediliyor — ilgisiz bir deploy.sh koşumu "
            f"(cutover.sh adım 4) günlük Telegram kadansını operatör kararı olmadan açar: {ln!r}")
    assert f"is-enabled {t.name}" in DEPLOY_SH.read_text(encoding="utf-8"), (
        f"{profil.name}: kapı `is-enabled` üstünde kurulmamış — 'zaten açıksa açık tut' "
        "davranışı ölçülemez ve her dağıtım kadansı kapatabilir")


@pytest.mark.parametrize("profil", _profiller(), ids=lambda p: p.name)
def test_deploy_sh_PROFIL_BIRIMINI_KOSULSUZ_DEVRETMEZ(profil):
    """KURULUM KAPISI, BİR KATMAN YUKARISI — `enable` kapısının ikizi.

    Timer canlıda ZATEN AÇIKSA (bir kez açıldıktan sonra öyle kalır), birim dosyasını koşulsuz
    kopyalamak, ÇALIŞAN bir kadansın NE KOŞTURACAĞINI kimse karar vermeden değiştirir. Kurulum
    zararsız DEĞİLDİR: bu dosya teslimatın kendisini tanımlar."""
    svc = _profil_birimi(profil)
    assert svc is not None, f"{profil.name}: birim yok (kardeş çivi kırmızıdır)"
    satirlar = [ln for ln in _deploy_kod() if svc.name in ln and " cp " in ln]
    assert satirlar, (
        f"{profil.name}: deploy.sh `{svc.name}`ı hiç kurmuyor — taze kurulumda kadans dosyasız "
        "kalır ve timer var olmayan bir birimi tetikler")
    for ln in satirlar:
        assert ln.startswith((" ", "\t")), (
            f"{profil.name}: `{svc.name}` KOŞULSUZ kopyalanıyor — timer zaten açıksa ilgisiz "
            f"bir dağıtım günlük teslimatı kimse karar vermeden değiştirir: {ln!r}")


# ---------------------------------------------------------------------------
# F9 — HER PROFİLİN DOSYALARI SÜRÜKLENME KAPISININ KAPSAMINDA (Faz 3)
#
# v266'daki başlık çivisi TEK YÖNLÜDÜR: `F9_LISTE`deki her ad `deploy.sh` başlığında geçmeli.
# Ters yön AÇIKTI — bir profilin dosyalarını listeye HİÇ EKLEMEMEK hiçbir çiviyi kırmızıya
# döndürmüyordu. Sonuç tam olarak F9'un kapatmak için var olduğu sınıf: repo ilerler, canlıdaki
# KURULU kopya yerinde sayar ve kimse bağırmaz. Roster yediye çıkarken bu yön kapalı olmalı.
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("profil", _profiller(), ids=lambda p: p.name)
def test_F9_PROFILIN_UC_DOSYASINI_IZLIYOR(profil):
    """Profilin üç dosyası da `F9_LISTE`de, ve canlı yanı KURULU kopyayı göstermeli.

    İNCELİK: rsync depo tarafını (`deploy/hermes/profiles/<ad>/`) canlıya taşır, ama F9'un
    kıyasladığı şey o değil `~/.hermes/profiles/<ad>/` altındaki KURULU kopyadır — profil
    canlıya `hermes profile install` ile varır ve o komut operatörün kararıdır. "Repoda güncel"
    ile "botun okuduğu dosya güncel" AYRI iki gerçektir; kapının ölçtüğü ikincisidir."""
    liste = dict(_f9_listesi())
    for ad in ("distribution.yaml", "config.yaml", "SOUL.md"):
        repo_yol = f"deploy/hermes/profiles/{profil.name}/{ad}"
        assert repo_yol in liste, (
            f"{profil.name}: `{repo_yol}` dagit `F9_LISTE`sinde YOK — repo ilerler, botun "
            "canlıda OKUDUĞU kopya yerinde sayar ve hiçbir kapı bağırmaz (OB-2 sınıfı)")
        assert liste[repo_yol] == f"/home/ubuntu/.hermes/profiles/{profil.name}/{ad}", (
            f"{profil.name}: `{repo_yol}` canlı yanı KURULU profili göstermiyor "
            f"({liste[repo_yol]}) — kapı botun okumadığı bir dosyayı kıyaslar")


@pytest.mark.parametrize("profil", _profiller(), ids=lambda p: p.name)
def test_F9_PROFILIN_BIRIM_CIFTINI_IZLIYOR(profil):
    """Profilin `.service` + `.timer` çifti de `F9_LISTE`de olmalı.

    Bu dosyalar dagit'in rsync kapsamı DIŞINDA elle kurulur (`sudo cp` + `daemon-reload`).
    Listede değillerse repodaki bir düzeltme — sertleştirme, safe-root daraltması, saat
    değişikliği — canlıda AYLARCA yürürlüğe girmez ve hiçbir şey bunu söylemez."""
    liste = dict(_f9_listesi())
    for yol in (_profil_birimi(profil), _profil_timeri(profil)):
        assert yol is not None, f"{profil.name}: birim/timer yok (kardeş çivi kırmızıdır)"
        repo_yol = f"deploy/oracle-a1/{yol.name}"
        assert repo_yol in liste, (
            f"{profil.name}: `{repo_yol}` dagit `F9_LISTE`sinde YOK — bu dosya rsync'le "
            "TAŞINMAZ, elle kurulur; listede olmayan bir birim repo↔canlı ayrışmasını sessizce "
            "biriktirir")
        assert liste[repo_yol] == f"/etc/systemd/system/{yol.name}", (
            f"{profil.name}: `{repo_yol}` canlı yanı yanlış ({liste[repo_yol]})")
