"""EDG-2026-043 · devam koşumu (2026-08-22) — kesinti telafisi.

NEDEN VAR: tam koşum (olcum.py, arka plan görevi) slip25_B koşumu SIRASINDA dışarıdan
öldürüldü (görev durumu 'killed'; süreç yok; slip25_B çıktısı YAZILMADI — şasi çıktıları
koşum sonunda yazar, yarıda kalan koşumun kalıntısı yok). Diskte TAMAMLANMIŞ ve kapıları
geçmiş dört koşum var: kontrol (şasi kapısı kill#1 GEÇTİ — sasi_kontrolu.json) +
slip15_A / slip15_B / slip25_A (hucre_*.json: kill2/bütünlük/kill3 hepsi True).

BU BETİK YENİDEN İCAT ETMEZ: olcum.py modül olarak yüklenir, AYNI fonksiyonlar çağrılır
(hucre_kos / delta_pnl_ci / motor_sha / referans_modul). İDEMPOTENT: hucre_<run>.json
TAMAMSA o koşum ATLANIR (diskteki kanıt yeniden üretilmez, bayrakları doğrulanır);
eksikler koşulur; hepsi tamamsa Δ+CI ve sonuc_grid.json (kesinti şerhiyle) yazılır.

KAPALI-KAPI HÜCRELERİ (edg040) BU BETİKTE DE ASLA KOŞULMAZ (kill#4). KONTROL YENİDEN
KOŞULMAZ: şasi kapısı koşum-öncesi kanıttır, kaydı diskte; kesintinin iki yakası motor
sha ZİNCİRİYLE bağlanır: duman koşumunun motor_sha256_once kaydı == şimdi == koşum sonu
değilse kill#5 düşer (broker.py + backtest.py + state/goal.yaml)."""
import datetime as dt
import json
import pathlib
import sys

BURASI = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(BURASI.parents[2]))

# olcum.py modül olarak (argv'de --smoke yok; __main__ bloğu import'ta çalışmaz)
#
# KAYNAKTAN DERLENİR (2026-08-30). Eski `exec_module` yolu `__pycache__`e bakardı ve zaman
# damgalı pyc'nin geçerlilik kontrolü YALNIZ (tam-saniye mtime, bayt boyutu) çiftidir: boyutu
# değiştirmeyen bir düzenleme aynı saniyede kalırsa BAYAT bytecode koşar. Bedeli burada
# DOĞRUDAN ölçümdür — `M.motor_sha()` ve devam koşumunun bütün hücreleri ESKİ bir `olcum.py`den
# gelir, üstelik `sonuc.json` doğru görünür. Kesinti telafisi koşumu tam da "aynı ölçüm devam
# ediyor" iddiasındadır; sessizce başka bir sürüme kaymak o iddiayı geçersiz kılardı.
# Gerekçe + ölçüm: `ops/sasi_yukleyici.py` başlığı · kapı: tests/test_bayat_bytecode_v334.py §C.
# (`sys.path` eki bu dosyanın başında ZATEN var — `ops` bu noktada çözülür.)
from ops.sasi_yukleyici import kaynaktan_yukle                                    # noqa: E402

M = kaynaktan_yukle(BURASI / "olcum.py", "edg043_olcum")

PLAN = [(15.0, "A"), (15.0, "B"), (25.0, "A"), (25.0, "B"), (35.0, "A"), (35.0, "B")]


