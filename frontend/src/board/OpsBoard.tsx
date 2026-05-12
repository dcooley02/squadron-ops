import { useQuery, useQueries } from "@tanstack/react-query";
import { format, parseISO, isSameDay, startOfDay } from "date-fns";
import { AlertTriangle } from "lucide-react";
import {
  fetchAircraft,
  fetchUpcomingSorties,
  fetchSortieFitness,
  fetchSortie,
  fetchPersons,
  fetchDashboardSummary,
  type AircraftStatus,
  type SortieSummary,
  type SortieFitness,
  type SortieDetail,
  type CrewPosition,
} from "../lib/api";
import BoardLayout from "./BoardLayout";

const QUERY_OPTS = {
  refetchInterval: 30_000,
  staleTime: 0,
  refetchOnWindowFocus: true,
} as const;

const REQUIRED_POSITIONS: CrewPosition[] = ["HAC", "CREW_CHIEF"];

const POSITION_LABELS: Record<CrewPosition, string> = {
  HAC: "HAC",
  H2P: "H2P",
  H2P_U: "H2P(U)",
  CREW_CHIEF: "CC",
  AIRCREW: "AIRCREW",
  AWS: "AWS",
};

const STATUS_TINT: Record<AircraftStatus, string> = {
  FMC: "bg-green-950/30",
  PMC: "bg-yellow-950/30",
  NMC: "bg-red-950/30",
  NMCM: "bg-red-950/30",
  NMCS: "bg-red-950/30",
};

const STATUS_TEXT_COLOR: Record<AircraftStatus, string> = {
  FMC: "text-green-400",
  PMC: "text-yellow-400",
  NMC: "text-red-400",
  NMCM: "text-red-400",
  NMCS: "text-red-400",
};

const FITNESS_BORDER: Record<string, string> = {
  green: "border-l-green-500",
  yellow: "border-l-yellow-400",
  red: "border-l-red-500",
};

function formatHHMM(str: string | null | undefined): string {
  if (!str) return "—";
  return format(parseISO(str), "HH:mm");
}

function formatCrewName(personName: string, callsign?: string | null): string {
  const parts = personName.split(", ");
  const last = parts[0] ?? personName;
  const first = parts[1] ?? "";
  const abbrev = first ? `${last}, ${first.charAt(0)}.` : last;
  return callsign ? `${abbrev} "${callsign}"` : abbrev;
}

