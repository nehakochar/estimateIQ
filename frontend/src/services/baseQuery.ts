import type { BaseQueryFn } from "@reduxjs/toolkit/query";
import type { AxiosRequestConfig, AxiosError } from "axios";
import { axiosInstance } from "./api-client";

/**
 * RTK Query baseQuery backed by our Axios instance.
 *
 * axiosInstance already has baseURL = VITE_API_BASE_URL, so endpoint URLs
 * here are just paths (e.g. "/documents/123/status") — no need to repeat
 * the origin. The baseUrl param is kept for flexibility but defaults to "".
 */
export const axiosBaseQuery =
  (
    { baseUrl }: { baseUrl: string } = { baseUrl: "" }
  ): BaseQueryFn<
    {
      url: string;
      method?: AxiosRequestConfig["method"];
      data?: unknown;
      params?: unknown;
      headers?: Record<string, string>;
    },
    unknown,
    { status?: number; message: string }
  > =>
  async ({ url, method = "GET", data, params, headers }) => {
    try {
      const result = await axiosInstance({
        url: baseUrl + url,
        method,
        data,
        params,
        headers,
      });
      return { data: result.data };
    } catch (err) {
      const axiosError = err as AxiosError<{ detail?: string }>;
      return {
        error: {
          status: axiosError.response?.status,
          message:
            axiosError.response?.data?.detail ??
            axiosError.message ??
            "Unknown error",
        },
      };
    }
  };
