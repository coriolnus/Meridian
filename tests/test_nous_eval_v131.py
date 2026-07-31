"""test_nous_eval_v131.py — NOUS SİSTEM-DEĞERLENDİRME KATMANI (ROADMAP §3.2, 2026-07-30).

Bu turun çivileri. HİÇBİR TEST CANLI STATE'E YAZMAZ (canlı worker koşuyor) ve HİÇBİR TEST LLM
ÇAĞIRMAZ (`hermes.chain_text` monkeypatch'lenir — ağa çıkan bir test, geçtiğinde bir şey
kanıtlamaz, kotayı yakar ve makineye göre farklı sonuç verir).

  ① KATMAN A — TELEMETRİ PAKETİ: 12 bölüm sabitle birebir; boş state'te SAYI UYDURMAZ; üreticinin
     kendi beyan ettiği ölçüm boşlukları AYRI sayaçta (bölüm doldu ≠ mekanizma ölçüyor).
  ② KATMAN B — KALİTE KAPISI: kanıt-atıfsız / eksik alanlı / geçersiz enum'lu öneri DÜŞER, düşme
     SAYISI ve NEDENİ kayda geçer; ayrıştırılamayan cevap şablon öneri ÜRETMEZ.
  ③ KATMAN C — KÖPRÜ: parametre-şekilli öneri composite kuyruğuna `nous_eval` damgasıyla girer;
     AYRI BÜTÇE AÇILMAZ (H4'ün 3/hafta tavanı) ve taşan öneri GÖRÜNÜR biçimde DEVREDER.
  ④ KATMAN D — ANAYASAL KORUMA: çekirdek-şekilli öneri kuyruğa YAPISAL olarak giremez (tek çağrı
     yeri + AST), deneme SESSİZ DÜŞMEZ (istisna + AUTHORITY_CHANGE alarmı), ve modelin KENDİ
     "parametre" etiketi şekli EZEMEZ.
  ⑤ TÜKETİCİLER (YASA 6) + SÖZLEŞME: defter ledgers sözleşmeli, dış okuyucusu var, pano kartı
     düşürülen-öneri sayısını çiziyor, `--ozet` CLI Rol 1'e özet basıyor, ve önceki önerilerin
     akıbeti SONRAKİ prompt'a geri besleniyor.
  ⑥ SYSTEM STATİK KALIR: görev şablonu `nous_eval.TASK`tadır, hermes.SYSTEM'e SIZMAZ (AST).
"""
from __future__ import annotations

import ast
import json
import pathlib

import pytest

from meridian import analytics, hermes, hermes_composite, ledgers, nous_eval, obs, store

SRC = pathlib.Path("meridian")

# GERÇEK bounds düğmeleri (state/bounds.yaml). Uydurma bir düğme adı, köprü testlerini "bounds'ta
# tanımlı değil" reddine sokar ve test kendi kurgusunu değil şekil denetimini ölçmüş olurdu.
_KNOB_A = "stop_loss_atr_mult"      # min 0.8 · max 4.0 · step 0.1
_KNOB_B = "exit.time_stop_days"     # min 3   · max 40  · step 1


def _tohumla(st):
    """`sandbox_state` boş state verir; köprünün bounds'a ihtiyacı var (bkz. v125'teki aynı not)."""
    for f in ("bounds.yaml", "goal.yaml"):
        p = st / f
        if not p.exists():
            p.write_text(pathlib.Path("state") .joinpath(f).read_text())
    return st


def _tel(**ek) -> dict:
    """Küçük ama GERÇEKÇİ bir telemetri paketi: atıf jetonları gerçek alan adları ve sayılardır."""
    t = {
        "hafta": "2026-W31",
        "bolum_adlari": list(analytics.TELEMETRY_SECTIONS),
        "bolumler": {
            "kar_selalesi": {"n": 95, "genel": {"net_r": -0.0421, "sinyal_mfe_r": 0.9648}},
            "veto_istatistigi": {"islem_kapisi": {"n_plan": 390,
                                                  "yumusak_vetolar": [{"veto": "leading_sector",
                                                                       "n": 217}]}},
            "golge_varyant_ayrisma": {"durum": "DEFTER BOŞ — ilk satırlar ilk EOD döngüsünde doğar",
                                      "n_satir": 0},
            "dsr_pbo": {"pbo": {"durum": "olculemedi", "n_aday": 0, "min_aday": 8}},
        },
        "bounds_dugmeleri": [_KNOB_A, _KNOB_B, "entry.min_score"],
    }
    t.update(ek)
    return t


def _oneri(**ek) -> dict:
    o = {"alan": "kar_selalesi",
         "gozlem": "kar_selalesi bölümünde net_r -0.0421 iken sinyal_mfe_r 0.9648 — çıkış "
                   "sunulan hareketin neredeyse tamamını geri veriyor",
         "oneri": "çıkış eşiğini sıkılaştır",
         "beklenen_etki": "net_r +0.10 yönünde",
         "onerilen_olcum": "profit_waterfall geri_verilen_r yeniden ölçülür",
         "oncelik": "yuksek", "sekil": "tasarim"}
    o.update(ek)
    return o


def _cevap(oneriler: list) -> str:
    return json.dumps({"oneriler": oneriler}, ensure_ascii=False)


# =================================================================================================
# ① KATMAN A — TELEMETRİ PAKETİ
# =================================================================================================
def test_A1_paket_12_bolumu_sabitle_birebir_tasir(sandbox_state):
    """Bölüm adları ADLANDIRILMIŞ SABİTTİR. Kod ile sabit ayrışırsa "paket bu hafta neyi görmedi"
    sorusu cevaplanamaz hâle gelir — ve o soru Katman B'nin en verimli öneri kaynağıdır."""
    _tohumla(sandbox_state)
    t = analytics.system_telemetry()
    assert set(t["bolumler"]) == set(analytics.TELEMETRY_SECTIONS), \
        "üretilen bölümler sabit listeyle ayrışıyor"
    assert t["sabit_ile_ayrisan"] == [], "sabitte olup pakette olmayan bölüm var"
    assert t["n_bolum"] == len(analytics.TELEMETRY_SECTIONS) == 12


