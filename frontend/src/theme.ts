// Brand tokens + light/dark theming for CreativeIQ.
//
// Single source of truth = PALETTES. applyTheme() writes them onto <html> as CSS
// variables consumed by tailwind.config.js (so utilities like bg-panel, text-ink
// follow the active mode) and index.css (body bg). Brand accents (teal,
// terracotta) read well on both modes and stay constant.
//
// Design note: `ink` and `offwhite` are a CONTRAST PAIR — ink = "dark thing"
// (primary text + dark chips), offwhite = "light thing" (page bg + on-accent
// text). In dark mode they swap, so `bg-ink text-offwhite` (active nav, format
// chip) stays a readable inverted pill in both modes.

export type Mode = "light" | "dark";

const PALETTES: Record<Mode, Record<string, string>> = {
  light: {
    offwhite: "#F6F2EA", // page bg + on-accent text
    sand: "#E8DFD2",
    panel: "#FFFFFF", // card surface
    panel2: "#EFE7DA", // secondary surface (warm)
    line: "#E0D8C9", // borders
    teal: "#5C8A8A",
    tealDeep: "#3F6B6B",
    terracotta: "#C97B5A",
    ink: "#2B2B28", // primary text + dark chips
    stone: "#9A9387", // muted text
  },
  dark: {
    offwhite: "#17160F", // page bg (deep warm charcoal)
    sand: "#221F18",
    panel: "#211E17", // card surface
    panel2: "#2A271E", // secondary surface
    line: "#3A352B", // borders
    teal: "#6FA3A3", // brand, lifted for dark contrast
    tealDeep: "#5C9090",
    terracotta: "#DB8E6C", // brand, lifted
    ink: "#F1EADC", // primary text (warm off-white) + light chips
    stone: "#A89F8E", // muted text
  },
};

// Per-segment accent — slightly lifted in dark for contrast.
const SEGMENT_ACCENTS: Record<Mode, Record<string, string>> = {
  light: {
    "genz-instagram": "#C97B5A",
    "millennials-email": "#3F6B6B",
    "genx-display": "#9A9387",
    "professionals-social": "#5C8A8A",
  },
  dark: {
    "genz-instagram": "#DB8E6C",
    "millennials-email": "#5C9090",
    "genx-display": "#A89F8E",
    "professionals-social": "#6FA3A3",
  },
};

const EXTRAS: Record<Mode, Record<string, string>> = {
  light: {
    "--header-bg": "rgba(246,242,234,0.9)",
    "--card-shadow": "0 10px 40px -12px rgba(43,43,40,0.25)",
  },
  dark: {
    "--header-bg": "rgba(23,22,15,0.9)",
    "--card-shadow": "0 10px 40px -12px rgba(0,0,0,0.6)",
  },
};

const STORAGE_KEY = "ciq-theme";
const DEFAULT_MODE: Mode = "light";

let _mode: Mode = readInitial();

function readInitial(): Mode {
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved === "light" || saved === "dark") return saved;
  } catch {
    /* ignore */
  }
  return DEFAULT_MODE;
}

function toRgbChannels(hex: string): string {
  const h = hex.replace("#", "");
  return `${parseInt(h.slice(0, 2), 16)} ${parseInt(h.slice(2, 4), 16)} ${parseInt(h.slice(4, 6), 16)}`;
}

export function applyTheme(mode: Mode): void {
  _mode = mode;
  const root = document.documentElement;
  const p = PALETTES[mode];
  for (const k in p) {
    root.style.setProperty(`--${k}`, p[k]);
    root.style.setProperty(`--${k}-rgb`, toRgbChannels(p[k]));
  }
  const ex = EXTRAS[mode];
  for (const k in ex) root.style.setProperty(k, ex[k]);
  root.dataset.theme = mode;
  root.style.colorScheme = mode;
  try {
    localStorage.setItem(STORAGE_KEY, mode);
  } catch {
    /* ignore */
  }
}

export const getMode = (): Mode => _mode;
export const toggleMode = (): Mode => {
  const next: Mode = _mode === "dark" ? "light" : "dark";
  applyTheme(next);
  return next;
};

// ---------------------------------------------------------------------------
// Static brand metadata (unchanged) + helpers
// ---------------------------------------------------------------------------
export const BRAND = {
  name: "Lumen & Coast",
  tagline: "Coastal resort-wear",
};

export const segmentAccent = (id: string): string =>
  SEGMENT_ACCENTS[_mode][id] || PALETTES[_mode].teal;

// Back-compat: components import SEGMENT_ACCENT as a map. Expose a Proxy that
// reads the live mode so existing `SEGMENT_ACCENT[id]` lookups stay theme-aware.
export const SEGMENT_ACCENT = new Proxy({} as Record<string, string>, {
  get: (_t, key: string) => segmentAccent(key),
});

export const FORMAT_ASPECT: Record<string, string> = {
  social_square: "1 / 1",
  email_hero: "16 / 9",
  display_banner: "1200 / 628",
  story: "9 / 16",
};

export const FORMAT_LABEL: Record<string, string> = {
  social_square: "Social · Square",
  email_hero: "Email · Hero",
  display_banner: "Display · Banner",
  story: "Story · Vertical",
};

export const TOUCH = "min-h-[48px] min-w-[48px]";

applyTheme(_mode);
