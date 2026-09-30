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
  * BOT AĞ GEÇİDİ (G3) — ikincil profilde `api_server` kapalı, MCP `env:`inde birim adından türeyen credential
    yolu, ortak bot kum havuzu, `.env`e yönlendiren Hindsight açıklaması; kök (varsayılan) profil çoklu kipte,
    araçsız, hafızasız, duruşu sef rapor profilinden ve SOUL'u yalnız yönlendirme cümlesi.

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


def test_ureteci_yuklemek_obs_ithal_etmez():
    # Tur 3 ek (ölçülmüş sınıf: pytest-dışı koşum canlı yerel deftere yazar, 3 vaka): üreteç `--yaz`/`--kontrol` ile
    # pytest DIŞINDA koşar; ithal zinciri `meridian.obs`a ulaşırsa bir sonraki değişiklik deftere yazabilir.
    # ALT SÜREÇ ŞART: bu pytest oturumunda `meridian.obs` zaten ithal edilmiştir. Modül KAYNAKTAN yüklenir, `main`
    # ÇAĞRILMAZ (ad `__main__` değil → dosya yazılmaz). İkinci değer pozitif kontroldür: zincir gerçekten yüklendi.
    import os
    kod = ("import sys\n"
           "from ops.sasi_yukleyici import kaynaktan_yukle\n"
           "kaynaktan_yukle('ops/sohbet_profili_uret.py', 'sohbet_profili_uret_obs_yoklugu')\n"
           "print('meridian.obs' in sys.modules, 'meridian.bot_hafiza' in sys.modules)\n")
    r = subprocess.run([sys.executable, "-c", kod], cwd=KOK, capture_output=True, text=True,
                       env={**os.environ, "PYTHONPATH": str(KOK)})
    assert r.returncode == 0, r.stderr[-2000:]
    assert r.stdout.strip() == "False True", r.stdout


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
    for a in ("command", "tools"):
        assert m[a] == kok[a]
    # G3: `env`e tek ek credential yoludur (aşağıdaki çivi); geri kalanı kökle AYNI kalır. Değişken ADI okuyucunun
    # sabitinden (`secrets.CREDENTIAL_DIZIN_ENV`) — literal değil (tek kaynak; Tur 2 Minor 1).
    from meridian import secrets
    assert {k: v for k, v in m["env"].items() if k != secrets.CREDENTIAL_DIZIN_ENV} == kok["env"]


@pytest.mark.parametrize("bot", _aktifler(), ids=lambda b: b.ad)
def test_hafiza_saglayicisi_banka_ve_sirsiz(bot):
    assert _cfg(bot.ad)["memory"] == {"provider": "hindsight"}
    h = json.loads((KOK / f"deploy/hermes/sohbet/profiles/{bot.ad}/hindsight/config.json").read_text(encoding="utf-8"))
    assert h["bank_id"] == f"bot-{bot.ad}" and h["memory_mode"] == "context" and h["mode"] == "local_external"
    assert "api_key" not in h


