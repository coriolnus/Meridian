"use client";

/* ============================================================================
   HAFIZA · BELLEKLER — üst yüzeyin `data` görünümünün karşılığı
   ----------------------------------------------------------------------------
   SÜTUNLAR UYDURULMADI, OKUNDU: üst yüzeyin tablosu (`data-view.tsx`) beş sütun
   çiziyor — kaydın metni (+ bağlamı) · varlıklar · etiketler · gerçekleşme ·
   anılma — ve satıra tıklamak detay panelini açıyor. Buradaki tablo o düzenin
   birebir karşılığıdır.

   İKİ FARK VAR VE İKİSİ DE ÖLÇÜM SONUCU:

   1. ÜST YÜZEY BU TABLOYU GRAF UCUNDAN BESLİYOR, biz LİSTE ucundan. Graf ucu
      bu vekilde bir bellek listesi olarak açılmıyor (kapsam kararı). Sonucu
      görünür: liste gövdesinde `occurred_start` her kayıtta olmayabilir ve o
      zaman hücre "—" değil GEREKÇE taşır.
   2. TÜR SÜZGECİ TEK SEÇİMLİDİR. Üst yüzey türleri çoklu seçtiriyor; bizim
      vekilimiz üst servise TEK bir tür parametresi geçiriyor. Çoklu seçim
      istemciden N ayrı çağrı ve istemcide birleştirme demek olurdu — yani
      sayfalamanın ve toplamın anlamı kaybolurdu. Tek seçim dürüst olandır;
      "hepsi" seçeneği süzgeci hiç göndermez.

   ---------------------------------------------------------------------------
   TARİHÇE — VE NEDEN AYRI BİR BACAK
   ---------------------------------------------------------------------------
   Kaydın gövdesinde `history` diye bir alan VAR ve üst servis onu "artık
   kullanılmıyor, her zaman boş liste" diye belgeliyor. O alanı okuyan bir ekran
   her kayıt için "tarihçe yok" derdi — ölçülmemiş bir boşluğu ölçülmüş gibi
   göstererek. Vekil bu yüzden tarihçeyi AYRI uçtan çekiyor ve bu ekran onu ayrı
   bir gerekçeyle çiziyor: kaydın kendisi okunabilirken tarihçesi okunamayabilir.

   Tarihçenin ŞEKLİ ölçülemedi (üst servisin şeması bu yanıt için boş) — bu
   yüzden gelen gövde anahtarlarıyla ham basılır. Alan adı uydurmak, tam da bu
   dosyanın kapattığı sınıf.

   ARAMA "ENTER"A BASINCA GİDER, HER TUŞA DEĞİL: her harfte bir üst servis
   sorgusu açmak hem gereksiz yük hem de yarım yazılmış bir kelimenin boş
   sonucunu "kayıt yok" diye gösterirdi.
   ============================================================================ */
import { useEffect, useState } from "react";
import { History } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { cn } from "@/lib/utils";

import type { Bolum } from "../../alanlar";
import { useApi, type Durum } from "../../veri";
import { BolumKart, Kapi as UcKapisi, Olculemedi, Satir } from "../sistem/parcalar";
import { Cipler, Faz2Dugme, Faz2Grup, HamSatirlar, Sayfalama, SuzgecSeridi, damga, listeye, metin, sozluk } from "./parcalar";
import type { HafizaDetayi, HafizaKaydi, HafizaListesi } from "./uctipleri";

const UC_LISTE = "/api/hindsight/liste";
const UC_DETAY = "/api/hindsight/detay";

/* SAYFA BOYU BİR GÖRÜNÜM KARARIDIR, BİR ÖLÇÜM DEĞİL — ve bu ayrım yazılı durmalı.
   Sunucu tavanı 200 (`api.py::HAFIZA_LISTE_TAVANI`); burada 50 seçildi çünkü tek
   ekranda taranabilir bir tablo isteniyor. 200 istemek dürüst olurdu ama okunmayan
   150 satır için üç kat gövde taşırdı. Tavanı burada TEKRAR yazmıyoruz: sınırlama
   zaten sunucuda (`api.py::_hafiza_sayi`) ve iki kopya sessizce ayrışır. */
