import { useState, useEffect, useCallback } from "react";
import { Link, useParams } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft } from "lucide-react";
import { format, parseISO } from "date-fns";
import {
  fetchGradecard,
  fetchPerson,
  fetchEligibleInstructors,
  patchGradecard,
  patchGradecardLineItem,
  type GradecardOut,
  type GradecardLineItemResultOut,
  type GradecardStatus,
  type GradingScheme,
  type FourTierScore,
  type CompletionStatus,
} from "../lib/api";
import Loading from "../components/Loading";
import Badge from "../components/Badge";

// ── Constants ────────────────────────────────────────────────────────────────

const SECTION_ORDER = [
  "PLANNING_BRIEFING",
  "PRELAUNCH",
  "ENROUTE",
  "EXECUTION",
  "COMMUNICATION",
  "GENERAL_FLIGHT_CONDUCT",
  "DEBRIEF",
];

const SECTION_LABELS: Record<string, string> = {
  PLANNING_BRIEFING: "Planning / Briefing",
  PRELAUNCH: "Prelaunch",
  ENROUTE: "Enroute",
  EXECUTION: "Execution",
  COMMUNICATION: "Communication",
  GENERAL_FLIGHT_CONDUCT: "General Flight Conduct",
  DEBRIEF: "Debrief",
};

const STATUS_VARIANT: Record<string, "success" | "warning" | "danger" | "neutral" | "info"> = {
  PASS: "success",
  COMPLETE: "success",
  CONDITIONAL_PASS: "warning",
  IN_PROGRESS: "info",
  INCOMPLETE: "danger",
  UNSAT: "danger",
};

const SEL_CLS =
  "bg-slate-800 border border-slate-700 rounded px-2 py-1 text-xs text-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-slate-500 disabled:opacity-50";

// ── Score widgets ────────────────────────────────────────────────────────────

function FourTierSelect({
  value,
  onChange,
}: {
  value: string;
  onChange: (v: string) => void;
}) {
  return (
    <select value={value} onChange={(e) => onChange(e.target.value)} className={SEL_CLS}>
      <option value="">Score…</option>
      <option value="UNSAT_1_0">1.0 — Unsat</option>
      <option value="BELOW_STANDARD_2_0">2.0 — Below Standard</option>
      <option value="STANDARD_3_0">3.0 — Standard</option>
      <option value="EXCEPTIONAL_4_0">4.0 — Exceptional</option>
    </select>
  );
}

function CompletionSelect({
  value,
  onChange,
}: {
  value: string;
  onChange: (v: string) => void;
}) {
  return (
    <select value={value} onChange={(e) => onChange(e.target.value)} className={SEL_CLS}>
      <option value="">Status…</option>
      <option value="COMPLETE">Complete</option>
      <option value="INCOMPLETE">Incomplete</option>
    </select>
  );
}

// ── Line item fill row ────────────────────────────────────────────────────────

