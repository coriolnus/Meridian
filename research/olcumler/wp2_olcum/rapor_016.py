"""RAPOR_016.md üretici — HER SAYI sonuc_016.json'dan OKUNUR. Elle yazılmış sayı YOKTUR.

YASA 6 (okuyucusuz yazım yok): rapor Rol-1'in hüküm işlemesi için yazılır; her tablo hükmün
hangi bacağını beslediğini söyler.
"""
from __future__ import annotations

import json

import ortak as O

SB = O.SANDBOX
D = json.load(open(SB / "sonuc_016.json"))
S = json.load(open(SB / "kod_damgasi_016.json"))
L = []


def w(s=""):
    L.append(s)


def pc(x, nd=3):
    return "—" if x is None else f"{100*float(x):+.{nd}f}%"


def ci(c):
    return "—" if not c else f"[{100*c['lo']:+.3f}%, {100*c['hi']:+.3f}%]"


def icci(c):
    return "—" if not c else f"[{c['lo']:+.4f}, {c['hi']:+.4f}]"


def hkm(x):
    return {True: "ANLAMLI", False: "CI 0 içi", None: "ölçülemedi"}.get(x, str(x))


def isaret(x):
    return {True: "EVET", False: "hayır", None: "ölçülemedi"}.get(x, str(x))


K = D["kart_metni_uygulamasi"]
B = D["bekciler"]
H = D["hukum_onerisi"]
K1 = D["i_katman_turnover_ust20"]
A = D["ii_katman_turnover_artik_rvol_mom_kontrollu"]
A1 = A["A1_kova_tabanli_ust20_fazlasi"]
A2 = A["A2_edg007_kova_ici_ust20_eksi_kalan"]
IC = A["B_artik_ic"]
M = D["iii_maliyet_sonrasi_net"]
T = D["iv_tani"]
UF = ("10", "20")

# =============================================================== başlık
w("# EDG-2026-016 — TURNOVER ANA-ETKİSİ · ÖLÇÜM RAPORU")
w()
w(f"- Kart: `research/cards/EDG-2026-016-turnover-ana-etkisi.yaml` · aile `{D['aile']}`")
w(f"- Ölçüm: `{D['olcum_tarihi']}` · sandbox `{D['sandbox']}`")
w(f"- Repo HEAD: `{S['repo_HEAD']}` · {S['python']}")
w(f"- Rol: {D['rol']}")
w(f"- Kart sha256 ölçüm ÖNCESİ = SONRASI: **{isaret(S['kart_dokunulmadi'])}** "
  f"(`{S['kart_sha256']['EDG-2026-016-turnover-ana-etkisi.yaml']}`)")
w()
w(f"> **HÜKÜM ÖNERİSİ: {H['oneri']}**")
w()

# =============================================================== 0. bekçiler
w("## 0. Bekçiler (pozitif kontrol İLK KOŞAN İŞ)")
w()
p = B["pozitif_kontrol_CANLI"]
w(f"**Pozitif kontrol (CANLI, bu turda yeniden ölçüldü)** — ham `rvol20` @20 cf-katman IC: "
  f"**{p['civi_olculen']}** (hedef {p['civi_hedef']}, tolerans {p['tolerans']}, sapma "
  f"{p['civi_sapma']}) → **GEÇTİ={isaret(p['GECTI'])}** · n={p['20']['n']}, CI {p['20']['ci']}")
w(f"- @5 IC {p['5']['ic']} (CI {p['5']['ci']}) · @10 IC {p['10']['ic']} (CI {p['10']['ci']})")
w(f"- Kart guard'ı 0.0642 çivisini anıyor; önceki tur (pk.json) {B['pk4_pk5_devralma']['onceki_tur_civi']} "
  f"ölçmüştü — bu tur aynı sayı yeniden üretildi.")
w(f"- Katman: {p['katman']} · eşleşme: {p['eslesme_muhasebesi']}")
w()
d45 = B["pk4_pk5_devralma"]
w(f"**PK4 / PK5 devralması** — PK4 geçti={isaret(d45['pk4_gecti'])}, "
  f"PK5 geçti={isaret(d45['pk5_gecti'])} ({d45['pk5_alt']}).")
