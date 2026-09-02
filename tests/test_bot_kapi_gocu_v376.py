"""v376 · BOT KAPI GÖÇÜ (TSK-105 Görev 1) — üç hermes botunun kapıya bağlanmasının REPO yarısı.

BOŞ NUMARA ÖLÇÜLDÜ: `ls tests/ | grep -oE "v[0-9]+" | sort -t v -k2 -n | tail -1` → v375; depo
çapında `v376` hiçbir dosyada/atıfta geçmiyor. Numara KİMLİKTİR, çakışırsa az-çapalı taraf taşınır.

NEDEN AYRI DOSYA. v361 kapının PANO VEKİLİNİ ölçer (okuma yüzeyi), v364 `apisix_uygula.py`nin
TÜKETİCİ desteğini, v329 bot profillerinin GÜVENLİK DURUŞUNU. Bu dosyanın ölçtüğü şey üçünün de
dışında: botun kimliğinin kapıdan GEÇEBİLİYOR olması — yani `routes.yaml`daki köprü ile üç
profildeki sağlayıcı beyanının BİRBİRİNİ TUTMASI. İki belge iki dosyada yaşıyor ve ayrıştıklarında
belirti şudur: bot 401 alır, sıralama katmanı sessizce ham yola düşer.

NE ÖLÇÜLMÜYOR, ADIYLA (uydurma yasağı):
  · LUA KOŞULMUYOR. `serverless-pre-function`ın gövdesi APISIX'in içinde koşan Lua'dır; bu
    makinede ne APISIX var ne LuaJIT. Aşağıdaki köprü çivisi bu yüzden bir YAPI + İMZA + SIRA
    çivisidir: fonksiyonun `apikey` yokken `Bearer ` önekini soyup başlığı kurduğunu, ve `apikey`
    VARKEN dokunmadığını METİN DÜZENİNDEN okur. Davranış kanıtı UYGULAMA CANARY'sindedir
    (bot smoke → 9091 sayacında `consumer=bot_*`).
  · KAPININ GERÇEK ÖNCELİK SIRASI ölçülmedi. `serverless-pre-function` (rewrite) ile `key-auth`ın
    hangisinin önce koştuğu APISIX'in plugin önceliğine bağlıdır ve o da ancak canlıda ölçülür;
    yanlışsa canary 401 verir — SESSİZ ARIZA DEĞİL.
  · HERMES'İN `Authorization: Bearer` GÖNDERDİĞİ, OpenAI-uyumlu istemci sözleşmesinden gelen bir
    ÇIKARIMDIR (kaynak okuması: `hermes_cli/runtime_provider.py` çözülen `api_key`i standart
    istemciye veriyor). Yanlışsa köprü boşa düşer ve yine canary 401'i görülür.
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

import pytest
import yaml

KOK = pathlib.Path(__file__).resolve().parents[1]
if str(KOK) not in sys.path:
    sys.path.insert(0, str(KOK))

from tests.conftest import betikten_modul_yukle  # noqa: E402

ROTA_KAYNAGI = KOK / "deploy" / "apisix" / "routes.yaml"
KAPI_CONFIG = KOK / "deploy" / "apisix" / "config.yaml"
PROFIL_KOKU = KOK / "deploy" / "hermes" / "profiles"
BETIK = KOK / "ops" / "apisix_uygula.py"

# Botun kapıya bakan tabanı. A1-İÇİ loopback: kapı 9080'i dışarı açmaz, bot ile kapı aynı
# makinededir. `/llm/v1` seçildi çünkü hermes buna `/chat/completions` (llm-danisma) ve `/models`
# (llm-models, nous sağlık sondası) ekler — iki uç da bu önekte tanımlı.
KAPI_TABANI = "http://127.0.0.1:9080/llm/v1"
SAGLAYICI_ADI = "kapi"          # `providers:` girdisinin adı; profil onu `custom:kapi` ile seçer


# --------------------------------------------------------------------------- kaynak okuyucular

def _routes() -> dict:
    return yaml.safe_load(ROTA_KAYNAGI.read_text(encoding="utf-8")) or {}


def _llm_rotalari() -> list[dict]:
    """LLM rotaları KÜME OLARAK TÜRETİLİR, ad listesi yazılmaz.

    Üç kimliği (`llm-danisma`/`llm-hizli`/`llm-models`) literal yazan bir çivi, dördüncü LLM
    rotası doğduğu gün SESSİZCE kör kalırdı — bu deponun tekrarlayan hata deseni (v266, v329).
    Ölçüt `uri`nin `/llm/` önekidir: kapının LLM egress yüzeyi tam olarak budur.
    """
    return [r for r in (_routes().get("rotalar") or [])
            if str(r.get("uri", "")).startswith("/llm/")]


def _profiller() -> list[pathlib.Path]:
    """v329 ile AYNI kapsam kuralı: `distribution.yaml` taşıyan dizinler."""
    if not PROFIL_KOKU.is_dir():
        return []
    return sorted(p for p in PROFIL_KOKU.iterdir() if (p / "distribution.yaml").is_file())


def _tuketici_env_adlari() -> dict[str, str]:
    """`{tüketici adı: key-auth anahtarının ENV ADI}` — routes.yaml'ın kendi beyanından.

    Profilin `key_env`i BURADAN doğrulanır, "büyük harfe çevir" kuralından DEĞİL: iki belge
    (kapının tüketicisi ↔ botun profili) ayrı dosyalarda yaşıyor ve ayrıştıklarında bot 401
    alır. Türetim, ayrışmayı çivinin kendisi yakalasın diye var.
    """
    out: dict[str, str] = {}
    for t in (_routes().get("tuketiciler") or []):
        anahtar = ((t.get("plugins") or {}).get("key-auth") or {}).get("key")
        if isinstance(anahtar, str) and anahtar.startswith("$env://"):
            out[str(t.get("username"))] = anahtar[len("$env://"):]
    return out


def _kapinin_sundugu_modeller() -> set[str]:
    """Kapının `ai-proxy-multi` instance'larında SABİTLENMİŞ model adları."""
    modeller: set[str] = set()
    for r in (_routes().get("rotalar") or []):
        multi = (r.get("plugins") or {}).get("ai-proxy-multi") or {}
        for inst in (multi.get("instances") or []):
            m = (inst.get("options") or {}).get("model")
            if isinstance(m, str) and m:
                modeller.add(m)
    return modeller


