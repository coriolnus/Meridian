"""test_ogrenme_hafiza_kunye_v245.py — İKİ KÖK: exploit yolunda HAFIZA + künyede CEVAP VEREN model.

KALEM 1 — TEKRAR DESENİNİN KÖKÜ (ROADMAP Ö-28c; ölçüm docs/TESHIS-OGRENME-TIKANIKLIGI-2026-08-13.md)
`reflect.propose_deterministic`te `already_failed` kontrolü YALNIZ `explore` dalının içindeydi;
varsayılan exploit yolunda hafıza YOKTU. Ölçülen bedel: `stop_loss_atr_mult=2.1` defterde 21 kez
(1 backtest reti + 20 guard reti) — bounds o düğmede 33 adım-üstü değer taşırken 32'sine HİÇ
bakılmadı. Döngüyü kıran şey üretici değil guard'ın kara listesiydi.
BU DOSYANIN ÇİVİLERİ: (a) aynı değer ikinci kez ÖNERİLMEZ · (b) hafıza GERÇEKTEN okunuyor
(pozitif + negatif kontrol; "başarısız" tanımı guard'ınkiyle aynı küme) · (c) tüm adaylar elenirse
durum İŞARETLİ (olay + `memory_exhausted`) ve çağıran sözleşmesi kırılmıyor · (d) explore yolunun
kendi dönüşü DEĞİŞMEDİ.

KALEM 2 — KÜNYE "İSTENEN"İ DEĞİL "CEVAP VEREN"İ YAZAR (canlı ölçüm 2026-08-13, A1):
    20:37:26  agent_call kind=review model=tencent/hy3:free      attempt=1 empty=True  rc=1
    20:37:31  agent_call kind=review model=gemini-flash-latest   attempt=2 empty=False rc=0
    20:37:32  candidate_review.json → "model": "tencent/hy3:free"
Görüşü ikinci model yazdı, künye birinciyi söyledi (`active_model()` YAPILANDIRMAYI okur). Bedeli:
tencent 56 çağrının 56'sında boş döndü ama pano haftalarca `TENCENT/HY3:FREE` yazdı — hatalı künye
ARIZAYI GİZLEDİ.
BU DOSYANIN ÇİVİLERİ: (a) zincir ilk denemede dolu → künye birincil · (b) ilk boş/ikinci dolu →
künye İKİNCİ (bu gecenin vakası) · (c) hiçbiri dolu değil → None + neden · (d) `_agent_call`in
dönüş türü ve mevcut çağıranları KIRILMADI.

Ağ/gerçek alt süreç YOK: `subprocess.run` saplı, `_hermes_bin` sahte, state sandbox'ta.
"""
import subprocess

import pytest

from meridian import config, guard, hermes, memory, reflect, store

KNOB = "stop_loss_atr_mult"      # canlı vakanın düğmesi (bounds: 0.8..4.0, adım 0.1)


# ==================================================================================================
# KALEM 1 — EXPLOIT YOLUNDA HAFIZA
# ==================================================================================================
@pytest.fixture
def sezgisel_stop(sandbox_state):
    """Sezgiseli SABİTLE: son 40 işlemin hepsi `stop` → `hvar=stop_loss_atr_mult, hdir=+1`.
    Böylece merdiven 2.0'dan yukarı yürür ve testler değeri tahmin etmez, HESAPLAR."""
    store.write_jsonl("trades.jsonl",
                      [{"exit_reason": "stop", "r_multiple": -1.0} for _ in range(40)])
    return sandbox_state


def _cur():
    return float(config.load_strategy()["params"][KNOB])


def _adim(k: int) -> float:
    """Sezgiselin yönünde k'ıncı adım değeri (bounds'tan türetilir — sabit yazılmaz)."""
    b = config.bounds()[KNOB]
    return round(min(b["max"], _cur() + k * b["step"]), 4)


def _defter(*ciftler, status="rejected_by_backtest"):
    for var, val in ciftler:
        memory.record({"variable": var, "new": val, "status": status,
                       "rationale": "fikstür", "version_from": 1})


def _olaylar(ad):
    return [r for r in store.read_jsonl("events.jsonl") if r.get("event") == ad]


