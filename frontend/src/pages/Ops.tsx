import { useState } from "react";
import axios from "axios";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { format, parseISO } from "date-fns";
import {
  fetchDayOps,
  publishSchedule,
  patchSortieOpsStatus,
  downloadAtoPdf,
  downloadBriefSheetPdf,
  type SortieOpsStatus,
  type DayOpsSortie,
} from "../lib/api";
import Loading from "../components/Loading";
import PdfExportButton from "../components/PdfExportButton";
import Badge from "../components/Badge";
import { useToast } from "../components/Toast";

const OPS_STATUS_ORDER: SortieOpsStatus[] = [
  "PLANNED", "PUBLISHED", "BRIEFED", "MANNED", "AIRBORNE", "RECOVERED", "DEBRIEFED",
];

const OPS_VARIANT: Record<SortieOpsStatus, "neutral" | "info" | "success" | "warning"> = {
  PLANNED: "neutral",
  PUBLISHED: "info",
  BRIEFED: "info",
  MANNED: "warning",
  AIRBORNE: "warning",
  RECOVERED: "success",
  DEBRIEFED: "success",
};

function nextOpsStatus(current: SortieOpsStatus): SortieOpsStatus | null {
  const idx = OPS_STATUS_ORDER.indexOf(current);
  if (idx < 0 || idx >= OPS_STATUS_ORDER.length - 1) return null;
  return OPS_STATUS_ORDER[idx + 1];
}

function queryErrorDetail(error: unknown): string | null {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) {
      return detail
        .map((item) =>
          typeof item === "object" && item && "msg" in item
            ? String((item as { msg: string }).msg)
            : String(item)
        )
        .join("; ");
    }
    return error.message || null;
  }
  if (error && typeof error === "object" && "message" in error) {
    return String((error as { message: string }).message);
  }
  return null;
}

