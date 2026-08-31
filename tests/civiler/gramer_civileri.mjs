/* ============================================================================
   AJAN GRAMERİ ÇİVİLERİ — node ile GERÇEKTEN koşuluyor (2026-08-31)
   ----------------------------------------------------------------------------
   NEDEN NODE, NEDEN KAYNAK METNİ DEĞİL: `assert "<kimlik>" in kaynak` biçimindeki
   bir çivi, ifadeyi bozan ama adı koruyan mutasyonda ISIRMAZ (v347 incelemesi B4).
   `ui/src/pano/yuzeyler/ajan/gramer.ts`teki her hüküm bu yüzden SAF fonksiyon ve
   burada ÇAĞRILIYOR.

   TEK KAYNAK, İKİ KOŞUCU: bu dosya hem `tests/test_ajan_grameri_v350.py` içinden
   (suite yolu) hem de doğrudan elden koşulur:

       node tests/civiler/gramer_civileri.mjs                  # kendisi esbuild'ler
       node tests/civiler/gramer_civileri.mjs <paket.mjs>      # hazır pakete bağlanır
       node tests/civiler/gramer_civileri.mjs --kendini-sina   # POZİTİF KONTROL

   `--kendini-sina` düzeneğin GERÇEKTEN kırmızıya dönebildiğini gösterir: bilerek
   yanlış bir iddia koşulur ve süreç 1 ile çıkmak ZORUNDADIR. Bu olmadan "35 çivi
   geçti" cümlesi vakumda doğru olabilirdi (v152 disiplini).
   ============================================================================ */
import { execFileSync } from "node:child_process";
import { mkdtempSync, readFileSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import assert from "node:assert/strict";

const KOK = path.resolve(import.meta.dirname, "../..");
const UI = path.join(KOK, "ui");
const ESBUILD = path.join(UI, "node_modules/.bin/esbuild");

const argv = process.argv.slice(2);
const kendiniSina = argv.includes("--kendini-sina");
const hazirPaket = argv.find((a) => !a.startsWith("--")) ?? null;

const gecici = () => mkdtempSync(path.join(tmpdir(), "gramer-civi-"));
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
if (paket === null) paket = paketle("src/pano/yuzeyler/ajan/gramer.ts", "gramer.mjs");
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
    assert.equal(G.rotaEsle("sohbet").muhatap, "bu-dilim-yok",
      "kendini-sınama iddiası: düzenek çalışıyorsa BURADA düşer");
  });
  console.log("HATA: düzenek yanlış bir iddiayı geçirdi — çivi koşucusu KIRIK");
  process.exit(2);
}

// DİKİŞ PAKETİ (2026-08-31, yeniden-inceleme Ö-1b). `alanlar.ts` KAYIT SİSTEMİdir ve
// `gramer.ts`in çözücüsünü oraya kaydetmek bu turun düzeltmesiydi; dikişin kendisi hiçbir
// çiviyle tutulmuyordu. Ayrı paket, çünkü v350 koşucuya YALNIZ gramer paketini veriyor —
// bunu koşucu kendi kurar. `alanlar.ts` React ithal etmiyor (yalnız `lucide-react` ikon
// nesneleri), node'da değerlendirilebiliyor: ölçüldü 2026-08-31.
// POZİTİF KONTROLDEN SONRA kuruluyor: burada esbuild düşerse `--kendini-sina` YİNE sıfırdan
// farklı çıkardı ve "düzenek kırmızıya dönebiliyor" çivisi YANLIŞ sebeple yeşil kalırdı.
const A = await import(paketle("src/pano/alanlar.ts", "alanlar.mjs"));

/* ---- yardımcılar --------------------------------------------------------- */

const AJAN = (o) => ({
  ad: "sef", tur: "bot", anahtar: "bot:sef", model: null, sonOturumTs: null,
  oturumlar: null, teslimler: null, teslimToplam: null, teslimKirpildi: null,
  durum: "ok", neden: null, ...o,
});
const OTURUM = (o) => ({ id: null, ts: null, tsHam: null, model: null, mesajlar: [], ...o });
const MESAJ = (o) => ({ rol: "assistant", ts: null, tsHam: null, metin: "m", kirpildi: null, hamUzunluk: null, ...o });
const TESLIM = (o) => ({ ts: null, olay: "sef_brifingi_teslim", damgalanan: null, detay: null, olculemeyen: null, ...o });

const SIMDI = Date.parse("2026-08-31T14:00:00Z");
const iso = (ms) => new Date(ms).toISOString();
const GUN = 86_400_000;

/* ==========================================================================
   1) ROTA EŞLEME — DÖRT ESKİ DERİN BAĞ KIRILMIYOR
   ========================================================================== */
