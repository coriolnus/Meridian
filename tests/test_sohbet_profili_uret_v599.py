"""v599 — SOHBET PROFİLİ ÜRETECİ (konuşan filo Parça 1b G2, 2026-09-30).

`ops/sohbet_profili_uret.py` her `aktif` bot için rapor profilinden (`deploy/hermes/profiles/<ad>/`)
bir SOHBET profili türetir ve `deploy/hermes/sohbet/profiles/<ad>/` altına yazar. Bu dosya üç şeyi çiviler:
  * TAZELİK — depodaki üretilmiş dosyalar üreteçle bayt-özdeş (`--kontrol` 0); elle düzenleme, eksik ve
    fazla (kadroda `aktif` olmayan bot) dosya adıyla raporlanır; üretim deterministik.
  * DURUŞ MİRASI — guard kancası, onay, kapalı takımlar, model ve kapı sağlayıcısı rapor profilinden AYNEN
    gelir; v329'un yasak takım listesi buraya KOPYALANMAZ, İTHAL edilir.
  * SOHBET FARKLARI — Meridian MCP girdisi kök yapılandırmadan (`--bot <ad>` ekiyle), platform izin listesi
    yalnız `meridian`, Hindsight bankası `bot-<ad>` ve sırsız, zaman aşımı Hermes'in okuduğu yerde, SOUL
    rapor SOUL'u + tek sohbet bölümü ve bölüm yalnız kadrodaki aracı vaat eder.

YÜKLEYİCİ: üreteç paket değildir; `tests.conftest.betikten_modul_yukle` ile KAYNAKTAN yüklenir (ham
`loader.exec_module` bayat `__pycache__` koşturabilir ve v334 §B onu yasaklar).
"""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys

import pytest
import yaml

from tests.conftest import betikten_modul_yukle
from tests.test_bot_profil_durusu_v329 import YASAK_TAKIMLAR

KOK = pathlib.Path(__file__).resolve().parent.parent


def _ur():
    return betikten_modul_yukle(KOK / "ops/sohbet_profili_uret.py", "sohbet_profili_uret_v599")


def _aktifler():
    from meridian import kadro
    return list(kadro.aktif_botlar())


def _cfg(ad):
    return yaml.safe_load((KOK / f"deploy/hermes/sohbet/profiles/{ad}/config.yaml").read_text(encoding="utf-8"))


def _rap(ad):
    return yaml.safe_load((KOK / f"deploy/hermes/profiles/{ad}/config.yaml").read_text(encoding="utf-8"))


def test_depo_guncel_kontrol_bos():
    assert _ur().kontrol() == []


