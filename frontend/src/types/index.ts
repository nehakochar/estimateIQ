// ─── Common ──────────────────────────────────────────────────────────────────

export type UUID = string;

export type Nullable<T> = T | null;

export type Optional<T> = T | undefined;

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  has_next: boolean;
  has_prev: boolean;
}

export interface ApiError {
  detail: string;
  status_code?: number;
}

// ─── Document / Upload ───────────────────────────────────────────────────────

export type DocumentStatus =
  | "uploaded"
  | "processing"
  | "parsed"
  | "chunked"
  | "classified"
  | "embedding"
  | "embedded"
  | "extracted"
  | "failed"
  | "extraction_failed";

export type DocumentType = "pdf" | "docx" | "xlsx";

export interface Document {
  id: UUID;
  project_id: UUID;
  filename: string;
  file_type: DocumentType;
  file_size: number;
  status: DocumentStatus;
  storage_path: string;
  created_at: string;
  updated_at: string;
}

// ─── Upload API response shapes ───────────────────────────────────────────────

export interface FileUploadResult {
  file_name: string;
  status: "uploaded" | "failed";
  document_id: UUID | null;
  job_id: UUID | null;
  error_reason: string | null;
}

export interface UploadApiResponse {
  project_id: UUID;
  uploaded_files: FileUploadResult[];
}

// ─── Pipeline status ──────────────────────────────────────────────────────────

export type PipelineStageStatus = "pending" | "in_progress" | "completed" | "failed";

export interface PipelineStage {
  name: string;
  label: string;
  description: string;
  status: PipelineStageStatus;
}

export interface DocumentStatusResponse {
  document_id: UUID;
  project_id: UUID;
  file_name: string;
  file_type: string;
  file_size_bytes: number;
  current_status: DocumentStatus;
  status_message: string;
  extraction_error: string | null;
  is_ready: boolean;
  pipeline: PipelineStage[];
  created_at: string;
}

export interface ProjectStatusResponse {
  project_id: UUID;
  total_documents: number;
  ready_documents: number;
  failed_documents: number;
  is_ready: boolean;
  documents: DocumentStatusResponse[];
}

// ─── Project ─────────────────────────────────────────────────────────────────

export type ProjectStatus = "active" | "processing" | "completed" | "failed";

export interface Project {
  id: UUID;
  name: string;
  description?: string;
  status: ProjectStatus;
  document_count: number;
  created_at: string;
  updated_at: string;
}

// ─── Processing Job ───────────────────────────────────────────────────────────

export type JobStatus = "pending" | "running" | "completed" | "failed";

export interface ProcessingJob {
  id: UUID;
  document_id: UUID;
  job_type: string;
  status: JobStatus;
  progress: number;
  error_message?: string;
  created_at: string;
  updated_at: string;
}

// ─── Retrieval ────────────────────────────────────────────────────────────────

export interface RetrievalResult {
  chunk_id: UUID;
  document_id: UUID;
  content: string;
  score: number;
  metadata: Record<string, unknown>;
}

export interface RetrievalQuery {
  query: string;
  project_id?: UUID;
  top_k?: number;
  score_threshold?: number;
}

// ─── UI State ─────────────────────────────────────────────────────────────────

export type Theme = "dark" | "light" | "system";

export interface NavItem {
  label: string;
  href: string;
  icon?: React.ComponentType<{ className?: string }>;
  badge?: string | number;
  children?: NavItem[];
}

export interface BreadcrumbItem {
  label: string;
  href?: string;
}
