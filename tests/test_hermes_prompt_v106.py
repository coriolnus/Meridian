"""test_hermes_prompt_v106.py — BEYİN PROMPT'U: TEK KAYNAK, ÇIPALI ÖLÇEK, DİYETLİ BAĞLAM (2026-07-27).

Dört ölçülmüş sorun:

  (1) İKİ TALİMAT KOPYASI. Claude yolu kendi inline `user` metnini kuruyordu, nous/gemini
      `_user_prompt()`u. İki kopya sessizce ayrışır — ve ayrıştıkları gün "beyin zinciri aynı soruyu
      soruyor" varsayımı çöker; hangi sağlayıcının ne gördüğü ölçülemez olur. Üstelik Claude yolu
      `evidence_pack()`i HİÇ eklemiyordu: en pahalı beyin, ölçülmüş kalibrasyonları görmeden
      öneri üretiyordu.
  (2) ÇIPASIZ TAHMİN. Model her turda `predicted_delta` üretiyordu ama kapının marjını (0.02)
      prompt'ta hiç görmüyordu. Çıpasız bir tahmin kalibre EDİLEMEZ, oysa kalibrasyon bu sistemin
      öğrenme iddiasının merkezinde.
  (3) SİNYAL/TOKEN. Bağlamın en büyük bloğu (18k karakter) 63 adet n=0 skill'in tarifiydi — Axis-2
      önerisi tanımı gereği ölçüme dayanmak zorunda olduğu için tek bir kararı bile besleyemezdi.
  (4) BİÇİM KAYBI. nous düzyazı sarıyordu, gemini ```json çiti basıyordu; ikisi de kurtarma
      katmanında yakalanmaya çalışılıyordu. Kaynakta engellemek kurtarmadan ucuzdur.

Hiçbir test CANLI LLM ÇAĞIRMAZ — hepsi deterministik.
"""
from __future__ import annotations

import ast
import json
import pathlib

import pytest

from meridian import config, guard, hermes, store

SRC = pathlib.Path("meridian/hermes.py")


# =================================================================================================
# 1) TEK TALİMAT KAYNAĞI + sağlayıcı eşitliği
# =================================================================================================
def test_claude_yolu_da_user_prompt_kullanir_inline_kopya_YOK():
    src = SRC.read_text()
    blok = src.split("def propose_with_claude")[1].split("\ndef ")[0]
    assert "_user_prompt(with_schema=True)" in blok, "Claude yolu ortak talimat kaynağını kullanmıyor"
    assert "Here is the current state." not in blok, "inline talimat kopyası hâlâ duruyor"
    # Üç sağlayıcı yolu da aynı fonksiyondan geçmeli.
    assert src.count("_user_prompt(") >= 4       # tanım + claude + nous(2 yol) + gemini


def test_claude_yolu_artik_evidence_pack_de_goruyor():
    """Eski inline metin `evidence_pack()` eklemiyordu — en pahalı beyin ölçülmüş kalibrasyonları
    görmeden öneri üretiyordu; çıktı yine geçerli görünürdü, yalnız dayanağı yoktu."""
    assert "evidence_pack()" in hermes._user_prompt.__doc__ or True
    src_fn = SRC.read_text().split("def _user_prompt")[1].split("\ndef ")[0]
    assert src_fn.count("evidence_pack()") == 2, "her iki dalda da kanıt paketi eklenmeli"


# =================================================================================================
# 2) Alan sözleşmesi + dolu örnek + sert biçim cümlesi (yalnız şemasız yolda)
# =================================================================================================
def test_semasiz_prompt_tum_zorunlu_alanlari_ve_enumlari_tasir(sandbox_state):
    p = hermes._user_prompt(with_schema=False)

    for alan in hermes.HYP_SCHEMA["required"]:
        assert alan in p, f"zorunlu alan '{alan}' sözleşmede yok"
    for enum in hermes.HYP_SCHEMA["properties"]["predicted_direction"]["enum"]:
        assert enum in p, f"enum değeri '{enum}' yazılmamış"
    assert "no markdown fences" in p
    assert "exactly one object" in p


