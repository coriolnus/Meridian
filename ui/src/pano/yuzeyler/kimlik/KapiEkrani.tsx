"use client";

/* ============================================================================
   KAPI EKRANLARI — kurulum ve giriş gövdeleri, KABINDAN BAĞIMSIZ
   ----------------------------------------------------------------------------
   TEK TÜKETİCİ: `pano/GirisKapisi.tsx`. Dosya bir tur boyunca İKİ kap tarafından
   çağrıldı (kapı + kabuk içi yüzey); düzeltme-2'de (2026-09-02) kabuk içindeki
   dallar erişilemez olduğu için silindi ve geriye tek çağıran kaldı.

   PEKİ NEDEN HÂLÂ AYRI BİR DOSYA — iki gerekçe, ikisi de `GirisKapisi.tsx`e
   taşımaya karşı:
     1. ÇAPALAR: `bolum-giris` ve `bolum-kayit`, `alanlar.ts`teki kayıtla eşleşen
        DOM çapalarıdır ve `tests/test_pano_yuzey_kaydi_v288.py` pariteyi YALNIZ
        `yuzeyler/**` altında ölçer. Gövdeyi `pano/`ye taşımak çiviyi kör ederdi —
        yani kaydı ile ekranı ayrışan bölüm sınıfını geri açardı.
     2. KOMŞULUK: bu dosya üç formu (`GirisFormu` · `KayitFormu` · `KurulumFormu`)
        birleştiriyor ve üçü de bu dizinde. Ekran gövdesinin formlarının yanında
        durması, kabın (çerçeve) gövdeden ayrı durması kadar doğal.

   AÇIK KALEM (Rol-1'in kararı): kapı tam ekrana çıktığından beri `giris`/`kayit`
   bölümlerine kenar çubuğundan DERİN BAĞLA gidilemiyor — o iki çapa yalnız kapıda
   çiziliyor, kapıda ise kenar çubuğu yok. Ya kayıttan düşerler ya da kabuk içi
   yüzey onları yeniden sunar. Bu dosya o karar verilene kadar kaydın söylediği
   sözleşmeyi tutuyor.
   ============================================================================ */
import { KeyRound, UserPlus } from "lucide-react";

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

import { GirisFormu } from "./GirisFormu";
import { KayitFormu } from "./KayitFormu";
import { KurulumFormu } from "./KurulumFormu";

export type KapiSekmesi = "giris" | "kayit";

/* --- KURULUM: parola HENÜZ YOK --------------------------------------------- */

export function KurulumEkrani({ onBasari }: { readonly onBasari: () => void }) {
  return (
    <div className="flex flex-col gap-4">
      <div className="space-y-1">
        <h2 className="flex items-center gap-2 font-medium text-xl">
          <KeyRound className="size-4 text-muted-foreground" aria-hidden />
          İlk kurulum
        </h2>
        {/* İÇ AYRINTI KALKTI, OLGU KALDI (düzeltme-1): eskiden burada uç yolu ve
            alan adı yazıyordu (`/api/session` `password_set: false`). Ziyaretçinin
            bilmesi gereken şey hangi alanın ne döndürdüğü değil, PANONUN ŞU AN
            KORUMASIZ olduğu — o cümle olduğu gibi duruyor, uyarı zayıflatılmadı. */}
        <p className="text-muted-foreground text-sm">
          Bu kurulumda henüz bir parola belirlenmemiş ve pano şu an korumasız. Aşağıdan ilk parolayı belirle.
        </p>
      </div>
      <KurulumFormu onBasari={onBasari} />
    </div>
  );
}

/* --- GİRİŞ: parola kurulu, oturum kapalı ----------------------------------- */

/**
 * `dustu` İKİ AYRI OLGUYU AYIRIR ve ekran aynı kalır, CÜMLE değişir:
 *   false → bu tarayıcıda hiç oturum açılmadı (ilk yüz)
 *   true  → bu sekmede AÇIK bir oturum ölçülmüştü ve artık kapalı
 * Aynı formu iki cümleyle sunmak bir süs değil: "yeniden gir" ile "giriş yap"
 * operatöre farklı şeyler söyler — birincisi bir şeyin BİTTİĞİNİ bildirir.
 * Ölçüm bu SEKMEYE aittir; yeni bir sekme oturumun daha önce açık olduğunu
 * bilemez ve bu ekran öyle olduğunu iddia etmez.
 */
export function GirisEkrani({
  sekme,
  onSekme,
  onBasari,
  dustu = false,
}: {
  readonly sekme: KapiSekmesi;
  readonly onSekme: (s: KapiSekmesi) => void;
  readonly onBasari: (omurS: number | null) => void;
  readonly dustu?: boolean;
}) {
  return (
    <Tabs value={sekme} onValueChange={(v) => onSekme(v === "kayit" ? "kayit" : "giris")} className="gap-4">
      <TabsList>
        <TabsTrigger value="giris">
          <KeyRound className="size-4" aria-hidden />
          Giriş
        </TabsTrigger>
        <TabsTrigger value="kayit">
          <UserPlus className="size-4" aria-hidden />
          Kayıt
        </TabsTrigger>
      </TabsList>
      <TabsContent value="giris" id="bolum-giris" className="flex scroll-mt-20 flex-col gap-4">
        <div className="space-y-1">
          <h2 className="font-medium text-xl">{dustu ? "Oturumun kapandı" : "Panoya giriş"}</h2>
          {/* "HALT kolu" İÇ BİR ADDI ve bu cümle artık anonim ziyaretçinin gördüğü
              ekranda duruyor (düzeltme-1). Kapının NEDEN var olduğu doğru bir
              gerekçeydi ama iç sözlükle söylenmişti; aynı gerekçe günlük dille
              duruyor, iddiası küçültülmeden. */}
          <p className="text-muted-foreground text-sm">
            {dustu
              ? "Bu sekmede açık bir oturum vardı; süresi doldu ya da sunucuda kapatıldı. Parolayı yeniden gir, kaldığın yerden devam edersin."
              : "Bu pano gerçek bir hesabın durumunu gösteriyor ve alım-satımı durdurma kolunu taşıyor; kapı o yüzden var."}
          </p>
        </div>
        <GirisFormu onBasari={onBasari} />
      </TabsContent>
      <TabsContent value="kayit" id="bolum-kayit" className="scroll-mt-20">
        <KayitFormu />
      </TabsContent>
    </Tabs>
  );
}
