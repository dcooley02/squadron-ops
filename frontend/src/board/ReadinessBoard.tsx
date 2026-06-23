import { useQuery } from "@tanstack/react-query";
import { format } from "date-fns";
import clsx from "clsx";
import {
  fetchDashboardSummary,
  fetchAircraft,
  fetchSquadronReadiness,
  type AircraftStatus,
} from "../lib/api";
import TRatingBadge from "../components/TRatingBadge";
import BoardLayout from "./BoardLayout";

const QUERY_OPTS = {
  refetchInterval: 30_000,
  staleTime: 0,
  refetchOnWindowFocus: true,
} as const;

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

function BigRateRing({ rate }: { rate: number }) {
  const radius = 100;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (rate / 100) * circumference;
  const color =
    rate >= 75 ? "text-green-500" : rate >= 50 ? "text-yellow-500" : "text-red-500";

  return (
    <div className="flex flex-col items-center justify-center">
      <div className="relative w-[min(14rem,24vh)] h-[min(14rem,24vh)]">
        <svg className="w-full h-full -rotate-90" viewBox="0 0 240 240">
          <circle
            cx="120"
            cy="120"
            r={radius}
            stroke="currentColor"
            strokeWidth="14"
            fill="none"
            className="text-slate-800"
          />
          <circle
            cx="120"
            cy="120"
            r={radius}
            stroke="currentColor"
            strokeWidth="14"
            fill="none"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            strokeLinecap="round"
            className={clsx("transition-all duration-700", color)}
          />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center">
          <span className={clsx("text-[clamp(2rem,5vh,3rem)] font-black tabular-nums", color)}>
            {rate.toFixed(1)}%
          </span>
        </div>
      </div>
      <div className="text-2xl font-bold uppercase tracking-widest text-slate-400 mt-2">
        FMC Rate
      </div>
    </div>
  );
}

