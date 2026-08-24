"use client";

/* ============================================================================
   PLAN KARTI — bir adayın kapı hikâyesi tek karede
   ----------------------------------------------------------------------------
   Kart gramerini şablonun kanban `task-card.tsx`inden aldık (başlık satırı +
   rozet, iki satır açıklama, ayraç, alt şerit). DEĞİŞEN: şablonun kartı
   sürüklenebilir; bu kart DEĞİL ve olmamalı — bir kartı elle başka kolona
   taşımak, kapının verdiği HÜKMÜ elle değiştirmek olurdu. Hüküm `guard.classify_gate`
   çıktısıdır; pano onu gösterir, kurmaz.

   "DÜŞTÜĞÜ KAPI" satırının dört ayrı cevabı var (bkz. `planlar.ts::dustuguKapi`) ve
   dördü de ayrı çiziliyor: ölçülemeyeni "—" ile geçmek, kapının o planda hiç
   yazılmadığını "sorun yok" diye okutur.
   ============================================================================ */
import { CircleSlash, Compass, Gavel, ShieldX, TrendingDown, TrendingUp } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { cn } from "@/lib/utils";

import { Olculemedi } from "./Hal";
import { dustuguKapi, type Plan } from "./planlar";

function skorMetni(s: number | null): string {
  if (s === null) return "";
  // Skor ondalıklı geliyor (`score` alanı); iki hane operatörün eski panoda gördüğü
  // hassasiyetle aynı. Yuvarlamayı burada yapıyoruz ki sıralama HAM skorla kalsın.
  return s.toFixed(2);
}

export function PlanKarti({ p }: { p: Plan }) {
  const kapi = dustuguKapi(p);

  return (
    <article className="flex flex-col gap-3 rounded-xl border bg-card p-4 text-card-foreground shadow-xs">
      <div className="min-w-0 space-y-1.5">
        <div className="flex items-center justify-between gap-3">
          <h3 className="min-w-0 truncate font-medium text-sm leading-none">
            {p.sembol ?? <span className="text-muted-foreground">sembolsüz plan satırı</span>}
          </h3>
          {p.skor === null ? (
            <Olculemedi kisa neden="plan satırında `score` alanı yok — skorsuz plan" />
          ) : (
            <Badge variant="outline" className="shrink-0 tabular-nums" title="kapı skoru (`score`)">
              {skorMetni(p.skor)}
            </Badge>
          )}
        </div>
        <p className="truncate text-muted-foreground text-sm leading-5">
          {p.kurulum ?? "kurulum yazılmamış"}
          {p.sektor ? ` · ${p.sektor}` : ""}
        </p>
      </div>

      <div className="flex flex-col gap-1.5 rounded-lg bg-muted/40 p-2.5">
        <span className="flex items-center gap-1.5 text-muted-foreground text-xs leading-none">
          <Gavel className="size-3" aria-hidden />
          düştüğü kapı
        </span>
        {kapi.tur === "olculdu" ? (
          <div className="space-y-1">
            <code className="break-all font-mono text-[11px] text-destructive">{kapi.ad}</code>
            {kapi.siddet ? (
              <Badge variant="ghost" className="ml-1 h-4 px-1 text-[10px]">
                {kapi.siddet}
              </Badge>
            ) : null}
            {kapi.not ? <p className="text-muted-foreground text-xs leading-4">{kapi.not}</p> : null}
          </div>
        ) : kapi.tur === "hepsi_gecti" ? (
          <p className="text-muted-foreground text-xs leading-4">
            {kapi.n} kapının hepsi geçti — hüküm kapı satırlarından gelmiyor
            {p.gerekceler && p.gerekceler.length > 0 ? `; gerekçe: ${p.gerekceler[0]}` : ""}
          </p>
        ) : (
          <p className="text-muted-foreground text-xs leading-4">
            <CircleSlash className="mr-1 inline size-3 align-[-2px]" aria-hidden />
            {kapi.neden}
          </p>
        )}
      </div>

      {p.gerekceler && p.gerekceler.length > 0 && kapi.tur !== "hepsi_gecti" ? (
        <ul className="space-y-1">
          {p.gerekceler.slice(0, 3).map((g) => (
            <li key={g} className="text-muted-foreground text-xs leading-4">
              · {g}
            </li>
          ))}
          {p.gerekceler.length > 3 ? (
            <li className="text-muted-foreground text-xs leading-4">
              · +{p.gerekceler.length - 3} gerekçe daha
            </li>
          ) : null}
        </ul>
      ) : null}

      <Separator />

      <div className="flex flex-wrap items-center gap-1.5">
        {p.kesif === true ? (
          <Badge variant="secondary" className="gap-1" title="keşif kotasından açılan plan (`exploration`)">
            <Compass className="size-3" aria-hidden />
            keşif
          </Badge>
        ) : null}
        {p.llmVeto === true ? (
          <Badge variant="destructive" className="gap-1" title="LLM danışma katmanı veto koydu (`llm_veto`)">
            <ShieldX className="size-3" aria-hidden />
            LLM veto
          </Badge>
        ) : null}
        {p.onayBekliyor === true ? (
          <Badge variant="default" title="REVIEW planı operatör onayında (`onay_bekliyor`)">
            onayında
          </Badge>
        ) : null}
        {p.onaylandi ? (
          <Badge variant="secondary" title="operatör onayı yazılmış (`operator_onayi`)">
            onaylandı
          </Badge>
        ) : null}
        {p.islendi === true ? (
          <Badge variant="secondary" title="bu plandan işlem açılmış (`traded`)">
            işlendi
          </Badge>
        ) : null}
        {p.bayat === true ? (
          <Badge variant="outline" title="planın seansı geçmiş (`expired`)">
            bayat{p.yasGun === null ? "" : ` · ${p.yasGun}g`}
          </Badge>
        ) : null}
        {p.sapmaYuzde === null ? null : (
          <Badge
            variant="ghost"
            className={cn(
              "gap-1 tabular-nums",
              p.sapmaYuzde >= 0 ? "text-emerald-600 dark:text-emerald-400" : "text-red-600 dark:text-red-400",
            )}
            title="son kapanışın giriş tetiğinden sapması (`drift_pct`)"
          >
            {p.sapmaYuzde >= 0 ? (
              <TrendingUp className="size-3" aria-hidden />
            ) : (
              <TrendingDown className="size-3" aria-hidden />
            )}
            {p.sapmaYuzde.toFixed(1)}%
          </Badge>
        )}
      </div>
    </article>
  );
}
