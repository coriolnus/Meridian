"""v565 — TSK-064(c): iki bayat yol tarifi — sır dosyası denetimi reçetesi + pano birimi şerhi (2026-09-27).

SINIF: bir REÇETE/ŞERH bugünkü yolu değil ESKİ yolu gösteriyor. Okuyan onu izler ve yanlış yere gider;
hiçbir şey kırmızı olmaz, çünkü metin hiçbir koda karşı ölçülmüyordu.

A. `deploy/ansible/roles/meridian_a1/tasks/sir_denetimi.yml` `fail_msg`i zorunlu sır dosyalarının
   çoğu için `sir_credential_gecis.sh`i gösteriyordu. O betik 2026-09-07 KANAL geçişi aracıdır
   (ortam → LoadCredential); bugün zorunlu sır dosyalarının HEPSİ Vault Agent render hedefidir ve
   değeri `sir_rotasyon.sh --<alt> --vault` döndürür. Yeni reçete iki TEK KAYNAĞA işaret eder
   (`deploy/vault/agent.hcl` `destination` · `deploy/sir_envanteri.yaml` `rotasyon_kopyalari`) ve
   dosya-başı eşlemeyi YENİDEN YAZMAZ. Reçetenin iki adımı birer İDDİADIR; çiviler onları kaynağından
   ölçer (tek-kaynak yasası: kopya kaçınılmazsa ayrışma çivisi):
     A1 — her zorunlu sır dosyası `agent.hcl` render hedefidir (adım 1'in önkoşulu). Render hedefi
          OLMAYAN bir zorunlu yol doğduğu gün öter: reçete o dosya için yanlış olur.
     A2 — her zorunlu sır dosyası rotasyon tablosunda TEK bir alt komuta bağlıdır, o alt komut
          `sir_rotasyon.sh`in gerçek bir bayrağıdır ve sırrı kasaya bağlıdır (`vault_kv` →
          `rotasyon_siri`; adım 2'nin `--vault` kipinin önkoşulu).
     A3 — reçete dosya-başı eşleme TAŞIMAZ: envanterin somut alt komut bayrakları ve zorunlu yollar
          `fail_msg`de literal geçmez (yol `{{ item.item.yol }}` ile gelir).
   Ölçüm (2026-09-27, bu dosyanın kendisiyle): 6 zorunlu yolun 6'sı render hedefi; 6'sının 6'sı
   rotasyon tablosunda tek alt komutla bağlı (dash · openrouter ×2 · kapi · db · tenant) ve 6'sının
   sırrı kasaya bağlı (üçü birincil girdide, üçü takma addan: `bot_key_meridian` ·
   `openrouter_api_key` · `hindsight_cp_dataplane_api_key`).

B. `deploy/oracle-a1/meridian.service` şerhi elle yansımanın pano sürecinde "KALDIĞINI" söylüyordu,
   kardeşi `meridian-learn.service` de arama düğmelerinin iki birimde durma gerekçesini aynı iddiaya
   bağlıyordu. TSK-233'ten sonra pano yansımayı KOŞMAZ, istek dosyası bırakır; öğrenme süreci koşar.
     B1 — iki birimin şerhi de `reflect_now`u anmaz (eski iddianın taşıyıcısı; uç zaten hiç
          `/api/hermes/reflect_now` adını taşımadı — rota `/api/hermes/reflect`).
     B2 — pano birimindeki arama düğmeleri ÖLÜ AYAR DEĞİL ve şerh bunu kaynağa bağlı söyler: pano
          süreci sprint'i tetikler ve iki düğmeyi çocuğa devreder (`sprint.DEVREDILEN_ORTAM`);
          `HERMES_SEARCH_BUDGET` devredilmez ama pano karnesi (`analytics.hermes_scorecard` →
          `hermes.search_budget`) onu BU sürecin ortamından okur. Gerekçe değişirse (devretme kalkar,
          karne başka yerden okur) şerh bayatlar — çivi öter.
"""
from __future__ import annotations

import ast
import pathlib
import re

import yaml

REPO = pathlib.Path(__file__).resolve().parents[1]
DEFAULTS_YML = REPO / "deploy" / "ansible" / "roles" / "meridian_a1" / "defaults" / "main.yml"
SIR_DENETIMI_YML = REPO / "deploy" / "ansible" / "roles" / "meridian_a1" / "tasks" / "sir_denetimi.yml"
AGENT_HCL = REPO / "deploy" / "vault" / "agent.hcl"
ENVANTER = REPO / "deploy" / "sir_envanteri.yaml"
SIR_ROTASYON = REPO / "deploy" / "oracle-a1" / "sir_rotasyon.sh"
ANA_BIRIM = REPO / "deploy" / "oracle-a1" / "meridian.service"
OGRENME_BIRIMI = REPO / "deploy" / "oracle-a1" / "meridian-learn.service"
ANALYTICS = REPO / "meridian" / "analytics.py"

