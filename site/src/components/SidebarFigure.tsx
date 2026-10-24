import "./browser-mock.css";
import { Favorites, SidebarTop, SpaceLists, spaces } from "./MockParts";

// The three demo spaces side by side. Favorites stay the same across all
// three; pinned tabs, open tabs and the color belong to each space. Rendered
// at build time with no client script.
export default function SidebarFigure() {
  return (
    <div className="bm-wrap sf">
      <div className="sf-row">
        {spaces.map((space, index) => (
          <figure key={space.key} className="bm sf-item" data-space={space.key}>
            <div className="sf-sidebar">
              <SidebarTop />
              <Favorites />
              <div className="bm-lists">
                <SpaceLists space={space} />
              </div>
              <div className="bm-foot" data-part="dots">
                <span className="bm-space-name">{space.name}</span>
                <span className="bm-dots">
                  {spaces.map((s, i) => (
                    <span key={s.key} className="bm-dot" data-active={i === index} />
                  ))}
                </span>
              </div>
            </div>
            <figcaption className="sr-only">The {space.name} space's sidebar.</figcaption>
          </figure>
        ))}
      </div>
    </div>
  );
}
