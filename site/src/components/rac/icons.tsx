import type { ReactNode, SVGProps } from "react";

// Line icons drawn to match rac's toolbar and sidebar glyphs.
const line = (path: ReactNode, props: SVGProps<SVGSVGElement> = {}) => (
  <svg
    viewBox="0 0 20 20"
    fill="none"
    stroke="currentColor"
    strokeWidth={1.6}
    strokeLinecap="round"
    strokeLinejoin="round"
    aria-hidden="true"
    {...props}
  >
    {path}
  </svg>
);

export const SidebarIcon = (p: SVGProps<SVGSVGElement>) =>
  line(
    <>
      <rect x="2.5" y="3.5" width="15" height="13" rx="2.6" />
      <path d="M7.5 3.5v13" />
    </>,
    p,
  );
export const BackIcon = (p: SVGProps<SVGSVGElement>) => line(<path d="M16 10H4.5M9 5 4 10l5 5" />, p);
export const ForwardIcon = (p: SVGProps<SVGSVGElement>) => line(<path d="M4 10h11.5M11 5l5 5-5 5" />, p);
export const ReloadIcon = (p: SVGProps<SVGSVGElement>) =>
  line(<path d="M16 10a6 6 0 1 1-1.8-4.3M16 3.5v3.7h-3.7" />, p);
export const ChevronIcon = ({ flip, ...p }: SVGProps<SVGSVGElement> & { flip?: boolean }) =>
  line(<path d={flip ? "M12 4.5 6.5 10l5.5 5.5" : "M8 4.5l5.5 5.5L8 15.5"} />, p);
export const PlusIcon = (p: SVGProps<SVGSVGElement>) => line(<path d="M10 4v12M4 10h12" />, p);
export const CloseIcon = (p: SVGProps<SVGSVGElement>) => line(<path d="m5.5 5.5 9 9m0-9-9 9" />, { strokeWidth: 1.9, ...p });
export const ProfileIcon = (p: SVGProps<SVGSVGElement>) =>
  line(
    <>
      <circle cx="10" cy="10" r="7.5" />
      <circle cx="10" cy="8.3" r="2.6" />
      <path d="M5.2 15.5c1.1-1.9 2.8-2.8 4.8-2.8s3.7.9 4.8 2.8" />
    </>,
    p,
  );
export const MoreIcon = (p: SVGProps<SVGSVGElement>) => (
  <svg viewBox="0 0 20 20" fill="currentColor" aria-hidden="true" {...p}>
    <circle cx="10" cy="4.5" r="1.5" />
    <circle cx="10" cy="10" r="1.5" />
    <circle cx="10" cy="15.5" r="1.5" />
  </svg>
);
export const TuneIcon = (p: SVGProps<SVGSVGElement>) =>
  line(<path d="M3.5 6h8m3 0h2M3.5 14h2m3 0h8M11.5 4v4M5.5 12v4" />, p);
export const ShieldIcon = (p: SVGProps<SVGSVGElement>) =>
  line(<path d="M10 2.8 4 5v4.6c0 3.6 2.6 6.4 6 7.6 3.4-1.2 6-4 6-7.6V5l-6-2.2Z" />, p);
export const PuzzleIcon = (p: SVGProps<SVGSVGElement>) =>
  line(
    <path d="M7.5 4.5h2.2a1.6 1.6 0 1 1 3.2 0h2.6v3a1.6 1.6 0 1 1 0 3.2v3.8h-3.3a1.6 1.6 0 1 0-3.2 0H4.5v-3.3a1.6 1.6 0 1 0 0-3.2V4.5h3Z" />,
    p,
  );
export const SunIcon = (p: SVGProps<SVGSVGElement>) =>
  line(
    <>
      <circle cx="10" cy="10" r="3.2" />
      <path d="M10 2.5v1.6M10 15.9v1.6M2.5 10h1.6M15.9 10h1.6M4.7 4.7l1.1 1.1M14.2 14.2l1.1 1.1M4.7 15.3l1.1-1.1M14.2 5.8l1.1-1.1" />
    </>,
    p,
  );
export const MoonIcon = (p: SVGProps<SVGSVGElement>) =>
  line(<path d="M16 12.3A6.5 6.5 0 0 1 7.7 4a6.5 6.5 0 1 0 8.3 8.3Z" />, p);
