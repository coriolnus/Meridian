"use client";

/* ============================================================================
   SIR GİRİŞ FORMU — `POST /api/secrets/{name}` (yazan uç) + `GET /api/secrets`
   (adların KAYNAĞI) + `GET /api/secrets/test/{provider}` (canlı doğrulama)
   ----------------------------------------------------------------------------
   NİYE VAR: operatör bildirdi — "KEY'leri girebileceğim bir alan göremedim".
   Doğruydu. `Sirlar.tsx` HANGİ anahtarın kurulu olduğunu gösteriyordu ama
   girmenin yolu yoktu; anahtar girmek terminale inmeyi gerektiriyordu. Yazan uç
   ZATEN vardı ve çalışıyordu (`api.py::api_set_secret`), eksik olan yalnız yüzeydi.

   BEŞ GÜVENLİK KURALI — üslup değil, sözleşme:

   1. DEĞER HİÇBİR YERDE GÖRÜNMEZ. Uç zaten değeri döndürmüyor (yalnız maskeli
      `hint`) ve bu dosya o maskeyi de ÇİZMEZ: son dört karakter bir anahtarı
      tanımaya yeter (`Sirlar.tsx` başlığındaki aynı gerekçe). "Göster" gözü de
      YOK — `GirisFormu.tsx`te var çünkü orada yazılan şey operatörün KENDİ
      parolası ve tek alan; burada 23 alan var, ekran paylaşımında/omuz üstünden
      bir sağlayıcı anahtarı sızarsa geri alınamaz (rotasyon gerekir).
   2. DEĞER URL'E KONMAZ. Uç `{name}`i yolda, DEĞERİ gövdede okuyor — ad bir sır
      değil, değer sır. URL'ler proxy loglarına, tarayıcı geçmişine ve Referer
      başlığına düşer.
   3. ALAN HER GÖNDERİMDEN SONRA TEMİZLENİR — başarısız denemede DE. Ağ düşünce
      yapıştırılan uzun anahtarı kaybettirmek can sıkıcıdır; ama başarısız bir
      POST'tan sonra sırrı React state'inde bekletmek, sekme açık kaldığı sürece
      onu bellekte tutmak demek. Takas bilinçli ve ekranda yazılı.
   4. YALNIZ UCUN BİLDİRDİĞİ ADLAR İÇİN ALAN ÜRETİLİR. Serbest ad kutusu YOK:
      `secrets.py::set` ALLOWED dışındaki her adı reddeder (`ValueError` → 400) ve
      arayüz reddedilecek bir şeyi teklif etmemeli. Liste TSX'e SABİTLENMEDİ —
      `GET /api/secrets` gövdesindeki `secrets` sözlüğünün ANAHTARLARI kullanılır;
      o sözlük `status()` içinde `sorted(ALLOWED)` üzerinden üretiliyor, yani
      ALLOWED büyüdüğünde bu form kendiliğinden büyür. Sabit liste yazsaydık yeni
      bir anahtar SESSİZCE girilemez kalırdı.
   5. SİLME DÜĞMESİ YOK (bu tur kapsam dışı). `DELETE /api/secrets/{name}` ucu
      var ve çalışıyor; yüzeyi ayrı bir turda konur.

   "KAYDEDİLDİ" DEĞİL, "KAYDEDİLDİĞİ ÖLÇÜLDÜ. İyimser güncelleme yok: başarı
   rozetinin kaynağı POST cevabının `status` alanıdır ve o alan sunucuda YAZIMDAN
   SONRA `secrets_mod.status().get(name)` ile yeniden hesaplanır — istemcinin
   varsayımı değil, sunucunun ölçümü. Ayrıca `/api/secrets` bir kez daha okunur
   (üstteki tablo da tazelensin diye).

   ÜÇ HATA HÂLİ AYRI KARŞILANIR çünkü ÜÇ AYRI ÇARE var: 400 = ad/değer reddedildi
   (girdiye bak) · 401 = oturum düştü (yeniden giriş) · kod 0 = sunucuya
   ulaşılamadı (ağa/servise bak). Tek "bir şeyler ters gitti" cümlesi operatörü
   yanlış yere gönderirdi (`gonder.ts` başlığındaki aynı hüküm).

   GRUPLAMA ADIN KENDİSİNDEN TÜRER, TABLO DEĞİL. `GET /api/secrets` gövdesinde
   grup bilgisi YOK (ölçüldü: `secrets.py::status` yalnız {set, source, hint}
   döndürüyor). Bu yüzden ÖN EK kuralı kullanılıyor; tanınmayan bir ad "sınıflanmadı"
   grubuna düşer ve ORADA DA ALANI ÇİZİLİR — sessizce düşürmek, yeni bir ALLOWED
   adını girilemez kılardı.

   "SON TEST/KULLANIM" NEDEN BURADA: FMP vakası (ölçüldü, 2026-08-25) —
   `FMP_API_KEY` canlıda KURULU ama çağrılar HTTP 402 ile düşüyor (43/43,
   `pipeline.fmp_usage.by_status`). "Anahtar yok" ile "anahtar var ama plan
   kapsamıyor" AYRI hâllerdir ve form bunları karıştırırsa operatör aynı anahtarı
   boşuna yeniden yapıştırır. Bu yüzden kurulu her anahtarın yanında, VARSA:
   sağlayıcının son çağrı sonucu + günün kota muhasebesi (`/api/diagnostics`
   `saglayicilar[].ek`; AĞ ÇAĞRISI YOK) ve isteğe bağlı CANLI test düğmesi
   (`/api/secrets/test/{provider}`; ağa GİDER, o yüzden yalnız elle).
   ============================================================================ */
