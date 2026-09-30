"""test_ensure_birlestirir_v603.py — TSK-258: öz-onarım yönetilen alanları BİRLEŞTİRİR, operatör
kararlarını EZMEZ + pano MCP çipi `enabled` kararını okur.

KUSUR (TSK-257 uygulayıcı kaygısı + bağımsız inceleme, 2026-09-30): TSK-257 yalnız
`mcp_servers.meridian.enabled`ı korudu. Aynı fonksiyon (`hermes.config_ensure_integrations`):
  (a) `mcp_servers.meridian` girdisinde `enabled` DIŞINDAKİ operatör anahtarlarını siliyordu
      (ör. `timeout`, `tools.include` araç daraltması — daraltma silinince yetenek GENİŞLER);
  (b) `hooks.pre_tool_call` listesini BÜTÜN değiştiriyordu (operatörün ek koruma kancası silinir).
Ayrıca `integrations_status()["mcp"]` girdinin VARLIĞINA bakıyordu, `enabled`a değil → K-1'den
(`enabled: false`) beri kapalı MCP panoda YEŞİL görünüyordu.

HERMES SEMANTİĞİ (ölçüldü 2026-09-30, YEREL hermes-agent 0.18.2 kaynağı, salt-okur; A1 v0.19
kaynağı bu turda ÖLÇÜLMEDİ): `tools/mcp_tool.py` sunucuyu
`_parse_boolish(cfg.get("enabled", True), default=True)` ile açık sayar — anahtar YOK = AÇIK;
bool aynen; dizge `true/1/yes/on` → açık, `false/0/no/off` → kapalı; öteki her şey (int dahil)
varsayılana (AÇIK) düşer. Sözlük olmayan girdi `_load_mcp_config`te ATLANIR (bağlanmaz).
`pre_tool_call` yönergelerinde "ilk geçerli yönerge kazanır" (`hermes_cli/plugins.py`
`_get_pre_tool_call_directive_details`) → eksik guard listenin BAŞINA eklenir: önde duran bir
operatör kancasının `approve` yönergesi guard'ın `block`unu gölgeleyemesin.

SÖZLEŞME (bu dosya çiviler):
  B1  MCP: operatörün ek anahtarları (`timeout`, `tools.include`) KORUNUR; `command/args/env`
      kanonikleşir, `tools.resources/prompts` zorlanır; `enabled` korunur; ikinci çağrı YAZMAZ.
  B2  MCP: yönetilen alanlar kanonikken ek anahtarlar tek başına YAZIM ÜRETMEZ (churn yok).
  B3  MCP: `env` YÖNETİLEN alandır (Rol-1 kararı) — ek değişken kanoniğe çekilir.
  B4  MCP: sözlük olmayan girdi / bölüm çökertmez; kanonik girdi kurulur, `enabled` eklenmez.
  K1  Kanca: guard yoksa BAŞA bir kez eklenir; operatör kancaları ve SIRASI korunur; öteki kanca
      olayları dokunulmaz; ikinci çağrı YAZMAZ.
  K2  Kanca: bayat guard girdisi YERİNDE kanonikleşir (konumu korunur, operatör alanları korunur).
  K3  Kanca: guard kanonik + operatör kancaları → YAZIM YOK.
  S1  Çip: `integrations_status()["mcp"]` = girdi var ∧ Hermes'in `enabled` yorumu.
  S2  Çip: dağıtılan `deploy/hermes/config.yaml` (K-1) → `mcp` False.
  T1  (Tur 2, Rol-1 kararı) TAŞIMA anahtarları (`hermes._MCP_TASIMA_ANAHTARLARI`) YÖNETİLEN alandır:
      varsa KALDIRILIR, `hermes_mcp_yonetilen_alan_duzeltildi` uyarısı yalnız ANAHTAR ADLARIYLA
      yazılır (değer basılmaz); operatörün öteki anahtarları korunur; ikinci çağrı yazmaz. Ölçüm
      (yerel 0.18.2): stdio yerine HTTP'yi seçtiren TEK anahtar `url`dur (`MCPServerTask._is_http`);
      `transport` (sse/streamable) ve `headers` yalnız `url` varken okunur — Rol-1 üçünü de yönetir.
  G1  (Tur 2) Guard çipi öz-onarımla AYNI tanımı kullanır (`_guard_girdisi_mi`, tek kaynak):
      guard'a benzeyen başka yol "var" sayılmaz; sözlük olmayan kanca girdisi öteki alanları düşürmez.

Mutasyon beklentisi: birleştirme yerine bütün-değiştirme → B1 kırmızı; kanca listesi
bütün-değiştirme → K1/K2 kırmızı; çip `enabled`ı okumazsa → S1/S2 kırmızı; kıyas eski
(birleştirilmemiş) hedefle → B2 kırmızı; taşıma anahtarı kaldırılmazsa → T1 kırmızı; guard çipi
alt-dizge eşleşmesine dönerse → G1 kırmızı.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys

import pytest
import yaml

from meridian import config as mconfig
from meridian import hermes

BAYAT = {
    "command": "/eski/python",
    "args": ["-m", "eski.sunucu"],
    "env": {"PYTHONPATH": "/eski", "MERIDIAN_ROOT": "/eski"},
    "tools": {"resources": True, "prompts": True},
}

OP_KANCA_A = {"matcher": "terminal", "command": "/op/kancalar/denetim-a.sh", "timeout": 5}
OP_KANCA_B = {"matcher": "write_file", "command": "/op/kancalar/denetim-b.sh", "timeout": 7}
OP_POST = [{"command": "/op/kancalar/sonra.sh"}]


@pytest.fixture(autouse=True)
def _kum(sandbox_state, monkeypatch):
    """Kum havuzu + sahte hermes ikilisi + sırsız ortam. GERÇEK `~/.hermes` OKUNMAZ/YAZILMAZ:
    her test AGENT_CONFIG'i kendi geçici dosyasına çevirir."""
    monkeypatch.setattr(hermes, "_hermes_bin", lambda: "/fake/hermes")
    monkeypatch.setattr(hermes.secrets, "get", lambda k, *a, **kw: None, raising=False)
    yield


