"use client";

/* ============================================================================
   MERİDİAN SOHBETİ — panonun İLK gerçek yazma şeridi (TSK-012 dalga-B, B2)
   ----------------------------------------------------------------------------
   BU DOSYA BİR "HAYIR"IN KAPANIŞIDIR. `Ajan.tsx`in ilk cümlesi 2026-08-25'ten beri
   şuydu: "panodan ajana serbest metin gönderen bir uç yok, bu yüzden yazma şeridi
   çizili ama KİLİTLİ". Uç 2026-09-07'de açıldı (dalga-B/B1, dağıtım #27):
     · `POST /api/sohbet {mesaj, oturum}` → defter satırının TA KENDİSİ
     · `GET  /api/sohbet?oturum&n`        → geçmiş + künye + kota
     · `GET  /api/sohbet/kota`            → {bugun|null, kalan, tavan, neden}
   Kilit bu yüzden AÇILDI; şerhi silinmedi, GÜNCELLENDİ (`SohbetHatti::YazmaSeridi`).

   AYRI MUHATAP, ÇÜNKÜ AYRI DEFTER: #öneri-hattı `hypotheses.jsonl`i, ajan satırları
   `~/.hermes` konuşma defterlerini gösteriyor. Buradaki akış `state/sohbet.jsonl`.
   Kilidi o kanallardan birinde açsaydık, operatör yazar-gönderir ve cevabı O AKIŞTA
   hiç göremezdi; iki defteri tek akışta birleştirmek ise aynı deftere iki gerçek
   uydurmak olurdu (bu yüzeyin ilk kuralı).

   DURUM AJAN.TSX'TE DEĞİL BURADA, AMA ÇİZİM İKİYE BÖLÜNÜYOR: akış kaydırma kabının
   İÇİNDE, yazma şeridi DIŞINDA duruyor (kabuk sözleşmesi). Bu yüzden durum bir
   hook'ta (`useSohbet`) toplanıyor ve iki bileşene veriliyor — ikinci bir `useApi`
   kopyası açsaydık aynı geçmiş iki kez çekilir, iki farklı anın gövdesi yan yana
   çizilirdi.

   GÖNDERİLEN SATIR YERELDE TUTULUR, GEÇMİŞ YENİDEN ÇEKİLMEZ: uç zaten deftere
   yazdığı satırın kendisini döndürüyor (api.py::api_sohbet şerhi). "Yeniden yükle"ye
   basıldığında yerel ekler TEMİZLENİR ve defterin kendisi okunur — iki kaynak
   birbirinin üstüne binmez.

   UYDURMA YASAĞI EKRANDA GÖRÜNÜR (kartın B3 sayımı bunlara bakacak):
     · `kaynaklar: []` → "kaynak atfı yok" rozeti (sessiz boşluk YOK)
     · `llm_dustu`     → "MODEL YOK" durumu, hata kılığında DEĞİL
     · `kota_bugun: null` → "ölçülemedi + neden"; 0 YAZILMAZ
   ============================================================================ */
import { useCallback, useEffect, useRef, useState } from "react";

import { AlertTriangle, Inbox, Loader2, MessageSquareDashed, RefreshCw, Send, User } from "lucide-react";

import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Bubble, BubbleContent, BubbleGroup } from "@/components/ui/bubble";
import { Button } from "@/components/ui/button";
import { Empty, EmptyDescription, EmptyHeader, EmptyMedia, EmptyTitle } from "@/components/ui/empty";
import { InputGroup, InputGroupAddon, InputGroupButton, InputGroupTextarea } from "@/components/ui/input-group";
import { Message, MessageAvatar, MessageContent, MessageFooter, MessageHeader } from "@/components/ui/message";
import { cn } from "@/lib/utils";

