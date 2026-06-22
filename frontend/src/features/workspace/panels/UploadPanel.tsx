import { useState, useCallback, useEffect, useRef } from "react";
import { useParams } from "react-router-dom";
import { useAppDispatch, useAppSelector } from "@/store";
import { uploadDocuments, resetUpload, markToastShown } from "@/store/slices/uploadSlice";
import { useGetProjectStatusQuery } from "@/services/documentsApi";
import { useToast } from "@/components/ui/use-toast";
import type { DocumentStatusResponse } from "@/types";

// ─── UploadPanel ──────────────────────────────────────────────────────────────

export function UploadPanel() {
  const dispatch = useAppDispatch();
  const { slug: workspaceProjectId } = useParams<{ slug: string }>();
  const { isUploading, isSuccess, uploadError, currentProjectId, toastShown } = useAppSelector((s) => s.upload);
  const { toast } = useToast();

  const [localFiles, setLocalFiles] = useState<File[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const dragCounter = useRef(0);

  // Reset upload state when panel mounts fresh
  useEffect(() => {
    dispatch(resetUpload());
  }, [dispatch]);

  // Show success toast when files are uploaded
  useEffect(() => {
    if (isSuccess && currentProjectId && !toastShown) {
      dispatch(markToastShown());
      toast({
        title: "Documents uploaded successfully",
        description: "Your documents are now being processed.",
        variant: "default",
      });
    }
  }, [isSuccess, currentProjectId, toastShown, dispatch, toast]);

  const addFiles = useCallback((incoming: File[]) => {
    const valid = incoming.filter((f) => {
      const ext = f.name.split(".").pop()?.toLowerCase() ?? "";
      return ["pdf", "docx", "xlsx"].includes(ext);
    });
    setLocalFiles((prev) => [...prev, ...valid]);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    dragCounter.current = 0;
    setIsDragging(false);
    addFiles(Array.from(e.dataTransfer.files));
  }, [addFiles]);

  const handleDragEnter = (e: React.DragEvent) => {
    e.preventDefault();
    dragCounter.current += 1;
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    dragCounter.current -= 1;
    if (dragCounter.current <= 0) {
      dragCounter.current = 0;
      setIsDragging(false);
    }
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) addFiles(Array.from(e.target.files));
    e.target.value = "";
  };

  const handleUpload = () => {
    if (!localFiles.length || isUploading || !workspaceProjectId) return;
    dispatch(uploadDocuments({ files: localFiles, projectId: workspaceProjectId }));
  };

  const handleReset = () => {
    setLocalFiles([]);
    dispatch(resetUpload());
  };

  // ── After upload succeeds, show pipeline progress ─────────────────────────
  if (isSuccess && currentProjectId) {
    return <PipelineView projectId={currentProjectId} onReset={handleReset} />;
  }

  // ── Upload form ───────────────────────────────────────────────────────────
  return (
    <div>
      <div className="section-hdr">
        <h2>RFP Source Ingestion Portal</h2>
      </div>

      <label style={{ display: "block" }}>
        <div
          className={`upload-zone${isDragging ? " dragging" : ""}`}
          onDragEnter={handleDragEnter}
          onDragLeave={handleDragLeave}
          onDragOver={(e) => e.preventDefault()}
          onDrop={handleDrop}
          style={{ cursor: "pointer" }}
        >
          <div className="upload-icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#6c63ff" strokeWidth="2">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="17 8 12 3 7 8" />
              <line x1="12" y1="3" x2="12" y2="15" />
            </svg>
          </div>
          <div className="upload-title">
            {isDragging ? "Release to add files" : "Drop project documentation or RFP payload here"}
          </div>
          <div className="upload-sub">
            Supports system engineering spreadsheets, structural specifications, PDFs and markdown exports
          </div>

          {localFiles.length > 0 && (
            <div className="upload-file-list">
              {localFiles.map((f, i) => (
                <div key={i} className="upload-file-item">✓ {f.name}</div>
              ))}
            </div>
          )}

          <input
            id="upload-panel-input"
            type="file"
            multiple
            accept=".pdf,.docx,.xlsx"
            className="sr-only"
            onChange={handleFileInput}
          />
        </div>
      </label>

      {uploadError && (
        <div style={{
          marginTop: "12px",
          padding: "10px 14px",
          borderRadius: "8px",
          background: "rgba(239,68,68,0.1)",
          border: "1px solid rgba(239,68,68,0.3)",
          color: "#f87171",
          fontSize: "13px",
        }}>
          Upload failed: {uploadError}
        </div>
      )}

      {localFiles.length > 0 && (
        <div className="upload-actions">
          <button className="btn btn-primary" onClick={handleUpload} disabled={isUploading}>
            {isUploading ? "Uploading…" : `Upload ${localFiles.length} file${localFiles.length !== 1 ? "s" : ""}`}
          </button>
          <button className="btn btn-ghost" onClick={() => setLocalFiles([])}>Clear</button>
        </div>
      )}
    </div>
  );
}

