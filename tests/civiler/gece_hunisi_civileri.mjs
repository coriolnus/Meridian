/* ============================================================================
   "GECE NE BULDU" HUNİSİ — ÇİVİLER node ile GERÇEKTEN KOŞULUYOR (2026-08-31)
   ----------------------------------------------------------------------------
   NEDEN NODE, NEDEN KAYNAK METNİ DEĞİL: bu turun düzelttiği üç kusurun üçü de
   bir React bileşeninin İÇİNDE yaşıyordu ve oraya yalnız `assert "..." in kaynak`
   biçiminde bakılabiliyordu. O çivi, ifadeyi bozan ama adı koruyan mutasyonda
   ISIRMAZ (v347 incelemesi B4) — nitekim "Taranan aday" etiketi haftalarca
   yanlış alana bağlıydı ve hiçbir çivi ötmedi. Türetme `gece.ts` + `huni_cekirdek.ts`
   içinde SAF duruyor; burada ÇAĞRILIYOR.

   TEK KAYNAK, İKİ KOŞUCU (v350 deseni):

       node tests/civiler/gece_hunisi_civileri.mjs                 # kendisi esbuild'ler
       node tests/civiler/gece_hunisi_civileri.mjs <paket.mjs>     # hazır pakete bağlanır
       node tests/civiler/gece_hunisi_civileri.mjs --kendini-sina  # POZİTİF KONTROL

   `--kendini-sina` düzeneğin GERÇEKTEN kırmızıya dönebildiğini gösterir: bilerek
   yanlış bir iddia koşulur ve süreç sıfırdan farklı çıkmak ZORUNDADIR.
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
const hazirPaket = argv.find((a) => !a.startsWith("--")) ?? null;

const gecici = () => mkdtempSync(path.join(tmpdir(), "gece-civi-"));
const paketle = (giris, ad) => {
  const cikti = path.join(gecici(), ad);
  execFileSync(
    ESBUILD,
    [giris, "--bundle", "--format=esm", "--platform=node", `--outfile=${cikti}`],
    { cwd: UI, stdio: "inherit" },
  );
  return cikti;
};

let paket = hazirPaket;
if (paket === null) paket = paketle("src/pano/yuzeyler/kanban/gece.ts", "gece.mjs");
const G = await import(path.isAbsolute(paket) ? paket : path.resolve(paket));

let gecen = 0;
const civi = (ad, f) => {
  f();
  gecen += 1;
  console.log(`  ✓ ${ad}`);
};

if (kendiniSina) {
  console.log("[0] POZİTİF KONTROL — düzenek kırmızıya dönebiliyor mu");
  civi("bilerek yanlış iddia (bu satır GEÇMEMELİ)", () => {
    assert.equal(G.AD_TARANAN, "bu-etiket-yok",
      "kendini-sınama iddiası: düzenek çalışıyorsa BURADA düşer");
  });
  console.log("HATA: düzenek yanlış bir iddiayı geçirdi — çivi koşucusu KIRIK");
  process.exit(2);
}

/* ---- yardımcılar --------------------------------------------------------- */

/** `_son_dongu()` gövdesinin şekli. Varsayılan: HER ŞEY ÖLÇÜLMÜŞ bir gece. */
const SD = (o) => ({
  var: true, neden: null, tarih: "2026-08-30", yasSaat: 9.0,
  taranan: 251, tarananNeden: null, aday: 3, plan: 2, silahli: 1,
  veriTamam: true, durduruldu: false, rejim: "trend_up", ...o,
});

const adlar = (m) => m.basamaklar.map((b) => b.ad);
const sayilar = (m) => m.basamaklar.map((b) => b.n);
const nedenler = (m) => m.dususler.map((d) => d.neden ?? null);

/* ==========================================================================
   1) KUSUR (a) — İLK BASAMAK ARTIK EVRENE BAĞLI, ADI DA ONU SÖYLÜYOR
   ========================================================================== */
console.log("\n[1] huninin ağzı");

civi("`taranan` varken ilk basamak EVREN, ikinci basamak elemeyi geçen aday", () => {
  const m = G.geceModeli(SD());
  assert.deepEqual(adlar(m), [G.AD_TARANAN, G.AD_ADAY, G.AD_PLAN, G.AD_HAZIR]);
  assert.deepEqual(sayilar(m), [251, 3, 2, 1],
    "ilk basamak eleme SONRASI sayıya bağlanmış — düzeltilen kusurun ta kendisi");
});

