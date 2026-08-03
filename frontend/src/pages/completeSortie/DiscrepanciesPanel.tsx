import type { Dispatch, SetStateAction } from "react";
import { Plus, Trash2 } from "lucide-react";
import { uid, type DiscrepancyRow, type Severity } from "./helpers";
import { Section } from "./Section";

type Props = {
  discRows: DiscrepancyRow[];
  setDiscRows: Dispatch<SetStateAction<DiscrepancyRow[]>>;
  discCompact: boolean;
  setDiscCompact: Dispatch<SetStateAction<boolean>>;
  downCount: number;
  majCount: number;
};

export default function DiscrepanciesPanel({
  discRows,
  setDiscRows,
  discCompact,
  setDiscCompact,
  downCount,
  majCount,
}: Props) {
  return (
    <Section
      title="Discrepancies"
      badge={
        discRows.length > 0 ? (
          <span className="text-xs text-slate-400">
            {discRows.length}
            {downCount > 0 && ` · ${downCount} DOWNING`}
            {majCount > 0 && ` · ${majCount} MAJOR`}
          </span>
        ) : null
      }
    >
      {/* Compact mode toggle */}
      <div className="flex items-center gap-3">
        <span className="text-xs text-slate-400">Compact mode</span>
        <button
          type="button"
          onClick={() => setDiscCompact((v) => !v)}
          className={`relative inline-flex h-5 w-9 rounded-full transition-colors shrink-0 ${
            discCompact ? "bg-blue-600" : "bg-slate-700"
          }`}
          aria-pressed={discCompact}
        >
          <span
            className={`absolute top-0.5 h-4 w-4 rounded-full bg-white shadow transition-transform ${
              discCompact ? "translate-x-4" : "translate-x-0.5"
            }`}
          />
        </button>
      </div>

      <div className="space-y-2">
        {discRows.map((row, i) => (
          <div key={row._key} className="p-3 bg-slate-800/40 rounded-lg space-y-2">
            <div className="flex gap-2">
              <textarea
                rows={2}
                placeholder="Description…"
                value={row.description}
                onChange={(e) =>
                  setDiscRows((prev) =>
                    prev.map((r, j) => (j === i ? { ...r, description: e.target.value } : r))
                  )
                }
                className="flex-1 bg-slate-800 border border-slate-700 rounded px-3 py-1.5 text-sm resize-none"
              />
              <div className="flex flex-col gap-2 shrink-0">
                <select
                  value={row.severity}
                  onChange={(e) =>
                    setDiscRows((prev) =>
                      prev.map((r, j) =>
                        j === i ? { ...r, severity: e.target.value as Severity } : r
                      )
                    )
                  }
                  className="bg-slate-800 border border-slate-700 rounded px-2 py-1.5 text-sm"
                >
                  {(["MINOR", "MAJOR", "DOWNING"] as Severity[]).map((s) => (
                    <option key={s} value={s}>{s}</option>
                  ))}
                </select>
                <button
                  type="button"
                  onClick={() => setDiscRows((prev) => prev.filter((_, j) => j !== i))}
                  className="text-slate-500 hover:text-red-400 self-center p-1"
                  title="Remove"
                >
                  <Trash2 size={14} />
                </button>
              </div>
            </div>
            {!discCompact && (
              <div className="grid grid-cols-2 gap-2">
                <input
                  type="text"
                  placeholder="System affected (e.g. AFCS)"
                  value={row.system_affected}
                  onChange={(e) =>
                    setDiscRows((prev) =>
                      prev.map((r, j) =>
                        j === i ? { ...r, system_affected: e.target.value } : r
                      )
                    )
                  }
                  className="bg-slate-800 border border-slate-700 rounded px-3 py-1.5 text-sm"
                />
                <input
                  type="text"
                  placeholder="Notes"
                  value={row.notes}
                  onChange={(e) =>
                    setDiscRows((prev) =>
                      prev.map((r, j) => (j === i ? { ...r, notes: e.target.value } : r))
                    )
                  }
                  className="bg-slate-800 border border-slate-700 rounded px-3 py-1.5 text-sm"
                />
              </div>
            )}
          </div>
        ))}
      </div>
      <button
        type="button"
        onClick={() =>
          setDiscRows((prev) => [
            ...prev,
            { _key: uid(), description: "", severity: "MINOR", system_affected: "", notes: "" },
          ])
        }
        className="flex items-center gap-1 text-sm text-blue-400 hover:text-blue-300"
      >
        <Plus size={14} /> Add Discrepancy
      </button>
    </Section>
  );
}
