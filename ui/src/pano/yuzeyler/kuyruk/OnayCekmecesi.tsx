"use client";

/* ============================================================================
   ONAY ÇEKMECESİ — bir kalemin TAM kanıtı, karar düğmesi OLMADAN
   ----------------------------------------------------------------------------
   NEDEN DÜĞME YOK (brief maddesi, gerekçesi burada yazılı olsun): bu kuyruktaki
   kalemlerin bir kısmı GERİ ALINAMAZ bir icra tetikliyor — `POST /api/plan/{id}/
   onayla` planı silahlı kümeye almakla kalmıyor, ONAY ANINDA aynaya gönderim
   deniyor (api.py; yanıtın `gonderim` alanı bunu beyan ediyor). Bir görev
   listesinin satır sonundaki düğme, "listeyi temizleme" refleksiyle basılan bir
   düğmedir; emir gönderen bir eylem oraya konmaz. Onay kendi turunda, çift onaylı
   bir yüzeyle gelecek.

   ÇEKMECE UYDURMAZ, TAŞIR: her tür kendi ham gövdesini gösterir ve gövdenin
   yazmadığı alan "ölçülemedi + neden" olur. Silahlanma ölçümü ikinci bir uçtan
   (`/api/diagnostics.gatekeeper.arming`) geliyor; o uç düşerse kanıt bloğu boş
   çizilmez, düştüğünü söyler.
   ============================================================================ */
import type { ReactNode } from "react";

import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from "@/components/ui/sheet";

import { Deger, HukumRozet, Olculemedi, Satir, tarihMetni, zamanMetni } from "./parcalar";
import { TUR_ETIKET, type KuyrukOgesi } from "./onaylar";

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

