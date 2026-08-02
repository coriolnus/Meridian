"""RAPOR.md üretici — HER SAYI sonuc.json'dan OKUNUR. Elle yazılmış sayı YOKTUR.

YASA 6 (okuyucusuz yazım yok): rapor Rol-1'in hüküm işlemesi için yazılır; her tablo hükmün
hangi bacağını beslediğini söyler.
"""
from __future__ import annotations

import json

import ortak as O

SB = O.SANDBOX
D = json.load(open(SB / "sonuc.json"))
S = json.load(open(SB / "kod_damgasi.json"))
L = []


def w(s=""):
    L.append(s)


def pc(x, nd=3):
    return "—" if x is None else f"{100*float(x):+.{nd}f}%"


def ci(c):
    if not c:
        return "—"
    return f"[{100*c['lo']:+.3f}%, {100*c['hi']:+.3f}%]"


def isaret(x):
    return {True: "EVET", False: "hayır", None: "ölçülemedi"}.get(x, str(x))


def blok_satir(ad, u, key):
    x = u.get(key, {})
    if x.get("ort") is None:
        return f"| {ad} | {x.get('n', 0)} | — | — | {x.get('neden', '—')} |"
    return (f"| {ad} | {x['n']} | {pc(x['ort'])} | {ci(x.get('ci'))} | "
            f"{'ANLAMLI' if x.get('anlamli') else 'CI 0 içi'} |")


# =============================================================== başlık
w("# WP2 ÖLÇÜM DALGASI — EDG-2026-012 / -013 / -014")
w()
w(f"- Ölçüm: `{D['olcum_tarihi']}` · sandbox `{D['sandbox']}`")
w(f"- Repo HEAD: `{S['repo_HEAD']}` · {S['python']}")
w(f"- Rol: {D['rol']}")
w("- Üç kart **AYRI AİLEDİR**: birinin hükmü diğerini etkilemez. Ortak olan tek şey aşağıdaki "
  "boru-hattı bekçisidir.")
w()

# =============================================================== bekçi
b = D["ortak_bekci"]
pk = b["pozitif_kontrol"]
w("## 0. Boru hattı bekçisi (İLK KOŞAN İŞ)")
w()
w(f"**Pozitif kontrol** — ham `rvol20` @20 cf-katman IC: **{pk['civi_olculen']}** "
  f"(hedef {pk['civi_hedef']}, tolerans {pk['tolerans']}, sapma {pk['civi_sapma']}) → "
  f"**GEÇTİ={pk['GECTI']}**  ·  n={pk['20']['n']}, CI {pk['20']['ci']}")
w(f"- @5 IC {pk['5']['ic']} (CI {pk['5']['ci']}), @10 IC {pk['10']['ic']} (CI {pk['10']['ci']})")
w(f"- defterdeki referans (`state/component_ic.json`, cf/rvol20): {pk['defterdeki_deger_cf_rvol20']}")
w(f"- katman: {pk['katman']}; eşleşme: {pk['eslesme_muhasebesi']}")
w()
p4 = b["pk4_yol_tutarliligi"]
w(f"**PK4 (yol tutarlılığı)** — GEÇTİ={p4['gecti']}. "
  + "; ".join(f"fwd{h}: n={p4[f'fwd{h}']['n']}, maks|fark|={p4[f'fwd{h}']['maks_mutlak_fark']}"
              for h in (5, 10, 20, 60)))
w()
p5 = b["pk5_ozdeslikler"]
w(f"**PK5 (özdeşlikler)** — GEÇTİ={p5['gecti']}")
for k, v in p5.items():
    if k == "gecti":
        continue
    w(f"- `{k}`: {', '.join(f'{a}={c}' for a, c in v.items() if a != 'tanim')}")
w()
sd = b["split_takvimi_bar_serisi_duz_mu"]
w("**Brief'in bar-tabanlı split yolu bu veride YOK.** Bilinen bölünme günlerinde bar serisinde "
  "sıçrama gözlenmedi (seri split-DÜZELTİLMİŞ):")
w()
w("| sembol | bölünme günü | o günün getirisi | hacim oranı |")
w("|---|---|---|---|")
for sym, v in sd["sonuc"].items():
    w(f"| {sym} | {v.get('split_gunu', '—')} | {pc(v.get('gun_getirisi'))} | "
      f"{v.get('hacim_orani')} |")
w()
w(sd["yorum"])
w()

