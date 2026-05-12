import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { X, UserPlus } from "lucide-react";
import { fetchEligibleCrew, assignCrew, type CrewPosition } from "../lib/api";
import Loading from "./Loading";

const POSITION_LABELS: Record<CrewPosition, string> = {
  HAC: "HAC",
  H2P: "H2P",
  H2P_U: "H2P (U/I)",
  CREW_CHIEF: "Crew Chief",
  AIRCREW: "Aircrew",
  AWS: "AWS",
};

interface Props {
  sortieId: number;
  crewPosition: CrewPosition;
  onClose: () => void;
}

export default function AssignCrewPanel({ sortieId, crewPosition, onClose }: Props) {
  const qc = useQueryClient();
  const [assigning, setAssigning] = useState<number | null>(null);

  const { data: candidates, isLoading } = useQuery({
    queryKey: ["eligible-crew", sortieId, crewPosition],
    queryFn: () => fetchEligibleCrew(sortieId, crewPosition),
  });

  async function handleAssign(personId: number) {
    setAssigning(personId);
    try {
      await assignCrew(sortieId, { person_id: personId, crew_position: crewPosition });
      qc.invalidateQueries({ queryKey: ["sortie-detail", sortieId] });
      qc.invalidateQueries({ queryKey: ["sortie-fitness", sortieId] });
      onClose();
    } finally {
      setAssigning(null);
    }
  }

  return (
    <>
      <div className="fixed inset-0 bg-black/50 z-40" onClick={onClose} />
      <div className="fixed right-0 top-0 h-full w-[400px] bg-slate-900 border-l border-slate-700 z-50 flex flex-col shadow-2xl">
        <div className="flex items-center justify-between px-4 py-3 border-b border-slate-800">
          <div>
            <div className="font-semibold text-slate-100">
              Assign {POSITION_LABELS[crewPosition]}
            </div>
            <div className="text-xs text-slate-400 mt-0.5">Ranked by priority</div>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-200 p-1">
            <X size={18} />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-4 space-y-2">
          {isLoading && <Loading message="Loading eligible crew..." />}
          {!isLoading && candidates?.length === 0 && (
            <p className="text-sm text-slate-500 text-center py-8">
              No eligible crew found for this position.
            </p>
          )}
          {candidates?.map((c) => (
            <div key={c.person_id} className="card flex items-start justify-between gap-3">
              <div className="flex-1 min-w-0">
                <div className="font-medium text-slate-100 text-sm">
                  {c.rank && <span className="text-slate-400 mr-1">{c.rank}</span>}
                  {c.last_name}, {c.first_name}
                  {c.callsign && (
                    <span className="text-slate-400 text-xs ml-1">"{c.callsign}"</span>
                  )}
                </div>
                <ul className="mt-1 space-y-0.5">
                  {c.reasons.map((r, i) => (
                    <li key={i} className="text-xs text-slate-400 flex items-start gap-1">
                      <span className="text-slate-500 mt-0.5 shrink-0">·</span>
                      <span>{r}</span>
                    </li>
                  ))}
                </ul>
              </div>
              <button
                onClick={() => handleAssign(c.person_id)}
                disabled={assigning !== null}
                className="shrink-0 flex items-center gap-1 text-xs px-3 py-1.5 rounded bg-blue-700 hover:bg-blue-600 text-white disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <UserPlus size={12} />
                {assigning === c.person_id ? "…" : "Assign"}
              </button>
            </div>
          ))}
        </div>
      </div>
    </>
  );
}
