import { NavLink, useLocation } from "react-router-dom";
import {
  LayoutDashboard,
  Upload,
  FileText,
  ListChecks,
  Calculator,
  CalendarDays,
  Search,
  Settings,
  ChevronLeft,
  Zap,
} from "lucide-react";
import { cn } from "@/utils";
import { useAppDispatch, useAppSelector } from "@/store";
import { toggleSidebar } from "@/store/slices/uiSlice";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { Separator } from "@/components/ui/separator";

// ─── Nav config ───────────────────────────────────────────────────────────────

const primaryNav = [
  { label: "Dashboard", href: "/", icon: LayoutDashboard },
  { label: "Upload RFP", href: "/upload", icon: Upload },
  { label: "Documents", href: "/documents", icon: FileText },
  { label: "Requirements", href: "/requirements", icon: ListChecks },
  { label: "Estimates", href: "/estimates", icon: Calculator },
  { label: "Timeline", href: "/timeline", icon: CalendarDays },
  { label: "Search", href: "/search", icon: Search },
];

const secondaryNav = [
  { label: "Settings", href: "/settings", icon: Settings },
];

// ─── Component ────────────────────────────────────────────────────────────────

export function Sidebar() {
  const dispatch = useAppDispatch();
  const collapsed = useAppSelector((s) => s.ui.sidebarCollapsed);
  const location = useLocation();

  const isActive = (href: string) =>
    href === "/" ? location.pathname === "/" : location.pathname.startsWith(href);

  return (
    <aside
      className={cn(
        "relative flex h-full flex-col border-r border-sidebar-border bg-sidebar transition-all duration-300 ease-in-out",
        collapsed ? "w-[60px]" : "w-[220px]"
      )}
    >
      {/* Logo */}
      <div
        className={cn(
          "flex h-14 items-center border-b border-sidebar-border px-3",
          collapsed ? "justify-center" : "justify-between"
        )}
      >
        {!collapsed && (
          <div className="flex items-center gap-2">
            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-primary">
              <Zap className="h-4 w-4 text-white" />
            </div>
            <span className="text-sm font-semibold tracking-tight text-sidebar-foreground">
              EstimateIQ
            </span>
          </div>
        )}
        {collapsed && (
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-primary">
            <Zap className="h-4 w-4 text-white" />
          </div>
        )}
        {!collapsed && (
          <button
            onClick={() => dispatch(toggleSidebar())}
            className="rounded-md p-1 text-sidebar-foreground/50 hover:bg-sidebar-accent hover:text-sidebar-foreground transition-colors"
            aria-label="Collapse sidebar"
          >
            <ChevronLeft className="h-4 w-4" />
          </button>
        )}
      </div>

      {/* Navigation */}
      <ScrollArea className="flex-1 py-3">
        <nav className="flex flex-col gap-0.5 px-2">
          {primaryNav.map((item) => (
            <NavItem
              key={item.href}
              {...item}
              collapsed={collapsed}
              active={isActive(item.href)}
            />
          ))}
        </nav>

        <Separator className="my-3 mx-2 w-auto" />

        <nav className="flex flex-col gap-0.5 px-2">
          {secondaryNav.map((item) => (
            <NavItem
              key={item.href}
              {...item}
              collapsed={collapsed}
              active={isActive(item.href)}
            />
          ))}
        </nav>
      </ScrollArea>

      {/* Expand button when collapsed */}
      {collapsed && (
        <div className="border-t border-sidebar-border p-2">
          <button
            onClick={() => dispatch(toggleSidebar())}
            className="flex w-full items-center justify-center rounded-md p-2 text-sidebar-foreground/50 hover:bg-sidebar-accent hover:text-sidebar-foreground transition-colors"
            aria-label="Expand sidebar"
          >
            <ChevronLeft className="h-4 w-4 rotate-180" />
          </button>
        </div>
      )}
    </aside>
  );
}

// ─── NavItem ──────────────────────────────────────────────────────────────────

interface NavItemProps {
  label: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  collapsed: boolean;
  active: boolean;
  badge?: string | number;
}

function NavItem({ label, href, icon: Icon, collapsed, active, badge }: NavItemProps) {
  const content = (
    <NavLink
      to={href}
      className={cn(
        "flex items-center gap-3 rounded-md px-2 py-2 text-sm font-medium transition-colors",
        active
          ? "bg-sidebar-accent text-sidebar-primary"
          : "text-sidebar-foreground/70 hover:bg-sidebar-accent hover:text-sidebar-foreground",
        collapsed && "justify-center px-2"
      )}
    >
      <Icon className={cn("h-4 w-4 shrink-0", active && "text-sidebar-primary")} />
      {!collapsed && (
        <>
          <span className="flex-1 truncate">{label}</span>
          {badge !== undefined && (
            <span className="ml-auto flex h-5 min-w-5 items-center justify-center rounded-full bg-primary/20 px-1.5 text-[10px] font-semibold text-primary">
              {badge}
            </span>
          )}
        </>
      )}
    </NavLink>
  );

  if (collapsed) {
    return (
      <Tooltip>
        <TooltipTrigger asChild>{content}</TooltipTrigger>
        <TooltipContent side="right">{label}</TooltipContent>
      </Tooltip>
    );
  }

  return content;
}
