"""EXE-2026-006 — limit bacağı hüküm sınaması · ölçüm koşumu.

KART: research/cards/EXE-2026-006-limit-bacagi-hukum-sinamasi.yaml (OKU-DOKUNMA).
Ölçüm ajanı karta DOKUNMAZ; hükmü Rol-1 işler.

NE YAPAR: E1'in limit bacağını ÖLÇÜM KOLUNDA silahlandırıp (canlı yasa onu etkisizleştirmiş)
K=8 hücreyi tarar — 4 tavan × 2 dolum kuralı.

════════ TASARIM KARARI: ŞASİ YENİDEN KURULMAZ, ÇAĞRILIR ════════
Bu betiğin İLK HÂLİ `backtest.replay`i kendisi çağırıyordu ve YANLIŞTI (2026-08-17): imzayı
tahmin etmişti (`replay(bars, index)` — gerçeği `replay(params, bars, index_bars, goal, ...)`)
ve referans koşumun `replay`den ÖNCE taktığı ÜÇ KANCAYI (`brk.max_positions_at`,
`regime_mod.build_regime_json`, `strat.scan_entry`) hiç takmıyordu.

Kartın kill kriteri: *"şasi kapısı YENİDEN koşulmazsa geçersiz."* Yanlış kurulmuş bir şasi
SESSİZCE farklı sonuç üretir ve bu ancak sekiz hücre koştuktan SONRA görünür. Bu yüzden şasi
YENİDEN KURULMUYOR: referans koşumun `kosum("kontrol", smoke)` yolu OLDUĞU GİBİ çağrılıyor.
Bu betiğin eklediği TEK şey iki yamadır — yasa tavanı ve dolum kuralı bayrağı.

════════ ARTEFAKT KORUMASI YAPISAL ════════
Referans modülün `SANDBOX`ı BU dizine yönlendirilir. İlk turda koşumlar `edg032b` dizinine
yazıyordu ve `git checkout` ile geri alınıyordu — sonradan-temizlik, önlem değil. Artık
tamamlanmış ölçümün artefaktına DOKUNULMASI yapısal olarak imkânsız.
"""
import contextlib
import importlib
import importlib.util
import json
import os
import pathlib
import sys

BURASI = pathlib.Path(__file__).resolve().parent
REPO = BURASI.parents[2]
REFERANS = REPO / "research" / "olcumler" / "edg032b_tamsatir_2026-08-13" / "olcum.py"
sys.path.insert(0, str(REPO))

TAVANLAR = [0.005, 0.01, 0.02, 0.03]              # kartın parameter_grid'i — DEĞİŞTİRİLEMEZ
DOLUM_KURALLARI = ["yalniz_acilis", "dinlenen_limit"]


def referans_modul():
    """Referans koşumu modül olarak yükler ve `SANDBOX`ını BU dizine çevirir.

    `__main__` bloğu `sys.argv`e bakıp iş yapıyor; modül olarak yüklerken argv geçici olarak
    boşaltılır ki içe aktarma bir koşum TETİKLEMESİN."""
    sp = importlib.util.spec_from_file_location("edg032b_ref", REFERANS)
    m = importlib.util.module_from_spec(sp)
    eski_argv = sys.argv
    sys.argv = [str(REFERANS)]
    try:
        sp.loader.exec_module(m)
    except SystemExit:                # `raise SystemExit(main())` deseni — içe aktarmada beklenir
        pass
    finally:
        sys.argv = eski_argv
    m.SANDBOX = BURASI                # ← artefakt koruması: referans dizine ASLA yazılmaz
    return m


@contextlib.contextmanager
def yasa_silahli(cap: float):
    """Limit bacağını `cap` tavanıyla silahlandırır — YALNIZ bu süreçte, yalnız bu blok boyunca.

    `state/goal.yaml` DEĞİŞMEZ (kartın kill kriteri). `limit_atr_mult` de kod varsayılanına (0.5)
    çekilir: canlıdaki 100.0 ATR bacağını yapısal olarak devre dışı bırakıyor ve o hâlde `cap`
    tek bağlayıcı olurdu — grid'in ATR ekseni sessizce ölürdü. Kart bacağı SİLAHLI istiyor."""
    from meridian import broker as B
    asil = B.entry_law
    yeni = {**asil(), "limit_atr_mult": B.ENTRY_LIMIT_ATR_MULT, "limit_pct_cap": cap}
    B.entry_law = lambda *a, **k: yeni
    try:
        yield yeni
    finally:
        B.entry_law = asil


