import { useMemo } from "react";
import { useQuery, useQueries } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { format, parseISO, addHours, isAfter, isBefore } from "date-fns";
import {
  fetchDashboardSummary,
  fetchAircraft,
  fetchAircraftDetail,
  fetchUpcomingSorties,
  fetchSquadronReadiness,
  type AircraftDetail,
  type SortieSummary,
} from "../lib/api";
import { Users, Plane, AlertTriangle, Calendar, Clock, ArrowRight } from "lucide-react";
import MetricCard from "../components/MetricCard";
import RateRing from "../components/RateRing";
import Loading from "../components/Loading";
import Badge from "../components/Badge";
import TRatingBadge from "../components/TRatingBadge";

export default function Dashboard() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["dashboard-summary"],
    queryFn: fetchDashboardSummary,
  });

  const { data: aircraftList } = useQuery({
    queryKey: ["aircraft"],
    queryFn: () => fetchAircraft(),
  });

  const { data: upcomingSorties } = useQuery({
    queryKey: ["upcoming-sorties"],
    queryFn: fetchUpcomingSorties,
  });

  const { data: readiness } = useQuery({
    queryKey: ["squadron-readiness"],
    queryFn: fetchSquadronReadiness,
  });

  const detailQueries = useQueries({
    queries: (aircraftList ?? []).map((ac) => ({
      queryKey: ["aircraft-detail", ac.id],
      queryFn: () => fetchAircraftDetail(ac.id),
      enabled: !!aircraftList,
    })),
  });

  const next24hSorties = useMemo(() => {
    const now = new Date();
    const cutoff = addHours(now, 24);
    return (upcomingSorties ?? [])
      .filter((s): s is SortieSummary & { takeoff_time: string } => {
        if (!s.takeoff_time) return false;
        const t = parseISO(s.takeoff_time);
        return !isBefore(t, now) && !isAfter(t, cutoff);
      })
      .sort((a, b) => parseISO(a.takeoff_time).getTime() - parseISO(b.takeoff_time).getTime());
  }, [upcomingSorties]);

  if (isLoading) return <Loading message="Loading squadron status..." />;
  if (error || !data) {
    return (
      <div className="card border-red-600/50 bg-red-950/20 text-red-300">
        Failed to load dashboard data. Is the backend running on port 8001?
      </div>
    );
  }

  const details: AircraftDetail[] = detailQueries
    .map((q) => q.data)
    .filter(Boolean) as AircraftDetail[];

  const fmcCount = details.length > 0
    ? details.filter((a) => a.computed_status === "FMC").length
    : data.aircraft_fmc_count;
  const pmcCount = details.length > 0
    ? details.filter((a) => a.computed_status === "PMC").length
    : data.aircraft_pmc_count;
  const nmcmCount = details.filter((a) => a.computed_status === "NMCM").length;
  const nmcsCount = details.filter((a) => a.computed_status === "NMCS").length;
  const computedFmcRate = data.aircraft_total > 0
    ? (fmcCount / data.aircraft_total) * 100
    : 0;
  const stampedFmcRate = data.aircraft_total > 0
    ? (data.aircraft_fmc_count / data.aircraft_total) * 100
    : 0;

  const driftingAircraft = details.filter((a) => a.status !== a.computed_status);
  const driftCount = driftingAircraft.length;

  const expiringSoon = data.currencies_expiring_14d_count;
  const expired = data.currencies_expired_count;

  return (
    <div className="space-y-6">
      <div>
        <h1>Squadron Dashboard</h1>
        <p className="text-sm text-slate-400 mt-1">
          Morning brief — personnel, aircraft readiness, and today&apos;s schedule
        </p>
      </div>

      {/* Today's schedule — SDO quick-look */}
      <section className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wide">
            Next 24 Hours
          </h2>
          <Link
            to="/schedule"
            className="text-xs text-slate-500 hover:text-slate-300 flex items-center gap-1"
          >
            Full schedule <ArrowRight size={12} />
          </Link>
        </div>
        {next24hSorties.length === 0 ? (
          <div className="card text-sm text-slate-500 py-4">
            No sorties scheduled in the next 24 hours.
          </div>
        ) : (
          <div className="card divide-y divide-slate-800 p-0 overflow-hidden">
            {next24hSorties.map((s) => (
              <Link
                key={s.id}
                to={`/sorties/${s.id}`}
                className="flex items-center gap-4 px-4 py-3 hover:bg-slate-800/40 transition-colors"
              >
                <div className="text-sm font-mono text-slate-300 w-16 shrink-0">
                  {format(parseISO(s.takeoff_time), "HHmm")}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium text-slate-100 truncate">
                    {s.event_code ?? s.event_type ?? "Sortie"}
                  </div>
                  <div className="text-xs text-slate-500 truncate">
                    {s.event_type ?? "Mission"}
                    {s.duration_hours != null && ` · ${s.duration_hours.toFixed(1)} hr`}
                  </div>
                </div>
                <div className="text-xs text-slate-400 shrink-0">
                  {s.aircraft_side_number ? `#${s.aircraft_side_number}` : "TBD acft"}
                </div>
              </Link>
            ))}
          </div>
        )}
      </section>

      {/* Personnel section */}
      <section className="space-y-3">
        <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wide">
          Personnel
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <MetricCard
            label="Total Personnel"
            value={data.total_personnel}
            icon={<Users size={16} />}
          />
          <MetricCard label="Pilots" value={data.total_pilots} />
          <MetricCard label="Aircrew" value={data.total_aircrew} />
        </div>
      </section>

      {/* Aircraft readiness section */}
      <section className="space-y-3">
        <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wide">
          Aircraft Readiness
        </h2>
        <p className="text-xs text-slate-500">
          <span className="text-slate-400">Computed</span> reflects open discrepancies and
          inspections. <span className="text-slate-400">Stamped</span> is the line-maintainer
          status until QA release updates it.
        </p>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-3">
          <div className="card flex flex-col items-center justify-center gap-2 lg:row-span-1 py-6">
            <RateRing rate={computedFmcRate} label="Computed FMC" />
            <p className="text-xs text-slate-500">
              Stamped: {data.aircraft_fmc_count}/{data.aircraft_total} FMC
              {" "}({stampedFmcRate.toFixed(0)}%)
            </p>
          </div>
          <div className="grid grid-cols-2 gap-3 lg:col-span-2">
            <MetricCard
              label="Total Aircraft"
              value={data.aircraft_total}
              icon={<Plane size={16} />}
            />
            <MetricCard
              label="Computed FMC"
              value={fmcCount}
              variant="good"
            />
            <div className="col-span-2 grid grid-cols-3 gap-3">
              <MetricCard
                label="Computed PMC"
                value={pmcCount}
                variant={pmcCount > 0 ? "warning" : "default"}
              />
              <MetricCard
                label="Computed NMCM"
                value={nmcmCount}
                variant={nmcmCount > 0 ? "danger" : "default"}
              />
              <MetricCard
                label="Computed NMCS"
                value={nmcsCount}
                variant={nmcsCount > 0 ? "danger" : "default"}
              />
            </div>
          </div>
        </div>
        {data.open_discrepancies_count > 0 && (
          <MetricCard
            label="Open Discrepancies"
            value={data.open_discrepancies_count}
            sublabel="Outstanding maintenance items requiring action"
            variant="warning"
            icon={<AlertTriangle size={16} />}
          />
        )}
        {driftCount > 0 && (
          <Link to="/maintenance" className="block">
            <div className="card border-yellow-700/40 bg-yellow-950/20 space-y-2 py-3 hover:border-yellow-600/60 transition-colors cursor-pointer">
              <div className="flex items-center gap-3">
                <AlertTriangle size={16} className="text-yellow-400 shrink-0" />
                <span className="text-sm text-yellow-300">
                  Stamped vs. computed — {driftCount} aircraft awaiting QA release
                </span>
                <span className="ml-auto text-xs text-yellow-500 shrink-0">Maintenance →</span>
              </div>
              <p className="text-xs text-yellow-300/70 pl-7">
                Open discrepancies changed computed readiness; stamped status has not been updated
                yet. This is expected until QA signoff and release for flight.
              </p>
              <div className="pl-7 flex flex-wrap gap-2">
                {driftingAircraft.map((ac) => (
                  <span
                    key={ac.id}
                    className="text-xs text-yellow-200/80 flex items-center gap-1.5"
                  >
                    <span className="font-mono">{ac.side_number ?? ac.bureau_number}</span>
                    <Badge variant="neutral">{ac.status}</Badge>
                    <span className="text-slate-500">→</span>
                    <Badge variant={ac.computed_status === "FMC" ? "success" : "warning"}>
                      {ac.computed_status}
                    </Badge>
                  </span>
                ))}
              </div>
            </div>
          </Link>
        )}
      </section>

      {/* WTM capability readiness — distinct from B-2 currencies below */}
      {readiness && (
        <section className="space-y-3">
          <div className="flex items-center justify-between gap-3">
            <div>
              <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wide">
                Capability Readiness (WTM)
              </h2>
              <p className="text-xs text-slate-500 mt-0.5">
                T-ratings from anchor-task recency — not the same as Table B-2 currency counts.
              </p>
            </div>
            <Link
              to="/readiness"
              className="text-xs text-blue-400 hover:text-blue-300 shrink-0"
            >
              Full readiness board →
            </Link>
          </div>
          <div className="card flex flex-wrap items-center gap-4 py-3">
            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-500 uppercase">Squadron</span>
              <TRatingBadge rating={readiness.squadron_overall_rating} large />
            </div>
            <div className="flex flex-wrap gap-2">
              {readiness.areas.map((area) => (
                <div
                  key={area.capability_area}
                  className="flex items-center gap-1.5 rounded border border-slate-800 px-2 py-1"
                >
                  <span className="font-mono text-xs text-slate-500">{area.capability_area}</span>
                  <TRatingBadge rating={area.squadron_rating} />
                </div>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* Table B-2 currency status */}
      <section className="space-y-3">
        <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wide">
          Table B-2 Currencies
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <MetricCard
            label="Expiring within 14 days"
            value={expiringSoon}
            sublabel={expiringSoon > 0 ? "Crew at risk of going non-current" : "All current"}
            variant={expiringSoon > 0 ? "warning" : "good"}
            icon={<AlertTriangle size={16} />}
          />
          <MetricCard
            label="Already Expired"
            value={expired}
            sublabel={expired > 0 ? "Crew currently non-current — schedule recovery" : "All current"}
            variant={expired > 0 ? "danger" : "good"}
            icon={<AlertTriangle size={16} />}
          />
        </div>
      </section>

      {/* Activity section */}
      <section className="space-y-3">
        <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wide">
          30-Day Activity
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <MetricCard
            label="Sorties Flown"
            value={data.sorties_last_30_days}
            sublabel="Last 30 days"
            icon={<Calendar size={16} />}
          />
          <MetricCard
            label="Total Hours Flown"
            value={data.total_hours_last_30_days.toFixed(1)}
            sublabel="Last 30 days, all crew"
            icon={<Clock size={16} />}
          />
        </div>
      </section>
    </div>
  );
}