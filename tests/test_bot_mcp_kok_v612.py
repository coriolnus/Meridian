"""v612 — BOT AĞ GEÇİDİNDE MCP SUNUCULARI KÖKTE, BOT BAŞINA AYRI AD (G3d, Ruling G3d-R1, 2026-10-02).

KUSUR (G3c canlı test-ateşlemesi, 2026-10-02): çoklu profil kipinde botların ARACI YOKTU, model araç çağrısını metin
olarak uyduruyordu. Kök neden (Hermes v0.19.0 kaynağıyla kanıtlı, rapor `g3c-mcp-kokneden`): Hermes MCP keşfi SÜREÇ
düzeyindedir ve ağ geçidi açılışında YALNIZ BİR KEZ, profil kapsamı olmadan, KÖK config'ten koşar
(`gateway/run.py::start_gateway` → `tools/mcp_tool.py::discover_mcp_tools` → `_load_mcp_config`). Kökte `mcp_servers`
yoktu → hiçbir sunucu başlamadı. Profil config'indeki `mcp_servers.meridian` keşif tarafından HİÇ okunmaz; istek anında
profil config'ini okuyan tek yer `hermes_cli/tools_config.py::_get_platform_tools`tir ve orada yalnız izin listesindeki
ADI belirler — kayıtta karşılığı olmayan ad boş araç kümesine çözülür.

DÜZELTME (seçenek b): kökte her aktif sohbet botu için AYRI adlı bir sunucu `meridian-<ad>` (`--bot <ad>`), profilin
izin listesi YALNIZ `[meridian-<kendi adı>]`; kök kendi istekleri için `[no_mcp]` + `agent.disabled_toolsets`e
sunucu adları (ikinci kat). Sunucular SÜREÇ-globaldir (`register_mcp_servers` adla `_servers`a koyar) → tek ortak ad
üç profilde TEK sunucu olurdu ve ilk gelenin `--bot`u kazanırdı.

GÜVENLİK SINIRI: MCP sunucusunun `tools/list`/`tools/call` çift kapısı bot kimliğini SUNUCUNUN `--bot`undan alır;
izin listesi yanlışlıkla bekçiye `meridian-sef` yazarsa bekçi sef'in tam yetkisiyle konuşur ve sunucu bunu
YAKALAYAMAZ. Asıl kontrol bu dosyadaki eşleme çivileridir: (1) sunucu adı ↔ `--bot` argümanı, (2) profil izin
listesi tam olarak kendi sunucusu.

KÖK TUZAĞI: `api_server: []` MCP'yi KAPATMAZ — `_get_platform_tools` açık MCP adı yoksa ve `no_mcp` yoksa config'te
etkin olan HER sunucuyu ekler; öneksiz istek üç botun BİRLEŞİM araç kümesini alırdı. Hermes çözümleyicisi çivisi bu
tuzağı pozitif kontrol olarak ölçer.

`${…}` YASAĞI: keşif kapsamsız koşar; `_interpolate_env_vars` → `agent/secret_scope.py::get_secret` kapsamsız
çağrıda hata atar, `_load_mcp_config` onu yutup `{}` döner — MCP SESSİZCE kapanırdı.

YÜKLEYİCİ: üreteç paket değildir; `tests.conftest.betikten_modul_yukle` ile KAYNAKTAN yüklenir (v334 §B).
Çiviler hem üretecin çıktısını (`uret()`) hem de depodaki üretilmiş dosyaları ölçer: üreteç mutasyonu da, elle
düzenleme de yakalanır. Tazelik (`--kontrol` komut satırı 0) v599'dadır, burada tekrarlanmaz.
"""
from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys

import pytest
import yaml

from tests.conftest import betikten_modul_yukle

KOK = pathlib.Path(__file__).resolve().parent.parent
KOK_CONFIG = "deploy/hermes/sohbet/config.yaml"


def _ur():
    return betikten_modul_yukle(KOK / "ops/sohbet_profili_uret.py", "sohbet_profili_uret_v612")


def _aktifler():
    from meridian import kadro
    return sorted(kadro.aktif_botlar(), key=lambda b: b.ad)


def _yapilandirmalar(kaynak: str) -> dict[str, dict]:
    """Kök + profil config'leri: `uret` = üretecin çıktısı, `disk` = depodaki üretilmiş dosyalar."""
    u = _ur()
    yollar = [KOK_CONFIG, *(f"{u.SOHBET_KOK}/{b.ad}/config.yaml" for b in _aktifler())]
    if kaynak == "uret":
        cikti = u.uret()
        return {y: yaml.safe_load(cikti[y].decode("utf-8")) for y in yollar}
    return {y: yaml.safe_load((KOK / y).read_text(encoding="utf-8")) for y in yollar}


