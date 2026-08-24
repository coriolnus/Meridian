"use client";

/* ============================================================================
   GİRİŞ FORMU — şablonun `auth/_components/login-form.tsx` gramerine, Meridian
   kapısının GERÇEK sözleşmesiyle bağlanmış hâli
   ----------------------------------------------------------------------------
   ŞABLONDAN NE ALINDI: alan dizilimi (`FieldGroup`/`Field`/`FieldLabel`/`Input`/
   `FieldError`), tam-genişlik birincil düğme, `noValidate` + kendi hata metnimiz.

   ŞABLONDAN NE ALINMADI ve NEDEN — üçü de ölçülmüş sapma:
     1. E-POSTA ALANI YOK. `api.py::api_login` YALNIZ `{"password": ...}` okuyor
        (satır 1339); kullanıcı tablosu diye bir şey yok. Bir e-posta kutusu
        çizmek, doldurulunca hiçbir yere gitmeyen bir alan olurdu.
     2. `zod` + `react-hook-form` KOŞUMU YOK. Bu depoda ikisinin de HİÇ çağrıldığı
        yer yok (`grep react-hook-form src` → 0 satır) ve tek alanlık bir formda
        çözümleyici zinciri, kazandırdığından çok tip yüzeyi getirirdi. Kural aynı
        kalıyor, sahibi değişiyor: doğrulama aşağıda ve GEREKÇESİ yazılı.
     3. "BENİ HATIRLA" KUTUSU YOK. Çerezin ömrü sunucuda sabit (`auth.SESSION_TTL_S`)
        ve istemci onu uzatamaz; kutuyu koymak, hiçbir şeye bağlı olmayan bir anahtar
        göstermek olurdu.

   PAROLA UZUNLUĞU BURADA SINANMAZ (kurulumdan farklı olarak): mevcut parola ne
   uzunluktaysa odur, ve 12 karakter kuralı `set_password` yolunda — girişte değil.
   İstemcide bir alt sınır dayatmak, kural değişirse operatörü KENDİ parolasıyla
   dışarıda bırakırdı. Tek istemci kontrolü "boş gönderme" (ağı boşuna yormamak).
   ============================================================================ */
import { Eye, EyeOff, LogIn } from "lucide-react";
import { useState } from "react";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Field, FieldDescription, FieldError, FieldGroup, FieldLabel } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { Spinner } from "@/components/ui/spinner";

import { apiPost, type GonderSonucu } from "./gonder";
import type { GirisBasarisi } from "./uctipleri";

/** `meridian/auth.py:80` — pencerede bu kadar başarısızlıktan sonra IP kilitlenir. */
const KILIT_ESIGI = 8;
/** `meridian/auth.py:79` — kayan pencere, saniye. */
const KILIT_PENCERESI_S = 900;

function hataMetni(s: GonderSonucu): { readonly baslik: string; readonly govde: string } {
  // HER KOD AYRI BİR ÇARE: yanlış parola → tekrar dene · kilit → bekle ·
  // ağ → sunucuya bak. Üçünü tek "giriş başarısız" cümlesine ezmek, operatörü
  // yanlış işi yapmaya gönderirdi.
  if (s.kod === 401) {
    return { baslik: "Parola hatalı", govde: s.detay ?? "sunucu 401 döndü, gerekçe metni gelmedi" };
  }
  if (s.kod === 429) {
    return {
      baslik: "Kaba-kuvvet kilidi devrede",
      govde:
        (s.detay ?? "sunucu 429 döndü, bekleme süresi metni gelmedi") +
        ` · kural: ${KILIT_PENCERESI_S / 60} dk içinde ${KILIT_ESIGI} başarısız deneme (meridian/auth.py FAIL_MAX/FAIL_WINDOW_S)`,
    };
  }
  if (s.kod === 0) {
    return { baslik: "Sunucuya ulaşılamadı", govde: s.detay ?? "istek yanıtsız kaldı ve tarayıcı bir gerekçe vermedi" };
  }
  return { baslik: `Giriş reddedildi (HTTP ${s.kod})`, govde: s.detay ?? "sunucu gerekçe metni döndürmedi" };
}

