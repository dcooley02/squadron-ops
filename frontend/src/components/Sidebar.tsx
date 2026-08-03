import { NavLink } from "react-router-dom";
import {
  LayoutDashboard, Users, Plane, Calendar,
  GraduationCap, Wrench, Tv, Settings, ClipboardList, Shield, Radio, LogOut,
} from "lucide-react";
import clsx from "clsx";
import { useAuth } from "../context/AuthContext";
import { canSeeNav, NAV_ITEMS } from "../lib/permissions";

const ICONS: Record<string, typeof LayoutDashboard> = {
  Dashboard: LayoutDashboard,
  Crew: Users,
  Aircraft: Plane,
  Sorties: ClipboardList,
  Schedule: Calendar,
  Ops: Radio,
  Readiness: Shield,
  Training: GraduationCap,
  Maintenance: Wrench,
  "TV Board": Tv,
  Admin: Settings,
};

export type SidebarProps = {
  /** Called after nav link click or sign-out (closes mobile drawer). */
  onNavigate?: () => void;
  className?: string;
  id?: string;
};

export default function Sidebar({ onNavigate, className, id }: SidebarProps) {
  const { user, logout } = useAuth();
  const visible = user ? NAV_ITEMS.filter((item) => canSeeNav(user.role, item)) : [];

  return (
    <aside
      id={id}
      className={clsx(
        "h-full w-56 bg-slate-900 border-r border-slate-800 flex flex-col",
        className
      )}
    >
      <div className="p-4 border-b border-slate-800">
        <h1 className="text-base font-semibold tracking-tight">HSC Squadron Ops</h1>
        <p className="text-xs text-slate-500 mt-0.5">MH-60S Operations</p>
        {user && (
          <p className="text-xs text-slate-400 mt-2 truncate" title={user.username}>
            {user.rank ? `${user.rank} ` : ""}
            {user.last_name}
            {user.callsign ? ` (${user.callsign})` : ""}
          </p>
        )}
      </div>
      <nav className="flex-1 p-2 space-y-0.5 overflow-y-auto">
        {visible.map(({ to, label }) => {
          const Icon = ICONS[label] ?? LayoutDashboard;
          return (
            <NavLink
              key={to}
              to={to}
              end={to === "/"}
              onClick={() => onNavigate?.()}
              className={({ isActive }) =>
                clsx(
                  "flex items-center gap-2 px-3 py-2.5 min-h-10 rounded-md text-sm transition-colors",
                  isActive
                    ? "bg-slate-800 text-white"
                    : "text-slate-400 hover:bg-slate-800/50 hover:text-slate-200"
                )
              }
            >
              <Icon size={16} />
              {label}
            </NavLink>
          );
        })}
        {user && (
          <NavLink
            to={`/crew/${user.id}`}
            onClick={() => onNavigate?.()}
            className={({ isActive }) =>
              clsx(
                "flex items-center gap-2 px-3 py-2.5 min-h-10 rounded-md text-sm transition-colors",
                isActive
                  ? "bg-slate-800 text-white"
                  : "text-slate-400 hover:bg-slate-800/50 hover:text-slate-200"
              )
            }
          >
            <Users size={16} />
            My Jacket
          </NavLink>
        )}
      </nav>
      <div className="p-2 border-t border-slate-800">
        <button
          type="button"
          onClick={() => {
            logout();
            onNavigate?.();
          }}
          className="flex items-center gap-2 w-full px-3 py-2.5 min-h-10 rounded-md text-sm text-slate-400 hover:bg-slate-800/50 hover:text-slate-200"
        >
          <LogOut size={16} />
          Sign out
        </button>
      </div>
    </aside>
  );
}
