import { Provider as ReduxProvider } from "react-redux";
import { RouterProvider } from "react-router-dom";
import { TooltipProvider } from "@/components/ui/tooltip";
import { Toaster } from "@/components/ui/toaster";
import { store } from "@/store";
import { router } from "@/routes";

export function AppProviders() {
  return (
    <ReduxProvider store={store}>
      <TooltipProvider delayDuration={300}>
        <RouterProvider router={router} />
        <Toaster />
      </TooltipProvider>
    </ReduxProvider>
  );
}
