import { CalendarDays } from "lucide-react";
import { Header } from "@/components/layout/Header";
import { PageHeader } from "@/components/shared/PageHeader";
import { EmptyState } from "@/components/shared/EmptyState";

export function TimelinePage() {
  return (
    <div className="flex h-full flex-col">
      <Header breadcrumbs={[{ label: "Dashboard", href: "/" }, { label: "Timeline" }]} />
      <div className="flex-1 overflow-auto p-6 animate-fade-in">
        <div className="space-y-5">
          <PageHeader
            title="Project Timeline"
            description="Automatically generated project timeline and milestones"
          />
          <EmptyState
            icon={<CalendarDays className="h-6 w-6" />}
            title="Timeline generation coming soon"
            description="After estimates are finalized, a detailed project timeline will be generated here."
          />
        </div>
      </div>
    </div>
  );
}
