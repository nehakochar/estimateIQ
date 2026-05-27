import { useAppDispatch, useAppSelector } from "@/store";
import { setReqTab } from "@/store/slices/workspaceSlice";
import { useSearchByCategoryQuery } from "@/services/retrievalApi";
import { REQ_TABS, type ReqTab } from "@/data/portfolio";

// Map backend category names to frontend tab names
const CATEGORY_MAP: Record<string, string> = {
  "functional": "Functional",
  "non_functional": "Non-Functional",
  "ui_ux": "UI/UX",
  "integrations": "Integrations",
  "security_compliance": "Security & Compliance",
  "data_validation": "Data & Validation",
  "workflow_roles": "Workflow & Roles",
  "infrastructure_deployment": "Infrastructure & Deployment",
  "risks_assumptions_dependencies": "Risks / Assumptions / Dependencies",
  "open_questions": "Open Questions",
  "out_of_scope": "Out of Scope",
};

// Reverse map: frontend tab names to backend category names
const TAB_TO_CATEGORY: Record<string, string> = Object.entries(CATEGORY_MAP).reduce(
  (acc, [key, val]) => ({ ...acc, [val]: key }),
  {}
);

export function RequirementsPanel() {
  const dispatch = useAppDispatch();
  const { selectedProjectId, activeReqTab } = useAppSelector((s) => s.workspace);

  // Convert tab name to backend category name
  const backendCategory = TAB_TO_CATEGORY[activeReqTab] || "functional";

  // Fetch requirements for the current category
  const { data, isLoading, error } = useSearchByCategoryQuery(
    {
      projectId: selectedProjectId || "",
      category: backendCategory,
      topK: 100,
    },
    {
      skip: !selectedProjectId,
    }
  );

  // Handle both cases: data could be the response object or the results array directly
  const requirements = Array.isArray(data) ? data : (Array.isArray(data?.results) ? data.results : []);

  return (
    <div>
      <div className="section-hdr">
        <h2>Functional Requirements Mapping</h2>
        <span className="ai-tag">NLP Parsing Core</span>
      </div>

      {/* Tabs */}
      <div className="req-tabs">
        {REQ_TABS.map((tab) => {
          return (
            <div
              key={tab}
              className={`req-tab${activeReqTab === tab ? " active" : ""}`}
              onClick={() => dispatch(setReqTab(tab as ReqTab))}
            >
              {tab}
              {data && (
                <span style={{ marginLeft: 5, fontSize: 9, background: "rgba(108,99,255,0.2)", color: "var(--accent2)", padding: "1px 5px", borderRadius: 8 }}>
                  {data.total_results}
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
              <th style={{ width: 130 }}>Confidence</th>
              <th style={{ width: 130 }}>Type</th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <tr>
                <td colSpan={4} style={{ textAlign: "center", color: "var(--text3)", padding: 32 }}>
                  Loading requirements…
                </td>
              </tr>
            ) : error ? (
              <tr>
                <td colSpan={4} style={{ textAlign: "center", color: "#f87171", padding: 32 }}>
                  Failed to load requirements. Please try again.
                </td>
              </tr>
            ) : requirements.length === 0 ? (
              <tr>
                <td colSpan={4} style={{ textAlign: "center", color: "var(--text3)", padding: 32 }}>
                  No requirements in this category.
                </td>
              </tr>
            ) : (
              requirements.map((req, idx) => (
                <tr key={req.chunk_id}>
                  <td style={{ fontFamily: "'DM Mono', monospace", color: "var(--accent2)" }}>
                    {req.section ? `${req.section.slice(0, 8)}` : `REQ-${String(idx + 1).padStart(3, "0")}`}
                  </td>
                  <td>{req.text}</td>
                  <td>
                    <span className="badge b-pipeline">
                      {Math.round(req.confidence_score * 100)}%
                    </span>
                  </td>
                  <td>
                    <span className="badge b-pending">{req.chunk_type}</span>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
