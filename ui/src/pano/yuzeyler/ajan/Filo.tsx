"use client";

/* ============================================================================
   FİLO — üç bot + ana hermes beyni, GERÇEK defterlerinden (2026-08-31)
   ----------------------------------------------------------------------------
   BU MODÜL `GET /api/ajanlar`IN TAMAMINI ÇİZER — tek uç, tek modül. Yandaki
   #öneri-hattı kanalı hipotez defterini (`state/hypotheses.jsonl`) sohbet
   grameriyle okutuyor: orada konuşan taraf öneri üretecidir. Burada konuşan
   taraf AJANLARIN KENDİSİdir — `~/.hermes/profiles/<ad>/state.db` ve
   `~/.hermes/state.db` defterleri, yani @sef · @bekci · @karne botlarının ve
   ana beynin gerçek oturumları.

   ÜÇ HÜKÜM ÜÇ AYRI YERDE DURUR ve bu modül onları KARIŞTIRMAZ (ucun sözleşmesi):
     · `ok`/`hata`      — LİSTE hakkında: roster ve olay defteri okunabildi mi.
                          `HukumSeridi` bunu sol sütunun ÜSTÜNDE ince şerit
                          olarak çizer; ⓘ'ye GİRMEZ, çünkü hüküm bir ayrıntı
                          değildir (ruling 2026-08-31).
     · ajan `durum`     — YALNIZ o ajanın OTURUM kaynağı hakkında.
     · `teslimler`      — AYRI bir kaynak (`state/events.jsonl`); oturumları
                          ölçülemeyen bir ajanın teslimleri ölçülmüş OLABİLİR ve
                          bu modül onu o hâlde de çizer (Teslimler sekmesi).

   `durum: olculemedi` BİR BOŞ DURUM DEĞİLDİR. Boş bir ekran "bu ajanla iletişim
   yok" diye okunur — bir İDDİA. Ölçülemeyen ajan bu yüzden nedeniyle birlikte,
   uyarı kabında çizilir; boş-durum grafiğiyle DEĞİL.

   ULTRA GEÇİŞİ GÖRÜNÜR AMA ARTIK TEKRAR ETMİYOR (maket): model DEĞİŞTİĞİ yerde
   tek amber çip çıkar, güncel model başlıkta durur. Eski kabukta her oturum
   satırı kendi rozetini taşıyordu ve aynı ad on kez tekrar edince değişimin
   kendisi gürültünün içinde kayboluyordu. Kıyasın kendisi `gramer.ts`te ve
   TERSLEME BEYANLI: uç `oturumlar`ı yeniden→eskiye gönderiyor, ekran
   eskiden→yeniye okuyor, kıyas yeni sıraya göre düzeltildi.

   SOHBET HÂLÂ TEK YÖNLÜ: bu uç SALT OKUNUR. Yazma/gönderme dalga-B'nin işi
   (`SohbetHatti::YazmaSeridi`).
   ============================================================================ */
import { Inbox, Package, Radio, TriangleAlert } from "lucide-react";

import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Bubble, BubbleContent, BubbleGroup } from "@/components/ui/bubble";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { Marker, MarkerContent } from "@/components/ui/marker";
import { Message, MessageAvatar, MessageContent, MessageFooter, MessageHeader } from "@/components/ui/message";
import { Separator } from "@/components/ui/separator";

import type { Durum } from "../../veri";
import { Kapi, Olculemedi, OlculemediBlok, bicimSayi, gunMetni, saatMetni, zamanMetni } from "./ortak";
import { ROL_ETIKET, botAkisi, mesajYani, type AkisOgesi, type Muhatap, type SekmeAdi } from "./gramer";
import { ajanListesiNedeni, type FiloAjani, type FiloMesaji, type FiloTeslimi, type FiloYuku } from "./filoOku";

/* ---- LİSTE HÜKMÜ --------------------------------------------------------- */