const SAYFA_BOYU = 50;

/* İKİ SÖZLÜK, İKİ AYRI GÜVENCE — VE İLK YAZIM İKİSİNİ TEK CÜMLEYE KOYMUŞTU
   (düzeltme turu 1, inceleme bulgusu M-8). Ölçülen ayrım şudur:

     · DURUM sunucuda BEYAZ LİSTEDEN geçer (`api.py::_HAFIZA_KAYIT_DURUMU`):
       tanımadığı değeri üst servise hiç göndermez. Buraya fazladan bir değer
       yazmak düğmeyi çalışır gösterir, süzgeci sessizce düşürürdü.
     · TÜR sunucuda SÜZÜLMEZ; `fact_type` üst servise HAM geçer. Tanınmayan bir
       değer orada 422 üretir ve gerekçeye döner — sessiz değil, ama "sunucu beni
       korur" diye okumak yanlış olurdu.

   TÜR LİSTESİNİN ÜÇ DEĞERE DARALTILMASI BİR GERİLİMDİR ve yazılı durmalı
   (inceleme bulgusu M-7): bu dosya tür DAĞILIMINI daraltmamayı savunuyor, ama
   burada daraltıyor. Gerekçe farkı: dağılım bir ÖLÇÜMÜ gösterir (yeni bir tür
   doğduğunda kendiliğinden görünmeli), süzgeç ise somut SEÇENEK sunar ve boş bir
   liste seçenek değildir. Bedeli gerçek: yeni bir tür dağılımda görünür ama
   süzgeçte seçilemez — metin araması o boşluğun bugünkü telafisi. */
const TURLER = [
  { deger: "", etiket: "Hepsi" },
  { deger: "world", etiket: "Dünya bilgisi" },
  { deger: "experience", etiket: "Deneyim" },
  { deger: "observation", etiket: "Gözlem" },
] as const;

const DURUMLAR = [
  { deger: "valid", etiket: "Geçerli" },
  { deger: "invalidated", etiket: "Geçersiz kılınmış" },
] as const;

/** Kaydın TÜRÜ — iki ad, iki kaynak (`uctipleri.ts::HafizaKaydi` şerhi). */
function kayitTuru(o: HafizaKaydi): string | null {
  return metin(o.fact_type) ?? metin(o.type);
}

function kayitKimligi(o: HafizaKaydi): string | null {
  return metin(o.id);
}

/* ---------------------------------------------------------------------------
   DETAY PANELİ — üst yüzeyin `memory-detail-panel` bölümlerinin karşılığı
   --------------------------------------------------------------------------- */

function Tarihce({ govde, neden }: { readonly govde: unknown; readonly neden: string | null | undefined }) {
  if (neden) return <Olculemedi neden="Kaydın tarihçesi okunamadı" teknik={neden} />;
  if (govde === undefined) return <Olculemedi neden="Tarihçe bildirilmedi" teknik="uç tarihçe bacağını hiç döndürmedi" />;
  if (govde === null) return <Olculemedi neden="Ölçüm denendi, tarihçe gelmedi" teknik="tarihçe alanı boş döndü ve gerekçe de taşınmadı" />;
  const s = sozluk(govde);
  if (s === null) {
    return <Olculemedi neden="Tarihçe tanınmayan bir biçimde geldi" teknik={`beklenen sözlük, gelen ${Array.isArray(govde) ? "dizi" : typeof govde}`} />;
  }
  return (
    <>
      <p className="text-muted-foreground text-xs">
        Tarihçenin alan şeması üst serviste tanımlı değil — gelen gövde anahtarlarıyla ham basılıyor
      </p>
      <HamSatirlar govde={s} />
    </>
  );
}

