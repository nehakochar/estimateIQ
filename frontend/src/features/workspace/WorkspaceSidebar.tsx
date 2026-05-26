import { useAppSelector } from "@/store";
import { type WorkspacePanel } from "@/store/slices/workspaceSlice";
import { portfolioData } from "@/data/portfolio";

const navItems: { id: WorkspacePanel; label: string; icon: React.ReactNode }[] = [
  {
    id: "upload",
    label: "Upload",
    icon: (
      <svg className="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
        <polyline points="17 8 12 3 7 8"/>
        <line x1="12" y1="3" x2="12" y2="15"/>
      </svg>
    ),
  },
  {
    id: "requirements",
    label: "Requirements",
    icon: (
      <svg className="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M9 11l3 3L22 4"/>
        <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/>
      </svg>
    ),
  },
  {
    id: "estimate",
    label: "Estimate",
    icon: (
      <svg className="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <line x1="12" y1="1" x2="12" y2="23"/>
        <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>
      </svg>
    ),
  },
  {
    id: "timeline",
    label: "Timeline",
    icon: (
      <svg className="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
        <line x1="16" y1="2" x2="16" y2="6"/>
        <line x1="8" y1="2" x2="8" y2="6"/>
        <line x1="3" y1="10" x2="21" y2="10"/>
      </svg>
    ),
  },
  {
    id: "documents",
    label: "Documents",
    icon: (
      <svg className="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
        <polyline points="14 2 14 8 20 8"/>
      </svg>
    ),
  },
];

interface WorkspaceSidebarProps {
  onPanelSwitch: (panel: WorkspacePanel) => void;
  onExitToHub: () => void;
}

export function WorkspaceSidebar({ onPanelSwitch, onExitToHub }: WorkspaceSidebarProps) {
  const { selectedProjectId, activePanel } = useAppSelector((s) => s.workspace);
  const project = portfolioData.find((p) => p.id === selectedProjectId);
  const reqCount = project?.requirements.length ?? 0;
  const projectLabel = project
    ? project.name.split(" ")[0] + " Architecture Workspace"
    : "Current Context";

  return (
    <nav className="sidebar">
      {/* Logo */}
      <div className="sidebar-logo-container">
        <div className="logo-block" onClick={onExitToHub}>
          <div className="logo-icon">
            <svg viewBox="0 0 24 24"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/></svg>
          </div>
          <div className="logo-text">
            EstimateIQ
            <span>← Dashboard Hub</span>
          </div>
        </div>
      </div>

      <div className="sidebar-section">{projectLabel}</div>

      {navItems.map((item) => (
        <div
          key={item.id}
          className={`nav-item${activePanel === item.id ? " active" : ""}`}
          onClick={() => onPanelSwitch(item.id)}
        >
          {item.icon}
          {item.label}
          {item.id === "requirements" && (
            <span className="nav-badge">{reqCount}</span>
          )}
        </div>
      ))}

      <div className="sidebar-footer">
        <div className="status-pill">
          <div className="dot-pulse" />
          Workspace Synchronized
        </div>
      </div>
    </nav>
  );
}
