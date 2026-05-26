import { Outlet } from "react-router-dom";
import { Sidebar } from "./Sidebar";
import { useAppDispatch, useAppSelector } from "@/store";
import { setMobileSidebarOpen } from "@/store/slices/uiSlice";
import { cn } from "@/utils";

export function AppShell() {
  const dispatch = useAppDispatch();
  const mobileOpen = useAppSelector((s) => s.ui.sidebarMobileOpen);

  return (
    <div className="flex h-screen w-full overflow-hidden bg-background">
      {/* Mobile overlay */}
      {mobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/60 md:hidden"
          onClick={() => dispatch(setMobileSidebarOpen(false))}
          aria-hidden="true"
        />
      )}

      {/* Sidebar — desktop always visible, mobile slide-in */}
      <div
        className={cn(
          "fixed inset-y-0 left-0 z-50 md:relative md:z-auto md:flex",
          mobileOpen ? "flex" : "hidden md:flex"
        )}
      >
        <Sidebar />
      </div>

      {/* Main content area */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Page content rendered by nested routes */}
        <main className="flex-1 overflow-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
