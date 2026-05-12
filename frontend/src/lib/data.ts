import { differenceInDays, parseISO, format } from "date-fns";

export type ExpirationStatus = "expired" | "expiring-soon" | "ok" | "no-date";

/**
 * Classify a date string (ISO format) relative to today.
 * "expiring-soon" = within 14 days of expiration.
 */
export function classifyExpiration(dateStr: string | null): ExpirationStatus {
  if (!dateStr) return "no-date";
  const date = parseISO(dateStr);
  const days = differenceInDays(date, new Date());
  if (days < 0) return "expired";
  if (days <= 14) return "expiring-soon";
  return "ok";
}

/**
 * Days until a date. Negative if past.
 */
export function daysUntil(dateStr: string | null): number | null {
  if (!dateStr) return null;
  return differenceInDays(parseISO(dateStr), new Date());
}

/**
 * Format an ISO date as "May 8, 2026" or similar.
 */
export function formatDate(dateStr: string | null): string {
  if (!dateStr) return "—";
  return format(parseISO(dateStr), "MMM d, yyyy");
}