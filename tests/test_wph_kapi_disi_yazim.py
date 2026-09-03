"""WP-H / H9 Kademe B — KAPI-DIŞI YAZIMLARIN TEK KAPIYA TAŞINMASI (2026-08-09).

`test_wph_store_kapi.py` kapının KENDİSİNİ ölçer (write_text/write_json atomik+kilitli mi). Bu dosya
onun tamamlayıcısıdır: kapıyı ATLAYAN dört çağrı-noktasının artık kapıdan geçtiğini ölçer. Keşif
WP-HD'nin envanteri (docs/KESIF-WP-HD-2026-08-09.md, H9 tablosu) bunları adıyla sayıyordu:

  * auth._write   — SABİT tmp adı (`.json.tmp`): iki süreç aynı tmp'ye yazar → EN TEHLİKELİ tekil.
  * memory.py     — `lessons.md` düz `Path.write_text` (KIRPMA sınıfı).
  * run.py        — `history/scoreboard-*.json` arşivi düz `Path.write_text` (KIRPMA sınıfı).
  * config.dump_yaml — mkstemp+os.replace ama fsync YOK, flock YOK.

Dördü de artık `store.write_text`e taşındı. Ölçülen üç sınıf: (1) ROUND-TRIP — davranış/biçim
BİREBİR korunur (taşıma bir regresyon değil); (2) ATOMİKLİK — yazım ortasında (os.replace) düşerse
HEDEF dokunulmamış kalır, yarım içerik deftere HİÇ girmez; (3) KAPIYA GİRİŞ — yazım gerçekten
`store.write_text`ten (yani flock+fsync+benzersiz-tmp) geçer. Kapının süreçler-arası flock'u
`test_wph_store_kapi.py::test_flock_SURECLER_ARASI_gercekten_bekletir`de kanıtlıdır; dört çağıran da
AYNI `store.write_text`e indiği için o garantiyi devralır — burada her çağıranın kilidi KAPIDA
tuttuğu (derinlik>0) ayrıca ölçülür.

SAHİPLİK/YASA-6: taşınan artefaktların okuyucuları belgelidir — auth.json (auth._read),
lessons.md (`hermes._gate_anchor` reflection prompt + `skill_evolve` taslak üreticisi), strategy.yaml/history yaml'ları
(config.load_strategy + versioning + run._ancestor_from_history), scoreboard arşivi (kurtarma:
operatör; run.py'deki console satırı yolunu verir).
"""
from __future__ import annotations

import ast
import inspect
import json
import textwrap

import pytest
import yaml

from meridian import auth, config, memory, run, store


def _capture_write_text(monkeypatch):
    """`store.write_text`i saran ve (name, text)i yakalayan yardımcı — ASIL yazım YAPILIR
    (aksi halde auth._write'ın son `os.chmod`u olmayan dosyada patlardı)."""
    real = store.write_text
    seen: dict = {}

    def cap(name, text):
        seen["name"] = name
        seen["text"] = text
        return real(name, text)

    monkeypatch.setattr(store, "write_text", cap)
    return seen


def _patlat_replace(monkeypatch):
    """os.replace'i yazımın ATOMİK son adımında düşür — yarım-yazım simülasyonu."""
    def patlat(src, dst):
        raise OSError("simüle: replace düştü")
    monkeypatch.setattr(store.os, "replace", patlat)


def _tmp_artigi(state) -> list[str]:
    return [p.name for p in state.iterdir() if p.name.endswith(".tmp")]


# =================================================================================================
# 1) auth._write — EN TEHLİKELİ tekil (SABİT tmp adı). Regresyon + atomiklik + izin + kapı.
# =================================================================================================
def test_auth_write_roundtrip_regresyon(sandbox_state):
    """MANTIK DEĞİŞMEDİ: parola/oturum/anahtar-döndürme yaz→oku round-trip'i aynen tutar."""
    pw = "correct horse battery"          # ≥12 karakter (set_password yasası)
    assert auth.password_set() is False
    auth.set_password(pw)
    assert auth.password_set() is True
    assert auth.verify_password(pw) is True
    assert auth.verify_password("yanlis parola!") is False
    tok = auth.issue_session()
    assert auth.verify_session(tok) is True
    assert auth.verify_session("bozuk.token.xyz") is False
    # rotate_key AÇIK TÜM OTURUMLARI düşürür ama PAROLAYI korur (auth sözleşmesi)
    auth.rotate_key()
    assert auth.verify_session(tok) is False
    assert auth.verify_password(pw) is True


