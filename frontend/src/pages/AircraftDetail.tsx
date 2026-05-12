import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import {
  fetchAircraftDetail,
  type AircraftStatus,
  type DiscrepancySeverity,
  type DiscrepancyWorkStatus,
} from "../lib/api";
import Loading from "../components/Loading";
import Badge from "../components/Badge";
import { formatDate } from "../lib/dates";

const STATUS_BADGE_VARIANT: Record<AircraftStatus, "success" | "warning" | "danger"> = {
  FMC: "success",
  PMC: "warning",
  NMC: "danger",
  NMCM: "danger",
  NMCS: "danger",
};

const SEV_VARIANT: Record<DiscrepancySeverity, "neutral" | "warning" | "danger"> = {
  MINOR: "neutral",
  MAJOR: "warning",
  DOWNING: "danger",
};

const WS_VARIANT: Record<DiscrepancyWorkStatus, "neutral" | "warning" | "danger" | "success" | "info"> = {
  OPEN: "danger",
  IN_WORK: "info",
  AWP: "warning",
  AWM: "warning",
  COMPLETED: "success",
  CLOSED: "neutral",
};

const WS_LABEL: Record<DiscrepancyWorkStatus, string> = {
  OPEN: "Open",
  IN_WORK: "In Work",
  AWP: "AWP",
  AWM: "AWM",
  COMPLETED: "Completed",
  CLOSED: "Closed",
};

export default function AircraftDetail() {
  const { id } = useParams<{ id: string }>();
  const aircraftId = Number(id);

  const { data, isLoading, error } = useQuery({
    queryKey: ["aircraft-detail", aircraftId],
    queryFn: () => fetchAircraftDetail(aircraftId),
    enabled: !isNaN(aircraftId),
  });

  if (isLoading) return <Loading />;
  if (error || !data) {
    return (
      <div className="card border-red-600/50 bg-red-950/20 text-red-300">
        Aircraft not found.
      </div>
    );
  }

  const statusDrift = data.status !== data.computed_status;

  return (
    <div className="space-y-5">
      <Link
        to="/aircraft"
        className="inline-flex items-center gap-1 text-sm text-slate-400 hover:text-slate-200"
      >
        <ArrowLeft size={14} /> Back to aircraft
      </Link>

      {/* Header card */}
      <div className="card">
        <div className="flex items-start justify-between flex-wrap gap-3">
          <div>
            <h1 className="flex items-center gap-3 flex-wrap">
              {data.side_number ?? "—"}
              <Badge variant={STATUS_BADGE_VARIANT[data.computed_status]}>
                {data.computed_status}
              </Badge>
              {statusDrift && (
                <span className="text-sm font-normal text-yellow-400">
                  (stamped: {data.status})
                </span>
              )}
            </h1>
            <div className="text-sm text-slate-400 mt-1">
              {data.bureau_number} · {data.type_model_series}
            </div>
          </div>
          <Link
            to={`/maintenance/${data.id}`}
            className="text-xs text-slate-400 hover:text-slate-200 transition-colors"
          >
            Full maintenance view →
          </Link>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-4 pt-4 border-t border-slate-800">
          <div>
            <div className="text-xs text-slate-500 uppercase tracking-wide">Total Hours</div>
            <div className="text-2xl font-semibold mt-0.5">
              {data.total_airframe_hours.toFixed(1)}
            </div>
          </div>
          <div>
            <div className="text-xs text-slate-500 uppercase tracking-wide">Since Phase</div>
            <div className="text-2xl font-semibold mt-0.5">
              {data.hours_since_phase.toFixed(1)}
            </div>
          </div>
          <div>
            <div className="text-xs text-slate-500 uppercase tracking-wide">Phase Interval</div>
            <div className="text-2xl font-semibold mt-0.5">{data.phase_interval.toFixed(0)}</div>
          </div>
          <div>
            <div className="text-xs text-slate-500 uppercase tracking-wide">Hours to Phase</div>
            <div
              className={`text-2xl font-semibold mt-0.5 ${
                data.hours_to_phase < 50 ? "text-yellow-400" : ""
              }`}
            >
              {data.hours_to_phase.toFixed(1)}
            </div>
            {data.hours_to_phase < 50 && (
              <div className="mt-1">
                <Badge variant="warning">Approaching</Badge>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Open Discrepancies */}
      <div className="card">
        <div className="flex items-center justify-between mb-3">
          <h2>Open Discrepancies</h2>
          <Link
            to={`/maintenance/${data.id}`}
            className="text-xs text-slate-400 hover:text-slate-200"
          >
            Manage in Maintenance →
          </Link>
        </div>
        {data.open_discrepancies.length === 0 ? (
          <p className="text-sm text-slate-500">No open discrepancies.</p>
        ) : (
          <div>
            {data.open_discrepancies.map((d) => (
              <div
                key={d.id}
                className="py-3 border-b border-slate-800 last:border-0"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      {d.maf_number && (
                        <span className="font-mono text-sm font-semibold text-slate-200">
                          {d.maf_number}
                        </span>
                      )}
                      <Badge variant={SEV_VARIANT[d.severity]}>{d.severity}</Badge>
                      <Badge variant={WS_VARIANT[d.work_status]}>{WS_LABEL[d.work_status]}</Badge>
                      {d.system_affected && (
                        <span className="text-xs text-slate-400 font-mono">{d.system_affected}</span>
                      )}
                    </div>
                    <p className="text-sm text-slate-300 mt-1">{d.description}</p>
                    <div className="text-xs text-slate-500 mt-1">
                      Opened {formatDate(d.opened_date)}
                      {d.sortie_id && (
                        <>
                          {" · "}
                          <Link
                            to={`/sorties/${d.sortie_id}`}
                            className="text-blue-400 hover:text-blue-300"
                          >
                            Sortie #{d.sortie_id}
                          </Link>
                        </>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
