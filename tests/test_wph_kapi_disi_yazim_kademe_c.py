"""WP-H / H9 Kademe C — KAPI-DIŞI YAZIMLARIN KAPIYA TAŞINMASI: ÖĞRENME + VERİ/DURUM KATMANI (2026-08-09).

Kademe A/B (test_wph_kapi_disi_yazim.py) auth/memory/config/run'ı taşımıştı. Bu dosya H9 raporunun
"KALAN" listesini ölçer — SEKİZ yazım, BEŞ dosya:
  * skill_evolve.draft_revision   — SKILL.md.v2-draft düz open(w) → store.write_text. ATOMİKLİK ŞART:
    taslak apply_revision'da os.replace ile CANLI SKILL.md olur; yarım/sıfır-baytlık taslak = bozuk skill.
  * sprint_run._write_live_status  — elle mkstemp (fsync/flock/sanitize YOK) → store.write_json.
  * earnings.refresh (×2)          — elle mkstemp → store.write_text("earnings.csv"); kilit PAYLAŞIMLI.
  * adapters.data._write_bars      — HOT PATH: elle mkstemp → store.write_text, DOSYA-BAŞINA kilit.
  * hermes _write_env/backup/config.yaml — elle mkstemp/json.dump → store gate (env .env 0600 KORUNUR).

Ölçülen sınıflar: (1) KAPIYA GİRİŞ (ad + gate), (2) ROUND-TRIP (biçim birebir), (3) ATOMİKLİK
(os.replace düşerse hedef DOKUNULMAZ + tmp SIZMAZ), (4) HOT-PATH GRANÜLERLİĞİ (_write_bars dosya-başına
kilit → farklı ticker SERİLEŞMEZ), (5) SANITIZE (sprint status np.float → sonlu/None).

SAHİPLİK: taşınan sekiz yazımın hiçbiri SAHİPLİK-MANİFESTİNE (test_na_revision_v53) girmez —
write_text İZLENMEZ, sprint_status/backup ise write_json ama adları SABİT DEĞİL (değişken) → AST
taraması yakalamaz. Bu bilinçlidir: manifest STATE DEFTERLERİNİ (sabit-adlı json/jsonl) izler; bu
sekiz artefakt ya JSON-olmayan metin (CSV/MD/YAML/.env) ya da canlı/dış/dinamik-yollu dosyalardır.
"""
from __future__ import annotations

import ast
import inspect
import json
import textwrap
from pathlib import Path

import pandas as pd
import pytest

from meridian import config, earnings, hermes, skill_evolve, sprint_run, store
from meridian.adapters import data


# ---------------- yardımcılar (Kademe B deseniyle aynı) ----------------
def _capture(monkeypatch, attr: str) -> dict:
    """`store.<attr>`ı sar, (name, payload)ı yakala — ASIL yazımı YAP (round-trip/atomiklik korunsun)."""
    real = getattr(store, attr)
    seen: dict = {}

    def cap(name, payload):
        seen["name"] = name
        seen["payload"] = payload
        return real(name, payload)

    monkeypatch.setattr(store, attr, cap)
    return seen


def _patlat_replace(monkeypatch):
    """Kapının ATOMİK son adımını (os.replace) düşür — yarım-yazım simülasyonu (tüm gate yazarları
    tek `store._atomic_write` boğazından geçer, o da store.py'nin içe aktardığı stdlib `os.replace`i çağırır)."""
    def patlat(src, dst):
        raise OSError("simüle: replace düştü")
    monkeypatch.setattr(store.os, "replace", patlat)


def _calls(fn) -> set:
    """Bir fonksiyonun gövdesindeki Call düğümlerinin adları (attr veya isim) — docstring metnini
    yakalamaz, yalnız GERÇEK çağrıları (mezar-taşı testleri buna dayanır)."""
    tree = ast.parse(textwrap.dedent(inspect.getsource(fn)))
    out = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Call):
            if isinstance(n.func, ast.Attribute):
                out.add(n.func.attr)
            elif isinstance(n.func, ast.Name):
                out.add(n.func.id)
    return out


