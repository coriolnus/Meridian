"""test_uretec_kesif_dengesi_v135.py — ÜRETEÇ KEŞİF DENGESİ (Nous N00002, 2026-07-30).

ÖLÇÜLMÜŞ SORUN (canlı defter, 41 hipotez / 32 düğme):
  * Denemelerin %51,2'si TEK düğmede: `stop_loss_atr_mult` — 21 deneme, 0 ship.
  * bounds.yaml'daki 32 düğmenin 18'i HİÇ hipotez taşımadı (kör nokta).
  * Ölü aile istatistiği ÖLÇÜLÜYORDU (`analytics.dead_families`, H2) ama isteme yalnız ham veri
    olarak, kanıt paketinin İÇİNDE ve tavana çarpınca DÜŞEBİLİR hâlde giriyordu; üreteç kendi
    tarihini bir YÖNLENDİRME olarak hiç görmüyordu ve kuraklıkta aynı kuyuyu kazıyordu.

BU DOSYANIN ÇİVİLEDİĞİ ŞEY (dört başlık):
  (1) İstem gövdesine iki KANIT bölümü giriyor ve ikisi de H2'nin GERÇEK hesabından türüyor —
      ikinci bir sayım yazılmadı (yazılsaydı panodaki "ölü aile" ile istemdeki sessizce ayrışırdı).
  (2) Beyin yokken düşülen deterministik yol artık BOŞ değil: bakir bir düğmeden tek hamle üretir,
      guard'a takılanı ADIYLA atlar, bakir kalmayınca ZARİFÇE düşer (eski davranış birebir korunur).
  (3) Keşif payı ÖLÇÜLÜR ve TÜKETİLİR (YASA 6): aile dağılımı, bakir isabet, ölü-aile tekrarı;
      ölçülemeyen None (uydurma yasağı).
  (4) DEĞİŞMEZLER: HYP_SCHEMA geriye-uyumlu, K/`k_probes` muhasebesi aynı, SYSTEM statik sabit.

Hiçbir test CANLI LLM ÇAĞIRMAZ ve hiçbiri canlı `state/`e yazmaz — hepsi `sandbox_state` altında.
"""
from __future__ import annotations

import ast
import json
import pathlib

import pytest

from meridian import analytics, config, guard, hermes, memory

SRC = pathlib.Path("meridian/hermes.py")


# =================================================================================================
# Sahte H2 verisi — bölümlerin KANITTAN kurulduğunu göstermek için (uydurma yasağının test hâli)
# =================================================================================================
def _sahte_h2(monkeypatch, *, olu: dict | None = None, bakir: list | None = None,
              n_hipotez: int = 41, en_yogun: str = "stop_loss_atr_mult", pay: float = 0.512):
    """`analytics.dead_families`i sahte bir hükümle değiştirir. Bölümler BUNDAN kurulmalı — kendi
    saymıyor olduklarının kanıtı, sahte veriyi birebir yansıtmalarıdır."""
    olu = {"stop_loss_atr_mult": {"denendi": 21, "ship": 0,
                                  "durumlar": {"rejected_by_guard": 20, "rejected_by_backtest": 1},
                                  "denenen_degerler": [2.1], "son": "2026-07-20"}} if olu is None else olu
    bakir = ["entry.min_rvol", "exit.scale_out_r"] if bakir is None else bakir
    doc = {"n_hipotez": n_hipotez, "n_aile": 14, "olu_aileler": olu,
           "en_yogun_aile": en_yogun, "en_yogun_pay": pay,
           "hic_onerilmemis_dugmeler": list(bakir),
           "hic_onerilmemis_sayi": f"{len(bakir)}/32",
           "beyan": "ölü aile = >= 3 deneme, 0 ship."}
    monkeypatch.setattr(analytics, "dead_families", lambda: doc)
    return doc