def test_a1_NEGATIF_KONTROL_bos_defterde_tek_adim_aynen_doner(sezgisel_stop):
    """Hafıza BOŞKEN davranış eski hâliyle birebir: sezgiselin tek adımı. Bu testin işi, sonraki
    testteki kaymanın merdivenin kendisinden değil HAFIZADAN geldiğini kanıtlamaktır."""
    p = reflect.propose_deterministic()
    assert p["variable"] == KNOB and p["new"] == _adim(1)
    assert p["memory_exhausted"] is False


def test_a2_POZITIF_KONTROL_denenmis_deger_ikinci_kez_onerilmez(sezgisel_stop):
    """21 tekrarın kökü: k=1 defterde başarısızsa üretici k=2'ye geçer — DEĞİŞKEN ve YÖN aynı kalır."""
    _defter((KNOB, _adim(1)))
    p = reflect.propose_deterministic()
    assert p["variable"] == KNOB, "hafıza değişkeni değiştirdi — sezgiselin teşhisi korunmalıydı"
    assert p["new"] == _adim(2)
    assert p["new"] > _cur(), "yön ters çevrildi — sezgiselin teşhisi çürütüldü"
    assert "hafıza" in p["rationale"] and str(p["new"]) not in ("", "None")


def test_a3_ARDISIK_TEKRAR_YOK_merdiven_yurur(sezgisel_stop):
    """CANLI DESENİN TAM TERSİ: aynı sezgisel üst üste koşsa bile aynı değer bir daha çıkmaz.
    Defterde 2.1 varken 2.1'i, 2.1+2.2 varken 2.2'yi öneremez."""
    gorulen = []
    for _ in range(5):
        p = reflect.propose_deterministic()
        assert p["new"] not in gorulen, f"aynı değer ikinci kez önerildi: {p['new']} ({gorulen})"
        gorulen.append(p["new"])
        _defter((KNOB, p["new"]))          # kapı reddetti → defter büyüdü
    assert gorulen == [_adim(k) for k in range(1, 6)]


def test_a4_BASARISIZ_TANIMI_guardin_kara_listesiyle_AYNI(sezgisel_stop):
    """İkinci bir "başarısız" tanımı üretilmedi: hafıza YALNIZ guard'ın kalıcı kara listesini
    (`rejected_by_backtest` / `rolled_back`) okur. `rejected_by_guard` ya da `shipped` bir satır
    değeri BLOKLAMAZ — aksi hâlde tekrar-reti kendi kendini besleyen bir kısırlığa dönerdi."""
    for gecersiz in ("rejected_by_guard", "shipped", "live", "queued_composite"):
        store.write_jsonl(memory.HYP, [])          # defteri sıfırla
        _defter((KNOB, _adim(1)), status=gecersiz)
        assert reflect.propose_deterministic()["new"] == _adim(1), \
            f"{gecersiz} statüsü hafızaya girdi — guard'ın tanımıyla ayrıştı"
    for gecerli in ("rejected_by_backtest", "rolled_back"):
        store.write_jsonl(memory.HYP, [])
        _defter((KNOB, _adim(1)), status=gecerli)
        assert reflect.propose_deterministic()["new"] == _adim(2), \
            f"{gecerli} statüsü hafızaya GİRMEDİ"
    # ve tanım guard'ın kendi satırıyla ölçülür (kopya sabit değil, kaynağın kendisi):
    kaynak = (config.ROOT / "meridian" / "guard.py").read_text()
    assert '("rejected_by_backtest", "rolled_back")' in kaynak


