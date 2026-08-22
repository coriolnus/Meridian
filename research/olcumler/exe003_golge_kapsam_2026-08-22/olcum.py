"""EXE-2026-003 — gölge kapsam genişletme (planli kol) · ölçüm koşumu.

KART: research/cards/EXE-2026-003-golge-planli-kol.yaml (OKU-DOKUNMA).
Ölçüm ajanı karta DOKUNMAZ; hükmü Rol-1 işler. Bu betik SAYI üretir, hüküm üretmez —
motorun okuma yüzeyinin kendi ürettiği `hukum` alanları ŞASİNİN çıktısı olarak aynen taşınır.

════════ TASARIM: ŞASİ YENİDEN KURULMAZ, ÇAĞRILIR (emsal: exe006b_o1_kimlik) ════════
Kartın ölçüm şasisi motorda ZATEN yaşıyor: `meridian.intraday_shadow` modülünün saf okuma
yüzeyi (`kollar` / `planli_kol_uretimi` / `golge_cf_eslestirme`) + gerçek-çift hattı
(`meridian.faz5_cikis.cikis_olcumu`). Eşleştirme anahtarı, ikinci elek, tarih-kümeli
bootstrap (B=10.000), n_min ve pencere sabitleri HEP o modüllerde donuk — burada onların
bir kopyasını yazmak, iki gövdenin sessizce ayrışması demek olurdu (R1'in tam da ölçtüğü
sınıf). Bu betiğin yaptığı TEK şey: canlı defterlerin salt-okunur kopyası üzerinde o
yüzeyi çağırmak + kartın şema/kill kanıtlarını (kol alanı, anahtar kümeleri, nüfus
bağlamı) defter kopyalarından saymak.

════════ VERİ KAYNAĞI: CANLI state/ SALT-OKUNUR KOPYA ════════
Kart canlı defterleri ölçer (yerel state/ 30 Temmuz'da donuk — orada planli defter HİÇ YOK).
Kopyalar `canli_state/` altında (KOMUT.txt'de çekim komutları; scp salt-okunur, canlıya tek
bayt yazılmadı). `config.STATE` BU dizine çevrilir — `store._state()` ve `storage.db_path()`
her çağrıda config'ten okur; bu, depo mimarisinin ölçüm sandbox'ları için AÇIKÇA tasarladığı
yoldur (store.py:42, storage.py:128 docstring'leri). Yani ana checkout'un state/'ine ve
canlıya hiçbir yazım yolu yoktur; modüllerin obs kayıtları bile sandbox'a düşer.

DAĞITIM KANITI (v217 canlıya iniş): /opt/meridian/meridian/intraday_shadow.py
mtime = 2026-08-16 20:13 UTC (SSH ls -la, 2026-08-22; KOMUT.txt). İlk planli obs olayı
2026-08-20T13:31Z, canlı events.jsonl'de 5 `intraday_shadow_planli_order` / 0 `_failed`.
"""
import importlib
import json
import pathlib
import statistics
import sys
from datetime import datetime

BURASI = pathlib.Path(__file__).resolve().parent
REPO = BURASI.parents[2]
SANDBOX = BURASI / "canli_state"
sys.path.insert(0, str(REPO))

# v217'nin canlıya indiği gün (kanıt modül başlığında). Şemanın önce/sonra kıyası bu sınırla.
DAGITIM_TARIHI = "2026-08-16"


def _sandbox_kur():
    """`config.STATE` → canli_state kopyası. Motor dosyalarına DOKUNULMAZ; yalnız modül
    niteliği çevrilir (storage/store her çağrıda buradan okur — tasarlanmış sandbox yolu)."""
    from meridian import config
    config.STATE = SANDBOX
    assert str(config.STATE) == str(SANDBOX), "sandbox yönlendirmesi tutmadı"
    return config


def _yas(dosya: str) -> str | None:
    """Kopyanın taşıdığı verinin KENDİ tazeliği (kopyalama anı değil): son satırın ts/date'i."""
    p = SANDBOX / dosya
    if not p.exists():
        return None
    son = None
    with open(p, encoding="utf-8") as f:
        for satir in f:
            if satir.strip():
                son = satir
    if son is None:
        return None
    r = json.loads(son)
    return r.get("ts") or r.get("date") or r.get("decision_as_of")


