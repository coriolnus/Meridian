"""EDG-2026-017 — RAPOR ÜRETİCİ. YALNIZ sonuc_017.json okur; hiçbir sayı elle taşınmaz.

HÜKÜM CÜMLESİ YAZMAZ (rol sınırı): kill/success ölçütlerinin sayısal KARŞILIKLARI tablo hâlinde
verilir, "tetiklendi/arşiv/ship" gibi bir hüküm cümlesi kurulmaz — onu Rol-1 yazar.
"""
from __future__ import annotations

import json
import pathlib

KLASOR = pathlib.Path(__file__).resolve().parent
S = json.load(open(KLASOR / "sonuc_017.json"))
L = []


def w(s=""):
    L.append(s)


def pct(x, basamak=3):
    return "_ölçülemedi_" if x is None else f"{100*float(x):+.{basamak}f}%"


def ci_pct(c, basamak=3):
    if not c:
        return "_ölçülemedi_"
    return f"[{100*c['lo']:+.{basamak}f}%, {100*c['hi']:+.{basamak}f}%]"


def ci_ham(c, basamak=4):
    if not c:
        return "_ölçülemedi_"
    return f"[{c['lo']:+.{basamak}f}, {c['hi']:+.{basamak}f}]"


def sifir_disi(c):
    if not c:
        return "_ölçülemedi_"
    return "**EVET**" if (c["lo"] > 0 or c["hi"] < 0) else "hayır"


def num(x, b=4):
    return "_ölçülemedi_" if x is None else f"{float(x):+.{b}f}"


K = S["kart_metni_uygulamasi"]
B = S["bekciler"]
PK = B["pozitif_kontrol"]

w(f"# {S['kart']} — rvol FORM REVİZYONU · ÖLÇÜM RAPORU")
w()
w(f"* Kart: `research/cards/EDG-2026-017-rvol-form-revizyonu.yaml` · aile `{S['aile']}`")
w(f"* Ölçüm zamanı: {S['olcum_tarihi']}")
w(f"* Kum havuzu: `{S['kum_havuzu']}` · çalışma dizini `{S['calisma_dizini']}`")
w(f"* Durum: **{S['DURUM']}**")
w()
w("> **SALT-ÖLÇÜM.** Repoya ve canlı `state/`e hiçbir yazım yapılmadı; barlar canlı önbellekten "
  "SALT-OKUNUR okundu, `config.STATE` kum havuzuna çevrildi. **KART DOSYASINA DOKUNULMADI.** "
  "Aşağıda hiçbir hüküm cümlesi yoktur: kill/success ölçütlerinin sayısal karşılıkları veri olarak "
  "verilir, hükmü Rol-1 işler.")
w()

# ------------------------------------------------------------------ 0. BEKÇİLER
w("## 0. BEKÇİLER — İLK KOŞAN İŞ")
w()
w(f"**Pozitif kontrol (kart guard'ı: tutmazsa ÖLÇÜM DURUR)** — ham `rvol20` @20 cf-katman IC: "
  f"**{PK['civi_olculen']}** (hedef {PK['civi_hedef']}, tolerans {PK['tolerans']}, sapma "
  f"{PK['civi_sapma']}) → **GEÇTİ={PK['GECTI']}**")
w()
w(f"* n={PK['20']['n']} · CI {ci_ham(PK['20']['ci'])}")
w(f"* @5 IC {PK['5']['ic']} CI {ci_ham(PK['5']['ci'])} · @10 IC {PK['10']['ic']} "
  f"CI {ci_ham(PK['10']['ci'])}")
