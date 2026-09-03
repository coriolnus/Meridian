"""EDG-2026-021 · QC defteri v4 — PARÇA C/4 (H5 KAPI … H10b KAPSAMA … H11 SONUÇ JSON)

TEK BAŞINA KOŞMAZ. Sıra: _a.py → _d.py → _b.py → _c.py, hepsi AYNI namespace'e.
H10b (kapsama) ve H11 (JSON) DUR hâlinde de koşar — bu parça HER HÂLÜKÂRDA koşturulmalıdır.
"""

if "S" not in globals() or "gun_blok_bootstrap_ort" not in globals():
    raise RuntimeError("ÖNCE qc_defter_021_a.py koşmalı — sıra: a → b → c")
if not S.get("_parca_b_yuklendi"):
    raise RuntimeError("ÖNCE qc_defter_021_b.py koşmalı — sıra: a → b → c "
                       "(yükleme sırası sorulur, DUR durumu değil: _c her hâlde koşmalıdır)")

# %%
# --- H5 — POZİTİF KONTROL (KART GUARD'I) · KAPI -------------------------------------
# Kart guards: rvol20 @20 IC işaret/mertebesi (çivi ≈0.064) yeniden üretilmeli, yoksa DUR.
# H2–H4 yalnız VERİ TAŞIR — ilk ÖLÇÜM işi budur; tutmazsa kayıtlı hücre (H6–H8) KOŞMAZ.

if _kapi("5"):
    B = S["panel"]
    pk_df = B[B["evren_uye"] & B["rvol20"].notna() & B["fwd20"].notna()]
    kesit = pk_df.groupby("tarih").size()
    kullan = kesit[kesit >= ANAHTAR["MIN_KESIT"]].index
    pk_df = pk_df[pk_df["tarih"].isin(kullan)]
    pk = {"tanim": "rvol20 = hacim / SMA20(hacim), payda bugünü içerir (meridian.indicators)",
          "olcum": "havuzlanmış Spearman IC (rvol20, fwd20) · aynı kesit kuralları",
          "yerel_civi": ANAHTAR["PK_CIVI"], "mertebe_carpani": ANAHTAR["PK_MERTEBE"],
          "beyan": "yerel çivi karşı-olgusal katmanda ölçüldü; İŞARET ve MERTEBE aranır "
                   "(nokta eşitliği değil). Hüküm eşiği DEĞİL, boru hattı kapısı.",
          "n": int(len(pk_df)), "n_gun": int(pk_df["tarih"].nunique())}
    if len(pk_df) < ANAHTAR["MIN_DILIM"]:
        pk["ic"] = None
        pk["neden"] = f"n={len(pk_df)} < MIN_DILIM={ANAHTAR['MIN_DILIM']}"
        pk["GECTI"] = None
    else:
        ic = spearman_ic(pk_df["rvol20"].to_numpy(float), pk_df["fwd20"].to_numpy(float))
        pk["ic"] = None if ic is None else float(ic)
        pk["ci"] = ic_gun_blok_ci(pk_df["rvol20"].to_numpy(float),
                                  pk_df["fwd20"].to_numpy(float), pk_df["tarih"].to_numpy())
        if ic is None:
            pk["GECTI"] = None
            pk["neden"] = "rütbe değişimi yok — IC tanımsız"
        else:
            alt = ANAHTAR["PK_CIVI"] / ANAHTAR["PK_MERTEBE"]
            ust = ANAHTAR["PK_CIVI"] * ANAHTAR["PK_MERTEBE"]
            pk["bant"] = [alt, ust]
            pk["GECTI"] = bool(ic > 0 and alt <= ic <= ust)
            pk["neden"] = None if pk["GECTI"] else (
                f"IC={ic:.4f} · beklenen POZİTİF ve bant [{alt:.4f}, {ust:.4f}]")
    S["pk"] = pk
    print(f"   PK · IC@20={pk.get('ic')} · n={pk['n']} · gün={pk['n_gun']} · "
          f"çivi={ANAHTAR['PK_CIVI']} → GEÇTİ={pk.get('GECTI')}")
    if pk.get("ci"):
        print(f"   PK CI: {pk['ci'].get('lo')} .. {pk['ci'].get('hi')}")
    if pk.get("GECTI") is not True:
        S["DUR"] = (f"POZİTİF KONTROL TUTMADI (kart guard'ı) — IC@20={pk.get('ic')}; beklenen: "
                    f"pozitif ve ≈{ANAHTAR['PK_CIVI']} mertebesinde (×{ANAHTAR['PK_MERTEBE']} "
                    f"bandı). Ayrıntı: {pk.get('neden')}. Boru hattı geçersiz sayılır; sonraki "
                    "hücreler KOŞTURULMAZ, hiçbir kart sayısı üretilmez.")
        print("\n" + "=" * 78)
        print("PK-DUR: DEFTER DURDU. Son hücreyi (H11) yine de koş — DUR nedenini taşıyan")
        print("        JSON'u basar. O JSON'u operatör talimatındaki gibi Rol-1'e ilet.")
        print("=" * 78)