console.log("\n[1] rota eşleme");

civi("eski `sohbet` bağı kanalın Sohbet sekmesine düşüyor", () => {
  assert.deepEqual(G.rotaEsle("sohbet"), { muhatap: "oneri-hatti", sekme: "sohbet", eskiBag: true });
});
civi("eski `defter` bağı kanalın Defter sekmesine düşüyor", () => {
  assert.deepEqual(G.rotaEsle("defter"), { muhatap: "oneri-hatti", sekme: "defter", eskiBag: true });
});
civi("eski `olcum` bağı kanalın Ölçüm sekmesine düşüyor", () => {
  assert.deepEqual(G.rotaEsle("olcum"), { muhatap: "oneri-hatti", sekme: "olcum", eskiBag: true });
});
civi("eski `filo` bağı AJAN tarafına düşüyor (muhatap seçimi oturuma bırakılır)", () => {
  assert.deepEqual(G.rotaEsle("filo"), { muhatap: null, sekme: "sohbet", eskiBag: true });
});
civi("boş bölüm URL SÖZLEŞMESİ gereği kanalı açar — ve ESKİ BAĞ DEĞİL", () => {
  assert.deepEqual(G.rotaEsle(""), { muhatap: "oneri-hatti", sekme: "sohbet", eskiBag: false });
});
civi("yeni kanonik biçim `<muhatap>.<sekme>` ayrışıyor", () => {
  assert.deepEqual(G.rotaEsle("bot-sef.teslimler"), { muhatap: "bot-sef", sekme: "teslimler", eskiBag: false });
  assert.deepEqual(G.rotaEsle("ana-hermes"), { muhatap: "ana-hermes", sekme: "sohbet", eskiBag: false });
});
civi("tanınmayan sekme muhatabı DÜŞÜRMEDEN Sohbet'e düşüyor", () => {
  const r = G.rotaEsle("bot-karne.olmayan");
  assert.equal(r.muhatap, "bot-karne", "bilinmeyen sekme muhatabı da yuttu — panel sessizce kanala kayardı");
  assert.equal(r.sekme, "sohbet");
});
civi("rotaYaz ↔ rotaEsle gidiş-dönüş", () => {
  const yol = G.rotaYaz("bot-bekci", "teslimler");
  assert.equal(yol, "/dashboard/chat/bot-bekci.teslimler");
  assert.deepEqual(G.rotaEsle(yol.split("/").pop()), { muhatap: "bot-bekci", sekme: "teslimler", eskiBag: false });
});
civi("sekme takımı muhataba göre kapanıyor (bota Defter, kanala Teslimler yok)", () => {
  assert.equal(G.sekmeSec("ajan", "defter"), "sohbet");
  assert.equal(G.sekmeSec("kanal", "teslimler"), "sohbet");
  assert.equal(G.sekmeSec("ajan", "teslimler"), "teslimler");
  assert.equal(G.sekmeSec("kanal", "olcum"), "olcum");
  assert.equal(G.sekmeSec("sahipsiz", "sohbet"), "teslimler");
});
civi("DİFERANSİYEL: eski bağ haritası silinseydi `filo` düz dilim gibi okunurdu", () => {
  const yanlis = { muhatap: "filo", sekme: "sohbet", eskiBag: false };
  assert.notDeepEqual(G.rotaEsle("filo"), yanlis,
    "eski `filo` bağı düz dilim gibi okunuyor — listede `filo` diye bir muhatap yok, panel kanala kayar");
});

/* ---- ÜST BAR KIRINTISI (inceleme Ö-1) ------------------------------------ */
console.log("\n[1b] kırıntı çözücüsü");

civi("yeni kanonik bölüm kırıntıda SEKME etiketine çözülüyor", () => {
  assert.equal(G.bolumEtiketi("bot-sef.teslimler"), "Teslimler");
  assert.equal(G.bolumEtiketi("oneri-hatti.olcum"), "Ölçüm");
  assert.equal(G.bolumEtiketi("sahipsiz-teslimler.teslimler"), "Teslimler");
});
civi("düz kimlik çözücüye DÜŞMEZ — kaydın kendi girdisi eşleşsin diye", () => {
  assert.equal(G.bolumEtiketi("sohbet"), null);
  assert.equal(G.bolumEtiketi("filo"), null);
  assert.equal(G.bolumEtiketi(""), null);
});
civi("tanınmayan sekme kırıntıda UYDURULMUYOR, Sohbet'e düşüyor", () => {
  assert.equal(G.bolumEtiketi("bot-sef.olmayan"), "Sohbet");
});

/* ==========================================================================
   2) AKTİFLİK — bugün / dün / ölçülemedi
   ========================================================================== */
console.log("\n[2] aktiflik hesaplayıcı");

