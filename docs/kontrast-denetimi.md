# Kontrast denetimi — Meridian panosu (WCAG 2.2 AA, iki tema)

> **Bilet:** UIUX S1-T2 (`docs/UIUX-WORKORDER.md` § Program V / Program X · `docs/UIUX-WP0.md` borç #5).
> **Tarih:** 2026-08-01. **Kapsam:** `meridian/web/index.html` `<style>` bloğundaki 59 jeton,
> iki temada, ve bu jetonların panoda fiilen kurduğu 136 çift.
> **BU RAPOR DEĞER DEĞİŞTİRMEZ.** Kalan her çift için hüküm önerisi §7'de durur ve hiçbiri
> uygulanmadı — jeton yeniden-değerlemesi (gündüz beyazı dahil) WP0 kararıyla ayrı bir onay
> turudur. Bu turda tek bir renk kımıldamadı.

## 1 · Yöntem

Her oran WCAG 2.x göreli-luminans formülüyle hesaplandı (`0.2126R + 0.7152G + 0.0722B`,
sRGB doğrusallaştırmasıyla), eşik metin için **4.5:1**, metin-dışı için **3:1** (WCAG 2.2
1.4.3 / 1.4.11).

Üç yöntem kuralı, ve her birinin neyi engellediği:

1. **BİLEŞİK ZEMİN, HAM JETON DEĞİL.** Alfa taşıyan her katman 8-bit sRGB'de `source-over`
   ile bileşiklenir — tarayıcının fiilen yaptığı işlem. Bir çipin mürekkebi karta karşı
   değil, çipin **kendi %10 tintinin karta bileşiklenmiş hâline** karşı ölçülür
   (DESIGN.md § The Own-Ground Rule). Bunu atlamak, ekranda hiç var olmayan bir zemini
   ölçmektir ve düşen bir çipi denetimden geçirir.
2. **ALFA TAŞIYAN MÜREKKEP DE BİLEŞİKLENİR.** Çip iç saç telleri %35, sakin damga %55,
   bayatlık solması %42–78, hücre tinti %7–8. Bunları opak sanmak, aşağıdaki 42 kalanın
   yarısını görünmez yapardı. (Bu raporun DESIGN.md'den ayrıldığı ilk yer — bkz. §8.)
3. **ZEMİN, KURALDAN OKUNUR.** Çift listesi `index.html`'in kurallarından çıkarıldı
   (`color:` bildirimi olan her kural + o kuralın miras aldığı zemin), tahminle değil.

Ölçüm kaynak-çivilidir: §9'daki çivi tablosunun her satırı
`tests/test_tasarim_token_v153.py::test_rapordaki_KONTRAST_RAKAMLARI_yeniden_uretilebilir`
tarafından kaynaktan yeniden hesaplanır. Bir jeton değerlenirse bu rapor **bayat ilan
edilir** — çünkü sessizce eskimiş bir erişilebilirlik raporu, hiç yapılmamış bir
denetimden daha kötüdür: okuyucu ona güvenir.

**Ölçülmeyen ve bu raporun kapsamadığı şey:** gerçek tarayıcıda render edilmiş piksel
(yerel sunucu YASAK — CLAUDE.md §5), alt-piksel/antialias etkisi, `backdrop-filter:blur`
sonrası fiilî bileşke (üst bar ve modal perdesi için zeminin bulanık ortalaması
alınır; burada bulanıksız zemin ölçüldü, ki bu **kötümser değil iyimser** olabilir),
ve renk körlüğü simülasyonu (Program X'in ayrı kalemi).

## 2 · Özet

| | çift | geçti | kaldı |
|---|---|---|---|
| **Metin (4.5:1)** | 71 | 65 | **6** |
| **Metin-dışı (3:1)** | 65 | 29 | **36** |
| **TOPLAM** | **136** | **94** | **42** |

Kalanların dağılımı bir tesadüf değil, bir tasarım hükmünün faturası:

- **36 metin-dışı kalanın 28'i saç teli, ray ve ton basamağıdır** — yani "kutu değil saç
  teli, gölge değil ton" kararının doğrudan sonucu. Bunlar DESIGN.md'de zaten **beyanlı
  sapma**; §6'da gerekçeleriyle durur ve bu turda da açık kalır.
- **8'i beyansızdır ve bu raporun asıl bulgusudur** (§5): yoğunluk merdiveninin son iki
  basamağı aynı renk, IC-trend grafiğinin iki serisi aynı renk, bullet ölçüm çubuğu gece
  en koyu bandın üstünde kayboluyor, ve bayatlık solmasının 2./3. kademesi okunaklılığın
  altına iniyor.
- **6 metin kalanının tamamı `opacity` ile soldurulmuş metindir.** Hiçbiri jeton
  değerinden gelmiyor; hepsi kuralın içindeki bir opaklık çarpanından geliyor. Yani
  panonun **renk paleti AA'yı geçiyor, opaklık disiplini geçmiyor.**

Metin katmanının çekirdeği — gövde mürekkebi (9/9), vurgu (8/8), para renkleri (31/31),
dolgu üstü ters mürekkep (3/3) — **iki temada da tam geçer** ve en kötü gerçek bileşik
zeminde bile pay bırakır (en dar: `--red` kendi tintinde gömülü panelde **4.78**, gündüz).

## 3 · Tam tablo

Her satır: çift · L1 (mürekkep, bileşiklenmiş) · L2 (zemin, bileşiklenmiş) · oran ·
eşik · hüküm. Hex değerleri `gündüz/gece` sırasıyla verilir.

### A · gövde mürekkebi
| çift | L1 (mürekkep) | L2 (zemin) | gündüz | gece | eşik | hüküm |
|---|---|---|---|---|---|---|
| `--tx` — body · sayfa gövdesi | #050505/#d4d0cb | #ffffff/#1c1a18 | **20.38** | **11.31** | 4.5:1 | geçti |
| `--tx` — kbd · girdi · .ksgroup düğmesi · .pm-strip · .pane | #050505/#d4d0cb | #fbfaf8/#232120 | **19.54** | **10.45** | 4.5:1 | geçti |
| `--tx` — .card/.hero/.gate-card/.kbd-panel/.ksgroup/.gloss içi | #050505/#d4d0cb | #f8f5f2/#262320 | **18.76** | **10.18** | 4.5:1 | geçti |
| `--tx` — .sitem:hover · .rowbtn:hover · .mcard:hover · .hyp:hover | #050505/#d4d0cb | #f1ece8/#2f2b27 | **17.38** | **9.15** | 4.5:1 | geçti |
| `--tx` — .rowbtn.sel · .sitem.tema:hover · palet seçili satır | #050505/#d4d0cb | #f3f3f3/#302c28 | **18.37** | **9.02** | 4.5:1 | geçti |
| `--tx` — .spine.attn .msg | #050505/#d4d0cb | #f0ede6/#30281a | **17.43** | **9.48** | 4.5:1 | geçti |
| `--tx` — .spine.act .msg | #050505/#d4d0cb | #f7e9ea/#322524 | **17.27** | **9.60** | 4.5:1 | geçti |
| `--tx` — kart içi kehribar çip metni | #050505/#d4d0cb | #eae4da/#393021 | **16.12** | **8.45** | 4.5:1 | geçti |
| `--tx` — en kötü gerçek bileşik | #050505/#d4d0cb | #ebd8d5/#433531 | **14.86** | **7.64** | 4.5:1 | geçti |

### B · ikincil mürekkep
| çift | L1 (mürekkep) | L2 (zemin) | gündüz | gece | eşik | hüküm |
|---|---|---|---|---|---|---|
| `--tx2` — .subline · .sessizhat · .hint · footer | #585450/#b0a9a0 | #ffffff/#1c1a18 | **7.50** | **7.46** | 4.5:1 | geçti |
| `--tx2` — .mono · .pd-* çekmece etiketleri · .pane | #585450/#b0a9a0 | #fbfaf8/#232120 | **7.19** | **6.89** | 4.5:1 | geçti |
| `--tx2` — .statuspill · .hudchip · .bl-lab · .bl-ax · .gc.arrow · kart etiketleri | #585450/#b0a9a0 | #f8f5f2/#262320 | **6.91** | **6.72** | 4.5:1 | geçti |
| `--tx2` — .sitem:hover .sub · hover satırları | #585450/#b0a9a0 | #f1ece8/#2f2b27 | **6.40** | **6.04** | 4.5:1 | geçti |
| `--tx2` — .slabel komşu metin · seçili satır alt-okuma | #585450/#b0a9a0 | #f3f3f3/#302c28 | **6.76** | **5.95** | 4.5:1 | geçti |
| `--tx2` — yeşil çip içi ikincil | #585450/#b0a9a0 | #e0e7e0/#2a332b | **5.96** | **5.62** | 4.5:1 | geçti |
| `--tx2` — kehribar çip içi ikincil | #585450/#b0a9a0 | #eae4da/#393021 | **5.93** | **5.58** | 4.5:1 | geçti |
| `--tx2` — kırmızı çip içi ikincil | #585450/#b0a9a0 | #f1e0de/#3b2d2b | **5.88** | **5.66** | 4.5:1 | geçti |
| `--tx2` — en kötü gerçek bileşik (DESIGN.md hükmü) | #585450/#b0a9a0 | #ebd8d5/#433531 | **5.47** | **5.04** | 4.5:1 | geçti |
| `--tx2` — kehribar çip / gömülü panel | #585450/#b0a9a0 | #e4dcd1/#413828 | **5.52** | **4.96** | 4.5:1 | geçti |
| `--tx2` — .pm-n pozitif hücrede | #585450/#b0a9a0 | #ecf3ef/#202821 | **6.66** | **6.51** | 4.5:1 | geçti |
| `--tx2` — .pm-n negatif hücrede | #585450/#b0a9a0 | #faf0f0/#2b2220 | **6.71** | **6.68** | 4.5:1 | geçti |
| `--tx2` — .statuspill üst barda (kart opak, bar altta) | #585450/#b0a9a0 | #ffffff/#1c1a18 | **7.50** | **7.46** | 4.5:1 | geçti |
| `--slip-ink` — .term::after ipucu (slip-ink) | #050505/#d4d0cb | #f1ece8/#2f2b27 | **17.38** | **9.15** | 4.5:1 | geçti |
| `--tx2@0.7` — .sitem .sub (opacity .7) rayda | #8a8784/#847e77 | #ffffff/#1c1a18 | **3.57** | **4.32** | 4.5:1 | KALDI |
| `--tx2@0.7` — .pm-none (opacity .7) ekilmemiş hücrede | #898682/#86807a | #fbfaf8/#232120 | **3.47** | **4.11** | 4.5:1 | KALDI |
| `--tx2@0.45` — .sessizhat .sh-sep (opacity .45) | #b4b2b0/#5f5a55 | #ffffff/#1c1a18 | **2.11** | **2.54** | 3.0:1 | KALDI |
| `--tx2@0.78` — .bayat-1 (opacity .78) sayfa zemininde | #7d7a76/#8f8a82 | #ffffff/#1c1a18 | **4.27** | **5.06** | 4.5:1 | gündüz KALDI · gece geçti |
| `--tx2@0.58` — .bayat-2 (opacity .58) sayfa zemininde | #9e9c9a/#726d67 | #ffffff/#1c1a18 | **2.74** | **3.39** | 4.5:1 | KALDI |
| `--tx2@0.42` — .bayat-3 (opacity .42) sayfa zemininde | #b9b7b6/#5a5651 | #ffffff/#1c1a18 | **2.00** | **2.38** | 4.5:1 | KALDI |
| `--tx2@0.42` — .bayat-3 (opacity .42) kart üstünde | #b5b1ae/#605b56 | #f8f5f2/#262320 | **1.96** | **2.33** | 4.5:1 | KALDI |

### C · vurgu mürekkebi
| çift | L1 (mürekkep) | L2 (zemin) | gündüz | gece | eşik | hüküm |
|---|---|---|---|---|---|---|
| `--accent-2` — .slabel · .t-vi · .lv.on · code · .dlbtn:hover | #050505/#e8e4df | #f3f3f3/#302c28 | **18.37** | **10.94** | 4.5:1 | geçti |
| `--accent-2` — .card .t · .sitem.on .sub · .regrow.live .nm | #050505/#e8e4df | #f8f5f2/#262320 | **18.76** | **12.35** | 4.5:1 | geçti |
| `--accent-2` — .pd-l · .mono .k · .pane içi anahtar | #050505/#e8e4df | #fbfaf8/#232120 | **19.54** | **12.67** | 4.5:1 | geçti |
| `--accent-2` — .spine.calm hover · sayfa zemininde bağ | #050505/#e8e4df | #ffffff/#1c1a18 | **20.38** | **13.71** | 4.5:1 | geçti |
| `--accent-2` — .spine.attn .items button:hover | #050505/#e8e4df | #f0ede6/#30281a | **17.43** | **11.49** | 4.5:1 | geçti |
| `--accent-2` — .spine.act .items button:hover | #050505/#e8e4df | #f7e9ea/#322524 | **17.27** | **11.64** | 4.5:1 | geçti |
| `--accent` — .gloss summary · .kbd-panel h3.t · .hstat .l | #050505/#d4d0cb | #f8f5f2/#262320 | **18.76** | **10.18** | 4.5:1 | geçti |
| `--accent` — .spine .items button:hover::after | #050505/#d4d0cb | #ffffff/#1c1a18 | **20.38** | **11.31** | 4.5:1 | geçti |

### D · para renkleri (metin)
| çift | L1 (mürekkep) | L2 (zemin) | gündüz | gece | eşik | hüküm |
|---|---|---|---|---|---|---|
| `--green` — çip: kendi tinti sayfa zemininde | #0c6a3b/#4cc38a | #e7f0eb/#212b23 | **5.75** | **6.61** | 4.5:1 | geçti |
| `--green` — çip: kendi tinti çekmece/pano zemininde (.pd-warn · .mono) | #0c6a3b/#4cc38a | #e3ece5/#27312b | **5.54** | **6.08** | 4.5:1 | geçti |
| `--green` — çip: kendi tinti kart üstünde (.t-go/.t-rv/.t-no · .ck.*) | #0c6a3b/#4cc38a | #e0e7e0/#2a332b | **5.31** | **5.90** | 4.5:1 | geçti |
| `--green` — çip: kendi tinti gömülü panelde — EN KÖTÜ GERÇEK ZEMİN | #0c6a3b/#4cc38a | #dadfd7/#323a31 | **4.94** | **5.31** | 4.5:1 | geçti |
| `--green` — çıplak: .pos/.neg/.warn sayfa zemininde | #0c6a3b/#4cc38a | #ffffff/#1c1a18 | **6.69** | **7.83** | 4.5:1 | geçti |
| `--green` — çıplak: .mono .ok/.w/.no · .ksgroup düğme hover | #0c6a3b/#4cc38a | #fbfaf8/#232120 | **6.41** | **7.24** | 4.5:1 | geçti |
| `--green` — çıplak: .hudchip.explore · .gate-msg · .sh-sap · palet rozeti | #0c6a3b/#4cc38a | #f8f5f2/#262320 | **6.16** | **7.06** | 4.5:1 | geçti |
| `--green` — çıplak: hover satırında para rengi | #0c6a3b/#4cc38a | #f1ece8/#2f2b27 | **5.70** | **6.34** | 4.5:1 | geçti |
| `--amber` — çip: kendi tinti sayfa zemininde | #6e4a00/#e0a82e | #f0ede6/#30281a | **6.80** | **6.79** | 4.5:1 | geçti |
| `--amber` — çip: kendi tinti çekmece/pano zemininde (.pd-warn · .mono) | #6e4a00/#e0a82e | #ede8df/#362e21 | **6.51** | **6.25** | 4.5:1 | geçti |
| `--amber` — çip: kendi tinti kart üstünde (.t-go/.t-rv/.t-no · .ck.*) | #6e4a00/#e0a82e | #eae4da/#393021 | **6.29** | **6.06** | 4.5:1 | geçti |
| `--amber` — çip: kendi tinti gömülü panelde — EN KÖTÜ GERÇEK ZEMİN | #6e4a00/#e0a82e | #e4dcd1/#413828 | **5.85** | **5.39** | 4.5:1 | geçti |
| `--amber` — çıplak: .pos/.neg/.warn sayfa zemininde | #6e4a00/#e0a82e | #ffffff/#1c1a18 | **7.95** | **8.11** | 4.5:1 | geçti |
| `--amber` — çıplak: .mono .ok/.w/.no · .ksgroup düğme hover | #6e4a00/#e0a82e | #fbfaf8/#232120 | **7.62** | **7.49** | 4.5:1 | geçti |
| `--amber` — çıplak: .hudchip.explore · .gate-msg · .sh-sap · palet rozeti | #6e4a00/#e0a82e | #f8f5f2/#262320 | **7.32** | **7.30** | 4.5:1 | geçti |
| `--amber` — çıplak: hover satırında para rengi | #6e4a00/#e0a82e | #f1ece8/#2f2b27 | **6.78** | **6.56** | 4.5:1 | geçti |
| `--red` — çip: kendi tinti sayfa zemininde | #b3242c/#f58b8f | #f7e9ea/#322524 | **5.55** | **6.29** | 4.5:1 | geçti |
| `--red` — çip: kendi tinti çekmece/pano zemininde (.pd-warn · .mono) | #b3242c/#f58b8f | #f4e5e4/#382c2b | **5.36** | **5.74** | 4.5:1 | geçti |
| `--red` — çip: kendi tinti kart üstünde (.t-go/.t-rv/.t-no · .ck.*) | #b3242c/#f58b8f | #f1e0de/#3b2d2b | **5.13** | **5.62** | 4.5:1 | geçti |
| `--red` — çip: kendi tinti gömülü panelde — EN KÖTÜ GERÇEK ZEMİN | #b3242c/#f58b8f | #ebd8d5/#433531 | **4.78** | **5.01** | 4.5:1 | geçti |
| `--red` — çıplak: .pos/.neg/.warn sayfa zemininde | #b3242c/#f58b8f | #ffffff/#1c1a18 | **6.55** | **7.41** | 4.5:1 | geçti |
| `--red` — çıplak: .mono .ok/.w/.no · .ksgroup düğme hover | #b3242c/#f58b8f | #fbfaf8/#232120 | **6.28** | **6.85** | 4.5:1 | geçti |
| `--red` — çıplak: .hudchip.explore · .gate-msg · .sh-sap · palet rozeti | #b3242c/#f58b8f | #f8f5f2/#262320 | **6.03** | **6.68** | 4.5:1 | geçti |
| `--red` — çıplak: hover satırında para rengi | #b3242c/#f58b8f | #f1ece8/#2f2b27 | **5.59** | **6.00** | 4.5:1 | geçti |
| `--green` — .pm-cell.pos .pm-yield (hücre kendi tintinde) | #0c6a3b/#4cc38a | #ecf3ef/#202821 | **5.93** | **6.84** | 4.5:1 | geçti |
| `--red` — .pm-cell.neg .pm-yield (hücre kendi tintinde) | #b3242c/#f58b8f | #faf0f0/#2b2220 | **5.86** | **6.63** | 4.5:1 | geçti |
| `--amber` — .pm-thin ekim-az kazığı (kehribar tint + pozitif hücre) | #6e4a00/#e0a82e | #dfe2d7/#333522 | **6.05** | **5.86** | 4.5:1 | geçti |
| `--amber` — .pm-thin ekim-az kazığı (kehribar tint + negatif hücre) | #6e4a00/#e0a82e | #ecdfd8/#3d2f21 | **6.10** | **6.03** | 4.5:1 | geçti |
| `--red` — HALT/KRİZ etiketi üst barda (bar sayfa üstünde) | #b3242c/#f58b8f | #ffffff/#1c1a18 | **6.55** | **7.41** | 4.5:1 | geçti |
| `--red` — HALT/KRİZ etiketi üst barda (bar kart üstünde kayarken) | #b3242c/#f58b8f | #fcfcfb/#1f1d1b | **6.38** | **7.18** | 4.5:1 | geçti |
| `--red` — .kscover:hover (kırmızı tint üst barda) | #b3242c/#f58b8f | #f7e9ea/#322524 | **5.55** | **6.29** | 4.5:1 | geçti |

### E · dolgu üstü metin
| çift | L1 (mürekkep) | L2 (zemin) | gündüz | gece | eşik | hüküm |
|---|---|---|---|---|---|---|
| `--bg2` — .gate-btn · .pillc · .dlbtn.primary · birincil eylem | #fbfaf8/#232120 | #050505/#d4d0cb | **19.54** | **10.45** | 4.5:1 | geçti |
| `--bg2` — .dlbtn.primary:hover · .skip (içeriğe atla) | #fbfaf8/#232120 | #050505/#e8e4df | **19.54** | **12.67** | 4.5:1 | geçti |
| `--bg2` — .halt:hover · .kscover[aria-expanded=true] | #fbfaf8/#232120 | #b3242c/#f58b8f | **6.28** | **6.85** | 4.5:1 | geçti |

### F · metin-dışı: kenar
| çift | L1 (mürekkep) | L2 (zemin) | gündüz | gece | eşik | hüküm |
|---|---|---|---|---|---|---|
| `--line` — varsayılan saç teli · bg | #e7e3df/#38342f | #ffffff/#1c1a18 | **1.28** | **1.40** | 3.0:1 | KALDI |
| `--line` — varsayılan saç teli · bg2 | #e7e3df/#38342f | #fbfaf8/#232120 | **1.22** | **1.30** | 3.0:1 | KALDI |
| `--line` — varsayılan saç teli · card | #e7e3df/#38342f | #f8f5f2/#262320 | **1.18** | **1.27** | 3.0:1 | KALDI |
| `--line` — varsayılan saç teli · card-2 | #e7e3df/#38342f | #f1ece8/#2f2b27 | **1.09** | **1.14** | 3.0:1 | KALDI |
| `--line-2` — güçlü saç teli · bg | #d9d4cf/#4a453f | #ffffff/#1c1a18 | **1.47** | **1.83** | 3.0:1 | KALDI |
| `--line-2` — güçlü saç teli · bg2 | #d9d4cf/#4a453f | #fbfaf8/#232120 | **1.41** | **1.69** | 3.0:1 | KALDI |
| `--line-2` — güçlü saç teli · card | #d9d4cf/#4a453f | #f8f5f2/#262320 | **1.36** | **1.65** | 3.0:1 | KALDI |
| `--line-2` — güçlü saç teli · card-2 | #d9d4cf/#4a453f | #f1ece8/#2f2b27 | **1.25** | **1.48** | 3.0:1 | KALDI |
| `--field` — form kontrolü kenarı (metin girişi/select) · bg | #8a8580/#7e776e | #ffffff/#1c1a18 | **3.65** | **3.93** | 3.0:1 | geçti |
| `--field` — form kontrolü kenarı (metin girişi/select) · bg2 | #8a8580/#7e776e | #fbfaf8/#232120 | **3.50** | **3.63** | 3.0:1 | geçti |
| `--field` — form kontrolü kenarı (metin girişi/select) · card | #8a8580/#7e776e | #f8f5f2/#262320 | **3.36** | **3.54** | 3.0:1 | geçti |
| `--field` — form kontrolü kenarı (metin girişi/select) · card-2 | #8a8580/#7e776e | #f1ece8/#2f2b27 | **3.12** | **3.18** | 3.0:1 | geçti |
| `--green-h` — .t-go/.pillc.g/.ck.ok çip iç kenarı kendi dolgusunda | #96bba6/#36654c | #e0e7e0/#2a332b | **1.68** | **1.94** | 3.0:1 | KALDI |
| `--amber-h` — .t-rv/.ck.man çip iç kenarı kendi dolgusunda | #bfae8e/#735a26 | #eae4da/#393021 | **1.72** | **1.99** | 3.0:1 | KALDI |
| `--red-h` — .t-no/.s-rb çip iç kenarı kendi dolgusunda | #db9ea0/#7c4e4e | #f1e0de/#3b2d2b | **1.75** | **1.92** | 3.0:1 | KALDI |
| `--amber-h2` — .pd-warn kenarı kendi dolgusunda | #baa986/#7a5f26 | #ede8df/#362e21 | **1.89** | **2.22** | 3.0:1 | KALDI |
| `--ink-h-soft` — .slabel kenarı (ink-h-soft) tint üstünde | #c8c8c8/#4e4a45 | #f3f3f3/#302c28 | **1.51** | **1.58** | 3.0:1 | KALDI |
| `--ink-h` — .t-vi/.lv.on kenarı (ink-h) tint üstünde | #acacac/#615d59 | #f3f3f3/#302c28 | **2.05** | **2.12** | 3.0:1 | KALDI |
| `--amber-h` — .pm-cell.thin kehribar iç kenarı (pozitif hücre) | #c0b89b/#635526 | #ecf3ef/#202821 | **1.76** | **2.06** | 3.0:1 | KALDI |
| `--line-2` — nav alt kenarı (line-2) sayfa üstünde | #d9d4cf/#4a453f | #ffffff/#1c1a18 | **1.47** | **1.83** | 3.0:1 | KALDI |

### G · durum grafikleri
| çift | L1 (mürekkep) | L2 (zemin) | gündüz | gece | eşik | hüküm |
|---|---|---|---|---|---|---|
| `--green` — .dot sağlıklı (yeşil) üst barda | #0c6a3b/#4cc38a | #ffffff/#1c1a18 | **6.69** | **7.83** | 3.0:1 | geçti |
| `--amber` — .dot.stale (kehribar) üst barda | #6e4a00/#e0a82e | #ffffff/#1c1a18 | **7.95** | **8.11** | 3.0:1 | geçti |
| `--red` — .dot.halt (kırmızı) üst barda | #b3242c/#f58b8f | #ffffff/#1c1a18 | **6.55** | **7.41** | 3.0:1 | geçti |
| `--green` — .hudchip .ld yeşil (çip zemini kart) | #0c6a3b/#4cc38a | #f8f5f2/#262320 | **6.16** | **7.06** | 3.0:1 | geçti |
| `--amber` — .hudchip .ld.warn kehribar | #6e4a00/#e0a82e | #f8f5f2/#262320 | **7.32** | **7.30** | 3.0:1 | geçti |
| `--red` — .hudchip .ld.bad kırmızı | #b3242c/#f58b8f | #f8f5f2/#262320 | **6.03** | **6.68** | 3.0:1 | geçti |
| `--tx2` — .hudchip .ld.off (tx2) | #585450/#b0a9a0 | #f8f5f2/#262320 | **6.91** | **6.72** | 3.0:1 | geçti |
| `--green` — .spine::before damga (yeşil) kart üstünde | #0c6a3b/#4cc38a | #f8f5f2/#262320 | **6.16** | **7.06** | 3.0:1 | geçti |
| `--green-stamp` — .spine.calm::before damga (green-stamp) sayfa üstünde | #79ad93/#367757 | #ffffff/#1c1a18 | **2.56** | **3.25** | 3.0:1 | gündüz KALDI · gece geçti |
| `--amber` — .spine.attn::before damga kendi bandında | #6e4a00/#e0a82e | #f0ede6/#30281a | **6.80** | **6.79** | 3.0:1 | geçti |
| `--red` — .spine.act::before damga kendi bandında | #b3242c/#f58b8f | #f7e9ea/#322524 | **5.55** | **6.29** | 3.0:1 | geçti |
| `--accent` — .sitem::before etkin görünüm işareti (3px) | #050505/#d4d0cb | #ffffff/#1c1a18 | **20.38** | **11.31** | 3.0:1 | geçti |
| `--amber@0.7` — body.explore-mode::after keşif çerçevesi (2px, opacity .7) | #9a804d/#a57d27 | #ffffff/#1c1a18 | **3.77** | **4.60** | 3.0:1 | geçti |
| `--pm-pos` — .pm-cell.pos hücre zemini ↔ nötr hücre (işaret kodlaması) | #ecf3ef/#202821 | #ffffff/#1c1a18 | **1.13** | **1.15** | 3.0:1 | KALDI |
| `--pm-neg` — .pm-cell.neg hücre zemini ↔ nötr hücre (işaret kodlaması) | #faf0f0/#2b2220 | #ffffff/#1c1a18 | **1.12** | **1.12** | 3.0:1 | KALDI |

### H · ölçüm grafikleri
| çift | L1 (mürekkep) | L2 (zemin) | gündüz | gece | eşik | hüküm |
|---|---|---|---|---|---|---|
| `--accent` — .bar dolgusu (accent) ↔ ray (bg2) | #050505/#d4d0cb | #fbfaf8/#232120 | **19.54** | **10.45** | 3.0:1 | geçti |
| `--bg2` — .bar rayı (bg2) ↔ kart zemini | #fbfaf8/#232120 | #f8f5f2/#262320 | **1.04** | **1.03** | 3.0:1 | KALDI |
| `--line` — .bar ray kenarı (line) ↔ ray | #e7e3df/#38342f | #fbfaf8/#232120 | **1.22** | **1.30** | 3.0:1 | KALDI |
| `--accent` — .thermo tüp dolgusu (accent) ↔ tüp (bg2) | #050505/#d4d0cb | #fbfaf8/#232120 | **19.54** | **10.45** | 3.0:1 | geçti |
| `--raise` — --raise ölçer rayı ↔ kart (DESIGN.md beyanlı) | #ffffff/#38342f | #f8f5f2/#262320 | **1.09** | **1.27** | 3.0:1 | KALDI |
| `--line` — .pm-conf güven rayı (line) ↔ pozitif hücre | #e7e3df/#38342f | #ecf3ef/#202821 | **1.13** | **1.23** | 3.0:1 | KALDI |
| `--green@0.85` — .pm-conf dolgusu (yeşil @.85) ↔ güven rayı | #2d7c54/#49ae7c | #e7e3df/#38342f | **3.99** | **4.49** | 3.0:1 | geçti |
| `--red@0.85` — .pm-conf dolgusu (kırmızı @.85) ↔ güven rayı | #bb4147/#d97e81 | #e7e3df/#38342f | **4.15** | **4.26** | 3.0:1 | geçti |
| `--accent` — equity çizgisi (accent) ↔ kart zemini | #050505/#d4d0cb | #f8f5f2/#262320 | **18.76** | **10.18** | 3.0:1 | geçti |
| `--tx2` — sparkline/eksen (tx2) ↔ kart zemini | #585450/#b0a9a0 | #f8f5f2/#262320 | **6.91** | **6.72** | 3.0:1 | geçti |
| `--line-2` — grafik ızgarası (line-2) ↔ kart zemini | #d9d4cf/#4a453f | #f8f5f2/#262320 | **1.36** | **1.65** | 3.0:1 | KALDI |
| `--card-2` — bullet nitel bant 1 (card-2) ↔ kart zemini | #f1ece8/#2f2b27 | #f8f5f2/#262320 | **1.08** | **1.11** | 3.0:1 | KALDI |
| `--accent` — bullet ölçüm çubuğu (accent) ↔ en açık bant (card-2) | #050505/#d4d0cb | #f1ece8/#2f2b27 | **17.38** | **9.15** | 3.0:1 | geçti |
| `--accent` — bullet ölçüm çubuğu (accent) ↔ en koyu bant (tx2/tx3) | #050505/#d4d0cb | #585450/#b0a9a0 | **2.72** | **1.52** | 3.0:1 | KALDI |
| `--card-2` — yoğunluk merdiveni: bant1 (card-2) ↔ bant2 (line) | #f1ece8/#2f2b27 | #e7e3df/#38342f | **1.09** | **1.14** | 3.0:1 | KALDI |
| `--line` — yoğunluk merdiveni: bant2 (line) ↔ bant3 (line-2) | #e7e3df/#38342f | #d9d4cf/#4a453f | **1.15** | **1.30** | 3.0:1 | KALDI |
| `--line-2` — yoğunluk merdiveni: bant3 (line-2) ↔ bant4 (tx3) | #d9d4cf/#4a453f | #585450/#b0a9a0 | **5.10** | **4.08** | 3.0:1 | geçti |
| `--tx3` — yoğunluk merdiveni: bant4 (tx3) ↔ bant5 (tx2) — AYNI RENK | #585450/#b0a9a0 | #585450/#b0a9a0 | **1.00** | **1.00** | 3.0:1 | KALDI |
| `--accent` — IC trendi: `gerçek` (accent) ↔ `sim` (violet) — AYNI RENK | #050505/#d4d0cb | #050505/#d4d0cb | **1.00** | **1.00** | 3.0:1 | KALDI |
| `--accent` — IC trendi: `gerçek` (accent) ↔ `havuz` (tx3) | #050505/#d4d0cb | #585450/#b0a9a0 | **2.72** | **1.52** | 3.0:1 | KALDI |
| `--violet` — IC trendi: `sim` (violet) ↔ `havuz` (tx3) | #050505/#d4d0cb | #585450/#b0a9a0 | **2.72** | **1.52** | 3.0:1 | KALDI |
| `--line` — IC trendi: sıfır ekseni (line) ↔ kart zemini | #e7e3df/#38342f | #f8f5f2/#262320 | **1.18** | **1.27** | 3.0:1 | KALDI |

### I · odak halkası
| çift | L1 (mürekkep) | L2 (zemin) | gündüz | gece | eşik | hüküm |
|---|---|---|---|---|---|---|
| `--accent` — :focus-visible 2px --accent · sayfa zemininde | #050505/#d4d0cb | #ffffff/#1c1a18 | **20.38** | **11.31** | 3.0:1 | geçti |
| `--accent` — :focus-visible 2px --accent · kart üstünde | #050505/#d4d0cb | #f8f5f2/#262320 | **18.76** | **10.18** | 3.0:1 | geçti |
| `--accent` — :focus-visible 2px --accent · gömülü panelde | #050505/#d4d0cb | #f1ece8/#2f2b27 | **17.38** | **9.15** | 3.0:1 | geçti |
| `--accent` — :focus-visible 2px --accent · seçili satırda | #050505/#d4d0cb | #f3f3f3/#302c28 | **18.37** | **9.02** | 3.0:1 | geçti |
| `--accent` — :focus-visible 2px --accent · kırmızı çip üstünde | #050505/#d4d0cb | #f1e0de/#3b2d2b | **15.97** | **8.57** | 3.0:1 | geçti |
| `--card` — modal kart ↔ perdeyle karartılmış sayfa (.kbd-panel ↔ .kbd-ov) | #f8f5f2/#262320 | #969696/#100f0d | **2.72** | **1.23** | 3.0:1 | KALDI |
| `--card` — modal kart ↔ perdeyle karartılmış KART zemini | #f8f5f2/#262320 | #92908e/#141210 | **2.93** | **1.20** | 3.0:1 | KALDI |

Bölüm başlıkları: **A** gövde mürekkebi · **B** ikincil mürekkep · **C** vurgu mürekkebi ·
**D** para renkleri · **E** dolgu üstü ters mürekkep · **F** metin-dışı kenarlar ·
**G** durum grafikleri · **H** ölçüm grafikleri · **I** odak halkası ve perde.

## 4 · Kalanların tam listesi (42)
- B · ikincil mürekkep · .sitem .sub (opacity .7) rayda  → gündüz 3.57 · gece 4.32 (eşik 4.5)
- B · ikincil mürekkep · .pm-none (opacity .7) ekilmemiş hücrede  → gündüz 3.47 · gece 4.11 (eşik 4.5)
- B · ikincil mürekkep · .sessizhat .sh-sep (opacity .45)  → gündüz 2.11 · gece 2.54 (eşik 3.0)
- B · ikincil mürekkep · .bayat-1 (opacity .78) sayfa zemininde  → gündüz 4.27 · gece 5.06 (eşik 4.5)
- B · ikincil mürekkep · .bayat-2 (opacity .58) sayfa zemininde  → gündüz 2.74 · gece 3.39 (eşik 4.5)
- B · ikincil mürekkep · .bayat-3 (opacity .42) sayfa zemininde  → gündüz 2.00 · gece 2.38 (eşik 4.5)
- B · ikincil mürekkep · .bayat-3 (opacity .42) kart üstünde  → gündüz 1.96 · gece 2.33 (eşik 4.5)
- F · metin-dışı: kenar · varsayılan saç teli · bg  → gündüz 1.28 · gece 1.40 (eşik 3.0)
- F · metin-dışı: kenar · varsayılan saç teli · bg2  → gündüz 1.22 · gece 1.30 (eşik 3.0)
- F · metin-dışı: kenar · varsayılan saç teli · card  → gündüz 1.18 · gece 1.27 (eşik 3.0)
- F · metin-dışı: kenar · varsayılan saç teli · card-2  → gündüz 1.09 · gece 1.14 (eşik 3.0)
- F · metin-dışı: kenar · güçlü saç teli · bg  → gündüz 1.47 · gece 1.83 (eşik 3.0)
- F · metin-dışı: kenar · güçlü saç teli · bg2  → gündüz 1.41 · gece 1.69 (eşik 3.0)
- F · metin-dışı: kenar · güçlü saç teli · card  → gündüz 1.36 · gece 1.65 (eşik 3.0)
- F · metin-dışı: kenar · güçlü saç teli · card-2  → gündüz 1.25 · gece 1.48 (eşik 3.0)
- F · metin-dışı: kenar · .t-go/.pillc.g/.ck.ok çip iç kenarı kendi dolgusunda  → gündüz 1.68 · gece 1.94 (eşik 3.0)
- F · metin-dışı: kenar · .t-rv/.ck.man çip iç kenarı kendi dolgusunda  → gündüz 1.72 · gece 1.99 (eşik 3.0)
- F · metin-dışı: kenar · .t-no/.s-rb çip iç kenarı kendi dolgusunda  → gündüz 1.75 · gece 1.92 (eşik 3.0)
- F · metin-dışı: kenar · .pd-warn kenarı kendi dolgusunda  → gündüz 1.89 · gece 2.22 (eşik 3.0)
- F · metin-dışı: kenar · .slabel kenarı (ink-h-soft) tint üstünde  → gündüz 1.51 · gece 1.58 (eşik 3.0)
- F · metin-dışı: kenar · .t-vi/.lv.on kenarı (ink-h) tint üstünde  → gündüz 2.05 · gece 2.12 (eşik 3.0)
- F · metin-dışı: kenar · .pm-cell.thin kehribar iç kenarı (pozitif hücre)  → gündüz 1.76 · gece 2.06 (eşik 3.0)
- F · metin-dışı: kenar · nav alt kenarı (line-2) sayfa üstünde  → gündüz 1.47 · gece 1.83 (eşik 3.0)
- G · durum grafikleri · .spine.calm::before damga (green-stamp) sayfa üstünde  → gündüz 2.56 · gece 3.25 (eşik 3.0)
- G · durum grafikleri · .pm-cell.pos hücre zemini ↔ nötr hücre (işaret kodlaması)  → gündüz 1.13 · gece 1.15 (eşik 3.0)
- G · durum grafikleri · .pm-cell.neg hücre zemini ↔ nötr hücre (işaret kodlaması)  → gündüz 1.12 · gece 1.12 (eşik 3.0)
- H · ölçüm grafikleri · .bar rayı (bg2) ↔ kart zemini  → gündüz 1.04 · gece 1.03 (eşik 3.0)
- H · ölçüm grafikleri · .bar ray kenarı (line) ↔ ray  → gündüz 1.22 · gece 1.30 (eşik 3.0)
- H · ölçüm grafikleri · --raise ölçer rayı ↔ kart (DESIGN.md beyanlı)  → gündüz 1.09 · gece 1.27 (eşik 3.0)
- H · ölçüm grafikleri · .pm-conf güven rayı (line) ↔ pozitif hücre  → gündüz 1.13 · gece 1.23 (eşik 3.0)
- H · ölçüm grafikleri · grafik ızgarası (line-2) ↔ kart zemini  → gündüz 1.36 · gece 1.65 (eşik 3.0)
- H · ölçüm grafikleri · bullet nitel bant 1 (card-2) ↔ kart zemini  → gündüz 1.08 · gece 1.11 (eşik 3.0)
- H · ölçüm grafikleri · bullet ölçüm çubuğu (accent) ↔ en koyu bant (tx2/tx3)  → gündüz 2.72 · gece 1.52 (eşik 3.0)
- H · ölçüm grafikleri · yoğunluk merdiveni: bant1 (card-2) ↔ bant2 (line)  → gündüz 1.09 · gece 1.14 (eşik 3.0)
- H · ölçüm grafikleri · yoğunluk merdiveni: bant2 (line) ↔ bant3 (line-2)  → gündüz 1.15 · gece 1.30 (eşik 3.0)
- H · ölçüm grafikleri · yoğunluk merdiveni: bant4 (tx3) ↔ bant5 (tx2) — AYNI RENK  → gündüz 1.00 · gece 1.00 (eşik 3.0)
- H · ölçüm grafikleri · IC trendi: `gerçek` (accent) ↔ `sim` (violet) — AYNI RENK  → gündüz 1.00 · gece 1.00 (eşik 3.0)
- H · ölçüm grafikleri · IC trendi: `gerçek` (accent) ↔ `havuz` (tx3)  → gündüz 2.72 · gece 1.52 (eşik 3.0)
- H · ölçüm grafikleri · IC trendi: `sim` (violet) ↔ `havuz` (tx3)  → gündüz 2.72 · gece 1.52 (eşik 3.0)
- H · ölçüm grafikleri · IC trendi: sıfır ekseni (line) ↔ kart zemini  → gündüz 1.18 · gece 1.27 (eşik 3.0)
- I · odak halkası · modal kart ↔ perdeyle karartılmış sayfa (.kbd-panel ↔ .kbd-ov)  → gündüz 2.72 · gece 1.23 (eşik 3.0)
- I · odak halkası · modal kart ↔ perdeyle karartılmış KART zemini  → gündüz 2.93 · gece 1.20 (eşik 3.0)

Her satır §6 (bilinçli istisna) ya da §5 (beyansız bulgu) altında karşılığını bulur;
hiçbiri sınıflandırılmadan bırakılmadı.

## 5 · Beyansız bulgular (bu turun asıl çıktısı)

Aşağıdaki altı kalem, DESIGN.md'nin beyanlı sapma listesinde **yok** ve bugüne kadar
ölçülmemişti.

### B1 · Yoğunluk merdiveninin son iki basamağı AYNI RENK

`app.js`'in bullet grafiğindeki nitel aralık merdiveni beş basamak olarak yazılmış:
`--card-2 → --line → --line-2 → --tx3 → --tx2`. Ama `--tx3`, iki temada da `--tx2`'nin
bire-bir kopyasıdır (`#585450` / `#b0a9a0`), yani **4. ve 5. bant arasındaki oran 1.00**.
Üstelik ilk üç basamak da birbirinden ayrılmıyor (1.09 ve 1.15 gündüz). Fiilen ayırt
edilebilen tek geçiş `--line-2 → --tx3` (5.10 gündüz / 4.08 gece). **Beş bantlı bir
skala olarak tarif edilen şey, ekranda iki tonlu bir skaladır.** Few'nun nitel aralık
fikri (kötü/kabul/iyi) burada okunmuyor.

### B2 · Bullet ölçüm çubuğu gece en koyu bandın üstünde kayboluyor

Ölçüm çubuğu `--accent`; gece `--accent` = `#d4d0cb` ve en koyu nitel bant `--tx2` =
`#b0a9a0`. Oran **1.52** (gündüz 2.72 — o da eşiğin altında). Bileşenin tek üstünlüğü
"ölçüm ile hedef bandını tek satırda karşılaştırmak" olduğuna göre, ölçümün bandın
üstünde okunamaması bileşeni işlevsiz bırakır. Bu bir estetik sapma değil, bir **okuma
arızası**.

### B3 · Bayatlık solmasının 2. ve 3. kademesi metin eşiğinin altında

`.bayat-1/-2/-3` sırasıyla `opacity: .78 / .58 / .42`. Sayfa zemininde ölçüldü:
**4.27 / 2.74 / 2.00** (gündüz), **5.06 / 3.39 / 2.38** (gece). Kural kaynakta
"sayının KENDİSİ hiçbir kademede değişmez ve gizlenmez" diyor — ama 3. kademede sayı
2.00:1'de duruyor, yani fiilen gizleniyor. Bayatlık **niceliği** taşımayan bir sinyal
olarak tasarlandığına göre, sinyali okunamazlığa kadar götürmesi gerekmiyor.

### B4 · `.sitem .sub` ve `.pm-none` — `opacity:.7` AA'yı gündüzde deviriyor

Kenar rayındaki canlı alt-okuma (`3.57`) ve matrisin "hiç ekilmemiş" hücre metni
(`3.47`) gündüz temasında AA altında. İkisi de `--tx2` üzerine `opacity:.7`. Gece
temasında sınırın hemen altında (4.32 / 4.11) — yani sorun tek temaya özgü değil.

### B5 · Matris hücre tinti tek başına işaret taşımıyor

`.pm-cell.pos` / `.neg` zeminleri nötr hücreye karşı **1.13** ve **1.12**. Bu bir
**arıza değil**, ama raporun bunu söylemesi gerekiyor: kâr/zarar işareti hücre
zemininden okunamaz. Second-Channel Rule zaten işareti (`+`/`−`) ve rakam rengini
(5.93 / 5.86) zorunlu kılıyor, yani bilgi kaybolmuyor. Kayıt için: **hücre tinti
dekoratiftir, kodlama değildir** — ve o hâlde bir gün "tint yeter" diye kısaltılamaz.

### B6 · IC-trend grafiğinin iki serisi AYNI RENK, ve efsane bunu söylemiyor

`app.js` IC trend çizgisini üç seriyle çiziyor: `gerçek` = `--accent`, `sim` = `--violet`,
`havuz` = `--tx3`. Ama **`--violet` iki temada da `--accent`'in bire-bir kopyasıdır**
(`#050505` / `#d4d0cb`) — iki seri arasındaki oran **1.00**. Çizimde ayrım
`stroke-dasharray` ile yapılıyor (`gerçek` düz, `sim` `1 3`, `havuz` `2 2`) ve bu, iş
emrinin "grafikler renk olmadan da okunmalı" kuralının doğru uygulamasıdır. **Arıza
efsanededir:** efsane satırı üç adı üç RENKLE etiketliyor (`color:var(--accent)` /
`var(--violet)` / `var(--tx3)`) ve kesik-çizgi desenini hiç göstermiyor. Yani okuyucu
`gerçek` ile `sim`i efsanede ayıramaz, ve grafikte ayırdığı şeyi hangi ada bağlayacağını
bilemez. Üstelik `havuz` ↔ `gerçek` oranı da eşiğin altında (**2.72** gündüz / **1.52**
gece), yani gece temasında üç serinin hiçbiri birbirinden luminansla ayrılmıyor.

## 6 · Bilinçli istisnalar

Aşağıdakiler 3:1'i geçmiyor ve **bu turda da geçmeyecek**. Hepsi DESIGN.md'de
gerekçeli bir hüküm olarak duruyor; burada ölçülmüş rakamlarıyla tekrarlanıyorlar ki
"denetim bunu görmedi" denemesin.

| # | İstisna | Ölçüm (gündüz / gece) | Gerekçe |
|---|---|---|---|
| İ1 | `--line` ve `--line-2` saç telleri (8 çift) | 1.09–1.47 / 1.14–1.83 | 1.4.11 "bileşeni tanıtan bilgi" ister; kart ve çip **dolgusuyla** tanınır, kenarıyla değil. Her kuralı bağırtmak, rampanın ürettiği sükûneti yok eder (DESIGN.md § Non-text contrast). |
| İ2 | Çip iç saç telleri `--green-h/--amber-h/--red-h/--amber-h2` | 1.68–1.89 / 1.92–2.22 | Aynı gerekçe; çipi tanıtan şey dolgusu ve metnidir. **Rakamlar bu turda düzeltildi — bkz. §8.** |
| İ3 | `--ink-h` / `--ink-h-soft` nötr çip kenarları | 2.05 / 1.51 · 2.12 / 1.58 | Aynı aile. `--ink-h-soft` (%18) sınıfın en zayıfı. |
| İ4 | Ton merdiveni basamakları (`bg→bg2→card→card-2`, ray/kart) | 1.03–1.09 | Ton basamağı bir **kontrast aygıtı değil, düzlem aygıtıdır**; kenarı saç teli kapatır (DESIGN.md, 1.043/1.041/1.080). |
| İ5 | Gece modal perdesi | — / 1.23 (tavan 1.34) | Mekanizmanın **yeri yok**: gece zemini zaten koyu, saf siyah perde bile 1.34 verir. Ayrım `backdrop-blur` + modalın kendi saç teliyle kurulur. Bu **beyan**, bir çözüm değil. |
| İ6 | `.spine.calm::before` sakin damgası | 2.56 / 3.25 | Sağlıklı durum **bilerek sönüktür** (iş emri Ç2, karanlık kokpit). Damganın yanında aynı şeyi söyleyen tam bir cümle var; damga tek taşıyıcı değil. |
| İ7 | `.sessizhat .sh-sep` ayırıcı (`opacity:.45`) | 2.11 / 2.54 | Ayırıcı **noktalama**dır, bilgi değil; kaldırılsa cümle aynı okunur. |

## 7 · Değişiklik önerileri

**ÖNERİ — UYGULANMADI.** Aşağıdakilerin hiçbiri bu turda uygulanmadı ve hiçbiri
tek başına uygulanamaz: her biri bir jeton ya da bir kural değeri değiştirir, ve
WP0 kararına göre jeton yeniden-değerlemesi (gündüz beyazı dahil) kendi onay turunu
ve kendi ölçümünü hak ediyor. Sıralama, **operatöre maliyeti** değil, **operatörün
kaybettiği bilgiyi** ölçer.

| # | Kalan | Öneri | Neden bu | Bedeli |
|---|---|---|---|---|
| Ö1 | B1 — merdivenin 4./5. basamağı aynı renk | Merdiveni **dört** basamağa indir (`--card-2 → --line-2 → --tx3` + ölçüm çubuğu) ya da `--tx3`'ü gerçek bir ara tona ayır. | Beş bant iddiası ölçülemiyor; olmayan bir basamağı listede tutmak "yapılmış iş" izlenimi verir. | `--tx3` 7 yerde kullanılıyor; ayrıştırmak yeni bir renk jetonu demek. |
| Ö2 | B2 — bullet çubuğu gece kayboluyor | Ölçüm çubuğunu `--accent` yerine **zemin polaritesine göre** seç (gece: `--bg`/`--card` tonunda ters çubuk) ya da çubuğa 1px `--bg` kontur ver. | Bileşenin tek işi karşılaştırma; okunmayan çubuk bileşeni işlevsiz bırakır. | `_bullet` çiziminde tek satır; jeton değişikliği gerekmez → **en ucuz kalem, ilk sırada değerlendirilmeli.** |
| Ö3 | B3 — `.bayat-2/-3` | Opaklık kademelerini `.78/.58/.42` yerine `.85/.72/.60` yap (gündüzde ≈4.9/4.0/3.3) **ya da** solmayı metinden alıp satırın **sol kenar çizgisine** taşı. | Sayının kendisi hiçbir kademede gizlenmemeli — kuralın kendi yazdığı şey bu. | Üç sınıf tek satır; eşikler `app.js bayatSinif`'ta, dokunulmaz. |
| Ö4 | B4 — `opacity:.7` iki yerde | Opaklığı kaldır, sönüklüğü zaten var olan `--tx2` taşısın. | Aynı sönüklüğü iki mekanizmayla (jeton + opaklık) üretmek, ikisini de ölçülemez yapar. | İki kural; görsel fark küçük. |
| Ö8 | B6 — IC-trend efsanesi | Efsanede rengi bırak, **çizgi örneğini** göster (3 küçük SVG: düz / `1 3` / `2 2`). `--violet`'i `--accent`'e eşit tutmak sorun değil — sorun onu bir AYIRT EDİCİ gibi kullanmak. | Renk ile ayrılmayan bir şeyi renkle etiketlemek, efsaneyi süse çevirir. | Efsane satırı `app.js`'te; jeton değişikliği gerekmez. |
| Ö5 | İ3 — `--ink-h-soft` %18 | `.slabel` kenarını kaldır ve çipi yalnız `--accent-tint` dolgusuyla tanıt. | %18'lik bir kenar zaten görülmüyor; **çizmemek**, görünmeyeni çizmekten dürüst. | Tek kural. |
| Ö6 | İ5 — gece perdesi | Değişiklik önerilmiyor. Onun yerine **beyanı arayüze taşı**: modal açıkken arkadaki içerik `inert` (zaten öyle) ve bu davranış belgeye bağlansın. | Luminans mekanizmasının gece **yeri yok**; sayıyı büyütmek sahte bir çözüm olur. | — |
| Ö7 | İ1/İ2/İ4 saç telleri ve ton basamakları | Değişiklik önerilmiyor. | Sistemin kimliği bu. Üstelik `--field` çıpası, 1.4.11'in gerçekten bağladığı tek yeri (form kenarı) **zaten** 3.12–3.93 ile kapatıyor. | — |

**Gündüz beyazı hakkında (WP0 borç #5).** Bu denetim, `--bg:#ffffff` / `--raise:#ffffff`
sorununun bir **kontrast** sorunu olmadığını doğruluyor: gündüz temasında AA'yı deviren
altı çiftin hiçbiri saf beyazdan gelmiyor, hepsi opaklıktan geliyor. Saf beyazın davası
parlama ve yüzey merdiveninin sığlığıdır (`bg→bg2` 1.043) — ikisi de bu raporun ölçtüğü
şey değil. **Kontrast verisi, gündüz beyazını değiştirmek için bir gerekçe üretmiyor.**

## 8 · Yeniden üretilemeyen rakamlar (kaynak düzeltmeleri)

DESIGN.md § Measurement provenance'ın kurduğu gelenek: aynı yöntemle yeniden üretilemeyen
her rakam düzeltilerek kaydedilir. Bu turda iki tanesi çıktı.

**D1 — Çip iç saç telleri (DESIGN.md § Non-text contrast).** Belge "1.50 / 1.53 / 1.54
(gündüz) · 1.69 / 1.74 / 1.66 (gece)" diyor. Bu üçlüler **yeniden üretildi ve yöntemi
bulundu**: saç teli, çipin **kart zeminine** bileşiklenmiş; oysa `box-shadow: inset`
öğenin **kendi arka planının** — yani %10 tintin — üstüne boyar. Doğru zeminle ölçüm
**1.68 / 1.72 / 1.75** (gündüz) ve **1.94 / 1.99 / 1.92** (gece). Hüküm değişmiyor
(üçü de 3:1'in çok altında, beyanlı sapma), **rakam değişiyor**.

**D2 — Gündüz perdesi (`index.html`, gece bloğu yorumu).** Kaynak "gündüz siyah %42
perde sayfayı karta karşı **2.79** ayırıyor" diyor. Yeniden üretilemedi: ölçüm **2.72**
(`#969696` ↔ `#f8f5f2`) — ki bu DESIGN.md'nin verdiği rakamdır. En yakın alternatif
okumalar 2.84 (`--bg2`'ye karşı) ve 2.52 (`--card-2`'ye karşı); 2.79'u veren bir zemin
DOM'da yok. Yorum bu turda düzeltildi (**yalnız yorum metni; hiçbir değer kımıldamadı**).

**Doğrulananlar.** DESIGN.md'nin metin ve para tabloları, `--field` satırı, perde
tavanı (1.34) ve tarihsel 1.27:1 arızası **birebir yeniden üretildi**. Bu raporun
motoru o tabloyla aynı sayıları veriyor — yöntem farkı yalnız D1'de.

## 9 · Çivi tablosu

Aşağıdaki satırlar `tests/test_tasarim_token_v153.py` tarafından kaynaktan yeniden
hesaplanır ve ±0.005 içinde eşleşmezse test kırmızı verir. Tablo bir özet değil, bir
**bekçi**: jeton değerlenirse rapor burada bayat ilan edilir.
Biçim: `mürekkep · zemin yığını (alttan üste, `+` ile) · tema · oran · eşik`.

<!-- CIVI-TABLOSU-BASI -->
| mürekkep | zemin yığını | tema | oran | eşik |
|---|---|---|---|---|
| --tx | --bg | gunduz | 20.38 | 4.5 |
| --tx | --bg | gece | 11.31 | 4.5 |
| --tx | --card | gunduz | 18.76 | 4.5 |
| --tx | --card | gece | 10.18 | 4.5 |
| --tx | --card-2 + --red-t | gunduz | 14.86 | 4.5 |
| --tx | --card-2 + --red-t | gece | 7.64 | 4.5 |
| --tx2 | --bg | gunduz | 7.50 | 4.5 |
| --tx2 | --bg | gece | 7.46 | 4.5 |
| --tx2 | --card | gunduz | 6.91 | 4.5 |
| --tx2 | --card | gece | 6.72 | 4.5 |
| --tx2 | --card-2 + --red-t | gunduz | 5.47 | 4.5 |
| --tx2 | --card-2 + --red-t | gece | 5.04 | 4.5 |
| --tx2 | --card-2 + --amber-t | gunduz | 5.52 | 4.5 |
| --tx2 | --card-2 + --amber-t | gece | 4.96 | 4.5 |
| --accent-2 | --accent-tint | gunduz | 18.37 | 4.5 |
| --accent-2 | --accent-tint | gece | 10.94 | 4.5 |
| --green | --card-2 + --green-t | gunduz | 4.94 | 4.5 |
| --green | --card-2 + --green-t | gece | 5.31 | 4.5 |
| --amber | --card-2 + --amber-t | gunduz | 5.85 | 4.5 |
| --amber | --card-2 + --amber-t | gece | 5.39 | 4.5 |
| --red | --card-2 + --red-t | gunduz | 4.78 | 4.5 |
| --red | --card-2 + --red-t | gece | 5.01 | 4.5 |
| --green | --bg | gunduz | 6.69 | 4.5 |
| --green | --bg | gece | 7.83 | 4.5 |
| --amber | --bg | gunduz | 7.95 | 4.5 |
| --amber | --bg | gece | 8.11 | 4.5 |
| --red | --bg | gunduz | 6.55 | 4.5 |
| --red | --bg | gece | 7.41 | 4.5 |
| --red | --bg + --nav-bg | gunduz | 6.55 | 4.5 |
| --red | --bg + --nav-bg | gece | 7.41 | 4.5 |
| --field | --card-2 | gunduz | 3.12 | 3.0 |
| --field | --card-2 | gece | 3.18 | 3.0 |
| --field | --bg | gunduz | 3.65 | 3.0 |
| --field | --bg | gece | 3.93 | 3.0 |
| --line | --card-2 | gunduz | 1.09 | 3.0 |
| --line | --card-2 | gece | 1.14 | 3.0 |
| --line-2 | --bg | gunduz | 1.47 | 3.0 |
| --line-2 | --bg | gece | 1.83 | 3.0 |
| --accent | --card | gunduz | 18.76 | 3.0 |
| --accent | --card | gece | 10.18 | 3.0 |
| --accent | --card-2 + --red-t | gunduz | 14.86 | 3.0 |
| --accent | --card-2 + --red-t | gece | 7.64 | 3.0 |
| --green-h | --card + --green-t | gunduz | 1.68 | 3.0 |
| --green-h | --card + --green-t | gece | 1.94 | 3.0 |
| --ink-h | --accent-tint | gunduz | 2.05 | 3.0 |
| --ink-h | --accent-tint | gece | 2.12 | 3.0 |
| --green-stamp | --bg | gunduz | 2.56 | 3.0 |
| --green-stamp | --bg | gece | 3.25 | 3.0 |
| --tx3 | --tx2 | gunduz | 1.00 | 3.0 |
| --tx3 | --tx2 | gece | 1.00 | 3.0 |
| --violet | --accent | gunduz | 1.00 | 3.0 |
| --violet | --accent | gece | 1.00 | 3.0 |
| --card | --bg + --scrim | gunduz | 2.72 | 3.0 |
| --card | --bg + --scrim | gece | 1.23 | 3.0 |
<!-- CIVI-TABLOSU-SONU -->

---

## 10 · S2R-3 (cila) eki — 2026-08-02

**Kapsam sınırı:** yalnız S2R-3'ün DEĞİŞTİRDİĞİ/EKLEDİĞİ yüzeyler. 136 çiftin tamamı yeniden
üretilmedi (§3 tablosu değişmedi ve bayat değil: jeton değerlerine bu turda DOKUNULMADI —
`tokens.json` ve `:root` blokları bit-bit aynı, `test_tasarim_token_v153` bunu her koşumda
yeniden ölçüyor). B1–B6 bulgularına ve §6/§7 hükümlerine dokunulmadı; onlar ayrı bir onay turu.

### 10.1 · Bulgu: S2R-3 SIFIR yeni renk çifti getirdi

Cila turu üç yeni görsel yüzey doğurdu ve üçü de mevcut jeton çiftlerini yeniden kullanıyor:

| Yeni yüzey | Kullanılan çift | gündüz | gece | eşik | hüküm |
|---|---|---|---|---|---|
| Bekçi ÜÇÜNCÜ DURUM çipi (`t-vi` · "ÖLÇÜLEMEDİ") | `--accent-2` üstünde `--accent-tint` | **18.37** | **10.94** | 4.5 | GEÇTİ — §9 çivisinde zaten var |
| Aynı çipin kenarı | `--ink-h` üstünde `--accent-tint` | **2.05** | **2.12** | 3.0 | KALDI — **önceden kayıtlı** (§3-F, istisna İ3, öneri Ö5) |
| Ölçülemedi satırının gövdesi (`.mut`) | `--tx2` üstünde `--card` | **6.91** | **6.72** | 4.5 | GEÇTİ — §9 çivisinde var |
| Gölge-varyant kartı gövdesi | `--tx` üstünde `--card` | **18.76** | **10.18** | 4.5 | GEÇTİ — §9 çivisinde var |
| Gölge-varyant "kâğıt defter" çipi (`t-rv`) | `--amber` üstünde `--card` + `--amber-t` | **6.29** | **6.06** | 4.5 | GEÇTİ — §9'daki en kötü hâli (`--card-2` üstünde 5.85/5.39) zaten çivili |
| Öz-değerlendirme kartı (sev çipleri) | `t-no`/`t-rv`/`t-vi`, hepsi taşındı | — | — | — | Renk çifti DEĞİŞMEDİ, yalnız kabı değişti |

Rakamlar `test_tasarim_token_v153`in kendi hesabıyla (source-over alfa birleştirme + WCAG 2.x
bağıl parlaklık) kaynaktan yeniden üretildi. **§9 çivi tablosuna satır eklenmedi**, çünkü eklenecek
yeni bir çift yok — eklemek, aynı rakamı ikinci kez yazıp ikisinin ayrışmasına kapı açardı.

### 10.2 · Bulgu S3-1 · Nötr çipin DOLGUSU gündüz temasında fiilen görünmez (1.02:1)

Ölçüm (dolgunun kart zeminine karşı oranı; metin değil, DOLGU):

| çip dolgusu | gündüz | gece |
|---|---|---|
| `--accent-tint` (t-vi · nötr) | **1.02** | 1.13 |
| `--green-t` (t-go) | 1.16 | 1.20 |
| `--red-t` (t-no) | 1.17 | 1.19 |
| `--amber-t` (t-rv) | 1.16 | 1.20 |

Yani dört çipin DÖRDÜ de "kutu" olarak görünmüyor; hüküm **mürekkepten ve KELİMEDEN** geliyor.
Bu bir gerileme DEĞİL — nötr çip, yanındaki yeşil/kırmızı kardeşleriyle aynı görsel bütçede
duruyor ve ISA-101 disiplininin ("sağlıklı durumun rengi yoktur") beklenen sonucu. **Ama bir
kırılganlık kaydıdır:** üçüncü durumu taşıyan tek güçlü kanal `ÖLÇÜLEMEDİ` kelimesinin kendisi
(18.37:1). Kelime kısaltılır ya da yalnız bir ikona indirilirse durum gündüz temasında
GÖRÜNMEZ olur. Çift kodlama (Ç7) bu yüzden metinle sağlanıyor ve testi var
(`test_s2r3_cila_v160::test_UCUNCU_DURUM_ne_yesil_ne_kirmizi_ve_YENI_RENK_ICAT_ETMEZ`).

**ÖNERİ — UYGULANMADI (Ö-S3-1):** nötr çipe kesikli kenar (`.belirsiz` deseninin çip karşılığı)
vermek, dolgu kontrastına dokunmadan ikinci bir kanal açardı. Uygulanmadı çünkü yeni bir çip
varyantı üç yıl sonra "hangi kenar neydi?" sorusunu doğurur ve bu turun sözleşmesi "mevcut dünya
korunur" idi. Karar bir sonraki jeton yeniden-değerleme turuna bırakıldı.

### 10.3 · Yeniden doğrulanan kural: boşluk jetonları renk çiftlerini kaydırmaz

S2R-3'ün asıl işi boşluktu (blok ritmi `--s4`/`--s5`/`--s12`+`--s10`). Boşluk jetonlarının
kontrasta etkisi YOKTUR ve bu ölçüldü değil, yapısaldır: `--s*` jetonları `dimension` tipinde,
hiçbiri `color` katmanında değil (`test_tasarim_token_v153::test_renk_jetonlarinin_HEPSI_renk_
TEMEL_jetonlarin_HICBIRI_degil` bunu her koşumda ayırıyor). Yeni jeton EKLENMEDİ: jeton sayımı
23 temel + 2×36 renk = 95, S2R-3 öncesiyle aynı.
