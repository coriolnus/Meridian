#!/usr/bin/env python3
"""EDG-2026-065 arşiv ingest'i — kart: research/cards/EDG-2026-065-hindsight-faz1-kurulum-recall.yaml

Dört kaynak sınıfını Hindsight `meridian-arsiv` bank'ine git-sha'lı ve MÜKERRERSİZ taşır:
  gunluk    MERIDIAN_ENGINEERING_LOG.md (tek belge)
  roadmap7  ROADMAP.md §7 KARAR GÜNLÜĞÜ bloğu (başlık regex'iyle koşum anında kesilir)
  kartlar   research/cards/*.yaml (kart başına belge)
  vaka      docs/ vaka belgeleri (beyanlı önek süzgeci; RUNBOOK üretilmiş olduğu için ASLA girmez)

Sözleşme KOMUT SATIRIdır:
  ingest.py --sinif gunluk|roadmap7|kartlar|vaka [--kuru] [--limit N] [--zorla]
            [--host H] [--anahtar YOL]   (varsayılanlar filo ile aynı; env MERIDIAN_A1_*)

Mükerrersizlik İKİ katman: (1) sunucu tarafı document_id upsert (kart kanıtı: smoke-001 ikinci
retain 0 token); (2) istemci tarafı: manifest'te AYNI doc_id+blob_sha YEŞİL ise çağrı hiç
yapılmaz (--zorla ile ezilir). Manifest (Yasa 6 okuyucusu: kıyas raporu + tur özeti):
  research/olcumler/edg065_hindsight_faz1/ingest_manifest.jsonl — satır başına
  {ts, sinif, doc_id, blob_sha, bayt, durum, usage|hata}
"""
import argparse, hashlib, json, os, re, subprocess, sys, time
from pathlib import Path

KOK = Path(__file__).resolve().parents[3]
MANIFEST = Path(__file__).resolve().parent / "ingest_manifest.jsonl"
BANK_URL = "http://localhost:8888/v1/default/banks/meridian-arsiv/memories"
VAKA_ONEK = ("KARAR", "HUKUM", "TESHIS", "DENETIM", "DEVIR", "VAKA", "ACIK-KALEMLER",
             "DEGERLENDIRME", "INCELEME", "TASARIM", "UZLASTIRMA", "GECE-RAPORU")
TARIH = re.compile(r"(20\d{2}-\d{2}-\d{2})")


def varsayilan_host():
    return os.environ.get("MERIDIAN_A1_HOST", "ubuntu@130.61.126.87")


def varsayilan_anahtar():
    return os.environ.get("MERIDIAN_A1_KEY", str(Path.home() / ".ssh" / "oci-a1.key"))


def blob_sha(veri: bytes) -> str:
    # git hash-object eşdeğeri: içerik-adresli kimlik (EDG-059 dersi: çalışma-ağacı referansı
    # kartı sessizce öldürür — sha manifest'te durur, ağaç değişse de kanıt değişmez)
    h = hashlib.sha1()
    h.update(b"blob %d\0" % len(veri))
    h.update(veri)
    return h.hexdigest()


def belgeler(sinif: str):
    """→ [(doc_id, metin_bytes, tarih|None)] — sınıf başına kaynak listesi."""
    if sinif == "gunluk":
        p = KOK / "MERIDIAN_ENGINEERING_LOG.md"
        return [("MERIDIAN_ENGINEERING_LOG.md", p.read_bytes(), None)]
    if sinif == "roadmap7":
        metin = (KOK / "ROADMAP.md").read_text(encoding="utf-8")
        m = re.search(r"^## §7 .*?(?=^## §8 )", metin, re.M | re.S)
        if not m:
            raise SystemExit("KIRMIZI: ROADMAP §7 bloğu bulunamadı (başlık deseni değişmiş olabilir)")
        return [("ROADMAP.md#s7-karar-gunlugu", m.group(0).encode("utf-8"), None)]
    if sinif == "kartlar":
        cikti = []
        for p in sorted((KOK / "research" / "cards").glob("*.yaml")):
            cikti.append((str(p.relative_to(KOK)), p.read_bytes(), None))
        return cikti
    if sinif == "vaka":
        cikti = []
        for p in sorted((KOK / "docs").glob("*.md")):
            if p.name == "RUNBOOK.md" or not p.name.startswith(VAKA_ONEK):
                continue
            t = TARIH.search(p.name)
            cikti.append((str(p.relative_to(KOK)), p.read_bytes(), t.group(1) if t else None))
        return cikti
    raise SystemExit(f"KIRMIZI: bilinmeyen sınıf {sinif!r}")


def yesil_kayitlar():
    """manifest → {(doc_id, blob_sha)} YEŞİL veya KUYRUKTA olanlar (mükerrer kalkanı —
    kuyruğa girmiş belge de yeniden gönderilmez; akıbeti stats/dogrula turunda ölçülür)."""
    kume = set()
    if MANIFEST.exists():
        for i, satir in enumerate(MANIFEST.read_text(encoding="utf-8").splitlines(), 1):
            try:
                k = json.loads(satir)
                if k.get("durum") in ("YESIL", "KUYRUKTA"):
                    kume.add((k["doc_id"], k["blob_sha"]))
            except (KeyError, json.JSONDecodeError):
                # sessiz-yutma: bozuk manifest satırı kalkanı zayıflatır ama koşumu durdurmaz;
                # satır numarası basılır, upsert ikinci katman olarak arkada durur
                print(f"  ! manifest satır {i} bozuk — atlandı (upsert kalkanı devrede)")
    return kume


