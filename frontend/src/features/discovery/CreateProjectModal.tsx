import { useEffect, useRef } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";

const schema = z.object({
  projectName: z.string().min(1, "Project name is required").max(100),
  clientName:  z.string().max(100).optional(),
});

type FormValues = z.infer<typeof schema>;

interface CreateProjectModalProps {
  open: boolean;
  onClose: () => void;
  onCreate: (data: FormValues) => void;
}

export function CreateProjectModal({ open, onClose, onCreate }: CreateProjectModalProps) {
  const overlayRef = useRef<HTMLDivElement>(null);

  const { register, handleSubmit, reset, formState: { errors } } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { projectName: "", clientName: "" },
  });

  useEffect(() => { if (open) reset(); }, [open, reset]);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
    if (open) window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [open, onClose]);

  const onSubmit = (data: FormValues) => { onCreate(data); onClose(); };

  if (!open) return null;

  return (
    <div
      ref={overlayRef}
      className="modal-overlay"
      onClick={(e) => { if (e.target === overlayRef.current) onClose(); }}
    >
      <div className="modal-panel">
        {/* Header */}
        <div className="modal-header">
          <h2 className="modal-title">Create New Project</h2>
          <button className="modal-close-btn" onClick={onClose}>✕</button>
        </div>

        {/* Body */}
        <form onSubmit={handleSubmit(onSubmit)}>
          <div className="modal-body">
            {/* Project Name */}
            <div className="form-field">
              <label className="form-label">
                Project Name <span className="form-label-required">*</span>
              </label>
              <input
                {...register("projectName")}
                placeholder="e.g. BOPC ITMP Modernization"
                autoFocus
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
                className="form-input"
              />
            </div>
          </div>

          {/* Footer */}
          <div className="modal-footer">
            <button type="button" className="btn btn-ghost" onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary">
              Create Project
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
