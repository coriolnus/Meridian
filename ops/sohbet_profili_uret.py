#!/usr/bin/env python3
"""ops/sohbet_profili_uret.py — her aktif bot için SOHBET profilini rapor profilinden ÜRET (Parça 1b G2).

NEDEN VAR. Konuşan filonun her botu iki kipte koşar: zamanlanmış RAPOR (`deploy/hermes/profiles/<ad>/`,
hafızasız, kendi systemd birimi) ve operatörün sorusuna cevap veren SOHBET (`deploy/hermes/sohbet/profiles/<ad>/`,
ayrı Hermes kökünde çoklu ağ geçidi). Parça 0 v3 ölçümü: rapor yolu (`-z`) hafızaya YAZABİLİYOR, yani tek
profil iki işi göremez — ikiz zorunlu. İkizi elle yazmak ise bu deponun baskın arızasını çağırır: aynı duruşun
(guard kancası, onay, kapalı takımlar, model, kapı sağlayıcısı) iki kopyası sessizce ayrışır ve bayatlayan
taraf hep okunmayan taraf olur. Bu betik ikizi TÜRETİR; duruş rapor profilinde yaşar, burada kopyalanmaz.

TEK KAYNAK:
  * duruş ve rapor SOUL'u   → `deploy/hermes/profiles/<ad>/` (`config.yaml`, `SOUL.md`, `distribution.yaml`)
  * Meridian MCP girdisi     → `deploy/hermes/config.yaml` içindeki mcp_servers → meridian girdisi
                               (`enabled` true olur, argümanlara `--bot <ad>` eklenir)
  * hangi bot, hangi araç    → `deploy/hermes/kadro.yaml` (`meridian.kadro`; yalnız `aktif` satırlar)
  * sohbet farkları          → BU MODÜLÜN sabitleri (zaman aşımı, yeniden deneme, Hindsight ayarları, SOUL
                               sohbet bölümü) — başka yerde yazılmaz.

KOMUT SATIRI SÖZLEŞMESİ (ops aracı sözleşmesi KOMUT SATIRIdır, `main()` değil):

    python ops/sohbet_profili_uret.py --yaz       # üret ve yaz (yalnız içeriği değişen dosyaya dokunur)
    python ops/sohbet_profili_uret.py --kontrol   # yazMA; diskteki dosyalar güncel mi

Çıkış kodu HÜKÜMDÜR:
    0  yazıldı (`--yaz`) / güncel (`--kontrol`)
    1  BAYAT (yalnız `--kontrol`) — ayrışan/eksik/fazla dosyalar stdout'a, satır başına bir tane
    2  KULLANIM hatası — `--yaz` ile `--kontrol` birlikte ya da hiçbiri (sessiz öncelik kuralı YOK: biri
       SORAR, öteki YAZAR; biri ötekini yutarsa operatör "yazdım" sanır — `ops/jeton_css_uret.py` emsali)

SİLMEZ. Kadroda `aktif`ten çıkan botun sohbet profili SİLİNMEZ, `--kontrol` onu "fazla" diye ADIYLA raporlar
(ve `--yaz` da uyarır). Silme bir karardır, üretecin yan etkisi değil.

RAPOR PROFİLLERİNE YAZMAZ. Yalnız `deploy/hermes/sohbet/profiles/**` yazılır.

DETERMİNİSTİK: aynı kaynaktan aynı bayt çıkar (sözlük sırası sabit, zaman damgası YOK) — damga olsaydı her
koşum fark üretir ve `--kontrol` kapısı anlamsızlaşırdı.

SIR YOK: hiçbir sır değeri okunmaz, yazılmaz, basılmaz. `hindsight/config.json`da anahtar alanı YOKTUR (değer
G3 biriminin credential'ından `HINDSIGHT_API_KEY` ortamıyla gelir); profil `.env`i üretilmez.

`meridian.obs`'A ULAŞMAZ: yalnız `meridian.kadro` ithal edilir (o da yalnız `meridian.config` sabitlerine
dayanır); pytest dışı koşum canlı yerel deftere yazmaz.

OKUYUCU (Yasa 6): üretilmiş profiller Hermes çoklu ağ geçidinin profil evleridir (kuruluş G3'te); tazelik
kapısı `--kontrol` ve `tests/test_sohbet_profili_uret_v599.py`dir.
"""
from __future__ import annotations

