/* ============================================================================
   Bu dosya HTML'in içinden ÇIKARILDI (2026-08-01), yeniden yazılmadı.
   SEBEP: dağıtım CSP'si `script-src 'self'` (deploy/Caddyfile). Satır içi
   script üretimde bloklanır — bu blok HTML'de kalsaydı sayfa canlıda ölü
   açılırdı. Davranış birebir korundu; tek değişiklik dosyanın yeri.
   ============================================================================ */

// ic: düğüm işaretleri artık ÇİZİLMİYOR — kanonda doymuş emoji kaçak bir tuhaflık.
// Tipi Recursive Mono kategori etiketi taşıyor. Alanlar veride korundu, hiçbir şey silinmedi.
const N = [
 {id:"poll",  t:"trigger",x:520,y:0,   ic:"⏱️",lb:"Zamanlayıcı poll",sb:"300 sn'de bir · bekçi nabzı",
  tip:"scheduler.advance_once: her 300 saniyede uyanır, bekçiyi damgalar, kapanmış seans arar. Seans başına en fazla 1 ağ tazelemesi."},
 {id:"newq",  t:"dec",    x:520,y:110, ic:"❓",lb:"Yeni seans var mı?",sb:"kitap ↔ en yeni bar",
  tip:"portfolio.last_date ile eldeki en yeni bar karşılaştırılır. Yoksa 'current' (nabız tazelenir, rejim geri-doldurulur); varsa ilerleme."},
 {id:"catch", t:"proc",   x:250,y:225, ic:"🔁",lb:"Sıralı seans yakalama",sb:"YENİ · atlanmış her seans işlenir",
  tip:"YENİ: İki poll arasına birden çok seans sığarsa HEPSİ sırayla (on_date) işlenir — 07-16/MNST sınıfı sessiz kayıp kapandı. Tatbikatta gerçek veriyle kanıtlandı."},
 {id:"mono",  t:"dec",    x:790,y:225, ic:"🛡️",lb:"Monotonluk bekçisi",sb:"YENİ · geçmiş seans reddedilir",
  tip:"YENİ: İşlenecek seans kitabın son tarihinden ESKİYSE döngü olaylı reddeder (refused_regressive). Bayat yedek kaynağın kitabı geri sarması — GS'yi öldüren halka — imkânsızlaştı."},
 {id:"dq",    t:"proc",   x:250,y:345, ic:"🔬",lb:"Veri kalitesi kapısı",sb:"karantina + SPY çapraz doğrulama",
  tip:"validate_bars: bozuk barlı sembol karantinaya alınır; bağımsız kaynakla SPY kapanışı çapraz doğrulanır. Kötü veri asla işlem üretmez."},
 {id:"rgm",   t:"proc",   x:790,y:345, ic:"🌡️",lb:"P1 · Rejim + bütçe",sb:"v4: eşik 20 → chop bütçe %25",
  tip:"Endeksten rejim (trend_up/chop/…) ve maruziyet bütçesi. Strateji v4 (operatör kararı, defterde açık): min_exposure_score 40→20 — chop'ta normal boru hattı yeniden işlem silahlar."},
 {id:"curr",  t:"dec",    x:80, y:470, ic:"📡",lb:"Güncellik denetimi",sb:"YENİ · seans barı geldi mi?",
  tip:"YENİ: Bu seansın barı yayınlanmamış sembol o seans TARANMAZ (bayat tetik sınıfı kaynağında kapandı) ve RS havuzuna girmez. Taze gecikenler borç defterine yazılır."},
 {id:"debt",  t:"store",  x:80, y:600, ic:"🧾",lb:"Tarama borcu",sb:"scan_debt.json · geç_bar telafisi",
  tip:"YENİ: Barı sonradan gelen sembolün KAÇAN seansı, o günün kuyruğu ve o günün RS kesitiyle değerlendirilip karşı-olgusala geç_bar satırı olarak işlenir. Kayıp görünmez değil, ölçülü. (07-16 MNST böyle kurtarıldı.)"},
 {id:"scan",  t:"proc",   x:430,y:470, ic:"🔍",lb:"P2 · Tarama (250)",sb:"4 ekran: VCP·pullback·burst·EP",
  tip:"250 sembollük evren (7 ölü sembol bugün tazeleriyle değişti: PNC, USB, EQT, TTWO, EA, KVUE, HRL). Her sembolde 4 ekran birden değerlendirilir."},
 {id:"shdw",  t:"proc",   x:790,y:470, ic:"👥",lb:"Gölge-gevşek tarama",sb:"YENİ · eşik-altı ölçümü",
  tip:"YENİ: İkinci tarama gevşek eşiklerle (hacim 1.0×, RS 55, skor 50) koşar. Sıkıda ölen ama gevşekte doğan adaylar near_miss olarak deftere girer — 'hangi eşik masada para bırakıyor?' artık ölçülüyor. Sıfır yetki."},
 {id:"cf",    t:"store",  x:790,y:600, ic:"📒",lb:"Karşı-olgusal defter",sb:"near_miss · geç_bar · uyuyan · plan",
  tip:"Günün tüm planları + uyuyan ateşlemeler + eşik-altı + geç-bar satırları statik parantezle simüle edilir. Hiçbir karar bu deftere bakmaz; silahlanma/eşik kanıtı buradan birikir. Mevcut tüketiciler near_miss satırlarını varsayılan dışlar."},
 {id:"plan",  t:"proc",   x:430,y:600, ic:"📋",lb:"P3 · Plan + Kapı",sb:"GO / REVIEW / NO_GO + karar ağacı",
  tip:"Aday → plan (tetik/stop/hedef/boyut) → deterministik kapı: R:R disiplini, sektör, ısı, korelasyon, kazanç karartması, ayna-meşgul, gölge veto. Kapı yasadır — hiçbir LLM kararı değiştiremez."},
 {id:"herm",  t:"tool",   x:80, y:730, ic:"🤖",lb:"Nous Hermes ajanı",sb:"canlı skill seti · görüş + sıralama",
  tip:"Yerel hermes-agent: aday ikinci görüşü (destekle/çekimser/karşı), keşif slot sıralaması, terfiliyse REVIEW+karşı vetosu. Yalnız önerir/sıralar — kapıya dokunamaz."},
 {id:"dorm",  t:"dec",    x:430,y:730, ic:"🌱",lb:"Uyuyan kurulum mu?",sb:"YENİ · yalnız keşif yolu",
  tip:"YENİ: momentum_burst / episodic_pivot ateşlemeleri artık plan olur ve kapıdan geçer — ama GO alsalar bile YALNIZ keşif sondası (0.25R) olarak silahlanabilir. Tam silahlanma kararı haftalık değerlendirme + kapı ölçümünün."},
 {id:"arm",   t:"proc",   x:300,y:860, ic:"🎯",lb:"Normal silahlanma",sb:"bütçe>0 · 5 slot · tam boy",
  tip:"GO/REVIEW planlar açık slot varsa bir sonraki açılış için silahlanır (1R'a kadar, dereceli risk azaltma çarpanıyla). Chop bütçesi artık %25 → bu yol chop'ta yeniden açık."},
 {id:"expl",  t:"proc",   x:570,y:860, ic:"🧪",lb:"Keşif sondaları",sb:"YENİ tavan: 5 × 0.25R",
  tip:"GO notlu adaylar (bütçe %0 rejimde herkes; her rejimde uyuyan kurulumlar) keşif slotuyla küçük gerçek işlem açar. 5 eşzamanlı sonda, toplam ≤1.25R. ≥2 adayda yerel ajan sıralar; cevap yoksa skor sırası."},
 {id:"alp",   t:"tool",   x:850,y:860, ic:"🪞",lb:"Alpaca kâğıt ayna",sb:"bracket emir · GTC",
  tip:"Silahlanan her plan kâğıt hesaba stop-giriş + hedef + stop-loss bracket olarak gider (client_order_id = plan kimliği). paper-api'ye sabit kilitli — gerçek para imkânsız. Her döngü uzlaştırma: hayalet/sapma/ret denetimi."},
 {id:"fill",  t:"proc",   x:430,y:990, ic:"⚖️",lb:"P4 · Dolum + taşıma",sb:"YENİ: bar yoksa 1 seans taşınır",
  tip:"Ertesi açılışta tetik görülürse dolum (boşluk emniyeti + likidite tavanıyla). YENİ: dolum anında bar yayınlanmamışsa plan olaylı şekilde BİR seans taşınır; ikinci seansta da yoksa olaylı düşer — sessiz buharlaşma bitti."},
 {id:"cal",   t:"proc",   x:430,y:1120,ic:"📐",lb:"P5 · Kalibrasyonlar",sb:"gölge·skor·çıkış·LLM·sadakat·karne",
  tip:"Her döngü sonunda: gölge model, skor IC, çıkış verimliliği (MFE), LLM görüş kalibrasyonu, cf sadakati, near-miss karnesi, bekçi nabızları. Haftalık: öz-değerlendirme, silahlanma değerlendirmesi, skill revizyon taslağı."},
 {id:"out",   t:"out",    x:430,y:1250,ic:"📊",lb:"Panel · Olaylar · Bildirim",sb:"Cam Kokpit + Telegram",
  tip:"Her adım olay defterine yazar; Cam Kokpit canlı okur (HUD, karar ağacı, teşhis). Beyaz-liste alarmlar (ARMING_READY, MIRROR_DRIFT…) 6 saat sessizlik penceresiyle telefona düşer."},
];
const E = [
 ["poll","newq","kapanmış seans?"],
 ["newq","catch","ilerleme: işlenmemiş seans listesi"],
 ["newq","mono","seans tarihi"],
 ["catch","dq","on_date · sırayla her seans"],
 ["mono","rgm","onaylı seans (geriye asla)"],
 ["dq","curr","temiz semboller"],
 ["dq","scan","karantina dışı barlar"],
 ["rgm","scan","rejim + bütçe %"],
 ["curr","debt","bar gelmemiş: sembol+tarih"],
 ["debt","cf","geç_bar satırları"],
 ["scan","plan","adaylar (skor sıralı)"],
 ["shdw","cf","eşik-altı near_miss"],
 ["scan","shdw","aynı kuyruk, gevşek eşik"],
 ["plan","cf","günün tüm planları"],
 ["herm","plan","ikinci görüş · veto (terfiliyse)"],
 ["plan","dorm","kapı kararı"],
 ["dorm","arm","hayır → GO/REVIEW + slot"],
 ["dorm","expl","evet → yalnız GO"],
 ["herm","expl","≥2 adayda sıralama"],
 ["arm","alp","bracket emir"],
 ["expl","alp","0.25R sonda emri"],
 ["arm","fill","silahlı planlar"],
 ["expl","fill","sonda planları"],
 ["alp","fill","dolum/uzlaştırma"],
 ["fill","cal","işlem sonuçları (R)"],
 ["cal","out","karneler + alarmlar"],
 ["cal","cf","çözülen satırlar (MFE/MAE)"],
];
// Her düğüm tipinin TİPİNİ yazıyla da taşır — kategori asla yalnız biçimde kalmaz.
// Metinler alttaki gösterge (legend) ile birebir aynı.
const CAT = {trigger:"Tetik",proc:"İşlem",tool:"Araç / Servis",out:"Çıktı",store:"Veri Deposu",dec:"Karar"};
const stage=document.getElementById("stage"),svg=document.getElementById("edges"),tip=document.getElementById("tip");
const byId={};
function showTipAt(n,x,y){tip.style.display="block";tip.textContent=n.tip;
  tip.style.left=Math.max(8,Math.min(x,innerWidth-332))+"px";tip.style.top=y+"px";}
