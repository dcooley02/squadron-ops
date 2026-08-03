import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft } from "lucide-react";
import {
  fetchAircraftDetail,
  fetchAircraftInspections,
  fetchAircraftDiscrepancies,
  fetchWorkOrders,
  fetchLogbook,
  fetchReleaseForecast,
} from "../lib/api";
import Loading from "../components/Loading";
import Badge from "../components/Badge";
import { useToast } from "../components/Toast";
import {
  STATUS_VARIANT,
  collectReleaseBlockers,
} from "./aircraftMaintenance/statusHelpers";
import QaReleaseModal from "./aircraftMaintenance/QaReleaseModal";
import CreateDiscrepancyModal from "./aircraftMaintenance/CreateDiscrepancyModal";
import InspectionSection from "./aircraftMaintenance/InspectionSection";
import DiscrepancySection, {
  DiscrepancyHistorySection,
} from "./aircraftMaintenance/DiscrepancySection";
import WorkOrderSection from "./aircraftMaintenance/WorkOrderSection";
import LogbookSection from "./aircraftMaintenance/LogbookSection";
import ReleaseSection from "./aircraftMaintenance/ReleaseSection";

// ── Main page ──────────────────────────────────────────────────────────────

export default function AircraftMaintenance() {
  const { aircraftId } = useParams<{ aircraftId: string }>();
  const id = Number(aircraftId);
  const [releaseOpen, setReleaseOpen] = useState(false);
  const [createDiscOpen, setCreateDiscOpen] = useState(false);
  const { showToast } = useToast();

  const { data: ac, isLoading: acLoading } = useQuery({
    queryKey: ["aircraft-detail", id],
    queryFn: () => fetchAircraftDetail(id),
    enabled: !isNaN(id),
  });

  const { data: inspections, isLoading: inspLoading } = useQuery({
    queryKey: ["aircraft-inspections", id],
    queryFn: () => fetchAircraftInspections(id),
    enabled: !isNaN(id),
  });

  const { data: allDiscrepancies, isLoading: discLoading } = useQuery({
    queryKey: ["aircraft-discrepancies", id],
    queryFn: () => fetchAircraftDiscrepancies(id),
    enabled: !isNaN(id),
  });

  const { data: workOrders } = useQuery({
    queryKey: ["aircraft-work-orders", id],
    queryFn: () => fetchWorkOrders(id),
    enabled: !isNaN(id),
  });

  const { data: logbook } = useQuery({
    queryKey: ["aircraft-logbook", id],
    queryFn: () => fetchLogbook(id),
    enabled: !isNaN(id),
  });

  const { data: releaseForecast } = useQuery({
    queryKey: ["release-forecast", id],
    queryFn: () => fetchReleaseForecast(id),
    enabled: !isNaN(id),
  });

  if (acLoading || inspLoading || discLoading) return <Loading />;
  if (!ac) {
    return (
      <div className="card border-red-600/50 bg-red-950/20 text-red-300">
        Aircraft not found.
      </div>
    );
  }

  const openDiscs = (allDiscrepancies ?? []).filter((d) => d.work_status !== "CLOSED");
  const closedDiscs = (allDiscrepancies ?? []).filter((d) => d.work_status === "CLOSED");
  const statusDrift = ac.status !== ac.computed_status;
  const overdueDowning = (inspections ?? []).filter(
    (i) => i.is_overdue && i.inspection_type.is_downing_when_overdue
  );
  const releaseBlockers = collectReleaseBlockers(openDiscs, overdueDowning);
  const releaseReady = releaseBlockers.length === 0;

  return (
    <div className="space-y-5">
      <Link
        to="/maintenance"
        className="inline-flex items-center gap-1 text-sm text-slate-400 hover:text-slate-200"
      >
        <ArrowLeft size={14} /> Back to Maintenance
      </Link>

      {/* A — Header card */}
      <div className="card">
        <div className="flex items-start justify-between gap-4 flex-wrap">
          <div>
            <h1 className="flex items-center gap-3 flex-wrap">
              {ac.side_number ?? "—"}
              <Badge variant={STATUS_VARIANT[ac.computed_status]}>{ac.computed_status}</Badge>
              {statusDrift && (
                <span className="text-xs text-yellow-400 font-normal">
                  (stamped: {ac.status})
                </span>
              )}
            </h1>
            <div className="text-sm text-slate-400 mt-1">
              {ac.bureau_number} · {ac.type_model_series}
            </div>
          </div>
          <Link
            to={`/aircraft/${ac.id}`}
            className="text-xs text-slate-400 hover:text-slate-200"
          >
            Flight ops view →
          </Link>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-4 pt-4 border-t border-slate-800">
          <div>
            <div className="text-xs text-slate-500 uppercase tracking-wide">Total Hours</div>
            <div className="text-2xl font-semibold mt-0.5">
              {ac.total_airframe_hours.toFixed(1)}
            </div>
          </div>
          <div>
            <div className="text-xs text-slate-500 uppercase tracking-wide">Since Phase</div>
            <div className="text-2xl font-semibold mt-0.5">
              {ac.hours_since_phase.toFixed(1)}
            </div>
          </div>
          <div>
            <div className="text-xs text-slate-500 uppercase tracking-wide">Phase Interval</div>
            <div className="text-2xl font-semibold mt-0.5">{ac.phase_interval.toFixed(0)}h</div>
          </div>
          <div>
            <div className="text-xs text-slate-500 uppercase tracking-wide">Hours to Phase</div>
            <div
              className={`text-2xl font-semibold mt-0.5 ${ac.hours_to_phase < 50 ? "text-yellow-400" : ""}`}
            >
              {ac.hours_to_phase.toFixed(1)}
            </div>
          </div>
        </div>

        {statusDrift && (
          <div className="mt-3 p-2.5 bg-yellow-950/30 border border-yellow-800/40 rounded text-xs text-yellow-300">
            Stamped vs. computed: line shows{" "}
            <span className="font-semibold">{ac.status}</span> but system computes{" "}
            <span className="font-semibold">{ac.computed_status}</span> from open discrepancies
            and inspections. Update stamped status after QA signoff and release for flight.
          </div>
        )}
      </div>

      <ReleaseSection
        computedStatus={ac.computed_status}
        stampedStatus={ac.status}
        statusDrift={statusDrift}
        releaseBlockers={releaseBlockers}
        releaseReady={releaseReady}
        releaseForecast={releaseForecast}
        onOpenRelease={() => setReleaseOpen(true)}
      />

      {releaseOpen && (
        <QaReleaseModal
          ac={ac}
          openDiscs={openDiscs}
          inspections={inspections ?? []}
          onClose={() => setReleaseOpen(false)}
          onReleased={(side, from, to) =>
            showToast(
              `${side ?? "Aircraft"} released safe for flight — line status ${from} → ${to}`,
              "success"
            )
          }
        />
      )}

      <InspectionSection
        inspections={inspections ?? []}
        aircraftId={id}
        currentHours={ac.total_airframe_hours}
      />

      <WorkOrderSection workOrders={workOrders ?? []} aircraftId={id} />

      <DiscrepancySection
        openDiscs={openDiscs}
        onCreateClick={() => setCreateDiscOpen(true)}
      />

      {createDiscOpen && (
        <CreateDiscrepancyModal aircraftId={id} onClose={() => setCreateDiscOpen(false)} />
      )}

      <LogbookSection logbook={logbook ?? []} />

      <DiscrepancyHistorySection closedDiscs={closedDiscs} />
    </div>
  );
}