def _kok(kaynak):
    return _yapilandirmalar(kaynak)[KOK_CONFIG]


def _profil(kaynak, ad):
    return _yapilandirmalar(kaynak)[f"{_ur().SOHBET_KOK}/{ad}/config.yaml"]


def _bot_argumani(girdi: dict) -> str | None:
    args = list(girdi.get("args") or [])
    if args.count("--bot") != 1 or args.index("--bot") + 1 >= len(args):
        return None
    return args[args.index("--bot") + 1]


KAYNAKLAR = pytest.mark.parametrize("kaynak", ["uret", "disk"])


def test_sunucu_adi_deseni_ruling_ve_bot_basina_ayri():
    # Ruling G3d-R1: ad `meridian-<ad>`; desen TEK sabitte. Ad bot başına AYRI olmalı — tek ortak ada dönüş üç profili
    # süreç-global TEK sunucuya bağlar (ilk gelenin `--bot`u kazanır).
    u = _ur()
    adlar = [u.mcp_sunucu_adi(b.ad) for b in _aktifler()]
    assert adlar == [f"meridian-{b.ad}" for b in _aktifler()]
    assert len(set(adlar)) == len(adlar) >= 2


@KAYNAKLAR
def test_kok_her_aktif_bot_icin_tam_bir_sunucu(kaynak):
    u = _ur()
    sunucular = _kok(kaynak).get("mcp_servers") or {}
    assert sorted(sunucular) == sorted(f"meridian-{b.ad}" for b in _aktifler())
    kaynak_girdi = yaml.safe_load((KOK / u.KOK_YAPILANDIRMA).read_text(encoding="utf-8"))["mcp_servers"]["meridian"]
    from meridian import secrets
    for b in _aktifler():
        g = sunucular[f"meridian-{b.ad}"]
        assert g["enabled"] is True, b.ad
        assert g["args"] == kaynak_girdi["args"] + ["--bot", b.ad], b.ad
        for anahtar in ("command", "tools"):
            assert g[anahtar] == kaynak_girdi[anahtar], (b.ad, anahtar)
        # MCP alt süreç ortamı SÜZÜLÜR: kaynağın env'i AYNEN + birimin credential yolu (değişken ADI okuyucunun sabiti).
        assert g["env"] == {**kaynak_girdi["env"], secrets.CREDENTIAL_DIZIN_ENV: u.BOT_CREDENTIAL_DIZINI}, b.ad
        assert set(g) == set(kaynak_girdi), b.ad


@KAYNAKLAR
def test_kok_sunucu_adi_bot_argumaniyla_eslesir(kaynak):
    # ASIL GÜVENLİK KONTROLÜ: sunucu kapısı kimliği `--bot`tan alır; ad↔argüman ayrışırsa bir profil başka botun
    # yetkisiyle konuşur ve hiçbir katman bunu görmez.
    sunucular = _kok(kaynak).get("mcp_servers") or {}
    assert len(sunucular) == len(_aktifler()), "kökte bot başına sunucu yok — çivi boş-boşa geçerdi"
    for ad, g in sunucular.items():
        assert ad == f"meridian-{_bot_argumani(g)}", (ad, g.get("args"))


@KAYNAKLAR
def test_profil_izin_listesi_tam_olarak_kendi_sunucusu(kaynak):
    kok_sunuculari = set(_kok(kaynak).get("mcp_servers") or {})
    for b in _aktifler():
        izin = _profil(kaynak, b.ad)["platform_toolsets"]
        assert izin == {"api_server": [f"meridian-{b.ad}"]}, (b.ad, izin)
        assert izin["api_server"][0] in kok_sunuculari, b.ad


@KAYNAKLAR
def test_profilde_mcp_servers_yok(kaynak):
    # Profil `mcp_servers`i keşif için ETKİSİZ (keşif yalnız kökten). İzin sınıflaması için de gerekmez: açık ad
    # `explicit_passthrough` ile etkinleşir. İkinci kopya tek-kaynak yasasını çiğner ve ayrışırsa sahte güvence olur.
    for b in _aktifler():
        assert "mcp_servers" not in _profil(kaynak, b.ad), b.ad


