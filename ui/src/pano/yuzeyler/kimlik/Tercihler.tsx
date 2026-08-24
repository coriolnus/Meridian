"use client";

/* ============================================================================
   ARAYÜZ TERCİHLERİ — `usePreferencesStore` (sunucu değil, TARAYICI durumu)
   ----------------------------------------------------------------------------
   BU BÖLÜM BİR ÖLÇÜM DEĞİL, BİR AYNADIR ve farkı ekranda yazıyor: yukarıdaki iki
   bölüm sunucudan gelen sayıları gösteriyor, burası tarayıcının kendi kayıtlı
   tercihini. Kaynak tek: `<html>` üzerindeki `data-*` nitelikleri. Önyükleyici
   (`pano-onyuk.js`) onları ilk boyamadan ÖNCE çerezden okuyup yazıyor, depo da
   aynı yerden doğuyor (`App.tsx::belgedenTercihler`). İkinci bir kopya tutmak,
   bir tercihin iki farklı yerde iki farklı değeri olması demekti.

   TABLO KAYITTAN ÜRETİLİYOR, ELLE YAZILMIYOR: sütunlar
   `lib/preferences/preferences-config.ts::PREFERENCE_REGISTRY`ten okunuyor —
   izin verilen değerler, saklama biçimi ve DOM niteliği dahil. Kayda yeni bir
   tercih eklendiğinde bu tablo kendiliğinden doğru kalır.

   NEDEN HER SATIR AYRI BİLEŞEN: `setPreference` imzası
   `<K extends PreferenceKey>(k: K, v: PreferenceValueMap[K])` — anahtar ile
   değerin İLİŞKİLİ olmasını istiyor. Tabloyu `PREFERENCE_KEYS.map(...)` ile
   üretseydik anahtar bir BİRLEŞİM tipi olurdu ve TypeScript bu ilişkiyi birleşim
   üstünde taşıyamaz (correlated union); tek çıkış bir `as` kaçamağı olurdu.
   Satırları adlarıyla yazmak o kaçamağı gereksiz kılıyor: her `<TercihSatiri>`
   çağrısında `K` TEK bir anahtardır ve tip zinciri baştan sona sağlam kalır.

   ETİKETLER BİRER ÇEVİRİDİR, VERİ DEĞİL: kayıt yalnız DEĞERLERİ dışa aktarıyor
   (`THEME_MODE_VALUES` gibi); okunabilir adlar yalnız `THEME_PRESET_OPTIONS` ve
   `fontOptions` için var. Bu yüzden aşağıdaki sözlük bir ARAYÜZ METNİDİR ve
   eksik kaldığında ham değer basılır — uydurulmuş bir ad değil.
   ============================================================================ */
import { RotateCcw, SlidersHorizontal } from "lucide-react";
import { useShallow } from "zustand/react/shallow";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { fontOptions } from "@/lib/fonts/registry";
import {
  PREFERENCE_REGISTRY,
  parsePreference,
  type PreferenceKey,
} from "@/lib/preferences/preferences-config";
import { THEME_PRESET_OPTIONS } from "@/lib/preferences/theme";
import { usePreferencesStore } from "@/stores/preferences/preferences-provider";

import { BolumKart, Satir } from "./parcalar";

/** Ham değer → okunabilir ad. Kayıtta ad YOKSA burada var; burada da yoksa ham değer basılır. */
const DEGER_ADI: Readonly<Record<string, string>> = {
  light: "Açık",
  dark: "Koyu",
  system: "Sistem",
  centered: "Ortalanmış",
  "full-width": "Tam genişlik",
  sticky: "Yapışkan",
  scroll: "Kayan",
  sidebar: "Kenar çubuğu",
  inset: "İçe gömülü",
  floating: "Yüzen",
  icon: "İkona daralt",
  offcanvas: "Tümüyle gizle",
  ...Object.fromEntries(THEME_PRESET_OPTIONS.map((o) => [o.value, o.label])),
  ...Object.fromEntries(fontOptions.map((o) => [o.key, o.label])),
};

const SAKLAMA_ADI: Readonly<Record<string, string>> = {
  none: "saklanmaz (yenilemede sıfırlanır)",
  "client-cookie": "tarayıcı çerezi",
  "server-cookie": "sunucu çerezi",
  localStorage: "localStorage",
};

function ad(deger: string): string {
  return DEGER_ADI[deger] ?? deger;
}

/**
 * TEK TERCİH SATIRI. `K` her çağrıda TEK bir anahtardır (bkz. dosya başı) — bu
 * sayede `parsePreference` ve `setPreference` arasındaki tip ilişkisi korunur.
 */
