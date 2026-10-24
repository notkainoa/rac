// rac's space themes, copied from the browser so the drawings tint exactly
// like the real window. Source: chrome/browser/rac/spaces/space.cc (presets)
// and chrome/browser/ui/views/rac/spaces/space_tint_background.cc (how
// they're painted), both added by patches/rac/spaces/.

export interface Preset {
  name: string;
  swatch: string;
  light: [string, string];
  dark: [string, string];
}

export const presets: Preset[] = [
  { name: "Neutral", swatch: "#262626", light: ["#FFFFD7", "#FFD9FB"], dark: ["#516CD3", "#FFD9FB"] },
  { name: "Red", swatch: "#C1575C", light: ["#C1575C", "#FCD098"], dark: ["#CC4A55", "#632E20"] },
  { name: "Orange", swatch: "#D87249", light: ["#D87249", "#FFD1B1"], dark: ["#C95125", "#65251A"] },
  { name: "Yellow", swatch: "#E3AC38", light: ["#E3AC38", "#F9E6C0"], dark: ["#C98400", "#60371E"] },
  { name: "Green", swatch: "#3EB489", light: ["#3EB489", "#C8E8AD"], dark: ["#008B5D", "#00544D"] },
  { name: "Blue", swatch: "#3A88C4", light: ["#3A88C4", "#CFEFE9"], dark: ["#007FBD", "#004263"] },
  { name: "Pink", swatch: "#D37B8B", light: ["#D37B8B", "#D4D5F0"], dark: ["#BD556B", "#4E5081"] },
  { name: "Purple", swatch: "#5F5B9E", light: ["#5F5B9E", "#E2BEBF"], dark: ["#625DA5", "#562F43"] },
];

// kColorRacSpaceTintLight / Dark: the gradient's alpha over the base.
const ALPHA = { light: 0x4d / 255, dark: 0x2e / 255 };

function rgba(hex: string, a: number) {
  const n = parseInt(hex.slice(1), 16);
  return `rgb(${n >> 16} ${(n >> 8) & 255} ${n & 255} / ${a.toFixed(3)})`;
}

// The window wash: Neutral is a flat gray; every other preset is a diagonal
// gradient between its two stops over white (light) or #1C1A1F (dark).
export function tint(index: number, dark: boolean): string {
  if (index === 0) return dark ? "#181818" : "#E6E6E6";
  const p = presets[index];
  const [a, b] = dark ? p.dark : p.light;
  const alpha = dark ? ALPHA.dark : ALPHA.light;
  return `linear-gradient(to bottom right, ${rgba(a, alpha)}, ${rgba(b, alpha)}), ${dark ? "#1C1A1F" : "#FFFFFF"}`;
}

// The selected tab is white in light mode. In dark mode it's black on a
// colored wash, and an opaque gray on Neutral's flat #181818.
export function selectedTab(index: number, dark: boolean): string {
  if (!dark) return "#FFFFFF";
  return index === 0 ? "#424242" : "#000000";
}

export type Mode = "auto" | "light" | "dark";
