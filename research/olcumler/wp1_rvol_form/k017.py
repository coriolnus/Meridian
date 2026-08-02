"""EDG-2026-017 · rvol FORM REVİZYONU — SALT-ÖLÇÜM, KUM HAVUZU.

Kart: research/cards/EDG-2026-017-rvol-form-revizyonu.yaml (status: registered).
KART DIŞINA ÖLÇÜM YOK · KARTA DOKUNULMAZ · EŞİK SONRADAN DEĞİŞMEZ · HÜKÜM ROL-1'DE.

KATMANLAR (kart parameter_grid, K+=2 — ÇARPILARAK):
  1) rvol25_bolge_fazlasi                  — rvol20>=2.5 bölgesi, aynı-gün EVREN taban fazlası
  2) rvol25_artik_rvol_surekli_kontrollu   — sürekli rvol20 DESİL kontrolünde artık katkı
                                             (kova-tabanı + artık-IC; EDG-007/016 şablonu)

Ufuk 10/20 kartın `horizon` alanıdır, K çarpanı DEĞİLDİR (EDG-013/016 ile aynı okuma).
CI'sı OLMAYAN her tablo TANI'dır ve K harcamaz.
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

import ortak017 as O
import pk017 as PK

HORIZONS = (10, 20)          # kart: ileri getiri 10/20g
RVOL_ESIK = 2.5              # kart: rvol>=2.5 bölgesi — üçgenin (strategy.rvol_band_score) 0'ladığı sağ kol
DESIL = 10                   # kart: "sürekli-rvol20 DESİL-kontrollü artık"
KOVA_MIN = 2                 # kova-içi merkezleme için asgari üye (n=1'de merkezleme tanım gereği 0)
# Alt-dönem sınırları ÖLÇÜMDEN ÖNCE sabitlendi (betimleyici; grid'e dahil DEĞİL — kart notu).
DONEMLER = [("...-2014", None, "2014-12-31"), ("2015-2018", "2015-01-01", "2018-12-31"),
            ("2019-2022", "2019-01-01", "2022-12-31"), ("2023-...", "2023-01-01", None)]


def _bolge_maskesi(x: np.ndarray) -> np.ndarray:
    return np.isfinite(x) & (x >= RVOL_ESIK)


def net(blok, c):
    """Maliyet bir SABİT olduğundan CI aynı sabitle ötelenir (bootstrap yeniden koşulmaz —
    cebirsel özdeş; EDG-016 ile birebir)."""
    if blok.get("ort") is None or not blok.get("ci"):
        return {"brut": blok.get("ort"), "net": None, "ci": None,
                "neden": blok.get("neden") or "brüt ölçülemedi"}
    return {"brut": blok["ort"], "maliyet": O._r6(c), "net": O._r6(blok["ort"] - c),
            "ci": {"lo": O._r6(blok["ci"]["lo"] - c), "hi": O._r6(blok["ci"]["hi"] - c),
                   "seviye": 0.95},
            "net_pozitif_anlamli": bool(blok["ci"]["lo"] - c > 0),
            "net_ort_pozitif": bool(blok["ort"] - c > 0), "neden": None}


def main() -> None:
    print("== 017: barlar ==", flush=True)
    pan, bar_acc = O.bars_cached()
    print(f"   {bar_acc['yuklendi']}/{bar_acc['istenen']} sembol", flush=True)

    sonuc = {
        "kart": "EDG-2026-017", "aile": "rvol_form_revizyonu",
        "olcum_tarihi": pd.Timestamp.now("UTC").isoformat(),
        "kum_havuzu": str(O.KLASOR), "calisma_dizini": str(O.CALISMA),
        "rol": "ölçüm ajanı — HÜKÜM VERMEZ, KARTA DOKUNMAZ; kill/success karşılıkları VERİ olarak "
               "yazılır, hükmü Rol-1 işler",
        "DURUM": None,
    }

    # ---------- (0) POZİTİF KONTROL — İLK KOŞAN İŞ (kart guard: tutmazsa ÖLÇÜM DURUR) ----------
    print("== 017: pozitif kontrol (İLK) ==", flush=True)
    pkc, PKD = PK.pozitif_kontrol(pan)
    print(f"   çivi={pkc['civi_olculen']} hedef={pkc['civi_hedef']} → GEÇTİ={pkc['GECTI']}",
          flush=True)
    if not pkc["GECTI"]:
        sonuc["DURUM"] = "DURDU — POZİTİF KONTROL BAŞARISIZ"
        sonuc["bekciler"] = {"pozitif_kontrol": pkc}
        sonuc["neden"] = ("Kart guard'ı: 'ham rvol20 @20 IC ≈0.0642 çivisi sandbox'ta yeniden "
                          "üretilir (üretilemezse ölçüm DURUR)'. Çivi tutmadı; boru hattı geçersiz "
                          "sayıldı ve HİÇBİR grid hücresi ölçülmedi.")
        O.json_yaz(O.KLASOR / "sonuc_017.json", sonuc)
        print("!! POZİTİF KONTROL DÜŞTÜ — ölçüm durdu", flush=True)
        return

    pk4 = PK.pk4(pan, PKD)
    pk5 = PK.pk5(pan)
    print(f"   PK4 geçti={pk4['gecti']} · PK5-C={pk5['C_hizli_ortalama']['gecti']} "
          f"PK5-E={pk5['E_hizli_spearman']['gecti']}", flush=True)

    # ---------------- PANEL ----------------
    print("== 017: panel ==", flush=True)
    takvim = O.ortak_takvim(pan)
    gun_idx = {d: i for i, d in enumerate(takvim)}
    sym_ad = sorted(pan)
    sym_idx = {s: i for i, s in enumerate(sym_ad)}
    parts = []
    for s in sym_ad:
        v = pan[s]
        n = len(v["dates"])
        row = {"date": v["dates"], "sym": np.full(n, sym_idx[s], np.int32),
               "gun": np.array([gun_idx[d] for d in v["dates"]], np.int32),
               "rvol20": v["rvol20"], "rvol20_medyan": v["rvol20_medyan"],
               "close": v["close"], "volume": v["volume"]}
        for h in HORIZONS:
            row[f"fwd{h}"] = v[f"fwd{h}"]
        parts.append(pd.DataFrame(row))
    D = pd.concat(parts, ignore_index=True)
    del parts

    # ---------------- kesit kapısı ----------------
    rv_ok = D["rvol20"].notna()
    kesit = D.loc[rv_ok].groupby("gun").size()
    kullanilan_gun = set(kesit[kesit >= O.MIN_KESIT].index.tolist())
    D["kesit_ok"] = D["gun"].isin(kullanilan_gun)
    V = D[rv_ok & D["kesit_ok"]].copy()
    V["bolge"] = _bolge_maskesi(V["rvol20"].to_numpy(float))
    kesit_k = kesit[kesit >= O.MIN_KESIT]

    sonuc["kart_metni_uygulamasi"] = {
        "universe": "full_251 — KAPSAM BEYANLI: bar önbelleğinde dosyası olan ve şablon asgari "
                    "uzunluğunu (TREND_TEMPLATE_WARMUP+65) geçen semboller; düşenler "
                    "bar_muhasebesi'nde sayılı.",
        "veri_yolu": "state/bars (SALT-OKUNUR) → dat.sanitize_bars (takvim kapısı, hayalet seans + "
                     "bölünme-karantinası) → dat.measurement_bars (bars_integrity defteri: "
                     "GÜVENSİZ DÖNEM DIŞLANIR) → dat.integrity_safe_start (HESAPLANAN ikinci yol). "
                     "wp2_olcum dalgasıyla BİREBİR aynı yol; ölçüm ÇİVİSİ bu yolda kalibre.",
        "rvol20_tanimi": "ind.rvol20 = hacim(t) / SMA20(hacim) — CANLI TANIM (indicators.py), "
                         "kartın 'canlı tanımla BİREBİR' niteleyicisi. KART METNİ AYNI SATIRDA "
                         "'medyan20(hacim)' yazıyor; iki tanım AYNI DEĞİL. Ders#2 (eşik dilbilgisi) "
                         "gereği belirsizlik BEYAN EDİLİR ve muhafazakâr okunur: hüküm taşıyan "
                         "sayılar canlı (SMA) tanımıyla üretildi — çünkü (a) kart o dalı 'canlı "
                         "tanımla BİREBİR (indicators.py kaynak)' diye niteliyor, (b) EDG-002'nin "
                         "2.5 kenarı ve pozitif-kontrol çivisi O tanımla ölçüldü. MEDYAN varyantı "
                         "TANI olarak ayrıca verilir (CI YOK → K harcamaz).",
        "bolge": f"rvol20 >= {RVOL_ESIK} — FORM ŞARTSIZ (üçgen/bant dönüşümü UYGULANMADI); "
                 "strategy.rvol_band_score'un 0'ladığı sağ kol.",
        "kesit": f"gözlem günü, o gün rvol20 tanımlı sembol sayısı >= {O.MIN_KESIT}; TEK KURAL, "
                 "iki katmana da aynı uygulanır (aksi hâlde artık-katkı farkı kapsam farkıyla "
                 "karışırdı).",
        "taban": "aynı-gün EVREN ortalaması (ders#3: ham-getiri YASAK). İKİ SÜRÜM: (a) TEMİZ taban "
                 "— ders#4/temiz_taban: olay-penceresi (h, h) İÇİNDEKİ satırlar tabandan DÜŞÜRÜLÜR "
                 "ve kirlilik oranı raporlanır; HÜKÜM TAŞIYAN sürüm budur (kart guard'ı zorunlu "
                 "kılıyor). (b) HAM taban — EDG-013/016 ile kıyaslanabilirlik için, temizlik YOK.",
        "olay_tanimi_ders4": f"olay = o sembolde rvol20>={RVOL_ESIK} olan seans; pencere (h, h) "
                             "SEANS ORDİNALİ birimindedir (takvim günü değil) — ileri getiri h BAR "
                             "olduğu için kirlilik 'olayın h-barlık penceresi bu satırınkiyle "
                             "örtüşüyor mu' sorusudur. rvol20'si TANIMSIZ satır (ilk 19 bar) olay "
                             "SAYILMAZ (olay ölçülemedi) ve tabana temiz girer — beyanlı.",
        "katman_2_kontrol": f"gün bazlı kesitte sürekli rvol20'nin DESİLİ ({DESIL} kova). "
                            "A1: bölgenin AYNI-GÜN AYNI-DESİL leave-one-out taban fazlası. "
                            "A2 (EDG-007): desil İÇİNDE bölge vs bölge-dışı farkı. "
                            "B: gün bazlı kesit artığı e = 1{rvol>=2.5} − desil-içi ortalaması "
                            "(desil kuklalarına OLS ile ÖZDEŞ) → havuzlanmış Spearman(e, FAZLA).",
        "ci": f"{O.BLOCK} ardışık gözlem günü blok-bootstrap, %95; ortalama {O.BOOT} / IC "
              f"{O.BOOT_IC} tekrar",
        "maliyet": f"kart cost_model: {O.MALIYET_BPS}bps sabit + {2*O.MALIYET_BPS}bps duyarlılık "
                   "satırı. Kill#3 kartın modeliyle (10bps) okunur; 20bps BEYANLI duyarlılıktır.",
        "K_beyani": "Kart grid'i 2 katman → K+=2 (ÇARPILARAK; grid ekseni tek: `katman`). Ufuk "
                    "10/20 `horizon` alanıdır. Alt-dönem, desil dağılımı, bölge-içi bant, medyan "
                    "tanım varyantı ve HAM-taban okumaları TANI'dır (CI yok / kart bacağı değil).",
        "hayatta_kalma_serhi": "Evren `data.REPLAY_UNIVERSE` = bugün yaşayan likit isimler; "
                              "delist edilmiş adlar YOK ve tarihsel üyelik nokta-zamanlı DEĞİL. "
                              "Kartın kalıcı şerhi (EDG-016 emsali): POZİTİF bir bulguyu YUKARI "
                              "çarpıtır; büyüklüğü bu veriyle ölçülemez.",
    }
    sonuc["bar_muhasebesi"] = {k: v for k, v in bar_acc.items() if k != "kisa_semboller"}
    sonuc["bar_muhasebesi"]["takvim_reddedilen"] = len(bar_acc["takvim_reddedilen"])
    sonuc["bar_muhasebesi"]["kisa_semboller"] = bar_acc["kisa_semboller"]
    sonuc["kesit_muhasebesi"] = {
        "gozlem_gunu_toplam": int(D["gun"].nunique()),
        "kesit_yeterli_gun": int(len(kesit_k)), "min_kesit": O.MIN_KESIT,
        "kesit_buyuklugu": {"medyan": O._r6(kesit_k.median()), "min": int(kesit_k.min()),
                            "maks": int(kesit_k.max())},
        "tarih_araligi": [str(V["date"].min()), str(V["date"].max())],
        "n_satir_kesit": int(len(V)), "n_sembol": int(V["sym"].nunique()),
        "n_satir_panel_tum": int(len(D)),
        "rvol20_dagilimi": {str(q): O._r6(V["rvol20"].quantile(q))
                            for q in (0.01, 0.25, 0.5, 0.75, 0.95, 0.99)},
        "bolge_pay_pct": O._r6(100.0 * float(V["bolge"].mean())),
        "bolge_n": int(V["bolge"].sum()),
    }

    # ---------------- TABANLAR (ham + temiz, ders#3/#4) ----------------
    print("== 017: tabanlar (ders#3 + ders#4 temiz kıyas) ==", flush=True)
    n_gun = len(takvim)
    sym_kod_all = D["sym"].to_numpy(np.int64)
    gun_kod_all = D["gun"].to_numpy(np.int64)
    olay_all = _bolge_maskesi(D["rvol20"].to_numpy(float))
    tabanlar, ders4 = {}, {}
    for h in HORIZONS:
        y = D[f"fwd{h}"].to_numpy(float)
        fin = np.isfinite(y)
        # (a) HAM taban — EDG-013/016 ile birebir
        s = np.bincount(gun_kod_all[fin], weights=y[fin], minlength=n_gun)
        c = np.bincount(gun_kod_all[fin], minlength=n_gun).astype(float)
        with np.errstate(divide="ignore", invalid="ignore"):
            ham_taban = np.where(c > 0, s / c, np.nan)
        # (b) TEMİZ taban — olay penceresi (h, h) DIŞI satırlar
        temiz = O.temiz_maske(sym_kod_all, gun_kod_all, olay_all, h)
        tem_taban, c_tem = O.temiz_evren_tabani(gun_kod_all[fin], y[fin], temiz[fin], n_gun)
        tabanlar[h] = {"ham": ham_taban, "temiz": tem_taban, "n_ham": c, "n_temiz": c_tem}
        olculebilir = int(fin.sum())
        kirli = int((fin & ~temiz).sum())
        ders4[str(h)] = {
            "pencere": {"once": h, "sonra": h}, "gun_birimi": "sira/bar indeksi (SEANS ORDİNALİ)",
            "n_toplam_taban_satiri": olculebilir,
            "n_kirli": kirli, "n_temiz": olculebilir - kirli,
            "kirlilik_orani": O._r6(kirli / olculebilir) if olculebilir else None,
            "gun_sayisi_temiz_taban_YOK": int(((c > 0) & (c_tem == 0)).sum()),
            "temiz_taban_medyan_uye": O._r6(np.median(c_tem[c_tem > 0])) if (c_tem > 0).any() else None,
            "ham_taban_medyan_uye": O._r6(np.median(c[c > 0])) if (c > 0).any() else None,
            "beyan": "kirlilik_orani = olay-penceresi-İÇİ taban satırı / ölçülebilir taban satırı. "
                     "EAP dersi: temizlenmemiş kıyas etkiyi SIKIŞTIRIR (olayı olayla kıyaslar).",
        }
    sonuc["ders4_kiyas_temizligi"] = ders4

    # ---------------- I. KATMAN — rvol25_bolge_fazlasi ----------------
    print("== 017: katman 1 (rvol25_bolge_fazlasi) ==", flush=True)
    sub = V[V["bolge"]]
    kat1 = {"n_sembol_gun": int(len(sub)), "n_gun": int(sub["gun"].nunique()),
            "n_sembol": int(sub["sym"].nunique()),
            "rvol20_medyan_bolge": O._r6(sub["rvol20"].median()),
            "rvol20_ort_bolge": O._r6(sub["rvol20"].mean()),
            "rvol20_p95_bolge": O._r6(sub["rvol20"].quantile(0.95)),
            "ufuklar": {}}
    kat1_kayit = {}
    for h in HORIZONS:
        s2 = sub[["date", "gun", f"fwd{h}"]].dropna()
        y = s2[f"fwd{h}"].to_numpy(float)
        gk = s2["gun"].to_numpy(np.int64)
        dts = s2["date"].to_numpy()
        bh = tabanlar[h]["ham"][gk]
        bt = tabanlar[h]["temiz"][gk]
        okh, okt = np.isfinite(bh), np.isfinite(bt)
        kat1["ufuklar"][str(h)] = {
            "ham_getiri_TANI_kart_olcutu_DEGIL": O.mean_with_ci(y, dts),
            "evren_fazlasi_TEMIZ_taban_HUKUM": O.mean_with_ci((y - bt)[okt], dts[okt]),
            "evren_fazlasi_HAM_taban_kiyas": O.mean_with_ci((y - bh)[okh], dts[okh]),
            "temiz_taban_yok_dusen_satir": int((~okt).sum()),
        }
        kat1_kayit[h] = ((y - bt)[okt], dts[okt])
    sonuc["i_katman_rvol25_bolge_fazlasi"] = kat1

    # ---------------- II. KATMAN — ARTIK (sürekli rvol20 DESİL kontrolü) ----------------
    print("== 017: katman 2 (desil-kontrollü artık) ==", flush=True)
    V["rvol_pct"] = V.groupby("gun")["rvol20"].rank(pct=True, method="first")
    V["desil"] = np.clip((V["rvol_pct"].to_numpy(float) * DESIL).astype(int), 0, DESIL - 1)
    art = {"kontrol": f"gün bazlı kesitte sürekli rvol20 DESİLİ ({DESIL} kova)"}
    dag = V.groupby("desil")["bolge"].agg(["size", "sum"])
    art["bolge_desil_dagilimi"] = {
        "aciklama": "bölge (rvol>=2.5) satırlarının kontrol desillerine dağılımı — kontrolün "
                    "GERÇEKTEN çalışıp çalışmadığının ön koşulu: bölge tek bir desilde toplanıyorsa "
                    "kontrol o desilin İÇİNDE ayrım arıyor demektir (ve bunu söylemek zorundayız).",
        "desiller": {str(int(k)): {"n": int(r["size"]), "bolge_n": int(r["sum"]),
                                   "bolge_pay_pct": O._r6(100.0 * r["sum"] / r["size"])}
                     for k, r in dag.iterrows()}}

    # --- A1: KAYITLI bölge, taban = AYNI-GÜN AYNI-DESİL leave-one-out ---
    a1 = {"tanim": "KAYITLI dilim (rvol>=2.5 bölgesi) — taban EVREN yerine AYNI-GÜN AYNI-DESİL "
                   "leave-one-out ortalaması (gözlemin kendisi tabana girmez). Katman 1 ile TEK "
                   "farkı tabandır; aradaki düşüş doğrudan sürekli-rvol kontrolünün bedelidir.",
          "ufuklar": {}}
    a1_kayit = {}
    for h in HORIZONS:
        g = V[["date", "gun", "desil", "bolge", f"fwd{h}"]].dropna(subset=[f"fwd{h}"]).copy()
        grp = g.groupby(["gun", "desil"])[f"fwd{h}"]
        n_k = grp.transform("size").to_numpy(float)
        s_k = grp.transform("sum").to_numpy(float)
        yv = g[f"fwd{h}"].to_numpy(float)
        with np.errstate(divide="ignore", invalid="ignore"):
            loo = (s_k - yv) / (n_k - 1.0)
            ici = s_k / n_k
        yeter = n_k >= KOVA_MIN
        m = g["bolge"].to_numpy(bool) & yeter & np.isfinite(loo)
        a1["ufuklar"][str(h)] = {
            "kova_yetersiz_dusen_satir": int((~yeter & g["bolge"].to_numpy(bool)).sum()),
            "loo_desil_fazlasi": O.mean_with_ci(yv[m] - loo[m], g["date"].to_numpy()[m]),
            "kendini_iceren_desil_fazlasi_ort_CI_YOK": O._r6(float(np.mean(
                (yv - ici)[g["bolge"].to_numpy(bool) & yeter]))),
        }
        a1_kayit[h] = (yv[m] - loo[m], g["date"].to_numpy()[m])
    art["A1_desil_tabanli_bolge_fazlasi"] = a1

    # --- A2: EDG-007 şablonu — desil İÇİNDE bölge vs bölge-dışı ---
    a2 = {"tanim": "EDG-007 çift-sıralama şablonu: her rvol DESİLİNDE bölge (rvol>=2.5) üyeleri vs "
                   "aynı desilin bölge-dışı üyeleri; hücre farkları + desil-içi merkezlenmiş "
                   "havuzlanmış yayılım.", "ufuklar": {}}
    for h in HORIZONS:
        g = V[["date", "gun", "desil", "bolge", f"fwd{h}"]].dropna(subset=[f"fwd{h}"]).copy()
        grp = g.groupby(["gun", "desil"])[f"fwd{h}"]
        n_k = grp.transform("size").to_numpy(float)
        s_k = grp.transform("sum").to_numpy(float)
        yv = g[f"fwd{h}"].to_numpy(float)
        with np.errstate(divide="ignore", invalid="ignore"):
            loo = (s_k - yv) / (n_k - 1.0)
        yeter = n_k >= KOVA_MIN
        g = g.assign(_merkezli=yv - loo, _yeter=yeter)
        hucre = {}
        for dv, gg in g[g["_yeter"]].groupby("desil"):
            hi = gg[gg["bolge"]]
            lo = gg[~gg["bolge"]]
            if len(hi) < O.MIN_SLICE or len(lo) < O.MIN_SLICE:
                hucre[str(int(dv))] = {"n_bolge": int(len(hi)), "n_bolge_disi": int(len(lo)),
                                       "fark": None, "ci": None, "anlamli": None,
                                       "neden": f"dilim < {O.MIN_SLICE}"}
                continue
            r = O.fark_with_ci(hi[f"fwd{h}"].to_numpy(float), hi["date"].to_numpy(),
                               lo[f"fwd{h}"].to_numpy(float), lo["date"].to_numpy())
            r["ort_bolge"] = O._r6(hi[f"fwd{h}"].mean())
            r["ort_bolge_disi"] = O._r6(lo[f"fwd{h}"].mean())
            hucre[str(int(dv))] = r
        gy = g[g["_yeter"]]
        hi, lo = gy[gy["bolge"]], gy[~gy["bolge"]]
        hav = O.fark_with_ci(hi["_merkezli"].to_numpy(float), hi["date"].to_numpy(),
                             lo["_merkezli"].to_numpy(float), lo["date"].to_numpy())
        hav["aciklama"] = "desil-içi (leave-one-out) MERKEZLENMİŞ getirilerde bölge − bölge-dışı: " \
                          "desil bileşimi farkından arınmış havuzlanmış yayılım"
        a2["ufuklar"][str(h)] = {"desiller": hucre, "havuzlanmis": hav}
    art["A2_edg007_desil_ici_bolge_eksi_kalan"] = a2

    # --- B: ARTIK-IC ---
    print("== 017: katman 2b (artık-IC) ==", flush=True)
    x = V["bolge"].to_numpy(float)
    gk = V["gun"].to_numpy(np.int64)
    dk = V["desil"].to_numpy(np.int64)
    anahtar = gk * DESIL + dk
    uq, inv = np.unique(anahtar, return_inverse=True)
    m_k = np.bincount(inv, weights=x) / np.bincount(inv)
    e_desil = x - m_k[inv]                      # desil kuklalarına gün-bazlı OLS artığıyla ÖZDEŞ
    V["artik_desil"] = e_desil

    # robustluk: EDG-016 tarzı SÜREKLİ pctrank OLS artığı (gün bazlı)
    e_sur = np.full(len(V), np.nan)
    z = V["rvol_pct"].to_numpy(float)
    _, ginv = np.unique(gk, return_inverse=True)
    order = np.argsort(ginv, kind="stable")
    cnt = np.bincount(ginv)
    start = np.concatenate([[0], np.cumsum(cnt)[:-1]])
    tekil = 0
    for gi in range(len(cnt)):
        ii = order[start[gi]:start[gi] + cnt[gi]]
        if len(ii) < 3:
            tekil += 1
            continue
        A = np.column_stack([np.ones(len(ii)), z[ii]])
        try:
            beta, *_ = np.linalg.lstsq(A, x[ii], rcond=None)
        except np.linalg.LinAlgError:
            tekil += 1
            continue
        e_sur[ii] = x[ii] - A @ beta
    V["artik_surekli"] = e_sur

    # ortogonallik bekçisi
    okv = V[["gun", "artik_desil", "desil", "rvol_pct"]].dropna()
    c_des, m0 = [], []
    for _, gg in okv.groupby("gun"):
        if len(gg) < 10:
            continue
        a = gg["artik_desil"].to_numpy()
        m0.append(abs(a.mean()))
        # desil kuklalarına diklik: her desil içinde artığın ortalaması 0 olmalı
        c_des.append(float(np.abs(gg.groupby("desil")["artik_desil"].mean()).max()))
    ortog = {"tanim": "gün bazlı desil-kukla artığı: HER DESİL İÇİNDE ortalaması 0 olmalı "
                      "(ve dolayısıyla gün-içi ortalaması da 0); değilse artıklaştırma yapılmamıştır",
             "maks_desil_ici_ortalama": O._r6(max(c_des)), "maks_gun_ici_ortalama": O._r6(max(m0)),
             "gecti": bool(max(c_des) < 1e-9 and max(m0) < 1e-9),
             "tekil_gun_surekli_yol": int(tekil)}

    icb = {"tanim": "havuzlanmış Spearman IC. HEADLINE: DESİL artığı ↔ TEMİZ-taban FAZLA getirisi. "
                    "Artık gün-içinde zaten merkezlidir; ham getiriyle havuzlanmış IC gün-düzeyi "
                    "varyansla sulandırılırdı (ham okuma TANI olarak var).",
           "beraberlik_serhi": "Bölge üyesi OLMAYAN desillerde artık TAM SIFIRDIR (o desilde "
                               "gösterge sabittir) → havuzlanmış Spearman'da büyük bir beraberlik "
                               "kütlesi oluşur ve IC'yi SIFIRA doğru seyreltir. Bu yüzden aynı IC "
                               "bir de YALNIZ bölge üyesi bulunan desillerde raporlanır.",
           "ufuklar": {}}
    bolge_desilleri = sorted(int(k) for k, r in dag.iterrows() if r["sum"] > 0)
    for h in HORIZONS:
        g = V[["date", "gun", "desil", "artik_desil", "artik_surekli", "rvol20", f"fwd{h}"]] \
            .dropna(subset=[f"fwd{h}", "artik_desil"]).copy()
        bt = tabanlar[h]["temiz"][g["gun"].to_numpy(np.int64)]
        ok = np.isfinite(bt)
        g = g[ok].copy()
        fz = g[f"fwd{h}"].to_numpy(float) - bt[ok]
        dts = g["date"].to_numpy()
        sel = g["desil"].isin(bolge_desilleri).to_numpy()
        gs = g.dropna(subset=["artik_surekli"])
        bts = tabanlar[h]["temiz"][gs["gun"].to_numpy(np.int64)]
        icb["ufuklar"][str(h)] = {
            "artik_desil_ic_fazla_HUKUM": O.ic_hizli(g["artik_desil"].to_numpy(float), fz, dts),
            "artik_desil_ic_fazla_YALNIZ_BOLGELI_DESILLER": O.ic_hizli(
                g.loc[sel, "artik_desil"].to_numpy(float), fz[sel], dts[sel]),
            "artik_surekli_pctrank_ic_fazla_ROBUSTLUK": O.ic_hizli(
                gs["artik_surekli"].to_numpy(float),
                gs[f"fwd{h}"].to_numpy(float) - bts, gs["date"].to_numpy()),
            "ham_rvol20_ic_fazla_TANI": O.ic_hizli(g["rvol20"].to_numpy(float), fz, dts),
            "artik_desil_ic_HAM_getiri_TANI_CI_YOK": O.ic_hizli(
                g["artik_desil"].to_numpy(float), g[f"fwd{h}"].to_numpy(float), dts, ci=False),
        }
    art["B_artik_ic"] = icb
    art["artik_ortogonallik_bekcisi"] = ortog
    sonuc["ii_katman_rvol25_artik_rvol_surekli_kontrollu"] = art

    # ---------------- III. MALİYET-SONRASI NET (kill#3) ----------------
    print("== 017: maliyet-sonrası net ==", flush=True)
    c1_ = O.MALIYET_BPS / 10000.0
    c2_ = 2 * O.MALIYET_BPS / 10000.0
    mal = {"tanim": "Maliyet SABİT olduğundan CI aynı sabitle ötelenir (cebirsel özdeş). Kart "
                    f"modeli {O.MALIYET_BPS}bps; {2*O.MALIYET_BPS}bps BEYANLI duyarlılıktır.",
           "kart_modeli_bps": O.MALIYET_BPS, "duyarlilik_bps": 2 * O.MALIYET_BPS, "ufuklar": {}}
    for h in HORIZONS:
        b1 = kat1["ufuklar"][str(h)]["evren_fazlasi_TEMIZ_taban_HUKUM"]
        b2 = a1["ufuklar"][str(h)]["loo_desil_fazlasi"]
        mal["ufuklar"][str(h)] = {
            "katman1_evren_fazlasi": {"kart_modeli_10bps": net(b1, c1_),
                                      "duyarlilik_20bps": net(b1, c2_)},
            "katman2_desil_fazlasi_A1": {"kart_modeli_10bps": net(b2, c1_),
                                         "duyarlilik_20bps": net(b2, c2_)},
        }
    V["dolar_hacim"] = V["volume"] * V["close"]
    mal["spread_daralmasi_beyan_notu"] = {
        "kart_metni": "cost_model: 'yüksek-rvol günü spread daralması beyan-notu'",
        "beyan": "SABİT bps maliyet modeli, yüksek-rvol günlerinde gerçekleşen spread DARALMASINI "
                 "taşımaz; yani net rakam bu yönde MUHAFAZAKÂRDIR. Bu depoda gerçek spread serisi "
                 "YOK → daralmanın büyüklüğü ÖLÇÜLEMEDİ (uydurma yasağı). Aşağıdaki dolar-hacim "
                 "kıyası yalnız BETİMLEYİCİ dolaylı kanıttır, CI yoktur ve kart bacağı DEĞİLDİR.",
        "spread_serisi": None,
        "spread_serisi_neden": "depoda gün-içi kotasyon/spread verisi yok (yalnız günlük OHLCV)",
        "bolge_medyan_dolar_hacim": O._r6(V.loc[V["bolge"], "dolar_hacim"].median()),
        "evren_medyan_dolar_hacim": O._r6(V["dolar_hacim"].median()),
        "oran": O._r6(V.loc[V["bolge"], "dolar_hacim"].median() / V["dolar_hacim"].median()),
    }
    sonuc["iii_maliyet_sonrasi_net"] = mal

    # ---------------- IV. ALT-DÖNEM KARARLILIK (BETİMLEYİCİ — kart: grid'e dahil DEĞİL) ----------
    print("== 017: alt-dönem kararlılık ==", flush=True)
    alt = {"not": "BETİMLEYİCİ — kart notu: 'alt-dönem kararlılık satırı rapora eklenir (grid'e "
                  "dahil değil, betimleyici)'. CI blok-bootstrap ile verilir ama HÜKÜM TAŞIMAZ ve "
                  "K harcamaz: dönem sınırları ölçümden ÖNCE sabitlendi ve hiçbir dönem 'seçilmedi'.",
           "hayalet_2018_serhi": "s1_retro (BT-2) tespiti: 2018-11-22 hayalet seansı ve genel olarak "
                                 "UZUN GEÇMİŞ artefaktları O turda AKLANMADI. Bu turda takvim kapısı "
                                 "(sanitize_bars) hayalet seansları düşürür — bar_muhasebesi."
                                 "hayalet_dusen sayısı raporda durur — ama '2018 aklandı' DENMEZ; "
                                 "alt-dönem satırı tam da bu yüzden vardır.",
           "donemler": {}}
    for ad, d0, d1 in DONEMLER:
        m = pd.Series(True, index=sub.index)
        if d0:
            m &= sub["date"] >= d0
        if d1:
            m &= sub["date"] <= d1
        ss = sub[m]
        rec = {"baslangic": d0, "bitis": d1, "n": int(len(ss)), "ufuklar": {}}
        for h in HORIZONS:
            s2 = ss[["date", "gun", f"fwd{h}"]].dropna()
            if len(s2) < O.MIN_SLICE:
                rec["ufuklar"][str(h)] = {"n": int(len(s2)), "ort": None,
                                          "neden": f"n<{O.MIN_SLICE}"}
                continue
            bt = tabanlar[h]["temiz"][s2["gun"].to_numpy(np.int64)]
            ok = np.isfinite(bt)
            rec["ufuklar"][str(h)] = O.mean_with_ci(
                (s2[f"fwd{h}"].to_numpy(float) - bt)[ok], s2["date"].to_numpy()[ok])
        alt["donemler"][ad] = rec
    # 2018 takvim yılı HARİÇ okuma (hayalet şerhinin doğrudan karşılığı)
    ss = sub[~sub["date"].astype(str).str.startswith("2018")]
    haric = {"tanim": "2018 takvim yılı satırları DIŞLANARAK aynı katman-1 okuması", "ufuklar": {}}
    for h in HORIZONS:
        s2 = ss[["date", "gun", f"fwd{h}"]].dropna()
        bt = tabanlar[h]["temiz"][s2["gun"].to_numpy(np.int64)]
        ok = np.isfinite(bt)
        haric["ufuklar"][str(h)] = O.mean_with_ci(
            (s2[f"fwd{h}"].to_numpy(float) - bt)[ok], s2["date"].to_numpy()[ok])
    alt["2018_haric"] = haric
    sonuc["iv_alt_donem_kararlilik"] = alt

    # ---------------- V. TANI (K harcanmaz) ----------------
    print("== 017: tanı ==", flush=True)
    tani = {"not": "TANI — kart grid'inde OLMAYAN kesitler; CI'sızlar hüküm taşımaz."}
    # (1) bölge içi bant tablosu (2.5-3 / 3-4 / 4+) + EDG-002 bant tablosunun panel karşılığı
    kenar = [(0.0, 0.8), (0.8, 1.5), (1.5, 2.0), (2.0, 2.5), (2.5, 3.0), (3.0, 4.0), (4.0, 1e9)]
    bant = {}
    for h in HORIZONS:
        g = V[["date", "gun", "rvol20", f"fwd{h}"]].dropna()
        bt = tabanlar[h]["temiz"][g["gun"].to_numpy(np.int64)]
        fz = g[f"fwd{h}"].to_numpy(float) - bt
        rv = g["rvol20"].to_numpy(float)
        satir = {}
        for lo_, hi_ in kenar:
            m = (rv >= lo_) & (rv < hi_) & np.isfinite(fz)
            ad = f"{lo_}-{hi_ if hi_ < 1e8 else 'inf'}"
            satir[ad] = {"n": int(m.sum()), "temiz_fazla_ort": O._r6(float(np.mean(fz[m])))
                         if m.sum() else None,
                         "ham_ort": O._r6(float(np.mean(g[f"fwd{h}"].to_numpy(float)[m])))
                         if m.sum() else None}
        bant[str(h)] = satir
    tani["bant_tablosu_panel_CI_YOK"] = {
        "aciklama": "EDG-002'nin cf-katman bant tablosunun PANEL karşılığı (temiz-taban fazlası ve "
                    "ham). s1_retro'nun panel tanısı bant yapısının panelde DÜZLEŞTİĞİNİ söylüyordu; "
                    "bu satır o okumayı bu turun verisiyle tekrarlar.", "ufuklar": bant}
    # (2) MEDYAN tanımlı rvol varyantı (kart metnindeki ikinci tanım)
    Vm = V[V["rvol20_medyan"].notna()].copy()
    Vm["bolge_med"] = _bolge_maskesi(Vm["rvol20_medyan"].to_numpy(float))
    med = {"aciklama": "Kart METNİNİN yazdığı ikinci tanım: rvol = hacim/MEDYAN20(hacim). CI YOK "
                       "→ K harcamaz; hüküm taşıyan sayı SMA (canlı) tanımıyladır.",
           "bolge_n": int(Vm["bolge_med"].sum()),
           "iki_tanim_spearman": O._r6(O.spearman_np(
               Vm["rvol20"].sample(n=min(200000, len(Vm)), random_state=5),
               Vm["rvol20_medyan"].sample(n=min(200000, len(Vm)), random_state=5))),
           "ufuklar": {}}
    for h in HORIZONS:
        g = Vm[Vm["bolge_med"]][["date", "gun", f"fwd{h}"]].dropna()
        bt = tabanlar[h]["temiz"][g["gun"].to_numpy(np.int64)]
        ok = np.isfinite(bt)
        v = (g[f"fwd{h}"].to_numpy(float) - bt)[ok]
        med["ufuklar"][str(h)] = {"n": int(len(v)), "temiz_fazla_ort_CI_YOK": O._r6(float(np.mean(v)))
                                  if len(v) else None}
    tani["medyan_tanim_varyanti_CI_YOK"] = med
    # (3) cf katmanı ile panel arasındaki popülasyon farkı (s1_retro'nun "kırılıma koşullu" tespiti)
    tani["cf_vs_panel_populasyon_notu"] = {
        "aciklama": "EDG-002'nin +1.61% gözlemi cf (kırılım adayı) KATMANINDA ölçüldü; bu kart "
                    "`universe: full_251` + `kesit dilim: günlük gözlem` diyor, yani PANEL. İki "
                    "popülasyon aynı değildir ve s1_retro paneli ayrıca ölçüp 'pozitif hacim etkisi "
                    "KIRILIM popülasyonuna koşulludur, evrensel değil' demişti. Bu turda cf-katman "
                    "yeniden üretimi bekçiler bölümünde (EDG-002 nesnesinin birebir kopyası) durur; "
                    "hüküm taşıyan hücreler PANELDEN gelir.",
        "cf_katman_bolge_n": pkc["edg002_bolge_yeniden_uretimi"]["olculen"].get("n"),
        "panel_bolge_n": int(V["bolge"].sum()),
    }
    sonuc["v_tani"] = tani

    # ---------------- BEKÇİLER ----------------
    print("== 017: bekçiler (PK5-F temiz_taban özdeşliği) ==", flush=True)
    pk5f = {}
    for h in HORIZONS:
        pk5f[str(h)] = PK.pk5_f_temiz_taban(sym_ad, sym_kod_all, gun_kod_all, olay_all, h)
    pk5["F_temiz_taban_ozdesligi"] = pk5f
    pk5["gecti"] = bool(pk5["C_hizli_ortalama"]["gecti"] and pk5["E_hizli_spearman"]["gecti"]
                        and all(v["gecti"] for v in pk5f.values()))
    sonuc["bekciler"] = {
        "pozitif_kontrol": pkc,
        "pk4_yol_tutarliligi": pk4,
        "pk5_ozdeslikler": pk5,
        "artik_ortogonallik": ortog,
        "kod_damgasi": {"motor_kopyalandi": True, "n_dosya": len(O.MOTOR_DAMGA),
                        "repo_kopya_ayni": all(v["repo"] == v["kopya"]
                                               for v in O.MOTOR_DAMGA.values()),
                        "not": "Ölçüm anında repo çalışma ağacı KİRLİYDİ (başka ajanlar uçuşta). "
                               "Motor kum havuzuna KOPYALANDI ve tüm koşumlar kopyadan yapıldı; "
                               "dosya bazında sha256 kod_damgasi_017.json'da."},
    }

    # ---------------- KILL / SUCCESS KARŞILIKLARI (VERİ — HÜKÜM CÜMLESİ YOK) ----------------
    def _oku(b):
        if not b or b.get("ci") is None:
            return {"nokta": None if not b else b.get("ort", b.get("ic")),
                    "ci": None, "ci_sifiri_iceriyor": None, "neden": (b or {}).get("neden")}
        lo, hi = b["ci"]["lo"], b["ci"]["hi"]
        return {"nokta": b.get("ort", b.get("ic")), "ci": b["ci"],
                "ci_sifiri_iceriyor": bool(lo <= 0 <= hi),
                "pozitif_anlamli": bool(lo > 0), "negatif_anlamli": bool(hi < 0)}

    k1_20 = kat1["ufuklar"]["20"]["evren_fazlasi_TEMIZ_taban_HUKUM"]
    k1_10 = kat1["ufuklar"]["10"]["evren_fazlasi_TEMIZ_taban_HUKUM"]
    a1_20 = a1["ufuklar"]["20"]["loo_desil_fazlasi"]
    a1_10 = a1["ufuklar"]["10"]["loo_desil_fazlasi"]
    b_20 = icb["ufuklar"]["20"]["artik_desil_ic_fazla_HUKUM"]
    b_10 = icb["ufuklar"]["10"]["artik_desil_ic_fazla_HUKUM"]
    n20 = mal["ufuklar"]["20"]["katman1_evren_fazlasi"]["kart_modeli_10bps"]
    n10 = mal["ufuklar"]["10"]["katman1_evren_fazlasi"]["kart_modeli_10bps"]

    def _yon(v):
        return None if v is None else (1 if v > 0 else (-1 if v < 0 else 0))

    sonuc["kill_success_karsiliklari"] = {
        "UYARI": "Bu blok VERİDİR, hüküm DEĞİLDİR. Kartın kill/success metinleri BİREBİR "
                 "kopyalanmış ve her birinin sayısal karşılığı yanına yazılmıştır. Hangi dalın "
                 "tetiklendiğine Rol-1 karar verir; bu ajan kart dosyasına DOKUNMADI.",
        "success_metric_metni":
            "rvol>=2.5 bölge fazlası @20 anlamlı POZİTİF (CI 0-dışı) VE artık-katkı anlamlı: "
            "sürekli rvol20 (desil-kontrol, EDG-007/016 çift-sıralama şablonu) hesaba katıldıktan "
            "sonra >=2.5 bölgesi hâlâ bilgi taşıyor (kova-tabanı VE artık-IC iki yöntemde de aynı "
            "yön + en az birinde CI 0-dışı).",
        "success_bilesenleri": {
            "A_bolge_fazlasi_20_anlamli_pozitif": _oku(k1_20),
            "B_kova_tabani_20_(A1)": _oku(a1_20),
            "C_artik_ic_20_(B)": _oku(b_20),
            "iki_yontem_ayni_yon_20": None if (a1_20.get("ort") is None or b_20.get("ic") is None)
            else bool(_yon(a1_20["ort"]) == _yon(b_20["ic"])),
            "en_az_birinde_CI_0_disi_20": None if (a1_20.get("ci") is None and b_20.get("ci") is None)
            else bool((a1_20.get("ci") and not (a1_20["ci"]["lo"] <= 0 <= a1_20["ci"]["hi"]))
                      or (b_20.get("ci") and not (b_20["ci"]["lo"] <= 0 <= b_20["ci"]["hi"]))),
        },
        "kill_1": {"metin": "bölge fazlası @20 CI-0-içi → bilgisiz, arşiv (EDG-002 yan gözlemi "
                            "pencere-artefaktıydı — karta not düşer)",
                   "karsilik_20": _oku(k1_20), "karsilik_10_BILGI": _oku(k1_10)},
        "kill_2": {"metin": "artık yok (sürekli-rvol açıklıyor: kontrol sonrası CI-0-içi) → "
                            "'monoton devam' arşiv; canlı eşik yeterli, yeni mekanizma açılmaz",
                   "karsilik_A1_kova_tabani_20": _oku(a1_20),
                   "karsilik_B_artik_ic_20": _oku(b_20),
                   "karsilik_A1_kova_tabani_10_BILGI": _oku(a1_10),
                   "karsilik_B_artik_ic_10_BILGI": _oku(b_10)},
        "kill_3": {"metin": "maliyet-sonrası net fazla <=0 (10bps) → 'brüt-var-net-yok' arşiv + not",
                   "karsilik_20_kart_modeli": n20, "karsilik_10_kart_modeli": n10,
                   "karsilik_20_duyarlilik_20bps":
                       mal["ufuklar"]["20"]["katman1_evren_fazlasi"]["duyarlilik_20bps"]},
        "guard_karsiliklari": {
            "pozitif_kontrol_GECTI": pkc["GECTI"], "civi": pkc["civi_olculen"],
            "pk4_gecti": pk4["gecti"], "pk5_gecti": pk5["gecti"],
            "temiz_taban_uygulandi": True,
            "esik_dilbilgisi_belirsizligi": "rvol20 tanımı: kart metni 'medyan20' der, aynı satırda "
                                            "'canlı tanımla BİREBİR (indicators.py)' der; canlı "
                                            "tanım SMA20'dir. Muhafazakâr/beyanlı okuma uygulandı "
                                            "(bkz. kart_metni_uygulamasi.rvol20_tanimi); MEDYAN "
                                            "varyantı TANI olarak v_tani'de.",
        },
    }

    sonuc["DURUM"] = "TAMAM"
    O.json_yaz(O.KLASOR / "sonuc_017.json", sonuc)
    O.json_yaz(O.KLASOR / "kod_damgasi_017.json",
               {"olcum_tarihi": sonuc["olcum_tarihi"], "motor_sha256_repo_vs_kopya": O.MOTOR_DAMGA,
                "olcum_kodu_sha256": {
                    p.name: __import__("hashlib").sha256(p.read_bytes()).hexdigest()
                    for p in sorted(O.KLASOR.glob("*.py"))}})
    print("== yazıldı: sonuc_017.json + kod_damgasi_017.json ==", flush=True)


if __name__ == "__main__":
    main()
