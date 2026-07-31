"""selfreview.py — Haftalık Öz-Değerlendirme (#2) + Çelişki Dedektörü (#3).

v3→v10 telemetrisi dört panele dağılmıştı; sentezi operatör kafasında yapıyordu. Bu modül sentezi
SİSTEME verir: haftada bir (ve istendiğinde) tüm kalibrasyon/defter/bekçi sinyallerini tek raporda
toplar, kural-tabanlı bir DİKKAT listesi çıkarır ve katmanların birbiriyle ÇELİŞTİĞİ yerleri
listeler (her çelişki ya öğrenme fırsatı ya hata işareti). Rapor ayrıca ajanın kanıt paketine girer.

Rapor ayrıca DANIŞMA KATMANI MEKANİZMALARININ SAĞLIK DEFTERİdir (mechanisms): bir mekanizma çıktı
üretemiyorsa bu, boş bir rapordan ayırt edilebilir biçimde burada durur (aşağıdaki MECH_KEY notu).

Yalnız OKUR ve yazar (state/self_review.json) — hiçbir karara dokunmaz."""
from __future__ import annotations
import datetime as dt

from . import config, store, obs

REVIEW_FILE = "self_review.json"

# DANIŞMA KATMANI MEKANİZMA SAĞLIĞI — self_review.json İÇİNDE (ayrı artefakt açılmadı: tüketicisi
# olmayan yeni bir dosya bekçinin 'artifact_unread' bulgusudur). Neden var: bu iki mekanizma canlıda
# 424 + 436 koşum boyunca ÜST ÜSTE düştü, tek iz zamanlayıcıdaki obs.warn'dı ve pano "dikkat maddesi
# yok" gösteriyordu — SAKİN sistemle ARIZALI sistem ayırt edilemiyordu. Üst üste düşen bir mekanizma
# uyarı değil KESİNTİdir; sayacı burada tutulur, DİKKAT listesine düşer ve alarmlanır.
MECH_KEY = "mechanisms"


def _score_ic(sc: dict | None):
    """Skor kalibrasyonundan KARAR VERİLEBİLİR IC'yi çıkar → (ic, n, kaynak).

    2026-07-26'ya kadar burada havuzlanmış `rank_ic` okunuyordu; canlı defterde o havuz 2102 cf ile
    95 gerçek işlemi 22:1 oranında karıştırıyordu, yani "skorun tahmin gücü" diye raporlanan sayı
    fiilen ALINMAMIŞ hipotetik girişlerin IC'siydi ve bu dosya ona bakıp 'yüksek' önem derecesiyle
    dikkat satırı üretiyordu. Artık GERÇEK dilim esastır. Eski şema (yalnız `rank_ic`) yazılmış bir
    defter hâlâ okunabilsin diye geriye dönük düşüş korunur — düşüş kaynağı adıyla raporlanır."""
    if not sc:
        return None, 0, ""
    if "real" in sc:
        # YENİ ŞEMA. `real` ANAHTARI VARSA hüküm ORADADIR — değeri None olsa bile (2026-07-26).
        # Eski hâl havuza DÜŞÜYORDU: gerçek dilim <30 olduğu için ölçülememişken, dosyada duran
        # havuzlanmış IC (fiilen cf'in IC'si) devreye giriyor ve "skorun tahmin gücü" diye
        # okunuyordu. Yani "ölçemedim" cevabı, tam da yerine geçmemesi gereken sayıyla doldurulmuş
        # oluyordu. Havuza düşüş YALNIZ anahtarın hiç olmadığı GERÇEK eski-şema dosyaları için var.
        real = sc["real"]
        if isinstance(real, dict) and real.get("rank_ic") is not None:
            return real["rank_ic"], int(real.get("n") or 0), "gerçek dilim"
        return None, 0, "gerçek dilim <30 — ölçülmedi"
    if sc.get("rank_ic") is None:
        return None, 0, ""
    return sc["rank_ic"], int(sc.get("n") or 0), "havuzlanmış (eski şema)"


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def _week_ago_iso() -> str:
    return (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=7)).isoformat(timespec="seconds")


