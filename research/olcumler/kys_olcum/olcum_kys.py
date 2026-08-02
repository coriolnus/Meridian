"""olcum_kys.py — KYS-2026-001 ADIM 3: İKİ YÜZEY (K=2), STANDART vs OLAY-DIŞI TEMİZ KIYAS.

KARTIN GRİDİ (K+=2, çarpmayla): `yuzey: [temiz_kiyas_component_ic, temiz_kiyas_cf_r_tablosu]`.
  Y1 — component_ic ÜST-DESİL taban-fazlası @10/@20
  Y2 — cf R-tablosu MEDYAN-KIYAS satırı (aynı ikili: standart vs temiz)
Her ikisinde `fark` + 21 GÜNLÜK blok CI (`olcum_araclari.blok_bootstrap_ci`).

ÖLÇÜM KENDİ KIYAS MANTIĞINI YAZMAZ: taban da fazla da `olcum_araclari.olay_disi_kiyas`tan gelir
(Ders #5). Bu dosyanın işi popülasyonu kurmak, aracı çağırmak ve sayıyı raporlamaktır.

--- TASARIM KARARLARI (hepsi sayıyı değiştirdiği için burada yazılı) ---

(1) İKİ KIYASIN FARKI YALNIZ TABANDIR. `fazla = getiri − taban`. `taban` iki türlü kurulur:
      STANDART : o günün evren medyanı (olay-penceresi satırları DAHİL) — bugün depoda yapılan
      TEMİZ    : aynı gün, olay-penceresi satırları ÇIKARILMIŞ medyan
    Her ikisinde de hedefin KENDİ kimliği tabandan düşer (aracın 1. dürüstlük kuralı; EAP'nin
    "kendisi hariç" pratiğiyle de aynı). Yani `fark = temiz_taban − standart_taban`ın ta kendisidir
    ve BİLEŞENDEN BAĞIMSIZDIR: hangi bileşenin üst-desilini seçtiğimiz yalnız hangi GÜNLERİN
    kaça ağırlıklandığını belirler. Bu, Y1'de bileşen seçiminin bir "K arayışı" olmadığının
    matematiksel sebebidir — bileşenler AYNI büyüklüğün farklı gün-bileşimlerini gösterir.

(2) POPÜLASYON = component_ic'in cf KATMANI (n=2.106). Gerçek katman n=95'tir ve üst-desili ~10
    satırdır; desil istatistiği orada kurulamaz — sayı yine hesaplanır ama `n_yetersiz` bayrağıyla
    raporlanır, hükme girmez. Popülasyon tanımı `component_ic._rows` ile BİREBİR (kopyalanmadı,
    kaynak modülün fonksiyonu çağrıldı).

(3) ETİKETLENEBİLİR ALT-KÜME. Takvimin GÖRDÜĞÜ gün aralığı dışındaki satırlar ölçüme GİRMEZ; orada
    `in_blackout` False döner ama o "temiz" değil "veri yok"tur (kart kill #2'nin konusu). Hem
    hedefler hem TABAN satırları bu kapıdan geçer.

(4) GETİRİ TANIMI `component_ic.forward_returns` ile BİREBİR: `close[t+h]/close[t] − 1`, sinyal
    barının kapanışından, yüzde. Ufku dolmayan satır NaN kalır ve düşer (uydurulmaz).

(5) CI GÜN SERİSİNDEN, BLOK = 21 GÜN. Gözlemler güne kümelenir (tek günde onlarca satır); seri
    GÜN düzeyinde kurulur (o günün hedeflerinin ortalaması), zaman sırasına dizilir ve blok
    bootstrap 21 GÜNLÜK bloklarla koşar — kartın "21g blok CI" şartı budur. Nokta tahmini
    GÖZLEM ağırlıklı da raporlanır (`ort_gozlem`), çünkü iki ağırlıklandırma aynı sayı değildir ve
    farkı gizlemek okuyucuya kapalı bir kutu bırakırdı.
"""
from __future__ import annotations

import json

import ortak_kys as ok

ok.muhurle()

import datetime as dt                            # noqa: E402
import pandas as pd                              # noqa: E402