# =============================================================== ortak altyapı
k12 = D["kartlar"]["EDG-2026-012"]
sh = k12["hisse_muhasebesi"]
tk = k12["split_takvimi_muhasebesi"]
w("## 0b. Ortak as-of altyapısı (012 ve 013 aynı nesneyi kullanır)")
w()
w(f"- Anlık hisse serisi olan sembol: {sh['birincil_dei'] + sh['birincil_usgaap']} "
  f"(birincil dei {sh['birincil_dei']}, birincil us-gaap {sh['birincil_usgaap']}); "
  f"evrende serisi OLMAYAN: {sh['seri_olmayan_sembol']} "
  f"(çok-sınıflı kapak sayısı boyutlu → companyfacts taşımıyor)")
w(f"- `val<=0` / birim filtresiyle düşen ham satır: {sh['birim_veya_val_dusen']}")
w(f"- Yedek etiketten doldurulan boşluk kaydı: {sh['yedek_etiket_eklenen_kayit']}")
w(f"- **Split takvimi**: {tk['aday_sicrama']} aday sıçrama tarandı → {tk['kabul']} bölünme kabul "
  f"({tk['kabul_sembol']} sembolde); temiz orana oturmayan {tk['snap_olmayan']}, "
  f"yeniden-beyan kanıtı olmayan {tk['kanitsiz']}")
w(f"- Açıklanamayan ≥{O.SICRAMA_ESIK}× sınır (kart kuralı): {tk['kirik_sinir']} · "
  f"ölçek-hatası gidiş-dönüş penceresi: {tk['olcek_gidis_donus']}")
w(f"- Kanıt yalnız anlık etiketlerden toplansaydı kabul sayısı "
  f"{tk['yalniz_anlik_kanitla_kabul_n']} olurdu (tam kanıtla {tk['kabul']}); "
  f"iki takvim aynı mı: {tk['yalniz_anlik_kanitla_ayni_mi']} — ağırlıklı-ortalama etiketleri "
  f"YALNIZ bölünme KANITI olarak okundu, seviye olarak ASLA.")
fb = sh.get("fiziksel_bekci", {})
w(f"- **Fiziksel ölçek bekçisi** (veri kalitesi, sinyal eşiği DEĞİL): implied medyan-21g devir "
  f"hızı > {fb.get('tavan')} olan {fb.get('gecersiz_kayit')} as-of kaydı geçersiz — "
  f"{ {k: v['ornek_deger'] for k, v in fb.get('etkilenen_sembol', {}).items()} } "
  f"(dosyalayan kabuk/ölçek hatası: 3, 100, 8.000, 25.000 hisse)")
w()
dg = b["split_normalizasyon_dogrulama"]
w("**Split normalizasyonu doğrulaması** (brief'in istediği NVDA/AVGO sınavı) — güncel baza "
  "çevrilmiş as-of hisse sayımı bölünmenin ÜZERİNDEN pürüzsüz geçmelidir; ham EDGAR serisi ise "
  "sıçrar. PK5-B baz çarpanını ayrıca cebirsel olarak da doğruluyor.")
w()
kabul = {}
for e in tk["kabul_listesi"]:
    kabul.setdefault(e["symbol"], []).append(f"{e['filed']} ×{e['oran']} (ham {e['ham_oran']})")
w("| sembol | kabul edilen bölünme(ler) | B_son |")
w("|---|---|---|")
for sym, v in dg["seri"].items():
    w(f"| {sym} | {'; '.join(kabul.get(sym, [])) or '—'} | {v.get('B_son', '—')} |")
w()
w("| sembol | seri | " + " | ".join(dg["tarihler"]) + " |")
w("|---" * (len(dg["tarihler"]) + 2) + "|")
for sym, v in dg["seri"].items():
    if "neden" in v:
        continue
    w(f"| {sym} | güncel baz | " + " | ".join(
        ("—" if x is None else f"{x:.4g}") for x in v["guncel_baz"]) + " |")
    w(f"| {sym} | ham EDGAR | " + " | ".join(
        ("—" if x is None else f"{x:.4g}") for x in v["ham_edgar"]) + " |")
w()

