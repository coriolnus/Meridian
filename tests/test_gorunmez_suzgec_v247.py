"""test_gorunmez_suzgec_v247.py — EDG-2026-041: GÖRÜNMEZ SÜZGEÇ (arka plan ön-elemesi).

KART: `research/cards/EDG-2026-041-gorunmez-suzgec.yaml` (status: measured, hüküm D1 + D2).
ÖLÇÜLEN (Rol-1, 2026-08-14, canlı defterden MOTOR DEĞİŞMEDEN ÖNCE): `hermes_bg_proposal_rejected`
47 kez ateşledi (2026-08-02T14:00 → 2026-08-13T17:26) ve o 47 önerinin HİÇBİRİ hipotez defterine
girmedi. Sertifika 47/47'de BİLİNİYORDU (hepsi `chop`, `None(auto)` SIFIR) → korkuluk KÖRLÜKTEN
değil AYRIMSIZLIKTAN kesiyordu. 46/47 düz global (`@`siz), 1/47 farklı rejime giden
(`exit.time_stop_days@trend_up`). Değişken dağılımı: `entry.w_turnover` 21 · `exit.trail_atr_mult`
16 · `regime.vix_backwardation_gate` 8 · `exit.breakeven_r` 1 · `exit.time_stop_days@trend_up` 1.

HÜKÜM, İKİ DAL — bu dosya ikisini de DAVRANIŞTAN ölçer, docstring'den değil:
  D2 ÇİVİLEME — `@`siz öneri ATILMAK yerine `x@<sertifika>` biçimine çivilenir. Korkuluğun
     invaryantı "kanıt kendi rejimini terk etmesin"di; RET bunu sağlar ama işi çöpe atar, YENİDEN
     YAZIM aynı invaryantı sağlar ve işi korur.
  D1 KAYIT — reddedilen öneri REDDEDİLDİ damgasıyla kayda geçer ve o kayıt ADAY SAYAN hiçbir
     tüketicide aday gibi sayılmaz (kartın kill kriteri: yoksa 28b'nin TERS YÖNÜ doğar).

KORKULUK KILL KRİTERİ (MUTLAK): canlı-DIŞI bir rejimin kanıtı canlı `params`ı ETKİLEYEMEZ. Üç
ayrı test bunu ayrı ayrı çiviler: sertifika yoksa ret · farklı rejim yine ret · canlı tur zerre
değişmedi.
"""
from __future__ import annotations

import pytest

from meridian import analytics, config, dataset, hermes, memory, reflect, store


# =================================================================================================
# ORTAK ORTAM
# =================================================================================================
def _ortam(monkeypatch, *, submit_sapla: bool) -> dict:
    """Canlı rejim `chop` — denetimde ölçülen CANLI durumun aynısı. Beyin/bakir yolları ve arama
    HER ZAMAN yakalanır (hiçbir walk-forward koşmaz).

    `monkeypatch.undo()` BU DOSYADA YASAK ve bu bir DENEY SONUCUDUR: `sandbox_state` fikstürü
    `config.STATE`i AYNI `monkeypatch` örneğiyle yönlendiriyor, dolayısıyla `undo()` yalnız yerel
    saplamayı değil DEPO YÖNLENDİRMESİNİ de geri alır ve test CANLI `state/`e yazar (conftest'in
    `_no_live_state_writes` bekçisi bunu teardown'da yakaladı — yani hasar zaten olmuştu). Gerçek
    kapı yolunu ölçmek isteyen test bu yüzden saplamayı HİÇ KURMAZ (`submit_sapla=False`), geri
    almaz."""
    store.write_json("regime.json", {"regime": "chop"})
    monkeypatch.setattr(hermes, "propose_with_llm", lambda: None)
    monkeypatch.setattr(hermes, "propose_virgin_knob", lambda: None)
    monkeypatch.setattr(dataset, "load", lambda **k: (None, None))
    c: dict = {"search": [], "submit": []}
    monkeypatch.setattr(reflect, "search_and_submit",
                        lambda *a, **k: (c["search"].append(k)
                                         or {"status": "no_clearing_candidate", "search": {}}))
    if submit_sapla:
        monkeypatch.setattr(reflect, "submit",
                            lambda *a, **k: (c["submit"].append(a[0] if a else k)
                                             or {"status": "rejected_by_backtest"}))
    return c