import { KeyRound, PlugZap, Save } from "lucide-react";
import { useState } from "react";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import {
  Field,
  FieldDescription,
  FieldError,
  FieldGroup,
  FieldLabel,
  FieldLegend,
  FieldSet,
} from "@/components/ui/field";
import {
  InputGroup,
  InputGroupAddon,
  InputGroupButton,
  InputGroupInput,
} from "@/components/ui/input-group";
import { Spinner } from "@/components/ui/spinner";

import { type Durum, OturumHatasi, apiGet } from "../../veri";
import { apiPost, type GonderSonucu } from "./gonder";
import { BolumKart, Kapi, Metin, OkRozet, Olculemedi, zamanMetni } from "./parcalar";
import type { SaglayiciSatiri, SirDurumu, SirlarGovdesi, TeshisGovdesi } from "./uctipleri";

/* --- KÜÇÜK DARALTICILAR (uç gövdesi `unknown`; tahmin edilmez, sınanır) ---- */

function nesne(x: unknown): Record<string, unknown> | null {
  return x !== null && typeof x === "object" && !Array.isArray(x) ? (x as Record<string, unknown>) : null;
}

function sayi(x: unknown): number | null {
  return typeof x === "number" && Number.isFinite(x) ? x : null;
}

function metin(x: unknown): string | null {
  return typeof x === "string" && x.trim() !== "" ? x : null;
}

/* --- GRUPLAMA (adın ÖN EKİNDEN; uç grup bilgisi taşımıyor) ---------------- */

const SINIFLANMADI = "siniflanmadi";

/** Adın ön ekinden mantıksal grup. Tanınmayan ad DÜŞÜRÜLMEZ, `siniflanmadi`ya girer. */
function grubu(ad: string): string {
  if (ad.startsWith("FMP_") || ad.startsWith("FINVIZ_") || ad.startsWith("MASSIVE_")) return "veri";
  if (ad.startsWith("ALPACA_")) return "broker";
  if (ad.startsWith("TELEGRAM_") || ad.startsWith("MERIDIAN_WEBHOOK")) return "bildirim";
  if (ad.startsWith("HERMES_") || ad.startsWith("NOUS_") || ad.startsWith("GEMINI_") || ad.startsWith("ANTHROPIC_"))
    return "beyin";
  if (ad.startsWith("LITESTREAM_")) return "yedekleme";
  return SINIFLANMADI;
}

interface GrupKunye {
  readonly baslik: string;
  readonly aciklama: string;
}

