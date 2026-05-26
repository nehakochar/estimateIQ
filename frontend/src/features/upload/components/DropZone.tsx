import { useCallback, useState } from "react";
import { Upload, FileText, FileSpreadsheet, File, X, AlertCircle } from "lucide-react";
import { cn, formatFileSize } from "@/utils";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { useAppDispatch, useAppSelector } from "@/store";
import { addFiles, removeFile } from "@/store/slices/uploadSlice";

// ─── Constants ────────────────────────────────────────────────────────────────

const ACCEPTED_TYPES = {
  "application/pdf": [".pdf"],
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
  "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx"],
};

const MAX_FILE_SIZE_MB = 50;
const MAX_FILES = 10;

// ─── Component ────────────────────────────────────────────────────────────────

export function DropZone() {
  const dispatch = useAppDispatch();
  const files = useAppSelector((s) => s.upload.files);
  const [isDragging, setIsDragging] = useState(false);
  const [errors, setErrors] = useState<string[]>([]);

  const validateAndAddFiles = useCallback(
    (incoming: FileList | File[]) => {
      const fileArray = Array.from(incoming);
      const newErrors: string[] = [];
      const valid: File[] = [];

      if (files.length + fileArray.length > MAX_FILES) {
        newErrors.push(`Maximum ${MAX_FILES} files allowed.`);
        setErrors(newErrors);
        return;
      }

      for (const file of fileArray) {
        const ext = file.name.split(".").pop()?.toLowerCase();
        if (!["pdf", "docx", "xlsx"].includes(ext ?? "")) {
          newErrors.push(`"${file.name}" — unsupported format. Use PDF, DOCX, or XLSX.`);
          continue;
        }
        if (file.size > MAX_FILE_SIZE_MB * 1024 * 1024) {
          newErrors.push(`"${file.name}" exceeds ${MAX_FILE_SIZE_MB} MB limit.`);
          continue;
        }
        valid.push(file);
      }

      setErrors(newErrors);

      if (valid.length > 0) {
        dispatch(
          addFiles(
            valid.map((f) => ({
              id: `${f.name}-${f.size}-${Date.now()}`,
              file: f,
              name: f.name,
              size: f.size,
              type: f.name.split(".").pop()?.toLowerCase() ?? "unknown",
            }))
          )
        );
      }
    },
    [dispatch, files.length]
  );

  const onDrop = useCallback(
    (e: React.DragEvent<HTMLDivElement>) => {
      e.preventDefault();
      setIsDragging(false);
      validateAndAddFiles(e.dataTransfer.files);
    },
    [validateAndAddFiles]
  );

  const onInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) validateAndAddFiles(e.target.files);
    e.target.value = "";
  };

  return (
    <div className="space-y-4">
      {/* Drop area */}
      <div
        onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={onDrop}
        className={cn(
          "relative flex flex-col items-center justify-center gap-4 rounded-xl border-2 border-dashed p-10 text-center transition-all duration-200",
          isDragging
            ? "border-primary bg-primary/5 scale-[1.01]"
            : "border-border hover:border-primary/50 hover:bg-accent/20"
        )}
      >
        <div className="flex h-14 w-14 items-center justify-center rounded-full bg-primary/10">
          <Upload className={cn("h-6 w-6 transition-colors", isDragging ? "text-primary" : "text-muted-foreground")} />
        </div>

        <div className="space-y-1">
          <p className="text-sm font-medium text-foreground">
            {isDragging ? "Drop files here" : "Drag & drop RFP documents"}
          </p>
          <p className="text-xs text-muted-foreground">
            PDF, DOCX, XLSX · Up to {MAX_FILE_SIZE_MB} MB per file · Max {MAX_FILES} files
          </p>
        </div>

        <label className="cursor-pointer">
          <Button size="sm" variant="outline" asChild>
            <span>
              Browse Files
              <input
                type="file"
                multiple
                accept=".pdf,.docx,.xlsx"
                className="sr-only"
                onChange={onInputChange}
              />
            </span>
          </Button>
        </label>
      </div>

      {/* Validation errors */}
      {errors.length > 0 && (
        <div className="rounded-lg border border-destructive/30 bg-destructive/10 p-3 space-y-1">
          {errors.map((err, i) => (
            <div key={i} className="flex items-start gap-2 text-xs text-destructive">
              <AlertCircle className="h-3.5 w-3.5 mt-0.5 shrink-0" />
              {err}
            </div>
          ))}
        </div>
      )}

      {/* File list */}
      {files.length > 0 && (
        <div className="space-y-2">
          <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
            {files.length} file{files.length !== 1 ? "s" : ""} selected
          </p>
          <div className="space-y-2">
            {files.map((f) => (
              <FileRow
                key={f.id}
                id={f.id}
                name={f.name}
                size={f.size}
                type={f.type}
                progress={f.progress}
                status={f.status}
                error={f.error}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ─── FileRow ──────────────────────────────────────────────────────────────────

interface FileRowProps {
  id: string;
  name: string;
  size: number;
  type: string;
  progress: number;
  status: "pending" | "uploading" | "success" | "error";
  error?: string;
}

const typeIcons: Record<string, React.ComponentType<{ className?: string }>> = {
  pdf: FileText,
  docx: File,
  xlsx: FileSpreadsheet,
};

const typeColors: Record<string, string> = {
  pdf: "text-red-400",
  docx: "text-blue-400",
  xlsx: "text-green-400",
};

function FileRow({ id, name, size, type, progress, status, error }: FileRowProps) {
  const dispatch = useAppDispatch();
  const Icon = typeIcons[type] ?? FileText;
  const iconColor = typeColors[type] ?? "text-muted-foreground";

  return (
    <div
      className={cn(
        "flex items-center gap-3 rounded-lg border p-3 transition-colors",
        status === "error" ? "border-destructive/30 bg-destructive/5" : "border-border bg-card"
      )}
    >
      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-muted">
        <Icon className={cn("h-4 w-4", iconColor)} />
      </div>

      <div className="flex-1 min-w-0 space-y-1">
        <div className="flex items-center justify-between gap-2">
          <p className="text-xs font-medium text-foreground truncate">{name}</p>
          <span className="text-[11px] text-muted-foreground shrink-0">
            {formatFileSize(size)}
          </span>
        </div>

        {status === "uploading" && (
          <Progress value={progress} className="h-1" />
        )}

        {status === "error" && error && (
          <p className="text-[11px] text-destructive">{error}</p>
        )}

        {status === "success" && (
          <p className="text-[11px] text-green-400">Uploaded successfully</p>
        )}
      </div>

      {status === "pending" && (
        <Button
          variant="ghost"
          size="icon"
          className="h-6 w-6 shrink-0 text-muted-foreground hover:text-destructive"
          onClick={() => dispatch(removeFile(id))}
          aria-label={`Remove ${name}`}
        >
          <X className="h-3.5 w-3.5" />
        </Button>
      )}
    </div>
  );
}
