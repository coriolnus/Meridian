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
   bloğunda ne tek-varlık ucu ne de listede varlık süzgeci var). Bu yüzden graf
   TIKLANABİLİR DEĞİL: bir düğüme tıklamanın açacağı ekran bu panoda mevcut
   olmadığı için imleç de değişmiyor. "Tıkladım, bir şey olmadı" ile "bu pano onu
   okumuyor" iki ayrı cümledir; ikincisi hem aşağıda yazılı, hem de imlecin
   kendisi tarafından söyleniyor.

   ---------------------------------------------------------------------------
   ÇEMBER YERLEŞİMİ EMEKLİ (operatör görsel turu, 2026-09-02)
   ---------------------------------------------------------------------------
   Bu görünümün ilk grafı kütüphanesiz bir SVG çemberdi: düğümler ağırlığa göre
   sıralı, yerleşim anlamsız, yakınlaştırma yok. Operatör üst yüzeyle kıyasladı
   ("orijinaldeki bayağı başarılı, bizimkinin alakası yok") ve karar verildi:
   varlık grafı da bellek grafıyla AYNI takımyıldız görseline geçer. Kazanç:
   yakınlaştırma/kaydırma, komşu vurgusu, üst yüzeyin kendi ısı ve boyut
   kuralları. Bedel ve ödendiği yer: seçili düğümün bağ LİSTESİ kayboldu —
   yerine üzerine gelince açılan künye geldi; bağların tek tek okunması gereken
   bir soru için liste kipi hâlâ duruyor.
   ============================================================================ */
