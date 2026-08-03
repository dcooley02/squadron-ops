import { useState } from "react";
import { Link } from "react-router-dom";
import { Plus, Wrench } from "lucide-react";
import type { Discrepancy } from "../../lib/api";
import Badge from "../../components/Badge";
import { formatDate } from "../../lib/dates";
import { SEV_VARIANT, WS_VARIANT, WS_LABEL } from "./statusHelpers";
import UpdateDiscrepancyModal from "./UpdateDiscrepancyModal";

function DiscrepancyRow({ disc, showHistory }: { disc: Discrepancy; showHistory?: boolean }) {
  const [modalOpen, setModalOpen] = useState(false);

  return (
    <>
      <div className="py-3 border-b border-slate-800 last:border-0">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              {disc.maf_number && (
                <span className="font-mono text-sm font-semibold text-slate-200">
                  {disc.maf_number}
                </span>
              )}
              <Badge variant={SEV_VARIANT[disc.severity]}>{disc.severity}</Badge>
              <Badge variant={WS_VARIANT[disc.work_status]}>
                {WS_LABEL[disc.work_status]}
              </Badge>
              {disc.type_wo_code && (
                <span
                  className="font-mono text-[10px] uppercase tracking-wide text-slate-300 bg-slate-800 border border-slate-700 rounded px-1 py-0.5"
                  title="CNAF M-4790.2 Type Work Order"
                >
                  WO·{disc.type_wo_code}
                </span>
              )}
              {disc.jcn && (
                <span
                  className="font-mono text-[10px] text-slate-400"
                  title="Job Control Number — CNAF M-4790.2"
                >
                  JCN {disc.jcn}
                </span>
              )}
              {disc.system_affected && (
                <span className="text-xs text-slate-400 font-mono">{disc.system_affected}</span>
              )}
              {disc.work_center_code && (
                <span className="text-xs text-slate-500">WC {disc.work_center_code}</span>
              )}
              {disc.has_qa_signoff && (
                <Badge variant="success" className="text-xs">QA signed</Badge>
              )}
            </div>
            {disc.reported_by_name && (
              <div className="text-xs text-slate-500 mt-0.5">Reported by {disc.reported_by_name}</div>
            )}
            <p className="text-sm text-slate-300 mt-1">{disc.description}</p>
            <div className="flex items-center gap-3 mt-1 text-xs text-slate-500">
              <span>Opened {formatDate(disc.opened_date)}</span>
              {disc.sortie_id && (
                <Link
                  to={`/sorties/${disc.sortie_id}`}
                  className="text-blue-400 hover:text-blue-300"
                >
                  Sortie #{disc.sortie_id}
                </Link>
              )}
              {disc.closed_date && (
                <span>Closed {formatDate(disc.closed_date)}</span>
              )}
            </div>
            {showHistory && disc.corrective_action && (
              <div className="mt-2 p-2 bg-slate-800/50 rounded text-xs text-slate-400">
                <span className="text-slate-500">Corrective action: </span>
                {disc.corrective_action}
              </div>
            )}
          </div>
          {!showHistory && (
            <button
              onClick={() => setModalOpen(true)}
              className="btn-secondary text-xs shrink-0 flex items-center gap-1"
            >
              <Wrench size={12} />
              Update
            </button>
          )}
        </div>
      </div>

      {modalOpen && (
        <UpdateDiscrepancyModal disc={disc} onClose={() => setModalOpen(false)} />
      )}
    </>
  );
}

export default function DiscrepancySection({
  openDiscs,
  onCreateClick,
}: {
  openDiscs: Discrepancy[];
  onCreateClick: () => void;
}) {
  return (
    <div className="card">
      <div className="flex items-center justify-between mb-3">
        <h2>
          Open Discrepancies
          {openDiscs.length > 0 && (
            <span className="ml-2 text-sm font-normal text-slate-400">
              ({openDiscs.length})
            </span>
          )}
        </h2>
        <button
          onClick={onCreateClick}
          className="btn-secondary text-xs flex items-center gap-1"
        >
          <Plus size={12} /> New
        </button>
      </div>
      {openDiscs.length === 0 ? (
        <p className="text-sm text-slate-500">No open discrepancies.</p>
      ) : (
        <div>
          {openDiscs.map((d) => (
            <DiscrepancyRow key={d.id} disc={d} />
          ))}
        </div>
      )}
    </div>
  );
}

export function DiscrepancyHistorySection({
  closedDiscs,
}: {
  closedDiscs: Discrepancy[];
}) {
  return (
    <div className="card">
      <h2 className="mb-3 text-slate-400">
        Discrepancy History
        {closedDiscs.length > 0 && (
          <span className="ml-2 text-sm font-normal text-slate-500">
            ({closedDiscs.length} closed)
          </span>
        )}
      </h2>
      {closedDiscs.length === 0 ? (
        <p className="text-sm text-slate-500">No closed discrepancies on record.</p>
      ) : (
        <div>
          {closedDiscs.map((d) => (
            <DiscrepancyRow key={d.id} disc={d} showHistory />
          ))}
        </div>
      )}
    </div>
  );
}