def _beyan_edilen_pluginler() -> list[str]:
    """`deploy/apisix/config.yaml`ın `plugins:` listesi — kapının AÇIK plugin beyanı."""
    veri = yaml.safe_load(KAPI_CONFIG.read_text(encoding="utf-8")) or {}
    return [str(p) for p in (veri.get("plugins") or [])]


def _kullanilan_pluginler() -> dict[str, list[str]]:
    """`{plugin adı: [kullanıldığı yerler]}` — routes.yaml'ın ÜÇ bölümünden birden.

    Yalnız `rotalar`a bakan bir tarama eksik olurdu: `tuketici_gruplari` (`limit-count`) ve
    `tuketiciler` (`key-auth`) de plugin ADI taşır ve aynı 400'ü üretebilir.
    """
    veri = _routes()
    out: dict[str, list[str]] = {}
    for bolum, kimlik in (("rotalar", "id"), ("tuketici_gruplari", "id"),
                          ("tuketiciler", "username")):
        for kalem in (veri.get(bolum) or []):
            for ad in (kalem.get("plugins") or {}):
                out.setdefault(str(ad), []).append(f"{bolum}/{kalem.get(kimlik)}")
    return out


def _cfg(profil: pathlib.Path) -> dict:
    return yaml.safe_load((profil / "config.yaml").read_text(encoding="utf-8")) or {}


def _kopru(rota: dict) -> dict:
    return (rota.get("plugins") or {}).get("serverless-pre-function") or {}


# --------------------------------------------------------------------------- A. VAKUM KAPILARI

def test_LLM_ROTA_KUMESI_BOS_DEGIL():
    """Kapsam boşsa altındaki parametreli çiviler VACUOUSLY yeşil olurdu: sıfır rota, sıfır ihlal."""
    assert _llm_rotalari(), (
        f"{ROTA_KAYNAGI} içinde `/llm/` önekli rota YOK — köprü çivilerinin hiçbiri bir şey "
        "ölçmüyor demektir (uri şeması mı değişti?)")


