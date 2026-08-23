#!/usr/bin/env python3
"""aylik_bucket_kopya.py — seans-içi bar arşivinin ÖNCEKİ AY tar'ını OCI bucket'ına yükler.

NEDEN VAR (E-kod [4], operatör partisi 2026-08-23). `state/bars_intraday/` ve
`state/intraday_bars/` TTL'li Redis akışının TEK KALICI ARŞİVİDİR (meridian-backup.service
başlığındaki beyan: "düşerlerse geri gelmezler"). Bugün bu iki dizin YALNIZ gece tar'ında ve
Mac'e çekilen kopyada yaşıyor: ikisi de tek-medya. Litestream aşama-2 (2026-08-23) SQLite
defterini bucket'a çoğaltıyor ama bu iki dizin SQLite DEĞİL — off-box kopyaları YOKTU. Bu birim
o boşluğu ayda bir, ölçülmüş ve doğrulanmış bir nesneyle kapatır.

ÜÇ SÖZLEŞME (hepsi yapısal, yorumla değil kodla/birimle çivili):
  1. YEREL SİLME YOK. Bu betik `state/` altında hiçbir dosyayı silmez/değiştirmez — ve birim
     dosyası (`meridian-aylik-bucket-kopya.service`) `ReadWritePaths=` vermeyerek bunu
     YAPISAL kılar: ProtectSystem=strict altında yazılabilir tek yer PrivateTmp'tir. "Arşivi
     bucket'a taşıdık" diye yereli budayan bir tur, tek kopyayı ağın ucuna bağlardı.
  2. KİMLİK YALNIZ `state/litestream.env`TEN. Sır repoda/komut satırında/journal'de görünmez;
     birim onu `EnvironmentFile=` ile yükler (litestream'in `10-s3-env.conf` deseni birebir).
  3. HEDEF, litestream.yml İLE AYNI KOVA. Sabitler aşağıda BEYANLIdır ve
     `tests/test_e_partisi_v278.py` onları `deploy/oracle-a1/litestream.yml`den okuyup kıyaslar —
     iki yerde ayrışan bir endpoint, yıllar sonra "yedek nerede?" sorusunu cevapsız bırakırdı.

NEDEN saf stdlib (boto3/aws-cli DEĞİL): A1'de ölçüldü (2026-08-23) — `aws`, `rclone`, `s3cmd`
ve `boto3` YOK; kurulmaları yeni bir tedarik-zinciri yüzeyi açardı. SigV4 tek bir PUT için
~40 satırdır ve `hashlib`/`hmac`/`urllib` ile tamamen stdlib'dir. `uv run` DE KULLANILMAZ:
sistem python3'ü yeter, böylece birim .venv/uv-önbelleğine bağımlı değildir (yedek yolu, yedeği
alınan sistemin sağlığına bağlı olmamalıdır).

UYDURMA YASAĞI: yüklenmeyen ay "yüklendi" demez. Dosya bulunamazsa çıkış kodu 1 + neden; PUT
doğrulaması (ETag=MD5) tutmazsa çıkış kodu 1 + iki tarafın özeti basılır. Nesne ZATEN varsa ve
özeti tutuyorsa yeniden yüklenmez ("atlandı" beyanıyla, sessizce değil).

Kullanım:
    python3 deploy/oracle-a1/aylik_bucket_kopya.py            # önceki ay (UTC'ye göre)
    python3 deploy/oracle-a1/aylik_bucket_kopya.py --ay 2026-07
    python3 deploy/oracle-a1/aylik_bucket_kopya.py --kuru     # tar'ı kurar, YÜKLEMEZ (ölçüm)
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import hmac
import json
import os
import pathlib
import sys
import tarfile
import tempfile
import urllib.error
import urllib.request

# ── HEDEF KOVA — `deploy/oracle-a1/litestream.yml`in replica bloğuyla AYNI olmak ZORUNDA ────────
# (çivi: tests/test_e_partisi_v278.py — bu dört sabit yml'den okunup kıyaslanır). `PREFIX`
# litestream'in kendi `litestream/` yolundan AYRI: aynı kovada iki farklı ürün yaşar ve
# litestream'in `retention`ı bizim arşivimize dokunamamalı.
BUCKET = "meridian-bucket"
REGION = "eu-frankfurt-1"
ENDPOINT = "https://frllsrdbjodk.compat.objectstorage.eu-frankfurt-1.oraclecloud.com"
PREFIX = "arsiv/intraday"

STATE = pathlib.Path(os.environ.get("MERIDIAN_STATE", "/opt/meridian/state"))
DIZINLER = ("bars_intraday", "intraday_bars")   # ikisi de arşivlenir: farklı yazarlar, farklı şema


def _onceki_ay(bugun: dt.date) -> str:
    """`YYYY-MM` — bugünün İÇİNDE bulunduğu ayın BİR ÖNCEKİSİ. Yürürlükteki ay BİLEREK atlanır:
    daha kapanmamış bir ayı arşivlemek, eksik bir nesneyi "o ayın arşivi" diye damgalamaktır."""
    ilk = bugun.replace(day=1)
    onceki = ilk - dt.timedelta(days=1)
    return f"{onceki.year:04d}-{onceki.month:02d}"


def _dosyalar(ay: str) -> list[tuple[str, pathlib.Path]]:
    """(arşiv-içi ad, disk yolu) çiftleri — iki dizinin de `AY-*.jsonl` üyeleri, ad sırasında."""
    out: list[tuple[str, pathlib.Path]] = []
    for d in DIZINLER:
        kok = STATE / d
        if not kok.is_dir():
            continue
        for p in sorted(kok.glob(f"{ay}-*.jsonl")):
            out.append((f"{d}/{p.name}", p))
    return out


def _tar_kur(ay: str, dosyalar: list[tuple[str, pathlib.Path]], hedef: pathlib.Path) -> None:
    """tar.gz — arşiv-içi yollar `bars_intraday/…` / `intraday_bars/…` (dizin adı KORUNUR: iki
    dizinde AYNI tarihli dosya var ve düz bir arşiv onları birbirinin üstüne yazardı)."""
    with tarfile.open(hedef, "w:gz") as tf:
        for ad, p in dosyalar:
            tf.add(p, arcname=f"intraday-{ay}/{ad}")


def _ozet(p: pathlib.Path) -> tuple[str, str, int]:
    """(sha256_hex, md5_hex, bayt) — akış hâlinde; 100MB'lık tar belleğe alınmaz."""
    s, m, n = hashlib.sha256(), hashlib.md5(), 0
    with p.open("rb") as f:
        while True:
            blok = f.read(1024 * 1024)
            if not blok:
                break
            s.update(blok); m.update(blok); n += len(blok)
    return s.hexdigest(), m.hexdigest(), n