# =================================================================================================
# 1) İSTEM BESLEMESİ — iki bölüm, KANITTAN kurulur
# =================================================================================================
def test_iki_bolum_H2_KANITINDAN_kurulur(sandbox_state, monkeypatch):
    _sahte_h2(monkeypatch)

    s = hermes._exploration_sections()

    # (A) ÖLÜ AİLELER: ad, deneme sayısı, ship sayısı, ÖLÜM SEBEPLERİ (durum kırılımı) ve
    # denenmiş değerler — "farklı sebep gerekçesi" talebi ancak sebepler görünürse anlamlıdır.
    assert "DEAD KNOB FAMILIES" in s
    assert "stop_loss_atr_mult" in s and "21 tries" in s and "0 shipped" in s
    assert "rejected_by_guard" in s and "2.1" in s
    assert "51%" in s, "yoğunlaşma payı (H2'nin en_yogun_pay'ı) bölüme girmemiş"
    # (B) BAKİR DÜĞMELER: ad + BOUNDS ARALIĞI (aralıksız liste yönlendirme değil ad dökümüdür)
    assert "NEVER-PROPOSED KNOBS" in s
    assert "entry.min_rvol" in s and "exit.scale_out_r" in s
    b = config.bounds()["entry.min_rvol"]
    assert f"{b['min']}..{b['max']}" in s and f"step {b['step']}" in s


def test_bolumler_YONLENDIRME_dir_KOTA_degil(sandbox_state, monkeypatch):
    """Kapı tek hakem kalır: bölümler bir YASAK ya da kota cümlesi kurmaz, MALİYET bilgisi verir."""
    _sahte_h2(monkeypatch)

    s = hermes._exploration_sections()

    assert "NOT a quota" in s and "the only judge" in s
    assert "MUST name a failure reason DIFFERENT" in s, "gerekçesiz ölü-aile tekrarı caydırılmıyor"
    assert "family error budget K" in s and "p_required" in s, \
        "K maliyeti (p_required yükselmesi) bölümde yok"
    for yasak in ("forbidden to propose", "you may not propose", "quota of"):
        assert yasak not in s


def test_bakir_liste_H2_DEN_gelir_paralel_hesap_YOK(sandbox_state, monkeypatch):
    """H2'nin listesi değişince bölüm de değişmeli. Değişmiyorsa ikinci bir sayım yazılmış demektir
    ve o sayım, panodaki hükümle sessizce ayrışacak ilk şeydir."""
    _sahte_h2(monkeypatch, bakir=["exit.trail_atr_mult"])
    s1 = hermes._exploration_sections()
    _sahte_h2(monkeypatch, bakir=["position_size_r"])
    s2 = hermes._exploration_sections()

    assert "exit.trail_atr_mult" in s1 and "position_size_r" not in s1
    assert "position_size_r" in s2 and "exit.trail_atr_mult" not in s2


def test_bakir_liste_bounds_ile_ayrisirsa_SESSIZ_atlanmaz(sandbox_state, monkeypatch):
    """H2 listesi bounds'tan türer; bir ad bounds'ta yoksa bu bir AYRIŞMADIR ve adıyla görünmeli."""
    _sahte_h2(monkeypatch, bakir=["entry.min_rvol", "boyle.bir.dugme.yok"])
    kayit = []
    monkeypatch.setattr(hermes.obs, "warn", lambda ev, **f: kayit.append((ev, f)))

    kn = hermes.virgin_knobs()

    assert [r["knob"] for r in kn] == ["entry.min_rvol"]
    assert any(ev == "hermes_virgin_knob_not_in_bounds" for ev, _ in kayit)


def test_H2_dusunce_bolumler_SESSIZCE_bos_gecmez(sandbox_state, monkeypatch):
    def _patla():
        raise RuntimeError("defter okunamadı")
    monkeypatch.setattr(analytics, "dead_families", _patla)
    kayit = []
    monkeypatch.setattr(hermes.obs, "warn", lambda ev, **f: kayit.append((ev, f)))

    assert hermes._exploration_sections() == ""
    assert any(ev == "hermes_h2_families_failed" for ev, _ in kayit), "YASA 4: sessiz yutma"


def test_BOS_defterde_bolum_HIC_yazilmaz(sandbox_state, monkeypatch):
    """Sıfır hipotezde "32 düğmenin 32'si bakir" TEKNİK olarak doğru ama bilgi taşımaz; istemi kanıt
    kılığında gürültüyle doldurur (`evidence_pack`in `_SkipHermesPack` kuralıyla aynı disiplin)."""
    _sahte_h2(monkeypatch, n_hipotez=0, olu={}, bakir=list(config.bounds().keys()))

    assert hermes._exploration_sections() == ""