civi("ELEME SONRASI aday kaybolmuyor — dört basamak da ekranda", () => {
  const m = G.geceModeli(SD());
  assert.equal(m.olculen, 4, "bir basamak sessizce düştü (bedel yasası: ne kaybettiğini ölç)");
});

civi("alan HİÇ YOKKEN (eski kayıt) ilk basamak `Elemeyi geçen aday`a düşüyor", () => {
  const m = G.geceModeli(SD({ taranan: null, tarananNeden: null }));
  assert.deepEqual(adlar(m), [G.AD_ADAY, G.AD_PLAN, G.AD_HAZIR],
    "eski kayıtta olmayan bir evren basamağı çizildi — 'ölçülemedi' şeridi eski davranışı bozar");
  assert.equal(m.basamaklar[0].ad, G.AD_ADAY, "ilk basamak hâlâ 'Taranan' diye etiketli");
});

civi("alan VAR ama ölçülemediyse basamak DURUYOR ve motorun nedenini taşıyor", () => {
  const m = G.geceModeli(SD({ taranan: null, tarananNeden: "HALT çekili — bu turda hiç tarama yapıldı" }));
  assert.deepEqual(adlar(m), [G.AD_TARANAN, G.AD_ADAY, G.AD_PLAN, G.AD_HAZIR]);
  assert.equal(m.basamaklar[0].n, null);
  assert.match(m.basamaklar[0].neden, /HALT/,
    "motorun beyan ettiği sebep düştü — pano kendi açıklamasını uydurur");
});

civi("üç hâl ÜÇ AYRI sonuç veriyor (ölçüldü · ölçülemedi · alan yok)", () => {
  const a = G.geceModeli(SD({ taranan: 251, tarananNeden: null }));
  const b = G.geceModeli(SD({ taranan: null, tarananNeden: "veri kalitesi kapısı kapalı" }));
  const c = G.geceModeli(SD({ taranan: null, tarananNeden: null }));
  assert.equal(a.basamaklar.length, 4);
  assert.equal(b.basamaklar.length, 4);
  assert.equal(c.basamaklar.length, 3);
  assert.notEqual(b.basamaklar[0].neden, undefined);
});

/* ==========================================================================
   2) KUSUR (b) — DİPNOT İKİ GERÇEĞE AYRILDI
   ========================================================================== */
console.log("\n[2] payda dipnotu");

civi("0 aday: dipnot PAYDA 0 diyor, 'yazılı değil' DEMİYOR", () => {
  // ARIZANIN KENDİSİ: operatör bu geceyi "hiç tarama olmadı" diye okudu.
  const m = G.geceModeli(SD({ taranan: null, tarananNeden: null, aday: 0, plan: 0, silahli: 0 }));
  const n = nedenler(m);
  assert.ok(n.length > 0, "hiç düşüş satırı doğmadı — dipnot ölçülemedi");
  for (const s of n) {
    assert.match(s, /payda 0/i, `dipnot payda 0'ı söylemiyor: ${s}`);
    assert.doesNotMatch(s, /yazılı değil|ölçülemedi/i,
      `ÖLÇÜLMÜŞ bir sıfır 'ölçülemedi' diye anlatılıyor: ${s}`);
  }
});

civi("ilk basamak ÖLÇÜLEMEDİ: dipnot bunu söylüyor, payda 0 DEMİYOR", () => {
  const m = G.geceModeli(SD({ taranan: null, tarananNeden: "HALT çekili", aday: 0, plan: 0, silahli: 0 }));
  const dipnot = m.dususler.map((d) => d.neden ?? "").join(" | ");
  assert.match(dipnot, /ölçülemedi/i, `ölçülemeyen ilk basamak dipnotta yok: ${dipnot}`);
  assert.doesNotMatch(dipnot, /payda 0/i,
    `ölçülemeyen basamak 'payda 0' diye anlatılıyor — iki olgu yine tek cümlede`);
});

civi("payda VARKEN dipnot hiç doğmuyor (oran hesaplandı)", () => {
  const m = G.geceModeli(SD());
  for (const d of m.dususler) {
    assert.equal(d.neden, undefined, `oran hesaplandığı hâlde kusur cümlesi taşınıyor: ${d.neden}`);
    assert.notEqual(d.oran, null);
  }
});

