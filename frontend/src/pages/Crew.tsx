import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { Search } from "lucide-react";
import { fetchPersons, type Role } from "../lib/api";
import Loading from "../components/Loading";
import Badge from "../components/Badge";

type RoleFilter = "all" | Role;

const ROLE_FILTERS: { value: RoleFilter; label: string }[] = [
  { value: "all", label: "All" },
  { value: "pilot", label: "Pilots" },
  { value: "aircrew", label: "Aircrew" },
];

const ROLE_BADGE_VARIANT: Record<Role, "neutral" | "info" | "success"> = {
  pilot: "info",
  aircrew: "success",
  sdo: "neutral",
  training_officer: "neutral",
  maint_control: "neutral",
  co_xo: "neutral",
  admin: "neutral",
};

export default function Crew() {
  const [roleFilter, setRoleFilter] = useState<RoleFilter>("all");
  const [search, setSearch] = useState("");

  const { data, isLoading, error } = useQuery({
    queryKey: ["persons", roleFilter],
    queryFn: () => fetchPersons(roleFilter === "all" ? undefined : roleFilter),
  });

  if (isLoading) return <Loading message="Loading personnel..." />;
  if (error || !data) {
    return (
      <div className="card border-red-600/50 bg-red-950/20 text-red-300">
        Failed to load personnel.
      </div>
    );
  }

  // Client-side text search across name and callsign
  const filtered = data.filter((p) => {
    if (!search) return true;
    const haystack = `${p.last_name} ${p.first_name} ${p.callsign ?? ""}`.toLowerCase();
    return haystack.includes(search.toLowerCase());
  });

  return (
    <div className="space-y-4">
      <div>
        <h1>Crew</h1>
        <p className="text-sm text-slate-400 mt-1">
          {data.length} squadron personnel
        </p>
      </div>

      {/* Filter + search bar */}
      <div className="flex flex-wrap gap-3 items-center">
        <div className="flex gap-1 bg-slate-900 border border-slate-800 rounded-md p-1">
          {ROLE_FILTERS.map((f) => (
            <button
              key={f.value}
              onClick={() => setRoleFilter(f.value)}
              className={
                roleFilter === f.value
                  ? "px-3 py-1 text-xs rounded bg-slate-800 text-white"
                  : "px-3 py-1 text-xs rounded text-slate-400 hover:text-slate-200"
              }
            >
              {f.label}
            </button>
          ))}
        </div>
        <div className="relative flex-1 max-w-xs">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
          <input
            type="text"
            placeholder="Search name or callsign..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full bg-slate-900 border border-slate-800 rounded-md pl-9 pr-3 py-1.5 text-sm placeholder:text-slate-500 focus:outline-none focus:border-slate-600"
          />
        </div>
      </div>

      {/* Results table */}
      <div className="card p-0 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-slate-900/60 text-xs uppercase tracking-wide text-slate-400">
            <tr>
              <th className="text-left px-4 py-2 font-medium">Name</th>
              <th className="text-left px-4 py-2 font-medium">Callsign</th>
              <th className="text-left px-4 py-2 font-medium">Rank</th>
              <th className="text-left px-4 py-2 font-medium">Role</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((p) => (
              <tr
                key={p.id}
                className="border-t border-slate-800 hover:bg-slate-900/40 transition-colors"
              >
                <td className="px-4 py-2.5">
                  <Link
                    to={`/crew/${p.id}`}
                    className="font-medium text-slate-100 hover:text-blue-400"
                  >
                    {p.last_name}, {p.first_name}
                  </Link>
                </td>
                <td className="px-4 py-2.5 text-slate-300">
                  {p.callsign ?? "—"}
                </td>
                <td className="px-4 py-2.5 text-slate-300">{p.rank ?? "—"}</td>
                <td className="px-4 py-2.5">
                  <Badge variant={ROLE_BADGE_VARIANT[p.role]}>
                    {p.role.replace("_", " ")}
                  </Badge>
                </td>
              </tr>
            ))}
            {filtered.length === 0 && (
              <tr>
                <td colSpan={4} className="px-4 py-8 text-center text-slate-500">
                  No matches.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}