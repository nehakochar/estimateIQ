import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { portfolioData, type Project, toSlug } from "@/data/portfolio";
import { CreateProjectModal } from "./CreateProjectModal";

export function DiscoveryPage() {
  const navigate = useNavigate();
  const [modalOpen, setModalOpen] = useState(false);
  const [projects, setProjects] = useState<Project[]>(portfolioData);

  const handleCreate = (data: { projectName: string; clientName?: string }) => {
    const slug = toSlug(data.projectName);
    const newProject: Project = {
      id: `proj-${Date.now()}`,
      slug,
      name: data.projectName,
      desc: data.clientName ? `Client: ${data.clientName}` : "No description provided.",
      badge: "Pending Audit",
      statusClass: "b-pending",
      progress: 0,
      reqCount: 0,
      requirements: [],
      modules: [],
      estimates: [],
      timeline: [],
      docs: [],
    };
    setProjects((prev) => [newProject, ...prev]);
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
                  <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/>
                </svg>
              </div>
              <div className="logo-text">
                EstimateIQ
                <span>Enterprise Workspace Hub</span>
              </div>
            </div>
          </div>
          <div className="topbar-right">
            <span className="ai-tag">Workspace Hub v2.5</span>
          </div>
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
                  <line x1="12" y1="5" x2="12" y2="19"/>
                  <line x1="5" y1="12" x2="19" y2="12"/>
                </svg>
                Create New Project
              </button>
            </div>
          </div>

          {/* KPI cards */}
          <div className="kpi-container">
            <div className="kpi-card">
              <div className="kpi-value">{projects.length} Workspaces</div>
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

          {/* Project grid */}
          <div className="project-grid">
            {projects.map((p) => (
              <div
                key={p.id}
                className="project-card"
                onClick={() => navigate(`/projects/${p.slug}/upload`)}
              >
                <div>
                  <div className="project-card-header">
                    <span className={`badge ${p.statusClass}`}>{p.badge}</span>
                    <span className="project-req-count">{p.reqCount} Req Elements</span>
                  </div>
                  <div className="project-title">{p.name}</div>
                  <div className="project-desc">{p.desc}</div>
                </div>
                <div>
                  <div className="project-progress-header">
                    <span>Target Architecture Setup</span>
                    <span className="project-progress-pct">{p.progress}%</span>
                  </div>
                  <div className="progress-bar">
                    <div className="progress-fill" style={{ width: `${p.progress}%` }} />
                  </div>
                  <div className="project-meta">
                    <span>Click to open workspace →</span>
                  </div>
                </div>
              </div>
            ))}
          </div>

        </div>
      </div>

      <CreateProjectModal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        onCreate={handleCreate}
      />
    </div>
  );
}