const GRUP_KUNYE: Readonly<Record<string, GrupKunye>> = {
  veri: {
    baslik: "Veri sağlayıcıları",
    aciklama:
      "Tarama/haber/bar kaynakları. Bu anahtarlar İCRAYA KARŞI ETKİSİZDİR: girmek ekranları ve tarayıcıları açar, canlı alım-satımı ASLA açmaz (secrets.py başlık şerhi).",
  },
  broker: {
    baslik: "Broker (kâğıt)",
    aciklama:
      "Alpaca paper hesabı. Canlı broker yolu ayrıca iki elle-kurulan env bayrağı + otonomi seviyesiyle kapılı — buraya anahtar girmek o kapıyı AÇMAZ.",
  },
  bildirim: {
    baslik: "Bildirim",
    aciklama: "Telegram / webhook. Alarm ve HALT bildirimlerinin çıkış kanalı.",
  },
  beyin: {
    baslik: "Beyin (LLM)",
    aciklama:
      "Model sağlayıcıları ve zincir sırası. `HERMES_BRAIN_ORDER`, `*_MODEL`, `*_ENDPOINT` alanları bir sır değil YAPILANDIRMA taşır; yine de maskeli girilirler (aynı uç, aynı depo).",
  },
  yedekleme: {
    baslik: "Yedekleme (Litestream)",
    aciklama:
      "S3 kimliği. İKİSİ DE girildiğinde sunucu `state/litestream.env` dosyasını 0600 ile üretir; biri silinirse dosyayı KALDIRIR (yarım kimlik sessiz arıza olurdu).",
  },
  [SINIFLANMADI]: {
    baslik: "Sınıflanmadı",
    aciklama:
      "Uç bu adları bildirdi ama bu ekranın ön-ek kuralları onları bir gruba oturtamadı. Alan yine de çizildi: sessizce düşürmek, yeni bir ALLOWED adını girilemez kılardı.",
  },
};

/** Ekranda görünme sırası. Listede olmayan bir grup en sona eklenir. */
const GRUP_SIRA: readonly string[] = ["veri", "broker", "bildirim", "beyin", "yedekleme", SINIFLANMADI];

/* --- UÇ EŞLEMELERİ (api.py OKUNARAK yazıldı, tahmin edilmedi) ------------- */

/**
 * `GET /api/secrets/test/{provider}` hangi sağlayıcı adlarını tanıyor:
 * `fmp` · `fmp_backup` · `finviz` · `massive` · `alpaca` · `gemini` · `nous`
 * (api.py::api_test_secret; başka her ad 400 döner). Karşılığı OLMAYAN anahtar
 * için düğme HİÇ ÇİZİLMEZ — devre dışı bir düğme, "test var ama şimdi olmaz"
 * diye okunurdu; oysa o anahtarın testi diye bir şey YOK.
 */
function testSaglayicisi(ad: string): string | null {
  if (ad === "FMP_API_KEY") return "fmp";
  if (ad === "FMP_API_KEY_2") return "fmp_backup";
  if (ad === "FINVIZ_API_KEY") return "finviz";
  if (ad === "MASSIVE_API_KEY") return "massive";
  if (ad.startsWith("ALPACA_")) return "alpaca";
  if (ad.startsWith("GEMINI_")) return "gemini";
  if (ad.startsWith("NOUS_")) return "nous";
  return null;
}

/**
 * `/api/diagnostics` `saglayicilar` listesindeki SATIR ADI. Sekiz satır var
 * (finviz · massive · insider · shortinterest · alpaca_veri · alpaca_ticaret ·
 * fmp · uyelik) ve GEMINI/NOUS/TELEGRAM için satır YOKTUR — o anahtarların
 * "son kullanım"ı bu uçtan ölçülemez ve ekran bunu böyle söyler.
 */
function saglikSatiriAdi(ad: string): string | null {
  if (ad.startsWith("FMP_")) return "fmp"; // İKİ anahtar TEK satırı paylaşır — ayrım `by_key`de
  if (ad === "FINVIZ_API_KEY") return "finviz";
  if (ad === "MASSIVE_API_KEY") return "massive";
  if (ad.startsWith("ALPACA_")) return "alpaca_ticaret";
  return null;
}

/* --- GÜNÜN KOTA MUHASEBESİ (`ek.kullanim` — bugün yalnız FMP satırında) ---- */

interface Kullanim {
  readonly tarih: string | null;
  readonly cagri: number | null;
  readonly hata: number | null;
  /** `by_status`: HTTP kodu (ya da yanıt hiç gelmediyse istisna sınıf adı) → sayı. */
  readonly durumDagilimi: readonly (readonly [string, number])[];
  /** `by_key[ad]`. Sözlük VARSA ve ad yoksa 0 (her çağrı `by_key`e işlenir); sözlük yoksa null. */
  readonly buAnahtarCagri: number | null;
  readonly kotaBlokli: boolean | null;
}

function kullanimCikar(satir: SaglayiciSatiri | undefined, anahtarAdi: string): Kullanim | null {
  const ek = nesne(satir?.ek);
  if (ek === null) return null;
  const k = nesne(ek["kullanim"]);
  if (k === null) return null;
  const dagilim = nesne(k["by_status"]);
  const anahtarlar = nesne(k["by_key"]);
  const kb = ek["kota_blokli"];
  return {
    tarih: metin(k["date"]),
    cagri: sayi(k["calls"]),
    hata: sayi(k["fails"]),
    durumDagilimi:
      dagilim === null
        ? []
        : Object.entries(dagilim)
            .map(([etiket, n]) => [etiket, sayi(n)] as const)
            .filter((p): p is readonly [string, number] => p[1] !== null)
            .sort((a, b) => b[1] - a[1]),
    buAnahtarCagri: anahtarlar === null ? null : (sayi(anahtarlar[anahtarAdi]) ?? 0),
    kotaBlokli: typeof kb === "boolean" ? kb : null,
  };
}

