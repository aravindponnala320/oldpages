/**
 * OldPages design tokens.
 *
 * Single source of truth for colors, spacing, radii, typography, shadows.
 * Every UI primitive and page pulls from here so the theme stays uniform.
 */

export const colors = {
  // Surfaces
  bg:            "#f5f6f8",   // page background
  surface:       "#ffffff",   // card / header background
  surfaceMuted:  "#f9fafb",   // subtle fills
  border:        "#eef0f3",   // hairline separators
  borderStrong:  "#e5e7eb",   // stronger separators
  divider:       "#f3f4f6",

  // Text
  text:          "#111827",
  textMuted:     "#374151",
  textSubtle:    "#6b7280",
  textFaint:     "#9ca3af",
  textInverse:   "#ffffff",

  // Brand
  primary:       "#2563eb",   // blue
  primaryHover:  "#1d4ed8",
  primarySoft:   "#eaf2ff",
  primaryStrong: "#1e40af",

  // Semantic
  success:       "#16a34a",
  successSoft:   "#dcfce7",
  successText:   "#166534",

  warning:       "#f59e0b",
  warningSoft:   "#fef3c7",
  warningText:   "#92400e",

  danger:        "#dc2626",
  dangerSoft:    "#fee2e2",
  dangerText:    "#991b1b",

  info:          "#0284c7",
  infoSoft:      "#e0f2fe",
  infoText:      "#075985",

  // Category pastels (match demo header)
  catPink:       "#fce7f3",
  catBlue:       "#dbeafe",
  catGreen:      "#dcfce7",
  catOrange:     "#ffedd5",
  catPurple:     "#ede9fe",
  catYellow:     "#fef3c7",

  // Feature-card pastels
  featPurple:    "#f5f0ff",
  featBlue:      "#eaf2ff",
  featGreen:     "#e6f7ee",
  featPink:      "#ffe9ee",
} as const;

export const space = {
  0:  "0px",
  1:  "4px",
  2:  "8px",
  3:  "12px",
  4:  "16px",
  5:  "20px",
  6:  "24px",
  7:  "28px",
  8:  "32px",
  10: "40px",
  12: "48px",
  16: "64px",
  20: "80px",
} as const;

export const radius = {
  none: "0",
  sm:   "4px",
  md:   "6px",
  lg:   "10px",
  xl:   "12px",
  "2xl":"16px",
  pill: "999px",
  full: "50%",
} as const;

export const font = {
  family: "system-ui, -apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif",
  size: {
    xs:   "11px",
    sm:   "12px",
    base: "14px",
    md:   "15px",
    lg:   "16px",
    xl:   "18px",
    "2xl":"22px",
    "3xl":"28px",
    "4xl":"36px",
  },
  weight: {
    normal:   400,
    medium:   500,
    semibold: 600,
    bold:     700,
    heavy:    800,
  },
  lineHeight: {
    tight:  1.2,
    snug:   1.35,
    normal: 1.5,
    relaxed: 1.65,
  },
} as const;

export const shadow = {
  none: "none",
  sm:   "0 1px 2px rgba(15, 23, 42, 0.05)",
  md:   "0 4px 12px rgba(15, 23, 42, 0.06)",
  lg:   "0 8px 24px rgba(15, 23, 42, 0.10)",
  primary: "0 6px 16px rgba(37, 99, 235, 0.35)",
} as const;

export const layout = {
  maxWidth: 1440,
  gutter:   40,
  gutterSm: 20,
  headerHeight: 74,
  bottomNavHeight: 68,
} as const;

export const zIndex = {
  base:      0,
  raised:    10,
  overlay:   40,
  header:    50,
  bottomNav: 50,
  modal:     100,
  toast:     200,
} as const;

/** Merge helper for style objects. Last object wins. */
export function sx<T extends React.CSSProperties>(...parts: (T | undefined | false)[]): T {
  return Object.assign({}, ...parts.filter(Boolean)) as T;
}
