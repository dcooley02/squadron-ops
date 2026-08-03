import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { ShieldCheck } from "lucide-react";
import {
  qaRelease,
  type AircraftInspection,
  type AircraftStatus,
  type Discrepancy,
} from "../../lib/api";
import Badge from "../../components/Badge";
import {
  SEV_VARIANT,
  previewComputedStatus,
  collectReleaseBlockers,
} from "./statusHelpers";
import Overlay from "./Overlay";

export default function QaReleaseModal({
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