def test_A2_bos_state_SAYI_UYDURMAZ(sandbox_state):
    """Boş bir state'te paket SAHTE bir "her şey yolunda" göstermez: ölçülemeyen bölüm `olculemedi`
    der ve NEDENİNİ yazar. `neden` alanı olmayan bir "olculemedi", denetlenemez bir boşluktur."""
    _tohumla(sandbox_state)
    t = analytics.system_telemetry()
    assert t["n_olculemedi"] >= 1, "tamamen boş state'te hiçbir bölüm ölçülemedi demiyor"
    for ad in t["olculemeyenler"]:
        b = t["bolumler"][ad]
        assert b["durum"] == "olculemedi" and str(b.get("neden") or "").strip(), \
            f"{ad}: ölçülemedi ama nedeni yazılmamış"
    # kâr şelalesi boş defterde ÖLÇÜLEMEZ ve bunu tabanın adıyla söyler
    assert t["bolumler"]["kar_selalesi"]["durum"] == "olculemedi"
    assert str(analytics.WATERFALL_MIN_N) in t["bolumler"]["kar_selalesi"]["neden"]


def test_A3_iki_sayac_ayri_kalir_bolum_doldu_mekanizma_olcuyor_DEGIL(sandbox_state):
    """`n_olculemedi` (üretici hiç çıktı vermedi) ile `beyan_edilen_bosluklar` (üretici çıktı verdi
    ama kendi içinde "ölçemedim" dedi) AYRI sorulardır. İlk canlı koşuda birincisi 0, ikincisi 3'tü:
    yalnız birinciyi raporlamak "12/12 bölüm doldu, her şey ölçülüyor" yanılgısını üretirdi."""
    _tohumla(sandbox_state)
    bolumler = {
        "dsr_pbo": {"pbo": {"durum": "olculemedi", "neden": "defterde 0/8 aday"}},
        "golge_varyant_ayrisma": {"durum": "DEFTER BOŞ — ilk satırlar ilk EOD döngüsünde doğar"},
        "kar_selalesi": {"n": 95, "genel": {"net_r": -0.04}},
    }
    bos = analytics._beyan_edilen_bosluklar(bolumler)
    assert "dsr_pbo.pbo.durum" in bos and "golge_varyant_ayrisma.durum" in bos
    assert not any(b.startswith("kar_selalesi") for b in bos), \
        "dolu bir bölüm boşluk sayıldı — tarama kodun deyimini değil sayıları okuyor"
    # HEURİSTİK YASAK: "0 var demek ki ölçülmemiş" çıkarımı YAPILMAZ (o bir tahmindir)
    assert analytics._beyan_edilen_bosluklar({"x": {"n": 0, "toplam": None}}) == []


def test_A4_paket_bounds_dugmelerini_SALT_OKUR(sandbox_state):
    """Katman C yalnız bounds'ta TANIMLI düğme için kurulabilir; adlar prompt'ta olmazsa beyin var
    olmayan düğmeler önerir ve kalite kapısı gürültüye boğulur. Paket bounds'u YAZMAZ."""
    _tohumla(sandbox_state)
    onceki = (sandbox_state / "bounds.yaml").read_text()
    t = analytics.system_telemetry()
    assert len(t["bounds_dugmeleri"]) >= 5 and t["bounds_dugmeleri"] == sorted(t["bounds_dugmeleri"])
    assert (sandbox_state / "bounds.yaml").read_text() == onceki, "paket bounds.yaml'a DOKUNDU"


def test_A5_bolum_hatasi_paketi_dusurmez_ama_SESSIZ_de_kalmaz(sandbox_state, monkeypatch):
    """Tek bölüm yüzünden paketin tamamı düşerse haftalık değerlendirme HİÇ koşmaz — ve o sessizlik
    bir bölümün eksikliğinden pahalıdır. Ama arıza `olculemedi`ye çevrilirken istisna metni
    KAYBOLMAZ (YASA 4: sessiz yutma yok)."""
    _tohumla(sandbox_state)

    def _patla():
        raise RuntimeError("bilerek patlatıldı")
    monkeypatch.setattr(analytics, "skill_attribution", _patla)
    t = analytics.system_telemetry()
    b = t["bolumler"]["skill_atiflari"]
    assert b["durum"] == "olculemedi" and "RuntimeError" in b["neden"] \
        and "bilerek patlatıldı" in b["neden"]
    assert len(t["bolumler"]) == 12, "bir bölümün arızası paketi düşürdü"


