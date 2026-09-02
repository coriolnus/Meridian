"use client";

/* ============================================================================
   HAFIZA YÜZEYİ — Hindsight'ın pano görünümü (`/api/hindsight`), SALT-OKUNUR
   ----------------------------------------------------------------------------
   TARAYICI 8888'E ASLA GİTMEZ. Hindsight loopback'te dinler ve `/v1/*` uçları bir
   tenant anahtarı ister; o anahtar A1'de 0600 bir dosyada durur. Tarayıcıyı oraya
   bağlamanın iki yolu olurdu — portu dışarı açmak ya da anahtarı panoya indirmek —
   ve ikisi de bütün hafızayı bir XSS'in menziline sokardı. Bu sayfanın okuduğu TEK
   yer `api.py::api_hindsight` (+ `::api_hindsight_liste`, `::api_hindsight_detay`)
   vekilidir: sunucu okur, maskeler, anahtarsız bir gövde döner.

   YAZMA YOLU YOK VE OLMAYACAK. Hindsight'ın hafıza ekleme/silme fiilleri bu
   yüzeyden GEÇMEZ ve `gonder.ts` bu dosyaya hiç girmez. Hafızaya yazan taraf
   içe-aktarım hattıdır; panodan bir "sil" düğmesi, geri alınamaz bir fiili en hızlı
   erişime koymak olurdu (paletin YAZMA sınıfını dışarıda bırakan kararla aynı).

   ---------------------------------------------------------------------------
   BEDEL BEYANI — MEMORY DEFENSE BU SAYFADA AYRI BİR BÖLÜM DEĞİLDİR
   ---------------------------------------------------------------------------
   Bedel yasası: kazanç ölçülüp bedel ölçülmezse körlüğün belirtisi hiçbir şeydir.
   Bu sayfa DÖRT bölüm çiziyor ve BEŞİNCİSİ bilerek YOK.

   Hindsight'ın "memory defense" tarafının (şüphecilik ayarı, çelişki tespiti,
   reddedilen yazım) ÖLÇÜLEN API'de KENDİ UCU YOKTUR — `api.py::api_hindsight`ın
   okuduğu üç `/v1/*` bacağı `stats` · `llm-requests/stats` · `audit-logs/stats`tir
   ve savunma kararları bunların hiçbirinde ayrı bir alan olarak gelmiyor. Bu
   yüzden burada gösterilebilen TEK yakın şey denetim kaydı istatistiğidir ve o da
   `hafiza-operasyon` bölümünde çizilir.

   KAYBEDİLEN AÇIKÇA YAZILI: bir yazım REDDEDİLDİYSE bu sayfa onu göstermez ve
   gösteremez. Operatör "hafızaya ne girmedi" sorusunu bu ekrandan CEVAPLAYAMAZ.
   Boş bir "Savunma" bölümü çizip içine denetim sayaçlarını koymak, ölçülmeyen bir
   yeteneği ölçülmüş gibi gösterirdi — beşinci bölümün yokluğu, o bölümün yalanından
   dürüsttür. Aynı cümle ekranda da durur (`hafiza-operasyon` kapsam beyanı):
   şerhte kalan bir bedel, okuyucusu olmayan bir bedeldir (Yasa 6).

   ---------------------------------------------------------------------------
   KADANS — EMSALDEN ÖLÇÜLDÜ, TAHMİN EDİLMEDİ
   ---------------------------------------------------------------------------
   `KapiYuzey.tsx`in GERÇEK kadansı ölçüldü: `useApi(UC, NABIZ_MS * 2)` — yani
   YOKLAMA, 30 sn. Toplu uç burada AYNISINI uygular ve gerekçesi bu uçta DAHA
   güçlüdür: `api.py::api_hindsight` banka başına üç çağrı yapar (toplam `2+1+3N`),
   önbelleği yoktur ve N'e TAVAN YOKTUR. Panonun 15 sn'lik nabzıyla sormak bu
   maliyeti ikiye katlar, karşılığında hiçbir yeni bilgi getirmezdi: hafıza bankası
   sayısı ve sayaçları saniyede bir kaymaz.

   AÇIK RİSK (uydurma yasağı — çözülmüş gibi yazılmıyor): bugün N=2 (ölçüldü
   2026-09-02). Bot bank'leri doğduğunda `3N` çağrı 30 sn'lik yoklamanın altında
   kalmayabilir. Buraya bir tavan YAZILMADI çünkü ölçülmemiş bir eşik, ölçülmüş bir
   sayı gibi okunurdu; bu satır o günü BEKLEYEN kayıttır.

   LİSTE VE DETAY YOKLANMAZ (periyot verilmez, tek seferlik okunur) ve bu bilinçli
   bir AYRIMDIR: ikisi de GEZİNMEYLE tetiklenen okumalardır. Sayfalanmış bir listeyi
   30 sn'de bir yeniden çekmek, operatör satırları okurken altındaki tabloyu
   değiştirirdi — üstelik yeni bir bilgi vaadi olmadan (bu bankaya yazan taraf içe
   aktarım hattıdır, saniyelik değil).
   ============================================================================ */