export function OnayCekmecesi({
  oge,
  acik,
  kapat,
}: {
  readonly oge: KuyrukOgesi | null;
  readonly acik: boolean;
  readonly kapat: () => void;
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
                  <Olculemedi neden="uç bu öğede `evidence` alanına metin yazmamış" />
                )}
              </Blok>

              {oge.not ? (
                <Blok baslik="Ucun notu">
                  <p className="rounded-md border border-amber-500/30 bg-amber-500/5 p-3 text-sm leading-6">
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
                <Blok baslik="Silahlanma ölçümü (/api/diagnostics.gatekeeper.arming)">
                  {oge.ayrinti.olcum === null ? (
                    <Olculemedi neden={oge.ayrinti.olcumNeden ?? "ölçüm bulunamadı"} />
                  ) : (
                    <div>
                      <Satir etiket="Kapı hükmü">
                        <HukumRozet
                          ton={silahlanmaTonu(oge.ayrinti.olcum.status)}
                          metin={oge.ayrinti.olcum.status ?? "yazılmamış"}
                          baslik="`measurements[kurulum].status` — kapının kendi hükmü"
                        />
                      </Satir>
                      <Satir etiket="Arama P(ΔS>0)">
                        <Deger deger={oge.ayrinti.olcum.search_p} basamak={4} neden="`search_p` yazılmamış" />
                      </Satir>
                      <Satir etiket="Onay P">
                        <Deger deger={oge.ayrinti.olcum.confirm_p} basamak={4} neden="`confirm_p` yazılmamış" />
                      </Satir>
                      <Satir etiket="Gereken P">
                        <Deger deger={oge.ayrinti.olcum.p_required} basamak={2} neden="`p_required` yazılmamış" />
                      </Satir>
                      <Satir etiket="Kat kazanımı">
                        {oge.ayrinti.olcum.fold_wins ?? <Olculemedi neden="`fold_wins` yazılmamış" kisa />}
                      </Satir>
                      <Satir etiket="OOS (mevcut → aday)">
                        <span className="tabular-nums">
                          <Deger deger={oge.ayrinti.olcum.incumbent_oos} basamak={4} neden="`incumbent_oos` yok" />
                          {" → "}
                          <Deger deger={oge.ayrinti.olcum.candidate_oos} basamak={4} neden="`candidate_oos` yok" />
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
                      <Olculemedi neden="bu kurulum için `cf_report` satırı yok" kisa />
                    ) : (
                      <div>
                        <Satir etiket="n">
                          <Deger deger={oge.ayrinti.cf.n} neden="`n` yazılmamış" />
                        </Satir>
                        <Satir etiket="Kazanma oranı">
                          <Deger deger={oge.ayrinti.cf.win_rate} basamak={3} neden="`win_rate` yazılmamış" />
                        </Satir>
                        <Satir etiket="Ortalama R">
                          <Deger deger={oge.ayrinti.cf.avg_r} basamak={3} neden="`avg_r` yazılmamış" />
                        </Satir>
                      </div>
                    )}
                  </div>
                </Blok>
              ) : null}

              {oge.ayrinti.cesit === "revizyon" ? (
                <Blok baslik="Revizyon kaydı (/api/skills.revisions)">
                  {oge.ayrinti.kayit === null ? (
                    <Olculemedi neden="bu skill için ham revizyon kaydı /api/skills'ten okunamadı" />
                  ) : (
                    <div>
                      <Satir etiket="Durum">
                        {oge.ayrinti.kayit.status ?? <Olculemedi neden="`status` yazılmamış" kisa />}
                      </Satir>
                      <Satir etiket="Taslak damgası">
                        {zamanMetni(oge.ayrinti.kayit.at) ?? <Olculemedi neden="`at` yazılmamış" kisa />}
                      </Satir>
                      <Satir etiket="Taslak uzunluğu">
                        <Deger deger={oge.ayrinti.kayit.chars} birim=" karakter" neden="`chars` yazılmamış" />
                      </Satir>
                      <Satir etiket="Kanıt n">
                        <Deger deger={oge.ayrinti.kayit.evidence?.n} neden="`evidence.n` yazılmamış" />
                      </Satir>
                      <Satir etiket="Kanıt ortalama R">
                        <Deger deger={oge.ayrinti.kayit.evidence?.avg_r} basamak={3} neden="`evidence.avg_r` yazılmamış" />
                      </Satir>
                      <Satir etiket="Karşıolgusal n / R">
                        <span className="tabular-nums">
                          <Deger deger={oge.ayrinti.kayit.evidence?.n_cf} neden="`evidence.n_cf` yazılmamış" />
                          {" / "}
                          <Deger
                            deger={oge.ayrinti.kayit.evidence?.cf_avg_r}
                            basamak={3}
                            neden="`evidence.cf_avg_r` yazılmamış"
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
                <Blok baslik="Eksen-2 önerisi (/api/skills.recommendations)">
                  <div>
                    <Satir etiket="Örneklem (n)">
                      <Deger
                        deger={oge.ayrinti.oge.ornek}
                        neden={oge.ayrinti.oge.ornek_notu ?? "`ornek` alanı yazılmamış"}
                      />
                    </Satir>
                    <Satir etiket="Örneklem yeterli mi">
                      {oge.ayrinti.oge.ornek_yeterli === null || oge.ayrinti.oge.ornek_yeterli === undefined ? (
                        <Olculemedi
                          neden={oge.ayrinti.oge.ornek_notu ?? "`ornek_yeterli` null — ölçülemedi (false DEĞİL)"}
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
                        <Olculemedi neden="uç `uygulanabilir` alanını döndürmedi" kisa />
                      ) : (
                        <HukumRozet
                          ton={oge.ayrinti.oge.uygulanabilir ? "iyi" : "notr"}
                          metin={oge.ayrinti.oge.uygulanabilir ? "uygulayıcısı var" : "uygulayıcısı YOK"}
                          baslik="`skills.eylem_uygulanabilir` — uygulayıcının kendi kümesi"
                        />
                      )}
                    </Satir>
                    <Satir etiket="Kaynak (öneriyi kim yazdı)">
                      {oge.ayrinti.kayit?.source ?? <Olculemedi neden="ham satır `source` taşımıyor" kisa />}
                    </Satir>
                  </div>
                  {oge.ayrinti.karar !== null ? (
                    <div className="mt-2 rounded-md border bg-muted/30 p-3">
                      <h5 className="text-muted-foreground text-[11px] uppercase">Karar kaydı</h5>
                      <Satir etiket="Karar">
                        {oge.ayrinti.karar.karar === undefined ? (
                          <Olculemedi neden="`karar_kaydi.karar` alanı yok" kisa />
                        ) : oge.ayrinti.karar.karar === null ? (
                          <span className="text-muted-foreground text-xs">karar YOK — hâlâ bekliyor</span>
                        ) : (
                          <Badge variant="outline">{oge.ayrinti.karar.karar}</Badge>
                        )}
                      </Satir>
                      <Satir etiket="Karar damgası">
                        {zamanMetni(oge.ayrinti.karar.ts) ?? <Olculemedi neden="karar damgası yok" kisa />}
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

              {oge.ayrinti.cesit === "plan" ? (
                <Blok baslik="Plan (/api/today.todays_plans)">
                  <div>
                    <Satir etiket="Sembol">
                      {oge.ayrinti.plan.ticker ?? <Olculemedi neden="`ticker` yazılmamış" kisa />}
                    </Satir>
                    <Satir etiket="Kurulum">
                      {oge.ayrinti.plan.setup ?? <Olculemedi neden="`setup` yazılmamış" kisa />}
                    </Satir>
                    <Satir etiket="Sektör">
                      {oge.ayrinti.plan.sector ?? <Olculemedi neden="`sector` yazılmamış" kisa />}
                    </Satir>
                    <Satir etiket="Skor">
                      <Deger deger={oge.ayrinti.plan.score} basamak={3} neden="`score` yazılmamış" />
                    </Satir>
                    <Satir etiket="Giriş tetiği">
                      <Deger deger={oge.ayrinti.plan.entry_trigger} basamak={2} neden="`entry_trigger` yazılmamış" />
                    </Satir>
                    <Satir etiket="Son kapanış">
                      <Deger
                        deger={oge.ayrinti.plan.last_close}
                        basamak={2}
                        neden="`last_close` yok — bar CSV'si okunamadı"
                      />
                    </Satir>
                    <Satir etiket="Tetikten sapma">
                      <Deger
                        deger={oge.ayrinti.plan.drift_pct}
                        birim="%"
                        basamak={2}
                        neden="`drift_pct` yok — tetik 0 ya da yazılmamış"
                      />
                    </Satir>
                    <Satir etiket="Risk büyüklüğü (R)">
                      <Deger deger={oge.ayrinti.plan.size_r} basamak={2} neden="`size_r` yazılmamış" />
                    </Satir>
                    <Satir etiket="LLM vetosu">
                      {oge.ayrinti.plan.llm_veto === undefined ? (
                        <Olculemedi neden="`llm_veto` alanı yok" kisa />
                      ) : (
                        <HukumRozet
                          ton={oge.ayrinti.plan.llm_veto ? "kotu" : "notr"}
                          metin={oge.ayrinti.plan.llm_veto ? "VETO" : "veto yok"}
                          baslik="`llm_veto` — ikinci beynin reddi"
                        />
                      )}
                    </Satir>
                  </div>
                  {oge.ayrinti.plan.gate_reasons && oge.ayrinti.plan.gate_reasons.length > 0 ? (
                    <div className="mt-2">
                      <h5 className="text-muted-foreground text-[11px] uppercase">Kapı gerekçeleri</h5>
                      <ul className="mt-1 list-disc pl-5 text-sm leading-6">
                        {oge.ayrinti.plan.gate_reasons.map((r) => (
                          <li key={r}>{r}</li>
                        ))}
                      </ul>
                    </div>
                  ) : null}
                  {oge.ayrinti.plan.llm_opinion ? (
                    <p className="mt-2 whitespace-pre-wrap rounded-md border bg-muted/30 p-3 text-sm leading-6">
                      {oge.ayrinti.plan.llm_opinion}
                    </p>
                  ) : null}
                </Blok>
              ) : null}

              {oge.ayrinti.cesit === "bilinmeyen" ? (
                <Blok baslik="Tanınmayan tür — ham gövde">
                  <pre className="overflow-x-auto rounded-md border bg-muted/30 p-3 text-[11px] leading-5">
                    {JSON.stringify(oge.ayrinti.oge, null, 2)}
                  </pre>
                </Blok>
              ) : null}
            </div>
          </>
        )}
      </SheetContent>
    </Sheet>
  );
}
