import { useState, type CSSProperties } from "react";
import "./rac-ui.css";
import { favorites, sites } from "./data";
import { Page } from "./Pages";
import { presets, selectedTab, tint, type Mode } from "./theme";
import { Toolbar } from "./Toolbar";
import { AutoIcon, Favicon, MoonIcon, MoreIcon, PlusIcon, ProfileIcon, SearchIcon, SunIcon } from "./icons";

// rac's space editor, working: rename the space, pick light, dark or auto,
// one of the eight colors, and an emoji for the switcher. The window behind
// it re-tints with the browser's own formula.

const EMOJI = ["🌿", "🌊", "☕️", "📚", "🎨", "🏔️", "🍋", "🌙", "🧭", "🎧", "🪴", "✈️", "🧪", "🍞", "📷", "🛠️"];

export default function SpaceEditor() {
  const [name, setName] = useState("Garden");
  const [preset, setPreset] = useState(4);
  const [mode, setMode] = useState<Mode>("auto");
  const [icon, setIcon] = useState("");

  const style = {
    "--t-l": tint(preset, false),
    "--t-d": tint(preset, true),
    "--sel-l": selectedTab(preset, false),
    "--sel-d": selectedTab(preset, true),
  } as CSSProperties;

  const modes: { id: Mode; label: string; Icon: typeof SunIcon }[] = [
    { id: "auto", label: "Match the system", Icon: AutoIcon },
    { id: "light", label: "Light", Icon: SunIcon },
    { id: "dark", label: "Dark", Icon: MoonIcon },
  ];

  return (
    <div className="rac se" data-mode={mode === "auto" ? undefined : mode}>
      <div className="rac-window se-window" style={style}>
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
                {icon ? <span className="se-emoji">{icon}</span> : <span className="rac-space-dot" />}
                <span className="se-name">{name.trim() || "Space 2"}</span>
              </div>
              <div className="rac-row">
                <span className="rac-row-hit">
                  <Favicon glyph="leaf" color="#3EB489" className="rac-row-icon" />
                  <span className="rac-row-title">Seed catalog</span>
                </span>
              </div>
              <div className="rac-divider" />
              <div className="rac-row rac-new">
                <PlusIcon className="rac-row-icon" />
                <span>New Tab</span>
              </div>
              <div className="rac-row" data-selected="true">
                <span className="rac-row-hit">
                  <Favicon glyph="drop" color="#3A88C4" className="rac-row-icon" />
                  <span className="rac-row-title">Watering schedule</span>
                </span>
              </div>
              <div className="rac-row">
                <span className="rac-row-hit">
                  <Favicon glyph="tri" color="#E3AC38" className="rac-row-icon" />
                  <span className="rac-row-title">Raised beds, a guide</span>
                </span>
              </div>
            </div>
          </div>
          <div className="rac-bottom">
            <ProfileIcon className="rac-bottom-icon" />
            <div className="rac-dots">
              <span className="rac-dot" />
              {icon ? <span className="rac-dot se-dot-emoji">{icon}</span> : <span className="rac-dot" data-on="true" />}
              <span className="rac-dot-add">
                <PlusIcon />
              </span>
            </div>
            <MoreIcon className="rac-bottom-icon" />
          </div>
        </aside>
        <div className="rac-card se-card" aria-hidden="true">
          <Toolbar host="sky.example.com" />
          <div className="rac-page">
            <Page id="weather" />
          </div>
        </div>

        <div className="se-pop" role="group" aria-label="Edit space">
          <div className="se-top">
            <label className="se-field">
              <span className="sr-only">Space name</span>
              <input value={name} maxLength={24} onChange={(e) => setName(e.target.value)} placeholder="Space 2" spellCheck={false} />
            </label>
            <div className="se-modes" role="radiogroup" aria-label="Appearance">
              {modes.map(({ id, label, Icon }) => (
                <button
                  key={id}
                  type="button"
                  role="radio"
                  aria-checked={mode === id}
                  aria-label={label}
                  title={label}
                  className="se-mode"
                  onClick={() => setMode(id)}
                >
                  <Icon />
                </button>
              ))}
            </div>
          </div>
          <div className="se-swatches" role="radiogroup" aria-label="Color">
            {presets.map((p, i) => (
              <button
                key={p.name}
                type="button"
                role="radio"
                aria-checked={preset === i}
                aria-label={p.name}
                title={p.name}
                className="se-swatch"
                style={{ "--c": p.swatch } as CSSProperties}
                onClick={() => setPreset(i)}
              />
            ))}
          </div>
          <div className="se-emoji-area">
            <div className="se-search">
              <span className="se-search-field">
                <SearchIcon />
                Search emoji
              </span>
              <button
                type="button"
                className="se-nodot"
                aria-label="Use a dot instead of an emoji"
                aria-pressed={!icon}
                onClick={() => setIcon("")}
              >
                <i />
              </button>
            </div>
            <div className="se-grid" role="radiogroup" aria-label="Emoji">
              {EMOJI.map((e) => (
                <button key={e} type="button" role="radio" aria-checked={icon === e} className="se-e" onClick={() => setIcon(e)}>
                  {e}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
