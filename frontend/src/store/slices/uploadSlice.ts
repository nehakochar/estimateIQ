import { createSlice, createAsyncThunk, type PayloadAction } from "@reduxjs/toolkit";
import { axiosInstance } from "@/services/api-client";
import { documentsApi } from "@/services/documentsApi";
import type { Document, UUID } from "@/types";

// ─── Types ────────────────────────────────────────────────────────────────────

export interface UploadFile {
  id: string;
  /** NOTE: File is not serializable — kept in state but excluded from devtools checks */
  file: File;
  name: string;
  size: number;
  type: string;
  progress: number;
  status: "pending" | "uploading" | "success" | "error";
  error?: string;
  documentId?: UUID;
}

interface UploadState {
  files: UploadFile[];
  projectName: string;
  isUploading: boolean;
  uploadedDocuments: Document[];
  currentProjectId: UUID | null;
  uploadError: string | null;
}

const initialState: UploadState = {
  files: [],
  projectName: "",
  isUploading: false,
  uploadedDocuments: [],
  currentProjectId: null,
  uploadError: null,
};

// ─── Async thunk ──────────────────────────────────────────────────────────────

export interface UploadPayload {
  projectName: string;
  files: File[];
}

export interface UploadResponse {
  project_id: UUID;
  documents: Document[];
}

export const uploadDocuments = createAsyncThunk<
  UploadResponse,
  UploadPayload,
  { rejectValue: string }
>(
  "upload/uploadDocuments",
  async ({ projectName, files }, { dispatch, rejectWithValue }) => {
    const form = new FormData();
    form.append("project_name", projectName);
    files.forEach((file) => form.append("files", file));

    try {
      const response = await axiosInstance.post<UploadResponse>(
        "/api/upload",
        form,
        {
          headers: { "Content-Type": "multipart/form-data" },
          onUploadProgress: (event) => {
            const progress = event.total
              ? Math.round((event.loaded * 100) / event.total)
              : 0;
            dispatch(setGlobalProgress(progress));
          },
        }
      );

      // Invalidate the documents list cache so DocumentsPage auto-refreshes
      dispatch(documentsApi.util.invalidateTags([{ type: "Document", id: "LIST" }]));

      return response.data;
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Upload failed";
      return rejectWithValue(message);
    }
  }
);

// ─── Slice ────────────────────────────────────────────────────────────────────

export const uploadSlice = createSlice({
  name: "upload",
  initialState,
  reducers: {
    addFiles(
      state,
      action: PayloadAction<Omit<UploadFile, "progress" | "status">[]>
    ) {
      const newFiles = action.payload.map((f) => ({
        ...f,
        progress: 0,
        status: "pending" as const,
      }));
      state.files.push(...newFiles);
    },
    removeFile(state, action: PayloadAction<string>) {
      state.files = state.files.filter((f) => f.id !== action.payload);
    },
    clearFiles(state) {
      state.files = [];
    },
    setProjectName(state, action: PayloadAction<string>) {
      state.projectName = action.payload;
    },
    setGlobalProgress(state, action: PayloadAction<number>) {
      // Spread progress across all pending/uploading files
      state.files.forEach((f) => {
        if (f.status === "uploading" || f.status === "pending") {
          f.progress = action.payload;
        }
      });
    },
    resetUpload() {
      return initialState;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(uploadDocuments.pending, (state) => {
        state.isUploading = true;
        state.uploadError = null;
        state.files.forEach((f) => {
          f.status = "uploading";
        });
      })
      .addCase(uploadDocuments.fulfilled, (state, action) => {
        state.isUploading = false;
        state.uploadedDocuments = action.payload.documents;
        state.currentProjectId = action.payload.project_id;
        state.files.forEach((f) => {
          f.status = "success";
          f.progress = 100;
        });
      })
      .addCase(uploadDocuments.rejected, (state, action) => {
        state.isUploading = false;
        state.uploadError = action.payload ?? "Upload failed";
        state.files.forEach((f) => {
          if (f.status === "uploading") {
            f.status = "error";
            f.error = action.payload ?? "Upload failed";
          }
        });
      });
  },
});

export const {
  addFiles,
  removeFile,
  clearFiles,
  setProjectName,
  setGlobalProgress,
  resetUpload,
} = uploadSlice.actions;

export default uploadSlice.reducer;
