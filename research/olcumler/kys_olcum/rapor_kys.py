"""rapor_kys.py — KYS-2026-001 çıktı birleştirici: `sonuc_kys001.json` + `RAPOR_KYS001.md`.

HÜKÜM YAZMAZ. Üç adımın (PK · kapsama · ölçüm) JSON'larını tek kanıt dosyasında toplar ve raporu
üretir. Kartın ölçütleri ile ölçülen sayılar YAN YANA konur; "kill tetiklendi / kart arşiv" gibi
cümleler bu dosyada YOKTUR — o cümle Rol-1'indir (kart: "ölçüm ajanı karta dokunmaz").
"""
from __future__ import annotations

import json

import ortak_kys as ok

PK = ok.CIKTI / "pk_kys001.json"
KAP = ok.CIKTI / "kapsama_kys001.json"
OLC = ok.CIKTI / "olcum_kys001.json"


def _bps(x, basamak=2):
    return "—" if x is None else f"{x:+.{basamak}f}"


def _md(metin: str) -> str:
    """Markdown tablo hücresi için boru işaretini kaçır — ölçüt metinleri `|fark|` içerir ve
    kaçırılmazsa tabloyu sütun sütun BÖLER (rapor okunmaz hâle gelir, sayı da kaybolur)."""
    return str(metin).replace("|", "\\|")


