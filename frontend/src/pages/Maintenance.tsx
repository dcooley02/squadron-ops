import { useQuery, useQueries } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { AlertTriangle } from "lucide-react";
import { fetchAircraft, fetchAircraftDetail, type AircraftDetail, type AircraftStatus } from "../lib/api";
import Loading from "../components/Loading";
import Badge from "../components/Badge";

const STATUS_VARIANT: Record<AircraftStatus, "success" | "warning" | "danger" | "neutral"> = {
  FMC: "success",
  PMC: "warning",
  NMC: "danger",
  NMCM: "danger",
  NMCS: "danger",
};

function isNmc(s: AircraftStatus) {
  return s === "NMC" || s === "NMCM" || s === "NMCS";
}

export default function Maintenance() {
  const { data: aircraftList, isLoading: listLoading } = useQuery({
    queryKey: ["aircraft"],
    queryFn: () => fetchAircraft(),
  });

  const detailQueries = useQueries({
    queries: (aircraftList ?? []).map((ac) => ({
      queryKey: ["aircraft-detail", ac.id],
      queryFn: () => fetchAircraftDetail(ac.id),
      enabled: !!aircraftList,
    })),
  });

  const allLoading = listLoading || detailQueries.some((q) => q.isLoading);
  if (allLoading) return <Loading />;

  const details: AircraftDetail[] = detailQueries
    .map((q) => q.data)
    .filter(Boolean) as AircraftDetail[];

  const fmcCount = details.filter((a) => a.computed_status === "FMC").length;
  const pmcCount = details.filter((a) => a.computed_status === "PMC").length;
  const nmcCount = details.filter((a) => isNmc(a.computed_status)).length;

  const driftingAircraft = details.filter((a) => a.status !== a.computed_status);

  return (
    <div className="space-y-5">
      <h1>Maintenance</h1>

      {/* A — Stat strip (computed_status) */}
      <div className="grid grid-cols-3 gap-4">
        <StatCard label="FMC" value={fmcCount} variant="success" />
        <StatCard label="PMC" value={pmcCount} variant="warning" />
        <StatCard label="NMC" value={nmcCount} variant="danger" />
      </div>

      {/* B — Status drift alert */}
      {driftingAircraft.length > 0 && (
        <div className="card border-yellow-700/40 bg-yellow-950/20 space-y-2">
          <div className="flex items-center gap-2 text-yellow-400 font-medium text-sm">
            <AlertTriangle size={16} />
            {driftingAircraft.length} aircraft with status drift — stamped status doesn't match
            computed reality
          </div>
          <div className="space-y-1">
            {driftingAircraft.map((ac) => {
              return (
                <div key={ac.id} className="text-xs text-yellow-300/80 flex items-center gap-2">
                  <span className="font-mono">{ac.side_number ?? ac.bureau_number}</span>
                  <span className="text-slate-500">·</span>
                  <span>
                    stamped <Badge variant={STATUS_VARIANT[ac.status]}>{ac.status}</Badge>
                  </span>
                  <span className="text-slate-500">→ computed</span>
                  <Badge variant={STATUS_VARIANT[ac.computed_status]}>{ac.computed_status}</Badge>
                  {ac.open_discrepancies.length > 0 && (
                    <span className="text-slate-400">
                      ({ac.open_discrepancies.filter((d) => d.severity === "DOWNING").length} DOWNING,{" "}
                      {ac.open_discrepancies.length} open total)
                    </span>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* C — Aircraft grid */}
      <div>
        <h2 className="mb-3">Aircraft Status</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4">
          {details.map((ac) => (
            <AircraftCard key={ac.id} ac={ac} />
          ))}
        </div>
      </div>

      {/* D — Phase forecast */}
      <div className="card">
        <h2 className="mb-3">Phase Forecast</h2>
        <div className="space-y-3">
          {details
            .map((ac) => ({ ac, hoursRemaining: ac.phase_interval - ac.hours_since_phase }))
            .sort((a, b) => a.hoursRemaining - b.hoursRemaining)
            .map(({ ac, hoursRemaining }) => (
              <PhaseBar key={ac.id} ac={ac} hoursRemaining={hoursRemaining} />
            ))}
        </div>
      </div>
    </div>
  );
}

// ── Sub-components ─────────────────────────────────────────────────────────

function StatCard({
  label,
  value,
  variant,
}: {
  label: string;
  value: number;
  variant: "success" | "warning" | "danger";
}) {
  const colors = { success: "text-green-400", warning: "text-yellow-400", danger: "text-red-400" };
  return (
    <div className="card text-center">
      <div className={`text-3xl font-bold ${colors[variant]}`}>{value}</div>
      <div className="text-xs text-slate-500 uppercase tracking-wide mt-1">{label}</div>
      <div className="text-xs text-slate-600 mt-0.5">computed</div>
    </div>
  );
}

function AircraftCard({ ac }: { ac: AircraftDetail }) {
  const drift = ac.status !== ac.computed_status;
  const openDowning = ac.open_discrepancies.filter((d) => d.severity === "DOWNING").length;
  const openMajor = ac.open_discrepancies.filter((d) => d.severity === "MAJOR").length;
  const openMinor = ac.open_discrepancies.filter((d) => d.severity === "MINOR").length;

  return (
    <Link
      to={`/maintenance/${ac.id}`}
      className={`card block hover:border-slate-600 transition-colors ${
        drift ? "border-yellow-700/50 bg-yellow-950/10" : ""
      }`}
    >
      <div className="flex items-start justify-between gap-2">
        <div>
          <div className="font-semibold text-slate-100">
            {ac.side_number ?? ac.bureau_number}
          </div>
          <div className="text-xs text-slate-500 font-mono">{ac.bureau_number}</div>
        </div>
        <div className="flex flex-col items-end gap-1">
          <div className="flex items-center gap-1.5">
            <span className="text-xs text-slate-500">computed</span>
            <Badge variant={STATUS_VARIANT[ac.computed_status]}>{ac.computed_status}</Badge>
          </div>
          {drift && (
            <div className="flex items-center gap-1.5">
              <span className="text-xs text-slate-500">stamped</span>
              <Badge variant={STATUS_VARIANT[ac.status]}>{ac.status}</Badge>
            </div>
          )}
        </div>
      </div>

      <div className="grid grid-cols-3 gap-2 mt-3 pt-3 border-t border-slate-800 text-center">
        <div>
          <div className="text-xs text-slate-500">Total hrs</div>
          <div className="text-sm font-medium">{ac.total_airframe_hours.toFixed(0)}</div>
        </div>
        <div>
          <div className="text-xs text-slate-500">Since phase</div>
          <div className="text-sm font-medium">{ac.hours_since_phase.toFixed(0)}</div>
        </div>
        <div>
          <div className="text-xs text-slate-500">To phase</div>
          <div
            className={`text-sm font-medium ${ac.hours_to_phase < 50 ? "text-yellow-400" : ""}`}
          >
            {ac.hours_to_phase.toFixed(0)}
          </div>
        </div>
      </div>

      {ac.open_discrepancies.length > 0 && (
        <div className="mt-2 flex items-center gap-2 text-xs">
          <span className="text-slate-500">{ac.open_discrepancies.length} open discrep.</span>
          {openDowning > 0 && (
            <Badge variant="danger">{openDowning} DOWNING</Badge>
          )}
          {openMajor > 0 && (
            <Badge variant="warning">{openMajor} MAJOR</Badge>
          )}
          {openMinor > 0 && (
            <Badge variant="neutral" className="text-amber-400 border-amber-700/40 bg-amber-950/20">{openMinor} MINOR</Badge>
          )}
        </div>
      )}

      {drift && (
        <div className="mt-2 text-xs text-yellow-400 flex items-center gap-1">
          <AlertTriangle size={11} />
          Status drift
        </div>
      )}
    </Link>
  );
}

function PhaseBar({
  ac,
  hoursRemaining,
}: {
  ac: AircraftDetail;
  hoursRemaining: number;
}) {
  const pct = Math.min(100, (ac.hours_since_phase / ac.phase_interval) * 100);
  const barColor = pct >= 90 ? "bg-red-500" : pct >= 75 ? "bg-yellow-500" : "bg-green-500";

  return (
    <div>
      <div className="flex items-center justify-between mb-1">
        <Link
          to={`/maintenance/${ac.id}`}
          className="text-sm font-medium hover:text-blue-400 transition-colors"
        >
          {ac.side_number ?? ac.bureau_number}
        </Link>
        <span className="text-xs text-slate-500">
          {ac.hours_since_phase.toFixed(1)} / {ac.phase_interval.toFixed(0)}h
          {" · "}
          <span className={hoursRemaining < 50 ? "text-yellow-400" : "text-slate-400"}>
            {hoursRemaining.toFixed(0)}h remaining
          </span>
        </span>
      </div>
      <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
        <div className={`h-full rounded-full transition-all ${barColor}`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}
