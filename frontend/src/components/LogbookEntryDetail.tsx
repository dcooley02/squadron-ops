import { useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { X } from "lucide-react";
import { format, parseISO } from "date-fns";
import { fetchSortieDetail } from "../lib/logbook";
import type { LogbookEntry, FlightLogFull } from "../types/logbook";

interface Props {
  entry: LogbookEntry | null;
  onClose: () => void;
}

function fmt(n: number | null | undefined): string {
  if (n == null || n === 0) return "";
  return n.toFixed(1);
}

function formatDt(str: string | null): string {
  if (!str) return "—";
  return format(parseISO(str), "d MMM yyyy, HH:mm");
}

function formatDtShort(str: string | null): string {
  if (!str) return "—";
  return format(parseISO(str), "HH:mm");
}

function CrewRow({ fl }: { fl: FlightLogFull }) {
  const pos = fl.crew_position.replace(/_/g, " ");
  const roleHours: string[] = [];
  if (fl.ac_commander_hours > 0) roleHours.push(`${fl.ac_commander_hours.toFixed(1)} AC`);
  if (fl.first_pilot_hours > 0) roleHours.push(`${fl.first_pilot_hours.toFixed(1)} 1P`);
  if (fl.copilot_hours > 0) roleHours.push(`${fl.copilot_hours.toFixed(1)} CoP`);
  if (fl.mission_commander_hours > 0) roleHours.push(`${fl.mission_commander_hours.toFixed(1)} MC`);
  if (fl.instructor_hours > 0) roleHours.push(`${fl.instructor_hours.toFixed(1)} IP`);
  if (fl.special_crew_time_hours && fl.special_crew_time_hours > 0) {
    roleHours.push(`${fl.special_crew_time_hours.toFixed(1)} SC`);
  }
  const envParts: string[] = [];
  if (fl.night_hours > 0) envParts.push(`${fl.night_hours.toFixed(1)} night`);
  if (fl.nvg_hours > 0) envParts.push(`${fl.nvg_hours.toFixed(1)} NVG`);
  if (fl.actual_instrument_hours > 0) envParts.push(`${fl.actual_instrument_hours.toFixed(1)} inst`);
  if (fl.sim_instrument_hours > 0) envParts.push(`${fl.sim_instrument_hours.toFixed(1)} sim`);

  return (
    <div className="flex items-start justify-between py-2 border-b border-slate-800 last:border-0 gap-3">
      <div>
        <span className="text-xs text-slate-500 uppercase tracking-wide mr-2">{pos}</span>
        {fl.crew_qual_code && (
          <span
            className="font-mono text-xs font-semibold text-slate-300 bg-slate-800 border border-slate-700 rounded px-1 py-0.5 mr-2"
            title="CNAF M-3710.7 qualification code"
          >
            {fl.crew_qual_code}
          </span>
        )}
        <span className="text-sm font-medium">{fl.person_name}</span>
        {fl.syllabus_event_completed && (
          <span className="ml-2 text-xs text-blue-400">✓ {fl.syllabus_event_completed}</span>
        )}
      </div>
      <div className="text-right text-xs text-slate-400 space-y-0.5">
        {roleHours.length > 0 && <div>{roleHours.join(", ")}</div>}
        {envParts.length > 0 && <div className="text-slate-500">{envParts.join(", ")}</div>}
        {roleHours.length === 0 && envParts.length === 0 && (
          <div>{fl.hours_logged.toFixed(1)} hrs</div>
        )}
      </div>
    </div>
  );
}

export default function LogbookEntryDetail({ entry, onClose }: Props) {
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [onClose]);

  const { data, isLoading } = useQuery({
    queryKey: ["sortie-detail-modal", entry?.sortie_id],
    queryFn: () => fetchSortieDetail(entry!.sortie_id),
    enabled: entry != null,
    staleTime: 60_000,
  });

  if (!entry) return null;

  const myFlightLog = data?.flight_logs.find((fl) => fl.id === entry.flight_log_id);
  const approaches = myFlightLog?.instrument_approaches ?? [];
  const legs = data?.legs ?? [];
  const tmrCodes = data?.tmr_codes ?? [];

  const title = [data?.event_code, data?.event_type]
    .filter(Boolean)
    .join(" — ") || `Sortie ${entry.sortie_id}`;

  return (
    <div
      className="fixed inset-0 bg-black/60 z-50 flex items-start justify-center p-4 pt-12 overflow-y-auto"
      onClick={onClose}
    >
      <div
        className="bg-slate-900 border border-slate-800 rounded-xl w-full max-w-4xl mb-12"
        onClick={(e) => e.stopPropagation()}
      >
        {/* ── Header ── */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-slate-800">
          <div>
            <h2 className="text-base font-semibold">
              Sortie {entry.sortie_id}
              {title && <span className="font-normal text-slate-400 ml-2">— {title}</span>}
            </h2>
            {data && (
              <div className="text-xs text-slate-500 mt-0.5">
                {data.flight_mode !== "LIVE" && (
                  <span className="mr-2 uppercase">{data.flight_mode.replace(/_/g, " ")}</span>
                )}
                {data.takeoff_time && formatDt(data.takeoff_time)}
                {data.land_time && ` – ${formatDtShort(data.land_time)} local`}
                {data.duration_hours != null && ` · ${data.duration_hours.toFixed(1)} hrs`}
              </div>
            )}
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-200 transition-colors"
            aria-label="Close"
          >
            <X size={18} />
          </button>
        </div>

        <div className="px-5 py-4 space-y-5">
          {isLoading && (
            <p className="text-sm text-slate-500 text-center py-6">Loading sortie detail…</p>
          )}

          {data && (
            <>
              {/* ── Overview ── */}
              <div className="grid grid-cols-2 gap-x-8 gap-y-1 text-sm">
                {data.aircraft_side_number && (
                  <div>
                    <span className="text-slate-500">Aircraft</span>{" "}
                    <span className="text-slate-200">
                      {data.aircraft_side_number}
                      {entry.bureau_number && ` (BuNo ${entry.bureau_number})`}
                      {entry.tms && `, ${entry.tms}`}
                    </span>
                  </div>
                )}
                {(data.departure_location || data.arrival_location) && (
                  <div>
                    <span className="text-slate-500">Route</span>{" "}
                    <span className="text-slate-200">
                      {data.departure_location ?? "?"} → {data.arrival_location ?? "?"}
                    </span>
                  </div>
                )}
              </div>

              {/* ── Crew ── */}
              {data.flight_logs.length > 0 && (
                <div>
                  <h3 className="text-xs uppercase tracking-widest text-slate-500 mb-2">
                    Crew ({data.flight_logs.length})
                  </h3>
                  <div>
                    {data.flight_logs.map((fl) => (
                      <CrewRow key={fl.id} fl={fl} />
                    ))}
                  </div>
                </div>
              )}

              {/* ── Instrument Approaches (this person) ── */}
              {approaches.length > 0 && (
                <div>
                  <h3 className="text-xs uppercase tracking-widest text-slate-500 mb-2">
                    Approaches ({approaches.length})
                  </h3>
                  <div className="space-y-1">
                    {approaches.map((appr) => (
                      <div key={appr.id} className="text-sm flex items-center gap-2">
                        <span className="font-mono text-blue-400 text-xs">{appr.approach_type}</span>
                        <span className="text-slate-300">{appr.airport_icao}</span>
                        {appr.runway && (
                          <span className="text-slate-500">Rwy {appr.runway}</span>
                        )}
                        <span className="text-xs text-slate-500">
                          ({appr.actual_or_simulated})
                        </span>
                        {appr.remarks && (
                          <span className="text-xs text-slate-600 truncate">{appr.remarks}</span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* ── TMR Codes ── */}
              {tmrCodes.length > 0 && (
                <div>
                  <h3 className="text-xs uppercase tracking-widest text-slate-500 mb-2">
                    TMR Codes
                  </h3>
                  <div className="space-y-1">
                    {tmrCodes.map((tmr) => (
                      <div key={tmr.slot} className="text-sm flex items-center gap-2">
                        <span className="font-mono text-blue-400 text-xs w-10">MSN{tmr.slot}</span>
                        <span className="font-mono text-slate-300">{tmr.code}</span>
                        <span className="text-slate-500 truncate">{tmr.description}</span>
                        {tmr.hours != null && (
                          <span className="text-slate-600 text-xs ml-auto shrink-0">
                            {tmr.hours.toFixed(1)} hrs
                          </span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* ── Legs ── */}
              {legs.length > 1 && (
                <div>
                  <h3 className="text-xs uppercase tracking-widest text-slate-500 mb-2">
                    Legs ({legs.length})
                  </h3>
                  <div className="space-y-1">
                    {legs.map((leg) => (
                      <div key={leg.id} className="text-sm text-slate-300">
                        <span className="text-slate-500 mr-1">Leg {leg.leg_number}:</span>
                        {leg.departure_location} → {leg.arrival_location}
                        {leg.duration_hours != null && (
                          <span className="text-slate-500 ml-1">({leg.duration_hours.toFixed(1)} hr)</span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* ── Debrief Notes ── */}
              {data.debrief_notes && (
                <div>
                  <h3 className="text-xs uppercase tracking-widest text-slate-500 mb-1">
                    Debrief Notes
                  </h3>
                  <p className="text-sm text-slate-300 whitespace-pre-wrap">
                    {data.debrief_notes}
                  </p>
                </div>
              )}

              {/* ── Instructor Remarks (this person) ── */}
              {myFlightLog?.instructor_remarks && (
                <div>
                  <h3 className="text-xs uppercase tracking-widest text-slate-500 mb-1">
                    Remarks
                  </h3>
                  <p className="text-sm text-slate-300 whitespace-pre-wrap">
                    {myFlightLog.instructor_remarks}
                  </p>
                </div>
              )}

              {/* ── Hour detail (all 15 fields, non-zero) ── */}
              {(() => {
                const fields: [string, number | null | undefined][] = [
                  ["Total", entry.total_hours],
                  ["Night", entry.night_hours],
                  ["NVG", entry.nvg_hours],
                  ["Instr Act", entry.actual_instrument_hours],
                  ["Instr Sim", entry.sim_instrument_hours],
                  ["NVG HL (Unaided)", entry.nvg_unaided_hl_hours],
                  ["NVG LL (Unaided)", entry.nvg_unaided_ll_hours],
                  ["NVG HL (Tactical)", entry.nvg_tactical_hl_hours],
                  ["NVG LL (Tactical)", entry.nvg_tactical_ll_hours],
                ];
                const nonZero = fields.filter(([, v]) => v != null && v > 0);
                if (nonZero.length <= 1) return null; // just total, nothing interesting
                return (
                  <div>
                    <h3 className="text-xs uppercase tracking-widest text-slate-500 mb-2">
                      Hour Detail
                    </h3>
                    <div className="grid grid-cols-3 sm:grid-cols-4 gap-x-6 gap-y-1 text-sm">
                      {nonZero.map(([label, v]) => (
                        <div key={label}>
                          <span className="text-slate-500">{label}</span>{" "}
                          <span className="text-slate-200">{fmt(v)}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                );
              })()}

              {/* ── Data provenance ── */}
              {entry.data_provenance && entry.data_provenance !== "ENTERED" && (
                <div className="text-xs text-slate-600">
                  Data source: {entry.data_provenance}
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
