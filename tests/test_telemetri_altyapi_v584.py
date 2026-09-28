"""v584 — TSK-020 UYGULA-9 Faz A: gecikme telemetrisi ALTYAPISI (Prometheus + node_exporter + Grafana; docker;
yalnız 127.0.0.1) — birim · yapılandırma · sır zinciri · A0 rolü çivileri (2026-09-28).

TASARIM (bağlayıcı, operatör ONAYLI 2026-09-28): `docs/TASARIM-TELEMETRI-PROMETHEUS-2026-09-28.md` — T1 (docker, pinli
imaj, loopback), T2 (saklama tavanı; TSDB `/` altında, `/opt/veri` %82), T3 (kazıma hedefleri), T5 (Grafana yönetici
parolası: Vault → `LoadCredential` → dosyadan okuma), T6 (A0 rolü; birimler İLK GÜN `etkin_birimler`e GİRMEZ), §2
(ikinci alarm kanalı YOK). Motor (`meridian/`) bu fazda DEĞİŞMEZ — histogramlar Faz B'nin işi.

NE ÖLÇÜLÜR — her bölüm bir iddia; beklenen değerler DEPODAN türetilir (tek istisna: A1 port ölçümü, depoda yok):
  A. Birimler. Üç docker birimi `--network host` ile; imaj `depo:tam-sürüm@sha256:<64 hex>` (`latest` yok); dinleme
     127.0.0.1 ve A1'de ÖLÇÜLMÜŞ BOŞ bir porta (9090/9091 APISIX'in); bellek tavanı İKİ katmanda — birimin
     `MemoryMax=`ı yalnız docker İSTEMCİSİNİN cgroup'unu sınırlar, konteyner dockerd'nin cgroup'unda koşar, gerçek
     tavan `--memory`dir; `Restart=on-failure`; konteyner imajın kendi kullanıcısıyla (root/ayrıcalık bayrağı yok);
     bağlamalar `--mount` biçiminde (kaynak YOKSA `-v` sessizce root sahipli bir DİZİN yaratır, `--mount` DÜŞER) ve
     veri kökü dışındaki her bağlama salt-okur.
  B. Prometheus. Kazıma 30 s; tam üç hedef, her biri TEK KAYNAĞINDAN (APISIX `KAPI_PROMETHEUS_URL`, meridian A0
     `saglik_url` soketi, node_exporter kendi biriminin dinleme adresi); saklama 30d + 2GB YAPILANDIRMADA — 3.15.0'da
     iki bayrak `[DEPRECATED]` (yapılandırma alanı bayrağa üstün gelir; ikisi birden yazılırsa aynı gerçeğin iki
     kopyası olurdu); TSDB veri kökünde; `alerting:`/`rule_files:` yok, depoda Alertmanager yok.
  C. Grafana. Anonim · kayıt · birleşik uyarı KAPALI; parola YALNIZ `GF_SECURITY_ADMIN_PASSWORD__FILE` ile (değer
     satırı, değersiz `-e` ve ortam dosyası YASAK — değersiz `-e` değeri docker istemcisinin ortamından çeker);
     credential zincirinin halkaları birbirine EŞİT: Vault hedefi = `LoadCredential` kaynağı → boşluk kapısı →
     tmpfs kopya (0400, konteyner kullanıcısına) → salt-okur `--mount` → `__FILE` yolu; sağlayıcılar iç tutarlı;
     pano brief'in panellerini taşır.
  D. A0 rolü. Birimler `birim_kaynaklari` glob'unda, `etkin_birimler`de DEĞİL; drop-in dizini listede;
     yapılandırma listesi `deploy/telemetri` ağacıyla İKİ YÖNLÜ eşit; veri dizinleri konteyner kullanıcı kimliğiyle
     ve ata önce; birimlerdeki literal yollar/kimlikler defaults ile eşit (birimler ŞABLONSUZ kopyalanır — kopya
     kaçınılmaz, bu bölüm ayrışma çivisidir); [F9] içerik aynası birim + yapılandırma çiftlerini taşır.
  E. Pozitif kontrol. Her denetçi, gerçek dosyanın bellekte bozulmuş kopyasında ÖTER — çivi yeşili kanıt değildir.
  F. İzin-denetimli sır kapısı (tur 2, inceleme O-1). Rotasyon dışı bırakılan (v447 `ROTASYON_DISI_KREDENSIYELLER`) her
     credential kaynağı A0 `izin_denetimli_sir_dosyalari` listesindedir — rotasyon dışı ≠ denetim dışı; liste ile
     `sir_denetimi.yml`deki kapı eşleşir (dosya YOKSA beyan satırıyla geç, VARSA sahip/grup/mod DUR); beklenen
     mod/sahip/grup Vault Agent şablonunun ürettiğiyle (agent.hcl `perms` + envanter + agent biriminin kimliği) AYNI.

BİLİNEN SINIR (dürüst beyan): A1'e bağlantı YOK. Konteyner kullanıcı kimlikleri (prometheus/node-exporter `nobody`,
grafana `472`) imaj YAPILANDIRMASINDAN okundu (Docker Hub registry, arm64 bildirimi, 2026-09-28); `nobody`nun 65534
olduğu imajın passwd dosyasından ÖLÇÜLMEDİ — Rol-1 A1'de ilk çekimde `docker run --rm --entrypoint id <imaj>` ile
doğrular (RUNBOOK telemetri bölümü).

Numara v584: v583 başka dalda alındı (Rol-1 bildirimi 2026-09-28; `ls tests | grep v584` boş). Bu dosya `state/`e
dokunmaz, ağa çıkmaz, `meridian` paketini ithal ETMEZ (`KAPI_PROMETHEUS_URL` kaynak METNİNDEN okunur).
"""
from __future__ import annotations

import dataclasses
import glob
import json
import pathlib
import posixpath
import re
import shlex
import urllib.parse

import pytest
import yaml

# Tek-kaynak: birim sözdizimi (yorum + `\\` devamı) ve yönerge ayrıştırması v553'te yaşar.
from tests.test_sertlesmis_birim_yazim_yolu_v553 import _yonergeler
# Tek-kaynak: [F9] çiftlerinin sökücüsü v452'de yaşar (v451 de oradan ithal eder).
from tests.test_ansible_dagit_v452 import f9_ciftleri as _f9_ciftleri
# Tek-kaynak: rotasyon dışı credential beyanı ve drop-in `LoadCredential` haritası v447'de yaşar (F bölümü).
from tests.test_sir_rotasyon_v447 import (  # noqa: E402
    KRED_KAYNAKLARI as _KRED_KAYNAKLARI,
    ROTASYON_DISI_KREDENSIYELLER as _ROTASYON_DISI,
)

