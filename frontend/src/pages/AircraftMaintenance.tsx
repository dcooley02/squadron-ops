import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, CheckCircle, Wrench } from "lucide-react";
import { differenceInDays, parseISO } from "date-fns";
import {
  fetchAircraftDetail,
  fetchAircraftInspections,
  fetchAircraftDiscrepancies,
  patchDiscrepancy,
  patchInspection,
  type AircraftInspection,
  type Discrepancy,
  type AircraftStatus,
  type DiscrepancySeverity,
  type DiscrepancyWorkStatus,
} from "../lib/api";
import Loading from "../components/Loading";
import Badge from "../components/Badge";
import { formatDate } from "../lib/dates";

// ── Status display helpers ──────────────────────────────────────────────────

const STATUS_VARIANT: Record<AircraftStatus, "success" | "warning" | "danger" | "neutral"> = {
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

// ── Modal: Record Inspection Completion ────────────────────────────────────

function RecordInspectionModal({
  insp,
  aircraftId,
  currentHours,
  onClose,
}: {
  insp: AircraftInspection;
  aircraftId: number;
  currentHours: number;
  onClose: () => void;
}) {
  const qc = useQueryClient();
  const d = new Date();
  const today = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
  const [completedDate, setCompletedDate] = useState(today);
  const [completedHours, setCompletedHours] = useState(
    insp.inspection_type.periodicity_hours != null ? String(currentHours) : ""
  );
  const [notes, setNotes] = useState("");

  const mutation = useMutation({
    mutationFn: () =>
      patchInspection(aircraftId, insp.id, {
        last_completed_date: completedDate,
        last_completed_hours:
          completedHours !== "" ? parseFloat(completedHours) : undefined,
        last_completion_notes: notes || undefined,
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["aircraft-inspections", aircraftId] });
      qc.invalidateQueries({ queryKey: ["aircraft-detail", aircraftId] });
      onClose();
    },
  });

  return (
    <Overlay onClose={onClose}>
      <h3 className="text-base font-semibold mb-4">
        Record Completion — {insp.inspection_type.name}
      </h3>
      <div className="space-y-3">
        <div>
          <label className="block text-xs text-slate-400 mb-1">Completion Date *</label>
          <input
            type="date"
            value={completedDate}
            onChange={(e) => setCompletedDate(e.target.value)}
            className="w-full bg-slate-800 border border-slate-700 rounded px-3 py-1.5 text-sm"
          />
        </div>
        {insp.inspection_type.periodicity_hours != null && (
          <div>
            <label className="block text-xs text-slate-400 mb-1">
              Airframe Hours at Completion *
            </label>
            <input
              type="number"
              step="0.1"
              value={completedHours}
              onChange={(e) => setCompletedHours(e.target.value)}
              className="w-full bg-slate-800 border border-slate-700 rounded px-3 py-1.5 text-sm"
            />
          </div>
        )}
        <div>
          <label className="block text-xs text-slate-400 mb-1">Notes (optional)</label>
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            rows={2}
            className="w-full bg-slate-800 border border-slate-700 rounded px-3 py-1.5 text-sm resize-none"
          />
        </div>
      </div>
      <div className="flex gap-2 justify-end mt-5">
        <button onClick={onClose} className="btn-secondary text-sm">
          Cancel
        </button>
        <button
          onClick={() => mutation.mutate()}
          disabled={mutation.isPending || !completedDate}
          className="btn-primary text-sm"
        >
          {mutation.isPending ? "Saving…" : "Save Completion"}
        </button>
      </div>
      {mutation.isError && (
        <p className="text-xs text-red-400 mt-2">Failed to save. Try again.</p>
      )}
    </Overlay>
  );
}

// ── Modal: Update Discrepancy Status ───────────────────────────────────────

