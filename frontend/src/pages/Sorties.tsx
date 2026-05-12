import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { format, parseISO } from "date-fns";
import { fetchSorties } from "../lib/api";
import Loading from "../components/Loading";
import Badge from "../components/Badge";

type DateRange = "7d" | "30d" | "90d" | "all";

const DATE_RANGES: { value: DateRange; label: string; days: number | null }[] = [
  { value: "7d",  label: "7d",  days: 7 },
  { value: "30d", label: "30d", days: 30 },
  { value: "90d", label: "90d", days: 90 },
  { value: "all", label: "All", days: null },
];

function localDateStr(d = new Date()): string {
  return [
    d.getFullYear(),
    String(d.getMonth() + 1).padStart(2, "0"),
    String(d.getDate()).padStart(2, "0"),
  ].join("-");
}

function toDateParam(days: number | null): string | undefined {
  if (days === null) return undefined;
  const d = new Date();
  d.setDate(d.getDate() - days);
  return localDateStr(d);
}

function formatTakeoff(str: string | null): string {
  if (!str) return "—";
  return format(parseISO(str), "MMM d, HH:mm");
}

export default function Sorties() {
  const [dateRange, setDateRange] = useState<DateRange>("30d");

  const rangeDays = DATE_RANGES.find((r) => r.value === dateRange)!.days;
  const dateFrom = toDateParam(rangeDays);

  const { data, isLoading, error } = useQuery({
    queryKey: ["sorties", dateRange],
    queryFn: () =>
      fetchSorties(dateFrom ? { date_from: dateFrom, date_to: localDateStr() } : undefined),
  });

  if (isLoading) return <Loading message="Loading sorties..." />;
  if (error || !data) {
    return (
      <div className="card border-red-600/50 bg-red-950/20 text-red-300">
        Failed to load sorties. Is the backend running on port 8001?
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div>
        <h1>Sorties</h1>
        <p className="text-sm text-slate-400 mt-1">{data.length} flights</p>
      </div>

      <div className="flex gap-1 bg-slate-900 border border-slate-800 rounded-md p-1 w-fit">
        {DATE_RANGES.map((r) => (
          <button
            key={r.value}
            onClick={() => setDateRange(r.value)}
            className={
              dateRange === r.value
                ? "px-3 py-1 text-xs rounded bg-slate-800 text-white"
                : "px-3 py-1 text-xs rounded text-slate-400 hover:text-slate-200"
            }
          >
            {r.label}
          </button>
        ))}
      </div>

      <div className="card p-0 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-slate-900/60 text-xs uppercase tracking-wide text-slate-400">
            <tr>
              <th className="text-left px-4 py-2 font-medium">Date</th>
              <th className="text-left px-4 py-2 font-medium">Event Type</th>
              <th className="text-left px-4 py-2 font-medium">Event Code</th>
              <th className="text-left px-4 py-2 font-medium">Aircraft</th>
              <th className="text-left px-4 py-2 font-medium">Duration</th>
              <th className="text-left px-4 py-2 font-medium">Status</th>
            </tr>
          </thead>
          <tbody>
            {data.map((s) => (
              <tr
                key={s.id}
                className="border-t border-slate-800 hover:bg-slate-900/40 transition-colors"
              >
                <td className="px-4 py-2.5">
                  <Link
                    to={`/sorties/${s.id}`}
                    className="font-medium text-slate-100 hover:text-blue-400"
                  >
                    {formatTakeoff(s.takeoff_time)}
                  </Link>
                </td>
                <td className="px-4 py-2.5 text-slate-300">{s.event_type ?? "—"}</td>
                <td className="px-4 py-2.5 text-slate-300">{s.event_code ?? "—"}</td>
                <td className="px-4 py-2.5 text-slate-300">
                  {s.aircraft_side_number ?? "—"}
                </td>
                <td className="px-4 py-2.5 text-slate-300">
                  {s.duration_hours != null ? s.duration_hours.toFixed(1) : "—"}
                </td>
                <td className="px-4 py-2.5">
                  <Badge variant={s.is_complete ? "success" : "info"}>
                    {s.is_complete ? "Complete" : "Scheduled"}
                  </Badge>
                </td>
              </tr>
            ))}
            {data.length === 0 && (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-slate-500">
                  No sorties in this period.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
