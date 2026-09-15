"""v493 TSK-189 — YEDEK BEYİN ÖLÜ BİR ADA ÇİVİLENMİŞTİ (OpenRouter 404), varsayılanı da uydurmaydı.

ÖLÇÜLEN ARIZA (Rol-1, A1 `state/events.jsonl`, 2026-09-14 22:1xZ): `agent_call_empty` /
`review_fallback_empty` (kind=review|backfill, chain=2) 2026-09-02'den beri GÜNDE 12-26 kez
düşüyor. Sebep tek satır: OpenRouter `openai/gpt-oss-20b:free` için
"HTTP 404: This model is unavailable for free. The paid version is available now" döndürüyor —
yani YEDEK beyin ÖLÜ. Birincil (`nvidia/nemotron-3-super-120b-a12b:free`) sağ; zincirin ikinci
ayağı her düşüşte boşa çakılıyordu, "yedek var" görüntüsü GERÇEK DEĞİLDİ.

İKİNCİ, DAHA SESSİZ KUSUR: `hermes.config_ensure_integrations` hermes CLI config'ine
`fallback_providers` yazarken sırrı HAM alıyordu (`secrets.get(...) or "tencent/hy3:free"`) —
yani (a) ölü-ad göçünden GEÇMİYORDU ve (b) gömülü varsayılanın kendisi de ölü/uydurma bir addı
(ROADMAP §7 2026-08-14: `tencent/hy3` OpenRouter katalogunda HİÇ var olmadı). `_nous_model_zinciri`
çağrı anında göçürüyordu, config yüzeyi göçürmüyordu: aynı gerçeğin ikinci evi.

YENİ VARSAYILAN — SEÇİM ÖLÇÜMLE (A1 sondası 2026-09-14, tek çağrı): `nex-agi/nex-n2.5-mini:free`
bayraksız HTTP 200 · finish=stop · 48 token · 0,6 s DOLU cevap. `nvidia/nemotron-3.5-lightning:free`
yalnız `reasoning.enabled=false` ile dolu döndü ve hermes CLI yolu o bayrağı TAŞIMIYOR → seçilmedi.
Rol-1 kararı ayrıca üst-akım AYRIMI arar: aynı gece 22:03Z Nvidia "temporarily overloaded" 502 ×2
verdi — aynı havuzdan alınan yedek yedeklilik DEĞİLDİR (`hermes.brain_chain_facts` docstring'inin
ölçtüğü yanılsama). Bu yüzden T6 satıcı önekini çivi altına alır.

BU DOSYA ÇİVİLER:
  T1  bilinen-ölü iki ad (gpt-oss-20b, hy3) kanonik yedeğe göçer;
  T2  çağrı-anı zinciri ölü YEDEĞİ göçürür ve OLAYLAR (sessiz değiştirme yasak);
  T3  iki sır da aynı ölü ada bakıyorsa zincir TEKE iner (sahte yedeklilik yok);
  T4  config yüzeyi de aynı kanonik adı yazar — sır ölü olsa da, sır hiç yokken de;
  T5  `deploy/hermes/config.yaml` ile kod sabiti TEK KAYNAKTAN türer (iki kopya ayrışmaz);
  T6  yedeğin kendisi ücretsiz ve BİRİNCİLDEN FARKLI üst-akımdan;
  T7  yeni varsayılan ölü listesine düşerse çivi öter (kendi kuyruğunu yiyen göç yok);
  T8  PORTAL ayağı da göçürür ve künye ile istek gövdesi TEK kaynaktan gelir (2026-09-15);
  T9  RAPOR yüzeyi (`_model_id("nous")`) aynı kapıdan okur ama defter YAZMAZ (2026-09-15).

T9 NEDEN GEREKTİ (öneri havuzu, TSK-189 kapanış notu): T8 portal adını `_nous_portal_model`de
tek kaynağa bağlarken `_model_id`in portal dalı aynı çözümlemeyi (sır → göç → varsayılan) ELLE
İKİNCİ KEZ yazıyordu. İki ifade ölçüldüğü gün aynı adı üretiyordu — yani hiçbir davranış çivisi
onları ayıramazdı — ama göç haritası ya da varsayılan değiştiğinde sessizce ayrışırlardı
(tek-kaynak yasası; Sonnet inceleme bulgusu). Dal artık delege ediyor; ayrım tek bir bayrakta
kaldı: `olay=False`. T9b bu DELEGASYONU ölçer (sahte dönüş yansımazsa kırmızı) — davranış çivisi
T9a tek başına eski, kopyalı ifadede de yeşil kalırdı.

T8 NEDEN SONRADAN GELDİ: TSK-189 kapsamı yedek (`_nous_model_zinciri`) ve config yüzeyleriydi;
portal ayağı (`_nous_portal_model`) açık kalemdi ve docstring'i bunu dürüstçe beyan ediyordu.
Kapanışın bedeli ölçülmüştü: bu ayağın adı künye sözleşmesine de giriyor (`chain_text` künyesi
aynı fonksiyondan okur), yani göç buraya taşınınca istek gövdesi ile künye AYNI kanonik adı
görmek ZORUNDA — ikisi ayrışırsa "ne çağırdık / ne rapor ettik" sınıfı geri gelir. T8b tam bu
sözleşmeyi ölçer; T8a olayın süreç başına BİR kez basıldığını (sessiz değiştirme yasağı ama
alarm gürültüsü de yok), T8c tanınmayan adın serbest geçtiğini çiviler.
"""
from __future__ import annotations