KOK = pathlib.Path(__file__).resolve().parent.parent
DEPLOY = KOK / "deploy"
TELEMETRI = DEPLOY / "telemetri"
ANSIBLE = DEPLOY / "ansible"
ROL = ANSIBLE / "roles" / "meridian_a1"
DEFAULTS = ROL / "defaults" / "main.yml"
BIRIMLER_YML = ROL / "tasks" / "birimler.yml"
DIZINLER_YML = ROL / "tasks" / "dizinler.yml"
ENVANTER = DEPLOY / "sir_envanteri.yaml"
AGENT_HCL = DEPLOY / "vault" / "agent.hcl"
AGENT_POLITIKA = DEPLOY / "vault" / "policies" / "meridian-agent.hcl"
SIR_DENETIMI_YML = ROL / "tasks" / "sir_denetimi.yml"
AGENT_BIRIMI = DEPLOY / "vault" / "vault-agent.service"
API_PY = KOK / "meridian" / "api.py"
PROMETHEUS_YML = TELEMETRI / "prometheus" / "prometheus.yml"
GRAFANA_DROPIN_DIZINI = TELEMETRI / "meridian-grafana.service.d"
GRAFANA_SAGLAYICI = TELEMETRI / "grafana" / "provisioning"
GRAFANA_PANOLAR = TELEMETRI / "grafana" / "panolar"

#: A1 port ölçümü (Rol-1, salt-okur `ss -ltn`, 2026-09-28) — depodan türetilemeyen TEK girdi.
#: 9090 APISIX kontrol API'si, 9091 APISIX prometheus eklentisi (Prometheus'un varsayılanı ÇAKIŞIR).
OLCULEN_DOLU_PORTLAR = frozenset({9090, 9091})
OLCULEN_BOS_PORTLAR = frozenset({3000, 9092, 9093, 9095, 9100, 9101})

#: Tasarım T1 + brief: birim adı → (imaj deposu, bellek tavanı).
BIRIMLER: dict[str, tuple[str, str]] = {
    "meridian-prometheus": ("prom/prometheus", "512M"),
    "meridian-node-exporter": ("prom/node-exporter", "64M"),
    "meridian-grafana": ("grafana/grafana", "256M"),
}
GRAFANA = "meridian-grafana"
PROMETHEUS = "meridian-prometheus"
NODE = "meridian-node-exporter"

#: Vault envanterindeki girdi adı (tek kaynak `deploy/sir_envanteri.yaml` `vault_kv`).
PAROLA_ADI = "grafana_admin_parola"
PAROLA_ORTAM = "GF_SECURITY_ADMIN_PASSWORD"

_IMAJ = re.compile(r"(?P<depo>[a-z0-9][a-z0-9./_-]*):(?P<etiket>[A-Za-z0-9._-]+)@sha256:(?P<ozet>[0-9a-f]{64})")
_TAM_SURUM = re.compile(r"v?\d+\.\d+\.\d+")

#: `docker run` seçeneklerinden DEĞER alanlar (değer ayrı jetonda gelebilir).
_DEGERLI = frozenset({
    "--name", "--network", "--net", "-v", "--volume", "--mount", "-e", "--env", "--env-file", "--memory", "-m",
    "-u", "--user", "--pid", "--ipc", "--entrypoint", "--cap-add", "--security-opt", "--userns", "--device",
    "-p", "--publish", "-w", "--workdir",
})
#: Konteyneri root'a ya da ev sahibi ad alanlarına bağlayan bayraklar — brief: "konteyner kullanıcısı root DEĞİL".
_AYRICALIK = frozenset({
    "-u", "--user", "--privileged", "--cap-add", "--pid", "--ipc", "--userns", "--device", "--security-opt",
})


# =================================================================================================
# Ayrıştırıcılar
# =================================================================================================

@dataclasses.dataclass
class _Run:
    secenekler: list[tuple[str, str | None]]
    imaj: str
    argumanlar: list[str]


def _docker_run(execstart: str) -> _Run:
    j = shlex.split(execstart)
    assert len(j) > 2 and j[0].endswith("/docker") and j[1] == "run", f"docker run değil: {j[:2]}"
    i, sec = 2, []
    while i < len(j) and j[i].startswith("-"):
        t = j[i]
        if t.startswith("--") and "=" in t:
            ad, deg = t.split("=", 1)
            sec.append((ad, deg))
            i += 1
        elif t in _DEGERLI:
            sec.append((t, j[i + 1]))
            i += 2
        else:
            sec.append((t, None))
            i += 1
    assert i < len(j), "imaj jetonu yok"
    return _Run(sec, j[i], j[i + 1:])


def _yorumsuz(metin: str) -> str:
    return "\n".join(s for s in metin.splitlines() if s.strip()[:1] not in ("#", ";"))


def _degerler(metin: str, bolum: str, anahtar: str) -> list[str]:
    return [d for b, a, d in _yonergeler(metin) if b == bolum and a == anahtar]


def _servis_degerleri(metin: str, anahtar: str) -> list[str]:
    return _degerler(metin, "Service", anahtar)


def _tek(metin: str, anahtar: str) -> str | None:
    v = _servis_degerleri(metin, anahtar)
    return v[0] if len(v) == 1 else None


def _ortam(run: _Run) -> dict[str, str | None]:
    """`-e AD=değer` → {AD: değer}; değersiz `-e AD` → {AD: None} (istemci ortamından çekilir)."""
    out: dict[str, str | None] = {}
    for a, d in run.secenekler:
        if a in ("-e", "--env") and d is not None:
            ad, esit, deg = d.partition("=")
            out[ad] = deg if esit else None
    return out


def _mountlar(run: _Run) -> list[dict[str, str]]:
    out = []
    for a, d in run.secenekler:
        if a == "--mount" and d is not None:
            alanlar: dict[str, str] = {}
            for parca in d.split(","):
                k, esit, v = parca.partition("=")
                alanlar[k] = v if esit else "true"
            out.append(alanlar)
    return out


def _salt_okur(m: dict[str, str]) -> bool:
    return (m.get("readonly") or m.get("ro") or "false").lower() in ("true", "1")


def _kaynak(m: dict[str, str]) -> str:
    return m.get("source") or m.get("src") or ""


def _hedef(m: dict[str, str]) -> str:
    return m.get("target") or m.get("destination") or m.get("dst") or ""


def _altinda(yol: str, kok: str) -> bool:
    yol, kok = posixpath.normpath(yol), posixpath.normpath(kok)
    return yol == kok or yol.startswith(kok.rstrip("/") + "/")


def _dinleme(ad: str, run: _Run) -> tuple[str | None, int]:
    if ad == GRAFANA:
        env = _ortam(run)
        port = env.get("GF_SERVER_HTTP_PORT")
        return env.get("GF_SERVER_HTTP_ADDR"), int(port) if port and port.isdigit() else -1
    adr = [x.split("=", 1)[1] for x in run.argumanlar if x.startswith("--web.listen-address=")]
    if len(adr) != 1:
        return None, -1
    host, _, port = adr[0].rpartition(":")
    return host, int(port) if port.isdigit() else -1


def _birim_metni(ad: str) -> str:
    return (TELEMETRI / f"{ad}.service").read_text(encoding="utf-8")


def _run(ad: str, metin: str | None = None) -> _Run:
    es = _tek(metin if metin is not None else _birim_metni(ad), "ExecStart")
    assert es is not None, f"{ad}: ExecStart TEK değil"
    return _docker_run(es)


def _defaults() -> dict:
    return yaml.safe_load(DEFAULTS.read_text(encoding="utf-8"))


def _veri_koku() -> str:
    return str(_defaults()["telemetri_veri_dizini"])