w(f"- Devralma meşru çünkü `ortak.py` sha aynı={isaret(d45['ortak_py_sha_ayni'])} ve "
  f"`pk.py` sha aynı={isaret(d45['pk_py_sha_ayni'])} — **bu turda ortak altyapıya DOKUNULMADI**; "
  f"yeni kodun tamamı `k016.py` içindedir. {d45['kural']}")
w()
w("**Bu turun KENDİ bekçileri:**")
w()
w("| bekçi | ölçülen | geçti |")
w("|---|---|---|")
pit = B["pit_sizinti"]
w(f"| PIT sızıntısı (`filed > t` olamaz) | ihlal satırı = {pit['ihlal_satir']} | "
  f"{isaret(pit['gecti'])} |")
og = B["artik_ortogonallik"]
w(f"| Artık ortogonalliği | maks &#124;kesit-korelasyon&#124; = {og['maks_mutlak_kova_korelasyon']}, "
  f"maks &#124;gün-içi ortalama&#124; = {og['maks_mutlak_gun_ici_ortalama']} "
  f"({og['gun']} gün, tekil {og['tekil_gun']}) | {isaret(og['gecti'])} |")
hs = B["hizli_spearman_ozdesligi"]
w(f"| Hızlı Spearman ≡ kanonik `analytics.spearman_ic` | maks &#124;fark&#124; = "
  f"{hs['maks_mutlak_fark']} ({hs['n_ornek']} örnek) | {isaret(hs['gecti'])} |")
fz = B["fiziksel_devir_bekcisi"]
w(f"| Fiziksel devir bekçisi (implied devir > {fz['tavan']}) | {fz['gecersiz_kayit']} as-of kaydı "
  f"geçersiz, {len(fz['etkilenen_sembol'])} sembolde | uygulandı |")
by = B["bayatlik_bekcisi_200g"]
w(f"| {O.BAYAT_GUN}g bayatlık bekçisi | {by['bayat_seri_hucre']} hücre `bayat_seri` → None+neden | "
  f"uygulandı |")
w()
w(f"- Fiziksel bekçinin geçersizlediği kayıtlar (kabuk/ölçek hatası): "
  f"{ {k: v['ornek_deger'] for k, v in fz['etkilenen_sembol'].items()} }")
w(f"- Bayatlıktan etkilenen sembol sayısı: {by['etkilenen_sembol_sayisi']} · en çok etkilenen ilk 10: {by['en_cok_etkilenen_sembol_ilk10']}")
sc = by["SCHW_vakasi"]
if "en_buyuk_dosyalama_boslugu_gun" in sc:
    w(f"- **Kartın adıyla andığı SCHW vakası**: dei serisinde en büyük dosyalama boşluğu "
      f"{sc['en_buyuk_dosyalama_boslugu_gun']} gün (`{sc['bosluk_baslangic_filed']}` → "
      f"`{sc['bosluk_bitis_filed']}`), eşik {sc['esik_gun']}g → eşiği aşıyor="
      f"{isaret(sc['bosluk_esigi_asiyor'])}. Boşluk penceresinde "
      f"{sc['bosluk_penceresindeki_gozlem_gunu']} gözlem günü var, bunların "
      f"{sc['bosluk_penceresinde_turnover_tanimli']}'inde turnover tanımlı kaldı; bu turda SCHW'de "
      f"{sc['bu_turda_bayat_isaretlenen_hucre']} hücre bayat işaretlendi. {sc['yorum']}")
else:
    w(f"- SCHW vakası: {sc.get('neden')}")
w()

# =============================================================== 1. kapsam
w("## 1. Kapsam, kesit ve tanımlar")
w()
ba, pa, ke = D["bar_muhasebesi"], D["panel_muhasebesi"], D["kesit_muhasebesi"]
w(f"- Evren beyanı: {K['universe']}")
w(f"- Bar: istenen {ba['istenen']}, yüklendi {ba['yuklendi']} (dosya yok {ba['dosya_yok']}, "
  f"kısa {ba['kisa']}, okunamadı {ba['okunamadi']}); takvim reddedilen {ba['takvim_reddedilen']}, "
  f"defter yolu düşen {ba['defter_yolu_dusen']} satır / {ba['defter_yolu_sembol']} sembol")
