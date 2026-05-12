import { useQuery } from "@tanstack/react-query";
import { Link, useNavigate, useParams } from "react-router-dom";
import { ArrowLeft, PencilLine } from "lucide-react";
import { format, parseISO } from "date-fns";
import { fetchGradecard, fetchPerson, type GradecardLineItemResultOut } from "../lib/api";
import Loading from "../components/Loading";
import Badge from "../components/Badge";

const STATUS_VARIANT: Record<string, "success" | "warning" | "danger" | "neutral" | "info"> = {
  PASS: "success",
  COMPLETE: "success",
  CONDITIONAL_PASS: "warning",
  IN_PROGRESS: "info",
  INCOMPLETE: "danger",
  UNSAT: "danger",
};

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

const FOUR_TIER_DISPLAY: Record<string, { label: string; score: string; variant: "danger" | "warning" | "success" | "info" }> = {
  UNSAT_1_0:          { label: "Unsat",          score: "1.0", variant: "danger" },
  BELOW_STANDARD_2_0: { label: "Below Standard", score: "2.0", variant: "warning" },
  STANDARD_3_0:       { label: "Standard",       score: "3.0", variant: "success" },
  EXCEPTIONAL_4_0:    { label: "Exceptional",    score: "4.0", variant: "info" },
};

const COMPLETION_DISPLAY: Record<string, { label: string; variant: "success" | "danger" | "neutral" }> = {
  COMPLETE:    { label: "Complete",   variant: "success" },
  INCOMPLETE:  { label: "Incomplete", variant: "danger" },
  IN_PROGRESS: { label: "In Progress", variant: "neutral" },
};

export default function GradecardDetail() {
  const { id } = useParams<{ id: string }>();
  const gcId = Number(id);
  const navigate = useNavigate();

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

  if (isLoading) return <Loading />;
  if (error || !gc) {
    return (
      <div className="card border-red-600/50 bg-red-950/20 text-red-300">
        Gradecard not found.
      </div>
    );
  }

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

  return (
    <div className="space-y-5">
      <Link
        to="/training"
        className="inline-flex items-center gap-1 text-sm text-slate-400 hover:text-slate-200"
      >
        <ArrowLeft size={14} /> Back to training
      </Link>

      {/* Header */}
      <div className="card">
        <div className="flex items-start justify-between flex-wrap gap-3">
          <div>
            <h1 className="flex items-center gap-2 flex-wrap">
              Gradecard
              <span className="text-slate-400 font-normal text-lg">#{gc.id}</span>
            </h1>
            <div className="flex flex-wrap gap-3 text-sm text-slate-400 mt-1">
              {person && (
                <Link
                  to={`/crew/${person.id}`}
                  className="hover:text-blue-400 transition-colors"
                >
                  {person.last_name}, {person.first_name}
                </Link>
              )}
              <span>·</span>
              <span>{format(parseISO(gc.card_date), "MMM d, yyyy")}</span>
              <span>·</span>
              <span className="text-slate-500">{gc.grading_scheme.replace(/_/g, " ")}</span>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant={STATUS_VARIANT[gc.overall_status] ?? "neutral"}>
              {gc.overall_status.replace(/_/g, " ")}
            </Badge>
            {gc.overall_status === "IN_PROGRESS" && (
              <button
                onClick={() => navigate(`/training/gradecard/${gcId}/fill`)}
                className="flex items-center gap-1.5 px-3 py-1.5 text-sm rounded bg-blue-700 hover:bg-blue-600 text-white font-medium transition-colors"
              >
                <PencilLine size={13} />
                Continue filling →
              </button>
            )}
          </div>
        </div>

        {gc.remarks && (
          <div className="mt-3 pt-3 border-t border-slate-800 text-sm text-slate-400 italic">
            {gc.remarks}
          </div>
        )}
      </div>

      {/* Line item results by section */}
      {sections.length === 0 ? (
        <div className="card text-sm text-slate-500">No line items recorded.</div>
      ) : (
        sections.map((section) => (
          <div key={section} className="card">
            <h2 className="mb-3 text-sm uppercase tracking-wide text-slate-400">
              {SECTION_LABELS[section] ?? section.replace(/_/g, " ")}
            </h2>
            <div className="space-y-0">
              {bySection[section]
                .sort((a, b) => a.line_item.display_order - b.line_item.display_order)
                .map((r) => (
                  <LineItemRow key={r.id} result={r} scheme={gc.grading_scheme} />
                ))}
            </div>
          </div>
        ))
      )}
    </div>
  );
}

function LineItemRow({
  result,
  scheme,
}: {
  result: GradecardLineItemResultOut;
  scheme: string;
}) {
  return (
    <div className="flex items-start justify-between py-2 border-b border-slate-800 last:border-0 gap-3">
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-sm text-slate-200">{result.line_item.item_name}</span>
          {result.line_item.is_critical && (
            <Badge variant="danger" className="text-[10px]">Critical</Badge>
          )}
          {result.waived && (
            <Badge variant="neutral" className="text-[10px]">Waived</Badge>
          )}
        </div>
        {result.remarks && (
          <div className="text-xs text-slate-500 mt-0.5 truncate">{result.remarks}</div>
        )}
      </div>
      {!result.waived && <ScoreBadge result={result} scheme={scheme} />}
    </div>
  );
}

function ScoreBadge({ result, scheme }: { result: GradecardLineItemResultOut; scheme: string }) {
  if (scheme === "FOUR_TIER") {
    const raw = result.four_tier_score;
    if (!raw) return null;
    const display = FOUR_TIER_DISPLAY[raw];
    if (display) {
      return (
        <Badge variant={display.variant}>
          {display.score} {display.label}
        </Badge>
      );
    }
    return <Badge variant="neutral">{raw}</Badge>;
  }

  // COMPLETION scheme
  const raw = result.completion_status;
  if (!raw) return null;
  const display = COMPLETION_DISPLAY[raw];
  if (display) {
    return <Badge variant={display.variant}>{display.label}</Badge>;
  }
  return <Badge variant="neutral">{raw}</Badge>;
}