import { useEffect, useState } from "react";
import { Activity, BookOpen, Brain, Gauge, Landmark } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { cn } from "@/lib/utils";

import { YUZEYLER } from "../../alanlar";
import { useRota } from "../../rota";
import { NABIZ_MS, useApi, type Durum } from "../../veri";
import { BolumKart, Kapi as UcKapisi, Olculemedi, OkRozet, Satir, zamanMetni } from "../sistem/parcalar";
import type {
  HafizaDetayi,
  HafizaGovdesi,
  HafizaKaydi,
  HafizaListesi,
  HamGovde,
} from "./uctipleri";

const UC = "/api/hindsight";
const UC_LISTE = "/api/hindsight/liste";
const UC_DETAY = "/api/hindsight/detay";

/* SAYFA BOYU BİR GÖRÜNÜM KARARIDIR, BİR ÖLÇÜM DEĞİL — ve bu ayrım yazılı durmalı.
   Sunucu tavanı 200 (`api.py::HAFIZA_LISTE_TAVANI`); burada 50 seçildi çünkü tek
   ekranda taranabilir bir tablo isteniyor. 200 istemek dürüst olurdu ama okunmayan
   150 satır için üç kat gövde taşırdı. Tavanı burada TEKRAR yazmıyoruz: sınırlama
   zaten sunucuda (`api.py::_hafiza_sayi`) ve iki kopya sessizce ayrışır. */
const SAYFA_BOYU = 50;

/* ---------------------------------------------------------------------------
   HAM GÖVDE ÇİZİMİ — "tanımadığını sessizce boş sayma" ilkesinin ekran karşılığı
   Bu sayfanın gösterdiği sayıların BÜYÜK KISMI depo tarafından KURULMAZ, yalnız
   TAŞINIR (`uctipleri.ts::HamGovde` şerhi). Alan adlarını burada sabitlemek
   `api.py::_hafiza_surum`un ölçülmüş dersini tekrarlamak olurdu: `version`
   varsayılmıştı, canlıda alan `api_version`dı, ve sürüm SESSİZCE boş kalacaktı.
   Bu yüzden anahtarlar TELDEN gelir ve tanınmayan anahtar ATILMAZ, ham basılır.
   --------------------------------------------------------------------------- */

/** JSON değerini insan metnine çevirir. Çeviremediğinde `null` — çağıran ham basar. */
function hamMetin(deger: unknown): string | null {
  if (typeof deger === "string") return deger;
  if (typeof deger === "number") return Number.isFinite(deger) ? deger.toLocaleString("tr-TR") : null;
  if (typeof deger === "boolean") return deger ? "evet" : "hayır";
  return null;
}

/**
 * ISO-BENZERİ DAMGA TESTİ — ve NEDEN VAR (düzeltme turu 1, inceleme bulgusu B-1).
 *
 * İlk yazımda `HamDeger` HER skaleri `zamanMetni`ne veriyordu: "alan adını bilmiyorum, belki
 * tarihtir" mantığıyla. ÖLÇÜLDÜ ki bu, ekrana UYDURMA TARİH bastırıyordu — V8'de
 * `new Date("3")` GEÇERLİ bir tarihtir (01.03.2001). Yani 0-999 arası her sayaç (olay sayısı,
 * istek sayısı) ekranda bir tarihe dönüşüyordu; 1000 ve üstü yalnız KAZARA kurtuluyordu, çünkü
 * `toLocaleString("tr-TR")` binlik ayracı olarak nokta koyuyor ve `new Date("1.234")` geçersiz
 * oluyordu. Bir sayacı tarihe çevirmek, uydurma yasağının en sinsi biçimi: ekran hem yanlış hem
 * kendinden emin görünür.
 *
 * KURAL: `zamanMetni` bu dosyada ancak biçimi ISO damgasına BENZEYEN bir dizgeye uygulanır.
 * Repodaki 30+ `zamanMetni` çağrısının hepsi ALAN ADI bilinen yerlerde duruyor (`date`,
 * `hesaplama_ts` …); tek spekülatif çağrı buydu. Alan adından bağımsız skaler beslemek YASAK.
 */