import { yuzeyYolu } from "../../alanlar";
import { apiPost } from "../../gonder";
import { useRouter } from "../../rota";
import { useApi } from "../../veri";
import { zamanMetni } from "./ortak";
import {
  durumBeyani,
  gecmisOku,
  gonderimHatasi,
  gonderimKapaliMi,
  jetonMetni,
  kaynakBeyani,
  kaynakEtiketi,
  kotaMetni,
  kotaOku,
  modelMetni,
  oturumSec,
  satirOku,
  sohbetIstegiAbone,
  sohbetIstegiAl,
  sureMetni,
  yanitDurumu,
  type GonderimHatasi,
  type KotaGorunumu,
  type SohbetSatiri,
} from "./sohbet";

/** Oturum kimliğinin yeri. Tarayıcıya özgüdür ve gün başına yenilenir (`oturumSec`). */
const OTURUM_ANAHTARI = "meridian.sohbet.oturum";

/** Geçmişte kaç satır istenecek — spec §2: "UI son 50 mesajı gösterir". */
const GECMIS_N = 50;

/* ---- YEREL DEPO: OKUNAMAYABİLİR, YAZILAMAYABİLİR ------------------------- */

function depoOku(anahtar: string): string | null {
  try {
    return window.localStorage.getItem(anahtar);
  } catch {
    // YASA 4 · sessiz-yutma İŞARETLİ: gizli sekmede/çerez kapalıyken `localStorage`
    // erişimi ATAR. Kaybedilen şey ÖLÇÜLÜ ve küçüktür — oturum kimliği kalıcı olmaz,
    // her açılışta yenisi üretilir; sohbet çalışmaya devam eder. Panoyu bu yüzden
    // karartmak, taşınabilir olmayan bir depoyu zorunlu kılmak olurdu.
    return null;
  }
}

function depoYaz(anahtar: string, deger: string): void {
  try {
    window.localStorage.setItem(anahtar, deger);
  } catch {
    // YASA 4 · sessiz-yutma İŞARETLİ: yukarıdakiyle aynı sınıf (kota dolu da olabilir).
    // Yazamamak bir arıza değil, kalıcılığın yokluğudur ve sohbeti engellemez.
  }
}

/* ---- DURUM --------------------------------------------------------------- */

export interface SohbetDurumu {
  readonly oturum: string;
  readonly satirlar: readonly SohbetSatiri[];
  /** Geçmiş okunamadıysa NEDENİ — boş liste "hiç konuşulmadı" DEMEK DEĞİL. */
  readonly gecmisNeden: string | null;
  readonly gecmisYukleniyor: boolean;
  readonly oturumDustu: boolean;
  readonly kota: KotaGorunumu;
  readonly gonderiliyor: boolean;
  readonly hata: GonderimHatasi | null;
  readonly taslak: string;
  readonly taslakYaz: (x: string) => void;
  readonly gonder: () => void;
  readonly yenidenYukle: () => void;
  /** ⌘K devri: palet odak istediğinde artan sayaç — şerit bunu izleyip odaklanır. */
  readonly odakSayaci: number;
}

