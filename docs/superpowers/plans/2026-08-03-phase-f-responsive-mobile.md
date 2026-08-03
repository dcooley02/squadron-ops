# Phase F — Responsive / Mobile-Friendly Access Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver demo-on-phone credibility: drawer nav under 768px and no horizontal layout traps on Login, Dashboard, Complete Sortie, Aircraft Maintenance, plus Maintenance/Sorties/Crew/Readiness lists — while preserving permanent desktop sidebar.

**Architecture:** Shell-first. `Layout` owns mobile top bar, drawer open state, backdrop, and closes on route change. `Sidebar` supports static desktop and drawer mobile presentation. Page changes are minimal reflow only (overflow, grids, min-w-0, padding). No API/backend/cascade changes.

**Tech Stack:** React 19, TypeScript, Tailwind CSS, React Router, lucide-react (Menu/X), Vite.

**Spec:** `docs/superpowers/specs/2026-08-03-phase-f-responsive-mobile-design.md`

## Global Constraints

- Breakpoint chrome: **&lt; md (768px)** drawer; **≥ md** permanent sidebar
- Page set **A:** Login, Dashboard, Complete Sortie, Aircraft Maintenance
- Page set **B:** Maintenance list, Sorties, Crew, Readiness
- Minimal reflow — no mobile page variants, no bottom tabs
- Desktop look preserved (no sidebar visual redesign)
- No backend, seed, API, cascade, or TV board phone work
- Gate: FE test/lint/build green; manual ~390px checklist

---

## File map

| Path | Responsibility |
|------|----------------|
| `frontend/src/components/Layout.tsx` | navOpen, top bar, backdrop, main min-w-0, padding p-4 md:p-6, close on navigate |
| `frontend/src/components/Sidebar.tsx` | Accept `mode: "static" \| "drawer"`, optional `onNavigate` to close drawer; shared nav content |
| A/B pages | Trap-fix only as listed in tasks |
| `ROADMAP.md`, `docs/MODULE_MAP.md`, `README.md`, `docs/LIMITATIONS.md` | Phase F status / UX note |

---

### Task 1: Responsive Layout + Sidebar drawer

**Files:**
- Modify: `frontend/src/components/Layout.tsx`
- Modify: `frontend/src/components/Sidebar.tsx`

**Interfaces:**
- Produces: `SidebarProps = { mode?: "static" | "drawer"; onNavigate?: () => void; className?: string }`
- Layout: `const [navOpen, setNavOpen] = useState(false)`; `useEffect` on `location.pathname` → `setNavOpen(false)`

- [ ] **Step 1: Update Sidebar to accept mode + onNavigate**

Extract the existing aside content. When `mode === "drawer"`, render as:

```tsx
<aside
  id="app-sidebar"
  className={clsx(
    "fixed inset-y-0 left-0 z-50 w-56 bg-slate-900 border-r border-slate-800 flex flex-col transform transition-transform duration-200 ease-out",
    open ? "translate-x-0" : "-translate-x-full",
    className
  )}
>
```

Actually drawer open state lives in Layout — pass `open` and `onNavigate`:

```tsx
export type SidebarProps = {
  /** Desktop permanent rail vs mobile overlay panel chrome is controlled by Layout wrappers */
  onNavigate?: () => void;
  className?: string;
  id?: string;
};
```

Keep Sidebar as the **inner** nav panel (always `w-56 bg-slate-900 … flex flex-col`). Layout positions it:

- Desktop: `<Sidebar className="hidden md:flex shrink-0 h-full" />`  
- Mobile: fixed drawer wrapper with transform based on `navOpen`

On every `NavLink` click and Sign out, call `onNavigate?.()`.

- [ ] **Step 2: Rewrite Layout**

