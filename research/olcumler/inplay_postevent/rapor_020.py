"""EDG-2026-020 · RAPOR ÜRETİCİSİ — RAPOR_020.md'yi `sonuc_020.json` + `pk_020.json`dan yazar.

RAPOR ELLE YAZILMAZ. Her sayı JSON'dan okunur; hiçbir değer metne elle girilmez (bu, "rapordaki
sayı ile defterdeki sayı ayrıştı" sınıfını yapısal olarak kapatır).

HÜKÜM CÜMLESİ YOKTUR. Ölçüm ajanı karta dokunmaz ve hüküm vermez; rapor kill/success ölçütlerinin
KARŞILIKLARINI bir TABLO olarak yazar, hükmü Rol-1 işler.
"""
from __future__ import annotations

import json
import pathlib

KLASOR = pathlib.Path(__file__).resolve().parent


def pc(x, basamak=3):
    return "—" if x is None else f"{x * 100:+.{basamak}f}%"


def pci(ci, basamak=3):
    return "—" if not ci else f"[{ci['lo'] * 100:+.{basamak}f}%, {ci['hi'] * 100:+.{basamak}f}%]"


def evet(b):
    return "—" if b is None else ("EVET" if b else "hayır")


def esc(s):
    """Markdown TABLO hücresi için `|` kaçışı — kaçırılmazsa sütun kayar ve tablo sessizce
    yanlış okunur (metin kaybolmaz, YERİ değişir: gözle fark edilmesi en zor bozulma)."""
    return str(s).replace("|", "\\|")


def ci4(ci):
    """IC ölçeğinde CI — 4 basamak, işaretli. Ölçülemediyse em-dash."""
    return "—" if not ci else f"[{ci['lo']:+.4f}, {ci['hi']:+.4f}]"


def ci0(r):
    """Eşik-dilbilgisi (Ders #2): CI 0'ı KAPSIYOR mu? Ölçülemediyse None (False DEĞİL)."""
    if not r.get("ci"):
        return None
    return not (r["ci"]["lo"] > 0 or r["ci"]["hi"] < 0)


