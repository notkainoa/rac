// Shared drawing pieces for rac's illustrated UI: the demo spaces, favorites,
// favicons and icons. Used by the interactive hero window and by the static
// sidebars in the Spaces section.

import type { ReactNode } from "react";

export type Glyph = "dot" | "ring" | "tri" | "bars" | "square" | "wave" | "half" | "plus";

export interface Tab {
  title: string;
  glyph: Glyph;
  color: string;
}

export interface Space {
  name: string;
  key: "personal" | "work" | "reading";
  pinned: Tab[];
  folder?: { name: string; tabs: Tab[] };
  tabs: Tab[];
  address: string;
  page: { site: string; title: string; meta: string; body: string[]; figure: "hills" | "list" | "quote" };
}

export const favorites: Tab[] = [
  { title: "Mail", glyph: "ring", color: "#4271ff" },
  { title: "Calendar", glyph: "square", color: "#e8594a" },
  { title: "Music", glyph: "wave", color: "#d9478f" },
  { title: "Maps", glyph: "tri", color: "#2fa36b" },
  { title: "Notes", glyph: "bars", color: "#e3a21a" },
  { title: "Photos", glyph: "half", color: "#7a5af5" },
  { title: "Chat", glyph: "dot", color: "#16a3b8" },
  { title: "Files", glyph: "plus", color: "#5b6478" },
];

export const spaces: Space[] = [
  {
    name: "Personal",
    key: "personal",
    pinned: [
      { title: "Groceries", glyph: "bars", color: "#2fa36b" },
      { title: "Bank", glyph: "square", color: "#5b6478" },
    ],
    folder: {
      name: "Trip to Kyoto",
      tabs: [
        { title: "Flights", glyph: "tri", color: "#4271ff" },
        { title: "Ryokan booking", glyph: "half", color: "#e8594a" },
      ],
    },
    tabs: [
      { title: "Ten quiet trails", glyph: "tri", color: "#2fa36b" },
      { title: "Sourdough, week three", glyph: "dot", color: "#e3a21a" },
      { title: "Weekend weather", glyph: "ring", color: "#16a3b8" },
    ],
    address: "fieldnotes.blog",
    page: {
      site: "Field Notes",
      title: "Ten quiet trails north of the city",
      meta: "A walking guide · 8 min read",
      body: [
        "Leave early, before the fog lifts off the ridge, and you will have most of these paths to yourself.",
        "Each one starts within an hour of town and none needs more than good shoes.",
      ],
      figure: "hills",
    },
  },
  {
    name: "Work",
    key: "work",
    pinned: [
      { title: "Team inbox", glyph: "ring", color: "#4271ff" },
      { title: "Roadmap", glyph: "bars", color: "#7a5af5" },
      { title: "Standup notes", glyph: "square", color: "#e3a21a" },
    ],
    tabs: [
      { title: "Launch checklist", glyph: "plus", color: "#2fa36b" },
      { title: "Design review", glyph: "half", color: "#d9478f" },
      { title: "Pull request 214", glyph: "dot", color: "#5b6478" },
      { title: "Q4 planning", glyph: "square", color: "#e8594a" },
    ],
    address: "docs.team/launch",
    page: {
      site: "Team Docs",
      title: "Launch checklist",
      meta: "Edited today · 3 people",
      body: ["Everything that has to be true before we ship on Thursday."],
      figure: "list",
    },
  },
  {
    name: "Reading",
    key: "reading",
    pinned: [{ title: "Reading list", glyph: "bars", color: "#e8594a" }],
    tabs: [
      { title: "The case for slow software", glyph: "half", color: "#e8594a" },
      { title: "Notes on typography", glyph: "tri", color: "#7a5af5" },
      { title: "A field guide to clouds", glyph: "ring", color: "#16a3b8" },
    ],
    address: "longform.press",
    page: {
      site: "Longform",
      title: "The case for slow software",
      meta: "Essay · 14 min read",
      body: [
        "The best tools disappear. You stop noticing them the way you stop noticing a good chair.",
        "That takes restraint: fewer settings, fewer pop-ups, and nothing that asks for your attention without a reason.",
      ],
      figure: "quote",
    },
  },
];

export function Page({ space }: { space: Space }) {
  const { page } = space;
  return (
    <article className="bm-article">
      <header className="bm-site">
        <span className="bm-site-mark" />
        <span className="bm-site-name">{page.site}</span>
        <span className="bm-site-links">
          <span>Latest</span>
          <span>About</span>
        </span>
      </header>
      <h3 className="bm-title">{page.title}</h3>
      <p className="bm-meta">{page.meta}</p>
      {page.figure === "hills" && <Hills />}
      {page.body.map((line) => (
        <p key={line} className="bm-body">
          {line}
        </p>
      ))}
      {page.figure === "list" && (
        <ul className="bm-checks">
          {["Release notes written", "Update feed signed", "Screenshots retaken", "Docs reviewed"].map((item, i) => (
            <li key={item} data-done={i < 2}>
              <span className="bm-check" />
              {item}
            </li>
          ))}
        </ul>
      )}
      {page.figure === "quote" && <blockquote className="bm-quote">Good tools disappear.</blockquote>}
    </article>
  );
}

