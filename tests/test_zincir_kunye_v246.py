"""test_zincir_kunye_v246.py — v245 künye kusurunun ADIYLA devredilen İKİ KARDEŞİ (ROADMAP Ö-31).

KALEM 1 (Ö-31a) — `chain_text` künyesi "istenen"i değil CEVAP VERENİ yazar.
`hermes.py` `chain_text` → `out.update({..., "model": active_model()})` idi: zincir KOŞTUKTAN sonra
YAPILANDIRMA yeniden okunuyordu. Zincirin varlık sebebi ayakların düşmesi olduğu için alan tam da
düşüş anında yanlış oluyordu. `candidate_review`de ölçülen bedel: `tencent/hy3:free` 56 çağrıda 0
cevap verdi, pano haftalarca onun adını yazdı — hatalı künye ARIZAYI GİZLEDİ.
ÇİVİLER: (a) birinci ayak dolu → BİRİNCİL · (b) birinci boş/ikinci dolu → İKİNCİ · (c) hiçbiri →
None + neden · (d) TÜKETEN-OKUMA NOKTASI DOĞRU: agent kutusu yalnız kendi ayağında okunur — ne
gemini'nin künyesini None'a çevirir (ters yön!) ne de bayat bir künyeyi claude'un cevabına yapıştırır
· (e) ayrışma OLAY basar · (f) tüketici (`nous_eval`) sözleşmesi kırılmadı.

KALEM 2 (Ö-31b) — `active_model()` uydurma korumasını TAŞIMIYORDU.
`_model_id("nous")` 2026-07-26'dan beri "yerel ajan + `NOUS_MODEL` yok → None" diyor; `active_model()`
aynı durumda `'Hermes-4-405B'` döndürüyordu, yani HİÇ ÇAĞRILMAMIŞ bir ad deftere/panoya düşebiliyordu.
ÇİVİLER: (a) yerel+adsız → None · (b) `_model_id(active_brain())` ile HER sağlayıcıda AYNI (ikinci
kopya kalmadı) · (c) çağıranlar None'u taşıyor (`hermes_runtime` diske None yazar).

KALEM 3 — ÖLÇÜM ÇİVİSİ: kalibrasyonun girdisi `trade_plans.jsonl`ın `llm_opinion` alanıdır ve o alan
HANGİ MODELİN konuştuğunu taşımaz; `candidate_review.json`ın `model` alanı kalibrasyona HİÇ girmez.

Ağ/gerçek alt süreç YOK: `subprocess.run` saplı, `_hermes_bin` sahte, sırlar test tarafından kurulu.
"""
import subprocess

import pytest

from meridian import analytics, hermes, hermes_runtime, nous_eval, spend, store

DOLU = "CEVAP METNI\nMessages: 2 (1 user, 0 tool calls)"
BOS_RC = 1


class _Sonuc:
    def __init__(self, rc=0, stdout="", stderr=""):
        self.returncode, self.stdout, self.stderr = rc, stdout, stderr


def _olaylar(ad):
    return [r for r in store.read_jsonl("events.jsonl") if r.get("event") == ad]


@pytest.fixture
def zincir(sandbox_state, monkeypatch):
    """Zincirin sahte dünyası: ikili 'kurulu', senkron/havuz okuması saplı, bütçe açık.
    Sırlar HER testte kendi sözlüğüyle kurulur (`_sir`) — makinenin gerçek yapılandırması sızmaz."""
    monkeypatch.setattr(hermes, "_hermes_bin", lambda: "/sahte/hermes")
    monkeypatch.setattr(hermes, "sync_agent_skills", lambda: None)
    monkeypatch.setattr(hermes, "_pool_exhausted", lambda: None)
    monkeypatch.setattr(hermes, "_quiet_flag_ok", True)
    monkeypatch.setattr(spend, "over_budget", lambda: False)
    return sandbox_state


def _sir(monkeypatch, **vals):
    """Sır deposunu TAMAMEN testin sözlüğüne indirger (yok olan anahtar None döner)."""
    monkeypatch.setattr(hermes.secrets, "get", lambda k: vals.get(k))
    return vals


def _surec(monkeypatch, karar):
    """`karar(model) -> _Sonuc` — yerel ajan alt süreci. Çağrılan model adları listede birikir."""
    cagrilar = []

    def _run(cmd, **kw):
        model = cmd[cmd.index("--model") + 1] if "--model" in cmd else None
        cagrilar.append(model)
        return karar(model)
    monkeypatch.setattr(subprocess, "run", _run)
    return cagrilar


def _ayaklar(monkeypatch, *, claude=None, gemini=None, portal=None):
    """HTTP ayaklarını sapla — dönüş None ise o ayak boş cevap vermiş olur."""
    monkeypatch.setattr(hermes, "_claude_text", lambda *a, **k: claude)
    monkeypatch.setattr(hermes, "_gemini_call", lambda *a, **k: gemini)
    monkeypatch.setattr(hermes, "_nous_text", lambda *a, **k: portal)


# ==================================================================================================
# KALEM 1 — chain_text künyesi
# ==================================================================================================
def test_k1_BIRINCI_AYAK_DOLU_kunye_birincili_tasir(zincir, monkeypatch):
    """Zincirin ilk ayağı cevap verdiyse künye onu yazar — ve beyan alanları HER kayıtta durur."""
    _sir(monkeypatch, HERMES_API_KEY="k")
    _ayaklar(monkeypatch, claude=DOLU)
    out = hermes.chain_text("soru", kind="t")
    assert out["text"] == DOLU and out["beyin"] == "claude"
    assert out["model"] == hermes.MODEL
    assert out["model_kaynagi"] == "cevap_veren" and out["model_olculemedi"] is None
    assert _olaylar("nous_chain_model_ayrismasi") == [], "ayrışma YOKken ayrışma olayı basıldı"


