import { useEffect, useRef, useState, type CSSProperties } from "react";
import { AnimatePresence, LazyMotion, domAnimation, m, useReducedMotion } from "motion/react";
import "./rac-ui.css";
import { favorites, sites } from "./data";
import { selectedTab, tint } from "./theme";
import { Toolbar } from "./Toolbar";
import { CheckIcon, CloseIcon, Favicon, MoreIcon, PlusIcon, ProfileIcon, SendIcon, SparkIcon } from "./icons";

// The assistant and its browser control, played out with rac's own cards and
// wording (resources/rac_ai). AI starts off, as in rac. Turn it on, send the
// request, and answer the cards: Allow for the plan, Confirm for the one step
// that sends something.

const HOST = "hanaya-inn.jp";
const REQUEST = "Book the inn for March 12 to 14, two guests";
const STEPS = ["Choose March 12 to 14", "Set guests to 2", "Fill in your name and email"];

const SUGGESTIONS = ["Summarize this page", "What would two nights cost?", REQUEST];

type Phase = "idle" | "plan" | "running" | "confirm" | "done" | "stopped";
type Kind = "book" | "booked" | "summary" | "price" | "cancel" | "breakfast" | "where" | "other";
type Turn = { id: number; q: string; kind: Kind };

// What the demo answers. It only knows the page in the tab, and says so.
function classify(text: string, booked: boolean): Kind {
  const t = text.toLowerCase();
  if (/\b(book|reserve|fill|sign me up)/.test(t)) return booked ? "booked" : "book";
  if (/\b(cancel|refund)/.test(t)) return "cancel";
  if (/\b(cost|costs|price|prices|pay|much|yen|cheap|expensive)\b|¥/.test(t)) return "price";
  if (/\b(breakfast|food|eat|meals?)\b/.test(t)) return "breakfast";
  if (/\b(where|location|address|station|area|kyoto|neighborhood)\b/.test(t)) return "where";
  if (/\b(summar|about|tl;?dr|what is|overview|this page)/.test(t)) return "summary";
  return "other";
}

function Answer({ kind }: { kind: Kind }) {
  switch (kind) {
    case "summary":
      return (
        <>
          <p>Hanaya Inn rents a tatami garden room in Higashiyama, Kyoto, for ¥32,000 a night with breakfast.</p>
          <ul className="asst-answer-list">
            <li>Booking needs dates, the number of guests, and a name.</li>
            <li>The page doesn’t mention a cancellation policy.</li>
          </ul>
        </>
      );
    case "price":
      return <p>¥32,000 a night with breakfast, so two nights, March 12 to 14, come to ¥64,000.</p>;
    case "cancel":
      return <p>The page doesn’t mention a cancellation policy. It may be worth asking the inn before you book.</p>;
    case "breakfast":
      return <p>Yes, breakfast is included in the nightly price.</p>;
    case "where":
      return <p>Higashiyama, in Kyoto. The page doesn’t give a street address.</p>;
    case "booked":
      return <p>It’s already booked: the garden room, March 12 to 14, for two.</p>;
    default:
      return (
        <p>
          This is a demo, so I only know this page: Hanaya Inn’s garden room. Ask what it costs, or ask me to book it.
        </p>
      );
  }
}