@pytest.fixture
def bg(sandbox_state, monkeypatch):
    """Ship yolu saplı: `reflect.submit`e NE GİTTİĞİ ölçülür, hiçbir şey gerçekten koşmaz."""
    return _ortam(monkeypatch, submit_sapla=True)


@pytest.fixture
def bg_gercek_kapi(sandbox_state, monkeypatch):
    """GERÇEK `reflect.submit` (guard + defter yazımı dahil). Kullanılan öneriler GUARD'DA düşecek
    şekilde seçilir — guard'ı geçen bir öneri gerçek walk-forward'a girer ve test dakikalarca
    koşardı."""
    return _ortam(monkeypatch, submit_sapla=False)


def _oneri(monkeypatch, **alanlar):
    prop = {"variable": "stop_loss_atr_mult", "new": 2.2, "old": 2.0, "source": "llm",
            "rationale": "ORİJİNAL GEREKÇE"}
    prop.update(alanlar)
    monkeypatch.setattr(hermes, "propose_with_llm", lambda: dict(prop))
    return prop


def _olay(ad: str) -> list:
    return [e for e in store.read_jsonl("events.jsonl") if e.get("event") == ad]


# =================================================================================================
# D2 — ÇİVİLEME: `@`SİZ ÖNERİ ATILMAZ, SERTİFİKALI REJİME YENİDEN YAZILIR
# =================================================================================================
def test_D2_bg_globali_REJIME_CIVILENIR_atilmaz(bg, monkeypatch):
    """ÇİVİ-1: `background` + `@`siz + sertifika VAR → öneri yeniden yazılır ve KAPIYA GİDER.

    Eski davranışta bu öneri `proposal = None` ile çöpe gidiyordu ve aramaya düşülüyordu; ölçülen
    47 redin 46'sı tam olarak bu daldı."""
    _oneri(monkeypatch, variable="stop_loss_atr_mult")
    hermes.reflect_once(target_regime="chop", background=True)

    assert bg["submit"], "çivilenen öneri kapıya HİÇ gitmedi — hâlâ atılıyor"
    assert bg["submit"][-1]["variable"] == "stop_loss_atr_mult@chop", \
        "öneri sertifikalı rejime çivilenmedi"
    assert not _olay("hermes_bg_proposal_rejected"), \
        "çivilenen öneri AYRICA reddedilmiş sayıldı — çift muhasebe"


def test_D2_civileme_OLAY_BASAR_eski_yeni_sertifika(bg, monkeypatch):
    """ÇİVİ-1b: sessiz dönüşüm YASAK — bu turun bütün konusu görünürlük. Olay üç alanı da taşır."""
    _oneri(monkeypatch, variable="exit.trail_atr_mult", new=1.5, old=2.5)
    hermes.reflect_once(target_regime="chop", background=True)

    ev = _olay("hermes_bg_proposal_rejimlendi")
    assert ev, "yeniden yazım SESSİZ yapıldı — olay basılmadı"
    assert ev[-1]["eski"] == "exit.trail_atr_mult"
    assert ev[-1]["yeni"] == "exit.trail_atr_mult@chop"
    assert ev[-1]["sertifika"] == "chop"
    assert len(str(ev[-1].get("detail", ""))) >= 20, "olay gerekçesiz (YASA 4 eşiği)"


def test_D2_civileme_GEREKCEYE_de_yansir(bg, monkeypatch):
    """ÇİVİ-1c: defterde "bu öneri global doğdu, rejime çivilendi" OKUNABİLMELİ — `rationale`
    kapıya giden öneriyle birlikte `memory.record`a düşer, yani izin kalıcı yeri orasıdır."""
    _oneri(monkeypatch, variable="exit.breakeven_r", new=0.5, old=1.0)
    hermes.reflect_once(target_regime="chop", background=True)

    r = str(bg["submit"][-1]["rationale"])
    assert "rejime çivilendi" in r and "exit.breakeven_r@chop" in r, \
        f"gerekçe çivilemeyi anlatmıyor: {r[:120]}"
    assert "ORİJİNAL GEREKÇE" in r, "orijinal gerekçe SİLİNDİ — beynin kendi tezi kayboldu"