def _health() -> dict:
    h = (store.read_json(REVIEW_FILE, {}) or {}).get(MECH_KEY)
    return dict(h) if isinstance(h, dict) else {}


def mechanism_ok(name: str) -> None:
    """Mekanizma bu koşumda çıktı ÜRETTİ — seri sayacı sıfırlanır, DİKKAT satırı kalkar."""
    def _fn(doc):
        if not isinstance(doc, dict):
            return False
        doc.setdefault(MECH_KEY, {})[name] = {"ok": True, "streak": 0, "at": _now()}
        doc["attention"] = [a for a in (doc.get("attention") or [])
                            if not _is_outage_row(a, name)]
        return True
    try:
        store.update_json(REVIEW_FILE, _fn, {})
    except Exception:  # sessiz-yutma: sağlık defteri yardımcıdır; yazımı başarısız olsa bile asıl mekanizmayı düşürmez ve arıza yolu ayrıca alarmlanır
        pass


def mechanism_failed(name: str, err: BaseException) -> None:
    """Mekanizma çıktı ÜRETEMEDİ. Üç ayrı iz bırakılır ki bir daha sessizce ölmesin:
    (1) sağlık defterinde üst üste düşüş sayacı, (2) panonun okuduğu DİKKAT listesinde bir satır
    (boş rapor artık 'her şey sakin' diye okunamaz), (3) MECHANISM_STALE alarmı — bu jeton
    obs.NOTIFY_TOKENS içindedir (pano açılmadan operatöre gider) ve monitoring.sh onu grepler."""
    detail = f"{type(err).__name__}: {err}"[:200]
    box = {"streak": 1}

    def _fn(doc):
        if not isinstance(doc, dict):
            return False
        prev = (doc.get(MECH_KEY) or {}).get(name) or {}
        box["streak"] = int(prev.get("streak") or 0) + 1
        doc.setdefault(MECH_KEY, {})[name] = {"ok": False, "streak": box["streak"],
                                              "at": _now(), "error": detail}
        doc["attention"] = [_outage_row(name, detail, box["streak"])] + \
                           [a for a in (doc.get("attention") or []) if not _is_outage_row(a, name)]
        return True
    try:
        store.update_json(REVIEW_FILE, _fn, {})
    except Exception:  # sessiz-yutma: defter yazılamasa bile alarm AŞAĞIDA yine çıkar — kesinti görünürlüğü tek kanala bağlı değil
        pass
    try:
        obs.alarm("MECHANISM_STALE",
                  f"mekanizma ÜRETEMİYOR: {name} — {detail} (üst üste {box['streak']} koşum)",
                  mechanism=name, kind="failing", streak=box["streak"])
    except Exception:  # sessiz-yutma: kayıt kanalının kendisi düştü — ikinci bir kanal yok; kayıt denemesi çağıranı düşüremez
        pass


_OUTAGE_PREFIX = "MEKANİZMA ÜRETEMİYOR"


def _outage_row(name: str, detail: str, streak: int) -> dict:
    return {"why": f"{_OUTAGE_PREFIX}: {name} — {detail} (üst üste {streak} koşum)",
            "sev": "yüksek", "mechanism": name}


def _is_outage_row(row, name: str) -> bool:
    return isinstance(row, dict) and row.get("mechanism") == name \
        and str(row.get("why", "")).startswith(_OUTAGE_PREFIX)


