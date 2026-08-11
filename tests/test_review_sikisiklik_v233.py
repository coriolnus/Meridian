"""test_review_sikisiklik_v233.py — CANDIDATE_REVIEW SIKIŞIKLIĞI: sessiz spin biter, defter dürüst kalır.

CANLI VAKA (2026-07-31 → 08-08, A1 journal'ından ölçüldü): scheduler 5 dakikada bir `review_backlog`
çağırıyor, en yeni seans (08-07) incelenemiyor ve `candidate_review_backlog requested:[2026-08-07]
reviewed:[] already:2026-07-27` günde ~276 kez basılıyordu. Başarısızlığın kendisi OLAYSIZDI:
`review_candidates` içindeki `if text is None: return None` yolu, `_agent_call`ın üç ayrı arızasını
(zincir cevapsız / 900 sn havuz soğuması / RPD reddi) `candidate_review*` ailesinden tek satır
basmadan yutuyordu — aile 08-02 16:48'den beri sessizdi. Üstelik spin günlük 150'lik ajan RPD
bütçesinin TAMAMINI yiyordu (75 deneme × 2 model; 19:21'de `agent_budget_exhausted`, gece yarısına
dek açlık) — öneri yolu dahil her ajan tüketicisi kotasız kalıyordu.

BU DOSYA v233 SÖZLEŞMESİNİ ÇİVİLER:
  1. SESSİZ YOL KALMAZ — `review_candidates`ın HER kayıtsız dönüşü adı+nedeniyle olay basar
     (`candidate_review_skipped` yeni yollar için; parse ailesi mevcut `candidate_review_empty_parse`
     ile konuşmaya devam eder) ve sıkışıklık defterine işlenir.
  2. N GERÇEK DENEMEDE `gecersiz` — görüş üretilemeyen seans kalıcı işaretlenir (tarih+neden+deneme),
     backlog SONRAKİ görüşsüz seansa İLERLER; sahte review asla yazılmaz.
  3. EN-YENİ-TARİH DONMASI BİTER — gecersiz işaretli en yeni tarih, arkasındaki seansların
     incelenmesini artık BLOKLAMAZ.
  4. BAŞARI YOLU AYNEN — review yazılır, işaretçi ilerler, backlog olayı `reviewed` dolu basar.
  5. SPAM KADANSI — başarısız tarih üstel geri-çekilme penceresinde YENİDEN DENENMEZ; bekleyen
     turlar olaysızdır (makullük bekçisine gürültü gitmez), süreç doğurma hızı saatte 1'e iner.

Ağ/alt süreç yok: `_agent_call` saplı, `_hermes_bin` sahte; fikstürlerde sır yok.
"""
import json
import time

import pytest

from meridian import hermes, store

GUN = "2026-08-07"          # canlı vakanın donuk tarihi
ESKI = "2026-08-06"         # arkasında bekleyen görüşsüz seans


@pytest.fixture
def hazir(sandbox_state, monkeypatch):
    """Sandbox state + iki seanslı plan defteri + saplı ajan kapısı (v168 fikstürünün kardeşi)."""
    monkeypatch.setattr(hermes.secrets, "get", lambda k: None)
    monkeypatch.setattr(hermes, "_hermes_bin", lambda: "/sahte/hermes")
    monkeypatch.setattr(hermes, "_skill_preload", lambda *a, **k: ())
    for d, t in ((ESKI, "BBB"), (GUN, "VLO")):
        store.append_jsonl("trade_plans.jsonl",
                           {"date": d, "ticker": t, "setup": "breakout_vcp", "gate_verdict": "GO",
                            "entry_trigger": 10, "stop": 9, "profit_target": 12, "size_r": 1,
                            "score": 70})
    return sandbox_state


def _olaylar(event):
    return [r for r in store.read_jsonl("events.jsonl") if r.get("event") == event]


