import { useAppDispatch, useAppSelector } from "@/store";
import { exitToDiscovery, switchProject } from "@/store/slices/workspaceSlice";
import { WorkspaceSidebar } from "./WorkspaceSidebar";
import { UploadPanel } from "./panels/UploadPanel";
import { RequirementsPanel } from "./panels/RequirementsPanel";
import { EstimatePanel } from "./panels/EstimatePanel";
import { TimelinePanel } from "./panels/TimelinePanel";
import { DocumentsPanel } from "./panels/DocumentsPanel";
import { portfolioData } from "@/data/portfolio";

const panelLabel: Record<string, string> = {
  upload:       "Upload Workspace",
  requirements: "Requirements",
  estimate:     "Estimate",
  timeline:     "Timeline",
  documents:    "Documents",
};

export function WorkspacePage() {
  const dispatch = useAppDispatch();
  const { selectedProjectId, activePanel } = useAppSelector((s) => s.workspace);

  return (
    <div className="workspace-shell">
      <WorkspaceSidebar />

      <div className="workspace-main">
        <div className="topbar">
          <div className="topbar-left">
            <span className="topbar-title">{panelLabel[activePanel] ?? "Workspace"}</span>
            <span className="topbar-sub">— Tracking Context</span>

            <div className="topbar-project-switcher">
              <span className="topbar-divider">/</span>
              <select
                className="project-dropdown"
                value={selectedProjectId ?? ""}
                onChange={(e) => dispatch(switchProject(e.target.value))}
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
            <button className="btn btn-ghost" onClick={() => dispatch(exitToDiscovery())}>
              ← Dashboard Hub
            </button>
          </div>
        </div>

        <div className="content">
          {activePanel === "upload"       && <UploadPanel />}
          {activePanel === "requirements" && <RequirementsPanel />}
          {activePanel === "estimate"     && <EstimatePanel />}
          {activePanel === "timeline"     && <TimelinePanel />}
          {activePanel === "documents"    && <DocumentsPanel />}
        </div>
      </div>
    </div>
  );
}
