import { useAppDispatch, useAppSelector } from "@/store";
import { uploadDocuments } from "@/store/slices/uploadSlice";
import type { UploadPayload } from "@/store/slices/uploadSlice";

/**
 * Convenience hook that wraps the uploadDocuments async thunk.
 * Returns the dispatch-bound upload function plus relevant state.
 */
export function useUpload() {
  const dispatch = useAppDispatch();
  const { isUploading, uploadError, currentProjectId, uploadedDocuments } =
    useAppSelector((s) => s.upload);

  const upload = (payload: UploadPayload) =>
    dispatch(uploadDocuments(payload));

  return {
    upload,
    isUploading,
    uploadError,
    currentProjectId,
    uploadedDocuments,
    isSuccess: !isUploading && currentProjectId !== null && uploadError === null,
  };
}
