import { type LucideIcon } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/utils";

interface StatsCardProps {
  title: string;
  value: string | number;
  change?: string;
  changeType?: "positive" | "negative" | "neutral";
  icon: LucideIcon;
  iconColor?: string;
  description?: string;
}

export function StatsCard({
  title,
  value,
  change,
  changeType = "neutral",
  icon: Icon,
  iconColor = "text-primary",
  description,
}: StatsCardProps) {
  return (
    <Card className="relative overflow-hidden">
      <CardContent className="p-5">
        <div className="flex items-start justify-between">
          <div className="space-y-1">
            <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
              {title}
            </p>
            <p className="text-2xl font-bold text-foreground">{value}</p>
            {description && (
              <p className="text-xs text-muted-foreground">{description}</p>
            )}
          </div>
          <div
            className={cn(
              "flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10",
              iconColor.replace("text-", "bg-").replace("primary", "primary/10")
            )}
          >
            <Icon className={cn("h-4 w-4", iconColor)} />
          </div>
        </div>
        {change && (
          <div className="mt-3 flex items-center gap-1">
            <span
              className={cn(
                "text-xs font-medium",
                changeType === "positive" && "text-green-400",
                changeType === "negative" && "text-red-400",
                changeType === "neutral" && "text-muted-foreground"
              )}
            >
              {change}
            </span>
          </div>
        )}
      </CardContent>
      {/* Subtle gradient accent */}
      <div className="absolute inset-x-0 bottom-0 h-[2px] bg-gradient-to-r from-transparent via-primary/30 to-transparent" />
    </Card>
  );
}
