import { describe, expect, it } from "vitest";
import { canAccessRoles, canSeeNav, type NavItem } from "./permissions";
import type { Role } from "./api";

const adminItem: NavItem = { to: "/admin", label: "Admin", roles: ["admin", "co_xo"] };
const openItem: NavItem = { to: "/", label: "Dashboard" };

describe("canSeeNav", () => {
  it("allows everyone on items without roles", () => {
    expect(canSeeNav("pilot", openItem)).toBe(true);
  });

  it("allows admin on restricted items", () => {
    expect(canSeeNav("admin", adminItem)).toBe(true);
  });

  it("allows listed roles", () => {
    expect(canSeeNav("co_xo", adminItem)).toBe(true);
  });

  it("denies unlisted roles", () => {
    expect(canSeeNav("pilot", adminItem)).toBe(false);
  });
});

describe("canAccessRoles", () => {
  it("allows empty allowed list", () => {
    expect(canAccessRoles("pilot")).toBe(true);
  });

  it("enforces role lists", () => {
    const allowed: Role[] = ["sdo", "co_xo", "admin"];
    expect(canAccessRoles("sdo", allowed)).toBe(true);
    expect(canAccessRoles("pilot", allowed)).toBe(false);
  });
});
