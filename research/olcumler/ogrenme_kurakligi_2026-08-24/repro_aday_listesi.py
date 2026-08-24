"""CANLI GİRDİLERLE ISINMA ADAY LİSTESİNİN YENİDEN ÜRETİMİ (salt-okuma, yerel).
MERIDIAN_ROOT = scratch/livestate (canlıdan kopyalanan bounds/strategy/hypotheses/exit_efficiency).
Yalnız aday SIRALAMASI hesaplanır — hiçbir walk-forward koşulmaz."""
import os, sys, hashlib, json
SB = "/private/tmp/claude-501/-Users-erdemozturk-AI-Trading/f323a729-1d39-4530-b645-7c71fa2ed997/scratchpad/livestate"
os.environ["MERIDIAN_ROOT"] = SB
sys.path.insert(0, "/Users/erdemozturk/AI-Trading")
from meridian import config, reflect, memory, guard, versioning  # noqa

def liste(k_max=2, budget=10):
    bounds = config.bounds()
    current = config.load_strategy()
    params = reflect.params_of(current)
    hyps = memory.all_hypotheses()
    arama_uzayi, hayalet = reflect.hayalet_suzgeci(bounds, kaynak="repro")
    ranked = reflect._ucb_rank(arama_uzayi, hyps)
    probes, seen = [], set()
    for k in range(k_max, 0, -1):
        for var in ranked:
            b = bounds[var]
            lo, hi, step, typ = b["min"], b["max"], b["step"], b["type"]
            cur = params.get(var, lo)
            for direction in (+1, -1):
                raw = cur + direction * k * step
                new = max(lo, min(hi, raw))
                new = int(round(new)) if typ == "int" else round(new, 4)
                if guard._equalish(new, cur, typ):
                    continue
                sig = (var, new)
                if sig in seen or reflect._already_failed(var, new, hyps, bounds):
                    continue
                seen.add(sig)
                probes.append(sig)
    return probes, len(bounds), len(arama_uzayi), (hayalet if hayalet is None else len(hayalet)), len(hyps)

p1, nb, nu, nh, nhyp = liste()
p2, *_ = liste()
cap = max(10 * 4, 40)
ilk40_1, ilk40_2 = p1[:cap], p2[:cap]
h1 = hashlib.sha256(repr(ilk40_1).encode()).hexdigest()[:16]
h2 = hashlib.sha256(repr(ilk40_2).encode()).hexdigest()[:16]
print("bounds anahtar sayisi:", nb, "| hayalet suzgecinden gecen:", nu, "| hayalet:", nh, "| defter hipotez:", nhyp)
print("toplam uretilen aday (k_max=2):", len(p1), "| plan kapagi max(budget*4,40) =", cap)
print("iki cagri ayni mi:", p1 == p2, "| sha16:", h1, h2)
print("--- PLANA GIREN ILK 40 ADAY (sira aynen):")
for i, (v, n) in enumerate(ilk40_1, 1):
    print(f"{i:3d}. {v} -> {n}")
print("--- PLANA GIREMEYEN ILK 10 (41-50):")
for i, (v, n) in enumerate(p1[cap:cap+10], cap+1):
    print(f"{i:3d}. {v} -> {n}")
