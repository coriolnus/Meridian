"""test_inceleme_hatti_v188.py — LLM inceleme hattının iki ÖLÇÜLÜ kusuru (canlı defter, 2026-08-04).

KANIT (canlı olaylar, 2026-08-04T07:23:32):
    agent_call kind=review model=tencent/hy3:free attempt=2 empty=true
    agent_call_empty chain=2 fallback_model_configured=true pool_exhausted="gemini" cooldown_s=21600

Bu iki satır iki AYRI arızayı taşıyor ve ikisi de aynı yerde birleşiyordu:

  (a) BAYAT TÜKENME İŞARETİ. Kimlik havuzunun "exhausted" kaydı DÜNE aitti; sağlayıcının günlük
      kota penceresi 07:00 UTC'de yenilendiği hâlde işaret hiç eskimiyordu — üstelik havuz satırı
      zaman taşımıyorsa eski kod (`not last_status_at` dalı) onu SONSUZA dek tükenmiş sayıyordu.
      Sonuç: taze kota penceresi HİÇ denenmeden yedek modele düşülüyordu.

  (b) BOŞ YEDEK = TAM SOĞUMA. Yedek model boş dönünce zincir 21600 sn (6 saat) soğuma yazıyordu.
      Oysa boş cevap "kota bitti" değil "hat çalıştı, model sustu" demektir ve o ceza kotası
      DOLMAMIŞ birinci modeli de kapsıyordu: hat kendi kendini altı saatliğine kilitliyordu.

Dosya dört sözleşmeyi kilitler:
  1. İşaret son kota sıfırlamasından ESKİYSE temizlenir ve birinci model GERÇEKTEN yoklanır.
  2. İşaret TAZE ise (bu pencerede kondu) hiçbir şey değişmez — süreç başlatılmaz (eski davranış).
  3. Boş yedek → 6 saatlik üstel ceza YOK; düz kısa pencere + `review_fallback_empty` olayı; birinci
     bir sonraki turda yeniden denenebilir kalır.
  4. GERÇEK kota hatası (çıktıda 429/quota imzası) → mevcut üstel merdiven aynen sürer (regresyon).

Saat ÇİVİLİDİR: gerçek duvar saatine bağlı bir fikstür günün saatine göre yeşil/kırmızı olurdu
(2026-08-03 tarih-bağımlı fikstür dersi). Alt süreç ve ağ saplıdır; fikstürlerde gizli/anahtar YOK.
"""
import calendar
import json
import subprocess
import time

import pytest

from meridian import hermes, store


# Canlı olayın anı — 07:00 UTC sıfırlamasından SONRA, yani "taze pencere" içinde.
T0 = float(calendar.timegm((2026, 8, 4, 7, 23, 32, 0, 0, 0)))
# Dünkü tükenme işareti: son sıfırlama sınırından (2026-08-04T07:00Z) ÖNCE.
DUN_2000 = float(calendar.timegm((2026, 8, 3, 20, 0, 0, 0, 0, 0)))

# FİKSTÜR MODEL ADI TAZELENDİ (2026-08-13): burası eskiden `gemini-3.1-pro` idi. v239 çağrı-anı
# göçü (`hermes.canonical_model` / `_nous_model_zinciri`) o adı BİLİNEN-ÖLÜ sayıp `gemini-pro-latest`
# alias'ına çeviriyor (üretim 404 sınıfı, `GEMINI_DEAD_MODEL_MAP`) — yani zincire giren ad ile bu
# dosyanın beklediği ad ayrıştı ve üç test "yoklanan birinci model" karşılaştırmasında düştü.
# BU DOSYANIN İDDİASI GÖÇ DEĞİL SIRA: "bayat tükenme işareti temizlenir ve BİRİNCİ model gerçekten
# yoklanır; yedeğe erken düşülmez". O iddia model adından bağımsızdır, dolayısıyla doğru düzeltme
# beklentiyi göçe göre eğmek değil fikstürü CANLI ada taşımaktır (göç katmanının kendi çivileri
# `test_agent_olu_model_cagri_ani_v239.py` + `test_gemini_olu_model_gocu_v235.py`de).
BIRINCI = "gemini-pro-latest"
YEDEK = "tencent/hy3:free"