w(f"* Katman: {PK['katman']}")
w(f"* Defterdeki referans (`state/component_ic.json`, cf/rvol20): {PK['defterdeki_deger_cf_rvol20']}")
w(f"* Eşleşme muhasebesi: {PK['eslesme_muhasebesi']}")
w()
E2 = PK["edg002_bolge_yeniden_uretimi"]
w("**EDG-002'nin ölçülmüş nesnesinin yeniden üretimi** (yeni K DEĞİL — bekçi):")
w()
w("| nesne | n | ort (20 bar, HAM) | %95 CI |")
w("|---|---|---|---|")
h_ = E2["hedef_edg002"]
w(f"| EDG-002 raporu (s1_retro §3) | {h_['n']} | {pct(h_['ort'],2)} | {ci_pct(h_['ci'],2)} |")
o_ = E2["olculen"]
w(f"| bu tur, aynı katman ve tanım | {o_['n']} | {pct(o_['ort'],2)} | {ci_pct(o_['ci'],2)} |")
w()
w(f"> {E2['tanim']}")
w()
P4 = B["pk4_yol_tutarliligi"]
w(f"**PK4 (yol tutarlılığı)** — GEÇTİ={P4['gecti']}. " +
  " · ".join(f"fwd{h}: n={P4[f'fwd{h}']['n']}, maks|fark|={P4[f'fwd{h}']['maks_mutlak_fark']}"
             for h in (5, 10, 20)))
w()
P5 = B["pk5_ozdeslikler"]
w(f"**PK5 (özdeşlikler)** — GEÇTİ={P5['gecti']}")
w()
w(f"* `C_hizli_ortalama`: n={P5['C_hizli_ortalama']['n_ornek']}, "
  f"maks|fark|={P5['C_hizli_ortalama']['maks_mutlak_fark']}, geçti={P5['C_hizli_ortalama']['gecti']}")
w(f"* `E_hizli_spearman`: geçti={P5['E_hizli_spearman']['gecti']} — "
  + " · ".join(f"n={m['n']}: |fark|={m['mutlak_fark']}" for m in P5['E_hizli_spearman']['olcumler']))
for h, f in P5["F_temiz_taban_ozdesligi"].items():
    w(f"* `F_temiz_taban_ozdesligi` @{h}: alt örnek {f['n_ornek']}/{f['n_toplam_satir']} satır, "
      f"ayrışan={f['ayrisan']}, geçti={f['gecti']} · kanonik `temiz_taban` raporu: "
      f"kirlilik={f['kanonik_kirlilik_orani']}, gün birimi='{f['kanonik_gun_birimi']}', "
      f"pencere={f['kanonik_pencere']}, n_olay={f['kanonik_n_olay']}, "
      f"n_olaysiz_kimlik={f['kanonik_n_olaysiz_kimlik']}, çözülemeyen={f['kanonik_n_cozulemeyen']}")
w()
w(f"> **PK5 KAPSAM BEYANI.** {P5['kapsam_beyani']}")
w()
OG = B["artik_ortogonallik"]
w(f"**Artık ortogonallik bekçisi** — geçti={OG['gecti']} · maks desil-içi ortalama "
  f"{OG['maks_desil_ici_ortalama']} · maks gün-içi ortalama {OG['maks_gun_ici_ortalama']} · "
  f"tekil gün (sürekli yol) {OG['tekil_gun_surekli_yol']}")
w()
KD = B["kod_damgasi"]
w(f"**Kod damgası** — motor kopyalandı ({KD['n_dosya']} dosya), repo↔kopya aynı: "
  f"{KD['repo_kopya_ayni']}. {KD['not']}")
w()

# ------------------------------------------------------------------ 1. YÖNTEM
w("## 1. YÖNTEM BEYANI (kartın harfiyen uygulanması)")
w()
for k, v in K.items():
    w(f"* **`{k}`** — {v}")
w()

# ------------------------------------------------------------------ 2. ÖRNEKLEM
w("## 2. ÖRNEKLEM, KESİT ve KIYAS TEMİZLİĞİ")
w()
BM = S["bar_muhasebesi"]
w(f"* Barlar: {BM['yuklendi']}/{BM['istenen']} sembol yüklendi (dosya yok {BM['dosya_yok']}, "
  f"kısa {BM['kisa']}: {BM['kisa_semboller']})")