civi("gün anahtarı YEREL gün; çevrilemeyen damga null (uydurma yok)", () => {
  // Aynı ANI temsil eden iki farklı yazım aynı yerel güne düşmeli — aksi hâlde
  // "bugün" hükmü damganın biçimine göre değişirdi.
  const ms = Date.parse("2026-08-31T14:00:00Z");
  assert.equal(G.isoGunu(new Date(ms).toISOString()), G.isoGunu(new Date(ms + 1).toISOString()));
  assert.equal(G.isoGunu(null), null);
  assert.equal(G.isoGunu("20260831-2201"), null, "ayrıştırılamayan damga bir güne UYDURULUYOR");
});
civi("bugün oturumu olan ajan AKTİF", () => {
  const a = AJAN({ oturumlar: [OTURUM({ ts: iso(SIMDI - 3600_000) })], teslimler: [] });
  assert.equal(G.aktiflik(a, SIMDI), "aktif");
});
civi("bugün TESLİMİ olan ajan AKTİF (oturumu dün olsa bile) — iki kaynak da sayılır", () => {
  const a = AJAN({
    oturumlar: [OTURUM({ ts: iso(SIMDI - GUN) })],
    teslimler: [TESLIM({ ts: iso(SIMDI - 600_000) })],
  });
  assert.equal(G.aktiflik(a, SIMDI), "aktif");
});
civi("dünkü kayıtlar + iki kaynak da ÖLÇÜLMÜŞ → SESSİZ", () => {
  const a = AJAN({
    oturumlar: [OTURUM({ ts: iso(SIMDI - GUN) })],
    teslimler: [TESLIM({ ts: iso(SIMDI - GUN) })],
  });
  assert.equal(G.aktiflik(a, SIMDI), "sessiz");
});
civi("iki kaynak da boş AMA ölçülmüş → SESSİZ (boş liste bir ölçümdür)", () => {
  assert.equal(G.aktiflik(AJAN({ oturumlar: [], teslimler: [] }), SIMDI), "sessiz");
});
civi("oturum defteri okunamadıysa SESSİZ DEĞİL, ÖLÇÜLEMEDİ", () => {
  const a = AJAN({ oturumlar: null, teslimler: [TESLIM({ ts: iso(SIMDI - GUN) })], durum: "olculemedi" });
  assert.equal(G.aktiflik(a, SIMDI), "olculemedi",
    "okunamayan defterde bugün konuşulmuş olabilir — 'sessiz' demek ölçülmemişi ölçülmüş saymaktır");
});
civi("teslim defteri okunamadıysa da ÖLÇÜLEMEDİ", () => {
  const a = AJAN({ oturumlar: [OTURUM({ ts: iso(SIMDI - GUN) })], teslimler: null });
  assert.equal(G.aktiflik(a, SIMDI), "olculemedi");
});
civi("zamana YERLEŞMEYEN damga da ÖLÇÜLEMEDİ (ham damga)", () => {
  const a = AJAN({ oturumlar: [OTURUM({ ts: null, tsHam: "20260831-2201" })], teslimler: [] });
  assert.equal(G.aktiflik(a, SIMDI), "olculemedi");
});
civi("ölçülemeyen kaynak varken BİLE bugüne düşen damga AKTİF'i kazanır", () => {
  const a = AJAN({ oturumlar: null, teslimler: [TESLIM({ ts: iso(SIMDI - 60_000) })] });
  assert.equal(G.aktiflik(a, SIMDI), "aktif",
    "ölçülmüş bir bugün damgası, başka kaynağın okunamaması yüzünden yutuluyor");
});
civi("DİFERANSİYEL: `?? []` ile null yutulsaydı hüküm 'sessiz'e kayardı", () => {
  const okunamayan = AJAN({ oturumlar: null, teslimler: null });
  const yutulmus = AJAN({ oturumlar: [], teslimler: [] });
  assert.equal(G.aktiflik(okunamayan, SIMDI), "olculemedi");
  assert.equal(G.aktiflik(yutulmus, SIMDI), "sessiz");
  assert.notEqual(G.aktiflik(okunamayan, SIMDI), G.aktiflik(yutulmus, SIMDI),
    "`null` ile `[]` aynı hükme düşüyor — ölçülemeyen sessizlik ölçülmüş gibi görünür");
});

/* ---- ŞERİDİN SAYIMI (inceleme K-1) --------------------------------------- */
console.log("\n[2b] 'şu an aktif' şeridinin sayımı");

const S_AKTIF = AJAN({ ad: "sef", oturumlar: [OTURUM({ ts: iso(SIMDI - 3600_000) })], teslimler: [] });
const S_SESSIZ = AJAN({ ad: "bekci", oturumlar: [OTURUM({ ts: iso(SIMDI - GUN) })], teslimler: [] });
const S_KOR = AJAN({ ad: "karne", oturumlar: null, teslimler: null, durum: "olculemedi" });

