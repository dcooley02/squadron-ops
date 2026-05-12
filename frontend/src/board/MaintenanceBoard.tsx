import { useQuery, useQueries } from "@tanstack/react-query";
import {
  fetchAircraft,
  fetchAircraftDetail,
  type AircraftStatus,
  type AircraftDetail,
} from "../lib/api";
import BoardLayout from "./BoardLayout";

const QUERY_OPTS = {
  refetchInterval: 30_000,
  staleTime: 0,
  refetchOnWindowFocus: true,
} as const;

const STATUS_TEXT_COLOR: Record<AircraftStatus, string> = {
  FMC: "text-green-400",
  PMC: "text-yellow-400",
  NMC: "text-red-400",
  NMCM: "text-red-400",
  NMCS: "text-red-400",
};

const STATUS_CARD_TINT: Record<AircraftStatus, string> = {
  FMC: "",
  PMC: "bg-yellow-950/20",
  NMC: "bg-red-950/40",
  NMCM: "bg-red-950/40",
  NMCS: "bg-red-950/40",
};

const SEVERITY_COLOR: Record<string, string> = {
  MINOR: "text-slate-400",
  MAJOR: "text-yellow-400",
  GROUNDING: "text-red-400",
};

export default function MaintenanceBoard() {
  const { data: aircraft, dataUpdatedAt } = useQuery({
    queryKey: ["aircraft"],
    queryFn: () => fetchAircraft(),
    ...QUERY_OPTS,
  });

  const sortedAircraft = [...(aircraft ?? [])].sort((a, b) =>
    (a.side_number ?? "").localeCompare(b.side_number ?? "")
  );

  const detailQueries = useQueries({
    queries: sortedAircraft.map((ac) => ({
      queryKey: ["aircraft-detail", ac.id],
      queryFn: () => fetchAircraftDetail(ac.id),
      ...QUERY_OPTS,
    })),
  });

  const detailById: Record<number, AircraftDetail> = {};
  sortedAircraft.forEach((ac, i) => {
    const d = detailQueries[i]?.data;
    if (d) detailById[ac.id] = d;
  });

  const totalDiscrepancies = Object.values(detailById).reduce(
    (sum, d) => sum + (d?.open_discrepancies?.length ?? 0),
    0
  );

  const phaseDue50 = sortedAircraft.filter((ac) => {
    const d = detailById[ac.id];
    const toPhase = d ? d.hours_to_phase : ac.phase_interval - ac.hours_since_phase;
    return toPhase < 50;
  }).length;

  const fmcCount = sortedAircraft.filter((a) => a.status === "FMC").length;
  const nonFmcCount = sortedAircraft.length - fmcCount;

  return (
    <BoardLayout boardName="MAINTENANCE STATUS" lastUpdatedAt={dataUpdatedAt}>
      <div className="flex flex-col h-full">

        {/* Header */}
        <div className="shrink-0 px-6 py-4 flex items-baseline gap-6 border-b border-slate-800">
          <h2 className="text-3xl font-bold uppercase tracking-wide text-slate-100">
            Maintenance Status
          </h2>
          <span className="text-xl text-slate-400">{sortedAircraft.length} airframes</span>
          <span className="text-xl font-bold text-green-400">{fmcCount} FMC</span>
          {nonFmcCount > 0 && (
            <span className="text-xl font-bold text-red-400">{nonFmcCount} non-FMC</span>
          )}
        </div>

        {/* 4×2 aircraft grid */}
        <div className="flex-1 min-h-0 p-5 overflow-hidden">
          <div className="grid grid-cols-4 grid-rows-2 gap-4 h-full">
            {sortedAircraft.map((ac) => {
              const detail = detailById[ac.id];
              const toPhase = detail
                ? detail.hours_to_phase
                : ac.phase_interval - ac.hours_since_phase;
              const toPhaseColor =
                toPhase < 50
                  ? "text-red-400"
                  : toPhase < 100
                  ? "text-yellow-400"
                  : "text-slate-200";

              return (
                <div
                  key={ac.id}
                  className={`bg-slate-900 border border-slate-800 rounded-xl flex flex-col p-4 min-h-0 ${STATUS_CARD_TINT[ac.status]}`}
                >
                  {/* Primary ID */}
                  <div className={`text-7xl font-black leading-none ${STATUS_TEXT_COLOR[ac.status]}`}>
                    {ac.side_number ?? "—"}
                  </div>
                  <div className="text-sm text-slate-500 mt-0.5 mb-2">{ac.bureau_number}</div>

                  {/* Status label */}
                  <div className={`text-xl font-bold ${STATUS_TEXT_COLOR[ac.status]} mb-3`}>
                    {ac.status}
                  </div>

                  {/* Hours stats */}
                  <div className="grid grid-cols-3 gap-2 mb-3">
                    <div>
                      <div className="text-xs text-slate-500 uppercase tracking-wide">Total</div>
                      <div className="text-lg font-semibold text-slate-200">
                        {ac.total_airframe_hours.toFixed(1)}h
                      </div>
                    </div>
                    <div>
                      <div className="text-xs text-slate-500 uppercase tracking-wide">Since Ph</div>
                      <div className="text-lg font-semibold text-slate-200">
                        {ac.hours_since_phase.toFixed(1)}h
                      </div>
                    </div>
                    <div>
                      <div className="text-xs text-slate-500 uppercase tracking-wide">To Phase</div>
                      <div className={`text-lg font-semibold ${toPhaseColor}`}>
                        {toPhase.toFixed(1)}h
                      </div>
                    </div>
                  </div>

                  {/* Discrepancies */}
                  <div className="flex-1 min-h-0 overflow-hidden">
                    {detail?.open_discrepancies && detail.open_discrepancies.length > 0 ? (
                      <div>
                        <div className="text-xs text-slate-500 uppercase tracking-wide mb-1.5">
                          Discrepancies ({detail.open_discrepancies.length})
                        </div>
                        <div className="space-y-1">
                          {detail.open_discrepancies.slice(0, 3).map((d) => (
                            <div key={d.id} className="flex items-start gap-2">
                              <span
                                className={`text-xs font-bold shrink-0 mt-0.5 ${SEVERITY_COLOR[d.severity] ?? "text-slate-400"}`}
                              >
                                {d.severity.charAt(0)}
                              </span>
                              <span className="text-sm text-slate-300 leading-snug line-clamp-2">
                                {d.description.length > 80
                                  ? d.description.slice(0, 77) + "…"
                                  : d.description}
                              </span>
                            </div>
                          ))}
                          {detail.open_discrepancies.length > 3 && (
                            <div className="text-xs text-slate-500">
                              +{detail.open_discrepancies.length - 3} more
                            </div>
                          )}
                        </div>
                      </div>
                    ) : (
                      <div className="text-sm text-slate-600">No open discrepancies</div>
                    )}
                  </div>
                </div>
              );
            })}

            {/* Empty placeholder cells if fewer than 8 aircraft */}
            {Array.from({ length: Math.max(0, 8 - sortedAircraft.length) }).map((_, i) => (
              <div
                key={`empty-${i}`}
                className="bg-slate-900/20 border border-slate-800/30 rounded-xl"
              />
            ))}
          </div>
        </div>

        {/* Footer strip */}
        <div className="shrink-0 h-[56px] flex items-center px-6 gap-8 bg-slate-900 border-t border-slate-800">
          <span className="text-sm font-bold uppercase tracking-widest text-slate-500 shrink-0">
            Fleet Summary
          </span>
          <span className="text-xl font-bold text-slate-300">
            Open Discrepancies:{" "}
            <span className={totalDiscrepancies > 0 ? "text-yellow-400" : "text-green-400"}>
              {totalDiscrepancies}
            </span>
          </span>
          <span className="text-slate-700">·</span>
          <span className="text-xl font-bold text-slate-300">
            Phase Due Within 50h:{" "}
            <span className={phaseDue50 > 0 ? "text-red-400" : "text-green-400"}>
              {phaseDue50}
            </span>
          </span>
        </div>

      </div>
    </BoardLayout>
  );
}
