import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { format, parseISO } from "date-fns";
import {
  MoreHorizontal,
  Plus,
  Trash2,
  AlertTriangle,
  CheckCircle2,
  AlertCircle,
  XCircle,
} from "lucide-react";
import {
  fetchSortie,
  fetchSortieFitness,
  removeCrew,
  deleteSortie,
  type SortieSummary,
  type CrewPosition,
} from "../lib/api";
import AssignCrewPanel from "./AssignCrewPanel";
import Badge from "./Badge";

const REQUIRED_POSITIONS: CrewPosition[] = ["HAC", "CREW_CHIEF"];
const OPTIONAL_POSITIONS: CrewPosition[] = ["H2P", "H2P_U", "AIRCREW", "AWS"];

const POSITION_LABELS: Record<CrewPosition, string> = {
  HAC: "HAC",
  H2P: "H2P",
  H2P_U: "H2P (U/I)",
  CREW_CHIEF: "Crew Chief",
  AIRCREW: "Aircrew",
  AWS: "AWS",
};

const FITNESS_BORDER: Record<string, string> = {
  green: "border-l-green-500",
  yellow: "border-l-yellow-400",
  red: "border-l-red-500",
};

function FitnessIcon({ status }: { status: string }) {
  if (status === "red") return <XCircle size={14} className="text-red-400" />;
  if (status === "yellow") return <AlertCircle size={14} className="text-yellow-400" />;
  return <CheckCircle2 size={14} className="text-green-400" />;
}

interface Props {
  sortieId: number;
  sortieSummary: SortieSummary;
  onDeleted: () => void;
}