def test_A6_veto_istatistigi_IKI_KAPIYI_karistirmaz(sandbox_state):
    """390 plan reddi ile 41 hipotez reddi aynı kovaya atılırsa öğrenme kapısının istatistiği
    görünmez olur (`rejected_by_dsr`ın `rejected_by_backtest`e karıştırılmama gerekçesinin aynısı).
    Ayrıca sert/yumuşak ayrımı korunur: yumuşak bir not planı ÖLDÜRMEZ."""
    _tohumla(sandbox_state)
    store.append_jsonl("trade_plans.jsonl", {
        "id": "P-2026-07-30-AAA", "date": "2026-07-30", "ticker": "AAA", "setup": "s", "score": 70,
        "entry_trigger": 1.0, "stop": 0.9, "strategy_version": 1, "gate_verdict": "NO_GO",
        "gate_reasons": ["max_open_positions doldu"],
        "gate_checks": [{"check": "max_open_positions", "passed": False, "severity": "hard"},
                        {"check": "leading_sector", "passed": False, "severity": "soft"},
                        {"check": "score_band", "passed": True, "severity": "soft"}]})
    v = analytics.gate_veto_tally()
    assert v["islem_kapisi"]["n_plan"] == 1 and v["islem_kapisi"]["hukumler"] == {"NO_GO": 1}
    assert {"veto": "max_open_positions", "n": 1} in v["islem_kapisi"]["sert_vetolar"]
    assert {"veto": "leading_sector", "n": 1} in v["islem_kapisi"]["yumusak_vetolar"]
    assert {"veto": "score_band", "n": 1} not in v["islem_kapisi"]["yumusak_vetolar"], \
        "GEÇEN bir kontrol veto sayıldı"
    assert "hipotez_kapisi" in v and v["hipotez_kapisi"]["n_hipotez"] == 0
    assert "aile" in v["beyan"].lower(), "aile türetiminin YAKLAŞIM olduğu beyan edilmiyor"


# =================================================================================================
# ② KATMAN B — KALİTE KAPISI
# =================================================================================================
def test_B1_kanit_atifsiz_oneri_DUSER_ve_dusme_SAYILIR(sandbox_state):
    """Kapının asıl dişi. Atıfsız gözlem, pakete değil MODELİN HAFIZASINA dayanır — ve bu sistemde
    uydurma bir sayıya dayanan öneri, önerinin en pahalı türüdür (ölçüm bütçesi yakar, hiçbir şey
    öğretmez). Düşme SESSİZ olamaz: sayı ve neden kayda geçer."""
    _tohumla(sandbox_state)
    tel = _tel()
    iyi = _oneri()
    kotu = _oneri(gozlem="Sistem genel olarak iyi görünüyor, biraz daha agresif olabilir.")
    r = nous_eval.ayristir(_cevap([iyi, kotu]), tel)
    assert r["n_uretilen"] == 2 and len(r["kabul"]) == 1 and r["n_dusen"] == 1
    assert r["dusme_nedenleri"] == {"kanit_atifsiz": 1}
    assert r["kabul"][0]["kanit_atifi"], "kabul edilen önerinin atıf listesi BOŞ"
    # atıf DENETLENEBİLİR olmalı: eşleşen jeton kaydedilir
    assert any("net_r" in a or "0.042" in a for a in r["kabul"][0]["kanit_atifi"])


def test_B2_jenerik_alan_adlari_atif_SAYILMAZ(sandbox_state):
    """"beyan"/"durum"/"rol" her bölümde geçer. Bunları atıf saymak, boş bir cümleyi kanıtlı sanmak
    ve kapıyı kendi eliyle geçersiz kılmak olurdu."""
    _tohumla(sandbox_state)
    j = nous_eval.kanit_jetonlari(_tel())
    assert "beyan" not in j["adlar"] and "durum" not in j["adlar"] and "rol" not in j["adlar"]
    assert nous_eval.kanit_atifi("beyan ve durum alanlarına göre rol belirsiz", j) == []
    # ayırt edici OLMAYAN sayılar da atıf değildir ("3 kez" her metinde var)
    assert nous_eval.kanit_atifi("bunu 8 kez gördük", j) == []
    # ayırt edici bir sayı ise atıftır
    assert nous_eval.kanit_atifi("n_plan 390 satırda", j)


def test_B3_eksik_alan_ve_gecersiz_enum_DUSER(sandbox_state):
    """ZORUNLU alanların her biri bir karardır: `onerilen_olcum` yoksa öneri falsifiye edilemez,
    `oncelik` yoksa liste sıralanamaz — sıralanamayan liste tüketilemez."""
    _tohumla(sandbox_state)
    tel = _tel()
    r = nous_eval.ayristir(_cevap([
        _oneri(onerilen_olcum=""),                 # eksik zorunlu alan
        _oneri(oncelik="kritik"),                  # enum dışı
        _oneri(sekil="her_neyse"),                 # enum dışı
        "bu bir sözlük değil",
    ]), tel)
    assert r["kabul"] == [] and r["n_dusen"] == 4
    assert r["dusme_nedenleri"]["eksik_alan:onerilen_olcum"] == 1
    assert r["dusme_nedenleri"]["gecersiz_oncelik"] == 1
    assert r["dusme_nedenleri"]["gecersiz_sekil"] == 1
    assert r["dusme_nedenleri"]["sozluk_degil"] == 1
    assert nous_eval.ZORUNLU_ALANLAR and set(nous_eval.ONCELIKLER) == {"yuksek", "orta", "dusuk"}


def test_B4_ayristirilamayan_cevap_SABLON_ONERI_URETMEZ(sandbox_state):
    """UYDURMA YASAĞI. Ayrıştırılamayan cevap, "0 öneri düştü" diye kaydedilemez: tek tek öneri
    SAYILAMAZ, o yüzden durum koşu düzeyinde `ayristirilamadi` olur."""
    _tohumla(sandbox_state)
    r = nous_eval.ayristir("Merhaba! Sanırım stop mesafesini gevşetmelisiniz.", _tel())
    assert r["durum"] == "ayristirilamadi" and r["kabul"] == []
    assert r["dusme_nedenleri"] == {"cevap_ayristirilamadi": 1}
    bos = nous_eval.ayristir("", _tel())
    assert bos["durum"] == "cevap_yok" and bos["kabul"] == []


