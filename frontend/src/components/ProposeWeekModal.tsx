import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { format, addDays, setHours, setMinutes } from "date-fns";
import {
  proposeWeek,
  createSortie,
  assignCrew,
  type ProposedSortie,
  type CrewPosition,
} from "../lib/api";
import { useToast } from "./Toast";

const SAMPLE_MISSIONS = `PROFICIENCY | FAM-101 | 09:00
PROFICIENCY | TAC-201 | 13:00
SAR | SAR-301 | 09:00`;

function parseMissionLines(text: string): {
  event_type?: string;
  event_code?: string;
  takeoff_time: string;
  positions: CrewPosition[];
}[] {
  const today = new Date();
  return text
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line, idx) => {
      const parts = line.split("|").map((p) => p.trim());
      const event_type = parts[0] || "PROFICIENCY";
      const event_code = parts[1] || undefined;
      const timePart = parts[2] || "09:00";
      const [h, m] = timePart.split(":").map(Number);
      const day = addDays(today, idx % 5 + 1);
      const takeoff = setMinutes(setHours(day, h || 9), m || 0);
      return {
        event_type,
        event_code,
        takeoff_time: takeoff.toISOString(),
        positions: ["HAC", "CREW_CHIEF"] as CrewPosition[],
      };
    });
}

interface Props {
  onClose: () => void;
}

export default function ProposeWeekModal({ onClose }: Props) {
  const [text, setText] = useState(SAMPLE_MISSIONS);
  const [proposals, setProposals] = useState<ProposedSortie[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [accepting, setAccepting] = useState<number | null>(null);
  const qc = useQueryClient();
  const { showToast } = useToast();

  async function handlePropose() {
    setLoading(true);
    try {
      const missions = parseMissionLines(text);
      const result = await proposeWeek({ missions });
      setProposals(result.proposals);
    } catch {
      showToast("Failed to generate proposals", "error");
    } finally {
      setLoading(false);
    }
  }

  async function handleAccept(proposal: ProposedSortie) {
    setAccepting(proposal.stub_index);
    try {
      const created = await createSortie({
        event_type: proposal.event_type ?? undefined,
        event_code: proposal.event_code ?? undefined,
        aircraft_id: proposal.aircraft_id ?? undefined,
        takeoff_time: proposal.takeoff_time,
        duration_hours: proposal.duration_hours ?? 2,
      });
      for (const crew of proposal.suggested_crew) {
        await assignCrew(created.id, {
          person_id: crew.person_id,
          crew_position: crew.crew_position,
        });
      }
      qc.invalidateQueries({ queryKey: ["upcoming-sorties"] });
      showToast(`Created sortie with ${proposal.suggested_crew.length} crew`, "success");
    } catch {
      showToast("Failed to create sortie", "error");
    } finally {
      setAccepting(null);
    }
  }

  return (
    <>
      <div className="fixed inset-0 bg-black/50 z-40" onClick={onClose} />
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
        <div className="bg-slate-900 border border-slate-700 rounded-lg w-full max-w-2xl max-h-[90vh] overflow-auto shadow-xl p-5 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="font-semibold text-slate-100">Propose Week</h2>
            <button onClick={onClose} className="text-slate-500 hover:text-slate-300 text-sm">
              Close
            </button>
          </div>
          <p className="text-sm text-slate-400">
            Enter mission stubs (one per line: event type | event code | HH:MM). Ranked crew
            suggestions are generated — nothing is published until you accept each sortie.
          </p>
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            rows={5}
            className="w-full rounded bg-slate-950 border border-slate-700 px-3 py-2 text-sm font-mono text-slate-200"
          />
          <button
            onClick={handlePropose}
            disabled={loading}
            className="px-4 py-2 text-sm rounded bg-blue-700 hover:bg-blue-600 text-white disabled:opacity-50"
          >
            {loading ? "Generating…" : "Generate proposals"}
          </button>

          {proposals && (
            <div className="space-y-3 border-t border-slate-800 pt-4">
              {proposals.map((p) => (
                <div key={p.stub_index} className="card text-sm space-y-2">
                  <div className="flex items-center justify-between gap-2">
                    <div>
                      <span className="font-medium text-slate-200">
                        {p.event_type ?? "PROFICIENCY"}
                        {p.event_code && (
                          <span className="text-slate-400 ml-1">· {p.event_code}</span>
                        )}
                      </span>
                      <div className="text-xs text-slate-500">
                        {format(new Date(p.takeoff_time), "EEE MMM d · HH:mm")}
                      </div>
                    </div>
                    <button
                      onClick={() => handleAccept(p)}
                      disabled={accepting === p.stub_index}
                      className="px-3 py-1 text-xs rounded bg-green-800 hover:bg-green-700 text-green-100 disabled:opacity-50"
                    >
                      {accepting === p.stub_index ? "Creating…" : "Accept"}
                    </button>
                  </div>
                  <ul className="text-xs text-slate-400 space-y-1">
                    {p.suggested_crew.map((c) => (
                      <li key={`${c.crew_position}-${c.person_id}`}>
                        <span className="text-slate-300">{c.crew_position}</span>: {c.last_name},{" "}
                        {c.first_name}
                        {c.reasons[0] && <span className="text-slate-500"> — {c.reasons[0]}</span>}
                      </li>
                    ))}
                  </ul>
                  {p.warnings.length > 0 && (
                    <ul className="text-xs text-yellow-400 space-y-0.5">
                      {p.warnings.map((w, i) => (
                        <li key={i}>{w.message}</li>
                      ))}
                    </ul>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </>
  );
}