w(f"* Takvim kapısı: hayalet seans satırı **{BM['hayalet_dusen']}**, karantina "
  f"**{BM['karantina_dusen']}**, takvim reddedilen sembol {BM['takvim_reddedilen']}")
w(f"* **Güvensiz dönem dışlaması**: kanonik defter yolu (`measurement_bars`) "
  f"{BM['defter_yolu_dusen']} satır / {BM['defter_yolu_sembol']} sembol; HESAPLANAN yol "
  f"(`integrity_safe_start`) ek {BM['hesaplanan_dislanan_satir']} satır; iki yolun ayrıştığı "
  f"sembol: {BM['iki_yol_ayrisan_sembol']}")
KM = S["kesit_muhasebesi"]
w(f"* Gözlem günü {KM['gozlem_gunu_toplam']} → kesiti yeterli (>= {KM['min_kesit']}) gün "
  f"**{KM['kesit_yeterli_gun']}**; kesit medyanı {KM['kesit_buyuklugu']['medyan']} "
  f"(min {KM['kesit_buyuklugu']['min']}, maks {KM['kesit_buyuklugu']['maks']})")
w(f"* Tarih aralığı {KM['tarih_araligi'][0]} → {KM['tarih_araligi'][1]} · kesit satırı "
  f"**{KM['n_satir_kesit']}** ({KM['n_sembol']} sembol; panel toplamı {KM['n_satir_panel_tum']})")
w(f"* `rvol20` dağılımı (kesit): {KM['rvol20_dagilimi']}")
w(f"* **Bölge (rvol20 >= 2.5): n={KM['bolge_n']} satır, kesitin %{KM['bolge_pay_pct']}'i**")
w()
w("### Ders #4 — kıyas temizliği (zorunlu üç alan: kirlilik oranı · pencere+birim · n_temiz)")
w()
w("| ufuk | pencere | gün birimi | taban satırı | kirli | temiz | **kirlilik oranı** | "
  "temiz taban medyan üye | ham taban medyan üye | temiz tabanı OLMAYAN gün |")
w("|---|---|---|---|---|---|---|---|---|---|")
for h, d in S["ders4_kiyas_temizligi"].items():
    w(f"| @{h} | ({d['pencere']['once']}, {d['pencere']['sonra']}) | {d['gun_birimi']} | "
      f"{d['n_toplam_taban_satiri']} | {d['n_kirli']} | {d['n_temiz']} | "
      f"**{d['kirlilik_orani']}** | {d['temiz_taban_medyan_uye']} | {d['ham_taban_medyan_uye']} | "
      f"{d['gun_sayisi_temiz_taban_YOK']} |")
w()
w(f"> {list(S['ders4_kiyas_temizligi'].values())[0]['beyan']}")
w()

# ------------------------------------------------------------------ 3. KATMAN 1
K1 = S["i_katman_rvol25_bolge_fazlasi"]
w("## 3. KATMAN 1 — `rvol25_bolge_fazlasi` (KAYITLI GRID HÜCRESİ 1/2)")
w()
w(f"Bölge: {K1['n_sembol_gun']} sembol-gün · {K1['n_gun']} gün · {K1['n_sembol']} sembol · "
  f"bölge içi rvol20 medyanı {K1['rvol20_medyan_bolge']} (ort {K1['rvol20_ort_bolge']}, "
  f"p95 {K1['rvol20_p95_bolge']})")
w()
w("| ufuk | ölçüt | n | ort | %95 CI (21g blok) | CI 0'ı dışlıyor mu |")
w("|---|---|---|---|---|---|")
for h, u in K1["ufuklar"].items():
    for ad, etiket in (("evren_fazlasi_TEMIZ_taban_HUKUM", "**TEMİZ evren-fazlası (HÜKÜM)**"),
                       ("evren_fazlasi_HAM_taban_kiyas", "ham-taban evren-fazlası (kıyas)"),
                       ("ham_getiri_TANI_kart_olcutu_DEGIL", "HAM getiri (ders#3: ölçüt DEĞİL)")):
        b = u[ad]
        w(f"| @{h} | {etiket} | {b['n']} | {pct(b['ort'])} | {ci_pct(b['ci'])} | "
          f"{sifir_disi(b['ci'])} |")
