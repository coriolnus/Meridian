"use client";

/* ============================================================================
   ONAY ÇEKMECESİ — bir kalemin TAM kanıtı, ve ALTINDA çift adımlı karar
   ----------------------------------------------------------------------------
   TARİHÇE-KORU (v-önceki tur): burada "karar düğmesi YOK" yazıyordu ve gerekçesi
   şuydu: bu kuyruktaki kalemlerin bir kısmı GERİ ALINAMAZ bir icra tetikliyor —
   `POST /api/plan/{id}/onayla` planı silahlı kümeye almakla kalmıyor, ONAY ANINDA
   aynaya gönderim deniyor. O gerekçe DOĞRUYDU ve HÂLÂ GEÇERLİ; yanlış olan sonuçtu
   — operatör kararı veremez hâle geldi ("review butonuna basınca onaylayabilmem
   için bir ekran açılması gerekli", 2026-08-25).

   ÇÖZÜM DÜĞMEYİ SATIRA KOYMAK DEĞİL: düğme hâlâ görev listesinin satır sonunda
   DEĞİL. Satırdaki eylem yalnız "İncele" — kalemin TAM kanıtını açar. Karar,
   kanıtın ALTINDA, çift adımlı ve iki tık arasında ne olacağı yazılı olarak durur
   (`KararPaneli.tsx`). "Listeyi temizleme" refleksiyle basılabilecek tek tık
   ortadan kalktı; kaybolan karar yolu geri geldi.

   ÇEKMECE UYDURMAZ, TAŞIR: her tür kendi ham gövdesini gösterir ve gövdenin
   yazmadığı alan "ölçülemedi + neden" olur. Silahlanma ölçümü ikinci bir uçtan
   (`/api/diagnostics.gatekeeper.arming`) geliyor; o uç düşerse kanıt bloğu boş
   çizilmez, düştüğünü söyler.
   ============================================================================ */
import type { ReactNode } from "react";

import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from "@/components/ui/sheet";

import { KararPaneli } from "./KararPaneli";
import { Deger, HukumRozet, Olculemedi, Satir, tarihMetni, zamanMetni } from "./parcalar";
import type { KapiKontrolu, PlanAyrintisi } from "./onayEylem";
import { TUR_ETIKET, type KuyrukOgesi } from "./onaylar";
import type { PlanOzeti } from "./tipler";

/** Silahlanma ölçümünün `status` alanı bir HÜKÜMDÜR; tonu burada tek yerde eşlenir. */
function silahlanmaTonu(durum: string | undefined): "iyi" | "kotu" | "notr" {
  if (durum === "gate_passed") return "iyi";
  if (durum === "gate_rejected") return "kotu";
  return "notr";
}

function Blok({ baslik, children }: { readonly baslik: string; readonly children: ReactNode }) {
  return (
    <section className="flex flex-col gap-1">
      <h4 className="font-medium text-muted-foreground text-xs uppercase tracking-wide">{baslik}</h4>
      {children}
    </section>
  );
}

/** `gate_checks[].value` sayı da olabilir metin de (`"industrials"`) — tipe göre basılır, zorlanmaz. */
function kontrolDegeri(v: unknown): string {
  if (v === null || v === undefined) return "—";
  if (typeof v === "number") return Number.isFinite(v) ? v.toLocaleString("tr-TR") : String(v);
  if (typeof v === "boolean") return v ? "evet" : "hayır";
  if (typeof v === "string") return v;
  return JSON.stringify(v);
}

/**
 * KAPI DÖKÜMÜ — "düştüğü/geçtiği kapılar" sorusunun tam cevabı.
 * `gate_reasons` yalnız DÜŞENLERİN metnini taşıyor; `gate_checks` ise HER kontrolü
 * (geçen/düşen · sert/yumuşak · ölçülen değer · eşik) tek tek taşıyor. Operatör
 * neyi onayladığını görecekse, geçen kapıları da görmeli: "yalnız düşenleri göster"
 * bir onay ekranında, kararın dayandığı zemini gizlemek olurdu.
 */