def test_k2_BIRINCI_BOS_IKINCI_DOLU_kunye_IKINCIYI_tasir(zincir, monkeypatch):
    """CANLI VAKANIN ZİNCİR EŞLENİĞİ: yerel ajan birincil modelde boş, yedekte dolu → künye YEDEK.
    Eski kod burada `active_model()` (= istenen = birincil) yazıyordu; ölçülen bedel o satırdı."""
    _sir(monkeypatch, NOUS_MODEL="tencent/hy3:free", NOUS_FALLBACK_MODEL="gemini-flash-latest")
    _ayaklar(monkeypatch)
    cagrilar = _surec(monkeypatch,
                      lambda m: _Sonuc(0, DOLU) if m == "gemini-flash-latest" else _Sonuc(BOS_RC))
    out = hermes.chain_text("soru", kind="system_eval")
    assert cagrilar == ["tencent/hy3:free", "gemini-flash-latest"]
    assert out["beyin"] == "nous" and out["text"] == DOLU
    assert out["model"] == "gemini-flash-latest", "künye hâlâ İSTENENİ yazıyor"
    assert out["model_istenen"] == "tencent/hy3:free", "iki anlam aynı ada binmiş"
    assert out["model_olculemedi"] is None
    ev = _olaylar("nous_chain_model_ayrismasi")
    assert len(ev) == 1 and ev[0]["cevap_veren"] == "gemini-flash-latest"
    assert ev[0]["istenen"] == "tencent/hy3:free" and ev[0]["beyin"] == "nous"
    assert len(ev[0]["detail"]) >= 20


def test_k3_TERS_YON_TUZAGI_ajan_bos_gemini_dolu_kunye_GEMINIYI_tasir(zincir, monkeypatch):
    """TÜKETEN-OKUMANIN YANLIŞ YERDE OKUNMASI kusuru TERS YÖNDE üretirdi: kutuyu ayak ayrımı
    yapmadan okumak, gemini'nin cevabına BOŞ kutuyu (None künye) yapıştırırdı. Ajan ayağı boş
    dönüp gemini konuştuğunda künye gemini'nin GERÇEKTEN çağrılan adını taşımalı."""
    _sir(monkeypatch, NOUS_MODEL="tencent/hy3:free", GEMINI_API_KEY="g",
         GEMINI_MODEL="gemini-flash-latest")
    _ayaklar(monkeypatch, gemini=DOLU)
    cagrilar = _surec(monkeypatch, lambda m: _Sonuc(BOS_RC))
    out = hermes.chain_text("soru", kind="t")
    assert cagrilar and out["beyin"] == "gemini" and out["text"] == DOLU
    assert out["model"] == "gemini-flash-latest", "ajan kutusu gemini künyesini yuttu"
    assert out["model_olculemedi"] is None
    assert out["neden"]["nous"], "boş dönen ajan ayağının sebebi kaydedilmemiş"


def test_k4_HICBIRI_DOLU_DEGIL_None_ve_NEDEN(zincir, monkeypatch):
    """UYDURMA YASAĞI: zincirden metin çıkmadıysa künye None + neden; beyan alanı yine durur."""
    _sir(monkeypatch)                                   # hiçbir sağlayıcı hazır değil
    monkeypatch.setattr(hermes, "_hermes_bin", lambda: None)
    _ayaklar(monkeypatch)
    out = hermes.chain_text("soru", kind="t")
    assert out["text"] is None and out["beyin"] is None and out["model"] is None
    assert out["model_kaynagi"] == "cevap_veren"
    assert out["model_olculemedi"] == hermes.ZINCIR_MODEL_YOK and len(hermes.ZINCIR_MODEL_YOK) >= 20
    assert out["model_istenen"] is None                 # deterministik yolda ad UYDURULMAZ


def test_k5_BAYAT_KUNYE_claude_cevabina_YAPISMAZ(zincir, monkeypatch):
    """Kutuyu tek yerde okumanın ikinci tuzağı: aynı iş parçacığında ÖNCEKİ bir `_agent_call`in
    tüketilmemiş künyesi, hiç ajan çağırmayan bir cevaba yapışırdı. Okuma ayağa bağlı olduğu için
    kutuya DOKUNULMAZ — kanıt: chain_text'ten sonra künye hâlâ okunabilir durumdadır."""
    _sir(monkeypatch, NOUS_MODEL="isinma-model", HERMES_API_KEY="k")
    _surec(monkeypatch, lambda m: _Sonuc(0, DOLU))
    assert hermes._agent_call("ısınma", kind="t") == DOLU        # kutuda künye var, OKUNMADI
    _ayaklar(monkeypatch, claude=DOLU)
    out = hermes.chain_text("soru", kind="t")
    assert out["beyin"] == "claude" and out["model"] == hermes.MODEL
    assert out["model"] != "isinma-model", "bayat ajan künyesi claude'un cevabına yapıştı"
    assert hermes.cevap_veren_model()[0] == "isinma-model", "chain_text ilgisiz kutuyu tüketti"


def test_k6_ADSIZ_ZINCIR_metin_var_kunye_OLCULEMEDI(zincir, monkeypatch):
    """Metin geldi ama zincir adsızdı (CLI kendi varsayılanına gitti ve adı bildirmiyor): künye
    None + ZİNCİRİN kendi nedeni. Yapılandırmaya (`active_model()`) sessizce dönmek YASAK."""
    _sir(monkeypatch)                                   # NOUS_MODEL yok; ajan ikilisi hazır
    _ayaklar(monkeypatch)
    cagrilar = _surec(monkeypatch, lambda m: _Sonuc(0, DOLU))
    out = hermes.chain_text("soru", kind="t")
    assert cagrilar == [None] and out["text"] == DOLU and out["beyin"] == "nous"
    assert out["model"] is None
    assert out["model_olculemedi"] == hermes.AGENT_MODEL_YOK_ZINCIR
    assert out["model_istenen"] is None                 # KALEM 2 koruması aynı hâli None diyor
    assert _olaylar("nous_chain_model_ayrismasi") == []


def test_k7_PORTAL_AYAGI_istek_govdesindeki_ADI_tasir(zincir, monkeypatch):
    """Uzak (portal) nous ayağında künye ölçüm değil OLGUDUR: `_nous_text`in istek gövdesine
    yazdığı adın TEK kaynağı okunur — ikinci bir kopya yazmak bu turun kapattığı sınıftı."""
    _sir(monkeypatch, NOUS_ENDPOINT="https://portal.example/v1", NOUS_API_KEY="nk",
         NOUS_MODEL="Hermes-4-405B")
    _ayaklar(monkeypatch, portal=DOLU)
    out = hermes.chain_text("soru", kind="t")
    assert out["beyin"] == "nous" and out["model"] == "Hermes-4-405B"
    assert out["model"] == hermes._nous_portal_model() and out["model_olculemedi"] is None


