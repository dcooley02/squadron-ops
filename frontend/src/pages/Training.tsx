import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { Plus } from "lucide-react";
import { format, parseISO } from "date-fns";
import {
  fetchPersons, fetchSyllabusEvents, fetchPersonGradecards,
  fetchBoardSchedules, fetchInstructorCandidates, createBoardSchedule,
  type PersonSummary, type GradecardSummary, type SyllabusEventOut,
  type BoardSchedule, type BoardType, type InstructorCandidate,
} from "../lib/api";
import Loading from "../components/Loading";
import Badge from "../components/Badge";
import NewGradecardModal from "../components/NewGradecardModal";

type Tab = "people" | "events" | "gradecards" | "boards";

export default function Training() {
  const [tab, setTab] = useState<Tab>("people");

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1>Training</h1>
      </div>

      {/* Tab bar */}
      <div className="flex gap-1 border-b border-slate-800 pb-0">
        {(["people", "events", "gradecards", "boards"] as Tab[]).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={
              "px-4 py-2 text-sm capitalize rounded-t transition-colors " +
              (tab === t
                ? "bg-slate-800 text-white border-b-2 border-blue-500"
                : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50")
            }
          >
            {t === "gradecards" ? "Gradecards" : t === "boards" ? "Boards" : t.charAt(0).toUpperCase() + t.slice(1)}
          </button>
        ))}
      </div>

      {tab === "people" && <PeopleTab />}
      {tab === "events" && <EventsTab />}
      {tab === "gradecards" && <GradecardsTab />}
      {tab === "boards" && <BoardsTab />}
    </div>
  );
}

// ── People tab ───────────────────────────────────────────────────────────────

function PeopleTab() {
  const { data: persons, isLoading } = useQuery({
    queryKey: ["persons"],
    queryFn: () => fetchPersons(),
  });

  if (isLoading) return <Loading />;

  const pilots = persons?.filter((p) => p.role === "pilot" || p.role === "co_xo") ?? [];
  const aircrew = persons?.filter((p) => p.role === "aircrew") ?? [];

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
      <PersonGroup label="Pilots" persons={pilots} />
      <PersonGroup label="Aircrew" persons={aircrew} />
    </div>
  );
}

