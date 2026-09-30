"""test_ensure_mcp_enabled_korunur_v600.py — TSK-257: öz-onarım operatörün MCP `enabled` kararını EZMEZ.

K-1 (operatör, 2026-09-30): varsayılan Hermes profilinde `mcp_servers.meridian` KAPALI
(`enabled: false`, `deploy/hermes/config.yaml` şerhi). Gerekçe: Hermes venv'ine `mcp` paketi
kurulunca girdi ilk kez canlanır ve varsayılan profili kullanan yollar (öğrenme, bileşik
ön-eleme, pano 'düşün') Meridian araçlarını ÖLÇÜLMEDEN görmeye başlar.

KUSUR (Rol-1 A1 ölçümü, 2026-09-30): `hermes.config_ensure_integrations` hedef MCP girdisini
`enabled` alanı OLMADAN kuruyor ve mevcut girdiyle sözlük eşitliğiyle kıyaslıyordu → K-1 girdisi
her çağrıda "farklı" çıkıyor, girdinin TAMAMI hedefle değiştiriliyor, `enabled: false` siliniyordu.
Canlıda tutmasının tek nedeni learn biriminin `~/.hermes`e yazamamasıydı (tesadüfi bir yazma
yasağı, kasıtlı bir kural değil); worker birimindeki pano 'entegrasyonları eşitle' ucu aynı
fonksiyonu yazma izniyle çağırır → tek tıkla K-1 silinirdi.

SÖZLEŞME (bu dosya çiviler):
  E1  `enabled: false` KORUNUR; öteki alanlar (command/args/env/tools) bugünkü gibi kanonikleşir.
  E2  `enabled: false` + öteki alanlar kanonik → YAZIM YOK (dönüş `changed` boş; dosyanın inode'u,
      mtime'ı ve sha'sı değişmez — atomik yazım tmp+replace olduğu için inode değişimi yazımın
      kendisini ölçer, aynı baytların yeniden yazılması sha'yı değiştirmese bile).
  E3  `enabled` anahtarı YOKSA eklenmez (yetenek eklenmez, kaldırılmaz) — girdi hiç yokken de.
  E4  `enabled: true` KORUNUR (koruma yön-bağımsız: operatörün değeri aynen taşınır).
  E5  A1 GEOMETRİSİ: `deploy/hermes/config.yaml` BAYT-BAYT (yorumlarıyla) A1 yollarıyla
      (`/opt/meridian`, `/opt/meridian/.venv/bin/python`) okunduğunda öz-onarım HİÇBİR ŞEY yazmaz.
      Canlıda asıl soru budur: yalnız `enabled` değil, dağıtılan dosyanın geri kalanı da kanonik
      mi? Değilse her tur yazım denenir ve her yazım `yaml.safe_dump` ile dosyanın TÜM yorumlarını
      (K-1 şerhi dahil) siler.

Mutasyon beklentisi (rapor: scratchpad tsk257-rapor): koruma satırı kaldırılırsa E1/E2/E4/E5
kırmızı; kıyas korunmuş hedef yerine eski (enabled'sız) hedefle yapılırsa E2/E5 kırmızı.
"""
from __future__ import annotations

import hashlib
import os
import sys

import pytest
import yaml

from meridian import hermes, store

# Kanonik olmayan (bayat) bir girdi: öz-onarımın düzeltmesi gereken alanlar.
BAYAT = {
    "command": "/eski/python",
    "args": ["-m", "eski.sunucu"],
    "env": {"PYTHONPATH": "/eski", "MERIDIAN_ROOT": "/eski"},
    "tools": {"resources": True, "prompts": True},
}

A1_KOK = "/opt/meridian"
A1_PYTHON = "/opt/meridian/.venv/bin/python"


@pytest.fixture(autouse=True)
def _kum(sandbox_state, monkeypatch):
    """Kum havuzu + sahte hermes ikilisi + sırsız ortam. GERÇEK `~/.hermes` OKUNMAZ/YAZILMAZ:
    `sandbox_state` AGENT_CONFIG'i zaten geçici yola çevirir; her test ayrıca kendi dosyasını kurar."""
    monkeypatch.setattr(hermes, "_hermes_bin", lambda: "/fake/hermes")
    monkeypatch.setattr(hermes.secrets, "get", lambda k, *a, **kw: None, raising=False)
    yield