civi("üç hâl ÜÇ AYRI kovada sayılıyor", () => {
  const l = G.muhataplar([S_AKTIF, S_SESSIZ, S_KOR], "#oneri");
  const s = G.aktiflikSayimi(l, SIMDI);
  assert.deepEqual(s.aktif.map((m) => m.dilim), ["bot-sef"]);
  assert.equal(s.sessiz, 1);
  assert.equal(s.olculemedi, 1);
});
civi("KANAL sayıma girmiyor — aktiflik ölçümü yalnız ajanlar için tanımlı", () => {
  const s = G.aktiflikSayimi(G.muhataplar([], "#oneri"), SIMDI);
  assert.deepEqual(s, { aktif: [], sessiz: 0, olculemedi: 0 });
});
civi("K-1 SENARYOSU: üç defter kilitliyken 'ölçülmüş boşluk' cümlesi KURULAMAZ", () => {
  // Maketin kendi vakası: uç ayakta, üç profilin defteri okunamıyor.
  const l = G.muhataplar([S_KOR, AJAN({ ad: "sef", oturumlar: null, teslimler: null }),
                          AJAN({ ad: "bekci", oturumlar: null, teslimler: null })], "#oneri");
  const s = G.aktiflikSayimi(l, SIMDI);
  assert.equal(s.aktif.length, 0);
  assert.equal(s.sessiz, 0, "ölçülemeyen ajanlar 'sessiz' kovasına düştü — ekranda 'boşluk' yazardı");
  assert.equal(s.olculemedi, 3);
});
civi("DİFERANSİYEL: iki-kovalı eski sayım ölçülemeyeni sessize karıştırırdı", () => {
  const l = G.muhataplar([S_AKTIF, S_SESSIZ, S_KOR], "#oneri");
  const s = G.aktiflikSayimi(l, SIMDI);
  const eskiSessiz = l.filter((m) => m.tur === "ajan" && G.aktiflik(m.ajan, SIMDI) !== "aktif").length;
  assert.equal(eskiSessiz, 2, "kıyas kurgusu bayat");
  assert.notEqual(s.sessiz, eskiSessiz,
    "sessiz kovası ölçülemeyeni de sayıyor — şerit iki zıt hüküm basardı");
});

/* ==========================================================================
   3) OTURUM TERSLEME + MODEL-GEÇİŞ KIYASI
   ========================================================================== */
console.log("\n[3] oturum tersleme ve model geçişi");

const UCTAN = [
  OTURUM({ id: "o3", ts: iso(SIMDI - 1 * GUN), model: "fable-5" }),
  OTURUM({ id: "o2", ts: iso(SIMDI - 2 * GUN), model: "opus-5" }),
  OTURUM({ id: "o1", ts: iso(SIMDI - 3 * GUN), model: "opus-5" }),
];

civi("görünüm sırası ESKİDEN→YENİYE çevriliyor (beyanlı tek tersleme)", () => {
  const g = G.oturumlariEskidenYeniye(UCTAN);
  assert.deepEqual(g.map((x) => x.oturum.id), ["o1", "o2", "o3"]);
});
civi("giriş dizisi DEĞİŞTİRİLMİYOR (yerinde tersleme yok)", () => {
  const kopya = UCTAN.map((o) => o.id);
  G.oturumlariEskidenYeniye(UCTAN);
  assert.deepEqual(UCTAN.map((o) => o.id), kopya,
    "uçtan gelen dizi yerinde terslendi — aynı yükü okuyan başka bir hesap sessizce bozulur");
});
civi("model geçişi DOĞRU oturumda ve DOĞRU yönde", () => {
  const g = G.oturumlariEskidenYeniye(UCTAN);
  assert.equal(g[0].gecis, null, "en eski oturumda kıyaslanacak önceki yok");
  assert.equal(g[1].gecis, null, "aynı model iki oturumda geçiş üretti");
  assert.deepEqual(g[2].gecis, { onceki: "opus-5", yeni: "fable-5" });
});
civi("DİFERANSİYEL: eski `i + 1` kıyası terslenmiş dizide YANLIŞ oturumu işaretler", () => {
  const sirali = [...UCTAN].reverse();
  const yanlis = sirali.map((o, i) => {
    const onceki = sirali[i + 1] ?? null;           // ← eski indeks, yeni sırada
    return onceki && onceki.model && o.model && onceki.model !== o.model
      ? { onceki: onceki.model, yeni: o.model } : null;
  });
  const dogru = G.oturumlariEskidenYeniye(UCTAN).map((x) => x.gecis);
  assert.deepEqual(yanlis, [null, { onceki: "fable-5", yeni: "opus-5" }, null]);
  assert.notDeepEqual(dogru, yanlis,
    "kıyas indeksi terslemeyle birlikte düzeltilmemiş — geçiş çipi bir oturum kayar ve YÖNÜ ters çıkar");
});
civi("modeli kaydedilmemiş oturum geçiş UYDURMUYOR", () => {
  const g = G.oturumlariEskidenYeniye([
    OTURUM({ id: "b", ts: iso(SIMDI), model: null }),
    OTURUM({ id: "a", ts: iso(SIMDI - GUN), model: "opus-5" }),
  ]);
  assert.equal(g[1].gecis, null, "eksik model bir 'değişim' gibi okundu");
});