def _config_kur(tmp_path, monkeypatch, belge) -> str:
    yol = tmp_path / "config.yaml"
    yol.write_text(belge if isinstance(belge, str) else yaml.safe_dump(belge, sort_keys=False))
    monkeypatch.setattr(hermes, "AGENT_CONFIG", str(yol))
    return str(yol)


def _oku(yol: str) -> dict:
    with open(yol) as fh:
        return yaml.safe_load(fh.read()) or {}


def _yaz(yol: str, belge: dict) -> None:
    with open(yol, "w") as fh:
        fh.write(yaml.safe_dump(belge, sort_keys=False))


def _parmak_izi(yol: str) -> tuple:
    """Yazım dedektörü (v600 deseni): atomik yazım inode'u değiştirir; mtime_ns + sha ek kanıt."""
    st = os.stat(yol)
    with open(yol, "rb") as fh:
        sha = hashlib.sha256(fh.read()).hexdigest()
    return (st.st_ino, st.st_mtime_ns, sha)


def _kanonik_komut_alanlari(girdi: dict) -> None:
    kok = hermes._repo_root()
    assert girdi["command"] == sys.executable
    assert girdi["args"] == ["-m", "meridian.mcp_server"]
    assert girdi["env"] == {"PYTHONPATH": kok, "MERIDIAN_ROOT": kok}
    assert girdi["tools"]["resources"] is False and girdi["tools"]["prompts"] is False


def _guard() -> dict:
    return {"matcher": "terminal|write_file|patch|edit|apply_patch",
            "command": os.path.join(hermes._repo_root(), "ops", "meridian-guard.sh"),
            "timeout": 10}


def _kanonik_taban(tmp_path, monkeypatch) -> str:
    """Öz-onarımın kendi kanoniğine çektiği bir config (tek çağrı). Üstüne operatör düzenlemesi
    yapılır; sonraki çağrının yazıp yazmadığı ölçülür."""
    yol = _config_kur(tmp_path, monkeypatch, {"model": {"provider": "gemini"}})
    assert hermes.config_ensure_integrations()["ok"] is True
    return yol


# ----------------------------------------------------------------------------- B1

