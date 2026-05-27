import { createApi } from "@reduxjs/toolkit/query/react";
import { axiosBaseQuery } from "./baseQuery";
import type { ProcessingJob, UUID } from "@/types";

export const jobsApi = createApi({
  reducerPath: "jobsApi",
  baseQuery: axiosBaseQuery(),
  tagTypes: ["Job"],
  endpoints: (builder) => ({
    listJobsByDocument: builder.query<ProcessingJob[], UUID>({
      query: (documentId) => ({
        url: "/jobs",
        params: { document_id: documentId },
      }),
      providesTags: (_result, _err, documentId) => [
        { type: "Job", id: documentId },
      ],
    }),

    getJob: builder.query<ProcessingJob, UUID>({
      query: (id) => ({ url: `/jobs/${id}` }),
      providesTags: (_result, _err, id) => [{ type: "Job", id }],
    }),
  }),
});

export const { useListJobsByDocumentQuery, useGetJobQuery } = jobsApi;
