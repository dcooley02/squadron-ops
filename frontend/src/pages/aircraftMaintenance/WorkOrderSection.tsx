import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  fetchWorkCenters,
  patchWorkOrder,
  qaSignoffWorkOrder,
  type DiscrepancyWorkStatus,
  type WorkOrder,
} from "../../lib/api";
import Badge from "../../components/Badge";
import { WS_VARIANT, WS_LABEL } from "./statusHelpers";

function WorkOrderRow({ wo, aircraftId }: { wo: WorkOrder; aircraftId: number }) {
  const qc = useQueryClient();
  const { data: centers } = useQuery({ queryKey: ["work-centers"], queryFn: fetchWorkCenters });
  const [signoffNotes, setSignoffNotes] = useState("");

  const patchMut = useMutation({
    mutationFn: (body: { status?: DiscrepancyWorkStatus; work_center_id?: number }) =>
      patchWorkOrder(wo.id, body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["aircraft-work-orders", aircraftId] });
      qc.invalidateQueries({ queryKey: ["aircraft-discrepancies", aircraftId] });
      qc.invalidateQueries({ queryKey: ["aircraft-detail", aircraftId] });
    },
  });

  const signoffMut = useMutation({
    mutationFn: () => qaSignoffWorkOrder(wo.id, { notes: signoffNotes }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["aircraft-work-orders", aircraftId] });
      setSignoffNotes("");
    },
  });

  return (
    <div className="py-3 border-b border-slate-800 last:border-0 text-sm">
      <div className="flex items-center gap-2 flex-wrap">
        <span className="font-mono font-semibold text-slate-200">{wo.jcn}</span>
        <span className="font-mono text-xs text-slate-500">{wo.maf_number}</span>
        <Badge variant={WS_VARIANT[wo.status]}>{WS_LABEL[wo.status]}</Badge>
        {wo.work_center_code && (
          <span className="text-xs text-slate-400">{wo.work_center_code}</span>
        )}
        {wo.has_qa_signoff && (
          <Badge variant="success">QA signed</Badge>
        )}
      </div>
      <div className="flex flex-wrap gap-2 mt-2">
        <select
          value={wo.work_center_id ?? ""}
          onChange={(e) =>
            patchMut.mutate({
              work_center_id: e.target.value ? Number(e.target.value) : undefined,
            })
          }
          className="bg-slate-800 border border-slate-700 rounded px-2 py-1 text-xs"
        >
          <option value="">Route…</option>
          {(centers ?? []).map((c) => (
            <option key={c.id} value={c.id}>{c.code}</option>
          ))}
        </select>
        {(["IN_WORK", "AWP", "COMPLETED"] as DiscrepancyWorkStatus[]).map((s) => (
          <button
            key={s}
            onClick={() => patchMut.mutate({ status: s })}
            className="text-xs px-2 py-1 rounded border border-slate-700 hover:bg-slate-800"
          >
            {WS_LABEL[s]}
          </button>
        ))}
      </div>
      {!wo.has_qa_signoff && wo.status === "COMPLETED" && (
        <div className="mt-2 flex gap-2">
          <input
            value={signoffNotes}
            onChange={(e) => setSignoffNotes(e.target.value)}
            placeholder="QA signoff notes"
            className="flex-1 bg-slate-800 border border-slate-700 rounded px-2 py-1 text-xs"
          />
          <button
            onClick={() => signoffMut.mutate()}
            disabled={!signoffNotes.trim() || signoffMut.isPending}
            className="btn-secondary text-xs"
          >
            Sign off
          </button>
        </div>
      )}
    </div>
  );
}

export default function WorkOrderSection({
  workOrders,
  aircraftId,
}: {
  workOrders: WorkOrder[];
  aircraftId: number;
}) {
  const openOrders = workOrders.filter((w) => w.status !== "CLOSED");

  return (
    <div className="card">
      <h2 className="mb-3">Work Orders (4790 chain)</h2>
      {openOrders.length === 0 ? (
        <p className="text-sm text-slate-500">No open work orders.</p>
      ) : (
        openOrders.map((wo) => (
          <WorkOrderRow key={wo.id} wo={wo} aircraftId={aircraftId} />
        ))
      )}
    </div>
  );
}
