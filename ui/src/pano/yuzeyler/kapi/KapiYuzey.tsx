"use client";

/* ============================================================================
   KAPI YÜZEYİ — APISIX'in pano görünümü (`/api/gateway`), SALT-OKUNUR
   ----------------------------------------------------------------------------
   TARAYICI 9180/9091'E ASLA GİTMEZ. Admin API loopback'te dinler ve `X-API-KEY`
   ister; metrik ucu da yalnız loopback'tedir. Tarayıcıyı oraya bağlamanın iki yolu
   olurdu — portları dışarı açmak ya da admin anahtarını panoya indirmek — ve ikisi
   de altyapının tamamını bir XSS'in menziline sokardı. Bu sayfanın okuduğu TEK yer
   `api.py::api_gateway` vekilidir: sunucu okur, süzer, anahtarsız bir gövde döner.

   YAZMA YOLU YOK VE OLMAYACAK. Konfigürasyonun tek kaynağı `deploy/apisix/routes.yaml`
   + GitOps (`ops/apisix_uygula.py`). Panodan yapılan bir değişiklik ilk `--uygula`
   koşumunda sessizce geri alınırdı — yani "düzenle" düğmesi bir vaat değil, bir tuzak
   olurdu. Sayfa bu yüzden kaynağın ADRESİNİ söyler, kendisini sunmaz.

   DÖRT BÖLÜM, TEK UÇ. `SistemSagligiYuzey` dört ayrı uç açar çünkü dört ayrı ölçüm
   penceresi var; burada dört bölüm de AYNI gövdenin dört alanıdır. İkinci bir istek
   açmak aynı anı iki kez sormak olurdu ve iki cevap ayrışabilirdi.

   NABIZ 30 SN (`NABIZ_MS * 2`) VE GEREKÇESİ ÖLÇÜLÜ: (a) bu yüzeyin gösterdiği şey
   GitOps hızında değişir — rota tanımı saniyede bir kaymaz, dakikalar/günler mertebesinde
   kayar; (b) ucun ÖNBELLEĞİ YOK (`/api/infra`nın 8 sn'lik zarfı burada uygulanmadı), yani
   her yoklama iki loopback GET demek. 15 sn'de sormak bu iki maliyeti ikiye katlar ve
   karşılığında hiçbir yeni bilgi getirmezdi.

   İSİM ÇAKIŞMASI BİLEREK ÇÖZÜLDÜ: `sistem/parcalar`ın `Kapi` bileşeni VERİ kapısıdır
   (yükleniyor / oturum düştü / okunamadı / veri), bu sayfanın konusu olan APISIX
   "kapı"sıyla hiçbir ilgisi yoktur. Aynı dosyada iki anlamda "Kapi" okumak, bakımı
   yapan kişiye sessizce yanlış şeyi düşündürürdü — bu yüzden `UcKapisi` diye geliyor.
   ============================================================================ */
import { useEffect } from "react";
import { ChartColumn, DoorOpen, HeartPulse, Milestone, Waypoints } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { cn } from "@/lib/utils";

import { YUZEYLER } from "../../alanlar";
import { useRota } from "../../rota";
import { NABIZ_MS, useApi, type Durum } from "../../veri";
import { BolumKart, Deger, Kapi as UcKapisi, Olculemedi, OkRozet, Satir, zamanMetni } from "../sistem/parcalar";
import type { KapiGovdesi, KapiRotasi, KapiZincirHalkasi } from "./uctipleri";

const UC = "/api/gateway";

/* ---------------------------------------------------------------------------
   FAZ SÖZLÜĞÜ — ucun HÜKMÜNÜ insan diline çevirir, hükmü KURMAZ
   `Bilesenler.tsx::SINIF` ile aynı kalıp ve aynı gerekçe: hangi fazın canlı olduğu
   `api.py::_kapi_fazlar`ta plugin imzasından TÜRETİLİR; burada yalnız etiketi var.
   Bu bir ikinci kaynak DEĞİLDİR — tabloda olmayan bir anahtar geldiğinde ekran onu
   HAM basar ve "?" ile işaretler (v280 disiplini: tanınmayan değer sessizce nötr
   okunamaz). Yani beşinci bir faz doğduğu gün görünür olur, kaybolmaz.
   --------------------------------------------------------------------------- */