N.forEach(n=>{
  const el=document.createElement("div");
  el.className="node t-"+({trigger:"trigger",proc:"proc",tool:"tool",out:"out",store:"store",dec:"dec"})[n.t];
  el.style.left=n.x+"px";el.style.top=n.y+"px";
  el.tabIndex=0;el.setAttribute("role","button");
  el.innerHTML=`<div class="cat">${CAT[n.t]}</div>`+
               `<div class="lb">${n.lb}</div><div class="sb">${n.sb}</div>`;
  el.addEventListener("mousemove",ev=>showTipAt(n,ev.clientX+14,ev.clientY+14));
  el.addEventListener("mouseleave",()=>tip.style.display="none");
  // klavye eşdeğeri: odakta not açılır, Enter/Boşluk zinciri izler
  el.addEventListener("focus",()=>{const r=el.getBoundingClientRect();showTipAt(n,r.left,r.bottom+8);});
  el.addEventListener("blur",()=>tip.style.display="none");
  el.addEventListener("keydown",ev=>{if(ev.key==="Enter"||ev.key===" "){ev.preventDefault();ev.stopPropagation();select(n.id);}});
  el.addEventListener("click",ev=>{ev.stopPropagation();select(n.id);});
  stage.appendChild(el);byId[n.id]={...n,el};
});
function anchor(a,b){  // kutu merkezleri arası, kenardan kenara
  const A=byId[a].el,B=byId[b].el;
  const ax=A.offsetLeft+A.offsetWidth/2, ay=A.offsetTop+A.offsetHeight/2;
  const bx=B.offsetLeft+B.offsetWidth/2, by=B.offsetTop+B.offsetHeight/2;
  const dx=bx-ax,dy=by-ay;
  const cut=(w,h,vx,vy)=>{const sx=Math.abs(vx)/(w/2),sy=Math.abs(vy)/(h/2);const s=Math.max(sx,sy)||1;return [vx/s,vy/s];};
  const [o1x,o1y]=cut(A.offsetWidth,A.offsetHeight,dx,dy);
  const [o2x,o2y]=cut(B.offsetWidth,B.offsetHeight,-dx,-dy);
  return [ax+o1x,ay+o1y,bx+o2x,by+o2y];
}
svg.innerHTML=`<defs>
  <marker id="ar" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="7" markerHeight="7" orient="auto">
    <path d="M0 0 L8 4 L0 8 z"/></marker>
  <marker id="ar-hi" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="7" markerHeight="7" orient="auto">
    <path d="M0 0 L8 4 L0 8 z"/></marker></defs>`;
