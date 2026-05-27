import { useParams } from "react-router-dom";
import { useGetProjectStatusQuery } from "@/services/documentsApi";
import type { DocumentStatusResponse, PipelineStage } from "@/types";

// ─── Status config ────────────────────────────────────────────────────────────

const STATUS_LABEL: Record<string, string> = {
  uploaded:   "Queued",
  processing: "Parsing",
  parsed:     "Chunking",
  chunked:    "Classifying",
  classified: "Embedding",
  embedding:  "Embedding",
  embedded:   "Ready",
  failed:     "Failed",
};

const STATUS_COLOR: Record<string, { dot: string; text: string; bg: string; border: string }> = {
  uploaded:   { dot: "#a78bfa", text: "#a78bfa", bg: "rgba(124,58,237,0.08)",  border: "rgba(124,58,237,0.2)"  },
  processing: { dot: "#60a5fa", text: "#60a5fa", bg: "rgba(59,130,246,0.08)",  border: "rgba(59,130,246,0.2)"  },
  parsed:     { dot: "#60a5fa", text: "#60a5fa", bg: "rgba(59,130,246,0.08)",  border: "rgba(59,130,246,0.2)"  },
  chunked:    { dot: "#60a5fa", text: "#60a5fa", bg: "rgba(59,130,246,0.08)",  border: "rgba(59,130,246,0.2)"  },
  classified: { dot: "#f59e0b", text: "#f59e0b", bg: "rgba(245,158,11,0.08)",  border: "rgba(245,158,11,0.2)"  },
  embedding:  { dot: "#f59e0b", text: "#f59e0b", bg: "rgba(245,158,11,0.08)",  border: "rgba(245,158,11,0.2)"  },
  embedded:   { dot: "#22c55e", text: "#4ade80", bg: "rgba(34,197,94,0.08)",   border: "rgba(34,197,94,0.2)"   },
  failed:     { dot: "#ef4444", text: "#f87171", bg: "rgba(239,68,68,0.08)",   border: "rgba(239,68,68,0.2)"   },
};

const STAGE_PROGRESS: Record<string, number> = {
  uploaded: 5, parsed: 30, chunked: 55, classified: 75, embedded: 100,
};

function getProgress(doc: DocumentStatusResponse): number {
  if (doc.is_ready) return 100;
  if (doc.current_status === "failed") return 100;
  const lastCompleted = [...doc.pipeline].reverse().find((s) => s.status === "completed");
  const inProgress    = doc.pipeline.find((s) => s.status === "in_progress");
  const base = lastCompleted ? (STAGE_PROGRESS[lastCompleted.name] ?? 0) : 0;
  const next = inProgress    ? (STAGE_PROGRESS[inProgress.name]    ?? base) : base;
  return Math.round((base + next) / 2);
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
}

// ─── DocumentsPanel ───────────────────────────────────────────────────────────

export function DocumentsPanel() {
  // Project ID comes directly from the URL — same UUID the backend uses
  const { slug: projectId } = useParams<{ slug: string }>();

  const { data, isLoading, error } = useGetProjectStatusQuery(projectId!, {
    skip: !projectId,
  });

  if (isLoading) {
    return (
      <div>
        <div className="section-hdr"><h2>Documents</h2></div>
        <div style={{ color: "var(--text3)", fontSize: "13px", padding: "24px 0" }}>
          Loading documents…
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div>
        <div className="section-hdr"><h2>Documents</h2></div>
        <div style={{
          padding: "10px 14px", borderRadius: "8px",
          background: "rgba(239,68,68,0.08)", border: "1px solid rgba(239,68,68,0.2)",
          color: "#f87171", fontSize: "13px",
        }}>
          Could not load documents for this project.
        </div>
      </div>
    );
  }

  const docs = data?.documents ?? [];

  return (
    <div>
      <div className="section-hdr" style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <h2>Documents</h2>
        {docs.length > 0 && (
          <span style={{ fontSize: "12px", color: "var(--text3)", fontFamily: "monospace" }}>
            {docs.length} file{docs.length !== 1 ? "s" : ""}
          </span>
        )}
      </div>

      {docs.length === 0 ? (
        <div style={{
          padding: "48px 24px", textAlign: "center",
          color: "var(--text3)", fontSize: "13px",
          border: "1px dashed var(--border2)", borderRadius: "12px",
        }}>
          No documents yet. Upload files from the Upload panel.
        </div>
      ) : (
        <div style={{
          border: "1px solid var(--border2)",
          borderRadius: "12px",
          overflow: "hidden",
          background: "var(--surface)",
        }}>
          {docs.map((doc, idx) => (
            <DocRow
              key={String(doc.document_id)}
              doc={doc}
              isLast={idx === docs.length - 1}
            />
          ))}
        </div>
      )}
    </div>
  );
}

