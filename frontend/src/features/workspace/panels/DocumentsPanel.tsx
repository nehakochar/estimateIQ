import { useAppSelector } from "@/store";
import { portfolioData } from "@/data/portfolio";

export function DocumentsPanel() {
  const { selectedProjectId } = useAppSelector((s) => s.workspace);
  const project = portfolioData.find((p) => p.id === selectedProjectId);

  return (
    <div>
      <div className="section-hdr">
        <h2>Asset Inventory Matrix</h2>
      </div>
      <div className="card">
        <div className="card-title">Indexed Reference Documentation</div>
        <div className="doc-list">
          {!project?.docs.length ? (
            <p className="card-sub">No attachment records present.</p>
          ) : (
            project.docs.map((d, i) => (
              <div className="doc-row" key={i}>
                <span style={{ fontFamily: "'DM Mono', monospace", fontSize: 12 }}>{d}</span>
                <span className="doc-download">Download Asset 📥</span>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