def test_k8_KAYNAK_CIVISI_kunye_alani_artik_active_model_okumuyor():
    """YAPISAL ÇİVİ: `chain_text` içinde `active_model()` YALNIZ "istenen" için okunabilir; künye
    (`"model"`) alanına bağlanırsa kusur geri gelmiştir. Kutu okuması da AYAĞIN yanında kalmalı."""
    import ast
    import inspect
    src = inspect.getsource(hermes.chain_text)
    fn = ast.parse(src.lstrip()).body[0]
    for n in ast.walk(fn):
        if isinstance(n, ast.Dict):
            for anahtar, deger in zip(n.keys, n.values):
                if isinstance(anahtar, ast.Constant) and anahtar.value == "model":
                    assert not (isinstance(deger, ast.Call)
                                and getattr(deger.func, "id", None) == "active_model"), \
                        "künye yeniden yapılandırmayı okuyor (v245/v246 kusuru geri geldi)"
    assert src.count("cevap_veren_model()") == 1, "tüketen okuma birden çok yerde"
    assert "_nous_local()" in src and "_agent_call(" in src, "okuma noktası ajan ayağından koptu"


def test_k9_TUKETICI_SOZLESMESI_KIRILMADI_nous_eval(zincir, monkeypatch):
    """TÜKETİCİ ADIYLA: tek üretim tüketicisi `nous_eval.haftalik_degerlendirme` (nous_eval.py::haftalik_degerlendirme).
    GERÇEK `chain_text` dönüşüyle koşar; okuduğu dört anahtar (text/beyin/model/neden) yerinde."""
    _sir(monkeypatch)
    monkeypatch.setattr(hermes, "_hermes_bin", lambda: None)     # zincir boş → "kosulamadi" dalı
    _ayaklar(monkeypatch)
    out = hermes.chain_text("soru", kind="system_eval")
    for anahtar in ("text", "beyin", "model", "neden"):
        assert anahtar in out, f"tüketicinin okuduğu alan kayıp: {anahtar}"
    res = nous_eval.haftalik_degerlendirme(telemetri={"hafta": "2026-W33"}, yaz=False, kuyruk=False)
    assert res["kosu"]["durum"] == "kosulamadi" and res["kosu"]["model"] is None
    assert res["kosu"]["zincir_neden"], "zincir nedenleri tüketiciye ulaşmadı"


# ==================================================================================================
# KALEM 2 — active_model() uydurma koruması
# ==================================================================================================
def test_m1_YEREL_AJAN_ADSIZ_active_model_None_der(zincir, monkeypatch):
    """ÖLÇÜLEN KUSUR: aynı yapılandırmada `_model_id('nous')=None` iken `active_model()`
    `'Hermes-4-405B'` döndürüyordu — hiç çağrılmamış bir ad. Artık ikisi de dürüst."""
    _sir(monkeypatch)                                   # NOUS_MODEL yok, ajan ikilisi var
    assert hermes.active_brain() == "nous"
    assert hermes._model_id("nous") is None
    assert hermes.active_model() is None, "uydurma koruması taşınmamış"


def test_m2_YEREL_AJAN_ADLI_ad_aynen_doner(zincir, monkeypatch):
    """Koruma yalnız ADSIZ hâli kapsar: ad varsa (ve ölü-ad göçünden geçtiyse) aynen raporlanır."""
    _sir(monkeypatch, NOUS_MODEL="gemini-3.5-flash")     # bilinen-ölü ad → alias'a göçer
    assert hermes.active_model() == "gemini-flash-latest" == hermes._model_id("nous")


def test_m3_TEK_KAYNAK_active_model_model_id_ile_HER_SAGLAYICIDA_ayni(zincir, monkeypatch):
    """İKİNCİ KOPYA KALMADI: iki gövde ayrışabildiği için koruma birinde unutulmuştu."""
    for vals in ({"HERMES_API_KEY": "k"},
                 {"NOUS_MODEL": "portal-x", "NOUS_ENDPOINT": "https://p/v1", "NOUS_API_KEY": "n"},
                 {"GEMINI_API_KEY": "g", "GEMINI_MODEL": "gemini-flash-latest"},
                 {},                                     # yerel ajan + adsız (kusurun hâli)
                 {"HERMES_BRAIN_ORDER": "gemini"}):       # hiçbiri hazır değil → deterministik
        _sir(monkeypatch, **vals)
        assert hermes.active_model() == hermes._model_id(hermes.active_brain()), \
            f"iki kaynak ayrıştı: {vals}"
    import inspect
    assert "_model_id(active_brain())" in inspect.getsource(hermes.active_model), \
        "active_model kendi kopyasını geri yazmış"


def test_m4_CAGIRANLAR_None_TASIYOR_hermes_runtime_diske_yazar(zincir, monkeypatch):
    """YAYILMA ALANI ÖLÇÜLDÜ: iki üretim çağıranı `hermes_runtime._persist` ve `.status`.
    İkisi de None'u taşıyor — pano `s.model || '—'` basar, ölçülemeyen ad UYDURULMAZ."""
    _sir(monkeypatch)                                   # yerel ajan + adsız → model ölçülemez
    st = hermes_runtime.status()
    assert st["model"] is None and st["brain"] == "nous"
    hermes_runtime._persist()
    disk = store.read_json(hermes_runtime.STATUS_FILE, {})
    assert disk["model"] is None, "ölçülemeyen model adı diske uydurularak yazıldı"
    assert disk["brain_availability"]["nous"]["model_id"] is None    # aynı gerçek, aynı cevap