// ─── PipelineView ─────────────────────────────────────────────────────────────

interface PipelineViewProps {
  projectId: string;
  onReset: () => void;
}

function PipelineView({ projectId, onReset }: PipelineViewProps) {
  const [pollInterval, setPollInterval] = useState<number | undefined>(2000);
  const { data, isLoading, error } = useGetProjectStatusQuery(projectId, {
    pollingInterval: pollInterval,
  });

  const hasLlmError = data?.documents.some(d => d.current_status === "extraction_failed") ?? false;

  useEffect(() => {
    if (hasLlmError) {
      setPollInterval(undefined);
    } else {
      setPollInterval(2000);
    }
  }, [hasLlmError]);

  if (isLoading) {
    return (
      <div>
        <div className="section-hdr">
          <h2>Processing Documents</h2>
        </div>
        <div style={{ padding: "24px 0", color: "var(--muted-foreground)", fontSize: "13px" }}>
          Loading pipeline status…
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div>
        <div className="section-hdr">
          <h2>Processing Documents</h2>
        </div>
        <div style={{
          padding: "10px 14px",
          borderRadius: "8px",
          background: "rgba(239,68,68,0.1)",
          border: "1px solid rgba(239,68,68,0.3)",
          color: "#f87171",
          fontSize: "13px",
          marginBottom: "12px",
        }}>
          Could not load pipeline status. The documents were uploaded successfully.
        </div>
        <button className="btn btn-ghost" onClick={onReset}>Upload more files</button>
      </div>
    );
  }

  const allReady = data?.is_ready ?? false;
  const totalDocs = data?.total_documents ?? 0;
  const readyDocs = data?.ready_documents ?? 0;
  const overallPct = totalDocs > 0 ? Math.round((readyDocs / totalDocs) * 100) : 0;

  return (
    <div>
      <div className="section-hdr" style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <h2>{allReady ? "Documents Ready" : "Processing Documents"}</h2>
        {allReady && (
          <button className="btn btn-ghost" onClick={onReset} style={{ fontSize: "12px" }}>
            Upload more
          </button>
        )}
      </div>

      {/* Overall progress bar */}
      <div style={{ marginBottom: "20px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "6px" }}>
          <span style={{ fontSize: "12px", color: "var(--muted-foreground)" }}>
            {allReady
              ? `All ${totalDocs} document${totalDocs !== 1 ? "s" : ""} ready`
              : `Processing ${totalDocs - readyDocs} of ${totalDocs} document${totalDocs !== 1 ? "s" : ""}…`}
          </span>
          <span style={{ fontSize: "12px", fontFamily: "monospace", color: "var(--muted-foreground)" }}>
            {overallPct}%
          </span>
        </div>
        <div style={{ height: "3px", background: "rgba(255,255,255,0.08)", borderRadius: "2px", overflow: "hidden" }}>
          <div style={{
            height: "100%",
            width: `${overallPct}%`,
            background: allReady ? "#22c55e" : "linear-gradient(90deg, #7c3aed, #a78bfa)",
            borderRadius: "2px",
            transition: "width 0.6s ease",
          }} />
        </div>
      </div>

      {/* Per-document cards */}
      <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
        {data?.documents.map((doc) => (
          <DocCard key={String(doc.document_id)} doc={doc} />
        ))}
      </div>
    </div>
  );
}

// ─── DocCard ──────────────────────────────────────────────────────────────────

const STAGE_PROGRESS: Record<string, number> = {
  uploaded: 5,
  parsed: 30,
  chunked: 55,
  classified: 75,
  embedded: 100,
};

const RUNNING_LABELS: Record<string, string> = {
  uploaded:          "Queuing for processing…",
  processing:        "Parsing document — extracting text…",
  parsed:            "Sending to AI for requirement extraction…",
  chunked:           "Classifying requirements…",
  classified:        "Running NLP pipeline — detecting requirement patterns…",
  embedding:         "Generating AI search vectors…",
  embedded:          "Document ready ✓",
  extracted:         "Requirements extracted ✓",
  failed:            "Processing failed",
  extraction_failed: "AI extraction failed",
};

function getProgress(doc: DocumentStatusResponse): number {
  if (doc.is_ready) return 100;
  if (doc.current_status === "failed") return 100;
  const lastCompleted = [...doc.pipeline].reverse().find((s) => s.status === "completed");
  const inProgress = doc.pipeline.find((s) => s.status === "in_progress");
  const base = lastCompleted ? (STAGE_PROGRESS[lastCompleted.name] ?? 0) : 0;
  const next = inProgress ? (STAGE_PROGRESS[inProgress.name] ?? base) : base;
  return Math.round((base + next) / 2);
}

function DocCard({ doc }: { doc: DocumentStatusResponse }) {
  const progress = getProgress(doc);
  const isFailed = doc.current_status === "failed";
  const isExtractionFailed = doc.current_status === "extraction_failed";
  const isAnyFailed = isFailed || isExtractionFailed;
  const isReady = doc.is_ready;
  const label = RUNNING_LABELS[doc.current_status] ?? "Processing…";

  const borderColor = isAnyFailed
    ? "rgba(239,68,68,0.3)"
    : isReady
    ? "rgba(34,197,94,0.2)"
    : "rgba(255,255,255,0.08)";
  const barColor = isAnyFailed
    ? "#ef4444"
    : isReady
    ? "#22c55e"
    : "linear-gradient(90deg, #7c3aed, #a78bfa, #7c3aed)";

  return (
    <div style={{
      borderRadius: "10px",
      border: `1px solid ${borderColor}`,
      background: "#0f1117",
      overflow: "hidden",
    }}>
      <div style={{ display: "flex", alignItems: "center", gap: "12px", padding: "12px 14px" }}>
        {/* Icon */}
        <div style={{
          width: "32px", height: "32px", borderRadius: "8px",
          background: isAnyFailed ? "rgba(239,68,68,0.1)" : isReady ? "rgba(34,197,94,0.1)" : "rgba(124,58,237,0.1)",
          display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0,
        }}>
          {isAnyFailed ? "✗" : isReady ? "✓" : "✦"}
        </div>

        {/* Label + filename */}
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontSize: "13px", fontWeight: 500, color: "rgba(255,255,255,0.9)", marginBottom: "2px" }}>
            {label}
          </div>
          <div style={{ fontSize: "11px", color: "rgba(255,255,255,0.4)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
            {doc.file_name}
          </div>
        </div>

        {/* Percentage */}
        <div style={{
          fontSize: "11px", fontFamily: "monospace", flexShrink: 0,
          color: isAnyFailed ? "#f87171" : isReady ? "#4ade80" : "rgba(255,255,255,0.4)",
        }}>
          {isAnyFailed ? "Failed" : `${progress}%`}
        </div>
      </div>

      {/* Progress bar */}
      <div style={{ height: "3px", background: "rgba(255,255,255,0.05)" }}>
        <div style={{
          height: "100%",
          width: `${progress}%`,
          background: barColor,
          transition: "width 0.6s ease",
        }} />
      </div>

      {/* Extraction error detail box */}
      {isExtractionFailed && doc.extraction_error && (
        <div style={{
          margin: "10px 14px 12px",
          padding: "10px 12px",
          borderRadius: "8px",
          background: "rgba(239,68,68,0.08)",
          border: "1px solid rgba(239,68,68,0.25)",
        }}>
          <div style={{ fontSize: "11px", fontWeight: 600, color: "#f87171", marginBottom: "4px", textTransform: "uppercase", letterSpacing: "0.05em" }}>
            AI Extraction Error
          </div>
          <div style={{ fontSize: "12px", color: "rgba(255,255,255,0.65)", lineHeight: "1.6" }}>
            {doc.extraction_error}
          </div>
          <div style={{ marginTop: "8px", fontSize: "11px", color: "rgba(255,255,255,0.35)" }}>
            Fix: update <code style={{ color: "#f87171", background: "rgba(239,68,68,0.1)", padding: "1px 5px", borderRadius: "3px" }}>EXTRACTION_PROVIDER</code> or <code style={{ color: "#f87171", background: "rgba(239,68,68,0.1)", padding: "1px 5px", borderRadius: "3px" }}>GEMINI_API_KEY</code> in <code style={{ color: "rgba(255,255,255,0.5)", background: "rgba(255,255,255,0.05)", padding: "1px 5px", borderRadius: "3px" }}>.env</code>, then restart the worker and re-upload.
          </div>
        </div>
      )}

      {/* Generic failed box */}
      {isFailed && (
        <div style={{
          margin: "10px 14px 12px",
          padding: "10px 12px",
          borderRadius: "8px",
          background: "rgba(239,68,68,0.08)",
          border: "1px solid rgba(239,68,68,0.25)",
          fontSize: "12px",
          color: "rgba(255,255,255,0.55)",
          lineHeight: "1.6",
        }}>
          {doc.status_message}
        </div>
      )}

      {/* Stage pills — only while in progress */}
      {!isReady && !isAnyFailed && (
        <div style={{ display: "flex", flexWrap: "wrap", gap: "6px", padding: "8px 14px" }}>
          {doc.pipeline.map((stage) => {
            const pillColor =
              stage.status === "completed"   ? { bg: "rgba(34,197,94,0.1)",    border: "rgba(34,197,94,0.3)",    text: "#4ade80" } :
              stage.status === "in_progress" ? { bg: "rgba(124,58,237,0.15)",  border: "rgba(124,58,237,0.4)",   text: "#a78bfa" } :
                                               { bg: "rgba(255,255,255,0.03)", border: "rgba(255,255,255,0.08)", text: "rgba(255,255,255,0.3)" };
            return (
              <span key={stage.name} style={{
                fontSize: "11px", padding: "2px 8px", borderRadius: "999px",
                background: pillColor.bg, border: `1px solid ${pillColor.border}`, color: pillColor.text,
              }}>
                {stage.label}
              </span>
            );
          })}
        </div>
      )}
    </div>
  );
}