def test_a5_TUM_ADAYLAR_ELENINCE_isaretli_ve_cagiran_kirilmiyor(sezgisel_stop):
    """SESSİZ KISIRLAŞMA YASAK: merdivenin tamamı defterdeyse üretici yeni hamle üretemez.
    Bu hâl (a) olayla, (b) `memory_exhausted` alanıyla GÖRÜNÜR olur; dönüş yine geçerli bir
    öneridir — `reflect --auto` CLI'ı `proposal['variable']` okur, None dönmek onu kırardı."""
    b = config.bounds()[KNOB]
    n = int(round((b["max"] - b["min"]) / b["step"])) + 1
    _defter(*[(KNOB, _adim(k)) for k in range(1, n + 1)])
    p = reflect.propose_deterministic()

    assert p["memory_exhausted"] is True
    assert p["variable"] == KNOB and p["new"] == _adim(1)      # dönüş DEĞERİ eski davranış
    assert "HAFIZA TÜKENDİ" in p["rationale"]
    ev = _olaylar("propose_deterministic_memory_exhausted")
    assert len(ev) == 1 and ev[0]["level"] == "warn"
    assert ev[0]["variable"] == KNOB and ev[0]["n_elenen"] == ev[0]["n_aday"] > 0
    assert len(ev[0]["detail"]) >= 20 and ev[0]["elenen"], "eleme dökümü olaydan okunamıyor"
    # ve kısırlık BİR KAPIYLA kapanır: guard aynı hamleyi tekrar diye reddeder (eski emniyet yerinde)
    v = guard.validate_change({"variable": KNOB, "new": p["new"]},
                              config.load_strategy()["params"], config.bounds(), config.goal(),
                              memory.all_hypotheses(), 0)
    assert not v.ok and any("already tried and failed" in r for r in v.reasons)


def test_a6_kenetlenen_yonde_de_sessiz_kalmaz(sandbox_state):
    """SINIR: sezgisel AŞAĞI derken düğme zaten tabandaysa merdiven tek adımda kenetlenir ve
    tüm adaylar no-op'tur. Bu da bir kısırlıktır ve aynı biçimde işaretlenir."""
    store.write_jsonl("trades.jsonl",
                      [{"exit_reason": "time_stop", "r_multiple": -0.2} for _ in range(40)])
    knob = "exit.time_stop_days"                       # sezgisel: time_stop baskın → hdir = -1
    lo = config.bounds()[knob]["min"]
    strat = config.load_strategy()
    strat["params"][knob] = lo                          # tabana kenetli
    config.dump_yaml(strat, config.strategy_path())
    p = reflect.propose_deterministic()
    assert p["variable"] == knob and p["memory_exhausted"] is True
    assert _olaylar("propose_deterministic_memory_exhausted")[0]["variable"] == knob


def test_a7_EXPLORE_yolunun_davranisi_DEGISMEDI(sezgisel_stop):
    """Explore dalının KENDİ dönüşü dokunulmadan durur: UCB sıralaması, bakir düğme tercihi ve
    `explore=True` künyesi aynen. (Kuyruktaki merdiven yapı gereği EXPLOIT hamlesidir.)"""
    p = reflect.propose_deterministic(explore=True)
    assert p["rationale"].startswith("bandit(UCB) explore: ")
    assert p["confidence"] == 0.4 and p["memory_exhausted"] is False
    base = str(p["variable"]).split("@", 1)[0]
    spec = config.bounds()[base]
    assert spec["min"] <= p["new"] <= spec["max"]
    # hafıza explore'da da okunur (eski davranış): ilk sıradaki değer defterdeyse atlanır
    ilk = p["variable"]
    _defter((ilk, p["new"]))
    p2 = reflect.propose_deterministic(explore=True)
    assert not (p2["variable"] == ilk and p2["new"] == p["new"])


def test_a8_EXPLORE_rejim_son_ekinde_ARTIK_PATLAMIYOR(sezgisel_stop):
    """GİZLİ ÇÖKME (bu turda kapandı): eski yerel `already_failed` kapanışı `bounds[var]` aramasını
    SON EKLİ adla yapıyordu (`stop_loss_atr_mult@chop`) — defterde o adla bir satır varsa KeyError.
    Yani hafıza tam da iş göreceği anda üreticiyi düşürüyordu. Tek tanıma (`_already_failed`,
    `@` ayrıştırmalı) inince yol dürüstçe atlıyor."""
    store.write_json("regime.json", {"regime": "chop"})
    p_once = reflect.propose_deterministic(explore=True)
    _defter((f"{p_once['variable']}", p_once["new"]))       # değişken ZATEN @chop son-ekli döner
    assert str(p_once["variable"]).endswith("@chop")

    # ÇÖKME İDDİA DEĞİL ÖLÇÜM: eski kapanış birebir yeniden kurulur ve AYNI girdide patlar.
    bounds, hyps = config.bounds(), memory.all_hypotheses()

    def _eski_already_failed(var, val):                    # sökülen kapanışın birebir kopyası
        for h in hyps:
            if h.get("variable") == var and guard._equalish(h.get("new"), val, bounds[var]["type"]) \
                    and h.get("status") in ("rejected_by_backtest", "rolled_back"):
                return True
        return False
    with pytest.raises(KeyError):
        _eski_already_failed(p_once["variable"], p_once["new"])
    assert reflect._already_failed(p_once["variable"], p_once["new"], hyps, bounds) is True

    p = reflect.propose_deterministic(explore=True)          # eski kodda bu çağrı KeyError'la düşerdi
    assert p["variable"] and p["new"] is not None
    assert not (p["variable"] == p_once["variable"] and p["new"] == p_once["new"])


