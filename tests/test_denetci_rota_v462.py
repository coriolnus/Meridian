"""v462 — Denetçi kapı rotası ÜÇ brifing botunda ORTAK (TSK-138 dilim-2 tamamlama, 2026-09-12).

KEŞİF (A1 `state/events.jsonl`): dilim-2 rotayı yalnız `@sef`e vermişti; `bekci` denetçisi
09-09/09-10 sabah "profil 150 sn'de bitmedi" ile düşüyordu, `karne` olayında `cevaplayan_model`
`None` kalıyordu — ikisi de `cagir=_profili_cagir` veriyordu, birimlerinde KAPI credential'ı yoktu.

Numara v462: ölçüldü (ana checkout + worktree'ler: v460 arama UI, v461 gölge sayım; v462 boş).

Bu dosyanın çivileri:
  1. Üç bot `soul_denetimi.gecir`e ROTAYI verir (`cagir=_ROTA.cagir` ya da sef'te `_denetci_cagir`)
     ve `cevaplayan_oku=`yu taşır; `cagir=_profili_cagir` HİÇBİRİNDE kalmaz (kaynak taraması —
     hangi üretim değişikliğinde kırılır: bir bot yeniden profil yoluna döndürülürse).
  2. Düşüş olayı BOT ÖNEKİYLE yazılır (`bekci_brifingi_denetci_rota_dustu`): teşhis bot bazında.
  3. bekci/karne düşüş yolu GÜNCEL `_profili_cagir`i çağırır (geç bağlama; v455 B-serisi deseni).
  4. sef yüzeyi ortak modüle devreder: `_cevaplayan_model_oku` `_ROTA`nın ölçümünü döndürür, sef
     kaynağında HTTP gövdesi (httpx) KALMAZ (ikinci kopya yok — tek-kaynak yasası).
  5. KAPI credential drop-in'i üç oneshot birimde AYNI satır; `sir_rotasyon.sh` oneshot listesi
     üçünü de taşır (rotasyonda "sonraki tetikte okur" sınıfı).
"""
from __future__ import annotations

import importlib
import re
from pathlib import Path

import pytest

from meridian import obs
from ops import denetci_rota

REPO = Path(__file__).resolve().parents[1]
KRED_SATIRI = "LoadCredential=KAPI_APIKEY:/etc/meridian/kapi_apikey"


def _kaynak(ad: str) -> str:
    return (REPO / "ops" / ad).read_text(encoding="utf-8")


def _gecir_blogu(ad: str) -> str:
    s = _kaynak(ad)
    i = s.index("soul_denetimi.gecir(")
    return s[i:s.index(")\n", i) + 2]


@pytest.mark.parametrize("bot", ["bekci_brifingi.py", "karne_brifingi.py", "sef_brifingi.py"])
def test_civi1_uc_bot_gecir_cagrisina_ROTAYI_verir(bot):
    blok = _gecir_blogu(bot)
    assert re.search(r"cagir=(_ROTA\.cagir|_denetci_cagir)\b", blok), blok
    assert "cevaplayan_oku=" in blok, blok
    assert "model_kimligi=" in blok, blok
    assert "cagir=_profili_cagir" not in blok, blok


def test_civi1b_bekci_ve_karne_kendi_ROTA_orneklerini_kurar():
    for bot, onek in (("bekci_brifingi.py", "bekci_brifingi"), ("karne_brifingi.py", "karne_brifingi")):
        s = _kaynak(bot)
        assert "_ROTA = denetci_rota.DenetciRota(" in s, bot
        assert f'olay_oneki="{onek}"' in s, bot