def _ajan_yok(monkeypatch, sayac=None):
    """Çağrı HİÇ yapılamadı sınıfı: None döner, RPD sayacına dokunmaz (soğuma/bütçe reddi imzası)."""
    def _cagri(*a, **k):
        if sayac is not None:
            sayac.append(1)
        return None
    monkeypatch.setattr(hermes, "_agent_call", _cagri)


def _ajan_bos(monkeypatch, sayac=None):
    """Zincir KOŞTU ama cevapsız sınıfı: gerçek koşumun ölçülmüş imzası RPD düşümüdür — sahtesi de
    aynı izi bırakır (üretim sınıflandırması `_agent_gun_sayaci` farkına bakar, tahmine değil)."""
    def _cagri(*a, **k):
        if sayac is not None:
            sayac.append(1)
        st = store.read_json(hermes.AGENT_BUDGET_FILE, {}) or {}
        st["day"] = int(st.get("day") or 0) + 1
        store.write_json(hermes.AGENT_BUDGET_FILE, st)
        return None
    monkeypatch.setattr(hermes, "_agent_call", _cagri)


def _ajan_basarili(monkeypatch, ticker):
    monkeypatch.setattr(hermes, "_agent_call", lambda *a, **k: json.dumps(
        {"reviews": [{"ticker": ticker, "opinion": "destekle", "note": "taban sıkı, hacim kuru"}]},
        ensure_ascii=False))


def _deneme_tohumla(day, n, n_llm, sonraki_epoch=0.0):
    """Deftere hazır deneme kaydı koy — eşik/pencere testleri saatlerce koşmasın."""
    def _f(doc):
        defter = hermes._review_backlog_defteri(doc)
        defter["denemeler"][day] = {"n": n, "n_llm": n_llm, "ilk_ts": "2026-08-08T00:00:00+00:00",
                                    "son_asama": "agent_bos", "son_ts": "2026-08-08T00:00:00+00:00",
                                    "bekleme_s": hermes._review_bekleme_s(n),
                                    "sonraki_epoch": sonraki_epoch}
        doc["backlog"] = defter
        return True
    store.update_json("candidate_review.json", _f, {})


# ---------------------------------------------------------------------------------------------
# 1) SESSİZ YOL KALMADI — her kayıtsız dönüş adı+nedeniyle konuşur
# ---------------------------------------------------------------------------------------------
def test_s1a_ikili_yoklugu_olayli(hazir, monkeypatch):
    monkeypatch.setattr(hermes, "_hermes_bin", lambda: None)
    assert hermes.review_candidates(GUN) is None
    (e,) = _olaylar("candidate_review_skipped")
    assert e["asama"] == "ikili_yok" and e["date"] == GUN and e["level"] == "warn"
    assert len(e["detail"]) >= 20 and "CLI" in e["detail"]
    defter = hermes._review_backlog_defteri()
    assert defter["denemeler"][GUN]["n"] == 1
    assert defter["denemeler"][GUN]["n_llm"] == 0        # modele hiç sorulmadı — eşiğe sayılmaz


def test_s1b_plansiz_tarih_olayli(hazir, monkeypatch):
    _ajan_yok(monkeypatch)
    assert hermes.review_candidates("2099-01-01") is None
    (e,) = _olaylar("candidate_review_skipped")
    assert e["asama"] == "plan_yok" and e["date"] == "2099-01-01" and e["level"] == "warn"
    assert "plan" in e["detail"]


def test_s1c_cagri_yapilamadi_olayli_ve_tarihe_fatura_edilmez(hazir, monkeypatch):
    """Soğuma/bütçe reddi: RPD sayacı kımıldamaz → `agent_cagri_yok`. Tarih incelenemez İLAN
    EDİLEMEZ (n_llm sayılmaz) — modele hiç sorulmamış seansı mahkûm etmek uydurma hüküm olurdu."""
    _ajan_yok(monkeypatch)
    assert hermes.review_candidates(GUN) is None
    (e,) = _olaylar("candidate_review_skipped")
    assert e["asama"] == "agent_cagri_yok" and e["level"] == "info"
    assert "soguma_s" in e and "butce_gun" in e          # olay kendi başına teşhis taşır
    rec = hermes._review_backlog_defteri()["denemeler"][GUN]
    assert rec["n"] == 1 and rec["n_llm"] == 0