def sema_kaniti() -> dict:
    """Kill#3 + birincil 'bayt-düzeyi etkilenmez' kanıtı — DEFTER KOPYALARINDAN SAYILIR.

    'Değişmedi' iddiasının ölçülebilir hâli: (1) silahli defterin HİÇBİR satırında `kol`
    alanı yok; (2) dağıtım ÖNCESİ ve SONRASI silahli satırlar AYNI anahtar kümesini taşıyor
    (v217 satır GÖVDESİNE dokunmadı iddiasının canlı-veri sınaması); (3) planli satır kümesi
    tam olarak silahli + {kol} (iki kol `_satir()`in tek gövdesinden çıkıyor iddiası);
    (4) silahli deftere planli satır SIZMADI (gerçek-çift hattının girdisi kirlenmedi)."""
    sil = [json.loads(l) for l in open(SANDBOX / "intraday_shadow_orders.jsonl", encoding="utf-8")]
    pla = [json.loads(l) for l in open(SANDBOX / "intraday_shadow_planli_orders.jsonl", encoding="utf-8")]
    sil_once = [r for r in sil if (r.get("date") or "") < DAGITIM_TARIHI]
    sil_sonra = [r for r in sil if (r.get("date") or "") >= DAGITIM_TARIHI]
    kume = lambda rows: sorted({tuple(sorted(r.keys())) for r in rows})
    ks_once, ks_sonra = kume(sil_once), kume(sil_sonra)
    kp = kume(pla)
    return {
        "silahli_n": len(sil), "silahli_once_n": len(sil_once), "silahli_sonra_n": len(sil_sonra),
        "planli_n": len(pla),
        "silahli_kol_alani_tasiyan": sum(1 for r in sil if "kol" in r),
        "silahli_anahtar_kumesi_once": [list(k) for k in ks_once],
        "silahli_anahtar_kumesi_sonra": [list(k) for k in ks_sonra],
        "silahli_sema_once_sonra_ozdes": ks_once == ks_sonra and len(ks_once) == 1,
        "planli_esittir_silahli_arti_kol": (
            len(kp) == 1 and len(ks_once) == 1
            and set(kp[0]) - set(ks_once[0]) == {"kol"} and set(ks_once[0]) - set(kp[0]) == set()),
        "planli_kol_disi_status": sorted({r.get("status") for r in pla}),
    }


def nufus_baglami() -> dict:
    """4a kararlar defterinden PAYDA: dağıtımdan beri seans × tetiği-kesilen-silahlanmamış plan.

    'Defterde 2 seans var' cümlesi tek başına iki şeyi ayırt edemez: fırsat yoktu / kol
    yazmadı. 4a defteri (`fired` + `eod_armed`) fırsatı bağımsız sayar — kolun yazım oranı
    (yazılan satır ÷ fırsat) buradan çıkar."""
    firsat: dict[str, set] = {}
    for satir in open(SANDBOX / "intraday_decisions.jsonl", encoding="utf-8"):
        r = json.loads(satir)
        d = (r.get("ts") or "")[:10]
        if d >= DAGITIM_TARIHI and r.get("fired") and not r.get("eod_armed"):
            firsat.setdefault(d, set()).add(r.get("plan_id"))
    pla = [json.loads(l) for l in open(SANDBOX / "intraday_shadow_planli_orders.jsonl", encoding="utf-8")]
    yazilan: dict[str, set] = {}
    for r in pla:
        yazilan.setdefault(r.get("date"), set()).add(r.get("plan_id"))
    gunler = sorted(set(firsat) | set(yazilan))
    tablo = {g: {"firsat_n": len(firsat.get(g, ())), "yazilan_n": len(yazilan.get(g, ())),
                 "kacirilan": sorted(firsat.get(g, set()) - yazilan.get(g, set()))}
             for g in gunler}
    tf = sum(v["firsat_n"] for v in tablo.values())
    ty = sum(v["yazilan_n"] for v in tablo.values())
    return {"dagitimdan_beri": tablo, "toplam_firsat": tf, "toplam_yazilan": ty,
            "yazim_orani": (round(ty / tf, 4) if tf else None),
            "yazim_orani_olculemedi_nedeni": (None if tf else "dağıtımdan beri fırsat 0 — oran tanımsız")}