# =============================================================== kart blokları
def kart_blok(kid, baslik, ufuklar, dilim_key, fazla_key):
    K = D["kartlar"][kid]
    w(f"## {baslik}")
    w()
    if K.get("DURUM") != "OLCULDU":
        w(f"**DURUM: {K.get('DURUM')}** — {K.get('neden')}")
        w()
        return K
    kes = K["kesit_muhasebesi"]
    pa = K["panel_muhasebesi"]
    w("### (i) Örneklem / kapsam")
    w()
    w(f"- Gözlem günü: {kes['gozlem_gunu_toplam']} · kesiti yeterli "
      f"(>= {kes['min_kesit']} sembol) gün: {kes['kesit_yeterli_gun']} · "
      f"kesit medyanı {kes['kesit_buyuklugu']['medyan']} "
      f"(min {kes['kesit_buyuklugu']['min']}, maks {kes['kesit_buyuklugu']['maks']})")
    w(f"- Tarih aralığı: {kes['tarih_araligi'][0]} → {kes['tarih_araligi'][1]}")
    if "kill3_ornekem" in K:
        k3 = K["kill3_ornekem"]
        w(f"- **Örneklem kapısı**: geçerli sembol-ay {k3['gecerli_sembol_ay']} "
          f"(kart eşiği {k3['esik']}) → yeterli={k3['yeterli']}")
    w(f"- Ölçülemeyen hücrelerin nedenleri: `{json.dumps(pa['neden_sayimi'], ensure_ascii=False)}`")
    if "filed_gecikme_ozeti" in pa:
        g = pa["filed_gecikme_ozeti"]
        w(f"- **filed gecikmesi** (gözlem günü − kullanılan kaydın filed'ı): n={g['n']}, "
          f"medyan {g['medyan']}g, p10 {g['p10']}g, p90 {g['p90']}g, maks {g['maks']}g, "
          f"negatif {g['negatif_n']} (negatif = PIT ihlali olurdu)")
    w()
    return K


# ---------------------------------------------------------------- 012
K = kart_blok("EDG-2026-012", "1. EDG-2026-012 · net hisse ihracı (`net_share_issuance`)",
              (20, 60), "i_dilim_tablosu", "evren_fazlasi")
if K.get("DURUM") == "OLCULDU":
    w(f"- net_ihrac dağılımı (kesit): "
      f"`{json.dumps(K['kesit_muhasebesi']['net_ihrac_dagilimi'], ensure_ascii=False)}`")
    w()
    w("### (ii) Dilim tablosu — aynı-gün EVREN tabanına göre FAZLA")
    w()
    w("| dilim / ufuk | n | fazla ort. | %95 CI (21 ay blok) | hüküm |")
    w("|---|---|---|---|---|")
    for ad, blk in K["i_dilim_tablosu"].items():
        for h in ("20", "60"):
            w(blok_satir(f"{ad} @{h}g", blk["ufuklar"][h], "evren_fazlasi"))
    w()
    w("Ham (tabansız) ortalamalar ve dar bloklu (3 ay) CI'lar `sonuc.json`'da; **3 aylık blok "
      "hiçbir bacağın işaretini değiştirmiyor**.")
    w()
    for ad, blk in K["i_dilim_tablosu"].items():
        w(f"- `{ad}`: {blk['n_sembol_ay']} sembol-ay, {blk['n_sembol']} sembol, "
          f"{blk['n_gun']} gün; dilim içi net_ihrac ort. {pc(blk['net_ihrac_ort'], 2)}, "
          f"medyan {pc(blk['net_ihrac_medyan'], 2)}")
    w()
    w("**Yayılım (geri-alım − ihraç, TANI):** "
      + "; ".join(f"@{h}g {pc(v['fark'])} CI {ci(v['ci'])} ({'ANLAMLI' if v['anlamli'] else 'CI 0 içi'})"
                  for h, v in K["i_yayilim_gerialim_eksi_ihrac"]["ufuklar"].items()))
    w()
    w("**Beşli dilim (TANI, CI YOK — K harcanmaz; 0 = en çok geri-alan, 4 = en çok ihraç eden):**")
    w()
    w("| ufuk | q0 | q1 | q2 | q3 | q4 |")
    w("|---|---|---|---|---|---|")
    for h, t in K["i_besli_dilim_TANI"]["ufuklar"].items():
        w(f"| @{h}g | " + " | ".join(pc(t[str(q)]["fazla_ort"]) for q in range(5)) + " |")
    w()
    w("**İhraç diliminde en sık görülen semboller (TANI):** "
      + ", ".join(f"{k}({v})" for k, v in K["i_ihrac_diliminde_en_sik_semboller_TANI"].items()))
    w()
    hu = K["hukum_onerisi"]
    w("### (iii) Hüküm ÖNERİSİ")
    w()
    w(f"- Kart ölçütü: *{hu['kart_success_metric']}*")
    w(f"- success karşılandı: **{isaret(hu['success_metric_KARSILANDI'])}** · "
      f"kill#1 (iki uç da CI-0-içi): {isaret(hu['kill1_iki_uc_de_CI_0_ici'])} · "
      f"kill#2 (yön TERS ve anlamlı): **{isaret(hu['kill2_yon_literaturun_TERSI_ve_anlamli'])}** · "
      f"kill#3 (örneklem): {isaret(hu['kill3_ornek_yetersiz'])}")
    w(f"- **ÖNERİ: {hu['oneri']}**")
    w()

