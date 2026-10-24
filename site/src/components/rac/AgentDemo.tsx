import { useEffect, useRef, useState, type CSSProperties } from "react";
import { AnimatePresence, LazyMotion, domAnimation, m, useReducedMotion } from "motion/react";
import "./rac-ui.css";
import { favorites, sites } from "./data";
import { selectedTab, tint } from "./theme";
import { Toolbar } from "./Toolbar";
import { CheckIcon, Favicon, MoreIcon, PlusIcon, ProfileIcon, SendIcon, SparkIcon } from "./icons";

// The assistant and its browser control, played out with rac's own cards and
// wording (resources/rac_ai). AI starts off, as in rac. Turn it on, send the
// request, and answer the cards: Allow for the plan, Confirm for the one step
// that sends something.

const HOST = "hanaya-inn.jp";
const REQUEST = "Book the inn for March 12 to 14, two guests";
const STEPS = ["Choose March 12 to 14", "Set guests to 2", "Fill in your name and email"];

type Phase = "idle" | "plan" | "running" | "confirm" | "done" | "stopped";

export default function AgentDemo() {
  const [on, setOn] = useState(false);
  const [phase, setPhase] = useState<Phase>("idle");
  const [done, setDone] = useState(0);
  const [elapsed, setElapsed] = useState(0);
  const reduce = useReducedMotion();
  const timers = useRef<number[]>([]);
  const started = useRef(0);

  const clear = () => {
    timers.current.forEach(clearTimeout);
    timers.current = [];
  };
  useEffect(() => clear, []);

  const reset = () => {
    clear();
    setPhase("idle");
    setDone(0);
  };

  const send = () => {
    started.current = performance.now();
    setPhase("plan");
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

  const filled = phase === "idle" || phase === "plan" ? 0 : phase === "running" ? done : STEPS.length;
  const working = phase === "running" || phase === "confirm";
  const enter = reduce
    ? { initial: { opacity: 0 }, animate: { opacity: 1 } }
    : { initial: { opacity: 0, transform: "translateY(6px) scale(0.98)" }, animate: { opacity: 1, transform: "translateY(0px) scale(1)" } };
  const cardMotion = { ...enter, transition: { duration: 0.24, ease: [0.23, 1, 0.32, 1] as const } };

  return (
    <LazyMotion features={domAnimation} strict>
      <div className="ad">
        <div className="ad-setting">
          <div>
            <p className="ad-setting-title" id="ad-setting-title">
              Turn on the assistant
            </p>
            <p className="ad-setting-text">
              Chat about the page you’re on in a side panel. Nothing runs and nothing is sent anywhere until you turn
              this on and add your own provider.
            </p>
          </div>
          <button type="button" role="switch" aria-checked={on} aria-labelledby="ad-setting-title" className="ad-switch press" onClick={toggle}>
            <i />
          </button>
        </div>

        <div className="rac ad-rac">
          <div className="rac-window ad-window" data-assistant={on || undefined} style={style}>
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

            <div className="rac-card ad-card" aria-hidden="true">
              <Toolbar host={HOST} path="/book" />
              <div className="rac-page">
                <Booking filled={filled} booked={phase === "done"} />
                <AnimatePresence>
                  {working && (
                    <m.div className="ad-working" {...cardMotion} exit={{ opacity: 0 }}>
                      <span className="ad-spin" />
                      Working in {HOST}…
                    </m.div>
                  )}
                </AnimatePresence>
              </div>
            </div>

            <section className="ad-panel" aria-label="Assistant" inert={!on || undefined}>
              <header className="ad-head">
                <SparkIcon className="ad-head-icon" />
                Assistant
              </header>
              <div className="ad-thread" aria-live="polite">
                {phase === "idle" && <p className="ad-empty">Ask about this page, or ask rac to do something on it.</p>}
                {phase !== "idle" && (
                  <>
                    <m.div className="ad-bubble" {...cardMotion}>
                      {REQUEST}
                    </m.div>
                    <m.p className="ad-reply" {...cardMotion} transition={{ ...cardMotion.transition, delay: 0.15 }}>
                      I’ll fill in the booking form. You’ll see each step here.
                    </m.p>
                  </>
                )}

                {phase === "plan" && (
                  <m.div className="ad-card-ui" role="group" aria-label="Plan" {...cardMotion} transition={{ ...cardMotion.transition, delay: 0.3 }}>
                    <div className="ad-eyebrow">
                      <i />
                      Waiting for you
                    </div>
                    <h4 className="ad-title">rac will:</h4>
                    <ul className="ad-steps">
                      {STEPS.map((s) => (
                        <li key={s}>{s}</li>
                      ))}
                    </ul>
                    <div className="ad-label">On these sites</div>
                    <span className="ad-chip">
                      <Favicon glyph="leaf" color="#C1575C" className="ad-chip-icon" />
                      {HOST}
                    </span>
                    <div className="ad-actions">
                      <button type="button" className="ad-pill ad-primary press" onClick={allow} title="Allow (⌘Return)">
                        Allow
                      </button>
                      <button type="button" className="ad-pill ad-quiet press" onClick={stop}>
                        Stop
                      </button>
                    </div>
                    <p className="ad-note">rac will still ask before buying, sending, or deleting anything.</p>
                  </m.div>
                )}

                {phase !== "idle" && phase !== "plan" && (
                  <div className="ad-log">
                    <div className="ad-step" data-status={phase === "stopped" && done === 0 ? "stopped" : "done"}>
                      <Mark status={phase === "stopped" && done === 0 ? "stopped" : "done"} />
                      {phase === "stopped" && done === 0 ? "Stopped" : `Allowed on ${HOST}`}
                    </div>
                    {STEPS.map((s, i) => {
                      let status: "done" | "running" | null = null;
                      if (i < done || phase === "confirm" || phase === "done") status = "done";
                      else if (phase === "running" && i === done) status = "running";
                      if (!status) return null;
                      return (
                        <m.div key={s} className="ad-step" data-status={status} {...cardMotion}>
                          <Mark status={status} />
                          {s}
                        </m.div>
                      );
                    })}
                  </div>
                )}

                {phase === "confirm" && (
                  <m.div className="ad-card-ui" role="group" aria-label="Confirm a step" {...cardMotion}>
                    <div className="ad-eyebrow">
                      <i />
                      Waiting for you
                    </div>
                    <h4 className="ad-title">Clicks Book room</h4>
                    <p className="ad-detail">It sends the form to {HOST}</p>
                    <div className="ad-actions">
                      <button type="button" className="ad-pill ad-primary press" onClick={confirm}>
                        Confirm
                      </button>
                      <button type="button" className="ad-pill press" onClick={stop}>
                        Skip
                      </button>
                      <button type="button" className="ad-pill ad-quiet press" onClick={stop}>
                        Stop
                      </button>
                    </div>
                  </m.div>
                )}

                {phase === "done" && (
                  <m.div className="ad-log" {...cardMotion}>
                    <div className="ad-step" data-status="done">
                      <Mark status="done" />
                      Confirmed: Clicks Book room
                    </div>
                    <p className="ad-summary">
                      Done in {elapsed}s · 1 confirmed. Your room is booked for March 12 to 14.
                    </p>
                  </m.div>
                )}

                {phase === "stopped" && <p className="ad-summary">Stopped. Nothing was sent.</p>}
              </div>

              <div className="ad-composer">
                {phase === "idle" ? (
                  <>
                    <span className="ad-input">{REQUEST}</span>
                    <button type="button" className="ad-send press" aria-label="Send" onClick={send}>
                      <SendIcon />
                    </button>
                  </>
                ) : (
                  <>
                    <span className="ad-input ad-placeholder">Ask another question…</span>
                    {(phase === "done" || phase === "stopped") && (
                      <button type="button" className="ad-pill press" onClick={reset}>
                        Start over
                      </button>
                    )}
                  </>
                )}
              </div>
            </section>
          </div>
        </div>
      </div>
    </LazyMotion>
  );
}

function Mark({ status }: { status: "done" | "running" | "stopped" }) {
  if (status === "running") return <span className="ad-mark ad-spin" />;
  if (status === "stopped") return <span className="ad-mark ad-ring" />;
  return <CheckIcon className="ad-mark" />;
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
