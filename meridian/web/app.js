// Meridian dashboard — sabah brifingi. Read-model client, matches meridian-landing.html. No build step.
// Plain-Turkish glossary + hover tooltips + always-visible captions so a low-finance-literacy reader can follow.
const OPERATOR = "Erdem";
// ---- BEŞ YÜZEY (D2-b, 2026-08-07 — bağlayıcı IA: docs/TASARIM-YONU-2026-08-07.md §3) ---------
// S2R-1/2'nin YEDİ alan sayfası, işten değil widget'tan türemişti: "Veri Sağlığı" ile "Gözetim &
// Alarmlar" aynı görevin (TASK ③: alarmdan nedene) iki yarısıydı ve operatör zinciri iki sayfaya
// yayarak yürüyordu (denetim B12). "Koşu & Döngü" ile "Portföy & Emirler" ise aynı durum
// ızgarasını İKİ KEZ çiziyordu (`DURUM_SAYFALARI` iki elemanlıydı — v191 çakışmayı bir bantla
// örttü, kökünü çözmedi). Yeni yapı İŞTEN türer ve beş yüzeydir:
//   ① Bugün   → sağlıklı mı, dün gece ne oldu, benden ne bekleniyor?
//   ② Karar   → ne önerildi, neden geçti/geçmedi, ne oldu?
//   ③ Sağlık  → veri ve işleyiş güvenilir mi; bir şey bozulduysa ne yapmalıyım?
//   ④ Öğrenme → ajan öğreniyor mu, neyi düzeltti, neyi bozdu, kaça mal oldu?
//   ⑤ Kilitler→ ajanın yetkisi ne, sınırları nerede, nasıl durdururum?
// Sıra ekrandaki sırayla aynıdır ve çıplak 1-5 tuşları bu sıradan türer.
const VIEWS = [
  ["bugun", "Bugün"], ["karar", "Karar"], ["saglik", "Sağlık"],
  ["ogrenme", "Öğrenme"], ["kilitler", "Kilitler"],
];
// ---- ESKİ ADRESLER → YENİ EVİ (17/17, hiçbiri düşmez) ----------------------------------------
// Eski yer imleri, derin bağlantılar, `docs/RUNBOOK.md` bağları ve çekmece çipleri KIRILMAZ:
// hepsi yeni yüzeyine yönlenir ve içerik oraya TAŞINMIŞTIR (silinmemiştir).
//
// ALIAS SÖZLÜĞÜ ARTIK İKİ SINIF TAŞIR ve ikisi de "eski adres"tir — bölüm listesi DEĞİL:
//   (a) BÖLÜM ALIASI — eski on iki GÖRÜNÜM adı. Bugün birer `.alan-bolum` kabıdır ve hedefi o
//       kabın İÇİNDE durduğu yüzeydir (`#page-<eski>` gerçekten orada). `<eski>` tek başına
//       yazıldığında sayfa açılır; `<eski>#<bölüm>` biçimi go()'nun çapa dalıyla çözülür.
//   (b) SAYFA ALIASI — S2R'nin BEŞ eski alan sayfası (genel/veri/kosu/portfoy/gozetim). Bunların
//       artık bir DOM kabı yoktur: yüzeyleri birleşti. Alias, `kosu#adaylar` / `portfoy#mutabakat`
//       / `gozetim#failsub` / `veri#veriboru` biçimindeki YÜZLERCE eski adresi (RUNBOOK bağları,
//       çekmece çipleri, operatörün yer imleri) yeni yüzeye taşır — çapa aynen korunur.
// S2R-2'nin sekiz yeni bölümü (mutabakat, kapilar, veriboru, intraemir, karne, golge, bilesenic,
// mudahale) ve D2-b'nin `cizelge`si buraya GİRMEZ: hiçbiri bir eski yer imi değil. Onların evi
// ALAN_BOLUMLERI'dir.
const ROUTE_ALIAS = {
  // (a) eski on iki görünüm → bugün bir bölüm
  brifing: "karar", performans: "karar", onaylar: "karar", adaylar: "karar",
  market: "saglik", intraday: "saglik", operasyon: "saglik",
  ajan: "ogrenme", hermes: "ogrenme", skiller: "ogrenme", hafiza: "ogrenme",
  ayarlar: "kilitler",
  // (b) eski beş alan sayfası → yeni yüzey (D2-b birleşmesi)
  genel: "bugun", kosu: "karar", portfoy: "karar", veri: "saglik", gozetim: "saglik",
};
// Hash yoksa ya da tanınmıyorsa açılan sayfa. TEK YERDE: üç ayrı yerde ("baslat", "buildSidebar",
// R tuşu) elle "brifing" yazılıydı ve bu tur onları ayrı ayrı kaydırabilirdi.
const VARSAYILAN_ROTA = "bugun";
// ÖĞRENME YÜZEYİ AÇIK MI? Sprint ve Hermes yoklamaları bunu `location.hash.includes("ajan")` ile
// soruyordu ve S2R-1 o cümleyi SESSİZCE yanlışladı: hash artık "#ogrenme". Yoklama hiç dönmez,
// canlı arama ilerlemesi ekranda donar ve hiçbir yerde hata görünmez — tam olarak bu deponun
// "kurulu ≠ çalışır" kusur sınıfı. Soru artık DOM'un kendisine sorulur: hangi sayfa aktif?
// Hash'e değil sayfaya bakmak alias'lardan da bağımsızdır (#ajan da buraya çözülür).
const _ogrenmeAcik = () => !!$("page-ogrenme")?.classList.contains("active");
// Bağ metinleri VIEWS'ten TÜRER — Genel Bakış'ın altı kartı "→ <alan adı>" yazıyor ve o adların
// ikinci bir listesi olsaydı ilk etiket değişikliğinde sessizce ayrışırdı.
const ALAN_ADI = Object.fromEntries(VIEWS);
// ---- EKRAN-BAŞINA SORU CÜMLESİ (UIUX S1-T5) --------------------------------------------------
// İş emri Program IA: "Her ekran tek cümlelik bir soruyu cevaplar; cevaplamadığı hiçbir veri o
// ekranda durmaz ('ekrana dök' yasağı)." O cümleler bugüne dek YALNIZ kod yorumlarında yaşıyordu
// (bkz. yukarıdaki VIEWS bloğu) — yani kuralı uygulaması gereken kişi onu ekranda göremiyordu.
// Cümle ekrana çıktığı an bir DENETİM ÇIPASI olur: bir blok eklerken "bu, bu sorunun cevabı mı?"
// diye sorulacak yer, o bloğun eklendiği ekranın kendi başlığıdır.
//
// YİRMİ ALTI GİRDİ (D2-b): beş YÜZEY + yirmi bir BÖLÜM. Bölümler de kendi sorusunu taşır,
// çünkü "ekrana dök" riski tam olarak orada doğuyor — bir sayfaya bir bölüm daha eklemek, yeni
// bir sayfa açmaktan çok daha ucuz görünür.
//
// CÜMLENİN İLK İKİ KELİMESİ MERTEBEYİ SÖYLER ve bu bir sözleşmedir (testte çivili):
//   "Bu ekran şunu cevaplar:"  → alan sayfası (yedi tane). Sayfadaki HER bölüm bu soruya hizmet
//                                etmeli; etmeyen bölüm taşınır ya da detay katmanına iner.
//   "Bu bölüm şunu cevaplar:"  → sayfa içi bölüm (yirmi tane).
//
// S2R-2'DE CÜMLELER İÇERİĞE GÖRE DARALDI. Bir bölüm ikiye bölündüğünde ESKİ cümleyi iki parçaya
// da vermek, ikisini de yanlış yapardı: `intraday` artık silahlanmayı ANLATMIYOR (o `intraemir`e
// gitti) ve `performans` artık kırılımları anlatmıyor (onlar `karne`ye gitti). Cümle bir
// sözleşmedir; sözleşme içerikle birlikte taşınır.
//
// TEK KAYNAK BURASIDIR. WP0'ın "Ek-A" listesi bu sözlüğün kendisidir; belgeye kopyalanan bir
// ikinci liste, ilk düzenlemede sessizce ayrışırdı.
const EKRAN_SORUSU = {
  // --- beş yüzey (cümleler yön belgesinin §3 tablosundan, BİREBİR) ---
  bugun:      "Bu ekran şunu cevaplar: sağlıklı mı, dün gece ne oldu, benden ne bekleniyor?",
  karar:      "Bu ekran şunu cevaplar: ne önerildi, neden geçti/geçmedi, ne oldu?",
  saglik:     "Bu ekran şunu cevaplar: veri ve işleyiş güvenilir mi; bir şey bozulduysa ne yapmalıyım?",
  ogrenme:    "Bu ekran şunu cevaplar: ajan öğreniyor mu — neyi düzeltti, neyi bozdu, kaça mal oldu?",
  kilitler:   "Bu ekran şunu cevaplar: ajanın yetkisi ne, sınırları nerede, nasıl durdururum?",
  // --- eski on iki görünüm, artık bölüm ---
  brifing:    "Bu bölüm şunu cevaplar: kitap şu an nerede — sermaye, risk ve açık pozisyonlar ne durumda?",
  adaylar:    "Bu bölüm şunu cevaplar: gece döngüsü ne önerdi — kapıdan ne geçti, ne elendi?",
  market:     "Bu bölüm şunu cevaplar: bugün neyi izliyorum — evrenin tamamı hangi kapanışta, neresi bayat?",
  operasyon:  "Bu bölüm şunu cevaplar: hangi alarm çaldı, bütçesi aştı mı, bekçiler ne diyor?",
  intraday:   "Bu bölüm şunu cevaplar: dakikalık bar akışı canlı mı, kayıp dakika var mı?",
  ajan:       "Bu bölüm şunu cevaplar: beyin ne önerdi, kapı ne dedi, gerçekte ne oldu?",
  ayarlar:    "Bu bölüm şunu cevaplar: sistem nasıl yapılandırılmış, hangi anahtarlar kurulu?",
  hermes:     "Bu bölüm şunu cevaplar: düşünen beyin şu an ne yapıyor, sıradaki tur ne bekliyor?",
  hafiza:     "Bu bölüm şunu cevaplar: ajan kendi geçmişinden ne çıkardı — kalıcı dersler neler?",
  skiller:    "Bu bölüm şunu cevaplar: hangi araçlar hatta, hangileri emekli, katkıları ölçüldü mü?",
  performans: "Bu bölüm şunu cevaplar: bugüne kadar ne birikti — eğri, düşüş ve kapanmış işlemler ne diyor?",
  onaylar:    "Bu bölüm şunu cevaplar: şu an benim onayımı bekleyen ne var?",
  // --- S2R-2'nin sekiz yeni bölümü (eski görünümlerin bölünmesinden doğdular) ---
  mutabakat:  "Bu bölüm şunu cevaplar: iç defter ile brokerin defteri aynı şeyi mi söylüyor?",
  intraemir:  "Bu bölüm şunu cevaplar: seans içinde tetiği kesen plana ne oldu — emir çıkar mıydı?",
  kapilar:    "Bu bölüm şunu cevaplar: disiplin kapısı bu seansta neyi hangi ölçütle eledi?",
  veriboru:   "Bu bölüm şunu cevaplar: veri hattı sağlam mı — karantina, bütünlük ve sıcak katman ne durumda?",
  karne:      "Bu bölüm şunu cevaplar: öğreniyor mu — hangi ölçülmüş sayı bunu söylüyor?",
  golge:      "Bu bölüm şunu cevaplar: kâğıt üstünde koşan gölge kollar ne veriyor?",
  bilesenic:  "Bu bölüm şunu cevaplar: bir kenar var mı, hangi bileşenden geliyor, büyüyor mu?",
  mudahale:   "Bu bölüm şunu cevaplar: elimde hangi durdurma kolu var ve hangisi şu an çekili?",
  // --- D2-b'nin tek yeni bölümü: workflow.html'in halefi ---
  cizelge:    "Bu bölüm şunu cevaplar: gece hattı hangi adımdan geçti — hangisi penceresinde, hangisi geciken?",
};
// SÖNÜK VE TEK SATIR (iş emri: "başlık-altı tek sönük satır"). Kendi CSS sınıfı YOK — bu tur
// paralel koşuyor ve index.html'in <style>'ı başka bir hattın alanı; satır mevcut `.hint`
// mertebesine oturur, tonu satır içi düşürülür. `data-soru` bir kancadır: testler on iki
// görünümün on ikisinde de bu satırın varlığını buradan ölçer.
function soruCumlesi(id) {
  const s = EKRAN_SORUSU[id];
  if (!s) return "";           // kayıtsız görünüm sessizce boş satır üretir, uydurma cümle değil
  return `<p class="hint soru-c" data-soru="${id}" style="margin-top:6px;font-size:12px;` +
         `color:var(--tx3);max-width:80ch">${esc(s)}</p>`;
}
let HALTED = false, SUMMARY = null;
// Şeridin Öğrenme satırı (`{loop_state, skill_count, status}`) /api/hermes'ten gelir ve o uç
// YALNIZ Portföy (eski Bugün) çizilirken okunur. S2R-1'de açılış sayfası Genel Bakış oldu; paket
// önbelleklenmeseydi ray o satırı Portföy'e girilene kadar HİÇ göstermezdi. null = "hiç ölçülmedi"
// ve o hâlde satır dürüstçe kısalır — eski bir değeri taze gibi göstermek yerine hiç göstermemek.
let _HERMES_PAKET = null;
// Piyasa sekmesi bir kez çizildiğinde şeridin alt satırına düşen CANLI sayılar. null = "henüz
// ölçülmedi" (sayfa açılmadı) — şerit o zaman satırı hiç yazmaz, sıfır yazmaz.
let MARKET_N = null, MARKET_STALE = null;
const $ = id => document.getElementById(id);

// --- API target: same-origin by default, or a REMOTE Meridian agent. Set once via URL and it sticks:
//     http://localhost:8080/?api=http://<host>:8080&token=<MERIDIAN_DASH_TOKEN>
// Best practice: reach the remote agent over an IAP tunnel and just use same-origin (no api/token needed).
const _qs = new URLSearchParams(location.search);
if (_qs.has("api")) localStorage.setItem("meridian_api", _qs.get("api"));
if (_qs.has("token")) localStorage.setItem("meridian_token", _qs.get("token"));
const API_BASE = (localStorage.getItem("meridian_api") || "").replace(/\/+$/, "");   // "" = same origin
const API_TOKEN = localStorage.getItem("meridian_token") || "";
const _JC = new Map();   // yanıt önbelleği — apiFetch mutasyonda siler, bkz. aşağı
// ---- HTTP HATASI BİR İSTİSNADIR (v219 · 409-YUTMASI) -----------------------------------------
// ÖLÇÜLEN KUSUR: `apiFetch` HER yanıtı olduğu gibi döndürüyordu ve çağıranların çoğu `r.ok`a hiç
// bakmıyordu. L1'de uygulama kapısı (`api._onay_kapisi`) bir uygulamayı reddederken 409 + gövdede
// `[kimlik] <en az 20 karakter gerekçe>` yazıyor — pano bunu HİÇ okumuyordu. `applySkillRec`'in
// boş `catch`i ile birleşince ölçülen davranış şuydu: operatör "Uygula"ya basar, sunucu
// gerekçesiyle REDDEDER, ekranda HİÇBİR ŞEY olmaz. Bir onay kapısının en pahalı hâli, sessizce
// reddeden hâlidir: kapı çalışıyordur ama operatör onun çalıştığını asla öğrenemez.
//
// SÖZLEŞME: 2xx dışındaki her yanıt `ApiHata` olarak FIRLAR. Gövdedeki `detail` mesajın İÇİNE
// girer (operatörün gördüğü tek metin o olabilir) ve `status`/`detay`/`govde` alanları çağırana
// AÇIK kalır — kimi yüzeyin 409'u (dünyanın durumu) 500'den (arıza) ayırması gerekir, kimisinin
// de ağ kopması ile sunucu reddini: ilkinde `status` vardır, ikincisinde YOKTUR ve bu ayrım
// "emir gitmiş olabilir" cümlesinin kurulup kurulmayacağını belirler.
class ApiHata extends Error {
  constructor(status, detay, govde, yol) {
    super(`HTTP ${status} — ${detay || "sunucu sebep bildirmedi"}`);
    this.name = "ApiHata";
    this.status = status;
    this.detay = detay || "";
    this.govde = govde;
    this.yol = yol;
  }
}
async function apiFetch(path, opts = {}) {
  const headers = Object.assign({}, opts.headers || {});
  if (API_TOKEN) headers["x-meridian-token"] = API_TOKEN;         // authenticate every network call
  // MUTASYON ÖNBELLEĞİ DÜŞÜRÜR: "Şimdi düşün" gibi bir eylemden sonra kod RENDER.ajan()'ı
  // çağırıyor ve TAZE durum bekliyor. Yanıt önbelleği bunu bilmezse eylem öncesi durumu geri
  // gösterirdi — kullanıcıya "hiçbir şey olmadı" dedirtir. GET dışı her istek defteri siler.
  const m = (opts.method || "GET").toUpperCase();
  if (m !== "GET") _JC.clear();
  const ham0 = await fetch(API_BASE + path, Object.assign({}, opts, { headers }));
  // 401 KAPISI ÖNCE: oturum düştüyse kapak her koşulda açılır — fırlatma onu atlamamalı.
  const r = (typeof _yetkisizYakala === "function" ? _yetkisizYakala(ham0) : ham0);
  if (r.ok) return r;
  // TEK İSTİSNA — `hamYanit`. Bir yüzeyin durum kodunu KENDİSİ okuması, o yüzeyin kendi
  // hükmüyse (v195-a: `alpacaSubmit` 401/500 gövdesini "0 emir gönderildi" diye okumasın diye
  // durumu SATIRINDA okur ve mesajı kalıcı `_ALP_MSG` durumuna yazar) bayrak AÇIKÇA verilir.
  // Bayrak bir gevşeklik değil bir BEYANdır: muafiyet sayılabilir olur ve sessizce yayılamaz
  // (kaç yerde kullanıldığı testte çivilidir).
  if (opts.hamYanit) return r;
  // GÖVDE BİR KEZ OKUNUR, HAM METİN KORUNUR: JSON olmayan bir hata gövdesinde (vekil 502'si,
  // HTML hata sayfası) `detail` yoktur ama gövdenin kendisi operatörün elindeki TEK ipucudur.
  let ham = "";
  try { ham = await r.text(); }
  catch (e) { ham = ""; }   // YASA 4 · işaretli yutma: gövde okunamadı; durum kodu YİNE DE fırlar, sessiz başarı YOK
  let govde = null;
  try { govde = ham ? JSON.parse(ham) : null; }
  catch (e) { govde = null; }   // YASA 4 · işaretli yutma: gövde JSON değil; ham metin aşağıda gerekçe olarak kalır
  const d = govde ? govde.detail : null;
  // 422'de FastAPI `detail`i bir LİSTE verir — dizgeye çevrilmezse "[object Object]" basılırdı.
  const detay = (typeof d === "string" && d) ? d
    : (d != null ? JSON.stringify(d) : (ham ? ham.slice(0, 300) : ""));
  throw new ApiHata(r.status, detay, govde, path);
}
// ---- EYLEM HATASININ YÜZEYİ — SESSİZ DAL YOK (v219 · YASA 4 pano yüzeyi) ---------------------
// Panonun yazma yolları (onayla · uygula · reddet · başlat · durdur) bugüne dek ÜÇ ayrı biçimde
// bitiyordu: kimi hatayı kendi mesaj kutusuna yazıyor, kimi `alert` ediyor, kimi de BOŞ `catch`e
// düşürüyordu. Üçüncüsü ölçülen kusurun ta kendisi ve en pahalısı: reddedilen bir onay, hiç
// gönderilmemiş bir istekle ekranda AYNI görünüyordu.
// TEK GÖVDE: mesaj kutusu VARSA oraya yazılır (sayfa yeniden çizilmeden okunabilsin diye), YOKSA
// `alert` düşer. Hiçbir dal sessiz değildir — dönüş değeri hangi dalın koştuğunu söyler.
// GEREKÇE KIRPILMAZ, KİMLİK ÖNEKİ KORUNUR: sunucu 409'u `[kimlik] <gerekçe>` biçiminde yazıyor ve
// o önek operatörün `POST /api/approvals/{id}`ye geçireceği DİZGEnin ta kendisidir.
function eylemHatasiYaz(hedef, e, onEk) {
  const metin = String((e && e.message) || e || "bilinmeyen hata");
  const kutu = (typeof hedef === "string") ? $(hedef) : (hedef || null);
  if (kutu) {
    kutu.innerHTML = `<span class="neg">✗ ${esc(metin)}</span>${onEk ? ` <span class="hint">${esc(onEk)}</span>` : ""}`;
    return true;
  }
  alert((onEk ? onEk + "\n\n" : "") + metin);   // kutusu olmayan yüzey SESSİZ KALAMAZ
  return false;
}
// SATIR BAŞINA MESAJ KUTUSU — İD İLE DEĞİL ÖZNİTELİKLE, VE AKTİF SAYFANIN İÇİNDEN.
// Gizli sayfa DOM'dan silinmez ("gizli sayfa silinmez", alanSayfasi beyanı) ve aynı beceri iki
// yüzeyde birden listelenebilir (Onaylar gelen kutusu + Öğrenme öneri kartı). Sabit bir `id`
// olsaydı `getElementById` belge sırasındaki İLKİNİ döndürür, ret mesajı OPERATÖRÜN BAKMADIĞI
// sayfaya yazılırdı — sessiz yutmanın en ikna edici taklidi.
function eylemKutusu(anahtar) {
  const sayfa = document.querySelector(".page.active") || document;
  const a = String(anahtar == null ? "" : anahtar).replace(/["\\\]]/g, "");
  return a ? sayfa.querySelector(`[data-eylem-msg="${a}"]`) : null;
}
// ---- KISA ÖMÜRLÜ YANIT ÖNBELLEĞİ + BOŞTA ÖN-YÜKLEME (2026-07-28) ---------------------------
// Ölçüm: pano, işlem döngüsü ve Hermes beyniyle AYNI Python sürecinde koşuyor
// (serve.sh: MERIDIAN_AUTOSTART_CYCLE=1, MERIDIAN_AUTOSTART_HERMES=1). Onlar CPU işi yaparken
// GIL'i tutuyor ve panonun her isteği arkalarında kuyruğa giriyor: /api/today tek başına 13,7 ms,
// ağır bir istek uçarken 109,8 ms — sekiz kat. Bir görünüme İLK girişte bu 4-5 saniyeye çıkıyor.
//
// İki kapı: (1) aynı uç kısa pencerede tekrar istenirse ağ'a çıkılmaz; (2) açılıştan sonra boşta
// kalan ilk anda her görünümün ucu SIRAYLA ısıtılır — paralel değil, çünkü tek süreci boğmak
// tam da kaçındığımız şey. Kullanıcı bir görünüme tıkladığında veri çoğu zaman zaten elde.
//
// NEDEN VERİ, RENDER DEĞİL: alan sayfası kabuğu her çizimde `recReset()` çağırıyor — açık
// çekmeceyi kapatır ve kayıt defterini siler. Arka planda görünüm render etmek, kullanıcının
// BAKTIĞI sayfadaki satırları ölü bırakırdı. Önbellek fetch katmanında, DOM'a hiç dokunmaz.
const JCACHE_TTL_MS = 15000;       // sunucunun kendi bütünlük TTL'i 20 sn — bunun ALTINDA kalır,
                                   // yani istemci sunucunun kendi bayatlık sınırından eski veri sunmaz
const j = async u => {
  const hit = _JC.get(u);
  if (hit && (performance.now() - hit.t) < JCACHE_TTL_MS) return hit.p;
  // `!r.ok` KONTROLÜ BURADAN KALKTI (v219): `apiFetch` artık 2xx dışını `ApiHata` olarak
  // FIRLATIYOR ve o hata gövdedeki `detail`i taşıyor — buradaki eski kontrol yalnız durum kodunu
  // basıyordu ("→ HTTP 409"), yani sunucunun gerekçesini tam da bu katman siliyordu.
  const p = apiFetch(u).then(r => r.json())
    .catch(e => { _JC.delete(u); throw e; });   // hata önbellekte KALMAZ
  _JC.set(u, { t: performance.now(), p });
  return p;
};
// Görünüm başına tek uç — RENDER gövdelerinden çıkarıldı, elle senkron tutulur.
const PREFETCH = ["/api/agent", "/api/signals", "/api/diagnostics", "/api/alpaca", "/api/secrets"];
function warmViews() {
  let i = 0;
  const next = () => {
    if (i >= PREFETCH.length) return;
    const u = PREFETCH[i++];
    // Süreci boğmamak için SIRAYLA ve boşta: biri bitmeden diğeri başlamaz.
    j(u).catch(() => {}).then(() => setTimeout(next, 250));
  };
  next();
}
addEventListener("load", () => {
  const idle = window.requestIdleCallback || (f => setTimeout(f, 1200));
  idle(() => warmViews(), { timeout: 3000 });
});
// SABİT ARALIKLA ISITMA YOK: süreç zaten doygun, düzenli bir damla onu daha da yavaşlatırdı.
// Bunun yerine kullanıcı sekmeye DÖNDÜĞÜNDE ısıtılır — birazdan bir şeye tıklayacağı an.
document.addEventListener("visibilitychange", () => {
  if (document.visibilityState === "visible") warmViews();
});
// download/link URL (token in query, since <a href> can't send a header) — same-origin needs neither
const dl = path => API_BASE + path + (API_TOKEN ? (path.includes("?") ? "&" : "?") + "token=" + encodeURIComponent(API_TOKEN) : "");
const esc = s => (s == null ? "" : String(s)).replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const trn = (x, d = 0) => { const n = Number(x); return (x == null || !Number.isFinite(n)) ? "—" : n.toLocaleString("tr-TR", { minimumFractionDigits: d, maximumFractionDigits: d }); };
const money = x => x == null ? "—" : "$" + trn(x, 2);
const pctf = (x, d = 2) => { const n = Number(x); return (x == null || !Number.isFinite(n)) ? "—" : "%" + (n * 100).toLocaleString("tr-TR", { minimumFractionDigits: d, maximumFractionDigits: d }); };   // fraction -> localized Turkish %
const cls = x => x == null ? "" : (x > 0 ? "pos" : (x < 0 ? "neg" : ""));
// ÖN EKLİ DEĞER — değer yoksa ÖN EK DE BASILMAZ.
// `L${d.autonomy_level}` boş veride "Lundefined", `v${s.strategy_version}` "vundefined"
// üretiyordu. Bunlar bir sayı gibi görünür (harf + jeton) ama hiçbir şey ölçmez — trn()'in
// "—" dediği yerde şablonun uydurma kaçırması. Aynı yasa, tipografik hâli.
// Görsel doğrulama sunucusunda (boş /api/*) yakalandı, 2026-08-01.
const onk = (p, v) => (v == null || v === "" || (typeof v === "number" && !Number.isFinite(v))) ? "—" : `${p}${v}`;
// KAZANCA AÇIK İŞARET — renk TEK kanal olmasın.
// pctf/money pozitifte işaret basmıyor: "%12,34" ile "%-12,34" arasındaki tek fark, biri için
// İŞARETİN YOKLUĞU. Yokluk bir işaret değildir. Renk körü bir okuyucu (ve gri basılmış bir ekran
// görüntüsü) için ayırt edici tek kanal renge kalıyordu — oysa cls() zaten "bu bir kazanç/kayıp"
// diyor. Kod tabanının R ve IC değerlerinde kullandığı sözleşme buydu ("+0,214R"); yüzde ve para
// okumaları o sözleşmenin dışında kalmıştı. Yeni glif sözlüğü GETİRİLMEDİ: ok yerine mevcut "+".
// İşaret % ve $'ın İÇİNE girer — "%+12,34", "+%12,34" değil (Türkçe'de birim önce gelir).
const isr = (x, metin) => {
  const n = Number(x);
  if (x == null || !Number.isFinite(n) || n <= 0) return metin;
  const s = String(metin);
  return (s[0] === "%" || s[0] === "$") ? s[0] + "+" + s.slice(1) : "+" + s;
};
const TAG = { GO: "t-go", REVIEW: "t-rv", NO_GO: "t-no", pass: "t-go", reject: "t-no" };

const REGIME_TR = { trend_up: "yükseliş trendi", trend_down: "düşüş trendi", chop: "yatay/kararsız", high_vol: "yüksek dalgalanma" };
const HSTATUS = {
  live: ["canlı", "s-ok"], promoted: ["terfi etti", "s-ok"],
  rejected_by_backtest: ["backtest reddetti", "s-rj"], rejected_by_guard: ["guard reddetti", "s-rj"],
  rejected_by_confirmation: ["teyit dilimi reddetti", "s-rj"],
  // Y1 SERT KAPI (v130): kapı ölçümü GEÇTİ, doğrulama kapısı reddetti. Ayrı etiket şart — aynı
  // "backtest reddetti" kovasına atmak, panoda kapı istatistiğini sessizce kirletirdi.
  rejected_by_dsr: ["DSR sert kapısı reddetti", "s-rj"],
  rejected_by_pbo: ["PBO sert kapısı reddetti (süreç overfit)", "s-rj"],
  rolled_back: ["geri alındı", "s-rb"], proposed: ["önerildi", "s-rj"],
};

// ---- plain-Turkish glossary (shown as tooltips + in the "Terimler ne demek?" panel) ----
const TERMS = {
  exposure_tavani: "Bugün, piyasanın havasına göre en fazla ne kadar sermayenin riske atılabileceği (0–%100). %0 ise bugün yeni alım yok.",
  mevcut_exposure: "Şu anda açık pozisyonlarda fiilen riskte olan sermaye oranı.",
  distribution: "Büyük kurumların yoğun sattığı gün sayısı (son 25 seans). Çok olması piyasanın zayıfladığına işarettir; azı iyidir.",
  ftd: "Follow-through day: düşüşten sonra hacimli, güçlü bir toparlanma günü — yeni yükselişin teyidi.",
  onay_bekleyen: "Senin bakman için hazır bekleyen fırsat (plan) sayısı.",
  rr: "Risk:Ödül oranı. Kazanırsan, kaybetme riskinin kaç katını kazanırsın. 2,5R = riske ettiğinin 2,5 katı hedef.",
  boyut: "Pozisyonun risk büyüklüğü. 1R ≈ hesabın %1'i; yani tek bir işlemde bu kadar riske girilir.",
  kapi: "Disiplin kapısının kararı. Kötü bir işlemi sana ulaşmadan durdurur.",
  kurulum: "Hissenin teknik formasyonu. breakout_vcp = fiyatın sıkışıp daraldıktan sonra yukarı kırılması (VCP kurulumu).",
  rs: "Relative Strength — göreceli güç (1–99). Hissenin diğer hisselere kıyasla ne kadar güçlü olduğu. Yüksek = güçlü.",
  skor: "Kurulumun kalite puanı (0–100). Yüksek = daha güçlü, daha güvenilir sinyal.",
  sharpe: "Getiriyi, alınan riske (dalgalanmaya) göre ölçer. Yüksek olması iyidir; 1'in üstü genelde iyi kabul edilir.",
  drawdown: "Zirveden yaşanan en sert düşüş yüzdesi — ne kadar 'acı' yaşandığını gösterir. Düşük olması iyidir.",
  skor_track: "Stratejinin genel başarı notu (−1 ile +1 arası). Artı = hedeflere yakın, eksi = kötü gidiyor.",
  getiri: "Başlangıç parasına göre bugüne dek elde edilen toplam kâr/zarar yüzdesi.",
  islem: "Açılıp kapanmış, yani tamamlanmış alım-satım sayısı.",
  equity: "Hesabın (paranın) zaman içindeki değişimi.",
  rejim: "Piyasanın genel havası: yükseliş trendi, yatay/kararsız, düşüş veya yüksek dalgalanma.",
  backtest: "Bir değişikliği geçmiş veriyle sınama. Örneklem-dışı (OOS) = ajanın daha önce hiç görmediği bir dönemde test etmek — en dürüst sınav.",
  hipotez: "Ajanın 'şu ayarı değiştirirsem sonuç iyileşir' tahmini. Önce test edilir; sadece gerçekten daha iyiyse uygulanır.",
  kalibrasyon: "Ajanın tahmini ile gerçekte olanın ne kadar örtüştüğü. Örtüşüyorsa ajan gerçekten öğreniyor demektir.",
  paper: "Kağıt üzerinde / sanal para. Gerçek para hiç riske girmez; sadece kaydı tutulur.",
  otonomi: "Ajanın yetki seviyesi. L0: sadece kağıt üzerinde, gerçek para yok. L1: her emir senin onayınla. L2: gerçek para, otonom. Güncel seviye panoda canlı gösterilir.",
  skill: "Ajanın kullandığı hazır analiz aracı (tarama, planlama, ders çıkarma gibi).",
  pipeline: "Sırayla çalışan analiz hattı: tara → planla → disiplin kapısından geçir.",
  minsample: "Bir değişikliğe canlı sonuçla güvenmek için gereken en az kapanmış işlem sayısı (goal.yaml'da tanımlı eşik). Altında 'skor' bilinmez sayılır.",
};
const T = (label, key, right) => `<span class="term${right ? ' r' : ''}" data-tip="${esc(TERMS[key] || '')}" tabindex="0">${label}</span>`;

// ================= KAYIT ÇEKMECESİ — panonun tek detay mekanizması ============================
// Matrisin etkileşimi operatörün beğendiği şeydi: hücreye bas, o kesitin kaydı SAĞDAN açılır,
// tablo yerinde kalır. Aynı hareket artık defterin bütün satırlarında geçerli — kapanmış işlem,
// plan, hipotez, olay. Bir satır ne sayfa değiştirir ne de kırpılır: kendi kaydını yanında açar.
// Tek kapı: openDrawer({title, eyebrow, bodyHTML, originEl}). `title`/`eyebrow` HAZIR HTML'dir
// (çağıran esc'ler); bodyHTML da öyle. Esc kapatır ve odak geldiği öğeye döner.
let _drawerOrigin = null;
// SEÇİLİ İŞARETİN TEK SEÇİCİSİ. Açılış ve kapanış aynı listeyi okumak ZORUNDA: v191'de dördüncü
// bir tıklanabilir yüzey (durum kartı) doğdu ve liste iki yerde elle tutulsaydı kart `.sel`
// sınıfını ÜSTÜNDE bırakırdı — çekmece kapalıyken hâlâ "seçili" görünen bir kart.
const _SECILI = ".pm-cell.sel,.rowbtn.sel,.durum-kart.sel";
function openDrawer({ title, eyebrow, bodyHTML, originEl }) {
  const dr = $("plotdrawer"); if (!dr) return;
  dr.innerHTML = `
    <div class="pd-head">
      <div><p class="pd-l">${eyebrow || "KAYIT"}</p>
        <h2 class="pd-t" id="pd-title">${title || ""}</h2></div>
      <button type="button" class="pd-x" data-act="closeDrawer" aria-label="Kaydı kapat">✕</button>
    </div>
    <div class="pd-body">${bodyHTML || ""}</div>`;
  dr.classList.add("open");
  document.body.classList.add("drawer-open");
  _drawerOrigin = originEl || (document.activeElement !== document.body ? document.activeElement : null);
  const x = dr.querySelector(".pd-x"); if (x) x.focus();
}
function closeDrawer() {
  const dr = $("plotdrawer"); if (!dr || !dr.classList.contains("open")) return;
  dr.classList.remove("open");
  document.body.classList.remove("drawer-open");
  document.querySelectorAll(_SECILI).forEach(el => el.classList.remove("sel"));
  const o = _drawerOrigin; _drawerOrigin = null;
  if (o && document.contains(o)) o.focus();
}
window.closeDrawer = closeDrawer;
// Odak tuzağı — aria-modal bir diyalog Tab'ı dışarı kaçırmamalı. Öğe kalıcı, içeriği değişken:
// dinleyici bir kez bağlanır, odaklanabilirler her seferinde yeniden okunur.
(function drawerKeys() {
  const dr = $("plotdrawer"); if (!dr) return;
  dr.addEventListener("keydown", e => {
    if (e.key === "Escape") { e.stopPropagation(); closeDrawer(); return; }
    if (e.key !== "Tab") return;
    const f = [...dr.querySelectorAll('button,[href],input,select,textarea,[tabindex]:not([tabindex="-1"])')]
      .filter(el => !el.disabled && el.offsetParent !== null);
    if (!f.length) return;
    const first = f[0], last = f[f.length - 1];
    if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
    else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
  });
})();
document.addEventListener("keydown", e => { if (e.key === "Escape") closeDrawer(); });

// ---- KAYIT DEFTERİ — satır ile kaydı arasındaki bağ ------------------------------------------
// Satır HTML'i saf fonksiyonlardan çıkıyor, dolayısıyla nesneyi satıra iliştirmenin yolu bir
// anahtar. Anahtar render başına sıfırlanır: aynı satır iki kez çizilse de defter şişmez.
const _REC = new Map();
let _recSeq = 0;
const rec = (kind, o) => { const k = "k" + (++_recSeq); _REC.set(k, { kind, o }); return k; };
function recReset() { closeDrawer(); _REC.clear(); }
// Satırı basılabilir yapan tek yardımcı. `<button>` kullanılabildiği yerde buton kullanılır;
// içinde başlık/paragraf olan slip (.hyp) HTML'de butona giremez — orada role+tabindex.
const rowAttrs = (k, label, asDiv) =>
  `${asDiv ? `role="button" tabindex="0"` : `type="button"`} data-rk="${k}" aria-label="${esc(label)}"`;
function openRecord(el) {
  const entry = _REC.get(el.dataset.rk); if (!entry) return;
  const build = RECORD_VIEW[entry.kind]; if (!build) return;
  const v = build(entry.o); if (!v) return;
  document.querySelectorAll(_SECILI).forEach(x => x.classList.remove("sel"));
  el.classList.add("sel");
  openDrawer({ eyebrow: v.eyebrow, title: v.title, bodyHTML: v.body, originEl: el });
  // İŞLEM ÇEKMECESİNİN FİYAT SEYRİ (K1, 2026-07-30): çekmece SENKRON kurulur (istemcinin elindeki
  // satırdan), seri ise ayrı bir uçtan gelir. Bu yüzden enjeksiyon asenkron: çekmece anında açılır,
  // seri gelince yerine oturur. Hata YUTULMAZ — "seri alınamadı" yazar, sessizce boş kalmaz.
  if (entry.kind === "trade") _fillTradeSeries();
}
async function _fillTradeSeries() {
  const box = $("pd-trade-series"); if (!box) return;
  const id = box.dataset.tradeId; if (!id) return;
  try {
    const d = await j("/api/trade/" + encodeURIComponent(id));
    const s = (d && d.series) || [];
    if (!s.length) { box.innerHTML = `<p class="hint" style="margin:0">Bu işlem için bar serisi yok (kaynak veri bulunamadı).</p>`; return; }
    // Kapanış serisi + giriş/çıkış işaretleri. `line()` para eğrisi için para birimi basıyor;
    // burada FİYAT var, o yüzden kendi küçük çizimi — aynı ölçek mantığı, farklı etiket.
    const W = 640, H = 150, pad = 26;
    const cs = s.map(p => p.c), mn = Math.min(...cs), mx = Math.max(...cs);
    const sx = i => pad + (s.length > 1 ? i / (s.length - 1) : 0.5) * (W - 2 * pad);
    const sy = v => H - pad - ((v - mn) / ((mx - mn) || 1)) * (H - 2 * pad);
    const path = s.map((p, i) => `${i ? "L" : "M"}${sx(i).toFixed(1)},${sy(p.c).toFixed(1)}`).join("");
    box.innerHTML = `<svg viewBox="0 0 ${W} ${H}" style="width:100%" role="img"
        aria-label="Fiyat seyri: ${esc(s[0].date)} ${trn(s[0].c, 2)} → ${esc(s[s.length-1].date)} ${trn(s[s.length-1].c, 2)}">
      <path d="${path}" fill="none" stroke="var(--accent)" stroke-width="2"/>
      <text x="${pad}" y="14" fill="var(--tx2)" font-size="10">${trn(s[0].c, 2)} · ${esc(s[0].date)}</text>
      <text x="${W - pad}" y="14" text-anchor="end" fill="var(--tx2)" font-size="10">${trn(s[s.length-1].c, 2)} · ${esc(s[s.length-1].date)}</text>
      </svg><p class="hint" style="margin:4px 0 0">${s.length} bar · en düşük ${trn(mn, 2)} · en yüksek ${trn(mx, 2)}</p>`;
  } catch (e) {
    box.innerHTML = `<p class="hint warn" style="margin:0">Seri alınamadı: ${esc(String(e).slice(0, 90))}</p>`;
  }
}
document.addEventListener("click", e => {
  const el = e.target.closest && e.target.closest("[data-rk]");
  if (el) openRecord(el);
});
document.addEventListener("keydown", e => {
  if (e.key !== "Enter" && e.key !== " ") return;
  const el = e.target.closest && e.target.closest('[data-rk][role="button"]');
  if (!el) return;
  e.preventDefault(); openRecord(el);
});
// çekmece gövdesinin ortak parçaları
const pdStat = (l, v, k) => `<div><p class="l">${l}</p><p class="v mono-num ${k || ""}">${v}</p></div>`;
const pdRow = (l, v) => v == null || v === "" ? "" : `<div class="srow"><span>${l}</span><b>${v}</b></div>`;

// ---- nav ----
const nav = $("nav");
addEventListener("scroll", () => nav.classList.toggle("stuck", scrollY > 20));

// ---- MOD JETONU — KOŞULSUZ KANAL (v196/KALEM-1) ----------------------------------------------
// ÖLÇÜLEN KUSUR (BASELINE-2026-08-06 §B.9 / T3): mod YALNIZ sağlıklı dalda basılıyordu.
// `t.halted` → "DURDURULDU", `t.stale` → "gecikmiş · N sn": her iki hâlde de "paper" hecesi
// DOM'DAN TAMAMEN KAYBOLUYORDU. Yani mod, tam da sistem bozukken görünmez oluyordu — ve bu
// alandaki en pahalı kaza sınıfı operatörün YANLIŞ MODDA olduğunu sanmasıdır; o yanılgı en çok
// bir arıza anında doğar. Kusur bir görüntü tercihi değil, bir güvenlik-görünürlüğü kusurudur.
//
// MOD BİR DURUM DEĞİLDİR, bu yüzden durum CÜMLESİNİN İÇİNDE taşınamaz: cümle üç dala ayrılıyor,
// mod ise dalsızdır. Ayrı bir jeton, sabit yerde, DÖRT HÂLDE DE (sağlıklı · halted · stale ·
// veri-yok) basılır. `#statuspill` zaten `role=status aria-live=polite` — jeton ekran okuyucuya
// da düşer, ikinci bir ARIA kanalı açılmaz.
//
// YENİ DİL/RENK YOK: jeton panonun MEVCUT `_chip` reçetesidir ve `t-vi` — bu panonun "hüküm yok"
// kanalı, akromatik (`--accent-tint`/`--accent-2`). Mod kroması bu turda AÇILMADI (T4 ayrı bir
// kalem ve `index.html` bu turda yazılabilir değil): paper/live ayrımı METNİN KENDİSİYLE taşınır
// ve `.tag` zaten `text-transform:uppercase` basar. `data-mod` özniteliği ayrı bir makine kanalı
// (yapısal test + mod kroması açıldığında CSS kancası) — bugün hiçbir rengi tetiklemez.
//
// SABİT DİZE YOK: mod ÖLÇÜMDEN gelir (`/api/today.mode` ← `config.MODE`). "paper" kelimesini koda
// çakmak, `MERIDIAN_MODE=live` olduğu gün panoyu yalancı yapardı — ve o yalan sessiz olurdu.
// ÖLÇÜLEMEYEN MOD UYDURULMAZ: uç düştüğünde ya da alan boş geldiğinde jeton "MOD ÖLÇÜLEMEDİ" der.
// SON BİLİNEN MODU HATIRLAYIP BASMAK (ffill) BİLEREK YAPILMADI: bu turun KALEM 2'de kapattığı
// kusur sınıfının ta kendisi, üstelik burada bedeli daha ağır — bayat bir "paper", canlı hesapta
// operatöre "kâğıttayım" dedirtir.
const MOD_OLCULEMEDI = "MOD ÖLÇÜLEMEDİ";
// D1 (2026-08-07) · MOD KROMASI AÇILDI — ve taşıyıcı YAPISAL. Yukarıdaki blok "mod kroması bu
// turda AÇILMADI (T4 ayrı bir kalem ve `index.html` bu turda yazılabilir değil)" diyordu; o kalem
// bu turda kapandı. `data-mod` artık İKİ yere yazılır: jetona (yerinde okuma) ve `<body>`ye —
// çünkü sayfanın üst kenar bandını süren seçici `body[data-mod]`dir ve Design rules modun "any
// pixel"den okunabilir olmasını istiyor, bir çipin görüş alanında olmasını değil.
// TEK KAYNAK: ikisi de AYNI ölçümden (`/api/today.mode`) beslenir; ikinci bir mod hesabı yok.
// ÖLÇÜLEMEDİ ÜÇÜNCÜ HÂLDİR: `paper`a düşmez, banda KESİK desen bastırır.
function modJetonu(mod) {
  const m = (mod == null || String(mod).trim() === "") ? null : String(mod).trim().toLowerCase();
  const beyan = m ? `emir yolu modu: ${m} (ölçüm: /api/today.mode ← config.MODE)`
                  : "mod ÖLÇÜLEMEDİ — uç okunamadı ya da `mode` alanı boş geldi; son bilinen mod BASILMAZ";
  // BANT YAZIMI BU FONKSİYONUN İÇİNDE ve AYRI BİR YARDIMCIDA DEĞİL: v196'nın Node koşum
  // düzeneği `modJetonu`yu kaynaktan kesip tek başına çalıştırıyor. Dışarıdan çağrılan bir
  // yardımcı, o düzenekte `ReferenceError` verir — yani ölçüm aracını kırar. `typeof document`
  // koruması aynı sebeple: DOM'suz koşumda sessizce atlar, tarayıcıda yazar.
  if (typeof document !== "undefined" && document.body)
    document.body.dataset.mod = m || "olculemedi";
  return `<span class="tag t-vi" data-mod="${esc(m || "olculemedi")}" title="${esc(beyan)}">${
    esc(m || MOD_OLCULEMEDI)}</span> `;
}
// AYNI CÜMLE İKİNCİ KEZ DUYURULMAZ: `#statuspill` bir `aria-live` bölgesidir ve şerit 15 sn'de bir
// yeniden yazılıyor. HALT hâlinde metin sabittir ("DURDURULDU"); onu her turda yeniden yazmak ekran
// okuyucuya aynı cümleyi dakikada dört kez okuturdu — alarm yorgunluğunun en ucuz kaynağı.
let _DURUM_HTML = "";
function durumYaz(html) {
  if (html === _DURUM_HTML) return;
  _DURUM_HTML = html;
  $("statustext").innerHTML = html;
}

async function refreshStatus() {
  let t;
  try { t = await j("/api/today"); }
  catch (e) {
    $("pulse").className = "dot halt";
    // VERİ-YOK DALI DA MODU TAŞIR: jeton DOM'dan düşmez, ölçülemediğini SÖYLER.
    durumYaz(modJetonu(null) + "bağlantı yok");
    return {};
  }
  HALTED = t.halted;
  const pulse = $("pulse");
  pulse.className = "dot pulse" + (t.halted ? " halt" : (t.stale ? " stale" : ""));
  const age = t.heartbeat_age_seconds == null ? "—" : Math.round(t.heartbeat_age_seconds) + " sn önce";
  // Durum cümlesinden "paper" ÇIKARILDI — aynı gerçeği iki yerde yazmak, ilk düzenlemede ayrışır.
  const durum = t.halted ? "DURDURULDU" : (t.stale ? `gecikmiş · ${age}` : `canlı · ${onk("L", t.autonomy_level)} · ${age}`);
  durumYaz(modJetonu(t.mode) + esc(durum));
  const hb = $("haltbtn");
  hb.textContent = t.halted ? "DEVAM" : "HALT";
  hb.title = t.halted ? "Devam et: yeni alımlara tekrar izin ver" : "Acil durdur: yeni hiçbir alım yapılmaz";
  hb.style.borderColor = hb.style.color = t.halted ? "var(--green)" : "var(--red)";
  // SESSİZ HAT ARTIK HER SAYFADA (S2R-1) ve nabzı BURADAN alır — 15 saniyelik tur zaten dönüyor.
  // ATEŞLE-UNUT: HALT/nabız satırı teşhis ucunu BEKLEMEZ. Bir alt sistemin yavaşlığı, panonun en
  // üstteki durum satırını geciktiremez; teşhis geldiğinde şerit yerinde güncellenir.
  // ÖLÇÜM: /api/diagnostics 3,984 ms (ilk çağrıda 11,130 ms) — 15 sn'de bir bu, ihmal edilebilir.
  j("/api/diagnostics").then(d => sessizHatGlobal(d && d.sessiz_hat)).catch(() => {});
  return t;
}
// Şerit tek yerde çizilir ve tek yere yazılır. İkinci bir çizim noktası olsaydı iki farklı
// tazelikte iki şerit doğar ve hangisinin doğru olduğu ancak saate bakılarak anlaşılırdı.
function sessizHatGlobal(sh) {
  const el = $("sessizhat-global");
  if (!el) return;
  // ÖLÇÜLEMEDİYSE BOŞ KALIR, "sağlıklı" YAZMAZ: teşhis ucu düştüğünde yeşil bir satır göstermek,
  // bu şeridin var olma sebebinin tam tersi olurdu (uydurma yasağı).
  el.innerHTML = sh ? sessizHat(sh) : "";
}
async function toggleHalt() {
  if (!HALTED && !confirm("Acil durdur (HALT)?\n\nBir sonraki muma kadar YENİ hiçbir alım yapılmaz. Mevcut pozisyonlar yönetilmeye devam eder. İstediğinde 'DEVAM' ile açarsın.")) return;
  // BU KOLUN SESSİZ DÜŞMESİ EN PAHALISI (v219): operatör "durdurdum" sanıp ekrandan ayrılırsa
  // sistem çalışmaya devam eder. `apiFetch` artık fırlatıyor; hata KAPAK MESAJIYLA yüzeye çıkar
  // ve şerit tazelenmez — yani rozet eski hâlinde kalarak da "olmadı" der.
  try { await apiFetch(HALTED ? "/api/resume" : "/api/halt", { method: "POST" }); }
  catch (e) { eylemHatasiYaz(null, e, (HALTED ? "DEVAM" : "DURDURMA") + " isteği sunucuya işlenemedi — kol ÇEKİLMEDİ."); return; }
  await refreshStatus();
  const active = document.querySelector(".sitem.on")?.dataset.p || VARSAYILAN_ROTA;
  if (RENDER[active]) await RENDER[active]();
  revealActive();
}
window.toggleHalt = toggleHalt;

// ---- BASİT/UZMAN GÖRÜNÜM ANAHTARI SİLİNDİ (2026-07-27, operatörün açık talebi) ----
// İki görünüm vardı: Basit teknik telemetriyi gizliyor, Uzman açıyordu. Anahtar üç şeyi birden
// bozuyordu. (1) Varsayılan Basit'ti, yani pano AÇILDIĞINDA eksik başlıyordu. (2) Basit
// alternatifleri (.simple-only) aynı okumanın sulandırılmış kopyalarıydı — iki bakım yüzeyi,
// tek gerçek. (3) En ağırı: spineHTML sarı uyarıları Basit'te TAMAMEN düşürüyordu, yani nabız
// dokuz saattir ölüyken pano "Sistem sakin" yazıyordu. Her şey artık yalnızca GÖRÜNÜR.
//
// Sabit nav'ın GERÇEK yüksekliğini ölç ve --navh'a yaz — rozetler ikinci satıra sararsa nav
// büyür ve shell'in sabit dolgusu bunu karşılamaz; karşılama başlığı barın ALTINA girerdi
// (2026-07-22). Yeniden boyutlamada ve rozetler her tazelendiğinde yeniden ölç.
function syncNavHeight() {
  const nav = document.querySelector("nav");
  if (nav) document.documentElement.style.setProperty("--navh", nav.offsetHeight + "px");
}
window.syncNavHeight = syncNavHeight;
addEventListener("resize", syncNavHeight);
if (window.ResizeObserver) {
  const _nv = document.querySelector("nav");
  if (_nv) new ResizeObserver(syncNavHeight).observe(_nv);   // rozet sarması yüksekliği değiştirir
}
// İLK ÖLÇÜM ŞART: --navh yazılmazsa shell 76px'lik YEDEK dolguyla kalır ve bar daha uzunsa
// sayfanın ilk öğesi — yani durum şeridi — barın ALTINDA gizlenir. Bu çağrı, silinen görünüm
// anahtarının içinde duruyordu; anahtar gidince ölçüm de gitmişti (2026-07-27, canlı yakalandı:
// nav 109px, shell dolgusu 93px, şeridin üst 16px'i barın arkasındaydı).
syncNavHeight();
addEventListener("load", syncNavHeight);

// ---- KRİZ KAPAĞI — yıkıcı kontroller yalnız TIKLAYINCA açılır ----------------------------
// Eskiden :hover ve :focus-within açıyordu: imleç üst bardan geçerken "Flatten — TÜM pozisyonlar"
// paneli niyet gecikmesi olmadan içeriğin üstüne düşüyor, ve odak-içi kuralı yüzünden dört yıkıcı
// düğme sayfanın 4-7. sekme durakları oluyordu — HALT'tan bile önce. Kapak artık gerçek bir düğme.
function setKs(open) {
  const wrap = $("kswrap"), cover = $("kscover"), grp = $("ksgroup");
  if (!wrap || !cover || !grp) return;
  grp.classList.toggle("open", open);
  cover.setAttribute("aria-expanded", open ? "true" : "false");
}
window.toggleKs = () => {
  const grp = $("ksgroup");
  setKs(!(grp && grp.classList.contains("open")));
};
// dışarı tıklama ve Esc kapatır — açık kalmış bir kriz paneli içeriği örtmemeli
document.addEventListener("click", e => {
  const w = $("kswrap");
  if (w && !w.contains(e.target)) setKs(false);
});
document.addEventListener("keydown", e => {
  if (e.key === "Escape" && $("ksgroup")?.classList.contains("open")) { setKs(false); $("kscover")?.focus(); }
});

async function go(id) {
  // "operasyon#failsub" biçimi: görünüme git VE oradaki bloğa kaydır. Triyaj şeridinin bir
  // uyarısı sayfanın ortasındaki bir bloğu işaret ettiğinde, operatörü sayfanın başına bırakıp
  // "şimdi ara" demek döngüyü yarıda kesiyordu. Çapa render'dan SONRA çözülür.
  let anchor = "";
  if (typeof id === "string" && id.includes("#")) [id, anchor] = id.split("#");
  id = ROUTE_ALIAS[id] || id;
  document.querySelectorAll(".sitem").forEach(t => {
    const on = t.dataset.p === id;
    t.classList.toggle("on", on);
    if (on) t.setAttribute("aria-current", "page"); else t.removeAttribute("aria-current");
  });
  document.querySelectorAll(".page").forEach(p => p.classList.toggle("active", p.id === "page-" + id));
  if (location.hash.slice(1) !== id) location.hash = id;
  scrollTo({ top: 0, behavior: "instant" });
  try {
    // GEÇİŞ AĞI BEKLEMEZ (2026-07-28). Ölçüm: /api/diagnostics 3.984 ms (ilk çağrıda 11.130 ms),
    // /api/alpaca 1.510 ms. `await RENDER[id]()` görünüm değişimini bu uçlara zincirliyordu:
    // go('operasyon') 4.009 ms sürüyor ve o süre boyunca ekran ESKİ sayfada donuyordu.
    //
    // Kural: DAHA ÖNCE RENDER EDİLMİŞ bir sayfaya dönerken beklemek yok — eldeki veri hemen
    // gösterilir, tazeleme arkada yürür ve bitince yerinde güncellenir. Yalnız İLK açılışta
    // (gösterilecek hiçbir şey yokken) iskelet konur ve beklenir; orada beklemek dürüsttür,
    // çünkü alternatif boş ekrandır.
    const _pg0 = $("page-" + id);
    // BOŞLUK ARTIK METİNDEN ÖLÇÜLÜR, innerHTML'den DEĞİL (S2R-1). Yeni alan sayfaları HTML'de
    // boş kaplarla (`.alan-bas` + `.alan-bolum`) doğuyor: `innerHTML.trim()` onları "çizilmiş"
    // sayar ve İLK açılışta ne iskelet konur ne beklenir — operatör boş beyaz bir sayfaya bakar
    // ve orada bir şey yüklendiğini hiçbir yerden bilmez.
    const _bos = !_pg0 || !_pg0.textContent.trim();
    // İSKELET VE HATA KABIN TAMAMINI DEĞİL BAŞLIK YUVASINI EZER: `_pg0.innerHTML = ...` demek,
    // eski görünümlerin kaplarını (`#page-market`, `#page-brifing`, …) DOM'dan silmek olurdu —
    // render'ları o kaplara yazıyor, yani sonraki çizim sessizce hiçbir yere düşerdi.
    const _yuva = () => { const el = $("page-" + id); return el && (el.querySelector(".alan-bas") || el); };
    if (_bos && _pg0) {
      const y = _yuva();
      if (y) y.innerHTML = '<div class="card rise in"><p class="mut" style="padding:6px 0">yükleniyor…</p></div>';
    }
    const _hata = e => {
      const el = _yuva();
      if (el) el.innerHTML = `<div class="card rise in"><h2 class="t">Veri yüklenemedi</h2>` +
        `<p class="mut">${esc(String(e))}</p>` +
        `<p class="mut" style="font-size:12px;margin-top:8px">Sunucu çalışıyor mu? Terminalde <b>./serve.sh</b> ile başlatabilirsin.</p></div>`;
    };
    const _p = RENDER[id] ? RENDER[id]() : null;
    const _bitti = () => { if (_pg0) { _pg0.removeAttribute("aria-busy"); _pg0.classList.remove("tazeleniyor"); } };
    if (_bos || anchor) {
      // İlk açılış (gösterilecek hiçbir şey yok) ya da çapa hedefi (render'dan sonra var olur):
      // beklemek burada dürüsttür, alternatifi boş ekran ya da sahte bir kaydırma.
      try { await _p; } catch (e) { _hata(e); }
      _bitti(); revealActive(!_bos);
    } else if (_p) {
      // ESKİ VERİ SESSİZCE DURMAZ: tazeleme sürerken sayfa bunu söyler. Gösterilen rakamlar
      // gerçek ve daha önce çekilmiş, ama "şu an" olmayabilir; saklamak yanıltıcı olurdu.
      _pg0.setAttribute("aria-busy", "true");
      _pg0.classList.add("tazeleniyor");
      _p.then(() => { _bitti(); revealActive(true); }).catch(e => { _bitti(); _hata(e); });
    }
  } catch (e) {
    // Aynı gerekçe yukarıdaki `_yuva()` ile: kabın tamamını ezmek eski görünüm kaplarını siler.
    const _kap = $("page-" + id);
    const el = _kap && (_kap.querySelector(".alan-bas") || _kap);
    if (el) el.innerHTML = `<div class="card rise in"><h2 class="t">Veri yüklenemedi</h2>` +
      `<p class="mut">${esc(String(e))}</p>` +
      `<p class="mut" style="font-size:12px;margin-top:8px">Sunucu çalışıyor mu? Terminalde <b>./serve.sh</b> ile başlatabilirsin.</p></div>`;
  }
  revealActive(true);
  // Çapa ancak RENDER.<id>() bittikten sonra DOM'da olur; bu yüzden burada, revealActive'ten
  // sonra çözülür. Blok bulunamazsa sessizce vazgeçilir — sahte bir kaydırma yapılmaz.
  if (anchor) {
    const a = document.getElementById(anchor);
    if (a) {
      const nav = parseInt(getComputedStyle(document.documentElement).getPropertyValue("--navh")) || 76;
      scrollTo({ top: a.getBoundingClientRect().top + scrollY - nav - 16, behavior: "smooth" });
      // Odağı da götür: klavye kullanıcısı için kaydırma tek başına bir varış değildir.
      a.setAttribute("tabindex", "-1"); a.focus({ preventScroll: true });
    }
  }
}
function revealActive(instant) {
  // instant=true: ARKA PLAN POLL re-render'ı (2026-07-23). Sprint/reflect poll'u her 5s tüm sayfayı
  // yeniden çizip fade+slide animasyonunu TEKRAR oynatıyordu — öğrenme ekranı sürekli "titriyor"
  // görünüyordu. Poll güncellemelerinde animasyonu atla: içerik anında yerinde durur, göz yorulmaz.
  // BAŞLIK MERTEBESİ BURADA DÜZELTİLİR, RENDER'IN İÇİNDE DEĞİL (S2R-1). Sebep ölçüldü: eski
  // görünümlerin çoğu KENDİNİ yeniden çiziyor (sprint/Hermes yoklaması her 5-8 sn, intradayArm,
  // ackReject, saveSecret) ve her yeniden çizim kendi `<h1>`ini geri koyuyor. Düzeltmeyi yalnız
  // sayfa açılışına bağlasaydık ilk yoklamada geri düşerdi — yani sessizce çalışmayan bir
  // erişilebilirlik önlemi olurdu. `revealActive` her çizim yolunun ortak boğazı.
  _bolumBasliklariniIndir(document.querySelector(".page.active"));
  const els = document.querySelectorAll(".page.active .rise");
  if (els.length) els[0].getBoundingClientRect();
  els.forEach((el, i) => {
    el.style.transitionDelay = instant ? "0ms" : (i % 6) * 50 + "ms";
    el.style.transition = instant ? "none" : "";
    el.classList.add("in");
  });
}
addEventListener("hashchange", () => {
  const h = ROUTE_ALIAS[location.hash.slice(1)] || location.hash.slice(1);
  const known = VIEWS.some(v => v[0] === h);   // alias'lar yukarıda zaten çözüldü
  if (known && $("page-" + h) && !$("page-" + h).classList.contains("active")) go(h);
});
window.go = go;

// ---- ŞERİT İKONLARI --------------------------------------------------------------------------
// 56px'lik marj şeridi tek Türkçe baş harf basıyordu: B K O I Ö A. O (Operasyon) ile Ö (Öğrenme)
// 13px'te yalnız iki noktayla ayrılıyordu — aynı yerde, aynı ağırlıkta, ayırt edilemez. Yerine
// 20px satır çizimi: kanonun kendi kalemi (currentColor, 1.5px kontur, yuvarlatılmış uç, dolgu
// yok), hiçbiri diğerine benzemeyen altı siluet. Glif aria-hidden; adı .vis-label taşır.
const _ico = p => `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"
  stroke-linecap="round" stroke-linejoin="round" focusable="false" aria-hidden="true">${p}</svg>`;
const RAIL_ICON = {
  // Çıkış — kapıdan dışarı çıkan ok. Diğer gliflerle aynı kalem: 24 birim kutu, 1.5px kontur.
  cikis: _ico('<path d="M14.5 20.5h-8a2 2 0 0 1-2-2v-13a2 2 0 0 1 2-2h8"/><path d="M15 12h5.5"/><path d="m18 8.5 3.5 3.5-3.5 3.5"/>'),
  // Tema — HEDEFİ gösterir, mevcut hâli değil: gündüzdeyken ay (gece'ye geçer), gecedeyken güneş.
  // Düğmenin üstündeki etiket de hedefi söyler, yani ikon ile yazı aynı şeyi anlatır.
  tema_gece: _ico('<path d="M20 14.2A8.2 8.2 0 0 1 9.8 4 8.5 8.5 0 1 0 20 14.2Z"/>'),
  tema_gunduz: _ico('<circle cx="12" cy="12" r="4.2"/><path d="M12 2.5v2M12 19.5v2M4.2 4.2l1.4 1.4M18.4 18.4l1.4 1.4M2.5 12h2M19.5 12h2M4.2 19.8l1.4-1.4M18.4 5.6l1.4-1.4"/>'),
  // ---- BEŞ YÜZEY (D2-b). Anahtarlar VIEWS kimlikleridir. Yüzeyler birleşince glif de birleşti:
  //      kokpit penceresi ①'e, gece halkası ②'ye (döngünün çıktısı KARARdır), kadran ③'e (sorunun
  //      kendisi "sağlıklı mı"), defter ④'te, sürgü ⑤'te kaldı. Mum (eski `veri`) ve defter kapağı
  //      (eski `portfoy`) EMEKLİ: okuyucusu kalmayan bir glif, okunmayan bir yazımdır (YASA 6) —
  //      taşıdıkları sorular ③ ve ②'nin gliflerinin altında yaşıyor.
  //      Hiçbiri diğerine benzemez — 20px'te ayırt edilebilirlik ölçütü.
  // ① Bugün — dört bölmeli tek pencere: kokpitin kendisi
  bugun: _ico('<rect x="3.5" y="3.5" width="17" height="17" rx="1.5"/><path d="M3.5 12h17M12 3.5v17"/>'),
  // ② Karar — kapanan halka: her gece bir tur, turun sonunda bir karar
  karar: _ico('<path d="M20 12a8 8 0 1 1-2.6-5.9"/><path d="M20.5 3.8v3.6h-3.6"/>'),
  // ③ Sağlık — kadranlı gösterge: sistem sağlıklı mı?
  saglik: _ico('<path d="M4 18a8 8 0 1 1 16 0"/><path d="M4 18h16"/><path d="m12 18 4-5"/>'),
  // ④ Öğrenme — açık defter
  ogrenme: _ico('<path d="M12 7.5C12 6 10 4.5 6.5 4.5H4v13h2.5c3.5 0 5.5 1.5 5.5 3"/><path d="M12 7.5C12 6 14 4.5 17.5 4.5H20v13h-2.5c-3.5 0-5.5 1.5-5.5 3"/>'),
  // ⑤ Kilitler — sürgülü ayarlar
  kilitler: _ico('<path d="M4 7.5h8.5M17.5 7.5H20M4 16.5h4.5M13.5 16.5H20"/><circle cx="15" cy="7.5" r="2.5"/><circle cx="11" cy="16.5" r="2.5"/>'),
};

// ---- SERMAYENİN KÖKENİ (2026-08-01) ------------------------------------------------------------
// ÖLÇÜLEN KUSUR: pano "Sermaye 94.457,91$" yazıyordu. Sayı doğruydu, ANLATTIĞI şey yanlıştı —
// 100.000$ başlangıçtan ANTRENMAN TOHUMUNUN (replay_seed, 95 satır) −5.542,09$'ı düşülmüş hâliydi
// ve canlı-kâğıt işlem sayısı SIFIRDI. Operatör her sabah bir simülasyon artefaktını "sistemin
// kaybı" diye okuyordu. İki ekleme, ikisi de /api/today `sermaye_koken` bloğundan:
//   * değerin YANINDA türü söyleyen kısa ibare  → "gerçek-canlı (0 işlem)"
//   * ALTINDA sönük ayrı satır                  → tohumun etkisi + ayrıştırılıp ayrıştırılmadığı
// BOYANMA KURALI: renk `k.renk`ten gelir ve gerçek-canlı P&L 0 iken NÖTRDÜR. Hiç işlem yapmamış
// bir çağa kırmızı/yeşil vermek, tam da bu turun kapattığı yanlış okumanın görsel hâliydi.
// İKİ TÜKETİCİ, TEK İŞLEV: kenar şeridi ve Bugün kahramanı aynı satırı çizer — iki kopya olsaydı
// biri güncellenip diğeri bayatlar ve pano kendi içinde çelişirdi.
const SERMAYE_RENK = { poz: "pos", neg: "neg", notr: "" };

function sermayeIbaresi(k) {
  if (!k) return "";                       // uç bu alanı vermiyorsa SUS — uydurma etiket yok
  return `<span class="mut" style="font-weight:400;letter-spacing:0">${esc(k.ibare || "")}</span>`;
}

function sermayeKokenSatiri(k, { kisa = false, ibareyle = false } = {}) {
  if (!k) return "";
  const parca = [];
  // KENAR ŞERİDİNDE İBARE BU SATIRA İNER, `<b>`nin İÇİNE DEĞİL: `.acct .r b` kuralı
  // `white-space:nowrap` + `flex:none` taşır (index.html:330), yani değerin yanına eklenen her
  // kelime satırı GENİŞLETİR ve dar şeritte "Sermaye" etiketini taşırırdı. Geniş kahraman kartında
  // ibare değerin hemen altında kendi satırında durur.
  if (ibareyle && k.ibare) parca.push(esc(k.ibare));
  // BAYAT NABIZ BEYAN EDİLİR. Büyük sayı `today.equity`den gelir ve o da NABIZDAN okunur
  // (analytics.today: hb.equity ?? pf.cash). Ayrıştırma uygulandığı an kitap yeni tabana geçer ama
  // nabız worker bir tur koşana kadar ESKİ tabanı taşır — yani pano birkaç dakika iki farklı
  // sermaye biliyor olur. Sessiz kalmak, tam da bu turun kapattığı "sayı doğru, anlattığı yanlış"
  // hâlinin küçük bir tekrarı olurdu.
  if (k.nabiz_ayrisik) parca.push(`<span class="warn">nabız bayat — kitap ${
      money(k.gercek_canli_sermaye)} (worker ilk turda tazeler)</span>`);
  if (k.tohum_etkisi_usd != null) {
    // Tohum etkisi ÖLÇÜLDÜ. Reset sonrası 0 YAZILMAZ: değer olduğu gibi durur, DURUMU değişir.
    parca.push(`tohum (antrenman) etkisi ${money(k.tohum_etkisi_usd)} · ${esc(k.tohum_etkisi_ibare || "")}`);
  } else if (k.tohum_etkisi_neden) {
    // ÜÇÜNCÜ HÂL: "etki yok" değil "ölçülemedi" — nedeni yanında durur (uydurma yasağı).
    parca.push(`tohum etkisi ölçülmedi${kisa ? "" : ` — ${esc(k.tohum_etkisi_neden)}`}`);
  }
  if (k.ayrisik && k.reset_tarihi) parca.push(`ayrıştırma ${esc(String(k.reset_tarihi).slice(0, 10))}`);
  if (k.tohum_islem_n) parca.push(`${k.tohum_islem_n} tohum satırı defterde kaldı`);
  if (!parca.length) return "";
  return `<p class="sub mut" style="margin-top:4px;font-size:11px;line-height:1.45">${
      parca.join(" · ")}</p>`;
}

// ---- AYNA ROZETİ: İKİ BOYUT, TEK CÜMLE -------------------------------------------------------
// (2026-08-13 · docs/DENETIM-SPLIT-SINIFI-2026-08-13.md §3.1)
// KUSUR NEYDİ: bu rozet YALNIZ `hb.mirror_drift`e bakıyordu ve o alan FİYAT sapmasını ölçer
// (loop.py:25 `MIRROR_DRIFT_TOL` — iç sim dolumu ↔ gerçek Alpaca dolumu). ADET sapması
// (`position_drift`, `loop.reconcile_broker_state`) BAŞKA bir gerçektir ve nabızda anahtarı hiç
// yoktu. Canlı
// ölçüm (2026-08-12T22:01Z): fiyat sapması False, adet sapması True, 4/4 pozisyon ~2 kat ayrık —
// rozet "ayna uyumlu" (yeşil) yazarken aynı ekranın eylem şeridi "Alpaca aynasında sapma var"
// diyordu. Kök neden bir DÜZELTMENİN yan ürünüydü: P6 tekilleştirmesi (app.js:9739-9744) sapma
// metnini mutabakat masasına taşıdı, bu özet rozeti BAŞKA bir alandan besleniyordu ve taşınmadı.
//
// SÖZLEŞME: iki boyut da doğruysa "ayna uyumlu" YAZILABİLİR; biri bile sapıksa yazılamaz ve HANGİ
// boyutun saptığı adıyla söylenir. Ölçülmemiş boyut ÜÇÜNCÜ hâldir (ne yeşil ne kırmızı) — nabız
// artık `mirror_checked` taşır ve ölçülmeyen tur iki alanı da `null` yazar
// (`loop.ayna_sapma_alanlari` — satır numarası değil AD verilir: bu turun kendi dersi).
// GERİYE UYUM: dağıtım öncesi yazılmış bir nabızda `position_drift` anahtarı YOKTUR (undefined) →
// adet boyutu "ölçülmedi" okunur. Eski nabzı "temiz" saymak, kapatılan kusuru geri açmak olurdu.
function aynaRozeti(hb) {
  const _boyut = v => (v === true ? "sapma" : v === false ? "uyumlu" : "olculemedi");
  const fiyat = _boyut(hb.mirror_drift), adet = _boyut(hb.position_drift);
  const sapan = [fiyat === "sapma" ? "fiyat" : null, adet === "sapma" ? "adet" : null].filter(Boolean);
  const olcumsuz = [fiyat === "olculemedi" ? "fiyat" : null,
                    adet === "olculemedi" ? "adet" : null].filter(Boolean);
  const kunye = `fiyat sapması: ${fiyat === "olculemedi" ? "ÖLÇÜLMEDİ" : fiyat}`
              + ` · adet sapması: ${adet === "olculemedi" ? "ÖLÇÜLMEDİ" : adet}`
              + (hb.mirror_checked === false ? " · bu turda mutabakat KOŞMADI" : "");
  if (sapan.length) return { metin: `sapma: ${sapan.join("+")}`, sinif: "neg", baslik: kunye };
  // "AYNA YOK" ≠ "AYNA ÖLÇÜLEMEDİ" (loop._skip sınıfı). Dahili brokerde kıyaslanacak bir ayna
  // hiç yoktur; o hâli amber basmak, hiç var olmayan bir arızayı sonsuza dek raporlamak olurdu —
  // ve "kalıcı bir uyarı, hiç uyarı olmamakla aynı bilgiyi taşır" (bu panonun kendi kuralı).
  if (hb.mirror_skip_sinifi === "ayna_yok")
    return { metin: "ayna yok", sinif: "", baslik: `${kunye} · dahili broker — kıyaslanacak ayna yok` };
  if (olcumsuz.length === 2) return { metin: "ayna ölçülmedi", sinif: "warn", baslik: kunye };
  if (olcumsuz.length) return { metin: `${olcumsuz[0]} ölçülmedi`, sinif: "warn", baslik: kunye };
  return { metin: "ayna uyumlu", sinif: "pos", baslik: kunye };
}

async function buildSidebar(today, x) {
  // Nav bir İNDEKS'tir, etiket listesi değil: her görünümün altında o sayfanın tek satırlık CANLI
  // özeti okunur — kullanıcı tıklamadan "orada ne var?" sorusunun cevabını görür. Tüm değerler
  // API'den; veri yoksa satır dürüstçe kısalır, asla uydurulmaz. x = brifing'in hermes paketi
  // (öğrenme/araç özetleri için; periyodik tazelemede olmayabilir → o satırlar sabit kalır).
  const hb = today.heartbeat || {};
  const _ayna = aynaRozeti(hb);     // İKİ boyut (fiyat + adet) — bkz. aynaRozeti şerhi
  const vc = today.verdict_counts || {};
  const adayN = (today.todays_plans || []).length;
  // Rozet artık BEKLEYEN KARAR sayısını taşır (aday sayısını değil): aday bilgi, bekleyen karar
  // ise senden iş ister. Aday sayısı alt satırda GO/REVIEW kırılımıyla zaten okunuyor.
  //
  // ÜÇ AYRI SAYI, ÜÇ AYRI AD (pano turu 2026-07-31). Eskiden `inbox_count ?? pending_count` vardı
  // ve bu iki farklı gerçeği tek rozette birleştiriyordu: `inbox_count` GELEN KUTUSUDUR (silahlanma
  // kapısını geçen ölçüm + skill revizyon taslağı + Eksen-2 önerisi — senden İŞ isteyen karar),
  // `pending_count` ise o seans KURULAN PLAN sayısıdır (GO/REVIEW) ve kimseden bir şey istemez.
  // Alan bir kez düşünce pano "10 bekleyen karar" yazıyordu; canlı gerçek 0'dı.
  // KURAL: "bekleyen karar" YALNIZ ölçülmüş `inbox_count` ile yazılır ve yalnız o dolgulu rozet
  // alır. `inbox_count` ÖLÇÜLMEMİŞSE (alan hiç yok) rozet yine bir sayı taşıyabilir ama ADINI
  // değiştirir — "kurulan plan", sönük stil. Sayı aynı kalsa bile cümle artık doğrudur.
  const inboxN = today.inbox_count == null ? null : (Number(today.inbox_count) || 0);
  const planN = today.pending_count == null ? null : (Number(today.pending_count) || 0);
  const ROZET_TR = { inbox: "bekleyen karar", plan: "kurulan plan", aday: "aday" };
  const rozet = inboxN ? "inbox" : (inboxN == null && planN ? "plan" : "aday");
  // ROZET ARTIK "karar" ÜSTÜNDE (D2-b): onay kuyruğu ve adaylar aynı yüzeyin ardışık iki bölümü.
  // Rozet içeriğin GERÇEKTEN durduğu maddede olmalı — başka bir maddeye basmak, sayıyı gördüğü
  // yerde bulamayan bir operatör üretirdi.
  const badges = { karar: rozet === "inbox" ? inboxN : (rozet === "plan" ? planN : adayN) };
  const LOOP_TR = { no_hypotheses: "henüz fikir yok", no_ship_v1_stands: "kapı geçilmedi",
                    shipped_awaiting_min_sample: "sonuç birikiyor", closing: "döngü kapanıyor",
                    closed_learning: "öğreniyor", closed_weak_cal: "zayıf kalibre" };
  if (x) _HERMES_PAKET = x; else x = _HERMES_PAKET;   // bkz. _HERMES_PAKET beyanı (S2R-1)
  const learn = (x && x.learning) || {}, hst = (x && x.status) || {};
  const posN = (today.open_positions || []).length;
  // Alt satır = o ALAN SAYFASININ tek satırlık CANLI özeti (S2R-1: anahtarlar yedi yeni kimlik).
  // Birleşen sayfaların özetleri de birleşti: Portföy sermayeyi ve pozisyonu taşır, Öğrenme araç
  // sayısını, Veri Sağlığı evren ve bayatlık sayısını.
  // BEŞ YÜZEY, BEŞ ÖZET (D2-b). Birleşen sayfaların özetleri de birleşti ve birleşirken TEKRAR
  // AYIKLANDI: eski `subs.gozetim` "ayna uyumlu/SAPMA" yazıyordu, eski `subs.portfoy` sermayeyi ve
  // pozisyonu; ikisi aynı yüzeye düşseydi şerit satırı beş parçaya çıkardı. Kural: bir yüzeyin
  // özeti EN FAZLA dört parça ve her parça o yüzeyin KENDİ sorusunun bir kelimesi.
  const subs = {
    // ① Bugün'ün özeti sayfanın KENDİ cümlesidir: sakin mi, senden bir şey mi bekliyor?
    // Sayı tekrarı YOK — aynı rakamı hem şeritte hem kartta göstermek, ikisini de zayıflatır.
    // P4 TEKİLLEŞTİRMESİ: "nabız gecikmiş" BURADAN DÜŞTÜ (üçüncü kopyaydı). Nabzın tazeliği
    // `#statuspill`de YAŞIYLA birlikte duruyor ve sessiz hattın `veri` segmenti sapmayı adıyla
    // açıyor; şeritte üçüncü kez, üstelik süresiz yazmak sinyali seyreltiyordu.
    bugun: [today.halted ? "DURDURULDU" : (hb.breaker_tripped ? "kesici tetikli" : "sakin")],
    // ② Karar: gecenin çıktısı (bekleyen karar + kapı kırılımı) ve o kararın düştüğü kitap.
    karar: [rozet === "inbox" ? `${inboxN} bekleyen karar`
            : (rozet === "plan" ? `${planN} kurulan plan · gelen kutusu ölçülmedi` : null),
            ...(adayN ? [vc.GO ? `${vc.GO} GO` : null, vc.REVIEW ? `${vc.REVIEW} REVIEW` : null,
                         vc.NO_GO ? `${vc.NO_GO} NO_GO` : null] : ["sinyal yok"]),
            `${posN} pozisyon`],
    // ③ Sağlık: evren/tazelik özeti /api/market'ten gelir. ① onu ARKA PLANDA çeker ve bu iki
    // alanı doldurur; hiç ölçülmediyse satır dürüstçe kısalır — tahmini bir sayı uydurma olurdu.
    // "ayna uyumlu/SAPMA" BURADAN DÜŞTÜ (P6 tekilleştirmesi): aynanın tek evi mutabakat masası.
    saglik: [MARKET_N != null ? `${MARKET_N} hisse` : null,
             MARKET_STALE ? `${MARKET_STALE} bayat bar` : null,
             today.data_ok === false ? "veri kapısı KAPALI" : "veri temiz"],
    ogrenme: [hb.version ? `v${hb.version}` : null,
              hst.reflecting ? "düşünüyor…" : (LOOP_TR[learn.loop_state] || null),
              x && x.skill_count ? `${x.skill_count} araç` : null],
    // P7 + P10 TEKİLLEŞTİRMESİ (D2-b · baseline §2):
    //   * "HALT çekili" BURADAN DÜŞTÜ (dördüncü kopyaydı). Durdurmanın evi üçtür ve üçü de
    //     AYRI ROL taşır: `#statuspill` her-an bandı, triyaj şeridi yalnız çekiliyken çalan
    //     alarm (adresiyle), `kilitler#mudahale` kolun kendi durumu. Ray dördüncü bir kopyaydı.
    //   * OTONOMİ SEVİYESİ BURAYA GELDİ, `.acct` kutusundan çıktı. Üç kopyası vardı; kalan iki
    //     rolden biri budur, çünkü "ajanın yetkisi ne?" TAM OLARAK ⑤'in sorusudur. `.acct` bir
    //     broker/sermaye kutusudur ve otonomi oraya bir yorum satırıyla açıklanacak kadar uzaktı.
    kilitler: [onk("L", today.autonomy_level)],
  };
  // Hangi görünüm açık? Şerit her tazelemede yeniden kurulduğu için go()'nun yazdığı
  // aria-current siliniyordu — aktiflik yalnız BİÇİMLE anlatılıyordu, ekran okuyucuya hiç
  // söylenmiyordu. Aktif kimlik burada tekrar hesaplanır ve rozetle birlikte yazılır.
  let act = document.querySelector(".sitem.on")?.dataset.p;
  if (!act) { const h = location.hash.slice(1), r = ROUTE_ALIAS[h] || h;
              act = VIEWS.some(v => v[0] === r) ? r : VARSAYILAN_ROTA; }
  const items = VIEWS.map(([id, label]) => {
    const b = badges[id];
    // Rozetin ADI olur: çıplak "1" ekran okuyucuda hiçbir şey demiyordu. Ad, sayının NEYİ
    // saydığını da söyler — dolgulu rozet bekleyen KARAR, sönük rozet aday ya da kurulan plandır.
    const dolgulu = id === "karar" && rozet === "inbox";
    const rozetAdi = id === "karar" ? ROZET_TR[rozet] : "aday";
    const badge = b ? `<span class="pillc${dolgulu ? '' : ' q'}" role="img" aria-label="${
        esc(label)}, ${b} ${rozetAdi}">${b}</span>` : "";
    const sub = (subs[id] || []).filter(Boolean).join(" · ");
    // KENAR ŞERİDİ: matris arayüzün kendisi olduğundan görünüm listesi 224px'lik bir menü
    // kolonu olmaktan çıkıp dar bir marj şeridine indi. Şeritte görünümün İKONU durur (eskiden
    // tek Türkçe baş harf vardı ve O/Ö 13px'te ayırt edilemiyordu); tam etiket ve canlı özeti
    // hover/odakta yaprağın ÜSTÜNE biner — ızgara hiç oynamaz. Glif aria-hidden, adı .vis-label
    // taşır; `sub` DOM'da kalır: dar ekranda ve ekran okuyucuda hâlâ okunur.
    const full = sub ? `${label} — ${sub}` : label;
    const on = id === act;
    return `<button class="sitem${on ? ' on' : ''}" data-p="${id}" data-act="go" data-a1="${id}"${on ? ' aria-current="page"' : ''}>` +
           `<span class="top"><span class="lbl" aria-hidden="true">${RAIL_ICON[id] || ""}</span>` +
           `<span class="vis-label">${esc(label)}</span>${badge}</span>` +
           `${sub ? `<span class="sub">${sub}</span>` : ""}</button>`;
  }).join("");
  $("side").innerHTML = `
    <p class="slab">HESAP</p>
    <div class="acct">
      <div class="r"><span>${esc(today.broker || "Dahili broker")}</span><b class="${_ayna.sinif}" title="${esc(_ayna.baslik)}">${esc(_ayna.metin)}</b></div>
      <div class="r"><span>Sermaye</span><b class="${SERMAYE_RENK[(today.sermaye_koken || {}).renk] || ""}">${money(today.equity)}</b></div>
      ${sermayeKokenSatiri(today.sermaye_koken, { kisa: true, ibareyle: true })}
      <!-- MOD HER DURUMDA GÖRÜNÜR (Dalga-0 hükmü) — bu satır o yüzden kalır. Otonomi seviyesi
           ⑤'in ray özetine taşındı (P10 tekilleştirmesi): bu kutu hesabın kutusudur, yetkinin
           değil, ve aynı harf 200 piksel arayla üç kez basılıyordu. -->
      <div class="r"><span>Mod</span><b>${esc(today.mode || MOD_OLCULEMEDI)}</b></div>
      <div class="r"><span>Nabız</span><b class="${today.stale ? 'warn' : 'pos'}">${today.stale ? 'gecikmiş' : 'canlı'}</b></div>
    </div>
    <p class="slab">GÖRÜNÜM</p>${items}
    ${_temaDugmesiHTML()}
    ${_PAROLA_KURULU ? `<button class="sitem cikis" id="cikis-btn" type="button" data-act="cikisYap">
      <span class="top"><span class="lbl" aria-hidden="true">${RAIL_ICON.cikis}</span>
      <span class="vis-label">Çıkış yap</span></span></button>` : ""}`;
}

// ---- TEMA ANAHTARI ---------------------------------------------------------------------------
// YERİ RAYIN SONU, üst bar DEĞİL. İki sebep:
//  1. Üst barda HALT ve KRİZ var ve HALT'ın SABİT bir evi olmak zorunda (kas hafızası; sarmada
//     kaymaması için ayrıca kural yazılmıştı). Bara bir düğme eklemek o evi 44px kaydırırdı.
//  2. Tema bir OPERASYON kontrolü değil, bir oturum tercihidir — çıkışla aynı ailedendir.
//     Ray sonu zaten o aile için ayrılmış bölge.
// Düğme HEDEFİ söyler ("Gece teması" = basınca geceye geçer), mevcut hâli değil: tek düğmeli bir
// anahtarda mevcut hâli yazmak, düğmenin ne yapacağını okuyucunun tersine çevirmesini gerektirir.
function _temaDugmesiHTML() {
  const gece = window.MeridianTema && window.MeridianTema.al() === "gece";
  // Etiket ve aria-label AYRI yazılır, biri diğerine ek getirilerek üretilmez: "Gece teması"
  // + "ne geç" → "temasıne geç" çıkıyordu. Türkçe ek ünlü uyumuna bağlıdır ve dizgi
  // birleştirmesiyle doğru sonuç vermez.
  const hedef = gece ? "Gündüz teması" : "Gece teması";
  const eylem = gece ? "Gündüz temasına geç" : "Gece temasına geç";
  return `<button class="sitem tema" id="tema-btn" type="button" data-act="temaDegistir"
      aria-label="${eylem}">
      <span class="top"><span class="lbl" aria-hidden="true">${
        gece ? RAIL_ICON.tema_gunduz : RAIL_ICON.tema_gece}</span>
      <span class="vis-label">${hedef}</span></span></button>`;
}

window.temaDegistir = () => {
  if (!window.MeridianTema) return;   // theme.js yüklenmediyse sessizce hiçbir şey yapma
  window.MeridianTema.degistir();
};

// ---- OLAY DELEGASYONU — satır içi onclick/oninput'un yerine ----------------------------------
// NEDEN: dağıtım CSP'si (deploy/Caddyfile) `script-src 'self'` olmalı, ve o başlık satır içi
// OLAY ÖZNİTELİKLERİNİ de bloklar — sadece <script> bloklarını değil. Ölçüldü: app.js'te 34,
// index.html'de 6 öznitelik vardı. O CSP ile dağıtım yapılsaydı pano ÇİZİLİR ama hiçbir düğme
// iş görmezdi: gezinme, çekmece, KRİZ grubu ve HALT dahil. Sessizce ölü bir acil durdurma,
// eksik bir güvenlik başlığından tehlikelidir — bu yüzden öznitelikler kaldırıldı, CSP değil.
//
// AD ÇÖZÜMLEME KAYITLIDIR, window[ad] DEĞİL. Doğrudan `window[el.dataset.act]()` çağırmak,
// DOM'a bir `data-act` sokabilen herkese sayfadaki HER global fonksiyonu açardı. Aşağıdaki
// küme bir izin listesidir: kayıtlı olmayan bir ad sessizce düşer.
// Geç bağlama bilinçli: fonksiyonlar bu noktadan SONRA da tanımlanıyor, o yüzden referans
// değil AD tutuluyor ve çözümleme tıklama anında yapılıyor.
const EYLEMLER = new Set([
  // alpacaClose v195-a'da DÜŞTÜ: yıkıcı ucun ikinci ve tek-onaylı yolu kapandı (bkz. Alpaca kartı).
  // ADI BU YORUMDA TIRNAKSIZ YAZILIR — izin listesini okuyan test tırnaklı her adı KAYITLI sayar
  // ve kaldırılmış bir eylem, kendi mezar taşı yüzünden "kayıtlı ama tanımsız" görünürdü.
  "ackAlerts", "ackReject", "ackRejectAll", "addPoolKey", "alpacaSubmit",
  "olayAc",
  "applySkillRec", "cikisYap", "clearSecret", "closeDrawer", "denetimAra", "filterLessons", "go",
  "hermesBackfill", "hermesCtl", "hermesReflect", "intradayArm", "kararKaydet", "kbdOverlay",
  "kmMod", "korumaKur", "mktChip",
  "mktPaint", "mktSort", "notifyTest", "opCancelOpen", "opFlatten", "opLearnHaltToggle",
  "opSoftHalt", "planOnayla", "saveSecret", "skillRev", "sprintStart", "sprintStop", "temaDegistir",
  "testKey", "toggleHalt", "toggleKs",
]);

// Argüman kuralı: data-a1/a2 dizgidir. "true"/"false" boole'a çevrilir — intradayArm ve
// kbdOverlay boole bekliyor ve dizgi "false" JS'te DOĞRUDUR, yani çevrilmezse `kbdOverlay("false")`
// paneli kapatmak yerine açardı. Sayı çevrimi YAPILMIYOR: mevcut eylemlerin hiçbiri sayı almıyor
// ve "007" gibi bir kimliği sessizce 7'ye çevirmek gerçek bir hata sınıfı olurdu.
const _arg = v => v === undefined ? undefined : (v === "true" ? true : (v === "false" ? false : v));

function _eylemCalistir(el, olay) {
  const ad = el.dataset.act;
  if (!ad || !EYLEMLER.has(ad)) return;
  const fn = window[ad];
  if (typeof fn !== "function") {
    // Sessiz yutma DEĞİL: kayıtlı ama tanımsız bir ad, izin listesi ile kodun ayrıştığı
    // anlamına gelir ve bu bir programlama hatasıdır — görünür olmalı.
    console.error("kayıtlı eylem tanımsız:", ad);
    return;
  }
  olay.preventDefault();
  const a = [_arg(el.dataset.a1), _arg(el.dataset.a2)].filter(x => x !== undefined);
  fn(...a);
}

document.addEventListener("click", e => {
  const el = e.target.closest("[data-act]");
  if (el && !el.dataset.actOn) _eylemCalistir(el, e);
});
// `data-act-on="input"` taşıyanlar tıklamada DEĞİL yazarken çalışır (arama kutuları).
document.addEventListener("input", e => {
  const el = e.target.closest('[data-act][data-act-on="input"]');
  if (el) _eylemCalistir(el, e);
});

// Kapak altındaki "Halt Learning" düğmesi tıklama ANINDAKİ durumu tersine çeviriyordu
// (`opLearnHalt(!window._LEARN_HALTED)`). Bir öznitelikte hesap yapılamayacağı için sarmalayıcı:
// aynı hesap, aynı anda, artık bir fonksiyonun içinde.
window.opLearnHaltToggle = () => window.opLearnHalt(!window._LEARN_HALTED);

// Düğmenin kendi etiketi tema değişiminde güncellenmeli. Tüm rayı yeniden çizmek yerine YALNIZ
// düğmeyi değiştiriyoruz: ray yeniden çizilirse odak kaybolur ve klavyeyle gezinen operatör
// düğmenin üstünden düşer.
addEventListener("meridian:tema", () => {
  const btn = document.getElementById("tema-btn");
  if (!btn) return;
  const yeni = document.createRange().createContextualFragment(_temaDugmesiHTML()).firstElementChild;
  const odakta = document.activeElement === btn;
  btn.replaceWith(yeni);
  if (odakta) yeni.focus();
});

// ---- ÇIKIŞ -----------------------------------------------------------------------------------
// YERİ RAYIN SONU, üst bar DEĞİL: üst barda HALT ve KRİZ duruyor. Oturumu kapatan bir düğmeyi
// acil durdurmanın yanına koymak, iki ayrı niyeti bir kas hafızasında birleştirir — yanlış
// tıklamanın bedeli asimetrik (biri oturum, diğeri işlem durdurma).
//
// Çıkış YALNIZ parola kuruluyken görünür: parola yokken kapatılacak bir oturum da yoktur ve
// düğme hiçbir şey yapmayan bir vaat olurdu.
window.cikisYap = async () => {
  try { await apiFetch("/api/logout", { method: "POST" }); }
  catch (e) { /* ağ gitse bile aşağıdaki yerel temizlik yapılır */ }
  _oturumAcik = false;
  _JC.clear();          // önbellekte kalan yanıtlar bir sonraki operatöre görünmesin
  recReset();           // kayıt defteri + açık çekmece
  kapiyiGoster(false, _tlsRiski());
  $("gate-msg").className = "gate-msg ok";
  $("gate-msg").textContent = "çıkış yapıldı";
};

// ---- DURUM ŞERİDİ — panonun tek zorunlu cümlesi: "benden bir şey lazım mı?" Tüm sinyaller CANLI:
// heartbeat (halted/breaker/drift/stale/data), onay kuyruğu, Hermes bütçesi, Alpaca uzlaştırması.
// Sakinken görünmez denecek kadar sessiz; müdahale gerekince ekrandaki en yüksek sesli şey.
function spineHTML(t, h, rc, ws) {
  const hb = t.heartbeat || {};   // breaker/mirror sinyalleri heartbeat'in İÇİNDE yaşar — düz t.* okumak
  const acts = [], attn = [];     // iki kritik sinyali sessizce köreltiyordu
  // ---- İÇ HEDEFLER D2-b'DE BEŞ YÜZEYE ÇEVRİLDİ (S2R-2'nin adresleri korunuyor) ---------------
  // Bu şerit panonun en yüksek sesli yüzeyi ve her çipi bir ADRESTİR. S2R-1'de adresler eski
  // görünüm adlarıydı ("performans", "ayarlar", "operasyon#failsub"); alias sayesinde doğru
  // SAYFAYA gidiyorlardı ama sayfanın BAŞINA bırakıyorlardı — operatör "3 emir reddedildi"
  // çipine basıp beş bölümlük bir sayfanın tepesine düşüyordu. Artık bölüm çapasına gider.
  // D2-b'de yüzey adı değişti (`portfoy#` → `karar#`, `veri#` → `saglik#`); ESKİ adres yazan
  // her dış bağ ROUTE_ALIAS'ın (b) sınıfıyla çözülmeye devam eder — burada YENİSİ yazılır ki
  // panonun kendi içinde tek adres dili kalsın.
  if (t.halted) acts.push(["sistem DURDURULDU — sağ üstten DEVAM", "kilitler#mudahale"]);
  if (hb.breaker_tripped) acts.push(["günlük kayıp devre kesici tetikli", "kilitler#mudahale"]);
  // NABIZ ARTIK ADET BOYUTUNU DA TAŞIYOR (2026-08-13): `hb.position_drift` eklendi
  // (`loop.ayna_sapma_alanlari` → `health.write_heartbeat`).
  // Bu satır zaten mutabakat tarafından okuyordu, yani şerit DOĞRUYDU — eksik olan HESAP rozetiydi
  // (bkz. aynaRozeti). Nabız bacağı yine de tamamlanır: `/api/alpaca` yavaş/kopuk olduğunda `rc`
  // boş gelir ve şerit o turda YALNIZ nabza bakar; adet sapmasını orada da görebilmeli.
  if (hb.mirror_drift || hb.position_drift || (rc && (rc.mirror_drift || rc.position_drift))) acts.push(["Alpaca aynasında sapma var", "karar#mutabakat"]);
  // REDDEDİLEN EMİR ARTIK KAYDA GİDER (2026-07-27). Eskiden hedef "ayarlar" idi ve oradaki
  // karşılık tek bir cansız cümleydi: hangi hisse, broker ne dedi, şimdi ne yapılmalı —
  // hiçbiri yanıtlanmıyordu. Ürünün var olma nedeni olan an, en zayıf desteğe sahipti.
  // Hedef artık Operasyon'daki #failsub bloğu; satırlar basılabilir, çekmecede tam kayıt var.
  // SAYI YALNIZ AÇIK RETLERİ SAYAR (2026-07-27): kapatılanlar pakette kalır ama şeridi besleyemez.
  // Şeridin tek sorusu "ŞU AN müdahale gerekiyor mu?"dur; beş günlük, görülmüş bir ret o soruya
  // "evet" diyemez — ve kalıcı bir kırmızı, hiç kırmızı olmamakla aynı bilgiyi taşır.
  const _fsOpen = ((rc || {}).failed_submissions || {}).open || [];
  if (_fsOpen.length) acts.push([`${_fsOpen.length} emir reddedildi`, "karar#failsub"]);
  if (rc && ((rc.positions || {}).engine_orphans || []).length) acts.push(["motor yetimi pozisyon", "karar#mutabakat"]);
  // P9 / N1 TEKİLLEŞTİRMESİ (D2-b · baseline §2 + §4). Bu satır `pending_count > 0 &&
  // autonomy_level >= 1` koşuluyla "N onay bekliyor" basıyordu ve İKİ ayrı kusur taşıyordu:
  //   (a) ÖLÜ KOL — sistem L0'da; koşul kurulduğundan beri bir kez bile ateşlemedi.
  //   (b) YANLIŞ AD — `pending_count` o seans KURULAN PLAN sayısıdır ve `analytics.py`nin kendi
  //       yorumu "kimseden bir şey istemez" diyor; onay bekleyen sayaç `inbox_count`tur.
  // Yani şerit, hiç çalışmayan bir kolda yanlış adlandırılmış bir sayıyı vaat ediyordu. "Bugün
  // ne bekliyor?" sorusunun TEK evi ① Bugün'ün "Bugün ne var" kartıdır (`inbox_count` + REVIEW
  // kırılımı, aynı `onay_bekliyor` bayrağından). Kol SİLİNDİ, sayı taşınmadı — çünkü taşınacak
  // doğru bir sayı yoktu.
  // Bayatlığın SÜRESİ yazılır: "gecikmiş" bir bayrak, "9 sa gecikmiş" bir karardır (bekle mi,
  // zamanlayıcıya bak mı). Süre API'nin kendi alanından gelir; yoksa yazılmaz.
  const _hbAge = sureTR(t.heartbeat_age_seconds);
  if (t.stale) attn.push([`nabız gecikmiş${_hbAge ? ` · ${_hbAge}` : ""} — zamanlayıcıyı kontrol et`, "saglik#cizelge"]);
  if (rc && rc.api_ok === false) attn.push(["broker API'sine erişilemiyor — ayna körlemesine", "karar#mutabakat"]);
  // Bu uyarı BUGÜNE KADAR HİÇ ÇIKMADI: `rc` broker_reconcile.json'dır ve o dosyada `stream_ok`
  // anahtarı YOKTUR — `undefined === false` hep yanlış. Yani akış koptuğunda şerit sessiz kalıyordu;
  // sessizlik "sorun yok" diye okunur. Akış sağlığı artık AYRI parametreyle gelir (ws) ve dürüsttür.
  const _wsDown = wsDownFor(ws);
  if (ws && ws.stream_ok === false)
    attn.push([`yürütme akışı koptu${_wsDown ? ` · ${_wsDown}` : ""} — dolumlar gecikmeli görünür`, "karar#mutabakat"]);
  if (t.data_ok === false) attn.push(["veri kalitesi kapısı kapalı — bugün yeni alım yok", "saglik#veriboru"]);
  if (((h || {}).spend || {}).over_budget) attn.push(["Hermes bütçesi doldu — ücretsiz beyinde", "ogrenme#hermes"]);
  // HİÇBİR UYARI BAŞKA BİR UYARININ VARLIĞI YÜZÜNDEN DÜŞMEZ (2026-07-27).
  // Eski kod iki kez susuyordu. (1) `simple ? [] : attn` — varsayılan Basit görünümde sarı
  // sinyallerin TAMAMI atılıyordu; nabız dokuz saattir ölüyken pano "Sistem sakin" yazıyordu.
  // (2) `acts.length ? acts : attn` — bir kırmızı varsa sarıların hepsi listeden düşüyordu;
  // yani devre kesici tetiklendiği an, akışın kopmuş olduğunu SÖYLEYEN satır siliniyordu.
  // Canlılık uyarısı (bayat nabız, ölü yürütme akışı, tetiklenmiş kesici) hiçbir koşulda
  // bastırılamaz. Hepsi listelenir, kırmızılar önce; bant en yüksek sesli sinyale boyanır.
  const items = [...acts, ...attn];
  const cls = acts.length ? "act" : (attn.length ? "attn" : "calm");
  const msg = acts.length ? "Senden bir şey bekliyor." : (attn.length ? "Göz atmaya değer." : "Sistem sakin — bugün senden bir şey beklemiyor.");
  const chips = items.map(([txt, page]) => page
    ? `<button data-act="go" data-a1="${page}">${esc(txt)}</button>` : `<span>${esc(txt)}</span>`).join("");
  return `<div class="spine ${cls}" id="triage-spine" role="status" aria-live="polite">` +
         `<span class="msg">${msg}</span>${items.length ? `<span class="items">${chips}</span>` : ""}</div>`;
}

// ---- SIRADAKİ SEANS — niyet yüzeyi. Canlı-paper modda operatörün akşam sorusu "yarın ne
// yapacaksın?"dır: açılışta ateşlenecek her silahlı emri, tam seviyeleriyle ve ayna durumuyla
// gösterir. Boş hali de birinci sınıf: "emir yok" bir özür değil, bir bilgidir.
function nextSessionCard(t) {
  const armed = t.armed_plans || [];
  const sent = new Set(t.alpaca_submitted || []);
  if (!armed.length)
    return `<div class="card rise"><h2 class="t">Sıradaki seans · niyet</h2>
      <div class="empty">Silahlı emir yok — açılışta yeni tarama yapılır; kapıyı geçen çıkarsa burada listelenir.</div></div>`;
  const rows = armed.map(p => {
    const mirror = sent.has(p.id)
      ? '<span class="tag t-go">aynada</span>'
      : (p.broker_status === "failed_broker_rejection" ? '<span class="tag t-no">RET</span>'
                                                       : '<span class="tag t-vi">gönderilecek</span>');
    return `<div class="trow" style="grid-template-columns:64px 1fr 90px 90px 90px 92px">
      <span class="tick">${esc(p.ticker)}</span>
      <span class="mut">${esc(p.setup || "")} · tetik ${trn(p.entry_trigger, 2)}</span>
      <!-- D1 (2026-08-07) · YÖN SIZINTISI KAPANDI. Bu iki sayı koşulsuz kırmızı ve koşulsuz
           yeşildi: her silahlı plan satırı bir "kayıp" ve bir "kazanç" rengi taşıyordu. Oysa
           ikisi de bir SONUÇ değil bir FİYAT SEVİYESİ — plan daha ateşlenmedi bile. Yön hue'su
           K/Z işaretine aittir; bir eşiğe değil. Ayrım artık sütun başlıklarında ve etiketlerde
           (STOP / HEDEF) — zaten oradaydı, renk ikinci kez ve yanlış söylüyordu. -->
      <span class="mono-num">stop ${trn(p.stop, 2)}</span>
      <span class="mono-num">hedef ${trn(p.profit_target, 2)}</span>
      <span class="mono-num">${p.size_r ?? "—"}R</span>
      <span style="text-align:right">${mirror}</span></div>`;
  }).join("");
  return `<div class="card rise"><h2 class="t">Sıradaki seans · ${armed.length} emir ateşlenecek</h2>
    <div class="trow head" style="grid-template-columns:64px 1fr 90px 90px 90px 92px">
      <span>HİSSE</span><span>PLAN</span><span>STOP</span><span>HEDEF</span><span>${T("BOYUT","boyut")}</span><span style="text-align:right">AYNA</span></div>
    ${rows}</div>`;
}

// ---- OLAY AKIŞI — ajanın denetim izi, insan dilinde. Bilinen olaylar TR cümleye çevrilir;
// bilinmeyenler mono ham adıyla DÜRÜSTÇE gösterilir (gizlenmez). Seviye rengi durumu kodlar.
const EV_TR = {
  daily_cycle: e => `Günlük döngü işledi — ${e.date || ""} · ${e.candidates ?? 0} aday, ${e.armed ?? 0} silahlı`,
  alpaca_submit: e => `Alpaca'ya emir: ${e.ticker || "?"} — ${e.ok ? "kabul" : "RET"}${e.detail ? " · " + e.detail : ""}`,
  alpaca_orders_sent: e => `${e.n} emir Alpaca'ya gönderildi`,
  reconcile_strip_armed: e => `Ölü emir ayıklandı: ${e.ticker || "?"} (${e.status || ""})`,
  outcome_evaluated: e => `Sonuç değerlendirildi — v${e.version}, Δ ${e.delta}`,
  hermes_search_start: e => `Hermes arama başladı (${e.regime || "global"}, bütçe ${e.budget})`,
  hermes_search_done: e => `Hermes arama bitti — ${e.evaluated ?? 0} aday, ${e.cleared ?? 0} kapıyı geçti`,
  hermes_proposal: e => `Hermes önerdi: ${e.variable || ""}`,
  hermes_result: e => `Hermes sonuç: ${e.status || ""}`,
  corporate_action_cache_reset: e => `Split/temettü tespit — ${e.ticker} önbelleği tazelendi`,
  duplicate_trade_suppressed: e => `Mükerrer işlem satırı engellendi: ${e.ticker || ""}`,
  warmup_coverage_short: e => `Isınma verisi kısa: ${e.ticker} (${e.first_bar || ""}'den başlıyor)`,
  scheduler_started: () => `Zamanlayıcı başladı`,
  // ---- ONAY KAPISI + KORUMA AİLESİ (v219) ----------------------------------------------------
  // PANONUN EN YÜKSEK BAHİSLİ DOKUZ OLAYI ham adla akıyordu: `approval_missing_refused` bir
  // operatör reddidir, `koruma_oco_dusuru` çıplak kalmış bir pozisyondur — ikisi de akışta
  // `koruma_oco_dusuru` diye, İngilizce-benzeri bir mono jeton olarak geçiyordu.
  // ADLAR VE ALANLAR UÇTAN ÖLÇÜLDÜ, VARSAYILMADI: `api.py` ve `watchdog.py` içindeki
  // `obs.log(...)`/`obs.warn(...)` çağrılarının BİREBİR anahtarları (kimlik/yol/seviye/neden ·
  // ticker/adet/stop/hedef/hata · gonderilen/toplam · verilen/olculen · error). Alan yoksa
  // UYDURULMAZ: cümle o parçayı hiç yazmaz ya da "?" basar.
  approval_gate_passed: e => `Onay kapısı GEÇTİ — [${e.kimlik || "?"}] için defterde onay var`
    + ` (L${e.seviye ?? "?"} · ${e.yol || "yol yazılmamış"})`,
  approval_missing_refused: e => `ONAY KAPISI REDDETTİ — ${e.neden
    || `[${e.kimlik || "?"}] için defterde 'approve' satırı yok (karar: ${e.karar || "yok"})`}`,
  // `davranissal` v240'ta eklendi: aynı defterde artık İKİ sınıf satır var — bir uygulama kapısını
  // bağlayan karar (`rev:`/`rec:`) ve hiçbir şeyi bağlamayan KARAR KAYDI (`kayit:`). Olay akışında
  // ikisi aynı cümleyle akarsa, kayıt-önerisine verilen bir "Kabul" sonradan "uygulandı" diye
  // okunur — bu turun kapattığı yanlış-güven sınıfının ta kendisi.
  approval_decision: e => `Onay defterine karar yazıldı: ${e.approval_id || "?"} → ${e.decision || "?"}`
    + (e.davranissal === false ? " (kayıt-önerisi — davranış değişmez)" : "")
    + ` · ${e.has_reason ? "gerekçeli" : "gerekçesiz"}`,
  // v238 (2026-08-13): reddedilen beceri eylemi. Ekran mesajı ANLIKTIR (kutu bir sonraki çizimde
  // silinir) ve operatör o an başka bir sekmede olabilir — "bastım, hiçbir şey olmadı" vakası
  // SONRADAN da kurulabilmeli. Alanlar `api.api_skills_apply`ın obs.warn'undan BİREBİR: skill ·
  // action · kod · detail. Ölçülmeyen alan UYDURULMAZ.
  skill_action_refused: e => `Beceri eylemi REDDEDİLDİ — ${e.skill || "?"} → ${e.action || "?"}`
    + ` (${e.kod || "kod yazılmamış"})${e.detail ? " · " + e.detail : ""}`,
  koruma_kur_istegi: e => `Koruma kurma isteği — ${e.onay_verildi ? "ONAYLI" : "onaysız (kuru koşu)"}`
    + ` · sonuç ${e.sonuc || "?"} · ${e.gonderilen ?? "?"}/${e.toplam ?? "?"} gönderildi`,
  koruma_oco_gonderildi: e => `Koruma OCO gönderildi: ${e.ticker || "?"} ${e.adet ?? "?"} adet`
    + ` · stop ${e.stop ?? "—"} / hedef ${e.hedef ?? "—"} (adet kaynağı: ${e.adet_kaynagi || "?"})`,
  koruma_oco_dusuru: e => `Koruma OCO'su GİTMEDİ: ${e.ticker || "?"} — pozisyon HÂLÂ çıplak`
    + `${e.hata ? " · " + e.hata : ""}`,
  koruma_kur_ozet: e => `Koruma turu bitti — ${e.gonderilen ?? "?"}/${e.toplam ?? "?"} OCO gönderildi`,
  koruma_onay_bayat: e => `Koruma onayı BAYAT — onay ölçülenden BAŞKA bir listeye verilmiş`
    + ` (ölçülen ${e.olculen || "?"}); hiçbir emir gönderilmedi`,
  koruma_dedektoru_dustu: e => `Koruma dedektörü düştü: ${e.error || "sebep yazılmamış"}`
    + ` — bu poll'da hüküm YOK ("koruma var" sayılmaz)`,
  // ---- SÜPÜRÜCÜ AİLESİ (v220/v221 · KALEM 10) --------------------------------------------------
  // Dolmamış giriş süpürücüsünün olayları ham adla akıyordu; v220 `siniflar`/`foreign` dökümünü,
  // v221 grup kemerini EKLEDİ ama olay çekmecesinde OKUYUCUSU yoktu (YASA-6). Adlar UÇTAN ölçüldü:
  // `alpaca.EV_SUPURME_SINIFLARI` (adapters/alpaca.py) · `api.control_cancel_open` (api.py) ·
  // `loop.EV_STALE_ENTRIES_CANCELLED`/`EV_MIRROR_ENTRIES_CANCELLED` (loop.py). RENK YOK: bunlar
  // obs.log BİLGİ olayı (koruma DOKUNULMADIĞINI raporlar), anomali değil — akışta `mut` çizilir.
  // Ölçülemeyen sayı UYDURULMAZ (?? 0 / ?? "?"), iç virgül dolu diye çeviri düz metindir.
  mirror_cancel_sinif_dokumu: e => `Süpürücü sınıf dökümü — ${e.cancelled ?? 0} giriş iptal edildi`
    + ` · sınıflar: giriş ${e.giris ?? 0} · koruma ${e.koruma ?? 0} (dokunulmadı) · yabancı ${e.yabanci ?? 0}`
    + ((e.korunan_coidler || []).length ? " · korunan bacak: " + (e.korunan_coidler || []).length : ""),
  control_cancel_open: e => `Cancel-Open (pano tuşu) — ${e.cancelled ?? 0} giriş iptal · ${e.kept ?? 0} korundu`
    + `${e.ok === false ? " · İŞLEM DÜŞTÜ" : ""}`,
  mirror_stale_entries_cancelled: e => `Bayat tetik süpürüldü (günlük kadans) — ${e.cancelled ?? 0} giriş iptal`
    + ` · ${e.kept ?? 0} korundu · ${e.foreign ?? 0} yabancı (dokunulmadı)`,
  mirror_entries_cancelled: e => `HALT/breaker süpürücüsü — ${e.cancelled ?? 0} ayna girişi iptal`
    + ` · ${e.kept ?? 0} korundu · ${e.foreign ?? 0} yabancı`,
};
// Akışın NE KADARDIR kopuk olduğu — "kopuk" ile "43 dakikadır kopuk" operatör için aynı şey değil:
// ilki bir bayrak, ikincisi bir karar (bekle mi, ayna kapansın mı).
//
// İKİ ALAN BİRBİRİNİN YERİNE GEÇMEZ, o yüzden ETİKETLERİ de aynı değil: `stream_down_since` kopuşun
// BAŞLANGICIDIR ("43 dk"dır kopuk); `stream_last_event_ts` yalnız son hayat belirtisidir ("son olay
// 3 gün önce") — kopuşun ne zaman başladığını SÖYLEMEZ. v68 öncesi yazılmış dosyada (canlıda tam bu
// durum) yalnız ikincisi vardır; onu "şu kadardır kopuk" diye yazmak ölçmediğimiz bir şeyi ölçmüş
// gibi göstermek olurdu. Hiçbiri yoksa boş döner — uydurma süre yazmak yalanların en kolayıdır.
function wsDownFor(x) {
  const o = x || {};
  if (o.stream_down_since) return sureTR(agoSec(o.stream_down_since));
  const son = sureTR(agoSec(o.stream_last_event_ts));
  return son ? `son olay ${son} önce` : "";
}
function agoSec(ts) {
  const ms = Date.parse(ts || "");
  return Number.isFinite(ms) ? Math.max(0, (Date.now() - ms) / 1000) : null;
}
function sureTR(s) {
  if (s == null) return "";
  if (s < 5400) return `${Math.max(1, Math.round(s / 60))} dk`;
  if (s < 172800) return `${Math.round(s / 3600)} sa`;
  return `${Math.round(s / 86400)} gün`;
}
function relTime(ts) {
  const s = Math.max(0, (Date.now() - Date.parse(ts)) / 1000);
  if (!Number.isFinite(s)) return "";
  if (s < 90) return "az önce";
  if (s < 3600) return `${Math.round(s / 60)} dk önce`;
  if (s < 86400) return `${Math.round(s / 3600)} sa önce`;
  return `${Math.round(s / 86400)} gün önce`;
}
// MUTLAK DAMGA — "30 Tem 14:55". `relTime` bir SÜRE söyler ve süre, ekranda duran bir cümlenin
// ne zaman ÖLÇÜLDÜĞÜNÜ söylemez: sayfa yenilenmeden duran bir "az önce" saatlerce yaşayabilir.
// Bir DURUM satırının damgası mutlak olmalı (HERMES-DAYANIKLILIK dersi (b), 2026-08-02: altı gün
// önceki bir OSError'un sonucu taze bir hüküm gibi okundu). Ayrıştırılamayan damga UYDURULMAZ —
// çağıran "damga yok" dürüstlüğünü basar.
function mutlakTs(ts) {
  if (!ts) return null;
  const d = new Date(ts);
  if (isNaN(d)) return null;
  return d.toLocaleString("tr-TR", { day: "numeric", month: "short",
                                     hour: "2-digit", minute: "2-digit" });
}
function eventsFeed(events) {
  const rows = (events || []).slice(0, 12).map(e => {
    const lvl = e.level === "alarm" ? "neg" : (e.level === "warn" ? "warn" : "mut");
    const mark = e.level === "alarm" ? "▲" : (e.level === "warn" ? "△" : "·");
    const name = String(e.event || "");
    const txt = e.level === "alarm" ? (e.message || name)
      : (EV_TR[name] ? EV_TR[name](e) : `<span class="chain">${esc(name)}</span>`);
    // Satır artık bir kontrol: çevirisi olan olay tek cümleye sığar ama olayın HAM alanları
    // (hangi hisse, hangi hata, hangi sayı) hiçbir yerde okunmuyordu — çekmecede tam kayıt var.
    // ETİKET DÜZ METİN OLMAK ZORUNDA: `txt` çevirisi olmayan olayda BİÇİMLENMİŞ HTML'dir
    // (<span class="chain">…</span>) ve aria-label'a olduğu gibi girerse okuyucu etiketi
    // işaretleme diliyle birlikte okur. Etikete her zaman ham ad/mesaj gider.
    const plain = e.level === "alarm" ? (e.message || name) : (EV_TR[name] ? EV_TR[name](e) : name);
    const k = rec("event", e);
    return `<button ${rowAttrs(k, `${relTime(e.ts)} · ${plain}. Kaydı aç.`)} class="evrow rowbtn">` +
           `<span class="${lvl}" aria-hidden="true">${mark}</span>` +
           `<span class="etxt ${e.level === "alarm" ? "neg" : ""}">${typeof txt === "string" && EV_TR[name] ? esc(txt) : txt}</span>` +
           `<span class="etime">${relTime(e.ts)}</span></button>`;
  }).join("");
  return rows || `<div class="empty">Henüz olay yok — ilk döngüyle dolmaya başlar.</div>`;
}

// ---- ALARM GELEN KUTUSU (2026-07-26) --------------------------------------------------------
// `notify.inbox()` docstring'i "panonun tükettiği görünüm" diyordu ama panoda TÜKETİCİSİ YOKTU:
// uzak kanal (Telegram/webhook) yapılandırılmamışken her alarm yalnız bir sayaca yazılıyor,
// İÇERİĞİ hiçbir yerde görünmüyordu. Kaynak yine `events.jsonl` — burada ikinci bir defter yok,
// yalnız "nereye kadar okudum" sınırı var. ACK hiçbir alarmı SİLMEZ.
function alertsInbox(a) {
  a = a || {};
  const groups = a.groups || [];
  const trunc = a.window_truncated === true
    ? `<p class="hint warn">Pencere KESTİ: son ${a.window_lines || "?"} olay okundu ve en eskisi
       (${esc((a.window_oldest_ts || "").slice(0, 16))}) okundu-sınırından daha yeni — sınırla o
       satır arasındaki alarmlar bu listeye HİÇ girmedi.</p>` : "";
  const btn = `<button class="dlbtn" data-act="ackAlerts" ${groups.length ? "" : "disabled"}
      style="margin-top:10px">Tümünü okundu işaretle</button>
    <span id="alerts-ack-msg" class="hint" style="margin-left:8px"></span>`;
  const kanal = a.channel_configured
    ? `<span class="pos">uzak kanal bağlı</span>`
    : `<span class="warn">uzak kanal YOK — alarmlar yalnız burada birikiyor</span>`;
  const head = `<p class="hint" style="margin-top:0">${a.pending || 0} okunmamış alarm · ${kanal}${
    a.ack_ts ? ` · son okundu ${esc(String(a.ack_ts).slice(0, 16))}` : " · hiç okunmadı"}</p>`;
  if (!groups.length)
    return head + trunc + `<div class="empty">Okunmamış alarm yok — dürüst boşluk.</div>` + btn;
  // ALARM SATIRI ARTIK BİR DENETİMDİR (2026-07-27). Eskiden `<div>` idi ve hemen yanındaki
  // olay akışı `<button class="evrow rowbtn">` üretiyordu: aynı görünüm, zıt davranış, aynı
  // sayfada. Tıkla-çekmece deseninin sisteme yayıldığı yerde sessizce başarısız olan tek nokta
  // buydu — üstelik operatörün en tedirgin olduğu yerde.
  // RUNBOOK BAĞI SATIRIN İÇİNE GİREMEZ, YANINA GİRER (UIUX S1-T3): satırın kendisi bir
  // <button>'dır (kaydı açar, j/k gezinmesine `data-rk` ile bağlıdır) ve bir <a> butonun
  // içerik modeline GİRMEZ — iç içe etkileşimli öğe, hem geçersiz HTML hem de "hangisine
  // bastım" belirsizliğidir. Bu yüzden satır bir sarmalayıcıya alınır: sol tarafta kayıt
  // butonu (eskisiyle birebir aynı), sağda ayrı bir teşhis bağı. İki niyet, iki hedef.
  // SARMALAYICI BİR CSS KURALINI DA DEVRE DIŞI BIRAKIR: `.evrow:last-child{border-bottom:none}`
  // artık eşleşemez (buton sarmalayıcının son çocuğu değil, bağ ondan sonra geliyor). Yani
  // listenin ALTINA fazladan bir kıl çizgi düşerdi. index.html'in <style>'ı bu turda başka bir
  // hattın alanı olduğu için kural orada değil BURADA telafi edilir — son satır kendi
  // kenarlığını kapatır. Görsel sonuç önceki hâlle birebir aynı.
  const rows = groups.map((g, i) => {
    const k = rec("alert", g);
    const son = i === groups.length - 1;
    return `<div class="alarm-satir" style="display:grid;grid-template-columns:minmax(0,1fr) auto;` +
      `gap:var(--s3, 10px);align-items:center">` +
      `<button ${rowAttrs(k, `${g.token}${g.n > 1 ? ` ×${g.n}` : ""} · ${g.message || ""}. Kaydı aç.`)} class="evrow rowbtn"${
        son ? ' style="border-bottom:none"' : ""}>
      <span class="sev-1" aria-hidden="true">▲</span>
      <span class="etxt"><span class="tag t-no">${esc(g.token)}</span>
        ${g.n > 1 ? `<b>×${g.n}</b>` : ""} <span class="sev-1">${esc(g.message || "")}</span></span>
      <span class="etime">${relTime(g.last_ts)}</span></button>` +
      olayBagi(g.token) + `</div>`;
  }).join("");
  return head + trunc + rows + btn;
}
window.ackAlerts = async () => {
  const msg = $("alerts-ack-msg");
  try {
    const r = await apiFetch("/api/alerts/ack", { method: "POST" }).then(x => x.json());
    // YENİDEN ÇEK: yanıttaki `inbox` zaten tazedir ama tek doğruluk kaynağı uç olsun — panonun
    // gösterdiği ile sunucunun bildiği ayrışırsa "okudum" iddiası kanıtsız kalır.
    const a = await j("/api/alerts");
    const el = $("bp-alerts"); if (el) el.innerHTML = alertsInbox(a);
    const m2 = $("alerts-ack-msg");
    if (m2) m2.innerHTML = `okundu işaretlendi · sınır ${esc(String(r.ack_ts || "").slice(0, 16))}`;
  } catch (e) { if (msg) msg.innerHTML = `<span class="neg">${esc(e.message)}</span>`; }
};

// ---- sermaye mini-eğrisi: bağlam veren tek çizgi (eksen/süs yok; tam grafik Performans'ta)
function sparkline(vals) {
  const W = 150, H = 30, mn = Math.min(...vals), mx = Math.max(...vals), rng = (mx - mn) || 1;
  const pts = vals.map((v, i) => `${(i / (vals.length - 1) * W).toFixed(1)},${(H - 3 - (v - mn) / rng * (H - 6)).toFixed(1)}`).join(" ");
  const up = vals[vals.length - 1] >= vals[0];
  return `<svg viewBox="0 0 ${W} ${H}" style="width:150px;height:30px;display:block" aria-hidden="true">` +
         `<polyline points="${pts}" fill="none" stroke="${up ? "var(--green)" : "var(--red)"}" stroke-width="1.5" opacity=".85"/></svg>`;
}

// reusable bits
const gateLegend = () => `<div class="legend-gate">
  <span class="lg"><span class="tag t-go">GO</span> tüm kurallara uygun — otomatik alınır</span>
  <span class="lg"><span class="tag t-rv">REVIEW</span> uygun ama bir noktası dikkat ister</span>
  <span class="lg"><span class="tag t-no">NO_GO</span> bir kuralı çiğniyor — alınmaz</span></div>`;

function glossaryCard() {
  const items = [
    ["Paper mode", TERMS.paper], ["Otonomi (L0/L1/L2)", TERMS.otonomi], ["Rejim", TERMS.rejim],
    ["Exposure tavanı", TERMS.exposure_tavani], ["Mevcut exposure", TERMS.mevcut_exposure],
    ["Distribution days", TERMS.distribution], ["Kurulum (VCP)", TERMS.kurulum], ["RS", TERMS.rs],
    ["Skor", TERMS.skor], ["R:R (risk:ödül)", TERMS.rr], ["Boyut (R)", TERMS.boyut],
    ["Kapı: GO / REVIEW / NO_GO", TERMS.kapi], ["Sharpe", TERMS.sharpe], ["Max drawdown", TERMS.drawdown],
    ["Track skor", TERMS.skor_track], ["Toplam getiri", TERMS.getiri], ["Hipotez", TERMS.hipotez],
    ["Backtest (OOS)", TERMS.backtest], ["Kalibrasyon", TERMS.kalibrasyon], ["Skill", TERMS.skill],
    ["HALT (acil durdur)", "Basınca yeni hiçbir alım yapılmaz. Mevcut açık pozisyonlar yönetilmeye devam eder. 'DEVAM' ile geri açılır."],
  ];
  return `<details class="gloss rise"><summary>ⓘ Terimler ne demek? — finans bilmeyene sade açıklama</summary>
    <div class="body">${items.map(([t, d]) => `<div class="gterm"><b>${esc(t)}</b><span>${esc(d)}</span></div>`).join('')}</div></details>`;
}

// ================= SABAH BRİFİNGİ — mission control =================
const RENDER = {};

// ==============================================================================================
// S2R-1 · ALAN SAYFASI KABUĞU (2026-08-02)
// ----------------------------------------------------------------------------------------------
// Yedi alan sayfasının HER BİRİ tek bir sorunun evidir. Kabuk üç şey yapar ve başka hiçbir şey:
//   (1) sayfanın başlığını + o sayfanın SORU CÜMLESİNİ yazar (denetim çıpası — ADR "ekrana dök"
//       yasağının uygulaması: yeni bir kart eklerken "bu, bu sorunun cevabı mı?" diye sorulacak
//       yer, kartın eklendiği sayfanın kendi başlığıdır),
//   (2) eski görünümlerin render'larını SIRAYLA çağırır (kendi kaplarına yazıyorlar),
//   (3) o kapların içinde kalan h1'leri h2'ye indirir.
// İÇERİK GÖÇÜ BURADA YOK — kart kart taşıma ve emekli listesi S2R-2'nin işi.
// BAŞLIK BİR AD, SORU CÜMLESİ BİR SÖZLEŞMEDİR — ikisi aynı cümle DEĞİL. Panonun mevcut dili
// başlıkta ad kullanıyor ("Piyasa — izlenen evren.", "Teşhis ve müdahale."); başlığı da soruya
// çevirseydik aynı cümleyi 24px'te ve 12px'te iki kez okuturduk ve ikincisi — asıl denetim
// çıpası olan sönük satır — süs gibi görünürdü.
const ALAN_BAS = {
  bugun:    ["① BUGÜN · SABAH TURU", "Dün gece", "ve bugün.", ""],
  karar:    ["② KARAR", "Ne önerildi", "ve ne oldu?",
             "Adaylar, disiplin kapısı, onay kuyruğu, kitap, broker mutabakatı, seans-içi emir ve birikim."],
  saglik:   ["③ SAĞLIK", "Veri", "ve işleyiş.",
             "Alarmlar ve olay yüzeyleri, gece hattının çizelgesi, veri hattı, izlenen evren ve seans-içi akış."],
  ogrenme:  ["④ ÖĞRENME", "Defter", "ve kalibrasyon.",
             "Karne, gölge kollar, bileşen kalibrasyonu, hipotez defteri, beceriler ve dersler."],
  kilitler: ["⑤ KİLİTLER", "Kollar", "ve yapılandırma.",
             "Müdahale kademeleri, bayraklar, anahtarlar ve oturum tercihleri."],
};
function alanBasHTML(id) {
  const [etiket, a, b, alt] = ALAN_BAS[id] || ["", id, "", ""];
  return `<div class="slabel rise"><span class="d"></span>${esc(etiket)}</div>
    <h1 class="ph rise">${esc(a)} <span class="g">${esc(b)}</span></h1>
    ${soruCumlesi(id)}
    ${alt ? `<p class="subline rise">${esc(alt)}</p>` : ""}`;
}
// BÖLÜM BAŞLIKLARI h2'YE İNER. Eski görünümlerin her biri kendi `<h1>`ini basıyor ve bu doğruydu —
// o zaman her biri bir SAYFAYDI. Artık bölümler; sayfada birden fazla h1 bırakmak, ekran
// okuyucuda "bu sayfa neyin sayfası?" sorusunu cevapsız bırakır (WCAG başlık hiyerarşisi).
// Dönüşüm TEK YERDE ve render gövdelerine dokunmadan yapılır: on iki gövdeyi elle düzenlemek
// hem büyük bir fark hem de S2R-2'de zaten silinecek bir iş olurdu.
function _bolumBasliklariniIndir(kok) {
  if (!kok) return;
  kok.querySelectorAll(".alan-bolum h1").forEach(h1 => {
    const h2 = document.createElement("h2");
    h2.className = h1.className;                 // .ph / .greet / .rise aynen taşınır
    if (h1.id) h2.id = h1.id;
    h2.innerHTML = h1.innerHTML;
    h1.replaceWith(h2);
  });
}
// Sayfayı çizen tek kalıp: başlık → kayıt defteri sıfırlaması → bölümler (SIRAYLA) → başlık
// mertebesi düzeltmesi.
// SIRAYLA, paralel DEĞİL: bölümler ortak bir kayıt defterine (`_REC`) yazıyor ve bazıları aynı
// uçtan besleniyor; paralel koşsalardı satır anahtarları iç içe geçer ve çekmece yanlış kaydı
// açardı. Sıra ayrıca bir SÖZLEŞMEdir (ALAN_BOLUMLERI): 'en kritik üstte'.
//
// HATA BÖLÜM BAŞINA YALITILIR ve bu birleşmenin doğrudan sonucudur: eskiden Piyasa ile Intraday
// AYRI sayfalardı, biri düşse diğeri sağlamdı. Aynı sayfaya alındıkları an tek bir istisna
// sayfanın TAMAMINI "Veri yüklenemedi" ekranına çevirirdi — hatayı bir sayfa büyütmek, birleşme
// için ödenmiş sessiz bir bedel olurdu. Yutma YOK (YASA 4): düşen bölüm kendi kabında NE
// olduğunu yazar, yani hangi bölümün düştüğü sayfanın tamamının düşmesinden daha okunaklıdır.
function alanSayfasi(id, bolumler) {
  return async () => {
    const kap = $("page-" + id);
    const bas = kap && kap.querySelector(".alan-bas");
    // DURUM IZGARASI (v191) BAŞLIĞIN ALTINA GİRER — Koşu & Döngü ile Portföy & Emirler'in
    // çakışan "sistem şu an nerede?" cevabı TEK yerde toplanır (gerekçe: `DURUM_SAYFALARI`).
    // KAP İD'SİZ VE SORGUYLA BULUNUR: iki sayfanın da `.alan-bas`ı kendi ızgarasını taşır ve
    // ikisi de DOM'da AYNI ANDA durur (gizli sayfa silinmez). Sabit bir `id` olsaydı `$()`
    // her zaman belge sırasındaki İLKİNİ (kosu) döndürür, Portföy'ün ızgarası hiç dolmazdı.
    if (bas) bas.innerHTML = alanBasHTML(id) + (DURUM_SAYFALARI.has(id)
      ? `<div class="durum-izgara-kap"><p class="durum-dus mut">durum okunuyor…</p></div>` : "");
    // KAYIT DEFTERİ SAYFA BAŞINA BİR KEZ SIFIRLANIR (S2R-2 · SESSİZ KIRILMA AVI).
    // `recReset()` açık çekmeceyi kapatır ve `_REC` haritasını SİLER. S2R-1'de üç render onu
    // kendi gövdesinin başında çağırıyordu (brifing/adaylar/ajan) ve üçü de kendi sayfasının
    // İLK bölümüydü — yani fiilen "sayfa başına bir kez" çalışıyordu. S2R-2'de Öğrenme'nin
    // sırası [karne, golge, bilesenic, hermes, ajan, …] oldu ve `ajan` BEŞİNCİ sıraya düştü:
    // kendi recReset'i, ondan ÖNCE çizilen mutabakat/kapı/olay satırlarının kayıt anahtarlarını
    // silerdi. Sonuç GÖRÜNMEZ bir kırılma olurdu — satırlar ekranda durur, tıklanır, çekmece
    // "kayıt bulunamadı" ile açılırdı. Sıfırlama artık sıradan BAĞIMSIZ: kabuğun kendi işi.
    recReset();
    // IZGARA `recReset`TEN SONRA ÇİZİLİR: kartların çekmece anahtarları (`rec()`) sıfırlamadan
    // ÖNCE yazılsaydı, kabuk onları hemen siler ve dört kart da "kayıt bulunamadı" ile açılırdı.
    if (bas) await durumIzgarasiCiz(bas.querySelector(".durum-izgara-kap"));
    for (const ad of bolumler) {
      if (!RENDER[ad]) continue;
      try {
        await RENDER[ad]();
      } catch (e) {
        const bol = $("page-" + ad);
        if (bol) bol.innerHTML = `<div class="card rise in"><h2 class="t">Bölüm yüklenemedi</h2>` +
          `<p class="mut">${esc(String(e))}</p>` +
          `<p class="mut" style="font-size:12px;margin-top:8px">Sayfanın diğer bölümleri çizildi — bu blok ${
            esc(ad)} verisini okuyamadı.</p></div>`;
        else throw e;      // kabı olmayan bir bölümün hatası GÖRÜNMEZ kalamaz: yukarı çıkar
      }
    }
    _bolumBasliklariniIndir(kap);
    // KART SÖZLEŞMESİ (v198) EN SONDA: bütün bölümler yazıldıktan sonra tek geçişte kapak kurulur.
    // Bölüm bazlı kurmak, sayfanın bütçesini bölüm bölüm saymak olurdu — bütçe SAYFANIN.
    katKurulumu(kap, id);
  };
}
// ---- SATIR-DÜZEYİ YALITIM — yukarıdaki bölüm çerçevesinin KÜÇÜK KARDEŞİ ----------------------
// Bölüm çerçevesi (`alanSayfasi`) hatayı bir SAYFAdan bir BÖLÜMe küçültür. Bu, aynı küçültmeyi bir
// adım daha götürür: bir SATIRIN çizimi patlarsa o satır dürüst bir "ÖLÇÜLEMEDİ" satırına döner ve
// listenin GERİ KALANI çizilir.
//
// NEDEN VAR (2026-08-06 canlı vakası, operatör ekran görüntüsü): müdahale bölümünün TEK satır
// üreticisi çalışma zamanında patladı ve bölüm çerçevesi devreye girdi — yani dört müdahale
// kolunun DÖRDÜ birden ekrandan silindi ve yerlerine tek bir "Bölüm yüklenemedi" kutusu geldi.
// HALT/FLATTEN kollarının bulunduğu bir listede bu, tek bir çizim kusurunun panonun en yüksek
// bahisli düğmelerini görünmez yapması demektir. Bölüm çerçevesi doğru davrandı; eksik olan,
// ondan bir mertebe küçük olan bu kaptı.
//
// UYDURMA YASAĞI KORUNUR: guard hiçbir durumu tahmin ETMEZ ("kapalı"/"serbest" yazmaz). Söylediği
// tek şey ölçemediği ve NEREDE ölçemediğidir — None ≠ 0. YASA 4 (sessiz-yutma yasağı) da yerinde:
// hata yutulmaz, satırın kendi gövdesine yazılır ve konsola da düşer.
// YENİ SINIF AÇILMAZ: satır mevcut `.kol-satir` / `.kol-durum` / `.hint` / `.mut` kurallarını
// kullanır — olmayan bir sınıf yazmak ileride aranacak bir hayalet bırakırdı.
function satirKoru(alan, uret) {
  try {
    const s = uret();
    // BOŞ/DİZGİ-OLMAYAN DÖNÜŞ DE BİR ŞEKİL KUSURUDUR: `innerHTML`e "undefined" yazmak, sessizce
    // bozuk bir satır çizmek olurdu — ekranda durur, hiçbir şey söylemez.
    if (typeof s !== "string" || !s) throw new TypeError("satır üreticisi dizgi döndürmedi");
    return s;
  } catch (e) {
    console.error("satır çizilemedi:", alan, e);
    return `
    <div class="kol-satir">
      <div><b>ÖLÇÜLEMEDİ</b> · veri-şekli beklenmedik (alan: ${esc(alan)})
        <p class="hint" style="margin:2px 0 0">${esc(String((e && e.message) || e))}</p></div>
      <div class="kol-durum"><span class="mut">ölçülemedi</span></div>
    </div>`;
  }
}
// ---- S2R-2 · BÖLÜM → SAYFA EŞLEMESİ (içerik göçünün TEK kaydı) -------------------------------
// SIRA BİR SÖZLEŞMEDİR: liste hem çizim sırasını hem DOM sırasını belirler ve "en kritik üstte"
// kuralının ölçülebilir hâlidir. Her sayfa kendi soru cümlesine hizmet SIRASIYLA okunur.
//
// S2R-1'de bu tablo altı satırdı ve altısı da tek bir eski görünüm taşıyordu; iç sıralama o
// görünümün KENDİ gövdesinde, `await RENDER.x()` çağrılarıyla gizliydi (brifing→performans,
// adaylar→onaylar, ajan→hermes+skiller+hafiza). Gizli sıra ölçülemez ve taşınamaz: bir bölümü
// başka bir sayfaya almak, onu çağıran gövdeyi düzenlemeyi gerektiriyordu. S2R-2'de o zincirler
// SÖKÜLDÜ — her bölüm kendi kabına yazar, sırayı YALNIZ bu tablo söyler.
//
// D2-b'DE İKİ BİRLEŞME OLDU ve sıra ONLARIN ANLATISINDAN türer:
//   kosu + portfoy → karar   : "ne önerildi, neden geçti/geçmedi, ne oldu?" tek zincir.
//   veri + gozetim → saglik  : TASK ③'ün (alarmdan nedene) ölçülen yolu iki sayfaya yayılıyordu.
//
// NEDEN BU SIRA (yüzeyin sorusuna hizmet sırası):
//   karar    : ne önerildi (adaylar) → neden geçti/geçmedi (kapilar) → senden ne isteniyor
//              (onaylar) → ne oldu: kitap (brifing) → emir gerçekten aynaya ulaştı mı (mutabakat)
//              → seans-içi emir kapısı (intraemir) → birikim (en yavaş değişen en altta)
//   saglik   : bir şey bozulduysa ÖNCE o (operasyon: alarm gelen kutusu + olay yüzeyleri) →
//              gece hattı hangi adımda (cizelge) → hattın iç sağlığı (veriboru) → izlenen evren
//              (market) → seans-içi akış (intraday)
//   ogrenme  : karne (hüküm) → gölge kollar → bileşen kalibrasyonu → beyin/sprint → hipotez
//              defteri → araçlar → dersler   (ADR'nin Öğrenme hiyerarşisi birebir)
//   kilitler : kollar önce (acil olan), yapılandırma sonra
// ① Bugün BU TABLODA YOK ve bu bilinçli: bölümü yoktur, tek ekranlık kart kompozisyonudur
// (`GENEL_KARTLARI` kendi bütçesini taşır). Kabuk onu `alanSayfasi` ile çizmez.
const ALAN_BOLUMLERI = {
  karar:    ["adaylar", "kapilar", "onaylar", "brifing", "mutabakat", "intraemir", "performans"],
  saglik:   ["operasyon", "cizelge", "veriboru", "market", "intraday"],
  ogrenme:  ["karne", "golge", "bilesenic", "hermes", "ajan", "skiller", "hafiza"],
  kilitler: ["mudahale", "ayarlar"],
};
for (const [alan, bolumler] of Object.entries(ALAN_BOLUMLERI)) RENDER[alan] = alanSayfasi(alan, bolumler);

// ---- BÖLÜM BAŞLIĞI — tek katman, kart-içinde-kart YOK ----------------------------------------
// S2R-1'de her eski görünüm KENDİ sayfa başlığını basıyordu: `.slabel` + `<h1 class="ph">` +
// `.subline` + soru cümlesi. Yedi bölümlü Öğrenme sayfasında bu, aynı ritmin YEDİ KEZ tekrarı
// demekti — okur her bölümde "yeni bir sayfaya mı girdim?" diye duraklıyordu. Artık tek kalıp:
// h2 + (varsa) tek satır altyazı + soru cümlesi. Üst çizgi `.alan-bolum + .alan-bolum` CSS
// kuralından gelir; bölüm gövdesi kendi çerçevesini ÇİZMEZ.
//
// ÇAPA BAŞLIKTA: `id="<bolum>"` — sessiz-hat ve palet artık `portfoy#mutabakat` gibi bölüm
// çapalarına gidiyor (S2R-1'in beyanlı borcu: iç hedefler eski görünüm adlarına bakıyordu).
function bolumBasHTML(id, baslik, altyazi) {
  return `<div class="bolum-bas rise">
    <h2 class="ph" id="${esc(id)}">${esc(baslik)}</h2>
    ${altyazi ? `<p class="subline">${altyazi}</p>` : ""}
    ${soruCumlesi(id)}</div>`;
}
// ---- DETAY KATMANI (YASA-6 indirimi) ---------------------------------------------------------
// "Soruya hizmet etmeyen" bir bölüm SİLİNMEZ — çünkü çoğu zaman okuduğu API alanının TEK
// okuyucusudur ve silmek o alanı öksüz bırakır (codelaw'ın göremediği HTTP→DOM katmanında).
// Mertebesi düşer: varsayılan-KAPALI `<details>`. Gerekçe `neden` ile satırın kendisinde durur,
// ADR Ek'inde de yazılıdır — "neden burada değil" sorusu ekrandan cevaplanabilmeli.
function detayKatmani(baslik, neden, govde) {
  return `<details class="detay-kat rise">
    <summary>${esc(baslik)} <span class="dk-not">— detay katmanı</span></summary>
    <div class="dk-govde"><p class="hint dk-neden">${esc(neden)}</p>${govde}</div></details>`;
}
// Açık sayfayı yeniden çiz. Müdahale kolları ve ret-kapatma eskiden `RENDER.operasyon()`
// çağırıyordu; o render S2R-2'de altı parçaya bölündü ve hangi parçanın ekranda olduğu artık
// SAYFAYA bağlı. Sabit bir render adına çağrı yapmak, operatörün baktığı sayfayı tazelemeden
// başka bir sayfayı tazelemek olurdu — sessiz ve teşhisi zor.
async function _aktifSayfayiCiz() {
  const el = document.querySelector(".page.active");
  const id = el ? el.id.replace(/^page-/, "") : VARSAYILAN_ROTA;
  if (RENDER[id]) { await RENDER[id](); revealActive(true); }
}

// ==============================================================================================
// GENEL BAKIŞ v1 — J1'in 60 saniyelik sabah turu (ADR: TEK EKRAN, KAYDIRMASIZ · 1440×900)
// ----------------------------------------------------------------------------------------------
// KOMPOZİSYON SÖZLEŞMESİ BURADA, ŞABLONDA DEĞİL. Kart sayısı bir tasarım bütçesidir: altıncıdan
// sonrası "tek ekran" iddiasını sessizce yer. Piksel-kesin bir kaydırma testi yazılamaz (yazı
// tipi, tarayıcı, zum) — ama KART SAYISI ve SÜTUN DÜZENİ yazılabilir, ve tek ekranı fiilen
// bozacak olan da bu ikisidir. Bu yüzden liste veri, şablon değil: test onu sayabiliyor.
//
// HER KART TEK BAĞ TAŞIR ve bağ ÜÇÜNCÜ ALANDIR. "Detay kart içinde YOK" kuralının uygulaması
// budur: bir kart bir sayıyı gösterir, o sayının yaşadığı alan sayfasına gönderir, biter.
// HEDEF `sayfa` YA DA `sayfa#bolum` OLABİLİR (v195-a): panonun her yerinde kullanılan adresleme
// dilinin aynısı (`spineHTML`, `RECORD_VIEW`, ⌘K paleti). Kart hâlâ TEK bağ taşır — değişen şey
// bağın nereye indiği: "Bugün ne var" kartı bekleyen ONAYI sayıyor, dolayısıyla bağı da onay
// yüzeyine (Portföy & Emirler → onay kuyruğu) inmeli; sayfanın başına bırakıp "şimdi ara" demek
// kartın kendi cümlesini yarıda keserdi.
const GENEL_KARTLARI = [
  // [anahtar,   başlık,               hedef yüzey (opsiyonel #bölüm çapası)]
  ["gece",     "Dün gece",             "karar#adaylar"],
  ["sermaye",  "Sermaye · köken",      "karar#brifing"],
  ["bugun",    "Bugün ne var",         "karar#onaylar"],
  ["equity",   "Sermaye eğrisi",       "karar#performans"],
  ["karne",    "Karne",                "ogrenme"],
  ["kapsama",  "Kapsama",              "saglik#market"],
];
// `sayfa` çapadan AYRI tutulur: bağın ETİKETİ yüzeyin adıdır ("→ Karar"), çapa değil.
// `ALAN_ADI["karar#onaylar"]` undefined olsaydı düğme ham adresi yazardı.
//
// ÇAPA DA ETİKETE GİRER (D2-b): beş yüzeye inince altı kartın DÖRDÜ aynı yüzeye bakar oldu ve
// dördü de "→ Karar" yazsaydı bağ ayırt edici olmaktan çıkardı — okur hangi kartın nereye
// indiğini ancak basarak öğrenirdi. Çapa ADRESTEN türer; ikinci bir bölüm-adı listesi AÇILMAZ
// (palette.js'in `BOLUMLER` tablosuyla ayrışırdı — v160'ın çivilediği sınıf).
const _GB = Object.fromEntries(GENEL_KARTLARI.map(([k, ad, hedef]) =>
  [k, { ad, hedef, sayfa: String(hedef).split("#")[0], capa: String(hedef).split("#")[1] || "" }]));
// TEK ÇIKIŞ: `gb-kart` sınıfı ve `gb-bag` düğmesi YALNIZ burada üretilir. İkinci bir yerde
// üretilseydi "kart başına tek bağ" kuralı sayılamaz bir vaat olurdu.
function gbKart(anahtar, govde) {
  const k = _GB[anahtar];
  if (!k) return "";                       // kayıtsız anahtar sessizce düşer, uydurma kart doğmaz
  return `<section class="gb-kart rise" data-kart="${anahtar}">
    <h2 class="t">${esc(k.ad)}</h2>
    <div class="gb-govde">${govde}</div>
    <button class="gb-bag" type="button" data-act="go" data-a1="${k.hedef}">→ ${
      esc(ALAN_ADI[k.sayfa] || k.sayfa)}${k.capa ? ` <span class="tx3">· ${esc(k.capa)}</span>` : ""}</button>
  </section>`;
}
// "—" ile "0" ASLA KARIŞMAZ (dürüstlük arayüzü): ölçülmemiş alan tire basar, nedeni yanında.
const _gbSay = (v, birim) => v == null ? `<span class="gb-say mut">—</span>`
  : `<span class="gb-say">${trn(v)}</span>${birim ? `<span class="gb-alt" style="display:inline;margin-left:6px">${esc(birim)}</span>` : ""}`;

RENDER.bugun = async () => {
  recReset();
  // TEK UÇ BEKLENİR, GERİSİ ARKADAN GELİR (v243'te üçten bire indi — aşağıdaki blok).
  // Beklenen, sayfanın CÜMLESİNİ kuran uçtur (durum + döngü + plan); arkadan gelenler teşhis ve
  // eğilim kartları. `/api/market` 260 CSV okur ve onu ilk boyamaya zincirlemek, panonun açılış
  // sayfasını en pahalı ucuna bağlamak olurdu — aynı yasa artık `/api/diagnostics` için de geçerli.
  // `/api/events` ARTIK ÇEKİLMİYOR (v190): tek okuyucusu aşağıdaki "Dün gece" kartıydı ve o kart
  // uçtan gelen SON DÖNGÜ ÖZETİNİ okuyor. Olay penceresi bir defterdir, bir ölçüm kaynağı değil.
  // TEK UÇ BEKLENİR (v243, 2026-08-13) — ÖLÇÜLMÜŞ ÜRETİM ARIZASININ DÜZELTMESİ.
  // Bu satır `Promise.all([/api/today, /api/diagnostics])` idi ve `bugun` VARSAYILAN rotadır:
  // yani panonun ilk boyaması, uçların EN PAHALISINA zincirliydi. 2026-08-13 tohum yenilemesi
  // `trades.jsonl`ı 97→887 satıra çıkarınca `/api/diagnostics` 20-90 sn'ye tırmandı ve operatör
  // "pano yüklenmiyor" dedi — oysa `/api/today` 0,18 sn, `/api/approvals` 0,05 sn, `/api/summary`
  // 0,49 sn ile AYAKTAYDI. Ekranı tutan tek şey bu `await`di.
  // Neden PREFETCH'ten çıkarmak YETMEZDİ: ön-yükleme zaten boşta ve ATEŞLE-UNUT (warmViews);
  // sayfayı bekleten o değil, BURASIYDI. Uç PREFETCH'te KALIR — soğuk süreçte maliyeti boşta
  // ödemek, operatör Operasyon'a tıkladığında ödemekten iyidir.
  // Kart KAYBOLMAZ: teşhisin beslediği üç yüzey (sessiz hat şeridi, alarm bütçesi satırı, ret
  // sayısı) aşağıda YERİNDE doldurulur — sayfanın kendi "iskelet konur, ölçüm arkadan gelir"
  // deseni (eğri/karne/kapsama kartları) ve `refreshStatus`un ATEŞLE-UNUT beyanı ile aynı yasa.
  const t = await j("/api/today");

  // ---- 1) DÜN GECE — son günlük döngünün KENDİ kaydından (`/api/today.son_dongu`).
  //         ESKİ KUSUR (operatör bulgusu): kart, olay akışının son 80 kaydında `daily_cycle`
  //         arıyordu. Olay günde BİR yazılır; gün içindeki poll/uyarı satırları onu pencereden
  //         taşırınca kart "ölçülemedi" diyordu — oysa döngü koşmuştu. Ölçüm değil PENCERE
  //         bozuktu. Kayıt yoksa hâlâ uydurma yok: sunucunun yazdığı NEDEN basılır.
  const sonDongu = t.son_dongu || null;
  const geceGovde = (sonDongu && sonDongu.var)
    ? `<span class="gb-say">${esc(String(sonDongu.date || "—"))}</span>
       <p class="gb-alt"><b>${sonDongu.candidates ?? "—"}</b> aday · <b>${sonDongu.plans ?? "—"}</b> plan ·
         <b>${sonDongu.armed ?? "—"}</b> silahlı${sonDongu.regime ? ` · ${esc(REGIME_TR[sonDongu.regime] || sonDongu.regime)}` : ""}</p>
       <p class="gb-alt">${sonDongu.yas_saat == null ? "yaş ölçülemedi (döngü kaydında zaman damgası yok)"
           : `${trn(sonDongu.yas_saat, 1)} saat önce`}${sonDongu.data_ok === false ? ' · <span class="warn">veri kapısı kapalıydı</span>' : ""}</p>`
    : `<span class="gb-say mut">—</span>
       <p class="gb-alt">${esc((sonDongu && sonDongu.neden) || "günlük döngü özeti uçtan gelmedi — ölçülemedi.")}</p>`;

  // ---- 2) SERMAYENİN KÖKENİ — mevcut `sermayeKokenSatiri` yeniden kullanılır (ÖZET biçim).
  //         İkinci bir metin kurulsaydı biri güncellenip diğeri bayatlardı.
  const sermayeGovde = `<span class="gb-say ${SERMAYE_RENK[(t.sermaye_koken || {}).renk] || ""}">${money(t.equity)}</span>
    <p class="gb-alt">${sermayeIbaresi(t.sermaye_koken) || "—"}</p>
    ${sermayeKokenSatiri(t.sermaye_koken, { kisa: true })}`;

  // ---- 3) BUGÜN NE VAR — silahlı emir + senden iş isteyen bekleyen onay. İki sayı, iki ad:
  //         silahlı plan açılışta ateşlenir (sen bir şey yapmazsın), bekleyen onay SENİ bekler.
  //
  //         REDDEDİLEN EMİR DE BURAYA GİRER, ve bu bilinçli bir telafidir: eski açılış sayfası
  //         (Bugün) triyaj şeridini taşıyordu ve şerit "3 emir reddedildi" diyen TEK yüzeydi —
  //         sessiz hat o sinyali TAŞIMIYOR (bekçi/kilit/tazelik üçlüsü). Açılış sayfası Genel
  //         Bakış olunca o cümle ilk ekrandan düşerdi. Şerit ADR gereği buraya alınmadı
  //         ("BAŞKA HİÇBİR ŞEY"), ama sayı bu kartın KENDİ sorusuna aittir: bugün ne var?
  //         SAYI METİNDİR, İKİNCİ BİR BAĞ DEĞİL — kart başına tek bağ kuralı bozulmaz; retlerin
  //         evi Gözetim'dir ve oraya alarm bütçesi satırı zaten bağlıyor.
  const silahliN = (t.armed_plans || []).length;
  const onayN = t.inbox_count == null ? null : (Number(t.inbox_count) || 0);
  //         REVIEW KIRILIMI AYNI DAMGADAN OKUNUR (v195-a · B2/Ö4): `inbox_count` artık onay
  //         bekleyen REVIEW planlarını da içeriyor (api._inbox_count) ve buradaki kırılım aynı
  //         `onay_bekliyor` bayrağını sayar — pano İKİNCİ bir ölçüt kurmaz, yoksa kart ile rozet
  //         aynı gün ayrışırdı. Liste HİÇ gelmediyse sayı UYDURULMAZ: "0 REVIEW" ile "plan defteri
  //         uçtan gelmedi" aynı cümle değildir.
  const planlar = Array.isArray(t.todays_plans) ? t.todays_plans : null;
  const reviewN = planlar ? planlar.filter(p => p && p.onay_bekliyor).length : null;
  // RET SAYISI ARKADAN GELİR: kaynağı `/api/diagnostics.reconcile` ve o uç artık beklenmiyor.
  // Yuva BOŞ doğar — "0 ret" YAZMAZ: ölçülmemiş bir sayıyı sıfır göstermek uydurma olurdu.
  const bugunGovde = `${_gbSay(silahliN, "silahlı emir")}
    <p class="gb-alt">${onayN == null
      ? "bekleyen onay <b>ölçülmedi</b> — gelen kutusu alanı uçtan gelmedi"
      : `<b>${onayN}</b> bekleyen onay${onayN ? "" : " — senden bir şey beklenmiyor"}${
          reviewN == null
            ? ' · <span class="mut">REVIEW ölçülemedi — plan defteri uçtan gelmedi</span>'
            : (reviewN ? ` · <b>${reviewN}</b> plan onayını bekliyor` : "")}`}</p>
    <p class="gb-alt">${silahliN ? "açılışta ateşlenecek" : "açılışta yeni tarama yapılır"}<span id="gb-ret"></span></p>`;

  // ---- 4-6) ÜÇ MİNİ-TREND — iskelet konur, ölçüm arkadan gelir. "ölçülüyor…" bir sayı DEĞİL:
  //           dolmayan bir kart tire ile kalır ve nedenini söyler.
  const bekle = `<span class="gb-say mut">—</span><p class="gb-alt">ölçülüyor…</p>`;

  // SESSİZ HAT BURADA ÇİZİLMEZ: `<main>`in ilk çocuğu ve her sayfada aynı yerde duruyor
  // (yukarıda `sessizHatGlobal` besledi). ADR'nin "BAŞKA HİÇBİR ŞEY" kuralı gereği triyaj şeridi
  // de bu sayfada YOK — onun sorusu ("senden bir şey bekliyor mu?") burada "Bugün ne var"
  // kartının işidir ve iki yerden aynı şeyi söylemek, ikisini de zayıflatırdı.
  $("page-bugun").innerHTML = `
    <div class="alan-bas">${alanBasHTML("bugun")}</div>
    ${gbAlarmSatiri(null, true)}
    <div class="gb-ust">
      ${gbKart("gece", geceGovde)}
      ${gbKart("sermaye", sermayeGovde)}
      ${gbKart("bugun", bugunGovde)}
    </div>
    <div class="gb-trend">
      ${gbKart("equity", `<div id="gb-eq">${bekle}</div>`)}
      ${gbKart("karne", `<div id="gb-karne">${bekle}</div>`)}
      ${gbKart("kapsama", `<div id="gb-kapsama">${bekle}</div>`)}
    </div>`;
  buildSidebar(t);

  // --- arkadan gelen ölçümler ---------------------------------------------------------------
  // TEŞHİS UCU — sayfa ÇİZİLDİKTEN sonra. Üç yüzeyi yerinde doldurur; hiçbiri ilk boyamayı
  // bekletmez. Uç düşerse üçü de "ölçülemedi" der (uydurma yok, sessizlik de yok).
  j("/api/diagnostics").then(d => {
    if (d) _DIAG = d;
    sessizHatGlobal(d && d.sessiz_hat);
    const al = $("gb-alarm");
    if (al) al.outerHTML = gbAlarmSatiri((d || {}).alarm_butcesi);
    const ret = $("gb-ret"), acik = (((d || {}).reconcile || {}).failed_submissions || {}).open;
    if (ret && (acik || []).length) ret.innerHTML = ` · <span class="neg">${acik.length} emir reddedildi</span>`;
  }).catch(() => {
    const al = $("gb-alarm");
    if (al) al.outerHTML = gbAlarmSatiri(null);   // "ölçülmedi — teşhis ucu bu alanı vermedi"
    const ret = $("gb-ret");
    if (ret) ret.innerHTML = ` · <span class="mut">ret sayısı ölçülemedi — teşhis ucu okunamadı</span>`;
  });
  // Eğri + karne AYNI uçtan gelir (`/api/performance`): iki ayrı istek atmak, aynı dosyayı iki kez
  // okutmak olurdu.
  j("/api/performance").then(p => {
    const pts = ((p.equity_curve || {}).points || []).slice(-40);
    const eq = $("gb-eq");
    if (eq) eq.innerHTML = pts.length > 2
      ? `${sparkline(pts.map(q => +q[1]))}
         <p class="gb-alt">son <b>${pts.length}</b> kapanış · en düşük ${money(Math.min(...pts.map(q => +q[1])))}</p>`
      : `<span class="gb-say mut">—</span><p class="gb-alt">eğri için yeterli kapanmış işlem yok
           (${pts.length} nokta) — çizmek uydurma olurdu</p>`;
    const sd = p.score_detail || {}, kn = $("gb-karne");
    if (kn) kn.innerHTML = sd.score == null
      ? `<span class="gb-say mut">—</span><p class="gb-alt">${esc(sd.reason
          || `${sd.n ?? "—"}/${sd.min_sample ?? "—"} kapanmış işlem — skor tanımsız (0.0 DEĞİL)`)}</p>`
      : `<span class="gb-say">${trn(sd.score, 3)}</span>
         <p class="gb-alt"><b>${sd.n}</b> işlem · düşüş ${sd.max_drawdown == null ? "—" : pctf(sd.max_drawdown, 1)} ·
           isabet ${sd.win_rate == null ? "—" : pctf(sd.win_rate, 0)}</p>`;
  }).catch(() => {
    const m = `<span class="gb-say mut">—</span><p class="gb-alt">performans ucu okunamadı</p>`;
    const eq = $("gb-eq"), kn = $("gb-karne");
    if (eq) eq.innerHTML = m;
    if (kn) kn.innerHTML = m;
  });
  // KAPSAMA: pahalı uç ARKADAN çekilir ve şeridin Piyasa satırını da besler — bugüne kadar o satır
  // Piyasa sayfası bir kez açılana dek boş kalıyordu.
  j("/api/market").then(m => {
    MARKET_N = m.n; MARKET_STALE = m.stale_n;
    const el = $("gb-kapsama");
    if (!el) return;
    const n = m.n || 0, taze = m.stale_n == null ? null : n - m.stale_n;
    el.innerHTML = n
      ? `<span class="gb-say${taze == null ? " mut" : ""}">${taze == null ? "—" : pctf(taze / n, 1)}</span>
         <p class="gb-alt"><b>${taze == null ? "—" : taze}</b>/${n} sembolün barı <b>${esc(m.as_of || "—")}</b> seansında ·
           ${m.stale_n ? `<span class="warn">${m.stale_n} bayat</span>`
             : (m.stale_n === 0 ? "bayat yok" : "bayat sayısı ÖLÇÜLMEDİ")}</p>`
      : `<span class="gb-say mut">—</span><p class="gb-alt">evren boş okundu — kapsama hesaplanamaz</p>`;
  }).catch(() => {
    const el = $("gb-kapsama");
    if (el) el.innerHTML = `<span class="gb-say mut">—</span><p class="gb-alt">evren ucu okunamadı</p>`;
  });
};
// ALARM BÜTÇESİ TEK SATIR (ADR). Mevcut `alarmButce()` özeti burada KISALTILMADAN değil,
// ÖZETLENEREK yazılır: tam kırılım Gözetim & Alarmlar'ın işi, buradaki iş "bugün bu bütçe
// aşıldı mı?" sorusunu tek satırda kapatmak.
// ÜÇ DURUM, İKİ DEĞİL (v243, 2026-08-13): "ölçülüyor…" ile "ölçülmedi" AYNI cümle değildir.
// Teşhis ucu artık sayfayı bekletmediği için satır bir süre CEVAPSIZ duruyor; o aralıkta
// "ölçülmedi — uç bu alanı vermedi" yazmak, henüz sorulmamış bir soruya olumsuz cevap uydurmaktır.
// `id="gb-alarm"` sabittir: yanıt gelince satır YERİNDE (outerHTML) değişir.
function gbAlarmSatiri(ab, bekliyor) {
  const hedef = "saglik#operasyon", bag = `<button class="gb-bag" type="button" data-act="go" data-a1="${hedef}">→ ${
    esc(ALAN_ADI.saglik)} <span class="tx3">· alarmlar</span></button>`;
  if (bekliyor) return `<div class="gb-alarm" id="gb-alarm">alarm bütçesi · <span class="mut">ölçülüyor…</span>${bag}</div>`;
  if (!ab) return `<div class="gb-alarm" id="gb-alarm">alarm bütçesi · <b>ölçülmedi</b> — teşhis ucu bu alanı vermedi${bag}</div>`;
  const d = ab.dagilim || {};
  return `<div class="gb-alarm${ab.asim_var ? " asim" : ""}" id="gb-alarm">
    <span>alarm bütçesi · son 24 sa <b>${d.low ?? "—"}</b> low / <b>${d.high ?? "—"}</b> high</span>
    <span${ab.tepe_muafiyet_uygulandi ? ` title="${esc(ab.tepe_beyan || "")}"` : ""}>tepe <b>${
      ab.tepe_10dk ?? "—"}</b>/10dk (tavan ${ab.tavan_10dk ?? "—"})${
      ab.tepe_muafiyet_uygulandi ? ` <span class="ab-not">(restart-muafiyetli · ham ${ab.tepe_ham_10dk ?? "—"})</span>` : ""}</span>
    <span>duran <b>${ab.duran ?? "—"}</b> (tavan ${ab.tavan_duran ?? "—"})</span>
    <span>${ab.asim_var ? "▲ AŞIM" : "aşım yok"}</span>${bag}</div>`;
}

// ==============================================================================================
// HÜCRE ANATOMİSİ (v192) — PANONUN TEK SAYI DİLİ
// ----------------------------------------------------------------------------------------------
// OPERATÖR BULGUSU (2026-08-06, ekran görüntüsüyle): setup×rejim karne matrisi ("Hangi uygulama,
// hangi koşulda?") bir sayıyı ANLATMANIN çalışan biçimini bulmuştu — büyük tabular değer, altında
// kanıtın gücünü taşıyan ince çubuk, altında örneklem/payda satırı, gerekirse bej bir uyarı çipi,
// veri yoksa harf-aralıklı "VERİ YOK". Panonun geri kalanı ise aynı sayıları üç ayrı dille
// yazıyordu (`.durum-say`+`.durum-alt`, `.mcard`, `.srow`) ve hiçbiri KANITIN GÜCÜNÜ taşımıyordu:
// 3 işlemlik bir ortalama ile 55 işlemlik bir ortalama ekranda BİRBİRİNİN AYNI görünüyordu.
//
// BU BLOK YENİ BİR DİL AÇMAZ, VAR OLANI ORTAKLAŞTIRIR. Sınıflar matrisin kendi sınıflarıdır ve
// tek yerde tanımlıdır: `.pm-yield` (değer), `.pm-conf` (kanıt/durum çubuğu), `.pm-n` (meta),
// `.pm-thin` (rozet), `.pm-none` (boş hücre), kap `.pm-cell`. İkinci bir hücre sınıfı ailesi
// açmak, ilk düzenlemede iki dilin ayrışması demekti (bkz. `.km-*`nin BİLEREK ayrı olma gerekçesi
// — orası ayrı bir SEMANTİK; burası aynı semantiğin ikinci kopyası olurdu).
//
// ÇUBUĞUN PAYDASI BEYAN EDİLİR — SÖZLEŞME. Bir çubuk "ne kadar dolu" der; neyin paydası olduğu
// yazmıyorsa okur onu kendi uydurduğu bir tavana göre okur. `hucreGovde` paydasız çubuk ÇİZMEZ:
// `payda` boşsa çubuk hiç doğmaz (uydurma dolulukla "ölçtük" hissi verilmez) ve payda hem
// `data-payda` özniteliğinde hem `title`da durur.
// ---------------------------------------------------------------------------------------------
// KANIT ÇUBUĞUNUN LOG ÖLÇEĞİ — matristen çıkarıldı, artık TEK tanım. 55 işlemlik hücre neredeyse
// dolu, 3 işlemlik hücre üçte bir. `KANIT_TAVAN_N` bir EŞİK DEĞİL bir GÖRÜNTÜ ÖLÇEĞİdir: hiçbir
// karar, hiçbir kapı bu sayıya bağlı değildir (C10 dersi "eşik panoya sabit yazılmaz" kuralı
// hükümler içindir; bir çizim skalası hüküm değildir ve payda satırında adıyla yazar).
const KANIT_TAVAN_N = 61;
const kanitOrani = n => (!n || !Number.isFinite(Number(n))) ? null
  : Math.min(1, Math.log10(Number(n) + 1) / Math.log10(KANIT_TAVAN_N));
// "AZ ÖRNEK" EŞİĞİ — matrisin kendi kuralı (`c.n < 10`), v192'de tek tanıma çıkarıldı. Bir
// GÖRÜNÜRLÜK kuralıdır, bir kapı değil: hiçbir karar bu sayıda değişmez, yalnız rozet doğar.
const AZ_ORNEK_N = 10;
const azOrnek = n => n != null && Number.isFinite(Number(n)) && Number(n) < AZ_ORNEK_N;
// ORAN → ÇUBUK. `oran` 0..1; sınır dışı değer kırpılır (negatif bir "doluluk" çizilemez).
// AYRI BİR "0 ÇUBUK" HÂLİ YOKTUR: oran 0 ise çubuk ÇİZİLİR ve boş görünür (ölçüldü, sıfır çıktı);
// oran null ise çubuk HİÇ doğmaz (ölçülemedi). İkisi ekranda ayırt edilebilir olmak zorunda.
function hucreCubuk(oran, payda) {
  if (oran == null || !Number.isFinite(Number(oran)) || !payda) return "";
  const y = Math.max(0, Math.min(100, Math.round(100 * Number(oran))));
  return `<span class="pm-conf" aria-hidden="true" data-payda="${esc(payda)}"` +
    ` title="çubuk paydası: ${esc(payda)}" style="--conf:${y}%"><i></i></span>`;
}
// HÜCRENİN GÖVDESİ — dört katman, hepsi isteğe bağlı ama SIRASI sabit:
//   deger  → büyük tabular-mono sayı (null/"" ise BOŞ HÜCRE dalı: "VERİ YOK", uydurma sıfır YOK)
//   oran   → kanıt/durum çubuğu (payda beyanlı; paydasız çizilmez)
//   meta   → küçük ikinci satır ("33 işlem · %36 tutan" biçimi) — HTML kabul eder, çağıran kaçırır
//   rozet  → bej küçük-caps çip ("AZ VERİ" · "ÖLÇÜLEMEDİ" · "BEKLİYOR" · "SERMAYE-RESET")
// `degerSinif` YALNIZ anomali/para renginde dolar (`pos`/`neg`/`warn`); nötr değer renksizdir.
function hucreGovde(o) {
  o = o || {};
  const meta = o.meta ? `<span class="pm-n">${o.meta}</span>` : "";
  const rozet = o.rozet ? `<span class="pm-thin">${esc(o.rozet)}</span>` : "";
  // BOŞ HÜCRE: matrisin "ekilmemiş parsel"i. Sıfır BASILMAZ — "ölçtük, sıfır çıktı" ile
  // "ölçemedik" aynı piksele düşerse pano bir bilgi taşımaz, bir izlenim taşır.
  if (o.deger == null || o.deger === "") return `<span class="pm-none">veri yok</span>${meta}${rozet}`;
  return `<span class="pm-yield mono-num${o.degerSinif ? " " + esc(o.degerSinif) : ""}">${o.deger}</span>`
    + hucreCubuk(o.oran, o.payda) + meta + rozet;
}
// HÜCRENİN SESLİ HÂLİ — aynı gövdeden TÜRETİLİR, ikinci kez YAZILMAZ.
// NEDEN GEREKLİ: `rowAttrs` düğmeye bir `aria-label` koyar ve o etiket düğmenin içindeki metnin
// YERİNE geçer. Durum kartları bugüne dek yalnız "Son döngü — durum kaydını aç" diye
// duyuruluyordu: ekran okuyucu kullanan operatör bandın DÖRT SAYISININ hiçbirini duymuyordu.
// Matris bu kusuru kendi hücresinde zaten çözmüştü (`plotCell`in adı ortalamayı, örneklemi ve
// "az örnek"i cümleyle söyler); v192 aynı çözümü bandın tamamına taşır. Etiket gövdeden türediği
// için AYRIŞAMAZ — meta değiştiğinde sesli hâli de değişir.
function hucreSesli(o) {
  o = o || {};
  const duz = h => String(h == null ? "" : h)
    .replace(/<br\s*\/?>/gi, " · ").replace(/<[^>]*>/g, "").replace(/\s+/g, " ").trim();
  return [o.deger == null || o.deger === "" ? "veri yok" : duz(o.deger), duz(o.meta), duz(o.rozet)]
    .filter(Boolean).join(" · ");
}
// ÖZET ŞERİDİ — bölüm-içi sayısal özetlerin kabı. Kap `.pm-grid` ile AYNI reçete (1px saç teli
// ızgara, hücre zemini `--bg`); hücre `.pm-cell`, etiketi `.pm-sectlabel`. DÖRT HÜCRE bir
// bütçedir (durum bandının dört kartıyla aynı gerekçe): beşincisi şeridi tek satırdan taşırır.
// ŞERİT TIKLANMAZ: bu hücrelerin çekmece kaydı yoktur ve bir `<button>` olmayan hücre klavye
// sırasına girmez — tıklanabilir görünüp hiçbir şey açmayan yüzey üretilmez.
function ozetHucre(etiket, o) {
  return `<div class="pm-cell"><span class="pm-sectlabel">${esc(etiket)}</span>${hucreGovde(o)}</div>`;
}
function ozetSerit(hucreler, adlandirma) {
  return `<div class="ozet-serit" role="group" aria-label="${esc(adlandirma)}">${hucreler.join("")}</div>`;
}

// ==============================================================================================
// KART SÖZLEŞMESİ (v198 · D2-a) — KATLANIR KART, `.pm-*` HÜCRE DİLİNİN ÜSTÜNE
// ----------------------------------------------------------------------------------------------
// ÖLÇÜLEN KUSUR (docs/BASELINE-2026-08-06.md §3.2): kart sayısı beş alan sayfasının HİÇBİRİNDE
// bir bütçe değil. Ölçülen asimetri: Öğrenme 39 kart, Gözetim 3 — on üç kat. Bütçesi olan iki
// yüzey (`GENEL_KARTLARI` 6, `DURUM_KARTLARI` 4) bunu LİSTE-VERİ olarak tutup teste saydırdığı
// için tutuyor; alan sayfalarında böyle bir liste yoktu, dolayısıyla sayılamıyordu da.
//
// SIRA KASITLI (D2-a, yeni IA'dan ÖNCE): sözleşmesiz bir sayfa birleşmesi, yoğun iki sayfayı tek
// sütuna dizip yükü ikiye katlardı. Önce kartın kapağı, sonra sayfaların birleşmesi.
//
// ÜÇÜNCÜ DİL İCAT EDİLMEZ. Kapalı özet `hucreGovde(o)` çıktısıdır — `.pm-yield` / `.pm-conf`
// (payda beyanlı) / `.pm-n` / `.pm-thin` / `.pm-none`. v192'nin ortaklaştırdığı hücre dili
// aynen kullanılır; `.kk-*` sınıfları YALNIZ kapağın kendisini (düğme, ok, gövde kabı) taşır,
// tek bir sayı biçimi tanımlamaz.
//
// YAPI KODA DEĞİL MAKİNEYE YAZILIR. Kartlar yirmi dört ayrı yerde şablon-değişmezi olarak
// üretiliyor; başlık/özet/gövde üçlüsünü o yirmi dört yere elle yazmak, sözleşmenin yirmi dört
// kopyası demekti (ve ilk düzenlemede ayrışırdı). Bunun yerine emisyon yeri İKİ İŞARET koyar —
//   `katKart(anahtar)` → kartın etiketine `data-kart` özniteliği
//   `kartOzeti(o)`     → `<h2 class="t">`ten HEMEN SONRA `.kk-ozet` hücresi
// ve kapağın TAMAMINI (düğme, aria, gövde kabı, hafıza, ok) tek bir kurucu (`katKurulumu`)
// çizim sonrası DOM üstünde kurar. Sözleşme böylece TEK yerde yaşar ve testle sayılabilir.
//
// KAPALI ÖZETİN ÜÇ KAPISI (denetimin can damarı — `docs/UX-SADELESTIRME-DENETIMI-2026-08-06.md`
// §5.1). Özet "içeride önemli bir şey var mı?"yı kartı AÇMADAN cevaplamak ZORUNDADIR; cevaplamayan
// bir özet katlamayı yük azaltmaktan çıkarıp TIK ARTIRAN bir süse çevirir. Bu yüzden:
//   1. `deger` var — ya da `.pm-none` "veri yok" + NEDENİ,
//   2. `oran` verildiyse `payda` BEYANLI (paydasız çubuk çizilmez — `hucreCubuk`un kuralı),
//   3. `meta` en fazla iki satır; DEĞER varsa içinde en az bir SAYI, değer yoksa en az bir
//      GEREKÇE (≥20 karakter — YASA 4'ün gerekçe uzunluğuyla aynı ölçü).
// Üçünden biri kurulamıyorsa `kartOzeti` BOŞ DÖNER ve kurucu o kartı katlamaz. Özetsiz kartın
// açık kalması bir kusur değil bir BULGUdur: gizlenecek değil, sayılacak bir şeydir (aşağıdaki
// `_KAT_OZETSIZ` tam olarak onu sayar).
// ----------------------------------------------------------------------------------------------
// KART KAYIT DEFTERİ — anahtar → {alan, bolum}. `GENEL_KARTLARI`/`DURUM_KARTLARI` ile AYNI
// gerekçe: liste VERİ olduğu sürece test onu sayabilir, şablona gömülü olduğu sürece sayamaz.
// Kayıtsız bir anahtar sessizce düşer (uydurma kart doğmaz — `gbKart`/`durumKartHTML` deseni).
// `bolum` ZORUNLU: "sayfanın 1. bölümü açık başlar" kuralı ancak bölüm bilinirse uygulanabilir.
const KART_KAYDI = {
  // ---- ÖĞRENME (39 kartın en kalabalık yüzeyi; §5.3 önceliği 2) ----
  "golge:trend":        { alan: "ogrenme", bolum: "golge" },
  "golge:varyant":      { alan: "ogrenme", bolum: "golge" },
  "bilesenic:edge":     { alan: "ogrenme", bolum: "bilesenic" },
  "bilesenic:sonuc":    { alan: "ogrenme", bolum: "bilesenic" },
  "bilesenic:isi":      { alan: "ogrenme", bolum: "bilesenic" },
  "bilesenic:selale":   { alan: "ogrenme", bolum: "bilesenic" },
  "bilesenic:y3":       { alan: "ogrenme", bolum: "bilesenic" },
  "skiller:revizyon":   { alan: "ogrenme", bolum: "skiller" },
  "skiller:kosular":    { alan: "ogrenme", bolum: "skiller" },
  "skiller:kategori":   { alan: "ogrenme", bolum: "skiller" },
  "hafiza:dersler":     { alan: "ogrenme", bolum: "hafiza" },
  "ajan:surumler":      { alan: "ogrenme", bolum: "ajan" },
  "ajan:beceri":        { alan: "ogrenme", bolum: "ajan" },
  // ---- ③ SAĞLIK (§5.3 önceliği 3; eski "veri" yüzeyi D2-b'de buraya birleşti) ----
  "veriboru:karantina": { alan: "saglik",  bolum: "veriboru" },
  "veriboru:butunluk":  { alan: "saglik",  bolum: "veriboru" },
  "veriboru:redis":     { alan: "saglik",  bolum: "veriboru" },
  "veriboru:saglayici": { alan: "saglik",  bolum: "veriboru" },
  // ---- ② KARAR (§5.3 önceliği 4; `s1` mutabakat masasının ANA cevabı, katlanmaz) ----
  "mutabakat:icra":     { alan: "karar",   bolum: "mutabakat" },
  "mutabakat:band":     { alan: "karar",   bolum: "mutabakat" },
  "mutabakat:gecegun":  { alan: "karar",   bolum: "mutabakat" },
  // ---- v211 · KORUMANIN YENİDEN KURULMASI --------------------------------------------------
  // NEDEN MUTABAKAT MASASI: kartın taşıdığı asıl tuzak bir MUTABAKAT tuzağıdır — iç defterin
  // adedi ile broker'ın adedi AYRIŞIK ve emir broker'ınkini kullanıyor. "İç defterim brokerinkiyle
  // aynı mı?" sorusunun evi burasıdır; kartı Kilitler'e koymak onu bir kola çevirir ve ayrışmayı
  // sorunun sorulduğu yerden koparırdı.
  // KAPAK ALTINDA AMA GİZLENEMEZ: çıplak pozisyon varken özet bir ROZET taşır, rozet `data-dikkat`
  // doğurur ve kurucu kartı oturum hafızasını EZEREK açar. Yani kapak yalnız TEMİZ günlerde kapalı.
  "mutabakat:koruma":   { alan: "karar",   bolum: "mutabakat" },
  // ---- D3-UI · FIRSAT YÜZEYLERİ (C1'in on işi) --------------------------------------------
  // HEPSİ KAPAK ALTINA GİRER VE BU BİLİNÇLİ: on yeni kart, bütçesi zaten aşılmış üç yüzeye
  // ekleniyor. Kapaksız eklemek "ilk bakışta düşen yük"ü on kart büyütmek olurdu — sözleşmenin
  // ölçtüğü tam olarak o. Kapalı özet her birinde kartın KENDİ cümlesini taşır (kapı 1/2/3);
  // dikkat isteyen bir kart (rozet ya da `warn`) kendiliğinden AÇIK doğar, yani bir anomali
  // kapak yüzünden gizlenemez.
  "kapilar:retkarne":   { alan: "karar",   bolum: "kapilar" },      // C1-1
  "kapilar:eylemsizlik":{ alan: "karar",   bolum: "kapilar" },      // C1-8
  "mutabakat:emiryasam":{ alan: "karar",   bolum: "mutabakat" },    // C1-2
  "performans:cikis":   { alan: "karar",   bolum: "performans" },   // C1-9
  "adaylar:denetim":    { alan: "karar",   bolum: "adaylar" },      // C1-7
  "cizelge:damga":      { alan: "saglik",  bolum: "cizelge" },      // C1-4
  "hermes:maliyet":     { alan: "ogrenme", bolum: "hermes" },       // C1-3
  // v219 · W4-N5: `agent_calls` defterinin İLK pano okuyucusu (hermes.py'nin "veri hazır, çizim
  // yok" beyanı bu kartla kapanır). Kapak altında: Öğrenme yüzeyinin bütçesi zaten aşılmış.
  "hermes:telemetri":   { alan: "ogrenme", bolum: "hermes" },
  "ajan:rollback":      { alan: "ogrenme", bolum: "ajan" },         // C1-5
  "ajan:regresyon":     { alan: "ogrenme", bolum: "ajan" },         // C1-6
  "karne:olgunlasma":   { alan: "ogrenme", bolum: "karne" },        // C1-10
  // ---- D3-b · FIRSAT YÜZEYLERİ (F1/F2/F14) — kalan on beş FIRSAT'ın üçü -------------------
  // Üçü de kapak altına girer (bütçesi aşılmış üç yüzeye ekleniyor); kapalı özet kartın KENDİ
  // cümlesini taşır ve dikkat isteyen hâl (canlı şişme · defter boş · alarm eşiği) rozetle
  // AÇIK doğar — anomali kapak yüzünden gizlenemez.
  "veriboru:kagitcanli":{ alan: "saglik",  bolum: "veriboru" },     // F1 · kâğıt-canlı ayrışması
  "bilesenic:sapma":    { alan: "ogrenme", bolum: "bilesenic" },    // F2 · canlı-backtest sapması kökü
  "operasyon:esik":     { alan: "saglik",  bolum: "operasyon" },    // F14 · iki kademeli eşik + NO_DATA
  // ---- D3-b · F5 (v230, 2026-08-09) — YİNELENEN ARIZA TAKSONOMİSİ ------------------------------
  // `watchdog.alarm_gunluk`ın İLK pano okuyucusu. v192 sayacı UCA (`api._alarm_gunluk`) çıkıyordu ama
  // pano çizmiyordu: `test_alarm_hijyeni_v192::test_bastirma_sayaci_PANOYA_cikar` "sayacın dış
  // okuyucusu api.py'dir" der — yani sayı üretiliyordu, GÖRÜNMÜYORDU (YASA 6; F1/F2/F14 ile aynı kova).
  // Kapak altında; bastırma varsa özet rozetiyle AÇIK doğar (anomali kapak yüzünden gizlenemez).
  "operasyon:alarmkok": { alan: "saglik",  bolum: "operasyon" },    // F5 · alarm gürültüsünün kökü
};
// KART BÜTÇESİ — alan sayfası başına YAZILI tavan. BİRİMİ: "ilk çizimde AÇIK doğan kart".
// Toplam kart sayısı DEĞİL: bu turda hiçbir kart silinmiyor (silme kararı D2-b/IA turunda,
// gerekçeyle). Bütçenin ölçtüğü şey ekrana ilk bakışta düşen YÜK.
//
// TAVAN AŞILDIĞINDA KART GİZLENMEZ — BEYAN EDİLİR. Zorla kapatmak, dikkat isteyen bir kartı
// bütçe uğruna kapatmak demek olurdu ve bu sözleşme o an bir güvenlik açığına dönerdi. Aşım
// `.alan-bas`taki kontrol satırında sayıyla yazılır ve ŞİDDET RENGİ TAŞIMAZ (renk yalnız
// anomalide; bütçe aşımı bir sapma değil bir tasarım borcudur).
// D2-b'DE TAVANLAR BİRLEŞMEDİ, TAŞINDI. Bütçenin birimi "ilk bakışta düşen yük"tür ve bir okurun
// bir ekranda tutabildiği kart sayısı iki yüzey birleşti diye İKİYE KATLANMAZ — bütçeleri toplamak
// (4+6=10, 6+3=9) sözleşmeyi birleşmenin kendisiyle gevşetmek olurdu. Denetim §7.1'in yazdığı
// hedef sayı alınır; ölçülen aşım ekranda `.kk-butce` satırında SAYIYLA beyan edilir.
const KART_BUTCESI = {
  karar:    6,   // 21 kart (eski kosu 4 + portfoy 17) · kitap + kuyruk + mutabakatın ana masası
  saglik:   6,   // 12 kart (eski veri 9 + gozetim 3) + çizelge · alarm kutusu ve evren ana cevap
  ogrenme:  6,   // 39 kart · karne (sayfanın 1. bölümü) açık; altı bölüm kapak altında
  kilitler: 5,   // 5 kart · müdahale kolları hiçbir koşulda kapak altına girmez
};
// KURUCUNUN SON TURDA KURDUĞU KAPAK SAYISI — TEK OKUYUCUSU `_katKontrolCiz` (kontrol yalnız
// katlanır kart varsa doğar). YAZILAN TEK ŞEY BU: `acik`/`dikkat`/`ozetsiz` gibi sayaçları burada
// tutmak, okuyucusu olmayan bir durum yazmak olurdu (YASA 6) — ve bayatlardı da, çünkü bütçe
// satırı bu sayıları EKRANDAKİ DOM'dan sayıyor.
let _KAT_KATLANIR = 0;

// EMİSYON YERİNİN BİRİNCİ İŞARETİ. `<div class="card rise"${katKart("golge:trend")}>` biçiminde
// kullanılır — öznitelik parçası döner, HTML değil. Kayıtsız anahtar BOŞ döner ve kart eski
// hâlinde (katlanmaz) kalır: yanlış yazılmış bir anahtar sessizce ekrandan kart silmez.
//
// `alt` — AYNI KAYITTAN ÇOĞALAN KARTLAR İÇİN AYIRICI. Araç kütüphanesi kategorileri gibi bir
// `.map()` çıktısında kart sayısı VERİDEN gelir; kayıt defterine kategori adı yazılamaz (yarın
// yeni kategori doğar). Kayıt anahtarı AİLEyi, `alt` ise örneği adlandırır — kapağın kimliği
// (`id`, oturum hafızası) ikisinin birleşimidir, yoksa on kategori tek hafıza gözünü paylaşırdı.
function katKart(anahtar, alt) {
  if (!KART_KAYDI[anahtar]) return "";
  return ` data-kart="${esc(anahtar)}"` + (alt ? ` data-kart-alt="${esc(String(alt))}"` : "");
}
// EMİSYON YERİNİN İKİNCİ İŞARETİ — kapalı özet. `<h2 class="t">…</h2>` ile gövde ARASINA yazılır.
// ÜÇ KAPI BURADA UYGULANIR; kapıdan geçemeyen özet BOŞ döner ve kart katlanmaz.
function kartOzeti(o) {
  o = o || {};
  const degerVar = !(o.deger == null || o.deger === "");
  // Meta HTML kabul eder (`<b>`, `<br>`); kapılar DÜZ metin üstünde ölçülür.
  const metaDuz = String(o.meta == null ? "" : o.meta).replace(/<[^>]*>/g, " ").replace(/\s+/g, " ").trim();
  // KAPI 3a — iki satır tavanı. `<br>` sayısı 1'i geçerse özet artık bir özet değil, bir gövdedir.
  if ((String(o.meta == null ? "" : o.meta).match(/<br\s*\/?>/gi) || []).length > 1) return "";
  // KAPI 2 — oran verildiyse payda BEYANLI olmalı. `hucreCubuk` paydasız çubuk zaten çizmez;
  // burada bir adım daha ileri gidilir: paydasız bir oran, ÖZETİN kendisini düşürür (yarım
  // kanıtla "içeride önemli bir şey var mı?" sorusu cevaplanmış sayılamaz).
  if (o.oran != null && !o.payda) return "";
  // KAPI 1 + 3b — değer VARSA meta en az bir sayı taşır; değer YOKSA meta bir GEREKÇEdir.
  if (degerVar) { if (!/\d/.test(metaDuz)) return ""; }
  else if (metaDuz.length < 20) return "";
  // DİKKAT İŞARETİ ÖZETTEN TÜRER, ayrıca yazılmaz: rozet (ölçülemeyen/sapan hâl) ya da ŞİDDET
  // sınıfı. Kurucu bunu okuyup kartı AÇIK doğurur — ve oturum hafızasını EZER.
  // `neg` BİLEREK DIŞARIDA: o YÖN rolüdür (K/Z işareti), ŞİDDET değil (D1'in beş renk rolü).
  // Negatif bir sayı bir sapma değildir; "en zayıf araç −0,2R" her gün negatiftir ve onu dikkat
  // saymak kapağı fiilen kaldırır — sözleşme de o an anlamını yitirirdi.
  const dikkat = !!o.rozet || o.degerSinif === "warn";
  return `<span class="kk-ozet"${dikkat ? ' data-dikkat="1"' : ""}>${hucreGovde(o)}</span>`;
}

// ---- OTURUM HAFIZASI -------------------------------------------------------------------------
// `sessionStorage`, `localStorage` DEĞİL (denetim §5.2): geçen haftanın açık kartı bu sabahın
// bakışını yönetmemeli. Depolama erişimi try/catch'lidir — özel kipte `sessionStorage`a dokunmak
// istisna atar ve bir kapak mekanizması yüzünden sayfanın tamamı çizilmemeliydi.
const _katAnahtar = (alan, kart) => `mrd-kart:${alan}:${kart}`;
function _katHatirla(alan, kart) {
  try { return sessionStorage.getItem(_katAnahtar(alan, kart)); } catch (e) { return null; }
}
function _katYaz(alan, kart, acik) {
  try { sessionStorage.setItem(_katAnahtar(alan, kart), acik ? "1" : "0"); } catch (e) { /* depolama yok: hafıza kaybı kabul, çizim kaybı değil */ }
}
// AÇ/KAPA — tek yer. `aria-expanded` ve `hidden` BİRLİKTE değişir: biri ekran okuyucunun, diğeri
// düzenin hâli; ayrışırlarsa pano gören ile duyan operatöre farklı şey söyler.
function _katDurumYaz(kart, acik) {
  const dugme = kart.querySelector(":scope > .t > .kk-dugme");
  const govde = kart.querySelector(":scope > .kk-govde");
  if (!dugme || !govde) return;
  kart.dataset.katAcik = acik ? "1" : "0";
  dugme.setAttribute("aria-expanded", acik ? "true" : "false");
  govde.hidden = !acik;
}
function katKapak(kart) {
  if (!kart || kart.dataset.kat === "hayir") return;
  const acik = kart.dataset.katAcik !== "1";
  _katDurumYaz(kart, acik);
  _katYaz(kart.dataset.katAlan || "", kart.dataset.katKimlik || "", acik);
  _katKontrolTazele();
}
// ---- KURUCU --------------------------------------------------------------------------------
// Çizimden SONRA koşar (`alanSayfasi`in son adımı). İki kez koşarsa hiçbir şey bozulmaz:
// `data-kat-kuruldu` işaretli kartlara dokunmaz (bölüm bazlı yeniden çizimler bunu tetikler).
function katKurulumu(kok, alan) {
  if (!kok) return;
  const ilkBolum = (ALAN_BOLUMLERI[alan] || [])[0] || "";
  let katlanir = 0;
  const ozetsiz = [];
  kok.querySelectorAll(".card").forEach(kart => {
    if (kart.dataset.katKuruldu === "1") {
      if (kart.dataset.kat === "evet") katlanir++;
      return;
    }
    kart.dataset.katKuruldu = "1";
    const anahtar = kart.dataset.kart || "";
    const kayit = KART_KAYDI[anahtar];
    const bas = kart.querySelector(":scope > h2.t");
    const ozet = kart.querySelector(":scope > .kk-ozet");
    // YOĞUN-UZMAN MUAFİYETİ ve KAYITSIZ KART: ikisi de açık kalır. Muafiyet denetimin kuralı —
    // satırlarıyla zaten "içinde ne var" sorusunu cevaplayan tablo cezalandırılmaz.
    if (!kayit || !bas || kart.dataset.kat === "hayir") return;
    // SÖZLEŞMENİN ÇİVİSİ: özet üretilemeyen kart COLLAPSE ALMAZ. Boş özetli bir kapak yükü
    // azaltmaz, tık artırır.
    if (!ozet) { kart.dataset.kat = "hayir"; kart.dataset.katNeden = "özet üretilemedi"; ozetsiz.push(anahtar); return; }

    // KİMLİK = kayıt anahtarı + (varsa) örnek ayırıcısı. `id` DOM'da tek olmak zorunda
    // (`aria-controls` ona bağlanıyor); oturum hafızası da aynı kimliği kullanır.
    const kimlik = anahtar + (kart.dataset.kartAlt ? ":" + kart.dataset.kartAlt : "");
    kart.dataset.katKimlik = kimlik;
    const id = "kk-" + kimlik.replace(/[^\w-]+/g, "-");
    const dugme = document.createElement("button");
    dugme.type = "button";
    dugme.className = "kk-dugme";
    dugme.id = id + "-bas";
    dugme.setAttribute("aria-controls", id);
    // BAŞLIK METNİ TAŞINIR, KOPYALANMAZ: kart başlıklarının bir kısmı çip/alt-etiket taşıyor
    // (`_chip(...)`, `<span class="tx3">`); metni yeniden yazmak o parçaları düşürürdü.
    const ad = document.createElement("span");
    ad.className = "kk-ad";
    while (bas.firstChild) ad.appendChild(bas.firstChild);
    dugme.appendChild(ad);
    // DURUM ROZETİ BAŞLIĞA TAŞINIR (kopya değil, aynı düğüm): rozet YALNIZ ölçülemeyen/sapan
    // hâlde doğar ve kapalı kartta da görünmesi gerekir.
    const rozet = ozet.querySelector(".pm-thin");
    if (rozet) dugme.appendChild(rozet);
    const ok = document.createElement("span");
    ok.className = "kk-ok";
    ok.setAttribute("aria-hidden", "true");
    dugme.appendChild(ok);
    bas.appendChild(dugme);

    // GÖVDE: özetten SONRAKİ her şey tek kaba iner. `role="region"` + `aria-labelledby` ile
    // düğmeye bağlanır; `aria-controls` düğmede zaten var.
    const govde = document.createElement("div");
    govde.className = "kk-govde";
    govde.id = id;
    // ADSIZ BİR `region` LANDMARK OLARAK DUYURULMAZ: adı düğmeden gelir (aynı düğüm, ikinci bir
    // etiket metni yazılmaz — ayrışamaz).
    govde.setAttribute("role", "region");
    govde.setAttribute("aria-labelledby", dugme.id);
    let n = ozet.nextSibling;
    while (n) { const s = n.nextSibling; govde.appendChild(n); n = s; }
    kart.appendChild(govde);

    kart.classList.add("kat-kart");
    kart.dataset.kat = "evet";
    kart.dataset.katAlan = alan;
    katlanir++;

    // AÇIK/KAPALI HÜKMÜ — sıra sözleşmedir:
    //   varsayılan KAPALI → sayfanın 1. bölümü AÇIK → oturum hafızası → DİKKAT hafızayı EZER.
    const dikkat = ozet.dataset.dikkat === "1" || kart.dataset.katDikkat != null
      || kart.classList.contains("uyari") || kart.classList.contains("kopuk");
    const hatirlanan = _katHatirla(alan, kimlik);
    let acik = hatirlanan == null ? (kayit.bolum === ilkBolum) : hatirlanan === "1";
    let ezildi = false;
    // OTURUM HAFIZASI BİR ALARMI GİZLEYEBİLSEYDİ BU SÖZLEŞME BİR GÜVENLİK AÇIĞI OLURDU.
    if (dikkat && !acik) { acik = true; ezildi = hatirlanan != null; }
    _katDurumYaz(kart, acik);
    if (ezildi) {
      const not = document.createElement("p");
      not.className = "hint kk-not";
      not.textContent = "kapalı hatırlanmıştı — sapma geldiği için açıldı";
      kart.insertBefore(not, govde);
    }
  });
  // YASA 4: bulgu sessizce yutulmaz. Özet üretemeyen kart bir tasarım bulgusudur ve kapak
  // ALMAZ — ekranda bütçe satırında sayılır, konsolda ADIYLA yazılır.
  if (ozetsiz.length) console.warn("kart sözleşmesi · özet üretilemedi (kapak verilmedi):", ozetsiz.join(", "));
  _KAT_KATLANIR = katlanir;
  _katKontrolCiz(kok);
}
// ---- SAYFA BAŞINA TEK GLOBAL KONTROL ---------------------------------------------------------
// Denetim §5.2: "tek tek 39 kart açmak bir görev değil bir ceza." Kontrol `.alan-bas`ın içine
// girer; `alanSayfasi` her çizimde orayı yeniden yazdığı için bayat kalamaz.
// KATLANIR KART YOKSA KONTROL DE YOK: hiçbir şeyi açmayan bir düğme, ekranda duran bir yalandır.
function _katKontrolCiz(kok) {
  const bas = kok.querySelector(".alan-bas");
  if (!bas) return;
  const eski = bas.querySelector(".kk-kontrol");
  if (eski) eski.remove();
  if (!_KAT_KATLANIR) return;
  const kap = document.createElement("div");
  kap.className = "kk-kontrol";
  kap.innerHTML = `<button type="button" class="kk-hepsi" data-kk-hepsi="ac">hepsini aç ⌄</button>` +
    `<button type="button" class="kk-hepsi" data-kk-hepsi="kapat">hepsini kapat ⌃</button>` +
    `<span class="kk-butce mut" aria-live="polite"></span>`;
  bas.appendChild(kap);
  _katKontrolTazele();
}
// BÜTÇE BEYANI — sayıyla, renksiz. Aşım gizlenmez ve şiddet rengi de almaz (renk yalnız anomalide).
function _katKontrolTazele() {
  const sayfa = document.querySelector(".page.active");
  const el = sayfa && sayfa.querySelector(".kk-butce");
  if (!el) return;
  // SAYFA KİMLİĞİ DOM'DAN OKUNUR, modül durumundan DEĞİL. Modülde tutulan sayı en son KURULAN
  // sayfaya aittir; geçiş ağı beklemediği için (`go()`) arka planda başka bir sayfa çizilebilir
  // ve o fotoğraf ekrandakine ait olmayabilir — bütçe satırı BAŞKA bir sayfanın tavanını
  // yazardı. Aynı gerekçe sayaçlar için de geçerli: hepsi ekrandaki DOM'dan sayılır.
  const alan = sayfa.id.replace(/^page-/, "");
  const acik = sayfa.querySelectorAll('.card:not([data-kat="evet"]), .card[data-kat="evet"][data-kat-acik="1"]').length;
  const toplam = sayfa.querySelectorAll(".card").length;
  const ozetsiz = sayfa.querySelectorAll('.card[data-kart][data-kat="hayir"]').length;
  const butce = KART_BUTCESI[alan];
  const parca = [`${acik}/${toplam} kart açık`];
  if (butce == null) parca.push("bütçe ÖLÇÜLEMEDİ — bu sayfa için tavan yazılmamış");
  else {
    parca.push(`bütçe ${butce}`);
    if (acik > butce) parca.push(`tavan ${acik - butce} kart aşıldı — kart silinmedi, beyan edildi`);
  }
  if (ozetsiz) parca.push(`${ozetsiz} kart özet üretemedi (kapak yok)`);
  el.textContent = parca.join(" · ");
}
// TIKLAMA TEK DELEGE DİNLEYİCİDE. Satır içi öznitelik YOK (CSP `script-src 'self'` satır içi olay
// özniteliklerini de bloklar) ve `EYLEMLER` izin listesine yeni ad da girmiyor: o liste DOM'a
// `data-act` sokabilen birine global fonksiyon açmamak için var; kapak mekanizması global
// fonksiyon çağırmıyor, kendi düğmesini kendi tanıyor.
document.addEventListener("click", e => {
  const hepsi = e.target.closest(".kk-hepsi");
  if (hepsi) {
    const ac = hepsi.dataset.kkHepsi === "ac";
    const sayfa = hepsi.closest(".page") || document;
    sayfa.querySelectorAll('.card[data-kat="evet"]').forEach(k => {
      _katDurumYaz(k, ac);
      _katYaz(k.dataset.katAlan || "", k.dataset.katKimlik || "", ac);
    });
    _katKontrolTazele();
    return;
  }
  const dugme = e.target.closest(".kk-dugme");
  if (dugme) katKapak(dugme.closest(".card"));
});

// ==============================================================================================
// DURUM KART-IZGARASI (v191) — "Koşu & Döngü" ile "Portföy & Emirler" ÇAKIŞMASININ KAPANIŞI
// ----------------------------------------------------------------------------------------------
// OPERATÖR BULGUSU (2026-08-06): "Koşu & Döngü ile Portföy ve Emirler çakışıyor, benzer şeyleri
// gösteriyorlar; kartlara bölüp tıklayınca detay." Ölçülebilir hâli şuydu — AYNI SAYI İKİ SAYFADA:
//   sermaye + gün K/Z + pozisyon sayısı  → brifing kahramanı (portföy) ve kenar şeridi
//   silahlı emir + ayna durumu           → brifing kahramanı (portföy) + nextSessionCard + mutabakat
//   günün planları (GO/REVIEW/NO_GO)     → brifing "Son sinyaller" (portföy) ve adaylar (koşu)
//   rejim bütçesi + satış günü/FTD       → brifing "Risk" (portföy) ve kapılar (koşu)
// Yani iki sayfa da "sistem şu an nerede?" sorusuna KENDİ yarım cevabını veriyordu.
//
// KARAR: dört kart, TEK tanım, iki sayfanın da başında. Kartlar bir ÖZETTİR; kartın alanlarının
// bugün iki bölüme dağılmış ayrıntısı ÇEKMECEye iner (matrisin/planın kullandığı `rec()` +
// `RECORD_VIEW` mekanizması — yeni bileşen İCAT EDİLMEDİ, aynı klavye ve odak sözleşmesi).
//
// NEDEN YENİ BİR SAYFA / BÖLÜM DEĞİL: `VIEWS` (beş yüzey) ve `ALAN_BOLUMLERI` (yirmi bir bölüm)
// yön belgesinin §3 tablosuna BİREBİR çivilidir (test_s2r1_kabuk_v155, test_ia_v199). Izgara bir
// bölüm DEĞİL, sayfanın KENDİ başlığının altındaki özet bandıdır — Öğrenme'nin `#ogrenme-eylem`
// şeridiyle aynı mertebe: kabı `.alan-bolum` taşımaz, kendi soru cümlesini kurmaz (sayfanın
// sorusunun ÖZETİDİR, ayrı bir soru değil).
//
// TEK KAYNAK KURALI: bir sayı YALNIZ bir kartta durur. Sermaye ② KİTAP'ta, pozisyon sayısı
// ④ POZİSYONLAR'da, silahlı emir ③ EMİRLER'de, gecenin aday/plan sayıları ① SON DÖNGÜ'de.
// Aynı sayının ikinci kopyası bir "hiyerarşi" gibi okunur; yoktur.
//
// D2-b'DE KÜME TEKE İNDİ ve bu, v191 bandının KÖKÜNÜN kapanmasıdır: ızgara iki sayfada çiziliyordu
// çünkü "sistem şu an nerede?" sorusu iki sayfaya bölünmüştü. Sayfalar birleşince ızgara da tek
// yerde doğar — `durumIzgarasiCiz` çağrısı ikiden BİRE indi (denetim §7.1'in ölçülen kazancı).
const DURUM_SAYFALARI = new Set(["karar"]);
// Kart sayısı bir TASARIM BÜTÇESİdir (Genel Bakış'ın altı kartıyla aynı gerekçe): beşincisi
// ızgarayı tek satırdan taşırır ve "tek bakış" iddiasını sessizce yer. Liste veri, şablon değil —
// test onu sayabiliyor.
const DURUM_KARTLARI = [
  ["dongu",    "Son döngü"],
  ["kitap",    "Kitap"],
  ["emir",     "Emirler · ayna"],
  ["pozisyon", "Pozisyonlar"],
];
const _DURUM_AD = Object.fromEntries(DURUM_KARTLARI);
// TEK ÇIKIŞ: `durum-kart` sınıfı YALNIZ burada üretilir. Kart bir `<button>`dır — Tab ile gezilir,
// Enter/Space ile açılır (tarayıcının kendi düğme sözleşmesi; H23 deseninde ikinci bir tuş
// dinleyicisi yazmaya gerek yok). Çekmece bağı `rowAttrs` ile kurulur: kayıt defteri, odak
// dönüşü ve Esc davranışı planla/matrisle AYNI.
//
// GÖVDE ARTIK BİR HÜCREDİR (v192): `.durum-say`/`.durum-alt` ikilisi kaldırıldı ve yerine matrisin
// hücre anatomisi (`hucreGovde`) geçti. Kazanç bir estetik değil bir BİLGİ kanalı: eski gövdede
// hiçbir sayı KANITININ GÜCÜNÜ taşımıyordu — "3 saat önce" ile "31 saat önce", "3 silahlıdan
// 3'ü gitti" ile "3'ünden 0'ı gitti" aynı ağırlıkta okunuyordu.
//
// ANOMALİ NOKTASI KALDIRILDI, RENK KANALI TEK. Nokta ayrı bir işaret dili açıyordu (kartın
// başlığında 7px'lik bir daire) ve aynı sapmayı rozet/renk ile birlikte İKİ KEZ anlatıyordu.
// Artık matrisin kuralı burada da geçerli: sapma varsa HÜCRENİN MÜREKKEBİ renklenir
// (`.durum-kart.uyari` amber · `.durum-kart.kopuk` kırmızı) ve sapmanın adı düğmenin
// `aria-label`ına girer — okuyucu için nokta zaten hiçbir zaman yeterli değildi.
function durumKartHTML(anahtar, kayitK, hucre, { anomali = "", anomaliNe = "" } = {}) {
  const ad = _DURUM_AD[anahtar];
  if (!ad) return "";                    // kayıtsız anahtar sessizce düşer, uydurma kart doğmaz
  return `<button class="durum-kart${anomali ? " " + esc(anomali) : ""}" data-durum="${esc(anahtar)}"
    ${rowAttrs(kayitK, `${ad}: ${hucreSesli(hucre)}${anomaliNe ? ` — ${anomaliNe}` : ""}. Durum kaydını aç.`)}>
    <span class="t">${esc(ad)}</span>
    <span class="durum-govde">${hucreGovde(hucre)}</span>
    <span class="durum-ac" aria-hidden="true">detay →</span></button>`;
}
// Döngü tazelik çubuğunun penceresi. EŞİK DEĞİL GÖRÜNTÜ PENCERESİ: hiçbir kapı, hiçbir alarm bu
// sayıya bağlı değil — çubuk "bugünün turu mu?" sorusunu gözle okutur ve payda ekranda yazar.
const DONGU_TAZELIK_SAAT = 24;
// Gün-içi K/Z çubuğunun bandı (fraksiyon). Yine bir ÇİZİM ÖLÇEĞİ: `max_daily_loss_pct` gibi bir
// HÜKÜM uçtan gelmiyor ve panoya sabit yazılamaz (C10); band adıyla ekranda durur, karar taşımaz.
const KITAP_KZ_BANT = 0.02;
// ---- ① SON DÖNGÜ — gecenin KENDİ kaydı (`/api/today.son_dongu`, v190) ------------------------
// Sayılar olay PENCERESİNDEN değil döngünün kendi satırından gelir; kayıt yoksa sunucunun yazdığı
// NEDEN basılır ("sıfır aday" DEĞİL, "ölçülemedi").
function _durumDonguKarti(t) {
  const sd = t.son_dongu || null;
  const k = rec("durumDongu", { sd, regime: t.regime || {}, vc: t.verdict_counts || {},
                                halted: t.halted, planDate: t.todays_plan_date,
                                latestSession: t.latest_session });
  if (!sd || !sd.var) {
    // BOŞ HÜCRE DALI: değer YOK → "VERİ YOK". Rozet ölçülemeyişi ADIYLA söyler ve sunucunun
    // kendi nedeni meta satırında durur — pano ikinci bir açıklama uydurmaz.
    return durumKartHTML("dongu", k, { deger: null, rozet: "ÖLÇÜLEMEDİ",
      meta: esc((sd && sd.neden)
        || "günlük döngü özeti uçtan gelmedi — ölçülemedi (sıfır aday DEĞİL).") });
  }
  const kapali = sd.data_ok === false;
  // ÜÇLÜ TEK DEĞERDİR ve basamakları AYNI kayıttan gelir (döngünün kendi satırı) — ③'ün
  // `→` hunisiyle karışmasın diye ayraç `·`: o huninin üç basamağı ÜÇ AYRI paydadan gelir.
  const bas = v => v == null ? "—" : trn(v);
  return durumKartHTML("dongu", k, {
    deger: `${bas(sd.candidates)} · ${bas(sd.plans)} · ${bas(sd.armed)}`,
    // TAZELİK ÇUBUĞU: dolu = bu turun kaydı taze. Yaş ölçülemezse çubuk HİÇ çizilmez —
    // "0 saat önce" varsayıp dolu bir çubuk basmak, ölçülmemiş bir tazeliği ölçülmüş göstermekti.
    oran: sd.yas_saat == null ? null
      : Math.max(0, 1 - Number(sd.yas_saat) / DONGU_TAZELIK_SAAT),
    payda: `tazelik · ${DONGU_TAZELIK_SAAT} saatlik pencere`,
    meta: `aday · plan · silahlı<br>${esc(String(sd.date || "—"))} · ${sd.yas_saat == null
      ? `<b class="mut">yaş ölçülemedi</b> (döngü kaydında zaman damgası yok)`
      : `${trn(sd.yas_saat, 1)} saat önce`} · ${sd.regime
      ? esc(REGIME_TR[sd.regime] || sd.regime) : "rejim kaydı yok"}${kapali
      ? `<br><b class="warn">veri kapısı kapalıydı — o gece yeni alım yok</b>` : ""}`,
    rozet: sd.yas_saat == null ? "ÖLÇÜLEMEDİ" : "" },
    kapali ? { anomali: "uyari", anomaliNe: "veri kapısı kapalıydı" } : {});
}
// ---- ② KİTAP — sermaye · nakit · gerçekleşmiş · gün başı (+ beyan-ofset rozeti) ---------------
// BEYAN ROZETİ YALNIZ BEYAN VARSA: `sermaye_koken.ayrisik` false iken rozet HİÇ çizilmez —
// "ofset 0" yazmak, hiç yapılmamış bir beyanı yapılmış gibi göstermek olurdu.
//
// "GERÇEKLEŞMİŞ" GERÇEK-CANLI K/Z'DİR, DEFTER TOPLAMI DEĞİL — ve bu bir düzeltme değil bir YASA
// (meridian/sermaye.py'nin var oluş sebebi). Canlı ölçüm: `portfolio.realized_pnl` bugün
// −5.542,09$ ve bu sayının TAMAMI antrenman tohumundan (replay_seed) geliyor; gerçek-canlı işlem
// sayısı SIFIR. O toplamı karta kırmızı basmak, operatöre bir antrenman artefaktını "sistemin
// kaybı" diye okutmak olurdu — `sermaye.koken` docstring'inin adını koyduğu kusurun ta kendisi.
// Defter toplamı ÇEKMECEDE, tohum ayrıştırmasının yanında durur.
function _durumKitapKarti(t, s) {
  const kk = t.sermaye_koken || {}, kb = t.kitap || {};
  const k = rec("durumKitap", { t, s });
  // ROZET YALNIZ BEYAN VARSA: `kk.ayrisik` false iken çip HİÇ doğmaz. Ofsetin kendisi meta
  // satırında durur — rozet "dikkat, bu taban taşındı" der, rakamı meta söyler.
  const beyan = kk.ayrisik
    ? `<br><span title="Sermaye tabanı BEYANLI olarak taşındı (portfolio.sermaye_resetleri); ofset kitapta yazılıdır">beyan-ofset <b>${
        money(kk.ofset_usd)}</b>${kk.reset_tarihi ? ` · ${esc(String(kk.reset_tarihi).slice(0, 10))}` : ""}</span>`
    : "";
  return durumKartHTML("kitap", k, {
    deger: t.equity == null ? null : money(t.equity),
    // PARA RENGİ (Money Rule) — kökene göre: `sermaye_koken.renk` zaten "poz/neg/nötr" hükmünü
    // taşıyor ve pano ikinci bir işaret kuralı KURMAZ.
    degerSinif: SERMAYE_RENK[kk.renk] || "",
    // GÜN-İÇİ K/Z BANDI: çubuk günün hareketinin bandın neresinde olduğunu gösterir. Gün K/Z
    // ölçülmediyse çubuk YOK — "%0" çizmek "gün düz geçti" demek olurdu.
    oran: t.day_pnl_pct == null ? null
      : Math.min(1, Math.abs(Number(t.day_pnl_pct)) / KITAP_KZ_BANT),
    payda: `gün içi K/Z · ±${pctf(KITAP_KZ_BANT, 0)} bandı`,
    meta: `nakit <b>${money(kk.gercek_canli_sermaye)}</b> · gerçekleşmiş <b class="${cls(kk.canli_pnl_usd)}">${
        kk.canli_pnl_usd == null ? "—" : money(kk.canli_pnl_usd)}</b> <span class="tx3">(gerçek-canlı, ${
        kk.canli_islem_n ?? "—"} işlem)</span><br>gün başı ${kb.day_start_equity == null
      ? `<b class="mut">ölçülmedi</b> — kitapta gün-başı tabanı yok`
      : `<b>${money(kb.day_start_equity)}</b> · gün <span class="${cls(t.day_pnl_pct)}">${
          isr(t.day_pnl_pct, pctf(t.day_pnl_pct))}</span>`}${beyan}`,
    // İKİ ROZET SIRAYLA, TEK SLOT: beyan-ofseti ölçülemeyişten ÖNCE gelir — sermaye okunuyorsa
    // operatörün bilmesi gereken ilk şey tabanın taşınmış olmasıdır. Sermaye hiç okunamadıysa
    // (boş hücre) rozet ölçülemeyişi söyler; iki çipi yan yana basmak şeridi gürültüye çevirirdi.
    rozet: kk.ayrisik ? "SERMAYE-RESET" : (t.equity == null ? "ÖLÇÜLEMEDİ" : "") });
}
// ---- ③ EMİRLER / AYNA — huni + akış + "gönderilecekte kaldı" -------------------------------
// HUNİNİN ÜÇ BASAMAĞI AYNI PAYDADAN GELMEZ ve bu BEYAN EDİLİR: ilk ikisi ŞU ANKİ silahlı kümeden
// (portfolio.armed × alpaca_submitted), üçüncüsü icra defterinin PENCERESİNDEN (E2 ölçümü, gün
// sayısı yükte). Üçünü tek bir "3/2/1" gibi yazmak, farklı paydaları aynı huni sanmak olurdu.
// SARI NOKTA "GÖNDERİLECEKTE KALDI" VAKASI İÇİN: silahlı ama ne aynada ne reddedilmiş bir plan,
// bugüne kadar yalnız `nextSessionCard` satırındaki küçük bir çipte görünüyordu — bir bakışta değil.
function _durumEmirKarti(t, d) {
  const armed = t.armed_plans || [];
  const sent = new Set(t.alpaca_submitted || []);
  const gonderilen = armed.filter(p => sent.has(p.id)).length;
  const ret = armed.filter(p => p.broker_status === "failed_broker_rejection").length;
  const bekleyen = Math.max(0, armed.length - gonderilen - ret);
  const rc = (d || {}).reconcile || {};
  const slp = (((d || {}).icra || {}).slipaj) || {};
  const dl = (slp.ayna || {}).dolum || {};
  const acikRet = ((rc.failed_submissions || {}).open || []).length;
  const akis = rc.stream_ok;                 // true / false / null(=hiç kanıt yok)
  const k = rec("durumEmir", { t, armed, gonderilen, ret, bekleyen, rc, slp, dl, acikRet });
  const dolanTxt = dl.n_dolan == null
    ? `<b class="mut">—</b> <span class="tx3">(${esc(slp.durum || "icra defteri ölçüm vermedi")})</span>`
    : `<b>${trn(dl.n_dolan)}</b> <span class="tx3">(son ${esc(String(slp.pencere_gun ?? "?"))} gün)</span>`;
  // P5 TEKİLLEŞTİRMESİ (D2-b · baseline §2): "WS akıyor mu?" DÖRT yerde yazılıyordu — HUD çipi,
  // bu kart, `spineHTML` ve mutabakat masasının kendi satırı. Değerin TEK EVİ mutabakat masasıdır
  // (durum + kesinti süresi + son tur + poll aralığı + son hata, hepsi bir arada). Bu kart artık
  // yalnız ANOMALİ hâlinde konuşur — çünkü o zaman cümle bir tekrar değil, kartın taşıdığı
  // "kopuk" rozetinin GEREKÇESİdir. Sağlıklı/ölçülmemiş hâlde kart değeri tekrarlamaz, ADRES verir.
  const akisTxt = akis === false
    ? `<span class="neg">ayna akışı KOPUK</span>${wsDownFor(rc) ? ` · ${esc(wsDownFor(rc))}` : ""}`
    : `<span class="tx3">akışın hâli mutabakat masasında (tek ev)</span>`;
  return durumKartHTML("emir", k, {
    deger: `${trn(armed.length)} → ${trn(gonderilen)} → ${dl.n_dolan == null ? "—" : trn(dl.n_dolan)}`,
    // ÇUBUK YALNIZ İLK İKİ BASAMAĞIN ORANIDIR ve paydası bunu söyler. Üçüncü basamağı (dolan)
    // aynı çubuğa katmak, farklı paydaları tek doluluğa toplamak olurdu — huninin kendi
    // beyanının (üç payda ayrıdır) çubukta çiğnenmesi.
    // Silahlı küme boşsa payda YOK: çubuk çizilmez, "%100 gönderildi" gibi okunacak dolu bir
    // çubuk üretmek sıfır paydadan bir oran uydurmaktı.
    oran: armed.length ? gonderilen / armed.length : null,
    payda: "aynaya gönderim oranı · payda: silahlı plan",
    meta: `silahlı → aynaya gönderilmiş → dolan ${dolanTxt}<br>${akisTxt}${
      bekleyen ? `<br><b class="warn">${trn(bekleyen)}</b> plan gönderilecekte kaldı` : ""}${
      acikRet ? `<br><span class="neg">${trn(acikRet)} açık broker reddi</span>` : ""}`,
    rozet: bekleyen ? "BEKLİYOR" : "" },
    bekleyen ? { anomali: "uyari", anomaliNe: `${bekleyen} silahlı plan aynaya gönderilmedi` }
             : (akis === false ? { anomali: "kopuk", anomaliNe: "ayna akışı kopuk" } : {}));
}
// ---- ④ POZİSYONLAR — açık n · toplam ısı R · en yakın stop -----------------------------------
// STOP MESAFESİ GİRİŞE GÖREDİR ve bu BEYANLIDIR: kitapta CARİ FİYAT yok (portfolio.positions
// entry/stop/trail_stop taşır). "Cari fiyata mesafe" yazmak ölçmediğimiz bir şeyi ölçmüş gibi
// göstermek olurdu; ölçtüğümüz şey girişten etkin stopa olan yüzdedir ve etiketi de onu söyler.
function _durumPozisyonKarti(t) {
  const pos = t.open_positions || [];
  const k = rec("durumPozisyon", { t, pos });
  // ISI ÖLÇÜLEMEZSE TOPLANMAZ: `size_r` taşımayan tek bir satır bile varsa toplam eksik olurdu ve
  // eksik bir toplam, tam bir toplam gibi okunur.
  const isiOlculdu = pos.every(p => p.size_r != null && Number.isFinite(Number(p.size_r)));
  const isi = isiOlculdu ? pos.reduce((a, p) => a + Number(p.size_r), 0) : null;
  const mesafe = _durumStopMesafeleri(pos);
  const enYakin = mesafe.length ? Math.min(...mesafe.map(m => m.pay)) : null;
  // TAVAN ORANI YÜKTEN OKUNUR, PANOYA SABİT YAZILMAZ (C10 dersi). Isının R cinsinden sert tavanı
  // (`goal.heat_hard_r`) hiçbir uçtan servis edilmiyor; onu panoya "5,0R" diye gömmek, panonun
  // ölçmediği bir hükmü kendi ağzıyla iddia etmesi olurdu ve zarf değiştiği gün pano sessizce
  // eski tavanı savunmaya devam ederdi. Çubuk bu yüzden YÜKTE VAR OLAN zarfı ölçer: açık riskin
  // rejim maruziyet bütçesine oranı. Bütçe yoksa çubuk çizilmez ve meta nedeni söyler.
  const reg = t.regime || {};
  const butce = Number(reg.exposure_budget_pct);
  const acik = Number(t.current_exposure_pct);
  const zarf = (Number.isFinite(butce) && butce > 0 && Number.isFinite(acik)) ? acik / butce : null;
  return durumKartHTML("pozisyon", k, {
    // DEĞER ISIDIR: "kaç pozisyon" bir sayım, "ne kadar risk açıkta" bir HÜKÜM. Isı ölçülemezse
    // hücre boş çizilir — eksik bir toplam, tam bir toplam gibi okunur.
    deger: isi == null ? null : `${trn(isi, 2)}R`,
    oran: zarf, payda: butce > 0
      ? `açık risk / rejim maruziyet tavanı (%${trn(butce, 1)})` : "",
    meta: `<b>${trn(pos.length)}</b> açık pozisyon · açık risk ${Number.isFinite(acik)
        ? `<b>%${trn(acik, 1)}</b>` : `<b class="mut">ölçülmedi</b>`} ${butce > 0
        ? `· tavan %${trn(butce, 1)}` : `· <span class="mut">rejim tavanı yükte yok</span>`}<br>en yakın stop ${
      enYakin == null
        ? `<b class="mut">—</b> ${pos.length ? "(giriş/stop seviyesi okunamadı)" : "(açık pozisyon yok)"}`
        : `<b>${pctf(enYakin, 1)}</b> <span class="tx3">girişin altında — kitapta cari fiyat yok</span>`}${
      isi == null ? `<br><b class="mut">toplam ısı ölçülemedi</b> (bazı satırda size_r yok)` : ""}`,
    rozet: isi == null ? "ÖLÇÜLEMEDİ" : "" });
}
// Etkin stop = trail varsa trail, yoksa sert stop. İkisi de okunamazsa satır DÜŞER (0 sayılmaz).
function _durumStopMesafeleri(pos) {
  return (pos || []).map(p => {
    const tr = Number(p.trail_stop), st = Number(p.stop), e = Number(p.entry);
    const eff = Number.isFinite(tr) && tr > 0 ? tr : st;
    if (!Number.isFinite(eff) || !Number.isFinite(e) || e <= 0) return null;
    return { ticker: p.ticker, eff, entry: e, pay: (e - eff) / e };
  }).filter(Boolean);
}
// ---- IZGARANIN KENDİSİ -----------------------------------------------------------------------
// ÜÇ UCUN ÜÇÜ DE ÖNBELLEKLİ (`j`, 15 sn): aynı sayfadaki bölümler `/api/today` ve
// `/api/diagnostics`i zaten okuyor, yani ızgara ağ'a fazladan çıkmaz.
// HATA YUTULMAZ (YASA 4): ızgara düşerse kabında NE olduğunu yazar ve sayfanın bölümleri kendi
// verilerini okumayı sürdürür — bir özet bandının düşmesi sayfayı düşürmez.
function durumIzgarasiHTML(t, d, s) {
  return `<div class="durum-izgara">${_durumDonguKarti(t)}${_durumKitapKarti(t, s)}` +
         `${_durumEmirKarti(t, d)}${_durumPozisyonKarti(t)}</div>`;
}
async function durumIzgarasiCiz(kap) {
  if (!kap) return;
  let t, d, s;
  try {
    [t, d, s] = await Promise.all([
      j("/api/today"),
      j("/api/diagnostics").catch(() => null),
      j("/api/summary").catch(() => null),
    ]);
  } catch (e) {
    kap.innerHTML = `<p class="durum-dus">Durum kartları çizilemedi: ${esc(String(e))} —
      sayfanın bölümleri kendi verilerini okumayı sürdürüyor.</p>`;
    return;
  }
  kap.innerHTML = durumIzgarasiHTML(t, d, s);
}
// `bpAlpaca` BURADAN SİLİNDİ (2026-08-02, S2R-sonrası ölü-kod avı). Çağıranı YOKTU — göçten
// ÖNCE de yoktu, yani S2R kırığı değil, "tanımlı ama ölü" sınıfıydı. YASA-6 kontrolü yapıldı:
// okuduğu her alan (`account.connected/equity/buying_power/positions{symbol,qty,upl}/
// open_orders`) `_alpacaKartHTML`de (Ayarlar → Alpaca kartı) zaten okunuyor — tekil okuyucusu
// olduğu alan SIFIR, silmek hiçbir API alanını öksüz bırakmaz. Karar kaydı: UIUX-S2R ADR Ek B.
RENDER.brifing = async () => {
  // KİTABIN ŞU ANKİ HÂLİ — Portföy & Emirler'in ilk bölümü.
  // SIRALAMA (2026-07-27): DURUM ŞERİDİ EN ÜSTTE. Bir tasarım incelemesi şeridi masaüstünde
  // y=710'da, telefonda y=1386'da ölçtü: sayfanın var oluş sebebi olan cümle, bir matrisin ve
  // 48px'lik içeriksiz bir selamlamanın altında kalıyordu.
  //
  // S2R-2 GÖÇÜ — İKİ KART BU BÖLÜMDEN ÇIKTI, BİRİ DE ZİNCİRDEN:
  //   * "Alarm gelen kutusu" ve "Olay akışı · son 8" → Gözetim & Alarmlar. ADR o sayfayı
  //     "alarm gelen kutusu (runbook bağlı) … olay günlüğü" diye tanımlıyor; ikisi de "kitap
  //     nerede?" sorusuna hizmet etmiyordu ve alarmın iki evi olması (burada özet, orada
  //     ayrıntı) tam olarak operatörün "aynı soruya iki yerden cevap" şikâyetiydi.
  //   * `await RENDER.performans()` KALDIRILDI: birikim artık kardeş bir bölüm ve sırasını
  //     ALAN_BOLUMLERI söylüyor. Bir bölümün başka bir bölümü çağırması, sırayı ölçülemez ve
  //     taşınamaz kılıyordu (S2R-2'nin çözdüğü şey buydu).
  // SELAMLAMA ERİDİ: sabah turunun evi artık Genel Bakış. Aynı cümleyi iki sayfada iki kez
  // okutmak yerine tarih/seans bilgisi bölüm altyazısına indi — bir katman az, aynı bilgi.
  //
  // ---- v191 GÖÇÜ: KAHRAMAN BLOĞU (`.hero`) VE "SON SİNYALLER" KARTI BU BÖLÜMDEN ÇIKTI ---------
  // Operatör bulgusu: "Koşu & Döngü ile Portföy & Emirler çakışıyor". Ölçülen çakışmanın TAMAMI
  // bu iki bloktaydı ve üçü de artık `durumIzgarasiHTML`in dört kartında (+ çekmecelerinde):
  //   * kahraman sütun 1 (sermaye · gün K/Z · pozisyon sayısı · sermaye kökeni · eğri kıvılcımı)
  //       → ② KİTAP kartı; eğri kıvılcımının evi zaten Genel Bakış ve `performans` bölümü.
  //   * kahraman sütun 2 (rejim tavanı · açıktaki risk · satış günü/FTD)
  //       → ④ POZİSYONLAR çekmecesi (risk) ve ① SON DÖNGÜ çekmecesi (rejim göstergeleri);
  //         aynı sayılar Koşu & Döngü'nün `kapilar` bölümünde ZATEN tam hâliyle vardı.
  //   * kahraman sütun 3 (zamanlayıcı · Hermes · LLM harcama) → Öğrenme'nin `hermes` bölümünde
  //         zaten tam hâliyle var; "Ayna" satırı → ③ EMİRLER · AYNA kartı.
  //   * "Son sinyaller" kartı → Koşu & Döngü'nün `adaylar` bölümü. AYNI plan listesiydi: biri
  //         `planRowBrief`, diğeri `planRowFull` çiziyordu ve ikisi de aynı satırları açıyordu.
  // BÖLÜMDE KALAN: silahlı emirlerin ve açık pozisyonların AYRINTI TABLOLARI. Kart bir sayıdır,
  // bu tablolar o sayının satırlarıdır — ikisi aynı yerde durursa kart özet olmaktan çıkar.
  const [t, s, h] = await Promise.all([j("/api/today"), j("/api/summary"), j("/api/hermes").catch(() => null)]);
  SUMMARY = s;
  const r = t.regime || {};
  const planDate = t.todays_plan_date || "";
  const sessionDate = r.date || planDate || "";
  const realISO = new Date().toISOString().slice(0, 10);
  const realToday = new Date().toLocaleDateString("tr-TR", { weekday: "long", day: "numeric", month: "long" });
  const _hr = new Date().getHours();
  const greetWord = _hr < 5 ? "İyi geceler" : _hr < 12 ? "Günaydın" : _hr < 18 ? "İyi günler" : _hr < 23 ? "İyi akşamlar" : "İyi geceler";
  const staleSession = sessionDate && sessionDate !== realISO;
  const posRows = (t.open_positions || []).map(p => `<div class="trow" style="grid-template-columns:64px 1fr 88px 72px">
     <span class="tick">${esc(p.ticker)}</span><span class="mut">giriş ${trn(p.entry,2)} · stop ${trn(p.stop,2)}</span>
     <span class="mono-num">hedef ${trn(p.target,2)}</span><span class="mono-num">${p.qty} adet</span></div>`).join("");

  $("bugun-now").innerHTML = `
    ${spineHTML(t, h, null, (_DIAG || {}).hud)}
    ${bolumBasHTML("brifing", "Kitap · ayrıntı",
      `${esc(greetWord)}, ${esc(OPERATOR)} · ${esc(realToday)}${
        staleSession ? ` · son seans <b style="color:var(--tx)">${esc(sessionDate)}</b>` : ""}`)}

    ${nextSessionCard(t)}
    <!-- SAYIYI BAŞLIKTAN ÇIKARDIK (v191): açık pozisyon SAYISI ④ POZİSYONLAR kartının işidir.
         Aynı sayıyı iki yerde göstermek, ikisinden birinin bayatlaması için yeterli bir sebep. -->
    <div class="card rise"><h2 class="t">Açık pozisyonlar</h2>
      ${posRows || `<div class="empty">Açık pozisyon yok.</div>`}</div>`;
  buildSidebar(t, h);
  j("/api/alpaca").then(alp => {                         // yalnız ŞERİT sinyalleri için — ayna kartı mutabakat bölümünde
    const spn = $("triage-spine");
    if (spn) spn.outerHTML = spineHTML(t, h, alp.reconcile || {}, alp.stream || null);
  }).catch(() => {});
};
function staleBits(p) {
  // GS-1140 dersi: süresi dolmuş sinyal taze karar gibi OKUNMAZ. expired → rozet + güncel bağlam satırı.
  if (!p.expired) return { badge: "", ctx: "" };
  const badge = `<span class="tag t-no" style="margin-left:6px" title="planlar tek seans geçerlidir — bu sinyal ${p.age_days ?? "?"} seans önce üretildi ve bir daha silahlanamaz">SÜRESİ DOLDU · ${p.age_days ?? "?"}g</span>`;
  const drift = p.last_close != null && p.entry_trigger
    ? `tetik ${trn(p.entry_trigger, 2)} · son ${trn(p.last_close, 2)} (${p.drift_pct > 0 ? "+" : ""}${trn(p.drift_pct, 1)}%)` : "";
  const fate = p.traded ? "işleme dönüştü" : "emre dönüşmedi";
  return { badge, ctx: `<span class="reason" style="color:${p.traded ? "var(--tx2)" : "var(--amber)"}">${drift}${drift ? " · " : ""}${fate}</span>` };
}
// OPERATÖR ONAYI ROZETİ (v190). Onay bir OLAYdır: kapı etiketi (REVIEW) DEĞİŞMEZ, rozet onun
// YANINDA durur. Damga MUTLAK yazılır ("5 Ağu 14:55") — "az önce" diyen bir onay, sayfa açık
// kaldıkça saatlerce taze görünürdü. Damga okunamazsa saat UYDURULMAZ, rozet damgasız basılır.
function onayRozeti(p) {
  const o = p && p.operator_onayi;
  if (!o || !o.ts) return "";
  const t = mutlakTs(o.ts);
  return `<span class="tag t-go" style="margin-left:6px"
    title="Operatör bu REVIEW planını onayladı — kapı hükmü değişmedi, plan giriş kuyruğuna alındı${
      o.kanal ? ` (kanal: ${esc(o.kanal)})` : ""}">operatör-onaylı${t ? ` · ${esc(t)}` : ""}</span>`;
}
// PLAN KAYDININ EYLEM BLOĞU (v190) — operatörün "review edebiliyorum, işlem yapamıyorum"
// şikâyetinin kapandığı yer. Düğme YALNIZ REVIEW planında çizilir: GO zaten giriş kuyruğunda,
// NO_GO ise ASLA onaylanamaz (guard'ın sert reddi mutlaktır; ona düğme çizmek, kapıyı ezilebilir
// göstermek olurdu). Süresi dolmuş plan da onaylanamaz — sunucu da 409 verir, arayüz o reddi
// önden söyler ki operatör ölü bir düğmeye basmasın.
function planOnayBloguHTML(p) {
  const id = String((p && p.id) || "");
  if (!id) return "";
  const o = p.operator_onayi;
  if (o && o.ts) {
    const t = mutlakTs(o.ts);
    return `<p class="pd-warn" style="border-color:var(--green);color:var(--tx2)">
      <b>Operatör onaylı${t ? ` · ${esc(t)}` : ""}</b>${o.kanal ? ` (${esc(o.kanal)})` : ""} —
      kapı hükmü <b>${esc(p.gate_verdict || "?")}</b> olarak KALDI (onay bir olaydır, hüküm değil).
      Plan giriş kuyruğunda; dolum bir sonraki açılışta, kapılar aynen koşar.</p>`;
  }
  if ((p.gate_verdict || "") !== "REVIEW") return "";
  if (p.expired) return `<p class="hint">Süresi dolmuş bir plan onaylanamaz — seviyeleri bayat.</p>`;
  return `<div style="margin:14px 0">
    <button class="dlbtn" type="button" id="plan-onay-btn" data-act="planOnayla" data-a1="${esc(id)}">Onayla ve Arm Et</button>
    <p class="hint" id="plan-onay-msg" style="margin:8px 0 0">İki adımlı onay: ilk basış niyet, ikinci basış karar.
      Onay kapı hükmünü DEĞİŞTİRMEZ — planı giriş kuyruğuna alır; HALT/devre-kesici/veri/slot kapıları aynen koşar.</p></div>`;
}
// İKİ ADIMLI ONAY — ⌘K paletinin deseni (palette.js `onayIste`): yazan bir komut ilk basışta
// ÇALIŞMAZ, önce bir onay adımına döner. Burada modal yerine düğmenin KENDİSİ onay adımına geçer
// (çekmecenin içindeyiz; üstüne ikinci bir katman koymak odağı çekmeceden koparırdı). Zaman aşımı
// niyeti unutur: yarım kalmış bir onay adımı, sonraki tıklamada sürpriz bir emre dönüşemez.
let _PLAN_ONAY_ADIM = null, _PLAN_ONAY_ZAMAN = null;
// Onay adımının GÖRSEL imzası satır içi verilir: `.armed` sınıfı yalnız kapak altındaki kademe
// düğmelerine (`.ksgroup button.armed`) stillenmiştir; burada kullanılsaydı düğme adım değiştirir
// ama HİÇBİR ŞEY değişmiş görünmezdi — sessiz bir durum değişimi, tam da kaçındığımız şey.
const _ONAY_ADIM_STIL = { borderColor: "var(--amber)", color: "var(--amber)" };
function _planOnayStil(btn, acik) {
  if (!btn) return;
  btn.style.borderColor = acik ? _ONAY_ADIM_STIL.borderColor : "";
  btn.style.color = acik ? _ONAY_ADIM_STIL.color : "";
}
function _planOnayGeriAl(btn, msg) {
  _PLAN_ONAY_ADIM = null;
  _planOnayStil(btn, false);
  if (btn) btn.textContent = "Onayla ve Arm Et";
  if (msg) msg.textContent = "Onay adımı zaman aşımına uğradı — istersen yeniden bas.";
}
window.planOnayla = async (planId) => {
  if (!planId) return;
  const btn = $("plan-onay-btn"), msg = $("plan-onay-msg");
  if (_PLAN_ONAY_ADIM !== planId) {
    _PLAN_ONAY_ADIM = planId;
    _planOnayStil(btn, true);
    if (btn) btn.textContent = "Emin misin? — tekrar bas: ONAYLA ve ARM ET";
    if (msg) msg.textContent = "Bu bir YAZMA eylemidir: plan giriş kuyruğuna girer ve bir sonraki açılışta dolabilir.";
    clearTimeout(_PLAN_ONAY_ZAMAN);
    _PLAN_ONAY_ZAMAN = setTimeout(() => { if (_PLAN_ONAY_ADIM === planId) _planOnayGeriAl(btn, msg); }, 8000);
    return;
  }
  clearTimeout(_PLAN_ONAY_ZAMAN);
  _PLAN_ONAY_ADIM = null;
  _planOnayStil(btn, false);
  if (btn) { btn.disabled = true; btn.textContent = "onaylanıyor…"; }
  if (msg) msg.textContent = "gönderiliyor…";
  try {
    // v219: `!r.ok` dalı BURADAN KALKTI ama cümlesi kalktı DEĞİL — `apiFetch` artık aynı gerekçeyi
    // `ApiHata.message` içinde ("HTTP 409 — <sunucunun kendi cümlesi>") fırlatıyor ve aşağıdaki
    // `catch` onu basıyor. SESSİZ "OLMADI" YOK: NO_GO reddi, seansı geçmiş plan, HALT, slot yok…
    // hepsi sunucunun kendi metniyle görünür. Düğme geri gelir — karar operatörün.
    const r = await apiFetch("/api/plan/" + encodeURIComponent(planId) + "/onayla", { method: "POST" });
    let body = {};
    try { body = await r.json(); }
    catch (e) { body = {}; }   // YASA 4 · işaretli yutma: 2xx gövdesi JSON değil; aşağıdaki alanlar "?" basar, uydurma sayı YOK
    if (msg) msg.innerHTML = `<span class="pos">✓ onaylandı — plan silahlı kuyrukta (${body.armed_n ?? "?"} silahlı emir).</span>
      Dolum bir sonraki açılışta; aynaya göndermek için Ayarlar'daki "Silahlı planları Alpaca'ya gönder".
      ${body.not ? `<br><span class="warn">${esc(body.not)}</span>` : ""}`;
    if (btn) btn.remove();
    refreshStatus();                     // şerit/rozet taze okusun (mutasyon yanıt önbelleğini zaten düşürdü)
  } catch (e) {
    if (msg) msg.innerHTML = `<span class="neg">${esc(String(e.message || e))}</span>`;
    if (btn) { btn.disabled = false; btn.textContent = "Onayla ve Arm Et"; }
  }
};
// `planRowBrief` SİLİNDİ (v191, "Son sinyaller" kartıyla birlikte). Tek çağıranı o karttı ve kart
// Koşu & Döngü'deki `adaylar` bölümünün AYNISINI gösteriyordu — operatörün "benzer şeyleri
// gösteriyorlar" şikâyetinin en birebir hâli. YASA-6 kontrolü yapıldı: okuduğu her alan
// (`ticker/setup/score/gate_verdict/gate_reasons/r_multiple_expected/size_r` + `staleBits` ve
// `onayRozeti` yüzeyleri) `planRowFull`da (adaylar bölümü, `_PHEAD` tablosu) ZATEN okunuyor —
// tekil okuyucusu olduğu alan SIFIR. Çekmece kaydı da aynı: `rec("plan", …)` → `RECORD_VIEW.plan`.

// ================= ADAYLAR (sinyaller) =================
const _VORDER = { GO: 0, REVIEW: 1, NO_GO: 2 };
const _PHEAD = `<div class="trow head" style="grid-template-columns:78px 66px 1fr 92px 56px 90px"><span>TARİH</span><span>HİSSE</span><span>ANALİZ ZİNCİRİ</span><span>GİRİŞ→HEDEF</span><span>R:R</span><span style="text-align:right">KAPI</span></div>`;
RENDER.adaylar = async () => {
  // MATRİS ARTIK BURADA (2026-07-27): Bugün'ün tepesinden alındı, çünkü Bugün'ün açılış sorusu
  // "senden bir şey bekliyor mu?"dur ve matris o cümleyi y=710'a itiyordu. Kararlar'da ise matris
  // süs değil DAYANAK: bugünkü adayın kurulumu bu rejimde bugüne dek ne verdi? Sayfa kanıtla açılır,
  // sonra önerilere, sonra senin onayını bekleyenlere iner.
  // AWAIT ŞART: ateşle-unut çağrılırsa go()'nun revealActive'i matrisin `.rise`'ından ÖNCE koşar
  // ve matris `.in` sınıfını hiç alamaz — DOM'da var ama görünmez olur (bkz. RENDER.brifing notu).
  await renderPlotMap();
  // DENETİM İZİ AYRI UÇTAN (C1-7): `/api/signals` defterin SON 120 satırını verir ve tavanı
  // beyan eder; `/api/audit_trail` defterin TAMAMI üstünde sayar ve sorgu alır. İkisi aynı
  // defteri farklı SORU için okur — biri "sırada ne var", diğeri "geçmişte ne karar verdim".
  // Sorgu durumu modül düzeyinde tutulur (`_DENETIM_SEMBOL`), çünkü bölüm yeniden çizildiğinde
  // filtrenin kaybolması operatörün yazdığı sorguyu sessizce silmek olurdu.
  const [d, at] = await Promise.all([
    j("/api/signals"),
    j("/api/audit_trail" + (_DENETIM_SEMBOL ? "?sembol=" + encodeURIComponent(_DENETIM_SEMBOL) : ""))
      .catch(() => null),
  ]);
  const plans = (d.plans || []).slice()
    .sort((a, b) => (_VORDER[a.gate_verdict] ?? 3) - (_VORDER[b.gate_verdict] ?? 3)
                    || String(b.date).localeCompare(String(a.date)));
  const asOf = d.as_of, latestSignal = d.latest_signal_date, provider = d.data_provider || "veri";
  const actionable = plans.filter(p => p.gate_verdict === "GO" || p.gate_verdict === "REVIEW");
  const rejected = plans.filter(p => p.gate_verdict === "NO_GO");
  // FORWARD view = plans from the NEWEST signal session (armed for the NEXT open). Everything older is the
  // audit trail — those plans already armed/expired. This is why the page is forward-looking, not a log.
  const nextActionable = actionable.filter(p => String(p.date) === String(latestSignal));
  const histActionable = actionable.filter(p => String(p.date) !== String(latestSignal));
  const staleFresh = asOf && latestSignal && String(latestSignal) < String(asOf);   // data newer than last signal
  const vc = {}; plans.forEach(p => vc[p.gate_verdict] = (vc[p.gate_verdict] || 0) + 1);
  const rc = {};
  rejected.forEach(p => (p.gate_reasons || ["(gerekçesiz)"]).forEach(r => {
    const key = String(r).split("(")[0].replace(/%?\s*[0-9]+([.,][0-9]+)?\s*%?/g, " ").replace(/\s+/g, " ").trim();
    rc[key] = (rc[key] || 0) + 1;
  }));
  const rcTop = Object.entries(rc).sort((a, b) => b[1] - a[1]).slice(0, 6);
  const bySkill = {};
  (d.candidates || []).forEach(c => bySkill[c.source_skill] = (bySkill[c.source_skill] || 0) + 1);
  // BUGÜNÜN ELEMELERİ ÖNCE (2026-07-22, operatör: "son sinyaller kararlar kısmına yansımamış"):
  // eskiden 120 planlık TÜM geçmişten ilk 10 gösteriliyordu ve o günün kararı arada kayboluyordu.
  // Kapı bugün bir şey elediyse operatörün ilk göreceği şey o olmalı.
  const rejToday = rejected.filter(p => String(p.date) === String(latestSignal));
  const rejOlder = rejected.filter(p => String(p.date) !== String(latestSignal));
  const rejRows = rejToday.concat(rejOlder).slice(0, 10).map(planRowFull).join("");
  const candRows = (d.candidates || []).slice(0, 24).map(c => `<div class="trow" style="grid-template-columns:78px 66px 1fr 60px 60px 90px">
     <span class="mut" style="font-size:11px">${esc(c.date)}</span><span class="tick" style="font-size:14px">${esc(c.ticker)}</span>
     <span class="chain">${esc(c.source_skill||'')}</span><span class="mono-num">${c.score}</span>
     <span class="mono-num">RS ${c.rs_rating??'—'}</span><span class="mut" style="font-size:11px">${esc(c.sector||'')}</span></div>`).join("");
  $("adaylar-now").innerHTML = `
    ${bolumBasHTML("adaylar", "Tarama hattı · bir sonraki açılış",
      `Veri <b style="color:var(--tx)">${esc(asOf || '—')}</b>'e kadar taze · kaynak <b style="color:var(--tx)">${esc(provider)}</b> · adaylar <b style="color:var(--tx)">bir sonraki açılışa</b> yöneliktir`)}

    ${(() => {   // yerel LLM ajanının İKİNCİ GÖRÜŞÜ — danışma katmanı, kapı kararını değiştirmez
      const rv = d.candidate_review || {};
      if (!rv.date || !(rv.reviews || []).length) return "";
      const OP = { destekle: ["destekle", "t-go"], "çekimser": ["çekimser", "t-rv"], "karşı": ["karşı", "t-no"] };
      const rows = rv.reviews.map(r => {
        const [lbl, kls] = OP[r.opinion] || [r.opinion, "t-vi"];
        return `<div class="trow" style="grid-template-columns:64px 92px 1fr">
          <span class="tick">${esc(r.ticker)}</span><span><span class="tag ${kls}">${esc(lbl)}</span></span>
          <span class="mut" style="font-size:12px">${esc(r.note || "")}</span></div>`;
      }).join("");
      // BAYATLIK DÜRÜSTÇE SÖYLENİR: görüş katmanı bir seansı kaçırırsa (canlıda oldu — tek-atışlık
      // koşuda daemon thread öldürülüyordu) eski görüş taze karar gibi okunurdu.
      const bayat = latestSignal && String(rv.date) < String(latestSignal);
      return `<div class="card rise"><h2 class="t">LLM ikinci görüşü · ${esc(rv.date)} · ${esc(rv.model || rv.brain || "")}${
        bayat ? ` <span class="warn" style="letter-spacing:0;text-transform:none">— BAYAT: ${esc(latestSignal)} seansı için görüş alınmadı</span>` : ""}</h2>
        <p class="hint" style="margin-top:0">Danışma katmanı — kapı kararını DEĞİŞTİRMEZ, yalnız not düşer.</p>
        ${rows}</div>`;
    })()}

    <div class="card rise"><h2 class="t">${d.latest_session && latestSignal && latestSignal < d.latest_session
        ? `Son sinyaller · ${esc(latestSignal)} <span class="warn" style="letter-spacing:0;text-transform:none">— süresi doldu; ${esc(d.latest_session)} seansından beri kapıyı geçen taze aday yok</span>`
        : `Bir sonraki açılış için${latestSignal ? ` · ${esc(latestSignal)} kapanışından` : ''}`} <span class="tx3" style="font-weight:400">(${nextActionable.length})</span></h2>
      ${/* ---- BÖLÜM ÖZETİ · HÜCRE ŞERİDİ (v192) ------------------------------------------------
            Kapının çıktısı bugüne kadar YALNIZ aşağıdaki `.g2` panosunda, tek boşluklu bir mono
            listede duruyordu ("GO ....... 3"). O liste okunabilir ama TARTILAMAZ: 3 GO'nun 4
            plandan mı 120 plandan mı geldiği aynı satırda görünmüyordu. Şerit her hükmü kendi
            PAYDASIYLA (o seansın plan sayısı) çizer; huni hücresinin paydası ise adaydır ve bu
            iki payda AYRI olduğu için iki ayrı çubukta durur, tek bir "oran" gibi toplanmaz.
            SATIR TABLOLARI DEĞİŞMEDİ: aşağıdaki plan/eleme tabloları yoğun-uzman düzenidir ve
            hücreleşseydi bir tabloda 40 hücre eden bir ızgaraya dönerdi. */""}
      ${(() => {
        // ŞERİDİN KAPSAMI KARTIN KAPSAMIDIR — SON SEANS. Defter penceresinin tamamını (`vc`,
        // `plans`) bu kartın içine özet diye koymak, başlığı "bir sonraki açılış" olan bir
        // kutuya yüz yirmi günlük bir dağılım basmak olurdu: aynı kutuda iki farklı payda, ve
        // hangisinin okunduğu ancak kaynağa bakınca anlaşılırdı. Pencere dağılımı aşağıdaki
        // `.g2` panosunda kendi başlığıyla durmayı sürdürüyor.
        const sPlan = latestSignal ? plans.filter(p => String(p.date) === String(latestSignal)) : [];
        const sAday = latestSignal
          ? (d.candidates || []).filter(c => String(c.date) === String(latestSignal)).length : 0;
        const nP = sPlan.length;
        const svc = {};
        sPlan.forEach(p => svc[p.gate_verdict] = (svc[p.gate_verdict] || 0) + 1);
        // ÜÇ HÜKÜM SAYIMDIR, ÖLÇÜM DEĞİL: `svc` planların üstünde sayılıyor, yani 0 gerçekten
        // "ölçtük, sıfır çıktı"dır ve `?? 0` bir uydurma değil. Payda YOKSA (hiç plan yok) çubuk
        // çizilmez ve DEĞER de basılmaz — sıfır paydadan oran üretmek bu panonun reddettiği şey.
        const h = (etiket, n, sinif) => ozetHucre(etiket, {
          deger: nP ? trn(n) : null, degerSinif: nP && sinif ? sinif : "",
          oran: nP ? n / nP : null, payda: `seansın planı (${nP})`,
          meta: nP ? `%${Math.round(100 * n / nP)} · ${nP} planın ${n} tanesi`
                   : "bu seansta plan üretilmedi — payda kurulamadı",
          // ROZET YOK: payda sıfır olduğunda ORAN tanımsızdır ama "plan üretilmedi" ÖLÇÜLMÜŞ bir
          // olgudur. Buraya "ÖLÇÜLEMEDİ" çipi basmak, ölçülmüş bir boşluğu ölçülememiş gibi
          // göstermek olurdu — rozet kelimeleri yalnız GERÇEKTEN okunamayan alanlara ayrılır
          // (kapılar şeridinde `bud == null`, mutabakat şeridinde `red_orani == null` gibi).
          rozet: azOrnek(nP) && nP ? "AZ ÖRNEK" : "" });
        return ozetSerit([
          ozetHucre("Tarama → plan", {
            deger: sAday ? `${trn(sAday)} → ${trn(nP)}` : null,
            oran: sAday ? nP / sAday : null, payda: `seansın tarama adayı (${sAday})`,
            meta: sAday ? `${esc(latestSignal || "—")} · aday → kapıya giren plan`
                        : "bu seansta tarama adayı yok — huninin paydası kurulamadı",
            rozet: "" }),
          // RENK YALNIZ ELEMEDE: GO/REVIEW bir hüküm dağılımıdır, bir sapma değil — yeşile
          // boyamak "iyi gidiyor" okuması üretirdi ve pano o cümleyi kurmaz.
          h("Kapıdan geçen · GO", svc.GO ?? 0, ""),
          h("İncelemeye düşen", svc.REVIEW ?? 0, ""),
          h("Elenen · NO_GO", svc.NO_GO ?? 0, "warn"),
        ], "Disiplin kapısının bu seanstaki hüküm dağılımı");
      })()}
      ${gateLegend()}
      ${nextActionable.length ? _PHEAD + nextActionable.map(planRowFull).join("")
        : (rejToday.length
            // BOŞLUĞUN SEBEBİ GÖRÜNÜR OLMALI: "aday yok" ile "aday vardı, kapı eledi" AYRI şeylerdir.
            // Motor bugün çalıştıysa ve kapı eledi ise bu bir KARARDIR — gerekçesiyle burada durur.
            ? `<div class="empty" style="text-align:left">
                 <b>${esc(latestSignal)} seansında ${rejToday.length} plan üretildi, ${rejToday.length === 1 ? "o da" : "hepsi de"} disiplin kapısında elendi.</b>
                 Motor çalıştı ve karar verdi — bu bir boşluk değil, bir <b>karar</b>.
                 <div style="margin-top:10px">${rejToday.map(p => `<div class="trow" style="grid-template-columns:70px 1fr">
                    <span class="tick">${esc(p.ticker)}</span>
                    <span class="chain">${esc((p.gate_reasons || []).join(" · ") || "gerekçe kaydı yok")}</span></div>`).join("")}</div>
                 <p class="hint" style="margin-top:10px">Ayrıntılı karar ağacı aşağıdaki "Elenen planlar" tablosunda.</p></div>`
            : `<div class="empty">${staleFresh
                 ? `Veri ${esc(asOf)}'e kadar işlendi ama <b>${esc(latestSignal)}</b> sonrası disiplin kapısını geçen taze bir kurulum çıkmadı — dürüst boşluk, uydurma yok.`
                 : `Bu seansta temiz geçen taze bir aday yok — dürüst boşluk. Piyasa uygun olduğunda ajan otomatik silahlanır.`}</div>`)}
</div>

    <div class="g2 rise">
      <div class="pane"><p class="mut" style="font-size:12px;margin-bottom:14px">${T("tarama hattı", "pipeline")} · son çalışma</p>
        <div class="mono"><span class="k">tarama</span> toplam ${(d.candidates||[]).length} aday
${Object.entries(bySkill).map(([k, n]) => `  ${esc(k).padEnd(26, ' ')} ${n}`).join("\n")}

<span class="k">kapı</span> disiplin kontrolü
  <span class="ok">GO</span> ....... ${vc.GO || 0}
  <span class="w">REVIEW</span> ... ${vc.REVIEW || 0}
  <span class="no">NO_GO</span> .... ${vc.NO_GO || 0}</div></div>
      <div class="pane"><p class="mut" style="font-size:12px;margin-bottom:14px">elenme nedenleri (özet)</p>
        <div class="mono">${rcTop.length ? rcTop.map(([r, n]) => `  <span class="no">${String(n).padStart(3,' ')}</span> × ${esc(r)}`).join("\n") : '<span class="d">eleme yok</span>'}</div>
</div>
    </div>

    ${rejected.length ? `<div class="card rise"><h2 class="t">Elenen planlardan örnekler (${rejected.length})</h2>
      <div class="trow head" style="grid-template-columns:78px 66px 1fr 92px 56px 90px"><span>TARİH</span><span>HİSSE</span><span>${T("ANALİZ ZİNCİRİ", "skill")}</span><span>GİRİŞ→HEDEF</span><span>${T("R:R", "rr")}</span><span style="text-align:right">${T("KAPI", "kapi", true)}</span></div>
      ${rejRows}
      ${rejected.length > 10 ? `<p class="mut" style="font-size:12px;margin-top:10px">… ${rejected.length - 10} eleme daha (yukarıdaki özet hepsini kapsar).</p>` : ''}</div>` : ''}

    ${/* ---- DETAY KATMANINA İNDİ (S2R-2 "soruya hizmet" denetimi) --------------------------
          Bölümün sorusu: "gece döngüsü ne önerdi — kapıdan ne geçti, ne elendi?" GEÇMİŞ
          sinyaller o soruya hizmet etmez: geçmiş planlar zaten silahlandı ya da süresi doldu;
          bugünün kararına dayanak olmazlar. SİLİNMEDİ çünkü `ledger.plans_total/plans_shown`
          alanlarının TEK okuyucusu bu blok (kırpma beyanı başka hiçbir yüzeyde yok) ve denetim
          izi bir kanıttır. ---- */""}
    ${histActionable.length ? detayKatmani(
      `Geçmiş sinyaller · denetim izi (${histActionable.length})`,
      "Bu blok bölümün sorusuna (bugün kapıdan ne geçti?) hizmet etmiyor — geçmiş planlar zaten "
      + "silahlandı ya da süresi doldu. Kanıt olduğu için silinmedi, mertebesi düştü.",
      `${(() => { const L = d.ledger || {};
          return (L.plans_total && L.plans_shown && L.plans_total > L.plans_shown)
            ? `<p class="hint warn">Kırpma: son ${L.plans_shown} plan gösteriliyor (defterde ${L.plans_total}).</p>` : ""; })()}
       ${_PHEAD}${histActionable.slice(0, 30).map(planRowFull).join("")}`) : ''}

    ${/* Ham tarama çıktısı: kapıdan geçmemiş, hüküm verilmemiş satırlar. Bölümün sorusu
          "kapıdan ne geçti"; kapı görmemiş bir liste o soruya cevap değil, girdi. `candidates[]`
          satır alanlarının (rs_rating, sector, score) TEK okuyucusu burası — yukarıdaki özet
          yalnız `source_skill` sayıyor. */""}
    ${detayKatmani(
      `Ham tarama çıktısı (${(d.candidates||[]).length})`,
      "Kapı görmemiş girdi listesi — bölümün sorusu kapının ÇIKTISI. Satır alanlarının "
      + "(RS, sektör, skor) tek okuyucusu bu tablo olduğu için silinmedi, detay katmanına indi.",
      `${(() => { const L = d.ledger || {};
          return (L.candidates_total && L.candidates_shown && L.candidates_total > L.candidates_shown)
            ? `<p class="hint warn">Kırpma: son ${L.candidates_shown} aday (defterde ${L.candidates_total}).</p>` : ""; })()}
       <div class="trow head" style="grid-template-columns:78px 66px 1fr 60px 60px 90px"><span>TARİH</span><span>HİSSE</span><span>KAYNAK</span><span>${T("SKOR", "skor")}</span><span>${T("RS", "rs")}</span><span>SEKTÖR</span></div>
       ${candRows || `<div class="empty">Aday yok.</div>`}`)}
    ${firsatDenetimIzi(at)}`;
  // ONAY KUYRUĞU ARTIK BURADAN ÇAĞRILMIYOR (S2R-2): ADR'deki evi Portföy & Emirler ve kabı da
  // oraya taşındı. S2R-1'de kap `#page-adaylar`ın İÇİNDE olduğu için alias'ı Koşu'ya bakmak
  // zorundaydı; bölünme o borcu kapattı.
};
function planRowFull(p) {
  const v = p.gate_verdict || "?";
  const st = staleBits(p);
  const k = rec("plan", p);
  return `<button ${rowAttrs(k, `${p.date} · ${p.ticker} · kapı ${v}. Planı aç.`)}
    class="trow rowbtn" style="grid-template-columns:78px 66px 1fr 92px 56px 90px">
    <span class="mut" style="font-size:11px">${esc(p.date)}</span><span class="tick" style="font-size:14px">${esc(p.ticker)}${st.badge}</span>
    <span class="chain">${esc((p.skill_chain||[]).join(" → "))}${st.ctx ? "<br>" + st.ctx : ""}</span>
    <span class="mono-num" style="font-size:11px">${trn(p.entry_trigger,1)}→${trn((p.targets&&p.targets[0]),1)}</span>
    <span class="mono-num">${p.r_multiple_expected??'—'}R</span>
    <span style="text-align:right"><span class="tag ${TAG[v]||''}">${v}</span>${onayRozeti(p)}${p.p_win_shadow!=null?`<span class="reason" style="display:block" title="Gölge model kanıtı — karar yetkisi yok, kalibre olana dek yalnız gösterge">gölge P(kazanç) %${Math.round(p.p_win_shadow*100)}</span>`:''}${(p.gate_reasons||[]).length?`<span class="reason" style="display:block">${esc(p.gate_reasons.join(' · '))}</span>`:''}</span></button>`;
}

// ================= ÖĞRENME (ajan) =================
// =============================== HUD — Risk & Müdahale (sticky) ===============================
let _DIAG = null, _nextTickAt = null;
window._LEARN_HALTED = false;
function renderHUD(d) {
  const hud = $("hud"); if (!hud || !d) return;
  const h = d.hud || {}, sch = d.scheduler || {}, io = ((d.pipeline || {}).io) || {};
  const _rj = (d.risk || {}).regime || {};                    // heartbeat eski süreçten boş gelebilir —
  const _regime = h.regime || _rj.regime;                     // rejim/bütçe için regime.json da kaynak
  const _bud = h.exposure_budget_pct != null ? h.exposure_budget_pct : _rj.exposure_budget_pct;
  window._LEARN_HALTED = !!h.learn_halted;
  document.body.classList.toggle("explore-mode", !!h.explore_mode);
  const ks4 = $("ks4"); if (ks4) { ks4.classList.toggle("armed", !!h.learn_halted);
    ks4.textContent = h.learn_halted ? "4 · Halt Learning AKTİF — kaldır" : "4 · Halt Learning — işlem sürer, ship durur"; }
  const ks1 = $("ks1"); if (ks1) { ks1.classList.toggle("armed", !!h.halted);
    ks1.textContent = h.halted ? "1 · Soft Halt AKTİF — DEVAM et" : "1 · Soft Halt — yeni giriş durur"; }
  if (sch.updated && sch.poll_seconds) _nextTickAt = Date.parse(sch.updated) + sch.poll_seconds * 1000;
  const wsCls = h.stream_ok === false ? "bad" : (h.stream_ok ? "" : "off");
  // `h.stream_ok` artık HAM bayrak değil (api.py _stream_view): dinleyici ölünce diskte donan
  // `true` burada "canlı" okunuyordu. Süre de yazılır — bayrak "koptu" der, süre "ne kadar oldu"
  // der; operatörün kararı ikincisine bağlı. Nabız bayatsa nedeni ipucuna (title) girer.
  const wsDown = h.stream_ok === false ? wsDownFor(h) : "";
  // `stream_last_error` GEÇMİŞTİR, durum değil: mirror_stream toparlanınca `down_since`ı siler ama
  // son hatayı BIRAKIR. Koşulsuz basılırsa sağlıklı yeşil çipin ipucunda eski bir kesintinin hatası
  // durur ve okuyan "şu an bozuk" sanar — bu denetimin kovaladığı sınıfın ta kendisi (canlı kanıt
  // 2026-07-22 14:04: nabız 7 sn taze, akış CANLI, ama dosyada hâlâ "bayat bayrak" hatası duruyordu).
  // AKIŞ SAĞLIĞININ YAŞI (K1, 2026-07-30): `stream_checked_age_s` (api._stream_view) servis
  // ediliyordu ama pano onu HİÇ okumuyordu — yani "akış canlı" çipi, o hükmün NE ZAMAN
  // doğrulandığını söylemiyordu. Yeşil bir çipin en tehlikeli hâli, ne kadar eski olduğunu
  // söylemeyen hâlidir (aynı sınıf canlı kanıt: stream_ok=true iken last_event_ts 3 gün eskiydi).
  const _wsAge = h.stream_checked_age_s;
  const wsTip = "WebSocket trade_updates akışı"
    + (_wsAge != null ? ` · sağlık ${Math.round(_wsAge)} sn önce yoklandı` : "")
    + (h.stream_ok === false && h.stream_flag && h.stream_stale
        ? " · diskteki bayrak canlı diyor ama nabzı yok (bayat)" : "")
    + (h.stream_ok === false && h.stream_last_error
        ? ` · ${String(h.stream_last_error).slice(0, 80)}` : "");
  // Yaş çipe de yazılır (yalnız ipucunda kalmaz): 120 sn üstü yoklama, "canlı" hükmünün kendisinin
  // bayatladığı anlamına gelir ve bu ekranda görünmeli.
  const wsAgeTxt = (_wsAge != null && _wsAge >= 120)
    ? ` <span class="mut" style="font-weight:400">(${Math.round(_wsAge / 60)}dk önce yoklandı)</span>` : "";
  const ioBad = io.p95_ms != null && io.p95_ms > 50;
  // Basit modun tek satırlık "genel durum" çipi SİLİNDİ (2026-07-27): statuspill zaten aynı üç
  // durumu (durduruldu / gecikmiş / canlı) söylüyordu, üstelik nabzın YAŞIYLA birlikte. Aynı
  // okumanın sulandırılmış ikinci kopyası, bakılacak yeri çoğaltmaktan başka iş görmüyordu.
  hud.innerHTML = [
    `<span class="hudchip"><b>${esc(h.mode || "?")}</b>·${esc((h.broker || "").replace("alpaca_paper", "alpaca"))}</span>`,
    _regime ? `<span class="hudchip">${esc(REGIME_TR[_regime] || _regime)} · bütçe <b>${_bud != null ? "%" + trn(_bud) : "—"}</b></span>` : "",
    h.explore_mode ? `<span class="hudchip explore">· KEŞİF MODU · ≤0.25R sonda</span>` : "",
    `<span class="hudchip" title="zamanlayıcının bir sonraki döngüsüne kalan"><span class="ld ${sch.updated ? "" : "off"}"></span>döngü <b id="hud-count">${sch.updated ? "…" : "—"}</b></span>`,
    `<span class="hudchip" title="${esc(wsTip)}"><span class="ld ${wsCls}"></span>WS ${h.stream_ok === false ? `<b class='neg'>KOPUK</b>${wsDown ? ` · ${wsDown}` : ""}` : (h.stream_ok ? "canlı" + wsAgeTxt : "—")}</span>`,
    // BEKÇİ ÇİPİ D2-b'DE DÜŞTÜ (P3 tekilleştirmesi · baseline §2). "Bekçiler ne durumda?" İKİ
    // yerde yazılıydı: bu çip (lamba + `ok/total`) ve sessiz hattın `bekçiler` segmenti. İkisi
    // aynı `_wd_rep` nesnesinden besleniyordu ve çip HER ZAMAN konuşuyordu — sağlıklıyken bile.
    // Sessiz hat aynı gerçeği DAHA İYİ taşıyor: sağlıklıyken tek kelime, saparken geciken
    // mekanizmanın ADIYLA, SÜRESİYLE ve artık `teşhis ↗` olay yüzeyiyle birlikte. Ayrıntının
    // tam hâli (on yedi mekanizmanın hepsi, adım adım) ③ Sağlık'ın `cizelge` bölümünde.
    // Askıda hâli de orada adıyla ve nedeniyle duruyor — bu çiple birlikte hiçbir şey düşmedi.
    `<span class="hudchip" title="atomik yazım gecikmesi (son 200 yazım p95)"><span class="ld ${ioBad ? "warn" : ""}"></span>IO <b>${io.p95_ms != null ? trn(io.p95_ms, 1) + " ms" : (io.p50_ms != null ? trn(io.p50_ms, 1) + " ms·p50" : "—")}</b></span>`,
  ].filter(Boolean).join("");
  syncNavHeight();   // rozetler barın yüksekliğini değiştirir; shell dolgusu onu takip etmeli
}
async function pollHUD() {
  try { _DIAG = await j("/api/diagnostics"); renderHUD(_DIAG); } catch (e) { /* statuspill zaten bağlantıyı söylüyor */ }
}
setInterval(() => {                          // yerel saniye tiki — yalnız API zaman damgasından türetilir
  const el = $("hud-count"); if (!el || !_nextTickAt) return;
  const left = Math.round((_nextTickAt - Date.now()) / 1000);
  el.textContent = left > 0 ? left + " sn" : "şimdi…";
}, 1000);
setInterval(pollHUD, 20000); pollHUD();

// =============================== OPERASYON — teşhis paneli ===============================
// Faz 2: /api/diagnostics tek ucundan beslenir. Her satır CANLI; veri yoksa dürüstçe "yok" der.
function _chip(txt, cls) { return `<span class="tag ${cls}">${esc(txt)}</span>`; }

// CANLILIK (dalga-2 `diagnostics.liveness`, KALEM 3) — kadans NABZI "dişli döndü mü" der; canlılık
// "dişlinin ürettiği İŞ yaşıyor mu" der. Sahte-yeşil sınıfının pano yüzü: sprint pid'i ölü + faz
// takılıyken nabız taze kalır, hipotez defteri günlerce donukken kadans her seans nabız atar.
// `watchdog.liveness_report` GERÇEĞİ ölçüp BEYAN eder — bu blok o beyanı çizer (üretmez, uydurmaz).
// ÜÇ HÂL (koştu / koşmadı / ölçülemedi) — bu bir DURUM/sağlık göstergesi, o yüzden SEV JETONU (yön
// DEĞİL) taşır ve RENK YALNIZ ANOMALİDE:
//   ok===true  → canlı  (sessiz/yeşil, t-go)
//   ok===false → anomali (orphan/stall — t-no, dikkat çeker)
//   ok==null   → ÖLÇÜLEMEDİ (t-vi akromatik; 'koşuyor' DEMEZ — ÖLÇÜLEMEDİ≠0, YASA 4)
// Cümle (N-gün sayısı dahil) SUNUCUDAN gelir; pano tarafında sabit sayı yazılmaz (C10 ruhu).
function canlilikBloku(lv) {
  if (!lv) return "";
  const bacak = (etiket, x, anomaliLbl) => {
    if (!x) return "";
    const [lbl, kls] = x.ok == null ? ["ÖLÇÜLEMEDİ", "t-vi"]
      : (x.ok === false ? [anomaliLbl, "t-no"] : ["canlı", "t-go"]);
    return `<div class="srow"><span>${esc(etiket)}</span><b>${_chip(lbl, kls)} <span class="mut" style="font-weight:400">${esc(x.beyan || "")}</span></b></div>`;
  };
  const sp = bacak("sprint canlılığı", lv.sprint, "KOŞMADI");
  const lr = bacak("öğrenme canlılığı", lv.learning, "DURDU");
  if (!sp && !lr) return "";
  return `<h3 class="t" style="margin-top:16px">Canlılık <span class="tx3" style="font-weight:400">(kadans nabzı değil — üretilen iş yaşıyor mu)</span></h3>${sp}${lr}`;
}

// ---- BELİRSİZLİK KODLAMASI (WP-P/P5, 2026-08-01) ---------------------------------------------
// KUSUR SINIFI: bu panoda ONARILMIŞ/SİMÜLE bir hücre ile ölçülmüş bir hücre AYNI mürekkeple
// yazılıyordu. Köken bilgisi vardı (künye `_kaynak`, `n_cf`, `sadakat` şerhleri) ama METİN olarak,
// hücrenin YANINDA değil ALTINDA ya da bir paragraf uzağında. Okuyucu iki sayıyı yan yana gördüğü
// anda ikisine aynı ağırlığı veriyordu — Sarma/Kay'in "belirsizliği gösterimin İÇİNE göm" kuralının
// tam tersi.
//
// RENK KULLANILMAZ ve bu bir kısıt değil bir hüküm: renk bu panoda ÖLÇÜMÜN kanalı (Money Rule).
// Belirsizlik ölçüm değil, ölçümün KÖKENİ hakkında bir şerhtir. Kesikli alt çizgi ayrı bir kanal,
// tek kalınlıkta ve renk körü okuyucuda da çalışıyor.
//
// BEYAN ZORUNLU: `title` olmadan kesik çizgi bir süstür. Beyanı çağıran yazar, çünkü hücrenin
// neden belirsiz olduğunu YALNIZ çağıran bilir (sim dilim mi, onarılmış bar mı, havuz mu).
function belirsiz(icerik, beyan) {
  return `<span class="belirsiz" title="${esc(beyan)}">${icerik}</span>`;
}

// ---- İLERİ-DOLDURMA İŞARETİ (v196/KALEM-2 · BASELINE-2026-08-06 T12) --------------------------
// ÖLÇÜLEN KUSUR: `trend_shadow.py`nin ffill'i (sıralama penceresi) ve `_isaretle`in
// son-bilinen-kapanış taşıması EKRANA ULAŞIYORDU (`api.py` → `trend_kitabi` → Öğrenme#gölge), ama
// web katmanında "dolduruldu"/"ffill"/"ileri taşındı" dizesi SIFIR kez geçiyordu. Yani ileri
// taşınmış bir kapanışla ölçülmüş bir kapanış AYNI MÜREKKEPLE yazılıyordu. Design rules:
// *"Null renders as an explicit gap with a reason — never interpolated."* Doldurmanın kendisi
// meşru ve şasiyle birebir aynı semantik; ETİKETSİZ olması değildi.
//
// YENİ DİL AÇILMADI: işaret, P5'in MEVCUT belirsizlik kanalıdır (`belirsiz()` — kesik alt çizgi +
// ZORUNLU beyan) ve panonun MEVCUT `_chip` rozetidir (`t-vi`: akromatik "hüküm yok" jetonu).
// RENK YOK ve bu bir kısıt değil bir hüküm — `belirsiz()`in kendi gerekçesi: renk bu panoda
// ÖLÇÜMÜN kanalı; doldurma bir ölçüm değil, ölçümün KÖKENİ hakkında bir şerhtir.
//
// SÖZLEŞME (test edilir): DOLDURULMUŞ değer işaret TAŞIR, doldurulmamış TAŞIMAZ. Üçüncü hâl
// (kaynakta bayrak yok → doldurma ÖLÇÜLEMEZ) rozetle SÖYLENİR; sessizce "doldurulmadı" sayılmaz,
// çünkü o katlama tam olarak ÖLÇÜLEMEDİ≠0 yasasının ihlalidir.
function _dolduruldu(icerik, n) {
  if (n == null) return `${icerik} ${_chip("DOLDURMA ÖLÇÜLEMEDİ", "t-vi")}`;
  if (!n) return icerik;                      // ölçüldü, taşıma yok — TEMİZ HÜCREYE SÜS BASILMAZ
  return belirsiz(icerik, `İLERİ DOLDURULDU: bu seansta ${n} pozisyonun kendi barı yoktu; değer `
    + `SON BİLİNEN KAPANIŞLA taşındı (şasi ffill'i, trend_shadow._isaretle) — ölçülmüş bir kapanış değil.`)
    + " " + _chip("İLERİ DOLDURULDU", "t-vi");
}
// Eğrinin TAMAMI için doldurma muhasebesi. Tek hücrenin bayrağı "bu sayı taşındı mı" der; bu satır
// "defterin ne kadarı taşımayla yürüdü" der — ikisi ayrı soru ve ikisi de rakamın yanında durmalı.
function _dolduranSeanslar(tk) {
  const g = tk.dolduruldu_gun, o = tk.dolduruldu_olcumsuz, k = tk.karar_dolduruldu;
  if (g == null && o == null) return "";      // uç bu alanları servis etmiyor — satır UYDURULMAZ
  return `<div class="srow"><span>İleri doldurulan seans</span><b class="mono-num">${
    g == null ? '<span class="mut">ölçülemedi</span>' : `${trn(g)} seans`}${
    o ? ` <span class="mut">· ${trn(o)} satır bayraktan önce yazıldı — doldurma ÖLÇÜLEMEZ</span>` : ""}${
    k != null ? ` <span class="mut">· bekleyen kararın sıralama penceresinde ${trn(k)} doldurulmuş hücre</span>` : ""}</b></div>`;
}

// ---- BAYATLIK SOLMASI (WP-P/P5) --------------------------------------------------------------
// ÜÇ KADEME, EŞİKLER BURADA VE TEK YERDE. Opaklık NİCELİK TAŞIMAZ: "%58 opak = 4 gün eski" diye
// bir okuma yoktur ve olmamalı — solma yalnız "bu satır eskiyor" der, YAŞIN KENDİSİ metin olarak
// zaten yazılı (tarih hücrede duruyor). Sayı hiçbir kademede gizlenmez ve değişmez.
// GÜN SINIRLARI: 1 gün = önceki seans (hafta sonu normaldir) · 3 gün = uzun hafta sonu sınırı ·
// 7 gün = bir haftadır bar gelmiyor. Aynı takvim gerçekçiliği watchdog.EXPECTED'de de var.
const BAYAT_ESIK_GUN = [1, 3, 7];
function bayatSinif(tarih, referans) {
  if (!tarih || !referans) return "";           // ölçülemeyen bayatlık SOLDURULMAZ (uydurma yasağı)
  const t = Date.parse(String(tarih)), r = Date.parse(String(referans));
  if (!Number.isFinite(t) || !Number.isFinite(r)) return "";
  const gun = (r - t) / 86400000;
  if (gun < BAYAT_ESIK_GUN[0]) return "";
  if (gun < BAYAT_ESIK_GUN[1]) return " bayat-1";
  if (gun < BAYAT_ESIK_GUN[2]) return " bayat-2";
  return " bayat-3";
}

// ---- SESSİZ HAT (WP-P/P1, 2026-08-01) --------------------------------------------------------
// LEVEL-1 TOPLAMA. Üç sağlık yüzeyi (bekçi · kilit · tazelik) bu turdan önce ÜÇ AYRI yerde ve
// SAĞLIKLIYKEN DE konuşuyordu: HUD'da bekçi rozeti, statuspill'de nabız, Bölüm 1'de akış satırı.
// Sürekli konuşan bir gösterge sapma anında ses değiştiremez — toplama, alarm yorgunluğuna karşı
// kurulmuş tek yapısal savunmadır (ISA-101/HP-HMI Level-1; klinik alarm literatürüyle aynı bulgu).
//
// HÜKÜM PANODA KURULMAZ: hangi segmentin saplandığı, sapmanın SÜRESİ ve runbook ipucu sunucudan
// (`api._sessiz_hat`) gelir. Burada ikinci bir eşik hesabı olsaydı aynı gerçeğin iki metni doğardı
// ve biri sessizce bayatlardı — bu deponun tekrar eden kusur sınıfı.
//
// AÇILIMDA TAVAN VAR (4 satır): 11 bekçi birden geciktiğinde şerit bir listeye dönüşür ve Level-1
// olmaktan çıkar. Kalan sayı YAZILIR ("+7 daha") — kırpma sessiz olamaz.
const SH_ACILIM_TAVAN = 4;
// ---- ASKIDA DALI (v195-a · B6/Ö7 · YASA 6) ---------------------------------------------------
// ÖLÇÜLEN BOŞLUK: `api._sessiz_hat` bekçi segmentine `askida` ve `n_askida` YAZIYOR (v192) ama
// `sessizHat()` YALNIZ `sapmalar`/`n_sapma` okuyordu. Şerit "bekçiler 15/17" diyor, eksik ikinin
// nedeni yalnız HUD çipinin `title` ipucunda duruyordu: hover-only, klavyeyle erişilemez, ekran
// okuyucuya kapalı. Üretilen bir alanın okuyucusu yok = YASA 6.
//
// ASKIDA SAPMA DEĞİLDİR VE SAPMA SAYILMAZ: şeridin hâli (`ok`/`sap`), `kritik` bayrağı ve
// `n_sapma` sayımı bu daldan ETKİLENMEZ. Meşru bir beklemeyi (hermes kota soğuması, kimlik
// havuzu tükenmesi) alarm rengine çevirmek, hattın var oluş sebebi olan alarm-hijyenini bozardı.
// Satır sönük, tam genişlikte ve ADIYLA+NEDENİYLE yazılır; nedeni okunamıyorsa bunu söyler.
function _shAskidaSatiri(segmentler) {
  const hepsi = [];
  let toplam = 0;
  for (const s of segmentler || []) {
    const l = s.askida || [];
    if (!l.length && !s.n_askida) continue;
    toplam += (s.n_askida ?? l.length);
    for (const a of l) hepsi.push(a);
  }
  if (!toplam) return "";
  const gosterilen = hepsi.slice(0, SH_ACILIM_TAVAN);
  const kalan = toplam - gosterilen.length;
  const parca = gosterilen.map(a => `<b>${esc(a.ad ?? "?")}</b> ${
    esc(a.neden || a.detay || "neden bildirilmedi")}${a.sure ? ` · ${esc(a.sure)}` : ""}`);
  // AÇILIM TAVANI SESSİZ KIRPMAZ (şeridin mevcut kuralı): kalan sayı yazılır.
  return `<span class="sh-seg sh-ask">${toplam} askıda${
    parca.length ? " · " + parca.join(" · ") : " — ad/neden uçtan gelmedi"}${
    kalan > 0 ? ` · +${kalan} daha` : ""}</span>`;
}
// ---- RUNBOOK BAĞI (UIUX S1-T3) — D2-b'DE EMEKLİ ---------------------------------------------
// `runbookHref`/`runbookLink` SİLİNDİ, taşındığı için. İkisi de `/runbook#<ad>` üretiyordu ve o
// sayfa artık panonun İÇİNE emildi (aşağıdaki olay yüzeyleri). Bir bağ, hedefi "içerik buradan
// taşındı" diyen bir yönlendirmeye çıkıyorsa artık bir adres değil bir dolambaçtır — okuyucusu
// kalmamış bir fonksiyonu bırakmak da YASA 6 ihlali olurdu. Halefi: `olayBagi(ad, sınıf, segment)`.
// Çapa kuralının kendisi (ad = küçük harfli jeton) `olaySinifi()` içinde korunuyor.

// ==============================================================================================
// OLAY YÜZEYLERİ (Tier-4, D2-b) — `runbook.html` PANOYA EMİLDİ
// ----------------------------------------------------------------------------------------------
// ÖLÇÜLEN KUSUR (denetim B14 + baseline §3.3): alarmdan teşhise giden yol PANOYU TERK EDİYORDU.
// `runbookLink` bir <a href="/runbook#…"> idi; basan operatör dördüncü bir görsel dünyaya
// (kendi jetonları, Roboto, ölçülen 3,50:1 kontrast) düşüyor, panonun canlı değerlerini
// ARKASINDA bırakıyordu. Yani "ne oldu" bir sayfada, "değerler şimdi ne" başka sayfada,
// "ne yapmalıyım" üçüncü yerdeydi — üstelik operatörün en tedirgin olduğu anda.
//
// OLAY YÜZEYİ BİR SAYFA DEĞİLDİR: herhangi bir alarmdan açılan TAM ÇEKMECEdir ve DÖRT bölümü
// tek yerde taşır — (1) ne oldu · (2) değerler ŞİMDİ ne · (3) runbook adımları · (4) mevcut
// eylemler. Yeni bileşen İCAT EDİLMEDİ: aynı `openDrawer` deseni, aynı odak tuzağı, aynı Esc
// sözleşmesi (v191'in `RECORD_VIEW` kararının birebir tekrarı).
//
// UYDURMA YASAĞI BURADA EN SERT UYGULANIR. Adımlar `docs/RUNBOOK.md`den EMİLDİ ve o belge çoğu
// jeton için "runbook girdisi henüz yazılmadı" diyor — bu yüzey o boşluğu DOLDURMAZ, ADIYLA
// yazar. Bir olay yüzeyinin bilmediği bir çözümü varmış gibi davranması, olay anında
// yapılabilecek en pahalı yalandır.
//
// TEK EMİR-YOLU KORUNUR: "mevcut eylemler" YENİ bir kol açmaz. Hepsi `data-act="go"` ile
// kolun/masanın GERÇEKTEN yaşadığı bölüme götürür. Çekmeceye bir HALT düğmesi koymak, panoda
// ikinci bir emir yüzeyi açmak olurdu.
const OLAY_YUZEYLERI = {
  besleme: {
    ad: "Besleme kopuk / bayat",
    ozet: "Nabız ya da periyodik bir mekanizma penceresini aştı — sistem ölçüyor mu, ölçmüyor mu?",
    jetonlar: ["HEARTBEAT_STALE", "MECHANISM_STALE"],
    neOldu: "Bir mekanizma beklenen sessizlik penceresini aştı. Bekçi (`meridian/watchdog.py`) " +
            "YALNIZ GÖZLEMDİR: hiçbir mekanizmayı yeniden başlatmaz, hiçbir kararı etkilemez — " +
            "penceresi aşılınca sessiz hattın <b>bekçiler</b> segmenti açılır ve MECHANISM_STALE " +
            "ateşlenir. Nabız defteri: <code>state/mechanism_beats.json</code> (ad → son damga).",
    kaynak: "meridian/obs.py · meridian/watchdog.py::EXPECTED",
    degerler: d => {
      const wd = (d || {}).watchdog || {}, sch = (d || {}).scheduler || {};
      const st = wd.stale || [], nv = wd.never || [], ask = wd.askida || [];
      return [
        ["Penceresinde", wd.ok == null ? null : `${wd.ok}/${wd.total ?? "—"} mekanizma`],
        ["Geciken", st.length ? st.map(x => `${x.name} · ${trn(x.gap_h, 1)}sa (pencere ${trn(x.expected_h, 1)}sa)`).join("<br>") : (st.length === 0 ? "yok" : null)],
        ["Hiç koşmamış", nv.length ? nv.join(", ") : "yok"],
        ["Askıda (beyanlı)", ask.length ? ask.map(a => `${a.name} · ${esc(a.neden || a.detay || "neden bildirilmedi")}`).join("<br>") : "yok"],
        ["Zamanlayıcı son tur", sch.updated ? `${String(sch.updated).slice(11, 19)} · her ${sch.poll_seconds ?? "—"} sn` : null],
      ];
    },
    adimlar: [
      "Hangi mekanizmanın konuştuğu yukarıdaki <b>Geciken</b> satırında ADIYLA yazılı — bekçi raporu adı ve gecikmeyi birlikte verir.",
      "Askıdaki bir mekanizma ne OK'tir ne alarmlıktır: sistemin kendi beyanıyla beklemeye alınmıştır ve nedeni satırında durur.",
      "Kaydın tamamı: alarm satırına bas → çekmece; diskte <code>state/events.jsonl</code>.",
    ],
    cozum: null,
    eylemler: [["Gece hattının çizelgesi →", "saglik#cizelge"],
               ["Alarm gelen kutusu →", "saglik#operasyon"]],
  },
  mutabakat: {
    ad: "Mutabakat çatışması",
    ozet: "İç defter ile brokerin defteri aynı şeyi söylemiyor — hayalet, sapma, ret, PATCH reddi ya da korumasız pozisyon.",
    // NAKED_POSITION BU YÜZEYE ÖLÇÜMLE GELDİ (v219, 2026-08-09). W1'e (5df1657) kadar korumasız-
    // pozisyon alarmı MIRROR_DRIFT jetonunu ÖDÜNÇ alıyordu — yani olgu ZATEN bu yüzeyde yaşıyordu
    // ve jeton ayrılınca yüzeysiz kaldı (v154 parite testi bunu yakaladı). Kendi bölümünü açmak
    // olguyu taşıdığı masadan koparırdı: teşhis kartı (`mutabakat:koruma`) mutabakat masasında,
    // `karar#mutabakat` altında duruyor ve aşağıdaki "Mutabakat masası" eylemi zaten oraya gidiyor.
    // İCRA-SÖZLEŞMESİ (2026-08-12, v233 — VLO vakası): ONAYLI_PLAN_GONDERILMEDI de bu masada —
    // olgu ayna-gönderim olgusudur (onaylı plan broker'a ulaşmadı); MIRROR_DRIFT'ten AYRI jeton
    // olması split_brain gürültüsüne gömülmemesi için (obs.py:71 gerekçesi), yüzeyi aynı mutabakat masası.
    jetonlar: ["MIRROR_DRIFT", "BROKER_REJECT", "TRAIL_DESYNC", "NAKED_POSITION", "ONAYLI_PLAN_GONDERILMEDI"],
    neOldu: "İç sim dolumu ile gerçek Alpaca dolumu toleransın ötesinde ayrıştı (MIRROR_DRIFT), " +
            "broker iç defterin yürüteceği bir emri reddetti (BROKER_REJECT) ya da takip-stop " +
            "PATCH'i reddedildi ve iç HWM ile broker stopu ayrıştı (TRAIL_DESYNC). " +
            "MIRROR_DRIFT'i <b>altı</b> kod yolu ateşliyor (ayna çıkışı kapatılamadı · ayna " +
            "pozisyonu kayıp · adet sapması · motor yetimi · çıkış yetimi · dolum sapması); " +
            "hangisinin konuştuğu olay kaydındaki <code>detail</code> alanından okunur. " +
            "<b>NAKED_POSITION</b> bu ailenin en pahalı hâlidir: açık bir motor pozisyonunun " +
            "broker'da CANLI koruyucu stop'u yok — iç defter 'korunuyor' der, broker demez. " +
            "İki ayrı olguyu taşır ve <code>kind</code> alanı onları ayırır: " +
            "<code>korumasiz_pozisyon</code> (ölçtük, koruma YOK) ile " +
            "<code>koruma_olculemedi</code> (broker okunamadı — bu 'korumasız 0' DEĞİL). " +
            "Jeton W1'e kadar MIRROR_DRIFT'ten ÖDÜNÇTÜ ve ödüncün bedeli ölçülmüştü: susturma " +
            "penceresi jeton başınadır, yani gürültülü bir adet-sapması gecesi bir sermaye " +
            "riskinin teslimatını bastırabiliyordu.",
    kaynak: "meridian/obs.py · meridian/loop.py · meridian/mirror_stream.py · meridian/watchdog.py::check_koruma_and_alarm",
    degerler: d => {
      const rc = (d || {}).reconcile || {}, fs = rc.failed_submissions || {};
      const sure = wsDownFor(rc);
      return [
        ["Broker API", rc.api_ok == null ? null : (rc.api_ok ? "erişilebilir" : "ERİŞİLEMİYOR")],
        ["Yürütme akışı", rc.stream_ok == null ? null
          : (rc.stream_ok ? "canlı" : `KOPUK${sure ? ` · ${esc(sure)}` : ""}`)],
        ["Hayalet emir", (rc.ghosts || []).length ? (rc.ghosts || []).map(g => esc(g.symbol || "?")).join(", ") : "yok"],
        ["Açık broker reddi", (fs.open || []).length || "yok"],
        ["Motor yetimi", ((rc.positions || {}).engine_orphans || []).length || "yok"],
        ["Force-sync (bu tur)", (rc.force_sync || {}).stripped == null ? null
          : `strip ${rc.force_sync.stripped} · PATCH ${rc.force_sync.trail_patched ?? 0}`],
      ];
    },
    adimlar: [
      "Sapmanın hangi kod yolundan geldiği olay kaydının <code>detail</code> alanındadır — alarm satırının çekmecesi tam kaydı taşır.",
      "Hayalet emir = Alpaca'da canlı ama yerel izi (armed/submitted/mirror) olmayan emir; masadaki dedektör onları adıyla listeler.",
      "Ret defteri KALICI retleri taşır; ağ arızası ve gönderim bacağının kendi istisnası o deftere HİÇ girmez — onlar yalnız olay akışında görünür.",
      "Korumasız pozisyonun sayıları YUKARIDA DEĞİL, mutabakat masasındaki <b>Koruma · çıplak pozisyonlar</b> kartındadır: bu çekmece teşhis paketini okur, koruma ölçümü ise ayrı ve TAZE bir uçtan gelir (<code>/api/alpaca/koruma</code>) — 45 sn önbellekli bir sayıyı sermaye riski diye göstermek, eskimiş bir güvence cümlesi yazmak olurdu.",
      "O karttaki \"korumasız 0\" bir GÜVENCE cümlesidir ve yalnız ölçüm döndüyse yazılır; broker okunamadıysa kart ÖLÇÜLEMEDİ der ve hiçbir emir üretilmez.",
    ],
    cozum: null,
    eylemler: [["Mutabakat masası →", "karar#mutabakat"],
               ["Reddedilen emir kaydı →", "karar#failsub"]],
  },
  kill: {
    ad: "Kill-switch tetiklendi",
    ozet: "Bir durdurma kolu çekildi ya da kendiliğinden tetiklendi — yeni alım yolu kapalı.",
    jetonlar: ["HALT_ACTIVE", "CIRCUIT_BREAKER", "ROLLBACK"],
    neOldu: "HALT_ACTIVE panodan çekilen acil durdurmadır (<code>meridian/api.py</code> — " +
            "\"HALT via dashboard\"); CIRCUIT_BREAKER günlük kayıp devre kesicisidir; ROLLBACK " +
            "bir sürümün geri alınmasıdır. Üçünün ortak sonucu aynı: yeni alım yapılmaz, " +
            "mevcut açık pozisyonlar yönetilmeye devam eder.",
    kaynak: "meridian/obs.py · meridian/api.py · meridian/health.py",
    degerler: (d, t) => {
      const hb = (t || {}).heartbeat || {}, rc = (d || {}).reconcile || {};
      return [
        ["HALT", (t || {}).halted == null ? null : ((t || {}).halted ? "ÇEKİLİ" : "serbest")],
        ["Devre kesici", hb.breaker_tripped == null ? null : (hb.breaker_tripped ? "TETİKLİ" : "tetiklenmedi")],
        ["Öğrenme durdurma", rc.learn_halted == null ? null : (rc.learn_halted ? "ÇEKİLİ" : "serbest")],
        ["Veri kalitesi kapısı", (t || {}).data_ok == null ? null : ((t || {}).data_ok ? "açık" : "KAPALI — bugün yeni alım yok")],
        ["Otonomi", (t || {}).autonomy_level == null ? null : onk("L", (t || {}).autonomy_level)],
      ];
    },
    adimlar: [
      "Kolun kim tarafından ve ne zaman çekildiği olay defterindedir — panodaki olay akışı satırı kaydın tamamını açar.",
      "HALT geri alınabilir (üst bardaki DEVAM); kademe 3 (flatten) GERİ ALINAMAZ ve kendi onay kapısını taşır.",
      "Devre kesici kendiliğinden tetiklenir: geri açmadan önce günün kayıp nedenini okumak, kolu geri itmekten önce gelir.",
    ],
    cozum: null,
    eylemler: [["Müdahale kademeleri →", "kilitler#mudahale"],
               ["Kitap · şu an →", "karar#brifing"]],
  },
  butunluk: {
    ad: "Bütünlük ihlali",
    ozet: "Veri ya da defter kendi sözleşmesini çiğnedi: sessiz mutasyon, gerileme, ezilen alan, kaynak uyuşmazlığı.",
    jetonlar: ["DATA_QUALITY", "GOAL_FAILURE"],
    neOldu: "DATA_QUALITY'yi <b>on üç</b> kod yolu ateşliyor; en sertleri bütünlük " +
            "dedektörlerinden gelir: <b>SESSİZ BAR MUTASYONU</b> (bar determinizmi), " +
            "<b>GERİLEME</b> (ileri-only olması gereken bir alan geri gitti), <b>ALAN EZİLDİ</b> " +
            "(bir kez dolu olan alan şimdi kayıp), <b>BAR KAYNAK UYUŞMAZLIĞI</b> (iki sağlayıcı " +
            "aynı kapanışta anlaşmıyor), <b>SEANS ATLANDI</b>. GOAL_FAILURE ayrı bir sınıftır: " +
            "mekanizma çalıştı ve sonuç sözleşmenin başarısızlık eşiğinin altında " +
            "(<code>goal.yaml::failure_below</code>).",
    kaynak: "meridian/obs.py · meridian/watchdog.py · meridian/adapters/data.py · meridian/loop.py",
    degerler: d => {
      const pl = (d || {}).pipeline || {}, wd = (d || {}).watchdog || {};
      const kar = pl.quarantine || [];
      const rep = wd.conservation_report || {};
      return [
        ["Karantina", kar.length ? kar.join(", ") : "boş"],
        ["Son başarılı tazeleme", pl.last_refetch_session || null],
        ["Tazeleme sabrı", pl.refetch_attempts == null ? null : `${pl.refetch_attempts}/${pl.refetch_max ?? 8} deneme`],
        ["cf sadakati (sim↔gerçek)", pl.cf_fidelity ? `r=${pl.cf_fidelity.corr ?? "—"} · n=${pl.cf_fidelity.n ?? "—"}` : null],
        ["Muhafaza raporu", rep.unexplained == null ? null : `açıklanamayan ${rep.unexplained}`],
      ];
    },
    adimlar: [
      "Hangi dedektörün konuştuğu olay kaydının <code>detail</code> alanındadır; bütünlük bölümü aynı dedektörleri satır satır listeler.",
      "Karantinaya alınan sembol o seans HİÇ işlem üretmez — boş bir aday listesi bu yüzden bir arıza değil bir SONUÇ olabilir.",
      "ÖLÇÜLEMEDİ ile İHLAL aynı şey değildir: bekçinin <code>olculemedi</code>/<code>detector_failed</code> hâlleri ihlal diye okunmaz.",
    ],
    cozum: null,
    eylemler: [["Veri hattı · bütünlük →", "saglik#veriboru"],
               ["İzlenen evren →", "saglik#market"]],
  },
  yetki: {
    ad: "Yetki değişimi / silahlanma kararı",
    ozet: "Bir mekanizmanın yetkisi açıldı-kapandı ya da silahlanma eşiği karşılandı: karar SENDE.",
    jetonlar: ["ARMING_READY", "AUTHORITY_CHANGE"],
    neOldu: "ARMING_READY: silahlanma eşiği karşılandı ve operatör kararı bekleniyor. " +
            "AUTHORITY_CHANGE: bir mekanizmanın yetkisi açıldı ya da geri alındı. İkisi de bir " +
            "ARIZA DEĞİL bir KARAR ÇAĞRISIDIR — bu yüzden şiddet dili taşımaz ve kendi sınıfında durur.",
    kaynak: "meridian/obs.py",
    degerler: (d, t) => [
      ["Bekleyen onay", (t || {}).inbox_count == null ? null : (t || {}).inbox_count],
      ["Kurulan plan", (t || {}).pending_count == null ? null : (t || {}).pending_count],
      ["Silahlı emir", ((t || {}).armed_plans || []).length],
      ["Otonomi", (t || {}).autonomy_level == null ? null : onk("L", (t || {}).autonomy_level)],
    ],
    adimlar: [
      "Silahlanma eşiğinin hangi ölçümle karşılandığı onay kuyruğundaki kaydın içindedir — karar satırı kendi kanıtını taşır.",
      "Yetki değişimi bir OLAYDIR ve geri alınabilir; hangi mekanizmanın yetkisinin değiştiği olay kaydında adıyla yazılıdır.",
    ],
    cozum: null,
    eylemler: [["Onay kuyruğu →", "karar#onaylar"],
               ["Otonomi ve sınırlar →", "kilitler#ayarlar"]],
  },
  kota: {
    ad: "Ajan / beyin kotası",
    ozet: "Düşünen beyin bütçesini ya da çağrı kotasını doldurdu — öneri hattı daralır, kapı değişmez.",
    // JETONU YOK ve bu BEYAN EDİLİR: sınıf bir alarm jetonundan değil, teşhis ucunun ölçtüğü
    // kota alanlarından doğuyor. Boş bir liste burada bir eksik değil, bir ölçüm sonucudur.
    jetonlar: [],
    neOldu: "Ajan çağrı bütçesi (RPM/RPD) ya da LLM harcama bütçesi doldu. Bu bir ARIZA değildir: " +
            "kapı hiçbir koşulda LLM'e bağlı değildir ve beyin yalnız ÖNERİR/SIRALAR. Sonucu " +
            "şudur — ikinci görüş ve keşif sıralaması o tur için gelmez; kararlar deterministik " +
            "kapının kendi ölçütleriyle alınmaya devam eder.",
    kaynak: "meridian/hermes.py (AGENT_RPM / AGENT_RPD) · state/agent_budget.json",
    degerler: d => {
      const ml = (d || {}).mlops || {}, ac = ml.agent_calls || {};
      return [
        ["Çağrı kotası", ac.rpm_limit == null ? null : `${ac.rpm_limit}/dk · ${ac.rpd_limit ?? "—"}/gün`],
        ["Bugünkü çağrı", ac.day == null ? null : ac.day],
        ["Bütçe günü", ac.date || null],
        // ALAN ADLARI DÜZELTİLDİ (v242, 2026-08-13). Bu satır `ok`/`total` okuyordu; `agent_skill_coverage()`
        // (hermes.py) ise `{enabled, linked, missing, stale_linked}` döndürüyor — yani ikisi de `undefined`di
        // ve satır DOĞUŞUNDAN BERİ hep "—" gösteriyordu. Sessizce boş bir ölçüm satırı, ölçümün YOKLUĞUNDAN
        // beter: operatöre "baktım, veri yok" dedirtir. Aynı gövdeyi doğru okuyan ikinci bir yüzey zaten
        // vardı (aşağıda "Ajan skill kapsamı" satırı, `ag.linked`/`ag.enabled`) — iki yüzey ayrışmıştı.
        ["Beceri kapsaması", (ml.agent_skills || {}).enabled == null ? null
          : `${ml.agent_skills.linked ?? "—"}/${ml.agent_skills.enabled}`],
      ];
    },
    adimlar: [
      "Bütçenin dolduğu tur, sprint/yoklama satırında görünür; harcamanın kırılımı beyin bölümündedir.",
      "Kota dolduğunda pano SUSMAZ: öneri gelmediği tur, kararın kapıdan geldiğini söyleyen satır yerinde kalır.",
    ],
    cozum: null,
    eylemler: [["Düşünen beyin · sprint →", "ogrenme#hermes"],
               ["Ajan telemetrisi →", "ogrenme#ajan"]],
  },
};
// JETON → SINIF: TÜRETİLİR, elle yazılmaz. İkinci bir liste ilk düzenlemede ayrışırdı ve bir
// alarm jetonu iki yüzeye birden düşerdi (ya da hiçbirine — sessiz kayıp).
const OLAY_JETON = (() => {
  const m = {};
  for (const [sinif, y] of Object.entries(OLAY_YUZEYLERI))
    for (const j of y.jetonlar) m[j] = sinif;
  return m;
})();
// SESSİZ-HAT SEGMENTİ → SINIF. Segment adları `api.py::_sessiz_hat`ın kendi adlarıdır
// (bekçiler · kilitler · veri) ve sapma adları o segmentin İÇİNDEN gelir (mekanizma adı,
// `nabız`, `veri_kalitesi`, `devre_kesici`). Ad-düzeyi istisnalar önce bakılır.
const OLAY_AD_ESLEME = { "nabız": "besleme", "veri_kalitesi": "butunluk", "devre_kesici": "kill" };
const OLAY_SEGMENT = { "bekçiler": "besleme", "kilitler": "kill", "veri": "butunluk" };
// ÇÖZÜMLEME TEK YERDE. Eşleşmeyen bir ad SESSİZCE bir yüzeye ATANMAZ — `null` döner ve çağıran
// dürüst "sınıfı yok" hâlini çizer. Yanlış bir olay yüzeyi, hiç olay yüzeyi olmamasından pahalıdır.
function olaySinifi(ad, segment) {
  const a = String(ad ?? "");
  if (OLAY_YUZEYLERI[a]) return a;
  if (OLAY_AD_ESLEME[a]) return OLAY_AD_ESLEME[a];
  if (OLAY_JETON[a.toUpperCase()]) return OLAY_JETON[a.toUpperCase()];
  if (segment && OLAY_SEGMENT[segment]) return OLAY_SEGMENT[segment];
  return null;
}
// ---- ÇEKMECE GÖVDESİ — DÖRT BÖLÜM, HEP AYNI SIRA ---------------------------------------------
// Sıra bir sözleşmedir: ne oldu → değerler ŞİMDİ → runbook adımları → mevcut eylemler. Operatör
// olay anında aynı yerde aynı şeyi bulmalı; sıranın olaydan olaya değişmesi, aramayı her seferinde
// baştan başlatırdı.
function olayYuzeyiHTML(sinif, ad) {
  const y = OLAY_YUZEYLERI[sinif];
  if (!y) return null;
  const d = _DIAG || {}, t = SUMMARY || {};
  // DEĞERLER ŞİMDİ: `null` = ÖLÇÜLEMEDİ ve nedeni yazılır (0 DEĞİL). Satırın kendisi düşmez —
  // düşseydi "bu alan yok" ile "bu alan ölçülemedi" aynı görünürdü.
  let satirlar = [];
  try {
    satirlar = (y.degerler ? y.degerler(d, t) : []) || [];
  } catch (e) {
    // YASA 4: yutma yok. Şekil beklenmedikse çekmece bunu yazar ve konsola düşer.
    console.error("olay yüzeyi · değer okunamadı:", sinif, e);
    satirlar = [["Değerler", null]];
  }
  const olculdu = _DIAG ? "" : `<p class="hint">Teşhis paketi bu oturumda HİÇ çekilmedi — aşağıdaki
    satırlar boş değil, <b>ölçülmedi</b>. Sağlık yüzeyi bir kez çizildiğinde dolar.</p>`;
  const degerHTML = satirlar.map(([et, v]) => pdRow(esc(et), v == null
    ? `<span class="mut">ölçülemedi — teşhis ucu bu alanı vermedi</span>` : v)).join("");
  const adimHTML = (y.adimlar || []).map(s => `<li>${s}</li>`).join("");
  const eylemHTML = (y.eylemler || []).map(([et, adres]) =>
    `<button class="dlbtn" type="button" data-act="go" data-a1="${esc(adres)}">${esc(et)}</button>`).join(" ");
  return {
    eyebrow: "OLAY YÜZEYİ",
    title: `${esc(y.ad)}${ad && ad !== sinif ? ` <span class="mut">×</span> ${esc(String(ad))}` : ""}`,
    body: `<p class="hint" style="margin-top:0">${esc(y.ozet)}</p>
      <h3 class="pd-sub">1 · Ne oldu</h3>
      <p>${y.neOldu}</p>
      <p class="hint">kaynak: <code>${esc(y.kaynak)}</code>${
        y.jetonlar.length ? ` · jeton: ${y.jetonlar.map(j => `<code>${esc(j)}</code>`).join(" · ")}`
                          : " · bu sınıfın kendi alarm jetonu YOK — ölçümden doğar"}</p>
      <h3 class="pd-sub">2 · Değerler şimdi ne</h3>
      ${olculdu}${degerHTML}
      <h3 class="pd-sub">3 · Runbook adımları</h3>
      <ul class="pd-adim">${adimHTML}</ul>
      ${y.cozum
        ? `<p>${y.cozum}</p>`
        : `<p class="pd-warn">Çözüm/betik girdisi <b>henüz yazılmadı</b> — onaylı kaynaklarda
             (betik başlıkları · mühendislik günlüğü) bu sınıfın adı literal olarak geçmiyor.
             Eşleşme iddiası olmadan yön verilmez; hüküm operatöründür. <span class="mut">(Bu
             satır <code>docs/RUNBOOK.md</code>in kendi beyanıdır, panonun bir eksiği değil.)</span></p>`}
      <h3 class="pd-sub">4 · Mevcut eylemler</h3>
      <p class="hint">Yeni bir kol AÇILMAZ: aşağıdakiler kolun/masanın gerçekten yaşadığı bölüme
        götürür (tek emir-yolu sözleşmesi).</p>
      <div style="margin-top:10px;display:flex;gap:8px;flex-wrap:wrap">${eylemHTML}</div>`,
  };
}
// TEK KAPI. `ad` bir alarm jetonu, bir sessiz-hat sapma adı ya da doğrudan bir sınıf kimliği
// olabilir; `segment` yalnız sessiz-hattan gelirken dolu olur.
window.olayAc = (ad, segment) => {
  const sinif = olaySinifi(ad, segment);
  const v = sinif && olayYuzeyiHTML(sinif, ad);
  if (v) return openDrawer({ eyebrow: v.eyebrow, title: v.title, bodyHTML: v.body });
  // DÜRÜST BOŞLUK: sınıfı olmayan bir ad için uydurma bir yüzey açılmaz. Ne bilindiği yazılır.
  openDrawer({
    eyebrow: "OLAY YÜZEYİ",
    title: `${esc(String(ad ?? "—"))} <span class="mut">×</span> sınıfı yok`,
    bodyHTML: `<p class="pd-warn">Bu ad için yazılmış bir olay yüzeyi <b>yok</b>: jeton
        haritasında (${Object.keys(OLAY_JETON).length} jeton) ve sessiz-hat eşlemesinde karşılığı
        bulunamadı.</p>
      <p class="mut">Kaydın tamamı yerinde duruyor: alarm satırının kendi çekmecesi ham olayı
        açar, diskte <code>state/events.jsonl</code>.</p>
      <div style="margin-top:14px"><button class="dlbtn" type="button" data-act="go"
        data-a1="saglik#operasyon">Alarm gelen kutusu →</button></div>`,
  });
};
// OLAY BAĞI — `runbookLink`in halefi. Panoyu TERK ETMEZ: aynı çekmeceyi açar.
function olayBagi(ad, sinif, segment) {
  if (!ad) return "";
  const s = olaySinifi(ad, segment);
  return `<button class="${sinif || "rb-link"}" type="button" data-act="olayAc"` +
         ` data-a1="${esc(String(ad))}"${segment ? ` data-a2="${esc(segment)}"` : ""}` +
         ` title="Olay yüzeyi: ${esc(s ? OLAY_YUZEYLERI[s].ad : String(ad))}"` +
         ` style="font-size:11px;color:var(--tx2);background:none;border:0;padding:0;cursor:pointer;` +
         `text-decoration:underline;text-underline-offset:2px;white-space:nowrap">teşhis ↗</button>`;
}
function sessizHat(sh) {
  if (!sh) return "";
  const segler = (sh.segmentler || []).map(s => {
    if (s.saglikli) return `<span class="sh-seg">${esc(s.ad)} <b>${esc(s.ozet ?? "—")}</b></span>`;
    const kalan = (s.n_sapma ?? 0) - (s.sapmalar || []).length;
    const satirlar = (s.sapmalar || []).slice(0, SH_ACILIM_TAVAN).map(x =>
      `<span class="sh-row"><b>${esc(x.ad ?? "?")}</b>${
        x.sure ? ` <span class="sh-sure">${esc(x.sure)}</span>` : ""}${
        x.detay ? ` <span class="sh-ip">· ${esc(x.detay)}</span>` : ""}${
        x.ipucu ? ` <span class="sh-ip">· ${esc(x.ipucu)}</span>` : ""}${
        x.ad ? ` ${olayBagi(x.ad, "sh-rb", s.ad)}` : ""}</span>`).join("");
    return `<span class="sh-seg sh-sap${s.kritik ? " kritik" : ""}">${esc(s.ad)} <b>${esc(s.ozet ?? "—")}</b>
      <span class="sh-ac">${satirlar}${kalan > 0
        ? `<span class="sh-fazla">+${kalan} daha — tam liste bu kartın kendi bölümünde</span>` : ""}</span></span>`;
  });
  // AYIRICI YALNIZ SAĞLIKLI ŞERİTTE: sapan segment kendi bloğunu açtığı için nokta ayırıcı
  // satırın ortasında öksüz kalırdı.
  // ASKIDA SATIRI AYIRICININ DIŞINDA: segment dizisine katılsaydı ardına bir "·" düşerdi ve
  // nokta bir sonraki satırın başında öksüz kalırdı (kendi flex satırını alıyor).
  const govde = (sh.saglikli ? segler.join('<span class="sh-sep">·</span>') : segler.join(" "))
    + _shAskidaSatiri(sh.segmentler);
  // ARIA-LIVE DAR TUTULUR (ROADMAP §WP-P kararı: yalnız kritik alarm/kilit). Sağlıklı şerit
  // `role="status"` TAŞIMAZ — her yeniden çizimde "bekçiler 17/17" diye duyurulan bir satır,
  // görsel tarafta kapatılan gürültünün işitsel kopyası olurdu. Sapma varsa duyurulur.
  return `<div class="sessizhat${sh.saglikli ? " ok" : " sap"}"${
    sh.saglikli ? "" : ' role="status"'} aria-label="${esc(sh.satir || "")}">${govde}</div>`;
}

// ---- ALARM BÜTÇESİ (WP-P/P2) -----------------------------------------------------------------
// EEMUA 191 merceği: üretim HIZI da bir ölçüttür. TON KURALI — uyarı rengi YALNIZ ölçülen bir
// tavan aşıldığında (tepe/10dk ya da duran alarm). Dağılım hedefi (80/15/5) ton TAŞIMAZ: bu
// sistem üç dilimden birini (emergency) üretemiyor, yani hedefe göre "aşım" hükmü kurulamaz.
// Kurulsaydı ölçülemeyen bir şey hakkında hüküm olurdu.
function alarmButce(ab) {
  if (!ab) return "";
  const d = ab.dagilim || {}, t = ab.tepe_10dk, y = ab.yas_s;
  const tepeAsim = (ab.asim || {}).tepe, duranAsim = (ab.asim || {}).duran;
  // RESTART MUAFİYETİ GÖRÜNÜR OLMAK ZORUNDA (küçük-kuyruk turu, 2026-08-02). `tepe_10dk` artık
  // restart-sonrası 5 dk penceresindeki açılış patlamasını sayacın DIŞINDA bırakabiliyor (canlı
  // ölçüm: ham 18 → muafiyetli 5, tavan 10). Alan telde vardı ama panoda YOKTU — yani pano
  // "tepe 5, aşım yok" diyor, defterde 18 satır duruyordu. Sessiz maskeleme yasağı bir alanın
  // JSON'da bulunmasıyla değil OKUNMASIYLA yerine gelir (YASA 6). Rozet sayıyı, `title` tam
  // beyanı taşır; muafiyet UYGULANMADIYSA hiçbiri basılmaz — gürültü de bir yalandır.
  const muaf = !!ab.tepe_muafiyet_uygulandi;
  // ROLE YOK: bu bir KPI, bir olay değil. Duyurulacak bir şey olduğunda onu sessiz hat söyler.
  return `<div class="alarmbutce${ab.asim_var ? " asim" : ""}">
    alarm bütçesi · son 24 sa: <b>${d.low ?? "—"}</b> low · <b>${d.high ?? "—"}</b> high ·
    <span class="ab-not">acil ölçülemez (üretici yok)</span> —
    tepe <b>${t ?? "—"}</b>/10dk ${tepeAsim ? "▲" : ""}<span class="ab-not">(tavan ${ab.tavan_10dk ?? "—"})</span>${
      muaf ? ` <span class="ab-not" title="${esc(ab.tepe_beyan || "")}">(restart-muafiyetli · ham ${
        ab.tepe_ham_10dk ?? "—"})</span>` : ""} ·
    duran <b>${ab.duran ?? "—"}</b> ${duranAsim ? "▲" : ""}<span class="ab-not">(tavan ${ab.tavan_duran ?? "—"})</span>${
      ab.damgasiz ? ` · <span class="ab-not">${ab.damgasiz} damgasız satır sayıma girmedi</span>` : ""}${
      y ? ` · <span class="ab-not">${Math.round(y)} sn önce hesaplandı</span>` : ""}
    ${ab.asim_var ? `<span class="ab-not" style="display:block">${esc((ab.duran_beyan || ""))}</span>` : ""}</div>`;
}
function _bar(pct, color) {
  const w = Math.max(0, Math.min(100, pct));
  return `<div class="bar"><i style="width:${w}%${color ? `;background:var(--${color})` : ""}"></i></div>`;
}
async function _ctl(path, body) {
  // v219: `!r.ok → throw new Error(path + " → HTTP " + status)` KALKTI. O satır sunucunun
  // gerekçesini (409/403 gövdesindeki `detail`) siliyor ve yerine yalnız durum kodunu koyuyordu;
  // `apiFetch` artık gerekçenin kendisini fırlatıyor ve çağıranların `alert`i onu basıyor.
  const r = await apiFetch(path, { method: "POST", headers: { "content-type": "application/json" },
                                   body: body ? JSON.stringify(body) : "{}" });
  return r.json();
}
// MÜDAHALE KOLLARI — ÜÇ YÜZEY, TEK GÖVDE (S2R-2).
// Kollar bugüne dek YALNIZ üst bardaki `KRİZ ⚠` kapağının altında ve ⌘K'da yaşıyordu; yani
// panonun en yüksek bahisli dört düğmesinin hiçbir SAYFADA evi yoktu ve durumları (hangi kol
// çekili?) yalnız kapağı açınca okunuyordu. ADR: "kilit paneli (pozitif çerçeve) … müdahale
// ⌘K'da da yaşar" — kapak ve palet KALIR, kollar ayrıca Kilitler & Yapılandırma'da bir bölüm olur.
// Gövde tektir: üç yüzey de aynı `window.op*` fonksiyonlarını çağırır, ikinci bir yetki yolu yok.
//
// TAZELEME AKTİF SAYFAYA BAĞLI: kol hangi sayfadan çekilirse çekilsin (üst bar her sayfada var)
// o sayfa yeniden çizilir. Sabit `RENDER.operasyon()` çağrısı, S2R-2'den sonra çoğu durumda
// GÖRÜNMEYEN bir sayfayı tazelemek olurdu.
window.opSoftHalt = async () => {
  if (!HALTED && !confirm("Kademe 1 — Soft Halt?\n\nYeni emir girişi durur; mevcut pozisyonlar yönetilmeye devam eder.")) return;
  // `toggleHalt` ile AYNI gerekçe (v219): sessizce düşen bir durdurma kolu, çekilmiş sanılan bir
  // koldur. Kardeş kollar (`opLearnHalt`, `opCancelOpen`) zaten `_ctl` + `alert` yolundaydı.
  try { await apiFetch(HALTED ? "/api/resume" : "/api/halt", { method: "POST" }); }
  catch (e) { eylemHatasiYaz(null, e, (HALTED ? "DEVAM" : "DURDURMA") + " isteği sunucuya işlenemedi — kol ÇEKİLMEDİ."); return; }
  await refreshStatus(); await _aktifSayfayiCiz();
};
window.opLearnHalt = async (on) => {
  if (on && !confirm("Kademe 4 — Halt Learning?\n\nİşlemler DEVAM eder; Hermes yeni strateji versiyonu SHIP EDEMEZ. Rollback güvenlik olarak açık kalır.")) return;
  try { await _ctl("/api/control/learn_halt", { on }); } catch (e) { alert("Hata: " + e); }
  await _aktifSayfayiCiz();
};
window.opCancelOpen = async () => {
  if (!confirm("Kademe 2 — Cancel Open?\n\nYalnız DOLMAMIŞ giriş emirleri iptal edilir. Dolu pozisyonların koruyucu stop/hedef bacaklarına DOKUNULMAZ.")) return;
  try { const r = await _ctl("/api/control/cancel_open");
    // SINIF DÖKÜMÜ OKUNUR (v220/v221, KALEM 10 — YASA-6: `alpaca.cancel_open_entries` bu alanları
    // ÜRETİR, okuyucusu buydu). Süpürücü her açık emri `giris`/`koruma`/`yabanci` sınıflar ve YALNIZ
    // `giris`i iptal eder; salt "İptal: 4 · Korunan: 4" satırı korumanın DOKUNULMADIĞINI göstermiyordu.
    // `siniflar` yoksa UYDURULMAZ (?? 0): eski sunucu yanıtı da yalanmış gibi renklenmesin.
    const s = r.siniflar || {};
    const kept = r.kept || [];
    const korumaBacak = kept.filter(k => k.sinif === "koruma");
    const satir = [
      `İptal (giriş): ${(r.cancelled || []).length} · Korunan: ${kept.length}`,
      `Sınıf dökümü — giriş ${s.giris ?? 0} · koruma ${s.koruma ?? 0} · yabancı ${s.yabanci ?? 0}`,
      korumaBacak.length
        ? `Koruma bacağı DOKUNULMADI (${korumaBacak.length}): ${(korumaBacak[0].neden || "—").slice(0, 120)}`
        : "",
      (r.foreign || []).length ? `Yabancı (operatör emri, dokunulmadı): ${(r.foreign || []).length}` : "",
    ].filter(Boolean);
    alert(satir.join("\n"));
  } catch (e) { alert("Hata: " + e); }
  await _aktifSayfayiCiz();
};
window.opFlatten = async () => {
  if (!confirm("Kademe 3 — FLATTEN?\n\n⚠ Alpaca paper hesabındaki TÜM pozisyonlar piyasa fiyatından kapatılır ve tüm emirler iptal edilir.\n\nDİKKAT: Bu, senin ELLE aldığın pozisyonları da (ör. NVDA) kapatır!")) return;
  if (!confirm("SON ONAY — geri alınamaz. Tüm Alpaca paper pozisyonları kapatılsın mı?")) return;
  // onay jetonu: insan tuşu taşır, otomasyon taşımaz (jetonsuz çağrı kuru koşudur)
  try { const r = await _ctl("/api/alpaca/close_all?confirm=FLATTEN-PAPER"); alert("Flatten gönderildi: " + JSON.stringify(r).slice(0, 200)); }
  catch (e) { alert("Hata: " + e); }
  await _aktifSayfayiCiz();
};
// ---- KİLİTLER & YAPILANDIRMA · MÜDAHALE KADEMELERİ -------------------------------------------
// POZİTİF ÇERÇEVE (ADR): panel "neyin kapalı olduğunu" değil, "hangi kolun elinde olduğunu"
// söyler. Her satır ne yaptığını, şu anki hâlini ve düğmesini yan yana taşır — kapağın altındaki
// dört düğme aynı işi yapıyor ama orada hiçbir DURUM okunmuyordu.
// Durum kaynakları CANLI: `HALTED` (refreshStatus, 15 sn) ve `hud.learn_halted` (/api/diagnostics).
RENDER.mudahale = async () => {
  const d = await j("/api/diagnostics").catch(() => null);
  const h = (d || {}).hud || {};
  const olculdu = !!d;
  // TEHLİKE İŞARETİ SATIR İÇİ, YENİ SINIF DEĞİL: ".dlbtn.tehlike" diye bir kural yok ve olmayan
  // bir sınıf yazmak, ileride "neden kırmızı değil?" diye aranacak bir hayalet bırakır. Panonun
  // mevcut deseni zaten satır içi (bkz. skillRev "Reddet").
  //
  // BU AÇIKLAMA ŞABLONUN DIŞINDA DURUR — ve bu, canlı bir arızanın düzeltmesidir (2026-08-06).
  // Aynı cümle daha önce şablonun İÇİNDE bir HTML yorumuydu ve sınıf adını TERS TIRNAK içinde
  // yazıyordu. Ters tırnak şablon değişmezini KAPATIR: `.dlbtn.tehlike` bir üye erişimine, onu
  // izleyen ikinci ters tırnak da ETİKETLİ ŞABLON (tagged template) çağrısına dönüşür. Yani
  // "şablon-metni ⟨ters tırnak⟩ .dlbtn.tehlike ⟨ters tırnak⟩ devam-metni" dizisi,
  // ("şablon-metni").dlbtn.tehlike`devam-metni` diye ayrıştırılır;
  // "şablon-metni".dlbtn undefined olduğu için `.tehlike` okuması ÇALIŞMA ZAMANINDA patlar:
  // "TypeError: undefined is not an object". `node --check` bunu YAKALAMAZ — sözdizimi geçerli,
  // kusur anlamda. Bölüm çerçevesi devreye girdi ve dört müdahale kolunun DÖRDÜ birden ekrandan
  // silindi. KURAL: şablon değişmezinin içine ters tırnak YAZILMAZ (testte çivili).
  const kol = (no, ad, ne, durum, sinif, eylem, etiket, tehlike) => `
    <div class="kol-satir">
      <div><b>${esc(no)} · ${esc(ad)}</b><p class="hint" style="margin:2px 0 0">${ne}</p></div>
      <div class="kol-durum ${sinif || ""}">${durum}</div>
      <button class="dlbtn"${tehlike ? ' style="border-color:var(--red);color:var(--red)"' : ""}
        data-act="${eylem}">${esc(etiket)}</button>
    </div>`;
  // ÖLÇÜLEMEYEN DURUM "KAPALI" YAZMAZ: teşhis ucu düşerse learn-halt'ın hâli BİLİNMİYOR demektir
  // ve fail-closed bir kolun hâlini uydurmak, operatöre olmayan bir güvence vermek olurdu.
  const lh = !olculdu ? `<span class="mut">ölçülemedi</span>`
    : (h.learn_halted ? `<span class="warn">ÇEKİLİ</span>` : `<span class="pos">serbest</span>`);
  $("page-mudahale").innerHTML = bolumBasHTML("mudahale", "Müdahale kademeleri",
    "Dört kademe, artan sertlikte. Aynı kollar üst bardaki <b>KRİZ ⚠</b> kapağının altında ve "
    + "⌘K komut paletinde de yaşar — üçü de aynı gövdeyi çağırır, ikinci bir yetki yolu yoktur.")
    + `<div class="card rise" id="mudahale-kollar">
    ${satirKoru("Kademe 1 · Soft Halt", () =>
      kol("Kademe 1", "Soft Halt", "Yeni emir girişi durur; açık pozisyonlar yönetilmeye devam eder.",
      HALTED ? `<span class="warn">ÇEKİLİ</span>` : `<span class="pos">serbest</span>`, "",
      "opSoftHalt", HALTED ? "DEVAM et" : "Soft Halt", false))}
    ${satirKoru("Kademe 2 · Cancel-Open", () =>
      kol("Kademe 2", "Cancel-Open", "Yalnız DOLMAMIŞ giriş emirleri iptal edilir; koruyucu stop/hedef bacaklarına dokunulmaz.",
      `<span class="mut">anlık eylem</span>`, "", "opCancelOpen", "İptal et", false))}
    ${satirKoru("Kademe 3 · Flatten", () =>
      kol("Kademe 3", "Flatten", "Alpaca kağıt hesabındaki TÜM pozisyonlar piyasadan kapatılır, tüm emirler iptal edilir — elle açtıkların dahil. Çift onay ister.",
      `<span class="mut">anlık eylem</span>`, "", "opFlatten", "FLATTEN ⚠", true))}
    ${satirKoru("Kademe 4 · Halt Learning", () =>
      kol("Kademe 4", "Halt Learning", "İşlemler DEVAM eder; Hermes yeni strateji sürümü ship EDEMEZ. Rollback güvenlik olarak açık kalır.",
      lh, "", "opLearnHaltToggle", h.learn_halted ? "Kaldır" : "Ship'i durdur", false))}
    <p class="hint" style="margin-top:12px">HALT (üst bardaki kırmızı düğme) Kademe 1 ile AYNI
      kolu çeker — iki ad, tek mekanizma. Kademe 3 geri alınamaz.</p></div>`;
};

function _bellSVG(h) {
  // 40-kutu bootstrap dağılımı. Dikey çizgiler: Δ=0 (gri), ortalama (camgöbeği) ve EŞİK (amber) —
  // eşik = dağılımın (1−p_gerekli) kuantili; K-ceza eşiği yükseldikçe amber çizgi sola kayar ve
  // kapı ancak bu çizgi 0'ın SAĞINDA kalırsa geçer. Görsel kural = matematiksel kural.
  if (!h || !(h.counts || []).length) return "";
  const W = 560, H = 130, n = h.counts.length, mx = Math.max(...h.counts, 1);
  const bw = W / n, span = (h.hi - h.lo) || 1, total = h.counts.reduce((a, b) => a + b, 0) || 1;
  const bars = h.counts.map((c, i) => {
    const x = i * bw, bh = (c / mx) * (H - 22);
    const mid = h.lo + (i + 0.5) * span / n;
    return `<rect x="${x.toFixed(1)}" y="${(H - bh).toFixed(1)}" width="${Math.max(bw - 1, 1).toFixed(1)}" height="${bh.toFixed(1)}" fill="${mid > 0 ? "var(--green)" : "var(--red)"}" opacity=".5"/>`;
  }).join("");
  let acc = 0, qx = h.lo;                                  // (1−p_req) kuantili: kütlenin soldan bu kadarı
  const target = (1 - (h.p_required || 0.8)) * total;
  for (let i = 0; i < n; i++) {
    if (acc + h.counts[i] >= target) { const f = h.counts[i] ? (target - acc) / h.counts[i] : 0;
      qx = h.lo + (i + f) * span / n; break; }
    acc += h.counts[i];
  }
  const X = v => ((v - h.lo) / span) * W;
  return `<svg viewBox="0 0 ${W} ${H + 18}" style="width:100%;max-width:${W}px;display:block" role="img"
    aria-label="Bootstrap dağılımı: ortalama Δ ${h.mean}, P(ΔS>0)=${h.p}, gerekli ≥${h.p_required} — ${h.p >= h.p_required ? "kapıyı geçer" : "kapıyı geçmez"}">
    ${bars}
    <line x1="${X(0).toFixed(1)}" y1="0" x2="${X(0).toFixed(1)}" y2="${H}" stroke="var(--tx2)" stroke-dasharray="3 3"/>
    <line x1="${X(h.mean).toFixed(1)}" y1="0" x2="${X(h.mean).toFixed(1)}" y2="${H}" stroke="var(--accent)" stroke-width="2"/>
    <line x1="${X(qx).toFixed(1)}" y1="0" x2="${X(qx).toFixed(1)}" y2="${H}" stroke="var(--amber)" stroke-width="2" stroke-dasharray="6 3"/>
    <text x="${(X(0) + 4).toFixed(1)}" y="12" fill="var(--tx2)" font-size="10">Δ=0</text>
    <text x="${(X(h.mean) + 4).toFixed(1)}" y="26" fill="var(--accent)" font-size="10">ort ${h.mean}</text>
    <text x="${(X(qx) + 4).toFixed(1)}" y="42" fill="var(--amber)" font-size="10">eşik kuantili (P≥${h.p_required})</text>
    <text x="2" y="${H + 14}" fill="var(--tx2)" font-size="10">P(ΔS>0)=${h.p} · gerekli ≥${h.p_required} (0.80+K cezası) → ${h.p >= h.p_required ? "GEÇER ✓" : "GEÇMEZ ✗"}</text>
  </svg>`;
}
// ---- BULLET GRAPH — _donut ve _ring'in YERİNE (2026-08-01) ------------------------------------
// NEDEN İKİ HALKA KALDIRILDI: Few'nun bullet graph spesifikasyonu (Perceptual Edge 2006,
// rev. 2013) tam olarak bunun için yazıldı — "gösterge panolarında sıkça kullanılan metre ve
// kadranların YERİNİ almak üzere geliştirildi". Radyal kodlama niceliği AÇI ve ALAN ile taşır;
// Cleveland & McGill'in doğruluk sıralamasında bu, ortak bir eksen üzerindeki KONUM ve UZUNLUĞUN
// altındadır. Üstelik 92×92'lik bir halkanın çoğu pikseli hiçbir veri taşımıyordu.
//
// NÜANS — ÜÇ GÖSTERGE AYNI DEĞİLDİ, ÜÇÜ BİRDEN KALDIRILMADI: `.thermo` termometresi zaten
// LİNEER (dikey bir tüp). Yasak radyal kodlamayadır, dikey bara değil; termometre KALDI ve
// DESIGN.md'de izin verilen iki lineer metre formundan biri olarak yazıya geçti.
//
// SIRALAMA EVRENSEL DEĞİL: McColeman ve ark. Cleveland/McGill sıralamasının göreve bağlı
// olduğunu gösterdi. Bu yüzden gerekçe yalnız sıralamaya dayanmıyor — asıl dayanak Tufte'nin
// data-ink argümanı ve tek eksende KARŞILAŞTIRILABİLİRLİK.
//
// FEW'NUN BEŞ BİLEŞENİ, HEPSİ BURADA:
//   1. metin etiketi                      → `etiket`
//   2. tek lineer nicel eksen             → 0..`max`
//   3. belirgin çubuk (ölçülen değer)     → `deger`
//   4. DİK karşılaştırma çizgisi          → `hedef` (yoksa çizilmez, uydurulmaz)
//   5. 2–5 nitel aralık (ideal 3)         → `bantlar`
// Aralıklar TEK HUE'NUN FARKLI YOĞUNLUKLARI ile kodlanır, farklı hue'larla DEĞİL: farklı hue,
// renk körü bir okuyucunun ayıramadığı tam olarak o şeydir. Burada hue nötr sıcak gridir.
//
// BOŞ HÂL DÜRÜSTLÜĞÜ KORUNDU (bu, _donut'tan devralınan sözleşmedir): `deger == null` ise
// SIFIR BARI ÇİZİLMEZ. Eksen ve bantlar durur (ölçek metriğin kendisinden gelir, veriden değil),
// bar yoktur ve okuma "ölçüm yok" der. Sıfır uzunlukta bir bar "ölçtük, sıfır çıktı" demektir —
// ölçülmemiş bir şey için bu bir uydurmadır.
function _bullet(o) {
  // 150px EKSEN + 54px OKUMA = 212px. Eksen SABİT: aynı karttaki iki bullet farklı eksen
  // uzunluğuna sahip olursa uzunluklar karşılaştırılamaz ve bileşenin tek üstünlüğü gider.
  // Okuma kutusu da sabit — ilk denemede eksen 208px'ti ve okuma taşıp kırpılıyordu ("%42,").
  const W = 150, H = 18, IZ = 12, BAR = 6;          // iz: bant yüksekliği, bar: ölçüm yüksekliği
  const max = Number(o.max) > 0 ? Number(o.max) : 100;
  const olculdu = o.deger != null && Number.isFinite(Number(o.deger));
  const v = olculdu ? Math.max(0, Math.min(max, Number(o.deger))) : null;
  const X = n => (Math.max(0, Math.min(max, n)) / max) * W;

  // Yoğunluk merdiveni — TEK hue (sıcak nötr), artan koyuluk. Jetonlar temayla döndüğü için
  // gece zemininde merdiven kendiliğinden ters yöne (artan açıklık) çalışır; ayrı bir gece
  // listesi TUTULMUYOR.
  //
  // BEŞ BANTTAN ÜÇE (B1 düzeltmesi, 2026-08-02 · kontrast-denetimi.md §5/B1 + §11.1b).
  // Eski liste `card-2 → line → line-2 → tx3 → tx2` idi ve İKİ ayrı kusuru vardı:
  //   (1) son iki basamak (`tx3`, `tx2`) iki temada da AYNI RENKTİ — oran 1.00;
  //   (2) daha kötüsü, ekranda fiilen çizilen bantlar listenin İLK ikisiydi. `bantlar`
  //       varsayılanı üç, çağrıların çoğu İKİ bant istiyor — yani görünen tek geçiş
  //       `card-2 ↔ line`di ve o da 1.09:1, yani görünmüyordu. "2-5 nitel aralık" iddiası
  //       ekranda tek tonluk bir şeritti.
  // Üç bant Few'nun önerdiği idealdir ve orta basamak artık kendi jetonunu taşıyor:
  // adımlar 2.46 / 2.49 (gündüz) · 2.45 / 2.46 (gece). Tek-hue bir merdivenin toplam
  // menzili `card-2 ↔ tx2` ile sınırlı (~6.1:1), yani 3:1 adım ancak bantları ikiye
  // indirerek alınabilirdi — skalayı yok ederek "erişilebilir" kılmak olurdu.
  const YOG = ["var(--card-2)", "var(--band-2)", "var(--tx2)"];
  // Nitel aralıklar — kesir sınırları, açıktan koyuya. Bant sayısı merdivenin uzunluğuyla
  // sınırlı: liste kısaldığı gün fazladan sınır sessizce son bandı tekrarlardı.
  const bantlar = (o.bantlar && o.bantlar.length ? o.bantlar : [0.6, 0.85, 1]).slice(0, YOG.length);
  let onceki = 0;
  const iz = bantlar.map((b, i) => {
    const x0 = onceki * W, x1 = Math.min(1, b) * W;
    onceki = b;
    return `<rect x="${x0.toFixed(1)}" y="${(H - IZ) / 2}" width="${Math.max(0, x1 - x0).toFixed(1)}"
      height="${IZ}" fill="${YOG[i] || YOG[YOG.length - 1]}"/>`;
  }).join("");

  const bar = olculdu ? `<rect x="0" y="${(H - BAR) / 2}" width="${X(v).toFixed(1)}"
      height="${BAR}" fill="var(--${o.renk || "accent"})" rx="1"/>` : "";

  // Karşılaştırma ölçüsü: eksene DİK kısa çizgi. Few'nun spesifikasyonunda bu, barın kendisinden
  // ayrı okunmalı — bu yüzden iz yüksekliğini taşar.
  const hedef = (o.hedef != null && Number.isFinite(Number(o.hedef)))
    ? `<line x1="${X(o.hedef).toFixed(1)}" y1="1" x2="${X(o.hedef).toFixed(1)}" y2="${H - 1}"
        stroke="var(--tx)" stroke-width="2"/>` : "";

  // NİCEL EKSEN AÇIKÇA ÇİZİLİR (WP-P/P3, 2026-08-01). Few'nun 2. bileşeni "tek lineer NİCEL
  // eksen"dir ve nicel olması ölçek İŞARETLERİYLE kurulur. Bant sınırları uzunluğu okunabilir
  // kılıyordu ama sayısal ızgara yoktu: bar "üçte iki civarı" diye okunuyordu, "0-100 ekseninde
  // 66" diye değil. Çentikler eksenin ALTINDA ve saç teli — data-ink kuralı gereği bunlar
  // gösterimin en sönük mürekkebidir ve barla YARIŞMAZ.
  // Çentik konumları BANTLARDAN türetilir, ayrıca uydurulmaz: ikinci bir ölçek tanımı olsaydı
  // bantlarla çentikler ayrışabilir ve eksen kendi kendisiyle çelişirdi.
  // ÇENTİKLER SAÇ TELİ TONUNDA (--line-2, gündüz 1.47 · gece 1.83 zemine karşı) ve bu BEYANLI bir
  // sapmadır: WCAG 2.2 1.4.11'in 3:1 metin-dışı eşiğinin altındadırlar. Gerekçe, bu dosyanın saç
  // teli jetonları için zaten yazılı olan gerekçenin aynısı — çentikler ZORUNLU BİLGİ TAŞIMAZ,
  // bant merdiveni ve sağdaki sayısal okuma aynı ölçeği tek başlarına veriyor. Ölçeği erişilebilir
  // kılan şey çentikler değil, ALTLARINDAKİ İKİ UÇ ETİKETİdir (--tx2, gündüz 6.91 · gece 6.72).
  const centik = [0, ...bantlar].map(b => {
    const x = Math.min(1, b) * W;
    return `<line x1="${x.toFixed(1)}" y1="${H - 1}" x2="${x.toFixed(1)}" y2="${H + 2.5}"
      stroke="var(--line-2)" stroke-width="1"/>`;
  }).join("");
  // UÇ ETİKETLERİ — ekseni "nicel" yapan şey. Bunlar olmadan bar "üçte iki civarı" diye okunuyordu,
  // "0-100 ekseninde 66" diye değil. Ölçek metriğin KENDİSİNDEN gelir (max), veriden değil: bar
  // çizilmemiş olsa bile eksen aynı yerde durur (boş-hâl sözleşmesi).
  // BİÇİM CSS'TE (`.bl-ax`), ÖZNİTELİKTE DEĞİL: `font-family="var(--mono)"` bir sunum
  // özniteliğinde güvenilir değil (fill/stroke'ta çalışıyor olması onu genellemez).
  const ucEtiket = `<text class="bl-ax" x="0" y="${H + 10}">0</text>
    <text class="bl-ax" x="${W}" y="${H + 10}" text-anchor="end">${
      esc(o.olcek_ust != null ? o.olcek_ust : trn(max, 0))}</text>`;

  // MİNİ TREND — YALNIZ GERÇEK SERİ VARSA. `o.seri` verilmezse hiçbir şey çizilmez ve YERİ DE
  // TUTULMAZ: boş bir sparkline kutusu "trend ölçtük, düz çıktı" diye okunur — ölçülmemiş bir
  // şey için bu bir uydurmadır (bu dosyanın boş-hâl sözleşmesinin aynısı).
  // ≥2 NOKTA ŞARTI: tek noktalı bir "trend" bir trend değildir.
  const seri = (o.seri || []).map(Number).filter(Number.isFinite);
  let trendSvg = "";
  if (seri.length >= 2) {
    const TW = 54, TH = 14;
    const lo = Math.min(...seri), hi = Math.max(...seri), acik = (hi - lo) || 1;
    const pts = seri.map((s, i) =>
      `${(i * TW / (seri.length - 1)).toFixed(1)},${(TH - 1 - ((s - lo) / acik) * (TH - 2)).toFixed(1)}`
    ).join(" ");
    trendSvg = `<svg class="bl-spark" viewBox="0 0 ${TW} ${TH}" width="${TW}" height="${TH}"
      role="img" aria-label="son ${seri.length} ölçüm: ${trn(seri[0], 1)} → ${trn(seri[seri.length - 1], 1)}"
      preserveAspectRatio="none"><polyline points="${pts}" fill="none" stroke="var(--tx2)"
      stroke-width="1" vector-effect="non-scaling-stroke"/></svg>`;
  }

  const okuma = olculdu ? (o.metin != null ? o.metin : trn(v, 0)) : "—";
  const sesli = `${o.etiket}: ${olculdu ? okuma : "ölçüm yok"}`
    + (o.hedef != null ? `, karşılaştırma ${o.hedef}` : "")
    + (seri.length >= 2 ? `, son ${seri.length} ölçümün eğilimi` : "");

  // Etiket `.slabel` DEĞİL: o sınıf kutulu bir bölüm çipidir (kenar + tint dolgu) ve her
  // bullet'ı bir kontrol gibi gösteriyordu. Burada gereken çıplak mikro-etiket.
  return `<div class="bullet">
    <p class="bl-lab">${esc(o.etiket)}</p>
    <div class="bl-row">
      <svg viewBox="0 0 ${W} ${H + 12}" width="${W}" height="${H + 12}" role="img" aria-label="${esc(sesli)}"
        preserveAspectRatio="none">${iz}${bar}${hedef}${centik}${ucEtiket}</svg>
      <b class="bl-val mono-num${olculdu ? "" : " mut"}">${esc(okuma)}</b>
    </div>
    ${trendSvg ? `<div class="bl-trend">${trendSvg}<span class="bl-trend-lab">son ${seri.length}</span></div>` : ""}
    ${olculdu ? "" : `<p class="bl-yok">ölçüm yok</p>`}
  </div>`;
}
// ---- IC MİNİ TRENDİ (kütüphanesiz, 120×28) ------------------------------------------------------
// Tek bir IC sayısı "yükseliyor mu?" sorusunu CEVAPLAYAMAZ; score_calibration.json her turda üzerine
// yazıldığı için dünkü değer hiç var olmamış gibiydi. İki seri AYRI çizilir ve BİRLEŞTİRİLMEZ:
// havuzlanmış IC sim ağırlıklıdır (cf satırları gerçekleri 20:1 boğar), gerçek dilim IC ise kararın
// dayanacağı ölçümdür. Aynı çizgide toplamak iki farklı popülasyonu tek eğri gibi göstermek olurdu.
function icTrend(hist) {
  const W = 120, H = 28;
  const havuz = (hist || []).map(r => r.rank_ic).filter(v => v != null);
  const gercek = (hist || []).map(r => r.real_ic).filter(v => v != null);
  // ÜÇÜNCÜ SERİ (Aşama 1.1, 2026-07-28): havuz ile gerçek arasındaki fark cf diliminden gelir;
  // o dilim çizilmezse aradaki makas "neden?" sorusunu her bakışta yeniden tahmin ettirir.
  // Eski kayıtlarda `cf_ic` alanı YOKTUR — filtre onları düşürür, uydurma nokta eklenmez.
  const cfs = (hist || []).map(r => r.cf_ic).filter(v => v != null);
  if (havuz.length < 2 && gercek.length < 2 && cfs.length < 2)
    return `<span class="mut">trend için veri birikmedi (${(hist || []).length} nokta · günde bir düşer)</span>`;
  const all = havuz.concat(gercek).concat(cfs).concat([0]);
  const mn = Math.min(...all), mx = Math.max(...all), rng = (mx - mn) || 1;
  const y = v => (H - 2 - (v - mn) / rng * (H - 4)).toFixed(1);
  const poly = (vals, col, dash) => vals.length < 2 ? "" :
    `<polyline points="${vals.map((v, i) => `${(i / (vals.length - 1) * W).toFixed(1)},${y(v)}`).join(" ")}"
       fill="none" stroke="${col}" stroke-width="1.5" ${dash} opacity=".9"/>`;
  return `<svg viewBox="0 0 ${W} ${H}" style="width:${W}px;height:${H}px;flex:none" aria-hidden="true">
    <line x1="0" y1="${y(0)}" x2="${W}" y2="${y(0)}" stroke="var(--line)" stroke-width="1"/>
    ${poly(havuz, IC_SERI.havuz[1], `stroke-dasharray="${IC_SERI.havuz[2]}"`)}${
      poly(cfs, IC_SERI.sim[1], `stroke-dasharray="${IC_SERI.sim[2]}"`)}${
      poly(gercek, IC_SERI.gercek[1], "")}</svg>`;
}
// ---- IC TRENDİ · SERİ SÖZLEŞMESİ (B6 düzeltmesi, 2026-08-02) ------------------------------------
// TEK TABLO, İKİ TÜKETİCİ: çizim (`icTrend`) ve efsane (`icEfsane`) aynı satırdan okur. Ayrı
// yazıldıkları sürece ayrışabilirlerdi ve TAM OLARAK ayrıştılar: efsane üç adı üç RENKLE
// etiketliyordu, oysa `--violet` ile `--accent` iki temada da BİRE-BİR aynı renkti (oran 1.00)
// ve grafikteki gerçek ayrım kesik-çizgi DESENİYDİ — efsane o deseni hiç göstermiyordu
// (kontrast-denetimi.md §5/B6, öneri Ö8). Şimdi renk ayrı (luminans merdiveni: 17.80 → 9.60 →
// 5.06, kart üstünde) VE efsane çizgi örneğini basıyor. Renk körü okuyucu için taşıyıcı kanal
// desendir; hue EKLENMEDİ çünkü hue, renk körlüğünün sildiği tam o şeydir.
const IC_SERI = {
  gercek: ["gerçek", "var(--accent)", "0"],
  sim: ["sim", "var(--violet)", "1 3"],
  havuz: ["havuz", "var(--tx3)", "2 2"],
};
function icEfsane() {
  return Object.values(IC_SERI).map(([ad, renk, desen]) =>
    `<span style="display:inline-flex;align-items:center;gap:4px;white-space:nowrap">
       <svg width="18" height="6" viewBox="0 0 18 6" aria-hidden="true" style="flex:none">
         <line x1="0" y1="3" x2="18" y2="3" stroke="${renk}" stroke-width="1.5"${
           desen === "0" ? "" : ` stroke-dasharray="${desen}"`}/></svg>
       <span style="color:${renk}">${ad}</span></span>`).join(" · ");
}

const CHECK_TR = { exposure_budget: "bütçe", max_open_positions: "pozisyon", sector_cap: "sektör tavanı",
  daily_loss_breaker: "devre kesici", position_size: "boyut", rr_floor: "R:R", heat_hard: "ısı",
  sector_stacking: "sektör yığılması", heat_review: "ısı (soft)", correlation: "korelasyon",
  leading_sector: "lider sektör", rr_defined: "R:R tanımlı", rr_marginal: "R:R bandı",
  score_band: "skor bandı", earnings_blackout: "karartma", mirror_busy: "ayna", shadow_veto: "gölge veto" };

// ================= PİYASA — İZLENEN EVREN =================
// Pano kapıya GİRMİŞ birkaç sembolü gösteriyordu; "bugün neyi izliyorum?" sorusunun hiçbir yüzeyi
// yoktu — evrenin varlığı yalnız state/bars/ dizinindeki dosya sayısıydı. Bu sayfa o boşluğu
// kapatır ve tek bir şey ASLA iddia etmez: canlı fiyat. Her sayı EOD kapanış barından gelir,
// son seans başlıkta yazar, barı geride kalan semboller adıyla sayılır.
//
// FİLTRE VE SIRALAMA İSTEMCİDE: 260 satır tek pakette gelir, her tıklama için uca gitmek hem
// gereksiz hem de yanıltıcı olurdu (iki istek arasında evren değişirse kullanıcı iki farklı
// gerçeği tek tablo sanır). Sanal kaydırma YOK — 260 satır mevcut sayfaların çizdiği hacimde.
let _MKT = null;                                   // son çekilen paket (tazeleme dışında sabit)
let _MKT_SORT = { col: "ticker", dir: 1 };         // varsayılan: ticker artan
const _MKT_CHIPS = { position: false, armed: false, plan: false, earn: false };
// Kolonlar TEK yerde tanımlanır: başlık metni, sıralanabilirlik ve hücre sırası aynı satırdan
// okunur. İki ayrı liste (başlıklar + hücreler) tutulsaydı zamanla kayarlar ve tablo bir kolonun
// başlığına basıldığında BAŞKA bir kolonu sıralardı — sessiz ve fark edilmez bir yalan.
const _MKT_COLS = [
  // "SON 60 KAPANIŞ" başlığı komşusu "KAPANIŞ"ın hemen yanında duruyordu ve iki kolon tek bir
  // başlığın tekrarı gibi okunuyordu (tarayıcıda görüldü). Çizgi zaten kapanışlardan çizilir.
  ["ticker", "HİSSE", true], ["spark", "60 BAR TRENDİ", false], ["close", "KAPANIŞ", true],
  // SEANS İÇİ, KAPANIŞ'ın hemen yanında durur: iki fiyat yan yana okunmazsa "hangisi güncel?"
  // sorusu kolon başlığıyla cevaplanamaz. Yalnız silahlı satırlarda dolar (bkz. marketview).
  ["intraday_close", "SEANS İÇİ", true],
  ["chg1_pct", "1G", true], ["chg20_pct", "20G", true], ["dist_52w_high_pct", "52H ZİRVEYE", true],
  ["adv20_usd", "ADV $", true], ["plans_n", "PLAN", true], ["earnings_date", "EARNINGS", true],
  ["durum", "DURUM", false],
];
// Genişlikler tarayıcıda ÖLÇÜLDÜ (2026-07-27): "52H ZİRVEYE" 92px'lik kolonda 84px yer kaplıyor,
// yani komşu başlığa 8px kalıyordu; "SON 60 KAPANIŞ" ise iki satıra kırılıyordu. Kolonlar boşuna
// sıkışıktı. Toplam: 78+112+100+112+66+70+106+92+112+100+112 = 1060px (SEANS İÇİ eklendi).
// `min-width` kolon toplamıyla AYNI ve gereklidir: dar pencerede blok düzeyindeki satır kabın
// genişliğine düşer, sabit kolonlar dışarı taşar ve satırın alt çizgisi içerikten önce biterdi
// (kaydırınca ayrım çizgisi olmayan satırlar görünür). Mobil `.trow{min-width:460px}` kuralını da
// bilerek ezer — tablo kendi kabında yatay kayar, sayfanın gövdesi kaymaz.
const _MKT_GRID = "grid-template-columns:78px 112px 100px 112px 66px 70px 106px 92px 112px 100px 112px;min-width:1060px";

// Yüzde alanları uçtan YÜZDE SAYISI olarak gelir (rejim bütçesindeki gibi), kesir değil — bu
// yüzden pctf() değil bu biçimleyici kullanılır; ikisini karıştırmak 100× hataya yol açar.
// `renk=false`: 52 haftalık zirveye uzaklık YAPISAL olarak ≤0'dır (zirve tavandır). Onu kırmızıya
// boyamak her satırı "kayıp" diye okuturdu — oysa bu bir MESAFE ölçüsüdür, getiri değil.
const mktPct = (x, renk = true) => x == null ? '<span class="mut">—</span>'
  : `<span class="${renk ? cls(x) : ""}">${renk ? isr(x, "%" + trn(x, 2)) : "%" + trn(x, 2)}</span>`;
const mktUsd = v => {
  if (v == null) return '<span class="mut">—</span>';
  const a = Math.abs(v);
  if (a >= 1e9) return "$" + trn(v / 1e9, 1) + "B";
  if (a >= 1e6) return "$" + trn(v / 1e6, 1) + "M";
  if (a >= 1e3) return "$" + trn(v / 1e3, 0) + "K";
  return "$" + trn(v, 0);
};
// Bar damgasının SAATİ (yerel). Damga barın BAŞLANGICIdır; hücrede yanında duran fiyat o barın
// kapanışıdır — saatin yazılması "bu fiyat ne zamanki?" sorusunu kolonun içinde cevaplar.
function mktSaat(ts) {
  if (!ts) return "";
  const d = new Date(ts);
  return isNaN(d) ? String(ts).slice(11, 16) : d.toLocaleTimeString("tr-TR", { hour: "2-digit", minute: "2-digit" });
}
// Kazanç günü YAKIN MI? Bugünden ileriye ≤7 gün. Geçmiş tarih uçta zaten None'a düşer.
function mktSoon(d) {
  if (!d) return false;
  const t0 = new Date(); t0.setHours(0, 0, 0, 0);
  const gun = (new Date(d + "T00:00:00") - t0) / 86400000;
  return gun >= 0 && gun <= 7;
}
// 90×24 mini kapanış çizgisi — eksen/etiket yok, tek soruya cevap: son 60 barda yön ne?
function mktSpark(vals) {
  const v = (vals || []).filter(x => x != null);
  if (v.length < 2) return '<span class="mut">—</span>';
  const W = 90, H = 24, mn = Math.min(...v), mx = Math.max(...v), rng = (mx - mn) || 1;
  const pts = v.map((x, i) => `${(i / (v.length - 1) * W).toFixed(1)},${(H - 2 - (x - mn) / rng * (H - 4)).toFixed(1)}`).join(" ");
  return `<svg viewBox="0 0 ${W} ${H}" style="width:${W}px;height:${H}px;flex:none;display:block" aria-hidden="true">` +
         `<polyline points="${pts}" fill="none" stroke="${v[v.length - 1] >= v[0] ? "var(--green)" : "var(--red)"}" stroke-width="1.4" opacity=".9"/></svg>`;
}

RENDER.market = async () => {
  const d = await j("/api/market");
  _MKT = d;
  MARKET_N = d.n; MARKET_STALE = d.stale_n;        // şeridin alt satırı artık ölçülü (uydurma yok)
  const src = d.source || {}, reg = d.regime || {}, iq = d.intraday || {};
  // SEANS İÇİ CÜMLESİ ÖLÇÜMDEN GELİR, METİNDEN DEĞİL: eşik (stale_tol_s) uçtan taşınır, buraya
  // "120" yazılmaz — motor eşiği değiştirdiğinde pano sessizce yanlış söylemesin.
  const icSatir = !iq.tracked_n
    ? `seans içi ölçüm: ${esc(iq.reason || "silahlı plan yok")}`
    : `seans içi: <b style="color:var(--tx)">${iq.measured_n}/${iq.tracked_n}</b> silahlı hisse · kapanmış dakikalık bar` +
      `${iq.stale_tol_s != null ? ` (≤${iq.stale_tol_s} sn)` : ""}${iq.reason ? ` · ${esc(iq.reason)}` : ""}`;
  const regOzet = [REGIME_TR[reg.regime] || reg.regime || null,
                   reg.exposure_budget_pct != null ? `tavan %${reg.exposure_budget_pct}` : null,
                   reg.distribution_days != null ? `${reg.distribution_days} satış günü` : null,
                   reg.date ? `rejim ${esc(reg.date)}` : null].filter(Boolean).join(" · ");
  $("page-market").innerHTML = `
    ${bolumBasHTML("market", "Piyasa · izlenen evren", "")}
    <p class="subline rise"><b style="color:var(--tx)">${d.n}</b> hisse · kaynak
      <b style="color:var(--tx)">${src.bars ?? 0}</b> bars CSV${src.finviz_extra
        ? ` + <b style="color:var(--tx)">${src.finviz_extra}</b> finviz ekstrası` : ""}<br>
      <b style="color:var(--tx)">EOD kapanış verisi — seans içi fiyat yalnız silahlı hisselerde ölçülür</b> · son seans
      <b style="color:var(--tx)">${esc(d.as_of || "—")}</b>${regOzet ? ` · ${regOzet}` : ""}<br>
      ${icSatir}</p>
    ${d.stale_n > 0 ? `<p class="subline rise" style="color:var(--amber)">⚠ ${d.stale_n} hissenin barı ${esc(d.as_of || "")}'tan eski — o satırların tarihi sarı işaretli.</p>` : ""}
    ${d.retired_n > 0 ? `<p class="hint rise">${d.retired_n} sembol EMEKLİ (delist) — bar geçmişi
       gerçek olduğu için satırı durur, "emekli" etiketiyle işaretlidir; bayatlık sayımına GİRMEZ.</p>` : ""}
    ${src.finviz_reason ? `<p class="hint rise">finviz keşfi: ${esc(src.finviz_reason)}</p>` : ""}

    <div class="card rise" id="km-kart"></div>

    <div class="card rise">
      <input class="searchbox" id="mkt-q" type="search" placeholder="hisse ara… (ör. AAPL)"
             aria-label="Hisse kodunda ara" data-act="mktPaint" data-act-on="input">
      <div id="mkt-chips" style="display:flex;gap:8px;flex-wrap:wrap;margin-top:12px"></div>
      <!-- Sabit kolon genişlikleri toplam ~886px: dar bir pencerede tablo SIKIŞMAZ, kendi
           kabında yatay kayar. Sayfanın gövdesi asla yana kaymaz. -->
      <div id="mkt-tbl" style="margin-top:16px;overflow-x:auto"></div>
    </div>`;
  kmCiz();
  mktPaint();
  mktSideSub();
};

// ==============================================================================================
// P9 · KAPSAMA ISI-MATRİSİ (WP-P, 2026-08-02)
// ----------------------------------------------------------------------------------------------
// SORDUĞU SORU: "izlediğim evrende hangi ÖLÇÜM nerede EKSİK?" — Veri Sağlığı sayfasının soru
// cümlesinin ("baktığım veri sağlam mı?") sayısal hâli. Bugüne kadar panonun verdiği cevap tek
// bir sayıydı (`stale_n`), yani "kaç sembolün BARI bayat". Bar tazeliği kapsamanın YALNIZ BİR
// boyutudur: 300 barlık bir sembolün barı taze olabilir ama 52-haftalık ölçümü YOKTUR ve o
// eksiklik hiçbir yüzeyde görünmüyordu.
//
// EKSENLER MEVCUT VERİNİN DOĞAL EKSENİDİR, YENİ BİR UÇ AÇILMADI. Satırlar `marketview`in
// BEYAN ETTİĞİ ölçüm pencereleridir (her biri kendi asgari bar sayısını ister ve yoksa None
// döner — UYDURMA YASAĞI'nın kaynaktaki hâli); sütunlar evrenin dilimleridir. Hücre = o dilimde
// o ölçümün ölçülebildiği sembollerin oranı. Yani matris, `None` sayımının haritasıdır: her
// hücre "burada kaç sembol için bu soru CEVAPLANAMIYOR" der.
//
// İKİ SKALA, İKİ SORU (P9'un kendi sözleşmesi):
//   · KAPSAMA — tek-hue sequential (`--kap-1..4`). "Ne kadarı ölçülebiliyor?"
//   · SAPMA   — CVD-güvenli diverging (`--dv-n2..p2`). "Bu dilim EVRENDEN ne kadar ayrılıyor?"
// İkincisi asıl teşhis aracıdır: evrenin %98'inde ölçülen bir alan POZİSYONDAKİ hisselerde
// %60'a düşüyorsa, körlük tam da paranın durduğu yerdedir ve mutlak sayı bunu SÖYLEMEZ.
// Taban her zaman TÜM sütunudur ve payda hücrede yazılıdır.
//
// RAKAM BİRİNCİ KANAL, DOLGU İKİNCİ: bir ısı skalasının komşu basamakları 3:1 olamaz (menzil
// 2.05:1) — bu beyanlı bir sapmadır (kontrast-denetimi.md §6/İ8) ve bedeli, her hücrenin kendi
// oranını RAKAMLA yazmasıyla ödenir. Renk körü okuyucu için sapma kutupları ayrıca mavi ↔ toprak
// eksenindedir ve işaret (+/−) rakamın önünde durur.
const KM_OLCUM = [
  // [başlık, alan, pencere beyanı]  — pencereler marketview.py'nin sabitlerinden okunur DEĞİL,
  // ORADAN KOPYALANIR ve bu bilinçli: modül sabitleri uçtan servis edilmiyor. Kopyanın
  // ayrışması test edilemez, bu yüzden metin bir ÖLÇÜ değil bir AÇIKLAMA olarak yazıldı —
  // hücrenin hükmü alanın None olup olmamasından gelir, bu metinden değil.
  ["Son kapanış", "close", "bar var mı"],
  ["1-gün değişim", "chg1_pct", "iki kapanış ister"],
  ["20-gün değişim", "chg20_pct", "21 kapanış ister"],
  ["ADV20 (dolar)", "adv20_usd", "20 bar + eksiksiz hacim"],
  ["52-hafta uzaklık", "dist_52w_high_pct", "252 kapanış ister"],
  ["Seans-içi kapanış", "intraday_close", "TASARIM GEREĞİ yalnız silahlı"],
  ["Kazanç takvimi", "earnings_date", "ileri tarihli rapor"],
];
const KM_DILIM = [
  ["TÜM", () => true],
  ["pozisyon", r => !!r.position],
  ["silahlı", r => !!r.armed],
  ["planlı", r => (r.plans_n || 0) > 0],
  ["emekli", r => !!r.retired],
  ["barsız", r => r.source !== "bars"],
];
let _KM_MOD = "kapsama";
// Eşikler SABİT ve burada: hücre başına "yüzdelik dilim" hesaplamak, aynı matrisin iki koşumda
// iki farklı renk vermesine yol açardı (skala veriye göre kayardı). Sabit eşik, iki gün arasında
// karşılaştırılabilir bir harita demektir.
const _KM_ESIK = [50, 80, 95];              // <50 → k1 · <80 → k2 · <95 → k3 · ≥95 → k4
const _KM_SAPMA = [5, 20];                  // |d|<5 nötr · <20 zayıf · ≥20 güçlü
function _kmBant(pct) {
  return "k" + (pct < _KM_ESIK[0] ? 1 : pct < _KM_ESIK[1] ? 2 : pct < _KM_ESIK[2] ? 3 : 4);
}
function _kmSapmaBant(d) {
  const a = Math.abs(d);
  if (a < _KM_SAPMA[0]) return "";
  return (d < 0 ? "dn" : "dp") + (a < _KM_SAPMA[1] ? 1 : 2);
}
function kmCiz() {
  const kap = $("km-kart");
  if (!kap) return;
  const rows = (_MKT && _MKT.rows) || [];
  const bas = `<h2 class="t">Kapsama ısı-matrisi <span class="tx3" style="font-weight:400">(ölçüm × evren dilimi)</span></h2>`;
  if (!rows.length) {
    kap.innerHTML = bas + `<div class="empty">Evren satırı yok — matris çizilmedi (dürüst boşluk).</div>`;
    return;
  }
  const dilim = KM_DILIM.map(([ad, f]) => [ad, rows.filter(f)]);
  const sapma = _KM_MOD === "sapma";
  // TABAN HER ZAMAN İLK SÜTUN (TÜM). Sapma kipinde ilk sütun kendi kendisinden çıkarıldığı için
  // daima 0'dır ve bu bir arıza değil, tabanın KENDİSİDİR — hücre "taban" yazar, "0" değil.
  const taban = {};
  for (const [, alan] of KM_OLCUM) {
    const t = dilim[0][1];
    taban[alan] = t.length ? 100 * t.filter(r => r[alan] != null).length / t.length : null;
  }
  const hucre = (alan, satirlar, ilk) => {
    const n = satirlar.length;
    if (!n) return `<div class="km-cell km-yok" title="dilim boş">dilim yok</div>`;
    const pct = 100 * satirlar.filter(r => r[alan] != null).length / n;
    if (!sapma)
      return `<div class="km-cell ${_kmBant(pct)}" title="${Math.round(pct)}% · ${
        satirlar.filter(r => r[alan] != null).length}/${n} sembolde ölçüldü">%${Math.round(pct)}</div>`;
    if (ilk) return `<div class="km-cell km-yok" title="karşılaştırma tabanı">taban</div>`;
    const d = pct - (taban[alan] ?? 0);
    return `<div class="km-cell ${_kmSapmaBant(d)}" title="${Math.round(pct)}% · taban %${
      Math.round(taban[alan] ?? 0)} · ${n} sembol">${d > 0 ? "+" : d < 0 ? "−" : "±"}${
      Math.abs(Math.round(d))}</div>`;
  };
  const grid = `<div class="km-wrap"><div class="km-grid" style="--kmc:${KM_DILIM.length}">
    <div class="km-corner"></div>
    ${dilim.map(([ad, s]) => `<div class="km-head">${esc(ad)}<b>${s.length}</b></div>`).join("")}
    ${KM_OLCUM.map(([bas2, alan, pen]) => `<div class="km-row">${esc(bas2)}<i>${esc(pen)}</i></div>${
      dilim.map(([, s], i) => hucre(alan, s, i === 0)).join("")}`).join("")}</div></div>`;
  const sw = (kls, etiket) => `<span><span class="km-sw ${kls}"></span> ${etiket}</span>`;
  const lejant = sapma
    ? `<div class="km-lej">${sw("dn2", "−20p ve altı")}${sw("dn1", "−5…−20p")}${
        sw("", "±5p (nötr)")}${sw("dp1", "+5…+20p")}${sw("dp2", "+20p ve üstü")}
       <span class="mut">· taban: TÜM sütunu</span></div>`
    : `<div class="km-lej">${sw("k1", "&lt;%50")}${sw("k2", "%50-80")}${sw("k3", "%80-95")}${
        sw("k4", "≥%95")}${sw("", "dilim yok")}</div>`;
  kap.innerHTML = bas + `
    <div role="group" aria-label="Isı-matrisi skalası" style="display:flex;gap:8px;margin-top:12px">
      <button type="button" class="dlbtn${sapma ? "" : " primary"}" aria-pressed="${!sapma}"
        style="padding:7px 13px;min-height:36px;font-size:12px"
        data-act="kmMod" data-a1="kapsama">Kapsama</button>
      <button type="button" class="dlbtn${sapma ? " primary" : ""}" aria-pressed="${sapma}"
        style="padding:7px 13px;min-height:36px;font-size:12px"
        data-act="kmMod" data-a1="sapma">Evrenden sapma</button>
    </div>
    ${grid}${lejant}
    <p class="km-foot">Hücre, o dilimde ilgili ölçümün <b>ölçülebildiği</b> sembollerin oranıdır —
    yani <code>None</code> sayımının haritası. Payda her sütunun başlığında yazılı; boş dilim
    <b>renklendirilmez</b>, "dilim yok" der (sıfır bir ölçümdür, yokluk değil).
    <b>Seans-içi kapanış satırı tasarım gereği yalnız silahlı sembollerde doludur</b> — oradaki
    düşük kapsama bir arıza değil, "izlenmeyen sembole fiyat yazılmaz" kuralının kendisidir.
    Sapma kipi her hücreyi TÜM sütunundan çıkarır: körlüğün <b>nerede yoğunlaştığı</b> mutlak
    orandan okunamaz. Renk taramaya yardım eder, hükmü rakam verir.</p>`;
}
window.kmMod = (m) => { _KM_MOD = (m === "sapma") ? "sapma" : "kapsama"; kmCiz(); };

// Şeridin "Piyasa" satırı YERİNDE güncellenir. buildSidebar'ı çağırmak /api/today'i ikinci kez
// çekmek demekti — aynı veriyi iki kez istemek, iki farklı cevap alma ihtimalini de getirir.
// Bir sonraki tam şerit kurulumunda subs.market aynı iki değişkeni okur; iki yol ayrışamaz.
function mktSideSub() {
  const btn = document.querySelector('.sitem[data-p="market"]');
  if (!btn || MARKET_N == null) return;
  const txt = [`${MARKET_N} hisse`, MARKET_STALE ? `${MARKET_STALE} bayat bar` : null].filter(Boolean).join(" · ");
  let sub = btn.querySelector(".sub");
  if (!sub) { sub = document.createElement("span"); sub.className = "sub"; btn.appendChild(sub); }
  sub.textContent = txt;
  // data-full yazımı KALDIRILDI (2026-07-28): üzerine binen etiket kaldırıldığından o öznitelik
  // artık hiçbir yerde okunmuyordu. Özet .sub'a yazılıyor ve rayda zaten görünür.
  btn.title = `Piyasa — ${txt}`;
}

function mktChip(k) { _MKT_CHIPS[k] = !_MKT_CHIPS[k]; mktPaint(); }
function mktSort(col) {
  const sortable = (_MKT_COLS.find(c => c[0] === col) || [])[2];
  if (!sortable) return;
  _MKT_SORT = { col, dir: _MKT_SORT.col === col ? -_MKT_SORT.dir : 1 };
  mktPaint();
}
// ÖLÇÜLMEYEN HER ZAMAN SONA: None yönden BAĞIMSIZ olarak dibe iner. Aksi hâlde "en çok düşen"
// sıralamasının başında, hiç ölçülmemiş semboller dururdu — boşluk, bir uç değer gibi okunurdu.
function mktCmp(a, b) {
  const c = _MKT_SORT.col, dir = _MKT_SORT.dir, av = a[c], bv = b[c];
  if (av == null && bv == null) return String(a.ticker).localeCompare(String(b.ticker));
  if (av == null) return 1;
  if (bv == null) return -1;
  if (typeof av === "number" && typeof bv === "number") return (av - bv) * dir;
  return String(av).localeCompare(String(bv)) * dir;
}

function mktPaint() {
  if (!_MKT) return;
  const all = _MKT.rows || [];
  const q = ($("mkt-q")?.value || "").trim().toUpperCase();
  const say = { position: all.filter(r => r.position).length, armed: all.filter(r => r.armed).length,
                plan: all.filter(r => r.plans_n > 0).length, earn: all.filter(r => mktSoon(r.earnings_date)).length };
  const CHIP_TR = { position: "Pozisyonda", armed: "Silahlı", plan: "Planı var", earn: "Earnings ≤7g" };
  const chips = $("mkt-chips");
  if (chips) chips.innerHTML = Object.keys(CHIP_TR).map(k =>
    `<button type="button" class="dlbtn${_MKT_CHIPS[k] ? " primary" : ""}" aria-pressed="${_MKT_CHIPS[k]}"
       style="padding:7px 13px;min-height:36px;font-size:12px" data-act="mktChip" data-a1="${k}">${CHIP_TR[k]} · ${say[k]}</button>`).join("");

  const rows = all.filter(r =>
    (!q || String(r.ticker).includes(q)) &&
    (!_MKT_CHIPS.position || r.position) && (!_MKT_CHIPS.armed || r.armed) &&
    (!_MKT_CHIPS.plan || r.plans_n > 0) && (!_MKT_CHIPS.earn || mktSoon(r.earnings_date))
  ).sort(mktCmp);

  const basl = (id, label, sortable) => sortable
    ? `<button type="button" data-act="mktSort" data-a1="${id}" style="all:unset;cursor:pointer;padding:8px 0"
         aria-label="${esc(label)} kolonuna göre sırala">${label}${_MKT_SORT.col === id ? (_MKT_SORT.dir > 0 ? " ↑" : " ↓") : ""}</button>`
    : `<span>${label}</span>`;
  const head = `<div class="trow head" style="${_MKT_GRID}">${
    _MKT_COLS.map(([id, label, s]) => `<span>${basl(id, label, s)}</span>`).join("")}</div>`;

  const html = rows.map(r => {
    // Emekli satır BAYAT DEĞİLDİR: delist gününden sonra bar yok, yani "geride kalması" bir arıza
    // değil kesin sonuçtur. Sarı uyarı orada kalırsa gerçek bayatlığı bastıran kalıcı gürültü olur.
    const bayat = !r.retired && r.last_date && _MKT.as_of && r.last_date < _MKT.as_of;
    const durum = [r.position ? _chip("pozisyon", "t-go") : "", r.armed ? _chip("silahlı", "t-rv") : ""]
      .filter(Boolean).join(" ") || '<span class="mut">—</span>';
    return `<div class="trow" style="${_MKT_GRID}">
      <span class="tick">${esc(r.ticker)}${r.source !== "bars" ? `<br><span class="mut" style="font-size:10px;font-weight:400">${esc(r.source)}</span>` : ""}${
        r.retired ? `<br><span class="mut" style="font-size:10px;font-weight:400">emekli</span>` : ""}</span>
      <span>${mktSpark(r.spark)}</span>
      <span class="mono-num${bayat ? bayatSinif(r.last_date, _MKT.as_of) : ""}">${
        r.close == null ? '<span class="mut">—</span>' : money(r.close)}<br>
        <span class="${bayat ? "warn" : "mut"}" style="font-size:10px">${esc(r.last_date || "bar yok")}</span></span>
      <span class="mono-num">${r.intraday_close == null ? '<span class="mut">—</span>'
        : `${money(r.intraday_close)}<br><span class="mut" style="font-size:10px">${esc(mktSaat(r.intraday_ts))}</span>`}</span>
      <span class="mono-num">${mktPct(r.chg1_pct)}</span>
      <span class="mono-num">${mktPct(r.chg20_pct)}</span>
      <span class="mono-num">${mktPct(r.dist_52w_high_pct, false)}</span>
      <span class="mono-num">${mktUsd(r.adv20_usd)}</span>
      <span class="mono-num">${r.plans_n || 0}${r.last_plan_date
        ? ` <span class="mut" style="font-size:10px">${esc(r.last_plan_date)}</span>` : ""}</span>
      <span class="mono-num ${mktSoon(r.earnings_date) ? "warn" : ""}">${r.earnings_date ? esc(r.earnings_date) : '<span class="mut">—</span>'}</span>
      <span>${durum}</span></div>`;
  }).join("");

  const el = $("mkt-tbl");
  if (el) el.innerHTML = rows.length
    ? `${head}${html}<p class="mut" style="font-size:12px;margin-top:10px">${rows.length} / ${all.length} hisse gösteriliyor · ölçülmemiş alanlar "—" ve sıralamada sonda.</p>`
    : `<div class="empty">Filtreye uyan hisse yok — dürüst boşluk.</div>`;
}

// ==============================================================================================
// S2R-2 · OPERASYON'UN PARÇALANMASI — bir görünüm değil, ON DOKUZ BÖLÜMLÜK BİR DEPOYDU
// ----------------------------------------------------------------------------------------------
// Eski `RENDER.operasyon` tek bir `#page-operasyon` kabına on dokuz kart basıyordu: mutabakat
// masası, rejim kapıları, MLOps, edge sağlığı, dolar merceği, doğrulama, Hermes karnesi, sistem
// önerileri, rejim/risk dörtlüsü, kâr şelalesi, trend kolu, öğrenme çarkı, intraday gözlem, veri
// hattı, bütünlük dedektörleri, Redis, sağlayıcı sağlığı, öğrenme beslemesi. Yani "Teşhis ve
// müdahale" başlığı altında panonun ölçüm yüzeyinin yarısı yaşıyordu ve hiçbiri o sayfanın soru
// cümlesine ("sistem sağlıklı mı; değilse NE ve NEREDE?") hizmet etmiyordu — kapı kararı Koşu'nun,
// mutabakat Portföy'ün, bileşen IC'si Öğrenme'nin, karantina Veri'nin sorusudur.
//
// PARÇALAR BURADA ÜRETİLİR, SAYFALARA ORADA DAĞITILIR. İki alternatif vardı ve ikisi de kötüydü:
//   (a) her parçayı kendi fonksiyonuna çıkarmak → her fonksiyona kendi `const rc/rk/ml/gk/...`
//       çözümlemesi gerekir; aynı destructuring altı kez kopyalanır ve biri ilk düzenlemede
//       sessizce ayrışır (bu deponun tekrar eden kusur sınıfı).
//   (b) tek render'ın altı sayfaya yazması → o render YALNIZ kendi sayfası açılınca koşar; diğer
//       beş sayfa boş kalır ve nedeni hiçbir yerde görünmez.
// Seçilen üçüncü yol: TEK hesap, SAF çıktı. `opParcalar()` bir HTML sözlüğü döndürür; her sayfa
// bölümü yalnız kendi anahtarlarını yazar. Kullanılmayan parçalar da kurulur — maliyeti dizgi
// birleştirmedir ve `/api/diagnostics` zaten 15 sn önbellekli (JCACHE), yani ağ tek kez okunur.
async function opParcalar() {
  // OLAY HALKASI DA OKUNUR (pano turu 2026-07-31, §3.0 ③): kalıcı ret defteri
  // (`failed_submissions`) YALNIZ brokerin GERİ ÇEVİRDİĞİ emirleri taşır. Ağ arızası
  // (`alpaca_submit_unreachable`) ve gönderim bacağının kendi istisnası (`alpaca_submit_failed`)
  // o deftere HİÇ girmez — plan silahlı kalır ve mutabakat masası sessiz görünür. Bu iki hâl
  // yalnız olay akışında var; masaya oradan bakılır.
  const [d, evp] = await Promise.all([j("/api/diagnostics"), j("/api/events").catch(() => null)]);
  _DIAG = d; renderHUD(d);
  const rc = d.reconcile || {}, rk = d.risk || {}, ml = d.mlops || {}, pl = d.pipeline || {},
        lg = d.ledgers || {}, gk = d.gatekeeper || {}, hd = d.hud || {}, sch = d.scheduler || {};
  const reg = rk.regime || {};
  const bud = reg.exposure_budget_pct != null ? reg.exposure_budget_pct : hd.exposure_budget_pct;

  // ---------- BÖLÜM 1 · MUTABAKAT MASASI ----------
  const ghosts = (rc.ghosts || []).map(g =>
    `<div class="trow" style="grid-template-columns:80px 1fr auto">
       <span class="tick">${esc(g.symbol || "?")}</span><span class="chain">${esc(g.coid || "—")} · ${esc(g.status || "")}</span>
       ${_chip("GHOST", "t-no blink")}</div>`).join("");
  const hwm = (rc.hwm_pairs || []).map(hp => {
    const a = Number(hp.internal_trail), b = Number(hp.last_patch_to);
    const mx = Math.max(a || 0, b || 0) || 1;
    return `<div class="trow" style="grid-template-columns:70px 1fr auto;align-items:center">
      <span class="tick">${esc(hp.ticker)}</span>
      <span class="twin">
        <span class="tb">iç&nbsp;HWM <span class="bar"><i style="width:${(100 * (a || 0) / mx).toFixed(1)}%"></i></span><b class="mono-num">${trn(a, 2)}</b></span>
        <span class="tb">PATCH&nbsp;&nbsp; <span class="bar"><i style="width:${(100 * (b || 0) / mx).toFixed(1)}%;background:var(--${hp.desync ? "sev-1" : "sev-3"})"></i></span><b class="mono-num">${b ? trn(b, 2) : "—"}</b></span>
      </span>
      ${hp.desync ? _chip("DESYNC", "t-no blink") : (hp.last_patch_to != null ? _chip("senkron", "t-go") : _chip("PATCH bekleniyor", "t-vi"))}</div>`;
  }).join("");
  const fs = rc.force_sync || {};
  const pfills = (rc.partial_fills || []).map(pf => `<div class="trow" style="grid-template-columns:70px 1fr 1fr 1fr">
      <span class="tick">${esc(pf.ticker || "?")}</span>
      <span class="mono-num">${trn(pf.filled_qty)}/${trn(pf.total_qty)} (%${trn(pf.fill_pct, 1)})</span>
      <!-- D1 · gerçekleşen R koşulsuz yeşil, açık R koşulsuz kehribardı. İkisi de BÜYÜKLÜK,
           hiçbiri hüküm: kısmi dolumda riskin ne kadarının kapandığını, ne kadarının açıkta
           kaldığını söylerler. "Açık risk var" bir alarm seviyesi değildir — alarm, açık riskin
           TAVANI aştığı yerde doğar ve o ayrı bir satırdır (.alarmbutce.asim, --sev-2).
           TERS TIRNAK YOK — jeton/seçici adları burada TIRNAKSIZ yazılır. Bu yorum bir ŞABLON
           DEĞİŞMEZİNİN İÇİNDE ve oradaki her ters tırnak şablonu erkenden kapatır. Ölçüldü
           (2026-08-07, node): iki ters tırnak pfills ifadesini bir özellik erişimine çeviriyor
           ve kısmi dolum VARKEN çalışma zamanında TypeError atıyordu; istisna opParcalar()'ı
           düşürür, yani ondan beslenen ALTI bölüm birden "Bölüm yüklenemedi"ye iner —
           node --check bunu GÖRMEZ. Kural test_pano_mudahale_satiri_v194'te çivili. -->
      <span class="mono-num">gerçekleşen ${trn(pf.realized_risk_r, 2)}R</span>
      <span class="mono-num">açık ${trn(pf.open_risk_r, 2)}R</span></div>`).join("");
  const s1 = `<div class="card rise"><h2 class="t">Bölüm 1 · Mutabakat masası</h2>
    <div class="srow"><span>Broker API</span><b class="${rc.api_ok === false ? "neg" : "pos"}">${rc.api_ok === false ? "ERİŞİLEMİYOR" : "erişilebilir"}</b></div>
    ${(() => {
      // KESİNTİ SÜRESİ GÖRÜNÜR (2026-07-22): ham bayrak diskte donduğu için pano ölü akışı "canlı"
      // gösteriyordu. Artık bayrak × nabız tazeliği okunuyor ve kesinti NE KADARDIR yazıyor —
      // "kopuk" ile "45 dakikadır kopuk" operatör için aynı şey değil.
      // Sağlık alanları uçlarda DÜZ ve TEK isimle gelir (api.py _stream_view): hud, reconcile ve
      // /api/alpaca aynı anahtarları verir — aynı gerçeğin iki şekli olsaydı biri bayatlardı.
      const sure = wsDownFor(rc), dur = sure ? ` · ${sure}` : "";
      const etiket = rc.stream_ok === false
        ? `<span class="neg">WS KOPUK${dur}</span>${rc.stream_flag && rc.stream_stale ? ' <span class="warn">(nabız bayat)</span>' : ""}`
        : (rc.stream_ok ? "WS canlı" : "WS —");
      // Son hata yalnız KOPUKKEN gösterilir: toparlanmış akışta o metin geçmiştir (mirror_stream
      // `last_error`ı temizlemez) ve "şu an bozuk" diye okunur — sağlıklı satıra eski alarm yazmak
      // yanlış alarmların en sinsisidir, çünkü doğru görünür.
      const hata = rc.stream_ok === false && rc.stream_last_error
        ? `<span class="hint"> · ${esc(String(rc.stream_last_error).slice(0, 60))}</span>` : "";
      return `<div class="srow"><span>WS akışı · reconcile döngüsü</span><b>${etiket} · son tur ${esc((sch.updated || "").slice(11, 19) || "—")} · her ${sch.poll_seconds || "—"} sn${hata}</b></div>`;
    })()}
    <div class="srow"><span>Force-sync (bu tur)</span><b>strip ${fs.stripped ?? 0} · PATCH ${fs.trail_patched ?? 0}${fs.trail_failed ? ` · <span class="neg">RET ${fs.trail_failed}</span>` : ""}</b></div>
    ${ghosts ? `<h3 class="t" style="margin-top:16px">Hayalet emir dedektörü</h3>${ghosts}`
             : `<p class="hint">Hayalet emir yok — Alpaca'daki her canlı emrin yerel izi (armed/submitted/mirror) var.</p>`}
    ${hwm ? `<h3 class="t" style="margin-top:16px">HWM takip ikizleri</h3>${hwm}` : `<p class="hint">Açık pozisyon yok — HWM ikizleri pozisyon açılınca burada belirir.</p>`}
    ${pfills ? `<h3 class="t" style="margin-top:16px">Parçalı dolum · R ayrıştırma</h3>${pfills}` : ""}
    ${(() => {
      // AÇIK / KAPATILMIŞ (2026-07-27). Kapatma SİLMEZ: kapatılan ret sönük bir alt listede,
      // ack zamanıyla birlikte durur ve çekmecesi hâlâ açılır. Tarihçenin kaybolması ile sesinin
      // kısılması aynı şey değildir — biri kanıt kaybı, diğeri triyaj.
      const fsub = rc.failed_submissions || {};
      const open = fsub.open || [], acked = fsub.acked || [];
      if (!open.length && !acked.length) return "";
      const satir = (f, kapali) => {
        const k = rec("failsub", f);
        const key = `${f.plan_id || "?"}·${f.date || "?"}`;
        return `<div class="fsrow">
          <button ${rowAttrs(k, `${f.ticker || "?"} · ${f.detail || "gerekçe yok"}. Kaydı aç.`)}
                  class="trow rowbtn" style="grid-template-columns:64px 1fr 92px;flex:1;min-width:0">
            <span class="tick"${kapali ? ' style="opacity:.55"' : ""}>${esc(f.ticker || "—")}</span>
            <span class="mut">${esc(String(f.detail || "gerekçe kaydedilmemiş"))}</span>
            <span class="etime">${esc(String(f.date || "—"))}</span></button>
          ${kapali ? `<span class="mut" style="font-size:11px;white-space:nowrap">kapatıldı ${esc(String(f.ack_ts || "").slice(0, 16))}</span>`
                   : `<button class="dlbtn" style="padding:6px 12px;min-height:36px;font-size:12px" data-act="ackReject" data-a1="${esc(key)}">kapat</button>`}</div>`;
      };
      return `<h3 class="t" id="failsub" style="margin-top:16px">Reddedilen gönderimler (${open.length})</h3>
      <p class="hint">Broker emri geri çevirdi. Her satır açılır — gerekçe, plan ve tarih kayıtta.
        <b>Kapat</b>, kaydı silmez: yalnız triyaj şeridinden düşürür.</p>
      ${open.length ? `<div style="margin:10px 0 4px"><button class="dlbtn" data-act="ackRejectAll">
          Tümünü kapat (${open.length})</button> <span class="hint" id="fsub-msg" style="margin:0"></span></div>
        ${open.map(f => satir(f, false)).join("")}`
        : `<p class="hint">Açık ret yok — hepsi kapatıldı. <span id="fsub-msg"></span></p>`}
      ${acked.length ? `<h3 class="t" style="margin-top:14px;color:var(--tx2)">Kapatılanlar (${acked.length})</h3>
        ${acked.map(f => satir(f, true)).join("")}` : ""}`;
    })()}
    ${(() => {
      // GÖNDERİM OLAYLARI — RET DEFTERİNİN GÖRMEDİĞİ ÜÇ HÂL (pano turu 2026-07-31).
      // `alpaca_submit ok:false` broker reddidir ve kalıcı deftere de düşer; ama
      // `alpaca_submit_unreachable` (ağ) ile `alpaca_submit_failed` (gönderim bacağının istisnası)
      // O DEFTERE HİÇ YAZILMAZ — plan silahlı kalır ve masa "ret yok" der. Üçü burada yan yana.
      // BEYAN ŞART: olay halkası son 80 kayıtla sınırlıdır (obs.recent), yani BOŞLUK KANIT DEĞİLDİR.
      if (!evp) return `<p class="hint" style="margin-top:12px"><span class="mut">Gönderim olayları
        okunamadı (olay ucu düştü) — bu kutu ölçüm YOK demektir, "ret yok" demek değildir.</span></p>`;
      const ADI = { alpaca_submit: ["broker RET", "t-no"],
                    alpaca_submit_unreachable: ["ağ · ulaşılamadı", "t-rv"],
                    alpaca_submit_failed: ["gönderim istisnası", "t-no"] };
      const evs = (evp.events || []).filter(e => {
        const n = String(e.event || "");
        if (n === "alpaca_submit") return e.ok === false;
        return n === "alpaca_submit_unreachable" || n === "alpaca_submit_failed";
      }).slice(0, 8);
      const n80 = (evp.events || []).length;
      if (!evs.length) return `<p class="hint" style="margin-top:12px">Son ${n80} olayda başarısız
        gönderim yok (broker reddi · ağ arızası · gönderim istisnası). Halka son ${n80} kayıtla
        sınırlıdır — daha eski bir arıza bu pencerede görünmez.</p>`;
      const rows = evs.map(e => {
        const [lbl, kls] = ADI[String(e.event || "")] || [String(e.event || "?"), "t-vi"];
        const k = rec("event", e);
        return `<button ${rowAttrs(k, `${e.ticker || "?"} · ${lbl}. Olay kaydını aç.`)}
          class="trow rowbtn" style="grid-template-columns:64px 108px 1fr 86px">
          <span class="tick">${esc(e.ticker || "—")}</span>
          <span><span class="tag ${kls}">${esc(lbl)}</span></span>
          <span class="mut" style="font-size:12px">${esc(String(e.detail || e.error || "gerekçe alanı boş"))}</span>
          <span class="etime">${esc(relTime(e.ts) || "—")}</span></button>`;
      }).join("");
      return `<h3 class="t" style="margin-top:16px">Gönderim olayları · başarısız (${evs.length})</h3>
        <p class="hint">Kalıcı ret defterinin GÖRMEDİĞİ iki hâl burada: ağ arızasında plan silahlı
          kalır, gönderim istisnasında hiç deneme kaydı düşmez. Halka son ${n80} olay.</p>${rows}`;
    })()}
    ${(() => {
      // KAPIDA DÜŞEN SİLAHLI PLANLAR (E2 defterinin `motor="kapi"` kovası; yazan loop._armed_drop_row).
      // Bu satırlar bir İCRA KARARI DEĞİL: plan ne iç motora ne aynaya ulaştı, dolum HİÇ denenmedi.
      // Bu yüzden kart EXE-2026-001'in kill-ölçütü `dolmama_orani`nın PAYDASINA girmezler ve masada
      // AYRI durur — gönderim/ret satırlarıyla toplanırsa "emir çıktı ama tutmadı" gibi okunurdu.
      // ÜÇ HÂL AYRI (`_gapRows` deseni): kova YOK (ölçüm okunamadı) ≠ n=0 (ölçüldü, düşen yok) ≠ n>0.
      const slp = (d.icra || {}).slipaj || {}, kp = slp.kapi;
      if (!kp) return `<p class="hint" style="margin-top:12px"><span class="mut">Kapıda düşen silahlı
        planlar okunamadı (E2 özetinde <code>kapi</code> kovası yok) — bu kutu ölçüm YOK demektir,
        "düşen plan yok" demek değildir.</span></p>`;
      const pen = slp.pencere_gun ?? "?";
      if (!kp.n) return `<p class="hint" style="margin-top:12px">Son ${pen} günde kapıda düşen
        silahlı plan yok — silahlanan her plan icra yoluna girdi.</p>`;
      // BİLİNMEYEN ANAHTAR HAM GÖSTERİLİR (EXIT_TR deseni): sözlükte olmayan bir kapı adı sessizce
      // "diğer"e katlanırsa yeni bir kapı sınıfı panoda GÖRÜNMEDEN doğar.
      const KAPI_TR = { halt: "HALT — icra durdurma", breaker: "devre kesici",
                        data_bad: "veri arızası", throttle: "boyut kısıcı (size_mult=0)",
                        slot_full: "slot dolu", already_open: "sembol zaten defterde" };
      const rows = Object.entries(kp.kapi_dagilimi || {}).sort((a, b) => b[1] - a[1]).map(([g, n]) =>
        `<div class="srow"><span>${esc(KAPI_TR[g] || g)}</span><b class="mono-num">${n}</b></div>`).join("");
      return `<h3 class="t" style="margin-top:16px">Kapıda düşen silahlı planlar (${kp.n})</h3>
        <p class="hint">Plan silahlıydı, kapı kapalıydı: <b>dolum hiç denenmedi</b> — ne iç motorun
          ne aynanın icra kararı. Bu sayı <b>dolmama oranının</b> paydasına GİRMEZ; kill ölçütü kod
          değişikliğiyle kaymaz. Pencere son ${pen} gün.</p>${rows}`;
    })()}</div>`;

  // BPS ÖZETİ — ÜÇ İCRA KARTININ ORTAK BİÇİMLEYİCİSİ (E2 · E3 · E4). Eskiden sIcra'nın IIFE'si
  // içindeydi; E4'ün `giris_gap_bps`i de aynı `_bps_ozet` şeklini taşıdığı için buraya çıkarıldı.
  // TEK TANIM ŞART: ikinci bir kopya, "ölçülemeyen" satırının bir kartta gösterilip diğerinde
  // yutulması gibi sessiz bir ayrışmayı ilk düzenlemede doğururdu.
  // None istatistik 0.0 gibi BASILMAZ: n=0 "slipaj sıfırdı" değil "ölçüm yok"tur; paydadan düşen
  // satır (`n_olculemeyen`) sessizce kaybolmaz, sayısıyla yanında durur.
  const fmtBps = o => (!o || !o.n)
    ? `— (n=0${o && o.n_olculemeyen ? ` · ölçülemeyen ${trn(o.n_olculemeyen)}` : ""})`
    : `ort ${trn(o.ort, 1)} · medyan ${trn(o.medyan, 1)} · p90 ${trn(o.p90, 1)} bps `
      + `(n=${trn(o.n)}${o.n_olculemeyen ? ` · ölçülemeyen ${trn(o.n_olculemeyen)}` : ""})`;

  // ---------- İCRA GERÇEKLİĞİ · E2 SLİPAJ DEFTERİ (kart EXE-2026-001) --------------------------
  // NEDEN AYRI KART: Bölüm 1 "iç defterim brokerinkiyle aynı mı?" diye sorar (sapma/hayalet/HWM);
  // burası "emir çıkınca NE OLDU?" diye — ret SINIFI, dolumun bps faturası, kill ölçütü ve iki
  // motorun mutabakatı. İkisi tek kartta toplansa sapma sayıları icra sayılarıyla aynı sütuna
  // dizilir, "kaç emir reddedildi" ile "kaç pozisyon ayrıştı" birbirine karışırdı.
  // EŞİK YÜKTEN OKUNUR (C10 dersi): `kill_esigi` panoya SABİT yazılmaz — analytics'te değişirse
  // pano sessizce eski eşiği savunmaya devam ederdi; ekrandaki sayı ölçümün kendi sayısıdır.
  // None ≠ 0 (UYDURMA YASAĞI): oranın paydası boşken "%0" basmak "ret yok / slipaj yok" demek
  // olurdu. Ölçülemeyen her yerde "—" + NEDEN yazar.
  const sIcra = (() => {
    const slp2 = (d.icra || {}).slipaj;   // dosya idiyomu: `|| {}` zinciri, opsiyonel-zincir yok
    // BAŞLIK BİR FONKSİYON, DİZGİ DEĞİL: üç dalın üçü de AYNI başlığı basar ama KAPALI ÖZETİ
    // dala göre değişir (ölçüm yok / defter boş / ölçüldü) ve özet başlığın hemen ardında durmak
    // zorunda. Üç yere üç kez yazmak, sözleşmenin üç kopyası olurdu.
    const kartBas = ozet => `<div class="card rise"${katKart("mutabakat:icra")}><h2 class="t">İcra gerçekliği
      <span class="tx3" style="font-weight:400">(E2 slipaj defteri · kart EXE-2026-001)</span></h2>${ozet}`;
    // ÜÇ HÂL AYRI (`_gapRows` / kapı bloğu deseni): yük YOK (ölçüm okunamadı) ≠ defter BOŞ
    // (ölçüldü, satır düşmedi) ≠ dolu. Birincisi arıza, ikincisi durum — aynı kutuya sığmazlar.
    if (!slp2 || !Object.keys(slp2).length) return `${kartBas(kartOzeti({ deger: null, rozet: "ÖLÇÜLEMEDİ",
      meta: "teşhis yükünde <code>icra.slipaj</code> yok — E2 ölçümü okunamadı (\"icra temiz\" DEĞİL)." }))}
      <p class="hint"><span class="mut">Ölçüm okunamadı — E2 özeti teşhis yükünde yok
        (<code>icra.slipaj</code>). Bu kutu <b>ölçüm YOK</b> demektir, "icra temiz" demek
        değildir.</span></p></div>`;
    const pen = esc(String(slp2.pencere_gun ?? "?"));
    if (String(slp2.durum || "").includes("defter boş")) return `${kartBas(kartOzeti({ deger: null, rozet: "DEFTER BOŞ",
      meta: `${esc(slp2.durum)} · defterde ${trn(slp2.n_defter)} satır — boş defterden oran ÜRETİLMEZ ("%0 ret" yazmak "slipaj yok" demek olurdu).` }))}
      <div class="srow"><span>Defter</span><b class="mut">${esc(slp2.durum)}</b></div>
      <div class="srow"><span>Defterdeki satır</span><b class="mono-num">${trn(slp2.n_defter)}</b></div>
      <p class="hint">Nedeni yük kendi söylüyor; pano ikinci bir açıklama uydurmaz. Boş defterden
        oran/ortalama ÜRETİLMEZ: "%0 ret" ya da "0,0 bps" yazmak "slipaj yok" demek olurdu.
        Kaynak: <code>${esc(slp2.kaynak || "—")}</code></p></div>`;
    const ay = slp2.ayna || {}, dl = ay.dolum || {}, ic = slp2.ic_motor || {}, mt = slp2.mutabakat || {};
    // BİLİNMEYEN ANAHTAR HAM BASILIR (EXIT_TR/kapı deseni): sözlükte olmayan bir karar ya da ret
    // sınıfı sessizce "diğer"e katlanırsa yeni bir sınıf panoda GÖRÜNMEDEN doğar.
    const ICRA_TR = { submitted: "gönderildi", rejected: "broker reddetti", veto: "yasa vetosu",
                      unreachable: "broker erişilemedi", fill: "doldu", skip: "atlandı",
                      entry_missed_limit: "limit kaçtı (dolmadı)", entry_gap_veto: "gap vetosu",
                      stop_vs_current: "stop cari fiyatın yanlış tarafında", gap_veto: "gap vetosu",
                      buying_power: "alım gücü yetmedi", diger: "diğer" };
    // BOŞ SÖZLÜK SATIR BASMAZ: "0 kayıt" ile "kova hiç yok" ayrımı başlıkta zaten yapıldı.
    const dagRows = dag => Object.entries(dag || {}).sort((a, b) => b[1] - a[1]).map(([k, n]) =>
      `<div class="srow"><span>${esc(ICRA_TR[k] || k)}</span><b class="mono-num">${trn(n)}</b></div>`).join("");
    // `|| 0` KALDIRILDI (v196/KALEM-3, kademe 3): alan yükte yoksa bu satır "0 · ölçüt karşılandı"
    // yazıyordu — ÖLÇÜLMEMİŞ bir kill ölçütünü GEÇMİŞ gibi okutuyordu. `trn()` null'da zaten "—".
    const stopN = (ay.red_sinifi_dagilimi || {}).stop_vs_current;
    const dm = ic.dolmama_orani, ke = ic.kill_esigi;   // ikisi de YÜKTEN — eşik burada sabit değil
    const asildi = (dm != null && ke != null && dm > ke);
    const ayr = mt.ayrisan || [];
    const ayrRows = ayr.map(a => `<div class="trow" style="grid-template-columns:70px 120px 1fr 1fr">
        <span class="tick">${esc(a.ticker || "?")}</span>
        <span class="chain mut">${esc(String(a.plan_id || "—").slice(0, 14))}</span>
        <span class="chain">ayna: ${esc(ICRA_TR[a.ayna] || a.ayna || "—")} · dolum ${a.ayna_fill != null ? trn(a.ayna_fill, 2) : "yok"}</span>
        <span class="chain">iç: ${esc(ICRA_TR[a.ic] || a.ic || "—")}</span></div>`).join("");
    // ---- MUTABAKAT · BÖLÜM ÖZETİ · HÜCRE ŞERİDİ (v192) ---------------------------------------
    // Masanın dört hükmü aşağıda otuz `srow`un içine dağılmış durumda ve satır satır okunmadan
    // görünmüyorlar. Şerit dördünü açar; AŞAĞIDAKİ TABLOLAR AYNEN KALIR — bu bölüm bir teşhis
    // masasıdır ve satırların hepsi hücreleşseydi ekran otuz hücreye dönerdi ("özet" değil, ikinci
    // bir tablo). Her çubuğun paydası AYRI ve her biri kendi paydasını yazar: ret oranının paydası
    // gönderim denemesi, dolumun paydası gönderilen emir, kill ölçütününki EŞİĞİN KENDİSİ
    // (yükten okunur, panoda sabit değil), ayrışmanınki ortak plan.
    const _ozet = ozetSerit([
      ozetHucre("Ayna · ret oranı", {
        deger: ay.red_orani == null ? null : pctf(ay.red_orani, 1),
        degerSinif: ay.red_orani == null ? "" : (ay.red_orani > 0 ? "neg" : ""),
        oran: ay.red_orani, payda: `gönderim denemesi (${trn(ay.n)})`,
        meta: ay.red_orani == null ? "gönderim denemesi yok — oran tanımsız"
          : `${trn(ay.n)} denemede · <code>stop_vs_current</code> ${trn(stopN)}`,
        rozet: ay.red_orani == null ? "ÖLÇÜLEMEDİ" : (azOrnek(ay.n) ? "AZ ÖRNEK" : "") }),
      ozetHucre("Dolum oranı", {
        deger: dl.dolum_orani == null ? null : pctf(dl.dolum_orani, 1),
        oran: dl.dolum_orani, payda: "gönderilen emir",
        meta: dl.dolum_orani == null ? "gönderilen emir yok — oran tanımsız"
          : `${trn(dl.n_dolan)} dolan · pencere ${pen} gün`,
        rozet: dl.dolum_orani == null ? "ÖLÇÜLEMEDİ" : "" }),
      ozetHucre("İç motor · dolmama", {
        deger: dm == null ? null : pctf(dm, 1),
        degerSinif: asildi ? "neg" : "",
        // ÇUBUK EŞİĞE GÖRE DOLAR: tam dolu çubuk = kill ölçütü. Eşik yükte yoksa çubuk çizilmez —
        // paydası olmayan bir "doluluk" okuru kendi uydurduğu tavana göre okutur.
        oran: (dm == null || ke == null || !ke) ? null : dm / ke,
        payda: ke == null ? "" : `kill eşiği (${pctf(ke, 0)}) · yükten okunur`,
        meta: dm == null ? "iç motor satırı yok — ölçülmedi"
          : `${trn(ic.n)} satır · ${asildi ? "kill ölçütü AŞILDI (EXE-2026-001)" : "eşiğin altında"}`,
        rozet: dm == null ? "ÖLÇÜLEMEDİ" : (azOrnek(ic.n) ? "AZ ÖRNEK" : "") }),
      ozetHucre("İki motor · ayrışan", {
        // AYRIŞMA SAYISI PAYDASIYLA ANLAM KAZANIR: ortak plan yoksa iki motor hiç karşılaştırılmadı
        // ve "0 ayrışma" yazmak "ikisi hizalı" demek olurdu — ölçülmemiş bir uyum iddiası.
        deger: mt.ortak_plan_n == null ? null : trn(mt.ayrisan_n),
        degerSinif: mt.ayrisan_n ? "warn" : "",
        oran: (mt.ortak_plan_n && mt.ayrisan_n != null) ? mt.ayrisan_n / mt.ortak_plan_n : null,
        payda: mt.ortak_plan_n ? `ortak plan (${trn(mt.ortak_plan_n)})` : "",
        meta: mt.ortak_plan_n
          ? `${trn(mt.ortak_plan_n)} ortak planda · ${mt.ayrisan_n ? "iki motor hizalanmadı" : "ayrışma yok"}`
          : "ortak plan yok — iki motor karşılaştırılamadı",
        rozet: mt.ortak_plan_n ? "" : "ÖLÇÜLEMEDİ" }),
    ], "İcra gerçekliğinin bölüm özeti");
    // KAPALI ÖZET (v198) — ŞERİDİN DÖRT HÜCRESİNDEN BİRİ SEÇİLİR, beşinci bir sayı UYDURULMAZ.
    // Seçilen: AYNA RET ORANI. Gerekçe: kartın sorusu "emir gerçekten gitti mi?" ve o sorunun ilk
    // kapısı brokerin reddi; dolum/kill/ayrışma o kapıdan GEÇENLERİ ölçer. Payda aynı: gönderim
    // denemesi. Kart açıldığında dört hücrenin dördü de yerinde durur — özet onların yerini
    // almaz, hangisinin bakılmayı hak ettiğini söyler.
    const bas = kartBas(kartOzeti({
      deger: ay.red_orani == null ? null : pctf(ay.red_orani, 1),
      degerSinif: ay.red_orani == null ? "" : (ay.red_orani > 0 ? "warn" : ""),
      oran: ay.red_orani, payda: `gönderim denemesi (${trn(ay.n)})`,
      meta: ay.red_orani == null
        ? "gönderim denemesi yok — ret oranı tanımsız; defter dolu ama ayna bacağı ölçülemedi."
        : `${trn(ay.n)} denemede · dolum ${dl.dolum_orani == null ? "ölçülemedi" : pctf(dl.dolum_orani, 1)} · ${
            asildi ? "iç motor kill ölçütü AŞILDI" : `${trn(mt.ayrisan_n)} plan ayrıştı`} · pencere ${pen} gün`,
      rozet: ay.red_orani == null ? "ÖLÇÜLEMEDİ" : (asildi ? "KILL ÖLÇÜTÜ AŞILDI" : (azOrnek(ay.n) ? "AZ ÖRNEK" : "")) }));
    return `${bas}${_ozet}
      <div class="srow"><span>Pencere</span><b class="mono-num">${pen} gün · pencerede ${trn(slp2.n)} satır · defterde ${trn(slp2.n_defter)}</b></div>
      <p class="hint">Kaynak: <code>${esc(slp2.kaynak || "—")}</code></p>

      <h3 class="t" style="margin-top:16px">Ayna · gönderim &amp; ret (${trn(ay.n)})</h3>
      <div class="srow"><span>Ret oranı <span class="tx3">(payda: gönderim denemesi)</span></span>
        <b class="${ay.red_orani == null ? "mut" : (ay.red_orani > 0 ? "neg" : "pos")}">${ay.red_orani == null ? "— gönderim denemesi yok" : pctf(ay.red_orani, 1)}</b></div>
      <div class="srow"><span>Kartın (a) ölçütü · <code>stop_vs_current</code></span>
        <b class="${stopN ? "neg" : (stopN === 0 ? "pos" : "mut")}">${trn(stopN)}${
          stopN ? " — sıfıra inmeli" : (stopN === 0 ? " · ölçüt karşılandı" : " — ölçülmedi (alan yükte yok)")}</b></div>
      ${dagRows(ay.karar_dagilimi)}
      ${dagRows(ay.red_sinifi_dagilimi)}
      <div class="srow"><span>Dolum</span><b class="mono-num">${trn(dl.n_dolan)} dolan · oran ${dl.dolum_orani == null ? '<span class="mut">— gönderilen emir yok</span>' : pctf(dl.dolum_orani, 1)}</b></div>
      <div class="srow"><span>Dolum − resmî açılış</span><b class="mono-num">${fmtBps(dl.fill_vs_resmi_acilis_bps)}</b></div>
      <div class="srow"><span>Dolum − limit</span><b class="mono-num">${fmtBps(dl.fill_vs_limit_bps)}</b></div>
      <p class="hint">Limite sıfır yakınlık tavanın BAĞLADIĞINI, belirgin negatif ise yasanın para
        bıraktığını söyler — ikisi de kart grid'inin ölçüm girdisidir, karar değil.</p>

      <h3 class="t" style="margin-top:16px">İç motor · kill ölçütü (${trn(ic.n)})</h3>
      <div class="srow"><span>Dolmama oranı</span>
        <b class="${dm == null ? "mut" : (asildi ? "neg" : "pos")}">${dm == null ? "— ölçülmedi (iç motor satırı yok)" : pctf(dm, 1)}${dm == null ? "" : (asildi ? " · kill ölçütü aşıldı (kart EXE-2026-001)" : " · eşiğin altında")}</b></div>
      <div class="srow"><span>Kill eşiği <span class="tx3">(yükten okunur)</span></span>
        <b class="${ke == null ? "mut" : "mono-num"}">${ke == null ? "— eşik yükte yok" : pctf(ke, 0)}</b></div>
      <div class="srow"><span>Kaçan limit · gap vetosu · dolan</span>
        <b class="mono-num">${trn(ic.kacan_limit_n)} · ${trn(ic.gap_veto_n)} · ${trn(ic.n_dolan)}</b></div>
      <div class="srow"><span>Dolum − resmî açılış <span class="tx3">(iç motor)</span></span><b class="mono-num">${fmtBps(ic.fill_vs_resmi_acilis_bps)}</b></div>
      ${dagRows(ic.karar_dagilimi)}

      <h3 class="t" style="margin-top:16px">İki motor mutabakatı</h3>
      <div class="srow"><span>Ortak plan</span><b class="mono-num">${trn(mt.ortak_plan_n)}</b></div>
      <div class="srow"><span>Ayrışan plan</span>
        <b class="${mt.ayrisan_n ? "warn" : "pos"}">${mt.ayrisan_n ? trn(mt.ayrisan_n) + " — iki motor hizalanmadı" : "ayrışma yok"}</b></div>
      ${ayrRows ? `<div class="tbl" style="margin-top:8px">${ayrRows}</div>` : ""}
      <p class="hint">Ayna dolumu aynı gün henüz uzlaşmamış olabilir: <b>dolum yok</b> + iç motor
        <b>doldu</b> satırları pencere ilerledikçe kapanır. Kapanmayan ayrışma gizlenmez, kalıcı
        ölçüm olarak burada durur.</p></div>`;
  })();

  // ---------- İCRA GERÇEKLİĞİ · E3 KÖTÜMSER MALİYET BANDI --------------------------------------
  // NEDEN E2'DEN AYRI KART: E2 "emir çıkınca ne oldu?"yu ölçer; burası "o faturayı hangi VARSAYIMLA
  // hesaplıyoruz?" sorusudur. Yürürlükteki band bir GİRDİdir (goal.yaml sözleşmesi), ampirik ölçüm
  // ise o girdinin sınanmasıdır. İkisi E2'nin bps satırlarının arasına serpiştirilse "gerçekte
  // ödediğimiz" ile "varsaydığımız" aynı sütuna düşer ve fark okunmaz hâle gelirdi.
  // ASGARİ-N YÜKTEN OKUNUR (C10 dersi): `min_n` panoya SABİT yazılmaz — analytics'teki BAND_MIN_N
  // değişirse pano sessizce eski asgariyi savunmaya devam ederdi.
  // ÖLÇER, UYGULAMAZ: bu kart goal.yaml'ı DEĞİŞTİRMEZ ve değiştirdiğini ima etmez; `uygulama`
  // alanı sözleşmeyi kendi ağzıyla söyler, pano onu kendi cümlesiyle yeniden yazmaz.
  const sBand = (() => {
    const kb = (d.icra || {}).kotumser_band;   // dosya idiyomu: `|| {}` zinciri, opsiyonel-zincir yok
    const bas = `<div class="card rise"${katKart("mutabakat:band")}><h2 class="t">Kötümser maliyet bandı
      <span class="tx3" style="font-weight:400">(E3 · yürürlük + ampirik ölçüm)</span></h2>`;
    if (!kb || !Object.keys(kb).length) return `${bas}
      ${kartOzeti({ deger: null, rozet: "ÖLÇÜLEMEDİ",
        meta: "teşhis yükünde <code>icra.kotumser_band</code> yok — E3 ölçümü okunamadı (\"band yerinde\" DEĞİL)." })}
      <p class="hint"><span class="mut">Ölçüm okunamadı — E3 özeti teşhis yükünde yok
        (<code>icra.kotumser_band</code>). Bu kutu <b>ölçüm YOK</b> demektir, "maliyet bandı
        yerinde" demek değildir.</span></p></div>`;
    const yr = kb.yururlukteki || {};
    // BİLİNMEYEN TABAN HAM BASILIR (EXIT_TR/kapı deseni): sözlükte olmayan bir taban adı sessizce
    // "band yok"a katlanırsa yeni bir taban sınıfı panoda GÖRÜNMEDEN doğar.
    const TABAN = { ampirik: ["AMPİRİK TABAN", "t-go"], literatur: ["LİTERATÜR TABANI", "t-vi"],
                    yok: ["BAND YOK", "t-no"] };
    const [tlbl, tkls] = TABAN[String(yr.taban || "")] || [String(yr.taban || "—"), "t-no"];
    const amp = kb.ampirik_bps;   // None ≠ 0: ölçülmemiş bandı "0,0 bps" basmak "maliyet yok" derdi
    // KAPALI ÖZET (v198): kartın sorusu "hangi VARSAYIMLA faturalıyoruz ve o varsayım sınandı
    // mı?" — değer yürürlükteki ek maliyet, çubuğun paydası ise ASGARİ ÖRNEKLEM (yükten okunur,
    // panoya sabit yazılmaz — C10). İlerleme çubuğu "ampirik taban ne kadar yaklaştı"yı söyler;
    // asgari yükte yoksa çubuk çizilmez.
    return `${bas}
      ${kartOzeti({
        deger: yr.ek_bps_giris == null ? null : `${trn(yr.ek_bps_giris, 2)} bps`,
        oran: (kb.min_n && kb.n_olculen != null) ? Math.min(1, kb.n_olculen / kb.min_n) : null,
        payda: kb.min_n ? `asgari örneklem (${trn(kb.min_n)} dolum · yükten)` : "",
        meta: yr.ek_bps_giris == null
          ? `yürürlükteki ek maliyet yükte yok — band ölçülemedi; taban ${esc(tlbl)}, ampirik ${trn(kb.n_dolan)} dolan satır.`
          : `taban ${esc(tlbl)} · ölçülmüş dolum ${trn(kb.n_olculen)}/${trn(kb.min_n)}${
              amp == null ? " · ampirik band henüz kurulmadı" : ` · ampirik ${trn(amp, 2)} bps`}`,
        degerSinif: String(yr.taban || "") === "yok" ? "warn" : "",
        rozet: String(yr.taban || "") === "yok" ? "BAND YOK" : (amp == null ? "AMPİRİK YOK" : "") })}
      <h3 class="t">Yürürlükteki band ${_chip(tlbl, tkls)}</h3>
      <div class="srow"><span>Ek maliyet <span class="tx3">(giriş bacağına)</span></span>
        <b class="mono-num">${trn(yr.ek_bps_giris, 2)} bps</b></div>
      <div class="srow"><span>Açılış spread'i</span>
        <b class="${yr.acilis_spread_bps == null ? "mut" : "mono-num"}">${yr.acilis_spread_bps == null
          ? "—" : trn(yr.acilis_spread_bps, 2) + " bps"}</b></div>
      <div class="srow"><span>Yürürlükteki slipaj modeli</span>
        <b class="mono-num">${trn(yr.yururlukteki_slippage_bps, 2)} bps</b></div>
      ${(yr.ampirik_n || 0) > 0 ? `<div class="srow"><span>Dosyadaki ampirik değer</span>
        <b class="mono-num">${trn(yr.ampirik_bps, 2)} bps · n=${trn(yr.ampirik_n)}</b></div>` : ""}
      <p class="hint">Kapsam: ${esc(yr.kapsam || "—")}. Kaynak: <code>${esc(yr.kaynak || "—")}</code></p>

      <h3 class="t" style="margin-top:16px">Ampirik ölçüm <span class="tx3">(E2 defterinden)</span></h3>
      <div class="srow"><span>Pencerede dolan satır</span><b class="mono-num">${trn(kb.n_dolan ?? 0)}</b></div>
      ${amp == null
        ? `<div class="srow"><span>Ampirik band</span>
             <b class="mut">${esc(kb.neden || "gerekçe alanı boş — yük nedenini yazmadı")}</b></div>
           <div class="srow"><span>İlerleme <span class="tx3">(asgari örneklem yükten)</span></span>
             <b class="mono-num">ölçülmüş dolum ${trn(kb.n_olculen ?? 0)} / asgari ${trn(kb.min_n)}</b></div>`
        : `<div class="srow"><span>Ampirik ek maliyet <span class="tx3">(dolum − resmî açılış, ort)</span></span>
             <b class="mono-num">${trn(amp, 2)} bps · n=${trn(kb.n_olculen ?? 0)}</b></div>
           <div class="srow"><span>Medyan · p90</span>
             <b class="mono-num">${trn(kb.medyan_bps, 2)} · ${trn(kb.p90_bps, 2)} bps</b></div>`}
      <p class="hint">Bu bir <b>ÖLÇÜMDÜR</b>, uygulama değil: ${esc(kb.uygulama || "—")} Bandı doldurmak
        <b>operatör eylemidir</b>; pano da analytics de kendi maliyet paydasını kendisi güncellemez.
        Asgari örneklem (${trn(kb.min_n)}) yükten okunur — panoya sabit yazılsaydı analytics'teki
        değişiklik ekrana yansımaz, pano eski asgariyi savunmayı sürdürürdü.</p></div>`;
  })();

  // ---------- İCRA GERÇEKLİĞİ · E4 GECE / GÜNDÜZ AYRIŞTIRMASI ----------------------------------
  // NEDEN AYRI KART: E2/E3 emrin FATURASINI ölçer; bu kart "kâr hangi bacaktan geldi?" diye sorar.
  // Girişler AÇILIŞTA olduğu için her işlem önce bir gece bacağı satın alır ve momentumun işareti
  // iki bacakta zıt olabilir — tek ortalamada toplanırlarsa birbirlerini yerler ve kart "yol" diye
  // tek bir sayı gösterip ayrışmayı gizlerdi.
  // TRAINING AYRI SATIR (BT-1 dersi): `replay_seed` tohum satırları KURALLARIN karakteridir, canlı
  // icra kanıtı DEĞİL. Canlı kâğıtla aynı hücrede toplanırlarsa hüküm tohumdan gelir ve öyle
  // göründüğü yerde de öyle okunmaz.
  // İNCE HÜCRE EŞİĞİ YÜKTEN (C10): `hucre_min_n` panoya sabit yazılmaz; ince hücrenin değeri
  // GİZLENMEZ, etiketlenir — saklamak "ölçüm yok" ile "az örneklem"i aynı kutuya koyardı.
  // None ≠ 0: `gece_payi` paydası (|gece|+|gündüz|) ~0 iken oran TANIMSIZdır; "%0" basmak "gece
  // bacağı yok" demek olurdu.
  const sGeceG = (() => {
    const gg = (d.icra || {}).gece_gunduz;
    const bas = `<div class="card rise"${katKart("mutabakat:gecegun")}><h2 class="t">Gece / gündüz ayrıştırması
      <span class="tx3" style="font-weight:400">(E4 · tutuş yolunun iki bacağı)</span></h2>`;
    if (!gg || !Object.keys(gg).length) return `${bas}
      ${kartOzeti({ deger: null, rozet: "ÖLÇÜLEMEDİ",
        meta: "teşhis yükünde <code>icra.gece_gunduz</code> yok — E4 ölçümü okunamadı (\"bacaklar dengeli\" DEĞİL)." })}
      <p class="hint"><span class="mut">Ölçüm okunamadı — E4 özeti teşhis yükünde yok
        (<code>icra.gece_gunduz</code>). Bu kutu <b>ölçüm YOK</b> demektir, "bacaklar dengeli"
        demek değildir.</span></p></div>`;
    // ÜÇ HÂL AYRI (`_gapRows` deseni): yük YOK (yukarısı) ≠ ölçülemedi (`neden_bos` — yük nedenini
    // KENDİ söyler) ≠ ölçüldü. Ortadaki hâlde tek bir bacak yüzdesi bile uydurulmaz.
    if (gg.neden_bos) return `${bas}
      ${kartOzeti({ deger: null, rozet: "ÖLÇÜLEMEDİ",
        meta: `${esc(gg.neden_bos)} · defterde ${trn(gg.n)} işlem, ${trn(gg.n_olculemeyen)} ölçülemeyen — bacak payı ÜRETİLMEZ.` })}
      <div class="srow"><span>Durum</span><b class="mut">${esc(gg.neden_bos)}</b></div>
      <div class="srow"><span>Defterdeki işlem · ölçülemeyen</span>
        <b class="mono-num">${trn(gg.n ?? 0)} · ${trn(gg.n_olculemeyen ?? 0)}</b></div>
      <p class="hint">Nedeni yük kendi söylüyor; pano ikinci bir açıklama uydurmaz. Ölçülemeyen
        defterden bacak payı ÜRETİLMEZ: "%50 gece" yazmak ölçülmemiş bir kırılımı ölçülmüş
        göstermek olurdu.</p></div>`;
    const gn = gg.genel || {};   // bacaklar KESİRDİR (0,02 = %2) — pctf yüzdeye çevirir
    const KAYNAK_TR = { training: "eğitim (tohum)", live_paper: "canlı kâğıt", belirsiz: "belirsiz" };
    const CAPKOL = "grid-template-columns:112px 74px 46px 1fr 1fr 1fr";
    // BİLİNMEYEN KAYNAK/DİLİM HAM BASILIR: yeni bir damga sınıfı sessizce "belirsiz"e katlanırsa
    // panoda GÖRÜNMEDEN doğar. `olculemedi` dilimi de ham durur — bir güne düşürülmez.
    const capRows = (gg.capraz || []).map(c => {
      const ince = c.yeterli === false;
      return `<div class="trow" style="${CAPKOL}${ince ? ";opacity:.55" : ""}">
        <span class="tick">${esc(KAYNAK_TR[String(c.kaynak || "")] || c.kaynak || "—")}</span>
        <span class="chain">${esc(c.tutus_dilimi || "—")}</span>
        <span class="mono-num num">${trn(c.n ?? 0)}</span>
        <span class="mono-num num">${pctf(c.gece, 2)}</span>
        <span class="mono-num num">${pctf(c.gunduz, 2)}</span>
        <span class="mono-num num">${pctf(c.islem, 2)}${ince
          ? ' <span class="mut">· ince</span>' : ""}</span></div>`;
    }).join("");
    // KAPALI ÖZET (v198): kartın sorusu "kâr hangi bacaktan geldi?" — değer GECENİN PAYI,
    // paydası ölçülebilen defter satırı. İki bacak ~0 ise pay TANIMSIZDIR ve çubuk çizilmez
    // (kartın kendi kuralı, özete aynen taşındı).
    return `${bas}
      ${kartOzeti({
        deger: gn.gece_payi == null ? null : pctf(gn.gece_payi, 2),
        oran: gn.gece_payi == null ? null : Math.max(0, Math.min(1, Number(gn.gece_payi))),
        payda: gn.gece_payi == null ? "" : `ölçülebilen işlem (${trn(gg.n)})`,
        meta: gn.gece_payi == null
          ? `iki bacak ~0 — gecenin payı tanımsız; defterde ${trn(gg.n)} işlem, ${trn(gg.n_olculemeyen)} ölçülemeyen.`
          : `gece ${pctf(gn.gece, 2)} · gündüz ${pctf(gn.gunduz, 2)} · icra farkı ${pctf(gn.icra_farki, 2)}${
              gg.n_olculemeyen ? ` · ${trn(gg.n_olculemeyen)} satır ölçülemedi` : ""}`,
        rozet: gn.gece_payi == null ? "PAY TANIMSIZ" : (azOrnek(gg.n) ? "AZ ÖRNEK" : "") })}
      <h3 class="t">Genel <span class="tx3">(ölçülebilen tüm satırlar)</span></h3>
      <div class="srow"><span>Gece bacağı <span class="tx3">(önceki kapanış → açılış)</span></span>
        <b class="mono-num">${pctf(gn.gece, 2)}</b></div>
      <div class="srow"><span>Gündüz bacağı <span class="tx3">(açılış → kapanış)</span></span>
        <b class="mono-num">${pctf(gn.gunduz, 2)}</b></div>
      <div class="srow"><span>Tutulan yol <span class="tx3">(gece + gündüz)</span></span>
        <b class="mono-num">${pctf(gn.yol, 2)}</b></div>
      <div class="srow"><span>İşlemin kendi getirisi <span class="tx3">(<code>pnl_pct</code>)</span></span>
        <b class="mono-num">${pctf(gn.islem, 2)}</b></div>
      <div class="srow"><span>İcra farkı <span class="tx3">(işlem − yol)</span></span>
        <b class="mono-num">${pctf(gn.icra_farki, 2)}</b></div>
      <div class="srow"><span>Gecenin payı <span class="tx3">(mutlak bacaklardan)</span></span>
        <b class="${gn.gece_payi == null ? "mut" : "mono-num"}">${gn.gece_payi == null
          ? "— iki bacak ~0, pay tanımsız" : pctf(gn.gece_payi, 2)}</b></div>
      <div class="srow"><span>Payda <span class="tx3">(sayaç, alarm değil)</span></span>
        <b class="mono-num">ölçülebilen ${trn(gg.n_olculebilir ?? 0)} · <span class="mut">ölçülemeyen
          ${trn(gg.n_olculemeyen ?? 0)}</span> · defterde ${trn(gg.n ?? 0)}</b></div>
      <p class="hint">Özdeşlik: <code>${esc(gg.ozdeslik || "—")}</code> — gündüz + gece TUTULAN YOLun
        tamamıdır, yaklaşık değil tam. <b>İcra farkı</b> = işlem − yol: çıkış seviyesi + friksiyon,
        yani tam olarak E1/E2'nin ölçtüğü şey. Üçü tek sayıda toplansaydı icra maliyeti piyasa
        hareketi gibi görünürdü. Yöntem: ${esc(gg.yontem || "—")}</p>

      <h3 class="t" style="margin-top:16px">Giriş gap'i</h3>
      <div class="srow"><span>Açılış − önceki kapanış</span><b class="mono-num">${fmtBps(gg.giris_gap_bps)}</b></div>
      <p class="hint">SATIN ALINAN gece bacağı — tutulan yolun <b>İÇİNDE DEĞİLDİR</b> (yol giriş
        açılışında başlar). E1'in limit tavanı tam olarak bu sayıyı kelepçeler; ikisi ayrı
        okunmazsa tavanın neyi kestiği görünmez.</p>
      ${capRows ? `<h3 class="t" style="margin-top:16px">Kaynak × tutuş dilimi</h3>
        <div class="tbl"><div class="trow head" style="${CAPKOL}">
          <span>KAYNAK</span><span>DİLİM</span><span class="num">N</span>
          <span class="num">GECE</span><span class="num">GÜNDÜZ</span><span class="num">İŞLEM</span></div>
        ${capRows}</div>
        <p class="hint"><b>eğitim (tohum)</b> satırları <code>replay_seed</code> damgalıdır: kuralların
          karakteridir, <b>canlı icra kanıtı değildir</b> — canlı kâğıtla aynı hücrede toplanmaz.
          Sönük satırlar <b>ince hücre</b>: n &lt; ${trn(gg.hucre_min_n)} (eşik yükten okunur, panoda
          sabit değil); değer gizlenmez, etiketlenir. <code>olculemedi</code> dilimi
          <code>bars_held</code> taşımayan satırların kovasıdır ve ham durur.</p>` : ""}</div>`;
  })();

  // ---------- BÖLÜM 2 · RİSK & REJİM KAPILARI ----------
  const regimes = ["trend_up", "trend_down", "chop", "high_vol"].map(r => {
    const live = reg.regime === r;
    const pct = live && bud != null ? Math.max(0, Math.min(100, bud)) : null;
    return `<div class="regrow${live ? " live" : ""}">
      <span class="nm">${esc(REGIME_TR[r] || r)}${live ? " · CANLI" : ""}</span>
      <span class="bar">${live && pct != null ? `<i style="width:${pct}%;background:var(--${pct <= 0 ? "sev-2" : "accent"})"></i>` : ""}</span>
      <b class="mono-num">${live ? (bud != null ? "%" + trn(bud) + (bud <= 0 ? " ·" : "") : "—") : "aktif değil"}</b></div>`;
  }).join("");
  const radar = rk.blackout_radar || {};
  const radarRows = (radar.blackout || []).map(b =>
    `<div class="trow" style="grid-template-columns:80px 1fr auto"><span class="tick">${esc(b.ticker)}</span>
     <span class="chain">rapor: ${esc(b.next_report || "?")}</span>${_chip((b.days_left != null ? b.days_left + " gün" : "—"), "t-rv")}</div>`).join("");
  const matrix = (gk.plans || []).map(pln => {
    const checks = pln.checks || [];
    const fails = checks.filter(c => !c.passed);
    const passHard = checks.filter(c => c.passed && c.severity === "hard");
    const passSoft = checks.filter(c => c.passed && c.severity === "soft");
    const chips = [
      ...passHard.map(c => `<span class="gc p" title="${esc(c.check)}: ${esc(String(c.value ?? ""))} ${esc(String(c.threshold ?? ""))}">${esc(CHECK_TR[c.check] || c.check)} ✓</span>`),
      ...fails.map(c => `<span class="gc f" title="${esc(c.note || "")}">${esc(CHECK_TR[c.check] || c.check)} ✗ ${c.value != null ? esc(String(c.value)) : ""}${c.threshold ? "·gerek " + esc(String(c.threshold)) : ""}</span>`),
      passSoft.length ? `<span class="gc p" title="${esc(passSoft.map(c => CHECK_TR[c.check] || c.check).join(", "))}">+${passSoft.length} soft ✓</span>` : "",
      pln.llm_opinion ? `<span class="gc ${pln.llm_veto ? "f" : "p"}" style="${pln.llm_veto ? "" : "background:var(--accent-tint);color:var(--accent-2)"}" title="danışma katmanı — ${pln.llm_veto ? "TERFİLİ veto: dolum düşürüldü" : "karara etkisiz (terfisiz)"}">LLM: ${esc(pln.llm_opinion)}${pln.llm_veto ? " → VETO" : ""}</span>` : "",
    ].filter(Boolean).join('<span class="gc arrow">→</span>');
    // HÜCRE BASILABİLİR (pano turu 2026-07-31, §3.0 ①): zincir çipleri kapının ÖZETİdir; hangi
    // ölçüt hangi değerle hangi eşiğe çarptı, plan hangi kurulum/skorla geldi — hepsi `gk.plans`
    // paketinde ZATEN var ve hiçbir yüzeyde okunmuyordu. Yeni uç İCAT EDİLMEDİ: çekmece aynı
    // satırın kendi verisinden kurulur (RECORD_VIEW.gate).
    const k = rec("gate", pln);
    return `<button ${rowAttrs(k, `${pln.ticker} · kapı ${pln.verdict || "?"} · ${fails.length} ölçüt kaldı. Karar ağacını aç.`)}
      class="trow rowbtn" style="grid-template-columns:110px 1fr;align-items:start;width:100%">
      <span><span class="tick">${esc(pln.ticker)}</span><br><span class="tag ${TAG[pln.verdict] || "t-vi"}" style="margin-top:4px">${esc(pln.verdict || "?")}</span>${pln.exploration ? " " + _chip("keşif", "t-rv") : ""}</span>
      <span class="gatechain">${chips || '<span class="chain">karar ağacı kaydı yok (eski plan)</span>'}</span></button>`;
  }).join("");
  // ---------- KAPILAR · BÖLÜM ÖZETİ · HÜCRE ŞERİDİ (v192) --------------------------------------
  // Bölümün dört sayısı dört ayrı yerde ve dört ayrı biçimdeydi: bütçe rejim satırının sonunda,
  // karartma sayısı bir cümlenin içinde, silahlanma ölçümü etiket-çiplerinde, plan sayısı bir
  // başlıkta. Hiçbirinin PAYDASI yazmıyordu — "3 kurulum kapı geçti" kaç kurulumdan? Şerit dördünü
  // aynı dille ve paydalarıyla açar; ayrıntı tabloları AŞAĞIDA aynen durur (yoğun-uzman düzeni).
  const _ar = (gk.arming || {}).measurements || {};
  const _arK = Object.keys(_ar);
  const _arGecen = _arK.filter(x => _ar[x].status === "gate_passed").length;
  const _radarN = (radar.blackout || []).length;
  const _radarEvren = Number(radar.known_tickers);
  const _planN = (gk.plans || []).length;
  const _planGO = (gk.plans || []).filter(p => p.verdict === "GO").length;
  const s2Ozet = ozetSerit([
    // BÜTÇE YALNIZ CANLI REJİM İÇİN TANIMLI: rejim okunamıyorsa hücre BOŞ çizilir, "%0" değil —
    // %0 bütçe GERÇEK bir hâldir (keşif moduna düşürür) ve "ölçemedik" ile aynı piksele düşemez.
    ozetHucre("Rejim bütçesi", {
      deger: bud == null ? null : "%" + trn(bud),
      oran: bud == null ? null : Math.max(0, Math.min(100, bud)) / 100,
      payda: "sermayenin tamamı (%100)",
      meta: `canlı rejim: <b>${reg.regime ? esc(REGIME_TR[reg.regime] || reg.regime) : "okunamadı"}</b>${
        bud != null && bud <= 0 ? ` · <span class="warn">keşif modu</span>` : ""}`,
      rozet: bud == null ? "ÖLÇÜLEMEDİ" : "" }),
    // TAKVİM BOŞSA SAYI BASILMAZ: "0 karartma" ile "takvim gelmedi" AYRI şeylerdir ve bu ayrım
    // aşağıdaki uyarı satırının zaten var olma sebebi.
    ozetHucre("Karartma radarı", {
      deger: radar.empty ? null : trn(_radarN),
      oran: (radar.empty || !Number.isFinite(_radarEvren) || !_radarEvren) ? null : _radarN / _radarEvren,
      payda: Number.isFinite(_radarEvren) && _radarEvren ? `takvimdeki sembol (${trn(_radarEvren)})` : "",
      meta: radar.empty ? "takvim BOŞ — FMP kotası bekleniyor; boş liste \"karartma yok\" DEĞİLDİR"
        : `bugün karartmada · takvimde ${trn(_radarEvren)} sembol`,
      rozet: radar.empty ? "ÖLÇÜLEMEDİ" : "" }),
    ozetHucre("Uyuyan kurulumlar", {
      deger: _arK.length ? `${trn(_arGecen)} / ${trn(_arK.length)}` : null,
      oran: _arK.length ? _arGecen / _arK.length : null,
      payda: `ölçülen uyuyan kurulum (${_arK.length})`,
      meta: _arK.length ? "silahlanma kapısını geçen · onay bekleyen"
        : "silahlanma ölçümü yükte yok — ölçüm YOK demektir, \"uyuyan kurulum yok\" demek değil",
      rozet: _arK.length ? "" : "ÖLÇÜLEMEDİ" }),
    ozetHucre("Karar ağacı", {
      deger: _planN ? `${trn(_planGO)} / ${trn(_planN)}` : null,
      oran: _planN ? _planGO / _planN : null, payda: `seansın planı (${_planN})`,
      meta: _planN ? `${esc(gk.date || "tarih yok")} · kapıdan geçen · üretilen plan`
        : "bu seans plan üretilmedi — kapının hüküm vereceği satır yok",
      rozet: azOrnek(_planN) && _planN ? "AZ ÖRNEK" : "" }),
  ], "Risk ve rejim kapılarının bölüm özeti");
  const s2 = `<div class="card rise"><h2 class="t">Bölüm 2 · Risk & rejim kapıları</h2>
    ${s2Ozet}
    ${regimes}
    <p class="hint">Bütçe yalnız CANLI rejim için tanımlıdır (rejim-koşullu motor) — diğer satırlar dürüstçe "aktif değil" der; %0 bütçe · keşif moduna düşer.</p>
    <h3 class="t" style="margin-top:16px">Karartma radarı</h3>
    ${radar.empty ? `<p class="hint warn">Takvim BOŞ — FMP kotası bekleniyor; boş liste "karartma yok" DEĞİLDİR.</p>`
                  : (radarRows || `<p class="hint">Bugün karartmada sembol yok (takvimde ${radar.known_tickers} sembol).</p>`)}
    ${(() => { const ar = (gk.arming || {}).measurements || {}; const keys = Object.keys(ar);
      if (!keys.length) return "";
      const ST = { gate_passed: ["KAPI GEÇTİ — onayın bekleniyor", "t-go"], gate_rejected: ["kapı reddetti", "t-no"],
                   gate_rejected_confirmation: ["onay yürüyüşü reddetti", "t-no"], insufficient_cf: ["kanıt birikiyor", "t-vi"] };
      const rows = keys.map(k => { const m = ar[k]; let [lbl, kls] = ST[m.status] || [m.status || "—", "t-vi"];
        let det = m.status === "insufficient_cf" ? `cf ${m.n ?? 0}/30${m.avg_r != null ? " · ort " + m.avg_r + "R" : ""}`
                  : `P ${m.search_p ?? "—"}${m.confirm_p != null ? " · onay " + m.confirm_p : ""}`;
        // "BİRİKİYOR" ile "HİÇ ÜRETİLMİYOR" AYRI ŞEYLER (2026-07-22). n=0 iken "kanıt birikiyor"
        // demek bir VAAT'tir; oysa o kurulum defterde tek satır bile üretmemişse birikecek bir şey
        // yoktur ve etiket sonsuza kadar aynı kalır. Aç bir mekanizma, sabırla karıştırılmamalı.
        if (m.status === "insufficient_cf" && !(m.n > 0)) {
          lbl = "HİÇ KANIT ÜRETİLMEDİ"; kls = "t-no";
          det = `cf 0/30 — bu kurulum defterde tek satır bile üretmedi (tarama koşuyor, ateşlemiyor)`;
        }
        return `<div class="trow" style="grid-template-columns:130px 1fr auto"><span class="tick">${esc(k)}</span>
          <span class="chain">${esc(det)}</span><span class="tag ${kls}">${esc(lbl)}</span></div>`; }).join("");
      // BAYATLIK: ölçüm haftalık koşuyor; defter yeniden tohumlandıysa ekrandaki sayı ESKİ dünyaya
      // ait olabilir. Sessizce göstermek, taze ölçümle aynı görünmesi demekti.
      const _ac = (gk.arming || {}).checked_at;
      const _yas = _ac ? Math.round((Date.now() - Date.parse(_ac)) / 3600000) : null;
      const _bayat = _yas != null && _yas >= 12
        ? ` <span class="warn" style="letter-spacing:0;text-transform:none;font-weight:400">— ${_yas} saat önce ölçüldü</span>` : "";
      return `<h3 class="t" style="margin-top:16px">Uyuyan kurulumlar · silahlanma ölçümü${_bayat}</h3>${rows}`; })()}
    <h3 class="t" style="margin-top:16px">Karar ağacı matrisi · ${esc(gk.date || "plan yok")}</h3>
    ${matrix || `<div class="empty">Bu seans plan üretilmedi — bir sonraki döngüde kapıdan geçiş anı burada satır satır görünür.</div>`}</div>`;

  // ---------- BÖLÜM 3 · MLOPS & HERMES ----------
  const diffs = (ml.recent_hypotheses || []).slice(-6).reverse().map(h => {
    const st = HSTATUS[h.status] || [h.status || "—", "s-rj"];
    return `<div style="border:1px solid var(--line);border-radius:var(--r-card);padding:10px 12px;margin-bottom:8px">
      <div style="display:flex;justify-content:space-between;gap:8px;margin-bottom:6px">
        <span class="chain">${esc(h.id || "")} · ${esc(h.variable || "?")}</span><span class="st ${st[1]}">${esc(st[0])}</span></div>
      <div class="mono" style="line-height:1.7;font-size:11px">
        <span style="background:var(--red-t);color:var(--red);padding:1px 8px;border-radius:var(--r-ctl);display:inline-block">− ${esc(h.variable || "")} = ${esc(String(h.old ?? "—"))}</span><br>
        <span style="background:var(--green-t);color:var(--green);padding:1px 8px;border-radius:var(--r-ctl);display:inline-block">+ ${esc(h.variable || "")} = ${esc(String(h.new ?? "—"))}</span></div>
      <div class="chain" style="margin-top:6px">arama Δ ${h.predicted_delta_search ?? "—"} → onay Δ ${h.predicted_delta ?? "—"}${h.realized_delta != null ? ` → gerçekleşen ${h.realized_delta}` : ""}</div>
      ${(() => {
        // DÜŞÜK-DSR GÖRSEL UYARISI (v130). Kâğıt modunda düşük DSR ship'i BLOKLAMIYOR (bilinçli:
        // kâğıt evrimi ölçüm aracıdır) — ama bloklamamak SUSMAK değildir. Bu satır olmadan "zayıf
        // istatistiksel kanıtla canlıya çıkmış sürümler" ancak kapı kaydı elle açılarak bulunurdu.
        // ÜÇ HÂL AYRI ÇİZİLİR: düşük (uyarı) · ölçülemedi (nötr, ASLA "iyi" değil) · geçer (sessiz,
        // çünkü kural sağlandığında satır eklemek gürültüdür).
        if (h.dsr_dusuk === true) return `<div class="chain" style="margin-top:4px"><span class="st s-rj">⚠ düşük DSR ${
          h.dsr != null ? trn(h.dsr, 6) : "—"} ≤ 0,95</span> <span class="mut">kâğıt modunda ship BLOKLANMADI (damga) — gerçek-para bağlamında RET olurdu</span></div>`;
        if (h.dsr_durum === "olculemedi") return `<div class="chain" style="margin-top:4px"><span class="st s-rb">DSR ölçülemedi</span> <span class="mut">seri tabanı altında ya da varyans sıfır — "iyi" DEĞİL, ölçüm YOK</span></div>`;
        return "";
      })()}</div>`;
  }).join("");
  const gc2 = ml.gate_calibration || {}, wu = ml.warmup || {}, sc2 = ml.score_calibration;
  const thermoPct = wu.every ? Math.round(100 * (wu.ticks || 0) / wu.every) : 0;
  const s3 = `<div class="card rise"><h2 class="t">Bölüm 3 · MLOps & Hermes</h2>
    <div class="g2">
      <div>
        <div class="gaugewrap">${_bullet({
          deger: ml.deflate ? ml.deflate.avg_deflation_pct : null,
          // ÖLÇEĞİN ÜST UCU BİRİMİYLE YAZILIR: çıplak "100" bir yüzde ekseninde birimsiz kalırdı
          // ve okuma ("%42,1") ile eksen farklı iki dilde konuşurdu.
          // D1 · deflasyon bir VERİ ÖLÇEĞİ okumasıdır, bir uyarı seviyesi değil: şiddet
          // kanalından çıkarıldı ve seri merdiveninin orta basamağına verildi.
          max: 100, olcek_ust: "%100", etiket: "deflasyon", renk: "violet",
          metin: ml.deflate ? "%" + trn(ml.deflate.avg_deflation_pct, 1) : null,
          // HEDEF YOK ve UYDURULMUYOR: deflasyonun "olması gereken" bir değeri tanımlı değil.
          // Karşılaştırma çizgisi çizmek, var olmayan bir eşiği varmış gibi göstermek olurdu.
          // Bantlar yalnız ölçeği okunur kılar (üçte bir dilimler), bir hüküm taşımaz.
          bantlar: [1 / 3, 2 / 3, 1],
          // MİNİ TREND GERÇEK SERİDEN (WP-P/P3): `analytics.deflate_stats` ship BAŞINA
          // `deflation_pct` taşıyor (`last`, son 8 kayıt, defter sırasında) ve bugüne dek
          // panoda hiç okunmuyordu — ortalama tek başına "arama iyimserliği artıyor mu
          // azalıyor mu" sorusunu cevaplayamaz. Seri YOKSA sparkline ÇİZİLMEZ (bkz. _bullet).
          seri: (ml.deflate && ml.deflate.last || []).map(r => r.deflation_pct)})}
          <span class="cap"><b>Model aşırı-güven sayacı</b><br>${ml.deflate
            ? `arama iyimserliğinin ort. %${trn(ml.deflate.avg_deflation_pct, 1)}'i onay yürüyüşünde törpülendi (${ml.deflate.n} ship)`
            : (() => {
                // BOŞ HALKANIN GEREKÇESİ ÖLÇÜLÜR. Eski metin "henüz ship yok — ilk ship'te dolar"
                // diyordu; bu, deflate==None'dan uydurulmuş bir gerekçe ve YANLIŞ vaatti (defterde
                // ship vardı, üstelik alan yalnız teyidi geçen ship yolunda yazılıyor).
                const w = ml.deflate_why || {};
                const n = w.n_hypotheses;
                if (n == null) return "hipotez sayısı ÖLÇÜLMEDİ — halkanın boş kalma gerekçesi bilinmiyor";
                if (!n) return "defterde hipotez yok — ilk aramada dolmaya başlar";
                const red = Object.entries(w.by_status || {}).filter(([s]) => s.startsWith("rejected"))
                  .sort((a, b) => b[1] - a[1]);
                if (!w.shipped) return `${n} hipotezin hiçbiri ship'e ulaşmadı — halka ancak teyit yürüyüşünü geçen bir aday ölçüldüğünde dolar`
                  + (red.length ? `<br><span class="chain">en sık eleme: ${esc(red[0][0])} (${red[0][1]})</span>` : "");
                if (w.legacy_ships) return `${w.shipped} ship var ama hepsi ölçüm alanı eklenmeden önce — bir SONRAKİ ship'te dolar`;
                return `${w.measured} ölçüm var ama oran hesaplanamadı (arama tahmini sıfır)`;
              })()}</span></div>
        <div class="srow" style="margin-top:10px"><span>Kapı meta-kalibrasyonu</span><b>${gc2.extra_p ? `<span class="warn">eşik +${gc2.extra_p}</span>` : "ayar yok"} · medyan ${gc2.median_ratio ?? "—"} · n=${gc2.n_measured ?? 0}</b></div>
        ${(() => { if (!sc2) return `<div class="srow"><span>Skor kalibrasyonu</span><b>örneklem &lt;30 — defter doluyor</b></div>`;
          if (!sc2.real) return `<div class="srow"><span>Skor kalibrasyonu</span><b>rank-IC ${sc2.rank_ic ?? "—"} · n=${sc2.n ?? "—"}</b></div>`;
          // "ANLAMLI DEĞİL" İLE "ANLAMLILIK ÖLÇÜLMEDİ" AYRI ŞEYLER (2026-07-26): tek bir doğruluk
          // sınaması ikisini de aynı uyarıya çeviriyordu. `false` bir ÖLÇÜM SONUCUDUR (baktık,
          // gürültüden ayrılmıyor); `null/undefined` ise hiç bakılmadığını söyler — ve ölçülmemiş
          // bir şeyi "gürültü" diye raporlamak, olmayan bir ölçümü olmuş göstermektir.
          const an = sc2.real.anlamli;
          const not = an === true ? "" : an === false
            ? ' · <span class="warn">gürültüden ayrılmıyor</span>'
            : ' · <span class="mut">anlamlılık ölçülmedi</span>';
          return `<div class="srow"><span>Skor kalibrasyonu</span><b>gerçek IC ${sc2.real.rank_ic} · n=${sc2.real.n}${not}${
            sc2.cf ? ` &nbsp;·&nbsp; cf IC ${sc2.cf.rank_ic} (n=${sc2.cf.n})` : ""}</b></div>`; })()}
        ${(() => { const ee = ml.exit_efficiency;
          return `<div class="srow"><span>Çıkış verimliliği (MFE)</span><b>${ee
            ? `masada ort ${trn(ee.avg_left_r, 2)}R · en kötü: ${esc(ee.worst_reason)} (${trn(ee.worst_left_r, 2)}R)${ee.nudge_active ? ' · <span class="warn">UCB dürtmesi AÇIK</span>' : ""}`
            : "örneklem <10 — MFE birikiyor"}</b></div>`; })()}
        ${(() => { const lc = ml.llm_calibration || {}; const bk = lc.buckets || {};
          const f = o => bk[o] ? `${o} ${bk[o].avg_r > 0 ? "+" : ""}${bk[o].avg_r}R·n${bk[o].n}` : null;
          const parts = [f("destekle"), f("çekimser"), f("karşı")].filter(Boolean);
          const cfp = lc.cf_pairs ? ` · sim ${lc.cf_pairs} çift` : "";
          return `<div class="srow"><span>LLM görüş kalibrasyonu</span><b>${parts.length ? parts.join(" · ") + (lc.promoted ? ' · <span class="pos">TERFİLİ</span>' : "") : (lc.n_pairs != null ? lc.n_pairs + " gerçek çift" : "görüş-sonuç çifti yok")}${cfp}</b></div>`; })()}
        ${(() => { const lc = ml.llm_calibration || {};
          // ÖNCÜ GÖSTERGE: çift sayısı kapanan işlem bekler, damgalama beklemez. Beyin 07-21..26
          // arası ölüyken üstteki satır "çift yok" diyordu ve bu, ölü damgalama ile dolan defteri
          // AYIRT EDEMİYORDU. Bu iki satır o ayrımı panoya taşır.
          return `<div class="srow"><span>Görüşlü plan</span><b>${lc.n_plans_with_opinion ?? "—"}</b></div>`
            + `<div class="srow"><span>Son görüş damgası</span><b>${lc.last_opinion_plan_date ? esc(lc.last_opinion_plan_date) : '<span class="warn">— hiç yok</span>'}</b></div>`; })()}
      </div>
      <div>
        <div class="thermo">
          <span class="tube"><i style="--fill:${(Number(thermoPct) || 0) / 100}"></i></span>
          <span class="cap"><b>Isınma termometresi</b><br>sprint döngüsü ${wu.ticks ?? 0}/${wu.every ?? "—"} poll
          ${wu.last
            ? `<br>son sprint: ${esc((wu.last.at || "").slice(11, 19))} · ${wu.last.evaluated ?? "?"} sonda${wu.last.best ? ` · en iyi: ${esc(wu.last.best)}` : ""}`
            : (() => {
                // "henüz sprint koşmadı" SIRADA demekti — oysa sprint elif zincirinin son dalı ve
                // önceki dallar sırayı sürekli tutuyorsa sayaç ASLA ilerlemez. Nedeni söyle.
                const S = { bg_reflect: "arka plan yansıması sırayı tutuyor — sprint sıra bulamıyor",
                            reflect: "gerçek yansıma koşuyor — sprint beklemede",
                            lock_busy: "yansıma kilidi başka bir işte — sprint atlandı",
                            learn_halted: "öğrenme duraklatıldı (operatör)", disabled: "sprint kapalı (MERIDIAN_WARMUP_SPRINTS=0)",
                            halted_or_stale: "HALT ya da bayat nabız — döngü beklemede" };
                if (!wu.polled) return "<br>döngü henüz ilk poll'unu yapmadı";
                return `<br>${wu.skip ? `<span class="warn">${esc(S[wu.skip] || wu.skip)}</span>` : "henüz sprint koşmadı"}`;
              })()}
          <br>ufuk: ${wu.horizon_ready ? '<b class="pos">DOLU — yansıma hazır</b>' : "birikiyor"}</span></div>
        <div class="srow" style="margin-top:10px"><span>UCB öncelik sırası</span><b class="chain">${(wu.ucb_top || []).slice(0, 3).map(esc).join(" → ") || "—"}</b></div>
        ${(() => { const ac = ml.agent_calls || {}; const used = ac.day ?? 0, cap = ac.rpd_limit ?? "—";
          const warn2 = cap !== "—" && used >= cap * 0.8;
          return `<div class="srow"><span>Ajan çağrı bütçesi (bugün)</span><b class="${warn2 ? "warn" : ""}">${used}/${cap} · dakikada ≤${ac.rpm_limit ?? "—"}</b></div>`; })()}
        ${(() => { const ag = ml.agent_skills || {}; const ok = ag.enabled != null && ag.linked === ag.enabled && !ag.stale_linked;
          return `<div class="srow"><span>Ajan skill kapsamı</span><b class="${ok ? "pos" : "warn"}">${ag.enabled != null ? `${ag.linked}/${ag.enabled} bağlı${ag.stale_linked ? ` · ${ag.stale_linked} bayat` : ""}${(ag.missing || []).length ? " · eksik: " + ag.missing.join(",") : ""}` : "—"}</b></div>`; })()}
      </div>
    </div>
    ${ml.gate_hist ? `<h3 class="t" style="margin-top:16px">Bootstrap çan eğrisi — ${esc(ml.gate_hist.id || "")} · ${esc(ml.gate_hist.variable || "")}</h3>${_bellSVG(ml.gate_hist)}`
                   : `<p class="hint" style="margin-top:12px">Çan eğrisi: olasılıksal kapının bir sonraki koşusunda burada çizilir (histogram hipotez kaydıyla taşınır).</p>`}
    ${diffs ? `<h3 class="t" style="margin-top:16px">Değişken diferansiyeli · son öneriler</h3>${diffs}` : ""}</div>`;

  // ---------- ÖZ-DEĞERLENDİRME · DİKKAT — KENDİ KARTI, ÖĞRENME'DE KALIR (S2R-3) --------------
  // ADR'nin S2R-2'ye bıraktığı içerik borcu #2. İki karar ayrı ayrı verildi:
  //
  // (1) KARTTAN AYRIŞTIRILDI. Blok "Bölüm 3 · MLOps & Hermes" kartının DİBİNDE, iki ızgara
  //     sütununun altında bir `<h3>` olarak duruyordu. Kartın başlığı ("MLOps & Hermes") onu
  //     ARAMAYACAĞIN bir yere koyuyordu: bir DİKKAT listesi, bir tesisat kartının alt başlığı
  //     olamaz. Kendi kartına çıktı — kart-içinde-kart değil, kartTAN ayrılma.
  //
  // (2) GÖZETİM'E TAŞINMADI ve bu ÖLÇÜLDÜ, varsayılmadı. `selfreview._attention()` sekiz kural
  //     ailesi üretir; altısı ÖĞRENME katmanının hükmüdür (skor kalibrasyonu IC'si, cf sadakati,
  //     kapının kendini sıkılaştırması, çıkış verimliliği, eşik-doldu ilerlemeleri, bekleyen
  //     revizyonlar, near-miss hipotez tohumları), yalnız ikisi sağlık sinyalidir (mekanizma
  //     kesintisi, bekçi olay sayısı). Ve o ikisinin Gözetim'de ZATEN bir evi var: mekanizma
  //     kesintisi `MECHANISM_STALE` alarmı üretir (selfreview.mechanism_failed) ve alarm gelen
  //     kutusunda okunur. Bloğu Gözetim'e taşımak, altı öğrenme hükmünü "sistem sağlıklı mı?"
  //     sorusunun altına gömer ve iki sağlık satırını İKİNCİ kez göstererek operatörün asıl
  //     şikâyetini ("aynı soruya iki yerden cevap") geri getirirdi.
  //     ⇒ Ev: Öğrenme · beyin bölümü. Gerekçe ADR Ek C'de yazılıdır.
  const sOzDeg = (() => {
    const sr = d.selfreview_summary;
    if (!sr) return "";           // uç servis etmiyor: uydurma "sistem sakin" kartı DOĞMAZ
    const att = (sr.attention || []).map(a => `<div class="trow" style="grid-template-columns:auto 1fr">
      <span class="tag ${a.sev === "yüksek" ? "t-no" : "t-rv"}">${esc(a.sev)}</span><span style="font-size:12px">${esc(a.why)}</span></div>`).join("");
    const con = (sr.contradictions || []).map(c => `<div class="trow" style="grid-template-columns:auto 1fr">
      <span class="tag t-vi">${esc(c.pair)}</span><span class="chain">${esc(c.detail)}</span></div>`).join("");
    return `<div class="card rise"><h2 class="t">Öz-değerlendirme · DİKKAT (${(sr.attention || []).length})</h2>
      <p class="hint" style="margin-top:0">Öğrenme katmanlarının KENDİ denetimi: kural-tabanlı, eşiği
        geçen maddeler (selfreview). Mekanizma kesintileri ayrıca <b>MECHANISM_STALE</b> alarmı üretir
        ve Gözetim &amp; Alarmlar'ın gelen kutusunda okunur — burada tekrarlanmaz.</p>
      ${att || '<p class="hint">Eşiği geçen dikkat maddesi yok — sistem sakin.</p>'}
      ${con ? `<h3 class="t" style="margin-top:16px">Katman çelişkileri (${sr.contradictions.length})</h3>${con}` : ""}</div>`;
  })();

  // ---------- EDGE SAĞLIĞI · DÖRT ÖLÇÜT (2026-07-27) ----------
  // Panonun cevaplaması gereken asıl soru "mekanizmalar koşuyor mu" değil "bir KENAR var mı ve
  // büyüyor mu". Dört ölçüt dört ayrı yere dağılmıştı; üçü hiçbir uçtan servis bile edilmiyordu.
  // Her satır KENDİ veri kaynağını yazar: gerçek/sim/karışım aynı yazı tipiyle yan yana durursa
  // okur hepsini "ölçüm" sanır — oysa sim ağırlıklı bir sayı gösterge olabilir, karar tabanı olamaz.
  const hist = ml.score_calibration_history || [], ph = ml.prediction_hit || {},
        br = ml.benchmark_relative, re3 = ml.regime_edge || {};
  const icBlok = (() => {
    if (!sc2) return `<div class="srow"><span>Gerçek dilim IC ${_chip("gerçek", "t-go")}</span>
      <b class="mut">ölçülmedi — skor→sonuç örneklemi &lt;30; defter doluyor</b></div>`;
    const r3 = sc2.real, an3 = r3 ? r3.anlamli : null;
    const not3 = !r3 ? "" : (an3 === true ? ' · <span class="pos">anlamlı</span>'
      : an3 === false ? ' · <span class="warn">gürültüden ayrılmıyor</span>'
      : ' · <span class="mut">anlamlılık ölçülmedi</span>');
    // İKİ AYRI ÖLÇÜLEMEYİŞ AYRI CÜMLEYLE SÖYLENİR: "örneklem yetmedi" sabırdır, "örneklem yetti ama
    // dilim yok" bir ARIZA işaretidir (rütbe değişimi olmadı ya da dosya ayrık ölçümden önce yazıldı).
    // İkisini tek metne sıkıştırmak, n_real=95 iken "&lt;30" yazan kendi kendini çürüten bir satır üretir.
    const nr = sc2.n_real ?? 0;
    // ÜÇ KATMAN ÜÇ SATIR (Aşama 1.1, 2026-07-28): cf dilimi bugüne kadar hiç AYRI gösterilmiyordu;
    // okur "gerçek 0.049 ama havuz -0.010" farkını görüp aradaki 2100 satırın ne yaptığını tahmin
    // etmek zorundaydı. Üçüncü satır o tahmini ölçüme çevirir. cf satırı SADAKAT uyarısını taşır:
    // o IC, canlı çıkış yasasının yalnız bir kısmıyla simüle edilmiş sonuçlardan gelir.
    const cf3 = (sc2.katmanlar || {}).cf || sc2.cf;
    return `<div class="srow"><span>Gerçek dilim IC ${_chip("gerçek", "t-go")}</span><b class="${r3 ? "" : "mut"}">${r3
        ? `${trn(r3.rank_ic, 4)} · n=${r3.n}${not3}`
        : (nr < 30 ? `ölçülmedi — gerçek dilim &lt;30 (n_real=${nr}); defter doluyor`
                   : `ölçülmedi — n_real=${nr} yeterli ama ayrık dilim yok: rütbe değişimi olmadı ya da kalibrasyon dosyası ayrıştırmadan ÖNCE yazılmış (bayat)`)}</b></div>
      <div class="srow"><span>cf dilim IC ${_chip("sim", "t-rv")}</span><b class="${cf3 ? "mut" : "mut"}">${cf3
        ? `${belirsiz(trn(cf3.rank_ic, 4), "SİM KÖKENLİ: bu IC karşı-olgusal (alınmamış) girişlerin "
            + "simüle sonuçlarından hesaplandı — canlı çıkış yasasının yalnız bir kısmı simüle edilir. "
            + "Kesik alt çizgi bunu söyler: bağlam, kanıt değil."
            + (cf3.sadakat ? ` Sadakat: ${cf3.sadakat}` : ""))} · n=${cf3.n}` : "ölçülmedi"}</b></div>
      ${cf3 && cf3.sadakat ? `<p class="hint" style="margin:-2px 0 6px">Sim dilimin sadakati: ${esc(cf3.sadakat)}.
        Bu satır <b>bağlamdır, kanıt değildir</b> — hüküm yalnız gerçek dilimden çıkar.</p>` : ""}
      <div class="srow"><span>Havuzlanmış IC ${_chip("karışım", "t-rv")}</span><b>${sc2.rank_ic != null
        ? belirsiz(trn(sc2.rank_ic, 4),
            `KARIŞIK KÖKEN: ${sc2.n_real ?? 0} gerçek + ${sc2.n_cf ?? 0} sim satır tek sayıya `
            + "havuzlandı ve sim tarafı paydayı domine ediyor. Hüküm YALNIZ gerçek dilimden çıkar; "
            + "bu satır bağlamdır.")
        : "ölçülmedi"}
        <span class="mut">(sim ağırlıklı, ${sc2.n_real ?? 0} gerçek / ${sc2.n_cf ?? 0} sim)</span></b></div>`;
  })();

  // ---------- BİLEŞEN IC TABLOSU (Aşama 1.2, 2026-07-28) ----------
  // "Skorun IC'si sıfır" ile "skorun hiçbir parçası bilgi taşımıyor" AYNI CÜMLE DEĞİLDİR. Dört
  // bileşen ayrı ayrı gösterilmezse ağırlıkları (entry.w_*) hangi yöne çevireceğimiz kanıta
  // bağlanamaz. Yalnız GERÇEK katman tablosu çizilir — cf ve havuz JSON'da durur ama panoda yan
  // yana konsaydı okur üçünü aynı ağırlıkta okurdu (havuzlanmış rakamın yıllarca tek görünen sayı
  // olması tam olarak böyle oldu).
  const cic = ml.component_ic || null;
  const cicBlok = (() => {
    if (!cic || !cic.tablo) return `<p class="hint">Bileşen IC'si henüz üretilmedi — ilk P5 turunda
      <code>state/component_ic.json</code> dosyasına yazılır. Boş tablo "bileşenler işe yaramıyor" DEĞİLDİR.</p>`;
    const hz = cic.horizons || [5, 10, 20];
    const kolonlar = `grid-template-columns:92px 56px 64px repeat(${hz.length},1fr)`;
    // HÜCRE ARTIK ARALIĞINI DA TAŞIR (2026-07-29): tek başına bir IC sayısı, n'i okurun kafasında
    // taşımasını bekler. Aralık sıfırı kapsıyorsa hücre SÖNÜK çizilir — "ölçtük ama gösteremedik"
    // ile "ölçtük ve bulduk" aynı görünmemeli.
    // ---- 2C EMPİRİK-BAYES SÜTUNU (WP-M, 2026-08-01) — HÜCRENİN İÇİNDE, HAM SAYININ ALTINDA ----
    // `component_ic.json` artık `eb` adlı PARALEL bir sütun taşıyor ve panoda hiç görünmüyordu.
    // Küçültülmüş ikiz AYRI BİR TABLOYA konmadı: iki tablo, aynı hücrenin iki sayısını okurun
    // kafasında eşleştirmesini isterdi (bu kartın kendi tarihindeki "havuzlanmış rakam tek görünen
    // sayı oldu" kusurunun aynısı). Ham sayı BÜYÜK ve renkli kalır, EB ikizi onun ALTINDA sönük
    // durur — çünkü bugün eb HÜKME GİRMEZ, yalnız "bu sayı ne kadar gürültüydü"yü söyler.
    // BLOK YOKSA HÜCREDE HİÇBİR ŞEY YAZILMAZ (ve sebebi tablonun altındaki özet satırında durur):
    // hücreye "eb yok" basmak, ölçülmemiş bir şeyi her satırda tekrarlayan bir gürültü olurdu.
    const ebKatman = lay => (((cic.eb || {}).katmanlar || {})[lay] || {}).hucreler || null;
    const hucre = (tbl, c, h, lay) => {
      const cell = ((tbl[c] || {})[String(h)]) || {};
      if (cell.ic == null) return `<span class="mono-num num mut">— <span style="font-size:10px">(${esc(cell.neden || "ölçülmedi")})</span></span>`;
      const ci = cell.ci;
      const ebh = (ebKatman(lay) || {})[`${c}@${h}`];
      // `eb_ic` null olabilir (hücre küçültülemedi) — o zaman ikiz satırı da düşer.
      const ebYazi = ebh && ebh.eb_ic != null
        ? `<span class="mut" style="font-size:10px;display:block">EB ${(ebh.eb_ic > 0 ? "+" : "") + trn(ebh.eb_ic, 3)}${
            ebh.shrink_katsayisi != null ? ` · w=${trn(ebh.shrink_katsayisi, 2)}` : ""}</span>`
        : "";
      return `<span class="mono-num num ${cell.anlamli ? cls(cell.ic) : "mut"}">${(cell.ic > 0 ? "+" : "") + trn(cell.ic, 3)}
        ${ci ? `<span class="mut" style="font-size:10px">[${trn(ci.lo, 2)},${trn(ci.hi, 2)}]</span>` : ""}${ebYazi}</span>`;
    };
    const satir = (lay, c, etiket) => {
      const tbl = cic.tablo[lay] || {};
      const n0 = ((tbl[c] || {})[String(hz[0])] || {}).n;
      return `<div class="trow" style="${kolonlar}">
        <span class="tick">${esc(c)}</span>
        <span>${etiket}</span>
        <span class="mono-num num mut">n=${n0 ?? "—"}</span>${hz.map(h => hucre(tbl, c, h, lay)).join("")}
        </div>`; };
    // EB ÖZET SATIRI — DIŞ OKUYUCUDAN (YASA 6). Hücrelerdeki ikizler tablonun KENDİ `eb` bloğundan
    // geliyor; bu satır ise `analytics.shrunk_component_ic().tablo_ici_eb` okuyucusundan gelir ve
    // "blok var mı, kaç hücre küçüldü, en çok hangi hücre çekildi" sorularını cevaplar. İkisi AYNI
    // hesaptır (test_C_iki_cetvel_YOK...) — ayrışırlarsa aynı adı taşıyan iki sayı doğardı.
    const ebOzet = (() => {
      const t = ((ml.shrunk_component_ic || {}).tablo_ici_eb) || null;
      if (!t) return `<p class="hint"><b>EB sütunu:</b> okuyucu servis edilmiyor —
        <code>/api/diagnostics</code> <code>shrunk_component_ic.tablo_ici_eb</code> alanı boş.</p>`;
      if (!t.var) return `<p class="hint"><b>EB sütunu:</b> <span class="mut">henüz üretilmedi</span> —
        ${esc(t.neden || "")}. Bu bir arıza değil, dosyanın YAŞIDIR; "küçültme yok" diye okunamaz
        (ölçülmemiş bir küçültmeyi 0 diye raporlamak uydurma olurdu).</p>`;
      const e = t.en_cok_cekilen || null;
      return `<p class="hint"><b>EB sütunu</b> ${_chip("HÜKÜM VERMEZ", "t-rv")} — gerçek katmanda
        ${t.n_hucre ?? "—"} hücre${t.kucultuldu ? "" : " (küçültme YAPILMADI)"}${
        t.kucultuldu ? `, ortak ortalama ${trn(t.genel_ortalama, 4)} · τ²=${trn(t.tau2, 5)}` : ""}.
        ${t.neden ? esc(t.neden) + " " : ""}${e ? `En çok çekilen hücre <code>${esc(e.hucre)}</code>:
        ham ${trn(e.ham_ic, 3)} → EB ${trn(e.eb_ic, 3)} (çekim ${trn(e.cekim, 3)} · w=${trn(e.shrink_katsayisi, 2)} · n=${e.n ?? "—"}).` : ""}
        <br><span class="mut">${esc(t.yontem || "")}</span></p>
      <p class="hint">Hücrelerdeki <b>EB</b> ikizi ham sayının ALTINDA sönük durur çünkü ham <code>ic</code>
        alanları <b>bit-bit değişmedi</b> ve bugünün okuyucuları (beyin özeti, yeniden-üretim farkı, hükümler)
        HAM ic okumaya devam ediyor. <code>w</code> hücrenin KENDİ tahminine verilen ağırlıktır:
        w=1 hiç küçültme, w=0 tam küçültme. ${esc(t.kapsam || "")}</p>`;
    })();
    const komp = cic.components || [];
    // CF SATIRLARI AYRI VE "SIM" ETİKETLİ (Aşama 1.4 karar girdisi, 2026-07-29). Gerekçe kodda
    // yazılı (component_ic modül başlığı, karar 4): bu tablonun y ekseni cf'in kirli çıkış
    // simülasyonundan DEĞİL, barlardan gelir — cf'ten alınan tek şey giriş anıdır. Bu yüzden n≈2100
    // burada kullanılabilir; ama satırlar gerçek katmanla AYNI KEFEYE konmaz, altında ve etiketli durur.
    return `<div class="tbl"><div class="trow head" style="${kolonlar}">
        <span>BİLEŞEN</span><span>KATMAN</span><span class="num">ÖRNEKLEM</span>${hz.map(h => `<span class="num">${h} BAR</span>`).join("")}</div>
      ${komp.map(c => satir("gercek", c, _chip("gerçek", "t-go"))).join("")}
      ${komp.map(c => satir("cf", c, _chip("sim", "t-rv"))).join("")}</div>
      <p class="hint" style="margin-top:8px">İleri getiri: <code>${esc(cic.getiri_tanimi || "")}</code> ·
      aralık: ${esc(cic.ci_yontem || "")} · ağırlıklar: ${komp.map(c => `${esc(c)} ${trn((cic.agirliklar || {})[c], 2)}`).join(" · ")}.
      <b>${esc(cic.verdict || "")}</b></p>
      <p class="hint"><b>sim satırları neden burada:</b> ${esc(cic.cf_katman_gerekce || "")} —
      gerçek katmanda n≈${cic.n_gozlem ? cic.n_gozlem.gercek : "—"}, sim katmanında n≈${cic.n_gozlem ? cic.n_gozlem.cf : "—"};
      1.4 karar kapısının cevaplanabilmesi için gereken örneklem yalnız sim tarafında var. Yine de bunlar
      <b>alınmamış</b> hipotetik girişlerdir (seçim yanlılığı ayrı bir soru) ve kanıt değil <b>bağlam</b>dır.</p>
      <p class="hint">Aralık varsayımı: ${esc(cic.ci_varsayim || "")}. Sönük yazılan hücrelerde aralık
      sıfırı kapsıyor — bir bileşenin IC'si <b>ağırlığıyla ters işaretli</b> görünse bile önce aralığa bakılır;
      bu tablo hipotez ÜRETİR, karar vermez.</p>
      ${ebOzet}`;
  })();
  const reRows = Object.entries(re3)
    .filter(([k, v]) => k !== "_kaynak" && v && typeof v === "object")
    .sort((a, b) => (b[1].n || 0) - (a[1].n || 0))
    .map(([k, v]) => `<div class="trow" style="grid-template-columns:130px 64px 84px 1fr">
      <span class="tick">${esc(REGIME_TR[k] || k)}</span>
      <span class="mono-num num">n=${v.n ?? 0}</span>
      <span class="mono-num num ${cls(v.avg_r)}">${v.avg_r != null ? (v.avg_r > 0 ? "+" : "") + trn(v.avg_r, 3) + "R" : "—"}</span>
      <span class="chain">kazanç ${v.win_rate != null ? pctf(v.win_rate, 1) : "—"}${(v.n ?? 0) < 20
        ? ' · <span class="guven">ince örneklem (n&lt;20 — yön okunmaz)</span>' : ""}</span></div>`).join("");
  const reKaynak = (re3._kaynak || {}).source;
  // HÜKÜM SATIRI — KARTIN EN ÜSTÜNDE (2026-07-27). Dört ölçütü yan yana koyup birleştirmeyi okura
  // bırakmak, her bakışta yeniden yapılan ve her seferinde farklı çıkabilen bir işlemdir. Hüküm
  // sunucuda (analytics.edge_verdict) tek yerde yazılı eşiklerden türer; burada YALNIZ gösterilir —
  // panoda ikinci bir eşik hesabı olsaydı iki farklı gerçek doğardı.
  // TON KURALI: yeşil kutlama YALNIZ 4/4'te. Ölçülemeyen varken ton `warn`dır ve cümle ölçülemeyeni
  // açıkça sayar — "henüz bilmiyoruz" ile "kenar yok" aynı renge boyanamaz.
  // DÖRDÜNCÜ DURUM: ZAYIF (2026-07-29). Eşiği geçip istatistiksel anlamlılığı geçemeyen ölçüt ne
  // yeşil ne kırmızıdır — 0.0492'lik bir IC eşiğin (0.03) üstündedir ama n=95'te gürültüden ayırt
  // edilemez. Sunucu bunu `status:"zayif"` / `durum:"ZAYIF"` olarak veriyor; buradaki tek iş onu
  // AYRI BİR TONDA göstermek. Ara ton (amber) bilinçli: yeşile boyamak ölçülmemiş bir kesinlik,
  // kırmızıya boyamak ise ölçülmüş bir başarısızlık iddia ederdi.
  const ev = ml.edge_verdict || null;
  // PAYDA 5 (Hafta 3a): kuzey yıldızına beşinci ölçüt (KUYRUK) eklendi. `4` sabitleri burada elle
  // güncellendi — sunucu paydayı `len(criteria)`den türetiyor, pano ise ton kuralını sabit yazıyordu.
  const evTon = !ev ? "mut"
    : ev.passed === 5 ? "pos"
    : ev.zayif ? "warn"
    : ev.unmeasured ? "warn"
    : "neg";
  const DURUM_TON = { SAGLANDI: "pos", ZAYIF: "warn", SAGLANMADI: "neg", OLCULEMEDI: "mut" };
  // BEŞİNCİ ÖLÇÜT KUYRUK (3A, Hafta 3a 2026-07-30): ilk dördü "seçim doğru mu?"nun türevleriydi;
  // kuyruk "sermaye hayatta kalır mı?" sorusunu sorar (gerçekleşen maks düşüş + işlem-R CVaR%5).
  // Kapı yasası kuyruğu 2026-07-22'den beri VETO olarak taşıyordu, kuzey yıldızı hiç görmüyordu.
  const OLCUT_ADI = { skor_sonuc: "1 · skor→sonuç", spy_ustu: "2 · SPY-üstü",
                      tahmin_isabeti: "3 · tahmin", rejim_edge: "4 · rejim",
                      kuyruk: "5 · kuyruk" };
  // ÖLÇÜT ŞERİDİ: dört durumu tek satırda gösterir. Aşağıdaki bölümler ölçütleri kendi ham
  // alanlarından çiziyor (tarihsel sebep); şerit ise HÜKMÜN kendi `criteria` çıktısını okur —
  // yani kartın üstündeki cümle ile aşağıdaki satırların aynı kaynaktan geldiği görünür olur.
  const evSerit = (() => {
    if (!ev || !ev.criteria) return "";
    return `<div class="srow" style="margin-top:2px"><span class="mut">ölçüt durumları</span>
      <b>${Object.entries(ev.criteria).map(([k, c]) =>
        `<span class="${DURUM_TON[c.durum] || "mut"}" style="margin-left:10px">${esc(OLCUT_ADI[k] || k)}
         <b class="${DURUM_TON[c.durum] || "mut"}">${esc(c.durum || "?")}</b></span>`).join("")}</b></div>`;
  })();
  const evSatir = `<div class="srow" style="margin-top:2px"><span>HÜKÜM ${_chip(ev ? `${ev.passed}/5 geçti` : "hüküm yok", "t-rv")}</span>
    <b class="${evTon}">${ev ? esc(ev.verdict) : "hüküm üretilmedi — /api/diagnostics edge_verdict alanı boş"}</b></div>
    ${evSerit}
    ${ev && ev.zayif ? `<p class="hint" style="margin-top:4px"><b class="warn">ZAYIF</b> = eşik geçildi <b>ama</b> istatistiksel
      anlamlılık yok (güven aralığı sıfırı kapsıyor). SAĞLANDI artık ikisini BİRDEN ister; zayıf bir ölçüt paydaya girer,
      paya girmez — kuzey yıldızı gürültüyle yanamaz.</p>` : ""}
    ${ev && ev.unmeasured ? `<p class="hint" style="margin-top:4px">${ev.unmeasured} ölçüt <b>ölçülemedi</b> (örneklem eşiği dolmadı) —
      bu bir başarısızlık DEĞİL, henüz cevaplanmamış bir sorudur; aşağıdaki satırlar hangisi olduğunu söyler.</p>` : ""}`;
  // KAPALI ÖZET (v198): kuzey yıldızının kendi paydası zaten beş — çubuk onu okur, uydurma bir
  // tavan kurmaz. ÖLÇÜLEMEYEN ölçüt sayısı meta'da ADIYLA durur: "3/5 geçti" cümlesi, ikisinin
  // ölçülemediği bilgisinden koparılırsa bir başarısızlık gibi okunur (kartın kendi şerhi).
  const sEdge = `<div class="card rise"${katKart("bilesenic:edge")}><h2 class="t">Edge sağlığı · beş ölçüt</h2>
    ${kartOzeti(!ev ? {
      deger: null, rozet: "ÖLÇÜLEMEDİ",
      meta: "/api/diagnostics <code>edge_verdict</code> alanı boş — hüküm üretilmedi (0/5 geçti DEĞİL)." }
    : { deger: `${ev.passed}/5`, oran: ev.passed / 5, payda: "ölçüt (kuzey yıldızı)",
        degerSinif: ev.zayif || ev.unmeasured ? "warn" : "",
        meta: `${esc(ev.verdict || "")}${ev.unmeasured ? ` · ${ev.unmeasured} ölçüt ölçülemedi` : ""}${
          ev.zayif ? " · zayıf ölçüt var" : ""}`,
        rozet: ev.unmeasured ? "ÖLÇÜLEMEYEN VAR" : (ev.zayif ? "ZAYIF" : "") })}
    ${evSatir}
    <p class="hint">Her ölçütün yanında VERİ KAYNAĞI durur: <b>gerçek</b> = kapanmış canlı işlem · <b>sim</b> = karşı-olgusal defter
    (alınmamış hipotetik giriş) · <b>karışım</b> = ikisi tek havuzda. Ölçülmemiş olan "0" değil <b>ölçülmedi</b> yazar.</p>
    <h3 class="t" style="margin-top:14px">1 · Skor → sonuç (rank-IC)</h3>
    ${icBlok}
    <div class="srow"><span>IC trendi <span class="mut">(${icEfsane()} ·
      ${hist.length} nokta, günde bir)</span></span>${icTrend(hist)}</div>
    <h3 class="t" style="margin-top:16px">2 · SPY-üstü (alfa değil beta mı?)</h3>
    <div class="srow"><span>Fazla getiri <span class="mut">(ham)</span> ${_chip("gerçek", "t-go")}</span><b class="${br ? (br.beat_benchmark ? "pos" : "neg") : "mut"}">${br
      ? `${br.excess_return > 0 ? "+" : ""}${pctf(br.excess_return, 2)} · strateji ${pctf(br.strategy_return, 2)} vs ${esc(br.benchmark || "SPY")} ${pctf(br.benchmark_return, 2)}
         <span class="mut">(${esc(br.start || "")} → ${esc(br.end || "")})</span>`
      : "ölçülmedi — 5'ten az kapanmış işlem ya da endeks verisi yok"}</b></div>
    ${(() => {
      // MARUZİYET DÜZELTMESİ (S3C, 2026-07-29) — HÜKMÜN OKUDUĞU SATIR BUDUR. Ham fark, parası
      // SÜREKLİ piyasada duran bir SPY tutucusuyla kıyas yapar; strateji ise sermayesinin bir
      // kısmını, zamanın bir kısmında taşır. Boğada bu stratejiye hak etmediği bir ceza, düşüşte
      // hak etmediği bir başarı yazar. Ham satır üstte KALIR (geriye dönük okunabilirlik), ama
      // ölçütün durumu bu satırdan gelir.
      if (!br) return "";
      const adj = br.exposure_adjusted_excess, ci = br.ci, mz = (br.maruziyet || {}).oran;
      if (adj == null) return `<p class="hint">Maruziyet-düzeltilmiş fark <b>ölçülemedi</b>${
        (br.maruziyet || {}).neden ? ` — ${esc(br.maruziyet.neden)}` : ""}; ham fark düzeltilmiş gibi sunulmaz.</p>`;
      return `<div class="srow"><span>Maruziyet-düzeltilmiş ${_chip("hüküm bunu okur", "t-rv")}</span>
        <b class="${br.anlamli ? (adj > 0 ? "pos" : "neg") : "warn"}">${adj > 0 ? "+" : ""}${pctf(adj, 2)}
          <span class="mut">· maruziyet ${pctf(mz, 1)}${ci ? ` · %95 CI [${pctf(ci.lo, 2)}, ${pctf(ci.hi, 2)}]` : ""}
          ${br.anlamli ? "" : " · <span class=\"warn\">aralık sıfırı kapsıyor</span>"}</span></b></div>
        <p class="hint">getiri − (ortalama maruziyet × SPY getirisi). Maruziyet = ${esc((br.maruziyet || {}).yontem || "")}.
        Aralık kapsamı: ${esc(br.ci_kapsam || "")}.</p>`;
    })()}
    <h3 class="t" style="margin-top:16px">3 · Tahmin isabeti (öğrenmenin kapanan ucu)</h3>
    <div class="srow"><span>İşaret tutturma ${_chip("gerçek", "t-go")}</span><b class="${ph.n ? "" : "mut"}">${ph.n
      ? `${ph.sign_hits}/${ph.n} tahmin işareti tuttu · ort. |hata| ${trn(ph.mean_abs_err, 4)}`
      : "ölçülmedi — ilk terminal hipotez bekleniyor (tahmin VE gerçekleşen birlikte gerekir)"}</b></div>
    <h3 class="t" style="margin-top:16px">4 · Rejim başına edge ${_chip(reKaynak || "kaynak damgasız", "t-rv")}</h3>
    ${reRows ? `<div class="tbl"><div class="trow head" style="grid-template-columns:130px 64px 84px 1fr">
        <span>REJİM</span><span class="num">ÖRNEKLEM</span><span class="num">ORT. R</span><span>KAZANÇ ORANI</span></div>${reRows}</div>`
      : `<p class="hint">regime_edge.json henüz üretilmedi — ilk P5 turunda dolar; boş liste "edge yok" DEĞİLDİR.</p>`}
    <h3 class="t" style="margin-top:16px">5 · Kuyruk (sermaye hayatta kalır mı?) ${_chip("gerçek", "t-go")}</h3>
    ${(() => {
      // İKİ BACAK, İKİSİ BİRDEN GEREKİR. Maks düşüş YOL riskini ölçer (sıralanmış kayıpların
      // bileşiği), CVaR%5 BİRİM riskini (tek işlemin en kötü %5'i risk birimini aşıyor mu). Bir
      // sistem stop disiplinini kusursuz uygulayıp yine de üst üste kayıplarla derin düşebilir.
      // İKİ EĞRİ YAN YANA DURUR: kapanmış-işlem eğrisi açık pozisyon düşüşünü GİZLER (denetim #6)
      // ve canlıda fark büyük — %5,70 vs %8,04. Hüküm KÖTÜ olanı okur; ikisini de göstermek
      // "eşiği geçtik sanmak" ile "eşiği geçtik" arasındaki farkı görünür kılar.
      const k = ev && ev.criteria ? ev.criteria.kuyruk : null;
      if (!k) return `<p class="hint">Kuyruk ölçütü henüz servis edilmiyor.</p>`;
      const es = k.esikler || {};
      return `<div class="srow"><span>Maks düşüş <span class="mut">(eşik ${pctf(es.max_dd, 0)})</span></span>
          <b class="${k.max_dd == null ? "mut" : (k.dd_bacagi === true ? "pos" : k.dd_bacagi === false ? "neg" : "mut")}">${
          k.max_dd == null ? "ölçülmedi" : `${pctf(k.max_dd, 2)}
            <span class="mut">· kapanmış ${pctf(k.kapali_islem_dd, 2)} / günlük M2M ${pctf(k.gunluk_m2m_dd, 2)} — KÖTÜ olan okunur</span>`}</b></div>
        <div class="srow"><span>İşlem-R CVaR%5 <span class="mut">(taban ${trn(es.cvar5_r, 1)}R)</span></span>
          <b class="${k.cvar5_r == null ? "mut" : (k.cvar_bacagi === true ? "pos" : k.cvar_bacagi === false ? "neg" : "mut")}">${
          k.cvar5_r == null ? "ölçülmedi" : `${trn(k.cvar5_r, 3)}R
            <span class="mut">· VaR%5 ${trn(k.var5_r, 3)}R · en kötü ${trn(k.en_kotu_r, 3)}R · kuyrukta ${k.kuyruk_n ?? "—"} işlem</span>`}</b></div>
        <p class="hint">İşaret GETİRİ yönünde (negatif = kayıp) — kapı vetosundaki <code>score.tail_risk</code>
          POZİTİF kayıp büyüklüğü ve 20 işlemlik UFUK kullanır; bu satır TEK işlemin gerçekleşen R dağılımıdır.
          Boyutlayıcı adedi <code>risk_$/(giriş−stop)</code> diye kurar, yani stopa uyulan çıkış tam −1,0R'dir;
          taban −1,5R risk biriminin yarısı kadar boşluk/kayma hasarına izin verir.
          ${(k.n ?? 0) < (es.n_min ?? 40) ? `<b class="warn">n=${k.n ?? 0} &lt; ${es.n_min} — hüküm OLCULEMEDI.</b>` : ""}</p>`;
    })()}
    <h3 class="t" style="margin-top:18px">Bileşen IC · skorun dört ham parçası ${_chip("gerçek", "t-go")}</h3>
    ${cicBlok}
    <h3 class="t" style="margin-top:18px">min_score eşik eğrisi · kapıyı yükseltmek kâr getirir mi?</h3>
    ${(() => {
      // AŞAMA 1.3 (2026-07-29). Bu eğri SEÇİM etkisini ölçer ("eşiği yükseltseydik geçen adayların
      // ortalaması ne olurdu?"), SİSTEM etkisini değil ("eşiği yükseltseydik sistem ne yapardı?").
      // İkisi ayrışabilir ve 07-28'de ayrıştı: H2 (60→80) tam replay'de Δ-0.095 ile ÇÜRÜDÜ.
      // Çapraz not sayının YANINDA durur — yoksa tablo, kapıyı yükseltmek için bir davetiye gibi okunur.
      const tc = ml.threshold_curve || null;
      if (!tc || !tc.egri) return `<p class="hint">Eşik eğrisi henüz üretilmedi — ilk P5 turunda
        <code>state/threshold_curve.json</code> dosyasına yazılır.</p>`;
      const kol = "grid-template-columns:64px 60px 70px 128px 1fr";
      const satirlar = (lay, etiket) => (tc.egri[lay] || []).map(p => {
        const r = p.gerceklesen_r || {}, ci = r.ci;
        const canli = p.esik === tc.canli_min_score;
        return `<div class="trow" style="${kol}">
          <span class="tick">${p.esik}${canli ? ' <span class="warn" style="font-size:10px">CANLI</span>' : ""}</span>
          <span>${etiket}</span>
          <span class="mono-num mut">${p.n_aday}</span>
          <span class="mono-num ${r.ort == null ? "mut" : cls(r.ort)}">${r.ort == null
            ? `— <span style="font-size:10px">(${esc(r.neden || "ölçülmedi")})</span>`
            : `${r.ort > 0 ? "+" : ""}${trn(r.ort, 3)}R`}</span>
          <span class="chain">${ci ? `CI [${trn(ci.lo, 2)}, ${trn(ci.hi, 2)}]` : "aralık yok"} ·
            ileri getiri 10 bar ${((p.ileri_getiri || {})["10"] || {}).ort == null ? "—"
              : pctf(p.ileri_getiri["10"].ort, 2)} · aday oranı ${pctf(p.aday_orani, 0)}</span></div>`;
      }).join("");
      return `<div class="tbl"><div class="trow head" style="${kol}">
          <span>EŞİK</span><span>KATMAN</span><span>ADAY</span><span>ORT. R</span><span>ARALIK / İLERİ GETİRİ</span></div>
        ${satirlar("gercek", _chip("gerçek", "t-go"))}
        ${satirlar("cf", _chip("sim", "t-rv"))}</div>
        <p class="hint" style="margin-top:8px"><b>${esc(tc.verdict || "")}</b></p>
        <p class="hint"><b>Çapraz not:</b> ${esc(tc.capraz_not || "")}</p>
        <p class="hint">${esc(tc.cf_sadakat || "")} · ölçülebilir hücre için en az ${tc.min_n ?? "—"} gözlem.</p>`;
    })()}
    <h3 class="t" style="margin-top:18px">OOS aşınması · aynı sınav kaç kez soruldu?</h3>
    ${(() => {
      // AŞINMA SATIRI HÜKMÜN ÖMRÜNÜ SÖYLER: "OOS'ta kazandı" cümlesinin değeri, o pencereye kaç kez
      // sorulduğuna bağlıdır. Sayaç bugünden başlar (retro damga yasağı) ve bunu AÇIKÇA yazar —
      // düşük bir sayı "aşınma yok" değil "ölçmeye yeni başladık" demektir.
      const er = ml.oos_erosion || null;
      if (!er) return `<p class="hint">Aşınma defteri henüz servis edilmiyor.</p>`;
      const en = er.en_cok, q = en ? en.queries : null, lim = er.limit;
      const asir = q != null && q > lim;
      return `<div class="srow"><span>En çok sorulan pencere</span><b class="${asir ? "warn" : (q == null ? "mut" : "")}">${q == null
          ? "henüz sorgu kaydedilmedi — ilk resmî kapı değerlendirmesinde doğar"
          : `${q} sorgu / eşik ${lim}${asir ? " · <span class=\"warn\">EŞİK AŞILDI</span>" : ""}
             <span class="mut">(parmak izi ${esc(String(en.fingerprint).slice(0, 8))}…)</span>`}</b></div>
        <div class="srow"><span>Yürürlükteki ek marj</span><b class="${er.extra_margin_yururlukte ? "warn" : "mut"}">${
          er.extra_margin_yururlukte ? `+${trn(er.extra_margin_yururlukte, 3)} (kapı çıtası yükseltildi)`
                                     : "yok — eşik aşılmadı"}</b></div>
        <div class="srow"><span>Yürürlükteki pencere</span><b>${esc(er.pencere_id || "—")}
          <span class="mut">${er.rotasyon_tarihi ? `· rotasyon ${esc(er.rotasyon_tarihi)}` : ""}
          · izlenen pencere ${er.n_pencere ?? 0}</span></b></div>
        ${!er.arsiv ? "" : `
        <!-- ARŞİV SATIRI (HOLDOUT ROTASYONU R1, 2026-07-30). Rotasyondan önce bu kart defterdeki
             MAKSİMUM sayacı gösteriyordu; R1'den sonra o maksimum arşivlenmiş R0 satırıdır (434
             sorgu) ve onu "en çok sorulan pencere" diye göstermek, rotasyonun ÇÖZDÜĞÜ sorunu hâlâ
             açık gibi sunardı. Sayı kaybolmuyor: arşiv olarak, kendi adıyla ve kıyaslanamaz
             uyarısıyla duruyor. -->
        <div class="srow"><span>Arşiv <span class="mut">(döndürülmüş pencereler)</span></span>
          <b class="mut">${trn(er.arsiv.n_pencere, 0)} pencere · ${trn(er.arsiv.toplam_sorgu, 0)} sorgu
            <span class="mut">— silinmedi; yürürlükteki sayaca EKLENMEZ, kıyaslanamaz</span></b></div>`}
        <p class="hint">${esc(er.beyan || "")}${er.sayac_baslangici
          ? ` · sayaç başlangıcı ${esc(String(er.sayac_baslangici).slice(0, 10))}` : ""} ·
          izlenen pencere sayısı ${er.n_pencere ?? 0}.</p>
        <p class="hint">${er.kiyas_uyarisi ? `<b class="guven">${esc(er.kiyas_uyarisi)}</b>` : ""}</p>`; })()}</div>`;

  // ---------- SONUÇ HÜKMÜ · DOLAR MERCEĞİ (1B, Hafta 3a 2026-07-30) — EDGE KARTININ İKİZİ ----------
  // NEDEN AYRI BİR KART VE NEDEN EDGE'İN YANINDA. EDGE hükmü "kenar var mı?" sorusunu R biriminde
  // yargılıyor; R birimi geniş stopa YAPISAL olarak önyargılı (stop genişler → boyut R-nötr küçülür
  // → aynı fiyat hareketi daha az R üretir). Üç bağımsız ölçümde aynı desen çıktı: kuyruğu
  // İYİLEŞTİREN adaylar (G3a'nın üç paketi, S2 bant filtresi) ortalama-R tabanlı bileşik skor
  // tarafından reddedildi. Şüphe artık adayda değil ÖLÇÜTTE — bu kart ikinci merceği kurar.
  // KARAR KULLANIMI: rafineri kararları (çıkış reformu, otonomi) EDGE'e bakar; sermaye artırımı ve
  // Faz 6 silahlanması İKİ hükme birden bakar. Bu kart EDGE'i GEVŞETMEZ — paydası ayrı, cümlesi ayrı.
  const sSonuc = (() => {
    const rv = ml.result_verdict || null;
    if (!rv) return `<div class="card rise"${katKart("bilesenic:sonuc")}><h2 class="t">Sonuç hükmü · dolar merceği</h2>
      ${kartOzeti({ deger: null, rozet: "ÖLÇÜLEMEDİ",
        meta: "/api/diagnostics <code>result_verdict</code> alanı boş — dolar merceği hükmü üretilmedi (0/4 DEĞİL)." })}
      <p class="empty">Hüküm henüz servis edilmiyor — /api/diagnostics <code>result_verdict</code> alanı boş.</p></div>`;
    const c = rv.criteria || {};
    const ton = rv.passed === 4 ? "pos" : rv.zayif ? "warn" : rv.unmeasured ? "warn" : "neg";
    const ADI = { dolar_beklenti: "1 · $ beklenti", profit_factor: "2 · profit factor",
                  maks_dusus: "3 · maks düşüş", net_pnl: "4 · net vs friksiyon" };
    const serit = `<div class="srow" style="margin-top:2px"><span class="mut">ölçüt durumları</span>
      <b>${Object.entries(c).map(([k, v]) =>
        `<span class="${DURUM_TON[v.durum] || "mut"}" style="margin-left:10px">${esc(ADI[k] || k)}
         <b class="${DURUM_TON[v.durum] || "mut"}">${esc(v.durum || "?")}</b></span>`).join("")}</b></div>`;
    const b = c.dolar_beklenti || {}, pf = c.profit_factor || {}, dd = c.maks_dusus || {}, np = c.net_pnl || {};
    const ci = b.ci || null;
    // ---- CANLI-BEKLENTİ TAVANI (WP-M, 2026-08-01) — KOLON, ÖLÇÜT DEĞİL --------------------------
    // Sunucu bu alanı (`result_verdict.tavan_durumu` ← analytics.live_expectancy_ceiling) ÜRETİYORDU
    // ve hiçbir yüzey OKUMUYORDU: canlı beklenti backtest'in yarısını aşsa da, süspansiyon eşiğinin
    // altına düşse de panoda hiçbir şey değişmezdi. Satır ŞERİDİN ALTINDA ama ÖLÇÜT ŞERİDİNİN
    // DIŞINDA durur ve payda "4/4" olarak kalır — beşinci bir ölçüt gibi okunmasın diye rozeti
    // "HÜKME GİRMEZ" der. TON KURALI: `tavan_altinda` YEŞİL DEĞİLDİR — sunucunun kendi cümlesiyle
    // "iyi haber değil, kuralın BEKLEDİĞİ hâl". Yeşile boyamak, normal hâli bir başarı ilanına
    // çevirirdi; `tavan_ustunde` ise (bir başarı gibi görünmesine rağmen) bir ŞÜPHE işaretidir ve
    // süspansiyonla AYNI uyarı tonunu alır.
    const tavanSatir = (() => {
      const tv = rv.tavan_durumu || null;
      if (!tv) return `<div class="srow"><span>Canlı-beklenti tavanı ${_chip("HÜKME GİRMEZ", "t-rv")}</span>
        <b class="mut">servis edilmiyor — <code>result_verdict.tavan_durumu</code> alanı boş</b></div>`;
      const TAVAN_TR = { olculemedi: "ÖLÇÜLEMEDİ", suspansiyon_degerlendirmesi: "SÜSPANSİYON DEĞERLENDİRMESİ",
                         tavan_altinda: "tavan altında", tavan_ustunde: "TAVAN ÜSTÜNDE" };
      // Nötr = ölçülemedi + tavan_altinda · Uyarı = süspansiyon + tavan_ustunde.
      const TAVAN_TON = { olculemedi: "mut", tavan_altinda: "", tavan_ustunde: "warn",
                          suspansiyon_degerlendirmesi: "warn" };
      const t = TAVAN_TON[tv.durum] == null ? "mut" : TAVAN_TON[tv.durum];
      const olculdu = tv.durum !== "olculemedi";
      return `<div class="srow" style="margin-top:2px"><span>Canlı-beklenti tavanı
          <span class="mut">(canlı R ↔ backtest R)</span> ${_chip("HÜKME GİRMEZ", "t-rv")}</span>
        <b class="${t}">${esc(TAVAN_TR[tv.durum] || tv.durum || "—")}${olculdu
          ? ` <span class="mut">· canlı ${trn(tv.canli_beklenti_r, 4)}R ${tv.tavan_r != null
              ? `· tavan ${trn(tv.tavan_r, 4)}R (backtest ${trn(tv.backtest_beklenti_r, 4)}R × ${trn(tv.cap_mult, 2)})` : ""}
             ${tv.oran != null ? `· oran ${trn(tv.oran, 3)} (süspansiyon eşiği ${trn(tv.suspend_ratio, 2)})` : ""}
             · n=${tv.canli_n ?? 0}</span>`
          : ""}</b></div>
      <p class="hint" style="margin:-2px 0 6px">${esc(tv.hukum || "")}</p>
      <p class="hint">Bu satır <b>bir ölçüt değil bir KOLONdur</b>: yukarıdaki payda 4'te kalır,
        <code>passed/failed/unmeasured/zayif</code> sayaçlarına girmez ve hiçbir kapıyı (probgate/guard/arming)
        kısmaz. Süspansiyon bir <b>operatör kararıdır</b> — burası onu yalnız görünür kılar.
        ${tv.kural_uyari ? `<b class="warn">${esc(tv.kural_uyari)}</b> · ` : ""}${(() => {
          // Katsayının NEREDEN geldiği (goal.yaml mı kod varsayılanı mı) satırın parçasıdır:
          // "0,5" tek başına, kimsenin yazmadığı bir sayının operatör kararı sanılmasına açıktır.
          const kk = Object.entries(tv.kural_kaynak || {});
          return kk.length ? `Kural kaynağı: <code>${esc(kk.map(([k, v]) => `${k}=${v}`).join(" · "))}</code>. ` : "";
        })()}${tv.durum === "olculemedi" ? "" : `Olası hâller: ${esc((tv.durumlar || []).join(" / "))}.`}</p>`;
    })();
    // KAPALI ÖZET (v198): payda EDGE'inkinden AYRIDIR (4, 5 değil) — "EDGE'in ikizi" çipinin
    // özetteki karşılığı budur. Tavan satırı BİLEREK metaya girmez: o bir ölçüt değil bir kolon
    // ve paydayı 4'te tutma kuralı özete de aynen taşınır.
    return `<div class="card rise"${katKart("bilesenic:sonuc")}><h2 class="t">Sonuç hükmü · dolar merceği ${_chip("EDGE'in ikizi", "t-rv")}</h2>
      ${kartOzeti({ deger: `${rv.passed}/4`, oran: rv.passed / 4, payda: "ölçüt (dolar merceği)",
        degerSinif: rv.zayif || rv.unmeasured ? "warn" : "",
        meta: `${esc(rv.verdict || "")}${rv.unmeasured ? ` · ${rv.unmeasured} ölçüt ölçülemedi` : ""}${
          b.n != null ? ` · n=${b.n}` : ""}`,
        rozet: rv.unmeasured ? "ÖLÇÜLEMEYEN VAR" : (rv.zayif ? "ZAYIF" : "") })}
      <div class="srow" style="margin-top:2px"><span>HÜKÜM ${_chip(`${rv.passed}/4 geçti`, "t-rv")}</span>
        <b class="${ton}">${esc(rv.verdict)}</b></div>
      ${serit}
      ${tavanSatir}
      <p class="hint">Birim: ${esc(rv.birim || "")}. <b>Friksiyon İKİ KEZ kesilmez</b> — <code>pnl_dollars</code>
        zaten NET (kayma dolum fiyatının içinde, komisyonlar düşülmüş); <code>costs</code> yalnız 4. ölçütte
        KIYAS TABANI olarak kullanılır.</p>
      <h3 class="t" style="margin-top:14px">1 · İşlem başına $ beklentisi <span class="mut">(blok-bootstrap %95 CI)</span></h3>
      <div class="srow"><span>Ortalama net / işlem</span><b class="${b.value == null ? "mut" : cls(b.value)}">${
        b.value == null ? "ölçülmedi" : `${isr(b.value, money(b.value))}
          <span class="mut">${ci ? `· %95 CI [${money(ci.lo)}, ${money(ci.hi)}]` : ""}
          ${b.anlamli === false ? '· <span class="warn">aralık sıfırı kapsıyor</span>' : ""}
          · n=${b.n ?? "—"} · medyan ${money(b.medyan)}</span>`}</b></div>
      <p class="hint">${ci ? esc(ci.yontem) + " · " : ""}Blok bootstrap kayıp SERİLERİNİ korur; IID örnekleme
        bağımlılığı kırar ve aralığı sistematik olarak DARALTIR. ${esc(b.ci_kapsam || "")}</p>
      <h3 class="t" style="margin-top:14px">2 · Profit factor</h3>
      <div class="srow"><span>Σkazanç / |Σkayıp| <span class="mut">(taban ${trn(pf.esik_deger, 2)})</span></span>
        <b class="${pf.value == null ? "mut" : (pf.durum === "SAGLANDI" ? "pos" : "neg")}">${
        pf.value == null ? "ölçülmedi" : `${trn(pf.value, 4)}
          <span class="mut">· brüt kazanç ${money(pf.brut_kazanc)} (${pf.n_kazanan ?? "—"} işlem) vs
          brüt kayıp ${money(pf.brut_kayip)} (${pf.n_kaybeden ?? "—"} işlem)</span>`}</b></div>
      <h3 class="t" style="margin-top:14px">3 · Maks düşüş <span class="mut">(sermaye eğrisinden)</span></h3>
      <div class="srow"><span>Gerçekleşen düşüş</span><b class="${dd.value == null ? "mut" : (dd.durum === "SAGLANDI" ? "pos" : "neg")}">${
        dd.value == null ? "ölçülmedi" : `${pctf(dd.value, 2)}
          <span class="mut">· kapanmış işlem ${pctf(dd.kapali_islem_dd, 2)} / günlük M2M ${pctf(dd.gunluk_m2m_dd, 2)}
          (${dd.n_gun ?? 0} gün) — KÖTÜ olan okunur</span>`}</b></div>
      <p class="hint">Yalnız kapanmış işlemlere bakan bir eğri AÇIK pozisyonların düşüşünü gizler (denetim #6);
        bu yüzden iki eğrinin kötüsü alınır. EDGE'in 5. ölçütü AYNI hesabı okur — iki hüküm aynı olgu
        hakkında farklı şey söyleyemez.</p>
      <h3 class="t" style="margin-top:14px">4 · Toplam net PnL vs ödenen friksiyon</h3>
      <div class="srow"><span>Net PnL</span><b class="${np.value == null ? "mut" : cls(np.value)}">${
        np.value == null ? "ölçülmedi" : `${isr(np.value, money(np.value))}
          <span class="mut">· ödenen friksiyon ${money(np.toplam_friksiyon)} · oran ${trn(np.oran, 3)}×</span>`}</b></div>
      <p class="hint">4. ölçüt "net &gt; 0" DEĞİL <b>büyüklük</b> sorar: net PnL'in İŞARETİ 1. ölçütle
        matematiksel olarak aynı sorudur (Σpnl = n × ortalama), iki kez sormak paydayı şişirirdi. Kenar,
        ödediği geçiş ücretinden büyük olmalı — yoksa dolum kalitesi iki kat kötüleştiğinde tamamen silinir
        (Alpaca paper dolumları iyimser; Y2/TCA hâlâ ölçülmedi).</p>
      <p class="hint"><b>Karar kullanımı:</b> ${esc(rv.karar_kullanimi || "")}</p></div>`;
  })();

  // ---------- PORTFÖY ISISI (3B) + Y1 DOĞRULAMA ÜÇLÜSÜ (Hafta 3a) ----------
  // ISI: masadaki toplam açık risk tek sayı + NAV yüzdesi. Pozisyon başına risk ve pozisyon SAYISI
  // kapılıydı, TOPLAM açık risk hiçbir yerde tek sayı olarak durmuyordu. YALNIZ GÖSTERGE — bu turda
  // hiçbir kapıya bağlı değil; ısı TAVANI Hafta 3b'nin Y3 dörtlüsünde default-OFF knob olarak gelir.
  // DOĞRULAMA: DSR (kaç denemeden seçildi?) + PBO (seçim yöntemi overfit mi?) + sorgu sayacı yan yana.
  const sDogrulama = (() => {
    const h = ml.portfolio_heat || null, v = ml.validation_trio || null;
    const d = v ? v.dsr_canli : null, p = v ? v.pbo : null;
    const isiTon = h == null || h.isi_pct == null ? "mut" : (h.isi_pct > 8 ? "warn" : "");
    // KAPALI ÖZET (v198): kartın ilk cümlesi masadaki AÇIK RİSKtir; payda özsermayedir ve
    // beyan edilir (ısı yüzdesi zaten o paydanın oranı). Isı ölçülemediyse çubuk çizilmez.
    return `<div class="card rise"${katKart("bilesenic:isi")}><h2 class="t">Portföy ısısı + doğrulama ${_chip("gösterge", "t-rv")}</h2>
      ${kartOzeti(!h || h.isi_pct == null ? {
        deger: null, rozet: "ÖLÇÜLEMEDİ",
        meta: "/api/diagnostics <code>portfolio_heat</code> ısıyı vermedi — masadaki açık risk ölçülemedi (0$ DEĞİL)." }
      : { deger: money(h.acik_risk_dolar), degerSinif: isiTon,
          oran: Math.max(0, Number(h.isi_pct) / 100), payda: "özsermaye (NAV)",
          meta: `NAV ${trn(h.isi_pct, 3)}% · ${trn(h.n_pozisyon)} pozisyon${
            h.n_eksik ? ` · ${h.n_eksik} pozisyon eksik alanlı, sayılmadı` : ""}${
            !v ? " · doğrulama üçlüsü servis edilmiyor" : ""}`,
          rozet: h.n_eksik ? "EKSİK ALAN" : "" })}
      ${!h ? `<p class="empty">Isı henüz servis edilmiyor.</p>` : `
      <div class="srow"><span>Masadaki açık risk ${_chip("YALNIZ GÖSTERGE", "t-rv")}</span>
        <b class="${isiTon}">${money(h.acik_risk_dolar)} · NAV ${trn(h.isi_pct, 3)}%
          <span class="mut">· ${h.n_pozisyon ?? 0} pozisyon · özsermaye ${money(h.ozsermaye)}</span></b></div>
      <div class="srow"><span>Giriş stopuna göre risk <span class="mut">(kıyas)</span></span>
        <b class="mut">${money(h.ilk_stop_riski_dolar)} · NAV ${trn(h.ilk_stop_isi_pct, 3)}%</b></div>
      <p class="hint"><code>${esc(h.formul || "")}</code> — yürürlükteki stop (trail dahil) okunur; giriş
        stopuna göre hesap kıyas olarak yanında durur, çünkü ikisi bir kazanan pozisyonda ayrışır. Trail'i
        girişin üstüne çıkmış pozisyonun riski sıfıra kısılır ve BAŞKA pozisyonu mahsup ETMEZ (mahsup edilse
        ısı olduğundan soğuk okunurdu). ${h.n_eksik ? `<b class="warn">${h.n_eksik} pozisyon eksik alanlı — sayılmadı.</b>` : ""}</p>
      <p class="hint"><b>${esc(h.rol || "")}</b></p>`}
      <h3 class="t" style="margin-top:16px">Doğrulama · DSR / PBO / sorgu sayacı</h3>
      ${!v ? `<p class="hint">Doğrulama üçlüsü henüz servis edilmiyor.</p>` : `
      <!-- PENCERE SATIRI (HOLDOUT ROTASYONU R1, 2026-07-30). Panonun doğrulama satırı bugüne kadar
           HANGİ pencerede ölçüldüğünü söylemiyordu. Rotasyondan sonra bu bir eksik değil TUZAK olur:
           R0'da 12 kayıtla ölçülmüş bir PBO ile R1'de 2 kayıtla ölçülmüş bir PBO panoda AYNI
           görünürdü ve okuyan iyileşme/kötüleşme çıkarırdı — habersiz kıyasın ta kendisi. -->
      <div class="srow"><span>Pencere <span class="mut">(sınav kâğıdı kimliği)</span></span>
        <b>${esc(v.pencere_id || "—")} <span class="mut">· rotasyon ${esc(v.rotasyon_tarihi || "—")}
          · PBO paydası: bu pencerede ${trn((v.defter || {}).n_kayit_guncel_pencere, 0)} kayıt${
          (v.defter || {}).n_kayit_onceki_pencereler
            ? ` · önceki pencerelerde ${trn((v.defter || {}).n_kayit_onceki_pencereler, 0)} kayıt (arşiv — paydaya GİRMEZ)`
            : ""}</span></b></div>
      <div class="srow"><span>DSR <span class="mut">(deflated Sharpe — canlı defter)</span></span>
        <b class="${!d || d.dsr == null ? "mut" : (d.dsr >= 0.95 ? "pos" : "neg")}">${!d || d.dsr == null
          ? `ölçülemedi — seri ${d ? d.n : 0} gözlem (taban 20) ya da varyans sıfır`
          : `${trn(d.dsr, 6)} <span class="mut">· PSR(0) ${trn(d.psr_sifir, 4)} · gözlem-Sharpe ${trn(d.sharpe_gozlem, 4)}
             · beklenen maks ${trn(d.beklenen_maks_sharpe, 4)} · çarpıklık ${trn(d.skew, 3)} / basıklık ${trn(d.kurtosis, 3)}</span>`}</b></div>
      <div class="srow"><span>Deneme sayısı N</span><b>${trn(v.n_trials, 0)}
        <span class="mut">· aşınma sorgusu ${trn(v.erosion_sorgu, 0)} + oturum-içi k_probes ${trn(v.k_probes_toplam, 0)}
        · varyans kaynağı ${esc(d ? d.varyans_kaynagi : "—")}</span></b></div>
      <div class="srow"><span>PBO <span class="mut">(CSCV — seçim yöntemi overfit mi?)</span></span>
        <b class="${!p || p.pbo == null ? "mut" : (p.pbo < 0.2 ? "pos" : "neg")}">${!p || p.pbo == null
          ? esc((p && p.neden) || "ölçülemedi")
          : `${pctf(p.pbo, 1)} <span class="mut">· ${p.n_aday} aday · ${p.n_kombinasyon} kombinasyon
             · ort. OOS sıra ${trn(p.ort_oos_sira, 3)}</span>`}</b></div>
      <!-- ④ SERT KAPI DOĞRULAMA SATIRI (DSR hard-gate turu, v130). Pano bu iki sayıyı bugüne kadar
           GÖSTERİYORDU ama onların bir HÜKÜM doğurup doğurmadığını söylemiyordu — okuyan "DSR 0,02"
           görüp "demek ki ship engellendi" diye çıkarabilirdi (yanlış), ya da tersine sertleşmiş
           PBO'yu hâlâ tavsiye sanabilirdi. Satır kuralı AÇIKÇA yazar ve bugünkü değerlerin HANGİ
           damgayı/hükmü alacağını yanına koyar: bir kapı kuralı, uygulandığı sayıyla birlikte
           okunmazsa denetlenemez. -->
      <div class="srow"><span>Sert kapı <span class="mut">(ship hükmü — mod-farkındalıklı)</span></span>
        <b>DSR: <span class="mut">ship=</span>kâğıt-ADVISORY (damga) <span class="mut">·</span>
          gerçek-para=<b>SERT (fail-closed)</b> <span class="mut">· PBO:</span>
          <b>SERT</b> <span class="mut">(iki modda da, ölçülebilirse)</span></b></div>
      <div class="srow"><span>Bugünkü değerler bu kurala göre</span>
        <b>${!d || d.dsr == null
          ? `<span class="mut">DSR ölçülemedi → kâğıtta damga <code>dsr_durum: olculemedi</code>; gerçek-para bağlamında RET olurdu</span>`
          : (d.dsr <= 0.95
            ? `<span class="warn">DSR ${trn(d.dsr, 6)} ≤ 0,95 → kâğıtta <code>dsr_dusuk: true</code> damgası (ship GEÇER); gerçek-para bağlamında RET</span>`
            : `<span class="pos">DSR ${trn(d.dsr, 6)} &gt; 0,95 → iki modda da geçer</span>`)}
          <span class="mut">·</span> ${!p || p.pbo == null
            ? `<span class="mut">PBO ölçülemedi → kâğıtta VETO YOK (uygulanamayan kontrol veto olamaz); gerçek-para bağlamında RET</span>`
            : (p.pbo >= 0.2
              ? `<span class="neg">PBO ${pctf(p.pbo, 1)} ≥ %20 → İKİ MODDA DA RET</span>`
              : `<span class="pos">PBO ${pctf(p.pbo, 1)} &lt; %20 → geçer</span>`)}</b></div>
      ${(() => {
        // FAZ-6 KİLİT ZİNCİRİ (v130): beş kilit tek satırda. ROADMAP §3.5 "dört kilit" diyordu ve
        // hiçbir yüzeyde görünmüyordu — yani bir kilidin sessizce düşmesi kimseye görünmezdi.
        const f = ml.faz6_kilitleri || null;
        if (!f) return "";
        const ADI = {edge_kaniti: "EDGE kanıtı", sonuc_hukmu: "SONUÇ hükmü", faz5_cikisi: "Faz-5 çıkışı",
                     operator_onayi: "operatör onayı", dsr_gecer: "DSR geçer"};
        const cips = (f.adlar || []).map(a => {
          const k = (f.kilitler || {})[a] || {};
          const kls = k.gecer ? "t-go" : (k.durum === "olculemedi" ? "t-rv" : "t-no");
          return `<span class="st ${kls}" title="${esc(k.esik || "")}${k.neden ? " — " + esc(k.neden) : ""}">${
            k.gecer ? "✓" : "×"} ${esc(ADI[a] || a)}</span>`;
        }).join(" ");
        return `<div class="srow"><span>Faz-6 kilit zinciri <span class="mut">(silahlanma ön-koşulu)</span></span>
          <b class="${f.hepsi_acik ? "pos" : "warn"}">${f.n_acik ?? 0}/${f.n_kilit ?? 5} açık</b></div>
          <p class="hint">${cips}</p>
          <p class="hint">${esc(f.hukum || "")} <b>${esc(f.beyan || "")}</b></p>`;
      })()}
      <p class="hint">DSR: "bu Sharpe, N denemeden seçildikten SONRA hâlâ şaşırtıcı mı?" (Bailey &amp; López de
        Prado 2014 — çarpıklık/basıklık düzeltmeli). PBO: "in-sample'da en iyiyi seçtiğimde OOS'ta medyanın
        altına düşme olasılığım nedir?" %50 = yazı-tura; hedef &lt;%20.
        <b>${esc(v.rol || "")}</b></p>
      <p class="hint">${esc(v.n_trials_beyan || "")} · defter ${(v.defter || {}).n_kayit ?? 0} kayıt
        (<code>${esc((v.defter || {}).dosya || "")}</code>) — ${esc((v.defter || {}).beyan || "")}</p>
      <p class="hint">${v.kiyas_uyarisi ? `<b class="guven">${esc(v.kiyas_uyarisi)}</b>` : ""}</p>`}
      ${sw()}</div>`;
    // ---- BÜYÜKLÜK YASASI SATIRI — TERS GÖLGELEME (PARA-v3, 2026-07-30) ----------------------
    // 3b'de bu blok "v2 olsaydı" diyordu ve ÖLÇÜM MODU rozeti taşıyordu. Yasa yeniden tasarlandı:
    // artık KARAR PARA-v3'te, ESKİ yasa kayda geçiyor. Rozet bu yüzden "GEÇİŞ YAPILDI" demek
    // ZORUNDA — operatör bu satıra bakıp hâlâ eski yasanın koştuğunu sanırsa, kapı kayıtlarındaki
    // p'leri yanlış yasanın p'si olarak okur ve bütün karne yanlış okunur.
    // DÖRT ŞEY BİRLİKTE: (a) hangi yasa hüküm veriyor, (b) PARA payı %0,3 → %100, (c) skordan
    // çıkan bacakların NEREYE gittiği (vetolar — yoksa "korumayı kaldırdılar" diye okunur),
    // (d) eski yasanın son hükmü + ıraksama sayacı (sürekliliğin kanıtı).
    function sw() {
      const s = ml.shadow_law || null;
      if (!s) return `<p class="hint">Büyüklük yasası satırı henüz servis edilmiyor.</p>`;
      const pay1 = (s.varyans_payi || {}).eski || {}, pay3 = (s.varyans_payi || {}).v3 || {};
      const son = s.son_kayit, rot = s.v2_rotusu || {};
      return `<h3 class="t" style="margin-top:16px">Büyüklük yasası · ${esc(s.yasa_surumu || "")}
          ${_chip(s.law_transition ? `GEÇİŞ YAPILDI ${esc(s.gecis_tarihi || "")}` : "ÖLÇÜM MODU", "t-rv")}</h3>
        <div class="srow"><span>Yürürlükteki yasa <span class="mut">(passes'i üreten)</span></span>
          <b class="mut">${esc(s.aktif_yasa || "")}</b></div>
        <div class="srow"><span>Gölge yasa <span class="mut">(yalnız kayıt)</span></span>
          <b class="mut">${esc(s.golge_yasa || "")}</b></div>
        <div class="srow"><span>PARA teriminin varyans payı</span>
          <b class="${(s.para_payi_v3 || 0) >= 0.999 ? "pos" : "neg"}">eski ${pctf(pay1.para, 1)}
            → v3 ${pctf(pay3.para, 1)}
            <span class="mut">· para terimi ${trn(s.ret_scale_k, 2)}× canlandı (σ)</span></b></div>
        <div class="srow"><span>Skordan çıkan bacaklar <span class="mut">(nereye gitti)</span></span>
          <b class="mut">düşüş ${pctf(pay1.dusus, 1)} · Sharpe ${pctf(pay1.sharpe, 1)} →
            SERT VETOLARA: düşüş vetosu ${trn(s.dd_veto_margin, 2)} · kuyruk VaR/CVaR · fold
            çoğunluğu · DSR</b></div>
        <div class="srow"><span>Marj <span class="mut">(para ölçeğine çevrildi)</span></span>
          <b class="mut">${trn(s.gate_margin_eski, 3)} (bileşik) × ${trn(s.margin_scale, 4)} =
            ${trn(s.money_gate_margin, 4)} (para)</b></div>
        <div class="srow"><span>Gölge kayıt · ıraksayan hüküm</span>
          <b class="${(s.iraksayan_kayit || 0) > 0 ? "warn" : "mut"}">${s.golge_kayit_sayisi ?? 0} kayıt ·
            ${s.iraksayan_kayit ?? 0} ıraksama
            <span class="mut">· geçiş öncesi ${s.gecis_oncesi_kayit ?? 0} kayıt (v3 hükmü
            ters çevrilemez)</span></b></div>
        ${!son ? `<p class="hint">Henüz İKİ yasayı birlikte taşıyan kapı kaydı YOK — ilk kayıt
          sıradaki kapı değerlendirmesinde doğar (çift hesap her değerlendirmede koşar).</p>` : `
        <div class="srow"><span>Son kayıt ${esc(son.id || "")} <span class="mut">(${esc(son.dilim || "")})</span></span>
          <b class="mut">yasa: ${esc(son.yasa_surumu || s.yasa_surumu || "")} · P ${trn(son.p_v3, 4)}
            (gerekli ${trn(son.p_required, 2)}) → ${son.v3_gecti ? "GEÇTİ" : "RET"} ·
            eski hüküm: P ${trn(son.p_eski, 4)} → ${son.eski_gecerdi ? "GEÇERDİ" : "REDDEDERDİ"}</b></div>`}
        <p class="hint">v2 rötuşu NEDEN yetmedi (v3'ün gerekçesi): hedef PARA ${pctf(rot.hedef, 0)},
          en iyi deneme ${pctf(rot.en_iyi_para_payi, 1)} — ${rot.hedef_tuttu ? "TUTTU" : "TUTMADI"}
          (${rot.deneme_sayisi} deneme: ${(rot.denemeler || []).map(d =>
            `${esc(d.etiket)} → ${pctf(d.para_payi, 1)}`).join(" · ")})</p>
        <p class="hint"><b>${esc(s.beyan || "")}</b>
          <br><span class="mut">${esc(s.neden_tutmadi || "")}</span></p>`;
    }
  })();

  // ---------- HERMES KARNESİ (H1+H2+H3, 3b) + MAE ----------
  // NEDEN TEK KART: üçü de aynı soruyu farklı katmanda soruyor — "öğrenme döngüsü GERÇEKTEN kapandı
  // mı?" H1 beynin kendi tahmin isabetini, H2 mezarlığını ve kör noktasını, H3 bileşik kuyruğun
  // dolup boşaldığını gösterir. Ayrı kartlara dağıtılsa hiçbiri tek başına hüküm vermezdi.
  //
  // GÖLGE-VARYANT ARTIK BU KARTTA DEĞİL (S2R-3, ADR'nin S2R-2'ye bıraktığı içerik borcu #1).
  // O blok bu kartın bir ALT BAŞLIĞIYDI ve gerekçesi zayıftı: k_variants portföyleri "beyin
  // parametre tahminlerinde ne kadar isabetli?" sorusuna DEĞİL, "kâğıt üstünde koşan gölge kollar
  // ne veriyor?" sorusuna cevap veriyor — yani `golge` bölümünün soru cümlesinin birebir kendisi.
  // S2R-2 onu taşıyamadı çünkü sözleşmesi "bölüm taşı, kart gövdesi yeniden yazma"ydı; cila
  // turunun işi tam olarak o gövdeyi bölmekti. Bkz. aşağıdaki `sGolgeVaryant`.
  const sHermes = (() => {
    const c = ml.hermes_scorecard || null, mp = ml.mae_profile || null;
    if (!c) return `<div class="card rise"><h2 class="t">Hermes karnesi</h2>
      <p class="empty">Karne henüz servis edilmiyor.</p></div>`;
    const pb = c.prediction_band || {}, f = c.families || {}, q = c.composite_queue || {};
    const olu = Object.entries(f.olu_aileler || {}).slice(0, 5);
    const hic = f.hic_onerilmemis_dugmeler || [];
    return `<div class="card rise"><h2 class="t">Hermes karnesi · tahmin isabeti · ölü aileler · bileşik kuyruk
        ${_chip("H1-H3", "t-rv")}</h2>
      <div class="srow"><span>Tahmin isabeti <span class="mut">(öngörülen ΔS ↔ gerçekleşen)</span></span>
        <b class="${pb.band ? "" : "mut"}">${pb.band
          ? `medyan oran ${trn(pb.band.medyan_oran, 3)} <span class="mut">· p25 ${trn(pb.band.p25, 3)} /
             p75 ${trn(pb.band.p75, 3)} · n=${pb.n}</span>`
          : `n=${pb.n ?? 0} — BANT ÖLÇÜLEMEDİ`}</b></div>
      <p class="hint">${esc(pb.hukum || "")}${pb.yon_isabeti
        ? ` <b>Yön isabeti: ${pb.yon_isabeti.dogru}/${pb.yon_isabeti.n}</b>` : ""}</p>
      <!-- D1 · aile ADI bir etikettir, bir uyarı seviyesi değil: koşulsuz kehribardı. -->
      <div class="srow"><span>En yoğun aile</span><b>${esc(f.en_yogun_aile || "—")}
        <span class="mut">· tüm hipotezlerin ${pctf(f.en_yogun_pay, 1)}'i</span></b></div>
      ${!olu.length ? `<p class="hint">Ölü aile YOK (>= eşik denemeye ulaşmış ve 0 ship olan knob yok).</p>` : `
      <table class="tbl"><thead><tr><th>ölü aile</th><th class="num">denendi</th><th class="num">ship</th><th>denenen değerler</th></tr></thead>
      <tbody>${olu.map(([k, v]) => `<tr><td><code>${esc(k)}</code></td><td class="num">${v.denendi}</td>
        <td class="num ${v.ship ? "" : "neg"}">${v.ship}</td>
        <td class="mut">${esc((v.denenen_degerler || []).join(", "))}</td></tr>`).join("")}</tbody></table>`}
      <div class="srow"><span>Defterde HİÇ önerilmemiş düğme</span>
        <b class="${hic.length ? "warn" : "pos"}">${esc(f.hic_onerilmemis_sayi || "—")}</b></div>
      ${hic.length ? `<p class="hint">${hic.map(k => `<code>${esc(k)}</code>`).join(" · ")}
        — beyin 15 gündür aynı düğmelerde dönüyor; bu satır kör noktanın KENDİSİDİR ve prompt'a girer.</p>` : ""}
      <div class="srow"><span>Bileşik kuyruk <span class="mut">(H3/H4)</span></span>
        <b class="mut">${q.n_bekleyen ?? 0} bekleyen · ${q.n_olculen ?? 0} ölçülen ·
          haftalık bütçe kalan ${q.butce_kalan ?? "—"}/${q.haftalik_butce ?? "—"}</b></div>
      <p class="hint">${esc(q.beyan || "")}</p>
      ${!mp ? `<p class="hint">MAE karnesi henüz ölçülmedi.</p>` : `
      <h3 class="t" style="margin-top:16px">MAE · stopun kör ikizi</h3>
      <div class="srow"><span>Kazananların acısı <span class="mut">(n=${(mp.kazananlar || {}).n ?? 0})</span></span>
        <b class="mut">medyan ${trn((mp.kazananlar || {}).medyan, 3)}R · p90 ${trn((mp.kazananlar || {}).p90, 3)}R</b></div>
      <div class="srow"><span>Kaybedenlerin acısı <span class="mut">(n=${(mp.kaybedenler || {}).n ?? 0})</span></span>
        <b class="mut">medyan ${trn((mp.kaybedenler || {}).medyan, 3)}R · p90 ${trn((mp.kaybedenler || {}).p90, 3)}R
          · maks ${trn((mp.kaybedenler || {}).maks, 3)}R</b></div>
      <p class="hint">${(mp.hukum || []).map(x => esc(x)).join(" · ")} <b>${esc(mp.rol || "")}</b></p>`}
      </div>`;
  })();

  // ---------- GÖLGE-VARYANT PORTFÖYLERİ — KENDİ KARTI, EVİ `golge` (S2R-3) ----------
  // İçerik borcunun ödenmesi: blok Hermes karnesi kartının alt başlığı olmaktan çıkıp kendi
  // kartına taşındı ve `golge` bölümünde yazılıyor. OKUYUCU KORUNUMU BİREBİR: `shadow_variants`ın
  // altı alanı da (n_satir · son_karar{label,date,signal_n,would_arm_n} · kumulatif_ayrisma ·
  // k_variants · rol · durum) aynen taşındı — panoda başka okuyucusu yok, bir tanesi düşseydi
  // alan öksüz kalırdı (YASA-6, HTTP→DOM katmanı).
  //
  // İKİ HÂL AYRI CÜMLE OLARAK KORUNDU: `sv` YOKSA kart hiç doğmaz (uç servis etmiyor);
  // `sv.n_satir` sıfırsa kart DOĞAR ve `sv.durum`u yazar — "defter boş" ile "ölçüm yok" bu
  // panoda asla aynı ekran değildir.
  //
  // ÇOKLU-KARŞILAŞTIRMA PAYDASI (`k_variants`) TABLOYLA AYNI KARTTA KALIR: "en iyi varyant"
  // rakamı paydadan ayrılırsa seçim yanlılığı görünmez olur — şerh rakamdan ayrılamaz kuralının
  // (trend kitabındaki `pit_serh` ile aynı kural) bu karttaki karşılığı budur.
  const sGolgeVaryant = (() => {
    const sv = ml.shadow_variants || null;
    if (!sv) return "";
    // KAPALI ÖZET (v198): değer AYRIŞAN varyant sayısıdır, payda ÇOKLU-KARŞILAŞTIRMA PAYDASI
    // (`k_variants`) — şerh rakamdan ayrılamaz kuralı özette de geçerli: "3 varyant ayrıştı"
    // cümlesi k=12 paydasından koparılırsa seçim yanlılığı görünmez olur.
    const _ayrisan = Object.values(sv.kumulatif_ayrisma || {}).filter(x => x).length;
    return `<div class="card rise"${katKart("golge:varyant")}><h2 class="t">Gölge-varyant portföyleri ${_chip("kâğıt defter", "t-rv")}</h2>
      ${kartOzeti(sv.n_satir ? {
        deger: `${_ayrisan}/${sv.k_variants ?? "—"}`,
        oran: sv.k_variants ? _ayrisan / sv.k_variants : null,
        payda: sv.k_variants ? "varyant (çoklu-karşılaştırma paydası)" : "",
        meta: `${sv.n_satir} defter satırı · ${_ayrisan} varyant kümülatif ayrışma taşıyor` }
      : { deger: null, rozet: "ÖLÇÜLEMEDİ",
          meta: esc(sv.durum || "varyant defteri satır üretmedi — durum gerekçesi de gelmedi (0 ayrışma DEĞİL).") })}
      ${sv.n_satir ? `
      <table class="tbl"><thead><tr><th>varyant</th><th>son karar</th><th class="num">sinyal / silahlanır</th><th class="num">kümülatif ayrışma</th></tr></thead>
      <tbody>${Object.entries(sv.son_karar || {}).map(([k, v]) => `<tr><td><code>${esc(k)}</code>
        <span class="mut">${esc(v.label || "")}</span></td><td class="mut">${esc(v.date || "")}</td>
        <td class="num">${v.signal_n ?? 0} / ${v.would_arm_n ?? 0}</td>
        <td class="num ${(sv.kumulatif_ayrisma || {})[k] ? "warn" : "mut"}">${(sv.kumulatif_ayrisma || {})[k] ?? 0}</td>
        </tr>`).join("")}</tbody></table>
      <p class="hint">k_variants=${sv.k_variants ?? "—"} <b>ÇOKLU-KARŞILAŞTIRMA PAYDASI</b> — "en iyi varyant"
        seçimi bu sayıyla cezalandırılmalıdır. ${esc(sv.rol || "")}</p>`
      : `<p class="hint">${esc(sv.durum || "")}</p>`}</div>`;
  })();

  // ---------- SİSTEM ÖNERİLERİ (NOUS SİSTEM-DEĞERLENDİRME KATMANI B/C/D) ----------
  // NEDEN HERMES KARNESİNİN HEMEN ALTINDA: karne "beyin PARAMETRE tahminlerinde ne kadar isabetli?"
  // sorusunu cevaplıyor; bu kart bir üst katmanı gösterir — "beyin MEKANİZMALAR hakkında ne
  // görüyor?". İkisi yan yana durunca sistemin kendini geliştirme döngüsü tek bakışta okunur.
  // KALİTE KAPISI SAYISI KARTIN İÇİNDE: düşürülen öneri sayısı gizlenirse "beyin 4 öneri üretti"
  // ile "9 üretti, 5'i kanıt-atıfsız düştü" aynı görünür — ve ikincisi beynin karnesi hakkında
  // birincisinden çok daha fazla şey söyler.
  // OTOMATİK YÖNLENDİRME BORUSU (v192): 2026-W32'de üç öneri de `sekil=tasarim` + `kuyruk=yol_yok`
  // idi — yani kabul edildi, deftere yazıldı, panoda göründü ve SONRA HİÇBİR ŞEY olmadı. Boru üç
  // şekli üç AYRI yola bağlar; kart o yolu satır başına gösterir: kuyruk id'si (parametre),
  // FİŞLENDİ rozeti (tasarım) ya da KATMAN D (çekirdek — yalnız rapor, otomatik uygulama YOK).
  const sNous = (() => {
    const p = ml.improvement_proposals || null;
    if (!p) return "";
    const fis = ml.nous_fisler || {};
    const fisAnahtar = new Set(fis.anahtarlar || []);
    const rozet = { yuksek: "t-no", orta: "t-rv", dusuk: "t-go" };
    const sekilRozet = { parametre: "t-go", tasarim: "t-rv", cekirdek_hakkinda: "t-no" };
    // YOL HÜCRESİ: "kuyruk" sütunu yalnız parametre şeklini anlatabiliyordu; diğer iki şekilde
    // `yol_yok` yazıyordu ve o kelime bir çıkmaz sokağı bir durum gibi gösteriyordu.
    const yolHucre = (o) => {
      if (o.sekil === "cekirdek_hakkinda")
        return `<span class="mut" title="Katman D: kapı yasaları/guard/PROTECTED/vetolar hakkındaki öneri YALNIZ rapora gider — otomatik uygulama bu sınıfa ASLA dokunmaz">KATMAN D · yalnız rapor</span>`;
      if (o.sekil === "tasarim")
        return fisAnahtar.has(String(o.id))
          ? `${_chip("FİŞLENDİ", "t-rv")}<br><span class="mut" title="operatör kuyruğunda görünür iş kalemi — otomatik uygulama yolu YOK">operatör kuyruğu</span>`
          : `<span class="warn" title="tasarım önerisi fişlenmemiş — boru bu satırı işlemedi">fişlenmedi</span>`;
      return `${esc(o.kuyruk || "—")}${o.kuyruk_id ? `<br><code>${esc(o.kuyruk_id)}</code>` : ""}`;
    };
    if (p.durum !== "dolu") {
      return `<div class="card rise"><h2 class="t">Sistem önerileri ${_chip("Katman B/C/D", "t-rv")}</h2>
        <p class="empty">${esc(p.durum || "")}</p>
        <p class="hint">${esc(p.rol || "")}</p></div>`;
    }
    const dn = Object.entries(p.dusme_nedenleri || {});
    return `<div class="card rise"><h2 class="t">Sistem önerileri · nous mekanizma değerlendirmesi
        ${_chip(esc(p.son_hafta || "—"), "t-rv")}</h2>
      <div class="srow"><span>Bu hafta <span class="mut">(beyin ${esc(p.beyin || "—")}
        · ${esc(p.model || "—")})</span></span>
        <b>${p.n_son_hafta ?? 0} öneri <span class="mut">· defterde toplam ${p.n ?? 0}</span></b></div>
      <div class="srow"><span>KALİTE KAPISI <span class="mut">(kanıt-atıfsız öneri DÜŞÜRÜLÜR)</span></span>
        <b class="${p.n_dusen ? "warn" : "mut"}">${p.n_uretilen ?? "—"} üretildi →
          ${p.n_dusen ?? 0} düştü</b></div>
      ${dn.length ? `<p class="hint">Düşme nedenleri: ${dn.map(([k, v]) =>
        `<code>${esc(k)}</code>×${v}`).join(" · ")} — kapı sessiz çalışmaz.</p>` : ""}
      ${(p.devreden || []).length ? `<p class="hint"><b class="warn">DEVREDEN: ${p.devreden.length}
        öneri</b> — H4'ün haftalık yoklama bütçesi doluydu, sıradaki haftaya taşındı (ayrı bütçe
        AÇILMAZ; devir görünür olmak zorundadır).</p>` : ""}
      ${p.kosu_durumu && p.kosu_durumu !== "ayristirildi" ? `<p class="hint"><b class="warn">
        Koşu durumu: ${esc(p.kosu_durumu)}</b> — şablon öneri ÜRETİLMEZ (uydurma yasağı).</p>` : ""}
      ${!(p.oneriler || []).length ? `<p class="hint">Bu hafta kabul edilmiş öneri yok.</p>` : `
      <table class="tbl"><thead><tr><th>öncelik</th><th>şekil</th><th>alan</th><th>gözlem → öneri</th>
        <th>yol</th></tr></thead>
      <tbody>${(p.oneriler || []).map(o => `<tr>
        <td>${_chip(esc(o.oncelik || "?"), rozet[o.oncelik] || "t-rv")}</td>
        <td>${_chip(esc(o.sekil || "?"), sekilRozet[o.sekil] || "t-rv")}</td>
        <td><code>${esc(o.alan || "?")}</code></td>
        <td><span class="mut">${esc(String(o.gozlem || "").slice(0, 180))}</span><br>
          <b>${esc(String(o.oneri || "").slice(0, 180))}</b>
          <br><span class="mut">etki: ${esc(String(o.beklenen_etki || "").slice(0, 120))}
          · ölçüm: ${esc(String(o.onerilen_olcum || "").slice(0, 120))}</span>
          <br><span class="mut">atıf: ${esc((o.kanit_atifi || []).join(", ").slice(0, 120))}</span></td>
        <td class="${o.kuyruk === "evet" ? "pos" : o.kuyruk === "devredildi" ? "warn" : "mut"}">
          ${yolHucre(o)}</td>
        </tr>`).join("")}</tbody></table>`}
      ${fis.durum === "defter_yok" ? `<p class="hint"><b class="mut">Fiş defteri yok</b> — ${esc(fis.rol || "")}</p>`
        : `<p class="hint"><b>Fiş kuyruğu:</b> ${fis.n_acik ?? 0} açık / ${fis.n ?? 0} toplam${
          fis.guncellendi ? ` · son ${esc(String(fis.guncellendi).replace("T", " ").slice(0, 16))}` : ""} — ${esc(fis.rol || "")}</p>`}
      <p class="hint">Şekil dağılımı: ${Object.entries(p.sekil_dagilimi || {}).map(([k, v]) =>
        `${esc(k)}=${v}`).join(" · ") || "—"}.
        <b>${esc(p.rol || "")}</b></p></div>`;
  })();

  // ---------- Y3 REJİM/RİSK DÖRTLÜSÜ (3b) ----------
  // İKİ PİYASA BACAĞI ARTIK GÖSTERGE, KAPI DEĞİL (EDG-005 hükmü, 2026-08-01): hüküm ölçülür ve
  // burada görünür ama hiçbir karar yoluna girmez (guard tüketicisi + regime üreticisi kaldırıldı).
  // Kart bunu SÖYLER — "kapalı" yazmak, açılabilir bir kapı varmış gibi okunurdu. İki PORTFÖY
  // tavanı ise hâlâ karar yolunda ve DEFAULT-OFF. VIX bacağı ayrıca `veri_yok` (kaynak yok).
  const sY3 = (() => {
    const y = ml.y3_entry_gates || null;
    if (!y) return "";
    const sma = y.spy_sma_gate || {}, vix = y.vix_backwardation_gate || {}, caps = y.portfolio_caps || {};
    // KAPALI ÖZET (v198): dörtlünün KAÇI fiilen karar yolunda? İki piyasa bacağı EDG-005 ile
    // göstergeye indi, iki portföy tavanı default-OFF. Payda dörtlünün kendisi; değer, kapalı
    // olanın sayısı DEĞİL karar yolunda ETKİN olanın sayısıdır — "dörtlü var" ile "dördü de
    // etkisiz" aynı piksele düşemez.
    const _y3Etkin = (caps.sector_cap_pct ? 1 : 0) + (caps.heat_cap_pct ? 1 : 0);
    return `<div class="card rise"${katKart("bilesenic:y3")}><h2 class="t">Y3 rejim/risk dörtlüsü
        ${_chip("piyasa bacakları: GÖSTERGE (kapı değil)", "t-rv")}</h2>
      ${kartOzeti({ deger: `${_y3Etkin}/4`, oran: _y3Etkin / 4, payda: "Y3 kolu (dörtlü)",
        meta: `2 piyasa bacağı gösterge (karar yolunda değil) · ${2 - _y3Etkin} portföy tavanı KAPALI${
          sma.hukum ? ` · SPY ${esc(sma.hukum)}` : ""}`,
        rozet: sma.hukum === "altinda" ? "SPY SMA ALTINDA" : "",
        degerSinif: sma.hukum === "altinda" ? "warn" : "" })}
      <div class="srow"><span>SPY ${sma.window ?? 200}-SMA göstergesi
        <span class="mut">(karar yolunda DEĞİL — ${esc((sma.knob_emekli || {}).karar || "EDG-2026-005")})</span></span>
        <b class="${sma.hukum === "altinda" ? "warn" : "mut"}">${sma.hukum
          ? `${esc(sma.hukum)} · ${trn(sma.close, 2)} vs ${trn(sma.sma, 2)}`
          : "hüküm YOK (ısınma/veri)"}</b></div>
      <div class="srow"><span>VIX/VIX3M backwardation
        <span class="mut">(veri-kilitli${vix.enabled ? " · knob 1 ama etkisiz" : ""} — karar yolunda DEĞİL)</span></span>
        <b class="mut">${esc((vix.veri || {}).reason || "—")}</b></div>
      <p class="hint">VIX kaynağı DOĞRULANDI ve YOK: <code>${esc((vix.veri || {}).massive || "")}</code> ·
        <code>${esc((vix.veri || {}).fmp || "")}</code> — oran UYDURULMAZ, vekil bir seri VIX adıyla sunulmaz.</p>
      <div class="srow"><span>Sektör notional tavanı</span>
        <b class="mut">${caps.sector_cap_pct ? `%${trn(caps.sector_cap_pct, 0)}` : "KAPALI (0)"}</b></div>
      <div class="srow"><span>Isı tavanı <span class="mut">(açık risk / NAV)</span></span>
        <b class="mut">${caps.heat_cap_pct ? `%${trn(caps.heat_cap_pct, 1)}` : "KAPALI (0)"}</b></div>
      <p class="hint">${esc(caps.not || "")}</p>
      ${(() => {
        // 2C KÜÇÜLTME + 2D ROTASYON: ikisi de "bu sayıya ne kadar güvenebiliriz?" sorusunu sorar,
        // o yüzden Y3 kartının altında dururlar (risk okuması). Küçültülmüş değer verdict
        // tabanlarına GİRMEZ — etiket bunu her bakışta söyler.
        const sh = ml.shrunk_regime_cells || null, hr = ml.holdout_rotation || null;
        let o = "";
        if (sh && sh.hucreler) {
          const hl = Object.entries(sh.hucreler);
          o += `<h3 class="t" style="margin-top:16px">Rejim hücreleri ${_chip("küçültülmüş (2C)", "t-rv")}</h3>
            <table class="tbl"><thead><tr><th>rejim</th><th class="num">ham</th><th class="num">küçültülmüş</th><th class="num">n</th><th class="num">ağırlık w</th></tr></thead>
            <tbody>${hl.map(([k, v]) => `<tr><td><code>${esc(k)}</code></td>
              <td class="num mut">${trn(v.ham, 4)}R</td><td class="num"><b>${trn(v.kucultulmus, 4)}R</b></td>
              <td class="num">${v.n}</td><td class="num ${v.agirlik < 0.2 ? "warn" : "mut"}">${trn(v.agirlik, 3)}</td></tr>`).join("")}</tbody></table>
            <p class="hint">τ²=${trn(sh.tau2, 6)} · genel ortalama ${trn(sh.genel_ortalama, 4)}R.
              ${sh.tau2 === 0 ? `<b class="warn">τ²=0: hücreler-arası yayılımın TAMAMI hücre-içi gürültüyle
              açıklanıyor — bu defterde rejimler arasında ÖLÇÜLEBİLİR gerçek fark YOK, bu yüzden her hücre
              genel ortalamaya TAM küçültüldü.</b>` : ""}
              <b>${esc(sh.beyan || "")}</b></p>`;
        }
        if (hr) {
          // UYGULANMIŞ ROTASYON SATIRI (R1, 2026-07-30). 2D bugüne kadar yalnız ÖNERİ gösteriyordu;
          // öneri uygulandıktan sonra kart bunu söylemek ZORUNDA, yoksa panoyu okuyan ya hâlâ öneri
          // bekler ya da sıfırlanmış sayacı "aşınma bitti" sanır (ikisi de yanlış hüküm).
          const ur = hr.uygulanan_rotasyon || null, dh = ur && ur.dondurulmus_holdout;
          o += `<h3 class="t" style="margin-top:16px">Holdout aşınması ${_chip("öneri — uygulamaz (2D)", "t-rv")}</h3>
            ${!ur ? "" : `
            <div class="srow"><span>Uygulanmış rotasyon</span><b>${esc(ur.pencere_id || "—")}
              <span class="mut">· ${esc(ur.tarih || "—")} · önceki ${esc(ur.onceki || "—")}
              · OOS ${esc((ur.yeni_geometri || {}).oos_start || "")} → ${esc((ur.yeni_geometri || {}).oos_end || "")}</span></b></div>
            ${!dh ? "" : `<div class="srow"><span>Dondurulmuş holdout <span class="mut">(insana raporlanır, kabule girmez)</span></span>
              <b class="mut">${esc(dh.baslangic || "")} → ${esc(dh.son_DONMUS || "")}
                <span class="mut">· bugün ${esc(dh.bugun_RAPOR || "")} (yuvarlanmaz — parmak izi kararlı kalsın)</span></b></div>`}
            ${!ur.arsiv ? "" : `<div class="srow"><span>Arşiv <span class="mut">(${esc(ur.onceki || "önceki")} — döndürüldü)</span></span>
              <b class="mut">${trn(ur.arsiv.toplam_sorgu, 0)} sorgu · silinmedi, yürürlükteki sayaca EKLENMEZ</b></div>`}`}
            <div class="srow"><span>En çok sorulmuş pencere <span class="mut">(yürürlükteki)</span></span>
              <b class="${(hr.oran || 0) >= 1 ? "neg" : "mut"}">${hr.en_cok_sorgu ?? "—"} / ${hr.limit ?? "—"} sorgu
                ${hr.oran != null ? `<span class="mut">· ${trn(hr.oran, 2)}× limit</span>`
                                  : `<span class="mut">· henüz ÖLÇÜLMEDİ (≠ aşınma yok)</span>`}</b></div>
            <p class="hint">${esc(hr.hukum || "")}</p>
            <p class="hint">${hr.kiyas_uyarisi ? `<b class="guven">${esc(hr.kiyas_uyarisi)}</b>` : ""}</p>
            ${hr.oneri ? `<p class="hint"><b>${esc(hr.oneri.eylem)}</b> — ${esc(hr.oneri.gerekce)}<br>
              Seçenekler: ${(hr.oneri.secenekler || []).map(x => esc(x)).join(" · ")}<br>
              <span class="warn">Maliyet: ${esc(hr.oneri.maliyet)}</span></p>` : ""}
            <p class="hint"><b>${esc(hr.beyan || "")}</b></p>`;
        }
        return o;
      })()}
      <p class="hint"><b>${esc(y.beyan || "")}</b> Zorla tasfiye YOKTUR: kapı yalnız YENİ girişi durdurur,
        açık pozisyon kendi kuralıyla kapanır (aksi hâlde defterin çıkış istatistiği bozulur ve "kapı mı
        işe yaradı, çıkış mı" bir daha ayrıştırılamaz).</p></div>`;
  })();

  // ---------- KÂR ŞELALESİ (S1A, 2026-07-29) ----------
  // "Edge var mı?" ile "para var mı?" AYNI SORU DEĞİL. Bir sinyal doğru yönü gösterip yine de para
  // kaybettirebilir: tepe görülür ama geri verilir, ya da friksiyon kalanı yer. Üç kayıp kaynağı tek
  // bir `r_multiple` sayısının içinde eriyordu; bu kart onları AYIRIR ve Aşama 3'ün (çıkış mimarisi)
  // kararlarını besler. exit_reason kırılımı 07-28 otopsisinin (kâr time_stop'tan, stoplar kanatıyor)
  // KALICILAŞMASIdır — tek seferlik bir elde-hesap bir hafta sonra kimsenin bakmadığı yerde eskir.
  const sSelale = (() => {
    const wf = ml.profit_waterfall || null;
    if (!wf || !wf.genel) return `<div class="card rise"${katKart("bilesenic:selale")}><h2 class="t">Kâr şelalesi · sinyal → çıkış → friksiyon → net</h2>
      ${kartOzeti({ deger: null, rozet: "ÖLÇÜLEMEDİ",
        meta: "şelale ölçülemedi — kapanmış işlem yetersiz; boş tablo \"kayıp yok\" DEĞİLDİR." })}
      <p class="empty">Şelale henüz ölçülemedi — en az birkaç kapanmış işlem gerekir. Boş tablo "kayıp yok" DEĞİLDİR.</p></div>`;
    const g = wf.genel;
    // BAR GENİŞLİĞİ MUTLAK DEĞERE GÖRE, EN BÜYÜK BACAK %100: bacaklar R cinsinden ve işaretli;
    // ortak bir ölçek olmadan yan yana okunamazlar.
    const bacaklar = [
      // D1 · BAR RENGİ ROL ADIYLA: dördü de İŞARETLİ R büyüklüğü, yani YÖN rolü —
      // hue adıyla ("green"/"red"/"amber") bağlanmışlardı ve friksiyon şiddet kanalını
      // ödünç alıyordu. Friksiyon bir alarm değil, negatif bir bacaktır.
      ["Sinyalin sunduğu (MFE)", g.sinyal_mfe_r, "yon-arti"],
      ["Çıkışta geri verilen", g.geri_verilen_r, "yon-eksi"],
      ["Friksiyon", g.friksiyon_r == null ? null : -g.friksiyon_r, "yon-eksi"],
      ["NET (gerçekleşen)", g.net_r, g.net_r != null && g.net_r > 0 ? "yon-arti" : "yon-eksi"],
    ];
    const maks = Math.max(...bacaklar.map(b => b[1] == null ? 0 : Math.abs(b[1])), 0.0001);
    const bar = ([ad, v, renk]) => `<div class="srow"><span>${esc(ad)}</span>
      <b class="mono-num ${v == null ? "mut" : cls(v)}" style="min-width:96px;text-align:right">${v == null ? "ölçülmedi"
        : `${v > 0 ? "+" : ""}${trn(v, 3)}R`}</b></div>
      <div class="bar"><i style="width:${v == null ? 0 : Math.abs(v) / maks * 100}%;background:var(--${renk})"></i></div>`;
    const kol = "grid-template-columns:104px 52px 78px 78px 78px 1fr";
    const nedenler = Object.entries(wf.exit_reason || {}).map(([k, v]) =>
      `<div class="trow" style="${kol}">
        <span class="tick">${esc(k)}</span>
        <span class="mono-num mut">${v.n}</span>
        <span class="mono-num">${v.sinyal_mfe_r == null ? "—" : trn(v.sinyal_mfe_r, 2) + "R"}</span>
        <span class="mono-num">${v.geri_verilen_r == null ? "—" : trn(v.geri_verilen_r, 2) + "R"}</span>
        <span class="mono-num ${cls(v.net_r)}">${v.net_r == null ? "—" : (v.net_r > 0 ? "+" : "") + trn(v.net_r, 2) + "R"}</span>
        <span class="chain">çıkış verimi ${v.toplam_verim == null ? "tanımsız (MFE≤0)" : pctf(v.toplam_verim, 0)}
          <span class="mut">(toplulaştırılmış ΣR/ΣMFE)</span></span></div>`).join("");
    // KAPALI ÖZET (v198): kartın tek cümlesi NET R'dir; kanıtın gücü kapanmış işlem sayısıdır
    // (`wf.n`) ve payda ekranda yazar. ÇIKIŞ VERİMİ metada durur — "net +0,1R" cümlesi, MFE'nin
    // ne kadarının geri verildiği bilgisinden koparılırsa kartın kendi sorusunu cevaplamaz.
    return `<div class="card rise"${katKart("bilesenic:selale")}><h2 class="t">Kâr şelalesi · sinyal → çıkış → friksiyon → net</h2>
      ${kartOzeti({
        deger: g.net_r == null ? null : `${g.net_r > 0 ? "+" : ""}${trn(g.net_r, 3)}R`,
        degerSinif: g.net_r == null ? "" : cls(g.net_r),
        oran: kanitOrani(wf.n), payda: "kapanmış işlem",
        meta: g.net_r == null
          ? "net R ölçülmedi — özdeşliğin bacakları kurulamadı; sıfır kâr DEĞİL, ölçüm yok."
          : `n=${wf.n} · çıkış verimi ${g.toplam_verim == null ? "tanımsız (MFE≤0)" : pctf(g.toplam_verim, 0)}${
              g.friksiyon_r == null ? "" : ` · friksiyon ${trn(g.friksiyon_r, 3)}R`}`,
        rozet: azOrnek(wf.n) ? "AZ VERİ" : "" })}
      <p class="hint">İşlem başına ortalama, R cinsinden. Özdeşlik: <code>${esc(wf.ozdeslik || "")}</code>${
        wf.ozdeslik_farki != null ? ` · artık ${trn(wf.ozdeslik_farki, 4)}` : ""} · n=${wf.n}.</p>
      ${bacaklar.map(bar).join("")}
      <div class="srow" style="margin-top:8px"><span>Çıkış verimi ${_chip("toplulaştırılmış", "t-rv")}</span>
        <b class="${g.toplam_verim == null ? "mut" : cls(g.toplam_verim)}">${g.toplam_verim == null
          ? "tanımsız — MFE toplamı sıfır ya da negatif" : pctf(g.toplam_verim, 1) + " · ΣR / ΣMFE"}</b></div>
      <h3 class="t" style="margin-top:14px">Çıkış nedenine göre</h3>
      ${nedenler ? `<div class="tbl"><div class="trow head" style="${kol}">
          <span>NEDEN</span><span>N</span><span>MFE</span><span>GERİ VERİLEN</span><span>NET</span><span>ÇIKIŞ VERİMİ</span></div>
        ${nedenler}</div>` : `<p class="empty">Çıkış nedeni kırılımı yok.</p>`}
      <p class="hint" style="margin-top:8px">${esc(wf.verim_tanimi || "")} · friksiyon kapsamı: ${esc(wf.friksiyon_kapsam || "")}.</p>
      <p class="hint">Bu kart <b>karar vermez</b>: hangi bacağın en çok sızdırdığını gösterir ve Aşama 3'ün
      (çıkış mimarisi) hipotezlerini besler. Bir çıkış kuralı ancak olasılıksal kapıdan geçen bir hipotezle değişir.</p></div>`;
  })();

  // ---------- WP-K TREND KOLU · CANLI GÖLGE-KİTAP (2026-08-01) ----------
  // `/api/diagnostics.trend_kitabi` (← trend_shadow.ozet) üretiliyordu ve panoda HİÇ okunmuyordu:
  // EDG-2026-009'un hükümlü incumbent kolu canlı barlar üzerinde sanal bir defterde yürüyor, ama
  // operatör defterin doğup doğmadığını bile göremiyordu.
  //
  // TASARIM İLKESİ — ŞERH RAKAMDAN AYRILAMAZ. `pit_serh` kitabın İÇİNDE taşınıyor (trend_shadow
  // her yazımda yeniden çakıyor) ve burada da rakamlarla AYNI kartta, METİN olarak çıkar. Şerhi
  // bir tooltip'e, bir "detay" çekmecesine ya da başka bir karta koymak, +13,1p/yıl'ı şerhsiz
  // okutmanın en kolay yoludur — kolun hükmü "yanlılık-düşülmüş ~6-7p/yıl"dır ve o cümle rakamın
  // yanında durmazsa rakam yalan söyler.
  // GETİRİ YÜZDESİ YEŞİL/KIRMIZI BOYANMAZ: bu defter SANALDIR ve sıfır yetkilidir; canlı PnL ile
  // aynı görsel dile sokmak, kartı bir kazanç tablosu gibi okuturdu.
  const sTrend = (() => {
    const tk = d.trend_kitabi || null;
    if (!tk) return `<div class="card rise"${katKart("golge:trend")}><h2 class="t">Trend kolu · canlı gölge-kitap</h2>
      ${kartOzeti({ deger: null, rozet: "ÖLÇÜLEMEDİ",
        meta: "/api/diagnostics <code>trend_kitabi</code> alanı boş — defterin hâli ölçülemedi (kitap yok DEĞİL)." })}
      <p class="empty">Özet servis edilmiyor — /api/diagnostics <code>trend_kitabi</code> alanı boş.</p></div>`;
    if (!tk.var) return `<div class="card rise"${katKart("golge:trend")}><h2 class="t">Trend kolu · canlı gölge-kitap ${_chip("DOĞMADI", "t-vi")}</h2>
      ${kartOzeti({ deger: null, rozet: "DOĞMADI",
        meta: "state/trend_book.json henüz yazılmadı — ilk giriş ilk ay-sonunda olur (pozisyon 0 DEĞİL)." })}
      <p class="hint" style="margin-top:0">Defter (<code>state/trend_book.json</code>) henüz yazılmadı — kitap
      GEÇMİŞSİZ doğar ve ilk giriş ilk AY-SONUNDA olur. Bu bir arıza değil, kolun dürüst başlangıç hâlidir;
      "pozisyon 0" ile "defter yok" AYNI cümle değildir ve burada ikincisi yazıyor.</p></div>`;
    return `<div class="card rise"${katKart("golge:trend")}><h2 class="t">Trend kolu · canlı gölge-kitap
        ${_chip("SANAL · SIFIR YETKİ", "t-rv")}</h2>
      ${kartOzeti({
        // Değer SANAL özsermayedir ve ffill damgasını YANINDA taşır — özet, kartın kendi
        // dürüstlük şerhini kaybederek kısalamaz. Renk YOK: bu defter sıfır yetkili, canlı
        // P&L'in görsel diline sokulmaz (kartın kendi kuralı, aynen özete taşındı).
        deger: tk.equity == null ? null : _dolduruldu(money(tk.equity), tk.son_dolduruldu),
        oran: kanitOrani(tk.kapanan), payda: "kapanan işlem",
        meta: tk.equity == null
          ? "eğri boş — sanal özsermaye ölçülmedi (sıfır DEĞİL); defter doğdu, ilk bar bekleniyor."
          : `${trn(tk.pozisyon)} pozisyon · ${trn(tk.kapanan)} kapandı · ${trn(tk.gun)} gün eğri`,
        // PIT şerhi defterden düşmüşse bu bir SAPMAdır: rakamlar şerhsiz okunmamalı ve kart
        // kapağın altında kalmamalı. Rozet dikkat işaretidir; kurucu kartı açık doğurur.
        rozet: tk.pit_serh ? "" : "PIT ŞERHİ DÜŞMÜŞ",
        degerSinif: tk.pit_serh ? "" : "warn" })}
      <p class="hint" style="margin-top:0">EDG-2026-009'un hükümlü incumbent kolu (chandelier çıkış × N=10 × 12-1 momentum)
        canlı barlar üzerinde <b>sanal</b> bir defterde ileri yürütülüyor. Ölçüm DEĞİL — ölçülmüş bir hükmün
        canlı birikimi; emir yolu <b>import bile edilmiyor</b>.</p>
      <div class="srow"><span>Defter durumu</span><b>DOĞDU${
        tk.last_session ? ` · son seans ${esc(String(tk.last_session).slice(0, 10))}` : ""}${
        tk.last_run ? ` <span class="mut">· son koşum ${esc(String(tk.last_run).replace("T", " ").slice(0, 16))}</span>` : ""}</b></div>
      <div class="srow"><span>Açık pozisyon / kapanan işlem</span><b>${tk.pozisyon ?? 0} pozisyon ·
        <span class="mut">${tk.kapanan ?? 0} kapandı · ${tk.gun ?? 0} gün eğri</span></b></div>
      <div class="srow"><span>Sanal özsermaye</span><b>${tk.equity == null ? '<span class="mut">ölçülmedi — eğri boş</span>'
        : `${_dolduruldu(money(tk.equity), tk.son_dolduruldu)} <span class="mut">· nakit ${money(tk.nakit)}${
          tk.getiri_pct != null ? ` · defter başından beri ${isr(tk.getiri_pct, "%" + trn(tk.getiri_pct, 3))}` : ""}</span>`}</b></div>
      ${_dolduranSeanslar(tk)}
      ${tk.pit_serh ? `<p class="hint" style="margin-top:10px"><b class="warn">PIT ŞERHİ (rakamdan ayrılamaz):</b>
        ${esc(tk.pit_serh)}</p>`
        : `<p class="hint" style="margin-top:10px"><b class="neg">PIT ŞERHİ DEFTERDEN DÜŞMÜŞ.</b>
        Şerh kitabın içinde taşınır ve her yazımda yeniden çakılır; yokluğu bir görüntü kusuru değil,
        defterin kendisinde bir kırılmadır — rakamlar şerhsiz okunmamalı.</p>`}</div>`;
  })();

  // ---------- ÖĞRENME ÇARKI · HİPOTEZ HUNİSİ (2026-07-27) ----------
  // Huninin NEREDE öldüğü tek bir "ship yok" cümlesinden okunamaz. Sayılar 0 olsa da satır çıkar —
  // 0 dürüst bir sayıdır ve satırın hiç görünmemesi "ölçmedik" ile "hiç olmadı"yı aynı yapardı.
  // by_status'ta tanımadığımız durumlar "diğer" altında TOPLANIR: sessiz düşürme, huniyi kapatan
  // sızıntının ta kendisidir (toplam tutmazsa hangi kovada olduğu görünmez olurdu).
  const dw = ml.deflate_why || {}, byst = dw.by_status || {};
  const SHIP_ST = ["live", "promoted", "superseded", "rolled_back"];   // deflate_why'ın ship tanımıyla BİREBİR
  const TERM_ST = ["promoted", "rolled_back", "superseded"];
  const kirilim = ks => ks.map(k => `${esc((HSTATUS[k] || [k])[0])} ${byst[k]}`).join(" · ");
  const redK = Object.keys(byst).filter(k => k.startsWith("rejected")).sort((a, b) => byst[b] - byst[a]);
  const digerK = Object.keys(byst).filter(k => !k.startsWith("rejected") && !SHIP_ST.includes(k));
  const termK = TERM_ST.filter(k => byst[k]);
  const topla = ks => ks.reduce((s, k) => s + (byst[k] || 0), 0);
  const maxN = Math.max(1, dw.n_hypotheses || 0);
  const huni = (ad, n, renk, detay) => `<div class="trow" style="grid-template-columns:150px 56px 1fr;align-items:center">
      <span>${esc(ad)}</span><b class="mono-num">${n}</b>
      <span class="bar"><i style="width:${(100 * n / maxN).toFixed(1)}%;background:var(--${renk})"></i></span></div>
    ${detay ? `<div class="chain" style="margin:-4px 0 8px 150px">${detay}</div>` : ""}`;
  const sCark = `<div class="card rise"><h2 class="t">Öğrenme çarkı · hipotez hunisi</h2>
    ${/* D1 · HUNİ BİR VERİ ÖLÇEĞİDİR (rol 5), bir alarm merdiveni değil: "kapı reddi"
         kırmızı, "ship" yeşil basılıyordu — sayımlar şiddet kanalını ödünç alıyordu ve
         reddedilen bir hipotez bir arıza değil, arama katmanının normal ürünü. Yerine
         tek-hue LUMINANS merdiveni (IC_SERI'nin ölçülmüş reçetesi): hunide aşağı
         indikçe mürekkep koyulaşır. */""}
    ${huni("doğan hipotez", dw.n_hypotheses ?? 0, "tx3", "arama katmanının ürettiği her aday")}
    ${huni("kapı reddi", topla(redK), "band-2", redK.length ? kirilim(redK) : "hiç red yok")}
    ${huni("ship", dw.shipped ?? 0, "accent", `canlıya çıkan sürüm (${SHIP_ST.join("/")})`)}
    ${huni("ölçülen", dw.measured ?? 0, "violet", `arama tahmini (predicted_delta_search) ize düşmüş satır${dw.legacy_ships ? ` · ${dw.legacy_ships} eski ship alansız` : ""}`)}
    ${huni("terminal", topla(TERM_ST), "amber", termK.length ? kirilim(termK) : "henüz terfi/geri alma/devralma yok")}
    ${huni("diğer", topla(digerK), "tx3", digerK.length ? kirilim(digerK) : "tanınmayan durum yok — huni tam kapanıyor")}
    <p class="hint" style="margin-top:10px">Sıfır bir ARIZA değil, o günün dürüst hâli. "diğer" kovası boş değilse huninin
    bilinmeyen bir kolu var demektir — sessizce düşürülmesin diye burada sayılır.</p></div>`;

  // ---------- INTRADAY · CANLI AKIŞ (2026-07-27) ----------
  // SEANS DIŞINDA SIFIR SAYAÇ NORMALDİR. Aynı sıfırı kırmızıyla göstermek her akşam yanlış alarm
  // üretir ve gerçek kesintiyi görünmez kılar — kart "kopuk" ile "seans bekleniyor"u AYIRIR.
  const iq2 = d.intraday || {}, bf2 = d.barfeed || {}, dec2 = iq2.decisions || {};
  const akisSessiz = !(bf2.events_read || bf2.frames_seen);
  const akisEt = bf2.ok === true ? (akisSessiz ? ["seans bekleniyor", "t-vi"] : ["AKIŞ CANLI", "t-go"])
    : (bf2.running ? ["tüketici ayakta · Redis yok", "t-vi"] : ["akış başlamadı", "t-vi"]);
  const sonKarar = (dec2.recent || [])[0];
  const sIntra = `<div class="card rise"><h2 class="t">Intraday · Faz 4a gözlem ${_chip(akisEt[0], akisEt[1])}</h2>
    <div class="srow"><span>Dayanıklı tetik</span><b class="${bf2.ok === true && !akisSessiz ? "pos" : ""}">${bf2.running ? "tüketici koşuyor" : "tüketici durdu"} ·
      ${bf2.events_read ?? 0} olay · ${bf2.frames_seen ?? 0} bar${bf2.pending ? ` · <span class="warn">${bf2.pending} bekleyen</span>` : ""}</b></div>
    <div class="srow"><span>Silahlı plan (EOD)</span><b class="${iq2.armed_plans ? "" : "mut"}">${iq2.armed_plans
      ? `${iq2.armed_plans} plan izleniyor · ${iq2.watched ?? 0} sembol`
      : "seans silahsız açılıyor — gözlemin ölçecek şeyi yok"}</b></div>
    <div class="srow"><span>Bugünkü karar / toplam</span><b>${dec2.today ?? 0} bugün · ${dec2.total ?? 0} toplam · ${dec2.fired ?? 0} tetik-geçişi</b></div>
    <div class="srow"><span>Son karar</span><b class="${sonKarar ? "" : "mut"}">${sonKarar
      ? `${esc(sonKarar.ticker || "?")} · ${esc((sonKarar.bar_t || "").slice(11, 16))} UTC · ${sonKarar.fired === true ? "GEÇTİ" : (sonKarar.fired === false ? "eşik altı" : "eşiksiz")}`
      : "henüz karar satırı yok"}</b></div>
    ${iq2.last_error ? `<div class="srow"><span>Son hata</span><b class="neg">${esc(iq2.last_error)}</b></div>` : ""}
    <p class="hint" style="margin-top:10px">Gözlem-modu SIFIR YETKİLİDİR: emir göndermez, deftere dokunmaz — yalnız ölçer.
    Seans kapalıyken sayaçların 0 olması <b>beklenen</b> hâldir; kesinti ancak seans açıkken sayaç ilerlemiyorsa vardır.
    Ayrıntı ve silahlama anahtarı <b>Portföy &amp; Emirler → seans-içi silahlanma</b> bölümünde
    (S2R-2'de taşındı; bu satır oraya bakmasaydı operatör var olmayan bir sayfayı arardı).</p></div>`;

  // ---------- BÖLÜM 4 · VERİ HATTI & KARANTİNA ----------
  const xc = pl.crosscheck || {}, io = pl.io || {};
  const xcCls = xc.status === "diverged" ? "neg" : (xc.status === "ok" ? "pos" : "warn");
  const quar = (pl.quarantine || []).map(t => _chip(t, "t-no")).join(" ");
  // KAPALI ÖZET (v198): bölümün kendi sorusu "hat sağlam mı?" — özet KARANTİNAdaki sembol
  // sayısını ve sabır sayacını taşır. `?? 0` YOK: sabır sayacı ölçülemediyse çubuk çizilmez
  // (payda var ama pay yok) ve meta nedenini yazar.
  const _sabirMax = pl.refetch_max || 8;
  const _sabirN = Number.isFinite(Number(pl.refetch_attempts)) ? Number(pl.refetch_attempts) : null;
  const _karantinaN = (pl.quarantine || []).length;
  const s4 = `<div class="card rise"${katKart("veriboru:karantina")}><h2 class="t">Bölüm 4 · Veri hattı & karantina</h2>
    ${kartOzeti({
      deger: _karantinaN, degerSinif: _karantinaN ? "warn" : "",
      oran: _sabirN == null ? null : _sabirN / _sabirMax, payda: `EOD sabır adımı (${_sabirMax})`,
      meta: _sabirN == null
        ? `karantinada ${_karantinaN} sembol · EOD sabır sayacı ölçülemedi (0 deneme DEĞİL) · SPY çapraz-doğrulama ${esc(xc.status || "—")}`
        : `karantinada ${_karantinaN} sembol · EOD sabır ${_sabirN}/${_sabirMax} · SPY çapraz-doğrulama ${esc(xc.status || "—")}`,
      rozet: _karantinaN ? "KARANTİNA" : (xc.status === "diverged" ? "SPY SAPMASI" : "") })}
    <div class="gaugewrap">
      ${(() => {
        // Burada karşılaştırma ölçüsü GERÇEKTEN var: `refetch_max` bir eşiktir — o sayıda
        // denemede pes edilir. Bu yüzden dik çizgi çizilir. Halkada bu eşik hiç görünmüyordu,
        // yalnız "3/8" metninden çıkarılabiliyordu.
        // `|| 0` KULLANILMIYOR: alan hiç gelmediğinde "0/8" yazmak "sıfır deneme yapıldı"
        // demektir, oysa bilinen tek şey ölçümün ELDE OLMADIĞIDIR. Sıfır bir ölçümdür,
        // yokluk değil. Eski halka bu ikisini birbirine karıştırıyordu.
        const mx = pl.refetch_max || 8;
        const n = Number.isFinite(Number(pl.refetch_attempts)) ? Number(pl.refetch_attempts) : null;
        return _bullet({
          deger: n, max: mx, hedef: mx, etiket: "EOD sabır",
          metin: n == null ? null : `${n}/${mx}`,
          renk: n == null ? "accent" : (n >= mx ? "sev-1" : (n / mx > 0.6 ? "sev-2" : "accent")),
          bantlar: [0.6, 1]});
      })()}
      <span class="cap"><b>8 adımlı sabır sayacı</b><br>EOD yayını gecikirse tazeleme bayrağı sıcak tutulur; ${pl.refetch_max || 8}. denemede pes edilir ve LOGLANIR.<br>son başarılı tazeleme: <b>${esc(pl.last_refetch_session || "—")}</b> · kazanç takvimi ${pl.earnings_attempts || 0}/5 deneme</span></div>
    <div class="srow" style="margin-top:12px"><span>SPY çapraz-doğrulama</span><b class="${xcCls}">${esc(xc.status || "—")}${xc.divergence != null ? ` · sapma ${xc.divergence}` : ""}${xc.status === "cache_stale" ? " (önbellek bayat — karşılaştırma yapılmadı)" : ""}</b></div>
    <div class="srow"><span>Atomik yazım (IO)</span><b>${io.p95_ms != null ? `p50 ${trn(io.p50_ms, 1)} · p95 ${trn(io.p95_ms, 1)} ms` : (io.writes ? io.writes + " yazım (p95 için ≥20)" : "—")}${io.p95_ms > 50 ? ' · <span class="neg">DARBOĞAZ</span>' : ""}</b></div>
    ${(() => { const cfd = pl.cf_fidelity; return `<div class="srow"><span>cf sadakati (sim↔gerçek)</span><b class="${cfd ? (cfd.fidelity_ok ? "pos" : "warn") : ""}">${cfd ? `r=${cfd.corr ?? "—"} · sapma ${cfd.mean_diff_r > 0 ? "+" : ""}${cfd.mean_diff_r}R · n=${cfd.n}${cfd.fidelity_ok ? "" : " · İSKONTOLU OKU"}` : "kesişim <5 — alınan planlar birikiyor"}</b></div>`; })()}
    ${(() => { const sm = pl.bar_source_seams || {};
      if (!sm.tickers) return "";
      const pairs = Object.entries(sm.by_pair || {}).map(([k, n]) => `${esc(k)} ${n}`).join(" · ");
      // Uyarı susturuldu (her sembolde her turda basılıyordu ve gerçek uyarıları boğuyordu),
      // ama DURUM burada duruyor: bu sembollerin geçmişi sabit kaynağa ait, yeni kaynak yalnız
      // yeni tarihleri ekleyebiliyor — düzeltme ölçeği karışmıyor.
      return `<div class="srow"><span>Kaynak dikişi (susturulmuş uyarı)</span>
        <b>${sm.tickers} sembol · ${pairs}</b></div>`; })()}
    ${(() => { const fu = pl.fmp_usage || {}; if (!fu.calls) return "";
      // FMP KOTA (2026-07-23): api.py üretiyordu ama pano OKUMUYORDU — 429 kesintileri diskte
      // birikip görünmez kalıyordu. Operatörün "kota neden bitti" sorusunun tek okunabilir cevabı.
      const oran = Math.round(100 * (fu.fails || 0) / fu.calls);
      // SEBEP DAĞILIMI + RESET SAATİ (2026-07-26): "418 başarısız" tek başına kota mı, auth mı, ağ
      // mı olduğunu söylemiyordu ve yanlış teşhis yanlış politikayı doğurur (çağrı bütçesi, sorun
      // ConnectError ise tamamen yanlış araç). `by_status` ve `quota_hits` YAZILIYOR ama panoda
      // okuyucusu yoktu. YOKSA GÖSTERİLMEZ — boş bir etiket uydurmaktansa satır kısalır.
      const bs = Object.entries(fu.by_status || {}).sort((a, b) => b[1] - a[1])
        .map(([k, n]) => `${esc(k)}:${n}`).join(" · ");
      const qh = (fu.quota_hits || [])[fu.quota_hits ? fu.quota_hits.length - 1 : 0];
      return `<div class="srow"><span>FMP kota (bugün)</span><b class="${fu.blocked_at ? "warn" : ""}">${fu.calls} çağrı · ${fu.fails || 0} başarısız (%${oran})${fu.blocked_at ? ` · ${fu.blocked_at}. çağrıda 429 bloklandı` : ""}${
        bs ? `<br><span class="mut" style="font-weight:400">${bs}</span>` : ""}${
        qh && qh.at ? `<br><span class="mut" style="font-weight:400">son 429: ${esc(String(qh.at).slice(0, 16).replace("T", " "))}${qh.key ? ` (${esc(qh.key)})` : ""}</span>` : ""}</b></div>`; })()}
    ${(() => { const nd = pl.symbol_no_data || {}; const cn = (nd.confirmed_no_data || []).length, sp = (nd.suspect || []).length;
      if (!cn && !sp) return "";
      // 'kaynak hatası' (429, geçici) ile 'sembol yok' (evren bakımı) AYRI: sağlıklı sembol
      // throttling yüzünden 'ölü' sanılmasın diye ikisini ayrı gösterir.
      return `<div class="srow"><span>Veri dönmeyen sembol</span><b class="${cn ? "warn" : ""}">${cn} doğrulanmış${sp ? ` · ${sp} şüpheli (kaynak hatası)` : ""}${cn ? ": " + nd.confirmed_no_data.slice(0, 5).join(", ") : ""}</b></div>`; })()}
    ${(() => { const ud = d.universe_drift; if (!ud) return "";
      // ENDEKSTEN DÜŞEN İSİM: elle bakımlı evrende ölü sembol var mı — üretiliyordu, panoda düşüyordu.
      return `<div class="srow"><span>Evren sapması</span><b class="${ud.n_stale ? "warn" : (ud.n_stale === 0 && ud.status === "ok" ? "pos" : "")}">${ud.status === "unknown" ? `bilinmiyor (${esc(ud.reason || "kaynak yok")})` : (ud.n_stale == null ? "sapma sayısı ÖLÇÜLMEDİ — bu satır 'liste temiz' DEMEZ"
             : `${trn(ud.n_stale)} endeksten düşen${ud.n_stale ? ": " + (ud.stale || []).slice(0, 5).join(", ") : " — liste temiz"}`)}</b></div>`; })()}
    ${(() => { const mx = pl.massive_crosscheck || {}; if (!mx.compared) return "";
      // MASSIVE ÇAPRAZ-KONTROL (K1, 2026-07-30): `massive_crosscheck.json` her canlı turda
      // birikiyordu ve ÜRETİMDE hiç okunmuyordu — beyan edilen okuyucu `crosscheck_report()`in tek
      // çağıranı testlerdi. codelaw'un DECLARED_SINKS düzyazısı onu aklıyordu (yasa okuyucunun VAR
      // olduğuna bakar, ÇAĞRILDIĞINA bakamaz), yani beyan alarmı susturmuş ama zinciri bağlamamıştı.
      // Bu satır o zinciri kapatır: iki bağımsız kaynağın ÖRTÜŞEN günlerdeki kapanış uyumu.
      const bad = (mx.mismatches || 0) > 0;
      return `<div class="srow"><span>Massive çapraz-kontrol (bar hakemliği)</span>
        <b class="${bad ? "warn" : "pos"}">${mx.compared} bar · ${mx.tickers} sembol · ${mx.mismatches || 0} uyuşmazlık${
        mx.mismatch_pct != null ? ` (%${(mx.mismatch_pct * 100).toFixed(2)})` : ""}${
        mx.max_dev != null ? ` · en büyük sapma %${(mx.max_dev * 100).toFixed(3)}${mx.max_dev_ticker ? ` (${esc(mx.max_dev_ticker)})` : ""}` : ""} · tol %${esc(String(mx.tol_pct ?? "—"))}</b></div>`; })()}
    ${(() => { const fv = pl.finviz || {}; if (!Object.keys(fv).length) return "";
      // FINVIZ — /api/hermes'ten TAŞINDI (K1, 2026-07-30): evren keşif kaynağının sağlığı hermes
      // yükünde servis ediliyordu ve HİÇBİR yüzeyi yoktu. Alan adları CANLI yükten doğrulandı
      // (finviz.status(): elite_token / health{ok} / last{date,source,n,reason}) — `health.ok`
      // null OLABİLİR ("hiç denenmedi") ve bu false ile aynı şey değildir.
      const hz = fv.health || {}, ls = fv.last || {};
      const durum = hz.ok === true ? ["hazır", "pos"] : hz.ok === false ? ["hata", "warn"]
                  : [fv.elite_token ? "denenmedi" : "token yok", "mut"];
      return `<div class="srow"><span>Finviz (evren keşfi)</span><b class="${durum[1]}">${durum[0]}${
        ls.source ? ` · son kaynak ${esc(String(ls.source))} (n=${ls.n ?? 0})` : ""}${
        ls.reason ? `<br><span class="mut" style="font-weight:400">${esc(String(ls.reason).slice(0, 110))}</span>` : ""}</b></div>`; })()}
    <div class="srow"><span>Karşı-olgusal defter</span><b class="${lg.cf_cap && lg.cf_open > lg.cf_cap * 0.8 ? "warn" : ""}">${lg.cf_open ?? 0}/${lg.cf_cap ?? "—"} açık · ${lg.cf_resolved ?? 0} çözülmüş · ${lg.trades ?? 0} gerçek işlem</b></div>
    <h3 class="t" style="margin-top:16px">Karantina odası</h3>
    ${quar ? `<p>${quar}</p><p class="hint warn">Bu semboller %25 eşiğine bakılmaksızın taramadan DIŞLANDI (Faz 0 zorlaması).</p>`
           : `<p class="hint">Karantina boş — evrendeki tüm barlar bütünlük kapısını geçti.</p>`}</div>`;

  // ---------- BÖLÜM 5 · BÜTÜNLÜK & DEFTER SÖZLEŞMESİ ----------
  // (2026-07-21) Yedi dedektör rapor üretiyordu ama HİÇBİR panel okumuyordu — denetimin bulduğu
  // "kanıt üretiliyor, tüketilmiyor" sınıfının ta kendisi. Panel o boşluğu kapatır.
  const ig = d.integrity || {}, lc = d.ledger_contract || {}, cov = d.coverage || {}, sv = d.sieve || {};
  // 8. DEDEKTÖR (2026-08-13): `divergence` — DEĞER eşitliği. `coherence`ın kardeşi ve ondan
  // sonra gelmesi anlamlıdır: o ZAMAN ölçer ("türev kaynağından eski mi?"), bu DEĞER ölçer
  // ("iki kaynak aynı şeyi mi söylüyor?"). Aynı saniyede yazılmış ZIT değerli iki dosya yedi
  // dedektörün hepsinden yeşil geçiyordu (denetim 2026-08-13 §5).
  const PAT_TR = { production: "üretkenlik", conservation: "korunum", determinism: "determinizm",
                   coherence: "tutarlılık", monotonicity: "monotonluk", ownership: "sahiplik",
                   parity: "makullük", divergence: "değer-eşitliği" };
  // ÜRETİCİ/TÜKETİCİ PARİTESİ (2026-07-22 denetimi): bu iki satır üreticinin GÖNDERDİĞİ TİPTEN
  // farklı bir tip varsayıyordu. watchdog.conservation_report `unexplained` alanını TAM SAYI
  // gönderir; burada dizi sanılıp `.length` okunuyordu → `(5 || []).length` = undefined →
  // `!undefined` = true, yani açıklanamayan plan VARKEN panel daima yeşil "temiz" gösteriyordu
  // ve "N AÇIKLANAMAYAN" metni hiç basılmıyordu. Tip ne olursa olsun doğru sayan yardımcı:
  const _say = x => Array.isArray(x) ? x.length : (typeof x === "number" ? x : 0);
  const _patOK = (k, v) => k === "production" ? !(v.starved || []).length
                 : k === "conservation" ? !_say(v.unexplained)
                 : k === "coherence" ? !(v.stale || []).length
                 : k === "ownership" ? v.ok !== false && !(v.lost || []).length
                 // `divergence`: yalnız AYRIK olgular ihlaldir. `olculemeyen` (kaynak okunamadı)
                 // ve `beyanli` (bilinçli ikizleme, kıyasa girmez) ihlal DEĞİLDİR — ölçülemeyeni
                 // kırmızı basmak, "ölçemedim" hükmünü "ihlal" diye anlatmak olurdu (C22 dersi).
                 : k === "divergence" ? !(v.ayrik || []).length
                 : v.ok !== false && !(v.regressions || []).length && !(v.shrunk || 0);
  // ---- ÜÇÜNCÜ DURUM: ÖLÇÜLEMEDİ (S2R-3 · denetim C21/C22'nin pano ayağı, 2026-08-02) ---------
  // `_patOK` İKİ DEĞERLİYDİ ve bu, watchdog'un iki yeni alanını (dedektor_dustu / olculemedi)
  // panoda GÖRÜNMEZ kılıyordu. Düşen bir dedektör artık `_DEDEKTOR_BOS` iskeletiyle dönüyor —
  // yani `starved: []`, `stale: []`, `lost: []` BOŞ gelir. Üç desende (üretkenlik/korunum/
  // tutarlılık) `_patOK` o boşluğu "bulgu yok" diye okur ve satır YEŞİL "temiz" basardı:
  // ölçülemeyen bir hüküm, ölçülmüş bir temizlik kılığında. UYDURMA YASAĞI'nın tam karşılığı.
  // Ters yön de yanlıştı: determinism fail-closed'ta `ok:false` döner ve son dal onu KIRMIZI
  // "İHLAL" basardı — oysa watchdog'un kendi cümlesi "ölçülemeyen bir hükmü ihlal diye anlatmak
  // da bir uydurmadır" (determinism_report, C22 yorumu).
  //
  // ÜÇÜNCÜ DURUM NE YEŞİL NE KIRMIZI. Görsel dil UYDURULMADI, panoda zaten var: `t-vi` çipi bu
  // panoda "ölçüm yok / hüküm yok" kanalıdır (sağlayıcı kartı: `["çağrı yok", "t-vi"]`; defter
  // sözleşmesi: `"boş"`; trend kitabı: `"DOĞMADI"`). Aynı çip burada da kullanılır — ikinci bir
  // nötr renk icat etmek, üç yıl sonra "hangi gri neydi?" sorusunu doğururdu.
  //
  // MAKİNE-OKUNUR AD SATIRDA DURUR: metin `olculemedi` (ve dedektör yalıtımı devredeyse
  // `detector_failed`) kelimelerini AYNEN yazar. Operatörün panodan okuduğu ad ile obs
  // günlüğünde (`integrity_detector_failed`) ve alarm katmanında greplediği ad AYNI olmalı;
  // yalnız Türkçe bir cümle yazmak, panoyu günlükten koparırdı.
  const _patOlculemedi = v => !!v && (v.olculemedi === true || v.dedektor_dustu === true);
  const _patDurum = (k, v) => _patOlculemedi(v) ? "olculemedi" : (_patOK(k, v) ? "temiz" : "ihlal");
  const _patOlcumYok = v => `ÖLÇÜLEMEDİ — bu turda hüküm verilmedi (${
    v.dedektor_dustu ? "detector_failed · olculemedi" : "olculemedi"})${
    v.error ? ` · ${String(v.error).slice(0, 140)}` : ""}. Boş liste "bulgu yok" DEĞİL.`;
  const _patNote = (k, v) => _patOlculemedi(v) ? _patOlcumYok(v)
                 : k === "production" ? `${v.ok ?? 0}/${v.total ?? 0} mekanizma üretiyor${(v.starved || []).length ? ` · AÇ: ${v.starved.map(s => s.name).join(", ")}` : ""}${(v.waiting || []).length ? ` · ${v.waiting.length} bekliyor` : ""}`
                 : k === "conservation" ? `${v.plans ?? 0} plan → ${v.traded ?? 0} işlem · ${v.no_fill ?? 0} dolmadı${_say(v.unexplained) ? ` · ${_say(v.unexplained)} AÇIKLANAMAYAN` : ""}`
                 : k === "determinism" ? `${v.appended ?? 0} salt-ekleme defteri doğrulandı${v.shrunk ? ` · ${v.shrunk} defter KISALDI` : ""}`
                 : k === "coherence" ? `${v.ok ?? 0}/${v.total ?? 0} kalibrasyon taze${(v.stale || []).length ? ` · BAYAT: ${v.stale.map(x => `${x.artifact || x}${x.behind_h != null ? ` (${x.behind_h}sa geride)` : ""}`).join(", ")}` : ""}`
                 : k === "monotonicity" ? `${v.tracked ?? 0} sayaç izleniyor${(v.regressions || []).length ? ` · GERİLEME: ${v.regressions.map(x => `${x.field} ${x.was}→${x.now}`).join(", ")}` : ""}${(v.amnestied || []).length ? ` · AFFEDİLDİ: ${v.amnestied.map(a => `${a.field} ${a.was}→${a.now} (${a.reason || ""})`.slice(0, 120)).join(" | ")}` : ""}`
                 : k === "ownership" ? ((v.lost || []).length ? `${v.lost.length} sahipsiz alan: ${v.lost.map(x => `${x.file || "?"}.${x.field || "?"}`).join(", ")}` : "her kaydın sahibi var")
                 // ÜÇ SAYI, ÜÇ AYRI HÜKÜM: eşit / AYRIK / okunamayan kaynak. Beyanlı ikizlemeler
                 // ayrıca yazılır (kayıtta var, kıyasta yok) — sessiz muafiyet olmadıkları ancak
                 // ekranda görünürlerse doğrudur.
                 // `trn()` KULLANILIR, `?? 0` DEĞİL (2026-08-13, v196 çırçırı): bu satır ilk
                 // yazımında kardeşlerini (`production`/`coherence`) kopyalayıp `${v.esit ?? 0}/
                 // ${v.total ?? 0}` diyordu — ama tam o iki kardeş, nullsıfır triyajında **(a)
                 // YALAN SÖYLEYEN** olarak sınıflanmış ve kaldırma kuyruğunda duruyor
                 // (RAPOR.md §4, `app.js:4977`/`4980`: "yokluk 'ölçülmedi', basılan 0 'ölçtük,
                 // sıfır çıktı' der"). Yani kopyalanan şey desen değil KUSURDU ve çırçır 192→194
                 // GERİYE dönmüştü. `total` hiçbir zaman 0 olamaz (`len(EQUIVALENT_TRUTHS)`),
                 // dolayısıyla basılan "0/0 olgu eşit" ölçülmemiş bir turu "her şey kıyaslandı,
                 // hiçbiri eşit değil" diye okutur — iki yönlü uydurma. `trn()` yoklukta "—" basar.
                 : k === "divergence" ? `${trn(v.esit)}/${trn(v.total)} olgu eşit${(v.ayrik || []).length ? ` · AYRIK: ${v.ayrik.map(a => `${a.olgu} (${Object.entries(a.kaynaklar || {}).map(([n, d]) => `${n}=${JSON.stringify(d.deger)}`).join(" ≠ ")})`).join(", ")}` : ""}${(v.olculemeyen || []).length ? ` · ${v.olculemeyen.length} kaynak okunamadı: ${v.olculemeyen.map(o => `${o.olgu}/${o.kaynak}`).join(", ")}` : ""}${(v.beyanli || []).length ? ` · ${v.beyanli.length} beyanlı ikizleme (kıyas dışı)` : ""}`
                 : `${(v.rows || []).filter(r => r.ok).length}/${(v.rows || []).length} makullük denetimi geçti`;
  const PAT_CIP = { temiz: ["temiz", "t-go"], ihlal: ["İHLAL", "t-no"],
                    olculemedi: ["ÖLÇÜLEMEDİ", "t-vi"] };
  const patRows = Object.keys(PAT_TR).filter(k => ig[k]).map(k => {
    const v = ig[k], durum = _patDurum(k, v), [etiket, kls] = PAT_CIP[durum];
    // Metin de mertebe düşürür: ölçülemeyen satır `mut` ile yazılır. Ölçülmüş bir bulguyla aynı
    // mürekkeple yazılsaydı çip nötr olsa bile satır "okunmuş bir hüküm" gibi tararnırdı.
    return `<div class="trow" style="grid-template-columns:110px 1fr auto">
      <span class="tick">${esc(PAT_TR[k])}</span><span class="chain${
        durum === "olculemedi" ? " mut" : ""}">${esc(_patNote(k, v))}</span>
      ${_chip(etiket, kls)}</div>`;
  }).join("");
  // ÖLÇÜLEMEYEN DEDEKTÖR SAYISI BAŞLIKTA DA GÖRÜNÜR: yedi satırın içinde tek bir nötr çipi
  // kaçırmak kolaydır ve "7 desen temiz" izlenimi tam da bu kaçışla doğar.
  const patOlcumsuz = Object.keys(PAT_TR).filter(k => ig[k] && _patOlculemedi(ig[k]));
  // KOLON GENİŞLİĞİ ÖLÇÜLDÜ, SEÇİLMEDİ (v205, 2026-08-07). Bindirmeyi `.trow > *` sınıf kuralı
  // kapatıyor (index.html) — ama SARMALAMA da bir maliyettir ve bu panelde maliyet İSTİSNA değil
  // KURAL olurdu. `r.check` evreni kaynaktan sayıldı (watchdog.py: 18 düz ad + `yeniden_hesap:`
  // önekli 13 recompute satırı + `eleme:{aşama}:{kural}` çarpımı = 97 olası ad; medyan 38 karakter,
  // en uzunu 54 = `eleme:llm_opinion_calibration.gercek:sema_orani_yuksek`). 190px'te bu evrenin
  // %84'ü taşıyordu — yani neredeyse HER satır iki satıra sarardı ve "yoğun uzman defteri" düzeni
  // sarma yüzünden bozulurdu. Ölçülen diz noktası 340px'te: 320→340px arası tek-satır oranı
  // %39'dan %63'e sıçrıyor (medyan kümesi 38 karakter ≈ 330px orada geçiyor). Kalan %37 sarar —
  // kırpılmaz, bindirmez. Kolon genişliği SABİT kalır (minmax/max-content DEĞİL): her `.trow`
  // KENDİ ızgara kabıdır, içeriğe uyan bir kolon satırdan satıra farklı genişlik alır ve defterin
  // sütun hizası — bu tablonun tek okuma dayanağı — dağılırdı.
  const parityBad = ((ig.parity || {}).rows || []).filter(r => !r.ok).map(r =>
    `<div class="trow" style="grid-template-columns:340px 1fr">
      <span class="tick">${esc(r.check)}</span><span class="chain sev-1">${esc(r.detail || "")}</span></div>`).join("");
  const lcRows = Object.entries(lc.detail || {}).map(([nm, v]) => {
    const viol = Object.entries(v.violations || {}).map(([k, n]) => `${k} ×${n}`).join(" · ");
    return `<div class="trow" style="grid-template-columns:170px 1fr auto">
      <span class="tick">${esc(nm.replace(".jsonl", ""))}</span>
      <span class="chain${v.ok ? "" : " neg"}">${esc(v.rows ? (v.ok ? `${v.rows} satır · sözleşmeye uygun` : viol) : "defter boş")}</span>
      ${_chip(v.ok ? (v.rows ? "uygun" : "boş") : "İHLAL", v.ok ? (v.rows ? "t-go" : "t-vi") : "t-no")}</div>`;
  }).join("");
  const wv = Object.entries(lc.writer_violations || {}).map(([nm, v]) =>
    `<div class="trow" style="grid-template-columns:170px 1fr"><span class="tick">${esc(nm)}</span>
     <span class="chain sev-1">beyansız yazar: ${esc((v.beyan_edilmemis_yazar || []).join(", ") || "—")}${(v.beyan_edilip_yazmayan || []).length ? ` · yazmayan: ${esc(v.beyan_edilip_yazmayan.join(", "))}` : ""}</span></div>`).join("");
  // ---- TAZELİK ROZETİ (K1, 2026-07-30) -----------------------------------------------------
  // api.py:1300-1301 ve watchdog.py:660-661 açık bir TASARIM SÖZÜ veriyor: "pano raporun kaç
  // saniye önce hesaplandığını söyler, taze gibi göstermez". `integrity_age_s` bu yüzden dışarı
  // veriliyordu — ama pano onu HİÇ okumuyordu (repo genelinde sıfır eşleşme), yani 20 sn TTL'li
  // önbellekten gelen rapor ekranda YAŞSIZ basılıyordu. Söz kod yorumunda yaşıyordu, ekranda değil.
  // 0.0 = bu istekte hesaplandı; büyükse rapor önbellekten geldi ve o kadar saniye eskidir.
  const _ageS = d.integrity_age_s;
  const ageBadge = _ageS == null ? ""
    : `<span class="tag ${_ageS >= 15 ? "t-vi" : "t-go"}" style="font-weight:400;font-size:10px;margin-left:8px"
        title="Rapor 20 sn'lik önbellekten okunur; bu sayı kaç saniye önce hesaplandığını söyler (0 = bu istekte).">${
        _ageS <= 0 ? "şu an hesaplandı" : `${esc(String(_ageS))} sn önce hesaplandı`}</span>`;
  // KAPALI ÖZET (v198). ÜÇ DURUM ÜÇ SAYIYA ÇEVRİLİR ve payda UYGULANABİLİR desendir — yani
  // ölçülemeyen dedektörler paydadan DÜŞER, paya girmez. "7 desen temiz" izlenimi tam olarak
  // burada doğuyordu: ölçemeyen bir dedektörü temiz saymak, bu kartın kapattığı kusurun ta
  // kendisi. Kart B11'in kökü (tek kartta beş alt başlık); BÖLÜNMESİ D2-b'ye kalıyor — bu tur
  // sözleşmeyi kurar, içeriği bölmez.
  const _patKeys = Object.keys(PAT_TR).filter(k => ig[k]);
  const _patTemiz = _patKeys.filter(k => _patDurum(k, ig[k]) === "temiz").length;
  const _patIhlal = _patKeys.filter(k => _patDurum(k, ig[k]) === "ihlal").length;
  const _patUyg = _patTemiz + _patIhlal;
  // ---- BAŞLIK SAYISI ARTIK SABİT DEĞİL, RAPORDAN TÜRER (2026-08-13, denetim §3.6) ------------
  // ÖLÇÜLEN KUSUR: bu başlık "(7 desen)" yazıyordu ve AYNI KARTIN altındaki kapsam satırı
  // `${cov.patterns}` = 6 render ediyordu — tek görünümde 7 ve 6 yan yana, aralarında hiçbir
  // köprü yok. İkisi AYNI ŞEY DEĞİL: buradaki sayı ÇALIŞMA-ANI DEDEKTÖR ailesidir
  // (watchdog._DEDEKTOR_BOS), oradaki ise BİLEŞEN × DESEN KAPSAM MATRİSİnin desen ekseni
  // (integrity_registry.PATTERNS). Aynı sözcükle ("desen") adlandırıldıkları için çelişki gibi
  // okunuyordu. İki düzeltme birden: (1) sayı raporun kendisinden türer — 8. dedektör eklenince
  // başlık kendiliğinden 8 der, elle senkron YOKTUR; (2) alt satır artık "kapsam matrisi deseni"
  // diye ADLANDIRILIR, yani iki sayı iki ayrı soruyu cevapladığını söyler.
  // ÜÇÜNCÜ HÂL: pano tanımadığı bir dedektör görürse (backend ilerledi, pano geride kaldı) bunu
  // SÖYLER — sessizce düşürmek, tam da bu kartın kapattığı "görünmez kapsam daralması"dır.
  const _patBilinmeyen = Object.keys(ig).filter(k => !(k in PAT_TR) && ig[k] && typeof ig[k] === "object");
  const s5 = `<div class="card rise"${katKart("veriboru:butunluk")}><h2 class="t">Bölüm 5 · Bütünlük dedektörleri (${
      _patKeys.length ? `${_patKeys.length} dedektör` : "dedektör raporu yok"})${
      _patBilinmeyen.length ? " " + _chip(`${_patBilinmeyen.length} DEDEKTÖR PANODA TANIMSIZ`, "t-vi") : ""}${
      patOlcumsuz.length ? " " + _chip(`${patOlcumsuz.length} DEDEKTÖR ÖLÇEMEDİ`, "t-vi") : ""}${ageBadge}</h2>
    ${kartOzeti(!_patKeys.length ? {
      deger: null, rozet: "ÖLÇÜLEMEDİ",
      meta: "/api/diagnostics <code>integrity</code> hiçbir desen döndürmedi — dedektörler koşmadı (temiz DEĞİL)." }
    : { deger: `${_patTemiz} → ${_patIhlal}`, degerSinif: _patIhlal ? "warn" : "",
        oran: _patUyg ? _patTemiz / _patUyg : null,
        payda: _patUyg ? `uygulanabilir desen (${_patUyg})` : "",
        meta: `${_patIhlal} desen düşüyor · ${patOlcumsuz.length} dedektör ölçemedi${
          _ageS == null ? "" : ` · ${_ageS <= 0 ? "şu an hesaplandı" : esc(String(_ageS)) + " sn önce hesaplandı"}`}`,
        rozet: _patIhlal ? `${_patIhlal} İHLAL` : (patOlcumsuz.length ? "ÖLÇEMEYEN DEDEKTÖR" : "") })}
    ${patRows || '<p class="hint">Bütünlük raporu yok.</p>'}
    ${patOlcumsuz.length ? `<p class="hint">Bu turda hüküm veremeyen dedektör: <b>${
      esc(patOlcumsuz.map(k => PAT_TR[k]).join(", "))}</b> (watchdog <code>olculemedi</code>/<code>detector_failed</code>).
      Yalıtım çalıştı — diğerleri koştu; ama ölçülemeyen desen <b>temiz sayılmaz</b> ve bu satırlar
      ne yeşil ne kırmızıdır. Kanıt duruyor, tespit bir tur ertelendi.</p>` : ""}
    ${_patBilinmeyen.length ? `<p class="hint neg">Bekçi bu panonun TANIMADIĞI dedektör(ler) döndürdü:
      <b>${esc(_patBilinmeyen.join(", "))}</b>. Arka uç ilerledi, pano geride kaldı — satırları
      yukarıda GÖRÜNMÜYOR. Sessizce düşürmek, bu kartın kapattığı kusurun kendisi olurdu.</p>` : ""}
    <p class="hint">Testler "kod çalışıyor mu" der; bu dedektörler "sistem üretiyor mu, kaybetmiyor
    mu, ürettiği kanıt tüketilebilir mi, iki kaynak aynı şeyi mi söylüyor" diye sorar.
    2026-07-21'de motorun evrenin %18'inde karar verdiği hatayı yalnız <b>makullük</b> görebiliyordu;
    2026-08-13'te eklenen <b>değer-eşitliği</b> ise ilk yedisinin yapısal kör noktasını kapatır —
    onlar ZAMAN ölçer, o DEĞER ölçer (aynı saniyede yazılmış zıt değerli iki dosya hepsinden
    yeşil geçiyordu).</p>
    ${parityBad ? `<h3 class="t" style="margin-top:16px">Makullük ihlalleri</h3>${parityBad}` : ""}
    <h3 class="t" style="margin-top:16px">Defter sözleşmesi · ${lc.compliant ?? "—"}/${lc.ledgers ?? "—"} uyumlu</h3>
    ${lcRows || '<p class="hint">Sözleşme raporu yok.</p>'}
    ${wv ? `<h3 class="t" style="margin-top:16px">Yazar ihlalleri</h3>${wv}`
         : `<p class="hint">Yazar sınırı temiz — her deftere yalnız sözleşmede beyan edilen modüller yazıyor.</p>`}
    <h3 class="t" style="margin-top:16px">Eleme muhasebesi · ${sv.n_stages ?? 0} aşama</h3>
    ${(() => {
      // "Veri yok" ile "veri elendi" AYRI şeylerdir. Bu tablo, her hesabın kaç satırla çalıştığını
      // ve kaçını NEDEN düşürdüğünü gösterir: sema: = yazılım hatası, piyasa: = meşru filtre.
      const rows = Object.entries(sv.stages || {}).map(([nm, st]) => {
        const kotu = st.sema_drops > 0 || (st.in > 0 && st.out === 0);
        return `<div class="trow" style="grid-template-columns:200px 1fr auto">
          <span class="tick">${esc(nm)}</span>
          <span class="chain${kotu ? " neg" : ""}">${st.in} girdi → ${st.out} kullanıldı${st.piyasa_drops ? ` · piyasa filtresi ${st.piyasa_drops}` : ""}${st.sema_drops ? ` · <b>şema ${st.sema_drops}</b>` : ""}</span>
          ${_chip(kotu ? "İHLAL" : "temiz", kotu ? "t-no" : "t-go")}</div>`;
      }).join("");
      const viol = (sv.violations || []).map(v =>
        `<p class="hint ${v.severity === "kritik" ? "neg" : "warn"}" style="margin-top:6px">${esc(v.detail)}</p>`).join("");
      return (rows || '<p class="hint">Henüz eleme kaydı yok — kalibrasyonlar bir kez koşunca dolar.</p>') + viol;
    })()}
    ${cov.cells_applicable ? `<div class="srow" style="margin-top:12px"><span>Denetim kapsamı (${cov.components} bileşen × ${cov.patterns} <b>kapsam matrisi deseni</b> — yukarıdaki dedektör sayısıyla AYNI ŞEY DEĞİL: bu statik bir bileşen×desen tablosudur, o çalışma-anı dedektör ailesi)</span><b>${cov.cells_covered ?? "—"}/${cov.cells_applicable} uygulanabilir hücre (%${trn(cov.coverage_pct, 1)}) · ham %${trn(cov.raw_pct, 1)} · ${cov.cells_na ?? 0} N/A${cov.open_gaps ? ` · <span class="neg">${cov.open_gaps} açık boşluk</span>` : ""}</b></div>` : ""}</div>`;

  // ---------- BÖLÜM 6 · REDIS SICAK KATMAN (intraday) ----------
  // (2026-07-23) Redis sıcak katmanı `/api/hermes`te üretiliyordu ama HİÇBİR panel okumuyordu —
  // "kanıt üretiliyor, tüketilmiyor" sınıfı. Intraday geçişinde Redis kritik altyapı; kendi başlığı olmalı.
  const hs = d.hotstate || {};
  const hsOk = hs.ok === true, hsDown = hs.ok === false;
  // Faz 2: piyasa-veri akışı (Alpaca dakikalık KAPANMIŞ bar → mrd:bars + sıcak fiyat).
  const mkt = d.marketstream || {};
  const mktOk = mkt.ok === true, mktDown = mkt.ok === false;
  const mktBlock = `<h3 class="t" style="margin-top:18px">Piyasa-veri akışı <span class="tx3" style="font-weight:400">(dakikalık bar → mrd:bars)</span>
      ${_chip(mktOk ? "CANLI" : (mktDown ? "KOPUK" : "—"), mktOk ? "t-go" : (mktDown ? "t-no" : "t-vi"))}</h3>
    <div class="srow"><span>Akış</span><b class="${mktOk ? "pos" : (mktDown ? "neg" : "")}">${mktOk ? "canlı · " + esc(mkt.feed || "iex") + " feed" : (mktDown ? "kopuk — döngü EOD bar dosyalarına düşer" : "henüz başlamadı")}${mkt.down_since ? " · " + relTime(mkt.down_since) : ""}</b></div>
    <div class="srow"><span>Akan bar / abone sembol</span><b>${mkt.bars_seen ?? 0} bar · ${mkt.subscribed ?? 0} sembol</b></div>
    ${mkt.last_bar_at ? `<div class="srow"><span>Son kapanmış bar</span><b>${relTime(mkt.last_bar_at)}${mkt.last_bar_age_s > 180 ? ' · <span class="warn">seyrek (piyasa kapalı olabilir)</span>' : ""}</b></div>` : ""}
    ${mktDown && mkt.last_error ? `<div class="srow"><span>Hata</span><b class="neg">${esc(mkt.last_error)}</b></div>` : ""}`;
  // KAPALI ÖZET (v198): iki akış (Redis + piyasa-veri) tek satırda. Payda "izlenen akış (2)" —
  // uydurma bir tavan değil, kartın kendi kapsamı. "henüz denenmedi" hâli ne bağlı ne kopuktur
  // ve paya girmez; meta onu adıyla söyler.
  const _akisBagli = (hsOk ? 1 : 0) + (mktOk ? 1 : 0);
  const _akisKopuk = (hsDown ? 1 : 0) + (mktDown ? 1 : 0);
  const s6 = `<div class="card rise"${katKart("veriboru:redis")}><h2 class="t">Bölüm 6 · Redis sıcak katman <span class="tx3" style="font-weight:400">(intraday)</span>
      ${_chip(hsOk ? "BAĞLI" : (hsDown ? "KOPUK" : "—"), hsOk ? "t-go" : (hsDown ? "t-no" : "t-vi"))}</h2>
    ${kartOzeti({ deger: `${_akisBagli}/2`, degerSinif: _akisKopuk ? "warn" : "",
      oran: _akisBagli / 2, payda: "izlenen akış (Redis + piyasa-verisi)",
      meta: `Redis ${hsOk ? "bağlı" : (hsDown ? "KOPUK" : "denenmedi")} · piyasa akışı ${
        mktOk ? "canlı" : (mktDown ? "KOPUK" : "başlamadı")} · ${trn(hs.reads)} okuma / ${trn(hs.writes)} yazma${
        hs.fails ? ` · ${hs.fails} hata` : ""}`,
      rozet: _akisKopuk ? "AKIŞ KOPUK" : "" })}
    <div class="srow"><span>Bağlantı</span><b class="${hsOk ? "pos" : (hsDown ? "neg" : "")}">${hsOk ? "bağlı · yanıt veriyor" : (hsDown ? "erişilemiyor — dosyaya düşülüyor" : "henüz denenmedi")}</b></div>
    <div class="srow"><span>Okuma / yazma / hata</span><b>${hs.reads ?? 0} okuma · ${hs.writes ?? 0} yazma${hs.fails ? ` · <span class="neg">${hs.fails} hata</span>` : " · 0 hata"}</b></div>
    ${hsDown ? `<div class="srow"><span>Kopuk</span><b class="neg">${hs.down_since ? relTime(hs.down_since) : "—"}${hs.last_error ? " · " + esc(hs.last_error) : ""}</b></div>` : ""}
    ${mktBlock}
    <p class="hint" style="margin-top:16px">Redis yalnız <b>uçucu</b> türev tutar — son fiyat, pozisyon sıcak kopyası, dakikalık bar tamponu (mrd:bars).
    Piyasa-veri akışı yalnız <b>kapanmış</b> dakikalık barı ingest eder (look-ahead güvenli). Kalıcı gerçek — işlemler, kararlar,
    karşı-olgular — <b>dosya defterlerinde</b> yaşar; Redis silinse veri kaybı YOK. <b>Kopuk</b> = sistem durmaz, EOD dosyalarına düşer.</p></div>`;

  // ---------- SAĞLAYICI SAĞLIK KARTI (pano turu 2026-07-31) ----------------------------------
  // /api/diagnostics `saglayicilar` bloğu temizlik turunda eklendi ve app.js'te TÜKETİCİSİ YOKTU:
  // beş adaptörün (finviz · massive · insider · shortinterest · alpaca veri/ticaret) sağlık
  // sayaçları üretiliyor, hiçbir yüzeyde okunmuyordu. Kartın kendi BEYANI da taşınır: sayaçlar
  // süreç-içidir, yeniden başlatmada sıfırlanır — boş satır "bozuk" değil "bu süreçte hiç çağrı
  // yapılmadı" demektir ve bu ayrım olmadan kart yanlış alarm üretir.
  const sSag = (() => {
    const blok = d.saglayicilar || null;
    if (!blok) return "";
    const satirlar = blok.saglayicilar || [];
    const rows = satirlar.map(p => {
      // ÇİP KIRMIZIDAN NÖTRE İNDİ (S2R-3): sağlık OKUMASININ düşmesi, sağlayıcının ARIZALI
      // olduğu anlamına gelmez — "ölçemedim" ile "son çağrı başarısız" iki ayrı hükümdür ve
      // ikincisi zaten aşağıdaki `t-no` satırında yaşıyor. Ölçülemeyeni ihlal diye boyamak,
      // bütünlük dedektörlerindeki (C21/C22) kusurun aynısıydı — aynı turda aynı dille kapandı.
      if (p.olculemedi) return `<div class="trow" style="grid-template-columns:120px 1fr auto">
        <span class="chain">${esc(p.ad)}</span>
        <span class="mut" style="font-size:12px">sağlık okuması istisna verdi (olculemedi): ${esc(p.olculemedi)}</span>
        ${_chip("ÖLÇÜLEMEDİ", "t-vi")}</div>`;
      // ok: true/false/null — null "bu süreçte hiç çağrılmadı"dır ve YEŞİL de KIRMIZI da değildir.
      const [lbl, kls] = p.ok === true ? ["sağlıklı", "t-go"]
        : (p.ok === false ? ["SON ÇAĞRI BAŞARISIZ", "t-no"] : ["çağrı yok", "t-vi"]);
      const ek = Object.entries(p.ek || {})
        .filter(([, v]) => v !== null && v !== undefined && v !== "")
        .map(([k2, v]) => `${esc(k2)}: ${esc(typeof v === "object" ? JSON.stringify(v) : String(v))}`)
        .join(" · ");
      const oran = p.hata_orani == null ? null : `hata oranı ${pctf(p.hata_orani, 1)}`;
      const sayac = [p.cagri != null ? `${p.cagri} çağrı` : null,
                     p.hata != null ? `${p.hata} hata` : null, oran].filter(Boolean).join(" · ");
      return `<div class="trow" style="grid-template-columns:120px 1fr auto;align-items:start">
        <span class="chain">${esc(p.ad)}</span>
        <span class="mut" style="font-size:12px">${esc(sayac || "sayaç boş")}${
          p.son_cagri_ts ? ` · son çağrı ${esc(relTime(p.son_cagri_ts) || "—")}` : ""}${
          ek ? `<br>${ek}` : ""}${
          p.son_hata ? `<br><span class="neg">${esc(String(p.son_hata).slice(0, 110))}</span>` : ""}</span>
        ${_chip(lbl, kls)}</div>`;
    }).join("");
    // KAPALI ÖZET (v198). PAYDA "ÇAĞRILAN adaptör": bu süreçte hiç çağrılmamış bir adaptör ne
    // sağlıklı ne arızalıdır ve paydaya girerse oran yalan söyler — kartın kendi beyanı zaten
    // bunu söylüyordu ("sayaçlar süreç-içidir"), özet o beyanı ödünç alır.
    const _sagCagrili = satirlar.filter(p => !p.olculemedi && p.ok != null);
    const _sagIyi = _sagCagrili.filter(p => p.ok === true).length;
    const _sagKotu = _sagCagrili.filter(p => p.ok === false).length;
    const _sagOlcum = satirlar.filter(p => p.olculemedi).length;
    return `<div class="card rise"${katKart("veriboru:saglayici")}><h2 class="t">Sağlayıcı sağlığı <span class="tx3" style="font-weight:400">(${satirlar.length} adaptör · kapsam: ${esc(blok.kapsam || "—")})</span></h2>
      ${kartOzeti(!_sagCagrili.length ? {
        deger: null, rozet: _sagOlcum ? "ÖLÇÜLEMEDİ" : "ÇAĞRI YOK",
        meta: `${satirlar.length} adaptörün hiçbiri bu süreçte çağrılmadı — sağlık ölçülemedi (arıza DEĞİL); ${_sagOlcum} adaptörde sağlık okuması istisna verdi.` }
      : { deger: `${_sagIyi}/${_sagCagrili.length}`, degerSinif: _sagKotu ? "warn" : "",
          oran: _sagIyi / _sagCagrili.length, payda: "çağrılan adaptör",
          meta: `${_sagKotu} adaptörde son çağrı başarısız · ${satirlar.length - _sagCagrili.length} adaptör hiç çağrılmadı${
            _sagOlcum ? ` · ${_sagOlcum} ölçülemedi` : ""}`,
          rozet: _sagKotu ? "SON ÇAĞRI BAŞARISIZ" : "" })}
      ${rows || '<div class="empty">Sağlayıcı satırı üretilmedi.</div>'}
      <p class="hint">${esc(blok.beyan || "")}</p></div>`;
  })();

  // ---------- ÖĞRENME BESLEMESİ (pano turu 2026-07-31) ---------------------------------------
  // /api/diagnostics `ogrenme` bloğu öğrenme-otomasyonu turunda eklendi, tüketicisi yoktu. Kart üç
  // kadansın SAĞLIĞINI gösterir (antrenman · Eksen-2 · kanıt dolgusu) — MLOps kartı o kadansların
  // ÇIKTILARINI taşır. İkisini aynı yere koymak "ölçüm kötü" ile "ölçüm hiç koşmadı"yı aynı
  // cümleye sıkıştırırdı; bu turun kapattığı kusurun ta kendisi.
  const sOgr = (() => {
    const o = d.ogrenme || null;
    if (!o) return "";
    const nb = o.nabiz || {}, an2 = o.antrenman || {}, kq = o.dolgu_kuyrugu, ex = o.eksen2;
    // ETİKET v192'DE DÜZELTİLDİ (operatör: "pano antrenman hiç koşmamış diyor"). Bu satır MODELİN
    // fit'ini DEĞİL, zamanlayıcının seans-sonrası KADANSINI (shadow_model.maybe_refit) ölçer.
    // Eski etiket "antrenman (gölge model fit)" ikisini tek şey sanmaya davet ediyordu; canlıda
    // kadans hiç koşmamışken model tazeydi ve kart bunu hiçbir yerde yazmıyordu. Fiilî fit artık
    // ayrı bir satırda (`Son fit`, aşağıda) ve tarihiyle duruyor.
    // v207 DÜZELTMESİ: rozet DOĞRU okuyordu ama okuduğu damga SİLİNMİŞTİ — kadans 2026-08-06'da
    // koşup eğitmişti; `ShadowTradeOutcomeModel.save()` üstüne yazarak damgayı yok ediyordu.
    // Kırmızı rozet artık yalnız GERÇEKTEN damga yokken çıkar; ayrımı `Son deneme` satırı taşır.
    const NABIZ_TR = { shadow_fit: "antrenman KADANSI (seans-sonrası kanca)", axis2_cycle: "Eksen-2 üreteci",
                       opinion_backfill: "kanıt dolgusu kadansı" };
    const nabizRows = Object.entries(nb).map(([k, v]) => {
      const [lbl, kls] = v.hic_kosmadi ? ["HİÇ KOŞMADI", "t-no"]
        : (v.bayat ? ["BAYAT", "t-rv"] : ["taze", "t-go"]);
      return `<div class="trow" style="grid-template-columns:1fr 150px auto">
        <span class="chain">${esc(NABIZ_TR[k] || k)}</span>
        <span class="mut" style="font-size:12px">${v.gecen_saat == null ? "damga yok"
          : `${trn(v.gecen_saat, 1)} sa önce · pencere ${trn(v.pencere_saat, 1)} sa`}</span>
        ${_chip(lbl, kls)}</div>`;
    }).join("");
    const terfi = an2.terfi || {};
    // ---- SON FİT (v192) ----------------------------------------------------------------------
    // Kartın en yüksek sesli satırı kadansın kırmızı "HİÇ KOŞMADI" rozetiydi ve yanında modelin
    // TAZE olduğunu söyleyen tek bir satır yoktu. Bu satır o boşluğu kapatır: fit'in ANI, örneklem,
    // eğitim Brier'i ve terfi HÜKMÜ + NEDENİ. Hüküm üç değerlidir (EVET / HAYIR / ÖLÇÜLEMEDİ):
    // "hayır" tabanı yenememektir, "ölçülemedi" kıyas verisinin hiç birikmemesidir — operatörün
    // eylemi ikisinde farklıdır, aynı kelimeyle yazılamaz.
    const sonFitRow = (() => {
      const sf = o.son_fit;
      if (!sf) return "";
      const hk = sf.terfi || {};
      if (!sf.ts && sf.n == null)
        return `<div class="srow"><span>Son fit</span><b class="guven">model hiç kurulmadı — fit kaydı YOK</b></div>`;
      const karar = hk.karar === "EVET" ? '<span class="pos">EVET</span>'
        : (hk.karar === "HAYIR" ? '<span class="warn">HAYIR</span>' : '<span class="mut">ÖLÇÜLEMEDİ</span>');
      // TARİHİN KAYNAĞI YAZILIR (v207). `kaynak:"kunye"` = fit'in kendi damgası (`fit_ts`) YOK,
      // tarih kayıt künyesinden ÇIKARILDI. v207 öncesi canlının hâli tam olarak buydu ve ayrımı
      // yazmayan bir tarih, çıkarımı damga gibi gösterirdi.
      const kaynakNotu = sf.kaynak === "kunye"
        ? ' <span class="mut" style="font-size:12px">(fit damgası yok — künyeden)</span>' : "";
      return `<div class="srow"><span>Son fit</span><b>${
        sf.ts ? esc(String(sf.ts).replace("T", " ").slice(0, 16)) + kaynakNotu : '<span class="mut">tarih yok</span>'
        } · n ${sf.n ?? "—"}${sf.n_real != null ? ` (gerçek ${sf.n_real} · cf ${sf.n_cf ?? 0})` : ""}${
        sf.brier_train != null ? ` · Brier ${trn(sf.brier_train, 4)}` : ""} · terfi: ${karar}</b></div>
        ${hk.neden ? `<p class="hint" style="margin-top:-4px">Terfi gerekçesi: ${esc(hk.neden)}</p>` : ""}`;
    })();
    // ---- SON DENEME (v207) -------------------------------------------------------------------
    // FİT ile DENEME AYRI OLGUDUR ve bu satır ayrımı ekrana koyar. v207 öncesi canlıda
    // `fit_attempt_ts` BOŞTU — pano da (damgayı doğru okuduğu için) kırmızı "HİÇ KOŞMADI"
    // basıyordu; oysa kadans dün koşup EĞİTMİŞTİ (scheduler_status: fitted=true, n_fit=2217).
    // Kök `save()`in üstüne-yazması olduğu için düzeltme damganın kendisindeydi, bu satırda değil;
    // satır ise "denendi ama fit gerekmedi" hâlinin "hiç koşmadı" diye okunmasını engeller.
    const sonDenemeRow = (() => {
      const sd = o.son_deneme;
      if (!sd) return "";
      if (!sd.damga_var)
        return `<div class="srow"><span>Son deneme</span><b class="warn">damga YOK — fit hiç denenmedi</b></div>`;
      return `<div class="srow"><span>Son deneme</span><b>${
        esc(String(sd.ts).replace("T", " ").slice(0, 16))} · <span class="mut">${
        sd.atlama_nedeni ? esc(String(sd.atlama_nedeni)) : "fit edildi"}</span></b></div>`;
    })();
    // ---- EKSEN-2: "0 ÜRETİLDİ"NİN NEDENİ (v207) ----------------------------------------------
    // ESKİ SATIR: "0 üretildi · 0 kaydedildi · 0 bekleyen · 0 otomatik uygulandı". Dört sıfır,
    // paydasız, yan yana — bir BAŞARISIZLIK gibi okunuyordu. Ölçüm başka söylüyor (canlı teşhis
    // kovaları): 67 skillin 60'ı gerçek katmanda HİÇ ölçülmemiş, 5'i motor içi; hüküm verilebilen
    // 2. Üreteç kanıt olmayan yerde öneri ÜRETMEZ — doğru okuma KANIT YOKLUĞUdur.
    //
    // ŞERİT O DÖRT SAYININ KENDİSİDİR, YANINA EKLENEN BEŞİNCİ BİR ŞEY DEĞİL: aynı sayılar kart
    // sözleşmesinin (D2-a) hücre dilinde — büyük değer + PAYDA-BEYANLI çubuk + meta — yeniden
    // yazıldı. Paydayı ekrana koymak burada bütün farkı yaratıyor: üretimin paydası 67 DEĞİL,
    // hüküm verilebilen 2'dir. "0/67" üretecin 67 skilde başarısız olduğunu söylerdi; oysa 65'inde
    // ölçüm yok, yani hüküm kurulamaz. DÖRT HÜCRE `.ozet-serit`in ızgara bütçesidir (4 sütun).
    const eksen2Blok = (() => {
      if (!ex) return `<div class="srow"><span>Eksen-2 üreteci</span><b class="warn">durum defteri yazılmamış — kadans HİÇ koşmadı</b></div>`;
      const oz = ex.ozet || null;
      const olculemedi = !oz || oz.durum !== "dolu";
      const mi = oz ? oz.motor_ici_esik_asan : null;
      const kv = Object.entries(ex.kovalar || {}).sort((a, b) => b[1] - a[1]);
      const dokum = kv.map(([k, n]) => `${esc(KOVA_TR[k] || k)}: ${n}`).join(" · ");
      const uretilen = ex.uretilen ?? null;
      // ÜRETİMİN PAYDASI: hüküm verilebilen skill. Sıfırsa payda YOKTUR (çubuk çizilmez) —
      // bölünecek bir taban olmadan doluluk uydurulamaz.
      const paydaVar = !olculemedi && oz.olculen > 0;
      // `?? 0` TRİYAJI (v196 kuyruğu, sınıf (a)): bu bloğun DÖRT `?? 0`ı raporun kuyruğundaydı —
      // "0 kaydedildi" ile "kaydedilen sayısı yükte yok" aynı piksele düşüyordu. Dördü de bu turda
      // ödendi: yokluk artık ADIYLA yazılır ve hücre `ÖLÇÜLEMEDİ` rozetine düşer.
      const say = v => v == null ? "ölçülemedi" : trn(v);
      const serit = ozetSerit([
        ozetHucre("Kanıt tabanı", {
          deger: olculemedi ? null : `${trn(oz.olculen)} / ${trn(oz.toplam_skill)}`,
          oran: olculemedi ? null : oz.oran,
          payda: olculemedi ? "" : oz.payda,
          meta: olculemedi
            ? esc(oz ? oz.neden : "Eksen-2 teşhis kovaları yükte YOK — üretecin sessizliği ÖLÇÜLEMEDİ, kanıt yokluğu İLAN EDİLEMEZ")
            : `hüküm verilebilen skill / katalog · <b>${trn(oz.olculmemis)}</b> gerçek katmanda hiç ölçülmemiş · <b>${trn(oz.korumali)}</b> motor içi (aday değil)`,
          rozet: olculemedi ? "ÖLÇÜLEMEDİ" : "" }),
        ozetHucre("Üretilen öneri", {
          deger: uretilen == null ? null : trn(uretilen),
          oran: paydaVar && uretilen != null ? Math.min(1, uretilen / oz.olculen) : null,
          payda: paydaVar ? `hüküm verilebilen skill (${trn(oz.olculen)})` : "",
          meta: uretilen == null ? "üreteç bu turda hiç rapor vermedi — üretim ÖLÇÜLEMEDİ"
            : `<b>${say(ex.kaydedilen)}</b> kaydedildi · <b>${say(ex.otomatik_uygulanan)}</b> otomatik uygulandı${
               paydaVar ? "" : " · payda YOK: hüküm verilebilen skill sayısı 0"}`,
          rozet: uretilen == null ? "ÖLÇÜLEMEDİ" : "" }),
        ozetHucre("Bekleyen öneri", {
          // PAYDASIZ BİLEREK: bekleyen kuyruğun tavanı YOKTUR; uydurma bir tavana göre doluluk
          // çizmek, `hucreCubuk`un paydasız-çubuk yasağının tam olarak yasakladığı şey.
          deger: ex.bekleyen_toplam == null ? null : trn(ex.bekleyen_toplam),
          meta: ex.bekleyen_toplam == null
            ? "bekleyen öneri sayısı yükte YOK — kuyruk derinliği ÖLÇÜLEMEDİ"
            : `senin onayını bekliyor · bu turda <b>${say(ex.kaydedilen)}</b> yeni kayıt`,
          rozet: ex.bekleyen_toplam == null ? "ÖLÇÜLEMEDİ" : "" }),
        ozetHucre("Motor-içi eşiği aşan", {
          // null ≠ boş liste: "aşan yok" ÖLÇÜLMÜŞ bir sıfırdır, "defter okunamadı" bir körlüktür.
          deger: mi == null ? null : trn(mi.length),
          meta: mi == null
            ? "Eksen-2 durum defteri okunamadı — aşan skill sayısı ÖLÇÜLEMEDİ (0 DEĞİL)"
            : (mi.length
               ? `${mi.map(x => `<b>${esc(String(x.skill))}</b>`).join(" · ")} — eşiği aştı, bayrak BİLEREK yazılmadı`
               : "0 motor-içi skill eşiği aştı — ölçüldü, sıfır çıktı"),
          rozet: mi == null ? "ÖLÇÜLEMEDİ" : "" }),
      ], "Eksen-2 üretecinin kanıt tabanı ve çıktısı");
      // MOTOR-İÇİ KARARININ GEREKÇESİ: bayrak yazmamak bir ihmal değil, yazılı bir karardır.
      const miDetay = (mi && mi.length)
        ? `<p class="hint">${mi.map(x => `<b>${esc(String(x.skill))}</b>${
            x.cf_avg_r != null ? ` (cf ${trn(x.n_cf)} örnekte ${trn(x.cf_avg_r, 2)}R${
              x.avg_r != null ? ` · gerçek ${trn(x.n)} işlemde ${trn(x.avg_r, 2)}R` : ""})` : ""}`).join(" · ")
          } kanıt eşiğini AŞTI ama motor-içi: registry'ye <code>shadow</code> yazmak davranışı
          DEĞİŞTİRMEZ (motor bayraktan bağımsız koşar), yazmak ise davranış değişmeden kayıt
          üretirdi. Gerçek aksiyon knob/kapı düzeyindedir.</p>` : "";
      return `<h3 class="t" style="margin-top:16px">Eksen-2 üreteci</h3>
      ${serit}
      ${olculemedi ? "" : `<p class="hint">${esc(oz.neden)}</p>`}
      ${dokum ? `<p class="hint">Skiller hangi kolda elendi: ${dokum}</p>` : ""}
      ${miDetay}`;
    })();
    return `<div class="card rise"><h2 class="t">Öğrenme beslemesi <span class="tx3" style="font-weight:400">(kadansların sağlığı — çıktıları Bölüm 3'te)</span></h2>
      <div class="srow"><span>Kadans</span><b class="${o.son_kosu ? "" : "warn"}">${esc(o.durum || "—")}${
        o.son_kosu ? ` · son seans ${esc(String(o.son_kosu.session || "—"))} · ${esc(String(o.son_kosu.ts || "").replace("T", " ").slice(0, 16))}` : ""}</b></div>
      <div class="srow"><span>Gölge model</span><b>${an2.kuruldu ? `kurulu · n_fit ${an2.n_fit ?? "—"}${
        an2.n_real != null ? ` (gerçek ${an2.n_real} · cf ${an2.n_cf ?? 0})` : ""}${
        an2.brier_train != null ? ` · Brier ${trn(an2.brier_train, 4)}` : ""}` : `kurulmadı — asgari ${an2.min_fit_n ?? "—"} satır ister`}${
        an2.veri_seti_taze === false ? ' · <span class="warn">veri seti DEĞİŞTİ, fit bayat</span>'
        : (an2.veri_seti_taze === true ? ' · <span class="pos">veri seti taze</span>' : ' · <span class="mut">tazelik ölçülmedi</span>')}</b></div>
      ${sonFitRow}
      ${sonDenemeRow}
      <div class="srow"><span>Terfi</span><b>${terfi.promoted ? '<span class="pos">TERFİ ETTİ</span>' : "terfi yok"} · canlı çift ${
        terfi.n_live ?? 0}/${terfi.promote_min_n ?? "—"}${terfi.live_brier != null ? ` · Brier canlı ${trn(terfi.live_brier, 4)} vs taban ${trn(terfi.baseline_brier, 4)}` : ""}</b></div>
      ${kq ? `<div class="srow"><span>Kanıt dolgusu kuyruğu</span><b>${kq.dolgulanabilir_gun ?? 0} gün · ${
        kq.dolgulanabilir_satir ?? 0} satır dolgulanabilir · gece tavanı ${kq.gece_tavani ?? "—"}${
        kq.tahmini_gece != null ? ` → ~${kq.tahmini_gece} gece` : ""}</b></div>
      <div class="srow"><span>Görüşsüz plan (toplam)</span><b>${kq.gorussuz_toplam ?? "—"} / ${kq.n_plan ?? "—"}${
        kq.en_eski ? ` · ${esc(kq.en_eski)} → ${esc(kq.en_yeni)}` : ""}</b></div>
      <p class="hint">${esc(kq.beyan || "")}</p>`
       : `<div class="srow"><span>Kanıt dolgusu kuyruğu</span><b class="mut">ölçülemedi — kuyruk okuması istisna verdi (olay akışında)</b></div>`}
      ${eksen2Blok}
      ${nabizRows ? `<h3 class="t" style="margin-top:16px">Kadans nabzı</h3>${nabizRows}${
        (o.son_fit || {}).beyan ? `<p class="hint">${esc(o.son_fit.beyan)}</p>` : ""}` : ""}
      ${canlilikBloku(d.liveness)}
      ${o.bekci_notu ? `<p class="hint"><b>Bekçi notu:</b> ${esc(o.bekci_notu)}</p>` : ""}</div>`;
  })();

  // SESSİZ HAT BURADA ÇİZİLMEZ (S2R-1): `<main>`in ilk çocuğu ve HER sayfada, sabit üstte
  // duruyor (bkz. sessizHatGlobal). İkinci bir çizim, iki farklı anın ölçümünü aynı anda
  // gösterirdi. Alarm bütçesinin TAM kırılımı Gözetim'in işi olmayı sürdürür.
  return { alarm: alarmButce(d.alarm_butcesi),
           s1, sIcra, sBand, sGeceG, s2, s3, sOzDeg, sEdge, sSonuc, sDogrulama, sHermes, sNous, sY3,
           sSelale, sTrend, sGolgeVaryant, sCark, sIntra, s4, s5, s6, sSag, sOgr };
}

// ---- GÖZETİM & ALARMLAR (eski `operasyon` adı, yeni ve DAR kapsam) ---------------------------
// ADR: "alarm gelen kutusu (runbook bağlı), bekçi ayrıntıları, alarm-bütçesi detayı, olay
// günlüğü." Gelen kutusu ve olay akışı S2R-2'de Portföy'ün (eski Bugün) içinden BURAYA taşındı:
// alarmın iki evi vardı ve ikisi de yarımdı — biri "kaç tane", diğeri "hangileri".
RENDER.operasyon = async () => {
  const p = await opParcalar();
  $("page-operasyon").innerHTML = `
    ${bolumBasHTML("operasyon", "Alarmlar · bekçiler · olay günlüğü",
      "Her alarm satırının <b>teşhis ↗</b> düğmesi bir <b>olay yüzeyi</b> açar: ne oldu, değerler "
      + "şimdi ne, runbook adımları ve mevcut eylemler tek çekmecede (runbook panoya emildi). "
      + "Sessiz hat sayfanın üstünde her an canlıdır; müdahale kolları ⑤ Kilitler'de (ve ⌘K'da).")}
    ${p.alarm}
    ${firsatEsikPaneli(_DIAG)}
    <div class="card rise"><h2 class="t">Alarm gelen kutusu</h2>
      <div id="bp-alerts"><div class="empty">yükleniyor…</div></div></div>
    ${firsatAlarmTaksonomi(((_DIAG || {}).watchdog || {}).alarm_gunluk)}
    ${p.sOgr}
    <div class="card rise"><h2 class="t">Olay akışı · son 8</h2>
      <div id="bp-events"><div class="empty">yükleniyor…</div></div></div>`;
  // İKİSİ DE ARKADAN GELİR: alarm ucu ve olay halkası ayrı uçlar; birine zincirlemek diğerinin
  // gecikmesini sayfanın tamamına yayardı. Düşerse kutu NE OLDUĞUNU yazar (YASA 4).
  j("/api/alerts").then(a => {
    const el = $("bp-alerts"); if (el) el.innerHTML = alertsInbox(a);
  }).catch(() => { const el = $("bp-alerts"); if (el) el.innerHTML = '<div class="empty">gelen kutusu okunamadı</div>'; });
  j("/api/events").then(ev => {
    const el = $("bp-events"); if (el) el.innerHTML = eventsFeed((ev.events || []).slice(0, 8));
  }).catch(() => { const el = $("bp-events"); if (el) el.innerHTML = '<div class="empty">olay kaydı okunamadı</div>'; });
};

// ==============================================================================================
// ③ SAĞLIK · GECE HATTININ CANLI ZAMAN ÇİZELGESİ — `workflow.html`in HALEFİ (D2-b · C1#4)
// ----------------------------------------------------------------------------------------------
// EMEKLİ EDİLEN ŞEY: `workflow.html` (306 satır) statik bir boru-hattı RESMİydi — panodan sıfır iç
// bağ alıyordu (baseline §3.3), kendi jeton dünyasını taşıyordu ve gösterdiği her sayı elle
// yazılmıştı ("250 sembollük evren", "min_exposure_score 40→20"). Bir resim bayatladığında bunu
// kimseye söylemez; bir enstrüman söyler. Resmin cevapladığı soru ("gece hattı neden geçiyor?")
// burada GERÇEK veriyle cevaplanır.
//
// ADIMLAR RESİMDEN EMİLDİ, SAYILARI EMİLMEDİ. Taşınan şey hattın YAPISIdır (hangi adım, ne yapar,
// hangi mekanizma nabız atar); resimdeki nicel iddialar bilerek DIŞARIDA bırakıldı — onların canlı
// karşılığı zaten kendi bölümlerinde yaşıyor ve buraya kopyalamak yeni bir bayatlama yüzeyi açardı.
//
// CANLI OLAN NE, ÖLÇÜLEMEYEN NE (dürüstlük sınırı, D3-UI'a devredilen kalem):
//   * Bekçi raporu YALNIZ GECİKENLERİ adlandırır (`stale`/`never`/`askida`); penceresinde olanlar
//     yalnız bir SAYIdır (`ok`/`total`). Yani "bu adım saat 03:12'de koştu" bilgisi bu uçtan
//     GELMİYOR — adım başına damga `state/mechanism_beats.json`da var ama panoya açılmamış.
//   * Bu yüzden çizelge her adım için ya ÖLÇÜLMÜŞ gecikmeyi yazar, ya da "penceresinde" der,
//     ya da "kendi damgası yok" der. Uydurma saat YOK. Damgaların uca açılması D3-UI'ın işi.
// BEKÇİNİN HER MEKANİZMASI BU TABLODA (sayı `watchdog.EXPECTED`ten okunur, buraya YAZILMAZ): bir mekanizmayı çizelgeye koymamak, geciktiğinde
// operatörün onu hattın neresinde arayacağını bilememesi demekti.
const HAT_ADIMLARI = [
  // [adım adı, ne yapar, nabzı atan mekanizma(lar) — watchdog.EXPECTED adları]
  ["Zamanlayıcı poll", "Uyanır, bekçiyi damgalar, kapanmış seans arar; iki poll arasına birden çok seans sığarsa hepsini sırayla işler.", ["scheduler_poll"]],
  ["Veri kalitesi kapısı", "Bozuk barlı sembol karantinaya alınır; endeks kapanışı bağımsız kaynakla çapraz doğrulanır. Kötü veri asla işlem üretmez.", ["crosscheck"]],
  ["P1 · Rejim + bütçe", "Endeksten rejim ve maruziyet bütçesi. Kendi bekçi damgası YOK — döngünün içinde koşar.", []],
  ["P2 · Tarama", "Evren taranır; her sembolde dört ekran birden değerlendirilir. Gölge-gevşek tarama eşik-altını deftere yazar.", []],
  ["P3 · Plan + kapı", "Aday → plan → deterministik kapı (R:R, sektör, ısı, korelasyon, kazanç karartması, ayna-meşgul). Kapı yasadır.", []],
  ["Düşünen beyin", "İkinci görüş ve keşif slot sıralaması. Yalnız önerir/sıralar — kapıya dokunamaz.", ["hermes_poll", "warmup_sprint"]],
  ["Silahlanma değerlendirmesi", "Silahlanma eşiği haftalık ölçülür; eşik karşılanırsa ARMING_READY ile operatör kararı istenir.", ["arming_eval"]],
  ["Kâğıt ayna + mutabakat", "Silahlanan her plan brackete çevrilip aynaya gider; her döngü hayalet/sapma/ret denetimi koşar.", ["mirror_reconcile"]],
  ["P4 · Dolum + taşıma", "Ertesi açılışta tetik görülürse dolum; bar yayınlanmamışsa plan olaylı bir seans taşınır. Kendi damgası YOK.", []],
  ["P5 · Kalibrasyonlar", "Gölge model, skor IC, çıkış verimliliği, LLM görüş kalibrasyonu, cf sadakati, near-miss karnesi.", ["p5_calibrations"]],
  ["Karşı-olgusal defter", "Günün planları + uyuyan ateşlemeler + eşik-altı + geç-bar satırları ilerletilir; hiçbir karar bu deftere bakmaz.", ["cf_advance"]],
  ["Öğrenme kadansı", "Seans sonrası gölge fit, Eksen-2 turu, kanıt dolgusu ve antrenman sprinti.", ["shadow_fit", "axis2_cycle", "opinion_backfill", "sprint_cadence"]],
  ["Takvim ve dış veri", "Kazanç takvimi tazelemesi ve Y4 toplama (insider delta + short interest).", ["earnings_refresh", "y4_collect"]],
  ["Kanıt raporları", "Haftalık doğrulama raporu, Massive tutarlılık ölçümü ve MEASURED_V3 kayma bekçisi.", ["validation_report", "massive_verify", "shadowlaw_drift"]],
];
// TEK ÇIKIŞ: adım satırı YALNIZ burada üretilir. Renk YOK — geciken bir adım rozetini metinle
// taşır (renk yalnız anomalide kuralı burada da geçerli; gecikme bir ŞİDDET seviyesi değil,
// bekçinin ölçtüğü bir SÜREdir ve alarm sınıfı ayrı bir yüzeyde yaşıyor).
function _hatSatiri(ad, ne, mekler, wd) {
  const stale = wd.stale || [], never = wd.never || [], askida = wd.askida || [];
  const bul = (liste, m) => liste.find(x => (x.name || x) === m);
  const notlar = mekler.map(m => {
    const s = bul(stale, m);
    if (s) return `<b>${esc(m)}</b> · ${trn(s.gap_h, 1)}sa sessiz (pencere ${trn(s.expected_h, 1)}sa)`;
    if (never.includes(m)) return `<b>${esc(m)}</b> · kurulumdan beri hiç koşmadı`;
    const a = bul(askida, m);
    if (a) return `<b>${esc(m)}</b> · askıda — ${esc(a.neden || a.detay || "neden bildirilmedi")}`;
    return `<b>${esc(m)}</b> · penceresinde`;
  });
  const durum = mekler.length
    ? notlar.join("<br>")
    : `<span class="mut">bu adımın kendi bekçi damgası YOK — geciktiğini söyleyecek bağımsız
       bir nabız yok, döngünün kendi kaydından okunur</span>`;
  return `<div class="srow" style="align-items:flex-start">
    <span><b>${esc(ad)}</b><p class="hint" style="margin:2px 0 0;max-width:64ch">${esc(ne)}</p></span>
    <span class="hint" style="text-align:right;max-width:38ch">${durum}</span></div>`;
}
RENDER.cizelge = async () => {
  // Teşhis paketi bu sayfada `operasyon` bölümünde ZATEN çekiliyor (çizim SIRAYLA, `alanSayfasi`).
  // Yine de bağımsız okunur: sıraya bağlı bir okuma, sıra değiştiği gün sessizce boşalırdı.
  let d = _DIAG;
  if (!d) { try { d = await j("/api/diagnostics"); _DIAG = d; } catch (e) { d = null; } }
  const wd = (d || {}).watchdog || {}, sch = (d || {}).scheduler || {};
  const gecikenN = (wd.stale || []).length + (wd.never || []).length;
  const bas = bolumBasHTML("cizelge", "Gece hattı · canlı zaman çizelgesi",
    "Boru hattının statik resmi (<code>/workflow</code>) EMEKLİ: adımlar buraya taşındı ve "
    + "bekçinin ölçtüğü gecikmeyle birlikte okunuyor. Bir adımın <b>ne zaman</b> koştuğu "
    + "(mekanizma başına nabız damgası) D3-UI'da uca açıldı ve <b>aşağıdaki kartta</b> gerçek "
    + "saatiyle yazıyor; damgası olmayan adım için saat hâlâ ÜRETİLMEZ.");
  if (!d) {
    return void ($("page-cizelge").innerHTML = bas + `<div class="card rise">
      <h2 class="t">Hattın adımları</h2>
      <p class="mut">Teşhis ucu okunamadı — adımların gecikmesi <b>ölçülemedi</b>. Hattın yapısı
        aşağıda yine de duruyor; sayı yerine hiçbir şey yazılmaz.</p>
      ${HAT_ADIMLARI.map(([ad, ne]) => _hatSatiri(ad, ne, [], {})).join("")}</div>`
      // DAMGA KARTI KOPUK DALDA DA ÇİZİLİR: uç düştüyse kart YOK OLMAZ, "ölçülemedi + neden"
      // der. Kartın yokluğu bir bilgi taşımaz — operatör onu "bu tur damga yoktu" mu yoksa
      // "bu kart hiç yazılmamış" mı diye okuyacağını bilemezdi.
      + firsatCizelgeIzi(null));
  }
  $("page-cizelge").innerHTML = bas + `<div class="card rise">
    <h2 class="t">Hattın adımları <span class="tx3" style="font-weight:400">(${
      HAT_ADIMLARI.length} adım · ${wd.total ?? "—"} bekçi mekanizması)</span></h2>
    <p class="hint" style="margin-top:0">Bekçi ${wd.ok == null ? "<b>ölçülemedi</b>" : `<b>${wd.ok}/${
      wd.total ?? "—"}</b> mekanizmayı penceresinde`} buldu${gecikenN ? ` · <b>${gecikenN}</b> geciken` : ""}${
      sch.updated ? ` · zamanlayıcı son tur <b>${esc(String(sch.updated).slice(11, 19))}</b>` : ""}.
      Penceresinde olanlar bekçi raporunda ADLA gelmez (yalnız sayıyla) — "penceresinde" ibaresi
      bu yüzden bir çıkarımdır ve satırında böyle yazar.</p>
    ${HAT_ADIMLARI.map(([ad, ne, m]) => _hatSatiri(ad, ne, m, wd)).join("")}
    <p class="hint" style="margin-top:12px">Geciken bir adımın teşhisi bir tık ötede:
      <b>${esc(OLAY_YUZEYLERI.besleme.ad)}</b> olay yüzeyi.</p>
    <div style="margin-top:10px"><button class="dlbtn" type="button" data-act="olayAc"
      data-a1="besleme">Besleme olay yüzeyini aç →</button></div></div>`
    // D3-UI · C1-4: yukarıdaki tablo hattın YAPISIdır (hangi adım, ne yapar, geciken var mı);
    // aşağıdaki kart ZAMANdır (hangi adım saat kaçta koştu, ne kadar sürdü). Yukarıdaki başlığın
    // "damgalar henüz uca açılmadı" cümlesi ARTIK GEÇERSİZ — bu turda açıldı ve altyazı da
    // buna göre yeniden yazıldı.
    + firsatCizelgeIzi((d || {}).cizelge);
};

// ==============================================================================================
// D3-UI · FIRSAT YÜZEYLERİ (C1'in on işi) — "ÜRETİLİYOR AMA GÖRÜNMÜYOR" KOVASININ KAPANIŞI
// ----------------------------------------------------------------------------------------------
// ÖLÇÜLEN KUSUR SINIFI (docs/PATTERN-ETUDU-2026-08-06.md §C1, 22 FIRSAT satırının onu): sistemin
// ÜRETTİĞİ bilgi diskte duruyor, panoda karşılığı YOK. Üç örnek, üçü de bu turda ölçüldü:
//   * `near_miss.json` 4.988 çözülmüş satır — hiçbir uç tüketicisi yoktu, app.js'te adı geçmiyordu
//   * `app.js` içinde "rollback" kelimesi SIFIR kez geçiyordu (PRODUCT.md'nin AÇIK vaadi)
//   * `/api/spend` ucunun web tarafında SIFIR çağıranı vardı
//
// BU BLOK YENİ BİR DİL AÇMAZ. Her kart `.pm-*` hücre dilini (v192) ve kart sözleşmesini (v198)
// kullanır: `katKart(anahtar)` + `kartOzeti({deger, oran, payda, meta, rozet})`. Yeni sınıf,
// yeni renk, yeni bileşen YOK — on iş var olan sözleşmenin üstüne oturur.
//
// HER KART TEK `class="card"` EMİSYONU: ölçülemedi dalı kartın İÇİNDE yaşar, ayrı bir kart
// doğurmaz. Gerekçe iki katlı: (a) kart bütçesi statik emisyon sayar (`say_kart.py`) ve iki
// dallı bir kart bütçeyi iki kez yer; (b) "veri yok" ekranda bir KART olarak durmalı — kartın
// yokluğu bir bilgi taşımaz, kartın içindeki gerekçe taşır.
//
// YENİ EYLEM YÜZEYİ AÇILMADI (tek emir-yolu yasası): on kartın hiçbirinde POST yok. Tek etkileşim
// denetim izinin SEMBOL FİLTRESİdir ve o bir OKUMA sorgusudur (`/api/audit_trail`, GET).
// ----------------------------------------------------------------------------------------------
// ÖLÇÜLEMEDİ DALININ TEK BİÇİMİ. Uydurma yasağının bu bloktaki uygulaması: uç bir alanı hiç
// vermediyse kart "0" ya da boş bir tablo çizmez — NEDENİ yazar. Gerekçe ≥20 karakter olmak
// zorunda çünkü `kartOzeti`nin 3b kapısı bunu ölçüyor (YASA 4 ile aynı ölçü) ve kısa bir gerekçe
// özeti düşürüp kartı katlanamaz yapar — yani kusur SESSİZ kalmaz, sözleşme onu görünür kılar.
function firsatBos(neden, ipucu) {
  return `<p class="mut" style="margin-top:2px"><b>ÖLÇÜLEMEDİ</b> — ${esc(neden)}</p>`
    + (ipucu ? `<p class="hint" style="margin-top:6px">${ipucu}</p>` : "");
}
// KÜNYE ÇİPİ — bir defterin kanıt SINIFI. `_kaynak.source` "yalnız-simüle" ise o defterin sayıları
// GERÇEK kanıt değildir ve öyle okunursa R8'e düşer (etüdün C1-1 dürüstlük şartı). Çip metinle
// konuşur, renkle değil: kanıt sınıfı bir ŞİDDET seviyesi değildir (D1'in beş rolü).
function firsatKunye(k) {
  if (!k) return `<span class="tag t-vi">KÜNYE YOK</span>`;
  const real = k.n_real, cf = k.n_cf;
  return `<span class="tag t-vi" title="${esc("üretildi: " + (k.generated == null ? "ölçülemedi" : k.generated))}">${
    esc(String(k.source == null ? "kaynak beyansız" : k.source).toUpperCase())} · gerçek ${
    real == null ? "—" : trn(real)} / simüle ${cf == null ? "—" : trn(cf)}</span>`;
}

// ---- C1-1 · REDDEDİLEN KARARLARIN KARNESİ (② karar#kapilar) ----------------------------------
// OPERATÖRÜN SORUSU: "Bu eşik doğru mu? Reddettiklerim ne yapardı?" Bir kapı ancak REDDETTİKLERİYLE
// yargılanabilir; kabul edilenlerin karnesi (parsel matrisi) zaten vardı, reddedilenlerinki
// HİÇBİR yerde yoktu. Defter: `near_miss.json` → kova (`blocked_by`) × rejim.
// KÜNYE ZORUNLU VE ÜSTTE: defter `yalnız-simüle` (n_real: 0). Sayıları künyesiz göstermek,
// karşı-olgusal bir tahmini gerçekleşmiş kâr gibi okutmak olurdu.
function firsatRetKarnesi(ml) {
  const nm = (ml || {}).near_miss;
  const kovalar = (nm && nm.var) ? (nm.kovalar || []) : [];
  const en = kovalar.length ? kovalar[0] : null;
  // ÖZETİN DEĞERİ: en çok reddeden kovanın kaç kararı tuttuğu. Çubuğun paydası BEYANLI ve o
  // paydanın kendisi bir kanıt ölçeğidir (log, `kanitOrani`) — bir eşik değil.
  const ozet = !en
    ? kartOzeti({ deger: null, rozet: "ÖLÇÜLEMEDİ",
        meta: (nm && nm.neden) ? esc(nm.neden)
          : "near_miss defteri panoya ulaşmadı — kapının reddettiklerinin karnesi ölçülemedi." })
    : kartOzeti({ deger: trn(nm.resolved_total), oran: kanitOrani(en.n), payda: "en büyük kovanın reddi",
        degerSinif: (en.avg_r != null && en.avg_r > 0) ? "warn" : "",
        meta: `${kovalar.length} kova · en büyüğü <b>${esc(en.blocked_by)}</b> (${trn(en.n)} ret · ort. ${
          en.avg_r == null ? "—" : isr(en.avg_r, trn(en.avg_r, 3)) + "R"})`,
        rozet: (en.avg_r != null && en.avg_r > 0) ? "KAPI PARA BIRAKIYOR" : "" });
  const satir = k => {
    const rej = (k.rejim || []).slice(0, 4).map(r =>
      `<span class="tag t-vi" title="${esc(REGIME_TR[r.rejim] || r.rejim)}">${esc(REGIME_TR[r.rejim] || r.rejim)} ${
        trn(r.n_r)}${r.avg_r == null ? "" : " · " + isr(r.avg_r, trn(r.avg_r, 2)) + "R"}</span>`).join(" ");
    return `<div class="trow" style="grid-template-columns:120px 68px 68px 80px 1fr">
      <span class="chain">${esc(k.blocked_by)}</span>
      <span class="mono-num">${trn(k.n)}</span>
      <span class="mono-num mut">${trn(k.entered)}</span>
      <span class="mono-num ${cls(k.avg_r)}">${k.avg_r == null ? "—" : isr(k.avg_r, trn(k.avg_r, 3)) + "R"}</span>
      <span>${rej}</span></div>`;
  };
  return `<div class="card rise"${katKart("kapilar:retkarne")}>
    <h2 class="t">Reddedilen kararların karnesi <span class="tx3" style="font-weight:400">(kapı masada para bırakıyor mu?)</span></h2>
    ${ozet}
    ${!kovalar.length ? firsatBos((nm && nm.neden) ? nm.neden
        : "near_miss defteri bu turda okunamadı — kapının reddettikleri ölçülemedi ('ret yok' DEĞİL).",
        "Defter P5 kalibrasyonunda üretilir; hat o adıma gelmediyse karne de doğmaz.")
      : `<p class="hint" style="margin-top:0">${firsatKunye(nm.kaynak)} — <b>${trn(nm.resolved_total)}</b> çözülmüş
           karşı-olgusal satır. Bu tablo <b>ne olurdu</b>yu ölçer, <b>ne oldu</b>yu değil: hiçbir satırı
           gerçekleşmiş kâr/zarar olarak okuma.</p>
         <div class="tbl" style="margin-top:10px">
           <div class="trow head" style="grid-template-columns:120px 68px 68px 80px 1fr">
             <span>KAPI (blocked_by)</span><span>RET</span><span>GİRERDİ</span><span>ORT. R</span><span>REJİM KIRILIMI</span></div>
           ${kovalar.map(satir).join("")}</div>
         <p class="hint" style="margin-top:10px">Pozitif bir <b>ORT. R</b>, o kapının sistematik olarak
           kazanan kurulum elediğini söyler — eşiği değiştirmeden ÖNCE ön-kayıt kartı gerekir
           (ölçüm ≠ hüküm).</p>`}</div>`;
}

// ---- C1-8 · "BUGÜN NEDEN HİÇBİR ŞEY OLMADI" (② karar#kapilar) --------------------------------
// Pano bugüne kadar DÜRÜSTTÜ ("bu seansta tarama adayı yok") ama NEDENSİZDİ; oysa nedeni taşıyan
// alanların hepsi elde: rejim maruziyet bütçesi, karartma radarı, kapsama için ertelenen seans,
// halt bayrakları, kapı gerekçeleri. Bu kart onları TEK CÜMLEYE indirir ve kanıtını yanına koyar.
// NEDEN "BİRİNCİL" DİYE ADLANDIRILIYOR: sebeplerin birden çoğu aynı anda doğru olabilir; ilk
// yazan ZORLAYICI olandır (halt bir tercih değil, durdurmadır) ve sırayı uç belirler, pano değil.
function firsatEylemsizlik(rk) {
  const e = (rk || {}).eylemsizlik;
  const bir = (e && e.var) ? e.birincil : null;
  const vc = (e && e.verdict_counts) ? e.verdict_counts : {};
  const toplamPlan = Object.values(vc).reduce((a, b) => a + Number(b), 0);
  const ozet = !e
    ? kartOzeti({ deger: null, rozet: "ÖLÇÜLEMEDİ",
        meta: "teşhis ucu eylemsizlik bloğunu vermedi — nedenin kendisi ölçülemedi, 'neden yok' DEĞİL." })
    : kartOzeti(bir
        ? { deger: bir.ad, degerSinif: "", meta: `${esc(bir.kanit)} · son seansta ${trn(toplamPlan)} plan yargılandı`,
            rozet: e.halted ? "HALT" : "" }
        : { deger: "NEDEN BULUNAMADI", meta: `${trn(toplamPlan)} plan yargılandı · ölçülen dört zorlayıcı nedenin hiçbiri yok`,
            rozet: "KAPI KARARLARINA BAK" });
  const nedenSatir = n => `<div class="srow" style="align-items:flex-start">
    <span><b>${esc(n.ad)}</b><p class="hint" style="margin:2px 0 0;max-width:56ch">${esc(n.aciklama)}</p></span>
    <span class="hint mono-num" style="text-align:right;max-width:34ch">${esc(n.kanit)}</span></div>`;
  const kapiSatir = Object.entries((e && e.gate_reasons) ? e.gate_reasons : {})
    .sort((a, b) => b[1] - a[1]).slice(0, 6)
    .map(([ad, n]) => `<div class="trow" style="grid-template-columns:1fr 60px">
      <span class="chain">${esc(ad)}</span><span class="mono-num">${trn(n)}</span></div>`).join("");
  return `<div class="card rise"${katKart("kapilar:eylemsizlik")}>
    <h2 class="t">Bugün neden hiçbir şey olmadı? <span class="tx3" style="font-weight:400">(bozuk mu, tasarım mı?)</span></h2>
    ${ozet}
    ${!e ? firsatBos("teşhis ucu `risk.eylemsizlik` bloğunu vermedi — eylemsizliğin nedeni bu turda ölçülemedi.",
        "Alanlar (bütçe, karartma, erteleme, halt) tek uçtan gelir; uç düştüyse hiçbiri türetilemez.")
      : `<div class="srow"><span>Rejim maruziyet bütçesi</span>
           <b class="mono-num">${e.exposure_budget_pct == null ? "ölçülemedi" : pctf(Number(e.exposure_budget_pct) / 100, 0)}</b></div>
         ${(e.nedenler || []).map(nedenSatir).join("")}
         ${e.neden_yok_aciklama ? `<p class="hint">${esc(e.neden_yok_aciklama)}</p>` : ""}
         <div class="srow"><span>Son seansın kapı hükmü</span><b class="mono-num">${
           Object.entries(vc).map(([k, v]) => `${esc(k)} ${trn(v)}`).join(" · ") || "plan yok"}</b></div>
         ${kapiSatir ? `<div class="tbl" style="margin-top:10px">
             <div class="trow head" style="grid-template-columns:1fr 60px"><span>KAPI GEREKÇESİ</span><span>PLAN</span></div>
             ${kapiSatir}</div>` : ""}
         <p class="hint" style="margin-top:10px">Olay sayaçları son <b>${trn(e.olay_penceresi)}</b> olayda ölçüldü:
           ${Object.entries(e.olay_sayaci || {}).map(([k, v]) => `${esc(k)} <b>${trn(v)}</b>`).join(" · ") || "sayaç yok"}.
           Pencerede görülmemek "hiç olmadı" DEĞİLDİR.</p>`}</div>`;
}

// ---- C1-2 · EMİR YAŞAM-DÖNGÜSÜ İZİ (② karar#mutabakat) ---------------------------------------
// UX denetiminin B1 bulgusu: onaydan sonraki son bacak HİÇBİR kalıcı geri bildirim taşımıyordu —
// yalnız geçici bir çekmece mesajı. Panoya ulaşan tek şey TOPLAM huniydi ("silahlı → gönderilmiş
// → dolan", üç paydası ayrı olduğu beyanlı). `mirror_orders.json` coid başına status/filled_qty/
// **filled_avg_price** taşıyor ve panoya HİÇ ulaşmıyordu.
// SLİPAJ TÜRETİLİR AMA UYDURULMAZ: planın `entry_trigger`ı ile dolum fiyatı ikisi de varsa bps
// hesaplanır; biri yoksa hücre boş kalır — 0 bps "slipaj yoktu" demek olurdu.
function firsatEmirYasam(rc) {
  const ey = (rc || {}).emir_yasam;
  const sat = (ey && ey.var) ? (ey.satirlar || []) : [];
  const dolan = sat.filter(o => String(o.status).toLowerCase() === "filled").length;
  const slipajli = sat.filter(o => o.slipaj_bps != null);
  const ortSlipaj = slipajli.length
    ? slipajli.reduce((a, o) => a + Number(o.slipaj_bps), 0) / slipajli.length : null;
  const ozet = !ey
    ? kartOzeti({ deger: null, rozet: "ÖLÇÜLEMEDİ",
        meta: "ayna emir defteri panoya ulaşmadı — onayın hangi emre döndüğü ölçülemedi." })
    : (!ey.n
      ? kartOzeti({ deger: 0, meta: `${esc(String(ey.bos_neden == null ? "ayna defteri okundu, içinde emir yok" : ey.bos_neden))}` })
      : kartOzeti({ deger: trn(ey.n), oran: kanitOrani(ey.n), payda: "ayna defterindeki emir",
          meta: `${trn(dolan)} dolan · ${Object.entries(ey.durum_dagilim || {}).map(([k, v]) => `${esc(k)} ${trn(v)}`).join(" · ")}`,
          rozet: slipajli.length ? "" : "SLİPAJ ÖLÇÜLEMEDİ" }));
  const satir = o => `<div class="trow" style="grid-template-columns:64px 52px 92px 74px 84px 78px 1fr">
    <span class="tick">${esc(String(o.symbol == null ? "?" : o.symbol))}</span>
    <span class="chain mut">${esc(String(o.side == null ? "—" : o.side))}</span>
    ${_chip(String(o.status).toUpperCase(), String(o.status).toLowerCase() === "filled" ? "t-go" : "t-vi")}
    <span class="mono-num">${o.filled_qty == null ? "—" : trn(o.filled_qty)}</span>
    <span class="mono-num">${o.filled_avg_price == null ? "—" : money(o.filled_avg_price)}</span>
    <span class="mono-num mut">${o.plan_entry_trigger == null ? "—" : money(o.plan_entry_trigger)}</span>
    <span class="mono-num ${cls(o.slipaj_bps == null ? null : -Number(o.slipaj_bps))}">${
      o.slipaj_bps == null ? '<span class="mut">slipaj ölçülemedi</span>' : trn(o.slipaj_bps, 1) + " bps"}${
      o.plan_var ? "" : ' <span class="tag t-vi">PLANSIZ</span>'}</span></div>`;
  return `<div class="card rise"${katKart("mutabakat:emiryasam")}>
    <h2 class="t">Emir yaşam-döngüsü <span class="tx3" style="font-weight:400">(onayım aynaya ulaştı mı, kaça doldu?)</span></h2>
    ${ozet}
    ${!ey ? firsatBos("teşhis ucu `reconcile.emir_yasam` bloğunu vermedi — emrin son bacağı ölçülemedi.",
        "Bugüne kadar panoya yalnız TOPLAM huni ulaşıyordu; emir-başına iz bu blokla açıldı.")
      : (!ey.n ? firsatBos(String(ey.bos_neden == null ? "ayna defterinde emir yok" : ey.bos_neden),
          "Bu bir ÖLÇÜMdür: defter okundu ve boş çıktı — okunamamış olmakla aynı şey değil.")
        : `<div class="tbl" style="margin-top:10px">
             <div class="trow head" style="grid-template-columns:64px 52px 92px 74px 84px 78px 1fr">
               <span>HİSSE</span><span>YÖN</span><span>DURUM</span><span>DOLAN</span><span>DOLUM $</span><span>PLAN $</span><span>SLİPAJ</span></div>
             ${sat.map(satir).join("")}</div>
           <p class="hint" style="margin-top:10px">Defterde <b>${trn(ey.n)}</b> emir var, <b>${trn(ey.gosterilen)}</b>
             gösteriliyor (tavan beyanlı). Slipaj = (dolum − plan tetiği)/plan tetiği; ölçülen ortalama
             <b>${ortSlipaj == null ? "—" : trn(ortSlipaj, 1) + " bps"}</b>, paydası <b>${trn(slipajli.length)}</b>
             emir. Son ayna olayı: <b>${esc(String(ey.last_event_ts == null ? "ölçülemedi" : ey.last_event_ts))}</b>.</p>`)}</div>`;
}

// ---- C1-9 · ÇIKIŞ NEDENİ KIRILIMI (② karar#performans) ---------------------------------------
// Panoda bugüne kadar YALNIZ İKİ SAYI vardı (`avg_left_r` + en kötü neden). Defter (`exit_efficiency
// .reasons`) çıkış mekanizması başına n / MFE / gerçekleşen R / MASADA BIRAKILAN R taşıyor ve
// kategorinin standardı (FT `/stats`) tam olarak bu tablodur — Meridian'ın verisi daha zengin.
// "MASADA BIRAKILAN" BİR KAYIP DEĞİL BİR FARKTIR: MFE ile gerçekleşen arasındaki mesafe. Renk
// yalnız en kötü satırda doğar (anomali), her satırda değil.
function firsatCikisNedeni(ml) {
  const ee = (ml || {}).exit_efficiency;
  const reasons = (ee && ee.reasons) ? ee.reasons : null;
  const satirlar = reasons ? Object.entries(reasons)
    .map(([ad, v]) => ({ ad, ...v })).sort((a, b) => Number(b.left_r) - Number(a.left_r)) : [];
  const enKotu = satirlar.length ? satirlar[0] : null;
  const ozet = !satirlar.length
    ? kartOzeti({ deger: null, rozet: "ÖLÇÜLEMEDİ",
        meta: "çıkış verimliliği defteri panoya ulaşmadı — hangi mekanizmanın para bıraktığı ölçülemedi." })
    : kartOzeti({ deger: trn(ee.avg_left_r, 3) + "R", degerSinif: "warn",
        oran: kanitOrani(ee.n), payda: "çıkış kaydı (gerçek + simüle)",
        meta: `${trn(satirlar.length)} mekanizma · en kötü <b>${esc(enKotu.ad)}</b> ${
          trn(enKotu.left_r, 3)}R (n=${trn(enKotu.n)})`,
        rozet: azOrnek(enKotu.n) ? "AZ VERİ" : "" });
  const satir = (r, i) => `<div class="trow" style="grid-template-columns:118px 60px 60px 80px 84px 80px">
    <span class="chain">${esc(EXIT_TR[r.ad] == null ? r.ad : EXIT_TR[r.ad])}</span>
    <span class="mono-num">${trn(r.n)}</span>
    <span class="mono-num mut">${trn(r.n_cf)}</span>
    <span class="mono-num">${r.avg_mfe_r == null ? "—" : trn(r.avg_mfe_r, 3) + "R"}</span>
    <span class="mono-num ${cls(r.avg_realized_r)}">${r.avg_realized_r == null ? "—" : isr(r.avg_realized_r, trn(r.avg_realized_r, 3)) + "R"}</span>
    <span class="mono-num${i === 0 ? " warn" : ""}">${r.left_r == null ? "—" : trn(r.left_r, 3) + "R"}</span></div>`;
  return `<div class="card rise"${katKart("performans:cikis")}>
    <h2 class="t">Çıkış nedeni kırılımı <span class="tx3" style="font-weight:400">(hangi mekanizma masada para bırakıyor?)</span></h2>
    ${ozet}
    ${!satirlar.length ? firsatBos("`exit_efficiency.reasons` bu turda okunamadı — çıkış mekanizmalarının karnesi ölçülemedi.",
        "Defter P5 kalibrasyonunda üretilir; panoda bugüne dek yalnız iki özet sayı görünüyordu.")
      : `<p class="hint" style="margin-top:0">${firsatKunye(ee._kaynak)} · toplam <b>${trn(ee.n)}</b> çıkış kaydı.
           <b>MASADA</b> = ortalama MFE − gerçekleşen R; bir kayıp değil, çıkış kuralının ödediği FARK.</p>
         <div class="tbl" style="margin-top:10px">
           <div class="trow head" style="grid-template-columns:118px 60px 60px 80px 84px 80px">
             <span>ÇIKIŞ NEDENİ</span><span>N</span><span>N·SİM</span><span>ORT. MFE</span><span>GERÇEKLEŞEN</span><span>MASADA</span></div>
           ${satirlar.map(satir).join("")}</div>
         <p class="hint" style="margin-top:10px">Sıra <b>masada bırakılan R</b>'ye göre; en üstteki satır
           reformun ilk adresidir. Değişiklik ön-kayıt kartı ister — bu tablo ölçümdür, hüküm değil.</p>`}</div>`;
}

// ---- C1-7 · DENETİM İZİNİN TAMAMI (② karar#adaylar) ------------------------------------------
// Pano bugüne kadar "denetim izi" iddiasında bulunuyor ama defterin ÜÇTE BİRİNİ gösteriyordu
// (`plans_shown: 120` / 390). Tavan BEYANLIYDI, yani dürüsttü — ama iş cevaplanmıyordu:
// "AAPL'de son altı ayda kaç plan kuruldu, kaçı NO_GO oldu, neden?"
// ÇÖZÜM TAVANI KALDIRMAK DEĞİL SORGULANABİLİR KILMAK (etüdün kendi hükmü): sembol ekseni defterin
// TAMAMI üstünde sayılır, satırlar filtreyle gelir ve her iki payda da ekranda yazar.
// FİLTRE BİR EYLEM YÜZEYİ DEĞİLDİR: GET sorgusu, tek emir-yolu yasasına dokunmaz.
function firsatDenetimIzi(at) {
  const D = (at && at.defter) ? at.defter : null;
  const vc = (at && at.verdict_sayim) ? at.verdict_sayim : {};
  const toplam = Object.values(vc).reduce((a, b) => a + Number(b), 0);
  const noGo = vc.NO_GO;
  const ozet = !D
    ? kartOzeti({ deger: null, rozet: "ÖLÇÜLEMEDİ",
        meta: (at && at.neden) ? esc(at.neden)
          : "denetim izi ucu okunamadı — plan defterinin tamamı bu turda sorgulanamadı." })
    : kartOzeti({ deger: trn(D.plans_total), oran: kanitOrani(D.plans_total), payda: "defterdeki plan",
        meta: `${trn(at.sembol_n)} sembol · ${Object.entries(vc).map(([k, v]) => `${esc(k)} ${trn(v)}`).join(" · ")}`,
        rozet: (noGo != null && toplam > 0 && noGo / toplam > 0.5) ? "ÇOĞU NO_GO" : "" });
  // GERÇEK `<button>`, `role="button"` TAŞIYAN BİR DIV DEĞİL. Panonun klavye delegasyonu yalnız
  // `[data-rk][role="button"]` için Enter/Space dinliyor (çekmece satırları); `data-act` taşıyan
  // bir div klavyeyle HİÇ çalışmazdı — yani tıklanabilir görünüp faresiz operatöre kapalı bir
  // yüzey doğardı (bu deponun `ozetHucre`de adıyla yasakladığı sınıf). Satırın içeriği yalnız
  // `<span>`, yani buton içerik modeline uyuyor (aynı desen: plan satırları, `_PHEAD` tablosu).
  const semSatir = s => `<button type="button" class="trow rowbtn"
      style="grid-template-columns:64px 54px 1fr 150px" data-act="denetimAra" data-a1="${esc(s.ticker)}"
      aria-label="${esc(s.ticker)} denetim izini filtrele — ${trn(s.n)} plan">
    <span class="tick">${esc(s.ticker)}</span><span class="mono-num">${trn(s.n)}</span>
    <span class="chain mut">${Object.entries(s.verdicts || {}).map(([k, v]) => `${esc(k)} ${trn(v)}`).join(" · ")}</span>
    <span class="mono-num mut">${esc(String(s.ilk == null ? "—" : s.ilk))} → ${esc(String(s.son == null ? "—" : s.son))}</span></button>`;
  const planSatir = p => `<div class="trow" style="grid-template-columns:82px 58px 118px 48px 82px 1fr">
    <span class="mono-num">${esc(String(p.date == null ? "—" : p.date))}</span>
    <span class="tick">${esc(String(p.ticker == null ? "?" : p.ticker))}</span>
    <span class="chain mut">${esc(String(p.setup == null ? "—" : p.setup))}</span>
    <span class="mono-num">${p.score == null ? "—" : trn(p.score)}</span>
    ${_chip(String(p.verdict == null ? "—" : p.verdict), p.verdict === "GO" ? "t-go" : (p.verdict === "NO_GO" ? "t-no" : "t-vi"))}
    <span class="chain mut">${esc((p.reasons || []).join(" · ").slice(0, 120)) || "gerekçe yazılmamış"}</span></div>`;
  const sorgu = (at && at.sorgu) ? at.sorgu : {};
  return `<div class="card rise"${katKart("adaylar:denetim")}>
    <h2 class="t">Denetim izi · defterin tamamı <span class="tx3" style="font-weight:400">(bu sembolde geçmişte ne karar verdim?)</span></h2>
    ${ozet}
    ${!D ? firsatBos((at && at.neden) ? at.neden
        : "`/api/audit_trail` okunamadı — plan defteri bu turda sorgulanamadı ('plan yok' DEĞİL).",
        "Bu uç defterin TAMAMI üstünde sayar; sinyal listesinin 120'lik tavanı burada geçerli değil.")
      : `<div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin:10px 0">
           <label class="hint" for="denetim-ara">Sembol filtresi</label>
           <input id="denetim-ara" class="searchbox" type="search" placeholder="AAPL" maxlength="10"
             value="${esc(String(sorgu.sembol == null ? "" : sorgu.sembol))}"
             data-act="denetimAra" data-act-on="input" aria-label="Denetim izinde sembol ara">
           <span class="hint">defterde <b>${trn(D.plans_total)}</b> plan · sorgu <b>${trn(D.eslesen)}</b>
             satır eşledi · <b>${trn(D.gosterilen)}</b> gösteriliyor (tavan ${trn(D.limit)})</span></div>
         <div class="tbl">
           <div class="trow head" style="grid-template-columns:82px 58px 118px 48px 82px 1fr">
             <span>TARİH</span><span>HİSSE</span><span>KURULUM</span><span>SKOR</span><span>HÜKÜM</span><span>GEREKÇE</span></div>
           ${(at.satirlar || []).map(planSatir).join("") || `<div class="empty">Bu sorguya uyan plan yok — defter okundu, eşleşme çıkmadı.</div>`}</div>
         ${detayKatmani("Sembol ekseni · defterin TAMAMI üstünde sayım",
             "Tavan burada geçerli değil: sayımlar 390 satırın hepsinden gelir. Satıra tıklamak filtreyi kurar.",
             `<div class="tbl">
                <div class="trow head" style="grid-template-columns:64px 54px 1fr 150px">
                  <span>HİSSE</span><span>PLAN</span><span>HÜKÜM KIRILIMI</span><span>İLK → SON</span></div>
                ${(at.semboller || []).map(semSatir).join("")}</div>
              <p class="hint" style="margin-top:8px">İlk 60 sembol gösteriliyor; defterde <b>${
                trn(at.sembol_n)}</b> ayrı sembol var.</p>`)}`}</div>`;
}
// SORGU EYLEMİ — YALNIZ OKUMA. `data-act` izin listesine kayıtlıdır (`EYLEMLER`) ve tek yaptığı
// GET sorgusunu yenileyip bölümü yeniden çizmektir. POST yok, state'e dokunma yok.
// GECİKTİRME (debounce) ŞART: `data-act-on="input"` her tuş vuruşunda tetikler ve filtresiz bir
// çağrı defterin tamamını okur — her harfte bir istek, ağı da sunucuyu da gereksiz yorar.
let _DENETIM_ZAMAN = null, _DENETIM_SEMBOL = "";
window.denetimAra = (sembol) => {
  const el = document.getElementById("denetim-ara");
  _DENETIM_SEMBOL = String(sembol === undefined ? (el ? el.value : "") : sembol).trim().toUpperCase();
  if (el && sembol !== undefined) el.value = _DENETIM_SEMBOL;
  clearTimeout(_DENETIM_ZAMAN);
  _DENETIM_ZAMAN = setTimeout(() => {
    RENDER.adaylar().then(() => {
      // ODAK KORUNUR: bölüm yeniden çizildiğinde kutu yeni bir DOM düğümüdür ve odak kaybolurdu —
      // yani operatör her harften sonra kutunun dışına düşerdi. İmleç de sona alınır.
      const yeni = document.getElementById("denetim-ara");
      if (yeni) { yeni.focus(); yeni.setSelectionRange(yeni.value.length, yeni.value.length); }
      revealActive(true);
    }).catch(e => console.error("denetim izi yenilenemedi:", e));
  }, 260);
};

// ---- C1-4 · CANLI ZAMAN ÇİZELGESİ · DAMGALAR (③ saglik#cizelge) ------------------------------
// D2-b ÇİZELGE YÜZEYİNİ KURDU VE BİR BORÇ BEYAN ETTİ: "'bu adım saat 03:12'de koştu' bilgisi bu
// uçtan GELMİYOR — adım başına damga `state/mechanism_beats.json`da var ama panoya açılmamış.
// Damgaların uca açılması D3-UI'ın işi." Bu kart o borcu kapatır: damgalar artık uçtan geliyor
// (`diagnostics.cizelge.damgalar`) ve GERÇEK saatle yazılıyor.
// UYDURMA YOK: damgası olmayan mekanizma için saat üretilmez — satır "kendi damgası yok" der.
// Koşu defteri (`pipeline_runs.jsonl`) P-adımlarının GERÇEK süresini taşır ve o da buraya iner.
function firsatCizelgeIzi(cz) {
  const D = (cz && cz.var) ? (cz.damgalar || {}) : null;
  const adlar = D ? Object.keys(D).sort((a, b) => String(D[b]).localeCompare(String(D[a]))) : [];
  const kosular = (cz && cz.var) ? (cz.kosular || []) : [];
  const sd = (cz && cz.son_dongu) ? cz.son_dongu : null;
  const sure = r => {
    if (!r.started || !r.finished) return null;
    const a = Date.parse(r.started), b = Date.parse(r.finished);
    return (Number.isFinite(a) && Number.isFinite(b)) ? Math.max(0, Math.round((b - a) / 1000)) : null;
  };
  const ozet = !cz
    ? kartOzeti({ deger: null, rozet: "ÖLÇÜLEMEDİ",
        meta: "teşhis ucu `cizelge` bloğunu vermedi — adım damgaları bu turda okunamadı." })
    : kartOzeti(adlar.length
        ? { deger: trn(adlar.length), oran: kanitOrani(adlar.length), payda: "damgalı mekanizma",
            meta: `${trn(kosular.length)} koşu kaydı · en taze damga <b>${esc(String(D[adlar[0]]).slice(11, 19))}</b> (${esc(adlar[0])})`,
            rozet: (sd && sd.var === false) ? "DÖNGÜ KAYDI YOK" : "" }
        : { deger: null, rozet: "ÖLÇÜLEMEDİ",
            meta: String(cz.damga_neden_yok == null ? "mekanizma damgaları okunamadı — adım saatleri ölçülemedi." : cz.damga_neden_yok) });
  const damgaSatir = ad => `<div class="trow" style="grid-template-columns:1fr 168px">
    <span class="chain">${esc(ad)}</span>
    <span class="mono-num">${esc(String(D[ad]).replace("T", " ").slice(0, 19))}Z</span></div>`;
  const kosuSatir = r => {
    const s = sure(r);
    return `<div class="trow" style="grid-template-columns:128px 150px 62px 74px 1fr">
      <span class="chain">${esc(String(r.pipeline == null ? "?" : r.pipeline))}</span>
      <span class="mono-num">${esc(String(r.started == null ? "—" : String(r.started).replace("T", " ").slice(0, 19)))}</span>
      <span class="mono-num">${s == null ? '<span class="mut">—</span>' : trn(s) + " sn"}</span>
      ${_chip(String(r.status == null ? "—" : r.status).toUpperCase(), r.status === "ok" ? "t-go" : "t-vi")}
      <span class="chain mut">${trn(r.skills_invoked)} koştu · ${trn(r.skills_declared_not_run)} beyan-edilip-koşmadı · ${
        trn(r.artifacts)} artefakt${r.error ? " · " + esc(String(r.error).slice(0, 60)) : ""}</span></div>`;
  };
  return `<div class="card rise"${katKart("cizelge:damga")}>
    <h2 class="t">Adım damgaları · gerçek saat <span class="tx3" style="font-weight:400">(karar adım adım nasıl oluştu?)</span></h2>
    ${ozet}
    ${!cz ? firsatBos("teşhis ucu `cizelge` bloğunu vermedi — adım saatleri bu turda ölçülemedi.",
        "Yukarıdaki adım listesi (yapı) yine duruyor; eksik olan saat, uydurulmuyor.")
      : `${sd && sd.var ? `<div class="srow"><span>Son günlük döngü</span>
             <b class="mono-num">${esc(String(sd.date))} · ${trn(sd.candidates)} aday → ${trn(sd.plans)} plan → ${
               trn(sd.armed)} silahlı${sd.yas_saat == null ? "" : ` · ${trn(sd.yas_saat, 1)} sa önce`}</b></div>`
           : `<div class="srow"><span>Son günlük döngü</span><b class="mut">${
               esc(String((sd && sd.neden) ? sd.neden : "döngü kaydı ölçülemedi"))}</b></div>`}
         ${adlar.length ? `<div class="tbl" style="margin-top:10px">
             <div class="trow head" style="grid-template-columns:1fr 168px"><span>MEKANİZMA</span><span>SON NABIZ (UTC)</span></div>
             ${adlar.map(damgaSatir).join("")}</div>`
           : firsatBos(String(cz.damga_neden_yok == null ? "mekanizma damgaları okunamadı" : cz.damga_neden_yok))}
         ${detayKatmani("Koşu defteri · adım başına gerçek süre",
             "`pipeline_runs.jsonl` her skill koşusuna başlangıç/bitiş damgası yazar — süre TÜRETİLMEZ, ölçülür.",
             kosular.length ? `<div class="tbl">
                 <div class="trow head" style="grid-template-columns:128px 150px 62px 74px 1fr">
                   <span>BORU HATTI</span><span>BAŞLANGIÇ (UTC)</span><span>SÜRE</span><span>DURUM</span><span>SKİLLER</span></div>
                 ${kosular.map(kosuSatir).join("")}</div>`
               : firsatBos("koşu defteri boş okundu — adım süreleri bu turda ölçülemedi."))}
         <p class="hint" style="margin-top:10px">LLM çağrıları son <b>${trn(cz.olay_penceresi)}</b> olayda
           <b>${trn((cz.cagrilar || []).length)}</b> kez görüldü. Pencerede görülmemek "çağrı yapılmadı" DEĞİLDİR.</p>`}</div>`;
}

// ---- C1-3 · GECE MALİYET VE TOKEN KARNESİ (④ ogrenme#hermes) ---------------------------------
// ÖLÇÜLEN KUSUR: `/api/spend` ucunun web tarafında SIFIR çağıranı vardı; panoya ulaşan tek şey
// aylık toplam ve `over_budget` bayrağıydı. Model kırılımı, kol kırılımı, gece-başına maliyet:
// hiçbiri yoktu. Beyin bütçesi dolduğunda sistem ücretsiz yola düşüyor ve bu geçişin maliyeti
// yalnız ikili bir bayrakla görünüyordu.
// KANONİK UÇ KORUNDU: kırılım `/api/hermes` `spend_detay`den gelir (K1 hükmü — `/api/spend`
// EMEKLİ ve ona yeni tüketici bağlanmaz). Kova değişmedi, İÇİ zenginleşti.
function firsatMaliyetKarnesi(d) {
  const sd = (d || {}).spend_detay, sp = (d || {}).spend;
  const t = (sd && sd.var) ? sd.toplam : null;
  const ozet = !t
    ? kartOzeti({ deger: null, rozet: "ÖLÇÜLEMEDİ",
        meta: (sd && sd.neden) ? esc(sd.neden)
          : "harcama defteri panoya ulaşmadı — gecenin maliyeti ölçülemedi ('bedava' DEĞİL)." })
    : kartOzeti({ deger: money(t.cost_usd), oran: kanitOrani(t.n), payda: "kayıtlı LLM çağrısı",
        meta: `${trn(t.n)} çağrı · ${trn(t.in_tokens)} giriş / ${trn(t.out_tokens)} çıkış token · ${
          trn((sd.modeller || []).length)} model`,
        rozet: (sp && sp.over_budget) ? "BÜTÇE DOLDU" : (sd.olculemeyen_satir ? "EKSİK ALANLI SATIR" : "") });
  const grupSatir = g => `<div class="trow" style="grid-template-columns:1fr 54px 96px 96px 78px">
    <span class="chain">${esc(g.ad)}</span><span class="mono-num">${trn(g.n)}</span>
    <span class="mono-num mut">${trn(g.in_tokens)}</span><span class="mono-num mut">${trn(g.out_tokens)}</span>
    <span class="mono-num">${money(g.cost_usd)}</span></div>`;
  const gunSatir = g => `<div class="trow" style="grid-template-columns:96px 54px 96px 78px">
    <span class="mono-num">${esc(g.gun)}</span><span class="mono-num">${trn(g.n)}</span>
    <span class="mono-num mut">${trn(g.in_tokens + g.out_tokens)}</span>
    <span class="mono-num">${money(g.cost_usd)}</span></div>`;
  return `<div class="card rise"${katKart("hermes:maliyet")}>
    <h2 class="t">Gece maliyet ve token karnesi <span class="tx3" style="font-weight:400">(bu düşünme ne tuttu?)</span></h2>
    ${ozet}
    ${!t ? firsatBos((sd && sd.neden) ? sd.neden
        : "`spend_detay` bloğu uçtan gelmedi — çağrı-başına maliyet bu turda ölçülemedi.",
        "Aylık toplam ve bütçe bayrağı yukarıdaki durum kartında; eksik olan KIRILIM.")
      : `<div class="srow"><span>Bu ay (${esc(sd.ay)})</span>
           <b class="mono-num">${money(sd.bu_ay.cost_usd)} · ${trn(sd.bu_ay.n)} çağrı${
             sp && sp.budget_usd != null ? ` · bütçe ${money(sp.budget_usd)}` : ""}</b></div>
         ${sd.olculemeyen_satir ? `<div class="srow"><span>Maliyet alanı olmayan satır</span>
             <b class="mono-num warn">${trn(sd.olculemeyen_satir)}/${trn(sd.satir_n)}</b></div>` : ""}
         <div class="tbl" style="margin-top:10px">
           <div class="trow head" style="grid-template-columns:1fr 54px 96px 96px 78px">
             <span>MODEL</span><span>ÇAĞRI</span><span>GİRİŞ TOKEN</span><span>ÇIKIŞ TOKEN</span><span>MALİYET</span></div>
           ${(sd.modeller || []).map(grupSatir).join("")}</div>
         <div class="tbl" style="margin-top:10px">
           <div class="trow head" style="grid-template-columns:1fr 54px 96px 96px 78px">
             <span>KOL (note)</span><span>ÇAĞRI</span><span>GİRİŞ TOKEN</span><span>ÇIKIŞ TOKEN</span><span>MALİYET</span></div>
           ${(sd.kollar || []).map(grupSatir).join("")}</div>
         ${detayKatmani("Gece gece · son 14 gün",
             "Defterin gün kırılımı: hangi gece kaç çağrı ve kaç dolar. Satır yoksa o gün hiç çağrı YAZILMAMIŞ demektir.",
             `<div class="tbl">
                <div class="trow head" style="grid-template-columns:96px 54px 96px 78px">
                  <span>GÜN</span><span>ÇAĞRI</span><span>TOPLAM TOKEN</span><span>MALİYET</span></div>
                ${(sd.gunler || []).map(gunSatir).join("")}</div>`)}
         <p class="hint" style="margin-top:10px">Maliyet defteri <b>${trn(sd.satir_n)}</b> satır.
           Ücretsiz yola düşen çağrılar <b>$0,00</b> yazar ve bu bir ÖLÇÜMdür — alanı hiç taşımayan
           satırlar ayrıca <b>${trn(sd.olculemeyen_satir)}</b> olarak sayılır, sıfır sayılmaz.</p>`}</div>`;
}

// ---- HERMES ÇAĞRI TELEMETRİSİ (④ ogrenme#hermes · v219 iş 4) --------------------------------
// ÖLÇÜLEN KUSUR: `hermes.integrations_status()` (hermes.py) `agent_calls` alanını /api/hermes
// gövdesine KOYUYOR ve bunu kendi yorumunda beyan ediyordu — "veri hazır, çizim henüz yok".
// Yani defterin YASA-6 tüketicisi bir API alanıydı, bir OKUYUCU değil: `agent_telemetry.ozet()`
// her istekte hesaplanıp tele gidiyor, panoda hiçbir piksele dönüşmüyordu. Kartın cevapladığı
// soru defterin kendi docstring'inde yazılı: "gece koşusu neden 40 dk sürdü, hangi çağrı takıldı".
//
// BAŞLIK SAYISI SÜRE DEĞİL SINIF: "kaç çağrı KULLANILABİLİR cevap getirdi". Süre bir maliyettir
// ama boş dönen bir çağrı bir ARIZAdır ve p95 onu göstermez (boş cevap hızlı döner). Payda
// pencerede ÖLÇÜLEN çağrıdır; pencere dışında kalan satırlar ayrıca yazılır — boş bir özet,
// "hiç çağrı olmadı" ile "hepsi pencerenin dışında" arasındaki farkı söyleyemezse yanlış güven
// üretir (`ozet()`in kendi beyanı).
// ÖLÇÜLEMEDİ ≠ 0: `arac.ort` null ise oran ÇİZİLMEZ ve nedeni yazılır (`-Q` sessiz mod CLI
// oturum özetini bastırır); ölçülemeyenleri paydaya katmak oranı sessizce seyreltirdi.
function hermesTelemetriKarti(it) {
  const t = (it || {}).agent_calls || null;
  const sinif = (t && t.sinif) || {};
  // `n` UYDURULMAZ: alan yoksa özet ÖLÇÜLEMEDİ dalına düşer. `?? 0` yazmak, gelmemiş bir
  // ölçümü "sıfır çağrı" diye okutmak olurdu — bu turun kapattığı sınıfın ta kendisi.
  const n = (t && Number.isFinite(t.n)) ? t.n : null;
  // `sinif` bir SAYIM sözlüğüdür (`ozet()` anahtarı yalnız gördükçe açar): pencere ÖLÇÜLDÜYSE
  // anahtarın yokluğu "o sınıfta çağrı YOK" demektir ve bu TÜRETİLMİŞ değil ÖLÇÜLMÜŞ bir
  // sıfırdır. Pencere ölçülemediyse sıfır da yoktur — null kalır.
  const dolu = Number.isFinite(sinif.dolu) ? sinif.dolu : (n == null ? null : 0);
  const bosumsu = (n == null || dolu == null) ? null : (n - dolu);   // dolu OLMAYAN her sınıf: boş · yapılandırmasız · bayrak · skill · zaman aşımı
  const pencereSaat = (t && t.pencere_s) ? Math.round(t.pencere_s / 3600) : null;
  const sure = (t && t.sure_ms) || {};
  const arac = (t && t.arac) || {};
  const iz = (t && t.iz) || {};
  // İKİ AYRI BOŞLUK, TEK DAL: özet blok HİÇ gelmemiş olabilir (uç düştü) ya da gelmiş ama
  // sayacı taşımıyor olabilir (özet üretilemedi). İkisi de "0 çağrı" DEĞİLDİR ve gerekçeleri ayrı.
  const olculemedi = !t || n == null;
  const ozet = olculemedi
    ? kartOzeti({ deger: null, rozet: "ÖLÇÜLEMEDİ",
        meta: t ? "`agent_calls` bloğu geldi ama çağrı sayacı (`n`) yok — özet ÜRETİLEMEDİ; "
                + "bu 'hiç ajan çağrısı olmadı' DEĞİLDİR."
                : "çağrı telemetrisi özeti /api/hermes gövdesinde YOK — defter okunamadı ya da özet "
                + "üretilemedi; bu 'hiç ajan çağrısı olmadı' DEĞİLDİR." })
    : kartOzeti({ deger: `${trn(dolu)}/${trn(n)}`,
        oran: n ? dolu / n : null,
        payda: n ? `pencerede ölçülen ajan çağrısı${pencereSaat ? ` (son ${trn(pencereSaat)} sa)` : ""}` : "",
        degerSinif: bosumsu ? "warn" : "",
        meta: n
          ? `p50 ${trn(sure.p50)} ms · p95 ${trn(sure.p95)} ms · en yavaş ${trn(sure.max)} ms${
              t.pencere_disi ? ` · ${trn(t.pencere_disi)} satır pencere DIŞI` : ""}`
          : `pencerede ÇAĞRI YOK · ${trn(t.pencere_disi)} satır pencerenin dışında kaldı — "hiç çağrı olmadı" ile "hepsi eski" AYNI ŞEY DEĞİLDİR`,
        rozet: bosumsu ? "BOŞ DÖNEN ÇAĞRI" : "" });
  const dagilimSatir = (ad, adet) => `<div class="trow" style="grid-template-columns:1fr 64px 74px">
    <span class="chain">${esc(ad)}</span><span class="mono-num">${trn(adet)}</span>
    <span class="mono-num mut">${n ? pctf(adet / n, 0) : "—"}</span></div>`;
  return `<div class="card rise"${katKart("hermes:telemetri")}>
    <h2 class="t">Ajan çağrı telemetrisi <span class="tx3" style="font-weight:400">(gece koşusu neden uzadı, hangi çağrı takıldı?)</span></h2>
    ${ozet}
    ${olculemedi ? firsatBos(t
        ? "`agent_calls` bloğu geldi ama çağrı sayacı yok — pencerede kaç çağrı olduğu ölçülemedi."
        : "`integrations.agent_calls` bloğu uçtan gelmedi — çağrı-başına süre ve sonuç sınıfı bu turda ölçülemedi.",
        "Kota ve bütçe satırları yukarıdaki durum kartında; eksik olan ÇAĞRININ KENDİSİ (süre, sonuç sınıfı, taşıyıcı).")
      : `<div class="srow"><span>Pencere</span><b class="mono-num">${
           pencereSaat ? `son ${trn(pencereSaat)} sa` : "tüm defter"} · ${trn(n)} satır sayıldı${
           t.pencere_disi ? ` · ${trn(t.pencere_disi)} satır dışarıda` : ""}</b></div>
         <div class="srow"><span>Toplam süre (pencerede)</span><b class="mono-num">${
           sure.toplam == null ? "—" : `${trn(sure.toplam)} ms`}</b></div>
         <div class="srow"><span>Araç çağrısı (ortalama)</span><b class="mono-num">${
           arac.ort == null ? "ÖLÇÜLEMEDİ" : trn(arac.ort, 2)}</b></div>
         ${arac.olculemeyen ? `<p class="hint" style="margin-top:2px">${trn(arac.olculemeyen)} çağrıda
            araç sayısı ÖLÇÜLEMEDİ (<code>-Q</code> sessiz mod oturum özetini bastırır) ve ortalama
            YALNIZ ölçülen ${trn(arac.olculen)} çağrının içinden alındı — ölçülemeyeni paydaya katmak
            oranı sessizce seyreltirdi.</p>` : ""}
         ${(t.en_yavas) ? `<div class="srow"><span>En yavaş çağrı</span><b class="mono-num">${
            trn(t.en_yavas.sure_ms)} ms · ${esc(String(t.en_yavas.kind || "?"))} · ${
            esc(String(t.en_yavas.model || "model yazılmamış"))} · ${esc(String(t.en_yavas.sonuc_sinifi || "?"))}</b></div>`
          : `<p class="hint" style="margin-top:2px">En yavaş çağrı yok — pencerede süre taşıyan satır bulunamadı.</p>`}
         <div class="tbl" style="margin-top:10px">
           <div class="trow head" style="grid-template-columns:1fr 64px 74px">
             <span>SONUÇ SINIFI</span><span>ÇAĞRI</span><span>PAY</span></div>
           ${Object.entries(sinif).sort((a, b) => b[1] - a[1]).map(([ad, adet]) => dagilimSatir(ad, adet)).join("")
             || `<div class="empty" style="font-size:12px">pencerede sınıflanmış çağrı yok</div>`}</div>
         ${detayKatmani("Model ve taşıyıcı kırılımı · iz defteri",
             "Aynı pencerenin ikinci kesiti: hangi model kaç kez çağrıldı ve çağrı hangi taşıyıcıdan "
             + "gitti (yerel ajan CLI'ı mı, doğrudan HTTP mi). İz defteri satırı OKUNMADAN yalnız BAYT "
             + "damgasıyla ölçülür — satır sayısı türetilmez.",
             `<div class="tbl">
                <div class="trow head" style="grid-template-columns:1fr 64px 74px">
                  <span>MODEL</span><span>ÇAĞRI</span><span>PAY</span></div>
                ${Object.entries((t.model) || {}).sort((a, b) => b[1] - a[1]).map(([ad, adet]) => dagilimSatir(ad, adet)).join("")
                  || `<div class="empty" style="font-size:12px">model alanı taşıyan satır yok</div>`}</div>
              <div class="tbl" style="margin-top:10px">
                <div class="trow head" style="grid-template-columns:1fr 64px 74px">
                  <span>TAŞIYICI</span><span>ÇAĞRI</span><span>PAY</span></div>
                ${Object.entries((t.tasiyici) || {}).sort((a, b) => b[1] - a[1]).map(([ad, adet]) => dagilimSatir(ad, adet)).join("")
                  || `<div class="empty" style="font-size:12px">taşıyıcı alanı taşıyan satır yok</div>`}</div>
              <div class="srow" style="margin-top:10px"><span>Ham iz defteri</span><b class="mono-num">${
                iz.bayt == null ? "—" : `${trn(Math.round(iz.bayt / 1000))} KB`}${
                iz.disk_tavani_mb == null ? "" : ` / ${trn(iz.disk_tavani_mb, 2)} MB türetilmiş tavan`}</b></div>
              <p class="hint" style="margin-top:6px">${esc(String(iz.beyan || "iz defteri beyanı gelmedi"))}</p>`)}
         <p class="hint" style="margin-top:10px">${esc(String(t.beyan || "özet beyanı gelmedi"))}</p>`}</div>`;
}

// ---- C1-5 · ROLLBACK SİCİLİ (④ ogrenme#ajan) -------------------------------------------------
// PRODUCT.md'nin AÇIK VAADİ ("underperforming versions auto-rollback") ve konumlandırmanın dört
// sütunundan biri. Panoda karşılığı YOKTU: `app.js` içinde "rollback" kelimesi SIFIR kez geçiyordu.
// Bir vaadin görünmezliği, vaadin kendisini ölçülemez yapar.
function firsatRollbackSicili(rb) {
  const S = (rb && rb.var) ? (rb.surumler || []) : null;
  const geri = S ? S.filter(v => v.rolled_back) : [];
  const acik = (rb && rb.acik_dongu) ? Object.keys(rb.acik_dongu).length : null;
  const ozet = !S
    ? kartOzeti({ deger: null, rozet: "ÖLÇÜLEMEDİ",
        meta: (rb && rb.neden) ? esc(rb.neden)
          : "karne defteri okunamadı — geri-alma sicili ölçülemedi ('hiç geri alınmadı' DEĞİL)." })
    : kartOzeti({ deger: trn(geri.length), oran: kanitOrani(S.length), payda: "kayıtlı sürüm",
        meta: `${trn(S.length)} sürüm · yürürlükte <b>v${esc(String(rb.current_version))}</b>${
          rb.esik == null ? "" : ` · eşik ${trn(rb.esik, 3)}`}`,
        rozet: (acik != null && acik > 0) ? "AÇIK ÖĞRENME DÖNGÜSÜ" : "" });
  const satir = v => `<div class="trow" style="grid-template-columns:52px 96px 84px 74px 1fr">
    <span class="chain">v${esc(String(v.version).padStart(2, "0"))}${v.guncel ? " ●" : ""}</span>
    ${_chip(v.rolled_back ? "GERİ ALINDI" : (v.reinstated ? "GERİ GETİRİLDİ" : "yürürlükte kaldı"),
            v.rolled_back ? "t-no" : "t-vi")}
    <span class="mono-num">${v.live_score == null ? (v.backtest_oos == null ? "—" : trn(v.backtest_oos, 4)) : trn(v.live_score, 4)}</span>
    <span class="mono-num mut">${v.n_trades == null ? "—" : trn(v.n_trades) + " işlem"}</span>
    <span class="chain mut">${esc(String(v.note == null ? (v.source == null ? "gerekçe yazılmamış" : v.source) : v.note).slice(0, 110))}</span></div>`;
  const olaySatir = o => `<div class="trow" style="grid-template-columns:150px 1fr">
    <span class="mono-num">${esc(String(o.ts == null ? "—" : String(o.ts).replace("T", " ").slice(0, 19)))}</span>
    <span class="chain mut">${esc(o.event)}${o.version == null ? "" : ` · v${esc(String(o.version))}`}${
      o.reason ? " · " + esc(String(o.reason).slice(0, 90)) : ""}</span></div>`;
  return `<div class="card rise"${katKart("ajan:rollback")}>
    <h2 class="t">Rollback sicili <span class="tx3" style="font-weight:400">(kendini gerçekten geri alıyor mu?)</span></h2>
    ${ozet}
    ${!S ? firsatBos((rb && rb.neden) ? rb.neden
        : "karne defteri (`scoreboard.json`) okunamadı — geri-alma sicili bu turda ölçülemedi.",
        "Vaat PRODUCT.md'de yazılı; kanıtı bu kartta yaşar. Kartın boş olması vaadin yanlış olduğunu DEĞİL, ölçemediğimizi söyler.")
      : `<div class="srow"><span>Açık öğrenme döngüsü</span><b class="mono-num">${
           rb.acik_dongu == null ? esc(String(rb.acik_dongu_neden))
             : (acik ? `${trn(acik)} kayıt AÇIK` : "açık döngü YOK (defter okundu, boş)")}</b></div>
         <div class="tbl" style="margin-top:10px">
           <div class="trow head" style="grid-template-columns:52px 96px 84px 74px 1fr">
             <span>SÜRÜM</span><span>HÜKÜM</span><span>SKOR</span><span>ÖRNEKLEM</span><span>GEREKÇE / KAYNAK</span></div>
           ${S.map(satir).join("")}</div>
         ${(rb.olaylar || []).length ? detayKatmani("Çürütme kayıtları · olay defteri",
             "`rollback_*` ve `learning_loop_*` olayları: hükmün ne zaman ve neden verildiği.",
             `<div class="tbl">
                <div class="trow head" style="grid-template-columns:150px 1fr"><span>ZAMAN (UTC)</span><span>OLAY</span></div>
                ${rb.olaylar.map(olaySatir).join("")}</div>
              <p class="hint" style="margin-top:8px">Son <b>${trn(rb.olay_penceresi)}</b> olay tarandı.</p>`)
           : `<p class="hint" style="margin-top:10px">Son <b>${trn(rb.olay_penceresi)}</b> olayda çürütme kaydı
                görülmedi — bu "hiç olmadı" DEĞİL, "bu pencerede yok" demektir.</p>`}`}</div>`;
}

// ---- C1-6 · REGRESYON KIRILIMI (④ ogrenme#ajan) ----------------------------------------------
// "v3→v4 net iyileşme mi, yoksa bir yerde kazanıp başka yerde mi kaybettim?" Toplam skorun
// gizlediği TEK şey budur. Kaynak: `trades.jsonl` satırlarındaki `strategy_version` damgası —
// yani kırılım gerçekten ölçülebilir, türetilmiyor.
// SINIR AÇIK YAZILIR: dilim örneklemi küçükse satır `AZ` rozeti taşır ve bir HÜKÜM değil bir
// GÖZLEMdir; tek sürümlü bir defterde "neyi bozdu" sorusunun karşılaştırma tarafı YOKTUR.
function firsatRegresyon(rg) {
  const S = (rg && rg.var) ? (rg.surumler || []) : null;
  const f = (rg && rg.var) ? rg.fark : null;
  const bozan = f ? (f.rejim || []).filter(k => k.delta_r != null && k.delta_r < 0) : [];
  const duzelten = f ? (f.rejim || []).filter(k => k.delta_r != null && k.delta_r > 0) : [];
  const ozet = !S
    ? kartOzeti({ deger: null, rozet: "ÖLÇÜLEMEDİ",
        meta: (rg && rg.neden) ? esc(rg.neden)
          : "işlem defteri sürüm damgası taşımıyor — regresyon kırılımı ölçülemedi." })
    : kartOzeti(f
        ? { deger: `${trn(duzelten.length)}↑ / ${trn(bozan.length)}↓`,
            degerSinif: bozan.length ? "warn" : "",
            oran: kanitOrani(rg.islem_n), payda: "sürüm damgalı kapanmış işlem",
            meta: `v${esc(String(f.eski))} → v${esc(String(f.yeni))} · ${trn((f.rejim || []).length)} rejim dilimi karşılaştırıldı`,
            rozet: bozan.length ? "REGRESYON VAR" : "" }
        : { deger: trn(S.length), oran: kanitOrani(rg.islem_n), payda: "sürüm damgalı kapanmış işlem",
            meta: `${trn(rg.islem_n)} işlem tek sürümde toplanıyor — karşılaştırma tarafı yok`,
            rozet: "KIYAS YOK" });
  const dilimSatir = (d, etiket) => `<div class="trow" style="grid-template-columns:120px 54px 82px 1fr">
    <span class="chain">${esc(etiket === "rejim" ? (REGIME_TR[d.ad] == null ? d.ad : REGIME_TR[d.ad]) : (EXIT_TR[d.ad] == null ? d.ad : EXIT_TR[d.ad]))}</span>
    <span class="mono-num">${trn(d.n)}</span>
    <span class="mono-num ${cls(d.avg_r)}">${d.avg_r == null ? "—" : isr(d.avg_r, trn(d.avg_r, 3)) + "R"}</span>
    <span>${d.az_ornek ? '<span class="tag t-vi">AZ ÖRNEK</span>' : ""}</span></div>`;
  const farkSatir = k => `<div class="trow" style="grid-template-columns:120px 92px 84px 1fr">
    <span class="chain">${esc(REGIME_TR[k.ad] == null ? k.ad : REGIME_TR[k.ad])}</span>
    <span class="mono-num ${cls(k.delta_r)}">${k.delta_r == null ? "—" : isr(k.delta_r, trn(k.delta_r, 3)) + "R"}</span>
    <span class="mono-num mut">${k.n_yeni == null ? "—" : `${trn(k.n_yeni)} / ${trn(k.n_eski)}`}</span>
    <span class="chain mut">${k.delta_r == null ? esc(String(k.neden == null ? "ölçülemedi" : k.neden))
      : (k.az_ornek ? "az örneklem — gözlem, hüküm değil" : "")}</span></div>`;
  return `<div class="card rise"${katKart("ajan:regresyon")}>
    <h2 class="t">Bu sürüm neyi düzeltti, neyi BOZDU? <span class="tx3" style="font-weight:400">(regresyon kırılımı)</span></h2>
    ${ozet}
    ${!S ? firsatBos((rg && rg.neden) ? rg.neden
        : "`trades.jsonl` sürüm kırılımı üretmedi — regresyon bu turda ölçülemedi.",
        "Kırılım YALNIZ `strategy_version` damgalı kapanmış işlemlerden türer; damgasız satır hiçbir sürüme yazılmaz.")
      : `${f ? `<div class="tbl" style="margin-top:10px">
             <div class="trow head" style="grid-template-columns:120px 92px 84px 1fr">
               <span>REJİM</span><span>Δ ORT. R</span><span>N (yeni/eski)</span><span>NOT</span></div>
             ${(f.rejim || []).map(farkSatir).join("")}</div>
           <p class="hint" style="margin-top:8px">v${esc(String(f.eski))} → v${esc(String(f.yeni))}:
             <b>${trn(duzelten.length)}</b> dilim iyileşti, <b>${trn(bozan.length)}</b> dilim bozuldu.
             Toplam skor bu ayrımı GİZLER.</p>`
         : `<p class="hint" style="margin-top:0">Defterde karşılaştırılabilir ikinci bir sürüm yok —
              "neyi bozdu" sorusunun kıyas tarafı ÖLÇÜLEMEZ. Aşağıdaki kırılım tek sürümün kendi
              dilimleridir; bir öncekiyle farkı değil.</p>`}
         ${S.map(v => detayKatmani(`v${String(v.version).padStart(2, "0")} · ${v.n} işlem · ort. ${
             v.avg_r == null ? "ölçülemedi" : v.avg_r + "R"}`,
             "Dilim ortalaması bir hüküm değil bir gözlemdir; örneklem eşiğin altındaysa satır AZ ÖRNEK rozeti taşır.",
             `<div class="tbl">
                <div class="trow head" style="grid-template-columns:120px 54px 82px 1fr">
                  <span>REJİM</span><span>N</span><span>ORT. R</span><span></span></div>
                ${(v.rejim || []).map(d => dilimSatir(d, "rejim")).join("")}</div>
              <div class="tbl" style="margin-top:10px">
                <div class="trow head" style="grid-template-columns:120px 54px 82px 1fr">
                  <span>ÇIKIŞ NEDENİ</span><span>N</span><span>ORT. R</span><span></span></div>
                ${(v.cikis || []).map(d => dilimSatir(d, "cikis")).join("")}</div>`)).join("")}
         <p class="hint" style="margin-top:10px">${esc(String(rg.sinir))}</p>`}</div>`;
}

// ---- C1-10 · SKORUN OLGUNLAŞMA GÖSTERGESİ (④ ogrenme#karne) ----------------------------------
// Meridian DOĞRU davranıyor (n < min_sample'da skor `None`) ama operatöre MESAFEYİ söylemiyordu;
// "ölçülemedi" kalıcı bir duvar gibi okunuyordu. Numerai'nin 20D2L deseni: skor gün gün olgunlaşır
// ve olgunlaşmanın kendisi gösterilir.
// HİÇBİR EŞİK PANODA SABİTLENMEZ: `min_sample` hedeften, ufuk kapısı beyin durumundan, merdiven
// ölçütleri `/api/summary`den okunur. Sayı burada YAZILI OLSAYDI, hedef değiştiği gün pano yalan
// söylerdi (C10 dersi).
function firsatOlgunlasma(sd, hz, ladder, cf) {
  const n = (sd || {}).n, min = (sd || {}).min_sample;
  const kalan = (n != null && min != null) ? Math.max(0, Number(min) - Number(n)) : null;
  const oran = (n != null && min != null && Number(min) > 0)
    ? Math.min(1, Number(n) / Number(min)) : null;
  const ap = (ladder || {}).auto_progress;
  const ozet = (n == null || min == null)
    ? kartOzeti({ deger: null, rozet: "ÖLÇÜLEMEDİ",
        meta: "skor ayrıntısı (`score_detail.n` / `min_sample`) uçtan gelmedi — olgunlaşma mesafesi ölçülemedi." })
    : kartOzeti({ deger: `${trn(n)}/${trn(min)}`, oran: oran, payda: "hedefin min_sample'ı",
        meta: kalan === 0 ? `örneklem eşiği DOLDU · skor ${(sd.score == null ? "hâlâ ölçülemedi (başka kapı)" : trn(sd.score, 4))}`
          : `<b>${trn(kalan)}</b> kapanmış işlem daha gerekiyor · skor şu an ${sd.score == null ? "ölçülemedi" : trn(sd.score, 4)}`,
        rozet: kalan === 0 ? "" : "OLGUNLAŞIYOR" });
  const kapi = (ad, hazir, metin) => `<div class="srow"><span>${esc(ad)}</span>
    <b class="mono-num">${hazir === null ? '<span class="mut">ölçülemedi</span>' : metin}</b></div>`;
  return `<div class="card rise"${katKart("karne:olgunlasma")}>
    <h2 class="t">Skorun olgunlaşması <span class="tx3" style="font-weight:400">(bu sayı ne zaman güvenilir olacak?)</span></h2>
    ${ozet}
    ${(n == null || min == null)
      ? firsatBos("`score_detail` panoya ulaşmadı — skorun eşiğe mesafesi bu turda ölçülemedi.",
          "'Ölçülemedi' doğru bir cevaptır; MESAFESİZ olması kusurdu — mesafe bu kartın işi.")
      : `${kapi("Örneklem kapısı", n != null,
            `${trn(n)}/${trn(min)} kapanmış işlem${kalan === 0 ? " · DOLDU" : ` · ${trn(kalan)} kaldı`}`)}
         ${kapi("Ufuk kapısı (rejim dilimi)", hz == null ? null : true,
            hz == null ? "" : (hz.ready ? "hazır"
              : `${trn(hz.trades)}/${trn(hz.trades_needed)} işlem · ${trn(hz.span_days)}/${trn(hz.min_days)} gün${
                  hz.regime ? ` · ${esc(REGIME_TR[hz.regime] == null ? hz.regime : REGIME_TR[hz.regime])}` : ""}`))}
         ${kapi("Otonomi merdiveni (L0→L1)", ap == null ? null : true,
            ap == null ? "" : `${trn(ap.met)}/${trn(ap.total)} ölçüt karşılandı`)}
         ${kapi("Karşı-olgusal sadakat kesişimi", cf == null ? null : true,
            cf == null ? "" : `${trn(cf.n)} kesişim kaydı${
              cf.corr == null ? " · korelasyon ölçülemedi" : ` · korelasyon ${trn(cf.corr, 3)}`}`)}
         <p class="hint" style="margin-top:10px">Eşiklerin hiçbiri burada SABİT yazılı değil: örneklem
           eşiği hedeften (<code>goal.min_sample</code>), ufuk kapısı beyin durumundan, merdiven
           <code>/api/summary</code>'den okunur. Eşik değişirse bu kart onunla birlikte değişir.</p>
         ${(ladder && ladder.l0_to_l1) ? detayKatmani("L0 → L1 ölçütleri · tek tek",
             "Merdivenin ölçütleri; `manual` bayraklı olanlar operatör kalemidir, ajan onları kendi "
             + "kapatamaz. MESAFE sütunu üreticinin kendi `detail` metnidir — burada TÜRETİLMEZ.",
             `<div class="tbl">
                <div class="trow head" style="grid-template-columns:1fr 96px 118px 74px">
                  <span>ÖLÇÜT</span><span>DURUM</span><span>MESAFE</span><span>KİM</span></div>
                ${ladder.l0_to_l1.map(k => `<div class="trow" style="grid-template-columns:1fr 96px 118px 74px">
                    <span class="chain">${esc(String(k.label == null ? (k.criterion == null ? "—" : k.criterion) : k.label))}</span>
                    ${_chip(k.met === true ? "KARŞILANDI" : (k.met === false ? "bekliyor" : "ölçülemedi"),
                            k.met === true ? "t-go" : "t-vi")}
                    <span class="mono-num mut">${k.detail == null ? "ölçülemedi" : esc(String(k.detail))}</span>
                    <span class="chain mut">${k.manual ? "operatör" : "ajan"}</span></div>`).join("")}</div>`) : ""}`}</div>`;
}

// ==============================================================================================
// D3-b · FIRSAT YÜZEYLERİ (F1/F2/F14) — kalan on beş FIRSAT'ın üçü (docs/TASARIM-YONU-2026-08-07 §7)
// ----------------------------------------------------------------------------------------------
// Üçü de MEVCUT sözleşmenin üstüne oturur: `.pm-*` hücre dili (v192), kart sözleşmesi (v198),
// ÖLÇÜLEMEDİ≠0 (v191/v196) ve D1'in beş renk rolü. Yeni jeton, yeni renk, yeni bileşen YOK —
// üçü de "üretiliyor ama görünmüyor" kovasından bir kalem kapatır ve UÇTAN OKUR (uydurma rakam
// yasağı; landing-fabricated-figures dersi). Veri bacakları wave-2'de indi; bu blok PANO bacağıdır.

// ---- F14 · İKİ KADEMELİ EŞİK + NO_DATA — panonun TEK üç-hâl dili ------------------------------
// ÖLÇÜLEN KUSUR: eşikli göstergeler panoda ÜÇ ayrı biçimde konuşuyordu — kimi `warn` (sev-2), kimi
// elle `n >= mx ? "sev-1" : n/mx > 0.6 ? "sev-2" : "accent"` (app.js:5899), kimi renksiz. ÜÇ HÂL
// (uyarı / alarm / ölçülemedi) her göstergede AYNI olmalı; bu fonksiyon o dili TEK yerde kurar ve
// başka göstergeler de onu okuyabilsin diye SAF tutulur (Node'da davranış olarak ölçülür).
// D1 ROL KATMANI: uyarı → --sev-2 ("insan gerekiyor") · alarm → --sev-1 ("şimdi müdahale"). Renk
// YALNIZ bu iki hâlde doğar; "iyi" renksizdir (yeşil bir alarm bütçesi kalemidir) ve "ölçülemedi"
// bir ŞİDDET DEĞİLDİR — sönüktür, çünkü ölçememek bir alarm seviyesi değil bir veri boşluğudur.
// NO_DATA ≠ 0: değer null/boş/sonsuz ise hâl "olculemedi"dir ve eşik HİÇ sınanmaz (0, sınırı
// geçmiş sayılmaz — "ölçtük, sıfır çıktı" ile "ölçemedik" aynı kovaya düşemez).
function esikHal(deger, o) {
  o = o || {};
  const n = Number(deger);
  if (deger == null || deger === "" || !Number.isFinite(n))
    return { durum: "olculemedi", sev: "", etiket: "ÖLÇÜLEMEDİ" };
  // `yon`: "yuksek" (büyük değer kötü — sayı YUKARI geçince tetikler) / "dusuk" (küçük değer kötü).
  const yuksek = String(o.yon == null ? "yuksek" : o.yon) !== "dusuk";
  const gecti = esik => (esik == null || !Number.isFinite(Number(esik))) ? false
    : (yuksek ? n >= Number(esik) : n <= Number(esik));
  // ALARM ÖNCE SINANIR: iki eşik de geçildiyse daha şiddetli hâl kazanır (alarm eşiği uyarıdan
  // daha uçtadır — yuksek'te büyük, dusuk'te küçük — sıra bu yüzden alarm→uyarı).
  if (gecti(o.alarm)) return { durum: "alarm", sev: "sev-1", etiket: "ALARM" };
  if (gecti(o.uyari)) return { durum: "uyari", sev: "sev-2", etiket: "UYARI" };
  return { durum: "iyi", sev: "", etiket: "" };
}
// EŞİK SATIRI — bir göstergenin değeri + üç-hâl etiketi TEK `.srow`da. Etiket METİNle konuşur
// (renk üçüncü kanal, D1); "iyi" hâl SESSİZdir (etiketsiz), "ölçülemedi" sönük ve NEDENLİdir
// (`olcumsuz` beyanı — "0 DEĞİL"). Değerin rengi de aynı rol jetonundan gelir (sev-1/sev-2).
function esikSatiri(etiket, deger, o) {
  o = o || {};
  const h = esikHal(deger, o);
  const deg = h.durum === "olculemedi"
    ? `<span class="mut">${esc(o.olcumsuz == null ? "ölçülemedi (0 DEĞİL)" : o.olcumsuz)}</span>`
    : `<span class="mono-num${h.sev ? " " + h.sev : ""}">${o.bicim ? o.bicim(deger) : trn(deger)}</span>`;
  const et = h.etiket
    ? ` <span class="${h.durum === "olculemedi" ? "tx3" : h.sev}" style="font-weight:600">${h.etiket}</span>`
    : "";
  return `<div class="srow"><span>${esc(etiket)}${
    o.esikNot ? ` <span class="tx3" style="font-weight:400">${esc(o.esikNot)}</span>` : ""}</span><b>${deg}${et}</b></div>`;
}

// ---- F1 · KÂĞIDIN NEREDE YALAN SÖYLEDİĞİ (③ saglik#veriboru) ---------------------------------
// OPERATÖRÜN SORUSU (L1'e geçişin ÖN-ŞARTI): "Canlı kanıt ne kadar?" `/api/public/summary` 96
// "kapanmış işlem" diyordu ve gövdesi replay TOHUMU (training, survivorship'li); GERÇEK canlı
// yalnız N. Ayrım wave-2'de ledgerstamp'ten indi (closed_trades_live/seed, live{n,mean_r}) —
// pano onu ÜÇÜNCÜ kez KURMAZ, uçtan OKUR (landing ile aynı sayı; uydurma rakam yasağı). HANGİ
// METRİK KÂĞITTA ŞİŞİK: ham toplam (closed_trades) tohumla şişer, canlı satır onu paylaşmaz —
// çubukların paydası her ikisi için de HAM TOPLAM, yani şişme GÖZLE ölçülür. $ P&L dışarı verilmez.
function firsatKagitCanli(ps) {
  const p = ps && typeof ps === "object" ? ps : null;
  const liveN = p ? (p.live && p.live.n != null ? p.live.n : p.closed_trades_live) : null;
  const seedN = p ? (p.seed && p.seed.n != null ? p.seed.n : p.closed_trades_seed) : null;
  const belN  = p ? p.closed_trades_belirsiz : null;
  const hamN  = p ? p.closed_trades : null;
  const meanR = p && p.live ? p.live.mean_r : null;
  const payVar = hamN != null && Number.isFinite(Number(hamN)) && Number(hamN) > 0;   // çubuk paydası
  const sisik  = liveN != null && seedN != null && Number(liveN) < Number(seedN);
  const canliOran = (payVar && liveN != null) ? Number(liveN) / Number(hamN) : null;
  const ozet = !p
    ? kartOzeti({ deger: null, rozet: "ÖLÇÜLEMEDİ",
        meta: "/api/public/summary okunamadı — canlı/tohum ayrımı bu turda ÖLÇÜLEMEDİ ('canlı kanıt yok' DEĞİL)." })
    : kartOzeti({ deger: liveN == null ? null : trn(liveN),
        oran: canliOran, payda: payVar ? `kapanmış işlem (${trn(hamN)})` : "",
        meta: `defter toplamı <b>${trn(hamN)}</b> · tohum <b>${trn(seedN)}</b>${
          belN ? ` · belirsiz ${trn(belN)}` : ""} · canlı ort. ${
          meanR == null ? "ölçülemedi" : isr(meanR, trn(meanR, 3)) + "R"}`,
        rozet: liveN == null ? "ÖLÇÜLEMEDİ" : (sisik ? "KÂĞIT ŞİŞİK" : "") });
  // DÖRT SATIRLI KIRILIM (ozetSerit DEĞİL — şerit sayısı v226 tabanında 6 kalır; yeni şerit
  // BEYANI gerekmedi). CANLI + TOHUM'un PAYI ham toplama göre yazılır (payda başlıkta ve alt
  // hintte ADIYLA beyanlı); BELİRSİZ + HAM TOPLAM PAYSIZdır — kendileri bir sayıdır, uydurma
  // tavana bölünemez ("—" basar). Kırılım payda denetimi test_wpux_d3b_v229'da (F1 bölümü).
  // PAY = parçanın (canlı/tohum/belirsiz) HAM TOPLAM içindeki payı. `paysiz` satırlar (ham toplam
  // = paydanın KENDİSİ) "—" basar: bir sayının kendine oranını yazmak boş bir tavan uydurmaktır.
  const pay = (n, paysiz) => (!paysiz && payVar && n != null && Number.isFinite(Number(n))) ? pctf(Number(n) / Number(hamN), 0) : "—";
  const satir = (ad, n, not, vurgu, paysiz) => `<div class="trow" style="grid-template-columns:132px 62px 74px 1fr">
    <span class="chain${vurgu ? "" : " mut"}">${esc(ad)}</span>
    <span class="mono-num">${n == null ? "—" : trn(n)}</span>
    <span class="mono-num mut">${pay(n, paysiz)}</span>
    <span class="hint" style="margin:0">${not}</span></div>`;
  return `<div class="card rise"${katKart("veriboru:kagitcanli")}>
    <h2 class="t">Kâğıt-canlı ayrışması <span class="tx3" style="font-weight:400">(canlı kanıt ne kadar? — kâğıt nerede yalan söylüyor?)</span></h2>
    ${ozet}
    ${!p ? firsatBos("/api/public/summary okunamadı — canlı defter ile tohumun ayrıştığı yer ölçülemedi.",
        "Bu uç kimlik doğrulamasızdır (tanıtım yüzeyiyle aynı sayı); okunamıyorsa ayrım da türetilemez.")
      : `<p class="hint" style="margin-top:0">Ledgerstamp ayrımı (landing ile aynı kaynak): defter
           <b>${trn(hamN)}</b> işlemin <b>${trn(seedN)}</b>'i replay TOHUMU, gerçek canlı yalnız
           <b>${trn(liveN)}</b>. "Kapanmış işlem" manşeti bu yüzden kâğıtta ŞİŞİKtir — L1'e geçiş
           kararı canlı satıra bakar, ham toplama değil.</p>
         <div class="tbl" style="margin-top:10px">
           <div class="trow head" style="grid-template-columns:132px 62px 74px 1fr">
             <span>KAYNAK</span><span>N</span><span>PAY (ham)</span><span>NOT</span></div>
           ${satir("Canlı işlem", liveN, meanR == null ? "gerçek kanıt · ort. R ölçülemedi" : `gerçek kanıt · ort. ${isr(meanR, trn(meanR, 3))}R`, true)}
           ${satir("Tohum (replay)", seedN, "training · survivorship'li — canlı kanıt SAYILMAZ", true)}
           ${satir("Belirsiz", belN, "kaynak damgası sınıflanamadı (canlı/tohum değil)", false)}
           ${satir("Ham toplam", hamN, "tohum DAHİL — kâğıdın şiştiği sayı budur", false, true)}</div>
         <p class="hint" style="margin-top:10px">PAY sütunu parçaların (canlı / tohum / belirsiz)
           AYNI paydadan (ham toplam ${trn(hamN)}) payıdır — canlı payın küçüklüğü doğrudan görünür.
           HAM TOPLAM paydanın KENDİSİ olduğu için paysızdır ("—"). $ P&L bu uçtan DIŞARI VERİLMEZ;
           canlı sonuç R-multiple olarak taşınır (uç sözleşmesi).</p>`}</div>`;
}

// ---- F2 · CANLI-BACKTEST SAPMASININ KÖKÜ (④ ogrenme#bilesenic) -------------------------------
// E1/E2 HATTININ KALBİ. Karne-tazeleme (2026-08-03) ölçtü: replay defteri +2.493$ → −1.182$'a
// döndü ve farkın TAMAMI E1 giriş-limitinin ATR bacağıydı (dolum 237→176). "Canlı ödeme neden
// geri-testten sapıyor?" sorusunun KÖKÜ budur — ve E2 defteri (`entry_execution.jsonl`) onu satır
// satır ölçer. Kart sapmayı ADLANDIRIR, sayı ŞİŞİRMEZ:
//   * GERÇEK sapma = LİMİT bacağı (`ayna.dolum.fill_vs_limit_bps`): yasa tavanı bağladı mı?
//   * TOTOLOJİ = iç motorun `fill_vs_resmi_acilis_bps`i None (dolum açılıştan SABİT slippage ile
//     türer — kendi kendini ölçer). Yazar (loop) satıra None + BEYAN bırakır; kart 0 basmaz,
//     beyanı SURFACE eder. Bu "E2'nin ölçtüğü gerçek sapma + totoloji-beyanı"nın tam kendisidir.
// HÜKÜM AZ ÖRNEKTEN UYDURULMAZ: sunucunun `yorum`u n_dolan eşiğine bağlı — pano onu OKUR, ikinci
// hüküm KURMAZ. Bu kart mutabakat masasının icra kartından AYRIDIR: orası "ayna gönderdi mi/doldu
// mu" (operasyon); burası "geri-test neden yalan söyledi" (öğrenme) — aynı defter, ayrı soru.
function firsatSapmaKoku(slp) {
  const s = slp && typeof slp === "object" ? slp : null;
  const dl = s && s.ayna && typeof s.ayna.dolum === "object" ? s.ayna.dolum : {};
  const ic = s && typeof s.ic_motor === "object" ? s.ic_motor : {};
  const limit  = dl.fill_vs_limit_bps && typeof dl.fill_vs_limit_bps === "object" ? dl.fill_vs_limit_bps : null;
  const acilis = dl.fill_vs_resmi_acilis_bps && typeof dl.fill_vs_resmi_acilis_bps === "object" ? dl.fill_vs_resmi_acilis_bps : null;
  const icBeyan = ic.fill_vs_resmi_acilis_beyan != null ? String(ic.fill_vs_resmi_acilis_beyan) : null;
  const nDolan = dl.n_dolan != null ? dl.n_dolan : null;
  const limOrt = limit && limit.ort != null ? limit.ort : null;
  const defterBos = s != null && String(s.durum == null ? "" : s.durum).includes("defter boş");
  const bosHal = !s || defterBos || nDolan == null || Number(nDolan) === 0;
  const dagilim = (b, ad) => {
    if (!b || b.ort == null) return `<div class="srow"><span>${esc(ad)}</span><b><span class="pm-none">ölçülemedi</span></b></div>`;
    return `<div class="srow"><span>${esc(ad)}</span><b><span class="mono-num">${trn(b.ort, 1)} bps</span> <span class="tx3" style="font-weight:400">medyan ${
      trn(b.medyan, 1)} · p90 ${trn(b.p90, 1)} · n=${trn(b.n)}${b.n_olculemeyen ? ` · ${trn(b.n_olculemeyen)} ölçülemeyen` : ""}</span></b></div>`;
  };
  const ozet = !s
    ? kartOzeti({ deger: null, rozet: "ÖLÇÜLEMEDİ",
        meta: "teşhis ucu `icra.slipaj` bloğunu vermedi — canlı-backtest sapması bu turda ÖLÇÜLEMEDİ (0 bps DEĞİL)." })
    : (bosHal
      ? kartOzeti({ deger: null, rozet: "DEFTER BOŞ",
          meta: `E2 defteri henüz dolum yazmadı${nDolan == null ? "" : ` (${trn(nDolan)} dolum)`} — ilk satır ilk ayna döngüsünde düşer. Sapma ölçülemedi, 0 bps DEĞİL.` })
      : kartOzeti({ deger: limOrt == null ? null : trn(limOrt, 1) + " bps",
          oran: kanitOrani(nDolan), payda: `dolum (${trn(nDolan)})`,
          meta: "limit-bacağı ORTALAMASI (gerçek sapma) · iç motorun açılış-bacağı TOTOLOJİK (None)",
          rozet: limOrt == null ? "ÖLÇÜLEMEDİ" : "" }));
  return `<div class="card rise"${katKart("bilesenic:sapma")}>
    <h2 class="t">Canlı-backtest sapmasının kökü <span class="tx3" style="font-weight:400">(canlı ödeme neden geri-testten sapıyor? · E1/E2 hattı)</span></h2>
    ${ozet}
    ${!s ? firsatBos("teşhis ucu `icra.slipaj` (E2 defteri) bloğunu vermedi — sapmanın kökü ölçülemedi.",
        "E1/E2 hattının kalbi: canlı ödeme ile geri-test farkı bu defterde satır satır ölçülür.")
      : (bosHal
        ? firsatBos(String(s.durum == null ? "E2 defteri boş — dolum yok" : s.durum),
            "Bu bir ÖLÇÜMdür: defter doğdu ve ilk dolumu bekliyor — okunamamış olmakla aynı şey değil.")
        : `<p class="hint" style="margin-top:0">Kök (E1 kararı, 2026-08-03): replay geri-testi
             giriş-limitinin ATR bacağını modellemiyordu — canlıda dolumlar düştü ve "kâğıt kâr"ın
             ana kaynağı buydu. GERÇEK sapma bir tahmin DEĞİL, E2 defterinin CANLI ölçümüdür ve iki
             bacakta durur:</p>
           ${dagilim(limit, "Limit-bacağı (GERÇEK sapma) — yasa tavanı bağladı mı?")}
           ${dagilim(acilis, "Açılış-bacağı (açılış mikroyapısı) — ayna")}
           <div class="srow"><span>İç motor · açılış-bacağı <span class="tx3" style="font-weight:400">(totoloji)</span></span>
             <b>${belirsiz('<span class="pm-none">None — beyanlı</span>', icBeyan == null ? "iç motorun açılış-bacağı beyanı yükte yok" : icBeyan)}</b></div>
           <p class="hint" style="margin-top:6px">İç motorun açılış-bacağı değeri <b>None</b>'dır (0 bps
             DEĞİL): dolum açılıştan SABİT slippage ile türer, yani kendi kendini ölçer — totoloji.
             ${icBeyan == null ? "" : "Yazarın beyanı yukarıdaki kesik-çizgide."} GERÇEK sapma yukarıdaki
             LİMİT bacağıdır; sayıyı şişirmemek için totolojik bacak ölçülmez, BEYAN edilir.</p>
           ${dl.yorum == null ? "" : `<p class="hint" style="margin-top:10px">${esc(String(dl.yorum))}</p>`}`)}</div>`;
}

// ---- F14 · İKİ KADEMELİ EŞİK PANELİ (③ saglik#operasyon) -------------------------------------
// `esikHal`in canlı vitrini: sağlık göstergeleri TEK üç-hâl dilinde (uyarı sev-2 / alarm sev-1 /
// ölçülemedi sönük). Dört gösterge, dördü de _DIAG'dan OKUNUR (uydurma yok); eşikler burada SABİT
// yazılı DEĞİL göstergenin kendi ölçeğinden türer (EOD sabır tavanı `refetch_max` gibi — C10 dersi
// hükümler içindir, bir görünürlük eşiği hüküm değildir ve satırında ADIYLA yazar).
function firsatEsikPaneli(d) {
  const D = d && typeof d === "object" ? d : null;
  const wd = D && typeof D.watchdog === "object" ? D.watchdog : {};
  const pl = D && typeof D.pipeline === "object" ? D.pipeline : {};
  const geciken = D ? ((wd.stale || []).length + (wd.never || []).length) : null;
  const nd = pl.symbol_no_data && typeof pl.symbol_no_data === "object" ? pl.symbol_no_data : {};
  const veriYok = D ? (nd.confirmed_no_data || []).length : null;
  const ud = pl.universe_drift && typeof pl.universe_drift === "object" ? pl.universe_drift : null;
  const sapan = ud ? ud.n_stale : null;                    // null = ÖLÇÜLMEDİ (uydurma 0 yok)
  const mx = pl.refetch_max != null && Number.isFinite(Number(pl.refetch_max)) ? Number(pl.refetch_max) : null;
  const sabir = Number.isFinite(Number(pl.refetch_attempts)) ? Number(pl.refetch_attempts) : null;
  const kalemler = [
    { ad: "Geciken bekçi mekanizması", deger: geciken, o: { uyari: 1, alarm: 3, esikNot: "uyarı ≥1 · alarm ≥3", olcumsuz: "bekçi raporu okunamadı" } },
    { ad: "Veri dönmeyen sembol (doğrulanmış)", deger: veriYok, o: { uyari: 1, alarm: 5, esikNot: "uyarı ≥1 · alarm ≥5", olcumsuz: "no-data taraması yok" } },
    { ad: "Endeksten düşen sembol (evren sapması)", deger: sapan, o: { uyari: 1, alarm: 3, esikNot: "uyarı ≥1 · alarm ≥3", olcumsuz: (ud && ud.status === "unknown") ? "sapma sayısı ÖLÇÜLMEDİ ('liste temiz' DEĞİL)" : "evren sapması okunamadı" } },
    { ad: "EOD sabır sayacı", deger: sabir, o: { uyari: mx == null ? null : mx * 0.6, alarm: mx,
        esikNot: mx == null ? "tavan ölçülemedi" : `uyarı ≥${trn(mx * 0.6, 1)} · alarm ≥${trn(mx)}`,
        olcumsuz: "deneme sayacı ölçülemedi (0 deneme DEĞİL)", bicim: v => mx == null ? trn(v) : `${trn(v)}/${trn(mx)}` } },
  ];
  const haller = D ? kalemler.map(k => esikHal(k.deger, k.o)) : [];
  const nAlarm = haller.filter(h => h.durum === "alarm").length;
  const nUyari = haller.filter(h => h.durum === "uyari").length;
  const nOlc = haller.filter(h => h.durum === "olculemedi").length;
  const nIyi = haller.length - nAlarm - nUyari - nOlc;
  const ozet = !D
    ? kartOzeti({ deger: null, rozet: "ÖLÇÜLEMEDİ",
        meta: "teşhis ucu okunamadı — eşikli göstergelerin hiçbiri bu turda ölçülemedi ('hepsi iyi' DEĞİL)." })
    : kartOzeti({ deger: `${nAlarm + nUyari}/${haller.length}`, degerSinif: nAlarm ? "warn" : "",
        oran: haller.length ? (nAlarm + nUyari) / haller.length : null,
        payda: `eşikli gösterge (${haller.length})`,
        meta: `${nAlarm} alarm · ${nUyari} uyarı · ${nIyi} iyi · ${nOlc} ölçülemedi`,
        rozet: nAlarm ? `${nAlarm} ALARM` : (nUyari ? `${nUyari} UYARI` : (nOlc ? "KISMEN ÖLÇÜLEMEDİ" : "")) });
  return `<div class="card rise"${katKart("operasyon:esik")}>
    <h2 class="t">Eşik durumu · iki kademe + veri-yok <span class="tx3" style="font-weight:400">(uyarı / alarm / ölçülemedi — tek dil)</span></h2>
    ${ozet}
    ${!D ? firsatBos("teşhis ucu okunamadı — eşikli göstergeler ölçülemedi.",
        "Dört gösterge de tek uçtan (`/api/diagnostics`) gelir; uç düştüyse hiçbiri türetilemez.")
      : `<p class="hint" style="margin-top:0">Her gösterge AYNI üç hâli konuşur:
           <b class="sev-2">UYARI</b> (insan gerekiyor) · <b class="sev-1">ALARM</b> (şimdi müdahale) ·
           <span class="mut">ölçülemedi</span> (0 DEĞİL). Eşikler göstergenin kendi ölçeğinden gelir,
           panoya sabit yazılmaz.</p>
         ${kalemler.map(k => esikSatiri(k.ad, k.deger, k.o)).join("")}
         <p class="hint" style="margin-top:10px">Bu panel eşik dilini TEK yerde (<code>esikHal</code>)
           kurar; aynı üç hâl artık başka göstergelere de aynı jetonlarla uygulanabilir (D1 rol
           katmanı: uyarı→--sev-2, alarm→--sev-1). Renk YALNIZ bu iki hâlde; "iyi" sessizdir.</p>`}</div>`;
}

// ---- F5 · YİNELENEN ARIZALARI TAKSONOMİYE KÜMELEME (③ saglik#operasyon) -----------------------
// OPERATÖRÜN SORUSU (docs/TASARIM-YONU-2026-08-07 §7 · F5): "Alarm gürültüsünün kökü ne — hangi
// mekanizma tekrar tekrar bağırıyor ve ne kadarı BASTIRILDI?" `watchdog.alarm_gunluk` v192'den beri
// mekanizma başına GÜNLÜK {alarm · bastırılan · askıda} sayacını yazıyordu ve PANO OKUYUCUSU YOKTU:
// `test_alarm_hijyeni_v192::test_bastirma_sayaci_PANOYA_cikar` "sayacın DIŞ okuyucusu api.py'dir"
// diyordu — yani sayı UCA çıkıyordu ama hiçbir yüzey onu çizmiyordu (YASA 6 boşluğu; "üretiliyor ama
// görünmüyor" kovası, F1/F2/F14 ile aynı sınıf). Bu kart o defteri TAKSONOMİ olarak açar ve UÇTAN
// OKUR (uydurma rakam yasağı): her satır bir mekanizma (arıza sınıfı), üç sayı bir arada.
// NEDEN BASTIRMA GÖRÜNMELİ (üretici beyanı): "bugün 1 alarm" ile "1 alarm + 111 bastırıldı" ekranda
// aynı şeye benzerse tavanın kendisi bir sonraki turun gizli arızası olur. ASKIDA ≠ BASTIRILAN:
// askıda alarm hiç üretmeyen MEŞRU bir beklemedir (hermes kota soğuması / kimlik havuzu), bastırma
// ise üretilecek alarmın günlük tavanla susturulmasıdır — ikisi AYRI kovada sayılır, ayrı yazılır.
// RENK YOK: taksonomi bir ŞİDDET DEĞİL bir SAYIMdır (D1 — renk yalnız anomalide); bastırma çok
// olduğunda dikkat özet ROZETİYLE (kapağı açan `data-dikkat`) taşınır, satır mürekkebiyle DEĞİL.
function firsatAlarmTaksonomi(ag) {
  const a = ag && typeof ag === "object" ? ag : null;
  const bosDefter = a != null && String(a.durum == null ? "" : a.durum) === "defter_yok";
  const mek = a && a.mekanizmalar && typeof a.mekanizmalar === "object" ? a.mekanizmalar : {};
  // SIRA: en gürültülü mekanizma ÜSTTE (alarm + bastırılan toplamı) — taksonominin işi KÖKÜ
  // göstermek; alfabetik sıra kökü listenin ortasına gömerdi. `gurultu` sayı-güvenli (ölçülemeyen
  // hücreyi sıralamada 0 sayar; DÜŞÜMDE değil — display trn ile üçüncü hâli korur).
  const gurultu = m => { const al = Number((m || {}).alarm), ba = Number((m || {}).bastirilan);
    return (Number.isFinite(al) ? al : 0) + (Number.isFinite(ba) ? ba : 0); };
  const adlar = Object.keys(mek).sort((x, y) => gurultu(mek[y]) - gurultu(mek[x]));
  const nAlarm = a ? a.n_alarm : null;
  const nBast  = a ? a.n_bastirilan : null;
  const nAsk   = a && a.n_askida != null ? a.n_askida : null;
  const tavan  = a && a.tavan != null ? a.tavan : null;
  const ozet = !a
    ? kartOzeti({ deger: null, rozet: "ÖLÇÜLEMEDİ",
        meta: "teşhis ucu `watchdog.alarm_gunluk` bloğunu vermedi — alarm taksonomisi bu turda ÖLÇÜLEMEDİ (0 alarm DEĞİL)." })
    : (bosDefter
      ? kartOzeti({ deger: null, rozet: "DEFTER YAZILMADI",
          meta: String(a.beyan == null ? "bugün hiç mekanizma-gecikme alarmı üretilmedi (defter yazılmadı) — '0 alarm' DEĞİL, 'defter yok'." : a.beyan) })
      : kartOzeti({ deger: nAlarm == null ? null : trn(nAlarm),
          meta: `${trn(adlar.length)} mekanizma${nBast == null ? "" : ` · <b>${trn(nBast)}</b> bastırıldı`}${
            nAsk == null ? "" : ` · ${trn(nAsk)} askıda`}${tavan == null ? "" : ` · mekanizma başına günlük tavan ${trn(tavan)}`}`,
          rozet: nAlarm == null ? "ÖLÇÜLEMEDİ" : (nBast ? `${trn(nBast)} BASTIRILDI` : "") }));
  // SATIR: sayaçlar UÇTAN gelir ve api hepsini int garantiler; `trn` ölçülen sıfırı "0" (sönük),
  // gerçekten yok olanı "—" basar (uydurma yasağı — `?? 0`/`|| 0` YOK). `mut` yalnız sıfır/boş
  // hücreyi söndürür (renk yalnız anomalide; sıfır bir şiddet değil bir ölçümdür).
  const satir = ad => {
    const m = mek[ad] || {};
    const bast = m.bastirilan, ask = m.askida;
    const neden = ask && m.son_askida_neden != null ? String(m.son_askida_neden) : "";
    return `<div class="trow" style="grid-template-columns:158px 58px 82px 62px 1fr">
      <span class="chain">${esc(ad)}</span>
      <span class="mono-num">${trn(m.alarm)}</span>
      <span class="mono-num${bast ? "" : " mut"}">${trn(bast)}</span>
      <span class="mono-num${ask ? "" : " mut"}">${trn(ask)}</span>
      <span class="hint" style="margin:0">${neden ? esc(neden) : ""}</span></div>`;
  };
  return `<div class="card rise"${katKart("operasyon:alarmkok")}>
    <h2 class="t">Alarm taksonomisi · yinelenen arızanın kökü <span class="tx3" style="font-weight:400">(hangi mekanizma bağırıyor · ne kadarı bastırıldı?)</span></h2>
    ${ozet}
    ${!a ? firsatBos("teşhis ucu `watchdog.alarm_gunluk` bloğunu vermedi — alarm taksonomisi ölçülemedi.",
        "Bu defterin dış okuyucusu tek uçtur (`/api/diagnostics` watchdog.alarm_gunluk); uç düştüyse taksonomi türetilemez.")
      : (bosDefter
        ? firsatBos(String(a.beyan == null ? "bugün mekanizma-gecikme alarm defteri yazılmadı" : a.beyan),
            "Bu bir ÖLÇÜMdür: defter bugün hiç yazılmadı — '0 alarm' ile 'defter yok' aynı kovaya düşmez (üçüncü hâl).")
        : (!adlar.length
          ? firsatBos("defter dolu okundu ama mekanizma satırı yok — bu turda taksonomi kümelenemedi.",
              "Sayaç bugün bir mekanizmayı hiç damgalamadı; küme boş, ama bu bir ÖLÇÜM (defter var).")
          : `<p class="hint" style="margin-top:0">Her satır bir mekanizma (arıza sınıfı), en gürültülü üstte.
               <b>ALARM</b> üretilen · <b>BASTIRILDI</b> günlük tavana takılıp susturulan (SESSİZ DEĞİL,
               sayılı) · <b>ASKIDA</b> alarm hiç üretmeyen MEŞRU bekleme (hermes kota soğuması / kimlik
               havuzu). Bastırma ile askıda AYRI kovadır; ikisi karışırsa hijyen ile körlük ayırt edilemez.</p>
             <div class="tbl" style="margin-top:10px">
               <div class="trow head" style="grid-template-columns:158px 58px 82px 62px 1fr">
                 <span>MEKANİZMA</span><span>ALARM</span><span>BASTIRILDI</span><span>ASKIDA</span><span>SON ASKIDA NEDENİ</span></div>
               ${adlar.map(satir).join("")}</div>
             <p class="hint" style="margin-top:10px">Toplam <b>${trn(nAlarm)}</b> alarm${
               nBast ? ` · <b>${trn(nBast)}</b> bastırıldı` : " · bastırma yok"}${
               nAsk ? ` · ${trn(nAsk)} askıda` : ""}. Bastırma tavanı mekanizma BAŞINADIR (küresel değil):
               bir mekanizmanın çırpınması diğerini susturmaz. $ ya da ham defter satırı bu karttan DIŞARI
               VERİLMEZ; taksonomi yalnız sayımdır.</p>`))}</div>`;
}

// ---- PORTFÖY · MUTABAKAT MASASI (ADR: "dolum akışı/mutabakat … reddedilen emirler") ----------
// Emirlerin AYNASI kitabın yanında durur: "iç defterim brokerinkiyle aynı mı?" sorusu, "kitap
// nerede?" sorusunun ayrılmaz parçasıdır. Gözetim'de dururken operatör sapmayı ancak alarm
// sayfasına giderek görüyordu — yani pozisyonlara bakarken aynanın hâlini bilmiyordu.
// ==============================================================================================
// KORUMANIN YENİDEN KURULMASI (v211) — ÖNERİ KARTI + TURA ÖZEL ONAY KAPISI
// ----------------------------------------------------------------------------------------------
// ÖLÇÜLEN BOŞLUK (canlı A1, 2026-08-07): dört motor pozisyonu broker'da KORUMASIZ, açık emir sıfır.
// `watchdog.koruma_report()` bunu v209'dan beri GÖRÜYOR, panoda üç uç vardı (oku · gir · düzleştir)
// ve "korumayı yeniden kur" YOKTU. Bu kart o boşluğun operatör tarafıdır: sistem ÖNERİR, insan
// ONAYLAR, emir ondan sonra çıkar.
//
// ⚠ KARTIN ASIL İŞİ BİR TUZAĞI GÖRÜNÜR KILMAK. İç defter (portfolio.json) o gün 33/43/64/54 adet
// diyordu, broker 22/22/37/25. Emir BROKER adedini kullanır — çünkü defterin adediyle satış emri
// göndermek ELDE OLMAYAN hisseyi satmaktır ve `shorting_enabled=true` hesapta bu, koruma diye
// açılmış bir AÇIK POZİSYON demektir. Bu ayrışma ekranda görünmezse operatör yanlış sayıyı doğru
// sanar; o yüzden hem satır içinde (`defter …`) hem de tablonun üstünde AÇIKÇA yazılır.
//
// ONAY KALICI DEĞİL, TURA ÖZEL: düğme `oneri_id` taşır — o an ölçülmüş listenin (sembol/adet/stop/
// hedef) özeti. Sunucu icra anında listeyi YENİDEN ölçer ve özet tutmazsa emir GÖNDERMEZ. Yani bir
// onay yalnız GÖRÜLEN dünyayı kapsar; ekranda dört satır varken beşinci doğduysa onay düşer.
// Kalıcı bir "koruma otomatik kurulsun" anahtarı BİLEREK yoktur: o anahtar, ilk gün verilen onayı
// yarının bilinmeyen defterine uygulardı.
let _KORUMA_SON = null;      // en son ÇİZİLEN öneri yükü — onay diyaloğu ekrandakini okur, ağı değil
let _KORUMA_MSG = "";        // sonuç satırı: `_ALP_MSG` deseni (yeniden çizim onu SİLMEZ)
// Onay jetonu SUNUCUDA da tanımlı (`alpaca.KORUMA_ONAY_JETONU`) ve KASITLI olarak bir sır DEĞİL:
// işi sırrı korumak değil, KAZAYI önlemek — jetonsuz bir çağrı kuru koşudur, hiçbir şeye dokunmaz
// (`close_all`ın CLOSE_ALL_CONFIRM deseni). Gerçek yetki kapısı `_auth` + `oneri_id` eşleşmesidir.
const KORUMA_ONAY_JETONU = "KORUMA-KUR";
function korumaMsgYaz(html) {
  _KORUMA_MSG = html || "";
  const m = $("koruma-msg");
  if (m) m.innerHTML = _KORUMA_MSG;
}
// Bir öneri satırı. STOP VE HEDEF NÖTR: bir fiyat SEVİYESİ bir sonuç değildir (D1 · T5), koşulsuz
// kırmızı/yeşil taşıyamaz. Renk yalnız iki yerde doğar ve ikisi de anomali: adet ayrışması ve
// "gönderilmez" gerekçesi.
function korumaSatirHTML(s) {
  const adet = s.broker_adet == null ? '<span class="pm-none">ölçülemedi</span>'
    : `<b class="mono-num">${trn(s.broker_adet)}</b>`;
  const defter = s.defter_adet == null
    ? '<span class="tx3">defter: kayıt yok</span>'
    : (s.adet_ayrisik ? `<span class="tx3 warn">defter ${trn(s.defter_adet)} ✗</span>`
                      : `<span class="tx3">defter ${trn(s.defter_adet)}</span>`);
  const say = (v, d = 2) => v == null ? '<span class="pm-none">—</span>'
    : `<span class="mono-num">${trn(v, d)}</span>`;
  const uz = s.stop_uzakligi == null ? '<span class="pm-none">ölçülemedi</span>'
    : `<span class="mono-num">${pctf(s.stop_uzakligi, 1)}</span>`;
  const durum = s.gonderilir
    ? '<span class="tx3">gönderilecek</span>'
    : `<span class="tx3 warn">${esc(s.neden || "gerekçe bildirilmedi")}</span>`;
  return `<div class="trow" style="grid-template-columns:62px 108px 76px 76px 76px 84px">
      <span class="tick">${esc(s.ticker)}</span>
      <span>${adet} ${defter}</span>
      ${say(s.stop)}${say(s.hedef)}${say(s.son_fiyat)}${uz}
    </div><div class="trow" style="grid-template-columns:1fr">${durum}</div>`;
}
function korumaKurmaKarti(k) {
  const bas = ozet => `<div class="card rise"${katKart("mutabakat:koruma")}><h2 class="t">Koruma · çıplak pozisyonlar
    <span class="tx3" style="font-weight:400">(OCO önerisi — onay operatörde)</span></h2>${ozet}`;
  // ÖLÇÜLEMEDİ ≠ 0 — iki ayrı dal, iki ayrı cümle. "0 çıplak pozisyon" ile "broker okunamadı"
  // aynı piksele düşerse sessiz bir arıza temizlik diye okunur (koruma_report'un 3. sözleşmesi).
  if (!k || k.olculemedi || k.ok == null) {
    const neden = (k && k.neden) || "uç yanıt vermedi (/api/alpaca/koruma)";
    return `${bas(kartOzeti({ deger: null, rozet: "ÖLÇÜLEMEDİ",
      meta: `Broker durumu okunamadı — açık pozisyonların koruma hâli BİLİNMİYOR ("korumasız 0" DEĞİL). ${esc(neden)}` }))}
      <p class="hint"><span class="mut">Koruma durumu <b>ölçülemedi</b>; bu "korumasız pozisyon yok"
        demek değildir. Gerekçe: ${esc(neden)}</span></p>
      <p class="hint">Ölçüm dönmeden hiçbir emir üretilmez — ölçemediğimiz bir dünyaya emir
        göndermek, koruma kurduğumuzu <b>sanmak</b> olurdu.</p></div>`;
  }
  // `|| 0` YOK (v196 triyajının sınıfı): "uç bu alanı vermedi" ile "ölçtük, sıfır çıktı" aynı
  // piksele düşemez — hele bu kartta: "0 korumasız" bir güvence cümlesidir ve uydurulamaz.
  // Üç sayının biri bile okunamıyorsa kart ÖLÇÜLEMEDİ dalına düşer.
  const say = v => Number.isFinite(Number(v)) ? Number(v) : null;
  const n = say(k.korumasiz), t = say(k.toplam), g = say(k.gonderilebilir);
  if (n == null || t == null || g == null) {
    return `${bas(kartOzeti({ deger: null, rozet: "ÖLÇÜLEMEDİ",
      meta: "Uç sayıları eksik verdi (korumasız/toplam/öneri) — koruma durumu ölçülemedi; bu \"korumasız 0\" DEĞİL." }))}
      <p class="hint"><span class="mut">Uç <code>/api/alpaca/koruma</code> sayıları eksik döndürdü;
        pano eksik alanı sıfıra çevirmez.</span></p></div>`;
  }
  const oran = (t > 0 && k.payda_beyani) ? Math.max(0, Math.min(1, n / t)) : null;
  const ozet = kartOzeti({
    deger: `${trn(n)} / ${trn(t)}`,
    degerSinif: n > 0 ? "warn" : "",
    oran, payda: k.payda_beyani || "",
    meta: `${trn(t)} motor pozisyonu · ${trn(n)} korumasız · ${trn(g)} öneri hazır`,
    rozet: g > 0 ? "ONAY BEKLİYOR" : "",
  });
  const satirlar = (k.satirlar || []);
  const disi = (k.motor_disi_satirlar || []);
  const ayrisik = satirlar.filter(s => s.adet_ayrisik);
  const head = `<div class="trow head" style="grid-template-columns:62px 108px 76px 76px 76px 84px">
      <span>HİSSE</span><span>SAT ADET</span><span>STOP</span><span>HEDEF</span><span>SON</span>
      <span>STOPA UZAKLIK</span></div>`;
  return `${bas(ozet)}
    <p class="hint" style="margin-top:0">Broker'da <b>canlı koruyucu stop'u olmayan</b> motor
      pozisyonları. Emir <b>tek OCO</b> olarak gider (stop + hedef birbirine bağlı): bağsız iki emir
      gönderilse hedef dolduktan sonra stop canlı kalır ve tetiklendiğinde <b>açığa satış</b> açardı —
      korumasızlıktan <i>farklı</i> ve daha kötü bir risk. TIF <code>gtc</code> (E1-v2): <code>day</code>
      bacakları her kapanışta öldüren kök nedendi.</p>
    ${ayrisik.length ? `<p class="hint sev-1"><b>ADET AYRIŞMASI —
      ${trn(ayrisik.length)} sembol:</b> iç defter ile broker farklı adet söylüyor
      (${esc(ayrisik.map(s => `${s.ticker} defter ${trn(s.defter_adet)} ↔ broker ${trn(s.broker_adet)}`).join(" · "))}).
      Emir <b>BROKER</b> adedini kullanır — defterin fazla adediyle satmak elde olmayan hisseyi
      satmak, yani açık pozisyon açmak olurdu.</p>` : `<p class="hint"><span class="mut">Adet kaynağı:
      <b>broker</b> (<code>alpaca.positions</code>). İç defter yalnız görünürlük için gösterilir.</span></p>`}
    ${satirlar.length ? `<div class="tbl" style="margin-top:8px">${head}${satirlar.map(korumaSatirHTML).join("")}</div>`
      : `<p class="hint"><span class="mut">Motor pozisyonu yok — payda 0, öneri de yok.</span></p>`}
    ${disi.length ? `<p class="hint" style="margin-top:8px"><span class="mut">Motor-DIŞI pozisyon
      (${esc(disi.map(s => `${s.ticker} ${trn(s.broker_adet)}`).join(" · "))}): operatörün kendi emri.
      Görünür, ama bu yol onlara <b>asla</b> emir üretmez — A3 sahiplik sınırı.</span></p>` : ""}
    <div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:12px;align-items:center">
      ${g > 0 ? `<button class="dlbtn" type="button" data-act="korumaKur"
        data-a1="${esc(k.oneri_id || "")}">▲ Korumayı kur — ${trn(g)} OCO (onay iste)</button>`
        : `<span class="hint" style="margin:0">Gönderilecek öneri yok.</span>`}
      <span class="hint" id="koruma-msg" style="margin:0">${_KORUMA_MSG}</span></div>
    <p class="hint" style="margin-top:8px"><span class="mut">Onay <b>bu listeye</b> verilir
      (kimlik <code>${esc(k.oneri_id || "—")}</code>), kalıcı bir anahtara değil. Sunucu gönderim
      anında listeyi yeniden ölçer; ekrandaki tablo o an değişmişse emir <b>gitmez</b> ve tazeleme
      istenir. Aynı sembolde canlı koruma varsa emir üretilmez (idempotans), mevcut bir stop varsa
      öneri yalnız <b>yukarı</b> taşıyabilir (A4).</span></p></div>`;
}
// TURA ÖZEL ONAY — iki kapı: insan diyaloğu + sunucudaki kimlik eşleşmesi.
// Diyalog EKRANDAKİ yükü okur (`_KORUMA_SON`), ağı yeniden sormaz: operatörün onayladığı şey
// gördüğü şey olmalı. Sunucu ayrıca kendi ölçümüyle karşılaştırır — ikisi ayrışırsa emir gitmez.
window.korumaKur = async (oneriId) => {
  const k = _KORUMA_SON;
  const sat = ((k && k.satirlar) || []).filter(s => s.gonderilir);
  if (!sat.length) { korumaMsgYaz('<span class="warn">gönderilecek öneri kalmadı — listeyi tazele</span>'); return; }
  const dokum = sat.map(s => `  ${s.ticker}  SAT ${s.broker_adet} adet  ·  stop ${s.stop}  ·  hedef ${s.hedef}`
    + (s.adet_ayrisik ? `   [defter ${s.defter_adet} diyor — BROKER adedi kullanılıyor]` : "")).join("\n");
  if (!confirm(`KORUMAYI KUR — ${sat.length} adet OCO emri (stop + hedef, birbirine bağlı)\n\n`
    + `${dokum}\n\nAdet BROKER'dan alınır (iç defterden değil). TIF gtc.\n`
    + `Onay yalnız BU listeye verilir; liste değiştiyse emir gönderilmez.`)) return;
  const _btn = () => document.querySelector('[data-act="korumaKur"]');
  const b0 = _btn(); const etiket = b0 ? b0.textContent : "";
  if (b0) { b0.disabled = true; b0.textContent = "gönderiliyor…"; }
  korumaMsgYaz("gönderiliyor…");
  try {
    const r = await apiFetch("/api/alpaca/koruma_kur", {
      method: "POST", headers: { "content-type": "application/json" },
      body: JSON.stringify({ onay: KORUMA_ONAY_JETONU, oneri_id: oneriId || (k && k.oneri_id) || "" }),
    });
    let body = {};
    try { body = await r.json(); }
    catch (e) { body = {}; }   // YASA 4 · işaretli yutma: 2xx gövdesi JSON değil; aşağıdaki satır "ölçülemedi" der, "gönderildi" DEMEZ
    korumaMsgYaz(_korumaSonucSatiri(body));
    await _aktifSayfayiCiz();
  } catch (e) {
    // İKİ HÂL AYRIŞTIRILIR (v219): sunucu CEVAP VERDİYSE (`e.status` var) reddin gerekçesi
    // bilinir ve "emirler gitmiş olabilir" cümlesi kurulmaz — o cümle uydurma olurdu. Yalnız
    // AĞ koptuğunda (durum kodu YOK) sonuç gerçekten ölçülemez ve belirsizlik yazılır.
    korumaMsgYaz(e && e.status
      ? `<span class="neg">✗ ${esc(String(e.message))}</span> — sunucu REDDETTİ; emir gönderilmedi`
      : `<span class="neg">✗ ${esc(String((e && e.message) || e))}</span> — sonuç ÖLÇÜLEMEDİ;
         emirler gitmiş olabilir, kartı tazeleyip koruma durumunu doğrula`);
  } finally {
    const b = _btn();
    if (b && b.disabled) { b.disabled = false; b.textContent = etiket || "▲ Korumayı kur"; }
  }
};
// KISMİ BAŞARI DÜRÜST YAZILIR: "2/4 gönderildi + 2 neden" der, "tamam" DEMEZ. Tek bir "gönderildi"
// cümlesi, hâlâ çıplak duran iki pozisyonu ekrandan silerdi.
function _korumaSonucSatiri(r) {
  if (r.dry_run) return `<span class="warn">onaysız çağrı — hiçbir emir gönderilmedi</span>`;
  if (r.bayat_onay) return `<span class="warn">${esc(r.detail || "öneri değişti — emir gönderilmedi")}</span>`;
  if (r.olculemedi) return `<span class="warn">${esc(r.detail || "ölçülemedi — emir gönderilmedi")}</span>`;
  const sat = Array.isArray(r.satirlar) ? r.satirlar : [];
  const dusen = sat.filter(x => x && !x.ok);
  const bas = r.gonderilen == null
    ? `<span class="warn">gönderim sayısı ölçülemedi — uç <code>gonderilen</code> alanını vermedi (0 DEĞİL)</span>`
    : `${r.gonderilen ? '<span class="pos">✓</span> ' : ""}${trn(r.gonderilen)}/${trn(r.toplam)} koruma gönderildi`;
  // TERNARY, `if (…) return` DEĞİL — ve bu bir üslup tercihi değil bir ÖLÇÜM sözleşmesi: renk-rolü
  // tarayıcısı (`research/olcumler/renk_rolleri_2026-08-07/tara_emisyon.py`) bir emisyonun anomali
  // dalında olduğunu geriye yürüyerek anlar ve erken-çıkışlı bir `return` deseninde kapıyı
  // GÖREMEZ; koşullu bir renk KOŞULSUZ sayılır ve tavan-0 kuralı boşuna kırmızıya döner.
  return dusen.length
    ? `${bas} · <span class="neg">${trn(dusen.length)} gönderilemedi (pozisyon ÇIPLAK): ${
        esc(dusen.map(x => `${x.ticker || "?"} — ${String(x.detail || "gerekçe bildirilmedi")}`).join(" · ").slice(0, 240))}</span>`
    : bas;
}

RENDER.mutabakat = async () => {
  // İKİ UÇ PARALEL: koruma ölçümü BROKER'a çıkar (`/api/alpaca/koruma` → positions+orders) ve
  // ölçüm 1-1,5 sn sürebilir; `opParcalar()`ın arkasına zincirlenseydi masanın tamamı onu
  // beklerdi. Ölçüm DÜŞERSE kart kaybolmaz — `null` gelir ve kart "ÖLÇÜLEMEDİ + neden" dalını
  // çizer. Sessizce kaybolan bir risk kartı, kartın hiç olmamasından beterdir: operatör
  // "korumasız pozisyon yok" sanır.
  const [p, kor] = await Promise.all([
    opParcalar(),
    j("/api/alpaca/koruma").catch(() => null),
  ]);
  _KORUMA_SON = kor;
  $("page-mutabakat").innerHTML = bolumBasHTML("mutabakat", "Mutabakat masası",
    "Broker API'si, yürütme akışı, hayalet emirler, HWM ikizleri, parçalı dolum, reddedilen "
    + "gönderimler ve kapıda düşen silahlı planlar. Sessiz hattın <b>emir reddedildi</b> çipi "
    + "buraya iner. Altında <b>E2 icra gerçekliği</b> (ret sınıfı, dolumun bps faturası, iç "
    + "motorun kill ölçütü, iki motorun mutabakatı), <b>E3 kötümser band</b> (yürürlükteki "
    + "varsayım + defterden ampirik ölçüm) ve <b>E4 gece/gündüz</b> (kâr hangi bacaktan geldi).")
    // KORUMA KARTI EN BAŞTA (v211): masanın öteki kartları "ne oldu?" diye sorar; bu kart
    // "şu anda korumasız param var mı, ve düzeltmek için neye basmalıyım?" diye sorar. Açık bir
    // riskin cevabı, geçmişin muhasebesinin ALTINDA duramaz.
    + korumaKurmaKarti(kor)
    // EMİR YAŞAM-DÖNGÜSÜ MASANIN HEMEN ARDINDA (C1-2): `s1` "iç defterim brokerinkiyle aynı mı?"
    // der; bu kart "benim onayım hangi emre döndü ve KAÇA doldu?" der. İkincisi birincisinin
    // satır düzeyidir — araya E2/E3/E4 girseydi soru iki kaydırma uzağa düşerdi.
    + p.s1 + firsatEmirYasam((_DIAG || {}).reconcile) + p.sIcra + p.sBand + p.sGeceG;
};

// ---- KOŞU & DÖNGÜ · KAPILAR (ADR: "kapıdan ne geçti") ----------------------------------------
// Karar ağacı matrisi bir teşhis kartı değil, gecenin KARARININ gerekçesi. Adayların hemen
// altında durunca "neden bu geçti, şu elendi" tek kaydırmada okunur.
RENDER.kapilar = async () => {
  const p = await opParcalar();
  // TEŞHİS YÜKÜ ZATEN ELDE: `opParcalar()` onu AZ ÖNCE okudu ve `_DIAG`e yazdı. İkinci bir
  // `j("/api/diagnostics")` çağrısı JCACHE sayesinde ağa çıkmazdı ama yine de aynı yanıtın iki
  // kopyasını taşırdı — ve iki kopya, ilk düzenlemede ayrışır (bu deponun tekrar eden kusuru).
  const d = _DIAG;
  $("page-kapilar").innerHTML = bolumBasHTML("kapilar", "Disiplin kapısı · karar ağacı",
    "Rejim bütçesi, karartma radarı, uyuyan kurulumların silahlanma ölçümü ve plan başına "
    + "karar ağacı. Her satır açılır: hangi ölçüt hangi değerle hangi eşiğe çarptı. Altında "
    + "kapının <b>reddettiklerinin karnesi</b> ve <b>bugün neden hiçbir şey olmadığı</b>.") + p.s2
    // SIRA: önce eylemsizlik (bugünün sorusu), sonra ret karnesi (eşiğin sorusu). Operatör
    // sayfaya "bugün ne oldu?" diye gelir; "eşiğim doğru mu?" ikinci sıradaki sorudur.
    + firsatEylemsizlik((d || {}).risk) + firsatRetKarnesi((d || {}).mlops);
};

// ---- VERİ SAĞLIĞI · HATTIN İÇ SAĞLIĞI --------------------------------------------------------
// ADR Veri Sağlığı: "kapsama/tazelik/karantina/bütünlük + intraday akış durumu". Karantina,
// bütünlük dedektörleri, defter sözleşmesi, eleme muhasebesi, sıcak katman ve sağlayıcılar —
// hepsi "baktığım veri sağlam mı?" sorusunun cevabı ve hiçbiri "sistem sağlıklı mı?" değil.
RENDER.veriboru = async () => {
  const p = await opParcalar();
  // F1 · kâğıt-canlı ayrımı KİMLİK-DOĞRULAMASIZ uçtan gelir (landing ile aynı sayı; ayrı ve dar
  // uç, DASH_TOKEN'dan bağımsız). Arkadan okunur — düşerse kart "ölçülemedi + neden" der (YASA 4).
  const ps = await j("/api/public/summary").catch(() => null);
  $("page-veriboru").innerHTML = bolumBasHTML("veriboru", "Veri hattı · karantina · bütünlük",
    "Hattın kendi sağlığı: canlı/tohum defter ayrımı, karantina odası, yedi bütünlük deseni, defter "
    + "sözleşmesi, eleme muhasebesi, Redis sıcak katmanı ve sağlayıcı adaptörleri.")
    + firsatKagitCanli(ps)
    + p.s4 + p.s5 + p.s6 + p.sSag
    // ---- DETAY KATMANINA İNDİ (S2R-2 "soruya hizmet" denetimi) --------------------------------
    // Bu kart Faz-4a gözleminin ÖZETİdir ve ayrıntısı artık Portföy'ün `intraemir` bölümünde
    // TAM hâliyle duruyor. "Aynı soruya iki yerden cevap" tam olarak operatörün şikâyetiydi.
    // SİLİNMEDİ: `barfeed.running`, `intraday.armed_plans` ve `intraday.decisions.today`
    // alanlarının TEK okuyucusu bu özet — ayrıntı kartı o üçünü okumuyor (o `watched`,
    // `events_handled`, `decisions.total/recent` okuyor). Silmek üç alanı öksüz bırakırdı.
    + detayKatmani("Intraday · Faz 4a gözlem özeti",
        "Ayrıntısı Portföy & Emirler → seans-içi silahlanma bölümünde. Burada kalma sebebi: "
        + "barfeed.running / armed_plans / decisions.today alanlarının tek okuyucusu bu özet.",
        p.sIntra);
};

// ---- ÖĞRENME · BİLEŞEN-IC (+EB) VE KENAR ÖLÇÜMLERİ -------------------------------------------
// ADR Öğrenme: "karne, gölge kollar, bileşen-IC+EB, hipotez/sprint, K-defteri". Kenar ölçümleri
// (beş ölçüt + bileşen IC + EB ikizi + dolar merceği + doğrulama üçlüsü + rejim/risk dörtlüsü +
// kâr şelalesi + sistem önerileri) "makine ne öğreniyor?" sorusunun sayısal cevabıdır; Operasyon
// sayfasında dururken hiç kimse onları öğrenme kanıtı olarak okumuyordu.
RENDER.bilesenic = async () => {
  const p = await opParcalar();               // _DIAG'ı da doldurur (F2 `icra.slipaj`ı oradan okur)
  $("page-bilesenic").innerHTML = bolumBasHTML("bilesenic", "Kenar ölçümleri · bileşen IC + EB",
    "Skor→sonuç IC'si, SPY-üstü, tahmin isabeti, rejim başına kenar, kuyruk riski; skorun dört "
    + "ham parçası ve empirik-Bayes ikizi; dolar merceği, doğrulama üçlüsü, kâr şelalesi ve "
    + "canlı-backtest sapmasının kökü (E1/E2 hattı).")
    // F2 · sEdge→sSonuc (hüküm ikizi) BİTİŞİK KALIR (v102 çivisi); sapma kökü sonuç hükmünden SONRA
    // okunur — "kenar gerçek mi?"nin ardından "canlı ödeme neden geri-testten sapıyor?".
    + p.sEdge + p.sSonuc + firsatSapmaKoku(((_DIAG || {}).icra || {}).slipaj) + p.sSelale + p.sDogrulama + p.sY3;
};

// ---- ÖĞRENME · GÖLGE KOLLAR ------------------------------------------------------------------
// ADR: "gölge kollar (küçük-katlar hedefi)". Canlı gölge-kitap kâğıt üstünde koşar ve canlı
// deftere DOKUNMAZ; hükmü verilmiş bir kolun ölçülen birikimidir.
//
// S2R-3'TE BÖLÜM TAMAMLANDI: gölge-VARYANT portföyleri Hermes karnesi kartının alt başlığı
// olmaktan çıkarıldı ve buraya indi (`sGolgeVaryant`). Artık bölümün soru cümlesi ("kâğıt üstünde
// koşan gölge kollar ne veriyor?") İKİ kolun ikisini de kapsıyor ve altyazı okuru başka bir
// sayfaya yönlendirmiyor — S2R-2'nin beyanlı borcu kapandı.
//
// SIRA: canlı gölge-KİTAP önce (hükmü verilmiş TEK kol, gerçek barlar), varyant PORTFÖYLERİ sonra
// (k tane aday kol, çoklu-karşılaştırma paydasıyla). Hüküm verilmiş olan, aday olanın üstündedir.
RENDER.golge = async () => {
  const p = await opParcalar();
  $("page-golge").innerHTML = bolumBasHTML("golge", "Gölge kollar · kâğıt defter",
    "İki kâğıt kol: hükmü verilmiş trend kolunun canlı gölge-kitabı ve k adet varyant portföyü. "
    + "İkisi de kâğıt üstünde koşar, canlı sermayeye dokunmaz — emir yolu import bile edilmez.")
    + p.sTrend + p.sGolgeVaryant;
};

// 5.3 — seans-içi bar akışındaki eksik dakika pencereleri. Ölçümü zamanlayıcı kancası yapar; burası
// yalnız okur. "—" (ölçüm yok) ile "0 boşluk" (ölçüldü, temiz) BİLEREK farklı cümlelerdir.
// ---- HÜKÜM HARİTASI: BİLİNMEYEN DURUM YEŞİL DOĞAMAZ (WP-D eki, 2026-08-02) -------------------
// ÖLÇÜLEN KUSUR: `gap_scan` yeni bir `takvim_yok` durumu üretmeye başladı (XNYS takvimi
// konuşmadıysa BEKLENTİ üretilemez, dolayısıyla eksiklik de ÖLÇÜLEMEZ). Bu harita onu tanımıyordu
// ve `_gapRows` bilinmeyen durumu ÖLÇÜLMÜŞ SONUÇ dalına düşürüyordu: `bosluk_sayisi` 0 geldiği
// için satır YEŞİL "boşluk yok · 0 bar / 0 sembol" basıyordu. Yani takvimin sustuğu bir gün,
// sağlıklı bir akış raporu gibi okunuyordu — fonksiyonun kendi üst yorumunun ("bunlar birbirine
// karıştırılırsa pano, ölçülmemiş bir sessizliği 'sağlıklı' diye gösterir") tam olarak yasakladığı
// sınıf, ve bekçi ÖLÇÜLEMEDİ yüzeyiyle (S2R-3 · C21/C22) aynı kusur.
//
// HÜKÜM: (a) `takvim_yok` haritaya girdi; (b) haritadaki her hâl artık kendi ÇİPİNİ taşıyor ve
// hepsi `t-vi` (bu panonun "ölçüm yok / hüküm yok" kanalı — yeni renk İCAT EDİLMEDİ);
// (c) BİLİNMEYEN bir durum artık ölçülmüş sayılmaz: ham adıyla, nötr çiple, "hüküm verilmedi"
// diye basılır. Varsayılanın yeşil olması, üreticinin yarın ekleyeceği her yeni hâli
// SAHTE-SAĞLIKLI doğurur — ve o hata sessizdir.
// Çip sözcüğü de hükmün parçası: "ÖLÇEMEDİM" ile "ÖLÇÜLECEK BİR ŞEY YOKTU" aynı şey değildir.
// Seans dışı bir dakikada eksik bar aramak anlamsızdır (hüküm yok); takvim susmuşsa aranacak
// şey VARDI ama ölçülemedi. İkisi de nötr, ikisi de farklı KELİME — çift kodlama (Ç7).
const _GAP_DURUM = {
  seans_disi: ["seans dışı — o gün/o saatte beklenen bar YOK, aranacak boşluk da yok (alarm değil)",
               "HÜKÜM YOK"],
  takvim_yok: ["takvim okunamadı — boşluk taraması BU TURDA ÖLÇÜLEMEDİ; beklenti üretilemediği "
               + "için eksiklik de ölçülemez. Boş liste \"boşluk yok\" DEĞİL.", "ÖLÇÜLEMEDİ"],
  arsiv_yok: ["seans-içi arşiv açılmamış — ölçülemedi", "ÖLÇÜLEMEDİ"],
  pencerede_bar_yok: ["pencerede TEK bar yok — akış sessiz, hüküm verilmedi", "HÜKÜM YOK"],
  olculemedi: ["tarama düştü — bu turda ÖLÇÜLMEDİ", "ÖLÇÜLEMEDİ"],
};
function _gapRows(g) {
  if (!g) return `<div class="srow"><span>Seans-içi boşluk</span><b class="mut">— · tarama bu süreçte hiç koşmadı</b></div>`;
  if (g.durum !== "ok") {
    const bilinen = Object.prototype.hasOwnProperty.call(_GAP_DURUM, g.durum);
    // Takvim arızasının GEREKÇESİ üreticinin `seans` bloğunda duruyor (durum/takvim/açılış/
    // kapanış/hata). Bugün `scheduler._intraday_gap_check` durum kopyasına o bloğu ALMIYOR, yani
    // alan panoya çoğu zaman hiç ulaşmaz — okuma bu yüzden KORUMALI ve yokluğu bir arıza değil:
    // hüküm zaten `durum`dan geliyor, `seans.hata` yalnız teşhisi kısaltır.
    const se = g.seans || {};
    const ek = [se.takvim ? `takvim ${se.takvim}` : null,
                se.hata ? String(se.hata).slice(0, 90) : null].filter(Boolean).join(" · ");
    const [cumle, cip] = bilinen ? _GAP_DURUM[g.durum]
      : [`bilinmeyen tarama durumu (${g.durum ?? "—"}) — bu turda hüküm VERİLMEDİ`, "ÖLÇÜLEMEDİ"];
    return `<div class="srow"><span>Seans-içi boşluk</span>
      <b class="mut">${esc(cumle)}${ek ? ` · ${esc(ek)}` : ""} ${_chip(cip, "t-vi")}</b></div>`;
  }
  const n = g.bosluk_sayisi, pen = g.pencere || {};
  const satir = (g.bosluklar || []).slice(0, 4).map(b =>
    `<div class="trow" style="grid-template-columns:78px 108px 1fr">
       <span class="tick">${esc(b.sembol || "AKIŞ")}</span>
       <span class="mono-num">${esc(String(b.baslangic).slice(11, 16))}–${esc(String(b.bitis).slice(11, 16))}Z</span>
       <span class="chain mut">${b.eksik_dk} dk eksik · beklenen ${b.beklenen} / gelen ${b.gelen}</span></div>`).join("");
  return `<div class="srow"><span>Seans-içi boşluk <span class="tx3">(son ${pen.beklenen_dk ?? "?"} beklenen dk)</span></span>
      <b class="${n ? "neg" : (n === 0 ? "pos" : "mut")}">${
        n ? `${trn(n)} boşluk · ${trn(g.sembol)} sembol akıyor`
          : (n === 0 ? `boşluk yok · ${trn(g.gelen_bar)} bar / ${trn(g.sembol)} sembol`
                     : "boşluk sayısı ÖLÇÜLMEDİ — bu satır 'boşluk yok' DEMEZ")}</b></div>
    ${satir ? `<div class="tbl" style="margin-top:8px">${satir}</div>` : ""}`;
}

// ==============================================================================================
// S2R-2 · INTRADAY'İN İKİYE BÖLÜNMESİ (ADR: "akış→Veri, emir→Portföy")
// ----------------------------------------------------------------------------------------------
// Eski sayfa beş kart taşıyordu ve ikisi farklı soruya cevap veriyordu:
//   VERİ yarısı  — piyasa-veri akışı (marketstream), dayanıklı tetik (consumer-group), Redis
//                  sıcak katmanı, seans-içi boşluk taraması. Soru: "dakikalık bar akışı canlı mı?"
//   EMİR yarısı  — gözlem/silahlama kipi + ARM düğmesi, tetik-geçişi ölçümleri, gölge icra
//                  kararları ve EOD dolgusuyla kıyas. Soru: "tetiği kesen plana ne olurdu?"
// S2R-1 ikisini de Veri Sağlığı'na almıştı çünkü "sayfanın bugünkü tamamı ölçümdür ve SIFIR emir
// yetkisi vardır" — doğru bir gözlemdi ama YANLIŞ sonuç: ARM düğmesi bir emir kapısını açıyor ve
// gölge icra tam olarak "emir çıkar mıydı"yı ölçüyor. İkisi de kitabın sorusuna aittir.
//
// TEK UÇ, İKİ TÜKETİCİ: ikisi de `/api/diagnostics` okur ve o yanıt 15 sn önbelleklidir (JCACHE),
// yani bölünme ağda İKİNCİ bir istek doğurmaz.
const _INTRA_ALT = "Alpaca dakikalık kapanmış barlar → Redis akışı → dayanıklı tetik. Karar hattı "
  + "EOD kalır; burada yalnız veri akışının kendisi ölçülür.";
async function intraParcalar() {
  const d = await j("/api/diagnostics");
  const iq = d.intraday || {}, mkt = d.marketstream || {}, bf = d.barfeed || {}, hs = d.hotstate || {};
  const dec = iq.decisions || { total: 0, fired: 0, recent: [] };
  const armed = iq.armed === true, sk = iq.skipped || {};
  const mktOk = mkt.ok === true, mktDown = mkt.ok === false, bfOk = bf.ok === true, hsOk = hs.ok === true;
  const armChip = _chip(armed ? "SİLAHLI ⚠" : "GÖZLEM · SİLAHSIZ", armed ? "t-no" : "t-go");
  // ---- 1) Intraday gözlem durumu + arm toggle ----
  const s1 = `<div class="card rise"><h2 class="t">Intraday gözlem <span class="tx3" style="font-weight:400">(kapanmış-bar tüketicisi)</span> ${armChip}</h2>
    <div class="srow"><span>Mod</span><b class="${armed ? "neg" : "pos"}">${armed ? "SİLAHLI — otonom intraday emir kapısı AÇIK" : "gözlem-modu · yalnız ölçüm, emir YOK"}</b></div>
    <div class="srow"><span>İzlenen sembol / işlenen olay</span><b>${iq.watched ?? 0} sembol · ${iq.events_handled ?? 0} olay</b></div>
    <div class="srow"><span>Yazılan ölçüm / tetik-geçişi</span><b>${iq.decisions_written ?? 0} ölçüm · ${dec.fired ?? 0} geçiş · ${iq.shadow_written ?? 0} gölge kararı</b></div>
    ${(sk.session || sk.halt || sk.stale || sk.no_bars) ? `<div class="srow"><span>Atlanan</span><b class="mut">seans ${sk.session || 0} · halt ${sk.halt || 0} · bayat ${sk.stale || 0} · bar-yok ${sk.no_bars || 0}</b></div>` : ""}
    ${iq.last_error ? `<div class="srow"><span>Son hata</span><b class="neg">${esc(iq.last_error)}</b></div>` : ""}
    <div style="display:flex;gap:10px;flex-wrap:wrap;margin-top:12px;align-items:center">
      <button class="dlbtn" data-act="intradayArm" data-a1="${armed ? "false" : "true"}">${armed ? "■ Silahlamayı KAPAT (gözleme dön)" : "Intraday silahlamayı AÇ"}</button>
      <span class="hint" id="intraday-arm-msg" style="margin:0"></span></div>
    <p class="hint" style="margin-top:10px">Gözlem-modu (Faz 4a) canlı dakikalık <b>kapanmış</b> barlarda EOD-silahlı planların tetik-geçişini ÖLÇER ve
    <code>intraday_decisions.jsonl</code>'e yazar — <b>emir göndermez, iç deftere dokunmaz</b> (sıfır yetki). Gerçek intraday
    silahlanma (Faz 4b) yalnız bu bayrak + EOD ile aynı güvenlik kapılarıyla açılır ve <b>henüz uygulanmadı</b> — bayrağı
    açmak şu an yalnız hazırlıktır (emir çıkmaz).</p></div>`;
  // ---- 2) Son intraday ölçümleri ----
  const rows = (dec.recent || []).map(r => `<div class="trow" style="grid-template-columns:70px 1fr 90px 74px">
    <span class="tick">${esc(r.ticker || "?")}</span>
    <span class="chain mut">${esc((r.bar_t || "").slice(11, 16))} UTC · ${r.admissible_bars ?? 0} bar${r.last_close != null ? " · $" + trn(r.last_close, 2) : ""}</span>
    <span class="mono-num">${r.entry_trigger != null ? "eşik " + trn(r.entry_trigger, 2) : "—"}</span>
    ${_chip(r.fired === true ? "GEÇTİ" : (r.fired === false ? "bekliyor" : "—"), r.fired === true ? "t-go" : "t-vi")}</div>`).join("");
  const s2 = `<div class="card rise"><h2 class="t">Son intraday ölçümleri · ${dec.total ?? 0} toplam</h2>
    ${rows ? `<div class="tbl" style="margin-top:10px"><div class="trow head" style="grid-template-columns:70px 1fr 90px 74px"><span>HİSSE</span><span>KAPANMIŞ BAR</span><span>EŞİK</span><span>DURUM</span></div>${rows}</div>`
           : `<p class="hint">Henüz ölçüm yok — seans açıkken izlenen sembollerde (açık pozisyon ∪ EOD-silahlı) tetik-geçişi ölçülünce dolar. Piyasa kapalıysa tüketici doğru şekilde boştadır.</p>`}</div>`;
  // ---- 3) Piyasa-veri akışı (marketstream) ----
  const s3 = `<div class="card rise"><h2 class="t">Piyasa-veri akışı <span class="tx3" style="font-weight:400">(Alpaca → mrd:bars)</span>
      ${_chip(mktOk ? "CANLI" : (mktDown ? "KOPUK" : "—"), mktOk ? "t-go" : (mktDown ? "t-no" : "t-vi"))}</h2>
    <div class="srow"><span>Akış</span><b class="${mktOk ? "pos" : (mktDown ? "neg" : "")}">${mktOk ? "canlı · " + esc(mkt.feed || "iex") + " feed" : (mktDown ? "kopuk — EOD dosyalarına düşülür" : "başlamadı")}</b></div>
    <div class="srow"><span>Akan bar / abone</span><b>${mkt.bars_seen ?? 0} bar · ${mkt.subscribed ?? 0} sembol</b></div>
    ${mkt.last_bar_at ? `<div class="srow"><span>Son kapanmış bar</span><b>${relTime(mkt.last_bar_at)}${mkt.last_bar_age_s > 180 ? ' · <span class="warn">seyrek (piyasa kapalı olabilir)</span>' : ""}</b></div>` : ""}</div>`;
  // ---- 4) Dayanıklı tetik + Redis + SEANS-İÇİ BOŞLUK (5.3) ----
  // Bağlantı YEŞİL olduğu hâlde dakikaların kaybolabildiği bir sınıf var (soket ayakta, abonelik
  // sessiz). `akis_boslugu` o sınıfın tek görünür yüzeyidir. ÜÇ HÂL AYRI OKUNUR — null ("kanca hiç
  // koşmadı"), "seans_disi"/"arsiv_yok" ("bakılamadı") ve ölçülmüş sonuç ("0 boşluk" gerçekten 0).
  // Bunlar birbirine karıştırılırsa pano, ölçülmemiş bir sessizliği "sağlıklı" diye gösterir.
  const s4 = `<div class="card rise"><h2 class="t">Dayanıklı tetik <span class="tx3" style="font-weight:400">(consumer-group)</span>
      ${_chip(bfOk ? "CANLI" : (bf.ok === false ? "KOPUK" : "—"), bfOk ? "t-go" : (bf.ok === false ? "t-no" : "t-vi"))}</h2>
    <div class="srow"><span>Okunan olay / bar</span><b>${bf.events_read ?? 0} olay · ${bf.frames_seen ?? 0} bar</b></div>
    <div class="srow"><span>Bekleyen (lag) / düşen bayat</span><b class="${bf.pending > 50 ? "warn" : ""}">${bf.pending ?? 0} bekleyen · ${bf.stale_dropped ?? 0} düşürüldü</b></div>
    <div class="srow"><span>Tüketici bağlı</span><b class="${bf.has_consumer ? "pos" : "mut"}">${bf.has_consumer ? "evet · intraday_cycle" : "hayır"}</b></div>
    <div class="srow" style="margin-top:8px"><span>Redis sıcak katman</span><b class="${hsOk ? "pos" : (hs.ok === false ? "neg" : "")}">${hsOk ? "bağlı · " + (hs.writes ?? 0) + " yazma" : (hs.ok === false ? "kopuk — dosyaya düşülür" : "—")}</b></div>
    ${_gapRows(iq.akis_boslugu)}</div>`;

  // ---- 5) FAZ 4B GÖLGE: "tetik kesilseydi NE olurdu?" ----
  // Tetik-geçişi tek başına bir karar DEĞİLDİR: kapılar, boyutlandırma ve likidite tavanı emri
  // tümüyle iptal edebilir. Bu kart o farkı gösterir — ve hiçbir satırı "emir verildi" diye
  // okutmaz: başlıkta da satırda da GÖNDERİLMEDİĞİ yazar.
  const sh = iq.shadow || {}, ve = sh.vs_eod || {};
  // Ham durum kodu rozete BASILMAZ: `.tag` uppercase uygular ve tr-TR yerelinde "position_exists"
  // → "POSİTİON_EXİSTS" olur (noktalı İ). Üstelik kod operatörün dili değil; hangi kapının
  // engellediği Türkçe okunur. Bilinmeyen bir kod gelirse ham hâli gösterilir — sessizce yutulmaz.
  const SH_TR = { would_submit: "GÖNDERİLECEKTİ", halt: "HALT", breaker: "DEVRE KESİCİ",
                  data_bad: "VERİ KAPISI", size_mult: "BOYUT SIFIR", position_exists: "POZİSYON VAR",
                  max_open: "SLOT DOLU", broker_kurali: "BROKER KURALI",
                  breaker_olculemedi: "KESİCİ ÖLÇÜLEMEDİ", data_bad_olculemedi: "VERİ ÖLÇÜLEMEDİ" };
  const shDurum = s => SH_TR[String(s || "").replace("blocked:", "")] || String(s || "—");
  // ---- BORÇLAR TURUNUN BEYANI (2026-08-02): `red_nedeni` ve `atr_kaynak` ---------------------
  // `blocked:broker_kurali` bir SINIFTIR, teşhis değil: hangi broker kuralının kestiği ayrı bir
  // alanda (`red_nedeni`) taşınıyor ve o alan `broker._red(...)`ın kendi jetonudur — pano onu
  // ikinci kez HESAPLAMAZ (iki hesap zamanla ayrışır, intraday_shadow.py'nin kendi kuralı), yalnız
  // ÇEVİRİR. Çevirisiz bırakmak `qty_zero`yu ekrana ham basmak olurdu ve `.tag` uppercase'i
  // tr-TR'de `POSİTİON_EXİSTS` gibi bozuk bir sözcük üretiyor — aynı sınıf hata.
  // İKİSİ DE BUGÜNE KADAR ÖKSÜZDÜ (YASA 6): `intraday_shadow.record` yazıyor, `summarize` satırı
  // aynen geçiriyor, `/api/diagnostics` servis ediyor ve panoda TEK okuyucusu yoktu. Bu blok o
  // zinciri kapatır. Bilinmeyen bir jeton gelirse ham hâli basılır — sessizce yutulmaz (YASA 4).
  const RED_TR = { already_open: "zaten açık pozisyon", max_chase: "kovalama tavanı aşıldı",
                   open_below_stop: "açılış stop'un ALTINDA", qty_zero: "boyut sıfıra yuvarlandı",
                   illiquid: "likidite yetersiz (ADV)", notional_cap: "notional tavanı" };
  const redNedeni = k => k ? (RED_TR[String(k)] || String(k)) : null;
  // ---- ÜÇ İCRA GİRDİSİ, ÜÇ HÂL (borçlar turu, 2026-08-02) ------------------------------------
  // `entry_law` yan tablosu SİLAHLANMA ANINDA yazılır ve gölge icrasına üç girdi taşır: `atr`
  // (limitin sıkılığı), `pivot` (erken itlaf), `gap_at_submit` (gap-risk vetosu). Üçü de panoda
  // OKUNMUYORDU — üretici (`intraday_shadow.record`) yazıyor, `summarize` aynen geçiriyor,
  // `/api/diagnostics` servis ediyor, tüketici yoktu (YASA 6, satır düzeyinde öksüz alan).
  //
  // ÜÇLÜ AYRIM BEKÇİ DİLİNİN AYNISI (S2R-3 · C21/C22): "ölçülemedi" ile "temiz" ayrı şeylerdir,
  // ve burada ÜÇÜNCÜ bir hâl daha var — KOPUKLUK. Üretici bunu `_yan_tablo_kaynagi` ile TEK
  // yerde ayırıyor ve üç ayrı cümle yazıyor:
  //   · yan tabloda satır YOK        → KABLO KOPUK (tohumlanmış defter / yasa öncesi plan)
  //   · satır var, alan None         → MEŞRU ölçümsüzlük (o gün hesaplanamadı)
  //   · değer var                    → ölçüldü
  // İlk ikisini tek cümleye katlamak, kopmuş bir kabloyu meşru bir boşluk gibi gösterirdi.
  //
  // AYRIM ÜRETİCİNİN CÜMLESİNDEN OKUNUR, YENİDEN HESAPLANMAZ. İki çıpa (`satır YOK` / `var ama`)
  // `intraday_shadow._yan_tablo_kaynagi`nin İKİ dalına aittir ve testte o kaynağa karşı çivilenir:
  // üretici cümlesini değiştirirse test KIRMIZI verir — pano sessizce yanlış sınıflandırmaz.
  // Değerden türetmek mümkün DEĞİL: her iki hâlde de alan None gelir.
  const _IK_KOPUK = "satır YOK", _IK_OLCULEMEDI = "var ama";
  const icraDurum = kaynak => {
    const s = String(kaynak || "");
    if (!s) return "yok";                       // üretici bu alanı hiç yazmamış (yasa öncesi satır)
    if (s.includes(_IK_KOPUK)) return "kopuk";
    if (s.includes(_IK_OLCULEMEDI)) return "olculemedi";
    return "olculdu";
  };
  // Kaynak cümlesi HER ZAMAN `title`da durur (belirsiz() sözleşmesi: beyansız kesik çizgi süstür).
  // Renk kanal DEĞİL: kopukluk `warn`, ölçümsüzlük `mut` — ikisi de kelimeyle de ayrılıyor.
  const icraGirdi = (etiket, deger, kaynak, bicim) => {
    const d = icraDurum(kaynak);
    if (d === "yok") return "";
    if (d === "olculdu") return `${esc(etiket)} ${bicim(deger)}`;
    return `<span class="${d === "kopuk" ? "warn" : "mut"}">${esc(etiket)} ${
      belirsiz(d === "kopuk" ? "KABLO KOPUK" : "ÖLÇÜLEMEDİ", kaynak)}</span>`;
  };
  const shRows = (sh.today || []).map(r => {
    const ws = r.status === "would_submit";
    const g = r.gates || {};
    // Kapı özeti: engelleyen kapı zaten status'ta; burada ÖLÇÜLEN girdiler okunur ki "neden
    // bloklandı" satırın kendisinden anlaşılsın (boyut çarpanı, açık pozisyon, veri kapısı).
    const gz = [g.halt ? "halt" : null, g.breaker ? "kesici" : null, g.data_bad ? "veri" : null,
                g.position_exists ? "pozisyon var" : null, g.max_open_ok === false ? "slot dolu" : null,
                g.size_mult != null ? `boyut ×${trn(g.size_mult, 2)}` : null].filter(Boolean).join(" · ");
    // ÜÇ İCRA GİRDİSİ TEK ŞERİTTE. Sıra hüküm mertebesine göre: ATR (limitin sıkılığını
    // belirler) → gap (vetoyu ateşler) → pivot (bugün hükmü DEĞİŞTİRMEZ, yalnız satıra yazılır).
    // Ölçülmüş hâlde değer basılır; ölçülemeyen/kopuk hâlde üreticinin kendi cümlesi `title`da.
    const icra = [
      icraGirdi("ATR", r.atr, r.atr_kaynak,
                v => `${trn(v, 2)}${r.limit != null ? ` (limit ${trn(r.limit, 2)})` : ""}`),
      // gap ÜÇ DEĞERLİDİR: true/false ölçülmüş iki hüküm, None ise ölçüm YOK. `false`u
      // "gap yoktu" diye basmak doğru; `null`u öyle basmak uydurma olurdu — ayrımı icraDurum yapar.
      icraGirdi("gap", r.gap_at_submit, r.gap_at_submit_kaynak, v => (v ? "VAR" : "yok")),
      icraGirdi("pivot", r.pivot, r.pivot_kaynak, v => trn(v, 2)),
    ].filter(Boolean);
    return `<div class="trow" style="grid-template-columns:66px 96px 92px 74px 1fr 104px">
      <span class="tick">${esc(r.ticker)}</span>
      <span class="mono-num">${money(r.sim_price)}<br><span class="mut" style="font-size:10px">tetik ${trn(r.entry_trigger, 2)}</span></span>
      <span class="mono-num">${r.sim_fill == null ? '<span class="mut">—</span>' : money(r.sim_fill)}<br><span class="mut" style="font-size:10px">sim dolum</span></span>
      <span class="mono-num">${r.qty == null ? '<span class="mut">—</span>' : r.qty + " adet"}<br><span class="mut" style="font-size:10px">${r.risk_dollars == null ? "" : money(r.risk_dollars) + " risk"}</span></span>
      <span class="chain mut" style="font-size:11px">${esc(gz || "—")}<br>${esc(mktSaat(r.bar_t))} · bar ${esc(String(r.bar_t || "").slice(0, 10))}${
        r.red_nedeni ? `<br><span class="warn">broker kuralı: ${esc(redNedeni(r.red_nedeni))}</span>` : ""}${
        icra.length ? `<br>${icra.join(" · ")}` : ""}</span>
      ${_chip(shDurum(r.status), ws ? "t-go" : "t-vi")}</div>`;
  }).join("");
  const veRows = (ve.recent || []).map(p => `<div class="trow" style="grid-template-columns:66px 92px 92px 1fr">
      <span class="tick">${esc(p.ticker)}</span><span class="mono-num">${money(p.sim_fill)}</span>
      <span class="mono-num">${money(p.eod_fill)}</span>
      <span class="mono-num ${cls(p.delta_pct)}">${isr(p.delta_pct, "%" + trn(p.delta_pct, 2))} <span class="mut" style="font-size:11px">EOD − gölge · ${esc(p.date)}</span></span></div>`).join("");
  const s5 = `<div class="card rise"><h2 class="t">Gölge icra · Faz 4b
      ${_chip(sh.enabled === false ? "KAPALI" : "GÖLGE · EMİR YOK", sh.enabled === false ? "t-vi" : "t-go")}</h2>
    <p class="hint" style="margin-top:0">Tetik kesildiği anda <b>tam icra kararı</b> (kapılar + boyutlandırma + emir niyeti)
      hesaplanır ve <code>intraday_shadow_orders.jsonl</code>'e yazılır. <b>Hiçbir emir gönderilmez</b>, canlı defter
      fill edilmez, <code>INTRADAY_ARM</code> bayrağına dokunulmaz — boyutlandırma KOPYA bir broker üzerinde EOD ile
      aynı kodla simüle edilir. Sim fiyat sözleşmesi: <code>max(bar açılışı, tetik)</code>.</p>
    <p class="hint" style="margin-top:6px">Her satırın kapı şeridinde <b>üç icra girdisi</b> okunur —
      <b>ATR</b> (limitin sıkılığı), <b>gap</b> (gönderim anı veto girdisi), <b>pivot</b> (erken itlaf).
      Üçü de <code>portfolio.json.entry_law</code>'dan, <b>silahlanma anında</b> sabitlenir ve üç hâlleri
      AYRI okunur: değer yazılıysa ölçüldü · <b>ÖLÇÜLEMEDİ</b> = satır var, o girdi o gün hesaplanamadı ·
      <b>KABLO KOPUK</b> = yan tabloda plan satırı hiç yok (tohumlanmış defter ya da yasa öncesi
      silahlanmış plan). Son ikisi kesik alt çizgiyle işaretlidir; üzerine gelince üreticinin kendi
      cümlesi görünür. <b>Boş bir girdi "engel yoktu" DEĞİLDİR</b> — ölçülemeyen bir kapı, geçilmiş
      bir kapı gibi okunamaz.</p>
    <div class="srow"><span>Bugün · gönderilecekti / bloklandı</span><b>${sh.today_n ?? 0} satır · <span>${sh.would_submit_n ?? 0}</span> / <span class="mut">${sh.blocked_n ?? 0}</span></b></div>
    <div class="srow"><span>Defter toplamı</span><b>${sh.total ?? 0} gölge kararı</b></div>
    ${shRows ? `<div class="tbl" style="margin-top:10px"><div class="trow head" style="grid-template-columns:66px 96px 92px 74px 1fr 104px">
        <span>HİSSE</span><span>SİM FİYAT</span><span>SİM DOLUM</span><span>BOYUT</span><span>KAPILAR · BAR</span><span>SONUÇ</span></div>${shRows}</div>`
      : `<p class="hint">${esc(sh.enabled === false ? "Gölge katmanı kapalı (MERIDIAN_SHADOW=0)."
          : "Gölge henüz ölçmedi — bugün tetik kesen silahlı plan yok. Bu bir arıza değil, seansın dürüst hâli.")}</p>`}
    <h3 class="t" style="margin-top:18px">EOD dolgusuyla kıyas</h3>
    <p class="hint" style="margin-top:0">Aynı planın gölge dolumu ile <b>gerçek ertesi-açılış dolgusu</b> arasındaki fark.
      İki taraf da friksiyon (slipaj + etki) SONRASI fiyattır — aksi hâlde her satıra sabit bir sapma eklenir ve
      zamanlama farkı gibi okunurdu.</p>
    <div class="srow"><span>Eşleşen çift / eşleşmeyen</span><b>${ve.n_paired ?? 0} · <span class="mut">${ve.n_unpaired ?? 0} eşleşmedi</span></b></div>
    <div class="srow"><span>Ortalama fark (EOD − gölge)</span><b class="${ve.mean_delta_pct == null ? "mut" : cls(ve.mean_delta_pct)}">${
      ve.mean_delta_pct == null ? "ölçülmedi" : isr(ve.mean_delta_pct, "%" + trn(ve.mean_delta_pct, 3))}</b></div>
    ${veRows ? `<div class="tbl" style="margin-top:10px"><div class="trow head" style="grid-template-columns:66px 92px 92px 1fr">
        <span>HİSSE</span><span>GÖLGE</span><span>EOD</span><span>FARK</span></div>${veRows}</div>`
      : `<p class="hint">Henüz eşleşen çift yok — bir gölge kararı ancak aynı plan EOD'de de dolduğunda kıyaslanabilir.</p>`}</div>`;

  return { s1, s2, s3, s4, s5 };
}
// VERİ YARISI — Veri Sağlığı'nda kalır.
RENDER.intraday = async () => {
  const p = await intraParcalar();
  $("page-intraday").innerHTML = bolumBasHTML("intraday", "Seans-içi akış", _INTRA_ALT)
    + p.s3 + p.s4;
};
// EMİR / SİLAHLAMA YARISI — Portföy & Emirler'e taşındı.
// Bu yarının içinde bir EMİR KAPISI var (`intradayArm`) ve gölge icra tam olarak "emir çıkar
// mıydı?"yı ölçüyor. Veri Sağlığı sayfasında dururken silahlama düğmesi, veri tazeliği kartlarının
// arasında kayboluyordu — bir emir kapısının evi kitap sayfasıdır.
RENDER.intraemir = async () => {
  const p = await intraParcalar();
  $("page-intraemir").innerHTML = bolumBasHTML("intraemir", "Seans-içi silahlanma · gölge icra",
    "Gözlem kipi EOD-silahlı planların tetik-geçişini ÖLÇER, emir GÖNDERMEZ. Gölge icra aynı anda "
    + "tam icra kararını (kapılar + boyutlandırma) hesaplar ve deftere yazar — canlı kitaba dokunmadan.")
    + p.s1 + p.s2 + p.s5;
};

// ---- REDDEDİLEN GÖNDERİMİ KAPAT — "gördüm", "sil" değil ---------------------------------------
// Uç tanınmayan anahtarı SESSİZCE yutmaz (`unknown` döner); burada da yutulmaz: operatörün
// kapattığını sandığı ama kapanmamış bir ret, bu mekanizmanın önlemek için var olduğu şeyin ta
// kendisidir. Kapatma sonrası bölüm tazelenir ve çekmece kapanır (kayıt anahtarları yenilenir).
async function _ackRejects(payload, msgYazi) {
  const bekle = $("fsub-msg");
  if (bekle) bekle.textContent = "kapatılıyor…";
  let sonuc = null;
  try {
    sonuc = await apiFetch("/api/broker_reject/ack", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload) }).then(x => x.json());
  } catch (e) {
    if (bekle) bekle.innerHTML = `<span class="neg">${esc(e.message)}</span>`;
    return;
  }
  closeDrawer();
  // AKTİF SAYFA TAZELENİR, SABİT BİR RENDER ADI DEĞİL (S2R-2): ret defteri artık Portföy'ün
  // `mutabakat` bölümünde ve palet komutu oraya götürüyor. `RENDER.operasyon()` çağırmak,
  // operatörün BAKMADIĞI sayfayı tazelemek ve `#fsub-msg`i asla bulamamak olurdu.
  await _aktifSayfayiCiz();
  // MESAJ RENDER'DAN SONRA YAZILIR (2026-07-27, tarayıcıda ölçüldü): önce yazınca
  // yeniden çizim bölümü baştan kurup mesajı siliyordu. Sayı değişimi çoğu durumda kendi
  // başına geri bildirimdir ama `unknown` DEĞİLDİR: tanınmayan anahtar yalnız bu satırda görünür
  // ve silinirse, uç dürüstçe rapor etmesine rağmen operatör sessiz bir başarı görürdü — tam da
  // bu mekanizmanın önlemek için var olduğu şey.
  const el = $("fsub-msg");
  if (el) el.innerHTML = (sonuc.unknown || []).length
    ? `<span class="warn">${sonuc.acked_n} kapatıldı · ${sonuc.unknown.length} anahtar tanınmadı (${esc((sonuc.unknown || []).join(", "))})</span>`
    : `<span class="pos">✓ ${msgYazi(sonuc)}</span>`;
}
window.ackReject = key => _ackRejects({ keys: [key] }, r => `kapatıldı · ${r.open} açık kaldı`);
window.ackRejectAll = () => _ackRejects({ all: true }, r => `${r.acked_n} ret kapatıldı`);

window.intradayArm = async (on) => {
  const msg = $("intraday-arm-msg");
  if (on && !confirm("Intraday silahlamayı AÇ?\n\nBu, otonom intraday emir KAPISINI kaldırır. Faz 4b (gerçek silahlanma) HENÜZ uygulanmadığı için şu an emir GÖNDERMEZ — yalnız bir hazırlık bayrağıdır; ama açık bırakmak ileride Faz 4b gelince otonom intraday emri etkinleştirir. Emin misin?")) return;
  if (msg) msg.textContent = "uygulanıyor…";
  try {
    const r = await apiFetch("/api/intraday-arm", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ on }) }).then(x => x.json());
    if (msg) msg.innerHTML = r.intraday_armed ? '<span class="neg">⚠ SİLAHLI (Faz 4b yok — yalnız hazırlık)</span>' : '<span class="pos">✓ gözlem-modu (silahsız)</span>';
    // Düğme ve mesaj kutusu (`#intraday-arm-msg`) artık EMİR yarısındadır — `RENDER.intraday()`
    // (akış yarısı) çizilseydi düğmenin yeni durumu ekranda hiç güncellenmezdi.
    await RENDER.intraemir(); revealActive();
  } catch (e) { if (msg) msg.innerHTML = `<span class="neg">${esc(e.message)}</span>`; }
};

RENDER.ajan = async () => {
  const d = await j("/api/agent");
  const sb = d.scoreboard || { versions: {} };
  const versions = Object.entries(sb.versions || {}).sort((a, b) => +a[0] - +b[0]);
  const timeline = versions.map(([v, info]) => `<span class="lv ${(+v === sb.current_version) ? 'on' : ''}">v${String(v).padStart(2,'0')}${info.changed_variable ? ` · ${esc(info.changed_variable)}` : ''} · skor ${info.live_score ?? info.backtest_oos ?? '—'}</span>`).join('<span class="tx3" style="align-self:center">→</span>');
  const cards = d.hypotheses.slice().reverse().map(h => {
    const [label, kls] = HSTATUS[h.status] || [h.status, "s-rj"];
    const pd = h.predicted_delta, rd = h.realized_delta;
    const rr = (h.backtest && h.backtest.candidate_oos != null) ? `sınav notu <b style="color:${rd!=null?(rd>0?'var(--green)':'var(--red)'):'var(--tx)'}">${h.backtest.candidate_oos}</b>` : '';
    const meta = [pd != null ? `tahmin <b>${pd > 0 ? '+' : ''}${pd}</b>` : '',
      rd != null ? `gerçekleşen <b style="color:${rd > 0 ? 'var(--green)' : 'var(--red)'}">${rd > 0 ? '+' : ''}${rd}</b>` : rr,
      (h.reject_reasons || []).length ? esc(h.reject_reasons.join('; ')) : (h.status === 'live' ? 'canlı · yeterli işlem bekleniyor' : '')].filter(Boolean);
    // Slip bir kontrol olur ama <button> OLAMAZ: içinde başlık ve paragraf var, ikisi de butonun
    // içerik modeline girmez. Bu yüzden role+tabindex + Enter/Space (rowAttrs asDiv=true).
    // Çekmecede olan, burada OLMAYAN şey: backtest sayıları — aday/mevcut OOS, marj, P(ΔS>0),
    // sondaj sayısı. Kapının neden öyle dediği tek bir tıkla okunur.
    const k = rec("hyp", h);
    return `<div class="hyp rise rowbtn" ${rowAttrs(k, `Hipotez: ${h.variable} ${h.old ?? "?"} → ${h.new}, ${label}. Kaydı aç.`, true)}>
      <div class="top"><span class="v">v${String(h.version_to||h.version_from||'?').toString().padStart(2,'0')} · ${esc(h.variable)}</span><span class="st ${kls}">${label}</span></div>
      <h3>${esc(h.variable)} ${esc(h.old ?? '?')} → ${esc(h.new)}</h3>
      <p>${esc(h.rationale || '')}</p>
      <div class="meta">${meta.map(m => `<span>${m}</span>`).join('')}</div></div>`;
  }).join("");
  // KALİBRASYON KARTI BURADAN ÇIKTI (S2R-2): "tahmin mi tuttu?" karnenin sorusudur ve artık
  // `karne` bölümünde, dört sayacın yanında duruyor — hüküm ile kanıtı ayrı bölümlere koymak,
  // ikisini de zayıflatıyordu. `d.calibration_scatter`/`d.calibration` aynı uçtan orada okunur.
  // "DIŞA AKTAR & OPERASYON" KARTI DA ÇIKTI: CSV/özet/yedek/teşhis-zip/bildirim-testi hiçbiri
  // "makine ne öğreniyor?" sorusuna hizmet etmiyor — evi Kilitler & Yapılandırma (ayarlar bölümü,
  // detay katmanında). Okuyucu korunumu: `/api/report.csv`, `/api/digest`, `/api/digest/weekly`,
  // `/api/state/snapshot`, `/api/debug_export`, `/halt` ve `notifyTest`in TEK yüzeyi oydu.
  $("ajan-own").innerHTML = bolumBasHTML("ajan", "Hipotez defteri",
    "Beyin ne önerdi, kapı ne dedi, gerçekte ne oldu — üçü yan yana. Her satır açılır: kapı "
    + "kaydı, OOS sayıları ve eleme gerekçesi çekmecede. Sürüm ekseninin iki karnesi de burada: "
    + "<b>rollback sicili</b> (kendini geri alıyor mu?) ve <b>regresyon kırılımı</b> (neyi "
    + "düzeltti, neyi BOZDU).")
    + `<div class="card rise"${katKart("ajan:surumler")}><h2 class="t">Strateji sürümleri (v01 → …)</h2>
      ${kartOzeti(!versions.length ? {
        deger: null, rozet: "ÖLÇÜLEMEDİ",
        meta: "karne defterinde sürüm satırı yok — ölçülemedi (v01'de duruyor DEĞİL)." }
      : { deger: "v" + String(sb.current_version ?? versions[versions.length - 1][0]).padStart(2, "0"),
          oran: kanitOrani(versions.length), payda: "kayıtlı sürüm",
          meta: `${versions.length} sürüm kayıtlı${(() => {
            const son = versions[versions.length - 1][1] || {};
            return son.changed_variable ? ` · son değişen <b>${esc(son.changed_variable)}</b>` : "";
          })()}` })}
      <div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center">${timeline || '<span class="mut">yalnızca v01</span>'}</div></div>
    ${firsatRollbackSicili(d.rollback)}
    ${firsatRegresyon(d.regresyon)}
    ${skillAttrCard(d.skill_attribution)}
    <div class="lstack rise" style="margin-top:16px">${cards || '<div class="empty">Henüz tahmin yok.</div>'}</div>`;
  // ALT RENDER ZİNCİRİ SÖKÜLDÜ (S2R-2): hermes/skiller/hafiza artık kardeş bölümler ve sıralarını
  // ALAN_BOLUMLERI söylüyor. Buradan çağrılırken sıra bu gövdenin içinde gizliydi — ölçülemez ve
  // taşınamaz. Ayrıca `Promise.all` üçünü PARALEL koşuyordu ve üçü de `recReset()` zincirine
  // bağlı yüzeylere yazıyordu; alanSayfasi zaten SIRAYLA çağırıyor.
};
// Dışa aktarım kutusu — Kilitler & Yapılandırma'nın detay katmanında çizilir (bkz. RENDER.ayarlar).
// Saf fonksiyon: veri almaz, DOM'a dokunmaz, yalnız HTML üretir.
function disaAktarHTML() {
  return `<div style="display:flex;gap:10px;flex-wrap:wrap;margin-top:8px">
        <a class="dlbtn" href="${dl('/api/report.csv')}">↓ İşlem defteri (CSV)</a>
        <a class="dlbtn" href="${dl('/api/digest')}" target="_blank" rel="noopener">↗ Günlük özet</a>
        <a class="dlbtn" href="${dl('/api/digest/weekly')}" target="_blank" rel="noopener">↗ Haftalık özet</a>
        <a class="dlbtn" href="${dl('/api/state/snapshot')}">↓ Durum yedeği (.tar.gz)</a>
        <a class="dlbtn" href="${dl('/halt')}" target="_blank" rel="noopener">📱 Telefon HALT sayfası</a>
        <!-- TEŞHİS PAKETİ DÜĞMESİ (K1, 2026-07-30): /api/debug_export sansürlü teşhis zip'ini
             üretiyordu (secrets.json ve bars/ BİLİNÇLİ olarak hariç) ama HİÇBİR yüzeyde
             butonu yoktu — paylaşılabilir teşhis paketi vardı, ona basacak yer yoktu. -->
        <a class="dlbtn" href="${dl('/api/debug_export')}" title="state kök dosyaları + son olaylar tek zip. secrets.json ve bars/ HARİÇ — anahtar sızdırmaz.">↓ Teşhis paketi (.zip)</a>
        <button class="dlbtn" id="ntf-btn" data-act="notifyTest">🔔 Bildirimi test et</button></div>
      <p class="hint" id="ntf-msg" style="margin-top:6px"></p>`;
}
function skillAttrCard(attr) {
  const skills = (attr && attr.skills) || [];
  if (!skills.length) return '';
  // worst avg_r first (already sorted by the API); show the weakest and strongest links
  const row = s => {
    const col = s.avg_r == null ? 'var(--tx2)' : (s.avg_r > 0 ? 'var(--green)' : 'var(--red)');
    const cfc = s.cf_avg_r == null ? 'var(--tx2)' : (s.cf_avg_r > 0 ? 'var(--green)' : 'var(--red)');
    return `<div class="trow" style="grid-template-columns:1fr 46px 60px 64px 56px 70px">
      <span class="chain">${esc(s.skill)}</span><span class="mono-num">${s.n}</span>
      <span class="mono-num">${s.win_rate == null ? '—' : pctf(s.win_rate, 0)}</span>
      <span class="mono-num" style="color:${col}">${s.avg_r == null ? '—' : (s.avg_r > 0 ? '+' : '') + s.avg_r}R</span>
      <span class="mono-num mut">${s.n_cf || 0}</span>
      <span class="mono-num" style="color:${cfc}">${s.cf_avg_r == null ? '—' : (s.cf_avg_r > 0 ? '+' : '') + s.cf_avg_r}R</span></div>`;
  };
  // KAPALI ÖZET (v198): kartın kendi cümlesi "en zayıf üstte" — özet de onu söyler. Değer EN
  // ZAYIF halkanın ortalama R'si, kanıt çubuğunun paydası o halkanın kapanmış işlem sayısı.
  // Negatif değer YÖN rolündedir (şiddet değil): kartı kendiliğinden açmaz.
  const en = skills[0] || {};
  const ozet = kartOzeti(en.avg_r == null
    ? { deger: null, meta: `${skills.length} araç listeleniyor ama en zayıfının ortalama R'si ölçülemedi — kapanmış işlem yok.`,
        rozet: "ÖLÇÜLEMEDİ" }
    : { deger: `${en.avg_r > 0 ? "+" : ""}${en.avg_r}R`, degerSinif: en.avg_r > 0 ? "pos" : "neg",
        oran: kanitOrani(en.n), payda: "kapanmış işlem (en zayıf araç)",
        meta: `${skills.length} araç ölçüldü · en zayıf <b>${esc(en.skill || "—")}</b> · n=${trn(en.n)}`,
        rozet: azOrnek(en.n) ? "AZ VERİ" : "" });
  return `<div class="card rise"${katKart("ajan:beceri")}><h2 class="t">Beceri katkısı — hangi araç işe yarıyor? <span class="tx3" style="font-weight:400">(en zayıf üstte)</span></h2>
    ${ozet}
    <div class="tbl" style="margin-top:10px">
      <div class="trow head" style="grid-template-columns:1fr 46px 60px 64px 56px 70px"><span>ARAÇ</span><span>N</span><span>İSABET</span><span>ORT. R</span><span>N·SİM</span><span>SİM R</span></div>
      ${skills.map(row).join('')}</div></div>`;
}
function scatter(pts) {
  const W = 340, H = 220, pad = 32, dom = 0.2;
  const sx = x => pad + ((x + dom) / (2 * dom)) * (W - 2 * pad), sy = y => H - pad - ((y + dom) / (2 * dom)) * (H - 2 * pad);
  const dots = (pts || []).map(p => `<circle cx="${sx(p.predicted || 0)}" cy="${sy(p.realized || 0)}" r="5" fill="${(p.predicted > 0) === (p.realized > 0) ? 'var(--green)' : 'var(--red)'}"/>`).join("");
  return `<svg viewBox="0 0 ${W} ${H}" style="width:100%;max-width:360px" role="img" aria-label="Kalibrasyon dağılımı: tahmin edilen ve gerçekleşen sonuç">
    <line x1="${pad}" y1="${sy(0)}" x2="${W - pad}" y2="${sy(0)}" stroke="var(--line-2)"/>
    <line x1="${sx(0)}" y1="${pad}" x2="${sx(0)}" y2="${H - pad}" stroke="var(--line-2)"/>
    <line x1="${sx(-dom)}" y1="${sy(-dom)}" x2="${sx(dom)}" y2="${sy(dom)}" stroke="var(--accent)" stroke-dasharray="4 4" opacity=".5"/>
    ${dots || `<text x="${W / 2}" y="${H / 2}" text-anchor="middle" fill="var(--tx2)" font-size="11">henüz kapanmış tahmin yok</text>`}
    <text x="${W - pad}" y="${sy(0) - 6}" text-anchor="end" fill="var(--tx2)" font-size="10">tahmin →</text>
    <text x="${sx(0) + 6}" y="${pad + 2}" fill="var(--tx2)" font-size="10">gerçekleşen ↑</text></svg>`;
}

// ================= HAFIZA =================
RENDER.hafiza = async () => {
  const d = await j("/api/memory");
  window._lessons = d.lessons_md;
  // KAPALI ÖZET (v198): "içeride önemli bir şey var mı?" — kaç yazılı ders var, kaç başlık
  // altında. Sayılar DOSYANIN KENDİSİNDEN türer; uç bu alanı hiç vermediyse ÖLÇÜLEMEDİ dalı
  // çalışır ve "0 ders" YAZILMAZ (ölçemedik ile boş dosya aynı piksele düşemez).
  const _dSatir = d.lessons_md == null ? null : String(d.lessons_md).split("\n");
  const _dersN = _dSatir ? _dSatir.filter(l => /^- /.test(l)).length : null;
  const _dersBaslik = _dSatir ? _dSatir.filter(l => /^#{1,2}\s/.test(l)).length : 0;
  $("page-hafiza").innerHTML = bolumBasHTML("hafiza", "Hafıza · çıkarılan dersler",
    "Ajanın kendi geçmişinden damıttığı, kalıcı yazılı dersler.")
    + `<div class="card rise"${katKart("hafiza:dersler")}><h2 class="t">lessons.md</h2>
      ${kartOzeti(_dSatir == null ? {
        deger: null, rozet: "ÖLÇÜLEMEDİ",
        meta: "/api/memory <code>lessons_md</code> alanı gelmedi — ölçülemedi (ders yok DEĞİL)." }
      : { deger: _dersN, oran: kanitOrani(_dersN), payda: "yazılı ders",
          meta: `${_dersBaslik} başlık · ${_dSatir.length} satır` })}
      <input class="searchbox" id="lsearch" placeholder="derslerde ara…" data-act="filterLessons" data-act-on="input"/>
      <div class="md" id="lessons" style="margin-top:14px">${mdToHtml(d.lessons_md)}</div></div>`;
};
function filterLessons() {
  const q = $("lsearch").value.toLowerCase();
  const lines = window._lessons.split("\n").filter(l => !q || l.toLowerCase().includes(q) || l.startsWith("#"));
  $("lessons").innerHTML = mdToHtml(lines.join("\n"));
}
function mdToHtml(md) {
  const out = []; let inList = false;
  const inline = s => esc(s).replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
  const closeL = () => { if (inList) { inList = false; return "</ul>"; } return ""; };
  (md || "").split("\n").forEach(l => {
    // MARKDOWN BAŞLIKLARI SAYFANIN MERTEBESİNE OTURUR (2026-07-27): lessons.md'nin `#` satırı
    // belge düzeyinde bir h1 üretiyordu ve Öğrenme görünümünde İKİNCİ bir h1 oluyordu — üstelik
    // bir kartın içinde, kartın kendi h2 başlığının altında. Dosyanın `#`'i sayfanın h1'i
    // değildir; kartın içindeki bir alt başlıktır. Boyut değişmez, mertebe düzelir.
    if (/^#\s/.test(l)) { out.push(closeL(), `<h3>${esc(l.slice(2))}</h3>`); }
    else if (/^##\s/.test(l)) { out.push(closeL(), `<h4>${esc(l.slice(3))}</h4>`); }
    else if (/^- /.test(l)) { if (!inList) { out.push("<ul>"); inList = true; } out.push(`<li>${inline(l.slice(2))}</li>`); }
    else if (/^_.*_$/.test(l)) { out.push(closeL(), `<em>${esc(l.slice(1, -1))}</em>`); }
    else if (l.trim() === "") { out.push(closeL()); }
    else { out.push(closeL(), `<div>${inline(l)}</div>`); }
  });
  if (inList) out.push("</ul>");
  return out.join("");
}

// ================= SKİLLER =================
// ---- EMEKLİ ARAÇLAR AYRI RAFTA (pano turu 2026-07-31) ---------------------------------------
// Kütüphane 67 aracın HEPSİNİ tek listede çiziyordu; operatör panoda "67 skill" görüp temizliğin
// hiç yansımadığını okudu. Kayıtta damga ZATEN vardı (`enabled` + `retired` + `merged_into`),
// panoda filtre yoktu. Artık VARSAYILAN GÖRÜNÜM YALNIZ AKTİFLERDİR; emekli/birleştirilmiş olanlar
// katlanır bir bölümde durur ve her satır KENDİ gerekçesini (`reason`, `merged_into`) taşır.
// SİLİNMEZ, SESİ KISILIR: bir aracın nereye birleştiği kanıttır ve kanıt gizlenmez.
RENDER.skiller = async () => {
  const d = await j("/api/skills");
  const skills = d.skills || {}, c = d.counts || {};
  const STATE_TR = { active: "aktif", available: "hazır", disabled: "kapalı", shadow: "gölge" };
  const tumu = Object.entries(skills);
  const aktif = tumu.filter(([, i]) => i.enabled);
  const emekli = tumu.filter(([, i]) => !i.enabled);
  // Sayılar KAYITTAN türer, sabit yazılmaz: birleşen/emekli/kapalı üç ayrı hâldir ve tek sayıya
  // katlanırsa "37 kapalı" cümlesi "37'si anahtar bekliyor" diye okunur (yanlış: 36'sı emekli).
  const birlesenN = emekli.filter(([, i]) => i.merged_into).length;
  const emekliN = emekli.filter(([, i]) => i.retired && !i.merged_into).length;
  const kapaliN = emekli.length - birlesenN - emekliN;
  const byCat = {};
  // Kategorisiz kayıt "undefined" adlı bir bölüm üretiyordu (pullback-screener'ın kaydında
  // `category` yok). Eksik alan bir bölüm adı DEĞİLDİR; adıyla söylenir.
  aktif.forEach(([n, i]) => (byCat[i.category || "sınıfsız"] = byCat[i.category || "sınıfsız"] || []).push([n, i]));
  const satir = ([n, i]) => {
    const st = i.shadow ? "shadow" : (i.enabled ? i.mode : "disabled");
    const tag = i.enabled ? (i.mode === "active" ? "t-go" : "t-vi") : "t-no";
    return `<div class="trow" style="grid-template-columns:1fr 120px 78px 1fr">
      <span><b style="font-weight:500">${esc(n)}</b>${i.agent_authored ? ' <span class="tag t-vi" style="font-size:10px">ajan yazdı</span>' : ''}</span>
      <span class="mut" style="font-size:11px">${i.fmp !== '-' && i.fmp != null ? `FMP:${esc(i.fmp)} ` : ''}${i.alpaca !== '-' && i.alpaca != null ? `ALPACA:${esc(i.alpaca)}` : ''}</span>
      <span><span class="tag ${tag}">${STATE_TR[st] || esc(st)}</span></span>
      <span class="mut" style="font-size:11px">${esc(i.reason || '')}</span></div>`;
  };
  const cats = Object.entries(byCat).sort().map(([cat, list]) => {
    const rows = list.sort().map(satir).join("");
    // KAPALI ÖZET (v198): kategori kartı "bu rafta kaç araç var, kaçı FİİLEN aktif kipte?"
    // sorusunu satırları okutmadan cevaplar. Payda BEYANLI: rafın kendi araç sayısı.
    const aktifKip = list.filter(([, i]) => i.mode === "active" && !i.shadow).length;
    const golge = list.filter(([, i]) => i.shadow).length;
    return `<div class="card rise"${katKart("skiller:kategori", cat)}><h2 class="t">${esc(cat)} (${list.length})</h2>
      ${kartOzeti({ deger: `${aktifKip}/${list.length}`, oran: list.length ? aktifKip / list.length : null,
        payda: "raftaki araç", meta: `${aktifKip} aktif kip · ${list.length - aktifKip - golge} hazır${golge ? ` · ${golge} gölge` : ""}` })}
      ${rows}</div>`;
  }).join("");
  // Emekli rafı: hâl etiketi + gerekçe + (varsa) hangi araca birleştiği. Satırın tamamı kayıttan
  // gelir; alan yoksa hücre boş kalır, uydurma gerekçe yazılmaz.
  const emekliRows = emekli.sort().map(([n, i]) => {
    const [hal, kls] = i.merged_into ? ["birleşti", "t-vi"]
      : (i.retired ? ["emekli", "t-no"] : ["kapalı", "t-rv"]);
    const nereye = i.merged_into ? ` <span class="chain">→ ${esc(i.merged_into)}</span>` : "";
    return `<div class="trow" style="grid-template-columns:1fr 92px 1fr 96px">
      <span><b style="font-weight:500">${esc(n)}</b>${nereye}</span>
      <span><span class="tag ${kls}">${hal}</span></span>
      <span class="mut" style="font-size:11px">${esc(i.reason || "gerekçe kaydedilmemiş")}</span>
      <span class="mut" style="font-size:11px">${esc(String(i.retired_at || "").slice(0, 10))}</span></div>`;
  }).join("");
  const emekliCard = emekli.length ? `<details class="gloss rise" style="margin-top:16px">
    <summary>emekli / birleştirilmiş (${emekli.length}) — ${birlesenN} birleşti · ${emekliN} emekli · ${kapaliN} kapalı</summary>
    <div class="body">
      <p class="hint" style="margin-top:0">Bu araçlar kütüphaneden SİLİNMEDİ, hattan düşürüldü:
        kaydı, gerekçesi ve (birleştiyse) hangi araca taşındığı burada durur. Varsayılan görünüm
        yalnız aktifleri sayar — bir aracın var olması onun koştuğu anlamına gelmez.</p>
      ${emekliRows}</div></details>` : "";
  const revs = d.revisions || [];
  const revCard = revs.length ? `<div class="card rise" style="border-color:var(--amber)"${katKart("skiller:revizyon")}><h2 class="t">Revizyon taslakları · onayın bekleniyor (${revs.length})</h2>
    ${kartOzeti({ deger: revs.length, rozet: "ONAY BEKLİYOR",
      meta: `${revs.length} taslak · ${esc(revs.map(r => r.skill).slice(0, 3).join(", "))}${revs.length > 3 ? " …" : ""}` })}
    ${revs.map(r => `<div class="trow" style="grid-template-columns:1fr auto auto">
      <span><b>${esc(r.skill)}</b><br><span class="chain">${esc(r.rationale || "gerekçe yok")} · kanıt: n=${r.evidence?.n} ort ${r.evidence?.avg_r}R</span>
        <!-- SATIRIN KENDİ MESAJ KUTUSU (v219): onay kapısının reddi (409) BU satırda görünür.
             İd değil öznitelik — aynı beceri Onaylar yüzeyinde de listeleniyor ve iki id çakışırdı. -->
        <p class="hint" data-eylem-msg="${esc(r.skill)}" style="margin:6px 0 0"></p></span>
      <button class="dlbtn" data-act="skillRev" data-a1="${esc(r.skill)}" data-a2="apply">Onayla</button>
      <button class="dlbtn" style="border-color:var(--red);color:var(--red)" data-act="skillRev" data-a1="${esc(r.skill)}" data-a2="reject">Reddet</button></div>`).join("")}
    <p class="hint">Taslak ajan tarafından ölçülmüş zayıflık kanıtıyla yazıldı (skills/&lt;ad&gt;/SKILL.md.v2-draft). Onay eski sürümü arşivler; karne sıfırdan ölçülür.</p></div>` : "";
  $("page-skiller").innerHTML = bolumBasHTML("skiller", `Araç kütüphanesi · ${c.enabled ?? "—"} aktif araç`,
    "Ajanın kullandığı analiz araçları ve her birinin ölçülen katkısı. Listeler YALNIZ aktif "
    + "araçları sayar; hattan düşürülenler alttaki katlanır rafta, gerekçesiyle durur.")
    + revCard + `
    <div class="mrow rise">
      ${mc("Aktif", c.enabled, "var(--green)", "şu an çalışan")}${mc("Pipeline'da", c.active_in_pipelines, "var(--amber)", "günlük hatta bağlı")}${mc("Emekli · birleşti", birlesenN + emekliN, "var(--tx2)", "hattan düşürüldü, kaydı duruyor")}${mc("Kayıtta toplam", c.total, null, "aktif + emekli + kapalı")}</div>${runsCard(d.recent_runs)}${cats}${emekliCard}`;
};
// ---- PIPELINE KOŞU DEFTERİ (K1, 2026-07-30) -------------------------------------------------
// `pipeline_runs.jsonl` her skill koşusunda satır yazıyordu; tek okuyucusu /api/pipeline_runs'tı
// ve o ucu HİÇBİR istemci çağırmıyordu. Artefakt yasası tatmin görünüyordu (modüller-arası okuma
// VAR) ama zincir bir kat yukarıda — HTTP→DOM katmanında — kopuktu: statik Python grafı JS'i
// göremez. skills.py:3'ün "ajanın yaptığı hiçbir şey görünmez değildir" vaadi panoda karşılıksızdı.
//
// `skills_declared_not_run` BİLEREK ÖNE ÇIKARILIYOR: "beyan edildi ama koşmadı" tam olarak
// Hermes'in 15 gündür aynı 14 düğmede dönmesiyle aynı sınıf bir körlük kanıtıdır ve yalnız bu
// defterde ölçülüyor. Bir pipeline 9 beceriyi beyan edip 0'ını koşuyorsa, katalog sayısı ("22
// beceri") bir YETENEK değil bir İDDİA olur.
function runsCard(runs) {
  runs = runs || [];
  if (!runs.length) return `<div class="card rise"${katKart("skiller:kosular")}><h2 class="t">Pipeline koşuları</h2>
    ${kartOzeti({ deger: null,
      meta: "pipeline_runs.jsonl'de satır yok — ilk skill hattı koştuğunda ölçüm başlar (0 koşu DEĞİL: defter henüz açılmadı)." })}
    <div class="empty">Henüz koşu satırı yok — ilk skill pipeline'ı koştuğunda burada görünür.</div></div>`;
  const rows = runs.slice(0, 12).map(r => {
    const inv = (r.skills_invoked || []).length, notRun = (r.skills_declared_not_run || []).length;
    const dur = (r.started && r.finished) ? Math.round((Date.parse(r.finished) - Date.parse(r.started)) / 1000) : null;
    return `<div class="trow" style="grid-template-columns:118px 130px 64px 1fr 74px">
      <span class="mut" style="font-size:11px">${esc(relTime(r.started) || "—")}</span>
      <span><span class="tag t-vi">${esc(String(r.pipeline || "—"))}</span></span>
      <span class="mono-num">${dur == null ? "—" : dur + "s"}</span>
      <span class="chain">${inv} beceri koştu${notRun ? ` · <span class="warn">${notRun} beyan edildi KOŞMADI</span>` : ""}${
        r.error ? ` · <span class="neg">${esc(String(r.error).slice(0, 60))}</span>` : ""}</span>
      <span><span class="tag ${r.status === "ok" ? "t-go" : "t-no"}">${esc(String(r.status || "—"))}</span></span></div>`;
  }).join("");
  // KAPALI ÖZET (v198): defterin TEK ölçtüğü körlük kanıtı — "beyan edildi, koşmadı". Payda
  // BEYANLI ve gerçek: gösterilen koşularda beyan edilen toplam beceri. Beyan sıfırsa oran
  // ÇİZİLMEZ (paydasız çubuk yok) ve meta nedenini yazar.
  const _kosan = runs.slice(0, 12).reduce((s, r) => s + (r.skills_invoked || []).length, 0);
  const _kosmayan = runs.slice(0, 12).reduce((s, r) => s + (r.skills_declared_not_run || []).length, 0);
  const _beyan = _kosan + _kosmayan;
  return `<div class="card rise"${katKart("skiller:kosular")}><h2 class="t">Pipeline koşuları <span class="tx3" style="font-weight:400">(pipeline_runs.jsonl · en yeni ${Math.min(12, runs.length)})</span></h2>
    ${kartOzeti({ deger: `${_kosan}/${_beyan || "—"}`,
      oran: _beyan ? _kosan / _beyan : null, payda: _beyan ? "beyan edilen beceri" : "",
      degerSinif: _kosmayan ? "warn" : "",
      meta: _beyan ? `${Math.min(12, runs.length)} koşu · ${_kosmayan} beceri beyan edildi KOŞMADI`
                   : `${Math.min(12, runs.length)} koşu · hiçbiri beceri beyan etmemiş — oran tanımsız`,
      rozet: _kosmayan ? "BEYAN≠KOŞU" : "" })}
    <div class="trow head" style="grid-template-columns:118px 130px 64px 1fr 74px"><span>NE ZAMAN</span><span>HAT</span><span>SÜRE</span><span>BECERİ KULLANIMI</span><span>DURUM</span></div>
    ${rows}
    <p class="hint" style="margin-top:8px">"beyan edildi KOŞMADI" satırı önemlidir: bir hat becerileri
      beyan edip çağırmıyorsa, katalogdaki sayı bir yetenek değil bir İDDİADIR.</p></div>`;
}
window.skillRev = async (skill, action) => {
  if (action === "apply" && !confirm(`'${skill}' revizyonu yürürlüğe girsin mi?\n\nEski sürüm arşivlenir; skill karnesi bu tarihten itibaren yeni içerikle ölçülür.`)) return;
  // ÜÇ KUSUR BİRDEN DÜZELDİ (v219). (1) `alert("Hata: " + e)` HİÇ TETİKLENMİYORDU: `apiFetch`
  // 409'da fırlatmıyordu, yani onay kapısının reddi hiçbir yere düşmüyordu. (2) Hata OLSA BİLE
  // gövde `RENDER.skiller()` çağırıyordu — yeniden çizim mesajı silerdi. (3) Düğme Onaylar
  // yüzeyinde de var ve orada `RENDER.skiller()` GÖRÜNMEYEN bir bölümü tazelemek demekti
  // (S2R-2'nin `_ackRejects`te yazılı dersi). Tazeleme artık aktif sayfaya bağlı ve YALNIZ
  // başarıda koşuyor.
  const kutu = eylemKutusu(skill);
  if (kutu) kutu.innerHTML = `<span class="mut">${action === "apply" ? "uygulanıyor" : "reddediliyor"}…</span>`;
  try {
    await apiFetch("/api/skills/revision", { method: "POST", headers: { "content-type": "application/json" },
                                             body: JSON.stringify({ skill, action }) });
  } catch (e) {
    eylemHatasiYaz(kutu, e, (e && e.status === 409)
      ? "ONAY KAPISI REDDETTİ — onay defterinde bu revizyon kimliği için 'approve' satırı yok (ya da 'reject' var); revizyon YÜRÜRLÜĞE GİRMEDİ (fail-closed)."
      : "revizyon işlenemedi — taslak durumunu tazeleyip doğrula.");
    return;
  }
  await _aktifSayfayiCiz();
};
const mc = (l, v, col, sub) => `<div class="mcard"><p class="l">${l}</p><p class="v" style="color:${col || 'inherit'}">${v ?? '—'}</p>${sub ? `<p class="s">${sub}</p>` : ''}</div>`;

// ================= PARSEL TABLOSU =================
// Matris bir bileşen DEĞİL, kararın DAYANAĞI: Kararlar sayfasının ilk ve birincil öğesi
// (2026-07-27'ye kadar Bugün'ün tepesindeydi; oraya durum şeridi geldi). Bir tarla denemesinin
// okuduğu şeyi okur — hangi uygulama (kurulum) hangi koşulda (rejim) ne verdi VE kaç işlemden.
// GÜVEN ÇUBUĞU örneklem sayısını taşır: 3 işlemlik bir ortalama seyrek görünür, 55 işlemlik dolu.
// Az örnekli bir ortalamayı çok örnekliymiş gibi göstermek bu panonun reddettiği tek şeydir.
// Veri yoksa hücre EKİLMEMİŞ çizilir, sıfır değil. Gezinme listeyle değil KONUMLA.
let _PLOTS = null;

// İŞARET BİR HÜKÜM DEĞİLDİR (2026-07-27). Renk `mean_r > 0` ile veriliyordu: 33 işlemde
// −0.035R KIRMIZI, 55 işlemde +0.031R YEŞİL boyanıyordu — ikisi de gürültü, ikisi de sıfırdan
// ayırt edilemez. Artık bir NÖTR BANT var: ortalama, örneklem gürültüsünün (1/√n) içinde
// kalıyorsa hücre ne yeşil ne kırmızı — düz zeminde nötr mürekkep. İşaret sayının kendisinde
// durur, renkte değil. Renk ancak ortalama bandın DIŞINA çıktığında bir okuma taşır.
function signClass(meanR, n) {
  if (meanR == null || !n) return "";
  return Math.abs(meanR) > 1 / Math.sqrt(n) ? (meanR > 0 ? "pos" : "neg") : "";
}

function plotCell(c, setup, regime, si, ri) {
  const rg = REGIME_TR[regime] || regime;
  const tag = `<span class="pm-sectlabel">${esc(rg)}</span>`;
  // EKİLMEMİŞ HÜCRE: role="gridcell" taşıyan bir div'in aria-label'ı erişilebilirlik ağacına
  // HİÇ çıkmıyordu. Ad artık görsel-gizli metinle taşınır — okuyucu hangi kesitin boş olduğunu
  // bilir, gören göz "veri yok"u okur.
  if (!c) return `<div class="pm-cell pm-unsown">${tag}` +
      `<span class="vis-label">${esc(setup)} · ${esc(rg)}:</span>` +
      `<span class="pm-none">veri yok</span></div>`;
  const sc = signClass(c.mean_r, c.n), thin = azOrnek(c.n);
  // örneklem gücü: log ölçekli güven çubuğu (`kanitOrani`, v192'de TEK tanıma çıkarıldı — aynı
  // ölçek artık özet şeritlerinde de kullanılıyor ve iki kopya ilk düzenlemede ayrışırdı).
  // 55 işlemlik hücre neredeyse dolu, 3 işlemlik hücre üçte bir.
  const k = rec("plot", { si, ri });
  // HÜCRE BİR DÜĞMEDİR VE ÖYLE DUYURULUR: eskiden butonun üstüne role="gridcell" yazılıydı ve
  // bu buton rolünü EZİYORDU — yardımcı teknoloji hücreyi basılabilir olarak hiç anmıyordu.
  // RENK HÜCRE KABINDA (`.pm-cell.pos/.neg`) durur, değerin kendi sınıfında değil: matriste renk
  // zemini de boyar (gürültü bandının DIŞI), durum kartlarında yalnız mürekkebi.
  return `<button ${rowAttrs(k, `${setup} · ${rg}: ortalama ${c.mean_r}R, ${c.n} işlem, %${Math.round(c.hit * 100)} tutan${thin ? ", az örnek" : ""}${sc ? "" : ", gürültü bandında"}. Kaydı aç.`)}
      class="pm-cell ${sc}${thin ? ' thin' : ''}" data-s="${si}" data-r="${ri}">
    ${tag}${hucreGovde({
      deger: `${c.mean_r > 0 ? '+' : ''}${c.mean_r.toFixed(2)}R`,
      oran: kanitOrani(c.n), payda: `işlem sayısı · log ölçek, n=${KANIT_TAVAN_N} dolu`,
      meta: `${c.n} işlem · %${Math.round(c.hit * 100)} tutan`,
      rozet: thin ? "az örnek" : "" })}</button>`;
}

async function renderPlotMap() {
  const el = $("plotmap");
  if (!el) return;
  let d;
  try { d = await j("/api/plots"); } catch (e) { el.innerHTML = ""; return; }
  if (!d || !(d.grid || []).length) { el.innerHTML = ""; return; }
  _PLOTS = d;
  const sect = d.regimes.map(r => `<div class="pm-sect">${esc(REGIME_TR[r] || r)}</div>`).join("");
  const rows = d.grid.map((row, si) => `<div class="pm-strip">${esc(row.setup)}</div>`
    + row.cells.map((c, ri) => plotCell(c, row.setup, d.regimes[ri], si, ri)).join("")).join("");
  const untagged = d.n_trades_total - d.n_trades;
  // IZGARA ROLLERİ KALDIRILDI (2026-07-27). role="grid" vardı ama TEK BİR role="row" yoktu:
  // 12 doğrudan çocuk (presentation + columnheader×3 + rowheader×2 + gridcell×6) satırsız
  // duruyordu, yani rol geçersizdi; üstelik grid rolü ok-tuşu gezinmesi VAAT EDER ve o da yoktu.
  // Yalanı düzeltmenin dürüst yolu: rolü bırakmak. Yapı ızgaranın kendisinde zaten görülüyor,
  // her hücre ise adında kendi kurulumunu ve rejimini TAM olarak taşıyan bir düğme — okuyucu
  // konumu satır/sütun başlıklarından değil, düğmenin kendi cümlesinden alır.
  el.innerHTML = `
    <div class="rise">
      <span class="slabel"><span class="d"></span>KURULUM × REJİM</span>
      <h1 class="greet">Hangi uygulama, hangi koşulda?</h1>
      <p class="subline">Satırlar kurulum, sütunlar rejim. Her hücrenin altındaki çubuk kaç işlemden
        geldiğini gösterir — kısa çubuk, zayıf kanıt. Ortalama gürültü bandının içindeyse hücre
        renksiz kalır. Detay için hücreye tıkla.</p>
    </div>
    <div class="pm-grid rise" role="group" aria-label="Kurulum × rejim getiri matrisi — ${d.grid.length} kurulum, ${d.regimes.length} rejim" style="--cols:${d.regimes.length}">
      <div class="pm-corner" aria-hidden="true"></div>${sect}${rows}
    </div>
    <p class="pm-foot">${d.n_trades} kapanmış işlemden hesaplandı${untagged > 0
      ? ` · ${untagged} işlem kurulum/rejim etiketi taşımadığı için sayıma girmedi` : ""}.
      Ortalama R, işlem başına riske göre getiri. Renk yalnız ortalama, örneklem gürültüsünün
      (1/√n) dışına çıktığında verilir.</p>`;
}

// ================= KAYIT GÖRÜNÜMLERİ =========================================================
// Her liste türü kendi kaydını AYNI çekmecede açar. Kural: UYDURMA YOK — burada gösterilen her
// alan API paketinde zaten vardır; olmayan alan satırı hiç çizilmez (pdRow boş değeri düşürür).
const RECORD_VIEW = {
  // ---------------------------------------------------------------------------------------------
  // 00 · DURUM KARTLARI (v191) — kartın ÖZETİ ekranda, AYRINTISI burada.
  // Her çekmece, o kartın alanlarının bugüne kadar İKİ BÖLÜME dağılmış hâlini tek yerde toplar;
  // ilgili bölüme giden bağ da çekmecededir (kartın üstünde ikinci bir bağ YOK — kart tek eylem).
  // ---------------------------------------------------------------------------------------------
  durumDongu(o) {
    const sd = o.sd || {}, r = o.regime || {}, vc = o.vc || {};
    if (!sd.var) {
      return { eyebrow: "SON DÖNGÜ", title: "günlük döngü kaydı yok",
        body: `<p class="pd-warn">${esc(sd.neden || "ölçülemedi — neden bildirilmedi")}</p>
          <p class="mut">Bu bir <b>sıfır aday</b> raporu DEĞİLDİR: döngünün kendi satırı okunamadı.
          Olay defteri kuyruğunda <code>daily_cycle</code> satırı bulunamıyor.</p>` };
    }
    return { eyebrow: "SON DÖNGÜ", title: `${esc(String(sd.date || "—"))} <span class="mut">×</span> gece turu`,
      body: `<div class="pd-stats">
          ${pdStat("ADAY", sd.candidates ?? "—")}${pdStat("PLAN", sd.plans ?? "—")}
          ${pdStat("SİLAHLI", sd.armed ?? "—")}</div>
        ${sd.data_ok === false ? `<p class="pd-warn">Veri kalitesi kapısı KAPALIYDI — o gece yeni alım
          yapılmadı. Aday sayısı sıfırsa sebebi budur, kurulum yokluğu değil.</p>` : ""}
        ${sd.halted ? `<p class="pd-warn">Sistem o turda DURDURULMUŞ durumdaydı.</p>` : ""}
        <h3 class="pd-sub">Döngünün kendi kaydı</h3>
        ${pdRow("Seans", esc(sd.date))}${pdRow("Damga", esc(sd.ts))}
        ${pdRow("Yaş", sd.yas_saat == null
          ? `<span class="mut">ölçülemedi — kayıtta zaman damgası yok</span>`
          : `${trn(sd.yas_saat, 1)} saat önce`)}
        ${pdRow("Rejim", sd.regime ? esc(REGIME_TR[sd.regime] || sd.regime) : "")}
        ${pdRow("Açık pozisyon (o an)", sd.open_positions)}
        ${pdRow("Kaynak", esc(sd.kaynak))}
        <h3 class="pd-sub">Kapının hükmü · bugünkü plan defteri</h3>
        ${pdRow("GO · REVIEW · NO_GO", `${vc.GO || 0} · ${vc.REVIEW || 0} · ${vc.NO_GO || 0}`)}
        ${pdRow("Plan tarihi", esc(o.planDate))}${pdRow("İşlenen son seans", esc(o.latestSession))}
        <h3 class="pd-sub">Rejimin ham göstergeleri</h3>
        ${pdRow("Satış günleri", r.distribution_days)}
        ${pdRow("FTD (takip günü)", r.ftd == null ? "" : (r.ftd ? "var" : "yok"))}
        <div style="margin-top:14px"><button class="dlbtn" type="button" data-act="go"
          data-a1="karar#adaylar">Adaylar ve karar ağacı →</button></div>` };
  },
  durumKitap(o) {
    const t = o.t || {}, kk = t.sermaye_koken || {}, kb = t.kitap || {}, df = t.defter || {};
    const s = o.s || {};
    return { eyebrow: "KİTAP", title: `${money(t.equity)} <span class="mut">×</span> kağıt defter`,
      body: `<div class="pd-stats">
          ${pdStat("SERMAYE", money(t.equity), SERMAYE_RENK[kk.renk] || "")}
          ${pdStat("NAKİT", money(kk.gercek_canli_sermaye))}
          ${pdStat("GÜN", isr(t.day_pnl_pct, pctf(t.day_pnl_pct)), cls(t.day_pnl_pct))}</div>
        <h3 class="pd-sub">Kitabın tabanları</h3>
        ${pdRow("Gün başı sermaye", kb.day_start_equity == null
          ? `<span class="mut">ölçülmedi — kitapta alan yok (0 DEĞİL)</span>` : money(kb.day_start_equity))}
        ${pdRow("Tepe sermaye", kb.peak_equity == null ? `<span class="mut">ölçülmedi</span>` : money(kb.peak_equity))}
        ${pdRow("Nabız sermayesi", kk.nabiz_sermaye == null ? "" : money(kk.nabiz_sermaye))}
        ${pdRow("Strateji sürümü", s.strategy_version == null ? "" : "v" + esc(String(s.strategy_version)))}
        <h3 class="pd-sub">Sermayenin kökeni</h3>
        <p class="hint">Karttaki "gerçekleşmiş" GERÇEK-CANLI K/Z'dir. Aşağıdaki defter toplamı
        antrenman tohumunu (replay_seed) DA içerir — ikisi karıştırılırsa bir eğitim artefaktı
        "sistemin kaybı" diye okunur (bu ayrımın var oluş sebebi budur).</p>
        ${pdRow("Defter K/Z toplamı <span class=\"tx3\">(tohum dahil)</span>", kb.realized_pnl == null
          ? `<span class="mut">ölçülmedi</span>`
          : `<span class="${cls(kb.realized_pnl)}">${money(kb.realized_pnl)}</span>`)}
        ${pdRow("Beyan ofseti", kk.ayrisik
          ? `${money(kk.ofset_usd)}${kk.reset_tarihi ? ` · ${esc(String(kk.reset_tarihi).slice(0, 10))}` : ""}`
          : `<span class="mut">beyan yok — sermaye tabanı hiç taşınmadı</span>`)}
        ${sermayeKokenSatiri(kk, { ibareyle: true })}
        <h3 class="pd-sub">Defterin kökeni</h3>
        ${pdRow("Canlı-kâğıt satır", df.live_paper_n)}${pdRow("Antrenman tohumu satır", df.replay_seed_n)}
        ${pdRow("Kökeni ölçülmemiş satır", df.belirsiz_n)}
        <div style="margin-top:14px"><button class="dlbtn" type="button" data-act="go"
          data-a1="karar#performans">Birikim ve eğri →</button></div>` };
  },
  durumEmir(o) {
    const rc = o.rc || {}, dl = o.dl || {}, slp = o.slp || {}, ay = slp.ayna || {};
    const akis = rc.stream_ok;
    return { eyebrow: "EMİRLER · AYNA",
      title: `${trn((o.armed || []).length)} silahlı <span class="mut">×</span> ${trn(o.gonderilen)} aynada`,
      body: `<div class="pd-stats">
          ${pdStat("SİLAHLI", trn((o.armed || []).length))}
          ${pdStat("AYNAYA GİTTİ", trn(o.gonderilen))}
          ${pdStat("BEKLEYEN", trn(o.bekleyen), o.bekleyen ? "warn" : "")}</div>
        ${o.bekleyen ? `<p class="pd-warn">${trn(o.bekleyen)} plan <b>gönderilecekte kaldı</b>: silahlı,
          ama ne aynaya ulaştı ne de broker reddetti. Gönderim kolunu Ayarlar'daki
          "Silahlı planları Alpaca'ya gönder" çalıştırır.</p>` : ""}
        ${o.acikRet ? `<p class="pd-warn">${trn(o.acikRet)} açık broker reddi var — kayıtları mutabakat
          masasındaki ret defterinde açılır.</p>` : ""}
        <h3 class="pd-sub">Ayna akışı</h3>
        ${pdRow("Akış", akis == null
          ? `<span class="mut">ölçülmedi — hiç kanıt yok (ayna hiç koşmamış olabilir)</span>`
          : (akis ? `<span class="pos">canlı</span>`
                  : `<span class="neg">KOPUK</span>${wsDownFor(rc) ? ` · ${esc(wsDownFor(rc))}` : ""}`))}
        ${pdRow("Kopuş başlangıcı", esc(rc.stream_down_since))}
        ${pdRow("Son olay", esc(rc.stream_last_event_ts))}
        ${akis === false ? pdRow("Son hata", esc(rc.stream_last_error)) : ""}
        ${pdRow("Broker API", rc.api_ok == null ? "" : (rc.api_ok ? "erişilebilir" : `<span class="neg">erişilemiyor</span>`))}
        <h3 class="pd-sub">Dolum ölçümü <span class="mut">(icra defteri penceresi)</span></h3>
        ${pdRow("Dolan emir", dl.n_dolan == null
          ? `<span class="mut">${esc(slp.durum || "ölçüm yok")}</span>`
          : `${trn(dl.n_dolan)} · pencere ${esc(String(slp.pencere_gun ?? "?"))} gün`)}
        ${pdRow("Dolum oranı", dl.dolum_orani == null ? "" : pctf(dl.dolum_orani, 1))}
        ${pdRow("Ret oranı", ay.red_orani == null ? "" : pctf(ay.red_orani, 1))}
        <p class="hint">Huninin ilk iki basamağı ŞU ANKİ silahlı kümeden, üçüncüsü icra defterinin
        penceresinden gelir — aynı payda değildir ve bu yüzden ayrı etiketlenir.</p>
        <p class="hint">Emirlerin SATIR SATIR dökümü (tetik/stop/hedef/boyut + ayna çipi) aynı
        yüzeyin <b>Kitap · ayrıntı</b> bölümündeki "Sıradaki seans" tablosundadır — kart sayıyı,
        tablo satırları taşır; ikisi aynı yerde dursa kart özet olmaktan çıkardı. P1
        tekilleştirmesi: iki biçim (rozet ve oran çubuğu) ARTIK AYNI YÜZEYDE ve aralarında bir
        adres var; sayının kendisi tek yerde (bu kart), satırın kimliği tek yerde (tablo).</p>
        <div style="margin-top:10px"><button class="dlbtn" type="button" data-act="go"
          data-a1="karar#brifing">Sıradaki seans tablosu →</button></div>
        <div style="margin-top:14px"><button class="dlbtn" type="button" data-act="go"
          data-a1="karar#mutabakat">Mutabakat masası →</button></div>` };
  },
  durumPozisyon(o) {
    const t = o.t || {}, pos = o.pos || [], r = t.regime || {};
    const mes = _durumStopMesafeleri(pos).sort((a, b) => a.pay - b.pay);
    // POZİSYON SATIRLARI BURADA TEKRARLANMAZ: tam tablo (giriş/stop/hedef/adet) bu sayfanın
    // "Kitap · ayrıntı" bölümündedir. Çekmecenin taşıdığı şey o tabloda OLMAYAN ölçümdür —
    // etkin stop mesafesi ve maruziyetin rejim tavanıyla kıyası.
    const mesRows = mes.map(m => `<div class="srow"><span>${esc(m.ticker)}</span>
        <b class="mono-num">${pctf(m.pay, 1)} · ${trn(m.eff, 2)}</b></div>`).join("");
    return { eyebrow: "POZİSYONLAR",
      title: `${trn(pos.length)} açık <span class="mut">×</span> kitap`,
      body: `<div class="pd-stats">
          ${pdStat("AÇIK", trn(pos.length))}
          ${pdStat("AÇIKTAKİ RİSK", t.current_exposure_pct == null ? "—" : "%" + trn(t.current_exposure_pct, 1))}
          ${pdStat("REJİM TAVANI", r.exposure_budget_pct == null ? "—" : "%" + trn(r.exposure_budget_pct),
            r.exposure_budget_pct === 0 ? "warn" : "")}</div>
        ${r.exposure_budget_pct === 0 ? `<p class="pd-warn">Rejim bütçesi <b>%0</b> — kapı bu rejimde
          yeni pozisyon açtırmaz (keşif sondası hariç).</p>` : ""}
        <p class="hint">Pozisyonların satır satır dökümü (giriş · stop · hedef · adet) bu sayfanın
        <b>Kitap · ayrıntı</b> bölümünde; burada o tabloda olmayan ölçüm durur.</p>
        <h3 class="pd-sub">Stop mesafesi <span class="mut">(girişe göre)</span></h3>
        ${mesRows || `<p class="empty">ölçülemedi — giriş/stop seviyesi okunamadı</p>`}
        <p class="hint">Kitapta CARİ FİYAT yok; mesafe girişten etkin stopa (trail varsa trail)
        ölçülür. "Cari fiyata mesafe" yazmak ölçülmemiş bir sayı üretmek olurdu.</p>
        <div style="margin-top:14px"><button class="dlbtn" type="button" data-act="go"
          data-a1="karar#kapilar">Rejim ve kapı ölçütleri →</button></div>` };
  },
  // 0a · REDDEDİLEN GÖNDERİM — triyaj şeridinin işaret ettiği kayıt. Şeridin "N emir reddedildi"
  // cümlesi buraya iner; hangi hisse, broker ne dedi, hangi plandı, ne zaman.
  failsub(f) {
    return { eyebrow: "REDDEDİLEN GÖNDERİM",
      title: `${esc(f.ticker || "?")} <span class="mut">×</span> broker reddi`,
      body: `<p class="pd-warn">${esc(String(f.detail || "Broker gerekçe döndürmedi. Ham yanıt kaydedilmemiş."))}</p>
        ${pdRow("Hisse", esc(f.ticker))}${pdRow("Plan", esc(f.plan_id))}${pdRow("Tarih", esc(f.date))}
        ${pdRow("Kapatıldı", f.ack_ts ? esc(String(f.ack_ts).slice(0, 16)) : null)}
        ${f.ack_ts ? "" : `<div style="margin-top:12px"><button class="dlbtn"
            data-act="ackReject" data-a1="${esc(`${f.plan_id || "?"}·${f.date || "?"}`)}">Bu reddi kapat</button>
          <span class="hint" style="margin:0 0 0 8px">şeritten düşer, kayıt kalır</span></div>`}
        <h3 class="pd-sub">Ne anlama geliyor</h3>
        <p class="mut">Emir Alpaca'ya ulaştı ve geri çevrildi — yerel planda "gönderildi" görünür ama
        broker tarafında karşılığı yok. Ayna dökümü bu yüzden sapma gösterebilir. Plan hâlâ
        Kararlar'da duruyorsa seviyeleri gözden geçirip yeniden silahlandırman gerekir.</p>` };
  },
  // 0b · ALARM — gelen kutusundaki bir grubun tam kaydı
  alert(g) {
    return { eyebrow: "ALARM KAYDI",
      title: esc(g.token || "alarm"),
      body: `${g.message ? `<p class="pd-warn">${esc(String(g.message))}</p>` : ""}
        ${pdRow("Tekrar", g.n > 1 ? `${Number(g.n)} kez` : "1 kez")}
        ${pdRow("İlk görülme", esc(g.first_ts))}${pdRow("Son görülme", esc(g.last_ts))}
        ${pdRow("Düzey", esc(g.level))}${pdRow("Kaynak", esc(g.source))}
        <h3 class="pd-sub">Ham alan dökümü</h3>
        ${Object.entries(g).filter(([k2, v]) =>
            !["token", "message", "n", "first_ts", "last_ts", "level", "source"].includes(k2) &&
            v !== null && v !== undefined && v !== "" && typeof v !== "object")
          .map(([k2, v]) => `<div class="srow"><span class="mono-num">${esc(k2)}</span><b>${esc(String(v))}</b></div>`)
          .join("") || `<p class="empty">ek alan yok</p>`}` };
  },
  // 0c · KARAR AĞACI HÜCRESİ — Operasyon Bölüm 2'deki matrisin bir satırı, tam dökümüyle.
  // Zincirdeki çip "sektör tavanı ✗ 3" der; kaydın kendisi hangi eşiğe hangi değerle çarpıldığını,
  // ölçütün SERT mi YUMUŞAK mı olduğunu ve kapının yazdığı gerekçeyi taşır. Hepsi `gk.plans`
  // paketinden gelir — yeni uç yok, uydurma alan yok: olmayan alanın satırı hiç çizilmez.
  gate(p) {
    const v = p.verdict || "?";
    const ch = p.checks || [];
    const SEV = { hard: "SERT", soft: "yumuşak" };
    const sat = c => `<div class="trow" style="grid-template-columns:150px 62px 1fr">
      <span class="chain">${esc(CHECK_TR[c.check] || c.check || "?")}</span>
      <span><span class="tag ${c.passed ? "t-go" : "t-no"}">${c.passed ? "geçti" : "kaldı"}</span></span>
      <span class="mut" style="font-size:12px">${esc(SEV[c.severity] || c.severity || "")}${
        c.value != null ? ` · ölçülen ${esc(String(c.value))}` : ""}${
        c.threshold != null && c.threshold !== "" ? ` · eşik ${esc(String(c.threshold))}` : ""}${
        c.note ? `<br>${esc(String(c.note))}` : ""}</span></div>`;
    const kalan = ch.filter(c => !c.passed), gecen = ch.filter(c => c.passed);
    return { eyebrow: "KARAR AĞACI",
      title: `${esc(p.ticker || "?")} <span class="mut">×</span> kapı ${esc(v)}`,
      body: `<div class="pd-stats">
          ${pdStat("KAPI", `<span class="tag ${TAG[v] || ""}">${esc(v)}</span>`)}
          ${pdStat("KALAN ÖLÇÜT", kalan.length)}${pdStat("GEÇEN ÖLÇÜT", gecen.length)}</div>
        ${p.exploration ? `<p class="pd-warn">Keşif işlemi — bu satır ≤0,25R'lik bir sonda olarak kuruldu; kapı eşikleri onun için gevşetilmez, boyutu küçültülür.</p>` : ""}
        ${pdRow("Kurulum", esc(p.setup || ""))}${pdRow("Skor", p.score)}
        ${pdRow("LLM görüşü", p.llm_opinion ? `${esc(p.llm_opinion)}${p.llm_veto ? " → <b class=\"neg\">TERFİLİ VETO (dolum düşürüldü)</b>" : " <span class=\"mut\">· danışma katmanı, karara etkisiz</span>"}` : "")}
        ${kalan.length ? `<h3 class="pd-sub">Kaldığı ölçütler</h3>${kalan.map(sat).join("")}` : ""}
        ${gecen.length ? `<h3 class="pd-sub">Geçtiği ölçütler</h3>${gecen.map(sat).join("")}` : ""}
        ${!ch.length ? `<p class="empty">Bu planda yapılandırılmış karar ağacı kaydı yok (gate_checks alanı eklenmeden önce üretilmiş eski plan).</p>` : ""}
        ${(p.reasons || []).length ? `<h3 class="pd-sub">Kapının yazdığı gerekçe</h3>
          ${p.reasons.map(r => `<div class="srow"><span>${esc(r)}</span></div>`).join("")}` : ""}` };
  },
  // 1 · MATRİS KESİTİ — çekmecenin ilk ve asıl çağıranı
  plot({ si, ri }) {
    const d = _PLOTS; if (!d) return null;
    const row = d.grid[si]; if (!row) return null;
    const c = row.cells[ri]; if (!c) return null;
    const rg = REGIME_TR[d.regimes[ri]] || d.regimes[ri];
    const thin = c.n < 10, sc = signClass(c.mean_r, c.n);
    const exits = (c.exits || []).map(([k, n]) =>
      `<div class="srow"><span>${esc(EXIT_TR[k] || k)}</span><b>${n}</b></div>`).join("");
    const rows = (c.recent || []).map(t => `<div class="trow" style="grid-template-columns:58px 1fr 60px">
        <span class="tick">${esc(t.ticker || "—")}</span>
        <span class="mut">${esc(t.closed || "")} · ${t.bars ?? "—"} bar · ${esc(EXIT_TR[t.exit] || t.exit || "—")}</span>
        <span class="mono-num ${cls(t.r)}">${t.r == null ? "—" : isr(t.r, trn(t.r, 2)) + "R"}</span>
      </div>`).join("");
    return { eyebrow: "KESİT DETAYI",
      title: `${esc(row.setup)} <span class="mut">×</span> ${esc(rg)}`,
      body: `<div class="pd-stats">
          ${pdStat("ORTALAMA R", `${c.mean_r > 0 ? "+" : ""}${c.mean_r.toFixed(2)}R`, sc)}
          ${pdStat("İŞLEM", c.n)}${pdStat("TUTAN", `%${Math.round(c.hit * 100)}`)}</div>
        ${thin ? `<p class="pd-warn">Bu kesitte yalnızca ${c.n} işlem var. Ortalamayı bir sonuç değil, bir işaret say — bu kadar az örnekle yön bile güvenilir değil.</p>` : ""}
        ${!sc && !thin ? `<p class="pd-warn">Ortalama, ${c.n} işlemlik örneklemin gürültü bandının (±${(1 / Math.sqrt(c.n)).toFixed(2)}R) içinde. İşareti bir yön olarak okuma — bu kesit henüz ne kazandırıyor ne kaybettiriyor.</p>` : ""}
        <h3 class="pd-sub">Nasıl kapandı</h3>${exits || `<p class="empty">kayıt yok</p>`}
        <h3 class="pd-sub">Son işlemler</h3>${rows || `<p class="empty">kayıt yok</p>`}` };
  },
  // 2 · KAPANMIŞ İŞLEM — defterin tek satırının tam hesabı
  trade(t) {
    const r = Number(t.r_multiple);
    const rTxt = Number.isFinite(r) ? (r >= 0 ? "+" : "") + r.toFixed(2) + "R" : "—";
    return { eyebrow: "İŞLEM KAYDI",
      title: `${esc(t.ticker || "?")} <span class="mut">×</span> ${esc(EXIT_TR[t.exit_reason] || t.exit_reason || "kapandı")}`,
      body: `<div class="pd-stats">
          ${pdStat("SONUÇ", rTxt, cls(r))}
          ${pdStat("K/Z", t.pnl_pct == null ? "—" : isr(t.pnl_pct, pctf(t.pnl_pct, 1)), cls(t.pnl_pct))}
          ${pdStat("BAR", t.bars_held ?? "—")}</div>
        <h3 class="pd-sub">Giriş ve çıkış</h3>
        ${pdRow("Açılış", esc(t.ts_open || ""))}${pdRow("Kapanış", esc(t.ts_close || ""))}
        ${pdRow("Giriş", t.entry == null ? "" : trn(t.entry, 2))}${pdRow("Çıkış", t.exit == null ? "" : trn(t.exit, 2))}
        ${pdRow("Adet", t.qty)}${pdRow("Yön", esc(t.side || ""))}
        ${pdRow("Net K/Z", t.pnl_dollars == null ? "" : money(t.pnl_dollars))}
        ${pdRow("Maliyet", t.costs == null ? "" : money(t.costs))}
        <h3 class="pd-sub">Karar bağlamı</h3>
        ${pdRow("Kurulum", esc(t.setup || ""))}${pdRow("Rejim", esc(REGIME_TR[t.regime] || t.regime || ""))}
        ${pdRow("Skor", t.score)}${pdRow("Beklenen", t.r_multiple_expected == null ? "" : t.r_multiple_expected + "R")}
        ${pdRow("Strateji", t.strategy_version == null ? "" : "v" + String(t.strategy_version).padStart(2, "0"))}
        ${pdRow("Plan", esc(t.plan_id || ""))}
        ${pdRow("Keşif işlemi", t.exploration ? "evet · ≤0.25R sonda" : "")}
        ${pdRow("Kademeli çıkış", t.scaled_out ? "evet" : "")}
        <h3 class="pd-sub">Seyir</h3>
        ${pdRow("En iyi nokta (MFE)", t.mfe_r == null ? "" : `+${t.mfe_r}R`)}
        ${pdRow("En kötü nokta (MAE)", t.mae_r == null ? "" : `−${t.mae_r}R`)}
        ${pdRow("Ayna sapması", t.mirror_divergence == null ? "" : (t.mirror_divergence * 100).toFixed(2) + "%")}
        ${(t.skill_chain || []).length ? `<h3 class="pd-sub">Analiz zinciri</h3>
          <p class="chain" style="line-height:1.8">${esc(t.skill_chain.join(" → "))}</p>` : ""}
        <!-- #39'UN YARIM KALAN YARISI (K1, 2026-07-30): /api/trade/{id} işlemin tam detayını VE
             bar serisini üretiyordu ("drill-down view" için) ama panonun fetch envanterinde HİÇ
             yoktu — yani en pahalı yetim uç bar CSV'leri yükleyip seri üretiyor, kimse istemiyordu.
             Çekmece kaydı istemci tarafında rec('trade',tr) ile kuruluyordu; eksik olan tek şey
             FİYAT SEYRİ'ydi. Placeholder asenkron doldurulur (openRecord → _fillTradeSeries). -->
        ${t.id ? `<h3 class="pd-sub">Fiyat seyri <span class="tx3" style="font-weight:400">(giriş→çıkış penceresi)</span></h3>
          <div id="pd-trade-series" data-trade-id="${esc(String(t.id))}">
            <p class="hint" style="margin:0">seri yükleniyor…</p></div>` : ""}` };
  },
  // 3 · PLAN — kapıya giren aday, gerekçesiyle
  plan(p) {
    const v = p.gate_verdict || "?";
    return { eyebrow: "PLAN KAYDI",
      title: `${esc(p.ticker || "?")} <span class="mut">×</span> ${esc(p.setup || "plan")}`,
      body: `<div class="pd-stats">
          ${pdStat("KAPI", `<span class="tag ${TAG[v] || ""}">${esc(v)}</span>`)}
          ${pdStat("BEKLENEN", p.r_multiple_expected == null ? "—" : p.r_multiple_expected + "R")}
          ${pdStat("BOYUT", p.size_r == null ? "—" : p.size_r + "R")}</div>
        ${p.expired ? `<p class="pd-warn">Bu sinyalin süresi doldu — planlar tek seans geçerlidir${p.age_days != null ? ` ve bu ${p.age_days} seans önce üretildi` : ""}. Bir daha silahlanamaz; ${p.traded ? "işleme dönüşmüştü" : "emre dönüşmedi"}.</p>` : ""}
        ${planOnayBloguHTML(p)}
        <h3 class="pd-sub">Seviyeler</h3>
        ${pdRow("Tetik", p.entry_trigger == null ? "" : trn(p.entry_trigger, 2))}
        ${pdRow("Stop", p.stop == null ? "" : trn(p.stop, 2))}
        ${pdRow("Hedef", (p.targets && p.targets[0]) == null ? (p.profit_target == null ? "" : trn(p.profit_target, 2)) : trn(p.targets[0], 2))}
        ${pdRow("Son kapanış", p.last_close == null ? "" : `${trn(p.last_close, 2)}${p.drift_pct == null ? "" : ` (${p.drift_pct > 0 ? "+" : ""}${trn(p.drift_pct, 1)}%)`}`)}
        <h3 class="pd-sub">Bağlam</h3>
        ${pdRow("Tarih", esc(p.date || ""))}${pdRow("Skor", p.score)}
        ${pdRow("Sektör", esc(p.sector || ""))}${pdRow("Plan rejimi", esc(REGIME_TR[p.regime_at_plan] || p.regime_at_plan || ""))}
        ${pdRow("Uyuyan kurulum", p.dormant_setup ? "evet" : "")}
        ${pdRow("Ayna", p.broker_status === "failed_broker_rejection" ? "broker reddetti" : "")}
        ${pdRow("Gölge P(kazanç)", p.p_win_shadow == null ? "" : `%${Math.round(p.p_win_shadow * 100)}`)}
        ${(p.gate_reasons || []).length ? `<h3 class="pd-sub">Kapı gerekçesi</h3>
          ${p.gate_reasons.map(r => `<div class="srow"><span>${esc(r)}</span></div>`).join("")}` : ""}
        ${(p.skill_chain || []).length ? `<h3 class="pd-sub">Analiz zinciri</h3>
          <p class="chain" style="line-height:1.8">${esc(p.skill_chain.join(" → "))}</p>` : ""}` };
  },
  // 4 · HİPOTEZ — beyin ne önerdi, kapı ne dedi, gerçekte ne oldu
  hyp(h) {
    const [label] = HSTATUS[h.status] || [h.status];
    const b = h.backtest || {};
    return { eyebrow: "HİPOTEZ KAYDI",
      title: `${esc(h.variable || "?")} <span class="mut">${esc(String(h.old ?? "?"))} →</span> ${esc(String(h.new))}`,
      body: `<div class="pd-stats">
          ${pdStat("DURUM", esc(label || "—"))}
          ${pdStat("TAHMİN", h.predicted_delta == null ? "—" : (h.predicted_delta > 0 ? "+" : "") + h.predicted_delta, cls(h.predicted_delta))}
          ${pdStat("GERÇEKLEŞEN", h.realized_delta == null ? "—" : (h.realized_delta > 0 ? "+" : "") + h.realized_delta, cls(h.realized_delta))}</div>
        ${h.rationale ? `<h3 class="pd-sub">Gerekçe</h3><p class="hint" style="margin-top:0">${esc(h.rationale)}</p>` : ""}
        <h3 class="pd-sub">Sınav</h3>
        ${pdRow("Aday OOS", b.candidate_oos)}${pdRow("Mevcut OOS", b.incumbent_oos)}
        ${pdRow("Gerekli marj", b.margin)}${pdRow("Kapı yasası", esc(b.gate_law || ""))}
        ${pdRow("P(ΔS&gt;0)", b.search_p)}${pdRow("Gerekli P", b.search_p_required)}
        ${pdRow("Sondaj sayısı (K)", b.k_probes)}
        <h3 class="pd-sub">Kaynak</h3>
        ${pdRow("Sürüm", h.version_from == null ? "" : `v${String(h.version_from).padStart(2, "0")}${h.version_to ? ` → v${String(h.version_to).padStart(2, "0")}` : ""}`)}
        ${pdRow("Öneren", esc(h.source || ""))}${pdRow("Güven", h.confidence)}
        ${pdRow("Öneri anındaki rejim", esc(REGIME_TR[h.market_regime] || h.market_regime || ""))}
        ${(h.reject_reasons || []).length ? `<h3 class="pd-sub">Ret gerekçesi</h3>
          ${h.reject_reasons.map(r => `<div class="srow"><span>${esc(r)}</span></div>`).join("")}` : ""}` };
  },
  // 5 · OLAY — denetim izinin tek satırı, ham alanlarıyla
  event(e) {
    const name = String(e.event || "");
    const txt = EV_TR[name] ? EV_TR[name](e) : name;
    // Bilinen alanların dışında kalan ne varsa OLDUĞU GİBİ dökülür: akışta yalnız çevrilmiş
    // cümle görünüyordu ve çevirisi olmayan olay tek bir mono adla kalıyordu.
    const skip = new Set(["ts", "level", "event", "message"]);
    const extra = Object.entries(e).filter(([k, v]) => !skip.has(k) && v != null && v !== "")
      .map(([k, v]) => pdRow(esc(k), esc(typeof v === "object" ? JSON.stringify(v) : String(v)))).join("");
    const LVL = { alarm: "alarm", warn: "uyarı", info: "bilgi" };
    return { eyebrow: "OLAY KAYDI",
      title: esc(txt),
      body: `<div class="pd-stats">
          ${pdStat("SEVİYE", esc(LVL[e.level] || e.level || "—"), e.level === "alarm" ? "neg" : (e.level === "warn" ? "warn" : ""))}
          ${pdStat("NE ZAMAN", esc(relTime(e.ts) || "—"))}
          ${pdStat("KAYIT", `<span style="font-size:12px">${esc(name || "—")}</span>`)}</div>
        ${e.message ? `<h3 class="pd-sub">Mesaj</h3><p class="hint" style="margin-top:0">${esc(e.message)}</p>` : ""}
        <h3 class="pd-sub">Ham kayıt</h3>
        ${pdRow("Zaman damgası", esc(String(e.ts || "")))}${extra || ""}` };
  },
};

// ================= PERFORMANS — S2R-2'DE İKİYE BÖLÜNDÜ =======================================
// Eski tek gövde iki farklı soruya cevap veriyordu ve ikisi de yarım kalıyordu:
//   PARA yarısı   — eğri, boyut tavanı/kuyruk riski/ölçülen friksiyon, kapanmış işlem defteri.
//                   Soru: "kitap nerede, ne birikti?"  → Portföy & Emirler'de KALDI.
//   KARNE yarısı  — başarı notu/getiri/düşüş/Sharpe döşemesi, rejim başına kırılım, araç başına
//                   isabet. Soru: "makine öğreniyor mu?"  → Öğrenme'ye taşındı (ADR: "karne").
// Kırılım tabloları Portföy'de dururken hiç kimse onları öğrenme kanıtı olarak okumuyordu; oysa
// "hangi rejimde ne verdi" tam olarak karnenin sorusudur.
// AYNI UÇ, İKİ TÜKETİCİ: ikisi de `/api/performance` okur, yanıt 15 sn önbelleklidir.
RENDER.performans = async () => {
  // ÇIKIŞ VERİMLİLİĞİ TEŞHİS UCUNDA YAŞIYOR (`mlops.exit_efficiency`), performans ucunda değil.
  // İkinci istek JCACHE'ten döner (aynı sayfada `mutabakat`/`brifing` onu zaten çekti); düşerse
  // null gelir ve kart ÖLÇÜLEMEDİ dalına girer — sayfanın geri kalanı çizilmeye devam eder.
  const [d, dg] = await Promise.all([j("/api/performance"), j("/api/diagnostics").catch(() => null)]);
  const eq = (d.equity_curve && d.equity_curve.points) || [];
  $("page-performans").innerHTML = bolumBasHTML("performans", "Birikim · para eğrisi ve defter",
    "Bugüne kadar ne biriktiği: eğri, boyut tavanı, kuyruk riski, ölçülen friksiyon, <b>çıkış "
    + "nedeni kırılımı</b> ve kapanmış işlemlerin tek tek hesabı. Karne (öğreniyor mu?) Öğrenme "
    + "sayfasında.")
    + `<div class="card rise"><h2 class="t">Para eğrisi (paper)</h2>${line(eq)}</div>
    ${riskCard(d.kelly, d.tail_risk, d.slippage_measured, d.benchmark_veto_tally)}
    ${firsatCikisNedeni((dg || {}).mlops)}
    <div class="card rise"><h2 class="t">Son işlemler · tek tek hesap (${d.n_trades ?? 0} toplam)</h2>
      <div class="trow head" style="grid-template-columns:78px 60px 1fr 64px 96px 96px"><span>KAPANIŞ</span><span>HİSSE</span><span>ÇIKIŞ NEDENİ</span><span>R</span><span>REJİM</span><span style="text-align:right">AYNA</span></div>
      ${tradeRows(d.recent_trades || [])}</div>`;
};
// ---- ÖĞRENME · KARNE (hiyerarşinin İLK bölümü: hüküm önce) -----------------------------------
// Üç kaynak tek yüzeyde ve bu birleşme S2R-2'nin asıl kazancı:
//   /api/hermes      → "Öğreniyor mu? — dürüst karne" (yayınlanan/terfi/geri alınan/ölçülen) +
//                      rejim bütçe tetikleyicisi. Eskiden Hermes kartlarının ORTASINDAYDI.
//   /api/performance → başarı notu döşemesi + rejim/araç kırılımı. Eskiden Portföy'ün dibindeydi.
//   /api/agent       → kalibrasyon dağılımı (tahmin tuttu mu?). Eskiden hipotez defterinin içindeydi.
// Üçü de "öğreniyor mu?" sorusunun cevabıydı ve ÜÇ AYRI SAYFADAYDI; operatör hükmü kurmak için
// üç yerden sayı toplamak zorundaydı.
//
// DÖRDÜNCÜ VE BEŞİNCİ KAYNAK (eski Operasyon): `sHermes` Hermes KARNESİ'dir (beynin öneri
// isabeti, MAE profili, gölge-varyant portföyleri) — adı zaten karne ve evi burası. `sNous` onun
// HEMEN ARDINDA kalır: v131'in kurduğu bitişiklik sözleşmesi ("karne = beyin PARAMETRE
// tahminlerinde ne kadar isabetli?", sistem önerileri = ÜST katman, "beyin MEKANİZMALAR hakkında
// ne görüyor?" — yan yana durunca kendini geliştirme döngüsü tek bakışta okunur). Göç o
// bitişikliği BOZMADI, ikisini birlikte taşıdı.
RENDER.karne = async () => {
  // BEŞİNCİ KAYNAK: `/api/summary` — otonomi merdiveni (`ladder`) YALNIZ orada servis ediliyor ve
  // C1-10'un "L0→L1 ne kadar kaldı" bacağı ondan besleniyor. Global `SUMMARY` KULLANILMAZ: onu
  // `RENDER.brifing` (② Karar) yazıyor, yani ④ Öğrenme'ye doğrudan gelen bir operatörde null olur
  // ve kart sessizce "ölçülemedi" derdi — ölçüm değil OKUMA YOLU bozuk olurdu (v190'ın dersi).
  const [L0, p, a, op, sum] = await Promise.all([
    j("/api/hermes").then(x => x || {}).catch(() => null),
    j("/api/performance").catch(() => null),
    j("/api/agent").catch(() => null),
    opParcalar().catch(() => null),
    j("/api/summary").catch(() => null),
  ]);
  const sd = (p || {}).score_detail || {};
  const regRows = Object.entries((p || {}).per_regime || {}).map(([r, v]) => `<div class="trow" style="grid-template-columns:120px 50px 70px 70px 70px">
    <span><span class="tag t-vi">${REGIME_TR[r] || r}</span></span><span class="mono-num">${v.n}</span>
    <span class="mono-num ${cls(v.score)}">${v.score == null ? 'az işlem' : isr(v.score, v.score)}</span><span class="mono-num">${pctf(v.win_rate, 0)}</span>
    <span class="mono-num ${cls(v.avg_r)}">${v.avg_r == null ? '—' : isr(v.avg_r, v.avg_r)}R</span></div>`).join("");
  const skRows = Object.entries((p || {}).per_skill || {}).map(([s, v]) => `<div class="trow" style="grid-template-columns:1fr 60px 80px">
    <span class="chain">${esc(s)}</span><span class="mono-num">${v.n}</span><span class="mono-num">${pctf(v.hit_rate, 0)}</span></div>`).join("");
  // ÖLÇÜLEMEYEN UÇ SESSİZ KALMAZ (YASA 4 + uydurma yasağı): düşen her kaynak kendi kartında
  // "okunamadı" der; boş bir tablo "veri yok" diye okunmaz.
  const L = (L0 || {}).learning || {};
  const karneKart = !L0
    ? `<div class="card rise"><h2 class="t">Öğreniyor mu? — dürüst karne</h2>
        <div class="empty">Karne ucu okunamadı — bu boşluk "öğrenmiyor" DEĞİL, ölçüm YOK demektir.</div></div>`
    : `<div class="card rise"><h2 class="t">Öğreniyor mu? — dürüst karne</h2>
      <p class="hint" style="margin-top:0"><b>${esc(L.verdict || '—')}</b></p>
      ${(() => { const alt = karneAlt(L);
        return `<div class="mrow">
        ${mc("Yayınlanan", L.shipped, null, alt.shipped)}${mc("Terfi eden", L.promoted, "var(--green)", alt.promoted)}${mc("Geri alınan", L.rolled_back, "var(--red)", alt.rolled_back)}${mc("Ölçülen sonuç", L.outcomes_measured, "var(--amber)", alt.outcomes)}</div>`; })()}
      <p class="hint" style="margin-top:8px">Kalibrasyon: ${L.calibration?.n||0} sonuç · isabet ${L.calibration?.hit_rate!=null?pctf(L.calibration.hit_rate,0):'—'} · sürüm v${String(L.current_version??1).padStart(2,'0')} · zamanlayıcı ${(L0.scheduler||{}).active?'<b class="pos">aktif</b>':'<b class="warn">kapalı</b>'} · son seans ${esc((L0.scheduler||{}).portfolio_last_date||'—')}</p>
      ${regimeTriggerRows(L.regime_budget_triggers, L.status_counts, L.overfit_suspects)}</div>`;
  $("page-karne").innerHTML = bolumBasHTML("karne", "Karne · öğreniyor mu?",
    "Hükmün kendisi: kaç değişiklik yayınlandı, kaçı tuttu, kaçı geri alındı; kâğıt defterin "
    + "notu; rejim ve araç başına kırılım; tahminlerin kalibrasyonu. Skor 'ölçülemedi' diyorsa "
    + "<b>ne kadar kaldığı</b> da burada yazar.")
    + karneKart
    + `<div class="mrow rise">
      ${mc("Başarı notu", sd.score, cls(sd.score) === 'pos' ? 'var(--green)' : cls(sd.score) === 'neg' ? 'var(--red)' : 'inherit', "−1…+1")}
      ${mc("Toplam getiri", pctf(sd.total_return, 1), 'var(--green)', "baştan bugüne")}${mc("En sert düşüş", pctf(sd.max_drawdown, 1), 'var(--amber)', "azı iyi")}${mc("Sharpe", sd.sharpe, null, "riske göre getiri")}</div>
    ${!p ? `<div class="card rise"><div class="empty">Performans ucu okunamadı — kırılım tabloları çizilemedi.</div></div>`
      : `<div class="g2 rise">
      <div class="card"><h2 class="t">Piyasa havasına göre kırılım</h2>
        <div class="trow head" style="grid-template-columns:120px 50px 70px 70px 70px"><span>REJİM</span><span>N</span><span>NOT</span><span>KAZANMA %</span><span>ORT R</span></div>
        ${regRows || '<div class="empty">Rejim kırılımı için kapanmış işlem yok.</div>'}</div>
      <div class="card"><h2 class="t">Hangi araç ne kadar isabetli</h2>
        <div class="trow head" style="grid-template-columns:1fr 60px 80px"><span>KAYNAK ARAÇ</span><span>N</span><span>İSABET</span></div>
        ${skRows || '<div class="empty">Araç kırılımı için kapanmış işlem yok.</div>'}</div>
    </div>`}
    <div class="card rise"><h2 class="t">Kalibrasyon — tahmin mi tuttu?</h2>
      ${a ? scatter(a.calibration_scatter) : '<div class="empty">Ajan ucu okunamadı.</div>'}
      ${a && a.calibration && a.calibration.n ? `<p class="scatter-note" style="color:var(--tx2)">Brier <b>${a.calibration.brier}</b> (düşük iyi) · isabet <b>${pctf(a.calibration.hit_rate, 0)}</b> · ${a.calibration.n} sonuçlanan tahmin</p>` : ''}</div>
    ${firsatOlgunlasma(sd, ((L0 || {}).status || {}).horizon, (sum || {}).ladder,
                       ((_DIAG || {}).pipeline || {}).cf_fidelity)}
    ${op ? op.sHermes + op.sNous
         : `<div class="card rise"><div class="empty">Hermes karnesi ve sistem önerileri ölçülemedi — teşhis ucu okunamadı. Bu boşluk "karne boş" DEĞİL, ölçüm YOK demektir.</div></div>`}`;
};
// ---- BOYUT TAVANI · KUYRUK RİSKİ · ÖLÇÜLEN SLİPAJ (K1, 2026-07-30) -------------------------
// `/api/performance` her istekte `kelly_fraction` VE `tail_risk`i hesaplıyordu — ikincisi
// blok-bootstrap SİMÜLASYONU — ve ikisi de hiçbir yerde çizilmiyordu: her sayfa açılışında boşa
// koşan bir hesap. Repo genelinde `kelly|tail_risk|cvar|VaR` için pano tarafında SIFIR eşleşme
// vardı (yedek app.js kopyasında da yok). İki karar: ya çiz ya üretimden çıkar. Çizildi — çünkü
// ikisi de operatörün "ne kadar riske girebilirim / en kötü ne olur" sorusunun doğrudan cevabı.
//
// HEPSİ DANIŞMANDIR, KAPI DEĞİL: Kelly tavanı `sabit-R` boyutlamayı DEĞİŞTİRMEZ (ROADMAP §5:
// fractional Kelly bilinçli olarak YAPMA listesinde — sabit-R zaten ~çeyrek Kelly). Burada
// gösterilmesinin sebebi, gerçekleşen kenarın ima ettiği tavanın mevcut boyutlamayla
// KIYASLANABİLİR olması. full_kelly NEGATİFSE bu "kenar bugün negatif" demektir ve yarım-Kelly
// 0'a kırpılır — o sıfır bir hesap hatası değil, hükümdür.
function riskCard(kelly, tail, slip, veto) {
  kelly = kelly || {}; tail = tail || {}; slip = slip || {}; veto = veto || {};
  const fk = kelly.full_kelly, hk = kelly.half_kelly;
  // ÖLÇÜLEMEDİ ≠ SIFIR: n eşiğin altındaysa arka uç None döner (score.TAIL_MIN_SAMPLE). "—"
  // basılır; 0 basmak "ölçtük, risk yok" gibi okunurdu.
  const num = (v, suf = "") => (v == null ? '<span class="mut">— ölçülmedi</span>' : esc(String(v)) + suf);
  const slipTxt = slip.measured_bps == null
    ? `<span class="mut">— ayna hiç dolmadı (n=${slip.n ?? 0})</span>`
    : `<b class="${Math.abs(slip.measured_bps) > (slip.assumed_bps ?? 0) ? "warn" : "pos"}">${esc(String(slip.measured_bps))} bps</b>`;
  // ÖZET ŞERİDİ HÜCRELEŞTİ (v192). Eski `.mcard` döşemesi dört sayıyı büyük ve RENKLİ basıyordu
  // ama hiçbirinin ÖRNEKLEMİNİ göstermiyordu: 12 işlemlik bir Kelly ile 300 işlemlik bir Kelly
  // ekranda birbirinin aynıydı ve renk (yeşil/kırmızı) o farkı görünmez kılarken bir güven
  // duygusu üretiyordu. Artık her hücre kendi kanıt çubuğunu taşır ve RENK yalnız örneklem
  // "az örnek" eşiğinin ÜSTÜNDEYKEN verilir — matrisin kuralının aynısı, tek fark bandın adı.
  // ÖLÇÜLEMEDİ ≠ SIFIR: arka uç eşiğin altında None döner ve hücre BOŞ çizilir ("VERİ YOK").
  const kn = kelly.n, tn = tail.n;
  const kelPayda = `örneklem · log ölçek, n=${KANIT_TAVAN_N} dolu`;
  return `<div class="card rise"><h2 class="t">Boyut tavanı · kuyruk riski · ölçülen friksiyon
      <span class="tx3" style="font-weight:400">(hepsi DANIŞMAN — hiçbiri kapıya bağlı değil)</span></h2>
    ${ozetSerit([
      ozetHucre("Kelly tavanı (tam)", {
        deger: fk == null ? null : (fk >= 0 ? "+" : "") + fk,
        degerSinif: (fk == null || azOrnek(kn)) ? "" : (fk >= 0 ? "pos" : "neg"),
        oran: kanitOrani(kn), payda: kelPayda,
        meta: `isabet ${pctf(kelly.win_rate, 0)} · K/Z ${num(kelly.win_loss_ratio)} · n=${kn ?? "—"}`,
        rozet: azOrnek(kn) ? "AZ ÖRNEK" : "" }),
      ozetHucre("Yarım Kelly", {
        deger: hk == null ? null : String(hk), oran: kanitOrani(kn), payda: kelPayda,
        meta: `n=${kn ?? "—"} · sabit-R değişmez`,
        rozet: azOrnek(kn) ? "AZ ÖRNEK" : "" }),
      ozetHucre("VaR (%95)", {
        deger: tail.var_r == null ? null : tail.var_r + "R",
        oran: kanitOrani(tn), payda: kelPayda,
        meta: `${tail.horizon ?? "—"} işlem ufku · n=${tn ?? "—"}`,
        rozet: azOrnek(tn) ? "AZ ÖRNEK" : "" }),
      // CVaR ÇUBUĞU BURADA ÖRNEKLEM DEĞİL ŞİDDET TAŞIR ve paydası bunu söyler: beklenen kuyruk
      // kaybının, görülen EN KÖTÜ yola oranı. İki farklı payda aynı şeritte olabilir — yeter ki
      // her çubuk kendi paydasını yazsın; yazmayan çubuk hiç çizilmez.
      ozetHucre("CVaR (%95)", {
        deger: tail.cvar_r == null ? null : tail.cvar_r + "R",
        oran: (tail.cvar_r == null || !tail.worst_r) ? null : tail.cvar_r / tail.worst_r,
        payda: tail.worst_r ? `en kötü yol (${tail.worst_r}R)` : "",
        meta: `en kötü ${num(tail.worst_r, "R")} · n=${tn ?? "—"}`,
        rozet: azOrnek(tn) ? "AZ ÖRNEK" : "" }),
    ], "Boyut tavanı ve kuyruk riski özeti")}
    <p class="hint" style="margin-top:8px">
      Ölçülen slipaj: ${slipTxt} · varsayılan <b>${esc(String(slip.assumed_bps ?? "—"))} bps</b> (goal.slippage_bps)
      ${slip.measured_bps == null ? " — ayna dolu satır üretmeye başlayınca sabit varsayım ilk kez ölçüme karşı sınanır." : ""}
      <br>SPY-veto adayı: <b>${veto.n ?? 0}/${veto.decision_n ?? "—"}</b> gözlem
      ${veto.ready ? '<span class="tag t-go">KARAR EŞİĞİ DOLDU</span>' : '<span class="tag t-no">birikiyor</span>'}
      · SPY'ı geçen ${veto.beat ?? 0} · geçemeyen ${veto.lost ?? 0}
      <span class="tx3">(eşik dolunca "benchmark'ı geçemeyen sürüm ship edilmesin" kuralının kapıya eklenip eklenmeyeceğine VERİYLE karar verilir)</span></p></div>`;
}
// çıkış nedenleri — motorun kodları, insan dilinde (bilinmeyen kod ham gösterilir, gizlenmez)
const EXIT_TR = { stop: "stop", stop_gap: "stop (gap ile)", target: "hedef", target_gap: "hedef (gap ile)",
  time_stop: "zaman aşımı", trail: "iz süren stop", regime_flip: "rejim döndü", breakeven: "başabaş",
  giveback: "kâr geri-verme", eod_markout: "dönem sonu kapanışı", delisted_markout: "veri bitti (delist)" };
function tradeRows(trades) {
  if (!trades.length) return `<div class="empty">Henüz kapanmış işlem yok — ilk pozisyon kapanınca burada hesap verilir.</div>`;
  return trades.slice(0, 15).map(tr => {
    const r = Number(tr.r_multiple);
    const rTxt = Number.isFinite(r) ? (r >= 0 ? "+" : "") + r.toFixed(2) + "R" : "—";
    const div = tr.mirror_divergence != null
      ? `<span class="mono-num ${tr.mirror_divergence > 0.005 ? "warn" : "mut"}">${(tr.mirror_divergence * 100).toFixed(2)}%</span>`
      : '<span class="mut">—</span>';
    // Satır altı sütuna sığar; işlemin geri kalanı (giriş/çıkış fiyatı, MFE/MAE, plan, zincir,
    // maliyet) çekmecede. Kırpmak yerine yanında açmak — matrisin hareketi, defterde.
    const k = rec("trade", tr);
    return `<button ${rowAttrs(k, `${tr.ticker || "?"} · ${String(tr.ts_close || "").slice(0, 10)} · ${rTxt} · ${EXIT_TR[tr.exit_reason] || tr.exit_reason || ""}. Kaydı aç.`)}
      class="trow rowbtn" style="grid-template-columns:78px 60px 1fr 64px 96px 96px">
      <span class="mono-num mut">${esc(String(tr.ts_close || "").slice(0, 10))}</span>
      <span class="tick">${esc(tr.ticker || "?")}</span>
      <span class="mut">${esc(EXIT_TR[tr.exit_reason] || tr.exit_reason || "")}</span>
      <span class="mono-num ${cls(r)}">${rTxt}</span>
      <span><span class="tag t-vi">${esc(REGIME_TR[tr.regime] || tr.regime || "—")}</span></span>
      <span style="text-align:right">${div}</span></button>`;
  }).join("");
}
function line(pts) {
  if (!pts.length) return `<div class="empty">Para eğrisi verisi yok.</div>`;
  const W = 1080, H = 240, pad = 30, ys = pts.map(p => p[1]), mn = Math.min(...ys), mx = Math.max(...ys);
  const sx = i => pad + i / (pts.length - 1) * (W - 2 * pad), sy = v => H - pad - ((v - mn) / ((mx - mn) || 1)) * (H - 2 * pad);
  const path = pts.map((p, i) => `${i ? 'L' : 'M'}${sx(i).toFixed(1)},${sy(p[1]).toFixed(1)}`).join("");
  const base = sy(pts[0][1]);
  const area = `M${pad},${base} ` + pts.map((p, i) => `L${sx(i).toFixed(1)},${sy(p[1]).toFixed(1)}`).join("") + `L${W - pad},${base}Z`;
  return `<svg viewBox="0 0 ${W} ${H}" style="width:100%" role="img" aria-label="Para eğrisi: ${money(pts[0][1])} (${esc(pts[0][0])}) → ${money(pts[pts.length-1][1])} (${esc(pts[pts.length-1][0])})">
    <defs><linearGradient id="eg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="var(--accent)" stop-opacity=".35"/><stop offset="1" stop-color="var(--accent)" stop-opacity="0"/></linearGradient></defs>
    <path d="${area}" fill="url(#eg)"/><path d="${path}" fill="none" stroke="var(--accent)" stroke-width="2"/>
    <text x="${pad}" y="16" fill="var(--tx2)" font-size="11">${money(pts[0][1])} · ${esc(pts[0][0])}</text>
    <text x="${W - pad}" y="16" text-anchor="end" fill="var(--green)" font-size="11">${money(pts[pts.length - 1][1])} · ${esc(pts[pts.length - 1][0])}</text></svg>`;
}

// ================= ONAYLAR (Kararlar sayfasının alt yüzeyi) =================
// Ayrı sayfayken L0'da yapısal olarak boştu ve kullanıcıya "bu nav maddesini yok say" öğretiyordu.
// Artık adayların hemen altında: üstte sistemin ÖNERDİĞİ, altta senin ONAYINI bekleyen.
// ---- ÖRNEKLEM KÜNYESİ + KARAR DAMGASI (v240, 2026-08-13) -------------------------------------
// ÖLÇÜLEN KUSUR (canlı): gelen kutusundaki Eksen-2 önerisi "Strong live performance of 0.918
// avg_r" diyordu; aynı skill eksen-2 teşhisinde `ornek_yetersiz_cf_de_yetersiz` kovasında ve n=1.
// Metni LLM yazıyor (hermes `skill_recommendation`), örneklem eşiği ise yalnız DETERMİNİSTİK
// üreteçte vardı — iki ayrı yol, tek ekran. Pano metni DÜZELTMEZ (uydurma olurdu): sunucunun
// ÖLÇTÜĞÜ künyeyi metnin YANINA koyar, iddia ile ölçü ayrı ayrı okunur.
// ÜÇ HÂL AYRI: yeterli (nötr) · yetersiz (uyarı) · ölçülemedi (uyarı DEĞİL, bilgi) — "eşiği
// geçemedi" ile "ölçemedik" aynı tonda gösterilirse ikisi de inandırıcılığını kaybeder.
function ornekSatiri(it) {
  const o = it.ornek, notu = it.ornek_notu;
  if (!notu && !o) return "";
  const sayi = o ? `n=${o.n ?? "—"}${o.avg_r != null ? ` · ort ${trn(o.avg_r, 3)}R` : ""}`
                   + ` · cf n=${o.n_cf ?? "—"}${o.cf_avg_r != null ? ` · cf ort ${trn(o.cf_avg_r, 3)}R` : ""}` : "";
  const kls = it.ornek_yeterli === false ? "neg" : (it.ornek_yeterli == null ? "mut" : "pos");
  return `<br><span class="hint" style="font-size:11px">Ölçülen örneklem: <b class="${kls}">${
    esc(sayi || "ölçülemedi")}</b>${notu ? ` — ${esc(notu)}` : ""}</span>`;
}

const KARAR_TR = { approve: "KABUL", reject: "RET", bozuk: "OKUNAMIYOR" };
function kararDamgasi(kk) {
  if (!kk) return "";
  if (kk.okunamadi)
    return `<br><span class="hint" style="font-size:11px"><b class="neg">Karar defteri OKUNAMADI</b>
      (${esc(kk.okunamadi)}) — bu "karar yok" DEĞİL, ölçüm yok demektir.</span>`;
  if (!kk.karar)
    return `<br><span class="hint" style="font-size:11px">${esc(kk.not || "")} · kimlik
      <code>${esc(kk.id)}</code></span>`;
  const k = kk.kunye || {}, o = k.ornek || null;
  return `<br><span class="hint" style="font-size:11px">Karar: <b class="${
    kk.karar === "approve" ? "pos" : "neg"}">${esc(KARAR_TR[kk.karar] || kk.karar)}</b>${
    kk.ts ? ` · ${esc(String(kk.ts).replace("T", " ").slice(0, 16))}` : ""}${
    o ? ` · karar anındaki künye: n=${esc(String(o.n ?? "—"))} · cf n=${esc(String(o.n_cf ?? "—"))}` : ""}${
    kk.gerekce ? ` · “${esc(kk.gerekce)}”` : ""} — ${esc(kk.not || "")}</span>`;
}

// Kararı deftere yazar. DAVRANIŞ DEĞİŞTİRMEZ ve bu, düğmenin yanındaki cümlede de yazılı olmalı:
// operatör "onayladım, artık uygulanıyor" sanmamalı. Yanıtın `davranissal` alanı SUNUCUDAN gelir —
// panonun kimlik önekini kendi ayrıştırıp hüküm vermesi, aynı sorunun ikinci kez cevaplanması olurdu.
window.kararKaydet = async (id, decision) => {
  const kutu = eylemKutusu(id);
  if (kutu) kutu.innerHTML = `<span class="mut">kayda geçiriliyor…</span>`;
  try {
    const r = await apiFetch("/api/approvals/" + encodeURIComponent(id), {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ decision, reason: "pano · karar kaydı" }) }).then(x => x.json());
    if (kutu) kutu.innerHTML = `<span class="${decision === "approve" ? "pos" : "neg"}">${
      esc(KARAR_TR[decision] || decision)} deftere yazıldı</span>${
      r && r.davranissal === false ? ` <span class="mut">— ${esc(r.not || "")}</span>` : ""}`;
  } catch (e) {
    eylemHatasiYaz(kutu, e, "karar deftere YAZILMADI — kayıt yapılmadı, öneri hâlâ kararsız.");
    return;   // TAZELEME YOK: yeniden çizim mesajı siler ve ret yine görünmez olurdu (v219 dersi)
  }
  // `_JC.clear()` BURADA YOK ve bu bilinçli: `apiFetch` GET olmayan her istekte önbelleği zaten
  // boşaltıyor (app.js:171). İkinci bir temizlik, "önbelleği kim boşaltır" sorusuna ikinci bir
  // cevap yazmak olurdu — bu turda kapattığımız sınıfın küçük hali.
  await _aktifSayfayiCiz();
};

RENDER.onaylar = async () => {
  // Teşhis ucu merdivenin "neden L0?" satırı için okunur (faz6 kilit zinciri). Ön-yüklü + 15 sn
  // önbellekli; düşerse null gelir ve o satır dürüstçe hiç çizilmez.
  // `/api/today` v195-a'da eklendi: bölümün KENDİ sorusu ("şu an benim onayımı bekleyen ne var?")
  // REVIEW planlarını da kapsıyor ve onlar `todays_plans`ta yaşıyor. Uç zaten önbellekli (15 sn)
  // ve Genel Bakış tarafından ısıtılmış oluyor — yeni bir ölçüm maliyeti yok.
  const [a, s, dg, t] = await Promise.all([j("/api/approvals"), j("/api/summary"),
                                           j("/api/diagnostics").catch(() => null),
                                           j("/api/today").catch(() => null)]);
  const inbox = a.inbox || [];
  const TYPE_TR = { arming: ["SİLAHLANMA", "t-go"], skill_revision: ["REVİZYON", "t-rv"], skill_rec: ["EKSEN-2", "t-vi"] };
  const rows = inbox.map(it => {
    const [lbl, kls] = TYPE_TR[it.type] || [it.type, "t-vi"];
    const btns = (it.actions || []).map(ac => {
      if (it.type === "skill_revision")
        return `<button class="dlbtn" ${ac === "reject" ? 'style="border-color:var(--red);color:var(--red)"' : ""} data-act="skillRev" data-a1="${esc(it.skill)}" data-a2="${ac}">${ac === "apply" ? "Onayla" : "Reddet"}</button>`;
      if (it.type === "skill_rec")
        return `<button class="dlbtn" data-act="applySkillRec" data-a1="${esc(it.skill)}" data-a2="${esc(it.action)}">Uygula</button>`;
      return "";
    }).join(" ");
    // KARAR KAYDI DÜĞMESİ (v240): uygulanabilir karşılığı OLMAYAN öneri artık "görülüp geçilen"
    // bir satır değil. Düğmeler `it.actions`tan DEĞİL `it.karar_kaydi`ndan doğar — `actions`
    // UYGULAMA eylemlerinin listesidir ve oraya kayıt düğmesi koymak, v238'de kapattığımız
    // "uygulanamaz eylemi uygulanabilir gibi sunma" kusurunu geri getirirdi.
    const kk = it.karar_kaydi;
    const kararBtn = kk && !kk.karar
      ? `<button class="dlbtn" data-act="kararKaydet" data-a1="${esc(kk.id)}" data-a2="approve">Kabul · kayda geç</button>
         <button class="dlbtn" style="border-color:var(--red);color:var(--red)" data-act="kararKaydet" data-a1="${esc(kk.id)}" data-a2="reject">Ret · kayda geç</button>`
      : "";
    return `<div class="trow" style="grid-template-columns:96px 1fr auto;align-items:start">
      <span class="tag ${kls}">${lbl}</span>
      <span><b style="font-size:13px">${esc(it.title)}</b><br><span class="chain">${esc(it.evidence || "")}</span>
        ${ornekSatiri(it)}
        ${it.note ? `<br><span class="hint" style="font-size:11px">${esc(it.note)}</span>` : ""}
        ${kk ? kararDamgasi(kk) : ""}
        ${it.skill ? `<p class="hint" data-eylem-msg="${esc(kk ? kk.id : it.skill)}" style="margin:6px 0 0"></p>` : ""}</span>
      <span style="display:flex;gap:6px;flex-wrap:wrap;justify-content:flex-end">${btns}${kararBtn}</span></div>`;
  }).join("");
  // ---- ONAYINI BEKLEYEN REVIEW PLANLARI (v195-a · UX denetimi B4) ----------------------------
  // ÖLÇÜLEN KUSUR: bölümün soru cümlesi "şu an benim onayımı bekleyen ne var?" idi ama yüzey
  // YALNIZ `/api/approvals` gelen kutusunu çiziyordu; REVIEW planlarının onayı Koşu & Döngü →
  // adaylar → satır çekmecesinin İÇİNDE yaşıyordu. Bölüm kendi sorusunu cevaplamıyordu.
  //
  // İKİNCİ ONAY YOLU AÇILMADI — ve bu kasıtlı: satırlar `planRowFull` ile çizilir, tıklama aynı
  // `RECORD_VIEW.plan` çekmecesini açar ve onay düğmesi hâlâ TEK yerde (`planOnayBloguHTML`,
  // iki adımlı). Buraya ikinci bir "Onayla" düğmesi koymak, aynı yazma eylemine ikinci bir kapı
  // açmak olurdu — bu turda Alpaca kartından kaldırdığımız kusurun aynısı.
  //
  // SAYIM PANODA KURULMAZ: `onay_bekliyor` bayrağını sunucu damgalar (api._onay_bekleyen_damgala);
  // burada REVIEW + onaysız + süresi-dolmamış ölçütünü yeniden yazsaydık kart ile bu liste aynı
  // gün ayrışabilirdi.
  const planlar = (t && Array.isArray(t.todays_plans)) ? t.todays_plans : null;
  const bekleyen = planlar ? planlar.filter(p => p && p.onay_bekliyor) : null;
  const planKart = `<div class="card rise"><h2 class="t">Onayını bekleyen planlar${
      bekleyen == null ? "" : ` <span class="tx3" style="font-weight:400">(${bekleyen.length})</span>`}</h2>
    <p class="hint" style="margin-top:0">Kapı <b>REVIEW</b> dediğinde karar sende kalır. Satıra bas:
      plan kaydı açılır, onay düğmesi orada — <b>tek</b> onay yolu, iki adımlı. Onay kapı hükmünü
      DEĞİŞTİRMEZ, planı giriş kuyruğuna alır.</p>
    ${bekleyen == null
      ? `<div class="empty">Plan defteri uçtan gelmedi — <b>ölçülemedi</b>. Bu "bekleyen onay yok"
           DEĞİLDİR; <code>/api/today</code> okunamadı.</div>`
      : (bekleyen.length
          ? _PHEAD + bekleyen.map(planRowFull).join("")
          : `<div class="empty">${planlar.length
              ? `Bu seansta <b>${planlar.length}</b> plan üretildi; onayını bekleyen REVIEW yok
                 (GO'lar zaten giriş kuyruğunda, NO_GO onaylanamaz).`
              : "Bu seansta plan üretilmedi — dürüst boşluk."}</div>`)}</div>`;
  $("page-onaylar").innerHTML = bolumBasHTML("onaylar", "Onay kuyruğu · senden iş isteyenler",
    "Sistemin sana getirdiği her karar türü tek listede, kanıtıyla. Otonomi merdiveni de "
    + "burada: gerçek paraya bir ayarla değil, kanıtla geçilir.")
    + planKart
    + `<div class="card rise"><h2 class="t">Gelen kutusu (${inbox.length})</h2>
      <p class="hint" style="margin-top:0">Adaylar (Koşu &amp; Döngü) bilgi verir; burası iş ister.</p>
      ${rows || '<div class="empty">Bekleyen karar yok — eşik dolduğunda burada belirir (bildirimi de düşer).</div>'}</div>
    ${a.level >= 1 ? `<div class="card rise"><h2 class="t">Canlı emir onayları</h2>
      <div class="empty">${(a.pending || []).length || "kuyruk boş"}</div></div>` : ""}
    ${ladderCard(s.ladder, ((dg || {}).mlops || {}).faz6_kilitleri)}`;
};

// ================= öğrenme antrenmanı (learning sprint) =================
const SPRINT_PHASE_TR = { starting: "başlıyor", baseline: "v1 ileri baz", search: "aday araması",
  candidate: "v2 ileri ölçüm", done: "tamamlandı", stopped: "durduruldu", stopping: "durduruluyor", error: "hata" };
// ---- REJİM BÜTÇE TETİKLEYİCİSİ + KARNENİN OKUNMAYAN İKİ ALANI (K1, 2026-07-30) --------------
// `regime_trigger.py`nin docstring'i amacını "karne API'sine tetikleyici bayrağı" diye tanımlıyor
// ve `analytics.learning_scorecard` onu her istekte hesaplayıp /api/hermes ile taşıyordu — ama
// panoda `regime_budget_triggers` geçişi SIFIRDI. Yani sinyalin VAR OLUŞ NEDENİ olan görünürlük
// hiç kurulmamıştı: "dinamik bütçelemeye geçiş operatör kararı" olan bilgi operatöre ulaşmıyordu.
// Tek seferlik obs.log olayı da EV_TR sözlüğünde çevirisiz — akışta ham adla bir kez akıp kayboluyor.
// Aynı karnenin `overfit_suspects` ve `status_counts` alanları da okunmuyordu; üçü tek satırda.
function regimeTriggerRows(trig, statusCounts, overfit) {
  const rows = Object.entries(trig || {});
  if (!rows.length && !statusCounts && overfit == null) return "";
  // n/eşik + READY rozeti: rejim başına örneklem doluluğu. `ready` alanı ARKA UÇTAN gelir —
  // burada yeniden eşik kıyası yapmak "iki yerde iki hüküm" riski doğururdu (n>=threshold
  // kuralının sahibi regime_trigger.py'dir).
  const trigRows = rows.map(([r, v]) => {
    const n = v.n ?? 0, thr = v.threshold ?? "—", ready = !!v.ready;
    const pct = (typeof thr === "number" && thr > 0) ? Math.min(100, Math.round(n / thr * 100)) : 0;
    return `<div class="trow" style="grid-template-columns:120px 1fr 74px 92px">
      <span><span class="tag t-vi">${REGIME_TR[r] || esc(r)}</span></span>
      <span><span class="bar" style="margin:0"><i style="width:${pct}%"></i></span></span>
      <span class="mono-num">${n}/${thr}</span>
      <span><span class="tag ${ready ? "t-go" : "t-no"}">${ready ? "HAZIR" : "birikiyor"}</span></span></div>`;
  }).join("");
  const scRows = Object.entries(statusCounts || {}).map(([k, v]) =>
    // HSTATUS mevcut sözlüktür ([metin, sınıf] çifti); bilinmeyen durum HAM adla gösterilir —
    // çeviri yoksa gizlemek, karnede sessizce eksik bir sayı bırakırdı.
    `<span class="tag t-vi" style="margin-right:6px">${esc((HSTATUS[k] || [k])[0])}: ${v}</span>`).join("");
  return `<h3 class="pd-sub" style="margin-top:14px">Rejim bütçe tetikleyicisi
      <span class="tx3" style="font-weight:400">(eşiği dolan rejimde dinamik bütçelemeye geçiş OPERATÖR kararı)</span></h3>
    ${trigRows ? `<div class="trow head" style="grid-template-columns:120px 1fr 74px 92px"><span>REJİM</span><span>DOLULUK</span><span>N/EŞİK</span><span>DURUM</span></div>${trigRows}`
      : `<div class="empty" style="font-size:12px">Henüz rejim örneklemi yok.</div>`}
    <p class="hint" style="margin-top:8px">Hipotez durumları: ${scRows || "—"} · aşırı-uyum şüphelisi:
      <b class="${overfit ? "warn" : "pos"}">${overfit ?? "—"}</b></p>`;
}

function sprintCard(sp, learning) {
  sp = sp || {}; const ls = (learning || {}).loop_state;
  const active = !!sp.active, phase = sp.phase || (active ? "çalışıyor" : "kapalı");
  const total = sp.total || 0, prog = sp.progress || 0, pct = total ? Math.min(100, Math.round(prog / total * 100)) : 0;
  const search = sp.search || {}, realized = sp.realized, closed = sp.loop_closed;
  const ph = SPRINT_PHASE_TR[phase] || phase;
  // version + min-sample bound to LIVE API fields (learning.current_version / learning.min_sample) —
  // hardcoded "v1/v2/30" strings silently lied the moment the live strategy moved past v2.
  const lv = (learning || {}).current_version, lvTxt = lv != null ? "v" + lv : "mevcut sürüm";
  const minS = (learning || {}).min_sample ?? "—";
  let echo = "";
  if (ls === "no_ship_v1_stands") echo = `<p class="hint" style="margin-top:0">Canlı durum: <b class="warn">kapıyı geçen öneri yok — ${esc(lvTxt)} duruyor</b>. Antrenman bir adayı kum havuzunda dürüstçe kanıtlayabilir.</p>`;
  else if (ls === "shipped_awaiting_min_sample") echo = `<p class="hint" style="margin-top:0">Canlı durum: <b class="pos">${esc(lvTxt)} yayında</b> — işlem birikiyor.</p>`;
  const tiles = `<div class="mrow">
    ${mc("Aşama", ph, active ? "var(--accent-2)" : null, "kum havuzu")}
    ${mc("Baz ileri işlem", sp.n_v1 ?? "—", null, "kum havuzu bazı")}
    ${mc("Yayınlanan", sp.v2 ? "v" + String(sp.v2).padStart(2, "0") : (sp.shipped === false ? "yok" : "—"), sp.v2 ? "var(--green)" : null, "gate'i geçti")}
    ${mc("Aday ileri işlem", sp.n_v2 != null ? sp.n_v2 : "—", null, `min ${minS}`)}
    ${mc("Kapanış Δ", realized ? (realized.realized_delta >= 0 ? "+" : "") + realized.realized_delta : "—", realized ? (realized.realized_delta >= 0 ? "var(--green)" : "var(--red)") : null, "aday − baz ileri")}</div>`;
  const stepLog = ((search.trace) || []).filter(t => t.passes).map(t =>
    `  <span class="ok">YAYIN</span> ${esc(t.variable)} ${esc(String(t.old))}→${esc(String(t.new))} · oos ${t.candidate_oos} (inc ${t.incumbent_oos}) · folds ${esc(t.fold_wins)}`).join("\n");
  // ---- SON KOŞULAR: `sp.runs` NİHAYET ÇİZİLİYOR (K1, 2026-07-30) ----------------------------
  // `sprint_runs.jsonl` YASA 6 için okuyucuya bağlanmıştı (sprint.py:73 → status().runs) ve
  // gerekçesi "pano zaten sprint.status()'u render ediyor" diye yazılmıştı. Ama pano `.runs`'ı HİÇ
  // OKUMUYORDU: alan ağa çıkıp DOM'a hiç girmiyordu — yani düzeltme, görünürlük amacını
  // karşılamadan yasayı SUSTURMUŞTU (codelaw bu "kağıt tüketiciyi" göremez, çünkü modüller-arası
  // okuma gerçekten vardı). Kağıt tüketici, kopukluğun en sinsi türü: yasa yeşil, ekran boş.
  //
  // TERS ORPHAN DÜRÜSTÇE AYRILIR: defter DİSKTE HİÇ YOK (sprint.py `runs_ledger`). "Henüz koşu
  // yok" ile "defter hiç doğmadı" AYRI cümlelerdir; ikincisini "—" diye göstermek, olmayan bir
  // mekanizmayı "henüz veri yok" gibi okuturdu.
  const runs = sp.runs || [];
  const runRows = runs.length
    ? runs.slice(0, 5).map(r => `<div class="trow" style="grid-template-columns:110px 1fr 70px 90px">
        <span class="mut" style="font-size:11px">${esc(relTime(r.started || r.ts) || "—")}</span>
        <span class="chain">${esc(String(r.variable || r.sid || r.run_id || "—"))}</span>
        <span class="mono-num">${r.evaluated ?? r.n ?? "—"}</span>
        <span><span class="tag ${r.passes || r.status === "ok" ? "t-go" : "t-no"}">${esc(String(r.status || (r.passes ? "geçti" : "—")))}</span></span></div>`).join("")
    : `<div class="empty" style="font-size:12px">${sp.runs_ledger === "YOK"
        ? "sprint_runs.jsonl <b>diskte yok</b> — okuyucu bağlı ama defter hiç doğmadı (ters orphan). Bir sonraki antrenmanda satırın düştüğü doğrulanmalı."
        : "Henüz koşu satırı yok."}</div>`;
  const body = `${active && total ? `<div class="bar" style="margin:10px 0 4px"><i style="width:${pct}%"></i></div><p class="mut" style="font-size:12px">${ph} · ${prog}/${total} seans (%${pct})</p>` : ""}
    ${tiles}
    ${sp.note ? `<p class="hint" style="margin-top:8px"><b>${closed ? "✓ " : ""}${esc(sp.note)}</b></p>` : ""}
    ${stepLog ? `<div class="mono" style="margin-top:10px">${stepLog}</div>` : ""}
    <h3 class="pd-sub" style="margin-top:14px">Son koşular <span class="tx3" style="font-weight:400">(sprint_runs.jsonl · en yeni 5)</span></h3>
    <div class="trow head" style="grid-template-columns:110px 1fr 70px 90px"><span>NE ZAMAN</span><span>DEĞİŞKEN / KOŞU</span><span>DENENEN</span><span>SONUÇ</span></div>
    ${runRows}`;
  return `<div class="card rise" id="sprint-card"><h2 class="t">Öğrenme antrenmanı <span class="tx3" style="font-weight:400">(learning sprint)</span></h2>
    <p class="hint" style="margin-top:0">Kum havuzu · seçim ≤${esc(sp.cutoff || "—")} · ölçüm ${esc(sp.eval_start || "—")}→bugün (ayrık pencereler) · canlı defter dokunulmaz.</p>
    ${echo}<div id="sprint-body">${body}</div></div>`;
}
let _sprintTimer = null;
function _scheduleSprintPoll() {
  clearTimeout(_sprintTimer);
  _sprintTimer = setTimeout(async () => {
    if (!_ogrenmeAcik()) return;
    // re-render picks up fresh sprint status + re-arms poll if still active
    try { await RENDER.hermes(); revealActive(true); }
    catch (e) {   // YASA 4 · işaretli yutma: bir POLL turu düşmesi bir olay değildir (sayfa değişmiş,
                  // uç kısa süre meşgul olabilir). Sessiz kalmaz — yoklama yeniden kurulur ve bir
                  // sonraki tur ya çizer ya da aynı yerden yine dener; durum kutusu ekranda kalır.
      _scheduleSprintPoll();
    }
  }, 5000);
}
window.sprintStart = async () => {
  const budget = +(($("sprint-budget") || {}).value || 12), k_max = +(($("sprint-kmax") || {}).value || 3);
  const btn = $("sprint-start"); if (btn) { btn.disabled = true; btn.textContent = "başlatılıyor… (kum havuzu kuruluyor)"; }
  // BOŞ `catch` KALKTI (v219): düşen bir başlatma düğmeyi süresiz "başlatılıyor…"da bırakıyordu —
  // ekranda çalışıyormuş gibi görünen, aslında hiç başlamamış bir antrenman.
  try { await apiFetch("/api/sprint/start", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ budget, k_max }) }); }
  catch (e) {
    eylemHatasiYaz("sprint-msg", e, "antrenman BAŞLAMADI — kum havuzu kurulmadı.");
    if (btn) { btn.disabled = false; btn.textContent = "Antrenmanı başlat"; }
    return;
  }
  setTimeout(() => { if (_ogrenmeAcik()) RENDER.hermes().then(() => revealActive(true)); }, 800);
};
window.sprintStop = async () => {
  // BOŞ `catch` KALKTI (v219): "Durdur"a basıp koşmaya devam eden bir antrenman, operatörün
  // durdurduğunu sandığı bir antrenmandır.
  try { await apiFetch("/api/sprint/stop", { method: "POST" }); }
  catch (e) { eylemHatasiYaz("sprint-msg", e, "antrenman DURMADI — koşmaya devam ediyor olabilir."); return; }
  setTimeout(() => { if (_ogrenmeAcik()) RENDER.hermes().then(() => revealActive(true)); }, 800);
};

// ---- ÖĞRENME EYLEM ŞERİDİ (2026-07-22) ----------------------------------------------------
// Öğrenme yüzeyinde üç interaktif kontrol vardı ve üçü de üç ayrı kartın DİBİNE gömülüydü:
// "Şimdi düşün" Durum kartında, "Antrenman" sprint kartında, "Görüş dolgusu"+anahtar havuzu
// entegrasyon kartında. Operatör "şu an ne yapabilirim?" sorusunu sayfayı üç kez tarayarak
// cevaplıyordu. Üçü de aynı cinsten: bir işi ELLE başlatırsın, sonucu aşağıdaki kartlarda okursun.
// Artık tek hizada, aynı iskelette: ne yapar → şu an durumu → düğme.
function eylemKutu(baslik, amac, durum, durumSinif, kontrol, ipucuId, ayar) {
  // HİZA: üç kutu da AYNI beş satırlık iskelete oturur — başlık / amaç (esnek) / durum / düğme /
  // ayar+ipucu. Amaç satırı `1fr` olduğu için metinler farklı uzunlukta olsa da altındaki
  // "Durum" ve düğme satırları üç kutuda aynı yükseklikte hizalanır. Serbest akışta bırakıldığında
  // düğmeler üç farklı yükseklikte duruyordu ve şerit "üç ayrı kart" gibi okunuyordu.
  // IZGARA SATIR İÇİNDE DEĞİL CSS'TE (2026-07-28): satır içi `grid-template-rows` stil sayfasının
  // `subgrid` kuralını eziyordu, dolayısıyla üç kutu yine kendi 1fr'ini kendi içeriğine göre
  // bölüyordu ve "Durum" satırları 434/420/434'te kalıyordu. İskelet artık .eylem-serit>.card'da.
  return `<div class="card">
    <h2 class="t" style="margin:0">${baslik}</h2>
    <p class="hint" style="margin:0;min-height:60px">${amac}</p>
    <div class="srow" style="margin:0;border-top:1px solid var(--line);padding-top:8px;min-height:30px">
      <span>Durum</span><b class="${durumSinif || ''}" style="white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${durum}</b></div>
    <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap">${kontrol}</div>
    <div style="min-height:34px">${ayar || ''}<p class="hint" id="${ipucuId}" style="margin:0"></p></div></div>`;
}
function eylemSeridi(d) {
  const s = d.status || {}, sp = d.sprint || {}, it = d.integrations || {};
  const pend = it.backfill_pending;
  const inpStil = "background:var(--card);border:1px solid var(--field);color:var(--tx);border-radius:var(--r-ctl);padding:3px 6px;min-height:44px";

  // 1 · DÜŞÜN — beyni elle çalıştır
  const dusun = `<button class="dlbtn" id="hbtn-reflect" data-act="hermesReflect">Şimdi düşün</button>
    ${s.active ? `<button class="dlbtn" data-act="hermesCtl" data-a1="stop">Durdur</button>`
               : `<button class="dlbtn" data-act="hermesCtl" data-a1="start">Başlat</button>`}`;
  const dusunDurum = s.reflecting ? "düşünüyor…" : (s.active ? "aktif · beklemede" : "pasif");

  // 2 · ANTRENMAN — kum havuzunda aday strateji ara (canlı defter dokunulmaz)
  const antrenman = sp.active
    ? `<button class="dlbtn" data-act="sprintStop">Durdur</button>`
    : `<button class="dlbtn" id="sprint-start" data-act="sprintStart">Antrenmanı başlat</button>`;
  const antAyar = sp.active ? "" : `<p class="hint" style="margin:0 0 4px">bütçe
       <input id="sprint-budget" type="number" value="12" min="4" max="30" style="width:54px;${inpStil}">
       · k_max <input id="sprint-kmax" type="number" value="3" min="1" max="5" style="width:46px;${inpStil}"></p>`;
  const antDurum = sp.active
    ? `${esc(SPRINT_PHASE_TR[sp.phase] || sp.phase || "çalışıyor")}${sp.total ? ` · ${sp.progress || 0}/${sp.total}` : ""}`
    : (sp.v2 ? `v${String(sp.v2).padStart(2, "0")} yayında` : "kapalı");

  // 3 · KANIT DOLGUSU — geçmiş planlara toplu LLM görüşü (sonuç gizli, look-ahead yok)
  const dolgu = `<button class="dlbtn" id="hbtn-backfill" ${pend ? "" : "disabled"} data-act="hermesBackfill"> Görüş dolgusu${pend ? " (" + pend + ")" : ""}</button>`;

  // BAŞLIK KATMANI ERİDİ (S2R-2): şerit kendi `<h1>`ini basıyordu ("Öğrenme. Üç düğme, üç iş.")
  // ve sayfanın h1'i ile aynı ekranda İKİ h1 oluyordu — ekran okuyucuda "bu sayfa neyin sayfası?"
  // sorusu cevapsız kalırdı. Şerit bir BÖLÜM değil, sayfanın KONTROL yüzeyidir: kendi soru
  // cümlesi yok, kendi başlığı da olmaz. Tek satırlık etiket yeter.
  return `<div class="rise eylem-bas"><span class="slabel"><span class="d"></span>ELİNDEKİ EYLEMLER</span>
      <p class="subline">Üç düğme, üç iş. Hepsi kum havuzunda ya da danışma katmanında çalışır —
        hiçbiri canlı kitabı değiştirmez; sonuçları aşağıdaki bölümlerde okursun.</p></div>
    <div class="rise eylem-serit" style="display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px;margin-top:20px;align-items:stretch">
      ${eylemKutu("1 · Düşün", "Beyin, kapanan işlemlere bakıp tek değişkenli bir öneri üretir. Öneri kapıya girer; kapı reddedebilir.", dusunDurum, s.reflecting || s.active ? "pos" : "warn", dusun, "hbtn-msg")}
      ${eylemKutu("2 · Antrenman", "Kum havuzunda aday strateji arar ve ileriye dönük ölçer. Canlı defter dokunulmaz.", antDurum, sp.active ? "pos" : "", antrenman, "sprint-msg", antAyar)}
      ${eylemKutu("3 · Kanıt dolgusu", `Sonucu bilinen ama görüşü olmayan ${trn(pend)} geçmiş plana toplu görüş aldırır (sonuç gizli — geleceğe bakmaz). Kalibrasyon aylar yerine günlerde anlamlılığa ulaşır.`, pend ? `${trn(pend)} plan bekliyor` : (pend === 0 ? "bekleyen yok" : "kuyruk ÖLÇÜLMEDİ"), pend ? "warn" : "", dolgu, "backfill-msg")}
    </div>`;
}
// ---- YEDEK ANAHTAR HAVUZU — DETAY KATMANINA İNDİ (S2R-2 "soruya hizmet" denetimi) ------------
// Kutu bir ANAHTAR YÖNETİMİ yüzeyidir ("hangi kollar çekili, sistem nasıl kurulu?" = Kilitler)
// ve Öğrenme'nin sorusuna ("makine ne öğreniyor?") hizmet etmiyor. Ama eylem şeridiyle aynı
// nefeste okunması gereken bir şey de var: kota dolduğunda beyin sessizce deterministiğe düşüyor
// ve bu kutu o düşüşün ÖNLEMİ. Bu yüzden Kilitler'e TAŞINMADI, bulunduğu yerde mertebesi düştü.
// OKUYUCU KORUNUMU: `/api/hermes/pool_key` ucunun ve `integrations.pool_keys` alanının TEK
// yazma/okuma yüzeyi burasıdır — silinseydi uç öksüz kalırdı.
function havuzKutusuHTML() {
  return detayKatmani("Yedek anahtar havuzu (429 rotasyonu)",
    "Anahtar yönetimi Kilitler & Yapılandırma'nın sorusudur; burada duruyor çünkü kota düşüşünün "
    + "önlemi eylem şeridiyle aynı nefeste okunur. /api/hermes/pool_key ucunun tek yüzeyi budur.",
    `<p class="hint" style="margin-top:0">Aynı sağlayıcıdan yedek anahtar eklersen kota dolduğunda ajan otomatik döner. Değer loglanmaz.</p>
      <div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin-top:8px">
        <select id="pool-prov" style="background:var(--bg);color:var(--tx);border:1px solid var(--field);border-radius:var(--r-ctl);padding:6px 8px;min-height:44px;font-family:var(--mono);font-size:12px">
          <option value="gemini">gemini</option><option value="anthropic">anthropic</option><option value="openrouter">openrouter</option></select>
        <input id="pool-key" type="password" placeholder="yedek API anahtarı" autocomplete="off"
          style="flex:1;min-width:180px;background:var(--bg);color:var(--tx);border:1px solid var(--field);border-radius:var(--r-ctl);padding:6px 8px;min-height:44px;font-family:var(--mono);font-size:12px">
        <button class="dlbtn" data-act="addPoolKey">Havuza ekle</button></div>
      <p class="hint" id="pool-msg" style="margin-top:8px"></p>`);
}

// ================= hermes (düşünme beyni) =================
function intCard(it) {
  if (!it) return "";
  const chip = (on, label) => `<span class="term" style="display:inline-flex;align-items:center;gap:5px;padding:3px 9px;border:1px solid var(--line-2);border-radius:var(--r-ctl);font-family:var(--mono);font-size:11px">
    <span style="width:7px;height:7px;border-radius:var(--r-bar);background:${on ? 'var(--green)' : 'var(--tx3)'}"></span>${label}</span>`;
  const pool = Object.entries(it.pool_keys || {}).map(([p, n]) => `${esc(p)}·${n}`).join(" ") || "yok";
  const pend = it.backfill_pending;
  // ---- DETAY KATMANINA İNDİ (S2R-2) ----------------------------------------------------------
  // MCP/koruma-hook/fallback/prompt-cache çipleri BAĞLANTI TESİSATIDIR: "makine ne öğreniyor?"
  // sorusuna cevap vermezler, "beyin nasıl kurulmuş"a verirler. Ama `integrations.mcp`,
  // `guard_hook`, `prompt_cache` ve `tool_use` alanlarının TEK okuyucusu bu kart — silinseydi
  // dört alan öksüz kalırdı (YASA-6). Mertebesi düştü, kaydı durdu.
  return detayKatmani("Hermes entegrasyonları (Tier 1+2)",
    "Bağlantı tesisatı — bölümün sorusuna değil, beynin kurulumuna cevap verir. "
    + "integrations.mcp / guard_hook / prompt_cache / tool_use alanlarının tek okuyucusu budur.",
    `<div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:4px">
      ${chip(it.mcp, "MCP veri sunucusu")}${chip(it.guard_hook, "koruma hook'u")}
      ${chip(!!it.fallback, "fallback: " + esc(it.fallback || "yok"))}
      ${chip(it.prompt_cache === "1h", "prompt cache " + esc(it.prompt_cache || "—"))}
      ${chip((it.pool_keys && Object.keys(it.pool_keys).length) > 0, "havuz: " + pool)}</div>
    <div class="acct" style="margin-top:14px">
      <div class="r"><span>Görüş dolgusu bekleyen</span><b>${trn(pend)} plan</b></div>
      ${it.tool_use ? `<div class="r"><span>MCP araç kullanımı</span><b>${it.tool_use.with_tools}/${it.tool_use.calls} çağrı · ${it.tool_use.total_tools} araç</b></div>` : ''}</div>
    <p class="hint">Görüş dolgusu düğmesi sayfanın başındaki eylem şeridinde.</p>`);
}

// ---- KARNE SAYAÇLARININ "NEDEN 0?" ALT YAZISI (pano turu 2026-07-31) ------------------------
// Dört sayaç (yayınlanan / terfi / geri alınan / ölçülen sonuç) sabit alt yazılarla çiziliyordu:
// "gate'i geçen değişiklik", "tuttuğu doğrulanan". Sayı 0 iken bu bir TANIM'dır, CEVAP değil —
// operatör panodan "sayaç mı ölü, mekanizma mı yok?" sorusunu ayıramıyordu (§3.0 ⑦). Alt yazı
// artık 0 iken KARNENİN KENDİ ALANLARINDAN türer; sayı doluyken eski tanım kalır.
// UYDURMA YOK: türetilemeyen alan cümleyi kısaltır, doldurmaz.
function karneAlt(L) {
  const sc = L.status_counts || {};
  const nHyp = Object.values(sc).reduce((a, b) => a + (Number(b) || 0), 0);
  const red = Object.entries(sc).filter(([s2]) => String(s2).startsWith("rejected"))
    .sort((a, b) => b[1] - a[1]);
  const enSik = red.length ? `${esc(red[0][0])} (${red[0][1]})` : null;
  const terfi = ((L.besleme || {}).antrenman || {}).terfi || {};
  return {
    shipped: L.shipped ? "gate'i geçen değişiklik"
      : (!nHyp ? "defterde hiç hipotez yok — sayaç ilk aramayla dolmaya başlar"
               : `${nHyp} hipotezin hiçbiri kapıyı geçmedi${enSik ? ` · en sık eleme: ${enSik}` : ""}`),
    promoted: L.promoted ? "tuttuğu doğrulanan"
      : (!L.shipped ? "hiç ship yok — terfi ancak yayınlanmış bir sürümde ölçülür"
        : (terfi.n_live != null
           ? `gölge model ${terfi.n_live}/${terfi.promote_min_n ?? "—"} canlı çiftte — terfi eşiği dolmadı`
           : `${L.outcomes_measured ?? 0} sonuç ölçüldü; terfi sonucun TUTMASINI ister`)),
    rolled_back: L.rolled_back ? "kötüleşince iade"
      : (!L.shipped ? "hiç ship yok — geri alınacak sürüm de yok"
                    : "yayınlanan hiçbir sürüm geri alınmadı — bu iyi haber, arıza değil"),
    outcomes: L.outcomes_measured ? "gerçeğe bağlanan"
      : (!L.shipped ? "hiç ship yok — ölçülecek evrim yok"
                    : `min örneklem ${L.min_sample ?? "—"} kapanmış işlem bekleniyor`),
  };
}
// Eksen-2 kovalarının adı = sebebin kendisi. Bilinmeyen kova HAM adıyla gösterilir (gizlenmez).
const KOVA_TR = {
  korumali: "korumalı (motor içi)",
  gercek_katman_olculmemis: "gerçek katman hiç ölçülmemiş",
  gercek_katman_olculmemis_cf_dolu: "gerçek katman ölçülmemiş · cf defteri dolu",
  ornek_yetersiz_cf_de_yetersiz: "örneklem yetersiz (cf de yetersiz)",
  ornek_yetersiz_gercek_katman_yarim: "örneklem yetersiz · gerçek katman yarım",
  esik_araliginda: "eşik aralığında — öneri doğurmaz",
  esik_araliginda_cf_destekli: "eşik aralığında · cf destekli",
  shadow_esigi_asildi: "gölge eşiği aşıldı",
  shadow_esigi_asildi_cf_destekli: "gölge eşiği aşıldı · cf destekli",
  lean_in_esigi_asildi: "öne çıkarma eşiği aşıldı",
  lean_in_esigi_asildi_cf_destekli: "öne çıkarma eşiği aşıldı · cf destekli",
  zaten_golgede: "zaten gölgede",
};
// "Öneri yok" cümlesi ÖLÇÜMDEN gelir. Eski metin ("yeterli işlem birikince çıkar") bir VAATTİ ve
// yanlıştı: üreteç 2026-07-30'a kadar hiçbir üretim yolunda değildi, yani hiç koşmuyordu — işlem
// birikse de öneri çıkmazdı. Kaynak: /api/diagnostics `ogrenme.eksen2` (öğrenme turu ekledi).
function eksen2Bos(eksen2, olcumVar) {
  if (!olcumVar) return "Şu an net bir beceri önerisi yok. Üretecin durumu ÖLÇÜLEMEDİ — teşhis ucu okunamadı.";
  if (!eksen2) return "Şu an net bir beceri önerisi yok — Eksen-2 kadansı HİÇ koşmamış (durum defteri yazılmamış).";
  const kv = Object.entries(eksen2.kovalar || {}).sort((a, b) => b[1] - a[1]);
  const dokum = kv.length
    ? kv.slice(0, 4).map(([k, n]) => `${esc(KOVA_TR[k] || k)}: ${n}`).join(" · ") : null;
  const esik = (eksen2.esik || {});
  return `Şu an net bir beceri önerisi yok. Üreteç en son ${esc(String(eksen2.ts || "—").replace("T", " ").slice(0, 16))} koştu ve `
    + `${eksen2.uretilen ?? 0} öneri üretti (${eksen2.kaydedilen ?? 0} kaydedildi, ${eksen2.bekleyen_toplam ?? 0} bekleyen).`
    + (dokum ? `<br><span class="chain">skiller hangi kolda elendi: ${dokum}</span>` : "")
    + (esik.min_n != null ? `<br><span class="chain">eşik: n≥${esc(esik.min_n)} · gölge ≤${
        esc(esik.shadow_avg_r)}R · öne çıkar ≥${esc(esik.lean_in_avg_r)}R</span>` : "");
}

RENDER.hermes = async () => {
  // Teşhis ucu ZATEN ön-yüklenir (PREFETCH) ve 15 sn önbelleklidir — bu ikinci istek çoğu zaman
  // ağa hiç çıkmaz. Düşerse null döner ve boş kart "ölçülemedi" der, sebep UYDURMAZ.
  const [d, dg] = await Promise.all([j("/api/hermes"), j("/api/diagnostics").catch(() => null)]);
  const s = d.status || {}, sp = d.spend || {};
  const BRAIN_TR = { claude: "Claude", nous: "Nous Hermes", gemini: "Gemini",
                     deterministic: "deterministik önerici (ücretsiz)" };
  const claude = s.brain && s.brain !== "deterministic";   // "LLM beyni aktif" anlamında
  const brain = (BRAIN_TR[s.brain] || s.brain || "—") + (claude ? " (anahtar hazır)" : " · anahtar yok");
  const state = s.reflecting ? '<b class="pos">düşünüyor…</b>' : (s.active ? '<b class="pos">aktif · beklemede</b>' : '<b class="warn">pasif</b>');
  const left = s.trades_until_next;   // server-computed (baseline = trade count at the last reflection)
  // Strict-AND horizon gate: trade count alone is NOT the trigger anymore. When the count is satisfied
  // but the regime-scoped horizon still blocks, saying "hazır" would be dishonest — show the real gate.
  const hz = s.horizon || null;
  let nextTxt;
  if (left == null) nextTxt = '—';
  else if (left > 0) nextTxt = left + ' işlem sonra';
  else if (hz && !hz.ready) {
    const regTxt = hz.regime ? `${esc(REGIME_TR[hz.regime] || hz.regime)} rejiminde ` : '';
    nextTxt = `ufuk bekleniyor · ${regTxt}${hz.trades}/${hz.trades_needed} işlem · ${hz.span_days}/${hz.min_days} gün`;
  } else nextTxt = 'hazır';
  const sq = s.search || {};
  let searchTxt = "";
  if (s.reflecting) {
    if (sq.phase === "incumbent" || !sq.total)
      searchTxt = "temel (incumbent) OOS hesaplanıyor… (~1 dk)";   // a slow baseline must not look like a hang
    else
      searchTxt = `${sq.i}/${sq.total} aday${sq.variable ? ` · ${esc(sq.variable)} → ${esc(String(sq.new ?? ''))}` : ''}`
        + `${sq.candidate_oos != null ? ` · oos ${sq.candidate_oos}` : ''}`
        + `${sq.best ? ` · <span class="pos">en iyi ${esc(sq.best.variable)}</span>` : ''}`;
  }
  const searchRow = s.reflecting ? `<div class="r"><span>Arama ilerlemesi</span><b>${searchTxt}</b></div>` : '';
  const lastR = s.last_reflection ? `${esc(s.last_reflection.replace('T',' ').slice(0,16))} · <b>${esc(s.last_result || '—')}</b>${s.last_variable ? ' · ' + esc(s.last_variable) : ''}` : 'henüz yok';
  const over = sp.over_budget;
  const cards = (d.recent || []).map(h => {
    const [label, kls] = HSTATUS[h.status] || [h.status, "s-rj"];
    return `<div class="hyp"><div class="top"><span class="v">${esc(h.variable || '?')}</span><span class="st ${kls}">${label}</span></div>
      <h3 style="font-size:14px">${esc(h.variable || '')} ${esc(h.old ?? '?')} → ${esc(h.new ?? '?')}</h3>
      <p>${esc(h.rationale || '')}</p></div>`;
  }).join("");
  const ACT_TR = { shadow: "Gölgeye al", activate: "Aktifleştir", lean_in: "Öne çıkar" };
  const recCards = (d.skill_recommendations || []).map(rc => {
    // UYGULANABİLİRLİK SUNUCUDAN OKUNUR (v238, 2026-08-13). Burada eylem adlarını ELLE saymak
    // (eski satır: `rc.action === "shadow" || rc.action === "activate"`) uygulayıcı kümesinin
    // DÖRDÜNCÜ kopyasıydı; Onaylar gelen kutusundaki kopya bu listeyi hiç taşımadığı için orada
    // `lean_in` için "Uygula" düğmesi çiziliyor ve sunucu reddi ekrana ulaşmıyordu. Ölçüt artık
    // `skills.eylem_uygulanabilir` — yükte `uygulanabilir` alanı olarak gelir. Yedek dal
    // (alan gelmezse) YİNE eski davranışı verir ama BEYANLIDIR: eski bir arka uçla konuşan pano
    // düğmeyi kaybetmesin diye, uydurma bir "uygulanabilir" değeri üretmesin diye.
    const applyable = (rc.uygulanabilir != null)
      ? !!rc.uygulanabilir
      : (rc.action === "shadow" || rc.action === "activate");
    const notu = rc.uygulanamama_notu
      || "Bilgi amaçlı — bu araca daha çok yaslan; uygulanacak bir düğme YOK (davranışsal karşılığı yok).";
    // ÖRNEKLEM + KARAR DAMGASI BURADA DA OKUNUR (v240) ama DÜĞME YOK: karar yazma yolu TEK
    // yerdedir (Onaylar → gelen kutusu), tıpkı plan onayının tek yolu gibi. İki yüzey aynı
    // gerçeği göstermeli — damga yalnız gelen kutusunda olsaydı, operatör kararını verdikten
    // sonra bu kart aynı öneriyi hâlâ kararsız gösterirdi.
    return `<div class="hyp"><div class="top"><span class="v">${esc(rc.skill)}</span><span class="st ${rc.action === 'shadow' ? 's-rb' : 's-ok'}">${esc(ACT_TR[rc.action] || rc.action)}</span></div>
      <p>${esc(rc.rationale || '')}</p>
      <p class="hint" style="margin:4px 0 0;font-size:11px">${ornekSatiri(rc).replace(/^<br>/, "")}</p>
      ${applyable ? `<button class="dlbtn" style="margin-top:8px" data-act="applySkillRec" data-a1="${esc(rc.skill)}" data-a2="${esc(rc.action)}">${esc(ACT_TR[rc.action])} · uygula</button>
        <p class="hint" data-eylem-msg="${esc(rc.skill)}" style="margin:6px 0 0"></p>`
                  : `<p class="hint" style="margin-top:4px">${esc(notu)}${
                      rc.karar_kaydi ? `${kararDamgasi(rc.karar_kaydi)}<br><span style="font-size:11px">Karar düğmesi <b>Onaylar → Gelen kutusu</b>ndadır (tek karar yolu).</span>` : ""}</p>`}</div>`;
  }).join("");
  $("ogrenme-eylem").innerHTML = eylemSeridi(d);
  // MLOPS + ÖĞRENME ÇARKI BURAYA GELDİ (S2R-2): eski Operasyon'un "Bölüm 3 · MLOps & Hermes" ve
  // "Öğrenme çarkı · hipotez hunisi" kartları, beynin/sprintin sağlığını ölçüyor — "sistem
  // sağlıklı mı?" değil "makine ne öğreniyor?" sorusuna aitler ve beynin durumuyla aynı yüzeyde
  // okunmaları gerekiyordu (ısınma termometresi sprint kartının ta kendisini besliyor).
  const op = await opParcalar().catch(() => null);
  $("page-hermes").innerHTML = bolumBasHTML("hermes", "Düşünen beyin · sprint",
    `${d.skill_count ?? "—"} beceri okunuyor · ${claude ? esc(BRAIN_TR[s.brain] || s.brain) : "deterministik önerici (LLM anahtarı yok)"}`)
    + `<div class="g2 rise">
      <div class="card"><h2 class="t">Durum</h2>
        <div class="acct" style="margin-top:4px">
          <div class="r"><span>Beyin</span><b>${esc(brain)}</b></div>
          ${(() => {
            // BEYİN ERİŞİLEBİLİRLİĞİ (2026-07-22): kota dolduğunda sistem sessizce deterministik
            // önericiye düşüyordu ve pano yalnız "beyin: nous" yazdığı için ÜÇ GÜNLÜK kesinti
            // görünmüyordu. Artık hangi sağlayıcının neden devre dışı olduğu okunuyor.
            const av = s.brain_availability || {};
            // ÖLÇÜM ARIZASI BİR SAĞLAYICI DEĞİLDİR (2026-07-26): hesap düştüğünde arka uç artık
            // `{error: "<sınıf>"}` döndürüyor (hermes_runtime._brain_availability) — bu anahtarı
            // çip döngüsüne sokmak "error" adında bir beyin UYDURURDU. Ayrı satır olarak okunur:
            // "hiç sağlayıcı yok" ile "hangi sağlayıcının hazır olduğu ÖLÇÜLEMEDİ" aynı şey değil.
            if (av.error) return `<div class="r"><span>Sağlayıcı durumu</span><b class="neg">ÖLÇÜLEMEDİ (${esc(av.error)})</b></div>`;
            const names = Object.keys(av);
            if (!names.length) return "";
            const chips = names.map(n => {
              const a = av[n] || {};
              const kls = a.ready ? "t-go" : (a.credentials ? "t-no" : "t-vi");
              const not = a.cooling_s ? ` ${Math.round(a.cooling_s / 60)}dk` : (a.credentials ? "" : " anahtar yok");
              // MODEL KİMLİĞİ ÇİPTE (2026-07-26): `brain_availability.model_id` üretiliyordu ama
              // hiçbir yüzey OKUMUYORDU — oysa "üç beyin" bir sayım değil bir VARSAYIMDI ve iki
              // yeşil çipin arkasında tek kota olduğu ancak burada görünür. `null` = ölçülemedi
              // (yerel ajan modu, NOUS_MODEL boş): boş bırakılır, varsayılan UYDURULMAZ.
              const mid = a.model_id ? `<span class="mut" style="font-size:10px"> ${esc(a.model_id)}</span>` : "";
              const tip = esc((a.reason || (a.ready ? "hazır" : "kullanılamıyor"))
                + " · model: " + (a.model_id || "ölçülemedi (yerel ajan kendi yapılandırmasını kullanıyor)"));
              return `<span class="gc ${a.ready ? "p" : "f"}" title="${tip}">${esc(n)}${esc(not)}${mid}</span>`;
            }).join(" ");
            return `<div class="r"><span>Sağlayıcı durumu</span><b>${chips}</b></div>` +
              (s.brain_degraded
                ? `<div class="r"><span>Öneri katmanı</span><b class="neg">DETERMİNİSTİK — LLM beyni yok</b></div>`
                : "");
          })()}
          <div class="r"><span>Model</span><b>${esc(s.model || '—')}</b></div>
          <div class="r"><span>Durum</span>${state}</div>
          <div class="r"><span>Kapanan işlem</span><b>${s.closed_trades ?? '—'}</b></div>
          <div class="r"><span>Sonraki otomatik düşünme</span><b>${nextTxt}</b></div>
          ${searchRow}
          <div class="r"><span>Son düşünme</span><b style="font-weight:500;font-size:12px">${lastR}</b></div>
        </div>
        <p class="hint" style="margin-top:12px">${d.autostart ? 'Uygulama açılınca otomatik başlar (yerel).' : 'Otomatik başlatma kapalı.'} · Düğmeler yukarıdaki eylem şeridinde.</p></div>
      <div class="card"><h2 class="t">Harcama (bu ay)</h2>
        <div class="acct" style="margin-top:4px">
          <div class="r"><span>Harcanan</span><b class="${over ? 'neg' : ''}">${money(sp.spent_usd)}</b></div>
          <div class="r"><span>Aylık bütçe</span><b>$${sp.budget_usd ?? '—'}</b></div>
          <div class="r"><span>Kalan</span><b class="${over ? 'neg' : 'pos'}">$${sp.remaining_usd ?? '—'}</b></div>
          <div class="r"><span>Çağrı sayısı</span><b>${sp.calls_this_month ?? 0}</b></div>
          <!-- Düşünen modellerin gizli akıl yürütme tokenları: üretim tavanından yenir ve faturalanır
               ama candidatesTokenCount'ta görünmez. Ölçülmediyse "—" (0 yazmak uydurma olurdu). -->
          <div class="r"><span>Düşünce token'ı</span><b>${sp.thought_tokens ?? '— ölçülmedi'}</b></div>
          <div class="r"><span>Bütçe durumu</span><b class="${over ? 'neg' : 'pos'}">${over ? 'DOLDU — deterministiğe düşer' : 'uygun'}</b></div>
        </div>
</div>
    </div>
    ${sprintCard(d.sprint, d.learning)}
    ${/* KARNE KARTI BURADAN ÇIKTI (S2R-2): hüküm, Öğrenme hiyerarşisinin İLK bölümüdür
          (`karne`) ve orada performans kırılımlarıyla + kalibrasyonla yan yana durur. Burada
          kalsaydı aynı dört sayaç iki bölümde iki kez okunurdu. */""}
    <div class="card rise"><h2 class="t">Beceri önerileri · Eksen-2 <span class="tx3" style="font-weight:400">(${(d.skill_recommendations||[]).length} · sen onaylarsın)</span></h2>
      <div class="lstack" style="margin-top:10px">${recCards
        || `<div class="empty">${eksen2Bos(((dg || {}).ogrenme || {}).eksen2, !!dg)}</div>`}</div></div>
    <div class="card rise"><h2 class="t">Son parametre önerileri</h2>
      <div class="lstack" style="margin-top:10px">${cards || '<div class="empty">Henüz öneri yok — "Şimdi düşün"e bas.</div>'}</div></div>
    ${op ? op.s3 + op.sOzDeg + op.sCark : `<div class="card rise"><div class="empty">MLOps, öz-değerlendirme ve öğrenme çarkı ölçülemedi — teşhis ucu okunamadı. Bu boşluk "mekanizma yok" DEĞİL, ölçüm YOK demektir.</div></div>`}
    ${firsatMaliyetKarnesi(d)}
    ${hermesTelemetriKarti(d.integrations)}
    ${havuzKutusuHTML()}
    ${intCard(d.integrations)}`;
  if (d.sprint && d.sprint.active) _scheduleSprintPoll();        // live progress while a sprint runs
  if (d.status && d.status.reflecting) _hermesReflectPoll();     // live probe progress while a search runs
};
window.applySkillRec = async (skill, action) => {
  // BOŞ `catch` KALKTI — BU TURUN ÖLÇÜLEN KUSURUNUN MERKEZİ (v219). L1'de uygulama kapısı
  // `rec:{beceri}` kimliği için onay defterine bakar ve onay yoksa 409 + gövdede ≥20 karakterlik
  // `[kimlik] gerekçe` döner (api.py `_ONAY_RET_NEDEN`). Eski gövde o reddi yutuyordu: operatör
  // "Uygula"ya basıyor, sunucu gerekçesiyle reddediyor, EKRANDA HİÇBİR ŞEY OLMUYORDU. Kimlik
  // gerekçenin İÇİNDE geliyor ve operatörün `POST /api/approvals/{id}`ye geçireceği dizge o —
  // bu yüzden metin kırpılmadan basılır.
  const kutu = eylemKutusu(skill);
  if (kutu) kutu.innerHTML = `<span class="mut">uygulanıyor…</span>`;
  try {
    await apiFetch("/api/skills/apply", { method: "POST", headers: { "Content-Type": "application/json" },
                                          body: JSON.stringify({ skill, action }) });
  } catch (e) {
    eylemHatasiYaz(kutu, e, (e && e.status === 409)
      ? "ONAY KAPISI REDDETTİ — onay defterinde bu öneri kimliği için 'approve' satırı yok (ya da 'reject' var); eylem UYGULANMADI (fail-closed)."
      : "eylem uygulanamadı — beceri durumunu tazeleyip doğrula.");
    return;   // TAZELEME YOK: yeniden çizim mesajı siler ve ret yine görünmez olurdu
  }
  await _aktifSayfayiCiz();   // düğme Onaylar'da da var — sabit `RENDER.hermes()` görünmeyen sayfayı tazelerdi
};
window.hermesReflect = async () => {
  const btn = $("hbtn-reflect"), msg = $("hbtn-msg");
  if (btn) { btn.disabled = true; btn.textContent = "arıyor… (birkaç dakika)"; }
  if (msg) msg.textContent = "koordinat-iniş araması — tüm düğmeler aynı OOS kapısından geçiriliyor…";
  try {
    const r = await apiFetch("/api/hermes/reflect", { method: "POST" }).then(x => x.json());
    if (r.status === "busy") { if (msg) msg.textContent = "zaten bir düşünme sürüyor"; if (btn) btn.disabled = false; return; }
    _hermesReflectPoll();   // runs in the background (minutes) — poll status, re-render when it lands
  } catch (e) { if (msg) msg.innerHTML = `<span class="neg">${esc(e.message)}</span>`; if (btn) btn.disabled = false; }
};
window.hermesBackfill = async () => {
  const btn = $("hbtn-backfill"), msg = $("backfill-msg");
  if (btn) { btn.disabled = true; btn.textContent = "dolgu başlıyor…"; }
  try {
    const r = await apiFetch("/api/hermes/backfill", { method: "POST" }).then(x => x.json());
    if (msg) msg.innerHTML = `<span class="pos">${esc(r.detail || 'başladı')}</span> — arka planda görüş biriktiriliyor; kalibrasyon güncellendikçe karnede görünür.`;
  } catch (e) { if (msg) msg.innerHTML = `<span class="neg">${esc(e.message)}</span>`; if (btn) btn.disabled = false; }
};
window.addPoolKey = async () => {
  const prov = ($("pool-prov") || {}).value, key = ($("pool-key") || {}).value, msg = $("pool-msg");
  if (!key) { if (msg) msg.innerHTML = '<span class="warn">anahtar boş</span>'; return; }
  try {
    const r = await apiFetch("/api/hermes/pool_key", { method: "POST",
      headers: { "content-type": "application/json" }, body: JSON.stringify({ provider: prov, key }) }).then(x => x.json());
    if ($("pool-key")) $("pool-key").value = "";
    if (msg) msg.innerHTML = r.ok ? `<span class="pos">${esc(r.detail)}</span>` : `<span class="neg">${esc(r.detail)}</span>`;
    if (r.ok) { await RENDER.hermes(); revealActive(true); }
  } catch (e) { if (msg) msg.innerHTML = `<span class="neg">${esc(e.message)}</span>`; }
};
let _hermesTimer = null;
function _hermesReflectPoll() {
  clearTimeout(_hermesTimer);
  _hermesTimer = setTimeout(async () => {
    if (!_ogrenmeAcik()) return;
    // re-render every tick so the live probe progress (i/total, current knob, best-so-far) actually moves;
    // RENDER.hermes re-arms this poll while the search is still running.
    try { await RENDER.hermes(); revealActive(true); } catch (e) { _hermesReflectPoll(); }
  }, 8000);
}
window.hermesCtl = async (action) => {
  // BOŞ `catch` KALKTI (v219): "Başlat"/"Durdur" düğmesi sunucu reddettiğinde de aynı görünüyordu
  // ve beynin gerçek hâli yalnız bir sonraki tazelemede ortaya çıkıyordu.
  try { await apiFetch("/api/hermes/" + action, { method: "POST" }); }
  catch (e) { eylemHatasiYaz("hbtn-msg", e, `beyin kontrolü UYGULANMADI (${String(action || "?")}).`); return; }
  await RENDER.hermes(); revealActive(true);
};

// ================= ayarlar / anahtarlar =================
const SRC_TR = { env: "ortam değişkeni", file: "yerel kasa", gcp: "Secret Manager" };
const KEY_GROUPS = [
  ["Veri", "Piyasa taraması ve haber verisi. Yalnızca veri — işlem açmaz.", [
    ["FMP_API_KEY", "FMP anahtarı", "Financial Modeling Prep (stable API). Girince tarama + haber verisi açılır.", "fmp"],
    ["FMP_API_KEY_2", "FMP yedek anahtarı", "İKİNCİ bir FMP anahtarı (ayrı ücretsiz hesaptan). Birincil günlük kotayı (429) doldurunca motor OTOMATİK buna geçer — günlük kotayı ikiye katlar ve 'çalışmıyor'un ana sebebi olan kota tükenmesini erteler. Ayrı bir e-postayla ikinci bir ücretsiz FMP hesabı açıp o anahtarı buraya gir. Kaydedince kendi 'Test et'i çıkar.", "fmp_backup"],
    ["FINVIZ_API_KEY", "Finviz Elite token", "Finviz Elite 'auth' token'ı — otonom aday keşfi için evreni genişletir (karar vermez). elite.finviz.com'da bir ekran aç → export linkine tıkla → adres çubuğundaki URL'de auth=... kısmındaki değeri kopyala. Yalnız 'hangi hisselere bakılsın' listesini büyütür; kararı yine kapı (OOS sınavı) verir. Token yoksa/dolunca sistem sessizce REPLAY evrenine düşer. Kaydedince Test et çıkar.", "finviz"],
    ["MASSIVE_API_KEY", "Massive API Key", "Günlük EOD bar yenilemesinin TEK ÇAĞRILIK kaynağı: Massive'in grouped-daily ucu tüm ABD piyasasının o günkü barlarını bir istekte verir. Bugün aynı iş sembol başına bir FMP isteği harcıyor ve 250 sembollük tek tazeleme FMP'nin günlük kotasının tamamını yakıyor; anahtar girilince bar tarafı buraya taşınır ve FMP kotası bilgi katmanına (temel veri, insider, kazanç, haber) kalır. Anahtar yoksa hiçbir şey bozulmaz — zincir FMP→Cboe→Nasdaq ile aynen sürer. Kaydedince Test et çıkar.", "massive"],
  ]],
  ["Öğrenme beyni", "Beyin zinciri: HERMES_BRAIN_ORDER sırasıyla anahtarı hazır ilk sağlayıcı konuşur; hata olursa zincir bir sonrakine düşer; hiçbiri yoksa ücretsiz deterministik önerici. Hangi beyin konuşursa konuşsun yalnız ÖNERİR — kapı (OOS sınavı) karar verir.", [
    ["HERMES_BRAIN_ORDER", "Beyin sırası", "Örn: gemini,nous,claude — boşsa claude,nous,gemini."],
    ["HERMES_API_KEY", "Claude (Anthropic) anahtarı", "Claude API anahtarı. Aylık bütçe kapısı ile korunur."],
    ["ANTHROPIC_API_KEY", "Anthropic anahtarı (alternatif)", "Hermes anahtarı yoksa bu kullanılır."],
    ["NOUS_API_KEY", "Nous Portal anahtarı (opsiyonel)", "YEREL hermes-agent kuruluysa anahtar gerekmez — motor onu doğrudan çağırır. Bu anahtar yalnız bulut (Portal) modunda kullanılır.", "nous"],
    ["NOUS_ENDPOINT", "Nous modu (opsiyonel)", "Boş = yerel hermes-agent varsa YEREL, yoksa Portal. 'local' = yereli zorla. URL = o OpenAI-uyumlu uca bağlan."],
    // BEYİN ÇEŞİTLİLİĞİ KALDIRACI OPERATÖRDE (2026-07-27): "3 beyin" bir SAYIM değil varsayımdı —
    // nous ve gemini ayağı aynı model kimliğine gidebiliyor ve zincir üç ayaklı görünüp tek beyin
    // oluyordu. Alanın kendisi zaten vardı; eksik olan, tek bir metin girişinin ölçümü nasıl
    // düzelttiğinin YAZILI olmasıydı. 4. eleman ("nous") mevcut sır-alanı desenidir: alan ayarlıysa
    // keyField Test düğmesini çıkarır → /api/secrets/test/nous → hermes.ping_brain("nous").
    // YENİ UÇ YOK; var olan uca bağlandı.
    //
    // GEREKÇE DÜZELTMESİ (v244, 2026-08-14) — BU METİN HATAYI ÜRETTİ, sonra da anlattı.
    // Eski metin ölü bir adı ÖRNEK OLARAK öneriyordu ve "girildiğinde beyin çeşitliliği ölçümü
    // kendiliğinden düzelir" diyordu. İkisi birlikte bir tuzaktı: operatör tam bu satıra bakarak o
    // adı girdi, ad OpenRouter'ın 411 modelinden HİÇBİRİ DEĞİLDİ (hiç var olmadı) ve 24 saatte 33
    // çağrının 33'ü boş döndü (~354 sn israf). Çeşitlilik ölçütü (`same_model_ids`) yine de
    // "düzelmiş" göründü — çünkü o ölçüt İKİ ADIN FARKLI OLMASINI sayar, ikinci adın CEVAP
    // VERDİĞİNİ değil. Yani metnin vaat ettiği "düzelme" gerçekleşti ve ölçü YANILTTI.
    // Kanıt: docs/TESHIS-BEYIN-ZINCIRI-ERISILEMEZ-MODEL-2026-08-13.md.
    // Yeni örnek TAHMİN DEĞİL ÖLÇÜM: `nvidia/nemotron-3-ultra-550b-a55b:free` canlıda dolu cevap
    // verdi (838 ms, tam JSON uyumu, 1M bağlam, araç desteği, ücretsiz katman).
    ["NOUS_MODEL", "Nous modeli (opsiyonel)", "Boşsa {default}. Google-dışı ücretsiz model (ölçülmüş örnek: nvidia/nemotron-3-ultra-550b-a55b:free — canlıda dolu cevap verdiği doğrulandı). UYARI: adı değiştirmeden ÖNCE o modelin gerçekten ERİŞİLEBİLİR olduğunu doğrula — kimlik (OpenRouter anahtarı) + sağlayıcı yönlendirmesi + o modelden alınmış DOLU bir cevap. Çeşitlilik ölçütünün (same_model_ids) boşalması YETMEZ: o ölçüt iki adın farklı olmasını sayar, ikincisinin cevap verdiğini değil — hiç var olmayan bir ad da ölçüyü 'düzelmiş' gösterir. Test düğmesi nous ayağını canlı yoklar.", "nous"],
    ["NOUS_FALLBACK_MODEL", "Yedek model (opsiyonel)", "Birincil model cevapsız kalırsa (kota/RPM) ajan bir kez bu modelle dener — düşüş zinciri."],
    ["GEMINI_API_KEY", "Gemini anahtarı", "Google AI Studio anahtarı (aistudio.google.com/apikey). Kaydedince YEREL hermes-agent da otomatik Gemini 3.1 Pro'ya geçer — terminal adımı yok; anahtarı silersen ajan eski Nous ayarına döner.", "gemini"],
    ["GEMINI_OAUTH_TOKEN", "Gemini OAuth token (alternatif)", "Kendi OAuth akışından gelen Bearer token — süresi dolunca kendi aracınla yenilersin; motor yalnız kullanır."],
    // `{default}` KODDAN doldurulur (/api/secrets → model_defaults → hermes.GEMINI_DEFAULT_MODEL).
    // Sabit metin "gemini-2.5-pro" yazıyordu, kod ise 3.1-pro koşuyor: çelişik varsayılan beyanı.
    ["GEMINI_MODEL", "Gemini modeli (opsiyonel)", "Boşsa {default}."],
  ]],
  ["Bildirim", "Alarm ve önemli olayları telefonuna iletir (isteğe bağlı).", [
    ["TELEGRAM_BOT_TOKEN", "Telegram bot token", "BotFather'dan alınan bot anahtarı."],
    ["TELEGRAM_CHAT_ID", "Telegram chat ID", "Mesajın gideceği sohbet kimliği."],
    ["MERIDIAN_WEBHOOK_URL", "Webhook URL (alternatif)", "Telegram yerine kendi webhook adresin."],
  ]],
  ["Kağıt broker", "Alpaca KAĞIT hesabı (sanal para). Girmen CANLI işlemi AÇMAZ — sistem L0 kağıt modunda kalır, motor içsel simülatörü kullanır. Not: Alpaca genelde Key ID + Secret ister (Secret üretimde bir kez gösterilir; görmediysen anahtarı yeniden üret). Yalnızca Endpoint + Key'in varsa ikisini gir, Secret'ı boş bırak.", [
    ["ALPACA_PAPER_ENDPOINT", "Endpoint (isteğe bağlı)", "Boş bırakılırsa paper-api.alpaca.markets kullanılır."],
    ["ALPACA_PAPER_KEY", "Key (API Key ID)", "Alpaca panosundaki API anahtarı (paper). Kaydedince Test et çıkar.", "alpaca"],
    ["ALPACA_PAPER_SECRET", "Secret (varsa)", "Alpaca Secret Key — sende yoksa boş bırak."],
  ]],
];
function keyField(name, label, desc, st, provider) {
  st = st || {};
  const status = st.set
    ? `<span class="pos">✓ ayarlı</span> <span class="tx3">(${SRC_TR[st.source] || st.source || ""})${st.hint ? " " + esc(st.hint) : ""}</span>`
    : `<span class="tx3">— ayarlı değil</span>`;
  const del = (st.set && st.source === "file")
    ? `<button class="dlbtn" data-act="clearSecret" data-a1="${name}">Sil</button>` : "";
  const test = (provider && st.set)
    ? `<button class="dlbtn" data-act="testKey" data-a1="${provider}" data-a2="${name}">Test et</button>` : "";
  return `<div class="keyrow">
    <div class="kmeta"><b>${esc(label)}</b><span class="tx3" style="font-size:11px">${esc(desc)}</span>
      <span class="kstat" id="kstat-${name}">${status}</span></div>
    <div class="kin">
      <input type="password" id="key-${name}" placeholder="anahtarı yapıştır…" autocomplete="new-password" spellcheck="false" autocapitalize="off">
      <button class="dlbtn" data-act="saveSecret" data-a1="${name}">Kaydet</button>${del}${test}</div></div>`;
}
// ---- AYNAYA GÖNDERİM GERİ BİLDİRİMİ (v195-a · UX denetimi B1/Ö1) -----------------------------
// ÖLÇÜLEN KUSUR: `alpacaSubmit` her geri bildirim satırını `#alp-msg` üzerinden yazıyordu ve O
// ÖĞE DİYE BİR ŞEY YOKTU (grep: 0 eşleşme; kardeşleri `#intraday-arm-msg`, `#fsub-msg`,
// (Kimlik dizgisi bu yorumda TIRNAKSIZ anılır: kabın TEK kez üretildiğini sayan test, kendi
//  mezar taşını ikinci bir üretim sanmamalı.)
// `#plan-onay-msg` VARDI). Yani "Silahlı planları Alpaca'ya gönder" düğmesi ne "gönderiliyor…" ne
// "N emir gönderildi" ne de hatayı yazıyordu — AMGN "onay→gönderim kopukluğu" vakasının mekanik
// açıklaması budur.
//
// DÜZLEŞTİRMENİN İKİNCİ YOLU DA BU KARTTAN KALKTI (v195-a · B3/Ö3). Kartta "■ Tüm Alpaca
// pozisyonlarını kapat" düğmesi vardı ve Kademe 3 · FLATTEN ile AYNI ucu (close_all, aynı onay
// jetonu) çağırıyordu — ama TEK confirm ile, `opFlatten` ÇİFT onay isterken. Üstelik müdahale
// paneli ekranda "üçü de aynı gövdeyi çağırır, ikinci bir yetki yolu yoktur" yazıyordu: dördüncü
// yüzey vardı ve kapısı en zayıf olanıydı. Bir ucun kapısı, ona giden EN ZAYIF yolun kapısıdır.
// Düğme kaldırıldı, yerine ADRES bırakıldı — yol kaybolmadı, yetki tek yerde toplandı.
//
// MESAJ NEDEN MODÜL DURUMU (kabın kendisi yetmez): başarılı gönderim `RENDER.ayarlar()` çağırıyor
// ve o çizim kartı BAŞTAN yazıyor; üstelik `_alpacaSonra()` 1,4 sn sonra kartı İKİNCİ kez
// değiştiriyor. Mesaj yalnız DOM'da yaşasaydı iki kez silinirdi — yani düzeltmenin kendisi
// sessizce geri alınırdı. Sonuç KALICIDIR: şablon `_ALP_MSG`i okur, her yeniden çizim onu geri
// koyar. Boş dize = "bu oturumda gönderim denenmedi" (uydurma bir başarı satırı değil).
let _ALP_MSG = "";
const ALP_GONDER_ETIKET = "Silahlı planları Alpaca'ya gönder";
function alpMsgYaz(html) {
  _ALP_MSG = html || "";
  const m = $("alp-msg");
  if (m) m.innerHTML = _ALP_MSG;
}
// Alpaca kartının HTML'i — RENDER.ayarlar'dan AYRILDI (2026-07-28) ki görünüm bu dış
// çağrının arkasında beklemesin. Saf fonksiyon: veri girer, HTML çıkar, DOM'a dokunmaz.
function _alpacaKartHTML(a) {
  if (!a) return "";
  const acc = a.account;
    if (a.paper_available && acc) {
      const on = a.backend === "alpaca_paper";
      const posRows = (acc.positions || []).map(p => `<div class="trow" style="grid-template-columns:60px 60px 1fr 90px"><span class="tick">${esc(p.symbol)}</span><span class="mono-num">${p.qty}</span><span class="mut">giriş ${esc(p.avg_entry)}</span><span class="mono-num ${(+p.upl)>=0?'pos':'neg'}">${(+p.upl>=0?'+':'')}${esc(p.upl)}</span></div>`).join("");
      const ordRows = (acc.open_orders || []).map(o => `<div class="trow" style="grid-template-columns:60px 1fr 90px"><span class="tick">${esc(o.symbol)}</span><span class="mut">${esc(o.side)} ${o.qty} ${esc(o.type)}</span><span class="mono-num">${esc(o.stop||o.limit||'')}</span></div>`).join("");
      return `<div class="card rise"><h2 class="t">Alpaca kağıt hesabı ${acc.connected?'<span class="pos" style="font-size:12px">● bağlı</span>':'<span class="neg">bağlı değil</span>'}</h2>
        <p class="hint" style="margin-top:0">${esc(a.note||'')}</p>
        <div class="acct" style="margin-top:6px">
          <div class="r"><span>İcra arka-ucu</span><b class="${on?'pos':''}">${on?'ALPACA PAPER (aktif)':'içsel simülatör'}</b></div>
          <div class="r"><span>Hesap sermayesi</span><b>$${acc.equity!=null?trn(acc.equity,2):'—'}</b></div>
          <div class="r"><span>Nakit / alım gücü</span><b>$${acc.cash!=null?trn(acc.cash,0):'—'} / $${acc.buying_power!=null?trn(acc.buying_power,0):'—'}</b></div>
          <div class="r"><span>Açık pozisyon / emir</span><b>${(acc.positions||[]).length} / ${(acc.open_orders||[]).length}</b></div>
          ${(() => {
            // P6 TEKİLLEŞTİRMESİ (D2-b · baseline §2): "Ayna sapması var mı?" İKİ yerde, İKİ
            // FARKLI SÖZCÜKLE yazılıyordu — durum ızgarasının "sapma/ayna uyumlu" satırı ve
            // burası ("fiyat SAPMA · pozisyon SAPMA"), üstelik farklı sayfalarda ve aynı
            // `rc.mirror_drift` alanından. İki sözcük dağarcığı aynı gerçeği iki ayrı olay gibi
            // gösteriyordu. Değerin TEK EVİ mutabakat masasıdır; bu kart artık sapmayı
            // TEKRARLAMAZ, ADRES verir — harici pozisyon gibi YALNIZ burada olan bilgi kalır.
            const rc = a.reconcile || {};
            if (!rc.date) return '';
            const harici = ((rc.positions || {}).external || []);
            return `<div class="r"><span>Ayna uzlaştırma (${esc(rc.date)})</span>
              <b>${harici.length ? `harici: ${esc(harici.join(', '))} · ` : ''}<button class="dlbtn"
                type="button" data-act="go" data-a1="karar#mutabakat"
                style="min-height:0;padding:2px 8px;font-size:11px">mutabakat masası →</button></b></div>`;
          })()}</div>
        ${posRows?`<div class="tbl" style="margin-top:10px"><div class="trow head" style="grid-template-columns:60px 60px 1fr 90px"><span>HİSSE</span><span>ADET</span><span>GİRİŞ</span><span>K/Z</span></div>${posRows}</div>`:''}
        ${ordRows?`<div class="tbl" style="margin-top:8px"><div class="trow head" style="grid-template-columns:60px 1fr 90px"><span>HİSSE</span><span>EMİR</span><span>SEVİYE</span></div>${ordRows}</div>`:''}
        <div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:12px;align-items:center">
          <button class="dlbtn" data-act="alpacaSubmit">${esc(ALP_GONDER_ETIKET)}</button>
          <span class="hint" id="alp-msg" style="margin:0">${_ALP_MSG}</span></div>
        <p class="hint" style="margin-top:10px;display:flex;gap:8px;flex-wrap:wrap;align-items:center">
          <span>Pozisyon kapatma bu kartta <b>yok</b>: tek yolu <b>Kademe 3 · FLATTEN</b> ve o kol
          çift onay ister.</span>
          <button class="dlbtn" type="button" data-act="go" data-a1="kilitler#mudahale">Müdahale kademeleri →</button></p></div>`;
    }
  return "";
}

RENDER.ayarlar = async () => {
  // ALPACA KARTI GÖRÜNÜMÜ BEKLETMEZ (2026-07-28). /api/alpaca DIŞ bir çağrıdır — Alpaca'nın kendi
  // API'si, ölçüm 1,3-1,4 sn. Eskiden tüm Ayarlar sayfası onun arkasında bekliyordu (ölçüm:
  // 1.442 ms), oysa /api/secrets 30 ms'de dönüyor. Hızlı olan yavaşın arkasına zincirlenmez:
  // sayfa hemen çizilir, broker kartı geldiğinde YERİNE oturur. Bu, go()'ya uygulanan kuralın
  // aynısı — sadece bir kademe içeride.
  const d = await j("/api/secrets");
  const sec = d.secrets || {};
  let alpacaCard = `<div class="card rise" id="alpaca-kart" style="margin-top:16px" aria-busy="true">
    <h2 class="t">Alpaca kağıt hesabı</h2><p class="hint">broker sorgulanıyor…</p></div>`;
  const _alpacaSonra = async () => {
    try {
      const a = await j("/api/alpaca");
      const html = _alpacaKartHTML(a);
      const el = $("alpaca-kart");
      if (!el) return;
      if (!html) { el.remove(); return; }
      // GÖRÜNMEZ BÖLÜM TUZAĞI: kart `.rise` taşıyor ama revealActive() ÇOKTAN koştu, dolayısıyla
      // sonradan enjekte edilen düğüm `.in` sınıfını hiç alamaz ve opacity:0'da kalır — DOM'da
      // var, ekranda yok. Ölçüldü: 8 `.rise` öğesinin 7'si `.in` alıyordu, eksik olan buydu.
      // `outerHTML` yerine komşu ekleyip eskisini silmek, yeni düğüme REFERANS bırakır.
      el.insertAdjacentHTML("afterend", html);
      const yeni = el.nextElementSibling;
      el.remove();
      // ANINDA GÖRÜNÜR, GEÇİŞE BAĞLI DEĞİL: `.rise.in` bir CSS geçişiyle açılır ve geçiş
      // animasyon karesi ister. Sonradan enjekte edilen bu kartta ölçüldü — kart `.rise.in`
      // taşıdığı ve `.rise.in{opacity:1}` eşleştiği halde opacity 1 sn boyunca 0'da kaldı,
      // çünkü kare üretilmediğinde geçiş başlangıç değerinde donuyor. revealActive(true) aynı
      // sorunu `transition:none` ile çözüyor; burada da onu kullanıyoruz. Kart zaten ağdan
      // sonra iniyor — ayrıca bir açılış animasyonu oynatmasının bir değeri yok.
      if (yeni) { yeni.style.transition = "none"; yeni.getBoundingClientRect(); yeni.classList.add("in"); }
    } catch (e) { $("alpaca-kart")?.remove(); }
  };

  // VARSAYILAN MODEL ADI KODDAN GELİR (K1, 2026-07-30): açıklama metni "Boşsa gemini-2.5-pro."
  // yazıyordu, kod ise `GEMINI_DEFAULT_MODEL = "gemini-3.1-pro"` koşuyor (operatör tercihi
  // 2026-07-19). Operatör alanı boş bıraktığında panonun söylediği model ile GERÇEKTE koşan model
  // farklıydı — panoya bakarak "hangi model koşuyor?" sorusunun cevabı YANLIŞ okunuyordu.
  // Metin artık `/api/secrets` → `model_defaults` üzerinden sabitin KENDİSİNDEN türetilir; sabit
  // değişince pano kendiliğinden doğru söyler, elle senkron tutulacak ikinci bir yer kalmaz.
  // YER TUTUCU, DESEN DEĞİL: metinde `{default}` işareti aranır. İlk yazımda "Boşsa <ad>." kalıbını
  // regex ile değiştirmeyi denedim ve model adının KENDİSİ nokta içerdiği için ("gemini-2.5-pro")
  // desen yanlış yerde kesiyordu — kırılgan çıkarım yerine açık işaret.
  const md = d.model_defaults || {};
  const _defTxt = (n, dsc) => dsc.includes("{default}")
    ? dsc.replace("{default}", md[n] || "(kodda tanımlı varsayılan)") : dsc;
  const groups = KEY_GROUPS.map(([title, sub, keys]) => `
    <div class="card rise"><h2 class="t">${esc(title)}</h2>
      <p class="hint" style="margin-top:0">${esc(sub)}</p>
      <div class="ktbl">${keys.map(([n, l, dsc, prov]) => keyField(n, l, _defTxt(n, dsc), sec[n], prov)).join("")}</div></div>`).join("");
  $("page-ayarlar").innerHTML = bolumBasHTML("ayarlar", "Yapılandırma · API anahtarları",
    "Anahtarlar bu bilgisayarda yalnızca senin okuyabileceğin bir dosyada saklanır "
    + "(<code>state/secrets.json</code>, izin 0600) — <b>koda, loga veya ekrana asla yazılmaz</b>; "
    + "sadece son 4 hanesi maskeli gösterilir. Kaydettikten sonra kutu temizlenir.")
    + `<div class="card rise" style="border-color:${d.live_enabled ? 'var(--red)' : 'var(--line-2)'}">
      <div style="display:flex;gap:10px;align-items:baseline;flex-wrap:wrap">
        <b>· Güvenlik durumu</b>
        <span class="tx3">Canlı işlem: <b class="${d.live_enabled ? 'neg' : 'pos'}">${d.live_enabled ? 'AÇIK' : 'kapalı'}</b> · Otonomi: <b>${onk("L", d.autonomy_level)}</b> · Mod: ${
          /* SABİT "paper" KALDIRILDI (v196/KALEM-1): GÜVENLİK DURUMU kartı modu KODA ÇAKILMIŞ bir
             dizeden okuyordu — yani `MERIDIAN_MODE=live` olduğu gün, modun doğruluğunu iddia eden
             kartın kendisi "paper" yazmaya devam ederdi. Alan artık uçtan ölçülür. */
          modJetonu(d.mode)}</span></div>
      <p class="hint" style="margin-top:8px">${esc(d.note || '')} Canlı yalnızca iki güvenlik bayrağı (MERIDIAN_MODE=live + MERIDIAN_I_ACCEPT_RISK=true) elle ayarlanır ve otonomi ≥ L1 olursa açılır — bu ekran bunları değiştirmez.</p></div>
    ${alpacaCard}
    ${groups}
    ${/* DIŞA AKTARIM ÖĞRENME'DEN BURAYA TAŞINDI (S2R-2): CSV/özet/durum-yedeği/teşhis-paketi ve
          bildirim testi "makine ne öğreniyor?" sorusuna değil, "sistem nasıl kurulu, elimde ne
          var?" sorusuna aittir. Detay katmanında, çünkü günlük okuma yüzeyi değil — ama TEK
          yüzeyi burasıdır: altı uç (report.csv, digest, digest/weekly, state/snapshot,
          debug_export, notify/test) ve /halt sayfası başka hiçbir yerden erişilemez. */""}
    ${detayKatmani("Dışa aktarım · teşhis paketi · bildirim testi",
      "Günlük okuma yüzeyi değil, elindeki araçlar. Öğrenme sayfasından buraya taşındı: "
      + "CSV, günlük/haftalık özet, durum yedeği, sansürlü teşhis zip'i ve telefon HALT sayfası.",
      disaAktarHTML())}
    ${glossaryCard()}`;
  // DOM YAZILDIKTAN SONRA (2026-07-28): bu çağrı eskiden innerHTML'den ÖNCEYDİ. Yanıt önbelleğe
  // girdikten sonra /api/alpaca anında dönüyor, dolayısıyla kart ESKİ DOM'a yazılıyor ve hemen
  // ardından innerHTML her şeyi siliyordu — kart ilk açılışta görünüp sonraki render'da
  // kayboluyordu. İlk açılışta hata GÖRÜNMÜYORDU çünkü ağ çağrısı gerçekten yavaştı (1,4 sn) ve
  // yazımdan SONRA iniyordu; yarışı gizleyen tam da o yavaşlıktı.
  _alpacaSonra();
};
// GÖNDERİM SONUCU SATIRI — mutlu-yol YASAK. Uç `{ok, submitted, results[], detail}` döner ve
// `results` her plan için ayrı bir hâl taşır: kabul, dedup (zaten aynada), gap-vetosu (BİZİM
// kararımız — broker reddi değil, ret dağılımına yazılmaz), ulaşılamadı (plan SİLAHLI kalır) ve
// broker reddi. Beşi tek "N gönderildi" cümlesine sıkıştırılırsa operatör, planının neden aynada
// olmadığını ekrandan öğrenemez. `submitted` YOKSA "0" yazılmaz: ölçülemedi ≠ sıfır.
function _alpSonucSatiri(r) {
  if (r.ok === false)
    return `<span class="warn">gönderilmedi — ${esc(r.detail || "sunucu gerekçe bildirmedi")}</span>`;
  const rs = Array.isArray(r.results) ? r.results : [];
  const dedup = rs.filter(x => x && x.dedup).length;
  const veto = rs.filter(x => x && x.veto).length;
  const kopuk = rs.filter(x => x && x.reachable === false).length;
  const ret = rs.filter(x => x && !x.ok && !x.dedup && !x.veto && x.reachable !== false);
  const n = r.submitted;
  const parca = [n == null
    ? `<span class="warn">gönderim sayısı ölçülemedi — uç <code>submitted</code> alanını vermedi (0 DEĞİL)</span>`
    : (n ? `<span class="pos">✓ ${trn(n)} emir gönderildi</span>` : `0 emir gönderildi`)];
  if (dedup) parca.push(`${dedup} dedup (zaten aynada)`);
  if (veto) parca.push(`${veto} gap-vetosu (bizim kararımız, broker reddi değil)`);
  if (kopuk) parca.push(`<span class="warn">${kopuk} ulaşılamadı — plan SİLAHLI kaldı</span>`);
  if (ret.length) parca.push(`<span class="neg">${ret.length} ret: ${
    esc(ret.map(x => `${x.ticker || "?"} — ${String(x.detail || "gerekçe bildirilmedi")}`)
          .join(" · ").slice(0, 240))}</span>`);
  if (!rs.length && r.detail) parca.push(esc(r.detail));      // ör. "silahlı plan yok"
  return parca.join(" · ");
}
window.alpacaSubmit = async () => {
  const _btn = () => document.querySelector('[data-act="alpacaSubmit"]');
  const b0 = _btn();
  if (b0) { b0.disabled = true; b0.textContent = "gönderiliyor…"; }
  alpMsgYaz("gönderiliyor…");
  try {
    // HTTP DURUMU OKUNUR: eski hâl doğrudan `.json()`a geçiyordu, yani 401/500 bir yanıt gövdesi
    // döndürdüğünde arayüz onu BAŞARI gibi okuyordu (`r.submitted||0` → "0 emir gönderildi").
    // v219: DURUM BU SATIRDA OKUNMAYA DEVAM EDİYOR (`hamYanit`) — v195-a hükmü bu yüzeyin
    // kendi hükmüdür: sonuç cümlesi kalıcı `_ALP_MSG` durumuna yazılır ve iki yeniden çizimden
    // sağ çıkar; fırlatılan bir hata `finally`den önce o durumu kuramazdı.
    const r = await apiFetch("/api/alpaca/submit_armed", { method: "POST", hamYanit: true });
    let body = {};
    try { body = await r.json(); }
    catch (e) { body = {}; }   // YASA 4 · işaretli yutma: gövde JSON değil; satır sayı uydurmaz, "—" basar
    alpMsgYaz(r.ok ? _alpSonucSatiri(body)
      : `<span class="neg">✗ HTTP ${r.status} — ${esc(body.detail || "sunucu sebep bildirmedi")}</span>`);
    // Kart tazelenir ama MESAJ HAYATTA KALIR: şablon `_ALP_MSG`i okuyor (bkz. beyanı).
    await RENDER.ayarlar(); revealActive();
  } catch (e) {
    // İKİ HÂL AYRIŞTIRILIR (v219 · `korumaKur` ile aynı gerekçe): sunucu CEVAP VERDİYSE reddin
    // gerekçesi bilinir ve emir GİTMEMİŞTİR. AĞ koptuysa (durum kodu YOK) istek uca ulaşmış ve
    // emirler çıkmış olabilir — bilinen tek şey CEVABIN alınamadığıdır.
    alpMsgYaz(e && e.status
      ? `<span class="neg">✗ ${esc(String(e.message))}</span> — sunucu REDDETTİ; emir gönderilmedi`
      : `<span class="neg">✗ ${esc(String((e && e.message) || e))}</span> — sonuç ölçülemedi;
         emirler gitmiş olabilir, mutabakat bölümünden doğrula`);
  } finally {
    const b = _btn();
    if (b && b.disabled) { b.disabled = false; b.textContent = ALP_GONDER_ETIKET; }
  }
};
// `window.alpacaClose` SİLİNDİ (v195-a · B3/Ö3). Gerekçesi kartın kendi şablonunda yazılı:
// `/api/alpaca/close_all` artık panoda TEK yerden çağrılır — `opFlatten` (Kademe 3), çift onaylı.
// Ad `EYLEMLER` izin listesinden de düştü; kalsaydı "kayıtlı ama tanımsız" bir eylem olurdu.
async function _secretFetch(name, method, body) {
  const opt = { method, headers: {} };
  if (body) { opt.headers["Content-Type"] = "application/json"; opt.body = JSON.stringify(body); }
  // v219: elle `detail` çıkarma BURADAN KALKTI — `apiFetch` gövdedeki gerekçeyi zaten mesaja
  // koyuyor ve o çıkarımın BOŞ `catch`i (gövde JSON değilse sessizce durum koduna düşerdi) tek
  // yerde, işaretli olarak yaşıyor. İkinci bir kopya ilk düzenlemede ayrışırdı.
  const r = await apiFetch("/api/secrets/" + encodeURIComponent(name), opt);
  return r.json();
}
window.saveSecret = async (name) => {
  const el = $("key-" + name), stat = $("kstat-" + name);
  const val = (el.value || "").trim();
  if (!val) { if (stat) stat.innerHTML = '<span class="neg">önce anahtarı yapıştır</span>'; return; }
  if (stat) stat.textContent = "kaydediliyor…";
  try {
    const res = await _secretFetch(name, "POST", { value: val });
    el.value = "";                       // never leave the secret sitting in the DOM
    await RENDER.ayarlar(); revealActive();   // re-render shows masked status; re-reveal or it stays hidden
    _senkronSatiri(name, res.local_agent);   // yerel-ajan senkron sonucu (Gemini anahtarı)
  } catch (e) { if (stat) stat.innerHTML = `<span class="neg">${esc(e.message)}</span>`; }
};
// ---- HERMES-SENKRON SONUCU, ZAMAN DAMGALI (ders (b), 2026-08-02) ----------------------------
// KUSUR: bu satır `la.detail`i damgasız basıyordu ve `RENDER.ayarlar()` yeniden çizdikten SONRA
// ekranda kalıyordu — yani "senkron hatası (OSError)" cümlesi ne zaman ölçüldüğünü söylemiyordu.
// Canlı vaka: altı gün önce oluşmuş bir hata, bugünün hükmü gibi okundu. `hermes.
// sync_local_agent_gemini` artık HER dönüşünde (başarı · ret · istisna) `senkron_ts` taşıyor;
// OKUYAN taraf burasıdır.
// ALAN YOKSA UYDURULMAZ: "damga yok" yazılır. `Date.now()` basmak, ölçülmemiş bir anı ölçülmüş
// göstermek olurdu — panonun okuduğu damga, motorun YAZDIĞI damga olmalı.
// clearSecret DE ÇAĞIRIR: anahtar silindiğinde de senkron koşuyor (yedeklenen Nous ayarına
// dönüş) ve o sonucun bugüne kadar HİÇBİR okuyucusu yoktu — sessiz bir başarısızlık yüzeyiydi.
function _senkronSatiri(name, la) {
  const el = $("kstat-" + name);
  if (!el || !la) return;
  const ts = mutlakTs(la.senkron_ts);
  const damga = ts ? ` · ${esc(ts)}` : ' · <span class="warn">damga yok</span>';
  el.innerHTML = la.ok ? `<span class="pos">✓ ${esc(la.detail)}</span>${damga}`
                       : `<span class="neg">${esc(la.detail)}</span>${damga}`;
}
window.clearSecret = async (name) => {
  const stat = $("kstat-" + name);
  try {
    const res = await _secretFetch(name, "DELETE");
    await RENDER.ayarlar(); revealActive();
    _senkronSatiri(name, res.local_agent);
  } catch (e) { if (stat) stat.innerHTML = `<span class="neg">${esc(e.message)}</span>`; }
};
window.notifyTest = async () => {
  const msg = $("ntf-msg");
  if (msg) msg.textContent = "gönderiliyor…";
  try {
    const r = await apiFetch("/api/notify/test", { method: "POST" }).then(x => x.json());
    if (msg) msg.innerHTML = r.ok ? '<span class="pos">✓ gönderildi — kanalını kontrol et</span>'
                                  : `<span class="neg">${esc(r.detail || "kanal ayarlı değil")}</span>`;
  } catch (e) { if (msg) msg.innerHTML = `<span class="neg">${esc(e.message)}</span>`; }
};
window.testKey = async (provider, name) => {
  const stat = $("kstat-" + name);
  if (stat) stat.textContent = "test ediliyor…";
  try {
    const r = await j("/api/secrets/test/" + encodeURIComponent(provider));
    if (stat) stat.innerHTML = r.ok
      ? `<span class="pos">✓ ${esc(r.detail || "bağlandı")}</span>`
      : `<span class="neg">✕ ${esc(r.detail || "başarısız")}</span>`;
  } catch (e) { if (stat) stat.innerHTML = `<span class="neg">${esc(e.message)}</span>`; }
};

// ================= otonomi merdiveni =================
// FAZ-6 KİLİTLERİNİN ADLARI — Operasyon'daki zincir satırıyla AYNI sözlük (health.FAZ6_KILITLERI).
const FAZ6_TR = { edge_kaniti: "EDGE kanıtı", sonuc_hukmu: "SONUÇ hükmü", faz5_cikisi: "Faz-5 çıkışı",
                  operator_onayi: "operatör onayı", dsr_gecer: "DSR geçer" };
// "MERDİVEN NEDEN L0'DA?" (pano turu 2026-07-31, §3.0 operatör bulgusu). Kart bugüne kadar yalnız
// L0→L1 ölçütlerini gösteriyordu ve operatör "merdiven hiç ilerlemiyor" diye okuyordu. İKİ AYRI
// KAPI VAR ve karıştırılmaları tam da bu yanılsamayı üretiyor:
//   · L0→L1 ölçütleri (guard.py) — kâğıt provanın karnesi, yukarıdaki liste;
//   · FAZ-6 beş kilidi (health.faz6_kilitleri) — gerçek-para/silahlanma ÖN-KOŞULU, fail-closed.
// İkincisi kapalıyken merdivenin ilerlememesi bir ARIZA DEĞİL, tasarımdır — ve bu cümle panoda
// hiçbir yerde yazmıyordu. Zincir yoksa satır hiç çizilmez (uydurma yok).
// ---- KİLİDİN `olcum` SÖZLÜĞÜ — PANONUN İLK OKUYUCUSU (v219 · iş 3) --------------------------
// ÖLÇÜLEN KUSUR: `health.faz6_kilitleri` her kilit için `{gecer, durum, olcum, esik, neden}`
// üretiyor ve pano bugüne kadar YALNIZ `esik` + `neden` çiziyordu (ikisi de bir `title=`
// ipucunun içinde). `olcum` sözlüğünün — n, ortalama bps, %95 CI, eşleşmeyen oranı, DSR,
// pencere kimliği — hiçbir pano okuyucusu YOKTU. `test_faz5_cikis_v212`nin C-YASA6 testi bunu
// bir çiviyle kayda geçirmişti ("pano `olcum`u okumuyor, o yüzden karar sayıları `neden`
// metnine de yazılır") ve o çivi bilerek "pano okumaya başladığı gün kırılsın" diye kondu.
// Bu tur onu kırar: sayı artık bir CÜMLENİN İÇİNDEN değil, ÖLÇÜMÜN KENDİSİNDEN okunuyor.
//
// DÖRT HÜCRE, BEŞ KİLİT: hücreler kilide göre değil SORUYA göre sabittir (ölçülen · örneklem ·
// aralık · defter). Bir kilidin o sorusu yoksa hücre "veri yok" + GEREKÇE basar, SIFIR BASMAZ —
// ÖLÇÜLEMEDİ ≠ 0 bu yüzeyin tek kuralı. Çubuk yalnız paydası BEYAN EDİLEBİLDİĞİNDE doğar
// (`hucreCubuk`un kendi kapısı): tavanı olmayan bir sayacın (n_trials, defter satırı) doluluğu
// çizilemez, çünkü çizilen doluluk uydurma bir tavana göre okunurdu.
const _F6_BOS = n => ({ deger: null, meta: n });
function kilitOlcumHucreleri(ad, k) {
  const o = (k || {}).olcum;
  const olculemedi = (k || {}).durum === "olculemedi";
  // RENK YALNIZ ANOMALİDE (D1'in beş rolü): KAPALI bir kilit anomali DEĞİLDİR — zincir
  // fail-closed'dır ve kapalılık tasarımın kendisi. Anomali olan, ÖLÇÜLEMEYEN kilittir.
  const rz = olculemedi ? "ÖLÇÜLEMEDİ" : "";
  const sf = olculemedi ? "warn" : "";
  if (o == null) {
    const n = "ölçüm sözlüğü uçtan GELMEDİ — alanın yokluğu 'sıfır' değil 'ölçülemedi' demektir";
    return { olculen: { deger: null, meta: n, rozet: rz }, orneklem: _F6_BOS(n),
             aralik: _F6_BOS(n), defter: _F6_BOS(n) };
  }
  // (a) EDGE / SONUÇ hükmü — `olcum` bir DİZGEdir: "geçen/toplam ölçüt".
  if (typeof o === "string") {
    const m = /^\s*(\d+)\s*\/\s*(\d+)\s*$/.exec(o);
    const gecen = m ? +m[1] : null, tum = m ? +m[2] : null;
    return {
      olculen: { deger: esc(o), degerSinif: sf, rozet: rz,
                 oran: tum ? gecen / tum : null, payda: tum ? `${tum} ölçüt (HEPSİ geçmeli)` : "",
                 meta: tum ? `${gecen} ölçüt geçti · ${tum - gecen} kaldı` : "hüküm dizgesi ayrıştırılamadı" },
      orneklem: _F6_BOS("bu kilit ÖLÇÜT sayar, örneklem taşımaz — `olcum` alanında n yoktur"),
      aralik: _F6_BOS("aralık yok: hüküm geçti/kaldı sayımıdır, nokta tahmini + CI üretmez"),
      defter: _F6_BOS("defter satırı yok: hüküm `analytics` hesabından gelir, satır saymaz"),
    };
  }
  // (b) OPERATÖR ONAYI — tek boole; ölçülebilir bir büyüklüğü YOK ve bu beyan edilir.
  if ("intraday_arm" in o) {
    return {
      olculen: { deger: o.intraday_arm ? "SİLAHLI" : "SİLAHSIZ", degerSinif: o.intraday_arm ? "warn" : "",
                 rozet: rz, meta: "state/INTRADAY_ARM · 1 bayrak (elle açılır, hiçbir otomatik yol açamaz)" },
      orneklem: _F6_BOS("örneklem yok: bu kilit bir OPERATÖR kararıdır, bir ölçüm değil"),
      aralik: _F6_BOS("aralık yok: bir bayrağın belirsizlik aralığı olmaz (0 ya da 1)"),
      defter: { deger: "INTRADAY_ARM", meta: "kaynak: state/INTRADAY_ARM — 1 dosyanın varlığı" },
    };
  }
  // (c) DSR — nokta tahmin + pencere kimliği + deneme sayısı.
  if ("dsr" in o) {
    return {
      olculen: { deger: o.dsr == null ? null : trn(o.dsr, 4), degerSinif: sf, rozet: rz,
                 meta: o.dsr == null ? "DSR ÖLÇÜLEMEDİ — yürürlükteki pencerede hesap kurulamadı (0 DEĞİL)"
                                     : `deflated Sharpe · eşik ${esc(String(k.esik || "").slice(0, 60))}` },
      orneklem: { deger: o.n_trials == null ? null : trn(o.n_trials),
                  meta: o.n_trials == null ? "deneme sayısı yazılmamış — DSR'nin paydası bilinmiyor"
                                           : "denenmiş aday (DSR düzeltmesinin girdisi)" },
      aralik: _F6_BOS("aralık yok: DSR bir NOKTA tahminidir, bu ölçümde CI üretilmez"),
      defter: { deger: o.pencere_id ? esc(String(o.pencere_id)) : null,
                meta: o.pencere_id ? "yürürlükteki holdout penceresi (rotasyon kimliği)"
                                   : "pencere kimliği gelmedi — hangi holdout'ta ölçüldüğü BİLİNMİYOR" },
    };
  }
  // (d) FAZ-5 ÇIKIŞI — bu turun en kalabalık ölçümü (kart EXE-2026-002).
  const c = o.cikis_olcumu || null;
  const ci = c ? c.ci : null;
  const es = c ? c.eslesmeyen : null;
  const band = c && c.maliyet_bandi ? c.maliyet_bandi.ek_bps_giris : null;
  return {
    olculen: { deger: (c && c.ortalama_bps != null) ? `${trn(c.ortalama_bps, 1)} bps` : null,
               degerSinif: sf, rozet: rz,
               meta: (c && c.ortalama_bps != null)
                 ? `eşleştirilmiş gölge−EOD farkı · E3 maliyet bandı ${trn(band, 1)} bps`
                 : "ortalama ÖLÇÜLEMEDİ — eşleşmiş çift yok ya da hüküm kill listesinde durdu (0 DEĞİL)" },
    orneklem: { deger: (c && c.n_eslesen != null) ? `${trn(c.n_eslesen)}/${trn(c.n_min)}` : null,
                oran: (c && c.n_eslesen != null && c.n_min) ? c.n_eslesen / c.n_min : null,
                payda: (c && c.n_min) ? `asgari eşleşmiş çift (n_min=${trn(c.n_min)})` : "",
                meta: (c && c.n_eslesen != null)
                  ? `${trn(c.n_eslesen)} eşleşmiş çift${es ? ` · eşleşmeyen ${trn(es.n)} (%${trn(100 * es.oran, 1)}, kill eşiği %${trn(100 * es.kill_esigi, 0)})` : ""}`
                  : "eşleşmiş çift sayısı yok — defter/evren boş ya da eşleştirme kırık (kill#4)" },
    aralik: { deger: (ci && ci.alt != null && ci.ust != null) ? `[${trn(ci.alt, 1)} · ${trn(ci.ust, 1)}]` : null,
              meta: (ci && ci.alt != null)
                ? `%${trn(100 * ci.seviye, 0)} CI · ${esc(String(ci.yontem || "yöntem yazılmamış"))} · B=${trn(ci.B)} · ${trn(ci.n_kume)} tarih kümesi`
                : `aralık KURULAMADI — ${esc(String((ci && ci.neden) || "CI için yeterli tarih kümesi yok; aralıksız ortalama hüküm veremez"))}` },
    defter: { deger: (o.intraday_shadow_orders_n == null) ? null
                : `${trn(o.intraday_shadow_orders_n)}${c && c.n_evren != null ? `/${trn(c.n_evren)}` : ""}`,
              meta: (o.intraday_shadow_orders_n == null)
                ? "gölge defteri satır sayısı gelmedi — evren ölçülemedi"
                : `4b gölge defteri satırı${c && c.n_evren != null ? " / DOLUM üretmiş satır (evren)" : ""} · 4a saha kaydı ${trn(o.intraday_decisions_n)}` },
  };
}
function faz6Satiri(f) {
  if (!f || !(f.adlar || []).length) return "";
  const cips = f.adlar.map(ad => {
    const k = (f.kilitler || {})[ad] || {};
    const kls = k.gecer ? "t-go" : (k.durum === "olculemedi" ? "t-rv" : "t-no");
    const ipucu = esc((k.esik || "") + (k.neden ? " — " + k.neden : ""));
    return `<span class="gc ${k.gecer ? "p" : "f"}" title="${ipucu}">${k.gecer ? "✓" : "×"} ${esc(FAZ6_TR[ad] || ad)}</span>`;
  }).join(" ");
  const kapali = f.adlar.filter(ad => !((f.kilitler || {})[ad] || {}).gecer)
    .map(ad => FAZ6_TR[ad] || ad);
  // ÖLÇÜM BLOĞU DETAY KATMANINDA: kilit çipi bir BAKIŞ yüzeyidir ("kaç/beş açık?"); beş kilidin
  // yirmi hücresi o bakışı boğardı. Katman kapalı doğar ama GİZLEMEZ — açan operatör kilidin
  // kapalılığının SAYISINI görür, "×" ile bir tooltip'i değil.
  const olcumBloklari = f.adlar.map(ad => {
    const k = (f.kilitler || {})[ad] || {};
    const h = kilitOlcumHucreleri(ad, k);
    return `<div style="margin-top:12px">
      <p class="hint" style="margin:0 0 6px"><b>${esc(FAZ6_TR[ad] || ad)}</b>
        <span class="mut">· ${esc(k.durum === "olculemedi" ? "ÖLÇÜLEMEDİ" : "ölçüldü")} ·
        ${k.gecer ? "AÇIK" : "KAPALI"}</span></p>
      ${ozetSerit([
        ozetHucre("Ölçülen", h.olculen),
        ozetHucre("Örneklem", h.orneklem),
        ozetHucre("Aralık", h.aralik),
        ozetHucre("Defter", h.defter),
      ], "Faz-6 kilit ölçümü")}
      <p class="hint" style="margin:6px 0 0"><b>Eşik:</b> ${esc(k.esik || "eşik yazılmamış")}</p>
      ${k.neden ? `<p class="hint" style="margin:2px 0 0"><b>Gerekçe:</b> ${esc(k.neden)}</p>` : ""}</div>`;
  }).join("");
  return `<div style="margin-top:18px;border-top:1px solid var(--line);padding-top:14px">
    <h3 class="t" style="font-size:13px">Gerçek-para tarafındaki ikinci kapı — Faz-6 kilit zinciri
      <span class="tx3" style="font-weight:400">(${f.n_acik ?? 0}/${f.n_kilit ?? 5} açık)</span></h3>
    <p class="hint" style="margin-top:6px">Yukarıdaki ölçütler kâğıt provanın karnesidir. Silahlanma
      ve gerçek para AYRICA bu beş kilidi ister ve zincir <b>fail-closed</b>'dır: ölçülemeyen kilit
      KAPALI sayılır. Merdivenin burada durması bir arıza değil, kuralın kendisidir.</p>
    <p class="hint" style="margin-top:8px">${cips}</p>
    ${kapali.length ? `<p class="hint"><b>Şu an kapalı:</b> ${esc(kapali.join(", "))} — aşağıdaki
      katman her kilidin EŞİĞİNİ, GEREKÇESİNİ ve ÖLÇÜLEN sayılarını açar.</p>` : ""}
    ${detayKatmani("Kilit ölçümleri — beşinin de sayıları",
      "`health.faz6_kilitleri[*].olcum` sözlüğü. Dört hücre kilide göre değil SORUYA göre sabittir; "
      + "bir kilidin o sorusu yoksa hücre 'veri yok' + gerekçe basar, sıfır basmaz.",
      olcumBloklari)}</div>`;
}
function ladderCard(L, faz6) {
  if (!L) return "";
  const TR = [
    ["≥ 60 kapanmış paper işlem", "yeterince prova işlemi biriktir"],
    ["≥ 2 farklı piyasa havasında pozitif not", "sadece boğa piyasasında değil"],
    ["Düşüş, izin verilen sınırın içinde", "tüm dönem boyunca kontrollü kayıp"],
    ["≥ 3 tahmin tuttu (kalibrasyon)", "ajan sadece aktif değil, isabetli"],
    ["Son 20 seansta açıklanamayan devre kesici yok", "beklenmedik panik freni olmamış"],
    ["Broker anahtarı: para çekme kapalı + IP kısıtlı", "operatör/altyapı işi"],
    ["İki güvenlik bayrağı elle açıldı", "canlıya geçişi sen onaylarsın"],
    ["Telefondan acil durdurma bağlı", "her an durdurabilmelisin"],
  ];
  const crits = L.l0_to_l1.map((c, i) => {
    const k = c.manual ? "man" : (c.met ? "ok" : "no");
    const ic = c.manual ? "◆" : (c.met ? "✓" : "○");
    const label = TR[i] ? TR[i][0] : esc(c.label);
    const sub = TR[i] ? `${TR[i][1]} · ${esc(c.detail)}` : esc(c.detail);
    return `<div class="crit"><div class="ck ${k}">${ic}</div><div><div>${label}</div><div class="tx3" style="font-size:11px">${sub}</div></div></div>`;
  }).join("");
  const p = L.auto_progress;
  return `<div class="card rise"><h2 class="t">${T("Otonomi merdiveni", "otonomi")} — gerçek parayı hak etmek</h2>
    <p class="hint" style="margin-top:0;margin-bottom:12px">Meridian gerçek paraya, bir ayar değişikliğiyle değil, aşağıdaki şartları <b>kanıtlayarak</b> geçer. Şu an en alt basamakta (L0, gerçek para yok).</p>
    <div class="levels">${L.levels.map(l => `<span class="lv ${l.active ? 'on' : ''}">${l.id} · ${trLevel(l.name)}</span>`).join('')}</div>
    <div class="bar" style="margin-bottom:6px"><i style="width:${p.total ? 100 * p.met / p.total : 0}%"></i></div>
    <p class="tx3" style="font-size:11px;margin-bottom:12px">Otomatik şartlar: ${p.met}/${p.total} karşılandı · ◆ işaretliler terfi anında elle yapılır · her şart kod içinde (guard.py) zorunlu tutulur</p>
    ${crits}
    ${faz6Satiri(faz6)}</div>`;
}
const trLevel = n => ({ "Paper, fully autonomous": "Kağıt üzerinde, tam otonom", "Live, every order approved": "Canlı, her emir onaylı", "Live, autonomous": "Canlı, otonom" }[n] || n);

// ---- KİMLİK KAPISI -------------------------------------------------------------------------
// Sunucu sınırı `api._auth`'tadır (oturum çerezi yoksa 401). Buradaki iş o sınırı görünür bir
// kapıya çevirmek. Kapıyı DOM'dan silmek veri açmaz — API yine 401 döner.
//
// Oturum çerezi HttpOnly'dir, yani bu kod onu OKUYAMAZ. Durum yalnız /api/session'dan öğrenilir.
let _oturumAcik = false;
let _PAROLA_KURULU = false;   // ray sonundaki Çıkış düğmesi buna bağlı

// TLS uyarısı YALNIZ gerçek risk varken gösterilir: şifresiz bağlantı VE loopback DIŞI bir adres.
// localhost'ta parola ağa hiç çıkmaz; orada uyarmak yanlış alarmdır ve gerçek uyarıyı değersizleştirir.
const _tlsRiski = () => location.protocol !== "https:" &&
  !["127.0.0.1", "localhost", "::1", ""].includes(location.hostname);

function kapiyiGoster(kurulumMu, tlsYok) {
  const g = $("gate");
  g.hidden = false;
  document.querySelector("nav")?.setAttribute("inert", "");
  document.querySelector(".shell")?.setAttribute("inert", "");
  $("gate-t").textContent = kurulumMu ? "Parola belirle" : "Giriş";
  $("gate-sub").textContent = kurulumMu
    ? "İlk parolayı şimdi belirle. En az 12 karakter. Bu parola diskte düz metin tutulmaz."
    : "Bu pano bir broker hesabına bakıyor ve durdurma yüzeyini taşıyor.";
  $("gate-go").textContent = kurulumMu ? "Parolayı kur" : "Gir";
  $("gate-pw").autocomplete = kurulumMu ? "new-password" : "current-password";
  $("gate-pw2-wrap").hidden = !kurulumMu;
  $("gate-tls").hidden = !tlsYok;
  $("gate-form").dataset.kurulum = kurulumMu ? "1" : "";
  $("gate-pw").focus();
}

function kapiyiKapat() {
  $("gate").hidden = true;
  document.querySelector("nav")?.removeAttribute("inert");
  document.querySelector(".shell")?.removeAttribute("inert");
  $("gate-pw").value = ""; $("gate-pw2").value = "";
}

$("gate-form").addEventListener("submit", async e => {
  e.preventDefault();
  const kurulum = !!$("gate-form").dataset.kurulum;
  const msg = $("gate-msg"), btn = $("gate-go");
  const pw = $("gate-pw").value;
  if (kurulum && pw !== $("gate-pw2").value) {
    msg.className = "gate-msg"; msg.textContent = "Parolalar eşleşmedi."; return;
  }
  btn.disabled = true; msg.className = "gate-msg"; msg.textContent = "denetleniyor…";
  try {
    await apiFetch(kurulum ? "/api/setup-password" : "/api/login",
      { method: "POST", headers: { "content-type": "application/json" },
        body: JSON.stringify({ password: pw }) });
    _oturumAcik = true;
    _PAROLA_KURULU = true;
    msg.className = "gate-msg ok"; msg.textContent = "girildi";
    kapiyiKapat();
    await baslat();
  } catch (err) {
    // İKİ HÂL AYRI CÜMLEDİR (v219): sunucu CEVAP VERDİYSE kendi cümlesi gösterilir (401 "parola
    // hatalı", 429 kilit süresi, 400 kısa parola) — kilit süresi gibi GERÇEK bilgiyi kendi
    // metnimizle örtmek, kapıyı okunamaz yapardı. Durum kodu yoksa gerçekten ulaşılamamıştır.
    msg.textContent = (err && err.status)
      ? (err.detay || `giriş başarısız (HTTP ${err.status})`)
      : "sunucuya ulaşılamadı — çalışıyor mu?";
  } finally { btn.disabled = false; }
});

// 401 HER YERDEN gelebilir ve operatör o an hangi sayfadaysa oradadır. apiFetch tek boğaz olduğu
// için kapıyı oradan açmak, her çağrı yerine tek tek bakmaktan güvenli.
//
// "OTURUM 12 SAATTE DOLAR" ARTIK DOĞRU DEĞİL (2026-08-14) — ve o cümle bu satırda yazılıydı.
// Sunucu oturumu KAYAN pencereye geçti: yetkili her istek çerezi yarı-ömrü geçmişse tazeler, yani
// AKTİF kullanılan pano artık dolmuyor. Dolan iki hâl kaldı: (1) pano ~12 saat hiç kullanılmadı,
// (2) oturum veriliş anından itibaren 7 günlük mutlak tavana vardı (çalınan çerezin ömür sınırı).
// BU DOSYADA DAVRANIŞ DEĞİŞMEDİ ve değişmemeli: kapak yine 401'de açılır, `_JC` yine temizlenir.
// Sunucu tarafındaki tazeleme istemcinin göreceği bir şey DEĞİLDİR (çerez HttpOnly'dir, JS onu
// okuyamaz) — pano yalnız 401 görmemeye başlar. Kapak mantığına dokunmak, sunucu bir gün geri
// alınırsa operatörü kapısız bırakırdı.
function _yetkisizYakala(r) {
  if (r && r.status === 401 && _oturumAcik) {
    _oturumAcik = false;
    _JC.clear();
    kapiyiGoster(false, _tlsRiski());
    $("gate-msg").textContent = "Oturum doldu — tekrar gir.";
  }
  return r;
}

// ---- boot ----
async function baslat() {
  const t = await refreshStatus();
  await buildSidebar(t);
  const h = location.hash.slice(1);
  await go(VIEWS.some(v => v[0] === h) || ROUTE_ALIAS[h] ? h : VARSAYILAN_ROTA);
  setInterval(refreshStatus, 15000);
}

(async () => {
  let s;
  try { s = await (await apiFetch("/api/session")).json(); }
  catch (e) { s = { authenticated: false, password_set: true, tls: true }; }
  _oturumAcik = !!s.authenticated;
  _PAROLA_KURULU = !!s.password_set;
  if (!s.password_set) return kapiyiGoster(true, _tlsRiski());
  if (!s.authenticated) return kapiyiGoster(false, _tlsRiski());
  await baslat();
})();

// ---- KLAVYE KATMANI — günlük kullanılan alet klavyeden sürülebilmeli. 1-6 görünümler,
// R aktif sayfayı tazeler, ? yardım/sayfa haritası, Esc kapatır. Yazı alanlarında devre dışı.
//
// HARİTA ARTIK VIEWS'TEN TÜRETİLİR (2026-07-27). İki liste elle tutuluyordu ve KAYMIŞLARDI:
// panel "4 · Öğrenme" yazıyordu ama 4 tuşu Intraday'e gidiyordu, Ayarlar'ın gerçek tuşu (6)
// hiç yazmıyordu. Yani yardım paneli var olmayan kısayolları belgeliyordu. Tuş numarası
// artık görünümün VIEWS içindeki sırasıdır; ikisi ayrışamaz.
const PAGE_DESC = {
  bugun: "dün gece · sermayenin kökeni · bugün ne var · alarm bütçesi · üç mini-trend — hepsi özet, detay yüzeyde",
  karar: "adaylar · disiplin kapısı · onay kuyruğu · kitap ve pozisyonlar · broker mutabakatı · seans-içi emir · eğri ve işlemler",
  saglik: "alarm gelen kutusu ve olay yüzeyleri · gece hattının çizelgesi · karantina/bütünlük · izlenen evren · seans-içi akış",
  ogrenme: "karne · gölge kollar · bileşen IC + EB · beyin ve sprint · hipotez defteri · beceriler · dersler",
  kilitler: "müdahale kademeleri · güvenlik durumu · API anahtarları · Alpaca aynası · dışa aktarım · sözlük",
};
// ---- 'g' ÖNEKLİ SAYFA ATLAMA (UIUX S1-T4, S2R-1'de yeni IA'ya çekildi) ------------------------
// İş emri Program X `g d / g a / g r` diyor; WP0 İ6 bunu şiddet-2 borç saydı (1-7 vardı, g yoktu).
// HARFLER SAYFANIN ADINDAN GELİR ve D2-b'de beş yüzeye indi:
//   g b → ① Bugün           g k → ② Karar
//   g s → ③ Sağlık          g o → ④ Öğrenme
//   g y → ⑤ Kilitler
// Beş yüzeyin BEŞİ de kapsanır: bir kısmını bağlayıp gerisini dışarıda bırakmak, "hangileri var"
// sorusunu her seferinde deneyerek cevaplatırdı — kısayolun amacı tam da bunu bitirmek.
// ESKİ HARFLER (d/p/a/r) DÜŞTÜ: sayfaları düştü. Yarım kalan bir `g d`, tanınmayan tuş dalına
// düşer ve SESSİZCE iptal olur (yanlış sayfaya gitmekten iyi) — bkz. aşağıdaki önek kipi.
//
// NEDEN ÖNEK: `b`, `s`, `o` tek başına ALINAMAZ — `r` zaten "yenile", `k`/`j` satır gezinmesi.
// Önek bir ayrı kip açar ve o kipte tek tuş TÜKETİLİR; yani `g k` satır gezinmesini tetiklemez.
// `g g` gerekmez artık (Bugün'ün harfi `b`); `g` iki kez basılırsa ikinci `g` tanınmayan tuştur
// ve dizi sessizce iptal olur.
const GIT_KISAYOL = { b: "bugun", k: "karar", s: "saglik", o: "ogrenme", y: "kilitler" };
// Önek SÜRESİZ AÇIK KALAMAZ: yarım bırakılmış bir `g`, dakikalar sonra basılan `r`yi sayfa
// atlamasına çevirirdi — kullanıcının hiç istemediği bir eylem, hiç beklemediği anda.
const G_PENCERE_MS = 1500;
let _gOnekTs = 0;
const _gTusu = id => (Object.keys(GIT_KISAYOL).find(t => GIT_KISAYOL[t] === id) || "");
const PAGE_MAP = VIEWS.map(([id, label], i) =>
  [String(i + 1), label, PAGE_DESC[id] || "", _gTusu(id) ? `g ${_gTusu(id)}` : ""]);
let _kbdOrigin = null;
function kbdOverlay(show) {
  let ov = $("kbd-ov");
  if (!show) {
    if (ov) { ov.remove(); const o = _kbdOrigin; _kbdOrigin = null;
              if (o && document.contains(o)) o.focus(); }
    return;
  }
  if (ov) return;
  _kbdOrigin = document.activeElement !== document.body ? document.activeElement : null;
  ov = document.createElement("div"); ov.id = "kbd-ov"; ov.className = "kbd-ov";
  // Gerçek bir diyalog: modal, adlı, odak içeride kilitli. Öncesinde yalnız role="dialog" vardı;
  // arkadaki sayfa hem okunabiliyor hem Tab'la gezilebiliyordu.
  ov.setAttribute("role", "dialog"); ov.setAttribute("aria-modal", "true");
  ov.setAttribute("aria-label", "Klavye kısayolları ve sayfa haritası");
  // TÜM KISAYOLLAR TEK YERDE (UIUX S1-T4). Panel eskiden yalnız 1-7 · J/K · R · ?'i sayıyordu;
  // ⌘K paleti ve satır-içi Enter/Esc davranışı hiçbir yerde yazılı değildi — yani panonun en
  // çok kullanılan kısayolu, kısayol haritasında YOKTU. Harita eksikse hatırlamaya zorlar
  // (Nielsen İ6) ve bu tam da panelin kapatmak için var olduğu şey.
  ov.innerHTML = `<div class="kbd-panel"><h2 class="t">Kısayollar · sayfa haritası</h2>
    ${PAGE_MAP.map(([k, n, d, g]) => `<div class="krow"><kbd>${k}</kbd>${
      g ? `<kbd>${esc(g)}</kbd>` : ""}<b>${esc(n)}</b><span>${esc(d)}</span></div>`).join("")}
    <div class="krow"><kbd>g</kbd><b>Sayfa atlama öneki</b><span>g + harf (yukarıdaki ikinci sütun) · ${G_PENCERE_MS / 1000} sn içinde</span></div>
    <div class="krow"><kbd>⌘K</kbd><b>Komut paleti</b><span>Ctrl+K de olur · beş yüzey <b>ve yirmi bir bölümün tamamı</b> · sembol · müdahale · öğrenme eylemleri</span></div>
    <div class="krow"><kbd>#</kbd><b>Bölüm çapası</b><span>her bölüm başlığı bir adrestir (<code>karar#mutabakat</code>) — ⌘K aranan bölüme kaydırır, sayfanın tepesine değil</span></div>
    <div class="krow"><kbd>J</kbd><b>Sonraki satır</b><span>kayıt satırları arasında aşağı</span></div>
    <div class="krow"><kbd>K</kbd><b>Önceki satır</b><span>yukarı · Enter kaydı açar</span></div>
    <div class="krow"><kbd>R</kbd><b>Yenile</b><span>aktif sayfayı yeniden yükler</span></div>
    <div class="krow"><kbd>?</kbd><b>Bu panel</b><span>Esc ile kapanır</span></div>
    <div class="krow"><kbd>Esc</kbd><b>Kapat / iptal</b><span>çekmece · palet · bu panel · yarım kalmış g öneki</span></div>
    <p class="hint" style="margin-top:14px">Alarm ve sessiz-hat satırlarındaki <b>teşhis ↗</b> düğmesi
      artık panoyu TERK ETMEZ: aynı çekmece deseninde bir <b>olay yüzeyi</b> açar — ne oldu, değerler
      şimdi ne, runbook adımları ve mevcut eylemler tek yerde (D2-b · runbook emilimi).</p>
    <button type="button" class="dlbtn" style="margin-top:16px" data-act="kbdOverlay" data-a1="false">Kapat</button></div>`;
  ov.addEventListener("click", e => { if (e.target === ov) kbdOverlay(false); });
  ov.addEventListener("keydown", e => {
    if (e.key !== "Tab") return;
    const f = [...ov.querySelectorAll("button")].filter(el => el.offsetParent !== null);
    if (!f.length) return;
    const first = f[0], last = f[f.length - 1];
    if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
    else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
  });
  document.body.appendChild(ov);
  ov.querySelector("button").focus();
}
window.kbdOverlay = kbdOverlay;
addEventListener("keydown", e => {
  if (e.metaKey || e.ctrlKey || e.altKey) return;
  const tag = (e.target && e.target.tagName) || "";
  if (/INPUT|TEXTAREA|SELECT/.test(tag)) return;
  if (e.key === "Escape") { _gOnekTs = 0; return kbdOverlay(false); }
  // Çekmece açıkken (aria-modal) arkadaki kısayollar ateşlenmez — modalın altındaki sayfaya
  // görünmeden gitmek modal olmanın anlamını bozar. Esc yukarıda zaten çalıştı.
  if ($("plotdrawer")?.classList.contains("open")) return;
  // ---- 'g' ÖNEKLİ SAYFA ATLAMA (UIUX S1-T4) --------------------------------------------------
  // ÖNEK KİPİ HER ŞEYDEN ÖNCE ÇÖZÜLÜR: `g r` beklerken `r`nin "yenile"ye düşmesi, iki tuşluk
  // bir niyetin ortasında başka bir eylem yapmak olurdu. Kip TÜKETİCİDİR — tanınmayan bir
  // harf gelirse dizi İPTAL edilir ve o tuş da DÜŞER (yarım niyet, yanlış eyleme dönüşemez).
  if (_gOnekTs) {
    const zamaninda = Date.now() - _gOnekTs < G_PENCERE_MS;
    _gOnekTs = 0;
    if (zamaninda) {
      const hedef = GIT_KISAYOL[e.key.toLowerCase()];
      if (hedef) { e.preventDefault(); kbdOverlay(false); return go(hedef); }
      return;               // 'g' + tanınmayan tuş: sessiz iptal (yanlış sayfaya gitmekten iyi)
    }
    // Süre dolmuşsa önek YOK sayılır ve tuş NORMAL yolundan devam eder — aşağı düşer.
  }
  if (e.key === "g" || e.key === "G") { _gOnekTs = Date.now(); return; }
  if (e.key === "?") { e.preventDefault(); return kbdOverlay(!$("kbd-ov")); }
  // Tuş = görünümün VIEWS içindeki sırası. Sabit "1234567" dizesi listeden bağımsızdı ve
  // yardım paneliyle birlikte kayabiliyordu; artık aynı kaynaktan türer.
  const i = VIEWS.findIndex((v, n) => String(n + 1) === e.key);
  if (i >= 0) { kbdOverlay(false); return go(VIEWS[i][0]); }
  if (e.key === "r" || e.key === "R") {
    const active = document.querySelector(".sitem.on")?.dataset.p || VARSAYILAN_ROTA;
    if (RENDER[active]) RENDER[active]().then(revealActive);
  }
  // SATIR GEZİNMESİ — j/k. Görünüm tuşları sayfayı değiştiriyordu ama sayfanın İÇİNDE
  // gezinmenin tek yolu Tab'dı, ve Tab bir satırdan diğerine gitmez: satırın içindeki her
  // odaklanabilir parçaya uğrar. Kayıt açmak zaten Enter/Space ile çalışıyordu (satırlar
  // gerçek <button>); eksik olan satırdan satıra ATLAMAKTI.
  // Küme `[data-rk]`: kayıt defterine bağlı satırların TAMAMI ve yalnız onlar — hem <button>
  // hem role="button" olanlar (başlık taşıyan slip HTML'de butona giremiyor).
  if (e.key === "j" || e.key === "k" || e.key === "J" || e.key === "K") {
    const satirlar = [...document.querySelectorAll("[data-rk]")]
      .filter(el => el.offsetParent !== null);       // gizli görünümlerdekiler sayılmaz
    if (!satirlar.length) return;
    e.preventDefault();
    const asagi = e.key === "j" || e.key === "J";
    const su = satirlar.indexOf(document.activeElement);
    // Odak listede değilse (sayfaya yeni girildi): j ilkine, k sonuncusuna gider.
    const hedef = su < 0 ? (asagi ? 0 : satirlar.length - 1)
                         : Math.min(satirlar.length - 1, Math.max(0, su + (asagi ? 1 : -1)));
    const el = satirlar[hedef];
    // `preventScroll` + elle kaydırma: tarayıcının kendi kaydırması satırı üst barın ALTINA
    // sokuyor (bar position:fixed, 78px). Aynı sorun için --navh zaten ölçülüyor.
    el.focus({ preventScroll: true });
    const bar = parseInt(getComputedStyle(document.documentElement).getPropertyValue("--navh")) || 78;
    const r = el.getBoundingClientRect();
    if (r.top < bar + 8) scrollTo({ top: scrollY + r.top - bar - 16, behavior: "instant" });
    else if (r.bottom > innerHeight - 8) scrollTo({ top: scrollY + r.bottom - innerHeight + 16, behavior: "instant" });
  }
});
