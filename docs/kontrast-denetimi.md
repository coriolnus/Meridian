# Kontrast denetimi — Meridian panosu (WCAG 2.2 AA, iki tema)

> **Bilet:** UIUX S1-T2 (`docs/UIUX-WORKORDER.md` § Program V / Program X · `docs/UIUX-WP0.md` borç #5).
> **Tarih:** 2026-08-01 (S1-T2 denetimi) · **2026-08-02 YENİDEN ÖLÇÜLDÜ** (WP-P/P9 jeton turu, §11).
> **Kapsam:** `meridian/web/index.html` `<style>` bloğundaki 68 jeton, iki temada, ve bu
> jetonların panoda fiilen kurduğu 148 çift.
> **S1-T2 TURU DEĞER DEĞİŞTİRMEDİ; P9 TURU DEĞİŞTİRDİ.** İlk denetim yalnız ölçtü ve hüküm
> önerilerini §7'ye yazdı. Operatör onaylı P9 turunda (2026-08-02) o önerilerden üçü uygulandı
> (Ö1 · Ö8 · gündüz beyazı) ve **§3'ün TAMAMI kaynaktan yeniden üretildi** — bu rapor bayat
> DEĞİLDİR ve bayatlamadığı her koşumda `test_tasarim_token_v153` tarafından ölçülür.

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
   bayatlık solması %42–78, hücre tinti %7–8, kapsama rampası %6–30, sapma kutupları %10–22.
   Bunları opak sanmak, aşağıdaki 51 kalanın yarısını görünmez yapardı. (Bu raporun DESIGN.md'den ayrıldığı ilk yer — bkz. §8.)
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
| **Metin (4.5:1)** | 75 | 69 | **6** |
| **Metin-dışı (3:1)** | 73 | 28 | **45** |
| **TOPLAM** | **148** | **97** | **51** |

2026-08-01 sayımı 136 çift / 42 kalan idi. Fark bir gerileme değil, **yeni ölçüm yüzeyi**:
P9 turu 14 çift ekledi (kapsama ısı-matrisinin sequential rampası + sapmanın diverging
kutupları, §3-J), merdiven/seri satırları yeniden yazıldı ve gündüz yüzeyleri indi. Değişen
çiftlerin önce→sonra tablosu §11.2'de; bir tek çift hüküm değiştirmedi.

Kalanların dağılımı bir tesadüf değil, bir tasarım hükmünün faturası:

- **45 metin-dışı kalanın 28'i saç teli, ray ve ton basamağıdır** — yani "kutu değil saç
  teli, gölge değil ton" kararının doğrudan sonucu. Bunlar DESIGN.md'de zaten **beyanlı
  sapma**; §6'da gerekçeleriyle durur ve bu turda da açık kalır.
- **14'ü ÖLÇEK basamağıdır** (kapsama rampası, sapma kutupları, nitel bant merdiveni, IC
  serileri) ve bu turda BEYAN EDİLDİ: bir ısı skalası 3:1 adımlarla kurulamaz — hüküm
  hücrenin RAKAMINDAN gelir (§6/İ8).
- **B1 ve B6 KAPANDI** (§5): yoğunluk merdiveninin son iki basamağı ile IC-trendinin iki
  serisi artık aynı renk DEĞİL. Açık kalan iki beyansız bulgu: bullet ölçüm çubuğu gece en
  koyu bandın üstünde kayboluyor (B2), ve bayatlık solmasının 2./3. kademesi okunaklılığın
  altına iniyor (B3).
- **6 metin kalanının tamamı `opacity` ile soldurulmuş metindir.** Hiçbiri jeton
  değerinden gelmiyor; hepsi kuralın içindeki bir opaklık çarpanından geliyor. Yani
  panonun **renk paleti AA'yı geçiyor, opaklık disiplini geçmiyor.**

Metin katmanının çekirdeği — gövde mürekkebi (9/9), vurgu (8/8), para renkleri (31/31),
dolgu üstü ters mürekkep (3/3) — **iki temada da tam geçer** ve en kötü gerçek bileşik
zeminde bile pay bırakır (en dar: `--red` kendi tintinde gömülü panelde **4.59**, gündüz —
P9 turunda 4.78'den indi ve o pay artık paletin **bağlayıcı kısıtıdır**, bkz. §11.1).

## 3 · Tam tablo

Her satır: çift · L1 (mürekkep, bileşiklenmiş) · L2 (zemin, bileşiklenmiş) · oran ·
eşik · hüküm. Hex değerleri `gündüz/gece` sırasıyla verilir.

### A · gövde mürekkebi
| çift | L1 (mürekkep) | L2 (zemin) | gündüz | gece | eşik | hüküm |
|---|---|---|---|---|---|---|
| `--tx` — body · sayfa gövdesi | #050505/#d4d0cb | #fbf9f8/#1c1a18 | **19.42** | **11.31** | 4.5:1 | geçti |
| `--tx` — kbd · girdi · .ksgroup düğmesi · .pm-strip · .pane | #050505/#d4d0cb | #f5f4f2/#232120 | **18.54** | **10.45** | 4.5:1 | geçti |
| `--tx` — .card/.hero/.gate-card/.kbd-panel/.ksgroup/.gloss içi | #050505/#d4d0cb | #f2efed/#262320 | **17.80** | **10.18** | 4.5:1 | geçti |
| `--tx` — .sitem:hover · .rowbtn:hover · .mcard:hover · .hyp:hover | #050505/#d4d0cb | #ece7e3/#2f2b27 | **16.60** | **9.15** | 4.5:1 | geçti |
| `--tx` — .rowbtn.sel · .sitem.tema:hover · palet seçili satır | #050505/#d4d0cb | #eeeeee/#302c28 | **17.57** | **9.02** | 4.5:1 | geçti |
| `--tx` — .spine.attn .msg | #050505/#d4d0cb | #ede8df/#30281a | **16.70** | **9.48** | 4.5:1 | geçti |
| `--tx` — .spine.act .msg | #050505/#d4d0cb | #f4e4e4/#322524 | **16.56** | **9.60** | 4.5:1 | geçti |
| `--tx` — kart içi kehribar çip metni | #050505/#d4d0cb | #e5ded5/#393021 | **15.28** | **8.45** | 4.5:1 | geçti |
| `--tx` — en kötü gerçek bileşik | #050505/#d4d0cb | #e6d4d1/#433531 | **14.27** | **7.64** | 4.5:1 | geçti |

### B · ikincil mürekkep
| çift | L1 (mürekkep) | L2 (zemin) | gündüz | gece | eşik | hüküm |
|---|---|---|---|---|---|---|
| `--tx2` — .subline · .sessizhat · .hint · footer | #585450/#b0a9a0 | #fbf9f8/#1c1a18 | **7.15** | **7.46** | 4.5:1 | geçti |
| `--tx2` — .mono · .pd-* çekmece etiketleri · .pane | #585450/#b0a9a0 | #f5f4f2/#232120 | **6.83** | **6.89** | 4.5:1 | geçti |
| `--tx2` — .statuspill · .hudchip · .bl-lab · .bl-ax · .gc.arrow · kart etiketleri | #585450/#b0a9a0 | #f2efed/#262320 | **6.55** | **6.72** | 4.5:1 | geçti |
| `--tx2` — .sitem:hover .sub · hover satırları | #585450/#b0a9a0 | #ece7e3/#2f2b27 | **6.11** | **6.04** | 4.5:1 | geçti |
| `--tx2` — .slabel komşu metin · seçili satır alt-okuma | #585450/#b0a9a0 | #eeeeee/#302c28 | **6.47** | **5.95** | 4.5:1 | geçti |
| `--tx2` — yeşil çip içi ikincil | #585450/#b0a9a0 | #dbe2db/#2a332b | **5.69** | **5.62** | 4.5:1 | geçti |
| `--tx2` — kehribar çip içi ikincil | #585450/#b0a9a0 | #e5ded5/#393021 | **5.62** | **5.58** | 4.5:1 | geçti |
| `--tx2` — kırmızı çip içi ikincil | #585450/#b0a9a0 | #ecdbda/#3b2d2b | **5.61** | **5.66** | 4.5:1 | geçti |
| `--tx2` — en kötü gerçek bileşik (DESIGN.md hükmü) | #585450/#b0a9a0 | #e6d4d1/#433531 | **5.25** | **5.04** | 4.5:1 | geçti |
| `--tx2` — kehribar çip / gömülü panel | #585450/#b0a9a0 | #dfd7cc/#413828 | **5.26** | **4.96** | 4.5:1 | geçti |
| `--tx2` — .pm-n pozitif hücrede | #585450/#b0a9a0 | #e8eee9/#202821 | **6.37** | **6.51** | 4.5:1 | geçti |
| `--tx2` — .pm-n negatif hücrede | #585450/#b0a9a0 | #f6eaea/#2b2220 | **6.39** | **6.68** | 4.5:1 | geçti |
| `--tx2` — .statuspill üst barda (kart opak, bar altta) | #585450/#b0a9a0 | #fbf9f8/#1c1a18 | **7.15** | **7.46** | 4.5:1 | geçti |
| `--slip-ink` — .term::after ipucu (slip-ink) | #050505/#d4d0cb | #ece7e3/#2f2b27 | **16.60** | **9.15** | 4.5:1 | geçti |
| `--tx2@0.7` — .sitem .sub (opacity .7) rayda | #898682/#847e77 | #fbf9f8/#1c1a18 | **3.45** | **4.32** | 4.5:1 | KALDI |
| `--tx2@0.7` — .pm-none (opacity .7) ekilmemiş hücrede | #878481/#86807a | #f5f4f2/#232120 | **3.38** | **4.11** | 4.5:1 | KALDI |
| `--tx2@0.45` — .sessizhat .sh-sep (opacity .45) | #b2afac/#5f5a55 | #fbf9f8/#1c1a18 | **2.08** | **2.54** | 3.0:1 | KALDI |
| `--tx2@0.78` — .bayat-1 (opacity .78) sayfa zemininde | #7c7875/#8f8a82 | #fbf9f8/#1c1a18 | **4.17** | **5.06** | 4.5:1 | gündüz KALDI · gece geçti |
| `--tx2@0.58` — .bayat-2 (opacity .58) sayfa zemininde | #9c9997/#726d67 | #fbf9f8/#1c1a18 | **2.70** | **3.39** | 4.5:1 | KALDI |
| `--tx2@0.42` — .bayat-3 (opacity .42) sayfa zemininde | #b7b4b1/#5a5651 | #fbf9f8/#1c1a18 | **1.97** | **2.38** | 4.5:1 | KALDI |
| `--tx2@0.42` — .bayat-3 (opacity .42) kart üstünde | #b1aeab/#605b56 | #f2efed/#262320 | **1.93** | **2.33** | 4.5:1 | KALDI |

### C · vurgu mürekkebi
| çift | L1 (mürekkep) | L2 (zemin) | gündüz | gece | eşik | hüküm |
|---|---|---|---|---|---|---|
| `--accent-2` — .slabel · .t-vi · .lv.on · code · .dlbtn:hover | #050505/#e8e4df | #eeeeee/#302c28 | **17.57** | **10.94** | 4.5:1 | geçti |
| `--accent-2` — .card .t · .sitem.on .sub · .regrow.live .nm | #050505/#e8e4df | #f2efed/#262320 | **17.80** | **12.35** | 4.5:1 | geçti |
| `--accent-2` — .pd-l · .mono .k · .pane içi anahtar | #050505/#e8e4df | #f5f4f2/#232120 | **18.54** | **12.67** | 4.5:1 | geçti |
| `--accent-2` — .spine.calm hover · sayfa zemininde bağ | #050505/#e8e4df | #fbf9f8/#1c1a18 | **19.42** | **13.71** | 4.5:1 | geçti |
| `--accent-2` — .spine.attn .items button:hover | #050505/#e8e4df | #ede8df/#30281a | **16.70** | **11.49** | 4.5:1 | geçti |
| `--accent-2` — .spine.act .items button:hover | #050505/#e8e4df | #f4e4e4/#322524 | **16.56** | **11.64** | 4.5:1 | geçti |
| `--accent` — .gloss summary · .kbd-panel h3.t · .hstat .l | #050505/#d4d0cb | #f2efed/#262320 | **17.80** | **10.18** | 4.5:1 | geçti |
| `--accent` — .spine .items button:hover::after | #050505/#d4d0cb | #fbf9f8/#1c1a18 | **19.42** | **11.31** | 4.5:1 | geçti |

### D · para renkleri (metin)
| çift | L1 (mürekkep) | L2 (zemin) | gündüz | gece | eşik | hüküm |
|---|---|---|---|---|---|---|
| `--green` — çip: kendi tinti sayfa zemininde | #0c6a3b/#4cc38a | #e3ebe5/#212b23 | **5.50** | **6.61** | 4.5:1 | geçti |
| `--green` — çip: kendi tinti çekmece/pano zemininde (.pd-warn · .mono) | #0c6a3b/#4cc38a | #dee6e0/#27312b | **5.25** | **6.08** | 4.5:1 | geçti |
| `--green` — çip: kendi tinti kart üstünde (.t-go/.t-rv/.t-no · .ck.*) | #0c6a3b/#4cc38a | #dbe2db/#2a332b | **5.07** | **5.90** | 4.5:1 | geçti |
| `--green` — çip: kendi tinti gömülü panelde — EN KÖTÜ GERÇEK ZEMİN | #0c6a3b/#4cc38a | #d6dad2/#323a31 | **4.72** | **5.31** | 4.5:1 | geçti |
| `--green` — çıplak: .pos/.neg/.warn sayfa zemininde | #0c6a3b/#4cc38a | #fbf9f8/#1c1a18 | **6.37** | **7.83** | 4.5:1 | geçti |
| `--green` — çıplak: .mono .ok/.w/.no · .ksgroup düğme hover | #0c6a3b/#4cc38a | #f5f4f2/#232120 | **6.08** | **7.24** | 4.5:1 | geçti |
| `--green` — çıplak: .hudchip.explore · .gate-msg · .sh-sap · palet rozeti | #0c6a3b/#4cc38a | #f2efed/#262320 | **5.84** | **7.06** | 4.5:1 | geçti |
| `--green` — çıplak: hover satırında para rengi | #0c6a3b/#4cc38a | #ece7e3/#2f2b27 | **5.45** | **6.34** | 4.5:1 | geçti |
| `--amber` — çip: kendi tinti sayfa zemininde | #6e4a00/#e0a82e | #ede8df/#30281a | **6.51** | **6.79** | 4.5:1 | geçti |
| `--amber` — çip: kendi tinti çekmece/pano zemininde (.pd-warn · .mono) | #6e4a00/#e0a82e | #e8e3da/#362e21 | **6.22** | **6.25** | 4.5:1 | geçti |
| `--amber` — çip: kendi tinti kart üstünde (.t-go/.t-rv/.t-no · .ck.*) | #6e4a00/#e0a82e | #e5ded5/#393021 | **5.96** | **6.06** | 4.5:1 | geçti |
| `--amber` — çip: kendi tinti gömülü panelde — EN KÖTÜ GERÇEK ZEMİN | #6e4a00/#e0a82e | #dfd7cc/#413828 | **5.57** | **5.39** | 4.5:1 | geçti |
| `--amber` — çıplak: .pos/.neg/.warn sayfa zemininde | #6e4a00/#e0a82e | #fbf9f8/#1c1a18 | **7.57** | **8.11** | 4.5:1 | geçti |
| `--amber` — çıplak: .mono .ok/.w/.no · .ksgroup düğme hover | #6e4a00/#e0a82e | #f5f4f2/#232120 | **7.23** | **7.49** | 4.5:1 | geçti |
| `--amber` — çıplak: .hudchip.explore · .gate-msg · .sh-sap · palet rozeti | #6e4a00/#e0a82e | #f2efed/#262320 | **6.94** | **7.30** | 4.5:1 | geçti |
| `--amber` — çıplak: hover satırında para rengi | #6e4a00/#e0a82e | #ece7e3/#2f2b27 | **6.47** | **6.56** | 4.5:1 | geçti |
| `--red` — çip: kendi tinti sayfa zemininde | #b3242c/#f58b8f | #f4e4e4/#322524 | **5.32** | **6.29** | 4.5:1 | geçti |
| `--red` — çip: kendi tinti çekmece/pano zemininde (.pd-warn · .mono) | #b3242c/#f58b8f | #eedfde/#382c2b | **5.07** | **5.74** | 4.5:1 | geçti |
| `--red` — çip: kendi tinti kart üstünde (.t-go/.t-rv/.t-no · .ck.*) | #b3242c/#f58b8f | #ecdbda/#3b2d2b | **4.90** | **5.62** | 4.5:1 | geçti |
| `--red` — çip: kendi tinti gömülü panelde — EN KÖTÜ GERÇEK ZEMİN | #b3242c/#f58b8f | #e6d4d1/#433531 | **4.59** | **5.01** | 4.5:1 | geçti |
| `--red` — çıplak: .pos/.neg/.warn sayfa zemininde | #b3242c/#f58b8f | #fbf9f8/#1c1a18 | **6.24** | **7.41** | 4.5:1 | geçti |
| `--red` — çıplak: .mono .ok/.w/.no · .ksgroup düğme hover | #b3242c/#f58b8f | #f5f4f2/#232120 | **5.96** | **6.85** | 4.5:1 | geçti |
| `--red` — çıplak: .hudchip.explore · .gate-msg · .sh-sap · palet rozeti | #b3242c/#f58b8f | #f2efed/#262320 | **5.72** | **6.68** | 4.5:1 | geçti |
| `--red` — çıplak: hover satırında para rengi | #b3242c/#f58b8f | #ece7e3/#2f2b27 | **5.34** | **6.00** | 4.5:1 | geçti |
| `--green` — .pm-cell.pos .pm-yield (hücre kendi tintinde) | #0c6a3b/#4cc38a | #e8eee9/#202821 | **5.68** | **6.84** | 4.5:1 | geçti |
| `--red` — .pm-cell.neg .pm-yield (hücre kendi tintinde) | #b3242c/#f58b8f | #f6eaea/#2b2220 | **5.58** | **6.63** | 4.5:1 | geçti |
| `--amber` — .pm-thin ekim-az kazığı (kehribar tint + pozitif hücre) | #6e4a00/#e0a82e | #dcded2/#333522 | **5.84** | **5.86** | 4.5:1 | geçti |
| `--amber` — .pm-thin ekim-az kazığı (kehribar tint + negatif hücre) | #6e4a00/#e0a82e | #e8dad3/#3d2f21 | **5.83** | **6.03** | 4.5:1 | geçti |
| `--red` — HALT/KRİZ etiketi üst barda (bar sayfa üstünde) | #b3242c/#f58b8f | #fbf9f8/#1c1a18 | **6.24** | **7.41** | 4.5:1 | geçti |
| `--red` — HALT/KRİZ etiketi üst barda (bar kart üstünde kayarken) | #b3242c/#f58b8f | #f8f6f4/#1f1d1b | **6.08** | **7.18** | 4.5:1 | geçti |
| `--red` — .kscover:hover (kırmızı tint üst barda) | #b3242c/#f58b8f | #f4e4e4/#322524 | **5.32** | **6.29** | 4.5:1 | geçti |

### E · dolgu üstü metin
| çift | L1 (mürekkep) | L2 (zemin) | gündüz | gece | eşik | hüküm |
|---|---|---|---|---|---|---|
| `--bg2` — .gate-btn · .pillc · .dlbtn.primary · birincil eylem | #f5f4f2/#232120 | #050505/#d4d0cb | **18.54** | **10.45** | 4.5:1 | geçti |
| `--bg2` — .dlbtn.primary:hover · .skip (içeriğe atla) | #f5f4f2/#232120 | #050505/#e8e4df | **18.54** | **12.67** | 4.5:1 | geçti |
| `--bg2` — .halt:hover · .kscover[aria-expanded=true] | #f5f4f2/#232120 | #b3242c/#f58b8f | **5.96** | **6.85** | 4.5:1 | geçti |

### F · metin-dışı: kenar
| çift | L1 (mürekkep) | L2 (zemin) | gündüz | gece | eşik | hüküm |
|---|---|---|---|---|---|---|
| `--line` — varsayılan saç teli · bg | #e2deda/#38342f | #fbf9f8/#1c1a18 | **1.27** | **1.40** | 3.0:1 | KALDI |
| `--line` — varsayılan saç teli · bg2 | #e2deda/#38342f | #f5f4f2/#232120 | **1.22** | **1.30** | 3.0:1 | KALDI |
| `--line` — varsayılan saç teli · card | #e2deda/#38342f | #f2efed/#262320 | **1.17** | **1.27** | 3.0:1 | KALDI |
| `--line` — varsayılan saç teli · card-2 | #e2deda/#38342f | #ece7e3/#2f2b27 | **1.09** | **1.14** | 3.0:1 | KALDI |
| `--line-2` — güçlü saç teli · bg | #d4cfca/#4a453f | #fbf9f8/#1c1a18 | **1.47** | **1.83** | 3.0:1 | KALDI |
| `--line-2` — güçlü saç teli · bg2 | #d4cfca/#4a453f | #f5f4f2/#232120 | **1.41** | **1.69** | 3.0:1 | KALDI |
| `--line-2` — güçlü saç teli · card | #d4cfca/#4a453f | #f2efed/#262320 | **1.35** | **1.65** | 3.0:1 | KALDI |
| `--line-2` — güçlü saç teli · card-2 | #d4cfca/#4a453f | #ece7e3/#2f2b27 | **1.26** | **1.48** | 3.0:1 | KALDI |
| `--field` — form kontrolü kenarı (metin girişi/select) · bg | #86817d/#7e776e | #fbf9f8/#1c1a18 | **3.67** | **3.93** | 3.0:1 | geçti |
| `--field` — form kontrolü kenarı (metin girişi/select) · bg2 | #86817d/#7e776e | #f5f4f2/#232120 | **3.51** | **3.63** | 3.0:1 | geçti |
| `--field` — form kontrolü kenarı (metin girişi/select) · card | #86817d/#7e776e | #f2efed/#262320 | **3.37** | **3.54** | 3.0:1 | geçti |
| `--field` — form kontrolü kenarı (metin girişi/select) · card-2 | #86817d/#7e776e | #ece7e3/#2f2b27 | **3.14** | **3.18** | 3.0:1 | geçti |
| `--green-h` — .t-go/.pillc.g/.ck.ok çip iç kenarı kendi dolgusunda | #93b8a3/#36654c | #dbe2db/#2a332b | **1.65** | **1.94** | 3.0:1 | KALDI |
| `--amber-h` — .t-rv/.ck.man çip iç kenarı kendi dolgusunda | #bbaa8a/#735a26 | #e5ded5/#393021 | **1.71** | **1.99** | 3.0:1 | KALDI |
| `--red-h` — .t-no/.s-rb çip iç kenarı kendi dolgusunda | #d89b9d/#7c4e4e | #ecdbda/#3b2d2b | **1.73** | **1.92** | 3.0:1 | KALDI |
| `--amber-h2` — .pd-warn kenarı kendi dolgusunda | #b7a683/#7a5f26 | #e8e3da/#362e21 | **1.87** | **2.22** | 3.0:1 | KALDI |
| `--ink-h-soft` — .slabel kenarı (ink-h-soft) tint üstünde | #c4c4c4/#4e4a45 | #eeeeee/#302c28 | **1.50** | **1.58** | 3.0:1 | KALDI |
| `--ink-h` — .t-vi/.lv.on kenarı (ink-h) tint üstünde | #a8a8a8/#615d59 | #eeeeee/#302c28 | **2.05** | **2.12** | 3.0:1 | KALDI |
| `--amber-h` — .pm-cell.thin kehribar iç kenarı (pozitif hücre) | #bdb597/#635526 | #e8eee9/#202821 | **1.75** | **2.06** | 3.0:1 | KALDI |
| `--line-2` — nav alt kenarı (line-2) sayfa üstünde | #d4cfca/#4a453f | #fbf9f8/#1c1a18 | **1.47** | **1.83** | 3.0:1 | KALDI |

### G · durum grafikleri
| çift | L1 (mürekkep) | L2 (zemin) | gündüz | gece | eşik | hüküm |
|---|---|---|---|---|---|---|
| `--green` — .dot sağlıklı (yeşil) üst barda | #0c6a3b/#4cc38a | #fbf9f8/#1c1a18 | **6.37** | **7.83** | 3.0:1 | geçti |
| `--amber` — .dot.stale (kehribar) üst barda | #6e4a00/#e0a82e | #fbf9f8/#1c1a18 | **7.57** | **8.11** | 3.0:1 | geçti |
| `--red` — .dot.halt (kırmızı) üst barda | #b3242c/#f58b8f | #fbf9f8/#1c1a18 | **6.24** | **7.41** | 3.0:1 | geçti |
| `--green` — .hudchip .ld yeşil (çip zemini kart) | #0c6a3b/#4cc38a | #f2efed/#262320 | **5.84** | **7.06** | 3.0:1 | geçti |
| `--amber` — .hudchip .ld.warn kehribar | #6e4a00/#e0a82e | #f2efed/#262320 | **6.94** | **7.30** | 3.0:1 | geçti |
| `--red` — .hudchip .ld.bad kırmızı | #b3242c/#f58b8f | #f2efed/#262320 | **5.72** | **6.68** | 3.0:1 | geçti |
| `--tx2` — .hudchip .ld.off (tx2) | #585450/#b0a9a0 | #f2efed/#262320 | **6.55** | **6.72** | 3.0:1 | geçti |
| `--green` — .spine::before damga (yeşil) kart üstünde | #0c6a3b/#4cc38a | #f2efed/#262320 | **5.84** | **7.06** | 3.0:1 | geçti |
| `--green-stamp` — .spine.calm::before damga (green-stamp) sayfa üstünde | #78aa90/#367757 | #fbf9f8/#1c1a18 | **2.52** | **3.25** | 3.0:1 | gündüz KALDI · gece geçti |
| `--amber` — .spine.attn::before damga kendi bandında | #6e4a00/#e0a82e | #ede8df/#30281a | **6.51** | **6.79** | 3.0:1 | geçti |
| `--red` — .spine.act::before damga kendi bandında | #b3242c/#f58b8f | #f4e4e4/#322524 | **5.32** | **6.29** | 3.0:1 | geçti |
| `--accent` — .sitem::before etkin görünüm işareti (3px) | #050505/#d4d0cb | #fbf9f8/#1c1a18 | **19.42** | **11.31** | 3.0:1 | geçti |
| `--amber@0.7` — body.explore-mode::after keşif çerçevesi (2px, opacity .7) | #987f4a/#a57d27 | #fbf9f8/#1c1a18 | **3.66** | **4.60** | 3.0:1 | geçti |
| `--pm-pos` — .pm-cell.pos hücre zemini ↔ nötr hücre (işaret kodlaması) | #e8eee9/#202821 | #fbf9f8/#1c1a18 | **1.12** | **1.15** | 3.0:1 | KALDI |
| `--pm-neg` — .pm-cell.neg hücre zemini ↔ nötr hücre (işaret kodlaması) | #f6eaea/#2b2220 | #fbf9f8/#1c1a18 | **1.12** | **1.12** | 3.0:1 | KALDI |

### H · ölçüm grafikleri
| çift | L1 (mürekkep) | L2 (zemin) | gündüz | gece | eşik | hüküm |
|---|---|---|---|---|---|---|
| `--accent` — .bar dolgusu (accent) ↔ ray (bg2) | #050505/#d4d0cb | #f5f4f2/#232120 | **18.54** | **10.45** | 3.0:1 | geçti |
| `--bg2` — .bar rayı (bg2) ↔ kart zemini | #f5f4f2/#232120 | #f2efed/#262320 | **1.04** | **1.03** | 3.0:1 | KALDI |
| `--line` — .bar ray kenarı (line) ↔ ray | #e2deda/#38342f | #f5f4f2/#232120 | **1.22** | **1.30** | 3.0:1 | KALDI |
| `--accent` — .thermo tüp dolgusu (accent) ↔ tüp (bg2) | #050505/#d4d0cb | #f5f4f2/#232120 | **18.54** | **10.45** | 3.0:1 | geçti |
| `--raise` — --raise ölçer rayı ↔ kart (DESIGN.md beyanlı) | #fbf9f8/#38342f | #f2efed/#262320 | **1.09** | **1.27** | 3.0:1 | KALDI |
| `--line` — .pm-conf güven rayı (line) ↔ pozitif hücre | #e2deda/#38342f | #e8eee9/#202821 | **1.14** | **1.23** | 3.0:1 | KALDI |
| `--green@0.85` — .pm-conf dolgusu (yeşil @.85) ↔ güven rayı | #2c7b53/#49ae7c | #e2deda/#38342f | **3.86** | **4.49** | 3.0:1 | geçti |
| `--red@0.85` — .pm-conf dolgusu (kırmızı @.85) ↔ güven rayı | #ba4046/#d97e81 | #e2deda/#38342f | **4.01** | **4.26** | 3.0:1 | geçti |
| `--accent` — equity çizgisi (accent) ↔ kart zemini | #050505/#d4d0cb | #f2efed/#262320 | **17.80** | **10.18** | 3.0:1 | geçti |
| `--tx2` — sparkline/eksen (tx2) ↔ kart zemini | #585450/#b0a9a0 | #f2efed/#262320 | **6.55** | **6.72** | 3.0:1 | geçti |
| `--line-2` — grafik ızgarası (line-2) ↔ kart zemini | #d4cfca/#4a453f | #f2efed/#262320 | **1.35** | **1.65** | 3.0:1 | KALDI |
| `--line` — IC trendi: sıfır ekseni (line) ↔ kart zemini | #e2deda/#38342f | #f2efed/#262320 | **1.17** | **1.27** | 3.0:1 | KALDI |
| `--card-2` — yoğunluk merdiveni: bant1 (card-2) ↔ kart zemini | #ece7e3/#2f2b27 | #f2efed/#262320 | **1.07** | **1.11** | 3.0:1 | KALDI |
| `--band-2` — yoğunluk merdiveni: bant1 (card-2) ↔ bant2 (band-2) | #ece7e3/#2f2b27 | #979491/#676665 | **2.46** | **2.45** | 3.0:1 | KALDI |
| `--tx2` — yoğunluk merdiveni: bant2 (band-2) ↔ bant3 (tx2) | #979491/#676665 | #585450/#b0a9a0 | **2.49** | **2.46** | 3.0:1 | KALDI |
| `--accent` — bullet ölçüm çubuğu (accent) ↔ en açık bant (card-2) | #050505/#d4d0cb | #ece7e3/#2f2b27 | **16.60** | **9.15** | 3.0:1 | geçti |
| `--accent` — bullet ölçüm çubuğu (accent) ↔ en koyu bant (tx2) | #050505/#d4d0cb | #585450/#b0a9a0 | **2.72** | **1.52** | 3.0:1 | KALDI |
| `--violet` — IC trendi: `gerçek` (accent) ↔ `sim` (violet) | #050505/#d4d0cb | #3e3c39/#b1afad | **1.85** | **1.42** | 3.0:1 | KALDI |
| `--tx3` — IC trendi: `sim` (violet) ↔ `havuz` (tx3) | #3e3c39/#b1afad | #686562/#95928f | **1.90** | **1.42** | 3.0:1 | KALDI |
| `--tx3` — IC trendi: `gerçek` (accent) ↔ `havuz` (tx3) | #050505/#d4d0cb | #686562/#95928f | **3.52** | **2.02** | 3.0:1 | gündüz geçti · gece KALDI |

### I · odak halkası
| çift | L1 (mürekkep) | L2 (zemin) | gündüz | gece | eşik | hüküm |
|---|---|---|---|---|---|---|
| `--accent` — :focus-visible 2px --accent · sayfa zemininde | #050505/#d4d0cb | #fbf9f8/#1c1a18 | **19.42** | **11.31** | 3.0:1 | geçti |
| `--accent` — :focus-visible 2px --accent · kart üstünde | #050505/#d4d0cb | #f2efed/#262320 | **17.80** | **10.18** | 3.0:1 | geçti |
| `--accent` — :focus-visible 2px --accent · gömülü panelde | #050505/#d4d0cb | #ece7e3/#2f2b27 | **16.60** | **9.15** | 3.0:1 | geçti |
| `--accent` — :focus-visible 2px --accent · seçili satırda | #050505/#d4d0cb | #eeeeee/#302c28 | **17.57** | **9.02** | 3.0:1 | geçti |
| `--accent` — :focus-visible 2px --accent · kırmızı çip üstünde | #050505/#d4d0cb | #ecdbda/#3b2d2b | **15.25** | **8.57** | 3.0:1 | geçti |
| `--card` — modal kart ↔ perdeyle karartılmış sayfa (.kbd-panel ↔ .kbd-ov) | #f2efed/#262320 | #949392/#100f0d | **2.68** | **1.23** | 3.0:1 | KALDI |
| `--card` — modal kart ↔ perdeyle karartılmış KART zemini | #f2efed/#262320 | #8e8d8c/#141210 | **2.89** | **1.20** | 3.0:1 | KALDI |

### J · kapsama ısı-matrisi (P9)
| çift | L1 (mürekkep) | L2 (zemin) | gündüz | gece | eşik | hüküm |
|---|---|---|---|---|---|---|
| `--kap-1` — kapsama bandı 1 ↔ kart zemini | #e4e1df/#302d2a | #f2efed/#262320 | **1.14** | **1.14** | 3.0:1 | KALDI |
| `--kap-2` — kapsama bandı 2 ↔ bandı 1 | #d1cecd/#3e3b38 | #e4e1df/#302d2a | **1.20** | **1.23** | 3.0:1 | KALDI |
| `--kap-3` — kapsama bandı 3 ↔ bandı 2 | #bbb9b8/#4e4b47 | #d1cecd/#3e3b38 | **1.25** | **1.28** | 3.0:1 | KALDI |
| `--kap-4` — kapsama bandı 4 ↔ bandı 3 | #aba9a7/#5a5753 | #bbb9b8/#4e4b47 | **1.20** | **1.21** | 3.0:1 | KALDI |
| `--kap-4` — kapsama bandı 4 ↔ kart zemini (uç-uca menzil) | #aba9a7/#5a5753 | #f2efed/#262320 | **2.05** | **2.18** | 3.0:1 | KALDI |
| `--tx` — hücre rakamı en KOYU kapsama bandında | #050505/#d4d0cb | #aba9a7/#5a5753 | **8.70** | **4.68** | 4.5:1 | geçti |
| `--tx` — hücre rakamı en açık kapsama bandında | #050505/#d4d0cb | #e4e1df/#302d2a | **15.66** | **8.92** | 4.5:1 | geçti |
| `--dv-n2` — sapma: eksi kutbu (güçlü) ↔ kart zemini | #c7ccd4/#3c4045 | #f2efed/#262320 | **1.41** | **1.50** | 3.0:1 | KALDI |
| `--dv-p2` — sapma: artı kutbu (güçlü) ↔ kart zemini | #dad2c3/#494234 | #f2efed/#262320 | **1.31** | **1.57** | 3.0:1 | KALDI |
| `--dv-n1` — sapma: eksi kutbu (zayıf) ↔ kart zemini | #dedfe2/#303031 | #f2efed/#262320 | **1.16** | **1.19** | 3.0:1 | KALDI |
| `--dv-p1` — sapma: artı kutbu (zayıf) ↔ kart zemini | #e7e2da/#363129 | #f2efed/#262320 | **1.13** | **1.21** | 3.0:1 | KALDI |
| `--dv-p2` — sapma: eksi kutbu ↔ artı kutbu (kutuplar arası) | #c7ccd4/#3c4045 | #dad2c3/#494234 | **1.07** | **1.05** | 3.0:1 | KALDI |
| `--tx` — hücre rakamı en güçlü sapma dolgusunda (eksi) | #050505/#d4d0cb | #c7ccd4/#3c4045 | **12.63** | **6.80** | 4.5:1 | geçti |
| `--tx` — hücre rakamı en güçlü sapma dolgusunda (artı) | #050505/#d4d0cb | #dad2c3/#494234 | **13.58** | **6.48** | 4.5:1 | geçti |

Bölüm başlıkları: **A** gövde mürekkebi · **B** ikincil mürekkep · **C** vurgu mürekkebi ·
**D** para renkleri · **E** dolgu üstü ters mürekkep · **F** metin-dışı kenarlar ·
**G** durum grafikleri · **H** ölçüm grafikleri · **I** odak halkası ve perde ·
**J** kapsama ısı-matrisi (P9 · 2026-08-02'de eklendi).

## 4 · Kalanların tam listesi (51)
- B · ikincil mürekkep · .sitem .sub (opacity .7) rayda  → gündüz 3.45 · gece 4.32 (eşik 4.5)
- B · ikincil mürekkep · .pm-none (opacity .7) ekilmemiş hücrede  → gündüz 3.38 · gece 4.11 (eşik 4.5)
- B · ikincil mürekkep · .sessizhat .sh-sep (opacity .45)  → gündüz 2.08 · gece 2.54 (eşik 3.0)
- B · ikincil mürekkep · .bayat-1 (opacity .78) sayfa zemininde  → gündüz 4.17 · gece 5.06 (eşik 4.5)
- B · ikincil mürekkep · .bayat-2 (opacity .58) sayfa zemininde  → gündüz 2.70 · gece 3.39 (eşik 4.5)
- B · ikincil mürekkep · .bayat-3 (opacity .42) sayfa zemininde  → gündüz 1.97 · gece 2.38 (eşik 4.5)
- B · ikincil mürekkep · .bayat-3 (opacity .42) kart üstünde  → gündüz 1.93 · gece 2.33 (eşik 4.5)
- F · metin-dışı: kenar · varsayılan saç teli · bg  → gündüz 1.27 · gece 1.40 (eşik 3.0)
- F · metin-dışı: kenar · varsayılan saç teli · bg2  → gündüz 1.22 · gece 1.30 (eşik 3.0)
- F · metin-dışı: kenar · varsayılan saç teli · card  → gündüz 1.17 · gece 1.27 (eşik 3.0)
- F · metin-dışı: kenar · varsayılan saç teli · card-2  → gündüz 1.09 · gece 1.14 (eşik 3.0)
- F · metin-dışı: kenar · güçlü saç teli · bg  → gündüz 1.47 · gece 1.83 (eşik 3.0)
- F · metin-dışı: kenar · güçlü saç teli · bg2  → gündüz 1.41 · gece 1.69 (eşik 3.0)
- F · metin-dışı: kenar · güçlü saç teli · card  → gündüz 1.35 · gece 1.65 (eşik 3.0)
- F · metin-dışı: kenar · güçlü saç teli · card-2  → gündüz 1.26 · gece 1.48 (eşik 3.0)
- F · metin-dışı: kenar · .t-go/.pillc.g/.ck.ok çip iç kenarı kendi dolgusunda  → gündüz 1.65 · gece 1.94 (eşik 3.0)
- F · metin-dışı: kenar · .t-rv/.ck.man çip iç kenarı kendi dolgusunda  → gündüz 1.71 · gece 1.99 (eşik 3.0)
- F · metin-dışı: kenar · .t-no/.s-rb çip iç kenarı kendi dolgusunda  → gündüz 1.73 · gece 1.92 (eşik 3.0)
- F · metin-dışı: kenar · .pd-warn kenarı kendi dolgusunda  → gündüz 1.87 · gece 2.22 (eşik 3.0)
- F · metin-dışı: kenar · .slabel kenarı (ink-h-soft) tint üstünde  → gündüz 1.50 · gece 1.58 (eşik 3.0)
- F · metin-dışı: kenar · .t-vi/.lv.on kenarı (ink-h) tint üstünde  → gündüz 2.05 · gece 2.12 (eşik 3.0)
- F · metin-dışı: kenar · .pm-cell.thin kehribar iç kenarı (pozitif hücre)  → gündüz 1.75 · gece 2.06 (eşik 3.0)
- F · metin-dışı: kenar · nav alt kenarı (line-2) sayfa üstünde  → gündüz 1.47 · gece 1.83 (eşik 3.0)
- G · durum grafikleri · .spine.calm::before damga (green-stamp) sayfa üstünde  → gündüz 2.52 · gece 3.25 (eşik 3.0)
- G · durum grafikleri · .pm-cell.pos hücre zemini ↔ nötr hücre (işaret kodlaması)  → gündüz 1.12 · gece 1.15 (eşik 3.0)
- G · durum grafikleri · .pm-cell.neg hücre zemini ↔ nötr hücre (işaret kodlaması)  → gündüz 1.12 · gece 1.12 (eşik 3.0)
- H · ölçüm grafikleri · .bar rayı (bg2) ↔ kart zemini  → gündüz 1.04 · gece 1.03 (eşik 3.0)
- H · ölçüm grafikleri · .bar ray kenarı (line) ↔ ray  → gündüz 1.22 · gece 1.30 (eşik 3.0)
- H · ölçüm grafikleri · --raise ölçer rayı ↔ kart (DESIGN.md beyanlı)  → gündüz 1.09 · gece 1.27 (eşik 3.0)
- H · ölçüm grafikleri · .pm-conf güven rayı (line) ↔ pozitif hücre  → gündüz 1.14 · gece 1.23 (eşik 3.0)
- H · ölçüm grafikleri · grafik ızgarası (line-2) ↔ kart zemini  → gündüz 1.35 · gece 1.65 (eşik 3.0)
- H · ölçüm grafikleri · IC trendi: sıfır ekseni (line) ↔ kart zemini  → gündüz 1.17 · gece 1.27 (eşik 3.0)
- I · odak halkası · modal kart ↔ perdeyle karartılmış sayfa (.kbd-panel ↔ .kbd-ov)  → gündüz 2.68 · gece 1.23 (eşik 3.0)
- I · odak halkası · modal kart ↔ perdeyle karartılmış KART zemini  → gündüz 2.89 · gece 1.20 (eşik 3.0)
- H · ölçüm grafikleri · yoğunluk merdiveni: bant1 (card-2) ↔ kart zemini  → gündüz 1.07 · gece 1.11 (eşik 3.0)
- H · ölçüm grafikleri · yoğunluk merdiveni: bant1 (card-2) ↔ bant2 (band-2)  → gündüz 2.46 · gece 2.45 (eşik 3.0)
- H · ölçüm grafikleri · yoğunluk merdiveni: bant2 (band-2) ↔ bant3 (tx2)  → gündüz 2.49 · gece 2.46 (eşik 3.0)
- H · ölçüm grafikleri · bullet ölçüm çubuğu (accent) ↔ en koyu bant (tx2)  → gündüz 2.72 · gece 1.52 (eşik 3.0)
- H · ölçüm grafikleri · IC trendi: `gerçek` (accent) ↔ `sim` (violet)  → gündüz 1.85 · gece 1.42 (eşik 3.0)
- H · ölçüm grafikleri · IC trendi: `sim` (violet) ↔ `havuz` (tx3)  → gündüz 1.90 · gece 1.42 (eşik 3.0)
- H · ölçüm grafikleri · IC trendi: `gerçek` (accent) ↔ `havuz` (tx3)  → gündüz 3.52 · gece 2.02 (eşik 3.0)
- J · kapsama ısı-matrisi (P9) · kapsama bandı 1 ↔ kart zemini  → gündüz 1.14 · gece 1.14 (eşik 3.0)
- J · kapsama ısı-matrisi (P9) · kapsama bandı 2 ↔ bandı 1  → gündüz 1.20 · gece 1.23 (eşik 3.0)
- J · kapsama ısı-matrisi (P9) · kapsama bandı 3 ↔ bandı 2  → gündüz 1.25 · gece 1.28 (eşik 3.0)
- J · kapsama ısı-matrisi (P9) · kapsama bandı 4 ↔ bandı 3  → gündüz 1.20 · gece 1.21 (eşik 3.0)
- J · kapsama ısı-matrisi (P9) · kapsama bandı 4 ↔ kart zemini (uç-uca menzil)  → gündüz 2.05 · gece 2.18 (eşik 3.0)
- J · kapsama ısı-matrisi (P9) · sapma: eksi kutbu (güçlü) ↔ kart zemini  → gündüz 1.41 · gece 1.50 (eşik 3.0)
- J · kapsama ısı-matrisi (P9) · sapma: artı kutbu (güçlü) ↔ kart zemini  → gündüz 1.31 · gece 1.57 (eşik 3.0)
- J · kapsama ısı-matrisi (P9) · sapma: eksi kutbu (zayıf) ↔ kart zemini  → gündüz 1.16 · gece 1.19 (eşik 3.0)
- J · kapsama ısı-matrisi (P9) · sapma: artı kutbu (zayıf) ↔ kart zemini  → gündüz 1.13 · gece 1.21 (eşik 3.0)
- J · kapsama ısı-matrisi (P9) · sapma: eksi kutbu ↔ artı kutbu (kutuplar arası)  → gündüz 1.07 · gece 1.05 (eşik 3.0)

Her satır §6 (bilinçli istisna), §5 (beyansız bulgu) ya da §11 (P9 turunun beyanı)
altında karşılığını bulur; hiçbiri sınıflandırılmadan bırakılmadı.

## 5 · Beyansız bulgular (bu turun asıl çıktısı)

Aşağıdaki altı kalem, DESIGN.md'nin beyanlı sapma listesinde **yok** ve bugüne kadar
ölçülmemişti. **B1 ve B6 2026-08-02'de KAPANDI** (§11); metinleri tarihsel kayıt olarak
duruyor ve her birinin altında hükmü yazılı — bulguyu silmek, düzeltmenin gerekçesini de
silerdi.

### B1 · Yoğunluk merdiveninin son iki basamağı AYNI RENK — ✅ ÇÖZÜLDÜ (2026-08-02)

`app.js`'in bullet grafiğindeki nitel aralık merdiveni beş basamak olarak yazılmış:
`--card-2 → --line → --line-2 → --tx3 → --tx2`. Ama `--tx3`, iki temada da `--tx2`'nin
bire-bir kopyasıdır (`#585450` / `#b0a9a0`), yani **4. ve 5. bant arasındaki oran 1.00**.
Üstelik ilk üç basamak da birbirinden ayrılmıyor (1.09 ve 1.15 gündüz). Fiilen ayırt
edilebilen tek geçiş `--line-2 → --tx3` (5.10 gündüz / 4.08 gece). **Beş bantlı bir
skala olarak tarif edilen şey, ekranda iki tonlu bir skaladır.** Few'nun nitel aralık
fikri (kötü/kabul/iyi) burada okunmuyor.

**HÜKÜM (2026-08-02).** İki ayrı kusur vardı ve ikisi de kapandı. (a) `--tx3` artık
`--tx2`'nin kopyası değil, gerçek bir üçüncü mürekkep basamağı (kart üstünde 5.06 · adım
1.30 · AA korundu). (b) Merdivenin kendisi beş banttan **üçe** indi — Few'nun ideali — ve
orta basamak kendi jetonunu (`--band-2`) aldı: adımlar **2.46 / 2.49** (gündüz) ve
**2.45 / 2.46** (gece), uç-uca menzil 6.11 / 6.04. Ölçülmüş sınır: tek-hue bir merdivenin
toplam menzili `--card-2 ↔ --tx2` ile sınırlıdır (~6.1:1), yani üç bandın adımı en fazla
√6.1 ≈ 2.47 olabilir — 3:1'e çıkmak dördüncü bir yüzey tonu icat etmeyi gerektirir ve o,
merdiveni değil paleti değiştirir. **Beş bant iddiası kaldırıldı; kalan iddia ölçülüyor.**

### B2 · Bullet ölçüm çubuğu gece en koyu bandın üstünde kayboluyor — AÇIK

Ölçüm çubuğu `--accent`; gece `--accent` = `#d4d0cb` ve en koyu nitel bant `--tx2` =
`#b0a9a0`. Oran **1.52** (gündüz 2.72 — o da eşiğin altında). Bileşenin tek üstünlüğü
"ölçüm ile hedef bandını tek satırda karşılaştırmak" olduğuna göre, ölçümün bandın
üstünde okunamaması bileşeni işlevsiz bırakır. Bu bir estetik sapma değil, bir **okuma
arızası**.

### B3 · Bayatlık solmasının 2. ve 3. kademesi metin eşiğinin altında — AÇIK

`.bayat-1/-2/-3` sırasıyla `opacity: .78 / .58 / .42`. Sayfa zemininde ölçüldü:
**4.27 / 2.74 / 2.00** (gündüz), **5.06 / 3.39 / 2.38** (gece). Kural kaynakta
"sayının KENDİSİ hiçbir kademede değişmez ve gizlenmez" diyor — ama 3. kademede sayı
2.00:1'de duruyor, yani fiilen gizleniyor. Bayatlık **niceliği** taşımayan bir sinyal
olarak tasarlandığına göre, sinyali okunamazlığa kadar götürmesi gerekmiyor.

### B4 · `.sitem .sub` ve `.pm-none` — `opacity:.7` AA'yı gündüzde deviriyor — AÇIK

Kenar rayındaki canlı alt-okuma (`3.57`) ve matrisin "hiç ekilmemiş" hücre metni
(`3.47`) gündüz temasında AA altında. İkisi de `--tx2` üzerine `opacity:.7`. Gece
temasında sınırın hemen altında (4.32 / 4.11) — yani sorun tek temaya özgü değil.

### B5 · Matris hücre tinti tek başına işaret taşımıyor

`.pm-cell.pos` / `.neg` zeminleri nötr hücreye karşı **1.13** ve **1.12**. Bu bir
**arıza değil**, ama raporun bunu söylemesi gerekiyor: kâr/zarar işareti hücre
zemininden okunamaz. Second-Channel Rule zaten işareti (`+`/`−`) ve rakam rengini
(5.93 / 5.86) zorunlu kılıyor, yani bilgi kaybolmuyor. Kayıt için: **hücre tinti
dekoratiftir, kodlama değildir** — ve o hâlde bir gün "tint yeter" diye kısaltılamaz.

### B6 · IC-trend grafiğinin iki serisi AYNI RENK, ve efsane bunu söylemiyor — ✅ ÇÖZÜLDÜ (2026-08-02)

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

**HÜKÜM (2026-08-02).** Üç seri artık bir **luminans merdiveni**: `gerçek` (--accent) →
`sim` (--violet) → `havuz` (--tx3), kart üstünde 17.80 → 9.60 → 5.06. Seri-seri oranlar
**1.85 / 1.90 / 3.52** (gündüz) ve **1.42 / 1.42 / 2.02** (gece). Hue EKLENMEDİ ve bu bir
kısıt değil bir karar: hue farkı, renk körü bir okuyucunun ayıramadığı tam olarak o şeydir
— ayrım luminansla ve kesik-çizgi deseniyle taşınır. Ö8 de uygulandı: **efsane artık her
serinin çizgi ÖRNEĞİNİ gösteriyor** (düz · `1 3` · `2 2`), yani grafikte ayırt edilen şey
efsanede aynı desenle adlandırılıyor. Gece temasındaki 1.42'lik adımlar 3:1 değildir ve
öyle olamaz (accent↔card gece yalnız 10.18:1, üçe bölününce adım başına ~2.2 tavanı) —
ikinci kanal bu yüzden desendir, ve desen artık iki yerde birden okunur.

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
| İ7 | `.sessizhat .sh-sep` ayırıcı (`opacity:.45`) | 2.08 / 2.54 | Ayırıcı **noktalama**dır, bilgi değil; kaldırılsa cümle aynı okunur. |
| **İ8** | **ÖLÇEK basamakları** (P9 kapsama rampası 4 bant · sapma kutupları 4 · nitel bant merdiveni 2 adım · IC serileri 3 çift) | 1.05–2.49 / 1.05–2.46 | **Bir skala 3:1 adımlarla kurulamaz.** Dört basamaklı sequential bir rampanın uç-uca menzili 2.05:1'dir (gündüz); 3:1 adım istemek dört basamağın ikisini silmek demektir — yani skalayı yok ederek "erişilebilir" kılmak. 1.4.11 "bileşeni ya da durumu TANITAN bilgi" ister ve o bilgi burada **hücrenin rakamıdır**: her hücre oranını (%NN) ve sapmasını (işaretli, ±NN p) YAZAR. Dolgu tarama yardımıdır — gözün "nerede delik var" sorusunu tek bakışta sorabilmesi için. Rakamın kendisi her bantta AA geçer (en dar: gece, en koyu kapsama bandı **4.68**). Ayrıca sapma kutupları renk körlüğüne karşı **mavi ↔ toprak** ekseninde seçildi (protan/deutan kırmızı-yeşili siler, mavi-sarıyı korur) ve kutuplar arası luminans farkı 1.07 olduğu için işaret **kelimeyle/rakamla** taşınır, renkle değil. |

## 7 · Değişiklik önerileri

**ÖNERİ — UYGULANMADI (2026-08-01).** Aşağıdakilerin hiçbiri S1-T2 turunda uygulanmadı ve
hiçbiri tek başına uygulanamazdı: her biri bir jeton ya da bir kural değeri değiştirir, ve
WP0 kararına göre jeton yeniden-değerlemesi (gündüz beyazı dahil) kendi onay turunu ve kendi
ölçümünü hak ediyordu. Sıralama, **operatöre maliyeti** değil, **operatörün kaybettiği
bilgiyi** ölçer.

**2026-08-02 · O TUR GELDİ.** Operatör onaylı WP-P/P9 turunda **Ö1 ve Ö8 uygulandı**, ve
"gündüz beyazı hakkında" başlığı altındaki soru da kapatıldı (§11). Aşağıdaki tablo tarihsel
kayıttır; uygulanan satırlar ✅ ile işaretlidir. Ö2 · Ö3 · Ö4 · Ö5 **AÇIK KALDI** ve gerekçesi
kapsamdır: dördü de bir KURAL değeri (opaklık çarpanı, çizim satırı) değiştirir, jeton
değil — bu tur jeton turuydu ve iki ayrı kusur sınıfını tek commit'e koymak, kırılma hâlinde
hangisinin kırdığını ölçülemez kılardı.

| # | Kalan | Öneri | Neden bu | Bedeli |
|---|---|---|---|---|
| ✅ Ö1 | B1 — merdivenin 4./5. basamağı aynı renk | Merdiveni **dört** basamağa indir (`--card-2 → --line-2 → --tx3` + ölçüm çubuğu) ya da `--tx3`'ü gerçek bir ara tona ayır. | Beş bant iddiası ölçülemiyor; olmayan bir basamağı listede tutmak "yapılmış iş" izlenimi verir. | `--tx3` 7 yerde kullanılıyor; ayrıştırmak yeni bir renk jetonu demek. |
| Ö2 | B2 — bullet çubuğu gece kayboluyor | Ölçüm çubuğunu `--accent` yerine **zemin polaritesine göre** seç (gece: `--bg`/`--card` tonunda ters çubuk) ya da çubuğa 1px `--bg` kontur ver. | Bileşenin tek işi karşılaştırma; okunmayan çubuk bileşeni işlevsiz bırakır. | `_bullet` çiziminde tek satır; jeton değişikliği gerekmez → **en ucuz kalem, ilk sırada değerlendirilmeli.** |
| Ö3 | B3 — `.bayat-2/-3` | Opaklık kademelerini `.78/.58/.42` yerine `.85/.72/.60` yap (gündüzde ≈4.9/4.0/3.3) **ya da** solmayı metinden alıp satırın **sol kenar çizgisine** taşı. | Sayının kendisi hiçbir kademede gizlenmemeli — kuralın kendi yazdığı şey bu. | Üç sınıf tek satır; eşikler `app.js bayatSinif`'ta, dokunulmaz. |
| Ö4 | B4 — `opacity:.7` iki yerde | Opaklığı kaldır, sönüklüğü zaten var olan `--tx2` taşısın. | Aynı sönüklüğü iki mekanizmayla (jeton + opaklık) üretmek, ikisini de ölçülemez yapar. | İki kural; görsel fark küçük. |
| ✅ Ö8 | B6 — IC-trend efsanesi | Efsanede rengi bırak, **çizgi örneğini** göster (3 küçük SVG: düz / `1 3` / `2 2`). `--violet`'i `--accent`'e eşit tutmak sorun değil — sorun onu bir AYIRT EDİCİ gibi kullanmak. | Renk ile ayrılmayan bir şeyi renkle etiketlemek, efsaneyi süse çevirir. | Efsane satırı `app.js`'te; jeton değişikliği gerekmez. |
| Ö5 | İ3 — `--ink-h-soft` %18 | `.slabel` kenarını kaldır ve çipi yalnız `--accent-tint` dolgusuyla tanıt. | %18'lik bir kenar zaten görülmüyor; **çizmemek**, görünmeyeni çizmekten dürüst. | Tek kural. |
| Ö6 | İ5 — gece perdesi | Değişiklik önerilmiyor. Onun yerine **beyanı arayüze taşı**: modal açıkken arkadaki içerik `inert` (zaten öyle) ve bu davranış belgeye bağlansın. | Luminans mekanizmasının gece **yeri yok**; sayıyı büyütmek sahte bir çözüm olur. | — |
| Ö7 | İ1/İ2/İ4 saç telleri ve ton basamakları | Değişiklik önerilmiyor. | Sistemin kimliği bu. Üstelik `--field` çıpası, 1.4.11'in gerçekten bağladığı tek yeri (form kenarı) **zaten** 3.12–3.93 ile kapatıyor. | — |

**Gündüz beyazı hakkında (WP0 borç #5) — 2026-08-01 hükmü.** Bu denetim, `--bg:#ffffff` /
`--raise:#ffffff` sorununun bir **kontrast** sorunu olmadığını doğruluyor: gündüz temasında
AA'yı deviren altı çiftin hiçbiri saf beyazdan gelmiyor, hepsi opaklıktan geliyor. Saf
beyazın davası parlama ve yüzey merdiveninin sığlığıdır (`bg→bg2` 1.043) — ikisi de bu
raporun ölçtüğü şey değil. **Kontrast verisi, gündüz beyazını değiştirmek için bir gerekçe
üretmiyor.**

**2026-08-02 EKİ.** Bu hüküm hâlâ geçerli ve P9 turu onu ÇÜRÜTMEDİ: beyaz, kontrast
gerekçesiyle değil **parlama** gerekçesiyle kalktı (P6 kalemi, operatör onaylı). Turun
kontrast tarafındaki tek etkisi, bütün gündüz oranlarının aynı katsayıyla ~%5 inmesidir ve
**hiçbir çift hüküm değiştirmedi** (§11.2). Yani ölçüm bu kez değişikliğin gerekçesi değil,
**kapısı** oldu: katsayının ne kadar derine gidebileceğini `--red`in payı belirledi.

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
| --tx | --bg | gunduz | 19.42 | 4.5 |
| --tx | --bg | gece | 11.31 | 4.5 |
| --tx | --card | gunduz | 17.80 | 4.5 |
| --tx | --card | gece | 10.18 | 4.5 |
| --tx | --card-2 + --red-t | gunduz | 14.27 | 4.5 |
| --tx | --card-2 + --red-t | gece | 7.64 | 4.5 |
| --tx2 | --bg | gunduz | 7.15 | 4.5 |
| --tx2 | --bg | gece | 7.46 | 4.5 |
| --tx2 | --card | gunduz | 6.55 | 4.5 |
| --tx2 | --card | gece | 6.72 | 4.5 |
| --tx2 | --card-2 + --red-t | gunduz | 5.25 | 4.5 |
| --tx2 | --card-2 + --red-t | gece | 5.04 | 4.5 |
| --tx2 | --card-2 + --amber-t | gunduz | 5.26 | 4.5 |
| --tx2 | --card-2 + --amber-t | gece | 4.96 | 4.5 |
| --tx3 | --card | gunduz | 5.06 | 4.5 |
| --tx3 | --card | gece | 5.05 | 4.5 |
| --tx3 | --card-2 | gunduz | 4.72 | 4.5 |
| --tx3 | --card-2 | gece | 4.54 | 4.5 |
| --violet | --card | gunduz | 9.60 | 4.5 |
| --violet | --card | gece | 7.15 | 4.5 |
| --accent-2 | --accent-tint | gunduz | 17.57 | 4.5 |
| --accent-2 | --accent-tint | gece | 10.94 | 4.5 |
| --green | --card-2 + --green-t | gunduz | 4.72 | 4.5 |
| --green | --card-2 + --green-t | gece | 5.31 | 4.5 |
| --amber | --card-2 + --amber-t | gunduz | 5.57 | 4.5 |
| --amber | --card-2 + --amber-t | gece | 5.39 | 4.5 |
| --red | --card-2 + --red-t | gunduz | 4.59 | 4.5 |
| --red | --card-2 + --red-t | gece | 5.01 | 4.5 |
| --green | --bg | gunduz | 6.37 | 4.5 |
| --green | --bg | gece | 7.83 | 4.5 |
| --amber | --bg | gunduz | 7.57 | 4.5 |
| --amber | --bg | gece | 8.11 | 4.5 |
| --red | --bg | gunduz | 6.24 | 4.5 |
| --red | --bg | gece | 7.41 | 4.5 |
| --red | --bg + --nav-bg | gunduz | 6.24 | 4.5 |
| --red | --bg + --nav-bg | gece | 7.41 | 4.5 |
| --field | --card-2 | gunduz | 3.14 | 3.0 |
| --field | --card-2 | gece | 3.18 | 3.0 |
| --field | --bg | gunduz | 3.67 | 3.0 |
| --field | --bg | gece | 3.93 | 3.0 |
| --line | --card-2 | gunduz | 1.09 | 3.0 |
| --line | --card-2 | gece | 1.14 | 3.0 |
| --line-2 | --bg | gunduz | 1.47 | 3.0 |
| --line-2 | --bg | gece | 1.83 | 3.0 |
| --accent | --card | gunduz | 17.80 | 3.0 |
| --accent | --card | gece | 10.18 | 3.0 |
| --accent | --card-2 + --red-t | gunduz | 14.27 | 3.0 |
| --accent | --card-2 + --red-t | gece | 7.64 | 3.0 |
| --green-h | --card + --green-t | gunduz | 1.65 | 3.0 |
| --green-h | --card + --green-t | gece | 1.94 | 3.0 |
| --ink-h | --accent-tint | gunduz | 2.05 | 3.0 |
| --ink-h | --accent-tint | gece | 2.12 | 3.0 |
| --green-stamp | --bg | gunduz | 2.52 | 3.0 |
| --green-stamp | --bg | gece | 3.25 | 3.0 |
| --card-2 | --band-2 | gunduz | 2.46 | 3.0 |
| --card-2 | --band-2 | gece | 2.45 | 3.0 |
| --band-2 | --tx2 | gunduz | 2.49 | 3.0 |
| --band-2 | --tx2 | gece | 2.46 | 3.0 |
| --accent | --violet | gunduz | 1.85 | 3.0 |
| --accent | --violet | gece | 1.42 | 3.0 |
| --violet | --tx3 | gunduz | 1.90 | 4.5 |
| --violet | --tx3 | gece | 1.42 | 4.5 |
| --kap-4 | --card | gunduz | 2.05 | 3.0 |
| --kap-4 | --card | gece | 2.18 | 3.0 |
| --tx | --card + --kap-4 | gunduz | 8.70 | 4.5 |
| --tx | --card + --kap-4 | gece | 4.68 | 4.5 |
| --dv-n2 | --card | gunduz | 1.41 | 3.0 |
| --dv-n2 | --card | gece | 1.50 | 3.0 |
| --dv-p2 | --card | gunduz | 1.31 | 3.0 |
| --dv-p2 | --card | gece | 1.57 | 3.0 |
| --card | --bg + --scrim | gunduz | 2.68 | 3.0 |
| --card | --bg + --scrim | gece | 1.23 | 3.0 |
<!-- CIVI-TABLOSU-SONU -->

---

## 10 · S2R-3 (cila) eki — 2026-08-02

> **TARİHSEL KAYIT.** Bu ek, S2R-3 turunun (aynı gün, daha erken) hükmünü taşır ve o turda
> hiçbir jeton kımıldamadığını doğru olarak söyler. AYNI GÜN İÇİNDE, WP-P/P9 turunda jetonlar
> DEĞİŞTİ (§11): aşağıdaki rakamlar S2R-3 anındaki paletindir ve **§3'ün bugünkü hâliyle
> karşılaştırılmamalıdır**; yürürlükteki ölçüm her zaman §3 ve §9'dur. Jeton sayımı da değişti:
> 95 → **113** (23 temel + 2×45 renk).

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

---

## 11 · WP-P/P9 jeton turu eki — 2026-08-02 (DEĞER DEĞİŞTİ)

**Bu bölüm bir istisnadır:** §10'a kadarki her ek "hiçbir jeton kımıldamadı" diye başlıyor.
Bu tur kımıldattı — operatör onaylı, üç kalem: gündüz beyazı (P6 borcu), B1 merdiven-çöküşü,
B6 iki-seri-aynı-renk. Bu yüzden **§3'ün tamamı yeniden üretildi** ve §2 sayımı, §4 kalan
listesi, §9 çivi tablosu birlikte güncellendi. Hiçbiri elle yazılmadı: 136 çiftin her biri
raporun kendi L1/L2 hex'lerinden (mürekkep, zemin-yığını) ikilisine geri çözüldü, yeni
paletle yeniden hesaplandı ve tabloya öyle basıldı. Çözülemeyen çift **0**.

### 11.1 · Ne değişti, neden, ve neyin kapısına dayandı

**(a) Gündüz beyazı — DOKUZ yüzey birlikte indi.** `--bg` ve `--raise` saf `#ffffff` idi;
`index.html`in gece bloğu 2026-08-01'de bunu "AÇIK KALAN, BEYANLI" diye yazmış ve şunu
söylemişti: *"--bg'yi sıcak kırık-beyaza indirmek bu adımı çökertir; merdiveni korumak için
DÖRT yüzey jetonunun birden yeniden değerlenmesi gerekir."* Ölçüldü, doğruydu, ve dört değil
dokuz çıktı.

Yöntem: `bg2 · card · card-2 · slip · accent-tint · line · line-2 · field` jetonlarının
`(L+0.05)` değeri **tek bir katsayıyla (0.9523)** ölçeklendi. `(L+0.05)` uzayında sabit bir
çarpan, o katmanlar arasındaki her kontrast oranını **birebir korur** — merdiven adımları
bu yüzden kımıldamadı:

| adım | önce | sonra |
|---|---|---|
| `bg → bg2` | 1.0431 | **1.0472** |
| `bg2 → card` | 1.0412 | **1.0414** |
| `card → card-2` | 1.0799 | **1.0724** |
| `card → raise` | 1.0861 | **1.0906** |

`--bg` (ve onunla birebir aynı olan `--raise`) `#fbf9f8`e oturdu: luminans 1.0000 → **0.9504**
(%5 aşağı) ve **sıcak** — `lin(r) − lin(b) = 0.026`, yani ramp'in kendi sıcaklık yönünü
sürdürüyor (bg2 0.026 · card 0.051 · card-2 0.073). Gündüz temasında artık **sıfır saf beyaz**
var. `--nav-bg` de aynı rengin %82'sine döndü (`rgba(251,249,248,.82)`); sabit kalsaydı üst bar
sayfadan daha parlak bir şerit olurdu.

**KATSAYININ KAPISI ÖLÇÜLDÜ VE PARA RENGİDİR.** Mürekkepler (`--tx`, `--tx2`, `--accent`…) ve
para renkleri (`--green`, `--amber`, `--red`) bu turda **kımıldamadı**; onlar sabit kalınca
zemin indikçe oranları da iner. Bağlayıcı kısıt `--red`in en kötü gerçek zeminidir (kendi %10
tinti, gömülü panelde): **4.78 → 4.59**, eşik 4.5, kalan pay **0.09**. Katsayıyı 0.9523'ün
altına indirmek o çifti AA'nın altına düşürür — yani **daha derin bir kırık-beyaz, para
renklerinin de yeniden değerlenmesini şart koşar** ve o kendi turudur (üç renk + üç tint +
dört saç teli + damga = on bir jeton, ve bu raporun tamamı bir kez daha). Bu turda
yapılmadı: bir tasarım kararını, ölçülmemiş bir ikinci karara yaslamak.

**(b) B1 — `--tx3` ve nitel bant merdiveni.** İki ayrı kusurdu. `--tx3` iki temada da
`--tx2`'nin bire-bir kopyasıydı (oran 1.00) — artık gerçek bir üçüncü basamak (kart üstünde
**5.06**, `--tx2`'ye adım **1.30**, AA korundu). Merdiven ise beş banttan **üçe** indi ve orta
basamak kendi jetonunu (`--band-2`) aldı; `--tx3` merdivende artık KULLANILMIYOR. Buradaki asıl
bulgu ilk denetimin göremediği bir şeydi: `_bullet`in `bantlar` varsayılanı üç, çağrıların
çoğu **iki** bant istiyor — yani ekranda fiilen çizilen bantlar listenin İLK ikisiydi
(`--card-2` ve `--line`, adım **1.09**). Yani B1'in raporladığı "son iki basamak aynı" kusuru
gerçekti ama ekrandaki kusur daha kötüydü: **görünen adım en baştaki adımdı ve o da yoktu.**
Yeni merdivende iki bant istendiğinde adım **2.46**'dır.

**(c) B6 — ikinci seriye ayrık jeton.** `--violet` `--accent`in kopyasıydı. Üç seri artık bir
luminans merdiveni (17.80 → 9.60 → 5.06, kart üstünde) ve efsane her serinin **çizgi örneğini**
gösteriyor (Ö8). Hue eklenmedi — gerekçesi §5/B6'nın altında.

**(d) P9 · dokuz yeni jeton.** `--band-2` (yukarıda) · `--kap-1..4` (tek-hue sequential kapsama
rampası) · `--dv-n2/n1/p1/p2` (CVD-güvenli diverging sapma skalası). Dokuzu da **iki temaya
birden** girdi — `--nav-bg` arızasının kapısı olan kural (§Ç2) her koşumda bunu ölçüyor.
Rampanın tavan alfası (.30) ölçülmüş bir sınırdır: `.34`te hücrenin rakamı gece temasında
**4.45**'e, AA altına düşüyordu; `.30`da **4.68**.

### 11.2 · Değişen çiftler (önce → sonra)

Aşağıdaki tabloda **116 çift** var ve hiçbiri hüküm değiştirmedi: geçen geçti, kalan kaldı.
Değişmeyen 10 çift, iki ucu da gece jetonu olan ya da iki ucu da mürekkep olan çiftlerdir.

| çift | gündüz önce→sonra | gece önce→sonra | eşik | hüküm |
|---|---|---|---|---|
| `--tx` — body · sayfa gövdesi | 20.38 → **19.42** | 11.31 → **11.31** | 4.5 | geçti |
| `--tx` — kbd · girdi · .ksgroup düğmesi · .pm-strip · .pane | 19.54 → **18.54** | 10.45 → **10.45** | 4.5 | geçti |
| `--tx` — .card/.hero/.gate-card/.kbd-panel/.ksgroup/.gloss içi | 18.76 → **17.80** | 10.18 → **10.18** | 4.5 | geçti |
| `--tx` — .sitem:hover · .rowbtn:hover · .mcard:hover · .hyp:hover | 17.38 → **16.60** | 9.15 → **9.15** | 4.5 | geçti |
| `--tx` — .rowbtn.sel · .sitem.tema:hover · palet seçili satır | 18.37 → **17.57** | 9.02 → **9.02** | 4.5 | geçti |
| `--tx` — .spine.attn .msg | 17.43 → **16.70** | 9.48 → **9.48** | 4.5 | geçti |
| `--tx` — .spine.act .msg | 17.27 → **16.56** | 9.60 → **9.60** | 4.5 | geçti |
| `--tx` — kart içi kehribar çip metni | 16.12 → **15.28** | 8.45 → **8.45** | 4.5 | geçti |
| `--tx` — en kötü gerçek bileşik | 14.86 → **14.27** | 7.64 → **7.64** | 4.5 | geçti |
| `--tx2` — .subline · .sessizhat · .hint · footer | 7.50 → **7.15** | 7.46 → **7.46** | 4.5 | geçti |
| `--tx2` — .mono · .pd-* çekmece etiketleri · .pane | 7.19 → **6.83** | 6.89 → **6.89** | 4.5 | geçti |
| `--tx2` — .statuspill · .hudchip · .bl-lab · .bl-ax · .gc.arrow · kart etiketleri | 6.91 → **6.55** | 6.72 → **6.72** | 4.5 | geçti |
| `--tx2` — .sitem:hover .sub · hover satırları | 6.40 → **6.11** | 6.04 → **6.04** | 4.5 | geçti |
| `--tx2` — .slabel komşu metin · seçili satır alt-okuma | 6.76 → **6.47** | 5.95 → **5.95** | 4.5 | geçti |
| `--tx2` — yeşil çip içi ikincil | 5.96 → **5.69** | 5.62 → **5.62** | 4.5 | geçti |
| `--tx2` — kehribar çip içi ikincil | 5.93 → **5.62** | 5.58 → **5.58** | 4.5 | geçti |
| `--tx2` — kırmızı çip içi ikincil | 5.88 → **5.61** | 5.66 → **5.66** | 4.5 | geçti |
| `--tx2` — en kötü gerçek bileşik (DESIGN.md hükmü) | 5.47 → **5.25** | 5.04 → **5.04** | 4.5 | geçti |
| `--tx2` — kehribar çip / gömülü panel | 5.52 → **5.26** | 4.96 → **4.96** | 4.5 | geçti |
| `--tx2` — .pm-n pozitif hücrede | 6.66 → **6.37** | 6.51 → **6.51** | 4.5 | geçti |
| `--tx2` — .pm-n negatif hücrede | 6.71 → **6.39** | 6.68 → **6.68** | 4.5 | geçti |
| `--tx2` — .statuspill üst barda (kart opak, bar altta) | 7.50 → **7.15** | 7.46 → **7.46** | 4.5 | geçti |
| `--slip-ink` — .term::after ipucu (slip-ink) | 17.38 → **16.60** | 9.15 → **9.15** | 4.5 | geçti |
| `--tx2@0.7` — .sitem .sub (opacity .7) rayda | 3.57 → **3.45** | 4.32 → **4.32** | 4.5 | KALDI |
| `--tx2@0.7` — .pm-none (opacity .7) ekilmemiş hücrede | 3.47 → **3.38** | 4.11 → **4.11** | 4.5 | KALDI |
| `--tx2@0.45` — .sessizhat .sh-sep (opacity .45) | 2.11 → **2.08** | 2.54 → **2.54** | 3.0 | KALDI |
| `--tx2@0.78` — .bayat-1 (opacity .78) sayfa zemininde | 4.27 → **4.17** | 5.06 → **5.06** | 4.5 | gündüz KALDI · gece geçti |
| `--tx2@0.58` — .bayat-2 (opacity .58) sayfa zemininde | 2.74 → **2.70** | 3.39 → **3.39** | 4.5 | KALDI |
| `--tx2@0.42` — .bayat-3 (opacity .42) sayfa zemininde | 2.00 → **1.97** | 2.38 → **2.38** | 4.5 | KALDI |
| `--tx2@0.42` — .bayat-3 (opacity .42) kart üstünde | 1.96 → **1.93** | 2.33 → **2.33** | 4.5 | KALDI |
| `--accent-2` — .slabel · .t-vi · .lv.on · code · .dlbtn:hover | 18.37 → **17.57** | 10.94 → **10.94** | 4.5 | geçti |
| `--accent-2` — .card .t · .sitem.on .sub · .regrow.live .nm | 18.76 → **17.80** | 12.35 → **12.35** | 4.5 | geçti |
| `--accent-2` — .pd-l · .mono .k · .pane içi anahtar | 19.54 → **18.54** | 12.67 → **12.67** | 4.5 | geçti |
| `--accent-2` — .spine.calm hover · sayfa zemininde bağ | 20.38 → **19.42** | 13.71 → **13.71** | 4.5 | geçti |
| `--accent-2` — .spine.attn .items button:hover | 17.43 → **16.70** | 11.49 → **11.49** | 4.5 | geçti |
| `--accent-2` — .spine.act .items button:hover | 17.27 → **16.56** | 11.64 → **11.64** | 4.5 | geçti |
| `--accent` — .gloss summary · .kbd-panel h3.t · .hstat .l | 18.76 → **17.80** | 10.18 → **10.18** | 4.5 | geçti |
| `--accent` — .spine .items button:hover::after | 20.38 → **19.42** | 11.31 → **11.31** | 4.5 | geçti |
| `--green` — çip: kendi tinti sayfa zemininde | 5.75 → **5.50** | 6.61 → **6.61** | 4.5 | geçti |
| `--green` — çip: kendi tinti çekmece/pano zemininde (.pd-warn · .mono) | 5.54 → **5.25** | 6.08 → **6.08** | 4.5 | geçti |
| `--green` — çip: kendi tinti kart üstünde (.t-go/.t-rv/.t-no · .ck.*) | 5.31 → **5.07** | 5.90 → **5.90** | 4.5 | geçti |
| `--green` — çip: kendi tinti gömülü panelde — EN KÖTÜ GERÇEK ZEMİN | 4.94 → **4.72** | 5.31 → **5.31** | 4.5 | geçti |
| `--green` — çıplak: .pos/.neg/.warn sayfa zemininde | 6.69 → **6.37** | 7.83 → **7.83** | 4.5 | geçti |
| `--green` — çıplak: .mono .ok/.w/.no · .ksgroup düğme hover | 6.41 → **6.08** | 7.24 → **7.24** | 4.5 | geçti |
| `--green` — çıplak: .hudchip.explore · .gate-msg · .sh-sap · palet rozeti | 6.16 → **5.84** | 7.06 → **7.06** | 4.5 | geçti |
| `--green` — çıplak: hover satırında para rengi | 5.70 → **5.45** | 6.34 → **6.34** | 4.5 | geçti |
| `--amber` — çip: kendi tinti sayfa zemininde | 6.80 → **6.51** | 6.79 → **6.79** | 4.5 | geçti |
| `--amber` — çip: kendi tinti çekmece/pano zemininde (.pd-warn · .mono) | 6.51 → **6.22** | 6.25 → **6.25** | 4.5 | geçti |
| `--amber` — çip: kendi tinti kart üstünde (.t-go/.t-rv/.t-no · .ck.*) | 6.29 → **5.96** | 6.06 → **6.06** | 4.5 | geçti |
| `--amber` — çip: kendi tinti gömülü panelde — EN KÖTÜ GERÇEK ZEMİN | 5.85 → **5.57** | 5.39 → **5.39** | 4.5 | geçti |
| `--amber` — çıplak: .pos/.neg/.warn sayfa zemininde | 7.95 → **7.57** | 8.11 → **8.11** | 4.5 | geçti |
| `--amber` — çıplak: .mono .ok/.w/.no · .ksgroup düğme hover | 7.62 → **7.23** | 7.49 → **7.49** | 4.5 | geçti |
| `--amber` — çıplak: .hudchip.explore · .gate-msg · .sh-sap · palet rozeti | 7.32 → **6.94** | 7.30 → **7.30** | 4.5 | geçti |
| `--amber` — çıplak: hover satırında para rengi | 6.78 → **6.47** | 6.56 → **6.56** | 4.5 | geçti |
| `--red` — çip: kendi tinti sayfa zemininde | 5.55 → **5.32** | 6.29 → **6.29** | 4.5 | geçti |
| `--red` — çip: kendi tinti çekmece/pano zemininde (.pd-warn · .mono) | 5.36 → **5.07** | 5.74 → **5.74** | 4.5 | geçti |
| `--red` — çip: kendi tinti kart üstünde (.t-go/.t-rv/.t-no · .ck.*) | 5.13 → **4.90** | 5.62 → **5.62** | 4.5 | geçti |
| `--red` — çip: kendi tinti gömülü panelde — EN KÖTÜ GERÇEK ZEMİN | 4.78 → **4.59** | 5.01 → **5.01** | 4.5 | geçti |
| `--red` — çıplak: .pos/.neg/.warn sayfa zemininde | 6.55 → **6.24** | 7.41 → **7.41** | 4.5 | geçti |
| `--red` — çıplak: .mono .ok/.w/.no · .ksgroup düğme hover | 6.28 → **5.96** | 6.85 → **6.85** | 4.5 | geçti |
| `--red` — çıplak: .hudchip.explore · .gate-msg · .sh-sap · palet rozeti | 6.03 → **5.72** | 6.68 → **6.68** | 4.5 | geçti |
| `--red` — çıplak: hover satırında para rengi | 5.59 → **5.34** | 6.00 → **6.00** | 4.5 | geçti |
| `--green` — .pm-cell.pos .pm-yield (hücre kendi tintinde) | 5.93 → **5.68** | 6.84 → **6.84** | 4.5 | geçti |
| `--red` — .pm-cell.neg .pm-yield (hücre kendi tintinde) | 5.86 → **5.58** | 6.63 → **6.63** | 4.5 | geçti |
| `--amber` — .pm-thin ekim-az kazığı (kehribar tint + pozitif hücre) | 6.05 → **5.84** | 5.86 → **5.86** | 4.5 | geçti |
| `--amber` — .pm-thin ekim-az kazığı (kehribar tint + negatif hücre) | 6.10 → **5.83** | 6.03 → **6.03** | 4.5 | geçti |
| `--red` — HALT/KRİZ etiketi üst barda (bar sayfa üstünde) | 6.55 → **6.24** | 7.41 → **7.41** | 4.5 | geçti |
| `--red` — HALT/KRİZ etiketi üst barda (bar kart üstünde kayarken) | 6.38 → **6.08** | 7.18 → **7.18** | 4.5 | geçti |
| `--red` — .kscover:hover (kırmızı tint üst barda) | 5.55 → **5.32** | 6.29 → **6.29** | 4.5 | geçti |
| `--bg2` — .gate-btn · .pillc · .dlbtn.primary · birincil eylem | 19.54 → **18.54** | 10.45 → **10.45** | 4.5 | geçti |
| `--bg2` — .dlbtn.primary:hover · .skip (içeriğe atla) | 19.54 → **18.54** | 12.67 → **12.67** | 4.5 | geçti |
| `--bg2` — .halt:hover · .kscover[aria-expanded=true] | 6.28 → **5.96** | 6.85 → **6.85** | 4.5 | geçti |
| `--line` — varsayılan saç teli · bg | 1.28 → **1.27** | 1.40 → **1.40** | 3.0 | KALDI |
| `--line` — varsayılan saç teli · card | 1.18 → **1.17** | 1.27 → **1.27** | 3.0 | KALDI |
| `--line-2` — güçlü saç teli · card | 1.36 → **1.35** | 1.65 → **1.65** | 3.0 | KALDI |
| `--line-2` — güçlü saç teli · card-2 | 1.25 → **1.26** | 1.48 → **1.48** | 3.0 | KALDI |
| `--field` — form kontrolü kenarı (metin girişi/select) · bg | 3.65 → **3.67** | 3.93 → **3.93** | 3.0 | geçti |
| `--field` — form kontrolü kenarı (metin girişi/select) · bg2 | 3.50 → **3.51** | 3.63 → **3.63** | 3.0 | geçti |
| `--field` — form kontrolü kenarı (metin girişi/select) · card | 3.36 → **3.37** | 3.54 → **3.54** | 3.0 | geçti |
| `--field` — form kontrolü kenarı (metin girişi/select) · card-2 | 3.12 → **3.14** | 3.18 → **3.18** | 3.0 | geçti |
| `--green-h` — .t-go/.pillc.g/.ck.ok çip iç kenarı kendi dolgusunda | 1.68 → **1.65** | 1.94 → **1.94** | 3.0 | KALDI |
| `--amber-h` — .t-rv/.ck.man çip iç kenarı kendi dolgusunda | 1.72 → **1.71** | 1.99 → **1.99** | 3.0 | KALDI |
| `--red-h` — .t-no/.s-rb çip iç kenarı kendi dolgusunda | 1.75 → **1.73** | 1.92 → **1.92** | 3.0 | KALDI |
| `--amber-h2` — .pd-warn kenarı kendi dolgusunda | 1.89 → **1.87** | 2.22 → **2.22** | 3.0 | KALDI |
| `--ink-h-soft` — .slabel kenarı (ink-h-soft) tint üstünde | 1.51 → **1.50** | 1.58 → **1.58** | 3.0 | KALDI |
| `--amber-h` — .pm-cell.thin kehribar iç kenarı (pozitif hücre) | 1.76 → **1.75** | 2.06 → **2.06** | 3.0 | KALDI |
| `--green` — .dot sağlıklı (yeşil) üst barda | 6.69 → **6.37** | 7.83 → **7.83** | 3.0 | geçti |
| `--amber` — .dot.stale (kehribar) üst barda | 7.95 → **7.57** | 8.11 → **8.11** | 3.0 | geçti |
| `--red` — .dot.halt (kırmızı) üst barda | 6.55 → **6.24** | 7.41 → **7.41** | 3.0 | geçti |
| `--green` — .hudchip .ld yeşil (çip zemini kart) | 6.16 → **5.84** | 7.06 → **7.06** | 3.0 | geçti |
| `--amber` — .hudchip .ld.warn kehribar | 7.32 → **6.94** | 7.30 → **7.30** | 3.0 | geçti |
| `--red` — .hudchip .ld.bad kırmızı | 6.03 → **5.72** | 6.68 → **6.68** | 3.0 | geçti |
| `--tx2` — .hudchip .ld.off (tx2) | 6.91 → **6.55** | 6.72 → **6.72** | 3.0 | geçti |
| `--green` — .spine::before damga (yeşil) kart üstünde | 6.16 → **5.84** | 7.06 → **7.06** | 3.0 | geçti |
| `--green-stamp` — .spine.calm::before damga (green-stamp) sayfa üstünde | 2.56 → **2.52** | 3.25 → **3.25** | 3.0 | gündüz KALDI · gece geçti |
| `--amber` — .spine.attn::before damga kendi bandında | 6.80 → **6.51** | 6.79 → **6.79** | 3.0 | geçti |
| `--red` — .spine.act::before damga kendi bandında | 5.55 → **5.32** | 6.29 → **6.29** | 3.0 | geçti |
| `--accent` — .sitem::before etkin görünüm işareti (3px) | 20.38 → **19.42** | 11.31 → **11.31** | 3.0 | geçti |
| `--amber@0.7` — body.explore-mode::after keşif çerçevesi (2px, opacity .7) | 3.77 → **3.66** | 4.60 → **4.60** | 3.0 | geçti |
| `--pm-pos` — .pm-cell.pos hücre zemini ↔ nötr hücre (işaret kodlaması) | 1.13 → **1.12** | 1.15 → **1.15** | 3.0 | KALDI |
| `--accent` — .bar dolgusu (accent) ↔ ray (bg2) | 19.54 → **18.54** | 10.45 → **10.45** | 3.0 | geçti |
| `--accent` — .thermo tüp dolgusu (accent) ↔ tüp (bg2) | 19.54 → **18.54** | 10.45 → **10.45** | 3.0 | geçti |
| `--line` — .pm-conf güven rayı (line) ↔ pozitif hücre | 1.13 → **1.14** | 1.23 → **1.23** | 3.0 | KALDI |
| `--green@0.85` — .pm-conf dolgusu (yeşil @.85) ↔ güven rayı | 3.99 → **3.86** | 4.49 → **4.49** | 3.0 | geçti |
| `--red@0.85` — .pm-conf dolgusu (kırmızı @.85) ↔ güven rayı | 4.15 → **4.01** | 4.26 → **4.26** | 3.0 | geçti |
| `--accent` — equity çizgisi (accent) ↔ kart zemini | 18.76 → **17.80** | 10.18 → **10.18** | 3.0 | geçti |
| `--tx2` — sparkline/eksen (tx2) ↔ kart zemini | 6.91 → **6.55** | 6.72 → **6.72** | 3.0 | geçti |
| `--line-2` — grafik ızgarası (line-2) ↔ kart zemini | 1.36 → **1.35** | 1.65 → **1.65** | 3.0 | KALDI |
| `--line` — IC trendi: sıfır ekseni (line) ↔ kart zemini | 1.18 → **1.17** | 1.27 → **1.27** | 3.0 | KALDI |
| `--accent` — :focus-visible 2px --accent · sayfa zemininde | 20.38 → **19.42** | 11.31 → **11.31** | 3.0 | geçti |
| `--accent` — :focus-visible 2px --accent · kart üstünde | 18.76 → **17.80** | 10.18 → **10.18** | 3.0 | geçti |
| `--accent` — :focus-visible 2px --accent · gömülü panelde | 17.38 → **16.60** | 9.15 → **9.15** | 3.0 | geçti |
| `--accent` — :focus-visible 2px --accent · seçili satırda | 18.37 → **17.57** | 9.02 → **9.02** | 3.0 | geçti |
| `--accent` — :focus-visible 2px --accent · kırmızı çip üstünde | 15.97 → **15.25** | 8.57 → **8.57** | 3.0 | geçti |
| `--card` — modal kart ↔ perdeyle karartılmış sayfa (.kbd-panel ↔ .kbd-ov) | 2.72 → **2.68** | 1.23 → **1.23** | 3.0 | KALDI |
| `--card` — modal kart ↔ perdeyle karartılmış KART zemini | 2.93 → **2.89** | 1.20 → **1.20** | 3.0 | KALDI |

**Merdiven/seri satırları yeniden yazıldı** (eski etiketleri artık ekranda karşılığı yok):
`bant1↔bant2 (line)`, `bant2↔bant3`, `bant3↔bant4`, `bant4↔bant5 — AYNI RENK` ve
`IC: gerçek↔sim — AYNI RENK` satırları düştü; yerlerine üç bantlı merdivenin iki adımı ve
üç serinin üç çifti geldi (§3-H). **14 satır da yeni** (§3-J, ısı-matrisi).

### 11.3 · Ölçülmeyen ve bu ekin kapsamadığı şey

- **Ekranda görülmedi.** Yerel sunucu YASAK (CLAUDE.md §5); bu turun tamamı kaynak-çivili
  ölçümdür. %5'lik bir yüzey inişinin *hissi* ancak operatörün ekranında doğrulanır — rapor
  yalnız oranların korunduğunu ve hiçbir çiftin hüküm değiştirmediğini söyleyebilir.
- **Parlama ölçülmedi, luminans ölçüldü.** "Halation/parlama azaldı" bir psikofizik iddiadır;
  bu raporun söyleyebileceği şey, sayfanın en büyük yüzeyinin luminansının %5 indiği ve mavi
  kanalın ramp'in sıcaklık yönüne çekildiğidir. Fazlasını iddia etmek uydurma olurdu.
- **Renk körlüğü simülasyonu yapılmadı.** Sapma kutuplarının seçimi *literatür gerekçelidir*
  (mavi-sarı ekseni protan/deutan'da korunur), simülasyonla doğrulanmış değildir. Program X'in
  ayrı kalemi olmayı sürdürüyor.

