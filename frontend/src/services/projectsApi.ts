import { createApi } from "@reduxjs/toolkit/query/react";
import { axiosBaseQuery } from "./baseQuery";

export interface ProjectResponse {
  id: string;
  name: string;
  client_name: string | null;
  status: string;
  created_at: string;
}

export interface ProjectListResponse {
  total: number;
  projects: ProjectResponse[];
}

export interface ProjectCreate {
  name: string;
  client_name?: string;
}

export const projectsApi = createApi({
  reducerPath: "projectsApi",
  baseQuery: axiosBaseQuery(),
  tagTypes: ["Project"],
  endpoints: (builder) => ({
    // GET /projects
    listProjects: builder.query<ProjectListResponse, void>({
      query: () => ({ url: "/projects", method: "GET" }),
      providesTags: [{ type: "Project", id: "LIST" }],
    }),

    // POST /projects
    createProject: builder.mutation<ProjectResponse, ProjectCreate>({
      query: (body) => ({ url: "/projects", method: "POST", data: body }),
      invalidatesTags: [{ type: "Project", id: "LIST" }],
    }),
  }),
});

export const { useListProjectsQuery, useCreateProjectMutation } = projectsApi;