import inspect
import json

import httpx
import yaml

from meridian import hermes, store

# A1 sondasında sağ ölçülen birincil (zincirin BİRİNCİ ayağı) — T2/T6 bunun üstünden konuşur.
BIRINCIL = "nvidia/nemotron-3-super-120b-a12b:free"
OLU_YEDEK = "openai/gpt-oss-20b:free"          # 404: "unavailable for free" (canlı, 2026-09-02+)
OLU_ESKI = "tencent/hy3:free"                  # katalogda HİÇ olmadı (ROADMAP §7, 2026-08-14)


def _sirlar(monkeypatch, **kv):
    """`secrets.get`i yalnız bu testin sözlüğüyle besle — gerçek `.env`/credential OKUNMAZ."""
    monkeypatch.setattr(hermes.secrets, "get", lambda k, *a, **kw: kv.get(k), raising=False)
    hermes._OLU_MODEL_OLAYLI.clear()


def _olaylar(sandbox_state, ad: str) -> list:
    yol = sandbox_state / "events.jsonl"
    if not yol.exists():
        return []
    return [json.loads(l) for l in yol.read_text().splitlines()
            if l.strip() and json.loads(l).get("event") == ad]


def _tmp_config(tmp_path, monkeypatch, govde: str):
    cfg = tmp_path / "config.yaml"
    cfg.write_text(govde)
    monkeypatch.setattr(hermes, "AGENT_CONFIG", str(cfg))
    monkeypatch.setattr(hermes, "_hermes_bin", lambda: "/bin/true")
    return cfg


# ------------------------------------- T1 GÖÇ HARİTASI -------------------------------------

def test_T1_bilinen_olu_yedek_adlari_kanonige_gocer(sandbox_state, monkeypatch):
    """404 sınıfı iki ad da TEK kanonik yedeğe çıkar; harita gemini'ye özgü değildir."""
    _sirlar(monkeypatch)
    assert hermes.canonical_model(OLU_YEDEK, kaynak="t") == hermes.NOUS_FALLBACK_DEFAULT
    assert hermes.canonical_model(OLU_ESKI, kaynak="t") == hermes.NOUS_FALLBACK_DEFAULT


# --------------------------------- T2 ÇAĞRI ANI + OLAY ---------------------------------

