import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  createDiscrepancy,
  fetchWorkCenters,
  type DiscrepancySeverity,
  type WorkCenter,
} from "../../lib/api";
import Overlay from "./Overlay";

export default function CreateDiscrepancyModal({
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
