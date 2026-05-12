import { useState, useEffect } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, ChevronDown, ChevronUp, Plus, Trash2 } from "lucide-react";
import {
  fetchSortie,
  fetchCbrTaskOptions,
  completeSortie as completeSortieApi,
  type SortieCompletePayload,
} from "../lib/api";
import Loading from "../components/Loading";
import Badge from "../components/Badge";

// ── Local row types for dynamic lists ─────────────────────────────────────────

type FlightMode = "LIVE" | "SIM_TOFT";
type Severity = "MINOR" | "MAJOR" | "DOWNING";
type Grade = "Q" | "CQ" | "U" | "NO" | "NG";
type SafetyLevel = "INFO" | "HAZARD" | "INCIDENT" | "MISHAP";

let _seq = 0;
const uid = () => String(++_seq);

interface CrewActual {
  flight_log_id: number;
  person_name: string;
  crew_position: string;
  hours_logged: string;
}

interface TaskCreditRow {
  _key: string;
  person_id: string;
  task_code: string;
  grade: Grade;
  remarks: string;
}

interface DiscrepancyRow {
  _key: string;
  description: string;
  severity: Severity;
  system_affected: string;
  notes: string;
}

interface SafetyRow {
  _key: string;
  severity: SafetyLevel;
  category: string;
  description: string;
  actions_taken: string;
}

// ── Datetime helpers ──────────────────────────────────────────────────────────

function toInputDT(iso: string | null): string {
  return iso ? iso.slice(0, 16) : "";
}

function addHoursToStr(dtStr: string, hours: number): string {
  if (!dtStr) return "";
  const [datePart, timePart] = dtStr.split("T");
  const [h, m] = timePart.split(":").map(Number);
  const totalMins = h * 60 + m + Math.round(hours * 60);
  const dayBump = Math.floor(totalMins / 1440);
  const rem = totalMins % 1440;
  const newH = Math.floor(rem / 60);
  const newM = rem % 60;
  let newDate = datePart;
  if (dayBump > 0) {
    const [y, mo, d] = datePart.split("-").map(Number);
    const next = new Date(y, mo - 1, d + dayBump);
    newDate = [
      next.getFullYear(),
      String(next.getMonth() + 1).padStart(2, "0"),
      String(next.getDate()).padStart(2, "0"),
    ].join("-");
  }
  return `${newDate}T${String(newH).padStart(2, "0")}:${String(newM).padStart(2, "0")}`;
}

function durationBetween(t: string, l: string): number {
  if (!t || !l) return 0;
  const parse = (s: string) => {
    const [date, time] = s.split("T");
    const [y, mo, d] = date.split("-").map(Number);
    const [h, m] = time.split(":").map(Number);
    return new Date(y, mo - 1, d, h, m).getTime();
  };
  const diffH = (parse(l) - parse(t)) / 3_600_000;
  return Math.max(0, Math.round(diffH * 10) / 10);
}

// ── Collapsible section ───────────────────────────────────────────────────────

function Section({
  title,
  badge,
  required,
  defaultOpen = false,
  children,
}: {
  title: string;
  badge?: React.ReactNode;
  required?: boolean;
  defaultOpen?: boolean;
  children: React.ReactNode;
}) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="card">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="flex items-center justify-between w-full text-left"
      >
        <div className="flex items-center gap-2 flex-wrap">
          <span className="font-semibold text-slate-100">{title}</span>
          {required && (
            <span className="text-xs text-blue-400 font-medium uppercase tracking-wide">
              Required
            </span>
          )}
          {badge}
        </div>
        {open ? (
          <ChevronUp size={16} className="text-slate-400 shrink-0" />
        ) : (
          <ChevronDown size={16} className="text-slate-400 shrink-0" />
        )}
      </button>
      {open && <div className="mt-4 space-y-4">{children}</div>}
    </div>
  );
}

function Lbl({ children }: { children: React.ReactNode }) {
  return <label className="block text-xs text-slate-400 mb-1">{children}</label>;
}

const INPUT_CLS =
  "w-full bg-slate-800 border border-slate-700 rounded px-3 py-1.5 text-sm focus:outline-none focus:border-slate-500";