def main() -> int:
    motor_simdi = M.motor_sha()
    # zincir çapası: duman koşumunun başındaki sha kaydı (aynı gün, kesintiden önce)
    smoke_grid = json.loads((BURASI / "sonuc_grid_smoke.json").read_text())
    zincir_once = smoke_grid.get("motor_sha256_once")
    if motor_simdi != zincir_once:
        print(f"KILL#5 ZİNCİRİ KOPUK: motor/goal sha duman kaydından farklı — DUR\n"
              f"  duman: {zincir_once}\n  şimdi: {motor_simdi}")
        return 2

    sk = json.loads((BURASI / "sasi_kontrolu.json").read_text())
    if not sk.get("kill1_gecti"):
        print("kill#1 kaydı GEÇMEMİŞ görünüyor — devam edilemez, DUR")
        return 2

    kontrol = json.loads((BURASI / "hucre_kontrol.json").read_text())

    rapor: dict = {
        "kart": "EDG-2026-043", "smoke": False,
        "olcum_zamani": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "motor_sha256_once": zincir_once,
        "tavan": M.TAVAN,
        "kesinti_serhi": {
            "olay": ("ilk tam koşum (olcum.py) slip25_B koşumu sırasında arka plan görev "
                     "altyapısınca öldürüldü; slip25_B çıktısı yazılmamıştı (temiz kesinti)"),
            "devam_politikasi": ("tamamlanmış koşumlar DİSKTEN okundu (yeniden koşulmadı); "
                                 "eksikler bu koşumda; kapalı-kapı hücreleri (edg040) hiçbir "
                                 "aşamada yeniden koşulmadı; kontrol yeniden koşulmadı — şasi "
                                 "kapısı kaydı + motor sha zinciri iki yakayı bağlar"),
            "motor_sha_zinciri": {"duman_once": zincir_once, "devam_once": motor_simdi,
                                  "esit": motor_simdi == zincir_once}},
    }
    rapor["envanter"] = M.envanter_yap(False)
    rapor["kontrol_slip5_kapali"] = kontrol
    rapor["sasi_kontrolu"] = sk

    ref = None
    hucreler: dict = {}
    diskten, kosulan = [], []
    for bps, kol in PLAN:
        run = f"slip{int(bps)}_{kol}"
        kural = M.KOLLAR[kol]
        hj = BURASI / f"hucre_{run}.json"
        dj = BURASI / f"islemler_tam_{run}.json"
        if hj.exists() and dj.exists():
            h = json.loads(hj.read_text())
            # diskten okunan koşumun kapı bayrakları da doğrulanır (kör güven yok)
            if not (h.get("oz_sinama_kill2_gecti") and h.get("kol_kimligi_gecti")
                    and h.get("butunluk_gecerli")):
                rapor["DURDU"] = f"{run}: diskteki kayıtta kapı bayrağı düşük — devam edilemez"
                (BURASI / "sonuc_grid.json").write_text(
                    json.dumps(rapor, ensure_ascii=False, indent=1), encoding="utf-8")
                print(rapor["DURDU"])
                return 2
            hucreler[run] = h
            diskten.append(run)
            print(f"  [DİSKTEN] {run}: n={h['islem_n']} net={h['net_pnl_trades']} "
                  f"kill2={h['oz_sinama_kill2_gecti']} damga={h['dolum_kurali_damgasi']}",
                  flush=True)
            continue
        if ref is None:
            ref = M.referans_modul()
            print(f"referans şasi yüklendi · SANDBOX={ref.SANDBOX}", flush=True)
        try:
            h = M.hucre_kos(ref, run, bps, kural, cap=M.TAVAN, smoke=False)
        except AssertionError as e:
            rapor["DURDU"] = f"{run}: {e}"
            rapor["hucreler"] = {k: {a: b for a, b in v.items() if a != "red_kimlik"}
                                 for k, v in hucreler.items()}
            (BURASI / "sonuc_grid.json").write_text(
                json.dumps(rapor, ensure_ascii=False, indent=1), encoding="utf-8")
            print(f"KAPI DÜŞTÜ ({run}): {e} — ölçüm DURDU", flush=True)
            return 2
        hucreler[run] = h
        kosulan.append(run)
        if not h["oz_sinama_kill2_gecti"]:
            rapor["DURDU"] = f"kill#2: {run} öz-sınaması düştü — sonraki hücre koşulmadı"
            rapor["hucreler"] = {k: {a: b for a, b in v.items() if a != "red_kimlik"}
                                 for k, v in hucreler.items()}
            (BURASI / "sonuc_grid.json").write_text(
                json.dumps(rapor, ensure_ascii=False, indent=1), encoding="utf-8")
            print(f"KILL#2 DÜŞTÜ ({run}) — ölçüm DURDU", flush=True)
            return 2
    rapor["kesinti_serhi"]["diskten_okunan"] = diskten
    rapor["kesinti_serhi"]["bu_kosumda_kosulan"] = kosulan
    rapor["hucreler"] = {k: {a: b for a, b in v.items() if a != "red_kimlik"}
                         for k, v in hucreler.items()}

    # [5] Δ+CI — olcum.py main bloğu AYNEN (kapalı kol edg040 DONMUŞ defterinden)
    seanslar = json.loads((BURASI / "seanslar_kontrol.json").read_text())
    aylar = sorted({str(r["date"])[:7] for r in seanslar})
    envanter = rapor["envanter"]
    delta: dict = {}
    for bps in M.SLIPLER:
        s_int = int(bps)
        run_kapali = f"slip{s_int}"
        blok: dict = {}
        env = envanter["kapali_hucreler"].get(run_kapali) or {}
        kapali_defter = None
        if env.get("mevcut"):
            kapali_defter = json.loads(
                (M.EDG040 / f"islemler_tam_{run_kapali}.json").read_text())
        A_defter = json.loads((BURASI / f"islemler_tam_slip{s_int}_A.json").read_text())
        B_defter = json.loads((BURASI / f"islemler_tam_slip{s_int}_B.json").read_text())
        if kapali_defter is not None:
            blok["acikA_eksi_kapali"] = M.delta_pnl_ci(kapali_defter, A_defter, aylar)
            blok["acikB_eksi_kapali"] = M.delta_pnl_ci(kapali_defter, B_defter, aylar)
            blok["kapali_kaynak"] = {"dosya": env["islemler_tam_dosyasi"],
                                     "sha256": env.get("sha256")}
        else:
            neden = env.get("ci_kurulamaz_nedeni") or "kapalı defter envanterde yok"
            kapali_net = (env.get("edg040_hucre_ozeti") or {}).get("net_pnl_trades")
            for ad, kol in (("acikA_eksi_kapali", "A"), ("acikB_eksi_kapali", "B")):
                net = hucreler[f"slip{s_int}_{kol}"]["net_pnl_trades"]
                blok[ad] = {"delta_pnl": (round(net - kapali_net, 2)
                                          if None not in (net, kapali_net) else None),
                            "ci95": None, "ci_olculemedi_nedeni": neden,
                            "nokta_kaynagi": "hucre özet net_pnl_trades farkı (defter yok)"}
        blok["A_eksi_B"] = M.delta_pnl_ci(B_defter, A_defter, aylar)
        ak = {(t.get("ticker"), t.get("ts_open")) for t in A_defter}
        yalniz_b = [t for t in B_defter if (t.get("ticker"), t.get("ts_open")) not in ak]
        rler = [float(t["r_multiple"]) for t in yalniz_b if t.get("r_multiple") is not None]
        blok["kol_farki"] = {
            "kacan_A_olay": hucreler[f"slip{s_int}_A"]["entry_missed_limit_olay"],
            "kacan_A_distinkt_plan": hucreler[f"slip{s_int}_A"]["entry_missed_limit_distinkt_plan"],
            "dinlenen_kolda_DOLAN_ek_islem": len(yalniz_b),
            "ek_islem_ort_r": (round(sum(rler) / len(rler), 4) if rler else None),
            "ek_islem_ort_r_olculemedi": (None if rler else
                                          "ek işlem yok ya da r_multiple boş — ort-R ÖLÇÜLEMEDİ"),
            "ek_islem_n_r": len(rler)}
        delta[f"slip{s_int}"] = blok
        for ad in ("acikA_eksi_kapali", "acikB_eksi_kapali", "A_eksi_B"):
            b = blok[ad]
            print(f"  Δ[slip{s_int}·{ad}]: {b.get('delta_pnl')} CI95={b.get('ci95')} "
                  f"({b.get('sifir_disinda', b.get('ci_olculemedi_nedeni'))})", flush=True)
    rapor["delta"] = delta

    motor_sonra = M.motor_sha()
    rapor["motor_sha256_sonra"] = motor_sonra
    rapor["kill5_motor_goal_ayni"] = (zincir_once == motor_sonra)
    if not rapor["kill5_motor_goal_ayni"]:
        print("KILL#5: motor/goal sha koşum sırasında DEĞİŞTİ — ilgili hücreler geçersiz (raporda)",
              flush=True)

    yol = BURASI / "sonuc_grid.json"
    yol.write_text(json.dumps(rapor, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"yazıldı: {yol}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