# ── SigV4 (AWS Signature Version 4, tek istek) ──────────────────────────────────────────────────
def _imza_anahtari(gizli: str, tarih: str, bolge: str, servis: str) -> bytes:
    k = ("AWS4" + gizli).encode()
    for veri in (tarih, bolge, servis, "aws4_request"):
        k = hmac.new(k, veri.encode(), hashlib.sha256).digest()
    return k


def _istek(yontem: str, anahtar: str, *, govde_sha: str, uzunluk: int = 0,
           ek_baslik: dict | None = None, govde=None) -> urllib.request.Request:
    """İmzalı istek. `govde` KURUCUYA verilir, sonradan `req.data = …` ile DEĞİL: `Request.data`
    setter'ı (CPython issue 16464) atama anında `Content-length` başlığını SİLER — o başlık gidince
    urllib dosya nesnesi için uzunluk türetemez ve gövde HİÇ GİTMEZ. Ölçüldü (2026-08-23, yerel
    sahte-S3 uçtan uca koşumu): sunucu 0 bayt aldı ve ETag boş-dosya md5'i döndü; hata ancak
    doğrulama kolunda yakalandı. Sıra bu yüzden sözleşmedir: önce gövde, sonra başlıklar."""
    kimlik = os.environ.get("LITESTREAM_ACCESS_KEY_ID", "")
    gizli = os.environ.get("LITESTREAM_SECRET_ACCESS_KEY", "")
    if not kimlik or not gizli:
        raise SystemExit("!! kimlik YOK: LITESTREAM_ACCESS_KEY_ID/SECRET_ACCESS_KEY boş "
                         "(birim state/litestream.env'i yüklüyor mu? pano Ayarlar'dan girildi mi?)")
    host = ENDPOINT.split("://", 1)[1]
    yol = f"/{BUCKET}/{anahtar}"
    simdi = dt.datetime.now(dt.timezone.utc)
    damga = simdi.strftime("%Y%m%dT%H%M%SZ")
    tarih = simdi.strftime("%Y%m%d")

    basliklar = {"host": host, "x-amz-content-sha256": govde_sha, "x-amz-date": damga}
    for k, v in (ek_baslik or {}).items():
        basliklar[k.lower()] = v
    if uzunluk:
        basliklar["content-length"] = str(uzunluk)
    imzali = sorted(basliklar)
    kanonik_basliklar = "".join(f"{k}:{basliklar[k].strip()}\n" for k in imzali)
    imzali_ad = ";".join(imzali)
    kanonik = "\n".join([yontem, yol, "", kanonik_basliklar, imzali_ad, govde_sha])
    kapsam = f"{tarih}/{REGION}/s3/aws4_request"
    imzalanacak = "\n".join(["AWS4-HMAC-SHA256", damga, kapsam,
                             hashlib.sha256(kanonik.encode()).hexdigest()])
    imza = hmac.new(_imza_anahtari(gizli, tarih, REGION, "s3"),
                    imzalanacak.encode(), hashlib.sha256).hexdigest()
    basliklar["authorization"] = (f"AWS4-HMAC-SHA256 Credential={kimlik}/{kapsam}, "
                                  f"SignedHeaders={imzali_ad}, Signature={imza}")
    req = urllib.request.Request(ENDPOINT + yol, data=govde, method=yontem)
    for k, v in basliklar.items():
        if k != "host":                      # host'u urllib kendisi basar
            req.add_unredirected_header(k, v)
    return req