# ==================================================================================================
# KALEM 3 — ÖLÇÜM ÇİVİSİ: kalibrasyonun girdisi PLAN SATIRIDIR, künye DEĞİL
# [2026-08-24 ÇİVİ TAZELENDİ — Ö-39 tasarım-kapanışı]: çivinin ilk hâli "atıf eklenirse doğru yer
# plan satırıdır" diyordu ve `_stamp_llm_opinions` gövdesinde "model" kelimesini YASAKLIYORDU.
# Rol-1 o yolu REDDETTİ (ROADMAP §4-39, 2026-08-24): plan satırına ikinci alan yazmak
# `test_authority_boundaries_v77::test_c3` yasasını değiştirmeyi gerektirir. Seçilen yol (b) —
# AYRI atıf defteri — yasayı korur. Çivi bu yüzden SİLİNMEDİ, YÖNÜ düzeltildi: yasak artık
# "damga model yazmasın" değil, "damga modeli PLAN SATIRINA yazmasın"dır; künyenin gittiği yer
# `plan_atif.jsonl`tır ve orası KALEM 5'te ayrıca çivilenir.
# ==================================================================================================
def test_n1_kalibrasyonun_girdisi_PLAN_SATIRIDIR_kunye_degil(sandbox_state):
    """ÖLÇÜLDÜ (v246-B): `llm_opinion_calibration` ÇİFTLERİ `trade_plans.jsonl`ın `llm_opinion`
    alanından kurulur; `candidate_review.json`ın `model` alanı bu yola HİÇ girmez (o depo TEK-BELGE,
    yalnız SON günü tutar — geçmiş atıf üretemez). Çivi kapıyı kapatmaz, ÖLÇÜMÜ dondurur: çift
    kurma yolu künyeden BAĞIMSIZ kalmalı; künye ayrı defterden GELİR (KALEM 5), çifti tanımlamaz."""
    import inspect
    kaynak = inspect.getsource(analytics.llm_opinion_calibration)
    assert "candidate_review" not in kaynak
    assert 'plans.get(pid)' in kaynak and 'plan.get("llm_opinion")' in kaynak
    # ve damga PLAN SATIRINA model yazmıyor: yazan tek yer `_stamp_llm_opinions`
    damga = inspect.getsource(hermes._stamp_llm_opinions)
    assert 'pl["llm_opinion"] = op_by_ticker[pl["ticker"]]' in damga
    yama = inspect.getsource(hermes._stamp_llm_opinions).split("def _patch_plans")[1].split("def ")[0]
    assert "model" not in yama, "plan satırı yaması model alanı yazıyor — yetki sınırı yasası kırılır"
    # ölçümün canlı hâli: damga plan satırında ATIL kalmak zorunda (yetki sınırı testiyle çivili)
    store.write_jsonl("trade_plans.jsonl",
                      [{"id": "P1", "date": "2026-08-14", "ticker": "AAA"}])
    hermes._stamp_llm_opinions("2026-08-14", [{"ticker": "AAA", "opinion": "destekle"}])
    satir = store.read_jsonl("trade_plans.jsonl")[0]
    assert satir["llm_opinion"] == "destekle"
    assert not [k for k in satir if "model" in k or "beyin" in k], \
        "plan satırı model atıfı taşıyor — ölçüm güncellenmeli"


# ==================================================================================================
# KALEM 4 (WP7-40) — TÜKETİCİ BEYANLARI TAŞIYOR: künye ailesinin son bacağı
# `chain_text` üç beyanı (`model_kaynagi` · `model_olculemedi` · `model_istenen`) 2026-08-14'ten beri
# ÜRETİYOR ama tek üretim tüketicisi (`nous_eval.haftalik_degerlendirme`) onları OKUMUYORDU: beyanlar
# fonksiyon dönüşünde ölüyor, iki kalıcı defter (`nous_eval_runs.json` · `improvement_proposals.jsonl`)
# yalnız çıplak `model` alanını taşıyordu. Çıplak alan tek başına "cevap veren mi, istenen mi?"
# sorusunu CEVAPLAYAMAZ — v245 künye kusurunun deftere düşen hâli tam buydu.
# ==================================================================================================
_KUNYE_NEDEN = ("cevap veren model ölçülemedi: yerel ajan künye kutusu boş döndü "
                "(alt süreç adı yazmadı)")


def _tel_kunye() -> dict:
    """Kanıt atfı GEÇEBİLEN küçük telemetri paketi (v131'deki `_tel`in aynı deseni: gerçek alan
    adları ve gerçek sayılar — jetonsuz paket kalite kapısından her öneriyi düşürürdü)."""
    from meridian import analytics
    return {"hafta": "2026-W31",
            "bolum_adlari": list(analytics.TELEMETRY_SECTIONS),
            "bolumler": {"kar_selalesi": {"n": 95, "genel": {"net_r": -0.0421,
                                                             "sinyal_mfe_r": 0.9648}}},
            "bounds_dugmeleri": ["stop_loss_atr_mult"]}


def _oneri_kunye() -> dict:
    """Kalite kapısından GEÇEN tek öneri (şekil=tasarim → kuyruk yolu yok, bounds'a bağımlı değil)."""
    return {"alan": "kar_selalesi",
            "gozlem": "kar_selalesi bölümünde net_r -0.0421 iken sinyal_mfe_r 0.9648 — çıkış "
                      "sunulan hareketin neredeyse tamamını geri veriyor",
            "oneri": "çıkış eşiğini sıkılaştır",
            "beklenen_etki": "net_r +0.10 yönünde",
            "onerilen_olcum": "profit_waterfall geri_verilen_r yeniden ölçülür",
            "oncelik": "yuksek", "sekil": "tasarim"}


def _chain_sapla(monkeypatch, **ek):
    """`chain_text`i GERÇEK dönüş sözleşmesiyle sapla (üç beyan dahil); `ek` alanları ezer."""
    import json as _json
    cevap = {"text": _json.dumps({"oneriler": [_oneri_kunye()]}, ensure_ascii=False),
             "beyin": "nous", "model": None, "model_kaynagi": "cevap_veren",
             "model_olculemedi": _KUNYE_NEDEN, "model_istenen": "tencent/hy3:free", "neden": {}}
    cevap.update(ek)
    monkeypatch.setattr(hermes, "chain_text", lambda *a, **k: cevap)
    return cevap


