import { createApi } from "@reduxjs/toolkit/query/react";
import { axiosBaseQuery } from "./baseQuery";

// ── Response types — mirror app/schemas/extraction.py exactly ────────────────

export interface ExtractedRequirementItem {
  id: string;
  req_id: string;          // e.g. "FR-01"
  name: string;            // short label, e.g. "JWT Token Management"
  req_type: string;        // "Functional" | "Non-Functional" | "Technical" | etc.
  description: string;     // full 2-4 sentence description
  priority: string;        // "Must Have" | "Should Have" | "Nice to Have" | "Not Specified"
  section: string;         // source section heading in document
  page_number: number;
  confidence: number;      // 0.0 – 1.0
}

export interface DocumentRequirementsResponse {
  document_id: string;
  project_id: string;
  total_requirements: number;
  requirements: ExtractedRequirementItem[];
}

export interface ProjectRequirementsResponse {
  project_id: string;
  total_requirements: number;
  total_documents: number;
  requirements: ExtractedRequirementItem[];
}

export interface RequirementsSummaryResponse {
  document_id: string;
  total_requirements: number;
  by_type: Record<string, number>;
  by_priority: Record<string, number>;
}

// ── RTK Query API slice ────────────────────────────────────────────────────────

export const extractionApi = createApi({
  reducerPath: "extractionApi",
  baseQuery: axiosBaseQuery(),
  tagTypes: ["Requirements"],
  endpoints: (builder) => ({

    // GET /projects/{project_id}/requirements?req_type=Functional
    getProjectRequirements: builder.query<
      ProjectRequirementsResponse,
      { projectId: string; reqType?: string }
    >({
      query: ({ projectId, reqType }) => ({
        url: `/projects/${projectId}/requirements`,
        params: reqType ? { req_type: reqType } : {},
      }),
      providesTags: (_result, _err, { projectId, reqType }) => [
        { type: "Requirements", id: `${projectId}-${reqType ?? "all"}` },
      ],
    }),

    // GET /documents/{document_id}/requirements?req_type=Functional
    getDocumentRequirements: builder.query<
      DocumentRequirementsResponse,
      { documentId: string; reqType?: string }
    >({
      query: ({ documentId, reqType }) => ({
        url: `/documents/${documentId}/requirements`,
        params: reqType ? { req_type: reqType } : {},
      }),
      providesTags: (_result, _err, { documentId }) => [
        { type: "Requirements", id: documentId },
      ],
    }),

    // GET /documents/{document_id}/requirements/summary
    getRequirementsSummary: builder.query<
      RequirementsSummaryResponse,
      string // documentId
    >({
      query: (documentId) => ({
        url: `/documents/${documentId}/requirements/summary`,
      }),
    }),

    // POST /documents/{document_id}/requirements/reextract
    reextractDocument: builder.mutation<
      { document_id: string; status: string; message: string },
      string // documentId
    >({
      query: (documentId) => ({
        url: `/documents/${documentId}/requirements/reextract`,
        method: "POST",
      }),
      invalidatesTags: (_result, _err, documentId) => [
        { type: "Requirements", id: documentId },
      ],
    }),

  }),
});

export const {
  useGetProjectRequirementsQuery,
  useGetDocumentRequirementsQuery,
  useGetRequirementsSummaryQuery,
  useReextractDocumentMutation,
} = extractionApi;
