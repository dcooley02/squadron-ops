# Squadron Ops — Phase F: Responsive / Mobile-Friendly Access

**Date:** 2026-08-03  
**Status:** Design approved (brainstorm); awaiting implementation plan  
**Repo:** `dcooley02/squadron-ops`  
**Approach:** Shell-first drawer + trap-fix (Approach 1)  
**Depends on:** Phase E complete (MODULE_MAP, page panels)

## Problem

The app is desktop-primary: a fixed `w-56` sidebar plus dense ops/maint/debrief layouts make large-phone demos awkward. Phase F delivers **demo-on-phone credibility** without a phone-first redesign of the whole product.

## Goals

1. **Phone demo path** — At ~390px width, a reviewer can log in, open drawer nav, and walk Dashboard → Complete Sortie → Aircraft Maintenance without the sidebar permanently consuming the content column or horizontal scroll trapping the layout.
2. **B-set readable** — Maintenance list, Sorties, Crew, Readiness: vertical scroll; no chrome-induced trap; good enough for portfolio “looks real.”
3. **Desktop preserved** — At ≥ 768px (`md`), permanent sidebar; portfolio desktop look essentially unchanged.
4. **Minimal reflow** — Tailwind stacking / overflow fixes; no separate mobile page variants.

## Non-goals (Phase F v1)

- Phone-first redesign of every page
- TV boards optimized for phone
- Offline / PWA
- Admin and every edge workflow polish
- Backend, API, cascade, or seed changes
- Bottom tab bar or icon rail (drawer only)
- Multi-squadron or new domain features

## Product decisions (brainstorm lock)

| Decision | Choice |
|----------|--------|
| Success story | Demo-on-phone credibility (not full field-maintainer productization) |
| Page set | **A:** Login, Dashboard, Complete Sortie, Aircraft Maintenance. **B:** Maintenance list, Sorties, Crew, Readiness |
| Navigation | Hamburger + **overlay drawer** on narrow; permanent sidebar on desktop |
| Layout depth | Minimal reflow |
| Approach | Shell-first drawer + trap-fix |

## Breakpoints

| Viewport | Chrome behavior |
|----------|-----------------|
| **&lt; 768px (`md`)** | Sidebar hidden as permanent column. **Menu button** opens **overlay drawer** with same nav items (role-gated). Backdrop click and **route change** close drawer. |
| **≥ 768px** | Permanent sidebar (`w-56`); no hamburger chrome. |

Align shell breakpoint to Tailwind **`md`** (768px). Content may continue using `sm:` / `md:` grids.

## Acceptance criteria

| Path | Bar at ~390px |
|------|----------------|
| Login | Form usable; no overflow trap |
| Dashboard | Metrics/cards stack; scroll ok |
| Complete Sortie | Sections stack; sticky submit usable; no horizontal trap |
| Aircraft Maintenance | Panels stack; primary CTAs reachable |
| Maintenance / Sorties / Crew / Readiness | Lists/tables scroll; readable |
| Desktop ≥ 768px | Sidebar always visible; no mobile-only chrome |

**Gate:** `./scripts/verify.sh` green (or FE test/lint/build + backend pytest) **and** manual narrow-viewport pass on the paths above.

---

## Architecture

### Scope

Frontend only. Primary files:

| File | Role |
|------|------|
| `frontend/src/components/Layout.tsx` | `navOpen` state; mobile top bar; backdrop; main padding; close drawer on `useLocation` change |
| `frontend/src/components/Sidebar.tsx` | Desktop static + mobile drawer presentation (props: `open`, `onClose`, or `variant`) |
| Priority + B-set pages | Trap-fix only (overflow, grids, min-w-0) |
| Login | Outside Layout; ensure full-width usability if needed |
| TV boards | Out of shell; **no** Phase F work |

No route or RBAC model changes. Nav still uses `NAV_ITEMS` + `canSeeNav`.

### Recommended Layout structure

```
Layout
  [≥ md] Sidebar (static flex child, hidden md:flex pattern as appropriate)
  [< md] MobileTopBar (menu + title) + Drawer(Sidebar content) + Backdrop
  main.flex-1.min-w-0.overflow-auto
    Outlet (padding: p-4 md:p-6)
```

Prefer **CSS-first** visibility (`md:hidden` / `hidden md:flex`) so breakpoint behavior matches Tailwind. Drawer open state is the only required JS for mobile nav.

Accessibility:

- Menu control: `aria-expanded`, `aria-controls`, clear labels
- Backdrop dismissible
- Optional body scroll lock while drawer open; unlock on close

### Trap-fix rules (minimal reflow)

Apply on **A + B pages** only where needed:

| Rule | Action |
|------|--------|
| Horizontal trap | `min-w-0` on flex children; `overflow-x-auto` on wide tables; avoid fixed widths that exceed viewport |
| Grids | Prefer `grid-cols-1` base then `sm:` / `md:`; fix bare multi-column grids on A/B pages |
| Padding | Main content `p-4 md:p-6` via Layout |
| Sticky footers | Complete Sortie sticky bar stays within content column; adequate bottom padding |
| Touch | Primary actions on A paths ≥ ~40px hit area where currently too small; no global redesign |

**Out of scope pages** (Admin, GradecardFill, boards, etc.): no intentional edits unless a Layout-level change covers them automatically.

### Documentation updates (when implementing)

| Doc | Change |
|-----|--------|
| `ROADMAP.md` | Phase F status → Done; acceptance matches this design |
| `docs/MODULE_MAP.md` | UX targets: desktop-primary; drawer + acceptance paths |
| `README` / `LIMITATIONS` | Short note: responsive shell; phone demo paths; not full mobile parity |

---

## Implementation order (for plan)

1. Responsive Layout + Sidebar drawer  
2. Layout padding / main `min-w-0`  
3. Trap-fix pass on A pages, then B pages  
4. Manual ~390px checklist  
5. Docs + ROADMAP Phase F Done  
6. Full verify  

## Verification matrix

| Check | Method |
|-------|--------|
| Automated | `./scripts/verify.sh` |
| Manual phone | DevTools ~390×844: Login → Dashboard → drawer → Complete Sortie → Maintenance → Aircraft Maintenance; spot Sorties/Crew/Readiness |
| Desktop | ≥ 768px permanent sidebar, no hamburger |
| Scope | No API/seed/cascade diffs |

## Risks and mitigations

| Risk | Mitigation |
|------|------------|
| Double Sidebar / confusing state | Clear static vs drawer instances; close on navigate |
| Body scroll under drawer | Optional overflow lock while open |
| Desktop visual drift | No sidebar visual redesign; display classes only |
| Scope creep | Hard A+B page list |
| Dense forms still cramped | Accepted under minimal reflow; not a Phase F failure if no trap |

## Out of scope follow-ups

- Moderate polish (cards instead of tables, larger global touch targets)
- Bottom nav or icon rail
- TV board phone layouts
- Visual regression / Playwright suite for viewports (optional later)

## Decision log

| Question | Choice |
|----------|--------|
| Success | Demo-on-phone credibility (A) |
| Pages | A four + B read-heavy ops (B) |
| Nav | Drawer (not bottom tabs / rail) |
| Depth | Minimal reflow |
| Approach | Shell-first drawer + trap-fix (1) |

---

*Design produced via Superpowers brainstorming. Next: user reviews this file → writing-plans for Phase F only.*
