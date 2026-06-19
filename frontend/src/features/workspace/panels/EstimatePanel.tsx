import { useState } from "react";
import { useAppSelector } from "@/store";
import { portfolioData } from "@/data/portfolio";

interface FeatureRow {
  reqId: string;
  reqDesc: string;
  featureName: string;
  complexity: "High" | "Medium" | "Low";
  frontend: number;
  backend: number;
}

// ── Dummy data shown when no real project/features are available ─────────────
const DUMMY_ROWS: FeatureRow[] = [
  // Authentication & Access
  { reqId: "FR-01", reqDesc: "User Authentication & Role-Based Access Control", featureName: "Login with SSO / OAuth2", complexity: "High", frontend: 16, backend: 20 },
  { reqId: "FR-01", reqDesc: "User Authentication & Role-Based Access Control", featureName: "MFA enforcement flow", complexity: "High", frontend: 12, backend: 16 },
  { reqId: "FR-01", reqDesc: "User Authentication & Role-Based Access Control", featureName: "Token refresh & session mgmt", complexity: "High", frontend: 8, backend: 12 },
  { reqId: "FR-01", reqDesc: "User Authentication & Role-Based Access Control", featureName: "Role assignment on login", complexity: "High", frontend: 6, backend: 10 },

  // Dashboard & UI
  { reqId: "FR-02", reqDesc: "Admin Dashboard & Data Visualisation", featureName: "Dashboard layout & navigation", complexity: "Medium", frontend: 20, backend: 8 },
  { reqId: "FR-02", reqDesc: "Admin Dashboard & Data Visualisation", featureName: "Charts & KPI widgets", complexity: "Medium", frontend: 16, backend: 6 },
  { reqId: "FR-02", reqDesc: "Admin Dashboard & Data Visualisation", featureName: "Responsive mobile layout", complexity: "Medium", frontend: 12, backend: 2 },
  { reqId: "FR-02", reqDesc: "Admin Dashboard & Data Visualisation", featureName: "Export to PDF / CSV", complexity: "Medium", frontend: 8, backend: 12 },

  // Notifications
  { reqId: "FR-03", reqDesc: "Real-Time Notification & Alert System", featureName: "In-app notification centre", complexity: "Medium", frontend: 12, backend: 10 },
  { reqId: "FR-03", reqDesc: "Real-Time Notification & Alert System", featureName: "Email alert templates", complexity: "Medium", frontend: 4, backend: 8 },
  { reqId: "FR-03", reqDesc: "Real-Time Notification & Alert System", featureName: "WebSocket push events", complexity: "Medium", frontend: 8, backend: 14 },

  // API Integrations
  { reqId: "INT-01", reqDesc: "Third-Party API & Webhook Integrations", featureName: "Stripe payment integration", complexity: "High", frontend: 10, backend: 18 },
  { reqId: "INT-01", reqDesc: "Third-Party API & Webhook Integrations", featureName: "Webhook ingest & retry logic", complexity: "High", frontend: 4, backend: 16 },
  { reqId: "INT-01", reqDesc: "Third-Party API & Webhook Integrations", featureName: "Third-party OAuth connectors", complexity: "High", frontend: 6, backend: 14 },

  // Security
  { reqId: "SEC-01", reqDesc: "Data Security & Compliance Controls", featureName: "AES-256 encryption at rest", complexity: "Low", frontend: 2, backend: 8 },
  { reqId: "SEC-01", reqDesc: "Data Security & Compliance Controls", featureName: "TLS 1.3 in-transit config", complexity: "Low", frontend: 1, backend: 6 },
  { reqId: "SEC-01", reqDesc: "Data Security & Compliance Controls", featureName: "Audit trail & access logs", complexity: "Low", frontend: 6, backend: 10 },

  // Infrastructure
  { reqId: "INF-01", reqDesc: "CI/CD Pipeline & Cloud Infrastructure", featureName: "Docker & Kubernetes config", complexity: "High", frontend: 4, backend: 20 },
  { reqId: "INF-01", reqDesc: "CI/CD Pipeline & Cloud Infrastructure", featureName: "Auto-scaling policy setup", complexity: "High", frontend: 2, backend: 16 },
  { reqId: "INF-01", reqDesc: "CI/CD Pipeline & Cloud Infrastructure", featureName: "Deployment pipeline (GitHub Actions)", complexity: "High", frontend: 2, backend: 14 },
];

function defaultHrs(comp: string) {
  if (comp === "High")   return { fe: 16, be: 20 };
  if (comp === "Medium") return { fe: 8,  be: 12 };
  return                        { fe: 4,  be: 6  };
}

function buildRows(requirements: typeof portfolioData[0]["requirements"]): FeatureRow[] {
  return requirements.flatMap((req) =>
    (req.features ?? []).map((f) => ({
      reqId: req.id,
      reqDesc: req.desc,
      featureName: f.name,
      complexity: req.comp as "High" | "Medium" | "Low",
      ...(() => { const h = defaultHrs(req.comp); return { frontend: h.fe, backend: h.be }; })(),
    }))
  );
}

const COMPLEXITY_COLOR: Record<string, string> = {
  High:   "var(--accent3)",
  Medium: "var(--sky)",
  Low:    "var(--accent2)",
};