export function Favorites() {
  return (
    <div className="bm-favorites" data-part="favorites">
      {favorites.map((fav) => (
        <span key={fav.title} className="bm-fav" title={fav.title}>
          <Favicon glyph={fav.glyph} color={fav.color} />
        </span>
      ))}
    </div>
  );
}

export function SpaceLists({ space }: { space: Space }) {
  return (
    <>
      <ul className="bm-pinned" data-part="pinned">
        {space.pinned.map((tab) => (
          <TabRow key={tab.title} tab={tab} />
        ))}
        {space.folder && (
          <>
            <li className="bm-tab bm-folder">
              <Folder />
              <span>{space.folder.name}</span>
            </li>
            {space.folder.tabs.map((tab) => (
              <TabRow key={tab.title} tab={tab} indent />
            ))}
          </>
        )}
      </ul>
      <div className="bm-divider" />
      <ul data-part="tabs">
        <li className="bm-tab bm-new">
          <PlusIcon />
          <span>New Tab</span>
        </li>
        {space.tabs.map((tab, i) => (
          <TabRow key={tab.title} tab={tab} active={i === 0} />
        ))}
      </ul>
    </>
  );
}

export function SidebarTop() {
  return (
    <div className="bm-top">
      <span className="bm-lights">
        <i />
        <i />
        <i />
      </span>
      <span className="bm-nav">
        <SidebarIcon />
        <Arrow flip />
        <Arrow />
      </span>
    </div>
  );
}

export function TabRow({ tab, active, indent }: { tab: Tab; active?: boolean; indent?: boolean }) {
  return (
    <li className="bm-tab" data-active={active} data-indent={indent}>
      <Favicon glyph={tab.glyph} color={tab.color} small />
      <span>{tab.title}</span>
    </li>
  );
}

export function Favicon({ glyph, color, small }: { glyph: Glyph; color: string; small?: boolean }) {
  const shapes: Record<Glyph, ReactNode> = {
    dot: <circle cx="8" cy="8" r="3.2" fill="#fff" />,
    ring: <circle cx="8" cy="8" r="3.4" fill="none" stroke="#fff" strokeWidth="1.8" />,
    tri: <path d="M8 4.2 12 11.4H4L8 4.2Z" fill="#fff" />,
    bars: <path d="M4.5 5.5h7M4.5 8h7M4.5 10.5h4.5" stroke="#fff" strokeWidth="1.5" strokeLinecap="round" />,
    square: <rect x="4.8" y="4.8" width="6.4" height="6.4" rx="1.2" fill="#fff" />,
    wave: <path d="M3.8 9c1.4-2.6 2.8-2.6 4.2 0s2.8 2.6 4.2 0" fill="none" stroke="#fff" strokeWidth="1.6" strokeLinecap="round" />,
    half: <path d="M8 4.4a3.6 3.6 0 0 1 0 7.2Z" fill="#fff" />,
    plus: <path d="M8 4.6v6.8M4.6 8h6.8" stroke="#fff" strokeWidth="1.7" strokeLinecap="round" />,
  };
  return (
    <svg viewBox="0 0 16 16" className={small ? "bm-favicon bm-favicon-sm" : "bm-favicon"} aria-hidden="true">
      <rect width="16" height="16" rx="4" fill={color} />
      {shapes[glyph]}
    </svg>
  );
}

export function Hills() {
  return (
    <svg className="bm-figure" viewBox="0 0 320 120" preserveAspectRatio="xMidYMid slice" aria-hidden="true">
      <rect width="320" height="120" className="bm-sky" />
      <circle cx="238" cy="40" r="14" className="bm-sun" />
      <path d="M0 86 70 48l50 26 56-40 70 44 74-24v66H0Z" className="bm-hill-far" />
      <path d="M0 102 90 72l70 22 80-30 80 28v28H0Z" className="bm-hill-near" />
    </svg>
  );
}

const iconProps = {
  viewBox: "0 0 16 16",
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 1.5,
  strokeLinecap: "round" as const,
  strokeLinejoin: "round" as const,
  "aria-hidden": true,
};

export function SidebarIcon() {
  return (
    <svg {...iconProps} className="bm-icon">
      <rect x="2" y="3" width="12" height="10" rx="2.2" />
      <path d="M6.2 3v10" />
    </svg>
  );
}

export function Arrow({ flip }: { flip?: boolean }) {
  return (
    <svg {...iconProps} className="bm-icon" style={flip ? { transform: "scaleX(-1)" } : undefined}>
      <path d="M6 3.5 10.5 8 6 12.5" />
    </svg>
  );
}

export function Lock() {
  return (
    <svg {...iconProps} className="bm-icon bm-lock">
      <rect x="3.5" y="7" width="9" height="6.5" rx="1.6" />
      <path d="M5.5 7V5.5a2.5 2.5 0 0 1 5 0V7" />
    </svg>
  );
}

export function Folder() {
  return (
    <svg {...iconProps} className="bm-favicon-sm bm-folder-icon">
      <path d="M2 4.8c0-.7.5-1.3 1.2-1.3h2.9l1.5 1.6h5.2c.7 0 1.2.6 1.2 1.3v5.3c0 .7-.5 1.3-1.2 1.3H3.2c-.7 0-1.2-.6-1.2-1.3V4.8Z" />
    </svg>
  );
}

export function PlusIcon() {
  return (
    <svg {...iconProps} className="bm-favicon-sm">
      <path d="M8 3.5v9M3.5 8h9" />
    </svg>
  );
}
