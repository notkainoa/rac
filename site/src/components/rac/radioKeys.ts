import type { KeyboardEvent } from "react";

// Arrow keys, Home, and End move the choice within a role="radiogroup", as
// native radio buttons do. Put this on the group and give only the checked
// radio tabIndex 0, so Tab moves past the group in one step.
const STEPS: Record<string, number> = { ArrowRight: 1, ArrowDown: 1, ArrowLeft: -1, ArrowUp: -1 };

export function onRadioKeys(e: KeyboardEvent<HTMLElement>) {
  const radios = [...e.currentTarget.querySelectorAll<HTMLElement>('[role="radio"]')];
  if (!radios.length) return;
  const i = radios.indexOf(document.activeElement as HTMLElement);
  let next: number;
  if (e.key in STEPS) next = (i + STEPS[e.key] + radios.length) % radios.length;
  else if (e.key === "Home") next = 0;
  else if (e.key === "End") next = radios.length - 1;
  else return;
  e.preventDefault();
  radios[next].focus();
  radios[next].click();
}