const FAZ_ETIKET: Readonly<Record<string, string>> = {
  faz1_llm: "Faz 1 · LLM egress",
  faz2_fmp: "Faz 2 · FMP kotası",
  faz3_ingress: "Faz 3 · Pano ingress",
  faz4_filo: "Faz 4 · Bot filosu",
};

/* ÜÇ HÂL, ÜÇ AYRI GÖRÜNÜM — ve "ölçülemedi" ASLA yeşil değildir.
   `bekliyor` bir ARIZA DEĞİL, bir plandır: kırmızı yapmak operatörü olmayan bir işe
   koşturur. `olculemedi` de kırmızı değildir ama nötr de değildir — sağlık İDDİA
   EDİLMİYOR, o yüzden kendi sessiz kutusunda durur ve nedenini yanında taşır. */
type FazTonu = "canli" | "bekliyor" | "olculemedi" | "taninmiyor";

const FAZ_HAL: Readonly<Record<string, { etiket: string; ton: FazTonu }>> = {
  canli: { etiket: "canlı", ton: "canli" },
  bekliyor: { etiket: "bekliyor", ton: "bekliyor" },
  olculemedi: { etiket: "ölçülemedi", ton: "olculemedi" },
};

const FAZ_TON_SINIFI: Readonly<Record<FazTonu, string>> = {
  canli: "bg-basari-t text-basari",
  bekliyor: "text-muted-foreground",
  olculemedi: "text-muted-foreground",
  taninmiyor: "bg-uyari-t text-uyari",
};

const FAZ_NOKTA_SINIFI: Readonly<Record<FazTonu, string>> = {
  canli: "bg-basari",
  bekliyor: "bg-muted-foreground/40",
  olculemedi: "bg-muted-foreground/60",
  taninmiyor: "bg-uyari",
};

function FazRozeti({ hal }: { readonly hal: string }) {
  const bilinen = FAZ_HAL[hal];
  const ton: FazTonu = bilinen?.ton ?? "taninmiyor";
  return (
    <Badge
      variant="outline"
      className={cn("gap-1.5", FAZ_TON_SINIFI[ton])}
      title={
        bilinen
          ? undefined
          : `uç tanınmayan bir faz hâli döndürdü: ${hal} — sessizce "bekliyor" saymak bir ölçüm iddiası olurdu`
      }
    >
      <span className={cn("size-1.5 rounded-full", FAZ_NOKTA_SINIFI[ton])} />
      {bilinen ? bilinen.etiket : `${hal} ?`}
    </Badge>
  );
}

/* ---------------------------------------------------------------------------
   BÖLÜM 1 — SAĞLIK ŞERİDİ
   İKİ BACAK AYRI ROZET, çünkü uçta da ayrı ölçülüyorlar: admin anahtarı olmayan bir
   makinede prometheus yine açık olabilir. Tek rozete indirmek, bir arızayı iki
   körlüğe çevirirdi. `neden` GÖRÜNÜR — "ölçülemedi" ile "sağlıklı" aynı kutuya girmez.
   --------------------------------------------------------------------------- */