export function EstimatePanel() {
  const { selectedProjectId } = useAppSelector((s) => s.workspace);
  const project = portfolioData.find((p) => p.id === selectedProjectId);

  // Use real data if the project has features, otherwise fall back to dummy data
  const realRows = project ? buildRows(project.requirements) : [];
  const isDummy  = realRows.length === 0;
  const initialRows = isDummy ? DUMMY_ROWS : realRows;

  const [rows, setRows] = useState<FeatureRow[]>(initialRows);

  const update = (reqId: string, featureName: string, field: "frontend" | "backend", val: number) =>
    setRows((prev) =>
      prev.map((r) => r.reqId === reqId && r.featureName === featureName ? { ...r, [field]: val } : r)
    );

  const totalFE = rows.reduce((s, r) => s + (r.frontend || 0), 0);
  const totalBE = rows.reduce((s, r) => s + (r.backend || 0), 0);
  const grand   = totalFE + totalBE;

  // Group by reqId
  const groupMap = new Map<string, { reqId: string; reqDesc: string; complexity: string; features: FeatureRow[] }>();
  for (const row of rows) {
    if (!groupMap.has(row.reqId)) {
      groupMap.set(row.reqId, { reqId: row.reqId, reqDesc: row.reqDesc, complexity: row.complexity, features: [] });
    }
    groupMap.get(row.reqId)!.features.push(row);
  }
  const grouped = Array.from(groupMap.values());

  return (
    <div>
      <div className="section-hdr">
        <h2>Effort Costing Engine</h2>
        <span className="ai-tag">Feature-Based Estimation</span>
        {isDummy && (
          <span className="ai-tag" style={{ background: "rgba(255,180,0,0.12)", color: "var(--accent3)", marginLeft: 8 }}>
            Preview — Sample Data
          </span>
        )}
      </div>

      {/* Summary cards */}
      <div className="estimate-summary-grid">
        <SummaryCard label="Frontend Total" value={totalFE} color="var(--accent2)" />
        <SummaryCard label="Backend Total"  value={totalBE} color="var(--sky)" />
        <SummaryCard label="Grand Total"    value={grand}   color="var(--accent3)" highlight />
      </div>

      {/* Requirement groups */}
      {grouped.map(({ reqId, reqDesc, complexity, features }) => {
        const reqFE = features.reduce((s, r) => s + (r.frontend || 0), 0);
        const reqBE = features.reduce((s, r) => s + (r.backend || 0), 0);

        return (
          <div className="estimate-req-card" key={reqId}>
            {/* Requirement header */}
            <div className="estimate-req-header">
              <div className="estimate-req-id-wrap">
                <span className="estimate-req-id">{reqId}</span>
                <span
                  className="estimate-complexity-badge"
                  style={{ color: COMPLEXITY_COLOR[complexity], borderColor: COMPLEXITY_COLOR[complexity] }}
                >
                  {complexity}
                </span>
                <span className="estimate-req-desc">{reqDesc}</span>
              </div>
              <div className="estimate-req-totals">
                <span className="fe">FE: {reqFE}h</span>
                <span className="be">BE: {reqBE}h</span>
                <span className="total">{reqFE + reqBE}h</span>
              </div>
            </div>

            {/* Column headers */}
            <div className="estimate-col-headers">
              <span>Feature</span>
              <span className="col-right">
                <span className="estimate-col-fe">● </span>Frontend (hrs)
              </span>
              <span className="col-right">
                <span className="estimate-col-be">● </span>Backend (hrs)
              </span>
              <span className="col-right">Total</span>
            </div>

            {/* Feature rows */}
            {features.map((row) => (
              <div className="estimate-feature-row" key={row.featureName}>
                <span className="estimate-feature-name">{row.featureName}</span>

                <div className="estimate-input-cell">
                  <input
                    type="number"
                    min={0}
                    className="est-input"
                    value={row.frontend}
                    onChange={(e) => update(reqId, row.featureName, "frontend", Number(e.target.value))}
                  />
                  <span className="estimate-input-unit">h</span>
                </div>

                <div className="estimate-input-cell">
                  <input
                    type="number"
                    min={0}
                    className="est-input"
                    value={row.backend}
                    onChange={(e) => update(reqId, row.featureName, "backend", Number(e.target.value))}
                  />
                  <span className="estimate-input-unit">h</span>
                </div>

                <div className="estimate-row-total">
                  {(row.frontend || 0) + (row.backend || 0)}h
                </div>
              </div>
            ))}
          </div>
        );
      })}

      {/* Grand total footer */}
      <div className="estimate-grand-footer">
        <span className="estimate-grand-label">GRAND TOTAL</span>
        <span className="estimate-grand-fe">Frontend <strong>{totalFE}h</strong></span>
        <span className="estimate-grand-be">Backend <strong>{totalBE}h</strong></span>
        <span className="estimate-grand-total">{grand}h</span>
      </div>
    </div>
  );
}

function SummaryCard({ label, value, color, highlight = false }: {
  label: string; value: number; color: string; highlight?: boolean;
}) {
  return (
    <div className={`estimate-summary-card${highlight ? " highlight" : ""}`}>
      <div className="estimate-summary-label">{label}</div>
      <div className="estimate-summary-value" style={{ color }}>{value}h</div>
    </div>
  );
}
