"use client";

/* ============================================================================
   HAFIZA · HENÜZ ÇİZİLMEMİŞ GÖRÜNÜMLER — beş durak, dürüst boş hâl
   ----------------------------------------------------------------------------
   KENAR ÇUBUĞU SEKİZ DURAK GÖSTERİYOR VE ÜÇÜ DOLU. Kalan beşi GİZLEMİYORUZ:
   gizlemek, bilgi mimarisinin yarısını operatörden saklamak olurdu ve o zaman
   "bu yüzey bunu yapamıyor" ile "bu yüzey bunu henüz çizmiyor" ayrımı ekrandan
   okunamazdı. İkisi çok farklı iki cümle ve ikincisi doğru olan.

   "ÖLÇÜLEMEDİ" DEĞİL, "ÇİZİLMEDİ" — VE AYRIM BİLEREK: bu sayfalarda bir ölçüm
   denenip düşmüyor. Sunucu tarafı HAZIR (uçlar açık ve çivili), eksik olan
   yalnız çizim. Buraya `Olculemedi` koymak, çalışan bir ölçümü arızalı gibi
   gösterirdi — uydurma yasağının ters yönü.

   HER PANEL ÜÇ ŞEY SÖYLER: (1) burada ne olacak, (2) veriyi hangi okuma
   yüzeyleri besleyecek — yani iş gerçekten hazır mı, (3) o görünümün taşıdığı
   YAZMA düğmelerinin durumu. Üçüncüsü olmasaydı panel "yakında" diyen boş bir
   vaat olurdu.
   ============================================================================ */
import { Construction } from "lucide-react";

import { Badge } from "@/components/ui/badge";

import type { Bolum } from "../../alanlar";
import { BolumKart } from "../sistem/parcalar";
import { FAZ2_ROZET } from "./parcalar";

function Yakinda({
  kimlik,
  kayit,
  ne,
  hazir,
  yazma,
  ek,
}: {
  readonly kimlik: string;
  readonly kayit: Bolum;
  /** Bu görünüm neyi gösterecek — üst yüzeyin kendi bileşeninden okundu. */
  readonly ne: readonly string[];
  /** Veriyi besleyecek okuma yüzeyleri — hepsi bugün açık ve çivili. */
  readonly hazir: readonly string[];
  /** Bu görünümün taşıdığı yazma düğmeleri; boş dizi = yazma düğmesi yok. */
  readonly yazma: readonly string[];
  /** Bu görünüme özgü ek beyan — varsa kapsamın bedelini yazar. */
  readonly ek?: string;
}) {
  return (
    <BolumKart kimlik={kimlik} baslik={kayit.baslik} soru={kayit.soru} ikon={kayit.ikon}>
      <div className="flex items-center gap-2">
        <Construction className="size-4 shrink-0 text-muted-foreground" aria-hidden />
        <span className="text-sm">Bu görünüm henüz çizilmedi — okuma yüzeyi hazır, ekranı sıradaki turda geliyor</span>
      </div>

      <div className="flex flex-col gap-2">
        <h4 className="font-medium text-muted-foreground text-xs uppercase tracking-wide">Burada ne olacak</h4>
        <ul className="ml-4 list-disc text-sm leading-6">
          {ne.map((m) => (
            <li key={m}>{m}</li>
          ))}
        </ul>
      </div>

      <div className="flex flex-col gap-2">
        <h4 className="font-medium text-muted-foreground text-xs uppercase tracking-wide">Veriyi besleyecek okumalar</h4>
        <div className="flex flex-wrap gap-1.5">
          {hazir.map((u) => (
            <Badge key={u} variant="outline" className="font-normal text-[11px]">
              {u}
            </Badge>
          ))}
        </div>
        <p className="text-muted-foreground text-xs">
          Bunlar bugün açık ve sınanmış okumalar — yani bu panelin boş olması bir arıza değil, bir
          sıra kararı
        </p>
      </div>

      <div className="flex flex-col gap-2">
        <h4 className="font-medium text-muted-foreground text-xs uppercase tracking-wide">Bu görünümdeki yazma düğmeleri</h4>
        {yazma.length === 0 ? (
          <p className="text-muted-foreground text-sm">Bu görünümde yazan bir düğme yok — hepsi okuma</p>
        ) : (
          <>
            <ul className="ml-4 list-disc text-sm leading-6">
              {yazma.map((y) => (
                <li key={y}>{y}</li>
              ))}
            </ul>
            <Badge variant="outline" className="w-fit font-normal text-[11px] text-muted-foreground">
              {FAZ2_ROZET}
            </Badge>
          </>
        )}
      </div>

      {ek ? <p className="rounded-md border border-dashed p-3 text-muted-foreground text-xs">{ek}</p> : null}
    </BolumKart>
  );
}

/* --------------------------------------------------------------------------
   BEŞ GÖRÜNÜM — her biri KENDİ çapasını taşır.
   Tek bir bileşene kimliği dışarıdan geçirmek daha kısa olurdu ama o zaman beş
   çapa kimliğinin hiçbiri kaynakta LİTERAL olarak geçmezdi; kayıt ↔ ekran
   parite çivisi (v288) onları "çapası yok" diye bildirirdi ve haklı olurdu:
   derin bağ gerçekten hiçbir yere gitmezdi.
   -------------------------------------------------------------------------- */

