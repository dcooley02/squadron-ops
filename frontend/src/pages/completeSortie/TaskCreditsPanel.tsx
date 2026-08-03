import type { Dispatch, SetStateAction } from "react";
import { Plus, Trash2 } from "lucide-react";
import { uid, type Grade, type TaskCreditRow } from "./helpers";
import { Section } from "./Section";

type CrewOption = {
  id: number;
  person_id: number;
  person_name: string;
};

type TaskOption = {
  id: number;
  code: string;
  is_active: boolean;
};

type Props = {
  taskRows: TaskCreditRow[];
  setTaskRows: Dispatch<SetStateAction<TaskCreditRow[]>>;
  crew: CrewOption[];
  activeTaskOpts: TaskOption[];
};

export default function TaskCreditsPanel({
  taskRows,
  setTaskRows,
  crew,
  activeTaskOpts,
}: Props) {
  return (
    <Section
      title="Task Credits"
      badge={
        taskRows.length > 0 ? (
          <span className="text-xs text-slate-400">{taskRows.length}</span>
        ) : null
      }
    >
      <div className="space-y-2">
        {taskRows.map((row, i) => (
          <div key={row._key} className="flex items-center gap-2 flex-wrap">
            <select
              value={row.person_id}
              onChange={(e) =>
                setTaskRows((prev) =>
                  prev.map((r, j) => (j === i ? { ...r, person_id: e.target.value } : r))
                )
              }
              className="bg-slate-800 border border-slate-700 rounded px-2 py-1.5 text-sm flex-1 min-w-0"
            >
              <option value="">Person…</option>
              {crew.map((fl) => (
                <option key={fl.id} value={fl.person_id}>
                  {fl.person_name}
                </option>
              ))}
            </select>
            <select
              value={row.task_code}
              onChange={(e) =>
                setTaskRows((prev) =>
                  prev.map((r, j) => (j === i ? { ...r, task_code: e.target.value } : r))
                )
              }
              className="bg-slate-800 border border-slate-700 rounded px-2 py-1.5 text-sm flex-1 min-w-0"
            >
              <option value="">Task code…</option>
              {activeTaskOpts.map((o) => (
                <option key={o.id} value={o.code}>
                  {o.code}
                </option>
              ))}
            </select>
            <select
              value={row.grade}
              onChange={(e) =>
                setTaskRows((prev) =>
                  prev.map((r, j) =>
                    j === i ? { ...r, grade: e.target.value as Grade } : r
                  )
                )
              }
              className="bg-slate-800 border border-slate-700 rounded px-2 py-1.5 text-sm w-20"
            >
              {(["Q", "CQ", "U", "NO", "NG"] as Grade[]).map((g) => (
                <option key={g} value={g}>{g}</option>
              ))}
            </select>
            <button
              type="button"
              onClick={() => setTaskRows((prev) => prev.filter((_, j) => j !== i))}
              className="text-slate-500 hover:text-red-400 p-1"
              title="Remove"
            >
              <Trash2 size={14} />
            </button>
          </div>
        ))}
      </div>
      <button
        type="button"
        onClick={() =>
          setTaskRows((prev) => [
            ...prev,
            { _key: uid(), person_id: "", task_code: "", grade: "Q", remarks: "" },
          ])
        }
        className="flex items-center gap-1 text-sm text-blue-400 hover:text-blue-300"
      >
        <Plus size={14} /> Add Task Credit
      </button>
    </Section>
  );
}
