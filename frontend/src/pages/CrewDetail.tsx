import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import { fetchPerson, type CurrencyOut } from "../lib/api";
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
          <Badge variant={data.is_active ? "success" : "neutral"}>
            {data.is_active ? "Active" : "Inactive"}
          </Badge>
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