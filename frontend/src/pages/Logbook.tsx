import { useState, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";
import { format, parseISO } from "date-fns";
import {
  ArrowLeft,
  ChevronDown,
  ChevronUp,
  Download,
  Monitor,
} from "lucide-react";
import { fetchAircraft } from "../lib/api";
import {
  fetchLogbook,
  downloadLogbookPdf,
  downloadLogbookPdfFiltered,
} from "../lib/logbook";
import Loading from "../components/Loading";
import LogbookEntryDetail from "../components/LogbookEntryDetail";
import type { LogbookEntry, LogbookFilters, LogbookTotals } from "../types/logbook";

// ── Constants ────────────────────────────────────────────────────────────────

const CREW_POSITIONS = ["HAC", "H2P", "H2P_U", "CREW_CHIEF", "AIRCREW", "AWS"];
const FLIGHT_MODES = ["LIVE", "SIM_TOFT"];

// ── Helpers ──────────────────────────────────────────────────────────────────

function fmtDate(dateStr: string): string {
  if (!dateStr) return "—";
  return format(parseISO(dateStr), "d MMM yyyy");
}

function fmtNum(n: number): string {
  return n === 0 ? "" : n.toFixed(1);
}

function fmtInt(n: number): string {
  return n === 0 ? "" : String(n);
}

function pilotRoleLabel(entry: LogbookEntry): string {
  if (entry.ac_commander_hours > 0) return "AC";
  if (entry.first_pilot_hours > 0) return "1P";
  if (entry.copilot_hours > 0) return "CoP";
  if (entry.mission_commander_hours > 0) return "MC";
  if (entry.instructor_hours > 0) return "IP";
  return "";
}

function instrCell(entry: LogbookEntry): string {
  const a = entry.actual_instrument_hours;
  const s = entry.sim_instrument_hours;
  if (a === 0 && s === 0) return "";
  return `${a.toFixed(1)}/${s.toFixed(1)}`;
}

function landingsCell(entry: LogbookEntry): string {
  const { landings_day: d, landings_night: n, landings_shipboard_day: sd, landings_shipboard_night: sn } = entry;
  if (!d && !n && !sd && !sn) return "";
  return `${d}/${n}/${sd}/${sn}`;
}

// ── Window totals card ───────────────────────────────────────────────────────

function TotalsCard({ label, t }: { label: string; t: LogbookTotals }) {
  const instr = (t.total_actual_instrument_hours + t.total_sim_instrument_hours).toFixed(1);
  return (
    <div className="card flex-1 min-w-0">
      <div className="text-xs text-slate-500 uppercase tracking-widest mb-1">{label}</div>
      <div className="text-2xl font-bold text-slate-100">{t.total_hours.toFixed(1)}</div>
      <div className="text-xs text-slate-400 mt-0.5">hrs</div>
      <div className="mt-2 space-y-0.5 text-xs text-slate-400">
        <div>{t.sortie_count} sorties</div>
        <div>{t.night_hours.toFixed(1)} night</div>
        <div>{t.nvg_hours.toFixed(1)} NVG</div>
        <div>{instr} inst</div>
      </div>
    </div>
  );
}

// ── Main page ────────────────────────────────────────────────────────────────

export default function Logbook() {
  const { personId: personIdStr } = useParams<{ personId: string }>();
  const personId = Number(personIdStr);

  // Filter state — individual fields so queryKey array stays flat
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [aircraftId, setAircraftId] = useState<number | undefined>(undefined);
  const [eventCode, setEventCode] = useState("");
  const [crewPosition, setCrewPosition] = useState("");
  const [flightMode, setFlightMode] = useState("");

  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");
  const [selectedEntry, setSelectedEntry] = useState<LogbookEntry | null>(null);
  const [pdfError, setPdfError] = useState<string | null>(null);
  const [downloading, setDownloading] = useState(false);

  const filters: LogbookFilters = useMemo(() => {
    const f: LogbookFilters = {};
    if (dateFrom) f.date_from = dateFrom;
    if (dateTo) f.date_to = dateTo;
    if (aircraftId !== undefined) f.aircraft_id = aircraftId;
    if (eventCode) f.event_code = eventCode;
    if (crewPosition) f.crew_position = crewPosition;
    if (flightMode) f.flight_mode = flightMode;
    return f;
  }, [dateFrom, dateTo, aircraftId, eventCode, crewPosition, flightMode]);

  const hasFilter =
    !!(dateFrom || dateTo || aircraftId !== undefined || eventCode || crewPosition || flightMode);

  // ── Data queries ──────────────────────────────────────────────────────────

  const { data: logbook, isLoading, isError } = useQuery({
    queryKey: ["logbook", personId, dateFrom, dateTo, aircraftId, eventCode, crewPosition, flightMode],
    queryFn: () => fetchLogbook(personId, filters),
    enabled: !isNaN(personId),
  });

  const { data: aircraft } = useQuery({
    queryKey: ["aircraft"],
    queryFn: () => fetchAircraft(),
  });

  // ── Derived data ──────────────────────────────────────────────────────────

  const entries = useMemo(() => {
    const e = logbook?.entries ?? [];
    // API returns newest-first (desc). Reverse only for asc.
    return sortDir === "asc" ? [...e].reverse() : e;
  }, [logbook?.entries, sortDir]);

  const footerTotals = useMemo(() => ({
    count: entries.length,
    total_hours: entries.reduce((s, e) => s + e.total_hours, 0),
    instrument_hours: entries.reduce((s, e) => s + e.actual_instrument_hours + e.sim_instrument_hours, 0),
    night_hours: entries.reduce((s, e) => s + e.night_hours, 0),
    nvg_hours: entries.reduce((s, e) => s + e.nvg_hours, 0),
  }), [entries]);

  // ── Guards ────────────────────────────────────────────────────────────────

  if (isNaN(personId)) {
    return (
      <div className="card border-red-600/50 bg-red-950/20 text-red-300">
        Invalid person ID.
      </div>
    );
  }
  if (isLoading) return <Loading message="Loading logbook…" />;
  if (isError || !logbook) {
    return (
      <div className="card border-red-600/50 bg-red-950/20 text-red-300">
        Failed to load logbook. Is the backend running on port 8001?
      </div>
    );
  }

  const { person, totals } = logbook;
  const [lastName, firstName] = person.name.split(", ");
  const firstInitial = firstName?.[0] ?? "";

  // ── PDF handlers ──────────────────────────────────────────────────────────

  async function handleDownloadFull() {
    setDownloading(true);
    setPdfError(null);
    try {
      await downloadLogbookPdf(personId, lastName, firstInitial);
    } catch {
      setPdfError("PDF download failed. WeasyPrint may not be installed on the server (HTTP 503).");
    } finally {
      setDownloading(false);
    }
  }

  async function handleDownloadFiltered() {
    if (!hasFilter || downloading) return;
    setDownloading(true);
    setPdfError(null);
    try {
      await downloadLogbookPdfFiltered(personId, filters, lastName, firstInitial);
    } catch {
      setPdfError("PDF download failed. WeasyPrint may not be installed on the server (HTTP 503).");
    } finally {
      setDownloading(false);
    }
  }

  function clearFilters() {
    setDateFrom("");
    setDateTo("");
    setAircraftId(undefined);
    setEventCode("");
    setCrewPosition("");
    setFlightMode("");
  }

  // ── Render ────────────────────────────────────────────────────────────────

  return (
    <>
      <div className="space-y-4">
        {/* Back link */}
        <Link
          to={`/crew/${person.id}`}
          className="inline-flex items-center gap-1 text-sm text-slate-400 hover:text-slate-200"
        >
          <ArrowLeft size={14} /> Back to crew
        </Link>

        {/* ── Page header ── */}
        <div className="card">
          <div className="flex items-start justify-between flex-wrap gap-3">
            <div>
              <h1>Flight Logbook</h1>
              <div className="text-sm text-slate-400 mt-1">
                {person.name}
                {person.rank && <span> · {person.rank}</span>}
                {person.callsign && <span> · "{person.callsign}"</span>}
                <span className="ml-1 uppercase text-slate-500">({person.role})</span>
              </div>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <button
                onClick={handleDownloadFull}
                disabled={downloading}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm rounded bg-blue-700 hover:bg-blue-600 disabled:bg-slate-700 disabled:text-slate-400 disabled:cursor-not-allowed text-white font-medium transition-colors"
              >
                <Download size={14} />
                Download Logbook (PDF)
              </button>
              <button
                onClick={handleDownloadFiltered}
                disabled={!hasFilter || downloading}
                title={!hasFilter ? "Apply a filter first to enable filtered PDF" : "Download filtered view"}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm rounded bg-slate-700 hover:bg-slate-600 disabled:bg-slate-800 disabled:text-slate-500 disabled:cursor-not-allowed text-white font-medium transition-colors"
              >
                <Download size={14} />
                Download Filtered View (PDF)
              </button>
            </div>
          </div>
          {pdfError && (
            <p className="mt-2 text-xs text-red-400">{pdfError}</p>
          )}
        </div>

        {/* ── Four-window totals ── */}
        <div className="flex gap-3 flex-wrap">
          <TotalsCard label="Career" t={totals.career} />
          <TotalsCard label="Last 365d" t={totals.last_365d} />
          <TotalsCard label="Last 90d" t={totals.last_90d} />
          <TotalsCard label="Last 30d" t={totals.last_30d} />
        </div>

        {/* ── Filter bar ── */}
        <div className="card">
          <div className="flex flex-wrap items-end gap-2">
            <div className="flex flex-col gap-0.5">
              <label className="text-xs text-slate-500">Date From</label>
              <input
                type="date"
                value={dateFrom}
                onChange={(e) => setDateFrom(e.target.value)}
                className="bg-slate-800 border border-slate-700 rounded px-2 py-1 text-sm text-slate-200 focus:outline-none focus:border-blue-500"
              />
            </div>
            <div className="flex flex-col gap-0.5">
              <label className="text-xs text-slate-500">Date To</label>
              <input
                type="date"
                value={dateTo}
                onChange={(e) => setDateTo(e.target.value)}
                className="bg-slate-800 border border-slate-700 rounded px-2 py-1 text-sm text-slate-200 focus:outline-none focus:border-blue-500"
              />
            </div>
            <div className="flex flex-col gap-0.5">
              <label className="text-xs text-slate-500">Aircraft</label>
              <select
                value={aircraftId ?? ""}
                onChange={(e) =>
                  setAircraftId(e.target.value ? Number(e.target.value) : undefined)
                }
                className="bg-slate-800 border border-slate-700 rounded px-2 py-1 text-sm text-slate-200 focus:outline-none focus:border-blue-500"
              >
                <option value="">All</option>
                {(aircraft ?? []).map((ac) => (
                  <option key={ac.id} value={ac.id}>
                    {ac.side_number ?? ac.bureau_number}
                  </option>
                ))}
              </select>
            </div>
            <div className="flex flex-col gap-0.5">
              <label className="text-xs text-slate-500">Event Code</label>
              <input
                type="text"
                placeholder="e.g. P200"
                value={eventCode}
                onChange={(e) => setEventCode(e.target.value)}
                className="bg-slate-800 border border-slate-700 rounded px-2 py-1 text-sm text-slate-200 focus:outline-none focus:border-blue-500 w-24"
              />
            </div>
            <div className="flex flex-col gap-0.5">
              <label className="text-xs text-slate-500">Position</label>
              <select
                value={crewPosition}
                onChange={(e) => setCrewPosition(e.target.value)}
                className="bg-slate-800 border border-slate-700 rounded px-2 py-1 text-sm text-slate-200 focus:outline-none focus:border-blue-500"
              >
                <option value="">All</option>
                {CREW_POSITIONS.map((p) => (
                  <option key={p} value={p}>
                    {p.replace(/_/g, " ")}
                  </option>
                ))}
              </select>
            </div>
            <div className="flex flex-col gap-0.5">
              <label className="text-xs text-slate-500">Mode</label>
              <select
                value={flightMode}
                onChange={(e) => setFlightMode(e.target.value)}
                className="bg-slate-800 border border-slate-700 rounded px-2 py-1 text-sm text-slate-200 focus:outline-none focus:border-blue-500"
              >
                <option value="">All</option>
                {FLIGHT_MODES.map((m) => (
                  <option key={m} value={m}>
                    {m.replace(/_/g, " ")}
                  </option>
                ))}
              </select>
            </div>
            <button
              onClick={clearFilters}
              disabled={!hasFilter}
              className={
                hasFilter
                  ? "px-3 py-1 text-xs rounded border border-slate-700 text-slate-400 hover:text-slate-200 hover:border-slate-600 transition-colors self-end"
                  : "px-3 py-1 text-xs rounded border border-slate-800 text-slate-600 cursor-not-allowed self-end"
              }
            >
              Clear
            </button>
          </div>
        </div>

        {/* ── Logbook table ── */}
        <div className="card p-0 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-xs" style={{ minWidth: "780px" }}>
              <thead className="bg-slate-900/70 text-slate-400 uppercase tracking-wide">
                <tr>
                  <th
                    className="text-left px-3 py-2 font-medium cursor-pointer select-none hover:text-slate-200 transition-colors whitespace-nowrap"
                    style={{ width: "90px" }}
                    onClick={() => setSortDir((d) => (d === "desc" ? "asc" : "desc"))}
                  >
                    Date{" "}
                    {sortDir === "desc" ? (
                      <ChevronDown size={14} className="inline text-blue-400" />
                    ) : (
                      <ChevronUp size={14} className="inline text-blue-400" />
                    )}
                  </th>
                  <th className="text-left px-2 py-2 font-medium" style={{ width: "80px" }}>
                    Side/BuNo
                  </th>
                  <th className="text-left px-2 py-2 font-medium" style={{ width: "60px" }}>
                    TMS
                  </th>
                  <th className="text-left px-2 py-2 font-medium" style={{ width: "55px" }}>
                    Code
                  </th>
                  <th className="text-center px-1 py-2 font-medium" style={{ width: "28px" }}>
                    M
                  </th>
                  <th className="text-right px-2 py-2 font-medium" style={{ width: "85px" }}>
                    Pilot
                  </th>
                  <th className="text-right px-2 py-2 font-medium" style={{ width: "55px" }}>
                    Spec
                  </th>
                  <th className="text-right px-2 py-2 font-medium" style={{ width: "75px" }}>
                    Inst A/S
                  </th>
                  <th className="text-right px-2 py-2 font-medium" style={{ width: "48px" }}>
                    Night
                  </th>
                  <th className="text-right px-2 py-2 font-medium" style={{ width: "44px" }}>
                    NVG
                  </th>
                  <th className="text-right px-2 py-2 font-medium" style={{ width: "78px" }}>
                    Ldgs D/N/SD/SN
                  </th>
                  <th className="text-right px-2 py-2 font-medium" style={{ width: "40px" }}>
                    Appr
                  </th>
                  <th className="text-left px-2 py-2 font-medium">Remarks</th>
                </tr>
              </thead>
              <tbody>
                {entries.map((entry) => {
                  const roleLabel = pilotRoleLabel(entry);
                  const qual = entry.crew_qual_code;
                  const pilotCell =
                    roleLabel
                      ? `${entry.total_hours.toFixed(1)} / ${roleLabel}${qual ? ` · ${qual}` : ""}`
                      : `${entry.total_hours.toFixed(1)}${qual ? ` · ${qual}` : ""}`;

                  return (
                    <tr
                      key={entry.flight_log_id}
                      className="border-t border-slate-800 hover:bg-slate-800/50 cursor-pointer transition-colors"
                      onClick={() => setSelectedEntry(entry)}
                    >
                      <td className="px-3 py-2 text-slate-200 whitespace-nowrap">
                        {fmtDate(entry.date)}
                      </td>
                      <td className="px-2 py-2 text-slate-300">
                        {entry.side_number && (
                          <div className="leading-tight">
                            <div>{entry.side_number}</div>
                            {entry.bureau_number && (
                              <div className="text-slate-500 text-[10px]">{entry.bureau_number}</div>
                            )}
                          </div>
                        )}
                      </td>
                      <td className="px-2 py-2 text-slate-300">{entry.tms ?? "—"}</td>
                      <td className="px-2 py-2 text-slate-300">{entry.event_code ?? "—"}</td>
                      <td className="px-1 py-2 text-center text-slate-500">
                        {entry.flight_mode === "SIM_TOFT" && (
                          <span title="SIM">
                            <Monitor size={14} className="..." />
                          </span>
                        )}
                      </td>
                      <td className="px-2 py-2 text-right text-slate-200 whitespace-nowrap">
                        {pilotCell}
                      </td>
                      <td className="px-2 py-2 text-right text-slate-300">
                        {fmtNum(entry.special_crew_time_hours)}
                      </td>
                      <td className="px-2 py-2 text-right text-slate-300 font-mono">
                        {instrCell(entry)}
                      </td>
                      <td className="px-2 py-2 text-right text-slate-300">
                        {fmtNum(entry.night_hours)}
                      </td>
                      <td className="px-2 py-2 text-right text-slate-300">
                        {fmtNum(entry.nvg_hours)}
                      </td>
                      <td className="px-2 py-2 text-right text-slate-300 font-mono">
                        {landingsCell(entry)}
                      </td>
                      <td className="px-2 py-2 text-right text-slate-300">
                        {fmtInt(entry.approaches.length)}
                      </td>
                      <td className="px-2 py-2 text-slate-400 max-w-0">
                        <span
                          className="block truncate"
                          title={entry.remarks ?? undefined}
                        >
                          {entry.remarks}
                        </span>
                      </td>
                    </tr>
                  );
                })}
                {entries.length === 0 && (
                  <tr>
                    <td
                      colSpan={13}
                      className="px-4 py-10 text-center text-slate-500"
                    >
                      No logbook entries{hasFilter ? " match the current filter." : "."}
                    </td>
                  </tr>
                )}
              </tbody>
              <tfoot>
                <tr className="border-t-2 border-slate-700 bg-slate-900/60">
                  <td
                    colSpan={13}
                    className="px-3 py-2 text-xs text-slate-400 font-semibold"
                  >
                    Filtered Total —{" "}
                    <span className="text-slate-200">{footerTotals.count}</span>{" "}
                    {footerTotals.count === 1 ? "entry" : "entries"},{" "}
                    <span className="text-slate-200">{footerTotals.total_hours.toFixed(1)}</span> hrs,{" "}
                    <span className="text-slate-200">{footerTotals.instrument_hours.toFixed(1)}</span> inst,{" "}
                    <span className="text-slate-200">{footerTotals.night_hours.toFixed(1)}</span> night,{" "}
                    <span className="text-slate-200">{footerTotals.nvg_hours.toFixed(1)}</span> NVG
                  </td>
                </tr>
              </tfoot>
            </table>
          </div>
        </div>
      </div>

      {/* ── Detail modal ── */}
      <LogbookEntryDetail
        entry={selectedEntry}
        onClose={() => setSelectedEntry(null)}
      />
    </>
  );
}