```tsx
import { useEffect, useState } from "react";
import { Outlet, useLocation } from "react-router-dom";
import { Menu, X } from "lucide-react";
import Sidebar from "./Sidebar";

export default function Layout() {
  const [navOpen, setNavOpen] = useState(false);
  const location = useLocation();

  useEffect(() => {
    setNavOpen(false);
  }, [location.pathname]);

  return (
    <div className="flex h-screen bg-slate-950 overflow-hidden">
      {/* Desktop sidebar */}
      <div className="hidden md:flex h-full shrink-0">
        <Sidebar />
      </div>

      {/* Mobile drawer */}
      <div
        className={`fixed inset-y-0 left-0 z-50 w-56 transform transition-transform duration-200 ease-out md:hidden ${
          navOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <Sidebar onNavigate={() => setNavOpen(false)} id="app-sidebar" />
      </div>
      {navOpen && (
        <button
          type="button"
          aria-label="Close menu"
          className="fixed inset-0 z-40 bg-black/50 md:hidden"
          onClick={() => setNavOpen(false)}
        />
      )}

      <div className="flex min-w-0 flex-1 flex-col overflow-hidden">
        <header className="flex shrink-0 items-center gap-3 border-b border-slate-800 bg-slate-900 px-3 py-2 md:hidden">
          <button
            type="button"
            className="inline-flex h-10 w-10 items-center justify-center rounded-md text-slate-200 hover:bg-slate-800"
            aria-expanded={navOpen}
            aria-controls="app-sidebar"
            onClick={() => setNavOpen((o) => !o)}
          >
            {navOpen ? <X size={20} /> : <Menu size={20} />}
            <span className="sr-only">{navOpen ? "Close menu" : "Open menu"}</span>
          </button>
          <div className="min-w-0">
            <div className="truncate text-sm font-semibold">HSC Squadron Ops</div>
            <div className="truncate text-xs text-slate-500">MH-60S Operations</div>
          </div>
        </header>

        <main className="min-w-0 flex-1 overflow-auto">
          <div className="mx-auto max-w-7xl p-4 md:p-6">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
```

Ensure Sidebar root is `h-full` / `flex flex-col` so drawer fills height.

- [ ] **Step 3: Build FE**

```bash
cd frontend && npm run test && npx eslint src/components/Layout.tsx src/components/Sidebar.tsx && npx tsc -b --pretty false
```

Expected: pass.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/Layout.tsx frontend/src/components/Sidebar.tsx
git commit -m "feat: responsive shell with mobile nav drawer"
```

---

### Task 2: Trap-fix A pages (Login, Dashboard, Complete Sortie, Aircraft Maintenance)

**Files:**
- Modify as needed: `Login.tsx`, `Dashboard.tsx`, `CompleteSortie.tsx`, `completeSortie/*`, `AircraftMaintenance.tsx`, `aircraftMaintenance/*`

**Rules:**
- `grid-cols-2` / `grid-cols-3` without `grid-cols-1` base → add `grid-cols-1` or keep 2 only if fits ~390px
- Dashboard `grid-cols-2` metric cluster and `col-span-2 grid grid-cols-3` → stack on xs (`grid-cols-1 sm:grid-cols-2`, etc.)
- Tables/wide panels: wrap `overflow-x-auto` if not already
- Complete Sortie sticky bar: ensure `left-0 right-0` relative to main, not full viewport under sidebar; use `sticky bottom-0` inside content or fixed within main — keep existing sticky behavior usable (check current classes)
- Touch: primary buttons `min-h-10` / `py-2.5` where clearly cramped

- [ ] **Step 1: Dashboard grids**

Known hotspots from scan:
- `grid grid-cols-2 gap-3 lg:col-span-2` → `grid grid-cols-1 sm:grid-cols-2 …`
- `col-span-2 grid grid-cols-3` → `col-span-1 sm:col-span-2 grid grid-cols-1 sm:grid-cols-3`

- [ ] **Step 2: Complete Sortie / panels**

- `grid-cols-2 sm:grid-cols-4` activity rows — ok if cells wrap; add `min-w-0` on parent cards if needed
- Sticky footer: if using `fixed`, switch to sticky within scroll container or `fixed bottom-0 left-0 right-0 md:left-56` only if that matches design — prefer not inventing md:left-56 if sticky already works inside main

- [ ] **Step 3: Aircraft Maintenance header metrics**

- Already `grid-cols-2 sm:grid-cols-4` — ok; ensure card `min-w-0`

- [ ] **Step 4: Login**

- Centered form: ensure `w-full max-w-sm px-4` and no overflow

- [ ] **Step 5: FE verify + commit**

```bash
cd frontend && npm run test && npx tsc -b --pretty false
git add frontend/src/pages/
git commit -m "fix: reflow priority pages for narrow viewports"
```

---

### Task 3: Trap-fix B pages (Maintenance, Sorties, Crew, Readiness)

**Files:**
- `Maintenance.tsx` — `grid-cols-3` metric strip → `grid-cols-1 sm:grid-cols-3` (and nested `grid-cols-3` on cards → `grid-cols-3` ok if text tiny, or `grid-cols-1 xs` → use `grid-cols-3` with smaller text is fine if no overflow; prefer `grid-cols-1 sm:grid-cols-3` for top metrics)
- `Sorties.tsx` / `Crew.tsx` — wrap table: `<div className="card p-0 overflow-x-auto">` (already overflow-hidden — change to `overflow-x-auto` so table can scroll horizontally if needed)
- `Readiness.tsx` — `grid-cols-2 md:grid-cols-4` → `grid-cols-1 sm:grid-cols-2 md:grid-cols-4`; ensure all tables inside `overflow-x-auto`

- [ ] **Step 1: Apply fixes**
- [ ] **Step 2: FE verify + commit**

```bash
cd frontend && npm run test && npx tsc -b --pretty false
git add frontend/src/pages/Maintenance.tsx frontend/src/pages/Sorties.tsx frontend/src/pages/Crew.tsx frontend/src/pages/Readiness.tsx
git commit -m "fix: reflow list/readiness pages for narrow viewports"
```

---

### Task 4: Docs + ROADMAP Phase F Done

**Files:**
- `ROADMAP.md` — Phase F status Done; strike checklist; P5 done
- `docs/MODULE_MAP.md` — UX: desktop primary; drawer &lt; md; A/B paths
- `README.md` — one line under Architecture or features
- `docs/LIMITATIONS.md` — phone demo paths, not full mobile parity

- [ ] **Step 1: Update docs**
- [ ] **Step 2: Commit**

```bash
git add ROADMAP.md docs/MODULE_MAP.md README.md docs/LIMITATIONS.md
git commit -m "docs: mark Phase F responsive shell complete"
```

---

### Task 5: Full verification

- [ ] **Step 1:** `./scripts/verify.sh` or equivalent (pytest + npm test + lint + build)
- [ ] **Step 2:** Manual checklist note in commit message or report (390px paths)
- [ ] **Step 3:** Confirm no backend/seed diffs: `git diff origin/master -- backend/` should be empty for this phase (except if only docs)

---

## Spec coverage

| Spec item | Task |
|-----------|------|
| Drawer &lt; md, static ≥ md | 1 |
| A page traps | 2 |
| B page traps | 3 |
| Docs / ROADMAP | 4 |
| Verify | 5 |
| No Phase G scope | Global |

---

## Execution handoff

Plan complete at `docs/superpowers/plans/2026-08-03-phase-f-responsive-mobile.md`.