w()
w("Temiz taban bulunamadığı için düşen bölge satırı: "
  + " · ".join(f"@{h}: {u['temiz_taban_yok_dusen_satir']}" for h, u in K1["ufuklar"].items()))
w()

# ------------------------------------------------------------------ 4. KATMAN 2
K2 = S["ii_katman_rvol25_artik_rvol_surekli_kontrollu"]
w("## 4. KATMAN 2 — `rvol25_artik_rvol_surekli_kontrollu` (KAYITLI GRID HÜCRESİ 2/2)")
w()
w(f"Kontrol: {K2['kontrol']}")
w()
DD = K2["bolge_desil_dagilimi"]
w(f"**Bölgenin kontrol desillerine dağılımı** — {DD['aciklama']}")
w()
w("| desil | n | bölge n | bölge payı |")
w("|---|---|---|---|")
for d, r in DD["desiller"].items():
    w(f"| {d} | {r['n']} | {r['bolge_n']} | %{r['bolge_pay_pct']} |")
w()
A1 = K2["A1_desil_tabanli_bolge_fazlasi"]
w("### 4.1 A1 — kova (desil) tabanlı bölge fazlası")
w()
w(f"> {A1['tanim']}")
w()
w("| ufuk | n | LOO desil-fazlası | %95 CI | CI 0'ı dışlıyor mu | kendini-içeren varyant (CI YOK) | "
  "kova yetersiz düşen |")
w("|---|---|---|---|---|---|---|")
for h, u in A1["ufuklar"].items():
    b = u["loo_desil_fazlasi"]
    w(f"| @{h} | {b['n']} | {pct(b['ort'])} | {ci_pct(b['ci'])} | {sifir_disi(b['ci'])} | "
      f"{pct(u['kendini_iceren_desil_fazlasi_ort_CI_YOK'])} | "
      f"{u['kova_yetersiz_dusen_satir']} |")
w()
A2 = K2["A2_edg007_desil_ici_bolge_eksi_kalan"]
w("### 4.2 A2 — EDG-007 çift-sıralama (desil İÇİNDE bölge − bölge-dışı)")
w()
w(f"> {A2['tanim']}")
w()
for h, u in A2["ufuklar"].items():
    hv = u["havuzlanmis"]
    w(f"**@{h} havuzlanmış** (nA={hv.get('nA')}, nB={hv.get('nB')}): fark {pct(hv.get('fark'))} · "
      f"CI {ci_pct(hv.get('ci'))} · CI 0-dışı {sifir_disi(hv.get('ci'))}")
    w()
    w("| desil | n bölge | n bölge-dışı | ort bölge | ort bölge-dışı | fark | %95 CI | 0-dışı |")
    w("|---|---|---|---|---|---|---|---|")
    for d, c in sorted(u["desiller"].items(), key=lambda kv: int(kv[0])):
        if c.get("fark") is None:
            w(f"| {d} | {c.get('n_bolge', c.get('nA'))} | {c.get('n_bolge_disi', c.get('nB'))} | "
              f"_ölçülemedi_ | _ölçülemedi_ | _ölçülemedi_ | _ölçülemedi_ | "
              f"_{c.get('neden')}_ |")
            continue
        w(f"| {d} | {c['nA']} | {c['nB']} | {pct(c['ort_bolge'])} | {pct(c['ort_bolge_disi'])} | "
          f"{pct(c['fark'])} | {ci_pct(c['ci'])} | {sifir_disi(c['ci'])} |")
    w()