const ISO_BENZERI = /^\d{4}-\d{2}-\d{2}T/;

/** Düz sözlük mü? Dizi ve `null` BURADA sözlük DEĞİLDİR — ikisi de ayrı çizilir. */
function sozluk(deger: unknown): HamGovde | null {
  return typeof deger === "object" && deger !== null && !Array.isArray(deger) ? (deger as HamGovde) : null;
}

/** Tek bir ham değer. Üç hâl AYRI: alan yok · değer boş · değer var. */
function HamDeger({ deger }: { readonly deger: unknown }) {
  if (deger === undefined) {
    return <Olculemedi neden="Bu alan bildirilmedi" teknik="anahtar üst servisin gövdesinde hiç yok" kisa />;
  }
  if (deger === null) {
    return <Olculemedi neden="Ölçüldü, sonuç yok" teknik="alan geldi ama değeri boş — sıfır ile aynı şey değil" kisa />;
  }
  /* ZAMAN ÇEVİRİSİ YALNIZ DİZGEYE VE YALNIZ ISO BİÇİMİNDE (yukarıdaki `ISO_BENZERI` şerhi):
     sayıyı tarihe çevirmek ölçülmüş bir sayacı uydurma bir güne dönüştürürdü. */
  if (typeof deger === "string") {
    const zaman = ISO_BENZERI.test(deger) ? zamanMetni(deger) : null;
    return <span className="tabular-nums">{zaman ?? deger}</span>;
  }
  const duz = hamMetin(deger);
  if (duz !== null) {
    return <span className="tabular-nums">{duz}</span>;
  }
  /* İÇ İÇE GÖVDE: şekli ölçülmedi. Atmak "böyle bir veri yok" derdi; ham basmak
     "böyle bir veri var, biçimini tanımıyorum" der. İkincisi doğru olandır. */
  const metin = JSON.stringify(deger);
  return (
    <code className="break-all text-[11px]" title={metin}>
      {metin.length > 140 ? `${metin.slice(0, 140)}…` : metin}
    </code>
  );
}

/**
 * Bir sayaç gövdesinin TAMAMI — anahtarlarıyla birlikte.
 *
 * ANAHTARLAR ÇEVRİLMEZ VE BU BİR EKSİK DEĞİL, BEYAN: sözlükleri ölçülmediği için
 * bir çeviri tablosu yazmak, uydurulmuş bir ad kümesini ekranın birincil metni
 * yapardı. Tanınmayan bir alan geldiği gün ham adıyla görünür — kaybolmaz.
 */
function SayacGovdesi({ govde, neden }: { readonly govde: unknown; readonly neden?: string | null }) {
  if (neden) {
    return <Olculemedi neden="Bu bankanın sayaçları okunamadı" teknik={neden} />;
  }
  if (govde === undefined) {
    return <Olculemedi neden="Sayaçlar bildirilmedi" teknik="uç bu banka için sayaç alanını döndürmedi" />;
  }
  if (govde === null) {
    return <Olculemedi neden="Ölçüm denendi, gövde gelmedi" teknik="sayaç alanı boş döndü ve gerekçe de taşınmadı" />;
  }
  const s = sozluk(govde);
  if (s === null) {
    return (
      <Olculemedi
        neden="Sayaç gövdesi tanınmayan bir biçimde geldi"
        teknik={`beklenen sözlük, gelen ${Array.isArray(govde) ? "dizi" : typeof govde} — şema sürüklenmiş olabilir`}
      />
    );
  }
  const satirlar = Object.entries(s).sort((a, b) => a[0].localeCompare(b[0]));
  if (satirlar.length === 0) {
    return (
      <p className="text-muted-foreground text-sm">
        Sayaç gövdesi OKUNDU ve içi boş geldi. Bu ölçülmüş bir boşluktur — "okuyamadım" ile aynı şey değildir.
      </p>
    );
  }
  return (
    <div>
      {satirlar.map(([anahtar, deger]) => (
        <Satir key={anahtar} etiket={anahtar}>
          <HamDeger deger={deger} />
        </Satir>
      ))}
    </div>
  );
}

/** Banka kimliklerini gövdeden çıkarır — kimliksiz satır sayılmaz, uydurulmaz. */
function bankaKimlikleri(g: HafizaGovdesi | null): readonly string[] {
  return (g?.bankalar ?? []).map((b) => b.bank_id).filter((k): k is string => typeof k === "string" && k.length > 0);
}