def gonder(host: str, anahtar: str, doc_id: str, veri: bytes, tarih, kuyruk: bool):
    item = {"content": veri.decode("utf-8", errors="replace"), "document_id": doc_id,
            "metadata": {"blob_sha": blob_sha(veri), "kaynak": "meridian-repo"}}
    if tarih:
        item["timestamp"] = f"{tarih}T12:00:00Z"
    govde = {"items": [item]}
    if kuyruk:
        govde["async"] = True  # sunucu kuyruğu: teslim saniyelik, işleme worker'da —
        # 45-chunk'lık günlük belgesinin senkron çağrıyı 660sn'de öldürdüğü vaka (2026-08-31)
    yuk = json.dumps(govde, ensure_ascii=False).encode("utf-8")
    kom = ["ssh", "-i", anahtar, host,
           f"curl -s -m 600 -X POST {BANK_URL} -H 'Content-Type: application/json' -d @-"]
    try:
        p = subprocess.run(kom, input=yuk, capture_output=True, timeout=660)
    except subprocess.TimeoutExpired:
        return {"detail": "istemci-zaman-asimi-660s (sunucu işlemeye devam ediyor olabilir — "
                          "yeniden göndermeden önce stats/documents ölç)"}
    try:
        return json.loads(p.stdout.decode("utf-8", errors="replace"))
    except json.JSONDecodeError:
        return {"detail": f"cevap-json-degil rc={p.returncode}: "
                          f"{p.stdout[:200]!r} {p.stderr[:200]!r}"}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--sinif", required=True,
                    choices=["gunluk", "roadmap7", "kartlar", "vaka"])
    ap.add_argument("--kuru", action="store_true", help="listele+ölç, GÖNDERME")
    ap.add_argument("--limit", type=int, default=0, help="bu koşumda en çok N belge")
    ap.add_argument("--zorla", action="store_true", help="manifest YEŞİL kalkanını ez")
    ap.add_argument("--kuyruk", action="store_true",
                    help="async gönder: teslim saniyelik, işleme sunucu worker'ında")
    ap.add_argument("--host", default=varsayilan_host())
    ap.add_argument("--anahtar", default=varsayilan_anahtar())
    a = ap.parse_args(argv)

    docs = belgeler(a.sinif)
    if a.limit:
        docs = docs[: a.limit]
    kalkan = set() if a.zorla else yesil_kayitlar()
    toplam_b = sum(len(v) for _, v, _ in docs)
    print(f"SINIF={a.sinif} belge={len(docs)} bayt={toplam_b} tahmini-chunk≈{toplam_b // 3000}")
    if a.kuru:
        for d, v, t in docs:
            atla = " [manifest-YEŞİL, atlanacak]" if (d, blob_sha(v)) in kalkan else ""
            print(f"  {d} {len(v)}b tarih={t}{atla}")
        return 0

    yesil = kirmizi = atlanan = 0
    tok_toplam = 0
    with MANIFEST.open("a", encoding="utf-8") as mf:
        for d, v, t in docs:
            sha = blob_sha(v)
            if (d, sha) in kalkan:
                atlanan += 1
                print(f"  atla (YEŞİL): {d}")
                continue
            cevap = gonder(a.host, a.anahtar, d, v, t, a.kuyruk)
            if not a.kuyruk and cevap.get("detail") and \
                    "overloaded" in str(cevap.get("detail")).lower():
                print(f"  aşırı-yük, 30sn sonra BİR tekrar: {d}")
                time.sleep(30)
                cevap = gonder(a.host, a.anahtar, d, v, t, a.kuyruk)
            kayit = {"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                     "sinif": a.sinif, "doc_id": d, "blob_sha": sha, "bayt": len(v)}
            if cevap.get("success") and cevap.get("async"):
                op = cevap.get("operation_id") or cevap.get("operation_ids")
                kayit.update(durum="KUYRUKTA", op=op)
                yesil += 1
                print(f"  KUYRUKTA: {d} op={op}")
            elif cevap.get("success"):
                u = cevap.get("usage", {})
                kayit.update(durum="YESIL", usage=u)
                tok_toplam += u.get("total_tokens", 0)
                yesil += 1
                print(f"  YEŞİL: {d} token={u.get('total_tokens')}")
            else:
                kayit.update(durum="KIRMIZI", hata=str(cevap.get("detail", cevap))[:300])
                kirmizi += 1
                print(f"  KIRMIZI: {d} — {kayit['hata'][:120]}")
            mf.write(json.dumps(kayit, ensure_ascii=False) + "\n")
            mf.flush()
    print(f"OZET sinif={a.sinif}: YEŞİL={yesil} KIRMIZI={kirmizi} atlanan={atlanan} "
          f"toplam_token={tok_toplam}")
    return 0 if kirmizi == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