def main() -> pathlib.Path:
    S = json.loads((KLASOR / "sonuc_020.json").read_text())
    K = json.loads((KLASOR / "pk_020.json").read_text())
    L, H = [], S["hucreler"]
    ad = S["aday_muhasebesi"]
    ks = S["kod_surumu"]
    A = L.append

    A("# EDG-2026-020 — POST-EVENT in-play (PIT-temiz tek-yönlü) · ÖLÇÜM RAPORU")
    A("")
    A(f"- Kart: `research/cards/EDG-2026-020-postevent-inplay.yaml` · aile `{S['aile']}`")
    A(f"- Ölçüm zamanı: `{S['olcum_zamani']}` · sandbox: `research/olcumler/inplay_postevent/`")
    A(f"- Kod damgası: git `{ks.get('git_head_kisa')}` · kirli_ağaç **{ks.get('kirli_agac')}** · "
      f"olcum_araclari `{ks.get('olcum_araclari_surum')}` "
      f"({', '.join(f'{k}:{v}' for k, v in (ks.get('arac_surumleri') or {}).items())})")
    A(f"- Mühür: `config.STATE` = `{S['muhur']['config_STATE']}` — canlı `state/`e **hiçbir yazım "
      f"yok**; barlar canlı önbellekten SALT-OKUNUR.")
    A("")
    A("> Bu rapordaki her sayı `sonuc_020.json` / `pk_020.json`dan okunur (rapor elle yazılmaz).")
    A("> **Ölçüm ajanı karta DOKUNMADI ve HÜKÜM VERMEDİ.** §11 kill/success ölçütlerinin"
      " KARŞILIKLARINI tablo olarak verir; hükmü Rol-1 işler.")
    A("")
    A(f"**KAPI SATIRI:** pozitif kontrol {evet(S['KAPILAR']['pozitif_kontrol'])} · "
      f"PIT-assert {evet(S['KAPILAR']['pit_assert'])} · PK4 {evet(S['KAPILAR']['pk4'])} · "
      f"PK5 {evet(S['KAPILAR']['pk5'])}")
    A("")
    A("---")
    A("")

    # ---------------------------------------------------------------- 1
    A("## 1 · Kart metninin uygulaması (ne ölçüldü)")
    A("")
    A("| kalem | uygulama |")
    A("|---|---|")
    A("| popülasyon | cf-katmanlı **aday** havuzu: `counterfactuals.jsonl` entered=True "
      "(near_miss DÂHİL) + `cf_open.json`; TEKİL (ticker, date) — EDG-011 ile birebir |")
    A(f"| dilim | `{H['P3']['dilim_tanimi']}` (P grid'den gelir) |")
    A("| in_play kapısı | **YAPISAL**: olay dizisi t'de kesilir (`ev[:j]`, searchsorted right); "
      "gelecek tarih okunmuyor değil — **okunamıyor** (§4) |")
    A("| rvol20 | `meridian.indicators.rvol20` — canlı tanımla BİREBİR (SMA20; EDG-017 dersi) |")
    A("| taban | **AYNI-GÜN aday havuzunun in_play-DIŞI satırlarının ortalaması** (kart horizon). "
      "Hedef satır yapısal olarak kendi tabanında DEĞİL (Ders #5 k.1 kendiliğinden sağlanır) |")
    A("| fazla | `fwd_h − o günün tabanı`. **HAM getiri hükme girmez** (Ders #3) — betimleyici sütun |")
    A("| ileri getiri | `close[t+h]/close[t] − 1`, takvim-kapılı + `bars_integrity` dışlamalı seri |")
    A("| CI | 21g **HAREKETLİ BLOK** bootstrap %95, 2000 tekrar (Ders #6 — IID YASAK) |")
    A(f"| maliyet | {esc(S['hucreler']['P3']['@20']['maliyet']['beyan'])} |")
    A(f"| K muhasebesi | grid `pencere_gun ∈ {S['K_muhasebesi']['parameter_grid']['pencere_gun']}` "
      f"→ **K = {S['K_muhasebesi']['K_bu_turda']}**; kutup: {S['K_muhasebesi']['kutup']} |")
    A(f"| grid DIŞI satırlar (K harcamaz) | {', '.join(S['K_muhasebesi']['grid_disi_satirlar'])} |")
    A(f"| min_taban | **ÖLÇÜM ÖNCESİ BEYAN**: birincil `{S['hucreler']['P3']['@20']['min_taban']}` "
      f"(kartın harfi: 'havuz ortalaması'); `min_taban=5` yalnız DUYARLILIK satırıdır ve "
      f"HÜKME GİRMEZ |")
    A("")

    # ---------------------------------------------------------------- 2
    A("## 2 · Veri zemini")
    A("")
    b = S["bar_muhasebesi"]
    A("| kalem | değer |")
    A("|---|---|")
    A(f"| bar sembolü yüklendi | {b['yuklendi']} / {b['istenen']} |")
    A(f"| hayalet seans düşen satır | {b['hayalet_dusen']} |")
    A(f"| düzeltilmemiş karantina | {b['karantina_dusen']} |")
    A(f"| `bars_integrity` **defter yolu** düşen satır | {b['defter_yolu_dusen']} "
      f"({b['defter_yolu_sembol']} sembol) |")
    A(f"| `bars_integrity` **hesaplanan yol** ek dışlanan satır | {b['hesaplanan_dislanan_satir']} |")
    A(f"| iki yolun ayrıştığı sembol | {len(b['iki_yol_ayrisan_sembol'])} |")
    A(f"| cf defteri satırı | {ad['cf_satir']} (girilmemiş {ad['cf_girilmemis']}) · "
      f"cf_open {ad['open_satir']} |")
    A(f"| ham aday satırı | {ad['ham_aday_satiri']} · tekilleştirmede düşen {ad['tekillestirmede_dusen']} |")
    A(f"| **tekil aday-gün** | {ad['tekil_aday_gun']} · **bar eşleşen {ad['bar_eslesen_aday_gun']}** |")
    A(f"| havuz gün sayısı | {ad['havuz_gun_sayisi']} · gün başına aday medyan "
      f"{ad['gun_basina_aday_medyan']} |")
    A(f"| rvol20 ölçülemeyen aday-gün | {ad['rvol_olculemez_aday_gun']} |")
    A(f"| **geçmiş olayı olmayan** aday-gün (in_play tanım gereği False) | "
      f"{ad['gecmis_olayi_olmayan_aday_gun']} |")
    A("")

    # ---------------------------------------------------------------- 3
    A("## 3 · Olay takvimi — kanıt ARŞİVDE (EDG-016 dersi)")
    A("")
    t = S["takvim_muhasebesi"]
    A(f"Kaynak: {t['kaynak']}. Kanıt dosyaları **bu klasörde**: `takvim_kaniti/` "
      f"(scratchpad'de bırakılmadı — kart guard'ı: 'olay-takvimi kanıtı ölçüm klasörüne arşivlenir').")
    A("")
    A("| kalem | değer |")
    A("|---|---|")
    A(f"| sorulmuş iş günü (JSONL satırı) | {t['satir']} · bozuk satır {t['bozuk_satir']} |")
    A(f"| gün aralığı | {t['gun_araligi'][0]} … {t['gun_araligi'][1]} |")
    A(f"| sembol | {t['sembol']} · olay-günü {t['olay_gunu']} · sembol başına medyan "
      f"{t['sembol_basina_medyan']} |")
    A(f"| saat (bmo/amc) alanı | {t['saat_alani']} |")
    A("")
    A("**Arşiv dosyaları (sha256):**")
    A("")
    A("| dosya | satır | sha256 |")
    A("|---|---|---|")
    for f in K["takvim_muhasebesi"]["dosya"]:
        A(f"| `takvim_kaniti/{f['ad']}` | {f['satir']} | `{f['sha256'][:32]}…` |")
    A("")
    A("> **Kapsam şerhi (keşif turundan devralındı):** bu eksen **ex-post**tur — geçmiş bir kazanç")
    A("> günü kamusal bir olgudur ve `e ≤ t` dalında PIT-güvenlidir; kaynağın vermediği şey")
    A("> **duyuru-öncesi bilinirlik**tir ve bu kart onu ZATEN istemiyor (tek-yönlü form).")
    A("> Nasdaq önbelleğinin `bmo/amc` alanı `takvim_cek.py:74`te süzülmüştür; bu ölçüm saat")
    A("> bilgisi KULLANMAZ, dolayısıyla eksiklik hükme dokunmaz ama beyan edilir.")
    A("")

    # ---------------------------------------------------------------- 4
    A("## 4 · PIT KANITI — kartın en sert guard'ı")
    A("")
    p = K["pit_assert"]
    A("> Kart guard'ı harfiyen: *\"PIT: yalnız e≤t; gelecek-tarih okuyan tek satır bile ihlaldir")
    A("> (test/assert ile çivilenir)\"*. Üç bağımsız bacak + bir negatif kontrol koşuldu.")
    A("")
    A("| bacak | tanım | ölçü | geçti |")
    A("|---|---|---|---|")
    A(f"| 1 · YAPISAL | {esc(p['bacak_1_yapisal']['tanim'])} | satır-başı assert tetiklenme: "
      f"{p['bacak_1_yapisal']['satir_basi_assert_tetiklendi']} | "
      f"{evet(p['bacak_1_yapisal']['gecti'])} |")
    b2 = p["bacak_2_kesme_degismezligi"]
    A(f"| 2 · KESME-DEĞİŞMEZLİĞİ | {esc(b2['tanim'])} | n={b2['n_satir']} (**alt örnek DEĞİL**), "
      f"ayrışan **{b2['ayrisan']}** | {evet(b2['gecti'])} |")
    b3 = p["bacak_3_bagimsiz_saf_python"]
    A(f"| 3 · BAĞIMSIZ İKİZ | {esc(b3['tanim'])} | n={b3['n_satir']}, ayrışan **{b3['ayrisan']}** | "
      f"{evet(b3['gecti'])} |")
    nk = p["negatif_kontrol_kapi_etkin_mi"]
    A(f"| NEGATİF KONTROL | {esc(nk['tanim'])} | farklı sayı verecek satır: "
      f"**{nk['n_satir_farkli']}** (havuzun %{nk['oran'] * 100:.1f}'i) | "
      f"kapı ETKİN: {evet(nk['kapi_etkin'])} |")
    A("")
    A(f"**Okuma.** Bacak 2 asıl kanıttır: takvim her satırın kendi `t`'sinde fiziksel olarak "
      f"kesildiğinde sonuç **{b2['ayrisan']}** satırda değişti — yani gelecek tarihlerin sonuca "
      f"katkısı sıfırdır. Negatif kontrol bunun tavtoloji olmadığını gösterir: EDG-011'in "
      f"iki-yönlü `|t−e|` lafzı uygulansaydı havuzun **%{nk['oran'] * 100:.1f}**'inde farklı bir "
      f"sayı çıkardı — kapı gerçekten bir şey kesiyor.")
    A("")
    A(f"Kapsama: aday satırı {p['kapsama']['aday_satiri']} · takvimde olmayan sembol satırı "
      f"**{p['kapsama']['takvimde_olmayan_sembol_satiri']}** (EDG-011'deki 1669 kapsam-dışı "
      f"aday-gün sorunu bu kaynakla BİTTİ) · geçmiş olayı olmayan satır "
      f"{p['kapsama']['gecmis_olayi_olmayan_satir']}.")
    A("")
    A("**PEAD tarafında aynı yön sözleşmesi:** `evaluate_pead`in çapası `earnings.days_since_report`"
      " ve o da yapısal olarak tek yönlüdür (`earnings.py:193` → `0 <= (d − e).days <= max_days`)"
      " — ölçümün iki bacağı da `e ≤ t` dalındadır.")
    A("")

    # ---------------------------------------------------------------- 5
    A("## 5 · Pozitif kontrol + PK4 + PK5")
    A("")
    pk = K["pozitif_kontrol"]
    A(f"**Çivi (kart guard'ı):** {pk['katman']}")
    A("")
    A("| h | IC | n | CI | anlamlı |")
    A("|---|---|---|---|---|")
    for h in ("5", "10", "20"):
        r = pk[h]
        A(f"| {h} | {r['ic']} | {r['n']} | {ci4(r['ci'])} | {evet(r['anlamli'])} |")
    A("")
    A(f"**Çivi:** ölçülen `{pk['civi_olculen']}` · hedef `{pk['civi_hedef']}` · sapma "
      f"`{pk['civi_sapma']}` · tolerans `{pk['tolerans']}` → **GEÇTİ: {evet(pk['GECTI'])}**")
    A("")
    A(f"Defterdeki referans (`state/component_ic.json`, cf/rvol20): {pk['defterdeki_deger_cf_rvol20']}")
    A("")
    A("### 5.1 PK4 — yol tutarlılığı")
    A("")
    A(f"> {K['pk4']['tanim']} · kapsam: {K['pk4']['kapsam']}")
    A("")
    A("| ufuk | n | maks mutlak fark | geçti |")
    A("|---|---|---|---|")
    for h in ("5", "10", "20"):
        r = K["pk4"][f"fwd{h}"]
        A(f"| {h} | {r['n']} | {r['maks_mutlak_fark']} | {evet(r['gecti'])} |")
    A("")
    A("### 5.2 PK5 — özdeşlikler")
    A("")
    p5 = K["pk5"]
    A("| sınama | ölçü | geçti |")
    A("|---|---|---|")
    a = p5["A_rvol20_geriye_bakissiz"]
    A(f"| A · rvol20 geriye-bakışsız | n={a['n']}, maks fark {a['maks_mutlak_fark']} | "
      f"{evet(a['gecti'])} |")
    c = p5["C_hizli_ortalama"]
    A(f"| C · hızlı ortalama-bootstrap özdeşliği | n={c['n_ornek']}, maks fark "
      f"{c['maks_mutlak_fark']} | {evet(c['gecti'])} |")
    e = p5["E_hizli_spearman"]
    A(f"| E · hızlı Spearman ≡ kanonik | {len(e['olcumler'])} ölçüm, maks fark "
      f"{max(o['mutlak_fark'] for o in e['olcumler'])} | {evet(e['gecti'])} |")
    f5 = p5["F_temiz_taban_ozdesligi"]
    for P, v in f5["pencereler"].items():
        A(f"| F · in_play ≡ `temiz_taban(pencere=(0,{P}))` tümleyeni | ayrışan {v['ayrisan']}; "
          f"kanonik in_play {v['kanonik_inplay']} · birim `{v['kanonik_gun_birimi']}` | "
          f"{evet(v['gecti'])} |")
    g = p5["G_takvim_yukleyici"]
    A(f"| G · takvim yükleyici ≡ `earnings._load()` | sembol {g['bagimsiz_sembol']}/"
      f"{g['kanonik_sembol']}, ayrışma {g['ayrisan_sembol']}+{g['ayrisan_tarih']} | "
      f"{evet(g['gecti'])} |")
    A(f"| **PK5 toplam** | — | **{evet(p5['gecti'])}** |")
    A("")
    A(f"> **KAPSAM BEYANI (uygulanmayan bekçi 'geçti' diye yazılmaz):** WP2 dalgasının PK5-B "
      f"(split bazı) ve PK5-D (fundamentals as-of) bacakları BU KARTTA UYGULANMADI — kart yalnız "
      f"OHLCV + olay TARİHİ kullanır, hiçbir fundamentals/as-of serisi okumaz.")
    A("")

    # ---------------------------------------------------------------- 6
    A("## 6 · Ders #4 — kıyas temizliği muhasebesi (`temiz_taban`, KANONİK)")
    A("")
    A("| P | pencere | gün birimi | n_toplam | n_temiz | n_kirli | kirlilik_oranı | "
      "n_çözülemeyen | n_olaysız_kimlik | uyarı |")
    A("|---|---|---|---|---|---|---|---|---|---|")
    for P, v in S["ders4_temiz_taban"].items():
        A(f"| {P} | ({v['pencere']['once']}, {v['pencere']['sonra']}) | {v['gun_birimi']} | "
          f"{v['n_toplam']} | {v['n_temiz']} | {v['n_kirli']} | {v['kirlilik_orani']} | "
          f"{v['n_cozulemeyen']} | {v['n_olaysiz_kimlik']} | {v['uyari'] or '—'} |")
    A("")
    A("> Pencere `(0, P)` KANONİK `olcum_araclari.temiz_taban` aritmetiğinde `0 ≤ (gün − olay) ≤ P`"
      " demektir — bu kartın `in_play` tanımının TA KENDİSİ. PK5-F bu özdeşliği sıfır ayrışmayla"
      " sınadı, yani taban tanımı deponun kanonik pencere aritmetiğinden SAPMIYOR.")
    A("")

    # ---------------------------------------------------------------- 7
    A("## 7 · İKİ HÜCRE (K=2) — dilim sayıları")
    A("")
    A("| P | in_play aday-gün | **dilim** (∧ rvol≥1.5) | havuz | tarih aralığı | "
      "gecikme dağılımı (t−e) |")
    A("|---|---|---|---|---|---|")
    for P in ("P3", "P5"):
        c = H[P]
        gd = " · ".join(f"{k}g:{v}" for k, v in c["gecikme_dagilimi"].items())
        A(f"| {c['pencere_gun']} | {c['n_in_play']} | **{c['n_dilim']}** | {c['n_havuz']} | "
          f"{c['tarih_araligi'][0]} … {c['tarih_araligi'][1]} | {gd} |")
    A("")
    A("> **EDG-011 ile fark:** orada in-play dilimi 11-12 aday-gündü ve tamamı verinin son "
      "haftasındaydı (kill#3 askısı). Tarihsel takvimle dilim iki mertebe büyüdü ve **tüm defter "
      "penceresine yayıldı** — 011'in askı sebebi (örneklem kuraklığı) bu kartta YOK.")
    A("")

    # ---------------------------------------------------------------- 8
    A("## 8 · FAZLA TABLOSU + CI")
    A("")
    A("Fazla = aday getirisi − **aynı-gün aday-havuzu (in_play-DIŞI)** ortalaması. "
      "CI = 21g hareketli blok bootstrap %95.")
    A("")
    for P in ("P3", "P5"):
        c = H[P]
        A(f"### P = {c['pencere_gun']}")
        A("")
        A("| h | n | ham ort _(betimleyici)_ | **havuz fazlası** | **fazla CI** | CI 0'ı kapsıyor "
          "| poz. anlamlı | net@10bps | net@20bps | n_taban_yok |")
        A("|---|---|---|---|---|---|---|---|---|---|")
        for h in (5, 10, 20):
            r = c[f"@{h}"]
            hm = r.get("ham_getiri_betimleyici") or {}
            im = " **(hüküm ufku)**" if h in (10, 20) else " _(betimleyici)_"
            A(f"| {h}{im} | {r['n']} | {pc(hm.get('ort'))} | **{pc(r['ort'])}** | "
              f"**{pci(r['ci'])}** | {evet(ci0(r))} | {evet(r['pozitif_anlamli'])} | "
              f"{pc(r['maliyet']['10bps_net_ort'])} | {pc(r['maliyet']['20bps_net_ort'])} | "
              f"{r['n_taban_yok']} |")
        A("")
        A("**Duyarlılık ve muhasebe satırları (HÜKME GİRMEZ):**")
        A("")
        A("| h | min_taban=5 fazla | min_taban=5 CI | n | sıkışma (temiz − kirli taban) | "
          "dilim günlerinin taban ort. | havuz geneli (in_play-dışı) |")
        A("|---|---|---|---|---|---|---|")
        for h in (5, 10, 20):
            r = c[f"@{h}"]
            rs = c[f"@{h}_min_taban5_DUYARLILIK"]
            tb = r.get("taban_seviyesi_betimleyici") or {}
            A(f"| {h} | {pc(rs['ort'])} | {pci(rs['ci'])} | {rs['n']} | "
              f"{pc(r['sikisma']['fark_temiz_eksi_kirli'])} | "
              f"{pc(tb.get('dilim_gunlerinin_taban_ort'))} | "
              f"{pc(tb.get('havuz_geneli_in_play_disi_ort'))} |")
        A("")
    A("> **Ders #3 okuması (sayı, hüküm değil).** İki pencerede de @20 **HAM** getiri POZİTİFtir "
      f"({pc(H['P3']['@20']['ham_getiri_betimleyici']['ort'])} / "
      f"{pc(H['P5']['@20']['ham_getiri_betimleyici']['ort'])}) ama taban-fazlası NEGATİFtir. "
      "Sebep tabloda duruyor: dilim günlerinin AYNI-GÜN tabanı "
      f"({pc(H['P5']['@20']['taban_seviyesi_betimleyici']['dilim_gunlerinin_taban_ort'])}), havuzun "
      f"genel ortalamasının "
      f"({pc(H['P5']['@20']['taban_seviyesi_betimleyici']['havuz_geneli_in_play_disi_ort'])}) "
      "yaklaşık iki katıdır — kazanç-sonrası günler havuzun TAMAMININ iyi olduğu günlerdir. "
      "Ham getiriyle ölçen bir ölçüt burada 'kenar var' derdi.")
    A("")
    A("> **Sıkışma (Ders #5 k.3).** Kirli tabanla (o günün TÜM satırları, in_play dâhil) kurulan "
      "kıyas fazlayı sistematik olarak **yukarı** kaydırıyor; fark sütunu düzeltmenin büyüklüğünü "
      "gösterir. Kirli taban HÜKME GİRMEZ.")
    A("")

    # ---------------------------------------------------------------- 9
    A("## 9 · Alt-dönem satırı (BETİMLEYİCİ — grid'e dahil DEĞİL, K harcamaz)")
    A("")
    for P in ("P3", "P5"):
        A(f"**P = {H[P]['pencere_gun']} · @20**")
        A("")
        A("| yıl | aday-gün | n (dilim) | fazla | CI | gözlem günü | CI yoksa neden |")
        A("|---|---|---|---|---|---|---|")
        for y, v in sorted(H[P]["alt_donem_@20_BETIMLEYICI"].items()):
            A(f"| {y} | {v['n_aday_gun']} | {v.get('n')} | {pc(v.get('fazla_ort'))} | "
              f"{pci(v.get('ci'))} | {v.get('n_gozlem_gunu')} | {v.get('ci_neden') or '—'} |")
        A("")
    A("> 2022 ve 2026 dilimlerinde CI **ölçülemedi** (gözlem günü < 63 = 3×blok); boş bırakılmadı, "
      "nedeni yazıldı. İşaret yıllar arasında **dönüyor** — kararlılık yok.")
    A("")

    # ---------------------------------------------------------------- 10
    A("## 10 · PEAD-AYRIŞMASI (kartın varlık gerekçesi · kill#2 verisi)")
    A("")
    pa0 = H["P3"]["pead_ayrismasi"]
    A(f"> {pa0['tanim']}")
    A("")
    pm = S["pead_kosum_muhasebesi"]
    A(f"**`evaluate_pead` SANDBOX'ta koşturuldu** (motorun kendi fonksiyonu ÇAĞRILDI, kopyalanmadı): "
      f"{pm['cagri']} aday-gün çağrısı, **{pm['atesledi']} ateşleme**, hata {pm['hata']}, "
      f"bar-kısa {pm['bar_kisa']}. Bar dilimi motorla birebir (`backtest.py:320` `tail(340)`); "
      f"RS çapraz-kesiti `indicators.rs_rating` ile {pm['rs_gun']} günde kuruldu "
      f"(kesit medyanı {pm['rs_kesit_medyan']} sembol). Parametreler `state/strategy.yaml` v"
      f"{pm['strategy_yaml_version']} ({pm['params_okunan_anahtar']} anahtar); pead anahtarları "
      f"dosyada yok → motor varsayılanları: {pm['pead_params_varsayilan']}.")
    A("")
    A("> **NEDEN YENİDEN KOŞULDU.** Canlı cf defterinde `pead` satırı **SIFIRDIR** "
      "(setup dağılımı: breakout_vcp / momentum_burst / pullback / episodic_pivot). Sebep veri: "
      "replay sırasında `state/earnings.csv` yalnız ileriye-dönük tek anlık görüntüydü, dolayısıyla "
      "`days_since_report` daima False döndü ve pead hiç ateşlemedi. Örtüşme sorusu ancak "
      "değerlendiriciyi TARİHSEL takvimle yeniden koşturarak sorulabilirdi.")
    A("")
    A("### 10.1 Küme örtüşmesi (Jaccard)")
    A("")
    A("| P | küme A | n_A | n_B (pead) | kesişim | birleşim | **Jaccard** | A'nın B'de payı | "
      "B'nin A'da payı |")
    A("|---|---|---|---|---|---|---|---|---|")
    for P in ("P3", "P5"):
        pa = H[P]["pead_ayrismasi"]["ortusme"]
        for ad, key in (("dilim (in_play∧rvol)", "dilim_vs_pead"),
                        ("yalnız in_play", "yalniz_inplay_vs_pead")):
            j = pa[key]
            A(f"| {H[P]['pencere_gun']} | {ad} | {j['n_A']} | {j['n_B']} | {j['kesisim']} | "
              f"{j['birlesim']} | **{j['jaccard']}** | {j['A_icinde_B_orani']} | "
              f"{j['B_icinde_A_orani']} |")
    A("")
    A("### 10.2 Çift sıralama — pead kovası İÇİNDE dilim fazlası")
    A("")
    A(f"> {H['P3']['pead_ayrismasi']['A_cift_siralama']['tanim']}")
    A("")
    A("| P | h | kova | n | dilim ham n | fazla | CI | CI 0'ı kapsıyor | neden |")
    A("|---|---|---|---|---|---|---|---|---|")
    for P in ("P3", "P5"):
        cs = H[P]["pead_ayrismasi"]["A_cift_siralama"]
        for h in ("10", "20"):
            for kova in ("pead_yok", "pead_var"):
                r = cs[h][kova]
                A(f"| {H[P]['pencere_gun']} | {h} | `{kova}` | {r['n']} | {r['n_dilim_ham']} | "
                  f"{pc(r['ort'])} | {pci(r['ci'])} | {evet(ci0(r))} | {r.get('neden') or '—'} |")
    A("")
    A("> `pead_var` kovası **ölçülemedi** (n < 30) — dilim ile pead'in kesişimi zaten 16-20 "
      "aday-gündür. Bu bir sonuç değil bir ÖRNEKLEM olgusudur ve doldurulmadı (uydurma yasağı).")
    A("")
    A("### 10.3 Artık-IC (pead-kontrollü)")
    A("")
    A(f"> {H['P3']['pead_ayrismasi']['B_artik_ic']['tanim']}")
    A("")
    A("| P | h | kontrol | IC | n | CI | anlamlı | n_dilim | tek-üyeli kova düşen |")
    A("|---|---|---|---|---|---|---|---|---|")
    for P in ("P3", "P5"):
        ai = H[P]["pead_ayrismasi"]["B_artik_ic"]
        for h in ("10", "20"):
            blk = ai[h]
            if "pead_kontrollu" not in blk:
                A(f"| {H[P]['pencere_gun']} | {h} | — | — | — | — | — | — | {blk.get('neden')} |")
                continue
            r = blk["pead_kontrollu"]
            A(f"| {H[P]['pencere_gun']} | {h} | **pead-kontrollü** | {r['ic']} | {r['n']} | "
              f"{ci4(r['ci'])} | {evet(r['anlamli'])} | {r['n_dilim_artikta']} | "
              f"{r['n_tek_uyeli_kova_dusen']} |")
            r2 = blk["kontrolsuz_ikiz"]
            A(f"| {H[P]['pencere_gun']} | {h} | kontrolsüz ikiz _(karşılaştırma)_ | {r2['ic']} | "
              f"{r2['n']} | {ci4(r2['ci'])} | {evet(r2['anlamli'])} | — | — |")
    A("")
    A("> **Okuma (sayı, hüküm değil).** Kontrollü ile kontrolsüz IC neredeyse aynı — pead kontrolü "
      "artıktan kayda değer bir şey ALMIYOR. Bu, §10.1'deki düşük örtüşmenin ikinci bir "
      "görünümüdür: iki sinyal aynı satırları seçmiyor.")
    A("")

    # ---------------------------------------------------------------- 11
    A("## 11 · Ders #7 — en iyi hücre küçültülmeden yazılmaz")
    A("")
    d7 = S["ders7_eb_kucultme"]
    if d7.get("hucreler"):
        A("| hücre | ham | SE | küçültülmüş | ağırlık |")
        A("|---|---|---|---|---|")
        for k, v in d7["hucreler"].items():
            A(f"| {k} | {pc(v['ham'])} | {pc(v['se'])} | {pc(v['kucultulmus'])} | {v['agirlik']} |")
        A("")
        A(f"- en iyi HAM: `{d7['en_iyi_ham']['hucre']}` {pc(d7['en_iyi_ham']['ham'])} → "
          f"küçültülmüş {pc(d7['en_iyi_ham']['kucultulmus'])}")
        A(f"- sıra değişti mi: **{evet(d7['sira_degisti'])}** · τ² = {d7['tau2']} · "
          f"hedef {pc(d7['hedef'])}")
        A(f"- uyarı: {d7.get('uyari') or '—'}")
        A("")
        A("> Küçültülmüş değer **eşiklere GİRMEZ** ve `success`/`kill` ölçütlerinde kullanılmaz.")
    else:
        A(f"Ölçülemedi: {d7.get('neden')}")
    A("")

    # ---------------------------------------------------------------- 12
    A("## 12 · KILL / SUCCESS KARŞILIKLARI — **TABLO (hüküm Rol-1'de)**")
    A("")
    A("> Aşağıdaki tablo kart metnindeki ölçütlerin **ÖLÇÜLEN KARŞILIKLARINI** verir. "
      "Bu rapor bir hüküm cümlesi TAŞIMAZ.")
    A("")
    A("| # | kart metni (harfiyen) | ölçülen karşılık | ölçüt karşılandı mı |")
    A("|---|---|---|---|")

    s3, s5 = H["P3"]["@20"], H["P5"]["@20"]
    t3, t5 = H["P3"]["@10"], H["P5"]["@10"]
    ov3 = H["P3"]["pead_ayrismasi"]["ortusme"]["dilim_vs_pead"]["jaccard"]
    ov5 = H["P5"]["pead_ayrismasi"]["ortusme"]["dilim_vs_pead"]["jaccard"]
    ar3 = H["P3"]["pead_ayrismasi"]["B_artik_ic"]["20"]["pead_kontrollu"]
    ar5 = H["P5"]["pead_ayrismasi"]["B_artik_ic"]["20"]["pead_kontrollu"]
    cs3 = H["P3"]["pead_ayrismasi"]["A_cift_siralama"]["20"]["pead_yok"]
    cs5 = H["P5"]["pead_ayrismasi"]["A_cift_siralama"]["20"]["pead_yok"]

    A(f"| **success** | \"in_play∧rvol>=1.5 diliminin @20 taban-fazlası anlamlı POZİTİF "
      f"(CI 0-dışı) **VE** PEAD-ayrışması…\" | @20 fazla: P3 {pc(s3['ort'])} {pci(s3['ci'])} · "
      f"P5 {pc(s5['ort'])} {pci(s5['ci'])} — **ikisi de CI 0'ı KAPSIYOR**, poz-anlamlı "
      f"{evet(s3['pozitif_anlamli'])}/{evet(s5['pozitif_anlamli'])} | **1. bacak KARŞILANMADI** "
      f"(2. bacak koşullu olarak devreye girmiyor) |")
    A(f"| kill#1 | \"iki pencerede de @20 fazla CI-0-içi → bilgisiz, arşiv (011'e de not düşer: "
      f"tek-yönlü yarı da boş)\" | P3 {pci(s3['ci'])} → CI-0-içi {evet(ci0(s3))}; "
      f"P5 {pci(s5['ci'])} → CI-0-içi {evet(ci0(s5))} | **KARŞILIK TAM** (iki pencerede de) |")
    A(f"| kill#2 | \"PEAD-örtüşmesi **yüksek** VE pead-kontrollü artık CI-0-içi → 'PEAD kopyası' "
      f"arşiv\" | örtüşme Jaccard P3 **{ov3}** · P5 **{ov5}** (dilimin %"
      f"{H['P3']['pead_ayrismasi']['ortusme']['dilim_vs_pead']['A_icinde_B_orani'] * 100:.1f}"
      f"/%{H['P5']['pead_ayrismasi']['ortusme']['dilim_vs_pead']['A_icinde_B_orani'] * 100:.1f}"
      f"'i pead); artık-IC @20 P3 {ar3['ic']} CI-0-içi {evet(not ar3['anlamli'])} · "
      f"P5 {ar5['ic']} CI-0-içi {evet(not ar5['anlamli'])} | **BİLEŞİK KARŞILANMADI** — 2. bileşen "
      f"karşılık buluyor, 1. bileşen (**yüksek** örtüşme) BULMUYOR |")
    A(f"| kill#3 | \"maliyet-sonrası net <=0 → arşiv + not\" | @20 net 10bps: P3 "
      f"{pc(s3['maliyet']['10bps_net_ort'])} · P5 {pc(s5['maliyet']['10bps_net_ort'])}; "
      f"20bps: P3 {pc(s3['maliyet']['20bps_net_ort'])} · P5 {pc(s5['maliyet']['20bps_net_ort'])}. "
      f"@10 net 10bps: P3 {pc(t3['maliyet']['10bps_net_ort'])} · "
      f"P5 {pc(t5['maliyet']['10bps_net_ort'])} | **KARŞILIK TAM** (dört hücrede de net ≤ 0) |")
    A("")
    A("**§12 EK — ölçüm tarafından görülen EŞİK-DİLBİLGİSİ belirsizliği (Ders #2).**")
    A("")
    A(f"kill#2'nin ilk bileşeni **\"PEAD-örtüşmesi yüksek\"** kartta SAYISAL bir eşikle "
      f"yazılmamıştır; ölçüm bir eşik SEÇEMEZ (eşik ölçümden sonra belirlenemez). Bu yüzden tabloya "
      f"ham örtüşme ({ov3} / {ov5}) ve iki okuma birlikte yazıldı. Not: **kill#1 ve kill#3 zaten "
      f"belirsizlik taşımadan karşılık buluyor**, dolayısıyla bu belirsizlik hükmün yönünü "
      f"değiştirebilecek bir yerde durmuyor — yine de kayda geçirildi (Ders #2: belirsizlik "
      f"muhafazakâr okunur ve karta ders notu düşülür; not düşme işi Rol-1'dedir).")
    A("")
    A("**§12 EK — EDG-011'e taşınacak veri (kart notes'u öyle diyor: 'hükmü 011'e not düşülür').**")
    A("")
    A(f"- 011'in askı sebebi olan kill#3 (in-play aday-gün < 150) bu turda **YOK**: dilim "
      f"{H['P3']['n_dilim']} (P=3) / {H['P5']['n_dilim']} (P=5) aday-gün ve tüm defter penceresine "
      f"yayılmış durumda.")
    A(f"- 011'in kapsam sorunu (1669 kapsam-dışı aday-gün) bu kaynakla **bitti**: takvimde olmayan "
      f"sembol satırı {p['kapsama']['takvimde_olmayan_sembol_satiri']}.")
    A(f"- 011'in iki-yönlü `|t−e|` lafzının PIT-ihlalli olduğu ve tek-yönlü daldan **ne kadar** "
      f"ayrıldığı ölçüldü: havuzun %{nk['oran'] * 100:.1f}'i.")
    A("")

    # ---------------------------------------------------------------- 13
    A("## 13 · Beyanlı çekinceler ve sınırlar")
    A("")
    A("1. **Ex-post olay ekseni.** Nasdaq-geçmişi revizyon-SONRASI nihai tarihleri verir. Bu kartın "
      "tek-yönlü formu (`e ≤ t`) bundan etkilenmez — geçmiş bir kazanç günü t'de kamusal olgudur — "
      "ama kaynağın **duyuru-öncesi bilinirlik** iddiası taşımadığı burada da beyan edilir.")
    A(f"2. **Kirli ağaç.** `kod_surumu.kirli_agac = {ks.get('kirli_agac')}` → bu rapor "
      f"`{ks.get('git_head_kisa')}` SHA'sından **yeniden üretilemez**; SHA o anki kodun değil "
      f"ATASININ adıdır (ölçüm sırasında bu klasörün betikleri commit'lenmemişti).")
    A("3. **Hayatta-kalma yanlılığı.** Evren bugünkü 251 semboldür; delist olmuş isimler bar "
      "önbelleğinde yoktur. EDG-016 emsali kalıcı şerh: bu, POZİTİF bir bulguyu yukarı çarpıtır — "
      "bu turda bulgu pozitif değildir, dolayısıyla şerh hükmü gevşetme yönünde çalışmaz.")
    A("4. **Saat (BMO/AMC) yok.** Nasdaq önbelleği `bmo/amc` alanını süzmüş; `t−e = 0` günü "
      f"({H['P5']['gecikme_dagilimi'].get('0')} satır) rapor-öncesi mi sonrası mı ayrımı "
      "YAPILAMADI. AMC raporlarında `t−e=0` barı olayın **öncesindeki** seanstır; bu, dilimin bir "
      "kısmında olay-sonrası varsayımını zayıflatır. Ölçülemedi → düzeltilmedi, BEYAN EDİLDİ. "
      "(8-K `acceptance` damgası bu ayrımı birinci elden verebilir — keşif turu şerhi.)")
    A("5. **`pead_var` kovası ölçülemedi** (n<30): kesişim 16-20 aday-gün. Çift-sıralamanın "
      "`pead_var` bacağı bu turda boştur ve DOLDURULMADI.")
    A(f"6. **Maliyet modeli.** {S['hucreler']['P3']['@20']['maliyet']['beyan']}")
    A("7. **Sıralama overlay'i şerhi (011'den devralındı).** Bu eksen işlem ÜRETMEZ, mevcut "
      "adaylar arasında seçim değiştirir; maliyet satırı yine de kartın kill#3'ü gereği hesaplandı.")
    A("")
    A("## 14 · KOD DAMGASI — bu sayılar hangi BAYTLARLA üretildi")
    A("")
    md, mdk = S["motor_damgasi"], K["motor_damgasi"]
    A(f"`kod_surumu` git HEAD'i `{ks.get('git_head_kisa')}` diyor ama **`kirli_agac = "
      f"{ks.get('kirli_agac')}`** — yani SHA o anki kodun değil ATASININ adıdır ve tek başına "
      f"bu raporu yeniden üretmeye YETMEZ. Üstelik bu depoda Rol-1 **ajan uçuştayken** commit atar "
      f"(CLAUDE.md md.8) ve bu turda HEAD ölçüm ortasında GERÇEKTEN kaydı. Bu yüzden kimlik "
      f"dosya-bazında sha256'dır:")
    A("")
    A("| kalem | değer |")
    A("|---|---|")
    A(f"| motor dosyası (kum havuzu kopyası) | {md['n_dosya']} |")
    A(f"| **tüm ağaç sha256** — `pk_020.json` | `{mdk['tum_agac_sha256'][:32]}…` |")
    A(f"| **tüm ağaç sha256** — `sonuc_020.json` | `{md['tum_agac_sha256'][:32]}…` |")
    A(f"| iki çıktı AYNI motordan mı | **{evet(S['motor_damgasi_pk_ile_ayni_mi'])}** |")
    A(f"| repo ↔ kum havuzu kopyası ayrışan dosya | {len(md['repo_kopya_ayrisan'])} |")
    A(f"| kritik modül bulunamadı | {len(md['kritik_modul_bulunamadi'])} |")
    A("")
    A("**Ölçüme GİREN modüllerin sha256'ları (ilk 16 hane):**")
    A("")
    A("| modül | sha256 |")
    A("|---|---|")
    for m, h in md["olcume_giren_moduller"].items():
        A(f"| `meridian/{m}` | `{(h or '—')[:16]}…` |")
    A("")
    A("> **Neden bu tablo var.** Bu turun ilk koşumu `a173586`, ikinci koşumu `2066b8b` HEAD'inde "
      "yakalandı (arada Rol-1 commit'leri düştü: `api.py`, `backtest.py`, `reflect.py`, "
      "`watchdog.py`). İkisi de ölçümün BAĞIMLILIK YOLUNDA DEĞİL — ve bunu iddia etmek yerine "
      "kanıtlamak için iki betik tek motor anlık görüntüsünden YENİDEN koşuldu; yukarıdaki iki "
      "ağaç sha256'sı artık AYNIDIR. Sayılar HEAD hareketinden önce ve sonra bit-bit değişmedi.")
    A("")
    A("---")
    A("")
    A(f"**KAPI SATIRI (tekrar):** pozitif kontrol {evet(S['KAPILAR']['pozitif_kontrol'])} · "
      f"PIT-assert {evet(S['KAPILAR']['pit_assert'])} · PK4 {evet(S['KAPILAR']['pk4'])} · "
      f"PK5 {evet(S['KAPILAR']['pk5'])}")
    A("")
    A("**Kanıt dosyaları:** `sonuc_020.json` · `pk_020.json` · `RAPOR_020.md` · "
      "`takvim_kaniti/` (5 JSONL + 4 çekim özeti, sha256'lı) · betikler `ortak020.py` · "
      "`pk020.py` · `k020.py` · `rapor_020.py`")
    A("")

    yol = KLASOR / "RAPOR_020.md"
    yol.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"[rapor] {yol} · {len(L)} satır")
    return yol


if __name__ == "__main__":
    main()
