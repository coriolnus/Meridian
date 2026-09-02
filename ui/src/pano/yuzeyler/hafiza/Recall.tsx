"use client";

/* ============================================================================
   HAFIZA · RECALL — üst yüzeyin `recall` oyun alanının karşılığı
   ----------------------------------------------------------------------------
   BU YÜZEYİN TEK "GÖNDEREN" EKRANI, VE BEYANI BURADA DURUYOR. Vekilin yirmi iki
   ucundan yirmi biri salt-okunur GET; `recall` POST'tur ve nedeni bir yetki
   değil bir BOYUTtur: sorgu gövdesi (türler, etiketler, zaman damgası, bütçe)
   bir adres satırına sığmaz. Durum DEĞİŞTİRMEZ ve bu çivili
   (`api.py::api_hindsight_recall` şerhi + `test_recall_state_defterine_yazmaz`).
   İstek gövdesi sunucuda BEYAZ LİSTEyle süzülür (`::_HAFIZA_RECALL_ALANLARI`):
   burada yazdığımız bir alan listede yoksa upstream'e HİÇ gitmez.

   ---------------------------------------------------------------------------
   ÜST YÜZEYDE OLUP BURADA OLMAYAN İKİ DENETİM — VE NEDENLERİ
   ---------------------------------------------------------------------------
   Üst yüzeyin sorgu şeridi bizde OLMAYAN iki şey daha gönderiyor ve ikisi de
   ekranda adıyla yazılı duruyor:

     · EK GÖVDE (`include`) — "parçaları da getir" / "varlıkları da getir"
       kutuları. Alan vekilin beyaz listesinde YOK. Kutuyu çizip göndermemek,
       operatöre çalışan bir düğme göstermek olurdu: kutu işaretlenir, yanıtta
       hiçbir şey değişmez ve kimse nedenini bilmez.
     · ZAMAN PENCERESİ (`temporal_window`) — aynı sebep, aynı sonuç.

   Bu yüzden gövdenin `entities`/`chunks` bölümleri bu panoda HER ZAMAN boş
   gelir ve ekran bunu "sonuç yok" diye DEĞİL, "istenmedi" diye yazar. İkisi
   ayrı cümledir ve karıştırmak ölçülmemiş bir boşluğu ölçülmüş göstermek olurdu.

   ---------------------------------------------------------------------------
   SKORLAR YUVARLANMAZ
   ---------------------------------------------------------------------------
   Üst yüzey bunu kendi şerhinde ölçmüş: `0,001125` ile `0,001004` yuvarlandığında
   ikisi de "0,001" olur ve yeniden sıralayıcının davranışı okunamaz hâle gelir.
   Skorlar burada da HAM basılır.
   ============================================================================ */
import { useState } from "react";
import { Search } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

import type { Bolum } from "../../alanlar";
import { OturumHatasi } from "../../veri";
import { BolumKart, Olculemedi, Satir } from "../sistem/parcalar";

import { Bolme, ETIKET_ESLEME, HamSatirlar, Secim, damga, metin, sayi, sozluk } from "./parcalar";
import type { RecallGovdesi, RecallZarfi } from "./uctipleri";

const UC_RECALL = "/api/hindsight/recall";

/* TÜRLER — üst yüzeyin `fact-type-filter`ının üç değeri. Bu bir SUNUCU sözlüğü
   değil, upstream'in tür kümesidir ve vekil onu süzmez (gövde beyaz listede
   `types` olarak geçer). Tanınmayan bir tür upstream'de 422 olur ve gerekçeye
   döner — sessiz kalmaz. */
const TURLER = [
  { deger: "world", etiket: "dünya" },
  { deger: "experience", etiket: "deneyim" },
  { deger: "observation", etiket: "gözlem" },
] as const;

/* BÜTÇE — üst yüzeyin üç değeri (`search-debug-view.tsx`). */
const BUTCELER = [
  { deger: "low", etiket: "düşük" },
  { deger: "mid", etiket: "orta" },
  { deger: "high", etiket: "yüksek" },
] as const;

