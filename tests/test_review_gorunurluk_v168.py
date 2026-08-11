"""test_review_gorunurluk_v168.py — ADAY İKİNCİ GÖRÜŞÜNÜN İKİ SESSİZ ÖLÜM NOKTASI GÖRÜNÜR OLUR.

CANLI VAKA (2026-08-02): Gemini DOLU cevap veriyordu, `state/candidate_review.json` güncellenmiyordu
ve defterde bunu söyleyen TEK BİR SATIR yoktu. `review_candidates` iki yerden kayıtsız dönüyor:
  (a) JSON ayrıştırma — ikinci deneme (`_unwrap_strings` onarımı) da düşerse istisna, asenkron
      çağıranın (`review_candidates_async._bg`) genel `candidate_review_failed` uyarısına gidiyor,
      HAM METİN kayboluyordu: hangi cevabın ayrışmadığı bir daha asla bilinemezdi;
  (b) şekil/enum süzgeci — dolu bir `reviews` listesi süzgeçten sıfırla çıkınca `if not reviews:
      return None` OLAYSIZ dönüyordu (hermes.py ~2109): "model konuştu ama biz anlamadık" arızası
      "model hiç konuşmadı"dan AYIRT EDİLEMİYORDU.

Bu dosya GÖRÜNÜRLÜĞÜ kilitler, davranışı değil: kayıtsız-dönüşün HER yolu tek `candidate_review_
empty_parse` uyarısı basar (asama ile ayrışır), başarı yolu SESSİZ kalır (olay yoksa kayıt vardır),
ve `_unwrap_strings` onarımı hâlâ CEVAP KURTARIR — onarımın kurtardığı cevap olay basmaz.
Ağ/alt süreç yok: `_agent_call` saplı, `_hermes_bin` sahte; fikstürlerde sır yok.
"""
import json

import pytest

from meridian import hermes, store

OLAY = "candidate_review_empty_parse"
GUN = "2026-07-18"


@pytest.fixture
def hazir(sandbox_state, monkeypatch):
    """Sandbox state + planlı bir seans + saplı ajan kapısı. `config.STATE` tmp_path'te (sandbox_state),
    yani hiçbir yazım operatörün canlı defterine düşemez."""
    monkeypatch.setattr(hermes.secrets, "get", lambda k: None)          # gerçek ~/.env karışmasın
    monkeypatch.setattr(hermes, "_hermes_bin", lambda: "/sahte/hermes")  # ikili "kurulu" görünsün
    monkeypatch.setattr(hermes, "_skill_preload", lambda *a, **k: ())    # ön-yükleme bu testin konusu değil
    store.append_jsonl("trade_plans.jsonl",
                       {"date": GUN, "ticker": "AAA", "setup": "breakout_vcp", "gate_verdict": "GO",
                        "entry_trigger": 10, "stop": 9, "profit_target": 12, "size_r": 1, "score": 70})
    return sandbox_state


def _sap(monkeypatch, text):
    """Ajan cevabını sabitle — ağ/alt süreç yok."""
    monkeypatch.setattr(hermes, "_agent_call", lambda *a, **k: text)


def _olaylar(event=OLAY):
    return [r for r in store.read_jsonl("events.jsonl") if r.get("event") == event]


def _tek_olay():
    ev = _olaylar()
    assert len(ev) == 1, f"kayıtsız-dönüş TEK olay basmalı, {len(ev)} basıldı: {ev}"
    e = ev[0]
    assert e["level"] == "warn"                                   # bu bir arıza, bilgi değil
    for alan in ("asama", "text_len", "extract_len", "parse_ok", "on_filtre_n",
                 "son_filtre_n", "reddedilen_gorusler", "ham_ilk", "detail"):
        assert alan in e, f"olay alanı eksik: {alan} ({sorted(e)})"
    assert "\n" not in e["ham_ilk"], "ham_ilk tek satıra düzleştirilmeli (defter satırı bölünmez)"
    assert len(e["ham_ilk"]) <= 260                                # 220 karakter + repr kaçışları
    assert len(e["detail"]) >= 20 and isinstance(e["detail"], str)
    assert len(e["reddedilen_gorusler"]) <= 5
    assert all(len(v) <= 40 for v in e["reddedilen_gorusler"])
    return e


def test_h1_hermes_review_duz_metin_cevabi_json_parse_olayi_basar(hazir, monkeypatch):
    """(1) Model JSON yerine düz metin bastı: iki ayrıştırma denemesi de düşer → asama=json_parse,
    parse_ok=False, ham metnin başı olayda. Davranış AYNI: None + dosya yazılmaz (istisna DA sızmaz)."""
    cevap = "Adaylara baktım: AAA taban sıkı görünüyor, ama JSON basmayacağım — düz metin yazıyorum."
    _sap(monkeypatch, cevap)
    assert hermes.review_candidates(GUN) is None
    # GÖRÜŞ kaydı yok (davranış korunur). v233 inceltmesi: dosyada artık sıkışıklık defteri
    # (`backlog` sayaçları) durabilir — yasak olan görüş İÇERİĞİ uydurmaktır, deneme saymak değil.
    kayit = store.read_json("candidate_review.json", {}) or {}
    assert kayit.get("date") is None and not kayit.get("reviews")
    e = _tek_olay()
    assert e["asama"] == "json_parse"
    assert e["parse_ok"] is False
    assert e["on_filtre_n"] == 0 and e["son_filtre_n"] == 0
    assert e["text_len"] == len(cevap) and e["extract_len"] > 0
    assert "AAA taban sıkı" in e["ham_ilk"]                          # HAM METİN ARTIK KAYBOLMUYOR
    assert "JSON" in e["detail"] and "JSONDecodeError" in e["detail"]  # istisna adı hükümde


