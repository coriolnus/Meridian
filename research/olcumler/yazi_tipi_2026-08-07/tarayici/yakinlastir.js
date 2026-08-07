(async function () {
  const Z = 6;                                     // büyütme katsayısı (piksel, harf değil)
  const SIRALAR = [
    ["Recursive Mono", "0O1lI Il1O0 0123456789", [10, 11, 12, 13], [400, 700]],
    ["Recursive Mono", "IŞIK İĞNE ÇÖZÜM ÜSTÜNDE ĞAZI", [10, 11], [700]],
    ["Recursive Sans", "ö o ü u ğ g ş s ç c ı i İ I ıİşğçöüŞĞÇÖÜ", [10, 11, 12, 13], [400]],
    ["Recursive Sans", "0O 1lI · 0O1lI", [13, 28], [400]],
    ["Recursive Mono", "0O 1lI · 0O1lI", [13, 28], [400]],
  ];
  const ZEMIN = [["g", "#fbf9f8", "#050505"], ["k", "#1E1E1E", "#D4D4D4"]];

  for (const [aile] of SIRALAR) await document.fonts.load(`400 10px "${aile}"`, "0O1lIıİşğçöü");
  for (const [aile] of SIRALAR) await document.fonts.load(`700 10px "${aile}"`, "0O1lIıİşğçöü");
  await document.fonts.ready;

  for (const [kap, bg, ink] of ZEMIN) {
    const host = document.getElementById(kap);
    for (const [aile, metin, boylar, agirliklar] of SIRALAR) {
      for (const px of boylar) {
        for (const w of agirliklar) {
          const et = document.createElement("div");
          et.className = "et";
          et.textContent = `${aile} · ${px}px · w${w}`;
          host.appendChild(et);

          // 1) GERÇEK punto boyunda bas (dpr=1 zorlanır: ölçülen şey CSS pikselidir)
          const ham = document.createElement("canvas");
          const k = ham.getContext("2d");
          k.font = `${w} ${px}px "${aile}"`;
          const g = Math.ceil(k.measureText(metin).width) + 4;
          ham.width = g; ham.height = Math.ceil(px * 1.8);
          const k2 = ham.getContext("2d");
          k2.fillStyle = bg; k2.fillRect(0, 0, ham.width, ham.height);
          k2.font = `${w} ${px}px "${aile}"`;
          k2.fillStyle = ink; k2.textBaseline = "alphabetic";
          k2.fillText(metin, 2, Math.round(px * 1.25));

          // 2) O rasteri KOMŞU-PİKSEL ile büyüt — yumuşatma KAPALI
          const bt = document.createElement("canvas");
          bt.width = ham.width * Z; bt.height = ham.height * Z;
          const kb = bt.getContext("2d");
          kb.imageSmoothingEnabled = false;
          kb.drawImage(ham, 0, 0, bt.width, bt.height);
          bt.style.width = bt.width + "px";
          host.appendChild(bt);
        }
      }
    }
  }
  document.title = "YAKINLASTIRMA TAMAM";
})();