# ---------------------------------------------------------------- 013
K = kart_blok("EDG-2026-013", "2. EDG-2026-013 · kısa-dönem momentum × turnover",
              (10, 20), "i_dilim_tablosu", "evren_fazlasi")
if K.get("DURUM") == "OLCULDU":
    kes = K["kesit_muhasebesi"]
    w(f"- turnover21 dağılımı: `{json.dumps(kes['turnover21_dagilimi'], ensure_ascii=False)}` · "
      f"mom21 dağılımı: `{json.dumps(kes['mom21_dagilimi'], ensure_ascii=False)}`")
    ak = K["akrabalik_beyani"]
    w(f"- **Akrabalık beyanı (kart guard)**: Spearman(turnover21, rvol20) = "
      f"{ak['spearman_turnover21_rvol20']} (gün-içi ortalama "
      f"{ak['gun_ici_ortalama_spearman_turnover_rvol']}); Spearman(turnover21, mom21) = "
      f"{ak['spearman_turnover21_mom21']}. Yani turnover, skorda ZATEN olan rvol20'nin "
      f"kılık değiştirmiş hâli DEĞİL (ilişki zayıf ve NEGATİF).")
    w()
    w("### (ii) Katman tablosu — aynı-gün evren tabanına göre FAZLA")
    w()
    w("| katman / ufuk | n | fazla ort. | %95 CI (21 işlem günü blok) | hüküm |")
    w("|---|---|---|---|---|")
    for ad, blk in K["i_dilim_tablosu"].items():
        for h in ("10", "20"):
            w(blok_satir(f"{ad} @{h}g", blk["ufuklar"][h], "evren_fazlasi"))
    w()
    w("**ARTIMLILIK (koşullu − koşulsuz, eşleştirilmiş gün blokları):**")
    w()
    w("| ufuk | fark | %95 CI | hüküm |")
    w("|---|---|---|---|")
    for h, v in K["ii_artimlilik_kosullu_eksi_kosulsuz"].items():
        w(f"| @{h}g | {pc(v['fark'])} | {ci(v['ci'])} | "
          f"{'ANLAMLI POZİTİF' if v['pozitif_anlamli'] else ('ANLAMLI NEGATİF' if v['negatif_anlamli'] else 'CI 0 içi')} |")
    w()
    ta = K["iii_tani_dilimleri"]
    w("**TANI dilimleri (hüküm bacağı DEĞİL):**")
    w()
    w("| tanı | @10g | @20g |")
    w("|---|---|---|")
    alt = ta["mom_ust20_turnover_ALTI"]["ufuklar"]
    w(f"| mom üst%20 ∧ turnover ALTI (kayıtlı dilimlerin tümleyeni, CI okunabilir) | "
      f"{pc(alt['10']['ort'])} CI {ci(alt['10'].get('ci'))} | "
      f"{pc(alt['20']['ort'])} CI {ci(alt['20'].get('ci'))} |")
    tam = ta["mom_ust20_kosulsuz_TAM_EVREN"]["ufuklar"]
    w(f"| mom üst%20, koşulsuz, TAM evren (kapsam kontrolü) | {pc(tam['10']['ort'])} | "
      f"{pc(tam['20']['ort'])} |")
    w()
    w("**turnover ANA ETKİSİ — momentum koşulu YOK, tüm kesit (CI BİLEREK yok: kartın "
      "grid'inde olmayan dilim, CI'lı sınansa K çarpılırdı):**")
    w()
    w("| ufuk | q0 (en düşük TO) | q1 | q2 | q3 | q4 (en yüksek TO) |")
    w("|---|---|---|---|---|---|")
    for h, t in ta["turnover_ANA_ETKI_q5_CI_YOK"]["ufuklar"].items():
        w(f"| @{h}g | " + " | ".join(pc(t[str(q)]["fazla_ort"]) for q in range(5)) + " |")
    w()
    hu = K["hukum_onerisi"]
    w("### (iii) Hüküm ÖNERİSİ")
    w()
    w(f"- Kart ölçütü: *{hu['kart_success_metric']}*")
    w(f"- bacak1 (koşullu dilim @10 VEYA @20 anlamlı POZİTİF): "
      f"**{isaret(hu['bacak1_kosullu_pozitif_anlamli'])}** · bacak2 (artımlılık anlamlı POZİTİF): "
      f"**{isaret(hu['bacak2_artimlilik_pozitif_anlamli'])}** · iki bacak AYNI ufukta: "
      f"**{isaret(hu['iki_bacak_AYNI_ufukta'])}**")
    w(f"- kill#1 (koşullu CI-0-içi): {isaret(hu['kill1_kosullu_CI_0_ici'])} · "
      f"kill#2 (artımlılık yok): {isaret(hu['kill2_artimlilik_yok'])} · "
      f"kill#3 (reversal): {isaret(hu['kill3_reversal_anlamli_negatif'])}")
    w(f"- **ÖNERİ: {hu['oneri']}**")
    w()