def _yapilandirma_koku() -> str:
    return str(_defaults()["telemetri_yapilandirma_dizini"])


def _grafana_dropin_metni() -> str:
    confs = sorted(GRAFANA_DROPIN_DIZINI.glob("*.conf"))
    assert confs, f"{GRAFANA_DROPIN_DIZINI}: drop-in yok"
    return "\n".join(p.read_text(encoding="utf-8") for p in confs)


# =================================================================================================
# Denetçiler — gerçek dosya ve bellekte bozulmuş kopya AYNI fonksiyondan geçer (E bölümü)
# =================================================================================================

def _birim_bulgulari(ad: str, metin: str, veri_koku: str) -> list[str]:
    b: list[str] = []
    es = _tek(metin, "ExecStart")
    if es is None:
        return [f"{ad}: ExecStart TEK değil"]
    run = _docker_run(es)
    depo, bellek = BIRIMLER[ad]
    if ("--network", "host") not in run.secenekler:
        b.append(f"{ad}: `--network host` yok")
    if ("--name", ad) not in run.secenekler or ("--rm", None) not in run.secenekler:
        b.append(f"{ad}: `--rm --name {ad}` yok (ExecStop/ExecStartPre konteyneri adıyla bulur)")
    m = _IMAJ.fullmatch(run.imaj)
    if not m:
        b.append(f"{ad}: imaj pinli değil (`depo:sürüm@sha256:<64 hex>` bekleniyor): {run.imaj}")
    else:
        if m["depo"] != depo:
            b.append(f"{ad}: imaj deposu {m['depo']} != {depo}")
        if not _TAM_SURUM.fullmatch(m["etiket"]):
            b.append(f"{ad}: etiket tam sürüm değil (latest/kayan etiket yasak): {m['etiket']}")
    if re.search(r"(?<![\w.-])latest(?![\w.-])", _yorumsuz(metin)):
        b.append(f"{ad}: `latest` geçiyor")
    host, port = _dinleme(ad, run)
    if host != "127.0.0.1":
        b.append(f"{ad}: dinleme loopback değil: {host!r}")
    if port in OLCULEN_DOLU_PORTLAR:
        b.append(f"{ad}: port {port} A1'de DOLU (APISIX)")
    elif port not in OLCULEN_BOS_PORTLAR:
        b.append(f"{ad}: port {port} A1'de ölçülmüş boş portlardan değil")
    if re.search(r"0\.0\.0\.0|\[::\]", _yorumsuz(metin)):
        b.append(f"{ad}: tüm arayüzlere bağlama (0.0.0.0/[::]) geçiyor")
    if _tek(metin, "MemoryMax") != bellek:
        b.append(f"{ad}: MemoryMax={_tek(metin, 'MemoryMax')!r} != {bellek}")
    mem = [d for a, d in run.secenekler if a in ("--memory", "-m")]
    if len(mem) != 1 or str(mem[0]).upper() != bellek:
        b.append(f"{ad}: konteyner `--memory` tavanı {mem} != {bellek} (MemoryMax yalnız istemciyi sınırlar)")
    if _tek(metin, "Restart") != "on-failure":
        b.append(f"{ad}: Restart != on-failure")
    for a, _ in run.secenekler:
        if a in _AYRICALIK:
            b.append(f"{ad}: kullanıcı/ayrıcalık bayrağı {a} (konteyner imajın kendi kullanıcısıyla koşar)")
        if a in ("-v", "--volume"):
            b.append(f"{ad}: `{a}` bağlaması (kaynak yoksa docker root sahipli DİZİN yaratır) — `--mount` kullan")
    for mnt in _mountlar(run):
        if mnt.get("type") != "bind" or not _kaynak(mnt).startswith("/") or not _hedef(mnt).startswith("/"):
            b.append(f"{ad}: bağlama biçimsiz: {mnt}")
        elif not _altinda(_kaynak(mnt), veri_koku) and not _salt_okur(mnt):
            b.append(f"{ad}: {_kaynak(mnt)} veri kökü dışında ve salt-okur DEĞİL")
    return b


def _prometheus_bulgulari(cfg_metni: str, birim_metni: str, veri_koku: str, yap_koku: str) -> list[str]:
    b: list[str] = []
    cfg = yaml.safe_load(cfg_metni) or {}
    if (cfg.get("global") or {}).get("scrape_interval") != "30s":
        b.append("kazıma aralığı 30s değil")
    for yasak in ("alerting", "rule_files"):
        if yasak in cfg:
            b.append(f"`{yasak}:` bloğu var (ikinci alarm kanalı yasağı)")
    ret = ((cfg.get("storage") or {}).get("tsdb") or {}).get("retention") or {}
    if ret.get("time") != "30d" or ret.get("size") != "2GB":
        b.append(f"saklama tavanı 30d+2GB değil: {ret}")
    run = _docker_run(_tek(birim_metni, "ExecStart") or "")
    if any(x.startswith("--storage.tsdb.retention") for x in run.argumanlar):
        b.append("saklama BAYRAKLA da verilmiş (3.15.0'da DEPRECATED; yapılandırmayla iki kopya)")
    mnt = {_hedef(m): m for m in _mountlar(run)}
    tsdb = [x.split("=", 1)[1] for x in run.argumanlar if x.startswith("--storage.tsdb.path=")]
    if len(tsdb) != 1 or tsdb[0] not in mnt or _kaynak(mnt[tsdb[0]]) != f"{veri_koku}/prometheus":
        b.append(f"TSDB yolu veri kökündeki `prometheus` dizinine bağlı değil: {tsdb}")
    elif _altinda(_kaynak(mnt[tsdb[0]]), "/opt/veri"):
        b.append("TSDB /opt/veri altında (disk %82, DISK_ESIK alarmı)")
    conf = [x.split("=", 1)[1] for x in run.argumanlar if x.startswith("--config.file=")]
    if (len(conf) != 1 or conf[0] not in mnt or not _salt_okur(mnt[conf[0]])
            or _kaynak(mnt[conf[0]]) != f"{yap_koku}/prometheus/prometheus.yml"):
        b.append(f"--config.file salt-okur bağlanan depo yapılandırmasını göstermiyor: {conf}")
    return b


def _parola_bulgulari(birim_metni: str, dropin_metni: str) -> list[str]:
    b: list[str] = []
    run = _docker_run(_tek(birim_metni, "ExecStart") or "")
    env = _ortam(run)
    if PAROLA_ORTAM in env:
        b.append(f"`{PAROLA_ORTAM}` konteyner ortamında (değerli ya da değersiz — değer istemci ortamından gelir)")
    dosya = env.get(PAROLA_ORTAM + "__FILE")
    if not dosya or not dosya.startswith("/"):
        b.append(f"`{PAROLA_ORTAM}__FILE` yok ya da mutlak yol değil: {dosya!r}")
    if any(a == "--env-file" for a, _ in run.secenekler):
        b.append("`--env-file` var (değer kanalı ortam dosyasına açılır)")
    for metin in (birim_metni, dropin_metni):
        if _servis_degerleri(metin, "EnvironmentFile"):
            b.append("`EnvironmentFile=` var (değer kanalı ortam dosyasına açılır)")
        for atama in _servis_degerleri(metin, "Environment"):
            if "GF_SECURITY" in atama:
                b.append("`Environment=` Grafana güvenlik ayarı taşıyor")
        if re.search(rf"{PAROLA_ORTAM}(?!__FILE)", _yorumsuz(metin)):
            b.append(f"`{PAROLA_ORTAM}` `__FILE` sonekisiz geçiyor")
    return b


