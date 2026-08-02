"""EDG-2026-021 · QC defteri v3 — PARÇA B/3 (H2 evren+mini-sonda · H2b panel · H3 fiyat · H4)

TEK BAŞINA KOŞMAZ. Sıra: _a.py → _b.py → _c.py, hepsi AYNI namespace'e:
    for _p in ("a", "b", "c"):
        exec(open(f"qc_defter_021_{_p}.py").read(), globals())
"""

if "ANAHTAR" not in globals() or "S" not in globals():
    raise RuntimeError("ÖNCE qc_defter_021_a.py koşmalı (aynı namespace) — sıra: a → b → c")
S["_parca_b_yuklendi"] = True

# %%
# --- H2 — PANEL: universe_history YIL YIL (TEK KAYNAK) ------------------------------
# DELİST-DAHİLLİK KENDİLİĞİNDEN: panel geçmiş bir GÜNÜN kesitinden kurulur (bugünün listesi
# geçmişe taşınmaz). TAMPON: seçici üst-(EVREN_N×PANEL_CARPANI) alır, ÖLÇÜM evreni yine

if _kapi("2"):
    PANEL_N = int(ANAHTAR["EVREN_N"] * ANAHTAR["PANEL_CARPANI"])

    def _secici(fundamental):
        try:
            s = sorted(fundamental, key=lambda f: -(f.dollar_volume or 0.0))
        except Exception:
            s = list(fundamental)
        return [f.symbol for f in s[:PANEL_N]]

    # TAZE-QB (canlı ölçüm): evren örneği burada, SIFIRDAN kurulur. Üzerinde başka hiçbir
    # çağrı yapılmaz — add_equity/set_start_date gibi mutasyonlar universe_history'yi
    # sessizce boşaltıyor (v2'nin H2-DUR'unun kök nedeni).
    QB_PANEL = QuantBook()
    u = QB_PANEL.add_universe(_secici)
    S["api_yolu"]["evren"] = "TAZE QuantBook() + add_universe(secici) + universe_history"
    S["api_yolu"]["qb_panel"] = "QuantBook() — yalnız universe_history (paylaşılmaz)"

    def _sonda_say(seri):
        """Series[list[Fundamental]] içindeki toplam kayıt sayısı."""
        n = 0
        try:
            for _a, _d in seri.items():
                try:
                    n += len(list(_d))
                except Exception:
                    continue
        except Exception:
            return 0
        return n

    # KENDİNİ-DOĞRULAYAN AÇILIŞ: 7 yıllık boş çekim bir daha yaşanmasın diye panelden ÖNCE
    # aynı örnek + aynı seçiciyle SONDA_GUN günlük mini-sonda koşar. Satır yoksa HEMEN DUR.
    sonda = {"pencere_gun": ANAHTAR["SONDA_GUN"], "n_kayit": None, "neden": None,
             "beyan": "aynı QB_PANEL örneği ve aynı seçiciyle; panel çekimiyle birebir aynı yol"}
    try:
        _ss = QB_PANEL.universe_history(
            u, ANAHTAR["PENCERE_BAS"],
            ANAHTAR["PENCERE_BAS"] + timedelta(days=int(ANAHTAR["SONDA_GUN"])))
        sonda["n_kayit"] = _sonda_say(_ss)
        del _ss
    except Exception as e:
        sonda["neden"] = f"{type(e).__name__}: {e}"
    S["mini_sonda"] = sonda
    print(f"   MİNİ-SONDA ({ANAHTAR['SONDA_GUN']}g): n_kayit={sonda['n_kayit']} "
          f"neden={sonda['neden']}")
    if not sonda["n_kayit"]:
        S["DUR"] = ("QuantBook örneği evren döndürmüyor — taze örnek kuralı ihlal/etkisiz. "
                    f"{ANAHTAR['SONDA_GUN']} günlük mini-sonda 0 kayıt verdi "
                    f"({sonda['neden'] or 'hata yok, boş Series döndü'}). 7 yıllık panel çekimi "
                    "KOŞTURULMADI. Kontrol: QB_PANEL taze mi, üzerinde add_equity/"
                    "set_start_date çağrıldı mı, seçici Symbol listesi döndürüyor mu.")
        _olculemedi("panel", S["DUR"])


