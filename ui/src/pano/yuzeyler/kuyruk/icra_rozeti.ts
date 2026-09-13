/* ============================================================================
   İCRA ROZETİ — onay defteri satırının "ne OLDU" cümlesi (saf mantık)
   ----------------------------------------------------------------------------
   NEDEN AYRI DOSYA VE NEDEN SAF: panonun test koşucusu YOK (ölçüldü: `ui/package.json`
   yalnız `kontrol` ve `build` betikleri taşıyor, vitest/jest bağımlılığı hiç yok).
   Mantık JSX'in içinde kalsaydı hiçbir çivi ona ulaşamazdı; burada React'siz,
   DOM'suz ve yan etkisiz durduğu için TS tip denetimi ve Python metin çivisi
   (`tests/test_pano_icra_rozeti_v474.py`) ikisi birden ısırabiliyor.

   ÇÖZDÜĞÜ ÖLÇÜLMÜŞ YANLIŞ CÜMLE: defter sütunu tek bir alana (`davranissal`)
   bakıyordu ve o alan BAŞKA bir soruyu cevaplıyor — "bu kimliği bir L1+ uygulama
   kapısı okur mu". Sohbet önerisinin kimliğini hiçbir kapı okumaz, yani alan
   HER ZAMAN `false` gelir; sütun da her sohbet satırına "kayıt — icra açmaz"
   yazıyordu. Oysa onaylanan bir `plan_onayi` GERÇEKTEN plan onay yolunu çağırır,
   onaylanan bir `alarm_ack` GERÇEKTEN alarmı kapatır. Defteri yarın okuyan, icra
   etmiş bir kararı "hiçbir şey olmadı" diye okurdu — salt-ekleme bir sicilde bu
   yanlışlık KALICIDIR.

   CÜMLEYİ SUNUCU KURAR, PANO TAŞIR: künye metni (`not`) uçtan geliyor ve rozetin
   `title`ına AYNEN basılıyor. Burada ikinci bir açıklama yazmak, aynı gerçeğin
   iki kopyasını üretmek (ve yarın birinin ayrışması) olurdu.

   DÖRDÜNCÜ DÖNÜŞ BİR HÂL DEĞİL, BİR SUSMADIR: `icra_eder` boolean DEĞİLSE
   (alan hiç yok, ya da JSONL'e başka bir tip düşmüş) fonksiyon `null` döner ve
   karar çağırana kalır — defterde sohbet-dışı satırlar da var (`kayit:`, `arming:`)
   ve onların cümlesi `davranissal`dan kurulur. `null`u "icra yok" saymak, ölçmediği
   bir şeyi beyan etmek olurdu.
   ============================================================================ */
import type { DefterIcraKesiti } from "./onaylar";

/** Rozetin görsel rolü — `Badge` varyant sözlüğünün ALT KÜMESİ, serbest dizge değil. */
export type IcraVaryanti = "secondary" | "destructive" | "outline";

export interface IcraRozeti {
  readonly metin: string;
  readonly varyant: IcraVaryanti;
  /** Uçtan gelen künye; yoksa `null` — UI kendi cümlesini uydurmaz. */
  readonly title: string | null;
}

/* METİNLER TEK KAYNAK: sütunun "icra açmaz" hâli `davranissal` dalında da yazılıyor.
   İki yerde iki literal, yarın birinin düzeltilip ötekinin kalmasıyla biterdi. */
export const ICRA_EDILDI_METNI = "sohbet — icra EDİLDİ";
export const ICRA_DUSTU_METNI = "sohbet — icra DÜŞTÜ";
export const ICRA_ACMAZ_METNI = "kayıt — icra açmaz";
/** İCRA DENENDİ AMA HÜKMÜ OKUNAMADI: `icra_eder=true` iken `icra_ok` boolean gelmedi.
 *  Bu hâli "açmaz"a ya da "EDİLDİ"ye yuvarlamak, ölçülmemiş bir sonucu beyan etmek olurdu. */
export const ICRA_OLCULEMEDI_METNI = "sohbet — icra sonucu ölçülemedi";

/** Ham JSONL satırının okunabilen dilimi. Tip DARALTMASI burada olur: `unknown` alanlar
 *  yalnız GERÇEKTEN beklenen tipteyse geçer, aksi hâlde `undefined` (yani "ölçemedim"). */
function kesitOku(satir: Record<string, unknown>): DefterIcraKesiti {
  const eder = satir["icra_eder"];
  const ok = satir["icra_ok"];
  const kunye = satir["not"];
  return {
    icra_eder: typeof eder === "boolean" ? eder : undefined,
    icra_ok: typeof ok === "boolean" ? ok : undefined,
    not: typeof kunye === "string" && kunye.trim() !== "" ? kunye : undefined,
  };
}

/**
 * Defter satırının İCRA GERÇEĞİNİ rozete çevirir.
 *
 * Dönüş `null` ise satır icra alanları TAŞIMIYOR demektir ve çağıran kendi
 * (`davranissal`) dallanmasına düşer — bu bir "hayır" değil, bir "ölçmedim"dir.
 */
export function icraRozeti(satir: Record<string, unknown>): IcraRozeti | null {
  const { icra_eder, icra_ok, not } = kesitOku(satir);
  if (icra_eder === undefined) return null;
  const title = not ?? null;
  if (icra_eder === false) {
    // RET ya da `not` türü: icra DENENMEDİ. `icra_ok` burada her zaman `false`tur ve
    // TEK BAŞINA okunmaz — "başarısız" diye göstermek düşmüş bir icra iddia ederdi.
    return { metin: ICRA_ACMAZ_METNI, varyant: "outline", title };
  }
  if (icra_ok === true) return { metin: ICRA_EDILDI_METNI, varyant: "secondary", title };
  if (icra_ok === false) return { metin: ICRA_DUSTU_METNI, varyant: "destructive", title };
  return { metin: ICRA_OLCULEMEDI_METNI, varyant: "outline", title };
}
