"use client";

/* ============================================================================
   HAFIZA · YAPILANDIRMA — üst yüzeyin `profile` sekmesinin karşılığı
   ----------------------------------------------------------------------------
   ALTI ALT SEKME OKUNDU, UYDURULMADI. Üst yüzeyin banka yapılandırma sekmesi şu
   sırayla altı alt sekme taşıyor ve aşağıdaki sıra onun birebir karşılığıdır:

       genel · bellek savunması · yapılandırma · webhook · denetim kaydı ·
       model çağrıları

   Bir tanesi bizde BOŞ ve boşluğun nedeni ekranda yazılı: WEBHOOK okumasının
   vekilde karşılığı YOK. Sekmeyi silmek "böyle bir şey yok" derdi; boş bırakıp
   susmak "ölçtük, hiç webhook yok" derdi. İkisi de yanlış.

   ---------------------------------------------------------------------------
   KAYBEDİLEN İKİ SAYAÇ KUTUSU GERİ GELDİ — VE HİÇ YENİ ÇAĞRI AÇMADAN
   ---------------------------------------------------------------------------
   Bu sayfanın ESKİ sürümü banka başına iki sayaç kutusu çiziyordu: denetim
   sayaçları ve model çağrısı sayaçları. Yeni bilgi mimarisine geçerken ikisi de
   ekrandan düştü ve Görev 2 bedeli yazdı: veri gelmeye DEVAM ediyordu, kimse
   OKUMUYORDU (Görev 2 incelemesi, bulgu M-2). Yani otuz saniyede bir, banka
   başına iki upstream bacağı okuyucusuz koşuyordu.

   BURADA GERİ KONDU VE İKİNCİ BİR ÇAĞRIYLA DEĞİL: kutular kabuğun ZATEN yaptığı
   toplu okumadan (`/api/hindsight`) besleniyor; bu görünüm o gövdeyi yalnız
   AÇIKKEN okuyor. Aynı sayıyı bir de kendi ucundan çekseydik aynı gerçeğin iki
   kopyası olurdu ve ikisi FARKLI pencerelerle gelirdi (toplu uç pencere
   göndermiyor, ayrık uçlar 7 günü açıkça soruyor) — yani iki kutu iki ayrı sayı
   gösterir, hangisinin doğru olduğu ekrandan okunamazdı.

   VARSAYILAN HÂLDE İKİSİ AYNI PENCEREDİR — VE BU ŞERH DÜZELTİLDİ (inceleme M-1).
   Burada önce "ikisi farklı çıkarsa arıza değil, iki farklı sorudur" yazıyordu ve
   o cümle YANLIŞ: toplu uç `period` GÖNDERMİYOR (`api.py::api_hindsight`), üst
   servisin varsayılanı 7 gün (`api.py::_HAFIZA_VARSAYILAN_PENCERE`) ve alt şeridin
   varsayılanı da 7 gün. Yani açılışta ikisi AYNI uçtan AYNI pencereyi okur ve
   ayrışırlarsa bu gerçekten bir arızadır. Ayrışmanın meşru tek yolu operatörün
   alt şeridi 1 ya da 30 güne çevirmesidir — o zaman iki kutu iki ayrı soruyu
   cevaplar.
   ============================================================================ */
