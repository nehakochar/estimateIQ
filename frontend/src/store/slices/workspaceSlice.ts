import { createSlice, type PayloadAction } from "@reduxjs/toolkit";
import type { ReqTab } from "@/data/portfolio";

export type WorkspacePanel = "upload" | "requirements" | "estimate" | "timeline" | "documents";

interface WorkspaceState {
  selectedProjectId: string | null;
  activePanel: WorkspacePanel;
  activeReqTab: ReqTab;
}

const initialState: WorkspaceState = {
  selectedProjectId: null,
  activePanel: "upload",
  activeReqTab: "Functional",
};

export const workspaceSlice = createSlice({
  name: "workspace",
  initialState,
  reducers: {
    enterProject(state, action: PayloadAction<string>) {
      state.selectedProjectId = action.payload;
      state.activePanel = "upload";
      state.activeReqTab = "Functional";
    },
    exitToDiscovery(state) {
      state.selectedProjectId = null;
      state.activePanel = "upload";
    },
    switchPanel(state, action: PayloadAction<WorkspacePanel>) {
      state.activePanel = action.payload;
    },
    switchProject(state, action: PayloadAction<string>) {
      state.selectedProjectId = action.payload;
    },
    setReqTab(state, action: PayloadAction<ReqTab>) {
      state.activeReqTab = action.payload;
    },
  },
});

export const { enterProject, exitToDiscovery, switchPanel, switchProject, setReqTab } =
  workspaceSlice.actions;

export default workspaceSlice.reducer;