def test_fikstur_modeli_CANLI_kalmali():
    """Bu dosyanın sessizce bayatlamasını önleyen bekçi (2026-08-13 vakasının sınıfı).

    Üç test tek sebeple kırmızıya döndü: fikstür ölü bir model adı taşıyordu ve göç katmanı onu
    çevirince beklenti tutmaz oldu. Alias'lar da ölümlüdür; bir sonrakinde arıza "üç anlaşılmaz
    kırmızı" olarak değil, ADIYLA gelsin."""
    assert BIRINCI not in hermes.GEMINI_DEAD_MODEL_MAP, (
        f"fikstürün birinci modeli ({BIRINCI}) ölü-ad haritasına girmiş — çağrı-anı göçü onu "
        f"'{hermes.GEMINI_DEAD_MODEL_MAP.get(BIRINCI)}' yapar ve aşağıdaki sıra iddiaları "
        f"model adı yüzünden düşer. Fikstürü canlı alias'a taşı (iddiayı DEĞİL).")
    assert YEDEK not in hermes.GEMINI_DEAD_MODEL_MAP, f"yedek fikstür modeli ({YEDEK}) ölü"

# Boş-oturum imzası (canlıda görülen CLI özeti): model hiç cevap vermedi.
BOS_CIKTI = "…  |  Messages:       1 (1 user, 0 tool calls)"
DOLU_CIKTI = '{"reviews": []}\n…  |  Messages:       4 (1 user, 2 tool calls)'


class _SahteSaat:
    """`hermes` modülünün `time` global'ini çivileyen kabuk. YALNIZ `time()` sabitlenir; gmtime/sleep
    gibi her şey gerçek modüle iner ve store'un kilit saati hiç değişmez (sandbox gerçek zamanda)."""

    def __init__(self, now: float):
        self.now = float(now)

    def time(self) -> float:
        return self.now

    def ilerlet(self, saniye: float) -> float:
        self.now += float(saniye)
        return self.now

    def __getattr__(self, ad):
        return getattr(time, ad)


class _Kosum:
    """subprocess.run sonucu taklidi — süreç YOK, ağ YOK."""

    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode, self.stdout, self.stderr = returncode, stdout, stderr


@pytest.fixture
def saat(monkeypatch):
    s = _SahteSaat(T0)
    monkeypatch.setattr(hermes, "time", s)
    return s


@pytest.fixture
def ajan(sandbox_state, tmp_path, monkeypatch):
    """Yerel ajan düzeneği: sahte ikili, iki modelli düşüş zinciri, saplı alt süreç.

    `koşum` alanına yazılan sonuç bir SONRAKİ alt süreç çağrısında döner; çalıştırılan komutlar
    `runs` listesinde birikir (hangi modelin GERÇEKTEN yoklandığı ancak buradan ölçülür)."""
    monkeypatch.setattr(hermes, "_hermes_bin", lambda: "/sahte/hermes")
    monkeypatch.setattr(hermes, "sync_agent_skills", lambda: None)
    monkeypatch.setattr(hermes.secrets, "get",
                        lambda k: {"NOUS_MODEL": BIRINCI, "NOUS_FALLBACK_MODEL": YEDEK}.get(k))

    class _Duzenek:
        runs: list = []
        kosum = _Kosum(0, BOS_CIKTI, "")

        def modeller(self):
            return [c[c.index("--model") + 1] for c in self.runs if "--model" in c]

    d = _Duzenek()
    monkeypatch.setattr(subprocess, "run", lambda cmd, **kw: d.runs.append(list(cmd)) or d.kosum)
    return d


def _havuz(monkeypatch, tmp_path, at, exhausted=True):
    """Sahte kimlik havuzu. DİKKAT: gerçek anahtar/token YOK — yalnız durum alanları.
    `at=None` → satır `last_status_at` HİÇ taşımaz (zamansız işaret vakası)."""
    satir = {"id": "aaaa", "label": "GEMINI_API_KEY", "source": "env:GEMINI_API_KEY",
             "last_status": "exhausted" if exhausted else "ok",
             "last_error_code": 429 if exhausted else None}
    if at is not None:
        satir["last_status_at"] = at
    auth = tmp_path / "auth.json"
    auth.write_text(json.dumps({"credential_pool": {"gemini": [satir]}}))
    monkeypatch.setattr(hermes, "AGENT_AUTH_FILE", str(auth))
    # ajanın YAPILANDIRILMIŞ sağlayıcısı havuz satırıyla eşleşmeli; `sandbox_state` AGENT_CONFIG'i
    # tmp'ye çevirdiği için bu dosya operatörün makinesindeki gerçek yapılandırmayı ASLA okumaz.
    (tmp_path / "hermes_config.yaml").write_text("model:\n  provider: gemini\n  default: gemini-test\n")
    return auth