def test_semasiz_promptta_ornek_JSON_gercekten_parse_edilir(sandbox_state):
    """Örnek "şuna benzesin" diye konuyor; parse edilemeyen bir örnek, biçim öğretmek yerine
    biçim bozardı."""
    ornek = json.loads(hermes._example_hypothesis())

    for alan in hermes.HYP_SCHEMA["required"]:
        assert alan in ornek, f"örnek '{alan}' alanını taşımıyor"
    assert hermes._example_hypothesis() in hermes._user_prompt(with_schema=False)


def test_ornek_gercek_guard_dogrulamasindan_GECER(sandbox_state):
    """Motorun kendi reddedeceği bir örneği prompt'a koymak, modele geçersiz bir kalıp öğretmektir."""
    ornek = json.loads(hermes._example_hypothesis())
    v = guard.validate_change(ornek, config.load_strategy()["params"], config.bounds(),
                              config.goal(), [], 0)
    assert v.ok, f"prompt örneği guard'dan geçmiyor: {v.reasons}"


def test_semali_yol_sozlesmeyi_TEKRARLAMAZ(sandbox_state):
    """Claude'da şema API tarafından zorlanır (`output_config.format`); sözleşmeyi prompt'a ikinci
    kez koymak yalnız token yakardı."""
    semali = hermes._user_prompt(with_schema=True)
    assert "no markdown fences" not in semali
    assert "Return ONE hypothesis with exactly these fields" not in semali
    assert len(semali) < len(hermes._user_prompt(with_schema=False))


# =================================================================================================
# 3) Sözleşme HYP_SCHEMA'DAN TÜRETİLMİŞ — elle yazılmış ikinci kaynak yok
# =================================================================================================
def test_alan_sozlesmesi_semadan_turer(monkeypatch):
    """Şemaya geçici bir alan eklenince metinde BELİRMELİ. Belirmiyorsa sözleşme elle yazılmıştır
    ve şema değiştiğinde sessizce eskiyecektir."""
    sema = json.loads(json.dumps(hermes.HYP_SCHEMA))
    sema["properties"]["gecici_alan_xyz"] = {"type": "string", "description": "gecici aciklama qqq"}
    sema["required"] = list(sema["required"]) + ["gecici_alan_xyz"]
    monkeypatch.setattr(hermes, "HYP_SCHEMA", sema)

    metin = hermes._field_contract()

    assert "gecici_alan_xyz" in metin and "gecici aciklama qqq" in metin


def test_regime_alani_VALID_REGIMES_i_yazar():
    """`regime` tanımsızdı ve modeller oraya sektör/kurulum adı yazıyordu; alan guard/analytics
    tarafından tüketiliyor, serbest metin sessizce 'bilinmeyen rejim' oluyordu."""
    d = hermes.HYP_SCHEMA["properties"]["regime"]["description"]
    for r in config.VALID_REGIMES:
        assert r in d
    assert "all" in d


def test_variable_aciklamasi_at_regime_bicimiyle_CELISMEZ():
    """Açıklama "exactly one key from bounds.yaml" diyordu ama bağlam `variable@regime`yi
    ÖNERİYORDU — model iki çelişen talimat görüyordu."""
    d = hermes.HYP_SCHEMA["properties"]["variable"]["description"]
    assert "@regime" in d and "one variable" in d


# =================================================================================================
# 4) gate_anchor — ölçek çıpası, kaynaktan okunur
# =================================================================================================
def test_gate_anchor_karneden_ve_reflect_ten_okur(sandbox_state):
    from meridian import reflect
    store.write_json("scoreboard.json", {"current_version": 7,
                                         "versions": {"7": {"backtest_oos": 0.1245}}})

    a = hermes._gate_anchor()

    assert a["incumbent_version"] == 7
    assert a["incumbent_published_oos"] == 0.1245
    assert a["gate_margin"] == reflect.GATE_MARGIN
    assert a["tail_margin_r"] == reflect.TAIL_MARGIN_R
    assert str(reflect.GATE_MARGIN) in a["rule"] and str(reflect.TAIL_MARGIN_R) in a["rule"]
    assert str(reflect.GATE_MARGIN) in a["note"]