def _prom_ifadeleri() -> list[tuple[str, str]]:
    """(panel başlığı, ifade) — bütün panolardaki bütün hedefler."""
    out = []
    for p in sorted(GRAFANA_PANOLAR.glob("*.json")):
        pano = json.loads(p.read_text(encoding="utf-8"))
        for panel in pano.get("panels", []):
            for h in panel.get("targets", []):
                out.append((panel.get("title", ""), h.get("expr", "")))
    return out


# =================================================================================================
# A — birimler
# =================================================================================================

def test_A1_uc_docker_birimi_VAR_ve_kurallari_TASIR():
    bulunan = {p.stem for p in TELEMETRI.glob("*.service")}
    assert bulunan == set(BIRIMLER), f"deploy/telemetri birim kümesi ayrıştı: {sorted(bulunan)}"
    bulgular = [x for ad in BIRIMLER for x in _birim_bulgulari(ad, _birim_metni(ad), _veri_koku())]
    assert bulgular == [], "birim kural ihlalleri:\n" + "\n".join(bulgular)


def test_A2_ExecStartPre_ve_ExecStop_konteyneri_ADIYLA_yonetir():
    for ad in BIRIMLER:
        metin = _birim_metni(ad)
        assert f"-/usr/bin/docker rm -f {ad}" in _servis_degerleri(metin, "ExecStartPre"), ad
        assert _tek(metin, "ExecStop") == f"/usr/bin/docker stop {ad}", ad
        assert "docker.service" in " ".join(_degerler(metin, "Unit", "Requires")), ad


def test_A3_portlar_BIRBIRINDEN_ayri():
    portlar = [_dinleme(ad, _run(ad))[1] for ad in BIRIMLER]
    assert len(set(portlar)) == len(portlar), f"iki birim aynı portta: {portlar}"


def test_A4_node_exporter_ev_sahibi_yollari_SALT_OKUR_ve_yol_bayraklari_baglamalara_esit():
    """Brief: `/proc`, `/sys`, `/` salt-okur. `--pid host` YOK (Karar): toplayıcı bağlama tablosunu
    `<procfs>/1/mountinfo`dan okur (node_exporter v1.12.1 filesystem toplayıcısı) ve ev sahibinin procfs'i
    bağlandığında `1` ev sahibinin init'idir — ad alanı paylaşımı gereksiz ayrıcalık olurdu."""
    run = _run(NODE)
    baglar = {_kaynak(m): m for m in _mountlar(run)}
    assert set(baglar) == {"/proc", "/sys", "/"}, f"node_exporter bağlamaları: {sorted(baglar)}"
    assert all(_salt_okur(m) for m in baglar.values()), "node_exporter bağlaması salt-okur değil"
    for bayrak, kaynak in (("--path.procfs", "/proc"), ("--path.sysfs", "/sys"), ("--path.rootfs", "/")):
        deger = [x.split("=", 1)[1] for x in run.argumanlar if x.startswith(bayrak + "=")]
        assert deger == [_hedef(baglar[kaynak])], f"{bayrak} bağlama hedefini göstermiyor: {deger}"


# =================================================================================================
# B — Prometheus
# =================================================================================================

def _kapi_prometheus_url() -> str:
    m = re.search(r'^KAPI_PROMETHEUS_URL\s*=\s*"([^"]+)"', API_PY.read_text(encoding="utf-8"), re.M)
    assert m, "meridian/api.py'de KAPI_PROMETHEUS_URL okunamadı — ölçüm kör"
    return m.group(1)


def _isler() -> dict[str, tuple[str, list[str]]]:
    cfg = yaml.safe_load(PROMETHEUS_YML.read_text(encoding="utf-8"))
    out = {}
    for j in cfg["scrape_configs"]:
        hedefler = [t for sc in j.get("static_configs", []) for t in sc.get("targets", [])]
        out[j["job_name"]] = (j.get("metrics_path", "/metrics"), hedefler)
    return out


def test_B1_kural_seti_saklama_TSDB_alarm_YOK():
    bulgular = _prometheus_bulgulari(PROMETHEUS_YML.read_text(encoding="utf-8"), _birim_metni(PROMETHEUS),
                                     _veri_koku(), _yapilandirma_koku())
    assert bulgular == [], "Prometheus kural ihlalleri:\n" + "\n".join(bulgular)


def test_B2_UC_kazima_hedefi_TEK_KAYNAKLARINDAN():
    isler = _isler()
    assert set(isler) == {"apisix", "meridian", "node"}, f"kazıma işleri: {sorted(isler)}"
    yol, hedef = isler["apisix"]
    assert [f"http://{h}{yol}" for h in hedef] == [_kapi_prometheus_url()], "APISIX hedefi KAPI_PROMETHEUS_URL'den ayrıştı"
    yol, hedef = isler["meridian"]
    assert yol == "/metrics" and hedef == [urllib.parse.urlparse(_defaults()["saglik_url"]).netloc], (
        f"meridian hedefi A0 `saglik_url` soketinden ayrıştı: {hedef}")
    host, port = _dinleme(NODE, _run(NODE))
    assert isler["node"] == ("/metrics", [f"{host}:{port}"]), "node hedefi node_exporter dinlemesinden ayrıştı"
    for _yol, hs in isler.values():
        assert all(h.startswith("127.0.0.1:") for h in hs), f"loopback dışı hedef: {hs}"


def test_B3_depoda_Alertmanager_ve_grafana_uyari_saglayicisi_YOK():
    adlar = [str(p.relative_to(KOK)) for p in DEPLOY.rglob("*") if "alertmanager" in p.name.lower()]
    assert adlar == [], f"Alertmanager artefaktı: {adlar}"
    for p in TELEMETRI.rglob("*"):
        if p.is_file():
            assert "alertmanager" not in _yorumsuz(p.read_text(encoding="utf-8")).lower(), p
    assert sorted(d.name for d in GRAFANA_SAGLAYICI.iterdir()) == ["dashboards", "datasources"], (
        "Grafana sağlayıcısında veri kaynağı + pano dışında dizin (uyarı/kanal sağlayıcısı yasak)")


# =================================================================================================
# C — Grafana
# =================================================================================================

def test_C1_anonim_kayit_birlesik_uyari_KAPALI():
    env = _ortam(_run(GRAFANA))
    for ad in ("GF_AUTH_ANONYMOUS_ENABLED", "GF_USERS_ALLOW_SIGN_UP", "GF_UNIFIED_ALERTING_ENABLED"):
        assert env.get(ad) == "false", f"{ad}={env.get(ad)!r} (false bekleniyor)"


def test_C2_parola_YALNIZ_FILE_ile():
    bulgular = _parola_bulgulari(_birim_metni(GRAFANA), _grafana_dropin_metni())
    assert bulgular == [], "parola kanalı ihlalleri:\n" + "\n".join(bulgular)


