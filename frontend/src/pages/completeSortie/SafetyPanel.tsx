import type { Dispatch, SetStateAction } from "react";
import { Plus, Trash2 } from "lucide-react";
import { uid, type SafetyLevel, type SafetyRow } from "./helpers";
import { Section } from "./Section";

type Props = {
  safetyRows: SafetyRow[];
  setSafetyRows: Dispatch<SetStateAction<SafetyRow[]>>;
};

export default function SafetyPanel({ safetyRows, setSafetyRows }: Props) {
  return (
    <Section
      title="Safety Reports"
      badge={
        safetyRows.length > 0 ? (
          <span className="text-xs text-slate-400">{safetyRows.length}</span>
        ) : null
      }
    >
      <div className="space-y-2">
        {safetyRows.map((row, i) => (
          <div key={row._key} className="p-3 bg-slate-800/40 rounded-lg space-y-2">
            <div className="flex items-center gap-2">
              <select
                value={row.severity}
                onChange={(e) =>
                  setSafetyRows((prev) =>
                    prev.map((r, j) =>
                      j === i ? { ...r, severity: e.target.value as SafetyLevel } : r
                    )
                  )
                }
                className="bg-slate-800 border border-slate-700 rounded px-2 py-1.5 text-sm"
              >
                {(["INFO", "HAZARD", "INCIDENT", "MISHAP"] as SafetyLevel[]).map((s) => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>
              <input
                type="text"
                placeholder="Category (optional)"
                value={row.category}
                onChange={(e) =>
                  setSafetyRows((prev) =>
                    prev.map((r, j) => (j === i ? { ...r, category: e.target.value } : r))
                  )
                }
                className="flex-1 bg-slate-800 border border-slate-700 rounded px-3 py-1.5 text-sm"
              />
              <button
                type="button"
                onClick={() => setSafetyRows((prev) => prev.filter((_, j) => j !== i))}
                className="text-slate-500 hover:text-red-400 p-1"
                title="Remove"
              >
                <Trash2 size={14} />
              </button>
            </div>
            <textarea
              rows={2}
              placeholder="Description (required)…"
              value={row.description}
              onChange={(e) =>
                setSafetyRows((prev) =>
                  prev.map((r, j) => (j === i ? { ...r, description: e.target.value } : r))
                )
              }
              className="w-full bg-slate-800 border border-slate-700 rounded px-3 py-1.5 text-sm resize-none"
            />
            <input
              type="text"
              placeholder="Actions taken"
              value={row.actions_taken}
              onChange={(e) =>
                setSafetyRows((prev) =>
                  prev.map((r, j) => (j === i ? { ...r, actions_taken: e.target.value } : r))
                )
              }
              className="w-full bg-slate-800 border border-slate-700 rounded px-3 py-1.5 text-sm"
            />
          </div>
        ))}
      </div>
      <button
        type="button"
        onClick={() =>
          setSafetyRows((prev) => [
            ...prev,
            { _key: uid(), severity: "HAZARD", category: "", description: "", actions_taken: "" },
          ])
        }
        className="flex items-center gap-1 text-sm text-blue-400 hover:text-blue-300"
      >
        <Plus size={14} /> Add Safety Report
      </button>
    </Section>
  );
}