/* ==========================================================================
   4) AKIŞ — teslimler zamanla yerleşiyor, mesaj sırası bozulmuyor
   ========================================================================== */
console.log("\n[4] bot akışı");

const T0 = iso(SIMDI - 6 * 3600_000);
const S1 = iso(SIMDI - 5 * 3600_000);
const S2 = iso(SIMDI - 4 * 3600_000);
const T2 = iso(SIMDI - 3 * 3600_000);

const AKIS_AJANI = AJAN({
  oturumlar: [
    OTURUM({ id: "s2", ts: S2, model: "m", mesajlar: [MESAJ({ metin: "iki-a" }), MESAJ({ metin: "iki-b" })] }),
    OTURUM({ id: "s1", ts: S1, model: "m", mesajlar: [MESAJ({ metin: "bir" })] }),
  ],
  teslimler: [TESLIM({ ts: T2, olay: "gec" }), TESLIM({ ts: T0, olay: "erken" })],
});

civi("oturumlar eskiden→yeniye, teslimler zamanına göre yerleşiyor", () => {
  const a = G.botAkisi(AKIS_AJANI).map((o) => `${o.tur}:${o.oturum?.id ?? o.teslim?.olay ?? o.mesaj?.metin ?? ""}`);
  assert.deepEqual(a, [
    "gun:", "teslim:erken",
    "oturum:s1", "mesaj:bir",
    "oturum:s2", "mesaj:iki-a", "mesaj:iki-b",
    "teslim:gec",
  ]);
});
civi("mesaj sırası uçtan geldiği gibi kalıyor (damgasız mesaj konuşmayı bozmuyor)", () => {
  const m = G.botAkisi(AKIS_AJANI).filter((o) => o.tur === "mesaj").map((o) => o.mesaj.metin);
  assert.deepEqual(m, ["bir", "iki-a", "iki-b"]);
});
civi("damgası çevrilemeyen teslim DÜŞÜRÜLMÜYOR, sonda ayrı başlıkla duruyor", () => {
  const a = G.botAkisi(AJAN({
    oturumlar: [OTURUM({ id: "s", ts: S1, mesajlar: [] })],
    teslimler: [TESLIM({ ts: null, olay: "damgasiz" })],
  }));
  const son = a[a.length - 1];
  assert.equal(a.some((o) => o.tur === "yersiz"), true, "yerleştirilemeyen teslim SESSİZCE düşürüldü");
  assert.equal(son.tur, "teslim");
  assert.equal(son.teslim.olay, "damgasiz");
});
civi("oturum defteri okunamayan ajanda akış BOŞ döner (çağıran ölçülemedi hâlini çizer)", () => {
  assert.deepEqual(G.botAkisi(AJAN({ oturumlar: null, teslimler: [] })), []);
});
civi("mesaj listesi ölçülemedi ile ölçüldü-boş AYRI öğe üretiyor", () => {
  const olculemedi = G.botAkisi(AJAN({ oturumlar: [OTURUM({ ts: S1, mesajlar: null })], teslimler: [] }));
  const bos = G.botAkisi(AJAN({ oturumlar: [OTURUM({ ts: S1, mesajlar: [] })], teslimler: [] }));
  assert.equal(olculemedi.find((o) => o.tur === "bosluk").olculemedi, true);
  assert.equal(bos.find((o) => o.tur === "bosluk").olculemedi, false);
});
civi("gün ayracı gün başına BİR kez", () => {
  const a = G.botAkisi(AKIS_AJANI).filter((o) => o.tur === "gun");
  assert.equal(a.length, 1);
});
civi("mesaj balonunun YANI role bakar; rol kaydedilmemişse ajanın ağzına konmaz", () => {
  assert.equal(G.mesajYani("assistant"), "sag");
  assert.equal(G.mesajYani("user"), "sol");
  assert.equal(G.mesajYani("tool"), "sol");
  assert.equal(G.mesajYani(null), "sol",
    "rolü okunamayan satır SAĞA atıldı — ölçülmemiş bir cümle ajanın sözü sayılırdı");
});