def test_D2_UCTAN_UCA_entry_w_turnover_olculen_vaka(bg, monkeypatch):
    """ÇİVİ-7 (uçtan uca, ÖLÇÜLEN vaka): 47 redin 21'i `entry.w_turnover`dı. Bugün o öneri
    `entry.w_turnover@chop` olarak kapıya ulaşır."""
    _oneri(monkeypatch, variable="entry.w_turnover", new=0.15, old=None,
           source="deterministic:virgin")
    hermes.reflect_once(target_regime="chop", background=True)

    assert bg["submit"][-1]["variable"] == "entry.w_turnover@chop"
    assert _olay("hermes_bg_proposal_rejimlendi")[-1]["source"] == "deterministic:virgin", \
        "üretici etiketi çivilemede kayboldu — hangi kolun kurtarıldığı ölçülemez"


# =================================================================================================
# KORKULUK — BOZULAMAZ (kill kriteri, MUTLAK)
# =================================================================================================
def test_KORKULUK_sertifika_YOKSA_bugunku_ret_AYNEN_surer(bg, monkeypatch):
    """ÇİVİ-2: `target_regime="auto"` → `certified is None`. Hangi rejimin sertifikalı olduğu
    BİLİNMİYOR ve UYDURULAMAZ → çivileme YOK, ret AYNEN. (Ölçümde bu hâl 0/47'ydi; kapı yine de
    kapalı kalmalı — ölçülmemiş bir hâl 'olmaz' demek değildir.)"""
    _oneri(monkeypatch, variable="stop_loss_atr_mult")
    hermes.reflect_once(target_regime="auto", background=True)

    assert not bg["submit"], "sertifikasız turda öneri kapıya gitti — korkuluk delindi"
    assert not _olay("hermes_bg_proposal_rejimlendi"), "sertifika yokken uydurma bir rejime çivilendi"
    ev = _olay("hermes_bg_proposal_rejected")
    assert ev and ev[-1]["red_nedeni"] == "global_sertifikasiz"
    assert ev[-1]["bg_regime"] is None


def test_KORKULUK_FARKLI_rejime_giden_oneri_AYNEN_reddedilir(bg, monkeypatch):
    """ÇİVİ-3 (ölçümdeki 1/47): `exit.time_stop_days@trend_up`, sertifika `chop`. Korkuluğun ASIL
    hedefi budur — çivileme onu KURTARMAZ, çünkü kurtarmak kanıtı sahibi olmayan bir rejime
    taşımak olurdu."""
    _oneri(monkeypatch, variable="exit.time_stop_days@trend_up", new=10, old=15)
    hermes.reflect_once(target_regime="chop", background=True)

    assert not bg["submit"], "farklı rejime giden öneri kapıya gitti — denetim #27 deliği açıldı"
    assert not _olay("hermes_bg_proposal_rejimlendi")
    ev = _olay("hermes_bg_proposal_rejected")
    assert ev and ev[-1]["red_nedeni"] == "farkli_rejim"
    assert ev[-1]["variable"] == "exit.time_stop_days@trend_up", \
        "reddedilen önerinin ADI kayıtta değil — hangi öneri düştü okunamaz"


def test_KORKULUK_gecersiz_rejim_ADINA_civilenmez(bg, monkeypatch):
    """Sertifika bir DİZGİ olabilir ama geçerli bir rejim adı olmayabilir. O turda arama zaten
    `bg_reflection_skipped_unscoped` ile hiç koşmaz — kapsanamayan bir tura öneri çakmak,
    kimsenin notlandıramayacağı bir değişken üretirdi."""
    _oneri(monkeypatch, variable="stop_loss_atr_mult")
    r = hermes.reflect_once(target_regime="muz", background=True)

    assert not bg["submit"], "geçersiz rejim adına çivilenip kapıya gitti"
    assert not _olay("hermes_bg_proposal_rejimlendi")
    assert r["status"] == "bg_regime_unscoped"
    assert _olay("hermes_bg_proposal_rejected"), "kapsanamayan turdaki ret KAYITSIZ kaldı"


