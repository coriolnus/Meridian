"use client";

/* ============================================================================
   YÜZEY SEÇİCİ — rotanın işaret ettiği gövdeyi çizer
   ----------------------------------------------------------------------------
   TABLO AÇIK VE EKSİKSİZ: on beş yüzeyin hepsi burada adıyla var. Bir yüzeyin
   kendi gövdesi henüz yazılmadıysa `GenelYuzey`e düşer ve ekranda "taşınmadı"
   yazar. Sessiz bir `?? GenelYuzey` yazsaydık, unutulan bir yüzey ile bilerek
   ertelenmiş bir yüzey AYNI görünürdü — ve hangisinin hangisi olduğu yalnız
   git geçmişinden okunabilirdi.
   ============================================================================ */
import type { ComponentType } from "react";

import type { YuzeyAnahtari } from "./alanlar";
import { useRota } from "./rota";
import { GenelYuzey } from "./yuzeyler/GenelYuzey";

const GOVDELER: Record<YuzeyAnahtari, ComponentType> = {
  default: GenelYuzey,
  finance: GenelYuzey,
  analytics: GenelYuzey,
  productivity: GenelYuzey,
  academy: GenelYuzey,
  infrastructure: GenelYuzey,
  "file-manager": GenelYuzey,
  chat: GenelYuzey,
  calendar: GenelYuzey,
  kanban: GenelYuzey,
  tasks: GenelYuzey,
  profile: GenelYuzey,
  users: GenelYuzey,
  roles: GenelYuzey,
  authentication: GenelYuzey,
};

export function Yuzey() {
  const { yuzey } = useRota();
  const Govde = GOVDELER[yuzey];
  return <Govde />;
}