def test_rapor_profilinden_gelen_mcp_servers_profile_gecmez(tmp_path):
    # POZİTİF KONTROL: profil rapor config'inin TAMAMINI miras alır. Rapor profiline ileride bir `mcp_servers` eklenirse
    # sohbet profiline sızmamalı — sızarsa `_get_platform_tools` onu PROFİL config'inden "etkin sunucu" sayar.
    import shutil
    shutil.copytree(KOK / "deploy", tmp_path / "deploy")
    u = _ur()
    kaynak = tmp_path / u.RAPOR_KOK / "bekci" / "config.yaml"
    veri = yaml.safe_load(kaynak.read_text(encoding="utf-8"))
    veri["mcp_servers"] = {"meridian-sef": {"command": "x", "args": ["--bot", "sef"]}}
    kaynak.write_text(yaml.safe_dump(veri, allow_unicode=True, sort_keys=False), encoding="utf-8")
    profil = yaml.safe_load(u.uret(kok=tmp_path)[f"{u.SOHBET_KOK}/bekci/config.yaml"].decode("utf-8"))
    assert "mcp_servers" not in profil


@KAYNAKLAR
def test_kok_api_server_no_mcp_ve_kapali_takimlarda_sunucu_adlari(kaynak):
    k = _kok(kaynak)
    assert k["platform_toolsets"] == {"api_server": ["no_mcp"]}
    adlar = [f"meridian-{b.ad}" for b in _aktifler()]
    rapor = yaml.safe_load((KOK / _ur().RAPOR_KOK / _ur().KOK_DURUS_PROFILI / "config.yaml").read_text(encoding="utf-8"))
    # Duruşun kapalı takımları AYNEN + sunucu adları (ikinci kat; `_get_platform_tools` bunu EN SON uygular).
    assert k["agent"]["disabled_toolsets"] == rapor["agent"]["disabled_toolsets"] + adlar


def _dizgeler(d):
    if isinstance(d, dict):
        for v in d.values():
            yield from _dizgeler(v)
    elif isinstance(d, list):
        for v in d:
            yield from _dizgeler(v)
    elif isinstance(d, str):
        yield d


@KAYNAKLAR
def test_kok_mcp_girdilerinde_yer_tutucu_yok(kaynak):
    sunucular = _kok(kaynak).get("mcp_servers") or {}
    assert sunucular, "kökte MCP girdisi yok — çivi boş-boşa geçerdi"
    dizgeler = list(_dizgeler(sunucular)) + list(sunucular)
    assert not [s for s in dizgeler if "${" in s]


def test_uretec_kok_girdisinde_yer_tutucuyu_reddeder(tmp_path):
    # Kaynak (`deploy/hermes/config.yaml` meridian girdisi) bir gün `${VAR}` taşırsa üreteç onu köke TAŞIMAZ, açık hata
    # verir — kökte MCP sessizce kapanırdı (keşif kapsamsız; yer tutucu çözülemez, `_load_mcp_config` `{}` döner).
    import shutil
    shutil.copytree(KOK / "deploy", tmp_path / "deploy")
    u = _ur()
    hedef = tmp_path / u.KOK_YAPILANDIRMA
    veri = yaml.safe_load(hedef.read_text(encoding="utf-8"))
    veri["mcp_servers"]["meridian"]["env"]["MERIDIAN_ROOT"] = "${MERIDIAN_ROOT}"
    hedef.write_text(yaml.safe_dump(veri, allow_unicode=True, sort_keys=False), encoding="utf-8")
    with pytest.raises(ValueError, match=r"\$\{"):
        u.uret(kok=tmp_path)


# ---- Hermes'in KENDİ çözümleyicisiyle (v329 emsali: kaynak ağacı bulunamazsa ATLAR, sessizce geçmez) --------------------

def _hermes_kaynagi() -> tuple[pathlib.Path | None, str]:
    """`(kaynak kökü, açıklama)`. Hermes bu deponun `.venv`ine KURULU DEĞİL (v329 ölçümü) → kaynak ağacı aranır:
    `HERMES_SRC`, sonra `~/.hermes/hermes-agent`. Bulunamazsa `None` — "bulamadım" ile "geçti" aynı şey değildir."""
    adaylar = [pathlib.Path(os.environ["HERMES_SRC"])] if os.environ.get("HERMES_SRC") else []
    adaylar.append(pathlib.Path.home() / ".hermes" / "hermes-agent")
    gerekli = ("hermes_cli/tools_config.py", "tools/registry.py", "toolsets.py")
    for kok in adaylar:
        if all((kok / g).is_file() for g in gerekli):
            return kok, str(kok)
    return None, f"Hermes kaynak ağacı bulunamadı ({[str(a) for a in adaylar]}; HERMES_SRC ile verilebilir)"