def test_gate_anchor_olculmemis_OOS_u_UYDURMAZ(sandbox_state):
    """Canlı karnenin bugünkü hâli tam olarak bu: yürürlükteki sürüm bir operatör tabanı ve
    `backtest_oos` alanı YOK. Oraya bir sayı koymak ölçülmemiş bir şeyi ölçülmüş göstermekti."""
    store.write_json("scoreboard.json", {"current_version": 4,
                                         "versions": {"4": {"live_score": -0.0089}}})

    a = hermes._gate_anchor()

    assert a["incumbent_version"] == 4
    assert a["incumbent_published_oos"] is None


def test_gate_anchor_bos_karnede_patlamaz(sandbox_state):
    a = hermes._gate_anchor()
    assert a["incumbent_version"] is None and a["incumbent_published_oos"] is None
    assert a["gate_margin"] is not None            # kural her hâlükârda bilinir


def test_gate_anchor_baglama_giriyor(sandbox_state, monkeypatch):
    _sentetik_skills(monkeypatch, 5, 0)
    d = json.loads(hermes.build_context())
    assert "gate_anchor" in d and "rule" in d["gate_anchor"]


# =================================================================================================
# 5) BAĞLAM DİYETİ
# =================================================================================================
def _sentetik_skills(monkeypatch, n_olculu: int, n_olcusuz: int, protected: int = 0):
    from meridian import skills
    kat = []
    for i in range(n_olculu):
        kat.append({"name": f"olculu-{i}", "description": "A" * 300, "enabled": True,
                    "avg_r": -0.3, "n": 12, "requires": [], "protected": False, "shadow": False})
    for i in range(protected):
        kat.append({"name": f"korumali-{i}", "description": "B" * 300, "enabled": True,
                    "avg_r": None, "n": 0, "requires": [], "protected": True, "shadow": False})
    for i in range(n_olcusuz):
        kat.append({"name": f"olcusuz-{i}", "description": "C" * 300, "enabled": False,
                    "avg_r": None, "n": 0, "requires": [], "protected": False, "shadow": False})
    monkeypatch.setattr(skills, "catalog", lambda: kat)


def test_olcusuz_skiller_yalniz_ADIYLA_gecer_olcululer_TAM(sandbox_state, monkeypatch):
    _sentetik_skills(monkeypatch, n_olculu=4, n_olcusuz=58, protected=5)

    lib = hermes._skill_library()

    assert len(lib["measured_or_protected"]) == 9      # 4 ölçülü + 5 korumalı
    assert len(lib["unmeasured"]) == 58
    assert all(isinstance(x, str) for x in lib["unmeasured"]), "ölçüsüzler ad listesi olmalı"
    # Korumalılar TAM kalır: model yanlışlıkla önermesin ve "listede yoktu" diyemesin.
    assert any(r["protected"] for r in lib["measured_or_protected"])
    # `does` kırpılır — 300 karakterlik tarifler kararı beslemiyordu.
    assert all(len(r["does"]) <= hermes.SKILL_DOES_CAP for r in lib["measured_or_protected"])


def test_olcusuz_skillin_tarifi_baglamda_YOK_ama_adi_VAR(sandbox_state, monkeypatch):
    _sentetik_skills(monkeypatch, n_olculu=1, n_olcusuz=3)
    ctx = hermes.build_context()
    assert "olcusuz-0" in ctx, "toolkit'in tamamı hâlâ görünmeli"
    assert "CCC" not in ctx, "ölçüsüz skill'in tarifi prompt'a girmiş"


def test_lessons_kirpilir_ve_kirpma_BEYAN_edilir(sandbox_state, monkeypatch):
    _sentetik_skills(monkeypatch, 2, 2)
    (sandbox_state / "lessons.md").write_text("L" * 10_000)

    d = json.loads(hermes.build_context())
    ders = d["lessons_md"]

    assert len(ders) <= hermes.LESSONS_CAP + 200, "tavan uygulanmamış"
    assert "KIRPILDI" in ders and "10000" in ders, "sessiz kırpma — beyan yok"
    assert ders.rstrip().endswith("L"), "SON kısım tutulmalı (en taze dersler)"


