import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery, useMutation } from "@tanstack/react-query";
import {
  fetchPersons,
  fetchSyllabusEvents,
  fetchEligibleInstructors,
  createBlankGradecard,
  type SyllabusTrack,
} from "../lib/api";

interface NewGradecardModalProps {
  open: boolean;
  onClose: () => void;
  prefilledPersonId?: number;
  prefilledTrack?: SyllabusTrack;
}

const SEL =
  "w-full bg-slate-800 border border-slate-700 rounded px-3 py-1.5 text-sm focus:outline-none focus:border-slate-500 disabled:opacity-50";
const LBL = "block text-xs text-slate-400 mb-1";

export default function NewGradecardModal({
  open,
  onClose,
  prefilledPersonId,
  prefilledTrack,
}: NewGradecardModalProps) {
  const navigate = useNavigate();

  const today = new Date().toISOString().slice(0, 10);
  const [personId, setPersonId] = useState(prefilledPersonId ? String(prefilledPersonId) : "");
  const [eventId, setEventId] = useState("");
  const [instructorId, setInstructorId] = useState("");
  const [date, setDate] = useState(today);
  const [error, setError] = useState<string | null>(null);

  const { data: persons } = useQuery({
    queryKey: ["persons"],
    queryFn: () => fetchPersons(),
    enabled: open,
    staleTime: 60_000,
  });

  const { data: events } = useQuery({
    queryKey: ["syllabus-events"],
    queryFn: () => fetchSyllabusEvents(),
    enabled: open,
    staleTime: 60_000,
  });

  const { data: instructors } = useQuery({
    queryKey: ["eligible-instructors", eventId],
    queryFn: () => fetchEligibleInstructors(Number(eventId)),
    enabled: !!eventId,
  });

  const mutation = useMutation({
    mutationFn: () =>
      createBlankGradecard({
        person_id: Number(personId),
        syllabus_event_id: Number(eventId),
        instructor_person_id: instructorId ? Number(instructorId) : null,
        card_date: date,
      }),
    onSuccess: (gc) => {
      onClose();
      navigate(`/training/gradecard/${gc.id}/fill`);
    },
    onError: (err: Error) => {
      setError(err.message || "Failed to create gradecard. Check inputs and try again.");
    },
  });

  if (!open) return null;

  // Filter persons by role appropriate to track family
  const trackFamily = prefilledTrack?.startsWith("PILOT") ? "pilot"
    : prefilledTrack?.startsWith("AIRCREW") ? "aircrew"
    : null;
  const filteredPersons = (persons ?? []).filter((p) => {
    if (!trackFamily) return p.role === "pilot" || p.role === "aircrew" || p.role === "co_xo";
    if (trackFamily === "pilot") return p.role === "pilot" || p.role === "co_xo";
    return p.role === "aircrew";
  });

  // Filter events by track family
  const filteredEvents = (events ?? []).filter((ev) => {
    if (!prefilledTrack) return true;
    const family = prefilledTrack.startsWith("PILOT") ? "PILOT" : "AIRCREW";
    return ev.track?.startsWith(family) ?? false;
  });

  // Group events by track for the option groups
  const eventsByTrack = filteredEvents.reduce<Record<string, typeof filteredEvents>>(
    (acc, ev) => {
      const key = ev.track ?? "Other";
      if (!acc[key]) acc[key] = [];
      acc[key].push(ev);
      return acc;
    },
    {}
  );

  // Eligible instructors excluding the selected student
  const eligibleInstructors = (instructors ?? []).filter(
    (i) => !personId || i.id !== Number(personId)
  );

  const canSubmit = !!personId && !!eventId && !!date && !mutation.isPending;

  return (
    <>
      <div className="fixed inset-0 bg-black/50 z-40" onClick={onClose} />
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
        <div className="bg-slate-900 border border-slate-700 rounded-lg p-5 w-full max-w-md shadow-xl">
          <h3 className="font-semibold text-slate-100 mb-4">New Gradecard</h3>

          {/* Person */}
          <div className="mb-3">
            <label className={LBL}>Person</label>
            <select
              value={personId}
              onChange={(e) => setPersonId(e.target.value)}
              disabled={!!prefilledPersonId}
              className={SEL}
            >
              <option value="">Select person…</option>
              {filteredPersons.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.last_name}, {p.first_name}
                  {p.rank ? ` (${p.rank})` : ""}
                </option>
              ))}
            </select>
          </div>

          {/* Syllabus Event */}
          <div className="mb-3">
            <label className={LBL}>Syllabus Event</label>
            <select
              value={eventId}
              onChange={(e) => {
                setEventId(e.target.value);
                setInstructorId("");
              }}
              className={SEL}
            >
              <option value="">Select event…</option>
              {Object.entries(eventsByTrack).map(([track, evs]) => (
                <optgroup key={track} label={track.replace(/_/g, " ")}>
                  {evs.map((ev) => (
                    <option key={ev.id} value={ev.id}>
                      {ev.event_code ?? ev.code} — {ev.name}
                    </option>
                  ))}
                </optgroup>
              ))}
            </select>
          </div>

          {/* Instructor */}
          <div className="mb-3">
            <label className={LBL}>Instructor (optional)</label>
            <select
              value={instructorId}
              onChange={(e) => setInstructorId(e.target.value)}
              disabled={!eventId}
              className={SEL}
            >
              <option value="">
                {!eventId ? "Pick an event first" : eligibleInstructors.length === 0 ? "No eligible instructors" : "No instructor"}
              </option>
              {eligibleInstructors.map((i) => (
                <option key={i.id} value={i.id}>
                  {i.last_name}, {i.first_name}
                  {i.rank ? ` (${i.rank})` : ""}
                </option>
              ))}
            </select>
          </div>

          {/* Date */}
          <div className="mb-4">
            <label className={LBL}>Card Date</label>
            <input
              type="date"
              value={date}
              onChange={(e) => setDate(e.target.value)}
              className={SEL}
            />
          </div>

          {error && (
            <div className="mb-3 text-sm text-red-300 bg-red-950/30 border border-red-700/40 rounded px-3 py-2">
              {error}
            </div>
          )}

          <div className="flex justify-end gap-2">
            <button
              onClick={onClose}
              className="px-3 py-1.5 text-sm rounded border border-slate-700 text-slate-300 hover:text-slate-100 transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={() => {
                setError(null);
                mutation.mutate();
              }}
              disabled={!canSubmit}
              className="px-4 py-1.5 text-sm rounded bg-blue-700 hover:bg-blue-600 text-white font-medium disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              {mutation.isPending ? "Creating…" : "Create"}
            </button>
          </div>
        </div>
      </div>
    </>
  );
}