# %%
# --- H6 — turnover21 = medyan21(hacim) / as-of hisse sayısı -------------------------
# Hisse ayrı çağrıdan değil PANELİN KENDİ SATIRINDAN gelir (H2). AS-OF: yalnız İLERİ doldurma.
# Bayatlık bekçisi (EDG-016 SCHW dersi) + fiziksel bekçi (devir > TURNOVER_TAVAN imkânsız).

if _kapi("6"):
    B = S["panel"]
    n_ham_dolu = int(B["shares"].notna().sum())
    if n_ham_dolu == 0:
        S["DUR"] = ("shares_outstanding AS-OF ALINAMADI — panelin hiçbir satırında ne "
                    "company_profile.shares_outstanding ne earning_reports."
                    "basic_average_shares.value ölçülebildi. Kart kill_criteria: 'ölçülemedi' "
                    "beyanı, kart askıya (uydurma vekil YASAK).")
        _olculemedi("shares_outstanding_as_of", S["DUR"])
        S["shares_muhasebe"] = {"shares_ham_dolu_hucre": 0, "neden": S["DUR"]}
    else:
        gg = B.groupby("sid", sort=False)
        B["_ks"] = B["tarih"].where(B["shares"].notna())
        B["shares"] = gg["shares"].ffill()
        B["shares_bayatlik_gun"] = (B["tarih"] - gg["_ks"].ffill()).dt.days
        bayat = B["shares_bayatlik_gun"] > ANAHTAR["SHARES_BAYAT_GUN"]
        n_bayat = int((bayat & B["shares"].notna()).sum())
        B.loc[bayat, "shares"] = np.nan
        B = B.drop(columns=["_ks"])
        B["turnover21"] = B["med_hacim21"].astype("float64") / B["shares"]
        fiziksel = B["turnover21"] > ANAHTAR["TURNOVER_TAVAN"]
        n_fiziksel = int((fiziksel & B["turnover21"].notna()).sum())
        B.loc[fiziksel, "turnover21"] = np.nan
        B["turnover21"] = B["turnover21"].astype("float32")
        S["panel"] = B
        S.setdefault("bellek_mb", {})["H6_turnoverli"] = round(
            B.memory_usage(deep=True).sum() / 1e6, 1)
        n_dolu = int(B["shares"].notna().sum())
        S["shares_muhasebe"] = {
            "kaynak": "panel (universe_history): company_profile birincil, "
                      "basic_average_shares vekil",
            "shares_ham_dolu_hucre": n_ham_dolu,
            "shares_kaynak_dagilimi": S["panel_muhasebe"]["shares_kaynak_dagilimi"],
            "shares_kaynak_kodlari": S["panel_muhasebe"]["shares_kaynak_kodlari"],
            "ffill_sonrasi_dolu_hucre": n_dolu,
            "bayatlik_bekcisi_kapatti": n_bayat,
            "bayatlik_esik_gun": ANAHTAR["SHARES_BAYAT_GUN"],
            "bayatlik_medyan_gun": (float(B.loc[B["shares"].notna(),
                                                "shares_bayatlik_gun"].median())
                                    if n_dolu else None),
            "fiziksel_bekci_kapatti": n_fiziksel,
            "fiziksel_tavan": ANAHTAR["TURNOVER_TAVAN"],
            "turnover21_dolu_hucre": int(B["turnover21"].notna().sum()),
            "as_of_beyani": "QC evren verisi gün gün teslim edilir; t satırı t günü bilinen "
                            "değer sayıldı (EDGAR filed<=t karşılığı). BAĞIMSIZ DOĞRULANMADI.",
        }
        print("   TURNOVER ·", json.dumps(S["shares_muhasebe"], ensure_ascii=False))
        n_to = int(B["turnover21"].notna().sum())
        if n_to < ANAHTAR["MIN_DILIM"]:
            S["DUR"] = (f"turnover21 ÖLÇÜLEMEDİ — kullanılabilir hücre {n_to} < MIN_DILIM="
                        f"{ANAHTAR['MIN_DILIM']} (bayatlık/fiziksel bekçileri ya da hacim "
                        "penceresi kapattı). Uydurma doldurma YASAK.")
            _olculemedi("turnover21", S["DUR"])


# %%
# --- H7 — KESİT + ÜST-%20 DİLİM + AYNI-GÜN EVREN TABANI -----------------------------
# EDG-016 ile birebir: kesit = o gün ÖLÇÜM EVRENİ üyesi ve turnover21 tanımlı semboller
# (kesit ≥ MIN_KESIT); dilim = gün içi turnover21 yüzdelik rütbesi > 0.80; taban = AYNI GÜN