def test_w1_UC_BEYAN_KOSU_DEFTERINE_dusuyor(sandbox_state, monkeypatch):
    """ÖLÇÜLEMEYEN KÜNYE: `model` None kalır, NEDENİ yanında durur ve "istenen" ad künye alanına
    SIZMAZ (uydurma yasağı — `active_model()`e sessizce dönülmez)."""
    _chain_sapla(monkeypatch)
    nous_eval.haftalik_degerlendirme(telemetri=_tel_kunye(), hafta="2026-W31")
    kosu = (store.read_json("nous_eval_runs.json", {}) or {})["haftalar"]["2026-W31"]
    assert kosu["beyin"] == "nous"
    assert kosu["model"] is None, "ölçülemeyen künye deftere uydurularak yazıldı"
    assert kosu["model_olculemedi"] == _KUNYE_NEDEN, "ölçülemedi nedeni koşu defterine düşmedi"
    assert kosu["model_kaynagi"] == "cevap_veren", "kaynak beyanı koşu defterine düşmedi"
    assert kosu["model_istenen"] == "tencent/hy3:free", "istenen ad koşu defterine düşmedi"
    assert "tencent" not in str(kosu["model"] or ""), "istenen ad künye alanına sızmış"


def test_w2_UC_BEYAN_ONERI_DEFTERINE_dusuyor(sandbox_state, monkeypatch):
    """İKİNCİ DEFTER: öneri satırı da beyanları taşır — `improvement_proposals.jsonl` satırından
    "bu öneriyi hangi model yazdı, ölçülebildi mi?" sorusu CEVAPLANABİLİR olmalı."""
    from meridian import ledgers
    _chain_sapla(monkeypatch)
    nous_eval.haftalik_degerlendirme(telemetri=_tel_kunye(), hafta="2026-W31")
    satirlar = store.read_jsonl("improvement_proposals.jsonl")
    assert len(satirlar) == 1, f"öneri defteri beklenen satırı taşımıyor: {satirlar}"
    s = satirlar[0]
    assert s["beyin"] == "nous" and s["model"] is None
    assert s["model_olculemedi"] == _KUNYE_NEDEN
    assert s["model_kaynagi"] == "cevap_veren"
    assert s["model_istenen"] == "tencent/hy3:free"
    # EK ALAN SÖZLEŞMEYİ KIRMAZ: `required` kümesi değişmedi, satır hâlâ uyumlu.
    assert ledgers.validate_row("improvement_proposals.jsonl", s) == []


def test_w3_OLCULEN_KUNYE_neden_YOK_ad_YAZILIR(sandbox_state, monkeypatch):
    """Simetrik hâl: künye ÖLÇÜLDÜYSE ad yazılır ve `model_olculemedi` None kalır — "ölçülemedi"
    damgası her satıra basılan bir süs değildir."""
    _chain_sapla(monkeypatch, model="gemini-flash-latest", model_olculemedi=None)
    nous_eval.haftalik_degerlendirme(telemetri=_tel_kunye(), hafta="2026-W31")
    kosu = (store.read_json("nous_eval_runs.json", {}) or {})["haftalar"]["2026-W31"]
    assert kosu["model"] == "gemini-flash-latest" and kosu["model_olculemedi"] is None
    assert kosu["model_istenen"] == "tencent/hy3:free"
    s = store.read_jsonl("improvement_proposals.jsonl")[0]
    assert s["model"] == "gemini-flash-latest" and s["model_olculemedi"] is None


def test_w4_KOSULAMADI_DALI_da_beyanlari_tasir(sandbox_state, monkeypatch):
    """Zincir hiç metin döndürmediğinde de künye beyanları kayda geçer: `kosulamadi` kaydı
    "hangi ad istendi, niçin ölçülemedi" sorusunu cevaplayabilmeli."""
    _chain_sapla(monkeypatch, text=None)
    nous_eval.haftalik_degerlendirme(telemetri=_tel_kunye(), hafta="2026-W31")
    kosu = (store.read_json("nous_eval_runs.json", {}) or {})["haftalar"]["2026-W31"]
    assert kosu["durum"] == "kosulamadi"
    assert kosu["model"] is None and kosu["model_olculemedi"] == _KUNYE_NEDEN
    assert kosu["model_istenen"] == "tencent/hy3:free"


def test_w5_METIN_ENJEKTE_zincir_CAGRILMADI_neden_yazilir(sandbox_state, monkeypatch):
    """`text=` enjekte edildiğinde zincir HİÇ çağrılmaz — künye ölçülebileceği bir yer yoktur.
    Alan None kalır ve NEDENİ yazılır: sessiz bir None, "ölçtük ve boş çıktı" gibi okunurdu."""
    import json as _json
    monkeypatch.setattr(hermes, "chain_text",
                        lambda *a, **k: pytest.fail("metin enjekte iken zincir çağrıldı"))
    nous_eval.haftalik_degerlendirme(
        telemetri=_tel_kunye(), hafta="2026-W31",
        text=_json.dumps({"oneriler": [_oneri_kunye()]}, ensure_ascii=False))
    kosu = (store.read_json("nous_eval_runs.json", {}) or {})["haftalar"]["2026-W31"]
    assert kosu["model"] is None and kosu["model_istenen"] is None
    assert kosu["model_olculemedi"] == nous_eval.KUNYE_ZINCIR_CAGRILMADI
    assert len(kosu["model_olculemedi"]) >= 20


def test_w6_ESKI_SOZLESMELI_DONUS_sessiz_None_YAZMAZ(sandbox_state, monkeypatch):
    """GERİYE UYUM: beyan taşımayan (eski/saplı) bir zincir dönüşünde künye ölçülemedi sayılır ve
    NEDEN yazılır — beyansız dönüş "ölçtük, ad yok" gibi kaydedilemez."""
    import json as _json
    monkeypatch.setattr(hermes, "chain_text", lambda *a, **k: {
        "text": _json.dumps({"oneriler": [_oneri_kunye()]}, ensure_ascii=False),
        "beyin": "nous", "model": None, "neden": {}})
    nous_eval.haftalik_degerlendirme(telemetri=_tel_kunye(), hafta="2026-W31")
    kosu = (store.read_json("nous_eval_runs.json", {}) or {})["haftalar"]["2026-W31"]
    assert kosu["model"] is None
    assert kosu["model_kaynagi"] is None, "beyansız dönüşe kaynak damgası uydurulmuş"
    assert kosu["model_olculemedi"] == nous_eval.KUNYE_BEYANSIZ_DONUS


