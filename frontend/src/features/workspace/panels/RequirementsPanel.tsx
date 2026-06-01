import { useState, useMemo } from "react";
import { useParams } from "react-router-dom";
import {
  useGetProjectRequirementsQuery,
  useReextractDocumentMutation,
  type ExtractedRequirementItem,
} from "@/services/extractionApi";

// ── Category tabs — map req_type values from backend to display labels ────────
//
// req_type values from ExtractionService match these keys exactly.
// "All" is a frontend-only tab that shows the unfiltered result set.

const REQ_TYPE_TABS: { value: string | null; label: string }[] = [
  { value: null,              label: "All" },
  { value: "Functional",      label: "Functional" },
  { value: "Non-Functional",  label: "Non-Functional" },
  { value: "Technical",       label: "Technical" },
  { value: "Security",        label: "Security" },
  { value: "Integration",     label: "Integration" },
  { value: "Compliance",      label: "Compliance" },
  { value: "Infrastructure",  label: "Infrastructure" },
  { value: "Support",         label: "Support" },
];

// ── Badge colour map ──────────────────────────────────────────────────────────

const TYPE_COLORS: Record<string, { bg: string; text: string; border: string }> = {
  Functional:      { bg: "rgba(99,102,241,0.12)",  text: "#818cf8", border: "rgba(99,102,241,0.3)"  },
  "Non-Functional":{ bg: "rgba(245,158,11,0.12)",  text: "#fbbf24", border: "rgba(245,158,11,0.3)"  },
  Technical:       { bg: "rgba(59,130,246,0.12)",  text: "#60a5fa", border: "rgba(59,130,246,0.3)"  },
  Security:        { bg: "rgba(239,68,68,0.12)",   text: "#f87171", border: "rgba(239,68,68,0.3)"   },
  Integration:     { bg: "rgba(16,185,129,0.12)",  text: "#34d399", border: "rgba(16,185,129,0.3)"  },
  Compliance:      { bg: "rgba(236,72,153,0.12)",  text: "#f472b6", border: "rgba(236,72,153,0.3)"  },
  Infrastructure:  { bg: "rgba(107,114,128,0.12)", text: "#9ca3af", border: "rgba(107,114,128,0.3)" },
  Support:         { bg: "rgba(20,184,166,0.12)",  text: "#2dd4bf", border: "rgba(20,184,166,0.3)"  },
  Other:           { bg: "rgba(75,85,99,0.12)",    text: "#6b7280", border: "rgba(75,85,99,0.3)"    },
};

const PRIORITY_COLORS: Record<string, { text: string; bg: string }> = {
  "Must Have":     { text: "#f87171", bg: "rgba(239,68,68,0.10)"   },
  "Should Have":   { text: "#fbbf24", bg: "rgba(245,158,11,0.10)"  },
  "Nice to Have":  { text: "#34d399", bg: "rgba(16,185,129,0.10)"  },
  "Not Specified": { text: "#6b7280", bg: "rgba(75,85,99,0.10)"    },
};

// ── Sub-components ────────────────────────────────────────────────────────────

function TypeBadge({ label }: { label: string }) {
  const c = TYPE_COLORS[label] ?? TYPE_COLORS["Other"];
  return (
    <span style={{
      display: "inline-block",
      padding: "2px 10px",
      borderRadius: "999px",
      fontSize: "11px",
      fontWeight: 500,
      background: c.bg,
      color: c.text,
      border: `1px solid ${c.border}`,
      whiteSpace: "nowrap",
    }}>
      {label}
    </span>
  );
}

function PriorityDot({ priority }: { priority: string }) {
  const c = PRIORITY_COLORS[priority] ?? PRIORITY_COLORS["Not Specified"];
  return (
    <span style={{
      display: "inline-block",
      padding: "2px 8px",
      borderRadius: "999px",
      fontSize: "10px",
      fontWeight: 500,
      background: c.bg,
      color: c.text,
      whiteSpace: "nowrap",
    }}>
      {priority}
    </span>
  );
}