def test_B5_beyin_yoksa_kosulamadi_yazilir_SABLON_URETILMEZ(sandbox_state, monkeypatch):
    """LLM erişimi yoksa/kesintiliyse koşu DÜRÜSTÇE "kosulamadi" olur ve hangi ayağın niçin cevap
    vermediği yazılır. Şablon bir öneri listesi üretmek, ölçülmemiş bir şeyin sonucunu uydurmaktır."""
    _tohumla(sandbox_state)
    monkeypatch.setattr(hermes, "chain_text", lambda *a, **k: {
        "text": None, "beyin": None, "model": None,
        "neden": {"claude": "no_credentials", "nous": "cooldown", "gemini": "failed"}})
    out = nous_eval.haftalik_degerlendirme(telemetri=_tel())
    assert out["kosu"]["durum"] == "kosulamadi" and out["kabul"] == []
    assert out["kosu"]["zincir_neden"]["nous"] == "cooldown"
    assert store.read_jsonl(nous_eval.PROPOSALS_FILE) == [], "koşulamayan tur deftere satır yazdı"
    # koşu kaydı YAZILIR: "koşulamadı" da bir kayıttır, sessizlik değil
    assert (store.read_json(nous_eval.RUNS_FILE, {}).get("haftalar") or {}), \
        "koşulamayan tur hiç kaydedilmedi — sessiz kaldı"


# =================================================================================================
# ③ KATMAN C — KÖPRÜ (H4 BÜTÇESİ, AYRI BÜTÇE YOK, DEVİR GÖRÜNÜR)
# =================================================================================================
def _param_oneri(knobs: dict, **ek) -> dict:
    """Parametre-şekilli öneri. NOT: gözlem çekirdek kelimesi İÇERMEZ (yoksa Katman D onu haklı
    olarak `cekirdek_hakkinda`ya çevirir ve kuyruk yolu kapanır)."""
    o = _oneri(sekil="parametre",
               gozlem="time_stop_r_egrisi bölümünde n 95 ve kar_selalesi net_r -0.0421",
               oneri="iki düğmeyi birlikte dene", parametreler=knobs)
    o.update(ek)
    return o


def test_C1_parametre_onerisi_kuyruga_nous_eval_damgasiyla_girer(sandbox_state):
    """Köprü. Kuyruğa girmek ONAY DEĞİL ölçüm sırasıdır ve kaynak damgası kimin önerdiğini söyler —
    damgasız bir satır, bir hafta sonra "bunu kim istedi?" sorusunu cevaplayamaz."""
    _tohumla(sandbox_state)
    o = _param_oneri({_KNOB_A: 2.0, _KNOB_B: 12})
    r = nous_eval.koprule([o])
    assert r["n_parametre"] == 1 and len(r["kuyruga_giren"]) == 1, r
    rows = store.read_jsonl("composite_queue.jsonl")
    assert len(rows) == 1 and rows[0]["source"] == "nous_eval" and rows[0]["status"] == "pending"
    assert rows[0]["n_knobs"] == 2 and o["kuyruk"] == "evet" and o["kuyruk_id"] == rows[0]["id"]
    assert ledgers.validate_row("composite_queue.jsonl", rows[0]) == []


def test_C2_AYRI_BUTCE_ACILMAZ_tasan_oneri_GORUNUR_bicimde_devreder(sandbox_state):
    """H4'ün bütçesi bir EMNİYETTİR: her ölçüm bir denemedir ve aşınma defterine/DSR paydasına N
    olarak girer. `nous_eval` kendine ayrı bütçe açsaydı, "sınırsız otomatik yoklama deflasyonu
    şişirir" emniyeti ikinci bir kapıdan delinirdi. Taşan öneri SESSİZCE kaybolmaz: devreder."""
    _tohumla(sandbox_state)
    butce = hermes_composite.WEEKLY_PROBE_BUDGET
    oneriler = [_param_oneri({_KNOB_A: 2.0 + 0.1 * i, _KNOB_B: 10 + i},
                             alan=f"alan{i}") for i in range(butce + 2)]
    r = nous_eval.koprule(oneriler)
    assert len(r["kuyruga_giren"]) == butce, f"bütçe tavanı aşıldı: {r}"
    assert len(r["devreden"]) == 2, "taşan öneriler devretmedi"
    assert len(store.read_jsonl("composite_queue.jsonl")) == butce
    devreden = [o for o in oneriler if o.get("kuyruk") == "devredildi"]
    assert len(devreden) == 2
    assert "devred" in " ".join(devreden[0]["kuyruk_neden"]).lower(), "devir nedeni yazılmamış"
    assert r["haftalik_butce"] == butce


def test_C3_bekleyen_satirlar_butceyi_ONCE_talep_eder(sandbox_state):
    """Kuyrukta bekleyen satırlar bu haftanın yoklamalarını zaten sözlüdür; üstüne yenisini eklemek
    kuyruğu şişirir, ölçüm hızını ARTIRMAZ (`skill_revisions` çöplük dersinin tersi)."""
    _tohumla(sandbox_state)
    for i in range(hermes_composite.WEEKLY_PROBE_BUDGET):
        hermes_composite.enqueue({_KNOB_A: 2.0, _KNOB_B: 10 + i},
                                 source="hermes")
    r = nous_eval.koprule([_param_oneri({_KNOB_A: 2.1, _KNOB_B: 20})])
    assert r["slot"] == 0 and r["kuyruga_giren"] == [] and len(r["devreden"]) == 1


