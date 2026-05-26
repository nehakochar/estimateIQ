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
  | "embedded"
  | "failed";

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