def _soguma_yaz(kuruldu: float, saniye: float, reason: str = "pool_exhausted:gemini") -> None:
    """Var olan bir ajan soğumasını çivile: `kuruldu` anında `saniye` uzunluğunda yazılmış gibi."""
    store.write_json(hermes.BRAIN_COOLDOWN_FILE,
                     {"agent": {"until": kuruldu + saniye, "seconds": saniye, "streak": 5,
                                "reason": reason, "since": "2026-08-04T02:13:32Z"}})


def _events(event: str | None = None) -> list[dict]:
    rows = store.read_jsonl("events.jsonl")
    return [r for r in rows if event is None or r.get("event") == event]


# ---------------------------------------------------------- 0) SINIR MATEMATİĞİ (saatten bağımsız)
@pytest.mark.parametrize("spec,beklenen", [
    ((2026, 8, 4, 7, 23, 32), (2026, 8, 4, 7, 0, 0)),    # sıfırlamadan sonra → BUGÜNÜN sınırı
    ((2026, 8, 4, 7, 0, 0), (2026, 8, 4, 7, 0, 0)),      # tam sınırda → sınır bugündür
    ((2026, 8, 4, 6, 59, 59), (2026, 8, 3, 7, 0, 0)),    # sıfırlamadan önce → DÜNÜN sınırı
    ((2026, 1, 1, 3, 0, 0), (2025, 12, 31, 7, 0, 0)),    # yıl sınırı: ay/yıl geriye sarar
])
def test_gunluk_sifirlama_siniri_utc_hesaplanir(spec, beklenen):
    """`_quota_reset_epoch` SAF: verilen ana göre son günlük sıfırlama sınırını verir. Bu testin
    duvar saatiyle hiçbir bağı yok — davranış testleri sahte saat kullanabilsin diye sınır burada
    ayrıca ve doğrudan ölçülür."""
    got = hermes._quota_reset_epoch(calendar.timegm(spec + (0, 0, 0)))
    assert got == float(calendar.timegm(beklenen + (0, 0, 0)))


# ------------------------------------------- (a) ESKİ İŞARET + SIFIRLAMA SONRASI → BİRİNCİ YOKLANIR
def test_eski_isaret_sifirlamadan_sonra_temizlenir_ve_birinci_gercekten_yoklanir(
        sandbox_state, tmp_path, monkeypatch, saat, ajan):
    """CANLI VAKA: dünkü tükenme + bugünün taze kota penceresi. İşaret sıfırlama sınırından eski
    olduğu için düşer; ajan soğuması kaldırılır ve BİRİNCİ model gerçekten yoklanır."""
    _havuz(monkeypatch, tmp_path, at=DUN_2000)
    # dün 02:13'te (sınırdan ÖNCE) yazılmış 6 saatlik soğuma — T0'da hâlâ ~50 dk kalmış
    _soguma_yaz(kuruldu=T0 - 18600, saniye=hermes.BRAIN_COOLDOWN_MAX_S)
    assert hermes.brain_cooldown("agent") > 0, "önkoşul: kilit gerçekten duruyor"

    assert hermes._pool_exhausted() is None, \
        "dünkü işaret BUGÜNÜN kotası hakkında hiçbir şey söylemez — sıfırlamada düşmeli"

    ajan.kosum = _Kosum(0, DOLU_CIKTI, "")
    out = hermes._agent_call("soru", kind="review")

    assert out == DOLU_CIKTI, "taze pencere yoklanmalı ve dolu cevap geri dönmeli"
    assert ajan.modeller() == [BIRINCI], "yoklanan BİRİNCİ model olmalı — yedeğe düşülmemeli"
    assert hermes.brain_cooldown("agent") == 0, "bayat işaretten kalan soğuma kaldırılmalı"
    ev = _events("agent_pool_window_reset")
    assert len(ev) == 1 and ev[0]["reset_utc_hour"] == hermes.POOL_QUOTA_RESET_UTC_HOUR
    assert ev[0]["iptal_edilen_soguma_s"] > 0 and len(ev[0]["detail"]) >= 20   # YASA 4
    assert _events("agent_call_cooldown") == [], "süreç başlatmadan dönülmemeli"