export function BilgiTabani({ kayit }: { readonly kayit: Bolum }) {
  return (
    <Yakinda
      kimlik="hafiza-bilgi"
      kayit={kayit}
      ne={[
        "Klasör ve sayfa ağacı — bankanın kendi bilgi tabanının içindekiler listesi",
        "Sayfa görüntüleyici: seçilen sayfanın metni ve tazelik künyesi",
        "Sayfa içi arama; boş sorgu üst servise hiç gitmez ve ekran bunu 'arama yapılmadı' diye yazar",
      ]}
      hazir={["bilgi ağacı", "bilgi araması", "tek sayfa"]}
      yazma={["Sayfa oluştur / düzenle / sil"]}
    />
  );
}

export function Recall({ kayit }: { readonly kayit: Bolum }) {
  return (
    <Yakinda
      kimlik="hafiza-recall"
      kayit={kayit}
      ne={[
        "Soru kutusu: bankaya bir sorgu sorulur ve dönen kayıtlar sıralı gösterilir",
        "Sorgu ayarları — tür süzgeci, etiketler, zaman penceresi, yanıt bütçesi",
        "Dönen her kaydın hangi belgeden geldiği ve neden seçildiği",
      ]}
      hazir={["sorgu (yazma değil, arama)"]}
      yazma={[]}
      ek="Bu görünümün okuması bir istisnadır ve beyanlıdır: sorgu gövdesi bir bağlantı adresine sığmadığı için gönderi yöntemiyle yapılır, ama durum DEĞİŞTİRMEZ — istek gövdesi beyaz listeyle süzülüyor ve yazan hiçbir alan geçmiyor."
    />
  );
}

export function Reflect({ kayit }: { readonly kayit: Bolum }) {
  return (
    <Yakinda
      kimlik="hafiza-reflect"
      kayit={kayit}
      ne={[
        "Bankanın kendi çıkarım belgeleri: listesi, içerikleri ve tazelik durumu",
        "Bir çıkarımın tarihçesi — hangi tazelemede ne değişti",
        "Gözlemler ve gözlem kapsamları (hangi etiket kümesinden hangi çıkarım doğdu)",
        "Sonraki tazeleme zamanı — Ana Sayfa'da ölçülemeyen değer BURADA yaşıyor",
      ]}
      hazir={["çıkarım listesi", "tek çıkarım", "çıkarım tarihçesi", "gözlemler", "gözlem kapsamları"]}
      yazma={["Şimdi tazele", "Birleştirmeyi tetikle", "Düşen birleştirmeyi kurtar"]}
    />
  );
}

export function Varliklar({ kayit }: { readonly kayit: Bolum }) {
  return (
    <Yakinda
      kimlik="hafiza-varliklar"
      kayit={kayit}
      ne={[
        "Kayıtlarda geçen isimlerin listesi: kaç kez anıldı, ilk ve son ne zaman görüldü",
        "İsimler arası bağ haritası — hangi isim hangisiyle birlikte geçiyor",
        "Bir isme tıklayınca o ismin geçtiği kayıtlara süzme",
      ]}
      hazir={["varlık listesi", "varlık grafı"]}
      yazma={[]}
      ek="Bağ haritasının çizimi taşınmıyor, verisi taşınıyor: birebirleştirme düzen ve bilgi düzeyindedir, piksel düzeyinde değil."
    />
  );
}

export function Yapilandirma({ kayit }: { readonly kayit: Bolum }) {
  return (
    <Yakinda
      kimlik="hafiza-yapilandirma"
      kayit={kayit}
      ne={[
        "Bankanın ayarları — okuma yüzeyi: hangi model, hangi eşik, hangi görev tanımı",
        "Arka planda koşan işler: hangisi bekliyor, hangisi düştü",
        "Model çağrısı kayıtları ve kullanım sayaçları",
        "Denetim kaydı: bankaya ne işlendi, hangi yoldan geldi",
      ]}
      hazir={["banka ayarları", "işler", "model çağrıları", "çağrı sayaçları", "denetim kaydı", "denetim sayaçları"]}
      yazma={["Ayarları değiştir", "İşi iptal et / yeniden dene"]}
      ek="BEDEL BEYANI: bu sayfanın önceki sürümü iki sayaç kutusunu ÇİZİYORDU — banka başına denetim sayaçları ve model çağrısı sayaçları. Yeni bilgi mimarisinde ikisinin de evi burasıdır ve bu turda çizilmediler. Kaybedilen ölçüm değil çizim: veriler vekilin toplu okumasında hâlâ geliyor, sıradaki tur onları bu sayfaya koyacak. VE EKSİK YARISI, AÇIKÇA: o iki gövde şu an panoda HİÇ OKUNMUYOR — yani otuz saniyede bir, banka başına iki üst-servis çağrısı okuru olmadan yapılıyor. Bu körlük değil israftır ve nereden kesileceği bu turun dosya sahipliğinin dışındadır (`api.py` hafıza vekili); sıradaki tur ya okuru geri koyar ya da çağrıyı keser."
    />
  );
}