def test_T2_zincir_olu_yedegi_gocurur_ve_OLAYLAR(sandbox_state, monkeypatch):
    """CANLI GEOMETRİ (2026-09-14): birincil sağ, yedek ölü. Zincir yedeği kanoniğe çevirmeli
    ve göçü DEFTERE yazmalı — sessiz ad değiştirme yasağı bu yüzeyde de geçerli."""
    _sirlar(monkeypatch, NOUS_MODEL=BIRINCIL, NOUS_FALLBACK_MODEL=OLU_YEDEK)
    assert hermes._nous_model_zinciri() == [BIRINCIL, hermes.NOUS_FALLBACK_DEFAULT]
    ev = _olaylar(sandbox_state, "agent_model_olu_ad_gocuruldu")
    assert len(ev) == 1, f"göç olayı tek kez basılmadı: {ev}"
    assert ev[0]["kaynak"] == "NOUS_FALLBACK_MODEL", "hangi yüzeydeki ad göçtü yazılmamış"
    assert ev[0]["eski"] == OLU_YEDEK and ev[0]["yeni"] == hermes.NOUS_FALLBACK_DEFAULT


def test_T3_iki_sir_da_olu_adda_ise_zincir_TEKE_iner(sandbox_state, monkeypatch):
    """Aynı modeli iki kez denemek yedeklilik DEĞİLDİR; göç sonrası tekilleştirme bunu gösterir."""
    _sirlar(monkeypatch, NOUS_MODEL=OLU_ESKI, NOUS_FALLBACK_MODEL=OLU_YEDEK)
    assert hermes._nous_model_zinciri() == [hermes.NOUS_FALLBACK_DEFAULT]


# ------------------------------- T4 CONFIG YÜZEYİ AYNI KAPIDAN -------------------------------

def test_T4a_config_olu_sirri_kanonige_cevirerek_yazar(sandbox_state, monkeypatch, tmp_path):
    """Sır ölü adla DOLU: config yüzeyi de göçürmeli. Ham sır yazılırsa canlı CLI 404 yemeye
    devam eder — çağrı anını onarıp config'i açık bırakmak, v239'un kapattığı kusurun ikizidir."""
    cfg = _tmp_config(tmp_path, monkeypatch, "model:\n  provider: gemini\n")
    _sirlar(monkeypatch, NOUS_FALLBACK_MODEL=OLU_YEDEK)
    assert hermes.config_ensure_integrations().get("ok") is True
    fb = yaml.safe_load(cfg.read_text())["fallback_providers"]
    assert fb == [{"provider": "nous", "model": hermes.NOUS_FALLBACK_DEFAULT}]


def test_T4b_sir_yokken_de_kanonik_varsayilan_yazilir(sandbox_state, monkeypatch, tmp_path):
    """Sır HİÇ yokken gömülü varsayılan devreye girer — o varsayılanın kendisi de canlı olmalı
    (eski gömülü ad `tencent/hy3:free` katalogda hiç yoktu: uydurma bir yedek)."""
    cfg = _tmp_config(tmp_path, monkeypatch, "model:\n  provider: gemini\n")
    _sirlar(monkeypatch)
    assert hermes.config_ensure_integrations().get("ok") is True
    fb = yaml.safe_load(cfg.read_text())["fallback_providers"]
    assert fb == [{"provider": "nous", "model": hermes.NOUS_FALLBACK_DEFAULT}]


# ------------------------------- T5 TEK KAYNAK (kod ↔ dağıtım) -------------------------------

def test_T5_deploy_config_kod_sabitinden_ayrismaz():
    """İKİ KOPYA, TEK GERÇEK: A1'deki `~/.hermes/config.yaml`ı her standby turunda
    `hermes.config_ensure_integrations` yazar; `deploy/hermes/config.yaml` ise dağıtımla gider.
    İkisi ayrışırsa dağıtım sonrası ilk standby turu sessizce geri alır — tek-kaynak yasası."""
    yol = store.config.ROOT / "deploy" / "hermes" / "config.yaml"
    cfg = yaml.safe_load(yol.read_text())
    fb = cfg.get("fallback_providers") or []
    assert fb and fb[0]["provider"] == "nous", f"dağıtım config'inde nous yedeği yok: {fb}"
    assert fb[0]["model"] == hermes.NOUS_FALLBACK_DEFAULT, (
        "dağıtım config'i kod sabitinden ayrışmış — canlıda iki ayrı yedek adı doğar")