function LineItemFillRow({
  result,
  gradecardId,
  scheme,
  onSaved,
}: {
  result: GradecardLineItemResultOut;
  gradecardId: number;
  scheme: GradingScheme;
  onSaved: (updated: GradecardLineItemResultOut) => void;
}) {
  const [score, setScore] = useState(result.four_tier_score ?? "");
  const [compStatus, setCompStatus] = useState(result.completion_status ?? "");
  const [waived, setWaived] = useState(result.waived);
  const [remarks, setRemarks] = useState(result.remarks ?? "");
  const [saveState, setSaveState] = useState<"idle" | "saving" | "saved" | "error">("idle");

  // Sync from cache when server data updates (e.g., after another component patches the card)
  useEffect(() => {
    setScore(result.four_tier_score ?? "");
    setCompStatus(result.completion_status ?? "");
    setWaived(result.waived);
    setRemarks(result.remarks ?? "");
  }, [result]);

  const { mutate: save } = useMutation({
    mutationFn: (body: Parameters<typeof patchGradecardLineItem>[2]) =>
      patchGradecardLineItem(gradecardId, result.id, body),
    onMutate: () => setSaveState("saving"),
    onSuccess: (updated) => {
      setSaveState("saved");
      onSaved(updated);
      setTimeout(() => setSaveState("idle"), 2000);
    },
    onError: () => setSaveState("error"),
  });

  const handleScoreChange = useCallback(
    (v: string) => {
      setScore(v);
      save({ four_tier_score: (v as FourTierScore) || null });
    },
    [save]
  );

  const handleCompStatusChange = useCallback(
    (v: string) => {
      setCompStatus(v);
      save({ completion_status: (v as CompletionStatus) || null });
    },
    [save]
  );

  const handleWaivedChange = useCallback(
    (checked: boolean) => {
      setWaived(checked);
      save({ waived: checked });
    },
    [save]
  );

  const handleRemarksBlur = useCallback(() => {
    const trimmed = remarks.trim();
    const prev = result.remarks ?? "";
    if (trimmed !== prev) {
      save({ remarks: trimmed || null });
    }
  }, [remarks, result.remarks, save]);

  const saveIndicator =
    saveState === "saving" ? (
      <span className="text-[10px] text-slate-500">Saving…</span>
    ) : saveState === "saved" ? (
      <span className="text-[10px] text-green-500">Saved</span>
    ) : saveState === "error" ? (
      <span className="text-[10px] text-red-400">Failed</span>
    ) : null;

  return (
    <div className="py-3 border-b border-slate-800 last:border-0">
      <div className="flex items-start gap-3">
        {/* Left: name, MOP hints, remarks */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap mb-1">
            <span className="text-sm text-slate-200">{result.line_item.item_name}</span>
            {result.line_item.is_critical && (
              <Badge variant="danger" className="text-[10px]">
                Critical
              </Badge>
            )}
          </div>

          {/* MOP rubric anchors (FOUR_TIER only) */}
          {scheme === "FOUR_TIER" &&
            (result.line_item.mop_standard || result.line_item.mop_below_standard) && (
              <div className="text-xs text-slate-600 mb-1.5 space-y-0.5">
                {result.line_item.mop_standard && (
                  <div>
                    <span className="text-slate-500">Std: </span>
                    {result.line_item.mop_standard}
                  </div>
                )}
                {result.line_item.mop_below_standard && (
                  <div>
                    <span className="text-slate-500">BS: </span>
                    {result.line_item.mop_below_standard}
                  </div>
                )}
              </div>
            )}

          {/* Remarks */}
          <input
            type="text"
            placeholder="Remarks…"
            value={remarks}
            onChange={(e) => setRemarks(e.target.value)}
            onBlur={handleRemarksBlur}
            className="w-full mt-1 bg-slate-800/60 border border-slate-700/50 rounded px-2 py-1 text-xs text-slate-300 placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-slate-500"
          />
        </div>

        {/* Right: waived + score + save indicator */}
        <div className="flex flex-col items-end gap-1.5 shrink-0">
          <div className="flex items-center gap-2">
            <label className="flex items-center gap-1 text-xs text-slate-500 cursor-pointer select-none">
              <input
                type="checkbox"
                checked={waived}
                onChange={(e) => handleWaivedChange(e.target.checked)}
                className="accent-blue-500 focus:ring-2 focus:ring-blue-400"
              />
              Waived
            </label>

            {!waived && (
              scheme === "FOUR_TIER" ? (
                <FourTierSelect value={score} onChange={handleScoreChange} />
              ) : (
                <CompletionSelect value={compStatus} onChange={handleCompStatusChange} />
              )
            )}
          </div>
          {saveIndicator}
        </div>
      </div>
    </div>
  );
}

// ── Main page ────────────────────────────────────────────────────────────────

export default function GradecardFill() {
  const { id } = useParams<{ id: string }>();
  const gcId = Number(id);
  const qc = useQueryClient();

  const { data: gc, isLoading, error } = useQuery({
    queryKey: ["gradecard", gcId],
    queryFn: () => fetchGradecard(gcId),
    enabled: !isNaN(gcId),
  });

  const { data: person } = useQuery({
    queryKey: ["person", gc?.person_id],
    queryFn: () => fetchPerson(gc!.person_id),
    enabled: gc?.person_id != null,
  });

  const { data: instructors } = useQuery({
    queryKey: ["eligible-instructors", gc?.syllabus_event_id],
    queryFn: () => fetchEligibleInstructors(gc!.syllabus_event_id),
    enabled: gc?.syllabus_event_id != null,
  });

  // Local header state (editable date and instructor)
  const [localDate, setLocalDate] = useState("");
  const [localInstructorId, setLocalInstructorId] = useState("");
  const [headerInitialized, setHeaderInitialized] = useState(false);
  const [statusMsg, setStatusMsg] = useState<string | null>(null);

  useEffect(() => {
    if (gc && !headerInitialized) {
      setLocalDate(gc.card_date);
      setLocalInstructorId(gc.instructor_person_id ? String(gc.instructor_person_id) : "");
      setHeaderInitialized(true);
    }
  }, [gc, headerInitialized]);

  // Header mutation (date, instructor)
  const headerMutation = useMutation({
    mutationFn: (body: Parameters<typeof patchGradecard>[1]) => patchGradecard(gcId, body),
    onSuccess: (updated) => {
      qc.setQueryData<GradecardOut>(["gradecard", gcId], updated);
    },
  });

  // Status flip mutation
  const statusMutation = useMutation({
    mutationFn: (status: GradecardStatus) => patchGradecard(gcId, { overall_status: status }),
    onSuccess: (updated) => {
      qc.setQueryData<GradecardOut>(["gradecard", gcId], updated);
      const label = updated.overall_status.replace(/_/g, " ");
      setStatusMsg(`Marked ${label}`);
      setTimeout(() => setStatusMsg(null), 3000);
    },
  });

  // Update cache when a line item saves
  const handleResultSaved = useCallback(
    (updated: GradecardLineItemResultOut) => {
      qc.setQueryData<GradecardOut>(["gradecard", gcId], (old) => {
        if (!old) return old;
        return {
          ...old,
          line_item_results: old.line_item_results.map((r) =>
            r.id === updated.id ? updated : r
          ),
        };
      });
    },
    [qc, gcId]
  );

  // ── Guards ────────────────────────────────────────────────────────────────
  if (isLoading) return <Loading />;
  if (error || !gc) {
    return (
      <div className="card border-red-600/50 bg-red-950/20 text-red-300">
        Gradecard not found.
      </div>
    );
  }

  // Count unscored items for the pre-submit warning
  const countUnscored = () =>
    gc.line_item_results.filter((r) => {
      if (r.waived) return false;
      return gc.grading_scheme === "FOUR_TIER"
        ? !r.four_tier_score
        : !r.completion_status;
    }).length;

  const handleMarkStatus = (status: GradecardStatus) => {
    const unscored = countUnscored();
    if (
      unscored > 0 &&
      !window.confirm(
        `${unscored} line item${unscored !== 1 ? "s" : ""} still ha${unscored !== 1 ? "ve" : "s"} no score. Mark as ${status.replace(/_/g, " ")} anyway?`
      )
    )
      return;
    statusMutation.mutate(status);
  };

  // Group line items by section
  const bySection = gc.line_item_results.reduce<Record<string, GradecardLineItemResultOut[]>>(
    (acc, r) => {
      const s = r.line_item.section;
      if (!acc[s]) acc[s] = [];
      acc[s].push(r);
      return acc;
    },
    {}
  );
  const sections = Object.keys(bySection).sort(
    (a, b) =>
      (SECTION_ORDER.indexOf(a) === -1 ? 999 : SECTION_ORDER.indexOf(a)) -
      (SECTION_ORDER.indexOf(b) === -1 ? 999 : SECTION_ORDER.indexOf(b))
  );

  const isSaving = headerMutation.isPending || statusMutation.isPending;

  return (
    <div className="space-y-4 pb-20">
      <Link
        to={`/training/gradecard/${gcId}`}
        className="inline-flex items-center gap-1 text-sm text-slate-400 hover:text-slate-200"
      >
        <ArrowLeft size={14} /> Back to gradecard
      </Link>

      {/* ── Header card ───────────────────────────────────────────────────── */}
      <div className="card">
        <div className="flex items-start justify-between gap-4 flex-wrap">
          {/* Title + meta */}
          <div>
            <h1 className="flex items-center gap-2 flex-wrap">
              Gradecard
              <span className="text-slate-400 font-normal text-lg">#{gc.id}</span>
              <Badge variant="neutral" className="text-xs font-mono">
                {gc.grading_scheme.replace(/_/g, " ")}
              </Badge>
            </h1>
            <div className="flex flex-wrap items-center gap-3 text-sm text-slate-400 mt-1">
              {person && (
                <Link to={`/crew/${person.id}`} className="hover:text-blue-400 transition-colors">
                  {person.last_name}, {person.first_name}
                </Link>
              )}
              <span>·</span>
              <span>{format(parseISO(gc.card_date), "MMM d, yyyy")}</span>
            </div>
          </div>

          {/* Status + action buttons */}
          <div className="flex flex-col items-end gap-2">
            <div className="flex items-center gap-2">
              <Badge variant={STATUS_VARIANT[gc.overall_status] ?? "neutral"}>
                {gc.overall_status.replace(/_/g, " ")}
              </Badge>
              {isSaving && (
                <span className="text-xs text-slate-500">Saving…</span>
              )}
              {statusMsg && !isSaving && (
                <span className="text-xs text-green-400">{statusMsg}</span>
              )}
            </div>

            <div className="flex flex-wrap gap-3 justify-end">
              {gc.grading_scheme === "FOUR_TIER" ? (
                <>
                  <ActionBtn color="green" onClick={() => handleMarkStatus("PASS")}>
                    Mark Pass
                  </ActionBtn>
                  <ActionBtn color="yellow" onClick={() => handleMarkStatus("CONDITIONAL_PASS")}>
                    Conditional Pass
                  </ActionBtn>
                  <ActionBtn color="red" onClick={() => handleMarkStatus("UNSAT")}>
                    Mark Unsat
                  </ActionBtn>
                </>
              ) : (
                <>
                  <ActionBtn color="green" onClick={() => handleMarkStatus("COMPLETE")}>
                    Mark Complete
                  </ActionBtn>
                  <ActionBtn color="red" onClick={() => handleMarkStatus("INCOMPLETE")}>
                    Mark Incomplete
                  </ActionBtn>
                </>
              )}
              {gc.overall_status !== "IN_PROGRESS" && (
                <ActionBtn color="slate" onClick={() => handleMarkStatus("IN_PROGRESS")}>
                  Reopen
                </ActionBtn>
              )}
            </div>
          </div>
        </div>

        {/* Editable header fields */}
        <div className="mt-4 pt-4 border-t border-slate-800 grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs text-slate-500 mb-1">Card Date</label>
            <input
              type="date"
              value={localDate}
              onChange={(e) => setLocalDate(e.target.value)}
              onBlur={() => {
                if (localDate && localDate !== gc.card_date) {
                  headerMutation.mutate({ card_date: localDate });
                }
              }}
              className="w-full bg-slate-800 border border-slate-700 rounded px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-slate-500"
            />
          </div>
          <div>
            <label className="block text-xs text-slate-500 mb-1">Instructor</label>
            <select
              value={localInstructorId}
              onChange={(e) => {
                const v = e.target.value;
                setLocalInstructorId(v);
                headerMutation.mutate({
                  instructor_person_id: v ? Number(v) : null,
                });
              }}
              className="w-full bg-slate-800 border border-slate-700 rounded px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-slate-500"
            >
              <option value="">No instructor</option>
              {(instructors ?? []).map((i) => (
                <option key={i.id} value={i.id}>
                  {i.last_name}, {i.first_name}
                  {i.rank ? ` (${i.rank})` : ""}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* ── Line items by section ─────────────────────────────────────────── */}
      {sections.length === 0 ? (
        <div className="card text-sm text-slate-500">No line items on this gradecard.</div>
      ) : (
        sections.map((section) => (
          <div key={section} className="card">
            <h2 className="text-sm uppercase tracking-wide text-slate-400 mb-3">
              {SECTION_LABELS[section] ?? section.replace(/_/g, " ")}
            </h2>
            <div>
              {bySection[section]
                .sort((a, b) => a.line_item.display_order - b.line_item.display_order)
                .map((result) => (
                  <LineItemFillRow
                    key={result.id}
                    result={result}
                    gradecardId={gcId}
                    scheme={gc.grading_scheme}
                    onSaved={handleResultSaved}
                  />
                ))}
            </div>
          </div>
        ))
      )}

      {/* ── Sticky footer ─────────────────────────────────────────────────── */}
      <div className="fixed bottom-0 left-0 right-0 z-30 bg-slate-950/95 backdrop-blur border-t border-slate-800 px-4 py-3">
        <div className="max-w-4xl mx-auto flex items-center justify-between gap-4">
          <Link
            to={`/training/gradecard/${gcId}`}
            className="text-sm text-slate-400 hover:text-slate-200"
          >
            ← View read-only gradecard
          </Link>
          {isSaving && <span className="text-xs text-slate-500">Saving…</span>}
        </div>
      </div>
    </div>
  );
}

// ── Button helper ────────────────────────────────────────────────────────────

function ActionBtn({
  children,
  onClick,
  color,
}: {
  children: React.ReactNode;
  onClick: () => void;
  color: "green" | "yellow" | "red" | "slate";
}) {
  const cls =
    color === "green"
      ? "bg-green-800 hover:bg-green-700 text-green-100"
      : color === "yellow"
      ? "bg-yellow-800 hover:bg-yellow-700 text-yellow-100"
      : color === "red"
      ? "bg-red-800 hover:bg-red-700 text-red-100"
      : "bg-slate-700 hover:bg-slate-600 text-slate-200";
  return (
    <button
      type="button"
      onClick={onClick}
      className={`px-3 py-1 text-xs rounded font-medium transition-colors ${cls}`}
    >
      {children}
    </button>
  );
}
