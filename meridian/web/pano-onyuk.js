/* ============================================================================
   MERIDIAN PANO — TERCİH ÖNYÜKLEYİCİSİ
   ----------------------------------------------------------------------------
   NEDEN AYRI VE HARİCİ BİR DOSYA — `theme.js` ile AYNI iki sebep:

   1. SIÇRAMA. Tema ve yerleşim `<body>` boyanmadan ÖNCE seçilmek zorunda. Bu
      dosya `<head>` içinde SENKRON yüklenir (defer/async YOK). Paket sonuna
      konsaydı operatör her açılışta beyaz bir flaş görürdü; gece vardiyasında
      bu, karanlığa alışmış gözü resetleyen gerçek bir ergonomi hatasıdır.

   2. CSP. Dağıtım başlığı `script-src 'self'` — SATIR İÇİ SCRIPT YASAK. Şablonun
      Next sürümü tam olarak bu işi satır içi bir <script> ile yapıyordu ve o
      blok üretimde bloklanırdı: sayfa açılır, teması yanlış olurdu. Hata yok,
      yanlış sonuç var — bu depoda en pahalı arıza sınıfı.

   NEDEN `theme.js` DEĞİL: `theme.js` iki değerli bir anahtar tutuyor
   (`data-theme` = gunduz|gece) ve üç eski yüzeyin sözleşmesi o. Yeni pano YEDİ
   tercih taşıyor (tema modu, ön ayar, yüz, içerik yerleşimi, üst bar davranışı,
   kenar çubuğu türü ve daralma kipi) ve bunları ÇEREZDEN okuyor — şablonun kendi
   deposu çereze yazıyor. İki dosya bilerek ayrı; ikisi de `data-theme`i aynı
   değerlerle yazar, böylece iki dünya arasında geçen operatör aynı temayı bulur.
   ============================================================================ */
(function () {
  "use strict";

  var kok = document.documentElement;

  /* Kayıt, `ui/src/lib/preferences/preferences-config.ts` ile AYNI olmak zorunda.
     Ayrışırsa: burada yazılmayan bir nitelik depo tarafından varsayılan sanılır ve
     operatörün kaydettiği tercih SESSİZCE her açılışta kaybolur. */
  var KAYIT = [
    ["theme_mode",          "data-theme-mode",          ["light", "dark", "system"],                 "light"],
    ["theme_preset",        "data-theme-preset",        ["default", "brutalist", "soft-pop", "tangerine"], "default"],
    ["font",                "data-font",                ["inter", "recursiveMono"],                  "inter"],
    ["content_layout",      "data-content-layout",      ["centered", "full-width"],                  "centered"],
    ["navbar_style",        "data-navbar-style",        ["sticky", "scroll"],                        "sticky"],
    ["sidebar_variant",     "data-sidebar-variant",     ["sidebar", "floating", "inset"],            "sidebar"],
    ["sidebar_collapsible", "data-sidebar-collapsible", ["icon", "offcanvas"],                       "icon"]
  ];

  function cerez(ad) {
    try {
      var parcalar = document.cookie ? document.cookie.split("; ") : [];
      for (var i = 0; i < parcalar.length; i++) {
        var e = parcalar[i].indexOf("=");
        if (e > 0 && decodeURIComponent(parcalar[i].slice(0, e)) === ad) {
          return decodeURIComponent(parcalar[i].slice(e + 1));
        }
      }
    } catch (e) {
      /* YASA 4 · sessiz-yutma İŞARETLİ: çerez okuması bazı gizlilik kiplerinde
         ERİŞİMDE atar. Tercih kalıcılığı için açılışı çökertmek orantısız olurdu;
         varsayılana düşmek görünür ve zararsız bir sonuç. */
    }
    return null;
  }

  function sistemGece() {
    try { return window.matchMedia("(prefers-color-scheme: dark)").matches; } catch (e) { return false; }
  }

  var modu = "light";
  for (var i = 0; i < KAYIT.length; i++) {
    var anahtar = KAYIT[i][0], nitelik = KAYIT[i][1], kume = KAYIT[i][2], varsayilan = KAYIT[i][3];
    var v = cerez(anahtar);
    /* TANINMAYAN DEĞER VARSAYILANA DÜŞER: çerez elle kurcalanmış olabilir ve
       `data-theme-preset="<script>"` gibi bir değeri niteliğe yazmak, seçici
       eşleşmese bile DOM'a saldırgan girdi koymak olurdu. */
    if (kume.indexOf(v) === -1) v = varsayilan;
    kok.setAttribute(nitelik, v);
    if (anahtar === "theme_mode") modu = v;
  }

  var gece = modu === "dark" || (modu === "system" && sistemGece());
  kok.classList.toggle("dark", gece);
  /* ESKİ YÜZEYLERLE KÖPRÜ: landing / workflow / runbook `data-theme`i okur ve
     değerleri "gunduz"/"gece"dir (theme.js:29-30) — "light"/"dark" DEĞİL. Yanlış
     değer yazmak niteliği doldurur ama eski CSS onu tanımaz: hata yok, tema yok. */
  kok.setAttribute("data-theme", gece ? "gece" : "gunduz");
  /* Tarayıcı kendi çizdiklerini de bilsin: kaydırma çubuğu, form kontrolü,
     otomatik doldurma zemini. Bu satır olmadan gece temasında beyaz bir kaydırma
     çubuğu sayfanın kenarında parlar. */
  kok.style.colorScheme = gece ? "dark" : "light";
})();
