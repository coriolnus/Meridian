"""KALEM 3 — earnings fail-open TEŞHİS (kod değişikliği YOK, salt-okunur ölçüm).

Sorular:
  S1. Kapsam-dışı sembolde karartma kapısı ne yapıyor? (koddan + davranışsal)
  S2. Kapsam bugün ne? (evren × takvim)
  S3. RİSK NİCELEME: kapsam-dışı sınıfta geçmişte kaç plan GO aldı / kaç işlem açıldı, ve
      "kazanç gününde açıldı mı" sorusu ÖLÇÜLEBİLİR Mİ?
"""
from __future__ import annotations

import json
import os
import sys
from collections import Counter
from pathlib import Path

SB = Path(__file__).resolve().parent
os.environ["MERIDIAN_ROOT"] = str(SB)
os.environ.setdefault("MERIDIAN_MODE", "paper")
sys.path.insert(0, "/Users/erdemozturk/AI-Trading")

LIVE = Path("/Users/erdemozturk/AI-Trading/state")

# kum havuzuna canlı earnings.csv'nin KOPYASI (salt-okunur ölçüm; üretim dosyasına yazılmaz)
(SB / "state").mkdir(parents=True, exist_ok=True)
import shutil  # noqa: E402
shutil.copy2(LIVE / "earnings.csv", SB / "state" / "earnings.csv")

from meridian import earnings  # noqa: E402
from meridian.adapters import data  # noqa: E402


def jsonl(p: Path):
    if not p.exists():
        return
    for line in p.open():
        line = line.strip()
        if not line:
            continue
        try:
            yield json.loads(line)
        except Exception:
            continue