def _vault_girdisi() -> dict:
    kv = yaml.safe_load(ENVANTER.read_text(encoding="utf-8"))["vault_kv"]
    g = [x for x in kv if x.get("ad") == PAROLA_ADI]
    assert len(g) == 1, f"vault_kv'de {PAROLA_ADI} TEK değil: {len(g)}"
    return g[0]


def test_C3_credential_zincirinin_HALKALARI_esit():
    d = _defaults()
    hedef = _vault_girdisi()["hedef"]
    dropin = _grafana_dropin_metni()
    lc = _servis_degerleri(dropin, "LoadCredential")
    assert lc == [f"{PAROLA_ADI}:{hedef}"], f"LoadCredential Vault hedefine bağlı değil: {lc}"
    birim = _birim_metni(GRAFANA)
    rd = _tek(birim, "RuntimeDirectory")
    assert rd, "RuntimeDirectory yok (tmpfs kopyanın dizini)"
    tmpfs_kopya = f"/run/{rd}/{PAROLA_ADI}"
    kapi = f"/usr/bin/test -s %d/{PAROLA_ADI}"
    kopya = (f"/usr/bin/install -m 0400 -o {d['telemetri_grafana_uid']} -g {d['telemetri_grafana_gid']} "
             f"%d/{PAROLA_ADI} {tmpfs_kopya}")
    pre = _servis_degerleri(dropin, "ExecStartPre")
    assert kapi in pre and kopya in pre, f"boşluk kapısı / tmpfs kopyası yok:\n{pre}"
    assert pre.index(kapi) < pre.index(kopya), "boşluk kapısı kopyadan SONRA (boş parola kopyalanırdı)"
    run = _run(GRAFANA)
    hedefe_giden = [m for m in _mountlar(run) if _kaynak(m) == tmpfs_kopya]
    assert len(hedefe_giden) == 1 and _salt_okur(hedefe_giden[0]), "tmpfs kopya salt-okur bağlanmıyor"
    assert _ortam(run).get(PAROLA_ORTAM + "__FILE") == _hedef(hedefe_giden[0]), "__FILE bağlama hedefinden ayrıştı"
    ajan = AGENT_HCL.read_text(encoding="utf-8")
    assert re.search(rf'destination\s*=\s*"{re.escape(hedef)}"\s*\n\s*perms\s*=\s*0400', ajan), (
        "agent.hcl bu hedef için 0400 şablon taşımıyor — `ops/vault_politika_uret.py --uygula` koşulmadı mı?")
    assert f'path "secret/data/meridian/{PAROLA_ADI}"' in AGENT_POLITIKA.read_text(encoding="utf-8")


def test_C4_saglayicilar_IC_TUTARLI():
    run = _run(GRAFANA)
    mnt = {_kaynak(m): m for m in _mountlar(run)}
    yk = _yapilandirma_koku()
    sag = mnt.get(f"{yk}/grafana/provisioning")
    assert sag and _salt_okur(sag) and _hedef(sag) == "/etc/grafana/provisioning", "sağlayıcı bağlaması"
    pano = mnt.get(f"{yk}/grafana/panolar")
    assert pano and _salt_okur(pano), "pano dizini salt-okur bağlanmıyor"
    veri = yaml.safe_load(next(GRAFANA_SAGLAYICI.glob("datasources/*.yaml")).read_text(encoding="utf-8"))
    kaynaklar = veri["datasources"]
    assert len(kaynaklar) == 1, "tek veri kaynağı bekleniyor"
    ds = kaynaklar[0]
    host, port = _dinleme(PROMETHEUS, _run(PROMETHEUS))
    assert ds["type"] == "prometheus" and ds["url"] == f"http://{host}:{port}", ds
    saglayicilar = yaml.safe_load(next(GRAFANA_SAGLAYICI.glob("dashboards/*.yaml")).read_text(encoding="utf-8"))
    yollar = [p["options"]["path"] for p in saglayicilar["providers"]]
    assert yollar == [_hedef(pano)], f"pano sağlayıcı yolu bağlama hedefinden ayrıştı: {yollar}"
    panolar = sorted(GRAFANA_PANOLAR.glob("*.json"))
    assert panolar, "pano JSON'u yok"
    for p in panolar:
        for panel in json.loads(p.read_text(encoding="utf-8"))["panels"]:
            assert panel["datasource"]["uid"] == ds["uid"], (p.name, panel.get("title"))
            for h in panel["targets"]:
                assert h["datasource"]["uid"] == ds["uid"], (p.name, panel.get("title"))


def test_C5_pano_brief_panellerini_TASIR():
    ifadeler = [e for _, e in _prom_ifadeleri()]
    assert ifadeler, "panoda hiç sorgu yok"

    def var(*parcalar: str) -> bool:
        return any(all(p in e for p in parcalar) for e in ifadeler)

    for q in ("0.5", "0.95"):
        assert var(f"histogram_quantile({q}", "apisix_http_latency_bucket", "le, route"), f"geçit p{q} rota başına yok"
        assert var(f"histogram_quantile({q}", "apisix_llm_latency_bucket"), f"LLM p{q} yok"
    assert var("node_cpu_seconds_total"), "CPU paneli yok"
    assert var("node_memory_MemAvailable_bytes", "node_memory_MemTotal_bytes"), "RAM paneli yok"
    disk = [e for e in ifadeler if "node_filesystem_avail_bytes" in e]
    assert disk, "disk paneli yok"
    m = re.search(r'mountpoint=~"([^"]+)"', disk[0])
    assert m, "disk paneli bağlama noktası süzgeci taşımıyor"
    for nokta in ("/", "/opt/veri"):
        assert re.fullmatch(m.group(1), nokta), f"disk paneli {nokta} doluluğunu göstermiyor"


# =================================================================================================
# D — A0 rolü
# =================================================================================================

def _glob(desenler: list[str]) -> set[pathlib.Path]:
    out: set[pathlib.Path] = set()
    for d in desenler:
        out |= {pathlib.Path(p).resolve() for p in glob.glob(d.replace("{{ playbook_dir }}", str(ANSIBLE)))}
    return out


def test_D1_birimler_KOPYALANIR_ama_ilk_gun_ETKIN_DEGIL():
    d = _defaults()
    kapsam = _glob(d["birim_kaynaklari"])
    for ad in BIRIMLER:
        assert (TELEMETRI / f"{ad}.service").resolve() in kapsam, f"{ad} birim_kaynaklari'nda değil"
        assert f"{ad}.service" not in d["etkin_birimler"], f"{ad} ilk gün etkinleştirilemez (T6)"
    assert "meridian-grafana.service.d" in d["dropin_dizinleri"]
    confs = {p.resolve() for p in GRAFANA_DROPIN_DIZINI.glob("*.conf")}
    assert confs and confs <= _glob(d["dropin_kaynaklari"]), "grafana drop-in'i dropin_kaynaklari'nda değil"


def _yapilandirma_agaci() -> set[str]:
    out = set()
    for p in TELEMETRI.rglob("*"):
        if not p.is_file():
            continue
        rel = p.relative_to(TELEMETRI)
        if rel.suffix == ".service" and len(rel.parts) == 1:
            continue
        if rel.parts[0].endswith(".service.d"):
            continue
        out.add(rel.as_posix())
    return out