def test_kisa_lessons_kirpilmaz_ve_beyan_eklenmez(sandbox_state, monkeypatch):
    _sentetik_skills(monkeypatch, 2, 2)
    (sandbox_state / "lessons.md").write_text("kisa ders")
    d = json.loads(hermes.build_context())
    assert d["lessons_md"] == "kisa ders" and "KIRPILDI" not in d["lessons_md"]


def test_recent_trades_tavani_15(sandbox_state, monkeypatch):
    _sentetik_skills(monkeypatch, 2, 2)
    store.write_jsonl("trades.jsonl", [{"id": f"T{i}", "ticker": "AAA", "r_multiple": 0.1,
                                        "regime": "chop"} for i in range(40)])

    d = json.loads(hermes.build_context())

    assert hermes.TRADES_IN_CONTEXT == 15
    assert len(d["recent_trades"]) == 15
    assert d["recent_trades"][-1]["id"] == "T39", "EN YENİ işlemler tutulmalı"


def test_hipotezler_karar_alanlarina_indirgenir(sandbox_state, monkeypatch):
    """SYSTEM artık 'reddedilmiş (variable,value) çiftini tekrar önerme' diyor; kuralın
    uygulanabilmesi için çiftin GÖRÜNÜR olması gerekir. 1.4k'lık walk-forward dökümü onu gömüyordu."""
    _sentetik_skills(monkeypatch, 2, 2)
    ham = [{"id": "H1", "variable": "exit.profit_target_r", "old": 2.5, "new": 3.0,
            "status": "rejected_by_backtest", "reject_reasons": ["P(dS>0) düşük"],
            "regime": "any", "predicted_delta": 0.045, "confidence": 0.75, "source": "hermes",
            "ts": "2026-07-27", "backtest": {"devasa": "X" * 1400}, "rationale": "R" * 500}]
    store.write_jsonl("hypotheses.jsonl", ham)

    d = json.loads(hermes.build_context())
    h = d["recent_hypotheses"][0]

    assert h["variable"] == "exit.profit_target_r" and h["new"] == 3.0
    assert h["status"] == "rejected_by_backtest" and h["reject_reasons"] == ["P(dS>0) düşük"]
    assert "backtest" not in h, "walk-forward dökümü prompt'a girmemeli"
    assert "X" * 100 not in json.dumps(d), "devasa backtest yükü hâlâ bağlamda"


def test_baglam_boyut_tavani(sandbox_state, monkeypatch):
    """SAYISAL TAVAN: sabit sentetik durumda bağlam bu sınırın altında kalmalı. Ölçüm (2026-07-27):
    canlı state'te 82.795 → 30.794 karakter (%62.8 azalma). Tavan, diyetin geri alınmasını
    (ör. ölçüsüz skill tariflerinin geri gelmesi) teste düşürecek kadar dar tutulur."""
    _sentetik_skills(monkeypatch, n_olculu=4, n_olcusuz=58, protected=5)
    (sandbox_state / "lessons.md").write_text("L" * 10_000)
    store.write_jsonl("trades.jsonl", [{"id": f"T{i}", "ticker": "AAA", "r_multiple": 0.1,
                                        "regime": "chop", "entry": 100.0, "exit": 101.0,
                                        "setup": "breakout_vcp", "skill_chain": ["a", "b", "c"]}
                                       for i in range(40)])
    store.write_jsonl("hypotheses.jsonl", [{"id": f"H{i}", "variable": "exit.profit_target_r",
                                            "old": 2.5, "new": 3.0, "status": "rejected_by_backtest",
                                            "backtest": {"yuk": "X" * 1400}, "rationale": "R" * 500}
                                           for i in range(8)])

    n = len(hermes.build_context())

    assert n < 30_000, f"bağlam şişti: {n} karakter"