def test_s1d_zincir_kostu_cevapsiz_olayli_ve_esige_sayilir(hazir, monkeypatch):
    _ajan_bos(monkeypatch)
    assert hermes.review_candidates(GUN) is None
    (e,) = _olaylar("candidate_review_skipped")
    assert e["asama"] == "agent_bos"
    rec = hermes._review_backlog_defteri()["denemeler"][GUN]
    assert rec["n"] == 1 and rec["n_llm"] == 1           # gerçek deneme — gecersiz eşiğine sayılır


def test_s1e_parse_yollari_da_deftere_islenir(hazir, monkeypatch):
    """json_parse/filtre aileleri olaylarını (v168) korur; v233 onlara defter kaydı ekler —
    'model konuştu ama anlaşılamadı' da gerçek denemedir, eşiğe sayılır."""
    monkeypatch.setattr(hermes, "_agent_call", lambda *a, **k: "düz metin — JSON değil")
    assert hermes.review_candidates(GUN) is None
    assert len(_olaylar("candidate_review_empty_parse")) == 1        # aile konuşmaya devam ediyor
    assert _olaylar("candidate_review_skipped") == []                # çift olay yok
    assert hermes._review_backlog_defteri()["denemeler"][GUN]["n_llm"] == 1


def test_s1f_kaynak_kilidi_her_kayitsiz_donus_olay_makinesinden_gecer():
    """Yapısal çivi: `review_candidates`ta 5 kayıtsız dönüş var ve TOPLAMI olay/defter makinesine
    bağlı (3 × `_review_atla` + 2 parse yolu × `_review_deneme_isle`). Olaysız bir 6. `return None`
    eklenirse bu sayılar ayrışır ve kilit düşer — v168 h6'nın v233 genişlemesi."""
    import inspect
    src = inspect.getsource(hermes.review_candidates)
    assert src.count("return None") == 5
    assert src.count("_review_atla(") == 3
    assert src.count("_review_deneme_isle(") == 2
    assert src.count("_warn_review_empty(") == 2         # v168 sözleşmesi bozulmadı


# ---------------------------------------------------------------------------------------------
# 2) N GERÇEK DENEMEDE gecersiz + İLERLEME
# ---------------------------------------------------------------------------------------------
def test_s2_esikte_kalici_isaret_ve_sonraki_tarihe_ilerleme(hazir, monkeypatch):
    _deneme_tohumla(GUN, n=hermes.REVIEW_GECERSIZ_N - 1, n_llm=hermes.REVIEW_GECERSIZ_N - 1)
    _ajan_bos(monkeypatch)
    out = hermes.review_backlog()
    assert out["requested"] == [GUN] and out["reviewed"] == []
    assert out["gecersiz_yeni"] == [GUN]
    isaret = hermes._review_backlog_defteri()["gecersiz"][GUN]
    assert isaret["neden"] == "agent_bos" and isaret["deneme"] == hermes.REVIEW_GECERSIZ_N
    assert isaret["ts"] and isaret["deneme_llm"] == hermes.REVIEW_GECERSIZ_N
    (e,) = _olaylar("candidate_review_gecersiz")
    assert e["date"] == GUN and "sahte review" in e["detail"]
    # İLERLEME: bir sonraki tur artık ESKİ seansı hedefler — donma bitti.
    sayac = []
    _ajan_bos(monkeypatch, sayac)
    out2 = hermes.review_backlog()
    assert out2["requested"] == [ESKI] and len(sayac) == 1


