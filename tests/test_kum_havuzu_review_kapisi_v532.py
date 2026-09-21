"""test_kum_havuzu_review_kapisi_v532.py — SPRINT KUM HAVUZUNDA LLM GÖRÜŞÜ BİLEREK KAPALI (TSK-212).

ÖLÇÜLMÜŞ VAKA (A1, 2026-09-21 22:22Z). `meridian-sprint@<sid>.service` HOME'u salt-okunur tutar
(`ProtectHome=read-only`, `ReadWritePaths=/opt/meridian`) ve birim şerhi bunu "sprint LLM ÇAĞIRMAZ"
diye gerekçelendiriyordu. DAVRANIŞ TERSİYDİ: `sprint_run` A fazında `loop.daily_cycle` koşturur, o
yol scheduler üzerinden `hermes.review_backlog` → `review_candidates` → `_agent_call(kind="review")`e
ulaşır. Kum havuzunda hermes CLI `~/.hermes/logs/agent.log` açamayıp `[Errno 30] Read-only file
system` ile `returncode=1` döndü; `review_candidates` bunu `agent_bos` sebebiyle raporladı.
Ölçüm: tek sprintte 21 dakikada 23 çağrı, 23'ü boş; 09-01..09-10 sprintlerinde 268/268 aynı imza,
başarılı çağrı 0. Her boş çağrı ~1,44 s + ~2,5 kr stderr + kum havuzunun RPD gün sayacından bir düşüm.
İlk görülme 2026-08-21.

KAYIP YOK, BEDEL VAR. Kum havuzunda sağlayıcı anahtarı da yoktur (v242 `agent_skills_sync_atlandi_
kum_havuzu` beyanının kardeşi) — yazma izni verilse bile görüş üretilmezdi. Yani kapının kapattığı
şey 0/268 görüştür; kapattığı bedel 268 boş alt süreçtir.

BU DOSYA v532 SÖZLEŞMESİNİ ÇİVİLER:
  T1 KAPI — kum havuzunda `review_candidates` `_agent_call`a HİÇ ulaşmaz; `_agent_model_sifirla` da
     çağrılmaz (kapı ondan önce). Dönüş None ama SESSİZ DEĞİL: `candidate_review_skipped` tam 1 kez,
     `asama="kum_havuzu_llm_kapali"`, `kum_havuzu=True`, seviye info (arıza değil, tasarım).
  T2 DEFTER — sebep `agent_bos`tan AYRIDIR: `n` artar ama `n_llm` ARTMAZ ve gün `gecersiz`
     işaretlenmez. LLM denemesi olmayan bir yolu "12 denemede görüş üretilemedi" diye mahkûm etmek
     uydurma hüküm olurdu (UYDURMA YASAĞI); `agent_bos` gerçek arıza sınıfı olarak yerinde kalır.
  T3 CANLI YOL DEĞİŞMEZ — kum havuzu dışında `agent_bos` sözleşmesi (v233) aynen sürer. Kapının
     yalnız kum havuzunda çalıştığının ölçüsü budur.
  T4 SIKI DÖNGÜ YOK — kum havuzu sebebi de geri-çekilme penceresine girer; ikinci tur bekler,
     ikinci olay basılmaz (v233'ün spam kadansı yeni sebebi de kapsar).
  T5 KAPI SIRASI — `_hermes_bin()` kontrolünden ÖNCE: ikilinin var/yok olması kum havuzunda
     anlamsız bir sorudur, cevabı da yanıltıcı (`ikili_yok` "kurulum/symlink onarımı gerekir" der).
  T6 BİRİM YÖNERGESİ — yol (b) (kum havuzuna HOME yazma izni + anahtar) REDDEDİLDİ; çözüm kapıdır,
     izin genişletmesi değil. `ReadWritePaths` tek satır ve `/opt/meridian`dır.

Ağ/alt süreç yok: `_agent_call` saplı, `_hermes_bin` sahte, `kum_havuzunda` monkeypatch'li;
fikstürlerde sır yok.
"""
from pathlib import Path

import pytest

from meridian import hermes, sprint, store

GUN = "2026-09-10"          # ölçüm penceresinin son sprint seansı
SEBEP = "kum_havuzu_llm_kapali"


