import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * Merges Tailwind CSS classes with clsx, resolving conflicts intelligently.
 * This is the standard shadcn/ui utility.
 */
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}