/* ---------------------------------------------------------------------------
   BÖLÜM 1 — BANKALAR (+ SERVİSİN SAĞLIĞI)
   İKİ BACAK AYRI, çünkü uçta da ayrı ölçülüyorlar (`api.py::api_hindsight`): anahtar
   dosyası olmayan bir makinede servis YİNE de ayakta olabilir. Tek rozete indirmek
   bir arızayı iki körlüğe çevirirdi.

   BOŞ LİSTE İLE ÖLÇÜLEMEDİ AYRI ÇİZİLİR ve bu, bu sayfanın en çok iş gören ayrımıdır:
   bu makinede anahtar YOK, yani normal hâl `bankalar: []` + DOLU gerekçedir. Boş
   listeyi tek başına çizen bir ekran her gün "hafızada banka yok" diye yalan söylerdi.
   --------------------------------------------------------------------------- */
function Bankalar({ durum }: { readonly durum: Durum<HafizaGovdesi> }) {
  return (
    <BolumKart
      kimlik="hafiza-bankalar"
      baslik="Hafıza bankaları"
      soru="Hangi bankalar var, hafıza servisi ayakta mı?"
      ikon={Landmark}
    >
      <UcKapisi durum={durum} yol={UC}>
        {(g) => {
          const s = g.saglik;
          const bankalar = g.bankalar ?? [];
          return (
            <>
              {s === undefined ? (
                <Olculemedi neden="Servisin durumu bildirilmedi" teknik={`${UC} \`saglik\` bloğunu döndürmedi`} />
              ) : (
                <>
                  <div className="flex flex-wrap items-center gap-2">
                    <OkRozet
                      ok={s.erisilebilir}
                      iyi="Hafıza servisi ayakta"
                      kotu="Hafıza servisine ulaşılamadı"
                      neden="Servisin ayakta olup olmadığı ölçülmedi"
                      teknik="`saglik.erisilebilir` alanı gelmedi"
                    />
                  </div>
                  {s.neden ? (
                    <p className="text-destructive text-sm">{s.neden}</p>
                  ) : (
                    <p className="text-muted-foreground text-sm">
                      Servis okundu. Aşağıdaki banka satırları ÖLÇÜLMÜŞ değerlerdir.
                    </p>
                  )}
                  <Satir etiket="Servis sürümü">
                    {s.surum ? (
                      <code className="text-xs">{s.surum}</code>
                    ) : s.surum === null ? (
                      /* `null` BURADA "sürümsüz servis" DEĞİL, ŞEMA SÜRÜKLENMESİ İŞARETİDİR
                         (`api.py::_hafiza_surum`): uç okundu ama sürüm alanı tanınmadı. */
                      <Olculemedi
                        neden="Sürüm alanı tanınmadı"
                        teknik="sürüm ucu okundu ama beklenen adların hiçbiri gövdede yok — şema sürüklenmiş olabilir"
                        kisa
                      />
                    ) : (
                      <Olculemedi neden="Sürüm bildirilmedi" teknik="`saglik.surum` alanı gelmedi" kisa />
                    )}
                  </Satir>
                </>
              )}

              {g.bankalar === undefined ? (
                <Olculemedi neden="Bankalar bildirilmedi" teknik={`${UC} \`bankalar\` alanını döndürmedi`} />
              ) : g.bankalar_neden ? (
                /* ÖLÇÜLEMEDİ — boş liste burada bir ölçüm SONUCU değil, bir ölçüm YOKLUĞU. */
                <Olculemedi neden="Bankalar okunamadı" teknik={g.bankalar_neden} />
              ) : bankalar.length === 0 ? (
                <p className="text-muted-foreground text-sm">
                  Banka listesi OKUNDU ve hafızada tanımlı banka YOK. Bu bir arıza değil, ölçülmüş bir boşluk.
                </p>
              ) : (
                <div className="flex flex-col gap-3">
                  {bankalar.map((b, i) => (
                    <div key={b.bank_id ?? `banka-${i}`} className="flex flex-col gap-2 rounded-lg border p-4">
                      <div className="flex flex-wrap items-baseline gap-2">
                        <span className="font-semibold text-sm">
                          {b.bank_id ?? (
                            <Olculemedi
                              neden="Bankanın kimliği okunamadı"
                              teknik="satırda kimlik alanı yok — kimliksiz bankaya uç çağrılamaz"
                              kisa
                            />
                          )}
                        </span>
                      </div>
                      <SayacGovdesi govde={b.stats} neden={b.stats_neden} />
                    </div>
                  ))}
                </div>
              )}
            </>
          );
        }}
      </UcKapisi>
    </BolumKart>
  );
}