def test_PROFIL_KUMESI_BOS_DEGIL():
    assert _profiller(), (
        f"{PROFIL_KOKU} altında `distribution.yaml` taşıyan profil YOK — profil çivileri vakumda")


def test_ROTALARDA_KULLANILAN_HER_PLUGIN_KAPI_CONFIGINDE_BEYANLI():
    """VAKA 2026-09-02 (uygulama penceresi) — v376'nın ilk turdaki KÖR NOKTASI.

    Bu dosyanın on küsur çivisi routes.yaml'ı baştan sona doğru buldu ve `apisix_uygula
    --uygula` yine de **400 "unknown plugin"** ile düştü: `deploy/apisix/config.yaml`ın
    `plugins:` listesi varsayılanı EZER, yani orada adı geçmeyen bir plugin APISIX'te YOKTUR.
    `serverless-pre-function` o listeye yazılmamıştı. Düzeltme canlıda yapıldı (a751c07).

    KUSURUN SINIFI, ADIYLA: iki dosya arasında ZORLAYICI bir bağ vardı ve hiçbir çivi onu
    görmüyordu — routes.yaml "bu plugin'i kullanıyorum" der, config.yaml "bu plugin var" der,
    ve ikisi ayrıştığında belirti dağıtım ANINDA çıkar (sessiz değil, ama GEÇ: pencere açık,
    operatör bekliyor, teşhis Admin API'nin tek satırlık hata gövdesinde). Bu çivi o bağı
    dağıtımdan ÖNCEYE, repoya çeker.

    KÜME TÜRETİLİR: plugin adları üç bölümün `plugins` bloklarından okunur, liste yazılmaz —
    yarın doğacak bir Faz plugin'i bu çiviyi kendiliğinden kapsar. Tuzağı yeniden kuracak olan
    "routes'a plugin ekleyen herkes"tir, ve tam da o an bu çivi kırmızıya döner.
    """
    kullanilan = _kullanilan_pluginler()
    beyanli = _beyan_edilen_pluginler()
    assert kullanilan, (
        f"{ROTA_KAYNAGI} hiçbir plugin kullanmıyor görünüyor — çivi vakumda (şema mı değişti?)")
    assert beyanli, (
        f"{KAPI_CONFIG} `plugins:` listesi BOŞ/YOK — liste varsayılanı EZER, yani bu hâlde "
        "kapıda HİÇBİR plugin çalışmaz; kıyas da anlamsızlaşır")

    eksik = {ad: yerler for ad, yerler in kullanilan.items() if ad not in beyanli}
    assert not eksik, (
        "routes.yaml'da KULLANILAN ama `deploy/apisix/config.yaml` `plugins:` listesinde "
        f"BEYAN EDİLMEYEN plugin(ler): "
        + " · ".join(f"`{ad}` ({', '.join(yerler)})" for ad, yerler in sorted(eksik.items()))
        + ". Liste varsayılanı EZER: beyansız plugin APISIX'te YOKTUR ve `apisix_uygula "
        "--uygula` 400 `unknown plugin` ile düşer (VAKA 2026-09-02, düzeltme a751c07). "
        "Adı config.yaml'a ekle — 'varsayılan zaten açıktı' yok.")


# ------------------------------------------------------------------- B. KAPIDAKİ KÖPRÜ

@pytest.mark.parametrize("rota", _llm_rotalari(), ids=lambda r: r["id"])
def test_LLM_ROTASI_BEARER_KOPRUSU_TASIR(rota):
    """Köprü KAPIDA durur, hermes tarafında DEĞİL — ve gerekçesi ölçülmüştür.

    Hermes'in `extra_headers` alanı ENV GENİŞLETMESİ YAPMAZ (`hermes_cli/config.py::
    normalize_extra_headers` literal değer taşır), yani botun `apikey` başlığını repo'daki bir
    profile yazmanın tek yolu SIRRIN KENDİSİNİ repoya koymaktır. O yol kapalı. Kalan yol: bot
    standart `Authorization: Bearer <anahtar>` gönderir, kapı onu `apikey`e çevirir. Böylece
    tanım TEK KAYNAKTA (routes.yaml) kalır ve drift denetimi (`apisix_uygula --denetle`) kapsar.
    """
    k = _kopru(rota)
    assert k, (
        f"{rota['id']}: `serverless-pre-function` YOK — bot `Authorization: Bearer` gönderir, "
        "`key-auth` `apikey` bekler; köprüsüz rota botu 401'e düşürür ve sıralama katmanı "
        "sessizce ham yola iner")
    assert k.get("phase") == "rewrite", (
        f"{rota['id']}: köprünün fazı {k.get('phase')!r} — `rewrite` olmalı. Başlık kimlik "
        "doğrulamasından ÖNCE kurulmazsa `key-auth` hâlâ eksik başlığı görür")
    fns = k.get("functions")
    assert isinstance(fns, list) and fns and all(isinstance(f, str) and f.strip() for f in fns), (
        f"{rota['id']}: `functions` bir dolu dize listesi değil: {fns!r}")