def test_KORKULUK_CANLI_tur_ZERRE_degismedi(bg, monkeypatch):
    """ÇİVİ-4: `background=False`. Global muafiyet CANLI turda MEŞRUDUR (canlı rejimin kanıtı düz
    `params`ı da meşru biçimde ayarlar) — çivileme oraya UZANMAZ, kayıt da yazılmaz."""
    _oneri(monkeypatch, variable="stop_loss_atr_mult")
    hermes.reflect_once(target_regime="chop")

    assert bg["submit"], "canlı turda global öneri kapıya gitmedi — canlı yol daraltıldı"
    assert bg["submit"][-1]["variable"] == "stop_loss_atr_mult", \
        "canlı turda öneri sessizce rejime çivilendi — canlı davranış DEĞİŞTİ"
    assert not _olay("hermes_bg_proposal_rejimlendi")
    assert not _olay("hermes_bg_proposal_rejected")


def test_KORKULUK_canli_FARKLI_rejim_reddi_eski_yolunda_kaldi(bg, monkeypatch):
    """Canlı turda farklı-rejim reddi AYRI bir olaydır (`hermes_proposal_uncertified_regime`) ve
    D1 kaydına GİRMEZ: bg kaydını canlı yola da bağlamak, "canlı tur zerre değişmedi" çivisini
    kırardı."""
    _oneri(monkeypatch, variable="entry.min_score@chop", new=65, old=60)
    hermes.reflect_once(target_regime="trend_up")

    assert not bg["submit"]
    assert _olay("hermes_proposal_uncertified_regime"), "canlı yolun kendi olayı susturuldu"
    assert not _olay("hermes_bg_proposal_rejected"), "canlı ret bg kaydına sızdı"


# =================================================================================================
# ÇİVİ-5 — ÇİVİLENEN ÖNERİ GUARD/BOUNDS'TAN YİNE GEÇER (muafiyet YOK)
# =================================================================================================
def test_D2_civilenen_ad_GUARD_dogrulamasina_ULASIR(bg_gercek_kapi, monkeypatch):
    """Yeniden yazılan ad, `reflect.submit` içindeki `guard.validate_change`e AYNEN ulaşmalı —
    çivileme guard'ın ETRAFINDAN dolaşan ikinci bir yol OLAMAZ."""
    from meridian import guard as _guard
    gorulen: list = []
    gercek = _guard.validate_change
    monkeypatch.setattr(_guard, "validate_change",
                        lambda p, *a, **k: (gorulen.append(p.get("variable")) or gercek(p, *a, **k)))
    _oneri(monkeypatch, variable="entry.w_turnover", new=0.15, old=None)

    hermes.reflect_once(target_regime="chop", background=True)

    assert gorulen == ["entry.w_turnover@chop"], \
        f"guard çivilenen adı görmedi (guard yolu atlanıyor olabilir): {gorulen}"


def test_D2_guarddan_DUSEN_civileme_ONERIYI_dusurur_VE_KAYDA_gecer(bg_gercek_kapi, monkeypatch):
    """ÇİVİ-5 (ÖLÇÜLEN vaka, 21/47): `entry.w_turnover` canlı `params`ta YOKTUR → `@chop`
    override'ı sessizce yok sayılırdı, guard bunu DÜRÜSTÇE reddeder. Kartın beyanlı sınırı:
    "kurtarılan önerilerin İYİ olduğu İDDİA EDİLMİYOR — probgate'ten yine geçmek zorundadır".

    VE bu düşüş KAYITSIZ kalmaz: gerçek kapı reddi hipotez defterine kendi satırını yazar."""
    _oneri(monkeypatch, variable="entry.w_turnover", new=0.15, old=None)

    hermes.reflect_once(target_regime="chop", background=True)

    defter = memory.all_hypotheses()
    assert len(defter) == 1, f"çivilenen önerinin kapı reddi deftere GİRMEDİ: {defter}"
    assert defter[0]["variable"] == "entry.w_turnover@chop"
    assert defter[0]["status"] == "rejected_by_guard"
    assert any("live strategy params" in str(r) for r in defter[0]["reject_reasons"]), \
        f"ret gerekçesi guard'ın kendi cümlesi değil: {defter[0].get('reject_reasons')}"