function saglikSatiri(teshis: TeshisGovdesi | null, ad: string | null): SaglayiciSatiri | undefined {
  if (ad === null) return undefined;
  const xs = teshis?.saglayicilar?.saglayicilar;
  if (!Array.isArray(xs)) return undefined;
  return xs.find((s) => s.ad === ad);
}

/* --- YAZMA / TEST HÂLLERİ (ayrık birleşim: nedensiz hâl YAZILAMAZ) -------- */

type YazmaHali =
  | { readonly tip: "bos" }
  | { readonly tip: "gonderiliyor" }
  | { readonly tip: "olumlu"; readonly durum: SirDurumu | null; readonly yanEtki: readonly string[] }
  | { readonly tip: "olumsuz"; readonly baslik: string; readonly govde: string };

type TestHali =
  | { readonly tip: "bos" }
  | { readonly tip: "kosuyor" }
  | { readonly tip: "bitti"; readonly ok: boolean | undefined; readonly detay: string | null; readonly ts: string }
  | { readonly tip: "dustu"; readonly baslik: string; readonly govde: string };

/** POST cevabı — `api.py::api_set_secret` dönüşü OKUNARAK yazıldı. */
interface SirYazmaCevabi {
  readonly ok?: boolean;
  readonly name?: string;
  readonly status?: SirDurumu | null;
  readonly skills_enabled?: readonly string[];
  readonly local_agent?: { readonly ok?: boolean; readonly detail?: string; readonly senkron_ts?: string } | null;
  readonly litestream_env?: { readonly durum?: string; readonly path?: string } | null;
}

function yazmaHatasi(s: GonderSonucu): { readonly baslik: string; readonly govde: string } {
  // ÜÇ KOD, ÜÇ ÇARE. Tek mesaja ezmek operatörü yanlış yere gönderirdi.
  if (s.kod === 400) {
    return {
      baslik: "Uç reddetti (400)",
      govde:
        (s.detay ?? "sunucu 400 döndü ama gerekçe metni gelmedi") +
        " · uç yalnız ALLOWED içindeki adları ve BOŞ OLMAYAN bir değeri kabul eder (secrets.py::set).",
    };
  }
  if (s.kod === 401) {
    return {
      baslik: "Oturum düştü (401)",
      govde:
        (s.detay ?? "sunucu 401 döndü, gerekçe metni gelmedi") +
        " · bu bir yazma hatası DEĞİL: panoya yeniden girmek gerekiyor. Anahtar KAYDEDİLMEDİ.",
    };
  }
  if (s.kod === 0) {
    return {
      baslik: "Sunucuya ulaşılamadı",
      govde:
        (s.detay ?? "istek yanıtsız kaldı ve tarayıcı bir gerekçe vermedi") +
        " · isteğin sunucuya HİÇ ulaşmadığı ile ulaşıp cevabın kaybolduğu buradan ayırt EDİLEMEZ; kaydın olup olmadığını üstteki tablodan doğrulayın.",
    };
  }
  return { baslik: `Kaydedilemedi (HTTP ${s.kod})`, govde: s.detay ?? "sunucu gerekçe metni döndürmedi" };
}

/* --- TEK ANAHTAR SATIRI --------------------------------------------------- */