export function HukumSeridi({ yuk }: { yuk: FiloYuku }) {
  // `ok === false` LİSTE hakkındadır, tek bir ajan hakkında değil — ucun kendi
  // ayrımı. Bunu ajan panellerinin içine karıştırmak, bir profilin okunamamasını
  // "tüm liste okunamadı" diye gösterirdi.
  if (yuk.ok === true) return null;
  return (
    <div className="flex items-start gap-2 border-uyari-h border-b bg-uyari-t px-3 py-2">
      <TriangleAlert className="mt-0.5 size-3.5 shrink-0 text-uyari" aria-hidden />
      <div className="min-w-0">
        <p className="font-medium text-xs">
          {yuk.ok === null ? "Liste hükmü ölçülemedi" : "Ajan listesi eksik ölçüldü"}
        </p>
        <p className="mt-0.5 break-words text-[11px] text-muted-foreground leading-relaxed">
          {yuk.hata ??
            "Uç `ok: false` dedi ama `hata` alanı boş geldi — hangi kaynağın düştüğü söylenmemiş."}
        </p>
      </div>
    </div>
  );
}

/** `ajanlar` hiç dizi değilse sol listede duracak cümle. İKİ HÜKÜM DE TAŞINIR
 *  (`filoOku.ts::ajanListesiNedeni`): şeklin tanınmadığı BİZİM hükmümüz, `hata`
 *  UCUN hükmü — biri ötekinin yerine geçmez. */
export function ListeYok({ yuk }: { yuk: FiloYuku }) {
  return (
    <p className="px-3 py-2 text-[11px] leading-relaxed">
      <Olculemedi
        neden="Ajan listesi okunamadı"
        teknik={ajanListesiNedeni(yuk)}
      />
    </p>
  );
}

/* ---- ⓘ KÜNYESİ: HANGİ DEFTERLER OKUNDU ----------------------------------- */

function Satir({
  etiket,
  deger,
  neden,
  teknik,
}: { etiket: string; deger: string | null; neden: string; teknik?: string }) {
  return (
    <div className="flex flex-wrap items-baseline gap-x-2">
      <span className="w-24 shrink-0 text-muted-foreground">{etiket}</span>
      {deger === null ? (
        <Olculemedi neden={neden} teknik={teknik} />
      ) : (
        <code className="min-w-0 break-all font-mono text-[11px]">{deger}</code>
      )}
    </div>
  );
}

/** ⓘ POPOVER'IN İÇİ. Okunan yollar, pencere, tavan ve süzgeç birer AYRINTIdır:
 *  operatör onları ancak "bu sayı nereden geldi" diye sorduğunda arar. Ekranın
 *  en pahalı yerini sürekli işgal etmeleri asıl konuşmayı aşağı itiyordu.
 *  BEDEL: bir tık uzaklaştılar — kaybolmadılar, ve kaybolmamaları şart, çünkü
 *  kırpma beyanları (pencere tavanı, teslim tavanı) burada duruyor. */