export const AutoIcon = (p: SVGProps<SVGSVGElement>) => (
  <svg viewBox="0 0 20 20" aria-hidden="true" {...p}>
    <circle cx="10" cy="10" r="6.5" fill="none" stroke="currentColor" strokeWidth="1.6" />
    <path d="M10 3.5a6.5 6.5 0 0 1 0 13Z" fill="currentColor" />
  </svg>
);
export const SearchIcon = (p: SVGProps<SVGSVGElement>) =>
  line(
    <>
      <circle cx="8.8" cy="8.8" r="5" />
      <path d="m12.6 12.6 4 4" />
    </>,
    p,
  );
export const CheckIcon = (p: SVGProps<SVGSVGElement>) => line(<path d="m4.5 10.5 3.5 3.5 7.5-8" />, { strokeWidth: 2, ...p });
export const SendIcon = (p: SVGProps<SVGSVGElement>) => line(<path d="M10 16V4.5M5 9.5l5-5 5 5" />, { strokeWidth: 1.9, ...p });
// Chromium's chat icon, which rac's Chat button uses: a speech bubble with
// three lines of text.
export const ChatIcon = (p: SVGProps<SVGSVGElement>) =>
  line(
    <>
      <path d="M3.5 2.75h13a.75.75 0 0 1 .75.75v10a.75.75 0 0 1-.75.75H5.4l-2.65 2.65V3.5a.75.75 0 0 1 .75-.75Z" />
      <path d="M6 6.3h8M6 9h8M6 11.7h5" />
    </>,
    { strokeWidth: 1.5, ...p },
  );
export const SparkIcon = (p: SVGProps<SVGSVGElement>) => (
  <svg viewBox="0 0 20 20" fill="currentColor" aria-hidden="true" {...p}>
    <path d="M10 2.5c.5 3.6 1.9 5 5.5 5.5-3.6.5-5 1.9-5.5 5.5-.5-3.6-1.9-5-5.5-5.5 3.6-.5 5-1.9 5.5-5.5Z" />
  </svg>
);

// A stand-in site icon: a colored rounded square with a simple mark. No real
// site's logo, so the drawings never borrow anyone's brand.
export type Glyph = "dot" | "ring" | "tri" | "bars" | "square" | "wave" | "half" | "plus" | "leaf" | "drop";

const marks: Record<Glyph, ReactNode> = {
  dot: <circle cx="8" cy="8" r="3" fill="#fff" />,
  ring: <circle cx="8" cy="8" r="3.2" fill="none" stroke="#fff" strokeWidth="1.8" />,
  tri: <path d="M8 4.4 11.8 11H4.2L8 4.4Z" fill="#fff" />,
  bars: <path d="M4.6 5.6h6.8M4.6 8h6.8M4.6 10.4h4.4" stroke="#fff" strokeWidth="1.5" strokeLinecap="round" />,
  square: <rect x="5" y="5" width="6" height="6" rx="1.2" fill="#fff" />,
  wave: <path d="M3.9 9c1.4-2.5 2.7-2.5 4.1 0s2.7 2.5 4.1 0" fill="none" stroke="#fff" strokeWidth="1.6" strokeLinecap="round" />,
  half: <path d="M8 4.5a3.5 3.5 0 0 1 0 7Z" fill="#fff" />,
  plus: <path d="M8 4.7v6.6M4.7 8h6.6" stroke="#fff" strokeWidth="1.7" strokeLinecap="round" />,
  leaf: <path d="M4.6 11.4C4.6 7 7.4 4.6 11.4 4.6c0 4-2.4 6.8-6.8 6.8Z" fill="#fff" />,
  drop: <path d="M8 4c1.8 2.3 3 3.9 3 5.3a3 3 0 0 1-6 0C5 7.9 6.2 6.3 8 4Z" fill="#fff" />,
};

export function Favicon({ glyph, color, className }: { glyph: Glyph; color: string; className?: string }) {
  return (
    <svg viewBox="0 0 16 16" className={className} aria-hidden="true">
      <rect width="16" height="16" rx="4" fill={color} />
      {marks[glyph]}
    </svg>
  );
}
