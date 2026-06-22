import { createApi } from '@reduxjs/toolkit/query/react';
import { axiosBaseQuery } from './baseQuery';
import { ProjectEstimatesResponse } from '../types/estimation';

export const estimationApi = createApi({
  reducerPath: 'estimationApi',
  baseQuery: axiosBaseQuery(),
  tagTypes: ['Estimates'],
  endpoints: (builder) => ({
    getProjectEstimates: builder.query<ProjectEstimatesResponse, string>({
      query: (projectId) => ({
        url: `/projects/${projectId}/estimates`,
        method: 'GET',
      }),
      providesTags: (result) =>
        result ? [{ type: 'Estimates', id: result.project_id }] : [],
    }),
    generateProjectEstimates: builder.mutation<{ status: string }, string>({
      query: (projectId) => ({
        url: `/projects/${projectId}/estimates/generate`,
        method: 'POST',
      }),
      invalidatesTags: (result, error, projectId) => [{ type: 'Estimates', id: projectId }],
    }),
  }),
});

export const { useGetProjectEstimatesQuery, useGenerateProjectEstimatesMutation } = estimationApi;
