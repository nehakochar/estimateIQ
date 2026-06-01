import { createApi } from "@reduxjs/toolkit/query/react";
import { axiosBaseQuery } from "./baseQuery";
import type { RetrievalQuery, RetrievalResult } from "@/types";

export interface RetrievalResultItem {
  chunk_id: string;
  text: string;
  title: string;
  description: string;
  req_id: string;
  type_label: string;
  category: string;
  section: string;
  subsection: string;
  page_number: number;
  score: number;
  confidence_score: number;
  document_id: string;
  chunk_type: string;
}

export interface CategorySearchResponse {
  project_id: string;
  category: string;
  total_results: number;
  results: RetrievalResultItem[];
}

export interface SemanticSearchResponse {
  project_id: string;
  query: string;
  total_results: number;
  results: RetrievalResultItem[];
}

export const retrievalApi = createApi({
  reducerPath: "retrievalApi",
  baseQuery: axiosBaseQuery(),
  endpoints: (builder) => ({
    search: builder.mutation<SemanticSearchResponse, { projectId: string; query: string; topK?: number }>({
      query: ({ projectId, query, topK = 50 }) => ({
        url: "/search",
        method: "POST",
        params: { project_id: projectId },
        data: {
          query,
          top_k: topK,
          similarity_threshold: 0.3,
        },
      }),
    }),

    searchByCategory: builder.query<CategorySearchResponse, { projectId: string; category: string; topK?: number }>({
      query: ({ projectId, category, topK = 100 }) => ({
        url: "/search/category",
        method: "POST",
        params: { project_id: projectId },
        data: {
          category,
          top_k: topK,
          similarity_threshold: 0.0,
        },
      }),
    }),

    retrievalHealth: builder.query<{ status: string }, void>({
      query: () => ({ url: "/health" }),
    }),
  }),
});

export const {
  useSearchMutation,
  useSearchByCategoryQuery,
  useRetrievalHealthQuery,
} = retrievalApi;