# ------------------------------- T6/T7 YEDEĞİN KENDİSİ -------------------------------

def test_T6_yedek_ucretsiz_ve_BIRINCILDEN_FARKLI_ust_akimdan():
    """Aynı havuzdan alınan yedek yedeklilik değildir: 2026-09-14 22:03Z Nvidia "temporarily
    overloaded" 502 verirken nvidia/* bir yedek de düşerdi. Ayrıca operatörün kredisi yok —
    ücretsiz katman şart (`:free` soneki)."""
    ad = hermes.NOUS_FALLBACK_DEFAULT
    assert ad.endswith(":free"), f"ücretli yedek: {ad}"
    assert "/" in ad, f"satıcı öneki yok, üst-akım ayrımı ölçülemez: {ad}"
    assert ad.split("/", 1)[0] != BIRINCIL.split("/", 1)[0], (
        f"yedek birincille AYNI üst-akımdan ({ad}) — sahte yedeklilik")


def test_T7_yeni_varsayilan_olu_listesinde_DEGIL():
    """Göç haritasının hedefi haritanın anahtarı olursa göç kendi kuyruğunu yer (ve yeni
    varsayılan bir gün ölürse bu satır, sessiz 404 yerine kırmızı verir)."""
    assert hermes.NOUS_FALLBACK_DEFAULT not in hermes.GEMINI_DEAD_MODEL_MAP, (
        "yeni varsayılan ölü ad listesine düşmüş")
    assert all(v != k for k, v in hermes.GEMINI_DEAD_MODEL_MAP.items())


# ------------------------- T8 PORTAL AYAĞI (göç + künye tek kaynak) -------------------------
# Kaynak etiketi portal ayağını zincirden/rapor yüzeyinden AYIRIR: olay tekilleştirmesi
# (kaynak, eski_ad) çiftiyle yapılır, yani aynı sır iki ayrı yüzeyde göçerse ikisi de görünür.
PORTAL_KAYNAK = "NOUS_MODEL(portal)"


class _Yanit:
    """httpx.Response'un `_nous_text`in DOKUNDUĞU yüzeyi kadarı — ağ yok, gövde saptır."""

    def __init__(self, body: dict):
        self.status_code, self._body = 200, body

    def json(self):
        return self._body

    def raise_for_status(self):
        return None


_IYI_CEVAP = {"choices": [{"message": {"content": "tamam"}, "finish_reason": "stop"}],
              "usage": {"prompt_tokens": 3, "completion_tokens": 2}}


def _post_govdesi(monkeypatch) -> dict:
    """`_nous_text`in GERÇEKTEN gönderdiği istek gövdesini yakala — GERÇEK AĞ ÇAĞRISI YOK."""
    yakalanan: dict = {}

    def sahte_post(url, **kw):
        yakalanan["url"] = url
        yakalanan["json"] = kw.get("json") or {}
        return _Yanit(_IYI_CEVAP)

    monkeypatch.setattr(httpx, "post", sahte_post)
    return yakalanan


def test_T8a_portal_olu_adi_gocurur_ve_OLAYLAR_bir_kez(sandbox_state, monkeypatch):
    """Portal birincili ölü bir ada ayarlıysa (canlı 404 sınıfı) burası kanonik adı döndürmeli
    ve göçü DEFTERE yazmalı. Mandal süreç başınadır: yansıma turu ~5 dakikada bir koşuyor,
    her turda warn basmak alarmı gürültüye çevirirdi (bkz. `canonical_model` notu)."""
    _sirlar(monkeypatch, NOUS_MODEL=OLU_YEDEK)
    assert hermes._nous_portal_model() == hermes.NOUS_FALLBACK_DEFAULT
    ev = _olaylar(sandbox_state, "agent_model_olu_ad_gocuruldu")
    assert len(ev) == 1, f"portal göçü sessiz ya da tekrarlı: {ev}"
    assert ev[0]["kaynak"] == PORTAL_KAYNAK, "hangi yüzeydeki ad göçtü yazılmamış"
    assert ev[0]["eski"] == OLU_YEDEK and ev[0]["yeni"] == hermes.NOUS_FALLBACK_DEFAULT
    assert hermes._nous_portal_model() == hermes.NOUS_FALLBACK_DEFAULT
    assert len(_olaylar(sandbox_state, "agent_model_olu_ad_gocuruldu")) == 1, \
        "süreç başına mandal tutmuyor — her çağrı deftere satır yazıyor"


