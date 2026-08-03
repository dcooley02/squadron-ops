import { ShieldCheck } from "lucide-react";
import type { AircraftStatus } from "../../lib/api";
import Badge from "../../components/Badge";
import { STATUS_VARIANT } from "./statusHelpers";

type ReleaseForecast = {
  projected_release_date?: string | null;
  blockers: string[];
} | null | undefined;

export default function ReleaseSection({
  computedStatus,
  stampedStatus,
  statusDrift,
  releaseBlockers,
  releaseReady,
  releaseForecast,
  onOpenRelease,
}: {
  computedStatus: AircraftStatus;
  stampedStatus: AircraftStatus;
  statusDrift: boolean;
  releaseBlockers: string[];
  releaseReady: boolean;
  releaseForecast: ReleaseForecast;
  onOpenRelease: () => void;
}) {
  return (
    <div
      className={`card ${statusDrift ? "border-green-800/40 bg-green-950/10" : ""}`}
    >
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <h2 className="flex items-center gap-2">
            <ShieldCheck size={18} className="text-green-400" />
            QA Release
          </h2>
          <p className="text-sm text-slate-400 mt-1">
            After QA signoff, release aircraft safe for flight and stamp line status to{" "}
            <Badge variant={STATUS_VARIANT[computedStatus]}>{computedStatus}</Badge>
          </p>
        </div>
        <button
          onClick={onOpenRelease}
          className="btn-primary text-sm flex items-center gap-1.5 shrink-0"
        >
          <ShieldCheck size={14} />
          {statusDrift && releaseReady ? "Release for Flight" : "QA Release"}
        </button>
      </div>

      {releaseBlockers.length > 0 ? (
        <div className="mt-3 p-2.5 bg-red-950/20 border border-red-800/30 rounded text-xs text-red-300 space-y-1">
          <div className="font-medium text-red-400">Not safe for flight — resolve:</div>
          {releaseBlockers.map((b) => (
            <div key={b}>• {b}</div>
          ))}
        </div>
      ) : statusDrift ? (
        <div className="mt-3 p-2.5 bg-green-950/20 border border-green-800/30 rounded text-xs text-green-300">
          Ready for QA release — stamped {stampedStatus} will update to {computedStatus}.
        </div>
      ) : (
        <div className="mt-3 text-xs text-slate-500">
          Stamped status matches computed. QA release available when maintenance state changes.
        </div>
      )}
      {releaseForecast?.projected_release_date && (
        <div className="mt-2 text-xs text-slate-400">
          Projected release: {releaseForecast.projected_release_date}
          {releaseForecast.blockers.length > 0 && (
            <span className="text-yellow-400"> · {releaseForecast.blockers.length} blocker(s)</span>
          )}
        </div>
      )}
    </div>
  );
}
