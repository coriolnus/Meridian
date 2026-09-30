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
  B4  MCP: sözlük olmayan girdi / bölüm çökertmez; kanonik girdi kurulur. (Tur 3: `enabled`
      DAĞITILAN varsayılanla — bugün `false` — kurulur; eskiden eklenmiyordu = K-1 atlatması.)
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
  E1  (Tur 3, Rol-1: M4 → Important) Yeni kurulan / `enabled`sız girdi `enabled`ı DAĞITILAN varsayılan
      profilden (`deploy/hermes/config.yaml` `mcp_servers.meridian.enabled`) alır — kodda sabit YOK;
      dosya okunamazsa güvenli taraf `False` + uyarı. Anahtarsız sözlük → `hermes_mcp_enabled_eklendi`.
  M1  (Tur 3) Yönetilen `tools.resources/prompts` kıyası TİP-KATI: `0`/`None`/`"false"` kanonik
      `False`a ÇEKİLİR (Python'da `0 == False`; Hermes `0`ı AÇIK sayar).
  M3  (Tur 3) Olaylar YALNIZ başarılı yazımdan sonra: yazıcı OSError fırlatınca düzeltme olayları YOK.
  M2  (Tur 3) Guard kimliği Hermes'in ayrıştırıcısıyla (`shlex.split(os.path.expanduser(...))`);
      kanonik guard komutu `shlex.quote`lu → boşluklu kökte kanonik girdi KENDİNİ tanır.
  N1  (Tur 4, Rol-1: Important — K-1 DEĞİŞMEZİ: öz-onarım sonrası varsayılan profil ancak `enabled`
      bool `True` ise açıktır) `True` DEĞİLKEN Hermes'in AÇIK okuduğu değer (`None`, `0`, `2`, `[]`,
      `"maybe"`, tırnaklı `"true"` …) dağıtılan varsayılana çekilir + `neden: belirsiz_deger` (değer
      basılmaz, yalnız tür adı). Hermes'in KAPALI okudukları (`False`, `"false"`, `"off"`, `"0"` …) ve
      bool `True` AYNEN kalır.
  N2  (Tur 4) Tip-katı kıyasta kimlik kısayolu: `.nan` taşıyan ek anahtar churn üretmez.
  N3  (Tur 4) Varsayılan okunurken `UnicodeDecodeError`/bozuk YAML öz-onarımı İPTAL ETMEZ → `False` + uyarı.

