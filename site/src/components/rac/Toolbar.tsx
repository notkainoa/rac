import { BackIcon, ChatIcon, ForwardIcon, PuzzleIcon, ReloadIcon, ShieldIcon, SidebarIcon, TuneIcon } from "./icons";

// The toolbar inside the page card. Only the sidebar and Chat buttons do
// anything.
export function Toolbar({
  host,
  path,
  onSidebar,
  chat,
}: {
  host?: string;
  path?: string;
  onSidebar?: () => void;
  chat?: { open: boolean; toggle: () => void };
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
      <span className="rac-tool" aria-hidden="true">
        <TuneIcon />
      </span>
      <span className="rac-tool" aria-hidden="true">
        <ShieldIcon />
      </span>
      <span className="rac-tool" aria-hidden="true">
        <PuzzleIcon />
      </span>
      {/* rac's Chat pill, shown only while AI is on. */}
      {chat && (
        <button type="button" className="rac-chat" aria-expanded={chat.open} onClick={chat.toggle}>
          <ChatIcon />
          Chat
        </button>
      )}
    </div>
  );
}