@pytest.fixture
def hazir(sandbox_state, monkeypatch):
    """Sandbox state + tek seanslı plan defteri + saplı ajan kapısı (v233 fikstürünün kardeşi)."""
    monkeypatch.setattr(hermes.secrets, "get", lambda k: None)
    monkeypatch.setattr(hermes, "_hermes_bin", lambda: "/sahte/hermes")
    monkeypatch.setattr(hermes, "_skill_preload", lambda *a, **k: ())
    store.append_jsonl("trade_plans.jsonl",
                       {"date": GUN, "ticker": "VLO", "setup": "breakout_vcp", "gate_verdict": "GO",
                        "entry_trigger": 10, "stop": 9, "profit_target": 12, "size_r": 1,
                        "score": 70})
    return sandbox_state


def _olaylar(event):
    return [r for r in store.read_jsonl("events.jsonl") if r.get("event") == event]


def _kum_havuzu(monkeypatch, deger: bool):
    """`review_candidates` `meridian.sprint`i FONKSİYON İÇİNDE (tembel) import eder — sap modül
    nesnesine konur, çünkü tembel import her çağrıda sys.modules'tan taze niteliği okur."""
    monkeypatch.setattr(sprint, "kum_havuzunda", lambda: deger)


def _ajan_sayacli(monkeypatch, sayac):
    """Çağrılırsa iz bırakır — kapının ısırdığı şey tam olarak bu izin YOKLUĞUDUR."""
    def _cagri(*a, **k):
        sayac.append(1)
        return None
    monkeypatch.setattr(hermes, "_agent_call", _cagri)


def _ajan_bos(monkeypatch, sayac):
    """Zincir KOŞTU ama cevapsız sınıfı (v233 emsali): gerçek koşumun ölçülmüş imzası RPD
    düşümüdür — sahtesi de aynı izi bırakır, çünkü üretim sınıflandırması sayacın FARKINA bakar."""
    def _cagri(*a, **k):
        sayac.append(1)
        st = store.read_json(hermes.AGENT_BUDGET_FILE, {}) or {}
        st["day"] = int(st.get("day") or 0) + 1
        store.write_json(hermes.AGENT_BUDGET_FILE, st)
        return None
    monkeypatch.setattr(hermes, "_agent_call", _cagri)


# ---------------------------------------------------------------------------------------------
# T1) KAPI — ajan katmanına hiç girilmez, ama dönüş adıyla konuşur
# ---------------------------------------------------------------------------------------------
def test_t1_kum_havuzunda_kapi_doner_ve_ajan_katmanina_hic_girilmez(hazir, monkeypatch):
    _kum_havuzu(monkeypatch, True)
    sayac, sifirlama = [], []
    _ajan_sayacli(monkeypatch, sayac)
    monkeypatch.setattr(hermes, "_agent_model_sifirla", lambda: sifirlama.append(1))

    assert hermes.review_candidates() is None

    assert sayac == [], "kum havuzunda `_agent_call` koştu — kapı ısırmadı"
    assert sifirlama == [], "`_agent_model_sifirla` çağrıldı — kapı ondan SONRAYA kaymış"
    (e,) = _olaylar("candidate_review_skipped")
    assert e["asama"] == SEBEP and e["date"] == GUN
    assert e["kum_havuzu"] is True          # journal triyajı bu alanla tek satırda ayırır
    assert e["level"] == "info"             # tasarım gereği sessizlik ARIZA DEĞİLDİR
    assert len(e["detail"]) >= 20 and "TSK-212" in e["detail"]
    assert "0/268" in e["detail"], "olay kendi başına ölçümü taşımalı (neden kapalı)"
    # Kapı DANIŞMA katmanını kapatır; deterministik kapıya dokunmadığı olayda da yazılı.
    assert "deterministik" in e["detail"]


# ---------------------------------------------------------------------------------------------
# T2) DEFTER — sebep `agent_bos`tan ayrı sayılır; gün mahkûm edilmez
# ---------------------------------------------------------------------------------------------
def test_t2_defter_llm_denemesi_saymaz_ve_gun_gecersiz_olmaz(hazir, monkeypatch):
    _kum_havuzu(monkeypatch, True)
    _ajan_sayacli(monkeypatch, [])

    assert hermes.review_candidates() is None

    backlog = (store.read_json("candidate_review.json", {}) or {}).get("backlog") or {}
    rec = backlog["denemeler"][GUN]
    assert rec["n"] == 1                    # kayıtsız dönüş defterde görünür (v233 sözleşmesi)
    assert rec["n_llm"] == 0                # ama LLM'e hiç sorulmadı — eşiğe SAYILMAZ
    assert rec["son_asama"] == SEBEP
    assert GUN not in (backlog.get("gecersiz") or {})
    assert _olaylar("candidate_review_gecersiz") == []
    # TEK KAYNAK: sınıf ayrımı sabit kümenin KENDİSİNDE yaşar, testin kopyasında değil.
    assert SEBEP not in hermes._REVIEW_LLM_ASAMALARI
    assert "agent_bos" in hermes._REVIEW_LLM_ASAMALARI   # gerçek arıza sınıfı yerinde kaldı