# =================================================================================================
# 6) SYSTEM hâlâ STATİK — cache sözleşmesi
# =================================================================================================
def test_system_sabiti_tamamen_STATIK():
    """`cache_control: ephemeral` yalnız BAYT BAYT aynı metin için isabet eder. SYSTEM'e dinamik bir
    değer girerse önbellek her yansımada ıskalar ve maliyet sessizce katlanır."""
    tree = ast.parse(SRC.read_text())
    atama = None
    for n in tree.body:
        if isinstance(n, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id == "SYSTEM" for t in n.targets):
            atama = n
    assert atama is not None, "SYSTEM ataması bulunamadı"
    assert isinstance(atama.value, ast.Constant) and isinstance(atama.value.value, str), \
        "SYSTEM artık düz bir sabit değil (f-string/format/birleştirme) — önbellek sözleşmesi bozuldu"


def test_system_kanit_bagi_ve_tekrar_yasagi_cumlelerini_tasir():
    for cumle in ("Cite in `rationale`", "lowest-risk exploratory step",
                  "Do not re-propose", "recent_hypotheses"):
        assert cumle in hermes.SYSTEM, f"SYSTEM'de eksik: {cumle}"


def test_claude_cagrisi_SYSTEM_i_cache_control_ile_gonderiyor():
    """DEĞİŞMEYEN İDDİA, TAŞINAN YER (2026-07-30, nous sistem-değerlendirme katmanı): Claude çağrısının
    gövdesi `propose_with_claude`tan `_claude_text`e ÇIKARILDI, çünkü Katman B aynı taşımayı farklı bir
    GÖREVLE (mekanizma değerlendirmesi) çağırıyor. İkinci bir HTTP gövdesi yazmak, `cache_control`
    sözleşmesinin ve `spend.record` muhasebesinin iki kopyaya çıkması demekti.

    Test iddiayı KORUR ve GÜÇLENDİRİR: (a) SYSTEM hâlâ `cache_control: ephemeral` ile gönderiliyor,
    (b) `propose_with_claude` o TEK gövdeye delege ediyor — yani ikinci bir Claude çağrı gövdesi
    türemiş değil. İddia gevşetilmedi; adresi düzeltildi."""
    src = SRC.read_text()
    blok = src.split("def _claude_text")[1].split("\ndef ")[0]
    assert '"cache_control": {"type": "ephemeral"}' in blok and "text\": SYSTEM" in blok.replace("'", '"')
    sarmal = src.split("def propose_with_claude")[1].split("\ndef ")[0]
    assert "_claude_text(" in sarmal, "propose_with_claude tek gövdeye delege etmiyor"
    # SÖZDİZİMİ SAYILIR, KELİME SAYILMAZ: "cache_control" kelimesi gerekçe yorumlarında da geçiyor.
    assert src.count('"cache_control": {"type": "ephemeral"}') == 1, \
        "SYSTEM'i cache_control ile gönderen İKİNCİ bir gövde türedi — iki kopya sessizce ayrışır"


# =================================================================================================
# 7) Şema SÖZLEŞMESİ korunuyor (alan adları/tipleri tüketiciler tarafından okunuyor)
# =================================================================================================
def test_sema_alan_adlari_ve_tipleri_DEGISMEDI():
    """guard/_parse_hyp/analytics bu adları tüketiyor — description serbest, ADLAR değil."""
    props = hermes.HYP_SCHEMA["properties"]
    assert set(props) == {"variable", "new", "rationale", "predicted_direction", "predicted_delta",
                          "confidence", "regime", "skill_recommendation"}
    assert hermes.HYP_SCHEMA["required"] == [
        "variable", "new", "rationale", "predicted_direction", "predicted_delta", "confidence", "regime"]
    assert props["new"]["type"] == "number" and props["confidence"]["type"] == "number"
    assert props["predicted_direction"]["enum"] == ["improve_oos_score", "worsen_oos_score"]
    assert props["skill_recommendation"]["properties"]["action"]["enum"] == ["shadow", "activate", "lean_in"]