BB = K2["B_artik_ic"]
w("### 4.3 B — artık-IC (desil kuklası artığı ↔ TEMİZ-taban fazla getirisi)")
w()
w(f"> {BB['tanim']}")
w(f">")
w(f"> **Beraberlik şerhi.** {BB['beraberlik_serhi']}")
w()
w("| ufuk | okuma | IC | n | %95 CI | CI 0'ı dışlıyor mu |")
w("|---|---|---|---|---|---|")
etiketler = {
    "artik_desil_ic_fazla_HUKUM": "**desil-artık IC (HÜKÜM)**",
    "artik_desil_ic_fazla_YALNIZ_BOLGELI_DESILLER": "desil-artık IC · yalnız bölgeli desiller",
    "artik_surekli_pctrank_ic_fazla_ROBUSTLUK": "sürekli pctrank artık IC (robustluk)",
    "ham_rvol20_ic_fazla_TANI": "ham rvol20 IC (TANI)",
    "artik_desil_ic_HAM_getiri_TANI_CI_YOK": "desil-artık IC, HAM getiri (TANI, CI YOK)",
}
for h, u in BB["ufuklar"].items():
    for ad, et in etiketler.items():
        b = u[ad]
        w(f"| @{h} | {et} | {num(b['ic'])} | {b['n']} | {ci_ham(b['ci'])} | "
          f"{sifir_disi(b['ci']) if b['ci'] else '_' + str(b.get('neden')) + '_'} |")
w()

# ------------------------------------------------------------------ 5. MALİYET
M = S["iii_maliyet_sonrasi_net"]
w("## 5. MALİYET-SONRASI NET (kill#3'ün okunduğu yer)")
w()
w(f"> {M['tanim']}")
w()
w("| ufuk | katman | model | brüt | maliyet | **net** | net CI | net CI 0-dışı pozitif |")
w("|---|---|---|---|---|---|---|---|")
for h, u in M["ufuklar"].items():
    for kat, kad in (("katman1_evren_fazlasi", "katman 1 (evren fazlası)"),
                     ("katman2_desil_fazlasi_A1", "katman 2 A1 (desil fazlası)")):
        for mod, mad in (("kart_modeli_10bps", f"kart {M['kart_modeli_bps']}bps"),
                         ("duyarlilik_20bps", f"duyarlılık {M['duyarlilik_bps']}bps")):
            b = u[kat][mod]
            w(f"| @{h} | {kad} | {mad} | {pct(b.get('brut'))} | {pct(b.get('maliyet'))} | "
              f"**{pct(b.get('net'))}** | {ci_pct(b.get('ci'))} | "
              f"{b.get('net_pozitif_anlamli')} |")
w()
SD = M["spread_daralmasi_beyan_notu"]
w(f"**Spread daralması beyan notu** (kart metni: _{SD['kart_metni']}_)")
w()
w(f"> {SD['beyan']}")
w()
w(f"* gerçek spread serisi: **{SD['spread_serisi']}** — {SD['spread_serisi_neden']}")
w(f"* betimleyici dolaylı kanıt: bölge medyan dolar hacmi {SD['bolge_medyan_dolar_hacim']} vs "
  f"evren {SD['evren_medyan_dolar_hacim']} (oran {SD['oran']})")
w()

# ------------------------------------------------------------------ 6. ALT DÖNEM
AD = S["iv_alt_donem_kararlilik"]
w("## 6. ALT-DÖNEM KARARLILIK (BETİMLEYİCİ — grid'e dahil DEĞİL)")
w()
w(f"> {AD['not']}")
w(f">")
w(f"> **2018 hayaleti şerhi.** {AD['hayalet_2018_serhi']}")
w()
w("| dönem | aralık | n | @10 fazla | @10 CI | @20 fazla | @20 CI |")
w("|---|---|---|---|---|---|---|")
for ad, r in AD["donemler"].items():
    u10, u20 = r["ufuklar"].get("10", {}), r["ufuklar"].get("20", {})
    w(f"| {ad} | {r['baslangic'] or '…'} → {r['bitis'] or '…'} | {r['n']} | "
      f"{pct(u10.get('ort'))} | {ci_pct(u10.get('ci'))} | {pct(u20.get('ort'))} | "
      f"{ci_pct(u20.get('ci'))} |")