def test_civi2_dusus_olayi_BOT_ONEKIYLE_yazilir(tmp_path, monkeypatch):
    kayit: list[tuple[str, dict]] = []
    monkeypatch.setattr(obs, "log", lambda ad, **k: kayit.append((ad, k)))
    monkeypatch.delenv(denetci_rota.DENETIM_ROTA_ENV, raising=False)
    r = denetci_rota.DenetciRota(profil_evi=tmp_path, profil_cagir=lambda p: "PROFIL:" + p,
                                 olay_oneki="bekci_brifingi", model_timeout_s=5)
    assert r.cagir("soru") == "PROFIL:soru"          # config.yaml yok → kök ölçülemez → profil yolu
    assert [ad for ad, _ in kayit] == ["bekci_brifingi_denetci_rota_dustu"]
    assert kayit[0][1]["rota"] == "hizli"
    assert r.cevaplayan_oku() is None


def test_civi2b_taninmayan_rota_ADIYLA_kaydedilir_ve_varsayilana_duser(monkeypatch):
    kayit: list[str] = []
    monkeypatch.setattr(obs, "log", lambda ad, **k: kayit.append(ad))
    monkeypatch.setenv(denetci_rota.DENETIM_ROTA_ENV, "hızlı")   # Türkçe ı — yazım hatası
    assert denetci_rota.denetci_rotasi("karne_brifingi") == denetci_rota.VARSAYILAN_DENETIM_ROTASI
    assert kayit == ["karne_brifingi_denetci_rotasi_taninmadi"]


@pytest.mark.parametrize("m_ad", ["ops.bekci_brifingi", "ops.karne_brifingi"])
def test_civi3_bot_dusus_yolu_GUNCEL_profili_cagir_i_kullanir(m_ad, monkeypatch, tmp_path):
    m = importlib.import_module(m_ad)
    monkeypatch.setattr(obs, "log", lambda *a, **k: None)
    monkeypatch.delenv(denetci_rota.DENETIM_ROTA_ENV, raising=False)
    monkeypatch.setattr(m, "HERMES_PROFIL_HOME", str(tmp_path))     # config.yaml yok → düşüş
    monkeypatch.setattr(m, "_profili_cagir", lambda p: "SAHTE-PROFIL:" + p)
    assert m._ROTA.cagir("soru") == "SAHTE-PROFIL:soru"
    assert m._ROTA.cevaplayan_oku() is None


def test_civi4_sef_yuzeyi_ORTAK_modulu_kullanir():
    m = importlib.import_module("ops.sef_brifingi")
    assert m._ROTA.olay_oneki == "sef_brifingi"
    assert m.DENETIM_ROTA_ENV == denetci_rota.DENETIM_ROTA_ENV
    m._ROTA.son_cevaplayan_model = "olcum-x"
    try:
        assert m._cevaplayan_model_oku() == "olcum-x"
    finally:
        m._ROTA.son_cevaplayan_model = None
    s = _kaynak("sef_brifingi.py")
    assert "httpx.post(" not in s and "import httpx" not in s, "HTTP gövdesi sef'te ikinci kopya"
    assert "httpx.post(" in (REPO / "ops" / "denetci_rota.py").read_text(encoding="utf-8")


def test_civi5_kapi_credential_dropini_UC_oneshot_birimde_AYNI_ve_rotasyon_listesinde():
    for u in ("meridian-brifing", "meridian-bekci", "meridian-karne"):
        conf = REPO / "deploy" / "oracle-a1" / f"{u}.service.d" / "54-kapi-credential.conf"
        assert conf.is_file(), conf
        assert KRED_SATIRI in conf.read_text(encoding="utf-8"), conf
        birim = (REPO / "deploy" / "oracle-a1" / f"{u}.service").read_text(encoding="utf-8")
        assert "Type=oneshot" in birim, u
    rot = (REPO / "deploy" / "oracle-a1" / "sir_rotasyon.sh").read_text(encoding="utf-8")
    for u in ("meridian-brifing", "meridian-bekci", "meridian-karne"):
        assert f"kapi {u}.service KAPI_APIKEY /etc/meridian/kapi_apikey" in rot, u
