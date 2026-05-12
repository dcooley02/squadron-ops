import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { fetchAircraft, type AircraftStatus, type AircraftSummary } from "../lib/api";
import Loading from "../components/Loading";
import Badge from "../components/Badge";

type StatusFilter = "all" | "FMC" | "PMC" | "NMC";

const STATUS_FILTERS: { value: StatusFilter; label: string }[] = [
  { value: "all", label: "All" },
  { value: "FMC", label: "FMC" },
  { value: "PMC", label: "PMC" },
  { value: "NMC", label: "NMC" },
];

const STATUS_BADGE_VARIANT: Record<AircraftStatus, "success" | "warning" | "danger"> = {
  FMC: "success",
  PMC: "warning",
  NMC: "danger",
  NMCM: "danger",
  NMCS: "danger",
};

export default function Aircraft() {
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");

  const { data, isLoading, error } = useQuery({
    queryKey: ["aircraft"],
    queryFn: () => fetchAircraft(),
  });

  if (isLoading) return <Loading message="Loading aircraft..." />;
  if (error || !data) {
    return (
      <div className="card border-red-600/50 bg-red-950/20 text-red-300">
        Failed to load aircraft data. Is the backend running on port 8001?
      </div>
    );
  }

  const displayed =
    statusFilter === "all"
      ? data
      : statusFilter === "NMC"
      ? data.filter((ac) => ac.status === "NMC" || ac.status === "NMCM" || ac.status === "NMCS")
      : data.filter((ac) => ac.status === statusFilter);

  return (
    <div className="space-y-4">
      <div>
        <h1>Aircraft</h1>
        <p className="text-sm text-slate-400 mt-1">{data.length} MH-60S airframes</p>
      </div>

      <div className="flex gap-1 bg-slate-900 border border-slate-800 rounded-md p-1 w-fit">
        {STATUS_FILTERS.map((f) => (
          <button
            key={f.value}
            onClick={() => setStatusFilter(f.value)}
            className={
              statusFilter === f.value
                ? "px-3 py-1 text-xs rounded bg-slate-800 text-white"
                : "px-3 py-1 text-xs rounded text-slate-400 hover:text-slate-200"
            }
          >
            {f.label}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {displayed.map((ac) => (
          <AircraftCard key={ac.id} aircraft={ac} />
        ))}
        {displayed.length === 0 && (
          <p className="col-span-full py-4 text-sm text-slate-500">
            No aircraft match this filter.
          </p>
        )}
      </div>
    </div>
  );
}

function AircraftCard({ aircraft: ac }: { aircraft: AircraftSummary }) {
  const toPhase = ac.phase_interval - ac.hours_since_phase;

  return (
    <Link
      to={`/aircraft/${ac.id}`}
      className="card block hover:border-slate-600 transition-colors"
    >
      <div className="flex items-start justify-between mb-2">
        <div className="text-3xl font-bold text-slate-100">{ac.side_number ?? "—"}</div>
        <Badge variant={STATUS_BADGE_VARIANT[ac.status]}>{ac.status}</Badge>
      </div>

      <div className="text-xs text-slate-500 mb-4">{ac.bureau_number}</div>

      <div className="grid grid-cols-3 gap-3 text-xs">
        <div>
          <div className="text-slate-500 mb-0.5">Total Hrs</div>
          <div className="font-semibold text-slate-200">
            {ac.total_airframe_hours.toFixed(1)}
          </div>
        </div>
        <div>
          <div className="text-slate-500 mb-0.5">Since Phase</div>
          <div className="font-semibold text-slate-200">
            {ac.hours_since_phase.toFixed(1)}
          </div>
        </div>
        <div>
          <div className="text-slate-500 mb-0.5">To Phase</div>
          <div
            className={`font-semibold ${toPhase < 50 ? "text-yellow-400" : "text-slate-200"}`}
          >
            {toPhase.toFixed(1)}
          </div>
        </div>
      </div>

      {toPhase < 50 && (
        <div className="mt-3">
          <Badge variant="warning">Phase approaching</Badge>
        </div>
      )}
    </Link>
  );
}
