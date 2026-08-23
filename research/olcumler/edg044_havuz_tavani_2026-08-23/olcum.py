#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""EDG-2026-044 AŞAMA-1 yerel ölçümü — havuz tavanı 2 vs 3 işçi, duvar-saati + işçi başına CPU.

Kart: research/cards/EDG-2026-044-havuz-tavani.yaml (DONUK — bu betik karta DOKUNMAZ).
İş yükü (kart: "SABİT bir arama iş yükü, aynı tohum/aynı aday kümesi"): 6 sabit tek-değişken
sonda (aşağıda PROBES listesi — üretimdeki sprint bütçesiyle aynı boy: A1'de _workers()=2 →
budget = BUDGET_PER_WORKER(3) × 2 = 6). Adaylar üretim yolunun TA KENDİSİYLE kurulur
(versioning.bump → _probe_key → _pool_probe_job args şeması _parallel_prefill_probes ile birebir)
ve üretim havuz mekaniğiyle koşulur (spawn ctx + _pool_worker_init + _havuz_sonuclari).

YAZIM SINIRI: sonuçlar YALNIZ bu klasördeki sonuc*.json'a yazılır. _probe_disk_save/_PROBE_CACHE
disk kalıcılığı BİLEREK atlanır (state'e yazım yasak); işçiler zaten yalnız hesaplar
(reflect._havuzu_oldur docstring'i: "yazım ebeveynde").

HÜCRELER: KAL (1 işçi × 1 sonda — ısınma/kalibrasyon, sayılmaz) → A(2) → B(3) → A(2) → B(3).
SIRAYLA, paralel değil. Her hücre öncesi/sonrası sistem yükü kaydedilir (duvar-saati hijyeni).
"""
import hashlib
import json
import os
import resource
import subprocess
import sys
import threading
import time

REPO = "/Users/erdemozturk/AI-Trading"
OUTDIR = os.path.join(REPO, "research/olcumler/edg044_havuz_tavani_2026-08-23")
sys.path.insert(0, REPO)

from meridian import config, dataset, reflect, versioning  # noqa: E402

# SABİT ADAY KÜMESİ ("tohum" = bu donuk liste; her hücrede birebir aynı 6 sonda).
# Değerler v5 stratejisinin gerçek düğmelerinde makul tek-adım oynamalar; duvar-saati ölçümü
# için değerin kendisi değil SABİTLİĞİ önemli (determinizm parmak izi hücreler arası doğrulanır).
PROBES = [
    ("entry.rs_rating_min", 75),
    ("entry.pivot_proximity_pct", 2.0),
    ("entry.min_volume_ratio", 1.8),
    ("exit.profit_target_r", 3.0),
    ("exit.trail_atr_mult", 2.0),
    ("stop_loss_atr_mult", 2.5),
]

CELL_ORDER = [2, 3, 2, 3]  # A-B-A-B


def sysload() -> dict:
    """Toplam %CPU (ps -A) + loadavg — duvar-saati hijyeni beyanı."""
    try:
        out = subprocess.run(["/bin/sh", "-c", "ps -A -o %cpu | awk '{s+=$1} END {print s}'"],
                             capture_output=True, text=True, timeout=15).stdout.strip()
        toplam_cpu = float(out)
    except Exception as e:
        toplam_cpu = None  # ölçülemedi: ps/awk hattı düştü — None + neden (uydurma yasağı)
    return {"ts": time.time(), "toplam_ps_cpu_pct": toplam_cpu,
            "loadavg": list(os.getloadavg())}


def build_jobs() -> list:
    """_parallel_prefill_probes'un iş kurma yolu birebir (disk önbelleği adımları HARİÇ)."""
    current = config.load_strategy()
    goal = config.goal()
    w = reflect._default_windows()
    jobs = []
    for var, new in PROBES:
        cand = versioning.bump(current, var, new, note="EDG-044 asama-1 olcum sondasi")
        key = reflect._probe_key(cand, var, new, w)
        jobs.append({"key": key, "params": reflect.params_of(cand),
                     "by_regime": cand.get("params_by_regime"),
                     "version": cand["version"], "goal": goal,
                     "w": (w[0], w[1], w[2], w[3], list(w[4]), w[5]),
                     "eval_regime": reflect._eval_regime_of(var)})
    return jobs


def _fp(wf) -> str:
    """Sonuç parmak izi — hücreler arası determinizm kanıtı (aynı iş yükü, aynı sonuç)."""
    return hashlib.sha256(json.dumps(wf, sort_keys=True, default=str).encode()).hexdigest()[:16]


class Sampler(threading.Thread):
    """Havuz işçilerinin %CPU'sunu ~1.5 sn'de bir ps ile örnekler (işçi başına CPU beyanı)."""

    def __init__(self, ex):
        super().__init__(daemon=True)
        self.ex, self.stop_ev, self.samples = ex, threading.Event(), []

    def run(self):
        while not self.stop_ev.wait(1.5):
            try:
                pids = [p.pid for p in getattr(self.ex, "_processes", {}).values()]
                if not pids:
                    continue
                out = subprocess.run(["ps", "-o", "pid=,pcpu=", "-p", ",".join(map(str, pids))],
                                     capture_output=True, text=True, timeout=10).stdout
                tick = {}
                for line in out.strip().splitlines():
                    parts = line.split()
                    if len(parts) == 2:
                        tick[int(parts[0])] = float(parts[1])
                if tick:
                    self.samples.append({"ts": time.time(), "pcpu": tick})
            except Exception:
                pass  # örnekleyici ölçümü düşüremez; eksik örnek sonuçta görünür (n_ornek)


def run_cell(label: str, workers: int, jobs: list) -> dict:
    from concurrent.futures import ProcessPoolExecutor
    import multiprocessing as mp
    print(f"[{time.strftime('%H:%M:%S')}] HÜCRE {label}: {workers} işçi, {len(jobs)} sonda...",
          flush=True)
    yuk_once = sysload()
    r0 = resource.getrusage(resource.RUSAGE_CHILDREN)
    ctx = mp.get_context("spawn")
    ex = ProcessPoolExecutor(max_workers=workers, mp_context=ctx,
                             initializer=reflect._pool_worker_init)
    sampler = Sampler(ex)
    sampler.start()
    t0 = time.perf_counter()
    fps, tamamlar = {}, []
    try:
        for key, wf in reflect._havuz_sonuclari(ex, jobs):
            tamamlar.append(round(time.perf_counter() - t0, 2))
            fps[key[-40:]] = _fp(wf)
        wall = time.perf_counter() - t0
        ex.shutdown()  # işler bitti — join anlık (üretimdeki normal yol)
    except Exception:
        reflect._havuzu_oldur(ex)
        raise
    finally:
        sampler.stop_ev.set()
        sampler.join(timeout=5)
    r1 = resource.getrusage(resource.RUSAGE_CHILDREN)
    yuk_sonra = sysload()
    cocuk_cpu_sn = (r1.ru_utime - r0.ru_utime) + (r1.ru_stime - r0.ru_stime)
    # işçi başına ortalama %CPU (ps örneklerinden, pid bazında)
    per_pid: dict = {}
    for s in sampler.samples:
        for pid, pc in s["pcpu"].items():
            per_pid.setdefault(pid, []).append(pc)
    isci_cpu = {str(pid): {"ort_pcpu": round(sum(v) / len(v), 1), "maks_pcpu": max(v),
                           "n_ornek": len(v)} for pid, v in per_pid.items()}
    return {"hucre": label, "isci": workers, "n_sonda": len(jobs),
            "duvar_saati_sn": round(wall, 2),
            "sonda_tamamlanma_sn": tamamlar,
            "cocuk_cpu_sn_toplam": round(cocuk_cpu_sn, 1),
            "ort_kullanilan_cekirdek": round(cocuk_cpu_sn / wall, 2) if wall else None,
            "isci_basina_cpu": isci_cpu,
            "yuk_once": yuk_once, "yuk_sonra": yuk_sonra,
            "sonuc_parmak_izleri": fps}


def main() -> None:
    baslangic_yuku = sysload()
    print(f"Başlangıç yükü: {baslangic_yuku}", flush=True)
    # Künye: yerel veri durumu (ölçüm bağlamı tuzağına karşı beyan) + FS önbelleği ısındırma
    bars, index = dataset.load_cached()
    kunye = {"n_ticker": len(bars), "index_satir": int(len(index)),
             "fetch_end": dataset.fetch_end(), "cpu_count": os.cpu_count(),
             "makine": "Apple M3 (4P+4E, 8 mantıksal)", "platform": sys.platform,
             "python": sys.version.split()[0],
             "havuz_atalet_sn": reflect.HAVUZ_ATALET_SN,
             "strateji_surumu": config.load_strategy().get("version")}
    print(f"Künye: {kunye}", flush=True)
    del bars, index  # ebeveyn kopyası gereksiz; işçiler kendi load_cached()'ini koşar

    jobs = build_jobs()
    sonuc = {"kart": "EDG-2026-044", "asama": 1, "tarih": time.strftime("%Y-%m-%d %H:%M:%S"),
             "kunye": kunye, "sabit_aday_kumesi": [list(p) for p in PROBES],
             "baslangic_yuku": baslangic_yuku, "hucreler": []}

    def _kaydet(ad="sonuc_partial.json"):
        with open(os.path.join(OUTDIR, ad), "w") as f:
            json.dump(sonuc, f, ensure_ascii=False, indent=1)

    # KALİBRASYON/ISINMA (sayılmaz): 1 işçi × 1 sonda — T_wf + işçi-açılış maliyeti görünür,
    # FS/spawn önbellekleri ısınır (ilk sayılan hücre soğuk-başlangıç avantajsızlığı yaşamasın).
    sonuc["kalibrasyon"] = run_cell("KAL", 1, jobs[:1])
    _kaydet()
    print(f"  KAL bitti: {sonuc['kalibrasyon']['duvar_saati_sn']} sn", flush=True)

    for i, w_ in enumerate(CELL_ORDER):
        c = run_cell(f"{'AB'[w_ - 2]}{i // 2 + 1}", w_, jobs)
        sonuc["hucreler"].append(c)
        _kaydet()
        print(f"  bitti: {c['duvar_saati_sn']} sn (işçi={w_})", flush=True)

    # Determinizm kanıtı: tüm hücrelerde parmak izleri birebir aynı mı
    fp_setleri = [json.dumps(c["sonuc_parmak_izleri"], sort_keys=True) for c in sonuc["hucreler"]]
    sonuc["determinizm_ayni_sonuclar"] = len(set(fp_setleri)) == 1

    # EŞİK KIYASI (mekanik — kart success_metric aşama-1 kolu: kazanç < %20 → kart kapanır)
    t2 = [c["duvar_saati_sn"] for c in sonuc["hucreler"] if c["isci"] == 2]
    t3 = [c["duvar_saati_sn"] for c in sonuc["hucreler"] if c["isci"] == 3]
    med = lambda v: sorted(v)[len(v) // 2] if len(v) % 2 else sum(sorted(v)[len(v) // 2 - 1:len(v) // 2 + 1]) / 2
    kiyas = {}
    for ad, agg in (("ortalama", lambda v: sum(v) / len(v)), ("medyan", med)):
        a2, a3 = agg(t2), agg(t3)
        oran = a3 / a2
        kiyas[ad] = {"t2_sn": round(a2, 2), "t3_sn": round(a3, 2),
                     "oran_O1_3isci_bolu_2isci": round(oran, 4),
                     "kazanc_pct": round((1 - oran) * 100, 2),
                     "esik_pct20_karsilandi": (1 - oran) >= 0.20}
    sonuc["esik_kiyasi"] = {"kural": "kart success_metric aşama-1: kazanç ≥ %20 değilse kart kapanır",
                            "t2_kosumlari_sn": t2, "t3_kosumlari_sn": t3, **kiyas}
    sonuc["bitis_yuku"] = sysload()
    _kaydet("sonuc.json")
    try:
        os.remove(os.path.join(OUTDIR, "sonuc_partial.json"))
    except OSError:
        pass
    print("SONUC:", json.dumps(sonuc["esik_kiyasi"], ensure_ascii=False, indent=1), flush=True)
    print("determinizm_ayni_sonuclar:", sonuc["determinizm_ayni_sonuclar"], flush=True)


if __name__ == "__main__":
    main()
