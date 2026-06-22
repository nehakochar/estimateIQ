import { configureStore } from "@reduxjs/toolkit";
import { useDispatch, useSelector, type TypedUseSelectorHook } from "react-redux";
import uiReducer from "./slices/uiSlice";
import uploadReducer from "./slices/uploadSlice";
import workspaceReducer from "./slices/workspaceSlice";
import { documentsApi } from "@/services/documentsApi";
import { jobsApi } from "@/services/jobsApi";
import { projectsApi } from "@/services/projectsApi";
import { extractionApi } from "@/services/extractionApi";
import { estimationApi } from "@/services/estimationApi";

export const store = configureStore({
  reducer: {
    ui: uiReducer,
    upload: uploadReducer,
    workspace: workspaceReducer,
    [documentsApi.reducerPath]: documentsApi.reducer,
    [jobsApi.reducerPath]: jobsApi.reducer,
    [projectsApi.reducerPath]: projectsApi.reducer,
    [extractionApi.reducerPath]: extractionApi.reducer,
    [estimationApi.reducerPath]: estimationApi.reducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredPaths: ["upload.files"],
        ignoredActions: ["upload/addFiles"],
      },
    }).concat(
      documentsApi.middleware,
      jobsApi.middleware,
      projectsApi.middleware,
      extractionApi.middleware,
      estimationApi.middleware,
    ),
  devTools: import.meta.env.VITE_ENVIRONMENT !== "production",
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;

export const useAppDispatch = () => useDispatch<AppDispatch>();
export const useAppSelector: TypedUseSelectorHook<RootState> = useSelector;
