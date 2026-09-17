#!/usr/bin/env python3
"""ops/apisix_uygula.py — routes.yaml'ı APISIX Admin API'ye idempotent uygular + drift denetler.

SÖZLEŞME KOMUT SATIRIDIR (CLAUDE.md §1). A1'de koşar (admin 9180 yalnız loopback):
    python3 apisix_uygula.py                # KURU: ne değişecek, yazMAZ
    python3 apisix_uygula.py --uygula       # rotaları PUT'la (idempotent — id'li PUT)
    python3 apisix_uygula.py --denetle      # DRIFT: etcd'deki rotalar ↔ routes.yaml kıyası
                                            #   (tünel-CRUD sapması TSK-089'un adlı riski)

TEK KAYNAK: deploy/apisix/routes.yaml. `?ttl=` HİÇBİR istekte kullanılmaz (kaynağı sessizce
siler — TSK-089). Sır taşınmaz: $ENV:// referansları OLDUĞU GİBİ gider, çözüm APISIX'te.

ADMIN ANAHTARI — İKİ KANAL, SIRALI (TSK-064 Faz-1C, `docs/TASARIM-SIR-YOL1-2026-09-03.md` §3.4).
Önce CREDENTIAL dosyası (`/etc/meridian/apisix_admin_key`, 0400 root), bulunamazsa `.env-apisix`
YEDEĞİ. Değer hiçbir çıktıya yazılmaz; okunan KANALIN ADI her koşumda stderr'e bildirilir
(`kanal_bildir`) — "araç hangi kanaldan okudu" sorusu Faz-1C'nin kabul ölçütüdür ve bildirilmeyen
bir kanal ölçülmemiş bir kanaldır (Yasa 6; okuyucu OPERATÖRDÜR).
YEDEK BURADA KALICIDIR, geçici değil: `.env-apisix` apisix konteynerinin `--env-file`ıdır ve
`APISIX_ADMIN_KEY` satırı kapının KENDİ `config.yaml` çözümü için orada YAŞAMAYA DEVAM EDER
(B sınıfı yarım kazanım, spec §2). Yani TSK-049 faz-2'deki gibi "sonra silinecek satır" DEĞİL,
BAŞKA BİR TÜKETİCİNİN kanalıdır — bu araç ikisini de tanımak zorundadır.
KİMLİK/İZİN KAPISI OPERATÖRDE: 0400 root bir kaynağı `ubuntu` OKUYAMAZ, yani credential kanalı
ancak `sudo python3 ops/apisix_uygula.py …` ile okunur. Okunamayan bir kaynak `PermissionError`
verir ve "anahtar yok" gibi görünürdü — o yüzden düşüş SESSİZ değil: iki kanal da boşsa hata
metni izin sınıfını ADIYLA anar. Çivi: `tests/test_apisix_admin_credential_v476.py`.

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
#: Sır ADI = credential KİMLİĞİ = `.env` ALAN ADI. Üçü ayrışsaydı geçiş betiği bir dosyaya yazar,
#: bu araç başka bir adı arardı (v439 F4'ün bu yüzeydeki karşılığı).
ADMIN_ALAN = "APISIX_ADMIN_KEY"
#: Faz-1C credential kaynağı (0400 root:root). `deploy/sir_envanteri.yaml` → `rotasyon_kopyalari`
#: `apisix-admin` bloğunda beyanlıdır ve `sir_rotasyon.sh --apisix-admin` onu döndürür; üç yüzeyin
#: ayrışmadığı v476 E1/E2/E3 ile ölçülür.
KRED_DOSYASI = pathlib.Path("/etc/meridian/apisix_admin_key")
ENV_DOSYASI = pathlib.Path("/opt/apisix/.env-apisix")
BASE = "http://127.0.0.1:9180/apisix/admin"


def _kredensiyel_degeri(ham: str) -> str | None:
    """Credential kaynağının BİÇİM SÖZLEŞMESİ — `meridian.secrets.credential_oku` ile AYNI.

    KOPYA, VE BEYANLI. Bu araç A1'de sistem `python3`üyle koşar (`ops/` sözleşmesi KOMUT
    SATIRIdır) ve `meridian`ı ithal ETMEZ: pytest dışında `meridian.obs`a ulaşan bir ithal canlı
    yerel deftere yazar (CLAUDE.md §2, üç vaka 2026-08-30). Kopya kaçınılmaz olduğu için
    DAVRANIŞ eşitliği ayrışma çivisine bağlıdır (v476 A6): aynı ham içerik iki ayrıştırıcıda
    aynı sonucu vermeli.

    Sözleşme: `strip()` → İLK satır → isteğe bağlı `<AD>=` öneki → boş ise `None`. Öneki tanımak
    bir kolaylık değil ÖLÇÜLMÜŞ bir kazadır: operatörün `.env` satırını kaynağa kopyalaması
    öngörülebilir. BOŞ DEĞER `None`'DIR — "ayarlı ama değersiz" bir kaynak yedeğe düşülmesini
    ENGELLERDİ ve araç boş bir `X-API-KEY` ile 401 alırdı (2026-09-07 sınıfı: 1 baytlık satır
    sonu bir birimi sessizce yetkisiz bıraktı)."""
    satirlar = ham.strip().splitlines()
    deger = satirlar[0].strip() if satirlar else ""
    onek = f"{ADMIN_ALAN}="
    if deger.startswith(onek):
        deger = deger[len(onek):].strip()
    return deger or None


def _kredensiyelden() -> str | None:
    try:
        ham = KRED_DOSYASI.read_text(encoding="utf-8")
    # credential kanalı İSTEĞE BAĞLIDIR (dosya A1'de elle kurulur) — dosya-yok, izin ya da kodlama
    # hatasının tek doğru cevabı yedek kanala düşmektir; iki kanal da boşsa hüküm `anahtar()`ta
    # sessiz-yutma: isteğe bağlı kanal okunamadı → yedeğe düşülür; hüküm ve izin sınıfı anahtar()ta ADIYLA
    except (OSError, ValueError):
        return None
    return _kredensiyel_degeri(ham)


def _env_dosyasindan() -> str | None:
    """`.env-apisix`teki `APISIX_ADMIN_KEY=` satırı — TIRNAK SOYULMAZ.

    ÖLÇÜLMÜŞ BİR KARAR, ihmal değil: bu dosya docker'ın `--env-file`ıdır ve docker tırnağı
    SOYMAZ. `APISIX_ADMIN_KEY="x"` yazılırsa konteynerin gördüğü değer tırnaklar DAHİL `"x"`tir;
    araç soysaydı kapıyla AYRI bir değer kullanır, `X-API-KEY` 401 alır ve teşhis "anahtar
    yanlış" derken hata soyma kodunda olurdu. Mevcut davranış aynen korunur (çivi: v476 A7)."""
    try:
        ham = ENV_DOSYASI.read_text(encoding="utf-8")
    # yedek kanal da isteğe bağlıdır (bu makinede dosya YOKTUR ve olmaması bir ihlal değil ölçüm
    # sonucudur) — "okunamadı" ile "satır yok" aynı cevaba düşer
    # sessiz-yutma: isteğe bağlı yedek kanal okunamadı → None; iki kanal da boşken hükmü anahtar() verir
    except (OSError, ValueError):
        return None
    for satir in ham.splitlines():
        if satir.startswith(f"{ADMIN_ALAN}="):
            return satir.split("=", 1)[1].strip() or None
    return None


