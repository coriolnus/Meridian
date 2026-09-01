# EDG-2026-067 SÜPÜRME dilimleyicisi — ana koşum (ingest067.py) bittikten sonra A1'de koşar.
# NEDEN AYRI BETİK: manifest_uret.py kartın DONUK korpus artefaktıdır (taban kıyası kill maddesi
# "AYNI korpus") — ona dokunulmaz. Bu betik korpusu DEĞİŞTİRMEZ: ilerleme defterinde OLMAYAN
# belgeleri alır; devleri (ESIK_DEV+) ROADMAP %237 emsalindeki kimlik şemasıyla (`yol%23dilim-N`)
# bölüm sınırlarından dilimleyip aynı blob/commit üstverisiyle yollar, küçük düşenleri bütün
# yeniden dener. İçerik bayt-kayıpsızdır (dilimlerin birleşimi == belge; çivi v366).
# Taban-kıyası notu: dilim belge-kimlikleri hüküm turunda görünür olsun diye ilerleme defterine
# aynen yazılır — kıyas iki kolda aynı SORULARLA yapılır, belge-kimliği değil içerik eşleşir;
# yine de hüküm Rol-1'de bu sapmayı tartar (devir brifi).
# Kullanım (A1): /opt/hindsight/venv/bin/python dilim_sup.py  [--kuru]
# Idempotent: ilerleme.jsonl'e dilim kimliğiyle yazar; yarım kalırsa aynı komut devam eder.
import json
import os
import sys
import time
import urllib.error
import urllib.request

KOK = "/opt/hindsight/ingest067"
BASE = "http://127.0.0.1:8888/v1/default"
BANK = "meridian-arsiv"
ESIK_DEV = 50_000     # bayt — üstü "dev": tek chunk'ta Nvidia free boyut-sınıfı reddi (ölçüm 2026-09-01, 5/5)
ESIK_DILIM = 40_000   # bayt — dilim hedef tavanı (~10K token; başarıyla geçen en büyük sınıfın altı)


# ---- saf çekirdek (çivi: tests/test_edg067_dilim_v366.py) --------------------------------------

def _bloklar(metin: str) -> list[str]:
    """Metni önsöz + `## ` bölümlerine ayırır; ``` fence içindeki `## ` başlık SAYILMAZ.
    Blokların birleşimi girdiye bayt bayt eşittir (kayıpsızlık çekirdeği burada başlar)."""
    parcalar: list[str] = []
    mevcut: list[str] = []
    fence = False
    for satir in metin.splitlines(keepends=True):
        if satir.lstrip().startswith("```"):
            fence = not fence
        if satir.startswith("## ") and not fence and mevcut:
            parcalar.append("".join(mevcut))
            mevcut = []
        mevcut.append(satir)
    if mevcut:
        parcalar.append("".join(mevcut))
    return parcalar


def _zorla_bol(blok: str, esik: int) -> list[str]:
    """Tek başına eşiği aşan bloğu boş-satır (paragraf) sınırlarından böler; eşiği tek başına
    aşan paragraf kalırsa bayt düzeyinde kesilir (esnek tavan garantisi)."""
    paragraflar = blok.split("\n\n")
    # split birleştirilirken ayraçlar geri konur — kayıpsızlık için ayraçlı yeniden kurulum
    parcalar: list[str] = []
    for i, p in enumerate(paragraflar):
        parcalar.append(p + ("\n\n" if i < len(paragraflar) - 1 else ""))
    cikti: list[str] = []
    mevcut = ""
    for p in parcalar:
        while len(p.encode()) > esik:  # tek paragraf bile eşik üstü — kaba bayt kesimi
            if mevcut:
                cikti.append(mevcut)
                mevcut = ""
            kes = esik
            while kes > 0 and (p[:kes].encode() != p.encode()[:len(p[:kes].encode())]
                               or len(p[:kes].encode()) > esik):
                kes -= 1
            cikti.append(p[:kes])
            p = p[kes:]
        if mevcut and len((mevcut + p).encode()) > esik:
            cikti.append(mevcut)
            mevcut = p
        else:
            mevcut += p
    if mevcut:
        cikti.append(mevcut)
    return cikti


def _ilk_baslik(parca: str) -> str:
    for satir in parca.splitlines():
        if satir.startswith("## "):
            return satir[3:].strip()
    return ""


def dilimle(metin: str, esik: int = ESIK_DILIM) -> list[dict]:
    """Bölüm bloklarını eşiği aşmadan açgözlü paketler; dev bloğu paragraftan zorla böler.
    Dönen dilimlerin `metin` birleşimi girdiye EŞİTTİR; her dilim ilk bölüm başlığını taşır."""
    dilimler: list[str] = []
    mevcut = ""
    for blok in _bloklar(metin):
        if len(blok.encode()) > esik:
            if mevcut:
                dilimler.append(mevcut)
                mevcut = ""
            dilimler.extend(_zorla_bol(blok, esik))
            continue
        if mevcut and len((mevcut + blok).encode()) > esik:
            dilimler.append(mevcut)
            mevcut = blok
        else:
            mevcut += blok
    if mevcut:
        dilimler.append(mevcut)
    return [{"metin": d, "bolum": _ilk_baslik(d)} for d in dilimler]


