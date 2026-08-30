"""EXE-2026-009 P-1 — İKİ SATIRIN `pencere` DAMGASI DÜZELTMESİ (tek seferlik, cerrahi).

YETKİ: operatör hükmü 2026-08-29 ("damgayı gönderim anına bağla, iki satırı da düzelt").
Bu düzeltme, kartın kill#3'ünü ("geriye dönük pencere yeniden-etiketleme yapılırsa geçersiz")
OPERATÖR İSTİSNASIYLA aşar. Kill kriteri KALDIRILMADI; bu satırlar için bir kez, gerekçesi
defterde görünür biçimde aşıldı. Sessiz düzeltme YOKTUR: düzeltilen her satır `pencere_duzeltme`
alanıyla kendi gerekçesini taşır.

ÖLÇÜLMÜŞ ÖN-KOŞUL (teşhis: research/olcumler/edg042_teshis_pencere_damgasi_2026-08-29/):
  · hedef satırlar `motor="ayna"` · `karar="submitted"` · `pencere="1345"`
  · `ts="2026-08-21T20:32:22+00:00"` — EOD-GTC yolu, yani 13:30 rejimi
  · canlı `barclock.py` 1345'e 2026-08-23T14:53:43Z'de döndü — gönderimden İKİ GÜN SONRA
  · satırlar 2026-08-24'te yazıldı ve damgayı ORADA aldı (arızanın kendisi)
Doğru damga bu yüzden "1330"dur ve bu bir tahmin değil iki bağımsız işaretin (ts + canlı mtime)
aynı yeri göstermesidir.

KAPSAM SINIRI — DOKUNULMAYAN: aynı planların `motor="ic"` / `karar="fill"` satırları
(ts=2026-08-24T20:38:22Z) BU DÜZELTMENİN DIŞINDADIR. İç motorun dolumu gerçekten 08-24'te,
1345 yürürlükteyken oldu; ayrıca hiçbir ölçüm bandı o satırları okumaz (K1 filtresi
`motor=="ayna"`). Onları da çevirmek kapsam kaymasi ve ikinci bir uydurma olurdu.

KOŞUM (canlıda, BAKIM PENCERESİNDE — worker koşarken state'e yazılmaz, CLAUDE.md madde 5):
    ./.venv/bin/python ops/pencere_damgasi_duzeltme_2026_08_29.py          # KURU KOŞU (varsayılan)
    ./.venv/bin/python ops/pencere_damgasi_duzeltme_2026_08_29.py --yaz    # yazar
"""
import json
import sys

DEFTER = "entry_execution.jsonl"

#: Hedef satırlar ve ÖLÇÜLMÜŞ gönderim damgaları. Bir satırın `ts`i buradakiyle uyuşmuyorsa
#: betik hiçbir şey yazmaz — "hedefi bulduğunu sanıp yanlış satırı çevirmek" en kötü sonuçtur.
HEDEFLER = {"P-2026-08-21-DE": "2026-08-21T20:32:22+00:00",
            "P-2026-08-21-PANW": "2026-08-21T20:32:22+00:00"}
BEKLENEN_ESKI = "1345"
DOGRU = "1330"
GEREKCE = ("1345→1330, operatör hükmü 2026-08-29 (EXE-2026-009 P-1): damga DEFTERE YAZIM anında "
           "(2026-08-24) basılmıştı; gönderim ts=2026-08-21T20:32:22Z ile 13:30 rejimindeydi "
           "(canlı barclock 1345'e 2026-08-23T14:53:43Z'de döndü). kill#3 operatör istisnasıyla "
           "aşıldı; teşhis: research/olcumler/edg042_teshis_pencere_damgasi_2026-08-29/")


class OnKosulHatasi(Exception):
    """Ön-koşul tutmadı — HİÇBİR satır değiştirilmez (yarım düzeltme yoktur)."""


def _hedef_mi(r):
    return (r.get("plan_id") in HEDEFLER and r.get("motor") == "ayna"
            and r.get("karar") == "submitted")


def duzelt(rows):
    """Saf dönüşüm: (yeni_satirlar, rapor). Girdi listesi DEĞİŞTİRİLMEZ.

    Ön-koşul ihlalinde `OnKosulHatasi` yükselir ve hiçbir satır kopyalanıp yazılmaz."""
    bulunan, cevrilecek, zaten = {}, set(), set()
    for i, r in enumerate(rows):
        if not _hedef_mi(r):
            continue
        pid = r["plan_id"]
        bulunan.setdefault(pid, []).append(i)
        if r.get("pencere") == DOGRU and r.get("pencere_duzeltme"):
            zaten.add(i)
            continue
        if r.get("ts") != HEDEFLER[pid]:
            raise OnKosulHatasi(
                f"{pid}: ts={r.get('ts')!r} beklenen {HEDEFLER[pid]!r} değil — satır KİMLİĞİ "
                "doğrulanamadı, hiçbir şey yazılmadı")
        if r.get("pencere") != BEKLENEN_ESKI:
            raise OnKosulHatasi(
                f"{pid}: pencere={r.get('pencere')!r} beklenen {BEKLENEN_ESKI!r} değil — defter "
                "beklenen durumda değil (başka bir el değdi?), hiçbir şey yazılmadı")
        cevrilecek.add(i)

    eksik = sorted(set(HEDEFLER) - set(bulunan))
    if eksik:
        raise OnKosulHatasi(
            f"hedef satır(lar) defterde bulunamadı: {eksik} — yanlış defter ya da yanlış makine "
            "olabilir; sessizce 'düzeltecek bir şey yok' demek YASAK")

    yeni = []
    for i, r in enumerate(rows):
        if i in cevrilecek:
            yeni.append({**r, "pencere": DOGRU, "pencere_duzeltme": GEREKCE})
        else:
            yeni.append(dict(r))
    return yeni, {"duzeltilen": len(cevrilecek), "zaten_duzeltilmis": len(zaten),
                  "toplam_satir": len(rows)}


def main(argv):
    from meridian import store
    yaz = "--yaz" in argv
    with store.file_lock(DEFTER):
        rows = store.read_jsonl(DEFTER)
        yeni, rapor = duzelt(rows)
        if yaz and rapor["duzeltilen"]:
            store.write_jsonl(DEFTER, yeni)
    rapor["mod"] = "YAZDI" if (yaz and rapor["duzeltilen"]) else "KURU KOŞU"
    rapor["degisen_satirlar"] = [{k: r.get(k) for k in ("plan_id", "ts", "pencere")}
                                 for r in yeni if r.get("pencere_duzeltme")]
    print(json.dumps(rapor, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
