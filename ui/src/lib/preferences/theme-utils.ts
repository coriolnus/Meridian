import type { ResolvedThemeMode, ThemeMode } from "./theme";

function resolveThemeMode(mode: ThemeMode): ResolvedThemeMode {
  if (mode === "system") {
    const prefersDark = typeof window !== "undefined" && window.matchMedia?.("(prefers-color-scheme: dark)")?.matches;
    return prefersDark ? "dark" : "light";
  }
  return mode === "dark" ? "dark" : "light";
}

export function applyThemeMode(mode: ThemeMode): ResolvedThemeMode {
  const resolved = resolveThemeMode(mode);
  const doc = document.documentElement;
  doc.setAttribute("data-theme-mode", mode);
  doc.classList.add("disable-transitions");
  doc.classList.toggle("dark", resolved === "dark");
  // İKİ MEKANİZMA BİLEREK YAN YANA: şablon `.dark` SINIFINI okur
  // (`@custom-variant dark (&:is(.dark *))`, tema.css), Meridian'ın diğer üç yüzeyi
  // — landing / workflow / runbook, hepsi `theme.js` ile — `data-theme` NİTELİĞİNİ
  // okur. Göç bitene kadar ikisi de yazılır; yazılmasaydı panodan tema değiştiren
  // operatör landing'e geçtiğinde ESKİ temayı bulurdu (sessiz, hatasız, yanlış).
  //
  // DEĞERLER ŞABLONUNKİ DEĞİL: `theme.js` "gunduz"/"gece" okur, "light"/"dark" DEĞİL
  // (meridian/web/theme.js:29-30). Buraya `light` yazmak niteliği doldurur ama eski
  // yüzeylerin CSS'i onu TANIMAZ — hata yok, tema yok. Ölçülmeden yazılamayacak satır.
  doc.setAttribute("data-theme", resolved === "dark" ? "gece" : "gunduz");
  doc.style.colorScheme = resolved;
  requestAnimationFrame(() => {
    doc.classList.remove("disable-transitions");
  });
  return resolved;
}

export function subscribeToSystemTheme(onChange: (mode: ResolvedThemeMode) => void): () => void {
  if (typeof window === "undefined") return () => undefined;
  const media = window.matchMedia?.("(prefers-color-scheme: dark)");
  if (!media) return () => undefined;

  const listener = (event: MediaQueryListEvent) => {
    onChange(event.matches ? "dark" : "light");
  };

  media.addEventListener("change", listener);

  return () => {
    media.removeEventListener("change", listener);
  };
}
