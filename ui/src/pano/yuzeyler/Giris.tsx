"use client";

/* ============================================================================
   GİRİŞ YÜZEYİ — şablonun `auth/v1` + `auth/v2` ekranları, Meridian'ın GERÇEK
   parola kapısına bağlanmış hâli
   ----------------------------------------------------------------------------
   ŞABLONDAN NE GELDİ: bölünmüş panel (solda `bg-primary` marka rayı, sağda form),
   `Field*` alan grameri, tam-genişlik birincil düğme, giriş↔kayıt geçişi.
   Kaynak: `auth/v1/login`, `auth/v1/register`, `auth/v2/layout`, `auth/_components/*`.

   TEK EKRAN DEĞİL, ÜÇ HÂLLİ BİR MAKİNE — ve hâli PANO SEÇMİYOR, `/api/session`
   SÖYLÜYOR (`api.py::api_session`, /api altındaki TEK yetkisiz uç):
     · password_set === false            → KURULUM ekranı (ilk parola)
     · password_set && !authenticated    → GİRİŞ ekranı (+ bağsız Kayıt sekmesi)
     · authenticated === true            → "oturum açık" + çıkış
   Alanlardan biri HİÇ gelmezse (`=== undefined`) hiçbir ekran seçilmez ve neden
   seçilemediği yazılır. `undefined`ı `false` saymak, parolası kurulu bir sisteme
   "ilk parolanı belirle" ekranı göstermek olurdu — 409'a koşan bir yalan.

   NABIZ 15 SANİYE ve bu bir israf değil: kayan oturum middleware'i (api.py
   `KayanOturumMiddleware`) ÇEREZLİ HER isteği tazeleme fırsatı sayar, yani bu
   yoklama panonun geri kalanıyla aynı ritimde hem oturumu ayakta tutar hem de
   düşme anını saniyeler içinde ekrana taşır. Operatörün bildirdiği "arayüz bir
   süre sonra kayboluyor" arızasının teşhis yüzeyi tam olarak burası.

   YÜZEY KABUĞUN İÇİNDE ÇİZİLİYOR (kenar çubuğu + üst bar duruyor): şablonun
   `h-dvh` tam-ekran auth düzeni BİLEREK alınmadı. Bu pano tek bir HTML dosyası
   ve oturum kapısı uygulamanın ÖNÜNDE değil İÇİNDE bir yüzey — kabuğu gizlemek,
   olmayan bir yönlendirme katmanı varmış gibi göstermek olurdu.
   ============================================================================ */
import { Fingerprint, KeyRound, LogOut, UserPlus } from "lucide-react";
import { useEffect, useState } from "react";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Spinner } from "@/components/ui/spinner";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

import { YUZEYLER } from "../alanlar";
import { useRota } from "../rota";
import { NABIZ_MS, useApi } from "../veri";
import { GirisFormu } from "./kimlik/GirisFormu";
import { KapiKunyesi } from "./kimlik/KapiKunyesi";
import { KayitFormu } from "./kimlik/KayitFormu";
import { KurulumFormu } from "./kimlik/KurulumFormu";
import { apiPost, type GonderSonucu } from "./kimlik/gonder";
import { Kapi } from "./kimlik/parcalar";
import type { OturumGovdesi } from "./kimlik/uctipleri";

/* --- MARKA RAYI (şablonun v2 layout'undaki `bg-primary` sütunu) ----------- */

function MarkaRayi({ baslik, altBaslik }: { readonly baslik: string; readonly altBaslik: string }) {
  return (
    <div className="hidden flex-col justify-between bg-primary p-8 text-primary-foreground lg:flex">
      <div className="space-y-1">
        <Fingerprint className="size-9" aria-hidden />
        <h2 className="font-medium text-2xl">{baslik}</h2>
        <p className="text-primary-foreground/80 text-sm">{altBaslik}</p>
      </div>
      {/* ŞABLONUN İKİ SÜTUNLU ALT BLOĞU KORUNDU, METNİ MERİDİAN'IN GERÇEĞİ:
          şablonda "Clone the repo…" yazıyordu; burada operatörün gece yarısı
          ihtiyacı olan iki cümle var — kaç kullanıcı var, parola unutulursa ne olur. */}
      <div className="flex gap-3">
        <div className="flex-1 space-y-1">
          <h3 className="font-medium text-sm">Tek operatör</h3>
          <p className="text-primary-foreground/80 text-xs">
            Kullanıcı tablosu yok; kapı tek bir parola hash'i tutuyor (meridian/auth.py).
          </p>
        </div>
        <Separator orientation="vertical" className="h-auto! bg-primary-foreground/20" />
        <div className="flex-1 space-y-1">
          <h3 className="font-medium text-sm">Parolayı unuttuysan</h3>
          <p className="text-primary-foreground/80 text-xs">
            Panodan sıfırlanmaz. Sunucu kabuğunda: python -m meridian.auth_cli set
          </p>
        </div>
      </div>
    </div>
  );
}