/* ==========================================================================
   5) MUHATAP SEÇİMİ — bayat/yanlış dilim sessiz boş panel üretmiyor
   ========================================================================== */
console.log("\n[5] muhatap seçimi");

const SEF = AJAN({ ad: "sef", tur: "bot", anahtar: "bot:sef", oturumlar: [], teslimler: [] });
const BEKCI = AJAN({ ad: "bekci", tur: "bot", anahtar: "bot:bekci", oturumlar: [], teslimler: [] });
const ANA = AJAN({ ad: "hermes", tur: "ana", anahtar: "ana:hermes", oturumlar: [], teslimler: [] });

civi("dilim KİMLİK ÇİFTİNDEN türüyor (aynı ad, farklı tür ayrı adres)", () => {
  const bot = AJAN({ ad: "hermes", tur: "bot" });
  assert.equal(G.ajanDilimi(bot), "bot-hermes");
  assert.equal(G.ajanDilimi(ANA), "ana-hermes");
  assert.notEqual(G.ajanDilimi(bot), G.ajanDilimi(ANA), "iki muhatap tek adrese düştü — biri erişilemez");
});
civi("liste AJANLAR + KANAL sırasında; roster ölçülemediğinde YALNIZ kanal", () => {
  assert.deepEqual(G.muhataplar([SEF, ANA], "#oneri").map((m) => m.dilim),
    ["bot-sef", "ana-hermes", "oneri-hatti"]);
  assert.deepEqual(G.muhataplar(null, "#oneri").map((m) => m.dilim), ["oneri-hatti"]);
});
civi("eski `filo` bağı (dilim null) son seçili ajana, yoksa @sef'e düşüyor", () => {
  const l = G.muhataplar([BEKCI, SEF, ANA], "#oneri");
  assert.equal(G.muhatapSec(l, null, "ana-hermes", true).muhatap.dilim, "ana-hermes");
  assert.equal(G.muhatapSec(l, null, null, true).muhatap.dilim, "bot-sef", "son seçim yokken @sef beklenirdi");
  assert.equal(G.muhatapSec(G.muhataplar([BEKCI], "#oneri"), null, null, true).muhatap.dilim, "bot-bekci");
  assert.equal(G.muhatapSec(G.muhataplar(null, "#oneri"), null, null, false).muhatap.dilim, "oneri-hatti",
    "roster boşken muhatapsız kare üretiliyor — varsayılan sapmasının gerekçesi de buna dayanıyor");
});
civi("BAYAT seçim sessizce boş panel üretmiyor — kanala düşer VE adı taşınır", () => {
  const l = G.muhataplar([SEF], "#oneri");
  const s = G.muhatapSec(l, "bot-karne", null, true);
  assert.equal(s.muhatap.dilim, "oneri-hatti");
  assert.equal(s.bulunamayan, "bot-karne",
    "istenen muhatap listede yok ve bu SÖYLENMİYOR — kırık bir derin bağ sağlam görünür");
  assert.equal(s.listeOlculemedi, false, "liste OKUNDU; teşhis 'ad yok' olmalı");
});
civi("Ö-2: liste OKUNAMADIYSA teşhis AYRI — 'ad yok' değil 'liste ölçülemedi'", () => {
  const l = G.muhataplar(null, "#oneri");           // roster ölçülemedi
  const s = G.muhatapSec(l, "bot-sef", null, false);
  assert.equal(s.bulunamayan, "bot-sef");
  assert.equal(s.listeOlculemedi, true,
    "okunamayan liste 'bu ad yok' diye okunuyor — operatör SAĞLAM bir yer imini silerdi");
});
civi("GEÇERLİ seçim korunuyor ve iki hüküm de boş", () => {
  const s = G.muhatapSec(G.muhataplar([SEF, ANA], "#oneri"), "ana-hermes", null, true);
  assert.equal(s.muhatap.dilim, "ana-hermes");
  assert.equal(s.bulunamayan, null);
  assert.equal(s.listeOlculemedi, false);
});

/* ==========================================================================
   6) SÜZGEÇ VE TÜRETİLMİŞ ÖZETLER (inceleme Ö-6, Ö-7)
   ========================================================================== */
console.log("\n[6] süzgeç ve türetilmiş özetler");

const KONUSAN = AJAN({
  ad: "sef", tur: "bot",
  oturumlar: [
    OTURUM({ id: "y", ts: S2, model: "fable-5", mesajlar: [MESAJ({ metin: "RVOL eşiği", ts: S2 })] }),
    OTURUM({ id: "e", ts: S1, model: "opus-5", mesajlar: [MESAJ({ metin: "eski söz" }), MESAJ({ metin: "eski söz 2" })] }),
  ],
  teslimler: [TESLIM({ ts: T2 }), TESLIM({ ts: T0 })],
  sonOturumTs: S2,
});

