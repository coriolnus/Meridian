#!/usr/bin/env python3
"""EDG-2026-089 K1/K2 SAYIMI — retain kadansı (K1) + otomatik zihin-modeli tazelemesi (K2) günlük tablo.

A1'de SALT-OKUR koşar (ssh stdin ile: `ssh a1 python3 - --events /opt/meridian/state/events.jsonl < sayim.py`);
`meridian`ı İTHAL ETMEZ (obs'a ulaşmaz), hiçbir dosya yazmaz, stdout'a JSON basar. Hüküm Rol-1'in.
Sayı uydurulmaz: psql erişilemezse alan None + neden.

K1 ÜÇ BİLEŞENLİDİR (DÜZELTME 2026-09-21 — bu araç halef kartta KULLANILMADAN ÖNCE düzeltildi):
  (a) `k1_teslim`      — betik o gün `defter_ozeti_retain` olayını sonuc∈{retain, zaten_var} ile bastı mı (TANI),
  (b) `k1_op_basari`   — o gün hindsight `async_operations` tablosunda operation_type retain op'u status completed mi,
  (c) `k1_banka_artis` — o gün `memory_units` yeni satır sayısı ≥1 mi (created_at UTC gününe göre).
`k1_gun_dolu` = (b) ∧ (c). (a) TEK BAŞINA GÜN DOLDURMAZ.

NEDEN DEĞİŞTİ. Araç K1'i yalnız (a) ile, yani betiğin TESLİMİYLE ölçüyordu; kartın olcum_plani ise K1'i şöyle
tanımlar: "A1 hindsight DB async_operations (operation_type retain, status) + memory_units günlük count; hedef
7/7 ∧ artış ≥1/gün". İki ölçü pencere içinde İKİ KEZ çelişti (Rol-1, 2026-09-21, A1 salt-okur):
09-16 21:30:31Z retain + batch_retain FAILED (üst-akım sağlayıcı 404, "Fact extraction failed: 1/1 chunks") ve
banka büyümedi — araç o günü DOLU saydı; 09-18 op COMPLETED ama unit_ids_count 0 / facts_committed 0, banka yine
büyümedi — araç onu da DOLU saydı. Kusurun yönü tek taraflıydı: eşiği HAK ETMEDEN GEÇME. Eski (a) kolonu SİLİNMEDİ,
tanı olarak kaldı (bedel yasası: ölçüyü daraltırken kaybedilen sinyal de raporda durur). Kapı:
`tests/test_edg089_sayim_araci_v527.py`.

Kaynaklar: `state/events.jsonl` (olay `defter_ozeti_retain`, alanlar gun/sonuc/items — ops/defter_ozeti_retain.py),
Postgres `hindsight.async_operations` (operation_type/status/created_at) + `memory_units` (created_at, count)
— `sudo -u postgres psql`.
"""
from __future__ import annotations
import argparse, collections, datetime as dt, json, subprocess, sys

#: psql erişilemediğinde K1'in (b)/(c) bileşenleri için yazılan neden. "Bilinmiyor" YEŞİL sayılmaz:
#: `k1_gun_dolu` None kalır ve `k1_dolu_gun` sayıya DÖNÜŞMEZ (uydurma yasağı).
K1_PSQL_NEDEN = ("psql erişilemedi (sudo/postgres) — K1 (b) op başarısı ve/veya (c) banka artışı "
                 "ölçülemedi; teslim kolonu (a) olay defterinden ölçülüdür")

def olaylar(yol: str, baslangic: str) -> dict:
    gunler: dict[str, list] = collections.defaultdict(list)
    bozuk = 0
    with open(yol, encoding="utf-8") as fh:
        for satir in fh:
            if '"defter_ozeti_retain"' not in satir:
                continue
            try:
                r = json.loads(satir)
            except json.JSONDecodeError:
                bozuk += 1; continue
            if r.get("event") != "defter_ozeti_retain":
                continue
            ts = str(r.get("ts") or "")
            if ts[:10] < baslangic:
                continue
            gunler[ts[:10]].append({"ts": ts[:19], "sonuc": r.get("sonuc"), "items": r.get("items"),
                                    "gun": r.get("gun")})
    return {"gunler": dict(sorted(gunler.items())), "bozuk_satir": bozuk}

def psql(sql: str) -> list[str] | None:
    try:
        p = subprocess.run(["sudo", "-u", "postgres", "psql", "-d", "hindsight", "-At", "-c", sql],
                           capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired) as e:
        return None
    if p.returncode != 0:
        return None
    return [s for s in p.stdout.splitlines() if s.strip()]

def _gun_durum(satirlar: list[str] | None) -> dict[str, dict] | None:
    """`gun|status|n` satırlarını {gun: {status: n}} yapar. None girdi None kalır (ölçülemezlik)."""
    if satirlar is None:
        return None
    out: dict[str, dict] = collections.defaultdict(dict)
    for s in satirlar:
        gun, durum, n = s.split("|")
        out[gun][durum] = int(n)
    return dict(out)

