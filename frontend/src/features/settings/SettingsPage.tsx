import { Settings } from "lucide-react";
import { Header } from "@/components/layout/Header";
import { PageHeader } from "@/components/shared/PageHeader";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";

export function SettingsPage() {
  return (
    <div className="flex h-full flex-col">
      <Header breadcrumbs={[{ label: "Dashboard", href: "/" }, { label: "Settings" }]} />
      <div className="flex-1 overflow-auto p-6 animate-fade-in">
        <div className="mx-auto max-w-2xl space-y-6">
          <PageHeader
            title="Settings"
            description="Configure your EstimateIQ workspace"
          />
          <Card>
            <CardHeader>
              <CardTitle className="text-sm flex items-center gap-2">
                <Settings className="h-4 w-4" />
                Application Settings
              </CardTitle>
              <CardDescription className="text-xs">
                Settings and configuration options will appear here in future releases.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3 text-sm text-muted-foreground">
                <div className="flex items-center justify-between py-2 border-b border-border">
                  <span>API Endpoint</span>
                  <code className="text-xs bg-muted px-2 py-0.5 rounded font-mono">
                    {import.meta.env.VITE_API_BASE_URL}
                  </code>
                </div>
                <div className="flex items-center justify-between py-2 border-b border-border">
                  <span>App Version</span>
                  <code className="text-xs bg-muted px-2 py-0.5 rounded font-mono">
                    {import.meta.env.VITE_APP_VERSION}
                  </code>
                </div>
                <div className="flex items-center justify-between py-2">
                  <span>Environment</span>
                  <code className="text-xs bg-muted px-2 py-0.5 rounded font-mono">
                    {import.meta.env.VITE_ENVIRONMENT}
                  </code>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