if _kapi("7"):
    B = S["panel"]
    V = B[B["evren_uye"] & B["turnover21"].notna()].copy()
    kesit = V.groupby("tarih").size()
    kullan = kesit[kesit >= ANAHTAR["MIN_KESIT"]].index
    V = V[V["tarih"].isin(kullan)].copy()
    V["to_pct"] = V.groupby("tarih")["turnover21"].rank(pct=True, method="first")
    V["ust"] = V["to_pct"] > (1.0 - ANAHTAR["UST_PCT"])
    taban = {}
    for h in ANAHTAR["UFUKLAR"]:
        t = B[B["evren_uye"]][["tarih", f"fwd{h}"]].dropna()
        taban[h] = t.groupby("tarih")[f"fwd{h}"].mean()
    S["taban"] = taban
    S["V"] = V
    if len(V) == 0:
        S["DUR"] = ("KESİT KURULAMADI — hiçbir günde turnover21 tanımlı evren üyesi sayısı "
                    f"MIN_KESIT={ANAHTAR['MIN_KESIT']} eşiğine ulaşmadı")
        _olculemedi("kesit", S["DUR"])
    else:
        kk = kesit[kesit >= ANAHTAR["MIN_KESIT"]]
        S["kesit_muhasebe"] = {
            "gozlem_gunu_toplam": int(B[B["evren_uye"]]["tarih"].nunique()),
            "kesit_yeterli_gun": int(len(kullan)), "min_kesit": ANAHTAR["MIN_KESIT"],
            "kesit_buyuklugu": {"medyan": float(kk.median()), "min": int(kk.min()),
                                "maks": int(kk.max())},
            "tarih_araligi": [str(V["tarih"].min().date()), str(V["tarih"].max().date())],
            "n_satir": int(len(V)), "n_sembol": int(V["sid"].nunique()),
            "turnover21_dagilimi": {str(q): float(V["turnover21"].quantile(q))
                                    for q in (0.01, 0.25, 0.5, 0.75, 0.99)},
            "dilim_satir": int(V["ust"].sum()),
            "dilim_sembol": int(V.loc[V["ust"], "sid"].nunique()),
        }
        print("   KESİT ·", json.dumps(S["kesit_muhasebe"], ensure_ascii=False))


# %%
# --- H8 — ÖLÇÜM: ÜST-%20 DİLİM EVREN-FAZLASI + 21g BLOK CI + MALİYET ----------------
# Kartın TEK kayıtlı hücresi: qc_turnover_ust20_fazlasi (K+=1). Maliyet SABİTTİR → CI aynı
# sabitle ötelenir (bootstrap yeniden koşulmaz; cebirsel özdeş, EDG-016 ile aynı okuma).

if _kapi("8"):
    V = S["V"]
    taban = S["taban"]
    olcum, maliyet, fazla_kayit = {}, {}, {}
    for h in ANAHTAR["UFUKLAR"]:
        sub = V[V["ust"]][["tarih", "sid", f"fwd{h}"]].dropna(subset=[f"fwd{h}"])
        base = sub["tarih"].map(taban[h])
        ok = base.notna().to_numpy()
        y = sub[f"fwd{h}"].to_numpy(float)[ok]
        b = base.to_numpy(float)[ok]
        d = sub["tarih"].to_numpy()[ok]
        fazla = y - b
        fazla_kayit[h] = (fazla, d, sub["sid"].to_numpy()[ok])
        gun_ort = pd.Series(fazla, index=pd.Index(d, name="tarih")).groupby(level=0).mean()
        olcum[str(h)] = {
            "tanim": f"gün içi turnover21 üst %{int(ANAHTAR['UST_PCT'] * 100)} dilimi; taban "
                     "= AYNI GÜN evren ortalaması (delist DAHİL)",
            "n_sembol_gun": int(len(fazla)), "n_gun": int(len(gun_ort)),
            "n_sembol": int(pd.Series(sub["sid"].to_numpy()[ok]).nunique()),
            "dilim_turnover21_medyan": float(V.loc[V["ust"], "turnover21"].median()),
            "ham_getiri": gun_blok_bootstrap_ort(y, d),
            "evren_fazlasi": gun_blok_bootstrap_ort(fazla, d),
            "evren_fazlasi_gun_agirlikli_CI": gun_blok_bootstrap_ort(
                gun_ort.to_numpy(), gun_ort.index.to_numpy()),
            "taban_ort": (float(np.mean(b)) if len(b) else None),
        }
        blok = olcum[str(h)]["evren_fazlasi"]
        print(f"   @{h} · n={len(fazla)} gün={len(gun_ort)} · fazla ort={blok['ort']} "
              f"CI[{blok.get('lo')}, {blok.get('hi')}]", flush=True)
        satirlar = {}
        for etiket, bps in (("kart_modeli_10bps", ANAHTAR["MALIYET_BPS"]),
                            ("duyarlilik_20bps", ANAHTAR["MALIYET_BPS_DUYARLILIK"])):
            c = bps / 10000.0
            satirlar[etiket] = {
                "bps": bps, "brut": blok["ort"],
                "net": (None if blok["ort"] is None else blok["ort"] - c),
                "net_ci": (None if blok.get("lo") is None else
                           {"lo": blok["lo"] - c, "hi": blok["hi"] - c, "seviye": 0.95,
                            "sifir_disinda": bool((blok["lo"] - c) > 0 or (blok["hi"] - c) < 0)}),
                "beyan": "maliyet SABİT → CI aynı sabitle ötelendi (bootstrap koşulmadı)",
            }
        maliyet[str(h)] = satirlar
    S["olcum"] = olcum
    S["maliyet"] = maliyet
    S["fazla_kayit"] = fazla_kayit