civi("süzgeç ada VE ajanın son mesajına bakıyor", () => {
  const l = G.muhataplar([KONUSAN, BEKCI], "#oneri");
  assert.deepEqual(G.listeSuz(l, "sef", null, null).map((m) => m.dilim), ["bot-sef"]);
  assert.deepEqual(G.listeSuz(l, "rvol", null, null).map((m) => m.dilim), ["bot-sef"]);
});
civi("Ö-6: KANAL da önizlemesinden süzülüyor (yalnız adına göre değil)", () => {
  const l = G.muhataplar([BEKCI], "#oneri");
  const eslesen = G.listeSuz(l, "rvol", "RVOL eşiği 2.1→1.8 · red", null).map((m) => m.dilim);
  assert.deepEqual(eslesen, ["oneri-hatti"],
    "kanalın mesajı sağ panelde eşleşiyor ama SOL sütun onu düşürüyor — okunan konuşma listeden siliniyor");
  assert.deepEqual(G.listeSuz(l, "rvol", null, null).map((m) => m.dilim), [],
    "kanal metni verilmediğinde eşleşme UYDURULUYOR");
});
civi("Ö-6: AÇIK SOHBET süzgeçten muaf", () => {
  const l = G.muhataplar([KONUSAN, BEKCI], "#oneri");
  const d = G.listeSuz(l, "zzz-hicbir-sey", null, "bot-bekci").map((m) => m.dilim);
  assert.deepEqual(d, ["bot-bekci"], "okumakta olunan sohbet listeden düştü — seçim belirsizleşir");
});
civi("boş sorgu listeyi olduğu gibi geçirir", () => {
  const l = G.muhataplar([KONUSAN, BEKCI], "#oneri");
  assert.equal(G.listeSuz(l, "   ", null, null).length, l.length);
});
civi("önizleme EN YENİ mesajdır (ilk oturumun SON satırı) ve okunamayan defterde null", () => {
  assert.deepEqual(G.sonMesajOzeti(KONUSAN), { metin: "RVOL eşiği", ts: S2 });
  assert.equal(G.sonMesajOzeti(AJAN({ oturumlar: null })), null,
    "okunamayan defterde önizleme UYDURULUYOR");
  assert.equal(G.sonMesajOzeti(AJAN({ oturumlar: [] })), null);
});
civi("DİFERANSİYEL: uç sırası ters okunsaydı önizleme EN ESKİ mesajı gösterirdi", () => {
  const yanlis = [...KONUSAN.oturumlar].reverse().find((o) => o.mesajlar?.length)?.mesajlar.at(-1)?.metin;
  assert.equal(yanlis, "eski söz 2", "kıyas kurgusu bayat");
  assert.notEqual(G.sonMesajOzeti(KONUSAN).metin, yanlis,
    "önizleme uç sırası varsayımını ters okuyor — hata yok, boşluk yok, sadece yanlış cümle");
});
civi("son hareket = oturum ve teslim damgalarının EN YENİSİ", () => {
  assert.equal(G.sonHareketTs(KONUSAN), T2);
  assert.equal(G.sonHareketTs(AJAN({ oturumlar: [], teslimler: [] })), null);
});
civi("son teslim YALNIZ teslim kaynağından; ölçülemeyende ve boşta null", () => {
  assert.equal(G.sonTeslimTs(KONUSAN), T2);
  assert.equal(G.sonTeslimTs(AJAN({ oturumlar: [OTURUM({ ts: S2 })], teslimler: null })), null,
    "teslim defteri okunamazken oturum damgası 'son teslim' diye basılıyor");
  assert.equal(G.sonTeslimTs(AJAN({ teslimler: [] })), null);
});
civi("Ö-5: mesaj TOPLAMI ölçülemeyende null, ölçüldü-boşta 0", () => {
  assert.equal(G.mesajToplami(KONUSAN), 3);
  assert.equal(G.mesajToplami(AJAN({ oturumlar: null })), null,
    "okunamayan defterde 0 yazmak 'hiç mesajlaşılmadı' iddiasıdır");
  assert.equal(G.mesajToplami(AJAN({ oturumlar: [OTURUM({ mesajlar: null })] })), null);
  assert.equal(G.mesajToplami(AJAN({ oturumlar: [] })), 0);
});
civi("Ö-5: pencere modelleri TEKİL ve geçiş çipinden AYRI bir ölçüm", () => {
  assert.deepEqual(G.penceredekiModeller(KONUSAN), ["fable-5", "opus-5"]);
  assert.equal(G.penceredekiModeller(AJAN({ oturumlar: null })), null);
  // Gidip geri gelen model: çip İKİ kez çıkar, tekil sayı 2'de kalır.
  const gidipGelen = AJAN({ oturumlar: [
    OTURUM({ ts: iso(SIMDI), model: "opus-5" }),
    OTURUM({ ts: iso(SIMDI - GUN), model: "fable-5" }),
    OTURUM({ ts: iso(SIMDI - 2 * GUN), model: "opus-5" }),
  ] });
  assert.equal(G.penceredekiModeller(gidipGelen).length, 2);
  assert.equal(G.oturumlariEskidenYeniye(gidipGelen.oturumlar).filter((x) => x.gecis !== null).length, 2,
    "iki ölçüm aynı sayıyı veriyor — biri ötekinin yerine geçebilir sanılırdı");
});