def test_a9_tek_tanim_kaldi_ikinci_hafiza_tanimi_YOK(sezgisel_stop):
    """YAPISAL ÇİVİ: `reflect.py` içinde "başarısız mı" sorusunu cevaplayan TEK tanım kalmalı.
    İkinci bir kopya, biri düzeltilip öteki unutulduğunda bu turun kapattığı sınıfı geri getirir."""
    import inspect
    kaynak = inspect.getsource(reflect)
    assert kaynak.count("def _already_failed(") == 1
    assert "def already_failed(" not in kaynak, "yerel hafıza kapanışı geri gelmiş (ikinci tanım)"
    src = inspect.getsource(reflect.propose_deterministic)
    assert "_already_failed(" in src, "exploit/explore yolları hafızayı okumuyor"


# ==================================================================================================
# KALEM 2 — KÜNYE: CEVABI KİM VERDİ
# ==================================================================================================
class _Sonuc:
    def __init__(self, rc=0, stdout="", stderr=""):
        self.returncode, self.stdout, self.stderr = rc, stdout, stderr


DOLU = "CEVAP\nMessages: 2 (1 user, 0 tool calls)"
BOS = _Sonuc(rc=1, stdout="", stderr="upstream 404")


@pytest.fixture
def ajan(sandbox_state, monkeypatch):
    """`_agent_call` için sahte dünya (v169 fikstürünün kardeşi): ikili 'kurulu', senkron ve havuz
    okuması saplı, sırlar testin kendi zincirini kurar."""
    monkeypatch.setattr(hermes, "_hermes_bin", lambda: "/sahte/hermes")
    monkeypatch.setattr(hermes, "sync_agent_skills", lambda: None)
    monkeypatch.setattr(hermes, "_pool_exhausted", lambda: None)
    monkeypatch.setattr(hermes, "_quiet_flag_ok", True)
    return sandbox_state


def _zincir(monkeypatch, birincil, yedek=None):
    monkeypatch.setattr(hermes.secrets, "get",
                        lambda k: {"NOUS_MODEL": birincil, "NOUS_FALLBACK_MODEL": yedek}.get(k))


def _surec(monkeypatch, karar):
    """`karar(model) -> _Sonuc` — hangi modelin ne döndüğünü test yazar."""
    cagrilar = []

    def _run(cmd, **kw):
        model = cmd[cmd.index("--model") + 1] if "--model" in cmd else None
        cagrilar.append(model)
        return karar(model)
    monkeypatch.setattr(subprocess, "run", _run)
    return cagrilar


def test_b1_ILK_DENEME_DOLU_kunye_birincil_modeli_tasir(ajan, monkeypatch):
    _zincir(monkeypatch, "birincil-x", "yedek-y")
    cagrilar = _surec(monkeypatch, lambda m: _Sonuc(0, DOLU))
    assert hermes._agent_call("soru", kind="review") == DOLU     # dönüş türü DEĞİŞMEDİ (str)
    assert cagrilar == ["birincil-x"]
    assert hermes.cevap_veren_model() == ("birincil-x", None)


def test_b2_ILK_BOS_IKINCI_DOLU_kunye_IKINCI_modeli_tasir(ajan, monkeypatch):
    """BU GECENİN VAKASI: tencent boş → gemini dolu; künye gemini demeli."""
    _zincir(monkeypatch, "tencent/hy3:free", "gemini-flash-latest")
    cagrilar = _surec(monkeypatch,
                      lambda m: _Sonuc(0, DOLU) if m == "gemini-flash-latest" else BOS)
    assert hermes._agent_call("soru", kind="review") == DOLU
    assert cagrilar == ["tencent/hy3:free", "gemini-flash-latest"]
    model, neden = hermes.cevap_veren_model()
    assert model == "gemini-flash-latest" and neden is None