#: Pano biriminde duran arama düğmeleri (v249 `ORTAK_DUGMELER`in arama alt kümesi).
DEVREDILEN_DUGMELER = ("MERIDIAN_PARALLEL_PROBES", "MERIDIAN_SEARCH_MAX_MIN")
KARNE_DUGMESI = "HERMES_SEARCH_BUDGET"


def _zorunlu_yollar() -> list[str]:
    veri = yaml.safe_load(DEFAULTS_YML.read_text(encoding="utf-8"))
    yollar = [g["yol"] for g in veri["zorunlu_sir_dosyalari"]]
    assert len(yollar) >= 1, "zorunlu_sir_dosyalari boş okundu — ölçüm kör"
    return yollar


def _render_hedefleri() -> set[str]:
    hedefler = set(re.findall(r'^\s*destination\s*=\s*"([^"]+)"', AGENT_HCL.read_text(encoding="utf-8"),
                              re.M))
    assert hedefler, "agent.hcl'den hiç `destination` okunamadı — ölçüm kör"
    return hedefler


def _envanter() -> dict:
    return yaml.safe_load(ENVANTER.read_text(encoding="utf-8"))


def _fail_msg() -> str:
    gorevler = yaml.safe_load(SIR_DENETIMI_YML.read_text(encoding="utf-8"))
    kapilar = [g for g in gorevler
               if "ansible.builtin.assert" in g and "sir_stat" in str(g.get("loop", ""))]
    assert len(kapilar) == 1, f"sır dosyası assert kapısı TEK olmalı, bulunan: {len(kapilar)}"
    return str(kapilar[0]["ansible.builtin.assert"].get("fail_msg", ""))


def _serh(yol: pathlib.Path) -> str:
    return "\n".join(s for s in yol.read_text(encoding="utf-8").splitlines() if s.strip().startswith("#"))


# ---------------------------------------------------------------------------------------------
# A — sır dosyası denetimi reçetesi
# ---------------------------------------------------------------------------------------------


def test_A1_her_zorunlu_sir_dosyasi_agent_render_hedefi():
    """Reçete adım 1 ("dosya Vault Agent render hedefidir → önce `systemctl status vault-agent`")
    YALNIZ render hedefleri için doğrudur. Zorunlu listeye render hedefi OLMAYAN bir yol girerse
    reçete o dosya için operatörü yanlış birime gönderir — bu çivi o gün öter; çözüm ya dosyayı
    envantere (`vault_kv`) almak ya da reçeteyi ve bu çiviyi o sınıf için genişletmektir."""
    hedefler = _render_hedefleri()
    disarida = [y for y in _zorunlu_yollar() if y not in hedefler]
    assert disarida == [], (
        f"zorunlu sır dosyası Vault Agent render hedefi DEĞİL (agent.hcl destination kümesinde yok): "
        f"{disarida} — sir_denetimi.yml reçetesinin 1. adımı bu dosya için bayat")


def test_A2_her_zorunlu_sir_dosyasi_kasaya_bagli_tek_alt_komutla_doner():
    """Reçete adım 2 ("bu yolun `rotasyon_kopyalari` satırındaki `alt_komut` → `--<alt> --vault`")
    çözülebilir olmalı: yol tabloda VAR, tek alt komuta bağlı, alt komut betiğin gerçek bayrağı ve
    sır kasaya bağlı (`sir_rotasyon.sh --vault` KAPSAMI yalnız `rotasyon_siri` ile bağlı sırlardır)."""
    env = _envanter()
    kopyalar = env["rotasyon_kopyalari"]["kopyalar"]
    kasa_bagli = {g.get("rotasyon_siri") for g in env["vault_kv"]} - {None}
    # Bayrak kümesi betiğin argüman `case` DESENLERİNDEN okunur (`--kapi|--tenant|…)`), başlık şerhinden
    # DEĞİL: şerh bir bayrağı ansa da betik onu kabul etmeyebilir — ölçülen şey kabul edilen bayraktır.
    bayraklar = {b for m in re.finditer(r"^\s*((?:--[\w-]+\|)*--[\w-]+)\)", SIR_ROTASYON.read_text(encoding="utf-8"),
                                        re.M)
                 for b in m.group(1).split("|")}
    assert {"--vault", "--kuru"} <= bayraklar, f"sir_rotasyon.sh bayrak kümesi okunamadı — ölçüm kör: {bayraklar}"
    sorunlar = []
    for yol in _zorunlu_yollar():
        satirlar = [k for k in kopyalar if k.get("yol") == yol]
        if not satirlar:
            sorunlar.append(f"{yol}: rotasyon tablosunda satır YOK")
            continue
        altlar = {k.get("alt_komut") for k in satirlar}
        sirlar = {k.get("sir") for k in satirlar}
        if len(altlar) != 1 or None in altlar:
            sorunlar.append(f"{yol}: alt komut tek değil/boş {sorted(map(str, altlar))}")
            continue
        alt = next(iter(altlar))
        if f"--{alt}" not in bayraklar:
            sorunlar.append(f"{yol}: --{alt} sir_rotasyon.sh'ın kabul ettiği bir bayrak değil")
        bagsiz = sorted(s for s in sirlar if s not in kasa_bagli)
        if bagsiz:
            sorunlar.append(f"{yol}: sır kasaya BAĞLI DEĞİL (vault_kv rotasyon_siri yok): {bagsiz}")
    assert sorunlar == [], "sir_denetimi.yml reçetesinin 2. adımı çözülemiyor:\n" + "\n".join(sorunlar)


