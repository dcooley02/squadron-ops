import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { patchInspection, type AircraftInspection } from "../../lib/api";
import Overlay from "./Overlay";

export default function RecordInspectionModal({
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