def test_D2_yapilandirma_listesi_AGACLA_iki_yonlu_esit_ve_kopya_gorevi():
    d = _defaults()
    liste = d["telemetri_yapilandirma_dosyalari"]
    assert len(liste) == len(set(liste)), "yinelenen yapılandırma girdisi"
    assert set(liste) == _yapilandirma_agaci(), (
        f"liste ↔ ağaç ayrıştı: listede fazla {sorted(set(liste) - _yapilandirma_agaci())}, "
        f"ağaçta fazla {sorted(_yapilandirma_agaci() - set(liste))}")
    gorevler = yaml.safe_load(BIRIMLER_YML.read_text(encoding="utf-8"))
    kopya = [g for g in gorevler if g.get("loop") == "{{ telemetri_yapilandirma_dosyalari }}"]
    assert len(kopya) == 1, "yapılandırma kopya görevi TEK değil"
    a = kopya[0]["ansible.builtin.copy"]
    assert a["src"] == "{{ playbook_dir }}/../telemetri/{{ item }}"
    # Sondaki `/`: hedef dizin YOKSA copy modülü onu yaratır ve check kipinde "yaratılacak" der (dizin yokken
    # düz hedef check kipinde "Destination directory does not exist" ile düşer — ansible-core copy modülü).
    assert a["dest"] == "{{ telemetri_yapilandirma_dizini }}/{{ item | dirname }}/"
    assert (a["owner"], a["group"], str(a["mode"]), str(a["directory_mode"])) == ("root", "root", "0644", "0755")
    assert "notify" not in kopya[0], "yapılandırma kopyası restart/handler tetiklemez (RESTART YOK)"
    # Birimlerin bağladığı her yapılandırma yolu listedeki bir dosya ya da onların ATA dizinidir.
    yk = _yapilandirma_koku()
    tam = {f"{yk}/{r}" for r in liste}
    for ad in BIRIMLER:
        for m in _mountlar(_run(ad)):
            k = _kaynak(m)
            if _altinda(k, yk):
                assert k in tam or any(_altinda(t, k) for t in tam), f"{ad}: {k} listede karşılıksız"


def test_D3_veri_dizinleri_konteyner_KIMLIGIYLE_ve_ATA_once():
    d = _defaults()
    gorevler = yaml.safe_load(DIZINLER_YML.read_text(encoding="utf-8"))
    yollar = [str((g.get("ansible.builtin.file") or {}).get("path", "")) for g in gorevler]
    beklenen = {
        "{{ telemetri_veri_dizini }}": ("root", "root", "0755"),
        "{{ telemetri_veri_dizini }}/prometheus":
            ("{{ telemetri_prometheus_uid }}", "{{ telemetri_prometheus_uid }}", "0700"),
        "{{ telemetri_veri_dizini }}/grafana": ("{{ telemetri_grafana_uid }}", "{{ telemetri_grafana_gid }}", "0700"),
    }
    for yol, (sahip, grup, mod) in beklenen.items():
        assert yollar.count(yol) == 1, f"dizinler.yml: {yol} görevi TEK değil"
        a = gorevler[yollar.index(yol)]["ansible.builtin.file"]
        assert (a["state"], a["owner"], a["group"], str(a["mode"])) == ("directory", sahip, grup, mod), (yol, a)
    kok = yollar.index("{{ telemetri_veri_dizini }}")
    assert kok < yollar.index("{{ telemetri_veri_dizini }}/prometheus") and kok < yollar.index(
        "{{ telemetri_veri_dizini }}/grafana"), "veri kökü görevi çocuklarından SONRA"
    vk = _veri_koku()
    yazilir = {_kaynak(m) for ad in BIRIMLER for m in _mountlar(_run(ad)) if not _salt_okur(m)}
    assert yazilir == {f"{vk}/prometheus", f"{vk}/grafana"}, f"yazılabilir bağlamalar: {sorted(yazilir)}"
    assert str(d["telemetri_prometheus_uid"]) == "65534" and str(d["telemetri_grafana_uid"]) == "472", (
        "konteyner kimlikleri imaj yapılandırmasından ölçüldü (prometheus `nobody`, grafana `472`)")


def test_D4_F9_icerik_aynasi_birim_ve_yapilandirma_ciftlerini_TASIR():
    ciftler = set(_f9_ciftleri())
    yk = _yapilandirma_koku()
    beklenen = {(f"deploy/telemetri/{ad}.service", f"/etc/systemd/system/{ad}.service") for ad in BIRIMLER}
    beklenen |= {(f"deploy/telemetri/{r}", f"{yk}/{r}") for r in _defaults()["telemetri_yapilandirma_dosyalari"]}
    eksik = sorted(beklenen - ciftler)
    assert eksik == [], f"[F9] telemetri çiftleri eksik (dinleme adresinin sessiz ayrışması ölçülmez): {eksik}"


# =================================================================================================
# F — izin-denetimli sır kapısı (tur 2, inceleme O-1)
# =================================================================================================

def _izin_listesi() -> list[dict]:
    liste = _defaults().get("izin_denetimli_sir_dosyalari")
    assert isinstance(liste, list) and liste, "defaults'ta `izin_denetimli_sir_dosyalari` yok/boş"
    return liste


def _agent_sablon_bloklari(metin: str) -> dict[str, str]:
    """agent.hcl `template { … }` gövdeleri → {destination: gövde}. Yalnız tek-değer ve yan dosya blokları."""
    out: dict[str, str] = {}
    for govde in re.findall(r"^template \{\n(.*?)^\}", metin, re.M | re.S):
        m = re.search(r'^\s*destination\s*=\s*"([^"]+)"', govde, re.M)
        if m:
            out[m.group(1)] = govde
    return out


def _agent_kimligi(birim_metni: str) -> tuple[str, str]:
    """Agent'ın render ettiği dosyanın sahibi/grubu: şablon `user`/`group` taşımıyorsa sürecin kimliğidir —
    birimde `User=`/`Group=` yoksa root (systemd varsayılanı)."""
    kullanici = _tek(birim_metni, "User") or "root"
    grup = _tek(birim_metni, "Group") or ("root" if kullanici == "root" else kullanici)
    return kullanici, grup