# ---------------------------------------------------------------------------------------------
# T3) CANLI YOL — kapı yalnız kum havuzunda çalışır
# ---------------------------------------------------------------------------------------------
def test_t3_canli_yolda_agent_bos_sozlesmesi_aynen_surer(hazir, monkeypatch):
    _kum_havuzu(monkeypatch, False)
    sayac = []
    _ajan_bos(monkeypatch, sayac)

    assert hermes.review_candidates() is None

    assert len(sayac) == 1, "canlıda ajan çağrısı kapandı — kapı kum havuzunun dışına taştı"
    (e,) = _olaylar("candidate_review_skipped")
    assert e["asama"] == "agent_bos"
    assert "kum_havuzu" not in e            # varlık `in` ile ölçülür, `.get() is None` ile değil
    rec = hermes._review_backlog_defteri()["denemeler"][GUN]
    assert rec["n"] == 1 and rec["n_llm"] == 1          # gerçek deneme — eşiğe sayılır (v233)


# ---------------------------------------------------------------------------------------------
# T4) SIKI DÖNGÜ YOK — yeni sebep de geri-çekilme penceresine girer
# ---------------------------------------------------------------------------------------------
def test_t4_geri_cekilme_penceresi_kum_havuzu_sebebi_icin_de_isler(hazir, monkeypatch):
    _kum_havuzu(monkeypatch, True)
    sayac = []
    _ajan_sayacli(monkeypatch, sayac)

    out1 = hermes.review_backlog(max_sessions=1)
    assert out1["requested"] == [GUN] and out1["reviewed"] == []
    assert len(_olaylar("candidate_review_skipped")) == 1

    out2 = hermes.review_backlog(max_sessions=1)
    assert out2["requested"] == [] and out2["bekleyen"] == [GUN]
    assert len(_olaylar("candidate_review_skipped")) == 1, "pencere içinde ikinci olay basıldı"
    assert sayac == []


# ---------------------------------------------------------------------------------------------
# T5) KAPI SIRASI — `_hermes_bin` kontrolünden ÖNCE
# ---------------------------------------------------------------------------------------------
def test_t5_kapi_hermes_bin_kontrolunden_once_isler(hazir, monkeypatch):
    """İkili yoksa BİLE sebep kum havuzudur: kum havuzunda 'CLI kurulu mu' sorusu anlamsızdır ve
    `ikili_yok`un önerdiği onarım (kurulum/symlink) yanlış işi işaret ederdi."""
    monkeypatch.setattr(hermes, "_hermes_bin", lambda: None)
    _kum_havuzu(monkeypatch, True)
    _ajan_sayacli(monkeypatch, [])

    assert hermes.review_candidates() is None

    (e,) = _olaylar("candidate_review_skipped")
    assert e["asama"] == SEBEP, f"kapı `_hermes_bin`den sonraya kaymış (asama={e['asama']})"
    assert e["level"] == "info"             # `ikili_yok` warn basar — sınıf karışmamalı


# ---------------------------------------------------------------------------------------------
# T6) BİRİM YÖNERGESİ — yol (b) reddi tek kaynakta
# ---------------------------------------------------------------------------------------------
def test_t6_birim_readwritepaths_dar_kalir_ve_hermes_evi_acilmaz():
    """Çözüm KAPIDIR, izin genişletmesi değil: kum havuzuna HOME yazma izni + sağlayıcı anahtarı
    vermek, LLM kotasını antrenman replay'ine harcamak demektir — bu bir operatör kararıdır ve
    verilmemiştir. dagit [1c] kapısı yönergeleri kıyaslar; bu çivi aynı gerçeği repo tarafında tutar."""
    birim = Path(__file__).resolve().parents[1] / "deploy" / "oracle-a1" / "meridian-sprint@.service"
    satirlar = [s.strip() for s in birim.read_text(encoding="utf-8").splitlines()
                if s.startswith("ReadWritePaths=")]
    assert satirlar == ["ReadWritePaths=/opt/meridian"], f"yönerge kümesi değişmiş: {satirlar}"
    assert all(".hermes" not in s for s in satirlar)
    assert "ProtectHome=read-only" in birim.read_text(encoding="utf-8").splitlines()
