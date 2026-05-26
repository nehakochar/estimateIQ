import { FileText, FileSpreadsheet, File } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { StatusBadge } from "@/components/shared/StatusBadge";
import { Skeleton } from "@/components/ui/skeleton";
import { useListDocumentsQuery } from "@/hooks";
import { formatRelativeTime, formatFileSize } from "@/utils";
import type { DocumentType } from "@/types";

const fileIcons: Record<DocumentType, React.ComponentType<{ className?: string }>> = {
  pdf: FileText,
  docx: File,
  xlsx: FileSpreadsheet,
};

const fileIconColors: Record<DocumentType, string> = {
  pdf: "text-red-400",
  docx: "text-blue-400",
  xlsx: "text-green-400",
};

export function RecentDocuments() {
  const { data, isLoading } = useListDocumentsQuery({ page: 1, page_size: 5 });

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-sm font-semibold">Recent Documents</CardTitle>
      </CardHeader>
      <CardContent className="p-0">
        {isLoading ? (
          <div className="space-y-0">
            {Array.from({ length: 4 }).map((_, i) => (
              <div
                key={i}
                className="flex items-center gap-3 px-6 py-3 border-b border-border last:border-0"
              >
                <Skeleton className="h-8 w-8 rounded-lg" />
                <div className="flex-1 space-y-1.5">
                  <Skeleton className="h-3 w-48" />
                  <Skeleton className="h-2.5 w-24" />
                </div>
                <Skeleton className="h-5 w-16 rounded-md" />
              </div>
            ))}
          </div>
        ) : !data?.items.length ? (
          <p className="px-6 py-8 text-center text-sm text-muted-foreground">
            No documents yet. Upload your first RFP to get started.
          </p>
        ) : (
          <div>
            {data.items.map((doc) => {
              const Icon = fileIcons[doc.file_type] ?? FileText;
              const iconColor = fileIconColors[doc.file_type] ?? "text-muted-foreground";
              return (
                <div
                  key={doc.id}
                  className="flex items-center gap-3 px-6 py-3 border-b border-border last:border-0 hover:bg-accent/30 transition-colors cursor-pointer"
                >
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-muted">
                    <Icon className={`h-4 w-4 ${iconColor}`} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-foreground truncate">
                      {doc.filename}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {formatFileSize(doc.file_size)} ·{" "}
                      {formatRelativeTime(doc.created_at)}
                    </p>
                  </div>
                  <StatusBadge status={doc.status} />
                </div>
              );
            })}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
