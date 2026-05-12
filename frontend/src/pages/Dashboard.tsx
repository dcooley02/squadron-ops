import { useQuery, useQueries } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { fetchDashboardSummary, fetchAircraft, fetchAircraftDetail, type AircraftDetail } from "../lib/api";
import { Users, Plane, AlertTriangle, Calendar, Clock } from "lucide-react";
import MetricCard from "../components/MetricCard";
import RateRing from "../components/RateRing";
import Loading from "../components/Loading";

export default function Dashboard() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["dashboard-summary"],
    queryFn: fetchDashboardSummary,
  });

  const { data: aircraftList } = useQuery({
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

  if (isLoading) return <Loading message="Loading squadron status..." />;
  if (error || !data) {
    return (
      <div className="card border-red-600/50 bg-red-950/20 text-red-300">
        Failed to load dashboard data. Is the backend running on port 8000?
      </div>
    );
  }

  const details: AircraftDetail[] = detailQueries
    .map((q) => q.data)
    .filter(Boolean) as AircraftDetail[];

  // Counts from computed_status (falls back to dashboard summary until details load)
  const fmcCount = details.length > 0
    ? details.filter((a) => a.computed_status === "FMC").length
    : data.aircraft_fmc_count;
  const pmcCount = details.length > 0
    ? details.filter((a) => a.computed_status === "PMC").length
    : data.aircraft_pmc_count;
  const nmcCount = details.length > 0
    ? details.filter((a) => a.computed_status === "NMC" || a.computed_status === "NMCM" || a.computed_status === "NMCS").length
    : data.aircraft_nmc_count;
  const nmcmCount = details.filter((a) => a.computed_status === "NMCM").length;
  const nmcsCount = details.filter((a) => a.computed_status === "NMCS").length;
  const computedFmcRate = data.aircraft_total > 0
    ? (fmcCount / data.aircraft_total) * 100
    : 0;

  const driftCount = details.filter((a) => a.status !== a.computed_status).length;

  const expiringSoon = data.currencies_expiring_14d_count;
  const expired = data.currencies_expired_count;

  return (
    <div className="space-y-6">
      <div>
        <h1>Squadron Dashboard</h1>
        <p className="text-sm text-slate-400 mt-1">
          Real-time readiness across personnel, aircraft, and currency
        </p>
      </div>

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
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-3">
          <div className="card flex items-center justify-center lg:row-span-1">
            <RateRing rate={computedFmcRate} label="FMC Rate" />
          </div>
          <div className="grid grid-cols-2 gap-3 lg:col-span-2">
            <MetricCard
              label="Total Aircraft"
              value={data.aircraft_total}
              icon={<Plane size={16} />}
            />
            <MetricCard
              label="Fully Mission Capable"
              value={fmcCount}
              variant="good"
            />
            <div className="col-span-2 grid grid-cols-3 gap-3">
              <MetricCard
                label="Partially Mission Capable"
                value={pmcCount}
                variant={pmcCount > 0 ? "warning" : "default"}
              />
              <MetricCard
                label="NMCM (Maintenance)"
                value={nmcmCount}
                variant={nmcmCount > 0 ? "danger" : "default"}
              />
              <MetricCard
                label="NMCS (Supply)"
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
            <div className="card border-yellow-700/40 bg-yellow-950/20 flex items-center gap-3 py-3 hover:border-yellow-600/60 transition-colors cursor-pointer">
              <AlertTriangle size={16} className="text-yellow-400 shrink-0" />
              <span className="text-sm text-yellow-300">
                {driftCount} aircraft with status drift — stamped status doesn't match computed
                reality
              </span>
              <span className="ml-auto text-xs text-yellow-500">View in Maintenance →</span>
            </div>
          </Link>
        )}
      </section>

      {/* Currency status section */}
      <section className="space-y-3">
        <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wide">
          Currency Status
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