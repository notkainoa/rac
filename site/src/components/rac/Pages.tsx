import { PlusIcon } from "./icons";

// Simple, believable web pages for the drawn window. They're made-up sites,
// drawn in neutral colors so the rac chrome around them stays the subject.

function Article({ site, title, meta, figure, body }: { site: string; title: string; meta: string; figure?: "hills" | "loaf" | "sky"; body: string[] }) {
  return (
    <div className="pg pg-article">
      <header className="pg-masthead">
        <b>{site}</b>
        <span>Latest</span>
        <span>About</span>
      </header>
      <h3 className="pg-h1">{title}</h3>
      <p className="pg-meta">{meta}</p>
      {figure && <Figure kind={figure} />}
      {body.map((p) => (
        <p key={p} className="pg-p">
          {p}
        </p>
      ))}
    </div>
  );
}

function Figure({ kind }: { kind: "hills" | "loaf" | "sky" }) {
  return (
    <svg className="pg-figure" viewBox="0 0 400 150" preserveAspectRatio="xMidYMid slice" aria-hidden="true">
      {kind === "hills" && (
        <>
          <rect width="400" height="150" fill="#DCE9E1" />
          <circle cx="300" cy="46" r="18" fill="#F6F1E4" />
          <path d="M0 108 90 60l60 32 70-50 86 54 94-30v84H0Z" fill="#8DBFA4" />
          <path d="M0 128 110 92l84 26 98-36 108 34v34H0Z" fill="#3E8A64" />
        </>
      )}
      {kind === "loaf" && (
        <>
          <rect width="400" height="150" fill="#EFE6D8" />
          <ellipse cx="200" cy="96" rx="120" ry="44" fill="#C98B4E" />
          <path d="M120 86c30-18 60-20 80-8m-40 22c30-18 70-20 100-6" stroke="#EAD2A8" strokeWidth="6" strokeLinecap="round" fill="none" />
        </>
      )}
      {kind === "sky" && (
        <>
          <rect width="400" height="150" fill="#DCE6F2" />
          <ellipse cx="120" cy="70" rx="70" ry="22" fill="#fff" />
          <ellipse cx="160" cy="60" rx="46" ry="24" fill="#fff" />
          <ellipse cx="290" cy="96" rx="80" ry="18" fill="#F4F7FB" />
        </>
      )}
    </svg>
  );
}

function Checklist({ site, title, meta, items }: { site: string; title: string; meta: string; items: [string, boolean][] }) {
  return (
    <div className="pg pg-doc">
      <header className="pg-masthead">
        <b>{site}</b>
        <span>Share</span>
      </header>
      <h3 className="pg-h1 pg-h1-sans">{title}</h3>
      <p className="pg-meta">{meta}</p>
      <ul className="pg-checks">
        {items.map(([text, done]) => (
          <li key={text} data-done={done}>
            <span className="pg-box" />
            {text}
          </li>
        ))}
      </ul>
    </div>
  );
}

