import { useState } from "react";
import { X } from "lucide-react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { fetchAircraft, createSortie, type SortieSummary, type SortieCreate } from "../lib/api";

const EVENT_TYPES = ["FAM", "TAC-D", "SAR", "PROFICIENCY", "FCF", "OTHER"];

interface Props {
  onClose: () => void;
  onCreated: (s: SortieSummary) => void;
}

export default function NewFlightModal({ onClose, onCreated }: Props) {
  const qc = useQueryClient();
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [eventType, setEventType] = useState("");
  const [eventCode, setEventCode] = useState("");
  const [date, setDate] = useState("");
  const [briefTime, setBriefTime] = useState("");
  const [takeoffTime, setTakeoffTime] = useState("");
  const [landTime, setLandTime] = useState("");
  const [aircraftId, setAircraftId] = useState("");
  const [notes, setNotes] = useState("");

  const { data: aircraft } = useQuery({
    queryKey: ["aircraft"],
    queryFn: () => fetchAircraft(),
  });
  const missionCapable = aircraft?.filter((a) => a.status === "FMC" || a.status === "PMC") ?? [];

  function buildISO(timeStr: string): string | undefined {
    if (!date || !timeStr) return undefined;
    return `${date}T${timeStr}:00`;
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!date || !takeoffTime) {
      setError("Date and takeoff time are required.");
      return;
    }

    const takeoffISO = `${date}T${takeoffTime}:00`;
    const landISO = landTime ? `${date}T${landTime}:00` : undefined;

    let durationHours: number | undefined;
    let dayHours: number | undefined;
    let nightHours: number | undefined;

    if (landISO) {
      const diff = new Date(landISO).getTime() - new Date(takeoffISO).getTime();
      durationHours = Math.max(0, diff / 3_600_000);
      const takeoffHour = new Date(takeoffISO).getHours();
      const isNight = takeoffHour >= 19 || takeoffHour < 5;
      if (isNight) {
        nightHours = durationHours;
        dayHours = 0;
      } else {
        dayHours = durationHours;
        nightHours = 0;
      }
    }

    const payload: SortieCreate = {
      event_type: eventType || undefined,
      event_code: eventCode || undefined,
      aircraft_id: aircraftId ? Number(aircraftId) : undefined,
      brief_time: buildISO(briefTime),
      takeoff_time: takeoffISO,
      land_time: landISO,
      duration_hours: durationHours,
      day_hours: dayHours,
      night_hours: nightHours,
      notes: notes || undefined,
    };

    setSubmitting(true);
    setError(null);
    try {
      const sortie = await createSortie(payload);
      await qc.invalidateQueries({ queryKey: ["upcoming-sorties"] });
      onCreated(sortie);
    } catch {
      setError("Failed to create sortie. Check inputs and try again.");
    } finally {
      setSubmitting(false);
    }
  }

  const inputClass =
    "w-full bg-slate-800 border border-slate-700 rounded px-3 py-1.5 text-sm text-slate-100 placeholder:text-slate-600 focus:outline-none focus:border-blue-500";

  return (
    <>
      <div className="fixed inset-0 bg-black/60 z-40" onClick={onClose} />
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
        <div className="bg-slate-900 border border-slate-700 rounded-lg w-full max-w-lg shadow-xl">
          <div className="flex items-center justify-between px-5 py-4 border-b border-slate-800">
            <h2 className="text-base font-semibold">New Flight</h2>
            <button onClick={onClose} aria-label="Close" className="text-slate-400 hover:text-slate-200 p-1">
              <X size={18} />
            </button>
          </div>

          <form onSubmit={handleSubmit} className="p-5 space-y-4">
            {error && (
              <div className="text-sm text-red-400 bg-red-950/30 border border-red-800/50 rounded px-3 py-2">
                {error}
              </div>
            )}

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs text-slate-400 mb-1">Event Type</label>
                <select
                  value={eventType}
                  onChange={(e) => setEventType(e.target.value)}
                  className={inputClass}
                >
                  <option value="">— None —</option>
                  {EVENT_TYPES.map((t) => (
                    <option key={t} value={t}>
                      {t}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-xs text-slate-400 mb-1">Event Code</label>
                <input
                  type="text"
                  value={eventCode}
                  onChange={(e) => setEventCode(e.target.value)}
                  placeholder="e.g. FAM-101"
                  className={inputClass}
                />
              </div>
            </div>

            <div>
              <label className="block text-xs text-slate-400 mb-1">Date *</label>
              <input
                type="date"
                value={date}
                onChange={(e) => setDate(e.target.value)}
                required
                className={inputClass}
              />
            </div>

            <div className="grid grid-cols-3 gap-3">
              <div>
                <label className="block text-xs text-slate-400 mb-1">Brief</label>
                <input
                  type="time"
                  value={briefTime}
                  onChange={(e) => setBriefTime(e.target.value)}
                  className={inputClass}
                />
              </div>
              <div>
                <label className="block text-xs text-slate-400 mb-1">Takeoff *</label>
                <input
                  type="time"
                  value={takeoffTime}
                  onChange={(e) => setTakeoffTime(e.target.value)}
                  required
                  className={inputClass}
                />
              </div>
              <div>
                <label className="block text-xs text-slate-400 mb-1">Land</label>
                <input
                  type="time"
                  value={landTime}
                  onChange={(e) => setLandTime(e.target.value)}
                  className={inputClass}
                />
              </div>
            </div>

            <div>
              <label className="block text-xs text-slate-400 mb-1">Aircraft</label>
              <select
                value={aircraftId}
                onChange={(e) => setAircraftId(e.target.value)}
                className={inputClass}
              >
                <option value="">— None —</option>
                {missionCapable.map((a) => (
                  <option key={a.id} value={a.id}>
                    {a.side_number ?? a.bureau_number} ({a.status})
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs text-slate-400 mb-1">Notes</label>
              <textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                rows={2}
                className={`${inputClass} resize-none`}
              />
            </div>

            <div className="flex justify-end gap-2 pt-1">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-1.5 text-sm rounded border border-slate-700 text-slate-300 hover:text-slate-100"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={submitting}
                className="px-4 py-1.5 text-sm rounded bg-blue-700 hover:bg-blue-600 text-white disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {submitting ? "Creating…" : "Create Flight"}
              </button>
            </div>
          </form>
        </div>
      </div>
    </>
  );
}