export default function ReadinessBoard() {
  const { data: dashboard, dataUpdatedAt } = useQuery({
    queryKey: ["dashboard-summary"],
    queryFn: () => fetchDashboardSummary(),
    ...QUERY_OPTS,
  });

  const { data: aircraft } = useQuery({
    queryKey: ["aircraft"],
    queryFn: () => fetchAircraft(),
    ...QUERY_OPTS,
  });

  const { data: readiness } = useQuery({
    queryKey: ["squadron-readiness"],
    queryFn: fetchSquadronReadiness,
    ...QUERY_OPTS,
  });

  const sortedAircraft = [...(aircraft ?? [])].sort((a, b) =>
    (a.side_number ?? "").localeCompare(b.side_number ?? "")
  );

  const expiring = dashboard?.currencies_expiring_14d_count ?? 0;
  const expired = dashboard?.currencies_expired_count ?? 0;
  const openDiscrepancies = dashboard?.open_discrepancies_count ?? 0;

  return (
    <BoardLayout boardName="SQUADRON SNAPSHOT" lastUpdatedAt={dataUpdatedAt}>
      <div className="flex flex-col h-full overflow-hidden">

        {/* Header */}
        <div className="shrink-0 px-6 py-2 border-b border-slate-800 flex items-baseline justify-between gap-4">
          <div className="min-w-0">
            <h2 className="text-2xl font-bold uppercase tracking-wide text-slate-100 truncate">
              Squadron Snapshot
            </h2>
            <p className="text-sm text-slate-500 mt-0.5">
              Operational metrics plus WTM capability T-ratings
            </p>
          </div>
          <span className="text-sm text-slate-400 font-medium shrink-0 whitespace-nowrap">
            {format(new Date(), "EEEE, MMMM d, yyyy")}
          </span>
        </div>

        {/* Rows fill remaining height in 4:3:3 proportion */}
        <div className="flex-1 min-h-0 flex flex-col">

          {/* ROW 1 — FMC Rate / Personnel / 30-day Activity */}
          <div
            className="min-h-0 grid grid-cols-3 divide-x divide-slate-800 border-b border-slate-800"
            style={{ flex: "4 1 0" }}
          >
            {/* FMC Rate ring */}
            <div className="flex items-center justify-center p-6">
              <BigRateRing rate={dashboard?.fmc_rate ?? 0} />
            </div>

            {/* Personnel */}
            <div className="flex flex-col justify-center px-6 py-3 gap-2 overflow-hidden">
              <div className="text-sm font-bold uppercase tracking-widest text-slate-500">
                Personnel
              </div>
              <div className="flex gap-6 items-end">
                <div>
                  <div className="text-[clamp(2.5rem,9vh,5rem)] font-black text-slate-100 leading-none tabular-nums">
                    {dashboard?.total_personnel ?? "—"}
                  </div>
                  <div className="text-base text-slate-400 mt-1">Total</div>
                </div>
                <div>
                  <div className="text-[clamp(2rem,8vh,4rem)] font-black text-blue-400 leading-none tabular-nums">
                    {dashboard?.total_pilots ?? "—"}
                  </div>
                  <div className="text-base text-slate-400 mt-1">Pilots</div>
                </div>
                <div>
                  <div className="text-[clamp(2rem,8vh,4rem)] font-black text-blue-300 leading-none tabular-nums">
                    {dashboard?.total_aircrew ?? "—"}
                  </div>
                  <div className="text-base text-slate-400 mt-1">Aircrew</div>
                </div>
              </div>
            </div>

            {/* 30-day activity */}
            <div className="flex flex-col justify-center px-6 py-3 gap-2 overflow-hidden">
              <div className="text-sm font-bold uppercase tracking-widest text-slate-500">
                Last 30 Days
              </div>
              <div className="flex gap-8 items-end">
                <div>
                  <div className="text-[clamp(2.5rem,9vh,5rem)] font-black text-slate-100 leading-none tabular-nums">
                    {dashboard?.sorties_last_30_days ?? "—"}
                  </div>
                  <div className="text-base text-slate-400 mt-1">Sorties</div>
                </div>
                <div>
                  <div className="text-[clamp(2.5rem,9vh,5rem)] font-black text-slate-100 leading-none tabular-nums">
                    {dashboard?.total_hours_last_30_days?.toFixed(0) ?? "—"}
                  </div>
                  <div className="text-base text-slate-400 mt-1">Hours</div>
                </div>
              </div>
            </div>
          </div>

          {/* ROW 2 — WTM T-rating strip */}
          {readiness && (
            <div
              className="shrink-0 border-b border-slate-800 px-4 py-1.5 flex items-center gap-3 overflow-hidden"
            >
              <div className="flex items-center gap-2 shrink-0">
                <span className="text-sm font-bold uppercase tracking-widest text-slate-500">
                  WTM
                </span>
                <TRatingBadge rating={readiness.squadron_overall_rating} large />
              </div>
              <div className="flex flex-1 justify-between gap-1 min-w-0">
                {readiness.areas.map((area) => (
                  <div
                    key={area.capability_area}
                    className="flex flex-col items-center min-w-0 flex-1"
                  >
                    <span className="text-xs font-mono text-slate-500 truncate w-full text-center">
                      {area.capability_area}
                    </span>
                    <TRatingBadge rating={area.squadron_rating} />
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* ROW 3 — Currency overview */}
          <div
            className="min-h-0 grid grid-cols-3 divide-x divide-slate-800 border-b border-slate-800"
            style={{ flex: "3 1 0" }}
          >
            {/* Expiring soon */}
            <div
              className={clsx(
                "flex flex-col items-center justify-center p-4",
                expiring > 0 && "bg-yellow-950/30"
              )}
            >
              <div
                className={clsx(
                  "text-[clamp(3rem,12vh,7rem)] font-black leading-none tabular-nums",
                  expiring > 0 ? "text-yellow-400" : "text-green-400"
                )}
              >
                {expiring}
              </div>
              <div className="text-sm text-slate-400 mt-2 uppercase tracking-wide font-semibold text-center px-4 leading-tight">
                Currencies Expiring Within 14 Days
              </div>
            </div>

            {/* Expired */}
            <div
              className={clsx(
                "flex flex-col items-center justify-center p-4",
                expired > 0 && "bg-red-950/40"
              )}
            >
              <div
                className={clsx(
                  "text-[clamp(3rem,12vh,7rem)] font-black leading-none tabular-nums",
                  expired > 0 ? "text-red-400" : "text-green-400"
                )}
              >
                {expired}
              </div>
              <div className="text-sm text-slate-400 mt-2 uppercase tracking-wide font-semibold">
                Currencies Expired
              </div>
            </div>

            {/* Open discrepancies */}
            <div
              className={clsx(
                "flex flex-col items-center justify-center p-4",
                openDiscrepancies > 0 && "bg-yellow-950/20"
              )}
            >
              <div
                className={clsx(
                  "text-[clamp(3rem,12vh,7rem)] font-black leading-none tabular-nums",
                  openDiscrepancies > 0 ? "text-yellow-400" : "text-green-400"
                )}
              >
                {dashboard ? openDiscrepancies : "—"}
              </div>
              <div className="text-sm text-slate-400 mt-2 uppercase tracking-wide font-semibold">
                Open Discrepancies
              </div>
            </div>
          </div>

          {/* ROW 4 — Aircraft status strip */}
          <div className="min-h-0 flex flex-col" style={{ flex: "3 1 0" }}>
            <div className="shrink-0 px-6 pt-3 pb-1">
              <span className="text-base font-bold uppercase tracking-widest text-slate-500">
                Aircraft Status
              </span>
            </div>
            <div className="flex-1 min-h-0 flex border-t border-slate-800">
              {sortedAircraft.map((ac, i) => (
                <div
                  key={ac.id}
                  className={`flex-1 flex flex-col items-center justify-center ${STATUS_TINT[ac.status]} ${i > 0 ? "border-l border-slate-800" : ""}`}
                >
                  <div className="text-[clamp(1.25rem,4vh,2.25rem)] font-bold text-slate-100 leading-none">
                    {ac.side_number ?? ac.bureau_number}
                  </div>
                  <div className={`text-base font-bold mt-1 ${STATUS_TEXT_COLOR[ac.status]}`}>
                    {ac.status}
                  </div>
                </div>
              ))}
              {sortedAircraft.length === 0 && (
                <div className="flex-1 flex items-center justify-center text-slate-600 text-xl">
                  No aircraft data
                </div>
              )}
            </div>
          </div>

        </div>
      </div>
    </BoardLayout>
  );
}