def test_bolumler_HER_IKI_saglayici_yolunda_da_istemde(sandbox_state, monkeypatch):
    _sahte_h2(monkeypatch)

    s = hermes._exploration_sections()
    semali = hermes._user_prompt(with_schema=True)
    semasiz = hermes._user_prompt(with_schema=False)

    assert s and s in semali and s in semasiz
    # Kanıt paketinden SONRA gelmeli: yönlendirme, dayandığı sayılardan sonra okunur.
    assert semali.index("EXPLORATION BALANCE") > semali.index("EVIDENCE PACK")


def test_bolumler_SYSTEM_e_SIZMAZ_onbellek_sozlesmesi_durur():
    """SYSTEM statik bir sabittir; içine değişken metin girdiği gün `cache_control` her turda ıskalar
    ve maliyet sessizce katlanır. Bu turun eklediği her şey user-prompt yolundan girer."""
    tree = ast.parse(SRC.read_text())
    atama = [n for n in tree.body if isinstance(n, ast.Assign)
             and any(isinstance(t, ast.Name) and t.id == "SYSTEM" for t in n.targets)]
    assert atama and isinstance(atama[-1].value, ast.Constant)
    for sizinti in ("NEVER-PROPOSED", "DEAD KNOB FAMILIES", "EXPLORATION BALANCE"):
        assert sizinti not in hermes.SYSTEM


# =================================================================================================
# 2) DETERMİNİSTİK YOL — bakir düğmeden örnekler, zarifçe düşer
# =================================================================================================
def test_deterministik_yol_BAKIR_dugmeden_orneklerdi(sandbox_state, monkeypatch):
    _sahte_h2(monkeypatch, bakir=["exit.trail_atr_mult"])

    p = hermes.propose_virgin_knob()

    assert p is not None
    assert p["variable"] == "exit.trail_atr_mult"
    assert p["source"] == "deterministic:virgin", "defterde bakir yolu ayırt edilemezse etkisi ölçülemez"
    b = config.bounds()["exit.trail_atr_mult"]
    assert b["min"] <= p["new"] <= b["max"]
    v = guard.validate_change(p, config.load_strategy()["params"], config.bounds(),
                              config.goal(), [], 0)
    assert v.ok, f"deterministik öneri guard'dan geçmiyor: {v.reasons}"


def test_deterministik_oneri_ORTA_NOKTAYI_secer(sandbox_state, monkeypatch):
    """Bakir bir düğmede "hangi yön" sorusunun kanıtı yoktur; bir adımlık hareket ölçüm değil
    dokunuştur. Orta nokta, aralığın gerçekten ölçüldüğü tek deterministik seçimdir."""
    _sahte_h2(monkeypatch, bakir=["entry.min_rvol"])

    p = hermes.propose_virgin_knob()

    b = config.bounds()["entry.min_rvol"]
    assert p["new"] == pytest.approx((b["min"] + b["max"]) / 2.0)


def test_orta_nokta_NO_OP_ise_denenmemis_yariya_bir_adim(sandbox_state):
    """Aç/kapa düğmesinde orta nokta canlı değerin ta kendisi olabilir; no-op bir öneri guard'a
    takılır ve düğme HİÇ ÖLÇÜLMEDEN bakir listesinden düşerdi."""
    spec = {"min": 0, "max": 1, "step": 1, "type": "int"}
    assert hermes._virgin_value(spec, live=0) == 1
    assert hermes._virgin_value(spec, live=1) == 0
    assert hermes._virgin_value(spec, live=None) in (0, 1)
    # İki hamle de no-op ise dürüstçe None (çağıran bir sonraki düğmeye geçer)
    assert hermes._virgin_value({"min": 2.0, "max": 2.0, "step": 0.5, "type": "float"}, live=2.0) is None


def test_deterministik_deger_ADIM_ve_ARALIK_uzerinde(sandbox_state):
    for ad, spec in config.bounds().items():
        v = hermes._virgin_value(spec, live=None)
        assert v is not None, ad
        assert spec["min"] <= v <= spec["max"], f"{ad} aralık dışı: {v}"
        assert guard._on_step(v, spec["min"], spec["step"], spec["type"]), f"{ad} adım dışı: {v}"