function SirAlani({
  ad,
  durum,
  saglik,
  kullanim,
  onYazildi,
}: {
  readonly ad: string;
  readonly durum: SirDurumu | undefined;
  readonly saglik: SaglayiciSatiri | undefined;
  readonly kullanim: Kullanim | null;
  readonly onYazildi: () => void;
}) {
  const [deger, setDeger] = useState("");
  const [hal, setHal] = useState<YazmaHali>({ tip: "bos" });
  const [test, setTest] = useState<TestHali>({ tip: "bos" });

  const alanKimlik = `sir-${ad}`;
  const saglayici = testSaglayicisi(ad);
  // YAZMADAN SONRAKİ DURUM ÖNCELİKLİDİR: POST cevabındaki `status` sunucuda
  // yazımdan SONRA hesaplandı; `/api/secrets`in bu istekteki kopyası ondan eskidir.
  const gecerliDurum: SirDurumu | undefined = hal.tip === "olumlu" ? (hal.durum ?? undefined) : durum;
  const kaynak = gecerliDurum?.source;
  const envDen = kaynak === "env";

  async function kaydet(e: React.FormEvent) {
    e.preventDefault();
    const v = deger.trim();
    if (v === "") {
      // İSTEK GÖNDERİLMEDİ. Uç zaten 400 verirdi; ağı boşuna yormuyoruz ve
      // hata metni "sunucu reddetti" gibi okunmasın diye AYRI yazılıyor.
      setHal({
        tip: "olumsuz",
        baslik: "Boş değer — istek gönderilmedi",
        govde: "Uç boş/boşluk bir değeri 400 ile reddeder (api.py: missing non-empty 'value'). İstek hiç yapılmadı.",
      });
      return;
    }
    setHal({ tip: "gonderiliyor" });
    // DEĞER GÖVDEDE, AD YOLDA. Ters olsaydı sır proxy loguna/Referer'a düşerdi.
    const s = await apiPost(`/api/secrets/${encodeURIComponent(ad)}`, { value: v });
    setDeger(""); // KURAL 3: başarıda da başarısızlıkta da alan temizlenir
    if (!s.ok) {
      const h = yazmaHatasi(s);
      setHal({ tip: "olumsuz", baslik: h.baslik, govde: h.govde });
      return;
    }
    const g = s.govde as SirYazmaCevabi | null;
    const yanEtki: string[] = [];
    if (Array.isArray(g?.skills_enabled) && g.skills_enabled.length > 0) {
      yanEtki.push(`anahtar-kapılı beceri yeniden değerlendirildi: ${g.skills_enabled.join(", ")}`);
    }
    const la = g?.local_agent;
    if (la !== null && la !== undefined) {
      yanEtki.push(
        `yerel hermes-agent senkronu: ${la.ok === true ? "başarılı" : "başarısız"}` +
          (typeof la.detail === "string" && la.detail !== "" ? ` — ${la.detail}` : ""),
      );
    }
    const le = g?.litestream_env;
    if (le !== null && le !== undefined && typeof le.durum === "string") {
      yanEtki.push(`state/litestream.env: ${le.durum}`);
    }
    setHal({ tip: "olumlu", durum: g?.status ?? null, yanEtki });
    setTest({ tip: "bos" }); // ESKİ TEST SONUCU YENİ ANAHTARI ANLATMAZ — silinir
    onYazildi(); // /api/secrets YENİDEN OKUNUR (iyimser güncelleme yok)
  }

  async function testEt() {
    if (saglayici === null) return;
    setTest({ tip: "kosuyor" });
    try {
      // `veri.ts::apiGet` bu panonun tek OKUMA kapısı; 401'i ayrı sınıfla fırlatır.
      const g = await apiGet<{ ok?: boolean; detail?: string }>(`/api/secrets/test/${encodeURIComponent(saglayici)}`);
      setTest({
        tip: "bitti",
        ok: typeof g.ok === "boolean" ? g.ok : undefined,
        detay: metin(g.detail),
        ts: new Date().toISOString(),
      });
    } catch (e) {
      if (e instanceof OturumHatasi) {
        setTest({
          tip: "dustu",
          baslik: "Oturum düştü (401)",
          govde: "Test yapılmadı — panoya yeniden girmek gerekiyor.",
        });
        return;
      }
      // `apiGet` HTTP hatasını da ağ düşmesini de ATARAK bildirir ve ikisini
      // koda göre AYIRMAZ; metin ayırır ("… → HTTP 400 …" vs. tarayıcının kendi
      // ağ mesajı). Yazma yolunda ayrım `gonder.ts`in `kod` alanıyla yapılıyor.
      setTest({
        tip: "dustu",
        baslik: "Test isteği düştü",
        govde: e instanceof Error ? e.message : String(e),
      });
    }
  }

  return (
    <Field className="gap-1.5" data-invalid={hal.tip === "olumsuz"}>
      <div className="flex flex-wrap items-center gap-2">
        <FieldLabel htmlFor={alanKimlik} className="font-mono text-xs">
          {ad}
        </FieldLabel>
        <OkRozet
          ok={gecerliDurum?.set}
          iyi="kurulu"
          kotu="kurulu değil"
          neden="/api/secrets bu satırda `set` alanını döndürmedi"
        />
        {typeof kaynak === "string" && kaynak !== "" ? (
          <Badge variant="outline" className="font-mono text-[10px]">
            kaynak: {kaynak}
          </Badge>
        ) : null}
      </div>

      <form onSubmit={kaydet}>
        <InputGroup>
          <InputGroupInput
            id={alanKimlik}
            name={alanKimlik}
            type="password"
            autoComplete="off"
            spellCheck={false}
            value={deger}
            onChange={(ev) => setDeger(ev.target.value)}
            placeholder={gecerliDurum?.set === true ? "yeni değer yapıştır (mevcut değer okunamaz)" : "değer yapıştır"}
            disabled={hal.tip === "gonderiliyor"}
            aria-invalid={hal.tip === "olumsuz"}
          />
          <InputGroupAddon align="inline-end">
            <InputGroupButton type="submit" variant="outline" disabled={hal.tip === "gonderiliyor"}>
              {hal.tip === "gonderiliyor" ? <Spinner /> : <Save className="size-3.5" aria-hidden />}
              Kaydet
            </InputGroupButton>
            {saglayici !== null ? (
              <InputGroupButton
                type="button"
                variant="ghost"
                onClick={testEt}
                disabled={test.tip === "kosuyor"}
                title={`GET /api/secrets/test/${saglayici} — CANLI ağ çağrısı yapar`}
              >
                {test.tip === "kosuyor" ? <Spinner /> : <PlugZap className="size-3.5" aria-hidden />}
                Test et
              </InputGroupButton>
            ) : null}
          </InputGroupAddon>
        </InputGroup>
      </form>

      {/* ENV TUZAĞI: dosya deposu env'i EZEMEZ (`secrets.py::_fetch` sırası). */}
      {envDen ? (
        <FieldDescription className="text-destructive">
          Bu ad SÜREÇ ENV'inden geliyor. Form yerel 0600 deposuna yazar, ama <code className="text-[11px]">
            secrets.get
          </code>{" "}
          önce env'i okur (<code className="text-[11px]">secrets.py::_fetch</code>) — buradan girilen değer bu adı
          DEĞİŞTİRMEZ. Env değişkenini servis biriminde değiştirmek gerekir.
        </FieldDescription>
      ) : null}

      {/* --- KAYIT SONUCU --------------------------------------------------- */}
      {hal.tip === "olumlu" ? (
        <FieldDescription>
          <span className="font-medium">Kaydedildiği ölçüldü.</span>{" "}
          {hal.durum === null ? (
            <Olculemedi
              neden="POST cevabı `status` alanı taşımadı — yazım 200 döndü ama sonrası okunamadı; üstteki tablodan doğrulayın"
              kisa
            />
          ) : (
            <>
              sunucu yazımdan sonra yeniden okudu: <code className="text-[11px]">set={String(hal.durum.set)}</code>
              {typeof hal.durum.source === "string" ? (
                <>
                  {" "}
                  · <code className="text-[11px]">source={hal.durum.source}</code>
                </>
              ) : null}
              . Değer geri okunmadı ve okunamaz.
            </>
          )}
          {hal.yanEtki.length > 0 ? <span className="block">Yan etkiler — {hal.yanEtki.join(" · ")}</span> : null}
        </FieldDescription>
      ) : null}

      {hal.tip === "olumsuz" ? (
        <FieldError>
          <span className="font-medium">{hal.baslik}</span> — {hal.govde}
        </FieldError>
      ) : null}

      {/* --- CANLI TEST SONUCU ---------------------------------------------- */}
      {test.tip === "bitti" ? (
        <FieldDescription className="flex flex-wrap items-center gap-2">
          <OkRozet
            ok={test.ok}
            iyi="test geçti"
            kotu="test düştü"
            neden="test ucu `ok` alanını döndürmedi — sonuç okunamadı"
          />
          <Metin deger={test.detay} neden="test ucu `detail` metni döndürmedi" className="text-xs" />
          <span className="text-muted-foreground text-[11px] tabular-nums">{zamanMetni(test.ts) ?? ""}</span>
        </FieldDescription>
      ) : null}

      {test.tip === "dustu" ? (
        <FieldError>
          <span className="font-medium">{test.baslik}</span> — {test.govde}
        </FieldError>
      ) : null}

      {/* --- SON KULLANIM (ağ çağrısı YOK; süreç-içi sayaç + günlük defter) --- */}
      <SonKullanim ad={ad} kurulu={gecerliDurum?.set} saglik={saglik} kullanim={kullanim} />
    </Field>
  );
}

