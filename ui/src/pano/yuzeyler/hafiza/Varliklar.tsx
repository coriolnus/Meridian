"use client";

/* ============================================================================
   HAFIZA · VARLIKLAR — üst yüzeyin `entities` görünümünün karşılığı
   ----------------------------------------------------------------------------
   İKİ KİP OKUNDU, UYDURULMADI: üst yüzey (`entities-view.tsx`) bu görünümü İKİ
   kiple çiziyor — "ilişkiler" (bağ haritası) ve "liste" (tablo) — ve açılışta
   İLİŞKİLER kipinde duruyor. Tablonun dört sütunu da oradan: isim · anılma
   sayısı · ilk görülme · son görülme. Alan adlarının TAMAMI ayrıca A1'de
   ölçüldü (`entities?limit=2` → `canonical_name, mention_count, first_seen,
   last_seen, id, metadata`), yani bu görünümün zemini sağlam.

   GRAF YALNIZ İLİŞKİLER KİPİNDE OKUNUR ve bu bir bedel kararıdır: graf ucu
   bankadaki bütün birlikte-geçişleri tarar; liste kipinde duran bir operatör
   için onu önden çekmek, okunmayan bir yükü her açılışta taşımak olurdu. Üst
   yüzey de aynı ayrımı yapıyor (kip değişince yüklüyor).

   ---------------------------------------------------------------------------
   BU GÖRÜNÜMDE OLMAYAN ŞEY VE ADI — "eksik" ile "yok" ayrı yazılır
   ---------------------------------------------------------------------------
   Üst yüzeyde bir isme tıklamak İKİ okuma açıyor: tek-varlık ucu (`/entities/
   {id}`) ve o ismin geçtiği kayıtların ters araması (`memories/list` üzerinde
   varlık süzgeci). VEKİLDE İKİSİNİN DE KARŞILIĞI YOK (`api.py`nin hafıza
   bloğunda ne tek-varlık ucu ne de listede varlık süzgeci var). Bu yüzden bir
   isme tıklamak burada kaydı DEĞİL, o ismin BAĞLARINI açar — ve eksik olanın
   adı ekranda yazılı durur. "Tıkladım, bir şey olmadı" ile "bu pano onu
   okumuyor" iki ayrı cümledir.
   ============================================================================ */