def _bars(dates, close):
    return pd.DataFrame({"date": pd.to_datetime(dates), "open": close,
                         "high": [c * 1.01 for c in close], "low": [c * 0.99 for c in close],
                         "close": close, "volume": [1_000_000] * len(dates)})


_D = ["2026-07-01", "2026-07-02", "2026-07-06", "2026-07-07"]


# =================================================================================================
# 1) adapters.data._write_bars — HOT PATH: elle mkstemp → store.write_text, DOSYA-BAŞINA kilit
# =================================================================================================
def test_write_bars_kapiya_goreli_ad_ve_roundtrip(sandbox_state, monkeypatch):
    """CSV `store.write_text`ten STATE'e GÖRELİ adla (`bars/<ticker>.csv`) geçer; diskte round-trip."""
    seen = _capture(monkeypatch, "write_text")
    data._write_bars(_bars(_D, [10.0, 11.0, 12.0, 13.0]), data._cache_path("KO"))
    assert seen["name"] == "bars/ko.csv"                       # göreli → kilit paylaşımlı, global DEĞİL
    disk = pd.read_csv(sandbox_state / "bars" / "ko.csv")
    assert len(disk) == 4 and float(disk["close"].iloc[-1]) == 13.0


def test_write_bars_DOSYA_BASINA_kilit_hot_path_serilesmez(sandbox_state):
    """HOT-PATH KARARININ KANITI: farklı ticker → FARKLI kilit nesnesi → havuz işçileri birbirini
    BEKLEMEZ; aynı ticker → AYNI kilit (kayıp-güncelleme yalnız aynı dosyada serileşir)."""
    assert store.file_lock("bars/ko.csv") is not store.file_lock("bars/msft.csv")
    assert store.file_lock("bars/ko.csv") is store.file_lock("bars/ko.csv")


def test_write_bars_atomik_replace_duserse_eski_kalir(sandbox_state, monkeypatch):
    """os.replace düşerse eski bar defteri AYNEN durur (eşzamanlı okuyucu yarım CSV görmez) + tmp temiz."""
    cp = data._cache_path("KO")
    data._write_bars(_bars(_D, [1.0, 2.0, 3.0, 4.0]), cp)
    before = cp.read_bytes()
    _patlat_replace(monkeypatch)
    with pytest.raises(OSError):
        data._write_bars(_bars(_D, [9.0, 9.0, 9.0, 9.0]), cp)
    assert cp.read_bytes() == before
    assert not list(cp.parent.glob("*.tmp"))


def test_write_bars_ham_mkstemp_gitti():
    """MEZAR TAŞI: _write_bars artık elle mkstemp/os.replace kurmaz; to_csv KALIR (kapıya string verir)."""
    calls = _calls(data._write_bars)
    assert "mkstemp" not in calls and "replace" not in calls, "_write_bars hâlâ elle atomik yazıyor"
    assert "write_text" in calls, "_write_bars kapıya (store.write_text) taşınmadı"
    assert "to_csv" in calls


# =================================================================================================
# 2) sprint_run._write_live_status — elle mkstemp (fsync/flock/sanitize YOK) → store.write_json
# =================================================================================================
def test_sprint_status_STATE_ici_goreli_ad_roundtrip(sandbox_state, monkeypatch):
    status_path = sandbox_state / "sprint_status.json"
    monkeypatch.setenv("MERIDIAN_SPRINT_STATUS", str(status_path))
    seen = _capture(monkeypatch, "write_json")
    sprint_run._write_live_status({"sid": "s1", "phase": "baseline", "progress": 3})
    assert seen["name"] == "sprint_status.json"               # STATE İÇİ → göreli
    assert json.loads(status_path.read_text())["phase"] == "baseline"


def test_sprint_status_STATE_disi_mutlak_ad(sandbox_state, monkeypatch, tmp_path):
    """Çocuk sandbox STATE'inde koşar ama CANLI status yolu STATE DIŞIdır → mutlak ad (relative_to
    fallback); ebeveynle süreçler-arası kilit zaten SAĞLANAMAZ (ayrı STATE), damga güvenliği yapısal."""
    disari = tmp_path / "canli" / "sprint_status.json"
    monkeypatch.setenv("MERIDIAN_SPRINT_STATUS", str(disari))
    seen = _capture(monkeypatch, "write_json")
    sprint_run._write_live_status({"sid": "s2", "phase": "search"})
    assert seen["name"] == str(disari)                        # STATE DIŞI → mutlak
    assert json.loads(disari.read_text())["phase"] == "search"    # kapı parent'ı kendi kurdu


