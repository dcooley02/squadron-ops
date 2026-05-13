import { useQuery } from "@tanstack/react-query";
import { Link, useNavigate, useParams } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import { format, parseISO } from "date-fns";
import {
  fetchSortie,
  fetchSafetyReportsForSortie,
  type CrewPosition,
  type SortieDetail as SortieDetailType,
  type FlightLogOut,
  type SafetyReport,
  type SafetyReportSeverity,
  type SafetyReportStatus,
} from "../lib/api";
import Loading from "../components/Loading";
import Badge from "../components/Badge";

const POSITION_BADGE_VARIANT: Record<CrewPosition, "info" | "warning" | "neutral"> = {
  HAC: "info",
  H2P: "info",
  H2P_U: "warning",
  CREW_CHIEF: "neutral",
  AIRCREW: "neutral",
  AWS: "neutral",
};

function formatDateTime(str: string | null): string {
  if (!str) return "—";
  return format(parseISO(str), "MMM d, yyyy HH:mm");
}

export default function SortieDetail() {
  const { id } = useParams<{ id: string }>();
  const sortieId = Number(id);
  const navigate = useNavigate();

  const { data, isLoading, error } = useQuery({
    queryKey: ["sortie", sortieId],
    queryFn: () => fetchSortie(sortieId),
    enabled: !isNaN(sortieId),
  });

  const { data: safetyReports } = useQuery({
    queryKey: ["sortie-safety", sortieId],
    queryFn: () => fetchSafetyReportsForSortie(sortieId),
    enabled: !isNaN(sortieId),
  });

  if (isLoading) return <Loading />;
  if (error || !data) {
    return (
      <div className="card border-red-600/50 bg-red-950/20 text-red-300">
        Sortie not found.
      </div>
    );
  }

  const hourBreakdown = [
    { label: "Day",        hours: data.day_hours },
    { label: "Night",      hours: data.night_hours },
    { label: "NVG",        hours: data.nvg_hours },
    { label: "Instrument", hours: data.instrument_hours },
  ].filter((h): h is { label: string; hours: number } => h.hours != null && h.hours > 0);

  const activityQuantities = buildActivityQuantities(data);

  return (
    <div className="space-y-5">
      <Link
        to="/sorties"
        className="inline-flex items-center gap-1 text-sm text-slate-400 hover:text-slate-200"
      >
        <ArrowLeft size={14} /> Back to sorties
      </Link>

      {/* Header card */}
      <div className="card">
        <div className="flex items-start justify-between flex-wrap gap-3">
          <div>
            <h1 className="flex items-center gap-2 flex-wrap">
              {data.event_type ?? "Sortie"}
              {data.event_code && (
                <span className="text-slate-400 font-normal text-lg">{data.event_code}</span>
              )}
            </h1>
            <div className="flex flex-wrap gap-3 text-sm text-slate-400 mt-1">
              <span>{formatDateTime(data.takeoff_time)}</span>
              {data.aircraft_side_number && (
                <>
                  <span>·</span>
                  <span>Aircraft {data.aircraft_side_number}</span>
                </>
              )}
              {data.duration_hours != null && (
                <>
                  <span>·</span>
                  <span>{data.duration_hours.toFixed(1)} hrs</span>
                </>
              )}
              {data.flight_mode && data.flight_mode !== "LIVE" && (
                <>
                  <span>·</span>
                  <span>{data.flight_mode.replace(/_/g, " ")}</span>
                </>
              )}
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant={data.is_complete ? "success" : "info"}>
              {data.is_complete ? "Complete" : "Scheduled"}
            </Badge>
            {!data.is_complete && (
              <button
                onClick={() => navigate(`/sorties/${sortieId}/complete`)}
                className="px-3 py-1.5 text-sm rounded bg-blue-700 hover:bg-blue-600 text-white font-medium transition-colors"
              >
                Complete this sortie
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Hour breakdown */}
      {hourBreakdown.length > 0 && (
        <div className="card">
          <h2 className="mb-3">Hour Breakdown</h2>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            {hourBreakdown.map(({ label, hours }) => (
              <div key={label}>
                <div className="text-xs text-slate-500 uppercase tracking-wide">{label}</div>
                <div className="text-2xl font-semibold mt-0.5">{hours.toFixed(1)}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Activity Quantities */}
      {activityQuantities.length > 0 && (
        <div className="card">
          <h2 className="mb-3">Activity Quantities</h2>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-x-6 gap-y-3">
            {activityQuantities.map(({ label, value }) => (
              <div key={label}>
                <div className="text-xs text-slate-500 uppercase tracking-wide">{label}</div>
                <div className="text-lg font-semibold mt-0.5">{value}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* TMR Codes */}
      {data.tmr_codes && data.tmr_codes.length > 0 && (
        <div className="card">
          <h2 className="mb-3">TMR Codes</h2>
          <div className="space-y-1.5">
            {data.tmr_codes
              .slice()
              .sort((a, b) => a.slot - b.slot)
              .map((t) => (
                <div
                  key={t.slot}
                  className="flex items-center gap-3 py-1.5 border-b border-slate-800 last:border-0"
                >
                  <span className="text-xs text-slate-500 font-medium w-12 shrink-0">
                    Slot {t.slot}
                  </span>
                  <span className="font-mono text-sm font-semibold text-slate-200 w-14 shrink-0">
                    {t.code}
                  </span>
                  <span className="text-sm text-slate-300 flex-1 min-w-0 truncate">
                    {t.description ?? "—"}
                  </span>
                  {t.hours != null && (
                    <span className="text-sm text-slate-400 shrink-0">
                      {t.hours.toFixed(1)} hrs
                    </span>
                  )}
                </div>
              ))}
          </div>
        </div>
      )}

      {/* Crew */}
      <div className="card">
        <h2 className="mb-3">Crew</h2>
        {data.flight_logs.length === 0 ? (
          <p className="text-sm text-slate-500">No crew logged.</p>
        ) : (
          <div className="space-y-0">
            {data.flight_logs.map((fl) => (
              <CrewRow key={fl.id} fl={fl} />
            ))}
          </div>
        )}
        {data.notes && (
          <div className="mt-4 pt-4 border-t border-slate-800 text-sm text-slate-400 italic">
            {data.notes}
          </div>
        )}
      </div>

      {/* Task Credits */}
      {data.task_credits && data.task_credits.length > 0 && (
        <div className="card">
          <h2 className="mb-3">Task Credits</h2>
          <div className="space-y-0">
            {data.task_credits.map((tc) => (
              <div
                key={tc.id}
                className="flex items-center justify-between py-2 border-b border-slate-800 last:border-0"
              >
                <div className="flex items-center gap-3">
                  <span className="font-mono text-sm text-blue-400">{tc.task_code}</span>
                  <span className="text-sm text-slate-300">{tc.person_name}</span>
                </div>
                <div className="flex items-center gap-3">
                  {tc.grade && (
                    <Badge variant={gradeVariant(tc.grade)}>{tc.grade.replace(/_/g, " ")}</Badge>
                  )}
                  {tc.remarks && (
                    <span className="text-xs text-slate-500 max-w-48 truncate">{tc.remarks}</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Debrief Notes */}
      {data.debrief_notes && (
        <div className="card">
          <h2 className="mb-2">Debrief Notes</h2>
          <p className="text-sm text-slate-300 whitespace-pre-wrap">{data.debrief_notes}</p>
        </div>
      )}

      {/* Safety Reports */}
      {safetyReports && safetyReports.length > 0 && (
        <SafetyReportsCard reports={safetyReports} />
      )}
    </div>
  );
}

const SEVERITY_VARIANT: Record<SafetyReportSeverity, "neutral" | "warning" | "danger"> = {
  INFO: "neutral",
  HAZARD: "warning",
  INCIDENT: "danger",
  MISHAP: "danger",
};

const SR_STATUS_VARIANT: Record<SafetyReportStatus, "neutral" | "warning" | "success"> = {
  OPEN: "warning",
  UNDER_REVIEW: "warning",
  CLOSED: "success",
};

function SafetyReportsCard({ reports }: { reports: SafetyReport[] }) {
  return (
    <div className="card border-l-4 border-l-amber-600/60">
      <div className="flex items-center justify-between mb-3">
        <h2>Safety Reports</h2>
        <span className="text-xs text-slate-500">{reports.length} filed</span>
      </div>
      <div className="space-y-3">
        {reports.map((r) => (
          <div key={r.id} className="border border-slate-800 rounded p-3 bg-slate-900/50">
            <div className="flex items-center gap-2 flex-wrap">
              <Badge variant={SEVERITY_VARIANT[r.severity]}>{r.severity}</Badge>
              <Badge variant={SR_STATUS_VARIANT[r.status]}>
                {r.status.replace(/_/g, " ")}
              </Badge>
              {r.category && (
                <span className="text-xs text-slate-400 font-mono">{r.category}</span>
              )}
              <span className="text-xs text-slate-500 ml-auto">
                {format(parseISO(r.created_at), "MMM d, yyyy HH:mm")}
              </span>
            </div>
            <p className="text-sm text-slate-300 mt-2 whitespace-pre-wrap">{r.description}</p>
            {r.actions_taken && (
              <div className="mt-2 pt-2 border-t border-slate-800">
                <div className="text-[10px] uppercase tracking-wide text-slate-500 mb-1">
                  Actions taken
                </div>
                <p className="text-sm text-slate-400 whitespace-pre-wrap">{r.actions_taken}</p>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

function CrewRow({ fl }: { fl: FlightLogOut }) {
  const approaches = fl.instrument_approaches ?? [];
  const hasDetail = approaches.length > 0 || !!fl.instructor_remarks;
  return (
    <div className="py-2.5 border-b border-slate-800 last:border-0">
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-3 min-w-0">
          <Badge variant={POSITION_BADGE_VARIANT[fl.crew_position]}>
            {fl.crew_position.replace(/_/g, " ")}
          </Badge>
          {fl.crew_qual_code && (
            <span
              className="font-mono text-xs font-semibold text-slate-300 bg-slate-800 border border-slate-700 rounded px-1.5 py-0.5"
              title="CNAF M-3710.7 qualification code"
            >
              {fl.crew_qual_code}
            </span>
          )}
          <div className="min-w-0">
            <div className="font-medium text-sm flex items-center gap-2">
              {fl.person_name}
              {fl.data_provenance === "BACKFILLED" && (
                <span className="text-[10px] uppercase tracking-wide text-slate-500 border border-slate-700 rounded px-1 py-0.5">
                  backfilled
                </span>
              )}
            </div>
            {fl.syllabus_event_completed && (
              <div className="text-xs text-slate-500 mt-0.5">
                Completed: {fl.syllabus_event_completed}
              </div>
            )}
          </div>
        </div>
        <div className="text-sm text-slate-400 shrink-0">{fl.hours_logged.toFixed(1)} hrs</div>
      </div>

      {hasDetail && (
        <div className="mt-2 pl-1 space-y-1.5">
          {approaches.length > 0 && (
            <div className="flex items-start gap-2 text-xs">
              <span className="text-slate-500 uppercase tracking-wide shrink-0 w-20">
                Approaches
              </span>
              <div className="flex flex-wrap gap-x-3 gap-y-1">
                {approaches.map((ap) => (
                  <span key={ap.id} className="text-slate-300">
                    <span className="font-mono text-slate-200">{ap.approach_type}</span>
                    {ap.airport_icao && (
                      <span className="text-slate-400"> @ {ap.airport_icao}</span>
                    )}
                    {ap.runway && (
                      <span className="text-slate-500"> RWY {ap.runway}</span>
                    )}
                    <span className="text-slate-500">
                      {" "}
                      ({ap.actual_or_simulated === "ACTUAL" ? "A" : "S"})
                    </span>
                  </span>
                ))}
              </div>
            </div>
          )}
          {fl.instructor_remarks && (
            <div className="flex items-start gap-2 text-xs">
              <span className="text-slate-500 uppercase tracking-wide shrink-0 w-20">
                Remarks
              </span>
              <p className="text-slate-300 italic flex-1">{fl.instructor_remarks}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function buildActivityQuantities(data: SortieDetailType): { label: string; value: string }[] {
  const items: { label: string; value: string }[] = [];
  const addI = (label: string, val: number | null) => {
    if (val != null && val > 0) items.push({ label, value: String(val) });
  };
  const addF = (label: string, val: number | null, unit = " hrs") => {
    if (val != null && val > 0) items.push({ label, value: val.toFixed(1) + unit });
  };
  addI("Landings (Day)", data.landings_day);
  addI("Landings (Night)", data.landings_night);
  addI("DVE Ldgs (Day)", data.landings_dve_day);
  addI("DVE Ldgs (Night)", data.landings_dve_night);
  addI("Hoist Streams", data.hoist_streams);
  addI("Hoist Recoveries", data.hoist_recoveries);
  addI("20mm Rounds", data.rounds_fired_20mm);
  addI("UGR Fired", data.ugr_fired);
  addI("CSW Rounds", data.csw_rounds);
  addI("CSW Rounds (Night)", data.csw_rounds_night);
  addI("Strafe Dry (Day)", data.strafe_dry_profiles_day);
  addI("Strafe Dry (Night)", data.strafe_dry_profiles_night);
  addI("AMNS Iterations", data.amns_iterations);
  addI("AMNS NTRs", data.amns_ntrs);
  addF("ALMDS Hours", data.almds_hours);
  return items;
}

function gradeVariant(grade: string): "success" | "warning" | "danger" | "neutral" {
  if (grade === "PASS" || grade === "COMPLETE") return "success";
  if (grade === "CONDITIONAL_PASS" || grade === "IN_PROGRESS") return "warning";
  if (grade === "UNSAT" || grade === "INCOMPLETE") return "danger";
  return "neutral";
}
