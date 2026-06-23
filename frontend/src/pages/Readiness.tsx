import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import clsx from "clsx";
import { fetchSquadronReadiness, type CapabilityArea, type SquadronReadiness } from "../lib/api";
import Loading from "../components/Loading";
import TRatingBadge from "../components/TRatingBadge";
import { formatDate } from "../lib/dates";

const AREA_ORDER: CapabilityArea[] = ["MOB", "FSO", "ASU", "SOF", "PR", "STW", "LOG", "MIW"];

export default function Readiness() {
  const [selectedArea, setSelectedArea] = useState<CapabilityArea | null>(null);

  const { data, isLoading, error } = useQuery({
    queryKey: ["squadron-readiness"],
    queryFn: fetchSquadronReadiness,
  });

  if (isLoading) return <Loading message="Computing WTM readiness..." />;
  if (error || !data) {
    return (
      <div className="card border-red-600/50 bg-red-950/20 text-red-300">
        Failed to load readiness data. Is the backend running?
      </div>
    );
  }

  const selectedRollup = selectedArea
    ? data.areas.find((a) => a.capability_area === selectedArea)
    : null;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1>Capability Readiness</h1>
          <p className="text-sm text-slate-400 mt-1">
            WTM T-ratings by capability area — anchor-task recency and Table B-2 currency gates.
            Distinct from individual B-2 currency status on the dashboard.
          </p>
        </div>
        <div className="text-right">
          <div className="text-xs text-slate-500 uppercase tracking-wide">Squadron overall</div>
          <TRatingBadge rating={data.squadron_overall_rating} large />
          <div className="text-xs text-slate-500 mt-1">
            As of {formatDate(data.as_of_date)} · {data.pilots_rated} pilots rated
          </div>
        </div>
      </div>

      <section className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {AREA_ORDER.map((code) => {
          const area = data.areas.find((a) => a.capability_area === code);
          if (!area) return null;
          const isSelected = selectedArea === code;
          return (
            <button
              key={code}
              type="button"
              onClick={() => setSelectedArea(isSelected ? null : code)}
              className={clsx(
                "card text-left transition-colors hover:border-slate-600",
                isSelected && "border-blue-600/60 bg-blue-950/20"
              )}
            >
              <div className="flex items-center justify-between gap-2">
                <span className="font-mono text-sm text-slate-300">{code}</span>
                <TRatingBadge rating={area.squadron_rating} />
              </div>
              <div className="text-sm text-slate-400 mt-1">{area.label}</div>
              <div className="text-xs text-slate-500 mt-2 flex gap-2">
                <span className="text-green-400">{area.t1_count} T-1</span>
                <span className="text-yellow-400">{area.t2_count} T-2</span>
                <span className="text-red-400">{area.t3_count} T-3</span>
              </div>
            </button>
          );
        })}
      </section>

      {selectedRollup && (
        <section className="card border-blue-800/40 bg-blue-950/10">
          <h2 className="text-base mb-2">
            {selectedRollup.capability_area} — {selectedRollup.label}
          </h2>
          <p className="text-sm text-slate-400 mb-3">
            Squadron limiting rating: <TRatingBadge rating={selectedRollup.squadron_rating} />{" "}
            (worst pilot in this area)
          </p>
          <AreaPilotTable data={data} area={selectedRollup.capability_area} />
        </section>
      )}

      <section className="card">
        <h2 className="mb-3">Pilot T-Ratings</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs text-slate-500 uppercase tracking-wide border-b border-slate-800">
                <th className="font-medium py-2 pr-3">Pilot</th>
                <th className="font-medium py-2 pr-3">Overall</th>
                {AREA_ORDER.map((code) => (
                  <th key={code} className="font-medium py-2 pr-2 text-center font-mono">
                    {code}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {data.persons.map((p) => (
                <tr key={p.person_id} className="border-t border-slate-800">
                  <td className="py-2 pr-3">
                    <Link
                      to={`/crew/${p.person_id}`}
                      className="text-blue-400 hover:text-blue-300"
                    >
                      {p.person_name}
                      {p.callsign && (
                        <span className="text-slate-500 ml-1">"{p.callsign}"</span>
                      )}
                    </Link>
                  </td>
                  <td className="py-2 pr-3">
                    <TRatingBadge rating={p.overall_rating} />
                  </td>
                  {AREA_ORDER.map((code) => {
                    const area = p.areas.find((a) => a.capability_area === code);
                    return (
                      <td key={code} className="py-2 pr-2 text-center">
                        {area ? <TRatingBadge rating={area.rating} /> : "—"}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}

function AreaPilotTable({
  data,
  area,
}: {
  data: SquadronReadiness;
  area: CapabilityArea;
}) {
  return (
    <table className="w-full text-sm">
      <thead>
        <tr className="text-left text-xs text-slate-500 uppercase tracking-wide">
          <th className="font-medium py-1.5 pr-3">Pilot</th>
          <th className="font-medium py-1.5 pr-3">Rating</th>
          <th className="font-medium py-1.5">Contributing factors</th>
        </tr>
      </thead>
      <tbody>
        {data.persons.map((p) => {
          const row = p.areas.find((a) => a.capability_area === area);
          if (!row) return null;
          return (
            <tr key={p.person_id} className="border-t border-slate-800/60">
              <td className="py-2 pr-3">
                <Link to={`/crew/${p.person_id}`} className="text-blue-400 hover:text-blue-300">
                  {p.person_name}
                </Link>
              </td>
              <td className="py-2 pr-3">
                <TRatingBadge rating={row.rating} />
              </td>
              <td className="py-2 text-xs text-slate-400">
                {row.contributing_factors.length === 0 ? (
                  <span className="text-green-400/80">All anchor tasks current</span>
                ) : (
                  <ul className="list-disc list-inside space-y-0.5">
                    {row.contributing_factors.map((f, i) => (
                      <li key={i}>{f}</li>
                    ))}
                  </ul>
                )}
              </td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}