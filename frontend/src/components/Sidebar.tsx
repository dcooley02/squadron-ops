import { NavLink } from "react-router-dom";
import {
  LayoutDashboard, Users, Plane, Calendar,
  GraduationCap, Wrench, Tv, Settings, ClipboardList,
} from "lucide-react";
import clsx from "clsx";

const navItems = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard },
  { to: "/crew", label: "Crew", icon: Users },
  { to: "/aircraft", label: "Aircraft", icon: Plane },
  { to: "/sorties", label: "Sorties", icon: ClipboardList },
  { to: "/schedule", label: "Schedule", icon: Calendar },
  { to: "/training", label: "Training", icon: GraduationCap },
  { to: "/maintenance", label: "Maintenance", icon: Wrench },
  { to: "/board", label: "TV Board", icon: Tv },
  { to: "/admin", label: "Admin", icon: Settings },
];

export default function Sidebar() {
  return (
    <aside className="w-56 bg-slate-900 border-r border-slate-800 flex flex-col">
      <div className="p-4 border-b border-slate-800">
        <h1 className="text-base font-semibold tracking-tight">HSC Squadron Ops</h1>
        <p className="text-xs text-slate-500 mt-0.5">MH-60S Operations</p>
      </div>
      <nav className="flex-1 p-2 space-y-0.5">
        {navItems.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === "/"}
            className={({ isActive }) =>
              clsx(
                "flex items-center gap-2 px-3 py-2 rounded-md text-sm transition-colors",
                isActive
                  ? "bg-slate-800 text-white"
                  : "text-slate-400 hover:bg-slate-800/50 hover:text-slate-200"
              )
            }
          >
            <Icon size={16} />
            {label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}