def test_auth_json_0600_izni(sandbox_state):
    """Parola hash'i + imza anahtarı 0600 kalmalı — bu auth'un KENDİ güvenlik sözleşmesi, store'a
    devredilmez (auth._write son satırındaki açık `os.chmod`)."""
    auth.set_password("correct horse battery")
    mode = (sandbox_state / "auth.json").stat().st_mode & 0o777
    assert mode == 0o600, f"auth.json izni {oct(mode)} — 0600 olmalı (hash + anahtar diskte)"


def test_auth_write_tek_kapidan_gecer(sandbox_state, monkeypatch):
    """Yazım `store.write_text("auth.json", …)`ten geçer (flock+fsync+benzersiz-tmp devralınır)."""
    seen = _capture_write_text(monkeypatch)
    payload = {"salt": "s", "hash": "h", "key": "k", "algo": "scrypt-n15-r8-p1"}
    auth._write(payload)
    assert seen["name"] == "auth.json"
    assert json.loads(seen["text"]) == payload            # biçim (indent=2) round-trip
    assert (sandbox_state / "auth.json").stat().st_mode & 0o777 == 0o600


def test_auth_write_kilidi_kapida_tutar(sandbox_state, monkeypatch):
    """Yazım anında `auth.json` kilidi TUTULUYOR olmalı (derinlik>0) — eşzamanlı ikinci yazar bekler."""
    seen: dict = {}
    real = store._atomic_write

    def izle(path, data):
        seen["depth"] = store.file_lock("auth.json")._depth
        return real(path, data)

    monkeypatch.setattr(store, "_atomic_write", izle)
    auth._write({"k": "v"})
    assert seen.get("depth") == 1, "auth._write kilit ALTINDA yazmıyor — flock kapıda tutulmuyor"


def test_auth_write_atomik_replace_duserse_eski_kalir(sandbox_state, monkeypatch):
    """os.replace düşerse eski `auth.json` AYNEN durur (yarım kimlik = herkes kilitlenir) + tmp temiz."""
    auth._write({"v": "ESKI"})
    onceki = (sandbox_state / "auth.json").read_bytes()
    _patlat_replace(monkeypatch)
    with pytest.raises(OSError):
        auth._write({"v": "YENI"})
    assert (sandbox_state / "auth.json").read_bytes() == onceki    # hedef DOKUNULMADI
    assert _tmp_artigi(sandbox_state) == []                        # tmp sızmadı


def test_auth_write_sabit_tmp_kalibi_gitti():
    """MEZAR TAŞI: `_write` artık SABİT tmp adı (`with_suffix`) kurmaz; kapıya taşındı. Docstring'de
    eski kalıbın ADI geçer ama KOD onu çağırmaz — bu yüzden yalnız Call düğümleri taranır."""
    tree = ast.parse(textwrap.dedent(inspect.getsource(auth._write)))
    calls = {n.func.attr for n in ast.walk(tree)
             if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)}
    assert "with_suffix" not in calls, "auth._write hâlâ SABİT tmp adı kuruyor (with_suffix)"
    assert "write_text" in calls, "auth._write tek kapıya (store.write_text) taşınmadı"


# =================================================================================================
# 2) memory.distill_lessons — düz Path.write_text (KIRPMA sınıfı) → store.write_text
# =================================================================================================
def _seed_hyp(status="rejected_by_backtest"):
    store.write_jsonl(memory.HYP, [
        {"id": "H00001", "variable": "entry.min_score", "status": status,
         "predicted_direction": "up", "regime": "chop", "new": 70,
         "ts": "2026-07-01T00:00:00+00:00"}])


def test_distill_lessons_tek_kapidan_ve_roundtrip(sandbox_state, monkeypatch):
    """`lessons.md` `store.write_text`ten geçer; dönen metin diskteki içerikle BİREBİR."""
    _seed_hyp()
    seen = _capture_write_text(monkeypatch)
    text = memory.distill_lessons()
    assert seen["name"] == memory.LESSONS
    assert seen["text"] == text
    assert (sandbox_state / "lessons.md").read_text() == text     # round-trip
    assert "do not retry" in text.lower()                         # içerik gerçekten üretildi


