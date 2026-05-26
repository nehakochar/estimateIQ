import { Calculator } from "lucide-react";
import { Header } from "@/components/layout/Header";
import { PageHeader } from "@/components/shared/PageHeader";
import { EmptyState } from "@/components/shared/EmptyState";

export function EstimatePage() {
  return (
    <div className="flex h-full flex-col">
      <Header breadcrumbs={[{ label: "Dashboard", href: "/" }, { label: "Estimates" }]} />
      <div className="flex-1 overflow-auto p-6 animate-fade-in">
        <div className="space-y-5">
          <PageHeader
            title="Cost Estimates"
            description="AI-generated cost and effort estimates based on extracted requirements"
          />
          <EmptyState
            icon={<Calculator className="h-6 w-6" />}
            title="Estimates coming soon"
            description="Once requirements are extracted, AI will generate detailed cost and effort estimates."
          />
        </div>
      </div>
    </div>
  );
}