def test_BAKIR_KALMAYINCA_zarif_dusus(sandbox_state, monkeypatch):
    """Kör nokta kapandığında deterministik yol öneri ÜRETMEZ ve `reflect_once` birebir eski
    davranışına (doğrudan koordinat-inişi araması) döner."""
    _sahte_h2(monkeypatch, bakir=[])
    kayit = []
    monkeypatch.setattr(hermes.obs, "log", lambda ev, **f: kayit.append((ev, f)))

    assert hermes.propose_virgin_knob() is None
    assert any(ev == "hermes_virgin_none" for ev, _ in kayit), "sessiz düşüş — sebebi defterde yok"


def test_GUARDA_takilan_bakir_dugme_ADIYLA_atlanir_sonrakine_gecilir(sandbox_state, monkeypatch):
    """Guard'a takılan bir öneri deftere `rejected_by_guard` yazar ve düğme HİÇ ÖLÇÜLMEDEN bakir
    listesinden düşerdi. Ön-denetim aynı guard'ı çağırır, geçmeyeni atlar."""
    _sahte_h2(monkeypatch, bakir=["regime.min_exposure_score", "exit.trail_atr_mult"])
    gercek = guard.validate_change

    def _sadece_ilkini_reddet(proposal, *a, **k):
        if proposal.get("variable") == "regime.min_exposure_score":
            return guard.Verdict(False, ["sahte ret: bu düğme kapıya uygun değil"])
        return gercek(proposal, *a, **k)
    monkeypatch.setattr(guard, "validate_change", _sadece_ilkini_reddet)
    kayit = []
    monkeypatch.setattr(hermes.obs, "log", lambda ev, **f: kayit.append((ev, f)))

    p = hermes.propose_virgin_knob()

    assert p is not None and p["variable"] == "exit.trail_atr_mult", \
        "guard'a takılan bakir düğme atlanıp sonrakine geçilmedi"
    atlanan = [f for ev, f in kayit if ev == "hermes_virgin_proposal"][0]["skipped"]
    assert any("regime.min_exposure_score" in a for a in atlanan), "atlama SESSİZ kaldı"


def test_hicbir_bakir_dugme_gecmezse_None_ve_UYARI(sandbox_state, monkeypatch):
    _sahte_h2(monkeypatch, bakir=["exit.trail_atr_mult"])
    monkeypatch.setattr(guard, "validate_change",
                        lambda *a, **k: guard.Verdict(False, ["sahte ret"]))
    kayit = []
    monkeypatch.setattr(hermes.obs, "warn", lambda ev, **f: kayit.append((ev, f)))

    assert hermes.propose_virgin_knob() is None
    assert any(ev == "hermes_virgin_no_valid_candidate" for ev, _ in kayit)


def test_reflect_once_BEYIN_YOKKEN_bakir_oneriyi_kapiya_verir(sandbox_state, monkeypatch):
    """Yuva eskiden BOŞTU: beyin zinciri boş dönünce tek akıllı hamle üretilmeden doğrudan aramaya
    düşülüyordu. Artık yuva bakir bir düğmeyle dolar ve AYNI boru hattından (submit) geçer."""
    _sahte_h2(monkeypatch, bakir=["exit.trail_atr_mult"])
    monkeypatch.setattr(hermes, "propose_with_llm", lambda: None)
    gorulen = {}
    monkeypatch.setattr(hermes.reflect, "submit",
                        lambda prop, *a, **k: gorulen.update(prop) or {"status": "shipped"})

    r = hermes.reflect_once(target_regime=None)

    assert r["status"] == "shipped"
    assert gorulen["variable"] == "exit.trail_atr_mult"
    assert gorulen["source"] == "deterministic:virgin"