hx = AD["2018_haric"]["ufuklar"]
w(f"| **2018 HARİÇ** | tüm örneklem − 2018 | {hx['20']['n']} | {pct(hx['10']['ort'])} | "
  f"{ci_pct(hx['10']['ci'])} | {pct(hx['20']['ort'])} | {ci_pct(hx['20']['ci'])} |")
w()

# ------------------------------------------------------------------ 7. TANI
T = S["v_tani"]
w("## 7. TANI (K harcanmaz — CI'sız okumalar hüküm taşımaz)")
w()
BT = T["bant_tablosu_panel_CI_YOK"]
w(f"### 7.1 Bant tablosu — panel karşılığı")
w()
w(f"> {BT['aciklama']}")
w()
for h, satir in BT["ufuklar"].items():
    w(f"**@{h}**")
    w()
    w("| rvol bandı | n | temiz-taban fazlası | ham ort |")
    w("|---|---|---|---|")
    for ad, r in satir.items():
        w(f"| {ad} | {r['n']} | {pct(r['temiz_fazla_ort'])} | {pct(r['ham_ort'])} |")
    w()
MD = T["medyan_tanim_varyanti_CI_YOK"]
w("### 7.2 Kart metnindeki İKİNCİ rvol tanımı (medyan20)")
w()
w(f"> {MD['aciklama']}")
w()
w(f"* Bölge n (medyan tanımı): {MD['bolge_n']} · iki tanımın Spearman'ı: "
  f"{MD['iki_tanim_spearman']}")
w()
w("| ufuk | n | temiz-taban fazlası (CI YOK) |")
w("|---|---|---|")
for h, r in MD["ufuklar"].items():
    w(f"| @{h} | {r['n']} | {pct(r['temiz_fazla_ort_CI_YOK'])} |")
w()
CP = T["cf_vs_panel_populasyon_notu"]
w("### 7.3 cf katmanı ↔ panel popülasyon farkı")
w()
w(f"> {CP['aciklama']}")
w()
w(f"* cf katmanında bölge n = {CP['cf_katman_bolge_n']} · panelde bölge n = {CP['panel_bolge_n']}")
w()

# ------------------------------------------------------------------ 8. KILL/SUCCESS
KS = S["kill_success_karsiliklari"]
w("## 8. KILL / SUCCESS ÖLÇÜTLERİNİN SAYISAL KARŞILIKLARI")
w()
w(f"> **{KS['UYARI']}**")
w()
w("### 8.1 success_metric")
w()
w(f"Kart metni (birebir): _{KS['success_metric_metni']}_")
w()
SB = KS["success_bilesenleri"]
w("| bileşen | nokta | %95 CI | CI 0'ı içeriyor mu |")
w("|---|---|---|---|")
for ad, et in (("A_bolge_fazlasi_20_anlamli_pozitif", "bölge fazlası @20 (katman 1, temiz taban)"),
               ("B_kova_tabani_20_(A1)", "kova-tabanı @20 (A1)"),
               ("C_artik_ic_20_(B)", "artık-IC @20 (B)")):
    b = SB[ad]
    fmt = ci_pct if "IC" not in et else ci_ham
    nk = pct(b["nokta"]) if "IC" not in et else num(b["nokta"])
    w(f"| {et} | {nk} | {fmt(b['ci'])} | {b['ci_sifiri_iceriyor']} |")