def test_s2b_cagri_yapilamayan_firtina_tarihi_mahkum_edemez(hazir, monkeypatch):
    """UYDURMA YASAĞI çivisi: 50 ardışık 'çağrı yapılamadı' (soğuma/bütçe) birikse bile n_llm=0
    kaldıkça tarih gecersiz İLAN EDİLMEZ — işaret yalnız modele gerçekten sorulup görüş
    alınamadığında düşer."""
    _deneme_tohumla(GUN, n=50, n_llm=0)
    _ajan_yok(monkeypatch)
    hermes.review_backlog()
    defter = hermes._review_backlog_defteri()
    assert GUN not in defter["gecersiz"]
    assert defter["denemeler"][GUN]["n"] == 51 and defter["denemeler"][GUN]["n_llm"] == 0


# ---------------------------------------------------------------------------------------------
# 3) EN-YENİ-TARİH DONMASI BİTTİ (görev (b)'nin kanıtı)
# ---------------------------------------------------------------------------------------------
def test_s3_gecersiz_en_yeni_tarih_arkadaki_seansi_bloklamaz(hazir, monkeypatch):
    _deneme_tohumla(GUN, n=hermes.REVIEW_GECERSIZ_N - 1, n_llm=hermes.REVIEW_GECERSIZ_N - 1)
    _ajan_bos(monkeypatch)
    hermes.review_backlog()                              # GUN → gecersiz
    _ajan_basarili(monkeypatch, "BBB")
    out = hermes.review_backlog()
    assert out["reviewed"] == [ESKI]
    kayit = store.read_json("candidate_review.json", {})
    assert kayit["date"] == ESKI and kayit["reviews"][0]["ticker"] == "BBB"
    # SAHTE-REVIEW YOK: gecersiz seansın görüşü uydurulmadı; boşluk işaretli ve dürüst.
    assert GUN in kayit["backlog"]["gecersiz"] and kayit["backlog"]["tamam"].keys() == {ESKI}
    ev = _olaylar("candidate_review_backlog")
    assert ev[-1]["reviewed"] == [ESKI]
    # KARARLILIK: başarıdan sonraki tur olaysız ve işsizdir (gecersiz atlanır, tamam'da durulur).
    n_olay = len(_olaylar("candidate_review_backlog"))
    out3 = hermes.review_backlog()
    assert out3["requested"] == [] and out3["detail"]
    assert len(_olaylar("candidate_review_backlog")) == n_olay


# ---------------------------------------------------------------------------------------------
# 4) BAŞARI YOLU REGRESYONU — davranış aynen
# ---------------------------------------------------------------------------------------------
def test_s4_basari_yolu_yazar_isaretci_ilerler_olay_dolu_basar(hazir, monkeypatch):
    _deneme_tohumla(GUN, n=3, n_llm=2)                   # önceki başarısızlıklar başarıyı kirletmez
    _ajan_basarili(monkeypatch, "VLO")
    out = hermes.review_backlog()
    assert out["reviewed"] == [GUN] and out["requested"] == [GUN]
    kayit = store.read_json("candidate_review.json", {})
    assert kayit["date"] == GUN and "kapı" in kayit["note"]          # danışma sınırı kayıtta (v168 h4)
    assert kayit["reviews"][0]["opinion"] == "destekle"
    assert kayit["backlog"]["tamam"].keys() == {GUN}
    assert kayit["backlog"]["denemeler"] == {}                       # sayaç başarıda temizlendi
    (e,) = _olaylar("candidate_review_backlog")
    assert e["reviewed"] == [GUN] and e["gecersiz_yeni"] == []
    assert _olaylar("candidate_review_skipped") == []                # başarı sessizdir — gürültü yok


