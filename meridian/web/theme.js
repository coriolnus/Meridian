/* ============================================================================
   MERIDIAN — TEMA ÖNYÜKLEYİCİSİ
   ----------------------------------------------------------------------------
   NEDEN AYRI VE HARİCİ BİR DOSYA:

   1. SIÇRAMA. Tema `<body>` boyanmadan ÖNCE seçilmek zorunda. Bu dosya
      `<head>` içinde SENKRON yüklenir (defer/async YOK) — yani ilk boyamada
      doğru zemin yerindedir. app.js'in sonuna konsaydı operatör her açılışta
      beyaz bir flaş görürdü; gece vardiyasında bu, karanlığa alışmış gözü
      resetleyen gerçek bir ergonomi hatasıdır — temanın var olma sebebini
      ortadan kaldırırdı.

   2. CSP. Dağıtım başlığı `script-src 'self'` — SATIR İÇİ SCRIPT YASAK.
      Bu yüzden bir `<script>…</script>` bloğu değil, kendi kaynağından
      yüklenen bir dosya. (Aynı sebeple landing/workflow'un satır içi blokları
      da dışarı taşındı; yoksa üretimde o iki sayfa ölü açılırdı.)

   3. ÜÇ YÜZEY TEK KAYNAK. index, landing ve workflow aynı tercihi okur.
      Tercih kopyalanırsa üçü ayrışır ve operatör aynı üründe iki dünya görür.

   SÖZLEŞME: bu dosya YALNIZ `data-theme` niteliğini ve tercihi yönetir.
   Renk DEĞERİ taşımaz — değerler CSS'te, jetonlarda yaşar. Bir rengi burada
   aramak zorunda kalıyorsan bir kural yanlış yerde yazılmış demektir.
   ============================================================================ */
(function () {
  "use strict";

  var ANAHTAR = "meridian-tema";
  var GUNDUZ = "gunduz";
  var GECE = "gece";
  var kok = document.documentElement;

  /* Kayıtlı tercih. Sadece iki değer meşrudur; localStorage elle kurcalanmış
     olabilir ve tanınmayan bir değer sessizce "tema yok" hâline düşmemeli. */
  function kayitli() {
    try {
      var v = localStorage.getItem(ANAHTAR);
      return v === GUNDUZ || v === GECE ? v : null;
    } catch (e) {
      /* Safari özel pencerede localStorage ERİŞİMDE atar, okumada değil.
         Tema kalıcılığı için bir oturumu çökertmek orantısız. */
      return null;
    }
  }

  function sistem() {
    try {
      return window.matchMedia("(prefers-color-scheme: dark)").matches ? GECE : GUNDUZ;
    } catch (e) {
      return GUNDUZ;
    }
  }

  /* GÜNDÜZ VARSAYILANDIR — ve bu bir tasarım hükmüdür, bir yedek değil.
     DESIGN.md § The Polarity-Honesty Rule: kanıt pozitif polarite LEHİNE
     (Piepenbrock 2013/14, okuma hızı ve doğruluğu). Gece zemini okunabilirlik
     için değil, 24/7 düşük-ışık ergonomisi için var. Bu yüzden sistem tercihi
     yalnız İLK ziyarette tohum olarak alınır; operatör bir kez seçim yaptıysa
     seçimi işletim sistemini yener. */
  function etkin() {
    return kayitli() || sistem();
  }

  function uygula(t) {
    kok.setAttribute("data-theme", t);
    /* Tarayıcı kendi çizdiklerini de bilsin: kaydırma çubuğu, form kontrolü,
       otomatik doldurma zemini. Bu satır olmadan gece temasında beyaz bir
       kaydırma çubuğu sayfanın kenarında parlar. */
    kok.style.colorScheme = t === GECE ? "dark" : "light";
  }

  uygula(etkin());

  /* Sistem teması değişirse (macOS gün batımı otomatiği) TAKİP ET — ama yalnız
     operatör henüz açık bir seçim yapmadıysa. Seçim yapılmışsa ona dokunmak,
     kullanıcının verdiği kararı geri almaktır. */
  try {
    var mq = window.matchMedia("(prefers-color-scheme: dark)");
    var dinle = function () { if (!kayitli()) uygula(sistem()); };
    if (mq.addEventListener) mq.addEventListener("change", dinle);
    else if (mq.addListener) mq.addListener(dinle);
  } catch (e) { /* matchMedia yoksa sabit tema; sessizce geç */ }

  window.MeridianTema = {
    al: etkin,
    koy: function (t) {
      if (t !== GUNDUZ && t !== GECE) return;
      uygula(t);
      try { localStorage.setItem(ANAHTAR, t); } catch (e) { /* bkz. kayitli() */ }
      /* Yüzeyler kendi düğmelerini güncelleyebilsin diye haber ver. Doğrudan
         DOM'a dokunmak yerine olay: bu dosya hangi yüzeyde olduğunu bilmez. */
      try {
        window.dispatchEvent(new CustomEvent("meridian:tema", { detail: { tema: t } }));
      } catch (e) { /* CustomEvent yoksa düğme etiketi bir tık geç güncellenir */ }
    },
    degistir: function () {
      window.MeridianTema.koy(etkin() === GECE ? GUNDUZ : GECE);
    }
  };
})();
