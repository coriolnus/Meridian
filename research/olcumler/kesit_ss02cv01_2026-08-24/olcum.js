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
  // TAKİP TURU (kesit ss02/cv01) — liste DARALTILDI, yöntem değişmedi. Ölçülen tek soru:
  // özellikleri KORUYAN bir kesit, budanmış kesitten ve tam dosyadan nerede duruyor.
  const AILELER = [
    ["INTER kesit2",           "YENİ · ss02+cv01 KORUNMUŞ kesit, descriptor KAPALI"],
    ["INTER kesit2 ss02cv01",  "YENİ · aynı bayt, descriptor AÇIK — SINANAN HÂL"],
    ["INTER kesit",            "TABAN · bugün dağıtılan kesit (budanmış)"],
    ["INTER kesit ss02cv01",   "TABAN · budanmış kesit + descriptor (etkisiz olmalı)"],
    ["INTER tam ss02cv01",     "ÜST SINIR · tam dosya, iki özellik açık"],
    ["Recursive Sans",         "DONMUŞ TABAN · emekli sans"],
    ["Recursive Mono",         "DONMUŞ TABAN · yürürlükteki mono"],
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
    aciklama: "Aynı font BAYTI iki @font-face altında; biri descriptor'sız, biri özellikli. " +
              "Fark>0 ise özellik dosyada VAR ve tarayıcı descriptor'ı UYGULUYOR. Fark=0 ise " +
              "ya descriptor yok sayıldı ya özellik dosyada yok — ikisini AYIRMAK için eski " +
              "kesit (özelliksiz, fark 0 beklenir) ile tam dosya (özellikli, fark>0 beklenir) " +
              "aynı koşuda kontrol olarak durur.",
    dpr: 1,
    "yeni_kesit_l_descriptor_etkisi_28px": capraz("INTER kesit2", "INTER kesit2 ss02cv01", "l", 28, 1),
    "yeni_kesit_1_descriptor_etkisi_28px": capraz("INTER kesit2", "INTER kesit2 ss02cv01", "1", 28, 1),
    "yeni_kesit_I_descriptor_etkisi_28px": capraz("INTER kesit2", "INTER kesit2 ss02cv01", "I", 28, 1),
    "eski_kesit_l_descriptor_etkisi_28px": capraz("INTER kesit", "INTER kesit ss02cv01", "l", 28, 1),
    "yeni_kesit_vs_ust_sinir_l_28px": capraz("INTER kesit2 ss02cv01", "INTER tam ss02cv01", "l", 28, 1),
    "yeni_kesit_vs_eski_kesit_l_28px": capraz("INTER kesit2", "INTER kesit", "l", 28, 1),
    "negatif_kontrol_ayni_aile_ayni_karakter": capraz("INTER kesit", "INTER kesit", "l", 28, 1),
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
  // TAKİP TURU. Ölçülen tek soru: `ss02`/`cv01` KORUNMUŞ bir kesit, budanmış kesitten ve
  // tam dosyadan nerede duruyor. Çıta 08-07'de donduruldu ve DEĞİŞTİRİLMEDİ.
  const bul = (a) => satirlar.find((s) => s.aile === a);
  const o1l = (a, px) => bul(a).raster_1_l_dpr1[px + "px"].fark_orani;
  const o0O = (a, px) => bul(a).raster_0_O_dpr1[px + "px"].fark_orani;
  const olI = (a, px) => bul(a).raster_l_I_dpr1[px + "px"].fark_orani;
  const CITA = 0.75;

  const YENI = "INTER kesit2 ss02cv01", ESKI = "INTER kesit", UST = "INTER tam ss02cv01";
  const hukum = {
    "soru": "ss02/cv01 KORUNARAK alınan kesit, 1/l ayrımını budanmış kesidin üstüne çıkarıyor mu?",
    "kabul_citasi_10px_1l_fark_orani": CITA,
    "cita_kaynagi": "2026-08-07 turunda donduruldu; bu turda DEĞİŞTİRİLMEDİ",

    // KALİBRASYON — bu klasördeki düzenek, donmuş tabanı hâlâ üretiyor mu?
    "kalibrasyon_recursive_mono_1l_10px": o1l("Recursive Mono", 10),
    "kalibrasyon_recursive_mono_1l_28px": o1l("Recursive Mono", 28),
    "kalibrasyon_donmus_taban_recursive_mono": [1.00, 0.817],
    "kalibrasyon_recursive_sans_1l_28px": o1l("Recursive Sans", 28),
    "kalibrasyon_recursive_sans_0O_28px": o0O("Recursive Sans", 28),
    "kalibrasyon_donmus_taban_recursive_sans": [0.931, 0.663],
    "kalibrasyon_eski_kesit_1l_28px": o1l(ESKI, 28),
    "kalibrasyon_08_24_kaydindaki_eski_kesit": 0.968,

    // ÖZELLİK GERÇEKTEN GELDİ Mİ — descriptor açık/kapalı AYNI BAYT üzerinde ayrışmalı
    "yeni_kesitte_ozellik_VAR_MI":
      (probe["yeni_kesit_l_descriptor_etkisi_28px"].fark_orani || 0) > 0,
    "eski_kesitte_ozellik_YOK_MU":
      (probe["eski_kesit_l_descriptor_etkisi_28px"].fark_orani || 0) === 0,

    // ASIL SAYILAR
    "yeni_kesit_1l_10px": o1l(YENI, 10),
    "yeni_kesit_1l_28px": o1l(YENI, 28),
    "yeni_kesit_0O_28px": o0O(YENI, 28),
    "yeni_kesit_lI_28px": olI(YENI, 28),
    "eski_kesit_1l_28px": o1l(ESKI, 28),
    "eski_kesit_0O_28px": o0O(ESKI, 28),
    "eski_kesit_lI_28px": olI(ESKI, 28),
    "ust_sinir_tam_1l_28px": o1l(UST, 28),
    "kazanc_1l_28px": Math.round((o1l(YENI, 28) - o1l(ESKI, 28)) * 1000) / 1000,
    "ust_sinira_kalan_1l_28px": Math.round((o1l(UST, 28) - o1l(YENI, 28)) * 1000) / 1000,

    "cita_yeni_kesit": o1l(YENI, 10) >= CITA,
    "yeni_kesit_ESKISINI_geciyor_mu": o1l(YENI, 28) >= o1l(ESKI, 28),
    "yeni_kesit_RECURSIVE_SANSI_geciyor_mu":
      o1l(YENI, 28) > o1l("Recursive Sans", 28) && o0O(YENI, 28) > o0O("Recursive Sans", 28),

    // BİÇİM — kesit hâlâ oransal ve tnum hâlâ çalışıyor olmalı
    "yeni_kesit_oransal": !bul(YENI).monospace,
    "yeni_kesit_tnum_acikken_tekduze": tabular[YENI].tnum_acik_tekduze,
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