def test_b3_HICBIRI_DOLU_DEGIL_None_ve_NEDEN(ajan, monkeypatch):
    """UYDURMA YASAĞI: cevap yoksa künye None + neden — `active_model()`e sessizce dönülmez."""
    _zincir(monkeypatch, "birincil-x", "yedek-y")
    _surec(monkeypatch, lambda m: BOS)
    assert hermes._agent_call("soru", kind="review") is None
    model, neden = hermes.cevap_veren_model()
    assert model is None and neden == hermes.AGENT_MODEL_YOK_KAYIT and len(neden) >= 20


def test_b4_ADSIZ_ZINCIR_OLCULEMEDI_der_uydurmaz(ajan, monkeypatch):
    """Sır yoksa zincir `[None]`dır: CLI kendi varsayılanına gider ve o adı bize bildirmez.
    Ölçülemeyen ad UYDURULMAZ — alan None, neden zincirin adsızlığını söyler."""
    _zincir(monkeypatch, None, None)
    cagrilar = _surec(monkeypatch, lambda m: _Sonuc(0, DOLU))
    assert hermes._agent_call("soru", kind="t") == DOLU
    assert cagrilar == [None]                                 # `--model` bayrağı hiç eklenmedi
    model, neden = hermes.cevap_veren_model()
    assert model is None and neden == hermes.AGENT_MODEL_YOK_ZINCIR


def test_b5_kutu_HER_CAGRIDA_sifirlanir_bayat_kunye_sizmaz(ajan, monkeypatch):
    """Bir önceki çağrının künyesi sonrakinin cevabı sanılamaz: `_agent_call` girişte kutuyu
    boşaltır ve bu ERKEN DÖNÜŞLERİ de kapsar (ikili yok / soğuma / bütçe reddi)."""
    _zincir(monkeypatch, "birincil-x")
    _surec(monkeypatch, lambda m: _Sonuc(0, DOLU))
    assert hermes._agent_call("bir", kind="t") == DOLU
    monkeypatch.setattr(hermes, "_hermes_bin", lambda: None)   # ikili yok → en erken dönüş
    assert hermes._agent_call("iki", kind="t") is None
    assert hermes.cevap_veren_model() == (None, hermes.AGENT_MODEL_YOK_KAYIT)


def test_b6_okuma_TUKETIR(ajan, monkeypatch):
    """İkinci okuyucu bayat künyeyi taze sanamaz (emsal: `_trace_take`)."""
    _zincir(monkeypatch, "birincil-x")
    _surec(monkeypatch, lambda m: _Sonuc(0, DOLU))
    hermes._agent_call("soru", kind="t")
    assert hermes.cevap_veren_model()[0] == "birincil-x"
    assert hermes.cevap_veren_model() == (None, hermes.AGENT_MODEL_YOK_KAYIT)


# --------------------------------------------------------------------------------------------------
# candidate_review.json — künyenin gerçekten indiği yer
# --------------------------------------------------------------------------------------------------
GUN = "2026-08-13"
GORUS = ('{"reviews": [{"ticker": "VLO", "opinion": "destekle", "note": "taban sıkı"}]}\n'
         'Messages: 2 (1 user, 0 tool calls)')


@pytest.fixture
def inceleme(ajan, monkeypatch):
    monkeypatch.setattr(hermes, "_skill_preload", lambda *a, **k: ())
    store.append_jsonl("trade_plans.jsonl",
                       {"date": GUN, "ticker": "VLO", "setup": "breakout_vcp", "gate_verdict": "GO",
                        "entry_trigger": 10, "stop": 9, "profit_target": 12, "size_r": 1, "score": 70})
    return ajan


