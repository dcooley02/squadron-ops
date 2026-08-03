import { useState } from "react";
import { CheckCircle } from "lucide-react";
import { differenceInDays, parseISO } from "date-fns";
import type { AircraftInspection } from "../../lib/api";
import Badge from "../../components/Badge";
import { formatDate } from "../../lib/dates";
import RecordInspectionModal from "./RecordInspectionModal";

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

export default function InspectionSection({
  inspections,
  aircraftId,
  currentHours,
}: {
  inspections: AircraftInspection[];
  aircraftId: number;
  currentHours: number;
}) {
  return (
    <div className="card">
      <h2 className="mb-3">Inspections</h2>
      {inspections.length === 0 ? (
        <p className="text-sm text-slate-500">No inspection records.</p>
      ) : (
        <div>
          {inspections.map((insp) => (
            <InspectionRow
              key={insp.id}
              insp={insp}
              aircraftId={aircraftId}
              currentHours={currentHours}
            />
          ))}
        </div>
      )}
    </div>
  );
}
