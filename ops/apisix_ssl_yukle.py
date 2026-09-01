#!/usr/bin/env python3
"""ops/apisix_ssl_yukle.py — sertifika+anahtarı APISIX Admin API'ye (loopback) yükler.

SÖZLEŞME KOMUT SATIRIDIR (CLAUDE.md §1). A1'de koşar:
    python3 ops/apisix_ssl_yukle.py --cert <crt> --key <key> --sni <ad> [--id kapi-tls]

TSK-089 Faz 3 (2026-09-01): ilk kullanım self-signed geçici sertifika; alan adı kararı
gelince certbot'un deploy-hook'u da BU betiği çağırır (Admin API push otomasyonu — elle
yükleme kalıcı yol değildir). Anahtar malzemesi YALNIZ bu makinede dosyadan okunur ve
127.0.0.1:9180'e gider; hiçbir çıktıya/loga yazılmaz. Admin anahtarı /opt/apisix/.env-apisix.
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request

ADMIN = "http://127.0.0.1:9180/apisix/admin"
ENV_APISIX = "/opt/apisix/.env-apisix"


def admin_anahtari() -> str:
    for satir in open(ENV_APISIX):
        if satir.startswith("APISIX_ADMIN_KEY="):
            return satir.split("=", 1)[1].strip()
    raise SystemExit(f"APISIX_ADMIN_KEY {ENV_APISIX} içinde yok")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="APISIX'e TLS sertifikası yükle (Admin API PUT)")
    ap.add_argument("--cert", required=True, help="PEM sertifika dosyası")
    ap.add_argument("--key", required=True, help="PEM özel anahtar dosyası (çıktıya yazılmaz)")
    ap.add_argument("--sni", required=True, action="append",
                    help="eşleşecek SNI (tekrarlanabilir)")
    ap.add_argument("--id", default="kapi-tls", help="ssl objesi kimliği (varsayılan kapi-tls)")
    a = ap.parse_args(argv)

    govde = json.dumps({"cert": open(a.cert).read(), "key": open(a.key).read(),
                        "snis": a.sni}).encode()
    req = urllib.request.Request(f"{ADMIN}/ssls/{a.id}", data=govde, method="PUT",
                                 headers={"X-API-KEY": admin_anahtari(),
                                          "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            print(f"{a.id}: PUT {r.status} · snis={a.sni}")
            return 0
    except urllib.error.HTTPError as e:
        # Gövde teşhis taşır (şema reddi vb.) ama sertifika/anahtar İÇERMEZ — Admin API hata
        # zarfı isteği geri yansıtmaz; yine de 300 baytla kırpıyoruz.
        print(f"{a.id}: PUT HATA {e.code} {e.read()[:300]!r}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