from meridian import component_ic as cic, config, indicators as ind, strategy as strat  # noqa: E402
from meridian.adapters import data as da         # noqa: E402
from meridian.olcum_araclari import (blok_bootstrap_ci, kod_surumu_damgasi,  # noqa: E402
                                     olay_disi_kiyas)
import kapsama_kys as kap                        # noqa: E402

UFUKLAR = (10, 20)
DESIL = 0.10
BLOK_GUN = 21
MIN_TABAN = 5
MIN_HEDEF = 30          # bir hücrenin sayısının raporlanması için en az hedef (IC_MIN_SAMPLE ile aynı)


# ==================================================================================================
def _gozlem_tablosu(satirlar: dict, per: dict, index_close):
    """(katman, ticker, tarih) → bileşen değerleri + ileri getiriler. `component_ic`in eşleme
    döngüsünün AYNI kapıları (bar yok / tarih yok / rs kesiti yok) uygulanır ve düşenler sayılır."""
    params = config.load_strategy()["params"]
    prox_max = float(params.get("entry.pivot_proximity_pct", 2.0) or 2.0)
    tum = [(k, t, d) for k, v in satirlar.items() for t, d in v]
    gerekli = {t for _, t, _ in tum}
    comp = {}
    for t in sorted(gerekli & set(per)):
        try:
            comp[t] = cic._component_frame(per[t], prox_max, index_close, ticker=t)
        except Exception as e:      # noqa: BLE001 — sayılır, yutulmaz
            print(f"[gozlem] {t} çerçevesi kurulamadı: {type(e).__name__}: {e}")

    tarihler = {pd.Timestamp(d) for _, t, d in tum if t in comp}
    rs_map = cic._rs_by_date(per, tarihler)

    kayitlar, dusen = [], {"bar_yok_sembol": 0, "bar_yok_tarih": 0, "rs_kesiti_yok": 0}
    for katman, t, dstr in tum:
        frame = comp.get(t)
        if frame is None:
            dusen["bar_yok_sembol"] += 1
            continue
        d = pd.Timestamp(dstr)
        if d not in frame.index:
            dusen["bar_yok_tarih"] += 1
            continue
        satir = frame.loc[d]
        rsv = (rs_map.get(d) or {}).get(t)
        if rsv is None:
            dusen["rs_kesiti_yok"] += 1
            continue
        kayit = {"katman": katman, "ticker": t, "gun": dstr, "rs": float(rsv)}
        for c in cic.COMPONENTS:
            if c != "rs":
                kayit[c] = float(satir[c]) if pd.notna(satir[c]) else None
        for h in UFUKLAR:
            kayit[f"fwd{h}"] = float(satir[f"fwd{h}"]) if pd.notna(satir[f"fwd{h}"]) else None
        kayitlar.append(kayit)
    return kayitlar, dusen


def _evren_satirlari(per: dict, gunler: set, h: int) -> list:
    """TABAN havuzu: verilen günlerde EVRENİN TAMAMI (251 sembol) için ileri getiri satırları.

    Neden yalnız hedef günleri: taban AYNI GÜNÜN kesitidir (Ders #3/#5); başka günlerin satırları
    hiçbir tabana girmez, yalnız döngüyü uzatır. Bu bir kısaltma değil, tanımın kendisidir."""
    out = []
    hedef = {pd.Timestamp(g) for g in gunler}
    for t, df in per.items():
        kapanis = df["close"]
        ileri = kapanis.shift(-h) / kapanis - 1.0
        ortak = ileri.index.intersection(hedef)
        for d in ortak:
            v = ileri.loc[d]
            if pd.notna(v):
                out.append((t, str(d.date()), float(v)))
    return out


def _gun_serisi(kiyaslar: list, alan: str) -> list:
    """[(gün, o günün ortalaması)] — zaman sıralı. Blok bootstrap'ın girdisi (bkz. karar 5)."""
    kova: dict = {}
    for k in kiyaslar:
        v = k.get(alan)
        if v is None:
            continue
        kova.setdefault(str(k["gun"]), []).append(v)
    return [(g, sum(vs) / len(vs)) for g, vs in sorted(kova.items())]