import argparse
import copy
import json
import pathlib
import sys

import yaml

REPO = pathlib.Path(__file__).resolve().parents[1]
# `python ops/sohbet_profili_uret.py` depo kökünden koşulur ve o hâlde kök `sys.path`te değildir. Kök BAŞA
# eklenir: kurulu (düzenlenebilir) paket başka bir checkout'u gösterebilir; üreteç KENDİ ağacının kadro
# modülünü okumalı.
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from meridian import kadro as kadro_mod  # noqa: E402  (kök sys.path'e eklendikten sonra)

SOHBET_KOK = "deploy/hermes/sohbet/profiles"
RAPOR_KOK = "deploy/hermes/profiles"
KOK_YAPILANDIRMA = "deploy/hermes/config.yaml"
KADRO_DOSYASI = "deploy/hermes/kadro.yaml"

#: Model çağrısı başına istek zaman aşımı (sn) — Hermes'in OKUDUĞU yerde yazılır: sağlayıcı girdisinin
#: `request_timeout_seconds` alanı (kökte `timeout` anahtarı YOK; v329 emsali). Parça 0 v3: ücretsiz model
#: çağrı başına ~5 dk asıldı ≈ 3 deneme × 120 sn; 2 × 60 sn en kötü ~2 dk (G4 ara bildirimi bu süreyi karşılar).
SOHBET_ISTEK_ZAMAN_ASIMI_SN = 60
#: `agent.api_max_retries` — Hermes v0.19 varsayılanı 3 (`agent/agent_init.py`).
SOHBET_API_DENEME = 2

#: Üretilmiş her dosyanın beyanı (YAML'da baş yorum, JSON'da `_uretildi` alanı).
URETILDI = "ÜRETİLMİŞ — elle düzenlenmez; üreteç `ops/sohbet_profili_uret.py`"

#: Parça 0 v3'te ÖLÇÜLEREK çalışan Hindsight anahtar kümesi. `memory_mode: context` → hafıza bağlam olarak
#: gelir, modele hafıza ARACI açılmaz.
HINDSIGHT_API_URL = "http://127.0.0.1:8888"
HINDSIGHT_ZAMAN_ASIMI_SN = 10

SOHBET_BOLUMU_BASLIGI = "## Sohbet kipi"
_BOLUM_BASI = (
    SOHBET_BOLUMU_BASLIGI,
    "",
    "Bu bölüm yukarıdaki rapor talimatlarından önce gelir. Burada zamanlanmış bir rapor yazmıyorsun: "
    "operatörün sorusuna cevap veriyorsun.",
    "",
    "- Bugünün durumu hakkında yalnız araçlarından gelen veriyle konuş. Araç çağırmadan hiçbir sayı, yüzde, "
    "sembol ya da kaynak yazma.",
    "- Aracın yoksa ya da araç cevap vermediyse bilmediğini söyle ve nedenini yaz. Araç sonucu uydurma; "
    "çağırmadığın bir aracın adını anma.",
    "- Geçmiş konuşmalarından notlar bağlam olarak gelebilir. Oradan aktardığın her şeyin tarihini ver ve onu "
    "bugün için hüküm sayma.",
    "- Ayar değiştiremez, komut çalıştıramazsın.",
)
#: Koşullu satırlar: SOUL botun kadroda OLMAYAN aracını vaat ederse model yeteneği uydurur — satır yalnız araç
#: kadrodaysa (ve başka botların hafızası için hafıza kipi `hepsi` ise) yazılır. Karar `_vaat_edilir`de.
_KOSULLU_SATIRLAR = (
    ("oneri_yaz", "- Bir değişiklik gerekiyorsa oneri_yaz aracıyla öneri yaz; onayı operatör verir."),
    ("is_iste", "- Bir raporun yeniden üretilmesi gerekiyorsa is_iste aracıyla iste; işi Meridian koşar."),
    ("bot_hafizasi_ara", "- Başka bir botun geçmiş konuşmalarına bot_hafizasi_ara aracıyla bakabilirsin; oradan "
                         "aktardığın her şeyin hangi bota ve hangi tarihe ait olduğunu yaz."),
)
#: Rapor SOUL'undaki tek başına şablon satırı sohbette uygulanırsa bot soruya o jetonla cevap verir — bölüm onu
#: cümle içinde AÇIKÇA geçersiz kılar (tek başına satır olarak YAZILMAZ).
_BOLUM_SONU = (
    "- Bu kipte SESSIZ yazmazsın: her soruya cevap verirsin.",
    "- Kısa yaz; birkaç paragrafı geçme.",
)


