import { Badge } from "@/components/ui/badge";
import type { DocumentStatus, JobStatus, ProjectStatus } from "@/types";

type AnyStatus = DocumentStatus | JobStatus | ProjectStatus;

const statusConfig: Record<
  AnyStatus,
  { label: string; variant: "success" | "warning" | "destructive" | "info" | "secondary" }
> = {
  // Document statuses
  uploaded: { label: "Uploaded", variant: "secondary" },
  processing: { label: "Processing", variant: "warning" },
  parsed: { label: "Parsed", variant: "info" },
  chunked: { label: "Chunked", variant: "info" },
  embedded: { label: "Embedded", variant: "success" },
  failed: { label: "Failed", variant: "destructive" },
  // Job statuses
  pending: { label: "Pending", variant: "secondary" },
  running: { label: "Running", variant: "warning" },
  completed: { label: "Completed", variant: "success" },
  // Project statuses
  active: { label: "Active", variant: "success" },
};

interface StatusBadgeProps {
  status: AnyStatus;
  className?: string;
}

export function StatusBadge({ status, className }: StatusBadgeProps) {
  const config = statusConfig[status] ?? { label: status, variant: "secondary" as const };
  return (
    <Badge variant={config.variant} className={className}>
      {config.label}
    </Badge>
  );
}