function KayitDetayi({ durum }: { readonly durum: Durum<HafizaDetayi> }) {
  return (
    <UcKapisi durum={durum} yol={UC_DETAY}>
      {(d) => {
        if (d.neden) return <Olculemedi neden="Kayıt okunamadı" teknik={d.neden} />;
        if (d.oge === null) {
          /* `oge` boş dönüşü UCUN BİLİNÇLİ TERCİHİ: bulunamayan kayıtta boş sözlük
             dönmek "kayıt var ama içi boş" yalanı olurdu. Ekran o tercihi yazar. */
          return (
            <p className="text-muted-foreground text-sm">
              Bu kimlikle bir kayıt BULUNAMADI. Kayıt silinmiş ya da başka bir bankaya taşınmış
              olabilir — gövde boş değil, kaydın kendisi yok.
            </p>
          );
        }
        if (d.oge === undefined) {
          return <Olculemedi neden="Kayıt gövdesi bildirilmedi" teknik="uç kaydın kendisini döndürmedi" />;
        }
        const o = d.oge;
        const govdeMetni = metin(o.text);
        const gecersiz = o.state === "invalidated";
        const varliklar = listeye(o.entities);
        const kayitEtiketleri = listeye(o.tags);
        /* İKİ AD, İKİ KAYNAK (düzeltme turu 1, inceleme bulgusu I-2). Canlıda ölçülen
           ad `source_memory_ids`tir ve içi KİMLİK dizgeleridir; üst yüzeyin detay
           paneli ise nesne listesi taşıyan `source_memories`i okuyor. İlk yazım
           yalnız ikincisini okuyordu, yani bu bölüm canlıda hiç açılmazdı — üstelik
           sessizce. İkisi de okunuyor; ölçülen ad birincil. */
        const kaynakNesneler = Array.isArray(o.source_memories) ? o.source_memories : [];
        const kaynakKimlikler = listeye(o.source_memory_ids) ?? [];
        return (
          <>
            <div className="flex flex-wrap items-center gap-1.5">
              {kayitTuru(o) ? (
                <Badge variant="outline" className="font-mono text-[11px]">
                  {kayitTuru(o)}
                </Badge>
              ) : null}
              {gecersiz ? <Badge variant="destructive">geçersiz kılınmış</Badge> : null}
              {metin(o.edited_at) ? (
                <Badge variant="secondary" title={damga(o.edited_at) ?? undefined}>
                  düzenlenmiş
                </Badge>
              ) : null}
            </div>

            {govdeMetni === null ? (
              <Olculemedi neden="Kaydın metni okunamadı" teknik="metin alanı gelmedi ya da dizge değil" />
            ) : (
              <p className="whitespace-pre-wrap text-sm leading-6">{govdeMetni}</p>
            )}

            {/* ÜST YÜZEYDE BURADA İKİ YAZMA DÜĞMESİ VAR ve yerlerinde duruyorlar. */}
            <Faz2Grup>
              <Faz2Dugme ne="kaydın metnini düzenler">Düzenle</Faz2Dugme>
              <Faz2Dugme ne={gecersiz ? "geçersiz kılmayı geri alır" : "kaydı geçersiz kılar"}>
                {gecersiz ? "Geri al" : "Geçersiz kıl"}
              </Faz2Dugme>
            </Faz2Grup>

            {gecersiz ? (
              <Satir etiket="Geçersizleme gerekçesi">
                {metin(o.invalidation_reason) ?? (
                  <Olculemedi neden="Gerekçe kaydedilmemiş" teknik="geçersizleme gerekçesi alanı gelmedi" kisa />
                )}
              </Satir>
            ) : null}

            <div>
              <Satir etiket="Bağlam">
                {metin(o.context) ?? <Olculemedi neden="Bağlam kaydedilmemiş" teknik="bağlam alanı gelmedi ya da boş" kisa />}
              </Satir>
              <Satir etiket="Gerçekleşme">
                {damga(o.occurred_start) ?? (
                  <Olculemedi neden="Gerçekleşme zamanı gelmedi" teknik="olayın başlangıç damgası bu kayıtta yok ya da çözülemedi" kisa />
                )}
              </Satir>
              <Satir etiket="Anılma">
                {damga(o.mentioned_at) ?? (
                  <Olculemedi neden="Anılma zamanı gelmedi" teknik="anılma damgası bu kayıtta yok ya da çözülemedi" kisa />
                )}
              </Satir>
              <Satir etiket="Varlıklar">
                <Cipler degerler={varliklar} tavan={8} ne="Varlık alanı" />
              </Satir>
              <Satir etiket="Etiketler">
                <Cipler degerler={kayitEtiketleri} tavan={8} ne="Etiket alanı" />
              </Satir>
            </div>

            {kaynakNesneler.length === 0 && kaynakKimlikler.length > 0 ? (
              <div className="flex flex-col gap-2">
                <h4 className="font-medium text-muted-foreground text-xs uppercase tracking-wide">
                  Kaynak kayıtlar ({kaynakKimlikler.length})
                </h4>
                {/* KİMLİK GELDİ, METİN GELMEDİ — ve ekran bunu söylüyor: kimlikleri
                    metinlerine çevirmek kayıt başına bir çağrı daha demektir ve o
                    maliyet bu turda ölçülmedi. */}
                <Cipler degerler={kaynakKimlikler} tavan={12} ne="Kaynak kayıt kimlikleri" />
                <p className="text-muted-foreground text-[11px]">
                  Bu kayıt yukarıdaki kayıtlardan türetilmiş; metinleri ayrı bir okuma ister ve bu
                  yüzeyde çekilmiyor
                </p>
              </div>
            ) : null}

            {kaynakNesneler.length > 0 ? (
              <div className="flex flex-col gap-2">
                <h4 className="font-medium text-muted-foreground text-xs uppercase tracking-wide">
                  Kaynak kayıtlar ({kaynakNesneler.length})
                </h4>
                {kaynakNesneler.map((k, i) => {
                  const s = sozluk(k);
                  return (
                    <div key={s ? (metin(s.id) ?? `kaynak-${i}`) : `kaynak-${i}`} className="rounded-lg border p-3">
                      {s === null ? (
                        <Olculemedi neden="Kaynak kaydı tanınmayan bir biçimde geldi" teknik={`beklenen sözlük, gelen ${typeof k}`} kisa />
                      ) : (
                        <>
                          {metin(s.text) ? <p className="text-sm leading-6">{metin(s.text)}</p> : null}
                          <HamSatirlar govde={s} atla={["text"]} />
                        </>
                      )}
                    </div>
                  );
                })}
              </div>
            ) : null}

            <div className="flex flex-col gap-2">
              <h4 className="flex items-center gap-1.5 font-medium text-muted-foreground text-xs uppercase tracking-wide">
                <History className="size-3.5" aria-hidden />
                Tarihçe
              </h4>
              <Tarihce govde={d.tarihce} neden={d.tarihce_neden} />
            </div>

            <div className="flex flex-col gap-2">
              <h4 className="font-medium text-muted-foreground text-xs uppercase tracking-wide">Kaydın tamamı</h4>
              <HamSatirlar govde={o} atla={["text"]} />
            </div>
          </>
        );
      }}
    </UcKapisi>
  );
}