def _yaml_oku(yol: pathlib.Path) -> dict:
    veri = yaml.safe_load(yol.read_text(encoding="utf-8"))
    if not isinstance(veri, dict):
        raise ValueError(f"{yol}: YAML bir eşleme değil ({type(veri).__name__}) — sohbet profili türetilemez")
    return veri


def _yaml_yaz(baslik: tuple[str, ...], veri: dict) -> bytes:
    govde = yaml.safe_dump(veri, allow_unicode=True, sort_keys=False)
    return ("".join(f"# {s}\n" for s in baslik) + govde).encode("utf-8")


def _vaat_edilir(bot: kadro_mod.Bot, arac: str) -> bool:
    return arac in bot.araclar and (arac != "bot_hafizasi_ara" or bot.hafiza == "hepsi")


def sohbet_bolumu(bot: kadro_mod.Bot) -> str:
    """Botun SOUL'una eklenen sohbet bölümü — sabit metin + yalnız kadrodaki araçlar için koşullu satırlar."""
    kosullu = tuple(satir for arac, satir in _KOSULLU_SATIRLAR if _vaat_edilir(bot, arac))
    return "\n".join(_BOLUM_BASI + kosullu + _BOLUM_SONU) + "\n"


def _kadro(kok: pathlib.Path, kadro) -> tuple[kadro_mod.Bot, ...]:
    return kadro_mod.aktif_botlar(kadro if kadro is not None else kadro_mod.kadro_yukle(kok / KADRO_DOSYASI))


def _config(rapor_evi: pathlib.Path, bot: kadro_mod.Bot, kok_meridian: dict) -> bytes:
    cfg = copy.deepcopy(_yaml_oku(rapor_evi / "config.yaml"))
    girdi = copy.deepcopy(kok_meridian)
    cfg["mcp_servers"] = {"meridian": {**girdi, "enabled": True, "args": list(girdi["args"]) + ["--bot", bot.ad]}}
    cfg["platform_toolsets"] = {"api_server": ["meridian"]}
    cfg["memory"] = {"provider": "hindsight"}
    ajan = cfg.get("agent")
    if not isinstance(ajan, dict):
        raise ValueError(f"{rapor_evi}/config.yaml: 'agent' eşlemesi yok — duruş (kapalı takımlar) miras alınamaz")
    ajan["api_max_retries"] = SOHBET_API_DENEME
    saglayicilar = cfg.setdefault("providers", {})
    for ad in ("custom", "openrouter"):
        saglayicilar.setdefault(ad, {})["request_timeout_seconds"] = SOHBET_ISTEK_ZAMAN_ASIMI_SN
    baslik = (
        URETILDI + ".",
        f"Kaynak: {RAPOR_KOK}/{bot.ad}/config.yaml (duruş: kanca, onay, kapalı takımlar, model, sağlayıcılar —",
        f"gerekçeleri orada) + {KOK_YAPILANDIRMA} içindeki mcp_servers → meridian girdisi (--bot {bot.ad} ekiyle)",
        "+ üretecin sohbet sabitleri (zaman aşımı, yeniden deneme, hafıza sağlayıcısı, platform izin listesi).",
        "Değiştirmek için kaynağı düzenle ve üreteci --yaz ile koş; tazelik kapısı --kontrol.",
    )
    return _yaml_yaz(baslik, cfg)