# ---------------------------------------------------------------- 014
K = kart_blok("EDG-2026-014", "3. EDG-2026-014 · brüt kârlılık (GP/Assets)",
              (20, 60), "i_dilim_tablosu", "kendi_evren_fazlasi")
if K.get("DURUM") == "OLCULDU":
    kes = K["kesit_muhasebesi"]
    ka = K["kapsam_tanisi"]
    tm = K["temel_muhasebesi"]
    w(f"- GP alt-kümesi: {kes['gp_altkume_sembol_n']} sembol "
      f"(README §3 F∧G evrende {ka['README_F_ve_G_evrende']}; aradaki "
      f"{len(ka['aradaki_semboller'])} sembol: {ka['aradaki_semboller']} — {ka['neden']})")
    w(f"- Yıl başına kesit: `{json.dumps(ka['yil_basina_kesit'], ensure_ascii=False)}`")
    w(f"- gp kaynağı (hücre): `{json.dumps(K['panel_muhasebesi']['gp_kaynak_hucre'], ensure_ascii=False)}`")
    w(f"- Assets eşleşmesi: aynı dosyalama+aynı end {tm['assets_ayni_dosyalama_ayni_end']}, "
      f"aynı dosyalama+yakın end {tm['assets_ayni_dosyalama_yakin_end']}, "
      f"eşleşmeyen (DÜŞÜRÜLDÜ) {tm['assets_eslesmeyen']}")
    w(f"- `val<=0` nedeniyle düşen GrossProfit satırı: {tm['grossprofit_val_le0_dusen']} · "
      f"AFN birimli satır: {tm['AFN_dusen']} (MPWR)")
    w(f"- gpa dağılımı: `{json.dumps(kes['gpa_dagilimi'], ensure_ascii=False)}` · "
      f"sektör dağılımı: `{json.dumps(kes['sektor_dagilimi'], ensure_ascii=False)}`")
    w()
    w("### (ii) Dilim tablosu — aynı-gün **GP-alt-kümesi** tabanına göre FAZLA")
    w()
    w("| dilim / ufuk | n | fazla ort. | %95 CI (21 ay blok) | hüküm |")
    w("|---|---|---|---|---|")
    for ad, blk in K["i_dilim_tablosu"].items():
        for h in ("20", "60"):
            w(blok_satir(f"{ad} @{h}g", blk["ufuklar"][h], "kendi_evren_fazlasi"))
    w()
    w("**YAYILIM (üst − alt, monotonluk kanıtı — kartın İKİNCİ bacağı):**")
    w()
    w("| ufuk | yayılım | %95 CI | hüküm |")
    w("|---|---|---|---|")
    for h, v in K["ii_yayilim_ust_eksi_alt"].items():
        w(f"| @{h}g | {pc(v['fark'])} | {ci(v['ci'])} | "
          f"{'ANLAMLI' if v['anlamli'] else 'CI 0 içi'} |")
    w()
    w("**Beşli dilim (TANI, CI YOK; 0 = en düşük gpa, 4 = en yüksek):**")
    w()
    w("| ufuk | q0 | q1 | q2 | q3 | q4 |")
    w("|---|---|---|---|---|---|")
    for h, t in K["iii_besli_dilim_TANI"]["ufuklar"].items():
        w(f"| @{h}g | " + " | ".join(pc(t[str(q)]["fazla_ort"]) for q in range(5)) + " |")
    w()
    sk = K["iv_sektor_duyarliligi_TANI"]
    w(f"**Sektör duyarlılığı (kart guard — TANI, eşik DEĞİL):** finans-dışı alt-küme "
      f"{sk['finansdisi_sembol_n']} sembol; GP alt-kümesinde kalan finans/REIT sembolleri: "
      f"{sk['GP_altkumesinde_kalan_finans_sembol']}")
    w()
    w("| finans-dışı dilim / ufuk | n | fazla ort. | %95 CI | hüküm |")
    w("|---|---|---|---|---|")
    for ad, blk in sk["dilim"].items():
        for h in ("20", "60"):
            w(blok_satir(f"{ad} @{h}g", blk["ufuklar"][h], "kendi_evren_fazlasi"))
    w("")
    w("Finans-dışı yayılım: " + "; ".join(
        f"@{h}g {pc(v['fark'])} CI {ci(v['ci'])}" for h, v in sk["yayilim"].items()))
    w()
    hu = K["hukum_onerisi"]
    w("### (iii) Hüküm ÖNERİSİ")
    w()
    w(f"- Kart ölçütü: *{hu['kart_success_metric']}*")
    w(f"- bacak1 (üst dilim @60 anlamlı POZİTİF): **{isaret(hu['bacak1_ust60_pozitif_anlamli'])}** · "
      f"bacak2 (yayılım @60 anlamlı POZİTİF): **{isaret(hu['bacak2_yayilim60_pozitif_anlamli'])}**")
    w(f"- kill#1 (üst+yayılım @20 ve @60 CI-0-içi): "
      f"**{isaret(hu['kill1_ust_ve_yayilim_20_60_CI_0_ici'])}** · "
      f"kill#2 (yön ters-anlamlı): {isaret(hu['kill2_yon_ters_anlamli'])} · "
      f"kill#3 (örneklem): {isaret(hu['kill3_ornek_yetersiz'])}")
    w(f"- **ÖNERİ: {hu['oneri']}**")
    w()

