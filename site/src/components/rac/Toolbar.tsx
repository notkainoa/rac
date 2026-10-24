import { BackIcon, ForwardIcon, PuzzleIcon, ReloadIcon, ShieldIcon, SidebarIcon, TuneIcon } from "./icons";

// The toolbar inside the page card. Only the sidebar button does anything.
export function Toolbar({ host, path, onSidebar }: { host?: string; path?: string; onSidebar?: () => void }) {
  return (
    <div className="rac-toolbar">
      {onSidebar ? (
        <button type="button" className="rac-tool" aria-label="Show or hide the sidebar (⌘S)" title="⌘S" onClick={onSidebar}>
          <SidebarIcon />
        </button>
      ) : (
        <span className="rac-tool" aria-hidden="true">
          <SidebarIcon />
        </span>
      )}
      <span className="rac-tool" aria-hidden="true">
        <BackIcon />
      </span>
      <span className="rac-tool rac-tool-off" aria-hidden="true">
        <ForwardIcon />
      </span>
      <span className="rac-tool" aria-hidden="true">
        <ReloadIcon />
      </span>
      <div className="rac-url" data-empty={!host || undefined} aria-hidden="true">
        {host && (
          <>
            {host}
            <span>{path}</span>
          </>
        )}
      </div>
      <span className="rac-tool" aria-hidden="true">
        <TuneIcon />
      </span>
      <span className="rac-tool" aria-hidden="true">
        <ShieldIcon />
      </span>
      <span className="rac-tool" aria-hidden="true">
        <PuzzleIcon />
      </span>
    </div>
  );
}
