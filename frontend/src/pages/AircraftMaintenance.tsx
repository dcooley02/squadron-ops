import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, CheckCircle, Plus, ShieldCheck, Wrench } from "lucide-react";
import { differenceInDays, parseISO } from "date-fns";
import {
  fetchAircraftDetail,
  fetchAircraftInspections,
  fetchAircraftDiscrepancies,
  fetchWorkCenters,
  fetchWorkOrders,
  fetchLogbook,
  createDiscrepancy,
  patchDiscrepancy,
  patchInspection,
  patchWorkOrder,
  qaSignoffWorkOrder,
  qaRelease,
  fetchReleaseForecast,
  type AircraftInspection,
  type Discrepancy,
  type WorkOrder,
  type WorkCenter,
  type LogbookEntry,
  type AircraftStatus,
  type DiscrepancySeverity,
  type DiscrepancyWorkStatus,
} from "../lib/api";
import Loading from "../components/Loading";
import Badge from "../components/Badge";
import { useToast } from "../components/Toast";
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

// ── QA release preview helpers (mirror backend compute_status rules) ────────

const NON_RELEASE: AircraftStatus[] = ["NMC", "NMCM", "NMCS"];

function previewComputedStatus(
  openDiscs: Discrepancy[],
  overdueDowningInspections: AircraftInspection[]
): AircraftStatus {
  if (openDiscs.some((d) => d.severity === "DOWNING" && d.work_status === "AWP")) return "NMCS";
  if (openDiscs.some((d) => d.severity === "DOWNING")) return "NMCM";
  if (overdueDowningInspections.length > 0) return "NMCM";
  if (openDiscs.some((d) => d.severity === "MAJOR")) return "PMC";
  return "FMC";
}

