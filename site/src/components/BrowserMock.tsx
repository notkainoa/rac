import { useCallback, useEffect, useRef, useState } from "react";
import { AnimatePresence, LazyMotion, domAnimation, m, useReducedMotion } from "motion/react";
import "./browser-mock.css";
import { Favorites, Lock, Page, SidebarTop, SpaceLists, spaces } from "./MockParts";

// An illustrated rac window, drawn from the real layout: favorites, pinned
// tabs and open tabs in the sidebar, the space dots at its foot, and the page
// on the right. It stays abstract on purpose so it remains true as the real
// UI changes.
//
// Visitors can switch spaces with the dots, hide the sidebar with ⌘S or the
// button above the window, and bring it back by pointing at the left edge,
// the same way rac's edge reveal works.

type SidebarState = "shown" | "hidden" | "peek";

export default function BrowserMock() {
  const [index, setIndex] = useState(0);
  const [direction, setDirection] = useState(1);
  const [sidebar, setSidebar] = useState<SidebarState>("shown");
  const rootRef = useRef<HTMLDivElement>(null);
  const sidebarRef = useRef<HTMLElement>(null);
  const inViewRef = useRef(false);
  const reduce = useReducedMotion();
  const space = spaces[index];

  const switchTo = (next: number) => {
    if (next === index) return;
    setDirection(next > index ? 1 : -1);
    setIndex(next);
  };

  const toggleSidebar = useCallback(() => {
    setSidebar((s) => (s === "shown" ? "hidden" : "shown"));
  }, []);

  // ⌘S (Ctrl+S elsewhere) toggles the sidebar while the window is on screen,
  // the same shortcut rac uses.
  useEffect(() => {
    const el = rootRef.current;
    if (!el) return;
    const io = new IntersectionObserver(([entry]) => (inViewRef.current = entry.isIntersecting), {
      threshold: 0.35,
    });
    io.observe(el);
    const onKey = (e: KeyboardEvent) => {
      if (!inViewRef.current || e.altKey || e.shiftKey) return;
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

  const slide = reduce ? 0 : 36;
  const variants = {
    enter: (dir: number) => ({ opacity: 0, transform: `translateX(${dir * slide}%)` }),
    center: { opacity: 1, transform: "translateX(0%)" },
    exit: (dir: number) => ({ opacity: 0, transform: `translateX(${dir * -slide}%)` }),
  };
  const swap = { duration: reduce ? 0.2 : 0.42, ease: [0.32, 0.72, 0, 1] as const };

  return (
    <LazyMotion features={domAnimation} strict>
      <div className="bm-wrap">
        <div className="bm-controls">
          <button type="button" className="bm-toggle press" onClick={toggleSidebar}>
            <span>{sidebar === "shown" ? "Hide the sidebar" : "Show the sidebar"}</span>
            <kbd>⌘S</kbd>
          </button>
          <p>
            {sidebar === "shown"
              ? "Or switch spaces with the dots at the bottom of the sidebar."
              : "Point at the window’s left edge to peek at it."}
          </p>
        </div>
        <div ref={rootRef} className="bm" data-space={space.key} data-sidebar={sidebar}>
          <p className="sr-only">
            {`An illustration of a rac window in the ${space.name} space${
              sidebar === "shown" ? "" : ", with the sidebar hidden"
            }.`}
          </p>
          <div
            className="bm-window"
            onPointerMove={(e) => {
              // A peeking sidebar slides in under a still pointer, so it never
              // sees pointerenter. Track the pointer across the window instead.
              if (sidebar !== "peek" || !sidebarRef.current) return;
              const right = sidebarRef.current.getBoundingClientRect().right;
              if (e.clientX > right + 12) setSidebar("hidden");
            }}
            onPointerLeave={() => setSidebar((s) => (s === "peek" ? "hidden" : s))}
          >
            <div className="bm-page" aria-hidden="true">
              <AnimatePresence initial={false} mode="popLayout">
                <m.div
                  key={space.key}
                  className="bm-page-inner"
                  initial={{ opacity: 0, transform: reduce ? "none" : "translateY(1.2em)" }}
                  animate={{ opacity: 1, transform: "translateY(0em)" }}
                  exit={{ opacity: 0, transition: { duration: 0.15 } }}
                  transition={{ duration: reduce ? 0.2 : 0.5, ease: [0.23, 1, 0.32, 1], delay: 0.06 }}
                >
                  <Page space={space} />
                </m.div>
              </AnimatePresence>
            </div>

            {sidebar !== "shown" && (
              <div
                className="bm-edge"
                onPointerEnter={() => setSidebar("peek")}
                onClick={() => setSidebar("peek")}
                aria-hidden="true"
              />
            )}

            <aside className="bm-sidebar" ref={sidebarRef}>
              <div aria-hidden="true">
                <SidebarTop />
              </div>
              <div className="bm-address" aria-hidden="true">
                <Lock />
                <AnimatePresence initial={false} mode="popLayout">
                  <m.span
                    key={space.address}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    transition={{ duration: 0.18 }}
                  >
                    {space.address}
                  </m.span>
                </AnimatePresence>
              </div>

              <div aria-hidden="true">
                <Favorites />
              </div>

              <div className="bm-lists" aria-hidden="true">
                <AnimatePresence initial={false} custom={direction} mode="popLayout">
                  <m.div
                    key={space.key}
                    className="bm-list"
                    custom={direction}
                    variants={variants}
                    initial="enter"
                    animate="center"
                    exit="exit"
                    transition={swap}
                  >
                    <SpaceLists space={space} />
                  </m.div>
                </AnimatePresence>
              </div>

              <div className="bm-foot">
                <span className="bm-space-name" aria-hidden="true">{space.name}</span>
                <span className="bm-dots">
                  {spaces.map((s, i) => (
                    <button
                      key={s.key}
                      type="button"
                      className="bm-dot"
                      data-active={i === index}
                      data-dot={s.key}
                      aria-label={`Switch to the ${s.name} space`}
                      aria-pressed={i === index}
                      tabIndex={sidebar === "hidden" ? -1 : 0}
                      onClick={() => switchTo(i)}
                    />
                  ))}
                </span>
              </div>
            </aside>
          </div>
        </div>

      </div>
    </LazyMotion>
  );
}
