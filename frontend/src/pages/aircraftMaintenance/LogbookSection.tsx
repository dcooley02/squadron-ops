import type { LogbookEntry } from "../../lib/api";
import Badge from "../../components/Badge";
import { formatDate } from "../../lib/dates";

export default function LogbookSection({ logbook }: { logbook: LogbookEntry[] }) {
  return (
    <div className="card">
      <h2 className="mb-3">Aircraft Logbook</h2>
      {logbook.length === 0 ? (
        <p className="text-sm text-slate-500">No logbook entries yet.</p>
      ) : (
        <div className="space-y-2">
          {logbook.slice(0, 15).map((e: LogbookEntry) => (
            <div key={e.id} className="text-xs border-b border-slate-800 pb-2">
              <div className="flex items-center gap-2">
                <Badge variant="neutral">{e.entry_type}</Badge>
                <span className="text-slate-300 font-medium">{e.title}</span>
                <span className="text-slate-500">{formatDate(e.entry_date)}</span>
              </div>
              {e.description && (
                <p className="text-slate-500 mt-0.5 line-clamp-2">{e.description}</p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
