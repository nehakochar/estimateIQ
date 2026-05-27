import { createApi } from "@reduxjs/toolkit/query/react";
import { axiosBaseQuery } from "./baseQuery";
import type {
  Document,
  DocumentStatusResponse,
  PaginatedResponse,
  ProjectStatusResponse,
  UUID,
} from "@/types";

export interface ListDocumentsParams {
  project_id?: UUID;
  page?: number;
  page_size?: number;
}

export const documentsApi = createApi({
  reducerPath: "documentsApi",
  // baseUrl defaults to VITE_API_BASE_URL — all URLs below are backend paths
  baseQuery: axiosBaseQuery(),
  tagTypes: ["Document", "DocumentStatus", "ProjectStatus"],
  endpoints: (builder) => ({
    // ── List ──────────────────────────────────────────────────────────────
    listDocuments: builder.query<PaginatedResponse<Document>, ListDocumentsParams | void>({
      query: (params) => ({ url: "/documents", params: params ?? {} }),
      providesTags: (result) =>
        result
          ? [
              ...result.items.map(({ id }) => ({ type: "Document" as const, id })),
              { type: "Document", id: "LIST" },
            ]
          : [{ type: "Document", id: "LIST" }],
    }),

    // ── Get one ───────────────────────────────────────────────────────────
    getDocument: builder.query<Document, UUID>({
      query: (id) => ({ url: `/documents/${id}` }),
      providesTags: (_result, _err, id) => [{ type: "Document", id }],
    }),

    // ── Document pipeline status (for polling) ────────────────────────────
    getDocumentStatus: builder.query<DocumentStatusResponse, UUID>({
      query: (id) => ({ url: `/documents/${id}/status` }),
      providesTags: (_result, _err, id) => [{ type: "DocumentStatus", id }],
    }),

    // ── Project pipeline status (for polling all docs in a project) ───────
    getProjectStatus: builder.query<ProjectStatusResponse, UUID>({
      query: (projectId) => ({ url: `/projects/${projectId}/status` }),
      providesTags: (_result, _err, id) => [{ type: "ProjectStatus", id }],
    }),

    // ── Delete ────────────────────────────────────────────────────────────
    deleteDocument: builder.mutation<void, UUID>({
      query: (id) => ({ url: `/documents/${id}`, method: "DELETE" }),
      invalidatesTags: (_result, _err, id) => [
        { type: "Document", id },
        { type: "Document", id: "LIST" },
      ],
    }),
  }),
});

export const {
  useListDocumentsQuery,
  useGetDocumentQuery,
  useGetDocumentStatusQuery,
  useGetProjectStatusQuery,
  useDeleteDocumentMutation,
} = documentsApi;