def test_B1_mcp_operator_ek_anahtarlari_KORUNUR_yonetilenler_kanoniklesir(tmp_path, monkeypatch):
    girdi0 = {"enabled": False, **BAYAT, "timeout": 30,
              "tools": {"resources": True, "prompts": True, "include": ["a", "b"]}}
    yol = _config_kur(tmp_path, monkeypatch, {"model": {"provider": "gemini"},
                                              "mcp_servers": {"meridian": girdi0}})
    out = hermes.config_ensure_integrations()
    assert out["ok"] is True and "mcp_servers.meridian" in out["changed"]
    girdi = _oku(yol)["mcp_servers"]["meridian"]
    assert girdi.get("timeout") == 30, f"operatörün timeout'u silindi: {girdi}"
    assert girdi["tools"].get("include") == ["a", "b"], (
        f"operatörün araç daraltması silindi (yetenek GENİŞLEDİ): {girdi['tools']}")
    assert girdi.get("enabled") is False, "TSK-257 koruması kırıldı"
    _kanonik_komut_alanlari(girdi)
    once = _parmak_izi(yol)
    out2 = hermes.config_ensure_integrations()
    assert out2["ok"] is True and out2["changed"] == [], f"ikinci çağrı yine yazdı: {out2['changed']}"
    assert _parmak_izi(yol) == once, "dosya yeniden yazıldı"


# ----------------------------------------------------------------------------- B2

def test_B2_mcp_ek_anahtarlar_tek_basina_YAZIM_URETMEZ(tmp_path, monkeypatch):
    yol = _kanonik_taban(tmp_path, monkeypatch)
    belge = _oku(yol)
    m = belge["mcp_servers"]["meridian"]
    m["timeout"] = 30
    m["tools"]["include"] = ["a", "b"]
    _yaz(yol, belge)
    once = _parmak_izi(yol)
    out = hermes.config_ensure_integrations()
    assert out["ok"] is True and out["changed"] == [], f"churn: {out['changed']}"
    assert _parmak_izi(yol) == once, "yönetilen alan farkı yokken dosya yeniden yazıldı"


# ----------------------------------------------------------------------------- B3

def test_B3_mcp_env_YONETILEN_alan_ek_degisken_kanonige_cekilir(tmp_path, monkeypatch):
    yol = _kanonik_taban(tmp_path, monkeypatch)
    belge = _oku(yol)
    belge["mcp_servers"]["meridian"]["env"]["EK_DEGISKEN"] = "1"
    _yaz(yol, belge)
    out = hermes.config_ensure_integrations()
    assert out["ok"] is True and "mcp_servers.meridian" in out["changed"]
    _kanonik_komut_alanlari(_oku(yol)["mcp_servers"]["meridian"])


# ----------------------------------------------------------------------------- B4

@pytest.mark.parametrize("mcp_bolumu", [
    {"meridian": None},
    {"meridian": ["liste"]},
    None,
], ids=["girdi_null", "girdi_liste", "bolum_null"])
def test_B4_sozluk_olmayan_girdi_cokertmez_kanonik_kurulur(tmp_path, monkeypatch, mcp_bolumu):
    yol = _config_kur(tmp_path, monkeypatch, {"model": {"provider": "gemini"},
                                              "mcp_servers": mcp_bolumu})
    out = hermes.config_ensure_integrations()
    assert out["ok"] is True and "mcp_servers.meridian" in out["changed"]
    girdi = _oku(yol)["mcp_servers"]["meridian"]
    assert "enabled" not in girdi
    _kanonik_komut_alanlari(girdi)


# ----------------------------------------------------------------------------- K1

def test_K1_guard_yoksa_BASA_bir_kez_eklenir_operator_kancalari_ve_sirasi_korunur(
        tmp_path, monkeypatch):
    yol = _config_kur(tmp_path, monkeypatch, {
        "model": {"provider": "gemini"},
        "hooks": {"pre_tool_call": [dict(OP_KANCA_A), dict(OP_KANCA_B)],
                  "post_tool_call": [dict(h) for h in OP_POST]},
    })
    out = hermes.config_ensure_integrations()
    assert out["ok"] is True and "hooks.pre_tool_call" in out["changed"]
    hooks = _oku(yol)["hooks"]
    assert hooks["pre_tool_call"] == [_guard(), OP_KANCA_A, OP_KANCA_B], (
        f"guard başa eklenmedi ya da operatör kancaları/sırası bozuldu: {hooks['pre_tool_call']}")
    assert hooks["post_tool_call"] == OP_POST, "öteki kanca olayı değişti"
    once = _parmak_izi(yol)
    out2 = hermes.config_ensure_integrations()
    assert out2["ok"] is True and out2["changed"] == [], f"ikinci çağrı yine yazdı: {out2['changed']}"
    assert _parmak_izi(yol) == once
    assert sum(1 for h in _oku(yol)["hooks"]["pre_tool_call"]
               if "meridian-guard" in h["command"]) == 1, "guard birden çok kez eklendi"


# ----------------------------------------------------------------------------- K2