def _ci(seri_gun: list) -> dict:
    r = blok_bootstrap_ci([v for _, v in seri_gun], blok=BLOK_GUN)
    return {"ort_bps": None if r["ort"] is None else round(r["ort"] * 1e4, 3),
            "lo_bps": None if r["lo"] is None else round(r["lo"] * 1e4, 3),
            "hi_bps": None if r["hi"] is None else round(r["hi"] * 1e4, 3),
            "n_gun": r["n"], "blok": r["blok"], "blok_kaynagi": r["blok_kaynagi"],
            "sifiri_disliyor": r["sifiri_disliyor"], "yontem": r["yontem"],
            "neden": r["neden"], "uyari": r["uyari"]}


def _yuzey(ad: str, hedefler: list, evren: list, olaylar: dict, h: int) -> dict:
    """Bir yüzeyin bir ufuktaki TAM okuması: standart vs temiz + fark + CI'lar."""
    r = olay_disi_kiyas(evren, olaylar, pencere=ok.PENCERE, hedefler=hedefler,
                        ozet="medyan", min_taban=MIN_TABAN)
    kiyaslar = [k for k in r["kiyaslar"] if k["kirli_fazla"] is not None]
    if not kiyaslar:
        return {"ad": ad, "ufuk": h, "n_hedef": r["n_hedef"], "n_kiyaslanan": 0,
                "olculemedi": "hiçbir hedef kıyaslanamadı", "uyari": r["uyari"]}

    for k in kiyaslar:                       # fark = STANDART − TEMİZ (kartın yazdığı yön)
        k["fark"] = k["kirli_fazla"] - k["fazla"]
    n = len(kiyaslar)
    ort_temiz = sum(k["fazla"] for k in kiyaslar) / n
    ort_std = sum(k["kirli_fazla"] for k in kiyaslar) / n
    kirlilikler = sorted(v["kirlilik_orani"] for v in r["gun_tabani"].values()
                         if v["kirlilik_orani"] is not None)
    return {
        "ad": ad, "ufuk": h,
        "n_hedef": r["n_hedef"], "n_kiyaslanan": n, "n_taban_yok": r["n_taban_yok"],
        "n_gun": r["n_gun"], "n_yetersiz": bool(n < MIN_HEDEF),
        "standart_fazla_bps": round(ort_std * 1e4, 3),
        "temiz_fazla_bps": round(ort_temiz * 1e4, 3),
        "fark_standart_eksi_temiz_bps": round((ort_std - ort_temiz) * 1e4, 3),
        "ci_fark": _ci(_gun_serisi(kiyaslar, "fark")),
        "ci_standart": _ci(_gun_serisi(kiyaslar, "kirli_fazla")),
        "ci_temiz": _ci(_gun_serisi(kiyaslar, "fazla")),
        "taban_kirliligi": {
            "medyan": round(kirlilikler[len(kirlilikler) // 2], 4) if kirlilikler else None,
            "ortalama": round(sum(kirlilikler) / len(kirlilikler), 4) if kirlilikler else None,
            "maks": round(max(kirlilikler), 4) if kirlilikler else None,
            "beyan": "kıyas günlerinde evrenin ne kadarı KENDİ olay penceresindeydi (EAP'nin "
                     "%64 ort./%74 medyan bulgusunun bu yüzeydeki karşılığı)"},
        "arac_sikismasi": r["sikisma"],
        "uyari": r["uyari"]}


# ==================================================================================================
def kos() -> dict:
    # --- takvim + etiketlenebilirlik --------------------------------------------------------------
    olaylar, sorulan_gunler = kap.nasdaq_takvimi()
    if not sorulan_gunler:
        return {"olculemedi": "Nasdaq takvim önbelleği boş — takvim_cek.py koşmadı"}

    def _etiketlenebilir_gun(g: str) -> bool:
        d0 = dt.date.fromisoformat(g)
        is_gunleri = [(d0 + dt.timedelta(days=i)) for i in range(ok.BLACKOUT_DAYS + 1)]
        is_gunleri = [x.isoformat() for x in is_gunleri if x.weekday() < 5]
        return bool(is_gunleri) and all(x in sorulan_gunler for x in is_gunleri)

    satirlar = kap.olcum_satirlari()
    per = ok.panel_yukle()
    index_close = cic._load_index_close()
    kayitlar, dusen = _gozlem_tablosu(satirlar, per, index_close)

    n_ham = len(kayitlar)
    kayitlar = [k for k in kayitlar if _etiketlenebilir_gun(k["gun"])]
    print(f"[olcum] gözlem {n_ham} → etiketlenebilir {len(kayitlar)}", flush=True)

    cf_kayit = [k for k in kayitlar if k["katman"] == "cf"]
    gercek_kayit = [k for k in kayitlar if k["katman"] == "gercek"]

    sonuc: dict = {
        "kart": "KYS-2026-001", "adim": "3 — iki yüzey (K=2)",
        "pencere": {"once": ok.PENCERE[0], "sonra": ok.PENCERE[1],
                    "tanim": "earnings.in_blackout ile BİREBİR (PK-0 ile kanıtlandı)"},
        "populasyon": {"ham_gozlem": n_ham, "etiketlenebilir": len(kayitlar),
                       "cf": len(cf_kayit), "gercek": len(gercek_kayit),
                       "dusenler": dusen,
                       "beyan": "etiketlenemeyen satır ÖLÇÜME GİRMEZ (kart kill #2'nin konusu); "
                                "orada in_blackout False döner ama bu 'temiz' değil 'veri yok'tur"},
        "getiri_tanimi": "close[t+h]/close[t]-1 — component_ic.forward_returns ile birebir",
        "ozet_istatistigi": "medyan (gün tabanı)", "min_taban": MIN_TABAN,
        "ci": {"blok_gun": BLOK_GUN, "yontem": "moving block bootstrap, GÜN serisi üzerinde"},
        "yuzeyler": {}}

    gunler = {k["gun"] for k in kayitlar}
    evren_h = {h: _evren_satirlari(per, gunler, h) for h in UFUKLAR}
    sonuc["taban_havuzu"] = {str(h): len(v) for h, v in evren_h.items()}

    # --- Y1: component_ic ÜST-DESİL ---------------------------------------------------------------
    y1: dict = {"tanim": ("component_ic cf katmanının bileşen değerine göre ÜST DESİLİ; taban-fazlası "
                          "standart (kirli) ve olay-dışı (temiz) tabanla"),
                "desil": DESIL, "bilesenler": {}}
    for c in cic.COMPONENTS:
        y1["bilesenler"][c] = {}
        for h in UFUKLAR:
            uygun = [k for k in cf_kayit if k.get(c) is not None and k.get(f"fwd{h}") is not None]
            if not uygun:
                y1["bilesenler"][c][str(h)] = {"olculemedi": "bileşen ya da ufuk hiçbir satırda yok",
                                               "n": 0}
                continue
            uygun.sort(key=lambda k: k[c], reverse=True)
            kes = max(1, int(round(len(uygun) * DESIL)))
            ust = uygun[:kes]
            hedefler = [(k["ticker"], k["gun"], k[f"fwd{h}"]) for k in ust]
            y1["bilesenler"][c][str(h)] = _yuzey(f"Y1·{c}@{h}", hedefler, evren_h[h], olaylar, h)
            y1["bilesenler"][c][str(h)]["desil_esigi"] = round(ust[-1][c], 6)
            y1["bilesenler"][c][str(h)]["n_uygun_populasyon"] = len(uygun)

    # HAVUZLANMIŞ Y1 — yüzeyin TEK sayısı ve TEK CI'si. Bileşenlerin üst-desilleri BİRLEŞTİRİLİR
    # (aynı (ticker, gün) bir kez sayılır). Gerekçe: bileşen başına 16 hücre 16 aralık demektir ve
    # yüzeyin kendisinin bir aralığı olmaz; medyanın CI'si ise TÜRETİLEMEZ (hücreler aynı
    # gözlemlerden gelir, bağımsız değildir). Havuz, kartın "yüzey" biriminin doğal karşılığıdır.
    for h in UFUKLAR:
        havuz: dict = {}
        for c in cic.COMPONENTS:
            hucre = y1["bilesenler"][c].get(str(h)) or {}
            if hucre.get("n_kiyaslanan"):
                uygun = [k for k in cf_kayit
                         if k.get(c) is not None and k.get(f"fwd{h}") is not None]
                uygun.sort(key=lambda k: k[c], reverse=True)
                for k in uygun[:max(1, int(round(len(uygun) * DESIL)))]:
                    havuz[(k["ticker"], k["gun"])] = k[f"fwd{h}"]
        if havuz:
            y1.setdefault("havuzlanmis", {})[str(h)] = _yuzey(
                f"Y1·havuz@{h}", [(t, g, v) for (t, g), v in havuz.items()],
                evren_h[h], olaylar, h)
            y1["havuzlanmis"][str(h)]["not"] = ("bileşenlerin üst-desillerinin BİRLEŞİMİ "
                                                "((ticker,gün) tekilleştirildi)")

    # İKİNCİ ÖZET: bileşenler arası MEDYAN fark. Gerekçe (karar 1): fark bileşenden bağımsız bir
    # TABAN büyüklüğüdür; tek bir bileşeni "en iyi" diye seçmek kazananın-laneti olurdu, ortalama ise
    # tek bir uç bileşenden etkilenirdi. CI'si YOKTUR (bkz. havuzlanmış özet).
    for h in UFUKLAR:
        farklar = [v[str(h)].get("fark_standart_eksi_temiz_bps") for v in y1["bilesenler"].values()
                   if v.get(str(h), {}).get("fark_standart_eksi_temiz_bps") is not None]
        farklar.sort()
        y1.setdefault("baslik", {})[str(h)] = {
            "bilesen_sayisi": len(farklar),
            "fark_medyan_bps": farklar[len(farklar) // 2] if farklar else None,
            "fark_min_bps": farklar[0] if farklar else None,
            "fark_maks_bps": farklar[-1] if farklar else None}
    sonuc["yuzeyler"]["Y1_component_ic_ust_desil"] = y1

    # --- Y2: cf R-tablosu medyan-kıyas satırı -----------------------------------------------------
    y2: dict = {"tanim": ("cf defterinin (entered, near-miss hariç) TAMAMI — R tablosunun "
                          "medyan-kıyas satırının popülasyonu; aynı standart/temiz ikilisi"),
                "ufuklar": {}}
    for h in UFUKLAR:
        uygun = [k for k in cf_kayit if k.get(f"fwd{h}") is not None]
        hedefler = [(k["ticker"], k["gun"], k[f"fwd{h}"]) for k in uygun]
        y2["ufuklar"][str(h)] = _yuzey(f"Y2·cf@{h}", hedefler, evren_h[h], olaylar, h)
        y2["ufuklar"][str(h)]["n_uygun_populasyon"] = len(uygun)
    sonuc["yuzeyler"]["Y2_cf_r_tablosu"] = y2

    # --- GERÇEK katman (bağlam; n=95, desil kurulamaz) --------------------------------------------
    gercek: dict = {"not": "n=95 popülasyon — desil istatistiği kurulamaz; BAĞLAM, hüküm değil",
                    "ufuklar": {}}
    for h in UFUKLAR:
        uygun = [k for k in gercek_kayit if k.get(f"fwd{h}") is not None]
        if uygun:
            hedefler = [(k["ticker"], k["gun"], k[f"fwd{h}"]) for k in uygun]
            gercek["ufuklar"][str(h)] = _yuzey(f"gercek@{h}", hedefler, evren_h[h], olaylar, h)
        else:
            gercek["ufuklar"][str(h)] = {"olculemedi": "ufku dolan gerçek satır yok", "n": 0}
    sonuc["gercek_katman_baglam"] = gercek

    # --- AÇIKLAYICI SAYIM (K'ya GİRMEZ, etki tahmini DEĞİL) ---------------------------------------
    # NEDEN BURADA. Kartı doğuran EAP yan bulgusu "%64 ort. / %74 medyan" diyordu; bu turun kıyas
    # günlerinde ölçülen taban kirliliği ise çok daha küçük çıkıyor. Fark bir çelişki DEĞİL, PENCERE
    # farkıdır: EAP'nin penceresi [−10, −1] İŞLEM günü (~14 takvim günü), karartmanınki [olay−5, olay]
    # TAKVİM günü (~4 iş günü). Kart pencereyi `in_blackout` ile BİREBİR sabitlediği için ölçüm o
    # pencerede koşar; aşağıdaki satır yalnız İKİ SAYIMI yan yana koyar ki okuyucu iki raporu
    # birbirine karşı okumasın. HİÇBİR fazla-getiri/etki bu pencerede HESAPLANMAZ — grid K=2'dir.
    aciklayici = {}
    for etiket, pen in (("kart_penceresi_5_0", ok.PENCERE), ("eap_benzeri_14_1_yaklasik", (14, 1))):
        rr = olay_disi_kiyas(evren_h[UFUKLAR[0]], olaylar, pencere=pen,
                             hedefler=[(k["ticker"], k["gun"], k[f"fwd{UFUKLAR[0]}"])
                                       for k in cf_kayit if k.get(f"fwd{UFUKLAR[0]}") is not None],
                             ozet="medyan", min_taban=MIN_TABAN)
        kl = sorted(v["kirlilik_orani"] for v in rr["gun_tabani"].values()
                    if v["kirlilik_orani"] is not None)
        aciklayici[etiket] = {
            "pencere": {"once": pen[0], "sonra": pen[1]},
            "taban_kirliligi_medyan": round(kl[len(kl) // 2], 4) if kl else None,
            "taban_kirliligi_ortalama": round(sum(kl) / len(kl), 4) if kl else None,
            "taban_kirliligi_maks": round(max(kl), 4) if kl else None}
    aciklayici["beyan"] = ("YALNIZ SAYIM — hiçbir etki/fazla-getiri bu satırdan okunmaz ve K'ya "
                           "girmez. EAP penceresi İŞLEM günüdür; (14,1) onun TAKVİM günü "
                           "yaklaşımıdır (10 iş günü ≈ 14 takvim günü) ve birebir değildir.")
    sonuc["aciklayici_yayginlik_sayimi"] = aciklayici

    sonuc["kod_damgasi"] = kod_surumu_damgasi(kok=str(ok.DEPO))
    sonuc["muhur"] = ok.muhur_dogrula()
    sonuc["hukum_yok"] = "sayı üretildi; kart hükmü Rol-1'dedir (bu tur ALTYAPI kartıdır, retro hüküm YOK)"
    return sonuc


if __name__ == "__main__":
    r = kos()
    (ok.CIKTI / "olcum_kys001.json").write_text(
        json.dumps(r, ensure_ascii=False, indent=2), encoding="utf-8")
    if "olculemedi" in r:
        print(r["olculemedi"])
    else:
        print(json.dumps(r["populasyon"], ensure_ascii=False, indent=2))
        for h in UFUKLAR:
            b = r["yuzeyler"]["Y1_component_ic_ust_desil"]["baslik"][str(h)]
            hv = r["yuzeyler"]["Y1_component_ic_ust_desil"].get("havuzlanmis", {}).get(str(h), {})
            y2 = r["yuzeyler"]["Y2_cf_r_tablosu"]["ufuklar"][str(h)]
            print(f"\n@{h} Y1 HAVUZ n={hv.get('n_kiyaslanan')} std={hv.get('standart_fazla_bps')} "
                  f"temiz={hv.get('temiz_fazla_bps')} fark={hv.get('fark_standart_eksi_temiz_bps')}bps "
                  f"CI={hv.get('ci_fark', {}).get('lo_bps')}..{hv.get('ci_fark', {}).get('hi_bps')}")
            print(f"@{h} Y1 fark medyan={b['fark_medyan_bps']}bps "
                  f"[{b['fark_min_bps']} .. {b['fark_maks_bps']}]")
            print(f"@{h} Y2 standart={y2.get('standart_fazla_bps')} temiz={y2.get('temiz_fazla_bps')} "
                  f"fark={y2.get('fark_standart_eksi_temiz_bps')}bps "
                  f"CI={y2.get('ci_fark', {}).get('lo_bps')}..{y2.get('ci_fark', {}).get('hi_bps')}")
