"use client";

/* ============================================================================
   KAYIT EKRANI — ÇİZİLİ AMA BAĞSIZ (2. AŞAMA)
   ----------------------------------------------------------------------------
   Şablonun `auth/_components/register-form.tsx` alanları burada AYNEN duruyor
   (e-posta + parola + tekrar), çünkü çok-kullanıcılı yapı geldiğinde bu ekran
   olduğu yerde bağlanacak. Bugün BAĞLANACAK BİR UÇ YOK: `meridian/api.py` içinde
   kullanıcı OLUŞTURAN tek bir yol bile bulunmuyor — kimlik yüzeyi üç uçtan ibaret
   (`/api/login`, `/api/setup-password`, `/api/logout`) ve `auth.py` TEK bir parola
   hash'i tutuyor; kullanıcı tablosu diye bir şey yok.

   BU YÜZDEN HER ALAN `disabled` VE GÖNDER DÜĞMESİ KAPALI, üstünde nedeni yazılı.
   Çalışır görünen bir kayıt formu, doldurulduğunda hiçbir şey yapmayan bir düğme
   demekti — bu deponun birinci yasasının arayüzdeki hâli: olmayan bir yeteneği
   varmış gibi göstermek, yanlış bir sayı yazmakla aynı şeydir.

   TEK GERÇEK "KAYIT" AKIŞI KURULUM EKRANIDIR (`password_set === false` iken) ve
   o da yeni kullanıcı açmaz, İLK parolayı belirler. Aşağıdaki bağ oraya işaret
   etmiyor çünkü o ekran ancak parola KURULU DEĞİLKEN erişilebilir — bu ekranı
   gören operatörün parolası zaten kurulu.
   ============================================================================ */
import { UserPlus } from "lucide-react";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Field, FieldGroup, FieldLabel } from "@/components/ui/field";
import { Input } from "@/components/ui/input";

const GEREKCE =
  "Yeni kullanıcı açan bir uç YOK: meridian/api.py'de kullanıcı oluşturan hiçbir yol bulunmuyor ve " +
  "meridian/auth.py tek bir parola hash'i tutuyor (kullanıcı tablosu yok). Bu ekran çok-kullanıcılı " +
  "yapının iskeleti; bağlanacağı gün alanlar aynen kalır, düğme açılır.";

export function KayitFormu() {
  return (
    <div className="flex flex-col gap-4">
      <Alert>
        <AlertTitle>Bu ekran 2. aşama — bugün hiçbir yere bağlı değil</AlertTitle>
        <AlertDescription>{GEREKCE}</AlertDescription>
      </Alert>

      {/* `onSubmit` YOK ve bu bilinçli: `preventDefault` yazan boş bir işleyici bile
          "bir şey oluyor" izlenimi verirdi. Form hiçbir olayı dinlemiyor. */}
      <form noValidate aria-disabled className="flex flex-col gap-4 opacity-60">
        <FieldGroup className="gap-4">
          <Field className="gap-1.5">
            <FieldLabel htmlFor="kayit-eposta">E-posta</FieldLabel>
            <Input id="kayit-eposta" type="email" placeholder="ornek@alanadi.com" disabled autoComplete="off" />
          </Field>
          <Field className="gap-1.5">
            <FieldLabel htmlFor="kayit-parola">Parola</FieldLabel>
            <Input id="kayit-parola" type="password" placeholder="••••••••••••" disabled autoComplete="off" />
          </Field>
          <Field className="gap-1.5">
            <FieldLabel htmlFor="kayit-tekrar">Parola (tekrar)</FieldLabel>
            <Input id="kayit-tekrar" type="password" placeholder="••••••••••••" disabled autoComplete="off" />
          </Field>
        </FieldGroup>

        <Button className="w-full" type="button" disabled>
          <UserPlus className="size-4" aria-hidden />
          Kayıt ol — devre dışı
        </Button>
      </form>

      {/* SOSYAL GİRİŞ DÜĞMELERİ (şablonun `social-auth/google-button.tsx`) BİLEREK
          ALINMADI: karşılığı olan bir OAuth akışı yok, ve tıklanınca hiçbir yere
          gitmeyen bir "Google ile devam et" düğmesi kayıt formundan daha yanıltıcı
          olurdu — kimlik sağlayıcı iddiası, olmayan bir güven zinciri iddiasıdır. */}
      <p className="text-muted-foreground text-xs">
        Sosyal giriş düğmeleri (Google vb.) bu panoya alınmadı: karşılık gelen bir OAuth akışı yok.
      </p>
    </div>
  );
}