def kill1_gecikme() -> dict:
    """Kill#1 (p95 döngü süresi +%10): KARTIN METRİĞİ ÖLÇÜLEMEDİ — motorda döngü-süresi
    enstrümanı YOK (tarandı: intraday_cycle/loop'ta perf_counter/monotonic yok; tek gecikme
    telemetrisi store.py'nin YAZIM p95'i, o da döngü süresi değil ve dağıtım-öncesi tabanı
    süreç ömrüyle sınırlı). UYDURMA YASAĞI: None + neden.

    VEKİL (kartın metriği DEĞİL, hüküm beslemez; yalnız kaba işaret): silahli satırların
    bar-kapanışı → karar damgası gecikmesi (decision_as_of − close_ts), dağıtım öncesi/sonrası.
    Payda küçük (11 satır) ve ölçtüğü şey döngünün tamamı değil tek plan dalıdır — sınır beyanlı."""
    sil = [json.loads(l) for l in open(SANDBOX / "intraday_shadow_orders.jsonl", encoding="utf-8")]

    def _lag(r):
        try:
            a = datetime.fromisoformat(str(r["decision_as_of"]))
            b = datetime.fromisoformat(str(r["close_ts"]).replace("Z", "+00:00"))
            return (a - b).total_seconds()
        except (KeyError, ValueError, TypeError):
            return None

    once = [x for r in sil if (r.get("date") or "") < DAGITIM_TARIHI and (x := _lag(r)) is not None]
    sonra = [x for r in sil if (r.get("date") or "") >= DAGITIM_TARIHI and (x := _lag(r)) is not None]
    ozet = lambda v: (None if not v else
                      {"n": len(v), "ort_s": round(statistics.fmean(v), 3),
                       "min_s": round(min(v), 3), "max_s": round(max(v), 3)})
    return {"p95_dongu_suresi_degisimi": None,
            "olculemedi_nedeni": ("motorda döngü-süresi enstrümanı yok; tek gecikme telemetrisi "
                                  "(store.io_latency, yazım-p95) döngü süresi değil ve dağıtım-öncesi "
                                  "taban geriye dönük kurulamaz"),
            "vekil_karar_gecikmesi_s": {"sinir": ("VEKİL — kartın metriği değil; silahli satır başına "
                                                  "bar-kapanış→karar damgası; tek dal, n küçük"),
                                        "dagitim_oncesi": ozet(once), "dagitim_sonrasi": ozet(sonra)}}


def cf_bekleyen_teshisi(ikincil: dict, satirlar: list[dict]) -> dict:
    """`cf_yok` sınıfının KÖKÜ: cf defteri yalnız KAPANMIŞ karşı-olgusalları taşır
    (counterfactual.collect → cf_open.json → çözülünce counterfactuals.jsonl). Eşleşmeyen
    gölge satırının karşılığı `cf_open.json`da BEKLİYORSA bu bir kapsam deliği değil,
    boru-hattı gecikmesidir (zaman stopu dolunca kendiliğinden kapanır). İkisi ayrı sınıftır
    ve ayrı raporlanır — 'cf_yok' tek kova olarak okunursa ikincil hat kırık sanılırdı.
    YALNIZ şasinin `eslesmeyen.sinif == cf_yok` dediği satırlar sınanır; sınıf tanımı şasinin."""
    from meridian.intraday_shadow import _plan_tarihi
    acik = json.load(open(SANDBOX / "cf_open.json", encoding="utf-8"))
    acik_anahtar = {(str(r.get("date")), str(r.get("ticker") or "").upper()) for r in acik}
    satir_by_ad = {f"{r.get('plan_id') or '?'}·{r.get('date') or '?'}·{r.get('kol') or '?'}": r
                   for r in satirlar}
    bekleyen, acikta_da_yok, ad_cozulemedi = [], [], []
    for e in ((ikincil.get("eslesmeyen") or {}).get("nedenler") or []):
        if e.get("sinif") != "cf_yok":
            continue
        r = satir_by_ad.get(e.get("ad"))
        if r is None:
            ad_cozulemedi.append(e.get("ad"))
            continue
        anah = (_plan_tarihi(r.get("plan_id")), str(r.get("ticker") or "").upper())
        (bekleyen if anah in acik_anahtar else acikta_da_yok).append(e.get("ad"))
    return {"cf_open_n": len(acik), "cf_yok_bekleyen": sorted(bekleyen),
            "bekleyen_n": len(bekleyen), "acikta_da_yok": sorted(acikta_da_yok),
            "ad_cozulemedi": ad_cozulemedi,
            "not": ("bekleyen = karşılığı cf_open.json'da AÇIK duran cf_yok satırı (cf kapanınca "
                    "eşleşebilir — boru-hattı gecikmesi); acikta_da_yok = ne kapanmışta ne açıkta "
                    "karşılığı olan cf_yok satırı (gerçek kapsam sorusu)")}


