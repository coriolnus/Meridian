"""v463 — TSK-178: dört bot damga dosyası (`*_brifingi_damga.json`) YETİM DEĞİL, BEYANLI (2026-09-12).

ÖLÇÜLEN DURUM (A1 events, 2026-08-31 20:55Z MECHANISM_STALE `yeniden_hesap:orphan_state_files`):
"4 dosya diskte var ama hiçbir modül okumuyor: bekci/karne/oneri/sef_brifingi_damga.json". Ölçüm
(grep, 2026-09-12): dördünün de yazarı VE okuyucusu AYNI `ops/<bot>_brifingi.py` modülüdür
(`store.update_json(DAMGA_DOSYA, …)` yazar, `store.read_json(DAMGA_DOSYA, …)` okur — kadans,
sessizlik sayacı, son brifing künyesi). `codelaw.artifact_graph` yalnız `meridian/` kökünü tarar
(`_py_files("meridian")`), `ops/` modül-içi okumayı GÖREMEZ — `pool_exhausted_seen.json` /
`monotonic_amnesty.json` ile aynı sınıf. Doğru çıkış (ROADMAP TSK-178 metni): okuyucu VARSA
`codelaw.DECLARED_SINKS` gerekçeli beyan; `oneri_akibet.jsonl` listede DEĞİL — motor okuyucusu var
(`meridian/mukerrerlik.py`), alarm da onu saymıyordu.

Numara v463: ölçüldü (ana checkout + worktree'ler; v462 denetçi rotası, v463 boş).

ÇİVİLER
  1. Dört damga dosyası `DECLARED_SINKS`te ve her beyan yazar+okuyucu modülünü ADIYLA söyler.
  2. Beyan YALAN DEĞİL: her `ops/<bot>_brifingi.py` gerçekten hem yazıyor (`update_json(DAMGA_DOSYA`)
     hem okuyor (`read_json(DAMGA_DOSYA`) ve `DAMGA_DOSYA` sabiti tam o adı taşıyor — beyan
     kaynaktan ayrışırsa (dosya adı değişir, okuma kalkar) çivi öter; beyan 'kimsenin bakmadığı
     çöplüğe' dönmez (codelaw'un kendi kuralı).
  3. Dedektör sahnede dört dosya DURURKEN onları yetim saymaz — POZİTİF KONTROLLÜ: aynı sahnedeki
     uydurma yetim GÖRÜLÜR (v454 e2 deseni), yoksa 'yetim yok' hiç çalışmayan dedektörde de yeşildir.
  4. `codelaw.stale_claims` bu dört beyanı ÇÜRÜK saymaz (kind=sink iddiası: meridian'da okuyucu yok —
     doğru; bir gün motor okursa beyan kalkmalı, çivi o gün öter).
"""
from __future__ import annotations

import json
import pathlib
import re

import pytest

from meridian import codelaw, config, recompute

REPO = pathlib.Path(__file__).resolve().parents[1]
DAMGALAR = {
    "bekci_brifingi_damga.json": "bekci_brifingi.py",
    "karne_brifingi_damga.json": "karne_brifingi.py",
    "oneri_brifingi_damga.json": "oneri_brifingi.py",
    "sef_brifingi_damga.json": "sef_brifingi.py",
}


def test_civi1_dort_damga_DECLARED_SINKS_te_ve_beyan_modulu_ADIYLA_soyler():
    for dosya, modul in DAMGALAR.items():
        assert dosya in codelaw.DECLARED_SINKS, f"`{dosya}` beyansız — TSK-178 yetimi geri gelir"
        beyan = codelaw.DECLARED_SINKS[dosya]
        assert f"ops/{modul}" in beyan, f"`{dosya}` beyanı yazar/okuyucu modülünü adıyla söylemiyor: {beyan[:120]}"
        assert "update_json" in beyan and "read_json" in beyan, beyan[:160]


@pytest.mark.parametrize("dosya,modul", sorted(DAMGALAR.items()))
def test_civi2_beyan_kaynakla_ORTUSUR_yazar_ve_okuyucu_ayni_modulde(dosya, modul):
    src = (REPO / "ops" / modul).read_text(encoding="utf-8")
    assert re.search(rf'^DAMGA_DOSYA = "{re.escape(dosya)}"$', src, re.M), (
        f"`ops/{modul}` `DAMGA_DOSYA` sabiti `{dosya}` DEĞİL — beyan kaynaktan ayrıştı")
    assert "store.update_json(DAMGA_DOSYA" in src, f"`ops/{modul}` damgayı YAZMIYOR — beyan yalan"
    assert "store.read_json(DAMGA_DOSYA" in src, f"`ops/{modul}` damgayı OKUMUYOR — gerçek yetim, beyan değil okuyucu gerekir"


def test_civi3_dedektor_dort_damgayi_YETIM_SAYMAZ_pozitif_kontrollu(sandbox_state):
    kok = pathlib.Path(config.STATE)
    for dosya in DAMGALAR:
        (kok / dosya).write_text(json.dumps({"son": "2026-09-12"}), encoding="utf-8")
    uydurma = "uydurma_yetim_v463.json"
    (kok / uydurma).write_text(json.dumps({"a": 1}), encoding="utf-8")

    satir = recompute._orphan_state_files()
    detay = satir["detail"]
    assert uydurma in detay, (
        f"POZİTİF KONTROL DÜŞTÜ: dedektör bu sahnede uydurma yetimi bile görmüyor ({satir})")
    for dosya in DAMGALAR:
        assert dosya not in detay, f"`{dosya}` hâlâ yetim listesinde: {detay}"


def test_civi4_beyanlar_stale_claims_te_CURUK_degil():
    curuk = {c.get("artifact") for c in codelaw.stale_claims()}
    for dosya in DAMGALAR:
        assert dosya not in curuk, (
            f"`{dosya}` beyanı ÇÜRÜK sayıldı — motorda bir okuyucu doğduysa beyan KALKMALI (codelaw kuralı)")
