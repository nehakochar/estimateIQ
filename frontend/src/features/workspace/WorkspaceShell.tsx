import { useEffect } from "react";
import { Outlet, useParams, useNavigate, useLocation, Navigate } from "react-router-dom";
import { useAppDispatch, useAppSelector } from "@/store";
import { enterProject, exitToDiscovery, switchPanel, switchProject, type WorkspacePanel } from "@/store/slices/workspaceSlice";
import { portfolioData } from "@/data/portfolio";
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
  const { slug } = useParams<{ slug: string }>();
  const navigate  = useNavigate();
  const location  = useLocation();
  const dispatch  = useAppDispatch();
  const { selectedProjectId, activePanel } = useAppSelector((s) => s.workspace);

  // Find project by slug
  const project = portfolioData.find((p) => p.slug === slug);

  // Sync Redux state when slug changes
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

  // Unknown slug → 404
  if (!project) return <Navigate to="/404" replace />;

  const handlePanelSwitch = (panel: WorkspacePanel) => {
    dispatch(switchPanel(panel));
    navigate(`/projects/${slug}/${panel}`);
  };

  const handleProjectSwitch = (newSlug: string) => {
    const newProject = portfolioData.find((p) => p.id === newSlug);
    if (!newProject) return;
    dispatch(switchProject(newProject.id));
    navigate(`/projects/${newProject.slug}/${activePanel}`);
  };

  const handleExitToHub = () => {
    dispatch(exitToDiscovery());
    navigate("/");
  };

  return (
    <div className="workspace-shell">
      <WorkspaceSidebar
        onPanelSwitch={handlePanelSwitch}
        onExitToHub={handleExitToHub}
      />

      <div className="workspace-main">
        {/* Topbar */}
        <div className="topbar">
          <div className="topbar-left">
            <span className="topbar-title">{PANEL_LABEL[activePanel]}</span>
            <span className="topbar-sub">— Tracking Context</span>

            <div className="topbar-project-switcher">
              <span className="topbar-divider">/</span>
              <select
                className="project-dropdown"
                value={selectedProjectId ?? ""}
                onChange={(e) => handleProjectSwitch(e.target.value)}
              >
                <option value="" disabled>Change Project Context...</option>
                {portfolioData.map((p) => (
                  <option key={p.id} value={p.id}>{p.name}</option>
                ))}
              </select>
            </div>
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
