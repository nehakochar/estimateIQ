import { ListChecks } from "lucide-react";
import { Header } from "@/components/layout/Header";
import { PageHeader } from "@/components/shared/PageHeader";
import { EmptyState } from "@/components/shared/EmptyState";

export function RequirementsPage() {
  return (
    <div className="flex h-full flex-col">
      <Header breadcrumbs={[{ label: "Dashboard", href: "/" }, { label: "Requirements" }]} />
      <div className="flex-1 overflow-auto p-6 animate-fade-in">
        <div className="space-y-5">
          <PageHeader
            title="Requirements"
            description="AI-extracted requirements from your RFP documents"
          />
          <EmptyState
            icon={<ListChecks className="h-6 w-6" />}
            title="Requirements extraction coming soon"
            description="Upload and process RFP documents to automatically extract structured requirements."
          />
        </div>
      </div>
    </div>
  );
}
