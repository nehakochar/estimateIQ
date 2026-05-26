import { useState, useCallback } from "react";
import { useAppDispatch, useAppSelector } from "@/store";
import { uploadDocuments } from "@/store/slices/uploadSlice";

export function UploadPanel() {
  const dispatch = useAppDispatch();
  const { isUploading } = useAppSelector((s) => s.upload);
  const [isDragging, setIsDragging] = useState(false);
  const [files, setFiles] = useState<File[]>([]);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    setFiles((prev) => [...prev, ...Array.from(e.dataTransfer.files)]);
  }, []);

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) setFiles((prev) => [...prev, ...Array.from(e.target.files!)]);
  };

  const handleUpload = () => {
    if (!files.length) return;
    dispatch(uploadDocuments({ projectName: "RFP Upload", files }));
  };

  return (
    <div>
      <div className="section-hdr">
        <h2>RFP Source Ingestion Portal</h2>
      </div>

      <label>
        <div
          className={`upload-zone${isDragging ? " dragging" : ""}`}
          onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
          onDragLeave={() => setIsDragging(false)}
          onDrop={handleDrop}
        >
          <div className="upload-icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#6c63ff" strokeWidth="2">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
              <polyline points="17 8 12 3 7 8"/>
              <line x1="12" y1="3" x2="12" y2="15"/>
            </svg>
          </div>
          <div className="upload-title">Drop project documentation or RFP payload here</div>
          <div className="upload-sub">
            Supports system engineering spreadsheets, structural specifications, PDFs and markdown exports
          </div>

          {files.length > 0 && (
            <div className="upload-file-list">
              {files.map((f, i) => (
                <div key={i} className="upload-file-item">✓ {f.name}</div>
              ))}
            </div>
          )}

          <input
            type="file"
            multiple
            accept=".pdf,.docx,.xlsx"
            className="sr-only"
            onChange={handleFileInput}
          />
        </div>
      </label>

      {files.length > 0 && (
        <div className="upload-actions">
          <button className="btn btn-primary" onClick={handleUpload} disabled={isUploading}>
            {isUploading ? "Uploading…" : `Upload ${files.length} file${files.length !== 1 ? "s" : ""}`}
          </button>
          <button className="btn btn-ghost" onClick={() => setFiles([])}>Clear</button>
        </div>
      )}
    </div>
  );
}
