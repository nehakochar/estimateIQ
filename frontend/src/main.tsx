import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "@/styles/globals.css";
import "@/styles/components.css";
import { AppProviders } from "@/app/providers";
const rootElement = document.getElementById("root");
if (!rootElement) throw new Error('Root element "root" not found.');

createRoot(rootElement).render(
  <StrictMode>
    <AppProviders />
  </StrictMode>
);