/** Sunucu tavanı `HAFIZA_RECALL_TOKEN_TAVANI` = 4096 ve istemcinin sorduğu değer
 *  SUNUCUDA kırpılır. Buraya aynı sayıyı yazmak ikinci bir kopya olurdu; onun
 *  yerine kutu serbest bırakılır ve kırpmanın sunucuda olduğu ekranda yazılıdır. */
const VARSAYILAN_TOKEN = "4096";

/**
 * TEK GÖNDERİM — ve neden `veri.ts`e yazılmadı.
 *
 * Panonun veri katmanı bugün yalnız GET biliyor (`apiGet`/`useApi`). Oraya genel
 * bir gönderim yardımcısı eklemek, panonun HER yüzeyine yazma yolu açan bir
 * kapıyı bu turda açmak olurdu — oysa gönderen tek ekran bu ve gönderdiği şey
 * bir SORGU. Yardımcı bu yüzden burada, dar kapsamda yaşıyor. Genel bir ihtiyaç
 * doğduğu gün taşınır; o gün geldiğinde taşımak, bugün genelleştirmekten ucuzdur.
 *
 * OTURUM DÜŞMESİ AYRI HÂL (`veri.ts` sözleşmesi): 401'i "okunamadı" diye
 * göstermek operatörü ağa bakmaya gönderirdi; çaresi yalnız yeniden giriştir.
 */
async function recallGonder(govde: Record<string, unknown>): Promise<RecallZarfi> {
  const y = await fetch(UC_RECALL, {
    method: "POST",
    credentials: "same-origin",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify(govde),
  });
  if (y.status === 401) throw new OturumHatasi("oturum düştü");
  if (!y.ok) {
    let ek = "";
    try {
      const g = (await y.json()) as { detail?: unknown; error?: unknown };
      const d = g.detail ?? g.error;
      if (typeof d === "string") ek = ` — ${d}`;
    } catch {
      // sessiz-yutma: gövde JSON değilse (vekil önündeki bir katmanın düz metin
      // hatası) ayrıştırma hatası ASIL hatayı gizlememeli; durum kodu aşağıda yazılı.
    }
    throw new Error(`${UC_RECALL} → HTTP ${y.status}${ek}`);
  }
  return (await y.json()) as RecallZarfi;
}

/** Skor satırı — HAM basılır (dosya başlığındaki şerh). */
function Skor({ ad, deger }: { readonly ad: string; readonly deger: unknown }) {
  if (deger === undefined || deger === null) return null;
  const n = sayi(deger);
  return (
    <span className="font-mono text-[10px] text-muted-foreground">
      {ad} {n === null ? String(deger) : String(n)}
    </span>
  );
}

