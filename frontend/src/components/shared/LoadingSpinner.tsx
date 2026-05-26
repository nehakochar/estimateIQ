import { cn } from "@/utils";

interface LoadingSpinnerProps {
  size?: "sm" | "md" | "lg";
  className?: string;
}

const sizeMap = {
  sm: "h-4 w-4 border-2",
  md: "h-6 w-6 border-2",
  lg: "h-10 w-10 border-[3px]",
};

export function LoadingSpinner({ size = "md", className }: LoadingSpinnerProps) {
  return (
    <div
      role="status"
      aria-label="Loading"
      className={cn(
        "animate-spin rounded-full border-border border-t-primary",
        sizeMap[size],
        className
      )}
    />
  );
}

export function FullPageLoader() {
  return (
    <div className="flex h-full w-full items-center justify-center">
      <LoadingSpinner size="lg" />
    </div>
  );
}
