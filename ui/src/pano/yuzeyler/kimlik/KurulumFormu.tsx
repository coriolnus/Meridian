"use client";

/* ============================================================================
   KURULUM FORMU — İLK parolayı belirler (`POST /api/setup-password`)
   ----------------------------------------------------------------------------
   BU EKRAN YALNIZ `password_set === false` İKEN ÇİZİLİR ve bu bir görsel tercih
   değil, ucun sözleşmesi: parola kurulduktan sonra aynı uç 409 döner
   (`api.py::api_setup_password`). Yani bu bir "parolayı sıfırla" arka kapısı
   DEĞİLDİR — unutulan parola kabuktan sıfırlanır (`python -m meridian.auth_cli set`).
   Ekranda da böyle yazıyor: operatörün buraya bakıp "sıfırlarım" diye düşünmesi,
   sunucuya erişimi olmadığı bir gecede kaybedilmiş bir saat demek olurdu.

   12 KARAKTER SINIRI UYDURULMADI, OKUNDU: `meridian/auth.py:148`
   `if len(password) < 12: raise ValueError(...)`. İstemcide de sınamamızın tek
   sebebi turu ağa çıkmadan kesmek; SON SÖZ sunucunundur ve 400 gövdesindeki
   metin aynen basılır. İki alanın eşitliği ise TAMAMEN istemci tarafı bir
   kontroldür (sunucu ikinci alanı hiç görmez) ve bu ekranda öyle beyan ediliyor.
   ============================================================================ */
import { Eye, EyeOff, KeyRound } from "lucide-react";
import { useState } from "react";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Field, FieldDescription, FieldError, FieldGroup, FieldLabel } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { Spinner } from "@/components/ui/spinner";

import { apiPost, type GonderSonucu } from "./gonder";

/** `meridian/auth.py:148` — sunucunun dayattığı alt sınır. Burada TEKRARLANIYOR, TÜRETİLMİYOR. */
export const EN_AZ_KARAKTER = 12;

function hataMetni(s: GonderSonucu): { readonly baslik: string; readonly govde: string } {
  if (s.kod === 409) {
    // SIFIRLAMA KOMUTU EKRANDAN KALKTI (düzeltme-1, 2026-09-01): bir yönetim
    // komutu ekran öğesi değildir ve bu ekran artık kimliksiz ziyaretçinin
    // görebildiği kapının içinde. Olgu ("burası sıfırlama kapısı değil") duruyor;
    // yordamın yeri runbook. Komut bu dosyanın BAŞLIK ŞERHİNDE kayıtlı kalıyor —
    // şerh ekran metni değildir ve okuyucusu geliştiricidir.
    return {
      baslik: "Parola zaten kurulu",
      govde:
        (s.detay ?? "sunucu 409 döndü") +
        " · burası bir sıfırlama kapısı değil. Parola unutulduysa sıfırlama yordamı sunucu tarafındadır ve runbook'ta yazılıdır.",
    };
  }
  if (s.kod === 400) {
    return { baslik: "Parola kabul edilmedi", govde: s.detay ?? "sunucu 400 döndü, gerekçe metni gelmedi" };
  }
  if (s.kod === 0) {
    return { baslik: "Sunucuya ulaşılamadı", govde: s.detay ?? "istek yanıtsız kaldı ve tarayıcı bir gerekçe vermedi" };
  }
  return { baslik: `Kurulum reddedildi (HTTP ${s.kod})`, govde: s.detay ?? "sunucu gerekçe metni döndürmedi" };
}