// ─── DocRow ───────────────────────────────────────────────────────────────────

function DocRow({ doc, isLast }: { doc: DocumentStatusResponse; isLast: boolean }) {
  const progress  = getProgress(doc);
  const statusCfg = STATUS_COLOR[doc.current_status] ?? STATUS_COLOR.uploaded;
  const label     = STATUS_LABEL[doc.current_status] ?? "Processing";
  const isFailed  = doc.current_status === "failed";
  const isReady   = doc.is_ready;

  return (
    <div style={{ borderBottom: isLast ? "none" : "1px solid var(--border)" }}>
      {/* Main row */}
      <div style={{ display: "flex", alignItems: "center", gap: "12px", padding: "12px 18px" }}>
        {/* File type badge */}
        <div style={{
          width: "36px", height: "36px", borderRadius: "8px", flexShrink: 0,
          background: "var(--surface2)", border: "1px solid var(--border2)",
          display: "flex", alignItems: "center", justifyContent: "center",
          fontSize: "10px", fontFamily: "monospace", fontWeight: 700,
          color: doc.file_type === "pdf" ? "#f87171" : doc.file_type === "docx" ? "#60a5fa" : "#4ade80",
        }}>
          {doc.file_type.toUpperCase()}
        </div>

        {/* Name + meta */}
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{
            fontSize: "13px", fontWeight: 500, color: "var(--text)",
            overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap",
            marginBottom: "3px",
          }}>
            {doc.file_name}
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <span style={{ fontSize: "11px", color: "var(--text3)", fontFamily: "monospace" }}>
              {formatBytes(doc.file_size_bytes)}
            </span>
            <span style={{ fontSize: "11px", color: "var(--text3)" }}>·</span>
            <span style={{ fontSize: "11px", color: "var(--text3)" }}>
              {formatDate(doc.created_at)}
            </span>
          </div>
        </div>

        {/* Inline progress bar — only while processing */}
        {!isReady && !isFailed && (
          <div style={{ width: "80px", flexShrink: 0 }}>
            <div style={{ height: "3px", background: "rgba(255,255,255,0.06)", borderRadius: "2px", overflow: "hidden" }}>
              <div style={{
                height: "100%", width: `${progress}%`,
                background: "linear-gradient(90deg, #7c3aed, #a78bfa)",
                transition: "width 0.6s ease",
              }} />
            </div>
            <div style={{ textAlign: "right", fontSize: "10px", fontFamily: "monospace", color: "var(--text3)", marginTop: "2px" }}>
              {progress}%
            </div>
          </div>
        )}

        {/* Status badge */}
        <div style={{
          flexShrink: 0, display: "flex", alignItems: "center", gap: "5px",
          padding: "3px 10px", borderRadius: "999px",
          background: statusCfg.bg, border: `1px solid ${statusCfg.border}`,
          fontSize: "11px", color: statusCfg.text,
        }}>
          <div style={{
            width: "5px", height: "5px", borderRadius: "50%", background: statusCfg.dot,
            animation: (!isReady && !isFailed) ? "pulse 2s infinite" : "none",
          }} />
          {label}
        </div>
      </div>

      {/* Stage pills — only for in-progress docs */}
      {!isReady && !isFailed && (
        <StagePills pipeline={doc.pipeline} />
      )}
    </div>
  );
}

// ─── StagePills ───────────────────────────────────────────────────────────────

function StagePills({ pipeline }: { pipeline: PipelineStage[] }) {
  return (
    <div style={{ display: "flex", flexWrap: "wrap", gap: "5px", padding: "0 18px 10px 66px" }}>
      {pipeline.map((stage) => {
        const cfg =
          stage.status === "completed"   ? { bg: "rgba(34,197,94,0.08)",   border: "rgba(34,197,94,0.25)",   text: "#4ade80"  } :
          stage.status === "in_progress" ? { bg: "rgba(124,58,237,0.12)",  border: "rgba(124,58,237,0.35)",  text: "#a78bfa"  } :
          stage.status === "failed"      ? { bg: "rgba(239,68,68,0.08)",   border: "rgba(239,68,68,0.25)",   text: "#f87171"  } :
                                           { bg: "rgba(255,255,255,0.03)", border: "rgba(255,255,255,0.08)", text: "rgba(255,255,255,0.3)" };
        return (
          <span key={stage.name} style={{
            fontSize: "10px", padding: "1px 7px", borderRadius: "999px",
            background: cfg.bg, border: `1px solid ${cfg.border}`, color: cfg.text,
            display: "flex", alignItems: "center", gap: "4px",
          }}>
            {stage.status === "in_progress" && (
              <span style={{ width: "4px", height: "4px", borderRadius: "50%", background: "#a78bfa", display: "inline-block" }} />
            )}
            {stage.label}
          </span>
        );
      })}
    </div>
  );
}