def test_C4_sekil_disi_demet_kuyruga_girmez_ama_RAPORDA_kalir(sandbox_state):
    """Fikrin kendisi bilgidir (H3'ün kuruluş gerekçesi): şekil denetiminden geçmeyen öneri
    DÜŞÜRÜLMEZ, yalnız kuyruk yolu kapanır ve nedeni yazılır. Bileşik olmak, bir düğmeyi bounds
    dışına çıkarma ruhsatı değildir."""
    _tohumla(sandbox_state)
    disi = _param_oneri({_KNOB_A: 99.0, _KNOB_B: 12}, alan="a1")
    tek = _param_oneri({_KNOB_B: 12}, alan="a2")
    yok = _param_oneri({"boyle.bir.dugme.yok": 1.0, _KNOB_B: 12}, alan="a3")
    r = nous_eval.koprule([disi, tek, yok])
    assert r["kuyruga_giren"] == [] and len(r["sekil_disi"]) == 3
    assert store.read_jsonl("composite_queue.jsonl") == []
    for o in (disi, tek, yok):
        assert o["kuyruk"] == "hayir" and o["kuyruk_neden"], "kuyruk yolu sessizce kapandı"
    assert any("sınır dışı" in x for x in disi["kuyruk_neden"])
    assert any("tek düğme" in x for x in tek["kuyruk_neden"])
    assert any("bounds" in x for x in yok["kuyruk_neden"])


def test_C5_kuru_kosum_kuyruga_YAZMAZ(sandbox_state):
    """⑥ ilk koşusunun ve Rol 1 denetiminin ihtiyacı: "ne olurdu" görünsün, hiçbir ölçüm sırası
    tüketilmesin."""
    _tohumla(sandbox_state)
    r = nous_eval.koprule([_param_oneri({_KNOB_A: 2.0, _KNOB_B: 12})], yaz=False)
    assert len(r["kuyruga_giren"]) == 1 and r["yazildi"] is False
    assert store.read_jsonl("composite_queue.jsonl") == []


# =================================================================================================
# ④ KATMAN D — ANAYASAL KORUMA (YAPISAL, TESTLE ÇİVİLİ)
# =================================================================================================
def test_D1_cekirdek_listesi_ADLANDIRILMIS_SABIT(sandbox_state):
    """"Anayasal çekirdek nous'a KAPALI" cümlesi, çekirdeğin NE OLDUĞU yazılı olmadıkça uygulanamaz
    bir temenniydi. Liste tek yerde durur ve kapı yasasının yaşadığı dosyaları İÇERMEK zorundadır."""
    assert isinstance(nous_eval.CORE_FILES, tuple) and isinstance(nous_eval.CORE_CONCEPTS, tuple)
    for d in ("guard.py", "probgate.py", "validation.py", "goal.yaml"):
        assert d in nous_eval.CORE_FILES, f"çekirdek dosya listesinde {d} YOK"
    for c in ("guard", "protected", "veto", "autonomy_level", "one_variable_only"):
        assert c in nous_eval.CORE_CONCEPTS, f"çekirdek kavram listesinde {c} YOK"
    # gerçek dosyalar olmalı — silinen bir dosyanın adı listede kalırsa koruma boşa döner
    for d in nous_eval.CORE_FILES:
        assert (SRC / d).exists() or (pathlib.Path("state") / d).exists(), \
            f"çekirdek listesinde var olmayan dosya: {d}"


def test_D2_modelin_parametre_etiketi_sekli_EZEMEZ(sandbox_state):
    """En kritik çivi. `sekil` alanı MODELİN etiketidir; model çekirdek hakkındaki bir öneriyi
    "parametre" diye etiketlerse kuyruğa sızardı — yani hâkim kendi yasasını, üstüne yanlış bir
    etiket koyarak yazardı. Şekil KODDA yeniden türetilir ve etiket EZİLİR."""
    _tohumla(sandbox_state)
    kurnaz = _param_oneri({_KNOB_A: 2.0, _KNOB_B: 12},
                          oneri="guard'daki sert veto eşiğini gevşet")
    sekil, isaretler = nous_eval.sekil_sinifla(kurnaz)
    assert sekil == "cekirdek_hakkinda", "model etiketi şekli ezdi — ANAYASA DELİNDİ"
    assert "guard" in isaretler and "veto" in isaretler
    # KÖPRÜ DE ŞEKLİ YENİDEN TÜRETİR: `koprule` dışarıdan da çağrılabilir ve o hâlde `sekil` alanı
    # hâlâ modelin etiketidir. Süzgeç o alana güvenirse sayaç yalan söyler (ilk koşuda tam bu oldu:
    # `_kuyruga_yaz` ihlali yakalayıp alarm bastı ama `n_parametre` 1 yazmıştı).
    r = nous_eval.koprule([kurnaz])
    assert r["n_parametre"] == 0 and r["kuyruga_giren"] == []
    assert kurnaz["sekil"] == "cekirdek_hakkinda", "köprü şekli düzeltmedi"
    assert store.read_jsonl("composite_queue.jsonl") == [], "çekirdek öneri kuyruğa girdi"


def test_D3_kuyruga_yazma_denemesi_SESSIZ_DUSMEZ_ALARM_olur(sandbox_state):
    """Sessiz ret, sınıflandırma bir gün bozulduğunda ihlalin HİÇ görünmemesi demekti — ve
    görünmeyen bir anayasa ihlali, olmayan bir anayasadır. İstisna + AUTHORITY_CHANGE alarmı."""
    _tohumla(sandbox_state)
    cekirdek = _param_oneri({_KNOB_A: 2.0, _KNOB_B: 12},
                            alan="guard kapı yasası")
    with pytest.raises(nous_eval.CekirdekIhlali):
        nous_eval._kuyruga_yaz(cekirdek)
    assert store.read_jsonl("composite_queue.jsonl") == [], "ihlal denemesi kuyruğa satır yazdı"
    alarmlar = [e for e in store.read_jsonl("events.jsonl")
                if e.get("alarm") == obs.ALARM_AUTHORITY]
    assert alarmlar, "çekirdek ihlali denemesi ALARM üretmedi"
    assert "ÇEKİRDEK" in str(alarmlar[-1].get("message") or "")
    assert obs.ALARM_AUTHORITY in obs.NOTIFY_TOKENS, "alarm bildirim listesinde değil"


