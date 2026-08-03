"""E1 GRID KUM HAVUZU KURULUMU (kart EXE-2026-001, parameter_grid).

DESEN: research/olcumler/karne_tazeleme_2026-08-03 harness'i AYNEN — motor KOPYALANIR (yamalanmaz,
sha ile damgalanır), her kol kendi `state_<kol>/` dizinine yazar, barlar/research canlıdan SEMBOLİK
BAĞ ile salt-okunur.

TEK FARK KAYNAĞI: her kolun `state_<kol>/goal.yaml`ındaki `execution_v2` bloğu. Üretim dosyası
DEĞİŞTİRİLMEZ; parametre yalnız kum havuzu kopyasındaki SATIRLARDA değişir (satır-düzeyi cerrahi
değişim — dosyanın geri kalanı BAYT AYNI kalır, kanıt: goal_diff_<kol>.txt).
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import shutil

DEPO = pathlib.Path("/Users/erdemozturk/AI-Trading")
SB = pathlib.Path(__file__).resolve().parent

# --- KOLLAR: 6 grid hücresi (kart parameter_grid) + 1 grid-DIŞI referans ----------------------
# (limit_atr_mult, limit_pct_cap, gap_behavior)
KOLLAR = {
    # limit_offset = min(0.25*ATR14, %0.5)
    "a_mkt":  (0.25, 0.005, "marketable_limit"),
    "a_cnl":  (0.25, 0.005, "cancel"),
    # limit_offset = min(0.5*ATR14, %1.0)  ← MEVCUT VARSAYILAN (= referans "güncel varsayılan")
    "b_mkt":  (0.5,  0.01,  "marketable_limit"),
    "b_cnl":  (0.5,  0.01,  "cancel"),
    # limit_offset = min(1.0*ATR14, %1.5)
    "c_mkt":  (1.0,  0.015, "marketable_limit"),
    "c_cnl":  (1.0,  0.015, "cancel"),
    # REFERANS (grid DIŞI): "eski koşulsuz-açılış" — limit tavanı HİÇ BAĞLAMAZ.
    # limit = tetik + min(1000*ATR, %10*tetik) = tetik*1.10 > max_chase tavanı tetik*1.04,
    # yani `entry_missed_limit` YAPISAL OLARAK İMKANSIZ olmalı (ölçülür: iddia sayıyla sınanır).
    # Aynı bayrak yolu karne_olcum `e1_oncesi_icra` kolunda kullanıldı (pct_cap 0.01→0.10);
    # oradan farkı ATR bacağını da etkisizleştirmesi (o kolda replay atr GEÇİRMİYORDU).
    "ref_limitsiz": (1000.0, 0.10, "marketable_limit"),
}

STATE_DOSYA = ("goal.yaml", "bounds.yaml", "strategy.yaml", "bars_integrity.json", "earnings.csv")


def sha_dizin(d: pathlib.Path) -> tuple[int, str]:
    h = hashlib.sha256()
    n = 0
    for p in sorted(d.rglob("*.py")):
        h.update(p.relative_to(d).as_posix().encode())
        h.update(p.read_bytes())
        n += 1
    return n, h.hexdigest()[:16]


def goal_yaz(hedef: pathlib.Path, atr_mult: float, pct_cap: float, gap: str) -> list[str]:
    """execution_v2 bloğunun ÜÇ satırını değiştirir; dosyanın geri kalanına dokunmaz."""
    satirlar = (DEPO / "state" / "goal.yaml").read_text().splitlines(keepends=True)
    icinde = False
    degisiklik = []
    for i, s in enumerate(satirlar):
        if s.startswith("execution_v2:"):
            icinde = True
            continue
        if icinde and s and not s[0].isspace() and not s.startswith("#"):
            icinde = False
        if not icinde:
            continue
        for anahtar, deger in (("limit_atr_mult", atr_mult), ("limit_pct_cap", pct_cap),
                               ("gap_behavior", gap)):
            if s.strip().startswith(f"{anahtar}:"):
                yeni = f"  {anahtar}: {deger}\n"
                if yeni != s:
                    degisiklik.append(f"-{s.rstrip()}\n+{yeni.rstrip()}")
                satirlar[i] = yeni
    hedef.write_text("".join(satirlar))
    return degisiklik


def main() -> None:
    # 1) MOTOR: tek kopya, TÜM kollar aynı motoru koşar (kollar arası fark YALNIZ goal.yaml'dır).
    motor = SB / "meridian"
    if motor.exists():
        shutil.rmtree(motor)
    shutil.copytree(DEPO / "meridian", motor,
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    n_depo, sha_depo = sha_dizin(DEPO / "meridian")
    n_sb, sha_sb = sha_dizin(motor)
    assert (n_depo, sha_depo) == (n_sb, sha_sb), f"motor kopyası BAYT EŞİT DEĞİL: {sha_depo} vs {sha_sb}"

    # 2) research SEMBOLİK BAĞ (edgar_facts/shares_outstanding.csv.gz — turnover bileşeni)
    rlink = SB / "research"
    if not rlink.exists():
        rlink.symlink_to(DEPO / "research")

    damga = {"depo_meridian": {"dosya_n": n_depo, "sha256_16": sha_depo,
                               "yol": str(DEPO / "meridian")},
             "sandbox_motor": {"dosya_n": n_sb, "sha256_16": sha_sb, "yol": str(motor),
                               "bayt_esit_mi": True},
             "not": ("TEK motor kopyası; kollar arası fark YALNIZ state_<kol>/goal.yaml "
                     "execution_v2 bloğudur. Üretim kodu DEĞİŞTİRİLMEDİ, yama YOK."),
             "kollar": {}}

    for kol, (m, p, g) in KOLLAR.items():
        sd = SB / f"state_{kol}"
        sd.mkdir(exist_ok=True)
        for f in STATE_DOSYA:
            shutil.copy2(DEPO / "state" / f, sd / f)
        (sd / "history").mkdir(exist_ok=True)
        bars = sd / "bars"
        if not bars.exists():
            bars.symlink_to(DEPO / "state" / "bars")
        dg = goal_yaz(sd / "goal.yaml", m, p, g)
        (SB / f"goal_diff_{kol}.txt").write_text("\n".join(dg) or "(fark yok — mevcut varsayılan)\n")
        # dosyanın geri kalanı bayt-aynı mı? (satır sayısı + execution_v2 dışı satırlar)
        a = (DEPO / "state" / "goal.yaml").read_text().splitlines()
        b = (sd / "goal.yaml").read_text().splitlines()
        farkli = [i for i, (x, y) in enumerate(zip(a, b)) if x != y]
        damga["kollar"][kol] = {"limit_atr_mult": m, "limit_pct_cap": p, "gap_behavior": g,
                                "goal_degisen_satir_n": len(farkli),
                                "goal_satir_n": [len(a), len(b)],
                                "goal_diff": dg}
        assert len(a) == len(b), "goal.yaml satır sayısı değişti — cerrahi değişim bozuldu"

    (SB / "kod_damgasi.json").write_text(json.dumps(damga, ensure_ascii=False, indent=1))
    print(json.dumps({"motor_sha": sha_sb, "dosya_n": n_sb,
                      "kollar": {k: v["goal_diff"] for k, v in damga["kollar"].items()}},
                     ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
