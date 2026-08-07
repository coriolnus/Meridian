// İsim çakışması + yüz ayrımı ölçümü. Ayrı dosya, satır içi değil — panonun CSP'siyle (script-src
// 'self') aynı disiplin burada da geçerli, çünkü ölçüm sayfası bir üretim sayfasını taklit ediyor.
(async function () {
  const AILELER = [
    ["ESKI Sans", "eski çift · sans kesiti (isim ÇAKIŞIK)"],
    ["ESKI Mono", "eski çift · mono kesiti (isim ÇAKIŞIK)"],
    ["YENI Sans", "yeni çift · sans (isim AYRIK)"],
    ["YENI Mono", "yeni çift · mono (isim AYRIK)"],
    ["GEIST Mono", "TABAN · emekli edilen incumbent"],
    ["ui-monospace", "KONTROL · sistem monosu (yüklenmemiş yüzün düşeceği yer)"],
    ["system-ui", "KONTROL · sistem sansı"],
  ];
  const PX = 100;                       // 100px: alt-piksel gürültüsü ölçümü bulandırmasın
  const cv = document.createElement("canvas");
  const cx = cv.getContext("2d");

  function genislik(aile, s) {
    cx.font = `400 ${PX}px "${aile}"`;
    return Math.round(cx.measureText(s).width * 1000) / 1000;
  }

  // ---- RASTER FARKI ------------------------------------------------------------------------
  // DESIGN.md'nin kendi dersi: `1`/`l` sorusunu GEOMETRİ karara bağlayamadı, TARAYICI bağladı.
  // Burası o dersin ölçüye çevrilmiş hâli. İki glif aynı kutuya, aynı taban çizgisine, gerçek
  // punto boyunda basılır; alfa kanalları karşılaştırılır.
  //   fark_orani   = farklı piksel / mürekkepli piksel (birleşim)  → 0 = ayırt edilemez
  //   fark_enerji  = |α1−α2| toplamı / 255                          → gözün gördüğü mürekkep farkı
  // Ölçüm cihazın devicePixelRatio'sundan bağımsız olsun diye canvas ölçeklenir.
  const dpr = window.devicePixelRatio || 1;
  function bas(aile, ch, px) {
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
  function rasterFark(aile, a, b, px) {
    const A = bas(aile, a, px), B = bas(aile, b, px);
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

  // Yüklemeyi BEKLE. `document.fonts.ready` yetmiyor: hiçbir düğüm o yüzü kullanmıyorsa
  // tarayıcı indirmeye hiç başlamaz. Bu yüzden her aile açıkça `load()` ile istenir.
  const yukleme = {};
  for (const [aile] of AILELER) {
    if (aile === "ui-monospace" || aile === "system-ui") { yukleme[aile] = "sistem"; continue; }
    try {
      const yuz = await document.fonts.load(`400 ${PX}px "${aile}"`, "0O1lIiM");
      yukleme[aile] = yuz.length ? `yüklendi (${yuz.length} yüz)` : "YÜKLENMEDİ (0 yüz)";
    } catch (e) { yukleme[aile] = "HATA: " + e.message; }
  }
  await document.fonts.ready;

  const satirlar = [];
  for (const [aile, aciklama] of AILELER) {
    const i = genislik(aile, "i"), M = genislik(aile, "M");
    const rakamlar = "0123456789".split("").map((d) => genislik(aile, d));
    const tekduze = new Set(rakamlar).size === 1;
    satirlar.push({
      aile, aciklama, yukleme: yukleme[aile],
      // MONOSPACE KANITI: `i` ile `M` eşitse yüz monospace'tir. Oransal bir yüzde bu
      // İMKÂNSIZDIR — yani bu tek sayı "mono gerçekten yüklendi mi"yi karara bağlar.
      i_genislik: i, M_genislik: M, monospace: i === M,
      rakam_genislikleri: [...new Set(rakamlar)], rakam_tekduze: tekduze,
      bir: genislik(aile, "1"), l_kucuk: genislik(aile, "l"), I_buyuk: genislik(aile, "I"),
      sifir: genislik(aile, "0"), O_buyuk: genislik(aile, "O"),
      // ADVANCE FARKI MONO YÜZDE ANLAMSIZDIR ve bu ölçümün ilk koşusunda tam olarak öyle
      // çıktı: `1` ile `l` ikisi de 600/1000, fark 0 — ama bu "ayırt edilemiyor" DEMEK
      // DEĞİL, sadece "advance eşit" demek (monospace tanımı gereği). Kayda alınıyor ki
      // yanlış ölçütün neden bırakıldığı görünür olsun; hüküm aşağıdaki RASTER FARKINDA.
      bir_l_advance_fark_100px: Math.round((genislik(aile, "1") - genislik(aile, "l")) * 1000) / 1000,
      // GERÇEK ÖLÇÜT: MÜREKKEP. Aynı kutuya basılan iki glifin PİKSELLERİ karşılaştırılır.
      raster_1_l: [10, 11, 12, 13, 28].reduce((o, px) => (o[px + "px"] = rasterFark(aile, "1", "l", px), o), {}),
      raster_0_O: [10, 11, 12, 13, 28].reduce((o, px) => (o[px + "px"] = rasterFark(aile, "0", "O", px), o), {}),
    });
  }

  // ESKİ ile YENİ çiftin AYNI mı FARKLI mı çizildiği — çakışmanın gerçekten iş bozup
  // bozmadığının doğrudan cevabı.
  const bul = (a) => satirlar.find((s) => s.aile === a);
  const hukum = {
    // ÇAKIŞMA GERÇEKTEN İŞ BOZUYOR MUYDU? Rapor "self-host edilirse mono KAYBOLUR" diyordu.
    // Ölçüm bunu SINAR: eski (çakışık isimli) çift de ayrı @font-face aileleri altında ayrışıyorsa
    // iddia bu yol için YANLIŞTIR — ve yeniden adlandırma yine de doğrudur (ikili kendi hakkında
    // yanlış beyan taşıyordu), ama BLOKE EDİCİ değildi. Fark önemli: hangi kapının kapandığını
    // bilmek, kapanmamış kapıyı kapalı sanmaktan iyidir.
    "eski_cift_ayrisiyor_mu":
      bul("ESKI Sans").i_genislik !== bul("ESKI Mono").i_genislik ||
      bul("ESKI Sans").monospace !== bul("ESKI Mono").monospace,
    "yeni_cift_ayrisiyor_mu":
      bul("YENI Sans").i_genislik !== bul("YENI Mono").i_genislik ||
      bul("YENI Sans").monospace !== bul("YENI Mono").monospace,
    "yeni_mono_gercekten_mono": bul("YENI Mono").monospace,
    "yeni_sans_oransal": !bul("YENI Sans").monospace,
    "yeni_mono_rakamlar_tekduze": bul("YENI Mono").rakam_tekduze,
    "yeni_sans_rakamlar_tekduze": bul("YENI Sans").rakam_tekduze,
    // 10px'te `1` ile `l` — MÜREKKEPLE. Geist Mono tabanıyla yan yana okunmalı.
    "yeni_mono_1l_10px_fark_orani": bul("YENI Mono").raster_1_l["10px"].fark_orani,
    "geist_mono_1l_10px_fark_orani": bul("GEIST Mono").raster_1_l["10px"].fark_orani,
    "yeni_mono_1l_28px_fark_orani": bul("YENI Mono").raster_1_l["28px"].fark_orani,
    "geist_mono_1l_28px_fark_orani": bul("GEIST Mono").raster_1_l["28px"].fark_orani,
    "yeni_sans_0O_28px_fark_orani": bul("YENI Sans").raster_0_O["28px"].fark_orani,
  };

  // dpr KAYDA GİRER: raster farkı oranları cihaz piksel oranına duyarlıdır (dpr=2'de aynı
  // ölçüm daha düşük mutlak değer verir). Sıralama iki koşuda da AYNI çıktı, ama mutlak
  // sayıyı dpr'siz yazmak onu karşılaştırılamaz kılardı.
  const sonuc = { userAgent: navigator.userAgent, devicePixelRatio: dpr, olcum_px: PX, satirlar, hukum };
  document.getElementById("cikti").textContent = JSON.stringify(sonuc, null, 1);
  // Ekranda da görünsün — sayı ile göz aynı sayfada dursun.
  document.getElementById("ornek").innerHTML = AILELER.map(([a, d]) =>
    `<div style="font-family:'${a}';font-size:24px">${a} · 0O1lI iM 0123456789 · ıİşğçöü` +
    `<span style="font-size:11px;font-family:ui-monospace;opacity:.6"> ← ${d}</span></div>`).join("");
  document.title = "OLCUM TAMAM";
})();