def test_K2_bayat_guard_YERINDE_kanoniklesir(tmp_path, monkeypatch):
    bayat_guard = {"matcher": "terminal", "command": "/eski/kok/ops/meridian-guard.sh",
                   "timeout": 99, "op_notu": "kalsin"}
    yol = _config_kur(tmp_path, monkeypatch, {
        "model": {"provider": "gemini"},
        "hooks": {"pre_tool_call": [dict(OP_KANCA_A), bayat_guard, dict(OP_KANCA_B)]},
    })
    out = hermes.config_ensure_integrations()
    assert out["ok"] is True and "hooks.pre_tool_call" in out["changed"]
    liste = _oku(yol)["hooks"]["pre_tool_call"]
    assert len(liste) == 3, f"liste boyu değişti (guard çoğaldı ya da kanca silindi): {liste}"
    assert liste[0] == OP_KANCA_A and liste[2] == OP_KANCA_B, f"operatör kancaları bozuldu: {liste}"
    assert {k: liste[1][k] for k in ("matcher", "command", "timeout")} == _guard(), (
        f"guard girdisi kanonikleşmedi: {liste[1]}")
    assert liste[1].get("op_notu") == "kalsin", "guard girdisindeki operatör alanı silindi"


# ----------------------------------------------------------------------------- K3

def test_K3_guard_kanonik_ve_operator_kancalari_YAZIM_YOK(tmp_path, monkeypatch):
    yol = _kanonik_taban(tmp_path, monkeypatch)
    belge = _oku(yol)
    belge["hooks"]["pre_tool_call"].append(dict(OP_KANCA_A))
    belge["hooks"]["pre_tool_call"].insert(0, dict(OP_KANCA_B))   # operatör guard'ın ÖNÜNE koydu
    _yaz(yol, belge)
    once = _parmak_izi(yol)
    out = hermes.config_ensure_integrations()
    assert out["ok"] is True and out["changed"] == [], f"churn: {out['changed']}"
    assert _parmak_izi(yol) == once, "operatörün sıralaması yeniden yazıldı"


# ----------------------------------------------------------------------------- S1

@pytest.mark.parametrize("girdi,beklenen", [
    ({"command": "py", "enabled": False}, False),
    ({"command": "py", "enabled": True}, True),
    ({"command": "py"}, True),                       # anahtar YOK → Hermes varsayılanı AÇIK
    ({"command": "py", "enabled": None}, True),      # null → varsayılan
    ({"command": "py", "enabled": "false"}, False),
    ({"command": "py", "enabled": "off"}, False),
    ({"command": "py", "enabled": "0"}, False),
    ({"command": "py", "enabled": " Yes "}, True),
    ({"command": "py", "enabled": 0}, True),         # int: bool/dizge değil → varsayılan (0.18.2)
    (None, False),                                   # sözlük olmayan girdi Hermes'te ATLANIR
    ("yok", False),                                  # girdi hiç yok
], ids=["false", "true", "anahtar_yok", "null", "dizge_false", "dizge_off", "dizge_0",
        "dizge_yes", "int_0", "girdi_null", "girdi_yok"])
def test_S1_mcp_cipi_enabled_kararini_okur(tmp_path, monkeypatch, girdi, beklenen):
    servers = {} if girdi == "yok" else {"meridian": girdi}
    _config_kur(tmp_path, monkeypatch, {"mcp_servers": servers})
    assert hermes.integrations_status()["mcp"] is beklenen


# ----------------------------------------------------------------------------- S2

def test_S2_dagitim_config_i_K1_ile_cip_KAPALI(tmp_path, monkeypatch):
    metin = (mconfig.ROOT / "deploy" / "hermes" / "config.yaml").read_text()
    assert yaml.safe_load(metin)["mcp_servers"]["meridian"].get("enabled") is False, (
        "önkoşul: dağıtım config'i K-1'i taşımıyor — test geometrisi geçersiz")
    _config_kur(tmp_path, monkeypatch, metin)
    st = hermes.integrations_status()
    assert st["mcp"] is False, "K-1 ile kapalı MCP panoda AÇIK görünüyor"
    assert st["guard_hook"] is True, "guard çipi bu değişiklikten etkilenmemeliydi"


# ----------------------------------------------------------------------------- T1 (Tur 2)

URL_DEGERI = "http://deger-basilmaz.invalid/mcp"
BASLIK_DEGERI = "Bearer deger-basilmaz-kanarya"