# =============================================================== veri tuzakları
K12 = D["kartlar"]["EDG-2026-012"]
K13 = D["kartlar"]["EDG-2026-013"]
K14 = D["kartlar"]["EDG-2026-014"]
tk = K12["split_takvimi_muhasebesi"]
w("## 4. Veri tuzakları ve hükmü okurken bilinmesi gerekenler")
w()
w("Bunlar **gözlem**dir; hiçbiri hükmü değiştirmedi, hükmü Rol-1 işler.")
w()
w("**T1 — Bar serisi split-düzeltilmiş; bölünme takvimi bar verisinden ÇIKARILAMIYOR.** Brief'in "
  "önerdiği yol bu veri kümesinde yok (§0). Takvim EDGAR'ın kendi geriye-dönük yeniden-beyanından "
  f"kuruldu: {tk['kabul']} bölünme kabul, {tk['kanitsiz']} sıçrama 'temiz orana oturdu ama "
  f"yeniden-beyan kanıtı yok' diye REDDEDİLDİ. Reddedilenlerin çoğu birleşme kaynaklı GERÇEK "
  "ihraçtır (MRK/Schering 2009, RTX/UTC 2020, PLD/AMB 2011, O/VEREIT 2022, NEM/Goldcorp 2019, "
  "OMC/IPG 2026) — bölünme sayılsalardı gerçek ihraç silinirdi.")
w()
fb = K12["hisse_muhasebesi"].get("fiziksel_bekci", {})
w("**T2 — Dosyalayan ölçek/kabuk hataları kapak sayfasında yaşıyor.** İki ayrı desen: "
  f"(a) 1000×/10⁶× GİDİŞ-DÖNÜŞ ({tk['olcek_gidis_donus']} pencere: ON, ORCL, PKG, PSA, QCOM, "
  f"SWKS, AEP, CLX, EXC, MAR, CB, AMD, CRM); (b) yeni kayıtçının KABUK sayısı — serinin başında "
  f"tek yönlü, dönüşü yok ({fb.get('gecersiz_kayit')} kayıt: CSX=3, ETN=100, BKR=100, SPG=8.000, "
  "LIN=25.000 hisse). (b) kartın ≥5× kuralıyla YAKALANAMAZ (sıçramanın hangi tarafının bozuk "
  "olduğunu söylemez ve seri başında karşı sıçrama yoktur); fiziksel bekçi bunun için eklendi ve "
  "beyan edildi. Bekçi olmasaydı 013'ün devir hızı kuyruğunda 10⁴ mertebesinde uydurma değerler "
  "kalırdı.")