/* --- "ANAHTAR VAR AMA ÇALIŞMIYOR" HÂLİNİN EKRAN KARŞILIĞI ------------------ */

function SonKullanim({
  ad,
  kurulu,
  saglik,
  kullanim,
}: {
  readonly ad: string;
  readonly kurulu: boolean | undefined;
  readonly saglik: SaglayiciSatiri | undefined;
  readonly kullanim: Kullanim | null;
}) {
  if (kurulu !== true) return null; // kurulu olmayan anahtarın "kullanımı" diye bir şey yok
  if (saglik === undefined && kullanim === null) return null; // ölçüm kaynağı yok — boş satır yazmıyoruz

  const cagri = kullanim?.cagri ?? null;
  const hata = kullanim?.hata ?? null;
  // "KURULU AMA HİÇBİR ÇAĞRI GEÇMEDİ" — anahtarı yeniden girmek bunu ÇÖZMEZ.
  const hepsiDustu = cagri !== null && hata !== null && cagri > 0 && hata === cagri;
  const odemeReddi = (kullanim?.durumDagilimi ?? []).find(([etiket]) => etiket === "402");

  return (
    <div className="mt-0.5 flex flex-col gap-1 rounded-md border bg-muted/40 px-2.5 py-1.5">
      <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-[11px]">
        <span className="text-muted-foreground">son kullanım</span>
        {saglik === undefined ? (
          <Olculemedi
            neden={`/api/diagnostics sağlayıcı listesinde bu anahtara karşılık gelen satır yok (${ad} için sağlık sayacı tutulmuyor)`}
            kisa
          />
        ) : (
          <>
            <OkRozet
              ok={saglik.ok}
              iyi="son çağrı başarılı"
              kotu="son çağrı düştü"
              neden={saglik.olculemedi ?? "bu süreçte henüz çağrı yapılmadı — 'bozuk' DEĞİL"}
            />
            {saglik.son_durum !== null && saglik.son_durum !== undefined ? (
              <span className="font-mono text-muted-foreground">son durum: {String(saglik.son_durum)}</span>
            ) : null}
            <span className="text-muted-foreground">
              <Metin
                deger={zamanMetni(saglik.son_cagri_ts)}
                neden="satır bir zaman damgası taşımıyor — bu süreçte çağrı yapılmamış olabilir"
              />
            </span>
          </>
        )}
      </div>

      {kullanim !== null ? (
        <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-[11px]">
          <span className="text-muted-foreground">günlük kota defteri{kullanim.tarih === null ? "" : ` (${kullanim.tarih})`}</span>
          <span className="tabular-nums">
            {cagri === null ? "çağrı: ölçülemedi" : `${cagri} çağrı`}
            {hata === null ? " · hata: ölçülemedi" : ` · ${hata} hata`}
          </span>
          {kullanim.buAnahtarCagri === null ? (
            <Olculemedi neden="defterde `by_key` dağılımı yok — çağrılar anahtar bazında ayrıştırılamadı" kisa />
          ) : (
            <span className="tabular-nums" title="defterdeki by_key dağılımı; ad hiç geçmiyorsa bugün bu anahtarla çağrı yapılmamıştır">
              bu anahtarla: {kullanim.buAnahtarCagri}
            </span>
          )}
          {kullanim.durumDagilimi.length > 0 ? (
            <span className="font-mono text-muted-foreground">
              {kullanim.durumDagilimi.map(([etiket, n]) => `${etiket}×${n}`).join(" ")}
            </span>
          ) : null}
          {kullanim.kotaBlokli === true ? <Badge variant="destructive">kota bloklu (429)</Badge> : null}
        </div>
      ) : null}

      {hepsiDustu ? (
        <Alert variant="destructive" className="mt-1 px-2.5 py-2">
          <AlertTitle className="text-xs">Anahtar KURULU ama bugün hiçbir çağrı geçmedi</AlertTitle>
          <AlertDescription className="text-[11px]">
            {cagri} çağrının {hata}'i düştü.
            {odemeReddi !== undefined
              ? ` Dağılımın ${odemeReddi[1]} tanesi HTTP 402 (Payment Required): bu "anahtar yok" DEĞİL, "anahtar geçerli ama plan bu ucu kapsamıyor" hâlidir — AYNI anahtarı yeniden girmek bunu değiştirmez, sağlayıcıdaki planı değiştirmek gerekir.`
              : " Dağılım yukarıda: kodu okumadan anahtarı yeniden girmek büyük olasılıkla aynı sonucu verir."}
          </AlertDescription>
        </Alert>
      ) : null}
    </div>
  );
}

