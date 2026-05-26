import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { ArrowRight, CheckCircle2 } from "lucide-react";
import { Header } from "@/components/layout/Header";
import { PageHeader } from "@/components/shared/PageHeader";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";
import { DropZone } from "./components/DropZone";
import { useAppDispatch, useAppSelector } from "@/store";
import { setProjectName, resetUpload } from "@/store/slices/uploadSlice";
import { useUpload } from "@/hooks";

// ─── Schema ───────────────────────────────────────────────────────────────────

const uploadSchema = z.object({
  projectName: z
    .string()
    .min(3, "Project name must be at least 3 characters")
    .max(100, "Project name must be under 100 characters"),
});

type UploadFormValues = z.infer<typeof uploadSchema>;

// ─── Page ─────────────────────────────────────────────────────────────────────

export function UploadPage() {
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const { files } = useAppSelector((s) => s.upload);
  const { upload, isUploading, isSuccess, uploadError } = useUpload();

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm<UploadFormValues>({
    resolver: zodResolver(uploadSchema),
  });

  // Sync project name to store so DropZone can read it if needed
  const projectNameValue = watch("projectName");
  useEffect(() => {
    dispatch(setProjectName(projectNameValue ?? ""));
  }, [projectNameValue, dispatch]);

  // Redirect to documents after successful upload
  useEffect(() => {
    if (isSuccess) {
      const timer = setTimeout(() => {
        dispatch(resetUpload());
        navigate("/documents");
      }, 2000);
      return () => clearTimeout(timer);
    }
  }, [isSuccess, navigate, dispatch]);

  const onSubmit = (values: UploadFormValues) => {
    if (files.length === 0) return;
    upload({
      projectName: values.projectName,
      files: files.map((f) => f.file),
    });
  };

  const canSubmit = files.length > 0 && !isUploading && !isSuccess;

  return (
    <div className="flex h-full flex-col">
      <Header
        breadcrumbs={[
          { label: "Dashboard", href: "/" },
          { label: "Upload RFP" },
        ]}
      />

      <div className="flex-1 overflow-auto p-6 animate-fade-in">
        <div className="mx-auto max-w-2xl space-y-6">
          <PageHeader
            title="Upload RFP Documents"
            description="Upload PDF, DOCX, or XLSX files to begin AI-powered analysis"
          />

          {isSuccess ? (
            <SuccessState />
          ) : (
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
              {/* Project name */}
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm">Project Name</CardTitle>
                  <CardDescription className="text-xs">
                    Give this upload batch a descriptive name
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <Input
                    {...register("projectName")}
                    placeholder="e.g. City Infrastructure RFP 2025"
                    className={errors.projectName ? "border-destructive" : ""}
                  />
                  {errors.projectName && (
                    <p className="mt-1.5 text-xs text-destructive">
                      {errors.projectName.message}
                    </p>
                  )}
                </CardContent>
              </Card>

              {/* Drop zone */}
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm">Documents</CardTitle>
                  <CardDescription className="text-xs">
                    Supported formats: PDF, DOCX, XLSX · Max 50 MB per file
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <DropZone />
                </CardContent>
              </Card>

              {/* Upload error */}
              {uploadError && (
                <p className="text-xs text-destructive text-center">
                  {uploadError}
                </p>
              )}

              {/* Submit */}
              <div className="flex items-center justify-between">
                <p className="text-xs text-muted-foreground">
                  {files.length === 0
                    ? "Add at least one file to continue"
                    : `${files.length} file${files.length !== 1 ? "s" : ""} ready to upload`}
                </p>
                <Button type="submit" disabled={!canSubmit} className="gap-2">
                  {isUploading ? (
                    <>
                      <LoadingSpinner size="sm" />
                      Uploading…
                    </>
                  ) : (
                    <>
                      Start Analysis
                      <ArrowRight className="h-4 w-4" />
                    </>
                  )}
                </Button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}

// ─── Success state ────────────────────────────────────────────────────────────

function SuccessState() {
  return (
    <Card className="border-green-500/20 bg-green-500/5">
      <CardContent className="flex flex-col items-center gap-4 py-12 text-center">
        <div className="flex h-14 w-14 items-center justify-center rounded-full bg-green-500/10">
          <CheckCircle2 className="h-7 w-7 text-green-400" />
        </div>
        <div className="space-y-1">
          <p className="text-sm font-semibold text-foreground">
            Upload Successful
          </p>
          <p className="text-xs text-muted-foreground">
            Your documents are queued for processing. Redirecting to
            documents…
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
