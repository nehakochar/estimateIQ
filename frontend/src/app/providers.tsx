import { Provider as ReduxProvider } from "react-redux";
import { RouterProvider } from "react-router-dom";
import { TooltipProvider } from "@/components/ui/tooltip";
import { store } from "@/store";
import { router } from "@/routes";

export function AppProviders() {
  return (
    <ReduxProvider store={store}>
      <TooltipProvider delayDuration={300}>
        <RouterProvider router={router} />
      </TooltipProvider>
    </ReduxProvider>
  );
}
