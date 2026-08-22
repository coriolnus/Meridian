"""EXE-2026-006 · Ö-51b — Ö1'in KİMLİKLİ hesabı (2026-08-22).

KART: research/cards/EXE-2026-006-limit-bacagi-hukum-sinamasi.yaml (OKU-DOKUNMA).
Hükmü Rol-1 işler; bu betik yalnız SAYIYI üretir.

NEDEN AYRI BETİK: `olcum.py` bu dizine BAYT-ÖZDEŞ kopyalandı ki koşumun 2026-08-17 ile aynı
şasi olduğu KANITLANABİLİR olsun. Ö1 hesabını oraya eklemek o kanıtı bozardı. Ölçüm ile analiz
ayrı: betik hiçbir backtest KOŞMAZ, yalnız kaydedilmiş çıktıları okur (yeniden koşulabilir).

Ö1 2026-08-17'de ÖLÇÜLEMEDİ — kart İKİ kusur saydı, ikisi de burada kapanır:

  KUSUR 1 (BİRİM UYUŞMAZLIĞI): payda `entry_missed_limit` bir RED OLAYI sayacıydı (aynı plan
    günlerce reddedilebilir), pay DİSTİNKT İŞLEM. Ham bölme %132/%141 verdi — bir oran %100'ü
    AŞAMAZ. → ÇÖZÜM: payda `entry_reject_ids`ten DİSTİNKT (ticker, tarih) kümesi.

  KUSUR 2 (PAY SAF DEĞİL): pay "B kolunda olup A kolunda olmayan" işlemlerdi; bunların bir kısmı
    limit kapısının KURTARDIĞI işlem değil, bir slot boşaldığı için içeri giren YERİNDEN-ETME
    işlemidir. → ÇÖZÜM: pay, red kümesiyle KESİŞİME indirgenir. Kesişim dışı kalanlar
    `yerinden_etme` kovasına yazılır ve Ö1'e GİRMEZ (ama görünür kalır — kaybolmaz).

Bu iki düzeltmeyle Ö1 yapısal olarak ≤ %100'dür: pay, paydanın ALT KÜMESİDİR.
Kartın karar kuralı (ölçümden ÖNCE yazılı, DEĞİŞTİRİLMEDİ): **Ö1 > %20 ⇒ K1 şerhi açılır.**
"""
import json
import pathlib
import sys

BURASI = pathlib.Path(__file__).resolve().parent
DONMUS = BURASI.parent / "exe006_limit_bacagi_2026-08-17"   # 2026-08-17 kanıtı — SALT-OKUNUR
TAVANLAR = [0.005, 0.01, 0.02, 0.03]
# DUMAN MODU: analizin kendisi, PAHALI veri gelmeden ucuz veriyle sınanabilsin diye. Betiği
# 100 dakikalık koşumun SONUNDA ilk kez çalıştırmak, hatayı en pahalı anda bulmak demektir.
SMOKE = "--smoke" in sys.argv
EK = "_smoke" if SMOKE else ""


def _anahtar(t: dict) -> tuple:
    """İşlem kimliği. Alan adı DEFTERDEN okundu (`ts_open`), tahmin edilmedi."""
    return (t.get("ticker"), t.get("ts_open"))


def _defter(kok: pathlib.Path, cap: float, kural: str) -> list | None:
    y = kok / f"defter_cap{cap}_{kural}{EK}.json"
    return json.loads(y.read_text(encoding="utf-8")) if y.exists() else None


def bayt_ozdeslik(cap: float) -> dict:
    """A kolu 2026-08-17'den beri DEĞİŞTİ Mİ. `backtest.py` bu gece değişti; bu kapı onu ölçer.

    Özdeş değilse Ö1'den ÖNCE o işlenir — çünkü o zaman iki koşum aynı şeyi ölçmüyordur."""
    yeni, eski = _defter(BURASI, cap, "yalniz_acilis"), _defter(DONMUS, cap, "yalniz_acilis")
    if yeni is None or eski is None:
        return {"ozdes": None, "neden": "defterlerden biri YOK — özdeşlik ÖLÇÜLEMEDİ"}
    if yeni == eski:
        return {"ozdes": True, "n": len(yeni)}
    yk, ek = {_anahtar(t) for t in yeni}, {_anahtar(t) for t in eski}
    return {"ozdes": False, "n_yeni": len(yeni), "n_eski": len(eski),
            "yalniz_yeni": sorted(yk - ek)[:10], "yalniz_eski": sorted(ek - yk)[:10],
            "not": "ANAHTAR kümeleri eşitse fark ALAN düzeyindedir (yeni alan eklenmiş olabilir)"}


