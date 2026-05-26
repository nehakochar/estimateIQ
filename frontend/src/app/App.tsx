import { Outlet } from "react-router-dom";

/**
 * Root layout — just renders child routes.
 * The topbar for the hub is rendered inside DiscoveryPage.
 * The topbar for the workspace is rendered inside WorkspaceShell.
 */
export function App() {
  return <Outlet />;
}