export function KaynakOzeti({ yuk }: { yuk: FiloYuku }) {
  const k = yuk.kaynak;
  const s = yuk.suzgec;
  if (k === null) {
    return (
      <OlculemediBlok
        baslik="Kaynak künyesi yok"
        neden="Uç hangi defterleri okuduğunu söylemedi"
        teknik="gövdede `kaynak` alanı bir nesne değil"
      />
    );
  }
  const kirpildi = s !== null && s.limit !== null && s.limitIstenen !== null && s.limitIstenen > s.limit;
  return (
    <div className="flex flex-col gap-2 text-xs">
      <p className="text-[11px] text-muted-foreground leading-relaxed">
        Üç kaynak, üç ayrı hüküm: bot listesi (dizin) · konuşma defterleri (yalnız okunur) · teslim
        olayları. Biri düşerse ötekiler ölçülmeye devam eder.
      </p>
      <Satir etiket="bot kökü" deger={k.botKoku} neden="kaydedilmemiş" teknik="`kaynak.bot_koku` yükte yok" />
      <Satir etiket="profil kökü" deger={k.profilKoku} neden="kaydedilmemiş" teknik="`kaynak.profil_koku` yükte yok" />
      <Satir etiket="ana model" deger={k.anaBeyin} neden="kaydedilmemiş" teknik="`kaynak.ana_beyin` yükte yok" />
      <Satir etiket="olay defteri" deger={k.events} neden="kaydedilmemiş" teknik="`kaynak.events` yükte yok" />
      <div className="flex flex-wrap items-baseline gap-x-2 gap-y-1">
        <span className="w-24 shrink-0 text-muted-foreground">bot listesi</span>
        {k.botlar === null ? (
          <Olculemedi
            neden="bot listesi ölçülemedi"
            teknik="`kaynak.botlar: null` — boş liste 'bot yok' derdi; ölçülen şey 'listeyi okuyamadım'"
          />
        ) : (
          <span className="flex flex-wrap gap-1">
            {k.botlar.length === 0 ? (
              <span className="text-muted-foreground italic">dizin okundu, içinde profil yok</span>
            ) : (
              k.botlar.map((b) => (
                <Badge key={b} variant="outline" className="text-[10px]">
                  {b}
                </Badge>
              ))
            )}
          </span>
        )}
      </div>
      {k.eventsNeden === null ? null : (
        <p className="rounded-md border border-dashed bg-muted/30 px-2 py-1.5 text-muted-foreground leading-relaxed">
          Teslim olayları ölçülemedi: {k.eventsNeden}
        </p>
      )}
      <Separator className="my-1" />
      <div className="flex flex-col gap-1 text-muted-foreground">
        <span>
          konuşma penceresi:{" "}
          {s === null || s.limit === null ? (
            <Olculemedi neden="bildirilmedi" teknik="`suzgec.limit` yükte yok" />
          ) : (
            <strong className="tabular-nums">{bicimSayi(s.limit)}</strong>
          )}
          {kirpildi && s !== null && s.limitIstenen !== null ? (
            <span className="ml-1 text-uyari">
              (istenen {bicimSayi(s.limitIstenen)} TAVANDA kırpıldı)
            </span>
          ) : null}
        </span>
        <span>
          teslim tavanı:{" "}
          {k.teslimTavani === null ? (
            <Olculemedi neden="bildirilmedi" teknik="`kaynak.teslim_tavani` yükte yok" />
          ) : (
            <strong className="tabular-nums">{bicimSayi(k.teslimTavani)}</strong>
          )}
        </span>
        <span>
          sahipsiz teslim:{" "}
          {k.eslesmeyenToplam === null ? (
            <Olculemedi
              neden="ölçülemedi"
              teknik="bot listesi ya da olay defteri okunamadan kimin sahipsiz olduğu söylenemez"
            />
          ) : (
            <strong className="tabular-nums">{bicimSayi(k.eslesmeyenToplam)}</strong>
          )}
        </span>
        <span>
          süzgeç:{" "}
          {s === null || s.ajan === null ? (
            <span>yok (tümü)</span>
          ) : (
            <Badge variant="secondary" className="text-[10px]">
              ajan={s.ajan}
            </Badge>
          )}
          {s === null || s.eslesenN === null || s.toplamN === null ? null : (
            <span className="ml-1 tabular-nums">
              · {bicimSayi(s.eslesenN)} / {bicimSayi(s.toplamN)} kayıt
            </span>
          )}
        </span>
      </div>
      <Separator className="my-1" />
      {/* DURUM LEJANTI (maket): noktanın üç anlamı tek yerde yazılı. Renk tek başına
          anlam taşımaz — lejant olmadan amber "kötü" diye okunurdu, oysa söylediği
          şey "bilmiyorum". */}
      <div className="flex flex-wrap gap-x-4 gap-y-1 text-[11px] text-muted-foreground">
        <span className="flex items-center gap-1.5">
          <i className="size-2 rounded-full bg-basari" aria-hidden />
          bugün konuştu ya da teslim etti
        </span>
        <span className="flex items-center gap-1.5">
          <i className="size-2 rounded-full bg-muted-foreground" aria-hidden />
          bugün kaydı yok
        </span>
        <span className="flex items-center gap-1.5">
          <i className="size-2 rounded-full bg-uyari" aria-hidden />
          ölçülemedi
        </span>
      </div>
    </div>
  );
}

/* ---- DAMGA --------------------------------------------------------------- */

/** Damga ÇEVRİLEMEDİYSE HAM DEĞER GÖSTERİLİR — "geçersiz tarih" ya da boşluk
 *  yerine defterde NE YAZDIĞI. Ham'ı gizlemek ölçülemezliği iki kat yapardı:
 *  operatör hem damgayı göremez hem defterdeki değeri öğrenemezdi. */
