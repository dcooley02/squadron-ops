import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import {
  patchDiscrepancy,
  type Discrepancy,
  type DiscrepancyWorkStatus,
} from "../../lib/api";
import { WS_LABEL } from "./statusHelpers";
import Overlay from "./Overlay";

export default function UpdateDiscrepancyModal({
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