def test_virgin_fallback_KAPATILABILIR_eski_davranis_birebir(sandbox_state, monkeypatch):
    """Dağıtım anahtarı: `HERMES_VIRGIN_FALLBACK=0` ile `reflect_once` eski hâline döner."""
    _sahte_h2(monkeypatch, bakir=["exit.trail_atr_mult"])
    monkeypatch.setattr(hermes, "propose_with_llm", lambda: None)
    monkeypatch.setattr(hermes, "VIRGIN_FALLBACK", False)
    cagrildi = []
    monkeypatch.setattr(hermes, "propose_virgin_knob", lambda: cagrildi.append(1))
    monkeypatch.setattr(hermes.reflect, "submit", lambda *a, **k: {"status": "shipped"})
    monkeypatch.setattr(hermes.reflect, "search_and_submit",
                        lambda *a, **k: {"status": "no_clearing_candidate", "search": {}})
    monkeypatch.setattr(hermes, "SEARCH_BUDGET", 1)
    import meridian.dataset as _ds
    monkeypatch.setattr(_ds, "load", lambda: (None, None))

    r = hermes.reflect_once(target_regime=None)

    assert not cagrildi, "anahtar kapalıyken deterministik bakir yol çağrıldı"
    assert r["status"] == "no_clearing_candidate"


# =================================================================================================
# 3) KEŞİF PAYI ÖLÇÜMÜ (YASA 6) — ölçülemeyen None
# =================================================================================================
def _defter(monkeypatch, degiskenler: list):
    rows = [{"id": f"H{i}", "variable": v, "new": 1, "status": "rejected_by_backtest",
             "ts": f"2026-07-{10 + i:02d}"} for i, v in enumerate(degiskenler)]
    monkeypatch.setattr(memory, "all_hypotheses", lambda: rows)
    return rows


def test_kesif_payi_aile_dagilimi_bakir_isabet_ve_olu_tekrari(sandbox_state, monkeypatch):
    # Defter sırası kronolojiktir: a,a,a → 3. satırdan sonra `a` ailesi ölü (3 deneme, 0 ship).
    _defter(monkeypatch, ["a", "a", "a", "b", "a", "c@chop"])
    _sahte_h2(monkeypatch, olu={"a": {"denendi": 4, "ship": 0, "durumlar": {}, "denenen_degerler": []}},
              bakir=["entry.min_rvol", "exit.scale_out_r"], n_hipotez=6)

    k = hermes.exploration_share(n=6)

    assert k["n_olculen"] == 6 and k["n_defter"] == 6
    assert k["aile_dagilimi"] == {"a": 4, "b": 1, "c": 1}, "rejim eki ailenin parçası olmamalı"
    assert k["en_yogun_aile"] == "a" and k["en_yogun_pay"] == pytest.approx(4 / 6, abs=1e-3)
    # bakir isabet = ailesine defterdeki İLK dokunuş (a'nın ilki, b, c) → 3
    assert k["bakir_isabet"]["n"] == 3
    assert sorted(k["bakir_isabet"]["aileler"]) == ["a", "b", "c"]
    # ölü aile tekrarı = H2'nin BUGÜN ölü dediği aileye düşen öneriler → a'nın 4 satırı
    assert k["olu_aile_tekrari"]["n"] == 4 and k["olu_aile_tekrari"]["aileler"] == ["a"]
    assert k["bakir_dugme_kalan"] == 2


def test_kesif_payi_PENCEREYE_saygi_gosterir(sandbox_state, monkeypatch):
    _defter(monkeypatch, ["a", "a", "a", "b", "c"])
    _sahte_h2(monkeypatch, olu={}, bakir=[], n_hipotez=5)

    k = hermes.exploration_share(n=2)

    assert k["n_olculen"] == 2 and k["n_defter"] == 5
    assert k["aile_dagilimi"] == {"b": 1, "c": 1}
    # b ve c pencerede İLK dokunuş; a pencereye hiç girmiyor
    assert k["bakir_isabet"]["n"] == 2


def test_kesif_payi_BOS_defterde_None_uydurmaz(sandbox_state, monkeypatch):
    monkeypatch.setattr(memory, "all_hypotheses", lambda: [])

    k = hermes.exploration_share()

    for alan in ("aile_dagilimi", "en_yogun_aile", "bakir_isabet", "olu_aile_tekrari",
                 "bakir_dugme_kalan"):
        assert k[alan] is None, f"{alan} boş defterde uydurulmuş"
    assert "ÖLÇÜLEMEDİ" in k["beyan"]


