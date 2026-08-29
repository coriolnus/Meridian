"""HERMES AJAN YAPILANDIRMASI DEPODA VE GÜVENLİ — v326 (2026-08-27)

NEDEN. §9.0 ölçümü: canlıda `approvals` HİÇ TANIMLI DEĞİL, `terminal` tanımsız (→ local),
`security` tanımsız. Tek gerçek savunma `pre_tool_call → meridian-guard.sh` ve o kanca kendi
şerhinde "parse edilemezse FAIL-OPEN" diyor — kalkan değil desen filtresi.

VE ÖLÇÜLEN ASIL RİSK: yeni bir profil bu kancayı OTOMATİK MİRAS ALMAZ. `--clone` taşır,
sıfırdan kurulan profil KORUMASIZ doğar. Bot çoğaltmak kancasız ajan çoğaltmaktır.

Çare kural değil KONTROL: yapılandırma depoya alınır, duruş orada BEYAN edilir, ve bu çivi
beyanın bozulmadığını her koşumda sınar. `dagit` F9 de canlı ile depo arasındaki sürüklenmeyi
raporlar (F9 ENGELLEMEZ, RAPORLAR — kimlik kapısı doğruluk kapısı değildir).
"""
from __future__ import annotations

import pathlib

import pytest

yaml = pytest.importorskip("yaml")

KOK = pathlib.Path(__file__).resolve().parent.parent
CFG = KOK / "deploy/hermes/config.yaml"
DAGIT = KOK / "dagit.sh"

GEREKLI_DENY = ["*dagit.sh*", "*git push*", "*git commit*", "*systemctl*", "*serve.sh*"]


def _cfg() -> dict:
    assert CFG.exists(), f"{CFG} YOK — ajan yapılandırması versiyonlanmamış"
    return yaml.safe_load(CFG.read_text(encoding="utf-8")) or {}


def test_guard_kancasi_TANIMLI():
    """Kanca yoksa ajan `state/`e, sırlara ve Alpaca emrine dokunabilir."""
    h = (_cfg().get("hooks") or {}).get("pre_tool_call") or []
    kancalar = [str(e.get("command", "")) for e in h]
    assert any("meridian-guard.sh" in c for c in kancalar), (
        f"pre_tool_call kancası meridian-guard.sh'e gitmiyor: {kancalar}")


def test_cron_modu_DENY():
    """Başsız cron tehlikeli komutu ONAYLAYAMAZ. Bu pazarlığa kapalı (§9.2)."""
    a = _cfg().get("approvals") or {}
    assert a.get("cron_mode") == "deny", f"approvals.cron_mode={a.get('cron_mode')!r}, 'deny' olmalı"


def test_deny_listesi_TAM():
    """--yolo'da bile geçersiz olan yasaklar. Eksik biri, o kapının açık olması demektir."""
    a = _cfg().get("approvals") or {}
    deny = [str(x) for x in (a.get("deny") or [])]
    eksik = [d for d in GEREKLI_DENY if d not in deny]
    assert not eksik, f"deny listesinde eksik desen(ler): {eksik} · mevcut: {deny}"


def test_deny_desenleri_IKI_YANDAN_SARILI():
    """ÖLÇÜLMÜŞ DELİK (denetim 2026-08-29): `git push*` ve `git commit*` ÖN EKE ÇAKILIYDI. Hermes
    deny listesini `fnmatch` ile UYGULAR ve fnmatch TÜM DİZGEYİ eşler — yani şu üç biçim yasağın
    ALTINDAN geçiyordu:

        cd /opt/meridian && git push        (bileşik komut — ajanın en doğal yazımı)
        /usr/bin/git push                   (mutlak yol)
        ' git commit -m ...'                (baştaki tek boşluk)

    Listedeki öteki üç desen zaten iki yandan sarılıydı; bu ikisi kopyalanırken sarmalayıcıyı
    kaybetmiş. Kural: yasak bir KOMUTU yasaklar, komutun SATIR BAŞINDA olmasını değil."""
    a = _cfg().get("approvals") or {}
    deny = [str(x) for x in (a.get("deny") or [])]
    assert deny, "deny listesi boş"
    sarilmamis = [d for d in deny if not (d.startswith("*") and d.endswith("*"))]
    assert not sarilmamis, (
        f"iki yandan sarılmamış desen(ler): {sarilmamis} — `cd /x && <komut>`, mutlak yol ve "
        f"baştaki boşluk bu yasağın altından geçer")


def test_yapilandirmada_SIR_YOK():
    """Bu dosya versiyonlanıyor. İçine bir anahtar sızarsa git geçmişine kalıcı girer."""
    metin = CFG.read_text(encoding="utf-8")
    import re
    supheli = re.findall(r"(?i)(api[_-]?key|secret|token|password)\s*:\s*\S+", metin)
    supheli = [s for s in supheli if "***" not in s]
    assert not supheli, f"yapılandırmada sır görünümlü satır: {supheli}"


def test_dagit_F9_bu_dosyayi_IZLIYOR():
    """Depoda beyan edilen duruş, canlıdakiyle karşılaştırılmıyorsa beyan bir dilektir."""
    metin = DAGIT.read_text(encoding="utf-8")
    assert "deploy/hermes/config.yaml|/home/ubuntu/.hermes/config.yaml" in metin, (
        "F9_LISTE config.yaml'ı izlemiyor — canlı duruş sessizce sürüklenebilir")
