import { createApi } from "@reduxjs/toolkit/query/react";
import { axiosBaseQuery } from "./baseQuery";
import type { Document, PaginatedResponse, UUID } from "@/types";

export interface ListDocumentsParams {
  project_id?: UUID;
  page?: number;
  page_size?: number;
}

export const documentsApi = createApi({
  reducerPath: "documentsApi",
  baseQuery: axiosBaseQuery({ baseUrl: "" }),
  tagTypes: ["Document"],
  endpoints: (builder) => ({
    // ── List ──────────────────────────────────────────────────────────────
    listDocuments: builder.query<PaginatedResponse<Document>, ListDocumentsParams | void>({
      query: (params) => ({ url: "/api/documents", params: params ?? {} }),
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
      query: (id) => ({ url: `/api/documents/${id}` }),
      providesTags: (_result, _err, id) => [{ type: "Document", id }],
    }),

    // ── Delete ────────────────────────────────────────────────────────────
    deleteDocument: builder.mutation<void, UUID>({
      query: (id) => ({ url: `/api/documents/${id}`, method: "DELETE" }),
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
  useDeleteDocumentMutation,
} = documentsApi;