def test_b7_candidate_review_kunyesi_CEVAP_VERENI_tasir(inceleme, monkeypatch):
    """CANLI VAKANIN AYNISI: birincil boş, yedek dolu → dosyadaki `model` YEDEĞİ yazar,
    "istenen" ad kendi ADIYLA ayrı alanda durur (iki anlam, iki ad) ve ayrışma olay basar."""
    _zincir(monkeypatch, "tencent/hy3:free", "gemini-flash-latest")
    _surec(monkeypatch, lambda m: _Sonuc(0, GORUS) if m == "gemini-flash-latest" else BOS)
    res = hermes.review_candidates(GUN)
    assert res and res["model"] == "gemini-flash-latest"
    assert res["model_kaynagi"] == "cevap_veren" and res["model_olculemedi"] is None
    assert res["model_istenen"] != res["model"], "iki anlam hâlâ aynı adda"
    kayit = store.read_json("candidate_review.json", {})
    assert kayit["model"] == "gemini-flash-latest" and kayit["model_kaynagi"] == "cevap_veren"
    ev = _olaylar("candidate_review_model_ayrismasi")
    assert len(ev) == 1 and ev[0]["cevap_veren"] == "gemini-flash-latest"
    assert len(ev[0]["detail"]) >= 20


def test_b8_candidate_review_olculemezse_None_ve_NEDEN(inceleme, monkeypatch):
    """Zincir adsızsa künye UYDURULMAZ: `model=None` + neden. Eski davranışa (yapılandırma adı)
    sessizce dönmek, tam olarak bu turun kapattığı arızayı geri getirirdi."""
    _zincir(monkeypatch, None, None)
    _surec(monkeypatch, lambda m: _Sonuc(0, GORUS))
    res = hermes.review_candidates(GUN)
    assert res and res["model"] is None
    assert res["model_olculemedi"] == hermes.AGENT_MODEL_YOK_ZINCIR
    assert res["model_kaynagi"] == "cevap_veren"      # beyan HER kayıtta var (eski kayıtta yoktu)
    assert _olaylar("candidate_review_model_ayrismasi") == []


def test_b9_SAPLI_agent_call_bayat_kunye_yapistiramaz(inceleme, monkeypatch):
    """Okuyan taraf kendi garantisini tutar: `_agent_call` saplanmış olsa bile (kutuya hiç
    dokunmaz) bir önceki gerçek çağrının künyesi bu seansın görüşüne yapışamaz."""
    _zincir(monkeypatch, "birincil-x")
    _surec(monkeypatch, lambda m: _Sonuc(0, DOLU))
    hermes._agent_call("ısınma", kind="t")                     # kutuda "birincil-x" var, OKUNMADI
    monkeypatch.setattr(hermes, "_agent_call", lambda *a, **k: GORUS)
    res = hermes.review_candidates(GUN)
    assert res and res["model"] is None and res["model_olculemedi"] == hermes.AGENT_MODEL_YOK_KAYIT


def test_c1_agent_call_donus_sozlesmesi_KIRILMADI():
    """Mevcut çağıranlar `str | None` bekliyor — yan kanal imzayı DEĞİŞTİRMEDİ."""
    import inspect
    sig = inspect.signature(hermes._agent_call)
    assert str(sig.return_annotation) in ("str | None", "'str | None'")
    assert list(sig.parameters) == ["prompt", "preload", "kind", "timeout", "max_wait"]
    src = inspect.getsource(hermes._agent_call)
    assert "return out.stdout" in src and "_agent_model_kaydet(model)" in src


def test_c2_kunye_kutusu_ISPARCACIGINA_OZEL(ajan, monkeypatch):
    """EŞZAMANLILIK BEYANI ÇİVİSİ: kutu `threading.local` — arka plan dolgu kolu ile inceleme kolu
    aynı anda koşabilir ve modül düzeyinde tek kutu birinin künyesini ötekine yazardı. Başka bir
    iş parçacığından okuma ÖLÇÜLEMEDİ döner (uydurma değil, dürüst boşluk)."""
    import threading
    _zincir(monkeypatch, "birincil-x")
    _surec(monkeypatch, lambda m: _Sonuc(0, DOLU))
    hermes._agent_call("soru", kind="t")
    kutu = {}
    t = threading.Thread(target=lambda: kutu.update(zip(("m", "n"), hermes.cevap_veren_model())))
    t.start(); t.join()
    assert kutu["m"] is None and kutu["n"] == hermes.AGENT_MODEL_YOK_KAYIT
    assert hermes.cevap_veren_model()[0] == "birincil-x"      # kendi ipliğinde bozulmadan durur