def build() -> dict:
    """Tam rapor: hafta özeti + ilerleme sayaçları + DİKKAT + çelişkiler. Her alan dürüst:
    veri yoksa None/0 — hiçbir satır uydurulmaz."""
    since = _week_ago_iso()
    hyps = store.read_jsonl("hypotheses.jsonl")
    week_h = [h for h in hyps if str(h.get("ts") or "") >= since]
    ships = [h for h in week_h if h.get("status") in ("live", "promoted")]
    rejects = [h for h in week_h if str(h.get("status", "")).startswith("rejected")]

    from . import counterfactual as cf
    cf_rows = cf.resolved_rows(entered_only=False)
    cf_week = [r for r in cf_rows if str(r.get("resolved") or "") >= since[:10]]

    fid = store.read_json("cf_fidelity.json", None)
    shadow = (store.read_json("shadow_model.json", {}) or {}).get("promotion") or {}
    llmcal = store.read_json("llm_calibration.json", {}) or {}
    gatecal = store.read_json("gate_calibration.json", {}) or {}
    scorecal = store.read_json("score_calibration.json", None)
    exiteff = store.read_json("exit_efficiency.json", None)
    arming = store.read_json("arming_report.json", {}) or {}
    budget = store.read_json("agent_budget.json", {}) or {}
    # KÖK NEDEN BURADAYDI: ham `store.read_json("skill_revisions.json", [])` diskteki ŞEKLİ aynen
    # döndürüyordu; defter sözlük/çift-kodlanmış metin olduğunda aşağıdaki `r.get("status")` bir
    # `str` üzerinde çağrılıp raporu komple düşürüyordu. Defterin sahibi skill_evolve; tip garantisi
    # onun tek okuyucusunda (revisions()) — burada artık ŞEKİL VARSAYIMI YOK.
    from . import skill_evolve as _se
    revs = _se.revisions()

    # HAFTALIK RAPOR GERÇEKTEN HAFTAYI GÖRÜYOR MU (K1, 2026-07-30).
    #
    # ESKİ HÂL: `limit=4000` + `ts >= since` (7 gün). Süzgeç doğruydu ama PENCERE yanlıştı: 4000
    # satır nominal hacimde (~1.700/gün) ~2,3 gün, `hotstate_down` selinde ~16 SAAT ediyordu (canlı
    # ölçüm 2026-07-30: son 4000 satırın ilk damgası 07-29T05:53, istenen pencere 07-22'ye uzanmalı).
    # Sonuç: "hiçbir satır uydurulmaz" iddialı rapor `watchdog_incidents`'ı SESSİZCE eksik sayıyordu
    # — son 4000'de 7 MECHANISM_STALE vardı, defterin tamamında 100.
    #
    # YENİ HÂL: pencere TARİHE göre kurulur (store.read_jsonl zaten dosyanın tamamını okuyup
    # dilimliyor — satır limiti I/O tasarrufu etmiyordu, yalnız görüş alanını daraltıyordu).
    # Ayrıca `notify.inbox`ın ölçtüğü şey burada da ÖLÇÜLÜR: pencere kesildi mi? notify bunu
    # `window_truncated` ile raporluyordu, selfreview hiç ölçmüyordu — ve ölçmeyen rapor,
    # eksikliğini "olay yok" diye okutur.
    _all_events = store.read_jsonl("events.jsonl")
    stale_events = [e for e in _all_events
                    if e.get("alarm") == "MECHANISM_STALE" and str(e.get("ts") or "") >= since]
    _oldest_ts = str((_all_events[0].get("ts") if _all_events else "") or "")
    # Defterin EN ESKİ satırı istenen pencere başlangıcından daha yeniyse, haftanın bir kısmı
    # defterde HİÇ yok (budama/taşıma) — "0 olay" ile "0 GÖRDÜM" ayrı şeyler. Ölçülemiyorsa None.
    _truncated = (_oldest_ts > since) if _oldest_ts else None

    report = {
        "generated": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "week": {
            "reflections": len(week_h), "ships": len(ships), "rejections": len(rejects),
            "ship_details": [{"id": h.get("id"), "variable": h.get("variable"),
                              "predicted_delta": h.get("predicted_delta")} for h in ships][:5],
            "cf_resolved": len(cf_week),
            "watchdog_incidents": [{"mechanism": e.get("mechanism"), "gap_h": e.get("gap_h")}
                                   for e in stale_events][:8],
            # SAYININ DÜRÜSTLÜK ZARFI (K1): kaç olay SAYILDI, pencere kesildi mi, defterin en eski
            # damgası ne. `watchdog_incidents` en fazla 8 satır gösterir; toplam ayrıca yazılır ki
            # "8" bir tavan mı gerçek mi olduğu okunabilsin.
            "watchdog_incidents_n": len(stale_events),
            "window_truncated": _truncated,
            "window_oldest_ts": _oldest_ts or None,
            "window_since": since,
        },
        "progress": {   # her satır: "karara ne kadar kaldı?" — milestone para birimi
            "shadow_promotion": {"have": shadow.get("n_live", 0), "need": 30},
            "llm_promotion": {"have": llmcal.get("n_pairs", 0), "need": 30,
                              "sim_pairs": llmcal.get("cf_pairs", 0)},
            "meta_calibration": {"have": gatecal.get("n_measured", 0), "need": 5},
            "setup_arming": {s: {"have": v.get("n", 0), "need": 30}
                             for s, v in (arming.get("cf_report") or {}).items()},
            "cf_fidelity": {"have": (fid or {}).get("n", 0), "need": 10},
        },
        "calibrations": {"cf_fidelity": fid, "score": scorecal, "exit": exiteff,
                         "gate_meta": gatecal or None, "llm": llmcal or None},
        "agent": {"calls_today": budget.get("day", 0),
                  "revisions_pending": sum(1 for r in revs if r.get("status") == "draft")},
    }
    report["contradictions"] = contradictions()
    # Buraya gelmek = bu mekanizma ÇIKTI ÜRETTİ. Diğer mekanizmaların sağlığı TAŞINIR (rapor yazımı
    # onların kesinti kaydını silmesin — silseydi kesinti tek bir başarılı koşumla görünmez olurdu).
    # Oku-değiştir-yaz kilit altında: mechanism_ok/failed başka bir iş parçacığından gelebilir ve
    # kilitsiz yazım o kesinti kaydını sessizce geri alırdı (store.update_json aynı kilidi kullanır).
    with store.file_lock(REVIEW_FILE):
        health = _health()
        health["self_review"] = {"ok": True, "streak": 0, "at": _now()}
        report[MECH_KEY] = health
        report["attention"] = _attention(report)
        store.write_json(REVIEW_FILE, report)
    return report


