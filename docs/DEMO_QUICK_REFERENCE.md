# Squadron Ops — Quick Reference

Local demonstration environment. Password `demo1234` for all accounts below (demonstration only — not for production).

---

## Setup

```bash
./scripts/demo-prep.sh

# Terminal 1
cd backend && source .venv/bin/activate && uvicorn app.main:app --reload --port 8001

# Terminal 2
cd frontend && npm run dev
```

| Service | URL |
|---------|-----|
| Application | http://localhost:5174 |
| Login | http://localhost:5174/login |
| API | http://localhost:8001 |
| API docs | http://localhost:8001/docs |

---

## Demo Accounts

| Username | Role |
|----------|------|
| `anderson.robert` | SDO |
| `morgan.david` | Maintenance control |
| `mitchell.james` | Line pilot |
| `cooper.lisa` | Training officer |
| `admin` | Admin |

Run `./scripts/demo-prep.sh` before each demonstration to restore drift scenarios, today's sorties, and currency distribution.

---

## Key Aircraft (Side Numbers)

Database IDs change on reseed — use side numbers and the maintenance page to resolve.

| Side | Status |
|------|--------|
| 610–613 | True FMC (stamped = computed) |
| 614 | Drift: FMC stamped → PMC computed — QA release allowed |
| 615 | Drift: FMC stamped → NMCM computed — release blocked |
| 616 | Stamped PMC |
| 617 | Drift: FMC stamped → NMCS computed — release blocked |

---

## Demonstration Sorties

**Today (Dashboard → Next 24 Hours):**
- 0900 — Proficiency (day)
- 1400 — P201 intro
- Day+2 evening ASU P211 — best cascade demo (NVG/night hours)

**Simulator:** Schedule → day+3 1500 P200 TOFT sim → complete to show sim-eligible currency rules

---

## Terminology

- **QA release / release for flight / safe for flight** — post-maintenance line release
- **Stamped vs. computed** — line paperwork vs. derived status from open discrepancies
- **WTM T-ratings** — capability-area readiness (distinct from individual Table B-2 currency)
- Do not use **RTS** in maintenance context (conflicts with Ready to Strike)

---

## Routes

| Path | Purpose |
|------|---------|
| `/` | Dashboard |
| `/readiness` | WTM readiness |
| `/maintenance` | Maintenance overview |
| `/maintenance/{id}` | Aircraft maintenance detail |
| `/sorties` | Sortie list |
| `/sorties/{id}/complete` | Complete sortie |
| `/schedule` | Schedule + assisted scheduling |
| `/ops` | SDO day-of-ops |
| `/crew/{id}` | Crew detail |
| `/logbook/{personId}` | Digital logbook |
| `/board/readiness` | TV squadron snapshot |
| `/admin` | Audit log |

---

## PDF Exports

Requires WeasyPrint in the backend virtual environment (`pip install weasyprint`).

| Export | Location |
|--------|----------|
| Readiness brief | `/readiness` → Export PDF |
| ATO | `/ops` → Export ATO PDF |
| Brief sheet | Sortie detail → Export Brief Sheet PDF |
| Gradecard | Gradecard detail → Export PDF |
| Logbook | Logbook page → Download PDF |

---

## Troubleshooting

| Symptom | Action |
|---------|--------|
| 401 on API | Log in again (session expired) |
| Blank data | `./scripts/demo-prep.sh` |
| No drift banner | Reseed (QA release consumes drift) |
| PDF 503 | Install WeasyPrint in backend venv |
| DB connection failed | `docker compose ps` (port 5433) |
| Frontend errors | `cd frontend && npm ci` |

---

## Verify

```bash
cd backend && pytest -q
cd frontend && npm run build
```