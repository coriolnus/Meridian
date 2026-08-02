/* ============================================================================
   MERIDIAN — ⌘K KOMUT PALETİ
   ----------------------------------------------------------------------------
   NEDEN VAR: pano yedi görünüm, dört kademeli kriz kontrolü, iki onay kuyruğu ve
   yedi öğrenme eylemi taşıyor. Bunların hepsine ulaşmanın tek yolu FARE ile doğru
   kartı bulmaktı: "Şimdi düşün" Öğrenme'nin dibinde, "Cancel-Open" üst bardaki
   kapağın altında, "Uyarıları kapat" Bugün'ün ortasında. Operatör ne yapacağını
   biliyor ama NEREDE olduğunu hatırlamak zorunda kalıyordu. Palet bu yükü
   kaldırır: niyeti yaz, Enter.

   SÖZLEŞME — BU DOSYA TEK BAŞINA DURUR:
   1. CSS'İNİ KENDİ ENJEKTE EDER. index.html'e tek satırdan (script etiketi) fazla
      hiçbir şey eklemez; app.js'e hiç dokunmaz. Renk DEĞERİ taşımaz — yalnız
      mevcut jetonları (--card, --line, --tx, --accent, --red …) okur, yani tema
      değişiminde hiçbir şey yapmadan doğru boyanır. Bir hex kodu bu dosyada
      görünürse jeton sözleşmesi kırılmış demektir (testi var).
   2. YENİ AUTH İCAT ETMEZ. Yazma eylemleri app.js'in KENDİ global
      fonksiyonlarını çağırır (window.toggleHalt, window.opFlatten, …). Palet
      /api/halt'a doğrudan gitseydi token'ı ikinci bir yerden okumak zorunda
      kalırdı VE app.js'in süreç-içi `HALTED` bayrağı ile üst bardaki nabız
      15 saniyeye kadar YALAN söylerdi (refreshStatus 15 sn'de bir koşuyor).
      En yüksek bahisli eylemden hemen sonra başlığın gerçeği göstermemesi
      kabul edilemez; bu yüzden çağrı zinciri app.js'in kendi yolundan geçer.
   3. SATIR İÇİ İŞLEYİCİ YOK. Dağıtım CSP'si `script-src 'self'` — `onclick=`
      bloklanır. Tüm bağlama addEventListener ile yapılır. (app.js'in EYLEMLER
      izin listesi bu dosyanın DIŞINDA kalır: palet kendi düğmelerini kendi
      bağlar, `data-act` kullanmaz, yani o listeye dokunmaya gerek yoktur.)
   4. KOMUTLAR TÜRETİLİR, KOPYALANMAZ. Görünüm listesi kenar şeridinin
      `.sitem[data-p]` düğmelerinden, piyasa filtreleri `#mkt-chips`ten,
      HALT/DEVAM etiketi `#haltbtn`in kendi metninden okunur. Palet her AÇILIŞTA
      listeyi yeniden kurar — app.js bir görünüm eklerse palet onu ertesi
      açılışta zaten bilir.

   İKİ ADIMLI ONAY: yazan her komut Enter'da ÇALIŞMAZ; satır bir onay adımına
   döner ve ikinci, bilinçli bir Enter ister (tuş tekrarı — basılı tutma —
   ayrıca reddedilir). Klavyeyle sürülen bir yüzeyde tek Enter ile Flatten
   çalıştırmak, "hızlı" olmanın bedelini yanlış tarafa yazmak olurdu.

   BİLİNEN SINIR (uydurmamak için yazılıyor): ⌘/Ctrl+1-9 favori kısayolları
   YALNIZ palet AÇIKKEN dinlenir ve bazı tarayıcılarda (Chrome/Safari sekme
   değiştirme) işletim sistemi/tarayıcı bunu sayfaya hiç vermeyebilir. O durumda
   favori satırı bir ok tuşu uzaktadır — palet kırılmaz. Global olarak bağlamak
   ise sekme değiştirmeyi çalmak olurdu ve o bedel bu kazanca değmez.
   ============================================================================ */