function MetaTag({ label, value }: { label: string; value: string }) {
  return (
    <span style={{ fontSize: "11px", color: "var(--text3)" }}>
      <span style={{ marginRight: "4px" }}>{label}:</span>
      <span style={{ color: "var(--text2)", fontFamily: "monospace" }}>{value}</span>
    </span>
  );
}

// ── RequirementRow ────────────────────────────────────────────────────────────

function RequirementRow({
  item,
  isLast,
}: {
  item: ExtractedRequirementItem;
  isLast: boolean;
}) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div
      style={{
        borderBottom: isLast ? "none" : "1px solid var(--border)",
        cursor: "pointer",
        transition: "background 0.1s",
      }}
      onClick={() => setExpanded((v) => !v)}
      onMouseEnter={(e) => (e.currentTarget.style.background = "rgba(255,255,255,0.02)")}
      onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
    >
      {/* Main row — 4-column grid matching the header */}
      <div style={{
        display: "grid",
        gridTemplateColumns: "80px 180px 130px 1fr",
        gap: 0,
        padding: "14px 16px",
        alignItems: "start",
      }}>
        {/* ID */}
        <div style={{
          fontSize: "12px",
          fontFamily: "monospace",
          fontWeight: 600,
          color: "var(--accent2)",
          paddingTop: "2px",
        }}>
          {item.req_id}
        </div>

        {/* Name */}
        <div style={{
          fontSize: "13px",
          fontWeight: 500,
          color: "var(--text)",
          paddingRight: "12px",
          lineHeight: "1.4",
        }}>
          {item.name}
        </div>

        {/* Type badge */}
        <div>
          <TypeBadge label={item.req_type} />
        </div>

        {/* Description — clipped to 2 lines unless expanded */}
        <div style={{
          fontSize: "13px",
          color: "var(--text2)",
          lineHeight: "1.5",
          overflow: expanded ? "visible" : "hidden",
          display: expanded ? "block" : "-webkit-box",
          WebkitLineClamp: expanded ? undefined : 2,
          WebkitBoxOrient: "vertical" as const,
        }}>
          {item.description}
        </div>
      </div>

      {/* Expanded metadata row */}
      {expanded && (
        <div style={{
          padding: "0 16px 14px 16px",
          display: "flex",
          gap: "16px",
          flexWrap: "wrap",
          alignItems: "center",
        }}>
          <PriorityDot priority={item.priority} />
          <MetaTag label="Section" value={item.section || "—"} />
          <MetaTag label="Page" value={String(item.page_number || "—")} />
          <MetaTag
            label="Confidence"
            value={`${Math.round(item.confidence * 100)}%`}
          />
        </div>
      )}
    </div>
  );
}

// ── Summary bar ───────────────────────────────────────────────────────────────

function SummaryBar({ requirements }: { requirements: ExtractedRequirementItem[] }) {
  const counts = useMemo(() => {
    const byPriority: Record<string, number> = {};
    for (const r of requirements) {
      byPriority[r.priority] = (byPriority[r.priority] ?? 0) + 1;
    }
    return byPriority;
  }, [requirements]);

  const pills = Object.entries(counts).sort((a, b) => b[1] - a[1]);

  if (!pills.length) return null;

  return (
    <div style={{
      display: "flex",
      gap: "8px",
      flexWrap: "wrap",
      marginBottom: "14px",
    }}>
      {pills.map(([priority, count]) => {
        const c = PRIORITY_COLORS[priority] ?? PRIORITY_COLORS["Not Specified"];
        return (
          <span key={priority} style={{
            fontSize: "11px",
            padding: "3px 10px",
            borderRadius: "999px",
            background: c.bg,
            color: c.text,
            fontWeight: 500,
          }}>
            {priority} · {count}
          </span>
        );
      })}
    </div>
  );
}

// ── RequirementsPanel ─────────────────────────────────────────────────────────