@pytest.mark.parametrize("rota", _llm_rotalari(), ids=lambda r: r["id"])
def test_KOPRU_BEARER_SOYAR_ve_MEVCUT_APIKEYE_DOKUNMAZ(rota):
    """YAPI + İMZA + SIRA çivisi. LUA KOŞULMUYOR (dosya başlığındaki beyan) — ölçülen şey
    fonksiyonun METİN DÜZENİdir, ve düzen üç şey söyler:

      (1) `apikey` başlığı YOKSA yazılır — yani motorun bugünkü yolu (apikey ile gelen
          `motor_meridian`) köprüden ETKİLENMEZ. Bu sıra ters olsaydı köprü, motorun kendi
          anahtarını istemcinin `Authorization`ıyla EZERDİ ve regresyon sessiz olurdu.
      (2) Önek `Bearer ` (yedi karakter) SOYULUR — `sub(1, 7)` kıyası + `sub(8)` dilimi.
          Soyulmazsa kapıya giden anahtar `Bearer sk-...` olur ve `key-auth` eşleşmez.
      (3) Başlık `apikey` ADIYLA kurulur — `key-auth`ın varsayılan başlığı budur.
    """
    govde = "\n".join(_kopru(rota).get("functions") or [])
    assert govde.strip(), f"{rota['id']}: köprü gövdesi boş (kardeş çivi kırmızıdır)"

    kur = re.search(r"set_header\(\s*[\"']apikey[\"']", govde)
    assert kur, (
        f"{rota['id']}: gövde `apikey` başlığını KURMUYOR — `key-auth` başka bir başlık adına "
        f"bakmaz. Gövde: {govde!r}")
    assert re.search(r"[\"']Bearer [\"']", govde), (
        f"{rota['id']}: `Bearer ` öneki gövdede geçmiyor — soyulmayan önek `key-auth`ın "
        "eşleşmesini bozar")
    assert re.search(r"sub\(\s*1\s*,\s*7\s*\)", govde) and re.search(r"sub\(\s*8\s*\)", govde), (
        f"{rota['id']}: önek dilimlemesi (`sub(1, 7)` kıyası + `sub(8)` gövdesi) yok — "
        f"`Bearer ` yedi karakterdir ve elle sayılan bir ofset sessizce kayar. Gövde: {govde!r}")

    kapi = re.search(r"not\s+h\[[\"']apikey[\"']\]", govde)
    assert kapi, (
        f"{rota['id']}: `apikey` VARKEN atlayan kapı yok — köprü motorun kendi anahtarını "
        f"istemcinin `Authorization`ıyla ezebilir. Gövde: {govde!r}")
    assert kapi.start() < kur.start(), (
        f"{rota['id']}: `apikey` kapısı başlığı KURDUKTAN sonra sınanıyor — sıra ters, kapı "
        "hiçbir şey korumuyor")


def test_KOPRU_GOVDESI_UC_ROTADA_AYNIDIR():
    """Üç gövde bugün bit-eş; bunu ZORLAYAN bir şey yoktu (düzeltme turu 1, inceleme kalemi).

    APISIX plugin gövdeleri rota-BAŞINADIR, yani kopya kaçınılmaz — tek-kaynak yasasının
    ikinci yarısı burada devreye girer: kopya kaçınılmazsa AYRIŞMA ÇİVİSİ şart. Ayrışmanın
    belirtisi en kötü türden olurdu: iki rota doğru davranır, biri sapar; bot çağrı sınıfına
    göre bazen 401 alır, bazen almaz — yani arıza ARALIKLI ve kadansa bağlı görünür.
    """
    rotalar = _llm_rotalari()
    ilk = rotalar[0]
    ilk_govde = _kopru(ilk).get("functions")
    ayrik = [r["id"] for r in rotalar[1:] if _kopru(r).get("functions") != ilk_govde]
    assert not ayrik, (
        f"köprü gövdesi `{ilk['id']}`den AYRIŞAN rota(lar): {ayrik} — kimlik yolu rotaya göre "
        "değişemez; sapan rotada bot 401 alır ve arıza yalnız o çağrı sınıfında görünür")