/* --- FORM GÖVDESİ (adlar UÇTAN gelir) ------------------------------------- */

function GirisGovdesi({
  v,
  teshis,
  onYazildi,
}: {
  readonly v: SirlarGovdesi;
  readonly teshis: TeshisGovdesi | null;
  readonly onYazildi: () => void;
}) {
  const s = v.secrets;
  if (s === undefined || s === null || typeof s !== "object") {
    return (
      <Olculemedi neden="/api/secrets `secrets` sözlüğünü döndürmedi — hangi adların KABUL EDİLDİĞİ okunamadı, uydurma bir liste çizmektense form çizilmedi" />
    );
  }
  const adlar = Object.keys(s).sort();
  if (adlar.length === 0) {
    return (
      <Olculemedi neden="/api/secrets `secrets` sözlüğü BOŞ geldi — secrets.py::ALLOWED bu süreçte hiçbir ad bildirmiyor" />
    );
  }

  // Grupla; bilinmeyen grup en sona.
  const kovalar = new Map<string, string[]>();
  for (const ad of adlar) {
    const g = grubu(ad);
    const mevcut = kovalar.get(g);
    if (mevcut === undefined) kovalar.set(g, [ad]);
    else mevcut.push(ad);
  }
  const sirali = [...kovalar.keys()].sort((a, b) => {
    const ia = GRUP_SIRA.indexOf(a);
    const ib = GRUP_SIRA.indexOf(b);
    return (ia < 0 ? GRUP_SIRA.length : ia) - (ib < 0 ? GRUP_SIRA.length : ib);
  });

  return (
    <FieldGroup className="gap-6">
      {sirali.map((g) => {
        const kunye = GRUP_KUNYE[g];
        return (
          <FieldSet key={g}>
            <FieldLegend variant="label">{kunye?.baslik ?? g}</FieldLegend>
            {kunye === undefined ? (
              <FieldDescription>
                Bu grup için yazılı bir künye yok — ad bilinmeyen bir ön ek taşıyor. Alanlar yine de çizildi.
              </FieldDescription>
            ) : (
              <FieldDescription>{kunye.aciklama}</FieldDescription>
            )}
            <div className="flex flex-col gap-4">
              {(kovalar.get(g) ?? []).map((ad) => {
                const satir = saglikSatiri(teshis, saglikSatiriAdi(ad));
                return (
                  <SirAlani
                    key={ad}
                    ad={ad}
                    durum={s[ad]}
                    saglik={satir}
                    kullanim={kullanimCikar(satir, ad)}
                    onYazildi={onYazildi}
                  />
                );
              })}
            </div>
          </FieldSet>
        );
      })}
    </FieldGroup>
  );
}