export function RequirementsPanel() {
  const { slug: projectId } = useParams<{ slug: string }>();

  // Active tab — null means "All"
  const [activeType, setActiveType] = useState<string | null>(null);

  // Client-side text filter (applied on top of the active tab)
  const [filterText, setFilterText] = useState("");

  // Fetch ALL requirements for the project; filter by req_type in RTK Query
  // We fetch all and filter client-side so tab switching is instant (no refetch)
  const {
    data,
    isLoading,
    isError,
    isFetching,
    refetch,
  } = useGetProjectRequirementsQuery(
    { projectId: projectId! },
    { skip: !projectId }
  );

  const [reextract, { isLoading: isReextracting }] = useReextractDocumentMutation();

  // Derive the displayed list — filter by activeType then by free-text
  const displayed = useMemo(() => {
    if (!data?.requirements) return [];
    let list = data.requirements;

    if (activeType) {
      list = list.filter((r) => r.req_type === activeType);
    }

    const q = filterText.trim().toLowerCase();
    if (q) {
      list = list.filter(
        (r) =>
          r.name.toLowerCase().includes(q) ||
          r.description.toLowerCase().includes(q) ||
          r.req_id.toLowerCase().includes(q) ||
          r.section.toLowerCase().includes(q)
      );
    }

    return list;
  }, [data, activeType, filterText]);

  // Per-tab counts for the badge on each tab button
  const countByType = useMemo(() => {
    if (!data?.requirements) return {} as Record<string, number>;
    const counts: Record<string, number> = { __all__: data.requirements.length };
    for (const r of data.requirements) {
      counts[r.req_type] = (counts[r.req_type] ?? 0) + 1;
    }
    return counts;
  }, [data]);

  const tabCount = (value: string | null) =>
    value === null ? (countByType["__all__"] ?? 0) : (countByType[value] ?? 0);

  return (
    <div>
      {/* Header */}
      <div
        className="section-hdr"
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          flexWrap: "wrap",
          gap: "8px",
          marginBottom: "16px",
        }}
      >
        <h2 style={{ margin: 0 }}>Requirements</h2>
        <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
          {data && (
            <span style={{
              fontSize: "12px",
              color: "var(--text3)",
            }}>
              {data.total_requirements} total · {data.total_documents} document{data.total_documents !== 1 ? "s" : ""}
            </span>
          )}
          <span className="ai-tag">AI Extracted</span>
        </div>
      </div>

      {/* Search / filter bar */}
      <div style={{ display: "flex", gap: "8px", marginBottom: "14px" }}>
        <input
          type="text"
          placeholder="Filter requirements…"
          value={filterText}
          onChange={(e) => setFilterText(e.target.value)}
          style={{
            flex: 1,
            padding: "8px 12px",
            borderRadius: "8px",
            border: "1px solid var(--border2)",
            background: "var(--surface2)",
            color: "var(--text)",
            fontSize: "13px",
            outline: "none",
          }}
        />
        {filterText && (
          <button
            onClick={() => setFilterText("")}
            style={{
              padding: "8px 12px",
              borderRadius: "8px",
              border: "1px solid var(--border2)",
              background: "transparent",
              color: "var(--text3)",
              fontSize: "13px",
              cursor: "pointer",
            }}
          >
            Clear
          </button>
        )}
        <button
          onClick={() => refetch()}
          disabled={isFetching}
          style={{
            padding: "8px 12px",
            borderRadius: "8px",
            border: "1px solid var(--border2)",
            background: "transparent",
            color: "var(--text3)",
            fontSize: "13px",
            cursor: "pointer",
            opacity: isFetching ? 0.5 : 1,
          }}
          title="Refresh"
        >
          ↻
        </button>
      </div>

      {/* Category tabs */}
      <div style={{
        display: "flex",
        flexWrap: "wrap",
        gap: "6px",
        marginBottom: "16px",
      }}>
        {REQ_TYPE_TABS.map((tab) => {
          const isActive = activeType === tab.value;
          const count = tabCount(tab.value);
          // Hide tabs with zero requirements (except "All")
          if (tab.value !== null && count === 0 && data) return null;
          return (
            <button
              key={tab.label}
              onClick={() => setActiveType(tab.value)}
              style={{
                padding: "4px 12px",
                borderRadius: "999px",
                border: `1px solid ${isActive ? "var(--accent)" : "var(--border2)"}`,
                background: isActive ? "rgba(124,58,237,0.15)" : "transparent",
                color: isActive ? "#a78bfa" : "var(--text3)",
                fontSize: "12px",
                cursor: "pointer",
                fontWeight: isActive ? 600 : 400,
                transition: "all 0.15s",
                display: "flex",
                alignItems: "center",
                gap: "5px",
              }}
            >
              {tab.label}
              {count > 0 && (
                <span style={{
                  fontSize: "10px",
                  padding: "1px 5px",
                  borderRadius: "999px",
                  background: isActive ? "rgba(124,58,237,0.3)" : "rgba(255,255,255,0.06)",
                  color: isActive ? "#c4b5fd" : "var(--text3)",
                  fontWeight: 600,
                  lineHeight: "1.4",
                }}>
                  {count}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* Priority summary bar */}
      {displayed.length > 0 && <SummaryBar requirements={displayed} />}

      {/* Loading */}
      {(isLoading || isFetching) && (
        <div style={{
          color: "var(--text3)",
          fontSize: "13px",
          padding: "32px 0",
          textAlign: "center",
        }}>
          {isLoading ? "Extracting requirements…" : "Refreshing…"}
        </div>
      )}

      {/* Error */}
      {isError && !isLoading && (
        <div style={{
          padding: "16px",
          borderRadius: "8px",
          background: "rgba(239,68,68,0.08)",
          border: "1px solid rgba(239,68,68,0.2)",
          color: "#f87171",
          fontSize: "13px",
          marginBottom: "12px",
        }}>
          <div style={{ fontWeight: 600, marginBottom: "4px" }}>
            Could not load requirements
          </div>
          <div style={{ color: "#fca5a5", fontSize: "12px" }}>
            Make sure the document has finished processing and extraction completed.
            The document status must be "extracted".
          </div>
        </div>
      )}

      {/* Empty state */}
      {!isLoading && !isError && displayed.length === 0 && (
        <div style={{
          padding: "48px 24px",
          textAlign: "center",
          color: "var(--text3)",
          fontSize: "13px",
          border: "1px dashed var(--border2)",
          borderRadius: "12px",
        }}>
          {!data || data.total_requirements === 0
            ? "No requirements extracted yet. Upload a document and wait for processing to complete."
            : filterText
            ? `No requirements match "${filterText}" in this category.`
            : `No ${activeType ?? ""} requirements found.`}
        </div>
      )}

      {/* Requirements table */}
      {!isLoading && displayed.length > 0 && (
        <div style={{
          border: "1px solid var(--border2)",
          borderRadius: "12px",
          overflow: "hidden",
          background: "var(--surface)",
        }}>
          {/* Table header */}
          <div style={{
            display: "grid",
            gridTemplateColumns: "80px 180px 130px 1fr",
            padding: "10px 16px",
            background: "var(--surface2)",
            borderBottom: "1px solid var(--border2)",
          }}>
            {["ID", "REQUIREMENT", "TYPE", "DESCRIPTION"].map((col) => (
              <div key={col} style={{
                fontSize: "11px",
                fontWeight: 600,
                color: "var(--text3)",
                letterSpacing: "0.05em",
                textTransform: "uppercase",
              }}>
                {col}
              </div>
            ))}
          </div>

          {/* Rows */}
          {displayed.map((item, idx) => (
            <RequirementRow
              key={item.id}
              item={item}
              isLast={idx === displayed.length - 1}
            />
          ))}

          {/* Footer count */}
          <div style={{
            padding: "8px 16px",
            borderTop: "1px solid var(--border)",
            background: "var(--surface2)",
            fontSize: "11px",
            color: "var(--text3)",
            textAlign: "right",
          }}>
            {displayed.length} requirement{displayed.length !== 1 ? "s" : ""}
            {filterText && ` matching "${filterText}"`}
            {activeType && ` · ${activeType}`}
          </div>
        </div>
      )}
    </div>
  );
}