@pytest.mark.parametrize("rota", _llm_rotalari(), ids=lambda r: r["id"])
def test_LLM_ROTASI_KIMLIGI_UPSTREAME_SIZDIRMAZ(rota):
    """`key-auth` VARSAYILANI `hide_credentials: false`tur — yani doğrulanan `apikey` başlığı
    upstream'e (OpenRouter'a) OLDUĞU GİBİ gider. Bu, göçten ÖNCE de açıktı ve göç onu
    büyütür: bugün yalnız motorun anahtarı geçiyor, göçten sonra üç botunki de geçerdi.

    `Authorization`ı `proxy-rewrite` zaten siliyor; `apikey`i hiçbir şey silmiyordu.
    Kapanışın CANLI doğrulaması uygulama canary'sindedir (üç başlığın da upstream'e gitmediği).
    """
    ka = (rota.get("plugins") or {}).get("key-auth")
    assert isinstance(ka, dict), (
        f"{rota['id']}: `key-auth` yok ya da eşleme değil ({ka!r}) — F4-B kilidi bu rotada düşmüş")
    assert ka.get("hide_credentials") is True, (
        f"{rota['id']}: `key-auth.hide_credentials` {ka.get('hide_credentials')!r} — `true` "
        "olmalı; aksi halde tüketici anahtarı doğrulandıktan SONRA üçüncü tarafa iletilir")


# ------------------------------------------------------------------ C. PROFİL TARAFI

@pytest.mark.parametrize("profil", _profiller(), ids=lambda p: p.name)
def test_PROFIL_KAPI_SAGLAYICISINI_BEYAN_EDER(profil):
    """Botun sağlayıcı girdisi: taban KAPI, anahtar ADIYLA (değeri A1 bot env'inde).

    `key_env` deseni SEÇİLDİ çünkü alternatifi sırrın repoya girmesiydi (`extra_headers` env
    genişletmez — ölçüldü). Bu satır bir anahtar TAŞIMAZ, anahtarın ADINI taşır.
    """
    saglayici = ((_cfg(profil).get("providers") or {}).get(SAGLAYICI_ADI))
    assert isinstance(saglayici, dict), (
        f"{profil.name}: `providers.{SAGLAYICI_ADI}` YOK — `model.provider: custom:{SAGLAYICI_ADI}` "
        "hiçbir girdiye çözülmez ve hermes sessizce başka bir sağlayıcıya düşer")
    assert saglayici.get("base_url") == KAPI_TABANI, (
        f"{profil.name}: kapı tabanı {saglayici.get('base_url')!r} — beklenen {KAPI_TABANI!r}. "
        "Yanlış taban botu doğrudan üçüncü tarafa geri gönderir ve filo kotası onu SAYMAZ")

    bekleyen = _tuketici_env_adlari().get(f"bot_{profil.name}")
    assert bekleyen, (
        f"{profil.name}: routes.yaml'da `bot_{profil.name}` tüketicisi `$env://` referanslı bir "
        "`key-auth` anahtarı beyan etmiyor — profilin `key_env`i neye eşit olacağı ÖLÇÜLEMEZ")
    assert saglayici.get("key_env") == bekleyen, (
        f"{profil.name}: `key_env` {saglayici.get('key_env')!r}, kapının tüketicisi ise "
        f"{bekleyen!r} okuyor — iki belge ayrıştı, bot 401 alır ve düşüş SESSİZDİR (harness ham "
        "yola iner)")


