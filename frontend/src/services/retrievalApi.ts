import { createApi } from "@reduxjs/toolkit/query/react";
import { axiosBaseQuery } from "./baseQuery";
import type { RetrievalQuery, RetrievalResult } from "@/types";

export const retrievalApi = createApi({
  reducerPath: "retrievalApi",
  baseQuery: axiosBaseQuery({ baseUrl: "" }),
  endpoints: (builder) => ({
    search: builder.mutation<RetrievalResult[], RetrievalQuery>({
      query: (body) => ({
        url: "/api/retrieval/search",
        method: "POST",
        data: body,
      }),
    }),

    retrievalHealth: builder.query<{ status: string }, void>({
      query: () => ({ url: "/api/retrieval/health" }),
    }),
  }),
});

export const { useSearchMutation, useRetrievalHealthQuery } = retrievalApi;
