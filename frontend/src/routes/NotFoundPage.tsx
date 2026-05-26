import { Link } from "react-router-dom";
import { ArrowLeft, Zap } from "lucide-react";
import { Button } from "@/components/ui/button";

export function NotFoundPage() {
  return (
    <div className="flex h-screen w-full flex-col items-center justify-center gap-6 bg-background text-center">
      <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-primary/10">
        <Zap className="h-8 w-8 text-primary" />
      </div>
      <div className="space-y-2">
        <h1 className="text-4xl font-bold text-foreground">404</h1>
        <p className="text-sm text-muted-foreground">
          This page doesn't exist or was moved.
        </p>
      </div>
      <Button asChild>
        <Link to="/">
          <ArrowLeft className="h-4 w-4" />
          Back to Dashboard
        </Link>
      </Button>
    </div>
  );
}
