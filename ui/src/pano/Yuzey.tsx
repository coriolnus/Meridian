"use client";

/* ============================================================================
   YÜZEY SEÇİCİ — rotanın işaret ettiği gövdeyi çizer
   ----------------------------------------------------------------------------
   TABLO AÇIK VE EKSİKSİZ: on yedi yüzeyin hepsi burada adıyla var ve hiçbiri
   `?? GenelYuzey` gibi sessiz bir yedeğe düşmüyor. Sessiz yedek olsaydı UNUTULAN
   bir yüzey ile BİLEREK ertelenmiş bir yüzey ekranda aynı görünürdü — ve hangisinin
   hangisi olduğu yalnız git geçmişinden okunabilirdi. `Record<YuzeyAnahtari, ...>`
   tipi ayrıca derleme anında zorluyor: `alanlar.ts`e yeni bir yüzey eklendiğinde
   burası da yazılmadan derleme GEÇMEZ.

   `GenelYuzey` artık yalnız bir YEDEK değil, bir ARAÇ: gövdesi henüz yazılmamış bir
   yüzeyi ekranda "taşınmadı" diye sayar. Bugün hiçbir yüzey ona bağlı değil.
   ============================================================================ */
import type { ComponentType } from "react";

import type { YuzeyAnahtari } from "./alanlar";
import { useRota } from "./rota";
import { Ajan } from "./yuzeyler/Ajan";
import { AnalizYuzey } from "./yuzeyler/AnalizYuzey";
import { Antrenman } from "./yuzeyler/Antrenman";
import { Belgeler } from "./yuzeyler/Belgeler";
import { BugunYuzeyi } from "./yuzeyler/BugunYuzeyi";
import { Cizelge } from "./yuzeyler/Cizelge";
import { Giris } from "./yuzeyler/Giris";
import { HafizaYuzey } from "./yuzeyler/hafiza/HafizaYuzey";
import { KanbanYuzey } from "./yuzeyler/KanbanYuzey";
import { KapiYuzey } from "./yuzeyler/kapi/KapiYuzey";
import { Kullanicilar } from "./yuzeyler/Kullanicilar";
import { Ogrenme } from "./yuzeyler/Ogrenme";
import { OnayKuyrugu } from "./yuzeyler/OnayKuyrugu";
import { Operator } from "./yuzeyler/Operator";
import { PortfoyYuzey } from "./yuzeyler/PortfoyYuzey";
import { Roller } from "./yuzeyler/Roller";
import { SistemSagligiYuzey } from "./yuzeyler/SistemSagligiYuzey";

const GOVDELER: Record<YuzeyAnahtari, ComponentType> = {
  default: BugunYuzeyi,
  finance: PortfoyYuzey,
  analytics: AnalizYuzey,
  productivity: Antrenman,
  academy: Ogrenme,
  infrastructure: SistemSagligiYuzey,
  gateway: KapiYuzey,
  memory: HafizaYuzey,
  "file-manager": Belgeler,
  chat: Ajan,
  calendar: Cizelge,
  kanban: KanbanYuzey,
  tasks: OnayKuyrugu,
  profile: Operator,
  users: Kullanicilar,
  roles: Roller,
  authentication: Giris,
};

export function Yuzey() {
  const { yuzey } = useRota();
  const Govde = GOVDELER[yuzey];
  return <Govde />;
}
