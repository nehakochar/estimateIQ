import { useState, useEffect } from "react";
import { useAppSelector } from "@/store";
import { portfolioData } from "@/data/portfolio";

interface FeatureRow {
  reqId: string;
  reqDesc: string;
  featureName: string;
  frontend: number;
  backend: number;
}

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
      ...(() => { const h = defaultHrs(req.comp); return { frontend: h.fe, backend: h.be }; })(),
    }))
  );
}

export function EstimatePanel() {
  const { selectedProjectId } = useAppSelector((s) => s.workspace);
  const project = portfolioData.find((p) => p.id === selectedProjectId);
  const [rows, setRows] = useState<FeatureRow[]>([]);

  useEffect(() => {
    setRows(project ? buildRows(project.requirements) : []);
  }, [selectedProjectId]);

  const update = (reqId: string, featureName: string, field: "frontend" | "backend", val: number) =>
    setRows((prev) =>
      prev.map((r) => r.reqId === reqId && r.featureName === featureName ? { ...r, [field]: val } : r)
    );

  const totalFE = rows.reduce((s, r) => s + (r.frontend || 0), 0);
  const totalBE = rows.reduce((s, r) => s + (r.backend || 0), 0);
  const grand   = totalFE + totalBE;

  const grouped = project?.requirements
    .filter((req) => (req.features ?? []).length > 0)
    .map((req) => ({ req, features: rows.filter((r) => r.reqId === req.id) })) ?? [];

  if (!project || grouped.length === 0) {
    return (
      <div>
        <div className="section-hdr"><h2>Effort Costing Engines</h2></div>
        <div className="card">
          <p className="card-sub">No features found. Add features to requirements first.</p>
        </div>
      </div>
    );
  }

  return (
    <div>
      <div className="section-hdr">
        <h2>Effort Costing Engines</h2>
        <span className="ai-tag">Feature-Based Estimation</span>
      </div>

      {/* Summary cards */}
      <div className="estimate-summary-grid">
        <SummaryCard label="Frontend Total" value={totalFE} color="var(--accent2)" />
        <SummaryCard label="Backend Total"  value={totalBE} color="var(--sky)" />
        <SummaryCard label="Grand Total"    value={grand}   color="var(--accent3)" highlight />
      </div>

      {/* Requirement groups */}
      {grouped.map(({ req, features }) => {
        const reqFE = features.reduce((s, r) => s + (r.frontend || 0), 0);
        const reqBE = features.reduce((s, r) => s + (r.backend || 0), 0);

        return (
          <div className="estimate-req-card" key={req.id}>
            {/* Requirement header */}
            <div className="estimate-req-header">
              <div className="estimate-req-id-wrap">
                <span className="estimate-req-id">{req.id}</span>
                <span className="estimate-req-desc">{req.desc}</span>
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
                    onChange={(e) => update(req.id, row.featureName, "frontend", Number(e.target.value))}
                  />
                  <span className="estimate-input-unit">h</span>
                </div>

                <div className="estimate-input-cell">
                  <input
                    type="number"
                    min={0}
                    className="est-input"
                    value={row.backend}
                    onChange={(e) => update(req.id, row.featureName, "backend", Number(e.target.value))}
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