import { useEffect, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

import type { Bolum } from "../../alanlar";
import { useApi } from "../../veri";
import { BolumKart, Kapi as UcKapisi, Olculemedi } from "../sistem/parcalar";
import { Graf } from "./graf";

import { Bolme, Sayfalama, Secim, ZarfKapisi, damga, metin, sayi } from "./parcalar";
import type { HafizaZarfi, SayfaliGovde, VarlikGrafi, VarlikKaydi } from "./uctipleri";

const UC_VARLIKLAR = "/api/hindsight/varliklar";
const UC_GRAF = "/api/hindsight/varlik-graf";

/* Sayfa boyu bir GÖRÜNÜM kararıdır; sunucu tavanı (`HAFIZA_LISTE_TAVANI`) burada
   TEKRAR YAZILMAZ — iki kopya sessizce ayrışır. Üst yüzeyin kendi sayfası 50. */
const SAYFA_BOYU = 50;

/* GRAF TAVANI: üst yüzey `limit: 2000, min_count: 1` ile çağırıyor. Bizim
   vekilimiz limiti KENDİ tavanına (200) kırpıyor (`api.py::_hafiza_sayi` +
   `HAFIZA_LISTE_TAVANI`), yani 2000 yazmak sessizce 200 olurdu ve ekran
   istediğinden başka bir şey aldığını bilmezdi. 200 YAZILI ve sunucununkiyle
   AYNI sayı olduğu için ayrışma da görünür olur (istek düşerse gerekçeye döner). */
const GRAF_TAVANI = 200;

/** En az kaç kez birlikte geçmiş bağlar çizilsin. Sunucu 1 ile 2^31 arasına
 *  kırpıyor; buradaki liste bir SEÇENEK kümesidir, sunucu sözlüğü değil —
 *  o yüzden "geçersiz değer" hâli yok, yalnız daha dar/geniş bir graf var. */
const ESIK_SECENEKLERI = [
  { deger: "1", etiket: "en az 1 kez" },
  { deger: "2", etiket: "en az 2 kez" },
  { deger: "3", etiket: "en az 3 kez" },
  { deger: "5", etiket: "en az 5 kez" },
  { deger: "10", etiket: "en az 10 kez" },
] as const;

type Kip = "iliskiler" | "liste";

export function Varliklar({ bank, kayit }: { readonly bank: string | null; readonly kayit: Bolum }) {
  /* AÇILIŞ KİPİ ÜST YÜZEYDEN: orada da varsayılan "ilişkiler". Liste ile açsaydık
     birebirleştirmenin ölçülebilir yarısını kaybederdik. */
  const [kip, setKip] = useState<Kip>("iliskiler");
  const [atlanan, setAtlanan] = useState(0);
  const [esik, setEsik] = useState("1");

  useEffect(() => {
    setAtlanan(0);
  }, [bank]);

  const listeYolu =
    bank === null || kip !== "liste"
      ? null
      : `${UC_VARLIKLAR}?bank=${encodeURIComponent(bank)}&limit=${SAYFA_BOYU}&offset=${atlanan}`;
  const grafYolu =
    bank === null || kip !== "iliskiler"
      ? null
      : `${UC_GRAF}?bank=${encodeURIComponent(bank)}&limit=${GRAF_TAVANI}&min_count=${encodeURIComponent(esik)}`;

  const liste = useApi<HafizaZarfi<SayfaliGovde<VarlikKaydi>>>(listeYolu);
  const graf = useApi<HafizaZarfi<VarlikGrafi>>(grafYolu);

  if (bank === null) {
    return (
      <BolumKart kimlik="hafiza-varliklar" baslik={kayit.baslik} soru={kayit.soru} ikon={kayit.ikon}>
        <Olculemedi
          neden="Okunacak banka seçilemedi"
          teknik="banka listesi boş ya da okunamadı — yukarıdaki seçici gerekçeyi taşıyor"
        />
      </BolumKart>
    );
  }

  return (
    <BolumKart
      kimlik="hafiza-varliklar"
      baslik={kayit.baslik}
      soru={kayit.soru}
      ikon={kayit.ikon}
      aksiyon={
        <div className="flex items-center gap-1 rounded-lg bg-muted p-1">
          <Button
            type="button"
            size="sm"
            variant={kip === "iliskiler" ? "secondary" : "ghost"}
            className="h-7 px-2 text-xs"
            aria-pressed={kip === "iliskiler"}
            onClick={() => setKip("iliskiler")}
          >
            İlişkiler
          </Button>
          <Button
            type="button"
            size="sm"
            variant={kip === "liste" ? "secondary" : "ghost"}
            className="h-7 px-2 text-xs"
            aria-pressed={kip === "liste"}
            onClick={() => setKip("liste")}
          >
            Liste
          </Button>
        </div>
      }
    >
      {kip === "iliskiler" ? (
        <Bolme
          baslik="Bağ haritası"
          aciklama="Hangi isim hangisiyle birlikte geçiyor. Çizim bu panoya özgüdür ve sınırları haritanın altında yazılı."
          aksiyon={<Secim etiket="Bağ eşiği" deger={esik} setDeger={setEsik} secenekler={ESIK_SECENEKLERI} genislik="w-36" />}
        >
          <UcKapisi durum={graf} yol={UC_GRAF}>
            {(z) => (
              <ZarfKapisi zarf={z} ne="Bağ haritası">
                {(g) => <Graf govde={g} />}
              </ZarfKapisi>
            )}
          </UcKapisi>
        </Bolme>
      ) : (
        <Bolme
          baslik="İsim listesi"
          aciklama="Kayıtlarda geçen isimler: kaç kez anıldı, ilk ve son ne zaman görüldü."
        >
          <UcKapisi durum={liste} yol={UC_VARLIKLAR}>
            {(z) => (
              <ZarfKapisi zarf={z} ne="Varlık listesi">
                {(g) => {
                  if (!Array.isArray(g.items)) {
                    return (
                      <Olculemedi
                        neden="Varlık listesi tanınmayan bir biçimde geldi"
                        teknik="beklenen dizi, gelen başka bir tip — şema sürüklenmiş olabilir"
                      />
                    );
                  }
                  if (g.items.length === 0) {
                    return (
                      <p className="text-muted-foreground text-sm">
                        {atlanan === 0
                          ? "Bu banka okundu ve kayıtlı isim YOK. Bu ölçülmüş bir boşluktur."
                          : "Bu sayfada isim YOK — liste daha önceki bir sayfada bitmiş."}
                      </p>
                    );
                  }
                  return (
                    <div className="overflow-x-auto">
                      <Table className="min-w-[40rem]">
                        <TableHeader className="bg-muted/50">
                          <TableRow>
                            <TableHead>İsim</TableHead>
                            <TableHead className="w-28 text-right">Anılma</TableHead>
                            <TableHead className="w-44">İlk görülme</TableHead>
                            <TableHead className="w-44">Son görülme</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {g.items.map((v, i) => {
                            const ad = metin(v.canonical_name);
                            const kimlik = metin(v.id);
                            const n = sayi(v.mention_count);
                            const ilk = damga(v.first_seen);
                            const son = damga(v.last_seen);
                            return (
                              <TableRow key={kimlik ?? `varlik-${atlanan + i}`}>
                                <TableCell className="max-w-0">
                                  {ad === null ? (
                                    <Olculemedi
                                      neden="İsim gelmedi"
                                      teknik="satırda kanonik ad alanı yok ya da dizge değil"
                                      kisa
                                    />
                                  ) : (
                                    <span className="block truncate font-medium text-sm" title={ad}>
                                      {ad}
                                    </span>
                                  )}
                                  <span className="mt-0.5 block truncate font-mono text-[11px] text-muted-foreground">
                                    {kimlik ?? (
                                      <Olculemedi
                                        neden="kimlik gelmedi"
                                        teknik="satırda kimlik alanı yok ya da dizge değil"
                                        kisa
                                      />
                                    )}
                                  </span>
                                </TableCell>
                                <TableCell className="text-right tabular-nums">
                                  {n === null ? (
                                    <Olculemedi
                                      neden="Anılma sayısı gelmedi"
                                      teknik="anılma sayacı gelmedi ya da sayı değil"
                                      kisa
                                    />
                                  ) : (
                                    n.toLocaleString("tr-TR")
                                  )}
                                </TableCell>
                                <TableCell className="text-muted-foreground text-xs tabular-nums">
                                  {ilk ?? (
                                    <Olculemedi
                                      neden="İlk görülme gelmedi"
                                      teknik="ilk görülme damgası gelmedi ya da çözülemedi"
                                      kisa
                                    />
                                  )}
                                </TableCell>
                                <TableCell className="text-muted-foreground text-xs tabular-nums">
                                  {son ?? (
                                    <Olculemedi
                                      neden="Son görülme gelmedi"
                                      teknik="son görülme damgası gelmedi ya da çözülemedi"
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

          {/* SAYFALAMA KAPININ İÇİNDE (Görev 2 incelemesi, bulgu M-4): dışarıda
              dururken istek düştüğünde "Okunamadı" uyarısının altında ölçülmemiş
              bir sayfa konumu çiziliyordu. */}
          <UcKapisi durum={liste} yol={UC_VARLIKLAR} iskelet={<></>}>
            {(z) =>
              z.neden || !z.govde ? null : (
                <Sayfalama
                  atlanan={atlanan}
                  gelen={(z.govde.items ?? []).length}
                  sayfaBoyu={SAYFA_BOYU}
                  toplam={sayi(z.govde.total)}
                  setAtlanan={setAtlanan}
                />
              )
            }
          </UcKapisi>
        </Bolme>
      )}

      <p className="rounded-md border border-dashed p-3 text-muted-foreground text-xs">
        <span className="font-medium">Bu görünümün kapsamı: </span>
        üst yüzeyde bir isme tıklamak o ismin künyesini ve geçtiği kayıtları açıyor; ikisinin de
        panoda karşılığı YOK (ne tek-varlık okuması ne de kayıt listesinde isim süzgeci vekilde
        var). Burada bir isme tıklamak yalnız BAĞLARINI vurgular. Bu bir arıza değil, ölçülmüş bir
        kapsam sınırı.
      </p>

      {/* ÜST YÜZEYDE BU GÖRÜNÜMDE YAZAN DÜĞME YOK — ve bunu yazmak gerekiyor:
          boş bir düğme şeridi "unutulmuş" diye okunurdu. */}
      <div className="flex flex-wrap items-center gap-2">
        <Badge variant="outline" className="font-normal text-[11px] text-muted-foreground">
          bu görünümde yazan bir düğme yok — üst yüzeyde de yok, hepsi okuma
        </Badge>
      </div>
    </BolumKart>
  );
}