def anahtar_kanali() -> tuple[str | None, str]:
    """`(değer, KANAL ADI)` — okuma SIRASI bu fonksiyonda TEK yerde yaşar.

    İki okuyucu var (`anahtar` değeri, `kanal_bildir` raporu) ve ikisi de BURADAN geçer: ayrı
    ayrı yazılsalardı rapor bir kanalı, istek başka bir kanalı söylerdi — tek-kaynak yasasının
    tam olarak yasakladığı hâl. Dönen ikinci alan bir AD'dır; DEĞER ASLA rapora girmez."""
    deger = _kredensiyelden()
    if deger is not None:
        return deger, f"credential dosyası {KRED_DOSYASI}"
    deger = _env_dosyasindan()
    if deger is not None:
        return deger, f"{ADMIN_ALAN} satırı {ENV_DOSYASI} (YEDEK — kapının kendi kanalı)"
    return None, "YOK (iki kanal da boş/okunamadı)"


def anahtar() -> str:
    deger, kanal = anahtar_kanali()
    if deger is None:
        raise SystemExit(
            f"{ADMIN_ALAN} okunamadı — kanal: {kanal}\n"
            f"  credential: {KRED_DOSYASI} (0400 root) · yedek: {ENV_DOSYASI}\n"
            f"  Kaynak 0400 root ise bu aracı `sudo python3 ops/apisix_uygula.py …` ile koş:\n"
            f"  izin hatası 'anahtar yok' gibi görünür ve teşhis yanlış yerde aranır.")
    return deger


def kanal_bildir() -> None:
    """Okunan KANALI stderr'e bildirir — DEĞERİ DEĞİL, ve stdout'a DEĞİL.

    STDOUT BİR SÖZLEŞMEDİR: `--denetle` çıktısının TAMAMI JSON'dur (çivisi v364; okuyucusu
    operatör ve betikler). Rapor oraya basılsaydı sözleşme sessizce kırılırdı. Değer yokken de
    bir satır basılır: "okunamadı" bir bilgi YOKLUĞU değil, bir ÖLÇÜM SONUCUDUR."""
    _, kanal = anahtar_kanali()
    print(f"admin anahtarı kanalı: {kanal} (DEĞER BASILMAZ)", file=sys.stderr)


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

    # KANAL RAPORU AĞDAN ÖNCE: koşum bir Admin API arızasında düşse bile operatör hangi kanalın
    # okunduğunu GÖRMÜŞ olur — Faz-1C'nin kabul ölçütü tam olarak bu satırdır.
    kanal_bildir()

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