def test_zamansiz_isaret_sonsuza_dek_bloklamaz_ilk_gozlem_ani_civilenir(
        sandbox_state, tmp_path, monkeypatch, saat):
    """Havuz satırı `last_status_at` taşımıyorsa eski kod işareti SONSUZA dek tükenmiş sayıyordu.
    Artık ölçülemeyen zaman ne uydurulur ne yok sayılır: ilk gözlem anı çivilenir ve eskir."""
    _havuz(monkeypatch, tmp_path, at=None)
    assert hermes.pool_health()["gemini"]["last_status_at"] is None, "önkoşul: zamansız işaret"

    assert hermes._pool_exhausted() == "gemini", "ŞİMDİ gözlenen tükenme geçerlidir"
    civi = store.read_json(hermes.POOL_SEEN_FILE, {})["gemini"]
    assert civi == T0, "ilk gözlem anı çivilenmeli"

    saat.ilerlet(hermes.POOL_EXHAUSTED_WINDOW_S + 60)      # pencere doldu (sıfırlama gelmeden bile)
    assert hermes._pool_exhausted() is None
    assert store.read_json(hermes.POOL_SEEN_FILE, {}) == {}, "işaret düşünce çivi de kalkmalı"


# ------------------------------------------------------- (b) TAZE İŞARET → YOKLANMAZ (eski davranış)
def test_taze_isaret_yoklanmaz_surec_hic_baslatilmaz(sandbox_state, tmp_path, monkeypatch, saat, ajan):
    """POZİTİF KONTROL SINIFI: düzeltme her işareti temizlemiyor. Tükenme BU kota penceresinde
    konduysa bilgi tazedir — bilinen-ölü sağlayıcıyı dövmek kotayı geri getirmez."""
    _havuz(monkeypatch, tmp_path, at=T0 - 600)             # bugün 07:13 — sınırdan SONRA
    _soguma_yaz(kuruldu=T0 - 600, saniye=hermes.BRAIN_COOLDOWN_MAX_S)

    assert hermes._pool_exhausted() == "gemini", "taze tükenme işareti ayakta kalmalı"
    assert hermes._agent_call("soru", kind="review") is None
    assert ajan.runs == [], "soğumadaki ajan için süreç HİÇ başlatılmamalı"
    assert _events("agent_call_cooldown"), "eski davranış aynen: dinlenme penceresi bildirilir"
    assert _events("agent_pool_window_reset") == [], "taze işaret temizlenmemeli"


# ------------------------------------------------- (c) BOŞ YEDEK → 6h YOK, kısa pencere + ayrı olay
def test_bos_yedek_alti_saatlik_soguma_kurmaz_birinci_denenebilir_kalir(
        sandbox_state, tmp_path, monkeypatch, saat, ajan):
    """Yedek model boş döndü ve çıktıda kota imzası YOK: bu 'kota bitti' değil, 'hat çalıştı, model
    sustu'. Üstel merdiven yazılmaz; düz kısa pencere kurulur ve birinci yeniden denenebilir kalır."""
    _havuz(monkeypatch, tmp_path, at=T0 - 600)             # havuz TAZE-tükenmiş: eski kod 21600 yazardı
    ajan.kosum = _Kosum(0, BOS_CIKTI, "")

    assert hermes._agent_call("soru", kind="review") is None
    assert ajan.modeller() == [BIRINCI, YEDEK], "zincir sırayla yoklanmalı"

    rem = hermes.brain_cooldown("agent")
    assert 0 < rem <= hermes.BRAIN_COOLDOWN_BASE_S, \
        f"kısa pencere beklenir, 6 saatlik kilit değil (kalan={rem})"
    assert rem < hermes.BRAIN_COOLDOWN_MAX_S / 10
    satir = store.read_json(hermes.BRAIN_COOLDOWN_FILE, {})["agent"]
    assert satir["streak"] == 0, "susan model üstel merdivene binmemeli"

    fb = _events("review_fallback_empty")
    assert len(fb) == 1 and fb[0]["model"] == YEDEK and fb[0]["chain"] == 2
    assert fb[0]["pool_exhausted"] == "gemini" and len(fb[0]["detail"]) >= 20      # YASA 4
    bos = _events("agent_call_empty")[-1]
    assert bos["cooldown_sinifi"] == "fallback_empty" and bos["kota_imzasi"] is None
    assert bos["cooldown_s"] <= hermes.BRAIN_COOLDOWN_BASE_S

    # BİR SONRAKİ TUR: kısa pencere dolar dolmaz birinci GERÇEKTEN yeniden yoklanır
    saat.ilerlet(hermes.BRAIN_COOLDOWN_BASE_S + 1)
    ajan.runs.clear()
    ajan.kosum = _Kosum(0, DOLU_CIKTI, "")
    assert hermes._agent_call("soru", kind="review") == DOLU_CIKTI
    assert ajan.modeller() == [BIRINCI], "birinci model bir sonraki turda denenebilir kalmalı"


