"use client";

/* ============================================================================
   HAFIZA · MERİDİAN DERSLERİ — dokuzuncu görünümün GÖVDESİ
   ----------------------------------------------------------------------------
   TSK-118 (2026-09-03, operatör K8: "dokuzuncu nav durağı aç"). Bu dosya
   `MeridianDersleri.tsx`nin GÖVDE SARMALAYICISIDIR — bileşenin kendisi TAŞINMADI
   (import yolu aynı, dosya yerinde duruyor; kendi başlığı gerekçeyi taşıyor),
   yalnız ÇAĞRILDIĞI YER değişti: TSK-118 öncesi Bilgi Tabanı görünümünün üçüncü
   SEKMESİYDİ (`?sekme=dersler`, `BilgiTabani.tsx`); artık kendi bölüm kimliği
   (`hafiza-dersler`, `alanlar.ts::YUZEYLER.memory.bolumler`) ve kendi ekran
   çapası (`bolum-hafiza-dersler`, v288 paritesi) var.

   NEDEN AYRI DOSYA: kardeşleri (`Bellekler.tsx`, `Varliklar.tsx`, `Reflect.tsx`,
   `BilgiTabani.tsx` …) hepsi aynı kalıbı taşıyor — görünüm gövdesi `kayit`i (ve
   gerektiğinde `bank`i) alır, içeriği `BolumKart` ile sarar (başlık/soru/ikon
   kayıttan, TEK kaynak). `MeridianDersleri` bu imzayı taşımıyor: bankadan
   bağımsız tek bir sabit uçtan (`/api/memory`) okuyan, kendi kendine yeten bir
   bileşen — eskiden `<Bolme>` içinde çiziliyordu. Onu bu imzaya UYDURMAK yerine
   kalıbı burada tekrarlamak, bileşenin kendi davranışını bozmadan `HafizaYuzey.
   tsx::GOVDELER` tablosunun tek tipini (`GorunumOzellikleri`) korudu.

   TAŞI, ÇOĞALTMA (TSK-124 dersi): `BilgiTabani.tsx` artık `MeridianDersleri`yi
   HİÇ içe aktarmıyor — aynı içerik iki yerden erişilebilir olsaydı biri bayatlar
   (kopya risk, bu deponun tek-kaynak yasası). Bu dosya TEK çağıran.
   ============================================================================ */
import { BolumKart } from "../sistem/parcalar";
import type { Bolum } from "../../alanlar";

import { MeridianDersleri } from "./MeridianDersleri";

export function Dersler({ kayit }: { readonly kayit: Bolum }) {
  return (
    <BolumKart kimlik="hafiza-dersler" baslik={kayit.baslik} soru={kayit.soru} ikon={kayit.ikon}>
      <MeridianDersleri />
    </BolumKart>
  );
}