/** Bölünmüş panel kabı — üç hâlin üçü de bunun içinde çiziliyor. */
function Panel({
  marka,
  markaAlt,
  children,
}: {
  readonly marka: string;
  readonly markaAlt: string;
  readonly children: React.ReactNode;
}) {
  return (
    <Card className="gap-0 overflow-hidden p-0">
      <div className="grid lg:grid-cols-[minmax(0,0.85fr)_minmax(0,1fr)]">
        <MarkaRayi baslik={marka} altBaslik={markaAlt} />
        <CardContent className="p-6 sm:p-8">{children}</CardContent>
      </div>
    </Card>
  );
}

/* --- OTURUM AÇIKKEN: durum + çıkış ---------------------------------------- */

function OturumAcik({ onCikis }: { readonly onCikis: () => void }) {
  const [gonderiliyor, setGonderiliyor] = useState(false);
  const [sonuc, setSonuc] = useState<GonderSonucu | null>(null);

  async function cikis() {
    setGonderiliyor(true);
    const s = await apiPost("/api/logout");
    setGonderiliyor(false);
    setSonuc(s);
    // BAŞARISIZ ÇIKIŞTA DA TAZELE: `/api/logout` çerezi siler ve yetki aramaz, ama
    // yanıt gövdesi okunamadıysa (proxy düz metin döndürdü) çerezin silinip
    // silinmediğini yalnız `/api/session`ı yeniden sorarak öğrenebiliriz.
    onCikis();
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="space-y-1">
        <h2 className="font-medium text-xl">Oturum açık</h2>
        <p className="text-muted-foreground text-sm">
          Bu tarayıcının imzalı çerezi geçerli. Çerez kayan ömürlü: pano her istekle onu tazeliyor
          (api.py <code className="text-[11px]">KayanOturumMiddleware</code>).
        </p>
      </div>

      <Button variant="outline" className="w-full" onClick={cikis} disabled={gonderiliyor}>
        {gonderiliyor ? <Spinner /> : <LogOut className="size-4" aria-hidden />}
        {gonderiliyor ? "Çıkılıyor…" : "Çıkış yap"}
      </Button>

      {sonuc && !sonuc.ok ? (
        <Alert variant="destructive">
          <AlertTitle>Çıkış isteği düştü (HTTP {sonuc.kod})</AlertTitle>
          <AlertDescription>
            {sonuc.detay ?? "sunucu gerekçe metni döndürmedi"} — yukarıdaki oturum satırı çerezin gerçekten silinip
            silinmediğini söyler.
          </AlertDescription>
        </Alert>
      ) : null}
    </div>
  );
}

/* --- YÜZEY ---------------------------------------------------------------- */