export function useSohbet(acik: boolean): SohbetDurumu {
  const [oturum] = useState(() => {
    const bugun = new Date().toISOString().slice(0, 10);
    const secilen = oturumSec(depoOku(OTURUM_ANAHTARI), bugun, Math.random);
    depoYaz(OTURUM_ANAHTARI, secilen);
    return secilen;
  });

  // YOL `acik` DEĞİLKEN `null`: kapalı bir muhatabın defterini çekmek, her Ajan
  // ziyaretinde bedeli olan ama okunmayan bir istek olurdu (Bedel yasası).
  const yol = acik ? `/api/sohbet?oturum=${encodeURIComponent(oturum)}&n=${GECMIS_N}` : null;
  const gecmis = useApi<unknown>(yol, 0);
  const kotaUcu = useApi<unknown>(acik ? "/api/sohbet/kota" : null, 0);

  const [ekler, setEkler] = useState<readonly SohbetSatiri[]>([]);
  const [taslak, setTaslak] = useState("");
  const [gonderiliyor, setGonderiliyor] = useState(false);
  const [hata, setHata] = useState<GonderimHatasi | null>(null);
  const [odakSayaci, setOdakSayaci] = useState(0);

  const okuma = gecmisOku(gecmis.veri, gecmis.hata);
  const kota = kotaMetni(kotaOku(kotaUcu.veri), kotaUcu.hata);

  const yenidenYukle = useCallback(() => {
    // YEREL EKLER TEMİZLENİR: aynı satır hem defterden hem yerel listeden gelseydi
    // konuşma iki kez çizilirdi. Defter tek kaynaktır; yerel ek yalnız ONA kadar yaşar.
    setEkler([]);
    gecmis.tazele();
    kotaUcu.tazele();
  }, [gecmis, kotaUcu]);

  const gonder = useCallback(() => {
    // TEK KAPI (K-1): `gonderimKapaliMi` giriş kutusunun/düğmenin `disabled`ıyla AYNI
    // ifadeyi okur. Kota doluyken bu çağrı gövdesine hiç girmez — model çağrılmaz VE
    // `state/sohbet.jsonl`e ölçüm değeri olmayan bir satır YAZILMAZ.
    if (gonderimKapaliMi(taslak, gonderiliyor, kota.dolu)) return;
    const mesaj = taslak.trim();
    setGonderiliyor(true);
    setHata(null);
    void apiPost("/api/sohbet", { mesaj, oturum }).then((s) => {
      setGonderiliyor(false);
      if (!s.ok) {
        setHata(gonderimHatasi(s.kod, s.detay));
        return;
      }
      const satir = satirOku(s.govde);
      if (satir === null) {
        // ŞEKİL TANINMADIYSA TASLAK SİLİNMEZ: "gönderdim ama ne olduğunu bilmiyorum"
        // hâlinde metni de kaybettirmek, operatöre iki kayıp birden yaşatırdı.
        setHata({
          baslik: "Yanıt okunamadı",
          govde:
            "Uç 200 döndü ama gövdesi bir defter satırı değildi — cevabın deftere yazılıp " +
            "yazılmadığı buradan BİLİNEMEZ. Geçmişi yeniden yükle ve satırı ORADAN doğrula.",
          oturumDustu: false,
        });
        return;
      }
      setEkler((e) => [...e, satir]);
      setTaslak("");
      // KOTA HER TURDAN SONRA YENİDEN OKUNUR: yanıt `kota_bugun` taşıyor ama rozet
      // TAVANI ve KALANI da yazıyor; ikisini yanıttan türetmek, ucun kendi hükmünü
      // (halka taşması → `bugun: null`) panoda yeniden hesaplamak olurdu.
      kotaUcu.tazele();
    });
  }, [taslak, gonderiliyor, oturum, kotaUcu, kota.dolu]);

  // ⌘K DEVRİ: palet isteği bırakır, panel BURADA tüketir. Abonelik şart — palet
  // zaten bu adresteyken `push` hash'i değiştirmez, yani rotayı dinlemek yetmezdi.
  useEffect(() => {
    if (!acik) return;
    const uygula = () => {
      const istek = sohbetIstegiAl();
      if (istek === null) return;
      if (istek.taslak !== null) setTaslak(istek.taslak);
      setOdakSayaci((n) => n + 1);
    };
    uygula(); // panel yeni açıldıysa istek zaten kutuda bekliyordur
    return sohbetIstegiAbone(uygula);
  }, [acik]);

  return {
    oturum,
    satirlar: [...okuma.satirlar, ...ekler],
    gecmisNeden: okuma.neden,
    gecmisYukleniyor: gecmis.yukleniyor,
    oturumDustu: gecmis.oturumDustu || kotaUcu.oturumDustu,
    kota,
    gonderiliyor,
    hata,
    taslak,
    taslakYaz: setTaslak,
    gonder,
    yenidenYukle,
    odakSayaci,
  };
}

/* ---- AKIŞ ---------------------------------------------------------------- */