def main() -> int:
    smoke = "--smoke" in sys.argv
    _sandbox_kur()
    from meridian import intraday_shadow as gs

    k = gs.kollar()
    tazelik = {d: _yas(d) for d in ("intraday_shadow_orders.jsonl",
                                    "intraday_shadow_planli_orders.jsonl",
                                    "counterfactuals.jsonl", "intraday_decisions.jsonl")}
    print(f"kablo: kollar() → n={k['n']} etiketsiz={k['etiketsiz_n']} · veri tazeliği={tazelik}")
    if smoke:
        # KABLO SINAMASI: sandbox yönlendirmesi tutuyor mu, defterler okunuyor mu, kol sayımları
        # canlıda elle sayılanla (silahli 11 · planli 5) uyuşuyor mu. Ölçüm ÜRETMEZ.
        rapor = {"kart": "EXE-2026-003", "smoke": True, "kollar_n": k["n"],
                 "etiketsiz_n": k["etiketsiz_n"], "veri_tazeligi": tazelik,
                 "sandbox": str(SANDBOX)}
        yol = BURASI / "sonuc_smoke.json"
    else:
        birincil_uretim = gs.planli_kol_uretimi()                       # ŞASİ — pencere+dolum+kendi hükmü
        ikincil = gs.golge_cf_eslestirme(satirlar=k["satirlar"])        # ŞASİ — eşleştirme+B=10.000
        from meridian import faz5_cikis
        gercek_cift = faz5_cikis.cikis_olcumu()                         # ŞASİ — EXE-2026-002 hattı, yalnız silahli okur
        # kill#4 bilgi durumu: iki hattın işaret kıyası 40+ çift İSTER — sayılar burada, kıyas Rol-1'de
        rapor = {"kart": "EXE-2026-003", "smoke": False, "sandbox": str(SANDBOX),
                 "dagitim_kaniti": {"tarih": DAGITIM_TARIHI,
                                    "kaynak": "/opt/meridian/meridian/intraday_shadow.py mtime "
                                              "2026-08-16 20:13 UTC (SSH ls, 2026-08-22) + ilk planli "
                                              "obs olayı 2026-08-20T13:31Z (canlı events.jsonl)"},
                 "veri_tazeligi": tazelik,
                 "kollar_n": k["n"], "etiketsiz_n": k["etiketsiz_n"],
                 "birincil_planli_uretim": birincil_uretim,
                 "birincil_sema_kaniti": sema_kaniti(),
                 "nufus_baglami_4a": nufus_baglami(),
                 "ikincil_golge_cf": ikincil,
                 "ikincil_cf_yok_teshisi": cf_bekleyen_teshisi(ikincil, k["satirlar"]),
                 "gercek_cift_hatti_exe002": {k2: gercek_cift.get(k2) for k2 in ("gecer", "durum", "neden", "esik")},
                 "gercek_cift_olcum_ozeti": {k2: v for k2, v in (gercek_cift.get("olcum") or {}).items()
                                             if k2 in ("n_defter", "n_evren", "n_eslesen", "ortalama_bps",
                                                       "ci", "ortalama_R", "n_min")},
                 "kill1_gecikme": kill1_gecikme()}
        yol = BURASI / "sonuc.json"
    yol.write_text(json.dumps(rapor, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    print(f"yazıldı: {yol}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