Mutasyon beklentisi: birleştirme yerine bütün-değiştirme → B1 kırmızı; kanca listesi
bütün-değiştirme → K1/K2 kırmızı; çip `enabled`ı okumazsa → S1/S2 kırmızı; kıyas eski
(birleştirilmemiş) hedefle → B2 kırmızı; taşıma anahtarı kaldırılmazsa → T1 kırmızı; guard çipi
alt-dizge eşleşmesine dönerse → G1 kırmızı; varsayılan sabit `False`a dönerse → E1 türetme
kırmızı; kıyas `==`e dönerse → M1 kırmızı; olay yazımdan önce basılırsa → M3 kırmızı; `split()`e
dönerse → M2 kırmızı; `enabled` tip/değer denetimi kaldırılırsa (yalnız anahtar varlığı) → N1
kırmızı; kimlik kısayolu kalkarsa → N2 kırmızı; `ValueError` ailesi yakalanmazsa → N3 kırmızı.
"""
from __future__ import annotations

import hashlib
import json
import os
import shlex
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
            "command": shlex.quote(os.path.join(hermes._repo_root(), "ops", "meridian-guard.sh")),
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
    {"meridian": False},
    None,
], ids=["girdi_null", "girdi_liste", "girdi_false", "bolum_null"])
def test_B4_sozluk_olmayan_girdi_cokertmez_kanonik_kurulur(tmp_path, monkeypatch, mcp_bolumu):
    yol = _config_kur(tmp_path, monkeypatch, {"model": {"provider": "gemini"},
                                              "mcp_servers": mcp_bolumu})
    out = hermes.config_ensure_integrations()
    assert out["ok"] is True and "mcp_servers.meridian" in out["changed"]
    girdi = _oku(yol)["mcp_servers"]["meridian"]
    assert girdi.get("enabled") is False, f"K-1 atlatması: girdi AÇIK kuruldu ({girdi.get('enabled')!r})"
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
    ('"/opt/meridian/ops/meridian-guard.sh"', True),  # tırnaklı: Hermes shlex ile ayrıştırır
    ('"/opt/meridian/ops/meridian-guard.sh', False),  # kapanmamış tırnak: Hermes de koşturamaz
], ids=["bak_uzantili", "ops_disi", "gercek_guard", "argumanli_guard", "tirnakli", "tirnak_bozuk"])
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


# ----------------------------------------------------------------------------- E1 (Tur 3)

def _kok_kopyasi(tmp_path, monkeypatch, enabled_metni):
    """Geçici depo kökü: `deploy/hermes/config.yaml`ın kopyası, K-1 satırı `enabled: <metin>`e
    çevrilmiş; `None` → dosya HİÇ yok. `_repo_root` bu köke çevrilir (türetmenin kaynağı)."""
    kok = tmp_path / "kok"
    hedef = kok / "deploy" / "hermes" / "config.yaml"
    hedef.parent.mkdir(parents=True)
    if enabled_metni is not None:
        metin = (mconfig.ROOT / "deploy" / "hermes" / "config.yaml").read_text()
        assert metin.count("    enabled: false\n") == 1, "önkoşul: K-1 satırı tekil değil"
        hedef.write_text(metin.replace("    enabled: false\n", f"    enabled: {enabled_metni}\n"))
    monkeypatch.setattr(hermes, "_repo_root", lambda: str(kok))
    return str(kok)


@pytest.mark.parametrize("dosyadaki,beklenen", [("false", False), ("true", True)],
                         ids=["dagitim_false", "dagitim_true"])
def test_E1_yeni_girdinin_enabled_i_DAGITIM_configinden_TURER(tmp_path, monkeypatch, dosyadaki, beklenen):
    """Tek kaynak: değer kodda sabit DEĞİL. Geçici kopyada `true` yapılınca kurulan girdi `true`
    olmalı — aksi hâlde "türetme" bir sabitin kılığıdır."""
    _kok_kopyasi(tmp_path, monkeypatch, dosyadaki)
    yol = _config_kur(tmp_path, monkeypatch, {"model": {"provider": "gemini"}})
    assert hermes.config_ensure_integrations()["ok"] is True
    assert _oku(yol)["mcp_servers"]["meridian"].get("enabled") is beklenen


@pytest.mark.parametrize("dosyadaki", [None, "null", "'false'"],
                         ids=["dosya_yok", "deger_null", "deger_dizge"])
def test_E1b_dagitim_degeri_OKUNAMAZSA_guvenli_taraf_False_ve_uyari(
        tmp_path, monkeypatch, sandbox_state, dosyadaki):
    _kok_kopyasi(tmp_path, monkeypatch, dosyadaki)
    yol = _config_kur(tmp_path, monkeypatch, {"model": {"provider": "gemini"}})
    assert hermes.config_ensure_integrations()["ok"] is True
    assert _oku(yol)["mcp_servers"]["meridian"].get("enabled") is False
    assert len(_olaylar(sandbox_state, "hermes_mcp_varsayilan_okunamadi")) == 1


@pytest.mark.parametrize("mcp_bolumu,neden", [
    ({"meridian": dict(BAYAT)}, "anahtar_yok"),
    ({}, "girdi_yok"),
    ({"meridian": None}, "sozluk_degil"),
], ids=["anahtarsiz_sozluk", "girdi_yok", "girdi_null"])
def test_E1c_enabled_EKLENDIGINDE_uyari_yazilir_bir_kez(tmp_path, monkeypatch, sandbox_state,
                                                        mcp_bolumu, neden):
    yol = _config_kur(tmp_path, monkeypatch, {"model": {"provider": "gemini"},
                                              "mcp_servers": mcp_bolumu})
    assert hermes.config_ensure_integrations()["ok"] is True
    ev = _olaylar(sandbox_state, "hermes_mcp_enabled_eklendi")
    assert len(ev) == 1 and ev[0].get("neden") == neden and ev[0].get("enabled") is False, ev
    once = _parmak_izi(yol)
    out2 = hermes.config_ensure_integrations()
    assert out2["changed"] == [] and _parmak_izi(yol) == once
    assert len(_olaylar(sandbox_state, "hermes_mcp_enabled_eklendi")) == 1, "olay tekrarlandı"


@pytest.mark.parametrize("deger", [False, True, "false"], ids=["false", "true", "dizge_false"])
def test_E1d_mevcut_enabled_DEGISMEZ_uyari_yok(tmp_path, monkeypatch, sandbox_state, deger):
    yol = _config_kur(tmp_path, monkeypatch, {"model": {"provider": "gemini"},
                                              "mcp_servers": {"meridian": {"enabled": deger, **BAYAT}}})
    assert hermes.config_ensure_integrations()["ok"] is True
    girdi = _oku(yol)["mcp_servers"]["meridian"]
    assert type(girdi["enabled"]) is type(deger) and girdi["enabled"] == deger
    assert _olaylar(sandbox_state, "hermes_mcp_enabled_eklendi") == []


# ----------------------------------------------------------------------------- M1 (Tur 3)

@pytest.mark.parametrize("deger", [0, 0.0, None, "false"], ids=["int_0", "float_0", "null", "dizge_false"])
def test_M1_yonetilen_tools_booleanlari_TIP_KATI_kanonige_cekilir(tmp_path, monkeypatch, deger):
    """Python'da `0 == False` → eski kıyas "fark yok" derdi; Hermes `_parse_boolish(0)`ı AÇIK
    sayar (yerel 0.18.2) → `resources` yardımcı araçları açılırdı."""
    yol = _kanonik_taban(tmp_path, monkeypatch)
    belge = _oku(yol)
    belge["mcp_servers"]["meridian"]["tools"]["resources"] = deger
    belge["mcp_servers"]["meridian"]["tools"]["prompts"] = deger
    _yaz(yol, belge)
    out = hermes.config_ensure_integrations()
    assert out["ok"] is True and "mcp_servers.meridian" in out["changed"], f"tip farkı görülmedi: {out}"
    araclar = _oku(yol)["mcp_servers"]["meridian"]["tools"]
    assert araclar["resources"] is False and araclar["prompts"] is False, araclar
    out2 = hermes.config_ensure_integrations()
    assert out2["changed"] == [], f"ikinci çağrı yine yazdı: {out2['changed']}"


# ----------------------------------------------------------------------------- M3 (Tur 3)

def test_M3_yazim_DUSERSE_duzeltme_olaylari_YAZILMAZ(tmp_path, monkeypatch, sandbox_state):
    _config_kur(tmp_path, monkeypatch, {
        "model": {"provider": "gemini"},
        "mcp_servers": {"meridian": {**BAYAT, "url": URL_DEGERI}},   # taşıma + anahtarsız
    })

    def _dusen_yazici(*a, **kw):
        raise OSError("salt-okur dosya sistemi (learn birimi geometrisi)")

    monkeypatch.setattr(hermes.store, "write_text", _dusen_yazici)
    out = hermes.config_ensure_integrations()
    assert out["ok"] is False, out
    for ad in ("hermes_mcp_yonetilen_alan_duzeltildi", "hermes_mcp_enabled_eklendi",
               "agent_integrations_synced"):
        assert _olaylar(sandbox_state, ad) == [], f"yazılamayan düzeltme olaylandı: {ad}"


# ----------------------------------------------------------------------------- M2 (Tur 3)

def test_M2_bosluklu_kokte_kanonik_guard_KENDINI_tanir_ve_yazim_tekrarlanmaz(tmp_path, monkeypatch):
    kok = tmp_path / "kok bosluk"
    (kok / "deploy" / "hermes").mkdir(parents=True)
    monkeypatch.setattr(hermes, "_repo_root", lambda: str(kok))
    yol = _config_kur(tmp_path, monkeypatch, {"model": {"provider": "gemini"}})
    assert hermes.config_ensure_integrations()["ok"] is True
    liste = _oku(yol)["hooks"]["pre_tool_call"]
    assert len(liste) == 1 and hermes._guard_girdisi_mi(liste[0]), liste
    assert shlex.split(os.path.expanduser(liste[0]["command"])) == [
        str(kok / "ops" / "meridian-guard.sh")], "Hermes guard'ı doğru dosya olarak ayrıştıramaz"
    once = _parmak_izi(yol)
    out2 = hermes.config_ensure_integrations()
    assert out2["changed"] == [], f"guard kendini tanımadı, yeniden eklendi: {out2['changed']}"
    assert _parmak_izi(yol) == once
    assert len(_oku(yol)["hooks"]["pre_tool_call"]) == 1


# ----------------------------------------------------------------------------- N1 (Tur 4)

@pytest.mark.parametrize("deger", [None, 0, 2, [], "maybe", "true", "yes"],
                         ids=["null", "int_0", "int_2", "bos_liste", "dizge_maybe", "dizge_true", "dizge_yes"])
def test_N1_hermesin_ACIK_okudugu_belirsiz_deger_varsayilana_cekilir(tmp_path, monkeypatch, sandbox_state, deger):
    """K-1 değişmezi (Rol-1, Tur 4): öz-onarım sonrası varsayılan profil YALNIZ bool `True` ile açık.
    Hermes (yerel 0.18.2 `_parse_boolish`, varsayılan True) bu değerlerin hepsini AÇIK okur: `None`/int/
    liste/tanınmayan dizge uyarıyla varsayılana düşer; tırnaklı `"true"/"yes"` açık okunur ama bool
    `True` DEĞİLDİR (YAML 1.1'de tırnaksız `yes/on/true` zaten bool `True` ayrıştırılır — ölçüldü)."""
    yol = _config_kur(tmp_path, monkeypatch, {"model": {"provider": "gemini"},
                                              "mcp_servers": {"meridian": {"enabled": deger, **BAYAT}}})
    assert hermes._hermes_mcp_acik_mi({"enabled": deger}) is True, "önkoşul: Hermes bu değeri AÇIK okumalı"
    out = hermes.config_ensure_integrations()
    assert out["ok"] is True and "mcp_servers.meridian" in out["changed"]
    girdi = _oku(yol)["mcp_servers"]["meridian"]
    assert girdi["enabled"] is False, f"belirsiz değer korundu → Hermes AÇIK sayar: {girdi['enabled']!r}"
    assert list(girdi)[0] == "enabled", "anahtar yerinde değiştirilmeliydi (sıra korunur)"
    ev = _olaylar(sandbox_state, "hermes_mcp_enabled_eklendi")
    assert len(ev) == 1 and ev[0].get("neden") == "belirsiz_deger", ev
    assert ev[0].get("eski_tur") == type(deger).__name__
    assert set(ev[0]) <= {"ts", "level", "event", "enabled", "neden", "eski_tur", "detail"}, (
        f"olay beklenmeyen alan taşıyor (değer sızabilir): {sorted(ev[0])}")
    if isinstance(deger, str):
        assert deger not in json.dumps(ev[0], ensure_ascii=False), "olay DEĞERİ bastı"
    once = _parmak_izi(yol)
    out2 = hermes.config_ensure_integrations()
    assert out2["changed"] == [] and _parmak_izi(yol) == once
    assert len(_olaylar(sandbox_state, "hermes_mcp_enabled_eklendi")) == 1


@pytest.mark.parametrize("deger", [False, "false", "off", "no", "0", True],
                         ids=["false", "dizge_false", "dizge_off", "dizge_no", "dizge_0", "true"])
def test_N1b_hermesin_KAPALI_okudugu_ve_bool_True_AYNEN_kalir(tmp_path, monkeypatch, sandbox_state, deger):
    yol = _config_kur(tmp_path, monkeypatch, {"model": {"provider": "gemini"},
                                              "mcp_servers": {"meridian": {"enabled": deger, **BAYAT}}})
    assert hermes.config_ensure_integrations()["ok"] is True
    girdi = _oku(yol)["mcp_servers"]["meridian"]
    assert type(girdi["enabled"]) is type(deger) and girdi["enabled"] == deger
    assert _olaylar(sandbox_state, "hermes_mcp_enabled_eklendi") == []


# ----------------------------------------------------------------------------- N2 (Tur 4)

def test_N2_nan_tasiyan_ek_anahtar_CHURN_uretmez(tmp_path, monkeypatch):
    """`float('nan') != float('nan')`: kimlik kısayolu olmadan tip-katı kıyas `.nan`lı girdiyi her
    turda "farklı" bulur → her 300 sn yeniden yazım + yorum kaybı (eski `!=` kıyası kimliğe bakıyordu)."""
    yol = _kanonik_taban(tmp_path, monkeypatch)
    belge = _oku(yol)
    belge["mcp_servers"]["meridian"]["timeout"] = float("nan")
    belge["mcp_servers"]["meridian"]["ek"] = [float("nan")]
    _yaz(yol, belge)
    once = _parmak_izi(yol)
    out = hermes.config_ensure_integrations()
    assert out["ok"] is True and out["changed"] == [], f"nan churn: {out['changed']}"
    assert _parmak_izi(yol) == once


# ----------------------------------------------------------------------------- N3 (Tur 4)

@pytest.mark.parametrize("bayt", [b"mcp_servers:\n  meridian:\n    enabled: \xff\xfe\n",
                                  b"mcp_servers: [kapanmamis\n"],
                         ids=["bozuk_utf8", "bozuk_yaml"])
def test_N3_varsayilan_dosyasi_BOZUKSA_ozonarim_iptal_olmaz_False_ve_uyari(
        tmp_path, monkeypatch, sandbox_state, bayt):
    kok = tmp_path / "kok"
    hedef = kok / "deploy" / "hermes" / "config.yaml"
    hedef.parent.mkdir(parents=True)
    hedef.write_bytes(bayt)
    monkeypatch.setattr(hermes, "_repo_root", lambda: str(kok))
    yol = _config_kur(tmp_path, monkeypatch, {"model": {"provider": "gemini"}})
    out = hermes.config_ensure_integrations()
    assert out["ok"] is True, f"öz-onarım iptal oldu: {out}"
    belge = _oku(yol)
    assert belge["mcp_servers"]["meridian"].get("enabled") is False
    assert hermes._guard_girdisi_mi(belge["hooks"]["pre_tool_call"][0]), "öteki onarımlar da koşmalı"
    assert len(_olaylar(sandbox_state, "hermes_mcp_varsayilan_okunamadi")) == 1