function KapiDokumu({ kontroller }: { readonly kontroller: readonly KapiKontrolu[] }) {
  const dusen = kontroller.filter((k) => k.passed === false);
  const gecen = kontroller.filter((k) => k.passed === true);
  const belirsiz = kontroller.filter((k) => k.passed !== true && k.passed !== false);
  return (
    <div className="flex flex-col gap-2">
      <div className="flex flex-wrap gap-1.5">
        <HukumRozet
          ton={dusen.length === 0 ? "iyi" : "kotu"}
          metin={`${dusen.length} düştü`}
          baslik="`gate_checks[].passed === false` sayısı"
        />
        <HukumRozet ton="notr" metin={`${gecen.length} geçti`} baslik="`gate_checks[].passed === true` sayısı" />
        {belirsiz.length > 0 ? (
          <HukumRozet
            ton="olculemedi"
            metin={`${belirsiz.length} ölçülemedi`}
            baslik="`passed` alanı true/false değil — kontrolün kararı bu satırdan okunamıyor"
          />
        ) : null}
      </div>
      <ul className="flex flex-col gap-1">
        {[...dusen, ...belirsiz, ...gecen].map((k, i) => (
          <li
            key={`${k.check ?? "?"}-${i}`}
            className={
              k.passed === false
                ? "rounded-md border border-destructive/30 bg-destructive/5 p-2"
                : "rounded-md border p-2"
            }
          >
            <div className="flex flex-wrap items-baseline gap-x-2 gap-y-0.5">
              <code className="font-mono text-xs">{k.check ?? "(adsız kontrol)"}</code>
              <Badge variant="outline" className="text-[10px]">
                {k.severity ?? "şiddet yazılmamış"}
              </Badge>
              <span className="text-muted-foreground text-[11px]">
                {k.passed === true ? "geçti" : k.passed === false ? "DÜŞTÜ" : "karar okunamadı"}
              </span>
              <span className="ml-auto tabular-nums text-[11px]">
                {kontrolDegeri(k.value)} {k.threshold ? `↔ ${k.threshold}` : "(eşik yazılmamış)"}
              </span>
            </div>
            {k.note ? <p className="mt-1 text-sm leading-5">{k.note}</p> : null}
          </li>
        ))}
      </ul>
    </div>
  );
}

/**
 * PLANIN TAM KÜNYESİ — "neyi onaylıyorum" sorusunun tek satırlık özetten FAZLASI.
 *
 * ALANLAR ÖLÇÜLDÜ (`state/trade_plans.jsonl` anahtar birleşimi, `onayEylem.ts`
 * başlığında liste). `PlanOzeti` bu alanların yalnız bir kesitini tanıyor ve o tip
 * Çizelge ile PAYLAŞILAN `tipler.ts`te yaşıyor (imzası bozulmaz) — bu yüzden
 * genişletilmiş kesit `onayEylem.ts::PlanAyrintisi`de duruyor ve daraltma burada
 * yapılıyor. Daraltma bir İDDİA DEĞİL: eklenen alanların HEPSİ opsiyonel, yani
 * gelmeyen alan `undefined` kalır ve ekranda "ölçülemedi + neden" olur.
 *
 * ADET VE `risk_dollars` BU SATIRDA YOK: `broker.py::PaperBroker.size_position`
 * ikisini de GÖNDERİM ANINDA öz sermayeden hesaplıyor. Yokluk yazılır, türetilmez.
 */