@pytest.mark.parametrize("profil", _profiller(), ids=lambda p: p.name)
def test_BOTUN_GERCEKTEN_OKUDUGU_ANAHTAR_BEYAN_EDILIR(profil):
    """BEYAN, KOŞUMUN OKUDUĞU ANAHTARI ADLANDIRMALI (düzeltme turu 1, inceleme kalemi YÜKSEK).

    Göçten sonra hermes `OPENROUTER_API_KEY`i OKUMUYOR: sağlayıcı `custom:kapi`, anahtar
    `providers.kapi.key_env` ile gelir. Manifest hâlâ yalnız eski adı `required` beyan
    ediyorsa iki şey birden olur ve ikisi de SESSİZDİR:
      · `install` üretilen `.env.EXAMPLE`e YANLIŞ anahtarı yazar; operatör reçeteyi harfiyen
        izler, doğru anahtarı hiç doldurmaz ve bot her koşumda 401 alıp ham yola düşer —
        "çalışıyor" görünür (bu profillerin bütün var oluş sebebi o sınıfı görünür kılmaktı),
      · v329'un `test_CALISMAK_ICIN_GEREKEN_ANAHTAR_BEYAN_EDILIR` çivisi YEŞİL kalır, çünkü o
        yalnız eski adın VARLIĞINI ölçer — yani beyan bayatlar ve çivi bayatlığı örter.

    ÖLÇÜT ADI LİTERAL DEĞİL: beklenen ad profilin KENDİ `config.yaml`ındaki `key_env`den
    okunur. Dördüncü bot ya da yeniden adlandırılmış bir anahtar bu çiviyi kendiliğinden
    kapsar; literal bir liste bayatlar ve bayatlaması sessiz olurdu.
    """
    key_env = ((_cfg(profil).get("providers") or {}).get(SAGLAYICI_ADI) or {}).get("key_env")
    assert key_env, f"{profil.name}: `providers.{SAGLAYICI_ADI}.key_env` yok (kardeş çivi kırmızıdır)"

    man = yaml.safe_load((profil / "distribution.yaml").read_text(encoding="utf-8")) or {}
    beyanlar = {str(e.get("name")): e for e in (man.get("env_requires") or [])
                if isinstance(e, dict)}
    e = beyanlar.get(key_env)
    assert e is not None, (
        f"{profil.name}: koşumun GERÇEKTEN okuduğu anahtar `{key_env}` manifestte beyan "
        f"EDİLMEMİŞ (beyan edilenler: {sorted(beyanlar)}) — `.env.EXAMPLE` onu üretmez, "
        "operatör doldurmaz, bot 401 alıp sessizce ham yola düşer")
    assert e.get("required") is True, (
        f"{profil.name}: `{key_env}` beyanı `required: true` değil ({e.get('required')!r}) — "
        "opsiyonel bir anahtar reçetede 'isteğe bağlı' okunur, oysa o anahtar olmadan bu bot "
        "kapıdan HİÇ geçemez")

    # İkinci belge: operatörün dağıtım anında okuduğu reçete. Ad profile ÖZGÜdür, yani bu
    # kıyas kardeş botun satırıyla yanlışlıkla yeşile dönemez (v329'un ölçülmüş körlük sınıfı).
    dagit = (KOK / "deploy" / "oracle-a1" / "deploy.sh").read_text(encoding="utf-8")
    assert key_env in dagit, (
        f"{profil.name}: `deploy.sh` reçetesi hâlâ `{key_env}` demiyor — manifest ile dağıtım "
        "betiği ayrıştı ve bayatlayan taraf hep operatörün okuduğu taraf olur")


@pytest.mark.parametrize("profil", _profiller(), ids=lambda p: p.name)
def test_PROFIL_SIRRIN_KENDISINI_TASIMAZ(profil):
    """Sağlayıcı girdisi anahtarın ADINI taşır, DEĞERİNİ değil. `api_key` alanı (hermes'in
    kabul ettiği satır-içi biçim) bu dosyalarda YASAKTIR: `deploy/` versiyonlanır."""
    saglayici = ((_cfg(profil).get("providers") or {}).get(SAGLAYICI_ADI)) or {}
    assert "api_key" not in saglayici, (
        f"{profil.name}: `providers.{SAGLAYICI_ADI}.api_key` var — satır-içi anahtar depoya "
        "girer. Anahtar yalnız `key_env` ADIYLA anılır, değeri A1 bot env'indedir")