# %%
# --- H9 — ALT-DÖNEM BETİMLEYİCİ TABLO (CI YOK) --------------------------------------
# EDG-016 çekince Ç2. Kart grid'inde alt-dönem bacağı YOK → CI BİLEREK hesaplanmadı
# (CI'lı sınansaydı K çarpılırdı). Hüküm bacağı DEĞİLDİR.

if _kapi("9"):
    alt = {"beyan": "BETİMLEYİCİ — kart grid'inde alt-dönem bacağı yok; CI bilerek "
                    "hesaplanmadı (K çarpılmasın).", "ufuklar": {}}
    for h in ANAHTAR["UFUKLAR"]:
        fazla, d, _ = S["fazla_kayit"][h]
        yil = pd.DatetimeIndex(d).year
        tab = {}
        for y in sorted(set(yil.tolist())):
            m = (yil == y)
            tab[str(y)] = {"n": int(m.sum()), "n_gun": int(pd.Series(d[m]).nunique()),
                           "fazla_ort": float(np.mean(fazla[m])) if m.sum() else None,
                           "fazla_medyan": float(np.median(fazla[m])) if m.sum() else None,
                           "pozitif_oran": float((fazla[m] > 0).mean()) if m.sum() else None}
        alt["ufuklar"][str(h)] = tab
        print(f"   @{h} alt-dönem:", {k: (round(v["fazla_ort"], 5)
                                          if v["fazla_ort"] is not None else None)
                                      for k, v in tab.items()})
    S["alt_donem"] = alt


# %%
# --- H10 — EVREN / DELİST MUHASEBESİ · SURVIVORSHIP GÖSTERGELERİ (CI YOK) -----------
# Kartın asıl sorusu: dilimdeki sonradan-delist isimler ne kadar yer tutuyor, fazlaya ne
# katıyor? tum (kayıtlı hücre) · yalniz_hayatta_kalanlar (EDG-016'nın gördüğü dünya) ·