def main() -> None:
    uni = sorted(set(str(t).upper() for t in data.REPLAY_UNIVERSE))
    cal = earnings._load()
    kapsam_disi = [t for t in uni if t not in cal]
    out: dict = {
        "kaynak": {"earnings_csv": str(LIVE / "earnings.csv"),
                   "csv_mtime": __import__("datetime").datetime.fromtimestamp(
                       (LIVE / "earnings.csv").stat().st_mtime).isoformat(timespec="seconds"),
                   "not": "YEREL SNAPSHOT — canlı A1'deki takvim daha taze olabilir"},
        "S1_davranis": {},
        "S2_kapsam": {"evren": len(uni), "takvimde": len(cal),
                      "evren_kapsanan": len(uni) - len(kapsam_disi),
                      "evren_kapsam_disi": len(kapsam_disi),
                      "kapsam_disi_liste": kapsam_disi,
                      "takvimde_ama_evren_disi": sorted(set(cal) - set(uni)),
                      "BLACKOUT_DAYS": earnings.BLACKOUT_DAYS,
                      "coverage": {k: v for k, v in earnings.coverage(uni).items()
                                   if k != "unknown_sample"}},
        "S3_risk": {},
    }

    # --- S1: davranışsal kanıt (kod okumaya ek olarak fiilen koştur) -----------------------------
    ornek = kapsam_disi[0] if kapsam_disi else None
    bilinen = next(iter(cal), None)
    out["S1_davranis"] = {
        "kapsam_disi_ornek": ornek,
        "in_blackout(kapsam_disi, bilinen_bir_rapor_gunu)":
            (earnings.in_blackout(ornek, next(iter(cal.values()))[0]) if ornek and cal else None),
        "known(kapsam_disi)": earnings.known(ornek) if ornek else None,
        "coverage_note(kapsam_disi)": earnings.coverage_note(ornek) if ornek else None,
        "bilinen_ornek": bilinen,
        "in_blackout(bilinen, kendi_rapor_gunu)":
            (earnings.in_blackout(bilinen, cal[bilinen][0]) if bilinen else None),
        "hukum": "veri yoksa False döner — kapı GEÇİRGEN (fail-open), karar yolu değişmez",
    }

    # --- S3: plan/işlem defterlerinde kapsam-dışı sınıf -----------------------------------------
    plan_by_id: dict = {}
    say = Counter()
    kapsam_alani = Counter()
    go_kapsam_disi, go_kapsanan = [], []
    for p in jsonl(LIVE / "trade_plans.jsonl"):
        say["plan"] += 1
        t = str(p.get("ticker") or "").upper()
        plan_by_id[p.get("id")] = p
        cov = None
        for ch in (p.get("gate_checks") or []):
            if ch.get("check") == "earnings_blackout":
                cov = ch.get("coverage")
        kapsam_alani[str(cov)] += 1
        v = p.get("gate_verdict")
        say[f"verdict_{v}"] += 1
        disi = t not in cal
        if v == "GO":
            (go_kapsam_disi if disi else go_kapsanan).append({"t": t, "d": p.get("date"), "id": p.get("id")})
        # gerekçe metninde beyan var mı
        if any("earnings_kapsami_yok" in str(r) for r in (p.get("gate_reasons") or [])):
            say["gerekce_beyanli"] += 1
        if any("karartma" in str(r) for r in (p.get("gate_reasons") or [])):
            say["karartma_vetosu"] += 1

    islem_disi, islem_kapsanan = [], []
    for tr in jsonl(LIVE / "trades.jsonl"):
        t = str(tr.get("ticker") or "").upper()
        rec = {"t": t, "ts_open": tr.get("ts_open"), "plan_id": tr.get("plan_id")}
        (islem_disi if t not in cal else islem_kapsanan).append(rec)

    out["S3_risk"] = {
        "plan_defteri": {"toplam": say["plan"],
                         "gate_checks.coverage_dagilimi": dict(kapsam_alani),
                         "verdict_dagilimi": {k[8:]: v for k, v in say.items() if k.startswith("verdict_")},
                         "gerekce_metninde_beyan": say["gerekce_beyanli"],
                         "karartma_vetosu_dusen_plan": say["karartma_vetosu"]},
        "GO_plan_kapsam_disi": len(go_kapsam_disi),
        "GO_plan_kapsanan": len(go_kapsanan),
        "GO_plan_kapsam_disi_ornek": go_kapsam_disi[:15],
        "islem_defteri": {"toplam": len(islem_disi) + len(islem_kapsanan),
                          "kapsam_disi_sembolde": len(islem_disi),
                          "kapsanan_sembolde": len(islem_kapsanan),
                          "kapsam_disi_semboller": sorted({x["t"] for x in islem_disi}),
                          "kapsam_disi_ornek": islem_disi[:15]},
        "kazanc_gununde_acildi_mi": None,
        "kazanc_gunu_olcum_gerekcesi":
            "ÖLÇÜLEMEZ — UYDURMA YASAĞI. Kapsam-dışı sembolün takvimde HİÇ tarihi yok; geçmiş bir "
            "işlemin o sembolün kazanç gününe denk gelip gelmediğini söyleyecek PIT kazanç takvimi "
            "bu depoda YOK (earnings.csv ileri-pencere snapshot'ı, geçmiş çapa biriktirmiyor: "
            f"{len(cal)} sembol × {sum(len(v) for v in cal.values())} tarih = sembol başına "
            f"{round(sum(len(v) for v in cal.values()) / max(len(cal), 1), 2)} tarih). Ölçmek için "
            "dış PIT kaynak (NASDAQ/FMP geçmiş takvim) gerekir — bu tur kapsam dışı.",
    }

    # takvimin biçimi: sembol başına kaç tarih (geçmiş çapa birikiyor mu?)
    out["S2_kapsam"]["takvim_bicimi"] = {
        "toplam_tarih": sum(len(v) for v in cal.values()),
        "sembol_basina_tarih_dagilimi": dict(Counter(len(v) for v in cal.values())),
        "en_eski_tarih": min((d for v in cal.values() for d in v), default=None),
        "en_yeni_tarih": max((d for v in cal.values() for d in v), default=None),
    }
    print("###JSON###")
    print(json.dumps(out, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