function Saglik({ durum }: { readonly durum: Durum<KapiGovdesi> }) {
  return (
    <BolumKart
      kimlik="kapi-saglik"
      baslik="Kapının sağlığı"
      soru="APISIX'in yönetim ve metrik yüzeyleri okunabiliyor mu?"
      ikon={HeartPulse}
    >
      <UcKapisi durum={durum} yol={UC}>
        {(g) => {
          const s = g.saglik;
          const k = g.kaynak;
          return (
            <>
              {s === undefined ? (
                <Olculemedi neden="Kapının sağlığı bildirilmedi" teknik={`${UC} \`saglik\` bloğunu döndürmedi`} />
              ) : (
                <>
                  <div className="flex flex-wrap items-center gap-2">
                    <OkRozet
                      ok={s.admin_api}
                      iyi="Admin API okunuyor"
                      kotu="Admin API okunamadı"
                      neden="Admin API bacağı ölçülmedi"
                      teknik="`saglik.admin_api` alanı gelmedi"
                    />
                    <OkRozet
                      ok={s.prometheus}
                      iyi="Prometheus okunuyor"
                      kotu="Prometheus okunamadı"
                      neden="Prometheus bacağı ölçülmedi"
                      teknik="`saglik.prometheus` alanı gelmedi"
                    />
                  </div>
                  {s.neden ? (
                    <p className="text-destructive text-sm">{s.neden}</p>
                  ) : (
                    <p className="text-muted-foreground text-sm">
                      İki bacak da okundu — aşağıdaki rota, metrik ve faz satırları ÖLÇÜLMÜŞ değerlerdir.
                    </p>
                  )}
                </>
              )}

              {/* KAYNAK KÜNYESİ GÖVDEDEN OKUNUR, EKRANA SABİT YAZILMAZ: port ya da yol
                  değiştiğinde pano eski adresi göstermeye devam ederdi (tek-kaynak yasası). */}
              <div className="grid gap-x-6 gap-y-1 sm:grid-cols-2">
                <div>
                  <Satir etiket="Admin API adresi">
                    {k?.admin_url ? (
                      <code className="text-xs">{k.admin_url}</code>
                    ) : (
                      <Olculemedi neden="Adres bildirilmedi" teknik="`kaynak.admin_url` gelmedi" kisa />
                    )}
                  </Satir>
                  <Satir etiket="Prometheus adresi">
                    {k?.prometheus_url ? (
                      <code className="text-xs">{k.prometheus_url}</code>
                    ) : (
                      <Olculemedi neden="Adres bildirilmedi" teknik="`kaynak.prometheus_url` gelmedi" kisa />
                    )}
                  </Satir>
                </div>
                <div>
                  <Satir etiket="Vekil zaman aşımı">
                    <Deger
                      deger={k?.zaman_asimi_s}
                      birim=" sn"
                      basamak={1}
                      neden="Zaman aşımı bildirilmedi"
                      teknik="`kaynak.zaman_asimi_s` gelmedi"
                    />
                  </Satir>
                  <Satir etiket="Ölçüm anı">
                    {zamanMetni(g.hesaplama_ts) ?? (
                      <Olculemedi neden="Ölçüm damgası gelmedi" teknik="`hesaplama_ts` yok" kisa />
                    )}
                  </Satir>
                </div>
              </div>
            </>
          );
        }}
      </UcKapisi>
    </BolumKart>
  );
}

/* ---------------------------------------------------------------------------
   BÖLÜM 2 — LLM ROTA KARTLARI
   ZİNCİR SIRASI SUNUCUDA KURULDU (`api.py::_kapi_rota_cevir`, öncelik desc) ve BURADA
   YENİDEN SIRALANMAZ. Aynı sıralama kuralını iki yerde tutmak, ikisinin sessizce
   ayrışması demektir (tek-kaynak yasası) — dizinin sırası zaten denenme sırasıdır.

   BOŞ LİSTE İLE ÖLÇÜLEMEDİ AYRI: `rotalar_neden` doluysa admin API okunamadı ve boş
   liste bir ÖLÇÜM DEĞİL. Boş kart "kapıda rota yok" derdi ve bu bir yalan olurdu.
   --------------------------------------------------------------------------- */