def _config_kur(tmp_path, monkeypatch, belge) -> str:
    """Geçici config dosyası yazar ve AGENT_CONFIG'i ona çevirir. `belge` dict ya da ham metin."""
    yol = tmp_path / "config.yaml"
    yol.write_text(belge if isinstance(belge, str) else yaml.safe_dump(belge, sort_keys=False))
    monkeypatch.setattr(hermes, "AGENT_CONFIG", str(yol))
    return str(yol)


def _meridian_girdisi(yol: str):
    with open(yol) as fh:
        return (yaml.safe_load(fh.read()).get("mcp_servers") or {}).get("meridian")


def _kanonik_alanlar_dogru(girdi: dict) -> None:
    """command/args/env/tools öz-onarımın BUGÜNKÜ kanoniğine eşit (sözleşme değişmedi)."""
    kok = hermes._repo_root()
    assert girdi["command"] == sys.executable
    assert girdi["args"] == ["-m", "meridian.mcp_server"]
    assert girdi["env"] == {"PYTHONPATH": kok, "MERIDIAN_ROOT": kok}
    assert girdi["tools"] == {"resources": False, "prompts": False}


def _parmak_izi(yol: str) -> tuple:
    """Yazım dedektörü: atomik yazım (mkstemp + os.replace) inode'u değiştirir; mtime_ns ve sha
    ek kanıt. Aynı baytlar yeniden yazılsa bile inode/mtime yazımı ele verir."""
    st = os.stat(yol)
    with open(yol, "rb") as fh:
        sha = hashlib.sha256(fh.read()).hexdigest()
    return (st.st_ino, st.st_mtime_ns, sha)


# ----------------------------------------------------------------------------- E1

def test_E1_enabled_false_KORUNUR_oteki_alanlar_kanoniklesir(tmp_path, monkeypatch):
    """K-1 geometrisi + bayat alanlar: öz-onarım alanları düzeltir, operatörün kapattığı
    yeteneği AÇMAZ."""
    yol = _config_kur(tmp_path, monkeypatch, {
        "model": {"provider": "gemini"},
        "mcp_servers": {"meridian": {"enabled": False, **BAYAT}},
    })
    out = hermes.config_ensure_integrations()
    assert out["ok"] is True
    assert "mcp_servers.meridian" in out["changed"], "bayat alanlar düzeltilmedi"
    girdi = _meridian_girdisi(yol)
    assert "enabled" in girdi, "operatörün enabled anahtarı SİLİNDİ (K-1 ezildi)"
    assert girdi["enabled"] is False, f"K-1 ezildi: enabled={girdi['enabled']!r}"
    _kanonik_alanlar_dogru(girdi)


# ----------------------------------------------------------------------------- E2

def test_E2_enabled_false_ve_kanonik_girdi_YAZIM_YOK(tmp_path, monkeypatch):
    """Churn yok: ilk çağrı dosyayı kanonikleştirir (K-1 korunarak); ikinci çağrı HİÇBİR ŞEY
    yazmamalı. Kıyas korunmuş hedefle yapılmazsa `enabled: false` her turda 'fark' sayılır ve
    her standby turu dosyayı yeniden yazar."""
    yol = _config_kur(tmp_path, monkeypatch, {
        "model": {"provider": "gemini"},
        "mcp_servers": {"meridian": {"enabled": False, **BAYAT}},
    })
    assert hermes.config_ensure_integrations()["ok"] is True
    once = _parmak_izi(yol)
    out = hermes.config_ensure_integrations()
    assert out["ok"] is True
    assert "mcp_servers.meridian" not in out["changed"], f"churn: {out['changed']}"
    assert out["changed"] == [], f"ikinci çağrı yine yazdı: {out['changed']}"
    assert _parmak_izi(yol) == once, "dosya yeniden yazıldı (inode/mtime/sha değişti)"
    assert _meridian_girdisi(yol)["enabled"] is False


# ----------------------------------------------------------------------------- E3

