import { useQuery } from "@tanstack/react-query";
import { format } from "date-fns";
import clsx from "clsx";
import {
  fetchDashboardSummary,
  fetchAircraft,
  type AircraftStatus,
} from "../lib/api";
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
      <div className="relative w-64 h-64">
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
          <span className={clsx("text-5xl font-black tabular-nums", color)}>
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

  const sortedAircraft = [...(aircraft ?? [])].sort((a, b) =>
    (a.side_number ?? "").localeCompare(b.side_number ?? "")
  );

  const expiring = dashboard?.currencies_expiring_14d_count ?? 0;
  const expired = dashboard?.currencies_expired_count ?? 0;
  const openDiscrepancies = dashboard?.open_discrepancies_count ?? 0;

  return (
    <BoardLayout boardName="READINESS BOARD" lastUpdatedAt={dataUpdatedAt}>
      <div className="flex flex-col h-full overflow-hidden">

        {/* Header */}
        <div className="shrink-0 px-8 py-3 border-b border-slate-800 flex items-baseline justify-between">
          <h2 className="text-3xl font-bold uppercase tracking-wide text-slate-100">
            Squadron Readiness
          </h2>
          <span className="text-xl text-slate-400 font-medium">
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
            <div className="flex flex-col justify-center px-10 py-4 gap-4">
              <div className="text-base font-bold uppercase tracking-widest text-slate-500">
                Personnel
              </div>
              <div className="flex gap-8 items-end">
                <div>
                  <div className="text-8xl font-black text-slate-100 leading-none tabular-nums">
                    {dashboard?.total_personnel ?? "—"}
                  </div>
                  <div className="text-xl text-slate-400 mt-2">Total</div>
                </div>
                <div>
                  <div className="text-7xl font-black text-blue-400 leading-none tabular-nums">
                    {dashboard?.total_pilots ?? "—"}
                  </div>
                  <div className="text-xl text-slate-400 mt-2">Pilots</div>
                </div>
                <div>
                  <div className="text-7xl font-black text-blue-300 leading-none tabular-nums">
                    {dashboard?.total_aircrew ?? "—"}
                  </div>
                  <div className="text-xl text-slate-400 mt-2">Aircrew</div>
                </div>
              </div>
            </div>

            {/* 30-day activity */}
            <div className="flex flex-col justify-center px-10 py-4 gap-4">
              <div className="text-base font-bold uppercase tracking-widest text-slate-500">
                Last 30 Days
              </div>
              <div className="flex gap-10 items-end">
                <div>
                  <div className="text-8xl font-black text-slate-100 leading-none tabular-nums">
                    {dashboard?.sorties_last_30_days ?? "—"}
                  </div>
                  <div className="text-xl text-slate-400 mt-2">Sorties</div>
                </div>
                <div>
                  <div className="text-8xl font-black text-slate-100 leading-none tabular-nums">
                    {dashboard?.total_hours_last_30_days?.toFixed(0) ?? "—"}
                  </div>
                  <div className="text-xl text-slate-400 mt-2">Hours</div>
                </div>
              </div>
            </div>
          </div>

          {/* ROW 2 — Currency overview */}
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
                  "text-9xl font-black leading-none tabular-nums",
                  expiring > 0 ? "text-yellow-400" : "text-green-400"
                )}
              >
                {expiring}
              </div>
              <div className="text-xl text-slate-400 mt-3 uppercase tracking-wide font-semibold text-center px-6 leading-tight">
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
                  "text-9xl font-black leading-none tabular-nums",
                  expired > 0 ? "text-red-400" : "text-green-400"
                )}
              >
                {expired}
              </div>
              <div className="text-xl text-slate-400 mt-3 uppercase tracking-wide font-semibold">
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
                  "text-9xl font-black leading-none tabular-nums",
                  openDiscrepancies > 0 ? "text-yellow-400" : "text-green-400"
                )}
              >
                {dashboard ? openDiscrepancies : "—"}
              </div>
              <div className="text-xl text-slate-400 mt-3 uppercase tracking-wide font-semibold">
                Open Discrepancies
              </div>
            </div>
          </div>

          {/* ROW 3 — Aircraft status strip */}
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
                  <div className="text-4xl font-bold text-slate-100 leading-none">
                    {ac.side_number ?? ac.bureau_number}
                  </div>
                  <div className={`text-xl font-bold mt-2 ${STATUS_TEXT_COLOR[ac.status]}`}>
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