w(f"- Panel: {pa['sembol']} sembol, {pa['gozlem_hucre']} gözlem hücresi; turnover tanımlı "
  f"{pa['turnover_gecerli']}, rvol tanımlı {pa['rvol_gecerli']}, mom tanımlı {pa['mom_gecerli']}, "
  f"**üçü de** {pa['ucu_de']}")
w(f"- Ölçülemeyen hücrelerin neden dağılımı (UYDURMA YASAĞI — hepsi None + neden): "
  f"{pa['neden_sayimi']}")
w(f"- Kesit: {ke['gozlem_gunu_toplam']} gözlem gününden {ke['kesit_yeterli_gun']}'i kullanıldı "
  f"(kesit >= {ke['min_kesit']}); kesit medyanı {ke['kesit_buyuklugu']['medyan']} "
  f"(min {ke['kesit_buyuklugu']['min']}, maks {ke['kesit_buyuklugu']['maks']}); "
  f"tarih aralığı {ke['tarih_araligi']}; ölçüme giren {ke['n_satir']} satır / "
  f"{ke['n_sembol']} sembol")
w(f"- Kontrol kovası: {ke['kova_buyuklugu']['n_kova']} kova, gün başına medyan kova büyüklüğü "
  f"{ke['kova_buyuklugu']['medyan']}")
w(f"- `turnover21` kesit dağılımı: {ke['turnover21_dagilimi']}")
w()
w("**Tanımlar (kart metninin uygulaması):**")
w()
for k, v in K.items():
    w(f"- `{k}`: {v}")
w()
ak = D["akrabalik_beyani"]
w(f"**Akrabalık beyanı** — {ak['not']} n={ak['n_ornek']}: "
  f"spearman(turnover, rvol20) = {ak['spearman_turnover_rvol20']}, "
  f"spearman(turnover, mom21) = {ak['spearman_turnover_mom21']}; "
  f"gün-içi ortalama: rvol {ak['gun_ici_ortalama_spearman_turnover_rvol']}, "
  f"mom {ak['gun_ici_ortalama_spearman_turnover_mom']}. "
  f"Turnover kontrol değişkenleriyle **zayıf** akrabadır — artık katmanının ne kadarını "
  f"kontrolün yiyeceği bu sayılardan okunur.")
w()

# =============================================================== 2. katman 1
w("## 2. KATMAN 1 — `turnover_ust20` (kart bacağı 1)")
w()
w(f"Dilim: {K['katman_1']}; taban: {K['taban_katman_1']}. "
  f"n={K1['n_sembol_gun']} sembol-gün, {K1['n_gun']} gün, {K1['n_sembol']} sembol; "
  f"dilimin turnover medyanı {K1['turnover21_medyan']} (ortalama {K1['turnover21_ort']}), "
  f"mom21 ort {K1['mom21_ort']}, rvol20 ort {K1['rvol20_ort']}.")
w()
w("| ufuk | ölçüm | n | ortalama | %95 blok CI | hüküm |")
w("|---|---|---|---|---|---|")
for h in UF:
    for ad, key in (("ham getiri", "ham"), ("**EVREN FAZLASI**", "evren_fazlasi")):
        x = K1["ufuklar"][h][key]
        w(f"| @{h} | {ad} | {x['n']} | {pc(x['ort'])} | {ci(x.get('ci'))} | {hkm(x.get('anlamli'))} |")
w()
w(f"→ **Bacak 1 (@{H['degerlendirme_ufku']}, kart success_metric'in yazdığı ufuk): üst dilim "
  f"fazlası pozitif-anlamlı = {isaret(H['bacak1_ust20_pozitif_anlamli'])}** · "
  f"kill#1 (CI-0-içi) = {isaret(H['kill1_ust_dilim_CI_0_ici'])}")
w()