/* --- DIŞA AÇILAN BÖLÜM ---------------------------------------------------- */

export function SirGirisi({
  sirlar,
  teshis,
}: {
  readonly sirlar: Durum<SirlarGovdesi>;
  readonly teshis: Durum<TeshisGovdesi>;
}) {
  return (
    <BolumKart
      baslik="Anahtar girişi"
      soru="Yeni bir anahtarı buradan gir — değeri kimse (bu ekran dahil) geri okuyamaz."
      ikon={KeyRound}
      aksiyon={
        <Badge variant="outline" className="text-xs">
          POST /api/secrets/{"{name}"}
        </Badge>
      }
    >
      <Alert>
        <AlertTitle>Değer tek yönlüdür</AlertTitle>
        <AlertDescription>
          Girilen değer yerel 0600 deposuna (<code className="text-[11px]">state/secrets.json</code>) yazılır; uç onu
          geri döndürmez, bu ekran maskeli ipucunu bile çizmez ve değer hiçbir log'a/URL'e girmez. Alan HER gönderimden
          sonra temizlenir — başarısız denemede de, sır tarayıcı belleğinde beklemesin diye. Silme düğmesi bu turda
          bilerek yok.
        </AlertDescription>
      </Alert>

      <Kapi durum={sirlar} yol="/api/secrets">
        {(v) => <GirisGovdesi v={v} teshis={teshis.veri} onYazildi={sirlar.tazele} />}
      </Kapi>

      {teshis.veri === null ? (
        <p className="text-muted-foreground text-xs">
          Sağlayıcı sayaçları bu istekte okunamadı ({teshis.oturumDustu ? "/api/diagnostics 401 döndü" : (teshis.hata ?? "henüz okunmadı")}) —
          “son kullanım” satırları çizilmedi. Anahtar girişi bundan etkilenmez.
        </p>
      ) : null}
    </BolumKart>
  );
}