export function KurulumFormu({ onBasari }: { readonly onBasari: () => void }) {
  const [parola, setParola] = useState("");
  const [tekrar, setTekrar] = useState("");
  const [gorunur, setGorunur] = useState(false);
  const [gonderiliyor, setGonderiliyor] = useState(false);
  const [sonuc, setSonuc] = useState<GonderSonucu | null>(null);
  const [denendi, setDenendi] = useState(false);

  const kisa = parola.length > 0 && parola.length < EN_AZ_KARAKTER;
  const uyusmuyor = tekrar.length > 0 && tekrar !== parola;
  const gonderilebilir = parola.length >= EN_AZ_KARAKTER && tekrar === parola;

  async function gonder(e: React.FormEvent) {
    e.preventDefault();
    setDenendi(true);
    if (!gonderilebilir) return;
    setGonderiliyor(true);
    const s = await apiPost("/api/setup-password", { password: parola });
    setGonderiliyor(false);
    setSonuc(s);
    if (s.ok) {
      setParola("");
      setTekrar("");
      // KURULUM ANINDA OTURUM AÇILIR: uç yanıtında `set-cookie` var
      // (`api.py::api_setup_password`), yani ayrıca giriş yapmak gerekmiyor.
      // Yüzeyin `/api/session`ı yeniden okuması bunu ekranda doğrular.
      onBasari();
    }
  }

  const hata = sonuc && !sonuc.ok ? hataMetni(sonuc) : null;

  return (
    <form noValidate onSubmit={gonder} className="flex flex-col gap-4">
      <FieldGroup className="gap-4">
        <Field className="gap-1.5" data-invalid={kisa || (denendi && parola.length === 0)}>
          <FieldLabel htmlFor="kurulum-parola">İlk operatör parolası</FieldLabel>
          <div className="relative">
            <Input
              id="kurulum-parola"
              type={gorunur ? "text" : "password"}
              value={parola}
              onChange={(ev) => setParola(ev.target.value)}
              placeholder="en az 12 karakter"
              autoComplete="new-password"
              aria-invalid={kisa}
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
          {/* KAYNAK ÇAPASI EKRANDAN KALKTI (düzeltme-1): `meridian/auth.py:148`
              hem bir dosya yolu hem bir SATIR çapasıydı — ikisi de kimliksiz
              ziyaretçinin ekranında işi olmayan şeyler. Kuralın KENDİSİ ve
              GEREKÇESİ duruyor; nereden geldiği `EN_AZ_KARAKTER` şerhinde. */}
          {kisa ? (
            <FieldError>
              {parola.length}/{EN_AZ_KARAKTER} karakter. Sunucu en az {EN_AZ_KARAKTER} karakter istiyor: bu pano gerçek
              bir hesabın durumunu gösteriyor.
            </FieldError>
          ) : null}
          {denendi && parola.length === 0 ? <FieldError>Parola boş — istek gönderilmedi.</FieldError> : null}
        </Field>

        <Field className="gap-1.5" data-invalid={uyusmuyor}>
          <FieldLabel htmlFor="kurulum-tekrar">Parola (tekrar)</FieldLabel>
          <Input
            id="kurulum-tekrar"
            type={gorunur ? "text" : "password"}
            value={tekrar}
            onChange={(ev) => setTekrar(ev.target.value)}
            placeholder="aynısı"
            autoComplete="new-password"
            aria-invalid={uyusmuyor}
            disabled={gonderiliyor}
          />
          {uyusmuyor ? <FieldError>İki alan aynı değil.</FieldError> : null}
          <FieldDescription>
            Bu ikinci alan YALNIZ tarayıcıda karşılaştırılır: sunucuya tek bir parola gidiyor, ikinci alanı hiç görmüyor.
          </FieldDescription>
        </Field>
      </FieldGroup>

      <Button className="w-full" type="submit" disabled={gonderiliyor}>
        {gonderiliyor ? <Spinner /> : <KeyRound className="size-4" aria-hidden />}
        {gonderiliyor ? "Kuruluyor…" : "Parolayı kur ve gir"}
      </Button>

      {hata ? (
        <Alert variant="destructive">
          <AlertTitle>{hata.baslik}</AlertTitle>
          <AlertDescription>{hata.govde}</AlertDescription>
        </Alert>
      ) : null}
    </form>
  );
}