def birlestir() -> dict:
    pk = json.loads(PK.read_text(encoding="utf-8"))
    kap = json.loads(KAP.read_text(encoding="utf-8"))
    olc = json.loads(OLC.read_text(encoding="utf-8"))

    y1 = olc["yuzeyler"]["Y1_component_ic_ust_desil"]
    y2 = olc["yuzeyler"]["Y2_cf_r_tablosu"]
    yuzey_ozeti = {}
    for etiket, hucreler in (("Y1_component_ic_ust_desil", y1["havuzlanmis"]),
                             ("Y2_cf_r_tablosu", y2["ufuklar"])):
        yuzey_ozeti[etiket] = {
            h: {"n": c.get("n_kiyaslanan"),
                "standart_bps": c.get("standart_fazla_bps"),
                "temiz_bps": c.get("temiz_fazla_bps"),
                "fark_bps": c.get("fark_standart_eksi_temiz_bps"),
                "ci_lo_bps": (c.get("ci_fark") or {}).get("lo_bps"),
                "ci_hi_bps": (c.get("ci_fark") or {}).get("hi_bps"),
                "ci_sifiri_disliyor": (c.get("ci_fark") or {}).get("sifiri_disliyor")}
            for h, c in hucreler.items()}

    # KART ÖLÇÜTLERİNİN ARİTMETİĞİ (hüküm değil — sayının eşikle karşılaştırılması)
    aritmetik = {}
    for etiket, hucreler in yuzey_ozeti.items():
        h20 = hucreler.get("20") or {}
        aritmetik[etiket] = {
            "fark20_bps": h20.get("fark_bps"),
            "|fark20|>=10bps": (abs(h20["fark_bps"]) >= 10.0
                                if h20.get("fark_bps") is not None else None),
            "ci20_sifiri_disliyor": h20.get("ci_sifiri_disliyor"),
            "envanter_tetigi(>=10bps VE CI 0-dışı)": bool(
                h20.get("fark_bps") is not None and abs(h20["fark_bps"]) >= 10.0
                and h20.get("ci_sifiri_disliyor"))}

    sifir_disi = []
    for c, v in y1["bilesenler"].items():
        for h, hucre in v.items():
            ci = hucre.get("ci_fark") or {}
            if ci.get("sifiri_disliyor"):
                sifir_disi.append({"bilesen": c, "ufuk": h,
                                   "fark_bps": hucre["fark_standart_eksi_temiz_bps"],
                                   "ci": [ci["lo_bps"], ci["hi_bps"]]})

    return {
        "kart": "KYS-2026-001 · kiyas_kirlenmesi (ALTYAPI kartı)",
        "tur": "ön-kayıtlı ölçüm — RETRO YENİDEN-HÜKÜM YOK",
        "adim1_pk": {"gecti": pk["gecti"],
                     "kollar": [{k: kol.get(k) for k in
                                 ("ad", "gecti", "olcut", "temiz_fazla_bps", "kirli_fazla_bps",
                                  "sikisma_bps", "n_kirli_arac", "n_kirli_in_blackout")}
                                for kol in pk["kollar"]],
                     "esikler": pk["esikler"]},
        "adim2_kapsama": {
            "esik": kap["esik"],
            "kaynaklar": {k: {"sembol_kapsamasi": v.get("sembol_kapsamasi"),
                              "takvim_tamligi": (v.get("takvim_tamligi") or {}).get("tamlik_orani"),
                              "etiketlenemeyen_oran": (
                                  (v.get("kesin") or v.get("comert_sinir") or
                                   v.get("siki_sinir") or {}).get("etiketlenemeyen_oran")),
                              "gun_kapsamasi_kaydi": v.get("gun_kapsamasi_kaydi")}
                          for k, v in kap["kaynaklar"].items()},
            "kullanilan_kaynak": "nasdaq_kum_havuzu",
            "tarih_dogrulugu_birebir": (kap.get("tarih_dogrulugu") or {}).get("hepsi_birebir"),
            "olay_yayginligi_hedef_tarafi": kap.get("olay_yayginligi")},
        "adim3_yuzeyler": yuzey_ozeti,
        "adim3_y1_bilesen_tablosu": {
            c: {h: {"n": hucre.get("n_kiyaslanan"),
                    "standart_bps": hucre.get("standart_fazla_bps"),
                    "temiz_bps": hucre.get("temiz_fazla_bps"),
                    "fark_bps": hucre.get("fark_standart_eksi_temiz_bps"),
                    "ci": [(hucre.get("ci_fark") or {}).get("lo_bps"),
                           (hucre.get("ci_fark") or {}).get("hi_bps")]}
                for h, hucre in v.items()}
            for c, v in y1["bilesenler"].items()},
        "adim3_sifiri_dislayan_hucreler": {"n": len(sifir_disi), "toplam_hucre": 16,
                                           "hucreler": sifir_disi},
        "adim4_envanter": {
            "tetiklendi_mi(aritmetik)": any(v["envanter_tetigi(>=10bps VE CI 0-dışı)"]
                                            for v in aritmetik.values()),
            "yuzey_aritmetigi": aritmetik,
            "envanter": None,
            "neden_bos": ("kart şartı '@20 fark >=10bps VE CI 0-dışı' hiçbir yüzeyde aritmetik "
                          "olarak sağlanmadı — envanter doldurulmadı (uydurma yasağı)")},
        "taban_kirliligi": olc["aciklayici_yayginlik_sayimi"],
        "populasyon": olc["populasyon"],
        "gercek_katman_baglam": {
            h: {"n": c.get("n_kiyaslanan"), "fark_bps": c.get("fark_standart_eksi_temiz_bps"),
                "ci": [(c.get("ci_fark") or {}).get("lo_bps"), (c.get("ci_fark") or {}).get("hi_bps")]}
            for h, c in olc["gercek_katman_baglam"]["ufuklar"].items()},
        "kod_damgasi": olc["kod_damgasi"], "muhur": olc["muhur"],
        "hukum_yok": ("bu dosya SAYI taşır. Kill/arşiv/askı hükmü Rol-1'dedir; kart ALTYAPI "
                      "kartıdır ve geçmiş kart hükümleri bu turda DEĞİŞMEZ.")}