@pytest.mark.parametrize("profil", _profiller(), ids=lambda p: p.name)
def test_PROFIL_MODEL_SAGLAYICISI_KAPIYA_BAKAR(profil):
    """Flip'in kendisi. `custom:<ad>` biçimi ÖLÇÜLDÜ (`hermes_cli/runtime_provider.py::
    _get_named_custom_provider`, yerel kaynak v0.18.2): istenen ad `{ep_name, name_norm,
    f"custom:{name_norm}"}` kümesiyle karşılaştırılır, yani `providers.kapi` girdisi
    `custom:kapi` ile seçilir. Çıplak `kapi` de eşleşirdi ama menü anahtarının kanonik
    biçimi budur ve satıcının kendi belgesi ":<ad>" ekini ŞART koşuyor.
    """
    saglayici = str((_cfg(profil).get("model") or {}).get("provider") or "")
    assert saglayici == f"custom:{SAGLAYICI_ADI}", (
        f"{profil.name}: `model.provider` {saglayici!r} — `custom:{SAGLAYICI_ADI}` olmalı. "
        "`openrouter` kaldıysa bot kapıyı ATLAR: filo kotası (limit-count 1000/gün) onu saymaz "
        "ve kapının sayacında hiç görünmez")


@pytest.mark.parametrize("profil", _profiller(), ids=lambda p: p.name)
def test_PROFIL_KUNYESI_KAPININ_SUNDUGU_MODELI_ADLANDIRIR(profil):
    """`model.default` GÖÇTE DEĞİŞMEZ — ve değişmediği, kapının kendi beyanına bağlanarak ölçülür.

    v361 ölçümü: `ai-proxy-multi` instance'ları `options.model`i SABİTLER, yani istemcinin model
    alanı kapıda EZİLİR ve gerçek modeli zincir seçer. Buna rağmen künye ölü bir alan DEĞİLDİR:
    `obs` kayıtlarında ve fallback anında operatörün gördüğü ad odur. Kapının sunmadığı bir adı
    yazmak, o kaydı sessizce YALANA çevirir. (Fallback anında künyenin BİRİNCİL adı göstermesi
    bilinen sınırdır — TSK-089 kaydıyla aynı.)
    """
    kunye = str((_cfg(profil).get("model") or {}).get("default") or "")
    sunulan = _kapinin_sundugu_modeller()
    assert sunulan, "routes.yaml hiçbir `ai-proxy-multi` instance modeli beyan etmiyor — çivi ölçemez"
    assert kunye in sunulan, (
        f"{profil.name}: `model.default` {kunye!r} kapının sunduğu modeller arasında YOK "
        f"({sorted(sunulan)}) — künye kapının gerçekte koşturduğu modeli adlandırmıyor")


@pytest.mark.parametrize("profil", _profiller(), ids=lambda p: p.name)
def test_ZAMAN_ASIMI_HERMESIN_GOCTEN_SONRA_ARADIGI_ANAHTARDA(profil):
    """GÖÇÜN SESSİZ BEDELİ, ve kapağı.

    ÖLÇÜLDÜ (yerel hermes kaynağı v0.18.2 — canlı v0.19.0, sürüm farkı beyan edilir):
    adlandırılmış custom sağlayıcı çözüldüğünde runtime sözlüğü `{"provider": "custom", …}`
    döner (`runtime_provider.py::_resolve_custom_provider_runtime`), çağıran onu `agent.provider`
    yapar (`cli_agent_setup_mixin.py` ve `hermes_cli/oneshot.py` — botlar `-z`, yani oneshot
    yolundan koşar) ve zaman aşımı O DİZGEYLE aranır:
    `timeouts.py::get_provider_request_timeout` → `config["providers"]["custom"]`.

    Yani `providers.kapi` çözümlemeyi taşır ama zaman aşımını TAŞIMAZ. Kapak `providers.custom`
    altındadır. Kapak olmasa arıza şöyle görünürdü: hiçbir çivi kırmızı değil, hiçbir kayıt
    düşmüyor, ve asılan bir upstream'de bot 120 sn yerine istemci varsayılanı kadar bekliyor.
    """
    saglayicilar = (_cfg(profil).get("providers") or {})
    canli = (saglayicilar.get("custom") or {}).get("request_timeout_seconds")
    assert isinstance(canli, (int, float)) and canli > 0, (
        f"{profil.name}: `providers.custom.request_timeout_seconds` yok ({canli!r}) — göçten "
        "sonra hermes zaman aşımını TAM BU anahtarda arar; başka yerdeki bir değer okunmaz")

    beyanlar = {v["request_timeout_seconds"] for v in saglayicilar.values()
                if isinstance(v, dict) and v.get("request_timeout_seconds") is not None}
    assert len(beyanlar) == 1, (
        f"{profil.name}: dosyada BİRDEN FAZLA zaman aşımı değeri var ({sorted(beyanlar)}) — "
        "aynı gerçeğin iki kopyası sessizce ayrışır (tek-kaynak yasası). Değer tek yerde "
        "yazılır, ötekiler YAML çapasıyla ondan türer")


