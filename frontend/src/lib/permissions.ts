import type { Role } from "./api";

export type NavItem = {
  to: string;
  label: string;
  roles?: Role[];
};

export const NAV_ITEMS: NavItem[] = [
  { to: "/", label: "Dashboard" },
  { to: "/crew", label: "Crew" },
  { to: "/aircraft", label: "Aircraft" },
  { to: "/sorties", label: "Sorties" },
  { to: "/schedule", label: "Schedule", roles: ["sdo", "co_xo", "admin", "pilot", "aircrew", "training_officer"] },
  { to: "/ops", label: "Ops", roles: ["sdo", "co_xo", "admin"] },
  { to: "/readiness", label: "Readiness", roles: ["co_xo", "admin", "training_officer", "sdo"] },
  { to: "/training", label: "Training", roles: ["training_officer", "co_xo", "admin", "pilot", "aircrew"] },
  { to: "/maintenance", label: "Maintenance", roles: ["maint_control", "co_xo", "admin"] },
  { to: "/board", label: "TV Board" },
  { to: "/admin", label: "Admin", roles: ["admin", "co_xo"] },
];

export function canSeeNav(role: Role, item: NavItem): boolean {
  if (!item.roles) return true;
  if (role === "admin") return true;
  return item.roles.includes(role);
}