const edgeEls=E.map(([a,b,lab])=>{
  const [x1,y1,x2,y2]=anchor(a,b);
  const mx=(x1+x2)/2,my=(y1+y2)/2;
  const p=document.createElementNS("http://www.w3.org/2000/svg","path");
  p.setAttribute("d",`M${x1} ${y1} C ${x1} ${my}, ${x2} ${my}, ${x2} ${y2}`);
  p.setAttribute("class","edge");p.setAttribute("marker-end","url(#ar)");
  const t=document.createElementNS("http://www.w3.org/2000/svg","text");
  t.setAttribute("x",mx);t.setAttribute("y",my-5);t.setAttribute("text-anchor","middle");
  t.setAttribute("class","elabel");t.textContent=lab;
  svg.appendChild(p);svg.appendChild(t);
  return {a,b,p,t};
});
// Kesişen açıklama etiketlerini dikeyde ayırır: aynı bantta üst üste binen iki
// açıklama okunamıyordu. YALNIZ yerleşim — hiçbir bağlantı, sıra ya da metin
// değişmez; her etiket kendi eğrisinden en çok 22px uzaklaşabilir.
(function spreadLabels(){
  const items=edgeEls.map(e=>({t:e.t,y0:parseFloat(e.t.getAttribute("y")),box:e.t.getBBox()}));
  for(let pass=0;pass<8;pass++){
    let moved=false;
    for(let i=0;i<items.length;i++)for(let j=i+1;j<items.length;j++){
      const A=items[i],B=items[j];
      const ox=Math.min(A.box.x+A.box.width,B.box.x+B.box.width)-Math.max(A.box.x,B.box.x);
      const oy=Math.min(A.box.y+A.box.height,B.box.y+B.box.height)-Math.max(A.box.y,B.box.y);
      if(ox<=0||oy<=0)continue;
      const step=Math.min(oy/2+2,7);
      const up=A.box.y<=B.box.y?A:B, dn=(up===A?B:A);
      [[up,-step],[dn,step]].forEach(([it,d])=>{
        const y=parseFloat(it.t.getAttribute("y"));
        if(Math.abs(y+d-it.y0)<=22){it.t.setAttribute("y",y+d);it.box=it.t.getBBox();moved=true;}
      });
    }
    if(!moved)break;
  }
})();
function select(id){
  const keep=new Set([id]);
  edgeEls.forEach(e=>{const on=e.a===id||e.b===id;
    e.p.classList.toggle("hi",on);e.t.classList.toggle("hi",on);
    if(on){keep.add(e.a);keep.add(e.b);}});
  N.forEach(n=>{byId[n.id].el.classList.toggle("dim",!keep.has(n.id));
                byId[n.id].el.classList.toggle("sel",n.id===id);});
}
function reset(){
  edgeEls.forEach(e=>{e.p.classList.remove("hi");e.t.classList.remove("hi");});
  N.forEach(n=>{byId[n.id].el.classList.remove("dim","sel");});
}
document.body.addEventListener("click",reset);
document.addEventListener("keydown",ev=>{if(ev.key==="Escape")reset();});