function ZincirHalkasi({ halka, sira }: { readonly halka: KapiZincirHalkasi; readonly sira: number }) {
  return (
    <li className="flex flex-col gap-1 rounded-md border p-2.5">
      <div className="flex flex-wrap items-center gap-2">
        <Badge variant="secondary" className="tabular-nums">{sira}.</Badge>
        <span className="font-medium text-sm">
          {halka.ad ?? <Olculemedi neden="Halkanın adı yok" teknik="`instances[].name` gelmedi" kisa />}
        </span>
        <Badge variant="outline" className="tabular-nums">
          öncelik{" "}
          {halka.oncelik === null || halka.oncelik === undefined ? (
            <span className="ml-1 italic">yazılmamış</span>
          ) : (
            <span className="ml-1">{halka.oncelik}</span>
          )}
        </Badge>
      </div>
      <div className="text-muted-foreground text-xs">
        {halka.model ? (
          <code>{halka.model}</code>
        ) : (
          <Olculemedi neden="Model adı yok" teknik="`instances[].options.model` gelmedi" kisa />
        )}
      </div>
      {/* AUTH REFERANSI SIR DEĞİLDİR, SIRRA REFERANSTIR — ve tam olarak bu yüzden
          gösterilir: "hangi env okunuyor" sorusu panodan cevaplanabilmeli. Uç
          `$env://` ile başlamayan bir değeri zaten göstermez, ama gizlediğini SÖYLER
          ve o beyan burada aynen görünür (sessiz gizleme, körlüktür). */}
      <div className="text-xs">
        {halka.auth_referansi === null || halka.auth_referansi === undefined ? (
          <Olculemedi
            neden="Auth başlığı tanımlı değil"
            teknik="`auth.header.Authorization` bu halkada yok — upstream anahtarsız çağrılıyor olabilir"
            kisa
          />
        ) : halka.auth_referansi.toLowerCase().startsWith("$env://") ? (
          <span className="text-muted-foreground">
            anahtar: <code>{halka.auth_referansi}</code> <span className="italic">(referans — değer etcd'de yok)</span>
          </span>
        ) : (
          <span className="text-uyari">{halka.auth_referansi}</span>
        )}
      </div>
    </li>
  );
}

function RotaKarti({ rota }: { readonly rota: KapiRotasi }) {
  const zincir = rota.zincir ?? [];
  const tetikler = rota.fallback_tetikleri ?? [];
  const temizlenen = rota.temizlenen_basliklar ?? [];
  return (
    <div className="flex flex-col gap-3 rounded-lg border p-4">
      <div className="flex flex-wrap items-baseline gap-2">
        <span className="font-semibold text-sm">
          {rota.id ?? <Olculemedi neden="Rota kimliği yok" teknik="`id` alanı gelmedi" kisa />}
        </span>
        {rota.uri ? (
          <code className="text-muted-foreground text-xs">{rota.uri}</code>
        ) : (
          <Olculemedi neden="Rota yolu yok" teknik="`uri` alanı gelmedi" kisa />
        )}
      </div>

      {/* ZİNCİR */}
      {rota.zincir === undefined ? (
        <Olculemedi neden="Zincir bildirilmedi" teknik="rota `zincir` alanını taşımıyor" />
      ) : zincir.length === 0 ? (
        <p className="text-muted-foreground text-xs">
          Bu rotada LLM zinciri YOK — ölçüldü. `ai-proxy-multi` eklentisi tanımlı değil; rota başka bir
          iş yapıyor olabilir (bu bir arıza beyanı değil).
        </p>
      ) : (
        <>
          <p className="text-muted-foreground text-xs">
            Sıra DENENME sırasıdır (öncelik azalan; sunucuda kuruldu). İlk halka düşerse aşağıdaki tetiklerle
            bir sonrakine geçilir.
          </p>
          <ol className="flex flex-col gap-2">
            {zincir.map((h, i) => (
              <ZincirHalkasi key={h.ad ?? `halka-${i}`} halka={h} sira={i + 1} />
            ))}
          </ol>
        </>
      )}

      <div className="grid gap-x-6 gap-y-1 sm:grid-cols-2">
        <div>
          <Satir etiket="Fallback tetikleri">
            {rota.fallback_tetikleri === undefined ? (
              <Olculemedi neden="Tetikler bildirilmedi" teknik="`fallback_tetikleri` alanı gelmedi" kisa />
            ) : tetikler.length === 0 ? (
              <span className="text-muted-foreground text-xs italic">
                tanımlı değil — zincir ilk denemede biter
              </span>
            ) : (
              <span className="flex flex-wrap justify-end gap-1">
                {tetikler.map((t) => (
                  <Badge key={t} variant="outline" className="font-mono text-[11px]">
                    {t}
                  </Badge>
                ))}
              </span>
            )}
          </Satir>
        </div>
        <div>
          <Satir etiket="Temizlenen başlıklar">
            {rota.temizlenen_basliklar === undefined ? (
              <Olculemedi neden="Başlık temizliği bildirilmedi" teknik="`temizlenen_basliklar` alanı gelmedi" kisa />
            ) : temizlenen.length === 0 ? (
              /* BOŞ LİSTE BURADA İYİ HABER DEĞİLDİR: istemciden gelen `Authorization`
                 upstream'e GEÇER demektir. Sessiz bir "—" bunu gizlerdi. */
              <span className="text-uyari text-xs">
                hiçbiri — istemci başlıkları upstream'e GEÇER
              </span>
            ) : (
              <span className="flex flex-wrap justify-end gap-1">
                {temizlenen.map((b) => (
                  <Badge key={b} variant="outline" className="font-mono text-[11px]">
                    {b}
                  </Badge>
                ))}
              </span>
            )}
          </Satir>
        </div>
      </div>
    </div>
  );
}

function Rotalar({ durum }: { readonly durum: Durum<KapiGovdesi> }) {
  return (
    <BolumKart
      kimlik="kapi-rotalar"
      baslik="LLM rotaları"
      soru="Hangi model önce deneniyor, düşerse nereye geçiliyor?"
      ikon={Waypoints}
    >
      <UcKapisi durum={durum} yol={UC}>
        {(g) => {
          const rotalar = g.rotalar ?? [];
          const repoYolu = g.kaynak?.rota_kaynagi_repo;
          return (
            <>
              {g.rotalar === undefined ? (
                <Olculemedi neden="Rotalar bildirilmedi" teknik={`${UC} \`rotalar\` alanını döndürmedi`} />
              ) : g.rotalar_neden ? (
                /* ÖLÇÜLEMEDİ — boş liste burada bir ölçüm SONUCU değil, bir ölçüm YOKLUĞU. */
                <Olculemedi neden="Rotalar okunamadı" teknik={g.rotalar_neden} />
              ) : rotalar.length === 0 ? (
                <p className="text-muted-foreground text-sm">
                  Admin API OKUNDU ve kapıda tanımlı rota YOK. Bu bir arıza değil, ölçülmüş bir boşluk —
                  yukarıdaki sağlık şeridi "Admin API okunuyor" diyorsa sayı gerçektir.
                </p>
              ) : (
                <div className="flex flex-col gap-3">
                  {rotalar.map((r, i) => (
                    <RotaKarti key={r.id ?? `rota-${i}`} rota={r} />
                  ))}
                </div>
              )}

              {/* KAYNAĞIN ADRESİ — BAĞ DEĞİL, ADRES. Pano repo dosyası SUNMAZ (`api.py`
                  `StaticFiles` montajını bilerek reddediyor) ve olmayan bir bağ vermek
                  tıklandığında 404 veren bir vaat olurdu. Yol GÖVDEDEN okunur: burada sabit
                  yazsaydık kaynak taşındığı gün pano eski yeri göstermeye devam ederdi. */}
              <p className="text-muted-foreground text-xs">
                {repoYolu ? (
                  <>
                    Bu yüzey SALT-OKUNURDUR. Rotaların tek kaynağı depoda{" "}
                    <code className="text-foreground">{repoYolu}</code> — değişiklik oradan ve GitOps
                    koşumuyla (`ops/apisix_uygula.py`) yapılır. Panodan yapılan bir düzenleme ilk uygulama
                    koşumunda geri alınırdı.
                  </>
                ) : (
                  <Olculemedi
                    neden="Konfigürasyonun repo yolu bildirilmedi"
                    teknik="`kaynak.rota_kaynagi_repo` gelmedi — kaynağın adresi burada UYDURULMAZ"
                  />
                )}
              </p>
            </>
          );
        }}
      </UcKapisi>
    </BolumKart>
  );
}

/* ---------------------------------------------------------------------------
   BÖLÜM 3 — METRİKLER
   İKİ BOŞ DURUM AYRI ÇİZİLİR ve ayrımı bu bölümün OMURGASIDIR:
     · `kaynak_ok === false` → prometheus HİÇ okunamadı. Tablo çizilmez, neden yazılır.
     · `kaynak_ok === true` + boş `rota_basina` → OKUNDU, sayaç yok. Bu ölçülmüş bir
       sıfırdır ("kapıdan istek geçmemiş") ve birinciyle aynı görünmemeli.
   `atlanan_satir` da üç hâllidir: `null` ölçülemedi · `0` bozuk satır yok · `n` bozuk.
   `null`ı `0` diye çizmek "hiç bozulma yok" demek olurdu — ölçülmemiş bir temizlik beyanı.
   --------------------------------------------------------------------------- */
function AtlananSatir({ n }: { readonly n: number | null | undefined }) {
  if (n === undefined) {
    return <Olculemedi neden="Bozuk satır sayacı bildirilmedi" teknik="`metrikler.atlanan_satir` alanı gelmedi" kisa />;
  }
  if (n === null) {
    return (
      <Olculemedi
        neden="Ölçülemedi — prometheus metni hiç okunmadı"
        teknik="`atlanan_satir: null`; burada 0 yazmak 'bozuk satır yok' yalanı olurdu"
        kisa
      />
    );
  }
  if (n === 0) {
    return <span className="text-muted-foreground text-xs">okundu · bozuk satır yok</span>;
  }
  return (
    <span
      className="text-uyari text-xs tabular-nums"
      title="`apisix_http_status` diye başlayıp rota/kod/sayı üçlüsünü veremeyen satır. İlgisiz metrikler bu sayaca GİRMEZ."
    >
      {n} satır ayrıştırılamadı
    </span>
  );
}

function Metrikler({ durum }: { readonly durum: Durum<KapiGovdesi> }) {
  return (
    <BolumKart
      kimlik="kapi-metrikler"
      baslik="Kapıdan geçen trafik"
      soru="Hangi rotadan kaç istek geçti, hangi durum koduyla döndü?"
      ikon={ChartColumn}
    >
      <UcKapisi durum={durum} yol={UC}>
        {(g) => {
          const m = g.metrikler;
          if (m === undefined) {
            return <Olculemedi neden="Metrikler bildirilmedi" teknik={`${UC} \`metrikler\` bloğunu döndürmedi`} />;
          }
          const rotaBasina = m.rota_basina ?? {};
          // SIRALAMA BİR GÖRÜNÜM KARARIDIR, BİR HÜKÜM DEĞİL: en çok trafik alan rota üste
          // gelir ki gözle taranabilsin. Eşitlikte ad — sıra her yoklamada aynı kalsın,
          // yoksa satırlar okurken yer değiştirir.
          const satirlar = Object.entries(rotaBasina).sort(
            (a, b) => (b[1].istek_n ?? 0) - (a[1].istek_n ?? 0) || a[0].localeCompare(b[0]),
          );
          return (
            <>
              {m.kaynak_ok === false ? (
                /* BİRİNCİ BOŞ DURUM: kaynağa hiç ulaşılamadı. */
                <Olculemedi
                  neden="Prometheus okunamadı — trafik ÖLÇÜLMEDİ"
                  teknik={m.neden ?? "`metrikler.neden` boş geldi; kaynak yine de okunamadı olarak işaretli"}
                />
              ) : m.kaynak_ok === undefined ? (
                <Olculemedi neden="Metrik kaynağının durumu bildirilmedi" teknik="`metrikler.kaynak_ok` alanı gelmedi" />
              ) : satirlar.length === 0 ? (
                /* İKİNCİ BOŞ DURUM — BİRİNCİYLE AYNI DEĞİL: kaynak OKUNDU. */
                <p className="text-muted-foreground text-sm">
                  Prometheus OKUNDU, ama hiç <code>apisix_http_status</code> sayacı yok: kapıdan bu ayağa kalkıştan
                  beri istek geçmemiş (ya da APISIX yeniden başlatılıp sayaçlar sıfırlanmış). Bu ölçülmüş bir
                  sıfırdır — "ölçemedim" ile aynı şey değildir.
                </p>
              ) : (
                <div className="overflow-x-auto">
                  <Table className="min-w-[38rem]">
                    <TableHeader className="bg-muted/50">
                      <TableRow>
                        <TableHead>Rota</TableHead>
                        <TableHead className="text-right">İstek</TableHead>
                        <TableHead>Durum kodu kırılımı</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {satirlar.map(([rota, kutu]) => {
                        const kirilim = Object.entries(kutu.durum_kirilimi ?? {}).sort((a, b) =>
                          a[0].localeCompare(b[0], undefined, { numeric: true }),
                        );
                        return (
                          <TableRow key={rota}>
                            <TableCell className="font-medium">
                              <code className="text-xs">{rota}</code>
                            </TableCell>
                            <TableCell className="text-right tabular-nums">
                              <Deger
                                deger={kutu.istek_n}
                                neden="İstek sayacı gelmedi"
                                teknik="rota kutusu `istek_n` taşımıyor"
                              />
                            </TableCell>
                            <TableCell>
                              {kutu.durum_kirilimi === undefined ? (
                                <Olculemedi neden="Kırılım gelmedi" teknik="`durum_kirilimi` alanı yok" kisa />
                              ) : kirilim.length === 0 ? (
                                <span className="text-muted-foreground text-xs italic">kırılım boş</span>
                              ) : (
                                <span className="flex flex-wrap gap-1">
                                  {kirilim.map(([kod, n]) => (
                                    <Badge
                                      key={kod}
                                      variant="outline"
                                      className={cn(
                                        "font-mono text-[11px] tabular-nums",
                                        kod.startsWith("2") && "bg-basari-t text-basari",
                                        (kod.startsWith("4") || kod.startsWith("5")) &&
                                          "bg-uyari-t text-uyari",
                                      )}
                                    >
                                      {kod} · {n}
                                    </Badge>
                                  ))}
                                </span>
                              )}
                            </TableCell>
                          </TableRow>
                        );
                      })}
                    </TableBody>
                  </Table>
                </div>
              )}

              <Satir etiket="Ayrıştırılamayan metrik satırı">
                <AtlananSatir n={m.atlanan_satir} />
              </Satir>
            </>
          );
        }}
      </UcKapisi>
    </BolumKart>
  );
}

/* ---------------------------------------------------------------------------
   BÖLÜM 4 — FAZLAR
   ROZETLER SABİT METİN DEĞİL: her faz `api.py::_kapi_fazlar`ta bir plugin imzasından
   TÜRETİLİR. Sabit yazılsaydı Faz 2 indiği gün pano "bekliyor" demeye devam eder ve
   kimse fark etmezdi (F9 sınıfı ayrışma).

   KAPSAM BEYANI EKRANA BASILIR — süs değil, BEDEL YASASININ karşılığı: türetim yalnız
   `/routes` okur, yani rota DIŞINDA kurulan bir faz burada gecikmeli görünür. Kazancı
   (tek kaynak, otomatik güncellik) gösterip bedeli göstermemek, körlüğü sessiz bırakırdı.
   --------------------------------------------------------------------------- */
function Fazlar({ durum }: { readonly durum: Durum<KapiGovdesi> }) {
  return (
    <BolumKart
      kimlik="kapi-fazlar"
      baslik="Kurulum fazları"
      soru="Kapının hangi fazı canlı, hangisi hâlâ bekliyor?"
      ikon={Milestone}
    >
      <UcKapisi durum={durum} yol={UC}>
        {(g) => {
          const fazlar = g.fazlar;
          const kanit = g.fazlar_kanit ?? {};
          return (
            <>
              {fazlar === undefined ? (
                <Olculemedi neden="Fazlar bildirilmedi" teknik={`${UC} \`fazlar\` bloğunu döndürmedi`} />
              ) : Object.keys(fazlar).length === 0 ? (
                <Olculemedi neden="Faz listesi boş geldi" teknik="`fazlar` sözlüğünde hiç anahtar yok" />
              ) : (
                <div className="flex flex-col gap-2">
                  {/* SIRA UCUN VERDİĞİ SIRADIR (faz 1→4) — burada yeniden sıralamak, aynı
                      kuralı iki yerde tutmak olurdu. */}
                  {Object.entries(fazlar).map(([alan, hal]) => (
                    <div key={alan} className="flex flex-col gap-1 border-b py-2 last:border-b-0">
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <span className="font-medium text-sm">
                          {FAZ_ETIKET[alan] ?? (
                            <span title="uç, sözlükte olmayan bir faz döndürdü — ham basılıyor ki sessizce kaybolmasın">
                              {alan} ?
                            </span>
                          )}
                        </span>
                        <FazRozeti hal={hal} />
                      </div>
                      <span className="text-muted-foreground text-xs">
                        {kanit[alan] ?? (
                          <Olculemedi
                            neden="Bu fazın kanıtı bildirilmedi"
                            teknik={`\`fazlar_kanit.${alan}\` gelmedi — rozet neye dayandığını söyleyemiyor`}
                            kisa
                          />
                        )}
                      </span>
                    </div>
                  ))}
                </div>
              )}

              {/* KAPSAM BEYANI — KONTROLÖR HÜKMÜ: bu satır ekranda DURMAK ZORUNDA. */}
              {g.fazlar_kapsam_neden ? (
                <p className="rounded-md border border-dashed p-3 text-muted-foreground text-xs">
                  <span className="font-medium">Bu ölçümün kapsamı: </span>
                  {g.fazlar_kapsam_neden}
                </p>
              ) : (
                <Olculemedi
                  neden="Faz ölçümünün kapsamı bildirilmedi"
                  teknik="`fazlar_kapsam_neden` gelmedi — rozetler neyi göremediğini söyleyemiyor (bedel yasası)"
                />
              )}
            </>
          );
        }}
      </UcKapisi>
    </BolumKart>
  );
}

/* --------------------------------------------------------------------------- */

export function KapiYuzey() {
  const { bolum } = useRota();
  // BAŞLIK KAYITTAN OKUNUR (SistemSagligiYuzey deseni): `alanlar.ts` bu yüzeyin
  // başlığını ve cevapladığı SORUYU tek yerde tutuyor. İkinci kez yazsaydık kayıt
  // değiştiğinde ekran sessizce eski soruyu sormaya devam ederdi.
  const y = YUZEYLER.gateway;
  const kapi = useApi<KapiGovdesi>(UC, NABIZ_MS * 2);

  useEffect(() => {
    if (!bolum) {
      window.scrollTo({ top: 0, behavior: "instant" });
      return;
    }
    document.getElementById(`bolum-${bolum}`)?.scrollIntoView({ behavior: "smooth", block: "start" });
  }, [bolum]);

  const g = kapi.veri;
  const rotaN = g?.rotalar?.length;
  const canliFaz = g?.fazlar ? Object.values(g.fazlar).filter((h) => h === "canli").length : undefined;
  const fazN = g?.fazlar ? Object.keys(g.fazlar).length : undefined;
  // ADMİN OKUNAMADIĞINDA `_kapi_fazlar` DÖRT ANAHTARI DA "olculemedi" DÖNDÜRÜR (global
  // uygulama — karma hâl yok): bu durumda `canliFaz` sessizce 0'a düşer ve rozet "0/N faz
  // canlı" derdi, yani ÖLÇÜLEMEYEN bir şeyi ÖLÇÜLMÜŞ sıfır gibi basardı (uydurma yasağı).
  // Bekçi HEPSİ "olculemedi" mi diye sorar — `rotalar` çipinin `!g?.rotalar_neden`
  // bekçisiyle aynı disiplin.
  const fazDegerleri = g?.fazlar ? Object.values(g.fazlar) : undefined;
  const fazlarOlculemedi = !!fazDegerleri && fazDegerleri.length > 0 && fazDegerleri.every((h) => h === "olculemedi");

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0">
          <h1 className="flex items-center gap-2 font-semibold text-2xl tracking-tight">
            <DoorOpen className="size-5 shrink-0 text-muted-foreground" aria-hidden />
            {y.baslik}
          </h1>
          <p className="mt-1 text-muted-foreground text-sm">{y.soru}</p>
        </div>
        {/* ROZET ŞERİDİ YALNIZ ÖLÇÜLENİ TAŞIR (SistemSagligiYuzey kuralı): alanı gövdede
            OLMAYAN rozet HİÇ çizilmez — boş bir rozet "0" diye okunurdu. `rotalar_neden`
            doluyken rota sayısı da basılmaz: o sayı bir ölçüm değil. Aynı disiplin faz
            çipinde de geçerli: `fazlarOlculemedi` iken "N/4 faz canlı" da basılmaz — admin
            okunamadığında dört fazın hepsi "olculemedi" döner ve bu sayı bir ölçüm değildir. */}
        <div className="flex flex-wrap items-center gap-2">
          {rotaN !== undefined && !g?.rotalar_neden ? (
            <Badge variant="outline" className="tabular-nums">{rotaN} rota</Badge>
          ) : null}
          {canliFaz !== undefined && fazN !== undefined && !fazlarOlculemedi ? (
            <Badge variant="outline" className="tabular-nums">
              {canliFaz}/{fazN} faz canlı
            </Badge>
          ) : null}
          {g?.saglik?.admin_api === false && g?.saglik?.prometheus === false ? (
            <Badge variant="destructive">kapı okunamadı</Badge>
          ) : g?.saglik?.admin_api === false || g?.saglik?.prometheus === false ? (
            <Badge variant="destructive">kapı kısmen okunamadı</Badge>
          ) : null}
        </div>
      </div>

      <Saglik durum={kapi} />
      <Rotalar durum={kapi} />
      <Metrikler durum={kapi} />
      <Fazlar durum={kapi} />
    </div>
  );
}