function UpdateDiscrepancyModal({
  disc,
  onClose,
}: {
  disc: Discrepancy;
  onClose: () => void;
}) {
  const qc = useQueryClient();
  const [workStatus, setWorkStatus] = useState<DiscrepancyWorkStatus>(disc.work_status);
  const [correctiveAction, setCorrectiveAction] = useState(disc.corrective_action ?? "");
  const [systemAffected, setSystemAffected] = useState(disc.system_affected ?? "");

  const isClosingWithoutAction = workStatus === "CLOSED" && correctiveAction.trim() === "";

  const mutation = useMutation({
    mutationFn: () =>
      patchDiscrepancy(disc.id, {
        work_status: workStatus,
        corrective_action: correctiveAction || undefined,
        system_affected: systemAffected || undefined,
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["aircraft-discrepancies", disc.aircraft_id] });
      qc.invalidateQueries({ queryKey: ["aircraft-detail", disc.aircraft_id] });
      onClose();
    },
  });

  const WS_OPTIONS: DiscrepancyWorkStatus[] = [
    "OPEN", "IN_WORK", "AWP", "AWM", "COMPLETED", "CLOSED",
  ];

  return (
    <Overlay onClose={onClose}>
      <h3 className="text-base font-semibold mb-1">Update Discrepancy</h3>
      <p className="text-xs text-slate-400 font-mono mb-4">{disc.maf_number ?? `ID ${disc.id}`}</p>
      <div className="space-y-3">
        <div>
          <label className="block text-xs text-slate-400 mb-1">Work Status</label>
          <select
            value={workStatus}
            onChange={(e) => setWorkStatus(e.target.value as DiscrepancyWorkStatus)}
            className="w-full bg-slate-800 border border-slate-700 rounded px-3 py-1.5 text-sm"
          >
            {WS_OPTIONS.map((s) => (
              <option key={s} value={s}>{WS_LABEL[s]}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-xs text-slate-400 mb-1">System Affected</label>
          <input
            type="text"
            value={systemAffected}
            onChange={(e) => setSystemAffected(e.target.value)}
            placeholder="e.g. AFCS, XMSN"
            className="w-full bg-slate-800 border border-slate-700 rounded px-3 py-1.5 text-sm"
          />
        </div>
        <div>
          <label className="block text-xs text-slate-400 mb-1">Corrective Action</label>
          <textarea
            value={correctiveAction}
            onChange={(e) => setCorrectiveAction(e.target.value)}
            rows={3}
            placeholder="Describe corrective action taken…"
            className="w-full bg-slate-800 border border-slate-700 rounded px-3 py-1.5 text-sm resize-none"
          />
        </div>
        {isClosingWithoutAction && (
          <p className="text-xs text-yellow-400">
            Corrective action recommended before closing.
          </p>
        )}
      </div>
      <div className="flex gap-2 justify-end mt-5">
        <button onClick={onClose} className="btn-secondary text-sm">
          Cancel
        </button>
        <button
          onClick={() => mutation.mutate()}
          disabled={mutation.isPending}
          className="btn-primary text-sm"
        >
          {mutation.isPending ? "Saving…" : "Save"}
        </button>
      </div>
      {mutation.isError && (
        <p className="text-xs text-red-400 mt-2">Failed to save. Try again.</p>
      )}
    </Overlay>
  );
}

// ── Shared modal overlay wrapper ───────────────────────────────────────────

function Overlay({ children, onClose }: { children: React.ReactNode; onClose: () => void }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
      <div
        className="absolute inset-0"
        onClick={onClose}
        aria-hidden="true"
      />
      <div className="relative z-10 bg-slate-900 border border-slate-700 rounded-xl p-6 w-full max-w-md shadow-2xl">
        {children}
      </div>
    </div>
  );
}

// ── Inspection row ─────────────────────────────────────────────────────────

function InspectionRow({
  insp,
  aircraftId,
  currentHours,
}: {
  insp: AircraftInspection;
  aircraftId: number;
  currentHours: number;
}) {
  const [modalOpen, setModalOpen] = useState(false);
  const it = insp.inspection_type;

  const overdueLabel = (() => {
    if (!insp.is_overdue) return null;
    if (insp.next_due_date) {
      const days = Math.abs(differenceInDays(new Date(), parseISO(insp.next_due_date)));
      return `OVERDUE ${days}d`;
    }
    if (insp.next_due_hours != null) {
      const hrs = (currentHours - insp.next_due_hours).toFixed(0);
      return `OVERDUE ${hrs} hrs`;
    }
    return "OVERDUE";
  })();

  return (
    <>
      <div className="flex items-start justify-between gap-4 py-3 border-b border-slate-800 last:border-0">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-sm font-medium text-slate-200">{it.name}</span>
            <span className="text-xs text-slate-500 font-mono">({it.code})</span>
            {it.is_downing_when_overdue && (
              <Badge variant="danger" className="text-xs">Downing if overdue</Badge>
            )}
            {overdueLabel && (
              <Badge variant="danger">{overdueLabel}</Badge>
            )}
          </div>
          <div className="grid grid-cols-2 gap-x-6 mt-1.5 text-xs text-slate-500">
            <div>
              <span className="text-slate-600">Last completed: </span>
              {insp.last_completed_date
                ? formatDate(insp.last_completed_date)
                : "—"}
              {insp.last_completed_hours != null && (
                <span className="ml-1 text-slate-600">
                  @ {insp.last_completed_hours.toFixed(1)}h
                </span>
              )}
            </div>
            <div>
              <span className="text-slate-600">Next due: </span>
              {insp.next_due_date
                ? formatDate(insp.next_due_date)
                : insp.next_due_hours != null
                ? `${insp.next_due_hours.toFixed(1)}h`
                : "—"}
            </div>
          </div>
          {insp.last_completion_notes && (
            <div className="text-xs text-slate-600 mt-1 italic">{insp.last_completion_notes}</div>
          )}
        </div>
        <button
          onClick={() => setModalOpen(true)}
          className="btn-secondary text-xs shrink-0 flex items-center gap-1"
        >
          <CheckCircle size={12} />
          Record
        </button>
      </div>

      {modalOpen && (
        <RecordInspectionModal
          insp={insp}
          aircraftId={aircraftId}
          currentHours={currentHours}
          onClose={() => setModalOpen(false)}
        />
      )}
    </>
  );
}

// ── Discrepancy row ────────────────────────────────────────────────────────

function DiscrepancyRow({ disc, showHistory }: { disc: Discrepancy; showHistory?: boolean }) {
  const [modalOpen, setModalOpen] = useState(false);

  return (
    <>
      <div className="py-3 border-b border-slate-800 last:border-0">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              {disc.maf_number && (
                <span className="font-mono text-sm font-semibold text-slate-200">
                  {disc.maf_number}
                </span>
              )}
              <Badge variant={SEV_VARIANT[disc.severity]}>{disc.severity}</Badge>
              <Badge variant={WS_VARIANT[disc.work_status]}>
                {WS_LABEL[disc.work_status]}
              </Badge>
              {disc.system_affected && (
                <span className="text-xs text-slate-400 font-mono">{disc.system_affected}</span>
              )}
            </div>
            <p className="text-sm text-slate-300 mt-1">{disc.description}</p>
            <div className="flex items-center gap-3 mt-1 text-xs text-slate-500">
              <span>Opened {formatDate(disc.opened_date)}</span>
              {disc.sortie_id && (
                <Link
                  to={`/sorties/${disc.sortie_id}`}
                  className="text-blue-400 hover:text-blue-300"
                >
                  Sortie #{disc.sortie_id}
                </Link>
              )}
              {disc.closed_date && (
                <span>Closed {formatDate(disc.closed_date)}</span>
              )}
            </div>
            {showHistory && disc.corrective_action && (
              <div className="mt-2 p-2 bg-slate-800/50 rounded text-xs text-slate-400">
                <span className="text-slate-500">Corrective action: </span>
                {disc.corrective_action}
              </div>
            )}
          </div>
          {!showHistory && (
            <button
              onClick={() => setModalOpen(true)}
              className="btn-secondary text-xs shrink-0 flex items-center gap-1"
            >
              <Wrench size={12} />
              Update
            </button>
          )}
        </div>
      </div>

      {modalOpen && (
        <UpdateDiscrepancyModal disc={disc} onClose={() => setModalOpen(false)} />
      )}
    </>
  );
}

// ── Main page ──────────────────────────────────────────────────────────────

export default function AircraftMaintenance() {
  const { aircraftId } = useParams<{ aircraftId: string }>();
  const id = Number(aircraftId);

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
            Status drift detected: aircraft is stamped{" "}
            <span className="font-semibold">{ac.status}</span> but computed status is{" "}
            <span className="font-semibold">{ac.computed_status}</span>. Review open discrepancies
            and overdue inspections below.
          </div>
        )}
      </div>

      {/* B — Inspections */}
      <div className="card">
        <h2 className="mb-3">Inspections</h2>
        {(inspections ?? []).length === 0 ? (
          <p className="text-sm text-slate-500">No inspection records.</p>
        ) : (
          <div>
            {(inspections ?? []).map((insp) => (
              <InspectionRow
                key={insp.id}
                insp={insp}
                aircraftId={id}
                currentHours={ac.total_airframe_hours}
              />
            ))}
          </div>
        )}
      </div>

      {/* C — Open Discrepancies */}
      <div className="card">
        <h2 className="mb-3">
          Open Discrepancies
          {openDiscs.length > 0 && (
            <span className="ml-2 text-sm font-normal text-slate-400">
              ({openDiscs.length})
            </span>
          )}
        </h2>
        {openDiscs.length === 0 ? (
          <p className="text-sm text-slate-500">No open discrepancies.</p>
        ) : (
          <div>
            {openDiscs.map((d) => (
              <DiscrepancyRow key={d.id} disc={d} />
            ))}
          </div>
        )}
      </div>

      {/* D — Discrepancy History */}
      <div className="card">
        <h2 className="mb-3 text-slate-400">
          Discrepancy History
          {closedDiscs.length > 0 && (
            <span className="ml-2 text-sm font-normal text-slate-500">
              ({closedDiscs.length} closed)
            </span>
          )}
        </h2>
        {closedDiscs.length === 0 ? (
          <p className="text-sm text-slate-500">No closed discrepancies on record.</p>
        ) : (
          <div>
            {closedDiscs.map((d) => (
              <DiscrepancyRow key={d.id} disc={d} showHistory />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