export function MeridianAkisi({ s }: { s: SohbetDurumu }) {
  return (
    <div className="flex flex-col gap-4 px-4 py-4 sm:px-6">
      <div className="rounded-xl border border-bilgi-h bg-bilgi-t px-4 py-3">
        <p className="font-semibold text-[10px] text-bilgi uppercase tracking-wider">
          yetki sınırı · sohbet YALNIZ okur
        </p>
        <p className="mt-1.5 text-sm leading-relaxed">
          Meridian bu hatta salt-okunur araçlarla defterlere bakar ve kaynak atfıyla cevap verir.
          Hiçbir şeyi doğrudan değiştirmez: gerekirse onay kuyruğuna BEKLEYEN bir öneri bırakır,
          kararı sen verirsin. Bu turların hepsi <code className="font-mono">state/sohbet.jsonl</code>
          {" "}defterine yazılır.
        </p>
        <p className="mt-1.5 text-muted-foreground text-xs">
          oturum: <code className="font-mono">{s.oturum}</code> · gün başına tek oturum (kartın seans sayımı buna dayanıyor)
        </p>
      </div>

      {s.oturumDustu ? (
        <p className="rounded-md border border-kritik-h bg-kritik-t px-4 py-2.5 text-sm leading-relaxed">
          Oturum düştü — <code className="font-mono">/api/sohbet</code> 401 döndü. Bu bir ölçüm
          hatası değil: panoya yeniden giriş gerekiyor.
        </p>
      ) : null}

      {s.gecmisNeden !== null ? (
        <p className="rounded-md border border-uyari-h bg-uyari-t px-4 py-2.5 text-sm leading-relaxed">
          Geçmiş okunamadı: {s.gecmisNeden} — aşağıdaki akış defterin TAMAMI DEĞİL. &quot;Hiç
          konuşulmamış&quot; diye okuma.
        </p>
      ) : null}

      {s.satirlar.length === 0 ? (
        s.gecmisYukleniyor ? (
          <p className="text-muted-foreground text-sm">Geçmiş okunuyor…</p>
        ) : (
          <Empty className="border-0">
            <EmptyHeader>
              <EmptyMedia variant="icon">
                <MessageSquareDashed />
              </EmptyMedia>
              <EmptyTitle>
                {s.gecmisNeden === null ? "Bu oturumda henüz mesaj yok" : "Geçmiş ölçülemedi"}
              </EmptyTitle>
              <EmptyDescription>
                {s.gecmisNeden === null
                  ? "Defter okundu ve bu oturuma ait satır yok — ölçülmüş boşluk. Aşağıdaki kutuya yaz."
                  : "Yukarıdaki neden okunmadan bu ekran 'boş' sayılamaz."}
              </EmptyDescription>
            </EmptyHeader>
          </Empty>
        )
      ) : (
        s.satirlar.map((satir, i) => (
          <Tur key={`${satir.ts ?? "damgasiz"}-${i}`} satir={satir} />
        ))
      )}

      {s.gonderiliyor ? (
        <Message align="start">
          <MessageAvatar>
            <Avatar className="size-7">
              <AvatarFallback className="bg-muted text-foreground">
                <Loader2 className="size-3.5 animate-spin" aria-hidden />
              </AvatarFallback>
            </Avatar>
          </MessageAvatar>
          <MessageContent>
            <MessageHeader className="gap-2">
              <span>meridian · tur sürüyor</span>
            </MessageHeader>
            <BubbleGroup>
              <Bubble variant="outline" align="start">
                <BubbleContent>
                  <p className="text-sm leading-relaxed">
                    Araç turları koşuyor. Bu tur en çok 6 model turu ve 180 saniye sürebilir
                    (sunucu tavanı) — sayfayı kapatma; cevap deftere yazılıyor.
                  </p>
                </BubbleContent>
              </Bubble>
            </BubbleGroup>
          </MessageContent>
        </Message>
      ) : null}
    </div>
  );
}