def test_D4_kuyruga_TEK_yazma_yolu_var_AST(sandbox_state):
    """YAPISAL çivi. "Çekirdek öneri kuyruğa yazılamaz" bir davranış kuralı değil YAPISAL bir olgu
    olmalı: kuyruğa giden BAŞKA bir yol bulunmamalı. İkinci bir `enqueue` çağrısı belirdiği gün bu
    test düşer — ve düşmesi gerekir, çünkü o çağrı korumanın etrafından dolaşır."""
    tree = ast.parse((SRC / "nous_eval.py").read_text())
    cagrilar = []
    for fn in ast.walk(tree):
        if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for n in ast.walk(fn):
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) \
                    and n.func.attr == "enqueue":
                cagrilar.append(fn.name)
    assert cagrilar == ["_kuyruga_yaz"], \
        f"kuyruğa yazan tek fonksiyon `_kuyruga_yaz` olmalı; bulunan: {cagrilar}"
    # ve o fonksiyonun İLK işi şekil denetimi olmalı (guard'dan SONRA gelen bir denetim, denetim değildir)
    fn = next(n for n in ast.walk(tree)
              if isinstance(n, ast.FunctionDef) and n.name == "_kuyruga_yaz")
    govde = [n for n in fn.body if not isinstance(n, ast.Expr)]     # docstring atlanır
    assert isinstance(govde[0], ast.Assign) and "sekil_sinifla" in ast.dump(govde[0]), \
        "_kuyruga_yaz'ın ilk işi şekil sınıflandırması DEĞİL"
    assert any(isinstance(n, ast.Raise) for n in ast.walk(fn)), \
        "_kuyruga_yaz ihlalde istisna FIRLATMIYOR (sessiz ret)"


def test_D5_uctan_uca_cekirdek_oneri_defterde_var_kuyrukta_YOK(sandbox_state, monkeypatch):
    """Katman D'nin sözü iki yönlüdür: nous çekirdek HAKKINDA öneri YAZABİLİR (kör nokta oradadır)
    ama değişiklik TETİKLEYEMEZ. Yani defterde görünmeli, kuyrukta görünmemeli."""
    _tohumla(sandbox_state)
    cekirdek = _oneri(sekil="cekirdek_hakkinda", alan="veto_istatistigi",
                      gozlem="veto_istatistigi bölümünde n_plan 390 ve leading_sector 217 kez "
                             "yumuşak veto verdi — guard eşiği kararı fiilen tek başına belirliyor",
                      oneri="leading_sector vetosunun eşiğini yeniden düşün")
    monkeypatch.setattr(hermes, "chain_text", lambda *a, **k: {
        "text": _cevap([cekirdek]), "beyin": "nous", "model": "test-model", "neden": {}})
    out = nous_eval.haftalik_degerlendirme(telemetri=_tel())
    rows = store.read_jsonl(nous_eval.PROPOSALS_FILE)
    assert len(rows) == 1 and rows[0]["sekil"] == "cekirdek_hakkinda"
    assert rows[0]["cekirdek_isaretleri"], "çekirdek işaretleri kaydedilmemiş"
    assert store.read_jsonl("composite_queue.jsonl") == []
    assert out["kosu"]["n_kuyruk"] == 0


# =================================================================================================
# ⑤ TÜKETİCİLER (YASA 6) + DEFTER SÖZLEŞMESİ + GERİ BESLEME
# =================================================================================================
def test_E1_defter_sozlesmeli_ve_GERCEK_satir_sozlesmeye_uyar(sandbox_state, monkeypatch):
    """`trades.jsonl`ın `setup`/`score` dersi: alanları YAZARDAN doğrula, fixture'dan değil. Testin
    kendi ürettiği bir satır değil, üreticinin GERÇEKTEN yazdığı satır sözleşmeye uymalı."""
    _tohumla(sandbox_state)
    c = ledgers.CONTRACTS.get("improvement_proposals.jsonl")
    assert c is not None, "defter ledgers sözleşmesinde YOK"
    assert c.writers == ("nous_eval.py",)
    for alan in ("ts", "id", "hafta", "gozlem", "sekil", "kanit_atifi", "onerilen_olcum"):
        assert alan in c.required, f"sözleşmede zorunlu olmayan kritik alan: {alan}"
    monkeypatch.setattr(hermes, "chain_text", lambda *a, **k: {
        "text": _cevap([_oneri()]), "beyin": "nous", "model": "m", "neden": {}})
    nous_eval.haftalik_degerlendirme(telemetri=_tel())
    rows = store.read_jsonl("improvement_proposals.jsonl")
    assert len(rows) == 1
    assert ledgers.validate_row("improvement_proposals.jsonl", rows[0]) == [], \
        f"üreticinin GERÇEK satırı sözleşmeyi ihlal ediyor: {rows[0]}"
    assert ledgers.validate_live("improvement_proposals.jsonl")["ok"] is True


def test_E2_yazar_beyani_statik_taramayla_ORTUSUR(sandbox_state):
    """Beyan edilmemiş bir yazar belirdiği gün sözleşme yalancı olur (2026-07-21'in kök nedeni)."""
    yazarlar = ledgers.declared_writers()
    assert yazarlar.get("improvement_proposals.jsonl") == {"nous_eval.py"}, \
        f"statik tarama beyanla ayrışıyor: {yazarlar.get('improvement_proposals.jsonl')}"


def test_E3_hafta_damgasi_H4_BUTCE_ANAHTARIYLA_ayni(sandbox_state, monkeypatch):
    """İki damga biçimi olsaydı yılbaşı haftasında bütçe İKİ KEZ dolardı ya da hiç dolmazdı."""
    _tohumla(sandbox_state)
    assert analytics._week_stamp("2026-07-30") == hermes_composite.week_key("2026-07-30")
    assert hermes_composite.week_key("2026-07-30") == "2026-W31"
    monkeypatch.setattr(hermes, "chain_text", lambda *a, **k: {
        "text": _cevap([_oneri()]), "beyin": "nous", "model": "m", "neden": {}})
    nous_eval.haftalik_degerlendirme(telemetri=_tel())
    row = store.read_jsonl("improvement_proposals.jsonl")[0]
    assert row["hafta"] == hermes_composite.week_key()