/* ---------------------------------------------------------------------------
   BÖLÜM 2 — KAYITLAR (liste + detay)
   TOPLAM SAYI YOKTUR ve bu ekranda SÖYLENİR: `api.py::api_hindsight_liste` yalnız
   `{ogeler, neden}` döner. "3 / 12 sayfa" çizmek, sayfa sayısını uydurmak olurdu.
   "Sonraki" düğmesinin açık olması da bir ÖLÇÜM DEĞİL bir ÇIKARIMDIR (sayfa dolu
   geldi) — ve bu ayrım düğmenin yanında yazılı durur.
   --------------------------------------------------------------------------- */
function kayitKimligi(o: HafizaKaydi): string | null {
  return typeof o.id === "string" && o.id.length > 0 ? o.id : null;
}

/** Çekmecenin gövdesi: kaydın TAMAMI, anahtarlarıyla. Hiçbir alan gizlenmez. */
function KayitDetayi({ durum }: { readonly durum: Durum<HafizaDetayi> }) {
  return (
    <UcKapisi durum={durum} yol={UC_DETAY}>
      {(d) => {
        if (d.neden) {
          return <Olculemedi neden="Kayıt okunamadı" teknik={d.neden} />;
        }
        if (d.oge === null) {
          /* `oge: null` UCUN BİLİNÇLİ TERCİHİ: bulunamayan kayıtta boş sözlük dönmek
             "kayıt var ama içi boş" yalanı olurdu. Ekran o tercihi aynen yazar. */
          return (
            <p className="text-muted-foreground text-sm">
              Bu kimlikle bir kayıt BULUNAMADI. Kayıt silinmiş ya da başka bir bankaya taşınmış olabilir — gövde
              boş değil, kaydın kendisi yok.
            </p>
          );
        }
        if (d.oge === undefined) {
          return <Olculemedi neden="Kayıt gövdesi bildirilmedi" teknik={`${UC_DETAY} \`oge\` alanını döndürmedi`} />;
        }
        const satirlar = Object.entries(d.oge).sort((a, b) => a[0].localeCompare(b[0]));
        const metin = typeof d.oge.text === "string" ? d.oge.text : null;
        return (
          <>
            {metin === null ? (
              <Olculemedi neden="Kaydın metni okunamadı" teknik="`text` alanı gelmedi ya da dizge değil" />
            ) : (
              <p className="whitespace-pre-wrap text-sm leading-6">{metin}</p>
            )}
            <div>
              <h4 className="mb-1 font-medium text-muted-foreground text-xs uppercase tracking-wide">Kaydın tamamı</h4>
              {satirlar.map(([anahtar, deger]) => (
                <Satir key={anahtar} etiket={anahtar}>
                  <HamDeger deger={deger} />
                </Satir>
              ))}
            </div>
          </>
        );
      }}
    </UcKapisi>
  );
}