def test_w7_TUKETICI_CIVISI_uc_beyan_iki_deftere_de_bagli():
    """Statik çivi: üç beyan hem koşu kaydına hem öneri satırına bağlı kalmalı (biri kopunca
    defterlerden biri sessizce eski sözleşmeye döner)."""
    import inspect
    src = inspect.getsource(nous_eval)
    satir = inspect.getsource(nous_eval._oneri_kaydet)
    for alan in ("model_kaynagi", "model_olculemedi", "model_istenen"):
        assert f'"{alan}"' in src, f"koşu kaydı beyanı taşımıyor: {alan}"
        assert f'"{alan}"' in satir, f"öneri satırı beyanı taşımıyor: {alan}"
    # ve künye YAPILANDIRMADAN okunmuyor: AST'de `active_model()` ÇAĞRISI yok (yorumda geçen ad
    # sayılmaz — v246'nın kusuru bir çağrıydı, bir kelime değil).
    import ast
    for d in ast.walk(ast.parse(src)):
        if isinstance(d, ast.Call):
            ad = getattr(d.func, "id", None) or getattr(d.func, "attr", None)
            assert ad != "active_model", "tüketici künyeyi yapılandırmadan okumaya başlamış"


# ==================================================================================================
# KALEM 5 (Ö-39 / WP7 "künye turu"nun SON bacağı) — ATIF DEFTERİ: "görüşü HANGİ model yazdı"
# KALEM 3 çivisi (test_n1) kusuru ölçmüştü: kalibrasyonun girdisi plan satırıdır ve o satır künye
# TAŞIMAZ — taşıyamaz da, çünkü `test_authority_boundaries_v77::test_c3` plan satırına TEK anahtar
# (`llm_opinion`) yazılmasını YASA olarak çiviliyor. Tek kalıcı model defteri `agent_calls.jsonl`ta
# ise ticker ve plan günü YOK, üstelik `backfill_opinions` BUGÜNKÜ çağrıyla AYLAR öncesine damga
# vuruyor (canlı kanıt: 2026-08-16 koşumu 2026-02-26 ve 2026-04-14 planlarını damgaladı) — yani
# zaman-yakınlığı join'i YAPISAL olarak yanlıştı ve "yetkili danışman hangi modeldi?" sorusunun
# kalıcı bir cevabı YOKTU (terfi 2026-08-14'te açıldığı için soru akademik de değil).
# Rol-1 tasarım-kapanışı (ROADMAP §4-39, 2026-08-24; `docs/ELEME-WP7-2026-08-23.md` §6) YOL (b)'yi
# seçti: yasayı KIRMADAN ayrı bir append-only atıf defteri. Satır plan_id ↔ model ↔ iz_id üçlüsünü
# taşır, `backfill` bayrağıyla geriye-damgayı KENDİ BEYAN EDER ve tüketicisi İLK GÜNDEN bağlıdır
# (uyuyan-yol dersi / YASA 6: okuyucusuz defter açılmaz).
# ==================================================================================================
_ATIF_KUNYE = {"model": "gemini-flash-latest", "model_olculemedi": None,
               "model_kaynagi": "cevap_veren", "model_istenen": "tencent/hy3:free",
               "iz_id": "20260814T210334-review-1-0", "kind": "review", "backfill": False}


def _plan(pid: str, day: str, ticker: str) -> dict:
    return {"id": pid, "date": day, "ticker": ticker}


def _atif_satirlari() -> list:
    return store.read_jsonl(hermes.PLAN_ATIF_DEFTERI)


def test_o1_DAMGALANAN_HER_PLAN_ICIN_SOZLESMELI_atif_satiri(sandbox_state):
    """Defterin çekirdek sözleşmesi: damgalanan her plan için TEK satır, `ledgers.CONTRACTS`e uygun.
    Sözleşmesiz defter sınıfı bu depoda ölçülmüş bir hata ailesidir — satır doğmadan çivilenir."""
    from meridian import ledgers
    store.write_jsonl("trade_plans.jsonl", [_plan("P-2026-08-14-AAA", "2026-08-14", "AAA"),
                                            _plan("P-2026-08-14-BBB", "2026-08-14", "BBB")])
    hermes._stamp_llm_opinions("2026-08-14", [{"ticker": "AAA", "opinion": "destekle"},
                                              {"ticker": "BBB", "opinion": "karşı"}],
                               kunye=dict(_ATIF_KUNYE))
    satirlar = _atif_satirlari()
    assert len(satirlar) == 2, f"damgalanan her plan bir atıf satırı üretmeli: {satirlar}"
    for s in satirlar:
        assert ledgers.validate_row(hermes.PLAN_ATIF_DEFTERI, s) == [], f"sözleşme ihlali: {s}"
        assert s["model"] == "gemini-flash-latest" and s["model_kaynagi"] == "cevap_veren"
        assert s["model_istenen"] == "tencent/hy3:free" and s["model_olculemedi"] is None
        assert s["iz_id"] == "20260814T210334-review-1-0" and s["kind"] == "review"
        assert s["plan_date"] == "2026-08-14" and s["backfill"] is False
    assert {s["plan_id"] for s in satirlar} == {"P-2026-08-14-AAA", "P-2026-08-14-BBB"}
    assert {s["ticker"] for s in satirlar} == {"AAA", "BBB"}


def test_o2_OLCULEMEYEN_KUNYE_None_plus_NEDEN_ISTENEN_sizmaz(sandbox_state):
    """UYDURMA YASAĞI defterin KENDİSİNDE: ad ölçülemediyse `model` None kalır, nedeni yanında
    durur ve "istenen" ad `model` alanına SIZMAZ — v245 kusurunun deftere düşmüş hâli tam buydu."""
    store.write_jsonl("trade_plans.jsonl", [_plan("P-2026-08-14-AAA", "2026-08-14", "AAA")])
    hermes._stamp_llm_opinions("2026-08-14", [{"ticker": "AAA", "opinion": "destekle"}],
                               kunye={**_ATIF_KUNYE, "model": None,
                                      "model_olculemedi": hermes.AGENT_MODEL_YOK_ZINCIR})
    s = _atif_satirlari()[0]
    assert s["model"] is None
    assert s["model_olculemedi"] == hermes.AGENT_MODEL_YOK_ZINCIR
    assert len(s["model_olculemedi"]) >= 20
    assert s["model_istenen"] == "tencent/hy3:free"
    assert "tencent" not in str(s["model"] or ""), "istenen ad künye alanına sızmış"