def test_E4_pano_okuyucusu_dusurulen_oneri_SAYISINI_tasir(sandbox_state, monkeypatch):
    """YASA 6 + kalite kapısının görünürlüğü. "4 öneri üretti" ile "9 üretti, 5'i kanıt-atıfsız
    düştü" aynı görünmemelidir; ikincisi beynin karnesi hakkında çok daha fazla şey söyler."""
    _tohumla(sandbox_state)
    bos = analytics.improvement_proposals_status()
    assert bos["n"] == 0 and "DEFTER BOŞ" in bos["durum"], "boş defter sahte bir dolu gösteriyor"
    kotu = [_oneri(gozlem=f"genel izlenim {i}") for i in range(5)]
    monkeypatch.setattr(hermes, "chain_text", lambda *a, **k: {
        "text": _cevap([_oneri()] + kotu), "beyin": "nous", "model": "m", "neden": {}})
    nous_eval.haftalik_degerlendirme(telemetri=_tel())
    d = analytics.improvement_proposals_status()
    assert d["durum"] == "dolu" and d["n_son_hafta"] == 1
    assert d["n_uretilen"] == 6 and d["n_dusen"] == 5
    assert d["dusme_nedenleri"] == {"kanit_atifsiz": 5}
    assert d["beyin"] == "nous" and d["sekil_dagilimi"] == {"tasarim": 1}
    assert "UYGULANMAZ" in d["rol"]


def test_E5_pano_karti_ve_api_alani_BAGLI(sandbox_state):
    """YASA 6: üretilen kanıtın tüketicisi olmalı. Kart `ml.improvement_proposals` okumazsa alan
    servis edilir ve kimse görmez (bu deponun en sık hatası)."""
    api_src = (SRC / "api.py").read_text()
    assert '"improvement_proposals": an.improvement_proposals_status()' in api_src
    js = (SRC / "web" / "app.js").read_text()
    assert "ml.improvement_proposals" in js, "pano kartı alanı okumuyor"
    assert "${sNous}" in js, "kart Operasyon sayfasının render listesinde YOK"
    for parca in ("KALİTE KAPISI", "DEVREDEN", "Sistem önerileri"):
        assert parca in js, f"kartta eksik: {parca}"


def test_E6_ozet_CLI_kalite_kapisi_sayilarini_basar(sandbox_state, monkeypatch):
    """Rol 1 haftalık denetimi. Boş defterde SAHTE bir özet basmaz."""
    _tohumla(sandbox_state)
    assert "DEFTER BOŞ" in nous_eval.ozet_metni()
    monkeypatch.setattr(hermes, "chain_text", lambda *a, **k: {
        "text": _cevap([_oneri(), _oneri(gozlem="hiçbir şeye atıf yok")]),
        "beyin": "nous", "model": "m", "neden": {}})
    nous_eval.haftalik_degerlendirme(telemetri=_tel())
    m = nous_eval.ozet_metni()
    assert "KALİTE KAPISI" in m and "düşen=1" in m
    assert "kar_selalesi" in m and "atıf" in m and "kuyruk" in m


def test_E7_onceki_onerilerin_AKIBETI_sonraki_prompta_geri_beslenir(sandbox_state, monkeypatch):
    """H1 deseninin mekanizma-düzeyi ikizi: "geçen hafta şunu önerdin, ölçüldü ve tutmadı" bilgisi
    olmadan beyin her hafta aynı öneriyi yeniden üretir (H2'nin ölçtüğü "15 gündür aynı 14 düğme"
    hastalığının mekanizma sürümü). Akıbet CANLI okunur — deftere retro damga YAZILMAZ."""
    _tohumla(sandbox_state)
    # geçen haftanın önerisi: kuyruğa girdi ve ÖLÇÜLDÜ
    monkeypatch.setattr(hermes, "chain_text", lambda *a, **k: {
        "text": _cevap([_param_oneri({_KNOB_A: 2.0, _KNOB_B: 12})]),
        "beyin": "nous", "model": "m", "neden": {}})
    nous_eval.haftalik_degerlendirme(telemetri=_tel(), hafta="2026-W30")
    satir = store.read_jsonl(nous_eval.PROPOSALS_FILE)[0]
    assert satir["kuyruk"] == "evet" and satir["hafta"] == "2026-W30"
    assert "akibet" not in satir, "deftere retro AKIBET damgası yazılmış"
    hermes_composite.mark(satir["kuyruk_id"], "measured", result={"passes": False, "oos": 0.09})
    ak = nous_eval.onceki_akibet(hafta="2026-W31")
    assert ak["durum"] == "dolu" and ak["n"] == 1
    assert "ÖLÇÜLDÜ" in ak["kalemler"][0]["akibet"] and "passes" in ak["kalemler"][0]["akibet"]
    # ve akıbet PROMPT'a girer
    p = nous_eval._prompt(_tel(), ak)
    assert "AKIBETİ" in p and "ÖLÇÜLDÜ" in p
    # ilk koşuda UYDURMA DERS YOK
    store.write_jsonl(nous_eval.PROPOSALS_FILE, [])
    assert nous_eval.onceki_akibet()["durum"] == "gecmis_yok"