# =================================================================================================
# D1 — KAYIT: REDDEDİLDİ DAMGASI, TAM ÖNERİ, ADAY SAYILMAZ
# =================================================================================================
def test_D1_ret_kaydi_TAM_ve_DAMGALI(bg, monkeypatch):
    """Eski kayıt yalnız `variable` + `bg_regime` taşıyordu: kayıttan NE ÖNERİLDİĞİ okunamıyordu.
    D1 kaydı öneriyi yeniden kurabilecek kadar tam ve REDDEDİLDİ damgalıdır."""
    _oneri(monkeypatch, variable="exit.time_stop_days@trend_up", new=10, old=15,
           source="hermes:nous", rationale="stop payı yüksek")
    hermes.reflect_once(target_regime="chop", background=True)

    e = _olay("hermes_bg_proposal_rejected")[-1]
    assert e["damga"] == hermes.BG_RED_DAMGA == "REDDEDILDI"
    assert e["red_nedeni"] == "farkli_rejim"
    assert (e["old"], e["new"], e["source"]) == (15, 10, "hermes:nous")
    assert e["rationale"] == "stop payı yüksek"
    assert e["bg_regime"] == "chop"
    assert len(str(e.get("detail", ""))) >= 20


def test_D1_ret_kaydi_ADAY_SAYAN_tuketicide_SAYILMIYOR(bg_gercek_kapi, monkeypatch):
    """ÇİVİ-6 — 28b'nin TERS YÖNÜ ÇİVİSİ (kartın kill kriteri), POZİTİF + NEGATİF kontrol.

    NEGATİF: korkuluğun düşürdüğü öneri ADAY DEĞİLDİR → hipotez defterine ve ondan türeyen aday
    sayaçlarına (`analytics.deflate_why`, `hermes.exploration_share`) GİRMEZ.
    POZİTİF: kapıya ULAŞIP guard'da düşen öneri GERÇEK bir adaydır → aynı sayaçlar onu SAYAR.
    İkisi ayrılmazsa ya üretim görünmez kalır (bugünkü kusur) ya da sayı şişer (ters yönü)."""
    # --- NEGATİF: korkuluk reddi ---
    _oneri(monkeypatch, variable="exit.time_stop_days@trend_up", new=10, old=15)
    hermes.reflect_once(target_regime="chop", background=True)

    assert _olay("hermes_bg_proposal_rejected"), "ön koşul: ret gerçekleşmedi"
    assert memory.all_hypotheses() == [], "reddedilen öneri hipotez defterine ADAY gibi girdi"
    assert analytics.deflate_why()["n_hypotheses"] == 0, "aday sayacı ön-eleme reddiyle ŞİŞTİ"
    assert hermes.exploration_share()["n_defter"] == 0, "keşif payı paydası ön-eleme reddiyle ŞİŞTİ"

    # --- POZİTİF: çivilenip GERÇEK guard'a ulaşan öneri (aynı sayaçlar bunu SAYMALI) ---
    _oneri(monkeypatch, variable="entry.w_turnover", new=0.15, old=None)
    hermes.reflect_once(target_regime="chop", background=True)

    assert len(memory.all_hypotheses()) == 1, "gerçek kapı reddi deftere girmedi (sayaç körleşti)"
    assert analytics.deflate_why()["n_hypotheses"] == 1


def test_D1_okuyucu_karnede_ve_hermes_scorecardda_GORUNUR(bg, monkeypatch):
    """YASA 6: okuyucusuz yazım yok. D1 damgasının tüketicisi `bg_on_eleme_karnesi` → o da
    `exploration_share`in içinde → `analytics.hermes_scorecard()` onu olduğu gibi dışa verir."""
    _oneri(monkeypatch, variable="exit.time_stop_days@trend_up", new=10, old=15)
    hermes.reflect_once(target_regime="chop", background=True)     # 1 ret
    _oneri(monkeypatch, variable="entry.w_turnover", new=0.15, old=None)
    hermes.reflect_once(target_regime="chop", background=True)     # 1 çivileme

    k = hermes.bg_on_eleme_karnesi()
    assert k["reddedilen"]["n"] == 1 and k["reddedilen"]["damga"] == "REDDEDILDI"
    assert k["reddedilen"]["nedenler"] == {"farkli_rejim": 1}
    assert k["rejimlendirilen"]["n"] == 1
    assert k["rejimlendirilen"]["son"]["yeni"] == "entry.w_turnover@chop"
    assert len(str(k["beyan"])) >= 20

    assert hermes.exploration_share()["on_eleme"]["reddedilen"]["n"] == 1, \
        "keşif payı karnesi ön-elemeyi taşımıyor — damganın okuyucusu yok"
    sc = analytics.hermes_scorecard()
    assert sc["kesif_payi"]["on_eleme"]["rejimlendirilen"]["n"] == 1, \
        "hermes karnesi ön-elemeyi dışa vermiyor — YASA 6 zinciri kopuk"