def _hindsight(bot: kadro_mod.Bot) -> bytes:
    veri = {
        "_uretildi": URETILDI,
        "mode": "local_external",
        "api_url": HINDSIGHT_API_URL,
        "bank_id": f"bot-{bot.ad}",
        "recall_budget": "low",
        "memory_mode": "context",
        "auto_recall": True,
        "auto_retain": True,
        "retain_tags": f"bot:{bot.ad},kaynak:sohbet",
        "retain_source": bot.ad,
        "retain_async": False,
        "timeout": HINDSIGHT_ZAMAN_ASIMI_SN,
    }
    return (json.dumps(veri, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def _soul(rapor_evi: pathlib.Path, bot: kadro_mod.Bot) -> bytes:
    rapor = (rapor_evi / "SOUL.md").read_text(encoding="utf-8").rstrip()
    return (rapor + "\n\n" + sohbet_bolumu(bot)).encode("utf-8")


def _dagitim(rapor_evi: pathlib.Path, bot: kadro_mod.Bot) -> bytes:
    manifest = _yaml_oku(rapor_evi / "distribution.yaml")
    anahtar_adi = f"BOT_KEY_{bot.ad.upper()}"
    kapi = [g for g in (manifest.get("env_requires") or []) if isinstance(g, dict) and g.get("name") == anahtar_adi]
    if len(kapi) != 1:
        raise ValueError(f"{rapor_evi}/distribution.yaml: env_requires içinde tek bir {anahtar_adi} girdisi "
                         f"beklenirdi, {len(kapi)} bulundu — kapı anahtarı beyanı miras alınamaz")
    if "hermes_requires" not in manifest:
        raise ValueError(f"{rapor_evi}/distribution.yaml: hermes_requires yok — sürüm tabanı miras alınamaz")
    veri = {
        "name": bot.ad,
        "version": "0.1.0",
        "description": f"{bot.ad} sohbet profili — ÜRETİLMİŞ (rapor profilinden türetildi)",
        "hermes_requires": manifest["hermes_requires"],
        "env_requires": [
            copy.deepcopy(kapi[0]),
            {"name": "HINDSIGHT_API_KEY", "required": True,
             "description": "Hindsight kiracı anahtarı; değer G3 biriminin credential'ından, dosyaya yazılmaz"},
        ],
        "distribution_owned": ["SOUL.md", "config.yaml", "hindsight/config.json"],
    }
    baslik = (URETILDI + ".", f"Kaynak: {RAPOR_KOK}/{bot.ad}/distribution.yaml (sürüm tabanı, kapı anahtarı beyanı).")
    return _yaml_yaz(baslik, veri)


def uret(kok: pathlib.Path = REPO, kadro=None) -> dict[str, bytes]:
    """Göreli yol → içerik. YAZMAZ."""
    kok = pathlib.Path(kok)
    kok_cfg = _yaml_oku(kok / KOK_YAPILANDIRMA)
    kok_meridian = (kok_cfg.get("mcp_servers") or {}).get("meridian")
    if not isinstance(kok_meridian, dict) or not isinstance(kok_meridian.get("args"), list):
        raise ValueError(f"{KOK_YAPILANDIRMA}: mcp_servers → meridian girdisi (args listesiyle) yok — "
                         "sohbet profilinin araç sunucusu türetilemez")
    cikti: dict[str, bytes] = {}
    for bot in sorted(_kadro(kok, kadro), key=lambda b: b.ad):
        rapor_evi = kok / RAPOR_KOK / bot.ad
        if not rapor_evi.is_dir():
            raise ValueError(f"aktif @{bot.ad} için rapor profili yok ({RAPOR_KOK}/{bot.ad}) — "
                             "sohbet profili türetilemez")
        hedef = f"{SOHBET_KOK}/{bot.ad}"
        cikti[f"{hedef}/SOUL.md"] = _soul(rapor_evi, bot)
        cikti[f"{hedef}/config.yaml"] = _config(rapor_evi, bot, kok_meridian)
        cikti[f"{hedef}/distribution.yaml"] = _dagitim(rapor_evi, bot)
        cikti[f"{hedef}/hindsight/config.json"] = _hindsight(bot)
    return cikti


def _fazlalar(kok: pathlib.Path, beklenen: dict[str, bytes]) -> list[str]:
    taban = kok / SOHBET_KOK
    if not taban.is_dir():
        return []
    return sorted(str(p.relative_to(kok)) for p in taban.rglob("*")
                  if p.is_file() and str(p.relative_to(kok)) not in beklenen)


def yaz(kok: pathlib.Path = REPO, kadro=None) -> list[str]:
    """Üretir ve YALNIZ içeriği değişen dosyaları yazar (dokunulmayan dosyanın mtime'ı korunur). Yazılan
    göreli yollar döner. Hiçbir şey SİLMEZ."""
    kok = pathlib.Path(kok)
    yazilan = []
    for goreli, icerik in uret(kok, kadro).items():
        hedef = kok / goreli
        if hedef.is_file() and hedef.read_bytes() == icerik:
            continue
        hedef.parent.mkdir(parents=True, exist_ok=True)
        hedef.write_bytes(icerik)
        yazilan.append(goreli)
    return yazilan


def kontrol(kok: pathlib.Path = REPO, kadro=None) -> list[str]:
    """Ayrışan/eksik/fazla dosya açıklamaları; boş liste = güncel. YAZMAZ."""
    kok = pathlib.Path(kok)
    beklenen = uret(kok, kadro)
    bulgular = []
    for goreli, icerik in beklenen.items():
        hedef = kok / goreli
        if not hedef.is_file():
            bulgular.append(f"eksik: {goreli} — üretilmemiş (--yaz)")
        elif hedef.read_bytes() != icerik:
            bulgular.append(f"ayrışan: {goreli} — kaynaktan geride ya da elle düzenlenmiş (--yaz)")
    for goreli in _fazlalar(kok, beklenen):
        bulgular.append(f"fazla: {goreli} — kadroda aktif bir botun üretilmiş dosyası değil "
                        "(üreteç SİLMEZ; kaldırmak bir karardır)")
    return bulgular


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Aktif botların sohbet profillerini rapor profillerinden üret.")
    ap.add_argument("--yaz", action="store_true", help="üret ve yaz (yalnız içeriği değişen dosyalar)")
    ap.add_argument("--kontrol", action="store_true", help="yazma; diskteki dosyalar güncel mi (0/1)")
    ns = ap.parse_args(argv)
    if ns.yaz == ns.kontrol:
        print("kullanım: tam olarak biri — --yaz ya da --kontrol (ikisi birden ya da hiçbiri geçersiz)",
              file=sys.stderr)
        return 2
    if ns.kontrol:
        bulgular = kontrol()
        for b in bulgular:
            print(b)
        if not bulgular:
            print(f"güncel: {SOHBET_KOK}")
        return 1 if bulgular else 0
    yazilan = yaz()
    for y in yazilan:
        print(f"yazıldı: {y}")
    if not yazilan:
        print(f"değişiklik yok: {SOHBET_KOK}")
    fazla = [b for b in kontrol() if b.startswith("fazla:")]
    for b in fazla:
        print(f"UYARI {b}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