if _kapi("10"):
    V = S["V"]
    dl = S["delist_sid"]
    B = S["panel"]
    dm = {
        "yontem": S["delist_yontemi"],
        "beyan": "BETİMLEYİCİ — CI hesaplanmadı (kayıtlı hücre TEK). Hüküm bacağı değildir.",
        "panel_sembol": int(B["sid"].nunique()),
        "cikis_muhasebesi": S["cikis_muhasebe"],
        "delist_vekili_sembol": int(len(dl)),
        "delist_vekili_pay": float(len(dl)) / max(1, int(B["sid"].nunique())),
        "kesit_delist_satir": int(V["sid"].isin(dl).sum()), "kesit_satir": int(len(V)),
        "dilim_delist_satir": int((V["ust"] & V["sid"].isin(dl)).sum()),
        "dilim_satir": int(V["ust"].sum()),
        "dilim_delist_sembol": int(V.loc[V["ust"] & V["sid"].isin(dl), "sid"].nunique()),
        "delist_fwd_olculemeyen_satir": S["delist_fwd_dusen"],
        "span_bekcisi_kapatti": S["span_bekcisi"],
        "ufuklar": {},
    }
    dm["dilim_delist_satir_pay"] = dm["dilim_delist_satir"] / max(1, dm["dilim_satir"])
    dm["delist_dilime_yogunlasiyor_mu"] = {
        "dilimdeki_delist_payi": dm["dilim_delist_satir_pay"],
        "kesitteki_delist_payi": dm["kesit_delist_satir"] / max(1, dm["kesit_satir"]),
        "okuma": "dilim payı kesit payından BÜYÜKSE yüksek-turnover dilimi delist isimleri "
                 "fazladan topluyor (EDG-016 Ç1 göstergesi; yorum Rol-1)",
    }
    for h in ANAHTAR["UFUKLAR"]:
        fazla, d, sid_ar = S["fazla_kayit"][h]
        is_dl = pd.Series(sid_ar).isin(dl).to_numpy()

        def _bet(mask, fazla=fazla, sid_ar=sid_ar):
            if mask.sum() == 0:
                return {"n": 0, "ort": None, "neden": "satır yok"}
            return {"n": int(mask.sum()), "n_sembol": int(pd.Series(sid_ar[mask]).nunique()),
                    "ort": float(np.mean(fazla[mask])), "medyan": float(np.median(fazla[mask])),
                    "pozitif_oran": float((fazla[mask] > 0).mean())}

        tum, hay, dlt = _bet(np.ones(len(fazla), bool)), _bet(~is_dl), _bet(is_dl)
        dm["ufuklar"][str(h)] = {
            "tum": tum, "yalniz_hayatta_kalanlar": hay, "yalniz_sonradan_delist": dlt,
            "survivorship_primi_vekili": (None if (hay["ort"] is None or tum["ort"] is None)
                                          else hay["ort"] - tum["ort"]),
            "okuma": "prim_vekili > 0 → delist isimleri fazlayı AŞAĞI çekiyor, yani "
                     "sağkalan-evrende ölçülen sayı yukarı çarpıktı. SAYIDIR, hüküm değil.",
        }
        sut = f"fwd{h}_delist_kapatilmis"
        if sut in V.columns:
            sub = V[V["ust"]][["tarih", "sid", sut]].dropna(subset=[sut])
            base = sub["tarih"].map(S["taban"][h])
            m2 = base.notna().to_numpy()
            fz2 = sub[sut].to_numpy(float)[m2] - base.to_numpy(float)[m2]
            dm["ufuklar"][str(h)]["duyarlilik_delist_son_fiyattan_tasfiye"] = {
                "n": int(len(fz2)), "ort": (float(np.mean(fz2)) if len(fz2) else None),
                "beyan": "delist isminin son h gününde bar yok → fwd ölçülemez; bu satır o "
                         "boşluğu 'son kapanıştan tasfiye' VARSAYIMIYLA doldurur. CI YOK, "
                         "hüküm bacağı DEĞİL.",
            }
    S["delist_muhasebe"] = dm
    print("   delist payı — dilim:", round(dm["dilim_delist_satir_pay"], 5), "kesit:",
          round(dm["delist_dilime_yogunlasiyor_mu"]["kesitteki_delist_payi"], 5))
    for h in ANAHTAR["UFUKLAR"]:
        uu = dm["ufuklar"][str(h)]
        print(f"   @{h} tüm={uu['tum']['ort']} hayatta={uu['yalniz_hayatta_kalanlar']['ort']} "
              f"delist={uu['yalniz_sonradan_delist']['ort']} "
              f"prim_vekili={uu['survivorship_primi_vekili']}")


# %%
# --- H10b — v4 KAPSAMA ÖLÇÜMÜ (KAPI YOK: DUR hâlinde de koşar) ----------------------
# Sorulan: yerel PIT listesindeki ticker, QC'nin o günkü evreninde KAÇ kez bulundu? Kaçak
# kaynakları: yeniden adlandırma/devir (QC symbol.value NOKTA-ZAMANLI ticker'dır), QC'de o gün
# fundamental kaydı olmayan isim, PANEL_N kırpması. KARTTA KAPSAMA EŞİĞİ YOKTUR → bu blok DUR
# ÜRETMEZ, yalnız SAYAR (uydurma eşik yasak); okuması Rol-1'dedir.