def _attention(rep: dict) -> list:
    """Kural-tabanlı DİKKAT listesi — panelde ve bildirimde en üste çıkar. Kurallar yazılı ve sabit;
    'önemli görünen' değil 'eşiği geçen' listelenir."""
    out = []
    # ÖNCE KESİNTİLER: bir danışma mekanizması üretmiyorsa raporun geri kalanı EKSİK okunmalı.
    # Listenin başında dururlar ki out[:8] kırpması onları asla düşüremesin.
    for mname, mh in (rep.get(MECH_KEY) or {}).items():
        if isinstance(mh, dict) and mh.get("ok") is False:
            out.append(_outage_row(mname, str(mh.get("error") or "?"), mh.get("streak") or 1))
    cal = rep["calibrations"]
    sc = cal.get("score")
    _ic, _n, _kay = _score_ic(sc)
    # NEGATİF IC SATIRI ÜÇ KOŞULA BAĞLANDI (2026-07-26). Eskiden `_ic < 0` yetiyordu ve satır
    # canlıda sürekli "yüksek" önem derecesiyle çıkıyordu; oysa (a) kaynak havuzlanmış olabiliyor
    # (yani cf'in IC'si), (b) -0.01 gibi bir değer gürültüden ayırt EDİLEMEZKEN de satır düşüyordu.
    # Ölçülmemiş bir sinyalle operatörü strateji ağırlıklarını değiştirmeye çağırmak, dikkat
    # listesinin kendisini değersizleştirir. Üç koşul: GERÇEK dilim · anlamlılık ÖLÇÜLDÜ ve doğru ·
    # etki eşiği (-0.05) aşıldı. `anlamli` None ise (ölçülmedi) satır ÇIKMAZ — susmak dürüsttür.
    _anlamli = ((sc or {}).get("real") or {}).get("anlamli") if isinstance(sc, dict) else None
    if _kay == "gerçek dilim" and _anlamli is True and _ic is not None and _ic < -0.05:
        out.append({"why": f"skor kalibrasyonu NEGATİF (IC {_ic}, n={_n}, {_kay}, anlamlı) — "
                           "skor ağırlığı önerileri değerlendirilmeli", "sev": "yüksek"})
    fid = cal.get("cf_fidelity")
    if fid and fid.get("n", 0) >= 10 and not fid.get("fidelity_ok"):
        out.append({"why": f"cf sadakati ONAYSIZ (r={fid.get('corr')}, sapma {fid.get('mean_diff_r')}R) — "
                           "cf-beslemeli kalibrasyonları iskontolu oku", "sev": "yüksek"})
    if rep["week"]["watchdog_incidents"]:
        out.append({"why": f"{len(rep['week']['watchdog_incidents'])} bekçi olayı — mekanizma gecikmeleri",
                    "sev": "orta"})
    gm = cal.get("gate_meta") or {}
    if gm.get("extra_p"):
        out.append({"why": f"kapı kendini sıkılaştırdı (+{gm['extra_p']}) — öngörüler sistematik iyimserdi",
                    "sev": "orta"})
    ee = cal.get("exit")
    if ee and ee.get("nudge_active"):
        out.append({"why": f"çıkışta masada R kalıyor (ort {ee.get('avg_left_r')}R, en kötü {ee.get('worst_reason')})",
                    "sev": "orta"})
    for name, p in rep["progress"].items():
        if isinstance(p, dict) and p.get("need") and p.get("have", 0) >= p["need"]:
            out.append({"why": f"{name}: eşik doldu ({p['have']}/{p['need']}) — karar hazır", "sev": "yüksek"})
        elif isinstance(p, dict) and "have" not in p:      # setup_arming alt-sözlüğü
            for s2, pp in p.items():
                if pp.get("have", 0) >= pp.get("need", 10**9):
                    out.append({"why": f"silahlanma kanıtı doldu: {s2} ({pp['have']}/{pp['need']})",
                                "sev": "yüksek"})
    if rep["agent"]["revisions_pending"]:
        out.append({"why": f"{rep['agent']['revisions_pending']} revizyon taslağı onay bekliyor", "sev": "orta"})
    out += _near_miss_attention()                    # eşik-altı kanıtı → sonda önerisi (öğrenme döngüsü)
    order = {"yüksek": 0, "orta": 1}
    out.sort(key=lambda a: order.get(a["sev"], 2))
    return out[:8]