def test_sprint_status_sanitize_np_float_eklendi(sandbox_state, monkeypatch):
    """Çıplak json.dump np.float64'te patlardı; kapı SANITIZE eder (sonlu→değer, NaN→None)."""
    np = pytest.importorskip("numpy")
    status_path = sandbox_state / "sprint_status.json"
    monkeypatch.setenv("MERIDIAN_SPRINT_STATUS", str(status_path))
    sprint_run._write_live_status({"sid": "s3", "incumbent_oos": np.float64(1.5),
                                   "best": {"score": np.float64("nan")}})
    doc = json.loads(status_path.read_text())
    assert doc["incumbent_oos"] == 1.5 and doc["best"]["score"] is None


def test_sprint_status_atomik_replace_duserse_yutulur(sandbox_state, monkeypatch):
    """os.replace düşerse OSError YUTULUR (status salt gösterim), eski dosya durur, tmp sızmaz."""
    status_path = sandbox_state / "sprint_status.json"
    monkeypatch.setenv("MERIDIAN_SPRINT_STATUS", str(status_path))
    sprint_run._write_live_status({"sid": "s4", "phase": "baseline"})
    before = status_path.read_bytes()
    _patlat_replace(monkeypatch)
    sprint_run._write_live_status({"sid": "s4", "phase": "candidate"})   # YUTULUR — istisna yok
    assert status_path.read_bytes() == before
    assert not list(sandbox_state.glob("*.tmp"))


def test_sprint_status_ham_mkstemp_gitti():
    calls = _calls(sprint_run._write_live_status)
    assert "mkstemp" not in calls, "_write_live_status hâlâ elle mkstemp kuruyor"
    assert "write_json" in calls, "_write_live_status kapıya (store.write_json) taşınmadı"


# =================================================================================================
# 3) earnings.refresh (×2) — elle mkstemp → store.write_text("earnings.csv"), kilit PAYLAŞIMLI
# =================================================================================================
def test_earnings_iki_yol_da_kapidan_ayni_ada_yazar():
    """İki tazeleme yolu da AYNI dosyayı (STATE'e göreli "earnings.csv") kapıdan yazar; elle mkstemp yok."""
    for fn in (earnings.refresh, earnings.refresh_from_fmp):
        src = inspect.getsource(fn)
        assert 'store.write_text("earnings.csv"' in src, f"{fn.__name__} kapıya taşınmadı"
        assert "mkstemp" not in _calls(fn), f"{fn.__name__} hâlâ elle mkstemp kuruyor"


def test_earnings_paylasilan_kilit_nesnesi(sandbox_state):
    """STATE'e GÖRELİ ad → refresh ile refresh_from_fmp AYNI kilit nesnesine düşer (mutlak ad ayrı
    kilide = kilit YOK olurdu)."""
    assert store.file_lock("earnings.csv") is store.file_lock("earnings.csv")


def test_earnings_gate_bicimi_load_ile_roundtrip(sandbox_state):
    """Kapının yazdığı biçim (`ticker,date,time` başlık + satırlar) tam _load()'ın okuduğu biçimdir."""
    store.write_text("earnings.csv", "ticker,date,time\nAAA,2026-08-15,bmo\nBBB,2026-08-16,\n")
    earnings.clear_cache()
    known = earnings._load()
    assert "2026-08-15" in known.get("AAA", []) and "2026-08-16" in known.get("BBB", [])


