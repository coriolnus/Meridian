#!/usr/bin/env python3
"""ops/apisix_uygula.py — routes.yaml'ı APISIX Admin API'ye idempotent uygular + drift denetler.

SÖZLEŞME KOMUT SATIRIDIR (CLAUDE.md §1). A1'de koşar (admin 9180 yalnız loopback):
    python3 apisix_uygula.py                # KURU: ne değişecek, yazMAZ
    python3 apisix_uygula.py --uygula       # rotaları PUT'la (idempotent — id'li PUT)
    python3 apisix_uygula.py --denetle      # DRIFT: etcd'deki rotalar ↔ routes.yaml kıyası
                                            #   (tünel-CRUD sapması TSK-089'un adlı riski)

TEK KAYNAK: deploy/apisix/routes.yaml. `?ttl=` HİÇBİR istekte kullanılmaz (kaynağı sessizce
siler — TSK-089). Sır taşınmaz: $ENV:// referansları OLDUĞU GİBİ gider, çözüm APISIX'te.
Admin anahtarı /opt/apisix/.env-apisix'ten okunur, hiçbir çıktıya yazılmaz.
Drift kıyası NORMALİZE edilmiş gövdede: Admin API'nin eklediği alanlar (create_time,
update_time, status, priority varsayılanı) kıyastan düşülür — yalnız bizim beyan ettiğimiz
alanlar kıyaslanır (uri + plugins).
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
import urllib.request

KOK = pathlib.Path(__file__).resolve().parents[1]
ROTA_DOSYASI = KOK / "deploy" / "apisix" / "routes.yaml"
ENV_DOSYASI = pathlib.Path("/opt/apisix/.env-apisix")
BASE = "http://127.0.0.1:9180/apisix/admin"


def anahtar() -> str:
    for satir in ENV_DOSYASI.read_text().splitlines():
        if satir.startswith("APISIX_ADMIN_KEY="):
            return satir.split("=", 1)[1].strip()
    raise SystemExit("APISIX_ADMIN_KEY .env-apisix'te yok")


def api(method: str, yol: str, govde: dict | None = None) -> tuple[int, dict]:
    assert "ttl" not in yol, "?ttl= YASAK (kaynağı sessizce siler — TSK-089)"
    req = urllib.request.Request(
        BASE + yol,
        data=json.dumps(govde).encode() if govde is not None else None,
        method=method, headers={"X-API-KEY": anahtar(), "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}")


def rotalar() -> list[dict]:
    import yaml
    veri = yaml.safe_load(ROTA_DOSYASI.read_text())
    assert isinstance(veri, dict) and "rotalar" in veri, "routes.yaml şeması: üst anahtar 'rotalar'"
    return veri["rotalar"]


def _normalize(rota: dict) -> dict:
    """Kıyas gövdesi: yalnız beyan ettiğimiz alanlar (uri + plugins)."""
    return {"uri": rota.get("uri"), "plugins": rota.get("plugins")}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="APISIX rota uygulayıcı + drift denetçisi")
    ap.add_argument("--uygula", action="store_true", help="rotaları Admin API'ye PUT'la")
    ap.add_argument("--denetle", action="store_true", help="etcd ↔ routes.yaml drift kıyası")
    a = ap.parse_args(argv)

    beyan = {r["id"]: r for r in rotalar()}
    st, mevcut_ham = api("GET", "/routes")
    assert st == 200, f"Admin API GET /routes {st}"
    mevcut = {}
    for kalem in (mevcut_ham.get("list") or []):
        v = kalem.get("value") or {}
        mevcut[v.get("id") or kalem.get("key", "?").rsplit("/", 1)[-1]] = v

    if a.denetle:
        drift = []
        for rid, r in beyan.items():
            if rid not in mevcut:
                drift.append(f"EKSİK etcd'de: {rid}")
            elif _normalize(mevcut[rid]) != _normalize(r):
                drift.append(f"AYRIK: {rid} (etcd gövdesi routes.yaml'dan farklı)")
        for rid in mevcut:
            if rid not in beyan:
                drift.append(f"BEYANSIZ etcd rotası: {rid} (tünel-CRUD sapması?)")
        print(json.dumps({"drift": drift, "beyan_n": len(beyan), "etcd_n": len(mevcut)},
                         ensure_ascii=False, indent=1))
        return 1 if drift else 0

    for rid, r in beyan.items():
        govde = {"uri": r["uri"], "plugins": r["plugins"]}
        if a.uygula:
            st, cevap = api("PUT", f"/routes/{rid}", govde)
            print(f"{rid}: PUT {st}")
            if st not in (200, 201):
                print(json.dumps(cevap, ensure_ascii=False)[:300], file=sys.stderr)
                return 2
        else:
            durum = "YENİ" if rid not in mevcut else (
                "AYNI" if _normalize(mevcut[rid]) == _normalize(r) else "DEĞİŞECEK")
            print(f"{rid}: {durum} (kuru koşu — yazılmadı)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