if globals().get("PIT_MOD") and S.get("panel") is not None:
    _yil = {}
    for _ts, _n_uye, _n_es in pit_gun_muh:
        _r = _yil.setdefault(str(pd.Timestamp(_ts).year),
                             {"gun": 0, "pit_uye_top": 0, "qc_eslesen_top": 0})
        _r["gun"] += 1
        _r["pit_uye_top"] += int(_n_uye)
        _r["qc_eslesen_top"] += int(_n_es)
    # BEDEL YASASI: yukarıdaki eşleşme KIRPMADAN ÖNCE sayılır. Panele giren satır ise
    # üst-PANEL_N kırpmasından SONRAdır ve o gün üye sayısı (~503) PANEL_N'i (500) AŞABİLİR —
    # yani en düşük dolar-hacimli birkaç üye panele hiç girmez. Kazancı ölçüp bedeli ölçmemek
    # sessiz körlüktür; ikisi de yıl yıl basılır. (Ölçüm evreni üye-içi üst-EVREN_N olduğu için
    # kırpılanlar 250. sıranın ÇOK altındadır; yine de SAYILIR, varsayılmaz.)
    _Bk = S["panel"]
    _yk = _Bk["tarih"].dt.year.astype(str)
    _gun_y = _Bk.groupby(_yk)["tarih"].nunique()
    _pu_y = _Bk.groupby(_yk)["pit_uye"].sum()
    _eu_y = _Bk.groupby(_yk)["evren_uye"].sum()
    for _y, _r in _yil.items():
        _r["pit_uye_ort"] = _r["pit_uye_top"] / max(1, _r["gun"])
        _r["qc_eslesen_ort"] = _r["qc_eslesen_top"] / max(1, _r["gun"])
        _r["oran"] = _r["qc_eslesen_top"] / max(1, _r["pit_uye_top"])
        # PAYDA TEKTİR: `gun` (kesitin kurulduğu gün sayısı). İki *_ort farklı tabana
        # bölünseydi `panel_kirpma_ort` iki ayrı paydadan çıkarma yapardı. `panel_gun` ayrıca
        # basılır: ikisi ayrışırsa fiyatı okunamayan (px yok/≤0) günler var demektir.
        _g = max(1, _r["gun"])
        _r["panel_gun"] = int(_gun_y.get(_y, 0))
        _r["panel_uye_ort"] = float(_pu_y.get(_y, 0)) / _g       # kırpmadan SONRA
        _r["evren_uye_ort"] = float(_eu_y.get(_y, 0)) / _g       # ölçüme giren
        _r["panel_kirpma_ort"] = _r["qc_eslesen_ort"] - _r["panel_uye_ort"]
    _pgun = sorted({str(pd.Timestamp(t).date()) for t in S["panel"]["tarih"].unique()})
    _veri_disi = [g for g in _pgun if not pit_veri_icinde(g)]
    S["kapsama"] = {
        "beyan": "KARTTA KAPSAMA EŞİĞİ YOK → DUR üretmez, yalnız SAYAR. Oran = QC evreninde "
                 "eşleşen / o günün PIT üye sayısı (gün gün toplanmış, KIRPMADAN ÖNCE). "
                 "panel_uye_ort kırpmadan SONRA, evren_uye_ort ölçüme GİREN satırdır.",
        "kaynak": PIT_KAYNAK, "kaynak_sha256": PIT_KAYNAK_SHA256,
        "uretim_damgasi": PIT_URETIM_DAMGASI, "butunluk": S.get("pit_butunluk"),
        "pit_havuz_ticker": len(PIT_HAVUZ), "yil": _yil,
        "toplam_oran": (sum(r["qc_eslesen_top"] for r in _yil.values())
                        / max(1, sum(r["pit_uye_top"] for r in _yil.values()))),
        "secici_sayaci": dict(PIT_SECICI_SAYAC),
        "uyelik_arama_damgasi": "Üyelik araması QC PANEL ZAMAN DAMGASIYLA yapılır "
                                "(pit_uyeler(ts), ts = universe_history indeksinden). Ölçülen "
                                "şey tarihin İNDEKSTEN geldiğidir; damganın PİYASA gününe eşit "
                                "olduğu DEĞİL — kaymayı `fiyat_capraz_kontrol."
                                "kayma_taramasi`/`en_iyi_kayma` ölçer (ilk koşumda 1g idi). "
                                "Üyelik yılda 12-19 kez değiştiği için 1 günlük kayma yalnız o "
                                "değişim günlerinde üyeliği bir gün geç okur — kapsamanın %100 "
                                "olmamasının cevap adaylarından biridir.",
        "eslesme_siniri": "QC `symbol.value` NOKTA-ZAMANLI ticker'dır (QC belgesi); yerel PIT "
                          "listesi de ticker taşır. Yeniden adlandırma/devir günlerinde iki "
                          "taraf AYRIŞABİLİR; kayıp isim orana DÜŞER — ÖLÇÜLÜR, düzeltilmez.",
        "veri_sonu": {"pit_veri_son": PIT_VERI_SON,
                      "pencere_son": str(ANAHTAR["PENCERE_SON"].date()),
                      "panel_gunu_veri_disinda": len(_veri_disi),
                      "beyan": "PIT kaynağı pencere sonundan önce bitiyorsa aşan günlerde "
                               "üyelik BİLİNMİYOR; taşıma YAPILMADI (uydurma yasağı) → o "
                               "günler evren dışında kaldı ve kesitten düştü."},
    }
    print("   KAPSAMA ·", json.dumps({y: round(r["oran"], 4) for y, r in sorted(_yil.items())},
                                     ensure_ascii=False),
          "· toplam", round(S["kapsama"]["toplam_oran"], 4),
          "· veri-dışı panel günü", len(_veri_disi))
    if _veri_disi:
        _sapma("pit_veri_sonu", f"{len(_veri_disi)} panel günü PIT verisi DIŞINDA",
               f"PIT kaynağı {PIT_VERI_SON}'da bitiyor, pencere "
               f"{ANAHTAR['PENCERE_SON'].date()}'e gidiyor; taşıma YAPILMADI")