# ---------------------------------------------------------------------------------------------
# 5) SPAM KADANSI — geri-çekilme penceresi ve olay ekonomisi
# ---------------------------------------------------------------------------------------------
def test_s5a_basarisiz_deneme_pencere_koyar_pencerede_ne_cagri_ne_olay(hazir, monkeypatch):
    sayac = []
    _ajan_bos(monkeypatch, sayac)
    out1 = hermes.review_backlog()
    assert out1["requested"] == [GUN] and len(sayac) == 1
    assert len(_olaylar("candidate_review_backlog")) == 1
    rec = hermes._review_backlog_defteri()["denemeler"][GUN]
    assert rec["bekleme_s"] == hermes.REVIEW_BEKLEME_TABAN_S
    assert rec["sonraki_epoch"] > time.time()
    # Pencere içindeki tur: ajan ÇAĞRILMAZ, backlog olayı BASILMAZ (eski hâl: 5 dk'da bir ikisi de).
    out2 = hermes.review_backlog()
    assert out2["requested"] == [] and out2["bekleyen"] == [GUN]
    assert len(sayac) == 1
    assert len(_olaylar("candidate_review_backlog")) == 1
    # Pencere beklemede eskiye SIÇRANMAZ: canlı hedef hâlâ en yeni görüşsüz seanstır.
    assert ESKI not in out2["bekleyen"]


def test_s5b_bekleme_merdiveni_ustel_ve_tavanli():
    """taban·2^(n-1), tavan 3600: n=1 mevcut 5 dk kadansına eş (ilk tekrar cezasız), n≥5 saatte 1 —
    donuk bir tarih için günlük alt-süreç maliyeti 150'den ≤24'e iner (canlı ölçümün tersine)."""
    assert hermes._review_bekleme_s(1) == 300
    assert hermes._review_bekleme_s(2) == 600
    assert hermes._review_bekleme_s(4) == 2400
    assert hermes._review_bekleme_s(5) == 3600
    assert hermes._review_bekleme_s(40) == 3600          # tavan taşmaz (2^39 patlaması yok)


def test_s5c_guncel_durumda_tur_olaysiz(hazir, monkeypatch):
    """En yeni seans zaten görüşlüyse (canlının ~%95 hâli) tur SESSİZ geçer — eski davranış günde
    ~276 `requested:[]` satırı basıyordu; artık olay yalnız iş yapılınca var."""
    _ajan_basarili(monkeypatch, "VLO")
    hermes.review_backlog()
    n0 = len(_olaylar("candidate_review_backlog"))
    for _ in range(3):
        out = hermes.review_backlog()
        assert out["requested"] == []
    assert len(_olaylar("candidate_review_backlog")) == n0


def test_s5d_pencere_disi_eski_bosluklar_bu_telafinin_isi_degil(hazir, monkeypatch):
    """Tarama ufku `REVIEW_BACKLOG_PENCERE` seans (onarım geçidi emsali): en yeni 5 seansın hepsi
    gecersiz işaretliyse tur işsiz ve olaysızdır — daha eski boşluklar kanıt dolgusunun
    (backfill_opinions) alanıdır, backlog tarih avına çıkmaz."""
    gunler = [f"2026-07-{g:02d}" for g in range(20, 20 + hermes.REVIEW_BACKLOG_PENCERE + 2)]
    store.write_jsonl("trade_plans.jsonl",
                      [{"date": d, "ticker": "AAA", "setup": "breakout_vcp", "gate_verdict": "GO",
                        "entry_trigger": 10, "stop": 9, "profit_target": 12, "size_r": 1,
                        "score": 70} for d in gunler])
    def _f(doc):
        defter = hermes._review_backlog_defteri(doc)
        for d in sorted(gunler, reverse=True)[:hermes.REVIEW_BACKLOG_PENCERE]:
            defter["gecersiz"][d] = {"neden": "agent_bos", "deneme": 12, "ts": "t"}
        doc["backlog"] = defter
        return True
    store.update_json("candidate_review.json", _f, {})
    sayac = []
    _ajan_bos(monkeypatch, sayac)
    out = hermes.review_backlog()
    assert out["requested"] == [] and len(sayac) == 0
    assert len(out["gecersiz"]) == hermes.REVIEW_BACKLOG_PENCERE
    assert _olaylar("candidate_review_backlog") == []