def test_distill_lessons_atomik_replace_duserse(sandbox_state, monkeypatch):
    """os.replace düşerse eski `lessons.md` durur — okuyucu (reflection prompt) boş/yarım görmez."""
    memory.distill_lessons()                          # boş defter → "no lessons yet"
    onceki = (sandbox_state / "lessons.md").read_bytes()
    _seed_hyp(status="rolled_back")                   # sonraki distill FARKLI metin üretir
    _patlat_replace(monkeypatch)
    with pytest.raises(OSError):
        memory.distill_lessons()
    assert (sandbox_state / "lessons.md").read_bytes() == onceki
    assert _tmp_artigi(sandbox_state) == []


# =================================================================================================
# 3) config.dump_yaml — mkstemp+replace (fsync YOK, flock YOK) → store.write_text
# =================================================================================================
def test_dump_yaml_tek_kapidan_ve_roundtrip(sandbox_state, monkeypatch):
    """strategy.yaml `store.write_text`ten STATE'e GÖRELİ adla geçer (kilit store yazarlarıyla
    PAYLAŞILIR); biçim (sort_keys=False) round-trip'te korunur."""
    obj = {"version": 3, "params": {"entry.min_score": 65}, "note": "ünicode ıöşç"}
    seen = _capture_write_text(monkeypatch)
    config.dump_yaml(obj, config.strategy_path())
    assert seen["name"] == "strategy.yaml"            # mutlak değil GÖRELİ → aynı dosya tek kilit
    assert yaml.safe_load((sandbox_state / "strategy.yaml").read_text()) == obj


def test_dump_yaml_history_alt_dizin_goreli_ad(sandbox_state, monkeypatch):
    """history/vNNNN.yaml da STATE'e göreli adla geçer (alt dizin korunur)."""
    seen = _capture_write_text(monkeypatch)
    config.dump_yaml({"version": 9}, config.HISTORY / "v0009.yaml")
    assert seen["name"] == "history/v0009.yaml"
    assert yaml.safe_load((sandbox_state / "history" / "v0009.yaml").read_text()) == {"version": 9}


def test_dump_yaml_STATE_disi_yol_mutlak(sandbox_state, monkeypatch, tmp_path):
    """STATE DIŞI yol (sprint sandbox'ı, sprint.py::_reset_sandbox_state) mutlak yolla geçer — relative_to fallback."""
    disari = tmp_path / "disari" / "snap.yaml"
    seen = _capture_write_text(monkeypatch)
    config.dump_yaml({"version": 1}, disari)
    assert seen["name"] == str(disari)                # STATE dışı → mutlak
    assert yaml.safe_load(disari.read_text()) == {"version": 1}


def test_dump_yaml_atomik_replace_duserse_eski_kalir(sandbox_state, monkeypatch):
    """os.replace düşerse eski strategy.yaml durur — SICAK-yeniden-yükleyen okuyucu {} yedeğine düşmez."""
    config.dump_yaml({"version": 1, "note": "ESKI"}, config.strategy_path())
    onceki = (sandbox_state / "strategy.yaml").read_bytes()
    _patlat_replace(monkeypatch)
    with pytest.raises(OSError):
        config.dump_yaml({"version": 2, "note": "YENI"}, config.strategy_path())
    assert (sandbox_state / "strategy.yaml").read_bytes() == onceki
    assert _tmp_artigi(sandbox_state) == []


# =================================================================================================
# 4) run.py scoreboard arşivi — düz Path.write_text → store.write_text (biçim KORUNUR)
#    replay_seed ağır bir yoldur (bars+backtest); taşıma YAPISAL ölçülür, atomiklik kapıda kanıtlı.
# =================================================================================================
def test_run_arsiv_kapidan_ve_bicim_korunur():
    """Arşiv `store.write_text`ten geçer, düz `Path.write_text` KALMADI, `ensure_ascii=False` biçimi
    KORUNUR (write_json ensure_ascii=True yazıp arşiv baytlarını sessizce değiştirirdi)."""
    src = inspect.getsource(run.replay_seed)
    assert ").write_text(" not in src, "replay_seed'de düz Path.write_text (KIRPMA sınıfı) kaldı"
    assert 'store.write_text(f"history/scoreboard-' in src, "arşiv tek kapıya taşınmadı"
    assert "ensure_ascii=False" in src, "arşiv biçimi (ensure_ascii=False) korunmadı"
