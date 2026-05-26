import { useEffect, useRef } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useCreateProjectMutation } from "@/services/projectsApi";

const schema = z.object({
  projectName: z.string().min(1, "Project name is required").max(200),
  clientName:  z.string().max(200).optional(),
});

type FormValues = z.infer<typeof schema>;

interface CreateProjectModalProps {
  open: boolean;
  onClose: () => void;
  /** Called with the new project's UUID after a successful API create. */
  onCreated?: (projectId: string) => void;
}

export function CreateProjectModal({ open, onClose, onCreated }: CreateProjectModalProps) {
  const overlayRef = useRef<HTMLDivElement>(null);
  const [createProject, { isLoading, error }] = useCreateProjectMutation();

  const { register, handleSubmit, reset, formState: { errors } } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { projectName: "", clientName: "" },
  });

  useEffect(() => { if (open) reset(); }, [open, reset]);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => { if (e.key === "Escape" && !isLoading) onClose(); };
    if (open) window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [open, onClose, isLoading]);

  const onSubmit = async (data: FormValues) => {
    try {
      const result = await createProject({
        name: data.projectName,
        client_name: data.clientName || undefined,
      }).unwrap();
      onCreated?.(result.id);
      onClose();
    } catch {
      // error is surfaced via the `error` variable from the mutation hook
    }
  };

  if (!open) return null;

  const apiError =
    error && "message" in error
      ? (error as { message: string }).message
      : error
      ? "Failed to create project. Please try again."
      : null;

  return (
    <div
      ref={overlayRef}
      className="modal-overlay"
      onClick={(e) => { if (e.target === overlayRef.current && !isLoading) onClose(); }}
    >
      <div className="modal-panel">
        {/* Header */}
        <div className="modal-header">
          <h2 className="modal-title">Create New Project</h2>
          <button className="modal-close-btn" onClick={onClose} disabled={isLoading}>✕</button>
        </div>

        {/* Body */}
        <form onSubmit={handleSubmit(onSubmit)}>
          <div className="modal-body">
            {/* API error */}
            {apiError && (
              <div className="form-error" style={{ marginBottom: "0.75rem" }}>
                {apiError}
              </div>
            )}

            {/* Project Name */}
            <div className="form-field">
              <label className="form-label">
                Project Name <span className="form-label-required">*</span>
              </label>
              <input
                {...register("projectName")}
                placeholder="e.g. BOPC ITMP Modernization"
                autoFocus
                disabled={isLoading}
                className={`form-input${errors.projectName ? " error" : ""}`}
              />
              {errors.projectName && (
                <p className="form-error">{errors.projectName.message}</p>
              )}
            </div>

            {/* Client Name */}
            <div className="form-field">
              <label className="form-label">Client / Organization</label>
              <input
                {...register("clientName")}
                placeholder="e.g. Board of Pilot Commissioners"
                disabled={isLoading}
                className="form-input"
              />
            </div>
          </div>

          {/* Footer */}
          <div className="modal-footer">
            <button
              type="button"
              className="btn btn-ghost"
              onClick={onClose}
              disabled={isLoading}
            >
              Cancel
            </button>
            <button type="submit" className="btn btn-primary" disabled={isLoading}>
              {isLoading ? "Creating…" : "Create Project"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
