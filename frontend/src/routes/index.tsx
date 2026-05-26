import { createBrowserRouter, Navigate } from "react-router-dom";
import { App } from "@/app/App";
import { DiscoveryPage } from "@/features/discovery/DiscoveryPage";
import { WorkspaceShell } from "@/features/workspace/WorkspaceShell";
import { UploadPanel } from "@/features/workspace/panels/UploadPanel";
import { RequirementsPanel } from "@/features/workspace/panels/RequirementsPanel";
import { EstimatePanel } from "@/features/workspace/panels/EstimatePanel";
import { TimelinePanel } from "@/features/workspace/panels/TimelinePanel";
import { DocumentsPanel } from "@/features/workspace/panels/DocumentsPanel";
import { NotFoundPage } from "@/routes/NotFoundPage";

export const router = createBrowserRouter([
  {
    path: "/",
    element: <App />,
    children: [
      // Discovery hub
      { index: true, element: <DiscoveryPage /> },

      // Project workspace — nested under slug
      {
        path: "projects/:slug",
        element: <WorkspaceShell />,
        children: [
          { index: true, element: <Navigate to="upload" replace /> },
          { path: "upload",       element: <UploadPanel /> },
          { path: "requirements", element: <RequirementsPanel /> },
          { path: "estimate",     element: <EstimatePanel /> },
          { path: "timeline",     element: <TimelinePanel /> },
          { path: "documents",    element: <DocumentsPanel /> },
        ],
      },
    ],
  },
  { path: "/404", element: <NotFoundPage /> },
  { path: "*",    element: <Navigate to="/404" replace /> },
]);