export function Giris() {
  const { bolum } = useRota();
  // BAŞLIK KAYITTAN OKUNUR, ELLE YAZILMAZ: `alanlar.ts` bu yüzeyin başlığını ve
  // cevapladığı SORUYU tek yerde tutuyor; ikinci kez yazsaydık kayıt değiştiğinde
  // ekran sessizce eski soruyu sormaya devam ederdi.
  const y = YUZEYLER.authentication;
  const oturum = useApi<OturumGovdesi>("/api/session", NABIZ_MS);
  // Oturum ÖMRÜ yalnız bu sekmede giriş yapılırsa ölçülebilir (bkz. KapiKunyesi).
  const [omurS, setOmurS] = useState<number | null>(null);

  // SEKME ROTADAN SEÇİLİR, `defaultValue`dan DEĞİL: `#/dashboard/authentication/kayit`
  // bağı sayfayı açmakla kalmaz, o bölümün DURDUĞU sekmeyi de açar. `defaultValue`
  // yalnız ilk bağlanmada okunur — operatör bu yüzeydeyken kenar çubuğundan öteki
  // bölüme tıklasaydı sekme hiç değişmez, çapa kapalı sekmenin içinde kalır ve bağ
  // sessizce hiçbir şey yapmazdı. (`KanbanYuzey.tsx`teki desenin aynısı, aynı gerekçeyle.)
  const [sekme, setSekme] = useState<"giris" | "kayit">(() => (bolum === "kayit" ? "kayit" : "giris"));
  useEffect(() => {
    if (bolum === "giris" || bolum === "kayit") setSekme(bolum);
  }, [bolum]);

  useEffect(() => {
    if (!bolum) {
      window.scrollTo({ top: 0, behavior: "instant" });
      return;
    }
    // SEKME GEÇİŞİNDEN SONRA kaydır: etkin olmayan `TabsContent` DOM'da olmayabilir,
    // bu yüzden aynı turda `getElementById` boş döner. Bir kare beklemek, sekmenin
    // gövdesi bağlandıktan sonra çapayı bulmayı garantiler.
    const kare = window.requestAnimationFrame(() => {
      document.getElementById(`bolum-${bolum}`)?.scrollIntoView({ behavior: "smooth", block: "start" });
    });
    return () => window.cancelAnimationFrame(kare);
  }, [bolum, sekme]);

  const v = oturum.veri;
  const acik = v?.authenticated === true;

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0">
          <h1 className="flex items-center gap-2 font-semibold text-2xl tracking-tight">
            <Fingerprint className="size-5 shrink-0 text-muted-foreground" aria-hidden />
            {y.baslik}
          </h1>
          <p className="mt-1 text-muted-foreground text-sm">{y.soru}</p>
        </div>
        {/* ROZET YALNIZ ÖLÇÜLEN ALAN VARSA ÇİZİLİR — yokken hiç çizilmez, çünkü
            "kapalı" rozeti ölçülmemiş bir oturumu kapalı ilan etmek olurdu. */}
        {v?.authenticated !== undefined ? (
          <Badge variant={acik ? "secondary" : "outline"} className="shrink-0">
            {acik ? "oturum açık" : "oturum kapalı"}
          </Badge>
        ) : null}
      </div>

      <Kapi durum={oturum} yol="/api/session">
        {(s) => {
          if (s.password_set === undefined || s.authenticated === undefined) {
            // ÜÇÜNCÜ HÂL: uç cevap verdi ama karar alanları YOK. Hiçbir ekran seçilemez.
            return (
              <Alert variant="destructive">
                <AlertTitle>Hangi ekranın gösterileceği ölçülemedi</AlertTitle>
                <AlertDescription>
                  /api/session cevap verdi ama karar alanları gelmedi (password_set:{" "}
                  {String(s.password_set)}, authenticated: {String(s.authenticated)}). Bu alanlar olmadan kurulum ile
                  giriş ekranı arasında seçim yapmak tahmin olurdu.
                </AlertDescription>
              </Alert>
            );
          }

          if (s.password_set === false) {
            return (
              <Panel marka="Meridian" markaAlt="Kapı henüz kurulmadı — ilk parolayı belirle">
                <div className="flex flex-col gap-4">
                  <div className="space-y-1">
                    <h2 className="flex items-center gap-2 font-medium text-xl">
                      <KeyRound className="size-4 text-muted-foreground" aria-hidden />
                      İlk kurulum
                    </h2>
                    <p className="text-muted-foreground text-sm">
                      <code className="text-[11px]">/api/session</code> <code className="text-[11px]">password_set:
                      false</code> döndürdü: bu kurulumda henüz parola YOK ve pano şu an korumasız.
                    </p>
                  </div>
                  <KurulumFormu onBasari={oturum.tazele} />
                </div>
              </Panel>
            );
          }

          if (s.authenticated === true) {
            return (
              <Panel marka="Meridian" markaAlt="Operatör kapısı — oturum açık">
                <OturumAcik
                  onCikis={() => {
                    setOmurS(null); // ölçülen ömür bu oturuma aitti; oturum bitince ölçüm de biter
                    oturum.tazele();
                  }}
                />
              </Panel>
            );
          }

          return (
            <Panel marka="Meridian" markaAlt="Operatör kapısı — giriş bekleniyor">
              <Tabs value={sekme} onValueChange={(v) => setSekme(v === "kayit" ? "kayit" : "giris")} className="gap-4">
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
                    <h2 className="font-medium text-xl">Panoya giriş</h2>
                    <p className="text-muted-foreground text-sm">
                      Bu yüzey bir broker hesabına bakıyor ve HALT kolunu taşıyor; kapı o yüzden var.
                    </p>
                  </div>
                  <GirisFormu
                    onBasari={(omur) => {
                      setOmurS(omur);
                      oturum.tazele();
                    }}
                  />
                </TabsContent>
                <TabsContent value="kayit" id="bolum-kayit" className="scroll-mt-20">
                  <KayitFormu />
                </TabsContent>
              </Tabs>
            </Panel>
          );
        }}
      </Kapi>

      <Kapi durum={oturum} yol="/api/session">
        {(s) => <KapiKunyesi oturum={s} zaman={oturum.zaman} omurS={omurS} />}
      </Kapi>
    </div>
  );
}