def _izin_ayrisma_bulgulari(liste: list[dict], agent_metni: str, kv: list[dict], agent_birim_metni: str) -> list[str]:
    """Beklenen mod/sahip/grup, Vault Agent'ın o dosyayı GERÇEKTE nasıl yazdığıyla ayrışıyor mu."""
    b: list[str] = []
    bloklar = _agent_sablon_bloklari(agent_metni)
    hedefler = {g.get("hedef"): g for g in kv if "hedef" in g}
    a_kul, a_grup = _agent_kimligi(agent_birim_metni)
    for e in liste:
        yol = e.get("yol")
        govde = bloklar.get(yol)
        if govde is None:
            b.append(f"{yol}: agent.hcl'de render şablonu yok (izin kaynağı yok)")
            continue
        perms = re.search(r"^\s*perms\s*=\s*(0?[0-7]{3,4})\s*$", govde, re.M)
        if not perms or perms.group(1).rjust(4, "0") != str(e.get("mod")):
            b.append(f"{yol}: şablon perms {perms and perms.group(1)} != beklenen mod {e.get('mod')}")
        s_kul = re.search(r'^\s*user\s*=\s*"([^"]+)"', govde, re.M)
        s_grup = re.search(r'^\s*group\s*=\s*"([^"]+)"', govde, re.M)
        if (s_kul.group(1) if s_kul else a_kul) != e.get("sahip"):
            b.append(f"{yol}: render sahibi {s_kul.group(1) if s_kul else a_kul} != beklenen {e.get('sahip')}")
        if (s_grup.group(1) if s_grup else a_grup) != e.get("grup"):
            b.append(f"{yol}: render grubu {s_grup.group(1) if s_grup else a_grup} != beklenen {e.get('grup')}")
        g = hedefler.get(yol)
        if g is None:
            b.append(f"{yol}: envanter vault_kv hedefi değil")
        elif (g.get("mod"), g.get("sahip")) != (e.get("mod"), e.get("sahip")):
            b.append(f"{yol}: envanter mod/sahip {(g.get('mod'), g.get('sahip'))} ayrıştı")
    return b


def test_F1_ROTASYON_DISI_her_kredansiyel_IZIN_DENETIMLI_listede():
    """Rotasyon dışı ≠ denetim dışı: v447 istisnasına giren her `LoadCredential` kaynağı izin kapısındadır.
    Aksi hâlde bir sır İKİ kapıdan birden (zorunlu denetim + rotasyon) sessizce çıkmış olurdu."""
    assert _ROTASYON_DISI, "v447 rotasyon dışı beyanı boş — çivi kör"
    yollar = {e["yol"] for e in _izin_listesi()}
    kaynaklar = {(b, k): _KRED_KAYNAKLARI.get(b, {}).get(k) for b, k in _ROTASYON_DISI}
    curuk = sorted(str(c) for c, v in kaynaklar.items() if v is None)
    assert curuk == [], f"rotasyon dışı beyan hiçbir drop-in `LoadCredential` çiftine çözülmüyor: {curuk}"
    eksik = sorted(v for v in kaynaklar.values() if v not in yollar)
    assert eksik == [], f"rotasyon dışı ama izin denetimi DIŞI kaynak(lar): {eksik}"
    zorunlu = {e["yol"] for e in _defaults()["zorunlu_sir_dosyalari"]}
    assert not (yollar & zorunlu), f"iki kapıda birden (anlamları çelişir — biri varlık ister): {sorted(yollar & zorunlu)}"
    for e in _izin_listesi():
        assert set(e) == {"yol", "sahip", "grup", "mod"}, f"izin girdisi şeması: {sorted(e)}"


def _gorevler_sir() -> list[dict]:
    return yaml.safe_load(SIR_DENETIMI_YML.read_text(encoding="utf-8"))


def test_F2_kapi_gorevi_LISTEYLE_eslesir_YOKSA_gec_VARSA_dur():
    gorevler = _gorevler_sir()
    stat = [g for g in gorevler if "ansible.builtin.stat" in g and g.get("loop") == "{{ izin_denetimli_sir_dosyalari }}"]
    assert len(stat) == 1, "izin-denetimli liste üzerinde dönen TEK stat görevi yok"
    st = stat[0]
    assert st.get("no_log") is True and st["ansible.builtin.stat"].get("get_checksum") is False, (
        "stat içerik okumamalı (get_checksum false) ve çıktısı gizli olmalı (no_log)")
    kayit = st.get("register")
    assert kayit and "sir_stat" not in kayit, f"register adı zorunlu kapının süzgecine takılır: {kayit!r}"
    sonuclar = f"{{{{ {kayit}.results }}}}"
    kullanan = [g for g in gorevler if g.get("loop") == sonuclar]
    yoksa = [g for g in kullanan if "ansible.builtin.debug" in g]
    varsa = [g for g in kullanan if "ansible.builtin.assert" in g]
    assert len(yoksa) == 1 and len(varsa) == 1 and len(kullanan) == 2, "iki dal (yoksa-geç · varsa-dur) TEK ve AYRI değil"
    assert str(yoksa[0].get("when", "")).replace(" ", "") == "notitem.stat.exists", f"yoksa dalı: {yoksa[0].get('when')!r}"
    assert "ATLANDI" in str(yoksa[0]["ansible.builtin.debug"].get("msg", "")), "atlama beyan satırı yok (Yasa 6)"
    assert str(varsa[0].get("when", "")).replace(" ", "") == "item.stat.exists", f"varsa dalı: {varsa[0].get('when')!r}"
    assert varsa[0].get("no_log") is not True, "kapı çıktısı gizlenirse hangi dosyanın düştüğü okunamaz"
    that = {str(x).replace(" ", "") for x in varsa[0]["ansible.builtin.assert"]["that"]}
    assert that == {"item.stat.mode==item.item.mod", "item.stat.pw_name==item.item.sahip",
                    "item.stat.gr_name==item.item.grup"}, f"kapı koşulları: {sorted(that)}"
    # Sıra: kapı drop-in'lerden ÖNCE koşan dosyada (zincir v451'de çivili) ve zorunlu kapıdan SONRA.
    konum = {id(g): i for i, g in enumerate(gorevler)}
    zorunlu_kapi = [g for g in gorevler if "ansible.builtin.assert" in g and "sir_stat" in str(g.get("loop", ""))]
    assert len(zorunlu_kapi) == 1 and konum[id(zorunlu_kapi[0])] < konum[id(st)], "izin kapısı zorunlu kapıdan önce"


def test_F3_beklenen_mod_sahip_grup_VAULT_SABLONUYLA_ayrismaz():
    kv = yaml.safe_load(ENVANTER.read_text(encoding="utf-8"))["vault_kv"]
    bulgular = _izin_ayrisma_bulgulari(_izin_listesi(), AGENT_HCL.read_text(encoding="utf-8"), kv,
                                       AGENT_BIRIMI.read_text(encoding="utf-8"))
    assert bulgular == [], "izin beklentisi Vault Agent render'ından ayrıştı:\n" + "\n".join(bulgular)


IZIN_MUTASYONLARI = [
    ("perms_0440", "  destination = \"/etc/meridian/grafana_admin_parola\"\n  perms       = 0400",
     "  destination = \"/etc/meridian/grafana_admin_parola\"\n  perms       = 0440", "perms"),
    ("sablon_yok", "destination = \"/etc/meridian/grafana_admin_parola\"", "destination = \"/etc/meridian/baska\"",
     "şablonu yok"),
    ("sablon_grup", "  destination = \"/etc/meridian/grafana_admin_parola\"\n",
     "  destination = \"/etc/meridian/grafana_admin_parola\"\n  group = \"vault\"\n", "grubu"),
]