def test_h2_hermes_review_enum_disi_gorus_filtre_olayi_basar(hazir, monkeypatch):
    """(2) Geçerli JSON ama görüşler enum dışı ("support"/"oppose"): ayrıştırma başarılı, süzgeç
    sıfır bırakıyor → asama=filtre; REDDEDİLEN DEĞERLER olayda (canlı vakanın aradığı tam bilgi)."""
    _sap(monkeypatch, json.dumps({"reviews": [
        {"ticker": "AAA", "opinion": "support", "note": "İngilizce enum — süzgeç eler"},
        {"ticker": "BBB", "opinion": "oppose", "note": "aynı sınıf"},
    ], "reasoning": "model şemayı İngilizce doldurdu"}, ensure_ascii=False))
    assert hermes.review_candidates(GUN) is None
    kayit = store.read_json("candidate_review.json", {}) or {}
    assert kayit.get("date") is None and not kayit.get("reviews")    # görüş kaydı yok (v233: bkz. h1)
    e = _tek_olay()
    assert e["asama"] == "filtre"
    assert e["parse_ok"] is True
    assert e["on_filtre_n"] == 2 and e["son_filtre_n"] == 0
    assert e["reddedilen_gorusler"] == ["support", "oppose"]         # NEDEN düştüğü okunuyor
    assert "sıfır görüş" in e["detail"]


def test_h3_hermes_review_bos_reviews_listesi_de_olay_basar(hazir, monkeypatch):
    """(3) Şema doğru ama liste BOŞ: model "görüş yok" dedi. Bu da kayıtsız dönüştür ve
    "cevap gelmedi"den ayırt edilebilir olmalı (parse_ok=True, on_filtre_n=0)."""
    _sap(monkeypatch, json.dumps({"reviews": []}))
    assert hermes.review_candidates(GUN) is None
    e = _tek_olay()
    assert e["asama"] == "filtre" and e["parse_ok"] is True
    assert e["on_filtre_n"] == 0 and e["son_filtre_n"] == 0
    assert e["reddedilen_gorusler"] == []


def test_h4_hermes_review_gecerli_gorusler_sessizdir_ve_yazilir(hazir, monkeypatch):
    """(4) BAŞARI YOLU DEĞİŞMEDİ: geçerli Türkçe görüşler → OLAY YOK + sandbox state'e yazılır.
    (Olay yalnız kayıtsız-dönüşte basılır; yoksa "uyarı gürültüsü" teşhis değerini yer.)"""
    _sap(monkeypatch, json.dumps({"reviews": [
        {"ticker": "AAA", "opinion": "destekle", "note": "vcp tabanı sıkı"},
        {"ticker": "BBB", "opinion": "çekimser", "note": "hacim zayıf"},
    ], }, ensure_ascii=False))
    res = hermes.review_candidates(GUN)
    assert res and len(res["reviews"]) == 2
    assert _olaylar() == [], "başarı yolu SESSİZ olmalı"
    kayit = store.read_json("candidate_review.json", {})
    assert kayit["date"] == GUN and "kapı" in kayit["note"]           # danışma sınırı kayıtta
    assert store.read_jsonl("trade_plans.jsonl")[-1]["gate_verdict"] == "GO"   # kapıya dokunulmadı


def test_h5_hermes_review_sarmalanmis_cevap_onarilir_ve_olay_basmaz(hazir, monkeypatch):
    """REGRESYON KAPISI: `_unwrap_strings` onarımı (CLI'nın ~80 sütun satır-sarmalaması) hâlâ CEVAP
    KURTARIYOR — ilk `json.loads` düşer, ikincisi kurtarır, olay BASILMAZ. Görünürlük eklerken
    onarım kolunu kısaltmak, canlıda kurtarılan cevapları sessizce çöpe atardı."""
    _sap(monkeypatch, '{"reviews":[{"ticker":"AAA","opinion":"karşı","note":"taban gevşek ve\n'
                      '            hacim yok"}]}')
    res = hermes.review_candidates(GUN)
    assert res and res["reviews"][0]["opinion"] == "karşı"
    assert _olaylar() == [], "onarımla kurtarılan cevap arıza değildir"


def test_h6_hermes_review_olay_adi_ve_iki_yolu_kaynakta_kilitli():
    """Sözleşme kaynakta: kayıtsız-dönüşün İKİ yolu da tek olay adına bağlı ve `asama` ayrıştırıcı.
    (Yeni bir 'return None' kolu olaysız eklenirse bu kilit gevşer — o yüzden sayı burada sabit.)"""
    import inspect
    src = inspect.getsource(hermes.review_candidates)
    assert src.count("_warn_review_empty(") == 2                     # json_parse + filtre
    assert '"json_parse"' in src and '"filtre"' in src
    assert OLAY in inspect.getsource(hermes._warn_review_empty)
    # YASA-4: onarım kolunun sessiz-yutma gerekçesi ARTIK doğru olanı anlatır (bilgi kaybolmuyor).
    assert "sessiz-yutma" in src and OLAY in src.split("except json.JSONDecodeError:")[1][:400]
