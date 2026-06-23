import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";
import { ArrowLeft, BookOpen } from "lucide-react";
import {
  fetchPerson,
  fetchPersonTrainingJacket,
  type CurrencyOut,
  type TrainingJacketEntry,
} from "../lib/api";
import Loading from "../components/Loading";
import Badge from "../components/Badge";
import { classifyExpiration, daysUntil, formatDate } from "../lib/dates";

export default function CrewDetail() {
  const { id } = useParams<{ id: string }>();
  const personId = Number(id);

  const { data, isLoading, error } = useQuery({
    queryKey: ["person", personId],
    queryFn: () => fetchPerson(personId),
    enabled: !isNaN(personId),
  });

  const { data: trainingJacket } = useQuery({
    queryKey: ["training-jacket", personId],
    queryFn: () => fetchPersonTrainingJacket(personId),
    enabled: !isNaN(personId),
  });

  if (isLoading) return <Loading />;
  if (error || !data) {
    return (
      <div className="card border-red-600/50 bg-red-950/20 text-red-300">
        Person not found.
      </div>
    );
  }

  return (
    <div className="space-y-5">
      <Link
        to="/crew"
        className="inline-flex items-center gap-1 text-sm text-slate-400 hover:text-slate-200"
      >
        <ArrowLeft size={14} /> Back to crew
      </Link>

      {/* Header card */}
      <div className="card">
        <div className="flex items-start justify-between flex-wrap gap-3">
          <div>
            <h1>
              {data.last_name}, {data.first_name}
              {data.callsign && (
                <span className="text-slate-400 font-normal ml-3 text-lg">
                  "{data.callsign}"
                </span>
              )}
            </h1>
            <div className="flex gap-3 text-sm text-slate-400 mt-1">
              {data.rank && <span>{data.rank}</span>}
              <span>•</span>
              <span className="capitalize">{data.role.replace("_", " ")}</span>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Link
              to={`/logbook/${data.id}`}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm rounded bg-slate-800 hover:bg-slate-700 text-slate-200 font-medium transition-colors border border-slate-700"
            >
              <BookOpen size={14} /> View Logbook
            </Link>
            <Badge variant={data.is_active ? "success" : "neutral"}>
              {data.is_active ? "Active" : "Inactive"}
            </Badge>
          </div>
        </div>
      </div>

      {/* Two columns: quals and currencies */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Qualifications */}
        <div className="card">
          <h2 className="mb-3">Qualifications</h2>
          {data.qualifications.length === 0 ? (
            <p className="text-sm text-slate-500">No qualifications recorded.</p>
          ) : (
            <div className="space-y-2">
              {data.qualifications.map((q) => (
                <div
                  key={q.id}
                  className="flex items-center justify-between py-1.5 border-b border-slate-800 last:border-0"
                >
                  <div>
                    <div className="font-medium text-sm">{q.qual_code}</div>
                    {q.qualified_date && (
                      <div className="text-xs text-slate-500 mt-0.5">
                        Qualified {formatDate(q.qualified_date)}
                      </div>
                    )}
                  </div>
                  {q.expires_date && (
                    <div className="text-xs text-slate-400">
                      Expires {formatDate(q.expires_date)}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Currencies */}
        <div className="card">
          <h2 className="mb-3">Currencies</h2>
          {data.currencies.length === 0 ? (
            <p className="text-sm text-slate-500">No currencies tracked.</p>
          ) : (
            <div className="space-y-2">
              {data.currencies
                .slice()
                .sort((a, b) => {
                  const da = daysUntil(a.expires_date) ?? Infinity;
                  const db = daysUntil(b.expires_date) ?? Infinity;
                  return da - db;
                })
                .map((c) => (
                  <CurrencyRow key={c.id} currency={c} />
                ))}
            </div>
          )}
        </div>
      </div>

      {/* Training Jacket */}
      <TrainingJacketCard entries={trainingJacket} personId={personId} />
    </div>
  );
}

function TrainingJacketCard({
  entries,
  personId,
}: {
  entries: TrainingJacketEntry[] | undefined;
  personId: number;
}) {
  if (!entries) {
    return (
      <div className="card">
        <h2 className="mb-3">Training Jacket</h2>
        <p className="text-sm text-slate-500">Loading…</p>
      </div>
    );
  }
  const recent = entries.slice(0, 15);
  return (
    <div className="card">
      <div className="flex items-center justify-between mb-3">
        <h2>Training Jacket</h2>
        <Link
          to={`/logbook/${personId}`}
          className="text-xs text-slate-400 hover:text-slate-200"
        >
          Full logbook →
        </Link>
      </div>
      {entries.length === 0 ? (
        <p className="text-sm text-slate-500">No sorties flown.</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs text-slate-500 uppercase tracking-wide">
                <th className="font-medium py-1.5 pr-3">Date</th>
                <th className="font-medium py-1.5 pr-3">Event</th>
                <th className="font-medium py-1.5 pr-3">Pos</th>
                <th className="font-medium py-1.5 pr-3 text-right">Hrs</th>
                <th className="font-medium py-1.5 pr-3">Mode</th>
                <th className="font-medium py-1.5 pr-3">Tasks</th>
              </tr>
            </thead>
            <tbody>
              {recent.map((e) => (
                <tr key={e.sortie_id} className="border-t border-slate-800">
                  <td className="py-1.5 pr-3 text-slate-300">{formatDate(e.sortie_date)}</td>
                  <td className="py-1.5 pr-3">
                    <Link
                      to={`/sorties/${e.sortie_id}`}
                      className="text-blue-400 hover:text-blue-300 font-mono text-xs"
                    >
                      {e.event_code ?? "—"}
                    </Link>
                    {e.event_type && (
                      <span className="text-xs text-slate-500 ml-2">{e.event_type}</span>
                    )}
                  </td>
                  <td className="py-1.5 pr-3">
                    <span className="text-xs text-slate-300">
                      {e.crew_position.replace(/_/g, " ")}
                    </span>
                  </td>
                  <td className="py-1.5 pr-3 text-right text-slate-300">
                    {e.hours_logged.toFixed(1)}
                  </td>
                  <td className="py-1.5 pr-3 text-xs text-slate-500">
                    {e.flight_mode ?? "—"}
                  </td>
                  <td className="py-1.5 pr-3">
                    {e.task_credits.length === 0 ? (
                      <span className="text-xs text-slate-600">—</span>
                    ) : (
                      <div className="flex flex-wrap gap-1">
                        {e.task_credits.map((tc, i) => (
                          <span
                            key={i}
                            className="font-mono text-xs text-slate-300"
                            title={tc.grade ?? undefined}
                          >
                            {tc.task_code}
                            {tc.grade && (
                              <span className="text-slate-500">·{tc.grade}</span>
                            )}
                          </span>
                        ))}
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {entries.length > recent.length && (
            <div className="text-xs text-slate-500 mt-2">
              Showing 15 of {entries.length} sorties — see full logbook.
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function CurrencyRow({ currency }: { currency: CurrencyOut }) {
  const status = classifyExpiration(currency.expires_date);
  const days = daysUntil(currency.expires_date);

  const badge =
    status === "expired" ? <Badge variant="danger">Expired</Badge> :
    status === "expiring-soon" ? <Badge variant="warning">{days}d left</Badge> :
    status === "ok" ? <Badge variant="success">{days}d left</Badge> :
    <Badge variant="neutral">No date</Badge>;

  return (
    <div className="flex items-center justify-between py-1.5 border-b border-slate-800 last:border-0">
      <div>
        <div
          className="font-medium text-sm cursor-help"
          title={currency.currency_type?.name ?? currency.currency_code}
        >
          {currency.currency_code}
        </div>
        <div className="text-xs text-slate-500 mt-0.5">
          Last event {formatDate(currency.last_event_date)}
        </div>
      </div>
      <div className="text-right">
        {badge}
        <div className="text-xs text-slate-500 mt-0.5">
          {formatDate(currency.expires_date)}
        </div>
      </div>
    </div>
  );
}