# =============================================================== 3. katman 2
w("## 3. KATMAN 2 — `turnover_artik_rvol_mom_kontrollu` (kart bacağı 2)")
w()
w(f"Kontrol: {A['kontrol']}. Kart iki yöntemi birden istiyor: **çift-sıralama VE artık-IC**.")
w()
w("### 3a. Çift-sıralama — A1: kayıtlı dilim, kontrol-kovası tabanı")
w()
w(A1["tanim"])
w()
w("| ufuk | n | kova fazlası (LOO) | %95 blok CI | hüküm | kendini-içeren varyant | kova<2 düşen |")
w("|---|---|---|---|---|---|---|")
for h in UF:
    u = A1["ufuklar"][h]
    x = u["loo_kova_fazlasi"]
    w(f"| @{h} | {x['n']} | {pc(x['ort'])} | {ci(x.get('ci'))} | {hkm(x.get('anlamli'))} | "
      f"{pc(u['kendini_iceren_kova_fazlasi_ort_CI_YOK'])} | {u['kova_yetersiz_dusen_satir']} |")
w()
w("**Kontrolün bedeli** — aynı dilim, yalnız taban değişti:")
w()
w("| ufuk | evren tabanı (katman 1) | kova tabanı (katman 2/A1) | kalan pay |")
w("|---|---|---|---|")
for h in UF:
    a = K1["ufuklar"][h]["evren_fazlasi"]["ort"]
    b = A1["ufuklar"][h]["loo_kova_fazlasi"]["ort"]
    oran = "—" if not a or b is None else f"{100*b/a:.1f}%"
    w(f"| @{h} | {pc(a)} | {pc(b)} | {oran} |")
w()
w("### 3b. Çift-sıralama — A2: EDG-007 şablonu (kova İÇİNDE üst %20 vs kalanı)")
w()
w(A2["tanim"])
w()
for h in UF:
    u = A2["ufuklar"][h]
    w(f"**@{h}g** — 9 kontrol kovası (rvol20 terzili t1..t3 × mom21 terzili t1..t3):")
    w()
    w("| kova | n yüksek | n kalan | ort yüksek | ort kalan | fark | %95 CI | hüküm |")
    w("|---|---|---|---|---|---|---|---|")
    for kv, c in sorted(u["kovalar"].items(), key=lambda kv: int(kv[0])):
        if c.get("fark") is None:
            w(f"| {c['ad']} | {c.get('n_yuksek')} | {c.get('n_kalan')} | — | — | — | — | "
              f"{c.get('neden', '—')} |")
            continue
        w(f"| {c['ad']} | {c['nA']} | {c['nB']} | {pc(c['ort_yuksek'])} | {pc(c['ort_kalan'])} | "
          f"{pc(c['fark'])} | {ci(c.get('ci'))} | {hkm(c.get('anlamli'))} |")
    hv = u["havuzlanmis"]
    w(f"| **HAVUZLANMIŞ** | {hv['nA']} | {hv['nB']} | — | — | **{pc(hv['fark'])}** | "
      f"**{ci(hv.get('ci'))}** | **{hkm(hv.get('anlamli'))}** |")
    w()
    w(f"_{hv['aciklama']}_")
    w()
w("### 3c. Artık-IC")
w()
w(IC["tanim"])
w()
w(f"Artıklaştırma: {K['artik_ic']}")
w()
w("| ufuk | ölçüm | n | IC | %95 blok CI | hüküm |")
w("|---|---|---|---|---|---|")
for h in UF:
    u = IC["ufuklar"][h]
    for ad, key in (("**ARTIK IC** (fazla getiri)", "artik_ic_fazla"),
                    ("ham turnover IC (fazla getiri)", "ham_turnover_ic_fazla"),
                    ("artık IC / HAM getiri (tanı)", "artik_ic_HAM_getiri_TANI_CI_YOK")):
        x = u[key]
        w(f"| @{h} | {ad} | {x['n']} | {x['ic']} | {icci(x.get('ci'))} | "
          f"{hkm(x.get('anlamli'))} |")
