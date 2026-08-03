import { useState } from "react";
import { parseISO } from "date-fns";
import { Link, useNavigate, useParams } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft } from "lucide-react";
import {
  fetchSortie,
  fetchCbrTaskOptions,
  completeSortie as completeSortieApi,
  type SortieCompletePayload,
} from "../lib/api";
import Loading from "../components/Loading";
import {
  buildFlightLogActuals,
  CREW_LANDING_FIELDS,
  emptyCrewLandings,
  hasPerCrewLandings,
  sumCrewLandings,
  toInputDT,
  addHoursToStr,
  durationBetween,
  type FlightMode,
  type CrewActual,
  type TaskCreditRow,
  type DiscrepancyRow,
  type SafetyRow,
} from "./completeSortie/helpers";
import { Section, Lbl, INPUT_CLS } from "./completeSortie/Section";
import TimesHoursPanel from "./completeSortie/TimesHoursPanel";
import CrewActualsPanel from "./completeSortie/CrewActualsPanel";
import TaskCreditsPanel from "./completeSortie/TaskCreditsPanel";
import DiscrepanciesPanel from "./completeSortie/DiscrepanciesPanel";
import SafetyPanel from "./completeSortie/SafetyPanel";

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
  const [initializedSortieId, setInitializedSortieId] = useState<number | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);

  // ── Pre-fill when sortie loads (adjust state during render — React recommended pattern)
  if (sortie && initializedSortieId !== sortie.id) {
    const defDur = sortie.duration_hours ?? 2.0;
    const defDurStr = defDur.toFixed(1);

    const toStr = sortie.takeoff_time
      ? toInputDT(sortie.takeoff_time)
      : sortie.brief_time
      ? addHoursToStr(toInputDT(sortie.brief_time), 1.5)
      : "";
    const landStr = toStr ? addHoursToStr(toStr, defDur) : "";

    const isNvgMission = sortie.event_type?.toUpperCase().includes("NVG") ?? false;
    const takeoffHour = sortie.takeoff_time
      ? parseISO(sortie.takeoff_time).getHours()
      : 12;
    const isNightMission = takeoffHour >= 19 || takeoffHour < 5;
    const defaultNight = isNvgMission || isNightMission ? defDurStr : "0.0";
    const defaultNvg = isNvgMission ? defDurStr : "0.0";

    setInitializedSortieId(sortie.id);
    setTakeoff(toStr);
    setLand(landStr);
    setDuration(defDurStr);
    setDayH(isNvgMission || isNightMission ? "0.0" : defDurStr);
    setNightH(defaultNight);
    setNvgH(defaultNvg);
    setFlightMode((sortie.flight_mode as FlightMode) ?? "LIVE");
    setCrewActuals(
      sortie.flight_logs.map((fl) => ({
        flight_log_id: fl.id,
        person_name: fl.person_name,
        crew_position: fl.crew_position,
        hours_logged: defDurStr,
        night_hours: defaultNight,
        nvg_hours: defaultNvg,
        actual_instrument_hours: "0.0",
        ...emptyCrewLandings(),
      }))
    );
  }

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
      if (!sortie) throw new Error("Sortie not loaded");
      const activityFields = Object.fromEntries(
        Object.entries(activity)
          .filter(([, v]) => v !== "")
          .map(([k, v]) => [k, parseFloat(v)])
      );
      // Prefer per-crew landings when any crew landing field is filled; else sortie-level activity.
      const landingKeys = new Set<string>(CREW_LANDING_FIELDS);
      const useCrewLandings = hasPerCrewLandings(crewActuals);
      const filteredActivity = Object.fromEntries(
        Object.entries(activityFields).filter(([k]) => !(useCrewLandings && landingKeys.has(k)))
      );
      const crewLandingTotals = useCrewLandings ? sumCrewLandings(crewActuals) : null;
      const payload: SortieCompletePayload = {
        actual_takeoff_time: takeoff + ":00",
        actual_land_time: land + ":00",
        duration_hours: dur,
        flight_mode: flightMode,
        debrief_notes: debriefNotes || null,
        ...filteredActivity,
        ...(crewLandingTotals ?? {}),
        flight_log_actuals: buildFlightLogActuals(
          crewActuals,
          { nightH, nvgH, instrH },
          sortie.event_code
        ),
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
      qc.invalidateQueries({ queryKey: ["person"] });
      qc.invalidateQueries({ queryKey: ["persons"] });
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
  const canSubmit = timesValid && crewValid && !hourMismatch && !mutation.isPending;
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

      <TimesHoursPanel
        takeoff={takeoff}
        land={land}
        duration={duration}
        flightMode={flightMode}
        dayH={dayH}
        nightH={nightH}
        nvgH={nvgH}
        instrH={instrH}
        hourMismatch={hourMismatch}
        sumH={sumH}
        dur={dur}
        onTakeoffChange={onTakeoffChange}
        onLandChange={onLandChange}
        setDuration={setDuration}
        setFlightMode={setFlightMode}
        setDayH={setDayH}
        setNightH={setNightH}
        setNvgH={setNvgH}
        setInstrH={setInstrH}
      />

      <CrewActualsPanel
        crewActuals={crewActuals}
        setCrewActuals={setCrewActuals}
        duration={duration}
        nightH={nightH}
        nvgH={nvgH}
        instrH={instrH}
      />

      {/* ── Section 3: Activity Quantities ──────────────────────────────── */}
      <Section
        title="Activity Quantities"
        badge={
          activityFilled > 0 ? (
            <span className="text-xs text-slate-400">{activityFilled} filled</span>
          ) : null
        }
      >
        {hasPerCrewLandings(crewActuals) ? (
          <p className="text-xs text-slate-500">
            Sortie landing totals will be summed from per-crew landings above.
            Enter hoist / weapons / AMCM below as needed.
          </p>
        ) : (
          <p className="text-xs text-slate-500 mb-2">
            Optional: enter landings per crewmember above, or sortie-level landings here
            (mirrored to HAC if no per-crew values).
          </p>
        )}
        {[
          ...(hasPerCrewLandings(crewActuals)
            ? []
            : [
                {
                  label: "Landings (sortie-level)",
                  fields: [
                    { key: "landings_day", label: "Day" },
                    { key: "landings_night", label: "Night" },
                    { key: "landings_dve_day", label: "DVE Day" },
                    { key: "landings_dve_night", label: "DVE Night" },
                  ],
                },
              ]),
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

      <TaskCreditsPanel
        taskRows={taskRows}
        setTaskRows={setTaskRows}
        crew={crew}
        activeTaskOpts={activeTaskOpts}
      />

      <DiscrepanciesPanel
        discRows={discRows}
        setDiscRows={setDiscRows}
        discCompact={discCompact}
        setDiscCompact={setDiscCompact}
        downCount={downCount}
        majCount={majCount}
      />

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

      <SafetyPanel safetyRows={safetyRows} setSafetyRows={setSafetyRows} />

      {/* ── Sticky submit bar ────────────────────────────────────────────── */}
      <div className="fixed bottom-0 left-0 right-0 z-40 bg-slate-950/95 backdrop-blur border-t border-slate-800 px-4 py-3 md:left-56">
        <div className="max-w-4xl mx-auto flex items-center justify-between gap-4">
          <Link
            to={`/sorties/${sortieId}`}
            className="text-sm text-slate-400 hover:text-slate-200"
          >
            Cancel
          </Link>
          <div className="flex items-center gap-3">
            {!takeoff && (
              <span className="text-xs text-yellow-400">Takeoff time required</span>
            )}
            {takeoff && !land && (
              <span className="text-xs text-yellow-400">Landing time required</span>
            )}
            {takeoff && land && takeoff >= land && (
              <span className="text-xs text-yellow-400">Landing must be after takeoff</span>
            )}
            {timesValid && !crewValid && (
              <span className="text-xs text-yellow-400">Enter hours for all crew positions</span>
            )}
            {timesValid && crewValid && hourMismatch && (
              <span className="text-xs text-yellow-400">
                Activity hours ({sumH.toFixed(1)}) must match duration ({dur.toFixed(1)})
              </span>
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