def _var_mi(anahtar: str) -> dict | None:
    """HEAD — nesne varsa {"etag","uzunluk"}, yoksa None. 404 dışındaki hata FIRLATILIR
    (erişim arızasını "yok" diye okumak, her ay yeniden yükleme demekti)."""
    req = _istek("HEAD", anahtar, govde_sha=hashlib.sha256(b"").hexdigest())
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return {"etag": (r.headers.get("ETag") or "").strip('"'),
                    "uzunluk": int(r.headers.get("Content-Length") or 0)}
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise


def _yukle(anahtar: str, yol: pathlib.Path, sha: str, md5: str, n: int) -> str:
    """PUT (tek parça; 5GB sınırının çok altındayız — ölçüm: aylık ham ~360MB, gz sonrası daha az).
    Dönen: sunucunun ETag'i. Gövde dosya nesnesidir — tar belleğe alınmaz."""
    with yol.open("rb") as f:
        req = _istek("PUT", anahtar, govde_sha=sha, uzunluk=n, govde=f,
                     ek_baslik={"content-type": "application/gzip"})
        with urllib.request.urlopen(req, timeout=1800) as r:
            etag = (r.headers.get("ETag") or "").strip('"')
    if etag and etag != md5:
        raise SystemExit(f"!! DOĞRULAMA DÜŞTÜ: ETag={etag} ≠ yerel MD5={md5} — nesne bozuk "
                         f"yüklendi ya da sunucu parçalı yazdı; kova temizlenmeden TEKRAR DENEME")
    return etag


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--ay", default=None, help="YYYY-MM (varsayılan: önceki ay, UTC)")
    ap.add_argument("--kuru", action="store_true", help="tar'ı kur ve ÖLÇ, yükleme YAPMA")
    a = ap.parse_args(argv)

    ay = a.ay or _onceki_ay(dt.datetime.now(dt.timezone.utc).date())
    dosyalar = _dosyalar(ay)
    rapor: dict = {"ay": ay, "state": str(STATE), "n_dosya": len(dosyalar),
                   "dizinler": {d: len([1 for ad, _ in dosyalar if ad.startswith(d + "/")])
                                for d in DIZINLER}}
    if not dosyalar:
        # SESSİZ BAŞARI YOK: boş bir ay ya arşivcinin ay boyu durduğu bir olaydır ya da listenin
        # bayatlamasıdır. İkisi de iş kalemidir — birim BAŞARISIZ beyan eder.
        rapor["yuklendi"] = False
        rapor["neden"] = (f"{ay} için {'/'.join(DIZINLER)} altında hiç dosya yok — arşivci o ay "
                          f"koştu mu? (ölçü: uv run python -m meridian.barsarchive --ozet)")
        print(json.dumps(rapor, ensure_ascii=False, indent=1))
        return 1

    anahtar = f"{PREFIX}/{ay}/intraday-{ay}.tar.gz"
    rapor["anahtar"] = anahtar
    with tempfile.TemporaryDirectory() as td:
        tar = pathlib.Path(td) / f"intraday-{ay}.tar.gz"
        _tar_kur(ay, dosyalar, tar)
        sha, md5, n = _ozet(tar)
        rapor.update({"tar_bayt": n, "sha256": sha, "md5": md5})
        if a.kuru:
            rapor["yuklendi"] = False
            rapor["neden"] = "--kuru: tar kuruldu ve ölçüldü, yükleme İSTENMEDİ"
            print(json.dumps(rapor, ensure_ascii=False, indent=1))
            return 0
        mevcut = _var_mi(anahtar)
        if mevcut and mevcut.get("etag") == md5:
            # İDEMPOTENS: aynı ay ikinci kez tetiklenirse (Persistent=true telafisi) kova
            # dokunulmaz. "atlandı" BEYANLIdır — sessiz bir no-op, "yüklendi" gibi okunurdu.
            rapor.update({"yuklendi": False, "atlandi": True,
                          "neden": f"nesne zaten var ve özeti tutuyor (ETag={mevcut['etag']})"})
            print(json.dumps(rapor, ensure_ascii=False, indent=1))
            return 0
        if mevcut:
            rapor["uyari"] = (f"kovada AYNI ADLA farklı nesne var (ETag={mevcut.get('etag')}, "
                              f"{mevcut.get('uzunluk')} bayt) — üzerine yazılıyor: aynı ayın "
                              f"arşivi büyümüş olabilir (geç gelen bar dosyası)")
        rapor["etag"] = _yukle(anahtar, tar, sha, md5, n)
    rapor["yuklendi"] = True
    rapor["yerel_silme"] = ("YOK — bu birim state/ altına yazamaz (birim dosyasında "
                            "ReadWritePaths verilmedi; ProtectSystem=strict)")
    print(json.dumps(rapor, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
