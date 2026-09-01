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

KİMLİKLER DE TEK KAYNAKTAN (Faz 3-4, 2026-09-01). routes.yaml iki OPSİYONEL bölüm daha taşır:
`tuketici_gruplari:` ({id, plugins}) ve `tuketiciler:` ({username, plugins, opsiyonel group_id}).
Bölüm yoksa boş liste sayılır — rota-only yaml'lar aynen çalışır (geriye uyumluluk).
UYGULAMA SIRASI rotalar → gruplar → tüketiciler: bir tüketici dayandığı grup etcd'de yokken
PUT edilemez. Drift denetimi artık kimlikleri de kapsar; kapsamasaydı "beyansız rota" yakalanıp
"beyansız tüketici" (elle-CRUD'la açılmış bir anahtar) sessizce yaşardı — denetimin kör noktası.
`tuketici_drift`/`grup_drift` alanları bölümler BOŞ olsa da çıktıda DURUR: okuyucu "bölüm yok"
ile "alan yok"u ayırt edemezdi.
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


def _yaml() -> dict:
    import yaml
    veri = yaml.safe_load(ROTA_DOSYASI.read_text())
    assert isinstance(veri, dict) and "rotalar" in veri, "routes.yaml şeması: üst anahtar 'rotalar'"
    return veri


def rotalar() -> list[dict]:
    return _yaml()["rotalar"]


def tuketici_gruplari() -> list[dict]:
    """OPSİYONEL bölüm — yoksa boş liste (rota-only yaml'lar kırılmaz)."""
    return _yaml().get("tuketici_gruplari") or []


def tuketiciler() -> list[dict]:
    """OPSİYONEL bölüm — yoksa boş liste (rota-only yaml'lar kırılmaz)."""
    return _yaml().get("tuketiciler") or []


def _normalize(rota: dict) -> dict:
    """Kıyas gövdesi: yalnız beyan ettiğimiz alanlar (uri + plugins + varsa upstream).

    `upstream` yalnız ANAHTAR VARSA girer (Faz-1 ai-proxy rotaları upstream'siz — geriye
    uyumluluk). etcd tarafının upstream'i `_budanmis_mevcut`'ta beyan edilen anahtarlara
    ÖNCEDEN budanır — burada ekstra filtre gerekmez, aksi halde Admin API'nin enjekte ettiği
    hash_on/pass_host/scheme varsayılanı sahte drift üretirdi (ölçüldü: pano-ingress 503).
    """
    out = {"uri": rota.get("uri"), "plugins": rota.get("plugins")}
    if "upstream" in rota:
        out["upstream"] = rota["upstream"]
    return out


def _budanmis_mevcut(beyan: dict, mevcut: dict) -> dict:
    """etcd rota upstream'ini yalnız BEYAN EDİLEN anahtarlara buda.

    Admin API upstream'e varsayılan enjekte eder (hash_on, pass_host, scheme varsayılanı gibi
    routes.yaml'da hiç yazmadığımız alanlar) — bunlar kıyastan düşülür, aksi halde her PUT
    sonrası sahte drift doğar. Aynı felsefe: dış `_normalize` zaten create_time/update_time/
    status/priority varsayılanını böyle düşürüyor; burada nesting bir seviye içeri iniyor.
    Beyan upstream'i YOKSA budama yapılmaz — etcd'de kalan tam gövde "BEYANSIZ" kıyasını
    (elle-CRUD sapması) doğru tetiklesin diye.
    """
    budanmis: dict = {}
    for kimlik, deger in mevcut.items():
        deger = dict(deger)
        beyan_u = (beyan.get(kimlik) or {}).get("upstream")
        etcd_u = deger.get("upstream")
        if beyan_u is not None and etcd_u is not None:
            deger["upstream"] = {k: etcd_u.get(k) for k in beyan_u}
        budanmis[kimlik] = deger
    return budanmis


def _normalize_grup(grup: dict) -> dict:
    """Kıyas gövdesi: yalnız beyan ettiğimiz alanlar (id + plugins)."""
    return {"id": grup.get("id"), "plugins": grup.get("plugins")}


def _normalize_tuketici(t: dict) -> dict:
    """Kıyas gövdesi: username + group_id + plugins.

    `group_id` her iki tarafta da .get() ile okunur: beyanda yokken etcd'de de yoksa ikisi de
    None'dır ve sahte drift doğmaz. Admin API'nin eklediği create_time/update_time bu sözlüğe
    hiç girmediği için kıyastan doğal olarak düşer.
    """
    return {"username": t.get("username"), "group_id": t.get("group_id"),
            "plugins": t.get("plugins")}


def _mevcut(yol: str, kimlik_alani: str) -> dict:
    """Admin API GET listesini {kimlik: değer} sözlüğüne indirger."""
    st, ham = api("GET", yol)
    assert st == 200, f"Admin API GET {yol} {st}"
    out = {}
    for kalem in (ham.get("list") or []):
        v = kalem.get("value") or {}
        out[v.get(kimlik_alani) or kalem.get("key", "?").rsplit("/", 1)[-1]] = v
    return out


def _drift(beyan: dict, mevcut: dict, normalize, tur: str) -> list[str]:
    """Tek yönlü değil ÇİFT yönlü kıyas: eksik + ayrık + BEYANSIZ (elle-CRUD sapması)."""
    d = []
    for k, v in beyan.items():
        if k not in mevcut:
            d.append(f"EKSİK etcd'de: {k}")
        elif normalize(mevcut[k]) != normalize(v):
            d.append(f"AYRIK: {k} (etcd gövdesi routes.yaml'dan farklı)")
    for k in mevcut:
        if k not in beyan:
            d.append(f"BEYANSIZ etcd {tur}: {k} (tünel-CRUD sapması?)")
    return d


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="APISIX rota + tüketici uygulayıcı ve drift denetçisi")
    ap.add_argument("--uygula", action="store_true",
                    help="rotaları, tüketici gruplarını ve tüketicileri Admin API'ye PUT'la")
    ap.add_argument("--denetle", action="store_true",
                    help="etcd ↔ routes.yaml drift kıyası (rota + grup + tüketici)")
    a = ap.parse_args(argv)

    beyan = {r["id"]: r for r in rotalar()}
    g_beyan = {g["id"]: g for g in tuketici_gruplari()}
    t_beyan = {t["username"]: t for t in tuketiciler()}

    mevcut = _budanmis_mevcut(beyan, _mevcut("/routes", "id"))
    g_mevcut = _mevcut("/consumer_groups", "id")
    t_mevcut = _mevcut("/consumers", "username")

    if a.denetle:
        cikti = {
            "drift": _drift(beyan, mevcut, _normalize, "rotası"),
            "grup_drift": _drift(g_beyan, g_mevcut, _normalize_grup, "tüketici grubu"),
            "tuketici_drift": _drift(t_beyan, t_mevcut, _normalize_tuketici, "tüketicisi"),
            "beyan_n": len(beyan), "etcd_n": len(mevcut),
            "grup_beyan_n": len(g_beyan), "grup_etcd_n": len(g_mevcut),
            "tuketici_beyan_n": len(t_beyan), "tuketici_etcd_n": len(t_mevcut),
        }
        print(json.dumps(cikti, ensure_ascii=False, indent=1))
        return 1 if (cikti["drift"] or cikti["grup_drift"] or cikti["tuketici_drift"]) else 0

    # UYGULAMA SIRASI: rotalar → gruplar → tüketiciler. Tüketici dayandığı grup etcd'de
    # yokken PUT edilemez; sıra bir stil tercihi değil bağımlılıktır.
    plan: list[tuple[str, str, dict, dict, dict, object]] = []
    for rid, r in beyan.items():
        govde = {"uri": r["uri"], "plugins": r["plugins"]}
        # upstream yalnız ANAHTAR VARSA gövdeye girer (uydurma yasağı + geriye uyumluluk):
        # eksikliği "missing upstream configuration in Route" 503'ü üretti (pano-ingress + fmp-veri).
        if "upstream" in r:
            govde["upstream"] = r["upstream"]
        plan.append((rid, f"/routes/{rid}", govde, r, mevcut, _normalize))
    for gid, g in g_beyan.items():
        plan.append((gid, f"/consumer_groups/{gid}", {"id": gid, "plugins": g["plugins"]},
                     g, g_mevcut, _normalize_grup))
    for ad, t in t_beyan.items():
        govde = {"username": ad, "plugins": t["plugins"]}
        # group_id yalnız BEYAN EDİLDİĞİNDE gider — yoksa gövdeye uydurulmaz (uydurma yasağı).
        if t.get("group_id") is not None:
            govde["group_id"] = t["group_id"]
        plan.append((ad, f"/consumers/{ad}", govde, t, t_mevcut, _normalize_tuketici))

    for ad, yol, govde, kaynak, halihazir, normalize in plan:
        if a.uygula:
            st, cevap = api("PUT", yol, govde)
            print(f"{ad}: PUT {st}")
            if st not in (200, 201):
                print(json.dumps(cevap, ensure_ascii=False)[:300], file=sys.stderr)
                return 2
        else:
            durum = "YENİ" if ad not in halihazir else (
                "AYNI" if normalize(halihazir[ad]) == normalize(kaynak) else "DEĞİŞECEK")
            print(f"{ad}: {durum} (kuru koşu — yazılmadı)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