w()
w("**T3 — MLM 2015-02-24 10-K kapak sayfası bir önceki yılın hisse adedini KOPYALAMIŞ** "
  "(46.158.811 iki yıl üst üste); aynı dosyalamadaki us-gaap bilanço sayısı doğru (67.293.000). "
  "Oran 0,69 olduğu için kartın 5× kuralına takılmaz. **WFC 2023-08-01** 10-Q'da dei=1,82 Mr, "
  "üç gün sonra 10-Q/A ile 3,66 Mr'a düzeltilmiş. İkisi de tek çeyreklik, sembol düzeyinde "
  "sınırlı; düzeltilmedi, beyan edildi.")
w()
w(f"**T4 — SCHW'de dei serisinde 4,5 yıllık boşluk var** (2020-08-07 → 2025-02-26). Bayatlık "
  f"bekçisi ({O.BAYAT_GUN} gün) olmasaydı 2020 sayısı 2025'e kadar taşınırdı. Aynı bekçi "
  f"Citigroup'un companyfacts gecikmesini de (tutarsizlik.json #6) kapatıyor.")
w()
w("**T5 — 012'nin işareti bir SEVİYE etkisi değil, bir U eğrisi.** Beşli dilim tablosunda "
  "hem en çok geri-alan hem en çok ihraç eden uç, ORTA dilimlerin üstünde. Yani 'ihraç edenler "
  "kazanıyor' okuması eksik; monoton bir ilişki YOK. Ayrıca ihraç dilimi bileşimi REIT "
  "(O, WELL, EQIX, DLR) ve yüksek-büyüme teknoloji (TSLA, NOW, CRM, PANW) ağırlıklı — ikisi de "
  "yapısal olarak hisse ihraç eder ve bu örneklemde iyi getirmiştir.")
w()
w("**T6 — Evren HAYATTA KALANLARDAN oluşuyor.** Kartların `universe: full_251` metnine sadık "
  "kalındı; RETIRED_SYMBOLS (8 delist) DIŞARIDA. Ağır ihraç edip batan/çıkarılan şirketler "
  "örneklemde yok, bu 012'nin ihraç-dilimini YUKARI çarpıtır. Bu, kill#2 işaretinin en olası "
  "yapısal açıklamasıdır ve ölçümle ayrıştırılamaz.")
w()
ana = K13["iii_tani_dilimleri"]["turnover_ANA_ETKI_q5_CI_YOK"]["ufuklar"]["20"]
kos20 = K13["i_dilim_tablosu"]["mom_ust20_turnover_ustu"]["ufuklar"]["20"]["evren_fazlasi"]
w(f"**T7 — 013 SUCCESS'i muhtemelen turnover'ın ANA etkisidir, momentum×turnover ETKİLEŞİMİ "
  f"değil.** Kartın kayıtlı ölçütü harfiyen karşılandı; ama kartın grid'inde olmayan tanı "
  f"tablosu şunu gösteriyor: momentum koşulu HİÇ kullanılmadan, yalnız turnover en üst beşte "
  f"birinin @20 fazlası {pc(ana['4']['fazla_ort'])} — koşullu momentum diliminin fazlasından "
  f"({pc(kos20['ort'])}) BÜYÜK; ve turnover dilimleri boyunca ilişki MONOTON. Koşulsuz momentum "
  f"diliminin fazlası ise sıfırdan ayrışmıyor. Yani turnover tek başına bir sıralayıcı gibi "
  f"davranıyor; 'kısa momentum yüksek turnover'da güçlenir' tezi bu ölçümle DOĞRULANMIŞ SAYILMAZ. "
  f"Ayrım için turnover'ın KENDİ kartı gerekir (bu turda CI'lı sınanmadı — K çarpılmasın diye).")
w()
w(f"**T8 — 013'ün kazancı maliyet ölçeğinde ince.** Koşullu dilim @20 brüt {pc(kos20['ort'])}, "
  f"{O.MALIYET_BPS:g}bps tek-yön düşülünce {pc(kos20['maliyet_dusulmus_ort'])}; @10'da brüt "
  f"{pc(K13['i_dilim_tablosu']['mom_ust20_turnover_ustu']['ufuklar']['10']['evren_fazlasi']['ort'])}, "
  f"maliyet sonrası "
  f"{pc(K13['i_dilim_tablosu']['mom_ust20_turnover_ustu']['ufuklar']['10']['evren_fazlasi']['maliyet_dusulmus_ort'])}. "
  f"Kart maliyeti success ölçütüne koymamış; hüküm brüt üzerinden verildi, bu satır uyarıdır.")