function TercihSatiri<K extends PreferenceKey>({ anahtar, etiket }: { readonly anahtar: K; readonly etiket: string }) {
  const { deger, setPreference } = usePreferencesStore(
    useShallow((s) => ({ deger: s.values[anahtar], setPreference: s.setPreference })),
  );
  const tanim = PREFERENCE_REGISTRY[anahtar];
  const secenekler: readonly string[] = tanim.values;
  const saklama: string = tanim.persistence;
  const nitelik: string = tanim.attribute;

  return (
    <TableRow>
      <TableCell className="font-medium text-sm">{etiket}</TableCell>
      <TableCell>
        <Badge variant="secondary" className="font-normal">
          {ad(deger)}
        </Badge>
      </TableCell>
      <TableCell className="w-[13rem]">
        <Select
          value={deger}
          onValueChange={(v) => {
            // `parsePreference` gelen dizgeyi kaydın İZİN VERDİĞİ kümeye indirger;
            // tanınmayan bir değer sessizce varsayılana düşer (kayıt sözleşmesi).
            setPreference(anahtar, parsePreference(anahtar, v));
          }}
        >
          <SelectTrigger className="w-full" size="sm">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {secenekler.map((s) => (
              <SelectItem key={s} value={s}>
                {ad(s)}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </TableCell>
      <TableCell className="text-muted-foreground text-xs">{SAKLAMA_ADI[saklama] ?? saklama}</TableCell>
      <TableCell className="font-mono text-muted-foreground text-xs">{nitelik}</TableCell>
    </TableRow>
  );
}

export function Tercihler() {
  const { resolvedThemeMode, isSynced, resetPreferences } = usePreferencesStore(
    useShallow((s) => ({
      resolvedThemeMode: s.resolvedThemeMode,
      isSynced: s.isSynced,
      resetPreferences: s.resetPreferences,
    })),
  );

  return (
    <BolumKart
      kimlik="tercihler"
      baslik="Arayüz tercihleri"
      soru="Tema, yüz ve yerleşim nasıl kayıtlı?"
      ikon={SlidersHorizontal}
      aksiyon={
        <Button variant="outline" size="sm" onClick={resetPreferences}>
          <RotateCcw className="size-3.5" aria-hidden />
          Varsayılanlara dön
        </Button>
      }
    >
      <div className="flex flex-col">
        <Satir etiket="fiilen uygulanan tema">
          {/* AYRI BİR SORU: `theme_mode` "system" olabilir; hangi tarafın SEÇİLDİĞİNİ
              yalnız çözümlenmiş değer söyler (medya sorgusu her an değişebilir). */}
          <Badge variant="secondary" className="font-normal">
            {ad(resolvedThemeMode)}
          </Badge>
        </Satir>
        <Satir etiket="depo DOM ile eşitlendi mi">
          <Badge variant={isSynced ? "secondary" : "outline"} className="font-normal">
            {isSynced ? "eşitlendi" : "henüz ilk okuma yapılmadı"}
          </Badge>
        </Satir>
      </div>

      <div className="overflow-x-auto">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Tercih</TableHead>
              <TableHead className="w-[10rem]">Şu anki değer</TableHead>
              <TableHead className="w-[13rem]">Değiştir</TableHead>
              <TableHead className="w-[12rem]">Nerede saklanıyor</TableHead>
              <TableHead className="w-[12rem]">DOM niteliği</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {/* SATIRLAR ADLARIYLA YAZILI — gerekçesi dosya başında (correlated union). */}
            <TercihSatiri anahtar="theme_mode" etiket="Tema modu" />
            <TercihSatiri anahtar="theme_preset" etiket="Tema ön ayarı" />
            <TercihSatiri anahtar="font" etiket="Yazı yüzü" />
            <TercihSatiri anahtar="content_layout" etiket="İçerik yerleşimi" />
            <TercihSatiri anahtar="navbar_style" etiket="Üst bar davranışı" />
            <TercihSatiri anahtar="sidebar_variant" etiket="Kenar çubuğu biçimi" />
            <TercihSatiri anahtar="sidebar_collapsible" etiket="Kenar çubuğu daralması" />
          </TableBody>
        </Table>
      </div>

      <p className="text-muted-foreground text-xs">
        Bu tercihler sunucuya gitmez; çerezde saklanır ve <code className="text-[11px]">&lt;html&gt;</code> üzerindeki{" "}
        <code className="text-[11px]">data-*</code> niteliklerine yazılır. Aynı ayarların kısayolu üst bardaki yerleşim
        düğmesinde ve tema anahtarında da duruyor — tek kaynak aynı depo, iki ayrı kapı.
      </p>
      <p className="text-muted-foreground text-xs">
        Yazı yüzü listesi iki satır çünkü kayıt kendi barındırdığımız kesitlere daralmış
        (<code className="text-[11px]">lib/fonts/registry.ts</code>): canlı CSP{" "}
        <code className="text-[11px]">font-src 'self'</code> ve dış font sunucusu 2026-08-07'de bilerek düşürüldü.
      </p>
    </BolumKart>
  );
}