import { useCallback, useEffect, useMemo, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

import type { Bolum } from "../../alanlar";
import { useApi } from "../../veri";
import { BolumKart, Kapi as UcKapisi, Olculemedi } from "../sistem/parcalar";
import { KimliksizRozeti, Takimyildizi, TaninmayanBicim, varlikGrafiniCoz } from "./takimyildizi";

import { Bolme, KirpmaZinciri, Sayfalama, Secim, ZarfKapisi, damga, damgaMs, metin, sayi } from "./parcalar";
import type { HafizaZarfi, SayfaliGovde, TakimyildiziDugumu, VarlikGrafi, VarlikKaydi } from "./uctipleri";

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

/* ---------------------------------------------------------------------------
   BAĞ HARİTASI — takımyıldız, üst yüzeyin varlık görünümünün KENDİ ayarlarıyla
   ----------------------------------------------------------------------------
   Üç kural üst yüzeyin `entities-view` dosyasından ölçüldü ve birebir taşındı:
     · NOKTA BOYUTU birlikte geçiş ağırlıklarının toplamından, karekök ölçekli
       (3 piksel yalnız kalan isim → 14 piksel merkez isim). Karekök uzun kuyruğu
       düzleştirir: tek bir merkez ötekileri görünmez kılmaz.
     · RENK TAZELİK: düğümün EN SON birlikte geçişi. Boyut "ne kadar", renk "ne
       zaman" der — iki eksen birbirine karışmaz.
     · ETİKETLER SIK: varlık adları kısadır; kayıt metinlerine göre ayarlanmış
       seyrek yerleşim burada etiketlerin çoğunu gizlerdi.
   Tazelik damgası HİÇ gelmezse ısı ekseni ÇİZİLMEZ (üst yüzey de öyle yapıyor):
   bir ölçek çizip uçlarını yazamamak, rengi ölçüm gibi gösterirdi.
   --------------------------------------------------------------------------- */
function BagHaritasi({ govde }: { readonly govde: VarlikGrafi }) {
  const cozum = useMemo(() => varlikGrafiniCoz(govde, damgaMs), [govde]);

  const enAgir = useMemo(() => {
    let m = 1;
    for (const w of cozum.agirliklar.values()) if (w > m) m = w;
    return m;
  }, [cozum]);

  /* ISI ARALIĞI ÇÖZÜCÜDEN GELİR, DÜĞÜMLERDEN TÜRETİLMEZ (inceleme M-3).
     İlk yazım aralığı düğüm başına EN SON damgaların en küçüğü/en büyüğü olarak
     kuruyordu; üst yüzey ise BÜTÜN kenar damgalarından kuruyor. Fark sessiz ama
     gerçek: bizim alt ucumuz her zaman üst yüzeyinkine eşit ya da ondan YENİ
     çıkardı, yani efsanenin sol ucundaki tarih ve renk dağılımı ayrışırdı. */
  const tazelikAraligi = cozum.tazelikAraligi;

  const boyutFn = useCallback(
    (d: TakimyildiziDugumu) => 3 + Math.sqrt((cozum.agirliklar.get(d.kimlik) ?? 0) / enAgir) * 11,
    [cozum, enAgir],
  );
  const isiFn = useCallback(
    (d: TakimyildiziDugumu) => {
      if (tazelikAraligi === null) return 0.5;
      const t = cozum.tazelikler.get(d.kimlik);
      if (t === undefined) return 0;
      return (t - tazelikAraligi.alt) / (tazelikAraligi.ust - tazelikAraligi.alt);
    },
    [cozum, tazelikAraligi],
  );

  const gun = (ms: number) => new Date(ms).toLocaleDateString("tr-TR");

  if (!Array.isArray(govde.nodes)) return <TaninmayanBicim />;

  return (
    <div className="flex flex-col gap-3">
      {/* KIRPMA ZİNCİRİ — ÜÇ SAYI, ÜÇÜ DE ADIYLA. Bu uç SUNUCUDA kırpılıyor ve
          yalnız dönen diziyi sayan bir ekran eksik bir grafiği TAM gösterirdi. */}
      <div className="flex flex-col gap-1">
        <KirpmaZinciri
          ne="isim"
          cizilen={cozum.veri.dugumler.length}
          vekil={cozum.vekilDugum}
          tavan={cozum.tavan}
          toplam={cozum.toplamDugum}
        />
        <KirpmaZinciri
          ne="bağ"
          cizilen={cozum.veri.baglar.length}
          vekil={cozum.vekilBag}
          tavan={cozum.tavan}
          toplam={cozum.toplamBag}
        />
      </div>

      <KimliksizRozeti sayi={cozum.kimliksiz} />

      <Takimyildizi
        veri={cozum.veri}
        yukseklik={560}
        boyutFn={boyutFn}
        isiFn={tazelikAraligi === null ? undefined : isiFn}
        isiEtiketi={tazelikAraligi === null ? undefined : "tazelik · son birlikte geçiş"}
        isiUclari={tazelikAraligi === null ? undefined : [gun(tazelikAraligi.alt), gun(tazelikAraligi.ust)]}
        boyutEtiketi="birlikte geçiş"
        sikEtiket
        aciklama={`Varlık bağ haritası: ${cozum.veri.dugumler.length} isim, ${cozum.veri.baglar.length} bağ`}
      />

      {tazelikAraligi === null ? (
        <p className="text-muted-foreground text-[11px]">
          Isı ekseni çizilmedi: bağların son birlikte geçiş zamanı bu okumada gelmedi ya da hepsi
          aynı ana düşüyor. Renk bu durumda bağ sayısını gösterir.
        </p>
      ) : null}
    </div>
  );
}

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
          aciklama="Hangi isim hangisiyle birlikte geçiyor. Nokta büyüklüğü birlikte geçiş ağırlığını, rengi son geçişin tazeliğini gösterir; sınırlar haritanın üstünde sayıyla yazılı."
          aksiyon={<Secim etiket="Bağ eşiği" deger={esik} setDeger={setEsik} secenekler={ESIK_SECENEKLERI} genislik="w-36" />}
        >
          <UcKapisi durum={graf} yol={UC_GRAF}>
            {(z) => (
              <ZarfKapisi zarf={z} ne="Bağ haritası">
                {(g) => <BagHaritasi govde={g} />}
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
        var). Haritadaki düğümler bu yüzden TIKLANABİLİR DEĞİL — üzerlerine gelmek bağlarını
        vurgular ve künyelerini açar. Bu bir arıza değil, ölçülmüş bir kapsam sınırı.
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
