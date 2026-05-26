import {
  FileText,
  Upload,
  CheckCircle,
  Clock,
  TrendingUp,
  Zap,
  ArrowRight,
} from "lucide-react";
import { Link } from "react-router-dom";
import { Header } from "@/components/layout/Header";
import { PageHeader } from "@/components/shared/PageHeader";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { StatsCard } from "./components/StatsCard";
import { RecentDocuments } from "./components/RecentDocuments";

export function DashboardPage() {
  return (
    <div className="flex h-full flex-col">
      <Header
        breadcrumbs={[{ label: "Dashboard" }]}
        actions={
          <Button size="sm" asChild>
            <Link to="/upload">
              <Upload className="h-3.5 w-3.5" />
              Upload RFP
            </Link>
          </Button>
        }
      />

      <div className="flex-1 overflow-auto p-6 space-y-6 animate-fade-in">
        <PageHeader
          title="Dashboard"
          description="Overview of your RFP analysis pipeline"
        />

        {/* Stats grid */}
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <StatsCard
            title="Total Documents"
            value="0"
            icon={FileText}
            description="Across all projects"
            change="Upload your first RFP"
            changeType="neutral"
          />
          <StatsCard
            title="Processing"
            value="0"
            icon={Clock}
            iconColor="text-yellow-400"
            description="Currently in pipeline"
          />
          <StatsCard
            title="Completed"
            value="0"
            icon={CheckCircle}
            iconColor="text-green-400"
            description="Ready for analysis"
          />
          <StatsCard
            title="Accuracy"
            value="—"
            icon={TrendingUp}
            iconColor="text-cyan-400"
            description="Extraction accuracy"
          />
        </div>

        {/* Main content grid */}
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
          {/* Recent documents — takes 2/3 */}
          <div className="lg:col-span-2">
            <RecentDocuments />
          </div>

          {/* Quick actions — takes 1/3 */}
          <div className="space-y-4">
            <Card>
              <CardContent className="p-5 space-y-3">
                <div className="flex items-center gap-2">
                  <Zap className="h-4 w-4 text-primary" />
                  <p className="text-sm font-semibold">Quick Actions</p>
                </div>
                <div className="space-y-2">
                  <QuickAction
                    label="Upload New RFP"
                    description="Add documents to analyze"
                    href="/upload"
                    icon={Upload}
                  />
                  <QuickAction
                    label="Browse Documents"
                    description="View all uploaded files"
                    href="/documents"
                    icon={FileText}
                  />
                </div>
              </CardContent>
            </Card>

            {/* Getting started card */}
            <Card className="border-primary/20 bg-primary/5">
              <CardContent className="p-5 space-y-3">
                <p className="text-sm font-semibold text-foreground">
                  Getting Started
                </p>
                <ol className="space-y-2 text-xs text-muted-foreground">
                  {[
                    "Upload your RFP documents (PDF, DOCX, XLSX)",
                    "AI extracts and structures requirements",
                    "Review generated cost estimates",
                    "Export timeline and deliverables",
                  ].map((step, i) => (
                    <li key={i} className="flex items-start gap-2">
                      <span className="flex h-4 w-4 shrink-0 items-center justify-center rounded-full bg-primary/20 text-[10px] font-bold text-primary mt-0.5">
                        {i + 1}
                      </span>
                      {step}
                    </li>
                  ))}
                </ol>
                <Button size="sm" className="w-full" asChild>
                  <Link to="/upload">
                    Start Now
                    <ArrowRight className="h-3.5 w-3.5" />
                  </Link>
                </Button>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── Quick Action ─────────────────────────────────────────────────────────────

interface QuickActionProps {
  label: string;
  description: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
}

function QuickAction({ label, description, href, icon: Icon }: QuickActionProps) {
  return (
    <Link
      to={href}
      className="flex items-center gap-3 rounded-lg p-2.5 hover:bg-accent transition-colors group"
    >
      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-muted group-hover:bg-primary/10 transition-colors">
        <Icon className="h-4 w-4 text-muted-foreground group-hover:text-primary transition-colors" />
      </div>
      <div className="min-w-0">
        <p className="text-xs font-medium text-foreground">{label}</p>
        <p className="text-[11px] text-muted-foreground truncate">{description}</p>
      </div>
      <ArrowRight className="ml-auto h-3.5 w-3.5 text-muted-foreground/50 group-hover:text-muted-foreground transition-colors shrink-0" />
    </Link>
  );
}
