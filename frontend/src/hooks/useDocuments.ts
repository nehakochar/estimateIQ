/**
 * Re-export RTK Query hooks for documents so feature code imports from
 * a single @/hooks path rather than directly from the API slice.
 */
export {
  useListDocumentsQuery,
  useGetDocumentQuery,
  useDeleteDocumentMutation,
} from "@/services/documentsApi";
