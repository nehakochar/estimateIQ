import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { FileText, FileSpreadsheet, File, Trash2, Upload, RefreshCw } from "lucide-react";
import { Header } from "@/components/layout/Header";
import { PageHeader } from "@/components/shared/PageHeader";
import { StatusBadge } from "@/components/shared/StatusBadge";
import { EmptyState } from "@/components/shared/EmptyState";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  useListDocumentsQuery,
  useDeleteDocumentMutation,
} from "@/hooks";
import { formatFileSize, formatRelativeTime } from "@/utils";
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

export function DocumentsPage() {
  const navigate = useNavigate();
  const { data, isLoading, isFetching, refetch } = useListDocumentsQuery();
  const [deleteDocument, { isLoading: isDeleting }] = useDeleteDocumentMutation();
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const handleDelete = async (id: string) => {
    setDeletingId(id);
    try {
      await deleteDocument(id).unwrap();
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <div className="flex h-full flex-col">
      <Header
        breadcrumbs={[{ label: "Dashboard", href: "/" }, { label: "Documents" }]}
        actions={
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => refetch()}
              disabled={isFetching}
              aria-label="Refresh"
            >
              <RefreshCw className={`h-4 w-4 ${isFetching ? "animate-spin" : ""}`} />
            </Button>
            <Button size="sm" onClick={() => navigate("/upload")}>
              <Upload className="h-3.5 w-3.5" />
              Upload
            </Button>
          </div>
        }
      />

      <div className="flex-1 overflow-auto p-6 animate-fade-in">
        <div className="space-y-5">
          <PageHeader
            title="Documents"
            description={
              data?.total
                ? `${data.total} document${data.total !== 1 ? "s" : ""} across all projects`
                : "All uploaded RFP documents"
            }
          />

          {isLoading ? (
            <DocumentsTableSkeleton />
          ) : !data?.items.length ? (
            <EmptyState
              icon={<FileText className="h-6 w-6" />}
              title="No documents yet"
              description="Upload your first RFP document to start the analysis pipeline."
              action={{ label: "Upload RFP", onClick: () => navigate("/upload") }}
            />
          ) : (
            <div className="rounded-xl border border-border overflow-hidden">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border bg-muted/30">
                    <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                      Document
                    </th>
                    <th className="hidden md:table-cell px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                      Type
                    </th>
                    <th className="hidden sm:table-cell px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                      Size
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                      Status
                    </th>
                    <th className="hidden lg:table-cell px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                      Uploaded
                    </th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-muted-foreground uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {data.items.map((doc) => {
                    const Icon = fileIcons[doc.file_type] ?? FileText;
                    const iconColor =
                      fileIconColors[doc.file_type] ?? "text-muted-foreground";
                    const isThisDeleting =
                      deletingId === doc.id && isDeleting;

                    return (
                      <tr
                        key={doc.id}
                        className="hover:bg-accent/20 transition-colors"
                      >
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-3">
                            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-muted">
                              <Icon className={`h-4 w-4 ${iconColor}`} />
                            </div>
                            <span className="font-medium text-foreground truncate max-w-[200px]">
                              {doc.filename}
                            </span>
                          </div>
                        </td>
                        <td className="hidden md:table-cell px-4 py-3 text-muted-foreground uppercase text-xs">
                          {doc.file_type}
                        </td>
                        <td className="hidden sm:table-cell px-4 py-3 text-muted-foreground text-xs">
                          {formatFileSize(doc.file_size)}
                        </td>
                        <td className="px-4 py-3">
                          <StatusBadge status={doc.status} />
                        </td>
                        <td className="hidden lg:table-cell px-4 py-3 text-muted-foreground text-xs">
                          {formatRelativeTime(doc.created_at)}
                        </td>
                        <td className="px-4 py-3 text-right">
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-7 w-7 text-muted-foreground hover:text-destructive"
                            onClick={() => handleDelete(doc.id)}
                            disabled={isThisDeleting}
                            aria-label={`Delete ${doc.filename}`}
                          >
                            {isThisDeleting ? (
                              <LoadingSpinner size="sm" />
                            ) : (
                              <Trash2 className="h-3.5 w-3.5" />
                            )}
                          </Button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function DocumentsTableSkeleton() {
  return (
    <div className="rounded-xl border border-border overflow-hidden">
      <div className="border-b border-border bg-muted/30 px-4 py-3">
        <Skeleton className="h-3 w-48" />
      </div>
      {Array.from({ length: 5 }).map((_, i) => (
        <div
          key={i}
          className="flex items-center gap-4 px-4 py-3 border-b border-border last:border-0"
        >
          <Skeleton className="h-8 w-8 rounded-lg shrink-0" />
          <Skeleton className="h-3 flex-1 max-w-xs" />
          <Skeleton className="h-5 w-16 rounded-md ml-auto" />
        </div>
      ))}
    </div>
  );
}