w()
w(f"→ **Bacak 2 bayrakları (@{H['degerlendirme_ufku']}):** "
  f"çift-sıralama A1 pozitif-anlamlı = {isaret(H['cift_siralama_A1_pozitif_anlamli'])}, "
  f"A2 havuzlanmış pozitif-anlamlı = {isaret(H['cift_siralama_A2_pozitif_anlamli'])}, "
  f"çift-sıralama GEÇTİ (ikisi birden, muhafazakâr) = "
  f"{isaret(H['cift_siralama_GECTI_ikisi_birden'])}, "
  f"artık-IC pozitif-anlamlı = {isaret(H['artik_ic_pozitif_anlamli'])} → "
  f"**artık katkı GEÇTİ = {isaret(H['bacak2_artik_katki_GECTI'])}** · "
  f"kill#2 (artık yok) = {isaret(H['kill2_artik_yok'])}")
w()

# =============================================================== 4. maliyet
w("## 4. Maliyet-sonrası net (kill#3)")
w()
w(M["tanim"])
w(f"Kart modeli **{M['kart_modeli_tek_yon_bps']}bps tek-yön**; beyanlı duyarlılık "
  f"**{M['duyarlilik_gidis_donus_bps']}bps gidiş-dönüş**.")
w()
w("| ufuk | katman | model | brüt | maliyet | **net** | net %95 CI | net>0 anlamlı |")
w("|---|---|---|---|---|---|---|---|")
for h in UF:
    for kad, kkey in (("katman 1 (evren fazlası)", "katman1_evren_fazlasi"),
                      ("katman 2 A1 (kova fazlası)", "katman2_kova_fazlasi_A1")):
        for mad, mkey in (("kart (10bps)", "kart_modeli"),
                          ("duyarlılık (20bps)", "gidis_donus_duyarlilik")):
            x = M["ufuklar"][h][kkey][mkey]
            if x.get("net") is None:
                w(f"| @{h} | {kad} | {mad} | — | — | — | — | {x.get('neden', '—')} |")
                continue
            w(f"| @{h} | {kad} | {mad} | {pc(x['brut'])} | {pc(x['maliyet'])} | "
              f"**{pc(x['net'])}** | {ci(x.get('ci'))} | {isaret(x['net_pozitif_anlamli'])} |")
w()
lk = M["likidite_beyani"]
w(f"**Kartın 'ucuz işlem görür' beyanının kanıtı** — {lk['not']}")
w()
w(f"- Üst %20 diliminin medyan 21g dolar hacmi: {lk['ust20_medyan_dolar_hacim']} · "
  f"evren medyanı: {lk['evren_medyan_dolar_hacim']} · oran: "
  f"**{lk['ust20_medyan_dolar_hacim_orani']}×**")
w(f"- Medyan kapanış: dilim {lk['ust20_medyan_kapanis']} vs evren {lk['evren_medyan_kapanis']}")
w()
w(f"→ **kill#3 (maliyet-sonrası net <= 0) = {isaret(H['kill3_maliyet_sonrasi_net_sifir_alti'])}**")
w()

# =============================================================== 5. tanı
w("## 5. Tanı (K harcanmaz — CI YOK)")
w()
w(T["not"])
w()
q5 = T["turnover_q5_evren_fazlasi"]
w(f"**Turnover 5'lik tablosu** ({q5['aciklama']}):")
w()
w("| kova | " + " | ".join(f"@{h} n / turnover ort / fazla ort" for h in UF) + " |")
w("|---|" + "---|" * len(UF))
kovalar = sorted(q5["ufuklar"][UF[0]].keys(), key=int)
for kv in kovalar:
    hucre = []
    for h in UF:
        c = q5["ufuklar"][h][kv]
        hucre.append(f"{c['n']} / {c['turnover_ort']} / {pc(c['fazla_ort'])}")
    w(f"| q{kv} | " + " | ".join(hucre) + " |")
w()
e13 = T["edg013_karsilastirmasi"]
w(f"**EDG-013 karşılaştırması** — {e13['aciklama']}")
w()
w("| ufuk | n | 013 diliminin evren fazlası (CI YOK) | bu turun üst %20 dilimi (CI'lı) |")
w("|---|---|---|---|")
for h in UF:
    c = e13["ufuklar"][h]
    w(f"| @{h} | {c['n']} | {pc(c['evren_fazlasi_ort_CI_YOK'])} | "
      f"{pc(K1['ufuklar'][h]['evren_fazlasi']['ort'])} |")
