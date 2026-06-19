import { useEffect } from "react";
import { Outlet, useParams, useNavigate, useLocation, Navigate } from "react-router-dom";
import { useAppDispatch, useAppSelector } from "@/store";
import { enterProject, exitToDiscovery, switchPanel, type WorkspacePanel } from "@/store/slices/workspaceSlice";
import { useListProjectsQuery } from "@/services/projectsApi";
import { WorkspaceSidebar } from "./WorkspaceSidebar";

// Map URL segment → WorkspacePanel type
const PANEL_MAP: Record<string, WorkspacePanel> = {
  upload:       "upload",
  requirements: "requirements",
  estimate:     "estimate",
  timeline:     "timeline",
  documents:    "documents",
};

const PANEL_LABEL: Record<WorkspacePanel, string> = {
  upload:       "Upload Workspace",
  requirements: "Requirements",
  estimate:     "Estimate",
  timeline:     "Timeline",
  documents:    "Documents",
};

export function WorkspaceShell() {
  // The URL param is the project UUID (e.g. /projects/abc-123/upload)
  const { slug: projectId } = useParams<{ slug: string }>();
  const navigate  = useNavigate();
  const location  = useLocation();
  const dispatch  = useAppDispatch();
  const { activePanel } = useAppSelector((s) => s.workspace);

  // Fetch all projects and find the one matching the UUID in the URL
  const { data, isLoading } = useListProjectsQuery();
  const project = data?.projects.find((p) => p.id === projectId);

  // Sync Redux state when project changes
  useEffect(() => {
    if (project) dispatch(enterProject(project.id));
  }, [project?.id]);

  // Sync activePanel from URL segment
  useEffect(() => {
    const segment = location.pathname.split("/").pop() as WorkspacePanel;
    if (PANEL_MAP[segment] && segment !== activePanel) {
      dispatch(switchPanel(PANEL_MAP[segment]));
    }
  }, [location.pathname]);

  // Still loading — show nothing (avoids flash to 404)
  if (isLoading) {
    return (
      <div className="workspace-shell">
        <div style={{ display: "flex", alignItems: "center", justifyContent: "center", flex: 1, color: "var(--muted-foreground)" }}>
          Loading project…
        </div>
      </div>
    );
  }

  // Project not found after load → 404
  if (!project) return <Navigate to="/404" replace />;

  const handlePanelSwitch = (panel: WorkspacePanel) => {
    dispatch(switchPanel(panel));
    navigate(`/projects/${projectId}/${panel}`);
  };

  const handleExitToHub = () => {
    dispatch(exitToDiscovery());
    navigate("/");
  };

  return (
    <div className="workspace-shell">
      <WorkspaceSidebar
        projectName={project.name}
        onPanelSwitch={handlePanelSwitch}
        onExitToHub={handleExitToHub}
      />

      <div className="workspace-main">
        {/* Topbar */}
        <div className="topbar">
          <div className="topbar-left">
            <span className="topbar-title">{PANEL_LABEL[activePanel]}</span>
            <span className="topbar-sub">— {project.name}</span>
            {project.client_name && (
              <span className="topbar-sub"> · {project.client_name}</span>
            )}
          </div>

          <div className="topbar-right">
            <span className="ai-tag">Workspace Hub v2.5</span>
            <button className="btn btn-ghost" onClick={handleExitToHub}>
              ← Dashboard Hub
            </button>
          </div>
        </div>

        {/* Routed panel content */}
        <div className="content">
          <Outlet />
        </div>
      </div>
    </div>
  );
}