def hucre_kos(ref, cap: float, kural: str, smoke: bool) -> dict:
    """Tek hücre: bayrağı kur → şasiyi ÇAĞIR → kol kimliğini DOĞRULA → özeti çıkar."""
    os.environ["MERIDIAN_DINLENEN_LIMIT"] = "1" if kural == "dinlenen_limit" else "0"
    from meridian import backtest as BT
    importlib.reload(BT)                          # bayrak modül düzeyinde okunuyor
    ref.backtest = BT                             # referans modül yeniden yüklenen BT'yi görsün
    if BT.DINLENEN_LIMIT != (kural == "dinlenen_limit"):
        raise AssertionError(f"bayrak kola uymadı: istenen={kural} DINLENEN_LIMIT={BT.DINLENEN_LIMIT}")

    # DAMGAYI YAKALA (inceleme Kritik 1 · 2026-08-17 ikinci vaka): `BacktestResult.dolum_kurali`
    # ALANI var ama REFERANS koşumun ürettiği `sonuc_kontrol.json` onu TAŞIMIYOR — yani kol
    # kimliği kapısı burada ATIL kalırdı ve tam da kaçınmak istediğimiz duruma düşerdik.
    # Referans koşumu DEĞİŞTİRMİYORUZ (dondurulmuş artefakt); `replay`i sarmalayıp damgayı
    # kaynağından, sonucun KENDİSİNDEN okuyoruz.
    yakalanan = {}
    asil_replay = BT.replay

    def _sarmal(*a, **k):
        r = asil_replay(*a, **k)
        yakalanan["damga"] = getattr(r, "dolum_kurali", None)
        # RET KİMLİĞİ (Ö-51b): Ö1'in paydası DİSTİNKT PLAN olmalı, red OLAYI değil.
        yakalanan["red_kimlik"] = getattr(r, "entry_reject_ids", None)
        return r

    BT.replay = _sarmal
    try:
        with yasa_silahli(cap) as yasa:
            ref.kosum("kontrol", smoke=smoke)     # ŞASİ: referansın kendi yolu, dokunulmadan
    finally:
        BT.replay = asil_replay

    sonuc_yol = (BURASI / "smoke" / "sonuc_kontrol_smoke.json") if smoke \
        else (BURASI / "sonuc_kontrol.json")
    d = json.load(open(sonuc_yol, encoding="utf-8"))

    # KOL KİMLİĞİ KAPISI (inceleme Kritik 1, 2026-08-17): damgasız bir koşumda "bayrak açıktı
    # ama vaka yoktu" ile "bayrak hiç uygulanmadı" AYIRT EDİLEMEZ. Damga tutmazsa hücre ölçüm
    # DEĞİLDİR ve koşum DURUR — sessizce geçilmez.
    damga = yakalanan.get("damga")
    if damga != kural:
        raise AssertionError(
            f"KOL KİMLİĞİ TUTMADI: beklenen={kural} damga={damga} — hücre ölçüm DEĞİL, koşum DURUR")

    islem = d.get("islem") or {}
    perf = d.get("performans") or {}
    rejects = dict(islem.get("entry_rejects") or {})
    # İŞLEM DEFTERİ de saklanır: H2/H3 kol FARKINDAN çıkar (özet alanlardan değil).
    defter_yol = (BURASI / "smoke" / "islemler_tam_kontrol_smoke.json") if smoke \
        else (BURASI / "islemler_tam_kontrol.json")
    defter = json.load(open(defter_yol, encoding="utf-8")) if defter_yol.exists() else []
    (BURASI / f"defter_cap{cap}_{kural}{'_smoke' if smoke else ''}.json").write_text(
        json.dumps(defter, ensure_ascii=False), encoding="utf-8")
    # hücre çıktısı ADIYLA saklanır (üzerine yazılmasın)
    (BURASI / f"hucre_cap{cap}_{kural}{'_smoke' if smoke else ''}.json").write_text(
        json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"limit_pct_cap": cap, "dolum_kurali": kural, "dolum_kurali_damgasi": damga,
            "yasa": {k: yasa[k] for k in ("limit_atr_mult", "limit_pct_cap", "version")},
            "entry_rejects": rejects,
            "entry_missed_limit": int(rejects.get("entry_missed_limit", 0)),
            # NET P&L KANONİK ALANDAN (2026-08-17 düzeltmesi): önce `islem.net_pnl` okunuyordu
            # ve o alan YOK — `None` geliyordu, yani H1 (monotonluk) ölçülemiyordu. Doğru yer
            # `performans.net_pnl_trades`. `net_pnl_equity` ile aynı çıkıyor; ikisi de yazılır ki
            # ayrışırlarsa GÖRÜNSÜN (ayrışma tek başına bir bulgudur).
            "net_pnl_trades": perf.get("net_pnl_trades"),
            "net_pnl_equity": perf.get("net_pnl_equity"),
            "islem_n": islem.get("n"),
            # Ö-51b: distinkt reddedilen plan sayısı (payda), olay sayısı DEĞİL
            "red_kimlik": {k: sorted(set(map(tuple, v)))
                           for k, v in (yakalanan.get("red_kimlik") or {}).items()},
            "defter": defter}