function Saat({ ts, tsHam }: { ts: string | null; tsHam: string | null }) {
  if (ts !== null) return <span className="tabular-nums">{saatMetni(ts) ?? ts}</span>;
  if (tsHam !== null) {
    return (
      <span
        className="font-mono text-uyari"
        title="damga ISO-8601'e çevrilemedi — bu, defterde YAZAN ham değerdir (`ts_ham`)"
      >
        ham damga: {tsHam}
      </span>
    );
  }
  return <Olculemedi neden="damga yok" teknik="`ts` ve `ts_ham` ikisi de null — defterde damga alanı boş" />;
}

/* ---- BALON --------------------------------------------------------------- */

function isaretle(a: FiloAjani): string {
  if (a.tur === "ana") return "⌘";
  return (a.ad ?? "?").replace(/^@/, "").slice(0, 1).toLocaleUpperCase("tr-TR");
}

function MesajBalonu({ m, isaret }: { m: FiloMesaji; isaret: string }) {
  const yan = mesajYani(m.rol);
  return (
    <Message align={yan === "sag" ? "end" : "start"}>
      <MessageAvatar>
        <Avatar className="size-7">
          <AvatarFallback className="bg-muted text-[11px] text-foreground">
            {yan === "sag" ? isaret : "⚙"}
          </AvatarFallback>
        </Avatar>
      </MessageAvatar>
      <MessageContent>
        <MessageHeader className="gap-2">
          <span>{m.rol === null ? "rol kaydedilmemiş" : (ROL_ETIKET[m.rol] ?? m.rol)}</span>
        </MessageHeader>
        <BubbleGroup>
          <Bubble variant={yan === "sag" ? "default" : "outline"} align={yan === "sag" ? "end" : "start"}>
            <BubbleContent>
              {m.metin === null ? (
                <Olculemedi neden="gövde okunamadı" teknik="`mesaj.metin` bir dizge değil" />
              ) : m.metin === "" ? (
                <span className="text-xs italic opacity-80">
                  gövde ÖLÇÜLDÜ ve boş — defterde içeriksiz bir satır
                </span>
              ) : (
                <span className="whitespace-pre-wrap break-words text-sm leading-relaxed">{m.metin}</span>
              )}
              {m.kirpildi === true ? (
                <span className="mt-1 block text-[11px] opacity-80">
                  … devamı var — bu gövde uçta KIRPILDI
                  {m.hamUzunluk === null
                    ? " (ham uzunluk kaydedilmemiş)"
                    : `; tam metin ${bicimSayi(m.hamUzunluk)} karakter`}
                </span>
              ) : null}
            </BubbleContent>
          </Bubble>
        </BubbleGroup>
        <MessageFooter>
          <Saat ts={m.ts} tsHam={m.tsHam} />
        </MessageFooter>
      </MessageContent>
    </Message>
  );
}

/* ---- TESLİM ÇİPİ (akış içinde) ------------------------------------------- */

function TeslimAyrintisi({ t }: { t: FiloTeslimi }) {
  return (
    <>
      {t.detay === null ? null : <p className="mb-1 break-words leading-relaxed">{t.detay}</p>}
      <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
        <span className="text-muted-foreground">damgalanan:</span>
        {t.damgalanan === null ? (
          <Olculemedi
            neden="üretici bu alanı basmadı"
            teknik="olayda `damgalanan` alanı YOK — boş liste 'hiçbir şey damgalanmadı' derdi"
          />
        ) : t.damgalanan.length === 0 ? (
          <span className="text-muted-foreground italic">alan var, liste boş</span>
        ) : (
          t.damgalanan.map((d, i) => (
            <Badge key={`${d}-${i}`} variant="ghost" className="text-[10px]">
              {d}
            </Badge>
          ))
        )}
      </div>
      {/* ÖLÇÜLEMEYENLER DÜŞÜRÜLMEZ, ROZETLENİR: üreticinin "şu kaynakları ölçemedim"
          beyanı tam da bu yüzeyin konusudur — onu gizlemek, ölçülemezliği göstermek
          için yazılmış bir alanı kaybetmek olurdu. */}
      {t.olculemeyen === null ? null : t.olculemeyen.length === 0 ? (
        <p className="mt-1 text-muted-foreground">ölçülemeyen kaynak: yok (üretici hepsini ölçmüş)</p>
      ) : (
        <div className="mt-1 flex flex-wrap items-center gap-x-2 gap-y-1">
          <span className="text-uyari">ölçülemeyen kaynak:</span>
          {t.olculemeyen.map((o, i) => (
            <Badge key={`${o}-${i}`} variant="destructive" className="text-[10px]">
              {o}
            </Badge>
          ))}
        </div>
      )}
    </>
  );
}

