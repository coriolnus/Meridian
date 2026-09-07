/* ============================================================================
   PANO SOHBETİ ÇİVİLERİ — node ile GERÇEKTEN koşuluyor (TSK-012 dalga-B, B2)
   ----------------------------------------------------------------------------
   NEDEN NODE, NEDEN KAYNAK METNİ DEĞİL: `assert "<kimlik>" in kaynak` biçimindeki
   bir çivi, ifadeyi bozan ama adı koruyan mutasyonda ISIRMAZ (v347 incelemesi B4,
   v350'nin devraldığı ders). B2'nin saf hükümleri bu yüzden React'siz modüllerde
   duruyor ve burada ÇAĞRILIYOR:
     · `ui/src/pano/yuzeyler/ajan/sohbet.ts`         — geçmiş/kota/yanıt grameri
     · `ui/src/pano/yuzeyler/kuyruk/sohbetOnerisi.ts` — öneri türü sözlüğü
     · dikiş: `kuyruk/onaylar.ts::kuyrugaCevir` + `kuyruk/onayEylem.ts::onayHedefi`
       (saf fonksiyonun doğru olması ÇAĞRILDIĞINI kanıtlamaz — v350'nin [7] dikiş
       bölümüyle aynı gerekçe)

   TEK KAYNAK, İKİ KOŞUCU (v350 deseni): bu dosya hem `tests/test_pano_sohbet_v443.py`
   içinden hem de elden koşulur:

       node tests/civiler/sohbet_civileri.mjs                  # kendisi esbuild'ler
       node tests/civiler/sohbet_civileri.mjs --kendini-sina   # POZİTİF KONTROL

   `--kendini-sina` düzeneğin GERÇEKTEN kırmızıya dönebildiğini gösterir: bilerek
   yanlış bir iddia koşulur ve süreç 1 ile çıkmak ZORUNDADIR.
   ============================================================================ */