# %%
# --- H2b — PANEL ÇEKİMİ (yıl yıl) ---------------------------------------------------
# Mini-sonda geçtiyse koşar. Fundamental nesneleri TUTULMAZ: her dilimden yalnız gerekli
# alanlar çıkarılıp DataFrame'e yazılır, sonra Series serbest bırakılır (bellek).

if _kapi("2b"):

    SYM_KUTUGU, TICKER = {}, {}

    def _f_sayi(f, ad):
        try:
            v = float(getattr(f, ad))
        except Exception:
            return None
        return v if np.isfinite(v) else None

    def _f_hisse(f):
        """as-of hisse → (deger|None, kaynak): 1=company_profile.shares_outstanding (BİRİNCİL,
        SEVİYE) · 2=basic_average_shares.value (VEKİL, AĞIRLIKLI ORT.) · 0=ölçülemedi."""
        try:
            v = float(f.company_profile.shares_outstanding)
            if np.isfinite(v) and v > 0:
                return v, 1
        except Exception:
            pass
        try:
            v = float(f.earning_reports.basic_average_shares.value)
            if np.isfinite(v) and v > 0:
                return v, 2
        except Exception:
            pass
        return None, 0

    _SONDA_YOLLARI = ("price", "value", "adjusted_price", "price_factor", "split_factor",
                      "price_scale_factor", "dollar_volume", "volume", "market_cap",
                      "has_fundamental_data", "company_profile.shares_outstanding",
                      "earning_reports.basic_average_shares.value",
                      "security_reference.exchange_id")

    def _sonda(f):
        """Alan sondası: hangi alanlar GERÇEKTEN var? H3'ün bölünme kararı buna dayanır."""
        rap = {}
        for yol in _SONDA_YOLLARI:
            o = f
            try:
                for p in yol.split("."):
                    o = getattr(o, p)
                rap[yol] = (o if isinstance(o, (int, float, bool)) or o is None else str(o))
            except Exception as e:
                rap[yol] = f"<yok: {type(e).__name__}>"
        return rap

    dilimler = []
    _t = ANAHTAR["PENCERE_BAS"]
    while _t <= ANAHTAR["PENCERE_SON"]:
        _son = min(datetime(_t.year, 12, 31), ANAHTAR["PENCERE_SON"])
        dilimler.append((_t, _son))
        _t = datetime(_t.year + 1, 1, 1)
    if ANAHTAR["YIL_LIMIT"]:
        dilimler = dilimler[:int(ANAHTAR["YIL_LIMIT"])]
        _sapma("panel_dilimleri", f"ilk {len(dilimler)} yıl dilimi",
               "YIL_LIMIT daraltıldı — koşum kart penceresinin TAMAMI DEĞİLDİR")

    S["fiyat_alani"] = "price"          # H3 gerekirse değiştirir
    parcalar, dilim_muh = [], []
    for di, (t0, t1) in enumerate(dilimler):
        try:
            seri = QB_PANEL.universe_history(u, t0, t1)
        except Exception as e:
            _uyar(f"{t0.date()}–{t1.date()} universe_history başarısız ({type(e).__name__}: {e})")
            dilim_muh.append({"dilim": f"{t0.date()}/{t1.date()}", "n_gun": 0, "n_satir": 0,
                              "neden": f"{type(e).__name__}: {e}"})
            continue
        kayit = []
        n_gun, n_ham = 0, []
        try:
            ogeler = list(seri.items())
        except Exception:
            ogeler = []
        for anahtar, deger in ogeler:
            if deger is None:
                continue
            try:
                lst = list(deger)
            except Exception:
                continue
            if not lst:
                continue
            if "fund_alan_sondasi" not in S:
                S["fund_alan_sondasi"] = _sonda(lst[0])
                _ap = S["fund_alan_sondasi"].get("adjusted_price")
                if isinstance(_ap, (int, float)) and not isinstance(_ap, bool) \
                        and np.isfinite(float(_ap)) and float(_ap) > 0:
                    S["fiyat_alani"] = "adjusted_price"
                print("   ALAN SONDASI:", json.dumps(S["fund_alan_sondasi"], ensure_ascii=False),
                      "\n   → panel fiyat alanı:", S["fiyat_alani"], flush=True)
            PXA = S["fiyat_alani"]
            ts = pd.Timestamp(anahtar[-1] if isinstance(anahtar, tuple) else anahtar).normalize()
            # 1) TÜM üyeden yalnız dollar_volume okunur ve üst-N kırpılır (nesne tutulmaz)
            aday = []
            for f in lst:
                dv = _f_sayi(f, "dollar_volume")
                if dv is None or dv <= 0:
                    continue
                aday.append((dv, f))
            if not aday:
                continue
            n_ham.append(len(lst))
            n_gun += 1
            aday.sort(key=lambda z: -z[0])
            # 2) kalan alanlar YALNIZ üst-N için okunur
            for dv, f in aday[:PANEL_N]:
                px = _f_sayi(f, PXA)
                if px is None or px <= 0:
                    continue
                sym = f.symbol
                sid = _sid(sym)
                if sid not in SYM_KUTUGU:
                    SYM_KUTUGU[sid] = sym
                    try:
                        TICKER[sid] = str(sym.value)
                    except Exception:
                        TICKER[sid] = sid
                sh, sk = _f_hisse(f)
                kayit.append((ts, sid, dv, px, _f_sayi(f, "volume"), sh, sk))
        del seri, ogeler
        gc.collect()
        if kayit:
            d = pd.DataFrame(kayit, columns=["tarih", "sid", "dolar_hacim", "fiyat",
                                            "hacim", "shares", "shares_kaynak"])
            for c, tp in (("dolar_hacim", "float64"), ("fiyat", "float64"),
                          ("hacim", "float64"), ("shares", "float64"),
                          ("shares_kaynak", "int8")):
                d[c] = pd.to_numeric(d[c], errors="coerce").astype(tp)
            parcalar.append(d)
        dilim_muh.append({"dilim": f"{t0.date()}/{t1.date()}", "n_gun": n_gun,
                          "n_satir": len(kayit),
                          "n_ham_medyan": (float(np.median(n_ham)) if n_ham else None),
                          "neden": (None if kayit else "satır çıkmadı")})
        print(f"   panel dilim {di + 1}/{len(dilimler)} · {t0.date()}→{t1.date()} · gün={n_gun} "
              f"satır={len(kayit)} ham_medyan={(int(np.median(n_ham)) if n_ham else None)}",
              flush=True)
        del kayit

    if not parcalar:
        S["DUR"] = ("PANEL KURULAMADI — universe_history hiçbir yıl diliminde satır döndürmedi. "
                    f"Dilim muhasebesi: {dilim_muh}")
        _olculemedi("panel", S["DUR"])
        S["dilim_muhasebe"] = dilim_muh
    else:
        B = pd.concat(parcalar, ignore_index=True)
        del parcalar
        gc.collect()
        B = B.drop_duplicates(subset=["sid", "tarih"], keep="first")
        B = B.sort_values(["tarih", "sid"], kind="mergesort").reset_index(drop=True)
        # ÖLÇÜM EVRENİ: gün içi dolar-hacim rütbesi ≤ EVREN_N (tampon HARİÇ)
        B["dv_rutbe"] = B.groupby("tarih")["dolar_hacim"].rank(ascending=False,
                                                              method="first").astype("int32")
        B["evren_uye"] = (B["dv_rutbe"] <= ANAHTAR["EVREN_N"]).to_numpy()
        B = B.sort_values(["sid", "tarih"], kind="mergesort").reset_index(drop=True)
        S["panel"] = B
        S["sym_kutugu"] = SYM_KUTUGU
        S["ticker"] = TICKER
        S["dilim_muhasebe"] = dilim_muh
        kesit = B.groupby("tarih")["evren_uye"].sum()
        S["panel_muhasebe"] = {
            "satir": int(len(B)), "gun": int(B["tarih"].nunique()),
            "sembol": int(B["sid"].nunique()),
            "tarih_araligi": [str(B["tarih"].min().date()), str(B["tarih"].max().date())],
            "panel_ust_n": PANEL_N, "olcum_evreni_ust_n": ANAHTAR["EVREN_N"],
            "evren_uye_satir": int(B["evren_uye"].sum()),
            "gunluk_evren_buyuklugu": {"medyan": float(kesit.median()), "min": int(kesit.min()),
                                       "maks": int(kesit.max())},
            "fiyat_alani": S["fiyat_alani"],
            "hacim_dolu_satir": int(B["hacim"].notna().sum()),
            "shares_kaynak_dagilimi": {str(k): int(v) for k, v in
                                       B["shares_kaynak"].value_counts().sort_index().items()},
            "shares_kaynak_kodlari": {
                "0": "ölçülemedi (her iki alan da boş/0) → hücre None",
                "1": "company_profile.shares_outstanding — BİRİNCİL, nokta-zamanlı SEVİYE",
                "2": "earning_reports.basic_average_shares.value — VEKİL, AĞIRLIKLI ORTALAMA"},
            "dilim_muhasebesi": dilim_muh,
            "bellek_mb": round(B.memory_usage(deep=True).sum() / 1e6, 1),
        }
        print("   PANEL HAZIR ·", json.dumps(S["panel_muhasebe"], ensure_ascii=False))
        _nv = int((B["shares_kaynak"] == 2).sum())
        if _nv:
            _sapma("shares_outstanding", f"{_nv} hücrede basic_average_shares vekili",
                   "company_profile boş/0 idi; basic_average_shares AĞIRLIKLI ORTALAMA'dır ve "
                   "EDG-016 bunu SEVİYE olarak REDDEDER")

        # SPX/ETF kesişimi: yalnız vekilin SPX'e ne kadar yaklaştığını ÖLÇER (TANI).
        spx = {"denendi": True, "basarili": False, "yol": None, "n_kesisim": None, "neden": None,
               "karar": "kesişim yalnız TANIDIR; evren dolar-hacim üst-N vekilidir",
               "qb": "TAZE QuantBook() — QB_PANEL kirletilmesin diye ayrı örnek"}
        try:
            QB_SPX = QuantBook()          # TAZE: add_equity örnek durumunu değiştirir
            _sp = QB_SPX.add_equity("SPY", RES_DAILY)
            _h = QB_SPX.universe_history(QB_SPX.universe.etf(_sp.symbol),
                                         ANAHTAR["PENCERE_SON"] - timedelta(days=10),
                                         ANAHTAR["PENCERE_SON"])
            _sids = set()
            for _a, _d in list(_h.items()):
                try:
                    for _c in list(_d):
                        _sids.add(_sid(_c.symbol))
                except Exception:
                    continue
            if _sids:
                _uye = set(B.loc[(B["tarih"] == B["tarih"].max()) & B["evren_uye"], "sid"])
                spx.update({"basarili": True, "yol": "universe.etf(SPY)/universe_history",
                            "n_spx": len(_sids), "n_kesisim": len(_sids & _uye),
                            "n_son_gun_evren": len(_uye)})
                print(f"   SPX/ETF üyeliği ALINDI: n={len(_sids)} · kesişim={len(_sids & _uye)}"
                      f"/{len(_uye)}")
            else:
                spx["neden"] = "ETF üyelik verisi boş döndü"
        except Exception as e:
            spx["neden"] = f"{type(e).__name__}: {e}"
        if not spx["basarili"]:
            print(f"   SPX/ETF üyeliği ALINAMADI ({spx['neden']})")
        _sapma("large_cap_suzgeci", f"günlük dolar-hacim üst-{ANAHTAR['EVREN_N']} (delist dahil)",
               "evren birebir SPX üyeliği DEĞİL, süzgeç-vekilidir (kartın izin verdiği yol); "
               f"SPX kesişim tanısı: {spx.get('n_kesisim')}")
        S["spx_uyelik_denemesi"] = spx