function TeslimCipi({ t }: { t: FiloTeslimi }) {
  const damga = t.ts === null ? null : (zamanMetni(t.ts) ?? t.ts);
  return (
    <Collapsible className="self-center">
      <CollapsibleTrigger className="flex items-center gap-1.5 rounded-full border border-basari-h bg-basari-t px-3 py-1 text-[11px] text-foreground transition-colors hover:bg-basari-t">
        <Package className="size-3 text-basari" aria-hidden />
        <span>{t.olay ?? "teslim olayı"}</span>
        <span className="text-muted-foreground tabular-nums">{damga ?? "damgası okunamadı"}</span>
      </CollapsibleTrigger>
      <CollapsibleContent className="mt-1.5 rounded-lg border bg-card px-3 py-2 text-[11px]">
        <TeslimAyrintisi t={t} />
      </CollapsibleContent>
    </Collapsible>
  );
}

/* ---- AKIŞ ---------------------------------------------------------------- */

function Oge({ o, isaret }: { o: AkisOgesi; isaret: string }) {
  if (o.tur === "gun") {
    return (
      <Marker variant="separator">
        <MarkerContent>{gunMetni(o.ts) ?? "tarihsiz (damga çevrilemedi)"}</MarkerContent>
      </Marker>
    );
  }
  if (o.tur === "gecis") {
    return (
      <div className="self-center rounded-full border border-uyari-h border-dashed bg-uyari-t px-3 py-1 font-mono text-[11px] text-uyari">
        model değişti: {o.gecis.onceki} → {o.gecis.yeni}
      </div>
    );
  }
  if (o.tur === "oturum") {
    const n = o.oturum.mesajlar === null ? null : o.oturum.mesajlar.length;
    return (
      <div className="flex flex-wrap items-center justify-center gap-2 self-center rounded-full border border-dashed bg-card px-3 py-1 text-[11px] text-muted-foreground">
        <span className="tabular-nums">
          oturum · <Saat ts={o.oturum.ts} tsHam={o.oturum.tsHam} />
        </span>
        <span>{n === null ? "mesaj listesi ölçülemedi" : `${bicimSayi(n)} mesaj`}</span>
      </div>
    );
  }
  if (o.tur === "mesaj") return <MesajBalonu m={o.mesaj} isaret={isaret} />;
  if (o.tur === "bosluk") {
    return (
      <p className="self-center text-[11px] text-muted-foreground leading-relaxed">
        {o.olculemedi
          ? "Bu oturumun mesaj listesi ölçülemedi — boş liste 'bu oturumda hiç mesaj yok' derdi"
          : "Oturum kaydı var, mesaj satırı yok. Ölçülmüş boşluk — oturum açılmış, konuşma yazılmamış"}
      </p>
    );
  }
  if (o.tur === "yersiz") {
    return (
      <p className="self-center text-[11px] text-uyari leading-relaxed">
        {bicimSayi(o.n)} teslim olayının damgası çevrilemedi — zaman çizelgesine yerleştirilemedi,
        düşürülmedi
      </p>
    );
  }
  return <TeslimCipi t={o.teslim} />;
}

/** ÖLÇÜLEMEYEN AJAN BOŞ-DURUM GİBİ ÇİZİLMEZ. Boş bir ekran "bu ajanla
 *  konuşulmamış" diye okunur; ölçülen şey ise "defteri okuyamadım"dır. Maketin
 *  zarif boş-hâli tam bunu söylüyor ve teslim köprüsünü gösteriyor: teslimler
 *  AYRI kaynaktır, oturumları okunamayan bir ajanın teslimleri ölçülmüş olabilir. */