def main() -> int:
    smoke = "--smoke" in sys.argv
    ref = referans_modul()
    print(f"referans şasi yüklendi · SANDBOX={ref.SANDBOX.name} (referans dizine YAZILMAZ)")
    out = []
    for cap in TAVANLAR:
        for kural in DOLUM_KURALLARI:
            h = hucre_kos(ref, cap, kural, smoke)
            out.append(h)
            print(f"  cap={cap:<6} {kural:<15} damga={str(h['dolum_kurali_damgasi']):<15} "
                  f"missed_limit={h['entry_missed_limit']:<4} n={h['islem_n']} "
                  f"net_pnl={h['net_pnl_trades']}")
    # ── H2/H3: KOL FARKI ── dinlenen kolda DOLAN ama açılış kolunda KAÇAN işlemler.
    # Özet alanlardan çıkmaz; iki defterin FARKI gerekir. Kimlik = (ticker, giriş tarihi).
    def _kimlik(t):
        # Alan adları DEFTERDEN OKUNDU, tahmin edilmedi (2026-08-17): ilk hâl `entry_date`/`date`
        # deniyordu, hiçbiri yok — `r` de yoktu ve Ö2 sessizce None kalıyordu.
        return (t.get("ticker"), t.get("ts_open"))
    fark = {}
    for cap in TAVANLAR:
        a = next(h for h in out if h["limit_pct_cap"] == cap and h["dolum_kurali"] == "yalniz_acilis")
        b = next(h for h in out if h["limit_pct_cap"] == cap and h["dolum_kurali"] == "dinlenen_limit")
        ak = {_kimlik(t) for t in a["defter"]}
        yalniz_b = [t for t in b["defter"] if _kimlik(t) not in ak]
        rler = [float(t["r_multiple"]) for t in yalniz_b if t.get("r_multiple") is not None]
        fark[str(cap)] = {
            "kacan_sayisi_acilis_kolunda": a["entry_missed_limit"],
            "dinlenen_kolda_DOLAN_ek_islem": len(yalniz_b),
            # Ö1: kaçtı denilenlerin yüzde kaçı gerçekte doluyor
            # Ö1 HAM (GEÇERSİZ, tarihçe): payda RED OLAYI sayacı — birim uyuşmazlığı, %100 aşabilir
            "O1_HAM_GECERSIZ_olay_paydali": (round(100.0 * len(yalniz_b) / a["entry_missed_limit"], 1)
                                if a["entry_missed_limit"] else None),
            # Ö1 DÜZGÜN (Ö-51b): payda DİSTİNKT REDDEDİLEN PLAN
            "O1_distinkt_plan_paydasi": len(set(map(tuple, (a.get("red_kimlik") or {}).get("entry_missed_limit", [])))),
            "O1_olculemedi_nedeni": (None if a["entry_missed_limit"]
                                     else "açılış kolunda HİÇ kaçan yok — payda sıfır, oran TANIMSIZ"),
            # Ö2: o işlemlerin ort-R'si — "kaçanlar sistematik KAZANAN" iddiası buradan sınanır
            "O2_ek_islem_ort_r": (round(sum(rler) / len(rler), 4) if rler else None),
            "O2_n": len(rler),
            "O2_olculemedi_nedeni": None if rler else "ek işlem yok ya da r_multiple boş — ort-R ÖLÇÜLEMEDİ",
            # H1 girdisi
            "net_pnl_yalniz_acilis": a["net_pnl_trades"],
            "net_pnl_dinlenen": b["net_pnl_trades"],
            "delta_pnl": (round(b["net_pnl_trades"] - a["net_pnl_trades"], 2)
                          if None not in (a["net_pnl_trades"], b["net_pnl_trades"]) else None)}
    print("── KOL FARKI ──")
    for c, f in fark.items():
        print(f"  cap={c:<6} kaçan={f['kacan_sayisi_acilis_kolunda']} → dolan={f['dinlenen_kolda_DOLAN_ek_islem']} "
              f"Ö1ham={f['O1_HAM_GECERSIZ_olay_paydali']}% "
              f"distinkt_plan={f['O1_distinkt_plan_paydasi']} "
              f"Ö2ort-R={f['O2_ek_islem_ort_r']} ΔP&L={f['delta_pnl']}")

    yol = BURASI / f"sonuc_grid{'_smoke' if smoke else ''}.json"
    json.dump({"kart": "EXE-2026-006", "smoke": smoke, "K_hucre": len(out),
               "tavanlar": TAVANLAR, "dolum_kurallari": DOLUM_KURALLARI,
               "kol_farki": fark,
               "hucreler": [{k: v for k, v in h.items() if k != "defter"} for h in out]},
              open(yol, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"yazıldı: {yol} · K={len(out)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