/** Bir tur = operatörün mesajı + Meridian'ın cevabı. İkisi AYNI defter satırından. */
function Tur({ satir }: { satir: SohbetSatiri }) {
  const durum = yanitDurumu(satir);
  const beyan = durumBeyani(durum);
  const kaynakYok = kaynakBeyani(satir);
  const zaman = zamanMetni(satir.ts);
  const { push: git } = useRouter();

  return (
    <div className="flex flex-col gap-4">
      <Message align="end">
        <MessageAvatar>
          <Avatar className="size-7">
            <AvatarFallback className="bg-muted text-foreground">
              <User className="size-3.5" aria-hidden />
            </AvatarFallback>
          </Avatar>
        </MessageAvatar>
        <MessageContent>
          <MessageHeader className="gap-2">
            <span>operatör</span>
          </MessageHeader>
          <BubbleGroup>
            <Bubble variant="secondary" align="end">
              <BubbleContent>
                <p className="whitespace-pre-wrap text-sm leading-relaxed">{satir.mesaj}</p>
              </BubbleContent>
            </Bubble>
          </BubbleGroup>
          <MessageFooter>{zaman ?? "damga yok"}</MessageFooter>
        </MessageContent>
      </Message>

      <Message align="start">
        <MessageAvatar>
          <Avatar className="size-7">
            <AvatarFallback className="bg-muted text-[11px] text-foreground">⌘</AvatarFallback>
          </Avatar>
        </MessageAvatar>
        <MessageContent>
          <MessageHeader className="gap-2">
            <span>meridian</span>
            <span className="text-muted-foreground/70">· {modelMetni(satir)}</span>
          </MessageHeader>
          <BubbleGroup>
            <Bubble variant={durum === "cevap" ? "outline" : "destructive"} align="start">
              <BubbleContent className="flex flex-col gap-2">
                {beyan === null ? null : <p className="font-medium text-xs leading-relaxed">{beyan}</p>}
                <p className="whitespace-pre-wrap text-sm leading-relaxed">{satir.cevap}</p>
              </BubbleContent>
            </Bubble>
          </BubbleGroup>

          {/* ---- KAYNAK ATFI: BOŞLUK DA BİR SİNYALDİR ---------------------- */}
          <ul className="mt-1.5 flex flex-wrap items-center gap-1.5">
            {kaynakYok !== null ? (
              <li>
                <Badge variant="outline" className="border-uyari-h bg-uyari-t text-[10px] text-uyari">
                  {kaynakYok}
                </Badge>
              </li>
            ) : (
              satir.kaynaklar.map((k, i) => (
                <li key={`${k.arac}-${i}`}>
                  <Badge variant="outline" className="bg-card font-mono text-[10px]">
                    {kaynakEtiketi(k)}
                  </Badge>
                </li>
              ))
            )}
          </ul>

          {satir.oneriId === null ? null : (
            <div className="mt-2 flex flex-wrap items-center gap-2 rounded-md border border-uyari-h bg-uyari-t px-3 py-2">
              <span className="text-xs leading-relaxed">
                Bu tur onay kuyruğuna BEKLEYEN bir öneri bıraktı:{" "}
                <code className="font-mono text-[11px]">{satir.oneriId}</code> — icra YOK, karar sende.
              </span>
              <Button
                type="button"
                variant="outline"
                size="sm"
                className="h-7 px-2 text-xs"
                onClick={() => git(yuzeyYolu("tasks", "onaylar"))}
              >
                <Inbox className="size-3.5" aria-hidden />
                Onay kuyruğuna git
              </Button>
            </div>
          )}

          <MessageFooter className="flex-wrap gap-x-2">
            <span>{zaman ?? "damga yok"}</span>
            <span>· {sureMetni(satir.sureS)}</span>
            <span>· {satir.turN} araç turu</span>
            <span>· {jetonMetni(satir.jetonGiris, satir.jetonCikis)}</span>
            {satir.semaDisiN !== null && satir.semaDisiN > 0 ? (
              <span className="text-uyari">· {satir.semaDisiN} şema dışı çağrı (araç KOŞMADI)</span>
            ) : null}
          </MessageFooter>
        </MessageContent>
      </Message>
    </div>
  );
}

