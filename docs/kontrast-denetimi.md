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
| İ6 | `.spine.calm::before` sakin damgası | 1.95 / 1.99 (mint zemin, 2026-08-24) · ~~2.56 / 3.25~~ | Sağlıklı durum **bilerek sönüktür** (iş emri Ç2, karanlık kokpit). Damganın yanında aynı şeyi söyleyen tam bir cümle var; damga tek taşıyıcı değil. **2026-08-24: sayı DÜŞTÜ ve sebebi beyanlıdır** — `.spine.calm` artık `--mint` yüzeyinde duruyor (karar §10.5), yani damga ile zemini aynı hue ailesinden. İstisnanın gerekçesi değişmedi (sakin sönüktür); değişen zeminin adı. |
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
<!-- 2026-08-24 · DUB DÖNÜŞÜMÜ: bu gövdenin TAMAMI yeniden üretildi.
     Üreten: research/olcumler/dub_donusumu_2026-08-24/olc.py (çıktı: civi_tablosu.md).
     Elle yazılmış tek bir oran yoktur; tests/test_tasarim_token_v153.py her satırı
     KAYNAKTAN yeniden hesaplar ve ayrışırsa raporu BAYAT ilan eder.
     ~~Önceki gövde (WP-P/P9 + D1, 2026-08-02/07, 66 satır) sıcak-kemik dünyaya aitti
     ve emekli edildi; sayıları §11'in metninde okunabilir durumda kalıyor.~~

     2026-08-24 · ÖE1 TAŞIYICI TURU (karar §10.2/§10.3/§10.5) — gövde İKİNCİ kez
     yeniden üretildi ve TABLONUN YAPISI DEĞİŞTİ, çünkü ölçülen şey değişti:
       · Şiddet üçlüsünün satırları artık İKİ AYRI SORU soruyor. `--green/--amber/--red`
         satırları bir İŞARETİN kontrastıdır ve eşiği metin-dışı **3.0**'dır; aynı çipin
         YAZISI `--tx` satırlarındadır ve eşiği hâlâ **4.5**'tir. Eşik gevşemedi —
         ~~"--green | --card-2 + --green-t | 4.5"~~ satırı yanlış SORUYU soruyordu.
       · ROL 5 serisi (`--sapphire/--blue/--sky`) + tek-seri `--blue` ÇG2 ile ölçülür (≥3.0).
       2026-08-24: üçlü maketin hue ailesine geçti; `--violet`/`--violet2` adları DÜŞTÜ
       (değerleri lavender/sky'nin birebir kopyasıydı).
         ~~"--accent | --violet" ve "--violet | --tx3" satırları emekli~~: o ikisi
         akromatik merdivenin komşu-adım oranıydı; renkli merdivende ayrımı ΔL* ölçer
         (ÇG1, §12.9) ve kontrast oranı o soruyu cevaplamaz.
       · `--mint` (soft-mint) satırları eklendi: yüzey metin taşımaz ama ÜSTÜNE metin
         düşer, ve karar §10.5 onun da ölçülmesini istedi. -->
| mürekkep | zemin yığını | tema | oran | eşik |
|---|---|---|---|---|
| --tx | --bg | gunduz | 18.97 | 4.5 |
| --tx | --bg | gece | 14.23 | 4.5 |
| --tx | --card | gunduz | 19.80 | 4.5 |
| --tx | --card | gece | 12.01 | 4.5 |
| --tx | --card-2 + --red-t | gunduz | 15.80 | 4.5 |
| --tx | --card-2 + --red-t | gece | 9.16 | 4.5 |
| --tx2 | --bg | gunduz | 7.49 | 4.5 |
| --tx2 | --bg | gece | 12.09 | 4.5 |
| --tx2 | --card | gunduz | 7.81 | 4.5 |
| --tx2 | --card | gece | 10.21 | 4.5 |
| --tx2 | --card-2 + --red-t | gunduz | 6.24 | 4.5 |
| --tx2 | --card-2 + --red-t | gece | 7.79 | 4.5 |
| --tx2 | --card-2 + --amber-t | gunduz | 6.52 | 4.5 |
| --tx2 | --card-2 + --amber-t | gece | 8.20 | 4.5 |
| --tx3 | --card | gunduz | 4.74 | 4.5 |
| --tx3 | --card | gece | 6.00 | 4.5 |
| --tx3 | --card-2 | gunduz | 4.54 | 4.5 |
| --tx3 | --card-2 | gece | 5.38 | 4.5 |
| --accent-2 | --accent-tint | gunduz | 16.44 | 4.5 |
| --accent-2 | --accent-tint | gece | 12.46 | 4.5 |
| --tx | --card-2 + --green-t | gunduz | 16.80 | 4.5 |
| --tx | --card-2 + --green-t | gece | 9.79 | 4.5 |
| --tx | --card-2 + --amber-t | gunduz | 16.51 | 4.5 |
| --tx | --card-2 + --amber-t | gece | 9.65 | 4.5 |
| --green | --card-2 + --green-t | gunduz | 3.28 | 3.0 |
| --green | --card-2 + --green-t | gece | 3.15 | 3.0 |
| --amber | --card-2 + --amber-t | gunduz | 4.14 | 3.0 |
| --amber | --card-2 + --amber-t | gece | 3.89 | 3.0 |
| --red | --card-2 + --red-t | gunduz | 4.99 | 3.0 |
| --red | --card-2 + --red-t | gece | 4.69 | 3.0 |
| --green | --card | gunduz | 3.87 | 3.0 |
| --green | --card | gece | 3.87 | 3.0 |
| --amber | --card | gunduz | 4.96 | 3.0 |
| --amber | --card | gece | 4.84 | 3.0 |
| --red | --card | gunduz | 6.25 | 3.0 |
| --red | --card | gece | 6.15 | 3.0 |
| --green | --bg | gunduz | 3.70 | 3.0 |
| --green | --bg | gece | 4.58 | 3.0 |
| --amber | --bg | gunduz | 4.75 | 3.0 |
| --amber | --bg | gece | 5.73 | 3.0 |
| --red | --bg | gunduz | 5.99 | 3.0 |
| --red | --bg | gece | 7.28 | 3.0 |
| --red | --bg + --nav-bg | gunduz | 5.99 | 3.0 |
| --red | --bg + --nav-bg | gece | 7.28 | 3.0 |
| --tx | --bg + --nav-bg | gunduz | 18.97 | 4.5 |
| --tx | --bg + --nav-bg | gece | 14.23 | 4.5 |
| --bg2 | --red | gunduz | 5.74 | 4.5 |
| --bg2 | --red | gece | 6.69 | 4.5 |
| --tx | --mint | gunduz | 18.03 | 4.5 |
| --tx | --mint | gece | 10.63 | 4.5 |
| --tx2 | --mint | gunduz | 7.11 | 4.5 |
| --tx2 | --mint | gece | 9.04 | 4.5 |
| --green | --mint | gunduz | 3.52 | 3.0 |
| --green | --mint | gece | 3.42 | 3.0 |
| --green-stamp | --mint | gunduz | 1.95 | 3.0 |
| --green-stamp | --mint | gece | 1.99 | 3.0 |
| --blue | --card | gunduz | 5.67 | 3.0 |
| --blue | --card | gece | 7.85 | 3.0 |
| --blue | --bg2 | gunduz | 5.20 | 3.0 |
| --blue | --bg2 | gece | 8.56 | 3.0 |
| --sapphire | --card | gunduz | 10.02 | 3.0 |
| --sapphire | --card | gece | 12.13 | 3.0 |
| --sapphire | --bg2 | gunduz | 9.19 | 3.0 |
| --sapphire | --bg2 | gece | 13.21 | 3.0 |
| --sky | --card | gunduz | 3.31 | 3.0 |
| --sky | --card | gece | 4.78 | 3.0 |
| --sky | --bg2 | gunduz | 3.04 | 3.0 |
| --sky | --bg2 | gece | 5.21 | 3.0 |
| --field | --card-2 | gunduz | 4.54 | 3.0 |
| --field | --card-2 | gece | 5.38 | 3.0 |
| --field | --bg | gunduz | 4.54 | 3.0 |
| --field | --bg | gece | 7.11 | 3.0 |
| --line | --card-2 | gunduz | 1.21 | 3.0 |
| --line | --card-2 | gece | 1.31 | 3.0 |
| --line-2 | --bg | gunduz | 1.42 | 3.0 |
| --line-2 | --bg | gece | 2.29 | 3.0 |
| --accent | --card | gunduz | 19.80 | 3.0 |
| --accent | --card | gece | 12.01 | 3.0 |
| --accent | --card-2 + --red-t | gunduz | 15.80 | 3.0 |
| --accent | --card-2 + --red-t | gece | 9.16 | 3.0 |
| --green-h | --card + --green-t | gunduz | 1.51 | 3.0 |
| --green-h | --card + --green-t | gece | 1.52 | 3.0 |
| --ink-h | --accent-tint | gunduz | 2.03 | 3.0 |
| --ink-h | --accent-tint | gece | 2.33 | 3.0 |
| --green-stamp | --bg | gunduz | 2.03 | 3.0 |
| --green-stamp | --bg | gece | 2.20 | 3.0 |
| --card-2 | --band-2 | gunduz | 2.42 | 3.0 |
| --card-2 | --band-2 | gece | 2.86 | 3.0 |
| --band-2 | --tx2 | gunduz | 3.10 | 3.0 |
| --band-2 | --tx2 | gece | 3.20 | 3.0 |
| --kap-4 | --card | gunduz | 2.03 | 3.0 |
| --kap-4 | --card | gece | 2.37 | 3.0 |
| --tx | --card + --kap-4 | gunduz | 9.76 | 4.5 |
| --tx | --card + --kap-4 | gece | 5.07 | 4.5 |
| --dv-n2 | --card | gunduz | 1.41 | 3.0 |
| --dv-n2 | --card | gece | 1.76 | 3.0 |
| --dv-p2 | --card | gunduz | 1.42 | 3.0 |
| --dv-p2 | --card | gece | 1.75 | 3.0 |
| --card | --bg + --scrim | gunduz | 3.00 | 3.0 |
| --card | --bg + --scrim | gece | 1.28 | 3.0 |
| --nav | --bg | gunduz | 4.95 | 3.0 |
| --nav | --bg | gece | 7.11 | 3.0 |
| --nav | --card | gunduz | 5.17 | 3.0 |
| --nav | --card | gece | 6.00 | 3.0 |
| --nav-2 | --nav-t | gunduz | 7.15 | 4.5 |
| --nav-2 | --nav-t | gece | 8.87 | 4.5 |
| --nav | --nav-t | gunduz | 4.24 | 4.5 |
| --nav | --nav-t | gece | 5.78 | 4.5 |
| --nav-h | --nav-t | gunduz | 1.59 | 3.0 |
| --nav-h | --nav-t | gece | 1.91 | 3.0 |
| --bg2 | --nav | gunduz | 4.74 | 4.5 |
| --bg2 | --nav | gece | 6.54 | 4.5 |
| --tx | --nav-t | gunduz | 16.24 | 4.5 |
| --tx | --nav-t | gece | 11.57 | 4.5 |
| --tx | --nav-t + --nav-h | gunduz | 10.24 | 4.5 |
| --tx | --nav-t + --nav-h | gece | 6.05 | 4.5 |
| --tx2 | --nav-t | gunduz | 6.41 | 4.5 |
| --tx2 | --nav-t | gece | 9.83 | 4.5 |
| --tx3 | --nav-t | gunduz | 3.89 | 4.5 |
| --tx3 | --nav-t | gece | 5.78 | 4.5 |
| --sh-ring | --bg | gunduz | 1.24 | 3.0 |
| --sh-ring | --bg | gece | 1.28 | 3.0 |
| --sh-ring | --card | gunduz | 1.25 | 3.0 |
| --sh-ring | --card | gece | 1.31 | 3.0 |
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

---

## 12 · Dub dönüşümü — jeton katmanı (KARAR-2026-08-24-B) · 2026-08-24

_Bu bölüm §11'i (WP-P/P9 sıcak-kemik turu) SİLMEZ; hükmünü emekli eder ve yerine geçer._
_§11'in sayıları tarih olarak okunabilir kalır ve o değerler artık yürürlükte DEĞİLDİR._

**Ölçüm ve üretici:** `research/olcumler/dub_donusumu_2026-08-24/olc.py` → `sonuc.json` +
`RAPOR.md` + `civi_tablosu.md`. §9 çivi tablosunun TAMAMI o betiğin çıktısıdır; elle
yazılmış tek bir oran yoktur ve `tests/test_tasarim_token_v153.py` her satırı KAYNAKTAN
yeniden hesaplar. **Kaynak:** Dub'ın kendi DTCG dışa aktarımı (`~/Downloads/tokens.json`) —
değerler hatırlanmadı, dosyadan okundu.

### 12.1 · Dub'da karanlık tema YOK — doğrulandı

Karar §1.2'nin iddiası ölçüldü: dört Dub dosyası, ikinci bir renk katmanını AÇAN mekanizma
için tarandı (`prefers-color-scheme`, `[data-theme`, `.dark`, `color-scheme:dark`).

| dosya | karanlık-tema mekanizması |
|---|---|
| `tokens.json` | YOK |
| `DESIGN.md` | YOK |
| `variables.css` | YOK |
| `theme.css` | YOK |

Bu yüzden gece paleti **türetildi**. Türetme ters çevirme DEĞİLDİR: kroma taşıyan her jeton
kendi %10 tinti üzerinde AYRI ölçüldü ve gece para renkleri naif tersin vereceğinden
AÇIKTIR (tint-yönü kuralı). Gece yüzey rampası 8/255 ızgarasına oturur ve Dub'ın
`charcoal` (0x17) ile `graphite` (0x26) jetonları o ızgaraya çivi olarak girer.

### 12.2 · Ö1-Ö7 · eşikler ÖNCEDEN donduruldu (karar §4), sonuç

| Ö | ölçülen | eşik | hüküm |
|---|---|---|---|
| Ö1 · `#fafafa` parlama | en büyük yüzey Y=0.956 (saf beyaz 1.0) · kart/zemin adımı 1.0438 | Y<1.0 · adım ≥1.02 | **TUTTU** |
| Ö2 · para renkleri kendi %10 tinti üstünde | en düşük **4.503** (iki tema × üç renk × yedi gerçek zemin) | ≥4.5 | **TUTTU** |
| Ö3 · gezinme kroması | mürekkep C(--nav) 0.2152 / 0.1458 · dolgu C(--nav-t) 0.0328 / 0.072 · min C(şiddet) 0.0921 / 0.0809 | C(nav) < min C(şiddet) | **TUTMADI** — dolgu için **TUTTU** |
| Ö4 · `--nav` ↔ `--dv-n2` | 3.655 / 3.41 | ≥3.0 | **TUTTU** |
| Ö5 · wash üstünde mürekkep | `--nav` 4.239 / 5.778 · `--nav-2` 7.155 / 8.871 | ≥4.5 | **TUTMADI** — `--nav-2` için **TUTTU** |
| Ö6 · tip rampası | karar rampası [11, 14, 16, 20, 24, 30] → adımlar [1.2727, 1.1429, 1.25, 1.2, 1.25] | her adım ≥1.15, en az bir ≥1.25 | **TUTMADI** |
| Ö7 · odak halkası | `--sh-ring` 1.234-1.31 · 2px `--accent` ana hattı 10.78-19.798 | ≥3.0 | **TUTMADI** — ana hat için **TUTTU** |

Ö4'ün eşiği kararda NİTELdi ("ayırt edilebilir"). İşlemsel karşılık olarak deponun zaten
yürürlükteki metin-dışı ayrım ölçütü (WCAG 2.2 1.4.11, 3:1) alındı — yeni bir eşik icat
edilmedi, var olan uygulandı. Sonuç: ıraksayan negatif kutbun mor-toprağa taşınmasına
GEREK KALMADI (karar §2.1'in koşullu maddesi tetiklenmedi).

### 12.3 · Tutmayan DÖRT eşik — DEĞER ZORLANMADI, KULLANIM YÜZEYİ DARALDI

Karar §4'ün kuralı: *"Ölçülemeyen değer jetona GİRMEZ. Bir eşik tutmazsa çözüm §2.1'deki
gibi kullanım yüzeyini daraltmaktır, değeri zorlamak değil."* Dördü de öyle işlendi.

**Ö3 · gezinme kroması (mürekkep).** Elektrik mavisi doygundur: C=0,2152 > min C(şiddet)=0,1392
(gündüz). Jeton uydurulmadı, kroması düşürülmedi. **Daraltma:** gezinmenin BÜYÜK YÜZEYİ
washtır (`--nav-t`, C=0,0328 gündüz · 0,0874 gece) ve tavanın altındadır — dolgu için Ö3
TUTAR. `--nav`/`--nav-2` yalnız İNCE mürekkep taşır ve kaynakta iki okuyucusu vardır:
3px seçim çubuğu (`.sitem::before`) ve sayaç hapı dolgusu (`.pillc`). Bir para değeri, bir
alarm, bir yön ASLA mavi olmaz (karar §2.1) ve bu `tests/test_renk_rolleri_v197.py` §9'da
çivilidir — kroma tavanı da orada test edilir.

**Ö5 · wash üstünde mürekkep.** `--nav` (`electric-blue`) `--nav-t` üstünde **4.24** — AA ALTI.
**Daraltma** karar §2.1'in kendi cümlesidir (*"dolgu washı kalır, mürekkep koyulaşır"*):
washın üstündeki metin `--nav-2`dir (`deep-sapphire`; ölçüldü 7.15 gündüz · 8.95 gece).
`.sitem.on` bu yüzden `color:var(--nav-2)` okur, `var(--nav)` DEĞİL. Gecede `--nav` de eşiği
geçiyor (5.83) ama kural iki temada AYNI kalır: tek yüzey, tek gramer.

**Ö6 · tip rampası.** Karar §3'ün rampası [11, 14, 16, 20, 24, 30] → adımlar
[1.2727, 1.1429, 1.25, 1.2, 1.25]: **16/14 = 1.1429**, eşiğin (1.15) altında. **Daraltma:**
16px basamağı rampadan DÜŞER ve bedeli ölçüldü — SIFIR: `index.html`de 16px kullanımı zaten
yoktu. Kalan rampa [11, 14, 17, 20, 24, 30], adımlar [1.2727, 1.2143, 1.1765, 1.2, 1.25] —
**TUTTU**. Ayrıca 13px basamağı kaldırıldı (karar §3: *"14→15
oranı 1.07, hiyerarşi değil gürültü"*) ve `index.html`deki **28** kullanımı gövde basamağına
(14px) taşındı; 28px'in tek kullanımı (`.mcard .v`, büyük metrik rakamı) `--t-num` jetonuyla
30px'e çıktı.

**Ö7 · odak halkası.** Dub'ın `shadow-subtle-2`si (`rgba(0,0,0,.1) 0 0 0 4px`) her zeminde
**1.234-1.31** ölçtü — 3:1'in çok altında. Dub'ın alfası KIMILDATILMADI.
**Daraltma:** `--sh-ring` bir ODAK GÖSTERGESİ DEĞİLDİR, onu çevreleyen yardımcı halkadır.
G4'ü (odak her zeminde ≥3:1) taşıyan gösterge `:focus-visible` üzerindeki **2px `--accent`
ana hattı**dır ve o ölçüldü: **10.78-19.798** (iki tema, yedi gerçek zemin) — GEÇTİ.
Ayrım `tests/test_tasarim_token_v153.py::test_odak_halkasi_HER_ZEMINDE_3_1` ile çivilidir ve
o test `--accent`i ölçer, halkayı değil.

### 12.4 · ÖE1 · ŞİDDET MERDİVENİ ÇÖKTÜ — bulgu (jeton turu), hüküm (Rol-1 §9)

Karar §4 bir rolün ÜYELERİNİN ayrılabilirliğini sormuyordu. Ölçülmeyince görülmeyen şey
buydu: Dub `tangerine` (hue 41,1°) ile maketin `loss-red`i (38,4°) yalnız **2,7°** arayla
duruyor. Üye-üye AA türetmesi ikisini AYNI renge çökertiyordu — gündüz `#b54000` ↔
`#ba3a00`, gece `#ff8e63` ↔ `#ff8e6a`. Yani ŞİDDET-1 (P1, şimdi müdahale) ile ŞİDDET-2
(P2, insan gerekiyor) ekranda **tek renk** olacaktı. İkinci çökme: `tangerine` ile
`vivid-green` luminansta **1,004** ayrışıyordu, yani ayrım TAMAMEN protan/deutan'ın
sildiği eksende kalıyordu.

**Hiçbir mevcut test bunu görmezdi.** v197 rol AYRILIĞINI ölçer, v153 KONTRASTI ölçer;
ikisi de "iki seviye ayırt edilebiliyor mu" diye sormuyordu. Kör nokta buydu ve iki
rengin aynı olduğunu on iki saat görünmez kıldı.

Hükmü Rol-1 verdi (`docs/KARAR-2026-08-24-B-DUB-DONUSUMU.md` §9) ve eşikleri ölçümden
ÖNCE dondurdu (§9.3). Aşağısı o hükmün UYGULANMASIdır.

### 12.5 · ÖE1 · uygulanan çözüm — §9.4 geri çekilmesi

| ÖE1 | ölçü | eşik (§9.3, DONMUŞ) |
|---|---|---|
| a | komşu seviyelerin luminans oranı | ≥ 1.2 |
| b | komşu seviyelerin ΔE2000'i | ≥ 15.0 |
| c | her renk kendi %10 tinti üstünde (`--card`) | ≥ 4.5 |

**Önce kaynak üçlüler MERDİVENSİZ ölçüldü** — çünkü §9.4 "Omega üçlüsü yerinde kalır"
diyor ve bu ancak ölçülürse bir hüküm olur:

| üçlü (gündüz) | çift | luminans oranı | ΔE2000 |
|---|---|---|---|
| Dub ataması (ortak ΔL, merdiven YOK) | --sev-1 ↔ --sev-2 | 1.471 | 9.44 |
| Dub ataması (ortak ΔL, merdiven YOK) | --sev-2 ↔ --sev-3 | 1.004 | 55.73 |
| Omega üçlüsü AYNEN (#0c6a3b/#6e4a00/#b3242c) | --sev-1 ↔ --sev-2 | 1.213 | 29.37 |
| Omega üçlüsü AYNEN (#0c6a3b/#6e4a00/#b3242c) | --sev-2 ↔ --sev-3 | 1.188 | 32.38 |

**Omega üçlüsü bile, AYNEN alındığında ÖE1-a'yı tutmuyor** (gündüz 1,188 · gece 1,035 /
1,093). Yani hue ailesi hangisi olursa olsun üçlünün bir LUMİNANS MERDİVENİNE oturması
zorunlu — bu, hükmün ölçümle ortaya çıkan ikinci yarısıdır.

**Adaylar, karar §9'un kendi sırasıyla** (önce Dub içinde çöz, olmazsa §9.4):

| aday | tema | a (lum, iki komşu) | b (ΔE2000) | c | hüküm |
|---|---|---|---|---|---|
| A | gunduz | 1.251 / 1.253 | 5.39 / 54.18 | ✓ | **TUTMADI** |
| A | gece | 1.247 / 1.256 | 8.44 / 55.03 | ✓ | **TUTMADI** |
| B | gunduz | 1.242 / 1.253 | 13.53 / 54.18 | ✓ | **TUTMADI** |
| B | gece | 1.251 / 1.256 | 12.62 / 55.03 | ✓ | **TUTMADI** |
| C | gunduz | 1.255 / 1.247 | 28.47 / 32.43 | ✓ | **TUTTU** |
| C | gece | 1.247 / 1.255 | 22.75 / 30.1 | ✓ | **TUTTU** |

**SEÇİLEN: C · §9.4 geri çekilme · şiddet rolü Dub paletinden ÇIKAR, ölçülmüş Omega üçlüsünün hue/kroması kalır**

A ve B ÖE1-b'de düştü. B, `loss-red`in hue'sunu Meridian'ın ÖLÇÜLMÜŞ alarm hue'suna
(24,1° — Omega `--red`, bu depoda bir yıl yayında kalmış bir değer) çekti ve 17° ayrım
kazandı; yetmedi (ΔE2000 13,53 gündüz / 12,62 gece). Sebep yapısal ve ölçülebilir:
**Dub'ın paletinde şiddet için kullanılabilir ÜÇ ayrık hue yok.** `lavender` MOD'a,
`electric-blue` ve `deep-sapphire` ROL 6'ya kalıcı olarak ayrılmış durumda; geriye
`vivid-green` ve `tangerine` kalıyor, yani İKİ hue. Karar §9.4 bunu öngörmüştü —
*Dub bir pazarlama sitesidir ve üç seviyeli bir şiddet kanalı taşımaz* — ve ölçüm onu
doğruladı. **Şiddet rolü Dub paletinden ÇIKTI**; gezinme, yüzey, geometri, tipografi ve
yön rolleri Dub'da KALDI.

**Uygulanan merdiven:**

| tema | jeton | değer | kroma | komşu çift | luminans oranı | ΔE2000 | kendi tinti (`--card`) |
|---|---|---|---|---|---|---|---|
| gunduz | `--sev-1` (`--red`) | `#9a0019` | 0.1754 | --sev-1 ↔ --sev-2 | 1.255 | 28.47 | 7.272 |
| gunduz | `--sev-2` (`--amber`) | `#77520e` | 0.0917 | --sev-2 ↔ --sev-3 | 1.247 | 32.43 | 6.046 |
| gunduz | `--sev-3` (`--green`) | `#1f7646` | 0.1114 | — | — | — | 4.884 |
| gece | `--sev-1` (`--red`) | `#ffbab4` | 0.0815 | --sev-1 ↔ --sev-2 | 1.247 | 22.75 | 7.387 |
| gece | `--sev-2` (`--amber`) | `#d8b072` | 0.0917 | --sev-2 ↔ --sev-3 | 1.255 | 30.1 | 6.106 |
| gece | `--sev-3` (`--green`) | `#61b37f` | 0.1118 | — | — | — | 5.04 |

**MERDİVEN KURALI (yeni, beyanlı).** Şiddet arttıkça mürekkep zeminden UZAKLAŞIR —
tint-yönü kuralının şiddet hattındaki kardeşi: gündüz `--sev-1` en KOYU, gece en AÇIK;
nominal (`--sev-3`) zemine en yakın olandır (*renk yalnız anomalide* kuralının luminans
karşılığı). İnşa basamağı **1.25**, eşik 1.2 DEĞİL: 8-bit yuvarlama ve alfa bileşimi sıfır
paylı bir merdiveni eşiğin altına iter. Pay YALNIZ İNŞADADIR; ölçüm hâlâ 1,20'ye karşı
yapılır ve `tests/test_renk_rolleri_v197.py` §10 onu çiviler.

**BEDELİ BEYANLI — bu bir kazanç değil bir takas.** Gece `--sev-1` merdivenin en uzak
basamağındadır ve sRGB gamutu orada kroma tutmaz: **0,166 → 0,0809**. Alarm gecede daha
SOLUK bir mürekkeptir; ayrımını luminans ve hue taşır, doygunluk değil. Bu ayrıca Ö3'ün
DOLGU tavanını düşürdü ve gece gezinme washı o tavanın altına çekilerek yeniden türetildi
(`#172554` → `#1a274d`, C 0,0874 → 0,0720): eşik gevşetilmedi, TÜRETİLEBİLİR olan değer
kısıta uyduruldu.

**KÖR NOKTA KAPATILDI.** `tests/test_renk_rolleri_v197.py` §10 artık ÖE1-a + ÖE1-b'yi
komşu çiftler için İKİ temada ölçüyor, ÖE1-c'yi ayrıca çiviliyor (sıra bağlayıcı: a ve b
için c'den çalınamaz), merdivenin YÖNÜNÜ iki temada sınıyor ve eşiklerin karar §9.3'ten
oynamadığını belgeye karşı doğruluyor. ΔE2000 uygulamasının kendi çivisi de orada
(beyaz↔siyah = 100, aynı renk = 0, ve kusurun kendisi olan çift eşiğin ALTINDA).

### 12.6 · Türetilen jetonlar — hangi kural, kaç adım

| jeton | tema | kaynak | sonuç | ΔL adımı | kroma (kaynak) | kural |
|---|---|---|---|---|---|---|
| `--green` | gunduz | Dub vivid-green `#16a34a` | `#1f7646` | 0 | 0.1114 (0.1699) | ÖE1 MERDİVENİ (karar §9.3) · aday «C» · hue 154.4° kroma 0.1111 sabit, luminans basamağı 1.25; sev-3 AA sınırında, sev-1 iki basamak zeminden uzakta |
| `--amber` | gunduz | Dub tangerine `#ea580c` | `#77520e` | 0 | 0.0921 (0.1943) | ÖE1 MERDİVENİ (karar §9.3) · aday «C» · hue 76.9° kroma 0.0917 sabit, luminans basamağı 1.25; sev-3 AA sınırında, sev-1 iki basamak zeminden uzakta |
| `--red` | gunduz | maket beyanlı türetmesi loss-red (Dub'da kayıp rengi YOK) `#c2410c` | `#9a0019` | 0 | 0.175 (0.1739) | ÖE1 MERDİVENİ (karar §9.3) · aday «C» · hue 24.1° kroma 0.1782 sabit, luminans basamağı 1.25; sev-3 AA sınırında, sev-1 iki basamak zeminden uzakta |
| `--green` | gece | Dub vivid-green `#16a34a` | `#61b37f` | 0 | 0.1118 (0.1699) | ÖE1 MERDİVENİ (karar §9.3) · aday «C» · hue 154.4° kroma 0.1111 sabit, luminans basamağı 1.25; sev-3 AA sınırında, sev-1 iki basamak zeminden uzakta |
| `--amber` | gece | Dub tangerine `#ea580c` | `#d8b072` | 0 | 0.0922 (0.1943) | ÖE1 MERDİVENİ (karar §9.3) · aday «C» · hue 76.9° kroma 0.0917 sabit, luminans basamağı 1.25; sev-3 AA sınırında, sev-1 iki basamak zeminden uzakta |
| `--red` | gece | maket beyanlı türetmesi loss-red (Dub'da kayıp rengi YOK) `#c2410c` | `#ffbab4` | 0 | 0.0809 (0.1739) | ÖE1 MERDİVENİ (karar §9.3) · aday «C» · hue 24.1° kroma 0.1782 sabit, luminans basamağı 1.25; sev-3 AA sınırında, sev-1 iki basamak zeminden uzakta |
| `--yon-arti` | gunduz | --green (gunduz) `#1f7646` | `#4a6e56` | 0 | 0.0563 (0.1114) | C = min C(şiddet) x 0.6; ORTAK ΔL=0.000; AA>=4.5 kendi tinti + çıplak / #f5f5f5 |
| `--yon-eksi` | gunduz | --red (gunduz) `#9a0019` | `#6c4442` | 0 | 0.0559 (0.175) | C = min C(şiddet) x 0.6; ORTAK ΔL=0.000; AA>=4.5 kendi tinti + çıplak / #f5f5f5 |
| `--yon-arti` | gece | --green (gece) `#61b37f` | `#8bab94` | 9 | 0.0484 (0.1118) | C = min C(şiddet) x 0.6; ORTAK ΔL=0.009; AA>=4.5 kendi tinti + çıplak / #2e2e2e |
| `--yon-eksi` | gece | --red (gece) `#ffbab4` | `#edc3be` | 0 | 0.0487 (0.0809) | C = min C(şiddet) x 0.6; ORTAK ΔL=0.000; AA>=4.5 kendi tinti + çıplak / #2e2e2e |
| `--mod-canli` | gunduz | Dub lavender `#7c3aed` | `#7c3aed` *(Dub jetonu AYNEN)* | 0 | 0.2466 (0.2466) | AA>=4.5 kendi tinti + çıplak / #f5f5f5 |
| `--mod-kesif` | gunduz | --mod-canli (aynı hue, düşük kroma) `#7c3aed` | `#6c5e9e` | 16 | 0.0996 (0.2466) | C = C(mod-canli) x 0.4; AA>=4.5 kendi tinti + çıplak / #f5f5f5 |
| `--mod-canli` | gece | Dub lavender `#7c3aed` | `#ab91ff` | 184 | 0.157 (0.2466) | AA>=4.5 kendi tinti + çıplak / #2e2e2e |
| `--mod-kesif` | gece | --mod-canli (aynı hue, düşük kroma) `#ab91ff` | `#a79fcb` | 0 | 0.0637 (0.157) | C = C(mod-canli) x 0.4; AA>=4.5 kendi tinti + çıplak / #2e2e2e |
| `--nav-t` | gece | onaylanan maket (scratch-panov2) gece washı `#172554` | `#1a274d` | 0 | 0.072 (0.0874) | Ö3 DOLGU tavanı: C tohumda 0.0874 ≥ min C(şiddet) 0.0809; hue ve L sabit, kroma tavanın %90'ına indirildi |
| `--nav` | gece | Dub electric-blue `#2563eb` | `#72a2ff` | 172 | 0.1458 (0.2152) | AA>=4.5 gece washı #1a274d + çıplak/tint #2e2e2e |
| `--nav-2` | gece | Dub deep-sapphire `#1e40af` | `#b2caff` | 122 | 0.0791 (0.1809) | L = L(--nav gece) + 0.1217 (gündüzün nav↔nav-2 L farkı, yönü çevrilmiş); AA>=4.5 washı #1a274d + çıplak/tint #2e2e2e |
| `--field` | gunduz | Dub fog `#737373` | `#737373` *(Dub jetonu AYNEN)* | 0 | 0.0 (0.0) | rampadan SEÇİM: her gerçek yüzeyde >=3:1 tutan ilk basamak |
| `--field` | gece | Dub silver `#a3a3a3` | `#a3a3a3` *(Dub jetonu AYNEN)* | 0 | 0.0 (0.0) | rampadan SEÇİM: her gerçek yüzeyde >=3:1 tutan ilk basamak |
| `--band-2` | gunduz | Dub silver `#a3a3a3` | `#a3a3a3` *(Dub jetonu AYNEN)* | 0 | 0.0 (0.0) | rampadan SEÇİM: card-2->band-2 2.42 · band-2->tx2 3.10 |
| `--band-2` | gece | Dub fog `#737373` | `#737373` *(Dub jetonu AYNEN)* | 0 | 0.0 (0.0) | rampadan SEÇİM: card-2->band-2 2.86 · band-2->tx2 3.20 |
| `--violet` | gunduz | Dub slate `#404040` | `#404040` *(Dub jetonu AYNEN)* | 0 | 0.0 (0.0) | rampadan SEÇİM: accent->violet 1.91 · violet->tx3 2.19 (v171 kısıtı: ayrım ≥1.35, kart üstünde AA) |
| `--violet` | gece | TÜRETİLDİ — Dub nötr rampasında geçerli basamak YOK `#e5e5e5` | `#c2c2c2` | 0 | 0.0 (0.0) | accent↔tx3 merdiveninin GEOMETRİK ORTASI (eşit adım): accent->violet 1.41 · violet->tx3 1.42; akromatik |
| `--dv-n*` | gunduz | Dub deep-sapphire hue'su `#1e40af` | `#45526f` | 0 | 0.0509 (0.1809) | L=L(--tx2)=0.4386 · C = min C(şiddet) x 0.55; alfa .22/.10 DEĞİŞMEDİ |
| `--dv-p*` | gunduz | Dub tangerine hue'su `#ea580c` | `#6b493c` | 0 | 0.0513 (0.1943) | L=L(--tx2)=0.4386 · C = min C(şiddet) x 0.55; alfa .22/.10 DEĞİŞMEDİ |
| `--dv-n*` | gece | Dub deep-sapphire hue'su `#1e40af` | `#c6d4f2` | 0 | 0.0443 (0.1809) | L=L(--tx2)=0.8699 · C = min C(şiddet) x 0.55; alfa .22/.10 DEĞİŞMEDİ |
| `--dv-p*` | gece | Dub tangerine hue'su `#ea580c` | `#efcbbe` | 0 | 0.0446 (0.1943) | L=L(--tx2)=0.8699 · C = min C(şiddet) x 0.55; alfa .22/.10 DEĞİŞMEDİ |

**KIRPMA BEYANI.** OKLCh'de L kaydırılırken hue ve kroma sabit tutulur; sRGB gamut dışına
düşen bir bileşimde kroma o L'de gamut sınırına indirilir. Bu SESSİZ DEĞİLDİR: yukarıdaki
kroma sütunu hem gerçekleşen hem kaynak değeri taşır. En büyük kırpma gece kehribarında:
**0,1943 → 0,1054**. Gece `min C(şiddet)` odur ve Ö3'ün dolgu tavanı o sayıya karşı ölçülür —
yani kırpma bir kozmetik ayrıntı değil, bir EŞİĞİN girdisidir.

### 12.7 · Okuyucusuz jetonlar (YASA 6 kaydı — sayıldı, hüküm VERİLMEDİ)

"En kötü gerçek zemin" ölçülür, varsayılmaz: bir yüzey jetonunu hiçbir kural okumuyorsa o
bir zemin değildir ve türetmeyi gereksiz yere sıkar. Kaynaktan sayıldı
(`olc.py::_okuyucu_sayisi` — `index.html` kural gövdeleri + `app.js`):

Hesap gündüz `#f5f5f5`, gece `#2e2e2e` ile yapıldı. Okuyucusuz bulunan jetonlar:

- `--blue` · **0 okuyucu**
- `--elev` · **0 okuyucu**
- `--serif` · **0 okuyucu**
- `--violet2` · **0 okuyucu**

VAKA KAYDI (2026-08-24, aynı gün içinde iki kez ölçüldü): `--raise` sabah **0** okuyucuya
sahipti ve o yüzden "en kötü gerçek zemin" hesabından DÜŞMÜŞTÜ. Pano v2 bileşen kuralları
eklenince **19** okuyucuya çıktı (kart zemini) ve hesap kendiliğinden değişti — gece en kötü
zemin `#363636`e çıkıp gece kehribarının kroması 0,1054'ten 0,0829'a düştü, bu da Ö3'ün
DOLGU tavanını (`--nav-t` C 0,0874) altına aldı. Kök neden ölçüldü: gece `--raise` gündüzde
OLMAYAN bir basamak icat ediyordu (gündüz `--raise` = `--card` = `#ffffff`). Gece de eşitlendi
(`#262626`) ve zincir kapandı. **Ders:** "okuyucusuz" bir jeton kalıcı bir sıfat DEĞİLDİR;
bu yüzden sayı her koşumda kaynaktan yeniden üretilir, elle yazılmaz.

Bu 4 jeton ADIYLA duruyor çünkü jeton adları bu turda DEĞİŞMEZ (`app.js` DOM'u çalışma anında
üretir ve isim sözleşmesi bağlayıcıdır).

**HÜKÜM (Rol-1, 2026-08-24): BU TUR EMEKLİ EDİLMEZ — kalem `emeklilik adayı, tur
kapanışında ölçülecek` olarak açık kalır.** Gerekçe: dördü de uçuştaki `app.js` turunun
potansiyel tüketicisidir ve o tur henüz kapanmadı; şimdi kaldırmak, kapanmamış bir turu
kör noktadan kırar. Sayı her koşumda kaynaktan yeniden üretilir (`olc.py`), yani kalem
tur kapanışında elle değil ÖLÇÜMLE yeniden değerlenir.

### 12.8 · Ad borçları (jeton adı işini söylemiyor — hüküm Rol-1'de)

- **`--nav-h` FILL olarak da kullanılıyordu.** Ad bir SAÇ TELİ (hairline, %35 alfa)
  söylüyor, `.pv-gorev:hover` ise onu DOLGU olarak okuyordu. 2026-08-24'te düzeltildi:
  hover artık dolguyu `--nav-t` washında tutar ve geri bildirimi `--nav-h` SAÇ TELİYLE
  verir (`box-shadow:inset 0 0 0 1px`) — yani jeton işini yapıyor. Ölçüldü: gövde
  mürekkebi (`--tx`) saç telinin üstünde 10.24 (gündüz) / 6.05 (gece) — AA.
- **`--blue` akromatiktir** (`#0a0a0a` / `#e5e5e5`). Ad bir HUE söylüyor, değer
  akromatik bir seri basamağı. Adı değiştirmek `app.js`i kırar (isim sözleşmesi
  bağlayıcı) — kalem burada duruyor, hüküm tur kapanışında.


---

## 13 · ÖE1 TAŞIYICI DEĞİŞİMİ + RENKLİ SERİLER — 2026-08-24 (karar §10)

Bu bölüm karar `docs/KARAR-2026-08-24-B-DUB-DONUSUMU.md` §10'un ölçülmüş uygulamasıdır.
Sayıların üreticisi `research/olcumler/oe1_dub_dorduncu_2026-08-24/olc.py`nin renk
matematiğidir (`rgb2lab` / `lab2rgb` / `dE2000` / `kont` / `tint` / `uret`), üzerine
**HUE KAPISI** eklenmiş hâliyle. Elle yazılmış hex yoktur.

### 13.1 · Neden bir hue kapısı — bu turda ÜÇ araç hatası yakalandı

| # | hata | sonuç | kapı |
|---|---|---|---|
| 1 | gamut kırpması (`lab2rgb` sonrası RGB'yi [0,1]'e sıkıştırmak) | hue savruldu, macenta/mor üretti | üretilen rengin hue'su GERİ ÖLÇÜLÜR; sapma >1,0° ise aday REDDEDİLİR |
| 2 | jeton değeri yorum satırından okundu | gece kart zemini `#ffffff` sanıldı (doğrusu `#262626`) | jeton okurken CSS yorumları SIYRILIR (`re.sub(r"/\*.*?\*/")`) |
| 3 | gece kırmızısı serbest bırakıldı | pembeye kaydı | hue bantla sabitlenir (kırmızı 26,6°), kroma değişkendir, hue DEĞİL |

Ürettiğim her rengin hue'su hedefiyle karşılaştırıldı ve sapma **≤1,0°** çıktı:

| | hedef (LAB) | gündüz ölçülen | gece ölçülen |
|---|---|---|---|
| yeşil (Dub `vivid-green` hue'su) | 146,4° | 145,59° | 145,44° |
| turuncu (Dub `tangerine` hue'su) | 50,0° | 49,13° | 49,50° |
| kırmızı (TÜRETME — Dub'da yok) | 26,6° | 27,29° | 26,48° |

Seri merdiveni için kapı **OKLCh**'de kuruldu, LAB'de değil — ve bu bir tercih değil bir
düzeltmedir: MOD kanalının ayrılmış bandı (285-335°) OKLCh'de tanımlı, ve sabit LAB hue'su
ile üretilen "mavi" merdiven OKLCh'de tam o bandın içine düşüyordu (`#c5bfff` — bir lavanta).
Aynı sınıf hata, ikinci bir uzayda.

### 13.2 · ÖE1 · şiddet üçlüsü — üç eşik, iki tema

Eşikler karar §9.3'te ölçümden ÖNCE donduruldu ve **oynatılmadı**; §10.2 ÖE1-c'nin
ÖZNESİNİ değiştirdi (renkli mürekkep → nötr mürekkep), eşiğini değil.

| | gündüz | gece | eşik |
|---|---|---|---|
| **ÖE1-a** komşu luminans oranı (sev-1↔2, sev-2↔3) | 1.260 / 1.284 | 1.270 / 1.251 | ≥ 1,20 |
| **ÖE1-b** komşu ΔE2000 | 16.81 / 61.34 | 19.05 / 63.99 | ≥ 15 |
| **İŞARET** — kart üstünde | 6.25 / 4.96 / 3.87 | 6.15 / 4.84 / 3.87 | ≥ 3 |
| **İŞARET** — en kötü GERÇEK zemin | 5.74 / 4.55 / 3.55 (`--bg2`) | 5.51 / 4.34 / 3.47 (`--card-2`) | ≥ 3 |
| **İŞARET** — kendi %10 tinti üstünde | 5.22 / 4.29 / 3.16 | 4.69 / 3.89 / 3.15 | ≥ 3 |
| **ÖE1-c** ÇİP METNİ (`--tx`) kendi tinti üstünde | 16.53 / 17.13 / 17.46 | 9.16 / 9.65 / 9.79 | ≥ 4,5 |

Değerler: gündüz `--red #c3002d` · `--amber #c74300` · `--green #00963e` ·
gece `--red #ff7e7c` · `--amber #ff5a00` · `--green #00953d`.

**Kroma kazancı (OKLCh):** gündüz kehribar **+%94** · yeşil **+%50** · kırmızı **+%19** ·
gece kehribar **+%132** · kırmızı **+%95** · yeşil **+%49**.

Neden kazanç var: eski tavan "renkli mürekkep kendi tinti üstünde 4,5" idi ve bir rengi
4,5'e taşımanın tek yolu onu koyulaştırmaktı — sRGB'de koyulaşmak kromaya mal olur. Renk
metin olmaktan çıkınca tavan 3:1'e indi ve merdiven kromayı geri aldı. **Bu bir gevşetme
değildir**: okunabilirlik ölçütü aynı çipte 4,5 olarak DURUYOR, yalnız artık nötr mürekkebe
uygulanıyor ve o mürekkep 9,16-17,46 veriyor.

**Pay ölçüldü:** beşinci seçenek (renk metin kalıyordu) ΔE 15,1 ile 0,1 paylıydı; altıncı
seçenek 16,81 (gündüz) / 19,05 (gece) ile geliyor. Paylı arama (ΔE≥18) beşinci seçenekte
iki temada da BOŞ dönüyordu.

### 13.3 · Taşıyıcı grameri — üç biçim, sınıflandırılmış 39 kural

`index.html`de şiddet rengini `color:var(--sev-N)` deseniyle taşıyan **39 satır** tek tek
incelendi (`grep -cE "color:var\(--sev-[123]\)"`). Sınıflandırma:

| sınıf | satır | taşıyıcı | ölçüt |
|---|---|---|---|
| **çip / rozet** | 12 | 6px NOKTA (`::before`, kuralın `--isaret` değişkeni), tint zemin ve saç teli KORUNDU | işaret ≥3 · yazı ≥4,5 |
| **blok / satır** | 8 | 3px SOL ŞERİT (`border-left`) | işaret ≥3 |
| **satır içi metin** | 8 | 2px KALIN ALT ÇİZGİ (`text-decoration-color`, `skip-ink:none`) | işaret ≥3 |
| **kart mürekkebi** | 2 | kartın SOL ŞERİDİ (eski kural `currentColor` zinciriyle 24px'lik SAYIYI boyuyordu) | işaret ≥3 |
| **düğme** | 5 | kenar zaten renkliydi — yalnız YAZI nötrlendi | kenar ≥3 · dolgu üstündeki yazı ≥4,5 |
| **kenar / ikon — DOKUNULMADI** | 4 | `.spine.attn` / `.spine.act` (yalnız `border-*-color`) · `.ck.ok` / `.ck.man` (18×18 ikon kutusu) | metin-dışı 3:1, zaten sağlanıyor |

**GERÇEKTEN METİN OLMASI GEREKEN: SIFIR.** Bu bir tercih değil bir sonuçtur: metin kalan
her kural, rengin kendi tinti üstünde 4,5 tutmasını gerektirirdi ve yeni üçlü orada
3,16-5,22 veriyor. Tek bir kuralı metin bırakmak, ya o kuralı AA altında sevk etmek ya da
kroma kazancını geri vermek olurdu — ikisi de reddedildi.

İki istisna ADIYLA yazılıdır ve ikisi de "bu zaten metin değil" gerekçesine dayanır:
`.sev-N[aria-hidden="true"]` (ekran okuyucunun okumadığı glif — app.js'in alarm satırındaki
▲) ve `.ck.ok`/`.ck.man` (18px'lik kutuda tek işaret; kendi tinti üstünde 3.41/4.29 gündüz,
3.49/3.89 gece).

**Yan bulgu (aynı taramada):** `.pv-gorev.uyari{background:var(--sev-2-t))}` — fazladan bir
kapanış parantezi bildirimi GEÇERSİZ kılıyordu, yani "seni bekleyenler" satırının uyarı
zemini hiç boyanmıyordu. Düzeltildi.

### 13.4 · ÇG · seri merdiveni renklendi, CVD kanalı KALMADI

Eşikler karar §10.3'te donmuştu.

| | gündüz | gece | eşik |
|---|---|---|---|
| **ÇG1** komşu seri ΔL* | 16.45 / 16.37 | 15.60 / 15.61 | ≥ 15 |
| **ÇG2** her seri kart üstünde | 13.44 / 7.57 / 4.16 | 9.46 / 5.92 / 3.50 | ≥ 3 |
| **ÇG2** en kötü gerçek zemin | 12.33 / 6.95 / 3.82 | 8.49 / 5.31 / 3.14 | ≥ 3 |
| **ÇG3** `stroke-dasharray` sayısı (`app.js`) | 9 | 9 | DÜŞEMEZ |

Değerler: gündüz `--blue #003346` · `--violet #005b79` · `--violet2 #0086b1` ·
gece `--blue #83d7ff` · `--violet #40addb` · `--violet2 #0083ad`.

**Ad değişmedi, değer değişti.** `--violet` adı tarihseldir ve `app.js`in IC trend
sözleşmesinde yazılıdır (`IC_SERI.sim = "var(--violet)"`); adı değiştirmek kesik-çizgi
desenini kırardı. `--blue` ve `--violet2` bu tura kadar **ÖLÜ jetonlardı** (tanımlı, sıfır
okuyucu — YASA 6 ihlali); yeni ad açmak yerine onlar diriltildi, yani jeton sayısı seri
tarafında **artmadı**.

**HUE NEDEN DUB'IN MAVİSİ DEĞİL — ölçülmüş bir geri çekilme.** İlk deneme ROL 6'nın kendi
hue'suydu (deep-sapphire, OKLCh 265,6°) ve karar §10.3'ün önerisi de buydu. Gece merdiveni
orada `--nav-2` ile **ΔE2000 0,0**'a çöktü (üretilen en iyi kromalı aday birebir `#b2caff`
çıktı) ve "nav ailesine ΔE ≥8" arayan tarama **iki temada da BOŞ döndü**. Yani ROL 6'nın
bandında bir seri merdiveni kurulamıyor: gezinme mürekkebi (L* 67) ile gezinme mürekkep-2'si
(L* 81) tam olarak merdivenin ihtiyaç duyduğu iki basamağı işgal ediyor.

Hue bir sonraki SERBEST banda taşındı: **OKLCh 230°** (gök mavisi). Bu bir TÜRETMEDİR ve
gece paletiyle aynı damgayı taşır — Dub'da böyle bir jeton yok. Ölçülen ayrımlar:

| ayrım | gündüz | gece |
|---|---|---|
| seri ↔ `--nav` ailesi (min ΔE2000) | 14.7 | 13.9 |
| seri ↔ MOD bandı (`--mod-canli/kesif`) | 21.7 | 28.2 |
| seri ↔ şiddet üçlüsü | 33.6 | 34.0 |
| MOD bandına (285-335° OKLCh) giren seri basamağı | yok | yok |

**Kroma tavanı:** max C(seri) 0.1153 (gündüz) / 0.1179 (gece) < min C(şiddet) 0.1671 /
0.1578. Kural yön rolünün ×0,60'ının seri kardeşidir: **×0,75**. Bir seri çizgisi bir
alarmla dikkat için yarışamaz.

**§10.4 atama kuralı uygulandı ve bir yerde YETMEDİ, o da beyanlıdır.** `Sermaye` ↔ `Tepe`
aynı büyüklüğü ölçer (Tepe, Sermaye'den türetilir) → tek hue, iki açıklık. `.pv-nk.s1..s4`
ise DÖRT FARKLI büyüklüğün kimlik noktalarıdır ve §10.4 onlara ayrı hue ister; Dub'ın kalan
serbest hue bütçesi **birdir** ve dördüncü bir hue UYDURULMADI — `.pv-nk.s4` nötr kaldı.

**Kaynakta bulunan gizli kusur:** `pvAlanGrafigi` `pv-seri-${si}` sınıfı basıyor ama
`.pv-seri-2` kuralı YOKTU; üç serili bir metrik geldiği gün üçüncü çizgi `stroke` alamayıp
görünmez olurdu (SVG varsayılanı `none`). Merdivenin üçüncü basamağı artık kaynakta.

### 13.5 · `soft-mint` bağlandı (karar §10.5)

`#dcfce7` Dub'ın kendi `surface.tinted-accent` jetonudur ve bu tura kadar HİÇ
kullanılmıyordu. İki okuyucuya bağlandı, ikisi de KOŞULLU ve ikisi de olumlu:

* `.spine.calm` — durum şeridinin sakin hâli. Üçlü artık tamamlandı: `calm` mint,
  `attn` kehribar tinti, `act` kırmızı tinti. Öncesinde sakin hâlin yüzeyi YOKTU
  (`background:transparent`).
* `.pv-rz.ok` — "sakin" rozeti (olumlu onay).

Gece karşılığı TÜRETİLDİ (`#163523`): soft-mint'in OKLCh hue'su (156,7°) korundu, L 0,299'a
indirildi, kroma 0,0498'de tutuldu — min C(şiddet)'in görünür altında, çünkü bu bir zemindir.

Metin taşımaz ama üstüne metin düşer, ve karar §10.5 yine de ölçülmesini istedi:

| | gündüz `#dcfce7` | gece `#163523` |
|---|---|---|
| `--tx` üstünde | 18.03 | 10.63 |
| `--tx2` üstünde | 7.11 | 9.04 |
| `--tx3` üstünde | **4.32 (AA ALTI)** | 5.31 |
| `--sev-3` işareti (rozet noktası) | 3.52 | 3.42 |
| karttan farkı | 1.098 | 1.130 |

`--tx3` gündüzde AA altındadır ve bu yüzden **mint yüzeylerde `--tx3` okuyucusu yoktur**:
`.spine.calm` `--tx2` okur, `.pv-rz.ok` `--tx`. Bir gün mint bir `--tx3` metni taşırsa bu
satır o kararın kapısıdır.
