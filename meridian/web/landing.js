/* ============================================================================
   Bu dosya HTML'in içinden ÇIKARILDI (2026-08-01), yeniden yazılmadı.
   SEBEP: dağıtım CSP'si `script-src 'self'` (deploy/Caddyfile). Satır içi
   script üretimde bloklanır — bu blok HTML'de kalsaydı sayfa canlıda ölü
   açılırdı. Davranış birebir korundu; tek değişiklik dosyanın yeri.
   ============================================================================ */

const io=new IntersectionObserver(e=>e.forEach(x=>x.isIntersecting&&x.target.classList.add('in')),{threshold:.15,rootMargin:'0px 0px -60px'});
document.querySelectorAll('.rise').forEach((el,i)=>{el.style.transitionDelay=(i%4)*60+'ms';io.observe(el)});
const nav=document.getElementById('nav');
addEventListener('scroll',()=>nav.classList.toggle('stuck',scrollY>20));
const f=document.getElementById('fill');
f.innerHTML=f.textContent.trim().split(' ').map(w=>'<w>'+w+'</w>').join(' ');
const ws=[...f.querySelectorAll('w')];
function paint(){const r=f.getBoundingClientRect(),h=innerHeight;
 const p=Math.min(1,Math.max(0,(h*0.85-r.top)/(r.height+h*0.35)));
 const n=Math.round(p*ws.length);ws.forEach((w,i)=>w.classList.toggle('on',i<n));}
addEventListener('scroll',paint,{passive:true});paint();

/* ---------------------------------------------------------------- */

/* ÖLÇÜLEN — MANŞET: canlı/tohum AYRI (v223 KALEM 6'nın pano bacağı). Eskiden tek "kapanmış işlem 96"
   vardı; 96 replay TOHUMU (training, survivorship'li) DAHİL ham toplam, GERÇEK canlı 1 — manşet
   yanıltıyordu. Artık canlı n + ortalama R ÖNDE, tohum İKİNCİL (mut). $ P&L uç sözleşmesi gereği YOK
   (canlı sonuç yalnız R-multiple, uç bilerek $ vermez). Hiçbir sayı sabit yazılmaz — hepsi
   /api/public/summary'den okunur (C10; landing "uydurma rakam" geçmişi). SAF FONKSİYON: Node'da
   doğrulanır (test_dalga2_entegrasyon_v226). */
function olculenSatiri(d) {
  var live = d.live || {}, liveN = d.closed_trades_live, seedN = d.closed_trades_seed;
  var ortR = live.mean_r != null ? (live.mean_r > 0 ? "+" : "") + live.mean_r.toFixed(2) + "R" : null;
  return '<div class="hyp"><div class="top"><span class="v">ölçülen</span></div>' +
    '<div class="meta">' +
    '<span>canlı işlem <b>' + (liveN != null ? liveN : "—") + '</b>' +
      (ortR ? ' · ortalama <b>' + ortR + '</b>' : "") + '</span>' +
    '<span class="mut">tohum (replay) <b>' + (seedN != null ? seedN : "—") + '</b></span>' +
    '<span>başarı notu <b style="color:var(--' + ((d.score || 0) > 0 ? "green" : "red") + ')">' +
    (d.score != null ? d.score : "—") + '</b></span>' +
    '<span>denenen değişken <b>' + (d.variables_tried != null ? d.variables_tried : "—") + '</b></span>' +
    '<span>sürüm <b>v' + (d.strategy_version != null ? d.strategy_version : "—") + '</b></span>' +
    '</div></div>';
}

/* ÖĞRENME DEFTERİ — CANLI. Bu blok daha önce elle yazılmış dört sürüm kaydının yerini aldı;
   o kayıtlar state/ ile çelişiyordu (sayfa iki hipotezin kâr ettiğini söylüyordu, gerçekte
   hiçbiri kapıyı geçmemişti). Kural: sayı gelmezse sayı GÖSTERİLMEZ — asla yer tutucuya
   düşülmez, çünkü bu sayfanın tek dışa dönük iddiası dürüstlüktür. */