def test_A3_recete_dosya_basi_esleme_tasimaz():
    """Tek-kaynak: hangi dosyanın hangi alt komutla döndüğü envanterde yaşar. `fail_msg` somut bir
    alt komut bayrağı (`--dash` …) ya da somut bir zorunlu yol taşırsa eşlemenin İKİNCİ kopyası
    doğar ve envanter değişince sessizce ayrışır (eski reçetenin `/etc/meridian/dash_token` →
    `--dash` özel dalı tam bu kopyaydı)."""
    fail_msg = _fail_msg()
    altlar = sorted({k["alt_komut"] for k in _envanter()["rotasyon_kopyalari"]["kopyalar"]})
    assert altlar, "envanterden alt komut okunamadı — ölçüm kör"
    somut = [f"--{a}" for a in altlar if re.search(rf"(?<![\w-])--{re.escape(a)}(?![\w-])", fail_msg)]
    assert somut == [], f"fail_msg dosya-başı eşleme taşıyor (somut alt komut bayrağı): {somut}"
    literal = [y for y in _zorunlu_yollar() if y in fail_msg]
    assert literal == [], f"fail_msg zorunlu yolu literal taşıyor (yol `{{{{ item.item.yol }}}}` ile gelmeli): {literal}"
    assert "--<alt>" in fail_msg, "reçete alt komut yer tutucusunu (`--<alt>`) taşımıyor"


# ---------------------------------------------------------------------------------------------
# B — pano birimi şerhi (TSK-233 sonrası)
# ---------------------------------------------------------------------------------------------


def test_B1_birim_serhleri_elle_yansimayi_pano_surecine_baglamaz():
    """TSK-233: pano ucu yansımayı KOŞMAZ, istek dosyası bırakır; `reflect_now` pano sürecinin
    yolu değildir. İki birimin şerhi de bu eski iddiayı taşımaz."""
    for birim in (ANA_BIRIM, OGRENME_BIRIMI):
        assert "reflect_now" not in _serh(birim), (
            f"{birim.name} şerhi elle yansımayı hâlâ `reflect_now`a / pano sürecine bağlıyor (TSK-233 öncesi yol)")
    assert "meridian-learn" in _serh(ANA_BIRIM), "pano birimi şerhi elle yansımanın nerede koştuğunu söylemiyor"


def test_B2_pano_birimi_arama_dugmeleri_gerekcesi_kaynakla_uyumlu():
    """Pano birimindeki arama düğmeleri ölü ayar DEĞİL; şerh gerekçeyi adıyla söyler ve gerekçe
    kaynaktan ölçülür: iki düğme sprint çocuğuna devredilir, üçüncüsü pano karnesinde okunur."""
    from meridian import sprint

    serh = _serh(ANA_BIRIM)
    assert "DEVREDILEN_ORTAM" in serh and "hermes_scorecard" in serh, (
        "pano birimi şerhi arama düğmelerinin gerekçesini (sprint devri + karne) adıyla söylemiyor")
    eksik = [d for d in DEVREDILEN_DUGMELER if d not in sprint.DEVREDILEN_ORTAM]
    assert eksik == [], (f"şerh bu düğmelerin sprint'e devredildiğini söylüyor ama DEVREDILEN_ORTAM'da yoklar: "
                         f"{eksik} — pano birimindeki satırlar ölü ayar olabilir, şerh bayat")
    assert KARNE_DUGMESI not in sprint.DEVREDILEN_ORTAM, (
        f"{KARNE_DUGMESI} artık sprint'e devrediliyor — şerhin 'karne' gerekçesi eksik kaldı")
    agac = ast.parse(ANALYTICS.read_text(encoding="utf-8"))
    fn = next((d for d in agac.body if isinstance(d, ast.FunctionDef) and d.name == "hermes_scorecard"), None)
    assert fn is not None, "analytics.hermes_scorecard yok — şerhin karne gerekçesi bayat"
    cagrilar = {n.func.attr for n in ast.walk(fn)
                if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)}
    assert "search_budget" in cagrilar, (
        f"hermes_scorecard artık search_budget çağırmıyor — {KARNE_DUGMESI} pano sürecinde okunmuyor olabilir, "
        f"şerh bayat")