# eşik-altı ölüm-nedeni → gate-uygun ayar (near-miss → arama köprüsü, 2026-07-20)
NEAR_MISS_KNOB = {"hacim": "entry.min_volume_ratio", "rs": "entry.rs_rating_min",
                  "skor": "entry.min_score", "uzamış": "entry.pivot_proximity_pct"}
NM_MIN_N = 30          # kovada en az bu kadar SONUÇLU eşik-altı satır (cf-bootstrap sonrası yüzlerce var)
NM_MIN_AVG_R = 0.08    # ve ortalama R bu eşiği aşmalı. cf-tarih ölçtü: gerçek eşik-altı edge'ler 0.05-0.11R
                       # (RS +0.109). Eski 0.15 tavanı bu gerçek sinyalleri kaçırıyordu → 0.08'e indirildi.


def _near_miss_attention() -> list:
    """near_miss karnesi ARTIK bir karara besleniyor: bir giriş eşiğinin HEMEN ALTINDA ölen adaylar
    yeterli sayıda (n>=10) ve tutarlı POZİTİF R (avg_r>=0.15) ürettiyse, o eşiği GEVŞETMEYİ DEĞİL —
    ilgili @regime düğmesini ARAMANIN OOS kapısından geçirmesini öneren bir DİKKAT satırı çıkar. Kanıt
    zaten denenmişse (son hipotezlerde o düğme varsa) sessiz. Yetki yok: yalnız hipotez tohumu."""
    nm = store.read_json("near_miss.json", None)
    if not nm or not nm.get("buckets"):
        return []
    tried = {str(h.get("variable", "")).split("@")[0] for h in store.read_jsonl("hypotheses.jsonl")[-25:]}
    out = []
    for bucket, d in (nm["buckets"] or {}).items():
        knob = NEAR_MISS_KNOB.get(bucket)
        if not knob or knob in tried:
            continue
        n_r, avg_r = d.get("n_r", 0), d.get("avg_r")
        if n_r >= NM_MIN_N and avg_r is not None and avg_r >= NM_MIN_AVG_R:
            # HANGİ REJİM? (ikinci tur denetimi, 2026-07-21) Eskiden öneri "knob@rejim" diyordu ama
            # kanıtta rejim YOKTU (cf'nin eşik-altı satırları "?" ile yazılıyordu). Artık kanıtın en
            # güçlü rejim dilimi adlandırılır; yeterli dilim yoksa DÜRÜSTÇE global önerilir.
            slices = [(rg, v) for rg, v in (d.get("by_regime") or {}).items()
                      if rg in config.VALID_REGIMES and v.get("n_r", 0) >= NM_MIN_N
                      and v.get("avg_r") is not None and v["avg_r"] >= NM_MIN_AVG_R]
            slices.sort(key=lambda x: -x[1]["avg_r"])
            if slices:
                rg, v = slices[0]
                target, ev = f"{knob}@{rg}", f"{rg} diliminde +{v['avg_r']}R (n={v['n_r']})"
            else:
                target, ev = knob, "rejim dilimi eşiği dolduramadı — GLOBAL sonda"
            out.append({"why": f"eşik-altı '{bucket}' adayları masada +{avg_r}R bırakıyor (n={n_r}) — "
                               f"{target} sondası aramaya değer ({ev}; kapıdan geçerse gevşer)",
                        "sev": "yüksek"})
    return out


