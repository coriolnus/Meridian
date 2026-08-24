import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import "./stil.css";
import { App } from "./pano/App";

const kok = document.getElementById("kok");
if (!kok) throw new Error("#kok yok — sayfa iskeleti değişmiş");
createRoot(kok).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