function OlculemediHali({ a, teslimleriAc }: { a: FiloAjani; teslimleriAc: () => void }) {
  const teslimVar = a.teslimler !== null && a.teslimler.length > 0;
  return (
    <div className="m-auto flex max-w-md flex-col items-center gap-3 px-6 py-10 text-center">
      <div className="grid size-16 place-items-center rounded-full border-2 border-uyari-h border-dashed bg-muted font-semibold text-2xl text-muted-foreground">
        {isaretle(a)}
      </div>
      <h2 className="font-semibold text-sm">Konuşma defteri ölçülemedi</h2>
      <p className="text-muted-foreground text-xs leading-relaxed">
        Bu "iletişim yok" DEĞİLDİR — defter okunamadı.{" "}
        {a.neden ?? "Uç nedenini yazmadı: hangi defterin okunamadığı söylenmemiş."}
      </p>
      <details className="text-[11px] text-muted-foreground">
        <summary className="cursor-pointer text-primary">teknik ayrıntı</summary>
        <code className="mt-1 block break-all font-mono">
          durum: {a.durum ?? "kaydedilmemiş"} · oturumlar: null
        </code>
      </details>
      {teslimVar ? (
        <button type="button" onClick={teslimleriAc} className="text-primary text-xs underline underline-offset-2">
          Teslim damgaları ayrı kaynaktan ölçülebildi → Teslimler
        </button>
      ) : null}
    </div>
  );
}

function Akis({ a, teslimleriAc }: { a: FiloAjani; teslimleriAc: () => void }) {
  if (a.oturumlar === null) return <OlculemediHali a={a} teslimleriAc={teslimleriAc} />;

  const akis = botAkisi(a);
  if (akis.length === 0) {
    return (
      <div className="m-auto flex max-w-md flex-col items-center gap-3 px-6 py-10 text-center">
        <div className="grid size-16 place-items-center rounded-full border border-dashed bg-muted text-muted-foreground">
          <TriangleAlert className="size-6" aria-hidden />
        </div>
        <h2 className="font-semibold text-sm">Defter okundu, içinde oturum yok</h2>
        <p className="text-muted-foreground text-xs leading-relaxed">
          Bu ölçülmüş bir boşluktur ve "ölçülemedi"den farklıdır: profil koştu, konuşma kaydı
          üretmedi — ya da defteri yeni açılmış.
        </p>
      </div>
    );
  }

  const isaret = isaretle(a);
  return (
    <div className="flex flex-col gap-3 px-4 py-4 sm:px-6">
      {akis.map((o) => (
        <Oge key={o.anahtar} o={o} isaret={isaret} />
      ))}
    </div>
  );
}

/* ---- TESLİMLER SEKMESİ --------------------------------------------------- */

export function TeslimSatiri({ t }: { t: FiloTeslimi }) {
  return (
    <li className="rounded-lg border bg-card px-3 py-2 text-xs">
      <div className="flex flex-wrap items-center gap-2">
        <span className="font-medium tabular-nums">
          {t.ts === null ? (
            <Olculemedi neden="damga yok" teknik="olayda `ts` alanı yok" />
          ) : (
            (zamanMetni(t.ts) ?? t.ts)
          )}
        </span>
        <Badge variant="outline" className="font-mono text-[10px]">
          {t.olay ?? "olay adı kaydedilmemiş"}
        </Badge>
      </div>
      <div className="mt-1">
        <TeslimAyrintisi t={t} />
      </div>
    </li>
  );
}