export default function SortieTile({ sortieId, sortieSummary: summary, onDeleted }: Props) {
  const qc = useQueryClient();
  const [assignPanel, setAssignPanel] = useState<CrewPosition | null>(null);
  const [showAddMenu, setShowAddMenu] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [removing, setRemoving] = useState<number | null>(null);
  const [deleting, setDeleting] = useState(false);

  const { data: detail } = useQuery({
    queryKey: ["sortie-detail", sortieId],
    queryFn: () => fetchSortie(sortieId),
  });

  const { data: fitness } = useQuery({
    queryKey: ["sortie-fitness", sortieId],
    queryFn: () => fetchSortieFitness(sortieId),
  });

  const fitnessStatus = fitness?.overall_status ?? "green";
  const logs = detail?.flight_logs ?? [];

  function formatTime(str: string | null | undefined): string {
    if (!str) return "—";
    return format(parseISO(str), "HH:mm");
  }

  function isPositionFilled(pos: CrewPosition) {
    return logs.some((fl) => fl.crew_position === pos);
  }

  function getLog(pos: CrewPosition) {
    return logs.find((fl) => fl.crew_position === pos);
  }

  async function handleRemove(flightLogId: number) {
    setRemoving(flightLogId);
    try {
      await removeCrew(sortieId, flightLogId);
      qc.invalidateQueries({ queryKey: ["sortie-detail", sortieId] });
      qc.invalidateQueries({ queryKey: ["sortie-fitness", sortieId] });
    } finally {
      setRemoving(null);
    }
  }

  async function handleDelete() {
    setDeleting(true);
    try {
      await deleteSortie(sortieId);
      qc.invalidateQueries({ queryKey: ["upcoming-sorties"] });
      onDeleted();
    } finally {
      setDeleting(false);
      setShowDeleteConfirm(false);
    }
  }

  const optionalFilled = OPTIONAL_POSITIONS.filter(isPositionFilled);
  const openOptional = OPTIONAL_POSITIONS.filter((p) => !isPositionFilled(p));

  return (
    <div className={`card border-l-4 ${FITNESS_BORDER[fitnessStatus]}`}>
      {/* Header */}
      <div className="flex items-start justify-between gap-2 mb-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <FitnessIcon status={fitnessStatus} />
            <span className="font-semibold text-slate-100 text-sm">
              {summary.event_type ?? "PROFICIENCY"}
              {summary.event_code && (
                <span className="text-slate-400 font-normal ml-1">· {summary.event_code}</span>
              )}
            </span>
            {summary.aircraft_side_number && (
              <Badge variant="neutral">{summary.aircraft_side_number}</Badge>
            )}
          </div>
          <div className="text-xs text-slate-400 mt-1">
            T/O {formatTime(summary.takeoff_time)}
            {summary.land_time && <span> · Land {formatTime(summary.land_time)}</span>}
            {summary.duration_hours != null && (
              <span> · {summary.duration_hours.toFixed(1)}h</span>
            )}
          </div>
        </div>
        <button
          onClick={() => setShowDeleteConfirm(true)}
          className="p-1 text-slate-500 hover:text-slate-200 rounded shrink-0"
          title="Delete sortie"
        >
          <MoreHorizontal size={16} />
        </button>
      </div>

      {/* Crew slots */}
      <div className="space-y-1.5 mb-3">
        {REQUIRED_POSITIONS.map((pos) => {
          const log = getLog(pos);
          return (
            <div key={pos} className="flex items-center gap-2">
              <span className="w-20 shrink-0 text-xs text-slate-500 font-medium uppercase tracking-wide">
                {POSITION_LABELS[pos]}
              </span>
              {log ? (
                <div className="flex items-center gap-2 flex-1">
                  <span className="text-slate-200 text-xs">{log.person_name}</span>
                  <button
                    onClick={() => handleRemove(log.id)}
                    disabled={removing === log.id}
                    className="text-slate-600 hover:text-red-400 transition-colors disabled:opacity-50"
                    title="Remove"
                  >
                    <Trash2 size={11} />
                  </button>
                </div>
              ) : (
                <button
                  onClick={() => setAssignPanel(pos)}
                  className="flex items-center gap-1 text-xs text-slate-500 hover:text-blue-400 transition-colors"
                >
                  <Plus size={11} /> Assign
                </button>
              )}
            </div>
          );
        })}

        {optionalFilled.map((pos) => {
          const log = getLog(pos)!;
          return (
            <div key={pos} className="flex items-center gap-2">
              <span className="w-20 shrink-0 text-xs text-slate-500 font-medium uppercase tracking-wide">
                {POSITION_LABELS[pos]}
              </span>
              <div className="flex items-center gap-2 flex-1">
                <span className="text-slate-200 text-xs">{log.person_name}</span>
                <button
                  onClick={() => handleRemove(log.id)}
                  disabled={removing === log.id}
                  className="text-slate-600 hover:text-red-400 transition-colors disabled:opacity-50"
                  title="Remove"
                >
                  <Trash2 size={11} />
                </button>
              </div>
            </div>
          );
        })}

        {openOptional.length > 0 && (
          <div className="relative">
            <button
              onClick={() => setShowAddMenu((v) => !v)}
              className="flex items-center gap-1 text-xs text-slate-500 hover:text-blue-400 transition-colors mt-1"
            >
              <Plus size={11} /> Add crewmember
            </button>
            {showAddMenu && (
              <>
                <div
                  className="fixed inset-0 z-0"
                  onClick={() => setShowAddMenu(false)}
                />
                <div className="absolute left-0 top-6 z-10 bg-slate-800 border border-slate-700 rounded shadow-lg py-1 min-w-[140px]">
                  {openOptional.map((pos) => (
                    <button
                      key={pos}
                      onClick={() => {
                        setShowAddMenu(false);
                        setAssignPanel(pos);
                      }}
                      className="block w-full text-left px-3 py-1.5 text-xs text-slate-300 hover:bg-slate-700"
                    >
                      {POSITION_LABELS[pos]}
                    </button>
                  ))}
                </div>
              </>
            )}
          </div>
        )}
      </div>

      {/* Fitness warnings */}
      {fitness?.warnings && fitness.warnings.length > 0 && (
        <div className="space-y-1 border-t border-slate-800 pt-2">
          {fitness.warnings.map((w, i) => (
            <div
              key={i}
              className={`flex items-start gap-1.5 text-xs ${
                w.severity === "red" ? "text-red-300" : "text-yellow-300"
              }`}
            >
              <AlertTriangle size={11} className="shrink-0 mt-0.5" />
              <span>{w.message}</span>
            </div>
          ))}
        </div>
      )}

      {/* Complete sortie button */}
      {!summary.is_complete && (
        <div className="border-t border-slate-800 pt-2 mt-2">
          <Link
            to={`/sorties/${sortieId}/complete`}
            className="inline-flex items-center px-3 py-1.5 text-xs rounded bg-blue-800 hover:bg-blue-700 text-blue-100 font-medium transition-colors"
          >
            Complete
          </Link>
        </div>
      )}

      {/* Delete confirm dialog */}
      {showDeleteConfirm && (
        <>
          <div
            className="fixed inset-0 bg-black/50 z-40"
            onClick={() => setShowDeleteConfirm(false)}
          />
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            <div className="bg-slate-900 border border-slate-700 rounded-lg p-5 w-full max-w-sm shadow-xl">
              <h3 className="font-semibold text-slate-100 mb-2">Delete Sortie?</h3>
              <p className="text-sm text-slate-400 mb-4">
                This will permanently delete the sortie and all crew assignments.
              </p>
              <div className="flex justify-end gap-2">
                <button
                  onClick={() => setShowDeleteConfirm(false)}
                  className="px-3 py-1.5 text-sm rounded border border-slate-700 text-slate-300 hover:text-slate-100"
                >
                  Cancel
                </button>
                <button
                  onClick={handleDelete}
                  disabled={deleting}
                  className="px-3 py-1.5 text-sm rounded bg-red-700 hover:bg-red-600 text-white disabled:opacity-50"
                >
                  {deleting ? "Deleting…" : "Delete"}
                </button>
              </div>
            </div>
          </div>
        </>
      )}

      {/* Assign crew panel */}
      {assignPanel && (
        <AssignCrewPanel
          sortieId={sortieId}
          crewPosition={assignPanel}
          onClose={() => setAssignPanel(null)}
        />
      )}
    </div>
  );
}