civi("bir basamak eksikse SEBEP o basamağın kendisi — payda sorusuyla karışmıyor", () => {
  const m = G.geceModeli(SD({ plan: null }));
  const sat = m.dususler.find((d) => d.ok.includes(G.AD_PLAN));
  assert.equal(sat.oran, null);
  assert.match(sat.neden, new RegExp(G.AD_PLAN), `eksik basamağın ADI dipnotta yok: ${sat.neden}`);
});

/* ==========================================================================
   3) ORAN VE TABAN — TEK KURAL, İKİ OKUYUCU
   ========================================================================== */
console.log("\n[3] taban ve oranlar");

civi("oranlar İLK basamağa (evrene) göre — elemeyi geçen adaya DEĞİL", () => {
  const m = G.geceModeli(SD({ taranan: 100, aday: 10, plan: 4, silahli: 1 }));
  const o = m.dususler.map((d) => d.oran);
  assert.deepEqual(o, [0.9, 0.06, 0.03],
    "payda kaymış — evren yerine başka bir basamağa bölünüyor");
});

civi("eski kayıtta payda elemeyi geçen adaydır (davranış korunuyor)", () => {
  const m = G.geceModeli(SD({ taranan: null, tarananNeden: null, aday: 10, plan: 4, silahli: 1 }));
  assert.deepEqual(m.dususler.map((d) => d.oran), [0.6, 0.3]);
});

civi("payda beyanı HANGİ DÜNYADA olduğumuzu söylüyor", () => {
  const yeni = G.geceModeli(SD()).paydaBeyani;
  const eski = G.geceModeli(SD({ taranan: null, tarananNeden: null })).paydaBeyani;
  assert.notEqual(yeni, eski, "iki dünyada aynı payda cümlesi basılıyor — biri yalan");
  assert.match(yeni, /TARANAN/);
  assert.match(eski, /ELEMEYİ GEÇEN/);
});

civi("monotonluk ihlalinde NEGATİF oran basılmıyor, ihlal adıyla yazılıyor", () => {
  // `candidates` evreni aşabilir: uyuyan kurulum ateşlemeleri sembol başına birden
  // çok satır doğurur. O zaman şekil huni DEĞİLDİR ve `−−%5` basmak saçmalardı.
  const m = G.geceModeli(SD({ taranan: 2, aday: 5, plan: 1, silahli: 0 }));
  const ilk = m.dususler[0];
  assert.equal(ilk.oran, null, "negatif eriyen oranı basıldı");
  assert.match(ilk.metin, /aşıyor/);
});

civi("boş basamaktan sonra 'hepsi geçti' DENMİYOR", () => {
  const m = G.geceModeli(SD({ taranan: 251, aday: 0, plan: 0, silahli: 0 }));
  const sonraki = m.dususler.find((d) => d.ok.startsWith(G.AD_ADAY));
  assert.match(sonraki.metin, /boş/, `'eriyecek bir şey yoktu' hâli 'eriyen yok' ile karıştı: ${sonraki.metin}`);
});

/* ==========================================================================
   4) OKUMA — UÇTAN GELEN GÖVDE
   ========================================================================== */
console.log("\n[4] gövde okuma");

civi("`taranan` ve `taranan_neden` uçtan okunuyor", () => {
  const sd = G.sonDonguOku({ var: true, date: "2026-08-30", taranan: 251, taranan_neden: null,
                             candidates: 3, plans: 2, armed: 1 });
  assert.equal(sd.taranan, 251);
  assert.equal(sd.tarananNeden, null);
  assert.equal(sd.aday, 3, "eleme sonrası sayı `taranan`ın üstüne yazılmış");
});

civi("alan gelmediyse UYDURULMUYOR (0 değil null)", () => {
  const sd = G.sonDonguOku({ var: true, date: "2026-08-30", candidates: 0 });
  assert.equal(sd.taranan, null);
  assert.equal(sd.tarananNeden, null);
  assert.equal(sd.aday, 0, "ölçülmüş sıfır null'a düştü — iki olgu yine karıştı");
});

civi("sayı olmayan `taranan` bir ölçüm değildir", () => {
  for (const bozuk of ["251", null, {}, NaN, Infinity]) {
    assert.equal(G.sonDonguOku({ var: true, taranan: bozuk }).taranan, null, `kabul edildi: ${bozuk}`);
  }
});

console.log(`\nTOPLAM ${gecen} çivi GEÇTİ.`);