(function () {
  "use strict";

  /* ==========================================================================
     BÖLÜM 1 — SAF ÇEKİRDEK
     DOM'a, window'a, ağa dokunmaz. Node ile doğrudan sınanır (bkz.
     tests/test_pano_palet_v152.py): bulanık skorlayıcının davranışı bir
     tarayıcı açmadan çivilenebilsin diye bilerek burada, ayrı tutuluyor.
     ========================================================================== */

  /* TÜRKÇE KATLAMA — klavyede Türkçe harf olmayabilir, ve olsa bile kimse
     "Öğrenme" yazmak için ö'yü aramaz. `toLowerCase()` TEK BAŞINA YETMEZ:
     "İ".toLowerCase() bileşik bir "i̇" (i + birleşen nokta) üretir ve o dizgi
     "i" ile eşleşmez — arama sessizce boş dönerdi. Bu yüzden katlama ÖNCE,
     küçültme SONRA. */
  var KATLAMA = {
    "İ": "I", "I": "I", "ı": "i", "Ş": "S", "ş": "s", "Ğ": "G", "ğ": "g",
    "Ü": "U", "ü": "u", "Ö": "O", "ö": "o", "Ç": "C", "ç": "c",
    "Â": "A", "â": "a", "Î": "I", "î": "i", "Û": "U", "û": "u"
  };
  function katla(s) {
    if (s == null) return "";
    var out = "";
    var t = String(s);
    for (var i = 0; i < t.length; i++) {
      var c = t[i];
      out += (KATLAMA[c] !== undefined ? KATLAMA[c] : c);
    }
    return out.toLowerCase();
  }

  /* Kelime sınırı: bu karakterlerden SONRA gelen harf yeni bir kelimenin başıdır
     ve baş harf eşleşmesi bir orta-kelime eşleşmesinden daha anlamlıdır
     ("kk" → "Kademe 2 · Cancel-Open" değil, "Kısayol Kaydı"). */
  var SINIR = /[\s·\-_/(),.'"⌘→⚠]/;

  /* BULANIK SKOR — alt dizi eşleşmesi + biçim ödülleri.
     Dönüş: eşleşme yoksa null (bir eşik değil, GERÇEK yokluk); varsa
     { skor, isaret } — `isaret` eşleşen harflerin hedefteki indisleridir ve
     vurgulamada birebir kullanılır, yani ekranda altı çizilen harf ile skoru
     üreten harf AYNIDIR (ikinci bir eşleştirici yok).
     Harici bağımlılık yok; ağırlıklar sabit ve testte çivili. */
  function bulanikSkor(hedef, sorgu) {
    var h = katla(hedef), s = katla(sorgu);
    if (!s) return { skor: 0, isaret: [] };   // boş sorgu HER ŞEYLE eşleşir (sıralama geçmişe kalır)
    if (!h) return null;
    var isaret = [], skor = 0, imlec = 0, onceki = -2;
    for (var si = 0; si < s.length; si++) {
      var c = s[si], bulundu = -1;
      for (var k = imlec; k < h.length; k++) { if (h[k] === c) { bulundu = k; break; } }
      if (bulundu < 0) return null;           // bir harf bile düşerse eşleşme YOK
      var bitisik = bulundu === onceki + 1;
      var sinirda = bulundu === 0 || SINIR.test(h[bulundu - 1]);
      skor += 3;
      if (bitisik) skor += 12;                // bitişiklik en güçlü sinyal: yazdığın gibi duruyor
      if (sinirda) skor += 9;                 // kelime başı: baş harf kısaltmaları çalışsın
      if (!bitisik && !sinirda) skor -= Math.min(6, (bulundu - onceki - 1) * 0.4);
      isaret.push(bulundu);
      onceki = bulundu; imlec = bulundu + 1;
    }
    if (isaret[0] === 0) skor += 18;          // baştan başlayan eşleşme
    if (h.indexOf(s) === 0) skor += 12;       // gerçek ön ek
    skor -= Math.min(10, h.length * 0.2);     // eşitlikte KISA hedef kazanır
    return { skor: skor, isaret: isaret };
  }

  /* Komut skoru: ad > anahtar kelimeler > altyazı. Vurgulama YALNIZ ad
     eşleştiğinde üretilir — altyazıdan gelen bir eşleşmeyi adın harflerinin
     altını çizerek göstermek, okuyucuya neyin eşleştiği konusunda yalan söyler. */
  function komutSkoru(k, sorgu) {
    var a = bulanikSkor(k.ad, sorgu);
    if (a) return { skor: a.skor, isaret: a.isaret };
    var en = null;
    var anahtarlar = k.anahtarlar || [];
    for (var i = 0; i < anahtarlar.length; i++) {
      var r = bulanikSkor(anahtarlar[i], sorgu);
      if (r && (!en || r.skor > en.skor)) en = r;
    }
    if (en) return { skor: en.skor * 0.8, isaret: [] };
    var b = k.altyazi ? bulanikSkor(k.altyazi, sorgu) : null;
    if (b) return { skor: b.skor * 0.55, isaret: [] };
    return null;
  }

  var SON_GRUP = "Son kullanılan";
  var GRUP_SIRA = ["Gezinme", "Müdahale", "Onay kuyruğu", "Öğrenme", "Görünüm", "Yardımcı"];

  function gecmisHarita(gecmis) {
    var m = {};
    (gecmis || []).forEach(function (x, i) {
      if (x && x.id && m[x.id] === undefined) m[x.id] = { sira: i, n: Number(x.n) || 1 };
    });
    return m;
  }

  /* SIRALAMA — tek çıktı biçimi: [{komut, skor, isaret, grup, favori}].
     `grup` null ise çizici başlık basmaz (arama sonucunda gruplama sırayı
     parçalar; sıralanmış bir listeyi başlıklara bölmek en iyi eşleşmeyi
     üçüncü başlığın altına gömerdi).
     `favori` 1-9 arası ise satır ⌘N ile doğrudan çalıştırılabilir. */
  function sirala(komutlar, sorgu, gecmis) {
    var g = gecmisHarita(gecmis), q = katla(sorgu), out = [];
    if (!q) {
      var son = komutlar.filter(function (k) { return g[k.id]; })
        .sort(function (a, b) { return g[a.id].sira - g[b.id].sira; })
        .slice(0, 9);
      var sonId = {};
      son.forEach(function (k, i) {
        sonId[k.id] = true;
        out.push({ komut: k, skor: 0, isaret: [], grup: SON_GRUP, favori: i + 1 });
      });
      GRUP_SIRA.forEach(function (grp) {
        komutlar.forEach(function (k) {
          if (k.grup === grp && !sonId[k.id]) out.push({ komut: k, skor: 0, isaret: [], grup: grp, favori: 0 });
        });
      });
      // Bilinmeyen gruba düşen bir komut SESSİZCE KAYBOLMAZ — listenin sonuna gelir.
      komutlar.forEach(function (k) {
        if (!sonId[k.id] && GRUP_SIRA.indexOf(k.grup) < 0) out.push({ komut: k, skor: 0, isaret: [], grup: k.grup || "Diğer", favori: 0 });
      });
      return out;
    }
    komutlar.forEach(function (k) {
      var r = komutSkoru(k, sorgu);
      if (!r) return;
      var ek = 0, gk = g[k.id];
      if (gk) ek = (gk.sira < 9 ? 6 : 2) + 2 * Math.min(gk.n, 4);   // son kullanılan öne çıkar
      out.push({ komut: k, skor: r.skor + ek, isaret: r.isaret, grup: null, favori: 0 });
    });
    out.sort(function (a, b) {
      return (b.skor - a.skor) || a.komut.ad.localeCompare(b.komut.ad, "tr");
    });
    return out;
  }

  /* Geçmiş: en son kullanılan başa, tekrar YOK, 24 kayıtla sınırlı.
     Sayaç (`n`) korunur — "sık" ile "son" ayrı sinyaller ve sıralama ikisini de
     kullanıyor; her çalıştırmada sayacı sıfırlamak sık kullanılanı öldürürdü. */
  function gecmisiGuncelle(gecmis, id, simdi) {
    var liste = (gecmis || []).filter(function (x) { return x && x.id; });
    var mevcut = null;
    for (var i = 0; i < liste.length; i++) { if (liste[i].id === id) { mevcut = liste[i]; break; } }
    var kalan = liste.filter(function (x) { return x.id !== id; });
    return [{ id: id, n: ((mevcut && Number(mevcut.n)) || 0) + 1, t: simdi }].concat(kalan).slice(0, 24);
  }

  var CEKIRDEK = {
    katla: katla, bulanikSkor: bulanikSkor, komutSkoru: komutSkoru,
    sirala: sirala, gecmisiGuncelle: gecmisiGuncelle,
    SON_GRUP: SON_GRUP, GRUP_SIRA: GRUP_SIRA
  };

  /* Node testi için dışa aktarım. Tarayıcıda `module` tanımsızdır → dal hiç
     çalışmaz, global kirletilmez. */
  if (typeof module !== "undefined" && module.exports) module.exports = CEKIRDEK;

  /* Tarayıcı yoksa (test koşumu) bölüm 2 hiç kurulmaz. */
  if (typeof document === "undefined" || typeof window === "undefined") return;
  window.MeridianPalet = CEKIRDEK;   // konsoldan denetlenebilsin

  /* ==========================================================================
     BÖLÜM 2 — TARAYICI KATMANI
     ========================================================================== */

  var ID_KOK = "mrdp-kok", ID_GIRIS = "mrdp-giris", ID_LISTE = "mrdp-liste";
  var GECMIS_ANAHTAR = "meridian-palet-gecmis";
  var MAC = /Mac|iPhone|iPad|iPod/.test((navigator.platform || "") + " " + (navigator.userAgent || ""));
  var MOD = MAC ? "⌘" : "Ctrl+";

  /* ---- kalıcılık: theme.js'in deseni. Safari özel penceresinde localStorage
     ERİŞİMDE atar; bir kısayol geçmişi için oturumu çökertmek orantısız. ---- */
  function gecmisOku() {
    try {
      var v = JSON.parse(localStorage.getItem(GECMIS_ANAHTAR) || "[]");
      return Array.isArray(v) ? v : [];
    } catch (e) { return []; }
  }
  function gecmisYaz(v) {
    try { localStorage.setItem(GECMIS_ANAHTAR, JSON.stringify(v)); } catch (e) { /* bkz. gecmisOku */ }
  }

  function el(id) { return document.getElementById(id); }
  function hazir(ad) { return typeof window[ad] === "function"; }
  function aktifGorunum() {
    var s = document.querySelector(".sitem.on");
    if (s && s.dataset.p) return s.dataset.p;
    var h = (location.hash || "").slice(1);
    /* Son çare AÇILIŞ SAYFASIDIR ve o sayfa S2R-1'de "genel" oldu (app.js VARSAYILAN_ROTA).
       Eski ad burada kalsaydı yalnız bu dalda — ne ray çizilmiş ne hash yazılmış anın
       içinde — palet "yenile"yi yanlış sayfaya uygulardı: nadir, sessiz ve teşhisi zor. */
    return h || "genel";
  }
  /* Bir eylemi çalıştırmadan ÖNCE ilgili görünüme geç. Sebep ölçüldü, tercih
     değil: app.js'in eylemleri sonuçlarını sayfaya ait bir düğüme yazıyor
     (hermesReflect → #hbtn-msg, notifyTest → #ntf-msg, ackAlerts → #bp-alerts).
     O sayfa çizilmemişken çağrı POST'u yine atar ama SONUCU HİÇBİR YERDE
     GÖRÜNMEZ — sessiz bir yazma işlemi. Ayrıca sprintStart girdi kutularını
     (#sprint-budget/#sprint-kmax) okuyor: sayfa yokken operatörün girdiği
     değerleri değil varsayılanları kullanırdı. */
  function gorunumeGec(id) {
    if (!id || !hazir("go")) return Promise.resolve();
    try { return Promise.resolve(window.go(id)); } catch (e) { return Promise.resolve(); }
  }

  /* ---- CSS: JS'ten enjekte, ama DEĞER TAŞIMAZ — yalnız mevcut jetonlar ----
     Palet gri-önceliklidir: vurgulama altı çizgi + ağırlık ile yapılır, renkle
     değil. Renk yalnız İKİ yerde: yazan komutun kehribar rozeti ve yıkıcı onay
     adımının kırmızı kenarı — ikisi de sonuç uyarısı, dekorasyon değil. */
  function stilEnjekteEt() {
    if (el("mrdp-stil")) return;
    var st = document.createElement("style");
    st.id = "mrdp-stil";
    st.textContent = [
      ".mrdp-ov{position:fixed;inset:0;z-index:120;background:var(--scrim);backdrop-filter:blur(4px);",
      "  display:grid;align-items:start;justify-items:center;padding:12vh var(--s4) var(--s4)}",
      ".mrdp-panel{width:min(640px,100%);max-height:74vh;display:flex;flex-direction:column;",
      "  background:var(--card);border:1px solid var(--line-2);border-radius:var(--r-card);overflow:hidden;box-shadow:var(--elev)}",
      ".mrdp-bar{display:flex;align-items:center;gap:var(--s3);padding:var(--s3) var(--s4);border-bottom:1px solid var(--line-2);background:var(--bg2)}",
      ".mrdp-mark{font-family:var(--mono);font-size:var(--label-size);letter-spacing:var(--label-track);",
      "  text-transform:uppercase;color:var(--tx2);white-space:nowrap}",
      ".mrdp-giris{flex:1;min-width:0;border:0;background:transparent;color:var(--tx);font-family:var(--sans);",
      "  font-size:15px;min-height:36px;padding:0;outline:none}",
      ".mrdp-giris::placeholder{color:var(--tx2)}",
      ".mrdp-liste{list-style:none;margin:0;padding:0 0 var(--s2);overflow-y:auto;overscroll-behavior:contain}",
      ".mrdp-grp{font-family:var(--mono);font-size:var(--label-size);letter-spacing:var(--label-track);",
      "  text-transform:uppercase;color:var(--tx2);padding:var(--s4) var(--s4) var(--s2);",
      "  border-top:1px solid var(--line)}",
      ".mrdp-liste>.mrdp-grp:first-child{border-top:0;padding-top:var(--s3)}",
      ".mrdp-opt{display:grid;grid-template-columns:1fr auto;gap:var(--s3);align-items:center;",
      "  padding:9px var(--s4);cursor:pointer;border-left:2px solid transparent}",
      ".mrdp-opt[aria-selected=\"true\"]{background:var(--accent-tint);border-left-color:var(--accent)}",
      ".mrdp-opt.pasif{opacity:.5;cursor:not-allowed}",
      ".mrdp-ad{font-size:13.5px;font-weight:500;color:var(--tx);line-height:1.35}",
      ".mrdp-ad em{font-style:normal;font-weight:700;text-decoration:underline;text-underline-offset:2px;text-decoration-thickness:1px}",
      ".mrdp-alt{display:block;font-size:11.5px;color:var(--tx2);font-weight:400;margin-top:2px;line-height:1.35}",
      ".mrdp-sag{display:flex;align-items:center;gap:var(--s2);white-space:nowrap}",
      ".mrdp-yaz{font-family:var(--mono);font-size:10px;letter-spacing:.08em;text-transform:uppercase;",
      "  color:var(--amber);border:1px solid var(--amber-h);border-radius:var(--r-bar);padding:1px 5px}",
      ".mrdp-ipucu{font-family:var(--mono);font-size:11px;color:var(--tx2);border:1px solid var(--line-2);",
      "  border-radius:var(--r-bar);padding:1px 6px;background:var(--bg2)}",
      ".mrdp-bos{padding:var(--s6) var(--s4);color:var(--tx2);font-size:13px;text-align:center}",
      ".mrdp-alt-bar{display:flex;gap:var(--s4);flex-wrap:wrap;padding:var(--s2) var(--s4);",
      "  border-top:1px solid var(--line-2);background:var(--bg2);font-family:var(--mono);font-size:11px;color:var(--tx2)}",
      /* --- iki adımlı onay --- */
      /* tehlike çerçevesi: İNCE ve dört-kenar — kalın tek-kenar şerit jenerik/AI-tell (tasarım
         bekçisi bulgusu 2026-08-01); tehlike semantiği çerçeve+`.uyari` metniyle korunur */
      ".mrdp-onay{padding:var(--s5) var(--s4);border:1px solid var(--red);border-radius:var(--r-card)}",
      ".mrdp-onay h3{font-size:14px;font-weight:700;color:var(--tx);margin:0 0 var(--s2)}",
      ".mrdp-onay p{font-size:12.5px;color:var(--tx2);margin:0 0 var(--s3);line-height:1.45}",
      ".mrdp-onay .uyari{color:var(--red)}",
      ".mrdp-dugmeler{display:flex;gap:var(--s2);flex-wrap:wrap}",
      ".mrdp-btn{font-family:var(--sans);font-size:13px;font-weight:600;min-height:40px;padding:8px 15px;",
      "  border-radius:var(--r-ctl);border:1px solid var(--line-2);background:transparent;color:var(--tx);cursor:pointer}",
      ".mrdp-btn:hover{border-color:var(--accent);background:var(--accent-tint)}",
      ".mrdp-btn.tehlike{border-color:var(--red);color:var(--red)}",
      ".mrdp-btn.tehlike:hover{background:var(--red-t)}",
      ".mrdp-btn:focus-visible{outline:2px solid var(--accent);outline-offset:2px}",
      "@media(max-width:640px){.mrdp-ov{padding:6vh var(--s2) var(--s2)}.mrdp-panel{max-height:86vh}}"
    ].join("\n");
    document.head.appendChild(st);
  }

  /* ==========================================================================
     KOMUT ENVANTERİ — mevcut yüzeylerden türetilir
     ========================================================================== */

  /* Piyasa filtre anahtarları app.js'teki `_MKT_CHIPS` ile aynı dört anahtardır.
     Etiket CANLI okunur (#mkt-chips düğmesinin kendi metni, sayısıyla birlikte);
     aşağıdaki yazı yalnız sayfa HİÇ açılmamışken kullanılan yedektir. Yedek
     olmasaydı komutlar Piyasa bir kez çizilene kadar palette hiç görünmezdi —
     keşfedilebilirlik, tam da paletin var olma sebebi. */
  var MKT_YEDEK = { position: "Pozisyonda", armed: "Silahlı", plan: "Planı var", earn: "Earnings ≤7g" };

  function komutlariKur() {
    var K = [], i;

    /* ---- (a) BÖLÜM GEZİNMESİ — kenar şeridinden TÜRETİLİR ---------------- */
    var raylar = [].slice.call(document.querySelectorAll('.sitem[data-p]'));
    raylar.forEach(function (b, n) {
      var id = b.dataset.p;
      var adEl = b.querySelector(".vis-label"), subEl = b.querySelector(".sub");
      var ad = (adEl ? adEl.textContent : id) || id;
      K.push({
        id: "git:" + id, grup: "Gezinme", ad: ad,
        altyazi: subEl ? subEl.textContent : "",
        /* app.js çıplak 1-9 tuşlarını VIEWS sırasına bağlıyor; şerit de aynı
           sıradan kuruluyor, yani bu ipucu uydurma değil aynı kaynağın okunuşu. */
        ipucu: n < 9 ? String(n + 1) : "",
        anahtarlar: [id, "git", "gorunum", "sayfa"],
        yazma: false,
        calistir: function () { return gorunumeGec(id); }
      });
    });
    /* ŞERİT HENÜZ KURULMADIYSA BOŞLUK SESSİZ KALMAZ. Kenar şeridi /api/today
       geldikten sonra çiziliyor; ilk saniyede palet açılırsa gezinme komutları
       DOM'da yok demektir. Listeyi sessizce kısaltmak "böyle bir şey yok" demek
       olurdu — satır kalır, pasif çizilir ve nedenini söyler. */
    if (!raylar.length) {
      K.push({
        id: "git:bekliyor", grup: "Gezinme", ad: "Görünümler",
        anahtarlar: ["git", "gorunum", "sayfa"],
        yazma: false,
        pasif: "kenar şeridi henüz kurulmadı (ilk sunucu yanıtı bekleniyor) — paleti bir saniye sonra tekrar aç"
      });
    }

    /* BÖLÜM ÇAPALARI (S2R-2). S2R-1'de tek gerçek çapa `#failsub`ti ve o da eski
       `operasyon` görünümüne bağlıydı; içerik göçüyle ret defteri Portföy'ün
       `mutabakat` bölümüne taşındı. Artık her bölüm başlığı bir çapa taşıyor
       (`bolumBasHTML` → `id="<bolum>"`), yani palet sayfanın TEPESİNE değil
       aranan bölüme götürebiliyor. Uydurulmuş çapa YOK: her biri app.js'te
       gerçekten üretilen bir id. */
    if (el("page-mutabakat")) {
      K.push({
        id: "git:failsub", grup: "Gezinme", ad: "Reddedilen emirler",
        altyazi: "Portföy & Emirler → mutabakat masası → ret kaydı bloğuna kaydır ve odakla",
        anahtarlar: ["ret", "reject", "broker", "emir", "hata", "mutabakat"],
        yazma: false,
        calistir: function () { return gorunumeGec("portfoy#failsub"); }
      });
    }
    [["karne", "ogrenme", "Karne — öğreniyor mu?", ["karne", "ogrenme", "skor", "hukum"]],
     ["kapilar", "kosu", "Disiplin kapısı — karar ağacı", ["kapi", "gate", "karar", "matris", "eleme"]],
     ["mudahale", "kilitler", "Müdahale kademeleri", ["kademe", "kol", "halt", "mudahale", "kilit"]],
     ["intraemir", "portfoy", "Seans-içi silahlanma · gölge icra", ["intraday", "golge", "silah", "arm"]],
     ["veriboru", "veri", "Veri hattı · karantina · bütünlük", ["karantina", "butunluk", "veri", "hat"]]
    ].forEach(function (r) {
      if (!el("page-" + r[0])) return;
      K.push({
        id: "git:" + r[0], grup: "Gezinme", ad: r[2],
        altyazi: "Bölüm çapasına gider ve odaklar.",
        anahtarlar: r[3].concat(["bolum"]),
        yazma: false,
        calistir: function () { return gorunumeGec(r[1] + "#" + r[0]); }
      });
    });

    /* ---- (b) KİLİT / MÜDAHALE — hepsi app.js'in kendi eylemleri ---------- */
    var halt = el("haltbtn");
    var haltEtiketi = halt ? (halt.textContent || "").trim() : "";   // "HALT" | "DEVAM" — CANLI
    K.push({
      id: "act:halt", grup: "Müdahale",
      ad: haltEtiketi === "DEVAM" ? "DEVAM — yeni alımlara tekrar izin ver" : "HALT — acil durdur",
      altyazi: haltEtiketi === "DEVAM"
        ? "Sistem şu an DURDURULMUŞ. Bu komut yeni emir girişini geri açar."
        : "Bir sonraki muma kadar YENİ hiçbir alım yapılmaz; açık pozisyonlar yönetilmeye devam eder.",
      anahtarlar: ["halt", "durdur", "acil", "stop", "devam", "resume", "panik"],
      yazma: true, tehlike: true, yerliOnay: haltEtiketi !== "DEVAM",
      fn: "toggleHalt"
    });
    K.push({
      id: "act:soft", grup: "Müdahale", ad: "Kademe 1 · Soft Halt",
      altyazi: "Yeni emir girişi durur; mevcut pozisyonlar yönetilmeye devam eder.",
      anahtarlar: ["kademe", "soft", "halt", "1", "giris"],
      yazma: true, tehlike: true, yerliOnay: true, gorunum: "kilitler#mudahale", fn: "opSoftHalt"
    });
    K.push({
      id: "act:cancel", grup: "Müdahale", ad: "Kademe 2 · Cancel-Open",
      altyazi: "Yalnız DOLMAMIŞ giriş emirleri iptal edilir; koruyucu stop/hedef bacaklarına dokunulmaz.",
      anahtarlar: ["kademe", "cancel", "iptal", "2", "emir"],
      yazma: true, tehlike: true, yerliOnay: true, gorunum: "kilitler#mudahale", fn: "opCancelOpen"
    });
    K.push({
      id: "act:flatten", grup: "Müdahale", ad: "Kademe 3 · FLATTEN — tüm pozisyonlar",
      altyazi: "Alpaca paper hesabındaki TÜM pozisyonlar piyasadan kapatılır, tüm emirler iptal edilir. Elle açtığın pozisyonlar dahil. Geri alınamaz.",
      anahtarlar: ["kademe", "flatten", "kapat", "3", "pozisyon", "hepsi"],
      yazma: true, tehlike: true, yerliOnay: true, gorunum: "kilitler#mudahale", fn: "opFlatten"
    });
    K.push({
      id: "act:learnhalt", grup: "Müdahale", ad: "Kademe 4 · Halt Learning",
      altyazi: "İşlemler DEVAM eder; Hermes yeni strateji versiyonu ship EDEMEZ. Rollback açık kalır.",
      anahtarlar: ["kademe", "learning", "ogrenme", "ship", "4"],
      yazma: true, tehlike: true, yerliOnay: true, gorunum: "kilitler#mudahale", fn: "opLearnHaltToggle"
    });
    /* INTRADAY SİLAHLAMA — durumu BİLMEDEN çalıştırılmaz. Düğme yalnız Intraday
       çizildiğinde DOM'da olur ve `data-a1` o an hangi yöne gidileceğini taşır.
       Sayfa çizilmemişken `intradayArm(true)` demek, zaten silahlıyken tekrar
       silahlamak (ya da tersini) demektir — palet tahmin etmez, götürür. */
    var armBtn = document.querySelector('#page-intraemir [data-act="intradayArm"]');
    if (armBtn) {
      /* `data-a1` düğmenin GİDECEĞİ yönü taşır: "true" = şu an silahsız, komut açacak.
         Değişken adı `ac` OLAMAZ — bu kapsamda paleti açan `ac()` fonksiyonunu gölgeler. */
      var acacak = armBtn.dataset.a1 === "true";
      K.push({
        id: "act:arm", grup: "Müdahale",
        ad: acacak ? "Intraday silahlamayı AÇ" : "Intraday silahlamayı KAPAT (gözleme dön)",
        altyazi: acacak ? "Otonom intraday emir kapısını kaldıran hazırlık bayrağı. Faz 4b yok — şu an emir göndermez."
                        : "Gözlem-moduna döner: yalnız ölçüm, emir yok.",
        anahtarlar: ["intraday", "arm", "silah", "gozlem"],
        yazma: true, tehlike: true, yerliOnay: acacak, gorunum: "portfoy#intraemir",
        fn: "intradayArm", arg: acacak
      });
    } else {
      K.push({
        id: "act:arm-git", grup: "Müdahale", ad: "Intraday silahlama düğmesine git",
        altyazi: "Silahlama durumu yalnız Intraday çizildiğinde okunabilir — palet tahmin etmez, seni oraya götürür.",
        anahtarlar: ["intraday", "arm", "silah", "gozlem"],
        yazma: false,
        calistir: function () { return gorunumeGec("portfoy#intraemir"); }
      });
    }

    /* ---- ONAY KUYRUKLARI ------------------------------------------------- */
    K.push({
      id: "act:ackalerts", grup: "Onay kuyruğu", ad: "Uyarıları okundu işaretle",
      altyazi: "Bugün → uyarı gelen kutusu; sunucu sınırı yeniden çekilir.",
      anahtarlar: ["uyari", "alert", "ack", "okundu", "gelen kutusu"],
      yazma: true, gorunum: "gozetim", fn: "ackAlerts"
    });
    K.push({
      id: "act:ackrejects", grup: "Onay kuyruğu", ad: "Tüm reddedilen emirleri kapat",
      altyazi: "Açık broker retlerinin tamamı kapatılır; şerit uyarısı düşer.",
      anahtarlar: ["ret", "reject", "kapat", "ack", "broker"],
      yazma: true, gorunum: "portfoy#failsub", fn: "ackRejectAll"
    });

    /* ---- ÖĞRENME --------------------------------------------------------- */
    K.push({
      id: "act:reflect", grup: "Öğrenme", ad: "Hermes: şimdi düşün",
      altyazi: "Koordinat-iniş araması başlatır (dakikalar sürer); tüm düğmeler aynı OOS kapısından geçer.",
      anahtarlar: ["hermes", "dusun", "reflect", "arama", "beyin"],
      yazma: true, gorunum: "ogrenme#hermes", fn: "hermesReflect"
    });
    K.push({
      id: "act:backfill", grup: "Öğrenme", ad: "Hermes: görüş dolgusu (backfill)",
      altyazi: "Arka planda geçmiş görüş biriktirir; kalibrasyon güncellendikçe karnede görünür.",
      anahtarlar: ["backfill", "dolgu", "gorus", "kalibrasyon"],
      yazma: true, gorunum: "ogrenme#hermes", fn: "hermesBackfill"
    });
    K.push({
      id: "act:sprintstart", grup: "Öğrenme", ad: "Antrenman sprinti başlat",
      altyazi: "Bütçe ve K-max değerleri Öğrenme sayfasındaki kutulardan okunur — bu yüzden komut önce oraya götürür.",
      anahtarlar: ["sprint", "antrenman", "basla", "train"],
      yazma: true, gorunum: "ogrenme#hermes", fn: "sprintStart"
    });
    K.push({
      id: "act:sprintstop", grup: "Öğrenme", ad: "Antrenman sprintini durdur",
      altyazi: "Koşan sprinti keser.",
      anahtarlar: ["sprint", "durdur", "stop"],
      yazma: true, gorunum: "ogrenme#hermes", fn: "sprintStop"
    });

    /* ---- (c) GÖRÜNÜM FİLTRELERİ — mevcut çip mekanizması ----------------- */
    Object.keys(MKT_YEDEK).forEach(function (anahtar) {
      var cip = document.querySelector('#mkt-chips [data-act="mktChip"][data-a1="' + anahtar + '"]');
      var etiket = cip ? (cip.textContent || "").trim() : MKT_YEDEK[anahtar];
      var acik = cip ? cip.getAttribute("aria-pressed") === "true" : null;
      K.push({
        id: "flt:" + anahtar, grup: "Görünüm",
        ad: "Piyasa filtresi · " + etiket,
        altyazi: acik === null ? "Piyasa henüz çizilmedi — komut önce oraya gider, sonra filtreyi açar."
                               : (acik ? "Şu an AÇIK — bu komut filtreyi kaldırır." : "Şu an kapalı — bu komut filtreyi uygular."),
        anahtarlar: ["piyasa", "filtre", "market", anahtar],
        yazma: false,
        calistir: function () {
          return gorunumeGec("market").then(function () {
            if (hazir("mktChip")) window.mktChip(anahtar);
          });
        }
      });
    });
    K.push({
      id: "fok:mkt", grup: "Görünüm", ad: "Piyasa'da hisse ara",
      altyazi: "Piyasa'ya geçer ve arama kutusuna odaklanır.",
      anahtarlar: ["ara", "hisse", "ticker", "piyasa", "search"],
      yazma: false,
      calistir: function () {
        return gorunumeGec("market").then(function () { odakla("mkt-q"); });
      }
    });
    K.push({
      id: "fok:ders", grup: "Görünüm", ad: "Derslerde ara",
      altyazi: "Öğrenme'ye geçer ve ders arama kutusuna odaklanır.",
      anahtarlar: ["ders", "lesson", "ara", "ogrenme"],
      yazma: false,
      calistir: function () {
        return gorunumeGec("ogrenme#hafiza").then(function () { odakla("lsearch"); });
      }
    });

    /* ---- (d) YARDIMCILAR ------------------------------------------------- */
    K.push({
      id: "yrd:yenile", grup: "Yardımcı", ad: "Panoyu yenile",
      altyazi: "Açık görünümü yeniden çizer (aynı iş: R tuşu).",
      ipucu: "R",
      anahtarlar: ["yenile", "refresh", "tazele", "reload"],
      yazma: false,
      calistir: function () { return gorunumeGec(aktifGorunum()); }
    });
    K.push({
      id: "yrd:tema", grup: "Yardımcı",
      ad: (window.MeridianTema && window.MeridianTema.al() === "gece") ? "Gündüz temasına geç" : "Gece temasına geç",
      altyazi: "Tercih kaydedilir ve üç yüzeyde (pano, landing, workflow) birlikte döner.",
      anahtarlar: ["tema", "theme", "gece", "gunduz", "dark", "light"],
      yazma: false,
      calistir: function () { if (hazir("temaDegistir")) window.temaDegistir(); }
    });
    K.push({
      id: "yrd:kbd", grup: "Yardımcı", ad: "Kısayol haritası",
      altyazi: "Sayfa haritası + tuş listesi.",
      ipucu: "?",
      anahtarlar: ["kisayol", "klavye", "yardim", "help", "tus"],
      yazma: false,
      calistir: function () { if (hazir("kbdOverlay")) window.kbdOverlay(true); }
    });
    /* RUNBOOK ARTIK GERÇEK HEDEFİNE GİDİYOR (UIUX S1-T3, 2026-08-01).
       Bu satır bir süre "Karar hattı şeması (runbook)" adıyla /workflow'a gidiyordu — çünkü
       runbook diye bir yüzey YOKTU ve palet operatöre var olmayan bir şeyi vaat edemezdi;
       en yakın akrabasına bağlamak zorunda kalmıştı. `docs/RUNBOOK.md` + `/runbook` ile o
       zorunluluk bitti. İki komut artık AYRI ve adları ne olduklarını söylüyor: biri AKIŞ
       şeması (sistem nasıl çalışır), diğeri TEŞHİS belgesi (bozulunca ne yapılır). */
    K.push({
      id: "yrd:runbook", grup: "Yardımcı", ad: "Runbook · teşhis belgesi",
      altyazi: "/runbook — alarm → belirti → teşhis → çözüm. docs/RUNBOOK.md'nin okuyucusu; panodan AYRILIR.",
      anahtarlar: ["runbook", "teshis", "alarm", "bekci", "mekanizma", "nabiz", "ne yapmali"],
      yazma: false,
      calistir: function () { location.href = "/runbook"; }
    });
    K.push({
      id: "yrd:workflow", grup: "Yardımcı", ad: "Karar hattı şeması",
      altyazi: "/workflow — günlük karar hattının uçtan uca akışı. Panodan AYRILIR.",
      anahtarlar: ["workflow", "akis", "sema", "karar hatti", "diyagram"],
      yazma: false,
      calistir: function () { location.href = "/workflow"; }
    });
    K.push({
      id: "yrd:landing", grup: "Yardımcı", ad: "Tanıtım sayfası",
      altyazi: "/landing — sistemin dışa dönük anlatımı. Panodan AYRILIR.",
      anahtarlar: ["landing", "tanitim", "anasayfa"],
      yazma: false,
      calistir: function () { location.href = "/landing"; }
    });
    if (el("cikis-btn")) {
      K.push({
        id: "act:cikis", grup: "Yardımcı", ad: "Çıkış yap",
        altyazi: "Oturumu kapatır; önbellek ve kayıt defteri temizlenir.",
        anahtarlar: ["cikis", "logout", "oturum"],
        yazma: true, fn: "cikisYap"
      });
    }

    /* İMKÂNSIZ KOMUT SESSİZCE DURMAZ: app.js yüklenmediyse ya da bir eylem adı
       kaybolduysa satır listede KALIR, ama pasif çizilir ve NEDENİNİ söyler.
       Listeden düşürmek, operatöre "böyle bir şey yok" demek olurdu. */
    for (i = 0; i < K.length; i++) {
      var k = K[i];
      if (k.pasif) continue;                 // kendi sebebini taşıyan satır EZİLMEZ
      if (k.fn && !hazir(k.fn)) { k.pasif = "app.js yüklenmedi — `" + k.fn + "` tanımsız"; }
      else if (!k.fn && !k.calistir) { k.pasif = "eylem bağlanmadı"; }
    }
    return K;
  }

  function odakla(id) {
    var e = el(id);
    if (e && typeof e.focus === "function") { e.focus(); if (typeof e.select === "function") e.select(); }
  }

  /* ==========================================================================
     DURUM + ÇİZİM
     ========================================================================== */

  var KOK = null, GIRIS = null, LISTE = null;
  var KOMUTLAR = [], SATIRLAR = [], SECILI = 0, ONAY = null, ONCEKI_ODAK = null;

  function acikMi() { return !!KOK; }

  /* Giriş kapısı açıkken palet AÇILMAZ: oturum yokken paletteki her komut
     401 alırdı ve operatör bunu bir arıza sanırdı. */
  function kapiAcik() {
    var g = el("gate");
    return !!(g && !g.hasAttribute("hidden"));
  }

  function vurgula(kap, metin, isaret) {
    var im = {}, i;
    (isaret || []).forEach(function (x) { im[x] = true; });
    var tampon = "", vurguluMu = false;
    function bosalt() {
      if (!tampon) return;
      if (vurguluMu) { var b = document.createElement("em"); b.textContent = tampon; kap.appendChild(b); }
      else kap.appendChild(document.createTextNode(tampon));
      tampon = "";
    }
    for (i = 0; i < metin.length; i++) {
      var v = !!im[i];
      if (v !== vurguluMu) { bosalt(); vurguluMu = v; }
      tampon += metin[i];
    }
    bosalt();
  }

  function listeyiCiz() {
    LISTE.textContent = "";
    SATIRLAR = [];
    var sonuc = sirala(KOMUTLAR, GIRIS.value, gecmisOku());
    if (!sonuc.length) {
      var bos = document.createElement("li");
      bos.className = "mrdp-bos";
      bos.textContent = "eşleşme yok";
      LISTE.appendChild(bos);
      GIRIS.removeAttribute("aria-activedescendant");
      return;
    }
    var sonGrup = null;
    sonuc.forEach(function (kayit, n) {
      if (kayit.grup && kayit.grup !== sonGrup) {
        sonGrup = kayit.grup;
        var g = document.createElement("li");
        g.className = "mrdp-grp";
        g.setAttribute("role", "presentation");
        g.textContent = kayit.grup;
        LISTE.appendChild(g);
      }
      var k = kayit.komut;
      var li = document.createElement("li");
      li.className = "mrdp-opt" + (k.pasif ? " pasif" : "");
      li.id = "mrdp-opt-" + n;
      li.setAttribute("role", "option");
      li.setAttribute("aria-selected", "false");
      if (k.pasif) li.setAttribute("aria-disabled", "true");

      var sol = document.createElement("div");
      var ad = document.createElement("span");
      ad.className = "mrdp-ad";
      vurgula(ad, k.ad, kayit.isaret);
      sol.appendChild(ad);
      var altYazi = k.pasif ? k.pasif : k.altyazi;
      if (altYazi) {
        var alt = document.createElement("span");
        alt.className = "mrdp-alt";
        alt.textContent = altYazi;
        sol.appendChild(alt);
      }
      li.appendChild(sol);

      var sag = document.createElement("div");
      sag.className = "mrdp-sag";
      if (k.yazma) {
        var y = document.createElement("span");
        y.className = "mrdp-yaz";
        y.textContent = "yazar";
        y.title = "Bu komut sistemin durumunu DEĞİŞTİRİR — iki adımlı onay ister.";
        sag.appendChild(y);
      }
      var ipucuYazi = kayit.favori ? MOD + kayit.favori : (k.ipucu || "");
      if (ipucuYazi) {
        var kb = document.createElement("kbd");
        kb.className = "mrdp-ipucu";
        kb.textContent = ipucuYazi;
        sag.appendChild(kb);
      }
      li.appendChild(sag);

      /* Fare: mousedown'da girişten odak kaçmasın (blur → panel kapanma yarışı). */
      li.addEventListener("mousedown", function (e) { e.preventDefault(); });
      li.addEventListener("click", function () { secimiKoy(SATIRLAR.indexOf(li)); calistirSecili(); });
      li.addEventListener("mousemove", function () { secimiKoy(SATIRLAR.indexOf(li)); });

      LISTE.appendChild(li);
      SATIRLAR.push(li);
      li._komut = k;
      li._favori = kayit.favori;
    });
    secimiKoy(0);
  }

  function secimiKoy(n) {
    if (!SATIRLAR.length) return;
    if (n < 0) n = SATIRLAR.length - 1;
    if (n >= SATIRLAR.length) n = 0;
    if (SATIRLAR[SECILI]) SATIRLAR[SECILI].setAttribute("aria-selected", "false");
    SECILI = n;
    var li = SATIRLAR[SECILI];
    li.setAttribute("aria-selected", "true");
    GIRIS.setAttribute("aria-activedescendant", li.id);
    /* Kaydırma listenin İÇİNDE kalır — sayfayı oynatmaz. */
    var r = li.getBoundingClientRect(), lr = LISTE.getBoundingClientRect();
    if (r.top < lr.top) LISTE.scrollTop -= (lr.top - r.top);
    else if (r.bottom > lr.bottom) LISTE.scrollTop += (r.bottom - lr.bottom);
  }

  /* ---- İKİ ADIMLI ONAY ------------------------------------------------------
     Liste yerine tek bir onay bloğu çizilir ve odak "Evet"e taşınır. İkinci
     Enter BİLİNÇLİ olmak zorunda: `e.repeat` reddedilir, yani birinci Enter'ı
     basılı tutmak ikinci adımı geçemez. */
  function onayIste(k) {
    ONAY = k;
    LISTE.style.display = "none";
    var kutu = document.createElement("div");
    kutu.className = "mrdp-onay";
    kutu.id = "mrdp-onay";
    kutu.setAttribute("role", "group");
    kutu.setAttribute("aria-live", "assertive");

    var h = document.createElement("h3");
    h.textContent = "Emin misin? — " + k.ad;
    kutu.appendChild(h);

    var p = document.createElement("p");
    p.textContent = k.altyazi || "Bu komut sistemin durumunu değiştirir.";
    kutu.appendChild(p);

    /* YERLİ ONAY UYARISI: app.js'in kendi confirm() kutusu bu komutta da
       çıkacaksa operatör bunu ÖNCEDEN bilmeli — sürpriz bir ikinci modal,
       "onayladım" hissini bozar ve yanlış refleks kurar. */
    if (k.yerliOnay) {
      var p2 = document.createElement("p");
      p2.className = "uyari";
      p2.textContent = "Onayladıktan sonra panonun kendi tarayıcı onay kutusu da çıkacak.";
      kutu.appendChild(p2);
    }

    var dg = document.createElement("div");
    dg.className = "mrdp-dugmeler";
    var evet = document.createElement("button");
    evet.type = "button";
    evet.className = "mrdp-btn" + (k.tehlike ? " tehlike" : "");
    evet.textContent = "Evet, çalıştır";
    var hayir = document.createElement("button");
    hayir.type = "button";
    hayir.className = "mrdp-btn";
    hayir.textContent = "Vazgeç (Esc)";
    dg.appendChild(evet); dg.appendChild(hayir);
    kutu.appendChild(dg);

    evet.addEventListener("click", function () { onayla(); });
    hayir.addEventListener("click", function () { onaydanCik(); });
    kutu.addEventListener("keydown", function (e) {
      if (e.key === "Tab") {                       // odak tuzağı: iki düğme arasında döner
        e.preventDefault();
        (document.activeElement === evet ? hayir : evet).focus();
      }
    });

    LISTE.parentNode.insertBefore(kutu, LISTE);
    evet.focus();
  }

  function onaydanCik() {
    var k = ONAY;
    ONAY = null;
    var kutu = el("mrdp-onay");
    if (kutu) kutu.parentNode.removeChild(kutu);
    if (LISTE) { LISTE.style.display = ""; }
    if (GIRIS) GIRIS.focus();
    return k;
  }

  function onayla() {
    var k = onaydanCik();
    if (k) yurut(k);
  }

  function calistirSecili() {
    var li = SATIRLAR[SECILI];
    if (!li) return;
    var k = li._komut;
    if (!k) return;
    if (k.pasif) return;                 // sebep zaten satırda yazılı — sessiz düşme değil
    if (k.yazma) { onayIste(k); return; }
    yurut(k);
  }

  function yurut(k) {
    gecmisYaz(gecmisiGuncelle(gecmisOku(), k.id, Date.now()));
    kapat();
    /* Palet ÖNCE kapanır: app.js'in eylemleri sayfayı yeniden çiziyor ve
       sonucu bir DOM düğümüne yazıyor — üstünde bir modal dururken bunların
       hiçbiri görülmez. */
    if (k.calistir) { try { k.calistir(); } catch (e) { console.error("palet komutu:", k.id, e); } return; }
    if (!k.fn) return;
    var cagir = function () {
      var f = window[k.fn];
      if (typeof f !== "function") { console.error("palet: eylem tanımsız —", k.fn); return; }
      try { k.arg === undefined ? f() : f(k.arg); }
      catch (e) { console.error("palet komutu:", k.id, e); }
    };
    if (k.gorunum) gorunumeGec(k.gorunum).then(cagir, cagir);
    else cagir();
  }

  /* ==========================================================================
     AÇ / KAPAT
     ========================================================================== */

  function ac() {
    if (acikMi() || kapiAcik()) return;
    stilEnjekteEt();
    ONCEKI_ODAK = (document.activeElement && document.activeElement !== document.body)
      ? document.activeElement : null;
    KOMUTLAR = komutlariKur();

    KOK = document.createElement("div");
    KOK.className = "mrdp-ov";
    KOK.id = ID_KOK;
    KOK.setAttribute("role", "dialog");
    KOK.setAttribute("aria-modal", "true");
    KOK.setAttribute("aria-label", "Komut paleti");

    var panel = document.createElement("div");
    panel.className = "mrdp-panel";

    var bar = document.createElement("div");
    bar.className = "mrdp-bar";
    var mark = document.createElement("span");
    mark.className = "mrdp-mark";
    mark.textContent = "KOMUT";
    mark.setAttribute("aria-hidden", "true");
    GIRIS = document.createElement("input");
    GIRIS.id = ID_GIRIS;
    GIRIS.className = "mrdp-giris";
    GIRIS.type = "text";
    GIRIS.autocomplete = "off";
    GIRIS.spellcheck = false;
    GIRIS.placeholder = "ne yapmak istiyorsun?";
    GIRIS.setAttribute("role", "combobox");
    GIRIS.setAttribute("aria-expanded", "true");
    GIRIS.setAttribute("aria-controls", ID_LISTE);
    GIRIS.setAttribute("aria-autocomplete", "list");
    GIRIS.setAttribute("aria-label", "Komut ara");
    bar.appendChild(mark); bar.appendChild(GIRIS);

    LISTE = document.createElement("ul");
    LISTE.id = ID_LISTE;
    LISTE.className = "mrdp-liste";
    LISTE.setAttribute("role", "listbox");
    LISTE.setAttribute("aria-label", "Komutlar");

    var altBar = document.createElement("div");
    altBar.className = "mrdp-alt-bar";
    [["↑↓", "gez"], ["Enter", "çalıştır"], ["Esc", "kapat"], [MOD + "1-9", "favori"]]
      .forEach(function (par) {
        var s = document.createElement("span");
        s.textContent = par[0] + " " + par[1];
        altBar.appendChild(s);
      });

    panel.appendChild(bar); panel.appendChild(LISTE); panel.appendChild(altBar);
    KOK.appendChild(panel);
    document.body.appendChild(KOK);

    KOK.addEventListener("mousedown", function (e) { if (e.target === KOK) kapat(); });
    GIRIS.addEventListener("input", function () { listeyiCiz(); });
    KOK.addEventListener("keydown", panelTus);

    listeyiCiz();
    GIRIS.focus();
  }

  function kapat() {
    if (!KOK) return;
    ONAY = null;
    KOK.parentNode.removeChild(KOK);
    KOK = null; GIRIS = null; LISTE = null; SATIRLAR = []; SECILI = 0;
    /* ODAK İADESİ: paleti nereden açtıysan oraya dönersin. İade edilmezse odak
       <body>'ye düşer ve klavye kullanıcısı sayfanın başından tekrar başlar. */
    if (ONCEKI_ODAK && document.contains(ONCEKI_ODAK)) {
      try { ONCEKI_ODAK.focus(); } catch (e) { /* düğüm gitmiş olabilir */ }
    }
    ONCEKI_ODAK = null;
  }

  /* ---- panel içi tuşlar ---------------------------------------------------
     `stopPropagation`: palet açıkken app.js'in belge düzeyindeki kısayolları
     (Esc → çekmece kapat, j/k → satır gezinmesi) ateşlenmemeli — modalın
     ALTINDAKİ sayfaya görünmeden dokunmak modal olmanın anlamını bozar. */
  function panelTus(e) {
    if (e.key === "Escape") {
      e.preventDefault(); e.stopPropagation();
      if (ONAY) onaydanCik(); else kapat();
      return;
    }
    if (ONAY) {
      if (e.key === "Enter" && !e.repeat) { e.preventDefault(); e.stopPropagation(); onayla(); }
      return;                                    // onay adımında başka tuş geçmez
    }
    if (e.key === "ArrowDown") { e.preventDefault(); e.stopPropagation(); secimiKoy(SECILI + 1); return; }
    if (e.key === "ArrowUp") { e.preventDefault(); e.stopPropagation(); secimiKoy(SECILI - 1); return; }
    if (e.key === "Home") { e.preventDefault(); e.stopPropagation(); secimiKoy(0); return; }
    if (e.key === "End") { e.preventDefault(); e.stopPropagation(); secimiKoy(SATIRLAR.length - 1); return; }
    if (e.key === "PageDown") { e.preventDefault(); e.stopPropagation(); secimiKoy(SECILI + 8); return; }
    if (e.key === "PageUp") { e.preventDefault(); e.stopPropagation(); secimiKoy(SECILI - 8); return; }
    if (e.key === "Enter") {
      if (e.repeat) { e.preventDefault(); return; }   // basılı tutmak listeyi tıklamaz
      e.preventDefault(); e.stopPropagation(); calistirSecili(); return;
    }
    if (e.key === "Tab") {
      /* ODAK TUZAĞI: listede gezinme roving-index ile (aria-activedescendant)
         yapılıyor, yani panelde odaklanabilir TEK öğe giriş kutusudur. Tab'ı
         yutmak odağı arkadaki sayfaya kaçırmamanın en basit ve en sağlam yolu. */
      e.preventDefault(); e.stopPropagation(); return;
    }
    /* ⌘/Ctrl + 1-9 → favori (son kullanılan ilk dokuz). Bkz. dosya başındaki
       "BİLİNEN SINIR": bazı tarayıcılar bu birleşimi sayfaya hiç vermez. */
    if ((e.metaKey || e.ctrlKey) && /^[1-9]$/.test(e.key)) {
      var n = Number(e.key);
      for (var i = 0; i < SATIRLAR.length; i++) {
        if (SATIRLAR[i]._favori === n) {
          e.preventDefault(); e.stopPropagation();
          secimiKoy(i); calistirSecili();
          return;
        }
      }
    }
  }

  /* ---- global açıcı -------------------------------------------------------
     YAKALAMA EVRESİNDE (capture): app.js hem `document` hem `window` üzerinde
     keydown dinliyor; palet onlardan ÖNCE karar vermeli. app.js'in kendi
     kısayolları zaten `metaKey || ctrlKey` gördüğünde erken dönüyor, yani ⌘K
     ile j/k satır gezinmesi ÇAKIŞMAZ — bu bilerek böyle. */
  document.addEventListener("keydown", function (e) {
    if (!(e.metaKey || e.ctrlKey) || e.altKey || e.shiftKey) return;
    if (String(e.key).toLowerCase() !== "k") return;
    e.preventDefault();
    e.stopPropagation();
    if (acikMi()) kapat(); else ac();
  }, true);

  /* Sayfa terk edilirken (workflow/landing bağlantısı) açık kalan bir palet
     geri gelindiğinde hayalet bırakmasın. */
  window.addEventListener("pagehide", function () { if (acikMi()) kapat(); });

  window.MeridianPalet.ac = ac;
  window.MeridianPalet.kapat = kapat;
})();
