"""EDG-2026-056 — BİLİNEN SPLİT LİSTESİNİ DONDUR (ölçümden ÖNCE koşar, bir kez).

Kart kill: "bilinen-split listesi ölçüm sırasında genişletilirse geçersiz (liste önce donar,
sha rapora)". Bu betik listeyi üretir, sha256'sını yazar ve BİR DAHA KOŞULMAZ.
SALT-OKUMA: state/ altına YAZMAZ, meridian motorunu import ETMEZ.
"""
from __future__ import annotations
import hashlib, json, pathlib

KOK = pathlib.Path(__file__).resolve().parents[3]
CIKTI = pathlib.Path(__file__).resolve().parent / "bilinen_split_donuk.json"
BI = KOK / "state" / "bars_integrity.json"
BARS = KOK / "state" / "bars"
TESHIS = KOK / "docs" / "TESHIS-MNST-SPLIT-2026-08-12.md"


def _sha(p: pathlib.Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _arsiv_tarihleri(tic: str) -> set[str]:
    f = BARS / f"{tic.lower()}.csv"
    if not f.exists():
        return set()
    out = set()
    for i, satir in enumerate(f.read_text().splitlines()):
        if i == 0 or not satir:
            continue
        out.add(satir.split(",", 1)[0][:10])
    return out


def main() -> None:
    bi = json.loads(BI.read_text())
    birincil = []
    for tic, v in sorted(bi.get("semboller", {}).items()):
        for b in v.get("kirilma_listesi", []):
            if b.get("sinif") != "olcek_dikisi" or b.get("oran") in (None, 0):
                continue
            oran = float(b["oran"])                      # bars_integrity: c[t]/c[t-1]
            birincil.append({
                "ticker": tic,
                "tarih": str(b["tarih"])[:10],
                "kayitli_oran_c_t_bolu_c_t1": round(oran, 6),
                "r_kart_c_t1_bolu_c_t": round(1.0 / oran, 6),
                "sinif": b["sinif"], "kural": b["kural"],
                "arsivde_var": str(b["tarih"])[:10] in _arsiv_tarihleri(tic),
            })
    ikincil = [
        {"ticker": "MNST", "tarih": "2026-08-11", "oran_metni": "1->2", "r_kart_beklenen": 2.0,
         "arsivde_var": "2026-08-11" in _arsiv_tarihleri("MNST")},
        {"ticker": "MNST", "tarih": "2023-03-28", "oran_metni": "1->2", "r_kart_beklenen": 2.0,
         "arsivde_var": "2023-03-28" in _arsiv_tarihleri("MNST")},
        {"ticker": "MNST", "tarih": "2016-11-10", "oran_metni": "1->3", "r_kart_beklenen": 3.0,
         "arsivde_var": "2016-11-10" in _arsiv_tarihleri("MNST")},
    ]
    govde = {
        "kart": "EDG-2026-056",
        "donduruldu": "2026-08-24",
        "beyan": "ÖLÇÜMDEN ÖNCE donduruldu. Ölçüm sırasında GENİŞLETİLMEDİ (kart kill kriteri).",
        "birincil": {
            "kaynak": "state/bars_integrity.json -> semboller[*].kirilma_listesi, sinif=='olcek_dikisi' (K1)",
            "kaynak_sha256": _sha(BI),
            "kaynak_uretildi": bi.get("uretildi"),
            "neden_bu": ("Kart 'bilinen split' kaynağı olarak KENDİ karantina/temizlik kayıtlarımızı "
                         "gösteriyor. state/quarantine/ ÖLÇÜLDÜ: yalnız sp500_constituents FIXTURE'ı var, "
                         "SIFIR bölünme kaydı. Repodaki tek makine-okunur ölçek-dikişi defteri "
                         "bars_integrity.json'dur (K1 olcek_dikisi)."),
            "kapsam_uyarisi": ("K1 eşikleri r>=1.9 veya r<=0.55 (data.py BREAK_UP/BREAK_DN). Bu yüzden "
                               "3:2 gibi küçük oranlı bölünmeler bu YER GERÇEĞİNDE hiç YOKTUR — "
                               "yakalama oranı büyük-oranlı dikişlere yanlıdır (beyanlı)."),
            "sinif_uyarisi": ("K1 'ölçek dikişi'dir: gerçek bölünme, spinoff yeniden-tabanlaması ve "
                              "sağlayıcı taban değişimi AYNI kovada. Kart beyanli_sinirlar(1) bunu "
                              "kapsıyor: liste 'bizim kayıtlarımız kadardır'."),
            "olaylar": birincil,
        },
        "ikincil_hukum_disi": {
            "kaynak": "docs/TESHIS-MNST-SPLIT-2026-08-12.md (Massive /stocks/v1/splits takvimi, dış kanıt)",
            "kaynak_sha256": _sha(TESHIS),
            "neden_hukum_disi": ("Dış takvim bizim 'karantina/temizlik kaydımız' DEĞİL. Karar kuralına "
                                 "GİRMEZ; ayrı raporlanır."),
            "olaylar": ikincil,
        },
    }
    metin = json.dumps(govde, ensure_ascii=False, indent=2, sort_keys=False) + "\n"
    CIKTI.write_text(metin)
    print("birincil olay:", len(birincil), "| arsivde_var:", sum(1 for e in birincil if e["arsivde_var"]))
    print("ikincil olay:", len(ikincil), "| arsivde_var:", sum(1 for e in ikincil if e["arsivde_var"]))
    print("LISTE_SHA256:", hashlib.sha256(metin.encode()).hexdigest())


if __name__ == "__main__":
    main()