w()

# =============================================================== 5b. yapısal çekinceler
from meridian.adapters import data as _dat  # noqa: E402

w("## 5b. Yapısal çekinceler (ölçümle AYRIŞTIRILAMAZ — hüküm okunurken birlikte okunmalı)")
w()
w(f"**Ç1 — Evren HAYATTA KALANLARDAN oluşuyor.** Kartın `universe: full_251` metnine sadık "
  f"kalındı; `RETIRED_SYMBOLS` ({len(_dat.RETIRED_SYMBOLS)} delist) evrenin DIŞINDA. Bu çekince "
  f"POZİTİF bir bulguda NEGATİF bulgudakinden daha ağırdır: yüksek devir hızı sıkıntı/spekülasyon "
  f"göstergesidir ve yüksek-devirli isimlerin batan/çıkarılan kuyruğu örneklemde YOKTUR — bu, "
  f"üst dilimin fazlasını YUKARI çarpıtır. Etkinin işareti bilinir, büyüklüğü bu veriyle "
  f"ölçülemez. (Önceki turun T6 notuyla aynı yapısal sınır.)")
w()
w("**Ç2 — Örneklem içi tek dönem.** Ölçüm tek bir tarihsel pencerede yapıldı; alt-dönem "
  "kararlılığı bu kartın grid'inde YOK, ölçülmedi. Kart bir alt-dönem bacağı kaydetmediği için "
  "sonradan eklenmesi K'yı harcar — istenirse KENDİ kartını ister.")
w()
w("**Ç3 — `rvol20` skorda, `turnover21` değil.** Kontrol değişkenlerinden biri canlı skorun "
  "bileşenidir; artık katmanı bu yüzden 'skora ne EKLER' sorusunun doğru biçimidir. Ama mom21 "
  "kontrolü canlı skorun momentum kolunun BİREBİR aynısı değildir (kart, kontrolü 013 turundaki "
  "tanımla sabitledi) — entegrasyon kararında canlı skor bileşenleriyle çakışma ayrıca "
  "sınanmalıdır.")
w()
w("**Ç4 — Devir hızı ile işlem maliyeti arasındaki ilişki tek yönlü okunmamalı.** Yüksek devir "
  "likidite demek (yukarıdaki dolar-hacim kanıtı), ama aynı zamanda o isimlerin oynaklığı da "
  "yüksektir; kartın sabit-bps maliyet modeli oynaklığa bağlı kayma (slippage) farkını "
  "TAŞIMAZ. Kill#3 kartın yazdığı modelle işletildi.")
w()

# =============================================================== 6. hüküm
w("## 6. Hüküm önerisi (hükmü Rol-1 işler)")
w()
w(f"**Kart success_metric:** {H['kart_success_metric']}")
w(f"**Değerlendirme ufku:** @{H['degerlendirme_ufku']}")
w()
w("| ölçüt | sonuç |")
w("|---|---|")
for k in ("pozitif_kontrol_GECTI", "bacak1_ust20_pozitif_anlamli",
          "cift_siralama_A1_pozitif_anlamli", "cift_siralama_A2_pozitif_anlamli",
          "cift_siralama_GECTI_ikisi_birden", "artik_ic_pozitif_anlamli",
          "bacak2_artik_katki_GECTI", "success_metric_KARSILANDI",
          "kill1_ust_dilim_CI_0_ici", "kill2_artik_yok",
          "kill3_maliyet_sonrasi_net_sifir_alti"):
    w(f"| `{k}` | **{isaret(H[k])}** |")
w()
w(f"### → {H['oneri']}")
w()
w(f"**EDG-013'e yansıması.** {H['edg013_yansimasi']}")
w()
w("---")
w()
w("### Kod damgası")
w()
w(f"- Ölçüm kodu sha256: {S['olcum_kodu_sha256']}")
w(f"- Girdi sha256: {S['girdi_sha256']}")
w(f"- Çıktı sha256: {S['cikti_sha256']}")
w(f"- {S['not']}")

(SB / "RAPOR_016.md").write_text("\n".join(L) + "\n")
print(f"yazıldı: RAPOR_016.md ({len(L)} satır)")
