import { useCallback, useEffect, useRef, useState, type CSSProperties } from "react";
import { AnimatePresence, LazyMotion, domAnimation, m, useReducedMotion } from "motion/react";
import "./rac-ui.css";
import { NEW_TAB, demoSpaces, favorites, sites, type DemoSpace } from "./data";
import { Page } from "./Pages";
import { selectedTab, tint } from "./theme";
import { CloseIcon, Favicon, MoreIcon, PlusIcon, ProfileIcon } from "./icons";
import { Toolbar } from "./Toolbar";

// A working drawing of rac's window, built to the real measurements: a 202pt
// sidebar with favorites, the space's pinned tabs and open tabs, and the
// switcher at its foot; the page in a card inset 6pt from the window. Click
// around, swipe or use the dots to change spaces, press ⌘S to hide the
// sidebar and point at the left edge to peek at it.

interface Tab {
  key: string;
  site: string;
}

interface SpaceState extends DemoSpace {
  open: Tab[];
  active: string;
  unloaded: string[];
}

type SidebarState = "shown" | "hidden" | "peek";

let tabSerial = 0;
const newKey = () => `t${++tabSerial}`;

function initialSpaces(): SpaceState[] {
  return demoSpaces.map((s) => ({
    ...s,
    open: s.tabs.map((site) => ({ key: `${s.id}-${site}`, site })),
    active: `${s.id}-${s.tabs[0]}`,
    unloaded: [],
  }));
}

// Names and colors for spaces added with "+", in the order rac picks them.
const NEXT_PRESETS = [1, 4, 7, 3, 2];