def test_o3_KUNYESIZ_CAGRI_sessiz_None_YAZMAZ(sandbox_state):
    """Çağıran künye paketi vermezse satır yine yazılır ama NEDENİNİ taşır: sessiz bir None
    "ölçtük, ad yoktu" diye okunurdu; oysa gerçek "bu yol künyeyi hiç okumuyor"dur."""
    store.write_jsonl("trade_plans.jsonl", [_plan("P-2026-08-14-AAA", "2026-08-14", "AAA")])
    hermes._stamp_llm_opinions("2026-08-14", [{"ticker": "AAA", "opinion": "destekle"}])
    s = _atif_satirlari()[0]
    assert s["model"] is None and s["model_kaynagi"] is None
    assert s["model_olculemedi"] == hermes.KUNYE_DAMGA_VERILMEDI
    assert len(hermes.KUNYE_DAMGA_VERILMEDI) >= 20


def test_o4_GERIYE_DAMGA_KENDINI_BEYAN_EDER(sandbox_state):
    """Ö-39'un KÖK kusuru: dolgu bugünkü çağrıyla aylar öncesine damga vuruyor ve zaman-yakınlığı
    join'i bunu ayırt edemiyordu. Satır artık iki tarihi YAN YANA taşır (`ts` bugün, `plan_date`
    Şubat) ve `backfill=True` der — okuyucu tahmin etmez, OKUR."""
    store.write_jsonl("trade_plans.jsonl", [_plan("P-2026-02-26-AAA", "2026-02-26", "AAA")])
    hermes._stamp_llm_opinions("2026-02-26", [{"ticker": "AAA", "opinion": "karşı"}],
                               kunye={**_ATIF_KUNYE, "kind": "backfill", "backfill": True})
    s = _atif_satirlari()[0]
    assert s["backfill"] is True and s["kind"] == "backfill"
    assert s["plan_date"] == "2026-02-26"
    assert s["ts"][:10] != s["plan_date"], "geriye-damga bugünkü `ts` ile ayrışmıyor"


def test_o5_IKINCI_DAMGA_ATIF_URETMEZ(sandbox_state):
    """Damga var olan `llm_opinion`ı EZMEZ; ezmediği satır için atıf da YAZILMAZ. Yazsaydı defter
    aynı görüşü iki modele atfeder ve kırılımın paydası sessizce şişerdi."""
    store.write_jsonl("trade_plans.jsonl", [_plan("P-2026-08-14-AAA", "2026-08-14", "AAA")])
    gorus = [{"ticker": "AAA", "opinion": "destekle"}]
    hermes._stamp_llm_opinions("2026-08-14", gorus, kunye=dict(_ATIF_KUNYE))
    hermes._stamp_llm_opinions("2026-08-14", gorus,
                               kunye={**_ATIF_KUNYE, "model": "baska-model"})
    satirlar = _atif_satirlari()
    assert len(satirlar) == 1, f"ezilmeyen damga ikinci kez atfedilmiş: {satirlar}"
    assert satirlar[0]["model"] == "gemini-flash-latest"


def test_o6_PLAN_SATIRI_YASASI_KIRILMADI(sandbox_state):
    """YOL (b)'nin varlık sebebi: atıf AYRI deftere gider, plan satırı TEK anahtar almaya devam
    eder. Bu, `test_authority_boundaries_v77::test_c3` yasasının bu turdaki yerel çivisidir."""
    store.write_jsonl("trade_plans.jsonl", [_plan("P-2026-08-14-AAA", "2026-08-14", "AAA")])
    hermes._stamp_llm_opinions("2026-08-14", [{"ticker": "AAA", "opinion": "destekle"}],
                               kunye=dict(_ATIF_KUNYE))
    satir = store.read_jsonl("trade_plans.jsonl")[0]
    assert satir["llm_opinion"] == "destekle"
    assert set(satir) == {"id", "date", "ticker", "llm_opinion"}, \
        f"plan satırına ikinci anahtar yazılmış: {satir}"
    assert _atif_satirlari(), "atıf defterine düşmediyse künye yine kayıp demektir"


def test_o7_TUKETICI_ILK_GUNDEN_kalibrasyon_MODEL_KIRILIMI_basar(sandbox_state):
    """UYUYAN-YOL DERSİ (YASA 6): okuyucusuz defter AÇILMAZ. `llm_opinion_calibration` çiftleri
    plan_id üstünden atıf defteriyle birleştirir; "hangi model kaç çift üretti, ortalama R'si ne,
    kaçı geriye-damga" sorusu İLK GÜNDEN cevaplanabilir olmalı."""
    store.write_jsonl("trade_plans.jsonl", [_plan("P-2026-08-14-AAA", "2026-08-14", "AAA"),
                                            _plan("P-2026-08-14-BBB", "2026-08-14", "BBB")])
    hermes._stamp_llm_opinions("2026-08-14", [{"ticker": "AAA", "opinion": "destekle"}],
                               kunye=dict(_ATIF_KUNYE))
    hermes._stamp_llm_opinions("2026-08-14", [{"ticker": "BBB", "opinion": "karşı"}],
                               kunye={**_ATIF_KUNYE, "model": "nvidia/nemotron",
                                      "kind": "backfill", "backfill": True})
    store.write_jsonl("trades.jsonl",
                      [{"plan_id": "P-2026-08-14-AAA", "r_multiple": 1.5},
                       {"plan_id": "P-2026-08-14-BBB", "r_multiple": -0.5}])
    kir = analytics.llm_opinion_calibration()["model_kirilim"]
    assert kir["n_cift"] == 2 and kir["atifli_n"] == 2 and kir["atifsiz_n"] == 0
    assert kir["modeller"]["gemini-flash-latest"] == {"n": 1, "avg_r": 1.5, "backfill_n": 0}
    assert kir["modeller"]["nvidia/nemotron"] == {"n": 1, "avg_r": -0.5, "backfill_n": 1}
    assert kir["olculemeyen_n"] == 0