function Kayitlar({ durum }: { readonly durum: Durum<HafizaGovdesi> }) {
  const bankalar = bankaKimlikleri(durum.veri);
  const [secilen, setSecilen] = useState<string | null>(null);
  const [atlanan, setAtlanan] = useState(0);
  const [acikKayit, setAcikKayit] = useState<string | null>(null);

  /* SEÇİM TÜRETİLİR, KOPYALANMAZ: seçili banka `null` iken listenin İLKİ kullanılır.
     Bunu bir efektle duruma yazmak, aynı gerçeğin ikinci kopyasını üretirdi — banka
     listesi değiştiğinde kopya bayatlar ve ekran artık var olmayan bir bankayı sorar. */
  const aktif = (secilen !== null && bankalar.includes(secilen) ? secilen : bankalar[0]) ?? null;

  const listeYolu =
    aktif === null
      ? null
      : `${UC_LISTE}?bank=${encodeURIComponent(aktif)}&limit=${SAYFA_BOYU}&offset=${atlanan}`;
  const liste = useApi<HafizaListesi>(listeYolu);

  const detayYolu =
    aktif === null || acikKayit === null
      ? null
      : `${UC_DETAY}?bank=${encodeURIComponent(aktif)}&kimlik=${encodeURIComponent(acikKayit)}`;
  const detay = useApi<HafizaDetayi>(detayYolu);

  /* BANKA DEĞİŞTİĞİNDE SAYFA BAŞA DÖNER: 4. sayfadayken başka bankaya geçmek, o
     bankanın 4. sayfasını sormak olurdu ve kısa bir bankada boş bir tablo çizip
     "bu bankada kayıt yok" izlenimi verirdi. */
  useEffect(() => {
    setAtlanan(0);
    setAcikKayit(null);
  }, [aktif]);

  const ogeler = liste.veri?.ogeler ?? [];
  const doluSayfa = ogeler.length === SAYFA_BOYU;

  return (
    <BolumKart
      kimlik="hafiza-bellekler"
      baslik="Kayıtlar"
      soru="Bu bankada ne yazılı, tek tek ne diyor?"
      ikon={BookOpen}
      aksiyon={
        bankalar.length > 0 ? (
          <Select value={aktif ?? ""} onValueChange={(d) => setSecilen(d)}>
            <SelectTrigger className="w-56" aria-label="Banka seç">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {bankalar.map((b) => (
                <SelectItem key={b} value={b}>
                  {b}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        ) : undefined
      }
    >
      {/* TOPLU UÇ ÖNCE KAPIDAN GEÇER (düzeltme turu 1, inceleme bulgusu B-2).
          İlk yazımda "banka yok" dalı `UcKapisi` DIŞINDAYDI ve `bankalar` boş dizisi
          ÜÇ AYRI HÂLDEN geliyordu: gövde henüz YÜKLENMEDİ · istek DÜŞTÜ · oturum 401
          oldu. Üçü de "Okunacak bir banka YOK" cümlesine düşüyordu — yani ölçülmemiş
          bir şey ölçülmüş boşluk diye okunuyordu (`veri.ts`in kapatmak için var olduğu
          sınıfın ta kendisi). Kapı artık öteki üç bölümdekiyle AYNI yerde. */}
      <UcKapisi durum={durum} yol={UC}>
        {(g) =>
          bankalar.length === 0 ? (
            g.bankalar_neden ? (
              <Olculemedi neden="Okunacak banka belirlenemedi" teknik={g.bankalar_neden} />
            ) : (
              <p className="text-muted-foreground text-sm">
                Okunacak bir banka YOK — yukarıdaki banka bölümü ne ölçtüyse kayıt listesi de onu izler.
              </p>
            )
          ) : (
            <>
              <UcKapisi durum={liste} yol={UC_LISTE}>
                {(l) =>
                  l.neden ? (
                    <Olculemedi neden="Kayıtlar okunamadı" teknik={l.neden} />
                  ) : l.ogeler === undefined ? (
                    <Olculemedi neden="Kayıt listesi bildirilmedi" teknik={`${UC_LISTE} \`ogeler\` alanını döndürmedi`} />
                  ) : l.ogeler.length === 0 ? (
                    <p className="text-muted-foreground text-sm">
                      {atlanan === 0
                        ? "Bu banka OKUNDU ve içinde kayıt YOK. Bu ölçülmüş bir boşluktur."
                        : "Bu sayfada kayıt YOK — liste daha önceki bir sayfada bitmiş."}
                    </p>
                  ) : (
                    <div className="overflow-x-auto">
                      <Table className="min-w-[42rem]">
                        <TableHeader className="bg-muted/50">
                          <TableRow>
                            <TableHead>Kayıt</TableHead>
                            <TableHead className="w-32">Tür</TableHead>
                            <TableHead className="w-44">Tarih</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {l.ogeler.map((o, i) => {
                            const k = kayitKimligi(o);
                            const metin = typeof o.text === "string" ? o.text : null;
                            const tarih = typeof o.date === "string" ? zamanMetni(o.date) : null;
                            return (
                              <TableRow
                                key={k ?? `kayit-${atlanan + i}`}
                                className={cn(k !== null && "cursor-pointer hover:bg-muted/50")}
                                onClick={k === null ? undefined : () => setAcikKayit(k)}
                              >
                                <TableCell className="max-w-0">
                                  {metin === null ? (
                                    <Olculemedi
                                      neden="Kaydın metni okunamadı"
                                      teknik="`text` alanı gelmedi ya da dizge değil"
                                      kisa
                                    />
                                  ) : (
                                    <span className="line-clamp-2 text-sm">{metin}</span>
                                  )}
                                  {k === null ? (
                                    <span className="mt-1 block text-muted-foreground text-[11px] italic">
                                      kimliği gelmediği için bu kaydın tamamı açılamaz
                                    </span>
                                  ) : null}
                                </TableCell>
                                <TableCell>
                                  {typeof o.fact_type === "string" && o.fact_type ? (
                                    <Badge variant="outline" className="font-mono text-[11px]">
                                      {o.fact_type}
                                    </Badge>
                                  ) : (
                                    <Olculemedi neden="Türü bildirilmedi" teknik="`fact_type` alanı gelmedi" kisa />
                                  )}
                                </TableCell>
                                <TableCell className="text-muted-foreground text-xs tabular-nums">
                                  {tarih ?? (
                                    <Olculemedi
                                      neden="Tarihi okunamadı"
                                      teknik="`date` alanı gelmedi ya da çözülemeyen bir damga taşıyor"
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
                  )
                }
              </UcKapisi>

              {/* SAYFALAMA — VE SÖYLEYEMEDİĞİ ŞEY. Uç toplam sayı döndürmüyor; burada
                  "kaçıncı sayfadayız" yazmak o sayıyı uydurmak olurdu. Gösterilen tek
                  şey OKUNAN ARALIKtır ve "sonraki"nin açık olması bir çıkarımdır. */}
              <div className="flex flex-wrap items-center justify-between gap-2">
                <span className="text-muted-foreground text-xs tabular-nums">
                  {ogeler.length > 0
                    ? `${atlanan + 1}–${atlanan + ogeler.length} arası okundu`
                    : `${atlanan}. kayıttan sonrası okundu`}
                </span>
                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={atlanan === 0}
                    onClick={() => setAtlanan((n) => Math.max(0, n - SAYFA_BOYU))}
                  >
                    Önceki
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={!doluSayfa}
                    title={
                      doluSayfa
                        ? "sayfa dolu geldi — devamı OLABİLİR; uç toplam sayı döndürmediği için bu bir çıkarımdır, ölçüm değil"
                        : "sayfa dolmadan bitti — okunacak başka kayıt görünmüyor"
                    }
                    onClick={() => setAtlanan((n) => n + SAYFA_BOYU)}
                  >
                    Sonraki
                  </Button>
                </div>
              </div>
              <p className="text-muted-foreground text-xs">
                Bu uç toplam kayıt sayısını bildirmiyor: kaçıncı sayfada olduğun ekranda YAZAMAZ, çünkü o sayı ölçülmüş
                değil. "Sonraki" ancak sayfa dolu geldiğinde açılır — dolu bir sayfa devamının OLABİLECEĞİNİ söyler,
                olduğunu değil.
              </p>
            </>
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

/* ---------------------------------------------------------------------------
   BÖLÜM 3 ve 4 — BANKA BAŞINA SAYAÇ KUTULARI
   İKİSİ AYNI ŞEKİLDE ÇİZİLİR ve tek bir çizici paylaşır (tek-kaynak yasası: iki
   kopya sessizce ayrışır). Ayrı duran şey KUTUNUN İÇİNDEKİ ALAN ADIDIR — biri
   `audit_stats`, öteki `llm_stats` taşır ve ikisi de üst servisten AYNEN geçer.

   BOŞ SÖZLÜK İKİ AYRI ŞEY OLABİLİR ve ayrımı gövdeden okunur: bankalar hiç
   okunamadıysa (`bankalar_neden` dolu) uç bu sözlükleri BOŞ döndürür — o boşluk
   "kullanım yok" değil "ölçüm yapılmadı"dır.
   --------------------------------------------------------------------------- */
function BankaKutulari({
  govde,
  kutular,
  alanAdi,
  cikar,
  bosMetin,
}: {
  readonly govde: HafizaGovdesi;
  readonly kutular: Readonly<Record<string, { readonly neden?: string | null }>> | undefined;
  readonly alanAdi: string;
  readonly cikar: (kutu: { readonly neden?: string | null }) => unknown;
  readonly bosMetin: string;
}) {
  if (kutular === undefined) {
    return <Olculemedi neden="Sayaç bloğu bildirilmedi" teknik={`${UC} \`${alanAdi}\` bloğunu döndürmedi`} />;
  }
  if (govde.bankalar_neden) {
    /* ÖNCE BU: bankalar okunamadığında uç sözlüğü BOŞ döndürür. Aşağıdaki "ölçüldü,
       kullanım yok" cümlesini basmak, yapılmamış bir ölçümü sonuç diye okutmak olurdu. */
    return <Olculemedi neden="Sayaçlar ölçülmedi" teknik={`bankalar okunamadığı için hiç sorulmadı — ${govde.bankalar_neden}`} />;
  }
  const satirlar = Object.entries(kutular).sort((a, b) => a[0].localeCompare(b[0]));
  if (satirlar.length === 0) {
    return <p className="text-muted-foreground text-sm">{bosMetin}</p>;
  }
  return (
    <div className="flex flex-col gap-3">
      {satirlar.map(([bank, kutu]) => (
        <div key={bank} className="flex flex-col gap-2 rounded-lg border p-4">
          <span className="font-semibold text-sm">{bank}</span>
          <SayacGovdesi govde={cikar(kutu)} neden={kutu.neden} />
        </div>
      ))}
    </div>
  );
}

function Operasyon({ durum }: { readonly durum: Durum<HafizaGovdesi> }) {
  return (
    <BolumKart
      kimlik="hafiza-operasyon"
      baslik="Yazma ve okuma hareketleri"
      soru="Bankaya son günlerde ne işlendi?"
      ikon={Activity}
    >
      <UcKapisi durum={durum} yol={UC}>
        {(g) => (
          <>
            <BankaKutulari
              govde={g}
              kutular={g.operasyon}
              alanAdi="operasyon"
              cikar={(k) => (k as { readonly audit_stats?: unknown }).audit_stats}
              bosMetin="Hareket sayaçları OKUNDU ve hiçbir banka için kutu gelmedi. Bu ölçülmüş bir boşluktur."
            />

            {/* KAPSAM BEYANI — KONTROLÖR HÜKMÜ (bedel yasası): bu satır ekranda DURMAK
                ZORUNDA. Dosya başlığındaki bedel beyanının okuyucusu olan hâli budur;
                yalnız şerhte kalsaydı Yasa 6'nın tersine düşerdi (okuyucusuz yazım). */}
            <p className="rounded-md border border-dashed p-3 text-muted-foreground text-xs">
              <span className="font-medium">Bu ölçümün kapsamı: </span>
              burada görünen sayaçlar denetim kaydından gelir — yani hafızaya NE İŞLENDİĞİNİ sayar. Bir yazımın
              REDDEDİLİP reddedilmediğini, çelişki bulunup bulunmadığını bu sayfa GÖSTEREMEZ: ölçülen üç sayaç
              ucunun hiçbiri o kararı ayrı bir alan olarak taşımıyor. "Hafızaya ne girmedi" sorusu bu ekrandan
              cevaplanamaz.
            </p>
          </>
        )}
      </UcKapisi>
    </BolumKart>
  );
}

function Kota({ durum }: { readonly durum: Durum<HafizaGovdesi> }) {
  return (
    <BolumKart
      kimlik="hafiza-kota"
      baslik="Model çağrısı kullanımı"
      soru="Hafıza servisi ne kadar model çağrısı harcadı?"
      ikon={Gauge}
    >
      <UcKapisi durum={durum} yol={UC}>
        {(g) => (
          <BankaKutulari
            govde={g}
            kutular={g.kota}
            alanAdi="kota"
            cikar={(k) => (k as { readonly llm_stats?: unknown }).llm_stats}
            bosMetin="Kullanım sayaçları OKUNDU ve hiçbir banka için kutu gelmedi. Bu ölçülmüş bir boşluktur."
          />
        )}
      </UcKapisi>
    </BolumKart>
  );
}

/* --------------------------------------------------------------------------- */

export function HafizaYuzey() {
  const { bolum } = useRota();
  // BAŞLIK KAYITTAN OKUNUR (KapiYuzey deseni): `alanlar.ts` bu yüzeyin başlığını ve
  // cevapladığı SORUYU tek yerde tutuyor. İkinci kez yazsaydık kayıt değiştiğinde
  // ekran sessizce eski soruyu sormaya devam ederdi.
  const y = YUZEYLER.memory;
  const hafiza = useApi<HafizaGovdesi>(UC, NABIZ_MS * 2);

  useEffect(() => {
    if (!bolum) {
      window.scrollTo({ top: 0, behavior: "instant" });
      return;
    }
    document.getElementById(`bolum-${bolum}`)?.scrollIntoView({ behavior: "smooth", block: "start" });
  }, [bolum]);

  const g = hafiza.veri;
  const bankaN = g?.bankalar?.length;

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0">
          <h1 className="flex items-center gap-2 font-semibold text-2xl tracking-tight">
            <Brain className="size-5 shrink-0 text-muted-foreground" aria-hidden />
            {y.baslik}
          </h1>
          <p className="mt-1 text-muted-foreground text-sm">{y.soru}</p>
        </div>
        {/* ROZET ŞERİDİ YALNIZ ÖLÇÜLENİ TAŞIR (KapiYuzey kuralı): `bankalar_neden`
            doluyken banka sayısı BASILMAZ — o sıfır bir ölçüm değil, bir ölçüm
            yokluğudur ve "0 banka" diye okunurdu. */}
        <div className="flex flex-wrap items-center gap-2">
          {bankaN !== undefined && !g?.bankalar_neden ? (
            <Badge variant="outline" className="tabular-nums">
              {bankaN} banka
            </Badge>
          ) : null}
          {g?.saglik?.erisilebilir === false ? <Badge variant="destructive">servise ulaşılamadı</Badge> : null}
        </div>
      </div>

      <Bankalar durum={hafiza} />
      <Kayitlar durum={hafiza} />
      <Operasyon durum={hafiza} />
      <Kota durum={hafiza} />
    </div>
  );
}