// ── Main page ─────────────────────────────────────────────────────────────────

export default function CompleteSortie() {
  const { id } = useParams<{ id: string }>();
  const sortieId = Number(id);
  const navigate = useNavigate();
  const qc = useQueryClient();

  const { data: sortie, isLoading } = useQuery({
    queryKey: ["sortie", sortieId],
    queryFn: () => fetchSortie(sortieId),
    enabled: !isNaN(sortieId),
  });

  const { data: taskOptions } = useQuery({
    queryKey: ["cbr-task-options"],
    queryFn: fetchCbrTaskOptions,
  });

  // ── Form state ────────────────────────────────────────────────────────────
  const [takeoff, setTakeoff] = useState("");
  const [land, setLand] = useState("");
  const [duration, setDuration] = useState("2.0");
  const [dayH, setDayH] = useState("0.0");
  const [nightH, setNightH] = useState("0.0");
  const [nvgH, setNvgH] = useState("0.0");
  const [instrH, setInstrH] = useState("0.0");
  const [flightMode, setFlightMode] = useState<FlightMode>("LIVE");
  const [crewActuals, setCrewActuals] = useState<CrewActual[]>([]);
  const [activity, setActivity] = useState<Record<string, string>>({});
  const [taskRows, setTaskRows] = useState<TaskCreditRow[]>([]);
  const [discRows, setDiscRows] = useState<DiscrepancyRow[]>([]);
  const [discCompact, setDiscCompact] = useState(true);
  const [debriefNotes, setDebriefNotes] = useState("");
  const [safetyRows, setSafetyRows] = useState<SafetyRow[]>([]);
  const [initialized, setInitialized] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  // ── Pre-fill when sortie loads ────────────────────────────────────────────
  useEffect(() => {
    if (!sortie || initialized) return;
    const defDur = sortie.duration_hours ?? 2.0;
    const defDurStr = defDur.toFixed(1);

    const toStr = sortie.takeoff_time
      ? toInputDT(sortie.takeoff_time)
      : sortie.brief_time
      ? addHoursToStr(toInputDT(sortie.brief_time), 1.5)
      : "";
    const landStr = toStr ? addHoursToStr(toStr, defDur) : "";

    setTakeoff(toStr);
    setLand(landStr);
    setDuration(defDurStr);
    setDayH(defDurStr);
    setFlightMode((sortie.flight_mode as FlightMode) ?? "LIVE");
    setCrewActuals(
      sortie.flight_logs.map((fl) => ({
        flight_log_id: fl.id,
        person_name: fl.person_name,
        crew_position: fl.crew_position,
        hours_logged: defDurStr,
      }))
    );
    setInitialized(true);
  }, [sortie, initialized]);

  // ── Time change handlers (auto-compute duration) ──────────────────────────
  function onTakeoffChange(v: string) {
    setTakeoff(v);
    if (v && land) {
      const d = durationBetween(v, land);
      if (d > 0) setDuration(d.toFixed(1));
    }
  }
  function onLandChange(v: string) {
    setLand(v);
    if (takeoff && v) {
      const d = durationBetween(takeoff, v);
      if (d > 0) setDuration(d.toFixed(1));
    }
  }

  // ── Derived values (all from state — safe to compute before guards) ───────
  const dur = parseFloat(duration) || 0;
  const sumH =
    (parseFloat(dayH) || 0) +
    (parseFloat(nightH) || 0) +
    (parseFloat(nvgH) || 0) +
    (parseFloat(instrH) || 0);
  const hourMismatch = dur > 0 && Math.abs(sumH - dur) > 0.05;
  const timesValid = !!takeoff && !!land && takeoff < land && dur > 0;
  const crewValid = crewActuals.every((c) => parseFloat(c.hours_logged) > 0);
  const activityFilled = Object.values(activity).filter((v) => v !== "").length;
  const downCount = discRows.filter((d) => d.severity === "DOWNING").length;
  const majCount = discRows.filter((d) => d.severity === "MAJOR").length;

  // ── Mutation ──────────────────────────────────────────────────────────────
  const mutation = useMutation({
    mutationFn: () => {
      const activityFields = Object.fromEntries(
        Object.entries(activity)
          .filter(([, v]) => v !== "")
          .map(([k, v]) => [k, parseFloat(v)])
      );
      const payload: SortieCompletePayload = {
        actual_takeoff_time: takeoff + ":00",
        actual_land_time: land + ":00",
        duration_hours: dur,
        day_hours: parseFloat(dayH) || 0,
        night_hours: parseFloat(nightH) || 0,
        nvg_hours: parseFloat(nvgH) || 0,
        instrument_hours: parseFloat(instrH) || 0,
        debrief_notes: debriefNotes || null,
        ...activityFields,
        flight_log_actuals: crewActuals.map((c) => ({
          flight_log_id: c.flight_log_id,
          hours_logged: parseFloat(c.hours_logged) || 0,
        })),
        task_credits: taskRows
          .filter((r) => r.task_code && r.person_id)
          .map((r) => ({
            task_code: r.task_code,
            person_ids: [parseInt(r.person_id, 10)],
            grade: r.grade || null,
            remarks: r.remarks || null,
          })),
        new_discrepancies: discRows
          .filter((r) => r.description.trim())
          .map((r) => ({
            description: r.description,
            severity: r.severity,
            system_affected: r.system_affected || null,
            notes: r.notes || null,
          })),
        safety_reports: safetyRows
          .filter((r) => r.description.trim())
          .map((r) => ({
            severity: r.severity,
            category: r.category || null,
            description: r.description,
            actions_taken: r.actions_taken || null,
          })),
      };
      return completeSortieApi(sortieId, payload);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["sortie", sortieId] });
      qc.invalidateQueries({ queryKey: ["aircraft-detail"] });
      qc.invalidateQueries({ queryKey: ["dashboard-summary"] });
      qc.invalidateQueries({ queryKey: ["upcoming-sorties"] });
      navigate(`/sorties/${sortieId}`);
    },
    onError: (err: Error) => {
      setSubmitError(err.message || "Submit failed. Check your inputs and try again.");
    },
  });

  // ── Guards ────────────────────────────────────────────────────────────────
  if (isLoading) return <Loading />;
  if (!sortie) {
    return (
      <div className="card border-red-600/50 bg-red-950/20 text-red-300">
        Sortie not found.
      </div>
    );
  }
  if (sortie.is_complete) {
    return (
      <div className="space-y-4">
        <Link
          to={`/sorties/${sortieId}`}
          className="inline-flex items-center gap-1 text-sm text-slate-400 hover:text-slate-200"
        >
          <ArrowLeft size={14} /> Back to sortie
        </Link>
        <div className="card border-green-700/50 bg-green-950/20 text-green-300 text-sm">
          This sortie is already marked complete.{" "}
          <Link to={`/sorties/${sortieId}`} className="underline hover:text-green-200">
            View sortie →
          </Link>
        </div>
      </div>
    );
  }

  // ── Sortie-dependent derived values ───────────────────────────────────────
  const canSubmit = timesValid && crewValid && !mutation.isPending;
  const crew = sortie.flight_logs;
  const activeTaskOpts = (taskOptions ?? []).filter((o) => o.is_active);

  // ── Render ────────────────────────────────────────────────────────────────
  return (
    <div className="space-y-4 pb-24">
      <Link
        to={`/sorties/${sortieId}`}
        className="inline-flex items-center gap-1 text-sm text-slate-400 hover:text-slate-200"
      >
        <ArrowLeft size={14} /> Back to sortie
      </Link>

      {/* Header */}
      <div className="card">
        <h1 className="flex items-center gap-2 flex-wrap">
          Complete Sortie
          {sortie.event_code && (
            <span className="text-slate-400 font-normal text-lg">{sortie.event_code}</span>
          )}
        </h1>
        <div className="flex flex-wrap gap-3 text-sm text-slate-400 mt-1">
          {sortie.event_type && <span>{sortie.event_type}</span>}
          {sortie.aircraft_side_number && (
            <span>· Aircraft {sortie.aircraft_side_number}</span>
          )}
          {sortie.brief_time && (
            <span>· Brief {sortie.brief_time.slice(11, 16)}</span>
          )}
          {sortie.duration_hours != null && (
            <span>· Sched {sortie.duration_hours.toFixed(1)}h</span>
          )}
        </div>
      </div>

      {submitError && (
        <div className="card border-red-600/50 bg-red-950/20 text-red-300 text-sm">
          {submitError}
        </div>
      )}

      {/* ── Section 1: Times & Hours ─────────────────────────────────────── */}
      <Section title="Times & Hours" required defaultOpen>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <Lbl>Actual Takeoff</Lbl>
            <input
              type="datetime-local"
              value={takeoff}
              onChange={(e) => onTakeoffChange(e.target.value)}
              className={INPUT_CLS}
            />
          </div>
          <div>
            <Lbl>Actual Land</Lbl>
            <input
              type="datetime-local"
              value={land}
              onChange={(e) => onLandChange(e.target.value)}
              className={INPUT_CLS}
            />
          </div>
        </div>

        <div className="flex items-end gap-4">
          <div className="w-36">
            <Lbl>Duration (hrs)</Lbl>
            <input
              type="number"
              step="0.1"
              min="0"
              value={duration}
              onChange={(e) => setDuration(e.target.value)}
              className={INPUT_CLS}
            />
          </div>
          <div>
            <Lbl>Flight Mode</Lbl>
            <div className="flex rounded overflow-hidden border border-slate-700">
              {(["LIVE", "SIM_TOFT"] as FlightMode[]).map((m) => (
                <button
                  key={m}
                  type="button"
                  onClick={() => setFlightMode(m)}
                  className={`px-4 py-1.5 text-sm font-medium transition-colors ${
                    flightMode === m
                      ? "bg-blue-700 text-white"
                      : "text-slate-400 hover:text-slate-200"
                  }`}
                >
                  {m === "LIVE" ? "Live" : "Sim / TOFT"}
                </button>
              ))}
            </div>
          </div>
        </div>

        <div>
          <Lbl>Hour Breakdown</Lbl>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {[
              ["Day", dayH, setDayH],
              ["Night", nightH, setNightH],
              ["NVG", nvgH, setNvgH],
              ["Instrument", instrH, setInstrH],
            ].map(([label, val, setter]) => (
              <div key={label as string}>
                <Lbl>{label as string}</Lbl>
                <input
                  type="number"
                  step="0.1"
                  min="0"
                  value={val as string}
                  onChange={(e) => (setter as (v: string) => void)(e.target.value)}
                  className={INPUT_CLS}
                />
              </div>
            ))}
          </div>
          {hourMismatch && (
            <p className="text-xs text-yellow-400 mt-1.5">
              Hour breakdown ({sumH.toFixed(1)}) doesn't match duration ({dur.toFixed(1)}) — note
              that overlap between categories is normal.
            </p>
          )}
        </div>
      </Section>

      {/* ── Section 2: Crew Hours ────────────────────────────────────────── */}
      <Section title="Crew Hours" required defaultOpen>
        <div className="flex justify-end">
          <button
            type="button"
            onClick={() =>
              setCrewActuals((prev) => prev.map((c) => ({ ...c, hours_logged: duration })))
            }
            className="text-xs text-blue-400 hover:text-blue-300"
          >
            Set all to {duration}h
          </button>
        </div>
        {crewActuals.length === 0 ? (
          <p className="text-sm text-slate-500">No crew assigned to this sortie.</p>
        ) : (
          <div className="space-y-2">
            {crewActuals.map((ca, i) => (
              <div key={ca.flight_log_id} className="flex items-center gap-3">
                <Badge variant="neutral" className="shrink-0 text-xs">
                  {ca.crew_position.replace(/_/g, " ")}
                </Badge>
                <span className="text-sm text-slate-300 flex-1 min-w-0 truncate">
                  {ca.person_name}
                </span>
                <input
                  type="number"
                  step="0.1"
                  min="0"
                  value={ca.hours_logged}
                  onChange={(e) =>
                    setCrewActuals((prev) =>
                      prev.map((c, j) =>
                        j === i ? { ...c, hours_logged: e.target.value } : c
                      )
                    )
                  }
                  className="w-24 bg-slate-800 border border-slate-700 rounded px-3 py-1.5 text-sm"
                />
                <span className="text-xs text-slate-500 w-4">h</span>
              </div>
            ))}
          </div>
        )}
      </Section>

      {/* ── Section 3: Activity Quantities ──────────────────────────────── */}
      <Section
        title="Activity Quantities"
        badge={
          activityFilled > 0 ? (
            <span className="text-xs text-slate-400">{activityFilled} filled</span>
          ) : null
        }
      >
        {[
          {
            label: "Landings",
            fields: [
              { key: "landings_day", label: "Day" },
              { key: "landings_night", label: "Night" },
              { key: "landings_dve_day", label: "DVE Day" },
              { key: "landings_dve_night", label: "DVE Night" },
            ],
          },
          {
            label: "Hoist",
            fields: [
              { key: "hoist_streams", label: "Streams" },
              { key: "hoist_recoveries", label: "Recoveries" },
            ],
          },
          {
            label: "Weapons",
            fields: [
              { key: "rounds_fired_20mm", label: "20mm Rounds" },
              { key: "ugr_fired", label: "UGR" },
              { key: "csw_rounds", label: "CSW Rounds" },
              { key: "csw_rounds_night", label: "CSW Night" },
            ],
          },
          {
            label: "AMCM",
            fields: [
              { key: "amns_iterations", label: "AMNS Iterations" },
              { key: "amns_ntrs", label: "AMNS NTRs" },
              { key: "almds_hours", label: "ALMDS Hours" },
            ],
          },
          {
            label: "Strafe",
            fields: [
              { key: "strafe_dry_profiles_day", label: "Day Profiles" },
              { key: "strafe_dry_profiles_night", label: "Night Profiles" },
            ],
          },
        ].map((group) => (
          <div key={group.label}>
            <div className="text-xs text-slate-500 uppercase tracking-wide mb-2">
              {group.label}
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {group.fields.map(({ key, label }) => (
                <div key={key}>
                  <Lbl>{label}</Lbl>
                  <input
                    type="number"
                    step={key === "almds_hours" ? "0.1" : "1"}
                    min="0"
                    value={activity[key] ?? ""}
                    onChange={(e) =>
                      setActivity((prev) => ({ ...prev, [key]: e.target.value }))
                    }
                    placeholder="—"
                    className={INPUT_CLS}
                  />
                </div>
              ))}
            </div>
          </div>
        ))}
      </Section>

      {/* ── Section 4: Task Credits ──────────────────────────────────────── */}
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

      {/* ── Section 5: Discrepancies ─────────────────────────────────────── */}
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

      {/* ── Section 6: Debrief Notes ─────────────────────────────────────── */}
      <Section
        title="Debrief Notes"
        badge={
          debriefNotes.length > 0 ? (
            <span className="text-xs text-slate-400">{debriefNotes.length} chars</span>
          ) : null
        }
      >
        <textarea
          rows={4}
          placeholder="Enter debrief notes…"
          value={debriefNotes}
          onChange={(e) => setDebriefNotes(e.target.value)}
          className="w-full bg-slate-800 border border-slate-700 rounded px-3 py-2 text-sm resize-none"
        />
      </Section>

      {/* ── Section 7: Safety Reports ────────────────────────────────────── */}
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

      {/* ── Sticky submit bar ────────────────────────────────────────────── */}
      <div className="fixed bottom-0 left-0 right-0 z-40 bg-slate-950/95 backdrop-blur border-t border-slate-800 px-4 py-3">
        <div className="max-w-4xl mx-auto flex items-center justify-between gap-4">
          <Link
            to={`/sorties/${sortieId}`}
            className="text-sm text-slate-400 hover:text-slate-200"
          >
            Cancel
          </Link>
          <div className="flex items-center gap-3">
            {!timesValid && (
              <span className="text-xs text-slate-500">Fix times to continue</span>
            )}
            {timesValid && !crewValid && (
              <span className="text-xs text-slate-500">Enter crew hours to continue</span>
            )}
            <button
              type="button"
              onClick={() => {
                setSubmitError(null);
                mutation.mutate();
              }}
              disabled={!canSubmit}
              className="px-5 py-2 rounded bg-blue-700 hover:bg-blue-600 text-white text-sm font-medium disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              {mutation.isPending ? "Submitting…" : "Complete Sortie"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
