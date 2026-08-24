"use client";

/* ============================================================================
   KAPI KÜNYESİ — oturumun ÖLÇÜLEN hâli + kimlik uçlarının sözleşmesi
   ----------------------------------------------------------------------------
   İKİ TABLO, İKİ FARKLI KAYNAK ve ekranda ayrı ayrı beyan ediliyor:

     · ÜSTTEKİ tablo ÖLÇÜMDÜR — `/api/session` gövdesinden gelir. Alanın VARLIĞI
       kontrol ediliyor (`=== undefined`), doğruluğu değil: uç bir alanı hiç
       döndürmezse hücre "ölçülemedi" der, `false` demez. `false` bir cevaptır,
       yokluk değildir.

     · ALTTAKİ tablo SÖZLEŞMEDİR — `meridian/api.py` okunarak yazıldı, çalışma
       anında ölçülmüyor. Bu ayrım tabloların başlığında yazıyor; yazmasaydı
       okuyucu bir kod okumasını bir ölçüm sanardı.

   OTURUM ÖMRÜ ÖZEL BİR KALEM: `/api/session` onu DÖNDÜRMÜYOR. Tek ölçülen kaynak
   `POST /api/login`in başarı gövdesindeki `expires_in` — yani ömür ancak BU
   sekmede giriş yapıldıysa bilinir. `auth.SESSION_TTL_S = 12*3600` sabitinden
   yazmak kolaydı ama yanlış olurdu: çerez KAYAN ömürlü (KayanOturumMiddleware),
   ve sabitten okunan bir sayı "senin oturumun bu kadar sonra düşecek" iddiasını
   ölçmeden yapardı.
   ============================================================================ */
import { ShieldCheck } from "lucide-react";

import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

import { BolumKart, Olculemedi, OkRozet, Satir, sureMetni, zamanMetni } from "./parcalar";
import type { OturumGovdesi } from "./uctipleri";

interface UcSatiri {
  readonly yol: string;
  readonly yontem: string;
  readonly yetki: string;
  readonly is: string;
}

/* `meridian/api.py` OKUNARAK yazıldı (satır numaraları 2026-08-25 checkout'u):
   api_login 1322 · api_logout 1356 · api_session 1367 · api_setup_password 1376. */
const UCLAR: readonly UcSatiri[] = [
  {
    yol: "/api/session",
    yontem: "GET",
    yetki: "açık",
    is: "Panonun açılışta sorduğu tek soru: kurulum mu, giriş mi, uygulama mı. _auth ÇAĞRILMAZ — /api altındaki tek yetkisiz uç.",
  },
  {
    yol: "/api/login",
    yontem: "POST",
    yetki: "açık",
    is: "Gövde {password}. Doğruysa imzalı oturum çerezi + {ok, expires_in}. Hatalıysa 401. 15 dk'da 8 başarısızlıktan sonra IP kilidi → 429.",
  },
  {
    yol: "/api/setup-password",
    yontem: "POST",
    yetki: "açık",
    is: "İLK parolayı kurar (min 12 karakter) ve aynı yanıtta oturum açar. Parola zaten kuruluysa 409 — sıfırlama kapısı DEĞİL.",
  },
  {
    yol: "/api/logout",
    yontem: "POST",
    yetki: "istemez",
    is: "Oturum çerezini siler. Düşmüş bir oturum da kapatılabilsin diye yetki aramaz; sunucu durumuna yazmaz.",
  },
];

export function KapiKunyesi({
  oturum,
  zaman,
  omurS,
}: {
  readonly oturum: OturumGovdesi;
  /** `/api/session`ın son BAŞARILI okunma anı (`veri.ts::Durum.zaman`). */
  readonly zaman: Date | null;
  /** Bu sekmedeki girişin `expires_in`i; giriş yapılmadıysa null (ölçülmedi). */
  readonly omurS: number | null;
}) {
  const omur = sureMetni(omurS);
  return (
    <BolumKart
      kimlik="kapi"
      baslik="Kapının ölçülen hâli"
      soru="Oturum açık mı, parola kurulu mu, çerez güvenli mi?"
      ikon={ShieldCheck}
    >
      <div className="flex flex-col">
        <Satir etiket="oturum">
          <OkRozet
            ok={oturum.authenticated}
            iyi="açık"
            kotu="kapalı"
            neden="/api/session `authenticated` alanını döndürmedi"
          />
        </Satir>
        <Satir etiket="parola kurulu">
          <OkRozet
            ok={oturum.password_set}
            iyi="kurulu"
            kotu="kurulu değil"
            neden="/api/session `password_set` alanını döndürmedi"
          />
        </Satir>
        <Satir etiket="çerez Secure (TLS)">
          <OkRozet
            ok={oturum.tls}
            iyi="Secure işaretli"
            kotu="Secure DEĞİL (düz HTTP)"
            neden="/api/session `tls` alanını döndürmedi"
          />
        </Satir>
        <Satir etiket="oturum ömrü">
          {omur !== null ? (
            <span className="tabular-nums">{omur}</span>
          ) : (
            <Olculemedi neden="/api/session bu alanı döndürmüyor; ömür yalnız bu sekmede giriş yapılırsa /api/login yanıtındaki expires_in'den ölçülür" />
          )}
        </Satir>
        <Satir etiket="son okuma">
          {zaman !== null ? (
            <span className="tabular-nums text-xs">{zamanMetni(zaman.toISOString()) ?? "—"}</span>
          ) : (
            <Olculemedi neden="/api/session henüz bir kez bile başarıyla okunmadı" />
          )}
        </Satir>
      </div>

      <div>
        <p className="mb-2 text-muted-foreground text-xs">
          Aşağıdaki tablo bir ÖLÇÜM DEĞİL, <code className="text-[11px]">meridian/api.py</code> okunarak yazılmış
          sözleşmedir — kapının hangi kodu ne zaman döndürdüğü buradan okunur.
        </p>
        <div className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-[9rem]">Uç</TableHead>
                <TableHead className="w-[5rem]">Yöntem</TableHead>
                <TableHead className="w-[6rem]">Yetki</TableHead>
                <TableHead>Ne yapar</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {UCLAR.map((u) => (
                <TableRow key={u.yol}>
                  <TableCell className="font-mono text-xs">{u.yol}</TableCell>
                  <TableCell className="font-mono text-xs">{u.yontem}</TableCell>
                  <TableCell className="text-xs">{u.yetki}</TableCell>
                  <TableCell className="text-muted-foreground text-xs">{u.is}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </div>
    </BolumKart>
  );
}
