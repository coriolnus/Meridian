const THEME_MODE_OPTIONS = [
  { label: "Light", value: "light" },
  { label: "Dark", value: "dark" },
  { label: "System", value: "system" },
] as const;

export const THEME_MODE_VALUES = THEME_MODE_OPTIONS.map((o) => o.value);
export type ThemeMode = (typeof THEME_MODE_VALUES)[number];
export type ResolvedThemeMode = "light" | "dark";

// --- generated:themePresets:start ---

export const THEME_PRESET_OPTIONS = [
  {
    label: "Default",
    value: "default",
    primary: {
      light: "oklch(0.205 0 0)",
      dark: "oklch(0.922 0 0)",
    },
  },
  {
    label: "Brutalist",
    value: "brutalist",
    primary: {
      light: "oklch(0.6489 0.237 26.9728)",
      dark: "oklch(0.7044 0.1872 23.1858)",
    },
  },
  {
    label: "Soft Pop",
    value: "soft-pop",
    primary: {
      light: "oklch(0.5106 0.2301 276.9656)",
      dark: "oklch(0.6801 0.1583 276.9349)",
    },
  },
  {
    label: "Tangerine",
    value: "tangerine",
    primary: {
      light: "oklch(0.64 0.17 36.44)",
      dark: "oklch(0.64 0.17 36.44)",
    },
  },
  {
    // TSK-136, 2026-09-04: eski TSK-117 rezerve-hue palet turu preset oldu. Bu preset
    // shadcn'in --primary'sine DOKUNMAZ (yalnız Meridian'ın kendi rol jetonlarını
    // değiştirir, bkz. ui/src/styles/presets/meridian-palet.css) — swatch'ta öteki üç
    // preset gibi "gerçek --primary" göstermek yerine preset'in ölçülebilir en belirgin
    // kimliği seçildi: rezerve seri rampasının ilk basamağı (--seri-6 = teal), aynı zamanda
    // huni-1'in kaynağı. Değer Tailwind theme.css'ten ÖLÇÜLDÜ (--color-teal-600/-400 oklch).
    label: "Meridian Palet",
    value: "meridian-palet",
    primary: {
      light: "oklch(0.60 0.118 184.704)",
      dark: "oklch(0.777 0.152 181.912)",
    },
  },
] as const;

export const THEME_PRESET_VALUES = THEME_PRESET_OPTIONS.map((p) => p.value);

export type ThemePreset = (typeof THEME_PRESET_OPTIONS)[number]["value"];

// --- generated:themePresets:end ---