function Inbox() {
  const rows = [
    ["Mara Lin", "Saturday hike?", "Thinking the ridge trail if the fog clears early."],
    ["Bookshop", "Your order shipped", "A Field Guide to Clouds is on its way."],
    ["Jonah", "Photos from the coast", "Finally sorted them. The one with the heron is yours."],
    ["Studio", "Thursday crit", "Bring the type specimens, even the rough ones."],
    ["Library", "Hold ready", "Notes on Typography is waiting at the front desk."],
  ];
  return (
    <div className="pg pg-app">
      <h3 className="pg-h2">Inbox</h3>
      <ul className="pg-rows">
        {rows.map(([from, subject, preview], i) => (
          <li key={subject} data-unread={i < 2}>
            <b>{from}</b>
            <span>
              <em>{subject}</em> {preview}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}

function Week() {
  const days = ["Mon", "Tue", "Wed", "Thu", "Fri"];
  const events: [number, number, number, string][] = [
    [0, 1, 1, "Standup"],
    [1, 3, 2, "Design review"],
    [2, 1, 1, "Standup"],
    [3, 4, 2, "Studio crit"],
    [4, 2, 1, "Lunch with Mara"],
    [0, 5, 2, "Focus"],
  ];
  return (
    <div className="pg pg-app">
      <h3 className="pg-h2">This week</h3>
      <div className="pg-week">
        {days.map((d, i) => (
          <div key={d} className="pg-day">
            <span>{d}</span>
            {events
              .filter((e) => e[0] === i)
              .map(([, start, len, name]) => (
                <i key={name + start} style={{ top: `${start * 2.4 + 2}em`, height: `${len * 2.4 - 0.3}em` }}>
                  {name}
                </i>
              ))}
          </div>
        ))}
      </div>
    </div>
  );
}

function Player() {
  return (
    <div className="pg pg-app pg-player">
      <div className="pg-cover" />
      <div>
        <h3 className="pg-h2">Slow Mornings</h3>
        <p className="pg-meta">Playlist · 24 songs</p>
        <ol className="pg-tracks">
          {["Low Tide", "Paper Lanterns", "North Window", "Quiet Hours"].map((t, i) => (
            <li key={t}>
              <span>{i + 1}</span>
              {t}
            </li>
          ))}
        </ol>
      </div>
    </div>
  );
}

function Chat() {
  return (
    <div className="pg pg-app pg-chat">
      <h3 className="pg-h2">Mara</h3>
      <p className="pg-bubble">Ridge trail Saturday?</p>
      <p className="pg-bubble pg-bubble-me">Yes. Leaving at 7, before the fog lifts.</p>
      <p className="pg-bubble">Perfect. I'll bring the good coffee.</p>
    </div>
  );
}

function Forecast() {
  const days = [
    ["Sat", "64°", "Fog, then sun"],
    ["Sun", "68°", "Clear"],
    ["Mon", "61°", "Light rain"],
  ];
  return (
    <div className="pg pg-app">
      <h3 className="pg-h2">Weekend weather</h3>
      <div className="pg-forecast">
        {days.map(([d, t, s]) => (
          <div key={d}>
            <span>{d}</span>
            <b>{t}</b>
            <span>{s}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function Account() {
  return (
    <div className="pg pg-app">
      <h3 className="pg-h2">Checking</h3>
      <p className="pg-balance">$2,481.06</p>
      <ul className="pg-rows pg-ledger">
        {[
          ["Bakery", "−$8.50"],
          ["Bookshop", "−$24.00"],
          ["Paycheck", "+$1,920.00"],
          ["Electric", "−$61.12"],
        ].map(([a, b]) => (
          <li key={a}>
            <b>{a}</b>
            <span>{b}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

function Moodboard() {
  const tiles = ["#D87249", "#E9D8C4", "#5F5B9E", "#3EB489", "#F2C14E", "#D37B8B"];
  return (
    <div className="pg pg-app">
      <h3 className="pg-h2">Moodboard</h3>
      <div className="pg-board">
        {tiles.map((c) => (
          <span key={c} style={{ background: c }} />
        ))}
      </div>
    </div>
  );
}

// rac's new tab page with AI off: a calm, empty page with one shortcut slot.
export function NewTabPage() {
  return (
    <div className="pg pg-ntp">
      <span className="pg-ntp-add">
        <PlusIcon />
      </span>
      <span>Add shortcut</span>
    </div>
  );
}

export function Page({ id }: { id: string }) {
  switch (id) {
    case "mail":
      return <Inbox />;
    case "calendar":
      return <Week />;
    case "music":
      return <Player />;
    case "chat":
      return <Chat />;
    case "weather":
      return <Forecast />;
    case "bank":
      return <Account />;
    case "moodboard":
      return <Moodboard />;
    case "groceries":
      return (
        <Checklist
          site="Notes"
          title="Groceries"
          meta="Shared with Mara"
          items={[
            ["Rye flour", true],
            ["Coffee beans", false],
            ["Lemons", false],
            ["Oat milk", true],
            ["Basil", false],
          ]}
        />
      );
    case "roadmap":
      return (
        <Checklist
          site="Team Docs"
          title="Roadmap"
          meta="Updated Monday"
          items={[
            ["Spaces", true],
            ["Pinned tabs", true],
            ["Sidebar reveal", true],
            ["Space themes", false],
            ["Command bar", false],
          ]}
        />
      );
    case "standup":
      return (
        <Checklist
          site="Team Docs"
          title="Standup notes"
          meta="Today"
          items={[
            ["Ship the settings cleanup", true],
            ["Review the onboarding copy", false],
            ["Profile startup with AI off", false],
          ]}
        />
      );
    case "launch":
      return (
        <Checklist
          site="Team Docs"
          title="Launch checklist"
          meta="Edited today · 3 people"
          items={[
            ["Release notes written", true],
            ["Update feed signed", true],
            ["Screenshots retaken", false],
            ["Docs reviewed", false],
          ]}
        />
      );
    case "review":
      return (
        <Article
          site="Board"
          title="Design review: the new tab page"
          meta="4 comments"
          body={["Less on the page, not more. One shortcut slot, no feed, nothing that moves.", "Agreed. The empty state should feel like a clean desk."]}
        />
      );
    case "pr":
      return (
        <Checklist
          site="Code"
          title="Pull request 214"
          meta="Open · 2 approvals"
          items={[
            ["Checks passed", true],
            ["Reviewed by Mara", true],
            ["Ready to merge", false],
          ]}
        />
      );
    case "trails":
      return (
        <Article
          site="Field Notes"
          title="Ten quiet trails north of the city"
          meta="A walking guide · 8 min read"
          figure="hills"
          body={["Leave early, before the fog lifts off the ridge, and you will have most of these paths to yourself.", "Each one starts within an hour of town and none needs more than good shoes."]}
        />
      );
    case "bread":
      return (
        <Article
          site="Crumb"
          title="Sourdough, week three"
          meta="Baking journal · 5 min read"
          figure="loaf"
          body={["The starter finally smells like apples instead of paint. This week: a longer cold proof."]}
        />
      );
    case "type":
      return (
        <Article
          site="Longform"
          title="Notes on typography"
          meta="Essay · 12 min read"
          body={["Good type disappears. You notice the words, not the letters.", "Set the measure first. Everything else follows from how far the eye has to travel."]}
        />
      );
    case "color":
      return (
        <Article
          site="Longform"
          title="Color for interfaces"
          meta="Essay · 9 min read"
          body={["Use color to say one thing at a time. A screen where everything is colored says nothing."]}
        />
      );
    case "clouds":
      return (
        <Article
          site="Longform"
          title="A field guide to clouds"
          meta="Guide · 6 min read"
          figure="sky"
          body={["Cumulus build in the afternoon and flatten by evening. Watch the bases: when they lower, rain is close."]}
        />
      );
    default:
      return <NewTabPage />;
  }
}