#: Alt süreç kodu. AYRI SÜREÇ ŞART: Hermes'in üst düzey adları (`tools`, `agent`, `utils`, `toolsets`) bu pytest
#: oturumunun modül tablosunu kirletmesin. `-I -B`: PYTHON* ortamı ve kullanıcı site'ı yok sayılır, Hermes kaynağına
#: `.pyc` YAZILMAZ. HOME/HERMES_HOME geçici dizin: eklenti keşfi ve kimlik okumaları gerçek `~/.hermes`e dokunmaz.
#: İki durum ölçülür: kayıt BOŞ (keşif öncesi) ve sunucu adları Hermes'in kendi kayıt API'siyle diğer-ad olarak
#: kayıtlı (keşif sonrası, `_register_server_tools` sonundaki `register_toolset_alias(ad, "mcp-" + ad)`) — MCP kümesi
#: ikisinde de aynı olmalı.
_COZUCU = r"""
import json, sys
sys.path.insert(0, sys.argv[1])
import hermes_cli
from hermes_cli import tools_config as tc
from tools.registry import registry
girdi = json.load(sys.stdin)
def coz():
    return {ad: sorted(tc._get_platform_tools(cfg, "api_server")) for ad, cfg in girdi["configler"].items()}
once = coz()
for ad in girdi["sunucular"]:
    registry.register_toolset_alias(ad, "mcp-" + ad)
print(json.dumps({"surum": hermes_cli.__version__, "kayitsiz": once, "kayitli": coz()}))
"""


def _hermes_coz(kaynak_kok: pathlib.Path, configler: dict, sunucular: list[str], tmp_path) -> dict:
    ev = tmp_path / "ev"
    (ev / ".hermes").mkdir(parents=True)
    r = subprocess.run([sys.executable, "-I", "-B", "-c", _COZUCU, str(kaynak_kok)],
                       input=json.dumps({"configler": configler, "sunucular": sunucular}),
                       capture_output=True, text=True, cwd=tmp_path, timeout=180,
                       env={"HOME": str(ev), "HERMES_HOME": str(ev / ".hermes"), "PATH": os.environ.get("PATH", "")})
    assert r.returncode == 0, r.stderr[-3000:]
    return json.loads(r.stdout.strip().splitlines()[-1])


def test_hermes_cozumleyicisi_profil_kendi_sunucusunu_kok_hicbirini_gormez(tmp_path):
    kaynak_kok, aciklama = _hermes_kaynagi()
    if kaynak_kok is None:
        pytest.skip(f"Hermes çözümleyicisi ÖLÇÜLEMEDİ — {aciklama}. Bu çivi ATLANDI: yapısal çiviler (yukarıda) üretilmiş "
                    "config'i ölçer, Hermes'in o config'i NASIL çözdüğünü bu koşum ÖLÇMEDİ")
    u = _ur()
    cikti = u.uret()
    kok = yaml.safe_load(cikti[KOK_CONFIG].decode("utf-8"))
    sunucular = sorted(kok["mcp_servers"])
    configler = {"kok": kok}
    for b in _aktifler():
        configler[b.ad] = yaml.safe_load(cikti[f"{u.SOHBET_KOK}/{b.ad}/config.yaml"].decode("utf-8"))
    # POZİTİF KONTROLLER — çözümleyici gerçekten MCP adlarını görüyor mu (yoksa her şey boş döner ve çivi boş-boşa geçer):
    # (a) KÖK TUZAĞI: eski boş liste + ikinci kat yok → öneksiz istek ÜÇ sunucunun birleşimini alır;
    # (b) profil listesine başka botun sunucusu yazılırsa o sunucu çözülür (sunucu bunu YAKALAYAMAZ — rapor §5).
    tuzak = json.loads(json.dumps(kok))
    tuzak["platform_toolsets"] = {"api_server": []}
    tuzak["agent"]["disabled_toolsets"] = [t for t in tuzak["agent"]["disabled_toolsets"] if t not in sunucular]
    configler["pk_kok_bos_liste"] = tuzak
    ilk, ikinci = _aktifler()[0].ad, _aktifler()[1].ad
    sizinti = json.loads(json.dumps(configler[ilk]))
    sizinti["platform_toolsets"] = {"api_server": [f"meridian-{ilk}", f"meridian-{ikinci}"]}
    configler["pk_sizinti"] = sizinti
    sonuc = _hermes_coz(kaynak_kok, configler, sunucular, tmp_path)
    surum = f"Hermes {sonuc['surum']} ({aciklama})"
    for durum in ("kayitsiz", "kayitli"):
        mcp = {ad: set(ts) & set(sunucular) for ad, ts in sonuc[durum].items()}
        assert mcp["pk_kok_bos_liste"] == set(sunucular), (surum, durum, mcp["pk_kok_bos_liste"])
        assert mcp["pk_sizinti"] == {f"meridian-{ilk}", f"meridian-{ikinci}"}, (surum, durum)
        assert mcp["kok"] == set(), (surum, durum, sonuc[durum]["kok"])
        for b in _aktifler():
            assert mcp[b.ad] == {f"meridian-{b.ad}"}, (surum, durum, b.ad, sonuc[durum][b.ad])
