import React, { useEffect, useState } from 'react';
import { useAppSelector } from '@/store';
import { useGetProjectEstimatesQuery, useGenerateProjectEstimatesMutation } from '@/services/estimationApi';
import { ProjectEstimatesResponse, SubFeatureItem } from '@/types/estimation';
import { Spinner } from '@/components/Spinner';
import { useToast } from '@/hooks/useToast';

// Row = a sub-feature flattened with its parent requirement context for display
interface Row extends SubFeatureItem {
  requirement_id: string;
  req_id: string;
  req_desc: string;
  // complexity is already typed as 'Low' | 'Medium' | 'High' in SubFeatureItem
}

export function EstimatePanel() {
  const { selectedProjectId } = useAppSelector((s) => s.workspace);
  const { showSuccess, showError, showInfo } = useToast();

  // Trigger generation when the tab opens and estimates are not started
  const [generateEstimates, { isLoading: genLoading }] = useGenerateProjectEstimatesMutation();

  const {
    data: estimateData,
    isLoading,
    error,
    refetch,
  } = useGetProjectEstimatesQuery(selectedProjectId ?? '', {
    pollingInterval: 3000,
    skip: !selectedProjectId,
  });

  const handleManualGenerate = async () => {
    if (!selectedProjectId) return;
    showInfo("Triggering estimation...", "The effort estimates generation task has been queued.");
    try {
      await generateEstimates(selectedProjectId).unwrap();
      showSuccess("Estimation generation started", "Estimates are being calculated in the background.");
    } catch (err: any) {
      showError("Failed to trigger estimation", err?.data?.detail || "An unexpected error occurred.");
    }
  };

  const getButtonLabel = () => {
    if (genLoading || (estimateData && estimateData.estimation_status === 'generating')) {
      return 'Generating...';
    }
    if (estimateData) {
      if (estimateData.estimation_status === 'completed') {
        return 'Regenerate Estimates';
      }
      if (estimateData.estimation_status === 'failed') {
        return 'Retry Estimation';
      }
    }
    return 'Generate Estimates';
  };

  // Auto‑trigger generation on first load if needed
  useEffect(() => {
    if (!estimateData) return;
    if (estimateData.estimation_status === 'not_started' && !genLoading) {
      generateEstimates(selectedProjectId!);
    }
  }, [estimateData, generateEstimates, genLoading, selectedProjectId]);

  // Local editable rows derived from API data
  const [rows, setRows] = useState<Row[]>([]);

  // When API data arrives (and status is completed), populate rows
  useEffect(() => {
    if (!estimateData) return;
    if (estimateData.estimation_status !== 'completed') return;
    const flat: Row[] = [];
    estimateData.requirements.forEach((req) => {
      req.sub_features.forEach((sf) => {
        flat.push({
          ...sf,  // sf fields first (incl. complexity already typed correctly)
          requirement_id: req.requirement_id,
          req_id: req.req_id,
          req_desc: req.description,
        });
      });
    });
    setRows(flat);
  }, [estimateData]);

  const update = (requirementId: string, subFeatureId: string, field: 'frontend_hours' | 'backend_hours' | 'mobile_hours', val: number) => {
    setRows((prev) =>
      prev.map((r) =>
        r.requirement_id === requirementId && r.id === subFeatureId ? { ...r, [field]: val } : r
      )
    );
  };

  // Aggregate totals
  const totalFE = rows.reduce((s, r) => s + (r.frontend_hours || 0), 0);
  const totalBE = rows.reduce((s, r) => s + (r.backend_hours || 0), 0);
  const totalMob = rows.reduce((s, r) => s + (r.mobile_hours || 0), 0);
  const grand = totalFE + totalBE + totalMob;

  // Group rows by requirement for display
  const groupMap = new Map<string, { reqId: string; reqDesc: string; complexity: string; features: Row[] }>();
  rows.forEach((row) => {
    if (!groupMap.has(row.requirement_id)) {
      groupMap.set(row.requirement_id, {
        reqId: row.req_id,
        reqDesc: row.req_desc,
        complexity: row.complexity,
        features: [],
      });
    }
    groupMap.get(row.requirement_id)!.features.push(row);
  });
  const grouped = Array.from(groupMap.values());

  // UI helpers
  const COMPLEXITY_COLOR: Record<string, string> = {
    High: 'var(--accent3)',
    Medium: 'var(--sky)',
    Low: 'var(--accent2)',
  };

  if (!selectedProjectId) {
    return <div className="estimate-panel">Select a project to view estimates.</div>;
  }

  if (isLoading || genLoading || (estimateData && estimateData.estimation_status === 'generating')) {
    return (
      <div className="estimate-panel">
        <Spinner />
        <span>Preparing estimates…</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="estimate-panel error">
        <p>Failed to load estimates: {(error as any).data?.detail || 'Unknown error'}</p>
        <button onClick={() => refetch()}>Retry</button>
      </div>
    );
  }

  return (
    <div className="estimate-panel">
      <div className="section-hdr">
        <h2>Effort Costing Engine</h2>
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          <button
            className="btn btn-ghost"
            onClick={handleManualGenerate}
            disabled={genLoading || (estimateData && estimateData.estimation_status === 'generating')}
            style={{ padding: '6px 12px', fontSize: '12px' }}
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ marginRight: '4px' }}>
              <path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"/>
              <path d="m5 3 1 2.5L8.5 6 6 7 5 9.5 4 7 1.5 6 4 6z"/>
              <path d="m19 17 1 2.5 2.5.5-2.5 1-1 2.5-1-2.5-2.5-1 2.5-1z"/>
            </svg>
            {getButtonLabel()}
          </button>
          <span className="ai-tag">Feature‑Based Estimation</span>
        </div>
      </div>

      {/* Summary cards */}
      <div className="estimate-summary-grid">
        <SummaryCard label="Frontend Total" value={totalFE} color="var(--accent2)" />
        <SummaryCard label="Backend Total" value={totalBE} color="var(--sky)" />
        <SummaryCard label="Mobile Total" value={totalMob} color="var(--accent3)" />
        <SummaryCard label="Grand Total" value={grand} color="var(--accent3)" highlight />
      </div>

      {/* Requirement groups */}
      {grouped.map(({ reqId, reqDesc, complexity, features }) => {
        const reqFE = features.reduce((s, r) => s + (r.frontend_hours || 0), 0);
        const reqBE = features.reduce((s, r) => s + (r.backend_hours || 0), 0);
        const reqMob = features.reduce((s, r) => s + (r.mobile_hours || 0), 0);
        const reqTotal = reqFE + reqBE + reqMob;
        return (
          <div className="estimate-req-card" key={reqId}>
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
                <span className="mob">Mob: {reqMob}h</span>
                <span className="total">{reqTotal}h</span>
              </div>
            </div>

            <div className="estimate-col-headers">
              <span>Feature</span>
              <span className="col-right">
                <span className="estimate-col-fe">● </span>Frontend (hrs)
              </span>
              <span className="col-right">
                <span className="estimate-col-be">● </span>Backend (hrs)
              </span>
              <span className="col-right">
                <span className="estimate-col-mob">● </span>Mobile (hrs)
              </span>
              <span className="col-right">Total</span>
            </div>

            {features.map((row) => (
              <div className="estimate-feature-row" key={row.id}>
                <span className="estimate-feature-name">{row.sub_feature_name}</span>
                <div className="estimate-input-cell">
                  <input
                    type="number"
                    min={0}
                    className="est-input"
                    aria-label={`Frontend hours for ${row.sub_feature_name}`}
                    value={row.frontend_hours ?? 0}
                    onChange={(e) =>
                      update(row.requirement_id, row.id, 'frontend_hours', Number(e.target.value))
                    }
                  />
                  <span className="estimate-input-unit">h</span>
                </div>
                <div className="estimate-input-cell">
                  <input
                    type="number"
                    min={0}
                    className="est-input"
                    aria-label={`Backend hours for ${row.sub_feature_name}`}
                    value={row.backend_hours ?? 0}
                    onChange={(e) =>
                      update(row.requirement_id, row.id, 'backend_hours', Number(e.target.value))
                    }
                  />
                  <span className="estimate-input-unit">h</span>
                </div>
                <div className="estimate-input-cell">
                  <input
                    type="number"
                    min={0}
                    className="est-input"
                    aria-label={`Mobile hours for ${row.sub_feature_name}`}
                    value={row.mobile_hours ?? 0}
                    onChange={(e) =>
                      update(row.requirement_id, row.id, 'mobile_hours', Number(e.target.value))
                    }
                  />
                  <span className="estimate-input-unit">h</span>
                </div>
                <div className="estimate-row-total">
                  {(row.frontend_hours || 0) + (row.backend_hours || 0) + (row.mobile_hours || 0)}h
                </div>
              </div>
            ))}
          </div>
        );
      })}

      {/* Grand total footer */}
      <div className="estimate-grand-footer">
        <span className="estimate-grand-label">GRAND TOTAL</span>
        <span className="estimate-grand-fe">
          Frontend <strong>{totalFE}h</strong>
        </span>
        <span className="estimate-grand-be">
          Backend <strong>{totalBE}h</strong>
        </span>
        <span className="estimate-grand-mob">
          Mobile <strong>{totalMob}h</strong>
        </span>
        <span className="estimate-grand-total">
          {grand}h
        </span>
      </div>
    </div>
  );
}

function SummaryCard({ label, value, color, highlight = false }: { label: string; value: number; color: string; highlight?: boolean }) {
  return (
    <div className={`estimate-summary-card${highlight ? ' highlight' : ''}`}>
      <div className="estimate-summary-label">{label}</div>
      <div className="estimate-summary-value" style={{ color }}>
        {value}h
      </div>
    </div>
  );
}