export default function AgentDemo() {
  const [on, setOn] = useState(false);
  const [turns, setTurns] = useState<Turn[]>([]);
  const [thinking, setThinking] = useState<number | null>(null);
  const [bookTurn, setBookTurn] = useState<number | null>(null);
  const [phase, setPhase] = useState<Phase>("idle");
  const [done, setDone] = useState(0);
  const [elapsed, setElapsed] = useState(0);
  const [draft, setDraft] = useState("");
  const reduce = useReducedMotion();
  const timers = useRef<number[]>([]);
  const started = useRef(0);
  const nextId = useRef(1);
  const thread = useRef<HTMLDivElement>(null);

  const clear = () => {
    timers.current.forEach(clearTimeout);
    timers.current = [];
  };
  useEffect(() => clear, []);

  // Keep the newest message in view, inside the panel only.
  useEffect(() => {
    const el = thread.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [turns, thinking, phase, done]);

  const reset = () => {
    clear();
    setTurns([]);
    setThinking(null);
    setBookTurn(null);
    setPhase("idle");
    setDone(0);
    setDraft("");
  };

  const busy = thinking !== null || phase === "plan" || phase === "running" || phase === "confirm";

  const send = (raw: string) => {
    const text = raw.trim();
    if (!text || busy) return;
    const id = nextId.current++;
    const kind = classify(text, phase === "done");
    setTurns((t) => [...t, { id, q: text, kind }]);
    setDraft("");
    setThinking(id);
    timers.current.push(
      window.setTimeout(
        () => {
          setThinking(null);
          // Reading the page changes nothing, so it just answers. Acting in
          // the tab starts with a plan card.
          if (kind === "book") {
            started.current = performance.now();
            setBookTurn(id);
            setDone(0);
            setPhase("plan");
          }
        },
        reduce ? 200 : 650,
      ),
    );
  };

  const allow = () => {
    setPhase("running");
    setDone(0);
    STEPS.forEach((_, i) => {
      timers.current.push(window.setTimeout(() => setDone(i + 1), 750 * (i + 1)));
    });
    timers.current.push(window.setTimeout(() => setPhase("confirm"), 750 * STEPS.length + 350));
  };

  const confirm = () => {
    setElapsed(Math.max(6, Math.round((performance.now() - started.current) / 1000)));
    setPhase("done");
  };

  const stop = () => {
    clear();
    setPhase("stopped");
  };

  const toggle = () => {
    if (on) reset();
    setOn(!on);
  };

  const preset = 2;
  const style = {
    "--t-l": tint(preset, false),
    "--t-d": tint(preset, true),
    "--sel-l": selectedTab(preset, false),
    "--sel-d": selectedTab(preset, true),
  } as CSSProperties;

  const filled = phase === "idle" || phase === "plan" ? 0 : phase === "running" || phase === "stopped" ? done : STEPS.length;
  const working = phase === "running" || phase === "confirm";
  const enter = reduce
    ? { initial: { opacity: 0 }, animate: { opacity: 1 } }
    : { initial: { opacity: 0, transform: "translateY(6px) scale(0.98)" }, animate: { opacity: 1, transform: "translateY(0px) scale(1)" } };
  const cardMotion = { ...enter, transition: { duration: 0.24, ease: [0.23, 1, 0.32, 1] as const } };

  // The plan, its steps, and the confirmation, under the request that started them.
  const booker = (
    <>
      {phase === "plan" && (
        <m.div className="asst-card-ui" role="group" aria-label="Plan" {...cardMotion} transition={{ ...cardMotion.transition, delay: 0.15 }}>
          <div className="asst-eyebrow">
            <i />
            Waiting for you
          </div>
          <h4 className="asst-title">rac will:</h4>
          <ul className="asst-steps">
            {STEPS.map((s) => (
              <li key={s}>{s}</li>
            ))}
          </ul>
          <div className="asst-label">On these sites</div>
          <span className="asst-chip">
            <Favicon glyph="leaf" color="#C1575C" className="asst-chip-icon" />
            {HOST}
          </span>
          <div className="asst-actions">
            <button type="button" className="asst-pill asst-primary press" onClick={allow} title="Allow (⌘Return)">
              Allow
            </button>
            <button type="button" className="asst-pill asst-quiet press" onClick={stop}>
              Stop
            </button>
          </div>
          <p className="asst-note">rac will still ask before buying, sending, or deleting anything.</p>
        </m.div>
      )}

      {phase !== "idle" && phase !== "plan" && (
        <div className="asst-log">
          <div className="asst-step" data-status={phase === "stopped" && done === 0 ? "stopped" : "done"}>
            <Mark status={phase === "stopped" && done === 0 ? "stopped" : "done"} />
            {phase === "stopped" && done === 0 ? "Stopped" : `Allowed on ${HOST}`}
          </div>
          {STEPS.map((s, i) => {
            let status: "done" | "running" | null = null;
            if (i < done || phase === "confirm" || phase === "done") status = "done";
            else if (phase === "running" && i === done) status = "running";
            if (!status) return null;
            return (
              <m.div key={s} className="asst-step" data-status={status} {...cardMotion}>
                <Mark status={status} />
                {s}
              </m.div>
            );
          })}
        </div>
      )}

      {phase === "confirm" && (
        <m.div className="asst-card-ui" role="group" aria-label="Confirm a step" {...cardMotion}>
          <div className="asst-eyebrow">
            <i />
            Waiting for you
          </div>
          <h4 className="asst-title">Clicks Book room</h4>
          <p className="asst-detail">It sends the form to {HOST}</p>
          <div className="asst-actions">
            <button type="button" className="asst-pill asst-primary press" onClick={confirm}>
              Confirm
            </button>
            <button type="button" className="asst-pill press" onClick={stop}>
              Skip
            </button>
            <button type="button" className="asst-pill asst-quiet press" onClick={stop}>
              Stop
            </button>
          </div>
        </m.div>
      )}

      {phase === "done" && (
        <m.div className="asst-log" {...cardMotion}>
          <div className="asst-step" data-status="done">
            <Mark status="done" />
            Confirmed: Clicks Book room
          </div>
          <p className="asst-summary">Done in {elapsed}s · 1 confirmed. Your room is booked for March 12 to 14.</p>
        </m.div>
      )}

      {phase === "stopped" && <p className="asst-summary">Stopped. Nothing was sent.</p>}
    </>
  );

  return (
    <LazyMotion features={domAnimation} strict>
      <div className="asst">
        <button type="button" role="switch" aria-checked={on} className="asst-toggle press" onClick={toggle}>
          <SparkIcon className="asst-toggle-icon" />
          Assistant
          <span className="asst-switch" aria-hidden="true">
            <i />
          </span>
        </button>

        <div className="rac asst-rac">
          <div className="rac-window asst-window" data-assistant={on || undefined} style={style}>
            <div className="rac-tint" data-on="true" />
            <aside className="rac-sidebar" aria-hidden="true">
              <div className="rac-lights">
                <i />
                <i />
                <i />
              </div>
              <div className="rac-favs">
                {favorites.map((f) => (
                  <span key={f} className="rac-fav">
                    <Favicon glyph={sites[f].glyph} color={sites[f].color} className="rac-favicon" />
                  </span>
                ))}
              </div>
              <div className="rac-viewport">
                <div className="rac-space">
                  <div className="rac-space-name">
                    <span className="rac-space-dot" />
                    Trips
                  </div>
                  <div className="rac-row rac-new">
                    <PlusIcon className="rac-row-icon" />
                    <span>New Tab</span>
                  </div>
                  <div className="rac-row" data-selected="true">
                    <span className="rac-row-hit">
                      <Favicon glyph="leaf" color="#C1575C" className="rac-row-icon" />
                      <span className="rac-row-title">Hanaya Inn, Kyoto</span>
                    </span>
                  </div>
                  <div className="rac-row">
                    <span className="rac-row-hit">
                      <Favicon glyph="tri" color="#3A88C4" className="rac-row-icon" />
                      <span className="rac-row-title">Trains from Tokyo</span>
                    </span>
                  </div>
                </div>
              </div>
              <div className="rac-bottom">
                <ProfileIcon className="rac-bottom-icon" />
                <div className="rac-dots">
                  <span className="rac-dot" />
                  <span className="rac-dot" data-on="true" />
                  <span className="rac-dot-add">
                    <PlusIcon />
                  </span>
                </div>
                <MoreIcon className="rac-bottom-icon" />
              </div>
            </aside>

            <div className="rac-card asst-card">
              <Toolbar host={HOST} path="/book" assistant={{ on, toggle }} />
              <div className="rac-page" aria-hidden="true">
                <Booking filled={filled} booked={phase === "done"} />
                <AnimatePresence>
                  {working && (
                    <m.div className="asst-working" {...cardMotion} exit={{ opacity: 0 }}>
                      <span className="asst-spin" />
                      Working in {HOST}…
                    </m.div>
                  )}
                </AnimatePresence>
              </div>
            </div>

            <section className="asst-panel" aria-label="Assistant" inert={!on || undefined}>
              <header className="asst-head">
                <SparkIcon className="asst-head-icon" />
                Assistant
                <span className="asst-head-tools">
                  {turns.length > 0 && !busy && (
                    <button type="button" className="asst-pill asst-quiet press" onClick={reset}>
                      Start over
                    </button>
                  )}
                  <button type="button" className="asst-close press" aria-label="Turn off the assistant" onClick={toggle}>
                    <CloseIcon />
                  </button>
                </span>
              </header>
              <div className="asst-thread" ref={thread} aria-live="polite">
                {turns.length === 0 && (
                  <div className="asst-empty">
                    <p>Ask about this page, or ask rac to do something on it.</p>
                    <div className="asst-suggest">
                      {SUGGESTIONS.map((t) => (
                        <button key={t} type="button" className="asst-pill press" onClick={() => send(t)}>
                          {t}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
                {turns.map((turn) => (
                  <div key={turn.id} className="asst-turn">
                    <m.div className="asst-bubble" {...cardMotion}>
                      {turn.q}
                    </m.div>
                    {thinking === turn.id ? (
                      <m.div className="asst-reply asst-typing" aria-label="Thinking" {...cardMotion}>
                        <i />
                        <i />
                        <i />
                      </m.div>
                    ) : turn.kind !== "book" ? (
                      <m.div className="asst-reply" {...cardMotion}>
                        <Answer kind={turn.kind} />
                      </m.div>
                    ) : (
                      <>
                        <m.p className="asst-reply" {...cardMotion}>
                          I’ll fill in the booking form. You’ll see each step here.
                        </m.p>
                        {turn.id === bookTurn ? booker : <p className="asst-summary">Stopped. Nothing was sent.</p>}
                      </>
                    )}
                  </div>
                ))}
              </div>

              <form
                className="asst-composer"
                onSubmit={(e) => {
                  e.preventDefault();
                  send(draft);
                }}
              >
                <label className="sr-only" htmlFor="asst-input">
                  Message the assistant
                </label>
                <input
                  id="asst-input"
                  className="asst-input"
                  value={draft}
                  maxLength={140}
                  autoComplete="off"
                  spellCheck={false}
                  disabled={busy}
                  onChange={(e) => setDraft(e.target.value)}
                  placeholder={
                    phase === "plan" || phase === "confirm"
                      ? "Waiting for you…"
                      : busy
                        ? "Working…"
                        : turns.length
                          ? "Ask another question…"
                          : "Ask a question about this page…"
                  }
                />
                <button type="submit" className="asst-send press" aria-label="Send" disabled={busy || !draft.trim()}>
                  <SendIcon />
                </button>
              </form>
            </section>
          </div>
        </div>
      </div>
    </LazyMotion>
  );
}

function Mark({ status }: { status: "done" | "running" | "stopped" }) {
  if (status === "running") return <span className="asst-mark asst-spin" />;
  if (status === "stopped") return <span className="asst-mark asst-ring" />;
  return <CheckIcon className="asst-mark" />;
}

function Booking({ filled, booked }: { filled: number; booked: boolean }) {
  const fields: [string, string][] = [
    ["Dates", "March 12 – 14"],
    ["Guests", "2 adults"],
    ["Name", "Sam Tanaka"],
  ];
  return (
    <div className="pg pg-app pg-booking">
      <header className="pg-masthead">
        <b>Hanaya Inn</b>
        <span>Rooms</span>
        <span>Garden</span>
      </header>
      <h3 className="pg-h1">A garden room in Higashiyama</h3>
      <p className="pg-meta">Tatami room · breakfast included · ¥32,000 a night</p>
      <div className="pg-form">
        {fields.map(([label, value], i) => (
          <label key={label} className="pg-field" data-filled={i < filled}>
            <span>{label}</span>
            <b>{i < filled ? value : ""}</b>
          </label>
        ))}
        <span className="pg-book" data-booked={booked}>
          {booked ? "Booked" : "Book room"}
        </span>
      </div>
    </div>
  );
}