def test_T8b_istek_govdesi_ile_kunye_TEK_KAYNAK(sandbox_state, monkeypatch):
    """TEK KAYNAK SÖZLEŞMESİ: `_nous_text`in gövdeye yazdığı `model` ile künyenin okuduğu ad
    AYNI fonksiyondan gelir. Göç yalnız birine uygulansaydı defter "Hermes-4-405B çağırdık"
    derken portal başka bir modele giderdi — v246'nın kapattığı ayrışma sınıfı."""
    _sirlar(monkeypatch, NOUS_MODEL=OLU_YEDEK, NOUS_API_KEY="sahte-anahtar")
    yakalanan = _post_govdesi(monkeypatch)

    assert hermes._nous_text("merhaba", note="v493 civi") == "tamam"

    giden = yakalanan["json"].get("model")
    assert giden == hermes.NOUS_FALLBACK_DEFAULT, f"gövdeye ölü ad yazıldı: {giden}"
    assert giden == hermes._nous_portal_model(), "gövde ile künye ayrıştı (iki kopya)"
    ev = _olaylar(sandbox_state, "agent_model_olu_ad_gocuruldu")
    assert len(ev) == 1 and ev[0]["kaynak"] == PORTAL_KAYNAK, ev
    # YAPISAL ÇİVİ: künye alanı ikinci bir ifade değil, AYNI fonksiyonun dönüşüdür.
    assert "_nous_portal_model()" in inspect.getsource(hermes.chain_text), \
        "künye portal adını kendi ifadesiyle kuruyor — tek kaynak kırıldı"


def test_T8c_taninmayan_ad_serbest_gecer_ve_sir_yokken_varsayilan(sandbox_state, monkeypatch):
    """Elimizdeki ölü-ad listesi bir KESİTTİR: gelecekteki geçerli bir adı "onarmak" arızanın
    kendisi olurdu. Sır hiç yokken portal modunda varsayılan UYDURMA DEĞİL, gerçekten giden addır
    (gövdeyi biz kuruyoruz) — ve dönüş tipi her iki yolda da `str` kalır."""
    _sirlar(monkeypatch, NOUS_MODEL="Hermes-9-taninmayan")
    assert hermes._nous_portal_model() == "Hermes-9-taninmayan"
    assert _olaylar(sandbox_state, "agent_model_olu_ad_gocuruldu") == [], \
        "tanınmayan ad göç olayı bastı — kurt masalı"
    _sirlar(monkeypatch)
    ad = hermes._nous_portal_model()
    assert ad == hermes.NOUS_DEFAULT_MODEL and isinstance(ad, str)


# ------------------ T9 RAPOR YÜZEYİ: AYNI KAPI, AMA SESSİZ (2026-09-15) ------------------
# `_model_id("nous")` portal dalı ile `_nous_portal_model()` AYNI adı üretmek zorundadır
# (tek-kaynak yasası: harita ya da varsayılan değişince iki elle yazılmış ifade sessizce
# ayrışır) ama defteri YALNIZ gerçek çağrı yolu yazar (2026-08-13 ayrımı): bir pano isteği
# operatörün `state/events.jsonl`ine "göç oldu" satırı doğuramaz.
# T9a sözleşmeyi DAVRANIŞLA, T9b YAPISAL olarak (delegasyon) ölçer: T9a iki ifade elle
# senkron tutulduğunda da yeşil kalır — ayrışma riskini yalnız T9b ısırır.