function PersonGroup({ label, persons }: { label: string; persons: PersonSummary[] }) {
  const [modalPersonId, setModalPersonId] = useState<number | null>(null);

  return (
    <div className="card">
      <h2 className="mb-3">{label}</h2>
      {persons.length === 0 ? (
        <p className="text-sm text-slate-500">None.</p>
      ) : (
        <div className="space-y-0">
          {persons.map((p) => (
            <div
              key={p.id}
              className="flex items-center justify-between py-2.5 border-b border-slate-800 last:border-0"
            >
              <div>
                <Link
                  to={`/crew/${p.id}`}
                  className="text-sm font-medium hover:text-blue-400 transition-colors"
                >
                  {p.last_name}, {p.first_name}
                </Link>
                {p.callsign && (
                  <span className="text-slate-500 text-sm ml-2">"{p.callsign}"</span>
                )}
              </div>
              <div className="flex items-center gap-2">
                {p.rank && <span className="text-xs text-slate-500">{p.rank}</span>}
                <PersonGradecardBadge personId={p.id} />
                <button
                  onClick={() => setModalPersonId(p.id)}
                  className="flex items-center gap-0.5 text-xs text-slate-500 hover:text-blue-400 transition-colors"
                  title="New gradecard for this person"
                >
                  <Plus size={11} />
                  New gradecard
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      <NewGradecardModal
        open={modalPersonId !== null}
        prefilledPersonId={modalPersonId ?? undefined}
        onClose={() => setModalPersonId(null)}
      />
    </div>
  );
}

function PersonGradecardBadge({ personId }: { personId: number }) {
  const { data } = useQuery({
    queryKey: ["gradecards", personId],
    queryFn: () => fetchPersonGradecards(personId),
    staleTime: 60_000,
  });
  if (!data) return null;
  return (
    <span className="text-xs text-slate-500">{data.length} card{data.length !== 1 ? "s" : ""}</span>
  );
}

// ── Events tab ───────────────────────────────────────────────────────────────

const TRACK_COLORS: Record<string, string> = {
  PILOT_CORE: "bg-blue-950/50 text-blue-400 border border-blue-800/50",
  PILOT_AMCM: "bg-blue-950/50 text-blue-400 border border-blue-800/50",
  AIRCREW_CORE: "bg-purple-950/50 text-purple-400 border border-purple-800/50",
  AIRCREW_AMCM: "bg-purple-950/50 text-purple-400 border border-purple-800/50",
};

type TrackFilter = "all" | "PILOT" | "AIRCREW";

function EventsTab() {
  const [track, setTrack] = useState<TrackFilter>("all");
  const [stanEvalOnly, setStanEvalOnly] = useState(false);

  const { data: allEvents, isLoading, error } = useQuery({
    queryKey: ["syllabus-events", stanEvalOnly],
    queryFn: () =>
      fetchSyllabusEvents({
        is_stan_eval: stanEvalOnly || undefined,
      }),
  });

  const events = useMemo(() => {
    if (!allEvents) return [];
    if (track === "PILOT") {
      return allEvents.filter((e) => e.track?.startsWith("PILOT"));
    }
    if (track === "AIRCREW") {
      return allEvents.filter((e) => e.track?.startsWith("AIRCREW"));
    }
    return allEvents;
  }, [allEvents, track]);

  if (isLoading) return <Loading />;
  if (error) {
    return (
      <div className="card border-red-600/50 bg-red-950/20 text-red-300">
        Failed to load syllabus events. Is the backend running?
      </div>
    );
  }

  return (
    <div className="card">
      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3 mb-4">
        <div className="flex gap-1">
          {(["all", "PILOT", "AIRCREW"] as TrackFilter[]).map((t) => (
            <button
              key={t}
              onClick={() => setTrack(t)}
              className={
                "px-3 py-1 text-xs rounded transition-colors " +
                (track === t
                  ? "bg-slate-700 text-white"
                  : "text-slate-400 hover:bg-slate-800/50")
              }
            >
              {t === "all" ? "All Tracks" : t}
            </button>
          ))}
        </div>
        <label className="flex items-center gap-2 text-xs text-slate-400 cursor-pointer">
          <input
            type="checkbox"
            checked={stanEvalOnly}
            onChange={(e) => setStanEvalOnly(e.target.checked)}
            className="accent-blue-500"
          />
          Stan/Eval only
        </label>
        <span className="text-xs text-slate-500 ml-auto">{events?.length ?? 0} events</span>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-800 text-left text-xs text-slate-500 uppercase">
              <th className="py-2 pr-4 font-medium">Code</th>
              <th className="py-2 pr-4 font-medium">Name</th>
              <th className="py-2 pr-4 font-medium">Track</th>
              <th className="py-2 pr-4 font-medium">Hours</th>
              <th className="py-2 font-medium">Scheme</th>
            </tr>
          </thead>
          <tbody>
            {events.length === 0 ? (
              <tr>
                <td colSpan={5} className="py-8 text-center text-sm text-slate-500">
                  No events match this filter.
                </td>
              </tr>
            ) : (
              events.map((ev) => <EventRow key={ev.id} event={ev} />)
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function EventRow({ event }: { event: SyllabusEventOut }) {
  return (
    <tr className="border-b border-slate-800/60 last:border-0 hover:bg-slate-800/20">
      <td className="py-2 pr-4 font-mono text-blue-400 text-xs whitespace-nowrap">
        {event.event_code ?? event.code}
      </td>
      <td className="py-2 pr-4 text-slate-200">
        {event.name}
        {event.is_stan_eval && (
          <Badge variant="warning" className="ml-2 text-[10px]">S/E</Badge>
        )}
      </td>
      <td className="py-2 pr-4">
        {event.track ? (
          <span className={`badge text-[10px] ${TRACK_COLORS[event.track] ?? ""}`}>
            {event.track}
          </span>
        ) : (
          <span className="text-slate-600">—</span>
        )}
      </td>
      <td className="py-2 pr-4 text-slate-400">
        {event.time_hours != null ? event.time_hours.toFixed(1) : "—"}
      </td>
      <td className="py-2 text-slate-400 text-xs">
        {event.grading_scheme?.replace(/_/g, " ") ?? "—"}
      </td>
    </tr>
  );
}

// ── Gradecards tab ────────────────────────────────────────────────────────────

const STATUS_VARIANT: Record<string, "success" | "warning" | "danger" | "neutral" | "info"> = {
  PASS: "success",
  COMPLETE: "success",
  CONDITIONAL_PASS: "warning",
  IN_PROGRESS: "info",
  INCOMPLETE: "neutral",
  UNSAT: "danger",
};

function GradecardsTab() {
  const [modalOpen, setModalOpen] = useState(false);

  const { data: persons, isLoading: loadingPersons } = useQuery({
    queryKey: ["persons"],
    queryFn: () => fetchPersons(),
  });

  if (loadingPersons || !persons) return <Loading />;

  const fliers = persons.filter(
    (p) => p.role === "pilot" || p.role === "aircrew" || p.role === "co_xo"
  );

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <button
          onClick={() => setModalOpen(true)}
          className="flex items-center gap-1.5 px-3 py-1.5 text-sm rounded bg-blue-700 hover:bg-blue-600 text-white font-medium transition-colors"
        >
          <Plus size={14} />
          New Gradecard
        </button>
      </div>

      {fliers.map((p) => (
        <PersonGradecards key={p.id} person={p} />
      ))}

      <NewGradecardModal open={modalOpen} onClose={() => setModalOpen(false)} />
    </div>
  );
}

function PersonGradecards({ person }: { person: PersonSummary }) {
  const { data: cards, isLoading } = useQuery({
    queryKey: ["gradecards", person.id],
    queryFn: () => fetchPersonGradecards(person.id),
    staleTime: 60_000,
  });

  if (isLoading || !cards || cards.length === 0) return null;

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-3">
        <Link
          to={`/crew/${person.id}`}
          className="font-medium hover:text-blue-400 transition-colors"
        >
          {person.last_name}, {person.first_name}
        </Link>
        <span className="text-xs text-slate-500">{cards.length} gradecard{cards.length !== 1 ? "s" : ""}</span>
      </div>
      <div className="space-y-0">
        {cards.map((gc) => (
          <GradecardRow key={gc.id} gc={gc} />
        ))}
      </div>
    </div>
  );
}

function BoardsTab() {
  const { data: boards, isLoading } = useQuery({
    queryKey: ["board-schedules"],
    queryFn: fetchBoardSchedules,
  });

  if (isLoading) return <Loading />;

  return (
    <div className="space-y-4">
      <ScheduleBoardForm />
      <div className="card">
        <h2 className="mb-3">Upcoming boards</h2>
        {(boards ?? []).length === 0 ? (
          <p className="text-sm text-slate-500">No boards scheduled.</p>
        ) : (
          <div className="space-y-2">
            {(boards ?? []).map((b) => (
              <BoardRow key={b.id} board={b} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function BoardRow({ board }: { board: BoardSchedule }) {
  return (
    <div className="flex flex-wrap items-center gap-3 py-2 border-b border-slate-800 last:border-0">
      <Badge variant="info">{board.board_type.replace(/_/g, " ")}</Badge>
      <span className="text-sm font-medium">{board.examinee_name}</span>
      <span className="text-xs text-slate-500">
        {format(parseISO(board.scheduled_at), "MMM d HH:mm")}
      </span>
      {board.event_code && (
        <span className="font-mono text-xs text-blue-400">{board.event_code}</span>
      )}
      <span className="text-sm text-slate-400">
        IP: {board.instructor_name ?? "TBD"}
      </span>
      {board.location && <span className="text-xs text-slate-500">{board.location}</span>}
    </div>
  );
}

function ScheduleBoardForm() {
  const [open, setOpen] = useState(false);
  const [boardType, setBoardType] = useState<BoardType>("HAC_BOARD");
  const [examineeId, setExamineeId] = useState<number | "">("");
  const [eventId, setEventId] = useState<number | "">("");
  const [scheduledAt, setScheduledAt] = useState("");
  const [candidates, setCandidates] = useState<InstructorCandidate[]>([]);
  const [instructorId, setInstructorId] = useState<number | "">("");
  const queryClient = useQueryClient();

  const { data: persons } = useQuery({
    queryKey: ["persons"],
    queryFn: () => fetchPersons(),
  });
  const { data: events } = useQuery({
    queryKey: ["syllabus-events-stan"],
    queryFn: () => fetchSyllabusEvents({ is_stan_eval: true }),
  });

  const createMut = useMutation({
    mutationFn: createBoardSchedule,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["board-schedules"] });
      setOpen(false);
    },
  });

  async function loadCandidates() {
    if (!examineeId || !scheduledAt) return;
    const list = await fetchInstructorCandidates({
      board_type: boardType,
      examinee_person_id: Number(examineeId),
      scheduled_at: new Date(scheduledAt).toISOString(),
      syllabus_event_id: eventId ? Number(eventId) : undefined,
    });
    setCandidates(list);
    if (list[0]) setInstructorId(list[0].person_id);
  }

  if (!open) {
    return (
      <button
        onClick={() => setOpen(true)}
        className="flex items-center gap-1.5 px-3 py-1.5 text-sm rounded bg-blue-700 hover:bg-blue-600 text-white font-medium"
      >
        <Plus size={14} /> Schedule board
      </button>
    );
  }

  const pilots = (persons ?? []).filter((p) => p.role === "pilot" || p.role === "co_xo");

  return (
    <div className="card space-y-3">
      <h2>Schedule training board</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
        <label className="space-y-1">
          <span className="text-slate-500">Board type</span>
          <select
            value={boardType}
            onChange={(e) => setBoardType(e.target.value as BoardType)}
            className="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1.5"
          >
            <option value="HAC_BOARD">HAC Board</option>
            <option value="INSTRUCTOR_BOARD">Instructor Board</option>
            <option value="NATOPS_CHECK">NATOPS Check</option>
            <option value="STAN_EVAL">Stan/Eval</option>
          </select>
        </label>
        <label className="space-y-1">
          <span className="text-slate-500">Examinee</span>
          <select
            value={examineeId}
            onChange={(e) => setExamineeId(e.target.value ? Number(e.target.value) : "")}
            className="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1.5"
          >
            <option value="">Select pilot…</option>
            {pilots.map((p) => (
              <option key={p.id} value={p.id}>{p.last_name}, {p.first_name}</option>
            ))}
          </select>
        </label>
        <label className="space-y-1">
          <span className="text-slate-500">Syllabus event (optional)</span>
          <select
            value={eventId}
            onChange={(e) => setEventId(e.target.value ? Number(e.target.value) : "")}
            className="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1.5"
          >
            <option value="">—</option>
            {(events ?? []).map((ev) => (
              <option key={ev.id} value={ev.id}>{ev.event_code} — {ev.name}</option>
            ))}
          </select>
        </label>
        <label className="space-y-1">
          <span className="text-slate-500">Date & time</span>
          <input
            type="datetime-local"
            value={scheduledAt}
            onChange={(e) => setScheduledAt(e.target.value)}
            className="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1.5"
          />
        </label>
      </div>
      <button
        type="button"
        onClick={loadCandidates}
        className="text-sm text-blue-400 hover:text-blue-300"
      >
        Suggest instructors →
      </button>
      {candidates.length > 0 && (
        <div className="space-y-1">
          <span className="text-xs text-slate-500 uppercase">Ranked instructors</span>
          {candidates.slice(0, 5).map((c) => (
            <label key={c.person_id} className="flex items-center gap-2 text-sm cursor-pointer">
              <input
                type="radio"
                name="instructor"
                checked={instructorId === c.person_id}
                onChange={() => setInstructorId(c.person_id)}
              />
              <span>{c.person_name}</span>
              <span className="text-xs text-slate-500">score {c.score}</span>
            </label>
          ))}
        </div>
      )}
      <div className="flex gap-2">
        <button
          onClick={() =>
            createMut.mutate({
              board_type: boardType,
              scheduled_at: new Date(scheduledAt).toISOString(),
              examinee_person_id: Number(examineeId),
              instructor_person_id: instructorId ? Number(instructorId) : undefined,
              syllabus_event_id: eventId ? Number(eventId) : undefined,
              location: "Ready room",
            })
          }
          disabled={!examineeId || !scheduledAt || createMut.isPending}
          className="px-3 py-1.5 text-sm rounded bg-blue-700 hover:bg-blue-600 text-white disabled:opacity-50"
        >
          Save board
        </button>
        <button onClick={() => setOpen(false)} className="px-3 py-1.5 text-sm text-slate-400">
          Cancel
        </button>
      </div>
    </div>
  );
}

function GradecardRow({ gc }: { gc: GradecardSummary }) {
  return (
    <div className="flex items-center justify-between py-2 border-b border-slate-800 last:border-0">
      <div className="flex items-center gap-3">
        <Link
          to={`/training/gradecard/${gc.id}`}
          className="font-mono text-sm text-blue-400 hover:text-blue-300 transition-colors"
        >
          {gc.event_code ?? "—"}
        </Link>
        <span className="text-xs text-slate-500">
          {format(parseISO(gc.card_date), "MMM d, yyyy")}
        </span>
      </div>
      <Badge variant={STATUS_VARIANT[gc.overall_status] ?? "neutral"}>
        {gc.overall_status.replace(/_/g, " ")}
      </Badge>
    </div>
  );
}