export default function RacWindow({ compact = false }: { compact?: boolean }) {
  const [spaces, setSpaces] = useState(initialSpaces);
  const [index, setIndex] = useState(0);
  const [direction, setDirection] = useState(1);
  const [sidebar, setSidebar] = useState<SidebarState>("shown");
  const reduce = useReducedMotion();
  const rootRef = useRef<HTMLDivElement>(null);
  const sidebarRef = useRef<HTMLElement>(null);
  const inView = useRef(false);
  const wheel = useRef({ x: 0, cooling: false });
  const drag = useRef<{ x: number; id: number } | null>(null);

  const space = spaces[index];

  const goTo = (next: number) => {
    if (next === index || next < 0 || next >= spaces.length) return;
    setDirection(next > index ? 1 : -1);
    setIndex(next);
  };

  const update = (fn: (s: SpaceState) => SpaceState) =>
    setSpaces((all) => all.map((s, i) => (i === index ? fn(s) : s)));

  const select = (key: string) =>
    update((s) => ({ ...s, active: key, unloaded: s.unloaded.filter((k) => k !== key) }));

  const openNewTab = () => {
    const key = newKey();
    update((s) => ({ ...s, open: [...s.open, { key, site: NEW_TAB }], active: key }));
  };

  const closeTab = (key: string) =>
    update((s) => {
      const i = s.open.findIndex((t) => t.key === key);
      const open = s.open.filter((t) => t.key !== key);
      let active = s.active;
      if (active === key) {
        const neighbor = open[Math.min(i, open.length - 1)];
        active = neighbor ? neighbor.key : `${s.id}-pin-${s.pinned[0]}`;
      }
      return { ...s, open, active };
    });

  // Closing a pinned tab only resets it: it stays in the sidebar, unloaded,
  // back on the page it was pinned on.
  const resetPinned = (key: string) =>
    update((s) => {
      const active = s.active === key ? (s.open[0]?.key ?? key) : s.active;
      return { ...s, active, unloaded: [...s.unloaded.filter((k) => k !== key), key] };
    });

  const addSpace = () => {
    const n = spaces.length;
    const preset = NEXT_PRESETS[(n - demoSpaces.length) % NEXT_PRESETS.length];
    const key = newKey();
    const id = `space-${n + 1}`;
    setSpaces((all) => [
      ...all,
      { id, name: `Space ${n + 1}`, preset, pinned: [], tabs: [], open: [{ key, site: NEW_TAB }], active: key, unloaded: [] },
    ]);
    setDirection(1);
    setIndex(n);
  };

  const toggleSidebar = useCallback(() => setSidebar((s) => (s === "shown" ? "hidden" : "shown")), []);

  useEffect(() => {
    const el = rootRef.current;
    if (!el) return;
    const io = new IntersectionObserver(([e]) => (inView.current = e.isIntersecting), { threshold: 0.4 });
    io.observe(el);
    const onKey = (e: KeyboardEvent) => {
      if (!inView.current || e.altKey || e.shiftKey) return;
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "s") {
        e.preventDefault();
        toggleSidebar();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => {
      io.disconnect();
      window.removeEventListener("keydown", onKey);
    };
  }, [toggleSidebar]);

  // Two-finger swipes on the sidebar switch spaces, as on a trackpad in rac.
  const onWheel = (e: React.WheelEvent) => {
    if (Math.abs(e.deltaX) <= Math.abs(e.deltaY)) return;
    const w = wheel.current;
    if (w.cooling) return;
    w.x += e.deltaX;
    if (Math.abs(w.x) > 50) {
      goTo(index + (w.x > 0 ? 1 : -1));
      w.x = 0;
      w.cooling = true;
      setTimeout(() => (w.cooling = false), 450);
    }
  };

  // On touch screens, a horizontal drag across the sidebar does the same.
  const onPointerDown = (e: React.PointerEvent) => {
    if (e.pointerType === "mouse") return;
    drag.current = { x: e.clientX, id: e.pointerId };
  };
  const onPointerUp = (e: React.PointerEvent) => {
    const d = drag.current;
    drag.current = null;
    if (!d || d.id !== e.pointerId) return;
    const dx = e.clientX - d.x;
    if (Math.abs(dx) > 40) goTo(index + (dx < 0 ? 1 : -1));
  };

  const activeSite = (() => {
    const tab = space.open.find((t) => t.key === space.active);
    if (tab) return tab.site;
    const fav = favorites.find((f) => `fav-${f}` === space.active);
    if (fav) return fav;
    const pin = space.pinned.find((p) => `${space.id}-pin-${p}` === space.active);
    return pin ?? NEW_TAB;
  })();
  const site = sites[activeSite];

  const windowStyle = {
    "--sel-l": selectedTab(space.preset, false),
    "--sel-d": selectedTab(space.preset, true),
  } as CSSProperties;

  const slide = reduce ? 0 : 100;

  return (
    <LazyMotion features={domAnimation} strict>
      <div ref={rootRef} className="rac" data-compact={compact || undefined}>
        <p className="sr-only" aria-live="polite">
          {`rac window, ${space.name} space, showing ${site ? site.title : "a new tab"}${
            sidebar === "shown" ? "" : ", sidebar hidden"
          }.`}
        </p>
        <div
          className="rac-window"
          data-sidebar={sidebar}
          style={windowStyle}
          onPointerMove={(e) => {
            if (sidebar !== "peek" || !sidebarRef.current) return;
            if (e.clientX > sidebarRef.current.getBoundingClientRect().right + 16) setSidebar("hidden");
          }}
          onPointerLeave={() => setSidebar((s) => (s === "peek" ? "hidden" : s))}
        >
          {spaces.map((s, i) => (
            <div
              key={s.id}
              className="rac-tint"
              data-on={i === index}
              style={{ "--t-l": tint(s.preset, false), "--t-d": tint(s.preset, true) } as CSSProperties}
            />
          ))}

          <aside
            ref={sidebarRef}
            className="rac-sidebar"
            aria-label="Sidebar"
            onWheel={onWheel}
            onPointerDown={onPointerDown}
            onPointerUp={onPointerUp}
          >
            <div
              className="rac-tint rac-peek-tint"
              data-on="true"
              style={{ "--t-l": tint(space.preset, false), "--t-d": tint(space.preset, true) } as CSSProperties}
            />
            <div className="rac-lights" aria-hidden="true">
              <i />
              <i />
              <i />
            </div>

            <div className="rac-favs">
              {favorites.map((f) => (
                <button
                  key={f}
                  type="button"
                  className="rac-fav"
                  data-selected={space.active === `fav-${f}`}
                  aria-label={sites[f].title}
                  title={sites[f].title}
                  onClick={() => select(`fav-${f}`)}
                >
                  <Favicon glyph={sites[f].glyph} color={sites[f].color} className="rac-favicon" />
                </button>
              ))}
            </div>

            <div className="rac-viewport">
              <AnimatePresence initial={false} custom={direction} mode="popLayout">
                <m.div
                  key={space.id}
                  className="rac-space"
                  custom={direction}
                  initial={{ transform: `translateX(${direction * slide}%)`, opacity: reduce ? 0 : 1 }}
                  animate={{ transform: "translateX(0%)", opacity: 1 }}
                  exit={{ transform: `translateX(${direction * -slide}%)`, opacity: reduce ? 0 : 1 }}
                  transition={{ duration: reduce ? 0.15 : 0.32, ease: [0.32, 0.72, 0, 1] }}
                >
                  <div className="rac-space-name">
                    <span className="rac-space-dot" />
                    {space.name}
                  </div>

                  {space.pinned.length > 0 && (
                    <>
                      <ul className="rac-list">
                        {space.pinned.map((p) => {
                          const key = `${space.id}-pin-${p}`;
                          return (
                            <Row
                              key={key}
                              site={p}
                              selected={space.active === key}
                              unloaded={space.unloaded.includes(key)}
                              closeLabel={`Reset ${sites[p].title}`}
                              onSelect={() => select(key)}
                              onClose={() => resetPinned(key)}
                            />
                          );
                        })}
                      </ul>
                      <div className="rac-divider" />
                    </>
                  )}

                  <button type="button" className="rac-row rac-new" onClick={openNewTab}>
                    <PlusIcon className="rac-row-icon" />
                    <span>New Tab</span>
                  </button>

                  <ul className="rac-list">
                    <AnimatePresence initial={false}>
                      {space.open.map((t) => (
                        <m.li
                          key={t.key}
                          initial={{ opacity: 0, height: 0 }}
                          animate={{ opacity: 1, height: "auto" }}
                          exit={{ opacity: 0, height: 0 }}
                          transition={{ duration: reduce ? 0 : 0.18, ease: [0.23, 1, 0.32, 1] }}
                        >
                          <Row
                            asItem={false}
                            site={t.site}
                            selected={space.active === t.key}
                            closeLabel={`Close ${t.site === NEW_TAB ? "New Tab" : sites[t.site].title}`}
                            onSelect={() => select(t.key)}
                            onClose={() => closeTab(t.key)}
                          />
                        </m.li>
                      ))}
                    </AnimatePresence>
                  </ul>
                </m.div>
              </AnimatePresence>
            </div>

            <div className="rac-bottom">
              <ProfileIcon className="rac-bottom-icon" />
              <div className="rac-dots" role="group" aria-label="Spaces">
                {spaces.map((s, i) => (
                  <button
                    key={s.id}
                    type="button"
                    className="rac-dot"
                    data-on={i === index}
                    aria-label={`${s.name} space`}
                    aria-pressed={i === index}
                    onClick={() => goTo(i)}
                  />
                ))}
                {spaces.length < 8 && (
                  <button type="button" className="rac-dot-add" aria-label="New space" title="New space" onClick={addSpace}>
                    <PlusIcon />
                  </button>
                )}
              </div>
              <MoreIcon className="rac-bottom-icon" />
            </div>
          </aside>

          <div className="rac-card">
            <Toolbar host={site?.host} path={site?.path} onSidebar={toggleSidebar} />
            <div className="rac-page" aria-hidden="true">
              <Page id={activeSite} />
            </div>
          </div>

          {sidebar !== "shown" && (
            <div className="rac-edge" onPointerEnter={() => setSidebar("peek")} aria-hidden="true" />
          )}
        </div>
      </div>
    </LazyMotion>
  );
}

function Row({
  site,
  selected,
  unloaded,
  closeLabel,
  onSelect,
  onClose,
  asItem = true,
}: {
  site: string;
  selected: boolean;
  unloaded?: boolean;
  closeLabel: string;
  onSelect: () => void;
  onClose: () => void;
  asItem?: boolean;
}) {
  const info = site === NEW_TAB ? null : sites[site];
  const body = (
    <div className="rac-row" data-selected={selected} data-unloaded={unloaded || undefined}>
      <button type="button" className="rac-row-hit" onClick={onSelect} aria-current={selected || undefined}>
        {info ? <Favicon glyph={info.glyph} color={info.color} className="rac-row-icon" /> : <span className="rac-row-icon rac-ntp-icon">rac</span>}
        <span className="rac-row-title">{info ? info.title : "New Tab"}</span>
      </button>
      <button type="button" className="rac-close" aria-label={closeLabel} onClick={onClose}>
        <CloseIcon />
      </button>
    </div>
  );
  return asItem ? <li>{body}</li> : body;
}
