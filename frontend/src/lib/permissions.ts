import type { Role } from "./api";

export type NavItem = {
  to: string;
  label: string;
  /** When set, only these roles (plus admin) see the item unless open-RBAC mode. */
  roles?: Role[];
};

/** Open ACL for portfolio demos — mirrors backend DEMO_OPEN_RBAC. */
export function isDemoOpenRbac(): boolean {
  return import.meta.env.VITE_DEMO_OPEN_RBAC === "true";
}

export const NAV_ITEMS: NavItem[] = [
  { to: "/", label: "Dashboard" },
  { to: "/crew", label: "Crew" },
  { to: "/aircraft", label: "Aircraft" },
  { to: "/sorties", label: "Sorties" },
  {
    to: "/schedule",
    label: "Schedule",
    roles: ["sdo", "co_xo", "admin", "training_officer"],
  },
  { to: "/ops", label: "Ops", roles: ["sdo", "co_xo", "admin"] },
  { to: "/readiness", label: "Readiness" },
  { to: "/training", label: "Training" },
  { to: "/maintenance", label: "Maintenance" },
  { to: "/board", label: "TV Board" },
  { to: "/admin", label: "Admin", roles: ["admin", "co_xo"] },
];

/** Role-gated app routes (path prefix → allowed roles). Empty/missing = any auth user. */
export const ROUTE_ROLES: { path: string; roles: Role[] }[] = [
  { path: "/ops", roles: ["sdo", "co_xo", "admin"] },
  { path: "/schedule", roles: ["sdo", "co_xo", "admin", "training_officer"] },
  { path: "/admin", roles: ["admin", "co_xo"] },
];

export function canSeeNav(role: Role, item: NavItem): boolean {
  if (isDemoOpenRbac()) return true;
  if (!item.roles || item.roles.length === 0) return true;
  if (role === "admin") return true;
  return item.roles.includes(role);
}

export function canAccessRoles(role: Role, allowed?: Role[]): boolean {
  if (isDemoOpenRbac()) return true;
  if (!allowed || allowed.length === 0) return true;
  if (role === "admin") return true;
  return allowed.includes(role);
}

export function rolesForPath(pathname: string): Role[] | undefined {
  const match = ROUTE_ROLES.find(
    (r) => pathname === r.path || pathname.startsWith(`${r.path}/`)
  );
  return match?.roles;
}