# %%
# --- H11 — TEK JSON BLOĞU (şema: cikti_semasi.md) -----------------------------------
# DUR hâlinde de koşar: operatörün elinde iletilecek kanıt olur. JSON'da HÜKÜM YOKTUR.

def _json_guvenli(o):
    import numpy as _np
    if isinstance(o, dict):
        return {str(k): _json_guvenli(v) for k, v in o.items()}
    if isinstance(o, (list, tuple, set)):
        return [_json_guvenli(v) for v in o]
    if isinstance(o, _np.integer):
        return int(o)
    if isinstance(o, _np.floating):
        f = float(o)
        return None if (f != f or f in (float("inf"), float("-inf"))) else f
    if isinstance(o, _np.bool_):
        return bool(o)
    if isinstance(o, float):
        return None if (o != o or o in (float("inf"), float("-inf"))) else o
    if isinstance(o, (int, str, bool)) or o is None:
        return o
    try:
        import pandas as _pd
        if isinstance(o, (_pd.Timestamp, datetime)):
            return str(o)
        if isinstance(o, _pd.Series):
            return _json_guvenli(o.to_dict())
    except Exception:
        pass
    return str(o)


CIKTI = {
    "kart": "EDG-2026-021",
    "aile": "qc_delist_dogrulama",
    "defter_surumu": "v4",
    "defter_mimarisi": "TEK KAYNAK add_universe+universe_history → list[Fundamental]; evren, "
                       "fiyat, hacim, as-of hisse aynı çağrıdan. v1'in history(Fundamental)/"
                       "CoarseFundamental/get_fundamental yolları FREE hesapta BOŞ dönüyor "
                       "(QC_API_ZEMIN_GERCEGI.md) → çıkarıldı. v4: evren KAYNAĞI değişti — "
                       "dolar-hacim vekili yerine PIT S&P 500 üyeliği (yerel üyelik dosyası, "
                       "parça _d). EŞİK VE SABİTLER v3 ile AYNI (kart guard'ı); ikinci koşum "
                       "TANIM-EŞİTLEMEDİR, eşik-esnetme DEĞİLDİR.",
    "defter_sha256": None,
    "defter_sha256_neden": "koşan defter kendi kaynağını okumaz; sha256 REPO tarafında alınır",
    "rol": "ölçüm defteri — SAYI üretir, HÜKÜM VERMEZ. Eşik içermez. Hüküm Rol-1'de.",
    "kosum": {
        "zaman_utc": str(datetime.utcnow()) + "Z",
        "ortam": "QuantConnect Research (QuantBook)",
        "api_yolu": S.get("api_yolu"),
        "fundamental_alan_sondasi": S.get("fund_alan_sondasi"),
        "determinizm_sinamasi": S.get("determinizm_sinamasi"),
        "bellek_mb": S.get("bellek_mb"),
    },
    "anahtarlar": {k: (str(v) if isinstance(v, datetime) else v) for k, v in ANAHTAR.items()},
    "DUR": S.get("DUR"),
    "pozitif_kontrol": S.get("pk"),
    "evren": {
        "kaynak": ANAHTAR.get("EVREN_KAYNAGI"),
        "beyan": (
            (f"PIT S&P 500 ÜYELİĞİ (as-of gün, yerel üyelik dosyası) ∩ ÜYE-İÇİ dolar-hacim "
             f"üst-{ANAHTAR['EVREN_N']} — DELİST DAHİL (geçmiş günün QC evren kesiti; o gün "
             "borsada olan, bugün olmayan isimler İÇERİDEDİR). v3'ün dolar-hacim VEKİLİ "
             "bırakıldı: ilk koşumun hükmü 'evren-kompozisyon farkı' idi ve ikinci koşum hakkı "
             "TANIM-EŞİTLEME içindir. Eşleme TICKER üzerindendir; kapsama `evren.kapsama`da "
             "SAYILIDIR (kartta kapsama eşiği YOK → DUR üretmez).")
            if globals().get("PIT_MOD") else
            (f"GÜNLÜK dolar-hacim üst-{ANAHTAR['EVREN_N']} — DELİST DAHİL (geçmiş günün QC "
             "evren kesiti; o gün borsada olan, bugün olmayan isimler İÇERİDEDİR).")
        ) + (f" Panel üst-{ANAHTAR['EVREN_N'] * ANAHTAR['PANEL_CARPANI']} taşır; fazlası "
             "pencere sürekliliği TAMPONUDUR, ölçüm satırı yalnız evren_uye olanlardır."),
        "kapsama": S.get("kapsama"),
        "mini_sonda": S.get("mini_sonda"),
        "spx_uyelik_denemesi": S.get("spx_uyelik_denemesi"),
        "panel_muhasebesi": S.get("panel_muhasebe"),
        "kesit_muhasebesi": S.get("kesit_muhasebe"),
        "shares_muhasebesi": S.get("shares_muhasebe"),
    },
    "fiyat_capraz_kontrol": S.get("fiyat_capraz_kontrol"),
    "tanimlar": {
        "evren": (
            ("evren = PIT S&P 500 üyeliği (as-of gün) ∩ üye-içi dolar-hacim üst-"
             f"{ANAHTAR['EVREN_N']}; kaynak {globals().get('PIT_KAYNAK')} "
             f"sha256 {globals().get('PIT_KAYNAK_SHA256')}, veri "
             f"{globals().get('PIT_VERI_BAS')} → {globals().get('PIT_VERI_SON')} "
             "(AS-OF adım fonksiyonu: bir satır sonraki satıra kadar geçerli; veri sonundan "
             "sonrası TAŞINMAZ)")
            if globals().get("PIT_MOD") else
            f"evren = gün içi dolar-hacim üst-{ANAHTAR['EVREN_N']} (SPX süzgeç-vekili)"),
        "turnover21": "medyan21(hacim) / shares_outstanding(as-of t)",
        "rvol20": "hacim(t)/SMA20(hacim)[t] — payda BUGÜNÜ İÇERİR (meridian.indicators)",
        "dilim": f"gün içi turnover21 yüzdelik rütbesi > {1 - ANAHTAR['UST_PCT']}",
        "taban": "AYNI GÜN evren ortalaması (ileri getirisi tanımlı tüm evren üyeleri)",
        "fwd_h": "px(t+h)/px(t) - 1",
        "px_kaynagi": S.get("fiyat_kaynagi"),
        "sureklilik_bekcisi": f"satır-tabanlı pencere takvimde k×{ANAHTAR['SPAN_TOLERANS']} günü "
                              "aşarsa hücre ÖLÇÜLEMEZ (panelden düşüp dönen sembolde pencere "
                              "sessizce uzamasın diye)",
        "ci": f"{ANAHTAR['BLOK']} ardışık gözlem günü blok-bootstrap, %95, B={ANAHTAR['BOOT']} "
              f"(IC: {ANAHTAR['BOOT_IC']}), tohum={ANAHTAR['TOHUM']}; HEADLINE satır-ağırlıklı "
              "gün-blok (EDG-016 ile aynı). İkincil okuma AYNI araca gün-ortalaması serisi "
              "verilerek üretilir (satır=gün → gün-ağırlıklı); v1'deki kanonik "
              "olcum_araclari.blok_bootstrap_ci kopyası KARAKTER SINIRI nedeniyle çıkarıldı — "
              "fark: tohum (20260801 vs 11) ve blok kuralı (sabit 21 vs n^(1/3))",
        "maliyet": f"kart cost_model {ANAHTAR['MALIYET_BPS']}bps tek-yön; "
                   f"{ANAHTAR['MALIYET_BPS_DUYARLILIK']}bps BEYANLI DUYARLILIK",
        "K_beyani": "kart grid'i TEK katman (K+=1): qc_turnover_ust20_fazlasi. Ufuk 10/20 "
                    "horizon alanıdır, K çarpanı DEĞİL. Alt-dönem ve delist ayrıştırması "
                    "BETİMLEYİCİ, CI TAŞIMAZ.",
    },
    "tanim_sapmalari": S.get("tanim_sapmalari"),
    "olcum": {"ust20_evren_fazlasi": S.get("olcum")},
    "maliyet": S.get("maliyet"),
    "alt_donem_betimleyici": S.get("alt_donem"),
    "delist_muhasebesi": S.get("delist_muhasebe"),
    "kiyas_notu": {
        "edg_016": {"ust20_evren_fazlasi_10": 0.0031, "ust20_evren_fazlasi_20": 0.00648,
                    "net_10bps_20": 0.00548,
                    "kaynak": "wp2_olcum/RAPOR_016.md (sağkalan evren, full_251)"},
        "beyan": "EDG-016 sayıları BURADA HESAPLANMADI, kıyas için taşındı. İki ölçüm FARKLI "
                 "evrende yapıldı; fark yalnız survivorship'e atfedilemez.",
    },
    "uyarilar": S.get("uyarilar"),
    "olculemedi": S.get("olculemedi"),
}

print("\n" + "=" * 78)
print("EDG-2026-021 · SONUÇ JSON")
print("KOPYALANACAK ŞEY: aşağıdaki iki işaret ARASINDAKİ metin (işaretler DAHİL DEĞİL).")
print("kaydet: research/olcumler/qc_dogrulama/sonuc_021_v4.json")
print("=" * 78)
print("<<<SONUC_021_JSON_BASLANGIC>>>")
print(json.dumps(_json_guvenli(CIKTI), ensure_ascii=False, indent=2, sort_keys=False))
print("<<<SONUC_021_JSON_SON>>>")
print("=" * 78)
print("JSON SONU · DUR =", S.get("DUR"))