@pytest.mark.parametrize("kimlik, eski, yeni, beklenen", IZIN_MUTASYONLARI, ids=[m[0] for m in IZIN_MUTASYONLARI])
def test_F4_POZITIF_KONTROL_izin_ayrisma_denetcisi_OTER(kimlik, eski, yeni, beklenen):
    kv = yaml.safe_load(ENVANTER.read_text(encoding="utf-8"))["vault_kv"]
    bozuk = _bozuk(AGENT_HCL.read_text(encoding="utf-8"), eski, yeni)
    bulgular = _izin_ayrisma_bulgulari(_izin_listesi(), bozuk, kv, AGENT_BIRIMI.read_text(encoding="utf-8"))
    assert any(beklenen in x for x in bulgular), f"{kimlik}: denetçi ÖTMEDİ: {bulgular}"


def test_F5_POZITIF_KONTROL_agent_birimi_kullanici_degisirse_OTER():
    kv = yaml.safe_load(ENVANTER.read_text(encoding="utf-8"))["vault_kv"]
    birim = _bozuk(AGENT_BIRIMI.read_text(encoding="utf-8"), "[Service]\n", "[Service]\nUser=vault\n")
    bulgular = _izin_ayrisma_bulgulari(_izin_listesi(), AGENT_HCL.read_text(encoding="utf-8"), kv, birim)
    assert any("sahibi" in x for x in bulgular), f"agent kimliği değişince denetçi ÖTMEDİ: {bulgular}"


# =================================================================================================
# E — pozitif kontrol: denetçiler bellekte bozulmuş GERÇEK dosyada öter
# =================================================================================================

def _bozuk(metin: str, eski: str, yeni: str) -> str:
    assert eski in metin, f"mutasyon çapası dosyada yok (çivi bayatlamış): {eski!r}"
    return metin.replace(eski, yeni, 1)


BIRIM_MUTASYONLARI = [
    ("loopback_0000", PROMETHEUS, "--web.listen-address=127.0.0.1:", "--web.listen-address=0.0.0.0:", "loopback"),
    ("dolu_port", PROMETHEUS, "--web.listen-address=127.0.0.1:9095", "--web.listen-address=127.0.0.1:9090", "DOLU"),
    ("digest_yok", PROMETHEUS, "prom/prometheus:v3.15.0@sha256:", "prom/prometheus:v3.15.0@", "pinli değil"),
    ("latest", NODE, ":v1.12.1@", ":latest@", "tam sürüm"),
    ("bellek_bayragi_yok", GRAFANA, "--memory=256m ", "", "--memory"),
    ("memorymax_yanlis", NODE, "MemoryMax=64M", "MemoryMax=640M", "MemoryMax"),
    ("root_kullanici", GRAFANA, "--name meridian-grafana --network host",
     "--name meridian-grafana --network host --user 0", "kullanıcı/ayrıcalık"),
    ("pid_host", NODE, "--name meridian-node-exporter --network host",
     "--name meridian-node-exporter --network host --pid host", "kullanıcı/ayrıcalık"),
    ("proc_yazilabilir", NODE, "source=/proc,target=/host/proc,readonly", "source=/proc,target=/host/proc",
     "salt-okur"),
    ("v_baglamasi", PROMETHEUS, "--mount type=bind,source=/etc/", "-v /etc/", "`-v` bağlaması"),
    ("grafana_tum_arayuz", GRAFANA, "GF_SERVER_HTTP_ADDR=127.0.0.1", "GF_SERVER_HTTP_ADDR=0.0.0.0", "loopback"),
]


@pytest.mark.parametrize("kimlik, ad, eski, yeni, beklenen", BIRIM_MUTASYONLARI,
                         ids=[m[0] for m in BIRIM_MUTASYONLARI])
def test_E1_POZITIF_KONTROL_birim_denetcisi_OTER(kimlik, ad, eski, yeni, beklenen):
    bulgular = _birim_bulgulari(ad, _bozuk(_birim_metni(ad), eski, yeni), _veri_koku())
    assert any(beklenen in x for x in bulgular), f"{kimlik}: denetçi ÖTMEDİ: {bulgular}"


PROM_MUTASYONLARI = [
    ("alerting_blogu", "cfg", "scrape_configs:", "alerting:\n  alertmanagers: []\nscrape_configs:", "alerting"),
    ("kural_dosyasi", "cfg", "scrape_configs:", "rule_files: [a.yml]\nscrape_configs:", "rule_files"),
    ("saklama_boyutu_yok", "cfg", "size: 2GB", "size: 20GB", "saklama tavanı"),
    ("kazima_60s", "cfg", "scrape_interval: 30s", "scrape_interval: 60s", "30s"),
    ("bayrakla_saklama", "birim", "--storage.tsdb.path=/prometheus",
     "--storage.tsdb.path=/prometheus --storage.tsdb.retention.time=30d", "BAYRAKLA"),
    ("tsdb_opt_veri", "birim", "source=/var/lib/meridian-telemetri/prometheus,", "source=/opt/veri/prometheus,",
     "TSDB"),
]


@pytest.mark.parametrize("kimlik, hangi, eski, yeni, beklenen", PROM_MUTASYONLARI,
                         ids=[m[0] for m in PROM_MUTASYONLARI])
def test_E2_POZITIF_KONTROL_prometheus_denetcisi_OTER(kimlik, hangi, eski, yeni, beklenen):
    cfg, birim = PROMETHEUS_YML.read_text(encoding="utf-8"), _birim_metni(PROMETHEUS)
    if hangi == "cfg":
        cfg = _bozuk(cfg, eski, yeni)
    else:
        birim = _bozuk(birim, eski, yeni)
    bulgular = _prometheus_bulgulari(cfg, birim, _veri_koku(), _yapilandirma_koku())
    assert any(beklenen in x for x in bulgular), f"{kimlik}: denetçi ÖTMEDİ: {bulgular}"


PAROLA_MUTASYONLARI = [
    ("deger_satiri", "birim", "--name meridian-grafana --network host",
     "--name meridian-grafana --network host -e GF_SECURITY_ADMIN_PASSWORD=x", "konteyner ortamında"),
    ("degersiz_e", "birim", "--name meridian-grafana --network host",
     "--name meridian-grafana --network host -e GF_SECURITY_ADMIN_PASSWORD", "konteyner ortamında"),
    ("env_file", "birim", "--name meridian-grafana --network host",
     "--name meridian-grafana --network host --env-file /opt/x.env", "--env-file"),
    ("file_yok", "birim", "GF_SECURITY_ADMIN_PASSWORD__FILE=", "GF_SECURITY_ADMIN_PASSWORD_DOSYA=", "__FILE` yok"),
    ("dropin_environment", "dropin", "[Service]", "[Service]\nEnvironment=GF_SECURITY_ADMIN_PASSWORD=x",
     "Environment="),
]


@pytest.mark.parametrize("kimlik, hangi, eski, yeni, beklenen", PAROLA_MUTASYONLARI,
                         ids=[m[0] for m in PAROLA_MUTASYONLARI])
def test_E3_POZITIF_KONTROL_parola_denetcisi_OTER(kimlik, hangi, eski, yeni, beklenen):
    birim, dropin = _birim_metni(GRAFANA), _grafana_dropin_metni()
    if hangi == "birim":
        birim = _bozuk(birim, eski, yeni)
    else:
        dropin = _bozuk(dropin, eski, yeni)
    bulgular = _parola_bulgulari(birim, dropin)
    assert any(beklenen in x for x in bulgular), f"{kimlik}: denetçi ÖTMEDİ: {bulgular}"