def _olaylar(sandbox_state, ad: str) -> list:
    yol = sandbox_state / "events.jsonl"
    if not yol.exists():
        return []
    return [json.loads(l) for l in yol.read_text().splitlines()
            if l.strip() and json.loads(l).get("event") == ad]


def test_T1_tasima_anahtarlari_KALDIRILIR_olay_yalniz_ADLARLA(tmp_path, monkeypatch, sandbox_state):
    """Öz-onarımın güvencesi: `mcp_servers.meridian` YEREL stdio sunucumuzu gösterir. `url` varken
    Hermes `command`ı yok sayıp HTTP'ye bağlanır (yerel 0.18.2 ölçümü) — girdi başka bir uca
    yönelmiş olur. Taşıma anahtarları kaldırılır; operatörün öteki kararları kalır."""
    yol = _config_kur(tmp_path, monkeypatch, {
        "model": {"provider": "gemini"},
        "mcp_servers": {"meridian": {"enabled": False, **BAYAT, "timeout": 30,
                                     "url": URL_DEGERI, "transport": "http",
                                     "headers": {"Authorization": BASLIK_DEGERI}}},
    })
    out = hermes.config_ensure_integrations()
    assert out["ok"] is True and "mcp_servers.meridian" in out["changed"]
    girdi = _oku(yol)["mcp_servers"]["meridian"]
    kalan = [k for k in ("url", "transport", "headers") if k in girdi]
    assert kalan == [], f"taşıma anahtarları kaldırılmadı: {kalan}"
    assert girdi.get("enabled") is False and girdi.get("timeout") == 30, (
        f"operatörün öteki anahtarları korunmadı: {sorted(girdi)}")
    _kanonik_komut_alanlari(girdi)
    ev = _olaylar(sandbox_state, "hermes_mcp_yonetilen_alan_duzeltildi")
    assert len(ev) == 1, f"düzeltme olayı tek kez yazılmadı: {len(ev)}"
    assert ev[0].get("anahtarlar") == ["url", "transport", "headers"], ev[0].get("anahtarlar")
    ham = (sandbox_state / "events.jsonl").read_text()
    assert URL_DEGERI not in ham and BASLIK_DEGERI not in ham, "olay anahtar DEĞERİ bastı"
    once = _parmak_izi(yol)
    out2 = hermes.config_ensure_integrations()
    assert out2["ok"] is True and out2["changed"] == [], f"ikinci çağrı yine yazdı: {out2['changed']}"
    assert _parmak_izi(yol) == once
    assert len(_olaylar(sandbox_state, "hermes_mcp_yonetilen_alan_duzeltildi")) == 1, (
        "fark yokken olay yeniden yazıldı")


def test_T1b_tasima_anahtari_sabiti_TEK_KAYNAK():
    """Liste tek sabitte yaşar; `url` (Hermes'in HTTP seçicisi) mutlaka içinde."""
    assert hermes._MCP_TASIMA_ANAHTARLARI == ("url", "transport", "headers")


# ----------------------------------------------------------------------------- G1 (Tur 2)

@pytest.mark.parametrize("komut,beklenen", [
    ("/tmp/meridian-guard.sh.bak", False),          # benzer ad, başka dosya
    ("/tmp/meridian-guard.sh", False),              # `ops/` altında değil
    ("/opt/meridian/ops/meridian-guard.sh", True),
    ("/x/ops/meridian-guard.sh --kati", True),      # ilk sözcük guard
], ids=["bak_uzantili", "ops_disi", "gercek_guard", "argumanli_guard"])
def test_G1_guard_cipi_ozonarimla_AYNI_tanimi_kullanir(tmp_path, monkeypatch, komut, beklenen):
    _config_kur(tmp_path, monkeypatch, {"hooks": {"pre_tool_call": [{"command": komut}]}})
    assert hermes.integrations_status()["guard_hook"] is beklenen
    assert hermes._guard_girdisi_mi({"command": komut}) is beklenen, "iki tanım ayrıştı"


def test_G1b_sozluk_olmayan_kanca_girdisi_OTEKI_alanlari_dusurmez(tmp_path, monkeypatch):
    _config_kur(tmp_path, monkeypatch, {
        "hooks": {"pre_tool_call": ["dizge-girdi", {"command": "/opt/meridian/ops/meridian-guard.sh"}]},
        "prompt_caching": {"cache_ttl": "1h"},
    })
    st = hermes.integrations_status()
    assert st["guard_hook"] is True
    assert st["prompt_cache"] == "1h", "kanca satırındaki çökme öteki alanları düşürdü"