/* ---- YAZMA ŞERİDİ: ARTIK AÇIK -------------------------------------------- */

export function MeridianSeridi({ s }: { s: SohbetDurumu }) {
  const kutu = useRef<HTMLTextAreaElement | null>(null);

  // ⌘K'DAN GELEN ODAK. Sayaç artınca odaklanır — aynı adreste ikinci kez ⌘K
  // basıldığında da çalışsın diye (değer değil, ARTIŞ izleniyor).
  useEffect(() => {
    if (s.odakSayaci === 0) return;
    kutu.current?.focus();
  }, [s.odakSayaci]);

  return (
    <div className="flex shrink-0 flex-col gap-1.5 border-t bg-card px-4 py-2.5 sm:px-6">
      {s.kota.kapaliBeyan === null ? null : (
        <div className="rounded-md border border-uyari-h bg-uyari-t px-3 py-2">
          <p className="font-medium text-xs">Giriş kapalı — {s.kota.kapaliBeyan}</p>
        </div>
      )}
      {s.hata === null ? null : (
        <div className="rounded-md border border-kritik-h bg-kritik-t px-3 py-2">
          <p className="font-medium text-xs">{s.hata.baslik}</p>
          <p className="mt-1 text-xs leading-relaxed">{s.hata.govde}</p>
        </div>
      )}
      <InputGroup>
        <InputGroupTextarea
          ref={kutu}
          value={s.taslak}
          onChange={(e) => s.taslakYaz(e.target.value)}
          onKeyDown={(e) => {
            // ENTER GÖNDERİR, SHIFT+ENTER SATIR AÇAR (mesajlaşma grameri). IME
            // birleştirmesi sürerken (`isComposing`) Enter tuşu METNİN kendisine
            // aittir — göndermek, yazılmakta olan kelimeyi yarıda kesmek olurdu.
            if (e.key !== "Enter" || e.shiftKey || e.nativeEvent.isComposing) return;
            e.preventDefault();
            s.gonder();
          }}
          disabled={s.gonderiliyor || s.kota.dolu}
          placeholder="Meridian'a sor: “MU planı neden REVIEW aldı?” · Enter gönderir, Shift+Enter satır açar"
          className="min-h-9 px-3 py-2 text-xs"
        />
        <InputGroupAddon align="block-end">
          <span
            className={cn("flex items-center gap-1.5 text-[11px]", s.kota.uyari ? "text-uyari" : "text-muted-foreground")}
          >
            {s.kota.uyari ? <AlertTriangle className="size-3" aria-hidden /> : null}
            kota · {s.kota.metin}
          </span>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            className="h-6 px-2 text-[11px]"
            onClick={s.yenidenYukle}
            disabled={s.gonderiliyor}
          >
            <RefreshCw className="size-3" aria-hidden />
            Yeniden yükle
          </Button>
          <InputGroupButton
            type="button"
            variant="default"
            size="icon-sm"
            className="ml-auto"
            onClick={s.gonder}
            disabled={gonderimKapaliMi(s.taslak, s.gonderiliyor, s.kota.dolu)}
          >
            {s.gonderiliyor ? <Loader2 className="animate-spin" /> : <Send />}
            <span className="sr-only">{s.gonderiliyor ? "Gönderiliyor" : "Gönder"}</span>
          </InputGroupButton>
        </InputGroupAddon>
      </InputGroup>
      <p className="text-[11px] text-muted-foreground leading-relaxed">
        Mesaj ve cevap <code className="font-mono">state/sohbet.jsonl</code>e yazılır; olay defterine
        yalnız künye düşer (metin GİRMEZ). Sohbet salt-okunur araçlarla çalışır ve yalnız BEKLEYEN
        öneri yazabilir — hiçbir şeyi doğrudan değiştirmez.
      </p>
    </div>
  );
}