def _gun_sayi(satirlar: list[str] | None) -> dict[str, int] | None:
    """`gun|n` satırlarını {gun: n} yapar. None girdi None kalır."""
    if satirlar is None:
        return None
    return {s.split("|")[0]: int(s.split("|")[1]) for s in satirlar}

def main(argv):
    a = argparse.ArgumentParser()
    a.add_argument("--events", default="/opt/meridian/state/events.jsonl")
    a.add_argument("--baslangic", default="2026-09-13", help="pencere ilk günü (UTC)")
    a.add_argument("--gun-n", type=int, default=7)
    args = a.parse_args(argv)
    ev = olaylar(args.events, args.baslangic)
    tazeleme = psql("select to_char(created_at at time zone 'UTC','YYYY-MM-DD'), status, count(*) "
                    "from async_operations where operation_type='refresh_mental_model' "
                    f"and created_at >= '{args.baslangic}' group by 1,2 order by 1,2")
    # K1 (b): kartın olcum_plani'sinin adlandırdığı kaynak — TESLİM değil OP SONUCU.
    retain_op = psql("select to_char(created_at at time zone 'UTC','YYYY-MM-DD'), status, count(*) "
                     "from async_operations where operation_type='retain' "
                     f"and created_at >= '{args.baslangic}' group by 1,2 order by 1,2")
    # K1 (c): "memory_units günlük count" — gün kovası created_at'in UTC günüdür (ölçülen şema).
    banka_gunluk = psql("select to_char(created_at at time zone 'UTC','YYYY-MM-DD'), count(*) "
                        f"from memory_units where created_at >= '{args.baslangic}' "
                        "group by 1 order by 1")
    mu = psql("select count(*) from memory_units")
    k2: dict[str, dict] = collections.defaultdict(dict)
    if tazeleme is not None:
        for s in tazeleme:
            gun, durum, n = s.split("|")
            k2[gun][durum] = int(n)
    k1_op = _gun_durum(retain_op)
    k1_yeni = _gun_sayi(banka_gunluk)
    pencere = [(dt.date.fromisoformat(args.baslangic) + dt.timedelta(days=i)).isoformat() for i in range(args.gun_n)]
    bugun = dt.datetime.now(dt.timezone.utc).date().isoformat()
    tablo = []
    for g in pencere:
        e = ev["gunler"].get(g, [])
        sonuclar = [x["sonuc"] for x in e]
        gecti = g <= bugun
        teslim = (any(s in ("retain", "zaten_var") for s in sonuclar) if gecti else None)
        op = (k1_op.get(g, {}) if (k1_op is not None and gecti) else None)
        op_basari = (op.get("completed", 0) >= 1) if op is not None else None
        yeni = (k1_yeni.get(g, 0) if (k1_yeni is not None and gecti) else None)
        artis = (yeni >= 1) if yeni is not None else None
        dolu = (bool(op_basari and artis) if (op_basari is not None and artis is not None) else None)
        tablo.append({"gun": g, "gecti_mi_takvim": gecti,
                      "k1_retain_olay_n": len(e), "k1_sonuclar": sonuclar,
                      "k1_teslim": teslim,                # (a) TANI — tek başına gün DOLDURMAZ
                      "k1_op": op, "k1_op_basari": op_basari,          # (b)
                      "k1_banka_yeni": yeni, "k1_banka_artis": artis,  # (c)
                      "k1_gun_dolu": dolu,                # (b) ∧ (c)
                      "k2_tazeleme": (k2.get(g) if tazeleme is not None else None),
                      "k2_gun_dolu": ((k2.get(g, {}).get("completed", 0) >= 1) if (tazeleme is not None and g <= bugun) else None)})
    gecen = [t for t in tablo if t["gecti_mi_takvim"]]
    k1_olculur = k1_op is not None and k1_yeni is not None
    out = {"kart": "EDG-2026-089", "uretim_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
           "pencere": pencere, "tablo": tablo,
           "k1_dolu_gun": (sum(1 for t in gecen if t["k1_gun_dolu"]) if k1_olculur else None),
           "k1_gecen_gun": len(gecen),
           "k1_teslim_gun": sum(1 for t in gecen if t["k1_teslim"]),
           "k1_op_basari_gun": (sum(1 for t in gecen if t["k1_op_basari"]) if k1_op is not None else None),
           "k1_banka_artis_gun": (sum(1 for t in gecen if t["k1_banka_artis"]) if k1_yeni is not None else None),
           "k1_neden": (None if k1_olculur else K1_PSQL_NEDEN),
           "k2_dolu_gun": (sum(1 for t in gecen if t["k2_gun_dolu"]) if tazeleme is not None else None),
           "k2_neden": (None if tazeleme is not None else "psql erişilemedi (sudo/postgres) — K2 ölçülemedi"),
           "memory_units": (int(mu[0]) if mu else None),
           "memory_units_neden": (None if mu else "psql erişilemedi"),
           "events_bozuk_satir": ev["bozuk_satir"],
           "hukum": None, "hukum_notu": "hüküm Rol-1'in — 2026-09-20'de kart basari_tanimi ile; bu tablo sayımdır"}
    json.dump(out, sys.stdout, ensure_ascii=False, indent=1); print()

if __name__ == "__main__":
    main(sys.argv[1:])
