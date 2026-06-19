import { useState, useMemo, useEffect } from "react";
import { useParams } from "react-router-dom";
import {
  useGetProjectRequirementsQuery,
  useReextractDocumentMutation,
  type ExtractedRequirementItem,
} from "@/services/extractionApi";
import { useGetProjectStatusQuery } from "@/services/documentsApi";

// ── Category tabs ─────────────────────────────────────────────────────────────
const TABS = [
  { value: null,             label: "All" },
  { value: "Functional",     label: "Functional" },
  { value: "Non-Functional", label: "Non-Functional" },
  { value: "Technical",      label: "Technical" },
  { value: "Security",       label: "Security" },
  { value: "Integration",    label: "Integration" },
  { value: "Compliance",     label: "Compliance" },
  { value: "Infrastructure", label: "Infrastructure" },
  { value: "Support",        label: "Support" },
];

// ── Colours ───────────────────────────────────────────────────────────────────
const TYPE_COLOR: Record<string, { bg: string; text: string; border: string }> = {
  "Functional":      { bg: "rgba(99,102,241,.12)",  text: "#818cf8", border: "rgba(99,102,241,.3)"  },
  "Non-Functional":  { bg: "rgba(245,158,11,.12)",  text: "#fbbf24", border: "rgba(245,158,11,.3)"  },
  "Technical":       { bg: "rgba(59,130,246,.12)",  text: "#60a5fa", border: "rgba(59,130,246,.3)"  },
  "Security":        { bg: "rgba(239,68,68,.12)",   text: "#f87171", border: "rgba(239,68,68,.3)"   },
  "Integration":     { bg: "rgba(16,185,129,.12)",  text: "#34d399", border: "rgba(16,185,129,.3)"  },
  "Compliance":      { bg: "rgba(236,72,153,.12)",  text: "#f472b6", border: "rgba(236,72,153,.3)"  },
  "Infrastructure":  { bg: "rgba(107,114,128,.12)", text: "#9ca3af", border: "rgba(107,114,128,.3)" },
  "Support":         { bg: "rgba(20,184,166,.12)",  text: "#2dd4bf", border: "rgba(20,184,166,.3)"  },
};

const PRIORITY_COLOR: Record<string, { text: string; bg: string }> = {
  "Must Have":     { text: "#f87171", bg: "rgba(239,68,68,.10)"   },
  "Should Have":   { text: "#fbbf24", bg: "rgba(245,158,11,.10)"  },
  "Nice to Have":  { text: "#34d399", bg: "rgba(16,185,129,.10)"  },
  "Not Specified": { text: "#6b7280", bg: "rgba(75,85,99,.10)"    },
};

// ── Sub-components ────────────────────────────────────────────────────────────
function TypeBadge({ label }: { label: string }) {
  const c = TYPE_COLOR[label] ?? { bg: "rgba(75,85,99,.12)", text: "#6b7280", border: "rgba(75,85,99,.3)" };
  return (
    <span style={{ display:"inline-block", padding:"2px 10px", borderRadius:"999px",
      fontSize:"11px", fontWeight:500, background:c.bg, color:c.text, border:`1px solid ${c.border}`,
      whiteSpace:"nowrap" }}>
      {label}
    </span>
  );
}

function PriorityPill({ priority }: { priority: string }) {
  const c = PRIORITY_COLOR[priority] ?? PRIORITY_COLOR["Not Specified"];
  return (
    <span style={{ display:"inline-block", padding:"2px 8px", borderRadius:"999px",
      fontSize:"10px", fontWeight:500, background:c.bg, color:c.text, whiteSpace:"nowrap" }}>
      {priority}
    </span>
  );
}

function RequirementRow({ item, isLast }: { item: ExtractedRequirementItem; isLast: boolean }) {
  const [expanded, setExpanded] = useState(false);
  return (
    <div
      style={{ borderBottom: isLast ? "none" : "1px solid var(--border)", cursor:"pointer" }}
      onClick={() => setExpanded(v => !v)}
      onMouseEnter={e => (e.currentTarget.style.background = "rgba(255,255,255,.02)")}
      onMouseLeave={e => (e.currentTarget.style.background = "transparent")}
    >
      <div style={{ display:"grid", gridTemplateColumns:"80px 180px 130px 1fr",
        padding:"14px 16px", alignItems:"start" }}>
        <div style={{ fontSize:"12px", fontFamily:"monospace", fontWeight:600,
          color:"var(--accent2)", paddingTop:"2px" }}>
          {item.req_id}
        </div>
        <div style={{ fontSize:"13px", fontWeight:500, color:"var(--text)",
          paddingRight:"12px", lineHeight:"1.4" }}>
          {item.name}
        </div>
        <div><TypeBadge label={item.req_type} /></div>
        <div style={{ fontSize:"13px", color:"var(--text2)", lineHeight:"1.5",
          overflow: expanded ? "visible" : "hidden",
          display: expanded ? "block" : "-webkit-box",
          WebkitLineClamp: expanded ? undefined : 2,
          WebkitBoxOrient: "vertical" as const }}>
          {item.description}
        </div>
      </div>
      {expanded && (
        <div style={{ padding:"0 16px 14px", display:"flex", gap:"12px",
          flexWrap:"wrap", alignItems:"center" }}>
          <PriorityPill priority={item.priority} />
          {item.section && (
            <span style={{ fontSize:"11px", color:"var(--text3)" }}>
              Section: <span style={{ color:"var(--text2)", fontFamily:"monospace" }}>{item.section}</span>
            </span>
          )}
          {item.page_number > 0 && (
            <span style={{ fontSize:"11px", color:"var(--text3)" }}>
              Page: <span style={{ color:"var(--text2)" }}>{item.page_number}</span>
            </span>
          )}
          <span style={{ fontSize:"11px", color:"var(--text3)" }}>
            Confidence: <span style={{ color:"var(--text2)" }}>{Math.round(item.confidence * 100)}%</span>
          </span>
        </div>
      )}
    </div>
  );
}

