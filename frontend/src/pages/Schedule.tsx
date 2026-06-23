import { useState } from "react";
import { useQuery, useQueries } from "@tanstack/react-query";
import { format, addDays, startOfDay, isSameDay, parseISO } from "date-fns";
import { Plus } from "lucide-react";
import { fetchUpcomingSorties, fetchSortieFitness, type SortieSummary } from "../lib/api";
import SortieTile from "../components/SortieTile";
import NewFlightModal from "../components/NewFlightModal";
import Loading from "../components/Loading";

function sortiesForDay(sorties: SortieSummary[], day: Date): SortieSummary[] {
  return sorties.filter(
    (s) => s.takeoff_time && isSameDay(parseISO(s.takeoff_time), day)
  );
}

export default function Schedule() {
  const today = startOfDay(new Date());
  const [selectedDay, setSelectedDay] = useState<Date>(today);
  const [showNewFlight, setShowNewFlight] = useState(false);
  const [deletedIds, setDeletedIds] = useState<Set<number>>(new Set());

  const { data: sorties, isLoading } = useQuery({
    queryKey: ["upcoming-sorties"],
    queryFn: fetchUpcomingSorties,
    refetchInterval: 30_000,
  });

  const fitnessQueries = useQueries({
    queries: (sorties ?? []).map((s) => ({
      queryKey: ["sortie-fitness", s.id],
      queryFn: () => fetchSortieFitness(s.id),
      staleTime: 30_000,
    })),
  });

  const fitnessById: Record<number, "green" | "yellow" | "red"> = {};
  const topWarningById: Record<number, { severity: "red" | "yellow"; message: string } | null> = {};
  (sorties ?? []).forEach((s, i) => {
    const result = fitnessQueries[i]?.data;
    if (result) {
      fitnessById[s.id] = result.overall_status;
      const top =
        result.warnings.find((w) => w.severity === "red") ??
        result.warnings.find((w) => w.severity === "yellow") ??
        null;
      topWarningById[s.id] = top;
    }
  });

  const visibleSorties = (sorties ?? []).filter((s) => !deletedIds.has(s.id));
  const days = Array.from({ length: 7 }, (_, i) => addDays(today, i));
  const dayView = sortiesForDay(visibleSorties, selectedDay);

  function handleDeleted(id: number) {
    setDeletedIds((prev) => new Set([...prev, id]));
  }

  return (
    <div className="space-y-5">
      {/* Zone A: Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1>Schedule</h1>
          <p className="text-sm text-slate-400 mt-1">Upcoming sorties — next 7 days</p>
        </div>
        <button
          onClick={() => setShowNewFlight(true)}
          className="flex items-center gap-1.5 px-3 py-1.5 text-sm rounded bg-blue-700 hover:bg-blue-600 text-white"
        >
          <Plus size={14} />
          New Flight
        </button>
      </div>

      {isLoading && <Loading message="Loading schedule…" />}

      {/* Zone B: Week strip */}
      {!isLoading && (
        <div className="grid grid-cols-7 gap-1">
          {days.map((day) => {
            const daySorties = sortiesForDay(visibleSorties, day);
            const isSelected = isSameDay(day, selectedDay);
            const isToday = isSameDay(day, today);
            const dayCounts = daySorties.reduce(
              (acc, s) => {
                const fc = fitnessById[s.id] ?? "green";
                acc[fc] = (acc[fc] ?? 0) + 1;
                return acc;
              },
              { green: 0, yellow: 0, red: 0 } as Record<"green" | "yellow" | "red", number>
            );
            const topRed = daySorties
              .map((s) => topWarningById[s.id])
              .find((w) => w && w.severity === "red");
            const titleLines = daySorties.length
              ? `${daySorties.length} sortie${daySorties.length === 1 ? "" : "s"}${
                  dayCounts.red ? ` · ${dayCounts.red} red` : ""
                }${dayCounts.yellow ? ` · ${dayCounts.yellow} yellow` : ""}${
                  topRed ? `\n${topRed.message}` : ""
                }`
              : "No flights";
            return (
              <button
                key={day.toISOString()}
                onClick={() => setSelectedDay(day)}
                title={titleLines}
                className={`rounded-lg p-2 text-center transition-colors border ${
                  isSelected
                    ? "bg-slate-700 border-slate-500"
                    : "bg-slate-900 border-slate-800 hover:bg-slate-800"
                }`}
              >
                <div
                  className={`text-xs font-medium mb-0.5 ${
                    isToday ? "text-blue-400" : "text-slate-400"
                  }`}
                >
                  {format(day, "EEE")}
                </div>
                <div
                  className={`text-sm font-semibold ${
                    isToday ? "text-blue-300" : "text-slate-200"
                  }`}
                >
                  {format(day, "d")}
                </div>
                <div className="flex justify-center gap-0.5 mt-1.5 min-h-[8px]">
                  {daySorties.map((s) => {
                    const fc = fitnessById[s.id] ?? "green";
                    const dot =
                      fc === "red"
                        ? "bg-red-500"
                        : fc === "yellow"
                        ? "bg-yellow-400"
                        : "bg-green-500";
                    return (
                      <span
                        key={s.id}
                        className={`inline-block w-1.5 h-1.5 rounded-full ${dot}`}
                      />
                    );
                  })}
                </div>
                {(dayCounts.red > 0 || dayCounts.yellow > 0) && (
                  <div className="mt-1 flex justify-center gap-1.5 text-[10px] font-medium">
                    {dayCounts.red > 0 && (
                      <span className="text-red-400">{dayCounts.red}R</span>
                    )}
                    {dayCounts.yellow > 0 && (
                      <span className="text-yellow-400">{dayCounts.yellow}Y</span>
                    )}
                  </div>
                )}
              </button>
            );
          })}
        </div>
      )}

      {/* Zone C: Day view */}
      {!isLoading && (
        <div>
          <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wide mb-3">
            {format(selectedDay, "EEEE, MMMM d")}
          </h2>
          {dayView.length === 0 ? (
            <div className="card text-sm text-slate-500 text-center py-8">
              No flights scheduled for this day.
            </div>
          ) : (
            <div className="space-y-3">
              {dayView.map((s) => (
                <SortieTile
                  key={s.id}
                  sortieId={s.id}
                  sortieSummary={s}
                  onDeleted={() => handleDeleted(s.id)}
                />
              ))}
            </div>
          )}
        </div>
      )}

      {showNewFlight && (
        <NewFlightModal
          onClose={() => setShowNewFlight(false)}
          onCreated={() => setShowNewFlight(false)}
        />
      )}
    </div>
  );
}
