import { Bell, Menu, Search } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useAppDispatch } from "@/store";
import { toggleMobileSidebar } from "@/store/slices/uiSlice";
import type { BreadcrumbItem } from "@/types";

interface HeaderProps {
  breadcrumbs?: BreadcrumbItem[];
  title?: string;
  actions?: React.ReactNode;
}

export function Header({ breadcrumbs, title, actions }: HeaderProps) {
  const dispatch = useAppDispatch();

  return (
    <header className="flex h-14 shrink-0 items-center gap-4 border-b border-border bg-background/80 px-4 backdrop-blur-sm">
      {/* Mobile menu toggle */}
      <Button
        variant="ghost"
        size="icon"
        className="md:hidden"
        onClick={() => dispatch(toggleMobileSidebar())}
        aria-label="Open menu"
      >
        <Menu className="h-4 w-4" />
      </Button>

      {/* Breadcrumbs / Title */}
      <div className="flex flex-1 items-center gap-2 min-w-0">
        {breadcrumbs && breadcrumbs.length > 0 ? (
          <nav aria-label="Breadcrumb" className="flex items-center gap-1.5 text-sm">
            {breadcrumbs.map((crumb, i) => (
              <span key={i} className="flex items-center gap-1.5">
                {i > 0 && (
                  <span className="text-muted-foreground/40">/</span>
                )}
                <span
                  className={
                    i === breadcrumbs.length - 1
                      ? "font-medium text-foreground truncate"
                      : "text-muted-foreground hover:text-foreground transition-colors cursor-pointer"
                  }
                >
                  {crumb.label}
                </span>
              </span>
            ))}
          </nav>
        ) : title ? (
          <h1 className="text-sm font-semibold text-foreground truncate">{title}</h1>
        ) : null}
      </div>

      {/* Global search */}
      <div className="hidden md:flex items-center">
        <div className="relative">
          <Search className="absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search..."
            className="h-8 w-48 pl-8 text-xs bg-secondary/50 border-border/50 focus:w-64 transition-all duration-200"
          />
        </div>
      </div>

      {/* Notifications */}
      <Button variant="ghost" size="icon" className="relative" aria-label="Notifications">
        <Bell className="h-4 w-4" />
        <span className="absolute right-1.5 top-1.5 h-1.5 w-1.5 rounded-full bg-primary" />
      </Button>

      {/* Page-level actions */}
      {actions && <div className="flex items-center gap-2">{actions}</div>}

      {/* User avatar */}
      <button
        className="flex h-7 w-7 items-center justify-center rounded-full bg-gradient-to-br from-blue-500 to-cyan-500 text-xs font-semibold text-white shrink-0"
        aria-label="User menu"
      >
        U
      </button>
    </header>
  );
}
