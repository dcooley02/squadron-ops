import { Link } from "react-router-dom";
import { Monitor, Wrench, Shield } from "lucide-react";

const BOARDS = [
  {
    to: "/board/ops",
    icon: <Monitor size={36} className="text-blue-400" />,
    title: "Ops Board",
    description:
      "Today's flight schedule with crew and fitness status, aircraft strip, and currency warnings ticker.",
    accent: "hover:border-blue-700/60",
  },
  {
    to: "/board/maint",
    icon: <Wrench size={36} className="text-yellow-400" />,
    title: "Maintenance Board",
    description:
      "Per-airframe status, total hours, hours to phase inspection, and open discrepancies.",
    accent: "hover:border-yellow-700/60",
  },
  {
    to: "/board/readiness",
    icon: <Shield size={36} className="text-green-400" />,
    title: "Readiness Board",
    description:
      "FMC rate ring, personnel composition, 30-day activity, currency overview, and aircraft strip.",
    accent: "hover:border-green-700/60",
  },
];

export default function BoardIndex() {
  return (
    <div className="space-y-5">
      <div>
        <h1>TV Boards</h1>
        <p className="text-sm text-slate-400 mt-1">
          Fullscreen kiosk views for ready room and maintenance spaces. Open in a separate
          window and go fullscreen for wall display.
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {BOARDS.map((b) => (
          <Link
            key={b.to}
            to={b.to}
            target="_blank"
            rel="noopener noreferrer"
            className={`card flex flex-col gap-4 transition-colors ${b.accent}`}
          >
            {b.icon}
            <div>
              <div className="text-lg font-semibold text-slate-100">{b.title}</div>
              <div className="text-sm text-slate-400 mt-1 leading-relaxed">{b.description}</div>
            </div>
            <div className="text-xs text-slate-600 mt-auto pt-2 border-t border-slate-800">
              Opens in new tab — go fullscreen (F11) for wall display
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
