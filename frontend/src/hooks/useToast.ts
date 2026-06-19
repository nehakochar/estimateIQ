import { useCallback } from "react";
import { useToast as useRadixToast } from "@/components/ui/use-toast";

export function useToast() {
  const { toast } = useRadixToast();

  const showSuccess = useCallback(
    (message: string, description?: string) => {
      toast({
        title: message,
        description,
        variant: "default",
      });
    },
    [toast]
  );

  const showError = useCallback(
    (message: string, description?: string) => {
      toast({
        title: message,
        description,
        variant: "destructive",
      });
    },
    [toast]
  );

  const showInfo = useCallback(
    (message: string, description?: string) => {
      toast({
        title: message,
        description,
        variant: "default",
      });
    },
    [toast]
  );

  return { showSuccess, showError, showInfo, toast };
}