function Sonuclar({ govde }: { readonly govde: RecallGovdesi }) {
  const sonuclar = govde.results;
  const gozlemler = govde.observations;
  const iz = sozluk(govde.trace);
  const ozet = iz === null ? null : sozluk(iz.summary);

  return (
    <div className="flex flex-col gap-4">
      {ozet !== null ? (
        <div className="flex flex-wrap items-center gap-2">
          {/* SAYAÇ ANCAK SAYILABİLİYORSA BASILIR (inceleme M-4): dizi değilse
              önce `0` yazıyordu ve hemen altındaki cümle "tanınmayan bir biçimde
              geldi" diyordu — aynı ekranda iki zıt iddia. */}
          {Array.isArray(sonuclar) ? (
            <Badge variant="outline" className="tabular-nums">
              {sonuclar.length} sonuç
            </Badge>
          ) : (
            <Olculemedi
              neden="Sonuç sayısı okunamadı"
              teknik="sonuç alanı dizi değil — kaç kayıt döndüğü sayılamıyor"
              kisa
            />
          )}
          {sayi(ozet.total_duration_seconds) !== null ? (
            <Badge variant="outline" className="tabular-nums">
              {(sayi(ozet.total_duration_seconds) as number).toLocaleString("tr-TR", {
                maximumFractionDigits: 2,
              })}{" "}
              sn
            </Badge>
          ) : null}
          {sayi(ozet.total_nodes_visited) !== null ? (
            <Badge variant="outline" className="tabular-nums">
              {(sayi(ozet.total_nodes_visited) as number).toLocaleString("tr-TR")} düğüm gezildi
            </Badge>
          ) : null}
        </div>
      ) : null}

      {Array.isArray(gozlemler) && gozlemler.length > 0 ? (
        <Bolme
          baslik="Gözlemler"
          aciklama="Sorguya doğrudan cevap veren türetilmiş kayıtlar; üst yüzey de onları sonuçlardan ayrı çiziyor."
        >
          <div className="flex flex-col gap-2">
            {gozlemler.map((o, i) => (
              <div key={metin(o.id) ?? `gozlem-${i}`} className="rounded-lg border p-3">
                <p className="text-sm">
                  {metin(o.text) ?? (
                    <Olculemedi neden="Gözlem metni gelmedi" teknik="metin alanı gelmedi ya da dizge değil" />
                  )}
                </p>
                <div className="mt-2 flex flex-wrap items-center gap-3 text-[11px] text-muted-foreground">
                  <span className="tabular-nums">
                    {sayi(o.proof_count) === null ? (
                      <Olculemedi neden="Kaynak sayısı gelmedi" teknik="kanıt sayacı gelmedi ya da sayı değil" kisa />
                    ) : (
                      `${(sayi(o.proof_count) as number).toLocaleString("tr-TR")} kaynak`
                    )}
                  </span>
                  <Skor ad="ilgi" deger={o.relevance} />
                </div>
              </div>
            ))}
          </div>
        </Bolme>
      ) : null}

      <Bolme baslik="Sonuçlar" aciklama="Sıra üst servisin sıralamasıdır; ekran yeniden sıralamaz.">
        {!Array.isArray(sonuclar) ? (
          <Olculemedi
            neden="Sonuç listesi tanınmayan bir biçimde geldi"
            teknik="beklenen dizi, gelen başka bir tip — şema sürüklenmiş olabilir"
          />
        ) : sonuclar.length === 0 ? (
          <p className="text-muted-foreground text-sm">
            Bu sorgu okundu ve eşleşen kayıt YOK. Bu ölçülmüş bir boşluktur — "okuyamadım" ile
            aynı şey değildir.
          </p>
        ) : (
          <div className="flex flex-col gap-2">
            {sonuclar.map((r, i) => {
              const skorlar = sozluk(r.scores);
              return (
                <div key={metin(r.id) ?? `sonuc-${i}`} className="rounded-lg border p-3">
                  <div className="flex items-start gap-3">
                    <span className="w-6 shrink-0 text-center font-medium text-muted-foreground text-xs tabular-nums">
                      {i + 1}
                    </span>
                    <div className="min-w-0 flex-1">
                      <p className="text-sm">
                        {metin(r.text) ?? (
                          <Olculemedi neden="Kayıt metni gelmedi" teknik="metin alanı gelmedi ya da dizge değil" />
                        )}
                      </p>
                      <div className="mt-2 flex flex-wrap items-center gap-3 text-[11px] text-muted-foreground">
                        {metin(r.type) !== null ? (
                          <Badge variant="outline" className="font-normal text-[10px]">
                            {metin(r.type)}
                          </Badge>
                        ) : null}
                        {metin(r.context) !== null ? (
                          <span className="max-w-xs truncate" title={metin(r.context) as string}>
                            {metin(r.context)}
                          </span>
                        ) : null}
                        {damga(r.occurred_start) !== null ? <span>{damga(r.occurred_start)}</span> : null}
                      </div>
                      {skorlar === null ? (
                        <div className="mt-1">
                          <Olculemedi
                            neden="Skorlar gelmedi"
                            teknik="skor gövdesi gelmedi ya da sözlük değil — sıralamanın niçin böyle olduğu okunamaz"
                            kisa
                          />
                        </div>
                      ) : (
                        <div className="mt-1 flex flex-wrap gap-x-3">
                          <Skor ad="final" deger={skorlar.final} />
                          <Skor ad="yeniden sıralama" deger={skorlar.reranker} />
                          <Skor ad="anlam" deger={skorlar.semantic} />
                          <Skor ad="kelime" deger={skorlar.keyword} />
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </Bolme>

      <Bolme
        baslik="İstenmeyen bölümler"
        aciklama="Üst yüzeyin ek gövde kutuları bu panoda yok (dosya başlığındaki gerekçe); aşağıdaki iki bölüm bu yüzden BOŞ GELİR — sonuç yok demek DEĞİLDİR."
      >
        <div>
          <Satir etiket="Varlıklar">
            {govde.entities === undefined ? (
              <span className="text-muted-foreground text-xs italic">istenmedi — alan yanıtta yok</span>
            ) : (
              <HamSatirlar govde={{ entities: govde.entities }} />
            )}
          </Satir>
          <Satir etiket="Belge parçaları">
            {govde.chunks === undefined ? (
              <span className="text-muted-foreground text-xs italic">istenmedi — alan yanıtta yok</span>
            ) : (
              <HamSatirlar govde={{ chunks: govde.chunks }} />
            )}
          </Satir>
        </div>
      </Bolme>

      <Bolme
        baslik="Yanıtın tamamı"
        aciklama="Yukarıda kendi biçiminde çizilmeyen ne varsa burada ham adıyla durur — tanınmayan bir alan kaybolmaz."
      >
        <HamSatirlar govde={govde} atla={["results", "observations", "entities", "chunks"]} />
      </Bolme>
    </div>
  );
}

/* --------------------------------------------------------------------------- */

export function Recall({ bank, kayit }: { readonly bank: string | null; readonly kayit: Bolum }) {
  const [sorgu, setSorgu] = useState("");
  const [turler, setTurler] = useState<readonly string[]>(["world"]);
  const [butce, setButce] = useState("mid");
  const [token, setToken] = useState(VARSAYILAN_TOKEN);
  const [damgaKutusu, setDamgaKutusu] = useState("");
  const [etiketler, setEtiketler] = useState("");
  const [esleme, setEsleme] = useState("any");
  const [gozlemTercihi, setGozlemTercihi] = useState(false);

  const [zarf, setZarf] = useState<RecallZarfi | null>(null);
  const [yukleniyor, setYukleniyor] = useState(false);
  const [hata, setHata] = useState<string | null>(null);
  const [oturumDustu, setOturumDustu] = useState(false);
  const [soruldu, setSoruldu] = useState(false);

  const turDegistir = (t: string) =>
    setTurler((mevcut) => (mevcut.includes(t) ? mevcut.filter((x) => x !== t) : [...mevcut, t]));

  const sor = async () => {
    if (bank === null || sorgu.trim() === "" || turler.length === 0) return;
    setYukleniyor(true);
    setHata(null);
    setOturumDustu(false);
    setSoruldu(true);
    /* GÖVDE YALNIZ SORULANI TAŞIR: boş bir alanı göndermek, upstream'in kendi
       varsayılanını sessizce bizim boşluğumuzla değiştirmek olurdu (vekilin
       `max_tokens` şerhindeki ders, düzeltme turu 1 · M-7). */
    const govde: Record<string, unknown> = {
      bank,
      query: sorgu.trim(),
      types: turler,
      budget: butce,
      trace: true,
    };
    const n = Number.parseInt(token, 10);
    if (Number.isFinite(n) && n > 0) govde.max_tokens = n;
    /* SORGU ZAMANI YEREL YAZILIR, UTC GİDER (inceleme I-3).
       `<input type="datetime-local">` değeri saniyesiz ve SAAT DİLİMSİZDİR
       ("2026-09-02T14:30"). Vekil bu alanı beyaz listeden aynen geçiriyor, yani
       ham hâliyle giderse iki sonuç mümkündü ve ikisi de kötüydü: üst servis katı
       ayrıştırıyorsa 422 (görünür), naif damgayı UTC sayıyorsa operatörün yerel
       14:30'u sessizce başka bir ana kayardı — recall'ın zamansal akıl yürütmesi
       başka bir zamana bakardı ve ekranda hiçbir işaret olmazdı. Çevrim burada
       AÇIK yapılıyor; çözülemeyen değer GÖNDERİLMEZ (uydurma yasağı) ve kutunun
       altındaki cümle bunu söyler. */
    if (damgaKutusu !== "") {
      const t = new Date(damgaKutusu);
      if (!Number.isNaN(t.getTime())) govde.query_timestamp = t.toISOString();
    }
    if (gozlemTercihi) govde.prefer_observations = true;
    const etiketListesi = etiketler
      .split(",")
      .map((e) => e.trim())
      .filter((e) => e.length > 0);
    if (etiketListesi.length > 0) {
      govde.tags = etiketListesi;
      govde.tags_match = esleme;
    }
    try {
      setZarf(await recallGonder(govde));
    } catch (e: unknown) {
      if (e instanceof OturumHatasi) {
        setOturumDustu(true);
        setZarf(null);
      } else {
        setHata(e instanceof Error ? e.message : String(e));
      }
    } finally {
      setYukleniyor(false);
    }
  };

  if (bank === null) {
    return (
      <BolumKart kimlik="hafiza-recall" baslik={kayit.baslik} soru={kayit.soru} ikon={kayit.ikon}>
        <Olculemedi
          neden="Sorulacak banka seçilemedi"
          teknik="banka listesi boş ya da okunamadı — yukarıdaki seçici gerekçeyi taşıyor"
        />
      </BolumKart>
    );
  }

  return (
    <BolumKart kimlik="hafiza-recall" baslik={kayit.baslik} soru={kayit.soru} ikon={kayit.ikon}>
      <div className="flex flex-col gap-3">
        <div className="flex flex-wrap items-end gap-2">
          <label className="flex min-w-[16rem] flex-1 flex-col gap-1">
            <span className="text-muted-foreground text-xs">Soru</span>
            <span className="relative">
              <Search
                className="pointer-events-none absolute top-1/2 left-2.5 size-3.5 -translate-y-1/2 text-muted-foreground"
                aria-hidden
              />
              <Input
                value={sorgu}
                onChange={(e) => setSorgu(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") void sor();
                }}
                placeholder="bankaya sorulacak soru"
                className="h-9 pl-8"
              />
            </span>
          </label>
          <Button type="button" className="h-9" disabled={yukleniyor || sorgu.trim() === "" || turler.length === 0} onClick={() => void sor()}>
            {yukleniyor ? "Soruluyor…" : "Sor"}
          </Button>
        </div>

        <div className="flex flex-wrap items-end gap-3">
          <div className="flex flex-col gap-1">
            <span className="text-muted-foreground text-xs">Türler</span>
            <div className="flex h-8 items-center gap-3">
              {TURLER.map((t) => (
                <label key={t.deger} className="flex cursor-pointer items-center gap-1.5 text-sm">
                  <Checkbox
                    checked={turler.includes(t.deger)}
                    onCheckedChange={() => turDegistir(t.deger)}
                    aria-label={t.etiket}
                  />
                  {t.etiket}
                </label>
              ))}
            </div>
          </div>
          <Secim etiket="Bütçe" deger={butce} setDeger={setButce} secenekler={BUTCELER} genislik="w-28" />
          <label className="flex flex-col gap-1">
            <span className="text-muted-foreground text-xs">Yanıt bütçesi (jeton)</span>
            <Input value={token} onChange={(e) => setToken(e.target.value)} className="h-8 w-32" inputMode="numeric" />
          </label>
          <label className="flex flex-col gap-1">
            <span className="text-muted-foreground text-xs">Sorgu zamanı</span>
            <Input
              type="datetime-local"
              value={damgaKutusu}
              onChange={(e) => setDamgaKutusu(e.target.value)}
              className="h-8 w-56"
            />
            <span className="text-[11px] text-muted-foreground">yerel saat → UTC'ye çevrilir</span>
          </label>
          <label className="flex h-8 cursor-pointer items-center gap-1.5 self-end text-sm">
            <Checkbox
              checked={gozlemTercihi}
              onCheckedChange={(c) => setGozlemTercihi(c === true)}
              aria-label="Gözlemleri öne al"
            />
            Gözlemleri öne al
          </label>
        </div>

        <div className="flex flex-wrap items-end gap-3">
          <label className="flex min-w-[14rem] flex-1 flex-col gap-1">
            <span className="text-muted-foreground text-xs">Etiketler (virgülle)</span>
            <Input value={etiketler} onChange={(e) => setEtiketler(e.target.value)} className="h-8" />
          </label>
          {/* EŞLEŞME SÖZLÜĞÜ TEK KAYNAKTAN (`parcalar.tsx::ETIKET_ESLEME`): sunucu
              tanımadığı değeri üst servise göndermiyor, o yüzden burada fazladan
              bir değer düğmeyi çalışır gösterip süzgeci sessizce düşürürdü. */}
          <Secim
            etiket="Etiket eşleşmesi"
            deger={esleme}
            setDeger={setEsleme}
            secenekler={ETIKET_ESLEME.map((e) => ({ deger: e.deger, etiket: e.etiket }))}
            genislik="w-52"
          />
        </div>

        {turler.length === 0 ? (
          <p className="text-destructive text-xs">
            En az bir tür seçili olmalı — türsüz bir sorgu upstream'de hata olur ve sonuç
            listesi "kayıt yok" diye okunurdu
          </p>
        ) : null}
        <p className="text-muted-foreground text-[11px]">
          Yanıt bütçesi SUNUCUDA kırpılır; kutuya tavanın üstünde bir sayı yazmak sessizce
          reddedilmez, kırpılmış hâliyle gider. Kutu boş bırakılırsa alan hiç gönderilmez ve üst
          servisin kendi varsayılanı geçerli olur. Sorgu zamanı kutuya YEREL saatle yazılır ve
          gönderilmeden önce UTC'ye çevrilir; çözülemeyen bir değer hiç gönderilmez.
        </p>
      </div>

      <div className="rounded-md border border-dashed p-3 text-muted-foreground text-xs">
        <span className="font-medium">Bu oyun alanının kapsamı: </span>
        üst yüzeyde bulunan "parçaları da getir" / "varlıkları da getir" kutuları ve zaman
        penceresi burada YOK — o alanlar vekilin beyaz listesinde olmadığı için gönderilseler bile
        üst servise gitmezdi. Çizilmemelerinin sebebi budur; çalışan bir düğme gibi göstermek
        yanıtta hiçbir şeyi değiştirmeyen bir kutu olurdu.
      </div>

      {oturumDustu ? (
        <Olculemedi neden="Oturum düştü" teknik={`${UC_RECALL} 401 döndü — çaresi yeniden giriş`} />
      ) : hata !== null ? (
        <Olculemedi neden="Sorgu okunamadı" teknik={hata} />
      ) : !soruldu ? (
        <p className="text-muted-foreground text-sm">
          Henüz sorulmadı — boş bir sorgu üst servise hiç gitmez, yani bu ekran bir ölçüm sonucu
          göstermiyor
        </p>
      ) : yukleniyor ? (
        <p className="text-muted-foreground text-sm">Soruluyor…</p>
      ) : zarf === null ? null : zarf.neden ? (
        <Olculemedi neden="Sorgu okunamadı" teknik={zarf.neden} />
      ) : zarf.govde === undefined ? (
        <Olculemedi neden="Yanıt bildirilmedi" teknik="uç gövde alanını hiç döndürmedi" />
      ) : zarf.govde === null ? (
        <Olculemedi
          neden="Ölçüm denendi, gövde gelmedi"
          teknik="gövde boş döndü ve gerekçe de taşınmadı"
        />
      ) : (
        <Sonuclar govde={zarf.govde} />
      )}

      {/* ÜST YÜZEYDE BU GÖRÜNÜMDE YAZAN DÜĞME YOK. Boş bir şerit "unutuldu" diye
          okunurdu; bu yüzden yokluğu yazılı. */}
      <div className={cn("flex flex-wrap items-center gap-2")}>
        <Badge variant="outline" className="font-normal text-[11px] text-muted-foreground">
          bu görünümde yazan bir düğme yok — sorgu bir okumadır, durum değiştirmez
        </Badge>
      </div>
    </BolumKart>
  );
}