/* ==========================================================================
   7) DİKİŞ — çözücü KAYITTA duruyor mu, Ustbar KAYDA mı soruyor
   --------------------------------------------------------------------------
   NEDEN AYRI BİR BÖLÜM (yeniden-inceleme Ö-1b): `bolumEtiketi`nin kendisi [1b]de
   çivili, ama SAF bir fonksiyonun doğru olması onun ÇAĞRILDIĞINI kanıtlamaz.
   Bu turun düzeltmesi iki dikişten ibaretti — `alanlar.ts`in `chat` bloğu çözücüyü
   KAYDEDİYOR, `Ustbar` kendi `find`ini yazmak yerine kayda SORUYOR — ve iki dikişin
   ikisi de mutasyona kördü: `Ustbar`ı eski hâline döndürmek derleniyor ve tüm suite
   yeşil kalıyordu, yani Ö-1'in tarif ettiği arıza sessizce geri gelebiliyordu.
   Bu, bu turun kendi K-2 tezinin ta kendisi: kimliği değil DİKİŞİ ölç.
   ========================================================================== */
console.log("\n[7] dikiş: kayıt sistemi ↔ Ustbar");

civi("Ö-1b: `chat` yüzeyi gramerin çözücüsünü KAYDETMİŞ (yeni kanonik adres kırıntı üretiyor)", () => {
  assert.equal(A.bolumBasligi("chat", "bot-sef.teslimler"), "Teslimler",
    "kayıt çözücüyü tanımıyor — yeni kanonik derin bağda kırıntının ikinci seviyesi SESSİZCE düşer");
  assert.equal(A.bolumBasligi("chat", "oneri-hatti.olcum"), "Ölçüm");
});
civi("Ö-1b: ÖNCE kayıt, SONRA çözücü — kayıtlı kimlik çözücüsüz de başlığını buluyor", () => {
  // `bolumEtiketi` noktasız bölümde null döner; buradaki cevap bu yüzden ancak
  // `bolumler` kaydından gelebilir. Sıra ters çevrilirse dört eski derin bağ başlıksız kalır.
  assert.equal(G.bolumEtiketi("filo"), null);
  assert.equal(A.bolumBasligi("chat", "filo"), "Filo",
    "kayıtlı kimlik başlığını kaybetti — çözücü kaydın ÖNÜNE geçmiş");
});
civi("Ö-1b: çözücü YALNIZ kaydeden yüzeyde — başka yüzeye sızmıyor", () => {
  assert.equal(A.bolumBasligi("finance", "bot-sef.teslimler"), null,
    "her yüzey nokta taşıyan her bölümü 'Teslimler' diye okuyor — kayıt anlamını yitirir");
  assert.equal(A.bolumBasligi("chat", "boyle-bir-sey-yok"), null);
});
civi("Ö-1b: `Ustbar` KAYDA soruyor, kendi `find`ini yazmıyor", () => {
  // Metin çivisi ve bilinçli: `Ustbar.tsx` JSX+React, node'da çağrılamaz. İddia dar tutuldu —
  // incelemenin ADINI verdiği mutasyonu (`a.bolumler.find(...)`e dönüş) ısırır.
  const u = readFileSync(path.join(UI, "src/pano/kabuk/Ustbar.tsx"), "utf-8");
  assert.ok(u.includes("bolumBasligi(yuzey, bolum)"),
    "Ustbar kayıt çözümleyicisini çağırmıyor — kırıntı biçimi ikinci kez, başka yerde yorumlanıyor");
  assert.ok(!u.includes("bolumler"),
    "Ustbar yeniden kendi bölüm aramasını yazmış — `<muhatap>.<sekme>` biçimini bilmeyen bu yol "
    + "yeni derin bağlarda kırıntıyı sessizce düşürür (Ö-1 arızasının ta kendisi)");
});

console.log(`\nTOPLAM ${gecen} çivi GEÇTİ.`);