function TeslimlerPaneli({ a }: { a: FiloAjani }) {
  const teslimler = a.teslimler;
  return (
    <div className="flex flex-col gap-3 px-4 py-4 sm:px-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 leading-none">
            <Radio className="size-4" aria-hidden />
            Teslim damgaları
          </CardTitle>
          <CardDescription>
            `state/events.jsonl` içindeki `{a.ad ?? "<ad>"}_brifingi_teslim` olayları — konuşma
            defterinden AYRI bir kaynak. En yeniden eskiye.
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-2">
          {teslimler === null ? (
            <OlculemediBlok
              baslik="Teslim defteri ölçülemedi"
              neden="Olay defteri okunamadı — boş liste 'hiç brifing teslim edilmedi' derdi ve bu AYRI bir iddiadır; nedeni kaynak künyesinde yazılı"
              teknik="`teslimler: null`"
            />
          ) : teslimler.length === 0 ? (
            <p className="rounded-lg border border-dashed bg-muted/30 p-3 text-muted-foreground text-xs leading-relaxed">
              Olay defteri OKUNDU ve bu ajana ait teslim olayı yok. Ölçülmüş boşluk — defterin
              taranan kuyruğunda bu ajanın damgası geçmiyor.
            </p>
          ) : (
            <>
              {a.teslimKirpildi === true ? (
                <p className="rounded-md border border-uyari-h bg-uyari-t px-2 py-1.5 text-uyari text-xs leading-relaxed">
                  KESİLDİ: aşağıdaki son {bicimSayi(teslimler.length)} olay gösteriliyor
                  {a.teslimToplam === null
                    ? " — toplam sayı kaydedilmemiş"
                    : `, taranan pencerede toplam ${bicimSayi(a.teslimToplam)} olay var`}
                  .
                </p>
              ) : null}
              <ul className="flex flex-col gap-2">
                {teslimler.map((t, i) => (
                  <TeslimSatiri key={`${t.olay ?? "olay"}-${t.ts ?? i}`} t={t} />
                ))}
              </ul>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

/* ---- SAHİPSİZ TESLİMLER -------------------------------------------------- */

/** Hiçbir profile karşılık gelmeyen teslim olayı (`oneri_brifingi_teslim` gibi).
 *  Sessizce düşürmek, panonun "tüm ajan iletişimi burada" iddiasını yalan yapardı;
 *  bu yüzden sol listenin altında kendi hayalet satırı ve kendi paneli var. */
export function SahipsizPaneli({ yuk }: { yuk: FiloYuku | null }) {
  const liste = yuk === null ? null : yuk.eslesmeyenTeslimler;
  const toplam = yuk?.kaynak?.eslesmeyenToplam ?? null;
  return (
    <div className="flex flex-col gap-3 px-4 py-4 sm:px-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 leading-none">
            <Inbox className="size-4" aria-hidden />
            Sahipsiz teslimler
          </CardTitle>
          <CardDescription>
            `*_brifingi_teslim` sonekini taşıyan ama listedeki hiçbir ajana denk düşmeyen olaylar.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {liste === null ? (
            <OlculemediBlok
              baslik="Sahipsiz teslimler ölçülemedi"
              neden="Ajan listesi ya da olay defteri okunamadı — kimin sahipsiz olduğu ancak tam liste bilinirken söylenebilir"
              teknik="`eslesmeyen_teslimler: null`"
            />
          ) : liste.length === 0 ? (
            <p className="rounded-lg border border-dashed bg-muted/30 p-3 text-muted-foreground text-xs leading-relaxed">
              Olay defteri okundu ve sahipsiz teslim yok — her damga bir ajana denk düştü. Ölçülmüş
              boşluk.
            </p>
          ) : (
            <>
              {toplam !== null && toplam > liste.length ? (
                <p className="mb-2 text-uyari text-xs">
                  KESİLDİ: son {bicimSayi(liste.length)} olay gösteriliyor, toplam {bicimSayi(toplam)}.
                </p>
              ) : null}
              <ul className="flex flex-col gap-2">
                {liste.map((t, i) => (
                  <TeslimSatiri key={`${t.olay ?? "olay"}-${t.ts ?? i}`} t={t} />
                ))}
              </ul>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

/* ---- GİRİŞ: AJAN MUHATABININ PANELİ -------------------------------------- */

/** AYRI KAPI, AYRI UÇ: bu panel `/api/ajanlar`dan besleniyor ve `/api/agent`in
 *  düşmesi onu GİZLEYEMEZ. Tek kapı tüm yüzeyi sarsaydı, sağlam ve ölçülmüş bir
 *  ajan defteri başka bir kaynağın arızası yüzünden "okunamadı" kutusunun
 *  arkasında kalırdı. */
export function Filo({
  durum,
  m,
  sekme,
  teslimleriAc,
}: {
  durum: Durum<Record<string, unknown>>;
  m: Muhatap;
  sekme: SekmeAdi;
  teslimleriAc: () => void;
}) {
  return (
    <Kapi durum={durum} ad="`/api/ajanlar`" yukseklik="h-96">
      {() => {
        const a = m.ajan;
        if (a === null) {
          return (
            <p className="px-6 py-8 text-muted-foreground text-sm">
              Bu satırın ham kaydı düştü — liste yeniden çekildiğinde geri gelecek.
            </p>
          );
        }
        return sekme === "teslimler" ? (
          <TeslimlerPaneli a={a} />
        ) : (
          <Akis a={a} teslimleriAc={teslimleriAc} />
        );
      }}
    </Kapi>
  );
}
