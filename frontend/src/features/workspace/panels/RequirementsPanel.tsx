import { useAppDispatch, useAppSelector } from "@/store";
import { setReqTab } from "@/store/slices/workspaceSlice";
import { portfolioData, REQ_TABS, type ReqTab } from "@/data/portfolio";

export function RequirementsPanel() {
  const dispatch = useAppDispatch();
  const { selectedProjectId, activeReqTab } = useAppSelector((s) => s.workspace);
  const project = portfolioData.find((p) => p.id === selectedProjectId);

  const filtered = project?.requirements.filter(
    (r) => (r.category ?? "Functional") === activeReqTab
  ) ?? [];

  return (
    <div>
      <div className="section-hdr">
        <h2>Functional Requirements Mapping</h2>
        <span className="ai-tag">NLP Parsing Core</span>
      </div>

      {/* Tabs */}
      <div className="req-tabs">
        {REQ_TABS.map((tab) => {
          const count = project?.requirements.filter((r) => (r.category ?? "Functional") === tab).length ?? 0;
          return (
            <div
              key={tab}
              className={`req-tab${activeReqTab === tab ? " active" : ""}`}
              onClick={() => dispatch(setReqTab(tab as ReqTab))}
            >
              {tab}
              {count > 0 && (
                <span style={{ marginLeft: 5, fontSize: 9, background: "rgba(108,99,255,0.2)", color: "var(--accent2)", padding: "1px 5px", borderRadius: 8 }}>
                  {count}
                </span>
              )}
            </div>
          );
        })}
      </div>

      <div className="card">
        <table className="req-table">
          <thead>
            <tr>
              <th style={{ width: 110 }}>ID Code</th>
              <th>System Component Description Specification</th>
              <th style={{ width: 130 }}>Priority Level</th>
              <th style={{ width: 130 }}>Complexity Metric</th>
            </tr>
          </thead>
          <tbody>
            {filtered.length === 0 ? (
              <tr>
                <td colSpan={4} style={{ textAlign: "center", color: "var(--text3)", padding: 32 }}>
                  No requirements in this category.
                </td>
              </tr>
            ) : (
              filtered.map((r) => (
                <tr key={r.id}>
                  <td style={{ fontFamily: "'DM Mono', monospace", color: "var(--accent2)" }}>{r.id}</td>
                  <td>{r.desc}</td>
                  <td><span className="badge b-pending">{r.priority}</span></td>
                  <td><span className="badge b-pipeline">{r.comp}</span></td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