def test_E8_akibet_cekirdek_ve_devir_hallerini_AYIRIR(sandbox_state):
    """Üç farklı "kuyrukta değil" hâli üç ayrı şey söyler: anayasal rapor, dolmuş bütçe, şekil reddi.
    Tek cümleye katlanırsa beyin "önerim yok sayıldı" diye okur ve aynı öneriyi tekrar üretir."""
    for satir, beklenen in (
            ({"sekil": "cekirdek_hakkinda"}, "YALNIZ RAPOR"),
            ({"sekil": "parametre", "kuyruk": "devredildi"}, "DEVREDİLDİ"),
            ({"sekil": "parametre", "kuyruk": "hayir", "kuyruk_neden": ["sınır dışı"]}, "KAPALI"),
            ({"sekil": "tasarim", "kuyruk": "hayir"}, "YALNIZ RAPOR"),
            ({"sekil": "parametre", "kuyruk": "evet", "kuyruk_id": "C00009"}, "BULUNAMADI")):
        assert beklenen in nous_eval._akibet(satir, {}), f"{satir} → yanlış akıbet"
    assert "SIRADA" in nous_eval._akibet({"sekil": "parametre", "kuyruk": "evet",
                                          "kuyruk_id": "C00001"},
                                         {"C00001": {"id": "C00001", "status": "pending"}})


# =================================================================================================
# ⑥ SYSTEM STATİK KALIR + KADANS
# =================================================================================================
def test_F1_SYSTEM_statik_kalir_gorev_TASK_ta_durur_AST():
    """`cache_control: ephemeral` yalnız BAYT BAYT aynı metin için isabet eder. Katman B'nin görev
    metni SYSTEM'e girse önbellek her turda ıskalar ve maliyet sessizce katlanır."""
    tree = ast.parse((SRC / "hermes.py").read_text())
    atama = [n for n in ast.walk(tree) if isinstance(n, ast.Assign)
             and any(getattr(t, "id", None) == "SYSTEM" for t in n.targets)]
    assert len(atama) == 1 and isinstance(atama[0].value, ast.Constant)
    for ad in ("improvement_proposals", "cekirdek_hakkinda", "onerilen_olcum", "sekil"):
        assert ad not in atama[0].value.value, f"{ad} SYSTEM'e sızmış"
    # görev şablonu nous_eval'de ve o da DÜZ bir sabit (f-string olsaydı her tur değişebilirdi)
    ne = ast.parse((SRC / "nous_eval.py").read_text())
    task = [n for n in ne.body if isinstance(n, ast.Assign)
            and any(getattr(t, "id", None) == "TASK" for t in n.targets)]
    assert len(task) == 1 and isinstance(task[0].value, ast.Constant)
    assert "cekirdek_hakkinda" in nous_eval.TASK and "parametreler" in nous_eval.TASK


def test_F2_chain_text_SYSTEM_i_degistirmeden_gonderir():
    """Zincirin üç ayağı da SYSTEM'i AYNEN gönderir; görev `prompt` argümanından girer. Bir ayak
    SYSTEM'i yeniden yazarsa o ayak farklı bir sözleşmeyle konuşmaya başlar."""
    src = (SRC / "hermes.py").read_text()
    tree = ast.parse(src)
    fn = next(n for n in ast.walk(tree)
              if isinstance(n, ast.FunctionDef) and n.name == "chain_text")
    # DOKÜMANTASYON DEĞİL KOD OKUNUR: docstring "SYSTEM'E DOKUNULMAZ" diyor ve düz metin taraması
    # onu ihlal sanıyordu. Denetim `SYSTEM` adının bir İFADE olarak kullanılıp kullanılmadığıdır.
    assert not any(isinstance(n, ast.Name) and n.id == "SYSTEM" for n in ast.walk(fn)), \
        "chain_text SYSTEM'i kendisi gönderiyor — taşıma gövdeleriyle iki kopya olur"
    dump = ast.dump(fn)
    for ayak in ("_claude_text", "_nous_text", "_gemini_call", "_agent_call"):
        assert ayak in dump, f"zincirin {ayak} ayağı chain_text'te yok"
    # üç taşıma gövdesi de SYSTEM'i sabit olarak gönderir
    for ad in ("_claude_text", "_nous_text", "_gemini_call"):
        g = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == ad)
        assert "SYSTEM" in ast.dump(g), f"{ad} SYSTEM göndermiyor"


def test_F3_haftalik_kadansa_ASILI_sweep_orphan_deseni():
    """`rollback.sweep_orphan_hypotheses` dersi: kod olarak var, SÜREÇ olarak yok. Bu katman bir
    kadansa asılmazsa aynı hataya düşer — repo genelinde tek çağıranı testler olurdu."""
    src = (SRC / "scheduler.py").read_text()
    assert "nous_eval" in src and "haftalik_degerlendirme()" in src
    assert "nous_eval_week" in src, "haftalık damga yok — her poll'de yeniden koşardı"
    tree = ast.parse(src)
    fn = next(n for n in ast.walk(tree)
              if isinstance(n, ast.FunctionDef) and n.name == "advance_once")
    dump = ast.dump(fn)
    assert "haftalik_degerlendirme" in dump, "çağrı haftalık kadansın içinde değil"
    # arıza SESSİZ kalmaz (YASA 4)
    assert "nous_eval_failed" in src


def test_F4_katman_D_sozu_ROADMAP_ve_kodda_AYNI():
    """Belge ile kod ayrışırsa denetçi yanlış şeyi denetler."""
    rm = pathlib.Path("ROADMAP.md").read_text()
    assert "NOUS SİSTEM-DEĞERLENDİRME KATMANI" in rm
    assert "Katman D" in rm and "çekirdek" in rm
    doc = nous_eval.__doc__ or ""
    assert "YAPISAL olarak imkânsız" in doc or "YAPISAL olarak imkânsızdır" in doc
    assert "AYRI BÜTÇE AÇILMAZ" in doc or "AYRI BÜTÇE AÇILMAZ" in nous_eval.koprule.__doc__
