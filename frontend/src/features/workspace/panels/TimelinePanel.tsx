import { useAppSelector } from "@/store";
import { portfolioData } from "@/data/portfolio";

export function TimelinePanel() {
  const { selectedProjectId } = useAppSelector((s) => s.workspace);
  const project = portfolioData.find((p) => p.id === selectedProjectId);

  return (
    <div>
      <div className="section-hdr">
        <h2>Milestone Schedule Mapping</h2>
      </div>
      <div className="card">
        <div className="gantt-wrap">
          <table className="gantt-table">
            <thead>
              <tr>
                <th style={{ width: 300 }}>Functional Milestone Block</th>
                <th>Target Phase Deployment Schedule Preview</th>
              </tr>
            </thead>
            <tbody>
              {!project?.timeline.length ? (
                <tr>
                  <td colSpan={2} style={{ color: "var(--text3)" }}>No timeline scheduled.</td>
                </tr>
              ) : (
                project.timeline.map((t, i) => (
                  <tr key={i}>
                    <td style={{ fontWeight: 500 }}>{t.task}</td>
                    <td>
                      <div className="gantt-bar-preview" style={{ width: t.length }} />
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