def test_E3_enabled_anahtari_YOKSA_eklenmez(tmp_path, monkeypatch):
    """Bugünkü davranış korunur: anahtarsız girdi anahtarsız kalır (öz-onarım yetenek kararı
    VERMEZ — ne açar ne kapatır)."""
    yol = _config_kur(tmp_path, monkeypatch, {
        "model": {"provider": "gemini"},
        "mcp_servers": {"meridian": dict(BAYAT)},
    })
    out = hermes.config_ensure_integrations()
    assert out["ok"] is True and "mcp_servers.meridian" in out["changed"]
    girdi = _meridian_girdisi(yol)
    assert "enabled" not in girdi, f"öz-onarım enabled EKLEDİ: {girdi.get('enabled')!r}"
    _kanonik_alanlar_dogru(girdi)


def test_E3b_girdi_hic_yokken_de_enabled_eklenmez(tmp_path, monkeypatch):
    """Girdi hiç yok (ilk kurulum): bugünkü gibi kurulur, `enabled` alanı taşımaz."""
    yol = _config_kur(tmp_path, monkeypatch, {"model": {"provider": "gemini"}})
    out = hermes.config_ensure_integrations()
    assert out["ok"] is True and "mcp_servers.meridian" in out["changed"]
    girdi = _meridian_girdisi(yol)
    assert "enabled" not in girdi
    _kanonik_alanlar_dogru(girdi)


# ----------------------------------------------------------------------------- E4

def test_E4_enabled_true_KORUNUR(tmp_path, monkeypatch):
    """Koruma yön-bağımsız: operatör açtıysa açık kalır (öz-onarım kapatma kararı da vermez)."""
    yol = _config_kur(tmp_path, monkeypatch, {
        "model": {"provider": "gemini"},
        "mcp_servers": {"meridian": {"enabled": True, **BAYAT}},
    })
    out = hermes.config_ensure_integrations()
    assert out["ok"] is True
    girdi = _meridian_girdisi(yol)
    assert girdi.get("enabled") is True, f"enabled: true korunmadı: {girdi.get('enabled')!r}"
    _kanonik_alanlar_dogru(girdi)


# ----------------------------------------------------------------------------- E5

def test_E5_A1_geometrisinde_dagitim_config_i_HIC_YAZILMAZ(tmp_path, monkeypatch):
    """Dağıtılan `deploy/hermes/config.yaml` A1 yollarıyla okunduğunda öz-onarımın yapacak bir
    işi YOKTUR: dönüş `changed` boş, dosya bayt-bayt aynı (yorumlar dahil — tek bir yazım
    `yaml.safe_dump` ile K-1 şerhini de silerdi). Canlıda A1 `~/.hermes/config.yaml`ın sha'sı depo
    ile eşit ölçüldü (2026-09-30). Yorumlayıcı yolu learn biriminin ExecStart'ındaki yoldur
    (`deploy/oracle-a1/meridian-learn.service`); worker `uv run uvicorn` ile koşar ve oradaki
    yorumlayıcı yolu bu testte ÖLÇÜLMEDİ (betik shebang'ine bağlı) — farklıysa worker'daki pano
    ucu `command` alanını yeniden yazar (enabled korunur, yorumlar düşer)."""
    kaynak = store.config.ROOT / "deploy" / "hermes" / "config.yaml"
    metin = kaynak.read_text()
    assert yaml.safe_load(metin)["mcp_servers"]["meridian"].get("enabled") is False, (
        "önkoşul: dağıtım config'i K-1'i (enabled: false) taşımıyor — test geometrisi geçersiz")
    yol = _config_kur(tmp_path, monkeypatch, metin)
    monkeypatch.setattr(hermes, "_repo_root", lambda: A1_KOK)
    monkeypatch.setattr(sys, "executable", A1_PYTHON)
    once = _parmak_izi(yol)
    out = hermes.config_ensure_integrations()
    assert out["ok"] is True
    assert out["changed"] == [], f"dağıtım config'i A1'de yeniden yazılırdı: {out['changed']}"
    assert _parmak_izi(yol) == once, "dosya yeniden yazıldı (yorumlar silinirdi)"
    assert not os.path.exists(yol + ".meridian.bak"), "yazım yolu koştu (.bak alındı)"