function collectReleaseBlockers(
  openDiscs: Discrepancy[],
  overdueDowningInspections: AircraftInspection[]
): string[] {
  const blockers: string[] = [];
  for (const d of openDiscs.filter((x) => x.severity === "DOWNING")) {
    blockers.push(`Open DOWNING discrepancy ${d.maf_number ?? `#${d.id}`}`);
  }
  for (const insp of overdueDowningInspections) {
    blockers.push(`Overdue downing inspection: ${insp.inspection_type.name}`);
  }
  const computed = previewComputedStatus(openDiscs, overdueDowningInspections);
  if (NON_RELEASE.includes(computed)) {
    blockers.push(`Computed status is ${computed} — not safe for flight until maintenance is complete`);
  }
  return blockers;
}

// ── Modal: QA Release ──────────────────────────────────────────────────────

function QaReleaseModal({
  ac,
  openDiscs,
  inspections,
  onClose,
  onReleased,
}: {
  ac: { id: number; status: AircraftStatus; computed_status: AircraftStatus; side_number: string | null };
  openDiscs: Discrepancy[];
  inspections: AircraftInspection[];
  onClose: () => void;
  onReleased: (side: string | null, from: AircraftStatus, to: AircraftStatus) => void;
}) {
  const qc = useQueryClient();
  const [qaNotes, setQaNotes] = useState("");
  const [correctiveAction, setCorrectiveAction] = useState("");
  const [closeIds, setCloseIds] = useState<Set<number>>(new Set());

  const overdueDowning = (inspections ?? []).filter(
    (i) => i.is_overdue && i.inspection_type.is_downing_when_overdue
  );
  const remainingOpen = openDiscs.filter((d) => !closeIds.has(d.id));
  const previewStatus = previewComputedStatus(remainingOpen, overdueDowning);
  const blockers = collectReleaseBlockers(remainingOpen, overdueDowning);
  const canSubmit = qaNotes.trim().length > 0 && blockers.length === 0;

  const mutation = useMutation({
    mutationFn: () =>
      qaRelease(ac.id, {
        qa_notes: qaNotes.trim(),
        close_discrepancy_ids: closeIds.size > 0 ? [...closeIds] : undefined,
        corrective_action: correctiveAction.trim() || undefined,
      }),
    onSuccess: (updated) => {
      qc.invalidateQueries({ queryKey: ["aircraft-detail", ac.id] });
      qc.invalidateQueries({ queryKey: ["aircraft-discrepancies", ac.id] });
      qc.invalidateQueries({ queryKey: ["aircraft-inspections", ac.id] });
      qc.invalidateQueries({ queryKey: ["aircraft"] });
      qc.invalidateQueries({ queryKey: ["dashboard-summary"] });
      onReleased(ac.side_number, ac.status, updated.status);
      onClose();
    },
  });

  const serverBlockers =
    mutation.isError &&
    mutation.error &&
    typeof mutation.error === "object" &&
    "response" in mutation.error &&
    mutation.error.response &&
    typeof mutation.error.response === "object" &&
    "data" in mutation.error.response &&
    mutation.error.response.data &&
    typeof mutation.error.response.data === "object" &&
    "detail" in mutation.error.response.data &&
    mutation.error.response.data.detail &&
    typeof mutation.error.response.data.detail === "object" &&
    "blockers" in mutation.error.response.data.detail
      ? (mutation.error.response.data.detail.blockers as string[])
      : null;

  const toggleClose = (id: number) => {
    setCloseIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  return (
    <Overlay onClose={onClose}>
      <h3 className="text-base font-semibold mb-1 flex items-center gap-2">
        <ShieldCheck size={18} className="text-green-400" />
        QA Release — Safe for Flight
      </h3>
      <p className="text-xs text-slate-400 mb-4">
        After QA signoff, release aircraft safe for flight at line status{" "}
        <span className="font-semibold text-slate-300">{ac.status}</span>
        {" → "}
        <span className="font-semibold text-slate-300">{previewStatus}</span>
        {ac.status !== previewStatus && (
          <span className="text-yellow-400 ml-1">(sync with computed)</span>
        )}
      </p>

      {blockers.length > 0 && (
        <div className="mb-4 p-2.5 bg-red-950/30 border border-red-800/40 rounded text-xs text-red-300 space-y-1">
          <div className="font-medium text-red-400">Release blocked — not safe for flight</div>
          {blockers.map((b) => (
            <div key={b}>• {b}</div>
          ))}
        </div>
      )}

      {openDiscs.length > 0 && (
        <div className="mb-4">
          <label className="block text-xs text-slate-400 mb-2">
            Close discrepancies with this release (optional)
          </label>
          <div className="space-y-2 max-h-40 overflow-y-auto">
            {openDiscs.map((d) => (
              <label
                key={d.id}
                className="flex items-start gap-2 p-2 rounded bg-slate-800/50 border border-slate-700/50 cursor-pointer"
              >
                <input
                  type="checkbox"
                  checked={closeIds.has(d.id)}
                  onChange={() => toggleClose(d.id)}
                  className="mt-0.5"
                />
                <div className="min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-mono text-xs text-slate-300">
                      {d.maf_number ?? `#${d.id}`}
                    </span>
                    <Badge variant={SEV_VARIANT[d.severity]}>{d.severity}</Badge>
                  </div>
                  <p className="text-xs text-slate-400 mt-0.5 line-clamp-2">{d.description}</p>
                </div>
              </label>
            ))}
          </div>
        </div>
      )}

      {closeIds.size > 0 && (
        <div className="mb-4">
          <label className="block text-xs text-slate-400 mb-1">
            Corrective action (applied to selected discrepancies)
          </label>
          <textarea
            value={correctiveAction}
            onChange={(e) => setCorrectiveAction(e.target.value)}
            rows={2}
            placeholder="Describe corrective action for closed items…"
            className="w-full bg-slate-800 border border-slate-700 rounded px-3 py-1.5 text-sm resize-none"
          />
        </div>
      )}

      <div className="mb-4">
        <label className="block text-xs text-slate-400 mb-1">QA signoff notes *</label>
        <textarea
          value={qaNotes}
          onChange={(e) => setQaNotes(e.target.value)}
          rows={3}
          placeholder="QA inspection complete, aircraft cleared for line operations…"
          className="w-full bg-slate-800 border border-slate-700 rounded px-3 py-1.5 text-sm resize-none"
        />
      </div>

      <div className="flex gap-2 justify-end">
        <button onClick={onClose} className="btn-secondary text-sm">
          Cancel
        </button>
        <button
          onClick={() => mutation.mutate()}
          disabled={mutation.isPending || !canSubmit}
          className="btn-primary text-sm"
        >
          {mutation.isPending ? "Processing…" : "Release for Flight"}
        </button>
      </div>

      {serverBlockers && (
        <div className="mt-3 text-xs text-red-400 space-y-1">
          {serverBlockers.map((b) => (
            <div key={b}>• {b}</div>
          ))}
        </div>
      )}
      {mutation.isError && !serverBlockers && (
        <p className="text-xs text-red-400 mt-2">Release failed. Check blockers and try again.</p>
      )}
    </Overlay>
  );
}

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
              {disc.type_wo_code && (
                <span
                  className="font-mono text-[10px] uppercase tracking-wide text-slate-300 bg-slate-800 border border-slate-700 rounded px-1 py-0.5"
                  title="CNAF M-4790.2 Type Work Order"
                >
                  WO·{disc.type_wo_code}
                </span>
              )}
              {disc.jcn && (
                <span
                  className="font-mono text-[10px] text-slate-400"
                  title="Job Control Number — CNAF M-4790.2"
                >
                  JCN {disc.jcn}
                </span>
              )}
              {disc.system_affected && (
                <span className="text-xs text-slate-400 font-mono">{disc.system_affected}</span>
              )}
              {disc.work_center_code && (
                <span className="text-xs text-slate-500">WC {disc.work_center_code}</span>
              )}
              {disc.has_qa_signoff && (
                <Badge variant="success" className="text-xs">QA signed</Badge>
              )}
            </div>
            {disc.reported_by_name && (
              <div className="text-xs text-slate-500 mt-0.5">Reported by {disc.reported_by_name}</div>
            )}
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

// ── Create discrepancy (line entry) ────────────────────────────────────────

function CreateDiscrepancyModal({
  aircraftId,
  onClose,
}: {
  aircraftId: number;
  onClose: () => void;
}) {
  const qc = useQueryClient();
  const { data: centers } = useQuery({
    queryKey: ["work-centers"],
    queryFn: fetchWorkCenters,
  });
  const [description, setDescription] = useState("");
  const [severity, setSeverity] = useState<DiscrepancySeverity>("MINOR");
  const [system, setSystem] = useState("");
  const [typeWo, setTypeWo] = useState("DM");
  const [workCenterId, setWorkCenterId] = useState<number | "">("");

  const mutation = useMutation({
    mutationFn: () =>
      createDiscrepancy(aircraftId, {
        description,
        severity,
        system_affected: system || undefined,
        type_wo_code: typeWo,
        work_center_id: workCenterId === "" ? undefined : workCenterId,
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["aircraft-discrepancies", aircraftId] });
      qc.invalidateQueries({ queryKey: ["aircraft-work-orders", aircraftId] });
      qc.invalidateQueries({ queryKey: ["aircraft-logbook", aircraftId] });
      qc.invalidateQueries({ queryKey: ["aircraft-detail", aircraftId] });
      onClose();
    },
  });

  return (
    <Overlay onClose={onClose}>
      <h3 className="text-base font-semibold mb-4">New Discrepancy</h3>
      <div className="space-y-3">
        <div>
          <label className="block text-xs text-slate-400 mb-1">Description *</label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            rows={3}
            className="w-full bg-slate-800 border border-slate-700 rounded px-3 py-1.5 text-sm resize-none"
          />
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-xs text-slate-400 mb-1">Severity</label>
            <select
              value={severity}
              onChange={(e) => setSeverity(e.target.value as DiscrepancySeverity)}
              className="w-full bg-slate-800 border border-slate-700 rounded px-3 py-1.5 text-sm"
            >
              <option value="MINOR">MINOR</option>
              <option value="MAJOR">MAJOR</option>
              <option value="DOWNING">DOWNING</option>
            </select>
          </div>
          <div>
            <label className="block text-xs text-slate-400 mb-1">Type WO</label>
            <input
              value={typeWo}
              onChange={(e) => setTypeWo(e.target.value.toUpperCase().slice(0, 2))}
              className="w-full bg-slate-800 border border-slate-700 rounded px-3 py-1.5 text-sm font-mono"
            />
          </div>
        </div>
        <div>
          <label className="block text-xs text-slate-400 mb-1">System affected</label>
          <input
            value={system}
            onChange={(e) => setSystem(e.target.value)}
            className="w-full bg-slate-800 border border-slate-700 rounded px-3 py-1.5 text-sm"
          />
        </div>
        <div>
          <label className="block text-xs text-slate-400 mb-1">Work center</label>
          <select
            value={workCenterId}
            onChange={(e) => setWorkCenterId(e.target.value ? Number(e.target.value) : "")}
            className="w-full bg-slate-800 border border-slate-700 rounded px-3 py-1.5 text-sm"
          >
            <option value="">Unassigned</option>
            {(centers ?? []).map((c: WorkCenter) => (
              <option key={c.id} value={c.id}>
                {c.code} — {c.name}
              </option>
            ))}
          </select>
        </div>
      </div>
      <div className="flex gap-2 justify-end mt-5">
        <button onClick={onClose} className="btn-secondary text-sm">Cancel</button>
        <button
          onClick={() => mutation.mutate()}
          disabled={mutation.isPending || !description.trim()}
          className="btn-primary text-sm"
        >
          {mutation.isPending ? "Creating…" : "Create MAF + WO"}
        </button>
      </div>
    </Overlay>
  );
}

function WorkOrderRow({ wo, aircraftId }: { wo: WorkOrder; aircraftId: number }) {
  const qc = useQueryClient();
  const { data: centers } = useQuery({ queryKey: ["work-centers"], queryFn: fetchWorkCenters });
  const [signoffNotes, setSignoffNotes] = useState("");

  const patchMut = useMutation({
    mutationFn: (body: { status?: DiscrepancyWorkStatus; work_center_id?: number }) =>
      patchWorkOrder(wo.id, body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["aircraft-work-orders", aircraftId] });
      qc.invalidateQueries({ queryKey: ["aircraft-discrepancies", aircraftId] });
      qc.invalidateQueries({ queryKey: ["aircraft-detail", aircraftId] });
    },
  });

  const signoffMut = useMutation({
    mutationFn: () => qaSignoffWorkOrder(wo.id, { notes: signoffNotes }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["aircraft-work-orders", aircraftId] });
      setSignoffNotes("");
    },
  });

  return (
    <div className="py-3 border-b border-slate-800 last:border-0 text-sm">
      <div className="flex items-center gap-2 flex-wrap">
        <span className="font-mono font-semibold text-slate-200">{wo.jcn}</span>
        <span className="font-mono text-xs text-slate-500">{wo.maf_number}</span>
        <Badge variant={WS_VARIANT[wo.status]}>{WS_LABEL[wo.status]}</Badge>
        {wo.work_center_code && (
          <span className="text-xs text-slate-400">{wo.work_center_code}</span>
        )}
        {wo.has_qa_signoff && (
          <Badge variant="success">QA signed</Badge>
        )}
      </div>
      <div className="flex flex-wrap gap-2 mt-2">
        <select
          value={wo.work_center_id ?? ""}
          onChange={(e) =>
            patchMut.mutate({
              work_center_id: e.target.value ? Number(e.target.value) : undefined,
            })
          }
          className="bg-slate-800 border border-slate-700 rounded px-2 py-1 text-xs"
        >
          <option value="">Route…</option>
          {(centers ?? []).map((c) => (
            <option key={c.id} value={c.id}>{c.code}</option>
          ))}
        </select>
        {(["IN_WORK", "AWP", "COMPLETED"] as DiscrepancyWorkStatus[]).map((s) => (
          <button
            key={s}
            onClick={() => patchMut.mutate({ status: s })}
            className="text-xs px-2 py-1 rounded border border-slate-700 hover:bg-slate-800"
          >
            {WS_LABEL[s]}
          </button>
        ))}
      </div>
      {!wo.has_qa_signoff && wo.status === "COMPLETED" && (
        <div className="mt-2 flex gap-2">
          <input
            value={signoffNotes}
            onChange={(e) => setSignoffNotes(e.target.value)}
            placeholder="QA signoff notes"
            className="flex-1 bg-slate-800 border border-slate-700 rounded px-2 py-1 text-xs"
          />
          <button
            onClick={() => signoffMut.mutate()}
            disabled={!signoffNotes.trim() || signoffMut.isPending}
            className="btn-secondary text-xs"
          >
            Sign off
          </button>
        </div>
      )}
    </div>
  );
}

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

      {/* QA Release */}
      <div
        className={`card ${statusDrift ? "border-green-800/40 bg-green-950/10" : ""}`}
      >
        <div className="flex items-start justify-between gap-4 flex-wrap">
          <div>
            <h2 className="flex items-center gap-2">
              <ShieldCheck size={18} className="text-green-400" />
              QA Release
            </h2>
            <p className="text-sm text-slate-400 mt-1">
              After QA signoff, release aircraft safe for flight and stamp line status to{" "}
              <Badge variant={STATUS_VARIANT[ac.computed_status]}>{ac.computed_status}</Badge>
            </p>
          </div>
          <button
            onClick={() => setReleaseOpen(true)}
            className="btn-primary text-sm flex items-center gap-1.5 shrink-0"
          >
            <ShieldCheck size={14} />
            {statusDrift && releaseReady ? "Release for Flight" : "QA Release"}
          </button>
        </div>

        {releaseBlockers.length > 0 ? (
          <div className="mt-3 p-2.5 bg-red-950/20 border border-red-800/30 rounded text-xs text-red-300 space-y-1">
            <div className="font-medium text-red-400">Not safe for flight — resolve:</div>
            {releaseBlockers.map((b) => (
              <div key={b}>• {b}</div>
            ))}
          </div>
        ) : statusDrift ? (
          <div className="mt-3 p-2.5 bg-green-950/20 border border-green-800/30 rounded text-xs text-green-300">
            Ready for QA release — stamped {ac.status} will update to {ac.computed_status}.
          </div>
        ) : (
          <div className="mt-3 text-xs text-slate-500">
            Stamped status matches computed. QA release available when maintenance state changes.
          </div>
        )}
        {releaseForecast?.projected_release_date && (
          <div className="mt-2 text-xs text-slate-400">
            Projected release: {releaseForecast.projected_release_date}
            {releaseForecast.blockers.length > 0 && (
              <span className="text-yellow-400"> · {releaseForecast.blockers.length} blocker(s)</span>
            )}
          </div>
        )}
      </div>

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

      {/* Work Orders */}
      <div className="card">
        <h2 className="mb-3">Work Orders (4790 chain)</h2>
        {(workOrders ?? []).filter((w) => w.status !== "CLOSED").length === 0 ? (
          <p className="text-sm text-slate-500">No open work orders.</p>
        ) : (
          (workOrders ?? [])
            .filter((w) => w.status !== "CLOSED")
            .map((wo) => <WorkOrderRow key={wo.id} wo={wo} aircraftId={id} />)
        )}
      </div>

      {/* C — Open Discrepancies */}
      <div className="card">
        <div className="flex items-center justify-between mb-3">
          <h2>
            Open Discrepancies
            {openDiscs.length > 0 && (
              <span className="ml-2 text-sm font-normal text-slate-400">
                ({openDiscs.length})
              </span>
            )}
          </h2>
          <button
            onClick={() => setCreateDiscOpen(true)}
            className="btn-secondary text-xs flex items-center gap-1"
          >
            <Plus size={12} /> New
          </button>
        </div>
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

      {createDiscOpen && (
        <CreateDiscrepancyModal aircraftId={id} onClose={() => setCreateDiscOpen(false)} />
      )}

      {/* Aircraft logbook */}
      <div className="card">
        <h2 className="mb-3">Aircraft Logbook</h2>
        {(logbook ?? []).length === 0 ? (
          <p className="text-sm text-slate-500">No logbook entries yet.</p>
        ) : (
          <div className="space-y-2">
            {(logbook ?? []).slice(0, 15).map((e: LogbookEntry) => (
              <div key={e.id} className="text-xs border-b border-slate-800 pb-2">
                <div className="flex items-center gap-2">
                  <Badge variant="neutral">{e.entry_type}</Badge>
                  <span className="text-slate-300 font-medium">{e.title}</span>
                  <span className="text-slate-500">{formatDate(e.entry_date)}</span>
                </div>
                {e.description && (
                  <p className="text-slate-500 mt-0.5 line-clamp-2">{e.description}</p>
                )}
              </div>
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