def _hs(ad):
    return json.loads((KOK / f"deploy/hermes/sohbet/profiles/{ad}/hindsight/config.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("bot", _aktifler(), ids=lambda b: b.ad)
def test_hafiza_otomatik_kayit_kapali_hatirlama_acik(bot):
    # Dal sonu I-1 (Rol-1 seçenek A): Hermes'in otomatik kaydı sohbet dönüşünü `notify.scrub`'dan geçirmeden
    # kalıcı, silinemez bankaya yazar (spec §3.4 "kayıt öncesi scrub"). Yazan tek taraf kanal katmanıdır
    # (`bota_sor`, G4); hatırlama açık kalır — banka yalnız scrub'lı içerik taşır.
    h = _hs(bot.ad)
    assert h["auto_retain"] is False and h["auto_recall"] is True


@pytest.mark.parametrize("bot", _aktifler(), ids=lambda b: b.ad)
def test_hindsight_baglantisi_meridian_sabitleriyle_ayni(bot):
    # Dal sonu I-2 (tek kaynak, v596 emsali): Hermes'in okuduğu banka ve bağlantı, kanal katmanının
    # (`bot_hafiza`) yazdığı/okuduğu banka ve bağlantıyla AYNI olmalı — ayrışırsa `hatırla:` notu X'e yazılır,
    # Hermes Y'yi okur ve iki özellik sessizce ölür. Banka öneki bot_hafiza'da sabit değil: yol eşitliğiyle bağlı.
    from meridian import bot_hafiza, secrets
    h = _hs(bot.ad)
    assert h["api_url"] == secrets.HAFIZA_TABAN_URL
    assert h["timeout"] == bot_hafiza.HAFIZA_ZAMAN_ASIMI_S
    assert h["recall_budget"] == bot_hafiza.UNUT_RECALL_BUTCESI
    assert bot_hafiza.HindsightHafiza()._banka_yolu(bot.ad) == f"{h['api_url']}{bot_hafiza.BANKA_KOKU}/{h['bank_id']}"


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
    # Tur 2 (inceleme Minor 1): rapor kısmının tek başına şablon satırını EZEN cümle bölümde durmalı —
    # yoksa sef/bekci sohbette de o jetonla cevap verebilir (cevapsızlık = sessiz arıza).
    assert "SESSIZ yazmazsın" in bolum


def _bolum(ad):
    return (KOK / f"deploy/hermes/sohbet/profiles/{ad}/SOUL.md").read_text(encoding="utf-8").split(
        "## Sohbet kipi", 1)[1]


@pytest.mark.parametrize("bot", _aktifler(), ids=lambda b: b.ad)
def test_soul_rapor_kipi_ifadelerini_ezer(bot):
    # Tur 2 (inceleme Minor 2/3, Rol-1 metni): rapor SOUL'larındaki "araçların yok / hafızan yok" ve rapor
    # biçimi/uzunluk kuralları sohbette aracı reddettirmesin, cevabı kırpmasın. Aktif bot kadroda araçsız olamaz.
    bolum = _bolum(bot.ad)
    assert "çelişirse bu bölüm geçerlidir" in bolum and "önce gelir" not in bolum
    assert "o cümleler zamanlanmış rapor içindir. Bu kipte Meridian araçların ve geçmiş konuşmalarından gelen " \
           "notlar var." in bolum
    assert "notlar var; aracın yok." not in bolum
    assert "Rapor biçimi ve uzunluk kuralları (karakter payı, bölüm düzeni) bu kipte uygulanmaz." in bolum


def test_aracsiz_bot_arac_vaat_etmez(tmp_path):
    # Yetenek vaadi mekanizmaya bağlı: araç listesi boş bot "Meridian araçların var" demez.
    import dataclasses
    import shutil
    shutil.copytree(KOK / "deploy", tmp_path / "deploy")
    from meridian import kadro
    kd = tuple(dataclasses.replace(b, araclar=()) if b.ad == "karne" else b for b in kadro.kadro_yukle())
    soul = _ur().uret(kok=tmp_path, kadro=kd)["deploy/hermes/sohbet/profiles/karne/SOUL.md"].decode("utf-8")
    bolum = soul.split("## Sohbet kipi", 1)[1]
    assert "- Bu kipte geçmiş konuşmalarından gelen notlar var; aracın yok." in bolum
    assert "Meridian araçların" not in bolum and "is_iste" not in bolum


@pytest.mark.parametrize("bot", _aktifler(), ids=lambda b: b.ad)
def test_manifest_kapi_anahtari_ve_yazma_koku_sohbete_ozgu(bot):
    # Tur 2 (inceleme Minor 4): kapı anahtarının adı/zorunluluğu rapor manifestinden, açıklaması sohbet kipine
    # özgü (rapor düşüş yolunun "ham" anlatımı taşınmaz); yazma kökü beyanlı ve rapor kum havuzundan AYRI.
    import re
    m = yaml.safe_load((KOK / f"deploy/hermes/sohbet/profiles/{bot.ad}/distribution.yaml").read_text(encoding="utf-8"))
    r = yaml.safe_load((KOK / f"deploy/hermes/profiles/{bot.ad}/distribution.yaml").read_text(encoding="utf-8"))
    girdiler = {g["name"]: g for g in m["env_requires"]}
    anahtar = f"BOT_KEY_{bot.ad.upper()}"
    rapor_girdisi = next(g for g in r["env_requires"] if g["name"] == anahtar)
    assert anahtar in girdiler and girdiler[anahtar]["required"] == rapor_girdisi["required"]
    assert not re.search(r"\bham\b", girdiler[anahtar]["description"])
    kok = girdiler["HERMES_WRITE_SAFE_ROOT"]
    # G3 (ölçüldü 2026-09-30): değişken SÜREÇ başına okunur → tek ağ geçidinde bot başına kum havuzu imkânsız;
    # beyanlı sapma: bütün sohbet profilleri ortak `BOT_KUM_HAVUZU` (rapor kum havuzlarından yine AYRI).
    assert kok["required"] is True and kok["default"] == _ur().BOT_KUM_HAVUZU
    assert kok["default"] != next(g for g in r["env_requires"] if g["name"] == "HERMES_WRITE_SAFE_ROOT")["default"]
    # G3: çoklu kipte sırlar PROFİL `.env`inden okunur (`os.environ`a düşmez) — açıklama operatörü credential'a
    # değil `.env`e yönlendirmeli; yanlış yönlendirme anahtarsız profil ve sessiz hafızasızlık demektir.
    hs = girdiler["HINDSIGHT_API_KEY"]["description"]
    assert "credential" not in hs.casefold() and ".env" in hs


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


# ---- G3 (Parça 1b G3 Task 1, 2026-09-30): bot ağ geçidi — ikincil profil, MCP credential yolu, kök profil ------------
# Ölçüm kaynağı: plan `docs/superpowers/plans/2026-09-30-konusan-filo-parca1b-g3-bot-agi-gecidi.md` Architecture
# (A1 Hermes v0.19.0 kaynağından). Tek ağ geçidi (`BOT_BIRIMI`) ayrı bir Hermes kökünde çoklu kipte koşar: kök
# (varsayılan) profil dinleyiciyi tutar, sohbet profilleri `/p/<ad>/` altında ikincil profildir.

KOK_CONFIG = "deploy/hermes/sohbet/config.yaml"
KOK_SOUL = "deploy/hermes/sohbet/SOUL.md"


def _kok_cfg():
    return yaml.safe_load((KOK / KOK_CONFIG).read_text(encoding="utf-8"))


@pytest.mark.parametrize("bot", _aktifler(), ids=lambda b: b.ad)
def test_ikincil_profil_api_server_kapali(bot):
    # Süreç ortamındaki dinleyici anahtarı ikincil profilde de dinleyici açmaya zorlar → ağ geçidi açılışta
    # `MultiplexConfigError` ile düşer. Dinleyiciyi yalnız kök profil tutar.
    assert _cfg(bot.ad)["platforms"]["api_server"]["enabled"] is False


@pytest.mark.parametrize("bot", _aktifler(), ids=lambda b: b.ad)
def test_mcp_env_credential_yolu_birim_adindan_turer(bot):
    # MCP alt süreç ortamı SÜZÜLÜR → credential dizini değişkeni geçmez; `bot_hafizasi_ara` Hindsight anahtarını
    # credential dizininden okur. Yol birim ADINDAN türer: birim yeniden adlandırılıp yol unutulursa araç sessizce
    # "credential yok" döner (Review Focus 3). Değişkenin ADI okuyucunun (`secrets.credential_oku`) sabitidir:
    # ad ayrışırsa aynı sessiz arıza (Tur 2 Minor 1).
    from meridian import secrets
    u = _ur()
    env = _cfg(bot.ad)["mcp_servers"]["meridian"]["env"]
    assert env[secrets.CREDENTIAL_DIZIN_ENV] == f"/run/credentials/{u.BOT_BIRIMI}"


def test_credential_yolunun_birimi_depoda_var():
    # Yolun adını verdiği birim depoda olmalı (G3 Task 2 ile geldi; birimin yönergeleri ve üreteç sabitleriyle
    # eşitliği tests/test_bot_agi_gecidi_v601.py'de).
    u = _ur()
    assert (KOK / "deploy/oracle-a1" / u.BOT_BIRIMI).is_file()


def test_uret_kok_profil_dosyalarini_icerir():
    # Kök dosyalar `uret()` çıktısında değilse `--kontrol` onları hiç görmez ve elle yazılmış bir kök bayatlar.
    assert {KOK_CONFIG, KOK_SOUL} <= set(_ur().uret())


def test_kok_profil_coklu_kip_aracsiz_hafizasiz():
    # Review Focus 1: `/p/` öneksiz istek kök profile düşer; araçlı ya da hafızalı bir kök veri UYDURUR (Parça 0).
    k = _kok_cfg()
    assert k["gateway"]["multiplex_profiles"] is True
    assert k["platform_toolsets"] == {"api_server": []}
    assert set(YASAK_TAKIMLAR) <= set(k["agent"]["disabled_toolsets"])
    assert "mcp_servers" not in k or (k["mcp_servers"].get("meridian") or {}).get("enabled") is False
    assert "memory" not in k


def test_kok_profil_durusu_sef_rapor_profilinden():
    # Duruş mirası: kök de aynı süreçte koşar — kanca, onay ve kapalı takımlar sef rapor profilinden AYNEN gelir.
    k, r = _kok_cfg(), _rap("sef")
    for anahtar in ("hooks", "hooks_auto_accept", "approvals", "model"):
        assert k.get(anahtar) == r.get(anahtar), anahtar
    assert k["agent"]["disabled_toolsets"] == r["agent"]["disabled_toolsets"]
    assert k["providers"]["kapi"] == r["providers"]["kapi"]
    # Eşitlik boş-boşa geçmesin: kaynakta kanca, onay ve ret listesi GERÇEKTEN var.
    assert any("meridian-guard.sh" in h.get("command", "") for h in k["hooks"]["pre_tool_call"])
    assert k["hooks_auto_accept"] is True and k["approvals"]["deny"]


def _yapraklar(d, onek=()):
    """İç içe eşlemenin yaprak yolları ve değerleri (liste, skaler ve boş eşleme yapraktır)."""
    for k, v in d.items():
        if isinstance(v, dict) and v:
            yield from _yapraklar(v, onek + (k,))
        else:
            yield onek + (k,), v


def _kok_durus_ayrisimi(kok):
    """Duruş kaynağı rapor profili (`KOK_DURUS_PROFILI`) ile kök config arasındaki ayrışmalar; boş = tutarlı.

    İKİ YÖN (Tur 2 Minor 2 — yön körlüğü): (a) kaynağın HER üst anahtarı ya miras listesinde
    (`KOK_MIRAS_ANAHTARLARI`) ya da beyanlı istisnada (`KOK_MIRAS_DISI`) olmalı — yeni bir duruş anahtarı köke
    SESSİZCE geçmez, bir karar ister; (b) miras alınan her YAPRAK kökte AYNI değerle durur — yalnız sohbet çağrı
    bütçesinin beyanlı olarak ezdiği yollar (`SOHBET_BUTCESI`) hariç (değerleri ayrı çivide)."""
    u = _ur()
    kaynak = yaml.safe_load((kok / u.RAPOR_KOK / u.KOK_DURUS_PROFILI / "config.yaml").read_text(encoding="utf-8"))
    kc = yaml.safe_load((kok / KOK_CONFIG).read_text(encoding="utf-8"))
    bulgular = [f"kapsanmayan üst anahtar: {a}" for a in kaynak
                if a not in u.KOK_MIRAS_ANAHTARLARI and a not in u.KOK_MIRAS_DISI]
    kok_yapraklari = dict(_yapraklar(kc))
    for yol, deger in _yapraklar({a: v for a, v in kaynak.items() if a in u.KOK_MIRAS_ANAHTARLARI}):
        if yol in u.SOHBET_BUTCESI:
            continue
        if yol not in kok_yapraklari:
            bulgular.append(f"kökte yok: {'.'.join(yol)}")
        elif kok_yapraklari[yol] != deger:
            bulgular.append(f"değer farklı: {'.'.join(yol)}")
    return bulgular


def test_kok_durusu_kaynagin_her_anahtarini_ayni_degerle_tasir():
    assert _kok_durus_ayrisimi(KOK) == []


def test_kok_miras_listesi_ile_istisna_ayrik_ve_istisna_kokte_kaynaktan_gelmez():
    u = _ur()
    assert not set(u.KOK_MIRAS_ANAHTARLARI) & set(u.KOK_MIRAS_DISI)
    # Beyanlı istisna "kök bunu kendisi kurar ya da hiç taşımaz" demektir: hafıza ve MCP girdisi kökte YOK.
    k = _kok_cfg()
    assert "memory" in u.KOK_MIRAS_DISI and "mcp_servers" in u.KOK_MIRAS_DISI and "memory" not in k


def test_kok_durus_ayrisimi_yeni_kaynak_anahtarini_yakalar(tmp_path):
    # POZİTİF KONTROL (Tur 2 Minor 2 mutasyonu kalıcı): kaynağa yeni bir `approvals` alt anahtarı ve yeni bir üst
    # anahtar eklenir. Bayat kök İKİSİNİ de gösterir; yeniden üretimden sonra alt anahtar mirasla geçer (duruş
    # yayılır), yeni ÜST anahtar ise listede/istisnada olmadığı için hâlâ öter — karar ister.
    import shutil
    shutil.copytree(KOK / "deploy", tmp_path / "deploy")
    u = _ur()
    kaynak = tmp_path / u.RAPOR_KOK / u.KOK_DURUS_PROFILI / "config.yaml"
    veri = yaml.safe_load(kaynak.read_text(encoding="utf-8"))
    veri["approvals"]["yeni_kural"] = "deny"
    veri["guvenlik"] = {"kip": "siki"}
    kaynak.write_text(yaml.safe_dump(veri, allow_unicode=True, sort_keys=False), encoding="utf-8")
    once = _kok_durus_ayrisimi(tmp_path)
    assert "kökte yok: approvals.yeni_kural" in once and "kapsanmayan üst anahtar: guvenlik" in once
    u.yaz(kok=tmp_path)
    assert _kok_durus_ayrisimi(tmp_path) == ["kapsanmayan üst anahtar: guvenlik"]


def test_kok_config_basligi_model_anahtari_kararini_tasir():
    # Tur 2 Minor 3 (Rol-1 hükmü): kökün `.env`ine model anahtarı BİLİNÇLİ konmaz — öneksiz istek kapıda 401 ile
    # düşer. Kararı okuyan dosyada durmazsa kök `.env`ini tohumlayan biri anahtarı "eksik" sanıp koyar.
    baslik = [ln for ln in (KOK / KOK_CONFIG).read_text(encoding="utf-8").splitlines() if ln.startswith("#")]
    assert any("BİLİNÇLİ konmaz" in ln and "401" in ln for ln in baslik), baslik


def test_kok_profil_sohbet_zaman_asimi():
    # Kök de sohbet ağ geçidinde çağrılır: rapor bütçesiyle (120 sn × 3 deneme) asılmasın.
    u, k = _ur(), _kok_cfg()
    assert k["providers"]["custom"]["request_timeout_seconds"] == u.SOHBET_ISTEK_ZAMAN_ASIMI_SN
    assert k["agent"]["api_max_retries"] == u.SOHBET_API_DENEME


def test_kok_baglam_dizini_terminal_cwd_kum_havuzu():
    # G3 dal sonu I1 (2026-09-30): ağ geçidi bağlam dosyalarını (AGENTS.md/CLAUDE.md/.cursorrules/.hermes.md) SÜREÇ
    # cwd'sinden değil `TERMINAL_CWD`den arar ve onu açılışta YALNIZ kök config'in `terminal.cwd`sinden köprüler (yoksa
    # `MESSAGING_CWD`, yoksa ev dizini). Değer ÜRETECİN çıktısında (`uret()`) ortak kum havuzu olmalı; `TERMINAL_*`
    # çoklu kipte süreç-geneli olduğu için ikincil profillere yazılmaz (okunmaz — yazılsa sahte güvence olurdu).
    u = _ur()
    cikti = u.uret()
    kok = yaml.safe_load(cikti[KOK_CONFIG].decode("utf-8"))
    assert kok.get("terminal") == {"cwd": u.BOT_KUM_HAVUZU}, kok.get("terminal")
    assert "terminal" in u.KOK_MIRAS_DISI
    for bot in _aktifler():
        profil = yaml.safe_load(cikti[f"deploy/hermes/sohbet/profiles/{bot.ad}/config.yaml"].decode("utf-8"))
        assert "terminal" not in profil, bot.ad


def _yaprak(cfg: dict, yol: tuple[str, ...]):
    for parca in yol:
        cfg = cfg[parca]
    return cfg


@pytest.mark.parametrize("goreli", [KOK_CONFIG, *(f"deploy/hermes/sohbet/profiles/{b.ad}/config.yaml"
                                                  for b in _aktifler())])
def test_sohbet_butcesinin_her_yolu_uretec_sabitiyle(goreli):
    # Task 1 yeniden inceleme (Minor): yukarıdaki çiviler yalnız `custom` zaman aşımını ve deneme sayısını ölçüyordu;
    # `openrouter` (geri dönüş evi) değeri çivisizdi. Bütçenin HER yolu, yazıldığı her config'te (kök + sohbet
    # profilleri), üretecin ADLI sabitiyle — bütçe sözlüğü boşalsa ya da bir yolu düşse döngü kör kalmasın diye
    # üç yolun varlığı da ölçülür.
    u = _ur()
    cfg = yaml.safe_load((KOK / goreli).read_text(encoding="utf-8"))
    assert {("agent", "api_max_retries"), ("providers", "custom", "request_timeout_seconds"),
            ("providers", "openrouter", "request_timeout_seconds")} <= set(u.SOHBET_BUTCESI)
    for yol, deger in u.SOHBET_BUTCESI.items():
        sabit = u.SOHBET_API_DENEME if yol[-1] == "api_max_retries" else u.SOHBET_ISTEK_ZAMAN_ASIMI_SN
        assert deger == sabit and _yaprak(cfg, yol) == sabit, ".".join(yol)


def test_kok_soul_yalniz_yonlendirir():
    s = (KOK / KOK_SOUL).read_text(encoding="utf-8")
    assert "Bu uç doğrudan kullanılmaz" in s and "/p/<bot>/" in s
    assert "Bu kök profil; lütfen bir bot seçin." in s
    # Araç ya da hafıza vaadi yok: kök araçsız ve hafızasızdır, vaat edilen yetenek uydurulur.
    katli = s.casefold()
    for vaat in ("araç", "hafıza", "notlar", "oneri_yaz", "is_iste", "bot_hafizasi_ara"):
        assert vaat not in katli, vaat


@pytest.mark.parametrize("goreli", [KOK_CONFIG, KOK_SOUL])
def test_kontrol_bayat_kok_dosyasini_yakalar(tmp_path, goreli):
    import shutil
    shutil.copytree(KOK / "deploy", tmp_path / "deploy")
    hedef = tmp_path / goreli
    hedef.write_text(hedef.read_text(encoding="utf-8") + "\n# el ile\n", encoding="utf-8")
    assert any(goreli in a and a.startswith("ayrışan:") for a in _ur().kontrol(kok=tmp_path))


def test_kontrol_eksik_kok_dosyasini_yakalar(tmp_path):
    import shutil
    shutil.copytree(KOK / "deploy", tmp_path / "deploy")
    (tmp_path / KOK_SOUL).unlink()
    assert any(KOK_SOUL in a and a.startswith("eksik:") for a in _ur().kontrol(kok=tmp_path))


def test_kontrol_sohbet_kokundeki_fazla_dosyayi_yakalar(tmp_path):
    # Sohbet kökünün TAMAMI üretecindir (kök profil + profiller): orada üretilmemiş bir dosya Hermes köküne taşınır.
    import shutil
    shutil.copytree(KOK / "deploy", tmp_path / "deploy")
    (tmp_path / "deploy/hermes/sohbet/el_ile.yaml").write_text("x: 1\n", encoding="utf-8")
    assert any("deploy/hermes/sohbet/el_ile.yaml" in a and a.startswith("fazla:")
               for a in _ur().kontrol(kok=tmp_path))


@pytest.mark.parametrize("goreli", ["deploy/hermes/sohbet/.DS_Store", "deploy/hermes/sohbet/profiles/sef/.DS_Store"])
def test_kontrol_ds_store_fazla_sayilmaz(tmp_path, goreli):
    # Tur 2 Minor 5: tarama sohbet kökünün tamamına genişledi; macOS Finder'ın `.DS_Store`u yerelde `--kontrol`u
    # sahte kırmızıya çevirirdi. İstisna YALNIZ bu ad (aşağıdaki çivi: başka gizli dosya fazla kalır).
    import shutil
    shutil.copytree(KOK / "deploy", tmp_path / "deploy")
    (tmp_path / goreli).write_bytes(b"\x00\x00\x00\x01Bud1")
    assert _ur().kontrol(kok=tmp_path) == []


def test_kontrol_baska_gizli_dosya_fazla_sayilir(tmp_path):
    import shutil
    shutil.copytree(KOK / "deploy", tmp_path / "deploy")
    (tmp_path / "deploy/hermes/sohbet/.gizli").write_text("x\n", encoding="utf-8")
    assert any("deploy/hermes/sohbet/.gizli" in a and a.startswith("fazla:") for a in _ur().kontrol(kok=tmp_path))


def test_komut_satiri_bayat_kokte_bir_doner(tmp_path):
    # Sözleşme KOMUT SATIRIdır: betik kopyası geçici ağaçta koşar (REPO = betiğin iki üstü), `meridian` PYTHONPATH'ten.
    import os
    import shutil
    shutil.copytree(KOK / "deploy", tmp_path / "deploy")
    (tmp_path / "ops").mkdir()
    shutil.copyfile(KOK / "ops/sohbet_profili_uret.py", tmp_path / "ops/sohbet_profili_uret.py")
    hedef = tmp_path / KOK_SOUL
    hedef.write_text(hedef.read_text(encoding="utf-8") + "\nel ile\n", encoding="utf-8")
    r = subprocess.run([sys.executable, "ops/sohbet_profili_uret.py", "--kontrol"], cwd=tmp_path,
                       capture_output=True, text=True, env={**os.environ, "PYTHONPATH": str(KOK)})
    assert r.returncode == 1, r.stdout + r.stderr[-2000:]
    assert KOK_SOUL in r.stdout