def test_D1_karne_BOS_defterde_de_olcer(bg, monkeypatch):
    """Ön-eleme sayımı hipotez defterinden BAĞIMSIZDIR: defter boş diye onu da None yapmak,
    ÖLÇÜLMÜŞ bir sayıyı 'ölçülemedi' diye yazmak olurdu."""
    _oneri(monkeypatch, variable="exit.time_stop_days@trend_up", new=10, old=15)
    hermes.reflect_once(target_regime="chop", background=True)

    ks = hermes.exploration_share()
    assert ks["n_defter"] == 0 and ks["aile_dagilimi"] is None      # defter gerçekten boş
    assert ks["on_eleme"]["reddedilen"]["n"] == 1, "boş defterde ön-eleme sayısı da yutuldu"


def test_D1_damgasiz_ESKI_satirlar_uydurulmaz(sandbox_state):
    """Retro damga YASAK: damga bu turda eklendi, ölçülen 47 satır damgasızdır ve `damgasiz`
    kovasında SAYILIR — 'global_sertifikasiz' diye varsayılmaz."""
    k = hermes.bg_on_eleme_karnesi(olaylar=[
        {"event": "hermes_bg_proposal_rejected", "variable": "entry.w_turnover"},          # eski
        {"event": "hermes_bg_proposal_rejected", "variable": "x", "red_nedeni": "farkli_rejim"},
    ])
    assert k["reddedilen"]["n"] == 2
    assert k["reddedilen"]["nedenler"] == {"damgasiz": 1, "farkli_rejim": 1}


def test_D1_karne_olay_defteri_OKUNAMAZSA_None_der(sandbox_state, monkeypatch):
    """UYDURMA YASAĞI: ölçülemeyen sayı 0 değil None'dır, sebebiyle birlikte."""
    def _patlar(*a, **k):
        raise OSError("defter okunamadı")
    monkeypatch.setattr(store, "read_jsonl", _patlar)

    k = hermes.bg_on_eleme_karnesi()
    assert k["reddedilen"] is None and k["rejimlendirilen"] is None
    assert "ÖLÇÜLEMEDİ" in k["beyan"]


def test_D1_kayit_kanali_dususu_TURU_dusurmez_ama_SESSIZ_de_kalmaz(bg, monkeypatch):
    """Muhasebe kanalının arızası öğrenme turunu öldürmemeli (YASA 4 kaçışı işaretli) — ama ret
    kaydının düştüğü ADIYLA duyurulmalı, yoksa karne sessizce eksik sayar."""
    gercek_warn = hermes.obs.warn

    def _kirik(event, **f):
        if event == "hermes_bg_proposal_rejected":
            raise RuntimeError("olay kanalı düştü")
        return gercek_warn(event, **f)
    monkeypatch.setattr(hermes.obs, "warn", _kirik)
    _oneri(monkeypatch, variable="exit.time_stop_days@trend_up", new=10, old=15)

    hermes.reflect_once(target_regime="chop", background=True)      # patlamamalı

    monkeypatch.setattr(hermes.obs, "warn", gercek_warn)
    assert _olay("hermes_bg_on_eleme_kaydi_dustu"), "kayıt düşüşü SESSİZCE yutuldu"
    assert not bg["submit"], "kayıt düşünce ret de düştü — korkuluk muhasebeye bağlanmış"


# =================================================================================================
# YASA 4 — SESSİZ-YUTMA İŞARETLERİ (bu turda eklenen iki `except` bloğu)
# =================================================================================================
def test_YASA4_eklenen_sessiz_yutmalar_isaretli_ve_gerekceli():
    """Bu turun eklediği her `except` ya yeniden yükseltir ya da işaretli+gerekçelidir."""
    import inspect
    src = inspect.getsource(hermes._bg_on_eleme_kaydi).splitlines()
    isaretler = [s for s in src if "sessiz-yutma:" in s]
    assert len(isaretler) == 2, f"beklenen iki işaret bulunamadı: {len(isaretler)}"
    for s in isaretler:
        assert len(s.split("sessiz-yutma:", 1)[1].strip()) >= 20, f"gerekçe 20 karakterden kısa: {s}"
