import type { Role } from "./api";

export type NavItem = {
  to: string;
  label: string;
  /** Reserved for future per-route RBAC — not enforced yet. */
  roles?: Role[];
};

export const NAV_ITEMS: NavItem[] = [
  { to: "/", label: "Dashboard" },
  { to: "/crew", label: "Crew" },
  { to: "/aircraft", label: "Aircraft" },
  { to: "/sorties", label: "Sorties" },
  { to: "/schedule", label: "Schedule" },
  { to: "/ops", label: "Ops" },
  { to: "/readiness", label: "Readiness" },
  { to: "/training", label: "Training" },
  { to: "/maintenance", label: "Maintenance" },
  { to: "/board", label: "TV Board" },
  { to: "/admin", label: "Admin" },
];

/** All authenticated users see every nav item until per-route permissions ship. */
export function canSeeNav(_role: Role, _item: NavItem): boolean {
  return true;
}