def test_T9a_rapor_yuzeyi_ayni_adi_verir_ama_OLAY_BASMAZ(sandbox_state, monkeypatch):
    """Sır ölü adda: rapor yüzeyi (`/api/hermes`, `brain_chain_facts`, `active_model`) kanonik
    adı göstermeli — "ne çağırdık / ne rapor ettik" ayrışamaz — ama okuma defter YAZMAMALI."""
    _sirlar(monkeypatch, NOUS_MODEL=OLU_YEDEK)
    monkeypatch.setattr(hermes, "_hermes_bin", lambda: None)   # mod makineden bağımsız ölçülsün
    rapor = hermes._model_id("nous")
    assert rapor == hermes.NOUS_FALLBACK_DEFAULT, f"rapor yüzeyi ölü adı taşıyor: {rapor}"
    assert _olaylar(sandbox_state, "agent_model_olu_ad_gocuruldu") == [], \
        "rapor/pano okuması operatörün defterine göç satırı yazdı (2026-08-13 ayrımı düştü)"
    assert rapor == hermes._nous_portal_model(), "rapor adı ile istek gövdesine giden ad ayrıştı"
    ev = _olaylar(sandbox_state, "agent_model_olu_ad_gocuruldu")
    assert len(ev) == 1 and ev[0]["kaynak"] == PORTAL_KAYNAK, \
        f"çağrı yolu olayı basmadı (ya da rapor yüzeyi mandalı erken kapattı): {ev}"


def test_T9b_rapor_dali_portal_fonksiyonuna_DELEGE_eder(sandbox_state, monkeypatch):
    """DELEGASYON KANITI: portal adı rapor dalında İKİNCİ KEZ yazılmış olsaydı bu çivi kırmızı
    olurdu (sahte dönüş yansımaz). İki ifade bugün aynı adı üretiyor — bu çivi yarını, yani
    haritanın/varsayılanın değiştiği turu ısırır."""
    _sirlar(monkeypatch, NOUS_MODEL=BIRINCIL)
    monkeypatch.setattr(hermes, "_hermes_bin", lambda: None)
    gorulen: dict = {}

    def _sahte_portal(*, olay: bool = True) -> str:
        gorulen["olay"] = olay
        return "sahte/delegasyon-kaniti"

    monkeypatch.setattr(hermes, "_nous_portal_model", _sahte_portal)
    assert hermes._model_id("nous") == "sahte/delegasyon-kaniti", \
        "portal dalı adı KENDİ ifadesiyle kuruyor — aynı gerçeğin ikinci evi (tek-kaynak yasası)"
    assert gorulen.get("olay") is False, \
        "rapor yüzeyi portal adını olay bayrağı AÇIKKEN okudu — pano isteği deftere yazar"


def test_T9c_yerel_ajan_adsizken_None_korumasi_DURUYOR(sandbox_state, monkeypatch):
    """Delegasyon uydurma korumasını YUTMAMALI: yerel ajan modunda adı CLI'nın kendi config'i
    seçer, `NOUS_DEFAULT_MODEL` orada bir ÖLÇÜM değil bir varsayımdır (v246 m1, v96)."""
    _sirlar(monkeypatch)                                          # NOUS_MODEL yok
    monkeypatch.setattr(hermes, "_hermes_bin", lambda: "/bin/true")   # yerel ajan modu
    assert hermes._nous_local() is True
    assert hermes._model_id("nous") is None, \
        "yerel ajan modunda varsayılan uydurulmuş — kimse o modeli seçmedi"
    cagrilar: list = []

    def _sahte_portal(*, olay: bool = True) -> str:
        cagrilar.append(olay)
        return "sahte/olmamali"

    monkeypatch.setattr(hermes, "_nous_portal_model", _sahte_portal)
    assert hermes._model_id("nous") is None and cagrilar == [], \
        "koruma delegasyondan SONRAYA kaymış: adsız yerel ajan için portal adı üretildi"
