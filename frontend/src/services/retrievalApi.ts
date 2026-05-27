import { createApi } from "@reduxjs/toolkit/query/react";
import { axiosBaseQuery } from "./baseQuery";
import type { RetrievalQuery, RetrievalResult } from "@/types";

export interface RetrievalResultItem {
  chunk_id: string;
  text: string;
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

export const retrievalApi = createApi({
  reducerPath: "retrievalApi",
  baseQuery: axiosBaseQuery(),
  endpoints: (builder) => ({
    search: builder.mutation<RetrievalResult[], RetrievalQuery>({
      query: (body) => ({
        url: "/search",
        method: "POST",
        data: body,
      }),
    }),

    searchByCategory: builder.query<CategorySearchResponse, { projectId: string; category: string; topK?: number }>({
      query: ({ projectId, category, topK = 100 }) => ({
        url: "/search/category",
        method: "POST",
        params: {
          project_id: projectId,
        },
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

export const { useSearchMutation, useSearchByCategoryQuery, useRetrievalHealthQuery } = retrievalApi;