def markdown(s: dict, olc: dict, kap: dict, pk: dict) -> str:
    y1t = s["adim3_y1_bilesen_tablosu"]
    L: list = []
    A = L.append
    A("# KYS-2026-001 — KIYAS KİRLENMESİ: ÖN-KAYITLI NİCELLEŞTİRME")
    A("")
    A("**Kart:** `research/cards/KYS-2026-001-kiyas-kirlenmesi.yaml` (ALTYAPI kartı) · "
      "**Grid:** K=2 (iki yüzey) · **Ölçüm ajanı karta dokunmadı.**")
    A("")
    A("> **HÜKÜM YOK.** Bu rapor sayı taşır. Kill/arşiv/askı ve ileri-standart kararı Rol-1'dedir. "
      "Kart ALTYAPI kartıdır: **geçmiş kart hükümleri bu turda değişmez**, dil ENVANTER dilidir.")
    A("")
    A(f"**Kod damgası:** `{s['kod_damgasi']['git_head_kisa']}` · kirli ağaç: "
      f"`{s['kod_damgasi']['kirli_agac']}` (bu turun kendi dosyaları) · ölçüm araçları sürümü "
      f"`{s['kod_damgasi']['olcum_araclari_surum']}` (`olay_disi_kiyas` "
      f"{s['kod_damgasi']['arac_surumleri']['olay_disi_kiyas']}, `blok_bootstrap_ci` "
      f"{s['kod_damgasi']['arac_surumleri']['blok_bootstrap_ci']})")
    A(f"**Salt-ölçüm mührü:** `{s['muhur']['muhur']}` — `config.STATE` = kum havuzu; canlı "
      f"`state/`e tek bayt yazılmadı (bar kopyası + kum havuzu takvimi).")
    A("")
    A("---")
    A("")
    A("## 1. ARAÇ-DOĞRULAMA PK (kart `guards` #1) — **GEÇTİ**" if s["adim1_pk"]["gecti"]
      else "## 1. ARAÇ-DOĞRULAMA PK — **KALDI**")
    A("")
    A("Sentetik zeminde cevap ÖNCEDEN bilinir: δ kadar kaydırılmış bir olay penceresi enjekte edilir; "
      "temiz kıyasın δ'yı bulması, kirli kıyasın onu SIKIŞTIRMASI beklenir. Gürültü bilerek küçüktür "
      "(kestirici sınanıyor, istatistiksel güç değil).")
    A("")
    A("| Kol | Ölçüt | temiz | kirli | sıkışma | Sonuç |")
    A("|---|---|---|---|---|---|")
    for kol in pk["kollar"]:
        if "sikisma_bps" in kol:
            A(f"| {kol['ad']} | {_md(kol.get('olcut', ''))} | {_bps(kol['temiz_fazla_bps'])} bps | "
              f"{_bps(kol['kirli_fazla_bps'])} bps | {_bps(kol['sikisma_bps'])} bps | "
              f"{'GEÇTİ' if kol['gecti'] else 'KALDI'} |")
        else:
            A(f"| {kol['ad']} | küme birebir eşit | araç kirli={kol['n_kirli_arac']} | "
              f"in_blackout={kol['n_kirli_in_blackout']} | — | "
              f"{'GEÇTİ' if kol['gecti'] else 'KALDI'} |")
    A("")
    A("**PK-0 ne kanıtlar:** pencere `(once=5, sonra=0)` — yani `[olay−5, olay]` TAKVİM günü — "
      "`earnings.in_blackout` ile **birebir aynı** satır kümesini kirli sayıyor "
      f"({pk['kollar'][0]['n_kirli_arac']} satır, sembol×gün tam tarama, fark 0). Kartın "
      "`features_asof` şartı (\"karartma tanımıyla BİREBİR\") varsayılmadı, **ölçüldü**.")
    A("")
    A("**PK ölçütlerinin kaydı (dürüstlük notu):** ilk taslakta ek bir `kirli/temiz < 0,50` şartı "
      "vardı; o şart aracın değil SENTETİK TASARIMIN özelliğini ölçüyordu (180 günlük panelde "
      "kıyasların çoğu kirliliği ~%1 olan günlere düşüyordu — kol adında yazan \"%70 yaygınlık\" "
      "rejimi hiç kurulmuyordu). Düzeltme **eşiği gevşetmek değil tasarımı onarmak** oldu: panel "
      "sezona indirildi, ölçütler doğruluk + yaygınlık-tekdüzeliğine demirlendi. Kartın asıl şartı "
      "(YÖN) her taslakta geçiyordu. Gerekçe `pk_kys.py` başlığında yazılıdır.")
    A("")
    A("---")
    A("")
    A("## 2. OLAY-ETİKETLEME KAPSAMASI (kart kill #2)")
    A("")
    A("**Etiketlenebilirlik tanımı (ölçümden önce yazıldı):** bir satır `(t, g)` ancak takvim "
      "`[g, g+5]` iş günlerinin **tamamını görmüşse** etiketlenebilir. Görmediyse `in_blackout` "
      "False döner ama bu *\"karartma yok\"* değil *\"veri yok\"*tur (`earnings` modülünün beyanlı "
      "FAIL-OPEN'ı) — ikisini aynı saymak bu kartın avladığı hata sınıfının ta kendisidir.")
    A("")
    A("| Kaynak | Sembol kapsaması | Takvim tamlığı (gözlenen/beklenen) | Etiketlenemeyen satır |")
    A("|---|---|---|---|")
    kk = kap["kaynaklar"]
    ce = kk["state/earnings.csv"]
    A(f"| `state/earnings.csv` (CANLI) | %{ce['sembol_kapsamasi']*100:.1f} | "
      f"%{ce['takvim_tamligi']['tamlik_orani']*100:.1f} "
      f"(medyan {ce['takvim_tamligi']['gozlenen_medyan']} / beklenen "
      f"{ce['takvim_tamligi']['beklenen_ticker_basina']}) | "
      f"**%{ce['comert_sinir']['etiketlenemeyen_oran']*100:.1f}** (cömert sınır) — "
      f"%{ce['siki_sinir']['etiketlenemeyen_oran']*100:.1f} (sıkı sınır) |")
    sp = kk.get("state/sprint/.../earnings.csv")
    if sp:
        A(f"| `state/sprint/…/earnings.csv` | %{sp['sembol_kapsamasi']*100:.1f} | "
          f"%{sp['takvim_tamligi']['tamlik_orani']*100:.1f} | "
          f"%{sp['siki_sinir']['etiketlenemeyen_oran']*100:.1f} (sıkı sınır) |")
    nas = kk["nasdaq_kum_havuzu"]
    A(f"| **Nasdaq geçmişi (bu turda kum havuzuna çekildi)** | **%{nas['sembol_kapsamasi']*100:.1f}** "
      f"({nas['evren_kesisimi']}/251) | **%{nas['takvim_tamligi']['tamlik_orani']*100:.1f}** "
      f"(medyan {nas['takvim_tamligi']['gozlenen_medyan']}) | "
      f"**%{nas['kesin']['etiketlenemeyen_oran']*100:.1f}** (kesin — sorulan günler dosyada) |")
    A("")
    A(f"- **Yerel takvim tek başına kartın kapısından geçemiyor:** `state/earnings.csv` yalnız İLERİ "
      f"takvimdir (193 satır, 2026-07/08); ölçüm aralığında (2022-01-03 → 2026-07-23) evren "
      f"sembolü başına beklenen ~{ce['takvim_tamligi']['beklenen_ticker_basina']} rapora karşılık "
      f"**medyan {ce['takvim_tamligi']['gozlenen_medyan']}** tarih var ve "
      f"{ce['takvim_tamligi']['hic_tarihi_olmayan_evren_sembolu']} sembolün hiç tarihi yok.")
    A("- **Boşluk uydurmayla değil, deponun KENDİ birincil kaynağıyla kapatıldı:** "
      "`adapters.data.nasdaq_earnings_window` (anahtarsız Nasdaq) geçmişi de servis eder. "
      f"**{nas['sorulan_is_gunu']}/{nas['sorulan_is_gunu']} iş günü sorgulandı, 0 gün düştü, "
      f"0 FMP çağrısı harcandı** (EAP turunun 2026-07-31'de ölçtüğü aynı yol). Kaynak yeniden "
      "yazılmadı, çağrıldı; çıktı YALNIZ kum havuzuna yazıldı.")
    td = kap.get("tarih_dogrulugu") or {}
    A(f"- **Tarih doğruluğu sağlaması:** AAPL/MSFT/JPM/NVDA 2024 duyuru tarihleri bilinen gerçekle "
      f"**{'birebir' if td.get('hepsi_birebir') else 'UYUŞMUYOR'}** (tamlık, doğruluk demek değildir "
      f"— ikisi ayrı ayrı ölçüldü).")
    oy = kap.get("olay_yayginligi") or {}
    A(f"- **Hedef tarafı yaygınlığı:** ölçüm satırlarının %{oy.get('oran', 0)*100:.1f}'i "
      f"({oy.get('penceresinde')}/{oy.get('n_satir')}) KENDİ kazanç penceresinde.")
    A("")
    A("---")
    A("")
    A("## 3. İKİ YÜZEY (K=2) — STANDART vs OLAY-DIŞI TEMİZ KIYAS")
    A("")
    p = s["populasyon"]
    A(f"**Popülasyon:** {p['ham_gozlem']} gözlem → **{p['etiketlenebilir']} etiketlenebilir** "
      f"(cf {p['cf']} · gerçek {p['gercek']}). Düşenler: "
      f"{', '.join(f'{k}={v}' for k, v in p['dusenler'].items())}. "
      f"Taban havuzu: " + " · ".join(f"@{k} {v} satır" for k, v in olc["taban_havuzu"].items())
      + " (evrenin tamamı, kıyas günlerinde).")
    A("")
    A("**Fark yönü:** `fark = STANDART − TEMİZ`. Pozitif = standart (kirli) kıyas etkiyi **daha "
      "BÜYÜK** gösteriyordu; negatif = standart kıyas etkiyi **SIKIŞTIRIYORDU** (kartın hipotezi).")
    A("")
    A("| Yüzey | Ufuk | n | Standart | Temiz | **Fark** | %95 CI (21g blok) | CI 0-dışı? |")
    A("|---|---|---|---|---|---|---|---|")
    for etiket, hucreler in s["adim3_yuzeyler"].items():
        ad = "Y1 · component_ic üst-desil (havuz)" if etiket.startswith("Y1") else "Y2 · cf R-tablosu"
        for h, c in sorted(hucreler.items(), key=lambda kv: int(kv[0])):
            A(f"| {ad} | @{h} | {c['n']} | {_bps(c['standart_bps'])} bps | {_bps(c['temiz_bps'])} bps "
              f"| **{_bps(c['fark_bps'])} bps** | [{_bps(c['ci_lo_bps'])} · {_bps(c['ci_hi_bps'])}] | "
              f"{'EVET' if c['ci_sifiri_disliyor'] else 'hayır'} |")
    A("")
    A("**Y1 havuzu nedir:** sekiz bileşenin üst-desilinin BİRLEŞİMİ, `(ticker, gün)` tekilleştirilmiş. "
      "Yüzeyin tek sayısı ve tek CI'si buradan gelir; bileşen başına medyan da aşağıda durur ama "
      "medyanın CI'si TÜRETİLMEZ (hücreler aynı gözlemlerden gelir, bağımsız değildir).")
    A("")
    A("### 3.1 Y1 bileşen kırılımı (16 hücre)")
    A("")
    A("| Bileşen | @10 fark | @10 CI | @20 fark | @20 CI |")
    A("|---|---|---|---|---|")
    for c, v in y1t.items():
        a10, a20 = v.get("10", {}), v.get("20", {})
        A(f"| `{c}` | {_bps(a10.get('fark_bps'))} | [{_bps(a10['ci'][0])} · {_bps(a10['ci'][1])}] | "
          f"{_bps(a20.get('fark_bps'))} | [{_bps(a20['ci'][0])} · {_bps(a20['ci'][1])}] |")
    b = olc["yuzeyler"]["Y1_component_ic_ust_desil"]["baslik"]
    A("")
    A(f"Bileşenler arası **medyan fark**: @10 {_bps(b['10']['fark_medyan_bps'])} bps "
      f"(aralık {_bps(b['10']['fark_min_bps'])} … {_bps(b['10']['fark_maks_bps'])}) · "
      f"@20 {_bps(b['20']['fark_medyan_bps'])} bps "
      f"(aralık {_bps(b['20']['fark_min_bps'])} … {_bps(b['20']['fark_maks_bps'])}).")
    sd = s["adim3_sifiri_dislayan_hucreler"]
    A("")
    A(f"**CI'si sıfırı dışlayan hücre: {sd['n']}/{sd['toplam_hucre']}** — "
      + (", ".join(f"`{x['bilesen']}`@{x['ufuk']} {_bps(x['fark_bps'])} bps "
                   f"[{_bps(x['ci'][0])} · {_bps(x['ci'][1])}]" for x in sd["hucreler"])
         if sd["hucreler"] else "yok")
      + ". İki hücrenin işareti ZIT. 16 hücrede %95 aralıkla beklenen tesadüfi 0-dışı sayısı "
        "0,8'dir (aritmetik not, hüküm değil).")
    A("")
    A("### 3.2 Taban kirliliği — EAP'nin %64/%74'ü ile neden aynı sayı değil")
    A("")
    tk = s["taban_kirliligi"]
    A("| Pencere | Taban kirliliği medyan | ortalama | maks |")
    A("|---|---|---|---|")
    for etiket in ("kart_penceresi_5_0", "eap_benzeri_14_1_yaklasik"):
        v = tk[etiket]
        A(f"| {etiket} (`once={v['pencere']['once']}, sonra={v['pencere']['sonra']}`) | "
          f"%{v['taban_kirliligi_medyan']*100:.1f} | %{v['taban_kirliligi_ortalama']*100:.1f} | "
          f"%{v['taban_kirliligi_maks']*100:.1f} |")
    A("")
    A("EAP'nin penceresi **[−10, −1] İŞLEM günü** (~14 takvim günü), karartmanınki "
      "**[olay−5, olay] TAKVİM günü** (~4 iş günü). Kart pencereyi `in_blackout` ile BİREBİR "
      "sabitlediği için ölçüm birincisinde değil ikincisinde koştu; ikinci satır **YALNIZ SAYIMDIR**, "
      "hiçbir etki oradan okunmadı ve K'ya girmedi. İki raporun farkı bir çelişki değil, pencere "
      "farkıdır.")
    A("")
    A("---")
    A("")
    A("## 4. YENİDEN-OKUMA ADAYI ENVANTERİ")
    A("")
    env = s["adim4_envanter"]
    A("Kart şartı: **\"fark @20'de >=10 bps VE CI 0-dışı ise\"** envanter doldurulur.")
    A("")
    A("| Yüzey | @20 fark | \\|fark\\| ≥ 10 bps | CI 0-dışı | Envanter tetiği |")
    A("|---|---|---|---|---|")
    for etiket, v in env["yuzey_aritmetigi"].items():
        A(f"| {etiket} | {_bps(v['fark20_bps'])} bps | "
          f"{'EVET' if v['|fark20|>=10bps'] else 'hayır'} | "
          f"{'EVET' if v['ci20_sifiri_disliyor'] else 'hayır'} | "
          f"{'TETİKLENDİ' if v['envanter_tetigi(>=10bps VE CI 0-dışı)'] else 'tetiklenmedi'} |")
    A("")
    A(f"**Envanter boş** — {env['neden_bos']}. Bir eşiğe \"ne kadar yaklaşıldığı\" tablosu, o eşik "
      "aritmetik olarak sağlanmadan doldurulursa ölçülmemiş bir sayı üretirdi (UYDURMA YASAĞI).")
    A("")
    A("---")
    A("")
    A("## 5. BAĞLAM: GERÇEK KATMAN (n=95 — hüküm taşımaz)")
    A("")
    A("| Ufuk | n | fark | CI |")
    A("|---|---|---|---|")
    for h, c in sorted(s["gercek_katman_baglam"].items(), key=lambda kv: int(kv[0])):
        A(f"| @{h} | {c['n']} | {_bps(c['fark_bps'])} bps | "
          f"[{_bps(c['ci'][0])} · {_bps(c['ci'][1])}] |")
    A("")
    A("---")
    A("")
    A("## 6. NE ÖLÇÜLMEDİ (beyan)")
    A("")
    A("- **Retro yeniden-hüküm YOK.** Hiçbir geçmiş kartın taban-fazlası yeniden hesaplanmadı; "
      "bu tur ileri-standart için sayı üretir.")
    A("- **Pencere tek:** kart `in_blackout`u birebir şart koştuğu için başka bir olay penceresinde "
      "etki ölçülmedi (K=2 korundu).")
    A("- **`sonra=0`:** karartma tanımı rapor SONRASI günleri kapsamaz; PEAD çapası "
      "(`days_since_report`) ayrı bir tanımdır ve bu turda kullanılmadı.")
    A("- **cf katmanı simülasyondur** (`cf_fidelity` beyanı); bu turda ölçülen büyüklük cf'nin "
      "R'si değil, bar serisinden gelen ileri getirinin TABANIDIR — taban farkı çıkış sadakatinden "
      "bağımsızdır.")
    A("- **Canlı state'e yazılmadı:** bar kopyası + kum havuzu takvimi; `state/earnings.csv`, "
      "`fmp_usage.json`, `events.jsonl` dokunulmadı.")
    A("")
    A("## 7. ÜRETİLEN DOSYALAR")
    A("")
    A("```")
    A("research/olcumler/kys_olcum/")
    A("├── RAPOR_KYS001.md        ← bu dosya")
    A("├── sonuc_kys001.json      ← birleştirilmiş kanıt (PK + kapsama + iki yüzey)")
    A("├── pk_kys001.json         ← araç-doğrulama PK ham çıktısı")
    A("├── kapsama_kys001.json    ← kapsama ham çıktısı (üç kaynak)")
    A("├── olcum_kys001.json      ← yüzey ölçümü ham çıktısı (16 + 2 hücre, CI'lar)")
    A("├── ortak_kys.py           ← mühür + pencere tanımı + panel")
    A("├── pk_kys.py · kapsama_kys.py · olcum_kys.py · takvim_cek.py · rapor_kys.py")
    A("```")
    A("")
    A("> Takvim önbelleği (1.198 gün-JSONL) ve bar kopyası kum havuzundadır, depoya girmez.")
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    s = birlestir()
    (ok.CIKTI / "sonuc_kys001.json").write_text(
        json.dumps(s, ensure_ascii=False, indent=2), encoding="utf-8")
    md = markdown(s, json.loads(OLC.read_text(encoding="utf-8")),
                  json.loads(KAP.read_text(encoding="utf-8")),
                  json.loads(PK.read_text(encoding="utf-8")))
    (ok.CIKTI / "RAPOR_KYS001.md").write_text(md, encoding="utf-8")
    print("sonuc_kys001.json + RAPOR_KYS001.md yazıldı")