def test_kesif_payi_ISTEME_girer_yonlendirme_sayiyla_gerekcelenir(sandbox_state, monkeypatch):
    _defter(monkeypatch, ["stop_loss_atr_mult"] * 4)
    _sahte_h2(monkeypatch)

    s = hermes._exploration_sections()

    assert "Your last 4 proposals" in s
    assert "already-dead family 4/4" in s


def test_kesif_payi_TUKETICISI_var_CLI_basar(sandbox_state, monkeypatch, capsys):
    """YASA 6: ölçülüp kimseye ulaşmayan sayı üretilmemiş sayılır. Karneyi basan yollar
    (analytics.system_telemetry / /api/diagnostics) BAŞKA dosyaların malı; bu turun kendi
    okunabilir yüzeyi hermes CLI'sidir."""
    _defter(monkeypatch, ["a", "b"])
    _sahte_h2(monkeypatch, bakir=["entry.min_rvol"], n_hipotez=2)

    hermes.main(["--kesif"])

    d = json.loads(capsys.readouterr().out)
    assert d["kesif_payi"]["n_olculen"] == 2
    assert [r["knob"] for r in d["bakir_dugmeler"]] == ["entry.min_rvol"]


# =================================================================================================
# 4) DEĞİŞMEZLER — şema, K muhasebesi, kapı yetkisi
# =================================================================================================
def test_HYP_SCHEMA_geriye_uyumlu_YENI_ZORUNLU_ALAN_YOK():
    """Bu tur istem GÖVDESİNİ değiştirdi, SÖZLEŞMEYİ değil: yeni bir zorunlu alan, bugün geçerli
    olan her cevabı geçersiz kılardı."""
    props = hermes.HYP_SCHEMA["properties"]
    assert set(props) == {"variable", "new", "rationale", "predicted_direction", "predicted_delta",
                          "confidence", "regime", "skill_recommendation"}
    assert hermes.HYP_SCHEMA["required"] == [
        "variable", "new", "rationale", "predicted_direction", "predicted_delta", "confidence", "regime"]


def test_deterministik_oneri_SEMA_ALANLARINI_tasir(sandbox_state, monkeypatch):
    _sahte_h2(monkeypatch, bakir=["exit.trail_atr_mult"])

    p = hermes.propose_virgin_knob()

    for alan in hermes.HYP_SCHEMA["required"]:
        assert alan in p, f"deterministik öneri '{alan}' alanını taşımıyor"


def test_K_MUHASEBESI_DEGISMEDI_bakir_oneri_probes_tested_yazmaz(sandbox_state, monkeypatch):
    """`submit` kazanan-laneti cezasını `probes_tested`ten okur (yoksa K=1). Bakir öneri TEK adaydır;
    oraya bir sayı yazmak K-cezasını sessizce değiştirirdi."""
    _sahte_h2(monkeypatch, bakir=["exit.trail_atr_mult"])

    p = hermes.propose_virgin_knob()

    assert "probes_tested" not in p
    assert int(p.get("probes_tested", 1) or 1) == 1


def test_kapi_YETKISI_degismedi_bakir_yol_da_submitten_gecer():
    """Deterministik yol kendi kapısını KURMAZ: `reflect_once` içindeki tek ship otoritesi
    `reflect.submit`tir ve bakir öneri de oradan geçer."""
    blok = SRC.read_text().split("def propose_virgin_knob")[1].split("\ndef ")[0]
    for yasak in ("versioning.bump", "store.write_json", "memory.record", "walk_forward"):
        assert yasak not in blok, f"deterministik yol boru hattını atlıyor: {yasak}"


def test_bolumler_KANIT_TAVANINA_tabi_degil_dusurulemez(sandbox_state, monkeypatch):
    """`_render_pack` tavana çarpınca alanları öncelik sırasına göre TÜMDEN düşürür. Bu turun tek
    çözdüğü şey iki bölümün beyne ULAŞMASI; onları düşebilir bir kuyruğa koymak, işi yapmadan
    yapmış görünmekti."""
    _sahte_h2(monkeypatch)
    monkeypatch.setattr(hermes, "EVIDENCE_CAP", 10)      # paketi tümüyle düşür

    p = hermes._user_prompt(with_schema=True)

    assert "EXPLORATION BALANCE" in p and "NEVER-PROPOSED KNOBS" in p