export default function Ops() {
  const today = format(new Date(), "yyyy-MM-dd");
  const [opsDate, setOpsDate] = useState(today);
  const queryClient = useQueryClient();
  const toast = useToast();

  const { data, isLoading, error } = useQuery({
    queryKey: ["day-ops", opsDate],
    queryFn: () => fetchDayOps(opsDate),
  });

  const publishMut = useMutation({
    mutationFn: () => publishSchedule(opsDate, { remarks: "Published from Ops console" }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["day-ops", opsDate] });
      queryClient.invalidateQueries({ queryKey: ["upcoming-sorties"] });
      toast.showToast("Schedule published — crew notified", "success");
    },
    onError: () => toast.showToast("Publish failed — schedule may already be locked", "error"),
  });

  const advanceMut = useMutation({
    mutationFn: ({ id, status }: { id: number; status: SortieOpsStatus }) =>
      patchSortieOpsStatus(id, { ops_status: status }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["day-ops", opsDate] }),
  });

  if (isLoading) return <Loading message="Loading day-of ops..." />;
  if (error || !data) {
    const detail = error ? queryErrorDetail(error) : null;
    return (
      <div className="card border-red-600/50 bg-red-950/20 text-red-300">
        <p>Failed to load ops data.</p>
        {detail && <p className="text-sm mt-2 text-red-400/80">{detail}</p>}
        <p className="text-sm mt-2 text-slate-400">
          Confirm the backend is running on :8001 and try reseeding with{" "}
          <code className="text-slate-300">./scripts/demo-prep.sh</code>.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1>Day-of Operations</h1>
          <p className="text-sm text-slate-400 mt-1">
            SDO console — publish schedule, track sortie status, export ATO and brief sheets
          </p>
        </div>
        <div className="flex items-center gap-2">
          <input
            type="date"
            value={opsDate}
            onChange={(e) => setOpsDate(e.target.value)}
            className="bg-slate-900 border border-slate-700 rounded px-2 py-1 text-sm"
          />
          <PdfExportButton
            label="Export ATO PDF"
            onDownload={() => downloadAtoPdf(opsDate)}
          />
          {!data.is_published && data.sortie_count > 0 && (
            <button
              onClick={() => publishMut.mutate()}
              disabled={publishMut.isPending}
              className="px-3 py-1.5 text-sm rounded bg-blue-700 hover:bg-blue-600 text-white font-medium"
            >
              Publish Schedule
            </button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
        <div className="card">
          <div className="text-xs text-slate-500 uppercase">Schedule</div>
          <div className="text-2xl font-bold mt-1">
            {data.is_published ? (
              <span className="text-green-400">Published</span>
            ) : (
              <span className="text-yellow-400">Draft</span>
            )}
          </div>
          {data.publication?.published_by_name && (
            <div className="text-xs text-slate-500 mt-1">
              by {data.publication.published_by_name}
            </div>
          )}
        </div>
        <div className="card">
          <div className="text-xs text-slate-500 uppercase">Sorties</div>
          <div className="text-2xl font-bold mt-1">{data.sortie_count}</div>
        </div>
        <div className="card">
          <div className="text-xs text-slate-500 uppercase">Airborne</div>
          <div className="text-2xl font-bold mt-1 text-yellow-400">{data.airborne_count}</div>
        </div>
        <div className="card">
          <div className="text-xs text-slate-500 uppercase">Date</div>
          <div className="text-lg font-medium mt-1">
            {format(parseISO(data.ops_date), "EEE, MMM d")}
          </div>
        </div>
      </div>

      <section className="card">
        <h2 className="mb-3">Watchbill</h2>
        {data.watchbill.length === 0 ? (
          <p className="text-sm text-slate-500">No watchbill assignments.</p>
        ) : (
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
            {data.watchbill.map((w) => (
              <div key={w.id} className="rounded border border-slate-800 px-3 py-2">
                <div className="text-xs font-mono text-slate-500">{w.role}</div>
                <div className="text-sm font-medium">{w.person_name}</div>
                {w.shift_label && (
                  <div className="text-xs text-slate-500">{w.shift_label}</div>
                )}
              </div>
            ))}
          </div>
        )}
      </section>

      <section className="card">
        <h2 className="mb-3">Flight schedule</h2>
        {data.sorties.length === 0 ? (
          <p className="text-sm text-slate-500">No sorties on this day.</p>
        ) : (
          <div className="space-y-3">
            {data.sorties.map((s) => (
              <SortieOpsRow
                key={s.id}
                sortie={s}
                onAdvance={(status) => advanceMut.mutate({ id: s.id, status })}
                advancing={advanceMut.isPending}
              />
            ))}
          </div>
        )}
      </section>

      <p className="text-xs text-slate-500">
        Tip: use{" "}
        <Link to="/schedule" className="text-blue-400 hover:text-blue-300">
          Schedule
        </Link>{" "}
        to build the week; publish here locks the day for crew.
      </p>
    </div>
  );
}

function SortieOpsRow({
  sortie,
  onAdvance,
  advancing,
}: {
  sortie: DayOpsSortie;
  onAdvance: (s: SortieOpsStatus) => void;
  advancing: boolean;
}) {
  const next = nextOpsStatus(sortie.ops_status);
  const takeoff = sortie.takeoff_time ? format(parseISO(sortie.takeoff_time), "HH:mm") : "—";

  return (
    <div className="flex flex-wrap items-center gap-3 py-3 border-b border-slate-800 last:border-0">
      <div className="min-w-[4rem] font-mono text-sm text-slate-300">{takeoff}</div>
      <Link
        to={`/sorties/${sortie.id}`}
        className="font-mono text-blue-400 hover:text-blue-300 text-sm min-w-[4rem]"
      >
        {sortie.event_code ?? "—"}
      </Link>
      <span className="text-sm text-slate-400">{sortie.aircraft_side_number ?? "—"}</span>
      <Badge variant={OPS_VARIANT[sortie.ops_status]}>{sortie.ops_status}</Badge>
      <span className="text-sm text-slate-400 flex-1 min-w-0 truncate">
        {sortie.mission_summary ?? sortie.event_type ?? ""}
      </span>
      <span className="text-xs text-slate-500 hidden lg:inline">
        {sortie.crew.map((c) => c.crew_position).join(" · ")}
      </span>
      <PdfExportButton
        label="Brief PDF"
        variant="link"
        showIcon={false}
        onDownload={() => downloadBriefSheetPdf(sortie.id)}
      />
      {next && !sortie.is_complete && (
        <button
          onClick={() => onAdvance(next)}
          disabled={advancing}
          className="text-xs px-2 py-1 rounded border border-slate-700 hover:bg-slate-800"
        >
          → {next}
        </button>
      )}
    </div>
  );
}