export default function OpsBoard() {
  const { data: aircraft, dataUpdatedAt } = useQuery({
    queryKey: ["aircraft"],
    queryFn: () => fetchAircraft(),
    ...QUERY_OPTS,
  });
  const { data: sorties } = useQuery({
    queryKey: ["upcoming-sorties"],
    queryFn: () => fetchUpcomingSorties(),
    ...QUERY_OPTS,
  });
  const { data: dashboard } = useQuery({
    queryKey: ["dashboard-summary"],
    queryFn: () => fetchDashboardSummary(),
    ...QUERY_OPTS,
  });
  const { data: persons } = useQuery({
    queryKey: ["persons"],
    queryFn: () => fetchPersons(),
    ...QUERY_OPTS,
  });

  const today = startOfDay(new Date());
  const todaysSorties: SortieSummary[] = (sorties ?? []).filter(
    (s) => s.takeoff_time && isSameDay(parseISO(s.takeoff_time), today)
  );

  const fitnessQueries = useQueries({
    queries: todaysSorties.map((s) => ({
      queryKey: ["fitness", s.id],
      queryFn: () => fetchSortieFitness(s.id),
      ...QUERY_OPTS,
    })),
  });

  const detailQueries = useQueries({
    queries: todaysSorties.map((s) => ({
      queryKey: ["sortie-detail", s.id],
      queryFn: () => fetchSortie(s.id),
      ...QUERY_OPTS,
    })),
  });

  const fitnessById: Record<number, SortieFitness> = {};
  todaysSorties.forEach((s, i) => {
    const f = fitnessQueries[i]?.data;
    if (f) fitnessById[s.id] = f;
  });

  const detailById: Record<number, SortieDetail> = {};
  todaysSorties.forEach((s, i) => {
    const d = detailQueries[i]?.data;
    if (d) detailById[s.id] = d;
  });

  const personById = Object.fromEntries((persons ?? []).map((p) => [p.id, p]));

  const sortedAircraft = [...(aircraft ?? [])].sort((a, b) =>
    (a.side_number ?? "").localeCompare(b.side_number ?? "")
  );

  const expiring = dashboard?.currencies_expiring_14d_count ?? 0;
  const expired = dashboard?.currencies_expired_count ?? 0;
  const currencyTint =
    expired > 0
      ? "bg-red-950/40 border-t border-red-900/50"
      : expiring > 0
      ? "bg-yellow-950/30 border-t border-yellow-900/50"
      : "bg-slate-900 border-t border-slate-800";

  return (
    <BoardLayout boardName="OPS BOARD" lastUpdatedAt={dataUpdatedAt}>
      <div className="flex flex-col h-full">

        {/* STRIP A — Aircraft status */}
        <div className="shrink-0 h-[100px] flex border-b border-slate-800">
          {sortedAircraft.map((ac, i) => (
            <div
              key={ac.id}
              className={`flex-1 flex flex-col items-center justify-center ${STATUS_TINT[ac.status]} ${i > 0 ? "border-l border-slate-800" : ""}`}
            >
              <div className="text-3xl font-bold text-slate-100 leading-none">
                {ac.side_number ?? ac.bureau_number}
              </div>
              <div className={`text-base font-bold mt-1 ${STATUS_TEXT_COLOR[ac.status]}`}>
                {ac.status}
              </div>
            </div>
          ))}
          {sortedAircraft.length === 0 && (
            <div className="flex-1 flex items-center justify-center text-slate-600 text-lg">
              No aircraft data
            </div>
          )}
        </div>

        {/* SECTION B — Today's schedule */}
        <div className="flex-1 overflow-auto min-h-0 p-6">
          <div className="flex items-baseline gap-4 mb-5">
            <h2 className="text-3xl font-bold text-slate-100 uppercase tracking-wide">
              Today — {format(today, "EEEE, MMMM d")}
            </h2>
            <span className="text-xl text-slate-400">
              {todaysSorties.length} {todaysSorties.length === 1 ? "flight" : "flights"}
            </span>
          </div>

          {todaysSorties.length === 0 ? (
            <div className="flex items-center justify-center h-48">
              <p className="text-4xl font-bold text-slate-600 uppercase tracking-widest">
                No Flights Scheduled Today
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {todaysSorties.map((s) => {
                const fitness = fitnessById[s.id];
                const detail = detailById[s.id];
                const logs = detail?.flight_logs ?? [];
                const status = fitness?.overall_status ?? "green";

                const optionalLogs = logs.filter(
                  (fl) => !(REQUIRED_POSITIONS as string[]).includes(fl.crew_position)
                );

                return (
                  <div
                    key={s.id}
                    className={`bg-slate-900 border border-slate-800 rounded-lg border-l-8 ${FITNESS_BORDER[status]} p-5`}
                  >
                    {/* Header row */}
                    <div className="flex items-baseline gap-4 mb-4 flex-wrap">
                      <span className="text-4xl font-bold text-slate-100 tabular-nums">
                        {formatHHMM(s.takeoff_time)}
                        {s.land_time && (
                          <span className="text-slate-500 font-normal">
                            {" – "}{formatHHMM(s.land_time)}
                          </span>
                        )}
                      </span>
                      <span className="text-2xl text-slate-300">
                        {s.event_type ?? "PROFICIENCY"}
                        {s.event_code && (
                          <span className="text-slate-500 ml-2">· {s.event_code}</span>
                        )}
                        {s.aircraft_side_number && (
                          <span className="text-slate-500 ml-2">· {s.aircraft_side_number}</span>
                        )}
                      </span>
                      {s.duration_hours != null && (
                        <span className="text-xl text-slate-500 ml-auto">
                          {s.duration_hours.toFixed(1)}h
                        </span>
                      )}
                    </div>

                    {/* Crew grid */}
                    <div className="grid grid-cols-2 gap-x-10 gap-y-2">
                      {REQUIRED_POSITIONS.map((pos) => {
                        const log = logs.find((fl) => fl.crew_position === pos);
                        return (
                          <div key={pos} className="flex items-baseline gap-2">
                            <span className="text-slate-500 text-lg font-medium w-20 shrink-0">
                              {POSITION_LABELS[pos]}:
                            </span>
                            {log ? (
                              <span className="text-slate-100 text-xl font-semibold">
                                {formatCrewName(
                                  log.person_name,
                                  personById[log.person_id]?.callsign
                                )}
                              </span>
                            ) : (
                              <span className="text-red-400 text-xl font-bold">UNFILLED</span>
                            )}
                          </div>
                        );
                      })}
                      {optionalLogs.map((fl) => (
                        <div key={fl.id} className="flex items-baseline gap-2">
                          <span className="text-slate-500 text-lg font-medium w-20 shrink-0">
                            {POSITION_LABELS[fl.crew_position as CrewPosition]}:
                          </span>
                          <span className="text-slate-200 text-xl">
                            {formatCrewName(
                              fl.person_name,
                              personById[fl.person_id]?.callsign
                            )}
                          </span>
                        </div>
                      ))}
                    </div>

                    {/* Fitness warnings */}
                    {fitness?.warnings && fitness.warnings.length > 0 && (
                      <div className="mt-4 pt-3 border-t border-slate-800 space-y-1.5">
                        {fitness.warnings.map((w, wi) => (
                          <div
                            key={wi}
                            className={`flex items-start gap-2 text-lg ${
                              w.severity === "red" ? "text-red-300" : "text-yellow-300"
                            }`}
                          >
                            <AlertTriangle size={20} className="shrink-0 mt-0.5" />
                            {w.message}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* STRIP C — Currency warnings */}
        <div className={`shrink-0 h-[80px] flex items-center px-6 gap-8 ${currencyTint}`}>
          <span className="text-base font-bold uppercase tracking-widest text-slate-400 shrink-0">
            Currency Warnings
          </span>
          {expired === 0 && expiring === 0 ? (
            <span className="text-2xl font-bold text-green-400">ALL CURRENT</span>
          ) : (
            <div className="flex items-center gap-8">
              {expiring > 0 && (
                <span className="text-2xl font-bold text-yellow-400">
                  {expiring} EXPIRING SOON
                </span>
              )}
              {expired > 0 && (
                <span className="text-2xl font-bold text-red-400">
                  {expired} EXPIRED
                </span>
              )}
            </div>
          )}
        </div>

      </div>
    </BoardLayout>
  );
}
