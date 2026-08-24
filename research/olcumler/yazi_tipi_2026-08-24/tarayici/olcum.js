// ÜÇ YÜZ · DONMUŞ TABANA KARŞI — 2026-08-24 turu.
// YÖNTEM 08-07 turundan DEĞİŞMEDİ (değişseydi kıyas ölürdü): iki glif aynı kutuya, aynı
// taban çizgisine, GERÇEK punto boyunda basılır; ALFA kanalları karşılaştırılır.
//   fark_orani  = farklı piksel / mürekkepli piksel (birleşim)  → 0 = ayırt edilemez
//   fark_enerji = Σ|α1−α2| / 255
// ADVANCE ile ölçmek MONO YÜZDE ANLAMSIZDIR (1 ve l zaten eşit advance'ta) — 08-07 turunda
// açıkça düzeltilen ayrım budur; advance yine kayda girer ama hüküm MÜREKKEPTEDİR.
//
// BU TURUN İKİ EKİ:
//  (1) dpr=1 ZORLAMASI. 08-07 kaydı dpr=1 (HeadlessChrome) altında alındı ve kendi notunda
//      "dpr=2'de aynı ölçüm daha düşük değer verir" diyor. Bu koşu hem cihazın gerçek
//      dpr'sinde hem dpr=1'e zorlanmış hâlde ölçer; donmuş tabanla kıyaslanacak sütun dpr1'dir.
//  (2) ÇAPRAZ AİLE farkı: aynı karakterin İKİ AİLEDE (özellik kapalı/açık) mürekkep farkı.
//      Inter'in ss02/cv01 sınavı bunun üstünde koşar.
(async function () {
  const AILELER = [
    ["INTER kesit",          "A · YENİ sans · dağıtım adayı kesit (ss02/cv01 BUDANMIŞ)"],
    ["INTER tam",            "A' · Inter v4.1 TAM dosya, özellik KAPALI (varsayılan)"],
    ["INTER tam ss02",       "A'' · Inter TAM, ss02 AÇIK (I→I.1, l→l.ss02, 0→zero.slash)"],
    ["INTER tam ss02cv01",   "A''' · Inter TAM, ss02+cv01 AÇIK (ek: 1→one.ss01)"],
    ["INTER kesit ss02cv01", "A× · KESİT + aynı descriptor — budama iddiasının sınavı"],
    ["INTER kesit zero",      "A° · KESİT + yalnız 'zero' — budamanın TUTTUĞU özelliğin sınavı"],
    ["INTER tam opsz14",      "A^ · Inter TAM, opsz 14'e ÇİVİLİ (kesitin sabitlediği değer)"],
    ["INTER tam opsz32",      "A^^ · Inter TAM, opsz 32'ye ÇİVİLİ (Display ucu)"],
    ["GEIST Mono kesit",     "B · YENİ mono · Geist Mono v1.7.2 dağıtım adayı kesit"],
    ["GEIST Mono kesit zero", "B° · KESİT + yalnız 'zero' (eğik çizgili sıfır)"],
    ["Recursive Sans",       "C · DONMUŞ TABAN · canlıdaki sans"],
    ["Recursive Mono",       "C · DONMUŞ TABAN · canlıdaki mono"],
    ["GEIST Mono 0807",      "D · KALİBRASYON · 08-07'nin ölçtüğü Geist Mono'nun ta kendisi"],
    ["ui-monospace",         "KONTROL · sistem monosu (yüklenmemiş yüzün düşeceği yer)"],
    ["system-ui",            "KONTROL · sistem sansı"],
  ];
  const SISTEM = new Set(["ui-monospace", "system-ui"]);
  const PX = 100;                       // advance ölçümü: 100px, alt-piksel gürültüsü olmasın
  const BOYLAR = [10, 11, 12, 13, 28];  // 08-07 ile AYNI rampa
  const cv = document.createElement("canvas");
  const cx = cv.getContext("2d");
  const gercekDpr = window.devicePixelRatio || 1;

  function genislik(aile, s) {
    cx.font = `400 ${PX}px "${aile}"`;
    return Math.round(cx.measureText(s).width * 1000) / 1000;
  }

  // --- RASTER ------------------------------------------------------------------------------
  function bas(aile, ch, px, dpr) {
    const w = Math.ceil(px * 2), h = Math.ceil(px * 2);
    const c = document.createElement("canvas");
    c.width = Math.ceil(w * dpr); c.height = Math.ceil(h * dpr);
    const k = c.getContext("2d", { willReadFrequently: true });
    k.scale(dpr, dpr);
    k.clearRect(0, 0, w, h);
    k.fillStyle = "#000";
    k.textBaseline = "alphabetic";
    k.font = `400 ${px}px "${aile}"`;
    k.fillText(ch, px * 0.4, px * 1.4);
    return k.getImageData(0, 0, c.width, c.height).data;
  }
  function kiyas(A, B) {
    let farkli = 0, birlesim = 0, enerji = 0;
    for (let i = 3; i < A.length; i += 4) {
      const x = A[i], y = B[i];
      if (x > 8 || y > 8) birlesim++;
      if (Math.abs(x - y) > 8) farkli++;
      enerji += Math.abs(x - y);
    }
    return {
      fark_orani: birlesim ? Math.round((farkli / birlesim) * 1000) / 1000 : null,
      fark_enerji: Math.round((enerji / 255) * 100) / 100,
      murekkepli_piksel: birlesim,
    };
  }
  // AYNI ailede iki karakter (08-07'nin ölçtüğü şey)
  const rasterFark = (aile, a, b, px, dpr) => kiyas(bas(aile, a, px, dpr), bas(aile, b, px, dpr));
  // İKİ ailede AYNI karakter (özellik açık/kapalı sınavı)
  const capraz = (aileA, aileB, ch, px, dpr) => kiyas(bas(aileA, ch, px, dpr), bas(aileB, ch, px, dpr));

  function rampa(fn) { return BOYLAR.reduce((o, px) => (o[px + "px"] = fn(px), o), {}); }

  // --- YÜKLEME ------------------------------------------------------------------------------
  // `document.fonts.ready` YETMEZ: hiçbir düğüm yüzü kullanmıyorsa tarayıcı indirmeye
  // başlamaz. Her aile AÇIKÇA istenir ve sonuç kayda girer.
  const yukleme = {};
  for (const [aile] of AILELER) {
    if (SISTEM.has(aile)) { yukleme[aile] = "sistem"; continue; }
    try {
      const yuz = await document.fonts.load(`400 ${PX}px "${aile}"`, "0O1lIiM0123456789");
      yukleme[aile] = yuz.length ? `yüklendi (${yuz.length} yüz)` : "YÜKLENMEDİ (0 yüz)";
    } catch (e) { yukleme[aile] = "HATA: " + e.message; }
  }
  await document.fonts.ready;

  // --- PROBE: @font-face font-feature-settings descriptor GERÇEKTEN uygulanıyor mu? ---------
  // Bu VARSAYILMAZ. Descriptor sessizce yok sayılırsa "ss02 fark etmiyor" diye YANLIŞ hüküm
  // çıkardı. Kanıt: aynı BAYT, aynı karakter, iki aile — piksel farkı SIFIRDAN büyük mü?
  const probe = {
    aciklama: "Aynı font dosyası iki @font-face altında; biri descriptor'sız, biri özellikli. " +
              "Fark>0 ise tarayıcı descriptor'ı UYGULUYOR. Fark=0 ise descriptor yok sayılmış " +
              "YA DA özellik dosyada yok — ikisini ayırmak için kesit/tam çapraz okunur.",
    dpr: 1,
    "tam_l_ss02_vs_kapali_28px":    capraz("INTER tam", "INTER tam ss02", "l", 28, 1),
    "tam_I_ss02_vs_kapali_28px":    capraz("INTER tam", "INTER tam ss02", "I", 28, 1),
    "tam_0_ss02_vs_kapali_28px":    capraz("INTER tam", "INTER tam ss02", "0", 28, 1),
    "tam_1_cv01_vs_ss02tek_28px":   capraz("INTER tam ss02", "INTER tam ss02cv01", "1", 28, 1),
    "kesit_l_descriptor_etkisi_28px": capraz("INTER kesit", "INTER kesit ss02cv01", "l", 28, 1),
    "kesit_0_descriptor_etkisi_28px": capraz("INTER kesit", "INTER kesit ss02cv01", "0", 28, 1),
    "kesit_1_descriptor_etkisi_28px": capraz("INTER kesit", "INTER kesit ss02cv01", "1", 28, 1),
    // `zero` KESİTTE DURUYOR MU? Budama raporu "tuttu" diyor; ölçüm bunu sınar.
    "kesit_inter_0_zero_etkisi_28px":  capraz("INTER kesit", "INTER kesit zero", "0", 28, 1),
    "kesit_geist_0_zero_etkisi_28px":  capraz("GEIST Mono kesit", "GEIST Mono kesit zero", "0", 28, 1),
    // OPSZ: dağıtım kesiti (opsz=14 çivili) tam dosyanın opsz=14 hâliyle AYNI mı?
    // Aynıysa kesit üretimi yüzü bozmamıştır; farklıysa fark BURADA görünür.
    "kesit_vs_tam_opsz14_l_28px": capraz("INTER kesit", "INTER tam opsz14", "l", 28, 1),
    "kesit_vs_tam_opsz14_1_28px": capraz("INTER kesit", "INTER tam opsz14", "1", 28, 1),
    "kesit_vs_tam_opsz14_0_28px": capraz("INTER kesit", "INTER tam opsz14", "0", 28, 1),
    "kesit_vs_tam_opsz14_M_28px": capraz("INTER kesit", "INTER tam opsz14", "M", 28, 1),
    // opsz 14 ile 32 arasındaki gerçek biçim farkı (Display kesimi ne kadar başka?)
    "tam_opsz14_vs_opsz32_M_28px": capraz("INTER tam opsz14", "INTER tam opsz32", "M", 28, 1),
    "tam_opsz14_vs_opsz32_0_28px": capraz("INTER tam opsz14", "INTER tam opsz32", "0", 28, 1),
    // NEGATİF KONTROL: aynı aile, aynı karakter → 0 çıkmalı. Çıkmazsa ölçüm gürültülüdür.
    "negatif_kontrol_ayni_aile_ayni_karakter": capraz("INTER tam", "INTER tam", "l", 28, 1),
  };

  // --- SATIRLAR -----------------------------------------------------------------------------
  const satirlar = [];
  for (const [aile, aciklama] of AILELER) {
    const i = genislik(aile, "i"), M = genislik(aile, "M");
    const rakamlar = "0123456789".split("").map((d) => genislik(aile, d));
    satirlar.push({
      aile, aciklama, yukleme: yukleme[aile],
      // MONOSPACE KANITI: i === M oransal bir yüzde İMKÂNSIZDIR.
      i_genislik: i, M_genislik: M, monospace: i === M,
      rakam_genislikleri: [...new Set(rakamlar)], rakam_tekduze: new Set(rakamlar).size === 1,
      bir: genislik(aile, "1"), l_kucuk: genislik(aile, "l"), I_buyuk: genislik(aile, "I"),
      sifir: genislik(aile, "0"), O_buyuk: genislik(aile, "O"),
      bir_l_advance_fark_100px: Math.round((genislik(aile, "1") - genislik(aile, "l")) * 1000) / 1000,
      // HÜKMÜN KOŞTUĞU YER — dpr=1 (donmuş tabanla aynı koşul)
      raster_1_l_dpr1: rampa((px) => rasterFark(aile, "1", "l", px, 1)),
      raster_0_O_dpr1: rampa((px) => rasterFark(aile, "0", "O", px, 1)),
      // EK SÜTUN (08-07'de YOKTU): küçük l ile büyük I. 6× yakınlaştırma Inter'in
      // varsayılanında bu ikisinin ÇIPLAK DİKME olarak ÇAKIŞTIĞINI gösterdi; iddia
      // yerine sayı koymak için aynı yöntemle ölçülür. Taban sayısı yok — bu turda doğar.
      raster_l_I_dpr1: rampa((px) => rasterFark(aile, "l", "I", px, 1)),
      // Cihazın gerçek dpr'sinde aynı ölçüm — dpr duyarlılığı görünür olsun diye
      raster_1_l_gercek_dpr: rampa((px) => rasterFark(aile, "1", "l", px, gercekDpr)),
      raster_0_O_gercek_dpr: rampa((px) => rasterFark(aile, "0", "O", px, gercekDpr)),
    });
  }


  // --- TABULAR SINAVI, DOM ÜZERİNDEN ----------------------------------------------------------
  // Canvas2D `font-variant-numeric`i TAŞIMAZ; yukarıdaki `rakam_tekduze` bu yüzden yalnız
  // VARSAYILAN durumu ölçer. Oransal bir sansta (Inter) varsayılanın tekdüze OLMAMASI
  // beklenendir — asıl soru "tnum açıldığında tekdüze oluyor mu". O soru DOM'da sorulur.
  function domRakamGenislikleri(aile, tnum) {
    const kap = document.createElement("div");
    kap.style.cssText = "position:absolute;left:-9999px;top:0;visibility:hidden;" +
      `font:400 100px "${aile}";white-space:pre;` +
      (tnum ? "font-variant-numeric:tabular-nums;" : "font-variant-numeric:normal;");
    document.body.appendChild(kap);
    const w = [];
    for (const d of "0123456789") {
      const sp = document.createElement("span");
      sp.textContent = d; kap.appendChild(sp);
      w.push(Math.round(sp.getBoundingClientRect().width * 1000) / 1000);
    }
    kap.remove();
    return w;
  }
  const tabular = {};
  for (const [aile] of AILELER) {
    const varsayilan = domRakamGenislikleri(aile, false);
    const acik = domRakamGenislikleri(aile, true);
    tabular[aile] = {
      varsayilan_genislikler: [...new Set(varsayilan)].sort((a, b) => a - b),
      varsayilan_tekduze: new Set(varsayilan).size === 1,
      tnum_acik_genislikler: [...new Set(acik)].sort((a, b) => a - b),
      tnum_acik_tekduze: new Set(acik).size === 1,
      tnum_bir_sey_degistirdi_mi: JSON.stringify(varsayilan) !== JSON.stringify(acik),
    };
  }

  // --- HÜKÜM --------------------------------------------------------------------------------
  const bul = (a) => satirlar.find((s) => s.aile === a);
  const o1l = (a, px) => bul(a).raster_1_l_dpr1[px + "px"].fark_orani;
  const o0O = (a, px) => bul(a).raster_0_O_dpr1[px + "px"].fark_orani;
  const olI = (a, px) => bul(a).raster_l_I_dpr1[px + "px"].fark_orani;
  const CITA = 0.75;  // 08-07 turunda DONDURULDU: 10px'te 1/l fark oranı >= 0.75. Değiştirilmedi.

  const hukum = {
    "kabul_citasi_10px_1l_fark_orani": CITA,
    "cita_kaynagi": "2026-08-07 turunda donduruldu; bu turda DEĞİŞTİRİLMEDİ",

    // KALİBRASYON — düzenek 08-07'nin sayısını yeniden üretiyor mu?
    "kalibrasyon_geist0807_1l_10px_fark_orani": o1l("GEIST Mono 0807", 10),
    "kalibrasyon_geist0807_1l_28px_fark_orani": o1l("GEIST Mono 0807", 28),
    "kalibrasyon_donmus_taban_geist_1l_10px": 0.92,
    "kalibrasyon_donmus_taban_geist_1l_28px": 0.57,
    "kalibrasyon_recursive_mono_1l_10px_fark_orani": o1l("Recursive Mono", 10),
    "kalibrasyon_recursive_mono_1l_28px_fark_orani": o1l("Recursive Mono", 28),
    "kalibrasyon_donmus_taban_recursive_mono_1l_10px": 1.00,
    "kalibrasyon_donmus_taban_recursive_mono_1l_28px": 0.817,
    "kalibrasyon_recursive_sans_0O_28px_fark_orani": o0O("Recursive Sans", 28),
    "kalibrasyon_donmus_taban_recursive_sans_0O_28px": 0.663,

    // YENİ YÜZLER — 08-07 anahtar mantığıyla
    "inter_kesit_1l_10px_fark_orani": o1l("INTER kesit", 10),
    "inter_kesit_1l_28px_fark_orani": o1l("INTER kesit", 28),
    "inter_kesit_0O_28px_fark_orani": o0O("INTER kesit", 28),
    "inter_tam_kapali_1l_10px_fark_orani": o1l("INTER tam", 10),
    "inter_tam_kapali_1l_28px_fark_orani": o1l("INTER tam", 28),
    "inter_tam_kapali_0O_28px_fark_orani": o0O("INTER tam", 28),
    "inter_tam_ss02_1l_10px_fark_orani": o1l("INTER tam ss02", 10),
    "inter_tam_ss02_1l_28px_fark_orani": o1l("INTER tam ss02", 28),
    "inter_tam_ss02_0O_28px_fark_orani": o0O("INTER tam ss02", 28),
    "inter_tam_ss02cv01_1l_10px_fark_orani": o1l("INTER tam ss02cv01", 10),
    "inter_tam_ss02cv01_1l_28px_fark_orani": o1l("INTER tam ss02cv01", 28),
    "inter_tam_ss02cv01_0O_28px_fark_orani": o0O("INTER tam ss02cv01", 28),
    "geist_mono_kesit_1l_10px_fark_orani": o1l("GEIST Mono kesit", 10),
    "geist_mono_kesit_1l_28px_fark_orani": o1l("GEIST Mono kesit", 28),
    "geist_mono_kesit_0O_28px_fark_orani": o0O("GEIST Mono kesit", 28),
    "recursive_mono_0O_28px_fark_orani": o0O("Recursive Mono", 28),

    // l/I SÜTUNU — bu turda DOĞAN ölçüt, donmuş tabanda karşılığı YOK
    "EK_lI_sutunu_notu": "08-07 turu l/I'yı ölçmedi; aşağıdaki sayıların donmuş tabanda karşılığı YOKTUR. " +
      "Tüm yüzler AYNI koşuda ölçüldüğü için yüzler arası kıyas geçerlidir, tabanla kıyas DEĞİLDİR.",
    "inter_kesit_lI_10px_fark_orani": olI("INTER kesit", 10),
    "inter_kesit_lI_28px_fark_orani": olI("INTER kesit", 28),
    "inter_tam_ss02_lI_10px_fark_orani": olI("INTER tam ss02", 10),
    "inter_tam_ss02_lI_28px_fark_orani": olI("INTER tam ss02", 28),
    "geist_mono_kesit_lI_10px_fark_orani": olI("GEIST Mono kesit", 10),
    "geist_mono_kesit_lI_28px_fark_orani": olI("GEIST Mono kesit", 28),
    "recursive_mono_lI_10px_fark_orani": olI("Recursive Mono", 10),
    "recursive_mono_lI_28px_fark_orani": olI("Recursive Mono", 28),
    "recursive_sans_lI_10px_fark_orani": olI("Recursive Sans", 10),
    "recursive_sans_lI_28px_fark_orani": olI("Recursive Sans", 28),
    "inter_kesit_lI_28px_AYIRT_EDILEMEZ_MI": olI("INTER kesit", 28) === 0,

    // ÇITA KARARI (yalnız 10px 1/l — 08-07'nin dondurduğu tek çıta)
    "cita_inter_kesit": o1l("INTER kesit", 10) >= CITA,
    "cita_inter_tam_kapali": o1l("INTER tam", 10) >= CITA,
    "cita_inter_tam_ss02": o1l("INTER tam ss02", 10) >= CITA,
    "cita_inter_tam_ss02cv01": o1l("INTER tam ss02cv01", 10) >= CITA,
    "cita_geist_mono_kesit": o1l("GEIST Mono kesit", 10) >= CITA,
    "cita_recursive_mono": o1l("Recursive Mono", 10) >= CITA,

    // BİÇİM SINAVI
    "inter_kesit_oransal": !bul("INTER kesit").monospace,
    "geist_mono_kesit_gercekten_mono": bul("GEIST Mono kesit").monospace,
    "recursive_mono_gercekten_mono": bul("Recursive Mono").monospace,
    "recursive_sans_oransal": !bul("Recursive Sans").monospace,
    "inter_kesit_rakamlar_tekduze": bul("INTER kesit").rakam_tekduze,
    "inter_kesit_tnum_acikken_tekduze": tabular["INTER kesit"].tnum_acik_tekduze,
    "geist_mono_kesit_tnum_acikken_tekduze": tabular["GEIST Mono kesit"].tnum_acik_tekduze,
    "recursive_sans_tnum_acikken_tekduze": tabular["Recursive Sans"].tnum_acik_tekduze,
    "recursive_mono_tnum_acikken_tekduze": tabular["Recursive Mono"].tnum_acik_tekduze,
    "geist_mono_kesit_rakamlar_tekduze": bul("GEIST Mono kesit").rakam_tekduze,
    "recursive_mono_rakamlar_tekduze": bul("Recursive Mono").rakam_tekduze,
    "recursive_sans_rakamlar_tekduze": bul("Recursive Sans").rakam_tekduze,

    // ÖZELLİK HÜKMÜ
    "descriptor_uygulaniyor_mu":
      (probe["tam_l_ss02_vs_kapali_28px"].fark_orani || 0) > 0,
    "kesitte_ss02_var_mi":
      (probe["kesit_l_descriptor_etkisi_28px"].fark_orani || 0) > 0,
    "inter_kesit_zero_ozelligi_calisiyor_mu":
      (probe["kesit_inter_0_zero_etkisi_28px"].fark_orani || 0) > 0,
    "geist_kesit_zero_ozelligi_calisiyor_mu":
      (probe["kesit_geist_0_zero_etkisi_28px"].fark_orani || 0) > 0,
    "inter_kesit_zero_acik_0O_28px_fark_orani": o0O("INTER kesit zero", 28),
    "geist_kesit_zero_acik_0O_28px_fark_orani": o0O("GEIST Mono kesit zero", 28),
    "kesit_tam_opsz14_ile_ayni_mi":
      ["l","1","0","M"].every(c => (probe["kesit_vs_tam_opsz14_" + c + "_28px"].fark_orani || 0) === 0),
    "opsz_ekseni_gercekten_bicim_degistiriyor_mu":
      (probe["tam_opsz14_vs_opsz32_M_28px"].fark_orani || 0) > 0,
    "kesit_opsz14e_SABITLENDI_display_kesimi_ALINAMAZ": true,
    "cv01_rakam1i_degistiriyor_mu":
      (probe["tam_1_cv01_vs_ss02tek_28px"].fark_orani || 0) > 0,
  };

  const sonuc = {
    olcum_turu: "yazi_tipi_2026-08-24 · tarayıcı okunaklılık",
    yontem: "08-07 turunun olcum.js'i; MÜREKKEP (alfa) farkı, advance DEĞİL. Rampa ve eşikler aynı.",
    userAgent: navigator.userAgent,
    devicePixelRatio: gercekDpr,
    hukum_dpr: 1,
    olcum_px: PX,
    probe, tabular, satirlar, hukum,
  };
  window.__SONUC__ = sonuc;
  document.getElementById("cikti").textContent = JSON.stringify(sonuc, null, 1);
  document.getElementById("ozet").innerHTML = AILELER.map(([a, d]) =>
    `<div style="font-family:'${a}';font-size:24px">${a} · 0O1lI Il1O0 · 0123456789 · ıİşğçöü` +
    `<span style="font-size:11px;font-family:ui-monospace;opacity:.6"> ← ${d}</span></div>`).join("");
  document.title = "OLCUM TAMAM";
})();