function PlanBloku({ plan }: { readonly plan: PlanOzeti }) {
  const p = plan as PlanAyrintisi;
  // HİSSE BAŞINA RİSK TÜRETİLİR VE TÜRETİLDİĞİ SÖYLENİR: tetik ve stop ÖLÇÜLMÜŞ iki
  // alan; farkları planın kendi tanımladığı 1R'lik mesafedir. Uydurma değil aritmetik —
  // ama etiketi "türetildi" der, çünkü uç bu sayıyı YAZMIYOR.
  const birimRisk =
    typeof p.entry_trigger === "number" && typeof p.stop === "number" && Number.isFinite(p.entry_trigger - p.stop)
      ? p.entry_trigger - p.stop
      : null;
  return (
    <Blok baslik="Plan (/api/today.todays_plans)">
      <div>
        <Satir etiket="Sembol">{p.ticker ?? <Olculemedi neden="Sembol kaydedilmemiş" teknik="`ticker` yazılmamış" kisa />}</Satir>
        <Satir etiket="Yön">{p.side ?? <Olculemedi neden="İşlem yönü kaydedilmemiş" teknik="`side` yazılmamış" kisa />}</Satir>
        <Satir etiket="Kurulum">{p.setup ?? <Olculemedi neden="Kurulum adı kaydedilmemiş" teknik="`setup` yazılmamış" kisa />}</Satir>
        <Satir etiket="Sektör">{p.sector ?? <Olculemedi neden="Sektör kaydedilmemiş" teknik="`sector` yazılmamış" kisa />}</Satir>
        <Satir etiket="Plan kimliği">
          {p.id ? (
            <code className="break-all font-mono text-xs">{p.id}</code>
          ) : (
            <Olculemedi neden="Plan kimliği yok — bu plan onaylanamaz" teknik="`id` yazılmamış — onay ucu bu plana çağrılamaz" kisa />
          )}
        </Satir>
        <Satir etiket="Seans tarihi">{p.date ?? <Olculemedi neden="Seans tarihi kaydedilmemiş" teknik="`date` yazılmamış" kisa />}</Satir>
        <Satir etiket="Skor">
          <Deger deger={p.score} basamak={3} neden="Plan skoru kaydedilmemiş" teknik="`score` yazılmamış" />
        </Satir>
        <Satir etiket="Rejim (plan anı)">
          {p.regime_at_plan ?? <Olculemedi neden="Plan anındaki piyasa rejimi kaydedilmemiş" teknik="`regime_at_plan` yazılmamış" kisa />}
        </Satir>
      </div>

      <div className="mt-2">
        <h5 className="text-muted-foreground text-[11px] uppercase">Seviyeler ve risk</h5>
        <Satir etiket="Giriş tetiği">
          <Deger deger={p.entry_trigger} basamak={2} neden="Giriş tetiği kaydedilmemiş" teknik="`entry_trigger` yazılmamış" />
        </Satir>
        <Satir etiket="Stop">
          <Deger deger={p.stop} basamak={2} neden="Stop seviyesi kaydedilmemiş" teknik="`stop` yazılmamış" />
        </Satir>
        <Satir etiket="Kâr hedefi">
          <Deger deger={p.profit_target} basamak={2} neden="Kâr hedefi kaydedilmemiş" teknik="`profit_target` yazılmamış" />
        </Satir>
        <Satir etiket="Beklenen R katsayısı">
          <Deger deger={p.r_multiple_expected} basamak={2} neden="Beklenen R katsayısı kaydedilmemiş" teknik="`r_multiple_expected` yazılmamış" />
        </Satir>
        <Satir etiket="Risk büyüklüğü (R)">
          <Deger deger={p.size_r} basamak={2} neden="Risk büyüklüğü kaydedilmemiş" teknik="`size_r` yazılmamış" />
        </Satir>
        <Satir etiket="Hisse başına risk (türetildi)">
          {birimRisk === null ? (
            <Olculemedi neden="Tetik ya da stop yok — hisse başına risk hesaplanamadı" teknik="`entry_trigger − stop` hesaplanamaz" kisa />
          ) : (
            <span className="tabular-nums" title="türetildi: entry_trigger − stop (uç bu alanı yazmıyor)">
              {birimRisk.toLocaleString("tr-TR", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </span>
          )}
        </Satir>
        <Satir etiket="Risk (dolar)">
          <Olculemedi neden="Dolar riski planda yazmaz — gönderim anında hesaplanır" teknik="`risk_dollars` plan satırında yok — broker.size_position onu gönderim anında öz sermayeden hesaplar" />
        </Satir>
        <Satir etiket="Adet (lot)">
          <Olculemedi neden="Adet planda yazmaz — gönderim anında hesaplanır" teknik="plan satırı adet taşımıyor — lot gönderim anında hesaplanır (broker.size_position)" />
        </Satir>
        <Satir etiket="Son kapanış">
          <Deger deger={p.last_close} basamak={2} neden="Son kapanış fiyatı okunamadı" teknik="`last_close` yok — bar CSV'si okunamadı" />
        </Satir>
        <Satir etiket="Tetikten sapma">
          <Deger deger={p.drift_pct} birim="%" basamak={2} neden="Fiyatın tetikten sapması hesaplanamadı" teknik="`drift_pct` yok — tetik 0 ya da yazılmamış" />
        </Satir>
      </div>

      <div className="mt-2">
        <h5 className="text-muted-foreground text-[11px] uppercase">Karar ve ikinci model</h5>
        <Satir etiket="Kontrol kararı">
          {p.gate_verdict ?? <Olculemedi neden="Kontrollerin kararı kaydedilmemiş" teknik="`gate_verdict` yazılmamış" kisa />}
        </Satir>
        <Satir etiket="Süresi doldu mu">
          {p.expired === undefined ? (
            <Olculemedi neden="Planın süresinin dolup dolmadığı bildirilmedi" teknik="`expired` alanı yok — bayatlık ölçülemedi" kisa />
          ) : (
            <HukumRozet
              ton={p.expired ? "kotu" : "notr"}
              metin={p.expired ? "SÜRESİ DOLDU" : "seansı geçmemiş"}
              baslik="`expired` — süresi dolmuş plan onaylanamaz (uç 409 verir)"
            />
          )}
        </Satir>
        <Satir etiket="LLM vetosu">
          {p.llm_veto === undefined ? (
            <Olculemedi neden="İkinci beynin veto verip vermediği bildirilmedi" teknik="`llm_veto` alanı yok" kisa />
          ) : (
            <HukumRozet
              ton={p.llm_veto ? "kotu" : "notr"}
              metin={p.llm_veto ? "VETO" : "veto yok"}
              baslik="`llm_veto` — ikinci beynin reddi"
            />
          )}
        </Satir>
        <Satir etiket="Uyuyan kurulum">
          {p.dormant_setup === undefined ? (
            <Olculemedi neden="Kurulumun uykuda olup olmadığı bildirilmedi" teknik="`dormant_setup` alanı yok" kisa />
          ) : (
            <span className="text-xs">{p.dormant_setup ? "evet — icraya bağlı olmayan kurulum" : "hayır"}</span>
          )}
        </Satir>
        <Satir etiket="Strateji sürümü">
          <Deger deger={p.strategy_version} neden="Strateji sürümü kaydedilmemiş" teknik="`strategy_version` yazılmamış" />
        </Satir>
        <Satir etiket="Deneme p(kazanç)">
          <Deger deger={p.p_win_shadow} basamak={3} neden="Denemedeki kazanma olasılığı kaydedilmemiş" teknik="`p_win_shadow` yazılmamış" />
        </Satir>
        <Satir etiket="Broker durumu">
          {p.broker_status ?? <Olculemedi neden="Broker durumu kaydedilmemiş" teknik="`broker_status` yazılmamış" kisa />}
        </Satir>
      </div>

      {p.skill_chain && p.skill_chain.length > 0 ? (
        <div className="mt-2">
          <h5 className="text-muted-foreground text-[11px] uppercase">Skill zinciri (planı kim kurdu)</h5>
          <div className="mt-1 flex flex-wrap gap-1">
            {p.skill_chain.map((s) => (
              <Badge key={s} variant="secondary" className="font-mono text-[10px]">
                {s}
              </Badge>
            ))}
          </div>
        </div>
      ) : null}

      <div className="mt-2">
        <h5 className="text-muted-foreground text-[11px] uppercase">Kapılar — geçen ve düşen</h5>
        {p.gate_checks && p.gate_checks.length > 0 ? (
          <div className="mt-1">
            <KapiDokumu kontroller={p.gate_checks} />
          </div>
        ) : (
          <Olculemedi neden="Tek tek kontrol sonuçları kaydedilmemiş" teknik="plan satırı `gate_checks` taşımıyor" />
        )}
      </div>

      {p.gate_reasons && p.gate_reasons.length > 0 ? (
        <div className="mt-2">
          <h5 className="text-muted-foreground text-[11px] uppercase">Kontrol gerekçeleri (kararın metni)</h5>
          <ul className="mt-1 list-disc pl-5 text-sm leading-6">
            {p.gate_reasons.map((r) => (
              <li key={r}>{r}</li>
            ))}
          </ul>
        </div>
      ) : null}

      {p.llm_opinion ? (
        <p className="mt-2 whitespace-pre-wrap rounded-md border bg-muted/30 p-3 text-sm leading-6">
          {p.llm_opinion}
        </p>
      ) : null}
    </Blok>
  );
}

export function OnayCekmecesi({
  oge,
  acik,
  kapat,
  seviye,
  seviyeNeden,
  halt,
  broker,
  mod,
  tazele,
}: {
  readonly oge: KuyrukOgesi | null;
  readonly acik: boolean;
  readonly kapat: () => void;
  /** `/api/approvals.level` — `undefined` = ölçülemedi (L0 DEĞİL). */
  readonly seviye: number | undefined;
  readonly seviyeNeden: string;
  readonly halt: boolean | undefined;
  readonly broker: string | undefined;
  readonly mod: string | undefined;
  /** Karar gönderildikten SONRA kuyruğu yeniden okur (iyimser güncelleme yok). */
  readonly tazele: () => void;
}) {
  return (
    <Sheet open={acik} onOpenChange={(a) => (a ? undefined : kapat())}>
      <SheetContent side="right" className="w-full sm:max-w-xl">
        {oge === null ? (
          <>
            <SheetHeader>
              <SheetTitle>Kalem seçilmedi</SheetTitle>
              <SheetDescription>Tablodan bir satıra tıkla.</SheetDescription>
            </SheetHeader>
          </>
        ) : (
          <>
            <SheetHeader className="pr-10">
              <div className="flex flex-wrap items-center gap-2">
                <Badge variant="outline">{TUR_ETIKET[oge.tur]}</Badge>
                {oge.isIstiyor ? (
                  <HukumRozet ton="uyari" metin="iş istiyor" baslik="sunucunun `inbox_count` ölçütüne göre bekliyor" />
                ) : (
                  <HukumRozet
                    ton="notr"
                    metin="iş istemiyor"
                    baslik={oge.durgunNeden ?? "karar verilmiş — satır kayıt olarak duruyor"}
                  />
                )}
              </div>
              <SheetTitle className="text-base leading-6">{oge.baslik}</SheetTitle>
              <SheetDescription className="font-mono text-[11px]">{oge.kimlik}</SheetDescription>
            </SheetHeader>

            <div className="flex min-h-0 flex-1 flex-col gap-4 overflow-y-auto px-4 pb-6">
              <Blok baslik="Künye">
                <div>
                  <Satir etiket="Konu">
                    {oge.konu ?? <Olculemedi neden={oge.konuNeden} kisa />}
                  </Satir>
                  <Satir etiket="Kuyruğa geldi">
                    {/* Saati olmayan kaynağa saat basılmaz (bkz. `onaylar.ts` → `gelisSaatli`). */}
                    {(oge.gelisSaatli ? zamanMetni(oge.gelisIso) : tarihMetni(oge.gelisIso)) ?? (
                      <Olculemedi neden={oge.gelisNeden} kisa />
                    )}
                  </Satir>
                  <Satir etiket="Ne bekliyor">
                    <span className="text-sm">{oge.bekleyen}</span>
                  </Satir>
                  <Satir etiket="Uçtaki eylemler">
                    {oge.eylemler.length === 0 ? (
                      <span className="text-muted-foreground text-xs">
                        yok — uç bu öğeye uygulanabilir eylem yazmamış
                      </span>
                    ) : (
                      <span className="flex flex-wrap justify-end gap-1">
                        {oge.eylemler.map((e) => (
                          <Badge key={e} variant="secondary" className="font-mono text-[10px]">
                            {e}
                          </Badge>
                        ))}
                      </span>
                    )}
                  </Satir>
                </div>
                {oge.gelisIso !== null ? (
                  <p className="text-muted-foreground text-[11px] leading-4">{oge.gelisNeden}</p>
                ) : null}
              </Blok>

              <Blok baslik="Kanıt (uç ne yazdıysa)">
                {oge.kanit ? (
                  <p className="whitespace-pre-wrap rounded-md border bg-muted/30 p-3 text-sm leading-6">{oge.kanit}</p>
                ) : (
                  <Olculemedi neden="Bu kalem için kanıt metni kaydedilmemiş" teknik="uç bu öğede `evidence` alanına metin yazmamış" />
                )}
              </Blok>

              {oge.not ? (
                <Blok baslik="Ucun notu">
                  <p className="rounded-md border border-uyari-h bg-uyari-t p-3 text-sm leading-6">
                    {oge.not}
                  </p>
                </Blok>
              ) : null}

              {oge.durgunNeden ? (
                <Blok baslik="Neden iş istemiyor">
                  <p className="rounded-md border bg-muted/30 p-3 text-sm leading-6">{oge.durgunNeden}</p>
                </Blok>
              ) : null}

              <Separator />

              {/* ---- TÜRE ÖZEL KANIT ------------------------------------- */}
              {oge.ayrinti.cesit === "silahlanma" ? (
                <Blok baslik="İşleme hazırlık ölçümü (/api/diagnostics.gatekeeper.arming)">
                  {oge.ayrinti.olcum === null ? (
                    <Olculemedi neden={oge.ayrinti.olcumNeden ?? "Bu kurulum için ölçüm bulunamadı"} />
                  ) : (
                    <div>
                      <Satir etiket="Kontrol kararı">
                        <HukumRozet
                          ton={silahlanmaTonu(oge.ayrinti.olcum.status)}
                          metin={oge.ayrinti.olcum.status ?? "yazılmamış"}
                          baslik="`measurements[kurulum].status` — kontrolün kendi kararı"
                        />
                      </Satir>
                      <Satir etiket="Arama P(ΔS>0)">
                        <Deger deger={oge.ayrinti.olcum.search_p} basamak={4} neden="Arama olasılığı kaydedilmemiş" teknik="`search_p` yazılmamış" />
                      </Satir>
                      <Satir etiket="Onay P">
                        <Deger deger={oge.ayrinti.olcum.confirm_p} basamak={4} neden="Onay olasılığı kaydedilmemiş" teknik="`confirm_p` yazılmamış" />
                      </Satir>
                      <Satir etiket="Gereken P">
                        <Deger deger={oge.ayrinti.olcum.p_required} basamak={2} neden="Gereken olasılık eşiği kaydedilmemiş" teknik="`p_required` yazılmamış" />
                      </Satir>
                      <Satir etiket="Doğrulama dilimi kazancı">
                        {oge.ayrinti.olcum.fold_wins ?? <Olculemedi neden="Doğrulama dilimi kazancı kaydedilmemiş" teknik="`fold_wins` yazılmamış" kisa />}
                      </Satir>
                      <Satir etiket="OOS (mevcut → aday)">
                        <span className="tabular-nums">
                          <Deger deger={oge.ayrinti.olcum.incumbent_oos} basamak={4} neden="Mevcut kurulumun sonucu kaydedilmemiş" teknik="`incumbent_oos` yok" />
                          {" → "}
                          <Deger deger={oge.ayrinti.olcum.candidate_oos} basamak={4} neden="Aday kurulumun sonucu kaydedilmemiş" teknik="`candidate_oos` yok" />
                        </span>
                      </Satir>
                      {oge.ayrinti.olcum.why ? (
                        <p className="mt-2 rounded-md border bg-muted/30 p-3 text-sm leading-6">
                          {oge.ayrinti.olcum.why}
                        </p>
                      ) : null}
                    </div>
                  )}
                  <div className="mt-2">
                    <h5 className="text-muted-foreground text-[11px] uppercase">Karşıolgusal defter (cf_report)</h5>
                    {oge.ayrinti.cf === null ? (
                      <Olculemedi neden="Bu kurulum için karşıolgusal kayıt yok" teknik="bu kurulum için `cf_report` satırı yok" kisa />
                    ) : (
                      <div>
                        <Satir etiket="n">
                          <Deger deger={oge.ayrinti.cf.n} neden="Örneklem sayısı kaydedilmemiş" teknik="`n` yazılmamış" />
                        </Satir>
                        <Satir etiket="Kazanma oranı">
                          <Deger deger={oge.ayrinti.cf.win_rate} basamak={3} neden="Kazanma oranı kaydedilmemiş" teknik="`win_rate` yazılmamış" />
                        </Satir>
                        <Satir etiket="Ortalama R">
                          <Deger deger={oge.ayrinti.cf.avg_r} basamak={3} neden="Ortalama R kaydedilmemiş" teknik="`avg_r` yazılmamış" />
                        </Satir>
                      </div>
                    )}
                  </div>
                </Blok>
              ) : null}

              {oge.ayrinti.cesit === "revizyon" ? (
                <Blok baslik="Revizyon kaydı (/api/skills.revisions)">
                  {oge.ayrinti.kayit === null ? (
                    <Olculemedi neden="Bu skill'in revizyon kaydı okunamadı" teknik="bu skill için ham revizyon kaydı /api/skills'ten okunamadı" />
                  ) : (
                    <div>
                      <Satir etiket="Durum">
                        {oge.ayrinti.kayit.status ?? <Olculemedi neden="Revizyonun durumu kaydedilmemiş" teknik="`status` yazılmamış" kisa />}
                      </Satir>
                      <Satir etiket="Taslak damgası">
                        {zamanMetni(oge.ayrinti.kayit.at) ?? <Olculemedi neden="Taslağın yazılma zamanı kaydedilmemiş" teknik="`at` yazılmamış" kisa />}
                      </Satir>
                      <Satir etiket="Taslak uzunluğu">
                        <Deger deger={oge.ayrinti.kayit.chars} birim=" karakter" neden="Taslak uzunluğu kaydedilmemiş" teknik="`chars` yazılmamış" />
                      </Satir>
                      <Satir etiket="Kanıt n">
                        <Deger deger={oge.ayrinti.kayit.evidence?.n} neden="Kanıt örneklem sayısı kaydedilmemiş" teknik="`evidence.n` yazılmamış" />
                      </Satir>
                      <Satir etiket="Kanıt ortalama R">
                        <Deger deger={oge.ayrinti.kayit.evidence?.avg_r} basamak={3} neden="Kanıtın ortalama R değeri kaydedilmemiş" teknik="`evidence.avg_r` yazılmamış" />
                      </Satir>
                      <Satir etiket="Karşıolgusal n / R">
                        <span className="tabular-nums">
                          <Deger deger={oge.ayrinti.kayit.evidence?.n_cf} neden="Karşıolgusal örneklem sayısı kaydedilmemiş" teknik="`evidence.n_cf` yazılmamış" />
                          {" / "}
                          <Deger
                            deger={oge.ayrinti.kayit.evidence?.cf_avg_r}
                            basamak={3}
                            neden="Karşıolgusal ortalama R kaydedilmemiş" teknik="`evidence.cf_avg_r` yazılmamış"
                          />
                        </span>
                      </Satir>
                      {oge.ayrinti.kayit.rationale ? (
                        <p className="mt-2 rounded-md border bg-muted/30 p-3 text-sm leading-6">
                          {oge.ayrinti.kayit.rationale}
                        </p>
                      ) : null}
                    </div>
                  )}
                </Blok>
              ) : null}

              {oge.ayrinti.cesit === "oneri" ? (
                <Blok baslik="Beceri önerisi (/api/skills.recommendations)">
                  <div>
                    <Satir etiket="Örneklem (n)">
                      <Deger
                        deger={oge.ayrinti.oge.ornek}
                        neden={oge.ayrinti.oge.ornek_notu ?? "Örneklem sayısı kaydedilmemiş"}
                        teknik="`ornek` alanı yazılmamış"
                      />
                    </Satir>
                    <Satir etiket="Örneklem yeterli mi">
                      {oge.ayrinti.oge.ornek_yeterli === null || oge.ayrinti.oge.ornek_yeterli === undefined ? (
                        <Olculemedi
                          neden={oge.ayrinti.oge.ornek_notu ?? "Örneklemin yeterli olup olmadığı bildirilmedi"}
                          teknik="`ornek_yeterli` null — ölçülemedi (false değil)"
                          kisa
                        />
                      ) : (
                        <HukumRozet
                          ton={oge.ayrinti.oge.ornek_yeterli ? "iyi" : "uyari"}
                          metin={oge.ayrinti.oge.ornek_yeterli ? "eşiği geçti" : "eşiğin altında"}
                          baslik="öneri metnini LLM yazıyor; künye metnin YANINDA durur, İÇİNDE değil"
                        />
                      )}
                    </Satir>
                    <Satir etiket="Uygulanabilir mi">
                      {oge.ayrinti.oge.uygulanabilir === undefined ? (
                        <Olculemedi neden="Önerinin uygulanabilir olup olmadığı bildirilmedi" teknik="uç `uygulanabilir` alanını döndürmedi" kisa />
                      ) : (
                        <HukumRozet
                          ton={oge.ayrinti.oge.uygulanabilir ? "iyi" : "notr"}
                          metin={oge.ayrinti.oge.uygulanabilir ? "uygulayıcısı var" : "uygulayıcısı YOK"}
                          baslik="`skills.eylem_uygulanabilir` — uygulayıcının kendi kümesi"
                        />
                      )}
                    </Satir>
                    <Satir etiket="Kaynak (öneriyi kim yazdı)">
                      {oge.ayrinti.kayit?.source ?? <Olculemedi neden="Öneriyi kimin yazdığı kaydedilmemiş" teknik="ham satır `source` taşımıyor" kisa />}
                    </Satir>
                  </div>
                  {oge.ayrinti.karar !== null ? (
                    <div className="mt-2 rounded-md border bg-muted/30 p-3">
                      <h5 className="text-muted-foreground text-[11px] uppercase">Karar kaydı</h5>
                      <Satir etiket="Karar">
                        {oge.ayrinti.karar.karar === undefined ? (
                          <Olculemedi neden="Kararın ne olduğu bildirilmedi" teknik="`karar_kaydi.karar` alanı yok" kisa />
                        ) : oge.ayrinti.karar.karar === null ? (
                          <span className="text-muted-foreground text-xs">karar YOK — hâlâ bekliyor</span>
                        ) : (
                          <Badge variant="outline">{oge.ayrinti.karar.karar}</Badge>
                        )}
                      </Satir>
                      <Satir etiket="Karar damgası">
                        {zamanMetni(oge.ayrinti.karar.ts) ?? <Olculemedi neden="Kararın zamanı kaydedilmemiş" teknik="karar damgası yok" kisa />}
                      </Satir>
                      {oge.ayrinti.karar.gerekce ? (
                        <p className="mt-2 text-sm leading-6">{oge.ayrinti.karar.gerekce}</p>
                      ) : null}
                      {oge.ayrinti.karar.not ? (
                        <p className="mt-2 text-muted-foreground text-[11px] leading-4">{oge.ayrinti.karar.not}</p>
                      ) : null}
                    </div>
                  ) : null}
                </Blok>
              ) : null}

              {oge.ayrinti.cesit === "plan" ? <PlanBloku plan={oge.ayrinti.plan} /> : null}

              {oge.ayrinti.cesit === "bilinmeyen" ? (
                <Blok baslik="Tanınmayan tür — ham gövde">
                  <pre className="overflow-x-auto rounded-md border bg-muted/30 p-3 text-[11px] leading-5">
                    {JSON.stringify(oge.ayrinti.oge, null, 2)}
                  </pre>
                </Blok>
              ) : null}

              <Separator />

              {/* ---- KARAR: kanıtın ALTINDA, çift adımlı --------------------
                  `key` KALEM KİMLİĞİ: çekmece açıkken başka bir satıra geçilirse
                  panelin iç durumu (birinci tık alınmış "teyit" aşaması, yazılmış
                  gerekçe, önceki yanıt) SIFIRLANMALI. Aksi hâlde A kalemi için
                  alınmış bir niyet, B kalemi açıldığında ekranda duruyor olurdu —
                  ve ikinci tık B'yi gönderirdi. */}
              <KararPaneli
                key={oge.kimlik}
                oge={oge}
                seviye={seviye}
                seviyeNeden={seviyeNeden}
                halt={halt}
                broker={broker}
                mod={mod}
                tazele={tazele}
              />
            </div>
          </>
        )}
      </SheetContent>
    </Sheet>
  );
}
