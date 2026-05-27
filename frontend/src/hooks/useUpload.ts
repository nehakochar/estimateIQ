import { useAppDispatch, useAppSelector } from "@/store";
import { uploadDocuments } from "@/store/slices/uploadSlice";
import type { UploadPayload } from "@/store/slices/uploadSlice";

/**
 * Convenience hook that wraps the uploadDocuments async thunk.
 * isSuccess is read from Redux state (set in fulfilled case) — not derived —
 * so it's stable across re-renders and won't flicker.
 */
export function useUpload() {
  const dispatch = useAppDispatch();
  const { isUploading, isSuccess, uploadError, currentProjectId, uploadedFiles } =
    useAppSelector((s) => s.upload);

  const upload = (payload: UploadPayload) =>
    dispatch(uploadDocuments(payload));

  return {
    upload,
    isUploading,
    isSuccess,
    uploadError,
    currentProjectId,
    uploadedFiles,
  };
}