# %%
# --- H3 — FİYAT SERİSİ ÇAPRAZ-KONTROLÜ (zaman kayması + bölünme) --------------------
# SORU (varsayım değil, ÖLÇÜM): panelin fiyat serisi ileri getiri için yeterli mi?
#  (a) ZAMAN KAYMASI ölçümü bozmaz — öznitelik de ileri getiri de AYNI indeksten kurulur;

if _kapi("3"):
    B = S["panel"]
    ornek = list(B.groupby("sid").size().sort_values(ascending=False)
                 .index[:int(ANAHTAR["CAPRAZ_SEMBOL"])])
    cap = {"ornek_sembol": [S["ticker"].get(s, s) for s in ornek],
           "fiyat_alani": S["fiyat_alani"], "tol": ANAHTAR["CAPRAZ_TOL"],
           "maks_oran": ANAHTAR["CAPRAZ_MAKS_ORAN"],
           "beyan": "günlük GETİRİ kıyası (seviye değil); kayma k=0,1,2,-1 taranır"}
    H, hata = _bar_cek([S["sym_kutugu"][s] for s in ornek],
                       ANAHTAR["PENCERE_BAS"], ANAHTAR["PENCERE_SON"])
    S["fiyat_kaynagi"] = "panel"
    if H is None:
        cap["kosuldu"] = False
        cap["neden"] = f"qb.history çağrısı: {hata}"
        _uyar(f"fiyat çapraz-kontrolü KOŞMADI ({hata}) — panel serisi DOĞRULANMADI")
        _sapma("fiyat_serisi", f"panel {S['fiyat_alani']} (doğrulanmadı)",
               "çapraz-kontrol çağrısı işlemedi; bölünme düzeltmesi ve zaman kayması "
               "ÖLÇÜLEMEDİ — ileri getiri bölünme günlerinde sapabilir")
        _olculemedi("fiyat_capraz_kontrolu", cap["neden"])
        B["px"] = B["fiyat"]
    else:
        cap["kosuldu"] = True
        P = B[B["sid"].isin(ornek)][["sid", "tarih", "fiyat"]].sort_values(["sid", "tarih"])
        gp = P.groupby("sid", sort=False)
        P["ret_p"] = gp["fiyat"].pct_change()
        P["_bos"] = (P["tarih"] - gp["tarih"].shift(1)).dt.days
        P = P[(P["_bos"] <= 5) & P["ret_p"].notna()]        # yalnız ardışık seans çiftleri
        H = H.sort_values(["sid", "tarih"])
        gh = H.groupby("sid", sort=False)
        H["ret_h"] = gh["close_h"].pct_change()
        taramalar = {}
        for k in (0, 1, 2, -1):
            Hk = H.assign(tarih=gh["tarih"].shift(-k))[["sid", "tarih", "ret_h"]].dropna()
            m = P.merge(Hk, on=["sid", "tarih"], how="inner").dropna(subset=["ret_p", "ret_h"])
            if len(m) == 0:
                taramalar[str(k)] = {"n": 0, "sapan_oran": None, "neden": "kesişim boş"}
                continue
            fark = np.abs(m["ret_p"].to_numpy() - m["ret_h"].to_numpy())
            taramalar[str(k)] = {"n": int(len(m)),
                                 "sapan_oran": float((fark > ANAHTAR["CAPRAZ_TOL"]).mean()),
                                 "n_sapan_buyuk": int((fark > ANAHTAR["CAPRAZ_BUYUK_TOL"]).sum()),
                                 "maks_fark": float(fark.max()),
                                 "fark_medyan": float(np.median(fark))}
        cap["kayma_taramasi"] = taramalar
        gecerli = {k: v for k, v in taramalar.items() if v.get("sapan_oran") is not None}
        if not gecerli:
            cap["en_iyi_kayma"] = None
            cap["neden"] = "hiçbir kaymada kesişim kurulamadı"
            _uyar("fiyat çapraz-kontrolü kesişim kuramadı — panel serisi DOĞRULANMADI")
            _sapma("fiyat_serisi", f"panel {S['fiyat_alani']} (doğrulanmadı)", cap["neden"])
            B["px"] = B["fiyat"]
        else:
            k_iyi, v_iyi = min(gecerli.items(), key=lambda kv: (kv[1]["sapan_oran"], -kv[1]["n"]))
            k_iyi = int(k_iyi)
            cap["en_iyi_kayma"] = k_iyi
            cap["en_iyi"] = v_iyi
            # İKİ KAPI: (i) küçük farkların ORANI (temettü/yuvarlama) eşiği aşmayacak,
            # (ii) BÜYÜK fark SIFIR olacak. Bölünme seyrektir (sembol başına bir gün) ve
            cap["yeter"] = bool(v_iyi["sapan_oran"] <= ANAHTAR["CAPRAZ_MAKS_ORAN"]
                                and v_iyi["n_sapan_buyuk"] == 0)
            print(f"   çapraz-kontrol · en iyi kayma={k_iyi} · n={v_iyi['n']} · "
                  f"sapan_oran={v_iyi['sapan_oran']:.5f} · büyük sapan="
                  f"{v_iyi['n_sapan_buyuk']} (maks {v_iyi['maks_fark']:.4f}) → "
                  f"panel yeter={cap['yeter']}")
            if k_iyi != 0:
                _sapma("panel_zaman_kaymasi", f"{k_iyi} gün",
                       "öznitelik ve ileri getiri aynı indeksten kurulduğu için ölçüm içsel "
                       "tutarlı ve ileri-bakış yok — sinyal bu kadar GECİKMELİ okunmuş sayılır")
            if cap["yeter"]:
                B["px"] = B["fiyat"]
                S["fiyat_kaynagi"] = f"panel {S['fiyat_alani']} (çapraz-kontrol GEÇTİ)"
            elif k_iyi != 0:
                S["DUR"] = (f"FİYAT SERİSİ YETERSİZ *VE* ZAMAN KAYMASI VAR (k={k_iyi}): panel "
                            "bölünme/temettü düzeltmesi taşımıyor, history tamiri ise kaymalı "
                            "birleştirme gerektiriyor — bu defterde TANIMLI DEĞİL. Uydurma "
                            "hizalama YASAK; düzeltme Rol-1 kararıdır.")
                _olculemedi("ileri_getiri", S["DUR"])
            else:
                _sapma("fiyat_serisi", "qb.history düzeltilmiş kapanış (tam tamir)",
                       f"panel {S['fiyat_alani']} çapraz-kontrolde sapan_oran="
                       f"{v_iyi['sapan_oran']:.5f} ve {v_iyi['n_sapan_buyuk']} BÜYÜK sapma "
                       f"(maks {v_iyi['maks_fark']:.4f}) verdi → bölünme/temettü düzeltmesi "
                       "taşımıyor; ileri getiri history'den kuruldu")
                sids = list(B["sid"].unique())
                parca = [sids[i:i + ANAHTAR["PARCA"]] for i in range(0, len(sids), ANAHTAR["PARCA"])]
                topla, basarisiz = [], 0
                for pi, p in enumerate(parca):
                    d, e = _bar_cek([S["sym_kutugu"][s] for s in p],
                                    ANAHTAR["PENCERE_BAS"], ANAHTAR["PENCERE_SON"])
                    if d is None:
                        basarisiz += 1
                    else:
                        topla.append(d)
                    if pi % 5 == 0 or pi == len(parca) - 1:
                        print(f"   history tamiri {pi + 1}/{len(parca)} parça", flush=True)
                if not topla:
                    S["DUR"] = ("FİYAT TAMİRİ BAŞARISIZ — panel serisi yetersiz ve qb.history "
                                "hiçbir parçada veri döndürmedi; ileri getiri ÖLÇÜLEMEZ")
                    _olculemedi("ileri_getiri", S["DUR"])
                else:
                    HH = pd.concat(topla, ignore_index=True).drop_duplicates(
                        subset=["sid", "tarih"], keep="last")
                    B = B.merge(HH, on=["sid", "tarih"], how="left")
                    n_bos = int(B["close_h"].isna().sum())
                    B["px"] = B["close_h"]
                    S["fiyat_kaynagi"] = "qb.history düzeltilmiş kapanış (tamir)"
                    cap["tamir"] = {"parca": len(parca), "basarisiz_parca": basarisiz,
                                    "eslesmeyen_panel_satiri": n_bos,
                                    "beyan": "eşleşmeyen satırda px None → ileri getiri "
                                             "ÖLÇÜLEMEZ (doldurulmadı)"}
                    print(f"   history tamiri tamam · eşleşmeyen satır={n_bos}")
    S["fiyat_capraz_kontrol"] = cap
    if not S["DUR"]:
        if "px" not in B.columns:
            B["px"] = B["fiyat"]
        S["panel"] = B
        print("   fiyat kaynağı:", S["fiyat_kaynagi"])