# =================================================================================================
# 4) skill_evolve.draft_revision — SKILL.md.v2-draft düz open(w) → store.write_text (ATOMİK ŞART)
# =================================================================================================
def test_skill_draft_kapidan_mutlak_ad_ve_roundtrip(sandbox_state, monkeypatch, tmp_path):
    skdir = tmp_path / "skills" / "vcp-screener"
    skdir.mkdir(parents=True)
    (skdir / "SKILL.md").write_text("---\nname: vcp-screener\n---\norijinal gövde")
    monkeypatch.setattr(skill_evolve, "_repo_skill_dir", lambda n: str(skdir))
    body = "REVISED " + "x" * 300                              # ≥200 karakter (draft kapısı)
    monkeypatch.setattr(hermes, "_agent_call",
                        lambda *a, **k: f"<REVISED>\n{body}\n</REVISED>\nRATIONALE: test gerekçesi")
    from meridian import analytics
    monkeypatch.setattr(analytics, "skill_attribution",
                        lambda: {"skills": [{"skill": "vcp-screener", "n": 20, "avg_r": -0.3,
                                             "n_cf": 5, "cf_avg_r": -0.1}]})
    seen = _capture(monkeypatch, "write_text")
    rec = skill_evolve.draft_revision("vcp-screener")
    assert rec is not None and rec["status"] == "draft"
    assert seen["name"] == str(skdir / "SKILL.md.v2-draft")   # skills/ STATE dışı → mutlak
    assert seen["payload"] == body
    assert (skdir / "SKILL.md.v2-draft").read_text() == body  # round-trip: apply os.replace'i bunu taşır


def test_skill_draft_ham_open_w_gitti():
    """MEZAR TAŞI: taslak yazımı store.write_text; düz open(...,'w') KALMADI (open yalnız OKUMA için)."""
    tree = ast.parse(textwrap.dedent(inspect.getsource(skill_evolve.draft_revision)))
    open_w = [n for n in ast.walk(tree) if isinstance(n, ast.Call)
              and isinstance(n.func, ast.Name) and n.func.id == "open"
              and any(isinstance(a, ast.Constant) and a.value == "w" for a in n.args)]
    assert not open_w, "draft hâlâ open(...,'w') ile yazıyor (KIRPMA sınıfı)"
    assert "write_text" in _calls(skill_evolve.draft_revision)


# =================================================================================================
# 5) hermes — env/backup/config.yaml
# =================================================================================================
def test_hermes_config_yaml_kapidan_mutlak_ad_roundtrip(sandbox_state, monkeypatch):
    """config_ensure_integrations: config.yaml `store.write_text`ten (mutlak ad) geçer + round-trip."""
    import yaml
    cfgpath = hermes.AGENT_CONFIG                             # conftest sandbox'ta tmp'ye çevirir
    Path(cfgpath).write_text(yaml.safe_dump({"model": {"default": "x"}}))
    monkeypatch.setattr(hermes, "_hermes_bin", lambda: "/fake/hermes")
    seen = _capture(monkeypatch, "write_text")
    res = hermes.config_ensure_integrations()
    assert res["ok"] is True and res["changed"]
    assert seen["name"] == cfgpath                            # ~/.hermes STATE dışı → mutlak
    disk = yaml.safe_load(Path(cfgpath).read_text())
    assert "meridian" in (disk.get("mcp_servers") or {})     # entegrasyon yazıldı + round-trip


def test_hermes_config_yaml_ham_mkstemp_gitti():
    calls = _calls(hermes.config_ensure_integrations)
    assert "mkstemp" not in calls, "config_ensure_integrations hâlâ elle mkstemp kuruyor"
    assert "write_text" in calls, "config.yaml kapıya taşınmadı"


def test_hermes_env_ve_backup_kapiya_tasindi_0600_korundu():
    """_write_env → store.write_text (+ açık os.chmod 0600 KALIR, sır sözleşmesi), model-backup →
    store.write_json; elle mkstemp / json.dump KALMADI. (~/.hermes/.env sandbox'lanamaz → mezar taşı.)"""
    calls = _calls(hermes.sync_local_agent_gemini)
    assert "write_text" in calls, "_write_env store.write_text'e taşınmadı"
    assert "write_json" in calls, "model-backup store.write_json'a taşınmadı"
    assert "mkstemp" not in calls, "sync_local_agent_gemini hâlâ elle mkstemp kuruyor"
    assert "dump" not in calls, "backup hâlâ json.dump ile yazıyor (atomik değil)"
    assert "chmod" in calls, ".env 0600 chmod'u düştü — store mkstemp-0600 TESADÜFİdir, devredilmez"