import { useEffect, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { cn } from "@/lib/utils";

import type { Bolum } from "../../alanlar";
import { useApi, type Durum } from "../../veri";
import { BolumKart, Kapi as UcKapisi, Olculemedi, Satir } from "../sistem/parcalar";

import { Bolme, Faz2Dugme, Faz2Grup, HamSatirlar, KovaSeridi, PencereDugmeleri, Sayfalama, Secim, VARSAYILAN_ISTATISTIK_PENCERESI, ZarfKapisi, damga, damgaMs, kovaToplami, metin, sayi, secimDegeri, sozluk } from "./parcalar";
import type { DenetimKaydi, HafizaGovdesi, HafizaZarfi, HamGovde, IslemGovdesi, IslemKaydi, IstatistikGovdesi, ModelCagrisi, SayfaliGovde, YapilandirmaGovdesi } from "./uctipleri";

const UC_ISLEMLER = "/api/hindsight/islemler";
const UC_YAPILANDIRMA = "/api/hindsight/yapilandirma";
const UC_DENETIM = "/api/hindsight/denetim";
const UC_DENETIM_IST = "/api/hindsight/denetim-istatistik";
const UC_LLM = "/api/hindsight/llm-istekleri";
const UC_LLM_IST = "/api/hindsight/llm-istatistik";
const UC_TOPLU = "/api/hindsight";

const SAYFA_BOYU = 25;

/* SÖZLÜKLER ÜST YÜZEYDEN OKUNDU (`bank-operations-view.tsx::OPERATION_TYPE_VALUES`
   ve `STATUS_FILTER_VALUES`). Vekil bu iki parametreyi beyaz listeye SOKMUYOR,
   yani tanınmayan bir değer upstream'e gider ve orada 422 olur — gerekçeye döner,
   sessiz kalmaz. Listeyi daraltmak yeni bir işlem türü doğduğu gün onu
   süzülemez yapardı; genişletmek ise olmayan bir türü var göstermek olurdu. */
const ISLEM_TURLERI = [
  { deger: "", etiket: "her tür" },
  { deger: "retain", etiket: "retain" },
  { deger: "consolidation", etiket: "consolidation" },
  { deger: "refresh_mental_model", etiket: "refresh_mental_model" },
  { deger: "file_convert_retain", etiket: "file_convert_retain" },
  { deger: "webhook_delivery", etiket: "webhook_delivery" },
  { deger: "graph_maintenance", etiket: "graph_maintenance" },
  { deger: "vector_index_maintenance", etiket: "vector_index_maintenance" },
  { deger: "export_documents", etiket: "export_documents" },
  { deger: "import_documents", etiket: "import_documents" },
] as const;

const ISLEM_DURUMLARI = [
  { deger: "", etiket: "her durum" },
  { deger: "pending", etiket: "bekliyor" },
  { deger: "processing", etiket: "işleniyor" },
  { deger: "completed", etiket: "bitti" },
  { deger: "failed", etiket: "düştü" },
  { deger: "cancelled", etiket: "iptal" },
] as const;

/* `audit-logs-view.tsx::getActionOptions` — on sekiz eylem. */
const DENETIM_EYLEMLERI = [
  { deger: "", etiket: "her eylem" },
  { deger: "retain", etiket: "retain" },
  { deger: "recall", etiket: "recall" },
  { deger: "reflect", etiket: "reflect" },
  { deger: "create_bank", etiket: "create_bank" },
  { deger: "update_bank", etiket: "update_bank" },
  { deger: "delete_bank", etiket: "delete_bank" },
  { deger: "clear_memories", etiket: "clear_memories" },
  { deger: "consolidation", etiket: "consolidation" },
  { deger: "batch_retain", etiket: "batch_retain" },
  { deger: "create_mental_model", etiket: "create_mental_model" },
  { deger: "refresh_mental_model", etiket: "refresh_mental_model" },
  { deger: "delete_mental_model", etiket: "delete_mental_model" },
  { deger: "create_directive", etiket: "create_directive" },
  { deger: "delete_directive", etiket: "delete_directive" },
  { deger: "file_convert_retain", etiket: "file_convert_retain" },
  { deger: "webhook_delivery", etiket: "webhook_delivery" },
  { deger: "memory_defense", etiket: "memory_defense" },
] as const;

const DENETIM_TASIYICILARI = [
  { deger: "", etiket: "her yol" },
  { deger: "http", etiket: "http" },
  { deger: "mcp", etiket: "mcp" },
  { deger: "system", etiket: "system" },
] as const;

/* `llm-requests-view.tsx::getStatusOptions` / `getOperationOptions`. */
const LLM_DURUMLARI = [
  { deger: "", etiket: "her durum" },
  { deger: "success", etiket: "başarılı" },
  { deger: "error", etiket: "hatalı" },
] as const;

const LLM_ISLEMLERI = [
  { deger: "", etiket: "her işlem" },
  { deger: "retain", etiket: "retain" },
  { deger: "reflect", etiket: "reflect" },
  { deger: "consolidation", etiket: "consolidation" },
  { deger: "refresh_mental_model", etiket: "refresh_mental_model" },
] as const;

/**
 * İKİ DAMGA ARASI SÜRE — ve neden `sureMetni` DEĞİL (inceleme I-2 + M-6).
 *
 * ADI DEĞİŞTİ: `sistem/parcalar.tsx` zaten saniye alan bir süre yardımcısı ihraç
 * ediyor. Aynı yüzeyde aynı adın iki sözleşmesi (biri saniye alır, biri iki
 * damga) bir sonraki dokunuşta yanlış olanı içe aktarmayı SESSİZ kılardı —
 * ikisi de `string | null` döndürdüğü için tip hatası bile doğmazdı.
 *
 * KAPI DA DEĞİŞTİ: ham `Date.parse` yerine `damgaMs` (dizge → ISO benzeri →
 * çözülebilir). Korumasız hâli, denetim satırının damgası ISO değilse UYDURMA
 * bir süre bastırıyordu — üstelik aynı satırın zaman sütunu `damga()`den geçtiği
 * için "Başlangıç: ölçülemedi · Süre: 8.640,0 dk" gibi kendisiyle çelişen bir
 * satır çıkardı. Denetim öğesinin şekli canlıda ÖLÇÜLEMEDİ (liste boş geldi),
 * yani bu risk teorik değil.
 */
function araSuresi(baslangic: unknown, bitis: unknown): string | null {
  const t1 = damgaMs(baslangic);
  const t2 = damgaMs(bitis);
  if (t1 === null || t2 === null) return null;
  const ms = t2 - t1;
  if (ms < 0) return null;
  if (ms < 1000) return `${ms} ms`;
  if (ms < 60_000) return `${(ms / 1000).toLocaleString("tr-TR", { maximumFractionDigits: 1 })} sn`;
  return `${(ms / 60_000).toLocaleString("tr-TR", { maximumFractionDigits: 1 })} dk`;
}

function msMetni(deger: unknown): string | null {
  const ms = sayi(deger);
  if (ms === null) return null;
  if (ms < 1000) return `${ms.toLocaleString("tr-TR")} ms`;
  if (ms < 60_000) return `${(ms / 1000).toLocaleString("tr-TR", { maximumFractionDigits: 1 })} sn`;
  return `${(ms / 60_000).toLocaleString("tr-TR", { maximumFractionDigits: 1 })} dk`;
}

/* ---------------------------------------------------------------------------
   SAYAÇ KUTULARI — kabuğun toplu okumasından, yeni çağrı YOK (dosya başlığı)
   --------------------------------------------------------------------------- */
function SayacKutulari({ toplu, bank }: { readonly toplu: Durum<HafizaGovdesi>; readonly bank: string }) {
  return (
    <UcKapisi durum={toplu} yol={UC_TOPLU}>
      {(g) => {
        const kota = g.kota?.[bank];
        const operasyon = g.operasyon?.[bank];
        return (
          <div className="grid gap-3 sm:grid-cols-2">
            <div className="rounded-lg border p-3">
              <h4 className="font-medium text-muted-foreground text-xs uppercase tracking-wide">
                Denetim sayaçları
              </h4>
              <p className="mt-0.5 mb-2 text-[11px] text-muted-foreground">
                bankaya ne işlendi — üst servisin kendi penceresi
              </p>
              {kutuGovdesi(operasyon?.audit_stats, operasyon?.neden, "Denetim sayaçları")}
            </div>
            <div className="rounded-lg border p-3">
              <h4 className="font-medium text-muted-foreground text-xs uppercase tracking-wide">
                Model çağrısı sayaçları
              </h4>
              <p className="mt-0.5 mb-2 text-[11px] text-muted-foreground">
                bu bankanın model kullanımı — üst servisin kendi penceresi
              </p>
              {kutuGovdesi(kota?.llm_stats, kota?.neden, "Model çağrısı sayaçları")}
            </div>
          </div>
        );
      }}
    </UcKapisi>
  );
}

/** Sayaç kutusunun DÖRT hâli — kutunun kendisi hiç gelmemiş olabilir (banka
 *  gövdede yok), gerekçeli düşmüş olabilir, boş gelmiş olabilir, ya da dolu. */
function kutuGovdesi(govde: unknown, neden: string | null | undefined, ne: string) {
  if (neden) return <Olculemedi neden={`${ne} okunamadı`} teknik={neden} />;
  if (govde === undefined) {
    return (
      <Olculemedi
        neden={`${ne} bu banka için bildirilmedi`}
        teknik="toplu okuma bu bankanın kutusunu hiç döndürmedi"
      />
    );
  }
  if (govde === null) {
    return (
      <Olculemedi
        neden={`${ne} için ölçüm denendi, gövde gelmedi`}
        teknik="gövde boş döndü ve gerekçe de taşınmadı"
      />
    );
  }
  const s = sozluk(govde);
  if (s === null) {
    return (
      <Olculemedi
        neden={`${ne} tanınmayan bir biçimde geldi`}
        teknik="beklenen sözlük, gelen başka bir tip — şema sürüklenmiş olabilir"
      />
    );
  }
  /* ŞEKLİ ARTIK ÖLÇÜLDÜ (inceleme M-1, canlı ölçüm 16:25 UTC): bu gövde
     `bank_id·buckets·period·start·trunc` taşıyor ve `buckets[0]` =
     `statuses·time·tokens·total`. Yani tam olarak `IstatistikGovdesi`dir ve bu
     dosyada ZATEN bir kova şeridi var. Ham basmak, ölçülmüş bir sayacı 140
     karakterde kesilmiş bir JSON satırına çevirmekti — okunabilir sayaç yoktu.
     Kova gelmiyorsa ham basım GERİ DÖNER: kaybolan alan olmasın. */
  const kovalar = (s as IstatistikGovdesi).buckets;
  if (Array.isArray(kovalar)) {
    return (
      <div className="flex flex-col gap-2">
        <KovaSeridi kovalar={kovalar} deger={kovaToplami} ne={ne} />
        <HamSatirlar govde={s} atla={["buckets"]} />
      </div>
    );
  }
  return <HamSatirlar govde={s} />;
}

/* ---------------------------------------------------------------------------
   İŞLEMLER
   --------------------------------------------------------------------------- */
function Islemler({ bank }: { readonly bank: string }) {
  const [durum, setDurum] = useState("__hepsi");
  const [tur, setTur] = useState("__hepsi");
  const [ustleriGizle, setUstleriGizle] = useState(true);
  const [atlanan, setAtlanan] = useState(0);

  useEffect(() => {
    setAtlanan(0);
  }, [bank, durum, tur, ustleriGizle]);

  const yol = [
    `${UC_ISLEMLER}?bank=${encodeURIComponent(bank)}`,
    `limit=${SAYFA_BOYU}`,
    `offset=${atlanan}`,
    secimDegeri(durum) ? `status=${encodeURIComponent(secimDegeri(durum))}` : "",
    secimDegeri(tur) ? `islem_turu=${encodeURIComponent(secimDegeri(tur))}` : "",
    ustleriGizle ? "exclude_parents=true" : "",
  ]
    .filter(Boolean)
    .join("&");
  const islemler = useApi<HafizaZarfi<IslemGovdesi>>(yol);

  /* İKİ AD DA OKUNUR — VE BU BİR ÖLÇÜM SONUCU (bkz. `uctipleri.ts::IslemGovdesi`):
     bu uç diziyi `items` altında DEĞİL `operations` altında veriyor (A1'de
     ölçüldü). Tek ada bağlanan ekran "işlem yok" derdi, üstelik sessizce. */
  const dizi = (g: IslemGovdesi): readonly IslemKaydi[] | null =>
    Array.isArray(g.operations) ? g.operations : Array.isArray(g.items) ? g.items : null;

  return (
    <div className="flex flex-col gap-3">
      <div className="flex flex-wrap items-end gap-3">
        <Secim etiket="Durum" deger={durum} setDeger={setDurum} secenekler={ISLEM_DURUMLARI} genislik="w-40" />
        <Secim etiket="İşlem türü" deger={tur} setDeger={setTur} secenekler={ISLEM_TURLERI} genislik="w-56" />
        <label className="flex h-8 cursor-pointer items-center gap-1.5 self-end text-sm">
          <Checkbox
            checked={ustleriGizle}
            onCheckedChange={(c) => setUstleriGizle(c === true)}
            aria-label="Toplu işlerin şemsiye kaydını gizle"
          />
          Şemsiye kayıtları gizle
        </label>
      </div>
      <p className="text-muted-foreground text-[11px]">
        Üst yüzey şemsiye kayıtları HER ZAMAN gizliyor; burada seçilebilir bırakıldı, çünkü bir
        toplu işin alt parçalarıyla kendisini ayırt etmek arıza aramanın yarısıdır. Bu uçta sayfa
        tavanı da daha düşüktür (yüz kayıt) ve sunucu istenen sayıyı oraya kırpar.
      </p>

      <UcKapisi durum={islemler} yol={UC_ISLEMLER}>
        {(z) => (
          <ZarfKapisi zarf={z} ne="İşlemler">
            {(g) => {
              const ogeler = dizi(g);
              if (ogeler === null) {
                return (
                  <Olculemedi
                    neden="İşlem listesi tanınmayan bir biçimde geldi"
                    teknik="ne işlem dizisi ne de öğe dizisi bulundu — şema sürüklenmiş olabilir"
                  />
                );
              }
              if (ogeler.length === 0) {
                return (
                  <p className="text-muted-foreground text-sm">
                    {atlanan === 0
                      ? "Bu süzgeçle okundu ve eşleşen işlem YOK. Bu ölçülmüş bir boşluktur."
                      : "Bu sayfada işlem YOK — liste daha önceki bir sayfada bitmiş."}
                  </p>
                );
              }
              return (
                <div className="overflow-x-auto">
                  <Table className="min-w-[52rem]">
                    <TableHeader className="bg-muted/50">
                      <TableRow>
                        <TableHead className="w-28">Kimlik</TableHead>
                        <TableHead>Tür</TableHead>
                        <TableHead className="w-44">Oluşturma</TableHead>
                        <TableHead className="w-44">Güncelleme</TableHead>
                        <TableHead className="w-56">Durum</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {ogeler.map((o, i) => {
                        const kimlik = metin(o.id);
                        const ilerleme = sozluk(o.progress);
                        const hata = metin(o.error_message);
                        return (
                          <TableRow key={kimlik ?? `islem-${atlanan + i}`}>
                            <TableCell className="font-mono text-[11px]">
                              {kimlik === null ? (
                                <Olculemedi
                                  neden="Kimlik gelmedi"
                                  teknik="satırda kimlik alanı yok ya da dizge değil"
                                  kisa
                                />
                              ) : (
                                <span title={kimlik}>{kimlik.slice(0, 8)}</span>
                              )}
                            </TableCell>
                            <TableCell className="max-w-0">
                              <span className="block truncate font-medium text-sm">
                                {metin(o.task_type) ?? (
                                  <Olculemedi
                                    neden="İşlem türü gelmedi"
                                    teknik="tür alanı yok ya da dizge değil"
                                    kisa
                                  />
                                )}
                              </span>
                              <span className="block truncate text-[11px] text-muted-foreground">
                                {metin(o.filename) ?? metin(o.document_id) ?? "belge/dosya bağı gelmedi"}
                              </span>
                            </TableCell>
                            <TableCell className="text-muted-foreground text-xs tabular-nums">
                              {damga(o.created_at) ?? (
                                <Olculemedi
                                  neden="Oluşturma zamanı gelmedi"
                                  teknik="oluşturma damgası gelmedi ya da çözülemedi"
                                  kisa
                                />
                              )}
                            </TableCell>
                            <TableCell className="text-muted-foreground text-xs tabular-nums">
                              {damga(o.updated_at) ?? (
                                <Olculemedi
                                  neden="Güncelleme zamanı gelmedi"
                                  teknik="güncelleme damgası gelmedi ya da çözülemedi"
                                  kisa
                                />
                              )}
                            </TableCell>
                            <TableCell>
                              <div className="flex flex-col gap-1">
                                {metin(o.status) === null ? (
                                  <Olculemedi
                                    neden="Durum gelmedi"
                                    teknik="durum alanı yok ya da dizge değil"
                                    kisa
                                  />
                                ) : (
                                  <Badge variant="outline" className="w-fit font-normal text-[11px]">
                                    {metin(o.status)}
                                  </Badge>
                                )}
                                {ilerleme !== null ? (
                                  <span className="text-[11px] text-muted-foreground tabular-nums">
                                    {metin(ilerleme.stage) ?? "aşama bildirilmedi"}
                                    {sayi(ilerleme.processed) !== null && sayi(ilerleme.total) !== null
                                      ? ` · ${sayi(ilerleme.processed)}/${sayi(ilerleme.total)}`
                                      : ""}
                                  </span>
                                ) : null}
                                {hata !== null ? (
                                  <span className="text-[11px] text-destructive" title={hata}>
                                    {hata.length > 90 ? `${hata.slice(0, 90)}…` : hata}
                                  </span>
                                ) : null}
                              </div>
                            </TableCell>
                          </TableRow>
                        );
                      })}
                    </TableBody>
                  </Table>
                </div>
              );
            }}
          </ZarfKapisi>
        )}
      </UcKapisi>

      {/* Sayfalama kapının İÇİNDE (Görev 2 incelemesi, bulgu M-4). */}
      <UcKapisi durum={islemler} yol={UC_ISLEMLER} iskelet={<></>}>
        {(z) =>
          z.neden || !z.govde ? null : (
            <Sayfalama
              atlanan={atlanan}
              gelen={(dizi(z.govde) ?? []).length}
              sayfaBoyu={SAYFA_BOYU}
              toplam={sayi(z.govde.total)}
              setAtlanan={setAtlanan}
            />
          )
        }
      </UcKapisi>

      <Faz2Grup>
        <Faz2Dugme ne="bekleyen işi iptal eder">İptal et</Faz2Dugme>
        <Faz2Dugme ne="düşmüş işi yeniden kuyruğa alır">Yeniden dene</Faz2Dugme>
        <Faz2Dugme ne="bitmiş işin kaydını siler">Kaydı sil</Faz2Dugme>
      </Faz2Grup>
    </div>
  );
}

/* ---------------------------------------------------------------------------
   BELLEK SAVUNMASI — kaynağı AYRI BİR UÇ DEĞİL, YAPILANDIRMANIN İÇİ
   ----------------------------------------------------------------------------
   ÖLÇÜLDÜ VE BİR VARSAYIMI DÜZELTTİ: bu bölüm üst yüzeyde denetim kaydının
   içinde DEĞİL, banka yapılandırma sekmesinin İKİNCİ alt sekmesidir; ve verisi
   ayrı bir uçtan değil `GET /config` gövdesinden okunuyor
   (`memory-defense-section.tsx::readPolicy` → `config.memory_defense`).
   Ayrı bir uç aramak boşuna bir 404 olurdu.
   --------------------------------------------------------------------------- */
function Savunma({ govde }: { readonly govde: YapilandirmaGovdesi }) {
  /* ÜÇ KANAL DA OKUNUR (inceleme M-2) — `fact_type`/`type` deseninin aynısı.
     ÖLÇÜM: canlı `GET /config` gövdesi `bank_id·config·overrides` taşıyor ve
     `memory_defense` anahtarı `overrides` ALTINDA görüldü (16:25 UTC eki);
     `config`in anahtarları hiç sayılmadığı için orada da olduğu doğrulanmış
     DEĞİL. Yalnız `config`e bakan ilk yazım, brief'in zorunlu kıldığı alt sekmede
     canlı bankada "politika gelmedi" derdi — halbuki politika aynı gövdededir. */
  const ayarlar = sozluk(govde.config) ?? govde;
  const gecersizKilmalar = sozluk(govde.overrides);
  const kanallar: readonly (readonly [string, HamGovde | null])[] = [
    ["ayarlar", sozluk(ayarlar.memory_defense)],
    ["geçersiz kılmalar", gecersizKilmalar === null ? null : sozluk(gecersizKilmalar.memory_defense)],
    ["gövde kökü", sozluk(govde.memory_defense)],
  ];
  const bulunan = kanallar.find(([, p]) => p !== null);
  const politika = bulunan?.[1] ?? null;
  if (politika === null) {
    return (
      <Olculemedi
        neden="Bellek savunması politikası gelmedi"
        teknik="yapılandırma gövdesinde savunma bloğu yok ya da sözlük değil — bu bankada tanımlı olmayabilir"
      />
    );
  }
  const acik = politika.enabled;
  const kurallar = politika.rules;
  return (
    <div className="flex flex-col gap-3">
      {/* HANGİ KANALDAN OKUNDUĞU YAZILI: üç kanal aynı adı taşıyor ve hangisinin
          dolu olduğu, "devralınan" ile "bu bankaya özgü" ayrımının ta kendisi. */}
      <Satir etiket="Okunduğu yer">
        <span className="text-xs">{bulunan?.[0] ?? "bilinmiyor"}</span>
      </Satir>
      <Satir etiket="Durum">
        {acik === true ? (
          <Badge variant="outline">açık</Badge>
        ) : acik === false ? (
          <Badge variant="outline">kapalı</Badge>
        ) : (
          <Olculemedi
            neden="Açık/kapalı bildirilmedi"
            teknik="etkinlik bayrağı gelmedi — 'kapalı' demek ölçülmemiş bir durumu ölçülmüş göstermek olurdu"
            kisa
          />
        )}
      </Satir>
      <Bolme baslik="Kurallar" aciklama="Hangi dedektör tetiklendiğinde ne yapılıyor.">
        {!Array.isArray(kurallar) ? (
          <Olculemedi
            neden="Kural listesi tanınmayan bir biçimde geldi"
            teknik="beklenen dizi, gelen başka bir tip — şema sürüklenmiş olabilir"
          />
        ) : kurallar.length === 0 ? (
          <p className="text-muted-foreground text-sm">
            Politika okundu ve tanımlı kural YOK. Bu ölçülmüş bir boşluktur.
          </p>
        ) : (
          <div>
            {kurallar.map((k, i) => {
              const kural = sozluk(k);
              return (
                <Satir key={i} etiket={kural === null ? `kural ${i + 1}` : (metin(kural.on) ?? `kural ${i + 1}`)}>
                  {kural === null ? (
                    <Olculemedi neden="Kural okunamadı" teknik="kural sözlük değil" kisa />
                  ) : (
                    (metin(kural.action) ?? (
                      <Olculemedi neden="Eylem gelmedi" teknik="kuralın eylem alanı yok ya da dizge değil" kisa />
                    ))
                  )}
                </Satir>
              );
            })}
          </div>
        )}
      </Bolme>
      <Faz2Grup>
        <Faz2Dugme ne="savunmayı açar ya da kapatır">Savunmayı değiştir</Faz2Dugme>
        <Faz2Dugme ne="dedektörün eylemini değiştirir">Kuralı değiştir</Faz2Dugme>
      </Faz2Grup>
    </div>
  );
}

/* ---------------------------------------------------------------------------
   AYARLAR — ÇÖZÜLMÜŞ DEĞER İLE GEÇERSİZ KILMA AYRI
   Üst yüzeyin kendi gerekçesi: çözülmüş değer "devralınan doğru" ile "elle doğru
   yapılmış"ı ayırt edemez. Zarfın bu iki alanı gerçekten taşıyıp taşımadığı bu
   turda ölçülmedi — ekran hangisinin gelmediğini yazar.
   --------------------------------------------------------------------------- */
function Ayarlar({ govde }: { readonly govde: YapilandirmaGovdesi }) {
  const ayarlar = sozluk(govde.config);
  const gecersizKilmalar = sozluk(govde.overrides);
  return (
    <div className="flex flex-col gap-4">
      <Bolme
        baslik="Çözülmüş ayarlar"
        aciklama="Bankanın şu an geçerli ayarları — devralınanlar dahil. Alan adları üst servisin sözlüğüdür ve çevrilmez."
      >
        {ayarlar === null ? (
          /* GÖVDE SARMALSIZ GELMİŞ OLABİLİR: zarf ölçülmedi. `config` yoksa
             gövdenin KENDİSİ ayarlar olabilir — ikisi de çizilir, hangisinin
             okunduğu yazılı. */
          <>
            <Olculemedi
              neden="Ayarlar sarmalı gelmedi"
              teknik="gövdede ayar bloğu yok ya da sözlük değil — gövdenin kendisi ayar listesi olabilir, aşağıda ham basılıyor"
            />
            <HamSatirlar govde={govde} atla={["overrides"]} />
          </>
        ) : (
          <HamSatirlar govde={ayarlar} />
        )}
      </Bolme>
      <Bolme
        baslik="Bankaya özgü geçersiz kılmalar"
        aciklama="Yalnız bu banka için elle ayarlanmış olanlar. Boş olması bir arıza değil: hiçbir ayar devralınandan sapmıyor demektir."
      >
        {gecersizKilmalar === null ? (
          <Olculemedi
            neden="Geçersiz kılmalar gelmedi"
            teknik="gövde geçersiz kılma bloğunu döndürmedi — hangi ayarın devralındığı bu okumadan ayırt edilemiyor"
          />
        ) : (
          <HamSatirlar govde={gecersizKilmalar} />
        )}
      </Bolme>
      <Faz2Grup>
        <Faz2Dugme ne="banka ayarlarını değiştirir">Ayarları değiştir</Faz2Dugme>
        <Faz2Dugme ne="bankanın şablonunu dışa aktarır">Şablonu dışa aktar</Faz2Dugme>
        <Faz2Dugme ne="çıkarımı yazmadan dener">Kuru koşum</Faz2Dugme>
      </Faz2Grup>
    </div>
  );
}

/* --------------------------------------------------------------------------- */

export function Yapilandirma({
  bank,
  kayit,
  toplu,
}: {
  readonly bank: string | null;
  readonly kayit: Bolum;
  readonly toplu: Durum<HafizaGovdesi>;
}) {
  const [sekme, setSekme] = useState("genel");

  const [denetimEylemi, setDenetimEylemi] = useState("__hepsi");
  const [tasiyici, setTasiyici] = useState("__hepsi");
  const [denetimAtlanan, setDenetimAtlanan] = useState(0);
  const [denetimPenceresi, setDenetimPenceresi] = useState(VARSAYILAN_ISTATISTIK_PENCERESI);
  const [acikDenetim, setAcikDenetim] = useState<DenetimKaydi | null>(null);

  const [llmDurumu, setLlmDurumu] = useState("__hepsi");
  const [llmIslemi, setLlmIslemi] = useState("__hepsi");
  const [llmAtlanan, setLlmAtlanan] = useState(0);
  const [llmPenceresi, setLlmPenceresi] = useState(VARSAYILAN_ISTATISTIK_PENCERESI);

  useEffect(() => {
    setDenetimAtlanan(0);
    setAcikDenetim(null);
  }, [bank, denetimEylemi, tasiyici]);

  useEffect(() => {
    setLlmAtlanan(0);
  }, [bank, llmDurumu, llmIslemi]);

  /* HER OKUMA KENDİ SEKMESİ AÇIKKEN AÇILIR (`yol === null` iken `useApi` istek
     açmaz): altı sekmenin altısını birden çekmek, beşini okumadan ödemek olurdu.
     Sayaç kutuları BUNUN DIŞINDA ve nedeni dosya başlığında: onlar kabuğun zaten
     yaptığı okumadan geliyor, yani bu görünüm için yeni bir çağrı yok. */
  const yapilandirmaYolu =
    bank === null || (sekme !== "ayarlar" && sekme !== "savunma")
      ? null
      : `${UC_YAPILANDIRMA}?bank=${encodeURIComponent(bank)}`;
  const yapilandirma = useApi<HafizaZarfi<YapilandirmaGovdesi>>(yapilandirmaYolu);

  const denetimYolu =
    bank === null || sekme !== "denetim"
      ? null
      : [
          `${UC_DENETIM}?bank=${encodeURIComponent(bank)}`,
          `limit=${SAYFA_BOYU}`,
          `offset=${denetimAtlanan}`,
          secimDegeri(denetimEylemi) ? `action=${encodeURIComponent(secimDegeri(denetimEylemi))}` : "",
          secimDegeri(tasiyici) ? `transport=${encodeURIComponent(secimDegeri(tasiyici))}` : "",
        ]
          .filter(Boolean)
          .join("&");
  const denetim = useApi<HafizaZarfi<SayfaliGovde<DenetimKaydi>>>(denetimYolu);

  const denetimIstYolu =
    bank === null || sekme !== "denetim"
      ? null
      : [
          `${UC_DENETIM_IST}?bank=${encodeURIComponent(bank)}`,
          `period=${encodeURIComponent(denetimPenceresi)}`,
          secimDegeri(denetimEylemi) ? `action=${encodeURIComponent(secimDegeri(denetimEylemi))}` : "",
        ]
          .filter(Boolean)
          .join("&");
  const denetimIst = useApi<HafizaZarfi<IstatistikGovdesi>>(denetimIstYolu);

  const llmYolu =
    bank === null || sekme !== "model"
      ? null
      : [
          `${UC_LLM}?bank=${encodeURIComponent(bank)}`,
          `limit=${SAYFA_BOYU}`,
          `offset=${llmAtlanan}`,
          secimDegeri(llmDurumu) ? `status=${encodeURIComponent(secimDegeri(llmDurumu))}` : "",
          secimDegeri(llmIslemi) ? `operation=${encodeURIComponent(secimDegeri(llmIslemi))}` : "",
        ]
          .filter(Boolean)
          .join("&");
  const llm = useApi<HafizaZarfi<SayfaliGovde<ModelCagrisi>>>(llmYolu);

  const llmIstYolu =
    bank === null || sekme !== "model"
      ? null
      : [
          `${UC_LLM_IST}?bank=${encodeURIComponent(bank)}`,
          `period=${encodeURIComponent(llmPenceresi)}`,
          secimDegeri(llmIslemi) ? `operation=${encodeURIComponent(secimDegeri(llmIslemi))}` : "",
        ]
          .filter(Boolean)
          .join("&");
  const llmIst = useApi<HafizaZarfi<IstatistikGovdesi>>(llmIstYolu);

  if (bank === null) {
    return (
      <BolumKart kimlik="hafiza-yapilandirma" baslik={kayit.baslik} soru={kayit.soru} ikon={kayit.ikon}>
        <Olculemedi
          neden="Okunacak banka seçilemedi"
          teknik="banka listesi boş ya da okunamadı — yukarıdaki seçici gerekçeyi taşıyor"
        />
      </BolumKart>
    );
  }

  /* Açık denetim kaydının iki iç gövdesi BİR KEZ çözülür (inceleme M-10). */
  const istek = acikDenetim === null ? null : sozluk(acikDenetim.request);
  const yanit = acikDenetim === null ? null : sozluk(acikDenetim.response);

  return (
    <BolumKart kimlik="hafiza-yapilandirma" baslik={kayit.baslik} soru={kayit.soru} ikon={kayit.ikon}>
      <Bolme
        baslik="Sayaçlar"
        aciklama="Bu iki kutu panonun toplu okumasından gelir — bu görünüm için yeni bir çağrı açılmaz. Pencere üst servisin varsayılanıdır (7 gün): alt sekmelerdeki şeritler 7 günde AYNI sayıyı, 1/30 güne çevrilince başka bir sayıyı gösterir."
      >
        <SayacKutulari toplu={toplu} bank={bank} />
      </Bolme>

      <Tabs value={sekme} onValueChange={setSekme} className="flex flex-col gap-3">
        <TabsList className="flex-wrap">
          <TabsTrigger value="genel">Genel</TabsTrigger>
          <TabsTrigger value="savunma">Bellek savunması</TabsTrigger>
          <TabsTrigger value="ayarlar">Ayarlar</TabsTrigger>
          <TabsTrigger value="webhook">Webhook</TabsTrigger>
          <TabsTrigger value="denetim">Denetim kaydı</TabsTrigger>
          <TabsTrigger value="model">Model çağrıları</TabsTrigger>
        </TabsList>

        <TabsContent value="genel">
          <Bolme
            baslik="Arka planda koşan işler"
            aciklama="Hangi iş bekliyor, hangisi işleniyor, hangisi düştü."
          >
            <Islemler bank={bank} />
          </Bolme>
        </TabsContent>

        <TabsContent value="savunma">
          <Bolme
            baslik="Bellek savunması"
            aciklama="Hassas veri yakalandığında ne yapılacağı. Kaynağı ayrı bir uç değil, yapılandırmanın kendisidir."
          >
            <UcKapisi durum={yapilandirma} yol={UC_YAPILANDIRMA}>
              {(z) => (
                <ZarfKapisi zarf={z} ne="Yapılandırma">
                  {(g) => <Savunma govde={g} />}
                </ZarfKapisi>
              )}
            </UcKapisi>
          </Bolme>
        </TabsContent>

        <TabsContent value="ayarlar">
          <UcKapisi durum={yapilandirma} yol={UC_YAPILANDIRMA}>
            {(z) => (
              <ZarfKapisi zarf={z} ne="Yapılandırma">
                {(g) => <Ayarlar govde={g} />}
              </ZarfKapisi>
            )}
          </UcKapisi>
        </TabsContent>

        <TabsContent value="webhook">
          <Bolme baslik="Webhook" aciklama="Üst yüzeyin bu alt sekmesi bu panoda okunmuyor.">
            {/* "ÖLÇÜLEMEDİ" DEĞİL, "OKUNMUYOR": burada bir ölçüm denenip düşmüyor.
                Webhook uçlarının vekilde karşılığı yok — sekmeyi silmek yeteneğin
                yokluğunu, boş bırakmak da "hiç webhook yok"u söylerdi. */}
            <p className="text-muted-foreground text-sm">
              Bu sekmenin okuması panoda YOK: webhook listesi vekilin yirmi iki ucunun arasında
              değil. Bu bir ölçüm sonucu değil, bir kapsam sınırı — "bu bankada webhook yok"
              demiyoruz, "bu pano webhook'ları okumuyor" diyoruz.
            </p>
            <Faz2Grup>
              <Faz2Dugme ne="yeni bir webhook tanımlar">Webhook ekle</Faz2Dugme>
            </Faz2Grup>
          </Bolme>
        </TabsContent>

        <TabsContent value="denetim">
          <div className="flex flex-col gap-4">
            <Bolme
              baslik="İstek hacmi"
              aciklama="Seçilen pencerede kaç denetim kaydı doğdu. 7 günde yukarıdaki kutuyla AYNI sayıyı verir (aynı uç, aynı pencere); 1 ya da 30 güne çevrildiğinde ayrışması beklenir."
              aksiyon={<PencereDugmeleri pencere={denetimPenceresi} setPencere={setDenetimPenceresi} />}
            >
              <UcKapisi durum={denetimIst} yol={UC_DENETIM_IST}>
                {(z) => (
                  <ZarfKapisi zarf={z} ne="Denetim sayaçları">
                    {(g) => <KovaSeridi kovalar={g.buckets} deger={kovaToplami} ne="Denetim kaydı" />}
                  </ZarfKapisi>
                )}
              </UcKapisi>
            </Bolme>

            <Bolme baslik="Kayıtlar" aciklama="Bankaya ne işlendi, hangi yoldan geldi, ne kadar sürdü.">
              <div className="flex flex-wrap items-end gap-3">
                <Secim
                  etiket="Eylem"
                  deger={denetimEylemi}
                  setDeger={setDenetimEylemi}
                  secenekler={DENETIM_EYLEMLERI}
                  genislik="w-56"
                />
                <Secim
                  etiket="Taşıyıcı"
                  deger={tasiyici}
                  setDeger={setTasiyici}
                  secenekler={DENETIM_TASIYICILARI}
                  genislik="w-40"
                />
              </div>

              <UcKapisi durum={denetim} yol={UC_DENETIM}>
                {(z) => (
                  <ZarfKapisi zarf={z} ne="Denetim kaydı">
                    {(g) => {
                      if (!Array.isArray(g.items)) {
                        return (
                          <Olculemedi
                            neden="Denetim listesi tanınmayan bir biçimde geldi"
                            teknik="beklenen dizi, gelen başka bir tip — şema sürüklenmiş olabilir"
                          />
                        );
                      }
                      if (g.items.length === 0) {
                        return (
                          <p className="text-muted-foreground text-sm">
                            {denetimAtlanan === 0
                              ? "Bu süzgeçle okundu ve denetim kaydı YOK. Bu ölçülmüş bir boşluktur — denetim kaydı bu bankada kapalı da olabilir."
                              : "Bu sayfada kayıt YOK — liste daha önceki bir sayfada bitmiş."}
                          </p>
                        );
                      }
                      return (
                        <div className="overflow-x-auto">
                          <Table className="min-w-[44rem]">
                            <TableHeader className="bg-muted/50">
                              <TableRow>
                                <TableHead className="w-48">Zaman</TableHead>
                                <TableHead>Eylem</TableHead>
                                <TableHead className="w-28">Taşıyıcı</TableHead>
                                <TableHead className="w-28 text-right">Süre</TableHead>
                              </TableRow>
                            </TableHeader>
                            <TableBody>
                              {g.items.map((d, i) => {
                                const kimlik = metin(d.id);
                                const sure = araSuresi(d.started_at, d.ended_at);
                                return (
                                  <TableRow
                                    key={kimlik ?? `denetim-${denetimAtlanan + i}`}
                                    className="cursor-pointer hover:bg-muted/50"
                                    onClick={() => setAcikDenetim(d)}
                                  >
                                    <TableCell className="text-muted-foreground text-xs tabular-nums">
                                      {damga(d.started_at) ?? (
                                        <Olculemedi
                                          neden="Başlangıç zamanı gelmedi"
                                          teknik="başlangıç damgası gelmedi ya da çözülemedi"
                                          kisa
                                        />
                                      )}
                                    </TableCell>
                                    <TableCell className="font-medium text-sm">
                                      {metin(d.action) ?? (
                                        <Olculemedi
                                          neden="Eylem gelmedi"
                                          teknik="eylem alanı yok ya da dizge değil"
                                          kisa
                                        />
                                      )}
                                    </TableCell>
                                    <TableCell>
                                      {metin(d.transport) === null ? (
                                        <Olculemedi
                                          neden="Taşıyıcı gelmedi"
                                          teknik="taşıyıcı alanı yok ya da dizge değil"
                                          kisa
                                        />
                                      ) : (
                                        <Badge variant="outline" className="font-normal text-[11px]">
                                          {metin(d.transport)}
                                        </Badge>
                                      )}
                                    </TableCell>
                                    <TableCell className="text-right text-muted-foreground text-xs tabular-nums">
                                      {sure ?? (
                                        <Olculemedi
                                          neden="Süre hesaplanamadı"
                                          teknik="başlangıç ya da bitiş damgası gelmedi — iş hâlâ koşuyor olabilir"
                                          kisa
                                        />
                                      )}
                                    </TableCell>
                                  </TableRow>
                                );
                              })}
                            </TableBody>
                          </Table>
                        </div>
                      );
                    }}
                  </ZarfKapisi>
                )}
              </UcKapisi>

              <UcKapisi durum={denetim} yol={UC_DENETIM} iskelet={<></>}>
                {(z) =>
                  z.neden || !z.govde ? null : (
                    <Sayfalama
                      atlanan={denetimAtlanan}
                      gelen={(z.govde.items ?? []).length}
                      sayfaBoyu={SAYFA_BOYU}
                      toplam={sayi(z.govde.total)}
                      setAtlanan={setDenetimAtlanan}
                    />
                  )
                }
              </UcKapisi>

              {/* YAZAN DÜĞME YOKLUĞU BURADA DA YAZILI (inceleme M-9): aynı kural
                  Recall ve Varlıklar'da uygulanıyordu, burada atlanmıştı. */}
              <Badge variant="outline" className="w-fit font-normal text-[11px] text-muted-foreground">
                denetim kaydında yazan bir düğme yok — üst yüzeyde de yok, hepsi okuma
              </Badge>
            </Bolme>
          </div>
        </TabsContent>

        <TabsContent value="model">
          <div className="flex flex-col gap-4">
            <Bolme
              baslik="Çağrı hacmi"
              aciklama="Seçilen pencerede kaç model çağrısı yapıldı. 7 günde yukarıdaki kutuyla AYNI sayıyı verir; jeton kırılımı üst yüzeyde ayrı bir grafiktir, burada kova başına toplam çizilir."
              aksiyon={<PencereDugmeleri pencere={llmPenceresi} setPencere={setLlmPenceresi} />}
            >
              <UcKapisi durum={llmIst} yol={UC_LLM_IST}>
                {(z) => (
                  <ZarfKapisi zarf={z} ne="Model çağrısı sayaçları">
                    {(g) => (
                      <div className="flex flex-col gap-4">
                        <KovaSeridi kovalar={g.buckets} deger={kovaToplami} ne="Model çağrısı" />
                        <KovaSeridi
                          kovalar={g.buckets}
                          deger={(k) => sayi(k.tokens?.total)}
                          ne="Jeton"
                          birim=" jeton"
                        />
                      </div>
                    )}
                  </ZarfKapisi>
                )}
              </UcKapisi>
            </Bolme>

            <Bolme baslik="Çağrılar" aciklama="Hangi işlem, hangi model, ne kadar jeton, ne kadar sürdü.">
              <div className="flex flex-wrap items-end gap-3">
                <Secim etiket="Durum" deger={llmDurumu} setDeger={setLlmDurumu} secenekler={LLM_DURUMLARI} genislik="w-40" />
                <Secim etiket="İşlem" deger={llmIslemi} setDeger={setLlmIslemi} secenekler={LLM_ISLEMLERI} genislik="w-56" />
              </div>

              <UcKapisi durum={llm} yol={UC_LLM}>
                {(z) => (
                  <ZarfKapisi zarf={z} ne="Model çağrıları">
                    {(g) => {
                      if (!Array.isArray(g.items)) {
                        return (
                          <Olculemedi
                            neden="Çağrı listesi tanınmayan bir biçimde geldi"
                            teknik="beklenen dizi, gelen başka bir tip — şema sürüklenmiş olabilir"
                          />
                        );
                      }
                      if (g.items.length === 0) {
                        return (
                          <p className="text-muted-foreground text-sm">
                            {llmAtlanan === 0
                              ? "Bu süzgeçle okundu ve model çağrısı kaydı YOK. Bu ölçülmüş bir boşluktur — çağrı izleme bu bankada kapalı da olabilir."
                              : "Bu sayfada kayıt YOK — liste daha önceki bir sayfada bitmiş."}
                          </p>
                        );
                      }
                      return (
                        <div className="overflow-x-auto">
                          <Table className="min-w-[52rem]">
                            <TableHeader className="bg-muted/50">
                              <TableRow>
                                <TableHead className="w-48">Zaman</TableHead>
                                <TableHead className="w-40">İşlem</TableHead>
                                <TableHead>Kapsam</TableHead>
                                <TableHead className="w-24">Durum</TableHead>
                                <TableHead className="w-28 text-right">Jeton</TableHead>
                                <TableHead className="w-24 text-right">Süre</TableHead>
                              </TableRow>
                            </TableHeader>
                            <TableBody>
                              {g.items.map((c, i) => {
                                const kimlik = metin(c.id);
                                const jeton = sayi(c.total_tokens);
                                const sure = msMetni(c.duration_ms);
                                const durum = metin(c.status);
                                return (
                                  <TableRow key={kimlik ?? `cagri-${llmAtlanan + i}`}>
                                    <TableCell className="text-muted-foreground text-xs tabular-nums">
                                      {damga(c.started_at) ?? (
                                        <Olculemedi
                                          neden="Başlangıç zamanı gelmedi"
                                          teknik="başlangıç damgası gelmedi ya da çözülemedi"
                                          kisa
                                        />
                                      )}
                                    </TableCell>
                                    <TableCell className="font-medium text-sm">
                                      {metin(c.operation) ?? (
                                        <Olculemedi
                                          neden="İşlem gelmedi"
                                          teknik="işlem alanı yok ya da dizge değil"
                                          kisa
                                        />
                                      )}
                                    </TableCell>
                                    <TableCell className="max-w-0">
                                      {/* BOŞ HÜCRE SEBEBİNİ SÖYLER (inceleme M-5):
                                          burası tablonun kendi sütunu, ikincil bir
                                          satır değil — çıplak boşluk "değer yok" ile
                                          "alan gelmedi"yi ayırt ettirmezdi. */}
                                      <span className="block truncate font-mono text-[11px]">
                                        {metin(c.scope) ?? (
                                          <Olculemedi neden="Kapsam gelmedi" teknik="kapsam alanı yok ya da dizge değil" kisa />
                                        )}
                                      </span>
                                      <span className="block truncate text-[11px] text-muted-foreground">
                                        {metin(c.model) ?? (
                                          <Olculemedi neden="Model adı gelmedi" teknik="model alanı yok ya da dizge değil" kisa />
                                        )}
                                      </span>
                                    </TableCell>
                                    <TableCell>
                                      {durum === null ? (
                                        <Olculemedi
                                          neden="Durum gelmedi"
                                          teknik="durum alanı yok ya da dizge değil"
                                          kisa
                                        />
                                      ) : (
                                        <Badge
                                          variant={durum === "error" ? "destructive" : "outline"}
                                          className={cn("font-normal text-[11px]")}
                                        >
                                          {durum}
                                        </Badge>
                                      )}
                                    </TableCell>
                                    <TableCell className="text-right text-xs tabular-nums">
                                      {jeton === null ? (
                                        <Olculemedi
                                          neden="Jeton gelmedi"
                                          teknik="jeton sayacı gelmedi ya da sayı değil"
                                          kisa
                                        />
                                      ) : (
                                        jeton.toLocaleString("tr-TR")
                                      )}
                                    </TableCell>
                                    <TableCell className="text-right text-muted-foreground text-xs tabular-nums">
                                      {sure ?? (
                                        <Olculemedi
                                          neden="Süre gelmedi"
                                          teknik="süre alanı gelmedi ya da sayı değil"
                                          kisa
                                        />
                                      )}
                                    </TableCell>
                                  </TableRow>
                                );
                              })}
                            </TableBody>
                          </Table>
                        </div>
                      );
                    }}
                  </ZarfKapisi>
                )}
              </UcKapisi>

              <UcKapisi durum={llm} yol={UC_LLM} iskelet={<></>}>
                {(z) =>
                  z.neden || !z.govde ? null : (
                    <Sayfalama
                      atlanan={llmAtlanan}
                      gelen={(z.govde.items ?? []).length}
                      sayfaBoyu={SAYFA_BOYU}
                      toplam={sayi(z.govde.total)}
                      setAtlanan={setLlmAtlanan}
                    />
                  )
                }
              </UcKapisi>

              <Badge variant="outline" className="w-fit font-normal text-[11px] text-muted-foreground">
                model çağrılarında yazan bir düğme yok — üst yüzeyde de yok, hepsi okuma
              </Badge>
            </Bolme>
          </div>
        </TabsContent>
      </Tabs>

      <Sheet
        open={acikDenetim !== null}
        onOpenChange={(a) => {
          if (!a) setAcikDenetim(null);
        }}
      >
        <SheetContent side="right" className="w-full sm:max-w-2xl">
          <SheetHeader className="pr-10">
            <SheetTitle className="text-base leading-6">
              {acikDenetim === null ? "Denetim kaydı" : (metin(acikDenetim.action) ?? "Denetim kaydı")}
            </SheetTitle>
            <SheetDescription className="break-all font-mono text-[11px]">
              {acikDenetim === null ? "kayıt seçilmedi" : (metin(acikDenetim.id) ?? "kimlik gelmedi")}
            </SheetDescription>
          </SheetHeader>
          <div className="flex min-h-0 flex-1 flex-col gap-4 overflow-y-auto px-4 pb-6">
            {acikDenetim === null ? (
              <p className="text-muted-foreground text-sm">Tablodaki bir satıra tıkla.</p>
            ) : (
              <>
                {/* SÖZLÜK BİR KEZ ÇÖZÜLÜR (inceleme M-10): aynı çağrıyı koşulda ve
                    gövdede tekrarlamak, ikincisini `as` ile daraltmayı zorunlu
                    kılıyordu — cast, tipin söylediğinden fazlasını iddia etmektir. */}
                <div>
                  <Satir etiket="Başlangıç">
                    {damga(acikDenetim.started_at) ?? (
                      <Olculemedi
                        neden="Başlangıç zamanı gelmedi"
                        teknik="başlangıç damgası gelmedi ya da çözülemedi"
                        kisa
                      />
                    )}
                  </Satir>
                  <Satir etiket="Bitiş">
                    {damga(acikDenetim.ended_at) ?? (
                      <Olculemedi
                        neden="Bitiş zamanı gelmedi"
                        teknik="bitiş damgası gelmedi ya da çözülemedi — iş hâlâ koşuyor olabilir"
                        kisa
                      />
                    )}
                  </Satir>
                  <Satir etiket="Süre">
                    {araSuresi(acikDenetim.started_at, acikDenetim.ended_at) ?? (
                      <Olculemedi
                        neden="Süre hesaplanamadı"
                        teknik="iki damgadan biri gelmedi ya da çözülemedi"
                        kisa
                      />
                    )}
                  </Satir>
                </div>
                <Bolme baslik="İstek" aciklama="Üst servise ne gitti — şekli sözleşmede yok, ham basılır.">
                  {istek === null ? (
                    <Olculemedi
                      neden="İstek gövdesi gelmedi"
                      teknik="istek alanı yok ya da sözlük değil — denetim kaydı gövdesiz tutulmuş olabilir"
                    />
                  ) : (
                    <HamSatirlar govde={istek} />
                  )}
                </Bolme>
                <Bolme baslik="Yanıt" aciklama="Üst servis ne döndü.">
                  {yanit === null ? (
                    <Olculemedi
                      neden="Yanıt gövdesi gelmedi"
                      teknik="yanıt alanı yok ya da sözlük değil"
                    />
                  ) : (
                    <HamSatirlar govde={yanit} />
                  )}
                </Bolme>
                <Bolme baslik="Kaydın tamamı">
                  <HamSatirlar govde={acikDenetim} atla={["request", "response"]} />
                </Bolme>
              </>
            )}
          </div>
        </SheetContent>
      </Sheet>
    </BolumKart>
  );
}
