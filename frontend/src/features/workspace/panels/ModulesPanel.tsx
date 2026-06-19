import { useAppSelector } from "@/store";
import { portfolioData } from "@/data/portfolio";

export function ModulesPanel() {
  const { selectedProjectId } = useAppSelector((s) => s.workspace);
  const project = portfolioData.find((p) => p.id === selectedProjectId);

  return (
    <div>
      <div className="section-hdr">
        <h2>System Architecture Blocks</h2>
      </div>
      <div className="module-grid">
        {!project?.modules.length ? (
          <div style={{ color: "var(--text3)" }}>No tracking modules provisioned.</div>
        ) : (
          project.modules.map((m, i) => (
            <div className="module-card" key={i}>
              <div style={{ fontSize: 10, fontFamily: "'DM Mono', monospace", color: "var(--text3)" }}>{m.type}</div>
              <div className="card-title" style={{ margin: "4px 0 8px" }}>{m.title}</div>
              <p style={{ fontSize: 12, color: "var(--text2)", lineHeight: 1.5 }}>{m.desc}</p>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
