import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useListProjectsQuery } from "@/services/projectsApi";
import type { ProjectResponse } from "@/services/projectsApi";
import { CreateProjectModal } from "./CreateProjectModal";

export function DiscoveryPage() {
  const navigate = useNavigate();
  const [modalOpen, setModalOpen] = useState(false);

  const { data, isLoading, isError, refetch } = useListProjectsQuery();
  const projects: ProjectResponse[] = data?.projects ?? [];

  const handleCreated = (_projectId: string) => {
    // RTK Query auto-refetches via tag invalidation; nothing extra needed.
  };

  const handleOpenProject = (project: ProjectResponse) => {
    // Use the project UUID as the URL param — reliable, no slug lookup needed
    navigate(`/projects/${project.id}/upload`);
  };

  return (
    <div className="app-shell">
      <div className="app-main">

        {/* Topbar */}
        <div className="topbar">
          <div className="topbar-left">
            <div className="logo-block">
              <div className="logo-icon">
                <svg viewBox="0 0 24 24">
                  <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" />
                </svg>
              </div>
              <div className="logo-text">
                EstimateIQ
                <span>Enterprise Workspace Hub</span>
              </div>
            </div>
          </div>
          {/* <div className="topbar-right">
            <span className="ai-tag">Workspace Hub v2.5</span>
          </div> */}
        </div>

        {/* Scrollable content */}
        <div className="content">

          {/* Hub intro */}
          <div className="hub-intro">
            <div>
              <span className="ai-tag">Portfolio Deployment Overview</span>
              <h1>System Scope Control Panel</h1>
            </div>
            <div className="hub-actions">
              <button className="btn btn-primary" onClick={() => setModalOpen(true)}>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                  <line x1="12" y1="5" x2="12" y2="19" />
                  <line x1="5" y1="12" x2="19" y2="12" />
                </svg>
                Create New Project
              </button>
            </div>
          </div>

          {/* KPI cards */}
          <div className="kpi-container">
            <div className="kpi-card">
              <div className="kpi-value">{isLoading ? "—" : `${projects.length} Workspaces`}</div>
              <div className="kpi-label">Active Core Systems</div>
              <div className="kpi-trend">⚡ Operational Live Stack</div>
            </div>
            <div className="kpi-card">
              <div className="kpi-value">1,530 Hours</div>
              <div className="kpi-label">Aggregated Engineering Dev</div>
              <div className="kpi-trend">↑ 12% Month-Over-Month</div>
            </div>
            <div className="kpi-card">
              <div className="kpi-value">341 Units</div>
              <div className="kpi-label">AI Parsed Requirements</div>
              <div className="kpi-trend kpi-trend-accent">✦ 99.4% Parsing Acc</div>
            </div>
            <div className="kpi-card">
              <div className="kpi-value">$2.45M</div>
              <div className="kpi-label">Realized Value Capitalization</div>
              <div className="kpi-trend">✓ Audited Lifecycle</div>
            </div>
          </div>

          {/* Loading state */}
          {isLoading && (
            <div className="project-grid">
              {[1, 2, 3].map((i) => (
                <div key={i} className="project-card" style={{ opacity: 0.5, pointerEvents: "none" }}>
                  <div>
                    <div className="project-card-header">
                      <span className="badge b-pending">Loading…</span>
                    </div>
                    <div className="project-title" style={{ background: "var(--border)", borderRadius: 4, height: 20, width: "60%" }} />
                    <div className="project-desc" style={{ background: "var(--border)", borderRadius: 4, height: 14, width: "80%", marginTop: 8 }} />
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Error state */}
          {isError && !isLoading && (
            <div style={{ textAlign: "center", padding: "2rem", color: "var(--muted-foreground)" }}>
              <p>Failed to load projects.</p>
              <button className="btn btn-ghost" style={{ marginTop: "0.75rem" }} onClick={() => refetch()}>
                Retry
              </button>
            </div>
          )}

          {/* Empty state */}
          {!isLoading && !isError && projects.length === 0 && (
            <div style={{ textAlign: "center", padding: "3rem", color: "var(--muted-foreground)" }}>
              <p style={{ marginBottom: "1rem" }}>No projects yet. Create your first one to get started.</p>
              <button className="btn btn-primary" onClick={() => setModalOpen(true)}>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                  <line x1="12" y1="5" x2="12" y2="19" />
                  <line x1="5" y1="12" x2="19" y2="12" />
                </svg>
                Create New Project
              </button>
            </div>
          )}

          {/* Project grid */}
          {!isLoading && !isError && projects.length > 0 && (
            <div className="project-grid">
              {projects.map((p) => (
                <div
                  key={p.id}
                  className="project-card"
                  onClick={() => handleOpenProject(p)}
                >
                  <div>
                    <div className="project-card-header">
                      <span className={`badge ${p.status === "active" ? "b-active" : p.status === "pipeline" ? "b-pipeline" : "b-pending"}`}>
                        {p.status.charAt(0).toUpperCase() + p.status.slice(1)}
                      </span>
                    </div>
                    <div className="project-title">{p.name}</div>
                    <div className="project-desc">
                      {p.client_name ? `Client: ${p.client_name}` : "No client specified."}
                    </div>
                  </div>
                  <div>

                    <div className="project-meta">
                      <span>
                        Created {new Date(p.created_at).toLocaleDateString()}
                      </span>
                      <span>Click to open workspace →</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

        </div>
      </div>

      <CreateProjectModal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        onCreated={handleCreated}
      />
    </div>
  );
}