w()
w(f"* iki yöntem (A1, B) aynı yön @20: **{SB['iki_yontem_ayni_yon_20']}**")
w(f"* en az birinde CI 0-dışı @20: **{SB['en_az_birinde_CI_0_disi_20']}**")
w()
w("### 8.2 kill ölçütleri")
w()
w("| kill | kart metni (birebir) | sayısal karşılık | CI 0'ı içeriyor mu / net |")
w("|---|---|---|---|")
k1 = KS["kill_1"]
w(f"| #1 | {k1['metin']} | @20 fazla {pct(k1['karsilik_20']['nokta'])} CI "
  f"{ci_pct(k1['karsilik_20']['ci'])} (bilgi: @10 {pct(k1['karsilik_10_BILGI']['nokta'])} CI "
  f"{ci_pct(k1['karsilik_10_BILGI']['ci'])}) | **{k1['karsilik_20']['ci_sifiri_iceriyor']}** |")
k2 = KS["kill_2"]
w(f"| #2 | {k2['metin']} | A1 @20 {pct(k2['karsilik_A1_kova_tabani_20']['nokta'])} CI "
  f"{ci_pct(k2['karsilik_A1_kova_tabani_20']['ci'])} · B @20 IC "
  f"{num(k2['karsilik_B_artik_ic_20']['nokta'])} CI {ci_ham(k2['karsilik_B_artik_ic_20']['ci'])} | "
  f"A1: **{k2['karsilik_A1_kova_tabani_20']['ci_sifiri_iceriyor']}** · "
  f"B: **{k2['karsilik_B_artik_ic_20']['ci_sifiri_iceriyor']}** |")
k3 = KS["kill_3"]
w(f"| #3 | {k3['metin']} | @20 net {pct(k3['karsilik_20_kart_modeli'].get('net'))} CI "
  f"{ci_pct(k3['karsilik_20_kart_modeli'].get('ci'))} (bilgi: @10 net "
  f"{pct(k3['karsilik_10_kart_modeli'].get('net'))}) | net ort > 0: "
  f"**{k3['karsilik_20_kart_modeli'].get('net_ort_pozitif')}** · net CI 0-dışı pozitif: "
  f"**{k3['karsilik_20_kart_modeli'].get('net_pozitif_anlamli')}** |")
w()
w("**@10 bilgi satırları (kart ölçütü @20'dir, @10 `horizon` alanının ikinci ufkudur):**")
w()
w(f"* kill#2 A1 @10: {pct(k2['karsilik_A1_kova_tabani_10_BILGI']['nokta'])} CI "
  f"{ci_pct(k2['karsilik_A1_kova_tabani_10_BILGI']['ci'])} · "
  f"B @10 IC {num(k2['karsilik_B_artik_ic_10_BILGI']['nokta'])} CI "
  f"{ci_ham(k2['karsilik_B_artik_ic_10_BILGI']['ci'])}")
w(f"* kill#3 @20 duyarlılık ({M['duyarlilik_bps']}bps): net "
  f"{pct(k3['karsilik_20_duyarlilik_20bps'].get('net'))} CI "
  f"{ci_pct(k3['karsilik_20_duyarlilik_20bps'].get('ci'))}")
w()
G = KS["guard_karsiliklari"]
w("### 8.3 guard karşılıkları")
w()
w("| guard | karşılık |")
w("|---|---|")
w(f"| pozitif kontrol (rvol20 @20 IC ≈0.0642) | çivi **{G['civi']}** → GEÇTİ={G['pozitif_kontrol_GECTI']} |")
w(f"| PK4 yol tutarlılığı | {G['pk4_gecti']} |")
w(f"| PK5 özdeşlikler | {G['pk5_gecti']} |")
w(f"| temiz_taban (aynı-gün evren) zorunlu | {G['temiz_taban_uygulandi']} |")
w(f"| eşik dilbilgisi (ders#2) belirsizliği | {G['esik_dilbilgisi_belirsizligi']} |")
w()
w("---")
w()
w("Bu rapor `rapor_017.py` tarafından YALNIZ `sonuc_017.json`dan üretildi; hiçbir sayı elle "
  "taşınmadı. Kart dosyasına dokunulmadı ve hiçbir hüküm cümlesi kurulmadı.")
w()

(KLASOR / "RAPOR_017.md").write_text("\n".join(L))
print("yazıldı: RAPOR_017.md")