def test_komut_satiri_kontrol_sifir_doner():
    r = subprocess.run([sys.executable, "ops/sohbet_profili_uret.py", "--kontrol"], cwd=KOK,
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr


def test_bayat_dosya_yakalanir(tmp_path):
    import shutil
    shutil.copytree(KOK / "deploy", tmp_path / "deploy")
    hedef = tmp_path / "deploy/hermes/sohbet/profiles/bekci/config.yaml"
    hedef.write_text(hedef.read_text(encoding="utf-8") + "\n# el ile\n", encoding="utf-8")
    ayrisan = _ur().kontrol(kok=tmp_path)
    assert any("bekci/config.yaml" in a for a in ayrisan)


def test_uretim_deterministik():
    u = _ur()
    assert u.uret() == u.uret()


@pytest.mark.parametrize("bot", _aktifler(), ids=lambda b: b.ad)
def test_durus_rapor_profilinden_miras(bot):
    c, r = _cfg(bot.ad), _rap(bot.ad)
    for anahtar in ("hooks", "hooks_auto_accept", "approvals", "model"):
        assert c.get(anahtar) == r.get(anahtar), anahtar
    assert c["agent"]["disabled_toolsets"] == r["agent"]["disabled_toolsets"]
    assert set(YASAK_TAKIMLAR) <= set(c["agent"]["disabled_toolsets"])
    assert c["providers"]["kapi"] == r["providers"]["kapi"]


@pytest.mark.parametrize("bot", _aktifler(), ids=lambda b: b.ad)
def test_platform_izin_listesi_yalniz_meridian(bot):
    assert _cfg(bot.ad)["platform_toolsets"] == {"api_server": ["meridian"]}


@pytest.mark.parametrize("bot", _aktifler(), ids=lambda b: b.ad)
def test_mcp_girdisi_tek_kaynaktan_ve_bot_argumani(bot):
    kok = yaml.safe_load((KOK / "deploy/hermes/config.yaml").read_text(encoding="utf-8"))["mcp_servers"]["meridian"]
    m = _cfg(bot.ad)["mcp_servers"]["meridian"]
    assert m["enabled"] is True and m["args"] == kok["args"] + ["--bot", bot.ad]
    for a in ("command", "env", "tools"):
        assert m[a] == kok[a]


@pytest.mark.parametrize("bot", _aktifler(), ids=lambda b: b.ad)
def test_hafiza_saglayicisi_banka_ve_sirsiz(bot):
    assert _cfg(bot.ad)["memory"] == {"provider": "hindsight"}
    h = json.loads((KOK / f"deploy/hermes/sohbet/profiles/{bot.ad}/hindsight/config.json").read_text(encoding="utf-8"))
    assert h["bank_id"] == f"bot-{bot.ad}" and h["memory_mode"] == "context" and h["mode"] == "local_external"
    assert "api_key" not in h


@pytest.mark.parametrize("bot", _aktifler(), ids=lambda b: b.ad)
def test_zaman_asimi_hermesin_okudugu_yerde(bot):
    u, c = _ur(), _cfg(bot.ad)
    assert c["providers"]["custom"]["request_timeout_seconds"] == u.SOHBET_ISTEK_ZAMAN_ASIMI_SN
    assert c["agent"]["api_max_retries"] == u.SOHBET_API_DENEME and "timeout" not in c


@pytest.mark.parametrize("bot", _aktifler(), ids=lambda b: b.ad)
def test_soul_rapor_soulu_ile_baslar_bolum_tek(bot):
    s = (KOK / f"deploy/hermes/sohbet/profiles/{bot.ad}/SOUL.md").read_text(encoding="utf-8")
    r = (KOK / f"deploy/hermes/profiles/{bot.ad}/SOUL.md").read_text(encoding="utf-8").rstrip()
    assert s.startswith(r) and s.count("## Sohbet kipi") == 1
    bolum = s.split("## Sohbet kipi", 1)[1]
    assert not [ln for ln in bolum.splitlines() if ln.strip() == "SESSIZ"]


@pytest.mark.parametrize("bot", _aktifler(), ids=lambda b: b.ad)
def test_soul_yalniz_kadrodaki_araci_vaat_eder(bot):
    bolum = (KOK / f"deploy/hermes/sohbet/profiles/{bot.ad}/SOUL.md").read_text(encoding="utf-8").split(
        "## Sohbet kipi", 1)[1]
    for arac in ("oneri_yaz", "is_iste", "bot_hafizasi_ara"):
        beklenen = arac in bot.araclar and (arac != "bot_hafizasi_ara" or bot.hafiza == "hepsi")
        assert (arac in bolum) is beklenen, arac


def test_aktif_olmayan_bot_icin_profil_yok_ve_fazla_raporlanir(tmp_path):
    import dataclasses
    import shutil
    shutil.copytree(KOK / "deploy", tmp_path / "deploy")
    from meridian import kadro
    kd = tuple(dataclasses.replace(b, durum="sirada") if b.ad == "karne" else b for b in kadro.kadro_yukle())
    u = _ur()
    assert not any("/karne/" in y for y in u.uret(kok=tmp_path, kadro=kd))
    assert any("karne" in a and "fazla" in a for a in u.kontrol(kok=tmp_path, kadro=kd))


def test_rapor_profillerine_dokunulmaz(tmp_path):
    import hashlib
    import shutil
    shutil.copytree(KOK / "deploy", tmp_path / "deploy")

    def iz():
        return {p: hashlib.sha256(p.read_bytes()).hexdigest()
                for p in (tmp_path / "deploy/hermes/profiles").rglob("*") if p.is_file()}

    once = iz()
    _ur().yaz(kok=tmp_path)
    assert iz() == once