def o1(cap: float) -> dict:
    a, b = _defter(BURASI, cap, "yalniz_acilis"), _defter(BURASI, cap, "dinlenen_limit")
    grid = json.loads((BURASI / f"sonuc_grid{EK}.json").read_text(encoding="utf-8"))
    hucre = next((h for h in grid["hucreler"]
                  if h["limit_pct_cap"] == cap and h["dolum_kurali"] == "yalniz_acilis"), None)
    if a is None or b is None or hucre is None:
        return {"O1_yuzde": None, "olculemedi_neden": "defter ya da hücre çıktısı YOK"}

    ham = (hucre.get("red_kimlik") or {}).get("entry_missed_limit") or []
    red = {tuple(x) for x in ham}
    if not red:
        return {"O1_yuzde": None,
                "olculemedi_neden": "A kolunda entry_missed_limit reddi YOK — payda boş, oran TANIMSIZ",
                "red_olay_sayisi": hucre.get("entry_missed_limit")}

    ak = {_anahtar(t) for t in a}
    yalniz_b = [t for t in b if _anahtar(t) not in ak]
    kurtarilan = [t for t in yalniz_b if _anahtar(t) in red]       # SAF pay
    yerinden = [t for t in yalniz_b if _anahtar(t) not in red]     # Ö1'e GİRMEZ, görünür kalır
    oran = round(100.0 * len(kurtarilan) / len(red), 1)
    assert oran <= 100.0, f"pay paydanın alt kümesi olmalıydı: {len(kurtarilan)}/{len(red)}"

    rl = [float(t["r_multiple"]) for t in kurtarilan if t.get("r_multiple") is not None]
    return {
        "O1_yuzde": oran,
        "pay_KURTARILAN_distinkt_islem": len(kurtarilan),
        "payda_DISTINKT_reddedilen_plan": len(red),
        "red_OLAY_sayisi_gecersiz_payda": hucre.get("entry_missed_limit"),
        "olay_plan_carpani": (round(hucre["entry_missed_limit"] / len(red), 2)
                              if hucre.get("entry_missed_limit") else None),
        "yerinden_etme_PAYA_GIRMEDI": len(yerinden),
        "kurtarilanlarin_ort_r": (round(sum(rl) / len(rl), 4) if rl else None),
        "kurtarilan_ort_r_olculemedi": None if rl else "r_multiple boş — ort-R ÖLÇÜLEMEDİ",
        "K1_serhi": ("AÇILIR (Ö1 > %20)" if oran > 20.0 else "AÇILMAZ (Ö1 ≤ %20)"),
    }


def main() -> int:
    if not (BURASI / f"sonuc_grid{EK}.json").exists():
        print(f"sonuc_grid{EK}.json YOK — önce olcum.py koşmalı."); return 1
    out = {"kart": "EXE-2026-006", "kalem": "Ö-51b", "tarih": "2026-08-22", "smoke": SMOKE,
           "karar_kurali_donuk": "Ö1 > %20 ⇒ K1 şerhi açılır (ölçümden ÖNCE yazıldı)",
           "tavanlar": {}}
    print("── A KOLU BAYT ÖZDEŞLİĞİ (2026-08-22 ↔ 2026-08-17) ──")
    for cap in TAVANLAR:
        z = bayt_ozdeslik(cap); out["tavanlar"].setdefault(str(cap), {})["bayt_ozdeslik"] = z
        print(f"  cap={cap:<6} özdeş={z.get('ozdes')} {z.get('neden') or z.get('not') or ''}")
    print("── Ö1 (KİMLİKLİ) ──")
    for cap in TAVANLAR:
        r = o1(cap); out["tavanlar"][str(cap)]["O1"] = r
        if r["O1_yuzde"] is None:
            print(f"  cap={cap:<6} Ö1=ÖLÇÜLEMEDİ — {r['olculemedi_neden']}")
        else:
            print(f"  cap={cap:<6} Ö1={r['O1_yuzde']:>5}%  "
                  f"({r['pay_KURTARILAN_distinkt_islem']}/{r['payda_DISTINKT_reddedilen_plan']} plan) · "
                  f"red olayı={r['red_OLAY_sayisi_gecersiz_payda']} (×{r['olay_plan_carpani']}) · "
                  f"yerinden={r['yerinden_etme_PAYA_GIRMEDI']} · ort-R={r['kurtarilanlarin_ort_r']} · "
                  f"{r['K1_serhi']}")
    y = BURASI / f"O1_kimlikli{EK}.json"
    y.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"yazıldı: {y}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