# %%
# --- H4 — ÖZNİTELİKLER + SÜREKLİLİK BEKÇİLERİ + DELİST VEKİLİ -----------------------
# EDG-016 / meridian.indicators birebir: rvol20(t)=hacim(t)/SMA20(hacim)[t] (payda BUGÜNÜ
# İÇERİR) · med_hacim21(t)=medyan(hacim[t-20..t]) · fwd_h(t)=px(t+h)/px(t)-1. Geriye

if _kapi("4"):
    B = S["panel"]
    g = B.groupby("sid", sort=False)
    TOL = float(ANAHTAR["SPAN_TOLERANS"])
    bekci = {}

    def _geri_gecerli(k):
        """k satırlık GERİYE pencerenin takvim yayılımı tolerans içinde mi?"""
        return ((B["tarih"] - g["tarih"].shift(k - 1)).dt.days <= (k - 1) * TOL).to_numpy()

    kr = int(ANAHTAR["RVOL_PENCERE"])
    sma = g["hacim"].transform(lambda s: s.rolling(kr, min_periods=kr).mean())
    ok = _geri_gecerli(kr)
    ham = B["hacim"] / sma
    B["rvol20"] = ham.where(ok & (sma > 0))
    bekci["rvol20_span_kapatti"] = int((ham.notna() & ~ok).sum())

    kt = int(ANAHTAR["TURNOVER_PENCERE"])
    med = g["hacim"].transform(lambda s: s.rolling(kt, min_periods=kt).median())
    ok = _geri_gecerli(kt)
    B["med_hacim21"] = med.where(ok)
    bekci["med_hacim21_span_kapatti"] = int((med.notna() & ~ok).sum())

    for h in ANAHTAR["UFUKLAR"]:
        ileri = g["px"].transform(lambda s, h=h: s.shift(-h) / s - 1.0)
        okf = ((g["tarih"].shift(-h) - B["tarih"]).dt.days <= h * TOL).to_numpy()
        B[f"fwd{h}"] = ileri.where(okf)
        bekci[f"fwd{h}_span_kapatti"] = int((ileri.notna() & ~okf).sum())

    # DELİST VEKİLİ: erken biten sembol "çıkış adayı"dır ama çıkış SEBEBİ panelden ayırt
    # edilemez (delist mi, dolar-hacim sıralamasından düşüş mü). Ayırt edici ÇIKIŞ RÜTBESİ:
    # üst-EVREN_N içindeyken kaybolan isim, kuyrukta solarak çıkandan delist'e yakındır.
    son_bar = B.groupby("sid")["tarih"].max()
    panel_son = B["tarih"].max()
    esik = panel_son - pd.Timedelta(days=int(ANAHTAR["DELIST_TAMPON_GUN"] * 1.6))
    cikis_rutbe = B.sort_values(["sid", "tarih"]).groupby("sid").tail(1).set_index("sid")["dv_rutbe"]
    erken = set(son_bar[son_bar < esik].index)
    aday = {s for s in erken if int(cikis_rutbe.get(s, 10 ** 9)) <= ANAHTAR["EVREN_N"]}
    delist_sid = set(aday)
    S["delist_sid"] = delist_sid
    S["cikis_muhasebe"] = {"erken_cikan": len(erken), "yuksek_rutbe_aday": len(aday),
                           "dusuk_rutbe_cikis": len(erken) - len(aday)}
    S["delist_yontemi"] = (
        f"VEKİL: son panel günü panel sonundan >{ANAHTAR['DELIST_TAMPON_GUN']} iş günü önce "
        f"biten VE o gün dolar-hacim rütbesi üst-{ANAHTAR['EVREN_N']} içinde olan semboller "
        "(kuyrukta solarak evrenden düşenler böylece elenir). "
        "QC map-file/Delisting olayı SORULMADI (API yolu ölçülmedi) ve çıkış sonrası bar "
        "aranmadı — bu bir VEKİLDİR; gerçek delist'i veri/likidite kesintisinden ya da "
        "evrenden düşüşten kesin AYIRAMAZ.")
    _sapma("delist_tespiti", "panel-çıkış + çıkış-rütbesi vekili", S["delist_yontemi"])

    # Delist isminin son h günü için fwd TANIMSIZ (bar yok) → satır düşer, SAYILIR.
    # H10'da 'son fiyattan tasfiye' duyarlılığı ayrı satır olarak okunur.
    dusen = {}
    sonf = g["px"].transform("last")
    for h in ANAHTAR["UFUKLAR"]:
        m = B["sid"].isin(delist_sid) & B[f"fwd{h}"].isna() & B["px"].notna()
        dusen[str(h)] = int(m.sum())
        B[f"fwd{h}_delist_kapatilmis"] = B[f"fwd{h}"].where(
            B[f"fwd{h}"].notna(), (sonf / B["px"] - 1.0).where(m))
    S["delist_fwd_dusen"] = dusen
    S["span_bekcisi"] = bekci

    for c in (["rvol20", "med_hacim21"]
              + [f"fwd{h}" for h in ANAHTAR["UFUKLAR"]]
              + [f"fwd{h}_delist_kapatilmis" for h in ANAHTAR["UFUKLAR"]]):
        if c in B.columns:
            B[c] = B[c].astype("float32")
    B = B.drop(columns=[c for c in ("close_h",) if c in B.columns])
    S["panel"] = B
    S["bellek_mb"] = {"H4_oznitelikli": round(B.memory_usage(deep=True).sum() / 1e6, 1)}
    print(f"   öznitelikler · rvol20={int(B['rvol20'].notna().sum())} "
          f"med_hacim21={int(B['med_hacim21'].notna().sum())} "
          f"fwd20={int(B['fwd20'].notna().sum())} · bellek≈{S['bellek_mb']['H4_oznitelikli']} MB")
    print(f"   süreklilik bekçisi kapattı: {bekci}")
    print(f"   çıkış muhasebesi: {S['cikis_muhasebe']} · delist vekili={len(delist_sid)} · "
          f"delist yüzünden fwd düşen satır={dusen}")