def dilim_kimlikleri(yol: str, n: int) -> list[str]:
    """ROADMAP %237 emsali: URL-kodlu `#` + 1-tabanlı sıra."""
    return [f"{yol}%23dilim-{i}" for i in range(1, n + 1)]


# ---- A1 süpürme akışı (ingest067.py deseninin aynası) ------------------------------------------

def _api(anahtar: str, method: str, path: str, body=None, timeout=3600):
    req = urllib.request.Request(
        BASE + path,
        data=json.dumps(body).encode() if body is not None else None,
        method=method,
        headers={"Authorization": f"Bearer {anahtar}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, json.loads(r.read() or b"{}")


def main(argv: list[str] | None = None) -> int:
    kuru = "--kuru" in (argv or sys.argv[1:])
    anahtar = os.environ.get("HS_KEY") or open("/opt/hindsight/.env").read().split(
        "HINDSIGHT_API_TENANT_API_KEY=")[1].splitlines()[0]
    log = open(f"{KOK}/log.txt", "a", buffering=1)

    def kayit(*a):
        log.write(time.strftime("%H:%M:%S SUP ") + " ".join(str(x) for x in a) + "\n")

    manifest = json.load(open(f"{KOK}/manifest.json"))
    bitenler = set()
    for satir in open(f"{KOK}/ilerleme.jsonl"):
        try:
            bitenler.add(json.loads(satir)["yol"])
        except Exception as e:  # sessiz-yutma: bozuk ilerleme satiri yalnizca yeniden-isleme demektir
            kayit("ilerleme satiri bozuk, yok sayildi:", e)
    ilerleme = open(f"{KOK}/ilerleme.jsonl", "a", buffering=1)

    isler: list[tuple[str, str, dict]] = []  # (kimlik, icerik, ustveri)
    for d in manifest["dosyalar"]:
        yol = d["yol"]
        if yol in bitenler:
            continue
        icerik = open(f"{KOK}/korpus/{yol}", encoding="utf-8").read()
        ustveri = {"blob": d["blob"], "commit": manifest["head_commit"]}
        if d["bayt"] <= ESIK_DEV:
            isler.append((yol, icerik, ustveri))
            continue
        dilimler = dilimle(icerik)
        birlesim = "".join(x["metin"] for x in dilimler)
        assert birlesim == icerik, f"KAYIPLI dilimleme: {yol}"  # v366 çekirdeği; canlıda da tutulur
        for i, (kimlik, dl) in enumerate(zip(dilim_kimlikleri(yol, len(dilimler)), dilimler), 1):
            if kimlik in bitenler:
                continue
            isler.append((kimlik, dl["metin"],
                          {**ustveri, "dilim": f"{i}/{len(dilimler)}", "bolum": dl["bolum"]}))

    kayit(f"süpürme başlıyor: {len(isler)} iş (kuru={kuru})")
    if kuru:
        for kimlik, icerik, _ in isler:
            print(f"{kimlik}  {len(icerik.encode())}B")
        return 0

    basarisiz = []
    for kimlik, icerik, ustveri in isler:
        govde = {"items": [{"content": icerik, "document_id": kimlik,
                            "context": "arsiv-ingest EDG-2026-067 (süpürme)",
                            "metadata": ustveri}],
                 "async": False}
        ok = False
        for deneme in (1, 2, 3):
            t0 = time.time()
            try:
                st, r = _api(anahtar, "POST", f"/banks/{BANK}/memories", govde)
                u = r.get("usage") or {}
                gi, ci = u.get("input_tokens", 0) or 0, u.get("output_tokens", 0) or 0
                kayit(f"OK {kimlik} {time.time()-t0:.0f}s deneme={deneme} tok={gi}/{ci}")
                ilerleme.write(json.dumps({"yol": kimlik, "blob": ustveri["blob"],
                                           "sure_s": round(time.time()-t0, 1),
                                           "girdi_tok": gi, "cikti_tok": ci}) + "\n")
                ok = True
                break
            except urllib.error.HTTPError as e:
                kayit(f"HATA {kimlik} deneme={deneme} HTTP {e.code} {e.read()[:150]!r}")
            except Exception as e:  # sessiz-yutma: ag/timeout sinifi — kaydedilip backoff'la yeniden denenir
                kayit(f"HATA {kimlik} deneme={deneme} {type(e).__name__}: {e}")
            time.sleep(30 * deneme)
        if not ok:
            basarisiz.append(kimlik)
    kayit("SÜPÜRME BİTTİ · başarısız:", len(basarisiz), basarisiz[:5])
    return 1 if basarisiz else 0


if __name__ == "__main__":
    raise SystemExit(main())
