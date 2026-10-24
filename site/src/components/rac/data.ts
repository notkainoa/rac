import type { Glyph } from "./icons";

// The demo profile shown in the drawings. Sites are made up.

export interface Site {
  id: string;
  title: string;
  host: string;
  path?: string;
  glyph: Glyph;
  color: string;
}

export interface DemoSpace {
  id: string;
  name: string;
  preset: number;
  pinned: string[];
  tabs: string[];
}

export const sites: Record<string, Site> = {
  mail: { id: "mail", title: "Inbox", host: "mail.example.com", glyph: "ring", color: "#3A88C4" },
  calendar: { id: "calendar", title: "Calendar", host: "calendar.example.com", path: "/week", glyph: "square", color: "#C1575C" },
  music: { id: "music", title: "Music", host: "listen.example.com", glyph: "wave", color: "#D37B8B" },
  chat: { id: "chat", title: "Messages", host: "chat.example.com", glyph: "dot", color: "#3EB489" },

  groceries: { id: "groceries", title: "Groceries", host: "notes.example.com", path: "/groceries", glyph: "bars", color: "#3EB489" },
  bank: { id: "bank", title: "Checking", host: "bank.example.com", path: "/accounts", glyph: "drop", color: "#5F5B9E" },
  trails: { id: "trails", title: "Ten quiet trails north of the city", host: "fieldnotes.blog", path: "/quiet-trails", glyph: "tri", color: "#3EB489" },
  bread: { id: "bread", title: "Sourdough, week three", host: "crumb.kitchen", path: "/week-three", glyph: "half", color: "#E3AC38" },
  weather: { id: "weather", title: "Weekend weather", host: "sky.example.com", glyph: "leaf", color: "#3A88C4" },

  roadmap: { id: "roadmap", title: "Roadmap", host: "docs.team", path: "/roadmap", glyph: "bars", color: "#5F5B9E" },
  standup: { id: "standup", title: "Standup notes", host: "docs.team", path: "/standup", glyph: "square", color: "#E3AC38" },
  launch: { id: "launch", title: "Launch checklist", host: "docs.team", path: "/launch", glyph: "plus", color: "#3EB489" },
  review: { id: "review", title: "Design review", host: "board.example.com", path: "/review", glyph: "half", color: "#D37B8B" },
  pr: { id: "pr", title: "Pull request 214", host: "code.example.com", path: "/pulls/214", glyph: "dot", color: "#262626" },

  moodboard: { id: "moodboard", title: "Moodboard", host: "pins.example.com", glyph: "leaf", color: "#D87249" },
  type: { id: "type", title: "Notes on typography", host: "longform.press", path: "/notes-on-type", glyph: "tri", color: "#5F5B9E" },
  clouds: { id: "clouds", title: "A field guide to clouds", host: "longform.press", path: "/clouds", glyph: "ring", color: "#3A88C4" },
  color: { id: "color", title: "Color for interfaces", host: "longform.press", path: "/color", glyph: "drop", color: "#D87249" },
};

export const favorites = ["mail", "calendar", "music", "chat"];

export const demoSpaces: DemoSpace[] = [
  { id: "personal", name: "Personal", preset: 5, pinned: ["groceries", "bank"], tabs: ["trails", "bread", "weather"] },
  { id: "work", name: "Work", preset: 0, pinned: ["roadmap", "standup"], tabs: ["launch", "review", "pr"] },
  { id: "studio", name: "Studio", preset: 6, pinned: ["moodboard"], tabs: ["type", "color", "clouds"] },
];

export const NEW_TAB = "newtab";