# ------------------------------------------------------- D. ARAÇ KÖPRÜYÜ TAŞIYABİLİYOR MU

def test_ARAC_KOPRUYU_PUT_GOVDESINDE_AYNEN_TASIR(monkeypatch):
    """`ops/apisix_uygula.py` yeni plugin'i TAŞIYOR mu — süzgeçten mi geçiriyor?

    Betik `plugins`i olduğu gibi aktarıyor (beyaz liste yok), ama bu bir SÖZLEŞMEDİR ve
    sözleşmeler yazılmadıkça denetlenmez: bir gün "yalnız bildiğimiz plugin'leri gönderelim"
    diye bir süzgeç eklense köprü etcd'ye HİÇ gitmez, `--uygula` 200 döner ve botlar 401 alır.

    AĞ YOK, DOSYA YAZIMI YOK: `urlopen` ile `anahtar()` saplanır (v364 deseni), girdi GERÇEK
    `routes.yaml`dır. Betik pytest DIŞINDA koşulmaz — `meridian.obs`a hiç dokunmuyor (ithal
    etmiyor), ama kural kuraldır: burada da yalnız `main()` çağrılır, kabuktan değil.
    """
    mod = betikten_modul_yukle(BETIK, "apisix_uygula_v376")
    monkeypatch.setattr(mod, "anahtar", lambda: "SAHTE-ADMIN-ANAHTARI-v376")

    cagrilar: list[dict] = []

    class _Cevap:
        status = 200

        def read(self) -> bytes:
            return json.dumps({"list": []}).encode()

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    def _sahte_urlopen(req, timeout=None):
        cagrilar.append({"method": req.get_method(), "url": req.full_url,
                         "govde": json.loads(req.data.decode()) if req.data else None})
        return _Cevap()

    monkeypatch.setattr(mod.urllib.request, "urlopen", _sahte_urlopen)
    assert mod.main(["--uygula"]) == 0

    putlar = {c["url"].rsplit("/", 1)[-1]: c["govde"] for c in cagrilar
              if c["method"] == "PUT" and "/routes/" in c["url"]}
    for rota in _llm_rotalari():
        govde = putlar.get(rota["id"])
        assert govde is not None, f"{rota['id']}: rota HİÇ PUT edilmedi ({sorted(putlar)})"
        assert govde["plugins"] == rota["plugins"], (
            f"{rota['id']}: PUT gövdesindeki `plugins` routes.yaml'dakiyle BİREBİR değil — "
            "araç bir süzgeç uyguluyor, yani beyan edilen köprü etcd'ye eksik gidiyor")

    assert not [c for c in cagrilar if "ttl" in c["url"]], "`?ttl=` YASAK (kaynağı sessizce siler)"


def test_KOPRU_DRIFT_KIYASINA_GIRER():
    """Köprü `--denetle` kapsamında MI? `_normalize` yalnız beyan ettiğimiz alanları kıyaslıyor;
    `plugins` bütün olarak girmezse elle silinmiş bir köprü drift üretmez ve göç sessizce geri
    alınmış olur (kapı 401 verir, kimse nedenini bilmez)."""
    mod = betikten_modul_yukle(BETIK, "apisix_uygula_v376_norm")
    rota = next(iter(_llm_rotalari()))
    kopru_suz = {k: v for k, v in rota["plugins"].items() if k != "serverless-pre-function"}
    assert mod._normalize(rota) != mod._normalize({**rota, "plugins": kopru_suz}), (
        "köprüsü sökülmüş rota ile beyan edilen rota `_normalize` gözünde AYNI görünüyor — "
        "drift denetimi bu değişikliğe KÖR")