// ── RequirementsPanel ─────────────────────────────────────────────────────────
export function RequirementsPanel() {
  const { slug: projectId } = useParams<{ slug: string }>();
  const [activeType, setActiveType] = useState<string | null>(null);
  const [filterText, setFilterText] = useState("");

  const [statusPollInterval, setStatusPollInterval] = useState<number | undefined>(4000);
  const [reqsPollInterval, setReqsPollInterval] = useState<number | undefined>(5000);

  // Check project status to know if extraction is still running
  const { data: statusData } = useGetProjectStatusQuery(projectId!, {
    skip: !projectId,
    pollingInterval: statusPollInterval,
  });

  const hasLlmError = statusData?.documents.some(
    d => d.current_status === "extraction_failed"
  ) ?? false;

  useEffect(() => {
    if (hasLlmError) {
      setStatusPollInterval(undefined);
      setReqsPollInterval(undefined);
    } else {
      setStatusPollInterval(4000);
      setReqsPollInterval(5000);
    }
  }, [hasLlmError]);

  const { data, isLoading, isError, isFetching, refetch } =
    useGetProjectRequirementsQuery(
      { projectId: projectId! },
      { skip: !projectId, pollingInterval: reqsPollInterval }
    );

  const isExtracting = statusData?.documents.some(
    d => d.current_status === "parsed" || d.current_status === "processing"
  );

  // Client-side filter
  const displayed = useMemo(() => {
    if (!data?.requirements) return [];
    let list = data.requirements;
    if (activeType) list = list.filter(r => r.req_type === activeType);
    const q = filterText.trim().toLowerCase();
    if (q) list = list.filter(r =>
      r.name.toLowerCase().includes(q) ||
      r.description.toLowerCase().includes(q) ||
      r.req_id.toLowerCase().includes(q) ||
      r.section.toLowerCase().includes(q)
    );
    return list;
  }, [data, activeType, filterText]);

  const countByType = useMemo(() => {
    if (!data?.requirements) return {} as Record<string, number>;
    const counts: Record<string, number> = { __all__: data.requirements.length };
    for (const r of data.requirements) counts[r.req_type] = (counts[r.req_type] ?? 0) + 1;
    return counts;
  }, [data]);

  return (
    <div>
      {/* Header */}
      <div className="section-hdr" style={{ display:"flex", alignItems:"center",
        justifyContent:"space-between", flexWrap:"wrap", gap:"8px", marginBottom:"16px" }}>
        <h2 style={{ margin:0 }}>Requirements</h2>
        <div style={{ display:"flex", gap:"8px", alignItems:"center" }}>
          {data && (
            <span style={{ fontSize:"12px", color:"var(--text3)" }}>
              {data.total_requirements} total · {data.total_documents} document{data.total_documents !== 1 ? "s" : ""}
            </span>
          )}
          {isExtracting && (
            <span style={{ fontSize:"11px", color:"#fbbf24", background:"rgba(245,158,11,.1)",
              padding:"2px 8px", borderRadius:"999px", border:"1px solid rgba(245,158,11,.3)" }}>
              Extracting…
            </span>
          )}
          <span className="ai-tag">AI Extracted</span>
        </div>
      </div>

      {/* Search + refresh */}
      <div style={{ display:"flex", gap:"8px", marginBottom:"14px" }}>
        <input
          type="text"
          placeholder="Filter requirements…"
          value={filterText}
          onChange={e => setFilterText(e.target.value)}
          style={{ flex:1, padding:"8px 12px", borderRadius:"8px",
            border:"1px solid var(--border2)", background:"var(--surface2)",
            color:"var(--text)", fontSize:"13px", outline:"none" }}
        />
        {filterText && (
          <button onClick={() => setFilterText("")}
            style={{ padding:"8px 12px", borderRadius:"8px", border:"1px solid var(--border2)",
              background:"transparent", color:"var(--text3)", fontSize:"13px", cursor:"pointer" }}>
            Clear
          </button>
        )}
        <button onClick={() => refetch()} disabled={isFetching}
          style={{ padding:"8px 12px", borderRadius:"8px", border:"1px solid var(--border2)",
            background:"transparent", color:"var(--text3)", fontSize:"13px", cursor:"pointer",
            opacity: isFetching ? 0.5 : 1 }}
          title="Refresh">↻</button>
      </div>

      {/* Category tabs */}
      <div style={{ display:"flex", flexWrap:"wrap", gap:"6px", marginBottom:"16px" }}>
        {TABS.map(tab => {
          const count = tab.value === null
            ? (countByType["__all__"] ?? 0)
            : (countByType[tab.value] ?? 0);
          if (tab.value !== null && count === 0 && data) return null;
          const isActive = activeType === tab.value;
          return (
            <button key={tab.label} onClick={() => setActiveType(tab.value)}
              style={{ padding:"4px 12px", borderRadius:"999px", cursor:"pointer",
                border:`1px solid ${isActive ? "var(--accent)" : "var(--border2)"}`,
                background: isActive ? "rgba(124,58,237,.15)" : "transparent",
                color: isActive ? "#a78bfa" : "var(--text3)",
                fontSize:"12px", fontWeight: isActive ? 600 : 400,
                display:"flex", alignItems:"center", gap:"5px" }}>
              {tab.label}
              {count > 0 && (
                <span style={{ fontSize:"10px", padding:"1px 5px", borderRadius:"999px",
                  background: isActive ? "rgba(124,58,237,.3)" : "rgba(255,255,255,.06)",
                  color: isActive ? "#c4b5fd" : "var(--text3)", fontWeight:600, lineHeight:"1.4" }}>
                  {count}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* Loading */}
      {isLoading && (
        <div style={{ color:"var(--text3)", fontSize:"13px", padding:"32px 0", textAlign:"center" }}>
          Loading requirements…
        </div>
      )}

      {/* Extracting state — no results yet */}
      {!isLoading && !isError && data?.total_requirements === 0 && isExtracting && (
        <div style={{ padding:"48px 24px", textAlign:"center",
          border:"1px dashed var(--border2)", borderRadius:"12px" }}>
          <div style={{ fontSize:"24px", marginBottom:"12px" }}>⚙️</div>
          <div style={{ fontSize:"14px", fontWeight:500, color:"var(--text)", marginBottom:"6px" }}>
            AI extraction in progress
          </div>
          <div style={{ fontSize:"13px", color:"var(--text3)" }}>
            Sending document to LLM and extracting requirements…
          </div>
        </div>
      )}

      {/* Error */}
      {isError && !isLoading && (
        <div style={{ padding:"16px", borderRadius:"8px",
          background:"rgba(239,68,68,.08)", border:"1px solid rgba(239,68,68,.2)",
          color:"#f87171", fontSize:"13px" }}>
          Could not load requirements. Check that the document finished processing.
        </div>
      )}

      {/* Empty — done extracting but no results */}
      {!isLoading && !isError && data?.total_requirements === 0 && !isExtracting && (
        <div style={{ padding:"48px 24px", textAlign:"center",
          border:"1px dashed var(--border2)", borderRadius:"12px",
          color:"var(--text3)", fontSize:"13px" }}>
          No requirements extracted yet. Upload a document to get started.
        </div>
      )}

      {/* Filtered empty */}
      {!isLoading && !isError && data && data.total_requirements > 0 && displayed.length === 0 && (
        <div style={{ padding:"32px 24px", textAlign:"center",
          color:"var(--text3)", fontSize:"13px" }}>
          No requirements match your current filter.
        </div>
      )}

      {/* Requirements table */}
      {!isLoading && displayed.length > 0 && (
        <div style={{ border:"1px solid var(--border2)", borderRadius:"12px",
          overflow:"hidden", background:"var(--surface)" }}>
          {/* Header row */}
          <div style={{ display:"grid", gridTemplateColumns:"80px 180px 130px 1fr",
            padding:"10px 16px", background:"var(--surface2)",
            borderBottom:"1px solid var(--border2)" }}>
            {["ID","REQUIREMENT","TYPE","DESCRIPTION"].map(col => (
              <div key={col} style={{ fontSize:"11px", fontWeight:600,
                color:"var(--text3)", letterSpacing:"0.05em", textTransform:"uppercase" }}>
                {col}
              </div>
            ))}
          </div>

          {displayed.map((item, idx) => (
            <RequirementRow key={item.id} item={item} isLast={idx === displayed.length - 1} />
          ))}

          {/* Footer */}
          <div style={{ padding:"8px 16px", borderTop:"1px solid var(--border)",
            background:"var(--surface2)", fontSize:"11px", color:"var(--text3)", textAlign:"right" }}>
            {displayed.length} requirement{displayed.length !== 1 ? "s" : ""}
            {filterText && ` matching "${filterText}"`}
            {activeType && ` · ${activeType}`}
          </div>
        </div>
      )}
    </div>
  );
}