export function GirisFormu({ onBasari }: { readonly onBasari: (omurS: number | null) => void }) {
  const [parola, setParola] = useState("");
  const [gorunur, setGorunur] = useState(false);
  const [gonderiliyor, setGonderiliyor] = useState(false);
  const [sonuc, setSonuc] = useState<GonderSonucu | null>(null);
  const [bosUyari, setBosUyari] = useState(false);
  // BU SEKMEDE sayılan başarısızlık. Sunucunun defteri IP BAŞINA ve SÜREÇ-İÇİ
  // (`auth._FAILS`), yani bu sayaç yalnız bir ALT SINIRDIR — başka sekme, başka
  // cihaz ya da sunucu yeniden başlatması onu ölçemez. Ekranda böyle yazıyor.
  const [sekmeDeneme, setSekmeDeneme] = useState(0);

  async function gonder(e: React.FormEvent) {
    e.preventDefault();
    if (parola === "") {
      setBosUyari(true);
      return;
    }
    setBosUyari(false);
    setGonderiliyor(true);
    const s = await apiPost("/api/login", { password: parola });
    setGonderiliyor(false);
    setSonuc(s);
    if (s.ok) {
      setParola("");
      setSekmeDeneme(0);
      const g = s.govde as GirisBasarisi | null;
      const omur = typeof g?.expires_in === "number" ? g.expires_in : null;
      onBasari(omur);
      return;
    }
    if (s.kod === 401) setSekmeDeneme((n) => n + 1);
  }

  const hata = sonuc && !sonuc.ok ? hataMetni(sonuc) : null;

  return (
    <form noValidate onSubmit={gonder} className="flex flex-col gap-4">
      <FieldGroup className="gap-4">
        <Field className="gap-1.5" data-invalid={bosUyari}>
          <FieldLabel htmlFor="giris-parola">Operatör parolası</FieldLabel>
          <div className="relative">
            <Input
              id="giris-parola"
              type={gorunur ? "text" : "password"}
              value={parola}
              onChange={(ev) => setParola(ev.target.value)}
              placeholder="••••••••••••"
              autoComplete="current-password"
              aria-invalid={bosUyari}
              disabled={gonderiliyor}
              className="pr-10"
            />
            <button
              type="button"
              onClick={() => setGorunur((v) => !v)}
              className="absolute inset-y-0 right-0 flex w-10 items-center justify-center text-muted-foreground hover:text-foreground"
              aria-label={gorunur ? "Parolayı gizle" : "Parolayı göster"}
              tabIndex={-1}
            >
              {gorunur ? <EyeOff className="size-4" aria-hidden /> : <Eye className="size-4" aria-hidden />}
            </button>
          </div>
          {bosUyari ? <FieldError>Parola boş — istek gönderilmedi.</FieldError> : null}
          <FieldDescription>
            Tek alan, çünkü kapı tek soru soruyor: <code className="text-[11px]">POST /api/login</code> yalnız{" "}
            <code className="text-[11px]">{"{password}"}</code> okuyor. Kullanıcı adı/e-posta diye bir kayıt yok.
          </FieldDescription>
        </Field>
      </FieldGroup>

      <Button className="w-full" type="submit" disabled={gonderiliyor}>
        {gonderiliyor ? <Spinner /> : <LogIn className="size-4" aria-hidden />}
        {gonderiliyor ? "Doğrulanıyor…" : "Giriş"}
      </Button>

      {hata ? (
        <Alert variant="destructive">
          <AlertTitle>{hata.baslik}</AlertTitle>
          <AlertDescription>{hata.govde}</AlertDescription>
        </Alert>
      ) : null}

      {sekmeDeneme > 0 ? (
        <p className="text-muted-foreground text-xs">
          Bu sekmede sayılan başarısız deneme: <span className="tabular-nums">{sekmeDeneme}</span>. Sunucunun defteri IP
          başınadır ve süreç-içi tutulur (<code className="text-[11px]">auth._FAILS</code>) — bu sayaç kilide ne kadar
          kaldığını DEĞİL, yalnız bir alt sınırı gösterir.
        </p>
      ) : null}
    </form>
  );
}