import { execFileSync } from "node:child_process";
import { mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import assert from "node:assert/strict";

const KOK = path.resolve(import.meta.dirname, "../..");
const UI = path.join(KOK, "ui");
const ESBUILD = path.join(UI, "node_modules/.bin/esbuild");

const argv = process.argv.slice(2);
const kendiniSina = argv.includes("--kendini-sina");

const gecici = () => mkdtempSync(path.join(tmpdir(), "sohbet-civi-"));
const paketle = (giris, ad) => {
  const cikti = path.join(gecici(), ad);
  execFileSync(
    ESBUILD,
    [giris, "--bundle", "--format=esm", "--platform=node", `--outfile=${cikti}`],
    { cwd: UI, stdio: "inherit" },
  );
  return cikti;
};

const S = await import(paketle("src/pano/yuzeyler/ajan/sohbet.ts", "sohbet.mjs"));
const O = await import(paketle("src/pano/yuzeyler/kuyruk/sohbetOnerisi.ts", "oneri.mjs"));
const K = await import(paketle("src/pano/yuzeyler/kuyruk/onaylar.ts", "onaylar.mjs"));
const E = await import(paketle("src/pano/yuzeyler/kuyruk/onayEylem.ts", "onayEylem.mjs"));

let gecen = 0;
const civi = (ad, f) => {
  f();
  gecen += 1;
  console.log(`  ✓ ${ad}`);
};

if (kendiniSina) {
  console.log("[0] POZİTİF KONTROL — düzenek kırmızıya dönebiliyor mu");
  civi("bilerek yanlış iddia (bu satır GEÇMEMELİ)", () => {
    assert.equal(S.sureMetni(null), "1,0 sn",
      "kendini-sınama iddiası: düzenek çalışıyorsa BURADA düşer");
  });
  console.log("KENDİNİ SINAMA GEÇTİ — bu bir KUSURDUR (süreç 0 ile çıkacak).");
  process.exit(0);
}

/* =============================================================================
   [1] DEFTER SATIRI — uçtan gelen şekil, savunmacı okunuyor
   ========================================================================== */
console.log("[1] defter satırı");

const HAM = {
  ts: "2026-09-07T19:30:00+00:00",
  oturum: "pano-2026-09-07-a1b2",
  mesaj: "MU planı neden REVIEW aldı?",
  cevap: "Kapı `rvol` kontrolünü yumuşak düşürdü.",
  turlar: [{ model: "nemotron", tool_calls: 2, sema_disi: 0, sure_s: 3.1 }],
  kaynaklar: [{ arac: "plan_oku", anahtar: "P-2026-09-04-MU" }],
  model: "nvidia/nemotron-3-super-120b-a12b:free",
  sure_s: 12.5,
  jeton_giris: 1200,
  jeton_cikis: 340,
  kota_bugun: 7,
  oneri_id: null,
  sema_disi_n: 0,
  llm_dustu: false,
};

civi("satirOku ham defter satırını okur (alan adları uçtan, tahminden değil)", () => {
  const s = S.satirOku(HAM);
  assert.equal(s.mesaj, "MU planı neden REVIEW aldı?");
  assert.equal(s.cevap, "Kapı `rvol` kontrolünü yumuşak düşürdü.");
  assert.equal(s.model, "nvidia/nemotron-3-super-120b-a12b:free");
  assert.equal(s.sureS, 12.5);
  assert.equal(s.kotaBugun, 7);
  assert.equal(s.turN, 1);
  assert.deepEqual(s.kaynaklar, [{ arac: "plan_oku", anahtar: "P-2026-09-04-MU" }]);
});

civi("satirOku ÖLÇÜLMEYEN alanı 0'a değil null'a düşürür (uydurma yasağı)", () => {
  const s = S.satirOku({ mesaj: "x", cevap: "y" });
  assert.equal(s.sureS, null, "süre yokken 0 yazmak 'ölçtük, sıfırdı' demek olurdu");
  assert.equal(s.jetonGiris, null);
  assert.equal(s.jetonCikis, null);
  assert.equal(s.kotaBugun, null);
  assert.equal(s.model, null);
  assert.equal(s.turN, 0);
});

civi("satirOku nesne olmayanı REDDEDER (null döner, boş satır uydurmaz)", () => {
  assert.equal(S.satirOku(null), null);
  assert.equal(S.satirOku("satır"), null);
  assert.equal(S.satirOku(42), null);
});

civi("satirOku bozuk kaynak öğesini DÜŞÜRÜR, listeyi uydurmaz", () => {
  const s = S.satirOku({ mesaj: "x", cevap: "y", kaynaklar: [{ arac: "plan_oku" }, { anahtar: "a" }, 7] });
  assert.deepEqual(s.kaynaklar, [{ arac: "plan_oku", anahtar: null }],
    "araç adı olmayan öğe kaynak DEĞİLDİR — atıf paydasını şişirir");
});

/* =============================================================================
   [2] GEÇMİŞ — "boş" ile "ölçülemedi" AYRI
   ========================================================================== */
console.log("[2] geçmiş");

civi("gecmisOku alan yoksa BOŞ GEÇMİŞ demez, nedenini yazar", () => {
  const g = S.gecmisOku({ kunye: {} }, null);
  assert.equal(g.satirlar.length, 0);
  assert.ok(g.neden !== null && g.neden.includes("gecmis"),
    "`gecmis` alanı yokken sessiz boş liste, 'hiç konuşulmadı' yalanıdır");
});

civi("gecmisOku hatayı AYNEN taşır (teşhis ucun cümlesinde)", () => {
  const g = S.gecmisOku(null, "/api/sohbet → HTTP 500 — defter okunamadı");
  assert.equal(g.neden, "/api/sohbet → HTTP 500 — defter okunamadı");
});

civi("gecmisOku okunmamış gövdeyi 'boş' saymaz", () => {
  const g = S.gecmisOku(null, null);
  assert.ok(g.neden !== null, "gövde henüz yokken neden yazılmalı");
});

civi("gecmisOku GERÇEKTEN boş defteri boş sayar (neden YOK)", () => {
  const g = S.gecmisOku({ gecmis: [] }, null);
  assert.equal(g.neden, null, "ölçülmüş boşluk bir hüküm değil bir sonuçtur");
  assert.equal(g.satirlar.length, 0);
});

civi("gecmisOku satırları okur ve bozuk olanı düşürür", () => {
  const g = S.gecmisOku({ gecmis: [HAM, "bozuk", { mesaj: "a", cevap: "b" }] }, null);
  assert.equal(g.satirlar.length, 2);
  assert.equal(g.satirlar[0].mesaj, "MU planı neden REVIEW aldı?");
});

/* =============================================================================
   [3] KOTA — `bugun: null` ÖLÇÜLEMEDİ demektir, 0 DEĞİL
   ========================================================================== */
console.log("[3] kota");

civi("kotaOku uç gövdesini okur", () => {
  const k = S.kotaOku({ bugun: 3, kalan: 117, tavan: 120, defter_n: 900, neden: null });
  assert.deepEqual(k, { bugun: 3, kalan: 117, tavan: 120, neden: null, dolu: null });
});

civi("kotaOku `dolu` alanını okur; alan yoksa (B1 öncesi uç) null taşınır (0/false DEĞİL)", () => {
  const dolu = S.kotaOku({ bugun: 120, kalan: 0, tavan: 120, neden: null, dolu: true });
  assert.equal(dolu.dolu, true);
  const bos = S.kotaOku({ bugun: 3, kalan: 117, tavan: 120, neden: null });
  assert.equal(bos.dolu, null, "`dolu` yazılmamışsa `false` uydurmak 'ölçüldü, dolu değil' yalanı olurdu");
});

civi("kotaMetni ölçülemeyen kotayı SIFIR göstermez", () => {
  const m = S.kotaMetni({ bugun: null, kalan: null, tavan: 120, neden: "telemetri halkası bugünün içinde dolmuş" }, null);
  assert.ok(m.metin.includes("ölçülemedi") || m.metin.includes("ÖLÇÜLEMEDİ"),
    "kota ölçülemediğinde ekranda 'ölçülemedi' YAZAR");
  assert.ok(m.metin.includes("telemetri halkası"), "ucun nedeni AYNEN taşınır");
  assert.equal(m.uyari, true);
  assert.ok(!/\b0\/120\b/.test(m.metin), "0/120 yazmak 'bugün hiç çağrı yok' yalanı olurdu");
});

civi("kotaMetni ölçülen kotayı sayar ve dolduğunda uyarır", () => {
  const a = S.kotaMetni({ bugun: 7, kalan: 113, tavan: 120, neden: null }, null);
  assert.ok(a.metin.includes("7/120"), `beklenen "7/120", gelen: ${a.metin}`);
  assert.ok(a.metin.includes("113"));
  assert.equal(a.uyari, false);
  const b = S.kotaMetni({ bugun: 120, kalan: 0, tavan: 120, neden: null }, null);
  assert.equal(b.uyari, true, "kota dolu bir UYARI hâlidir — sohbet model çağırmayacak");
});

civi("kotaMetni okunamayan ucu 'kota yok' saymaz", () => {
  const m = S.kotaMetni(null, "/api/sohbet/kota → HTTP 401");
  assert.ok(m.metin.includes("401"), "ucun hatası ekrana taşınır");
  assert.equal(m.uyari, true);
  assert.equal(m.dolu, false, "GEÇİCİ bir GET hatası girişi haksız yere KAPATMAMALI");
  assert.equal(m.kapaliBeyan, null);
});

/* ---- K-1: kota dolunca giriş KAPANIR (inceleme düzeltme turu 1) ------------ */

civi("kotaMetni backend `dolu:true` derse giriş KAPANIR ve beyan ÖLÇÜLEN sayıları taşır", () => {
  const g = S.kotaMetni({ bugun: 120, kalan: 0, tavan: 120, neden: null, dolu: true }, null);
  assert.equal(g.dolu, true, "backend dolu dediyse pano da dolu saymalı — eşik burada yeniden hesaplanmaz");
  assert.ok(g.kapaliBeyan !== null && g.kapaliBeyan.includes("120/120"),
    `kapanış beyanı ölçülen sayıları taşımıyor: ${g.kapaliBeyan}`);
});

civi("kotaMetni `bugun:null` (ölçülemedi) ile `dolu:true` gelirse beyan 0 UYDURMAZ, nedeni taşır", () => {
  const g = S.kotaMetni(
    { bugun: null, kalan: null, tavan: 120, neden: "telemetri halkası bugünün içinde dolmuş", dolu: true },
    null,
  );
  assert.equal(g.dolu, true);
  assert.ok(g.kapaliBeyan !== null && g.kapaliBeyan.includes("telemetri halkası"),
    "ölçülemeyen kota 0 ya da sayı olarak YAZILAMAZ — ucun nedeni aynen taşınır");
});

civi("kotaMetni `dolu:false` ya da alan YOKSA giriş AÇIK kalır (geriye dönük uyum, K-1)", () => {
  const acikca = S.kotaMetni({ bugun: 5, kalan: 115, tavan: 120, neden: null, dolu: false }, null);
  assert.equal(acikca.dolu, false);
  assert.equal(acikca.kapaliBeyan, null);
  const alanYok = S.kotaMetni(S.kotaOku({ bugun: 5, kalan: 115, tavan: 120, neden: null }), null);
  assert.equal(alanYok.dolu, false,
    "B1 öncesi uç `dolu` yazmıyorsa mevcut davranış (açık) KALIR — eşik UI'da yeniden yazılmaz");
  assert.equal(alanYok.kapaliBeyan, null);
});

civi("gonderimKapaliMi TEK kapı: kota dolu olduğunda dolu taslak bile ENGELLENIR", () => {
  assert.equal(S.gonderimKapaliMi("bir soru", false, true), true, "dolu:true → gönderim çağrısı YAPILMAZ");
  assert.equal(S.gonderimKapaliMi("bir soru", false, false), false, "dolu:false → gönderim İZİN VERİLİR");
  assert.equal(S.gonderimKapaliMi("", false, false), true, "boş taslak zaten engelliydi — davranış BOZULMADI");
  assert.equal(S.gonderimKapaliMi("bir soru", true, false), true, "gönderiliyorken ikinci gönderim engellenir");
});

/* =============================================================================
   [4] YANIT DURUMU — "model yok" ile "cevap" aynı görünemez
   ========================================================================== */
console.log("[4] yanıt durumu");

civi("llm_dustu bir DURUMDUR, hata değil", () => {
  const s = S.satirOku({ ...HAM, model: null, llm_dustu: true, cevap: "model yok — zincirin hiçbir ayağı cevap vermedi" });
  assert.equal(S.yanitDurumu(s), "model-yok");
  assert.ok(S.durumBeyani("model-yok").length > 10, "durumun ekranda bir cümlesi olmalı");
});

civi("kota kapısı ayrı bir durum: model ÇAĞRILMADI (tur yok)", () => {
  const s = S.satirOku({ mesaj: "x", cevap: "kota dolu (120/120)", turlar: [], model: null, llm_dustu: false });
  assert.equal(S.yanitDurumu(s), "model-cagrilmadi");
});

civi("normal cevap 'cevap' durumudur ve beyan taşımaz", () => {
  assert.equal(S.yanitDurumu(S.satirOku(HAM)), "cevap");
  assert.equal(S.durumBeyani("cevap"), null);
});

civi("kaynaksız cevap GÖRÜNÜR bir beyan taşır (kartın uydurma sayımı için)", () => {
  const bos = S.satirOku({ ...HAM, kaynaklar: [] });
  assert.ok(S.kaynakBeyani(bos).includes("kaynak atfı yok"));
  assert.equal(S.kaynakBeyani(S.satirOku(HAM)), null, "atıf varken beyan gereksizdir");
});

civi("kaynakEtiketi araç adını ve anahtarı birlikte yazar; anahtarsız kaynağı gizlemez", () => {
  assert.equal(S.kaynakEtiketi({ arac: "plan_oku", anahtar: "P-1" }), "plan_oku · P-1");
  assert.ok(S.kaynakEtiketi({ arac: "pano_ozeti", anahtar: null }).startsWith("pano_ozeti"));
  assert.ok(S.kaynakEtiketi({ arac: "pano_ozeti", anahtar: null }).length > "pano_ozeti".length,
    "anahtar yokluğu SÖYLENİR, sessizce kırpılmaz");
});

civi("model / süre / jeton ölçülemediğinde sayı gibi görünmez", () => {
  const bos = S.satirOku({ mesaj: "x", cevap: "y" });
  assert.ok(S.modelMetni(bos).includes("künye"), `beklenen künye yokluğu, gelen: ${S.modelMetni(bos)}`);
  assert.equal(S.modelMetni(S.satirOku(HAM)), "nvidia/nemotron-3-super-120b-a12b:free");
  assert.ok(S.sureMetni(null).includes("ölçülemedi"));
  assert.equal(S.sureMetni(12.5), "12,5 sn");
  assert.ok(S.jetonMetni(null, null).includes("ölçülemedi"));
  assert.ok(S.jetonMetni(1200, 340).includes("1200") && S.jetonMetni(1200, 340).includes("340"));
});

civi("gönderim hatası her kod için AYRI cümle ve AYRI çare verir", () => {
  const ag = S.gonderimHatasi(0, "Failed to fetch");
  assert.ok(ag.govde.includes("DEĞİL"), "yanıtsız istek 'gitmedi' diye okunmamalı — tur sürüyor olabilir");
  assert.equal(ag.oturumDustu, false);
  const yetki = S.gonderimHatasi(401, null);
  assert.equal(yetki.oturumDustu, true, "401'in çaresi yeniden giriş — tekrar denemek değil");
  assert.ok(S.gonderimHatasi(400, "boş mesaj — cevaplanacak bir soru yok").govde.includes("boş mesaj"),
    "ucun ret gerekçesi AYNEN taşınır");
  assert.ok(S.gonderimHatasi(503, null).baslik.includes("503"));
  assert.ok(S.gonderimHatasi(418, null).baslik.toLowerCase().includes("beklenmeyen"));
});

/* =============================================================================
   [5] OTURUM KİMLİĞİ — gün başına tek oturum (kartın SEANS sayımı buna dayanıyor)
   ========================================================================== */
console.log("[5] oturum kimliği");

const SABIT = () => 0.5;

civi("kayıtlı kimlik AYNI GÜNDEYSE korunur (her mesaj ayrı seans olmaz)", () => {
  assert.equal(S.oturumSec("pano-2026-09-07-a1b2", "2026-09-07", SABIT), "pano-2026-09-07-a1b2");
});

civi("dünün kimliği bugüne TAŞINMAZ — seans sayımı anlamını yitirirdi", () => {
  const yeni = S.oturumSec("pano-2026-09-06-a1b2", "2026-09-07", SABIT);
  assert.ok(yeni.startsWith("pano-2026-09-07-"), `beklenen bugünün öneki, gelen: ${yeni}`);
  assert.notEqual(yeni, "pano-2026-09-06-a1b2");
});

civi("kayıt yokken kimlik ÜRETİLİR ve gün önekini taşır", () => {
  const y = S.oturumSec(null, "2026-09-07", SABIT);
  assert.ok(y.startsWith("pano-2026-09-07-"));
  assert.ok(y.length > "pano-2026-09-07-".length, "önek tek başına kimlik değildir");
});

civi("çöp kayıt (önek tutmayan) sessizce kabul EDİLMEZ", () => {
  const y = S.oturumSec("ajan-42", "2026-09-07", SABIT);
  assert.ok(y.startsWith("pano-2026-09-07-"));
});

civi("üretim rastgeleliğe bağlıdır — iki tarayıcı aynı kimliği paylaşmaz", () => {
  const a = S.oturumSec(null, "2026-09-07", () => 0.111);
  const b = S.oturumSec(null, "2026-09-07", () => 0.777);
  assert.notEqual(a, b);
});

/* =============================================================================
   [6] ⌘K DEVRİ — palet ile panel arasındaki TEK SEFERLİK istek
   ========================================================================== */
console.log("[6] ⌘K devri");

civi("istek bırakılır, BİR KEZ alınır (ikinci okuma null)", () => {
  S.sohbetIstegiBirak("MU planı neden REVIEW aldı?");
  const i = S.sohbetIstegiAl();
  assert.equal(i.taslak, "MU planı neden REVIEW aldı?");
  assert.equal(S.sohbetIstegiAl(), null, "tüketilmiş istek ikinci kez uygulanırsa kutu kendi kendine dolar");
});

civi("taslaksız istek de bir istektir (yalnız odak)", () => {
  S.sohbetIstegiBirak(null);
  const i = S.sohbetIstegiAl();
  assert.notEqual(i, null, "odak isteği taslaksız da gelir — ⌘K boş sorguyla açılır");
  assert.equal(i.taslak, null);
});

civi("abone istek bırakıldığında UYARILIR (aynı adreste ikinci kez ⌘K sessiz kalmasın)", () => {
  let n = 0;
  const birak = S.sohbetIstegiAbone(() => { n += 1; });
  S.sohbetIstegiBirak("a");
  S.sohbetIstegiBirak("b");
  assert.equal(n, 2, "panel zaten açıkken hash değişmez; sinyal aboneden gelir");
  birak();
  S.sohbetIstegiBirak("c");
  assert.equal(n, 2, "abonelik bırakıldıktan sonra çağrı gelmemeli (sızıntı)");
  S.sohbetIstegiAl();
});

/* =============================================================================
   [7] ÖNERİ SÖZLÜĞÜ — DONUK türler, GLOBAL etki uyarısı
   ========================================================================== */
console.log("[7] öneri sözlüğü");

civi("öneri türleri DONUK sözlüktür (spec §2) — kod genişletemez", () => {
  assert.deepEqual([...O.SOHBET_ONERI_TURLERI], ["plan_onayi", "alarm_ack", "not"]);
});

civi("sohbet kimliği `SO-<damga>-<n>` biçimindedir ve iki nokta TAŞIMAZ", () => {
  assert.equal(O.sohbetKimligiMi("SO-20260907T193000Z-1"), true);
  assert.equal(O.sohbetKimligiMi("SO:20260907T193000Z-1"), false, "iki nokta önek ayrıştırmasını bozardı");
  assert.equal(O.sohbetKimligiMi("rec:momentum"), false);
  assert.equal(O.sohbetKimligiMi(null), false);
  assert.equal(O.sohbetKimligiMi("SO-2026-1"), false, "damga biçimi tutmayan kimlik tanınmamalı");
});

civi("oneriTuruOku donuk sözlük dışını REDDEDER", () => {
  assert.equal(O.oneriTuruOku("alarm_ack"), "alarm_ack");
  assert.equal(O.oneriTuruOku("emir_gonder"), null, "sözlük dışı tür tanınırsa donukluk anlamsızlaşır");
  assert.equal(O.oneriTuruOku(undefined), null);
});

civi("alarm_ack GLOBAL etkiyi ekranda SÖYLER (B1 kaygısı)", () => {
  const u = O.oneriUyarisi("alarm_ack");
  assert.ok(u.includes("TÜM") || u.includes("GLOBAL"), `global etki uyarısı yok: ${u}`);
});

civi("`not` türü İCRA YOK etiketini taşır", () => {
  assert.ok(O.oneriUyarisi("not").toLowerCase().includes("icra"));
  assert.equal(O.oneriGeriAlinamaz("not"), false, "icrası olmayan karar geri alınamaz sayılamaz");
});

civi("plan_onayi ve alarm_ack GERİ ALINAMAZ sayılır; tanınmayan tür de öyle (fail-closed)", () => {
  assert.equal(O.oneriGeriAlinamaz("plan_onayi"), true);
  assert.equal(O.oneriGeriAlinamaz("alarm_ack"), true);
  assert.equal(O.oneriGeriAlinamaz(null), true, "bilinmeyen türü 'zararsız' saymak fail-open olurdu");
});

civi("oneriEtiketi ve oneriBekleyen her tür için bir cümle verir", () => {
  for (const t of [...O.SOHBET_ONERI_TURLERI, null]) {
    assert.ok(O.oneriEtiketi(t).length > 0, `etiket yok: ${t}`);
    assert.ok(O.oneriBekleyen(t).length > 5, `bekleyen cümlesi yok: ${t}`);
  }
});

civi("oneriNedir kimliği ve hedefi cümlenin İÇİNE koyar (iki tık arasında okunur)", () => {
  const n = O.oneriNedir("SO-20260907T193000Z-1", "plan_onayi", "P-2026-09-04-MU");
  assert.ok(n.includes("SO-20260907T193000Z-1"));
  assert.ok(n.includes("P-2026-09-04-MU"));
  const h = O.oneriNedir("SO-20260907T193000Z-2", "not", null);
  assert.ok(h.includes("hedef") || h.includes("Hedef"), "hedefsiz öneri de kendini anlatmalı");
});

/* =============================================================================
   [8] DİKİŞ — kuyruk gerçekten bu sözlüğü ÇAĞIRIYOR mu
   ========================================================================== */
console.log("[8] dikiş: gelen kutusu ve karar yolu");

const INBOX = {
  level: 0,
  inbox: [{
    type: "sohbet_onerisi",
    id: "SO-20260907T193000Z-1",
    kaynak: "sohbet",
    title: "Sohbet önerisi: alarm_ack → DATA_QUALITY",
    evidence: "üç gündür aynı alarm ötüyor ve kaynağı kapandı",
    tur: "alarm_ack",
    hedef: "DATA_QUALITY",
    oturum: "pano-2026-09-07-a1b2",
    ts: "2026-09-07T19:30:00+00:00",
    actions: ["approve", "reject"],
  }],
};

civi("kuyrugaCevir sohbet önerisini KENDİ türüne alır (bilinmeyen kovasına düşmez)", () => {
  const o = K.kuyrugaCevir(INBOX, null, null, null, null, null, [], null);
  const s = o.ogeler.find((x) => x.kimlik === "SO-20260907T193000Z-1");
  assert.notEqual(s, undefined, "sohbet önerisi kuyrukta YOK — operatör bekleyen kararı görmez");
  assert.equal(s.tur, "sohbet", `tür 'sohbet' bekleniyordu, gelen: ${s.tur}`);
  assert.equal(s.ayrinti.cesit, "sohbet");
  assert.equal(s.isIstiyor, true, "bekleyen öneri iş İSTER (uç yalnız kararsızları listeler)");
});

civi("kuyrugaCevir hedefi ve oturumu EKRANA taşır, damgayı uçtan alır", () => {
  const o = K.kuyrugaCevir(INBOX, null, null, null, null, null, [], null);
  const s = o.ogeler.find((x) => x.kimlik === "SO-20260907T193000Z-1");
  assert.ok(s.konu.includes("DATA_QUALITY"), `konu hedefi taşımıyor: ${s.konu}`);
  assert.equal(s.gelisIso, "2026-09-07T19:30:00+00:00",
    "damga gelen kutusunda VAR (`_bekleyen_sohbet_onerileri`) — 'ölçülemedi' demek yalan olurdu");
  assert.equal(s.kanit, "üç gündür aynı alarm ötüyor ve kaynağı kapandı");
  assert.ok(s.not !== null && (s.not.includes("TÜM") || s.not.includes("GLOBAL")),
    "alarm_ack'in global etkisi satırın notunda görünmeli");
});

civi("K-2: uç bir gün `note` yazsa bile alarm_ack'in GLOBAL uyarısı satırdan DÜŞMEZ", () => {
  // `??` ile yazılsaydı `note` doluyken tür uyarısı YERİNE geçerdi — bugün zararsız
  // (`_bekleyen_sohbet_onerileri` `note` yazmıyor) ama uç yarın eklerse global etki
  // beyanı çekmeceyi açmayan operatörden sessizce kaybolurdu.
  const govde = {
    level: 0,
    inbox: [{ ...INBOX.inbox[0], id: "SO-20260907T193000Z-4", note: "operatör daha önce benzerini reddetti" }],
  };
  const o = K.kuyrugaCevir(govde, null, null, null, null, null, [], null);
  const s = o.ogeler[0];
  assert.ok(s.not.includes("operatör daha önce benzerini reddetti"), `uçtan gelen not düştü: ${s.not}`);
  assert.ok(s.not.includes("TÜM") || s.not.includes("GLOBAL"),
    `not doluyken bile alarm_ack'in global etkisi görünmeli: ${s.not}`);
});

civi("TUR_ETIKET sohbet türünü tanır (grafik ve tablo başlığı ondan okunur)", () => {
  assert.ok(typeof K.TUR_ETIKET.sohbet === "string" && K.TUR_ETIKET.sohbet.length > 0);
});

civi("onayHedefi SO- kimliğini TANIR ve mevcut karar ucuna gönderir (yeni uç YOK)", () => {
  const o = K.kuyrugaCevir(INBOX, null, null, null, null, null, [], null);
  const s = o.ogeler.find((x) => x.kimlik === "SO-20260907T193000Z-1");
  const h = E.onayHedefi(s);
  assert.equal(h.engel, null, `karar yolu kapalı: ${h.engel}`);
  assert.equal(h.hedef.yol, "/api/approvals/SO-20260907T193000Z-1");
  assert.equal(h.hedef.redVar, true);
  assert.equal(h.hedef.l1Gerekir, false, "sohbet önerisi L0'da da karara bağlanır (api_approve istisnası)");
  assert.equal(h.hedef.geriAlinamaz, true, "alarm_ack onayı BEKLEYEN TÜM alarmları kapatır");
  assert.ok(h.hedef.geriAlmaNotu.length > 40);
});

civi("`not` önerisinde karar geri alınabilir sayılır ve icra YOKLUĞU yazılır", () => {
  const govde = {
    level: 0,
    inbox: [{ ...INBOX.inbox[0], id: "SO-20260907T193000Z-2", tur: "not", hedef: "", title: "Sohbet önerisi: not" }],
  };
  const o = K.kuyrugaCevir(govde, null, null, null, null, null, [], null);
  const s = o.ogeler[0];
  const h = E.onayHedefi(s);
  assert.equal(h.hedef.geriAlinamaz, false);
  assert.ok(h.hedef.nedir.toLowerCase().includes("icra"), `nedir cümlesi icra yokluğunu söylemiyor: ${h.hedef.nedir}`);
});

civi("BİÇİMSİZ kimlik POST yoluna GÖMÜLMEZ (fail-closed)", () => {
  // Defter elle düzenlenebilir bir dosya; `SO-` biçimini tutmayan bir kimlik `api_approve`
  // tarafından sohbet önerisi diye TANINMAZ ve karar tanınmayan bir uzaya yazılırdı.
  const govde = {
    level: 0,
    inbox: [{ ...INBOX.inbox[0], id: "sohbet-42" }],
  };
  const o = K.kuyrugaCevir(govde, null, null, null, null, null, [], null);
  const h = E.onayHedefi(o.ogeler[0]);
  assert.equal(h.hedef, null, "biçimsiz kimlik uca gönderiliyor");
  assert.ok(h.engel !== null && h.engel.includes("sohbet-42"),
    "engel cümlesi hangi kimliğin reddedildiğini söylemiyor");
});

civi("tanınmayan öneri türü SESSİZ geçmez — karar yolu açılır ama uyarı taşır", () => {
  const govde = {
    level: 0,
    inbox: [{ ...INBOX.inbox[0], id: "SO-20260907T193000Z-3", tur: "emir_gonder" }],
  };
  const o = K.kuyrugaCevir(govde, null, null, null, null, null, [], null);
  const s = o.ogeler[0];
  assert.equal(s.ayrinti.tur, null, "donuk sözlük dışı tür TANINMAZ");
  assert.ok(s.not !== null && s.not.length > 20, "tanınmayan tür için ekranda bir cümle olmalı");
  assert.equal(E.onayHedefi(s).hedef.geriAlinamaz, true, "bilinmeyen etki fail-closed sayılır");
});

console.log(`\nTOPLAM ${gecen} çivi GEÇTİ.`);