(function () {
  var STATUS_TR = {
    rejected_by_backtest: "backtest kapısında elendi",
    rejected_by_guard: "guard kurallarına takıldı",
    rejected_by_confirmation: "doğrulamada elendi",
    superseded: "yerini yenisi aldı",
    shipped: "canlıya çıktı", promoted: "canlıya çıktı", accepted: "canlıya çıktı"
  };
  var esc = function (t) { var d = document.createElement("div"); d.textContent = t == null ? "" : t; return d.innerHTML; };

  function fail(msg) {
    var n = document.getElementById("pub-note");
    if (n) n.textContent = "Canlı kayıt şu an okunamıyor. Rakam uydurmaktansa boş bırakıyoruz.";
    var l = document.getElementById("pub-ledger");
    if (l) l.innerHTML = '<div class="hyp"><div class="top"><span class="v">kayıt alınamadı</span></div>' +
      '<p>' + esc(msg) + '</p></div>';
  }

  fetch("/api/public/summary", { headers: { accept: "application/json" } })
    .then(function (r) { if (!r.ok) throw new Error("HTTP " + r.status); return r.json(); })
    .then(function (d) {
      var total = d.hypotheses_total || 0, shipped = d.hypotheses_shipped || 0;
      var note = document.getElementById("pub-note");
      if (note) {
        note.textContent = shipped > 0
          ? total + " hipotezden " + shipped + " tanesi kapıyı geçti ve canlıya çıktı."
          : total + " hipotez önerildi, hiçbiri kapıyı geçemedi. Defterin şu anki dürüst hali bu: "
            + "sistem henüz bir kenar bulduğunu kanıtlayamadı.";
      }
      var rows = [];
      var by = d.hypotheses_by_status || {};
      Object.keys(by).sort(function (a, b) { return by[b] - by[a]; }).forEach(function (k) {
        rows.push('<div class="hyp"><div class="top">' +
          '<span class="v">' + esc(STATUS_TR[k] || k) + '</span>' +
          '<span class="st ' + (k === "shipped" || k === "promoted" || k === "accepted" ? "s-ok" : "s-rj") + '">' +
          by[k] + ' hipotez</span></div></div>');
      });
      rows.push(olculenSatiri(d));
      var l = document.getElementById("pub-ledger");
      if (l) l.innerHTML = rows.join("");

      /* hero cred: skill sayısı CANLI (eski sabit sayı (66) 2026-07-30 arşiviyle çürüdü);
         sayı gelmezse yedek metin sayısız kalır — uydurma rakam kuralı burada da geçerli */
      var sc = document.getElementById("pub-skills");
      if (sc && d.skills_live != null) sc.textContent = d.skills_live + " skill";

      /* döngü panosu: mekanizmayı anlatır, sonucu state'ten söyler */
      var cs = document.getElementById("pub-cycle-state");
      if (cs) {
        cs.textContent = shipped > 0
          ? "→ şu ana kadar " + shipped + " öneri kapıyı geçti."
          : "→ şu ana kadar hiçbir öneri kapıyı geçemedi. Döngü çalışıyor, kenar henüz yok.";
      }

      /* matrisin örneklem dipnotu CANLI (K1): "31 kapanmış işlem" sabit yazılıydı, defterde 95 var */
      var mf = document.getElementById("pub-matrix-foot");
      if (mf && d.closed_trades != null) {
        // Matrisin paydası TÜM defter (tohum dahil) — o yüzden ham `closed_trades` DOĞRU sayıdır;
        // ama "hepsi canlı" sanılmasın diye tohum-dahil olduğu + canlı alt-kümesi AÇIKÇA yazılır
        // (manşetle aynı ayrım; ikisi de uçtan, sabit sayı yok).
        mf.textContent = d.closed_trades + " kapanmış işlemden hesaplandı"
          + (d.closed_trades_live != null ? " (tohum dahil; canlı " + d.closed_trades_live + ")" : "")
          + ". Ortalama R, işlem başına riske göre getiri.";
      }

      /* ürün maketindeki matris: gerçek kurulum × rejim verisi */
      var m = d.matrix, mg = document.getElementById("pub-matrix");
      if (mg && m && (m.grid || []).length) {
        var RG = { chop: "yatay/kararsız", trend_up: "yükseliş trendi", high_vol: "yüksek dalgalanma" };
        var h = '<div class="pm-corner"></div>' +
          m.regimes.map(function (r) { return '<div class="pm-sect">' + esc(RG[r] || r) + '</div>'; }).join("");
        m.grid.forEach(function (row) {
          h += '<div class="pm-strip">' + esc(row.setup) + '</div>';
          row.cells.forEach(function (c, i) {
            var rg = esc(RG[m.regimes[i]] || m.regimes[i]);
            if (!c) { h += '<div class="pm-cell pm-unsown"><span class="pm-sectlabel">' + rg +
                        '</span><span class="pm-none">veri yok</span></div>'; return; }
            /* nötr bant: |ortalama| örneklem gürültüsünün altındaysa ne yeşil ne kırmızı */
            var band = 1 / Math.sqrt(c.n);
            var cls = Math.abs(c.mean_r) <= band ? "" : (c.mean_r > 0 ? " pos" : " neg");
            var conf = Math.min(100, Math.round(100 * Math.log(c.n + 1) / Math.log(61)));
            h += '<div class="pm-cell' + cls + '" style="--conf:' + conf + '%">' +
                 '<span class="pm-sectlabel">' + rg + '</span>' +
                 '<span class="pm-yield mono-num">' + (c.mean_r > 0 ? "+" : "") + c.mean_r.toFixed(2) + 'R</span>' +
                 '<span class="pm-conf" aria-hidden="true"><i></i></span>' +
                 '<span class="pm-n">' + c.n + ' işlem</span></div>';
          });
        });
        mg.style.setProperty("--cols", m.regimes.length);
        mg.innerHTML = h;
      }
    })
    .catch(function (e) { fail(String(e && e.message || e)); });
})();