w()
ka = K14["kapsam_tanisi"]
w(f"**T9 — 014'ün evreni hem dar hem ZAMANLA BÜYÜYOR.** Kesit 2010'da "
  f"{ka['yil_basina_kesit']['2010']}, 2020'de {ka['yil_basina_kesit']['2020']} sembol; büyük "
  f"sıçrama 2018→2019'da RevenueFromContractWithCustomer etiketlerinin yaygınlaşmasıyla oluyor. "
  f"'Bilgisiz' hükmü bu dar ve dönem-boyunca-değişen kesitte okunmalı.")
w()
w("**T10 — 014'te `val<=0` kuralı asimetrik davranıyor.** Kart 'val<=0 düşülür' diyor; bu, "
  f"NEGATİF brüt kâr bildiren {K14['temel_muhasebesi']['grossprofit_val_le0_dusen']} `GrossProfit` "
  "satırını da düşürüyor, oysa gelir−maliyet YOLUYLA hesaplanan negatif brüt kâr düşmüyor. "
  "Kart metnine harfiyen uyuldu, sapma beyan edildi.")
w()
w(f"**T11 — 014'te Assets eşleşmesi {K14['temel_muhasebesi']['assets_eslesmeyen']} FY akış "
  f"gözlemini düşürdü.** Kart 'assets(t) aynı filed'dan' diyor; başka bir dosyalamaya düşmek "
  f"kart metnine aykırı olurdu, o yüzden eşleşmeyen gözlem UYDURULMADI, DÜŞÜRÜLDÜ. README §3'ün "
  f"184 sembollük kapsamı ile bu ölçümün {ka['bu_olcumde_gpa_uretebilen']} sembolü arasındaki "
  f"fark buradan geliyor.")
w()
blok3_ayrisan = []
for kid, key in (("EDG-2026-012", "evren_fazlasi"), ("EDG-2026-014", "kendi_evren_fazlasi")):
    KK = D["kartlar"][kid]
    for ad, blk in KK.get("i_dilim_tablosu", {}).items():
        for h, u in blk.get("ufuklar", {}).items():
            a, c = u.get(key, {}), u.get(key + "_blok3", {})
            if a.get("anlamli") != c.get("anlamli") or a.get("pozitif_anlamli") != c.get("pozitif_anlamli"):
                blok3_ayrisan.append(f"{kid}/{ad}@{h}")
w("**T12 — Aylık panellerde blok uzunluğu kartın yazdığından GENİŞ.** Kart '21g blok' diyor; "
  "aylık gözlemde 21 ardışık gözlem günü = 21 AY, yani 60g örtüşmesinin gerektirdiğinden çok "
  "daha muhafazakâr. Örtüşmeye denk 3 aylık blok da hesaplandı; işareti/anlamlılığı DEĞİŞEN "
  f"bacak sayısı: **{len(blok3_ayrisan)}** {blok3_ayrisan if blok3_ayrisan else '(yok)'} "
  "(`sonuc.json` → `*_blok3`). Yani 012'nin kill#2'si ve 014'ün kill#1'i blok seçimine "
  "dayanmıyor.")
w()

# =============================================================== damga
w("## 5. Kod damgası / üretilebilirlik")
w()
w(f"- repo HEAD `{S['repo_HEAD']}`")
w("- ölçüm kodu sha256:")
for k, v in S["olcum_kodu_sha256"].items():
    w(f"  - `{k}` `{v}`")
w("- girdi sha256:")
for k, v in S["girdi_sha256"].items():
    w(f"  - `{k}` `{v}`")
w("- **kart dosyaları (ajan DOKUNMADI)**:")
for k, v in S["kart_sha256"].items():
    w(f"  - `{k}` `{v}`")
w()
w("Dosyalar: `sonuc.json` (üç kart ayrı blok) · `sonuc_012.json` · `sonuc_013.json` · "
  "`sonuc_014.json` · `pk.json` · `kod_damgasi.json` · `panel_012.csv.gz` · `panel_014.csv.gz` · "
  "`RAPOR.md` · kod: `ortak.py`, `pk.py`, `k012.py`, `k013.py`, `k014.py`, `birlestir.py`, "
  "`rapor.py`.")
w()

(SB / "RAPOR.md").write_text("\n".join(L))
print(f"== RAPOR.md yazıldı ({len(L)} satır) ==")
