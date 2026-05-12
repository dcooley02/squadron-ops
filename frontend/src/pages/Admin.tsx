import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { fetchCurrencyTypes, fetchPersons, type CurrencyTypeOut, type PersonSummary } from "../lib/api";
import Loading from "../components/Loading";
import Badge from "../components/Badge";

type Tab = "currencies" | "people" | "syllabus";

const AUDIENCE_LABELS: Record<string, string> = {
  ALL_PILOTS: "All Pilots",
  HAC_ONLY: "HAC",
  AMCM_QUAL_PILOTS: "AMCM Pilots",
  ALL_AIRCREWMEN: "All Aircrew",
  AWS_ONLY: "AWS",
  HOIST_OP_QUAL: "Hoist Op",
};

const ROLE_LABEL: Record<string, string> = {
  pilot: "Pilot",
  aircrew: "Aircrew",
  co_xo: "CO/XO",
  sdo: "SDO",
  training_officer: "Training",
  maint_control: "Maint",
  admin: "Admin",
};

export default function Admin() {
  const [tab, setTab] = useState<Tab>("currencies");

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1>Admin</h1>
      </div>

      {/* Tab bar */}
      <div className="flex gap-1 border-b border-slate-800">
        {(["currencies", "people", "syllabus"] as Tab[]).map((t) => (
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
            {t === "currencies" ? "Currency Catalog" : t.charAt(0).toUpperCase() + t.slice(1)}
          </button>
        ))}
      </div>

      {tab === "currencies" && <CurrencyTab />}
      {tab === "people" && <PeopleTab />}
      {tab === "syllabus" && (
        <div className="card text-slate-500 text-sm">Syllabus management not yet implemented.</div>
      )}
    </div>
  );
}

// ── Currency Catalog tab ──────────────────────────────────────────────────────

function CurrencyTab() {
  const { data: types, isLoading } = useQuery({
    queryKey: ["currency-types"],
    queryFn: fetchCurrencyTypes,
  });

  if (isLoading) return <Loading />;

  return (
    <div className="card overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-slate-800 text-left text-xs text-slate-500 uppercase">
            <th className="py-2 pr-4 font-medium">Code</th>
            <th className="py-2 pr-4 font-medium">Name</th>
            <th className="py-2 pr-4 font-medium">Window</th>
            <th className="py-2 pr-4 font-medium">Applies To</th>
            <th className="py-2 pr-4 font-medium">Requirement</th>
            <th className="py-2 font-medium">Sim</th>
          </tr>
        </thead>
        <tbody>
          {(types ?? []).map((ct) => (
            <CurrencyRow key={ct.id} ct={ct} />
          ))}
        </tbody>
      </table>
    </div>
  );
}

function CurrencyRow({ ct }: { ct: CurrencyTypeOut }) {
  const audiences = ct.applicability.map((a) => AUDIENCE_LABELS[a.applies_to] ?? a.applies_to);
  const uniqueAudiences = [...new Set(audiences)];

  return (
    <tr className="border-b border-slate-800/60 last:border-0 hover:bg-slate-800/20 align-top">
      <td className="py-2.5 pr-4 font-mono text-blue-400 text-xs whitespace-nowrap">{ct.code}</td>
      <td className="py-2.5 pr-4 text-slate-200 font-medium">{ct.name}</td>
      <td className="py-2.5 pr-4 text-slate-400 whitespace-nowrap">{ct.periodicity_days}d</td>
      <td className="py-2.5 pr-4">
        <div className="flex flex-wrap gap-1">
          {uniqueAudiences.map((a) => (
            <Badge key={a} variant="neutral" className="text-[10px]">{a}</Badge>
          ))}
        </div>
      </td>
      <td className="py-2.5 pr-4 text-slate-400 text-xs max-w-64">
        {ct.requirement_text}
        {ct.min_hours != null && (
          <span className="ml-1 text-slate-500">({ct.min_hours}h min)</span>
        )}
        {ct.min_count != null && ct.count_unit != null && (
          <span className="ml-1 text-slate-500">
            ({ct.min_count} {ct.count_unit})
          </span>
        )}
      </td>
      <td className="py-2.5">
        <Badge variant={ct.sim_eligible ? "success" : "neutral"}>
          {ct.sim_eligible ? "Yes" : "No"}
        </Badge>
      </td>
    </tr>
  );
}

// ── People tab ────────────────────────────────────────────────────────────────

function PeopleTab() {
  const { data: persons, isLoading } = useQuery({
    queryKey: ["persons", "all"],
    queryFn: () => fetchPersons(),
  });

  if (isLoading) return <Loading />;

  return (
    <div className="card overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-slate-800 text-left text-xs text-slate-500 uppercase">
            <th className="py-2 pr-4 font-medium">Name</th>
            <th className="py-2 pr-4 font-medium">Rank</th>
            <th className="py-2 pr-4 font-medium">Role</th>
            <th className="py-2 font-medium">Status</th>
          </tr>
        </thead>
        <tbody>
          {(persons ?? []).map((p) => (
            <PeopleRow key={p.id} person={p} />
          ))}
        </tbody>
      </table>
    </div>
  );
}

function PeopleRow({ person }: { person: PersonSummary }) {
  return (
    <tr className="border-b border-slate-800/60 last:border-0 hover:bg-slate-800/20">
      <td className="py-2.5 pr-4">
        <Link
          to={`/crew/${person.id}`}
          className="text-slate-200 hover:text-blue-400 transition-colors"
        >
          {person.last_name}, {person.first_name}
        </Link>
        {person.callsign && (
          <span className="text-slate-500 text-xs ml-2">"{person.callsign}"</span>
        )}
      </td>
      <td className="py-2.5 pr-4 text-slate-400 text-xs">{person.rank ?? "—"}</td>
      <td className="py-2.5 pr-4">
        <Badge variant="neutral">{ROLE_LABEL[person.role] ?? person.role}</Badge>
      </td>
      <td className="py-2.5">
        <Badge variant={person.is_active ? "success" : "neutral"}>
          {person.is_active ? "Active" : "Inactive"}
        </Badge>
      </td>
    </tr>
  );
}