/* --------------------------------------------------------------------------- */

export function Bellekler({ bank, kayit }: { readonly bank: string | null; readonly kayit: Bolum }) {
  const [tur, setTur] = useState<string>("");
  const [durumSuzgeci, setDurumSuzgeci] = useState<string>("valid");
  /* KUTUDA YAZILAN ile ÜST SERVİSE GİDEN ayrı; ayrımın kendisi ortak şeritte
     yaşıyor (`parcalar.tsx::SuzgecSeridi`). Burada yalnız UYGULANMIŞ değer var. */
  const [arama, setArama] = useState("");
  const [etiketler, setEtiketler] = useState("");
  const [esleme, setEsleme] = useState<string>("any");
  const [atlanan, setAtlanan] = useState(0);
  const [acikKayit, setAcikKayit] = useState<string | null>(null);

  /* SÜZGEÇ DEĞİŞTİĞİNDE SAYFA BAŞA DÖNER: 4. sayfadayken süzgeci daraltmak, kısa
     bir sonuç kümesinin 4. sayfasını sormak olurdu ve boş bir tablo çizip "bu
     süzgeçte kayıt yok" izlenimi verirdi. */
  useEffect(() => {
    setAtlanan(0);
    setAcikKayit(null);
  }, [bank, tur, durumSuzgeci, arama, etiketler, esleme]);

  const sorgu =
    bank === null
      ? null
      : [
          `${UC_LISTE}?bank=${encodeURIComponent(bank)}`,
          `limit=${SAYFA_BOYU}`,
          `offset=${atlanan}`,
          `state=${encodeURIComponent(durumSuzgeci)}`,
          tur ? `fact_type=${encodeURIComponent(tur)}` : "",
          arama ? `q=${encodeURIComponent(arama)}` : "",
          etiketler ? `tags=${encodeURIComponent(etiketler)}&tags_match=${encodeURIComponent(esleme)}` : "",
        ]
          .filter(Boolean)
          .join("&");
  const liste = useApi<HafizaListesi>(sorgu);

  const detayYolu =
    bank === null || acikKayit === null
      ? null
      : `${UC_DETAY}?bank=${encodeURIComponent(bank)}&kimlik=${encodeURIComponent(acikKayit)}`;
  const detay = useApi<HafizaDetayi>(detayYolu);

  if (bank === null) {
    return (
      <BolumKart kimlik="hafiza-bellekler" baslik={kayit.baslik} soru={kayit.soru} ikon={kayit.ikon}>
        <Olculemedi neden="Okunacak banka seçilemedi" teknik="banka listesi boş ya da okunamadı — yukarıdaki seçici gerekçeyi taşıyor" />
      </BolumKart>
    );
  }

  return (
    <BolumKart kimlik="hafiza-bellekler" baslik={kayit.baslik} soru={kayit.soru} ikon={kayit.ikon}>
      {/* SÜZGEÇ ŞERİDİ — sonuç boş kalsa bile ÇİZİLİR, yoksa listeyi boşaltan bir
          süzgeç geri alınamazdı (üst yüzeyin kendi ölçülmüş dersi). */}
      <div className="flex flex-col gap-3">
        <div className="flex flex-wrap items-center gap-1.5">
          {TURLER.map((t) => (
            <Button key={t.deger || "hepsi"} variant={t.deger === tur ? "secondary" : "ghost"} size="xs" onClick={() => setTur(t.deger)}>
              {t.etiket}
            </Button>
          ))}
          <span className="mx-1 h-4 w-px bg-border" aria-hidden />
          {DURUMLAR.map((d) => (
            <Button
              key={d.deger}
              variant={d.deger === durumSuzgeci ? "secondary" : "ghost"}
              size="xs"
              onClick={() => setDurumSuzgeci(d.deger)}
            >
              {d.etiket}
            </Button>
          ))}
        </div>

        <SuzgecSeridi
          arama={arama}
          setArama={setArama}
          etiketler={etiketler}
          setEtiketler={setEtiketler}
          esleme={esleme}
          setEsleme={setEsleme}
          aramaEtiketi="Metinde ara"
        />
      </div>

      <UcKapisi durum={liste} yol={UC_LISTE}>
        {(l) =>
          l.neden ? (
            <Olculemedi neden="Kayıtlar okunamadı" teknik={l.neden} />
          ) : l.ogeler === undefined ? (
            <Olculemedi neden="Kayıt listesi bildirilmedi" teknik="uç kayıt dizisini döndürmedi" />
          ) : l.ogeler.length === 0 ? (
            <p className="text-muted-foreground text-sm">
              {atlanan === 0
                ? "Bu süzgeçle okundu ve eşleşen kayıt YOK. Bu ölçülmüş bir boşluktur."
                : "Bu sayfada kayıt YOK — liste daha önceki bir sayfada bitmiş."}
            </p>
          ) : (
            <div className="overflow-x-auto">
              <Table className="min-w-[52rem]">
                <TableHeader className="bg-muted/50">
                  <TableRow>
                    <TableHead>Kayıt</TableHead>
                    <TableHead className="w-40">Varlıklar</TableHead>
                    <TableHead className="w-40">Etiketler</TableHead>
                    <TableHead className="w-36">Gerçekleşme</TableHead>
                    <TableHead className="w-36">Anılma</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {l.ogeler.map((o, i) => {
                    const k = kayitKimligi(o);
                    const govdeMetni = metin(o.text);
                    const gerceklesme = damga(o.occurred_start);
                    const anilma = damga(o.mentioned_at);
                    return (
                      <TableRow
                        key={k ?? `kayit-${atlanan + i}`}
                        className={cn(k !== null && "cursor-pointer hover:bg-muted/50")}
                        onClick={k === null ? undefined : () => setAcikKayit(k)}
                      >
                        <TableCell className="max-w-0">
                          <div className="flex items-center gap-2">
                            {kayitTuru(o) ? (
                              <Badge variant="outline" className="shrink-0 font-mono text-[10px]">
                                {kayitTuru(o)}
                              </Badge>
                            ) : (
                              <Olculemedi neden="Türü bildirilmedi" teknik="tür alanı iki bilinen addan hiçbiriyle gelmedi" kisa />
                            )}
                            {govdeMetni === null ? (
                              <Olculemedi neden="Kaydın metni okunamadı" teknik="metin alanı gelmedi ya da dizge değil" kisa />
                            ) : (
                              <span className="line-clamp-2 min-w-0 text-sm">{govdeMetni}</span>
                            )}
                          </div>
                          {metin(o.context) ? (
                            <span className="mt-0.5 block truncate text-muted-foreground text-[11px]">{metin(o.context)}</span>
                          ) : null}
                          {k === null ? (
                            <span className="mt-1 block text-[11px] text-muted-foreground italic">
                              kimliği gelmediği için bu kaydın tamamı açılamaz
                            </span>
                          ) : null}
                        </TableCell>
                        <TableCell>
                          <Cipler degerler={listeye(o.entities)} tavan={2} ne="Varlık alanı" />
                        </TableCell>
                        <TableCell>
                          <Cipler degerler={listeye(o.tags)} tavan={2} ne="Etiket alanı" />
                        </TableCell>
                        <TableCell className="text-muted-foreground text-xs tabular-nums">
                          {gerceklesme ?? (
                            <Olculemedi
                              neden="Gerçekleşme zamanı gelmedi"
                              teknik="liste gövdesi olayın başlangıç damgasını her kayıtta taşımıyor"
                              kisa
                            />
                          )}
                        </TableCell>
                        <TableCell className="text-muted-foreground text-xs tabular-nums">
                          {anilma ?? (
                            <Olculemedi neden="Anılma zamanı gelmedi" teknik="anılma damgası gelmedi ya da çözülemedi" kisa />
                          )}
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </div>
          )
        }
      </UcKapisi>

      {/* SAYFALAMA KAPININ İÇİNDE (düzeltme turu 1, inceleme bulgusu M-4): dışarıda
          dururken istek düştüğünde üstte "Okunamadı" uyarısı, altında "0. kayıttan
          sonrası okundu" + Önceki/Sonraki çiziliyordu — yani ölçülmemiş bir sayfa
          konumu ölçülmüş gibi görünüyordu. Görev 1 incelemesinin B-2 bulgusunun
          küçük kardeşi: kapı, okuduğu şeyin ÜSTÜNDE durmalı. */}
      <UcKapisi durum={liste} yol={UC_LISTE} iskelet={<></>}>
        {(l) =>
          l.neden ? null : (
            <Sayfalama
              atlanan={atlanan}
              gelen={(l.ogeler ?? []).length}
              sayfaBoyu={SAYFA_BOYU}
              toplam={l.toplam}
              setAtlanan={setAtlanan}
            />
          )
        }
      </UcKapisi>

      <Sheet
        open={acikKayit !== null}
        onOpenChange={(a) => {
          if (!a) setAcikKayit(null);
        }}
      >
        <SheetContent side="right" className="w-full sm:max-w-xl">
          <SheetHeader className="pr-10">
            <SheetTitle className="text-base leading-6">Hafıza kaydı</SheetTitle>
            <SheetDescription className="break-all font-mono text-[11px]">
              {acikKayit ?? "kayıt seçilmedi"}
            </SheetDescription>
          </SheetHeader>
          <div className="flex min-h-0 flex-1 flex-col gap-4 overflow-y-auto px-4 pb-6">
            {acikKayit === null ? (
              <p className="text-muted-foreground text-sm">Tablodaki bir satıra tıkla.</p>
            ) : (
              <KayitDetayi durum={detay} />
            )}
          </div>
        </SheetContent>
      </Sheet>
    </BolumKart>
  );
}