def contradictions() -> list:
    """#3 — katmanlar arası tutarlılık taraması. Her kural bir katman-ÇİFTİNİ kıyaslar; çelişki
    bulunca örnekleriyle listeler. Yeni yetki yok: liste yalnız rapora girer."""
    out = []
    # (1) gölge P(kazanç) vs LLM görüşü — aynı planda zıt sinyal
    plans = [p for p in store.read_jsonl("trade_plans.jsonl")[-60:]
             if p.get("p_win_shadow") is not None and p.get("llm_opinion")]
    clash = [(p["ticker"], p["p_win_shadow"], p["llm_opinion"]) for p in plans
             if (p["p_win_shadow"] >= 0.6 and p["llm_opinion"] == "karşı")
             or (p["p_win_shadow"] <= 0.4 and p["llm_opinion"] == "destekle")]
    if len(plans) >= 8 and len(clash) / len(plans) > 0.3:
        out.append({"pair": "gölge_model↔LLM_görüşü",
                    "detail": f"{len(plans)} planın {len(clash)}'inde zıt sinyal (ör. "
                              f"{clash[0][0]}: gölge {clash[0][1]} vs '{clash[0][2]}')",
                    "sev": "orta"})
    # (2) skor IC negatif AMA skor ağırlığı hiç denenmemiş — kanıt var, öneri yok
    sc = store.read_json("score_calibration.json", None)
    _ic2, _n2, _kay2 = _score_ic(sc)
    if _ic2 is not None and _n2 >= 30 and _ic2 < -0.05:
        tried_w = any(str(h.get("variable", "")).split("@")[0].startswith("entry.w_")
                      for h in store.read_jsonl("hypotheses.jsonl")[-25:])
        if not tried_w:
            out.append({"pair": "skor_kalibrasyonu↔arama",
                        "detail": f"IC {_ic2} (n={_n2}, {_kay2}) negatifken son 25 SUBMIT'te hiç "
                                  "entry.w_* yok — sondalar bu deftere yazılmaz, yani 'hiç "
                                  "denenmedi' demek değildir; öneriye DÖNÜŞMÜYOR demektir",
                        "sev": "yüksek"})
    # (3) cf kurulum karnesi pozitif AMA kapı ölçümü ret — beklenen dürüst gerilim, görünür olsun
    ar = store.read_json("arming_report.json", {}) or {}
    for s2, m in (ar.get("measurements") or {}).items():
        rep_s = (ar.get("cf_report") or {}).get(s2) or {}
        if str(m.get("status", "")).startswith("gate_rejected") and rep_s.get("avg_r", 0) > 0.3:
            out.append({"pair": "cf_karne↔kapı_ölçümü",
                        "detail": f"{s2}: cf ort {rep_s['avg_r']}R pozitifken kapı reddetti "
                                  f"(P={m.get('search_p')}) — cf iyimserliği ya da ince dilim", "sev": "orta"})
    # (4) çıkış dürtmesi açık AMA arama exit.* hiç sondalamıyor
    ee = store.read_json("exit_efficiency.json", None)
    if ee and ee.get("nudge_active"):
        recent_exit = any(str(h.get("variable", "")).split("@")[0].startswith("exit.")
                          for h in store.read_jsonl("hypotheses.jsonl")[-15:])
        if not recent_exit:
            out.append({"pair": "çıkış_verimliliği↔arama",
                        "detail": "MFE dürtmesi açıkken son 15 hipotezde hiç exit.* yok — dürtme etkisiz kalıyor",
                        "sev": "orta"})
    # (6) eşik-altı kanıt POZİTİF ama ilgili düğme hiç denenmemiş — kanıt öneriye dönüşmüyor
    nm = store.read_json("near_miss.json", None)
    if nm and nm.get("buckets"):
        tried6 = {str(h.get("variable", "")).split("@")[0]
                  for h in store.read_jsonl("hypotheses.jsonl")[-25:]}
        for bucket, dd in (nm["buckets"] or {}).items():
            knob = NEAR_MISS_KNOB.get(bucket)
            if knob and knob not in tried6 and dd.get("n_r", 0) >= NM_MIN_N \
                    and (dd.get("avg_r") or 0) >= NM_MIN_AVG_R:
                out.append({"pair": "eşik-altı_karne↔arama",
                            "detail": f"'{bucket}' eşik-altı adayları +{dd['avg_r']}R (n={dd['n_r']}) "
                                      f"ama son 25 hipotezde hiç {knob} yok — kanıt sondaya dönüşmüyor",
                            "sev": "yüksek"})
    # (5) LLM gerçek vs sim kalibrasyonu işaret zıtlığı
    lc = store.read_json("llm_calibration.json", {}) or {}
    rb, cb = lc.get("buckets") or {}, lc.get("cf_buckets") or {}
    if (rb.get("karşı") or {}).get("n", 0) >= 8 and (cb.get("karşı") or {}).get("n", 0) >= 15:
        r_real, r_sim = rb["karşı"]["avg_r"], cb["karşı"]["avg_r"]
        if (r_real > 0.1) != (r_sim > 0.1) and abs(r_real - r_sim) > 0.4:
            out.append({"pair": "LLM_gerçek↔LLM_sim",
                        "detail": f"'karşı' kovası gerçekte {r_real}R, simde {r_sim}R — sim kalibrasyonuna "
                                  "güvenmeden önce sadakati kontrol et", "sev": "orta"})
    return out[:6]


def weekly() -> dict:
    """Haftalık koşum (scheduler): raporu üret, en yüksek DİKKAT satırını bildirime ver.

    build() düşerse KESİNTİ kaydedilir + alarmlanır, sonra hata AYNEN yükseltilir: çağıran kendi
    uyarısını yazsın ve haftayı 'yapıldı' diye işaretlemesin (yeniden deneme davranışı korunur)."""
    try:
        rep = build()
    except Exception as e:
        mechanism_failed("self_review", e)
        raise
    obs.log("self_review_generated", ships=rep["week"]["ships"], rejections=rep["week"]["rejections"],
            attention=len(rep["attention"]), contradictions=len(rep["contradictions"]))
    try:
        from . import notify
        if notify.configured() and rep["attention"]:
            top = rep["attention"][0]["why"]
            notify.send(f"📊 Haftalık öz-değerlendirme hazır — en önemli: {top}")
    except Exception:  # sessiz-yutma: obs alarmı/kaydı bu noktada ZATEN yazıldı; ikincil bildirim kanalının (Telegram/webhook) düşmesi alarmı asla düşüremez
        pass
    return rep