def test_bos_yedek_saglikli_havuzda_da_kisa_pencere_kurar(sandbox_state, tmp_path, monkeypatch, saat, ajan):
    """(1) numaralı düzeltmenin AÇABİLECEĞİ delik kapalı: işaret bayat olduğu için düştüğünde eski
    kod HİÇ soğuma yazmıyordu — ölü bir zincir her turda yeniden doğardı. Kısa pencere havuzun
    durumundan bağımsız kurulur; ölçülmemiş olan yedek modelin susmasıdır, havuzun sağlığı değil."""
    _havuz(monkeypatch, tmp_path, at=T0 - 600, exhausted=False)
    ajan.kosum = _Kosum(0, BOS_CIKTI, "")

    assert hermes._agent_call("soru", kind="review") is None
    assert hermes._pool_exhausted() is None, "önkoşul: havuz sağlıklı"
    rem = hermes.brain_cooldown("agent")
    assert 0 < rem <= hermes.BRAIN_COOLDOWN_BASE_S
    assert _events("review_fallback_empty")[0]["pool_exhausted"] is None
    assert _events("agent_call_empty")[-1]["cooldown_sinifi"] == "fallback_empty"


# --------------------------------------------- (d) GERÇEK KOTA HATASI → uzun soğuma aynen (regresyon)
def test_gercek_kota_hatasi_mevcut_ustel_soguma_merdivenini_korur(
        sandbox_state, tmp_path, monkeypatch, saat, ajan):
    """REGRESYON: çıktı gerçek bir kota/oran-sınırı imzası taşıyorsa hiçbir şey yumuşamaz — havuz
    cezası yazılır ve üstel merdiven (tavan 21600) aynen işler."""
    _havuz(monkeypatch, tmp_path, at=T0 - 600)
    ajan.kosum = _Kosum(1, "", "google.api_core.exceptions.ResourceExhausted: 429 "
                              "Quota exceeded for quota metric 'Generate Content API requests'")

    assert hermes._agent_call("soru", kind="review") is None
    assert _events("review_fallback_empty") == [], "kota hatası 'model sustu' sınıfına düşmemeli"
    bos = _events("agent_call_empty")[-1]
    assert bos["cooldown_sinifi"] == "pool_exhausted" and bos["kota_imzasi"]
    assert bos["cooldown_s"] == hermes.BRAIN_COOLDOWN_BASE_S
    satir = store.read_json(hermes.BRAIN_COOLDOWN_FILE, {})["agent"]
    assert satir["streak"] == 1 and satir["reason"] == "pool_exhausted:gemini"

    # merdiven KORUNDU: ikinci tur cezayı ikiye katlar (eski davranış birebir)
    saat.ilerlet(hermes.BRAIN_COOLDOWN_BASE_S + 1)
    assert hermes._agent_call("soru", kind="review") is None
    assert _events("agent_call_empty")[-1]["cooldown_s"] == hermes.BRAIN_COOLDOWN_BASE_S * 2
    assert store.read_json(hermes.BRAIN_COOLDOWN_FILE, {})["agent"]["streak"] == 2


# ------------------------------------------------------------------------------ POZİTİF KONTROL
def test_pozitif_kontrol_saglikli_havuz_ve_dolu_cevap_hicbir_kusur_olayi_uretmez(
        sandbox_state, tmp_path, monkeypatch, saat, ajan):
    """Dedektörler her şeyi 'kusurlu' görüyor olsaydı yukarıdaki testler de geçerdi (kurt masalı
    yasağı). AYNI düzenekte sağlıklı havuz + dolu cevap: tek bir kusur olayı bile yazılmamalı."""
    _havuz(monkeypatch, tmp_path, at=T0 - 600, exhausted=False)
    ajan.kosum = _Kosum(0, DOLU_CIKTI, "")

    assert hermes._agent_call("soru", kind="review") == DOLU_CIKTI
    assert ajan.modeller() == [BIRINCI]
    assert hermes._pool_exhausted() is None and hermes.brain_cooldown("agent") == 0
    for kotu in ("agent_call_empty", "review_fallback_empty", "agent_call_cooldown",
                 "agent_pool_window_reset", "agent_unconfigured"):
        assert _events(kotu) == [], f"sağlıklı yolda {kotu} yazılmamalı"