def test_o8_ATIFSIZ_CIFT_SAYILIR_uydurulmaz(sandbox_state):
    """Atıf defteri BUGÜN doğdu; ondan ÖNCEKİ çiftlerin künyesi yoktur ve olmayacaktır (retro damga
    yasağı). Kırılım o çiftleri bir modele YAMAMAZ — ayrı sayar."""
    store.write_jsonl("trade_plans.jsonl",
                      [{"id": "P-2026-07-01-OLD", "date": "2026-07-01", "ticker": "OLD",
                        "llm_opinion": "destekle"}])
    store.write_jsonl("trades.jsonl", [{"plan_id": "P-2026-07-01-OLD", "r_multiple": 0.4}])
    kir = analytics.llm_opinion_calibration()["model_kirilim"]
    assert kir["n_cift"] == 1 and kir["atifli_n"] == 0 and kir["atifsiz_n"] == 1
    assert kir["modeller"] == {}
    assert len(kir["not"]) >= 20


def test_o9_SOZLESME_YAZARI_ve_TUKETICISI_BEYANLI():
    """Statik çivi: defter `ledgers.CONTRACTS`ta, yazarı `hermes.py`, tüketicisi `analytics`.
    Beyansız bir yazar belirirse `ledgers.writer_violations` onu yakalar — bu satır o taramanın
    dayandığı beyanın kendisidir."""
    from meridian import ledgers
    c = ledgers.CONTRACTS[hermes.PLAN_ATIF_DEFTERI]
    assert c.writers == ("hermes.py",)
    assert "analytics" in c.consumers
    for alan in ("ts", "plan_id", "ticker", "plan_date", "kind", "model", "model_kaynagi",
                 "model_olculemedi", "model_istenen", "iz_id", "backfill"):
        assert alan in c.required, f"sözleşme alanı eksik: {alan}"
    assert len(c.note) >= 20


def test_o10_REVIEW_YOLU_UCTAN_UCA_kunyeyi_indirir(zincir, monkeypatch):
    """UÇTAN UCA (canlı yolun birebir eşleniği): birincil ayak boş, yedek dolu → atıf satırı
    YEDEĞİ yazar. `candidate_review.json` TEK-BELGE deposudur (yalnız son günü tutar), yani bu
    soru ancak append-only defterde kalıcı olarak cevaplanabilir."""
    monkeypatch.setattr(hermes, "_skill_preload", lambda *a, **k: ())
    _sir(monkeypatch, NOUS_MODEL="tencent/hy3:free", NOUS_FALLBACK_MODEL="gemini-flash-latest")
    _ayaklar(monkeypatch)
    gorus = ('{"reviews": [{"ticker": "VLO", "opinion": "destekle", "note": "taban sıkı"}]}\n'
             'Messages: 2 (1 user, 0 tool calls)')
    _surec(monkeypatch, lambda m: _Sonuc(0, gorus) if m == "gemini-flash-latest" else _Sonuc(BOS_RC))
    store.write_jsonl("trade_plans.jsonl", [_plan("P-2026-08-13-VLO", "2026-08-13", "VLO")])
    res = hermes.review_candidates("2026-08-13")
    assert res and res["model"] == "gemini-flash-latest"
    s = _atif_satirlari()
    assert len(s) == 1, f"inceleme yolu atıf yazmadı: {s}"
    s = s[0]
    assert s["plan_id"] == "P-2026-08-13-VLO" and s["ticker"] == "VLO"
    assert s["model"] == "gemini-flash-latest" and s["model_istenen"] == "tencent/hy3:free"
    assert s["model_kaynagi"] == "cevap_veren" and s["model_olculemedi"] is None
    assert s["kind"] == "review" and s["backfill"] is False
    assert s["iz_id"], "iz_id yazılmadı — `agent_calls.jsonl` join'i kurulamaz"
    izler = [r for r in store.read_jsonl("agent_calls.jsonl") if r.get("iz_id") == s["iz_id"]]
    assert len(izler) == 1 and izler[0]["model"] == "gemini-flash-latest", \
        "iz_id `agent_calls.jsonl` ile birleşmiyor — join anahtarı ölü"


def test_o11_BACKFILL_YOLU_UCTAN_UCA_kunyeyi_indirir(zincir, monkeypatch):
    """Dolgu yolu künyeyi ESKİDEN HİÇ OKUMUYORDU (`_stamp_llm_opinions` oradan künyesiz çağrılıyordu)
    — Ö-39'un canlı kanıtı bu yoldan çıkmıştı. Artık kendi çağrısının künyesini okur ve satırı
    `backfill=True` ile indirir."""
    monkeypatch.setattr(hermes, "_skill_preload", lambda *a, **k: ())
    _sir(monkeypatch, NOUS_MODEL="gemini-flash-latest")
    gorus = ('{"reviews": [{"ticker": "AAA", "opinion": "karşı", "note": "n"}]}\n'
             'Messages: 2 (1 user, 0 tool calls)')
    _surec(monkeypatch, lambda m: _Sonuc(0, gorus))
    store.write_jsonl("trade_plans.jsonl", [_plan("P-2026-02-26-AAA", "2026-02-26", "AAA")])
    store.write_jsonl("trades.jsonl", [{"plan_id": "P-2026-02-26-AAA", "r_multiple": -1.0}])
    out = hermes.backfill_opinions(max_days=1)
    assert out["days_processed"] == 1
    s = _atif_satirlari()
    assert len(s) == 1, f"dolgu yolu atıf yazmadı: {s}"
    s = s[0]
    assert s["plan_id"] == "P-2026-02-26-AAA" and s["plan_date"] == "2026-02-26"
    assert s["model"] == "gemini-flash-latest" and s["model_kaynagi"] == "cevap_veren"
    assert s["backfill"] is True and s["kind"] == "backfill"
    assert s["ts"][:10] != s["plan_date"], "aylar öncesine vurulan damga kendini beyan etmiyor"
