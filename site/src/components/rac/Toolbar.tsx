import { BackIcon, ForwardIcon, PuzzleIcon, ReloadIcon, ShieldIcon, SidebarIcon, SparkIcon, TuneIcon } from "./icons";

// The toolbar inside the page card. Only the sidebar and assistant buttons
// do anything.
export function Toolbar({
  host,
  path,
  onSidebar,
  assistant,
}: {
  host?: string;
  path?: string;
  onSidebar?: () => void;
  assistant?: { on: boolean; toggle: () => void };
}) {
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
      {assistant && (
        <button
          type="button"
          className="rac-tool rac-tool-assistant"
          aria-label="Assistant"
          aria-pressed={assistant.on}
          title="Assistant"
          onClick={assistant.toggle}
        >
          <SparkIcon />
        </button>
      )}
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
